---
phase: 09-eigene-ergebnisseite
audited: 2026-09-09
diff: a99271d..0175b56
files_reviewed: 58
findings:
  critical: 0
  high: 0
  medium: 3
  low: 6
  total: 9
status: issues_found
fix_run: 2026-09-09
fix_commits: 0c53c4d, 52db222, 0175b56
fixed: [M-01, M-02, M-03, L-03]
still_open: []
---

# Phase 09: Security-, Bug- und Performance-Audit

**Umfang:** `git diff a99271d..0175b56`, 58 Dateien, 8624 Zeilen dazu, 914 weg,
42 Commits. Produktiver Anteil sind 25 Dateien unter `php/` (4752 dazu, 819
weg), darunter eine neue Nutzerroute, ein neuer geteilter Dienst, ein neues
Template mit Stil und Skript und vier Übersetzungskataloge. Der Rest sind
Gates, Tests, ein CI-Job, Messdaten und Doku.

Dieser Bericht ist nach dem Muster von
`.planning/phases/08-deutsche-komposita-ohne-behelf/08-AUDIT.md` geschrieben und
liegt nach der Owner-Regel vom 15.08.2026 vor dem Phasenabschluss. Er ist der
erste Auditbericht unter `docs/audits/`; die früheren liegen bei ihren Phasen.

**Was gegengeprüft wurde, nicht nur gelesen:**

- Volle Python-Suite lokal: **1792 passed, 15 skipped in 173,39 s**. `ruff check`
  und `ruff format --check` über `backend` (119 Dateien) und über `scripts`
  (10 Dateien), `pyright` (0 errors, 0 warnings), `vulture` (still): alle grün.
- `php -l` über alle 46 PHP-Dateien der installierten App im Container: keine
  Meldung.
- `scripts/dev/validate_info_xml.sh php/appinfo/info.xml`: Transform und Schema
  grün gegen den gepinnten appstore-Commit `eda850ba`.
- Die zwei nachgezogenen Vertragszeilen gegen den gebauten Zustand: die
  Zweizeiligkeit der Trefferzeile steht in `php/templates/search.php` Zeile 198
  bis 208 so, wie die 09-UI-SPEC sie jetzt beschreibt.
- **22 Abnahme-Sichtproben an der laufenden Instanz**, 16 maschinell gefahren, 6
  vom Owner abgenommen. Das Protokoll steht im Summary von Plan 09-08.
- Der Testumzug aus Plan 09-03 maschinell gegengelesen: 14 alte Fälle, 7 davon
  heute unverändert vorhanden, 7 umbenannt, jedes Umbenennungsziel existiert.
- Ein Performance-Nachlauf von fünf Reihen mit je 20 Wiederholungen gegen die
  fertige Seitenroute, Rohdaten in
  `docs/measurements/2026-09-seitenbudget/raw/nachlauf-*.txt`.
- Die Abhängigkeitsdateien im Diff: `git diff --name-only` über
  `package.json`, `requirements*`, `pyproject.toml`, `uv.lock`, `composer.*` und
  `Dockerfile` liefert **keine Zeile**. Diese Phase installiert kein Paket.

**Was nicht gefahren werden konnte, und warum es keine Lücke im Urteil ist:**

- **PHPUnit.** Auf dieser Maschine gibt es kein PHP außer dem im Container und
  keine `require-dev`-Abhängigkeiten; `docs/testing.md` sagt genau das. Die 143
  PHP-Testfälle (davon 19 in `PageControllerTest`, 21 in `SearchServiceTest`, 11
  in `HighlighterTest`) laufen im Job `php.yml`. Ersatz in dieser Phase waren
  die Stand-in-Proben der Pläne 09-03 bis 09-06 und, für diesen Bericht, die
  Sichtproben am echten Rendering.
- **`integration.yml`** braucht eine frische Nextcloud, den Groupfolders-Aufbau
  und den Crawl. Der Paritätsjob dieser Phase ist lokal am Rumpf seiner Schritte
  geprüft (Plan 09-07), sein erster Lauf gehört an den Push.

---

## 1. Sicherheit

**Kein Befund ab MEDIUM.** Geprüft gegen die ASVS-Kategorien aus dem Abschnitt
"Security Domain" der `09-RESEARCH.md`, mit Blick auf die vier Flächen, die
diese Phase neu oder verändert hat.

### V3, die Nutzerroute ohne Tokenprüfung

`PageController::index()` trägt genau drei Attribute: `FrontpageRoute(GET, '/')`,
`NoAdminRequired`, `NoCSRFRequired`. Der Diff über `php/lib/**` enthält keine
weitere Routendeklaration, kein `PublicPage` und kein `ExAppRequired`.

`NoCSRFRequired` ist auf einer GET-Route ohne Zustandsänderung die richtige
Entscheidung und keine Bequemlichkeit: ohne sie scheitert jedes Lesezeichen,
jede Zurück-Navigation und der Link aus dem Suchdialog. Gegengeprüft, dass die
Route wirklich nichts schreibt: sie ruft ausschließlich `SearchService::run()`,
und der liest. Sichtprobe 6 hat die andere Hälfte belegt, eine tiefe Adresse
ohne `requesttoken` antwortet mit 200 und ohne CSRF-Fehler.

Die Routenklasse selbst hält `test_php_trust_boundary.py` (21 Fälle, Gate B),
mit der dritten Klasse "Nutzerseite" und je einem sauberen und einem
schmutzigen Selbstmuster. **T-09-06** und **T-09-14** sind damit an einem Gate
und nicht an einer Verabredung.

### V4, die Berechtigungsentscheidung, die Kernkategorie

Die Recheck-Schleife lebt genau einmal, in `SearchService`. `test_php_acl_boundary.py`
(8 Fälle) zählt die Aufrufstellen je Frage. Der Controller bringt keine eigene
Entscheidung mit, sondern nur Zahlen: `SearchCaps` mit Seitengröße, Runden,
Overfetch, zwei Recheck-Deckeln, Wanduhr und Per-Call-Deckel.

Am schärfsten belegt ist das nicht durch ein Gate, sondern durch Sichtprobe 8 an
zwei echten Konten: `testuser` sieht 25 Treffer für "Kündigung", `kollegin` sieht
für "Genehmigung" **genau eine** Trefferzeile, `fileid` 190, und das ist genau
die eine Datei, die ihr geteilt wurde (`file_source` 190 in der Share-API).
Dateiname und Pfad auf ihrer Seite kommen aus ihrem eigenen Node: dort steht
`09-bescheid.pdf` und nicht `corpus/09-bescheid.pdf` wie bei `testuser`.
**T-09-03**, **T-09-04**.

### V5, Eingabeprüfung des Adressformats und Ausgabe jedes Werts

`cursorPath()` prüft Länge gegen `page`, Ziffernform, Startwert 0 und strenge
Monotonie und fällt bei jeder Abweichung auf `[0]`. Sieben Varianten live
gefahren (zu hoch, Start nicht 0, falsche Länge, Komma statt Punkt, fallend,
`page=99`, `page=-1`): jedes Mal still Seite 1, HTTP 200, kein Fehlerblock und
**kein einziger Logeintrag**. **T-09-09**.

Ausgabeseitig: `grep -c print_unescaped` über `search.php` ist 0, und die Datei
enthält 45 `p()`-Aufrufe. Ein Suchbegriff `<script>alert(1)</script>Genehmigung`
erscheint an allen drei Stellen escaped, das Dokument enthält kein einziges
unescaped `<script>alert`. 300 Zeichen werden auf 255 gekürzt, `maxlength` steht
auf 255. Ein Suchbegriff in ungültigem UTF-8 wird wie kein Suchbegriff behandelt,
ohne Fehlermeldung. Die Markierung sitzt zeichengenau: `<mark>` umschließt
`Grundstücksverkehrsgenehmigung` und `Kündigungsfrist`, die UTF-8-Bytes im
Dokument sind intakt (`c3 bc` innerhalb des Elements). **T-09-01**, **T-09-02**.

### V7, die Logzeilen

Alle sieben in dieser Phase neuen Logaufrufe tragen einen statischen Satz. Die
Kontextfelder sind `reason` (ein Code aus der geschlossenen Liste von
`SearchOutcome`), `exception` (das Framework-Objekt) und im Driftfall die zwei
Versionen, die eine Administration lesen darf. Kein Suchbegriff, kein Dateiname,
kein Pfad, keine Nutzerkennung. **T-09-08**.

Ein Fund am Rande, der wie eine Ausnahme aussieht und keine ist: `ExAppService`
loggt zweimal `['path' => $path]`. Das ist der **Container-Routenpfad**
(`/search`, `/snippets`), nicht ein Dateipfad, und beide Zeilen sind älter als
diese Phase.

### Die erste Sonderfrage: erlaubt die Seite Rückschlüsse auf verworfene Kandidaten?

Am Quelltext: keine Gesamttrefferzahl, keine Seitenanzahl, kein Sprung zur
letzten Seite, keine Erklärung für eine kurze Seite, kein Satz über Rechte. Die
einzige Zahl der Seite ist die Seitenmarke, und die kommt aus der Adresse des
Nutzers.

An der Instanz, als eigene Sichtprobe (die zweite der beiden neuen): eine Suche
mit überwiegend genehmigten Kandidaten gegen eine mit überwiegend verworfenen.
`testuser` bekommt 25 Zeilen mit Pager, `kollegin` eine Zeile ohne Pager, und
eine Suche nach `entfernt|removed|weitere Treffer|von N|N Treffer` über ihr
Dokument liefert nichts. **T-09-05 hält.**

Eine Restaussage bleibt und ist als L-04 unten benannt: der Weiter-Knopf hängt an
`hasMore` des Containers, also an einer Aussage über **Kandidaten**. Wer klickt
und auf einer Seite mit weniger Treffern landet, kann daraus schließen, dass es
mehr Kandidaten gab als genehmigte Treffer. Die Aussage ist ein grober Aggregat
ohne Bezug auf eine Datei, der Dialog gibt sie über seinen Nachlade-Knopf seit
Phase 4 genauso, und die 09-UI-SPEC nimmt sie in der Zeile "Kurze Seite"
ausdrücklich in Kauf.

### Die zweite Sonderfrage: bindet der angehobene Per-Call-Deckel einen Prozess länger?

**Nein, und zwar aus zwei Gründen statt aus einem.**

Erstens wurde nichts angehoben: `PAGE_REQUEST_TIMEOUT_SECONDS` ist 1,5 Sekunden,
dieselbe Zahl wie beim Dialog, weil die Messung von Plan 09-01 einen
Kandidatenaufruf mit `limit=100` bei einem p95 von 0,022 s fand und die
Aufrundungsregel deshalb an ihrer Untergrenze landete. Der Gewinn der Phase ist,
dass die Seite eine **eigene** Konstante hat, nicht dass sie größer ist.

Zweitens kann der Deckel die Wanduhr nicht überziehen. `SearchService` reicht
`$this->secondsLeft($deadline)` in jeden Aufruf, und `ExAppService::call()`
rechnet `min($ceilingSeconds, $secondsLeft)` (`SearchService.php` Zeile 213 bis
222 für den Kandidatenaufruf, Zeile 383 bis 388 für den Snippet-Aufruf). Die
Obergrenze einer Anfrage ist damit `PAGE_BUDGET_SECONDS` = 3,0 Sekunden plus die
Restlaufzeit eines Aufrufs, der knapp vor der Frist begonnen hat, und nicht
Runden mal Deckel. Gemessen liegt der p95 bei 0,122 Sekunden. **T-09-07**,
**T-09-11**.

### Lieferkette

`git diff --name-only a99271d..0175b56` enthält keine Abhängigkeitsdatei. Kein
`npm install`, kein `pip install`, kein `composer require`, keine `package.json`
im Repositorium. Das neue Fremdmaterial der Phase sind drei
Symbolpfaddaten aus dem in `THIRD-PARTY.md` gepinnten MDI-Commit
`9e04201d...`, gegengeprüft in Plan 09-06 (zwölf Pfaddaten, `diff` über beide
sortierten Listen, kein Unterschied), plus `php/img/app.svg` als byte-identische
Kopie einer bereits attribuierten Datei. **T-09-SC**, **T-09-23**.

### Threat-Register der Phase, Zeile für Zeile

Jeder Threat aus den Threat Models der Pläne 09-01 bis 09-08, namentlich
abgehakt. "umgesetzt" heißt: es gibt einen Test, ein Gate oder eine protokollierte
Sichtprobe dafür.

| Threat | Plan | Verdikt | Wo es hängt |
|---|---|---|---|
| T-09-01 | 09-04, 09-05 | umgesetzt | `PlainText::bounded`, Ausgabe nur über `p()`, Sichtprobe 14 |
| T-09-02 | 09-04, 09-05 | umgesetzt | `Highlighter::segments` gibt Textstücke, `mark` ist ein Literal des Templates, `HighlighterTest` 11 Fälle, Sichtprobe 15 |
| T-09-03 | 09-03 | umgesetzt | Titel, Pfad und Mimetype aus dem bestätigten Node, `SearchServiceTest`, Sichtprobe 8 |
| T-09-04 | 09-03, 09-04, 09-06, 09-07 | umgesetzt | eine Schleife in `SearchService`, `test_php_acl_boundary.py`, dritter Vergleich im Paritätsjob |
| T-09-05 | 09-05, 09-08 | umgesetzt | keine Zahl und kein Satz, Sichtprobe 12 und die zweite neue Probe; Restaussage als L-04 benannt |
| T-09-06 | 09-02, 09-04 | umgesetzt | Gate B, `FORBIDDEN_ON_USER_PAGE_ROUTE` enthält `ExAppRequired` |
| T-09-07 | 09-03, 09-04 | umgesetzt | `MAX_PAGE` 20, `MAX_CONTAINER_OFFSET` 1200 vor jedem Aufruf, live an 1200 und 1201 gefahren |
| T-09-08 | 09-03, 09-04 | umgesetzt | sieben statische Logsätze, Kontext ohne Nutzerdaten |
| T-09-09 (Spoofing/CSRF) | 09-04 | akzeptiert | GET-only, kein Zustandswechsel; ohne `NoCSRFRequired` gibt es Erfolgskriterium 3 nicht |
| T-09-09 (Tampering `cursors`) | 09-04 | umgesetzt | `cursorPath()`, sieben Varianten live, `PageControllerTest` |
| T-09-10 | 09-07 | akzeptiert | Wegwerf-Konten, Behälter im Arbeitsverzeichnis des Runners |
| T-09-11 | 09-01 | umgesetzt | benannte Konstante mit Messdatum, plus `min(ceiling, secondsLeft)` |
| T-09-12 | 09-01 | umgesetzt | der Messbericht nennt Laufzeiten und Suchbegriffe des Testkorpus, keine Nutzerdaten |
| T-09-13 | 09-01 | umgesetzt | `ExAppServiceTest` liest die Konstanten über `constantFloat()` statt sie abzuschreiben |
| T-09-14 | 09-02 | umgesetzt | `USER_PAGE_REQUIRED` verlangt beide Attribute, mit schmutzigem Muster |
| T-09-15 | 09-02 | umgesetzt | jede neue Regel hat ein sauberes und ein schmutziges Selbstmuster; für den Fix M-01 dieses Berichts ebenfalls |
| T-09-16 | 09-02 | umgesetzt | textlicher Scan über `php/lib/**/*.php`, `IInAppSearch` kommt nicht vor |
| T-09-17 | 09-03, 09-08 | umgesetzt | eigener Grund `FAILURE_OFFSET_CEILING`, live jenseits der Decke: Hinweisbanner und kein Fehlerblock |
| T-09-18 | 09-03 | umgesetzt | `test_search_limits_lockstep.py`, 9 Fälle |
| T-09-19 | 09-05 | umgesetzt | der Speicherwert steuert nur eine Klasse an einer vorhandenen Zeile |
| T-09-20 | 09-05 | umgesetzt | beide Speicherzugriffe in `try`/`catch`, kein Polling (`test_the_page_script_does_no_polling`) |
| T-09-21 | 09-05 | akzeptiert | `no-store` bleibt; die Folge für Stufe 2 trägt Stufe 3, und die 09-UI-SPEC sagt das jetzt auch |
| T-09-22 | 09-06, 09-07 | umgesetzt | kein `fileId`-Attribut, Erkennung an der `resourceUrl`, zwei Testfälle, live gegen die OCS-Antwort gesehen |
| T-09-23 | 09-06 | umgesetzt | byte-identische Kopie, zwölf Pfaddaten gegen den gepinnten Commit |
| T-09-24 | 09-06 | umgesetzt | Existenzprüfung über sechs Pfade |
| T-09-25 | 09-06 | umgesetzt | Store-Pfad gefahren, nicht nur die Position im Diff |
| T-09-26 | 09-07 | umgesetzt | drei Fälle enden als unlesbare Antwort, negative Probe im Job |
| T-09-27 | 09-07 | akzeptiert | rund 44 zusätzliche Anfragen gegen eine Grenze von 30 Minuten |
| T-09-28 | 09-08 | umgesetzt | 22 Zeilen Protokoll, jede mit einem Ergebnis; die sechs Augen-Proben sind mit Datum als Owner-Abnahme geführt |
| T-09-29 | 09-08 | akzeptiert | siehe Performance, Abschnitt 3, und L-05 |
| T-09-30 | 09-08 | umgesetzt | Zuordnungstabelle maschinell gegengelesen, kein verlorener Fall |
| T-09-SC | alle | akzeptiert | keine Abhängigkeitsdatei im Diff der Phase |

---

## 2. Bugs

Drei Befunde, zwei davon MEDIUM und in dieser Phase gefixt.

### M-01: Der Leerzustand sprach über den Fehlerblock hinweg (GEFIXT)

**Dateien:** `php/templates/search.php` Zeile 219 (Fassung vor `52db222`)

**Gefunden in:** Abnahme-Sichtprobe 9, 10 und der neuen Probe jenseits der
Offset-Decke.

**Fehlerszenario:** Block 4 rendert, sobald die Trefferliste leer ist. Bei
gestopptem Backend stand deshalb auf einem Bildschirm:

```
Die Suche antwortet gerade nicht
Findling konnte sein Backend nicht erreichen. Ihre Dateien sind unveraendert.
Versuchen Sie es gleich noch einmal ...

Keine Datei enthaelt "Genehmigung"
Versuchen Sie ein anderes Wort, ein Teilwort oder pruefen Sie die Schreibweise.
```

Der erste Block bittet zu warten, der zweite schickt den Nutzer den Suchbegriff
umschreiben, und der zweite Satz ist unwahr: es hat keine Suche gegeben. Dasselbe
Bild jenseits der Offset-Decke, dort unter dem Hinweis "Es gibt weitere Treffer",
und bei Versionsdrift. Das Zustands-Inventar der 09-UI-SPEC sagt für "Backend
stumm" ausdrücklich "**Keine leere Liste**".

Erreichbar ohne Handarbeit: gestopptes Backend, und die Decke nach etwa zwölf
Klicks auf "Nächste Seite" bei niedriger Genehmigungsquote. Deshalb MEDIUM und
nicht LOW.

**Fix:** `52db222`. Eine Entscheidung, `$showEmpty`, neben der Bannerentscheidung,
von der sie abhängt. Der Leerzustand **ohne** Suchbegriff bleibt unter jedem
Banner stehen: er ist eine Einladung und nie eine Behauptung.

**Test:** `test_the_empty_state_of_the_page_does_not_speak_over_a_banner` in
`backend/tests/test_admin_ui_contract.py`. Gegen das Template von `0c53c4d`
gefahren: zwei Befunde, rot. Gegen das heutige: grün. Dazu zwei schmutzige
Selbstmuster, das nackte `else` und die halbe Entscheidung, die den Hinweis
vergisst.

**Nachgeprüft an der Instanz, alle fünf Zustände:** Treffer 25 Zeilen ohne
Leerzustand, echtes Nullergebnis mit seiner Überschrift, ohne Suchbegriff die
Einladung, jenseits der Decke der Hinweis allein, Versionsdrift der Fehlerblock
allein.

### M-02: Wer "Deutsch (Sie)" gewählt hatte, las die ganze App auf Englisch (GEFIXT)

**Dateien:** `php/l10n/` (nur `de.js` und `de.json`)

**Gefunden in:** Abnahme-Sichtprobe 20.

**Fehlerszenario:** Nextcloud führt `de` und `de_DE` als zwei Sprachen und
liefert im Core für jede einen Katalog (`core/l10n/de.json` **und**
`core/l10n/de_DE.json`). Diese App lieferte nur `de`. Ein Nutzer auf `de_DE` bekam
jede Zeichenkette der Ergebnisseite **und** der Verwaltungsseite im englischen
Quellstring. Live gegengeprüft: `lang=de_DE` liefert `Search term`, `lang=de`
liefert `Suchbegriff`. Die Instanz hatte für `testuser` genau `de_DE` gesetzt,
was der Grund ist, dass die Sichtprobe darüber stolperte.

Nicht durch diese Phase verursacht, sondern seit Phase 4 wahr, und trotzdem
MEDIUM: der Owner hat am 09.09.2026 entschieden, dass es in dieser Phase behoben
wird und nicht in Phase 11.

**Fix:** `0175b56`. `php/l10n/de_DE.json` und `de_DE.js` mit denselben Worten,
im Index byte-identisch mit ihren `de`-Zwillingen (gleicher Blob-Hash). Die
Begründung, warum dieselben Worte und nicht zwei Fassungen: jeder Satz dieses
Katalogs ist in der Sie-Form geschrieben, gehört also unter `de_DE` und ist unter
`de` höchstens eine Spur zu höflich. Ein zweiter, duzender Katalog wäre eine
Textrunde, die niemand bestellt hat, und die Hälfte davon wäre in einer Phase
auseinandergelaufen.

**Test:** `test_the_german_catalogue_covers_both_german_language_codes`. Zweimal
rot gesehen: einmal mit gelöschter `de_DE.json`, einmal mit einem geänderten
Wert. Vergleicht Text und Schlüsselmengen aller vier Dateien und die Zahl 173.

**Nachgeprüft an der Instanz:** `testuser` auf `de_DE` bekommt die Seite
vollständig deutsch, 25 Trefferzeilen, `lang="de-DE"`, kein englischer Rest.

**Nebenwirkung, die benannt gehört:** `docs/store-listing.md` sagt, `de_DE` sei
kein gültiger Sprachcode. Das gilt für die Store-Texte in `info.xml` und **nicht**
für die Kataloge, und genau dieser Satz steht jetzt dort, weil sonst jemand die
richtige Datei aus dem richtig klingenden Grund löscht.

### Die Randfälle der Zahlen, live gefahren

| Fall | Ergebnis |
|---|---|
| Seite 1 ohne Parameter | 25 Zeilen, "Seite 1", Weiter ja, Zurück nein |
| leerer Cursorpfad, `page=1` | wie Seite 1 |
| `cursors=0`, `page=1` | wie Seite 1 |
| Cursor **genau** auf der Decke (1200) | Suche findet statt, 0 Treffer, ehrlicher Leerzustand. Die Prüfung ist `> 1200`, also ist 1200 erlaubt: richtig, der Container nimmt Offsets bis 1200 |
| Cursor **genau über** der Decke (1201) | Hinweisbanner zur Obergrenze, kein Fehlerblock, kein Leerzustand mehr (nach M-01) |
| Seite 20, gültiger Pfad | 25 Zeilen, "Seite 20", kein Weiter |
| `page=21` (über `MAX_PAGE`) | still Seite 1, derselbe Suchbegriff |
| genau 1 Treffer | eine Zeile, kein Pager |
| genau 0 Treffer | Leerzustand mit Suchbegriff und drei Schritten |
| Kanarienvogel-Pfad | eine Zeile, 3 von 3 Läufen, 40 bis 70 ms |
| zwölf Seiten bis zum Ende geblättert | 12 mal 25 Zeilen, die letzte Seite ohne Weiter-Knopf, 300 Ids, keine doppelt |
| Filter "nur Dateinamen" | 0 Treffer für einen Begriff, der nur im Inhalt steht: richtig |

Die Cursor wachsen genau um 25 pro Seite (`0.25.50...`), weil dieser Nutzer alle
Kandidaten genehmigt bekommt. Der Fall "Weiter-Knopf führt auf eine leere Seite"
ist mit diesem Korpus nicht herstellbar: wo `hasMore` falsch ist, erscheint kein
Weiter, und wo es wahr ist, waren alle 25 genehmigt. Er bleibt als L-06 benannt.

### T-09-30: kein Testfall ist beim Umzug verloren gegangen

`ProviderTest` hatte vor `d814157` **14** Fälle. Heute stehen **16** in
`ProviderTest` und **21** in `SearchServiceTest`. Die Zuordnungstabelle aus
`09-03-SUMMARY.md` wurde maschinell gegen die beiden Klassen gehalten: 7 alte
Namen existieren unverändert, 7 sind umbenannt, jedes der 16 in der Tabelle
genannten Ziele existiert, und **kein** alter Name fehlt ohne Erklärung.

---

## 3. Performance

Nachlauf gegen die fertige Seitenroute, fünf Reihen mit je 20 Wiederholungen,
dieselbe Rangregel wie im Bericht von Plan 09-01. Rohdaten in
`docs/measurements/2026-09-seitenbudget/raw/nachlauf-*.txt`, ausführliche
Fassung als Abschnitt 6.3 desselben Berichts.

| Reihe | n | min | p50 | **p95** | max |
|---|---|---|---|---|---|
| Seite mit Suche, Sitzung | 20 | 0,090 s | 0,104 s | **0,122 s** | 0,125 s |
| Seite mit Suche, Basic-Auth | 20 | 0,386 s | 0,419 s | **0,445 s** | 0,457 s |
| Dialogweg OCS, Basic-Auth, `limit=100` | 20 | 0,474 s | 0,507 s | **0,538 s** | 0,540 s |
| Seite ohne Suche, Sitzung | 20 | 0,033 s | 0,044 s | **0,055 s** | 0,066 s |
| Seite ohne Suche, Basic-Auth | 20 | 0,327 s | 0,343 s | **0,373 s** | 0,390 s |

**Das Budget hält.** `PAGE_BUDGET_SECONDS` ist 3,0 Sekunden, die Vorhersage aus
`docs/measurements/2026-09-seitenbudget/` (p95 der Reihe C von 0,712 s plus die
Hälfte, aufgerundet). Nachgemessen liegt der p95 der Seitenroute auf dem Weg,
den ein angemeldeter Nutzer wirklich geht, bei **0,122 Sekunden**, also bei vier
Prozent des Budgets. Mit den Kosten der Basic-Auth, die ein Browser nicht
bezahlt, sind es 15 Prozent.

**Die Erwartung der Recherche ist widerlegt, und zwar in die andere Richtung.**
Erwartet war "wie der Dialog, plus ein Viertel". Gleich gemessen ist die Seite am
p95 um 0,093 Sekunden **schneller** als der Dialogweg mit `limit=100`, weil
`$fetchLimit` in `SearchService` auf das gedeckelt ist, was das Recheck-Budget
prüfen kann.

### M-03: Der Messbericht der Phase schrieb 0,318 Sekunden Passwortprüfung dem Rechteabgleich zu (GEFIXT)

**Datei:** `docs/measurements/2026-09-seitenbudget/README.md` Abschnitt 5.2

**Fehlerszenario:** Abschnitt 5.2 schließt aus 0,65 s Gesamtzeit und 0,07 s
Container-Zeit, "rund neun Zehntel der Zeit" lägen auf der PHP-Seite, und zählt
auf: Anfragebau, Vorfilter, Rechteabgleich Datei für Datei, Zusammensetzen der
Antwort. Die Rechnung stimmt, die Zuordnung nicht: alle Reihen dieses Berichts
sind mit `curl -u` gemessen, und Nextcloud prüft dabei je Anfrage das Passwort.
Die beiden neuen Reihen ohne Suchbegriff trennen das, weil sie dieselbe Adresse
ohne einen einzigen Container-Aufruf und ohne Recheck abrufen: 0,055 s mit
Sitzung gegen 0,373 s mit Basic-Auth. **Die Differenz von 0,318 s ist der Preis
der Messmethode.** Der wirkliche Anteil der ganzen Suche, beide Container-Aufrufe
plus Recheck von 25 genehmigten Treffern plus Rendern, ist 0,067 s am p95.

MEDIUM und nicht LOW, weil Phase 10 Zahl für Zahl gegen diesen Bericht vergleicht
und eine falsche Zuordnung genau die Art Satz ist, die in den nächsten Bericht
abgeschrieben wird.

**Fix:** Abschnitt 6.3 im Messbericht, mit den fünf Reihen, der Korrektur an 5.2
und dem Satz, dass ein Vergleich zwischen zwei Berichten nur bei gleichem
Anmeldeweg zulässig ist. **Ohne Test**, und das ist der Grund: der Befund ist eine
Aussage in einem Messbericht, kein Verhalten von Code. Es gibt nichts, was rot
werden könnte. Dasselbe Vorgehen wie bei M-04 und M-06 des Phase-8-Audits.

### T-09-29, der volle Vektorscan je Anzeigeseite

Bleibt akzeptiert, und diese Phase konnte ihn nicht messen: auf dieser Instanz
gibt es keine `vectors.db`, der Alltagsstack fährt das Backend als Host-Prozess
ohne Modell, und `one_round()` schaltet die Vektorseite nur ein, wenn
`side.vectors is not None`. Der zweiwortige Fall ist hier also der lexikalische
und nicht der hybride, wie Abschnitt 5.1 des Messberichts schon feststellte.
Die Zahlen für den hybriden Fall stehen in
`docs/measurements/2026-09-05-semantiklauf-m7g/` (p95 524 ms ohne Nebenlast,
1129 ms mit) und liegen ebenfalls weit unter 3,0 Sekunden.

Die Eigenschaft selbst ist unverändert: wer blättert, bezahlt pro Anzeigeseite
einen Vektorlauf, weil `SEARCH_VECTOR_DEPTH` nicht am Limit hängt. Diese Phase
verschärft das nicht, sie ruft dieselben zwei Container-Routen wie der Dialog.
**Eine Maßnahme folgt daraus nicht**, und die Begründung ist die Reihenfolge des
Milestones: die Vergleichsmessung der Phase 10 läuft auf der AWS-Box mit vollem
Vektorbestand und 51.961 Dokumenten. Wenn eine Maßnahme begründbar wird, dann
mit deren Zahlen und nicht mit denen einer Instanz ohne Vektoren.

---

## 4. LOW-Befunde, dokumentiert entschieden

- **L-01 (zwei `h1` im Dokument): OFFEN, akzeptiert.** Der Core-Rahmen setzt auf
  jeder App-Seite ein unsichtbares `<h1>Nextcloud</h1>`, unsere ist die zweite.
  Der Vertrag sagt "Genau eine `h1`" und meint den Inhaltsbereich. Das ist die
  Bauweise jeder Nextcloud-App-Seite, eine Änderung wäre ein Eingriff in den
  Core-Rahmen, und der Owner hat den Befund am 09.09.2026 als LOW akzeptiert.
  Wiedervorlage: die Barrierefreiheitsprüfung der Phase 11.
- **L-02 (`docs/certificates.md` nennt 67 Archiveinträge): OFFEN.** Die Zahl ist
  als "Measured" ausgewiesen und stammt aus einem Release-Lauf vor den Phasen 5
  bis 9; heute liegen 59 Dateien im Staging-Baum, und die zwei neuen Kataloge
  machen es um zwei staler. Sie wird von keinem Test gehalten. Eine geratene Zahl
  hineinzuschreiben wäre schlechter als eine erkennbar alte: der Release-Lauf
  druckt die richtige. Wiedervorlage: Phase 11, beim ersten Paketbau.
- **L-03 (der verlangsamte Stub band nur auf 127.0.0.1): GEFIXT** in `0c53c4d`.
  Aus dem Nextcloud-Container war er unerreichbar, also zeigte Sichtprobe 10 den
  Fehlerblock eines abwesenden Backends und belegte damit Sichtprobe 9 zum
  zweiten Mal statt Sichtprobe 10 zum ersten. `FINDLING_SLOW_BACKEND_HOST` mit
  dem alten Standard, damit der CI-Schritt seine Bindung behält.
- **L-04 (der Weiter-Knopf hängt an `hasMore`, also an Kandidaten): OFFEN,
  akzeptiert.** Siehe Abschnitt 1. Grobes Aggregat, kein Bezug auf eine Datei,
  der Dialog gibt dasselbe Signal, und die 09-UI-SPEC nimmt es in der Zeile
  "Kurze Seite" ausdrücklich in Kauf. Wiedervorlage: dort, falls die Paginierung
  je eine Gesamtzahl bekommen soll, was sie nach demselben Vertrag nicht darf.
- **L-05 (ein Indexlauf kann eine Suche in den Fehlerblock schicken): OFFEN.**
  Einmal beobachtet in dieser Sitzung, unter etwa 45 Seitenabrufen, zeitgleich mit
  einem Durchgang, der gerade ein Dokument einbuchte; das Nextcloud-Log sagt
  "backend unreachable", drei Wiederholungen danach antworteten in 40 bis 70 ms.
  Die Ursache ist im Backend dokumentiert und älter als diese Phase: `run_once()`
  öffnet SQLite, Wortliste und Index auf dem Loop, und der Modulkommentar sagt
  selbst, dass `/heartbeat` in dieser Zeit nicht antwortet. Der Dialog ist genauso
  betroffen. Diese Phase hat die Fläche nicht verändert, und ein Fix wäre eine
  Änderung am Worker-Loop, also ein eigener Plan. Wiedervorlage: Phase 11,
  Launch-Härtung, Abschnitt Ressourcengrenzen.
- **L-06 (der Leerzustand nennt die ganze Suche, auch wenn nur diese Seite leer
  ist): OFFEN.** Wer auf einer späteren Seite landet, auf der der Recheck nichts
  genehmigt hat, liest "Keine Datei enthält X", obwohl Seite 1 Treffer hatte. Mit
  diesem Korpus nicht herstellbar (siehe Abschnitt 2). Ein eigener Satz dafür wäre
  ein neuer Eintrag in einer geschlossenen Copy-Tabelle und müsste erklären, warum
  eine Seite leer ist, ohne über verworfene Kandidaten zu sprechen: genau die
  Aussage, die T-09-05 verbietet. Deshalb bewusst offen. Wiedervorlage: Phase 11,
  falls die Copy-Tabelle ohnehin aufgeht.

---

## 5. Was ausdrücklich in Ordnung ist

Damit der Bericht nicht nur die Löcher zeigt:

- **Die Sicherheitsgrenze ist eine geblieben.** Eine Recheck-Schleife, ein
  Vorfilter, ein Gate, das die Aufrufstellen zählt, und ein Paritätsjob, der
  seit Plan 09-07 drei Mengen statt zwei vergleicht. Die Seite bringt keine
  eigene Entscheidung mit, nur Zahlen.
- **Die Zahlen der Phase sind gemessen und nicht geraten.** `PAGE_SIZE` 25 aus
  `MAX_LIMIT` 100, `MAX_PAGE` 20, `MAX_CONTAINER_OFFSET` 1200 mit Lockstep-Gate
  gegen die Container-Konstante, `PAGE_BUDGET_SECONDS` 3,0 und
  `PAGE_REQUEST_TIMEOUT_SECONDS` 1,5 mit Messbericht und Datum im Kommentar.
- **Die Gates können rot werden.** Jede neue Regel dieser Phase trägt ein
  schmutziges Selbstmuster im selben Test, und für die beiden Fixes dieses
  Berichts wurde das Rot nicht behauptet, sondern hergestellt: einmal gegen das
  Template von `0c53c4d`, zweimal gegen eine entfernte und eine geänderte
  Katalogdatei.
- **Kein Debug-Rest, kein Geheimnis, kein auskommentierter Code** in den 4752
  neuen Zeilen unter `php/`. Kein `var_dump`, kein `error_log`, kein `console.log`
  im Seitenskript.
- **Die Sichtproben haben mehr gefunden als die Gates.** Von den drei
  MEDIUM-Befunden dieses Berichts kommen zwei aus dem Sichtprobenprotokoll und
  keiner aus einem Test. Das ist das Argument für den Aufwand, eine Phase an einer
  laufenden Instanz abzunehmen, und es gehört in die Planung der Phase 11.
- **Der Dev-Bestand indexiert wieder.** DI-09-05 sagte, die lokale Instanz
  indexiere nicht; die Ursache war ein Artefakt aus der Zeit vor Plan 06.1-17
  (`de.txt` statt `de-full.txt` in `.dev/storage/dict/`), das in jedem Durchgang
  einen `FileNotFoundError` erzeugte. Nach dem Nachziehen: 438 indexiert, 23
  gescheitert (die OCR-Dateien, kein `tesseract` auf dem Host), 10 übersprungen.
  Kein Repositoriumsstand war betroffen.

**Eine Beobachtung zur Probenhygiene, kein Befund:**
`occ config:app:delete` erreichte den Webprozess nicht sofort, `occ config:app:set`
schon. Wer die Drift-Sichtprobe nachfährt, setzt den Schlüssel danach auf leer und
wartet ein paar Sekunden, sonst zeigt die Instanz einen Fehlerblock über eine
Drift, die es nicht mehr gibt.

---

_Auditiert: 2026-09-09_
_Diff: a99271d..0175b56, 58 Dateien, 42 Commits_
_Suite zur Prüfzeit: 1792 passed, 15 skipped, 173,39 s_
_Fix-Lauf: 2026-09-09, Commits 0c53c4d, 52db222, 0175b56_
