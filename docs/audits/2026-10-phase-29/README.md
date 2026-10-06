# Auditbericht Phase 29

## CI-Beweis

Stand: 06.10.2026, Plan 29-13. Dieser Abschnitt nennt je Push den Kopf-SHA, die Laufnummer je Workflow und das Ergebnis.

### Push 1: 57b83358..390360c3

Freigabe des Owners, wörtlich: Auf die Frage "Bestaetigst du den Push von main (57b83358..390360c3) nach origin?" antwortete der Owner "ok". Vor dem Push geprüft: 76 Commits, alle von street1983nk, keine Co-Authored-By- oder Claude-Trailer; Suche in `git log -p` nach IPv4- und Token-Mustern ergab nur 127.0.0.1, 192.0.2.1 (Dokumentationsnetz) und den Plantext selbst.

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

### Offen

- Push 2 (Fix-Commit) braucht ein eigenes Owner-Wort (T-28-69).
- Einzelnachweis der beiden Linux-SIGKILL-Fälle aus `test_slots_kill.py` (Merker aus 29-04): python.yml läuft mit `-q` ohne `-rs`. Der Lauf 37452332061 belegt die Suite insgesamt (4721 passed, 14 skipped), nicht die beiden Fälle namentlich. Lokal ist kein Linux verfügbar (Docker-Engine und WSL-Distribution laufen nicht). Plan 29-13 sieht keine Workflow-Änderung dafür vor.
