# Auditbericht Phase 29

## CI-Beweis

Stand: 06.10.2026, Plan 29-13. Dieser Abschnitt nennt je Push den Kopf-SHA, die Laufnummer je Workflow und das Ergebnis.

### Push 1: 57b83358..390360c3

Freigabe des Owners, wörtlich: Auf die Frage "Bestaetigst du den Push von main (57b83358..390360c3) nach origin?" antwortete der Owner "ok". Vor dem Push geprüft: 76 Commits, alle von street1983nk, keine Co-Authored-By- oder Claude-Trailer; Suche in `git log -p` nach IPv4- und Token-Mustern ergab nur die Loopback-Adresse, eine Adresse aus dem Dokumentationsnetz nach RFC 5737 und den Plantext selbst; keine Box-Adresse, kein Token.

Kopf: `390360c3d21e5c827223362f3df33728512d42c7`, gepusht 10:49Z.

| Workflow | Lauf | Attempt | Ergebnis |
|---|---|---|---|
| Python gates (python.yml) | 37452332061 | 1 | success, 4721 passed, 14 skipped |
| PHP and store metadata gates (php.yml) | 37452332197 | 1 | success, PHPUnit `OK (589 tests, 2106 assertions)` |
| Multi-arch image (docker.yml) | 37452332135 | 1 | success, amd64 und arm64 |
| Integration (integration.yml) | 37452332015 | 1 | success |
| Resilience (resilience.yml) | 37452332174 | 1 | success |
| HaRP deploy (deploy-harp.yml) | 37452332294 | 1 | **failure**, nur Bein stable34/8.2/ubuntu-24.04, Schritt "Store upgrade 3" |

Die PHPUnit-Suite (`php/tests/Unit`) enthält `Version001400Date20261006000000Test.php`, `ProfileControllerTest.php` und `AdminViewServiceTest.php`; sie liefen damit erstmals in CI und sind grün.

Belege aus dem Bein stable34/amd64 (Job 112231598056), alle Schritte bis "Store upgrade 2b" grün:

- Store install 7: `content hit after 3 cron rounds, with nothing configured` und `occ calls between the installation and the hit: none, which is what zero config means`.
- Store upgrade 2b: `the picture is failed/corrupt in state.db and in findling_file_state`, `the sidecar is failed/corrupt in state.db and in findling_file_state`, `sown: a picture and a sidecar, both failed(corrupt) under v1.3.2, and the seed word finds nothing`.

### Befund C-29-01: Sprachmarke der 1.3.2-Installation

- Roter Schritt: "Store upgrade 3", `the v1.3.2 installation reports the languages mark 'de,en' instead of an empty one, so a rebuild already stamped it`.
- Kein Flake-Muster: Die Zusicherung prüfte eine Annahme aus Plan 29-11 ("1.3.2 meldet die Marke leer, solange kein Neuaufbau sie stempelt"), die der erste echte Lauf widerlegt. Die Upgrade-Strecke läuft nur auf diesem Bein, die anderen drei Beine waren dort `skipped`.
- Ursache, belegt am Code des Tags v1.3.2: `findling.index.open.stamp_a_new_directory` schreibt Schema-, Sprach- und Niederländisch-Marke, bevor ein frisches Indexverzeichnis angelegt wird (Befund M-19-05). Eine frische 1.3.2-Installation trägt die Marke deshalb mit dem registrierten Satz de,en. Das Produkt verhält sich richtig, die Erwartung im Workflow war falsch.
- Fix `8ae89572`: "Store upgrade 3" verlangt `de,en` (den Satz, den "Store upgrade 4" registriert, also ordnet das Upgrade keinen Neuaufbau an); "Store upgrade 5" verlangt `de,en` vorher und denselben Wert nachher. Das ist nicht schwächer als vorher: Jeder andere Wert vorher und jede Änderung nachher sind rot. Der Test `test_upgrade_seed_steps.py` folgt und prüft zusätzlich die Bedingung in Schritt 5.
- Lokal vor dem Commit: volle Suite 4711 passed, 25 skipped; ruff, ruff format, pyright (latest), vulture sauber.

### Push 2: 390360c3..7130c4f0

Freigabe des Owners, wörtlich: Auf die Frage "Darf ich die 2 Commits 390360c3..7130c4f0 (8ae89572 Fix, 7130c4f0 Auditbericht) auf origin/main pushen?" antwortete der Owner "ok".

Kopf: `7130c4f0240d88ca650f8ca44153bf98ff936b3b`, gepusht 11:21Z.

| Workflow | Lauf | Attempt | Ergebnis |
|---|---|---|---|
| Python gates | 37455892343 | 1 | **failure**, 1 failed (Befund C-29-02), 4721 passed, 14 skipped |
| Multi-arch image | 37455892371 | 1 | success |
| Integration | 37455892246 | 1 | success |
| Resilience | 37455892221 | 1 | success |
| HaRP deploy | 37455892381 | 1 | **failure**, nur Bein stable34/amd64, Schritt "Store upgrade 6" (Befund C-29-03); stable33, stable34/arm64 und stable35 success |
| PHP and store metadata gates | nicht ausgelöst | | Pfadfilter: der Diff 390360c3..7130c4f0 berührt weder `php/**` noch `backend/appinfo/**` noch einen anderen Pfad des Filters; der Beleg bleibt Lauf 37452332197 |

Belege aus dem Bein stable34/amd64 (Job 112243285452), Schritte 3 bis 5 jetzt grün:

- Store upgrade 4: `the instance performed the app update: 1.3.2 to 1.4.0`.
- Store upgrade 5, wörtlich:
  - `unchanged  .marks.indexVersion = 1`, ebenso schemaVersion 2, analyzerVersion 1, wordlistHash und tantivyVersion unverändert.
  - `the sidecar is skipped/system_file in state.db and in findling_file_state`
  - `the picture is indexed in state.db and carries no verdict in findling_file_state`
  - `the seed word finds exactly the file id 141, the picture 1.3.2 had booked as corrupt`
  - `no start_rebuild_on_drift line in 60 lines of container log`
  - `the recheck mark was absent before the upgrade and reads done after it`
  - `the languages mark reads de,en before and after the upgrade, nothing was restamped`
  - `unchanged  embedding mark = multilingual-e5-small/int8/384/1024` und `unchanged  vector stock without the picture = ...:94:222`, keine Neu-Einbettung des Bestands; `the picture carries 1 chunk(s), embedded once as a new document`
  - `the profile in force after the upgrade is economy`
  - `all eight assurances hold`
- Store upgrade 6: neun von zehn Zusicherungen grün, darunter `the question alemanes went from 0 to 1 hits across the rebuild` und `vectors.db is unchanged`.

### Befund C-29-02: Adressmuster im Auditbericht

- Rot: `test_public_artifacts.py::test_no_file_under_docs_carries_a_finding_outside_the_exception_list[muster-der-umsetzung]`, gefunden in diesem Bericht.
- Ursache: Der Abschnitt zu Push 1 nannte die beiden bei der Vorab-Suche gefundenen Adressen wörtlich. Die Ausnahmeliste des Gates führt nur unvermeidbare Kernelversionen; eine Adresse in einem Bericht ist vermeidbar.
- Fix: Formulierung ohne Adressen (Loopback, Dokumentationsnetz nach RFC 5737), keine Ausnahme. Lehre: Der lokale Vollauf vor Push 2 lief vor dem Anlegen dieses Berichts; der Bericht war nicht im lokalen Gate.

### Befund C-29-03: Schemaschritt im Neuaufbau von Store upgrade 6

- Rot: `the schema mark is still 2 after the rebuild, so nothing was stamped and the rebuild did not go through`.
- Ursache, belegt: Zusicherung 1 verlangte einen Schritt nach oben. Das galt beim Start v1.2.0 (Index-`SCHEMA_VERSION` 1). v1.3.2 und der Kopf tragen beide 2 (`git grep SCHEMA_VERSION v1.3.2 HEAD -- backend/src`), ein reiner Sprachsprung hat keine Schemadrift zu beantworten. Die übrigen neun Zusicherungen hielten, die Sprachmarke ging korrekt auf `de,en,es`.
- Fix `7361b771`: Zusicherung 1 verlangt 2 vorher und 2 nachher; ein Test bindet die 2 an `findling.config.SCHEMA_VERSION`, damit eine künftige Schemaerhöhung das Gate rot macht. Dass der Neuaufbau gestempelt hat, belegt Zusicherung 2, denn nur `stamp_after_swap` schreibt den neuen Satz in ein bestehendes Verzeichnis.

### Push 3: 7130c4f0..7b8b4271

Freigabe des Owners, wörtlich: Auf die Frage "Darf ich die 2 Commits 7130c4f0..7b8b4271 (7361b771 Fix Store upgrade 6, 7b8b4271 Auditbericht) auf origin/main pushen?" antwortete der Owner "ok". Mit diesem Wort hat der Owner die geänderte Zusicherung aus C-29-03 gesehen und mitgetragen.

Kopf: `7b8b4271ec73ae4160dd68afdc2dcc130d40b6bc`, gepusht 12:00Z. **Alle ausgelösten Workflows grün, jeweils im ersten Attempt.**

| Workflow | Lauf | Attempt | Ergebnis |
|---|---|---|---|
| Python gates | 37460204981 | 1 | success, 4723 passed, 14 skipped |
| Multi-arch image | 37460204900 | 1 | success, amd64 und arm64 |
| Integration | 37460204996 | 1 | success |
| Resilience | 37460204909 | 1 | success |
| HaRP deploy | 37460204929 | 1 | success, alle vier Beine (stable33, stable34 amd64 und arm64, stable35) |
| PHP and store metadata gates | nicht ausgelöst | | Pfadfilter: seit 390360c3 hat sich kein Pfad des Filters geändert (nur `deploy-harp.yml`, ein Backend-Test und diese Doku); der PHP-Beleg bleibt Lauf 37452332197 auf 390360c3, `OK (589 tests, 2106 assertions)` |

Belege aus dem Upgrade-Bein stable34/amd64 (Job 112257592326), wörtlich:

- Store install 7: `content hit after 3 cron rounds, with nothing configured`; `none, which is what zero config means`.
- Store upgrade 2b: `sown: a picture and a sidecar, both failed(corrupt) under v1.3.2, and the seed word finds nothing`.
- Store upgrade 3: `three terms, one file each; the Spanish question with no hit at all; the languages mark de,en; the state is on record in upgrade-before.json`.
- Store upgrade 4: `the instance performed the app update: 1.3.2 to 1.4.0`.
- Store upgrade 5:
  - `unchanged  .marks.indexVersion = 1`
  - `the sidecar is skipped/system_file in state.db and in findling_file_state`
  - `the seed word finds exactly the file id 141, the picture 1.3.2 had booked as corrupt`
  - `the recheck mark was absent before the upgrade and reads done after it`
  - `the languages mark reads de,en before and after the upgrade, nothing was restamped`
  - `unchanged  embedding mark = multilingual-e5-small/int8/384/1024`
  - `the profile in force after the upgrade is economy`
  - `all eight assurances hold`
- Store upgrade 6: `the schema mark reads 2 before and after the rebuild, the schema of the running code`; `the question alemanes went from 0 to 1 hits across the rebuild, which is the Spanish chain and the field plan working together`; `all ten assurances hold`.

Damit sind die Fremdinstallation (Store install 0 bis 7) und die Upgrade-Strecke 1.3.2 auf 1.4.0 (Store upgrade 0 bis 6) mit der neuen Saat auf demselben Kopf Ende zu Ende grün.

### Offen

- Einzelnachweis der beiden Linux-SIGKILL-Fälle aus `test_slots_kill.py` (Merker aus 29-04): python.yml läuft mit `-q` ohne `-rs`. Der Lauf 37452332061 belegt die Suite insgesamt (4721 passed, 14 skipped), nicht die beiden Fälle namentlich. Lokal ist kein Linux verfügbar (Docker-Engine und WSL-Distribution laufen nicht). Plan 29-13 sieht keine Workflow-Änderung dafür vor; der Nachweis (`-rs` für diese Datei) geht an Plan 29-14.
