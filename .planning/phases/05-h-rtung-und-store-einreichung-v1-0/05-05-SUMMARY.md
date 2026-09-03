---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 05
subsystem: infra
tags: [load-testing, cgroup-v2, hetzner-api, reproducible-builds, ocr, pillow, posix-sh]

# Dependency graph
requires:
  - phase: 03-aktualit-t-und-ocr
    provides: OCR-Pfad, Größendeckel MAX_FILE_BYTES, die per SHA-256 festgenagelte Schrift unter testdata/fonts
  - phase: 01-walking-skeleton
    provides: scripts/dev/build_corpus.py als deterministisches Korpus-Prinzip
provides:
  - Deterministischer, streamender Generator für 50.000 synthetische Dateien und rund 20 GB (scripts/dev/build_load_corpus.py)
  - Ehrlicher cgroup-v2-Speichersampler mit OOM-Beweis (scripts/ops/rss_sampler.sh)
  - Werkzeug zum Mieten, Kosten-Belegen und nachweislichen Abbauen der ARM-Box (scripts/ops/hetzner_box.sh)
  - Zwei Dauergates: die Determinismus-Zusage des Generators und die Hausregeln der Ops-Skripte
affects: [05-10-arm-lasttest, 05-messbericht-docs-performance, store-aussage-peak-rss]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Streamendes Schreiben je Datei: temporärer Name, SHA-256 mitlaufend, dann umbenennen"
    - "SHA-256 im Zählerbetrieb als Zufallsquelle, damit ein Seed auch nach einem Interpreter-Wechsel dasselbe Korpus bedeutet"
    - "Bytegewicht eines Dokuments kommt aus einer unkomprimierten Scan-Anlage, nicht aus Prosa"
    - "Messen heißt abbrechen statt Nullen schreiben"
    - "Geheimnis per curl-Konfiguration auf stdin statt als Argument, damit es nicht in der Prozessliste steht"

key-files:
  created:
    - scripts/dev/build_load_corpus.py
    - scripts/ops/rss_sampler.sh
    - scripts/ops/hetzner_box.sh
    - backend/tests/test_load_corpus.py
    - backend/tests/test_ops_scripts.py
  modified: []

key-decisions:
  - "Eigene Zufallsquelle (SHA-256 im Zählerbetrieb) statt random.Random, weil die Sprache die Stabilität des Mersenne-Twisters nicht zusagt"
  - "Das Bytegewicht der Büro- und Text-Dateien kommt aus einer unkomprimierten Scan-Anlage im Paket, nicht aus mehr Prosa: reine Prosa hätte 34 GB Text in einen Index gelegt, der auf 3 bis 6 GB veranschlagt ist"
  - "Text-PDF trägt zehn Textseiten und eine Bildseite, also ein Elftel Scan-Anteil, weit unter der Schwelle, ab der findling.extract.pdf ein Dokument für einen Scan hält"
  - "Seitenzahl der mehrseitigen Scans in drei Bändern statt gleichverteilt, damit der Mittelwert bei acht Seiten liegt und die Laufzeitrechnung der Recherche gilt"
  - "destroy löst das Volume zuerst, weil ein angehängtes Volume bei Hetzner nicht gelöscht werden kann; die Reihenfolge der Recherche wäre am ersten Aufruf gescheitert"
  - "Der Zustand der Miet-Box liegt unter $HOME/.findling-loadtest, nie im Arbeitsbaum"

patterns-established:
  - "Textgate für Skripte: Typografie, Zeilenenden und verbotene Abkürzungen als pytest statt als Reviewnotiz"
  - "Trockenlauf gegen einen lokalen Ersatz der Fremd-API, bevor der erste echte Aufruf Geld kostet"

requirements-completed: [PKG-03]

# Metrics
duration: 70min
completed: 2026-09-03
---

# Phase 5 Plan 05: Die drei Werkzeuge des ARM-Lasttests Summary

**Ein Seed erzeugt reproduzierbar 50.000 synthetische Dateien und 20,12 GB streamend, ein Sampler meldet `anon` aus `memory.stat` samt OOM-Beweis und bricht ab statt Nullen zu schreiben, und ein Skript mietet die CAX11 mit Volume, belegt ihre Kosten aus der Konto-API und baut sie nachweislich wieder ab.**

## Performance

- **Duration:** 70 min
- **Started:** 2026-09-03T08:50:00Z
- **Completed:** 2026-09-03T10:00:00Z
- **Tasks:** 3 (Task 1 nach TDD in zwei Schritten)
- **Files modified:** 5 neu, 0 geändert

## Accomplishments

- **Der Lastkorpus ist belegbar synthetisch und reproduzierbar.** `scripts/dev/build_load_corpus.py` schreibt aus einem Seed 50.000 Dateien in der Verteilung der Recherche, streamend, mit einer Prüfsumme über die sortierte Dateiliste als Beleg. Zwei Läufe mit demselben Seed liefern bitweise dieselben Dateien, ein anderer Seed eine andere Prüfsumme, und beides steht als Testfall in der Suite.
- **Der 500er-Trockenlauf ist gefahren und ausgezählt.** 500 Dateien in 17 Sekunden, 245.695.552 Bytes, Anteile 19,8 / 0,2 / 45 / 20 / 10 / 4,6 / 0,2 Prozent plus eine Datei über dem Deckel. Listen-Prüfsumme für Seed `phase5-dry`:

  ```
  cac56ed1801efb3e691b28088c363c84d8941670394f5fed95ab19359b17d530
  ```

  Die Hochrechnung auf 50.000 Dateien ergibt **20,12 GB** und trifft die Tabelle der Recherche fast Zeile für Zeile.
- **Die Messung ist ehrlich und gegen einen laufenden Container belegt.** Der Sampler fand den Cgroup-Pfad selbst (cgroupfs-Form), schrieb elf Zeilen mit sechs Spalten, `anon` = 71.057.408 Bytes, und die Abschlusszeile nennt alle vier OOM-Angaben:

  ```
  findling-rss summary samples=11 max_anon=71057408 peak=71696384 events=[low=0 high=0 max=0 oom=0 oom_kill=0 oom_group_kill=0] oom_killed=false
  ```

  Exitcode 0.
- **Der ganze Lebenslauf der Miet-Box ist trocken durchgespielt.** Gegen einen lokalen Ersatz der Hetzner-API laufen `prices`, `create`, `status` und `destroy` durch: Label auf Box und Volume, Zustandsdatei außerhalb des Repos ohne Token, Kostenausgabe aus `/pricing`, und `destroy` endet mit Exitcode 1, wenn eine Ressource stehen bleibt.
- **Zwei neue Dauergates.** 13 Testfälle halten die Zusagen des Generators, 13 weitere die Hausregeln der beiden Skripte (Typografie, Zeilenenden, `set -eu`, beide Cgroup-Formen, kein Umweg über den Docker-Client, Token nur an zwei Stellen, Label zweimal, geprüfte Löschung).

## Task Commits

1. **Task 1 (RED): Testfälle des Generators**, `aebf262` (test)
2. **Task 1 (GREEN): Generator**, `ed120c1` (feat)
3. **Task 2: RSS-Sampler**, `be18c17` (feat)
4. **Task 3: Hetzner-Box-Skript**, `2f173db` (feat)
5. **Nachtrag: ß im Vokabular**, `9320cf5` (fix)

**Plan-Metadaten:** dieser SUMMARY (docs)

## Files Created/Modified

- `scripts/dev/build_load_corpus.py`: Generator mit `--seed`, `--files`, `--out`, `--dry-run-files`, `--report`; Verteilung als benannte Datenstruktur mit Begründung je Zeile; Schriftprüfung und Glyphen-Assert vor dem ersten Byte; Report je Datei plus Summenzeile.
- `scripts/ops/rss_sampler.sh`: CSV mit `timestamp,anon,file,slab,current,peak`, festes Präfix zum Filtern aus einem Log, Abschlusszeile mit dem OOM-Beweis, Abbruch statt Nullen.
- `scripts/ops/hetzner_box.sh`: `prices`, `create`, `status`, `destroy`; Token nur aus der Umgebung und nur über eine curl-Konfiguration auf stdin; Zustandsdatei mit `umask 077` unter `$HOME/.findling-loadtest`.
- `backend/tests/test_load_corpus.py`: 13 Fälle gegen 50 und 500 Dateien, nie gegen den Volllauf; darunter der Speicher-Nachweis per tracemalloc und die Lesbarkeit jeder erzeugten Dateiart mit der Bibliothek, mit der das Backend sie extrahiert.
- `backend/tests/test_ops_scripts.py`: Textgate für beide Ops-Skripte.

## Decisions Made

- **Eigene Zufallsquelle.** `random.Random` wäre naheliegend, aber die Sprache sagt die Stabilität des Mersenne-Twisters nicht zu, und dieses Korpus muss Jahre nach der Messung nachbaubar sein. SHA-256 im Zählerbetrieb ist außerhalb des Projekts spezifiziert und kann mit keinem Interpreter-Release wandern. Nebeneffekt: der Griff nach der unbestimmten Quelle steht damit gar nicht im Erzeugungspfad, was ein Gate mechanisch prüfen kann.
- **Bytegewicht aus einer Scan-Anlage statt aus Prosa.** Die erste Fassung erreichte die 350 KB je Büro-Datei mit reiner Prosa. Gemessen deflatiert deutscher Text um den Faktor 6,7, also braucht eine Datei dafür 2,3 MB Text; 15.000 solche Dateien hätten 34 GB Text in einen Index gelegt, für den die Phase 3 bis 6 GB veranschlagt, und der Generator wäre auf 6 Stunden gelaufen. Eine unkomprimierte Graustufen-TIFF im Paket ist das, was ein Scanner wirklich schreibt, ihre Größe ist genau ihre Pixelzahl, und damit trifft eine Kategorie ihr Byteziel ohne ein einziges Füllbyte. Textmenge und Laufzeit sind danach realistisch: rund 45 Minuten Generatorlauf auf dem Entwicklungsrechner statt 6 Stunden, rund 1,7 GB Text im ganzen Korpus.
- **Ein Elftel Scan-Anteil im Text-PDF.** Die Anlage ist eine Bildseite unter zehn Textseiten. `findling.extract.pdf` erklärt ein Dokument erst ab einem viel höheren Anteil zum Scan; gegengeprüft am erzeugten Korpus: eine Text-PDF liefert 31.508 Zeichen ohne Scan-Verdikt, eine Scan-PDF `no_text_layer`. Die Kategorie bleibt also auf dem Textweg und wird nicht heimlich zur elften OCR-Stunde.
- **Seitenzahl der mehrseitigen Scans in drei Bändern.** Gleichverteilt zwischen 2 und 30 wäre der Mittelwert 16, und die Laufzeitrechnung der Recherche steht auf 8. 60 Prozent 2 bis 6 Seiten, 30 Prozent 7 bis 14, 10 Prozent 15 bis 30 ergeben rund 8. Jede Seite multipliziert direkt in die OCR-Stunden, also ist die Form dieser Ziehung mehr wert als ihre Spanne.
- **Flaches Zielverzeichnis.** Wie beim Referenzkorpus, aus demselben Grund: die Namen sind eindeutig durchnummeriert, und ein Unterbaum kauft für diese Messung nichts.
- **Peak-RSS-Budget nicht hier.** D-03 und Pitfall 10 verlangen einen Grenzwert; er gehört in den Messplan der Box (05-10), nicht in das Werkzeug. Der Sampler nennt Zahlen und fällt kein Urteil.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] destroy löst das Volume zuerst, sonst schlägt das Löschen fehl**
- **Found during:** Task 3
- **Issue:** Plan und Recherche geben die Reihenfolge `DELETE /volumes/<id>`, dann `DELETE /servers/<id>` vor. Ein Volume, das an einem Server hängt, kann bei Hetzner nicht gelöscht werden; der erste echte Aufruf wäre mit einem API-Fehler stehen geblieben, und zwar in genau dem Schritt, der das Aufräumen sicherstellen soll.
- **Fix:** `destroy` schickt zuerst `POST /volumes/<id>/actions/detach`, wartet das Ablösen mit Zähler und sprechendem Abbruch aus (Muster aus `register-exapp.sh`), löscht dann Volume und Server und versucht das Volume danach noch ein zweites Mal, falls erst der Server weg musste. Die anschließende Prüfung ist unverändert: beide Ressourcen müssen `not_found` liefern, sonst Exitcode 1.
- **Files modified:** scripts/ops/hetzner_box.sh
- **Verification:** Trockenlauf gegen den lokalen API-Ersatz; die Ablöse-Anfrage steht im Anfrageprotokoll, und der Ausfallpfad endet mit Exitcode 1.
- **Committed in:** 2f173db

**2. [Rule 2 - Missing Critical] Lesbarkeitsprüfung jeder erzeugten Dateiart**
- **Found during:** Task 1
- **Issue:** Der Plan verlangt Determinismus und Verteilung, aber nichts prüft, dass die erzeugten Dateien überhaupt lesbar sind. Ein Korpus mit einem kaputten OOXML-Teil hätte zwanzig Stunden lang den Fehlerpfad gemessen, und das Ergebnis hätte wie ein Mangel der App ausgesehen.
- **Fix:** Ein Testfall öffnet jede erzeugte Art mit derselben Bibliothek, mit der das Backend sie extrahiert (python-docx, openpyxl im read-only-Modus, python-pptx, pypdfium2, der ODF-Extraktor des Projekts). Dabei fielen zwei echte Mängel auf: die Tabelle brauchte ein `dimension`-Element, weil openpyxl im read-only-Modus eine Tabelle ohne Ausdehnung nicht iteriert, und ohne benannten Standardstil warnt openpyxl bei jeder Datei, was im Log des Volllaufs zehntausend Zeilen Rauschen gewesen wäre.
- **Files modified:** scripts/dev/build_load_corpus.py, backend/tests/test_load_corpus.py
- **Verification:** `uv run python -m pytest tests/test_load_corpus.py -q` grün, Warnungsliste leer.
- **Committed in:** ed120c1

**3. [Rule 2 - Missing Critical] Textgate für die beiden Ops-Skripte**
- **Found during:** Task 2
- **Issue:** Die Abnahmekriterien der Tasks 2 und 3 sind grep-Prüfungen, die einmal von Hand laufen und danach niemand mehr wiederholt. Genau diese Regeln (keine Gedankenstriche, kein Wagenrücklauf vor `/bin/sh`, kein Umweg über den Docker-Client für eine Speicherzahl, Token an nur zwei Stellen, Label zweimal) sind die, die ein gut gemeinter Edit in einem Jahr bricht.
- **Fix:** `backend/tests/test_ops_scripts.py` hält sie als Dauergate, mit derselben Begründung, die Pitfall 9 der Recherche für die Store-Texte gibt.
- **Files modified:** backend/tests/test_ops_scripts.py
- **Verification:** 13 Fälle grün; die beiden verbotenen grep-Muster sind 0, weil das Gate sie sonst rot färbt.
- **Committed in:** be18c17, 2f173db

**4. [Rule 3 - Blocking] Token per curl-Konfiguration auf stdin**
- **Found during:** Task 3
- **Issue:** Der Plan verlangt, dass der Token in keiner Ausgabe und keiner Zustandsdatei erscheint. `-H "Authorization: Bearer $HCLOUD_TOKEN"` erfüllt das, legt den Wert aber in die Argumentliste, und die ist auf der Box für jeden lesbar, der `ps` aufrufen kann.
- **Fix:** Die Kopfzeilen gehen als curl-Konfiguration über stdin. Kein Argument, keine Datei, kein Rest.
- **Files modified:** scripts/ops/hetzner_box.sh
- **Verification:** Trockenlauf; das Anfrageprotokoll des API-Ersatzes zeigt den Bearer-Kopf bei jedem Aufruf, das Skript nennt den Wert nirgends.
- **Committed in:** 2f173db

**5. [Rule 1 - Bug] ß im deutschen Vokabular**
- **Found during:** Abschlussprüfung nach Task 3
- **Issue:** Sechs Wörter des Vokabulars standen in der ASCII-Schreibweise (Erschliessung, Massnahme, Strassenbau, massgeblich, gemäss, Vorgaenge). Das verstößt gegen die Projektregel für deutsche Prosa, und es ist hier mehr als Form: die Prosa wird in Scans gerendert, also war die OCR des ß der eine Fall, der vorher nicht schiefgehen konnte.
- **Fix:** Echte Zeichen. Der Glyphen-Assert deckt sie ab, weil er über alle Vokabular-Zeichen läuft, und cp1252 kennt ß und die Umlaute, also bleibt der PDF-Textweg unverändert.
- **Files modified:** scripts/dev/build_load_corpus.py
- **Verification:** Trockenlauf erneut gefahren, neue Prüfsumme oben protokolliert; 26 Testfälle grün.
- **Committed in:** 9320cf5

---

**Total deviations:** 5 auto-fixed (2 Bug, 2 fehlende kritische Funktion, 1 blockierend)
**Impact on plan:** Alle fünf gehören zum Auftrag der drei Werkzeuge. Kein zusätzlicher Umfang, kein neues Paket: der Generator nutzt die Standardbibliothek und das schon gepinnte Pillow, die Skripte nutzen curl, docker, awk und das python3 der Zielplattform (T-05-SC gehalten).

## Issues Encountered

- **Die Bytezahlen der Verteilungstabelle und ihre Laufzeitrechnung passen nicht zu reiner Prosa.** Aufgelöst wie unter "Decisions Made" beschrieben: Byteziel über die Scan-Anlage, Textmenge realistisch. Die Tabelle wird damit in beiden Spalten getroffen, die Hochrechnung liegt bei 20,12 GB.
- **Die Testsuite wird um rund 90 Sekunden länger** (110 s statt gut 20 s), weil die Reproduzierbarkeit laut Plan bei 500 Dateien belegt wird und drei solche Läufe die echte Verteilung samt 300-dpi-Scans erzeugen. Bewusst so gelassen: der Beleg ist der Zweck des Plans, und 90 Sekunden im schnellen Gate sind gegen einen 20-Stunden-Lauf auf Mietblech keine Diskussion.
- **Die Messung gegen einen laufenden Container geht auf dieser Maschine nur im Umweg.** Docker Desktop hält die Cgroups in der WSL2-VM, die Windows-Seite hat kein `/sys/fs/cgroup`. Der Sampler lief deshalb in einem `docker:cli`-Container mit `--cgroupns=host`, dem Docker-Socket und der Cgroup-Wurzel nur lesbar. Das Ergebnis ist eine echte Messung an einem echten Container; auf der Box läuft er direkt und trifft dort die systemd-Form des Pfades, die im Skript zuerst probiert wird.
- **Der Rechtemodus der Zustandsdatei ist auf dieser Maschine nicht prüfbar.** `umask 077` steht vor dem ersten Schreiben, aber NTFS zeigt danach `rw-r--r--`. Auf der Box gilt die Maske; der Test prüft daher das Vorhandensein der Maske und den Ort der Datei, nicht den Modus.

## User Setup Required

Keine. Für den echten Lauf in Plan 05-10 braucht der Betreiber genau eines: `HCLOUD_TOKEN` mit Schreibrechten aus dem bestehenden Hetzner-Konto in der Umgebung, ausschließlich dort. Das Skript fragt nicht danach und speichert es nicht.

## Next Phase Readiness

- Bereit für 05-10 (Bestellung und Volllauf): Generator, Sampler und Box-Werkzeug liegen vor und sind je einzeln belegt. Die Reihenfolge auf der Box ist damit vorgezeichnet: `hetzner_box.sh prices` für die Kostenzeile des Berichts, `create`, Grundlast von AIO **vor** der Findling-Installation messen, 500er-Trockenlauf mit `--dry-run-files`, dann der Volllauf mit dem zweiten Seed, `destroy` am Ende jedes Ausgangs.
- Offen und ausdrücklich nicht hier entschieden: der Grenzwert für den Spitzenwert von `anon` (D-03, Empfehlung der Recherche 2,0 GB) und die vier Sätze zur Messmethode in `docs/performance.md`, die wörtlich im Kopf von `rss_sampler.sh` stehen und dort abgeholt werden können.
- Zwei Seeds sind zu dokumentieren: `phase5-dry` für den Trockenlauf (Prüfsumme oben) und ein eigener für den Volllauf. Der Volllauf-Seed wird beim ersten `create` festgelegt und gehört in den Messbericht.

## Self-Check: PASSED

Alle fünf zugesagten Dateien liegen auf der Platte, alle sechs genannten Commits stehen im Log:

| Prüfung | Ergebnis |
|---------|----------|
| scripts/dev/build_load_corpus.py | gefunden |
| scripts/ops/rss_sampler.sh | gefunden |
| scripts/ops/hetzner_box.sh | gefunden |
| backend/tests/test_load_corpus.py | gefunden |
| backend/tests/test_ops_scripts.py | gefunden |
| aebf262, ed120c1, be18c17, 2f173db, 9320cf5 | im Log |
| `uv run python -m pytest -q` | 801 bestanden, 11 übersprungen |
| ruff check, ruff format, pyright, vulture | grün |
| `sh -n` beide Skripte, Aufruf ohne Argument | fehlerfrei, Exitcode 2 |
| `git status --porcelain` | leer |
| Gedankenstriche in allen fünf Dateien | keine |

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-03*
