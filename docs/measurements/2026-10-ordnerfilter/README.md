# Messung: Budget des Ordnerfilters in der Unified Search (Plan 32-03)

Stand: 2026-10-13. Diese Messung belegt Annahme A2 der Phasen-Recherche
(Pitfall 4): reichen `FOLDER_FETCH_LIMIT` und `FOLDER_MAX_ROUNDS` in
`php/lib/Service/SearchService.php`, damit ein enger Ordner mit tief gerankten
Treffern im Dialog innerhalb der Frist von 2,5 s (`Provider::BUDGET_SECONDS`)
eine volle Gruppe liefert?

## 1. Entscheidungsregel (vor der Messung festgelegt)

Gewählt wird die kleinste Variante, bei der

1. beide Ordnerabfragen (`/Messung32/Innen`, `/Messung32/Einzeln`) bei jedem
   gemessenen Limit `min(Limit, Treffer im Ordner)` Treffer liefern,
2. der Median jeder Ordnerabfrage unter 1,5 s und das Maximum unter 2,5 s
   bleibt,
3. die Suche ohne Ordner gegenüber dem Basislauf (Commit vor 32-02) im Median
   um höchstens 10 Prozent langsamer ist.

Erfüllt keine Variante die Regel, wird keine still gewählt. Dann steht unten
eine Owner-Frage, und der Plan endet mit einem Checkpoint. Der Ausweg der
Recherche wäre eine Erlaubnisliste über `file_id` als neues Wire-Feld, das
D-32-06 (der Ordner verlässt PHP nie) widerspräche.

## 2. Umgebung

| Was | Wert |
|---|---|
| Datum des Laufs | 2026-10-13, 01:01 bis 01:35 Uhr MESZ |
| Maschine | Intel Core i5-1335U, 12 logische Kerne, 16 GB RAM (rund 3,1 GB frei bei Beginn), Windows 11 Pro |
| Docker | Docker Desktop, Engine 29.5.2, VM mit 7,6 GiB; `findling-nextcloud` 78 bis 181 MiB während der Läufe |
| Instanz | `findling-nextcloud`, Abbild `nextcloud:34.0.3-apache`, Port 8090, `php/` als Bind-Mount nach `custom_apps/findling` |
| Serverfassung | `versionstring` 34.0.3; vorher `needsDbUpgrade: true`, nach `occ upgrade` `false`, App `findling` dabei auf 1.4.2 gehoben |
| ExApp | `findling_backend` 1.4.2, `manual-install`, Host-Prozess auf Port 10035; vor der Messung mit `scripts/dev/register-exapp.sh` neu gestartet, weil der laufende Prozess noch 1.4.0 meldete |
| Kanarie | `term=findling-canary` über die OCS-Suchroute: Eintrag `findling-canary` aus dem Container, HTTP 200, vor jeder Variante wiederholt |
| Nutzer, Anmeldung | `testuser` mit einem App-Passwort (`occ user:auth-tokens:add`), damit keine Reihe die bcrypt-Prüfung des Login-Passworts mitmisst (Seitenbudget-Bericht, Abschnitt 6: rund 0,32 s je Anfrage); Token nach der Messung gelöscht |
| Dialog-Limit | stable34 `UnifiedSearchModal.vue`: `providerResultLimit: 5` (Zeile 306), `limit` wird erst über 5 gesendet (Zeilen 558 bis 560), "Mehr laden" erhöht um 5 (Zeile 670); ohne Parameter setzt `UnifiedSearchController` `SearchQuery::LIMIT_DEFAULT` = 5. Gemessen wurden daher `limit=5` (erster Abruf) und `limit=10` (erstes "Mehr laden") |

## 3. Korpus

Ein Begriff, der sonst nirgends vorkommt: `ordnermessung32`. Er steht in keinem
Dateinamen, das Ranking ist also allein der Textkörper.

| Ordner | Dateien | Inhalt | Rang |
|---|---|---|---|
| `/Messung32/Aussen/` | 1000 | kurz, Begriff 30-mal | 1 bis 1000 |
| `/Messung32/Innen/Tief/` | 10 | rund 400 Füllwörter, Begriff einmal (1 Prozent der Treffer) | 1001 bis 1010 |
| `/Messung32/Einzeln/` | 1 | wie Innen (0,1 Prozent) | 1011 |

Angelegt per WebDAV mit `scripts/dev/measure_folder_filter.sh setup`
(6 min 55 s). Beleg, dass der Index den ganzen Korpus trägt und die
Ordnertreffer wirklich hinten liegen, direkt gegen den Container
(`POST /search`, `limit=100`): Offset 900 liefert 100 Kandidaten mit
`hasMore: true`, Offset 1000 genau 11 mit `hasMore: false`, Offset 1100 keinen.
Die elf Datei-IDs auf Rang 1001 bis 1011 (1730 bis 1740) sind genau die
`oc:fileid`-Werte der Dateien unter `Innen/Tief` und `Einzeln` (PROPFIND).

## 4. Verfahren

- `scripts/dev/measure_folder_filter.sh measure`: je Variante sechs Abfragen
  (ohne Ordner, `folder=/Messung32/Innen`, `folder=/Messung32/Einzeln`, jeweils
  mit `limit=5` und `limit=10`), je Abfrage ein verworfener Aufwärmaufruf, dann
  20 Wiederholungen. Zeit ist `curl -w '%{time_total}'` der ganzen Anfrage.
- Treffer sind Einträge mit einer Datei-ID über 0; die Tür zur Ergebnisseite und
  die Kanarie zählen nicht. Stehen in einer Zelle zwei Werte (`4/5`), schwankte
  die Zahl innerhalb der Reihe; das kam nicht vor.
- Median ist der Rangwert an `ceil(0,5 * n)`, Maximum der größte Wert, beide
  ohne Interpolation (Regel des Seitenbudget-Berichts).
- Varianten über den Bind-Mount, `php/lib/Service/SearchService.php` je Lauf
  ersetzt, danach Neustart des Containers (OPcache prüft nur alle 60 s neu),
  SHA-256 der Datei im Container gegen die lokale Datei verglichen, Kanarie
  abgefragt, erst dann gemessen. Nach dem letzten Lauf die Originaldatei zurück,
  `git diff --quiet -- php/` ohne Befund.
  - **Basis**: `SearchService.php` aus Commit 39e8eca9 (vor 32-02), als Blob per
    `git show`, nachdem ein `git worktree` des Commits den Stand bestätigt
    hatte. Diese Fassung kennt keinen Ordner; die Ordnerabfragen liefern deshalb
    ungefilterte Gruppen. Das ist zugleich die Positivkontrolle, dass der
    Parameter ohne 32-02 nichts verengt.
  - **A**: Ordnermodus mit M4-Formel und 3 Runden (`FOLDER_MAX_ROUNDS = 3`,
    Abrufgröße wie ohne Ordner): "kein Sonderbudget".
  - **B**: 6 Runden x 100 (Stand 32-02).
  - **C**: 10 Runden x 100.
  - **D**: 12 Runden x 100; der letzte Abruf beginnt bei Offset 1100, unter
    `MAX_CONTAINER_OFFSET` 1200.
- Rohdaten in `rohdaten/`, je Abfrage eine Datei mit einer Zahl je Zeile
  (Sekunden), dazu je Lauf eine `.tsv` mit der Zusammenfassung.

## 5. Ergebnisse

Zeiten in Sekunden, n = 20 je Zeile.

| Variante | Abfrage | Limit | Treffer | isPaginated | Median | Maximum |
|---|---|---|---|---|---|---|
| Basis | ohne Ordner | 5 | 5 | true | 0,079 | 0,343 |
| Basis | Innen (ignoriert) | 5 | 5 | true | 0,057 | 0,183 |
| Basis | Einzeln (ignoriert) | 5 | 5 | true | 0,058 | 0,203 |
| Basis | ohne Ordner | 10 | 10 | true | 0,058 | 0,204 |
| Basis | Innen (ignoriert) | 10 | 10 | true | 0,059 | 0,208 |
| Basis | Einzeln (ignoriert) | 10 | 10 | true | 0,061 | 0,202 |
| A | ohne Ordner | 5 | 5 | true | 0,070 | 0,256 |
| A | Innen | 5 | **0** | false | 0,058 | 0,105 |
| A | Einzeln | 5 | **0** | false | 0,060 | 0,179 |
| A | ohne Ordner | 10 | 10 | true | 0,062 | 0,094 |
| A | Innen | 10 | **0** | false | 0,059 | 0,187 |
| A | Einzeln | 10 | **0** | false | 0,063 | 0,167 |
| B | ohne Ordner | 5 | 5 | true | 0,063 | 0,174 |
| B | Innen | 5 | **0** | false | 0,084 | 0,150 |
| B | Einzeln | 5 | **0** | false | 0,097 | 0,224 |
| B | ohne Ordner | 10 | 10 | true | 0,064 | 0,230 |
| B | Innen | 10 | **0** | false | 0,089 | 0,157 |
| B | Einzeln | 10 | **0** | false | 0,085 | 0,138 |
| C | ohne Ordner | 5 | 5 | true | 0,071 | 0,217 |
| C | Innen | 5 | **0** | false | 0,112 | 0,181 |
| C | Einzeln | 5 | **0** | false | 0,111 | 0,165 |
| C | ohne Ordner | 10 | 10 | true | 0,060 | 0,268 |
| C | Innen | 10 | **0** | false | 0,124 | 0,182 |
| C | Einzeln | 10 | **0** | false | 0,110 | 0,286 |
| D | ohne Ordner | 5 | 5 | true | 0,060 | 0,254 |
| D | Innen | 5 | 5 | true | 0,134 | 0,278 |
| D | Einzeln | 5 | 1 | false | 0,127 | 0,183 |
| D | ohne Ordner | 10 | 10 | true | 0,067 | 0,207 |
| D | Innen | 10 | 10 | true | 0,129 | 0,188 |
| D | Einzeln | 10 | 1 | false | 0,122 | 0,186 |

**Langreihe ohne Ordner.** Die Abfrage ohne Ordner läuft in A, B, C und D
durch denselben Code (die Konstanten wirken nur mit Ordnerkoordinaten), und
trotzdem streuen ihre Mediane bei `limit=10` zwischen 0,058 und 0,067 s. Mit
n = 20 ist der Unterschied von D zur Basis bei `limit=10` (+14,5 Prozent) und
bei `limit=5` (minus 23,5 Prozent) also Rauschen in beide Richtungen. Regelpunkt 3 ist
deshalb an einer längeren Reihe entschieden: Basis und D abwechselnd, je zwei
Läufe zu 50 Wiederholungen (Rohdaten `basis-lang1`, `D-lang1`, `basis-lang2`,
`D-lang2`), zusammengelegt n = 100 je Zelle.

| Fassung | Limit | n | Median | Abweichung zur Basis |
|---|---|---|---|---|
| Basis | 5 | 100 | 0,0618 | |
| D | 5 | 100 | 0,0609 | minus 1,5 Prozent |
| Basis | 10 | 100 | 0,0620 | |
| D | 10 | 100 | 0,0601 | minus 2,9 Prozent |

**Bestätigungslauf** mit der eingecheckten Fassung (Konstante 12, Kommentare
neu, Rohdaten `final`): Innen 5 und 10 Treffer, Einzeln 1, Mediane 0,126 bis
0,131 s, Maximum 0,289 s; ohne Ordner 0,077 s (`limit=5`) und 0,064 s
(`limit=10`).

Die Ordnerabfragen von D in denselben Langläufen: Innen 0,126 bis 0,133 s
Median, Einzeln 0,125 bis 0,130 s, Maximum höchstens 0,366 s, Trefferzahlen
gleich wie oben.

## 6. Urteil

- **A** (kein Sonderbudget) und **B** (6 x 100, Startwert der Recherche)
  liefern für beide Ordner eine leere Gruppe mit `isPaginated: false`, obwohl
  der Ordner Treffer hat. Das ist Pitfall 4, jetzt gemessen: Annahme A2 hält
  für die Zeit, nicht für die Trefferzahl. Mit 6 x 100 reicht der Dialog bis
  Rang 600.
- **C** (10 x 100) reicht bis Rang 1000 und verfehlt den ersten Ordnertreffer
  auf Rang 1001 um eine Stelle.
- **D** (12 x 100) erfüllt alle drei Regelpunkte: Innen 5 von 5 und 10 von 10,
  Einzeln 1 von 1; Median höchstens 0,134 s (Grenze 1,5 s), Maximum höchstens
  0,366 s (Grenze 2,5 s); ohne Ordner in der Langreihe nicht langsamer als die
  Basis.

**Gewählt: D, `FOLDER_FETCH_LIMIT = 100`, `FOLDER_MAX_ROUNDS = 12`.** Damit
reicht ein Dialoglauf im Ordnermodus bis Rang 1200, der letzte Abruf beginnt
bei Offset 1100. Die Kernzahl: zwölf Runden bis Rang 1200 in 0,134 s Median
auf dieser Maschine.

## 7. Grenzen

- Gemessen auf einem x86-Laptop. Auf einer kleinen ARM-Box mit 4 GB ist jede
  Runde langsamer; die Uhr von `SearchService` (2,5 s) beendet den Lauf dann
  früher, als die Rundenzahl erlaubt, und die Gruppe enthält weniger Treffer.
  Das ist das vorgesehene Verhalten und kein Fehler; die Abstandsreserve hier
  ist rund Faktor 18 zum Median.
- Treffer jenseits von Rang 1200 erreicht der Dialog mit D nicht. Mehr als
  eine weitere Runde gäbe der Container ohnehin nicht her: er nimmt Offsets bis
  einschließlich 1200 an (`SEARCH_OFFSET_MAX`, gespiegelt als
  `MAX_CONTAINER_OFFSET`), die tiefste Seite ist also Rang 1201 bis 1300. Ein
  Ordner, dessen Treffer alle dahinter liegen, bleibt im Dialog leer. Der Ausweg
  wäre die Erlaubnisliste über `file_id` (widerspricht D-32-06) und ist nicht
  Teil dieser Phase.
- Ein Ordner ohne jeden Treffer kostet im Ordnermodus bis zu zwölf
  Container-Aufrufe; die Zeiten von C (zehn leere Runden, 0,11 bis 0,12 s
  Median) zeigen die Größenordnung.
- Die Zeiten sind ganze HTTP-Anfragen inklusive Nextcloud-Start je Anfrage und
  Prüfung des App-Passworts; die Frist von 2,5 s zählt dagegen erst ab dem
  Beginn von `SearchService::run()`.

## 8. Aufräumen

`/Messung32` per WebDAV gelöscht, Papierkorb mit `occ trashbin:cleanup
testuser` geleert, App-Passwort `messung32` entfernt. Belege in
`.planning/phases/32-filter-in-der-unified-search/32-03-SUMMARY.md`.
