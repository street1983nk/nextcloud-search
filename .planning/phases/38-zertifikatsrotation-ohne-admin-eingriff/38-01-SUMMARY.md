---
phase: 38-zertifikatsrotation-ohne-admin-eingriff
plan: 01
subsystem: harp-tunnel
tags: [harp, frpc, x509, mtls, watcher, shellcheck, ZERT-01, D-37-09]
requires: [38-RESEARCH.md, D-37-09]
provides: [harp_connect.sh-Waechter, test_harp_connect_supervisor.py, shellcheck-Gate python.yml, Anker docs/harp-tunnel.md#repair-without-re-registering]
affects: [38-02 (Doku-Seite mit dem Anker, deploy-harp-Rotationsprobe), phase-40-release]
tech-stack:
  added: []
  patterns: [frpc im Hintergrund nach FIFO plus read -t auf fd 3, Fingerabdruck per sha256sum nur verglichen, Stub-frpc mit Startprotokoll und TERM-Trap fuer Shell-Tests]
key-files:
  created:
    - backend/tests/test_harp_connect_supervisor.py
  modified:
    - backend/docker/harp_connect.sh
    - backend/docker/init.sh
    - .github/workflows/python.yml
decisions:
  - "Neustart immer bei geaenderten und zweimal stabilen Dateien (auch mTLS nach mTLS), gedeckelt per MIN_GAP 60 s und CAP 6 je Fenster (3600 s), wie die Research empfiehlt"
  - "Abhilfe-Zeile nur bei unveraendertem Fingerabdruck gegenueber dem laufenden frpc; Meldeplan 0,300,900,3600 s, danach stuendlich, Neustart des Plans erst nach 'login to server success'"
  - "Fingerabdruck = sha256sum der sha256sum-Liste der lesbaren Dateien, damit fehlende und leere Datei verschieden sind"
  - "shellcheck-disable SC2317,SC2329 je eine Kommentarzeile vor den Trap-Funktionen in init.sh und harp_connect.sh (0.9 meldet SC2317, ab 0.11 SC2329); keine Codeaenderung in init.sh"
metrics:
  duration: "ca. 30 min"
  completed: 2026-10-28
  tasks: 2
  files: 4
---

# Phase 38 Plan 01: Tunnel-Waechter in harp_connect.sh Summary

harp_connect.sh ist unter HaRP kein exec mehr, sondern ein bash-Waechter vor frpc: Ausgabe ueber eine FIFO (mkfifo -m 600) durchgereicht, x509 bei unveraenderten Dateien ratenbegrenzt mit Abhilfe und Doku-Anker gemeldet (nie Neustart), geaenderte und stabile Dateien unter /certs/frp per genau einem gedeckelten frpc-Neustart in mTLS uebernommen, nie Abwaertswechsel, Exit-Vertrag mit init.sh erweitert (73 bei unschreibbarem Run-Verzeichnis, nie 0 nach frpc-Ende, 0 nach TERM).

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Waechtertests mit Stub-frpc (RED) | 13fbe79b |
| 2 | Waechter in harp_connect.sh, init.sh-Kommentar, shellcheck-Gate (GREEN) | 4030301a |

## RED-Nachweis (gegen das alte exec-Skript)

Unter Windows ist das Modul geskippt, darum hier ueber den Ist-Code von 82617298 begruendet: das alte Skript ignoriert FINDLING_FRPC_BIN und macht `exec /usr/local/bin/frpc`, das es ausserhalb des Images nicht gibt (Exit 127). Damit rot: (a) x509 ohne Neustart, (b) Moduswechsel, (c) einmaliger Tausch, (d)/(e) Deckel und Positivkontrolle, (f) kein Abwaertswechsel, (g) exit0 -> 1 und exit3 -> 3 (Stub nie gestartet, 127), (h) TERM, (i) Heilung, (j) FIFO-Modus (keine FIFO), (l)/(l2) Meldeplan, (m)/(m2) Deckelfenster, (n) Exit 73 (altes Skript: set -e plus mkdir-Fehler gibt 1), ungueltige Zeitknoepfe (alte Fassung prueft keine, Exit 127 statt 78). Gruen auch gegen das alte Skript: ohne HP_SHARED_KEY (0), fehlende Adresse (78), Port "80a" (78), bash -n.

## Verifikation

- Python-Gates in backend/: ruff check . gruen, ruff format --check . gruen (235 Dateien), pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest) 0 Fehler, vulture --min-confidence 80 ohne Funde; pytest tests/test_harp_connect_supervisor.py unter Windows: 25 skipped mit Grund in -rs.
- bash -n beider Skripte gruen; shellcheck 0.9.0 (Ubuntu-24.04-apt-Stand), 0.10.0 und 0.11.0 ueber `uvx --from shellcheck-py` beide Skripte Exit 0.
- WSL-Verhaltensbeweis: NICHT moeglich. Einzige WSL-Distribution ist `docker-desktop` (kein bash, kein Python; `wsl -e bash` scheitert mit "execvpe(bash) failed"). Ersatz: dieselbe Testdatei als Kopie im Scratchpad mit Git Bash 5.3 (Cygwin) als BASH unter Windows-Python: **22 passed, 2 failed, 1 skipped in 107 s**. Die zwei Fehlschlaege sind Plattform-Artefakte, keine Waechterfehler: Python `send_signal(SIGTERM)` ist unter Windows TerminateProcess (Exit 1 statt Trap), und `os.stat` kennt unter NTFS keine POSIX-Modi (0o666). Beides nativ in Git Bash nachgeprueft: `kill -TERM` an das Skript -> Exit 0 in unter 1 s, Stub-Protokoll "start, term"; FIFO `prw-------`. frpc.toml zeigt unter Git Bash 644, weil der noacl-Mount chmod nicht abbildet; unter Linux setzt chmod 600 wie bisher. shellcheck-Fall dort mangels Binary geskippt.
- CI: offen, der Push erfolgt durch den Koordinator. Erwartet im Job gates von python.yml: Schritt "Shell check of the tunnel scripts" gruen, test_harp_connect_supervisor.py in "Tests" nicht unter SKIPPED. Lauf-ID traegt der Koordinator nach.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] shellcheck-Infomeldungen zu Trap-Funktionen**
- **Found during:** Task 2
- **Issue:** shellcheck meldet die nur per trap aufgerufenen Funktionen forward_stop (init.sh) und on_stop (harp_connect.sh) als nie aufgerufen bzw. unerreichbar (SC2317 in 0.9, SC2329 ab 0.11); der neue CI-Schritt waere rot.
- **Fix:** je eine Kommentarzeile `# shellcheck disable=SC2317,SC2329 # invoked through the trap below`. In init.sh ist das nach Checker-Befund 6 ausdruecklich erlaubt (nur begruendete disable-Kommentarzeilen), keine Logikaenderung; der Diff-Check auf Nicht-Kommentarzeilen in init.sh ist leer.
- **Commit:** 4030301a

**2. [Rule 1 - Laufzeit] Flatter-Faelle (d)/(e) mit 12 s statt 15 s**
- **Found during:** Task 1
- **Issue:** Die Modulsumme liegt ueber dem Ziel von 90 s.
- **Fix:** (d) und (e) flattern 12 s (vier Wechsel bei 2,5 s, reicht fuer CAP 2 plus Deckelzeile und fuer mindestens 3 Neustarts in der Positivkontrolle). Trotzdem gemessen ca. 107 s unter Git Bash (die beiden 16-s-Fenstertests (m)/(m2) sind die groessten Posten); Laufzeit in CI pruefen, Ziel 90 s ist damit knapp verfehlt.

**3. Ungueltige Liste prueft zusaetzlich die aufsteigende Reihenfolge** (Plan: "aufsteigende ganze Sekunden"); bei Verstoss dieselbe "which is not a list of whole seconds"-Zeile, Exit 78. Werte ueber 9 Stellen ergeben ebenfalls Exit 78, damit die bash-Arithmetik nicht ueberlaeuft.

## Bekannte Grenze

Haelt der Deckel einen Neustart zurueck, waehrend die neuen Dateien weiter x509 liefern, bleibt der Fingerabdruck ungleich dem des laufenden frpc und die Abhilfe-Zeile schweigt bis zum Fensterende (dann folgt der Neustart, danach meldet sie wieder). Folgt dem Plan-Wortlaut "bei x509 und unveraendertem Fingerabdruck"; frpc liest die Dateien ohnehin pro Dial neu.

## Annahme fuer 38-02

A2 der Research (sha256sum und mkfifo in der Runtime-Stage) ist lokal nicht pruefbar (kein Docker); coreutils ist in python:3.13-slim-trixie essenziell. Die deploy-harp-Probe in 38-02 belegt es.

## Threat Flags

Keine neuen Flaechen ausserhalb des Threat-Registers (T-38-01 bis T-38-07 umgesetzt bzw. akzeptiert wie geplant).

## Self-Check: PASSED

- FOUND: backend/tests/test_harp_connect_supervisor.py, backend/docker/harp_connect.sh, backend/docker/init.sh, .github/workflows/python.yml
- FOUND: 13fbe79b, 4030301a
