---
phase: 18-schema-marken-und-umbauweg
plan: 02
subsystem: database
tags: [tantivy, schema, snowball, analyzer, index, config, i18n]

# Dependency graph
requires:
  - phase: 18-schema-marken-und-umbauweg
    plan: 01
    provides: "Dreizehn Schemafelder, BODY_FIELD, acht unbedingt registrierte Ketten, SCHEMA_VERSION 2"
  - phase: 17-owner-tor-und-analyseketten
    provides: "SUPPORTED_LANGUAGES, SNOWBALL_NAME, LANGUAGE_ALLOWLIST, snowball_analyzer"
provides:
  - "_languages() filtert gegen SUPPORTED_LANGUAGES: sechs Sprachcodes sind waehlbar"
  - "DEFAULT_LANGUAGES bleibt ('de','en') und ist ausdruecklich die Werkseinstellung, keine Faehigkeitsliste"
  - "IndexBatchWriter(languages=...) statt index_english: Befuellungsschleife ueber die aktive Sprachmenge"
  - "body_de wird bedingungslos geschrieben, mit dem Absatz, der gespeichert von analysiert trennt"
  - "info.xml nennt alle sechs Codes und den wahren Umbauweg"
  - "docs/language-analyzers.md benennt die Neustartgrenze des zwischengespeicherten settings()"
affects: [18-03, 18-04, 19-frageseite, 22-messphase]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Werkseinstellung und Faehigkeitsliste sind zwei Konstanten, und gefiltert wird gegen die zweite"
    - "Feldnamen im Schreibpfad ausschliesslich aus BODY_FIELD, nie zusammengesetzt"
    - "Gespeichertes Feld und analysiertes Feld sind zwei Eigenschaften, nur die zweite haengt an der Sprachmenge"

key-files:
  created: []
  modified:
    - backend/src/findling/config.py
    - backend/src/findling/index/writer.py
    - backend/appinfo/info.xml
    - backend/tests/test_config.py
    - backend/tests/test_index_writer.py
    - backend/tests/test_measurement_scripts.py
    - docs/language-analyzers.md

key-decisions:
  - "Gefiltert wird gegen SUPPORTED_LANGUAGES und nicht gegen die Schluessel von SNOWBALL_NAME: beide Mengen sind durch einen Paritaetstest aus 18-01 deckungsgleich, aber SUPPORTED_LANGUAGES ist die Konstante mit der Ordnung, und die Ordnung ist die Normalisierung"
  - "Die Sprachmenge wird im Konstruktor zu einem Tupel eingefroren, damit sich die Menge unter einem halb geschriebenen Stapel nicht bewegen kann"
  - "body_de wird ausserhalb der Schleife geschrieben und in der Schleife uebersprungen statt die Schleife de auslassen zu lassen, weil das Feld sonst zweimal geschrieben wuerde"
  - "Der Rat occ findling:index --restart steht weiterhin in info.xml, aber als ausdrueckliche Verneinung: die Aktionsbeschreibung des Plans verlangt genau diesen Satz"

patterns-established:
  - "Warnungstests belegen beide Haelften der Hausregel: Variablenname steht drin, Wert steht nicht drin"
  - "Leere Felder werden ueber das Termverzeichnis geprueft (terms_with_prefix) und nie ueber eine Trefferzahl"

requirements-completed: [LEX-02]

# Metrics
duration: 27min
completed: 2026-09-24
---

# Phase 18 Plan 02: Sechs waehlbare Sprachen Summary

**`_languages()` filtert gegen `SUPPORTED_LANGUAGES` und `IndexBatchWriter.add()` befuellt die aktive Sprachmenge, womit aus sechs vorhandenen Feldern sechs waehlbare Sprachen werden.**

## Performance

- **Duration:** 27 min
- **Started:** 2026-09-24T05:18:00Z
- **Completed:** 2026-09-24T05:45:00Z
- **Tasks:** 3 (zwei davon TDD, also fuenf Commits)
- **Files modified:** 7

## Accomplishments

- `_languages()` filtert die Eingabe gegen `SUPPORTED_LANGUAGES`. `FINDLING_LANGUAGES=es,de` antwortet `("de", "es")`, `FINDLING_LANGUAGES=es` antwortet `("es",)`, und jeder der sechs Codes ist einzeln waehlbar. Die Iteration laeuft weiter ueber die geordnete Konstante, also ist `es,de` dieselbe Einstellung wie `de,es` und traegt spaeter denselben Merker.
- `DEFAULT_LANGUAGES` steht unbewegt auf `("de", "en")`, und ein Test haelt das ausdruecklich fest, samt der echten Teilmengenbeziehung zu `SUPPORTED_LANGUAGES`. Eine Werkseinstellung, die zur Faehigkeitsliste erweitert wird, wuerde jede vorhandene Installation beim naechsten Upgrade auf sechs Felder heben.
- Der Kommentarblock an `SUPPORTED_LANGUAGES` behauptet nicht mehr, dass kein Produktivpfad ihn liest. Er sagt jetzt, was das Hinzufuegen eines Codes wirklich verlangt: Schemafeld, registrierte Kette, `SNOWBALL_NAME`-Eintrag.
- `IndexBatchWriter` nimmt `languages: Sequence[str] | None` statt `index_english: bool | None`, friert den Wert als Tupel ein und laeuft in `add()` ueber die aktive Menge. Jeder Feldname kommt aus `BODY_FIELD`, nie aus einer Zusammensetzung, weil `add_document` einen unbekannten Namen gemessen ohne Fehler verschluckt (T-18-02-03). `grep -rn "index_english" backend/ --include=*.py` liefert nichts mehr.
- `body_de` wird bedingungslos geschrieben und in der Schleife uebersprungen. Der Absatz an der Zeile trennt die beiden Eigenschaften, die der naechste Leser fuer eine haelt: gespeichert zu sein ist die Speicherung des ganzen Systems und haengt nie an der Sprachmenge, von der deutschen Kette analysiert zu werden haengt daran.
- `info.xml` nennt die sechs Codes, behaelt die Werkseinstellung und den Rueckfallsatz, und ersetzt den falschen Rat "der Index muss danach neu gebaut werden" durch die wahre Aussage: Findling baut selbst um, die Suche antwortet weiter, ein `occ findling:index --restart` ist dafuer nicht noetig.
- `docs/language-analyzers.md` hat einen Abschnitt "Switching a language on, and when it takes effect", der die Grenze aus 18-RESEARCH Pitfall 7 als Zusage ausspricht: `settings()` ist prozessweit zwischengespeichert und die Driftpruefung sitzt im Startpfad, also wirkt ein Sprachwechsel nach dem Neustart des Containers.
- Die Baumhash-Ratsche traegt `9ee107fb...` mit einem zwanzigsten Absatz, der `config.py` und `index/writer.py` einzeln nennt. `PACKAGE_FILES_TODAY` bleibt bei 55, weil keine Datei kam und keine ging.

## Task Commits

1. **Task 1 RED: Tests fuer sechs waehlbare Sprachen** - `cb61315` (test)
2. **Task 1 GREEN: `_languages()` gegen `SUPPORTED_LANGUAGES`** - `96d8333` (feat)
3. **Task 2 RED: Tests fuer die aktive Sprachmenge im Writer** - `f2f384a` (test)
4. **Task 2 GREEN: Befuellungsschleife ueber die aktive Menge** - `5b4985b` (feat)
5. **Task 3: Adminbeschreibung, Doku und Ratsche** - `661c6f2` (docs)

## Files Created/Modified

- `backend/src/findling/config.py` - Filter von `DEFAULT_LANGUAGES` auf `SUPPORTED_LANGUAGES`, neuer Docstring an `_languages()`, fortgeschriebener Kommentarblock an `SUPPORTED_LANGUAGES`
- `backend/src/findling/index/writer.py` - Konstruktorparameter `languages`, `BODY_FIELD`-Import statt `FIELD_BODY_EN`, Schleife in `add()`, Absatz ueber gespeichert gegen analysiert
- `backend/appinfo/info.xml` - Beschreibung von `FINDLING_LANGUAGES`: sechs Codes, Werkseinstellung, Rueckfall, wahrer Umbauweg, Neustarthinweis
- `backend/tests/test_config.py` - sechs neue Tests: `es,de` in Schemaordnung, `es` allein, jeder Code einzeln, leere Werte, Warnung ohne Wert, Stillstand der Werkseinstellung
- `backend/tests/test_index_writer.py` - drei neue Tests: drei befuellte gegen drei leere Koerperfelder ueber `terms_with_prefix`, gespeichertes `body_de` unter `FINDLING_LANGUAGES=es`, Konstruktorparameter
- `backend/tests/test_measurement_scripts.py` - zwanzigster Ratschenabsatz, neuer `PACKAGE_TREE_HASH_TODAY`
- `docs/language-analyzers.md` - neuer Abschnitt zur Wahl der Sprachmenge und zur Neustartgrenze

## Decisions Made

- **Gefiltert wird gegen `SUPPORTED_LANGUAGES`, nicht gegen `SNOWBALL_NAME.keys()`.** 18-RESEARCH nennt die Schluessel von `SNOWBALL_NAME`, `18-PATTERNS` nennt beide Mengen, und ein Paritaetstest aus Plan 18-01 haelt sie ohnehin deckungsgleich. Den Ausschlag gibt die Ordnung: `SUPPORTED_LANGUAGES` ist ein Tupel in Schemafeldreihenfolge, `SNOWBALL_NAME` ist eine Abbildung, und der Sprachmerker von Plan 18-04 haengt an genau dieser Ordnung. Die `must_haves` des Plans verlangen `for language in SUPPORTED_LANGUAGES` woertlich.
- **Die Sprachmenge wird im Konstruktor zu einem Tupel eingefroren.** Der Parameter ist eine `Sequence`, also koennte der Aufrufer eine Liste behalten und sie waehrend eines laufenden Stapels aendern. Ein Stapel, dessen erste Haelfte in drei und dessen zweite Haelfte in vier Felder geschrieben wurde, ist ein Index, den keine Marke beschreibt.
- **`body_de` steht ausserhalb der Schleife und wird in ihr uebersprungen.** Die Alternative waere, `de` aus der Schleifenmenge zu nehmen, was dasselbe Ergebnis mit einer stillen Voraussetzung mehr erreicht. So steht die Bedingung sichtbar an der Stelle, an der sie gilt, und der Grund (doppelte Postings fuer nichts) steht daneben.
- **`occ findling:index --restart` bleibt in `info.xml` stehen, als Verneinung.** Das Abnahmekriterium sagt "enthaelt keinen `occ findling:index --restart`-Rat", die Aktionsbeschreibung desselben Tasks verlangt den Satz "ein `occ findling:index --restart` ist dafuer ausdruecklich nicht noetig". Gemeint ist der Rat, nicht die Zeichenkette: `grep -c "currently de and en"` meldet 0, und der einzige Treffer auf den Befehl steht in einer Verneinung. Die Aktionsbeschreibung ist die genauere der beiden Aussagen und gibt den Ausschlag.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Test fuer die Warnung ohne Wert ergaenzt**
- **Found during:** Task 1
- **Issue:** Der `<behavior>`-Block verlangt eine Warnung, "die den Variablennamen nennt und nie den Wert", und das Threat-Register fuehrt genau das als `T-18-02-02` mit Disposition `mitigate`. Die Suite hatte dafuer keine Zusicherung: der vorhandene Test prueft nur den Rueckfallwert.
- **Fix:** `test_the_warning_for_an_unknown_language_never_repeats_the_value` prueft ueber `caplog` beide Haelften, dass `FINDLING_LANGUAGES` in der Meldung steht und der eingegebene Wert nicht.
- **Files modified:** backend/tests/test_config.py
- **Verification:** Test gruen, und rot, wenn man versuchsweise den Wert in die Meldung setzt
- **Committed in:** `cb61315` (Task-1-RED-Commit)

### Abweichungen in der Schreibweise, nicht in der Sache

- Die Abnahmekriterien von Task 1 verlangen "Neue Tests ... jeder mit `monkeypatch.setenv` und geleertem `settings`-Cache". Der Test `test_the_factory_setting_stays_at_two_entries` prueft zwei Konstanten und liest keine Umgebungsvariable, braucht also weder das eine noch das andere. Er gehoert trotzdem in diese Charge, weil das Kriterium `grep -n "DEFAULT_LANGUAGES = "` eine Zusicherung im Code verdient und nicht nur einen Befehl im Plan.
- Der Konstruktorparameter heisst `languages` und nicht `language_set`; `<action>` schreibt `languages: Sequence[str] | None` woertlich vor, und die Aufloesung folgt mit `resolved.languages` derselben Form wie `min_free_bytes`.

---

**Total deviations:** 1 auto-fixed (1 fehlende Sicherheitszusicherung)
**Impact on plan:** Keine Scope-Ausweitung. Der ergaenzte Test deckt eine Zeile ab, die der Plan als Verhalten fordert und das Threat-Register als Minderung fuehrt.

## Issues Encountered

- Die volle Suite war nach Task 2 an genau einer Stelle rot, dem Baumhash der Ratsche. Das ist kein Befund, sondern die Ratsche, die ihre Arbeit tut: sie meldet, dass zwei Dateien des Pakets ihre Bytes bewegt haben, und Task 3 zieht sie nach.
- Zwei Werkzeugaufrufe mit eingebettetem Python wurden von der Worktree-Absicherung abgelehnt, weil sie sich nicht als innerhalb des Arbeitsbaums verifizieren liessen. Die betroffenen Aenderungen sind stattdessen mit `Edit` gemacht worden; am Ergebnis aendert das nichts.

## Verification

- `cd backend && uv run python -m pytest -q` - **2567 bestanden, 15 uebersprungen** (4 min 30 s)
- `uv run ruff check` - All checks passed
- `uv run ruff format --check` - 129 files already formatted
- `uv run pyright` - 0 errors, 0 warnings, 0 informations
- `uv run vulture` - keine Befunde
- `grep -rn "index_english" backend/ --include=*.py` - keine Treffer
- `grep -v '^ *#' backend/src/findling/config.py | grep -c "for language in DEFAULT_LANGUAGES"` - 0
- `grep -c "No production path reads this constant" backend/src/findling/config.py` - 0
- `grep -c "currently de and en" backend/appinfo/info.xml` - 0
- `grep -n "DEFAULT_LANGUAGES = " backend/src/findling/config.py` - weiterhin `("de", "en")`
- Baumhash-Rezept ueber `backend/src/findling`: `dateien: 55`, `baumhash: 9ee107fbb1bda734022c5ee3a9c967e2d6aa11181078ba1062120603611a24e1`

## Threat Flags

Keine. Die vier Eintraege des Registers sind abgearbeitet: `T-18-02-01` durch den Filter gegen `SUPPORTED_LANGUAGES`, `T-18-02-02` durch den neuen Warnungstest, `T-18-02-03` durch die ausschliessliche Herkunft der Feldnamen aus `BODY_FIELD`, `T-18-02-04` unveraendert als bewusst angenommenes Verhalten (Rueckfall statt Startverweigerung). Keine neue Netzwerk-, Auth- oder Dateizugriffsflaeche.

## Known Stubs

Keine.

## Self-Check: PASSED

Alle sieben genannten Dateien liegen im Baum, und alle fuenf Commits (`cb61315`, `96d8333`, `f2f384a`, `5b4985b`, `661c6f2`) stehen im Verlauf ueber `d8f628a`.
