---
phase: 04-admin-sichtbarkeit-und-diagnose
plan: 05
subsystem: api
tags: [fastapi, pydantic, sqlite, php, nextcloud, l10n, vanilla-js, ocr]

# Dependency graph
requires:
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "AdminViewService::overview() mit coverage-Teilbaum, ScanStatsService::totals() mit pdfSeen, ExAppService::adminGet, Block 1 der Admin-Seite"
  - phase: 02-indexkern-und-volltextsuche
    provides: "Store, open_read_only, index_bytes, GET /status als strukturgleicher Analog, AppAPIAuthMiddleware"
  - phase: 03-aktualit-t-und-ocr
    provides: "files.ocr_used, files.indexed_at, der gemessene OCR-Seitenmedian aus docs/ocr.md"
provides:
  - "GET /rates: gemessener Durchsatz des laufenden Laufs, Text- und OCR-Rate getrennt, plus Bytes je Dokument"
  - "Store::throughput(): eine gruppierte Abfrage ueber indexed_at durch den Index files_indexed_at"
  - "AdminViewService::overview()['estimate']: dreizehn feste Schluessel mit Dateizahl, OCR-Intervall, Restdauer, Platzbedarf und Platzwarnung"
  - "Block 2 der Admin-Seite (findling-estimate), gerendert nur solange der Erstindex nicht durch ist"
  - "Beide info.xml und der Image-Tag auf 0.3.0"
affects: [04-06, 04-07, 04-08, 05-messlauf-auf-zielhardware]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Selbstkalibrierung statt Konstantenvorhersage: die Seite misst den laufenden Lauf und rechnet hoch, weil der ARM-Faktor gegen amd64 unbekannt ist"
    - "Startwerte sind ein eigenes Antwortfeld (startupValues), nie eine stille Annahme"
    - "Container-Konstanten reisen mit der Antwort (startupRateOcrMs), damit die PHP-Seite sie nicht zweitspeichert"
    - "Eine Fensterabfrage laeuft nur ueber einen Index, weil die Seite alle fuenf Sekunden pollt"

key-files:
  created:
    - backend/src/findling/api/rates.py
    - backend/tests/test_rates_endpoint.py
  modified:
    - backend/src/findling/store/repo.py
    - backend/src/findling/main.py
    - backend/appinfo/info.xml
    - php/appinfo/info.xml
    - php/lib/Service/AdminViewService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/css/admin.css
    - php/l10n/de.json
    - php/l10n/de.js
    - backend/tests/test_status_endpoint.py
    - backend/tests/test_admin_ui_contract.py

key-decisions:
  - "Der Durchsatz wird gemessen statt vorhergesagt: GET /rates meldet Text- und OCR-Rate getrennt ueber ein geklemmtes Fenster, und die Seite rechnet daraus hoch"
  - "Startwerte sind ein eigenes Feld (startupValues); die Seite beschriftet die Dauer entsprechend statt sie als Messung zu verkaufen"
  - "Der OCR-Anteil bleibt ein Intervall, bis die Haelfte der indexierbaren Dateien ein Verdikt hat (MEASURED_OCR_FROM_JUDGED_PERCENT)"
  - "Der Platzbedarf entsteht aus backend.indexBytes durch backend.docs und nicht aus dem Quotienten von /rates, damit die Zahl einen gescheiterten /rates-Aufruf ueberlebt"
  - "Bei firstIndexDone wird /rates nicht mehr aufgerufen, weil der Block nicht gerendert wird"
  - "Ohne gezaehlte Dateien zeigt Block 2 keine Nullzeile, sondern nur den Zaehl-Hinweis"
  - "windowSeconds wird auf 60 bis 86400 geklemmt statt abgelehnt; nur ein nicht numerischer Wert bleibt ein 422"
  - "Die Subtraktion filesSeen minus overCap minus excluded wanderte nach overview(), damit coverage.indexable und estimate.files aus einer Rechnung stammen"

patterns-established:
  - "Nullbare Anzeigewerte: secondsLeft, bytesExpected, bytesPerDoc und ocrMeasured sind null statt 0, weil 0 Sekunden 'fertig' und 0 Byte 'frei' bedeutet"
  - "Groessenformatierung in beiden Haelften identisch (eigene Einheitentabelle statt Util::humanFileSize, dessen Dezimalpunkt nicht lokalisiert ist)"
  - "Ein Test, dessen Name eine Anzahl behauptet, wird umbenannt statt mitgezaehlt (test_every_route_of_this_container_is_mounted)"

requirements-completed: [ADM-03]

# Metrics
duration: 21 min
completed: 2026-09-02
---

# Phase 04 Plan 05: Vorab-Schaetzung des Erstindex Summary

**GET /rates meldet den gemessenen Durchsatz getrennt fuer Text und OCR, und Block 2 der Admin-Seite zeigt daraus Dateizahl, OCR-Intervall, Restdauer und Platzbedarf, jede Zahl als Messung, Startwert oder vorlaeufig beschriftet.**

## Performance

- **Duration:** 21 min
- **Started:** 2026-09-02T17:35:00Z
- **Completed:** 2026-09-02T17:56:00Z
- **Tasks:** 3 (Task 1 nach TDD, RED und GREEN getrennt committet)
- **Files modified:** 14 (2 neu, 12 geaendert)

## Accomplishments

- **`GET /rates`** ist die vierte und letzte Route des Containers. Sie liefert `docsPerHourText` und `docsPerHourOcr` getrennt, das geklemmte Fenster, Bytes je Dokument samt beider Operanden und den dokumentierten amd64-Startwert je OCR-Seite. Sie oeffnet die Zustandsdatenbank ausschliesslich read-only, traegt keinen Namen und keinen Pfad und antwortet ohne Zustandsdatenbank mit Nullen plus Notiz.
- **`Store::throughput()`** gruppiert genau einmal ueber `indexed_at` und `ocr_used` und rechnet nichts nach. Die Abfrage laeuft ueber den Index `files_indexed_at` aus Plan 04-02, weil eine Seite, die alle fuenf Sekunden pollt, keinen Full Scan ueber hunderttausend Zeilen ausloesen darf (T-04-25).
- **Die Schaetzrechnung liegt an einer Stelle.** `overview()['estimate']` hat dreizehn feste Schluessel. Vier von ihnen sind bewusst nullbar, weil 0 Sekunden "fertig" und 0 Byte "frei" heisst. `startupValues` ist das Signal, mit dem die Seite eine Zahl als Startwert beschriftet; ein stummer Container erzeugt keine Zahl, sondern null.
- **Block 2 der Seite** erscheint nur solange der Erstindex nicht durch ist, zeigt in der ersten Minute ausschliesslich den Zaehl-Hinweis mit dem Mount-Fortschritt, ersetzt das OCR-Intervall durch die Messung, sobald sie belastbar ist, und warnt mit eigenem Banner, bevor der Index in `paused_low_disk` laeuft.
- **D-05 steht sichtbar auf der Seite:** die letzte Zeile des Blocks sagt, dass Findling auf keine Bestaetigung wartet und der Erstindex bereits laeuft. Es gibt kein Bestaetigungs-Gate, und es entstand keins.

## Task Commits

1. **Task 1 (RED): failing test fuer die Durchsatzroute** - `238e3cd` (test)
2. **Task 1 (GREEN): GET /rates, Store::throughput, Router, beide info.xml auf 0.3.0** - `a24db3e` (feat)
3. **Task 2: die Schaetzrechnung in AdminViewService** - `ff60fea` (feat)
4. **Task 3: Block 2 im Template, im Skript, im CSS und in de.json/de.js** - `38a7404` (feat)

**Plan metadata:** dieser Commit (docs)

_Task 1 war ein TDD-Task, daher zwei Commits. Ein Refactor-Schritt war nicht noetig._

## Files Created/Modified

- `backend/src/findling/api/rates.py` - die Route, ihr Privacy-Vertrag, die Klemmung des Fensters, der Startwert je OCR-Seite
- `backend/tests/test_rates_endpoint.py` - Feldmenge als Ganzes (`FIELDS`), Privacy-Lauf ueber jeden Stringwert, 401 ohne Header, read-only statisch geprueft, Byte-Identitaet der Datei, getrennte Zaehlung von Text und OCR, leeres Fenster, Klemmung, 422 bei nicht numerischem Fenster
- `backend/src/findling/store/repo.py` - `throughput(window_seconds, now)`, eine gruppierte Abfrage mit der Begruendung des Index im Docstring
- `backend/src/findling/main.py` - Import und `include_router` fuer den vierten Router
- `backend/appinfo/info.xml` - vierter `<route>`-Eintrag mit `access_level ADMIN`, Kommentar von "drei" auf "vier" korrigiert, `<version>` und `<image-tag>` auf 0.3.0
- `php/appinfo/info.xml` - `<version>` auf 0.3.0, mit der Begruendung neben der Zeile
- `php/lib/Service/AdminViewService.php` - `estimate`-Teilbaum, `measuredOcr()`, `timeLeft()`, `rates()`, fuenf neue Klassenkonstanten, D-05-Absatz im Klassen-Docblock; die Subtraktion des Nenners wanderte nach `overview()`
- `php/templates/admin.php` - Block 2 mit beiden Gestalten der Schaetzzeile, Zaehl-Hinweis, Platz-Satz, Startwert-Beschriftung, Warn-Banner und der D-05-Zeile; eigener Groessenformatierer
- `php/js/admin.js` - `estimateBlock()`, `size()`, erweiterter `fingerprint()`; der Block wird ueber `hidden` ausgeblendet, sobald `firstIndexDone` waehrend der Sitzung wahr wird
- `php/css/admin.css` - `max-width` fuer den zweiten Block und die Zeile mit dem Core-Spinner
- `php/l10n/de.json`, `php/l10n/de.js` - neun neue deutsche Texte mit echten Umlauten, woertlich aus der Copy-Tabelle, soweit sie dort steht
- `backend/tests/test_status_endpoint.py` - der Montage-Test umbenannt und um `/rates` erweitert
- `backend/tests/test_admin_ui_contract.py` - der Scanner-Typ des Gates benannt (siehe Abweichungen)

## Decisions Made

- **Messen statt vorhersagen.** Alle gemessenen Raten stammen von einem amd64-Laptopkern, das Hardware-Ziel ist eine ARM-Box, und der Messlauf dafuer steht laut STATE.md in Phase 5 aus. Eine Hochrechnung aus dem eigenen Lauf braucht diesen unbekannten Faktor nicht. Die Konstanten sind der Startwert der ersten Minute und sonst nichts.
- **Zwei Raten, nie eine.** Eine OCR-Seite kostet gemessen etwa zwei Sekunden, eine Textseite nichts Messbares. Eine kombinierte Zahl waere fuer jede Instanz falsch, deren Dokumentenmischung nicht die des Messkorpus ist.
- **Das Fenster wird geklemmt, nicht abgelehnt.** 60 bis 86400 Sekunden. Eine Admin-Seite braucht fuer eine Fensterlaenge keine Fehlermeldung; nur ein Wert, der gar keine Zahl ist, bleibt ein 422 der FastAPI-Signatur.
- **`MEASURED_OCR_FROM_JUDGED_PERCENT = 50`** als benannte Anzeigeentscheidung. Der gemessene OCR-Wert waechst, solange nur wenige Dateien ein Verdikt haben, und eine Zahl, die sich stillschweigend nach oben korrigiert, sieht wie ein Fehler aus. Bis zur Haelfte bleibt das Intervall stehen, danach steht die Messung. Der Satz, dass die Haelfte eine Anzeigeentscheidung und keine Messung ist, steht im Docblock der Konstante.
- **Der Platzbedarf kommt aus `backend.indexBytes` durch `backend.docs`**, nicht aus dem Quotienten, den `/rates` ebenfalls liefert. `/status` wird fuer Block 1 ohnehin gerufen, also ueberlebt die Platzangabe einen gescheiterten `/rates`-Aufruf, und es gibt weiterhin nur eine Regel je Zahl.
- **`MIN_FREE_BYTES` ist eine bewusste Zweitkopie** einer Container-Konstante. Die Alternative waere ein fuenftes Feld auf einer Statusantwort, die den daraus abgeleiteten Boolean schon traegt; die Zahl hat sich in drei Phasen nicht bewegt, und `lowDisk` bleibt in jedem Fall die Wahrheit des Containers.
- **Eigene Groessenformatierung statt `Util::humanFileSize`.** Diese Funktion setzt immer einen Punkt vor die Dezimalstelle, unabhaengig von der Sitzungssprache. Template und Skript benutzen dieselbe Einheitentabelle und dieselbe Stellenzahl, damit eineinhalb Gigabyte auf beiden Haelften der Seite gleich aussehen.
- **Kein `/rates`-Aufruf, wenn `firstIndexDone` wahr ist.** Der Block wird dann nicht gerendert, und eine ruhende Instanz wird alle dreissig Sekunden gepollt; ein Aufruf, dessen Antwort niemand rendert, ist eine Netzrunde fuer nichts.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `pyright` war schon vor diesem Plan rot**

- **Found during:** Task 1 (Abnahmekriterium "pyright ist gruen")
- **Issue:** `backend/tests/test_admin_ui_contract.py` deklarierte den Scanner seines Quelltripels als `object`. Der Aufruf in der Comprehension ist damit kein pruefbarer Aufruf, und `uv run pyright` meldete `Object of type "object" is not callable`. Die Datei stammt aus Plan 04-03 und wurde von diesem Plan nicht angefasst, aber das Abnahmekriterium von Task 1 und die Plan-Verifikation verlangen beide ein gruenes `pyright`, also war der Befund blockierend.
- **Fix:** Typalias `Scanner = Callable[[str, str], list[str]]` eingefuehrt und als Rueckgabetyp von `_sources()` verwendet, mit einem Docblock-Satz, warum der Typ benannt ist.
- **Files modified:** `backend/tests/test_admin_ui_contract.py`
- **Verification:** `uv run pyright` meldet 0 errors; `pytest tests/test_admin_ui_contract.py` bleibt gruen (13 passed).
- **Committed in:** `a24db3e` (Task-1-Commit)

**2. [Rule 2 - Missing Critical] `php/css/admin.css` stand nicht in der Dateiliste, ohne sie bricht der Abstandsvertrag**

- **Issue:** Der UI-Vertrag legt `max-width: 900px` fuer alle fuenf Bloecke fest, und die bestehende Regel war an `#findling-coverage` gebunden. Ohne eine Regel fuer `#findling-estimate` liefe der neue Block ueber die volle Fensterbreite, und der Core-Spinner `icon-loading-small` ist ein Hintergrundbild auf einem leeren Element und haette ohne eigene Box keine Groesse.
- **Fix:** `#findling-estimate` in den bestehenden `max-width`-Selektor aufgenommen und eine Klasse `findling-progress-hint` fuer die Zeile mit dem Spinner ergaenzt, beide ausschliesslich mit Theme-Variablen und Vielfachen der Vier-Pixel-Basis.
- **Files modified:** `php/css/admin.css`
- **Verification:** `pytest tests/test_admin_ui_contract.py` (Gate C: kein Hexwert, keine Farbfunktion, kein entfernter Fokusring) gruen.
- **Committed in:** `38a7404` (Task-3-Commit)

**3. [Rule 2 - Missing Critical] Zweite Gestalt der Schaetzzeile und kein Nullsatz in der ersten Minute**

- **Issue:** Die Schaetzzeile des UI-Vertrags hat vier Platzhalter, zwei davon eine Dauer und eine Groesse, die es erst nach einer Messung gibt. Woertlich gerendert stand in der ersten Minute "0 Dateien, davon 0 bis 0 mit OCR. Etwa 1 Minute und etwa 0 B Index." auf der Seite, also genau die Platzhalterzahlen, die der Vertrag fuer diesen Block verbietet.
- **Fix:** Zwei Gestalten der Zeile, beide im Markup, eine davon verborgen: die vollstaendige Zeile, solange Dauer und Groesse existieren, sonst eine kurze mit Dateizahl und OCR-Anteil. Bei `files === 0` ist keine der beiden sichtbar, und der Zaehl-Hinweis samt Mount-Fortschritt ist die ganze Antwort. Der fehlende Wert wird durch seinen eigenen Satz erklaert, nicht geraten.
- **Files modified:** `php/templates/admin.php`, `php/js/admin.js`, `php/l10n/de.json`, `php/l10n/de.js`
- **Verification:** DOM-Sichtprobe der vier Zustaende im Container (siehe unten): in Zustand A ist keine Schaetzzeile sichtbar.
- **Committed in:** `38a7404` (Task-3-Commit)

---

**Total deviations:** 3 auto-fixed (1 blockierend, 2 fehlende Notwendigkeit)
**Impact on plan:** Kein Scope Creep. Abweichung 1 raeumt ein Gate frei, das dieser Plan als Abnahmekriterium fuehrt; 2 und 3 sind der Abstandsvertrag und das Platzhalterverbot des UI-Vertrags, beide innerhalb der Aufgabenbeschreibung von Task 3.

## Verification

| Pruefung | Ergebnis |
|---|---|
| `cd backend && uv run python -m pytest -q` | 740 passed, 11 skipped |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 75 files already formatted |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | keine Meldung |
| `php -l` ueber `lib`, `appinfo`, `templates` im Container | keine Syntaxfehler |
| `node --check php/js/admin.js`, `node --check php/l10n/de.js` | ok |
| `json.load(php/l10n/de.json)` | ok |
| Beide `info.xml` als XML geparst, beide auf 0.3.0, vier `<route>`-Eintraege | ok |
| Em-Dash (U+2014) und En-Dash (U+2013) in allen geaenderten Dateien | keiner |

**Sichtproben** (CLI-Probe im Container `findling-nextcloud`: Nextcloud bootstrappen, `overview()` rufen, `OC_Template('findling','admin')` rendern, Block 2 per DOM auslesen):

| Zustand | Ergebnis |
|---|---|
| A: erste Minute, Scan laeuft (`files 0`, `provisional`) | nur Zaehl-Hinweis mit "0 von 3 Speicherorten" plus die D-05-Zeile; keine Schaetzzeile, keine Platzhalterzahl |
| B: Lauf laeuft, nichts gemessen (`secondsLeft` da, `bytesExpected` null) | kurze Zeile "164 Dateien, davon 30 bis 46 mit OCR.", Platz-wird-gemessen-Satz, Beschriftung "Startwert, wird gemessen." |
| C: Lauf laeuft, alles gemessen, Platz knapp | vollstaendige Zeile "164 Dateien, davon 38 mit OCR. Etwa 2 Stunden und etwa 1,5 GB Index.", Warn-Banner sichtbar, keine Startwert-Beschriftung |
| D: Erstindex durch (`firstIndexDone`) | Block gar nicht im Markup |
| Container nicht erreichbar (echter Zustand der Dev-Instanz) | `estimate.startupValues` true, `estimate.secondsLeft` null, alle dreizehn Schluessel vorhanden, `estimate.files` gleich `coverage.indexable` (164) |

**Deutsche Fassung** ueber `IFactory::get('findling','de')` geprueft: alle neun neuen Quellstrings loesen auf, mit echten Umlauten und ohne Em-Dash.

## Issues Encountered

- Der ExApp-Container laeuft in dieser Dev-Umgebung nicht, also war `backendReachable` in jeder Live-Probe false. Das ist fuer das Abnahmekriterium "nicht erreichbarer Container erzeugt keine erfundene Zahl" der Idealfall und wurde so geprueft; die drei uebrigen Zustaende wurden ueber gerenderte `estimate`-Baeume gegen dieselbe Template-Logik geprueft, weil die Verzweigungen ausschliesslich in Template und Skript liegen.
- Der erste Anlauf der Sichtprobe las die `hidden`-Attribute zeilenweise und meldete mehrzeilige Elemente falsch als sichtbar. Die Probe wurde auf `DOMDocument` und `hasAttribute('hidden')` umgestellt, und erst diese Fassung deckte die Nullzeile aus Abweichung 3 auf.

## Known Stubs

Keine. Jede Zahl des Blocks stammt aus einer Messung, einem beschrifteten Startwert oder ist null mit einem Satz daneben.

## Threat Flags

Keine neue Oberflaeche jenseits des Threat-Registers des Plans. `GET /rates` ist im Register als T-04-24 bis T-04-26 und T-04-29 gefuehrt und liegt hinter `AppAPIAuthMiddleware`; die PHP-Seite ruft sie ueber die bestehende admin-only Route. Kein Paket wurde installiert (T-04-SC).

## User Setup Required

Keine. Beim naechsten Release muessen `git tag` und beide `info.xml` auf `0.3.0` stehen; das prueft `docker.yml` selbst, bevor es baut.

## Next Phase Readiness

- ADM-03 ist erfuellt: der Admin sieht ab Minute 1 Dateizahl, OCR-Intervall, Restdauer und Platzbedarf, jede Zahl beschriftet, und wird gewarnt, bevor der Index pausiert.
- Fuer Plan 04-06 (Fehlerliste, Block 3) liegt bereit: `estimate` und `coverage` teilen eine Rechnung, `backend.reasons` ist bereits gefiltert und formgeprueft, und der Groessenformatierer sowie `findling-progress-hint` sind wiederverwendbar.
- Offen und bewusst nicht in diesem Plan: `STARTUP_TEXT_DOCS_PER_HOUR` ist die einzige Zahl dieses Plans, die nie gemessen wurde (Assumption A2 der Recherche). Sie wirkt nur in der ersten Minute und ist auf der Seite als Startwert beschriftet; der Messlauf in Phase 5 sollte sie mitnehmen und den ARM-Faktor dazu.
- Gate B (PHP-Routen) blieb unberuehrt: dieser Plan legte keine PHP-Route an, die untere Grenze von 9 gilt weiter.

---
*Phase: 04-admin-sichtbarkeit-und-diagnose*
*Completed: 2026-09-02*

## Self-Check: PASSED

Alle in `key-files.created` genannten Dateien liegen auf der Platte, alle fuenf Commit-Hashes sind im Repository, und ROADMAP.md fuehrt Phase 4 mit 5 von 10 Plaenen.
