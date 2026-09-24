# Phase 20: UI-Kataloge es/it/nl/pt - Pattern Map

**Kartiert:** 2026-09-24
**Dateien betrachtet:** 24 (10 neu, 6 geaenderte Kataloge, 1 Test, 4 Doku, 2 Workflows, 1 optionales Werkzeug)
**Analoga gefunden:** 24 / 24
**Quelle der Dateiliste:** `20-RESEARCH.md`, Abschnitt "Architecture Patterns / Dateiorte und Ladepfad" und Pitfall 10 ("Erwarteter Fussabdruck")

Es gibt kein `20-CONTEXT.md`. Jede Zeile unten stammt aus der Research oder aus dem
gelesenen Bestand, nicht aus Erinnerung.

---

## File Classification

| Neue/geaenderte Datei | Rolle | Datenfluss | Naechstes Analog | Passung |
|---|---|---|---|---|
| `php/l10n/es.json` | config/data (Katalog) | statisches File-I/O, von PHP gelesen | `php/l10n/fr.json` | exakt |
| `php/l10n/es.js` | config/data (Katalog) | statisches File-I/O, vom Browser gelesen | `php/l10n/fr.js` | exakt |
| `php/l10n/it.json` / `it.js` | config/data | wie oben | `php/l10n/fr.json` / `fr.js` | exakt |
| `php/l10n/nl.json` / `nl.js` | config/data | wie oben | `php/l10n/fr.json` / `fr.js` | exakt (2 Formen wie fr) |
| `php/l10n/pt_PT.json` / `pt_PT.js` | config/data | wie oben | `php/l10n/fr.json` / `fr.js` | exakt |
| `php/l10n/pt_BR.json` / `pt_BR.js` | config/data | wie oben | `php/l10n/fr.json` / `fr.js` | exakt (KEINE Kopie von pt_PT) |
| `php/l10n/{de,de_DE,fr}.{json,js}` (6x, Pluralfix) | config/data, Aenderung | wie oben | die Dateien selbst, Zielformat aus `apps/*/l10n/de.json` der NC-Instanz (120:0 zusammengesetzt) | exakt |
| `backend/tests/test_admin_ui_contract.py` | test (Gates) | batch / Dateien lesen und vergleichen | die Datei selbst: `L10N_CATALOGUES`, `scan_key_sets`, `FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` | exakt |
| `docs/l10n-spanish.md` | docs | - | `docs/l10n-french.md` | exakt |
| `docs/l10n-italian.md` | docs | - | `docs/l10n-french.md` | exakt |
| `docs/l10n-dutch.md` | docs | - | `docs/l10n-french.md` | exakt |
| `docs/l10n-portuguese.md` (zwei Spalten pt_PT/pt_BR) | docs | - | `docs/l10n-french.md` | rollengleich (zwei Zielspalten statt einer) |
| `.github/workflows/python.yml` (Pfadliste, optional) | config/CI | event-driven (Trigger) | dieselbe Datei, Zeilen 5-36 (jeder Eintrag mit Begruendungsabsatz) | exakt |
| `.github/workflows/integration.yml` (Sprachbeweis, optional) | config/CI | request-response (Cookie-Login gegen die Seite) | Job `search-parity`, Schritt "Log every account in and keep its session" (ab Zeile 3164), plus `scripts/dev/probe_page_login.sh` | rollengleich |
| `scripts/dev/<generator>.py` (optional, `.js` aus `.json` giessen) | utility | transform / file-I/O | `scripts/dev/stopword_supplement.py` | rollengleich |

**Nicht in dieser Phase, ausdruecklich:** `php/templates/*.php`, `php/js/*.js`,
`php/lib/**`, `backend/src/findling/**`, `backend/tests/test_measurement_scripts.py`.
Die ersten drei zoegen `PHP_TREE_HASH_TODAY` nach, die vierte kollidiert mit Phase 19.

---

## Pattern Assignments

### `php/l10n/<code>.json` (config/data, statisches File-I/O)

**Analog:** `php/l10n/fr.json` (207 Zeilen, 202 Schluessel, LF, UTF-8 ohne BOM,
abschliessender Zeilenumbruch, 4 Leerzeichen Einrueckung)

**Rahmen** (`php/l10n/fr.json:1-4` und `:205-207`):

```json
{
    "translations": {
        "Findling": "Findling",
        "File contents": "Contenu des fichiers",
```

```json
    },
    "pluralForm": "nplurals=2; plural=(n > 1);"
}
```

Kopieren heisst hier: **dieselbe Schluesselreihenfolge wie `de.json`**, `Findling` als
erster Schluessel mit sich selbst als Wert (sonst faellt G1), `pluralForm` als letztes
Feld neben `translations`, woertlich aus `core/l10n/<code>.json` der Ziel-Nextcloud
(Research, Tabelle "Pluralformen").

**Platzhalter, woertlich wie im Schluessel** (`php/l10n/fr.json:5`):

```json
        "%1$s of %2$s indexable files are searchable": "%1$s des %2$s fichiers indexables peuvent être trouvés par la recherche",
```

Nie `%s ... %s` aus `%1$s ... %2$s` machen; `scan_placeholder_parity` zaehlt Multimengen.

**Pluralwert, heutige Form im Bestand** (`php/l10n/fr.json:29` und `:63`):

```json
        "%n day": ["%n jour", "%n jours"],
        "and %n more": ["et %n autre", "et %n autres"],
```

**Pluralwert, Form nach dem Fix dieser Phase** (Zielformat, Research Pattern 1/2):

```json
        "_%n day_::_%n days_": ["%n día", "%n días", "%n días"],
```

Form 1 und Form 2 wortgleich fuer es/it/pt_PT/pt_BR (PHP erreicht Index 2 nie, JS schon),
zwei Formen fuer nl. Die fuenf betroffenen Schluessel stehen in `de.json` auf den Zeilen
27, 28, 29, 63 und dem Sperr-Sekundensatz.

---

### `php/l10n/<code>.js` (config/data, vom Browser gelesen)

**Analog:** `php/l10n/fr.js` (207 Zeilen, Rumpf um 4 Leerzeichen eingerueckt, Regel als
vierter Parameter, LF, abschliessender `\n` nach `");`)

**Rahmen** (`php/l10n/fr.js:1-4`):

```javascript
OC.L10N.register(
    "findling",
    {
    "Findling": "Findling",
```

**Abschluss** (`php/l10n/fr.js:206-207`, mit Zeilenumbruch danach, per `xxd` geprueft):

```javascript
},
"nplurals=2; plural=(n > 1);");
```

**Erzeugungsregel statt Handarbeit** (Research, Code Examples; Format an `de.js`/`fr.js`
abgelesen): `json.dumps(..., ensure_ascii=False, indent=4)`, Rumpfzeilen um vier
Leerzeichen einruecken, `newline="\n"` zwingend. Die `.js` ist eine reine Funktion der
`.json`; `test_the_two_translation_files_carry_the_same_keys` existiert, weil Handarbeit
hier schon einmal auseinandergelaufen ist.

---

### `backend/tests/test_admin_ui_contract.py` (test, Gate-Parametrisierung)

**Analog:** die Datei selbst. Vier Muster sind bereits da und werden nur auf der Datenseite
erweitert. Logikaenderung gibt es genau eine (die `_::_`-Teilung in
`scan_placeholder_parity`).

**Muster A, das Tupel als einzige Wachstumsstelle** (`:110-118`):

```python
# The third language, since plan 11-08. It is one language and not two codes, so
# it brings two files and not four: French knows no split between du and Sie,
# and ``fr_CA`` is not shipped. Both files are cast mechanically from the table
# in ``docs/l10n-french.md``, which the owner read and accepted on 11.09.2026.
L10N_FR_JSON = REPO_ROOT / "php" / "l10n" / "fr.json"
L10N_FR_JS = REPO_ROOT / "php" / "l10n" / "fr.js"

# All six catalogues in the order the gates below name them. Held as one tuple
# so that a seventh file is added in one place and every gate sees it.
L10N_CATALOGUES = (L10N_JSON, L10N_JS, L10N_DE_DE_JSON, L10N_DE_DE_JS, L10N_FR_JSON, L10N_FR_JS)
```

Kopieren: je neuem Sprachcode ein Konstantenpaar mit **Begruendungsabsatz davor** (warum
zwei Dateien, warum dieser Code, woher der Wortlaut), dann ins Tupel. `scan_prose` und
`scan_key_sets` wachsen dadurch automatisch mit.

**Muster B, benannte Ausnahmen statt Schwellwert** (`:319-340`) - die Vorlage fuer das
Mapping je Sprache:

```python
# The named exceptions of gate G2, taken from the section "Ausnahmen fuer das
# Vollstaendigkeitsgate G2" of docs/l10n-french.md. A list and deliberately not
# a threshold: a number that says "this many values may equal their key" covers
# a forgotten wording exactly as well as an intended one, while a list names each
# of them and nothing else. The reason travels with the key, so a third entry has
# to be argued rather than counted.
FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY = {
    "Findling": "the name of the app, the same word in all three languages",
    "Page %s": "Page is the same word in French, and a difference would be a loss",
    "PDF": "the proper name of a file format, the same abbreviation in all three languages",
    "Documents": "the same word in French, and an invented difference would be a mistranslation",
    "Images": "the same word in French, and an invented difference would be a mistranslation",
}
```

**Muster C, Scanner mit Fundliste statt Assertion im Rumpf** (`:399-409`) - der Scanner,
der die einzige Logikaenderung der Phase bekommt:

```python
def scan_placeholder_parity(name: str, catalogue: Mapping[str, str | list[str]]) -> list[str]:
    """Findings of a catalogue: a value whose directives are not those of its key."""
    violations: list[str] = []
    for key, value in catalogue.items():
        expected = sorted(PRINTF_DIRECTIVE.findall(key))
        for form in forms_of(value):
            found = sorted(PRINTF_DIRECTIVE.findall(form))
            if found != expected:
                violations.append(f"{name}: {key!r} carries {found} where its key carries {expected}")
    return violations
```

Aenderung: ein Schluessel mit `_::_` wird an der Marke geteilt, Singularhaelfte gegen
Form 0, Pluralhaelfte gegen jede weitere Form. Ohne das faellt das Gate nach dem
Pluralfix rot, obwohl alles stimmt (Research, Pattern 3).

**Muster D, Umbenennung eines sprachgebundenen Scanners** (`:379-397`,
`scan_french_completeness`): die Signatur traegt `name` und `catalogue` bereits, die
Ausnahmeliste ist der einzige globale Rest. Umbau zu
`scan_completeness(name, catalogue, exceptions)`; der Docstring erklaert dort schon,
warum die Identitaet auf dem **Wert** und nicht auf der Einzelform geurteilt wird
(`%n minute` ist im Franzoesischen korrekt gleich).

**Muster E, Gate-Rumpf mit drei festen Teilen** (`:1678-1706`,
`test_all_six_catalogues_carry_the_same_keys`) - fehlende Datei zuerst, dann der Scan,
dann die Anti-Leerlauf-Klausel:

```python
    missing = [path.name for path in L10N_CATALOGUES if not path.is_file()]
    assert missing == [], f"catalogues are missing: {missing}"

    findings = scan_key_sets({path.name: frozenset(catalogue_of(path)) for path in L10N_CATALOGUES})

    assert findings == []
    # And the comparison can go red. A gate whose body was deleted would report
    # six agreeing catalogues over a tree in which one of them lost a sentence.
    drifted = {"a.json": frozenset({"one", "two"}), "b.js": frozenset({"one"})}
    assert len(scan_key_sets(drifted)) == 1
```

Jedes neue oder erweiterte Gate traegt diese drei Teile. Der Testname muss mitziehen
("six" stimmt bei 16 Dateien nicht mehr).

**Muster F, Pluralregel-Gate** (`:411-421` und `:1767-1795`) - heute zwei Konstanten,
kuenftig ein Mapping je Sprachcode:

```python
FRENCH_PLURAL_FORM = "nplurals=2; plural=(n > 1);"
GERMAN_PLURAL_FORM = "nplurals=2; plural=(n != 1);"

def scan_french_plural_rule(name: str, plural_form: str) -> list[str]:
    """Findings of a French catalogue: the plural rule it declares."""
    violations: list[str] = []
    if GERMAN_PLURAL_FORM in plural_form:
        violations.append(f"{name}: carries the German plural rule, which answers n = 0 with the plural")
    if plural_form != FRENCH_PLURAL_FORM:
        violations.append(f"{name}: carries {plural_form!r} and not {FRENCH_PLURAL_FORM!r}")
    return violations
```

Der zugehoerige Test prueft zusaetzlich, dass die Regel **auch in der `.js`** steht und
dass die fuenf Pluralschluessel dieselben sind wie im Deutschen und die richtige
Formenzahl tragen:

```python
    assert rule in script, "fr.js does not carry the rule of fr.json"
    assert GERMAN_PLURAL_FORM not in script
    ...
    assert len(plural_keys) == 5
    assert [key for key in plural_keys if len(french[key]) != 2] == []
```

Die `2` wird zur Formenzahl je Sprache aus dem Mapping (3 fuer es/it/pt_PT/pt_BR).

**Muster G, die harte Zahl mit Absatzpflicht** (`:1674-1676`):

```python
    assert len(set(map(frozenset, keys_of.values()))) == 1, f"the four catalogues disagree: {sorted(keys_of)}"
    assert len(keys_of["de.json"]) == 202
```

Der Docstring darueber verlangt woertlich "Whoever raises it next writes the next
paragraph". Der Pluralfix aendert Schluessel**namen** bei gleicher Zahl: auch dafuer
gehoert ein Absatz in denselben Docstring. Die Zahl selbst am Plantag neu zaehlen.

---

### `docs/l10n-<sprache>.md` (docs)

**Analog:** `docs/l10n-french.md` (523 Zeilen). Abschnittsfolge eins zu eins uebernehmen:

| Zeile | Abschnitt | Was uebernommen wird |
|---|---|---|
| 1 | Titel | "<Sprache> Wortlaute, vollstaendig und zur Abnahme" |
| 19 | `## Die Schluesselmenge, aus der Datei gezaehlt` | Tabelle mit Herkunft der Zahl (202, aus `de.json`, am Plantag gezaehlt) |
| 64 | `## Wortwahl` | drei bis fuenf Begriffe je Sprache (backend, run, worker, index, coverage), jeder mit Spalte "Warum" |
| 83 | `## Typografie` | Regelliste, sprachspezifisch ergaenzt |
| 103 | `## Pluralformen` | Regel woertlich plus die Drei-Formen-Messung |
| 121 | `## Die Tabelle` | 202 Zeilen, Kopf `\| Schluessel \| DE \| <ZS> \|`, ASCII-Spaltennamen |
| 333 | `## Ausnahmen fuer das Vollstaendigkeitsgate G2` | benannte Liste mit Grund je Eintrag |
| 359 | `## Maschinelle Pruefungen` | Ergebnistabelle |
| 376 | `## Abnahme` / Nachtrag | der datierte Vorbehalt |

**Tabellenkopf woertlich** (`docs/l10n-french.md:129-131`):

```markdown
| Schluessel | DE | FR |
|---|---|---|
| `Search coverage` | Deckungsgrad der Suche | Couverture de la recherche |
```

Fuer `docs/l10n-portuguese.md` wird daraus `| Schluessel | DE | PT_PT | PT_BR |`, vier
Spalten, zwei echte Wortlaute.

**Wortwahl-Tabelle, Form der Begruendung** (`docs/l10n-french.md:69-71`):

```markdown
| Englisch | Französisch | Warum |
|---|---|---|
| the backend | le service | So steht es seit Phase 9 im abgenommenen Wortlaut der Ergebnisseite (`Findling n'a pas pu joindre son service`). Wo der Eigenname der App gemeint ist, bleibt er stehen |
```

**Ausnahmeliste, Form** (`docs/l10n-french.md:335-346`) - dieselbe Begruendung wie im
Test, damit Doku und Gate nicht auseinanderlaufen:

```markdown
Das ist eine benannte Liste und ausdrücklich **keine** Toleranzschwelle: eine Schwelle
würde einen vergessenen Wortlaut mitdecken, eine Liste nicht.

- `Findling`: Eigenname der App, in allen drei Sprachen derselbe.
- `PDF`: Eigenname eines Dateiformats, in allen drei Sprachen dasselbe Kürzel.
```

**Tabelle der maschinellen Pruefungen** (`docs/l10n-french.md:361-372`) - Zeilen
uebernehmen und um U+2019/U+00A0/U+202F ergaenzen, wie im Bestand schon vorhanden:

```markdown
| Prüfung | Ergebnis |
|---|---|
| Platzhalter-Parität Schlüssel gegen FR-Wert, über alle 37 Schlüssel mit Direktiven | 0 Abweichungen |
| Pluralschlüssel mit genau zwei Formen | 5 von 5 |
| U+2019 (typographischer Apostroph) | 0 |
| U+00A0 und U+202F (geschützte Leerzeichen) | 0 |
| FR-Wert identisch mit dem englischen Quellstring | 5, alle fünf oben benannt |
```

Die 37 wird zu 40 (Research, "Die Zahl heute").

---

### Der datierte Vorbehalt (Pattern 5, Erfolgskriterium 5)

**Analog:** `docs/l10n-french.md:400-403`, Nachtrag-Muster:

```markdown
**Nachtrag 17.09.2026 (Phase 13, Plan 13-11).** Die Abnahme vom 11.09.2026 deckt die
damaligen 173 Zeilen und nicht mehr. Die 23 Zeilen ... sind maschinell geprüft und
**vom Owner noch nicht gelesen**. ... Das steht hier, damit eine abgenommene Datei nicht
stillschweigend Zeilen mitträgt, die niemand abgenommen hat.
```

Die vier neuen Sprachen haben keinen Muttersprachler am Tisch (E-17-5). Der Vorbehalt
traegt deshalb: Erzeugungsdatum, Plannummer, Liste der gefahrenen Gates, **"von keinem
Muttersprachler gelesen"**, Ort des offenen Community-Review, und den Satz, dass die
Auslieferung darauf nicht wartet. Formal gleich, inhaltlich eine Stufe schwaecher als die
FR-Abnahme.

---

### `.github/workflows/python.yml` (config/CI, Pfadfilter)

**Analog:** dieselbe Datei, `:5-28`. Jeder Eintrag der Pfadliste traegt seinen Grund in
Prosa:

```yaml
on:
  push:
    paths:
      - 'backend/**'
      - 'scripts/**'
      # Two reasons for the second line, and both are load bearing.
      # backend/tests/test_corpus_terms.py ... load scripts/dev/build_corpus.py at run
      # time ... Without this line the breakage surfaces on the next commit that happens
      # to touch backend/** and is blamed on the wrong one.
      - '.github/workflows/python.yml'
```

`php/l10n/**` kommt in **beide** Listen (push `:6-28` und pull_request `:31-36`), mit
einem Absatz derselben Bauart: die Katalog-Gates liegen in `backend/tests/`, ihr Gegenstand
liegt in `php/l10n/`, und ein Gate, das bei einem reinen Katalogcommit nicht startet,
faellt nicht rot.

---

### `.github/workflows/integration.yml` (config/CI, Sprachbeweis)

**Analog:** Job `search-parity` (`:2700-2711`) und sein Login-Schritt (`:3164-3205`).

```yaml
  search-parity:
    name: search-parity
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix:
        server-version: ['stable34']
        php-version: ['8.2']
```

```yaml
      - name: Log every account in and keep its session
        run: |
          login() {  # $1 user, $2 password
            jar="cookies-$1.txt"
            token=$(curl -sfS -c "${jar}" 'http://localhost:8080/login' \
              | sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' | head -1)
            ...
            status=$(curl -sS -b "${jar}" -c "${jar}" -o "login-probe-$1.html" -w '%{http_code}' \
              --get --data-urlencode 'query=parityloginprobe' \
              'http://localhost:8080/index.php/apps/findling/')
```

Der Sprachschritt kopiert genau diese Strecke: Sprache per
`occ user:setting <user> core lang <code>` setzen, Seite mit dem vorhandenen Cookie-Jar
holen, auf einen Satz aus dem Katalog **und** auf die Abwesenheit eines bekannten
englischen Satzes pruefen, Sprache zuruecksetzen. Der Job triggert bereits auf `php/**`
(`:33-34` und `:50-51`), am Filter ist nichts zu tun. Handlauf derselben Strecke:
`scripts/dev/probe_page_login.sh <user> <pass> <term>`.

---

### `scripts/dev/<generator>.py` (utility, transform, optional)

**Analog:** `scripts/dev/stopword_supplement.py`.

Uebernommene Form: Modul-Docstring, der zuerst die **eine Frage** nennt, die das Werkzeug
beantwortet, dann warum es nicht anders gebaut ist, dann eine Sicherheitszeile ("liest
nur X, nie state.db, nie eine Nutzerdatei"), dann `Usage:`; am Ende:

```python
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_literal_block(supplement), encoding=ENCODING)

    print(_numbers(tag, builtin, supplement, digest), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

**Achtung, Fussabdruck:** `scripts/**` steht in der Pfadliste von `python.yml` und wird
mit dem Backend-Regelsatz gelintet (ruff-Vollregelsatz, pyright basic, vulture). Ein
Generator hier ist also Gate-pflichtiger Code. Wer das vermeiden will, giesst die Dateien
in einem Einmal-Lauf ohne abgelegtes Skript; dann fehlt aber die Wiederholbarkeit bei
jedem spaeteren Wortlaut-Nachtrag. Entscheid gehoert in den Plan.

---

## Shared Patterns

### Prosa-Verbote gelten ueber alle Kataloge
**Quelle:** `backend/tests/test_admin_ui_contract.py:250-262` und `:818-834`
**Gilt fuer:** jede der 16 Katalogdateien, automatisch ueber `L10N_CATALOGUES`

```python
def scan_prose(name: str, source: str) -> list[str]:
    """Findings that apply to all three files alike: dashes and emoji."""
    violations: list[str] = []
    if EM_DASH in source:
        violations.append(f"{name}: carries an em dash")
    if EN_DASH in source:
        violations.append(f"{name}: carries an en dash")
    if _EMOJI.search(source) is not None:
        violations.append(f"{name}: carries an emoji; every icon on this page is inline SVG")
    return violations
```

Maschinelle es/pt-Uebersetzungen liefern gern Halbgeviertstriche. U+2019 und U+00A0 faengt
dieser Scanner **nicht**; sie gehoeren in die Pruefliste der Sprachdoku (FR-Muster) oder
werden zum Gate gehoben.

### Katalog lesen, wie Nextcloud liest
**Quelle:** `backend/tests/test_admin_ui_contract.py:353-366`
**Gilt fuer:** jedes Gate, jedes Hilfsskript, jede Pruefung dieser Phase

```python
def catalogue_of(path: Path) -> dict[str, str | list[str]]:
    source = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(source)["translations"]
    return json.loads(source[source.index("{") : source.rindex("}") + 1])
```

Kein zweiter Weg zum selben Objekt. Wer die `.js` anders aufschneidet, baut ein zweites
Ding, das richtig bleiben muss.

### Jede Form eines Wertes, nicht nur die erste
**Quelle:** `backend/tests/test_admin_ui_contract.py:348-350`

```python
def forms_of(value: str | list[str]) -> list[str]:
    """Every form of a catalogue value: one for a sentence, two for a plural."""
    return value if isinstance(value, list) else [value]
```

Bei drei Formen fuer es/it/pt bleibt diese Funktion unveraendert richtig; die Gates, die
auf "zwei" hart stehen, nicht (siehe Muster F).

### Direktiven-Regex, unveraendert uebernehmen
**Quelle:** `backend/tests/test_admin_ui_contract.py:345`

```python
PRINTF_DIRECTIVE = re.compile(r"%%|%\d+\$[sd]|%[sdn]")
```

Der neue `%`-Scanner aus Pitfall 3 baut darauf auf: die Zahl der `%`-Zeichen eines Wertes
muss der Zahl der von diesem Regex verbrauchten `%` entsprechen, sonst zerlegt ein
spanisches "50 % de los archivos" die Seite per `ValueError` in `vsprintf`.

### Begruendungsabsatz vor jeder Konstante
**Quelle:** `backend/tests/test_admin_ui_contract.py:100-118`, `:319-332`;
`.github/workflows/python.yml:8-28`; `docs/l10n-french.md:335-340`

Drei verschiedene Dateiarten, ein Hausstil: jede Konstante, jeder Pfadeintrag und jede
Ausnahme traegt davor den Absatz, der sagt, warum es sie gibt und was ohne sie still
kaputtginge. Neue Eintraege dieser Phase folgen dem, sonst sind sie in sechs Monaten der
Eintrag, den jemand als Schlendrian entfernt.

---

## No Analog Found

Keine Datei dieser Phase steht ohne Analog da. Zwei Bauteile haben nur ein **teilweises**
Analog und brauchen deshalb einen eigenen Entwurfsabsatz im Plan:

| Bauteil | Rolle | Warum kein vollstaendiges Analog | Was stattdessen traegt |
|---|---|---|---|
| Teilung zusammengesetzter Pluralschluessel an `_::_` in `scan_placeholder_parity` | test (Logik) | Der Bestand kennt nur blanke Pluralschluessel, also hat kein Scanner je geteilt | Research Pattern 3, Falle bei der Platzhalterparitaet; Rumpfform aus Muster C, Anti-Leerlauf-Klausel aus Muster E |
| Scanner "jedes `%` gehoert zu einer erkannten Direktive" | test (neu) | Pitfall 3 ist ein Fund dieser Phase, kein bestehendes Gate deckt ihn | `PRINTF_DIRECTIVE` als Basis, Rumpfform aus Muster C |

---

## Metadata

**Suchraum:** `php/l10n/`, `php/templates/`, `php/js/`, `backend/tests/`, `docs/`,
`scripts/dev/`, `.github/workflows/`
**Gelesene Dateien:** 9 (`php/l10n/{de,fr}.{json,js}` in Ausschnitten,
`backend/tests/test_admin_ui_contract.py` in sechs Ausschnitten, `docs/l10n-french.md` in
fuenf Ausschnitten, `.github/workflows/python.yml`, `.github/workflows/integration.yml` in
zwei Ausschnitten, `scripts/dev/stopword_supplement.py`, `scripts/dev/probe_page_login.sh`)
**Nicht geaendert:** keine Datei. Diese Kartierung ist rein lesend.
**Stand der beweglichen Zahl:** 202 Schluessel in `de.json` am 2026-09-24; am Plantag neu
zaehlen (Research, Pitfall 7).
