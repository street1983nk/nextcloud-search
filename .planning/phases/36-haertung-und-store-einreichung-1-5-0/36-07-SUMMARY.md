---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 07
subsystem: Testkorpus (Extraktion, Sandbox)
tags: [hart-06, d-36-01, d-36-02, d-36-17, hostile-corpus, sandbox, xfail]
requires: [36-06]
provides:
  - "backend/tests/hostile.py: eine Kopie aller Korpus-Generatoren (ZIP, CFB, Mail, Sandbox-Helfer) plus die neuen Familien aus D-36-02"
  - "ATTACK_RATIO = 1000 (O12) als Korpus-Konstante; 36-08 belegt die Gleichheit mit config.ARCHIVE_MALICIOUS_RATIO"
  - "backend/tests/test_phase36_hostile_corpus.py: sieben Falltabellen durch das echte Sandbox-Kind, je mit Positivkontrolle, Detailcode-Pflicht für die Sammelklasse, Log-Sonde"
  - "30 xfail(strict=True)-Fälle mit Zielurteil: 21 'built in 36-08', 9 'built in 36-09'"
affects: [36-08, 36-09]
tech-stack:
  added: []
  patterns:
    - "Generatoren-Modul ohne test_-Präfix (wie conftest), Import per from hostile import"
    - "Fehlende Erkennung als xfail(strict=True) mit wörtlichem reason='built in 36-0X' je Fall, damit der bauende Plan die Markierung per grep nachweisbar entfernt"
    - "Bombe deklariert ihre Größe statt sie zu tragen; Pseudozufall nur per LCG mit festem Seed"
key-files:
  created:
    - backend/tests/hostile.py
    - backend/tests/test_phase36_hostile_corpus.py
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/deferred-items.md
  modified:
    - backend/tests/test_phase31_audit.py
decisions:
  - "Neben den ZIP-Primitiven sind auch der CFB-Schreiber (als build_cfb_sectors), build_doc, build_workbook, die Zyklus-Editoren, nested_rfc822 und die Sandbox-Helfer nach hostile.py gewandert, weil das neue Modul sie braucht und pytest-Module sich nicht importieren"
  - "Die drei Pakete mit 1 Mio. Einträgen laufen vor 36-08 nicht (xfail strict, run=False): heute baut ZipFile eine ZipInfo je Record, etwa 560 MiB und 30 s je Fall. Dieselbe Lücke zeigen die 10 001-Record-Fälle, die laufen und in Millisekunden scheitern"
  - "XML-Tiefe 10 000 (Annahme A3) gemessen: ODT/DOCX/PPTX failed/xml_invalid (libxml2-Tiefengrenze 256), XLSX skipped/empty_text (expat ohne Tiefengrenze)"
  - "TIFF mit 100 000 IFDs bekommt eine eigene Laufzeitgrenze von 5 s und ist xfail 36-09 (Befund F-36-07-1)"
metrics:
  duration: "ca. 60 min (02:05 bis 03:05 Ortszeit), davon 12,5 min volle lokale Suite und das Warten auf CI"
  completed: 2026-10-21
  tasks: 2
  files: 4
requirements: [HART-06]
---

# Phase 36 Plan 07: Generierter bösartiger Formatkorpus Summary

Alle bösartigen Testdateien entstehen jetzt zur Laufzeit aus deterministischen, gedeckelten Generatoren in `backend/tests/hostile.py`. Im Baum liegt keine Binärdatei (D-36-01). `test_phase36_hostile_corpus.py` schickt 64 Fälle aus sieben Familien durch das echte Sandbox-Kind. 34 laufen heute grün, darunter die Positivkontrollen, die Polyglotte, die XML-Tiefe und die Log-Sonde. 30 Fälle stehen mit ihrem Zielurteil als `xfail(strict=True)` in den Tabellen und zeigen, was 36-08 und 36-09 noch bauen müssen.

## Commits

| Task | Name | Commit |
|------|------|--------|
| 1 | hostile.py: Generatoren verschoben, neue Familien | 2b57201a |
| 2 | test_phase36_hostile_corpus.py, Log-Sonde, deferred-items | 1d97d932 |

## Ergebnis je Fall (lokal, Windows)

**archive** (13): grün sind `plain`, `ratio-about-150` (Kontrolle O12, gemessen > 100 und < 200), `ratio-just-under-1000` (gemessen > 900 und <= 1000), `member-over-max-file-bytes` (indexiert, Name "riesig.txt" im Text), `depth-three-without-zeros` und `10001-entries` (beide archive_limit). Als xfail 36-08 stehen `ratio-over-the-attack-ratio` (heute archive_limit), `overlap-outside` und `overlap-inside` (heute archive_limit) sowie die vier `traversal-*` (heute indexiert). Jeder Fall prüft `left == ["korpus.bin"]`.

**package** (11): grün sind docx, pptx, xlsx und odt als echte kleine Pakete sowie `docx-of-10000-records` (corrupt, die Grenze selbst). Als xfail 36-08 stehen `*-of-10001-records` für docx, odt und xlsx (heute corrupt durch BadZipFile). Die drei `*-of-a-million-records` stehen als xfail mit `run=False`.

**xml** (14): grün sind plain-odt, plain-xlsx und `deep-nesting-*`. Für odt, docx und pptx ist das Urteil xml_invalid, für xlsx empty_text. Als xfail 36-08 stehen Billion Laughs und Quadratic Blowup, je in odt, docx, pptx und xlsx: heute xml_invalid über lxml bzw. corrupt über expat. Die Meldungen tragen nachweislich "amplification".

**image** (6): grün sind `honest-large-jpeg` und `png-of-60-megapixels` (beide too_large), `png-text-bomb` (corrupt durch den ValueError von Pillow MAX_TEXT_CHUNK) und `tiff-ifd-cycle` (READABLE). Als xfail 36-09 stehen `png-bomb` (heute too_large) und `tiff-of-100000-ifds` (heute 27,8 bis 28,9 s gegen eine Grenze von 5 s).

**mail** (3): grün ist `rfc822-nested-32-times` (indexiert). Als xfail 36-09 stehen 33 Ebenen (heute indexiert) und 1000 Ebenen (heute corrupt mit RecursionError).

**cfb** (7): grün sind die doc-Kontrolle und `doc-fat-declared-far-past-the-file` (corrupt). Als xfail 36-09 stehen die FAT-, MiniFAT-, DIFAT- und Verzeichnis-Zyklen in .doc und der MiniFAT-Zyklus in .xls (heute corrupt).

**polyglot** (5, ohne Markierung): pdf, PDF+ZIP als pdf und als zip sowie JPEG+ZIP als zip werden indexiert. JPEG+ZIP als jpeg endet als READABLE.

**Tabellenprüfungen** (4, grün):
- Ein Detailcode steht genau dann, wenn blocked_malicious erwartet wird, und nur aus der geschlossenen Liste der acht Codes.
- Jede Familie hat eine Positivkontrolle, die heute läuft.
- Die Verhältnisfälle liegen dort, wo O12 sie hinstellt. Das wird aus den Bytes gelesen, nicht aus dem Generator übernommen.
- Die Generatoren sind deterministisch.

**Log-Sonde** (grün): Ein frischer Worker liest 14 Dateien mit acht Geheimwörtern. In capfd und caplog steht keines davon. Die Positivkontrolle `DecompressionBombWarning` aus einem PNG mit 60 MP erscheint.

**Gegenprobe:** Mit `--runxfail` (ohne die drei run=False-Fälle) scheitern alle 27 markierten Fälle am erwarteten Punkt. 26 davon scheitern am Urteil, einer an der Laufzeit. Kein Fall scheitert an einem Generatorfehler.

## Gates

- Lokal: ruff (alle Dateien), ruff format (232 Dateien), pyright (0 errors), vulture und reuse lint (2901/2901) sind grün. Volle Suite: 6000 passed, 264 skipped, 30 xfailed in 12:32.
- hostile.py ist reines ASCII. Kein Generator nutzt time, random oder os.urandom. Die Uhr liest nur `run_timed`, als Stoppuhr der Sandbox-Helfer.
- `git diff --stat 37fb122e HEAD`: nur .py-Dateien und deferred-items.md, keine Binärdatei.
- CI für 1d97d932:
  - Python gates 39524695753 sind grün: ubuntu mit RLIMIT_AS, 6011 passed, 253 skipped, 30 xfailed. Das ist der Speicherbeleg.
  - Multi-arch image 39524695732, OpenSSF Scorecard 39524695736, Resilience 39524695837 und Integration 39524695744 sind grün.
  - HaRP deploy 39524695703 ist grün.
  - **Security scans 39524695697 ist rot:** Im Job pip-audit gibt es neue Advisories zu pillow 12.3.0 (8 CVEs, Fix 13.0.0) und certifi 2026.7.22. Ursache ist nicht dieser Plan: 37fb122e war um 19:39Z noch grün. Siehe F-36-07-2.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Mehr als die ZIP-Primitive nach hostile.py verschoben**
- **Found during:** Task 1
- **Issue:** Die CFB-Zyklusfälle, die Mailtiefe und die Sandbox-Helfer braucht das neue Modul auch. pytest-Module können sich nicht gegenseitig importieren.
- **Fix:** Nach hostile.py verschoben wurden der CFB-Schreiber (umbenannt in `build_cfb_sectors`, keine Kollision mit `conftest.build_cfb`), `Layout`, `build_doc`, `build_workbook`, die Zyklus-Editoren, `_HEAD` und `nested_rfc822`, dazu `Ran`, `run_timed`, `named_and_quick`, `corpus_case` und die Konstanten. `_text` heißt jetzt `text_member`. test_phase31_audit.py importiert alles und bleibt verhaltensgleich (97 passed).
- **Commit:** 2b57201a

**2. [Rule 1 - Bug] PDF-Generator ergab no_text_layer**
- **Found during:** Sonde vor Task 2
- **Issue:** "pdfwort" hat unter 25 Zeichen (`_MIN_CHARS_PER_PAGE`), die Seite galt deshalb als Scan.
- **Fix:** Der Standardtext ist jetzt länger. Damit prüft der Polyglott-Fall als pdf wirklich den PDF-Leser.
- **Commit:** 2b57201a

**3. [Rule 2 - Missing critical] Laufzeitgrenze für den TIFF-Rahmenlauf**
- **Found during:** Task 2
- **Issue:** `tiff_many_ifds(100_000)` hat einen Namen, braucht aber 27,8 s bei einer Fallgrenze von 30 s. Das ist keine "kurze Laufzeit" und würde in CI mal grün, mal rot.
- **Fix:** Der Fall bekommt `seconds=5.0` und xfail 36-09. Der Befund steht in deferred-items.md als F-36-07-1.
- **Commit:** 1d97d932

### Kleinere Abweichungen

- Die Falltabellen nutzen ein NamedTuple `Case(build, mime, verdict, detail, why, contains, seconds)` statt eines nackten 4-Tupels. Mimetype, Prüfwort und Laufzeitgrenze brauchen je Fall eine Stelle.
- Zusätzlich gibt es Fälle über den Plan hinaus:
  - `ratio-just-under-1000` (O12 "Fall knapp darunter")
  - `docx-of-10000-records` (Grenze)
  - `*-of-10001-records` (laufende Variante der 1-Mio.-Fälle)
  - JPEG+ZIP als zip
  - vier Tabellenprüfungen
- `zip_ratio_member` baut mit Deflate (2 MiB Nullen, gemessen über 1000:1). bzip2 und LZMA sind nicht nötig, weil 1000 unter dem Deflate-Höchstwert liegt.

### Betriebshinweis

Zwei Sondenaufrufe hingen: einmal fehlte der `__main__`-Schutz beim Spawn, einmal überschrieb `python -` mit `</dev/null` das Heredoc. Beendet wurden jeweils nur die eigenen PIDs (23472/27196 und 8304/16476), nie pauschal alle python.exe.

## Deferred Issues

- **F-36-07-1:** Der TIFF-Rahmenlauf wächst überlinear. 36-09 muss `n_frames` an der Seitengrenze kappen und dann die Markierung `tiff-of-100000-ifds` heben. Das steht noch nicht im Plan 36-09.
- **F-36-07-2 (Blocker für die Einreichung):** pip-audit ist rot, pillow 12.3.0 hat 8 CVEs (Fix 13.0.0), certifi 2026.7.22 eine. Ein Paket-Update ist kein Auto-Fix. Owner-Entscheid nötig: in 36-09 (Bildpfad) oder in einem eigenen Plan, vor 1.5.0.

## Threat Flags

Keine neue Oberfläche, nur Testcode.
- T-36-24 ist durch Generatoren statt Dateien abgedeckt.
- T-36-25 ist abgedeckt: Lauf nur im Sandbox-Kind mit Frist, die 1-Mio.-Pakete laufen vor 36-08 nicht, Tests laufen seriell.
- T-36-26 ist durch die Log-Sonde mit Positivkontrolle abgedeckt.

## Known Stubs

Keine. Die xfail-Fälle sind geplante Zielurteile für 36-08 und 36-09.

## Self-Check: PASSED

- Dateien vorhanden: backend/tests/hostile.py, backend/tests/test_phase36_hostile_corpus.py, deferred-items.md, 36-07-SUMMARY.md
- Commits 2b57201a und 1d97d932 vorhanden und gepusht
