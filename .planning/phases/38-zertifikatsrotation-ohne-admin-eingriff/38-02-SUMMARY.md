---
phase: 38-zertifikatsrotation-ohne-admin-eingriff
plan: 02
subsystem: harp-tunnel
tags: [harp, frpc, x509, mtls, ci-probe, deploy-harp, docs, ZERT-01, ZERT-02, D-37-09]
requires: [38-01 (Waechter, Abhilfe-Zeile mit Anker), 38-RESEARCH.md]
provides: [deploy-harp-Schritt "Certificate rotation, a reissued HaRP CA heals after the three files are copied in", backend/tests/test_cert_rotation_steps.py, docs/harp-tunnel.md, Entwurf Issue-#33-Antwort, Entwurf HaRP-Upstream-Vorschlag]
affects: [phase-40-release (Issue-#33-Antwort vor "Closes #33", Upstream-Vorschlag beim Owner)]
tech-stack:
  added: []
  patterns: [echte CA-Neuausstellung in CI per rm -rf /certs/frp plus HaRP-Neustart, Totfenster ueber Dial-Zaehlung statt x509-Zaehlung, Logs erst in Datei und dann grep -q unter pipefail]
key-files:
  created:
    - backend/tests/test_cert_rotation_steps.py
    - docs/harp-tunnel.md
    - .planning/phases/38-zertifikatsrotation-ohne-admin-eingriff/38-ENTWURF-ISSUE-33.md
    - .planning/phases/38-zertifikatsrotation-ohne-admin-eingriff/38-ENTWURF-HARP-UPSTREAM.md
  modified:
    - .github/workflows/deploy-harp.yml
decisions:
  - "Totfenster der Positivkontrolle: mindestens 1 x509-Zeile, mindestens 3 fehlgeschlagene Dials und 0 'login to server success' seit der Neuausstellung (statt mindestens 2 x509-Zeilen); auf arm64 sagte nur jeder neunte Dial x509, der Rest 'session shutdown'"
  - "Job-Deckel 45 min bleibt: laengstes Bein der letzten gruenen Laeufe 31 min 50 s, mit dem neuen Schritt 32 min 31 s"
  - "Doku Englisch in docs/harp-tunnel.md, Kopierbefehl in exakt der Form der CI-Probe"
metrics:
  duration: "ca. 130 min inkl. ca. 90 min CI"
  completed: 2026-10-28
  tasks: 3
  files: 5
---

# Phase 38 Plan 02: CI-Rotationsprobe, Tunnel-Doku und Owner-Entwuerfe Summary

Eine unbedingte deploy-harp-Probe stellt die HaRP-CA "harp.nc" auf allen vier Beinen echt neu aus, belegt den toten Tunnel ohne neue Dateien (x509, leere Kanariensuche, Abhilfe-Zeile genau einmal, kein frpc- und kein Container-Neustart) und die Heilung nach dem dokumentierten Kopierbefehl in 8 bis 19 s, ohne Re-Register und ohne Container-Neustart; dazu docs/harp-tunnel.md und zwei Entwuerfe fuer den Owner.

## Tasks

| Task | Name | Commit (main) |
|------|------|---------------|
| 1 | Vertragstest test_cert_rotation_steps.py (RED) | 831e9351 |
| 2 | CI-Probe in deploy-harp.yml | 701e7003, Fixes e8f1d236, 76cabf39 |
| 3 | docs/harp-tunnel.md und zwei Entwuerfe | 4889197f, Lauf-ID cf13ee09 |

## RED-Nachweis

Lokal vor Task 2: 11 failed, 20 passed, Exit 1. Rot: alle sieben Schritt-Tests (Schritt fehlt) und die vier Doku-Tests (Datei fehlt). Gruen schon vorher: beide Anker-Tests gegen harp_connect.sh sowie alle Selbsttests. Nach Task 2 mit -k "not doc": 20 passed; nach Task 3 komplett: 31 passed.

## CI-Beweis

- Wegwerf-Branch gsd/38-rotation-probe, drei Laeufe:
  - 40693521161 rot auf allen Beinen: dash druckt bei `command -v a b c` nur den ersten Namen (Vorbedingung 1 von 3).
  - 40695220173 rot auf stable34 amd64 und arm64, gruen auf stable33/35: (a) `docker logs | grep -qF` unter pipefail meldet eine gefundene Zeile als fehlend (SIGPIPE); (b) arm64 lieferte in 180 s nur 1 x509-Zeile bei 9 fehlgeschlagenen Dials.
  - **40696292903 gruen auf allen vier Beinen** (deploy-harp komplett, dazu Python gates 40696292896, Integration 40696292847, Resilience 40696292895 gruen).
- Messwerte aus 40696292903 (alle: HTTP 200 mit `entries: []` im Totfenster, Abhilfe-Zeile genau einmal, kein frpc-Neustart im Totfenster, RestartCount und StartedAt unveraendert, app_api:app:list unveraendert):

| Bein | CA vorher -> nachher | x509 / fehlgeschlagene Dials | Heildauer |
|------|----------------------|------------------------------|-----------|
| stable34 amd64 | 1123ebd895ee -> b716eba2940d | 1 / 6 | 19 s |
| stable35 amd64 | bd9f249f86a1 -> f8ff9d20528f | 1 / 9 | 18 s |
| stable33 amd64 | 39a2e92916ab -> 2506481d550c | 1 / 3 | 8 s |
| stable34 arm64 | ede3f807a9df -> 025cd8448664 | 1 / 3 | 8 s |

- Gelandet per Rebase auf origin/main (die zwei Fremd-Commits docs(39) und fix(tests) des Parallelstrangs wurden als Duplikate uebersprungen) und Fast-Forward; main-Lauf deploy-harp 40704387898 auf cf13ee09 beim Abschluss noch in Arbeit. Inhalt von deploy-harp.yml und Tests identisch mit dem gruenen Branch-Stand (git diff 2aa19a29 HEAD nur die Lauf-ID-Zeile in der Doku). Branch lokal und remote geloescht.
- Zeitbudget: laengstes Bein vorher 31 min 50 s (40678142925, stable34 amd64), mit Probe 32 min 31 s; Deckel 45 min unveraendert.

## Verifikation

- Lokal: test_cert_rotation_steps.py 31 passed; ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture ohne Funde; shellcheck (shellcheck-py) ueber den extrahierten run-Block Exit 0; YAML per pyyaml geparst, Schrittreihenfolge bestaetigt.
- Lokaler Volltest der Backend-Suite (ohne neue Datei): 1051 passed, 1 failed (test_exclusion_driver::test_the_prefixes_of_1_4_2_answer_exactly_as_before, subprocess-TimeoutExpired unter Windows, nicht beruehrt von diesem Plan; in CI Python gates gruen).
- Akzeptanz Task 3: 7 Ueberschriften, Repair-Ueberschrift genau einmal, Kopierschnipsel, `--rm-data`, `#6254`, `findling:diagnose`, `backend answered`, `FINDLING_HARP_PLAINTEXT` vorhanden; Antworttext 6 Saetze; `grep -ci closes` = 1 (Kopfzeile); `_install_frp_certificates` und `#107` im Upstream-Entwurf; keine U+2013/U+2014; `git log --all --grep='Closes #33'` leer; kein gh issue comment/create, kein gh pr create.
- Desktop-Kopien: C:/Users/Student/Desktop/Findling_Issue33_Antwort_ENTWURF.md, C:/Users/Student/Desktop/Findling_HaRP_Upstream_Vorschlag_ENTWURF.md.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] command -v mit mehreren Namen unter dash**
- **Found during:** Task 2, Lauf 40693521161
- **Fix:** Schleife, ein `command -v` je Werkzeug. **Commit:** e8f1d236

**2. [Rule 1 - Bug] grep -q unter pipefail**
- **Found during:** Task 2, Lauf 40695220173 (stable34 amd64)
- **Fix:** Container-Log erst nach rotation-start.log, dann grep; HaRP-Dateiliste per Here-String. **Commit:** 76cabf39

**3. [Rule 1 - Messfehler] Totfenster "mindestens 2 x509-Zeilen" nicht tragfaehig**
- **Found during:** Task 2, Lauf 40695220173 (arm64: 1 x509 in 9 Dials, die uebrigen "session shutdown"; welche Seite zuerst abbricht ist ein Rennen)
- **Fix:** tot = mindestens 1 x509-Zeile UND mindestens 3 Zeilen "connect to server error:" UND 0 "login to server success" seit der Neuausstellung, Fenster weiterhin 90 x 2 s; Begruendung mit Lauf-ID im Kommentar. Abweichung vom Wortlaut der must_haves-Wahrheit 2 ("mindestens zwei 'x509: '-Zeilen"); die Aussage "ohne neue Dateien bleibt der Tunnel tot" ist durch das Login-Verbot strenger belegt als vorher. **Commit:** 76cabf39

**4. Kleinigkeiten:** Commit-Typ `ci` statt `feat` fuer den Workflow-Schritt; zusaetzliche Pruefung, dass client.key nach dem Kopieren fuer den App-Nutzer lesbar ist; `set -o pipefail` im run-Block. Doku "Limits": Wechsel aus FINDLING_HARP_PLAINTEXT=1 auf mTLS geschieht mit dem frpc-Neustart des Waechters fuer die neuen Dateien (Code von 38-01), nicht erst bei einem Waechter-Neustart wie im Plantext.

## Hinweis Arbeitskopie

Ein Parallelstrang hat waehrend der Ausfuehrung in derselben Arbeitskopie zwei Commits auf den Probe-Branch gesetzt (docs(39), fix(tests)); beide hat der Koordinator separat auf main gebracht, sie wurden beim Rebase als Duplikate verworfen. Ein lokaler Pytest-Lauf (test_phase34_audit plus ruff ueber den ganzen Baum) blieb ohne CPU-Last haengen; die Prozesse konnten nicht beendet werden (Freigabe verweigert), sie stoeren nichts Committetes.

## Known Stubs

Keine.

## Threat Flags

Keine neuen Flaechen. T-38-08 bis T-38-12 umgesetzt: Shared Key maskiert, nur gekuerzter CA-Hash, client.key nie gehasht ausgegeben; umask 077, temp plus mv -f, kein docker cp; Positivkontrolle vor der Reparatur; nur Entwuerfe, kein gh-Schreibaufruf; timeout-minutes 10 am Schritt.

## Self-Check: PASSED

- FOUND: backend/tests/test_cert_rotation_steps.py, docs/harp-tunnel.md, 38-ENTWURF-ISSUE-33.md, 38-ENTWURF-HARP-UPSTREAM.md, beide Desktop-Kopien
- FOUND: 831e9351, 701e7003, 4889197f, e8f1d236, 76cabf39, cf13ee09 auf main
