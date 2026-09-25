---
phase: 20-ui-kataloge-es-it-nl-pt
reviewed: 2026-09-25T11:02:49Z
depth: standard
files_reviewed: 26
files_reviewed_list:
  - .github/workflows/integration.yml
  - .github/workflows/python.yml
  - backend/tests/test_admin_ui_contract.py
  - backend/tests/test_public_artifacts.py
  - docs/l10n-catalogues.md
  - docs/l10n-dutch.md
  - docs/l10n-french.md
  - docs/l10n-italian.md
  - docs/l10n-portuguese.md
  - docs/l10n-spanish.md
  - php/l10n/de.js
  - php/l10n/de.json
  - php/l10n/de_DE.js
  - php/l10n/de_DE.json
  - php/l10n/es.js
  - php/l10n/es.json
  - php/l10n/fr.js
  - php/l10n/fr.json
  - php/l10n/it.js
  - php/l10n/it.json
  - php/l10n/nl.js
  - php/l10n/nl.json
  - php/l10n/pt_BR.js
  - php/l10n/pt_BR.json
  - php/l10n/pt_PT.js
  - php/l10n/pt_PT.json
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 20: Code-Review-Bericht

**Geprueft:** 2026-09-25T11:02:49Z
**Tiefe:** standard
**Dateien:** 26
**Status:** issues_found

## Zusammenfassung

Geprueft wurden die 16 Katalogdateien, die vier Test- und Workflow-Dateien und die sechs
l10n-Dokumente der Phase 20. Die Kataloge selbst sind in tadellosem Zustand: das wurde nicht
den Gates geglaubt, sondern mit einem unabhaengigen Skript nachgemessen (unabhaengiges Muster,
nicht die Umsetzung nachgebaut). Ergebnis der Messung vom 25.09.2026:

- Alle 16 Dateien sind gueltiges UTF-8 und gueltiges JSON (die .js als eingebettetes Objekt),
  ohne CR-Zeichen, ohne Em-/En-Dash, ohne Emoji, ohne Pipe, ohne nacktes Prozentzeichen.
- Jede Datei fuehrt exakt die 202 Schluessel von de.json, davon 5 Pluralschluessel.
- **Schluessel UND Werte** jedes .json/.js-Paars sind gleich (das haelt derzeit kein Gate,
  siehe WR-01), pluralForm und viertes OC.L10N.register-Argument sind je Code zeichengleich
  mit PLURAL_FORM_OF und mit dem Regelblock in docs/l10n-catalogues.md (8/8, keine Duplikate).
- Platzhalter-Paritaet haelt in jeder Form jedes Werts (Kompositschluessel korrekt gesplittet).
- Formzahlen: es/it/pt_PT/pt_BR je 3, nl 2, ueberall; alle Pluralwerte sind uebersetzt.
- de/de_DE byte-identisch; pt_PT und pt_BR differieren bei allen elf Schluesseln von
  PORTUGUESE_WORDINGS_THAT_MUST_DIFFER (11/11 nachgemessen); 72 von 202 Werten gleich, wie
  dokumentiert.
- Die Ausnahmelisten VALUES_THAT_MAY_EQUAL_THEIR_KEY stimmen exakt mit dem Baum ueberein
  (nachgezaehlt je Sprache, kein stale und kein fehlender Eintrag).
- Jeder Wert jeder neuen Sprache steht woertlich in seinem Quelldokument (alle 197
  Nicht-Plural-Werte je Sprache gegen docs/l10n-*.md geprueft, 0 Abweichungen).
- Der neue CI-Schritt in integration.yml enthaelt kein einziges `${{ }}` im run-Block
  (keine Template-Injektion), liest die Erwartung zur Laufzeit per `php -r` aus dem
  installierten Katalog, escaped wie `p()` (htmlspecialchars ENT_QUOTES), grep-t mit `-F --`,
  und der `trap ... EXIT` ist vor der ersten Sprachaenderung gesetzt. Die Abwesenheitspruefung
  des englischen Titels ist die tragende Haelfte und korrekt gebaut.
- python.yml traegt in der Working Copy CRLF, der Git-Blob ist LF (.gitattributes erzwingt
  eol=lf, `git ls-files --eol`: i/lf). Kein Befund, nur ein Checkout-Artefakt.
- Die beiden neuen vokabular-Ausnahmen in test_public_artifacts.py stimmen mit dem Baum
  ueberein (l10n-spanish.md: 61 Stamm-Treffer, l10n-italian.md: 9, beides nachgezaehlt).

Was bleibt, sind drei Warnungen: zwei Luecken im Gate-Netz, von denen eine durch die
Schluessel-Umbenennung dieser Phase selbst entstanden ist, und ein Pfadfilter, der das
Dokument-Gate von seinem eigenen Gegenstand trennt. Keine davon ist heute ein falscher
Zustand im Baum; jede davon ist ein Drift, den niemand saehe.

## Warnungen

### WR-01: Kein Gate haelt die Werte-Gleichheit von .json und .js einer Sprache

**Datei:** `backend/tests/test_admin_ui_contract.py:789` (scan_key_sets), `:2349-2352` (irrefuehrender Docstring), `:2585-2594` (Formzahl nur auf der .json)
**Problem:** `scan_key_sets` vergleicht `frozenset(catalogue_of(path))`, also nur die
Schluesselmengen. Die Formzahl-Pruefung in
`test_every_catalogue_carries_the_plural_rule_of_its_language` liest ausschliesslich
`catalogue_of(path_json)`. Ein Wert, der nur in der `.js` driftet (Tippfehlerkorrektur in
einer Haelfte, verlorene dritte Pluralform nur in der `.js`), passiert damit jedes Gate:
gleiche Schluessel, gleiche Platzhalter je vorhandener Form, gleiche Regel. Die Folge ist
genau die Fehlerklasse, die diese Datei ueberall sonst jagt: der Server sagt einen Satz, der
Browser einen anderen, und nichts wird rot. Der Docstring von
`test_the_two_portuguese_catalogues_are_two` behauptet sogar, "the cast of each .js out of
its .json already hold the two halves of one language together" - der "cast" ist aber ein
Herstellungsschritt und kein Gate; es existiert keine Pruefung dieser Aussage. Fuer Deutsch
deckt auch die de/de_DE-Textgleichheit das nicht: de.json gegen de.js wird nirgends verglichen.
Heute sind alle acht Paare wertegleich (unabhaengig nachgemessen), der Befund ist die fehlende
Haltung, nicht ein Drift im Baum.
**Fix:**
```python
def test_the_two_halves_of_every_language_carry_the_same_values() -> None:
    for code in PLURAL_FORM_OF:
        json_half = catalogue_of(REPO_ROOT / "php" / "l10n" / f"{code}.json")
        js_half = catalogue_of(REPO_ROOT / "php" / "l10n" / f"{code}.js")
        drifted = sorted(k for k in json_half if json_half[k] != js_half.get(k))
        assert drifted == [], f"{code}: .json und .js sagen Verschiedenes bei {drifted}"
```
(Dazu den Docstring-Satz in `test_the_two_portuguese_catalogues_are_two` auf das neue Gate
zeigen lassen.)

### WR-02: G2 kann seit Plan 20-01 keinen unuebersetzten Pluralwert mehr melden

**Datei:** `backend/tests/test_admin_ui_contract.py:800-827` (scan_completeness)
**Problem:** `scan_completeness` meldet Unuebersetztheit ueber `value == key`. Seit Plan 20-01
heissen die fuenf Pluralschluessel `_<singular>_::_<plural>_`; ihr Wert ist eine Liste und kann
dem String-Schluessel nie gleich sein. Ein komplett englischer Pluralwert, etwa
`"_%n day_::_%n days_": ["%n day", "%n days", "%n days"]` in es.json, passiert G2 (kein
value==key), die Platzhalter-Paritaet (Direktiven stimmen) und die Formzahl (drei Formen).
Vor der Umbenennung griff die Identitaetspruefung ueber den blanken Singular-Schluessel noch;
die Umbenennung hat dieses Gate fuer die fuenf Schluessel still abgeschaltet, ohne dass es
irgendwo steht. Heute sind alle Pluralwerte aller acht Kataloge uebersetzt (nachgemessen),
der Befund ist die immer-gruene Pruefstrecke.
**Fix:** In `scan_completeness` Kompositschluessel am Mal `_::_` teilen (dieselbe Zerlegung
wie `expected_directives_per_form`) und Form 0 gegen die Singular-Haelfte, jede weitere Form
gegen die Plural-Haelfte auf Identitaet pruefen, mit demselben Ausnahme-Mechanismus (das
franzoesische `%n minute` == Singular-Haelfte ist legitim und braucht einen benannten Eintrag,
keinen Blindflug):
```python
if isinstance(value, list) and "_::_" in key:
    singular, plural = key.split("_::_", 1)
    halves = [singular.removeprefix("_")] + [plural.removesuffix("_")] * (len(value) - 1)
    if value == halves and key not in exceptions:
        violations.append(f"{name}: {key!r} is still the English source string in every form")
```

### WR-03: python.yml startet die Dokument-Gates nicht, wenn nur ihre Dokumente sich aendern

**Datei:** `.github/workflows/python.yml:28-42` (push-Pfade), `:50-55` (pull_request-Pfade)
**Problem:** `test_the_rule_table_of_the_documentation_and_the_constant_are_one_string`
beurteilt `docs/l10n-catalogues.md`, und `test_public_artifacts.py` fuehrt fuer
`docs/l10n-spanish.md` und `docs/l10n-italian.md` namentliche vokabular-Ausnahmen, die bei
einer Aenderung dieser Dateien stale werden koennen
(`test_every_exception_of_a_family_is_still_earning_its_place`). Die Pfadfilter beider
Trigger kennen aber nur `docs/measurements/**` und `php/l10n/**`; ein Commit, der nur
`docs/l10n-catalogues.md` umformatiert (der Regelblock parst dann zu nichts und die
Anti-Vakuitaets-Klausel schlaegt an) oder nur ein Sprachdokument umschreibt, startet kein
einziges Gate. Der Bruch faellt beim naechsten backend-Commit auf und wird dem falschen
Commit angelastet - woertlich die Fehlerklasse, die die eigenen Kommentare der Datei
(Zeilen 21-41) benennen und fuer `docs/measurements/**` bereits geschlossen haben. Die
Sprachdokumente sind zudem die erklaerte Quelle der Kataloge; eine Aenderung dort ist eine
Aenderung am Gegenstand dieser Gates.
**Fix:** In beide Pfadlisten aufnehmen:
```yaml
      - 'docs/l10n-catalogues.md'
      - 'docs/l10n-*.md'
```
(mit dem ueblichen Begruendungskommentar im Stil der Nachbarzeilen; `docs/l10n-*.md` deckt
beide Faelle in einer Zeile).

## Hinweise

### IN-01: Fehlermeldung des php-Erwartungslesers benennt nur einen der zwei Abbruchgruende

**Datei:** `.github/workflows/integration.yml:3276-3285`
**Problem:** `exit(3)` im `php -r`-Block feuert sowohl bei fehlender/leerer Uebersetzung als
auch bei Wert gleich Schluessel; die Shell-Meldung sagt nur "the catalogue has no translation
of ...". Wer den zweiten Fall debuggt, sucht am falschen Ort.
**Fix:** Meldung erweitern: "... has no translation of X, or the value still equals its key".

### IN-02: Ein scheiternder Restore im EXIT-Trap kann still bleiben

**Datei:** `.github/workflows/integration.yml:3254-3262`
**Problem:** Scheitert `./occ user:setting ... core lang "${original}"` im Trap
(had_original=1-Zweig, ohne Fehlerbehandlung), unterbleibt das abschliessende Echo, und je
nach errexit-Verhalten im EXIT-Trap kann ein gruener Schritt einen fehlgeschlagenen Restore
maskieren; alle folgenden Szenarien liefen dann in pt_BR. Der `--delete`-Zweig verschluckt
Fehler per `|| true` sogar ausdruecklich.
**Fix:** Restore-Erfolg im Trap explizit pruefen und den Schritt rot machen:
```bash
restore_language() {
  if [ "${had_original}" = "1" ]; then
    ./occ user:setting "${OWNER_USER}" core lang "${original}" \
      || { echo "::error::the user language could not be restored"; exit 1; }
  else
    ./occ user:setting "${OWNER_USER}" core lang --delete \
      || { echo "::error::the user language could not be deleted"; exit 1; }
  fi
  ...
}
```

### IN-03: Die vokabular-Ausnahmen der Sprachdokumente sind praesenz- und nicht zahlbasiert

**Datei:** `backend/tests/test_public_artifacts.py:602-615`
**Problem:** Die Ausnahmen fuer `l10n-spanish.md` (Begruendung nennt 61 Treffer) und
`l10n-italian.md` (nennt 9, "reworded rather than excused" fuer den einen deutschen Fund)
schalten die Familie fuer die ganze Datei ab. Ein spaeter hinzukommendes echtes deutsches
Vorkommen des gesperrten Stamms in diesen Dateien waere maskiert, und die Zahlen in den
Begruendungen prueft nichts. Die Zaehlung dieser Review bestaetigt beide Zahlen heute
(61 und 9).
**Fix:** Fuer diese beiden Eintraege die erwartete Trefferzahl pinnen (z. B. ein optionales
Mapping Datei/Familie -> erwartete Anzahl, das `matches_of` gegenprueft), damit ein
zusaetzlicher Treffer wieder ein Befund ist statt einer stillen Erweiterung der Ausnahme.

---

_Geprueft: 2026-09-25T11:02:49Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Tiefe: standard_
