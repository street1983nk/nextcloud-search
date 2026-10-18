---
phase: 33-ausschlussmuster-und-admin-feinschliff
audited: 2026-10-18
diff: 12a73359..92441a16
files_reviewed: 61
findings:
  critical: 0
  high: 2
  medium: 0
  low: 4
  total: 6
status: issues_found
---

# Phase 33: Security-, Bug- und Performance-Audit

**Stand:** Task 1 (Sicherheit) abgeschlossen am 18.10.2026. Task 2 (Fehler), Task 3
(Performance) und Task 4 (Fixes, LOW-Entscheidungen, Abschluss) folgen; `fix_run`,
`fix_commits`, `fixed` und `still_open` trägt erst Task 4 ein.

**Umfang:** `git diff 12a73359..92441a16` (Basis = Elternteil von 75f5f29e, dem ersten
Commit mit "(33-02)"; 21 Commits). Mit Planung 75 Dateien, 10 030 Zeilen dazu, 551 weg;
ohne `.planning/` 61 Dateien (8 023 dazu, 390 weg). Gelesen bzw. per Probe gefahren:
`php/lib/Service/{ExclusionService,FileStateService,AdminViewService,QueueService,SettingsService,PurgeService}.php`,
`php/lib/BackgroundJobs/{ExclusionSweepJob,SubtreeExpandJob}.php`,
`php/lib/Controller/{SettingsController,ReconcileController}.php`,
`php/lib/Listener/FileEventListener.php`, `php/templates/admin.php`, `php/js/admin.js`,
`php/css/admin.css`, 16 Kataloge unter `php/l10n/`, `backend/src/findling/worker/reconcile.py`,
`backend/src/findling/api/status.py`, `docs/admin-page.md`, `docs/reconcile.md`, die fünf
l10n-Dokus, `docs/store-listing.md`, der Treiber `backend/tests/drivers/exclusion_driver.php`
samt Fixture von 1.4.2 und die PHPUnit- und pytest-Dateien der Phase.
`StorageCrawlJob.php` ist seit der Basis unverändert und nur als Aufrufstelle geprüft.

Die Proben stehen als Regressionstests in `backend/tests/test_phase33_audit.py`, in drei
Gruppen:

- **Orakel über den Treiber** (Docker, sonst übersprungen): ein Python-Orakel, geschrieben
  aus `docs/admin-page.md` Abschnitt "Ausschlussmuster" (Semantik in Prosa im Modul
  festgehalten), als rekursive Definition `fits(i, j)` über Zeichenlisten mit Memo-Tabelle,
  ohne `fnmatch`, ohne regulären Ausdruck, ohne Bitmasken. Die PHP-Antworten kommen aus dem
  echten `php/lib/Service/ExclusionService.php` über den unveränderten Treiber von 33-02.
- **Quelltextproben** (Docker): `token_get_all` von PHP selbst in einem Einmalskript (im
  Test als String), also ein anderes Werkzeug als Gate D (`test_exclusion_path_space.py`,
  reguläre Ausdrücke). Mit Positivkontrolle an einer synthetischen Klasse.
- **Instanzproben** (ohne `FINDLING_AUDIT33_URL` übersprungen): Ablehnungskorpus,
  Zweitschreiber per `occ`, Rechte, NFC auf der echten Laufzeit, Logprobe.

**Wo gelaufen:** Windows 11 Pro 10.0.26200; Treiber auf `php:8.3-cli` (PHP 8.3.33) und
zusätzlich auf `nextcloud:34.0.3-apache` (PHP 8.5.9 mit intl, Laufzeit der Instanz);
Instanz `findling-nextcloud` (http://localhost:8090, Nextcloud 34.0.3, SQLite, `php/` als
Bind-Mount), Backend 1.4.2 als Host-Prozess auf Port 10035 (`.dev/exapp.log`).

**Aufruf:** aus `backend/` mit `PYTHONUTF8=1` und den Variablen aus dem Modulkopf
(`FINDLING_AUDIT33_URL`, `..._ADMIN_PASS`, `..._USER=testuser`, `..._USER_PASS`,
`..._CONTAINER=findling-nextcloud`, `..._BACKEND_LOG`, `..._BACKEND_URL`; Passwörter nur
per Umgebung):

```
uv run python -m pytest -q tests/test_phase33_audit.py -rxXs -p no:randomly
FINDLING_AUDIT33_PHP_IMAGE=nextcloud:34.0.3-apache uv run python -m pytest -q tests/test_phase33_audit.py -rxXs -p no:randomly
```

Rohausgaben (Korpus, Antworten, Logsuche) mit `FINDLING_AUDIT33_OUT` im Scratch, nicht im
Repo.

## Security

### S1 Orakel-Korpus gegen den echten Matcher

Gefahren: `uv run python -m pytest -q tests/test_phase33_audit.py -rxXs -p no:randomly -k "oracle or corpus or comparison or list_in_force or driver_log"`
am 18.10.2026, einmal auf `php:8.3-cli` und einmal mit
`FINDLING_AUDIT33_PHP_IMAGE=nextcloud:34.0.3-apache`.

Korpus (`random_runs()` und `edge_runs()`, Startwert 3311): **2593 Paare** in 73
Treiberläufen, davon **2352 zufällig** (60 Läufe, je 1 bis 3 erzeugte Muster, je Muster 16
verwandte Pfade aus Instanziierung, Vorfahren, Nachfahren und Mutation plus 8 Zufallspfade;
in 30 Prozent der Läufe zusätzlich ein unbrauchbarer Rohwert aus `UNUSABLE`, in 18 Prozent
eine Rohschreibweise mit `/` außen, `files/`, Leerraum oder `//`). Feste Gruppen:

| Gruppe | Paare | Inhalt |
|---|---|---|
| `doc_examples` | 13 | die Tabelle "Syntax" der Doku, Zeile für Zeile |
| `empty_segments` | 13 | `a//*.q`, `//*.k//`, `x/ /*y`, `/files//m/*`, `files/files/*.f` gegen Pfade mit `//` und `/` außen |
| `star_edges` | 16 | `*` vorn, hinten, beidseitig; `*/node_modules/*` oben im Home; `Backups/*` gegen den Ordner selbst |
| `question_before_slash` | 12 | `a?/*.t`, `?/x*`, `*/?`, `Scan_??.pdf` gegen `/` an der Stelle von `?` |
| `multibyte` | 13 | `Caf?`, `?` vor CJK, Emoji (U+1F600, vier Byte), `Ü?er*`, `U<U+0308>ber` (NFD) |
| `nfd_against_nfc` | 8 | NFD-Muster `Cafe<U+0301>*` und `*e<U+0301>` gegen NFC- und NFD-Pfade |
| `long_paths` | 7 | 4000 Zeichen: 1998 Ordnerebenen, ein Name mit 3996 Zeichen, gemischt, zufällig, `node_modules/` vorn |
| `sixty_character_patterns` | 101 | zwölf Muster mit genau 60 Zeichen aus `*`, `?`, `a`, `b`, `/`, `é`, je mit acht verwandten und den langen Pfaden |
| `prefix_and_pattern` | 9 | Präfixe `Archiv`, `Backups/2024` neben Mustern, die dieselben Dateien treffen |
| `white_space_edges` | 9 | Namen mit Leerzeichen vorn und hinten gegen `?x*`, `* `, ` *.k ` |
| `ceiling_and_duplicates` | 40 | 44 Rohwerte mit Doppeln; nur die ersten 32 eindeutigen gelten |

| Lauf | Abweichungen isExcluded | Liste in Kraft (`patterns`) | Ergebnis |
|---|---|---|---|
| `php:8.3-cli` | 5 von 2593, alle in `nfd_against_nfc` | 1 Abweichung, derselbe Lauf | 19 passed, 2 xfailed (**L-33-01**) |
| `nextcloud:34.0.3-apache` | **0 von 2593** | 0 | 21 passed |

Die fünf Abweichungen auf `php:8.3-cli` haben eine Ursache: Das Image hat weder intl noch
den Polyfill von Nextcloud, `ExclusionService::composed()` (Zeile 1295 bis 1303) fällt dann
dokumentiert auf den Rohwert zurück, und das NFD-Muster bleibt NFD. Auf der Laufzeit der
Instanz komponiert dieselbe Datei. Gegengeprüft auf der Instanz
(`test_a_pattern_stored_in_nfd_by_occ_hits_the_nfc_name_on_the_instance`): `Café.txt` (NFC)
per WebDAV angelegt, Diagnose `indexed`; Muster `Audit3311nfc/Cafe<U+0301>*` (NFD) per `occ`
gesetzt; Diagnose danach `skipped` / `excluded` / "Excluded by a rule", die Übersicht zeigt
das Muster als NFC. Kein Matcher-Befund, sondern ein Treiber-Befund: **L-33-01**.

Positivkontrollen: `test_the_oracle_reads_the_examples_of_the_documentation_as_written` (ohne
Docker, die Tabellenzeilen der Doku) und
`test_the_comparison_sees_a_difference_when_there_is_one` (Orakel mit `*.pages`, PHP mit
`*.key`: Unterschied gesehen; mit gleichem Muster gleich). Die Logeinträge aller
Treiberläufe tragen im Kontext nur Ganzzahlen
(`test_the_driver_log_of_the_corpus_carries_counters_only`).

Annahme A1 des Orakels (die Doku beschreibt den Pfadraum, nicht die Form eines übergebenen
Pfads): ein Pfad wird gefaltet wie ein Präfix (`//` zu `/`, `/` außen weg), Leerraum bleibt.
Die Gruppen `empty_segments` und `white_space_edges` bestätigen, dass der Matcher genau so
liest (0 Abweichungen).

### S2 Ablehnungskorpus gegen die Regelrouten

Gefahren: `test_a_refused_entry_names_its_code_never_fails_and_never_echoes` (65 Fälle) und
`test_a_refused_save_writes_nothing`, als admin mit Request-Token
(`/index.php/csrftoken`, Basic-Auth-Sitzung). Jeder Wert läuft gegen
`POST /apps/findling/admin/rules/preview`; jeder, der abgelehnt werden soll, zusätzlich gegen
`POST /apps/findling/admin/rules` mit den drei übrigen Feldern so, wie die Übersicht sie
meldet (57 Fälle). Erwartung je Fall vor dem Lauf in `refusal_cases()`; jeder Wert trägt
den Marker `q33`.

| Code | Varianten (Auswahl) | Vorschau | Speichern |
|---|---|---|---|
| `empty` | `""`, `"   "`, `"///"`, `"/"` | 400 `empty` | 400 `empty` |
| `too_long` | 66 ASCII; 61 Zeichen nach NFC aus 116 NFD-Codepunkten; **4 MB** in einem Eintrag | 400 `too_long` | 400 `too_long` |
| (Grenze) | 60 Zeichen nach NFC aus 114 NFD-Codepunkten | 200 | , |
| `too_many` | 33, 1000, **40 000** Muster | 400 `too_many` | 400 `too_many` |
| `duplicate` | gleich; mit `/` außen; mit `files/`; NFD gegen NFC | 400 `duplicate` | 400 `duplicate` |
| `traversal` | `../*.x`, `a/./*x`, `*/../x`, `x*/..` | 400 `traversal` | 400 `traversal` |
| `double_star` | `**/x`, `x/**`, `*x***`, `x/**/y` | 400 `double_star` | 400 `double_star` |
| `unsupported_character` | `[x]*`, `x{a,b}*`, Backslash, `]x*`, **ungültiges UTF-8** (`%FF` im Formular-Body) | 400 | 400 |
| `negation` | `!*.x`, `!x*`, mit Leerraum davor, nach `/` | 400 `negation` | 400 `negation` |
| `control_character` | LF, **NUL**, BEL, DEL, TAB innen, C1 NEL (U+0085) | 400 | 400 |
| `no_literal` | `*`, `*/*`, `?*`, `*?/?*` | 400 `no_literal` | 400 `no_literal` |
| `no_wildcard` | `x`, `x.key`, **U+FF0A, U+2217, U+204E, U+FE61** (Doppelgänger von `*`), U+FF1F (von `?`) | 400 `no_wildcard` | 400 `no_wildcard` |
| Literal | `*<U+FF0A>x` (Vollbreite neben echtem `*`) | 200, Literal | , |
| Bidi | U+202E innen und vorn, U+2066 | **200, als Literal angenommen: L-33-02** | , |
| Form im Eintrag | Array, verschachteltes Array, Objekt, Zahl, `null`, `true` | 400 `empty` (**L-33-04**) | 400 `empty` |
| Form der Liste | Objekt statt Liste | 200 (`array_values`) | , |
| Form der Liste | **String oder Zahl statt Liste** | 400 ohne Body (Kern) | **HTTP 500: H-33-01** |
| Präfixliste | `../x`, Doppel, 305 Byte | 400 mit Code unter `exclusions` | 400 |

Ergebnis: Vorschau 59 mal 400, 6 mal 200 wie erwartet, nie 5xx; Speichern 55 mal 400, **2 mal
500** (H-33-01). Keine Antwort enthält den Marker. appconfig vor und nach dem Korpus gleich
(`exclusions` `["Archiv"]`, `exclusion_patterns` fehlt, kein ExclusionSweepJob oder
SubtreeExpandJob). Rohdaten `refusals.json`.

### S3 Zweiter Schreiber per occ

Gefahren: `test_a_second_writer_with_garbage_breaks_neither_page_nor_crawl_nor_listener`, je
Wert: Kanarie `["*.q33my"]` per occ gesetzt und abgewartet, bis die Übersicht sie zeigt
(der Webprozess liest appconfig über einen lokalen Zwischenspeicher des Kerns; die
Verzögerung nach einem occ-Befehl lag bei 2 bis 4 Sekunden), dann Schlüssel gelöscht und der
Müll gesetzt, gewartet, bis die Übersicht die laut Doku geltende Liste zeigt, und noch einmal
nach 5 Sekunden. Dann Seite `/settings/admin/findling`, Übersicht, MKCOL und PUT als
testuser (Listener), Queue-Zeile per SQL, `occ findling:diagnose <id>`, und ein echter
Zähl-Crawl: das MKCOL markiert den Scan als veraltet, `occ background-job:execute
--force-execute <ScanRecountJob>` plant drei StorageCrawlJob, cron.php bis keiner mehr da ist.

| Wert (`occ config:app:set findling exclusion_patterns ...`) | in Kraft (Übersicht) | Seite | Übersicht | PUT / Queue | Diagnose | Crawl | Fehler (Level 3+) | Findling-Warnung |
|---|---|---|---|---|---|---|---|---|
| `--value='q33ma not json'` (Typ mixed) | `[]` | 200 | 200 | 201 / 1 | 0 | 3 geplant, 1 cron-Lauf, fertig | 0 | keine |
| `{"a":"*.q33mb"}` `--type=array` | `["*.q33mb"]` | 200 | 200 | 201 / 1 | 0 | fertig | 0 | keine |
| `[1,2.5,{...},null,true,[...],"*.q33me"]` `--type=array` | `["*.q33me"]` | 200 | 200 | 201 / 1 | 0 | fertig | 0 | `unusable: 6, inForce: 1` |
| 1000 Einträge `--type=array` | die ersten 32 | 200 | 200 | 201 / 1 | 0 | fertig | 0 | `dropped: 968, ceiling: 32` |
| `--value=42 --type=integer` | , | **500** | **500** | 201 / **0** | **Exit 1** | , | `AppConfigTypeConflictException` | **H-33-02** |

Die Warnzeilen tragen nur Zähler (Daten geprüft auf den Marker: 0). Die ganzzahlige Form ist
rot: siehe **H-33-02**.

### S4 Rechte und Request-Token

Gefahren: `test_the_rules_routes_refuse_a_non_admin_and_a_request_without_token`, Nicht-Admin
`testuser` mit eigenem Token (Passwort aus `FINDLING_AUDIT33_USER_PASS`):

| Anfrage | Status |
|---|---|
| testuser `POST /admin/rules/preview` mit Token | 403 |
| testuser `POST /admin/rules` mit Token | 403 |
| testuser `GET /admin/overview` mit Token | 403 |
| anonym `POST /admin/rules` | 401 |
| admin `POST /admin/rules` ohne Token | 412 |
| admin `POST /admin/rules/preview` ohne Token | 412 |
| admin `GET /admin/rules` | 405 |

appconfig und Jobliste vorher und nachher gleich; keine Antwort enthält den Marker. Kein
Rechteleck.

### S5 Quelltextproben (token_get_all)

Gefahren: die vier Quelltextproben des Moduls, Skript `PROBE_PHP` auf `php:8.3-cli`.

- **Positivkontrolle** (`test_the_token_probe_finds_real_calls_and_nothing_in_comments_or_strings`):
  synthetische Klasse mit `preg_match(` und `fnmatch(` in Kommentar und String und je einem
  echten Aufruf, einem `eval`, Selbstaufruf und einer Logzeile mit `$path`, `count($patterns)`
  und `$list === []`: genau ein `preg_match`, ein `fnmatch`, ein `eval`, Rekursion erkannt,
  `$path` roh, die beiden anderen als Zähler bzw. Vergleich.
- **Matcher und Normalisierer**
  (`test_the_matcher_and_the_normaliser_use_no_glob_no_regex_no_eval_and_no_recursion`):
  `matchesAPattern` (Zeile 874 bis 905) ruft `count`, `mb_str_split` und `$this->patterns()`;
  `normalisePattern` (751 bis 805) ruft `trim`, `mb_check_encoding`, `mb_ord`, `mb_str_split`,
  `mb_strlen`, `str_contains`, `str_replace`, `str_starts_with` und die Methoden `composed`,
  `trimmed`, `withoutTheFilesFolder`. Kein `fnmatch`, kein `preg_*`, kein `eval`, keine direkte
  oder indirekte Rekursion (Aufrufgraph der 27 Methoden).
- **Ein Regex-Aufruf** (`test_the_service_holds_exactly_one_preg_call_the_allowed_one_in_trimmed`):
  im ganzen ExclusionService genau ein Aufruf mit `preg_`-Namen, `preg_replace('#/+#', ...)`
  in `trimmed()` (Zeile 1264). `normalisePattern` erreicht ihn über `trimmed()`: das ist der
  erlaubte, feste, lineare Aufruf.
- **Logzeilen** (`test_no_log_call_of_the_phase_classes_carries_a_path_a_pattern_or_the_fingerprint`):
  48 Logger-Aufrufe in zwölf Klassen (ExclusionService 7, ExclusionSweepJob 2,
  SubtreeExpandJob 3, StorageCrawlJob 5, FileStateService 1, SettingsController 8,
  FileEventListener 1, QueueService 10, ReconcileController 7, SettingsService 4,
  AdminViewService und PurgeService 0). Keine Variable aus der Sperrliste (`$path`,
  `$pattern(s)`, `$prefix(es)`, `$fingerprint`, `$raw`, `$entry`, `$list`, `$name`, ...) roh
  übergeben; `$prefixes`, `$patterns`, `$list` und die Fehlerlisten nur in `count()` oder als
  Seite eines Vergleichs. Roh übergeben werden Zähler und Kennungen (`$storageId`, `$cursor`,
  `$lastFileId`, `$kind`, ...) und 13 mal `'exception' => $e`. Der erste Lauf meldete
  `$list` in `savePatterns()` (Zeile 649, `'planned' => $list === [] ? 0 : 1`): ein Fehlalarm
  der Probe, seitdem erkennt sie Vergleiche (Positivkontrolle ergänzt).

### S6 Logs

Gefahren: `test_no_log_line_carries_a_corpus_value` nach dem Korpus. Gelesen: neue Zeilen von
`nextcloud.log` seit Laufbeginn (282), neue Zeilen von `.dev/exapp.log` (2) und
`docker logs --since` des Containers (Access-Log, 122). Positivkontrolle mit Marker
`zz3311ctl<zeit>`: PROPFIND mit diesem Login-Namen (Kern schreibt "Login failed") und GET
`http://127.0.0.1:10035/<marker>` (Access-Log von uvicorn); in allen drei Quellen gefunden.
Ergebnis: **keine Zeile mit `q33`** außer den TypeError-Zeilen von H-33-01, die eine eigene
Probe haben (`test_a_wrong_list_shape_leaves_neither_a_500_nor_a_value_in_the_log`, rot).

Zusätzlich gefahren (`fingerprint_probe.py` im Scratch, Instanz danach zurück): Muster
`*.q33fp` über die Seite gespeichert, cron.php. Loglevel 2: keine Zeile mit dem
Fingerabdruck (SHA-256 berechnet wie die Doku es beschreibt) und keine mit dem Muster.
Loglevel 0 für ein Speichern und einen cron-Lauf, danach zurück auf 2: eine Debugzeile des
Kerns ("dirty table reads", Trace mit Argumenten) trägt Muster und Fingerabdruck. Dazu
schreibt der Kern bei einem Fehler eines Hintergrundjobs dessen Argument in die Fehlerzeile
(`lib/public/BackgroundJob/Job.php:47` und `57`, NC 34.0.3), beim Kehrjob also den
Fingerabdruck. Siehe **L-33-03**.

### S7 Gedankenstriche, REUSE, Store-Archiv

- `git diff 12a73359..HEAD | grep "^+" | LC_ALL=C.UTF-8 grep -cP "\x{2013}|\x{2014}"`: **0**;
  Positivkontrolle mit einer Probedatei mit U+2013: 1. Im Audit-Test 0.
- `LC_ALL=C grep -nP "[^\x00-\x7F]" backend/tests/test_phase33_audit.py`: leer.
- `uvx --from "reuse[charset-normalizer]" reuse lint`: 2734 / 2734, konform.
- `bash scripts/release/store-archive.sh stage-companion <scratch>/stage`: Exit 0;
  `lib/BackgroundJobs/ExclusionSweepJob.php`, `lib/Service/ExclusionService.php`,
  `js/admin.js`, `templates/admin.php` im Archiv und byte-gleich mit dem Repo (`cmp`). Das
  lokale Staging nimmt wieder die ignorierten Markerdateien `.claude-active` mit (bekannt aus
  32-AUDIT, CI baut aus frischem Checkout).

## Befunde

### H-33-01 (HIGH): Eine Liste als String oder Zahl endet in HTTP 500 mit allen Regelwerten im Log

- **Ort:** `php/lib/Controller/SettingsController.php:349` bis `355` (`saveRules(array
  $exclusions = [], ..., array $exclusionPatterns = [])`); der Kern ruft die Methode in
  `lib/private/AppFramework/Http/Dispatcher.php:165` mit dem rohen Wert auf.
- **Beleg (gefahren):** `POST /admin/rules` mit `"exclusionPatterns": "*.q33jd"`, mit `7`, mit
  `""` und mit `"exclusions": "q33xb"`: je HTTP 500 (HTML-Fehlerseite) und eine Zeile Level 3
  "saveRules(): Argument #5 ($exclusionPatterns) must be of type array, string given". Der
  Trace dieser Zeile trägt die Argumente: `"args": [["Archiv"], 52428800, true, false,
  "*.q33jd"]`, also die Ordnerliste und den Musterwert im Klartext. Die Vorschau antwortet
  auf dieselben Formen mit 400 ohne Body und ohne Logzeile.
- **Einordnung:** nur ein Admin mit gültigem Token erreicht den Weg, und die Seite sendet nie
  einen String. Nach der Schweregradtabelle des Plans (5xx, Wert im Log) HIGH. Für
  `exclusions` besteht die Form seit 1.4.2 (`git show v1.4.2:php/lib/Controller/SettingsController.php`,
  Zeile 312 bis 317), Phase 33 hat `exclusionPatterns` in derselben Form dazugelegt.
- **Fixvorschlag:** beide Listen untypisiert (`mixed`) annehmen und eine Nicht-Liste wie
  einen ungültigen Eintrag mit einem Code ablehnen (400, Code statt Wert), in Vorschau und
  Speichern gleich; Regressionstest: die zwei xfail-Fälle dieses Befunds und
  `test_a_wrong_list_shape_leaves_neither_a_500_nor_a_value_in_the_log`.

### H-33-02 (HIGH): Ein Musterschlüssel anderen Typs hält den Listener an und bricht Seite und Übersicht

- **Ort:** `php/lib/Service/ExclusionService.php:509` (`patterns()` ruft
  `IAppConfig::getValueArray()` ohne Schutz vor `AppConfigTypeConflictException`); Folgen in
  `FileEventListener::handle()` (fängt und loggt "an event could not be turned into queued
  work"), `SettingsController::overview()`, der Seite und `occ findling:diagnose`.
- **Beleg (gefahren):** `occ config:app:delete findling exclusion_patterns` und
  `occ config:app:set findling exclusion_patterns --value=42 --type=integer` (occ nimmt das
  an; `config:app:get --details` zeigt `type: integer`). Danach: Übersicht HTTP 500 "Status
  is not available.", Seite `/settings/admin/findling` HTTP 500, `occ findling:diagnose`
  Exit 1 "conflict with value type from database". MKCOL 201, PUT 201 und 204 von
  `Audit3311int/a.txt` (Datei 3128): **keine Queue-Zeile**, im Log je Ereignis die Warnung
  "conflict with value type from database" und "Findling: an event could not be turned into
  queued work". Jede Schreibaktion der Instanz wird so still nicht mehr indexiert, solange
  der Schlüssel steht. Ein String ohne Typ (`mixed`) liest sich dagegen als leere Liste.
- **Einordnung:** Die Doku verspricht für Listen, die per occ gesetzt werden, "gilt
  dieselbe Prüfung beim Lesen". 5xx und stiller Indexierungsausfall: HIGH nach der Tabelle
  des Plans. Dieselbe Aufrufform steht für `exclusions` seit 1.4.2 in `prefixes()` (Zeile
  240), nicht gefahren.
- **Fixvorschlag:** in `patterns()` (und `prefixes()`) den Typkonflikt fangen, als
  unbrauchbare Liste zählen (Warnung mit Zählern) und `[]` liefern; Regressionstest: der
  xfail-Fall `integer` und ein PHPUnit-Fall mit werfendem `getValueArray`.

### L-33-01 (LOW): Der Treiber von 33-02 läuft ohne Normalizer, die NFC-Hälfte sieht er nicht

- **Ort:** `backend/tests/test_exclusion_driver.py` und dieser Audit-Test (Image
  `php:8.3-cli`); `ExclusionService::composed()` Zeile 1295 bis 1303 (dokumentierter Rückfall
  auf den Rohwert ohne `\Normalizer`).
- **Beleg (gefahren):** `docker run --rm php:8.3-cli php -r 'echo class_exists("Normalizer")?"yes":"no";'`
  ergibt `no`, im Image der Instanz `yes`. Orakel auf `php:8.3-cli`: 5 Abweichungen und eine
  abweichende Liste in Kraft, alle NFD; auf `nextcloud:34.0.3-apache` 0. Auf der Instanz
  komponiert der Dienst (S1).
- **Einordnung:** kein Fehler des Produkts; die Differenz- und Laufzeitproben von 33-02
  prüfen die Komposition nur nicht. Der Treiber bleibt unverändert.
- **Fixvorschlag:** die NFC-Fälle über das Image der Instanz fahren (Variable wie hier) oder
  den Treiber in einem Image mit intl laufen lassen.

### L-33-02 (LOW): Bidi- und Formatzeichen gelten als Literal

- **Ort:** `ExclusionService::normalisePattern()` (Zeile 751 bis 805), Prüfung auf
  Steuerzeichen.
- **Beleg (gefahren):** `*q33ia<U+202E>.key`, `<U+202E>*q33ib`, `*q33ic<U+2066>x`: Vorschau 200,
  das Muster kommt so zurück (`newPatterns`). C0, DEL und C1 (U+0085) werden abgelehnt.
- **Einordnung:** Die Doku nennt "ein Steuerzeichen, etwa ein Zeilenumbruch"; U+202E und
  U+2066 sind Formatzeichen (Cf). Ein solches Muster ordnet auf der Seite die sichtbare
  Zeichenfolge um (Bestätigung, Liste), also kann ein Admin ein Muster sehen, das anders
  trifft, als es aussieht. Nur Admins schreiben Muster.
- **Fixvorschlag:** Bidi-Steuerzeichen (U+200E, U+200F, U+202A bis U+202E, U+2066 bis U+2069,
  U+061C) als `control_character` ablehnen, Satz und Code bleiben.

### L-33-03 (LOW): Auf Loglevel 0 und bei einem Jobfehler schreibt der Kern Muster bzw. Fingerabdruck

- **Ort:** Kern: Debug-Trace "dirty table reads" mit Argumenten; `lib/public/BackgroundJob/Job.php:47`
  und `57` (Job-Argument in "Starting job" auf Level 0 und in "Error while running
  background job" auf Level 3). Das Argument von ExclusionSweepJob trägt den Fingerabdruck
  (`ExclusionSweepJob::argument()`, Zeile 124 bis 131).
- **Beleg (gefahren):** S6. Auf Level 2 im Normalbetrieb keine Zeile; auf Level 0 eine Zeile
  mit Muster und Fingerabdruck. Der Fehlerweg ist aus Job.php hergeleitet (im Lauf von S3
  gesehen bei SubtreeExpandJob: "Error while running background job ... arguments:
  {...}").
- **Einordnung:** Findling schreibt beides nie selbst (S5); `docs/admin-page.md` Abschnitt
  "Was im Protokoll steht" sagt aber ohne Einschränkung "Nie ein Muster, ein Pfad oder ein
  Fingerabdruck". Wie L-32-02 eine Zeile des Kerns.
- **Fixvorschlag:** den Abschnitt (und `docs/privacy.md`) um die zwei Kernfälle ergänzen.

### L-33-04 (LOW): Ein Nicht-String in der Liste heißt "leer"

- **Ort:** `ExclusionService::validatePatterns()` (Code für einen Eintrag, der kein String
  ist).
- **Beleg (gefahren):** S2, Zeile "Form im Eintrag": Array, Objekt, Zahl, `null`, `true`
  ergeben `empty`; die Seite zeigt dazu "Der Eintrag ist leer ...".
- **Einordnung:** nur über eine gebaute Anfrage erreichbar, nie über das Formular; kein Wert
  in Antwort oder Log.
- **Fixvorschlag:** accept oder Doku-Zeile beim Code `empty` ("oder kein Text").

## Nebenbefunde ohne Befund-ID

- **occ-Verzögerung:** Ein per occ gesetzter Wert erreicht den Webprozess erst nach 2 bis 4
  Sekunden (lokaler Zwischenspeicher der AppConfig des Kerns; die CLI sieht ihn sofort).
  Für Weg C ohne Bedeutung; die Proben warten darauf (Kanarie).
- **SubtreeExpandJob nach geleertem Papierkorb:** Wird ein Ordner gelöscht und der
  Papierkorb vor dem nächsten cron geleert, endet der Löschjob mit
  `OCP\DB\Exception: Could not fetch storage root` (`SubtreeExpandJob.php:159`, Zeile aus
  e3de49a2 vom 01.09.2026, außerhalb des Phasen-Diffs). In `deferred-items.md` eingetragen.

## Was gegengeprüft wurde, nicht nur gelesen

| Prüfung | Verfahren (anders als die Umsetzung) | Ergebnis |
|---|---|---|
| Matcher | Orakel aus der Doku (Rekursion mit Memo) gegen den echten Dienst, 2593 Paare, zwei Laufzeiten | 0 Abweichungen auf der Laufzeit der Instanz; L-33-01 |
| Normalisierung und Liste in Kraft | Orakel der Doku für Kürzung, NFC, Doppel, Grenze 32 gegen `patterns()` | gleich auf der Laufzeit der Instanz |
| Ablehnungen | 65 Werte gegen beide Routen der Instanz, Erwartung vorher notiert | H-33-01, L-33-02, L-33-04 |
| Zweiter Schreiber | occ mit fünf Müllformen, Kanarie gegen den Zwischenspeicher, echter Zähl-Crawl | H-33-02 |
| Rechte | Nicht-Admin, anonym, ohne Token, falsches Verb | 403 / 401 / 412 / 405, nichts geschrieben |
| Quelltext | `token_get_all` statt regulärer Ausdrücke, mit Positivkontrolle | kein Glob, kein Regex außer `trimmed()`, keine Rekursion, Logs nur Zähler |
| Logs | drei Quellen mit Positivkontrolle; Loglevel 0 gefahren | Normalbetrieb sauber; L-33-03 |
