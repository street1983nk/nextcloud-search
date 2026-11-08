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
  - Branch rc/1.6.3-rc.1 lokal (f6c5a6ce, nur Versionsstellen + testbuild/)
  - 43-TESTBUILD.md (Image-Digest belegt, CI-Felder AUSSTEHEND)
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
  duration: "rund 1,5 h lokale Arbeit"
  completed: 2026-11-08
  tasks: 1 von 3 (Task 2 Checkpoint:decision und Task 3 Push/Dispatch stehen aus)
  commits: 2 (1x main, 1x Branch)
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

## Offen (Task 2 und Task 3, über den Koordinator)

- **Task 2 (checkpoint:decision, Owner):** Freigaben für (1) Push main, (2) Push rc/1.6.3-rc.1, (3) Dispatch release.yml auf dem Branch mit create_release=false, (4) Dispatch rc-version-proof.yml. 43-FREIGABEN.md ist absichtlich NICHT beschrieben; Zeilen-Wortlaute siehe Koordinator-Bericht.
- **Task 3 (nach Freigaben):** git pull --rebase, Push main, Security-Workflow grün; Push Branch; release.yml-Dispatch (liefert archive_run_id, Bytezahl, Verified OK, SHA-256, expires_at für `Aufbewahrung: 30 Tage, Ablauf <JJJJ-MM-TT>`); Proof-Dispatch mit image_sha 655fe197...; A5/A6 und Store-Erkennung wörtlich in 43-TESTBUILD.md; bei failed: Abschnitt "Befund und Alternativen", Stopp, Entscheid in 43-11.

## Risiken

- A5/A6 sind inhaltlich offen bis zum Proof-Lauf (LOW-Quelle 43-RESEARCH.md: version_compare-Verhalten bei rc-Versionen in Nextcloud/AppAPI dort nicht geprüft; die PHP-Semantik spricht dafür, der Lauf beweist es).
- Der Branch-Push startet die Test-Workflows auf dem Branch (python/php/integration); keine Versions-Pins in den Tests gefunden, Rot dort wäre ein Befund, kein Blocker für main.
- occ app_api:app:update ohne --force-update könnte den rc-Schritt verweigern; das Skript wiederholt mit --force-update und dokumentiert beide Ausgaben, der Installationsweg für mbozem übernimmt das Ergebnis.

## Self-Check: PASSED

- .github/workflows/rc-version-proof.yml: FOUND
- scripts/ci/rc_version_proof.sh: FOUND
- 43-TESTBUILD.md: FOUND
- Commit 3dba38dd (main): FOUND; Commit f6c5a6ce (rc/1.6.3-rc.1): FOUND
- rc-Diff gegen audited_head: nur info.xml-Versionszeilen und testbuild/
