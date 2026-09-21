---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 12
subsystem: store-texte
tags: [hart-02, rel-02, store-listing, messzahl, e1, ocr-sprachen, gates, store-media]

# Dependency graph
requires:
  - phase: 16-haertung-und-store-einreichung-v1-2-0
    provides: die vom Owner abgenommenen sechs Store-Texte und drei README-Zeilen aus Plan 16-11, ohne die diese Uebernahme eine Neuformulierung waere
  - phase: 16-haertung-und-store-einreichung-v1-2-0
    provides: die neun OCR-Sprachen im Abbild aus Plan 16-10, ohne die die neue Sprachzeile eine unbelegte Zusage waere
  - phase: 15-messphase-eine-box-anfahrt
    provides: Marke C der Messung vom 21.09.2026 (Rohdatei 94b), die Zahl 731,9 MB und ihre Messgroesse
provides:
  - die ausgelieferten Texte der Fassung 1.2.0 in beiden info.xml und den drei READMEs, dreisprachig
  - das Messzahl-Gate ueber README.en.md und beide info.xml, mit einem Mutationsfall je Stelle
  - das Connector-Gate mit Anzahlpruefung in drei Sprachen und beiden Haelften (HART-02)
  - die Kurztext-Regel als Maschine: genau eine Messzahl je Store-Beschreibung
  - die geschlossene Wiedervorlage der Store-Bilder vom 07.09.2026
affects: [16-13-launch-haertung, 16-14-abgabe]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Zahl, die an mehreren Stellen steht, wird einmal als Konstante festgelegt und je Sprache abgeleitet; zwei Schreibweisen derselben Messung sind eine Messung, und ein zweites Literal waere genau die Drift, gegen die das Gate gebaut wird"
    - "Ein Gate ueber eine Textzusage prueft die ANZAHL und nicht die Anwesenheit, wenn die Regel eine Anzahl nennt; ein zweiter Satz verletzt 'genau einer' ebenso wie ein fehlender"
    - "Die Mutationsprobe wird aus der echten Datei gestagt und nicht aus einem eigenen Muster gebaut: ein selbstgeschriebenes Muster beweist nur, dass der Scanner selbstgeschriebene Muster liest"
    - "Der Unterschied zwischen Anforderung und Messzahl wird an der Masseinheit mechanisiert (MB und Mo zaehlen, GB und Go nicht), statt als Satz in einer Dokumentationsdatei zu leben"

key-files:
  created: []
  modified:
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - README.md
    - README.en.md
    - README.fr.md
    - backend/tests/test_store_metadata.py
    - store/media/README.md
    - .planning/BACKLOG.md

key-decisions:
  - "Die Uebernahme ist eine Kopie und keine Abschrift: die Wortlaute sind maschinell aus docs/store-listing.md gelesen und maschinell eingesetzt worden, und danach hat ein Vergleich Zeichen fuer Zeichen 17 Stellen gegen die Quelle gehalten. Ein abgetippter Store-Text ist ein Text, der beim Tippen leise abweicht, und er ist nach dem Release nicht mehr editierbar"
  - "Die Messzahl steht einmal als Konstante RESIDENT_FIGURE im Gate, und die drei Schreibweisen (731.9 MB, 731,9 MB, 731,9 Mo) sind abgeleitet. Ein Literal je Sprache waere ein zweiter Ort fuer dieselbe Messung"
  - "Das Connector-Gate zaehlt und prueft nicht auf Anwesenheit. Die Regeltabelle in docs/store-listing.md sagt genau EIN Querverweis, und ein Gate auf Anwesenheit waere gegen die Haelfte der Regel blind"
  - "Die Kurztext-Regel ist als Masseinheit gefasst: MB und Mo sind Messzahlen, GB und Go sind Anforderungen. Der Unterschied steht im Docstring und wird von einem eigenen Fall belegt, statt nur behauptet zu werden"
  - "Die Groessentabelle der Store-Bilder war bereits richtig; falsch war die Live-Bestaetigung. Nachgezogen wurde deshalb die Bestaetigungstabelle, und der Vermerk vom 07.09.2026 bleibt datiert stehen, damit ablesbar bleibt, dass die Frage vierzehn Tage offen war"

patterns-established:
  - "Vor dem Nachziehen einer Tabelle wird nachgesehen, welche der beiden Tabellen in derselben Datei wirklich falsch ist; ein Auftrag, der 'die Tabelle' sagt, meint nicht zwingend die, die oben steht"

requirements-completed: []
requirements-partial: [HART-02, REL-02]

# Metrics
duration: 40 min
completed: 2026-09-21
---

# Phase 16 Plan 12: Textuebernahme, Messzahl-Gate und Connector-Gate Summary

Die abgenommenen Texte der Fassung 1.2.0 stehen ab jetzt dort, wo sie mit dem Release nach aussen gehen, und beide Zusagen, die sie tragen, haengen zum ersten Mal an einem Gate, das rot werden kann: die Messzahl 731,9 MB an drei Stellen im Gleichschritt und der Connector-Satz dreisprachig in beiden Haelften, genau einmal.

## Was gebaut wurde

### Die Uebernahme (`3422979`)

Fuenf Dateien, zwanzig Textstellen, und keine davon ist abgetippt. Die Wortlaute sind mit einem Skript aus `docs/store-listing.md` gelesen und mit demselben Skript eingesetzt worden; der Grund steht in den Entscheiden oben. Danach hat ein zweiter Lauf 17 Stellen Zeichen fuer Zeichen gegen die Quelle gehalten, je Stelle genau ein Treffer.

**Die Messzahl, neun Stellen (Entscheid E1).** Die RAM-Zeile beider Haelften nennt dreisprachig **731,9 MB resident nach einem Indexlauf** statt 103,2 MB im Leerlauf, und die Grundlast-Zeile der drei READMEs nennt dieselbe Zahl mit Messgroesse, Datum, Maschine und Abbild. Der Alt-Neu-Vergleich der READMEs ist ersatzlos weggefallen, samt der 85,1 Prozent: er verglich zwei verschiedene Messgroessen und behauptete damit eine Verbesserung, die nie gemessen wurde (T-16-40).

**Die Sprachangabe, elf Stellen.** Die drei Store-Texte der ersten Haelfte sagen jetzt "neun Sprachen verfuegbar, voreingestellt sind Deutsch, Englisch und Franzoesisch"; die drei READMEs duerfen die Namen nennen und nennen sie; die zwei englischen Stellen der zweiten Haelfte, der Kommentar ueber dem OCR-Block und die Beschreibung von `FINDLING_OCR_LANGUAGES`, fuehren jetzt neun Sprachcodes statt drei. Die drei Fassungen in `docs/store-listing.md` standen seit 16-11.

Unberuehrt geblieben, wie der Plan es verlangt: der Spitzen-Satz mit 52.111 Dokumenten und 1.764 MB in allen drei READMEs (und damit `MEASURED_SENTENCE`, `MEASURED_SENTENCE_DE` und `MEASURED_SENTENCE_FR`), der Datenschutzabsatz aus D-12, der Connector-Satz, die Enterprise-Zeile, die Versionsangaben aus 16-07, das Versionsfenster und alle `screenshot`-Elemente.

### Die zwei Gates (`8ce701a`)

**Gate 1, die Messzahl im Gleichschritt.** Die Zahl steht genau einmal als `RESIDENT_FIGURE`, mit Messgroesse, Datum, Maschine, Rohdatei und Entscheid E1 im Kommentar; `RESIDENT_SPELLING` leitet die drei Schreibweisen ab. Drei Faelle halten sie gegen `README.en.md`, `php/appinfo/info.xml` und `backend/appinfo/info.xml`, und die beiden `info.xml` werden je Sprache geprueft, also sieben Texte insgesamt. Je Stelle beweist ein Mutationsfall, dass der Fall rot werden kann: die echte Datei mit 741,9 statt 731,9 liefert einen Befund, und bei den beiden `info.xml` sind es drei Befunde, einer je Sprache. Ein vierter Fall haelt die Kurztext-Regel des Owners, genau eine Messzahl je Beschreibung, gemessen an der Masseinheit; warum die 4 GB und die harte 2-GB-Grenze nicht mitzaehlen, steht im Docstring und wird von einem eigenen Fall belegt.

**Gate 2, der Connector-Satz (HART-02).** Drei Konstanten (EN, DE, FR), ein Fall ueber beide Haelften, und geprueft wird die **Anzahl**: sie muss eins sein. Der Selbsttest fuehrt beide Richtungen vor, eine Beschreibung ohne den Satz und eine mit zwei. Beide Gates sagen im Docstring, warum es sie gibt: der Satz steht seit Commit `1c737e6` (Release 1.0.3) ausgeliefert im Store, war im Tag `v1.1.0` dabei und war bis heute von keiner Pruefung gehalten.

Die Datei waechst von 52 auf **67 Faelle**, also fuenfzehn mehr, verlangt waren mindestens acht.

### Die Bilder und der Backlog (`aa58fdc`)

**Die Groessentabelle war schon richtig.** Sie nennt seit dem 07.09.2026 abends die Groessen der Dateien, die heute im Verzeichnis liegen, und `scan_media_sizes` haelt sie dort fest. Falsch war die **Live-Bestaetigung** darunter: sie fuehrte die Groessen der abgeloesten Dateien und zweimal den Eintrag "siehe Vermerk unten".

Die Abfrage ist je Datei wiederholt worden, gegen `main` bei Stand `1f6f85c`, am 21.09.2026 um 12:56 UTC:

| Bild | Status | Inhaltstyp | Groesse laut Antwort | Groesse der Datei | Pruefsumme |
|---|---|---|---|---|---|
| `header.png` | 200 | `image/png` | 327635 | 327635 | `22cc597d...` |
| `screenshot-admin.png` | 200 | `image/png` | 159786 | 159786 | `1258e50a...` |
| `screenshot-search.png` | 200 | `image/png` | 277061 | 277061 | `568b0748...` |

Alle drei Antworten beginnen mit der PNG-Signatur, die Masse aus dem `IHDR`-Block stimmen mit den dokumentierten (1440 x 810, 1440 x 1100, 1440 x 700), und die heruntergeladenen Bytes sind byteweise dieselben wie die Dateien im Verzeichnis. Damit sind es genau die drei Pruefsummen, gegen die der Vermerk vom 07.09.2026 die Wiederholung angekuendigt hatte: die Wiedervorlage ist nach vierzehn Tagen geschlossen. Der alte Vermerk steht datiert darunter und ist nicht geloescht, dazu der Owner-Entscheid zu Q-6 im Wortlaut ("Bilder bleiben") samt dem, was damit bewusst in Kauf genommen ist.

**BL-F01** in `.planning/BACKLOG.md` ist fortgeschrieben: der Schluss-Satz, der dort mit Stand 07.09.2026 als "OFFEN NUR NOCH" gefuehrt war, ist seit `1c737e6` ausgeliefert und war im Tag `v1.1.0` dabei; seit diesem Plan haelt ihn ein Gate, das die Anzahl prueft. Der alte Absatz ist nicht geloescht, sondern als ueberholt datiert.

**BL-F02 brauchte nichts.** Der Eintrag ist am 21.09.2026 von Plan 16-10 fortgeschrieben worden, und zwar nicht mit "Folgerelease", sondern mit dem Owner-Wort "Mitfahren": Baustein 1 faehrt in v1.2.0 mit. Die Bedingung des Plans ("Hat Plan 16-10 mit 'folgerelease' geendet") ist damit nicht eingetreten.

## Der Zeichenvergleich, Stelle fuer Stelle

Verlangt war ein Vergleich Zeichen fuer Zeichen zwischen der Quelle und den Zieldateien, und hier ist sein Ergebnis. Je Zeile: ein Treffer, keine Abweichung.

| Datei | Stelle | Ergebnis |
|---|---|---|
| `php/appinfo/info.xml` | Sprachzeile EN, DE, FR | 3x gleich, je 1 Treffer |
| `php/appinfo/info.xml` | RAM-Zeile EN, DE, FR | 3x gleich, je 1 Treffer |
| `backend/appinfo/info.xml` | RAM-Zeile EN, DE, FR | 3x gleich, je 1 Treffer |
| `backend/appinfo/info.xml` | Kommentar ueber dem OCR-Block | gleich, 1 Treffer |
| `backend/appinfo/info.xml` | Beschreibung `FINDLING_OCR_LANGUAGES` | gleich, 1 Treffer |
| `README.en.md` | Grundlast-Zeile, Sprachzeile | 2x gleich, je 1 Treffer |
| `README.md` | Grundlast-Zeile, Sprachzeile | 2x gleich, je 1 Treffer |
| `README.fr.md` | Grundlast-Zeile, Sprachzeile | 2x gleich, je 1 Treffer |

Die drei README-Zeilen sind umbruchbereinigt verglichen worden (eine README bricht Zeilen, eine Vorlage nicht) und mit `docs/performance.md` als Markdown-Link statt als blossem Pfad, genau wie die abgeloeste Fassung es schon hielt.

## Verifikation

| Gegenstand | Ergebnis |
|---|---|
| die Messzahl in `php/appinfo/info.xml` | 3 (EN, DE, FR) |
| die Messzahl in `backend/appinfo/info.xml` | 3 (EN, DE, FR) |
| die Messzahl in den drei READMEs | je 1, zusammen 9 Stellen |
| 103,2 / 103.2 / 691,8 / 85,1 in den fuenf Dateien | 0, in jeder Schreibweise |
| `uv run pytest tests/test_store_metadata.py -q` | **67 bestanden** (vorher 52) |
| Live-Abfrage der drei Bildadressen | 3x 200, `image/png`, Groesse und Pruefsumme gleich der Datei |
| volle Suite `uv run pytest -q` | **2.487 bestanden / 15 uebersprungen** (2.472 + 15 neue Faelle, Skipzahl unveraendert) |
| `ruff check .` / `ruff format --check .` | All checks passed / 126 files already formatted |
| `PYRIGHT_PYTHON_FORCE_VERSION=latest pyright` | 0 errors, 0 warnings, 0 informations |
| `vulture src tests --min-confidence 80` | leer |
| Gedankenstriche, Emojis, gesperrter Begriff im neuen Code | 0, 0 und 0 |

**Die Tree-Hashes sind nachgesehen und nicht nachzuziehen.** Die Owner-Regel verlangt, die Zugehoerigkeit im Waechter nachzusehen: `test_measurement_scripts.py` fuehrt das Rezept mit `**/*.php` ueber `php/` und mit `**/*.py` ueber `backend/src/findling`. Eine `appinfo/info.xml` liegt in keinem der beiden Baeume, und der Kommentar ueber `PHP_FILES_TODAY` sagt genau das ueber den Versionsbump aus 16-07. `PHP_TREE_HASH_TODAY` und `PACKAGE_TREE_HASH_TODAY` bleiben deshalb unveraendert, und die beiden Faelle, die sie halten, sind in jedem der drei Suitelaeufe gruen geblieben.

## Abweichungen vom Plan

Keine. Die drei Aufgaben sind ausgefuehrt worden, wie sie geschrieben stehen; keine Regel 1 bis 4 ist gezogen worden.

Zwei Punkte, an denen der Plan eine Bedingung stellte und die Bedingung nicht eingetreten ist, damit der naechste Leser nicht nach der fehlenden Zeile sucht:

1. **Kein Zusatz zu neuen Bildern in `store/media/README.md`.** Die Zeile war an "Hat der Owner in 16-11 'bilder neu' entschieden" gebunden; der Entscheid lautet "Bilder bleiben". Vermerkt ist er trotzdem, mit dem, was er in Kauf nimmt.
2. **Keine fortgeschriebene Zeile zu BL-F02.** Sie war an "Hat Plan 16-10 mit 'folgerelease' geendet" gebunden; er endete mit "Mitfahren", und der Eintrag traegt seinen Stand vom 21.09.2026 bereits.

## Der Befund, den der Auftrag nicht vorhergesehen hat

Der Plan sagt, die Groessentabelle in `store/media/README.md` nenne die Groessen der abgeloesten Dateien. Nachgesehen stimmte das nicht: die Tabelle oben ist seit dem 07.09.2026 richtig, weil `scan_media_readme` sie gegen das Verzeichnis haelt und beim Austausch eines Bildes rot wird. Was die abgeloesten Groessen fuehrte, war die **Live-Bestaetigung** darunter, die kein Gate haelt, weil sie bewusst ohne Netz nicht pruefbar ist. Nachgezogen wurde deshalb die richtige der beiden Tabellen. Die Lehre steht oben als Muster.

## Der Bedrohungsbezug

| Bedrohung | Wie sie abgetragen ist |
|---|---|
| T-16-44 (eine Zahl in einer README laeuft von der Zahl in einer info.xml weg) | eine Konstante, drei Stellen, sieben gepruefte Texte, ein Mutationsfall je Stelle |
| T-16-45 (der Connector-Satz verschwindet in einer Sprache unbemerkt) | Gate je Haelfte und Sprache mit Anzahlpruefung, Selbsttest fuer null und fuer zwei |
| T-16-46 (eine Bildadresse zeigt auf nichts) | das bestehende Gate prueft ohne Netz; die Live-Bestaetigung ist je Datei wiederholt, mit Statuscode, Inhaltstyp, Groesse, Masse und Pruefsumme |
| T-16-47 (ein Bild ueber 2 MiB beendet die Einreichung) | `judge_image_size` gruen ueber alle drei Dateien, die Groessentabelle gegen das Verzeichnis gehalten |
| T-16-SC (Paketverzeichnis-Risiko) | keine Abhaengigkeit, kein Installationsbefehl in diesem Plan |

## Was die naechsten Plaene aus diesem Plan erhalten

1. **Erfolgskriterium 4 ist erfuellt und haengt an einem Gate**, das rot werden kann, und das ist mit drei Mutationsfaellen nachgewiesen.
2. **Erfolgskriterium 2 ist materiell und maschinell erfuellt**, soweit es den Connector-Satz betrifft; das Abhaken von HART-02 selbst bleibt bei 16-13/16-14, weil Erfolgskriterium 2 zusaetzlich die vier Katalog-Gates und die Typografie nennt (beide gruen, aber Teil der Abnahme).
3. **Nicht gepusht, kein Tag.** Der naechste Push stoesst die CI-Strecke an; was dabei zu erwarten ist, steht unten.
4. **Die Store-Texte sind ab jetzt das, was mit dem Release nach aussen geht.** Wer sie noch einmal anfasst, braucht eine neue Owner-Abnahme.

## Was der naechste Push in CI anstoesst

Drei der geaenderten Dateien liegen in Pfaden, die Workflows beobachten, und eine davon ist hier lokal nicht fahrbar gewesen:

- **`php.yml`** (PHP-Lint, PHPUnit, Store-Validierung). `php/appinfo/info.xml` ist geaendert, und dieser Ast ist auf dieser Maschine **nicht gelaufen**, weil weder PHP noch Composer vorhanden sind (Environment Availability der 16-RESEARCH). Worauf zu achten ist: der Schritt, der die `info.xml` durch `pre-info.xslt` schickt und gegen `info.xsd` validiert. Die Aenderung betrifft ausschliesslich Text innerhalb bestehender `CDATA`-Bloecke, kein Element, kein Attribut und keine Reihenfolge; die Laengengrenze von 128 Zeichen gilt nur fuer `name` und `summary`, und beide sind unberuehrt. Ein Fehlschlag waere deshalb ueberraschend, aber er waere genau hier zu sehen.
- **`python.yml`** (ruff, ruff format, pyright, vulture, pytest). Alle fuenf Gates sind lokal gefahren und gruen, pyright mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, also mit derselben Fassung wie CI.
- **`docker.yml`** wird von diesen Aenderungen **nicht** angestossen: `backend/appinfo/info.xml` ist keine Quelle des Abbilds, und `<image-tag>` und `<version>` sind unveraendert. Der Gleichschritt-Vergleich der drei Versionsstellen gegen den Git-Tag laeuft erst beim Tag von 16-14.

Dazu ein Hinweis fuer 16-14: die `screenshot`-Adressen zeigen auf `main`, und die Live-Bestaetigung oben ist gegen Stand `1f6f85c` gefahren. Die drei Bilddateien sind in diesem Plan nicht angefasst worden, ein Push aendert an den Antworten also nichts.

## Selbsttest

**Dateien:**

- `php/appinfo/info.xml` FOUND (Messzahl an 3 Stellen, 103,2 an 0)
- `backend/appinfo/info.xml` FOUND (Messzahl an 3 Stellen, neun Sprachcodes)
- `README.md`, `README.en.md`, `README.fr.md` FOUND (je 1 Messzahl, je 1 Sprachzeile)
- `backend/tests/test_store_metadata.py` FOUND (67 Faelle, enthaelt `731`)
- `store/media/README.md` FOUND (Live-Bestaetigung vom 21.09.2026, alter Vermerk datiert darunter)
- `.planning/BACKLOG.md` FOUND (BL-F01 fortgeschrieben)
- `.planning/phases/16-haertung-und-store-einreichung-v1-2-0/16-12-SUMMARY.md` FOUND

**Commits:** `3422979` FOUND, `8ce701a` FOUND, `aa58fdc` FOUND.

## Self-Check: PASSED
