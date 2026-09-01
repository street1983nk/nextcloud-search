---
phase: 03-aktualit-t-und-ocr
plan: 05
subsystem: ocr-image-und-konfiguration
tags: [ocr, tesseract, docker, config, messung, lizenz]
requires:
  - "backend/Dockerfile (wngerman-Block als Muster fuer apt plus fail-closed)"
  - "backend/src/findling/config.py (_int_from_environment, _languages als Muster)"
  - "backend/src/findling/extract/sandbox.py (RLIMIT_AS 512 MB, setsid/killpg)"
provides:
  - "tesseract 5.5.0 mit deu, eng und osd im Laufzeitimage, ohne Admin-Zutun"
  - "docs/ocr.md: Deckel-Kaskade und fuenf Messungen mit Datum und Kommandozeile"
  - "sechs OCR-Umgebungsvariablen in config.py und in der ExApp-info.xml"
  - "Settings.ocr_* als gemessene, benannte Zahlen fuer die Plaene 03-06 bis 03-10"
affects:
  - "backend/Dockerfile"
  - "backend/pyproject.toml"
  - "backend/uv.lock"
  - "backend/src/findling/config.py"
  - "backend/appinfo/info.xml"
  - "backend/tests/test_config.py"
  - "THIRD-PARTY.md"
  - "docs/ocr.md"
tech-stack:
  added:
    - "tesseract-ocr 5.5.0-1+b1 (Debian trixie, ungepinnt, Anker ist der Basis-Image-Digest)"
    - "tesseract-ocr-deu/-eng/-osd 1:4.1.0-2 (Architecture: all, hart gepinnt)"
    - "pillow 12.3.0 (nur direkt gepinnt, lag transitiv bereits im Lock)"
  patterns:
    - "apt-Block plus fail-closed-Pruefung plus Lizenzkopie, im Muster des wngerman-Blocks"
    - "abgeleitete statt zweiter Konstante: harte Deadline = weiche + 60 s"
    - "geschlossene Allowlist vor jedem Wert, der in eine Argumentliste wandert"
key-files:
  created:
    - "docs/ocr.md"
    - ".planning/phases/03-aktualit-t-und-ocr/03-05-SUMMARY.md"
  modified:
    - "backend/Dockerfile"
    - "backend/pyproject.toml"
    - "backend/uv.lock"
    - "backend/src/findling/config.py"
    - "backend/appinfo/info.xml"
    - "backend/tests/test_config.py"
    - "THIRD-PARTY.md"
decisions:
  - "A1 bestaetigt: 512 MB RLIMIT_AS reichen fuer eine A4-Seite bei 300 dpi um das Vierfache, deshalb bekommt der OCR-Zweig KEINEN eigenen Adressraumwert"
  - "A3 bestaetigt: die Debian-traineddata sind LSTM-only, --oem 1 wird trotzdem explizit gesetzt"
  - "A5 widerlegt: leptonica liest WebP direkt, der Pillow-Umweg behaelt seine anderen Gruende"
  - "OMP_THREAD_LIMIT=1 ist Teil der Speicherzusage, nicht Feintuning: ohne die Variable stirbt derselbe Lauf bei 128 MB"
  - "Die harte Deadline wird aus der weichen abgeleitet statt als 660 festgeschrieben"
  - "Die Engine bleibt ungepinnt, weil 5.5.0-1+b1 auf BEIDEN Architekturen steht"
metrics:
  duration: "ca. 40 Minuten"
  tasks: 3
  commits: 5
  files-changed: 8
  tests: "489 passed, 1 skipped"
  completed: 2026-09-01
---

# Phase 3 Plan 05: OCR ins Image und die Zahlen dahinter messen

OCR-Engine, deutsche und englische Sprachdaten und fail-closed-Lizenzpruefungen
im Laufzeitimage, dazu fuenf Messungen im gebauten Image, die vier
Recherche-Annahmen der Phase entweder belegen oder korrigieren, und sechs
OCR-Einstellungen, die genau diese gemessenen Zahlen als Default tragen.

## Was gebaut wurde

### Task 1: tesseract im Image, fail-closed geprueft

Ein vierter apt-Block in der Laufzeit-Stage, im Muster des wngerman-Blocks. Die
Engine ohne Versions-Pin, die drei Sprachpakete hart auf `1:4.1.0-2`. Im selben
`RUN` bricht der Bau ab, wenn `tesseract --list-langs` nicht deu und eng zeigt
oder eine der beiden Lizenzdateien fehlt; beide werden nach
`/usr/local/share/findling/COPYING.tesseract{,-langdata}` kopiert, weil slim
Images `/usr/share/doc` grossteils wegwerfen und eine Lizenzpflicht nicht an
einer dpkg-Konfigurationszeile haengen darf, die jemand anders pflegt.

Die Fraktur-Option aus D-09 liegt als auskommentierte, erklaerte Zeile daneben:
der Code heisst `frk`, `deu_frak` ist seit tesseract 4 tot und das Paket
`tesseract-ocr-deu-frak` existiert in trixie nicht.

`pillow` wird direkt auf 12.3.0 gepinnt. Es lag ueber python-pptx bereits im
Lock, der Diff in `uv.lock` sind exakt zwei Zeilen, und die Netto-Zahl neuer
PyPI-Pakete dieser Phase bleibt null.

THIRD-PARTY.md nennt jetzt beide Apache-2.0-Pflichten samt Fundort im Image und
die gemessene Groesse dessen, was tatsaechlich mitkommt.

### Task 2: der Messlauf

`docs/ocr.md`, 304 Zeilen, mit der Aufrufform, der Deckel-Kaskade als Tabelle,
der begruendeten Abweichung von STACK.md und fuenf Messungen, jede mit Datum,
Hardware und Kommandozeile.

Das Korpus-PDF `02-scan-no-text-layer.pdf` taugte als Vorlage nicht: 300 x 120
Punkt, 814 Byte. Gemessen wurde stattdessen an einer im Container erzeugten
echten A4-Seite mit 42 Zeilen deutscher Verwaltungsprosa, gerastert zu
2480 x 3509 Pixeln in Graustufen.

| Messung | Ergebnis |
|---|---|
| A1 Adressraum | tesseract laeuft bei `ulimit -v 131072` (128 MB) sauber durch. Die 512 MB des Sandbox-Kindes sind rund das Vierfache des Bedarfs. **A1 bestaetigt** |
| A3 Motorwahl | `--oem 0` und `--oem 2` scheitern mit "legacy engine requested, but components are not present". Die Debian-traineddata sind reines LSTM. **A3 bestaetigt** |
| A2 Zeit je Seite | Median 1984 ms mit `OMP_THREAD_LIMIT=1`, 2424 ms ohne. **A2 bestaetigt**, ein Thread ist auch auf zwoelf sichtbaren Kernen schneller |
| A5 WebP | leptonica 1.84.1 ist gegen libwebp 1.5.0 gebaut und liest WebP direkt von stdin, byteweise identischer Text wie aus PNG. **A5 widerlegt**, im guenstigen Sinn |
| Pitfall 10 | Bei zu wenig Adressraum stirbt der Enkel mit Exitcode 134 nach `std::bad_alloc`. Im Kind kommt **kein** MemoryError an. **bestaetigt** |

Die wichtigste Folge fuer den Code steht in der ersten Zeile: der OCR-Zweig
bekommt keinen eigenen, hoeheren `RLIMIT_AS`.
`EXTRACT_ADDRESS_SPACE_BYTES` bleibt unveraendert, und es entsteht keine zweite
Speicherkonstante, die gepflegt werden muesste.

Die zweite Folge steht in der dritten und in der ersten Zeile zusammen:
`OMP_THREAD_LIMIT=1` ist doppelt begruendet. Es ist 18 Prozent schneller, und
ohne die Variable stirbt derselbe Lauf bei 128 MB mit Exitcode 134. Die Variable
ist damit Teil der Speicherzusage, nicht Feintuning.

Nachgetragen wurde ausserdem die arm64-Paketaufloesung, weil dort das
eigentliche Pin-Risiko sitzt: die Engine traegt `5.5.0-1+b1` auf **beiden**
Architekturen, ein harter Pin auf das von der Recherche genannte `5.5.0-1` haette
also nicht nur arm64, sondern jeden Bau gebrochen.

### Task 3: die Konfiguration (TDD)

RED mit 33 fehlschlagenden Behauptungen, GREEN mit sechs Variablen, jede als
Modulkonstante mit ihrer Messung im Kommentar und jede zusaetzlich in der
ExApp-`info.xml` deklariert.

`FINDLING_OCR_ENABLED`, `_LANGUAGES`, `_MAX_PAGES`, `_PAGE_SECONDS`,
`_JOB_SECONDS`, `_DPI`. Zwei neue Leser, `_bool_from_environment` und
`_bounded_int_from_environment`, folgen dem bestehenden Vertrag: warnen mit dem
Namen, nie mit dem Wert, und auf den Default zurueckfallen. Im gesamten
OCR-Pfad wird nichts geworfen.

Die Sprachliste laeuft durch eine geschlossene Allowlist dessen, was das Image
traegt. Die Reihenfolge des Admins bleibt erhalten, anders als bei
`FINDLING_LANGUAGES`, weil sie hier ein tesseract-Argument ist und keine
Schema-Feldreihenfolge: die erste Sprache wiegt fuer die Engine mehr.

## Abweichungen vom Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Funktionalitaet] Harte Deadline abgeleitet statt festgeschrieben**

- **Gefunden bei:** Task 3
- **Problem:** Der Plan nennt 660 s als harte Deadline und 600 s als weiche,
  beide als feste Zahlen. `FINDLING_OCR_JOB_SECONDS` ist aber einstellbar. Setzt
  ein Admin die weiche Deadline auf 900, liegt sie ueber der harten, der
  Elternteil toetet das Kind vor dessen eigenem Schleifenende, und
  `indexed(truncated)` kommt nie mehr vor. Damit waere D-08 an genau der Stelle
  ausgehebelt, an der ein Admin eine gut gemeinte Aenderung macht.
- **Fix:** `OCR_HARD_DEADLINE_MARGIN_SECONDS = 60` und
  `ocr_hard_deadline_seconds = ocr_job_seconds + 60`. Die Invariante
  "hart strikt ueber weich" ist damit strukturell wahr statt zufaellig.
- **Test:** `test_the_hard_deadline_always_stays_above_the_soft_one`,
  parametrisiert ueber vier Budgets.
- **Commit:** 671bdf2

**2. [Rule 2 - Fehlende kritische Funktionalitaet] Bereichsgrenzen fuer die Zahlen**

- **Gefunden bei:** Task 3
- **Problem:** `_int_from_environment` prueft nur auf "positive ganze Zahl". Fuer
  die neuen Werte reicht das nicht: A4 bei 1200 dpi sind 137 Megapixel und
  sprengen den in Task 2 gemessenen Adressraum sofort, und ein Seiten- oder
  Zeitbudget weit ueber der Sperrfrist der Queue reproduziert exakt den
  Stuck-Claim-Fehler aus Pitfall 11, gegen den der 30-Seiten-Deckel existiert.
  Das ist die DoS-Fläche T-03-503, und sie war nur halb geschlossen.
- **Fix:** `_bounded_int_from_environment` mit vier Bereichskonstanten
  (`OCR_MAX_PAGES_RANGE` und drei weitere). Ausserhalb des Bereichs: Warnung und
  Default, kein Wurf.
- **Test:** `test_an_ocr_dpi_outside_the_measured_range_falls_back`, und der
  Seiten-Cap-Test enthaelt `100000` als Fall.
- **Commit:** 671bdf2

**3. [Rule 2 - Fehlende kritische Funktionalitaet] Injektionstests fuer die Allowlist**

- **Gefunden bei:** Task 3
- **Problem:** T-03-502 ist im Bedrohungsregister als `mitigate` gefuehrt, der
  Plan verlangt aber nur einen Rueckfalltest fuer unbekannte Sprachen. Ein
  Eintrag wie `--tessdata-dir /tmp` ist keine unbekannte Sprache, sondern eine
  Option, und er ist der eigentliche Fall.
- **Fix:** `test_the_ocr_language_list_never_leaves_the_allowlist`,
  parametrisiert ueber fuenf Versuche (Semikolon-Kette, fuehrender Doppelstrich,
  Kommandosubstitution, Pfad-Traversal).
- **Commit:** 42d222f (RED), 671bdf2 (GREEN)

**4. [Rule 1 - Bug in der Planvorgabe] Die Messvorlage des Plans war untauglich**

- **Gefunden bei:** Task 2
- **Problem:** Der Plan nennt `testdata/corpus/02-scan-no-text-layer.pdf` als
  Messvorlage. Die Seite misst 300 x 120 Punkt bei 814 Byte. An ihr laesst sich
  weder Adressraum noch Zeit je A4-Seite messen; jede Zahl daraus waere zu
  klein gewesen und haette A1 faelschlich bestaetigt.
- **Fix:** Im Container eine echte A4-Seite erzeugt, mit reiner
  Standardbibliothek nach dem Muster von `scripts/dev/build_corpus.py`. Der
  Grund und die Zahlen stehen in `docs/ocr.md` unter "Die Messvorlage", damit
  die naechste Messung nicht wieder in dieselbe Falle laeuft.
- **Commit:** 857dcdc

### Bewusst nicht getan

- **Kein eigener `RLIMIT_AS` fuer den OCR-Zweig.** Die Recherche hatte ihn fuer
  den Fall vorgesehen, dass 512 MB nicht reichen. Die Messung sagt, sie reichen
  vierfach. Eine zweite Speicherkonstante waere reine Pflegelast gewesen.
- **Kein Messtreiber im Repository.** Er baut eine Wegwerf-PDF und ruft die
  Kommandozeilen auf, die in `docs/ocr.md` vollstaendig abgedruckt sind. Was
  dauerhaft geprueft werden muss, prueft der Bau selbst, fail closed.
- **Kein `tesseract-ocr-frk`.** D-09 nennt Fraktur ausdruecklich als Option mit
  Default aus. Die Zeile liegt auskommentiert im Dockerfile, und der Kommentar
  neben `OCR_LANGUAGE_ALLOWLIST` sagt, dass beide Stellen zusammen geaendert
  werden muessen.

## Bekannte Stubs

Keine. Der Plan liefert Infrastruktur und Konfiguration, keinen Nutzerpfad; der
OCR-Zweig selbst entsteht in den Plaenen 03-06 und folgende. Die sechs
Settings-Felder haben heute noch keinen Leser ausser den Tests, und das ist die
beabsichtigte Reihenfolge: die Zahlen stehen fest, bevor der Code gebaut wird,
der sie braucht.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Registers. Die vier im Plan
aufgefuehrten Dispositionen sind umgesetzt:

| Threat | Umsetzung |
|---|---|
| T-03-501 | Sprachpakete hart gepinnt, Engine ueber den Digest verankert, Bau bricht ohne Sprachdaten und ohne Lizenztext ab |
| T-03-502 | Geschlossene Allowlist, fuenf Injektionsversuche als Test |
| T-03-503 | Deckel gemessen statt geschaetzt, zusaetzlich Bereichsgrenzen gegen absurde Werte |
| T-03-504 | Kein Wurf im gesamten OCR-Pfad, per Grep im Akzeptanzkriterium belegt |
| T-03-505 | Netto null neue PyPI-Pakete, Debian-Pakete einzeln geprueft, Lizenzen in THIRD-PARTY.md und im Image |

## Verifikation

| Gate | Ergebnis |
|---|---|
| `docker build -f backend/Dockerfile backend` | Exit 0 |
| `docker run --entrypoint tesseract <image> --list-langs` | deu, eng, osd |
| beide Lizenztexte im Image, nicht leer | Exit 0 |
| arm64-Paketaufloesung (`apt-get install -s`) | alle vier aufloesbar |
| `uv sync --frozen` | Exit 0 |
| `uv run pytest -q` | 489 passed, 1 skipped |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 62 files already formatted |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | Exit 0, keine Ausgabe |
| info.xml auf dem Store-Pfad (`pre-info.xslt` plus `info.xsd`) | beide validieren, alle sechs Variablen ueberleben die Transformation |

## TDD Gate Compliance

Task 3 traegt `tdd="true"`, und die Gate-Folge steht im Log:

- RED: `42d222f test(03-05): failing tests for the OCR configuration`, 33 rot
- GREEN: `671bdf2 feat(03-05): OCR configuration with the measured defaults`, 60 gruen
- REFACTOR: nicht noetig, alle Gates waren nach GREEN gruen

## Commits

| Commit | Typ | Inhalt |
|---|---|---|
| ce8a27a | feat | tesseract und Sprachdaten ins Laufzeitimage, pillow direkt gepinnt, THIRD-PARTY.md |
| 857dcdc | docs | docs/ocr.md mit Deckel-Kaskade und fuenf Messungen |
| 42d222f | test | RED-Gate der OCR-Konfiguration |
| 671bdf2 | feat | GREEN-Gate: config.py und info.xml |
| d907cda | docs | arm64-Paketaufloesung als Beleg der Pin-Entscheidung |

## Was die naechsten Plaene davon haben

- `settings().ocr_*` liefert sieben fertige Werte, inklusive der abgeleiteten
  harten Deadline. Kein Plan muss eine OCR-Zahl mehr schaetzen.
- `docs/ocr.md` sagt, wie ein Speichertod von aussen aussieht (Exitcode 134,
  kein MemoryError). Der Verdikt-Zweig in `ocr.py` kann direkt darauf bauen.
- Die WebP-Messung nimmt Plan 03-10 eine Unsicherheit ab: der Pillow-Umweg wird
  gebaut, aber wegen EXIF, Bombenpruefung und Plausibilitaetsdeckel, nicht weil
  das Format sonst unlesbar waere.
- Offen und ausdruecklich nicht hier erledigt: die Textlayer-Schwelle
  `_MIN_CHARS_PER_PAGE = 25` haengt weiter an zwei Korpusdateien und gehoert an
  einen echten DACH-Korpus.
