---
phase: 20-ui-kataloge-es-it-nl-pt
plan: 07
subsystem: l10n
tags: [portugiesisch, pt_PT, varietaet, drei-pluralformen, keine-pt-json, vorbehalt]

# Dependency graph
requires:
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 01
    provides: "die fuenf Pluralschluessel als _<singular>_::_<plural>_ und die Giessform, die den Bestand byteweise reproduziert"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 02
    provides: "PLURAL_FORM_OF['pt_PT'] und FORM_COUNT_OF['pt_PT'], der Ladepfad-Beweis (der Kern kennt kein pt), die Formenwahl und die benannte Abweichung bei n gleich 0"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 03
    provides: "VALUES_THAT_MAY_EQUAL_THEIR_KEY je Sprachcode, scan_percent_discipline, scan_pipe_character, sechs Scanner ueber L10N_CATALOGUES"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 06
    provides: "der Commit-Zuschnitt (Katalogpaar in EINEM Commit), die Abschnittsfolge der Sprachdoku und die Regel, die Ausnahmeliste zu messen statt zu raten"
provides:
  - "php/l10n/pt_PT.json: 202 Schluessel in der Reihenfolge von de.json, fuenf Pluralwerte mit DREI Formen (Form 1 gleich Form 2), pt_PT-Regel mit nplurals=3 und dem (n == 0 || n == 1)-Vorderzweig"
  - "php/l10n/pt_PT.js: mechanisch aus pt_PT.json gegossen, Objektvergleich haelt den Gleichstand"
  - "L10N_PT_PT_JSON und L10N_PT_PT_JS in L10N_CATALOGUES: das Tupel fuehrt vierzehn Eintraege, alle sechs Scanner nehmen europaeisches Portugiesisch mit"
  - "Der Begruendungsabsatz im Gate, der beide portugiesischen Fragen beantwortet: warum der Code pt_PT und nicht pt heisst, und warum pt_BR in 20-08 KEINE Kopie wird"
  - "VALUES_THAT_MAY_EQUAL_THEIR_KEY['pt_PT']: ZWEI begruendete Eintraege, gemessen statt geraten; die kuerzeste Liste des Baums"
  - "docs/l10n-portuguese.md: 566 Zeilen, neun Abschnitte plus 'Was diese Kataloge nicht leisten', 202 Tabellenzeilen in drei Spalten, datierter Vorbehalt vom 25.09.2026"
  - "Der Befund, dass das Vokabular-Gate ueber der portugiesischen Doku NICHT faellt: 0 Stammtreffer, wie bei nl und anders als bei es (61) und it (9)"
  - "Die schaerfere Gegenprobe des Pluralregel-Scanners: pt_PT mit der SPANISCHEN Regel faellt, obwohl sich die beiden nur im Vorderzweig unterscheiden"
affects: [20-08 (erbt die Giessform, die Sprachdoku als Gegenstueck und die vier Varietaetsproben; fuellt die Spalte PT_BR und baut das Unterschieds-Gate), 20-09 (CI-Sprachbeweis laeuft auch fuer pt_PT)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Datei, die jedes Gate passiert und die niemand laedt, wird nicht gebaut: php/l10n/pt.json ist als Abnahmekriterium ausdruecklich verboten, weil der Kern den Code pt nicht kennt und getL10nFilesForApp nicht kuerzt"
    - "Ein Codepaar kann zwei Wortlautsaetze tragen statt zweimal denselben: pt_PT und pt_BR sind das ausdrueckliche Gegenteil von de und de_DE, und das Gate sagt das in dem Absatz, der beim de-Paar die Textgleichheit begruendet"
    - "Eine Gegenprobe wird mit der AEHNLICHSTEN fremden Regel gefahren und nicht mit der auffaelligsten: pt_PT gegen die spanische Regel unterscheidet sich nur im Vorderzweig und faellt trotzdem"
    - "Eine Varietaetsprobe, die im Katalog keinen Gegenstand hat, wird als solche benannt: zwei der vier Probewoerter (ecra, a transferir) kommen nicht vor, und die Doku sagt das, statt eine Pruefung vorzutaeuschen"
    - "Eine Tabelle, die spaeter eine Spalte bekommt, bekommt sie spaeter und nicht leer: eine leere Zelle sieht aus wie eine vergessene Uebersetzung"

key-files:
  created:
    - php/l10n/pt_PT.json
    - php/l10n/pt_PT.js
    - docs/l10n-portuguese.md
    - .planning/phases/20-ui-kataloge-es-it-nl-pt/20-07-SUMMARY.md
  modified:
    - backend/tests/test_admin_ui_contract.py

key-decisions:
  - "Das Katalogpaar pt_PT.json und pt_PT.js steht in EINEM Commit (e3fc290). Das ist die begruendete Rule-3-Abweichung aus 20-05 und 20-06, hier zum dritten Mal uebernommen UND erneut gemessen: mit beiseitegelegter pt_PT.js stuerzt test_every_catalogue_carries_the_plural_rule_of_its_language mit FileNotFoundError ab. Der Gate-Eintrag bleibt ein eigener Commit"
  - "Die portugiesische Ausnahmeliste fuehrt ZWEI Eintraege und ist damit die KUERZESTE des Baums, gleichauf mit der spanischen. Gemessen mit leerem Mapping: vier Funde, zwei Schluessel (Findling, PDF) ueber zwei Dateien. Der Unterschied zu it (drei) und nl (vier) ist genau der Schluessel %1$s in %2$s: das Portugiesische schreibt em statt in, also ist er uebersetzt und keine Ausnahme. Spreadsheets steht ebenfalls nicht drin, weil das Portugiesische folhas de calculo sagt"
  - "Der Suchbegriff steht in Winkelanfuehrungszeichen ohne Leerzeichen innen (Resultados para %s in Guillemets), wie im spanischen und italienischen Katalog. Das Franzoesische setzt Leerzeichen innen, das Niederlaendische gerade ASCII-Zeichen; beide Abweichungen sind dort begruendet und hier nicht uebernommen worden, weil die portugiesische Buchtypografie die spanisch-italienische Form fuehrt"
  - "Die Rechtschreibreform von 1990 wird durchgehend in der reformierten Form geschrieben (atualizar, ativos, exceto) und ausdruecklich NICHT durch ein Gate gehalten. Die Grenze steht im eigenen Abschnitt 'Was diese Kataloge nicht leisten' der Sprachdoku, damit ein Leser, der die alte Schreibung gewohnt ist, einen Entscheid vorfindet und keinen Fehler"
  - "Es gibt KEIN Textgleichheits-Gate pt_PT gegen pt_BR, und das ist im Kommentarabsatz des Gates ausdruecklich festgehalten. Das positive Gegenstueck, ein Gate ueber die benannten Unterschiede, baut Plan 20-08, wenn die zweite Datei existiert"
  - "Das Gate hat KEINE Logikaenderung gebraucht. git diff ueber test_admin_ui_contract.py zeigt 56 Zufuegungen und 0 Loeschungen, verteilt auf das Konstantenpaar mit seinem Begruendungsabsatz, den Tupel-Eintrag und die Ausnahmeliste. Das ist die vierte neue Sprache, die die Parametrisierung aus 20-03 unberuehrt laesst (es, it 39, nl 55, pt_PT 56)"
  - "Kein Eintrag im Vokabular-Gate von tests/test_public_artifacts.py. Gemessen, nicht prognostiziert: 0 Stammtreffer ueber docs/l10n-portuguese.md, das Portugiesische schreibt Datei als ficheiro und Speicherort als armazenamento. Die Prognose aus 20-04 stimmt damit zum zweiten Mal in Folge"
  - "KAT-01 und KAT-02 bleiben UNGEHAKT. Beide umfassen zehn Katalogdateien; acht davon stehen. Der Haken gehoert zu 20-08"

requirements-completed: []

# Metrics
duration: 55min
completed: 2026-09-25
---

# Phase 20 Plan 07: Der europäisch-portugiesische Katalog Summary

**Findling spricht europäisches Portugiesisch: `php/l10n/pt_PT.json` und `php/l10n/pt_PT.js`
führen dieselben 202 Schlüssel wie der deutsche Katalog, tragen DREI Pluralformen mit
wortgleicher Form 1 und Form 2, und die Datei, die niemand geladen hätte, ist nicht entstanden:
es gibt keine `php/l10n/pt.json`. Das Gate hat dafür wieder keine Zeile Logik gebraucht: 56
Zufügungen, 0 Löschungen.**

## Was gebaut wurde

**Zwei Katalogdateien.** `pt_PT.json` trägt 202 Schlüssel in der Reihenfolge von `de.json`,
`Findling` als ersten mit sich selbst als Wert, fünf Pluralwerte mit je **drei** Formen (Form 1
und Form 2 wortgleich) und die Regel
`nplurals=3; plural=(n == 0 || n == 1) ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;`, zeichengleich
aus `docs/l10n-catalogues.md` übernommen. `pt_PT.js` ist daraus gegossen und nicht getippt; der
Objektvergleich zwischen dem `register`-Rumpf und der `.json` ist Teil der Abnahme.

**Die Varietät ist der Inhalt und keine Feinheit.** Der Katalog schreibt `ficheiro` (56 mal),
`utilizador`, `palavra-passe`, `reciclagem`, `registo`, `folhas de cálculo` und
`texto integral`. Er schreibt nirgends `arquivo`, `usuário` oder `tela`, maschinell geprüft und
nicht überflogen.

**Zwei Konstanten, ein Begründungsabsatz und eine Ausnahmeliste im Gate.** `L10N_PT_PT_JSON` und
`L10N_PT_PT_JS` stehen in `L10N_CATALOGUES`, das damit **vierzehn** Einträge führt. Der Absatz
darüber (39 Zeilen) beantwortet beide portugiesischen Fragen an der Stelle, an der sie
gestellt werden. `VALUES_THAT_MAY_EQUAL_THEIR_KEY["pt_PT"]` führt zwei begründete Einträge.

**Eine Sprachdokumentation.** `docs/l10n-portuguese.md`, 566 Zeilen, neun Abschnitte in der
Reihenfolge der drei vorhandenen Sprachdateien dieser Phase plus einem zehnten, den keine der
drei hat: "Was diese Kataloge nicht leisten". Die Tabelle trägt heute drei Spalten
`| Schluessel | DE | PT_PT |` und 202 Datenzeilen.

## Aufgaben und Commits

| Task | Name | Commit | Dateien |
| --- | --- | --- | --- |
| 1 | pt_PT.json mit drei Pluralformen, samt gegossener pt_PT.js | `e3fc290` | `php/l10n/pt_PT.json`, `php/l10n/pt_PT.js` |
| 2 | Das Gate um europäisches Portugiesisch erweitern | `2824a4b` | `backend/tests/test_admin_ui_contract.py` |
| 3 | docs/l10n-portuguese.md mit Tabelle, Grenzen und datiertem Vorbehalt | `7ae78d6` | `docs/l10n-portuguese.md` |

Drei Commits, wie bei Niederländisch: der vierte war bei Spanisch und Italienisch jeweils der
Rule-3-Fix am Vokabular-Gate, und der ist hier wieder nicht nötig gewesen.

## Die Begriffsentscheide

Der Plan verlangt fünf vor dem Schreiben getroffen und danach begründet. Sie stehen als Tabelle
im Abschnitt "Wortwahl" der Sprachdoku:

| Englisch | Portugiesisch (PT_PT) | Grund in einem Satz |
| --- | --- | --- |
| the backend | `o serviço` | wie `le service`, `el servicio`, `il servizio` und `de dienst`: der Nutzer sieht einen Dienst, der antwortet oder nicht; `o backend` benennt ein Bauteil und keine Zusage |
| run | `a passagem`, `passagem de comparação`, `passagem em segundo plano` | ein Durchgang über den Bestand, dasselbe Bild wie `passage`, `pasada`, `passata`, `doorloop`; `execução` ist schwerer, `ronda` verspricht eine Regelmäßigkeit, die der Abgleichlauf nicht hat |
| worker | `o processo de tratamento` | nach `processus de traitement` und `proceso de tratamiento`; `trabalhador` wäre der Mensch |
| index | `o índice` (Substantiv), `indexar` (Verb), `a indexação` | gewöhnliche portugiesische Wörter, die die Oberfläche selbst führt |
| coverage | `a cobertura` | die Zahl, die den durchsuchbaren Anteil nennt |

Fünfzehn weitere Entscheide standen nicht im Plan und gehörten trotzdem getroffen, weil sie
jeweils Dutzende Zeilen betreffen. Die wichtigsten sind die Varietätswörter: `ficheiro` für
file, `utilizador` für user, `palavra-passe` für password, `reciclagem` für den Papierkorb,
`registo` für den Log, `folhas de cálculo` für spreadsheets und `texto integral` für den
Volltext. Jedes einzelne davon heißt im brasilianischen Portugiesisch anders, und genau das
macht Plan 20-08 zu einer Übersetzung statt zu einer Kopie.

## Die Giessform, zum dritten Mal gegen den Bestand geprüft

Vor der ersten neuen Zeile lief die Form aus Plan 20-01 noch einmal gegen die zwölf
Bestandsdateien: `cast_json(alt) == alt` und `cast_js(alt) == alt`, byteweise, für `de`,
`de_DE`, `fr`, `es`, `it` und `nl`, **zwölf von zwölf `True`**. Der erste Anlauf lief mit null
von zwölf: `json.dumps(..., indent=4)` schreibt Listenwerte dreizeilig, der Bestand schreibt
sie einzeilig. Das ist genau die Lehre aus 20-01, und die Vorprüfung hat sie zum dritten Mal
eingefangen, bevor sie 30 Zeilen je Datei bewegt hätte.

Das Giessskript liegt **nicht** im Repo. Es lag für die Dauer der Ausführung außerhalb des
Arbeitsbaums und ist dort geblieben; `git status --short` ist nach jedem Task leer gewesen.

## Der Rule-3-Zuschnitt, erneut gemessen statt übernommen

Der Plan schneidet Task 1 auf `pt_PT.json` und Task 2 auf `pt_PT.js` plus Gate. Dieser
Zwischenstand ist nicht grün zu bekommen, und das ist hier nicht geglaubt, sondern nachgefahren
worden: mit beiseitegelegter `pt_PT.js` stürzt
`test_every_catalogue_carries_the_plural_rule_of_its_language` mit `FileNotFoundError` ab. Das
Gate läuft über die Codes von `PLURAL_FORM_OF`, die heute eine `.json` haben, und liest zu jedem
davon die `.js` **unbedingt**. Danach ist die Datei zurückgelegt worden, `git status --short`
zeigte die beiden neuen Dateien unverändert.

## Die schärfere Gegenprobe des Pluralregel-Scanners

Für Niederländisch war die Gegenprobe die deutsche Regelzeichenkette, weil `nl` sie zu Recht
führt. Für `pt_PT` ist die interessante Nachbarin eine andere: die **spanische** Regel
unterscheidet sich von der portugiesischen nur im Vorderzweig (`n == 1 ? 0` gegen
`(n == 0 || n == 1) ? 0`). Gemessen am 25.09.2026:

| Aufruf | Ergebnis |
| --- | --- |
| `scan_plural_rule("pt_PT.json", "pt_PT", PLURAL_FORM_OF["pt_PT"])` | `[]`, kein Fund |
| `scan_plural_rule("pt_PT.json", "pt_PT", GERMAN_PLURAL_FORM)` | zwei Funde |
| `scan_plural_rule("pt_PT.json", "pt_PT", PLURAL_FORM_OF["es"])` | **ein Fund**, die fremde Zeichenkette wird wörtlich genannt |

Die dritte Zeile ist die tragende. Ein Gate, das nur auf grobe Unterschiede anspricht, hätte
die spanische Regel in einer portugiesischen Datei durchgelassen, und genau dieser Fehler ist
der wahrscheinliche: beide Sprachen führen `nplurals=3` und dieselbe Millionenklausel.

## Die Ausnahmeliste ist gefunden und nicht geraten

Drei Läufe, in dieser Reihenfolge:

| Lauf | Ergebnis |
| --- | --- |
| kein Eintrag für `pt_PT` in der Tabelle | `AssertionError: languages without a list of exceptions: ['pt_PT']` |
| leeres Mapping `"pt_PT": {}` | vier Funde, zwei Schlüssel über zwei Dateien, erster davon `pt_PT.json: 'Findling' is still the English source string` |
| zwei begründete Einträge | grün, 52 passed |

Beurteilt wurde je Schlüssel: `Findling` ist der Eigenname der App, `PDF` der eines
Dateiformats. **Es ist die kürzeste Liste des Baums**, gleichauf mit der spanischen und kürzer
als die italienische (drei), die niederländische (vier) und die französische (fünf). Der
Unterschied zu den drei längeren ist genau ein Schlüssel und eine Eigenschaft der Sprache:
`%1$s in %2$s` steht in der deutschen, italienischen und niederländischen Liste, weil diese
Sprachen die Präposition schreiben wie das Englische. Das Portugiesische schreibt `em`, also ist
der Schlüssel übersetzt. Und `Spreadsheets`, der nl-Eintrag, heißt hier `folhas de cálculo`.

## Das Gate hat keine Logikänderung gebraucht

`git diff backend/tests/test_admin_ui_contract.py` zeigt **56 Zufügungen und 0 Löschungen**,
verteilt auf genau drei Stellen: das Konstantenpaar mit seinem Begründungsabsatz, der Eintrag
im Tupel, der Eintrag in `VALUES_THAT_MAY_EQUAL_THEIR_KEY`. Kein Scanner, kein Testrumpf und
keine Zahl im Testnamen ist angefasst worden.

Die Reihe der vier neuen Sprachen lautet damit 39 (it), 55 (nl), 56 (pt_PT), und der Unterschied
ist jedes Mal vollständig der Begründungsabsatz: Italienisch brauchte einen Absatz über die
fehlende Regionalvariante, Niederländisch zwei Sonderfälle, Portugiesisch die zwei Fragen
"warum `pt_PT` und nicht `pt`" und "warum `pt_BR` keine Kopie wird". Die **Parametrisierung**
selbst ist bei allen vier unberührt geblieben.

## Abnahmekriterien, nachgemessen

| Kriterium | Ergebnis |
| --- | --- |
| Schlüsselmenge und Reihenfolge `pt_PT.json` gegen `de.json` | gleich, 202 von 202 |
| Genau fünf Listenwerte, je **drei** Einträge, Eintrag 1 gleich Eintrag 2 | 5 von 5 |
| `pluralForm` zeichengleich mit `docs/l10n-catalogues.md`, `nplurals=3` | ja, in beiden Dateien |
| `pluralForm` zeichengleich mit `PLURAL_FORM_OF["pt_PT"]` | ja, maschinell verglichen |
| `ficheiro` und `utilizador` in der Datei | 56 und 1 |
| `arquivo`, `usuário`, `tela` in der Datei | 0, 0, 0 |
| U+2014, U+2013, U+2019, U+00A0, U+202F in `pt_PT.json`, `pt_PT.js`, `l10n-portuguese.md` | je 0 |
| Pipe-Zeichen in Schlüsseln und Formen | 0 |
| Prozentzeichen ohne erkannte Direktive | 0, und überhaupt kein literales Prozentzeichen |
| Platzhalterparität Schlüssel gegen Wert, Pluralschlüssel an `_::_` geteilt | 0 Abweichungen über 40 Schlüssel mit Direktiven |
| Wert zu `Findling` | `Findling` |
| `php/l10n/pt.json` und `php/l10n/pt.js` vorhanden | **nein**, beide nicht |
| LF, UTF-8 ohne BOM, abschließender Zeilenumbruch | beide Kataloge und die Doku, byteweise geprüft; der Git-Blob ist reines LF (0 CR) |
| `pt_PT.js` beginnt mit `OC.L10N.register(` und endet mit der Regel als viertem Parameter | ja, byteweise geprüft |
| Objektvergleich `pt_PT.js` gegen `pt_PT.json` | identisch, 202 Schlüssel |
| `grep -c 'L10N_PT_PT_JSON\|L10N_PT_PT_JS'` | 4, gefordert waren mindestens 4 |
| Einträge in `L10N_CATALOGUES` | 14 |
| Kommentarabsatz vor `L10N_PT_PT_JSON` nennt den Grund für `pt_PT` UND dass `pt_BR` keine Kopie wird | ja, 39 Zeilen, beide Punkte ausdrücklich |
| Gate, das `pt_PT` gegen `pt_BR` auf Textgleichheit prüft | keines; die acht `pt_BR`-Vorkommen sind Kommentare und die Datentabellen aus 20-02 |
| `VALUES_THAT_MAY_EQUAL_THEIR_KEY["pt_PT"]`, jeder Schlüssel mit Grund | 2 Einträge, beide mit Grund |
| `git diff` am Gate: nur Zufügungen in den drei genannten Bereichen | 56 zu, 0 weg |
| Neun Abschnitte der Doku plus "Was diese Kataloge nicht leisten" | ja, maschinell ausgelesen, 10 Überschriften |
| Tabellenkopf `\| Schluessel \| DE \| PT_PT \|`, Hinweis auf Plan 20-08 unmittelbar darüber | ja, Zeilen 218 bis 224 |
| Datenzeilen der Tabelle gleich der Schlüsselzahl | 202 |
| Jeder Schlüssel aus `pt_PT.json` kommt in der Doku vor | fehlend 0 |
| Wortwahltabelle nennt `ficheiro`, `utilizador`, `ecrã` | alle drei |
| Ausnahmeliste der Doku gegen `VALUES_THAT_MAY_EQUAL_THEIR_KEY["pt_PT"]` | dieselben zwei Schlüssel, maschinell verglichen |
| Abschnitt "Abnahme" mit Datum TT.MM.JJJJ, `20-07` und `von keinem Muttersprachler gelesen` | alle drei vorhanden |
| Zeilen in `docs/l10n-portuguese.md` | 566, gefordert waren mindestens 260 |
| Stammtreffer des Vokabular-Gates in der neuen Doku | 0 |
| `cd backend && uv run pytest -q tests/test_admin_ui_contract.py` | 52 passed |
| `cd backend && uv run pytest -q tests/test_public_artifacts.py` | 55 passed |
| `cd backend && uv run pytest -q` | 2879 passed, 15 skipped (dreimal gefahren, vor jedem Commit) |
| ruff check, ruff format --check, pyright, vulture | alle grün (pyright mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, 0 errors) |
| `git diff --name-only b374204..HEAD -- php/templates php/js php/lib backend/src` | leer, kein Baumhash fällig |
| Löschungen in den drei Commits | 0 |

## Abweichungen vom Plan

### 1. [Rule 3 - Blocker, erneut gemessen] Das Katalogpaar geht in EINEN Commit

- **Gefunden in:** Task 1, nachgemessen statt übernommen
- **Problem:** Der Plan schneidet Task 1 auf `pt_PT.json` und Task 2 auf `pt_PT.js` plus Gate.
  `test_every_catalogue_carries_the_plural_rule_of_its_language` läuft über die Codes von
  `PLURAL_FORM_OF`, die heute eine `.json` haben, und liest zu jedem davon die `.js`
  **unbedingt**. Eine alleinstehende `pt_PT.json` bringt das Gate nicht rot zum Fallen,
  sondern zum Absturz mit `FileNotFoundError`. Mit beiseitegelegter `pt_PT.js` ist genau das
  am 25.09.2026 nachgefahren worden.
- **Warum nicht anders zu lösen:** Die Projektregel "Gates lokal grün VOR jedem Commit" lässt
  den Zwischenstand nicht zu. Die Alternative, das Gate an ihn anzupassen, wäre die
  Logikänderung gewesen, die dieser Plan gerade nicht brauchen sollte.
- **Fix:** `pt_PT.json` und `pt_PT.js` stehen zusammen in `e3fc290`. Beide sind ohnehin ein
  mechanisches Erzeugnis desselben Laufs. Der Gate-Eintrag bleibt ein eigener Commit
  (`2824a4b`).
- **Dateien:** `php/l10n/pt_PT.json`, `php/l10n/pt_PT.js`
- **Commit:** `e3fc290`
- **Mitzunehmen in 20-08:** derselbe Schnitt für `pt_BR`.

### 2. [Rule 1 - Messung berichtigt die Erwartung] Zwei der vier Varietätsproben haben keinen Gegenstand

- **Gefunden in:** Task 1, beim Schreiben der Wortlaute
- **Problem:** Der Plan nennt `ficheiro`, `utilizador`, `ecrã` und `a transferir` als die vier
  Proben, an denen Plan 20-08 zeigen soll, dass die zwei portugiesischen Kataloge wirklich
  zwei sind. Zwei davon haben in diesem Katalog keinen Gegenstand: kein Schlüssel spricht von
  einem Bildschirm, und keiner von einem laufenden Download. Die Abnahmekriterien des Plans
  fangen das ab (sie verlangen "mindestens eines" der positiven Wörter und verbieten alle
  negativen), aber eine Doku, die vier Proben aufzählt und bei zweien schweigt, täuscht eine
  Prüfung vor.
- **Fix:** Die Varietätstabelle der Sprachdoku führt alle vier Zeilen und trägt eine vierte
  Spalte "in diesem Katalog" mit den gezählten Werten `56 mal`, `1 mal`, `kommt nicht vor`,
  `kommt nicht vor`. Dazu ein Absatz, der sagt, dass die Probe `ecrã` gegen `tela` erst dann
  eine echte wird, wenn ein Schlüssel dazukommt, der von einem Bildschirm spricht. Die
  Wortwahltabelle nennt beide Wörter trotzdem, damit der nächste solche Schlüssel nicht als
  `tela` hereinkommt. Zusätzlich sind fünf weitere Varietätswörter aufgenommen, die der
  Katalog wirklich führt: `palavra-passe`, `reciclagem`, `registo`, `folhas de cálculo`,
  `texto integral`.
- **Dateien:** `docs/l10n-portuguese.md`
- **Commit:** `7ae78d6`

### Was diesmal NICHT nötig war: der Rule-3-Fix am Vokabular-Gate

20-04 und 20-05 brauchten je einen vierten Commit, weil das Wortstamm-Gate in
`tests/test_public_artifacts.py` über der neuen Sprachdoku fiel (Spanisch 61 Treffer,
Italienisch 9). Über `docs/l10n-portuguese.md` fällt es **nicht**: das Portugiesische schreibt
Datei als `ficheiro` und Speicherort als `armazenamento`, und keines der beiden trägt den
gesperrten Stamm. **0 Stammtreffer**, `tests/test_public_artifacts.py` 55 passed.

Die Prognose aus 20-04 hat für `pt` also gestimmt, und das ist die zweite Bestätigung in Folge
nach `nl`. Gemessen ist sie trotzdem worden, und das bleibt die Regel. Für 20-08 lautet sie
weiterhin "kein Treffer": das brasilianische `arquivo` beginnt mit `arqu` und nicht mit dem
gesperrten Stamm. Diese eine Prognose ist neu und sollte in 20-08 genauso gemessen werden.

### Kleine Abweichungen in der Form, nicht in der Sache

**Fünfzehn Begriffsentscheide mehr als die fünf verlangten.** Sie stehen begründet in der
Wortwahl-Tabelle.

**Kein `%%` im Katalog.** Wie im Spanischen, Italienischen und Niederländischen ist der einzige
betroffene Satz umformuliert (`cem por cento`). Die Schreibregel steht trotzdem im
Typografie-Abschnitt, und für das Portugiesische mit dem zusätzlichen Grund, dass die Sprache
das Zeichen mit Leerzeichen davor setzt und genau dieses Leerzeichen die Direktive unkenntlich
macht.

**Ein zehnter Abschnitt in der Sprachdoku.** Der Plan verlangt die neunteilige Abschnittsfolge
plus "Was diese Kataloge nicht leisten"; die Datei führt also zehn Überschriften, wo die drei
Vorgängerdateien neun führen. Das ist keine Abweichung, sondern die Anweisung des Plans, und
sie steht hier, damit ein Vergleich der vier Sprachdateien nicht nach einem Fehler sucht.

## Was ausdrücklich NICHT geändert wurde

`PLURAL_FORM_OF["pt_PT"]` und `FORM_COUNT_OF["pt_PT"]` stehen unverändert so da wie nach 20-02;
sie sind hier benutzt und nicht angefasst worden, ebenso die Einträge für `pt_BR`. Die zwölf
Bestandskataloge, `docs/l10n-french.md`, `docs/l10n-spanish.md`, `docs/l10n-italian.md`,
`docs/l10n-dutch.md` und `docs/l10n-catalogues.md` liegen byteweise wie vor diesem Plan.
`backend/tests/test_public_artifacts.py` ist **nicht** angefasst worden.

Kein Pfad unter `php/templates/`, `php/js/`, `php/lib/` oder `backend/src/findling` ist
angefasst worden, also bewegt sich kein Baumhash.

**`php/l10n/pt.json` und `php/l10n/pt.js` sind nicht entstanden**, auch nicht als
Bequemlichkeit oder Weiterleitung. Das ist der Gegenstand von T-20-29 und ein eigenes
Abnahmekriterium.

`KAT-01` und `KAT-02` bleiben **ungehakt**. Beide umfassen zehn Katalogdateien, und acht davon
stehen. Der Haken gehört zu 20-08.

Nicht gepusht.

## Bedrohungen dieses Plans

| ID | Erledigt durch |
| --- | --- |
| T-20-29 (eine `pt.json` täuscht einen Katalog vor, den niemand lädt) | Abnahmekriterium `os.path.exists('../php/l10n/pt.json')` ist falsch, `ls php/l10n/ \| grep '^pt\.'` liefert nichts; der gemessene Grund steht in `docs/l10n-catalogues.md`, Abschnitt 1, und im Kommentarabsatz des Gates |
| T-20-30 (portugiesischer Wert mit nacktem Prozentzeichen) | `scan_percent_discipline` läuft über `pt_PT.json` und `pt_PT.js`, seit das Paar im Tupel steht; im Katalog steht überdies kein literales Prozentzeichen (`cem por cento`) |
| T-20-31 (die Varietät wird geglättet) | Abnahmekriterium über die vier benannten Wörter, positiv und negativ, maschinell gezählt: `ficheiro` 56, `utilizador` 1, `arquivo`/`usuário`/`tela` je 0. Das vollständige Gate dazu baut Plan 20-08 |
| T-20-32 (Platzhalter geht verloren oder wechselt die Nummerierung) | `scan_placeholder_parity` über beide neuen Dateien, 0 Abweichungen über 40 Schlüssel mit Direktiven |
| T-20-33 (die Grenzen des portugiesischen Ausbaus bleiben unerwähnt) | eigener Abschnitt "Was diese Kataloge nicht leisten" in `docs/l10n-portuguese.md`, mit der Rechtschreibreform und den fehlenden getrennten Suchwortlauten |
| T-20-SC (Paketinstallation) | keine Installation in dieser Phase |

## Authentifizierungs-Tore

Keine.

## Bekannte Stubs

Die Spalte PT_BR der Tabelle in `docs/l10n-portuguese.md` fehlt. Das ist **kein** Stub im Sinne
einer nicht verdrahteten Oberfläche, sondern der ausdrückliche Zuschnitt dieses Plans: die
Spalte trägt Plan 20-08 nach, ein Hinweis unmittelbar über der Tabelle sagt das, und eine leere
vierte Spalte ist bewusst nicht angelegt worden, weil eine leere Zelle aussieht wie eine
vergessene Übersetzung. Kein Nutzer sieht dieses Dokument; die ausgelieferte Hälfte,
`php/l10n/pt_PT.json` und `pt_PT.js`, ist vollständig.

## Self-Check: PASSED

`php/l10n/pt_PT.json`, `php/l10n/pt_PT.js`, `docs/l10n-portuguese.md` und
`backend/tests/test_admin_ui_contract.py` liegen im Baum; die drei Commit-Hashes `e3fc290`,
`2824a4b` und `7ae78d6` stehen in der Historie. `php/l10n/pt.json` und `php/l10n/pt.js` liegen
nicht im Baum, und das ist der einzige Fall dieses Plans, in dem ein fehlender Pfad ein
bestandenes Kriterium ist.
