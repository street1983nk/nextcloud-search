# Niederländische Komposita, Rezept B 4-14, gemessen am 25.09.2026

Dieser Bericht ist die Messgrundlage der Phase 21 für den niederländischen
Kompositasplitter. Jede spätere Aussage der Phase über niederländische Token soll
eine Zeile in `rohdaten/tokens-rezept-b.tsv` oder `rohdaten/kennzahlen.txt`
zitieren können, und die Fixture der Python-Suite entsteht reproduzierbar aus der
echten Liste.

Gemessen wurde mit `scripts/dev/measure_compounds_nl.sh`, das
`scripts/dev/compound_probe_nl.py` in einem Wegwerf-Container fährt. Die Sonde
baut keine eigene Filterkette: sie ruft `load_constituents_nl` aus
`findling.index.wordlist_nl` und `dutch_analyzer`, `snowball_analyzer`,
`cached_german_analyzer`, `cached_dutch_analyzer` aus `findling.index.analyzer`.
Der Bericht misst also das ausgelieferte Paket und nicht sich selbst.

---

## 1. Umgebung

| Was | Wert |
|---|---|
| Datum der Läufe | 2026-09-25 |
| Abbild | `python:3.13-slim-trixie`, das Basisabbild der ExApp |
| Niederländische Wortliste | Debian-Paket `wdutch=1:2.20.19+1-3`, hart gepinnt, derselbe Pin wie in `backend/Dockerfile` |
| Deutsche Wortliste (nur RAM-Modus) | `wngerman=20161207-15` |
| Suchbibliothek | `tantivy==0.26.2`, der Pin aus `backend/pyproject.toml` (das deutsche Messskript nennt noch 0.26.0) |
| Quelle | `/usr/share/dict/dutch`, **413288** Zeilen |
| Liste nach Rezept B 4-14 | **316740** Einträge |
| Digest der gefilterten Liste | `ee7f3b8380c752835692db8fbf1350786955d4fca13e94506812a23eece107a2` |
| Fälle | 28 Komposita mit Glied, 33 Wächter (`backend/tests/fixtures/compound_cases_nl.txt`) |
| Kettenfälle | 13 Formfamilien aus `backend/tests/fixtures/chain_cases_nl.txt` |

Alle Rezeptzahlen der Research (21-RESEARCH, Abschnitt "Die Rezeptmessung")
sind im Repo reproduziert: 413288 Quellzeilen, 316740 Einträge, Digest-Anfang
`ee7f3b8380c75283`, 21 von 28 Komposita über ihr Glied, 32 von 33 Wächter
einteilig, 0 von 28 ohne Splitter.

## 2. Die Rezepte

Die Research hat elf Varianten gemessen. Auszug, vollständig in
21-RESEARCH und im Modul-Docstring von `backend/src/findling/index/wordlist_nl.py`:

| Rezept | Fenster | Liste | Split-Position | Einträge | Komposita über Glied | Wächter einteilig |
|---|---|---|---|---|---|---|
| ohne Splitter (heutige nl-Kette) | n/a | n/a | n/a | n/a | 0/28 | n/a |
| A 4-14 | 4-14 | roh | vor Fold | 317320 | 20/28 | 32/33 |
| A 4-12 | 4-12 | roh | vor Fold | 257766 | 24/28 | 31/33 |
| **B 4-14** | 4-14 | gefaltet | hinter Fold | **316740** | **21/28** | **32/33** |
| B 4-12 | 4-12 | gefaltet | hinter Fold | 257194 | 25/28 | 31/33 |
| B 4-16 | 4-16 | gefaltet | hinter Fold | 352737 | 16/28 | 33/33 |

Rezept B 4-14 ist per Owner-Entscheid vom 25.09.2026 gewählt (D-03). Die
Fenster 4-12 und 4-13 finden mehr, zerlegen aber `onderhandelingen` in
`onderhandel, ing`: ein Junk-Term im Index, dasselbe Muster, das das deutsche
Rezept D verworfen hat.

## 3. Fall für Fall

Aus `rohdaten/tokens-rezept-b.tsv`. "Eintrag" heißt: die gefaltete Form des
Kompositums steht selbst in der Liste, und ein Eintrag wird nie zerlegt.

| Kompositum | Glied | Token ohne Splitter | Token Rezept B | Eintrag | Treffer |
|---|---|---|---|---|---|
| gemeentebelastingen | belasting | gemeentebelast | gemeent, belast | 0 | ja |
| gemeentebelasting | belasting | gemeentebelast | gemeent, belast | 0 | ja |
| inkomstenbelasting | belasting | inkomstenbelast | inkomst, belast | 0 | ja |
| waterschapsbelasting | belasting | waterschapsbelast | waterschap, belast | 0 | ja |
| belastingaangifte | aangifte | belastingaangift | belast, aangift | 0 | ja |
| huurovereenkomst | overeenkomst | huurovereenkomst | hur, overeenkomst | 0 | ja |
| arbeidsovereenkomst | overeenkomst | arbeidsovereenkomst | arbeid, overeenkomst | 0 | ja |
| koopovereenkomst | overeenkomst | koopovereenkomst | kop, overeenkomst | 0 | ja |
| bestemmingsplan | bestemming | bestemmingsplan | bestemm, plan | 0 | ja |
| omgevingsvergunning | vergunning | omgevingsvergunn | omgev, vergunn | 0 | ja |
| parkeervergunning | vergunning | parkeervergunn | parker, vergunn | 0 | ja |
| zorgverzekering | verzekering | zorgverzeker | zorg, verzeker | 0 | ja |
| ziektekostenverzekering | verzekering | ziektekostenverzeker | ziektekost, verzeker | 0 | ja |
| kinderopvangtoeslag | toeslag | kinderopvangtoeslag | kinderopvang, toeslag | 0 | ja |
| gemeenteraadsvergadering | vergadering | gemeenteraadsvergader | gemeenterad, vergader | 0 | ja |
| begrotingswijziging | wijziging | begrotingswijz | begrot, wijzig | 0 | ja |
| afvalstoffenheffing | heffing | afvalstoffenheff | afvalstoff, heffing | 0 | ja |
| subsidieaanvraag | aanvraag | subsidieaanvrag | subsidie, aanvrag | 0 | ja |
| vergaderverslag | verslag | vergaderverslag | vergader, verslag | 0 | ja |
| coördinatiecentrum | centrum | coordinatiecentrum | coordinatie, centrum | 0 | ja |
| coordinatiecentrum | centrum | coordinatiecentrum | coordinatie, centrum | 0 | ja |
| onroerendezaakbelasting | belasting | onroerendezaakbelast | onroer, zaakbelast | 0 | nein |
| bouwvergunning | vergunning | bouwvergunn | bouwvergunn | 1 | nein |
| huurtoeslag | toeslag | huurtoeslag | huurtoeslag | 1 | nein |
| verkeersboete | boete | verkeersboet | verkeersboet | 1 | nein |
| jaarrekening | rekening | jaarreken | jaarreken | 1 | nein |
| factuurnummer | nummer | factuurnummer | factuurnummer | 1 | nein |
| opzegtermijn | termijn | opzegtermijn | opzegtermijn | 1 | nein |

Die flache Schreibung `coordinatiecentrum` eines Nutzers, der das Trema nicht
tippt, zerfällt genauso wie `coördinatiecentrum`. Das ist der Grund für Rezept B:
unter Rezept A steht der Splitter vor dem Fold und die flache Form bleibt ganz.

### 3.1 Die sieben benannten Grenzen

- `onroerendezaakbelasting` wird `onroer, zaakbelast`: `zaakbelasting` ist
  selbst ein Eintrag, der längere Treffer gewinnt, und `belast` entsteht nie.
- `bouwvergunning`, `huurtoeslag`, `verkeersboete`, `jaarrekening`,
  `factuurnummer`, `opzegtermijn` stehen selbst in der Liste und bleiben
  deshalb ein Token.

Das ist dieselbe Eigenschaft, die beim deutschen Rezept A gemessen wurde: ein
Eintrag wird nie zerlegt. Die sechs kurzen Alltagskomposita sind nur über sich
selbst auffindbar, genau wie ohne Splitter.

### 3.2 Die Wächter

32 von 33 Wächtern bleiben ein Token. Der eine mehrteilige ist
`belastingplichtige` (`belast, plichtig`), und der ist ein echtes Kompositum
aus `belasting` und `plichtig`, also keine Fehlzerlegung.

`openbaarheid` wird `open`. Das ist der Snowball-Stemmer und nicht der
Splitter: die Kette ohne Splitter liefert dasselbe Token (Spalte
`tokens_without_splitter`).

### 3.3 Ohne Splitter

Die heutige niederländische Kette (`snowball_analyzer("dutch")`, Phase 17)
findet **0 von 28** Komposita über ihr Glied. Jedes Kompositum ist dort genau
ein Token, zum Beispiel `gemeentebelast` für `gemeentebelastingen`, und die
Frage `belasting` wird `belast`.

### 3.4 Die Kettenfälle aus Phase 17

Alle Wörter aus `chain_cases_nl.txt` wurden durch beide Ketten geschickt.
Ergebnis: `chain_cases_differing=0`. Die Splitterkette unterscheidet sich auf
den 13 Formfamilien der Phase 17 in keinem Token von der Snowball-Kette. Die
Phase-17-Zahl `"nl": (57, 81)` misst die Snowball-Kette und bleibt, und sie
gilt für die Splitterkette auf diesen Familien unverändert.

## 4. RAM des zweiten Automaten

Gemessen vor der Verdrahtung, produktnah in der Reihenfolge des laufenden
Containers: deutsche Liste gehalten und deutscher Automat über
`cached_german_analyzer` gebaut, Messpunkt; dann niederländische Liste gelesen,
`cached_dutch_analyzer` gebaut, Liste freigegeben, `gc.collect()`, Messpunkt.
`VmRSS` aus `/proc/self/status`, jeder Lauf in einem frischen Container,
Megabyte dezimal (10^6 Byte). amd64, Docker Desktop.

| Lauf | Grundlast (de-Liste und de-Automat) | nl dauerhaft zusätzlich, Liste freigegeben | Lesen, Filtern, Bauen |
|---|---|---|---|
| Messung 1, Lauf 1 | 92,03 MB | 24,22 MB | 0,770 s |
| Messung 1, Lauf 2 | 90,60 MB | 25,25 MB | 0,744 s |
| Messung 1, Lauf 3 | 91,14 MB | 25,14 MB | 0,751 s |
| Messung 2 (`--against`), Lauf 1 | 91,96 MB | 24,22 MB | 0,753 s |
| Messung 2 (`--against`), Lauf 2 | 90,58 MB | 25,25 MB | 0,780 s |
| Messung 2 (`--against`), Lauf 3 | 91,18 MB | 25,19 MB | 0,775 s |
| Research-Sonde (Scratchpad) | 94,2 bis 95,8 MB | 17,53 bis 17,66 MB | 0,73 bis 0,80 s |

`rohdaten/ram.txt` enthält die drei Läufe der zweiten Messung.

### 4.1 Befund: 24,2 bis 25,3 MB statt 17,5 bis 17,7 MB

Die Repo-Sonde liegt reproduzierbar rund 7 MB über der Research. Das ist mehr
als Messrauschen (die Läufe streuen um 1 MB) und wird hier als Befund geführt,
nicht nachgebessert. Die Rezeptzahlen sind davon nicht berührt.

Diagnose am selben Tag, im selben Abbild, zwei bis drei Läufe je Variante, Werkzeug nur
im Scratchpad:

| Variante | nl dauerhaft zusätzlich |
|---|---|
| ohne `wordlist_hash` über die nl-Liste | 24,23 bis 24,29 MB |
| mit `wordlist_hash` (wie die Sonde und wie `build_artifact_nl`) | 23,06 bis 23,19 MB |
| `malloc_trim(0)` vor dem ersten und nach dem zweiten Messpunkt | **15,11 bis 16,14 MB** |

Der Automat selbst hält also 15 bis 16 MB. Der Rest ist Heap, den Python nach
dem Freigeben der Liste an glibc zurückgegeben hat und den glibc nicht an das
Betriebssystem zurückgibt. Wie viel davon stehen bleibt, hängt von der
Vorgeschichte des Prozesses ab: die Research-Sonde baute ihre deutsche Kette
ohne das Findling-Paket zu importieren, die Repo-Sonde lädt das Paket wie das
Produkt. Der laufende Container ruft kein `malloc_trim`, deshalb ist für das
Budget die höhere, produktnahe Zahl maßgeblich.

### 4.2 Budget

| Posten | Wert | Quelle |
|---|---|---|
| Grenzwert Findling | 2000 MB | docs/performance.md, "Drei Zahlen" |
| gemessener Spitzenwert `anon` (ARM, Semantik) | 1812,7 MB | docs/performance.md, Nachmessung 07.09.2026 |
| + niederländischer Automat, Liste freigegeben, höchster Lauf | +25,3 MB, Summe 1838,0 MB, Reserve 162,0 MB | diese Messung |
| zum Vergleich: Research-Wert | +17,7 MB, Summe 1830,4 MB, Reserve 169,6 MB | 21-RESEARCH |
| ohne nl | +0 MB | Registrierung nur bei aktivem nl |

Das Budget der 4-GB-Box hält auch mit der höheren Zahl.

### 4.3 Die "rund 23 MB" sind eine überholte Schätzung

Die "rund 23 MB" aus Roadmap und Anforderung KOMP-01 sind die alte Schätzung
des DEUTSCHEN Automaten aus Phase 2 und gelten für Niederländisch nicht. Der
deutsche Posten ist inzwischen gemessen (41,9 MB Automat plus 21,9 MB Liste,
arm64 nativ, `docs/measurements/2026-09-grundlast-fein/`). Für Niederländisch
gilt die Zahl dieses Berichts: 24,2 bis 25,3 MB produktnah auf amd64. Dass sie
in der Nähe der alten Schätzung liegt, ist Zufall und keine Bestätigung.

### 4.4 ARM (Annahme A1)

Gemessen ist amd64. Die Übertragung auf ARM ist eine Annahme: beim deutschen
Automaten lagen amd64 und natives arm64 unter 0,5 MB auseinander
(`docs/measurements/2026-09-grundlast-fein/README.md`). Die native
ARM-Nachmessung des niederländischen Automaten gehört in die Anfahrt der
Phase 22. Messungen unter qemu-Emulation sind keine Box-Zahl.

## 5. Die Fixture-Teilmenge

`rohdaten/fixture-subset.txt` enthält die 359 Einträge der Vollliste, die als
Teilstring eines gefalteten Wortes aus `compound_cases_nl.txt` oder
`chain_cases_nl.txt` vorkommen, plus die Tussenklanken `s`, `e`, `en`. Die Sonde
vergleicht die Token der Teilmenge mit denen der Vollliste für jedes der 101
Wörter beider Dateien; der Lauf endet mit Exit 0.

`backend/tests/fixtures/constituents_nl.txt` ist eine Byte-Kopie davon. Der
zweite Lauf mit `--against backend/tests/fixtures/constituents_nl.txt` endete
mit "tokenises like the full list, 359 entries", Exit 0.

## 6. Vorbehalt A4

Kein Muttersprachler hat die Fälle gelesen (Stand 2026-09-25). Auswahl und
Glieder stammen aus Verwaltungsvokabular, die Token sind gemessen, die Frage
"würde ein Niederländer so suchen" ist offen.

## 7. Wie der Lauf wiederholt wird

Aus Git-Bash im Repo-Wurzelverzeichnis, Docker läuft:

```sh
MSYS_NO_PATHCONV=1 bash scripts/dev/measure_compounds_nl.sh
MSYS_NO_PATHCONV=1 bash scripts/dev/measure_compounds_nl.sh --against backend/tests/fixtures/constituents_nl.txt
```

Eine Abweichung von den Zahlen oben ist ein Befund, kein Anlass, eine Datei von
Hand anzupassen.
