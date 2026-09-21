---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 10
subsystem: ocr
tags: [bl-f02, ocr, sprachen, dockerfile, allowlist, third-party, owner-tor]

# Dependency graph
requires:
  - phase: 16-haertung-und-store-einreichung-v1-2-0
    provides: der Versionsbump auf 1.2.0 und die Migration (Plan 16-07), damit die sechs Pakete in das Abbild gehen, das eingereicht wird
  - phase: 15-messphase-eine-box-anfahrt
    provides: die abgebaute Messanfahrt; der Backlog bindet Baustein 1 ausdruecklich an "erst NACH der Messanfahrt", weil der Werkzeugstand Vergleichbarkeitsbedingung des Messlaufs war
  - phase: 06.1-launch-haertung-vor-der-store-abgabe
    provides: die Bauform, an der sich dieser Plan entlanghangelt (fra als dritte OCR-Sprache, Plan 06.1-21, und test_ocr_french.py als Vorbild des Gates)
provides:
  - neun OCR-Sprachen im Abbild (deu, eng, fra, spa, ita, nld, por, dan, est), jede beim Bau mit tesseract --list-langs geprueft
  - OCR_LANGUAGE_ALLOWLIST mit neun Eintraegen bei unveraendertem Standard deu+eng+fra
  - backend/tests/test_ocr_languages.py als Gate, das Positivliste und Dockerfile nicht mehr auseinanderlaufen laesst
  - die Lizenzlage der sieben spaeter zugekommenen Sprachpakete in THIRD-PARTY.md
affects: [16-11-textentwurf, 16-12-textuebernahme, 16-14-abgabe]

# Tech tracking
tech-stack:
  added:
    - "tesseract-ocr-spa 1:4.1.0-2 (Debian trixie, Quellpaket tesseract-lang, Architecture all)"
    - "tesseract-ocr-ita 1:4.1.0-2 (dieselbe Quelle)"
    - "tesseract-ocr-nld 1:4.1.0-2 (dieselbe Quelle)"
    - "tesseract-ocr-por 1:4.1.0-2 (dieselbe Quelle)"
    - "tesseract-ocr-dan 1:4.1.0-2 (dieselbe Quelle)"
    - "tesseract-ocr-est 1:4.1.0-2 (dieselbe Quelle)"
  patterns:
    - "Eine Sprache verfuegbar machen und eine Sprache einschalten sind zwei Entscheidungen; die Positivliste waechst, der Standard nicht, und der Kommentar traegt den Grund"
    - "Ein Gate, das zwei Listen zusammenhaelt, liest die eine aus dem Code und schreibt sie nicht ab; eine im Test wiederholte Liste ist sich selbst einig an genau dem Tag, an dem jemand die zehnte Sprache aufnimmt"
    - "Der rote Zustand eines Textlesers wird gestagt, indem die Zeilen einer Sprache aus einer Kopie des Dateitextes fallen; das kostet keinen Prozess und keine Datei"
    - "Die Existenz eines Distributionspakets wird vor dem Bau gegen die Paketquelle nachgesehen (api.ftp-master.debian.org), nicht aus einem Backlog-Eintrag uebernommen"

key-files:
  created:
    - backend/tests/test_ocr_languages.py
  modified:
    - backend/Dockerfile
    - backend/src/findling/config.py
    - THIRD-PARTY.md
    - backend/tests/test_ocr_french.py
    - backend/tests/test_measurement_scripts.py
    - docs/ocr.md
    - .planning/BACKLOG.md

key-decisions:
  - "Owner-Entscheid am Tor, im Wortlaut: \"Mitfahren\". Baustein 1 faehrt in v1.2.0 mit, der Abbruchpfad ist nicht gezogen worden. Bestaetigt am 21.09.2026 per strukturierter Rueckfrage, nachdem der Stand der Phase, der Umfang, die Pruefung der Annahme A7 und der Abbruchpfad vorlagen"
  - "Annahme A7 ist vor dem Bau gegen die Paketquelle geprueft und nicht geglaubt worden. Alle sechs Pakete stehen in Debian stable als 1:4.1.0-2, Komponente main, Architecture all, Quellpaket tesseract-lang, also dieselbe Signaturkette wie das Basisabbild. Faellt diese Pruefung anders aus, waere sie allein schon ein Grund fuer den Abbruchpfad gewesen"
  - "OCR_DEFAULT_LANGUAGES bleibt bei drei. Ein Standard mit neun Sprachen laedt sechs weitere traineddata auf jeder Seite jeder bestehenden Installation und waere eine Verhaltensaenderung, die niemand bestellt hat (T-16-37). Verfuegbar ist nicht eingeschaltet"
  - "Die Store-Texte bleiben in diesem Plan unberuehrt. Neun Sprachen heisst neun Sprachen im Text, dreisprachig, und diese Aenderung macht Plan 16-11 geschlossen; ein halber Textstand ueber zwei Plaene waere genau die Drift, die dieser Plan an anderer Stelle schliesst"
  - "test_ocr_french.py gibt die Behauptung ueber die Groesse der Positivliste ab und behaelt die ueber Franzoesisch. Zwei Dateien, die dieselbe Menge aufschreiben, widersprechen sich am Tag der zehnten Sprache; die Menge gegen das Abbild ist ab jetzt Gegenstand von test_ocr_languages.py"

patterns-established:
  - "Ein Backlog-Kandidat mit Nebenbedingung bekommt ein Tor VOR dem Bau, mit vier vorzulegenden Zeilen (Stand der Phase, Umfang, die ungeprueffte Annahme, Abbruchpfad), und die Antwort des Owners steht im Wortlaut in der SUMMARY"

requirements-completed: []
requirements-partial: []

# Metrics
duration: 75 min
completed: 2026-09-21
---

# Phase 16 Plan 10: Sechs weitere OCR-Sprachen, der Standard bleibt bei drei Summary

Das Abbild liest ab v1.2.0 Scans in neun Sprachen statt in drei, und trotzdem wird keine einzige bestehende Installation langsamer: die sechs neuen Pakete sind verfuegbar, nicht eingeschaltet, und ein Gate haelt ab jetzt die Positivliste des Lesers und den apt-Block des Abbilds zusammen, damit die beiden nicht stumm auseinanderlaufen koennen.

## Der Owner-Entscheid am Tor

Der Plan beginnt mit einem Tor (`checkpoint:decision`, `gate="blocking"`), weil Entscheid E4 der `16-CONTEXT.md` Baustein 1 an eine Bedingung bindet: **nur ohne Terminrisiko**, sonst faellt er ersatzlos aufs Folgerelease. Vorgelegt wurden die vier Zeilen, die der Plan verlangt:

1. **Stand der Phase.** 16-01 bis 16-09 abgeschlossen (9 von 14), Wellen 1 bis 3 vollstaendig, Welle 4 zur Haelfte. 16-09 ist gruen und seit dem 21.09.2026 mit Laufnummer belegt (`deploy-harp` Lauf 35594647362, alle sechs Zusicherungen halten). Kein offener Befund aus 16-09 stand gegen diesen Plan.
2. **Der Umfang**, ehrlich: sechs apt-Zeilen mit Pin, sechs Pruefungen beim Bau, die Lizenzlage, `OCR_LANGUAGE_ALLOWLIST` von drei auf neun, `THIRD-PARTY.md`, ein Gate, `PACKAGE_TREE_HASH_TODAY` und die Abbildgroesse.
3. **Annahme A7**, vor dem Bau nachgesehen und nicht uebernommen (siehe Verifikation).
4. **Der Abbruchpfad**, benannt, bevor gebaut wurde, samt der Angabe, welche zwei Commits er zurueckbaut und welche zwei Nacharbeiten er ausloest (`BACKLOG.md` fortschreiben, Plan 16-11 erfaehrt "drei Sprachen").

**Die Antwort des Owners, im Wortlaut: "Mitfahren".** Bestaetigt am 21.09.2026 per strukturierter Rueckfrage. Der Abbruchpfad ist damit nicht gezogen worden, und sein Grund ist auch nicht eingetreten: kein Paket fehlte, und der Bau ist nicht ins Rutschen gekommen.

## Was gebaut wurde

### Task 2: sechs Sprachpakete, sechs Pruefungen, eine Liste (`a9ee779`)

**Der Dockerfile.** Sechs Zeilen im bestehenden apt-Block, zwischen `fra` und `osd`, je mit dem harten Pin `=1:4.1.0-2`: `tesseract-ocr-spa`, `-ita`, `-nld`, `-por`, `-dan`, `-est`. Dahinter sechs eigene Pruefungen der Form `tesseract --list-langs 2>&1 | grep -qx <code>`. Das ist die Haelfte, die T-16-36 schliesst: apt kann erfolgreich sein, waehrend die traineddata nicht dort liegt, wo tesseract sie sucht, und ohne die Pruefung faellt genau das erst pro Seite auf einer fremden Box auf.

Der Kommentarblock ist an drei Stellen fortgeschrieben, weil er sonst eine falsche Zahl behauptet haette: aus den "vier Sprachpaketen" werden zehn, der neue Absatz nennt Anlass, Herkunft, Pruefdatum und Preis der sechs, und der Absatz zur Apache-2.0-Pflicht sagt jetzt genau, was gemessen ist und was hergeleitet: gemessen ist die Byte-Gleichheit der Lizenzdateien vom 01.09.2026 fuer die Packs jenes Tages, hergeleitet ist sie fuer die sieben spaeter zugekommenen, weil `tesseract-lang` ein einziges `debian/copyright` hat. Diese Unterscheidung steht ausdruecklich da, statt die alte Messung stillschweigend auf neue Pakete umzudeuten.

**Die Liste.** `OCR_LANGUAGE_ALLOWLIST` waechst von drei auf neun Eintraege. `OCR_DEFAULT_LANGUAGES` bleibt `("deu", "eng", "fra")`, und der Kommentar traegt den Grund an der Stelle, an der ein spaeterer Leser ihn sucht. Die Behandlung unbekannter Werte in `FINDLING_OCR_LANGUAGES` (Warnung, Rueckfall, Reihenfolge des Admins bleibt erhalten) ist unangetastet.

**THIRD-PARTY.md.** Eine eigene Tabelle fuer die sieben spaeter zugekommenen Packs, in der Form der bestehenden: Pakete, Quellpaket, Dateien im Abbild, Lizenz, Lizenztext im Abbild, Pin, Installationsgroesse je Paket und Pruefdatum. Sie steht bewusst neben der alten und nicht in ihr, weil die alte aussagt, was am 01.09.2026 im Abbild gemessen wurde.

**Nebenbefund, im selben Zug behoben:** `tesseract-ocr-fra` stand seit dem 06.09.2026 in keiner Zeile dieser Datei. Die neue Tabelle nennt es mit Datum, statt die Luecke zu schliessen, ohne sie zu erwaehnen.

**Nicht angefasst:** der OCR-Pfad selbst, die Seitendeckel, die DPI, das Zeitlimit je Seite, die Analysekette des Index.

### Task 3: das Gate und der Paket-Baumhash (`01dffa1` und `a9ee779`)

**Das Gate**, `backend/tests/test_ocr_languages.py`, drei Faelle:

1. Jede Sprache der Positivliste hat eine apt-Zeile mit Pin. Beide Richtungen: eine Sprache im Abbild, die die Liste nicht kennt, ist totes Gewicht in der Schicht, und `osd` ist die einzige erlaubte Ausnahme, weil es ein Orientierungsmodell und keine Textsprache ist.
2. Jede Sprache der Liste steht in der `--list-langs`-Pruefung des Baus.
3. Der Standard hat genau drei Eintraege und ist echte Teilmenge des Angebots. Welche drei es sind, bleibt Gegenstand von `test_ocr_french.py`: eine Aussage gehoert in eine Datei.

Die Liste wird aus `findling.config` importiert und nirgends abgeschrieben. Der rote Zustand ist **gestagt und nicht nur beschrieben**: die Leser bekommen ihre Zeilen als Liste uebergeben, und beide Faelle pruefen zusaetzlich gegen eine Kopie, aus der die zwei Zeilen einer Sprache gefallen sind.

**Der Paket-Baumhash.** `config.py` liegt unter `backend/src/findling`, also zieht `PACKAGE_TREE_HASH_TODAY` mit, **im selben Commit wie die Aenderung**: `f3f1fb13...` wird `7d0e5857...`. `PACKAGE_FILES` steht unveraendert bei 54, weil genau eine Datei ihre Bytes geaendert hat und keine kam oder ging. Die Kommentarkette hat ihren vierzehnten Eintrag mit Datum, Plan und Grund; die historischen Zwillinge (`PACKAGE_TREE_HASH`, `PHP_TREE_HASH`) sind unberuehrt.

## Verifikation

### Annahme A7, vor dem Bau gegen die Paketquelle nachgesehen

Abgefragt am 21.09.2026 bei `api.ftp-master.debian.org` (Suite `stable`) und `packages.debian.org/trixie`:

| Paket | Fassung | Komponente | Architektur | Quellpaket | Installiert |
|---|---|---|---|---|---|
| `tesseract-ocr-spa` | 1:4.1.0-2 | main | all | tesseract-lang | 2256,0 kB |
| `tesseract-ocr-ita` | 1:4.1.0-2 | main | all | tesseract-lang | 2654,0 kB |
| `tesseract-ocr-nld` | 1:4.1.0-2 | main | all | tesseract-lang | 5924,0 kB |
| `tesseract-ocr-por` | 1:4.1.0-2 | main | all | tesseract-lang | 1952,0 kB |
| `tesseract-ocr-dan` | 1:4.1.0-2 | main | all | tesseract-lang | 2535,0 kB |
| `tesseract-ocr-est` | 1:4.1.0-2 | main | all | tesseract-lang | 4369,0 kB |

Zusammen **19,7 MB installiert**, als Paketdateien rund 7,6 MB. Kein Paket aus npm, PyPI oder crates.io; dieselbe Distributionsquelle und dieselbe Signaturkette wie das Basisabbild (T-16-SC). Zum Vergleich mit derselben Abfrage: `tesseract-ocr-fra` 1119,0 kB.

### Der Abbildbau, echt gefahren

`docker.yml` Lauf **35597353780** (Push von `01dffa1`), **success**, Multi-Arch. Damit haben die sechs apt-Zeilen und ihre sechs `--list-langs`-Pruefungen zum ersten Mal wirklich gebaut, auf amd64 **und** arm64. Eine Vorher-Nachher-Zahl der Abbildgroesse nennt dieser Bericht bewusst nicht als Messung: `docker.yml` fuehrt **kein numerisches Groessen-Tor** (nachgesehen, es gibt dort keine Groessenpruefung), und eine Zahl ohne Messung waere eine Behauptung. Die belastbare Aussage ist der Zuwachs an Nutzlast: 19,7 MB unkomprimiert, rund 7,6 MB komprimiert je Architektur.

### Die Gates, lokal gruen vor jedem Commit

| Gate | vor dem Plan | nach dem Plan |
|---|---|---|
| `ruff check .` | All checks passed | All checks passed |
| `ruff format --check .` | 125 files already formatted | 126 files already formatted |
| `PYRIGHT_PYTHON_FORCE_VERSION=latest pyright` | 0 errors, 0 warnings | 0 errors, 0 warnings |
| `vulture src tests --min-confidence 80` | leer | leer |
| volle `pytest -q` | **2469 passed / 15 skipped** | **2472 passed / 15 skipped** |

Die drei zusaetzlichen Faelle sind das neue Gate. Die **Skipzahl ist unveraendert**.

### Der rote Zustand, einmal echt erzeugt

Zusaetzlich zur gestagten Mutation im Testtext ist das Gate einmal gegen eine echte Drift gefahren worden: mit einer voruebergehend in `OCR_LANGUAGE_ALLOWLIST` eingetragenen zehnten Sprache (`ces`, kein Paket im Abbild) werden Fall 1 und Fall 2 rot (`assert not {'ces'}`), Fall 3 bleibt gruen. Der Baum ist danach mit `git checkout --` auf die Datei zurueckgesetzt worden; die Probe liegt in keinem Commit.

### Die Rezeptur des Baumhashs

`python docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.py backend/src/findling "**/*.py"` antwortet `dateien: 54`, `baumhash: 7d0e5857...`. Genau das steht in der Konstanten, und `test_measurement_scripts.py` faehrt die Rezeptur bei jedem Lauf gegen den Baum.

## Was Plan 16-11 aus diesem Plan erfaehrt

**Die Antwort ist NEUN.** Die Store-Texte und die READMEs nennen ab jetzt neun OCR-Sprachen, dreisprachig und geschlossen in einem Zug. Die Stellen, Stand 21.09.2026, mit Zeilennummern zum Wiederfinden und nicht als Zusicherung:

| Datei | Zeile | Sprache des Textes | heutiger Wortlaut |
|---|---|---|---|
| `php/appinfo/info.xml` | 38 | EN | "OCR for scanned PDFs and images: German, English, French" |
| `php/appinfo/info.xml` | 59 | DE | "Texterkennung fuer gescannte PDFs und Bilder: Deutsch, Englisch, Franzoesisch" |
| `php/appinfo/info.xml` | 80 | FR | "Reconnaissance optique ... : allemand, anglais, francais" |
| `docs/store-listing.md` | 120 | EN | dieselbe Zeile, die Quelle der Store-Texte |
| `docs/store-listing.md` | 142 | DE | dieselbe Zeile |
| `docs/store-listing.md` | 164 | FR | dieselbe Zeile |
| `README.en.md` | 18 | EN | dieselbe Zeile |
| `README.md` | 18 | DE | dieselbe Zeile |
| `README.fr.md` | 19 | FR | dieselbe Zeile |
| `backend/appinfo/info.xml` | 364 | EN | "the engine and the German, English and French models are ..." |
| `backend/appinfo/info.xml` | 382 | EN | Beschreibung von `FINDLING_OCR_LANGUAGES`, zaehlt die erlaubten Werte einzeln auf ("which today are deu (German), eng (English) and fra (French)") |

Elf Stellen in fuenf Dateien. Zwei Hinweise fuer den Textblock, die aus diesem Plan folgen:

1. **Die Owner-Regel "kurze Produkttexte" gilt weiter.** Neun Sprachnamen in einer Zeile sind lang; der Textblock entscheidet, ob er sie aufzaehlt oder anders fasst. Diese SUMMARY schreibt dem Text nichts vor, sie sagt nur, dass die Zahl neun ist.
2. **Der Standard ist weiter deu+eng+fra.** Ein Text, der neun Sprachen so nennt, als waeren sie alle eingeschaltet, waere falsch. Die Zeile 382 der `backend/appinfo/info.xml` ist die einzige Stelle, an der der Unterschied zwischen "verfuegbar" und "voreingestellt" heute ueberhaupt erklaert wird, und sie muss beides nennen.

## Abweichungen vom Plan

### Auto-behoben

**1. [Regel 3 - blockierend] `test_ocr_french.py` haette die Suite rot gemacht**

- **Gefunden bei:** Task 2, vor dem ersten Commit.
- **Befund:** Die Datei behauptete `set(OCR_LANGUAGE_ALLOWLIST) == {"deu", "eng", "fra"}` und benutzte `spa` als Beispiel fuer eine Sprache, die das Abbild nicht hat. Beides wird mit diesem Plan falsch.
- **Fix:** Die Mengengleichheit weicht der Teilmengen-Behauptung `{"deu", "eng", "fra"} <= set(...)`, mit dem Kommentar, warum die ganze Menge ab jetzt woanders geprueft wird. Das Beispiel ist `frk`, dasselbe, das `test_config.py` benutzt, und weiter wahr.
- **Dateien:** `backend/tests/test_ocr_french.py`. **Commit:** `a9ee779`.

**2. [Regel 2 - fehlende Richtigkeit] `docs/ocr.md` haette einen dreiteiligen Sprachbestand beschrieben**

- **Gefunden bei:** Task 2.
- **Befund:** Die Seite beschreibt den OCR-Pfad einschliesslich der Sprachlage und haette nach diesem Plan einen Zustand beschrieben, den es nicht mehr gibt.
- **Fix:** Ein kurzer Nachtrag mit Datum, in derselben Bauform wie der Nachtrag vom 06.09.2026, mit dem ausdruecklichen Satz, dass alle gemessenen Zahlen der Seite unveraendert stehen bleiben, weil sie mit `-l deu+eng` entstanden sind.
- **Dateien:** `docs/ocr.md`. **Commit:** `a9ee779`.

**3. [Regel 2 - Lizenzlage] `tesseract-ocr-fra` fehlte in `THIRD-PARTY.md`**

- **Gefunden bei:** Task 2, beim Lesen der bestehenden Eintraege.
- **Befund:** Das Paket ist seit dem 06.09.2026 im Abbild und stand in keiner Zeile der Lizenzdatei. Ein ausgeliefertes Paket ohne Lizenzangabe ist genau der Fall, den T-16-39 fuer die neuen sechs abwehren soll.
- **Fix:** Die neue Tabelle fuehrt sieben Pakete, nicht sechs, und sagt, dass die Luecke bestand.
- **Dateien:** `THIRD-PARTY.md`. **Commit:** `a9ee779`.

### Bewusst nicht getan

- **Die Store-Texte.** Sie gehoeren geschlossen in Plan 16-11; die Liste steht oben.
- **Die Abbildgroesse als gemessene Vorher-Nachher-Zahl.** Es gibt kein Groessen-Tor in `docker.yml` und keine Messung, also auch keine Zahl, die so aussieht.

## Der Bedrohungsbezug

| Bedrohung | Wie sie abgetragen ist |
|---|---|
| T-16-36 (ein Paket fehlt, die Installation ist dafuer stumm) | sechs eigene `--list-langs`-Pruefungen im Bau, dazu ein Gate, das Liste und Dockerfile in beide Richtungen zusammenhaelt, und ein Bau, der real gelaufen ist (35597353780) |
| T-16-37 (ein Standard mit neun Sprachen macht jede Seite langsamer) | `OCR_DEFAULT_LANGUAGES` bleibt bei drei, und Fall 3 des Gates haelt die Zahl fest |
| T-16-38 (eine Paketfassung driftet vom Pin) | `=1:4.1.0-2` je Zeile, und Fall 1 des Gates prueft den Pin und nicht nur den Namen |
| T-16-39 (die Lizenzlage ist nirgends festgehalten) | sieben Eintraege in `THIRD-PARTY.md`, je mit Lizenz, Quelle und Pruefdatum |
| T-16-SC (Paketverzeichnis-Risiko) | kein Paket aus npm, PyPI oder crates.io; Existenz und Herkunft der sechs vor dem Bau gegen die Debian-Paketquelle nachgesehen |

## Selbsttest

**Dateien:**

- `backend/tests/test_ocr_languages.py` FOUND
- `backend/Dockerfile` FOUND (enthaelt `tesseract-ocr-spa=1:4.1.0-2`)
- `backend/src/findling/config.py` FOUND (`OCR_LANGUAGE_ALLOWLIST` mit neun Eintraegen)
- `THIRD-PARTY.md` FOUND (neue Tabelle mit sieben Paketen)

**Commits:** `a9ee779` FOUND, `01dffa1` FOUND.

## Self-Check: PASSED
