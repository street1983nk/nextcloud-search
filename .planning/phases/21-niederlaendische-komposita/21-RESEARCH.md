# Phase 21: Niederländische Komposita - Research

**Researched:** 2026-09-25
**Domain:** tantivy `Filter.split_compound` mit zweiter Wortliste (OpenTaal via Debian `wdutch`), Versionsmarken und Umbauweg
**Confidence:** HIGH (Rezept, Lizenz, RAM auf amd64 selbst gemessen), MEDIUM für die ARM-Übertragung der RAM-Zahl

## Summary

Die Mechanik trägt für Niederländisch unverändert, und das ist nicht übernommen, sondern am 25.09.2026 in einem Wegwerf-Container gemessen: `python:3.13-slim-trixie`, `wdutch=1:2.20.19+1-3`, `tantivy==0.26.2` (der aktuelle Pin aus `backend/uv.lock`). Ohne Splitter wird `gemeentebelastingen` in allen vier relevanten Ketten (de, en, nl) zu einem Term, den `belasting` nie trifft; mit Splitter wird es `gemeent, belast`, und `belasting` trifft genau über `body_nl`. Das Erfolgskriterium 2 ist damit technisch erfüllbar, und der CI-Fall ist ohne Splitter nachweislich rot.

Das empfohlene Rezept ist **NL-B 4-14**: alle Wörter aus `/usr/share/dict/dutch`, alphabetisch, Länge 4 bis 14, **mit tantivys eigenem `ascii_fold` gefaltet**, plus die Tussenklanken `s`, `e`, `en`; in der Kette steht der Splitter HINTER dem Fold (Position 3), damit die in Phase 17 gemessene Fold-Position 2 unberührt bleibt. Ergebnis: 316.740 Einträge, 21 von 28 Verwaltungskomposita über ein Glied auffindbar, 0 Fehlzerlegungen an 33 Wächterwörtern (das einzige mehrteilige Wächterwort, `belastingplichtige`, ist selbst ein echtes Kompositum). Die sieben Nicht-Treffer sind benannte Grenzen derselben Art wie `Mietvertrag` im Deutschen: sechs stehen selbst als Eintrag in der Liste, einer (`onroerendezaakbelasting`) scheitert am Eintrag `zaakbelasting`.

Die Zahl "rund 23 MB" aus Roadmap und Anforderung ist die alte Schätzung des DEUTSCHEN Automaten aus Phase 2 und für Niederländisch nicht belastbar. Gemessen, produktnah (deutsche Liste und deutscher Automat bereits im Prozess, wie im laufenden Container): **17,5 bis 17,7 MB dauerhaft, wenn die niederländische Liste nach dem Bau freigegeben wird; 37,1 bis 37,3 MB, wenn sie wie die deutsche im Prozess-Cache bleibt.** Gegen den gemessenen Spitzenwert von 1.812,7 MB `anon` (ARM, mit Semantik, 07.09.2026) und den Grenzwert 2,0 GB hält das Budget in beiden Fällen, und zwar nur auf Installationen mit aktivem nl. Lizenz: OpenTaal stellt die Liste upstream wahlweise unter BSD-3-Clause und/oder CC BY 3.0; Debians `copyright` nennt für `wordlist/*` nur CC-BY-3.0. Beides ist permissiv, keine GPL-Kaskade wie bei `wngerman`.

**Primary recommendation:** Eigenes Modul `findling/index/wordlist_nl.py` plus eine neue siebte Marke `wordlist_hash_nl`, die in jeder Hinsicht wie die Sprachmarke reist (nicht gesät, Fehlen bei inaktivem nl ist Legacy, Teil von `MARKS_A_REBUILD_ANSWERS`, geschrieben nur von `stamp_after_swap` und `stamp_a_new_directory`), die Splitter-Kette nur bei aktivem nl unter dem Namen `nl` registrieren, `ANALYZER_VERSION` NICHT anheben.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Wortliste ins Abbild | Image-Build (Dockerfile, `docker.yml`-Gate) | THIRD-PARTY.md | Wie `wngerman`: gepinnt, Lizenztext an eigenen Pfad kopiert, kein Download zur Laufzeit |
| Rezept und Artefakt `nl-full.txt` + `.sha256` | Containerstart, `findling.index.wordlist_nl` | Volume `$APP_PERSISTENT_STORAGE/dict/` | Präzedenz `wordlist.py`: Artefakt statt Laufzeitentscheid, fail closed gegen den eigenen Digest |
| Splitter-Kette und Automat-Singleton | Analyse-Tier, `findling.index.analyzer` | `findling.index.open` (Registrierung) | Eine Registrierung je Name, Singleton je Digest, Extraktionskind importiert es nie |
| Digest-Marke `wordlist_hash_nl` | Store/Meta, `findling.store.repo` | `findling.index.open` (Erwartung), `findling.index.rebuild` (Stempel) | Vergleich lebt im Store, Erwartung im Index-Tier, Stempel hinter dem Tausch |
| Umbau nur bei aktivem nl | Rebuild-Tier, `rebuild_the_index` | `api.resources.version_drift` (Banner) | Re-Analyse genügt, weil `body_nl` aus dem gespeicherten `body_de`-Text neu entsteht |
| Beweis gemeentebelastingen/belasting | CI `deploy-harp.yml` "Language proof" | Python-Suite (Fixture-Teilmenge) | Einziger CI-Schritt, der `languagesActive == de,en,es,it,nl,pt` erzwingt |

## Standard Stack

### Core
| Library / Paket | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Debian `wdutch` (Quelle `dutch`, OpenTaal) | `1:2.20.19+1-3` (trixie, forky, sid) | liefert `/usr/share/dict/dutch`, 413.288 Zeilen, 5.096.240 Byte, SHA-256 `2e5128e8e7f9a5bdfc427c784c839986b0df1386cc53aef90ed2df71644f3987` | `Architecture: all`, amd64 und arm64 byteidentisch gemessen; upstream-Stand `2020-12-29 18:12:58 2.20.19` [VERIFIED: sources.debian.org API + dpkg -s + sha256sum in beiden Plattform-Abbildern] |
| `tantivy` (Python) | `0.26.2`, Banner `tantivy v0.26.2, index_format v7` | `Filter.split_compound`, `Filter.ascii_fold`, `Filter.stemmer("dutch")` | Bereits gepinnt, keine neue Abhängigkeit [VERIFIED: backend/uv.lock + Containerlauf] |

### Supporting
| Paket | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `dictionaries-common` | bereits im Abbild | harte `Depends` von `wdutch` wie von `wngerman` | kommt nicht neu hinzu [VERIFIED: dpkg -s wdutch] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `wdutch` (`wordlist.txt`, 413.288 Zeilen) | OpenTaal `elements/basiswoorden-gekeurd.txt` (rund 200.000 Grundwörter) | Liegt NICHT im Debian-Binärpaket, müsste als Datei mit eigener Provenienz ins Repo; nicht gemessen. Nicht verwenden, solange das Paket-Rezept trägt. |
| NL-B (Fold vor Split, gefaltete Liste) | NL-A (Split vor Fold, rohe Liste) | A: 20/28 statt 21/28, verliert die flache Schreibung (`coordinatiecentrum` ohne Trema bleibt ganz) und verschiebt die in Phase 17 gemessene Fold-Position. Verworfen. |
| Fenster 4-14 | Fenster 4-12 | 25/28 statt 21/28, aber Übersplit (`onderhandelingen` wird `onderhandel, ing`, Junk-Term `ing`), genau das Muster des deutschen Rezepts D. Verworfen. |
| Fenster 4-14 | Fenster 4-16 | 16/28, weil längere Komposita selbst Einträge werden. Verworfen. |
| Mit Tussenklanken | ohne | 14/28 statt 20/28 (Rezept A). Die Tussenklanken sind tragend. |
| Alle Einträge | ohne großgeschriebene (Eigennamen) | 276.915 statt 317.320 Einträge, Ergebnis identisch 20/28 (Rezept A). Kein Grund für eine zweite Variante oder einen Schalter `FINDLING_COMPOUND_DICT_NL`. |

**Installation (Dockerfile, Muster des `wngerman`-Blocks):**
```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends wdutch=1:2.20.19+1-3 \
    && rm -rf /var/lib/apt/lists/* \
    && test -s /usr/share/dict/dutch \
    && test -s /usr/share/doc/wdutch/copyright \
    && install -D -m 0444 /usr/share/doc/wdutch/copyright \
        /usr/local/share/findling/COPYING.wdutch
```
Die Epoche `1:` im Pin funktioniert mit apt so geschrieben, in diesem Research gebaut [VERIFIED: docker build]. Installed-Size 5.021 kB.

## Package Legitimacy Audit

Diese Phase installiert keine pip- oder npm-Pakete. Einzige neue Abhängigkeit ist ein Debian-Archivpaket aus dem offiziellen trixie-Archiv, das über dieselbe apt-Kette wie `wngerman` kommt.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `wdutch` 1:2.20.19+1-3 | Debian trixie main | Quellpaket seit hamm (1998), diese Revision 2025 | n/a (Distributionspaket) | salsa.debian.org/debian/dutch, upstream github.com/OpenTaal/opentaal-wordlist | nicht anwendbar (kein PyPI/npm) | Approved, per sources.debian.org und Installation verifiziert |

**Packages removed due to slopcheck [SLOP] verdict:** keine
**Packages flagged as suspicious [SUS]:** keine

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| KOMP-01 | Nutzer findet niederländische Komposita über ihre Glieder (`gemeentebelastingen` über `belasting`) via `split_compound` mit `wdutch`/OpenTaal-Wortliste; eigene Digest-Marke, die NUR bei aktivem nl einen Rebuild auslöst; RAM des zweiten Automaten vor dem Bau gemessen; fällt bei Terminnot als Ganzes | Rezeptmessung (Abschnitt "Die Rezeptmessung"), Querprobe über alle Ketten (Code Examples), RAM-Messung (Abschnitt "RAM"), Markenmechanik (Pattern 3), Lizenz (Abschnitt "Lizenzlage"), No-Go-Rückbau (Pattern 5) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Code, Bezeichner und Kommentare Englisch; deutsche Prosa mit echten Umlauten nur in Doku, nie in Code, Keywords, URLs, YAML.
- Keine Em-Dashes und keine En-Dashes, keine Emojis.
- Qualitätsgates: ruff-Vollregelsatz, `ruff format --check`, pyright basic (lokal mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, sonst weicht die CI ab), vulture; lokal grün vor jedem Commit.
- Python nur über uv (System-Python defekt).
- RAM-Budget der 4-GB-Box ist hart, CPU-only, ARM-tauglich.
- Keine Inhalte verlassen den Server, keine Laufzeit-Downloads; Messmodi geben nur Zahlen aus, nie Token aus Nutzerinhalt (T-02-14).
- Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Abschluss fixen.
- Owner-Regel "nur erbetene Änderungen" an Owner-Dokumenten; Store-/README-Texte nur als Faktenliste, Entwurf vorher zeigen (betrifft Phase 23, nicht diese).
- Memory-Regel: Gegenprobe nie mit dem Muster der Umsetzung; der CI-Fall wird deshalb über die ausgelieferte Kette UND über eine Kette ohne Splitter gemessen, nicht über eine nachgebaute.

## Die Entscheidungsvorlage für das Owner-Tor (Erfolgskriterium 1)

Das Tor ist der erste Plan und ein blockierender Checkpoint, Muster 17-01/17-04 (Entscheiddokument mit datiertem Vollzug). Diese Fakten gehören hinein, jede mit ihrer Quelle:

| Frage | Harte Antwort | Quelle |
|---|---|---|
| Wirkt es? | `gemeentebelastingen` wird `gemeent, belast`; `belasting` wird `belast`; Treffer nur über `body_nl`. Ohne Splitter: 0 Treffer in de, en und nl | Querprobe 25.09.2026, Code Examples |
| Wie viel? | 21 von 28 Verwaltungskomposita über ein Glied auffindbar, 0 Fehlzerlegungen an 33 Wächtern | Rezepttabelle unten |
| Lizenz? | upstream BSD-3-Clause und/oder CC BY 3.0 nach Wahl; Debian nennt CC-BY-3.0; kein Copyleft | `wordlist/LICENSE.txt`, `debian/copyright` |
| RAM? | +17,6 MB (Liste freigegeben) bzw. +37,2 MB (Liste gecacht), nur bei aktivem nl; Spitze 1.812,7 MB gegen Grenzwert 2.000 MB bleibt mit 1.850 MB unter der Grenze | RAM-Abschnitt |
| Startzeit? | +0,73 bis 0,81 s beim ersten Start mit nl (Lesen, Filtern, Bauen), danach nur Artefakt lesen | produktnahe Messung |
| Abbild? | +5,0 MB (Installed-Size 5.021 kB) | dpkg |
| Wer merkt was? | Bestandsinstallation ohne nl: nichts (kein Banner, kein Lauf, kein RAM). Mit nl: ein Re-Analyse-Umbau, kein Download, kein OCR, keine Neueinbettung | Pattern 3 |
| Aufwand? | Schätzung 6 bis 8 Pläne (siehe Plan-Schnitt), Größenordnung der Phase 20 | [ASSUMED] |
| Was fällt bei No-Go? | Nur Planungs- und Doku-Text, KEIN Code (das Tor steht vor dem ersten Codeschritt). Liste in Pattern 5 | Grep 25.09.2026 |

Bei Go gehören zusätzlich die drei Entscheide aus "Open Questions" 1 bis 3 in dasselbe Dokument (Lizenzwahl, Liste cachen ja/nein, Fenster), jeweils mit Empfehlung, damit der Owner in einem Durchgang entscheidet.

## Die Rezeptmessung (Erfolgskriterium 3, "eigene Rezeptmessung wie beim deutschen Splitter")

**Präzedenz:** `docs/measurements/2026-09-komposita-rezept-a/README.md`, `scripts/dev/measure_compounds.sh`, `scripts/dev/compound_probe.py`, `scripts/dev/measure_wordlist.sh`, `backend/src/findling/index/wordlist.py` (Rezepttabelle A bis D im Modul-Docstring). Die Sonde baut KEINE eigene Kette, sondern ruft die ausgelieferten Funktionen; das Messskript fährt im Wegwerf-Container mit hart gepinntem Paket, weil es auf der Entwicklermaschine keine Debian-Liste gibt. Genau so muss die niederländische Messung in den Plan: `scripts/dev/measure_compounds_nl.sh` plus `scripts/dev/compound_probe_nl.py`, Fallliste `backend/tests/fixtures/compound_cases_nl.txt`, Rohdaten unter `docs/measurements/2026-09-komposita-nl/rohdaten/`, und die Sonde erzeugt die Fixture-Teilmenge `constituents_nl.txt` und beweist Token-Gleichheit Teilmenge gegen Vollliste.

**Diese Research hat die Messung vorab gefahren** (Prototyp im Scratchpad, gleiche Pins). Das Repo-Skript des Plans muss diese Zahlen reproduzieren; eine Abweichung ist ein Befund, kein Anlass zum Nachbessern.

### Umgebung
| Was | Wert |
|---|---|
| Datum | 2026-09-25 |
| Abbild | `python:3.13-slim-trixie` |
| Paket | `wdutch=1:2.20.19+1-3` |
| Engine | `tantivy==0.26.2`, `index_format v7` |
| Quelle | `/usr/share/dict/dutch`, 413.288 Zeilen, 5.096.240 Byte, davon 4.380 Zeilen mit Leerzeichen (fallen durch `isalpha`) |
| Fälle | 28 Komposita mit erwartetem Glied, 33 Wächter (17 Alltagswörter, 16 lange Nicht-Komposita) |

### Rezepte
| Rezept | Fenster | Tussenklanken | Liste | Split-Position | Einträge | Komposita über Glied | Wächter einteilig | SHA-256 (Anfang) |
|---|---|---|---|---|---|---|---|---|
| ohne Splitter (heutige nl-Kette) | n/a | n/a | n/a | n/a | n/a | **0/28** | n/a | n/a |
| A 4-14 | 4-14 | s, e, en | roh | vor Fold | 317.320 | 20/28 | 32/33 | `5f0b465d8a55adde` |
| A 4-16 | 4-16 | s, e, en | roh | vor Fold | 353.318 | 15/28 | 33/33 | `d6d3c2bd397bf903` |
| A 4-13 | 4-13 | s, e, en | roh | vor Fold | 290.366 | 21/28 | 31/33 | `58dd09df2873c471` |
| A 4-12 | 4-12 | s, e, en | roh | vor Fold | 257.766 | 24/28 | 31/33 | `3bfc7cf7090bf9b4` |
| A 3-14 | 3-14 | s, e, en | roh | vor Fold | 319.016 | 20/28 | 32/33 | `7ea7781c4744a9a1` |
| A 4-14 ohne Tussenklanken | 4-14 | keine | roh | vor Fold | 317.317 | 14/28 | 32/33 | `0fa98d8417540588` |
| A 4-14 ohne Großschreibung | 4-14 | s, e, en | roh | vor Fold | 276.915 | 20/28 | 32/33 | `ff5a14fd927d9c96` |
| **B 4-14 (empfohlen)** | 4-14 | s, e, en | **gefaltet** | **hinter Fold** | **316.740** | **21/28** | **32/33** | `ee7f3b8380c75283` |
| B 4-16 | 4-16 | s, e, en | gefaltet | hinter Fold | 352.737 | 16/28 | 33/33 | `972f07696871b7b5` |
| B 4-13 | 4-13 | s, e, en | gefaltet | hinter Fold | 289.786 | 22/28 | 31/33 | `95940f1ee57034f2` |
| B 4-12 | 4-12 | s, e, en | gefaltet | hinter Fold | 257.194 | 25/28 | 31/33 | `b58362850c76d382` |

"Wächter einteilig 32/33" bei 4-14: der eine mehrteilige Wächter ist `belastingplichtige` (`belast, plichtig`), und der ist ein echtes Kompositum, also keine Fehlzerlegung. Bei 4-13 und 4-12 kommt `onderhandelingen` dazu (`onderhandel, ing`): ein Junk-Term `ing` im Index, derselbe Übersplit, der das deutsche Rezept D verworfen hat.

### Rezept B 4-14, Fall für Fall
| Kompositum | Glied | Token | Eintrag selbst | Treffer |
|---|---|---|---|---|
| gemeentebelastingen | belasting | gemeent, belast | 0 | ja |
| gemeentebelasting | belasting | gemeent, belast | 0 | ja |
| inkomstenbelasting | belasting | inkomst, belast | 0 | ja |
| waterschapsbelasting | belasting | waterschap, belast | 0 | ja |
| belastingaangifte | aangifte | belast, aangift | 0 | ja |
| huurovereenkomst | overeenkomst | hur, overeenkomst | 0 | ja |
| arbeidsovereenkomst | overeenkomst | arbeid, overeenkomst | 0 | ja |
| koopovereenkomst | overeenkomst | kop, overeenkomst | 0 | ja |
| bestemmingsplan | bestemming | bestemm, plan | 0 | ja |
| omgevingsvergunning | vergunning | omgev, vergunn | 0 | ja |
| parkeervergunning | vergunning | parker, vergunn | 0 | ja |
| zorgverzekering | verzekering | zorg, verzeker | 0 | ja |
| ziektekostenverzekering | verzekering | ziektekost, verzeker | 0 | ja |
| kinderopvangtoeslag | toeslag | kinderopvang, toeslag | 0 | ja |
| gemeenteraadsvergadering | vergadering | gemeenterad, vergader | 0 | ja |
| begrotingswijziging | wijziging | begrot, wijzig | 0 | ja |
| afvalstoffenheffing | heffing | afvalstoff, heffing | 0 | ja |
| subsidieaanvraag | aanvraag | subsidie, aanvrag | 0 | ja |
| vergaderverslag | verslag | vergader, verslag | 0 | ja |
| coördinatiecentrum | centrum | coordinatie, centrum | 0 | ja |
| coordinatiecentrum (flach) | centrum | coordinatie, centrum | 0 | ja (nur Rezept B) |
| onroerendezaakbelasting | belasting | onroer, zaakbelast | 0 | nein, `zaakbelasting` ist Eintrag |
| bouwvergunning | vergunning | bouwvergunn | 1 | nein, Eintrag |
| huurtoeslag | toeslag | huurtoeslag | 1 | nein, Eintrag |
| verkeersboete | boete | verkeersboet | 1 | nein, Eintrag |
| jaarrekening | rekening | jaarreken | 1 | nein, Eintrag |
| factuurnummer | nummer | factuurnummer | 1 | nein, Eintrag |
| opzegtermijn | termijn | opzegtermijn | 1 | nein, Eintrag |

Wächter, alle einteilig in B 4-14: overeenkomst, vergadering, belasting, gemeente, verzekering, aangifte, rekening, bestemming, onderwerp, beleid, afspraak, opdracht, handtekening, bijlage, voorwaarden, herinnering, betaling, verantwoordelijkheid, beschikbaarheid, vertegenwoordiger, gemeentelijke, ontwikkelingen, overeenkomsten, aansprakelijkheid, verplichtingen, onderhandelingen, tegemoetkoming, burgemeester, wethouder, ondernemer, aanbesteding, openbaarheid. (`openbaarheid` wird `open`: das ist der Snowball-Stemmer, nicht der Splitter; in der Kette ohne Splitter identisch.)

## RAM (Erfolgskriterium 3, "VOR dem Bau gemessen")

### Messmethode
Wie `analyzer.measure()`: `VmRSS` aus `/proc/self/status`, jeder Lauf in einem frischen Prozess, dreimal wiederholt. Zwei Konstellationen, weil nur die zweite die Produktzahl ist:

1. **Frischer Prozess, nur Niederländisch:** überschätzt, weil der Python-Allokator die Arena der temporären Liste nicht zurückgibt.
2. **Produktnah:** deutsche Liste (276.496 Einträge, im Prozess gehalten wie `_CACHED_ENTRIES`) und deutscher Automat stehen bereits, dann kommt Niederländisch dazu. Das ist die Reihenfolge des laufenden Containers.

### Ergebnisse, amd64 (Docker Desktop, x86_64)
| Konstellation | Rezept | dauerhaft zusätzlich | Bau | Durchsatz |
|---|---|---|---|---|
| frischer Prozess | B 4-14 | 64,3 bis 64,7 MB | 0,47 bis 0,49 s | 1,43 bis 1,93 Mio. Token/s |
| frischer Prozess | A 4-14 | 64,6 bis 64,8 MB | 0,46 bis 0,49 s | 1,79 bis 1,89 Mio. Token/s |
| hinter deutschem Automat, deutsche Liste freigegeben | B 4-14 | 17,2 MB | 0,45 bis 0,48 s | 1,78 bis 1,96 Mio. Token/s |
| **produktnah, nl-Liste gecacht** | **B 4-14** | **37,10 bis 37,35 MB** | 0,73 bis 0,81 s (Lesen+Filtern+Bauen) | n/a |
| **produktnah, nl-Liste nach dem Bau freigegeben** | **B 4-14** | **17,53 bis 17,66 MB** | 0,73 bis 0,80 s | n/a |
| produktnah, gecacht | B 4-12 | 36,4 MB | 0,57 s | n/a |
| produktnah, freigegeben | B 4-12 | 21,3 MB | 0,58 s | n/a |

Grundlast mit deutscher Liste und deutschem Automat in dieser Sonde: 94,2 bis 95,8 MB; mit Niederländisch 112,0 bis 133,0 MB.

### ARM
Unter qemu-Emulation (arm64-Abbild auf x86) kamen 39,7 bis 41,8 MB (freigegeben) und 59,1 bis 59,2 MB (gecacht) bei 7,0 bis 7,5 s. **Diese Zahlen sind ein Emulationsartefakt und keine Box-Zahl**: `VmRSS` unter qemu-user enthält den Übersetzungscache des Emulators. Belastbar ist die Präzedenz aus `docs/measurements/2026-09-grundlast-fein/README.md`: dort lagen amd64 und NATIVES arm64 beim deutschen Automaten bei 42,6 gegen 42,1 MB und bei der Liste bei 22,1 gegen 21,9 MB, also unter 0,5 MB auseinander. Die amd64-Zahl ist damit der beste Vorab-Wert für ARM [ASSUMED: Übertragung per Präzedenz, nicht nativ gemessen]. Die native ARM-Zahl gehört als Nebenmessung in die Anfahrt der Phase 22 (Schritt "niederländischer Automat gebaut" in der Grundlast-Reihe).

### Budgetrechnung
| Posten | Wert | Quelle |
|---|---|---|
| Grenzwert Findling | 2.000 MB | docs/performance.md, "Drei Zahlen" |
| gemessener Spitzenwert `anon` (ARM, Semantik) | 1.812,7 MB | docs/performance.md, Nachmessung 07.09.2026 |
| + niederländischer Automat, Liste gecacht | +37,3 MB, Summe 1.850,0 MB, Reserve 150 MB | diese Messung |
| + niederländischer Automat, Liste freigegeben | +17,7 MB, Summe 1.830,4 MB, Reserve 170 MB | diese Messung |
| ohne nl | +0 MB | Pattern 2 (gated Registrierung) |

Das Gesamtbudget der 4-GB-Box hält in beiden Varianten. Empfehlung: Liste freigeben (Open Question 2), weil 19,6 MB für nichts gehalten würden: die Suchseite braucht vom Artefakt nur den Digest, nicht die Einträge.

**Die "rund 23 MB" richtigstellen:** Die Zahl stammt aus der Phase-2-Schätzung des deutschen Automaten. Der deutsche Posten ist inzwischen mit 41,9 MB Automat plus 21,9 MB Liste gemessen (arm64 nativ, grundlast-fein Schritte 09/10). Der Plan muss im Messbericht und in `docs/performance.md` die gemessene niederländische Zahl eintragen und die 23 MB ausdrücklich als überholte Schätzung benennen, sonst zitiert Phase 23 die falsche Zahl.

## Lizenzlage (Erfolgskriterium 3)

| Punkt | Befund | Quelle |
|---|---|---|
| Upstream | "Rechten: Revised BSD License en/of CC BY 3.0"; "Kies een of beide licenties" (Wahl des Nutzers) | `wordlist/LICENSE.txt` im Quellpaket `dutch` 1:2.20.19+1-3 [VERIFIED: sources.debian.org] |
| Debian | `Files: wordlist/*` `License: CC-BY-3.0`; BSD-3-Clause nur für `hunspell/*`, `aspell/*`, `ispell/*`, `convert`, `debian/*`; die Datei enthält beide Lizenztexte vollständig | `debian/copyright` [VERIFIED] |
| Was `wdutch` installiert | genau `wordlist/wordlist.txt` als `/usr/share/dict/dutch` (Build: `cp $UTF8WORDLIST $WORDLIST`), dazu `/usr/share/dict/nederlands` als Symlink | `convert`, `debian/wdutch.install`, `dpkg -L wdutch` [VERIFIED] |
| Was im Abbild an Lizenztext liegt | nur `/usr/share/doc/wdutch/copyright` (21.777 Byte); das upstream-`LICENSE.txt` ist NICHT im Binärpaket | `dpkg -L wdutch` [VERIFIED] |
| Urheber | © 2020 OpenTaal (Simon Brouwer, Sander van Geloven), © 2006-2011 OpenTaal (Ruud Baars, Simon Brouwer), © 2001-2005 Simon Brouwer e.a., © 1996 Nederlandstalige TeX Gebruikersgroep | `LICENSE.txt` |

**Korrektur an der Milestone-Recherche:** `.planning/research/FEATURES.md` Zeile 71 sagt "BSD-3-Clause und CC-BY-3.0 (geprüft im Debian-copyright)". Das Debian-`copyright` nennt für die Wortliste nur CC-BY-3.0; die Doppellizenz steht im upstream-`LICENSE.txt`. Beides ist permissiv, die Aussage "lizenzklar, keine GPL-Kaskade" bleibt richtig, aber THIRD-PARTY.md muss die Quelle korrekt benennen.

**Empfohlene Umsetzung:** `COPYING.wdutch` aus `/usr/share/doc/wdutch/copyright` nach `/usr/local/share/findling/` kopieren (fail closed wie `wngerman`), in THIRD-PARTY.md einen Abschnitt nach dem Muster "German word list" mit Paket, Version, Quelle, Datei, Zeilen/Bytes, Lizenz (CC-BY-3.0 laut Debian; upstream wahlweise BSD-3-Clause), Namensnennung "OpenTaal, https://www.opentaal.org" und dem Hinweis, dass das Artefakt `nl-full.txt` eine gefilterte und gefaltete Bearbeitung ist. Das erfüllt beide Lizenzen zugleich (Hinweis + Lizenztext + Namensnennung + Kennzeichnung der Bearbeitung) [ASSUMED: rechtliche Bewertung, keine Rechtsberatung; Owner bestätigt die Wahl].

## Architecture Patterns

### Datenfluss

```
Image-Build:  apt wdutch=1:2.20.19+1-3 -> /usr/share/dict/dutch + COPYING.wdutch
                                  |
Containerstart (nur wenn "nl" in settings().languages):
  /usr/share/dict/dutch -> Rezept B 4-14 (isalpha, 4..14, tantivy-Fold, + s/e/en)
        -> $APP_PERSISTENT_STORAGE/dict/nl-full.txt + .sha256   (fail closed)
        -> dutch_mark = digest                                   (sonst "off", nichts gelesen)
        -> cached_dutch_analyzer(digest, entries) -> Liste freigeben
                                  |
open_index(): register "nl" = Splitter-Kette (nl aktiv) | Snowball-Kette (nl inaktiv)
                                  |
expected_versions(...) enthält wordlist_hash_nl = dutch_mark
        |                                   |
Store.version_mismatch()             rebuild_the_index()
  stored None + expected "off" -> ok   MARKS_A_REBUILD_ANSWERS enthält wordlist_hash_nl
  stored != expected -> Drift          -> Re-Analyse: body_de-Text durch die neue nl-Kette
        |                                   -> swap -> stamp_after_swap schreibt Marke
  version_drift -> reindexRequired (Banner)
                                  |
Suche: Wort "belasting" -> FieldPlan (aus languages-Marke) -> body_nl -> Token "belast"
```

### Recommended Project Structure
```
backend/src/findling/index/
├── wordlist.py          # unverändert (deutscher Digest b1f6... muss byteidentisch bleiben)
├── wordlist_nl.py       # NEU: Quelle, Fenster, TUSSENKLANKEN, Rezept, Artefakt, dutch_mark, measure
├── analyzer.py          # + dutch_analyzer, cached_dutch_analyzer, dutch_build_count
├── open.py              # + DUTCH_MARK, Registrierung gated, expected_versions, stamp_a_new_directory
└── rebuild.py           # + MARKS_A_REBUILD_ANSWERS, stamp_after_swap
backend/src/findling/store/repo.py   # + _DUTCH_MARK, Saat-Ausnahme, Legacy-Regel
scripts/dev/measure_compounds_nl.sh, scripts/dev/compound_probe_nl.py
backend/tests/fixtures/compound_cases_nl.txt, constituents_nl.txt
docs/measurements/2026-09-komposita-nl/ (README.md + rohdaten/)
docs/dutch-analyzer.md (oder Abschnitt in docs/language-analyzers.md)
```

### Pattern 1: Eigenes Modul, deutsches Modul unberührt
**What:** `wordlist_nl.py` als Geschwister von `wordlist.py`, nicht als Sprachparameter in `wordlist.py`.
**When to use:** immer in dieser Phase.
**Warum:** (a) Der deutsche Digest `b1f64012...dde0` steht in `test_upgrade_compatibility.py` und in der Box-Historie; jede Refaktorierung, die ihn bewegt, ist ein Vollreindex für alle. (b) Rückbau bei Abbruch ist ein Dateilöschen plus wenige Berührpunkte. (c) Unterschiede sind echt: gefaltete Liste, andere Tussenklanken, keine `nouns`-Variante, kein Listen-Cache.
**Bausteine (Muster aus `wordlist.py` übernehmen):** `SYSTEM_WORDLIST_NL = Path("/usr/share/dict/dutch")`, `MIN_LEN = 4`, `MAX_LEN = 14`, `TUSSENKLANKEN = ("s", "e", "en")` (EIN Literal, zweimal benutzt: Liste und `custom_stopword`), `load_constituents_nl()`, `wordlist_hash` wiederverwenden (import, nicht kopieren), `artifact_path_nl()` -> `dict_dir / "nl-full.txt"`, `build_artifact_nl()` fail closed gegen den eigenen Digest, `dutch_mark(languages)`, `measure()` nur Zahlen.

### Pattern 2: Registrierung gated, aber nie abwesend
**What:** `open_index` registriert unter `TOKENIZER_NL` IMMER eine Kette; die Splitter-Kette nur, wenn nl aktiv ist, sonst die heutige `snowball_analyzer("dutch")`.
**Warum:** Phase-18-Pitfall 2 verbietet eine FEHLENDE Registrierung ("Error getting tokenizer for field: body_nl" beim ersten `add_document`). Er verbietet nicht, dass die Variante an der Sprachmenge hängt. Ohne nl ist `body_nl` leer und wird laut `field_plan_for` nicht durchsucht, also ist die Variante dort tokenisierungsneutral und spart 17,6 bis 37,2 MB auf jeder Installation ohne nl.
**Signatur:** `open_index(path, constituents, *, dutch: Sequence[str] | None)` als keyword-only ohne Default in `src`, damit kein Aufrufer die Entscheidung stillschweigend trifft; die Liste kommt aus EINER Hilfsfunktion (`dutch_constituents_for(languages)`), die bei inaktivem nl `None` liefert, ohne die Datei zu lesen. Das Extraktionskind darf `wordlist_nl`/`analyzer` nicht importieren (bestehender AST-Wächter, siehe `findling/extract/__init__.py`).

### Pattern 3: Die siebte Marke reist wie die Sprachmarke
**What:** `DUTCH_MARK: Final = "wordlist_hash_nl"`, Wert = Digest des gefilterten niederländischen Rezepts bei aktivem nl, sonst die Konstante `DUTCH_LIST_OFF = "off"`.
**Jede Stelle, an der die Sprachmarke eine Sonderbehandlung hat, bekommt dieselbe für diese Marke:**

| Stelle | Sprachmarke heute | wordlist_hash_nl |
|---|---|---|
| `open.expected_versions` | `LANGUAGES_MARK: languages` | `DUTCH_MARK: dutch_mark` (neuer keyword-only Parameter) |
| `repo._DEFAULT_META` | nicht enthalten | nicht enthalten |
| `repo._seed_meta` | `seed.pop(_LANGUAGES_MARK)` | `seed.pop(_DUTCH_MARK)`, sonst schreibt die Saat den Wunsch als Fakt und die Marke schweigt (Phase-18-Pitfall 1, T-18-05-01) |
| `repo.version_mismatch` | `_languages_are_legacy` | `_dutch_list_is_legacy(stored, expected)`: `stored is None and expected == DUTCH_LIST_OFF` -> kein Drift; alles andere wird verglichen |
| `rebuild.MARKS_A_REBUILD_ANSWERS` | enthalten | enthalten: Re-Analyse genügt, weil `_document_from` `body_nl` aus dem gespeicherten `body_de`-Text durch die jetzt registrierte Kette neu schreibt |
| `open._MARKS_OF_A_DIRECTORY` | enthalten | enthalten: die Marke beschreibt den Inhalt eines Verzeichnisses |
| `rebuild.stamp_after_swap` | schreibt | schreibt (Signatur um den Wert erweitern) |
| `open.stamp_a_new_directory` | schreibt | schreibt |
| `open.stamp_after_rebuild` | überspringt | überspringt (folgt aus `_MARKS_OF_A_DIRECTORY`) |

**Zustandstabelle, die die Tests abdecken müssen (beide Richtungen, Pitfall-1-Warnzeichen beachten: Marke NICHT setzen und trotzdem prüfen):**

| Fall | gespeichert | erwartet | Drift? | Folge |
|---|---|---|---|---|
| 1.2.0 -> 1.3.0, de,en | fehlt | off | nein | kein Banner, kein Lauf, kein RAM (Kriterium 4) |
| 1.2.0 -> 1.3.0, nl neu an | fehlt | Digest | ja (plus languages) | ein Re-Analyse-Umbau |
| 1.3.0 mit nl, Wortliste unverändert | Digest | Digest | nein | nichts |
| 1.3.0 mit nl, neues `wdutch`/Rezept | Digest alt | Digest neu | ja | Re-Analyse, nur bei nl |
| nl wieder aus | Digest | off | ja (plus languages) | Re-Analyse, stempelt off |
| frische Installation mit nl | fehlt | Digest | wird von `stamp_a_new_directory` vor dem Anlegen geschrieben | kein Drift |
| Hausinstallationen mit nl vor Phase 21 (CI, findling-nextcloud) | fehlt, languages enthält nl | Digest | ja | ein Umbau, korrekt |

### Pattern 4: `ANALYZER_VERSION` bleibt stehen
**What:** Die geänderte nl-Kette hebt `ANALYZER_VERSION` NICHT.
**Warum:** `analyzer_version` ist nicht in `MARKS_A_REBUILD_ANSWERS`; ein Hub löst über `start_rebuild_on_drift` die Generationserhöhung aus, also den Vollreindex (19 h 20 min) auf JEDER Installation, auch ohne nl. Das bricht Kriterium 4 direkt. Die Kettenänderung wird vollständig von der eigenen Marke getragen. Der Docstring von `analyzer.py` ("Any change to a chain below has to raise ANALYZER_VERSION") muss um genau diesen Fall ergänzt werden, sonst hebt ein Executor oder Reviewer die Zahl "vorsichtshalber".
**Offene Lücke dieses Musters:** Eine spätere Änderung NUR an der Reihenfolge der nl-Kette bei gleicher Liste bewegt den Digest nicht. Abhilfe (Empfehlung, Discretion des Planers): Markenwert als `f"{DUTCH_CHAIN_VERSION}:{digest}"` mit `DUTCH_CHAIN_VERSION = 1` neben der Kette.

### Pattern 5: No-Go ohne Reste, Go mit sauberem Abbruchweg
**Bei No-Go am Tor** (vor dem ersten Codeschritt) fällt ausschließlich Text. Gefunden per Grep am 25.09.2026, das ist die vollständige Liste:
- `.planning/ROADMAP.md`: Phase 21 als entfallen markieren (datiert), Phase-22-Abhängigkeit "(und Phase 21, falls das Tor auf Go steht)" auflösen, Phase-23-Kriterium 2 "Komposita gibt es nur für de und nl" auf "nur für de" ändern, Ausführungsreihenfolge und Traceability-Zeile.
- `.planning/REQUIREMENTS.md`: KOMP-01 in "Future"/Backlog verschieben, HART-05 "Komposita nur de/nl" auf "nur de", Traceability.
- `.planning/BACKLOG.md`: KOMP-01 als Eintrag mit Datum und Messung dieser Research (die Zahlen bleiben wiederverwendbar).
- `docs/language-analyzers.md` Zeile 443: "the Dutch constituent list is scheduled for phase 21" umformulieren.
- `backend/src/findling/index/schema.py` Zeile 170-171: Kommentar "the Dutch compounds are their own question and their own phase" ist auch nach No-Go wahr, darf bleiben; optional auf "deferred" präzisieren (dann aber mit Gates).
- Keine Marke, kein Feld, keine Datei im Abbild: `body_nl` existiert schon seit Phase 18 und bleibt.

**Bei Go, aber Abbruch mitten im Bau** (Terminnot): 1.3.0 ist noch nicht veröffentlicht, also hat keine Feldinstallation die Marke. Die Pläne so schneiden, dass alles bis zur Verdrahtung in eigenen Dateien lebt (Modul, Sonde, Fixture, Tests des Moduls) und die Verdrahtung (Registrierung, Marke, Stempel, Dockerfile) in einem abgegrenzten Plan kommt. Ein Abbruch vor der Verdrahtung ist ein Dateilöschen; ein Abbruch danach ist ein Revert einer Commit-Reihe VOR Phase 23. Die Planung muss festhalten: Phase 23 startet nicht mit halber Verdrahtung.

### Anti-Patterns to Avoid
- **`wordlist.py` generalisieren:** riskiert den deutschen Digest und damit einen Vollreindex für alle.
- **Die Liste mit Python falten (`unicodedata`):** die Liste muss exakt das treffen, was tantivys `ascii_fold` aus dem Token macht. Mit tantivy falten (Kette `simple -> lowercase -> ascii_fold` je Eintrag, Einträge, die nicht genau ein Token liefern, verwerfen). Eine Abweichung macht das Splitten still wirkungslos, während flache Tests grün bleiben (derselbe Mechanismus wie beim deutschen "the list keeps its umlauts").
- **Die deutsche Liste für Niederländisch nutzen:** falsche statt fehlender Zerlegungen (steht so in `docs/language-analyzers.md`).
- **Die Marke säen oder `ANALYZER_VERSION` heben:** siehe Pattern 3 und 4.
- **Den Schalter `FINDLING_COMPOUND_DICT_NL` einführen:** die Eigennamen-freie Variante bringt 13 Prozent weniger Einträge und kein anderes Ergebnis; ein Schalter ist eine weitere ungemessene Variante und eine `info.xml`-Zusage.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Komposita zerlegen | eigenes Aho-Corasick oder Decompounder in Python | `Filter.split_compound` | Leftmost-longest, zerlegt nur bei vollständiger Überdeckung, sonst Originaltoken; derselbe Pfad wie Deutsch |
| Liste falten | `unicodedata`-Fold | tantivy-Kette mit `ascii_fold` | nur so ist Liste = Token |
| Digest | eigener Hash über die Quelldatei | `wordlist.wordlist_hash(entries)` | Digest über die GEFILTERTE Liste, damit Umsortierung keinen Umbau erzwingt |
| Umbau | eigener Reindex-Pfad | `rebuild_the_index` über `MARKS_A_REBUILD_ANSWERS` | Tausch, Wiederaufnahme, Platz-Vorprüfung, Stempel hinter dem Tausch sind in Phase 18/19 auditiert |
| RSS messen | `psutil` | `wordlist.rss_bytes()` | bestehend, keine Abhängigkeit |

## Runtime State Inventory

Die Phase ist keine Umbenennung, fügt aber persistenten Zustand hinzu. Deshalb die fünf Kategorien für die neue Marke:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `state.db` meta: neuer Schlüssel `wordlist_hash_nl`; Volume: neues Artefakt `dict/nl-full.txt` + `.sha256` nur bei aktivem nl. Feldinstallationen (1.2.0) tragen weder Schlüssel noch Artefakt | Code-Änderung (Legacy-Regel), keine Datenmigration |
| Live service config | CI-Instanzen und `findling-nextcloud` (Haus-Box) mit `FINDLING_LANGUAGES` inkl. nl: tragen `languages` mit nl, aber keine nl-Marke -> ein Umbau beim ersten Start | keine Aktion, erwarteter Umbau; im Summary benennen |
| OS-registered state | Keine: kein Cron, kein Dienst trägt den Namen (Box-Cron betrifft nur das Messrunbook) | keine |
| Secrets/env vars | Keine neue Variable empfohlen; `FINDLING_LANGUAGES` bleibt der einzige Auslöser | keine |
| Build artifacts | Laufende `rebuild`-Zielverzeichnisse tragen `.rebuild-for` mit dem Fingerabdruck der sechs Marken; eine siebte Marke ändert den Fingerabdruck, ein halb gefülltes Ziel aus der Zeit davor wird verworfen (H-18-02-Logik) | nur in Hausinstallationen denkbar, im Summary benennen |

## Common Pitfalls

### Pitfall 1: Die Marke wird gesät und schweigt
**What goes wrong:** `open_store(meta=expected)` schreibt `wordlist_hash_nl` mit dem erwarteten Digest, `version_mismatch` meldet nie etwas, der Umbau startet nie, `body_nl` bleibt mit der alten Kette tokenisiert.
**How to avoid:** `seed.pop(_DUTCH_MARK)` neben `seed.pop(_LANGUAGES_MARK)`; Test, der die Marke NICHT setzt und beide Richtungen prüft.
**Warning signs:** Ein Test, der die Marke setzt und dann "kein Drift" prüft.

### Pitfall 2: `test_no_mark_appeared_and_none_went_missing` wird "grün gemacht"
**What goes wrong:** Der Test hält `ALL_MARKS` bei sechs und sagt wörtlich "A seventh mark is a rebuild for everyone". Wer `ALL_MARKS` einfach auf sieben erweitert, verliert die Aussage.
**How to avoid:** Wie bei der sechsten Marke: die siebte als begründete Ausnahme eintragen, mit Verweis auf den Legacy-Beweis in `test_store_metadata.py`, und `GOLD_V1_3` um den Wert `off` ergänzen. "Store upgrade 5" in `deploy-harp.yml` (1.2.0 -> aktuell, de,en, prüft die ABWESENHEIT des Drift-Signals) ist dann der End-to-End-Beweis von Kriterium 4, ohne neuen CI-Schritt.

### Pitfall 3: Splitter vor dem Fold mit roher Liste
**What goes wrong:** Rezept A. Die flache Schreibung (`coordinatiecentrum`) bleibt ganz, und die in Phase 17 gemessene Fold-Position verschiebt sich, womit die Phase-17-Kettentabellen für nl neu gemessen werden müssten.
**How to avoid:** Rezept B: `lowercase -> ascii_fold -> split_compound(gefaltet) -> custom_stopword(TUSSENKLANKEN) -> stopword("dutch") -> custom_stopword(Ergänzung, für nl leer) -> remove_long(48) -> stemmer("dutch")`. `remove_long` bleibt HINTER dem Splitter (deutscher Befund: davor verschwindet ein 63-Zeichen-Wort komplett).

### Pitfall 4: Die Phase-17-Gates für nl werden rot oder blind
**What goes wrong:** `test_language_analyzers.py` und die Kettenmessung (`scripts/dev/chain_probe.py`, `backend/tests/fixtures/chain_cases_nl.txt`, `chain_known_losses_nl.txt`) prüfen die nl-Kette ohne Splitter. Mit Splitter ändern sich Token für Komposita in den Fixtures.
**How to avoid:** Die Snowball-Fabrik `snowball_analyzer("dutch")` bleibt unverändert (sie ist die Kette ohne nl); die Splitter-Kette ist eine eigene Fabrik. Die Phase-17-Tabellen laufen gegen beide und dokumentieren die Differenz, statt eine davon still zu ersetzen.

### Pitfall 5: Tussenklank `en` doppelt, `e` und `s` als nackte Terme
**What goes wrong:** Ohne `custom_stopword(TUSSENKLANKEN)` landen `s` und `e` als Terme im Index (deutsches Gegenstück: `kundig, s, frist`). `en` ist zusätzlich ein niederländisches Stoppwort und fällt ohnehin.
**How to avoid:** Ein Literal `TUSSENKLANKEN`, zweimal verwendet; Test auf "kein Token der Länge 1 aus einem Kompositum".

### Pitfall 6: `dictionaries-common` fragt beim Build
**What goes wrong:** Mit zwei Wortlisten (`wngerman` und `wdutch`) will `dictionaries-common` per debconf eine Standardliste wählen. Im Research-Build ging es ohne Rückfrage durch (kein TTY, debconf fällt zurück); `/usr/share/dict/words` zeigt auf `/etc/dictionaries-common/words`.
**How to avoid:** `DEBIAN_FRONTEND=noninteractive` im RUN setzen; Findling liest ausschließlich `/usr/share/dict/dutch` und `/usr/share/dict/ngerman`, nie `words`.

### Pitfall 7: Treffer ohne Auszug für falsch halten
**What goes wrong:** Ein Treffer nur über `body_nl` kommt ohne Snippet zurück, weil der Auszug aus `body_de` geschnitten wird (19-RESEARCH M-4, dokumentiert im Language-proof-Schritt).
**How to avoid:** Der CI-Fall prüft `entries | length >= 1` und nie die Subline, wie die vier bestehenden Fälle; der Gate-Test `test_language_proof_steps.py` erzwingt das schon.

### Pitfall 8: Der Vollreindex-Ausweg stempelt Verzeichnismarken nicht
**What goes wrong:** Mit `FINDLING_REBUILD_FALLBACK=fullreindex` ruft `rebuild_the_index` `start_rebuild_on_drift`; `stamp_after_rebuild` überspringt `_MARKS_OF_A_DIRECTORY`. Nach aktuellem Code-Stand schreibt in diesem Pfad niemand `schema_version`/`languages`, und die nl-Marke erbt das.
**How to avoid:** Vor dem Bau prüfen, ob das für die Sprachmarke ein bekannter, entschiedener Zustand ist (Open Question 4). Die nl-Marke bekommt exakt dieselbe Behandlung, keine eigene Sonderlösung.

## Code Examples

### Querprobe CI-Fall (gemessen 25.09.2026, ausgelieferte de/en/nl-Fabriken plus Prototyp-Splitterkette)
```
Dokument: "De gemeentebelastingen voor dit jaar zijn verhoogd."
Frage "belasting":
  de        doc [de, gemeentebelasting, voor, dit, jaar, zijn, verhoogd]  q [belasting]  kein Treffer
  en        doc [de, gemeentebelastingen, voor, dit, jaar, zijn, verhoogd] q [belast]    kein Treffer
  nl ohne   doc [gemeentebelast, jar, verhoogd]                            q [belast]    kein Treffer
  nl mit    doc [gemeent, belast, jar, verhoogd]                           q [belast]    TREFFER
Frage "belastingen" und "gemeente": ebenfalls nur "nl mit".
```
Der Satz enthält kein Wort, das ein anderer Beweis des Workflows zählt; die Frage ist reines ASCII.

### Rezept B 4-14 (Prototyp, als Vorlage für `wordlist_nl.load_constituents_nl`)
```python
# Source: Research-Sonde 2026-09-25, Muster backend/src/findling/index/wordlist.py
from tantivy import Filter, TextAnalyzerBuilder, Tokenizer

TUSSENKLANKEN = ("s", "e", "en")
MIN_LEN, MAX_LEN = 4, 14

_FOLD = TextAnalyzerBuilder(Tokenizer.simple()).filter(Filter.lowercase()).filter(Filter.ascii_fold()).build()

def load_constituents_nl(source: Path) -> list[str]:
    words: set[str] = set()
    for word in source.read_text(encoding="utf-8", errors="replace").split("\n"):
        word = word.strip()
        if not word or not word.isalpha() or not MIN_LEN <= len(word) <= MAX_LEN:
            continue
        tokens = _FOLD.analyze(word)
        if len(tokens) == 1:
            words.add(tokens[0])
    words.update(TUSSENKLANKEN)
    return sorted(words)
```
Achtung: zeilenweise lesen (`split("\n")`), nicht `split()`; die Quelle hat 4.380 Zeilen mit Leerzeichen, die sonst in Einzelwörter zerfallen und die Liste verfälschen. Das Fenster wird auf die UNGEFALTETE Länge angewandt (so gemessen).

### Die Kette (Prototyp)
```python
def dutch_analyzer(constituents: Sequence[str]) -> TextAnalyzer:
    return (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.ascii_fold())                 # Position 2 wie Phase 17
        .filter(Filter.split_compound(list(constituents)))
        .filter(Filter.custom_stopword(list(TUSSENKLANKEN)))
        .filter(Filter.stopword("dutch"))
        .filter(Filter.custom_stopword(list(FOLDED_STOPWORDS["dutch"])))  # für nl leer, gemessen no-op
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer("dutch"))
        .build()
    )
```

### Legacy-Regel der Marke
```python
def _dutch_list_is_legacy(stored: str | None, expected: str) -> bool:
    # No release up to 1.2.0 could fill body_nl, and no release before this
    # phase split Dutch compounds, so an absent mark is compatible with an
    # expectation that says "no Dutch list" and with nothing else.
    if stored is not None:
        return False
    return expected == DUTCH_LIST_OFF
```

### CI-Fall im bestehenden Schritt "Language proof" (`deploy-harp.yml` ab Zeile 829)
Ein fünftes Dokument, nicht ein fünfter Schritt (die vier Ketten und die Vorbedingung `languagesActive == "de,en,es,it,nl,pt"` stehen schon):
```sh
printf 'De gemeentebelastingen voor dit jaar zijn verhoogd.\n' \
  > "${RUNNER_TEMP}/language-proof-nl-compound.txt"
# im case der Poll-Schleife:  nlc) term=belasting ;;
```
Der Kommentarblock muss die Querprobe oben zitieren ("red without split_compound, measured 2026-09-25"), wie es die deutschen Fälle 8 bis 10 in `integration.yml` tun. `backend/tests/test_language_proof_steps.py` liest den Schritt als Text und muss den fünften Fall kennen.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| "rund 23 MB" für einen Automaten | deutsch gemessen 41,9 MB Automat + 21,9 MB Liste; niederländisch 17,6 bzw. 37,2 MB | grundlast-fein (Sept. 2026), diese Research | Kriterium 3 mit echten Zahlen führen |
| nl-Kette ohne Splitter (Phase 17-19) | nl-Kette mit Splitter nur bei aktivem nl | diese Phase | eigene Marke statt `ANALYZER_VERSION` |
| Lizenzangabe "BSD-3 + CC-BY-3.0 laut Debian-copyright" | Debian: CC-BY-3.0; upstream: BSD-3 und/oder CC BY 3.0 | diese Research | THIRD-PARTY.md korrekt zitieren |

**Deprecated/outdated:** keine Bibliotheksänderung; `tantivy` 0.26.2 bleibt.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Die amd64-RSS-Zahl gilt auf nativem arm64 bis auf unter 1 MB (Präzedenz deutscher Automat) | RAM | Budget-Reserve schrumpft; bei 150 MB Reserve unkritisch, native Zahl in Phase 22 nachmessen |
| A2 | Die Kombination "COPYING.wdutch + Namensnennung + Bearbeitungshinweis" erfüllt BSD-3 und CC BY 3.0 zugleich und ist mit AGPL-3.0-Verteilung vereinbar | Lizenzlage | Nachbesserung an THIRD-PARTY.md/Abbild; keine Codefolge |
| A3 | Aufwand 6 bis 8 Pläne | Entscheidungsvorlage | Terminplanung; das Tor entscheidet ohnehin |
| A4 | Die 28/33 selbst gewählten Testfälle sind repräsentativ für niederländische Verwaltungssprache; kein Muttersprachler hat sie gelesen | Rezeptmessung | Trefferquote im Feld weicht ab; Fallliste im Plan von einem Muttersprachler gegenlesen lassen oder als Vorbehalt datieren (wie die Kataloge in Phase 20) |
| A5 | Unter FULL_REINDEX_FALLBACK werden Verzeichnismarken nicht gestempelt | Pitfall 8 | Aus Code gelesen, nicht per Test belegt; vor dem Bau verifizieren |

## Open Questions (RESOLVED)

1. **Lizenzwahl BSD-3-Clause oder CC BY 3.0 (oder beide nennen)?**
   - What we know: upstream erlaubt beides nach Wahl; Debian nennt CC-BY-3.0; beide permissiv.
   - What's unclear: welche Formulierung der Owner in THIRD-PARTY.md und Store-Text will.
   - Recommendation: beide nennen, CC-BY-3.0 als die von Debian ausgewiesene führen, Pflichten beider erfüllen. Entscheid ins Tor-Dokument.
   - RESOLVED: Teilentscheid in 21-GO-ENTSCHEID.md (CC-BY-3.0 laut Debian-Lizenzdatei, Upstream-Wahlfreiheit BSD-3/CC-BY-3.0 als Anmerkung); umgesetzt in Plan 21-02 (THIRD-PARTY.md).
2. **Niederländische Liste im Prozess halten (37,2 MB) oder nach dem Bau freigeben (17,6 MB)?**
   - What we know: die Suchseite braucht nur den Digest; der deutsche Cache existiert, weil `build_artifact()` auf der Suchseite ein zweites Mal gerufen wird.
   - Recommendation: freigeben; Digest aus der `.sha256`-Datei mit Identitätsschlüssel (Pfad, Digest, Größe, mtime) cachen, Automat-Singleton je Digest wie Deutsch. Zähler `read_count`/`build_count` als Testhebel übernehmen.
   - RESOLVED: Teilentscheid in 21-GO-ENTSCHEID.md (Liste nach dem Bau freigeben); umgesetzt in Plan 21-03, gemessen in Plan 21-04.
3. **Fenster 4-14 oder 4-12?**
   - Recommendation: 4-14 (21/28, 0 Fehlzerlegungen). 4-12 bringt 4 Treffer mehr und einen Junk-Term; das ist das verworfene deutsche Rezept D. Entscheid mit der Zahlentabelle ins Tor-Dokument.
   - RESOLVED: Teilentscheid in 21-GO-ENTSCHEID.md (Rezept B, Fenster 4-14); umgesetzt in Plan 21-03.
4. **Stempelt der `fullreindex`-Ausweg die Verzeichnismarken?**
   - What we know: `stamp_after_rebuild` überspringt `_MARKS_OF_A_DIRECTORY`, `stamp_after_swap` läuft nur im Band-Umbau.
   - Recommendation: Der Planer prüft das mit einem Test gegen den bestehenden Code, bevor die nl-Marke dazukommt; ist es eine bekannte Grenze, erbt die nl-Marke sie dokumentiert.
   - RESOLVED: per Test in Plan 21-01 (D-08-Stempeltest); die nl-Marke erbt das Ergebnis in Plan 21-06.
5. **Zeigt die Adminseite den nl-Digest (`wordlistHashNl`)?**
   - What we know: `status.py` zeigt `wordlistHash`; `test_admin_ui_contract.py` hält Schlüssellisten.
   - Recommendation: Discretion; nur wenn es billig ist, sonst Banner genügt.
   - RESOLVED: Claude's Discretion laut 21-CONTEXT.md; Entscheid in Plan 21-06: `wordlistHashNl` nur in tools/index_status.py, Adminseite ohne eigenen Schlüssel, Banner genügt.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker (Messcontainer, Abbild) | Rezept- und RAM-Messung, Dockerfile | ✓ | 29.5.2, x86_64, 12 CPU, 8 GB | n/a |
| arm64-Emulation (qemu/binfmt) | Plattformgleichheit der Liste | ✓ | lief im Research | nur für Byte-Gleichheit, nicht für RSS |
| uv | Suite, Gates | ✓ | 0.11.7 | n/a |
| `python:3.13-slim-trixie` + `wdutch=1:2.20.19+1-3` | Messung | ✓ (gezogen, gebaut) | s.o. | n/a |
| native ARM-Box | native RSS-Zahl | ✗ | n/a | Präzedenz grundlast-fein; Nachmessung in Phase 22 |

**Missing dependencies with no fallback:** keine
**Missing dependencies with fallback:** native ARM-Messung (Phase 22)

## Security Domain

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein | unverändert |
| V3 Session Management | nein | unverändert |
| V4 Access Control | nein | PHP-Nachprüfung bleibt einzige Autorität; neues Feld wird nicht angelegt |
| V5 Input Validation | ja | Artefakt fail closed gegen eigenen Digest; Sprachcode nur über `SUPPORTED_LANGUAGES`/`LANGUAGE_ALLOWLIST` |
| V6 Cryptography | nein | SHA-256 nur als Identität, nicht als Sicherheitsprimitive |
| V10/V14 Supply Chain, Config | ja | apt-Pin mit Epoche, `docker.yml`-Gate auf Version, Zeilen, Bytes, Lizenzdatei |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| manipuliertes `nl-full.txt` auf dem Volume | Tampering | Digest-Vergleich fail closed, Identitätsschlüssel inkl. Größe und mtime (T-06.1-13/14-Muster) |
| gesäte Marke unterdrückt fälligen Umbau | Repudiation/Integrity | Saat-Ausnahme, Test ohne gesetzte Marke (T-18-05-01) |
| Speichererschöpfung durch zweiten Automaten | DoS | nur bei aktivem nl, Singleton je Digest, Build-Zähler, Budgetmessung |
| stille Paketänderung ändert Tokenisierung | Tampering | exakter apt-Pin, CI-Gate auf Zeilen/Bytes, Digest über gefilterte Liste |
| Messausgabe mit Nutzerinhalt | Information Disclosure | Messmodi geben nur Zahlen und Repo-Fälle aus (T-02-14) |
| Lizenzpflicht nicht erfüllt | (Compliance) | `COPYING.wdutch` fail closed im Build, THIRD-PARTY.md |

## Vorschlag Plan-Schnitt (für den Planer, keine Vorgabe)

1. Owner-Tor: Entscheiddokument mit den Fakten oben plus Open Questions 1 bis 3, Checkpoint, datierter Vollzug. Blockiert alles.
2. Messwerkzeug im Repo: `measure_compounds_nl.sh`, `compound_probe_nl.py`, `compound_cases_nl.txt`, Rohdaten und Messbericht `docs/measurements/2026-09-komposita-nl/` (reproduziert die Zahlen dieser Research), Fixture `constituents_nl.txt` per Sonde.
3. `wordlist_nl.py` + Tests (isoliert, ohne Wirkung auf den Container).
4. `dutch_analyzer`/`cached_dutch_analyzer` + Kettentests, Phase-17-Tabellen gegen beide nl-Ketten, Docstring-Ergänzung zu `ANALYZER_VERSION`.
5. Abbild: Dockerfile-Block, `docker.yml`-Gate, THIRD-PARTY.md, `COPYING.wdutch`.
6. Verdrahtung: gated Registrierung, siebte Marke (Store, open, rebuild, alle Aufrufer von `expected_versions`), Upgrade-Kompatibilitätstests, Zustandstabelle als Tests.
7. CI-Fall im Language-proof-Schritt + `test_language_proof_steps.py`.
8. Doku: `docs/language-analyzers.md` (Absatz "Compounds are German only"), `docs/performance.md` (Posten + Richtigstellung 23 MB), Schlussabschnitt; danach Review/Audit.

## Sources

### Primary (HIGH confidence)
- sources.debian.org API `dutch` (Versionen je Suite), `debian/copyright`, `debian/control`, `debian/rules`, `debian/wdutch.install`, `convert`, `wordlist/LICENSE.txt`, `wordlist/README.md`, `wordlist/datetimeversion.txt` von `dutch` 1:2.20.19+1-3
- Eigene Messung 25.09.2026 im Container `python:3.13-slim-trixie` + `wdutch=1:2.20.19+1-3` + `tantivy==0.26.2` (Rezepte, RSS, Querprobe über die ausgelieferten Fabriken aus `backend/src`)
- Codebasis: `backend/src/findling/index/{wordlist,analyzer,open,rebuild,schema}.py`, `store/repo.py`, `api/resources.py`, `backend/Dockerfile`, `.github/workflows/{deploy-harp,docker,integration}.yml`, `backend/tests/test_upgrade_compatibility.py`, `backend/tests/conftest.py`
- Präzedenz-Doku: `docs/german-analyzer.md`, `docs/measurements/2026-09-komposita-rezept-a/README.md`, `docs/measurements/2026-09-grundlast-fein/README.md`, `docs/performance.md`, `docs/language-analyzers.md`, `.planning/phases/17-*/17-GRUNDSATZ-ENTSCHEID.md` (E-17-6 Option a), `.planning/phases/18-*/18-RESEARCH.md`

### Secondary (MEDIUM confidence)
- `.planning/research/FEATURES.md` und `SUMMARY.md` (Milestone-Recherche; Lizenzzitat hier korrigiert)

### Tertiary (LOW confidence)
- qemu-arm64-RSS-Zahlen (nur als Emulationsartefakt aufgeführt)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, Paket, Pin, Datei und Digest in zwei Plattform-Abbildern verifiziert
- Architecture: HIGH, jede Markenstelle im Code gelesen; Zustandstabelle aus `version_mismatch`/Stempeln abgeleitet
- Pitfalls: HIGH für 1 bis 7 (Code + Messung), MEDIUM für 8 (Code gelesen, nicht getestet)
- RAM: HIGH auf amd64, MEDIUM für ARM

**Research date:** 2026-09-25
**Valid until:** 2026-10-25 (Paket in trixie stabil; bei Bewegung von `wdutch` in trixie schlägt der Pin laut fehl)
