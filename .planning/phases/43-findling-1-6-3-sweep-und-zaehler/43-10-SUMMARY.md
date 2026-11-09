---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 10
subsystem: release (Testbuild, Versionsnachweis A5/A6)
tags: [testbuild, rc, version-proof, harp, appapi, mbozem]
requires:
  - 43-09 (audited_head 37b518d6, Image des 43-09-Pushes 655fe197)
  - Release v1.6.2 (Companion-Archiv und Image :1.6.2 als Startpunkt der Proofs)
provides:
  - .github/workflows/rc-version-proof.yml (Dispatch-Nachweis A5/A6)
  - scripts/ci/rc_version_proof.sh (Run-Blöcke, 6 Subkommandos)
  - Branch rc/1.6.3-rc.1 gepusht (47c4ce4e, nur Versionsstellen + testbuild/ gegen den main-Kopf 7725bba8)
  - 43-TESTBUILD.md (vollständig: Proof-Lauf 42565361965, Artefakt-Lauf 42537119924, SHA-256, Aufbewahrung, Installationsweg)
affects:
  - 43-11 (Kommentar an mbozem mit Installationsweg)
  - 43-12 (Owner-Runde, K6)
  - Task 2/3 dieses Plans (Owner-Freigaben, Pushes, Dispatches)
key-files:
  created:
    - .github/workflows/rc-version-proof.yml
    - scripts/ci/rc_version_proof.sh
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-TESTBUILD.md
    - testbuild/findling_backend-1.6.3-rc.1-info.xml (nur auf dem Branch)
  modified:
    - backend/appinfo/info.xml (nur auf dem Branch, 1.6.3-rc.1)
    - php/appinfo/info.xml (nur auf dem Branch, 1.6.3-rc.1)
decisions:
  - "Image-SHA = 655fe197 (Push-Kopf von 43-09) statt eines Vorfahren des audited_head: docker.yml taggt den Push-Kopf, einen Vorfahren-Tag mit leerem backend-Diff gibt es nicht; git diff 37b518d6..655fe197 -- backend ist leer, der backend/-Stand des Images IST der audited_head"
  - "Image-Digest schon jetzt anonym über die Registry-API belegt (sha256:30d56229..., amd64+arm64), kein zusätzlicher docker.yml-Dispatch nötig"
  - "A6-Job tauscht die Companion im Checkout VOR setup-test-nc gegen die Release-1.6.2, damit die Instanz wirklich bei 1.6.2 beginnt und occ upgrade ein echtes Upgrade ist"
  - "Scan-Zeile im A6-Job per SQL mit Begründung im Log: der Crawl braucht einen registrierten Backend-Container, der Job registriert bewusst keinen; die Migration liest nur 'mindestens eine Zeile'"
metrics:
  duration: "rund 1,5 h lokale Arbeit (Task 1) plus Fix-Delta und CI-Begleitung (Task 3)"
  completed: 2026-11-09
  tasks: 3 von 3 (Task 2 Freigaben in 43-FREIGABEN.md, Task 3 abgeschlossen)
  commits: "Task 1: 2; Fix-Delta: 2; Task 3 Doku: 1 (0fbfdfa6, lokal)"
---

# Phase 43 Plan 10: Testbuild 1.6.3-rc.1 und Versionsnachweis Summary

Proof-Workflow rc-version-proof.yml (dispatch only) weist vor der Weitergabe des
Testbuilds nach, dass 1.6.3 > 1.6.3-rc.1 > 1.6.2 auf einer frischen Nextcloud
(stable33/34, Servers eigene version_compare-Stelle per grep belegt) und auf dem
HaRP-Weg des Melders (AppAPI-Update per --info-xml-Raw-URL, Ausgaben wörtlich,
--force-update-Wiederholung bei jeder Weigerung) gilt; Branch rc/1.6.3-rc.1
liegt lokal mit exakt dem Versionsdelta plus Test-info.xml auf das unveränderliche
Image :655fe197.

## Commits

| Branch | Commit | Betreff |
| --- | --- | --- |
| main (lokal, NICHT gepusht) | 3dba38dd206766793f665a8c9be363981a572100 | ci(43-10): a proof of the rc version order on a fresh instance and on HaRP |
| rc/1.6.3-rc.1 (lokal, NIE pushen ohne Freigabe, NIE mergen) | f6c5a6ce0e5378ce0facacac155c919d64f019a2 | chore(43-10): test build 1.6.3-rc.1 for the reporter |

Autor beider Commits: street1983nk <k.cherif@outlook.de>, keine Trailer, kein closes/fixes.

## Was gebaut wurde (Task 1, abgeschlossen)

- **rc-version-proof.yml:** nur `workflow_dispatch` (Eingänge rc_ref, archive_run_id, image_sha), `permissions: contents: read, actions: read`, gepinnte Actions (checkout v7.0.1, repo-weiter Pin), timeout-minutes je Job. Job a6-companion (Matrix stable33/stable34) und Job a5-backend (stable34, HaRP-Daemon, Front-Proxy, Muster deploy-harp.yml). deploy-harp.yml selbst UNVERÄNDERT (36 Bytes unter dem 500-KB-Gate).
- **scripts/ci/rc_version_proof.sh:** set -eo pipefail, kein `${{`, Eingaben nur als Env mit Form-Validierung (RC_REF-Zeichensatz, archive_run_id numerisch, image_sha 40 hex). Subkommandos a6-swap, a6, a5-harp, a5-proxy, a5-register, a5. Signaturprüfung des rc-Archivs gegen das öffentliche Zertifikat inklusive DER-Fingerprint-Abgleich (T-43-29). Job-Summary-Zeilen exakt `A5: ok|failed <grund>` und `A6: ok|failed <grund>`, Exit 1 bei failed. Zeile `Store-Erkennung AppAPI: <datei>:<zeile> nutzt version_compare` für W7.
- **Branch rc/1.6.3-rc.1** ab audited_head 37b518d6: beide info.xml und image-tag auf 1.6.3-rc.1 (Lockstep grün), `testbuild/findling_backend-1.6.3-rc.1-info.xml` mit image-tag 655fe197cc4363e7da2f7c6a7e8000c561f3b31e. Diff-Nachweis: `git diff 37b518d6..rc/1.6.3-rc.1 --name-only` = genau die zwei info.xml plus testbuild/; Inhalts-Diff nur die drei Versionszeilen.
- **43-TESTBUILD.md:** Zweck, D-43-13, Branch-SHA, Image-SHA samt Digest-Beleg, Diff-Beleg, Abschnitte Proof-Lauf, Artefakt-Lauf, Aufbewahrung/Ablauf, SHA-256, Installationsweg für mbozem; alle CI-abhängigen Felder AUSSTEHEND.

## Gates (lokal, alle grün)

- bash -n scripts/ci/rc_version_proof.sh; YAML-Parse des Workflows
- pytest: test_workflow_size, test_workflow_pins, test_workflow_contexts, test_workflow_tag_triggers, test_lockstep_versions (87 passed)
- uv run --no-sync ruff check (grün), ruff format --check (255 Dateien), PYRIGHT_PYTHON_FORCE_VERSION=latest pyright (0/0/0), vulture --min-confidence 80 (leer)
- Plan-Task-1-verify wortgleich gefahren: PASS (inkl. Diff-Filter gegen audited_head aus 43-AUDIT.md)
- Kein Em-Dash/En-Dash in den neuen Dateien, Umlaute nur in deutscher Prosa (43-TESTBUILD.md, SUMMARY)

## Abweichungen vom Plan

**1. [Rule 1] Image-SHA ist der Push-Kopf 655fe197, kein Vorfahre des audited_head**
- **Gefunden in:** Task 1 (Bestimmung des <sha> für die Test-info.xml)
- **Problem:** Der Plan verlangt den "jüngsten Commit <= audited_head" mit grünem docker.yml-Lauf; docker.yml taggt aber GITHUB_SHA = Push-Kopf, und der 43-09-Push trug den Fix 37b518d6 mit Kopf 655fe197. Der letzte Lauf davor (d9f8a65d) liegt VOR dem Fix, sein Image trägt den audited-Stand nicht.
- **Lösung:** 655fe197 gewählt (Nachfahre, `git diff --stat 37b518d6 655fe197 -- backend` leer, Lauf 42523105680 grün); das must_have "backend/-Stand gleich audited_head" ist damit wörtlich erfüllt. Beleg in 43-TESTBUILD.md.
**2. Kein Platzhalter in der Test-info.xml nötig:** Das Image existiert bereits (Digest sha256:30d56229b7abebee1e93e1c25a33b1811a3b7a44a0ba35b88defc19a9032a58f, amd64+arm64, anonym über die ghcr-API verifiziert), daher trägt die Test-info.xml den echten SHA statt des <sha>-Platzhalters; kein zusätzlicher docker.yml-Dispatch erforderlich.

Sonst exakt nach Plan.

## Task 2 und Task 3 (abgeschlossen, 2026-11-09)

- **Task 2 (checkpoint:decision, Owner):** alle vier Freigaben mit "Entscheid: ja" in 43-FREIGABEN.md (Push main, Push rc, Dispatch release, Dispatch proof; dazu die Freigaben der Harness-Fixes und Wiederholungen).
- **Task 3 (ERGEBNIS):**
  - Branch rc/1.6.3-rc.1 gepusht, Kopf `47c4ce4e` (Neuaufsatz auf dem main-Kopf 7725bba8 nach dem Fix-Delta; Diff weiterhin genau drei Versionszeilen plus testbuild/).
  - Archiv-Lauf release.yml 42537119924 (create_release=false, grün): Artefakt `store-release`, findling.tar.gz 692 014 Bytes, SHA-256 `fa9c38745ec79dd21411d17aaa4bb46455987893f4ab13d2f8f3204861c333be`, `Aufbewahrung: 30 Tage, Ablauf 2026-12-08` (expires_at 2026-12-08T23:51:31Z).
  - Proof-Lauf rc-version-proof.yml 42565361965 GRÜN: `A5: ok` (HaRP, Raw-URL-Update 1.6.2 zu 1.6.3-rc.1 und Store-förmig 1.6.3 darüber, beides ohne --force-update, Image :655fe197 belegt, Heartbeat 200) und `A6: ok` auf stable33 UND stable34 (occ upgrade auf 1.6.3-rc.1, Migration 001603Date20261108000000, Hinweis-Flag 1, Verified OK). `Store-Erkennung AppAPI: apps/app_api/lib/Fetcher/ExAppFetcher.php:124 nutzt version_compare` (W7). Drei rote Vorläufer (42537244567 nginx-/exapps-401-Sonde, 42538879801 gh -d statt --dir, 42551978920 viewer/shipped.json), alle Harness; Einzeiler in 43-TESTBUILD.md, Abschnitt "Proof-Historie".
  - Alle Belege wörtlich in 43-TESTBUILD.md; Installationsweg für mbozem belegt (Kommentar entsteht in 43-11, nur mit Owner-Freigabe).
  - Plan-Task-3-verify wortgleich gefahren: PASS.

## Fix-Delta nach dem Audit (09.11.2026)

Die rc-Branch-Läufe 42530680761 (HaRP) und 42530680760 (Python gates) waren
rot; das Risiko "Rot dort wäre ein Befund" unten ist damit eingetreten. Beide
Ursachen lagen im HARNESS, kein Produktcode ist berührt, audited_head 37b518d6
gilt unverändert (Details in 43-AUDIT.md, Abschnitt "Fix-Delta nach dem
Audit").

| Branch | Commit | Betreff |
| --- | --- | --- |
| main (lokal, NICHT gepusht) | 9f99df1f | fix(43-10): the F2 gate reads a prerelease version and orders it below its release |
| main (lokal, NICHT gepusht) | bcab9012 | ci(43-10): assurance 18 waits bounded for the backfill line |

- **Fix 1 (Lauf 42530680761):** Zusicherung 18 in deploy-harp.yml grepte das
  Container-Log genau einmal und verlor das Rennen gegen die Worker-Kadenz
  (grüner Lauf bei Sekunde 62, roter bei Sekunde 61). Jetzt Poll alle 5 s,
  Deckel 240 s, bei Ablauf der bestehende ::error::. Platz dafür: Schritt
  "Store upgrade 1" nach Muster 41-08 in
  scripts/ci/upgrade_from_release_assets.sh ausgelagert; deploy-harp.yml
  505990 Bytes (vorher 511964, Gate 512000), MOVED_STEPS nachgeführt,
  Wächter test_the_backfill_assurance_waits_bounded_instead_of_looking_once
  erst rot gesehen.
- **Fix 2 (Lauf 42530680760):** das F2-Gate in test_phase36_audit.py las
  `[0-9.]+` und traf 1.6.3-rc.1 nicht (version is None, AssertionError).
  Jetzt optionales Prerelease-Suffix und _version() mit
  version_compare-Ordnung (1.6.2 <= 1.6.3-rc.1 < 1.6.3); Selbsttest mit dem
  rc-Beispiel erst rot gesehen. test_lockstep_versions brauchte nichts: sein
  _SEMVER trägt den Prerelease-Teil des Store-Schemas bereits.
- **rc/1.6.3-rc.1 neu aufgesetzt:** alter Stand f6c5a6ce verworfen, Branch
  auf den neuen main-Kopf gesetzt (der Commit dieses Nachtrags), wieder exakt
  drei Versionsstellen auf 1.6.3-rc.1 plus
  testbuild/findling_backend-1.6.3-rc.1-info.xml (Inhalt vom alten Branch,
  image-tag 655fe197cc4363e7da2f7c6a7e8000c561f3b31e). Diff gegen den neuen
  main-Kopf: nur die drei Versionszeilen und testbuild/. Commit-SHA im
  Koordinator-Bericht; NICHT gepusht.
- **Gates am neuen Kopf (lokal, alle grün):** ruff check, ruff format
  --check, pyright (latest) 0 errors, vulture 80; pytest
  test_phase36_audit, test_workflow_size/pins/contexts/tag_triggers,
  test_lockstep_versions, test_upgrade_seed_steps und die übrigen
  Workflow-Wächter; bash -n für das neue Skript, YAML-Parse deploy-harp.yml.
  Baumhash-Journal unberührt (Rezept hasht nur backend/src/findling und
  php/).

## Risiken

- A5/A6 sind inhaltlich offen bis zum Proof-Lauf (LOW-Quelle 43-RESEARCH.md: version_compare-Verhalten bei rc-Versionen in Nextcloud/AppAPI dort nicht geprüft; die PHP-Semantik spricht dafür, der Lauf beweist es).
- Der Branch-Push startet die Test-Workflows auf dem Branch (python/php/integration); keine Versions-Pins in den Tests gefunden, Rot dort wäre ein Befund, kein Blocker für main.
- occ app_api:app:update ohne --force-update könnte den rc-Schritt verweigern; das Skript wiederholt mit --force-update und dokumentiert beide Ausgaben, der Installationsweg für mbozem übernimmt das Ergebnis.

## Self-Check: PASSED

- .github/workflows/rc-version-proof.yml: FOUND
- scripts/ci/rc_version_proof.sh: FOUND
- 43-TESTBUILD.md: FOUND, keine AUSSTEHEND-Felder mehr
- Commit 0fbfdfa6 (main, Task-3-Doku): FOUND; rc/1.6.3-rc.1 bei origin: 47c4ce4e (git ls-remote exit 0)
- rc-Diff gegen 7725bba8: nur info.xml-Versionszeilen und testbuild/
- Task-3-verify des Plans: PASS (A5/A6-Zeilen, sha256, Aufbewahrungszeile, Store-Erkennung, Remote-Branch)
