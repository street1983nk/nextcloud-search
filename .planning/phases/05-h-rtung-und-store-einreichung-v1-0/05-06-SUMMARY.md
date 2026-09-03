---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 06
subsystem: testing
tags: [tantivy, sqlite, threading, php, exclusions, snippets, sandbox]

# Dependency graph
requires:
  - phase: 02-suchkern
    provides: Snippet-Erzeugung, char_ranges, Extraktions-Sandkasten, Store-Schema
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: Statusseite, Diagnose, Ausschlussregeln, 04-REVIEW.md mit IN-01..IN-07
provides:
  - "Snippet-Hervorhebungen verschmelzen nicht mehr bei benachbarten Treffern"
  - "Snippet-Dekodierung mit ausdruecklichem errors-Verhalten, kein Suchabbruch bei einem Byte-Offset im Zeichen"
  - "char_ranges dekodiert den Fragment-Praefix einmal statt je Bereich"
  - "Sandkasten-Zaehler je Kindprozess, ein Zeitablauf kostet keinen zusaetzlichen Spawn"
  - "Statuspoll ohne Warnflut auf einem frischen Index"
  - "acl_totals ohne temporaeren B-Tree je Aufruf"
  - "Lesende Seite unter einer Sperre, keine leckende Store-Verbindung"
  - "degraded mit benannter Gueltigkeitsfrist statt Messung je Suche"
  - "Ausschlussregeln mit Punkt-Segment werden abgelehnt und gespeicherte gemeldet"
  - "Dateinamen mit Backslash sind wieder diagnostizierbar"
affects: [05-arm-lasttest, 05-store-artefakte, 06-semantik]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "threading.RLock um jeden Modul-Cache der lesenden Seite, weil jede Suche aus einem Worker-Thread kommt"
    - "Besitz einer geoeffneten Verbindung liegt bis zur Uebergabe an den Cache in einer lokalen Variablen mit try/finally"
    - "Benannte Gueltigkeitsfrist als Konstante mit Begruendung im Docstring statt einer Messung je Aufruf"
    - "Zwei getrennte Zaehlabfragen statt COUNT(DISTINCT), damit SQLite keinen ephemeren Index baut"
    - "Textuelles Gate ueber PHP-Methodenkoerper mit Selbsttests an gestellten Proben"

key-files:
  created:
    - backend/tests/test_read_side.py
  modified:
    - backend/src/findling/index/search.py
    - backend/src/findling/extract/sandbox.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/api/resources.py
    - php/lib/Service/ExclusionService.php
    - php/lib/Service/PathResolverService.php
    - php/lib/Settings/Section.php
    - backend/tests/test_snippet_offsets.py
    - backend/tests/test_sandbox.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_exclusion_path_space.py

key-decisions:
  - "IN-04 Variante eins: die Backslash-Umwandlung im Diagnosepfad entfaellt, weil ein Dateiname mit Backslash sonst nicht nachschlagbar ist und die Umwandlung ohnehin der einzige Ort war, an dem ein Pfad hier etwas anderes bedeutete als in ExclusionService"
  - "errors=ignore bei der Snippet-Dekodierung: ein Snippet darf ein Zeichen verlieren, eine Suche darf nicht mit einer Ausnahme enden (T-05-22)"
  - "acl_totals als zwei Abfragen ueber den vorhandenen acl_file-Index; eine mitgefuehrte Summe wurde abgewogen und verworfen, weil sie eine zweite Stelle waere, die die Zahlen zu kennen behauptet"
  - "DEGRADED_TTL_SECONDS = 5.0, kuerzer als jeder Admin-Poll und kurz genug fuer eine gerade vollgelaufene Platte"
  - "threading.RLock statt Lock, weil degraded seinen Befund innerhalb der Sperre berechnet und version_drift dieselbe Sperre erneut nimmt"
  - "Ein unbrauchbarer gespeicherter Ausschlusseintrag wird mit einer Zeile je Lesevorgang gemeldet, nicht je Eintrag, nach dem Muster des WR-06-Befundes"

patterns-established:
  - "Sperre um Modulzustand: jeder Cache in findling.api.resources wird nur unter _LOCK gelesen und ersetzt"
  - "Verbindungsbesitz: open bis Cache-Uebergabe in einer lokalen Variablen, Freigabe im finally"
  - "Warnstufe nach Bedeutung: der Normalzustand eines frischen Containers ist debug, ein wirklich unerwarteter Zustand ist warning"
  - "Abfrageform als Modulkonstante, damit ein Test ihren Ausfuehrungsplan festnageln kann"
  - "Gate-Selbsttests: jede neue Feststellung eines textuellen Gates kommt mit sauberer Probe und gestellten Bruechen"

requirements-completed: [PKG-05]

# Metrics
duration: 66 min
completed: 2026-09-03
---

# Phase 5 Plan 06: Review-Kleinreste aus den Phasen 2 bis 4 Summary

**Neun benannte Audit-Positionen geschlossen: getrennte Hervorhebungen bei benachbarten Treffern, keine Ausnahme mehr bei einem Byte-Offset mitten im Zeichen, Praefix nur einmal dekodiert, Sandkasten-Zaehler je Kindprozess, Statuspoll ohne Warnflut und ohne temporaeren B-Tree, lesende Seite unter Sperre und ohne leckende Verbindung, abgelehnte Punkt-Segmente in Ausschlussregeln und ein Dateiname mit Backslash, der wieder diagnostizierbar ist.**

## Performance

- **Duration:** 66 min
- **Started:** 2026-09-03T08:27:00Z
- **Completed:** 2026-09-03T09:33:33Z
- **Tasks:** 3 von 3
- **Files modified:** 12 (11 geaendert, 1 neu)

## Accomplishments

- **Snippets:** Das `<=` der Bereichszusammenfassung ist ein `<`, also bleiben zwei aneinandergrenzende Treffer zwei Hervorhebungen; ueberlappende Bereiche verschmelzen weiterhin. Die Dekodierung traegt `errors="ignore"`, ein Byte-Offset mitten in einem Mehrbyte-Zeichen kostet hoechstens ein Zeichen statt der ganzen Suche. Der Fragment-Praefix wird einmal fuer alle Bereiche dekodiert, nicht je Bereich neu.
- **Sandkasten:** Der Zaehler der bearbeiteten Dateien wird nur noch erhoeht, wenn ein Kindprozess die Antwort ueberlebt hat. Nach einem Zeitablauf beginnt der Nachfolger bei null, statt sofort als benutzt zu gelten und eine Datei zu frueh erneuert zu werden.
- **Statuspoll:** Ein fehlendes Indexverzeichnis ist der Normalzustand der ersten Minuten und wird auf debug gemeldet; ein Pfad, der existiert und kein Verzeichnis ist, warnt weiterhin. `acl_totals` stellt zwei Abfragen statt einer mit `COUNT(DISTINCT)`: gemessen 14,4 ms gegen 8,9 ms auf 150.000 Zeilen ueber 50.000 Dokumenten, und im Ausfuehrungsplan steht kein `USE TEMP B-TREE` mehr.
- **Lesende Seite:** `_OPEN`, `_MARKS` und der neue degraded-Befund werden nur unter einem `threading.RLock` gelesen und ersetzt. Vier gleichzeitige Threads oeffnen jetzt genau eine Verbindung (vorher vier, davon drei verwaist). Eine Verbindung, die den Cache nicht erreicht, wird im `finally` geschlossen, und ein Handle fuer ein Volume, das nicht mehr das eingestellte ist, wird geschlossen statt vergessen.
- **degraded:** Der Befund gilt `DEGRADED_TTL_SECONDS` (5 s) und kostet nicht mehr je Suche einen Meta-Lesevorgang plus `disk_usage`. Kein Index bleibt ohne Messung sofort degradiert.
- **Ausschlussregeln:** `normalise()` lehnt ein `.`-Segment genauso ab wie `..`. Ein bereits gespeicherter Eintrag mit Punkt-Segment ist nicht in Kraft, nicht auf der Seite und wird mit einer Zeile je Lesevorgang gemeldet, mit Zahlen und ohne Wert.
- **Diagnose:** Die Backslash-Umwandlung ist weg, ein Dateiname wie `a\b.pdf` ist wieder ueber den Pfad nachschlagbar.
- **Docblock:** Section.php begruendet den Verzicht auf `#[\Override]` mit der Versionsspanne 8.2 gegen 8.3 statt mit einem Parse-Fehler, den es auf 8.2 nicht gibt. Am Code der Klasse hat sich nichts geaendert.

## Task Commits

1. **Task 1: Snippets und Sandkasten** (TDD)
   - `a3b0fa5` test(05-06): drei rote Faelle (benachbarte Treffer, Offset im Zeichen, Zaehler nach Zeitablauf)
   - `ddcbcbe` fix(05-06): Trennung, errors-Verhalten, einmalige Praefix-Dekodierung, Zaehler je Kind
2. **Task 2: Statuszahlen ohne Warnflut, ohne Full-Scan, ohne offene Verbindung** (TDD)
   - `7a5c4c7` test(05-06): fuenf rote Faelle (Warnung, temporaerer B-Tree, vier Threads, Fehlerlauf, degraded)
   - `e2ea9d2` fix(05-06): Warnstufe, zwei Zaehlabfragen, Sperre, Verbindungsbesitz, degraded-Frist
3. **Task 3: Drei Positionen der PHP-Haelfte** - `b342534` fix(05-06)

## Files Created/Modified

- `backend/src/findling/index/search.py` - `char_ranges` dekodiert den Praefix einmal, `errors="ignore"`, strenge Verschmelzungsbedingung, neuer Helfer `_inside` fuer die Klammerung eines gemeldeten Offsets
- `backend/src/findling/extract/sandbox.py` - `files_handled` als lesende Eigenschaft, Zaehler nur bei ueberlebendem Kindprozess
- `backend/src/findling/store/repo.py` - `_ACL_ROWS_SQL` und `_ACL_DOCUMENTS_SQL` als Konstanten, `acl_totals` in zwei Abfragen, `index_bytes` warnt nur noch bei einem Pfad, der kein Verzeichnis ist
- `backend/src/findling/api/resources.py` - `_LOCK` (RLock), `_DEGRADED`-Cache, `DEGRADED_TTL_SECONDS`, Verbindungsbesitz mit try/finally, Freigabe eines veralteten Handles
- `php/lib/Service/ExclusionService.php` - `.`-Segment abgelehnt, unbrauchbare gespeicherte Eintraege gemeldet
- `php/lib/Service/PathResolverService.php` - Backslash-Umwandlung entfernt, Entscheidung im Docblock
- `php/lib/Settings/Section.php` - Docblock korrigiert (nur Kommentarzeilen)
- `backend/tests/test_read_side.py` - **neu**, acht Faelle: vier Threads mit einer Verbindung, Fehlerlauf ohne offene Verbindung, ersetztes Volume, degraded-Fenster in beiden Richtungen, Versionsmarken aus vier Threads
- `backend/tests/test_snippet_offsets.py` - drei Faelle: benachbarte Treffer, Offset mitten im Zeichen, mehrere Bereiche unveraendert
- `backend/tests/test_sandbox.py` - zwei Faelle: kein Zaehler nach Zeitablauf, Zaehler nach echter Arbeit
- `backend/tests/test_store_repo.py` - Warnung nur bei einem Pfad, der kein Verzeichnis ist; Gleichheit und Laufzeit von `acl_totals` auf 6.000 Zeilen; Ausfuehrungsplan ohne temporaeren B-Tree
- `backend/tests/test_exclusion_path_space.py` - fuenfte Feststellung des Gates: Validierung und Vergleich haben einen Ausgang fuer ein Punkt-Segment, mit sauberer Probe und vier gestellten Bruechen

## Decisions Made

### IN-04, die verlangte Entscheidung: Variante eins

Die Backslash-Umwandlung in `PathResolverService::fileIdOfPath()` ist entfallen.

**Begruendung.** Ein Backslash ist ein zulaessiges Zeichen in einem Nextcloud-Dateinamen, und `ExclusionService::trimmed()` bewahrt ihn seit Phase 2 aus genau diesem Grund. Die Umwandlung war damit die einzige Stelle der App, an der ein Pfad etwas anderes bedeutete als ueberall sonst: sie zerlegte den Namen `a\b.pdf` in zwei Segmente und liess den Lauf nach einem Ordner fragen, den niemand hat. Der Preis war die Antwort auf "warum ist diese Datei nicht indexiert" fuer eine ganze Klasse von Namen, also genau die Frage, fuer die Phase 4 gebaut wurde.

**Was es kostet.** Wer `alice\files\x.pdf` einfuegt, bekommt jetzt dasselbe null wie bei jeder anderen unaufloesbaren Eingabe, also einmal neu tippen. Keine der beiden Schreibweisen, die die Seite zeigt, traegt einen Backslash: die Fehlerliste schreibt `alice/files/Ordner/x.pdf`, die Kurzform ist `alice:Ordner/x.pdf`, und `docs/admin-page.md` nennt ebenfalls keine Windows-Schreibweise. Die Aenderung fuegt keinen Pfadraum hinzu, sie entfernt einen. Variante eins war damit ohne zweiten Pfadraum machbar, also gilt sie; `docs/admin-page.md` wurde nicht angefasst.

### acl_totals: zwei Abfragen, keine mitgefuehrte Summe

Die alte Form baute laut Ausfuehrungsplan (`USE TEMP B-TREE FOR count(DISTINCT)`) je Aufruf einen ephemeren Index mit einem Eintrag pro Dokument. Auf der 50k-Zielbox war das mehrmals pro Minute eine temporaere Struktur in Korpusgroesse, auf einer Box mit 4 GB Gesamtbudget. Die neue Form fragt zweimal: `COUNT(*)` und `COUNT(*)` ueber `SELECT DISTINCT file_id`, das den vorhandenen `acl_file`-Index in Reihenfolge liest, sodass der Distinct-Schritt ein Vergleich mit der Vorzeile ist und keinen Speicher kostet.

Eine mitgefuehrte Summe (Zaehler bei jedem ACL-Schreibvorgang) waere schneller und wurde verworfen: sie waere eine zweite Stelle im Container, die die Zahlen zu kennen behauptet, und der Modulkopf von `repo.py` argumentiert genau dagegen fuer den Arbeitsvorrat. Nach dem ersten harten Kill widersprechen Zaehler und Tabelle sich, und die Admin-Seite nennt dann eine Korpusgroesse, die nichts auf der Platte stuetzt.

### errors="ignore" statt Klammerung auf Zeichengrenzen

Bei einem Bereichsende mitten in einem Mehrbyte-Zeichen wird das angebrochene Zeichen verworfen. Alternative waere ein Zurueckschieben auf die Zeichengrenze gewesen; das haette sauberere Zahlen geliefert, aber `errors=` waere damit unerreichbarer Verteidigungscode geworden, weil die Bytes aus `fragment.encode()` stammen und immer gueltiges UTF-8 sind. Ein Snippet verliert lieber ein Zeichen, als dass eine Suche mit einer Ausnahme endet, und die Konsequenz ist im Kommentar benannt.

### Punkt-Segment: abgelehnt statt gefiltert, gemeldet statt UI-Element

Abgelehnt und nicht gefiltert, aus demselben Grund wie bei `..`: `Archiv/./x` heruntergefiltert auf `Archiv/x` wuerde einen Ordner ausschliessen, den der Admin nicht getippt hat.

Fuer die Meldung eines bereits gespeicherten unwirksamen Eintrags wurde das Muster des WR-06-Befundes derselben Datei uebernommen: eine Warnung mit Zahlen (`unusable`, `inForce`) und ohne Wert, eine Zeile je Lesevorgang statt je Eintrag, damit die Meldung eine Meldung bleibt und nicht die Logflut von IN-01 wird. Kein neues UI-Element, weil die etablierte Antwort dieser Datei auf denselben Fall ebenfalls eine Warnzeile ist.

### DEGRADED_TTL_SECONDS = 5.0

Kuerzer als jeder Poll der Admin-Seite und kuerzer als die Geduld von jemandem, der gerade ein Volume vollgeschrieben hat. Oberhalb einer Minute waere die Marke kein Betriebssignal mehr, unterhalb einer Sekunde spart sie nichts. Die Frist steht als benannte Konstante mit Begruendung und zusaetzlich im Docstring von `degraded()`, weil sie bestimmt, wie schnell sich eine Suche als degradiert meldet.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Neue Testdatei backend/tests/test_read_side.py statt Faelle in test_store_repo.py**
- **Found during:** Task 2
- **Issue:** Der Plan nennt fuer Task 2 die Dateien `store/repo.py`, `api/resources.py` und `tests/test_store_repo.py`. Die sechs verlangten Verhaltensweisen betreffen aber zur Haelfte `api/resources.py`, und fuer dieses Modul gibt es keine Testdatei. Die Faelle in `test_store_repo.py` unterzubringen haette die Store-Tests mit Fixtures aus `conftest.py` (Index, Volume, Wortliste) vermischt, die dort nicht hingehoeren, und die Endpunkttests durften laut Akzeptanzkriterium nicht angefasst werden.
- **Fix:** `backend/tests/test_read_side.py` neu angelegt, mit dem Dateikopf-Stil der uebrigen Suiten und acht Faellen. Die Store-Faelle (Warnung, acl_totals) sind wie geplant in `test_store_repo.py`.
- **Files modified:** backend/tests/test_read_side.py (neu)
- **Verification:** `uv run python -m pytest -q` gruen (797 passed, 11 skipped), alle vier Qualitaetsgates gruen
- **Committed in:** `7a5c4c7` und `e2ea9d2`

**2. [Rule 2 - Missing Critical] Lesende Eigenschaft ExtractionWorker.files_handled**
- **Found during:** Task 1
- **Issue:** Die verlangte Verhaltensweise "der Zaehler beginnt bei diesem Prozess bei null" ist von aussen nicht beobachtbar, weil `_start_child()` den Zaehler beim Start eines neuen Kindes ohnehin auf null setzt. Der Fehler war deshalb latent, und ohne einen Zugang waere er nur mit einem Zugriff auf ein privates Feld pruefbar gewesen.
- **Fix:** `files_handled` als lesende Eigenschaft ergaenzt, symmetrisch zur vorhandenen `pid`-Eigenschaft, mit der Invariante im Docstring.
- **Files modified:** backend/src/findling/extract/sandbox.py
- **Verification:** Beide neuen Sandkasten-Faelle waren vor der Aenderung rot, danach gruen; vulture meldet nichts
- **Committed in:** `ddcbcbe`

**3. [Rule 1 - Bug] Ein veraltetes Handle wurde beim frueheren Ausstieg nicht geschlossen**
- **Found during:** Task 2
- **Issue:** Nicht in der Befundliste. In `read_side()` stand die Freigabe des alten Handles hinter den zwei Existenzpruefungen, sodass der Zweig fuer ein Volume, das noch nichts hat, daran vorbeilief: die Verbindung lebte weiter, ohne dass etwas auf sie zeigte. Das ist derselbe Leck-Typ wie IN-06, nur ohne Nebenlaeufigkeit, und der Weg, den eine Testsuite bei jedem Test geht.
- **Fix:** Die Freigabe steht jetzt vor den Pruefungen. Das Verhalten fuer ein unveraendertes Volume ist unberuehrt, weil der Cache-Treffer weiter oben zurueckkehrt.
- **Files modified:** backend/src/findling/api/resources.py
- **Verification:** `test_a_volume_that_is_replaced_closes_the_handle_it_had` war vor der Aenderung rot (DID NOT RAISE ProgrammingError)
- **Committed in:** `e2ea9d2`

**4. [Rule 3 - Blocking] php -l gegen eine Kopie im Container statt gegen das gemountete Verzeichnis**
- **Found during:** Task 3
- **Issue:** Das Akzeptanzkriterium nennt `docker compose exec app ... /var/www/html/custom_apps/findling/lib`. Dieses Verzeichnis ist ein Bind-Mount des Haupt-Checkouts; ein Worktree-Agent darf dort nicht schreiben und wuerde ohnehin die unveraenderten Dateien pruefen.
- **Fix:** Die PHP-Haelfte des Worktrees wurde per `docker cp` nach `/tmp/findling-lint` im laufenden `findling-nextcloud`-Container gelegt und dort geprueft, danach wieder entfernt. Dieselbe PHP-Laufzeit, geaenderte Dateien.
- **Files modified:** keine
- **Verification:** 33 Dateien, 33 Zeilen Ausgabe, 0 Zeilen ungleich "No syntax errors detected" (PHP 8.5.9 im Container)
- **Committed in:** keine (Verifikationsschritt)

**5. [Rule 3 - Blocking] Verhaltensbeweis der PHP-Haelfte per Wegwerf-Sonde statt ueber die Admin-Seite**
- **Found during:** Task 3
- **Issue:** Das Kriterium verlangt "auf dem lokalen Stack protokolliert", dass eine Regel mit Punkt-Segment abgelehnt wird und eine gueltige weiterhin angenommen. Es gibt keine PHP-Testumgebung im Repository, und das App-Verzeichnis des Stacks ist der Bind-Mount des Haupt-Checkouts, also nicht beschreibbar.
- **Fix:** Zwei Wegwerf-Sonden im Scratchpad, im PHP des Stacks gegen die Worktree-Kopie ausgefuehrt: `normalise()`/`validate()` direkt und `prefixes()` mit gestellter appconfig. Ergebnisse unter "Issues Encountered" protokolliert. Die Sonden liegen ausserhalb des Repositories und sind nicht committet.
- **Files modified:** keine
- **Verification:** siehe Protokoll unten
- **Committed in:** keine (Verifikationsschritt)

---

**Total deviations:** 5 auto-fixed (1 Bug, 1 fehlende Kritikalitaet, 3 Blocker)
**Impact on plan:** Kein Scope-Creep. Deviation 3 ist ein Fehler derselben Klasse wie der geplante und im selben Absatz. Die uebrigen vier sind Anpassungen an die Worktree-Isolation und an die Beobachtbarkeit, die der Plan verlangt.

## Issues Encountered

### Protokoll der PHP-Sonden (PHP 8.5.9 im Container findling-nextcloud, Worktree-Kopie)

Eingabeseite, `normalise()`:

```
./Archiv         -> REFUSED
Archiv/./x       -> REFUSED
.                -> REFUSED
files/./Backups  -> REFUSED
..               -> REFUSED
Archiv/../..     -> REFUSED
Archiv           -> 'Archiv'
files/Backups    -> 'Backups'
Backups/2026     -> 'Backups/2026'
a\b              -> 'a\b'
```

Eingabeseite, `validate()`: `./Archiv`, `Archiv/./x` und `Archiv/../..` antworten `["traversal"]`, `Archiv` und `files/Backups` antworten `[]`. Eine gueltige Regel wird also weiterhin angenommen, die `files/`-Vorhut faellt wie bisher weg und ein Backslash bleibt ein Zeichen des Namens.

Meldung: `Findling: refused an exclusion entry that is not a usable folder path | {"rejected":N}` - nennt den Fall und nicht den Wert. Die Gegenprobe ueber alle Logzeilen nach den eingereichten Werten (`Archiv`, `Backups`, `./`, `..`) antwortet "no".

Leseseite, `prefixes()` mit gestellter appconfig:

```
stored ["Archiv","files/Backups"]              -> in force ["Archiv","Backups"]
stored ["./Archiv","Backups"]                  -> in force ["Backups"]
    log: ... neither in force nor shown | {"unusable":1,"inForce":1}
stored ["Archiv/./x"]                          -> in force []
    log: ... neither in force nor shown | {"unusable":1,"inForce":0}
stored ["Archiv/../..","./Archiv","Backups"]   -> in force ["Backups"]
    log: ... neither in force nor shown | {"unusable":2,"inForce":1}
stored []                                      -> in force []
```

Eine bereits gespeicherte Regel mit Punkt-Segment verschwindet also nicht still: sie ist nicht in Kraft, nicht auf der Seite und wird gemeldet. Eine saubere Liste erzeugt keine Zeile.

### Gate-Gegenprobe

Die fuenfte Feststellung von `test_exclusion_path_space.py` wurde gegen die Fassung vor der Aenderung laufen gelassen und meldet dort genau einen Befund (`normalise() does not refuse a '.' segment ...`), gegen die neue Fassung nichts. Das Gate ist damit nicht vakuum-gruen.

### acl_totals-Laufzeit

Protokolliert im Test (`acl_totals over 6000 rows took 0.495 ms`). Der Groessenvergleich der Formen wurde gesondert gemessen: auf 150.000 Zeilen ueber 50.000 Dokumenten 14,39 ms fuer die alte Einzelabfrage gegen 8,92 ms fuer die zwei neuen, und im Ausfuehrungsplan verschwindet `USE TEMP B-TREE FOR count(DISTINCT)`.

### Verbliebene COUNT(DISTINCT)-Vorkommen

`grep -c 'COUNT(DISTINCT' backend/src/findling/store/repo.py` ist 2, nicht 0. Beide Vorkommen stehen in Kommentaren und benennen die Form, die ersetzt wurde (Zeile 190 im Konstantenblock, Zeile 876 im Docstring von `acl_totals`). In SQL, das ausgefuehrt wird, kommt `COUNT(DISTINCT` nicht mehr vor; das Kriterium erlaubt verbleibende Vorkommen ausdruecklich, wenn sie im Kommentar begruendet sind.

### Nichts angepasst, um eine Aenderung zu ermoeglichen

Kein bestehender Testfall wurde geaendert, damit die Aenderung durchgeht. Ausnahme mit Begruendung: `test_index_bytes_reports_zero_for_a_directory_that_is_not_there` in `test_store_repo.py` verlangte bisher eine Warnung fuer das fehlende Indexverzeichnis; das war genau der Befund IN-01, also ist die Erwartung umgedreht (keine Warnung) und der wirklich unerwartete Fall in einen zweiten Fall ausgelagert. Die bestehenden Umlaut-Offset-Tests und alle Endpunkttests sind unveraendert gruen; die Antwortformen von `/status` und `/rates` sind unberuehrt.

## Known Stubs

Keine.

## Threat Flags

Keine neue sicherheitsrelevante Oberflaeche. Alle drei Vertrauensgrenzen des Plans sind die Grenzen, an denen gearbeitet wurde, und die vier Positionen des Registers sind adressiert:

| Threat ID | Umsetzung |
|-----------|-----------|
| T-05-22 | `errors="ignore"` bei der Dekodierung, Fall "Offset mitten im Zeichen" als Test |
| T-05-23 | `threading.RLock` um jede Bearbeitung, Test mit vier Threads, Verbindung im `finally` geschlossen |
| T-05-24 | Punkt-Segmente abgelehnt, gespeicherte unwirksame Regeln gemeldet, Pfadraum-Gate prueft beide Seiten |
| T-05-SC | Kein Paket installiert; `uv.lock` und `pyproject.toml` unberuehrt |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Alle neun Positionen aus 05-RESEARCH.md, Abschnitt "Offen, gehoert nach D-20 in diese Phase", sind geschlossen. D-20 ist fuer diesen Plan erfuellt; keine Position ist stillschweigend vertagt.
- `DEGRADED_TTL_SECONDS` ist relevant fuer den ARM-Lasttest: der Backend-Offline-Drill aus D-05 muss die Frist von fuenf Sekunden abwarten, bevor er "Suche degradiert sauber" ablesen kann.
- Die Messwerte von `acl_totals` (8,9 ms auf 150.000 Zeilen) und der entfallene ephemere Index sind Zahlen fuer `docs/performance.md` aus D-06.
- Offen und nicht Teil dieses Plans: IN-02 (tote Uebersetzungsschluessel) und IN-03 (NBSP-Wechsel) aus 04-REVIEW.md; beide waren nicht in der Positionsliste dieses Plans.
- Die PHP-Haelfte hat weiterhin keine Testumgebung. Die drei Aenderungen sind per `php -l` und Wegwerf-Sonde belegt, ein PHPUnit-Aufbau ist Sache von D-24.

## Self-Check: PASSED

- `backend/tests/test_read_side.py` liegt auf der Platte (FOUND)
- Alle elf geaenderten Dateien liegen auf der Platte (FOUND)
- Commits vorhanden: `a3b0fa5`, `ddcbcbe`, `7a5c4c7`, `e2ea9d2`, `b342534` (FOUND)
- `cd backend && uv run python -m pytest -q`: 797 passed, 11 skipped
- `uv run ruff check .` / `ruff format --check .` / `pyright` / `vulture src tests --min-confidence 80`: alle gruen
- `php -l` ueber 33 PHP-Dateien: ausschliesslich "No syntax errors detected"
- `grep -c 'errors=' backend/src/findling/index/search.py`: 2 (> 0)
- Kein Em-Dash (U+2014) und kein En-Dash (U+2013) in einer geaenderten Datei

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-03*
