---
phase: 04-admin-sichtbarkeit-und-diagnose
plan: 04
subsystem: ui
tags: [nextcloud, php, migration, doctrine, queuebuilder, vanilla-js, l10n, coverage]

# Dependency graph
requires:
  - phase: 04-03
    provides: "Section, Admin-ISettings, SettingsController, AdminViewService::overview(), admin.php, admin.js, admin.css"
  - phase: 02
    provides: "StorageCrawlJob mit Transaktionsbaendern, StorageService::getFilesInMount, FileStateService als Rueckkanal"
provides:
  - "Tabelle findling_scan_stats, eine Zeile je Storage, hasTable-geschuetzt"
  - "ScanStatsService: beginStorage, add, finishStorage, totals, forStorage; idempotent gegen occ findling:index --restart"
  - "Der Crawl schreibt seine Zaehler dauerhaft mit (Dateien, Bytes, OCR-sichere Bilder, PDFs, Cap-Ueberschreitungen, Cursor)"
  - "AdminViewService::overview().coverage mit sieben festen Schluesseln"
  - "FileStateService::countByReason(state, reason)"
  - "Deckungsgrad als Bruch mit benanntem Nenner im Template, plus Zeile bewusst ausgelassen und Vorlaeufigkeitshinweis"
affects: [04-05, 04-06, 04-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zaehler-Upsert im Datenbankausdruck ueber IFunctionBuilder::add statt Lesen und Zurueckschreiben in PHP"
    - "Alle Anzeigezustaende eines Blocks liegen im Markup und werden ueber das hidden-Attribut geschaltet, das Skript baut kein Markup"
    - "Prozentzahl wird genau einmal serverseitig gerechnet und fertig ausgeliefert"

key-files:
  created:
    - php/lib/Migration/Version001000Date20260903000000.php
    - php/lib/Service/ScanStatsService.php
  modified:
    - php/lib/BackgroundJobs/StorageCrawlJob.php
    - php/lib/Service/AdminViewService.php
    - php/lib/Service/FileStateService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/de.json
    - php/l10n/de.js

key-decisions:
  - "Der Nenner des Deckungsgrads entsteht im Crawl (filesSeen minus overCap minus excluded) und nie aus einer zweiten Abfrage; die Subtraktion steht genau einmal in AdminViewService"
  - "Idempotenz nach Variante (a): beginStorage setzt die Zeile bei last_file_id === 0 zurueck, Variante (b) mit Cursor-Vergleich je Datei verworfen"
  - "pdf_seen ist eine eigene Spalte, weil der OCR-Anteil vor dem Lauf ein Intervall ist und keine Zahl; sie kam schon in die Migration von Task 1, damit spaeter keine Spalte in eine gefuellte Tabelle nachgezogen werden muss"
  - "percent ist auch dann null, wenn das Backend nicht antwortet: ohne Zaehler gibt es keinen ehrlichen Bruch, und 0 Prozent waere genau die Luege, gegen die diese Phase gebaut wird"
  - "Alle drei Gestalten des Deckungsgrad-Blocks stehen im Markup und werden ueber hidden geschaltet, damit die Kopfzahl im Erstindex ohne Neuladen erscheinen kann"
  - "Top-Level-Schluessel indexable entfaellt aus overview(); die Zahl lebt nur noch unter coverage, damit es keine zwei Quellen fuer eine Zahl gibt"
  - "Die Kachel Excluded liest die Scan-Zaehler, damit Kachel und Nenner dasselbe unter ausgeschlossen verstehen"

patterns-established:
  - "Zaehler-Addition in der Datenbank: IFunctionBuilder::add innerhalb des bestehenden Upsert-Musters (update, dann insertIgnoreConflict, zwei Versuche)"
  - "Ein Zaehler-Schreibvorgang je Transaktionsband, nie je Datei"
  - "Statusausgaben liefern immer alle Schluessel mit Nullen (array_fill_keys ueber eine geschlossene Liste)"

requirements-completed: [ADM-01]

# Metrics
duration: 25 min
completed: 2026-09-02
---

# Phase 04 Plan 04: Deckungsgrad mit nachrechenbarem Nenner Summary

**Der Crawl schreibt seine Zaehler in die neue Tabelle `findling_scan_stats`, und daraus rechnet die Admin-Seite den Deckungsgrad als Bruch, dessen Nenner im Text daneben steht.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-02T17:05:30Z
- **Completed:** 2026-09-02T17:30:50Z
- **Tasks:** 3
- **Files modified:** 9 (2 neu, 7 geaendert)

## Accomplishments

- `findling_scan_stats` liegt in der Nextcloud-Datenbank, eine Zeile je Storage, jede Schemaaenderung hinter `hasTable`, ein zweiter Migrationslauf ist nachweislich ein No-op.
- `ScanStatsService` addiert im Datenbankausdruck statt in PHP, setzt eine Storage-Zeile bei einem Neustart des Laufs zurueck und antwortet mit allen acht Schluesseln auch ueber einer leeren Tabelle.
- Der `StorageCrawlJob` fuehrt fuenf Zaehler je Transaktionsband und gibt sie einmal je Band und einmal am Ende ab; ein `occ findling:index --restart` verdoppelt nichts (lokal gemessen).
- Der Deckungsgrad steht als Prozentzahl mit `<progress>` und der Zeile `%1$s von %2$s indexierbaren Dateien sind durchsuchbar` auf der Seite; `Bewusst ausgelassen: N` hat eine eigene Zeile mit Erklaersatz und steht nicht im Nenner.
- Solange nicht jedes Mount durchgezaehlt ist, beschriftet die Seite die Zahl als vorlaeufig und nennt, wie viele von wie vielen Speicherorten durch sind.
- Bei `indexable === 0` erscheint der Empty-State und keine Null-Prozent-Aussage; bei stummem Backend erscheint ein Satz, der den Nenner nennt und den Bruch verweigert.

## Task Commits

Each task was committed atomically:

1. **Task 1: Die Tabelle findling_scan_stats und ihr idempotenter Dienst** - `6d0e6d7` (feat)
2. **Task 2: Der Crawl schreibt seine Zaehler mit, statt sie zu loggen** - `14482e3` (feat)
3. **Task 3: Der Deckungsgrad steht als Bruch mit benanntem Nenner auf der Seite** - `1bb3b8d` (feat)

## Files Created/Modified

- `php/lib/Migration/Version001000Date20260903000000.php` - Legt `findling_scan_stats` an: `storage_id` als Primaerschluessel `findling_ss_id`, sechs Zaehler, `cursor_file_id`, `finished_at` nullable, `updated_at`. Docblock begruendet den Ort in der Nextcloud-Datenbank, die Bedeutung eines fehlenden `finished_at` und den Verzicht auf Fremdschluessel.
- `php/lib/Service/ScanStatsService.php` - `beginStorage`, `add`, `finishStorage`, `totals`, `forStorage`, `reject`. Upsert nach dem Muster von `FileStateService::record`, Addition ueber `IFunctionBuilder::add`, `closeCursor` an jedem `executeQuery`.
- `php/lib/BackgroundJobs/StorageCrawlJob.php` - `ScanStatsService` im Konstruktor, `beginStorage` bei `last_file_id === 0`, fuenf Bandzaehler in der Schleife, `add` je `TX_BAND` und einmal am Ende, `finishStorage` an der Terminierungsbedingung. `MAX_SIZE`-Docblock nennt seine Rolle als kuenftiger Default, Klassen-Docblock erklaert, warum der Crawl der Metadaten-Scan ist.
- `php/lib/Service/AdminViewService.php` - Neuer Teilbaum `coverage` mit sieben festen Schluesseln, `excluded` aus den Scan-Zaehlern, Top-Level-`indexable` entfernt, vierte Quelle im Klassen-Docblock benannt.
- `php/lib/Service/FileStateService.php` - `countByReason(string $state, string $reason): int`, gegen beide geschlossenen Listen validiert.
- `php/templates/admin.php` - Kopfzahl, Balken, Subline, Unbekannt-Satz, Zeile `Bewusst ausgelassen`, Vorlaeufigkeitshinweis und Empty-State liegen alle im Markup und werden ueber `hidden` geschaltet.
- `php/js/admin.js` - `coverageBlock(view)` schreibt Textknoten und schaltet Sichtbarkeit, rechnet die Prozentzahl nicht nach, aktualisiert `value` des `<progress>` ueber `setAttribute`; `fingerprint` kennt die Coverage-Felder.
- `php/l10n/de.json`, `php/l10n/de.js` - Vier neue deutsche Texte mit echten Umlauten, in beiden Dateien identisch.

## Decisions Made

- **Nenner aus derselben Wanderung.** `indexable = filesSeen - overCap - excluded`, und die Subtraktion steht genau einmal in `AdminViewService`, weil Plan 04-05 dieselbe Zahl fuer die Schaetzung braucht. Der Mimetype-Filter und die beiden Verschluesselungs-Booleans liegen schon in der Abfrage des Crawls, Cap und Ausschluesse wendet er selbst an, also ist der Nenner woertlich die Menge, die auch die Arbeit erzeugt.
- **Idempotenz-Variante (a).** `beginStorage` setzt die Zeile zurueck, wenn ein Storage bei `last_file_id === 0` beginnt. Variante (b), Zaehler nur oberhalb von `cursor_file_id` addieren, waere eine Entscheidung je Datei fuer einen Zaehler, der einmal je Band geschrieben wird, und wuerde nach einer Cap-Aenderung stillschweigend nichts mehr tun. Die Begruendung steht im Docblock des Dienstes.
- **`pdf_seen` als eigene Spalte, schon in Task 1.** Bilder brauchen OCR sicher, ein PDF entscheidet sich erst am Textlayer im Container. Vor dem Lauf ist der OCR-Anteil deshalb ein Intervall; eine gemischte Zahl wuerde verbergen, von welchem Ende sie kommt. Die Spalte kam in die Migration von Task 1, weil sie sonst spaeter in eine gefuellte Tabelle nachgezogen werden muesste, und Plan 04-05 erwartet `pdfSeen` in `totals()`.
- **`percent` ist auch bei stummem Backend null.** Ohne Zaehler gibt es keinen ehrlichen Bruch, und die Nextcloud-Seite fuehrt bauartbedingt keine `indexed`-Zeilen, also waere die Zahl 0 Prozent. Genau diese Aussage verbietet der UI-Vertrag ("Kein 0 % Deckung als Aussage"), und sie ist der Ausfallmodus, an dem der Vorgaenger gestorben ist. Die Seite nennt stattdessen den Nenner und sagt, dass der Anteil im Moment nicht berechenbar ist.
- **Alle Gestalten im Markup, geschaltet ueber `hidden`.** Dasselbe Muster, das die Banner dieses Templates schon verwenden. Damit kann die Kopfzahl waehrend des Erstindex ohne Neuladen erscheinen, obwohl das Skript weiter kein Markup baut. Kein Skeleton: die verborgenen Elemente tragen echte Werte, sie sind nur nicht die Antwort dieses Augenblicks.
- **Eine Quelle je Zahl.** Der Top-Level-Schluessel `indexable` ist aus `overview()` entfernt, die Zahl lebt nur noch unter `coverage`. Die Prozentzahl wird nur serverseitig gerechnet; das Skript uebernimmt sie, statt die Regel ein zweites Mal zu formulieren.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `pdf_seen` schon in der Migration von Task 1 angelegt**
- **Found during:** Task 1 (Migration und Dienst)
- **Issue:** Task 2 des Plans verlangt einen getrennten PDF-Zaehler und erlaubt ausdruecklich, `ScanStatsService::add` und die Migration dafuer zu erweitern. Die Spalte in Task 2 nachzuziehen haette eine zweite Migration ueber eine Tabelle mit Daten bedeutet, und Plan 04-05 erwartet `pdfSeen` bereits in `totals()`.
- **Fix:** Spalte `pdf_seen` in `Version001000Date20260903000000.php`, Parameter `$pdfSeen` in `add()`, Schluessel `pdfSeen` in `totals()` und `forStorage()`.
- **Files modified:** php/lib/Migration/Version001000Date20260903000000.php, php/lib/Service/ScanStatsService.php
- **Verification:** `.schema oc_findling_scan_stats` zeigt die Spalte, `totals()` liefert acht Schluessel (die sieben verlangten plus `pdfSeen`), lokaler Lauf zaehlt 16 PDFs ueber drei Mounts.
- **Committed in:** 6d0e6d7

**2. [Rule 3 - Blocking] `FileStateService::countByReason()` ergaenzt**
- **Found during:** Task 3 (Deckungsgrad in der Aggregation)
- **Issue:** Der Plan verlangt fuer `deliberatelyLeftOut` die Zahl der `skipped`-Zeilen mit Grund `mime_not_allowed` aus `FileStateService`, aber dieser Leser existierte nicht, und `php/lib/Service/FileStateService.php` stand nicht in `files_modified`. `FileStateService` ist der einzige Zugriffsweg auf `findling_file_state`, eine eigene Abfrage in `AdminViewService` waere ein zweiter Zugang zur selben Tabelle gewesen.
- **Fix:** `countByReason(string $state, string $reason): int`, gegen `STATES` und `REASONS` validiert, ein abgelehntes Paar wird gezaehlt und geloggt wie in `reject()`. Der Grund kommt als Argument, damit ein zweiter Aufrufer die Abfrage nicht kopiert.
- **Files modified:** php/lib/Service/FileStateService.php
- **Verification:** `deliberatelyLeftOut` liefert lokal 1 (die 55-MB-Datei), `php -l` sauber, Gate C gruen.
- **Committed in:** 1bb3b8d

**3. [Rule 2 - Missing Critical] `percent` ist auch dann null, wenn das Backend nicht antwortet**
- **Found during:** Task 3 (Deckungsgrad im Template)
- **Issue:** Der Plan nennt nur `indexable === 0` als Fall ohne Prozentzahl. Bei stummem Container liefert `backend.indexed` aber 0, und die Nextcloud-Seite fuehrt bauartbedingt keine `indexed`-Zeilen. Der erste serverseitige Aufschlag mit gestopptem Backend haette also "0 %" behauptet, was der UI-Vertrag ausdruecklich verbietet und was genau der Ausfallmodus des Vorgaengers ist.
- **Fix:** `percent` bleibt null, solange `backendReachable` falsch ist. Das Template zeigt dann einen Satz, der den Nenner nennt und den Anteil verweigert; der bestehende Unreachable-Banner erklaert die Ursache.
- **Files modified:** php/lib/Service/AdminViewService.php, php/templates/admin.php, php/js/admin.js, php/l10n/de.json, php/l10n/de.js
- **Verification:** CLI-Probe mit gestopptem Backend rendert `findling-coverage-unknown` sichtbar, Kopfzahl, Balken und Subline verborgen.
- **Committed in:** 1bb3b8d

**4. [Rule 2 - Missing Critical] Alle drei Gestalten des Blocks im Markup statt if/else**
- **Found during:** Task 3 (Deckungsgrad im Template)
- **Issue:** Mit dem bestehenden `if ($indexable > 0)`-Zweig existiert die Kopfzahl im DOM nicht, wenn die Seite vor dem ersten Cron-Lauf geoeffnet wird. Das Skript darf laut UI-Vertrag kein Markup bauen, also waere die Kopfzahl erst nach einem Neuladen erschienen. Sichtprobe 2 des UI-Vertrags verlangt aber "Kopfzahl steigt ohne Neuladen".
- **Fix:** Kopfzahl, Balken, Subline, Unbekannt-Satz, Ausgelassen-Zeile, Vorlaeufigkeitshinweis und Empty-State liegen alle im Markup und tragen `hidden`, wenn sie nicht zutreffen. Dasselbe Muster, das die Banner des Templates schon verwenden. Kein Skeleton, weil die verborgenen Elemente echte Werte tragen.
- **Files modified:** php/templates/admin.php, php/js/admin.js
- **Verification:** CLI-Probe rendert alle vier Randzustaende (Bruch, Bruch mit Vorlaeufigkeit, Zaehler unbekannt, kein Nenner) mit jeweils genau einer sichtbaren Gestalt.
- **Committed in:** 1bb3b8d

---

**Total deviations:** 4 auto-fixed (2 blocking, 2 missing critical)
**Impact on plan:** Alle vier folgen aus dem Plan oder dem genehmigten UI-Vertrag selbst. Kein Scope Creep: keine neue Route, kein neues Paket, `php/composer.json` und `backend/pyproject.toml` unveraendert.

## Verification Results

| Pruefung | Ergebnis |
|---|---|
| `cd backend && uv run python -m pytest -q` | **728 passed, 11 skipped** (Gate A, Gate B, Gate C, Reason-Paritaet) |
| `php -l` ueber `lib`, `appinfo`, `templates` im Container | ausschliesslich "No syntax errors detected" |
| Migration erstmalig | `oc_findling_scan_stats` angelegt, Primaerschluessel `findling_ss_id`, zehn Spalten wie geplant plus `pdf_seen` |
| Migration zweiter Lauf | "Updated findling to 0.2.0" ohne Fehler, kein Schemaeingriff |
| Crawl-Lauf ueber drei Mounts | `files_seen` 49/66/49, `bytes_seen`, `ocr_candidates` 9/12/9, `pdf_seen` 3/10/3, `cursor_file_id` gesetzt |
| `finished_at` | nach den letzten Cron-Runden auf allen drei Zeilen gesetzt, `mountsFinished` 3 von 3 |
| Zweiter `occ findling:index --restart` | Storage 2 und 4 zeichengleich wie vorher, Storage 3 exakt um die neue Datei groesser. Keine Verdopplung (T-04-21) |
| Cap-Zweig | 55-MB-Datei in den Korpus gelegt, `over_cap` springt auf 1, `deliberatelyLeftOut` auf 1, `indexable` 165 minus 1 = 164 |
| `overview()` Schluessel | `indexed, skipped, failed, excluded, indexedDisplay, scheduled, running, lastJobRun, stalledFor, runState, backendReachable, backend, coverage` |
| `coverage` Schluessel | alle sieben vorhanden: `indexed 0, indexable 164, deliberatelyLeftOut 1, percent null, provisional false, mountsTotal 3, mountsFinished 3` |
| Template, Bruch | `73 %`, `<progress value="73">` mit `aria-labelledby`, Subline "120 von 163 indexierbaren Dateien sind durchsuchbar" |
| Template, vorlaeufig | "Vorlaeufige Zahl, 1 von 3 Speicherorten sind durchgezaehlt." sichtbar |
| Template, kein Nenner | nur `findling-coverage-empty` sichtbar, keine Null-Prozent-Aussage |
| Template, Backend stumm | nur `findling-coverage-unknown` sichtbar, nennt den Nenner |
| Deutsche Fassung | `force_language=de`: "Deckungsgrad der Suche", "Bewusst ausgelassen: 1", "Vorlaeufige Zahl, 1 von 3 Speicherorten sind durchgezaehlt." mit echten Umlauten |
| L10n-Abgleich | 23 PHP- und 8 JS-Quelltexte, jeder in `de.json` **und** `de.js` vorhanden |
| Route anonym | **401** |
| Route als Admin ohne Token | **412 CSRF check failed** |
| Em-Dash und En-Dash | in keiner der neun Dateien |

## Issues Encountered

- **Die 200er-Etappe der Routenkette konnte nicht erneut bewiesen werden.** Ein Anmeldevorgang per `curl` gegen `/login` scheitert auf dieser Instanz: der Login-Controller verwirft das aus der Anmeldeseite gelesene `data-requesttoken` und leitet auf `/login?direct=1&user=admin` um, ohne einen Fehlversuch zu verbuchen. Die Zugangsdaten sind nachweislich richtig (Basic Auth gegen `/ocs/v2.php/cloud/user` antwortet 200), ein App-Passwort hilft nicht, weil der Controller ausserhalb des OCS-Raums liegt und CSRF verlangt (Entscheidung aus 04-03). Ersatzweise wurden die Aggregation und alle vier Gestalten des Templates ueber eine CLI-Probe geprueft, die Nextcloud bootstrappt, `AdminViewService::overview()` aufruft und `OC_Template('findling', 'admin')` rendert. Die beiden Sicherungen der Route (401 anonym, 412 ohne Token) sind bestaetigt.
- **Das ExApp-Backend laeuft auf der Entwicklungsinstanz derzeit nicht.** Deshalb ist `backendReachable` falsch und `coverage.indexed` 0. Der Bruch selbst wurde mit einem synthetischen `coverage`-Teilbaum durch das echte Template gerendert; die Zahlen des Nenners stammen aus dem echten Scan.
- **Der Testkorpus enthielt keine Datei ueber dem Cap.** Fuer die Pruefung des `over_cap`-Zweigs wurde `99-riesenprotokoll.txt` (55 MB) in die Dateien von `testuser` gelegt und eingescannt. Die Datei bleibt liegen, weil Plan 04-06 die Fehlerliste mit der Gruppe `Zu gross` braucht. Sie liegt ausserhalb des Repositoriums, `scripts/dev/build_corpus.py` ist unveraendert.

## Known Stubs

| Stub | Datei | Grund |
|---|---|---|
| `excluded` bleibt 0 | `php/lib/BackgroundJobs/StorageCrawlJob.php`, Spalte in `findling_scan_stats` | Der Zaehler bekommt seinen Wert mit den Ausschlussregeln in Plan 04-08. Die Spalte und der Bandzaehler existieren schon, damit spaeter keine Spalte in eine gefuellte Tabelle nachgezogen werden muss. Im Code und im Migrations-Docblock so vermerkt. |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 04-05 kann `ScanStatsService::totals()` mit `filesSeen`, `bytesSeen`, `ocrCandidates`, `pdfSeen`, `overCap`, `excluded`, `mountsTotal`, `mountsFinished` lesen und `coverage.indexable` uebernehmen; die Subtraktion steht genau einmal in `AdminViewService`, sodass die Forderung "eine Rechnung, zwei Teilbaeume" einhaltbar bleibt.
- Plan 04-06 findet die Fehlerliste vorbereitet: `FileStateService::countByReason` ist der erste der neuen Leser, und `99-riesenprotokoll.txt` liefert auf der Entwicklungsinstanz eine echte `too_large`-Gruppe.
- Plan 04-08 muss beim Setzen von `excluded` den Bandzaehler `$bandExcluded` im Crawl fuellen und den Cap aus appconfig lesen; `MAX_SIZE` ist im Docblock schon als kuenftiger Default beschrieben.
- Offen und ausserhalb dieses Plans: die Anmeldung per `curl` gegen die Entwicklungsinstanz. Fuer kuenftige Sichtproben der Admin-Seite ist entweder ein Browser noetig oder die CLI-Probe dieses Plans.

---
*Phase: 04-admin-sichtbarkeit-und-diagnose*
*Completed: 2026-09-02*

## Self-Check: PASSED

- `php/lib/Migration/Version001000Date20260903000000.php` liegt auf der Platte
- `php/lib/Service/ScanStatsService.php` liegt auf der Platte
- `.planning/phases/04-admin-sichtbarkeit-und-diagnose/04-04-SUMMARY.md` liegt auf der Platte
- Commits `6d0e6d7`, `14482e3`, `1bb3b8d` sind im Verlauf
