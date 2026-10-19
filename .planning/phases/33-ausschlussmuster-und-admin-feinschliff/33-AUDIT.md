---
phase: 33-ausschlussmuster-und-admin-feinschliff
audited: 2026-10-18
diff: 12a73359..92441a16
files_reviewed: 61
findings:
  critical: 0
  high: 2
  medium: 0
  low: 6
  total: 8
status: issues_found
---

# Phase 33: Security-, Bug- und Performance-Audit

**Stand:** Task 1 (Sicherheit) und Task 2 (Fehler) abgeschlossen am 18.10.2026, Task 3
(Performance) am 19.10.2026. Task 4 (Fixes, LOW-Entscheidungen, Abschluss) folgt; `fix_run`,
`fix_commits`, `fixed` und `still_open` trägt erst Task 4 ein. Rote Proben stehen bis Task 4
als `xfail(strict=True)` mit der Befund-ID im Test.

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

## Bugs

Gefahren als ein Szenario auf 8090 (Fixture `bug_run`, Rohdaten `bugs.json`), dreimal:
18.10.2026 23:44 bis 23:53 Ortszeit, 19.10. ab 00:01 (volle Datei) und nach der Korrektur der
B2-Prüfung erneut; Werte unten aus dem ersten Lauf, Abweichungen der späteren Läufe genannt.
Dazu drei Einzelproben:

```
FINDLING_AUDIT33_STATE_DB=<repo>/.dev/storage/state.db uv run python -m pytest -q tests/test_phase33_audit.py -rxXs -p no:randomly -k "test_b1 or test_b2 or test_b3 or test_b4 or test_b5 or scenario"
```

**Saat** (testuser, WebDAV, je ein Wort ohne deutsche Wortbestandteile): R
`Audit3311bug/Ordner/r1.txt` (Datei 3197, `zyrnoka`), K `Audit3311bug/Keep/k1.txt` (3199,
Kontrolle), S1 `Audit3311bug/Sweep/a.pat1/s1.txt` (3202), S2 `.../b.pat2/s2.txt` (3204), S3
`.../c.pat6/s3.txt` (3206), D `Audit3311bug/Both/x.pat3/d1.txt` (3209), später V
`Archiv/v3311.txt` (3210). Positivkontrolle: alle sechs Wörter je 1 Treffer vor dem ersten
Schritt. Regeln über die echte Speicherroute (`POST /admin/rules` mit Token, die drei übrigen
Felder wie die Übersicht sie meldet).

| Nr. | Fall (Plan) | Verfahren | Ergebnis | Urteil |
|---|---|---|---|---|
| B1 | Ordner innerhalb eines Mounts unter ein Muster umbenannt | `*.bndl` gespeichert (Kehrjob, 2 cron-Läufe, nichts getroffen), dann `MOVE Audit3311bug/Ordner` nach `Ordner.bndl` (201). Abgleich fällig gemacht wie in 32-AUDIT: `finished_at` und `started_at` der Tabelle `reconcile` in `state.db` um 49 Stunden zurück (5 Zeilen), der laufende Prozess nahm ihn beim nächsten Takt auf | nach dem MOVE keine Queue-Zeile für R, kein Kehrjob, kein SubtreeExpandJob, kein Crawl-Job; nach einem Poll des Backends (150 s) R weiter 1 Treffer. Abgleich: `reconcile round walked, mounts=3 slices=3 seen=484 stale=2 missing=1 given_up=0` (zweiter Lauf `missing=0`), danach R 0, K 1 | in Ordnung (Weg C) |
| B1b | Muster zurückgenommen, Dateien kommen zurück | S1 war unter `*.pat1` geräumt (B2), `*.pat1` in B3 zurückgenommen | vor dem Abgleich S1 0, nach dem Abgleich 1 (`missing=1`) | in Ordnung, wie "Ein Muster entfernen" |
| B2 | Muster entfernen, während ein Kehrjob läuft | `*.pat1, *.pat2` gespeichert: genau ein Job (storage 0, cursor 0, Fingerabdruck `5ecc6c24...`). Dann `*.pat1`: genau ein Job (0, 0, `1a1b7a89...`), der alte ist weg, der neue läuft von vorn. Danach als Band im Flug der Nachfolger des alten Satzes über `IJobList::add` des Kerns eingehängt (storage 3, root 82, cursor 3196, `5ecc6c24...`), wie ihn ein laufendes Band nach dem Speichern anlegt; cron.php | nach ein bis zwei cron-Läufen keine Kehrjobs mehr (cron.php erreicht das eingehängte Band nicht immer im ersten Lauf); nie ein Nachfolger des alten Satzes, also kein Job mit `5ecc6c24...` und anderer ID; Queue: Löschzeile für S1, **keine für S2** (nur unter dem entfernten Muster), keine für S3 und K. Treffer S1 0, S2 1, S3 1, K 1 | in Ordnung |
| B2b | leerer Satz (N3) | `[]` gespeichert | HTTP 200, kein Kehrjob in der Jobliste | in Ordnung |
| B3 | zwei schnelle Speichervorgänge | `*.pat2` und direkt danach `*.pat6`, ohne cron dazwischen | genau ein Job mit dem Fingerabdruck von `*.pat6`; gespeichert `["*.pat6"]`; nach cron S3 0, S2 1 | in Ordnung |
| B3b | zwei Speichervorgänge im selben Moment | `test_b3_two_saves_at_the_same_moment_leave_one_sweep_for_the_stored_set`: zwei Sitzungen, `threading.Barrier`, 30 Runden (davor ein Lauf mit 6) mit `["*.race2","*.roundN"]` gegen `["*.race6","*.roundN"]` | alle 72 Antworten 200; in jeder Runde genau ein Job mit dem Fingerabdruck des gespeicherten Satzes; in 4 von 30 (2 von 6) Runden steht daneben ein Job des unterlegenen Satzes, der an seiner ersten Prüfung ohne Räumen endet (B2) | in Ordnung; Restrisiko **L-33-05** |
| B4 | Muster und Präfix decken dieselbe Datei | Urteil `skipped(no_text_layer)` für D gesetzt, dann Präfix `Audit3311bug/Both` und Muster `*.pat3` in einem Speichern | ein Kehrjob und ein SubtreeExpandJob geplant; nach dem ersten cron-Lauf **genau eine** Queue-Zeile für D (`delete`), Urteilszeile weg; Rest in 7 weiteren Läufen ohne zweite Zeile; keine Logzeile Level 3; D 0, K 1 | in Ordnung |
| B5 | Urteil einer Datei unter Regel, die der Container nie kannte | V unter dem Präfix `Archiv` angelegt: keine Queue-Zeile (Listener lässt sie aus, der Container kennt sie nie); Urteil `skipped(no_text_layer)` gesetzt; derselbe Abgleich wie B1 | nach dem Abgleich Urteilszeile weg (Slice von 33-04 Task 3, `ReconcileController::forgetExcludedVerdicts`), keine Queue-Zeile, V 0 Treffer | in Ordnung |
| B6 | Gruppenordner (#22-Form) | `occ app:list`: groupfolders nicht installiert | Verweis auf PHPUnit `ExclusionSweepJobTest::testExactlyTheTwoFilesUnderThePatternAreClearedAndForgotten` (Mount `__groupfolders/1`, Datei `__groupfolders/1/AG/2024/X.key/b.txt`, Löschzeile für die Bundle-Datei des Homes und des Team Folders), grün in CI php.yml 39162854657 auf 92441a16; der Pfadraum der Team Folders ist in 1.4.2 unverändert (Differenztest 33-02) | in Ordnung (Testprobe) |
| B7 | Status eines 1.4.x-Containers ohne die zwei neuen Felder | Proxy auf Port 10036 vor dem Backend (`strip_proxy.py` im Scratch), der aus `GET /status` die Felder `maxCells` und `extractAddressSpaceBytes` entfernt; Port in `oc_ex_apps` umgestellt und zurück. Seite per Playwright 1.59 (Chromium headless) als admin, Grenzblock vor und nach dem ersten Poll | Positivkontrolle ohne Proxy: Datei, Speicher, Zellen, Seiten (Profil) sichtbar. Mit Proxy (5 Statusantworten umgeschrieben, je 2 Felder entfernt): Übersicht `address_space` und `cells` mit `value: null, shown: false`; Zeilen Speicher und Zellen verborgen, Datei und Seiten sichtbar, vor und nach dem Poll gleich; 0 Konsolenfehler, 0 `pageerror`. Danach Port 10035, Statusroute direkt 200, Proxy beendet | in Ordnung |
| B8 | Link des Grenzblocks | `test_b8_the_limit_block_links_exactly_the_tag_url_of_pe8_and_the_anchor_exists` und mit `FINDLING_AUDIT33_NETWORK=1` `test_b8_the_anchor_answers_on_blob_main` | Template nennt genau `https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/admin-page.md#limits-per-file` einmal, `limits-per-file` einmal; `docs/admin-page.md` trägt `<a id="limits-per-file"></a>` genau einmal, direkt vor "## Grenzen je Datei ändern"; `blob/main/docs/admin-page.md` HTTP 200 mit dem Anker. Der Tag-Link selbst antwortet erst mit v1.5.0 | in Ordnung |

**Aufräumen** (im `finally` des Szenarios, Ergebnis in `bugs.json`): Regeln über die Route auf
`exclusions` `["Archiv"]` und Muster `[]`, dann `occ config:app:delete findling
exclusion_patterns`; WebDAV `DELETE /Audit3311bug` und `/Archiv/v3311.txt`; cron.php bis kein
SubtreeExpandJob und kein Kehrjob mehr da ist, danach `occ trashbin:cleanup testuser`;
gesetzte Urteilszeilen gelöscht. Endzustand: `exclusions` `["Archiv"]`,
`exclusion_patterns` fehlt (Exit 1), Jobliste nur ScanRecountJob
(`test_the_scenario_left_the_instance_as_it_found_it`).

**Nebenbefund ohne ID:** Im ersten Wettlauf (Threads, die vor dem Speichern die Übersicht
lasen) endete eine `GET /admin/overview` mit HTTP 500, `SQLSTATE[HY000]: General error: 5
database is locked`. Die Dev-Instanz läuft auf SQLite, das Nextcloud nur für Tests vorsieht;
die Probe B3b liest die Felder deshalb einmal vorher und schickt nur die zwei POST
gleichzeitig.

## Performance

Gemessen am 19.10.2026 zwischen 00:22 und 03:40 Ortszeit auf dem Entwicklungsrechner:
Windows 11 Pro 10.0.26200, Intel Core i5-1335U, 16 GB RAM (15,7 GB sichtbar), Docker
Desktop; Instanz `findling-nextcloud` (Nextcloud 34.0.3, PHP 8.5.9, SQLite, `php/` als
Bind-Mount), Backend 1.4.2 als Host-Prozess (Port 10035, Semantik aus,
`engineState: missing`). Freier RAM vor der ersten Messung 2,71 GB, vor P3 2,27 GB (neben
der Dev-Instanz liefen die drei Container der HaRP-Umgebung). Skripte und Rohdaten im
Scratch (`perf/p1_series.py` bis `perf/p5_page.js`, je eine JSON-Datei), nicht im Repo.

Jedes Verfahren weicht vom Prototyp in 33-RESEARCH ("Messung am Prototyp", 13.10.2026)
ab: der Prototyp maß ein Skript auf `php:8.3-cli` mit eigener Mustermenge; hier messen P1
den echten `ExclusionService` über den unveränderten Treiber, P2 bis P5 die echte Instanz
mit dem echten Listener, Kehrjob, Abgleich und der echten Seite.

| Nr. | Messgröße | Wert | Vergleich | Urteil |
|---|---|---|---|---|
| P1 | Matcher, gutartig, Median je Aufruf 250 / 1000 / 4000 Zeichen | 0,356 / 1,414 / 5,808 ms (Max 0,478 / 1,874 / 11,413) | 33-02: 0,454 / 1,506 / 6,025 ms (-22 / -6 / -4 %) | in Ordnung |
| P1 | Matcher, feindlich, Median 250 / 1000 / 4000 | 0,337 / 1,368 / 5,469 ms (Max 0,483 / 1,729 / 9,058) | 33-02: 0,476 / 1,547 / 6,096 ms (**-29** / -12 / -10 %) | in Ordnung, Begründung unten |
| P1 | t(4000)/t(1000) | gutartig 4,11, feindlich 4,00 | Band 2,5 bis 6; 33-02: 4,00 / 3,94 | in Ordnung |
| P1 | feindlicher Median bei 4000 | 5,47 ms | Decke 12,6 ms; Prototyp 8,4 ms | in Ordnung |
| P2 | Upload je Datei aus Client-Sicht, 0 / 4 / 32 Muster (je 100, verschränkt) | Median 169,2 / 170,6 / 169,5 ms; Max 270,9 / 385,5 / 475,6 ms | 0 gegen 32: **+0,2 %** im Median | in Ordnung |
| P2 | dieselben Uploads im Access-Log (Sekundenauflösung) | Summe der Blockspannen 15 / 17 / 18 s je 100 | grob 150 bis 180 ms je Upload | in Ordnung (Plausibilität) |
| P2 | `isExcluded()` im Prozess der Instanz, 68 Zeichen, 0 / 4 / 32 Muster | Median 0,27 / 14,8 / 103,8 µs (Max 17,5 / 2 336 / 7 182 µs) | Prototyp 75 Zeichen: 22 / 180 µs (-33 / -42 %) | in Ordnung |
| P3 | Kehrjob über 10 000 Dateien (2 500 im Bundle), Instanz gesamt 11 390 Dateien | 12 Bänder in 12 cron-Läufen; Lauf Median 0,48 s, Max 9,59 s (erster Lauf mit den übrigen fälligen Jobs) | Wanduhr 30 s je Lauf | in Ordnung |
| P3 | Löschzeilen gegen Treffer | 2 502 Dateien mit Löschzeile = 2 500 im Bundle + 2 unter dem Präfix `Archiv`; 0 außerhalb | 2 500 Bundle-Dateien | in Ordnung |
| P3 | Fehlerliste | 10 gesetzte Fehlerurteile im Bundle weg, 5 außerhalb geblieben; Übersicht `failed` 33 vor, 23 nach | , | in Ordnung |
| P4 | Abgleich Weg C, 5 000 bekannte Dateien unter einem per occ gesetzten Muster | 11 Takte am Ruhe-Tor, je Takt eine Scheibe übergeben (377, 9 x 500, 123), 3 260 s vom Rücksetzen bis zur letzten Übergabe, Takt 302,9 s | Takt 300 s, Scheibe 500, Ruhe-Marke 100 (`config.py`) | in Ordnung, Restbefund L-33-06 |
| P4 | Ergebnis Runde 1 | 5 000 von 5 000 im Container mit Grabstein, 5 000 von 5 000 Urteilszeilen `no_text_layer` weg, Warteschlange 0 | , | in Ordnung |
| P4 | Runde 2 | `walked, mounts=3 slices=15 seen=6227 stale=0 missing=0`, 0 neue Warteschlangenzeilen (Trigger) | keine Wiedereinreihung verlangt | in Ordnung |
| P4 | Scheibe mit 500 ausgeschlossenen Zeilen im Prozess | Seite lesen 7,0 bis 8,6 ms; Urteile anhängen und bereinigen mit 500 zu löschenden Urteilen Median 5,6 ms, ohne 0,41 ms (je 3 Läufe) | , | in Ordnung |
| P5 | Admin-Seite, 0 / 32 Muster (je 30 Ladevorgänge, verschränkt) | `load` Median 413,6 / 420,7 ms (Max 548,7 / 498,8), DOMContentLoaded 334,5 / 346,9 ms, erstes Byte 92,8 / 96,4 ms | 32 gegen 0: +1,7 % (`load`) | in Ordnung |
| P5 | Größe | HTML 107 608 / 123 445 Byte (die 32 Musterzeilen der Liste); Übersicht 14 135 / 14 569 Byte (die Musterliste) | , | in Ordnung |
| P5 | Statusantwort des Containers | 37 Felder, 984 Byte; ohne `maxCells` und `extractAddressSpaceBytes` 929 Byte (55 Byte); `git diff v1.4.2 HEAD -- backend/src/findling/api/status.py` fügt genau diese zwei Felder hinzu | 1.4.2: dieselben 35 Felder | in Ordnung |

**P1, Verfahren:** `perf/p1_series.py` ruft aus `backend/` die Helfer von
`tests/test_exclusion_driver.py` (Mustersätze, Pfade, `run_driver`) und liest Median und
Maximum der Treiberantwort; dazu die Verify-Probe des Plans
`FINDLING_TIMING=1 uv run python -m pytest -q tests/test_exclusion_driver.py -rs` am Ende
von Task 3: 5 passed, Mediane gutartig 0,357 / 1,431 / 5,914 ms, feindlich 0,350 / 1,316 /
5,316 ms bei 250 / 1000 / 4000 Zeichen, Quotienten 4,13 und 4,04. Je Länge 3 Pfade, 50 Wiederholungen, also 150 Aufrufe je Zelle;
`php:8.3-cli`. **Abweichung über 25 Prozent:** nur feindlich bei 250 Zeichen (0,337 gegen
0,476 ms), also schneller. Bei kurzen Pfaden trägt der feste Anteil je Aufruf
(`hrtime`, Methodenaufruf, `mb_str_split`) den größten Teil, und der schwankt mit dem
Zustand der Maschine; bei 4000 Zeichen liegen beide Sätze innerhalb von 10 Prozent von
33-02, und die Quotienten sind gleich. Kein Befund.

**P2, Verfahren:** testuser, WebDAV-PUT kleiner Textdateien unter
`Perf3311i/Projekte/Kunde<k>/2024/Unterlagen/Besprechungsnotiz-<n>.txt` (68 bis 70
Zeichen, kein Muster trifft, jede Datei wird also eingereiht). Muster per
`occ config:app:set --type=array` (erste vier bzw. alle 32 gutartigen Muster aus P1),
abgewartet, bis die Übersicht sie zeigt, dann 4 s für den Zwischenspeicher. Verschränkt:
10 Runden, jede Runde jeder Satz mit 10 Uploads in rotierender Reihenfolge, ein
verworfener Aufwärm-Upload je Block. **Erster Versuch verworfen:** vier Blöcke zu je 100
in der Reihenfolge 0, 4, 32, 0 ergaben Median 175,5 / 180,6 / 288,8 / 225,3 ms; der zweite
0-Block war 28 Prozent langsamer als der erste, die Reihe maß also die Drift (Backend
indexierte die Uploads gleichzeitig), nicht die Muster. **Mittelwert:** 173,8 / 186,4 /
199,2 ms; die Differenz kommt aus je einem bis zwei langsamen 10er-Blöcken (Blockmedian
275, 305 und 325 ms), die in den Sätzen 4 und 32 lagen. Die Kosten des Musters selbst
zeigt die Messung im Prozess: `perf/p2c.php` per `docker exec` auf der Instanz, echter
Dienst über `\OCP\Server::get`, echter appconfig-Wert, 7 Pfade je 1000 mal, drei Läufe je
Satz; 32 Muster kosten 0,104 ms, das sind 0,06 Prozent eines Uploads. Schneller als der
Prototyp, weil `mb_str_split` des Pfads einmal je Datei läuft und nicht je Muster
(Empfehlung aus 33-RESEARCH, umgesetzt) und PHP 8.5 statt 8.3 rechnet. Die Zeit je Upload
aus dem Nextcloud-Log gibt es auf Loglevel 2 nicht (keine Zeile je Anfrage), Loglevel 0
schreibt Muster in Kernzeilen (L-33-03); deshalb das Access-Log des Containers.

**P3, Verfahren:** RAM unter 4 GB frei, also halbierter Korpus: 10 000 statt 20 000
Dateien, davon 2 500 statt 5 000 unter einem Bundle, Verhältnis wie im Plan. Angelegt
direkt im Datenverzeichnis des Containers (7 500 unter
`Perf3311k/Abteilung<a>/Jahr<y>/Projekt<p>/Unterlagen/Teil<t>/`, 2 500 unter
`Perf3311k/Medien/Fotos.plib3311/Masters/<y>/<m>/<d>/`, 1,2 s) und mit
`occ files:scan --path=testuser/files/Perf3311k` eingelesen (10,1 s). Der Scan löst kein
Ereignis des Listeners aus (Warteschlange danach 0), der Kehrjob hat also den ganzen
Bestand vor sich. Muster `*.plib3311` über die echte Speicherroute (HTTP 200 in 96,8 ms,
genau ein ExclusionSweepJob), dann cron.php mit 5,5 s Pause (Intervall des Jobs 5 s), bis
kein Kehrjob mehr da war. Gezählt wurden die Löschzeilen über einen Trigger auf
`oc_findling_queue` (eigenes Werkzeug neben dem Zähler des Jobs, der auf Level 0 loggt;
danach entfernt). Die zwei Dateien außerhalb des Bundles sind `Archiv/alte-notiz.md` und
`Archiv/ereignis-probe.md` unter dem Präfix in Kraft; der Kehrjob räumt Präfix-Dateien
unterwegs erneut, so steht es im Kopf von `ExclusionSweepJob.php`. Bänder: 1 000 Dateien
je Lauf (`BATCH_SIZE`), Laufzeit 0,41 bis 0,73 s außer dem ersten Lauf. Keine Zahl aus
33-RESEARCH zum Vergleich (dort nur die Kosten je Vergleich); Durchsatz rund 2 000
Dateien je Sekunde Laufzeit.

**Abbau P3:** WebDAV `DELETE /Perf3311k` (204). Mein erster Aufräumlauf rief cron ohne
Pause und leerte den Papierkorb, bevor der SubtreeExpandJob fertig war; der Job endete mit
"Error while running background job" (Argument nur Zahlen), also der bekannte
Nebenbefund aus `deferred-items.md` (Löschjob nach geleertem Papierkorb), hier erneut
gesehen. Die Dateien kannte der Container nie, es blieb nichts im Index. Dazu schrieb der
Kern beim Leeren des Papierkorbs 77 Zeilen "More than 1000 expressions in a list are not
allowed on Oracle." (`FilesMetadata\Service\MetadataRequestService.php:160`, Kern, schon
am 12.10. im Log). filecache danach 0 Zeilen unter `Perf3311k`, 5 gesetzte Urteile mit
den Dateien weg.

**P4, Verfahren:** 5 000 Dateien unter
`Perf3311r/Medien/Archiv.wegc3311/Band<x>/Teil<y>/Mappe<z>/` im Datenverzeichnis angelegt
und gescannt (5 000 wie im Plan; der Korpus ist klein auf der Platte und der Container
indexiert ohne Semantik, die RAM-Grenze betrifft P3). Bekannt gemacht über
`QueueService::enqueueFile` im Container, also dieselbe Zeile, die Crawl oder Listener
schreiben (der Zähl-Crawl von S3 reiht nicht ein, er zählt; ein erster Versuch, sie über
den Abgleich selbst als fehlend einzureihen, lief mit 500 je Takt und wurde abgebrochen):
670,7 s bis alle 5 000 im Container lebten. Dann je Datei ein Urteil
`skipped(no_text_layer)` in `oc_findling_file_state`, Muster `*.wegc3311` per
`occ config:app:set --type=array` (Weg C allein: occ plant keinen Kehrjob, geprüft: 0
ExclusionSweepJob), Übersicht zeigt das Muster. Fällig gemacht wie in B1, hier für alle
Zeilen der Tabelle `reconcile` in `state.db` (Lesezeichen 0, Stempel 49 Stunden zurück).
Zeitpunkte aus dem Backend-Log, das ein Thread des Skripts mitlas (Ankunftszeit je
Zeile, Auflösung 0,05 s). Der erste Takt kam 233 s nach dem Rücksetzen. **Ruhe-Tor:** jede
Runde übergab genau eine Scheibe (die Scheibe vor dem Tor wird ganz übergeben), meldete
"reconcile stands down, 500 rows are scheduled and the quiet mark is 100" und endete
`queue_busy`; der Poller arbeitete die 500 Löschaufträge zwischen zwei Takten ab, die
nächste Runde setzte am Lesezeichen fort. Weg C räumt bei Standardwerten also 500 Dateien
je 5 Minuten, 5 000 in 50 Minuten. Das passt zu `docs/reconcile.md` ("in Bändern zu
höchstens 200 Aufträgen eingereiht, und das Ruhe-Gate vor der nächsten Seite beendet die
Runde"): eine Seite von 500 ging in drei Bändern hinüber, dann hielt das Tor. Weg C ist
das Netz unter Weg A, nicht der Hauptweg. **Kosten der Urteilsbereinigung:**
`perf/p4_slice.php` ruft auf der Instanz `StorageService::getFileSlice` mit dem Prädikat des
Controllers und dessen `withVerdicts` (per Reflection, die Route selbst prüft den
AppAPI-Aufrufer) über dieselben 500 Zeilen, abwechselnd mit 500 frisch gesetzten Urteilen
und ohne: die Bereinigung kostet rund 5 ms je Scheibe, also rund 10 µs je Urteil, neben
7 ms für das Lesen der Seite. Runde 2: Lesezeichen und Stempel erneut zurück, Trigger auf
`oc_findling_queue`; erster Takt nach 271,5 s, eine Runde über alle drei Mounts, nichts
eingereiht. **Fälligkeit nach der Regel aus 33-09** (`_is_due`: kein offener Lauf, dann
Pause und Stunde, sonst die doppelte Pause; geprüft je Takt von 300 s): hier über die
doppelte Pause (Stempel 49 Stunden zurück), der Start kam je mit dem nächsten Takt
(233 s bzw. 271,5 s nach dem Rücksetzen), wie die Regel es verlangt.

Beobachtung am Ende von Runde 1 (Befund **L-33-06**): die letzte Scheibe gehörte zum
Ende von Mount 3 (testuser), danach stand das Ruhe-Tor vor Mount 4 (kollegin). Alle drei
Lesezeichen standen dann auf 0 mit Stempel, `MAX(finished_at)` war frisch, und der
Abgleich galt als fertig: in den zwei folgenden Takten kam keine Runde mehr, obwohl Mount 4
in diesem Zyklus nicht gelaufen war. Erst die rückgesetzte Runde 2 lief über alle drei.

**P5, Verfahren:** `perf/p5_page.js`, Playwright (Chromium headless, aus der Installation
in `amt-einfach`), eine angemeldete Sitzung als admin, Seite `/settings/admin/findling`;
Muster per occ (0 = Schlüssel gelöscht, 32 = die gutartigen aus P1), abgewartet, bis die
Übersicht den Satz zeigt. 6 Runden, je Runde beide Sätze in wechselnder Reihenfolge mit je
5 Ladevorgängen, also 30 je Satz. Gelesen aus `performance.getEntriesByType('navigation')`
(`responseStart`, `responseEnd`, `domContentLoadedEventEnd`, `loadEventEnd`, je minus
`startTime`, `decodedBodySize`) und dem `PerformanceResourceTiming` der ersten Abfrage der
Übersicht. Die erste Abfrage kommt 30,3 s nach dem Laden (Median), also mit dem ersten
Takt der Seite und nicht beim Laden; die Seite selbst kommt fertig aus dem Template. Der
Unterschied von 15,8 KB im HTML ist die Liste der 32 Muster samt Bedienelementen, die
Ladezeit wächst um 7 ms. Kein Browser lief parallel zu einem Testlauf.

**Abbau P2 und P4:** WebDAV `DELETE` von `Perf3311r`, `Perf3311w` und `Perf3311i` (je 204),
cron mit 6 s Pause bis kein SubtreeExpandJob mehr da war (5 Läufe), erst dann
`occ trashbin:cleanup testuser`; Regeln über die Route auf `["Archiv"]` und `[]`, danach
`occ config:app:delete findling exclusion_patterns`. Ergebnis: filecache unter den drei
Ordnern 0 Zeilen, Warteschlange 0, im Container 0 lebende Zeilen unter `Perf3311` (5 750
mit Grabstein, wie jeder gelöschte Bestand), `exclusions` `["Archiv"]`,
`exclusion_patterns` fehlt (Exit 1), Jobliste nur ScanRecountJob, keine verwaisten Urteile
außer den 20, die vor dem Audit schon da waren (13.10. und 18.10.).

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

### L-33-05 (LOW, hergeleitet): Zwei gleichzeitige Speichervorgänge könnten den Kehrjob des gespeicherten Satzes verlieren

- **Ort:** `ExclusionService::savePatterns()` (Zeile 621 bis 656): erst `setValueArray`, dann
  `jobList->remove(ExclusionSweepJob::class)` und `add(...)`, ohne Sperre über die drei
  Schritte.
- **Beleg:** B3b, 36 Runden mit zwei gleichzeitigen POST: der Job des gespeicherten Satzes
  war immer da, in 6 Runden stand ein Job des unterlegenen Satzes daneben (endet am
  Fingerabdruck). Nicht beobachtet, aber aus der Reihenfolge möglich: A schreibt, B schreibt,
  B plant, **A entfernt** (auch den Job von B) und plant den eigenen. Gespeichert ist dann der
  Satz von B, geplant nur der Lauf von A, der am Fingerabdruck endet.
- **Einordnung:** Folge ist nur Verzögerung: die Dateien unter dem gespeicherten Satz verlassen
  den Index dann erst über Weg C (spätestens im nächsten Abgleich), und neue Schreibvorgänge
  darunter reiht der Listener ohnehin nicht ein. Nur zwei Admins, die im selben Moment
  speichern, erreichen den Fall.
- **Fixvorschlag:** accept mit Zielphase 36 (Launch-Korpus), oder `remove`/`add` so
  ordnen, dass der Plan aus dem nach dem Schreiben gelesenen Satz entsteht.

### L-33-06 (LOW, Performance): Endet eine Runde am Ruhe-Tor genau zwischen zwei Mounts, gilt der Zyklus als fertig

- **Ort:** `backend/src/findling/worker/reconcile.py` (`run_once`, Schleife über die Mounts,
  Zeile 416 bis 419; `_is_due`, Zeile 808 bis 822) und `backend/src/findling/store/repo.py`
  (`_RECONCILE_STATE_SQL`, Zeile 613 bis 615: `MAX(finished_at)` und die Zahl der Mounts
  mit Lesezeichen über 0).
- **Beleg (gefahren, P4):** die letzte Scheibe von Mount 3 schloss den Mount (Lesezeichen 0,
  Stempel), das Tor hielt vor Mount 4. Danach trug keine Zeile ein Lesezeichen über 0, und
  `MAX(finished_at)` war der eben geschriebene Stempel; die zwei folgenden Takte starteten
  keine Runde. Mount 4 wäre erst im nächsten Zyklus (24 Stunden später) gelaufen.
- **Einordnung:** ein Mount, der in der Reihenfolge nach einem Mount mit viel Arbeit am Ende
  steht, wartet einen Zyklus länger; trifft das Tor in jedem Zyklus dieselbe Grenze, öfter.
  Kein Datenverlust: Weg A räumt neue Muster unabhängig davon, und der nächste Zyklus
  beginnt wieder vorn. Die Regel stammt aus Phase 3 und ist nicht Teil des Phasen-Diffs;
  Phase 33 hat nur die Arbeitsmenge von Weg C vergrößert, die das Tor auslöst.
- **Fixvorschlag:** beim Halt am Tor vor einem Mount dessen Lesezeichen als begonnen
  schreiben (oder den Zyklus über einen eigenen Beginn-Stempel statt `MAX(finished_at)`
  führen), Regressionstest im Stil von `test_reconcile.py`.

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
| Räumwege | echte Saat, echte Speicherroute, Nachfolger über `IJobList::add` des Kerns, Abgleich über den Stempel in `state.db` statt über Tests mit Doppeln | B1 bis B5 in Ordnung |
| Wettlauf | zwei Sitzungen hinter einer Barriere, 36 Runden | Job des gespeicherten Satzes immer da; L-33-05 |
| Seite mit 1.4.x-Status | Proxy, der zwei Felder aus `/status` nimmt, Seite im Browser | Zeilen verborgen, keine Fehler |
