---
phase: 11-haertung-und-store-einreichung-v1-1
plan: 09
subsystem: store-texte
tags: [store-text, messsatz, d-06, d-07, d-08, fr-gate, kurztext-regel, rel-01, textabnahme]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: die Zahlen der Vergleichsmessung, vom Owner am 10.09.2026 abgenommen (Grundlast 103,2 MB, anon-Spitze 1.764,2 MB, p95 Stufe 8 = 2.125,5 ms)
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: die Werkzeug-Anfahrt vom 10.09.2026 abends mit DI-10-01 geschlossen und DI-10-02 offen (Plan 11-06)
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: der franzoesische Katalog und seine vier Gates, erster Teil des FR-Gates (Plan 11-05 und 11-08)
provides:
  - "die vom Owner am 11.09.2026 abgenommene Fassung aller sechs Store-Texte, Fassung B mit der einen Kernzahl 103,2 MB, dreisprachig"
  - "die Abnahmezeile in docs/store-listing.md, mit Datum, Fassung, Messsatz-Entscheid und FR-Gate Teil 2 von 2"
  - "der fortgeschriebene Messsatz mit 52.111 Dokumenten und 1.764 MB in allen drei READMEs"
  - "die datierte Grundlast-Zeile 691,8 auf 103,2 MB, minus 85,1 Prozent, in allen drei READMEs"
  - "scan_measured_sentence mit dem Wortlaut als Argument, drei Aufrufe, einer je README"
  - "MEASURED_SENTENCE_DE und MEASURED_SENTENCE_FR als gehaltene Wortlaute"
  - "die Sprachfall- und Werkzeugbefunde aus 11-06 im Messbericht docs/performance.md"
affects: [11-10, 11-11, 11-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Textrunde statt zwei: derselbe Entwurf, den der Owner sieht, ist der, den die Einreichung traegt"
    - "Ein Entwurf legt Fassungen woertlich und dreisprachig nebeneinander, damit der Owner entscheidet statt uebersetzt"
    - "Der Entwurf bleibt nach der Abnahme im Dokument stehen: eine Entscheidung ohne die verworfene Fassung ist spaeter nicht nachvollziehbar"
    - "Eine Zahl im Produkttext traegt genau eine Aufgabe; der datierte Vergleich steht eine Ebene tiefer, die Methode zwei"
    - "Wo eine Gleichlaeufigkeit bisher eine Regel in CLAUDE.md war, tritt ein Gate an ihre Stelle, sobald es die Gelegenheit dazu gibt"

key-files:
  created: []
  modified:
    - docs/store-listing.md
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - README.en.md
    - README.md
    - README.fr.md
    - backend/tests/test_store_metadata.py
    - docs/performance.md

key-decisions:
  - "Owner-Entscheid vom 11.09.2026: Fassung B. Beide info.xml tragen die eine Kernzahl 103,2 MB im Leerlauf, dreisprachig, in der RAM-Zeile ihres Anforderungsblocks. Die Kurztext-Regel bleibt gewahrt, weil es bei genau einer Zahl bleibt; der datierte Alt-Neu-Vergleich steht im README und nicht im Store-Text"
  - "Owner-Entscheid vom 11.09.2026: der Messsatz wird dreisprachig. Damit ist die Gleichlaeufigkeit der drei READMEs eine Maschine statt einer Regel in CLAUDE.md, und scan_measured_sentence nimmt den Wortlaut als Argument statt drei Scanner zu bekommen"
  - "Owner-Entscheid vom 11.09.2026: FR ok, keine Wortlautaenderung an den franzoesischen Texten. Die Wortwahl aus docs/l10n-french.md gilt unveraendert (le service, passage, Mo, reconnaissance optique)"
  - "Die Prozentzahl lautet 85,1 und nicht 85. Der Plan nannte die glatte Zahl, die Herkunftsregel dieses Projekts rundet nichts, und 588,6 von 691,8 MB sind 85,1 Prozent. Der Owner hat dazu keinen Einwand erhoben"
  - "Der Messsatz behaelt 52.111 und nicht 52.137. Er beschreibt den Lauf vom 09./10.09., und die 39 Dateien Unterschied sind der Sprachfall-Korpus, den Plan 11-06 nach diesem Lauf hochgeladen hat. Die Einordnung steht im Entwurf und im Kommentar der Konstante"
  - "Der Store-Text bekommt keine eigene Verweiszeile auf docs/. Der Verweis ist der website-Eintrag beider info.xml, der auf das Repository und damit auf README.en.md zeigt; eine Zeile mehr waere eine dritte Fassung gewesen, die niemand verlangt hat"
  - "Der Drei-Stellen-Merker aus DI-10-03 ist nicht repariert worden, weil er keine Regression ist: seit dem 07.09.2026 bindet das Gate den Messsatz an die READMEs und nicht an die info.xml. Diese Lesart steht jetzt im Docstring des Scanners mit beiden Daten"
  - "Die Mess-Vorbehalte stehen ausschliesslich im Bericht und in docs/performance.md (D-08). Der Entwurf benennt sie in einem eigenen Abschnitt, der ausdruecklich kein Store-Text ist, damit die Regel ihren Gegenstand nennt"

patterns-established:
  - "Ein Gate ueber mehrere Sprachen bekommt den Wortlaut als Argument und je Datei einen Aufruf, statt drei Scanner zu werden"
  - "Zu einem sprachabhaengigen Gate gehoert der Kreuztest: der deutsche Wortlaut gegen den englischen Text muss melden, sonst faellt ein Vertauschen nicht auf"
  - "Eine Anti-Leerlauf-Klausel begleitet jede neue Dateibindung: zwei neue READMEs im Gate brauchen den Existenztest, sonst sind zwei gruene Tests ueber zwei fehlende Dateien moeglich"

requirements-completed: []

# Metrics
duration: 95min
completed: 2026-09-11
---

# Phase 11 Plan 09: Die Store-Texte mit den v1.1-Zahlen, abgenommen Summary

**Der Owner hat am 11.09.2026 Fassung B gewaehlt und den Messsatz dreisprachig entschieden: beide `info.xml` tragen jetzt die eine Kernzahl 103,2 MB Grundlast in allen drei Sprachen, alle drei READMEs tragen den fortgeschriebenen Messsatz mit 52.111 Dokumenten und 1.764 MB samt der datierten Zeile 691,8 auf 103,2 MB, und `scan_measured_sentence` haelt seitdem drei Wortlaute mit je einem Aufruf je Datei.**

## Was entstanden ist

### Der Entwurf (Task 1)

`docs/store-listing.md` traegt unter der geltenden Vorlage einen Abschnitt mit
drei Teilen: den fortgeschriebenen Messsatz, die zwei Fassungen des Store-Textes
woertlich und dreisprachig nebeneinander, und den Wortlaut fuer die Frage nach
dem dreisprachigen Messsatz. Dazu die Leseliste des FR-Gates, die Ausschluesse
nach D-08 und das Gegenlesen der RAM-Budget-Tabelle.

Jede Zahl nennt ihre Rohdatei:

| Groesse | Vorwert v1.0 | v1.1 | Rohdatei |
|---|---:|---:|---|
| indexierte Dokumente | 51.961 | **52.111** | `rohdaten/48-vektorbestand.txt` |
| Spitze des anonymen Speichers | 1.813 MB | **1.764,2 MB** | `rohdaten/00-ende.txt` |
| Grundlast im Leerlauf | 691,8 MB | **103,2 MB** | `rohdaten/94-grundlast.txt` |

Zwei Punkte hat der Entwurf von sich aus geklaert, statt sie offen zu lassen.
Erstens die Prozentzahl: 588,6 von 691,8 MB sind 85,1 Prozent, und die
Herkunftsregel dieses Projekts rundet nichts. Zweitens der Bestand: Plan 11-06
hat auf derselben Box 52.137 gemessen, aber erst nachdem der Sprachfall-Korpus
mit seinen 39 Dateien hochgeladen war, und der Messsatz beschreibt den Lauf, den
er beschreibt.

**Das Gegenlesen der RAM-Budget-Tabelle in `CLAUDE.md` ergab keinen
Widerspruch.** Die Zeile ueber Tokenizer und Splitter fuehrt im Ruhezustand
"0 bei faulem Bau" und die 544 MB als Spitze ab dem ersten Chunkerlauf; die
103,2 MB sind die Grundlast mit nie geladenem Modell, also genau der Zustand,
den die Spalte Ruhezustand beschreibt. `CLAUDE.md` ist nicht angefasst worden.

### Die Abnahme (Task 2)

Der Owner hat beide Fassungen im Wortlaut gesehen und entschieden: **Fassung B,
Messsatz dreisprachig, FR ok.** Zur Prozentzahl kam kein Einwand. Die Zeile
steht in `docs/store-listing.md`:

```
Textabnahme: 2026-09-11, Fassung B, Messsatz dreisprachig, FR-Gate Teil 2 von 2 abgenommen (D-06, D-07, D-08)
```

Der Entwurf bleibt darueber stehen. Eine Entscheidung ohne die Fassung, die
nicht gewaehlt wurde, ist in einem halben Jahr nicht mehr nachvollziehbar.

### Die Einarbeitung (Task 3)

**Die sechs Store-Texte.** Geaendert hat sich genau eine Zeile je Text, in
beiden Haelften und in allen drei Sprachen:

| Sprache | vorher | nachher |
|---|---|---|
| Englisch | RAM: 4 GB is enough, the container runs under a hard 2 GB limit (measured) | RAM: 4 GB is enough, 103.2 MB idle, under a hard 2 GB limit (measured) |
| Deutsch | RAM: 4 GB genuegen, der Container laeuft unter einer harten 2-GB-Grenze (gemessen) | RAM: 4 GB genuegen, 103,2 MB im Leerlauf, unter einer harten 2-GB-Grenze (gemessen) |
| Franzoesisch | RAM : 4 Go suffisent, le conteneur reste sous une limite stricte de 2 Go (mesure) | RAM : 4 Go suffisent, 103,2 Mo au repos, sous une limite stricte de 2 Go (mesure) |

Vorlage und beide `info.xml` tragen denselben Wortlaut. Faktenliste,
Dateitypen, der eine Satz zum MCP Connector und der Datenschutzabsatz sind
unberuehrt.

**Die drei READMEs.** `README.en.md` traegt den Messsatz mit den getauschten
Werten, `README.md` und `README.fr.md` tragen ihn erstmals in ihrer Sprache,
und alle drei tragen darunter die datierte Grundlast-Zeile mit Verweis auf
`docs/performance.md`.

**Das Gate.** `scan_measured_sentence` nimmt den Wortlaut jetzt als drittes
Argument mit dem englischen als Vorgabe, und es gibt drei Aufrufe, einen je
Datei. Dazu `MEASURED_SENTENCE_DE` und `MEASURED_SENTENCE_FR`, jeweils in der
Zahlenschreibweise ihrer Sprache: 52.111 und 1.764 MB im Deutschen, 52 111 und
1 764 Mo im Franzoesischen. Der Docstring nennt beide Daten, den 07.09. und den
11.09., damit der naechste Leser den ueberholten Drei-Stellen-Merker nicht noch
einmal sucht.

Vier neue Tests, 48 auf 52:

| Test | Was er haelt |
|---|---|
| `test_the_two_other_readmes_exist_before_their_sentences_are_judged` | die Anti-Leerlauf-Klausel: ohne sie waeren zwei gruene Tests ueber zwei fehlende Dateien moeglich |
| `test_the_measured_sentence_stands_in_the_german_readme` | `README.md` gegen `MEASURED_SENTENCE_DE` |
| `test_the_measured_sentence_stands_in_the_french_readme` | `README.fr.md` gegen `MEASURED_SENTENCE_FR` |
| `test_a_mutated_peak_is_reported_in_each_of_the_three_languages` | die Spitze mutiert in allen drei Schreibweisen (1,764 / 1.764 / 1 764), dazu der Kreuztest: der deutsche Wortlaut gegen den englischen Text muss melden |

Der bestehende Selbsttest mutiert weiter die Zahl, jetzt 1,764 auf 1,964 statt
1,813 auf 1,913.

**Der Messbericht.** `docs/performance.md` trug die v1.1-Zahlen mit Methode
bereits aus Plan 10-07. Nachgezogen ist die Anfahrt aus 11-06: DI-10-01 ist
geschlossen (30 gemeldete Fehlschlaege der Stufe 16 rechnen als 14
Protokollabbrueche plus 16 trefferlose Begriffe auf), DI-10-02 bleibt offen (die
Vorpruefung misst einen Antwortdeckel von 26 statt des Bestands, die Bilanz
bleibt 6 von 10), und die Standtabelle traegt die Anfahrt mit Laufzeit und
Kosten.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Der Entwurf war in ASCII-Ersatzschreibung verfasst**

- **Found during:** Task 1, vor dem ersten Schreiben
- **Issue:** Die erste Fassung des Entwurfstextes trug `ae`, `oe`, `ue` und
  Akzente ohne Zeichen, wie es die Planungsdateien tun. `docs/store-listing.md`
  ist aber ein oeffentlicher Text mit echten Umlauten, und die zitierten
  Store-Texte muessen woertlich stimmen, sonst zitiert der Entwurf etwas, das so
  nirgends steht.
- **Fix:** Der Abschnitt ist mit echten Umlauten und Akzenten geschrieben
  worden, bevor er in die Datei ging.
- **Files modified:** docs/store-listing.md
- **Commit:** ad4c412

### Bewusste Auslegungen

**Der Zeilenumbruch in der Abnahmezeile ist aufgeloest worden.** Der erste Guss
hat die Zeile auf 80 Zeichen umbrochen, wie den Rest des Dokuments. Eine Zeile,
die ein Abnahmekriterium mit `grep` sucht, ist aber eine physische Zeile; sie
steht jetzt ungebrochen da und ist die einzige lange Zeile des Abschnitts.

**`docs/performance.md` hat keine neue Zahlenrunde bekommen.** Der Plan
verlangt die v1.1-Zahlen mit Methode; Plan 10-07 hat sie am 10.09. vollstaendig
eingetragen, samt Vorbehalten und der Methodik-Korrektur zur Kaltstartzahl. Was
fehlte, war die Anfahrt aus 11-06, und genau die ist nachgezogen. Doppelt
geschriebene Zahlen waeren die Fehlerquelle gewesen, gegen die dieser Plan
antritt.

**Kein Versionsbump.** Weder `version` noch `image-tag` sind angefasst; der
Bump auf 1.1.0 gehoert in Plan 11-11.

## Authentication Gates

Keine.

## Verification

Aus `backend/`:

| Gate | Ergebnis |
|---|---|
| `uv run python -m pytest -q` | 2020 passed, 15 skipped (Grundlinie 2016, plus die vier neuen Gates) |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 121 files already formatted |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | ohne Befund |
| `scripts/dev/validate_info_xml.sh php/... backend/...` | beide passieren den Store-Weg, Transform dann Schema, gegen appstore `eda850ba` |

Dazu von Hand, weil kein Gate diese vier Dateien liest: `README.md`,
`README.fr.md`, `README.en.md` und `docs/performance.md` tragen kein gesperrtes
Vokabular, keinen Gedankenstrich und kein Emoji. Die Zeilenenden sind je Datei
unveraendert geblieben (CRLF im Arbeitsbaum ausser `docs/performance.md`, das
LF traegt; der Index fuehrt alle mit LF).

**Die Rot-Faehigkeit ist am echten Baum belegt:** `1 764 Mo` in `README.fr.md`
auf `1 964 Mo` mutiert macht `test_the_measured_sentence_stands_in_the_french_readme`
rot. Die Datei ist danach wiederhergestellt worden.

### CI auf `70e19b0`

Alle sechs Workflows gruen, im ersten Anlauf:

| Workflow | Lauf | Ergebnis |
|---|---:|---|
| Python gates | 34553326038 | success |
| PHP and store metadata gates | 34553326034 | success |
| Integration | 34553326021 | success |
| Resilience | 34553326016 | success |
| Multi-arch image | 34553326019 | success |
| HaRP deploy | 34553326020 | success |

Der Entwurfs-Commit `ad4c412` beruehrt nur `docs/` und loest deshalb keinen
Lauf aus.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsflaeche. Dieser Plan aendert Text, keinen ausgefuehrten Pfad.
Die vier Dispositionen des Bedrohungsregisters sind bedient: T-11-35 durch die
eine Kernzahl mit dem datierten Vergleich eine Ebene tiefer, T-11-36 durch die
gemeinsame Aenderung von `README.en.md` und `MEASURED_SENTENCE`, T-11-37 durch
das gefahrene Vokabular-Gate und die Handpruefung der vier ungedeckten Dateien,
T-11-38 durch den blockierenden FR-Checkpoint, T-11-39 durch `scan_info`, das
ueber beide `info.xml` gruen steht, und zusaetzlich durch die Schema-Validierung
auf dem Store-Weg.

## Self-Check: PASSED

Acht geaenderte Dateien und die SUMMARY liegen im Baum, die vier Commits
`ad4c412`, `8024a00`, `d2b5fcd` und `70e19b0` stehen im Log, und alle sechs
CI-Workflows auf `70e19b0` sind gruen.
