---
phase: 34-umstiegsweg
audited: 2026-10-19
diff: 00dbafab..a701b4f9
files_reviewed: 39
findings:
  critical: 0
  high: 0
  medium: 0
  low: 1
  total: 1
status: in_progress
still_open: []
---

# Phase 34: Security-, Bug- und Performance-Audit

**Stand:** Task 1 (Sicherheit) am 19.10.2026.

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

## Befunde

### L-34-01 (LOW): Zwei Geviertstriche in STATE.md

- **Ort:** `.planning/STATE.md` (Kopfzeilen "Current focus" und "Phase"), geschrieben von
  `gsd-sdk query state.*`.
- **Beleg:** S5, `git diff ... | grep -cP` 2, ohne `.planning/` 0.
- **Einordnung:** nicht ausgeliefert, nicht öffentlich auf einer Seite; das Werkzeug setzt
  das Zeichen selbst. STATE.md gehört dem Orchestrator, der Worktree-Agent schreibt es nicht.
- **Fixvorschlag:** an den Orchestrator melden (Werkzeugausgabe nach dem Schreiben
  nachziehen); kein Produktfix.
