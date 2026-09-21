---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 08
subsystem: messbeleg-und-ci-gate
tags: [a4, l-09, erfolgskriterium-4, arm64, sprachfaelle, integration-yml, owner-checkpoint]

# Dependency graph
requires:
  - phase: 15-messphase-eine-box-anfahrt
    provides: die Bilanz der zehn Sprachfaelle mit Fremdbestand (5 von 10, 5 nicht messbar) als Vergleichszeile
  - phase: 16-haertung-und-store-einreichung-v1-2-0
    provides: Entscheid E3 der 16-CONTEXT.md (CI zuerst, Box nur bei belegtem CI-Fehlschlag) und das Gate ueber docs/ aus Plan 16-02
provides:
  - der arm64-Ast des Auftrags index-search-e2e in .github/workflows/integration.yml
  - docs/measurements/2026-09-a4-sprachfaelle-ci/README.md, der Beleg der zehn Faelle ohne Fremdbestand
  - L-09 in deferred-items.md als geschlossen, mit Laufnummer und Beleg
affects: [16-12-phasenaudit, 16-13-owner-abnahme]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Architekturachse in der Matrix traegt genau einen Wert, alles Weitere kommt ueber include; so bleibt die bestehende Kombination auf ihrer Maschine und der neue Eintrag ist eine vierte Kombination und keine geaenderte"
    - "runs-on liest den Runner aus der Matrix, damit ein Auftrag zwei Architekturen fahren kann, ohne dass eine zweite Auftragsdefinition entsteht, die auseinanderlaeuft"
    - "Ein Matrixumbau wird vor dem Push lokal expandiert und die erzeugten Kombinationen werden gedruckt; eine Workflow-Aenderung, die zum ersten Mal in CI ausgewertet wird, kostet einen Lauf je Tippfehler"
    - "Ein Zeitdeckel wird mit Laufnummern begruendet oder bleibt stehen; eine Anhebung ohne Zahl ist keine Aenderung, sondern eine Vermutung"

key-files:
  created:
    - docs/measurements/2026-09-a4-sprachfaelle-ci/README.md
  modified:
    - .github/workflows/integration.yml
    - .planning/phases/16-haertung-und-store-einreichung-v1-2-0/deferred-items.md

key-decisions:
  - "Der arm64-Eintrag faehrt sqlite und nur sqlite. Was dieser Ast beantwortet, ist eine Frage nach Suchqualitaet auf ARM und keine nach Datenbankdialekten; die drei Dialekte stehen unveraendert auf amd64 daneben"
  - "Der Zeitdeckel bleibt bei 45 Minuten, mit der Begruendung im Kommentar: die drei amd64-Eintraege des Vergleichslaufs 35582071147 brauchten 3:38 bis 3:54, der Deckel ist also rund das Elffache. Der gefahrene arm64-Eintrag brauchte 3:43 und hat die Entscheidung im Nachhinein bestaetigt"
  - "Der Beleg nennt ausdruecklich, dass der Schritt von sich aus nur eine Zeile druckt und die Trefferzahlen die zugesicherten sind; was sie belegt, ist der gruene Ausgang des Schritts und keine gedruckte Zahl. Eine bequemere Formulierung waere eine Behauptung ueber eine Ausgabe, die es nicht gibt"
  - "Der Beleg fuehrt die abweichende OCR-Fassung der Maschine (tesseract 5.3.4 statt 5.5.0 des Auslieferungsabbilds) im Abschnitt der Nicht-Beweise auf, obwohl der Plan sie nicht verlangt hat; die drei gescannten Faelle haengen daran"
  - "Kein Vermerk in deferred-items.md vor der Owner-Antwort. Der Plan bindet das Schliessen von L-09 an Zweig a, und der Zweig entscheidet sich am Beleg"

patterns-established:
  - "Die Sprachfaelle haben ab jetzt zwei Messorte mit verschiedenen Messwerkzeugen: die Rangmessung mit Fremdbestand aus Phase 15 und dieses dauerhafte Gate ohne Fremdbestand. Beide nennen ihre Grenze im eigenen Text"

requirements-completed: [A4]
requirements-partial: []

# Metrics
duration: 95 min
completed: 2026-09-21
---

# Phase 16 Plan 08: A4 ueber den arm64-CI-Ast Summary

Auflage A4 ist ohne Box erfüllt: der Auftrag `index-search-e2e` hat einen arm64-Ast, und Lauf 35586213137 beantwortet alle zehn deutschen Sprachfälle grün auf einer frischen Instanz, die vor dem Korpus null Dateien hält.

## Was gebaut wurde

**Der Ast** (`d34c392`). `.github/workflows/integration.yml` liest `runs-on` jetzt aus der Matrix. Die neue Achse `runner` trägt genau einen Wert, `ubuntu-24.04`, damit die drei bestehenden Kombinationen auf ihrer Maschine bleiben; ein `include`-Eintrag ergänzt `sqlite` / `stable34` / PHP 8.2 auf `ubuntu-24.04-arm`. Vier Kombinationen, drei auf amd64, eine auf arm64. Der Kommentar darüber nennt A4, Erfolgskriterium 4 und L-09, sagt was der Ast beweist (die zehn Fälle auf ARM64 gegen eine frische Instanz, wiederholbar und dauerhaft) und was er **nicht** beweist (keine echte Nextcloud mit AppAPI und HaRP auf einer m7g.large, keine harte Speichergrenze, Vier-Kern-Maschine derselben Flotte, Vorbehalt aus 14-02). `name:` trägt den Runner, damit die vier Kombinationen unterscheidbar sind.

**Der Beleg** (`b5da459`). `docs/measurements/2026-09-a4-sprachfaelle-ci/README.md`, gebaut aus der Ausgabe von Lauf **35586213137** (Auftrag `index-search-e2e (sqlite, ubuntu-24.04-arm)`, Auftragsnummer 106290048837, 21.09.2026, 09:58:38Z bis 10:02:21Z, 3 min 43 s, **success beim ersten Anlauf**, keine Wiederholung nötig). Er trägt die Bedingungen mit ihrer Fundstelle in der Laufausgabe, die zehn Fälle, die Gegenüberstellung zur Phase 15, den Pflichtabschnitt "Was dieser Lauf nicht beweist" und das Urteil zum Weg in einem Wort: **traegt**.

**Der Vermerk** (dieser Commit). L-09 steht in `deferred-items.md` als geschlossen, mit Laufnummer, Beleg und dem Owner-Wort.

## Der Lauf und die Bilanz

| Posten | Wert aus der Laufausgabe |
|---|---|
| Fremdbestand | `files on the instance before the corpus: 0` |
| Korpus | `corpus entries: 39`, `testdata/corpus`, rund 500 KB |
| Verdikte | `draining: open=0 indexed=26 skipped=7 failed=6`, 39 Dateien mit Verdikt |
| Zweite Spur | `second track: 26 of 26 documents carry a vector` |
| Maschine | `ubuntu-24.04-arm`, Abbild 20260907.118.1, Ubuntu 24.04.5 |
| Instanz | Zweig `stable34`, PHP 8.2.33, sqlite, App-Fassung 1.2.0, `tesseract 5.3.4` |
| Antwortzeit | 298 ms für den ersten Fall |

**Zehn von zehn Fällen grün, null rot, null ohne Aussage.** Die fünf in Phase 15 nicht messbaren Fälle (`Genehmigung`, `Frist`, `Vertrag`, `bescheid`, `type:pdf bescheid`) tragen jetzt eine Aussage; die fünf dort grünen bleiben grün. Damit bestätigt der Lauf auch die Begründung der Phase 15: die fünf scheiterten an der Verdünnung durch rund 52.000 Fremddokumente und an keinem Sprachbefund.

## Der Owner-Entscheid

Vorgelegt wurde **genau ein Zweig**, und der Beleg hat ihn bestimmt: Zweig a. Es wurde keine Box angeboten und kein Deckel abgerufen.

**Antwort des Owners am 21.09.2026, im Wortlaut, per strukturierter Rückfrage bestätigt:**

> "Zweig a, zustimmen"

Damit wird Erfolgskriterium 4 der Phase 15 (Befund L-09) mit Lauf 35586213137 und dem Beleg als erfüllt geführt. Keine Box, kein Deckel-Abruf.

## Die Zweig-a-Vorlage in Kurzform, wie sie dem Owner vorlag

1. **Bilanz:** zehn von zehn Fällen grün auf `ubuntu-24.04-arm`, Lauf 35586213137, Instanz ohne Fremdbestand (`files on the instance before the corpus: 0`), Korpus 39 Dateien.
2. **Gegenüberstellung:** Phase 15 hatte 5 von 10 grün bei 5 ohne Aussage; alle fünf ohne Aussage tragen jetzt eine, keiner von ihnen ist rot.
3. **Nicht-Beweise:** keine echte Nextcloud mit AppAPI und HaRP, keine m7g.large (Vier-Kern-Maschine derselben Flotte, Vorbehalt aus 14-02), keine harte Speichergrenze, keine Zeit- oder Speicheraussage, keine Aussage über das Verhalten unter Fremdbestand, keine über Datenbankdialekte, und eine andere OCR-Fassung als im Auslieferungsabbild.
4. **Vorschlag:** Erfolgskriterium 4 (L-09) als erfüllt führen, A4 über den kostenlosen Weg des Entscheids E3 schließen, den Ast als dauerhaftes Gate stehen lassen.

## Verifikation

| Was | Befehl | Ergebnis |
|---|---|---|
| arm64 in der Datei | `grep -c "ubuntu-24.04-arm" .github/workflows/integration.yml` | 1 |
| Matrix | YAML geladen, Kombinationen expandiert und gedruckt | vier Kombinationen, drei amd64, eine arm64, `matrix ok` |
| `runs-on` | dieselbe Auswertung | `${{ matrix.runner }}`, keine bestehende Kombination hat den Runner gewechselt |
| Deadline-Gate | `uv run pytest tests/test_workflow_pins.py -q` | 64 bestanden (siehe Abweichung 2) |
| Beleg vorhanden | `test -f docs/measurements/2026-09-a4-sprachfaelle-ci/README.md` | ja |
| Pflichtformeln | `grep -c "ohne Fremdbestand"`, `grep -cE "traegt( nicht)?"`, `grep -c "index-search-e2e"` | 2, 5, 2 |
| Gate ueber docs/ | `uv run pytest tests/test_public_artifacts.py -q` | 51 bestanden |
| ruff | `uv run ruff check .` | sauber |
| ruff format | `uv run ruff format --check .` | 125 Dateien formatiert |
| pyright | `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` | 0 errors, 0 warnings |
| vulture | `uv run vulture src tests --min-confidence 80` | sauber |
| volle Suite | `uv run pytest -q` | **2469 bestanden / 15 uebersprungen**, zweimal gefahren, unveraendert gegen den Stand nach 16-07 |
| der Lauf selbst | `gh run view 35586213137` | success, alle acht Auftraege gruen |

Der neue Bericht ist reines ASCII mit LF, wie der Plan es für dieses Verzeichnis verlangt; beide Commit-Blobs wurden nachgesehen.

## Abweichungen vom Plan

### 1. [Rule 1 - Bug] Der verify-Einzeiler des Plans kann nie grün werden

**Gefunden bei:** Task 1.
**Sachverhalt:** `assert any('arm' in str(v) for v in str(m))` iteriert über die Zeichen von `str(m)`; jedes `v` ist ein einzelnes Zeichen, `'arm' in v` ist deshalb immer falsch, und die Zusicherung reißt auch über einer korrekten Matrix.
**Folge:** Gefahren wurde die offensichtlich gemeinte Form `assert 'arm' in str(m)`, zusätzlich eine echte Matrixexpansion, die die vier Kombinationen druckt. Die PLAN-Datei wurde nicht editiert, der Befund steht hier.

### 2. Ein eigener Fehler, vom Gate des Repositoriums gefangen

**Gefunden bei:** Task 1.
**Sachverhalt:** Die erste Fassung des Kommentarblocks über `timeout-minutes` hat die Zeile `timeout-minutes: 45` mitgenommen. `test_every_job_of_every_workflow_has_a_deadline` ging rot mit der Meldung, der Auftrag habe keine Deadline und stehe damit bei den 360 Minuten der Voreinstellung.
**Folge:** Zeile wieder eingesetzt, Gate grün. Das ist genau der Wächter, den T-16-29 meint, und er hat vor dem Push zugeschlagen und nicht nach ihm.

### 3. Der Plan wurde in drei Etappen ausgeführt

**Gefunden bei:** Task 2.
**Sachverhalt:** Task 2 verlangt eine Laufausgabe, der Auftrag dieses Ausführers verbietet das Pushen. Zwischen Task 1 und Task 2 liegt deshalb der Push des Orchestrators, und zwischen Task 2 und dem Abschluss die Rückfrage an den Owner.
**Folge:** Vier Commits statt zwei, davon zwei reine STATE-Nachträge (`845c019`, `01b65d5`). Kein Zwischenstand war rot: der Ast allein ist grün, und der Beleg kam erst, als es ihn zu belegen gab.

### 4. Der Zeitdeckel wurde nicht angehoben

**Gefunden bei:** Task 1.
**Sachverhalt:** Das Abnahmekriterium lässt beides zu, verlangt aber für eine Anhebung eine Begründung.
**Folge:** 45 Minuten bleiben stehen, mit den drei amd64-Laufzeiten aus Lauf 35582071147 im Kommentar. Der gefahrene arm64-Eintrag brauchte 3:43 und liegt damit bei einem Zwölftel des Deckels.

## Was offen bleibt

**Die Namen der Prüfungen haben sich geändert.** `name:` trägt jetzt den Runner, die vier Kombinationen heißen also anders als die drei davor. Nachgesehen statt angenommen: das Regelwerk `protect-main` des Repositoriums führt nur `deletion` und `non_fast_forward` und keine erforderlichen Prüfungen, es zeigt also nichts auf die alten Namen. Wer später erforderliche Prüfungen einrichtet, muss die neuen Namen nehmen.

**Der Ast fährt sqlite und amd64 fährt die Dialekte.** Ein Dialektdefekt, der nur auf ARM aufträte, bliebe unentdeckt. Das ist eine bewusste Kostenentscheidung und keine Lücke aus Versehen.

**Die OCR-Fassung der Maschine ist nicht die des Auslieferungsabbilds** (5.3.4 gegen 5.5.0). Für die drei gescannten Fälle heißt das: der Text wurde erkannt, aber nicht von der Fassung, die ein Nutzer installiert. Steht im Beleg, gehört nicht in diesen Plan.

**Ein Nebenbefund, der einem anderen Plan gehört:** der sha256-Abgleich des Modells lief auf der arm64-Seite des veröffentlichten Abbilds durch. Damit ist belegt, was `docs/measurements/2026-09-05-modellqualitaet/` bisher nur für amd64 sagte, nämlich dass beide Architekturen dieselbe Modelldatei tragen. Der Bericht dort wurde nicht angefasst.

## Known Stubs

Keine. Der Ast fährt, der Beleg trägt Zahlen aus einer Laufausgabe, und kein Abschnitt des Berichts ist ein Platzhalter.

## Threat Flags

Keine neue Angriffsfläche. Die vier Bedrohungen des Plans sind belegt: T-16-28 (Box ohne Beleg) durch den blockierenden Checkpoint, an dem Zweig a mit Laufnummer vorlag; T-16-29 (Zeitdeckel) durch den geprüften und begründeten Deckel plus das Deadline-Gate, das in diesem Plan einmal ausgelöst hat; T-16-30 (fremder Maschinentyp) durch den Pflichtabschnitt der Nicht-Beweise; T-16-31 (Kennung im Messverzeichnis) durch das Gate aus Plan 16-02, das über dem neuen Verzeichnis grün ist. Keine neue Abhängigkeit, kein Paketinstall (T-16-SC).

## Self-Check: PASSED

Vier Commits vorhanden (`d34c392`, `845c019`, `b5da459`, plus dieser Abschluss), die geänderte Workflow-Datei und der neue Bericht vorhanden, Lauf 35586213137 über `gh` nachgesehen und success, alle verify-Befehle grün, volle Suite 2469 bestanden / 15 uebersprungen.
