# 40-06-SUMMARY: Issue-#36-Fix-Paket und Kandidat F in 1.6.0

Plan 40-06, Owner-Entscheid 28.10. ("1.6 verzögern statt 1.6.1"). Drei Tasks ausgeführt,
TDD je Task (RED-Commit vor dem ersten fix/feat-Commit), alles auf main gepusht.

## Was gebaut wurde

- **Befund B (Kern, budachst-Fall):** `GatewayRefused(NextcloudException)` in
  backend/src/findling/nc/client.py mit `status`; Statusraster E-40-06-01 an der einen
  Raise-Stelle (404/998 None, 502/503/504 `NextcloudException` = Ausfall, jeder andere
  Status ab 400 `GatewayRefused`), Konstante `_OUTAGE_STATUS`. poller.py urteilt an beiden
  `_fetch_file`-Aufrufstellen (Content-Zweig und OCR `_scan`, seriell und unter Slots)
  `failed(gateway_error)`, kein unlock, der Pass läuft weiter. Häufungs-Schwelle
  `GATEWAY_SAME_STATUS_OUTAGE_AFTER: Final = 5` (E-40-06-02): derselbe Status für
  min(5, claimed) Dateien bei mindestens 2 claimed wirft `_GatewayDown`, alle Urteile des
  Passes verfallen, Zeilen gehen mit Gutschrift zurück.
- **Befund A:** die Ausfall-Zeile behält ihre Worte ("content gateway did not deliver, ...")
  und hängt `with http status <n>` an, wenn die Exception einen Status trägt; eigene Zeile
  "content gateway refused one file, http status %d for file id %d" für die Ablehnung.
- **Befund C:** `IndexBatchWriter.rollback()` (unter `self._lock`, `_require_open().rollback()`,
  Zähler auf 0, INFO-Zeile); `_abort` rollt vor dem unlock zurück, ein Fehler des Rollbacks
  wird geloggt und verhindert das unlock nie (Test mit werfendem Rollback-Double).
- **Befund D:** Modulwert `_GATEWAY_UNAVAILABLE_SINCE` im Poller (erster Abbruch der
  Strähne, `ROUND_WORKED` und beide `ROUND_EMPTY`-Ausgänge löschen, `ROUND_QUEUE_UNAVAILABLE`
  lässt stehen), WARNING-Zeile beim Abbruch; `StatusResponse.gatewayUnavailableSince`
  in beiden Zweigen von report() (Pitfall 2); AdminViewService reicht das Feld als
  optionalCounter durch; admin.php und admin.js zeigen den einen neuen Satz.
- **Befund E:** GatewayController loggt den 422-Zweig statisch mit fileId; der
  \Throwable-Zweig bleibt byte-gleich 500 und trägt einen Kommentar zum budachst-Fall.
- **Suchpfad:** `StorageNotAvailableException` an den drei Aufrufstellen in SearchService
  (Suchschleife, Ähnliche-Quelle, Ähnliche-Kandidaten) gefangen; `readableFile()` und
  `readableNode()` zeichengleich zu c75fb6cf (awk-Vergleich im verify: gleich),
  test_php_acl_boundary.py grün.
- **Kandidat F (#19):** `filled_languages()` misst nie mehr im Aufrufpfad.
  `filled_languages_as_of()` liest unter `_LOCK` nur den Cache und startet bei Stale oder
  Kaltstart genau einen Daemon-Thread `findling-fill-refresh` (single flight, Flag = der
  Thread, im finally unter `_LOCK` gelöscht). Der Refresh nimmt `read_side()` selbst,
  misst ohne Lock, schreibt unter `_LOCK` nur bei gleicher Generation und gleichem
  index_dir (M-18-02 im Schreibpfad) und nie rückwärts. `StatusResponse.languagesFilledAsOf`
  kommt aus demselben Aufruf wie `languagesFilled`. report()-Signatur unverändert.
  Testhilfe `join_fill_refresh()`.

## Entscheidungen

- E-40-06-01 (Statusraster) und E-40-06-02 (Häufungs-Schwelle 5) wie im Plan, beide im
  Code zitiert (client.py `_OUTAGE_STATUS`, poller.py Konstante und `_count_refusal`).
- E-40-06-03 (PHP-404 für kaputte Mounts): gestrichen, ID bleibt belegt; der
  Regressionstest "StorageNotAvailableException an fopen -> 500, ausdrücklich nicht 404"
  steht in GatewayControllerTest.
- E-40-06-04 (ein neuer Katalogsatz): in allen 16 Katalogen und allen fünf
  docs/l10n-Tabellen, nicht in docs/l10n-catalogues.md; de.json steht bei 354 Schlüsseln
  (Absatz im Vertragstest nachgezogen).
- Der Ausfall-Snapshot liegt als Modulwert im Poller (Muster guard: ein Name, int oder
  None, atomar gelesen); status.py importiert `findling.worker.poller` (kein Zyklus, die
  Quelltext-Gates von status.py, z. B. genau ein `guard.snapshot()`, bleiben grün).

## Vorgaben des Koordinators (Z1 bis Z4)

- **Z1:** nachgezogen wurde ausschließlich `PHP_FILES_TODAY`/`PHP_TREE_HASH_TODAY`
  (test_measurement_scripts.py :1116-1117 vor dem Commit; der Journalabsatz steht direkt
  davor, hinter dem letzten 40-02-Absatz). Das eingefrorene Messlauf-Paar `PHP_FILES`/`PHP_TREE_HASH`
  (:458/:468) ist unberührt.
- **Z2:** zwei autouse-Fixtures in backend/tests/conftest.py, je vor und nach jedem Test:
  `forget_the_gateway_outage` (`poller.reset_gateway_outage()`) und
  `quiesce_the_fill_refresh` (`resources.join_fill_refresh()`). Sie kamen jeweils mit dem
  GREEN-Commit (4c3d33bd bzw. ab34d601), weil sie im RED-Stand jeden Test der Suite an
  einer fehlenden Funktion hätten scheitern lassen.
- **Z3:** test_a_fill_level_measured_before_a_reset_is_answered_and_not_remembered hält
  "and it is not remembered" wörtlich; die Teilaussage "the reading is handed out" ist
  ersetzt durch die gleich scharfe Prüfung, dass der Refresh de gemessen hat
  (`measured == [FIELD_BODY_DE]`) und nichts geschrieben wurde. Die Meldung steht englisch
  im Code ("the refresh measured de, but did not write it"), weil CLAUDE.md Code auf
  Englisch verlangt; inhaltlich ist es der Satz aus Z3.
- **Z4:** "httpx" steht in backend/src nur in nc/client.py (Vertragstests grün; poller.py
  nennt es auch im Kommentar nicht, die Tests importieren httpx nur in tests/);
  `guard.snapshot()` steht in status.py genau einmal; keine neue Poller-Logzeile enthält
  path/title/text/term (test_no_log_call_names_a_path_a_title_or_a_piece_of_text grün);
  `rollback` ist ein einzelnes `with self._lock`-Statement und steht in der Liste von
  test_every_writing_method_holds_the_lock. verify-Ketten liefen als `( ... ) || false`.

## Abweichungen

- **[Rule 1] OCR-Ablehnungstest auf zwei Zeilen:** der erste RED-Entwurf nahm drei
  OCR-Zeilen in Economy; Economy behält zwei OCR-Zeilen je Slot und gibt die dritte per
  unlock zurück, die Assertion `unlocked == []` hätte also etwas anderes geprüft. Im
  B-Commit (6880fa1e) auf zwei Zeilen gesetzt, der Mehr-Slot-Fall prüft weiter drei.
- **[Rule 1] Strähnen-Test:** eine Assertion las nach dem Sentinel noch den alten Wert;
  im D-Commit (4c3d33bd) auf den Sentinel 1_700_000_000 gezogen.
- **[Rule 2] Satz für Befund D in beiden Hälften der Seite:** der Plan nannte ein leeres
  `<p ... hidden></p>`. admin.js rendert den Bootstrap-Stand nicht neu ("the template has
  already put these very numbers on the page"), ein leeres Element wäre bis zum ersten
  Poll falsch gewesen. Deshalb rendert admin.php den statischen Satz mit `hidden`, solange
  `$gatewayDown` falsch ist (Muster rules-pending), und admin.js schreibt ihn per t() und
  `text()` (textContent) und schaltet ihn mit `shown()`; das Feld steht im Fingerprint.
- **[Rule 3] Schlüsselzahl:** test_the_german_catalogue_covers_both_german_language_codes
  pinnt die Zahl der de-Schlüssel; 353 -> 354 mit Absatz für Plan 40-06.
- **head_green mit sieben Workflows:** der Auftrag nannte sechs Namen, der Plan sieben
  ("PHP and store metadata gates" inklusive, php/ ist berührt). Gefahren wurde der Aufruf
  des Plans, also der strengere.
- PHP-RED: PHPUnit läuft nur in CI; RED belegt per Lektüre (422-Log-Erwartung und die drei
  Suchpfad-Fälle scheitern ohne den Fix an fehlender Logzeile bzw. an der Exception; der
  500-Regressionstest und die readableNode-Gegenprobe sind Wächter und waren schon vorher
  grün). CI-Beleg siehe unten.

## Commits

- 6b51f59d test(40-06): one broken file must not block the queue (#36) (RED Task 1)
- 6880fa1e fix(40-06): a refused file is a verdict, not a gateway outage (#36 B)
- 12f4f0a5 fix(40-06): log the http status of a gateway failure (#36 A)
- fc25db9b fix(40-06): roll back the pending batch on an aborted pass (#36 C)
- 4c3d33bd feat(40-06): expose gateway_unavailable since in /status (#36 D)
- 10377b41 test(40-06): the package tree hash follows the issue 36 fixes
- 3ef146d1 test(40-06): the gateway logs its 422 branch and the search survives a broken mount (#36) (RED Task 2)
- 910293ce fix(40-06): log the 422 branch of the gateway and keep the search answering on a broken mount (#36)
- e5603b78 feat(40-06): the admin page names a silent content gateway (#36 D)
- 0a44756e docs(40-06): changelog for the issue 36 fix package
- 2e4fad73 test(40-06): /status must answer at once while the fill level is measured (#19) (RED Task 3)
- ab34d601 fix(40-06): /status never waits for the language fill level (#19)
- 4ed0f846 test(40-06): the package tree hash follows candidate F (Code-Kopf)

RED-Belege lokal: Task 1 test_status_endpoint 50 failed (FIELDS), test_index_writer 4
failed, test_poller/test_gateway_client Collection-Fehler (GatewayRefused fehlte);
Task 3 59 failed in test_status_endpoint + test_read_side.

## Testfunktionszahlen (vorher c75fb6cf -> nachher, keine sank)

| Datei | vorher | nachher |
|---|---|---|
| backend/tests/test_poller.py | 186 | 199 |
| backend/tests/test_gateway_client.py | 23 | 26 |
| backend/tests/test_index_writer.py | 44 | 47 |
| backend/tests/test_status_endpoint.py | 73 | 78 |
| backend/tests/test_read_side.py | 34 | 34 |
| backend/tests/test_admin_ui_contract.py | 113 | 114 |
| backend/tests/test_measurement_scripts.py | 77 | 77 |
| php/tests/Unit/GatewayControllerTest.php | 8 | 11 |
| php/tests/Unit/SearchServiceTest.php | 53 | 57 |

Neu abgeleitet (Aussage behalten, Auslöser auf den Refresh): test_read_side.py :634 und
der M-18-02-Test (:723), test_status_endpoint.py :1030, :1078, :1168, :1206, :1237-1251
(Zählung je Refresh, innerhalb der TTL keine zweite Messung, nach reset_read_side eine
neue mit der Seite der neuen Generation). Umgeschrieben: der 500-Bestandstest auf 503
(Aussage gleich), 404-Test um :521 wortgleich.

## Baumhash-Paare

- Python-Paket (`PACKAGE_FILES_TODAY`/`PACKAGE_TREE_HASH_TODAY`), 80 Dateien durchgehend:
  3c7df60a... (40-01) -> b05eb576d0189e1e... (Task 1, Absatz "Plan 40-06 (issue #36 A, B,
  C, D)") -> 3c6f35e64df85b2d... (Task 3, Absatz "Plan 40-06 (issue #19, candidate F)").
- PHP (`PHP_FILES_TODAY`/`PHP_TREE_HASH_TODAY`), 110 Dateien:
  73bae603ef6cd629... -> 71443d7d69d7b505... (Task 2, Absatz "the 422 log line, the
  search on a broken mount and the outage sentence", "The package pair does not move in
  this step").
- Jeder Wert doppelt gerechnet: Rezept 40b-baumhash.py und unabhängig find | sort | tr -d
  '\r' | sha256sum (Gegenprobe des Shell-Rezepts auf dem alten PHP-Stand: 73bae603, gleich).
  `-k tree_hash` nach jedem Task grün.

## Lokale Suite und Gates

- Task 1: 3447 passed/48 skipped + 2684 passed/21 skipped (zwei Vordergrund-Hälften,
  1,66 GB frei).
- Kopf 4ed0f846: 3448 passed/48 skipped + 2687 passed/21 skipped = 6135 passed, 69
  skipped (1,89 GB frei, zwei Hälften).
- ruff check, ruff format --check, pyright (latest) 0 errors, vulture 80 vor jedem
  Commit grün (nur in den RED-Zwischenständen meldete pyright die noch fehlenden Namen).

## Workflow-Zusicherungs-Check (STOPP-Regel aus 40-03)

Suche 1, Logtexte und Verdikte (`content gateway did not deliver|unknown error reading a
file|gateway_unavailable|gateway_error`):

- .github/workflows/*.yml: **kein Treffer**. Urteil: unberührt.
- backend/tests: test_poller.py :1175, :1239, :1243, :1257, :1275, :1278, :1300, :1342,
  :1359, :1380, :1449-1482 (die Tests dieses Plans, angepasst), test_admin_ui_contract.py
  :2652 (Docstring dieses Plans), test_measurement_scripts.py :2353 (Journal dieses Plans),
  test_store_repo.py :692, :693, :776, :835 (record() mit failed/gateway_error, Vokabular
  unverändert). Urteil: alle geprüft, unberührt bzw. von diesem Plan selbst.
- Die Zeile "content gateway did not deliver" bleibt wortgleich am Anfang (nur
  " with http status <n>" angehängt), die greps aus #36 treffen weiter.

Suche 2, Status-Kopplung (`report(|StatusResponse|languagesFilled` in deploy-harp.yml):

- :4025 und :5100/:5202/:6224: Shell-Funktionen `report()`/`index_report()`, die
  `python -m findling.tools.index_status` aufrufen; das Tool liest weder
  filled_languages noch StatusResponse. Urteil: unberührt.
- :6880 (Kommentar), :6933 `report(leave_out=[storage])`, :6934 `report()` in Zusicherung
  12 ("the 1.6 changes survive the upgrade", Store upgrade 5): Signatur unverändert, die
  Substring-Prüfung sucht "indexedLeftOut"/"embeddedLeftOut" in `model_dump_json()`; die
  neuen Felder gatewayUnavailableSince und languagesFilledAsOf enthalten keinen der beiden
  Teilstrings und leaveOut-Felder bleiben ohne Parameter absent. Der Hintergrund-Refresh
  startet in diesem kurzlebigen `python -`-Prozess einen Daemon-Thread, dessen Ergebnis
  niemand liest; geprüft wird kein languagesFilled. Urteil: unberührt (Beleg: HaRP deploy
  grün auf dem Kopf, siehe unten).
- Kein Treffer auf `StatusResponse` oder `languagesFilled`. Einziger
  filled_languages-Treffer ist der Kommentar :7384 im Step "Store upgrade 6, the rebuild a
  changed language set orders": der Step misst den Füllstand selbst über
  `resources.read_side()` und `searcher.terms_with_prefix(...)` und nicht über
  filled_languages(); er ist von Kandidat F unberührt.
- Weitere Suche "gateway" in allen Workflows: nur integration.yml :615-943 (read_corpus
  über das Gateway, 404-Pfad und Fehlerzählung über `except Exception`), unberührt.
- deploy-harp.yml byte-unverändert: `git log c75fb6cf..HEAD -- .github/workflows/deploy-harp.yml`
  leer, `git status --porcelain` darauf leer.

## Kopf auf main: 4ed0f846, head_green.sh

`scripts/ci/head_green.sh 4ed0f846f7698e4f6d70ba5cc12ae74749b86a16 "Python gates" "PHP and store metadata gates" "HaRP deploy" "Integration" "Resilience" "Multi-arch image" "Security scans"`, Exit 0:

```
40834773386 PHP and store metadata gates success
40834773542 OpenSSF Scorecard success
40834773406 Security scans success
40834773362 Multi-arch image success
40834773368 Python gates success
40834773510 Integration success
40834773614 Resilience success
40834773430 HaRP deploy success
```

Der erste Wartelauf im Hintergrund wurde vom Speicher-Reaper der Box gestoppt (kein
Befund des Laufs); der Aufruf oben ist der formale Lauf nach Abschluss aller Workflows.
Keine Korrekturrunde nötig, alles im ersten Push grün.

PHP-Unit-Beleg: "PHP and store metadata gates" 40834773386, Job "PHPUnit over the
companion app": `OK (902 tests, 3994 assertions)`; der letzte grüne Lauf davor
(40750963023 auf 631763b5) meldete `OK (895 tests, 3949 assertions)`. Die Differenz von
sieben Tests sind genau die drei neuen GatewayControllerTest- und vier neuen
SearchServiceTest-Fälle (der Job druckt keine Testnamen, nur die Summe).

## Satz für die Owner-Runde 40-04 (Block G)

- en: "The content gateway did not answer on the last indexing pass. The affected files
  stay in the queue and are tried again; the search keeps answering."
- de: "Das Content-Gateway hat beim letzten Indexierungslauf nicht geantwortet. Die
  betroffenen Dateien bleiben in der Warteschlange und werden erneut versucht; die Suche
  antwortet weiter."
- fr: "La passerelle de contenu n'a pas répondu lors du dernier passage d'indexation. Les
  fichiers concernés restent dans la file d'attente et seront réessayés. La recherche
  continue de répondre."
- es/it/nl/pt_PT/pt_BR: maschineller Entwurf unter Vorbehalt (Muster 39-01).
- Dazu Kandidat F: /status antwortet sofort aus dem Cache, languagesFilledAsOf nennt das
  Alter der Messung, beim Kaltstart steht languagesFilled bis zum ersten Refresh leer.

## Issue #36

Fix-Link in #36 folgt nach Store-Release 1.6.0 (Owner-Entscheid 29.10.).

Hinweis: Die Änderung des Owners kam an, nachdem der eine Kommentar bereits gepostet war
(https://github.com/street1983nk/nextcloud-search/issues/36#issuecomment-6492666744,
englisch, ohne "Closes", Link auf 6880fa1e und den Vergleich c75fb6cf...4ed0f846). Er wurde
nicht gelöscht; die Entscheidung darüber liegt beim Owner bzw. Koordinator.

Issue #19: nichts gepostet.

## Known Stubs / Threat Flags

Keine Stubs. Keine neue Angriffsfläche außerhalb des Threat-Registers (T-40-20 bis
T-40-27 alle wie geplant mitigiert; neue Logzeilen tragen nur Status, file id und Zähler).
