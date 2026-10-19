---
phase: 34-umstiegsweg
audited: 2026-10-19
diff: 00dbafab..a701b4f9
files_reviewed: 39
findings:
  critical: 0
  high: 0
  medium: 0
  low: 2
  total: 2
status: in_progress
still_open: [L-34-01, L-34-02]
---

# Phase 34: Security-, Bug- und Performance-Audit

**Stand:** Task 1 (Sicherheit) und Task 2 (Fehler) am 19.10.2026.

**Umfang:** `git diff 00dbafab..a701b4f9` (Basis = Elternteil von d5258548, dem ersten Commit
mit "(34-02)"; 16 Commits). Mit Planung 47 Dateien, 2 193 Zeilen dazu, 44 weg; ohne
`.planning/` 39 Dateien (1 539 dazu, 27 weg). Gelesen bzw. per Probe gefahren:
`php/lib/Service/{ParallelSearchService,AdminViewService}.php`, `php/templates/admin.php`
(Banner, Sprach-Map, Link, Button-Klasse `findling-banner__link` aus der Owner-Runde 34-05),
`php/css/admin.css`, 16 Kataloge unter `php/l10n/`, die PHPUnit-Dateien
`ParallelSearchServiceTest.php` und `SettingsControllerTest.php`, die drei Umstiegs-Seiten
`docs/migrate-from-fulltextsearch{,.en,.fr}.md`, `docs/admin-page.md` (neuer Abschnitt), die
fünf l10n-Dokus, `README{,.en,.fr}.md`, `docs/store-listing.md` (Abschnitt Phase 34),
`CHANGELOG.md`, die Gates `backend/tests/test_migration_path.py` und
`backend/tests/test_admin_ui_contract.py` (Banner- und Linkgate) und die Baumhash-Ratsche in
`backend/tests/test_measurement_scripts.py`. `php/js/admin.js` ist seit der Basis
unverändert (PE-34-2) und nur als Leser des Banners geprüft: kein Zugriff auf
`findling-banner-parallel` (`grep -n "findling-banner" php/js/admin.js`, nur die sieben
bestehenden Banner).

Die Proben stehen als Regressionstests in `backend/tests/test_phase34_audit.py`:

- **Quelltextproben** (Docker): `token_get_all` von PHP selbst auf `php:8.3-cli` (Skript im
  Test als String), also ein anderes Werkzeug als das Kontrakt-Gate
  (`test_admin_ui_contract.py`, reguläre Ausdrücke), mit Positivkontrolle an einer
  synthetischen Vorlage.
- **Renderproben** (Docker): das Banner-Fragment des echten Templates, per Position
  ausgeschnitten und mit einem `p()` wie im Kern (`htmlspecialchars`, `ENT_QUOTES`, UTF-8)
  und einem IL10N-Stub ausgeführt; das HTML liest `html.parser`, kein regulärer Ausdruck.
- **Instanzproben** (ohne `FINDLING_AUDIT34_URL` übersprungen): Rechte, Logprobe,
  Bannerentscheidung gegen SQL.

**Wo gelaufen:** Windows 11 Pro 10.0.26200; `php:8.3-cli`; Instanz `findling-nextcloud`
(http://localhost:8090, Nextcloud 34.0.3, SQLite, `php/` des Hauptcheckouts als Bind-Mount,
inhaltsgleich mit dem Worktree bis auf Zeilenenden, geprüft mit `diff -rq` und
`diff --strip-trailing-cr`). Freier RAM vor den Proben 3,9 GB, alles seriell.

**Aufruf:** aus `backend/` mit `PYTHONUTF8=1` und den Variablen aus dem Modulkopf
(`FINDLING_AUDIT34_URL`, `..._ADMIN_PASS`, `..._USER=audit34user`, `..._USER_PASS`,
`..._CONTAINER=findling-nextcloud`; Passwörter nur per Umgebung). `audit34user` ist ein für
das Audit angelegtes Konto ohne Gruppen (`occ user:add --password-from-env`), nach dem Audit
gelöscht.

```
uv run python -m pytest -q tests/test_phase34_audit.py -rxXs -p no:randomly
```

## Security

### S1 Quelltextprobe der Ausgaben (token_get_all)

Gefahren: `test_the_token_probe_sees_every_unescaped_output_and_a_foreign_url`
(Positivkontrolle) und
`test_every_output_of_the_banner_goes_through_p_and_the_href_comes_from_three_literals`,
19.10.2026.

- **Positivkontrolle:** eine synthetische Vorlage mit `echo`, `<?=`, `print`,
  `print_unescaped`, `p($l->t($key))`, einer URL aus `$_`, einem Nicht-Literal in der Map und
  einem späteren Schreiben in die Map: alle acht Fehlerarten erkannt.
- **Echtes Template:** im ganzen `admin.php` kein `T_ECHO`, `T_PRINT`,
  `T_OPEN_TAG_WITH_ECHO`, `T_EVAL` und kein Aufruf von `print_unescaped`, `printf`,
  `print_r`, `var_dump`, `var_export`, `readfile`. Im Banner sechs PHP-Blöcke: `if`/`}` für
  `hidden` (druckt nichts) und vier Ausgaben, jede genau `p(...)`: das Icon, der Satz
  `p($l->t('<Literal>'))`, das href `p($migrationDocsUrl)`, der Linktext
  `p($l->t('<Literal>'))`. `$migrationDocsUrl` wird genau einmal zugewiesen, aus
  `$migrationDocsUrls[...]`; die Map genau einmal, nur aus String-Literalen, Werte genau die
  drei Tag-URLs `blob/v1.5.0/docs/migrate-from-fulltextsearch{.md,.fr.md,.en.md}`; kein
  späteres Schreiben in die Map.

Ergebnis: grün, kein Befund.

### S2 Kataloge und Renderprobe mit Markup

Gefahren: `test_no_catalogue_value_of_the_two_banner_keys_carries_markup_or_a_url` (mit
Positivkontrolle `test_the_markup_scan_of_the_catalogues_sees_a_planted_value`),
`test_markup_in_a_catalogue_value_renders_as_text` (mit Positivkontrolle
`test_the_render_probe_sees_markup_when_p_does_not_escape`) und
`test_the_banner_is_hidden_unless_the_flag_is_exactly_true`.

- 16 Kataloge (`php/l10n/*.json` und `*.js`, die `.js` per `raw_decode` ab der ersten
  Klammer gelesen): beide Schlüssel (Satz und "Steps in the documentation") in allen 16
  vorhanden; kein Wert enthält `<`, `>`, `"`, `http`, `://`, `www.`, `street1983nk` oder
  `.md`.
- Statt einer Katalogkopie auf 8090 (die Kataloge liegen im Bind-Mount des Hauptcheckouts,
  den ein Worktree-Audit nicht beschreibt) lief das echte Template-Fragment mit einem
  Katalogwert `<b id="inj">x</b><script>alert(1)</script>" onmouseover="alert(2)` für Satz
  und Linktext (de) bzw. nur Linktext (fr): Elementfolge bleibt `p, svg, path, span, a`, der
  Wert steht als Text im `span` und im `a`, kein Attribut `onmouseover`, das `a` trägt genau
  `class`, `href`, `target="_blank"`, `rel="noreferrer noopener"`. Positivkontrolle: mit einem
  `p()`, das roh druckt, erscheinen `b` und `script` als Elemente.
- `hidden` fehlt nur bei `parallelSearch === true`; bei `false`, `null`, `1`, `"1"`,
  `"true"`, `[]`, `[true]` steht es.

Ergebnis: grün, kein Befund.

### S3 Rechte

Gefahren: `test_a_non_admin_never_sees_the_overview_or_the_page` auf 8090 mit simuliertem
Flag (`occ config:app:set fulltextsearch enabled --value=yes`), Positivkontrolle als admin
(Übersicht trägt `parallelSearch: true`, Seite zeigt den Banner sichtbar).

| Anfrage | Status | Inhalt |
|---|---|---|
| audit34user `GET /apps/findling/admin/overview` mit Token | 403 | `{"message":"Logged in account must be an admin"}`, kein `parallelSearch` |
| audit34user dieselbe Route ohne Token | 403 | |
| audit34user `GET /settings/admin/findling` | 403 | 18 449 Byte Fehlerseite des Kerns, kein `findling-coverage`, kein Banner, kein Link |
| anonym `GET /apps/findling/admin/overview` | 401 | |

Flag danach entfernt (`config:app:delete`), SQL-Probe `oc_appconfig` ohne Zeile. Kein
Rechteleck.

### S4 Logprobe

Gefahren: `test_toggling_the_flag_writes_no_log_line_with_an_app_id`: dreimal Flag
`fulltextsearch` = yes per occ, gewartet, bis die Übersicht `true` meldet (Zwischenspeicher
der AppConfig, 2 bis 4 s), Seite geladen (Banner sichtbar), Flag gelöscht, gewartet auf
`false`, Seite geladen (Banner `hidden`). Gelesen: neue Zeilen von `nextcloud.log` seit
Laufbeginn und `docker logs --since` des Containers. Positivkontrolle mit Marker
`zz34ctl<zeit>`: PROPFIND mit diesem Login-Namen (Kern schreibt "Login failed") und
`GET /index.php/<marker>` (Access-Log); in beiden Quellen gefunden.

Ergebnis: **keine Zeile** nennt `fulltextsearch` oder `files_fulltextsearch`, weder von
Findling noch vom Kern. Kein Befund.

### S5 Gedankenstriche, Verbotsscan, REUSE, Store-Archiv

- `git diff 00dbafab..a701b4f9 | grep "^+" | LC_ALL=C.UTF-8 grep -cP "\x{2013}|\x{2014}"`:
  **2**, beide in `.planning/STATE.md` (Zeilen "Current focus: Phase 34 ... umstiegsweg" und
  "Phase: 34 (umstiegsweg) ... EXECUTING"), geschrieben vom Werkzeug `gsd-sdk`, nicht
  ausgeliefert. Ohne `.planning/`: 0. Positivkontrolle mit einer Probedatei mit U+2013: 1.
  Siehe **L-34-01**. Ohne Git-Verlauf prüft `test_no_file_of_the_phase_carries_an_en_or_em_dash`
  die 23 Produktdateien der Phase: 0.
- `LC_ALL=C grep -nP "[^\x00-\x7F]" backend/tests/test_phase34_audit.py`: leer.
- Verbotsscan `uv run python -m pytest -q tests/test_migration_path.py tests/test_admin_ui_contract.py -p no:randomly`:
  218 passed.
- `uvx --from "reuse[charset-normalizer]" reuse lint`: 2758 / 2758, konform.
- `bash scripts/release/store-archive.sh stage-companion <scratch>/stage`: Exit 0;
  `lib/Service/ParallelSearchService.php`, `lib/Service/AdminViewService.php`,
  `templates/admin.php`, `css/admin.css`, `l10n/de.json`, `l10n/fr.js` im Archiv und
  byte-gleich mit dem Repo (`cmp`); `tests/` nicht im Archiv.

## Bugs

Gefahren am 19.10.2026 zwischen 15:20 und 15:45 Ortszeit, alle Fälle als Tests des Moduls:

```
FINDLING_AUDIT34_NETWORK=1 FINDLING_AUDIT34_URL=http://localhost:8090 ... uv run python -m pytest -q tests/test_phase34_audit.py -rxXs -p no:randomly
```

Ergebnis des ganzen Moduls mit Instanz und Netz: **31 passed, 1 xfailed** (L-34-02). Die
Mutationsproben dazu mit `FINDLING_AUDIT34_MUTATION=1 ... -k "mutation or unmutated"`:
**7 passed**.

| Nr. | Fall (Plan) | Verfahren (anders als die Umsetzung) | Ergebnis | Urteil |
|---|---|---|---|---|
| B1 | Sprach-Map | Orakel als Tabelle im Test aus der Regel "beginnt mit de: `.md`, mit fr: `.fr.md`, sonst `.en.md`" (`code[:2]`, nicht `str_starts_with`), Selbstprobe der Tabelle gegen die Regel; Wahl des Templates über das echte Fragment auf `php:8.3-cli` mit IL10N-Stub, href aus dem DOM (`test_the_link_of_the_template_follows_the_oracle_for_every_language`) | 14 Codes: de, de_DE, de_CH, fr, fr_CA, en, en_GB, es, pt_BR, nl, cs, leerer Code, dazu dsb und fur (beginnen mit d bzw. f, aber nicht mit de/fr): alle 14 gleich dem Orakel | in Ordnung |
| B2 | Bannerentscheidung gegen SQL | `SELECT appid, configvalue FROM oc_appconfig WHERE configkey = 'enabled' AND appid IN (...)` per PDO im Container; Wahrheit "Zeile mit Wert ungleich `no`" (Definition des Kerns, `AppManager::getEnabledAppsValues`, NC 34.0.3 Zeile 158 bis 176); DOM der Seite per `html.parser` (`test_the_banner_agrees_with_the_appconfig_rows_in_every_case`) | sechs Fälle: keine Zeile (verborgen), fulltextsearch `yes` (sichtbar), files_fulltextsearch `yes` (sichtbar), fulltextsearch `["findling-probe34"]` mit admin nicht in der Gruppe (sichtbar), fulltextsearch `no` (verborgen), beide `no` (verborgen); Übersicht `parallelSearch` und DOM stimmen in allen sechs mit der SQL-Wahrheit überein | in Ordnung |
| B3 | Faktenprüfung | App-Store-API `platform/{32.0.0,33.0.0,34.0.3,35.0.0}/apps.json` und GitHub-Releases-API per `curl` und `jq` am 19.10.2026 um 13:21 UTC (Rohdaten im Scratch `34-06/store-*.json`, `rel-*.json`), unabhängig von der `gh`-Abfrage aus 34-01; im Test zusätzlich per `httpx` neu abgefragt (`test_every_claim_holds_in_the_app_store_and_on_github_today`, `FINDLING_AUDIT34_NETWORK=1`) | Tabelle "Faktenprüfung" unten: alle elf Aussagen gleich, auf allen drei Seiten (`test_every_fact_of_the_page_is_a_claim_of_the_audit`, jede Version und jedes Datum im Abschnitt Pflegestand ist eine Aussage der Tabelle, keine ungeprüfte); kein neueres Release seit dem Schreiben der Seiten | in Ordnung |
| B4 | Pflichtformel und Umschalter | Zeile 1 per Gleichheit; Formel zeilenweise wie `grep -F`, nicht über das Gate (`_flat` fügt Zeilen zusammen) | Umschalter in allen drei Seiten exakt; Formel de und en je in einer Zeile, **fr über einen Zeilenumbruch** ("l'OCR sans modifier" / "les fichiers et sans Elasticsearch", Zeile 7 bis 8) | **L-34-02** |
| B5 | Relative Links | eigene Zerlegung der Linkziele per `str.split` (kein regulärer Ausdruck), Existenz des Pfads (`test_every_relative_link_of_pages_and_readmes_resolves`, Positivkontrolle `test_the_link_check_sees_a_missing_target`); `lychee` ist nicht installiert | drei Seiten und drei READMEs: alle relativen Ziele vorhanden | in Ordnung |
| B6 | Gate-Qualität | Kopie des Baums im Temp-Verzeichnis (ohne `docs/measurements`), je Mutation die zwei Gate-Module dort gefahren, rote Tests aus `-rf` gelesen (`test_each_mutation_turns_exactly_its_gate_red`); Erwartung vor dem Lauf im Test notiert | unmutierte Kopie grün; Formel entfernt (de): nur `test_pages_exist_with_switch_line_and_formula`; Verbotsformel en und fr: je nur `test_forbidden_claim_occurs_in_no_shipped_file`; README.en.md auf die deutsche Seite: nur `test_readme_sections_link_the_page_of_their_language`; Store-Entwurf auf `blob/main`: nur `test_draft_section_of_phase_34_carries_a_tag_link_per_language`; fünfter Doku-Link im Template: nur `test_the_change_hint_links_the_anchor_of_the_documentation` | in Ordnung |
| B7 | Schritte gegen 34-02-NACHWEIS | Befehle der Schritte (Inline-Code mit `occ`/`--` und SQL-Block) gegen den Text des Protokolls, je Sprache (`test_every_command_of_the_steps_is_in_the_protocol_or_marked`) | je Seite neun Befehle; wörtlich im Protokoll: `occ fulltextsearch:stop`, `occ fulltextsearch:reset`, `--no-interaction`, die drei SQL-Zeilen; abgedeckt anders: `occ fulltextsearch:live` (nur Quelle, Zeile 7a, Seite verlinkt das Wiki), `occ app:remove <app-id>` (Zeile 5b), `occ app:disable files_fulltextsearch fulltextsearch_elasticsearch fulltextsearch` (Zeilen 4 und 4b; im Audit zusätzlich wörtlich auf 8090 gefahren: drei Zeilen "No such app enabled", Exit 0, keine appconfig-Zeile, `test_the_disable_command_of_the_page_takes_three_ids_in_one_call`) | in Ordnung |

**Faktenprüfung** (Abfrage 19.10.2026, 13:21 UTC; Store = Feld `created`, GitHub =
`published_at`):

| Aussage der Seiten | Store / GitHub am Audit-Tag | Urteil |
|---|---|---|
| fulltextsearch Release v35.0.0 am 20.09.2026 | GitHub v35.0.0 published 2026-09-20 (neuestes stabiles) | gleich |
| fulltextsearch 33.0.3 (20.09.2026) für Nextcloud 33 bis 35 | Store 33.0.3 created 2026-09-20, `>=33.0.0 <36.0.0` | gleich |
| fulltextsearch 34.0.2 und 35.0.0 (18.09.2026) | Store 34.0.2 und 35.0.0 created 2026-09-18 | gleich |
| files_fulltextsearch 34.0.1 (06.08.2026) für Nextcloud 34 | Store 34.0.1 created 2026-08-06, `>=34.0.0 <35.0.0` | gleich |
| files_fulltextsearch 35.0.0 (18.09.2026) für Nextcloud 35 | Store 35.0.0 created 2026-09-18, `>=35.0.0 <36.0.0` | gleich |
| fulltextsearch_elasticsearch v35.0.1 und v34.0.3 am 07.10.2026 | GitHub beide published 2026-10-07 | gleich |
| files_fulltextsearch_tesseract nur 32.0.0 (19.01.2026) für Nextcloud 32, keins für 33 bis 35 | Store genau ein Release 32.0.0, created 2026-01-19, `>=32.0.0 <33.0.0`; in den Listen 33.0.0, 34.0.3, 35.0.0 nicht vorhanden | gleich |
| fulltextsearch_sql 1.5.1 (14.10.2026) | Store 1.5.1 created 2026-10-14 (neuestes) | gleich |
| fulltextsearch_postgresql 0.1.4 (10.10.2026) | Store 0.1.4 created 2026-10-10 (neuestes) | gleich |
| Deck liefert seine Karten an fulltextsearch | `nextcloud/deck` `appinfo/info.xml` auf `main`, Zeile 80 bis 82 `<fulltextsearch>` | gleich |

Positivkontrolle der Faktenprüfung: ein auf der Seite geändertes Datum (14.10. zu 15.10.)
ist ein Unterschied (`test_the_fact_check_sees_a_wrong_date`).

**Aufräumen:** jeder Instanzfall räumt im `finally` beide Schlüssel `enabled`; die Fixture
prüft vorher und nachher per SQL, dass keine Zeile steht. Nach dem Lauf:
`SELECT ... configkey = 'enabled' AND appid IN (...)` leer.

## Befunde

### L-34-01 (LOW): Zwei Geviertstriche in STATE.md

- **Ort:** `.planning/STATE.md` (Kopfzeilen "Current focus" und "Phase"), geschrieben von
  `gsd-sdk query state.*`.
- **Beleg:** S5, `git diff ... | grep -cP` 2, ohne `.planning/` 0.
- **Einordnung:** nicht ausgeliefert, nicht öffentlich auf einer Seite; das Werkzeug setzt
  das Zeichen selbst. STATE.md gehört dem Orchestrator, der Worktree-Agent schreibt es nicht.
- **Fixvorschlag:** an den Orchestrator melden (Werkzeugausgabe nach dem Schreiben
  nachziehen); kein Produktfix.

### L-34-02 (LOW): Die französische Pflichtformel steht über einem Zeilenumbruch

- **Ort:** `docs/migrate-from-fulltextsearch.fr.md:7` bis `8`.
- **Beleg (gefahren, B4):** `grep -cF "OCR sans modifier les fichiers et sans Elasticsearch"`
  auf die Datei: 0; de und en: je 1. `test_the_formula_stands_on_one_line_of_the_page[fr]`
  rot (strict xfail bis Task 4).
- **Einordnung:** gerendert steht die Formel vollständig (Markdown macht aus dem Umbruch ein
  Leerzeichen), das Gate von 34-02 fügt die Zeilen zusammen und ist grün. Eine
  zeilenweise Suche (grep, ein Abgleich gegen den Store-Text) findet sie nicht. Kein falscher
  Satz, kein sichtbarer Unterschied.
- **Fixvorschlag:** die Zeilen 7 bis 8 so umbrechen, dass die Formel in einer Zeile steht;
  Wortlaut unverändert.
