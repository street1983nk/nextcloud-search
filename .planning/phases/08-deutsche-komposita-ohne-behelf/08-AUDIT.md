---
phase: 08-deutsche-komposita-ohne-behelf
audited: 2026-09-08
diff: b7f7b01..643d574
files_reviewed: 28
findings:
  critical: 0
  high: 1
  medium: 7
  low: 10
  total: 18
status: issues_found
fix_run: 2026-09-08
fix_commits: 5b4aff4..880c217
fixed: [H-01, M-01, M-02, M-03, M-04, M-06, M-07, L-10]
still_open: [M-05]
---

# Phase 08: Security-, Bug- und Performance-Audit

**Umfang:** `git diff b7f7b01..643d574`, 28 Dateien, 3584 Zeilen dazu, 243 weg.
Produktiver Code sind sieben Kommentarzeilen in
`backend/src/findling/tools/index_status.py`; alles andere sind Tests,
CI-Schritte, Doku, Messdaten und zwei Dev-Skripte.

**Was gegengeprueft wurde, nicht nur gelesen:**

- Volle Suite lokal gefahren: `1744 passed, 15 skipped in 179,60 s`. Die im
  Auftrag genannte Zahl 1744 stimmt, das Plus von 31 Faellen laesst sich Fall
  fuer Fall auf die vier Testdateien zurueckrechnen.
- `ruff check`, `ruff format --check`, `pyright` (Projektkonfiguration, venv)
  ueber `src` und `tests`: alle drei gruen, null Befunde.
- Die Testtabelle `COMPOUNDS` (21 Zeilen) und `UNSPLIT` (10 Zeilen) maschinell
  gegen `docs/measurements/2026-09-komposita-rezept-a/rohdaten/tokens-rezept-a.tsv`
  gehalten: **null Abweichungen**, alle 31 behaupteten Wortformen stehen in den
  46 gemessenen Faellen.
- Die ausgelieferte Fixture (223 Eintraege) gegen die gemessene Teilmenge
  (194 Eintraege) tokenweise ueber alle 46 Faelle verglichen: **null
  Abweichungen**. Die Vereinigung ist also tatsaechlich unschaedlich.
- Die drei neuen CI-Suchbegriffe mit und ohne `Filter.split_compound` gegen den
  echten Korpustext gefahren. Ergebnis siehe H-01.
- Die zwei Shell-Ebenen des neuen docker.yml-Schritts von Hand durchparst
  (aeussere bash-Einfachquotes, innere `sh -c`-Auswertung von `\${Version}`).

---

## Sicherheit

**Kein Befund ab MEDIUM.** Die neuen CI-Schritte sind sauber gebaut. Im
Einzelnen geprueft und in Ordnung:

- `.github/workflows/docker.yml:236-296`: `DIGEST` kommt ueber den
  `env`-Block herein, nicht ueber `${{ }}` im Skriptkoerper. Das ist genau der
  Weg, der Script-Injection ausschliesst. `"${IMAGE}@${DIGEST}"` ist gequotet.
- Das innere Skript steht in Einfachquotes, also fasst die aeussere Shell nichts
  davon an. `dpkg-query -W -f=\${Version}` ist ueber beide Ebenen korrekt: der
  Backslash bleibt in Einfachquotes stehen, die innere `sh` macht daraus das
  Literal `${Version}`, das dpkg als Feldvorlage braucht. Kein Fehler.
- `--rm --network none`, keine Volume-Mounts, kein Docker-Socket. Der Container
  bekommt nichts, was er missbrauchen koennte.
- Keine Secrets in Logs. `head -7` gibt nur den Lizenzkopf aus.
- `.github/workflows/integration.yml:1500-1537`: die drei neuen Faelle benutzen
  ausschliesslich `${VARIABLE}` aus dem `env`-Block, kein `${{ }}` im
  Skriptkoerper. `curl --data-urlencode` kodiert den Suchbegriff korrekt.
- `scripts/dev/measure_compounds.sh`: `set -eu`, alle Variablen gequotet, die
  einzige ungequotete Expansion (`$PROBE_ARGS`) traegt einen vom Skript selbst
  gesetzten Festwert und ist mit einer `shellcheck disable`-Zeile begruendet.
  Alle Lesemounts sind `:ro`.
- `scripts/dev/compound_probe.py` liest nur Repositoriumspfade und die
  Debian-Wortliste, nie `state.db`, nie einen Index, nie eine Nutzerdatei. Die
  Sicherheitsregel aus dem Modulkopf haelt.

Einen Restpunkt siehe L-08 (der Schritt laeuft nicht auf Pull Requests).

---

## HIGH

### H-01: CI-Sprachfall 8 beweist die Zerlegung nicht, ist aber das Leitbeispiel des Erfolgskriteriums

**Dateien:**
`.github/workflows/integration.yml:1500-1516`,
`.planning/REQUIREMENTS.md:16`,
`.planning/ROADMAP.md` (Erfolgskriterium 1 der Phase 8),
`backend/tests/test_corpus_terms.py:52-53`

**Fehlerszenario:** `14-pacht-mit-anhang.pdf` traegt das Wort `Vereinbarung`
**zweimal eigenstaendig in der Textebene**, nicht nur als zweiten Teil von
`Pachtvereinbarung`. Wortwoertlich aus dem Generator gelesen:

```
'Sonnenhang wird die nachstehende Vereinbarung geschlossen.'
'Die Anlagen 1 bis 3 dieser Vereinbarung liegen als Kopie der'
```

Damit trifft die Suche nach `Vereinbarung` diese Datei auch dann, wenn
`Filter.split_compound` vollstaendig aus der Kette faellt. Gegengeprueft mit
der ausgelieferten Kette gegen den echten Korpustext, einmal mit und einmal
ohne den Splitter:

| Fall | Suchbegriff | Datei | mit Splitter | ohne Splitter |
|---|---|---|---|---|
| 1 | Genehmigung | 09-bescheid.pdf | Treffer | kein Treffer |
| 2 | Frist | 10-kuendigung.docx | Treffer | kein Treffer |
| **8** | **Vereinbarung** | **14-pacht-mit-anhang.pdf** | **Treffer** | **Treffer** |
| 9 | Auszug | 16-oesterreich-mitteilung.pdf | Treffer | kein Treffer |
| 10 | Erinnerung | 30-nur-ein-bild.pdf | Treffer | kein Treffer |

Fall 8 ist der einzige der fuenf, der bei entferntem Splitter gruen bleibt. Das
waere fuer sich genommen ein LOW-Schoenheitsfehler, denn der Workflow-Kommentar
sagt es sogar selbst ("stands on the widest ground"). Es wird zum HIGH-Befund,
weil derselbe Fall an drei Stellen zum **Beleg** erhoben wird:

- `REQUIREMENTS.md` QUAL-02: `z. B. "Vereinbarung" findet "Pachtvereinbarung"`
- `ROADMAP.md` Erfolgskriterium 1: dieselbe Formulierung, zuerst genannt
- `integration.yml:26`: `ten German language cases, five of them a compound
  found through one of its parts`

Es sind vier, nicht fuenf. Und das Leitbeispiel des umformulierten
Erfolgskriteriums ist ausgerechnet der Fall, der ohne die Funktion, die er
belegen soll, gruen bleibt. Nach dem Wechsel weg von `Genehmigung` findet
`Baugenehmigung` ist das die zweite Umformulierung, die den Beleg schwaecht
statt ihn zu haerten.

Zusaetzlich haelt kein Test die Aussage lokal: `test_corpus_terms.py` prueft
Einmaligkeit und Tokenisierbarkeit, aber nicht, ob der Treffer am Splitter
haengt. `test_index_open.py::test_without_the_splitter_the_constituent_finds_nothing`
macht diesen Beweis nur fuer `frist`.

**Fix-Empfehlung, eine von zwei:**

a) Leitbeispiel tauschen. `REQUIREMENTS.md` QUAL-02 und ROADMAP-Kriterium 1
   nennen `Auszug` findet `Grundbuchsauszug` und `Erinnerung` findet
   `Zahlungserinnerung` zuerst; `Vereinbarung` bleibt als dritter Fall stehen,
   ausdruecklich als der breite und nicht als der scharfe. `integration.yml:26`
   auf `four of them a compound found through one of its parts` korrigieren, und
   im Kommentar zu Fall 8 einen Satz ergaenzen, dass dieser Fall die Zerlegung
   nicht isoliert.

b) Fall 8 scharf machen: den Suchbegriff auf einen Konstituenten umstellen, der
   in keiner Datei eigenstaendig steht. `Belehrung` aus
   `Rechtsmittelbelehrung` (`15-schweiz-baubewilligung.pdf`) ist bereits in
   Abschnitt 5 des Messberichts als tragfaehiger Kandidat gemessen; laut
   Befund 2 desselben Berichts muss er dann in die Einmaligkeits-Tabelle von
   `testdata/CORPUS.md` und in `UNIQUE_TERMS` nachgetragen werden.

Variante a ist billiger und ehrlich; b macht das CI-Set wirklich staerker.

---

## MEDIUM

### M-01: python.yml laeuft nicht, wenn scripts/dev/build_corpus.py sich aendert, obwohl die Suite es jetzt zur Laufzeit laedt

**Dateien:** `.github/workflows/python.yml:6-13`,
`backend/tests/test_corpus_terms.py:89-97`

**Fehlerszenario:** `test_corpus_terms.py` laedt `scripts/dev/build_corpus.py`
per `importlib.util.spec_from_file_location` und greift auf `FILES`,
`_searchable_text` und `UNIQUE_TERMS` zu. Ein Commit, der **nur**
`scripts/dev/build_corpus.py` anfasst (etwa eine neue Korpusdatei oder eine
Umbenennung von `_searchable_text`), passt auf keinen Pfadfilter von
`python.yml` (`backend/**`, `.github/workflows/python.yml`). Die Python-Gates
laufen also nicht, waehrend die Suite bereits rot waere. `integration.yml`
fuehrt `scripts/dev/build_corpus.py` seit Phase 3 in seiner Pfadliste, genau aus
diesem Grund; `python.yml` wurde in dieser Phase nicht nachgezogen.

Praktische Folge: der Bruch faellt erst beim naechsten Commit auf, der zufaellig
`backend/**` anfasst, und wird dort dem falschen Commit angelastet.

**Fix:** In `.github/workflows/python.yml` beide Pfadlisten (`push` und
`pull_request`) um `- 'scripts/dev/build_corpus.py'` ergaenzen, mit demselben
Begruendungskommentar, den `integration.yml` bereits traegt.

### M-02: scripts/dev/compound_probe.py faellt durch kein einziges Qualitaetsgate

**Dateien:** `scripts/dev/compound_probe.py` (196 Zeilen, neu),
`.github/workflows/python.yml:31-33,64-73`, `backend/pyproject.toml:110-117`

**Fehlerszenario:** Der Gates-Job hat `defaults.run.working-directory: backend`,
also prueft `uv run ruff check .` nur `backend/`. `[tool.pyright] include =
["src", "tests"]` und `uv run vulture src tests` schliessen `scripts/` ebenfalls
aus. Die neue Datei liegt in `scripts/dev/` und wird damit von **keinem** der
vier Gates beruehrt (ruff, ruff format, pyright, vulture). Das verletzt die
Owner-Regel aus `~/.claude/CLAUDE.md` ("Python-Qualitaetsgates in ALLEN
Python-Projekten ... CI-Steps") und die Projektregel in `CLAUDE.md:19`.

Der Diff verschlimmert die bestehende Luecke, weil er sie um eine neue Datei
erweitert, deren Ausgabe die Messgrundlage der ganzen Phase ist. Ein Tippfehler
in `_tsv` oder `_numbers` faellt niemandem auf, bevor die Zahlen in der Doku
stehen. (Von Hand gegengeprueft: ruff und ruff format sind auf der Datei heute
gruen, pyright meldet auf ihr nur Import-Rauschen ohne venv. Es geht um die
fehlende Automatik, nicht um einen aktuellen Befund.)

**Fix:** Entweder `working-directory` fuer die vier Gate-Schritte auf das
Repositoriumswurzelverzeichnis heben und `include`/`vulture`-Pfade um
`../scripts` erweitern, oder einen zweiten kurzen Job `scripts gates` in
`python.yml` anlegen, der `ruff check scripts`, `ruff format --check scripts`
und `pyright scripts` fahrt. Der Pfadfilter aus M-01 wird dann ohnehin
gebraucht.

### M-03: build_corpus.py wird pro Suite-Lauf mehrfach vollstaendig ausgefuehrt, Phase 8 legt rund 12 Sekunden drauf

**Datei:** `backend/tests/test_corpus_terms.py:89-97,115-123,214-222`

**Fehlerszenario:** `_load_build_corpus()` fuehrt das Skript per `exec_module`
komplett aus. `FILES` wird dort auf Modulebene gebaut, das heisst: alle 39
Korpusdateien werden erzeugt, inklusive AES-Verschluesselung, ZIP-Bombe und
tief verschachteltem PDF. Das Modul ruft die Funktion **zweimal**, einmal aus
der Fixture `searchable` und einmal aus
`test_every_ci_term_is_carried_by_the_uniqueness_check_of_the_generator`. Beide
Male wird ein neues Modulobjekt gebaut, es gibt keinen Cache.

Gemessen mit `--durations`:

```
5,95 s  call   test_every_ci_term_is_carried_by_the_uniqueness_check_of_the_generator
5,94 s  setup  test_a_ci_term_stands_in_exactly_one_corpus_file[Auszug-...]
```

Rund 11,9 s von 179,6 s Suitezeit, davon **rund 6 s glatt vermeidbar**.
Zusaetzlicher Befund am Rande: `test_ocr_quality.py` macht dasselbe noch dreimal
(3 x rund 5,9 s), so dass der Generator pro Lauf fuenfmal ausgefuehrt wird, rund
35 s oder ein Fuenftel der Gesamtzeit.

**Fix:** `_load_build_corpus` mit `functools.cache` dekorieren, das kostet eine
Zeile und holt die 6 s der Phase zurueck. Sauberer und mit dem groesseren
Gewinn: eine `session`-Fixture in `backend/tests/conftest.py`, die das
Generatormodul einmal laedt, und `test_corpus_terms.py` wie `test_ocr_quality.py`
darauf umstellen.

### M-04: Zwei verschiedene Mengen der Groesse 21 im selben Messbericht

**Dateien:**
`docs/measurements/2026-09-komposita-rezept-a/README.md:67` und `:210-213`,
`docs/german-analyzer.md:32-38`

**Fehlerszenario:** Abschnitt 3.1 heisst `### 3.1 Zerfaellt (21 Faelle)`; diese
21 sind die 21 von 46 Eingaben, die mehr als ein Token liefern
(`kennzahlen.txt: cases_more_than_one_token=21`). Abschnitt 4 schreibt: "von den
21 alltaeglichen Verwaltungskomposita dieser Messung zerfallen sieben nicht".
Das sind die 21 Zeilen der Tabelle `COMPOUNDS` in `test_analyzer.py`, von denen
14 zerfallen. Wer beide Saetze nebeneinanderlegt, rechnet 21 minus 7 gleich 14
und steht vor dem Widerspruch zur Ueberschrift von 3.1.

`docs/german-analyzer.md` traegt denselben Satz noch einmal ("of twenty one
everyday administrative compounds, seven do not come apart") und legt eine
zweite Ungenauigkeit drauf: 16 der 21 sind genau jene Woerter, die dasselbe
Dokument zwei Absaetze weiter oben als "long, rare words" bezeichnet.
`Rindfleischetikettierungsueberwachungsaufgabenuebertragungsgesetz` als
"everyday administrative compound" zu fuehren, entwertet die Aussage, die der
Satz treffen will.

**Fix:** Die beiden Mengen benennen statt zaehlen.
Ueberschrift 3.1 auf `### 3.1 Zerfaellt (21 der 46 Eingaben)`, Abschnitt 4 auf
"von den 21 Verwaltungskomposita der Waechtertabelle (16 lange aus der
Recherche plus 5 kurze aus dieser Messung) zerfallen sieben nicht". In
`docs/german-analyzer.md` dieselbe Praezisierung, und "everyday" streichen oder
auf die fuenf neuen Kurzwoerter beschraenken.

### M-05: STATE.md widerspricht ROADMAP.md ueber den Stand der Phase

**Dateien:** `.planning/STATE.md:5-13,27-33` gegen `.planning/ROADMAP.md:38,96-109`

**Fehlerszenario:** `ROADMAP.md:38` fuehrt
`- [x] **Phase 8: ...** (completed 2026-09-08)` und alle fuenf Plaene 08-01 bis
08-05 als `[x]`. `STATE.md` steht im selben Commit-Stapel unveraendert auf:

```
status: executing
stopped_at: Completed 06-10-PLAN.md
completed_plans: 4
percent: 20
Phase: 08 (deutsche-komposita-ohne-behelf) - EXECUTING
Plan: 1 of 5
Naechster Schritt: `/gsd:plan-phase 7`
```

`STATE.md` wurde um 17:13 beim Start der Ausfuehrung geschrieben und danach nie
wieder. Der naechste Schritt zeigt auf Phase 7, die laut ROADMAP schon fertig
ist. Wer nach `/clear` `STATE.md` liest, faengt an der falschen Stelle an. Genau
dafuer ist die Datei da.

**Fix:** `STATE.md` auf den Stand von `ROADMAP.md` ziehen: `Plan: 5 of 5`,
`completed_plans` und `percent` neu rechnen, `stopped_at` auf
`Completed 08-05-PLAN.md`, `Naechster Schritt` auf die naechste offene Phase.
Und im Zuge dessen die zwei Em-Dashes entfernen, siehe L-07.

### M-06: Der Messbericht nennt eine Fixture mit 172 Eintraegen, ausgeliefert werden 223, und der Beleg der 223 steht nur in .planning

**Dateien:**
`docs/measurements/2026-09-komposita-rezept-a/README.md` Abschnitt 6,
`backend/tests/fixtures/constituents_de.txt` (223 Eintraege),
`backend/tests/test_analyzer.py:11-16`

**Fehlerszenario:** Abschnitt 6 schreibt: "Die bestehende Fixture
`backend/tests/fixtures/constituents_de.txt` mit 172 Eintraegen ist einmalig von
Hand entstanden". Nach Plan 08-04 hat dieselbe Datei 223 Eintraege, die
Vereinigung der 172 alten mit den 194 gemessenen. Der Messbericht ist die im
Docstring von `test_analyzer.py` und in `docs/german-analyzer.md` verlinkte
Quelle, und er beschreibt die Datei falsch.

Schwerer wiegt der fehlende Beleg: Der Docstring sagt "The union is not
believed, it is measured", und `docs/german-analyzer.md` verweist auf
`measure_compounds.sh --against`. Der Lauf existiert, aber sein Ergebnis
(`/opt/findling/against.txt tokenises like the full list, 223 entries`) steht
ausschliesslich in `.planning/phases/08-.../08-04-SUMMARY.md`. Unter
`docs/measurements/` gibt es keine Zeile dazu. Ein spaeterer Leser, der die
Fixture pruefen will, findet in der zitierten Quelle nur den Beweis fuer die
194er-Teilmenge.

(Unabhaengig nachgemessen: Fixture und Teilmenge liefern fuer alle 46 Faelle
byteweise dieselben Token. Die Aussage stimmt inhaltlich, nur ihr Beleg liegt am
falschen Ort.)

**Fix:** In Abschnitt 6 des Messberichts einen Absatz "Nachtrag 08-04"
ergaenzen: 223 Eintraege, Vereinigung, Datum des `--against`-Laufs, die
Ausgabezeile woertlich, und der Satz, dass mehr Eintraege nicht automatisch
besser sind. Die Zahl 172 dabei als "vor Plan 08-04" kennzeichnen.

### M-07: Kein Waechter haelt CI_TERMS gegen die gemessene Fallliste, obwohl test_analyzer.py genau diesen Waechter hat

**Datei:** `backend/tests/test_corpus_terms.py:44-80`

**Fehlerszenario:** `test_analyzer.py` traegt seit dieser Phase
`test_every_asserted_word_stands_in_the_measured_case_list`: jedes Wort, ueber
das das Modul eine Behauptung aufstellt, muss in `compound_cases_de.txt` stehen,
weil eine Behauptung ueber ein nie gemessenes Wort eine Behauptung ueber nichts
ist. `test_corpus_terms.py` hat diesen Waechter nicht, obwohl es dieselbe
Gefahr traegt und obwohl seine Aussagen direkt in einen CI-Schritt wandern.

Konkret unbelegt sind heute schon zwei Bezeichner in dieser Datei:

- `LETTER_TRAPS["Verkehr"]` (Zeile 74): `Verkehr` steht **nicht** in den 46
  gemessenen Faellen. Die Zeile `assert len(_carriers(...)) == 1` ist damit eine
  listenabhaengige Behauptung ohne Messzeile.
- `HEADLINE_AS_READ = "Ubermittlungsprotokoll"` (Zeile 86): ebenfalls kein
  gemessener Fall. Die Zusicherung
  `german.analyze(HEADLINE_AS_READ) == [HEADLINE_AS_READ.lower()]` gilt gegen
  die Fixture, nicht nachweislich gegen die echte Debian-Liste. Das ist die
  Begruendung dafuer, `Protokoll` **nicht** als CI-Fall zu bauen, also eine
  tragende Entscheidung auf ungemessenem Grund.

Der eigentliche Schaden liegt in der Zukunft: ein vierter CI-Suchbegriff kann in
`CI_TERMS` eintreten, ohne je gegen die volle Liste gefahren worden zu sein, und
das Modul waere gruen, waehrend `main` rot wird. Genau dagegen ist der Rest der
Konstruktion gebaut.

**Fix:** Denselben Waechter spiegeln:

```python
CASES = Path(__file__).resolve().parent / "fixtures" / "compound_cases_de.txt"

def test_every_word_this_module_claims_about_was_measured() -> None:
    measured = set(CASES.read_text(encoding="utf-8").split())
    asserted = [*CI_TERMS, AMBIGUOUS, *LETTER_TRAPS, HEADLINE_AS_DRAWN, HEADLINE_AS_READ]
    assert sorted(w for w in asserted if w not in measured) == []
```

Dazu `Verkehr` und `Ubermittlungsprotokoll` als Fall 47 und 48 in
`compound_cases_de.txt` aufnehmen und `measure_compounds.sh` einmal neu fahren.

---

## LOW

### L-01: Das Buchstabengatter vergleicht Rohbuchstaben, getroffen wird ueber Staemme

**Datei:** `backend/tests/test_corpus_terms.py:130-133`

`_letter_carriers` prueft `term.lower() in text`. Der Index trifft aber ueber den
Snowball-Stamm: `Vereinbarung` wird zu `vereinbar`. Eine zweite Datei mit
`vereinbaren` oder `vereinbart` koennte denselben Term erzeugen, ohne die
Buchstabenfolge `vereinbarung` zu enthalten, und das Gatter wuerde sie nicht
sehen. Der Docstring verspricht mehr, als das Gatter halten kann ("Whenever a
second file merely contains the letters of the term, some word list can split it
there"). Heute existiert keine solche Datei, das Token-Gatter faengt sie
zusaetzlich ab, also ist es kein aktueller Fehler.

**Fix:** Entweder den Stamm statt des Rohterms suchen
(`german.analyze(term)[0] in text` reicht nicht, weil der Text nicht gestemmt
ist; sauber waere ein Vergleich der Stammmenge des Textes) oder den Docstring
auf die tatsaechliche Reichweite zurueckschrauben.

### L-02: Die Gatter messen gegen Text, den der Index nie sieht, und uebersehen Text, den er sieht

**Dateien:** `backend/tests/test_corpus_terms.py:106-113`,
`scripts/dev/build_corpus.py:1722-1737`

`_searchable_text` mischt `RENDERED_TEXT` und den cp1252-Rohtext. Fuer
`14-pacht-mit-anhang.pdf` enthaelt das die **drei Anhangseiten, die laut
`testdata/CORPUS.md` bewusst ungelesen bleiben**; fuer `34-zip-bombe.docx` faellt
das 64-MiB-Mitglied heraus, fuer `07-password-protected.pdf` und
`38-aes256-verschluesselt.pdf` ist der Text verschluesselt und damit unsichtbar.
Die Einmaligkeitsaussage wird also gegen eine Textmenge gefaellt, die sich in
beide Richtungen von der indexierten unterscheidet.

Fuer die heutigen drei Terme ist es folgenlos: `Vereinbarung` steht nachweislich
in der indexierten Textebene (Tj-Strings der Seiten 1 und 2), nicht nur im
Anhang. Kuenftig kann ein Term aber ausgerechnet auf einer nie gelesenen Seite
stehen; das Gatter sagt "einmalig", CI findet null Treffer.

**Fix:** Im Docstring von `searchable` beide Abweichungen benennen, und im
Kommentar zu `CI_TERMS` festhalten, dass ein neuer Term in indexiertem Text
stehen muss, nicht nur in `RENDERED_TEXT`.

### L-03: Die Negativkontrolle hat keine Positivkontrolle auf demselben Index

**Datei:** `backend/tests/test_index_open.py:266-284`

`test_without_the_splitter_the_constituent_finds_nothing` behauptet
`_hits(without, "frist") == 0`. Eine Null beweist nur dann etwas, wenn feststeht,
dass der Index ueberhaupt etwas enthaelt. Der Beweis dafuer steht im zweiten
Teil des Tests, aber auf einem **anderen** Index (`index_dir.parent / "shipped"`).
Ein Fehler, der nur den ersten Index leer laesst, waere unsichtbar.
(`_write` ruft `index.reload()`, `_hits` holt sich einen frischen Searcher, ein
Reader-Verzoegerungsproblem gibt es also nicht.)

**Fix:** Eine Zeile ergaenzen, die den splitterlosen Index als bestueckt
nachweist, zum Beispiel
`assert _hits(without, "Kündigungsfrist") == 1` vor der Null-Behauptung.

### L-04: filter_chain sieht nur Filter, die als Attributaufruf geschrieben sind

**Datei:** `backend/tests/test_analyzer.py:522-537`

`_factory_names` nimmt ein Argument nur auf, wenn es `ast.Call` mit
`ast.Attribute` als `func` ist, also `Filter.lowercase()`. Ein
`.filter(make_stopword_filter())` oder ein aus einer Variablen gereichter Filter
wird stillschweigend uebersprungen; die Kette bliebe gleich lang und der
Waechter gruen, obwohl ein Filter dazugekommen ist. Der Docstring von
`filter_chain` erwaehnt nur die Faelle "Funktion nicht gefunden" und "keine
Kette".

**Fix:** Im ansonsten uebersprungenen Zweig einen Platzhalter anhaengen
(zum Beispiel `names.append("<unbekannt>")`), damit ein nicht erkannter Filter
die Gleichheitspruefung bricht statt sie zu ueberspringen.

### L-05: measure_compounds.sh schluckt ein fehlgeschlagenes cd bei --against

**Datei:** `scripts/dev/measure_compounds.sh:57`

```sh
AGAINST=$(CDPATH='' cd -- "$(dirname -- "$2")" && pwd)/$(basename -- "$2")
```

Scheitert das `cd`, ist der Exit-Status der Zuweisung der der **letzten**
Substitution (`basename`, also 0), `set -e` greift nicht, und `AGAINST` wird
`/dateiname`. Die Fehlermeldung lautet dann `no list at /dateiname` statt "das
Verzeichnis gibt es nicht".

**Fix:** In zwei Schritte teilen und den Status pruefen:

```sh
AGAINST_DIR=$(CDPATH='' cd -- "$(dirname -- "$2")" && pwd) || {
    echo "measure_compounds: kein Verzeichnis fuer $2" >&2
    exit 1
}
AGAINST="$AGAINST_DIR/$(basename -- "$2")"
```

### L-06: measure_compounds.sh schreibt die Messdateien als root ins Repositorium

**Datei:** `scripts/dev/measure_compounds.sh:92,105-112`

`$OUT_DIR` wird schreibbar gemountet, der Container laeuft als root. Auf einem
Linux-Entwicklerrechner gehoeren die drei erzeugten Dateien unter
`docs/measurements/.../rohdaten/` danach root und lassen sich ohne `sudo` weder
ueberschreiben noch loeschen. Der Kommentar ueber dem `set --` betont, dass alles
Gelesene `:ro` ist, sagt zum Schreibpfad aber nichts.

**Fix:** `--user "$(id -u):$(id -g)"` an den `docker run` haengen. Die
`apt-get`- und `pip`-Schritte im Container brauchen dann allerdings root; sauber
ist deshalb ein `chown` nach dem Lauf oder ein `--tmpfs`-Zwischenschritt mit
`docker cp`. Mindestens den Umstand im Skriptkopf dokumentieren.

### L-07: Em-Dashes in den neuen STATE.md-Zeilen

**Datei:** `.planning/STATE.md:24,29`

Beide vom Diff hinzugefuegten Zeilen tragen das Zeichen U+2014 (Em-Dash):
einmal zwischen `Phase 08` und dem Phasennamen, einmal zwischen dem
Phasennamen und `EXECUTING`. Das Zeichen wird hier umschrieben statt zitiert,
damit dieser Bericht die Regel nicht selbst bricht. Nachsehen mit:

```bash
grep -nP "\x{2014}" .planning/STATE.md
```

Die Projektregel in `CLAUDE.md` und die globale Owner-Regel verbieten Em- und
En-Dashes ausnahmslos. Der Rest des Diffs ist sauber, das sind die einzigen zwei
Vorkommen.

**Fix:** Durch Doppelpunkt oder Komma ersetzen. Wenn die Zeilen von einem
GSD-Werkzeug erzeugt werden, gehoert die Regel in dessen Vorlage.

### L-08: Der neue Abbild-Pruefschritt laeuft nicht auf Pull Requests

**Datei:** `.github/workflows/docker.yml:1-40,236`

`docker.yml` hat keinen `pull_request`-Ausloeser. Der neue Schritt haengt am
`build`-Job und damit an `push` auf `main`, an Tags und am Monatslauf. Eine
Aenderung an der `apt`-Zeile oder am Installationsmodus in `backend/Dockerfile`
wird also erst rot, **nachdem** sie auf `main` liegt. Das ist die bewusste
Bauweise dieses Workflows (er pusht, deshalb laeuft er nur auf vertrauten Refs,
was sicherheitstechnisch richtig ist), aber der Kommentar ueber dem Schritt
verkauft ihn als die Haelfte, die vom Vergessen unabhaengig macht, ohne den
Zeitpunkt zu nennen.

**Fix:** Zwei Saetze im Kommentar ergaenzen, wann der Schritt greift und was
stattdessen die PR-Haelfte traegt (die `test -s`-Zeilen in `backend/Dockerfile`,
die jeden Bau betreffen).

### L-09: compound_probe.py meldet fehlende Eingaben als Traceback

**Datei:** `scripts/dev/compound_probe.py:163-171`

`cases_path.read_text(...)` und `SYSTEM_WORDLIST.read_text(...)` laufen ohne
Pruefung. Fehlt eine der beiden Dateien, endet der Lauf mit einem
`FileNotFoundError`-Traceback statt mit der Art Meldung, die der Rest des
Skripts sorgfaeltig pflegt (`USAGE`, `_report`). Fuer den Aufruf ueber
`measure_compounds.sh` ist es unkritisch (das Skript prueft `$CASES` vorher),
fuer den direkten Aufruf im Container nicht.

Nebenbei: `_split_arguments` erkennt `--against` nur an erster Stelle. Ein
`compound_probe.py CASES OUT --against LIST` faellt in die Usage-Meldung, ohne zu
sagen warum.

**Fix:** Beide Pfade vor dem Lesen auf `is_file()` pruefen und mit
Rueckgabewert 2 und einer Zeile auf stderr abbrechen. Die Positionsregel fuer
`--against` in `USAGE` aufnehmen.

### L-10: Der Docstring von wordlist.py steht noch auf sechzehn Faellen

**Datei:** `backend/src/findling/index/wordlist.py:3-12`

Der Modulkopf sagt weiterhin "measured against sixteen real administrative
compounds" und "14 of 16 compounds findable through one of their parts". Nach
dieser Phase ist die Waechtertabelle 21 Zeilen lang und die Doku hat den Satz
bereits praezisiert. Die Datei liegt nicht im Diff, aber der Diff macht ihren
Docstring stehend falsch: er ist die einzige Stelle im **produktiven** Code, die
diese Zahlen fuehrt, und sie widerspricht jetzt
`docs/german-analyzer.md` und `test_analyzer.py`.

**Fix:** Die drei Zahlenangaben im Docstring auf 21 Faelle, 14 Zerlegungen und
7 benannte Grenzen ziehen und auf
`docs/measurements/2026-09-komposita-rezept-a/` verweisen.

---

## Was ausdruecklich in Ordnung ist

Damit der Bericht nicht nur die Loecher zeigt:

- **Die Messkette traegt.** Fixture, Teilmenge, Falliste, TSV, Kennzahlen und
  die Testtabellen sind untereinander widerspruchsfrei. Ich habe alle vier
  Verbindungen maschinell nachgerechnet, nicht gelesen: 21 `COMPOUNDS`-Zeilen
  gegen die TSV (null Abweichungen), 10 `UNSPLIT`-Zeilen gegen die TSV (null),
  46 Faelle gleich 46 TSV-Zeilen ohne Doppelte, Fixture gegen Teilmenge ueber
  alle 46 Faelle (null). Das ist mehr Beleg, als die meisten Projekte fuer eine
  Wortliste haben.
- **Die drei neuen Suchbegriffe sind gegen die echte Debian-Liste gemessen**,
  nicht gegen die Fixture: `Pachtvereinbarung` als `pacht, vereinbar`,
  `Zahlungserinnerung` als `zahlung, erinner`, `Grundbuchsauszug` als
  `grundbuch, auszug`, und die drei Suchbegriffe liefern genau den jeweils
  zweiten Token. Alle sechs stehen mit eigener Zeile in der TSV.
- **`Filter.split_compound` kann keinen der drei Kompositumtreffer verlieren,
  weil das Kompositum selbst ein Listeneintrag waere**: alle drei sind laenger
  als `MAX_LEN = 14` (17, 18, 16 Zeichen), also strukturell ausserhalb der
  Falle, die `Mietvertrag` und `Baugenehmigung` erwischt hat.
- **Die vier zitierten Tests im Nachmessungsbericht existieren wirklich**
  (`test_exactly_twenty_files_lie_above_the_size_cap`,
  `test_a_file_over_the_size_cap_is_skipped_a_second_time`,
  `test_no_text_layer_is_requeued_and_not_acknowledged`,
  `test_a_stored_no_text_layer_verdict_does_not_block_the_handover`), jeweils in
  der genannten Datei. Kein Verweis ins Leere.
- **Die Umformulierung der Doku korrigiert einen echten Altfehler:** die alte
  Tabelle in `docs/german-analyzer.md` fuehrte
  `Grundstuecksverkehrsgenehmigung` in ASCII-Schreibweise mit den Token der
  Umlautschreibweise. Gemessen ergibt die ASCII-Form ein einziges Token. Die
  Phase hat die Tabelle auf echte Umlaute gezogen und den Unterschied als
  benannte Grenze aufgenommen. Das ist eine Verbesserung, keine Kosmetik.
- **Test-Isolation stimmt.** `test_switching_the_dictionary_variant_asks_for_a_reindex`
  setzt `FINDLING_COMPOUND_DICT` und leert den `settings`-Cache; die
  `volume`-Fixture leert ihn beim Abbau erneut, und zwar bevor `monkeypatch` die
  Umgebung zuruecksetzt, so dass kein Wert stehen bleibt. `_MARKS` wird von
  `monkeypatch.setattr` zurueckgegeben. Kein Nachlaufen in spaetere Tests, in der
  vollen Suite gegengeprueft.
- **Keine Plattformabhaengigkeit gefunden.** Alle neuen `read_text`-Aufrufe
  geben `encoding` explizit an, alle Fixture-Leser benutzen `.split()`, das
  CRLF miterledigt. Die volle Suite laeuft auf Windows gruen.
- **Kein Debug-Rest, kein Geheimnis, kein auskommentierter Code** in den 3584
  hinzugefuegten Zeilen.

---

## Pflicht vor Phasenabschluss

Nach der Owner-Regel ("Befunde ab MEDIUM vor Phase-Abschluss fixen"):

| Befund | Aufwand | Art |
|---|---|---|
| H-01 | 20 min (Variante a) | Doku und ein Workflow-Kommentar |
| M-01 | 2 Zeilen | Pfadfilter |
| M-02 | 10 min | CI-Job oder Konfiguration |
| M-03 | 1 Zeile (`functools.cache`) | Test |
| M-04 | 15 min | Doku |
| M-05 | 10 min | STATE.md |
| M-06 | 15 min | Messbericht |
| M-07 | 10 Zeilen Test plus ein Messlauf | Test und Messung |

L-01 bis L-10 sind dokumentiert und dem Owner zur Entscheidung vorgelegt. L-07
(Em-Dashes) und L-10 (falscher Docstring im produktiven Code) sind die zwei mit
dem besten Verhaeltnis von Aufwand zu Nutzen.

---

## Status nach dem Fix-Lauf (08.09.2026)

Ein Befund, ein Commit. Alle acht Commits sitzen auf `643d574` auf.

| Befund | Status | Commit | Was daraus wurde |
|---|---|---|---|
| H-01 | **FIXED** | `5b4aff4` | CI-Fall 8 laeuft jetzt ueber `Belehrung` aus `Rechtsmittelbelehrung` (`15-schweiz-baubewilligung.pdf`). Der Mit/Ohne-Splitter-Beweis ist gefahren, Tabelle unten. `Vereinbarung` ist nicht geloescht, sondern als splitterunabhaengiger Fall umdeklariert. Alle Stellen nachgezogen: `integration.yml`, ROADMAP-Kriterium 1, QUAL-02, `testdata/CORPUS.md`, `UNIQUE_TERMS`, `test_corpus_terms.py`. Zwei neue lokale Waechter halten die Aussage. |
| M-01 | **FIXED** | `61b18a0` | `scripts/dev/build_corpus.py` steht in beiden Pfadlisten von `python.yml`. |
| M-02 | **FIXED** | `114073f` | Zwei Schritte `ruff check` und `ruff format --check` ueber `../scripts` mit `--config pyproject.toml`, Pfadfilter auf `scripts/**` erweitert. Kein pyright- und kein vulture-Zwang fuer Dev-Skripte, benannt in `docs/testing.md`. |
| M-03 | **FIXED** | `02286a3` | Session-Fixture `corpus_generator` in `conftest.py`, beide Module haengen daran. Der Generator laeuft einmal statt fuenfmal pro Lauf. |
| M-04 | **FIXED** | `7bdadd7` | Beide 21er-Mengen tragen jetzt einen Namen statt einer Zahl, die Waechtertabelle ist als 16 aus Phase 2 plus 5 aus Phase 8 aufgeschluesselt. "everyday" gilt nur noch fuer die sieben kurzen. |
| M-05 | **OFFEN, bewusst** | keiner | `STATE.md` gehoert dem Orchestrator, dieser Lauf hat sie auftragsgemaess nicht angefasst. Der Befund bleibt gueltig und ist der Nachbarbefund von L-07. |
| M-06 | **FIXED** | `55b2137` | 172 als "vor Plan 08-04" gekennzeichnet, neuer Abschnitt 6.1 mit Befehl, Ausgabezeile und Rueckgabewert des `--against`-Laufs (223 Eintraege, 48 Faelle). `test_analyzer.py` und `docs/german-analyzer.md` verweisen jetzt dorthin. |
| M-07 | **FIXED** | `fedaf0f` | `test_every_word_this_module_claims_about_was_measured` gespiegelt, `Verkehr` und `Ubermittlungsprotokoll` als Fall 47 und 48 **gemessen** statt umformuliert, Nachtrag als Abschnitt 5.1 im Messbericht. |
| L-10 | **FIXED** (LOW, im Vorbeigehen) | `880c217` | Modulkopf von `wordlist.py` um die 21 der Waechtertabelle ergaenzt. |

### Der gefahrene Mit/Ohne-Splitter-Beweis

Gemessen am 08.09.2026 mit der ausgelieferten Kette gegen die **echte
Debian-Liste** (`.dev/storage/dict/de.txt`, 276496 Eintraege, Digest
`b1f64012...`, byteweise derselbe wie in `kennzahlen.txt`), einmal mit und
einmal ohne `Filter.split_compound`, gegen den Text, den der Generator als
auffindbar ausweist:

| Fall | Suchbegriff | Datei | mit Splitter | ohne Splitter |
|---|---|---|---|---|
| 1 | Genehmigung | 09-bescheid.pdf | Treffer | kein Treffer |
| 2 | Frist | 10-kuendigung.docx | Treffer | kein Treffer |
| 8 alt | Vereinbarung | 14-pacht-mit-anhang.pdf | Treffer | **Treffer** |
| **8 neu** | **Belehrung** | **15-schweiz-baubewilligung.pdf** | **Treffer** | **kein Treffer** |
| 9 | Auszug | 16-oesterreich-mitteilung.pdf | Treffer | kein Treffer |
| 10 | Erinnerung | 30-nur-ein-bild.pdf | Treffer | kein Treffer |

Damit ist die Zaehlung "five ... found through one of its parts" in
`integration.yml:26` wieder wahr, und zwar fuer alle fuenf im scharfen Sinn.

Zwei Nebenmessungen, weil der neue Fall sonst zwei ungeprueften Annahmen
aufgesessen waere:

- Die Schweizer Seite liest die OCR-Messung vom 06.09.2026 als Seite 4 mit
  `cer=0.000000`, `Rechtsmittelbelehrung` kommt also unversehrt in den Index.
- Der Snippet-Generator liefert auch fuer einen Treffer, den es nur ueber den
  Splitter gibt, ein Fragment: lokal gegen einen echten Tantivy-Index gefahren,
  das Fragment traegt das ganze Wort `rechtsmittelbelehrung`. Deshalb behaelt
  Fall 8 seine zwei Excerpt-Zusicherungen.

### Suite nach dem Fix-Lauf

`cd backend && uv run pytest -q`: **1749 passed, 15 skipped, 155,78 s**. Fuenf
Tests mehr als zur Pruefzeit (die beiden Splitter-Waechter mit ihren
Parametrisierungen und der Messwaechter) und rund 24 s schneller, was der
Gewinn aus M-03 ist. `ruff check`, `ruff format --check`, `pyright` und
`vulture` sind gruen, ueber `backend` und ueber `scripts`.

---

## LOW-Entscheidungen

Je Befund ein Satz. Gefixt wurde nur, was im Vorbeigehen anfiel, alles andere
ist bewusst offen und traegt seinen Grund.

- **L-01 (Buchstabengatter vergleicht Rohbuchstaben, getroffen wird ueber
  Staemme): OFFEN.** Das Gatter irrt konservativ, es kann einen Term nur zu
  streng ablehnen und nie zu grosszuegig durchwinken, heute existiert keine
  Datei, die es ausloest, und ein ehrlicher Fix waere ein Stammmengenvergleich
  ueber den ganzen Korpustext statt der Docstring-Kuerzung, die den Befund
  billig zum Verschwinden braechte.
- **L-02 (die Gatter messen gegen Text, den der Index nie sieht): OFFEN**, aber
  entschaerft: der Fall, der den Befund konkret machte, war `Vereinbarung` im
  ungelesenen Anhang von `14-pacht-mit-anhang.pdf`, und dieser Term ist mit
  H-01 kein CI-Fall mehr; alle drei heutigen Terme stehen auf Seiten, die
  nachweislich indexiert werden.
- **L-03 (Negativkontrolle ohne Positivkontrolle auf demselben Index): OFFEN**,
  weil die Luecke inzwischen an zweiter Stelle geschlossen ist: der neue
  `test_a_split_independent_term_is_kept_out_of_the_ci_set` ist genau diese
  Positivkontrolle auf derselben splitterlosen Kette, wenn auch auf Korpus-
  statt auf Indexebene; die eine Zeile in `test_index_open.py` bleibt trotzdem
  lohnend und ist dem Owner vorgelegt.
- **L-04 (`filter_chain` sieht nur Filter als Attributaufruf): OFFEN**, weil der
  Platzhalter-Fix zwar eine Zeile ist, aber die Bedeutung des Waechters aendert,
  und eine Aenderung an einem Waechter gehoert in einen Plan mit bewusster
  Gegenprobe, nicht in einen Audit-Fix-Lauf.
- **L-05 (`measure_compounds.sh` schluckt ein fehlgeschlagenes `cd` bei
  `--against`): OFFEN.** Reine Fehlermeldungsqualitaet eines Dev-Skripts, der
  Lauf bricht auch heute ab, nur mit dem falschen Satz, und das Skript wurde in
  diesem Fix-Lauf zweimal erfolgreich benutzt.
- **L-06 (`measure_compounds.sh` schreibt die Messdateien als root): OFFEN.**
  Die Entwicklungsmaschine ist Windows mit Docker Desktop, dort tritt es nicht
  auf, und der saubere Fix ist nicht das `--user`-Flag allein, sondern `--tmpfs`
  plus `docker cp`, also kein Einzeiler.
- **L-07 (Em-Dashes in `STATE.md`): OFFEN, nicht in meiner Zustaendigkeit.**
  `STATE.md` faellt unter M-05 und gehoert dem Orchestrator, die zwei Zeichen
  gehen mit demselben Schreibvorgang weg.
- **L-08 (der Abbild-Pruefschritt laeuft nicht auf Pull Requests): OFFEN.** Zwei
  Saetze Kommentar an einer Stelle, die dieser Lauf sonst nicht anfasst, und
  `docker.yml` steht in keinem der acht Commits; das Verhalten selbst ist die
  bewusste Bauweise des Workflows und kein Defekt.
- **L-09 (`compound_probe.py` meldet fehlende Eingaben als Traceback): OFFEN.**
  Ueber `measure_compounds.sh` unkritisch, weil das Skript vorher prueft, und
  der direkte Aufruf im Container ist der Weg, den die Doku ausdruecklich nicht
  empfiehlt.
- **L-10 (Docstring von `wordlist.py` steht auf sechzehn Faellen): GEFIXT** in
  `880c217`, weil der Satz durch den M-04-Fix sonst stehend falsch geblieben
  waere und die Aenderung nur einen Docstring im produktiven Code beruehrt.

---

_Auditiert: 2026-09-08_
_Diff: b7f7b01..643d574, 28 Dateien_
_Suite zur Pruefzeit: 1744 passed, 15 skipped, 179,60 s_
_Fix-Lauf: 2026-09-08, Commits 5b4aff4..880c217, Suite 1749 passed, 15 skipped, 155,78 s_
