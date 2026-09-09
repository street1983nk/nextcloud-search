# Zeitbudget der Ergebnisseite, gemessen am 09.09.2026

Dieser Bericht ist die Messgrundlage für das Zeitbudget der eigenen
Ergebnisseite (Phase 9). Der offene Punkt 4 der `09-UI-SPEC.md` verlangt eine
gemessene Zahl statt einer geschätzten, und Annahme A3 der `09-RESEARCH.md`
fragt, ob ein einzelner Kandidatenaufruf mit `limit=100` unter dem
1,5-Sekunden-Deckel von `ExAppService::call()` bleibt. Beides wird hier
beantwortet.

Gemessen wurde auf der laufenden lokalen Test-Nextcloud, über den echten
PHP-Weg, weil genau dieser Weg später die Seite trägt, und zusätzlich direkt
gegen die beiden Container-Routen, weil nur die Trennung zeigt, wo die Zeit
tatsächlich liegt.

---

## 1. Die Ausgangslage, und was vor der Messung dafür getan wurde

Die Instanz stand vor dieser Messung im Wartungszustand (`needsDbUpgrade: true`)
und trug die App-Fassung 0.3.0, während das Repository bei 1.0.3 steht. Eine
Messung in diesem Zustand hätte den Wartungszustand gemessen. Deshalb zuerst
`occ upgrade`, danach die Fassungsgleichheit geprüft, danach der Korpus, danach
erst die erste Zahl.

| Was | Wert |
|---|---|
| Datum des Laufs | 2026-09-09 |
| Container | `findling-nextcloud`, Abbild `nextcloud:34.0.3-apache`, Port 8090 |
| Serverfassung | 34.0.3.2, `maintenance: false`, `needsDbUpgrade: false` (nach `occ upgrade`) |
| App-Fassung | `findling: 1.0.3` (vorher 0.3.0, angehoben durch `occ upgrade`) |
| ExApp | `findling_backend`, angemeldet als `manual-install`, Host-Prozess auf Port 10035 |
| Nutzer | `testuser` |
| Korpus | `testdata/corpus` plus 300 synthetische Dateien aus `scripts/dev/build_load_corpus.py` |
| Seed des synthetischen Teils | `phase9-budget`, 300 Dateien, 168.952.616 Bytes, Prüfsumme `658058e515843fcabcbf953dbdc83ccd244e5d694a2a692aab4816adf66a2c78` |
| Index im Container | 431 Dokumente, davon 429 indiziert, 31 übersprungen, 10 gescheitert |
| Wortlisten-Digest | `b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0` |
| Warteschlange | `occ findling:index` meldet `scheduled 0` und `handed to the worker 0` |
| Dialogeinstellung | `occ config:app:set core unified_search_max_results_per_request --value 100` |

**Die Suchbegriffe und ihre Kandidatenzahl.** Beide stammen aus dem
Wortvorrat des synthetischen Korpus und aus keiner echten Ablage:

| Begriff | Wörter | Kandidaten bei `limit=100` | `hasMore` |
|---|---|---|---|
| `Bescheid` | 1 | 100 (der Deckel `MAX_LIMIT`) | ja |
| `Bescheid Antrag` | 2 | 100 (der Deckel `MAX_LIMIT`) | ja |

Die Bedingung aus Aufgabe 1 des Plans, mehr als 100 Kandidaten für einen
Begriff, ist damit erfüllt: beide Begriffe füllen die Seite bis an den Deckel
und melden weitere.

## 2. Das Verfahren

Fünf Messreihen, jede mit 20 Wiederholungen, jede Wiederholung eine ganze
Anfrage, gemessen mit `curl -w '%{time_total}' -o /dev/null`. Vor der ersten
Reihe liefen fünf Aufwärmanfragen, die nicht in die Rohdaten eingehen.

Drei Reihen über die Dialogroute, also über PHP, den Rechteabgleich und beide
Container-Aufrufe:

- **Reihe A**: ein Wort, `title-only=true`. Rein lexikalisch, nur der Dateiname.
- **Reihe B**: ein Wort, ohne den Filter. Nach `one_round()` ebenfalls
  `lexical_only`, weil ein einzelner Term die Vektorseite ausschaltet.
- **Reihe C**: zwei Wörter, ohne den Filter. Der Fall, der laut Bauart hybrid
  ist. Abschnitt 5.1 sagt, warum er es auf dieser Instanz nicht war.

Zwei Reihen direkt gegen den Container, mit den AppAPI-Kopfzeilen, ohne PHP:

- **Kandidatenaufruf**: `POST /search`, `limit=100`, zweiwortiger Begriff.
- **Snippet-Aufruf**: `POST /snippets` mit 25 `fileIds` aus der Antwort davor.

Rohdaten in `raw/`, eine Zahl je Zeile, Sekunden, unbearbeitet. `p50` und `p95`
sind Rangwerte ohne Interpolation: der Wert an Rang `ceil(0,50 * n)`
beziehungsweise `ceil(0,95 * n)` der sortierten Reihe, bei n gleich 20 also der
zehnte und der neunzehnte Wert.

## 3. Die Zahlen

| Reihe | Weg | n | min | p50 | **p95** | max |
|---|---|---|---|---|---|---|
| Reihe A | OCS, ein Wort, nur Dateiname | 20 | 0,392 s | 0,425 s | **0,490 s** | 0,494 s |
| Reihe B | OCS, ein Wort, Inhalt | 20 | 0,617 s | 0,651 s | **0,698 s** | 0,702 s |
| Reihe C | OCS, zwei Wörter, Inhalt | 20 | 0,611 s | 0,656 s | **0,712 s** | 0,726 s |
| Kandidatenaufruf | Container, `POST /search`, `limit=100` | 20 | 0,004 s | 0,005 s | **0,022 s** | 0,024 s |
| Snippet-Aufruf | Container, `POST /snippets`, 25 Dateien | 20 | 0,066 s | 0,068 s | **0,088 s** | 1,944 s |

## 4. Das Verdikt zu Annahme A3

**A3 hält: ja.** Ein Kandidatenaufruf mit `limit=100` bleibt auf dieser Instanz
weit unter dem 1,5-Sekunden-Deckel von `ExAppService::call()`. Die Zahl, auf die
sich die Antwort stützt, ist der p95 des Kandidatenaufrufs: **0,022 Sekunden**,
mit einem Höchstwert von 0,024 Sekunden über 20 Aufrufe. Das ist ein Achtzigstel
des Deckels.

Damit ist auch Pitfall 3 der Recherche für diesen Korpus entschärft: der Deckel
ist heute nicht die Stelle, an der die Zeit verloren geht.

## 5. Befunde, die von der Erwartung abweichen

### 5.1 Der teure Fall war nicht teuer, weil es ihn hier nicht gibt

Die Recherche erwartet Reihe C als den hybriden, teuren Fall mit vollem
Vektorlauf je Runde. Gemessen ist Reihe C praktisch so teuer wie Reihe B
(p95 0,712 s gegen 0,698 s), und der Grund ist nicht die Suche, sondern die
Umgebung: `one_round()` schaltet die Vektorseite nur ein, wenn
`side.vectors is not None`, und auf dieser Instanz gibt es keine `vectors.db`.
Das Modellverzeichnis `/usr/local/share/findling/model` liegt im
Auslieferungsabbild, der Alltagsstack fährt das Backend aber als gewöhnlichen
Host-Prozess, also ohne Modell und damit ohne Vektorbestand.

**Reihe C ist deshalb der zweiwortige lexikalische Fall und nicht der hybride.**
Der hybride Fall ist an anderer Stelle dieses Projekts gemessen und wird hier
zitiert statt geschätzt: `docs/measurements/2026-09-05-semantiklauf-m7g/`,
Abschnitt "Die Suche bleibt benutzbar", 30 echte Nutzersuchen über dieselbe
OCS-Route bei vollem Vektorbestand (145.854 Vektoren):

| Probe dort | p50 | p95 | max |
|---|---|---|---|
| während die zweite Spur lief | 735,5 ms | 1.129,0 ms | 2.065 ms |
| bei vollem Vektorbestand, ohne Nebenlast | 478,5 ms | 524,0 ms | 525 ms |

### 5.2 Die Zeit liegt in PHP, nicht im Container

Der Container beantwortet den Kandidatenaufruf in 5 Millisekunden und den
Snippet-Aufruf in 68, zusammen also rund 0,07 Sekunden. Eine ganze Suche über
die Dialogroute kostet 0,65 Sekunden. Rund neun Zehntel der Zeit liegen damit
auf der PHP-Seite: Anfragebau der Instanz, der günstige Vorfilter, der
Rechteabgleich Datei für Datei über `getFirstNodeById` und `isReadable`, und
das Zusammensetzen der Antwort. Für die Ergebnisseite heißt das, dass ihr
Budget vor allem von der Zahl der zu prüfenden Kandidaten abhängt und nur zu
einem kleinen Teil von der Geduld pro Container-Aufruf.

### 5.3 Ein Ausreißer, und die Gegenprobe dazu

Der dritte Snippet-Aufruf der gemessenen Reihe brauchte 1,944 Sekunden, während
alle anderen 19 zwischen 0,066 und 0,088 Sekunden lagen. Der Wert steht
unverändert in `raw/snippetaufruf.txt`, weil ein herausgenommener Ausreißer eine
Behauptung ist und kein Messwert.

Die Gegenprobe: 80 weitere Aufrufe derselben Anfrage, in
`raw/zusatz-snippet-gegenprobe.tsv`, Höchstwert 0,089 Sekunden, kein einziger
Wert über 1,5 Sekunden. Über alle 100 Aufrufe ist es ein Ereignis. Es ist zu
selten, um eine Konstante darauf zu setzen, und zu groß, um es zu verschweigen:
unter dem heutigen Deckel von 1,5 Sekunden wäre dieser eine Aufruf abgeschnitten
worden und die Runde hätte ihn verloren.

### 5.4 Was hier nicht gemessen werden konnte

- **Tiefe Seiten.** Der Korpus liefert für die benutzten Begriffe etwa 140
  Kandidaten. Der Offset-Deckel des Containers steht bei 1200, und die Kosten
  einer Anfrage an dieser Grenze bleiben ungemessen.
- **Der hybride Fall** auf dieser Instanz, siehe 5.1.
- **Nebenlast.** Alle Zahlen sind Leerlaufzahlen. Die einzige Messung dieses
  Projekts mit laufender zweiter Spur ist die zitierte aus 5.1, und sie ist dort
  gut doppelt so langsam wie ohne.

## 6. Die beiden abgeleiteten Zahlen

### 6.1 `PAGE_REQUEST_TIMEOUT_SECONDS` = 1.5

Regel des Plans: p95 des einzelnen Kandidatenaufrufs plus 50 Prozent Reserve,
auf halbe Sekunden aufgerundet, mindestens jedoch 1,5.

Rechnung: 0,022 s mal 1,5 ergibt 0,033 s, aufgerundet 0,5 s, und damit unter der
Untergrenze. **Es entscheidet die Untergrenze: 1,5 Sekunden.**

Die Zahl ist damit heute dieselbe wie die des Dialogs, und das ist der ehrliche
Ausgang dieser Messung: der Container ist auf diesem Korpus so schnell, dass
kein höherer Deckel begründbar wäre. Der Gewinn liegt nicht in der Zahl, sondern
darin, dass die Seite ab jetzt eine eigene hat: der Deckel ist ein Argument von
`ExAppService::call()` geworden, also ist Pitfall 3 keine Sackgasse mehr,
sondern eine Konstante, die eine spätere Messung auf einer echten Instanz
anheben kann, ohne dass der Dialogweg sich ändert.

Der Ausreißer aus 5.3 begründet keine höhere Zahl: ein Ereignis in 100 Aufrufen
ist kein p95, und eine Konstante auf einen einzelnen Wert zu setzen wäre
derselbe Fehler wie ihn wegzurunden, nur in die andere Richtung.

### 6.2 `PAGE_BUDGET_SECONDS` = 3.0

Regel des Plans: p95 der Reihe C plus 50 Prozent Reserve, auf halbe Sekunden
aufgerundet. Rechnung: 0,712 s mal 1,5 ergibt 1,068 s, aufgerundet **1,5 s**.

**Diese Zahl wird nicht übernommen, und der Grund ist ein Befund und keine
Bequemlichkeit.** Sie wäre kleiner als das Budget des Dialogs
(`Provider::BUDGET_NANOSECONDS` = 2,5 Sekunden). Eine Seite, die alle Treffer
verspricht und auf niemanden wartet, wäre damit ungeduldiger als der Dialog, aus
dem sie aufgerufen wird. Dazu kommt, dass ihre Eingangszahl nach 5.1 nicht der
teure Fall ist.

Die übernommene Zahl entsteht aus den gemessenen Werten dieses Berichts, entlang
des schlechtesten beobachteten Ablaufs einer einzelnen Runde:

| Posten | Wert | Herkunft |
|---|---|---|
| schlechtester beobachteter Container-Aufruf | 1,944 s | Abschnitt 5.3, 1 von 100 |
| PHP-Anteil einer Suche | rund 0,59 s | Reihe B p95 0,698 s minus die 0,110 s der beiden Container-p95 |
| Summe einer Runde im schlechtesten gemessenen Fall | 2,53 s | Addition der beiden Posten |
| nächste halbe Sekunde darüber | **3,0 s** | die übernommene Zahl |

Zur Kontrolle gegen den hybriden Fall aus 5.1: dessen p95 unter Nebenlast ist
1,129 s, sein Höchstwert 2,065 s; 3,0 Sekunden decken beides. Zur Kontrolle
gegen die Erwartungshaltung der Recherche, "wie der Dialog, plus ein Viertel":
3,0 Sekunden sind das Budget des Dialogs plus ein Fünftel, also nah an der
Erwartung und nicht darüber hinaus.

`PAGE_BUDGET_SECONDS` = 3,0 Sekunden ist die Zahl, die Plan 09-04 als Konstante
der Seitenroute übernimmt. `PAGE_REQUEST_TIMEOUT_SECONDS` = 1,5 Sekunden ist die
Zahl, die als Konstante in `php/lib/Service/ExAppService.php` steht, mit diesem
Bericht und diesem Messdatum im Kommentar.

## 6.3 Nachtrag vom 09.09.2026: der Nachlauf gegen die fertige Seitenroute

Dieser Abschnitt kommt aus dem Performance-Audit der Phase 9
(`docs/audits/2026-09-phase-09/`) und korrigiert eine Zuordnung dieses Berichts.
Er wurde nach der letzten Änderung der Seite gefahren, gegen dieselbe Instanz,
denselben Zwei-Wort-Begriff (`Bescheid Antrag`) und mit denselben 20
Wiederholungen und derselben Rangregel. Rohdaten in `raw/nachlauf-*.txt`.

| Reihe | Weg | n | min | p50 | **p95** | max |
|---|---|---|---|---|---|---|
| Seite mit Suche, Sitzung | `GET /apps/findling/?query=...`, Cookie | 20 | 0,090 s | 0,104 s | **0,122 s** | 0,125 s |
| Seite mit Suche, Basic-Auth | dieselbe Adresse, `-u testuser:...` | 20 | 0,386 s | 0,419 s | **0,445 s** | 0,457 s |
| Dialogweg, Basic-Auth, `limit=100` | die OCS-Route dieses Berichts | 20 | 0,474 s | 0,507 s | **0,538 s** | 0,540 s |
| Seite ohne Suche, Sitzung | `GET /apps/findling/`, kein Backend-Aufruf | 20 | 0,033 s | 0,044 s | **0,055 s** | 0,066 s |
| Seite ohne Suche, Basic-Auth | dieselbe Adresse | 20 | 0,327 s | 0,343 s | **0,373 s** | 0,390 s |

**Das Budget hält, mit Abstand.** Die Seitenroute antwortet auf dem Weg, den ein
angemeldeter Nutzer wirklich geht, mit einem p95 von 0,122 Sekunden. Das sind
vier Prozent von `PAGE_BUDGET_SECONDS` = 3,0 Sekunden. Auch mit den Kosten der
Basic-Auth, die ein Browser nicht bezahlt, bleiben es 15 Prozent.

**Die Erwartung der Recherche ist widerlegt, und zwar in die andere Richtung.**
Erwartet war "wie der Dialog, plus ein Viertel", weil die Seite pro Runde bis zu
100 Kandidaten holt statt bis zu 80. Gleich gemessen (beide mit Basic-Auth,
dieselbe Instanz, dieselbe Minute) ist die Seite am p95 um 0,093 Sekunden
**schneller** als der Dialogweg mit `limit=100`. Der Grund liegt in
`SearchService`: `$fetchLimit` ist auf das gedeckelt, was das Recheck-Budget
überhaupt prüfen kann, also holt die Seite für 25 Anzeigetreffer weniger
Kandidaten als der Dialogaufruf mit `limit=100`.

**Und die Korrektur an Abschnitt 5.2.** Dort steht, rund neun Zehntel der Zeit
einer Suche lägen "auf der PHP-Seite: Anfragebau, Vorfilter, Rechteabgleich Datei
für Datei, Zusammensetzen der Antwort". Das ist für die dort gemessene Reihe
richtig gerechnet und in der Zuordnung zu großzügig: **0,318 Sekunden davon sind
die Passwortprüfung der Messmethode.** Die beiden letzten Zeilen der Tabelle
oben trennen das, weil sie dieselbe Adresse ohne Suchbegriff abrufen, also ohne
einen einzigen Container-Aufruf und ohne Recheck: 0,055 s mit Sitzung gegen
0,373 s mit Basic-Auth. Die Differenz ist der Preis von `-u`, den jede Reihe
dieses Berichts zwanzigmal bezahlt hat und den kein angemeldeter Nutzer bezahlt.

Was von 5.2 stehen bleibt: die Zeit liegt nicht im Container. Was zu korrigieren
ist: sie liegt auch nicht in dem Umfang im Rechteabgleich, den 5.2 nahelegt. Der
gemessene Anteil der ganzen Suche, also beide Container-Aufrufe plus der Recheck
von 25 genehmigten Treffern plus das Rendern, ist die Differenz der ersten und
der vierten Zeile: **0,067 Sekunden am p95.** Für Phase 10 heißt das: eine Zahl
dieses Berichts mit einer Zahl von dort zu vergleichen, geht nur bei gleichem
Anmeldeweg.

**Was auch dieser Nachlauf nicht gemessen hat:** den hybriden Fall (auf dieser
Instanz gibt es keine `vectors.db`, siehe 5.1), Nebenlast, und eine Seite jenseits
der Offset-Decke unter Last. Der Korpus war ein anderer als in Abschnitt 3: die
Instanz trug am 09.09.2026 abends 438 indexierte Dateien, und der benutzte
Begriff liefert 12 volle Anzeigeseiten. Die Zahlen der Abschnitte 3 bis 6 sind
deshalb nicht durch diesen Nachlauf ersetzt, sondern durch ihn ergänzt.

## 7. Nachstellen

```bash
export COMPOSE_FILE=scripts/dev/compose.yaml
export FINDLING_PORT=8090

docker compose exec -T -u www-data app php occ upgrade
docker compose exec -T -u www-data app php occ app:list | grep findling
docker compose exec -T -u www-data app php occ config:app:set core \
  unified_search_max_results_per_request --value 100

# Reihe B, zwanzig Wiederholungen
for i in $(seq 20); do
  curl -s -o /dev/null -w '%{time_total}\n' \
    -u testuser:findling-dev-testuser \
    -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
    'http://localhost:8090/ocs/v2.php/search/providers/findling/search?term=Bescheid&limit=100'
done
```

Reihe A hängt `&title-only=true` an, Reihe C ersetzt den Begriff durch
`Bescheid%20Antrag`. Die beiden Container-Reihen gehen an
`http://127.0.0.1:10035/search` und `/snippets` mit den Kopfzeilen
`AA-VERSION`, `EX-APP-ID`, `EX-APP-VERSION` und
`AUTHORIZATION-APP-API: base64(testuser:$(cat .dev/exapp.secret))`.
