---
phase: 23-haertung-und-store-einreichung-1-3-0
plan: 06
subsystem: ci / release
tags: [deploy-harp, upgrade-proof, gone-repair, version-bump, REL-03, D-10]
requires:
  - "23-05 (Version001300Date20260927000000)"
  - "23-04"
provides:
  - "Store upgrade 2b: gesätes skipped(gone)-Fehlurteil vor dem Upgrade"
  - "Zusicherung 3 mit exakten Seed-Differenzen, neue Zusicherung 3b (Reparatur)"
  - "Beide Hälften auf 1.3.0"
affects:
  - "Plan 23-07 (Store-Texte, Release)"
  - "Orchestrator: Merge von ci-23-06-release-e2e nach main"
tech-stack:
  added: []
  patterns:
    - "Saat direkt in die SQLite-DB der Wegwerf-Instanz, Container per docker pause für das Fenster Scan bis Urteil"
    - "moved_by_seed(): Vorher plus Schritt statt unchanged, nur für die von der Saat berührten Zähler"
key-files:
  created: []
  modified:
    - .github/workflows/deploy-harp.yml
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
decisions:
  - "Variante nie gesehene Datei (kein Rückfall): neue Datei gone-seed/upgrade-gone-seed.txt, Container pausiert zwischen files:scan und Urteil"
  - "Wartezeit vor dem Nachher-Schnappschuss fragt nur den Poller, kein cron.php, Budget UPGRADE_DRAIN_BUDGET_SECONDS statt neuer Zahl"
  - "3b ist Unterzusicherung von 3, daher bleibt 'seven assurances' ungezählt"
  - "CI-Beweis auf Hilfsbranch ci-23-06-release-e2e, nicht auf main"
metrics:
  duration: "ca. 55 min"
  completed: 2026-09-27
  tasks: 2
  files: 3
---

# Phase 23 Plan 06: Versionssprung 1.3.0 und Upgrade-Beweis der gone-Reparatur Summary

Beide Hälften tragen 1.3.0. Die Upgrade-Strecke in deploy-harp.yml sät vor dem Upgrade ein #14-Fehlurteil auf eine nie indexierte Datei und verlangt danach seine Reparatur: 3 Zähler bewegen sich um genau 1, alle anderen bleiben unverändert, 3b findet die Datei. HaRP deploy (4 Beine), probe-92d mit from_tag=v1.2.0 und alle übrigen Workflows sind grün.

## Erst nachgesehen (vor dem Bau)

- **Wo 1.2.0 läuft:** Die Nextcloud-Instanz läuft direkt auf dem Runner (PHP, `cron.php`, `apps/`, `data/`). Die Datenbank ist SQLite unter `${FINDLING_DB}` und wird mit `sqlite3 -cmd '.timeout 30000'` erreicht, so wie Store upgrade 3b und 4 es schon tun. Der ExApp-Container `nc_app_findling_backend` (Image 1.2.0) wurde in Store upgrade 1 registriert, sein Name steht in `UPGRADE_OLD_CONTAINER`.
- **Wie der Container Arbeit bekommt:** über seinen eigenen Poller gegen die Queue-Route (Abkühlung 15 bis 120 s). `files:scan` löst kein Node-Event aus, der FileEventListener bleibt also still. Und sobald ein Endurteil in `findling_file_state` steht, lässt der Reconcile die Datei in Ruhe. Genau so wurden die Urteile aus #14 dauerhaft.
- **Vorher-Schnappschuss:** entsteht in Store upgrade 3, direkt nach dem Leerlaufen von Store upgrade 2 und ohne weiteres cron.php.
- **Nachher-Schnappschuss:** Store upgrade 5 hat bisher NICHT abgewartet, bis die Queue leer ist. Deshalb gibt es jetzt eine Warteschleife mit Frist vor dem Schnappschuss (siehe unten).
- **Zeichengrenze:** Der run-Block von Store upgrade 5 enthält `${{ }}`-Ausdrücke und unterliegt damit der 21000-Zeichen-Grenze. Die langen Begründungen stehen deshalb als YAML-Kommentar über dem Schritt. Stand jetzt: 14419 Zeichen.

## Was gebaut wurde

**Task 1 (f74644d), deploy-harp.yml:**
- `SEED_TERM: 'quorvintax'` im Job-env, mit Begründung.
- Neuer Schritt **"Store upgrade 2b, a gone verdict the way issue #14 wrote it (D-10)"** zwischen Store upgrade 2 und 3. Ablauf:
  - Vorbedingung: SEED_TERM liefert 0 Treffer.
  - `docker pause` auf den Container, mit Trap, der ihn auf jedem Ausweg wieder freigibt.
  - Datei `gone-seed/upgrade-gone-seed.txt` anlegen, danach `files:scan --path`.
  - file_id über `oc_storages`/`oc_filecache` ermitteln.
  - Queue-Zeile löschen und `skipped/gone` in `oc_findling_file_state` schreiben, danach `docker unpause`.
  - Fail-closed-Prüfung: genau ein Urteil, keine Queue-Zeile, 0 Suchtreffer.
  - file_id und Dateiname gehen über `GITHUB_ENV` an die späteren Schritte.
- **Store upgrade 5:**
  - Warteschleife vor dem Schnappschuss, bis scheduled plus running 0 sind und der Seed-Treffer 1 ist. Sie fragt nur den Poller, kein cron.php, Frist `UPGRADE_DRAIN_BUDGET_SECONDS`.
  - Neue Funktion `moved_by_seed`.
  - Zusicherung 3: `.container.docs` und `.container.indexed` müssen genau +1 sein, `.nextcloud.skipped` genau -1. Die `::error::`-Texte nennen die Saat.
  - Alle übrigen `unchanged`-Zeilen stehen wörtlich weiter da, auch `.container.skipped`, `.container.failed`, `.nextcloud.failed`, `.nextcloud.scheduled`, `.nextcloud.running` und `.container.rebuildState`.
  - Neue **Zusicherung 3b:** kein skipped/gone mehr für die file_id, und SEED_TERM liefert genau die Datei (per Titel geprüft).
  - Die Step-Summary nennt die Saat.
- Kommentarblöcke im Hausstil: warum es die Saat gibt (D-10, A3), warum genau diese Differenzen erlaubt sind und dass die Migration nur im Zweig "echtes App-Update" läuft.

**Task 2 (3b02ae6):**
- `php/appinfo/info.xml` version, `backend/appinfo/info.xml` version und image-tag auf 1.3.0, alles in einem Commit.
- Die Texte in deploy-harp.yml, die den Versionsabstand erzählen, sind auf "plan 23-06, the tree carries 1.3.0 against the 1.2.0 of the tag" umgestellt. Dazu gehört auch der Kopfkommentar des Upgrade-Blocks, der noch v1.1.0 nannte.
- `UPGRADE_FROM_TAG` bleibt v1.2.0.
- Sonst hängt nirgends Versionslogik an einer festen 1.2.0. Die restlichen Treffer sind Schema-Geschichte in Kommentaren und Tests und bleiben stehen.

## Belege

### Lokal

| Prüfung | Ergebnis |
|---|---|
| YAML-Parse (uv, pyyaml) | ok |
| `grep -c D-10` / `SEED_TERM` in deploy-harp.yml | 10 / 7 |
| `unchanged '.nextcloud.skipped'` | 0 (ersetzt) |
| `unchanged '.nextcloud.scheduled'` / `'.nextcloud.running'` | je 2, wie vorher (1 in Store upgrade 5, 1 in Store upgrade 6) |
| `<version>1.2.0</version>` in beiden info.xml | 0 |
| test_lockstep_versions.py | 23 passed |
| Volle Suite | 3339 passed, 15 skipped |

actionlint ist lokal nicht installiert, daher der pyyaml-Parse als Ersatz.

### CI auf Kopf 3b02ae6 (Branch `ci-23-06-release-e2e`)

| Workflow | Run-ID | Urteil |
|---|---|---|
| HaRP deploy (stable33, stable34 amd64, stable34 arm64, stable35) | 36288038636 | success (alle 4 Beine) |
| 92d probe, `from_tag=v1.2.0`, workflow_dispatch | 36288064261 | success |
| Integration | 36288038552 | success |
| Resilience | 36288038711 | success |
| Python gates | 36288038613 | success |
| PHP and store metadata gates | 36288038551 | success |

**Beweiszeilen HaRP deploy, Upgrade-Bein stable34/ubuntu-24.04 (Job 108532474240):**
- Store upgrade 2b: `sown: one readable file, never indexed, no queue row, skipped(gone) in findling_file_state` (file_id 140)
- Store upgrade 4: `Updated <findling> to 1.3.0`, `occ upgrade answered 0`, `installed_version went from 1.2.0 to 1.3.0`, `the instance performed the app update: 1.2.0 to 1.3.0`. Damit lief der Zweig "echtes App-Update".
- Container-Log nach dem Upgrade (Artefakt upgrade-exapp.log): `pass finished, claimed=1 indexed=1 ... requeued=1`. Der neue Container hat die neu eingereihte Saat also übernommen und indexiert.
- Warteschleife: `open=1 seed hits=0, 900s left` um 02:31:05, 9 s später war die Queue abgearbeitet und die Datei auffindbar.
- Zusicherung 3: `moved by 1 .container.docs 94 to 95`, `moved by 1 .container.indexed 94 to 95`, `moved by -1 .nextcloud.skipped 8 to 7`. Unverändert blieben container.skipped 7, container.failed 6, nextcloud.failed 6, nextcloud.scheduled 0, nextcloud.running 0 und rebuildState idle.
- Zusicherung 3b: `the sown file carries no skipped(gone) verdict any more`, `the seed word finds upgrade-gone-seed.txt, the file the verdict of issue #14 had hidden`
- `all seven assurances hold`
- Store upgrade 6 (Umbau) grün: `the rebuild is through after 4 rounds`, 95 Dokumente, Vektorbestand bitgleich. **Umbau-Dauer ca. 7 s**, gemessen vom Neustart mit neuer Sprachmenge (02:31:18,39) bis zur Meldung "through" (02:31:25,45).
- Store install 0-7 grün auf amd64 (stable33, stable34, stable35) und arm64 (stable34), alle Jobs success.

**Beweiszeilen probe-92d (Job 108532550683, arm64):** `companion started at 1.2.0, on disk 1.3.0, installed 1.3.0`, `occ-upgrade-rueckgabewert 0`, `occ-upgrade-gelungen ja`, `Updated <findling> to 1.3.0`, `bestandstor indexiert 26 uebersprungen 7 fehlgeschlagen 6`, `bestandstor-bestanden ja`. Die Gegenprobe endet wie verlangt mit 41 (`bestandstor-bestanden nein` bei 27/7/6).

## Commits

| Task | Commit | Nachricht |
|---|---|---|
| 1 | f74644d | ci(23-06): seed a gone verdict before the upgrade and prove its repair |
| 2 | 3b02ae6 | chore(23-06): both halves to 1.3.0 |

## Deviations from Plan

1. **Push-Ziel:** Gepusht wurde nach `origin/ci-23-06-release-e2e` statt nach main, nach der CI-Beweis-Regel des Orchestrators (Präzedenz 23-05). probe-92d wurde per `gh workflow run probe-92d.yml --ref ci-23-06-release-e2e -f from_tag=v1.2.0` auf dem Hilfsbranch gestartet. Der Hilfsbranch bleibt stehen.
2. **Migrationsausgabe nicht zitierbar:** `requeued 1 files once judged gone` erscheint weder in der Ausgabe von `occ upgrade` noch in den Artefakten. occ upgrade gibt die `IOutput::info`-Zeilen von Migrationen bei normaler Ausführlichkeit nicht aus. Die Migration ist stattdessen über ihre Wirkung belegt, und zwar in drei unabhängigen Stellen: das Urteil ist gelöscht (3b, SQL), skipped geht von 8 auf 7, und das Container-Log zeigt `requeued=1 ... indexed=1`. Store upgrade 4 blieb unverändert, weil dort kein `-v` gefordert war.
3. **Akzeptanzkriterium "je weiterhin 1":** `grep -c "unchanged '.nextcloud.scheduled'"` und `'.nextcloud.running'` lieferten schon vor diesem Plan 2, weil Store upgrade 6 dieselbe Zeile trägt. Die Absicht des Kriteriums (nichts entfernt) ist erfüllt: die Zählung steht vorher wie nachher bei 2.
4. **Zusätzlich angepasster Kommentar:** Der Kopfkommentar des Upgrade-Blocks ("Since plan 16-09 that tag is v1.1.0") war schon vor diesem Plan veraltet. Er beschreibt den Versionsabstand, deshalb habe ich ihn im Rahmen der Textumstellung von Task 2 mit angepasst.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche.
- T-23-21: nur die drei berührten Zähler laufen über Differenzen, der Rest bleibt `unchanged`.
- T-23-22: der Zweig "echtes App-Update" ist aus dem Log zitiert.
- T-23-23: der Saatschritt gibt keine Geheimnisse aus. Er nutzt nur die vorhandenen `TESTUSER_PASS` und `FINDLING_DB`.
- T-23-24: ein Commit für alle drei Versionsstellen, das Gleichlauf-Gate ist grün.

## Self-Check: PASSED

- FOUND: .github/workflows/deploy-harp.yml (Store upgrade 2b, moved_by_seed, 3b)
- FOUND: php/appinfo/info.xml und backend/appinfo/info.xml mit 1.3.0
- FOUND: Commits f74644d, 3b02ae6
