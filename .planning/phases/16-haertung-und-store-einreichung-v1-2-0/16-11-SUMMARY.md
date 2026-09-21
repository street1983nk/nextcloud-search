---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 11
subsystem: store-texte
tags: [hart-02, rel-02, store-listing, messzahl, e1, ocr-sprachen, owner-checkpoint]

# Dependency graph
requires:
  - phase: 16-haertung-und-store-einreichung-v1-2-0
    provides: die Antwort NEUN Sprachen aus Plan 16-10, ohne die der Textentwurf einen halben Stand haette
  - phase: 16-haertung-und-store-einreichung-v1-2-0
    provides: der Versionsbump auf 1.2.0 aus Plan 16-07, weil der Store-Text mit genau diesem Release reist
  - phase: 15-messphase-eine-box-anfahrt
    provides: Marke C der Messung vom 21.09.2026 (Rohdatei 94b), die Zahl 731,9 MB und ihre Messgroesse
provides:
  - die sechs Store-Texte der Fassung 1.2.0 im abgenommenen Wortlaut, dreisprachig, an einer Stelle
  - die neue Grundlast-Zeile der drei READMEs, dreisprachig, als Vorlage fuer Plan 16-12
  - die Fundstellenliste der Messzahl (neun Stellen) und der Sprachangabe (elf Stellen)
  - das Aenderungsprotokoll der Messzahl mit beiden Eintraegen (11.09. und 21.09.2026)
  - die Owner-Abnahme der Texte und die Entscheidung zu den Store-Bildern
affects: [16-12-textuebernahme, 16-13-launch-haertung, 16-14-abgabe]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Zahl wird nicht ersetzt, sondern abgeloest: der neue Wert kommt mit seiner Messgroesse, der alte bleibt fuer die Bedingungen gueltig, unter denen er entstand, und beides steht datiert in einem Aenderungsprotokoll"
    - "Ein Prozentwert zwischen zwei verschiedenen Messgroessen wird nicht nachgerechnet, sondern die Zeile wird ersetzt; ein Vergleich, der in die guenstige Richtung falsch ist, ist der gefaehrlichere Fehler"
    - "Verfuegbar und eingeschaltet sind zwei Angaben, und ein Store-Text nennt beide in einer Zeile, ohne die Namen aufzuzaehlen; die Namen stehen dort, wo Laenge erlaubt ist"
    - "Der Entwurf wird in der Vorlagedatei selbst gefahren und mit einem Stand-Hinweis versehen, statt in einer Planungsdatei zu leben; der Zwischenstand zwischen Vorlage und info.xml ist dadurch benannt und keine Drift"

key-files:
  created: []
  modified:
    - docs/store-listing.md

key-decisions:
  - "Owner-Abnahme im Wortlaut: \"Texte ABGENOMMEN im vorgelegten Wortlaut\" (21.09.2026, per strukturierter Rueckfrage). Die sechs Store-Texte und die drei README-Zeilen gehen ohne eine Silbe Aenderung in Plan 16-12"
  - "Owner-Entscheid zu Q-6 im Wortlaut: \"Bilder bleiben.\" Kein neuer Bilder-Plan in Welle 6; die drei Bilder vom 07.09.2026 reisen mit 1.2.0 mit. Nur die Groessentabelle in store/media/README.md zieht Plan 16-12 nach, weil sie die Groessen der abgeloesten Dateien nennt"
  - "Owner-Entscheid zur Enterprise-Zeile im Wortlaut: \"Enterprise-Zeile IN DIE SECHS TEXTE AUFNEHMEN (damit die Vorlage deckungsgleich mit den info.xml ist).\" Eingearbeitet am 21.09.2026 im Wortlaut des Nachtrags vom 11.09.2026, ohne inhaltliche Aenderung"
  - "Die RAM-Zeile nennt die Messgroesse und nicht mehr das Wort \"idle\": \"731,9 MB resident nach einem Indexlauf\". Vier Woerter, weil der Store-Text eine Faktenliste und keine Messgeschichte ist, und weil eine Zahl ohne ihre Messgroesse in einem unveraenderlichen Text die teuerste Sorte Ungenauigkeit ist"
  - "Der Alt-Neu-Vergleich der READMEs faellt ersatzlos weg, samt der 85,1 Prozent. 103,2 MB war die Grundlast im Leerlauf, 731,9 MB ist der residente Stand nach einem Indexlauf mit entladenem Modell; eine Prozentzahl zwischen zwei Messgroessen behauptete eine Verbesserung, die nie gemessen wurde (T-16-40)"
  - "Der Spitzen-Satz (52.111 Dokumente, 1.764 MB) bleibt zeichengleich, weil der v1.2-Lauf die Spitze eines Volllaufs nicht neu gemessen hat. Der Grund steht im Entwurf, damit der naechste Leser nicht dieselbe Nachziehbewegung versucht"
  - "Die neun Sprachnamen stehen nicht im Store-Text, sondern in den READMEs und in der Beschreibung von FINDLING_OCR_LANGUAGES. Die Zahl neun ist ein Bestand und keine Messzahl und bricht die Ein-Zahl-Regel des Owners deshalb nicht"

patterns-established:
  - "Eine Vorlage, die weniger fuehrt als das Ausgelieferte, ist eine stille Loeschfalle: wer sie woertlich uebernimmt, entfernt, was nur im Nachtrag stand. Vor jeder Uebernahme wird die Vorlage gegen das Ausgelieferte gezaehlt und nicht nur gelesen"

requirements-completed: []
requirements-partial: [HART-02, REL-02]

# Metrics
duration: 55 min
completed: 2026-09-21
---

# Phase 16 Plan 11: Der Textentwurf der Fassung 1.2.0 Summary

Der Store-Text von 1.2.0 nennt ab jetzt die Zahl, die ein Selfhoster auf seiner 4-GB-Box wirklich sieht (731,9 MB resident nach einem Indexlauf statt 103,2 MB im Leerlauf), und er nennt sie mit ihrer Messgroesse statt als blosse Zahl; der Owner hat die sechs Texte gesehen, bevor sie mit dem Release unveraenderlich werden.

## Die drei Owner-Entscheide, im Wortlaut

Vorgelegt wurden am 21.09.2026 per strukturierter Rueckfrage: die sechs Texte in allen drei Sprachen, die Gegenueberstellung alt gegen neu je Zeile, die Fundstellenliste, die offene Frage Q-6 und ein Befund, der beim Schreiben aufgefallen ist.

1. **Die Texte:** "Texte ABGENOMMEN im vorgelegten Wortlaut". Keine Aenderung, keine Neuvorlage.
2. **Q-6, die Store-Bilder:** "Bilder bleiben" (kein neuer Bilder-Plan; nur die Groessentabelle in `store/media/README.md` zieht 16-12 nach).
3. **Die Enterprise-Zeile:** "Enterprise-Zeile IN DIE SECHS TEXTE AUFNEHMEN (damit die Vorlage deckungsgleich mit den info.xml ist)."

Damit ist die Bedingung der Owner-Regel vom 07.09.2026 erfuellt: der Store-Text reist mit dem Release und ist danach nicht mehr editierbar, also lag er vorher vor. Die Abnahme steht mit Datum in `docs/store-listing.md` selbst, im Abschnitt "Die Abnahme" des Entwurfs, und nicht nur in dieser Datei.

## Was gebaut wurde

### Der Entwurf (`253abb5`)

**Die RAM-Zeile der sechs Store-Texte**, dreisprachig, in der Zahlenschreibweise jeder Sprache:

> Englisch: RAM: 4 GB is enough, 731.9 MB resident after an index run, under a hard 2 GB limit (measured)
>
> Deutsch: RAM: 4 GB genuegen, 731,9 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
>
> Franzoesisch: RAM : 4 Go suffisent, 731,9 Mo residents apres une indexation, sous une limite stricte de 2 Go (mesure)

Das Wort "im Leerlauf" ist verschwunden und durch die Messgroesse ersetzt, in vier Woertern und nicht in einem Satz. Je Text steht genau eine Messzahl; die 103,2 kommt in keinem der sechs Texte mehr vor, statt neben der neuen zu stehen. Die 4 GB und die harte 2-GB-Grenze bleiben, weil sie Anforderungen und keine Messzahlen sind.

**Die Sprachzeile der ersten Haelfte**, dreisprachig: "neun Sprachen verfuegbar, voreingestellt sind Deutsch, Englisch und Franzoesisch". Beides in einer Zeile, weil ein Text, der neun Sprachen nennt, als waeren sie eingeschaltet, falsch waere, und einer, der weiter drei nennt, sechs verschweigt. Die zweite Haelfte zaehlt die OCR-Sprachen nicht auf und bleibt unberuehrt.

**Die Grundlast-Zeile der drei READMEs** als Vorlage fuer Plan 16-12, dreisprachig, mit Zahl, Messgroesse, Datum, Maschine und dem Verweis auf `docs/performance.md`. Der alte Vergleich (691,8 MB auf 103,2 MB, minus 85,1 Prozent) faellt ersatzlos weg.

**Die Fundstellenliste**, zwei Tabellen: die Messzahl an neun Stellen (RAM-Zeile EN/DE/FR in beiden `info.xml`, Grundlast-Zeile in den drei READMEs) und die Sprachangabe an elf Stellen, einschliesslich des Kommentars ueber dem OCR-Block und der Beschreibung von `FINDLING_OCR_LANGUAGES` in `backend/appinfo/info.xml`. Beide Wortlaute stehen im Entwurf, damit Plan 16-12 eine Uebernahme und keine Uebersetzung wird.

**Das Aenderungsprotokoll** am Ende der Datei, mit beiden Eintraegen (11.09.2026 und 21.09.2026) und je Eintrag: Datum, Plan, was sich aendert, abgeloeste Zahl mit ihrer Messgroesse, neue Zahl mit ihrer Messgroesse, Grundlage. Dazu die drei Saetze, ohne die der zweite Eintrag falsch gelesen werden kann, darunter der wichtigste: **es ist kein Anstieg von 103,2 auf 731,9**, weil dieselbe Messung vom 21.09.2026 vor dem Indexlauf 103,9 MB gesehen hat (Marke A) und die alte Zahl damit fast genau bestaetigt.

**Der Stand-Hinweis** oben in der Datei: die sechs Texte sind seit dem 21.09.2026 Entwurf und noch nicht ausgeliefert, beide `info.xml` tragen bis zur Uebernahme weiter 103,2 MB, und ein Unterschied zwischen Vorlage und `info.xml` ist in diesem Fenster der erwartete Zwischenstand und keine Drift.

### Die Enterprise-Zeile nach der Abnahme (`5ff398d`)

Die drei Zeilen des Nachtrags vom 11.09.2026 stehen jetzt als eigener Absatz am Ende aller sechs Texte, im Wortlaut und ohne eine Silbe Aenderung:

> EN: Enterprise support and paid add-ons: request a quote at admin@infranode.dev
>
> DE: Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev
>
> FR: Support entreprise et modules payants : demande de devis a admin@infranode.dev

Der Text der Apps aendert sich dadurch nicht: er steht seit dem 11.09.2026 so in beiden `info.xml`. Was sich aendert, ist die Vorlage, und der Grund steht als datierter Nachtrag in der Datei.

## Der Befund, der diesen Plan fast zu einer Loeschung gemacht haette

Beim Zusammenstellen der Checkpoint-Vorlage ist aufgefallen, dass die sechs Texte in `docs/store-listing.md` die Enterprise-Zeile **nicht** fuehrten, obwohl sie seit dem 11.09.2026 in beiden `info.xml` steht; in der Vorlage lebte sie nur im Nachtrag darunter. Die Datei bezeichnet sich selbst als die Quelle, aus der beide `info.xml` woertlich beziehen. Eine woertliche Uebernahme in Plan 16-12 haette die Zeile also aus dem ausgelieferten Store-Text entfernt, und zwar stumm: kein Gate haelt sie fest, und der Diff haette nach einer Textpflege ausgesehen.

Der Befund ist **nicht** eigenmaechtig behoben worden, weil er eine Textentscheidung beruehrt, die der Owner am 11.09.2026 getroffen hat. Er ist als eigener Punkt an den Checkpoint gegangen und dort entschieden worden. Die Lehre steht oben als Muster: eine Vorlage, die weniger fuehrt als das Ausgelieferte, ist eine Loeschfalle, und vor einer Uebernahme wird gezaehlt und nicht nur gelesen.

## Verifikation

| Gegenstand | Ergebnis |
|---|---|
| `grep -c "731,9" docs/store-listing.md` | 15 |
| `grep -c "731.9" docs/store-listing.md` | 5 |
| 103,2 in den sechs Store-Texten | 0 (beide Schreibweisen) |
| die Messzahl in den sechs Texten | 6 Stellen, je eine Messzahl |
| Spitzen-Satz 52.111 / 1.764 MB | zeichengleich unveraendert, auch die drei Konstanten in `test_store_metadata.py` |
| Gedankenstriche, Emojis in der Datei | 0 und 0 |
| gesperrter Projektbegriff | 0 (`scan_german_document` gruen) |
| Backticks oder Tabellen in einer Beschreibung | keine |
| `uv run pytest tests/test_store_metadata.py -q` | 52 bestanden |
| volle Suite `uv run pytest -q` | **2.472 bestanden / 15 uebersprungen**, Referenz gehalten |
| `ruff check .` / `ruff format --check .` | All checks passed / 126 files already formatted |
| `vulture src tests --min-confidence 80` | leer |

Nicht angefasst, wie vom Plan verlangt: beide `info.xml`, die drei READMEs, `store/media/`, `backend/tests/test_store_metadata.py`. Nicht gepusht, kein Tag.

## Abweichungen vom Plan

### Auf Owner-Entscheid ergaenzt

**1. Die Enterprise-Zeile in den sechs Texten**

- **Gefunden bei:** Task 1, beim Zusammenstellen der Checkpoint-Vorlage.
- **Befund:** Die Vorlage fuehrte drei Zeilen weniger als beide `info.xml`; eine woertliche Uebernahme haette sie geloescht.
- **Behandlung:** nicht selbst entschieden, sondern dem Owner am Checkpoint vorgelegt und dort entschieden ("in die sechs Texte aufnehmen").
- **Dateien:** `docs/store-listing.md`. **Commit:** `5ff398d`.

### Bewusst nicht getan

- **Der Messsatz auf 52.137 Dokumente nachgezogen.** Die Spitze eines Volllaufs ist in v1.2 nicht neu gemessen; zwei Laeufe in einem Satz waeren eine Messung, die es nicht gibt.
- **Die 103,2 MB neben die neue Zahl gestellt.** Das waere eine zweite Messzahl im Store-Text und ein Bruch der Owner-Regel vom 07.09.2026.
- **Neue Store-Bilder.** Owner-Entscheid "Bilder bleiben".

## Der Bedrohungsbezug

| Bedrohung | Wie sie abgetragen ist |
|---|---|
| T-16-40 (eine Prozentzahl zwischen zwei Messgroessen behauptet eine Verbesserung, die es nicht gibt) | der Vergleich faellt ersatzlos weg; die neue Zahl steht mit ihrer Messgroesse da, und der alte Wert bleibt in `docs/performance.md` fuer seine Bedingungen gueltig |
| T-16-41 (eine ersetzte Zahl ohne Nachtrag) | das Aenderungsprotokoll mit beiden Eintraegen, je mit Messgroesse, Rohdatei und Grundlage |
| T-16-42 (ein Text laeuft in einer Sprache oder einer Haelfte auseinander) | alle sechs Texte stehen nebeneinander in einer Datei; der Befund zur Enterprise-Zeile ist genau dieser Fall und ist geschlossen |
| T-16-43 (ein leeres Element beendet den Upload) | kein Element angefasst; `test_store_metadata.py` gruen |
| T-16-SC (Paketverzeichnis-Risiko) | keine Abhaengigkeit, kein Installationsbefehl in diesem Plan |

## Was Plan 16-12 aus diesem Plan erhaelt

1. Die sechs Texte im abgenommenen Wortlaut, einschliesslich der Enterprise-Zeile: **woertliche Uebernahme in beide `info.xml`**, keine Neuformulierung.
2. Die drei README-Zeilen im abgenommenen Wortlaut, je in der Zahlenschreibweise der Sprache.
3. Die zwei englischen Wortlaute fuer `backend/appinfo/info.xml` (Kommentar ueber dem OCR-Block, Beschreibung von `FINDLING_OCR_LANGUAGES` mit den neun Codes).
4. Den Auftrag, die Groessentabelle in `store/media/README.md` nachzuziehen (Owner-Entscheid "Bilder bleiben", die Tabelle nennt die Groessen der abgeloesten Dateien).
5. Den Hinweis, dass der Spitzen-Satz und seine drei Konstanten nicht angefasst werden.
6. Das Messzahl-Gate aus Erfolgskriterium 4 haelt die 731,9 an drei Stellen (README.en.md und beide `info.xml`); es wird in 16-12 gebaut und nicht hier.

## Selbsttest

**Dateien:**

- `docs/store-listing.md` FOUND (enthaelt 731,9 an 15 Stellen, 731.9 an 5)
- `.planning/phases/16-haertung-und-store-einreichung-v1-2-0/16-11-SUMMARY.md` FOUND

**Commits:** `253abb5` FOUND, `2609d4d` FOUND, `5ff398d` FOUND.

## Self-Check: PASSED
