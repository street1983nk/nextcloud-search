---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 04
subsystem: worker
tags: [ocr, poller, queue, tesseract, php, events, trashbin, subtree, python]

# Dependency graph
requires:
  - phase: 03-09
    provides: "Die OCR-Spur: kind=ocr im Poller, erzwungene Route, harte OCR-Frist, ocr_used am Verdikt"
  - phase: 03-10
    provides: "Der Bildzweig: IMAGE_MIMETYPES in dispatch.py, extract/image.py mit Deckeln und Plausibilitaetsregeln"
  - phase: 03-04
    provides: "SubtreeExpandJob als der eine Weg von einer Ordner-Operation zu Aufgaben je Datei"
  - phase: 03-03
    provides: "kind=delete im Poller und der Grabstein, der eine Wiederherstellung ueberhaupt wirksam macht"
  - phase: 03-12
    provides: "Der ETag-Abgleich, der bis zu diesem Plan die Ordner-Wiederherstellung allein getragen hat"
provides:
  - "Bilder laufen ueber die OCR-Spur: der Inhaltsdurchgang uebergibt sie, der OCR-Durchgang liest sie mit der OCR-Frist und den OCR-Deckeln"
  - "ocr_used ist fuer Bilder gesetzt, der OCR-Anteil von Store.throughput enthaelt sie damit"
  - "NodeRestoredEvent auf einen Ordner plant SubtreeExpandJob mit kind=content, der Inhalt ist ohne Abgleich wieder auffindbar"
  - "SubtreeExpandJob akzeptiert kind=content und gibt einer Inhaltsaufgabe ihre echte Groesse"
  - "Eine Loeschung fragt keinen verschwindenden Knoten mehr nach seiner Groesse"
  - "docs/reconcile.md: Abschnitt zur Wiederherstellung mit gemessenen Zahlen und der Grenze"
affects: [05-messbericht, 05-integration, 06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Aufgabenart mit langer Frist gehoert in die Warteschlangenart, deren Sperre und Anspruchsgroesse fuer diese Laenge gerechnet sind, nicht in eine laengere Frist innerhalb der kurzen Art"
    - "Die Zuordnung Dateiart zu Route steht in der Allowlist und wird im Poller abgelesen, nie ein zweites Mal geschrieben"
    - "Die Uebergabe an die zweite Spur sitzt unter dem schnellen Ausgang, damit ein zweiter Crawl keine Engine-Zeit wiederholt"
    - "Vier Wachen einer Ordner-Operation in einer Methode, damit eine fuenfte Operation nicht mit drei davon ankommt"

key-files:
  created:
    - .planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md
  modified:
    - backend/src/findling/worker/poller.py
    - backend/tests/test_poller.py
    - php/lib/Listener/FileEventListener.php
    - php/lib/BackgroundJobs/SubtreeExpandJob.php
    - docs/reconcile.md

key-decisions:
  - "Ein Bild wird zur OCR-Aufgabe statt zu einer Inhaltsaufgabe mit langer Frist: eine Inhaltsforderung nimmt bis zu 32 Zeilen unter einer Sperre von 900 s, zwei Dateien mit 660 s reissen sie, und die Zeilen enden als failed(repeatedly_stuck), obwohl der Worker legitim arbeitet. Die OCR-Spur ist mit 2 Zeilen unter 1800 s die eine Stelle, deren Zahlen fuer diese Laenge gerechnet sind"
  - "Die PHP-Seite braucht dafuer keine Aenderung: requeueAs setzt kind=ocr, nullt den Versuchszaehler und gibt die Sperre frei, die Zeile lebt danach unter LOCK_TIMEOUTS[ocr]=1800 und KIND_BATCH[ocr]=2"
  - "Die Uebergabe steht unter dem schnellen Ausgang, nicht darueber: der Inhaltsdurchgang liest und hasht die Bytes, ein zweiter Crawl ueber ein unveraendertes Bild wird ohne Arbeit bestaetigt und wiederholt keine Engine-Zeit"
  - "Bei abgeschalteter OCR bekommt ein Bild das ehrliche Verdikt skipped(no_text_layer) und die Engine startet nicht mehr hinter dem Ruecken des Admins"
  - "Annahme A9 ist gemessen falsch: eine Ordner-Wiederherstellung erzeugte null Queue-Zeilen. Fall eins des Plans, also gebaut"
  - "kind=content kommt in EXPANDABLE_KINDS, weil die Nachkommen eines wiederhergestellten Ordners aus dem Index heraus und mit einem Grabstein versehen sind; die Enge liegt auf der Aufrufseite, der Listener fordert content nur im Wiederherstellungszweig"
  - "Eine Inhaltsaufgabe aus einem Teilbaum traegt ihre echte Groesse, sonst nimmt eine Forderung 32 Dokumente beliebiger Groesse an der Byte-Obergrenze vorbei"

patterns-established:
  - "Vorzustand und Nachzustand derselben Nachstellung als Zahlenpaar in der Zusammenfassung, nicht als Behauptung"
  - "Ein Laufzeitimage mit echter Engine als Messumgebung, wenn der vollstaendige Stack einem anderen Agenten gehoert"

requirements-completed: [PKG-03]

# Metrics
duration: 95 min
completed: 2026-09-03
---

# Phase 5 Plan 04: Bilder auf der OCR-Spur und die Ordner-Wiederherstellung Summary

**Bilder werden ueber die bestehende OCR-Spur gelesen statt als Inhaltsaufgabe mit 120-Sekunden-Frist, wodurch `ocr_used` fuer sie gesetzt ist und der OCR-Anteil der Zaehler von gemessenen 0 auf 6 von 6 indexierten Dokumenten steigt; ein aus dem Papierkorb geholter Ordner erzeugt jetzt Inhaltsaufgaben je Nachkomme statt null Queue-Zeilen.**

## Performance

- **Duration:** 95 min
- **Started:** 2026-09-03T09:05:00Z
- **Completed:** 2026-09-03T10:40:00Z
- **Tasks:** 2
- **Files modified:** 5 (davon 1 neu)

## Accomplishments

- Ein Bild ist eine OCR-Aufgabe. Der Inhaltsdurchgang uebergibt es an die zweite Spur, und dort laeuft es mit der harten OCR-Frist von 660 s und den OCR-Deckeln (Seitenzahl, Seitenfrist, Jobfrist) statt mit den 120 s einer Textaufgabe. Ein mehrseitiges TIFF endet damit als `indexed(truncated)` und nicht als `failed(timeout)`.
- `ocr_used` ist fuer Bilder gesetzt. Gemessen ueber die sieben Bilder des Referenzkorpus mit echter Engine: **vorher `text=6, ocr=0`, nachher `text=0, ocr=6`**, alle sieben Zustandszeilen mit `ocr_used=1`. Die Endverdikte sind unveraendert (6 indexiert, 1 uebersprungen), die Zahlen des `readonly-gate` also auch.
- Annahme A9 ist beantwortet und zwar mit Zahlen: eine Ordner-Wiederherstellung erzeugte **null** Queue-Zeilen. Seit diesem Plan plant der Wiederherstellungszweig denselben Teilbaum-Job, den die Ordner-Freigabe und die Ordner-Loeschung benutzen, und produziert **drei** Inhaltsaufgaben mit ihren echten Groessen.
- Eine Loeschung fragt keinen verschwindenden Knoten mehr nach einer Groesse, die zweifach verworfen wird (Gruppe-B-IN-02).
- Acht neue Testfaelle in `backend/tests/test_poller.py`, sechs davon vor der Codeaenderung rot; mit echter Engine im Laufzeitimage laufen `test_poller.py` und `test_ocr.py` mit 115 Faellen gruen.

## Task Commits

1. **Task 1: Ein Bild ist eine OCR-Aufgabe, und ihr Aufwand ist sichtbar** (TDD)
   - `568c715` (test) - acht Faelle fuer den Bildzweig, sechs rot
   - `50af75c` (feat) - die Uebergabe im Inhaltszweig, plus die drei Kommentare, die vorher nur von Scans sprachen
2. **Task 2: Ein wiederhergestellter Ordner kommt zurueck, und eine Loeschung fragt keine Groesse** - `36f067e` (fix)
3. **Zurueckgestellte Punkte dieses Plans** - `8ae2d45` (docs)

## Files Created/Modified

- `backend/src/findling/worker/poller.py` - Der Inhaltszweig uebergibt eine Datei mit `route is Route.OCR` an die zweite Spur, unter dem schnellen Ausgang; die Kommentare an der OCR-Verzweigung, an `_read_the_scan` und an `_goes_to_the_ocr_track` nennen jetzt beide Dateiarten, die dort ankommen.
- `backend/tests/test_poller.py` - Acht Faelle: Uebergabe statt Textroute, `ocr_used` nach dem zweiten Durchgang, die OCR-Frist am mehrseitigen TIFF, das Verdikt eines Bildes ohne lesbaren Text, der OCR-Anteil der Zaehler, abgeschaltete OCR, die unveraenderte Textroute eines Dokuments und der schnelle Ausgang beim zweiten Crawl.
- `php/lib/Listener/FileEventListener.php` - `queueRestore()` fuer den Wiederherstellungszweig, `expandFolder()` als der eine Ort der vier Ordner-Wachen fuer die drei Aufrufer, und die Groesse eines Knotens wird bei einer Loeschung nicht mehr erfragt.
- `php/lib/BackgroundJobs/SubtreeExpandJob.php` - `kind=content` in `EXPANDABLE_KINDS` mit der Begruendung, warum das Argument von Plan 03-04 fuer die Wiederherstellung nicht gilt; eine Inhaltsaufgabe traegt ihre echte Groesse, die beiden anderen Arten weiter die Null.
- `docs/reconcile.md` - Abschnitt "Die Wiederherstellung aus dem Papierkorb: was sofort passiert", mit der Messtabelle und der Grenze (der Abgleich ist die Sicherung, nicht der Weg).
- `.planning/phases/05-.../deferred-items.md` - Drei Punkte, siehe unten.

## Decisions Made

### Die PHP-seitige Pruefung, die der Plan ausdruecklich verlangt

**Frage:** Muss die Aufgabe fuer ein Bild auch auf der PHP-Seite als OCR-Art entstehen, sonst faellt die Sperre vor der Bearbeitung ab?

**Antwort: ja, sie muss als OCR-Art existieren, und sie tut es ohne eine Aenderung auf der PHP-Seite.**

Die Rechnung, die den Ausschlag gab:

| Art | Zeilen je Forderung | Sperre | Rechnet fuer |
|---|---|---|---|
| `content` | 32 (`QueueService::KIND_BATCH`) | 900 s (`QueueMapper::LOCK_TIMEOUT`) | Aufgaben von Sekunden |
| `ocr` | 2 | 1800 s (`LOCK_TIMEOUTS[ocr]`) | zwei Aufgaben von je 660 s |

Die naheliegende Loesung, die auch die Deferred-Liste vorschlug, waere eine Zeile im Inhaltszweig, die dem Bild dieselbe lange Frist gibt. Sie loest das Fristproblem und bricht die Rechnung der Forderung: zwei Bilder mit je 660 s in einer Forderung von 32 Zeilen unter einer Sperre von 900 s bringen die ganze Forderung ueber ihre Sperre, die Zeilen werden erneut ausgegeben, waehrend der Worker legitim noch an ihnen arbeitet, und enden nach drei Ausgaben als `failed(repeatedly_stuck)`. Das ist genau der Fall, den der Kommentar an `KIND_BATCH` beschreibt.

Der Weg dorthin ist deshalb die vorhandene Uebergabe: `requeueAs` setzt `kind=ocr`, nullt den Versuchszaehler und gibt die Sperre frei, sodass die Zeile sofort wieder einsammelbar ist. Die PHP-Seite lernt keine neue Zeilenart und der Crawl keine neue Regel; es gibt keinen zweiten Mechanismus (T-05-16).

Der Preis ist ein zweiter Download je **geaendertem** Bild, derselbe Preis, den die Scan-Spur seit Plan 03-09 zahlt. Was der Umweg dafuer kauft, ist der schnelle Ausgang: der Inhaltsdurchgang liest und hasht die Bytes, also wird ein unveraendertes Bild beim naechsten `occ findling:index` ohne Arbeit bestaetigt. Waere ein Bild von Nextcloud aus direkt als `ocr`-Zeile entstanden, haette jeder Crawl die Engine-Zeit des ganzen Mounts wiederholt, denn der OCR-Zweig fragt `is_unchanged` bewusst nicht.

### Die Nachstellung der Ordner-Wiederherstellung

Nachgestellt am 03.09.2026 auf einem eigenen Test-Nextcloud (`nextcloud:34.0.3-apache`, SQLite, eigener Containername und eigener Port, die PHP-App aus **diesem** Worktree eingebunden; die Container der Nachbar-Wellen und der Haupt-Checkout wurden nicht angefasst). Alle Schritte ueber WebDAV, damit die Ereignisse wirklich feuern, kein Abgleich angestossen.

| Schritt | Zeilen in `oc_findling_queue` |
|---|---|
| Ordner mit drei Dateien angelegt | `content=3` |
| Ordner geloescht, Teilbaum-Kette abgearbeitet | `delete=4` (die drei Dateien plus der Ordner, alle mit `size=0`) |
| Warteschlange geleert, Ordner wiederhergestellt, **Code vor diesem Plan** | **`total=0`**, kein Findling-Job geplant |
| dasselbe mit dem Code dieses Plans | `SubtreeExpandJob{kind: content}` geplant, danach **`content=3`, 144 Bytes** |
| einzelne Datei geloescht und wiederhergestellt | `delete=1` (`size=0`), danach `content=1` (`size=48`) |

Damit ist Annahme A9 widerlegt: Plan 03-12 hat die Ordner-Wiederherstellung nicht behandelt, der Abgleich trug sie allein, und das sind auf der Vorgabekadenz bis zu 24 Stunden. Es war Fall eins des Plans, also wurde gebaut.

### Die Messung des OCR-Anteils

Gemessen im Laufzeit-Testimage mit echter Engine (tesseract 5.5.0), gegen einen echten Tantivy-Index und eine echte Zustandsdatenbank, mit dem Produktions-Extraktor hinter der Prozessgrenze; die sieben Bilder des Referenzkorpus als Warteschlange.

| | Durchgaenge | `Store.throughput` | `ocr_used` |
|---|---|---|---|
| vor diesem Plan | 1 (6 indexiert, 1 uebersprungen) | `text=6, ocr=0` | 0 in allen sieben Zeilen |
| nach diesem Plan | 2 (7 Uebergaben, dann 6 indexiert, 1 uebersprungen) | `text=0, ocr=6` | 1 in allen sieben Zeilen |

Die Endverdikte sind in beiden Faellen identisch und stimmen mit `testdata/CORPUS.md` ueberein (`22-icon.png` bleibt `skipped(image_not_ocrable)`, ohne dass die Engine startet). Die drei Zahlen `EXPECTED_INDEXED`/`EXPECTED_SKIPPED`/`EXPECTED_FAILED` des `readonly-gate` bleiben damit richtig; was sich aendert, ist die Zahl der Durchgaenge, und die Drain-Schleife wartet auf eine leere Warteschlange und nicht auf eine feste Zahl.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Der Weg fuer Bilder ist die Uebergabe an die OCR-Spur, nicht eine laengere Frist im Inhaltszweig**
- **Found during:** Task 1
- **Issue:** Die Deferred-Liste und der Plan schlugen vor, dem Bild im Inhaltszweig dieselbe lange Frist zu geben. Das bricht die Rechnung der Inhaltsforderung: 32 Zeilen unter einer Sperre von 900 s tragen keine zwei Aufgaben von je 660 s. Die Zeilen werden erneut ausgegeben und enden als `failed(repeatedly_stuck)`, waehrend der Worker arbeitet, also genau das Gegenteil des ersten must_have.
- **Fix:** Der Inhaltszweig uebergibt eine Datei mit `route is Route.OCR` an die vorhandene OCR-Spur (`requeue(kind=ocr)`), wo Sperre und Anspruchsgroesse fuer diese Laenge gerechnet sind. Die Frist, die erzwungene Route und `ocr_used` kommen damit aus dem bestehenden OCR-Zweig, es gibt keine zweite Stelle.
- **Files modified:** backend/src/findling/worker/poller.py, backend/tests/test_poller.py
- **Verification:** Acht Testfaelle, darunter der schnelle Ausgang beim zweiten Crawl; Messung im Laufzeitimage mit echter Engine (siehe Tabelle oben); die Pruefung der PHP-Rechnung steht oben unter "Decisions Made".
- **Committed in:** 568c715, 50af75c

**2. [Rule 1 - Bug] Bei abgeschalteter OCR startete die Engine trotzdem fuer Bilder**
- **Found during:** Task 1
- **Issue:** `judge` bildet die vier Bild-Mimetypes auf `Route.OCR` ab, unabhaengig von `FINDLING_OCR_ENABLED`. Ein Bild lief damit auf einer Instanz mit abgeschalteter OCR trotzdem durch Pillow und tesseract, also durch die Engine, die der Admin ausdruecklich abgeschaltet hat.
- **Fix:** Die Uebergabe geht durch `_goes_to_the_ocr_track`, das schon vorher auf `ocr_enabled` sah. Mit abgeschalteter OCR bekommt ein Bild jetzt das ehrliche `skipped(no_text_layer)` und die Zeile verlaesst die Warteschlange im selben Durchgang.
- **Files modified:** backend/src/findling/worker/poller.py
- **Verification:** `test_a_picture_stays_skipped_when_ocr_is_off` prueft, dass der Extraktor gar nicht gerufen wird.
- **Committed in:** 50af75c

**3. [Rule 3 - Blocking] `SubtreeExpandJob` verweigerte die Art, die der Plan vorschreibt**
- **Found during:** Task 2
- **Issue:** Der Plan verlangt "denselben Teilbaum-Job, den die Ordner-Freigabe schon benutzt". Der Job hat eine geschlossene Liste erlaubter Arten (`EXPANDABLE_KINDS`), und `content` stand nicht darin: ein Argument mit dieser Art waere mit einer Warnung verworfen worden.
- **Fix:** `KIND_CONTENT` in die Liste, mit der Begruendung, warum das Argument von Plan 03-04 ("ein Teilbaum aus Inhaltsjobs ist ein Neu-Crawl") fuer die drei Operationen gilt, fuer die es geschrieben wurde, und fuer die Wiederherstellung nicht: dort sind die Nachkommen aus dem Index heraus und mit einem Grabstein versehen. Die Enge liegt auf der Aufrufseite, der Listener fordert `content` nur im Wiederherstellungszweig.
- **Files modified:** php/lib/BackgroundJobs/SubtreeExpandJob.php
- **Verification:** Nachstellung auf dem Test-Nextcloud: der Job wird geplant, laeuft und erzeugt drei Inhaltsaufgaben (Tabelle oben).
- **Committed in:** 36f067e

**4. [Rule 2 - Missing Critical] Eine Inhaltsaufgabe aus einem Teilbaum haette mit Groesse null gezaehlt**
- **Found during:** Task 2
- **Issue:** Der Job schrieb bisher fuer jede Art `size=0`, weil weder eine Berechtigungsaufgabe noch eine Loeschung Bytes bewegt. Fuer eine Inhaltsaufgabe ist die Groesse dagegen das, woran eine Forderung ihr Byte-Budget bemisst: ein wiederhergestellter Ordner mit 32 grossen Dokumenten haette in einer Forderung an der Obergrenze von 64 MB vorbei gelegen und die Charge in die Sperre ihrer Art laufen lassen.
- **Fix:** Eine Inhaltsaufgabe traegt die echte Groesse aus dem Cache-Eintrag, den das Band ohnehin in der Hand hat; die beiden anderen Arten behalten die Null.
- **Files modified:** php/lib/BackgroundJobs/SubtreeExpandJob.php
- **Verification:** Nachstellung: `content=3` mit 144 Bytes, `delete=4` mit 0 Bytes.
- **Committed in:** 36f067e

**5. [Rule 2 - Missing Critical] Die vier Ordner-Wachen standen kurz davor, ein drittes Mal abgeschrieben zu werden**
- **Found during:** Task 2
- **Issue:** `queueDeletion` und `expandMovedFolder` pruefen dieselben vier Bedingungen, bevor ein Teilbaum geplant wird (Storage-Id, Root-Id, Anker-Id, indexierter Mount). Der neue Wiederherstellungszweig waere die dritte Kopie geworden, und eine vierte Ordner-Operation kommt dann eines Tages mit drei der vier Wachen an.
- **Fix:** `expandFolder(Folder $node, string $kind)` als der eine Ort der Wachen, benutzt von allen drei Zweigen. `expandMovedFolder` behaelt nur seinen eigenen Zusatz, den Vergleich der Mount-Identitaet.
- **Files modified:** php/lib/Listener/FileEventListener.php
- **Verification:** `php -l` gruen; Nachstellung ueber Loeschung (Teilbaum-Wache) und Wiederherstellung (dieselbe Wache) auf dem Test-Nextcloud.
- **Committed in:** 36f067e

---

**Total deviations:** 5 auto-fixed (2 Bugs, 2 fehlende kritische Funktionalitaet, 1 Blocker)
**Impact on plan:** Alle fuenf liegen innerhalb der Aufgabenstellung. Abweichung 1 ist die Antwort auf die Pruefung, die der Plan ausdruecklich verlangt hat, und sie erfuellt die must_haves genauer als der wortwoertliche Vorschlag: der Schluesselverweis "Bilder gehen ueber den OCR-Zweig" ist jetzt buchstaeblich wahr. Kein Scope Creep, keine neue Abhaengigkeit, kein neuer Mechanismus.

## Issues Encountered

- **Der lokale Stack war nicht benutzbar, wie er ist.** `scripts/dev/compose.yaml` traegt einen festen Containernamen, und der laufende `findling-nextcloud` bindet die PHP-App aus dem Haupt-Checkout ein, den ein Wave-Executor nicht anfassen darf; die HaRP-Stacks der Nachbar-Wellen gehoeren anderen Agenten. Geloest mit einem eigenen Container unter eigenem Namen und eigenem Port, der die PHP-App aus diesem Worktree einbindet, und der nach der Messung entfernt wurde. Damit ist die Nachstellung, die die Plaene 03-03 und 03-04 aus genau diesem Grund zurueckgestellt haben, in diesem Plan tatsaechlich gelaufen.
- **Kein tesseract auf der Entwicklungsmaschine.** Die Messung des OCR-Anteils lief deshalb im Laufzeit-Testimage (`findling-ocr-09-test`, tesseract 5.5.0), mit dem Quellstand dieses Worktrees ueber die site-packages gelegt. Dort laufen auch die elf Faelle, die auf der Host-Maschine als `needs_engine` uebersprungen werden: `test_poller.py` und `test_ocr.py` zusammen 115 gruen.
- **Ein Fund neben der Spur:** ein Nachlaeufer der Loeschexpansion kann eine sofortige Wiederherstellung wieder loeschen. Enges Fenster, echte Klasse, in `deferred-items.md` beschrieben und nicht hier behoben, weil die Behebung eine Formataenderung am Jobargument braucht und andere Plaene dieser Phase dieselbe Datei anfassen.

## Verification

| Gate | Ergebnis |
|---|---|
| `cd backend && uv run python -m pytest -q` | 783 passed, 11 skipped |
| dieselbe Suite im Laufzeitimage mit echter Engine (`test_poller.py`, `test_ocr.py`) | 115 passed, 0 skipped |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 78 files already formatted |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | ohne Fund |
| `php -l` fuer beide geaenderten PHP-Dateien | No syntax errors detected |
| Em-Dash (U+2014) und En-Dash (U+2013) in allen geaenderten Dateien | keine |
| Nachstellung Bilder (OCR-Anteil) | vorher `ocr=0`, nachher `ocr=6` |
| Nachstellung Ordner-Wiederherstellung | vorher 0 Zeilen, nachher 3 Inhaltsaufgaben |
| `readonly-gate` und `reconcile-and-dach` | nicht lokal ausfuehrbar (brauchen den CI-Stack). Ihre Zusicherungen sind geprueft: die Endverdikte des Korpus sind unveraendert (6 indexiert, 1 uebersprungen bei den Bildern, gemessen), die Drain-Schleife wartet auf eine leere Warteschlange, und kein Gate greppt die geaenderten PHP-Dateien (`test_exclusion_path_space.py`, der einzige Test, der den Listener liest, ist gruen) |

## User Setup Required

None - keine externe Konfiguration.

## Next Phase Readiness

- Der Messbericht der Phase (D-06) kann den OCR-Anteil jetzt als Zahl ausweisen statt als Luecke: `Store.throughput` trennt Text und OCR, und Bilder zaehlen auf der OCR-Seite mit.
- Der 50k-Lastkorpus enthaelt Bilder (D-02, OCR-Anteil ~20 %). Sie laufen ab jetzt mit der OCR-Frist und der OCR-Anspruchsgroesse, also mit derselben Rechnung, die die gescannten PDFs schon tragen. Erwartete Nebenwirkung fuer den Lauf: zwei Durchgaenge je Bild statt einem, und zwei Zeilen je Forderung statt 32, wenn der Rueckstand aus Bildern besteht.
- Offen und beschrieben: der Nachlaeufer-Fall der Loeschexpansion, der Kommentar in `integration.yml` und die Anzeige des OCR-Anteils auf der Statusseite (alle drei in `deferred-items.md` dieser Phase).

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-03*
