---
phase: 20-ui-kataloge-es-it-nl-pt
plan: 04
subsystem: l10n
tags: [spanisch, katalog, giessform, vollstaendigkeitsgate, pluralformen, vorbehalt]

# Dependency graph
requires:
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 01
    provides: "die fuenf Pluralschluessel als _<singular>_::_<plural>_ und die Giessform, die den Bestand byteweise reproduziert"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 02
    provides: "PLURAL_FORM_OF['es'] und FORM_COUNT_OF['es'], docs/l10n-catalogues.md als gemeinsamer Beweis"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 03
    provides: "VALUES_THAT_MAY_EQUAL_THEIR_KEY je Sprachcode, scan_percent_discipline, scan_pipe_character, sechs Scanner ueber L10N_CATALOGUES"
provides:
  - "php/l10n/es.json: 202 Schluessel in der Reihenfolge von de.json, fuenf Pluralwerte mit drei Formen, Form 1 gleich Form 2, spanische Regel mit nplurals=3"
  - "php/l10n/es.js: mechanisch aus es.json gegossen, Objektvergleich haelt den Gleichstand"
  - "L10N_ES_JSON und L10N_ES_JS in L10N_CATALOGUES: das Tupel fuehrt acht Eintraege, alle sechs Scanner nehmen Spanisch mit"
  - "VALUES_THAT_MAY_EQUAL_THEIR_KEY['es']: zwei begruendete Eintraege, gemessen statt geraten"
  - "docs/l10n-spanish.md: neun Abschnitte, 202 Tabellenzeilen, Pruefergebnisse und der datierte Vorbehalt vom 25.09.2026"
  - "Der Eintrag l10n-spanish.md in AUSNAHMEN des Vokabular-Gates, mit dem Grund, den die naechste Sprache mit demselben Wortstamm wiederverwenden kann"
affects: [20-05 bis 20-08 (dieselbe Giessform, dieselbe Abschnittsfolge, und it braucht denselben Vokabular-Ausnahmeeintrag), 20-09 (CI-Sprachbeweis laeuft auch fuer es)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Ausnahmeliste wird nicht geraten, sondern gefunden: das Gate laeuft einmal mit leerem Mapping, die gemeldeten Schluessel werden einzeln beurteilt, und was bleibt, traegt seinen Grund bei sich"
    - "Eine Giessform wird auch beim vierten Gebrauch zuerst gegen den unveraenderten Bestand geprueft (cast(alt) == alt byteweise fuer alle sechs Dateien), bevor sie eine neue Datei schreibt"
    - "Ein literales Prozentzeichen wird lieber umformuliert als verdoppelt: 'el cien por cien' liest sich besser als '100 %%' und kann den vsprintf-Pfad gar nicht erst erreichen"
    - "Ein Wortstamm-Gate auf einer Sprache stolpert ueber die Homographen einer anderen; der Ausweg ist der benannte Eintrag mit Grund und nicht die aufgeweichte Regex"

key-files:
  created:
    - php/l10n/es.json
    - php/l10n/es.js
    - docs/l10n-spanish.md
    - .planning/phases/20-ui-kataloge-es-it-nl-pt/20-04-SUMMARY.md
  modified:
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_public_artifacts.py

key-decisions:
  - "Die spanische Ausnahmeliste fuehrt ZWEI Eintraege und nicht fuenf wie die franzoesische. Sie ist gemessen: das Vollstaendigkeitsgate lief einmal mit leerem Mapping fuer es und meldete genau vier Funde, zwei Schluessel ueber zwei Dateien (Findling, PDF). Page %s, Documents und Images haben im Spanischen echte eigene Wortlaute (Pagina %s, Documentos, Imagenes) und gehoeren deshalb nicht hinein"
  - "Kein einziges literales Prozentzeichen im Katalog, auch kein verdoppeltes. Der deutsche Satz 'damit der Deckungsgrad 100 Prozent erreichen kann' wird spanisch zu 'de modo que la cobertura puede alcanzar el cien por cien'. Der Plan laesst beides zu (verdoppeln oder umformulieren) und nennt Umformulieren den Weg, wo die Verdopplung den Satz unleserlich macht; hier war sie ausserdem vermeidbar, und was nicht dasteht, kann auch nicht verlorengehen"
  - "Die Tabelle in docs/l10n-spanish.md fuehrt 202 Zeilen und schliesst Findling ein, waehrend docs/l10n-french.md ihn ausdruecklich auslaesst. Das Abnahmekriterium des Plans verlangt so viele Datenzeilen wie es.json Schluessel fuehrt, und eine fehlende Zeile mit einem Absatz zu erklaeren ist teurer als die Zeile"
  - "Der Kollisionsfall des Vokabular-Gates wird ueber die vorgesehene Ausnahmeliste geloest und nicht ueber die Regex. Eine Regex, die den Stamm vor einem o nicht mehr faengt, verlore auch deutsche Zusammensetzungen; ein Eintrag mit Grund verliert nur fuer diese eine Datei"
  - "KAT-01 und KAT-02 bleiben UNGEHAKT. Beide umfassen zehn Katalogdateien; zwei davon stehen. Der Haken gehoert fruehestens zu 20-08"

requirements-completed: []

# Metrics
duration: 40min
completed: 2026-09-25
---

# Phase 20 Plan 04: Der spanische Katalog Summary

**Findling spricht Spanisch: `php/l10n/es.json` und `php/l10n/es.js` fuehren dieselben 202
Schluessel wie der deutsche Katalog, laufen durch dieselben sechs Scanner wie die sechs
Bestandsdateien, und `docs/l10n-spanish.md` sagt in einem datierten Absatz, was der Katalog wert
ist: maschinell erstellt und von keinem Muttersprachler gelesen.**

## Was gebaut wurde

**Zwei Katalogdateien.** `es.json` traegt 202 Schluessel in der Reihenfolge von `de.json`,
`Findling` als ersten mit sich selbst als Wert, fuenf Pluralwerte mit je drei Formen (Form 1 und
Form 2 wortgleich) und die spanische Regel mit `nplurals=3`, zeichengleich aus
`docs/l10n-catalogues.md` uebernommen. `es.js` ist daraus gegossen und nicht getippt; der
Objektvergleich zwischen dem `register`-Rumpf und der `.json` ist Teil der Abnahme.

**Zwei Konstanten und eine Ausnahmeliste im Gate.** `L10N_ES_JSON` und `L10N_ES_JS` stehen mit
Begruendungsabsatz in `L10N_CATALOGUES`, das damit acht Eintraege fuehrt. Prosa-Scan,
Schluesselmenge, Vollstaendigkeit, Platzhalterparitaet, Prozentdisziplin und Pipe-Pruefung
nehmen Spanisch seitdem automatisch mit. `VALUES_THAT_MAY_EQUAL_THEIR_KEY["es"]` fuehrt zwei
begruendete Eintraege.

**Eine Sprachdokumentation.** `docs/l10n-spanish.md`, 409 Zeilen, neun Abschnitte in der
Reihenfolge von `docs/l10n-french.md`, mit der vollstaendigen Tabelle `| Schluessel | DE | ES |`
und dem datierten Vorbehalt.

## Aufgaben und Commits

| Task | Name | Commit | Dateien |
| --- | --- | --- | --- |
| 1 | es.json, 202 Schluessel in der Reihenfolge des deutschen Katalogs | `7dd61fd` | `php/l10n/es.json` |
| 2 | es.js giessen und das Gate um Spanisch erweitern | `c61955d` | `php/l10n/es.js`, `backend/tests/test_admin_ui_contract.py` |
| 3 | docs/l10n-spanish.md mit Tabelle, Pruefergebnissen und datiertem Vorbehalt | `64527aa` | `docs/l10n-spanish.md` |
| 3a | Rule-3-Fix: Vokabular-Gate ueber der neuen Doku | `aa9f36a` | `backend/tests/test_public_artifacts.py` |

## Die fuenf Begriffsentscheide

Der Plan verlangt sie vor dem Schreiben getroffen und danach begruendet. Sie stehen als Tabelle
im Abschnitt "Wortwahl" der Sprachdoku und folgen der franzoesischen Linie, weil beide Kataloge
dieselben Saetze uebersetzen:

| Englisch | Spanisch | Grund in einem Satz |
| --- | --- | --- |
| the backend | `el servicio` | wie `le service`: der Nutzer sieht einen Dienst, der antwortet oder nicht |
| run | `pasada` | `ejecucion` ist das schwerere Wort fuer dieselbe Sache |
| worker | `proceso de tratamiento` | nach `processus de traitement`; `trabajador` waere der Mensch |
| index | `el indice` (Substantiv), `indexar` (Verb) | mit Akzent, sonst steht dort das Anzeichen |
| coverage | `cobertura` | die Zahl, die den durchsuchbaren Anteil nennt |

## Die Giessform, erneut gegen den Bestand geprueft

Vor der ersten neuen Zeile lief die Form aus Plan 20-01 noch einmal gegen die sechs
Bestandsdateien: `cast_json(alt) == alt` und `cast_js(alt) == alt`, byteweise, fuer `de`,
`de_DE` und `fr`, sechs von sechs `True`. Erst danach ist `es.json` geschrieben worden. Das
Faltschritt fuer einzeilige Listenwerte aus 20-01 ist dabei unveraendert noetig gewesen; ohne
ihn haette `es.json` 227 statt 207 Zeilen und ein anderes Format als seine fuenf Geschwister.

Das Giessskript liegt **nicht** im Repo. Es lag fuer die Dauer der Ausfuehrung ausserhalb des
Arbeitsbaums und ist dort geblieben; `git status --short` ist nach jedem Task leer gewesen.

## Die Ausnahmeliste ist gefunden und nicht geraten

Der Plan verlangt den Weg ausdruecklich, und er ist gegangen worden. Drei Laeufe:

| Lauf | Ergebnis |
| --- | --- |
| kein Eintrag fuer `es` in der Tabelle | `AssertionError: languages without a list of exceptions: ['es']` -- genau der Fehlschlag mit Namen, den 20-03 versprochen hat |
| leeres Mapping `"es": {}` | vier Funde, zwei Schluessel ueber zwei Dateien, erster davon `es.json: 'Findling' is still the English source string` |
| zwei begruendete Eintraege | gruen |

Beurteilt wurde je Schluessel und nicht gezaehlt: `Findling` ist der Eigenname der App, `PDF`
der eines Dateiformats. Fuer keinen weiteren Schluessel war der gleiche Wortlaut das Ergebnis;
`Page %s`, `Documents` und `Images`, die im Franzoesischen in der Liste stehen, haben im
Spanischen eigene Wortlaute und gehoeren deshalb nicht hinein. Die spanische Liste ist damit
kuerzer als die franzoesische, und das ist ein Befund und keine Nachlaessigkeit.

## Abnahmekriterien, nachgemessen

| Kriterium | Ergebnis |
| --- | --- |
| Schluesselmenge und Reihenfolge `es.json` gegen `de.json` | gleich, 202 von 202 |
| Genau fuenf Listenwerte, je drei Eintraege, Eintrag 1 gleich Eintrag 2 | 5 von 5 |
| `pluralForm` zeichengleich mit `docs/l10n-catalogues.md`, `nplurals=3` | ja, aus dem Dokument gelesen statt nachgetippt |
| U+2014, U+2013, U+2019, U+00A0, U+202F in `es.json`, `es.js`, `l10n-spanish.md` | je 0 |
| Pipe-Zeichen in Schluesseln und Formen | 0 |
| Prozentzeichen ohne erkannte Direktive | 0, und ueberhaupt kein literales Prozentzeichen |
| Wert zu `Findling` | `Findling` |
| LF, UTF-8 ohne BOM, abschliessender Zeilenumbruch | beide Kataloge und die Doku, byteweise geprueft; die Blobs sind reines LF |
| `es.js` beginnt mit `OC.L10N.register(` und endet mit der Regel als viertem Parameter | ja, `xxd` zeigt `2 ? 1 : 2;");\n` |
| Objektvergleich `es.js` gegen `es.json` | identisch, 202 Schluessel |
| `grep -c 'L10N_ES_JSON\|L10N_ES_JS'` | 4, gefordert waren mindestens 4 |
| Eintraege in `L10N_CATALOGUES` | 8 |
| Kommentarabsatz vor `L10N_ES_JSON`, nennt `es_MX` und `es_EC` | ja, 17 Zeilen |
| `VALUES_THAT_MAY_EQUAL_THEIR_KEY["es"]`, jeder Schluessel mit Grund | 2 Eintraege, beide mit Grund |
| Neun Abschnitte der Doku in der Reihenfolge des Plans | ja, Zeilen 1, 15, 39, 60, 90, 116, 332, 355, 381 |
| Datenzeilen der Tabelle gleich der Schluesselzahl | 202 |
| Jeder Schluessel aus `es.json` kommt in der Doku vor | fehlend 0 |
| Ausnahmeliste der Doku gegen `VALUES_THAT_MAY_EQUAL_THEIR_KEY["es"]` | dieselben zwei Schluessel, maschinell verglichen |
| Abschnitt "Abnahme" mit Datum TT.MM.JJJJ, `20-04` und `von keinem Muttersprachler gelesen` | alle drei vorhanden |
| Zeilen in `docs/l10n-spanish.md` | 409, gefordert waren mindestens 260 |
| `cd backend && uv run pytest -q tests/test_admin_ui_contract.py` | 52 passed |
| `cd backend && uv run pytest -q` | 2879 passed, 15 skipped |
| ruff check, ruff format --check, pyright, vulture | alle gruen (pyright mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, 0 errors) |
| `git diff --name-only -- php/templates php/js php/lib backend/src` | leer, kein Baumhash faellig |

## Abweichungen vom Plan

### 1. [Rule 3 - Blocker] Das Vokabular-Gate faellt ueber dem spanischen Wort fuer Datei

- **Gefunden in:** Task 3, beim vollen Suitelauf nach dem Commit der Doku
- **Problem:** `tests/test_public_artifacts.py` haelt eine Wortstamm-Sperre ueber alles unter
  `docs/`. Gesucht wird die deutsche Form eines Begriffs, also der Stamm ohne die englische
  Endung. Das spanische Wort fuer Datei beginnt mit genau diesem Stamm und ist das haeufigste
  Substantiv dieses Katalogs: `test_no_file_under_docs_carries_a_finding_outside_the_exception_list[vokabular]`
  meldete `l10n-spanish.md` mit 61 Treffern, alle davon dasselbe spanische Wort und keiner
  davon die deutsche Form, die die Familie fangen soll.
- **Warum nicht anders zu loesen:** Umformulieren scheidet aus, weil die ES-Spalte die
  ausgelieferten Wortlaute von `es.json` fuehrt und eine Doku, die anders schreibt als die
  Datei, aufhoert deren Quelle zu sein. Die Regex zu entschaerfen (den Stamm vor einem `o`
  nicht mehr fangen) haette auch deutsche Zusammensetzungen verloren und die Sperre fuer
  **alle** Dateien geschwaecht.
- **Fix:** Ein Eintrag `("l10n-spanish.md", "vokabular")` in `AUSNAHMEN`, mit eigenem Grund in
  eigenem Satz, wie es die vier Nachbareintraege dieser Familie fuehren. Das ist der
  Mechanismus, den die Datei selbst vorsieht ("A file that carries it stands on the list below
  with that reason and no other").
- **Dateien:** `backend/tests/test_public_artifacts.py`
- **Commit:** `aa9f36a`
- **Restrisiko, benannt:** die Ausnahme gilt fuer die ganze Datei, also wuerde eine spaeter
  eingefuegte **deutsche** Form in `docs/l10n-spanish.md` nicht mehr auffallen. Feiner kann die
  Liste heute nicht, sie ist auf Datei und Familie geschluesselt. **Mitzunehmen in 20-05:**
  Italienisch fuehrt dasselbe Wort mit derselben Wirkung und braucht denselben Eintrag; die
  portugiesischen und niederlaendischen Woerter fuer Datei tragen den Stamm nicht.

### Kleine Abweichungen in der Form, nicht in der Sache

**Die Tabelle fuehrt `Findling` mit.** `docs/l10n-french.md` laesst ihn aus und erklaert das in
einem Absatz unter der Tabelle. Das Abnahmekriterium dieses Plans verlangt genau so viele
Datenzeilen, wie `es.json` Schluessel fuehrt, also steht er drin und zusaetzlich in der
Ausnahmeliste. Die Doku sagt in einem Satz, warum sie hier von der franzoesischen abweicht.

**Kein `%%` im Katalog.** Der Plan nennt die Verdopplung als Regel und das Umformulieren als
Ausweg, wo die Verdopplung den Satz unleserlich macht. Im einzigen betroffenen Satz war das
Umformulieren nicht nur lesbarer, sondern billiger: `el cien por cien` traegt gar kein
Prozentzeichen mehr, und der Scanner hat in diesem Katalog nichts zu finden. Die Schreibregel
steht trotzdem im Typografie-Abschnitt der Doku, denn die naechste Zeile, die eine Zahl mit
Prozentzeichen braucht, kommt bestimmt.

**Task 3 hat zwei Commits statt einem.** Der Rule-3-Fix ist getrennt committet worden, weil er
eine andere Datei und eine andere Begruendung traegt als die Doku selbst.

## Was ausdruecklich NICHT geaendert wurde

`PLURAL_FORM_OF["es"]` und `FORM_COUNT_OF["es"]` stehen unveraendert so da wie nach 20-02; sie
sind hier benutzt und nicht angefasst worden. Die sechs Bestandskataloge, `docs/l10n-french.md`
und `docs/l10n-catalogues.md` liegen byteweise wie vor diesem Plan.

Kein Pfad unter `php/templates/`, `php/js/`, `php/lib/` oder `backend/src/findling` ist
angefasst worden, also bewegt sich kein Baumhash.

`KAT-01` und `KAT-02` bleiben **ungehakt**. Beide umfassen zehn Katalogdateien, und zwei davon
stehen. Der Haken gehoert fruehestens zu 20-08.

Nicht gepusht.

## Bedrohungen dieses Plans

| ID | Erledigt durch |
| --- | --- |
| T-20-14 (spanisches Prozentzeichen, Denial of Service) | `scan_percent_discipline` laeuft ueber `es.json` und `es.js`, seit das Paar im Tupel steht; im Katalog steht ueberdies kein literales Prozentzeichen |
| T-20-15 (verlorenes `%2$s`) | `scan_placeholder_parity` ueber beide neuen Dateien, mit Teilung der zusammengesetzten Pluralschluessel; 0 Abweichungen ueber 40 Schluessel mit Direktiven |
| T-20-16 (`.js` laeuft von der `.json` weg) | die `.js` ist gegossen, und der Gleichstand ist per Objektvergleich geprueft |
| T-20-17 (erfundener Dateiname im Wortlaut) | akzeptiert wie im Plan; die Paritaetspruefung haelt die Platzhaltermenge, der Inhalt kommt zur Laufzeit |
| T-20-18 (Katalog ohne Vorbehalt) | `docs/l10n-spanish.md`, Abschnitt "Abnahme", datiert auf den 25.09.2026, mit Plannummer und dem Satz "von keinem Muttersprachler gelesen" |
| T-20-SC (Paketinstallation) | keine Installation in dieser Phase |

## Authentifizierungs-Tore

Keine.

## Bekannte Stubs

Keine.

## Self-Check: PASSED

`php/l10n/es.json`, `php/l10n/es.js`, `docs/l10n-spanish.md`,
`backend/tests/test_admin_ui_contract.py` und `backend/tests/test_public_artifacts.py` liegen im
Baum; die vier Commit-Hashes `7dd61fd`, `c61955d`, `64527aa` und `aa9f36a` stehen in der
Historie. Kein Eintrag fehlt.
