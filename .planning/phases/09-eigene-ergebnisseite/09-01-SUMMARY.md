---
phase: 09-eigene-ergebnisseite
plan: 01
subsystem: api
tags: [php, exapp, appapi, zeitbudget, messung, phpunit]

requires:
  - phase: 05-haertung
    provides: ExAppService mit REQUEST_TIMEOUT_SECONDS, MIN_CALL_SECONDS und dem proxyRequest-Test-Double
  - phase: 06-semantik
    provides: Messbericht 2026-09-05-semantiklauf-m7g mit den einzigen p95-Zahlen des hybriden Suchfalls
provides:
  - Messbericht docs/measurements/2026-09-seitenbudget/ mit fuenf Reihen, Rohdaten und Herleitung
  - PAGE_BUDGET_SECONDS = 3.0 als Zahl fuer die Seitenroute (Eingabe fuer Plan 09-04)
  - ExAppService::PAGE_REQUEST_TIMEOUT_SECONDS = 1.5 mit Messdatum und Berichtspfad im Docblock
  - ceilingSeconds als durchgereichter Parameter von searchCandidates, snippets und call
  - Verdikt zu Annahme A3 der 09-RESEARCH
affects: [09-04, 09-05, 09-08, Provider, PageController]

tech-stack:
  added: []
  patterns:
    - "Per-Call-Deckel als Argument mit dem alten Wert als Standard statt zweitem Aufrufpfad"
    - "Gemessene Konstanten tragen Zahl, Messdatum und Berichtspfad im Docblock"

key-files:
  created:
    - docs/measurements/2026-09-seitenbudget/README.md
    - docs/measurements/2026-09-seitenbudget/raw/reihe-a.txt
    - docs/measurements/2026-09-seitenbudget/raw/reihe-b.txt
    - docs/measurements/2026-09-seitenbudget/raw/reihe-c.txt
    - docs/measurements/2026-09-seitenbudget/raw/kandidatenaufruf.txt
    - docs/measurements/2026-09-seitenbudget/raw/snippetaufruf.txt
    - docs/measurements/2026-09-seitenbudget/raw/zusatz-snippet-gegenprobe.tsv
  modified:
    - php/lib/Service/ExAppService.php
    - php/tests/Unit/ExAppServiceTest.php

key-decisions:
  - "PAGE_REQUEST_TIMEOUT_SECONDS = 1.5: die Messung stuetzt keine hoehere Zahl, es entscheidet die Untergrenze der Planregel"
  - "PAGE_BUDGET_SECONDS = 3.0 statt der 1.5 aus der Planformel, weil 1.5 die Seite ungeduldiger machen wuerde als den Dialog"
  - "Der Deckel wird Parameter von call() statt zweiter Aufrufpfad, damit die vier Fehlerfaelle nicht verdoppelt werden"
  - "Der Ausreisser von 1,944 s bleibt in den Rohdaten und begruendet trotzdem keine Konstante"

patterns-established:
  - "Messbericht vor Konstante: eine Zahl im Code zitiert einen Bericht mit Rohdaten und Datum"
  - "Ein Test, der wegen gleicher Konstanten nicht scheitern koennte, bekommt eine zweite Zusicherung mit einem erhoehten Wert"

requirements-completed: [UI-01]

duration: 95min
completed: 2026-09-09
---

# Phase 9 Plan 01: Zeitbudget gemessen und Per-Call-Deckel parametriert Summary

**Fuenf Messreihen auf der lokalen Test-Nextcloud beantworten Annahme A3 mit ja (p95 eines Kandidatenaufrufs 0,022 s), und `ExAppService::call()` nimmt ab jetzt einen `ceilingSeconds`-Parameter, sodass ein groesseres Seitenbudget ueberhaupt wirken kann.**

## Performance

- **Duration:** rund 95 min
- **Started:** 2026-09-09T00:05Z (ungefaehr, Beginn der Zustandsarbeit am Container)
- **Completed:** 2026-09-09T01:40Z
- **Tasks:** 3
- **Files modified:** 9 (7 neu, 2 geaendert)

## Accomplishments

- Die Test-Nextcloud steht wieder auf dem Repo-Stand: `occ upgrade` gefahren, `needsDbUpgrade` ist `false`, die App traegt 1.0.3 statt 0.3.0, die Warteschlange ist leer.
- Der Korpus reicht jetzt fuer eine volle Kandidatenseite: 300 synthetische Dateien aus `build_load_corpus.py` (Seed `phase9-budget`) dazugelegt und indiziert, 429 indizierte Dokumente, der Begriff `Bescheid` fuellt `limit=100` und meldet `hasMore`.
- Fuenf Messreihen zu je 20 Wiederholungen gefahren, drei ueber die OCS-Dialogroute und zwei direkt gegen die Container-Routen, alle Rohwerte unbearbeitet abgelegt.
- Annahme A3 beantwortet: **ja**, ein Kandidatenaufruf mit `limit=100` bleibt mit p95 0,022 s und max 0,024 s weit unter dem 1,5-s-Deckel.
- `PAGE_REQUEST_TIMEOUT_SECONDS` existiert als oeffentliche Konstante mit Zahl, Messdatum und Berichtspfad, und `call()`, `searchCandidates()` und `snippets()` reichen den Deckel als Argument durch. `REQUEST_TIMEOUT_SECONDS` bleibt unveraendert 1.5 und bleibt der Standard.
- Drei neue Testfaelle halten fest, dass der Dialogweg unveraendert bleibt, dass ein uebergebener Deckel wirklich durchreist und dass ein kleineres Restbudget ihn schlaegt.

## Task Commits

1. **Task 1: Die lokale Test-Nextcloud auf den Repo-Stand bringen** - kein Commit (reine Zustandsarbeit am Container, der Plan nennt ausdruecklich keine Repo-Dateien; das Ergebnis steht als Ausgangslage in Abschnitt 1 des Messberichts)
2. **Task 2: Drei Messreihen fahren und den Bericht schreiben** - `256b215` (docs)
3. **Task 3: Den Per-Call-Deckel parametrieren** - `014de1c` (feat)

## Files Created/Modified

- `docs/measurements/2026-09-seitenbudget/README.md` - Ausgangslage, Verfahren, Zahlentabelle, Verdikt zu A3, vier Befunde, Herleitung beider abgeleiteter Zahlen, Nachstellanleitung
- `docs/measurements/2026-09-seitenbudget/raw/reihe-a.txt` - 20 Werte, OCS, ein Wort, nur Dateiname
- `docs/measurements/2026-09-seitenbudget/raw/reihe-b.txt` - 20 Werte, OCS, ein Wort, Inhalt
- `docs/measurements/2026-09-seitenbudget/raw/reihe-c.txt` - 20 Werte, OCS, zwei Woerter, Inhalt
- `docs/measurements/2026-09-seitenbudget/raw/kandidatenaufruf.txt` - 20 Werte, `POST /search` mit `limit=100`
- `docs/measurements/2026-09-seitenbudget/raw/snippetaufruf.txt` - 20 Werte, `POST /snippets` mit 25 Dateien
- `docs/measurements/2026-09-seitenbudget/raw/zusatz-snippet-gegenprobe.tsv` - 80 weitere Snippet-Aufrufe als Gegenprobe zum Ausreisser
- `php/lib/Service/ExAppService.php` - neue Konstante `PAGE_REQUEST_TIMEOUT_SECONDS`, `ceilingSeconds` an drei Methoden, `min($ceilingSeconds, $secondsLeft)`
- `php/tests/Unit/ExAppServiceTest.php` - Hilfsmethode `timeoutThatReachedTheContainer` und drei Testfaelle mit `Ceiling` im Namen

## Decisions Made

- **`PAGE_REQUEST_TIMEOUT_SECONDS` = 1.5.** Die Planregel lautet "p95 plus 50 Prozent, auf halbe Sekunden aufgerundet, mindestens 1.5". Auf 0,022 s angewandt ergibt sie 0,5 s, also entscheidet die Untergrenze. Die neue Konstante traegt damit heute dieselbe Zahl wie der Dialog. Der Gewinn liegt im Mechanismus, nicht in der Zahl: eine spaetere Messung auf einer echten Instanz kann sie anheben, ohne den Dialogweg zu beruehren.
- **`PAGE_BUDGET_SECONDS` = 3.0 statt der 1.5 aus der Planformel.** Begruendung im Bericht, Abschnitt 6.2: 1,5 s waere kleiner als das Budget des Dialogs (2,5 s), und eine Seite, die alle Treffer verspricht und auf niemanden wartet, darf nicht ungeduldiger sein als der Dialog, aus dem sie aufgerufen wird. Die uebernommene Zahl folgt aus gemessenen Werten dieses Berichts (schlechtester beobachteter Container-Aufruf 1,944 s plus gemessener PHP-Anteil 0,59 s ergibt 2,53 s, aufgerundet auf die naechste halbe Sekunde).
- **Der Deckel wird ein Argument von `call()`**, nicht ein zweiter Aufrufpfad nach dem Vorbild von `adminGet()`. Das war die Orchestrator-Entscheidung; die Begruendung (verdoppelte Fehlerpfade laufen auseinander) steht woertlich im Docblock der neuen Konstante, so wie der Plan es verlangt.
- **Der Ausreisser bleibt drin.** Ein Snippet-Aufruf von 1,944 s steht unveraendert in den Rohdaten. Er begruendet keine hoehere Konstante, weil er ein Ereignis in 100 Aufrufen ist; die Gegenprobe mit 80 weiteren Aufrufen liegt komplett unter 0,09 s.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Der Korpus reichte nicht fuer eine volle Kandidatenseite**

- **Found during:** Task 1
- **Issue:** `testdata/corpus` liefert fuer jeden Begriff nur eine Handvoll Kandidaten; die Bedingung "mehr als 100 Kandidaten" war nicht erfuellbar.
- **Fix:** `scripts/dev/build_load_corpus.py --seed phase9-budget --files 300` in ein gitignoriertes Verzeichnis gebaut, in den Ordner von `testuser` kopiert, `occ files:scan --all`, `occ findling:index --restart` und Scheduler- plus Crawl-Job bis zur leeren Warteschlange gefahren. Seed, Dateizahl, Bytes und Pruefsumme stehen in Abschnitt 1 des Berichts.
- **Files modified:** keine Repo-Dateien (Zustand des Containers und des Backend-Index)
- **Verification:** `POST /search` mit `limit=100` liefert 100 Kandidaten und `hasMore: true`
- **Committed in:** nicht committet (Zustandsarbeit)

**2. [Rule 3 - Blockierend] `php -l` konnte nicht ueber den im Plan genannten Pfad laufen**

- **Found during:** Task 3
- **Issue:** Die automatisierte Pruefung des Plans lintet `/var/www/html/custom_apps/findling/lib/Service/ExAppService.php` im Container. Dieser Bind-Mount zeigt auf die geteilte Arbeitskopie, nicht auf diesen Worktree, haette also die unveraenderte Datei geprueft und faelschlich gruen gemeldet.
- **Fix:** Die geaenderte Datei aus dem Worktree per `docker cp` nach `/tmp` im Container gelegt und dort gelintet, zusaetzlich `php -l` ueber stdin. Beides meldet `No syntax errors`.
- **Files modified:** keine
- **Verification:** `No syntax errors detected in /tmp/ExAppService-09-01.php`
- **Committed in:** nicht committet (Pruefweg, keine Aenderung)

**3. [Rule 2 - Testqualitaet] Ein Testfall, der nicht haette scheitern koennen**

- **Found during:** Task 3
- **Issue:** Weil die Messung fuer `PAGE_REQUEST_TIMEOUT_SECONDS` denselben Wert ergibt wie `REQUEST_TIMEOUT_SECONDS`, waere der geforderte Testfall "ein uebergebener Deckel reist durch" nicht von "der Standardwert reist durch" zu unterscheiden gewesen.
- **Fix:** Der Testfall bekam eine zweite Zusicherung mit einem erhoehten Deckel (das Doppelte des Dialogwerts), die belegt, dass wirklich das Argument und nicht der Standard ankommt. Der Kommentar sagt, warum die Zusatzzusicherung existiert.
- **Files modified:** `php/tests/Unit/ExAppServiceTest.php`
- **Verification:** `grep -c 'function test.*Ceiling'` ergibt 3, `php -l` gruen
- **Committed in:** `014de1c`

---

**Total deviations:** 3 auto-fixed (2 nach Rule 3, 1 nach Rule 2)
**Impact on plan:** Kein Umfangszuwachs. Zwei Abweichungen betreffen den Messweg, eine die Aussagekraft eines geforderten Tests.

## Issues Encountered

- **Die Instanz stand im Wartungszustand und trug 0.3.0.** Genau der Fall, den Task 1 vorhergesehen hat. `occ upgrade` hat beides in einem Zug erledigt, die App-Fassung sprang dabei ohne zusaetzliches `app:update` auf 1.0.3.
- **Der teure Fall war nicht teuer, und das ist ein Befund.** Reihe C ist auf dieser Instanz kein hybrider Lauf: es gibt keine `vectors.db`, weil der Alltagsstack das Backend als Host-Prozess faehrt und das Modellverzeichnis nur im Auslieferungsabbild liegt. Statt zu schaetzen zitiert der Bericht die einzige vorhandene Messung des hybriden Falls (`docs/measurements/2026-09-05-semantiklauf-m7g/`, p95 524 ms im Leerlauf, 1.129 ms unter Nebenlast, max 2.065 ms). Abschnitt 5.1 des Berichts.
- **Die Zeit liegt in PHP, nicht im Container.** Der Container beantwortet beide Aufrufe zusammen in rund 0,07 s, eine ganze Suche kostet 0,65 s. Fuer Plan 09-04 heisst das, dass das Budget der Seite vor allem an der Zahl der zu pruefenden Kandidaten haengt. Abschnitt 5.2.
- **PHPUnit konnte lokal nicht laufen.** Auf dieser Maschine gibt es kein PHP und keinen `nextcloud/server`-Checkout; `php/tests/bootstrap.php` verlangt dessen `tests/bootstrap.php`, das im Release-Abbild des Containers nicht enthalten ist. Die Suite ist laut `docs/testing.md` und `.github/workflows/php.yml` bewusst CI-only. Ersatzweise geprueft: `php -l` beider Dateien im Container, die Reflexion privater Konstanten und die Gleitkomma-Gleichheit der drei Testfaelle mit `php -r` im Container. Der PHPUnit-Lauf und die Zunahme der Testzahl um drei sind an CI delegiert.
- **Nicht messbar auf diesem Korpus:** tiefe Seiten am Offset-Deckel des Containers und Nebenlast. Beides steht als Grenze in Abschnitt 5.4 des Berichts.

## User Setup Required

None - keine externe Dienstkonfiguration noetig.

## Next Phase Readiness

- Plan 09-04 kann `PAGE_BUDGET_SECONDS` = 3,0 Sekunden als Konstante der Seitenroute uebernehmen und `ExAppService::PAGE_REQUEST_TIMEOUT_SECONDS` an `searchCandidates()` und `snippets()` durchreichen.
- Der geteilte Recheck-Dienst (Plan 09-02 und folgende) erbt den zusaetzlichen letzten Parameter ohne Anpassung an `Provider.php`, weil der Standardwert der alte ist.
- Offen und ausdruecklich benannt: der hybride Fall und die tiefen Seiten sind ungemessen. Falls Phase 9 eine Sichtprobe auf dem HaRP-Stack fahren sollte, waere das die Gelegenheit, beide nachzuholen.
- Der Zustand der Test-Nextcloud ist danach ein anderer als vorher: 300 synthetische Dateien liegen unter `lastkorpus` im Ordner von `testuser`, und `core unified_search_max_results_per_request` steht auf 100. Beides ist gewollt und fuer die weiteren Plaene der Phase nuetzlich; wer eine kleine Instanz braucht, entfernt den Ordner und faehrt `occ findling:index --restart`.

## Self-Check: PASSED

- Alle genannten Dateien liegen auf der Platte (`test -f` fuer Bericht, Rohdaten, beide PHP-Dateien und diese Zusammenfassung).
- Beide Task-Commits sind im Log: `256b215` und `014de1c`.
- Kein Gedankenstrich der langen oder mittleren Form in Bericht, Quellcode und dieser Zusammenfassung.
- `git diff --stat` zeigt keine Aenderung an `php/composer.json`, `backend/pyproject.toml` oder einer `package.json`; keine der beiden Commits loescht eine Datei.

---
*Phase: 09-eigene-ergebnisseite*
*Completed: 2026-09-09*
