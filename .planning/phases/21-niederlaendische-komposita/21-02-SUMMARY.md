---
phase: 21-niederlaendische-komposita
plan: 02
subsystem: image
tags: [docker, wdutch, lizenz, ci-gate, third-party]
requires: []
provides:
  - "/usr/share/dict/dutch im Abbild (wdutch=1:2.20.19+1-3)"
  - "/usr/local/share/findling/COPYING.wdutch (0444)"
  - "CI-Gate fuer die niederlaendische Liste am gepushten Abbild"
affects: [21-05]
tech-stack:
  added: ["Debian-Paket wdutch 1:2.20.19+1-3 (OpenTaal, CC-BY-3.0)"]
  patterns: ["gleiches fail-closed-Muster wie wngerman"]
key-files:
  created: []
  modified:
    - backend/Dockerfile
    - backend/tests/test_upgrade_compatibility.py
    - .github/workflows/docker.yml
    - THIRD-PARTY.md
decisions:
  - "wdutch mit Epoche gepinnt, DEBIAN_FRONTEND=noninteractive nur im wdutch-RUN"
  - "CI-Pruefzeile genau 'License: CC-BY-3.0' (im Container gelesen, Zeile 17 der copyright-Datei)"
metrics:
  duration: "ca. 15 min"
  completed: 2026-09-25
---

# Phase 21 Plan 02: Niederländische Wortliste im Abbild Summary

wdutch=1:2.20.19+1-3 gepinnt im Runtime-Stage, fail closed auf Liste und Lizenztext, CC-BY-3.0-Text als COPYING.wdutch (0444), CI-Gate mit vier Prüfungen und THIRD-PARTY-Abschnitt mit OpenTaal-Namensnennung.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | wdutch ins Abbild, fail closed, mit Lizenztext | 948f94f | backend/Dockerfile, backend/tests/test_upgrade_compatibility.py |
| 2 | CI-Gate am gepushten Abbild und THIRD-PARTY.md | a6af39b | .github/workflows/docker.yml, THIRD-PARTY.md |

## Messung im Wegwerf-Container (python:3.13-slim-trixie, 25.09.2026)

Exakt die RUN-Zeile des Dockerfiles, danach:

```
1:2.20.19+1-3
 413288 5096240 /usr/share/dict/dutch
2e5128e8e7f9a5bdfc427c784c839986b0df1386cc53aef90ed2df71644f3987  /usr/share/dict/dutch
444
21777 /usr/local/share/findling/COPYING.wdutch
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: dutch
Upstream-Contact: OpenTaal <info@opentaal.org>
11:License: BSD-3-Clause
17:License: CC-BY-3.0
21:License: BSD-3-Clause
...
66:License: CC-BY-3.0
13:Files: wordlist/*
```

Alle Werte decken sich mit der Research (Zeilen, Bytes, SHA-256, 21777 Byte copyright). Die Lizenzzeile `License: CC-BY-3.0` steht genau so in der Datei und wird von docker.yml geprüft.

## Verifikation

- `pytest tests/test_upgrade_compatibility.py`: 12 passed (neu: `test_the_dutch_word_list_is_held_through_its_debian_pin`)
- Tests, die THIRD-PARTY.md oder docker.yml lesen (measurement_scripts, lockstep_versions, extract_documents, upgrade_compatibility): 470 passed
- docker.yml bleibt gültiges YAML, Schrittname unverändert
- THIRD-PARTY.md: alle Pflichtbegriffe vorhanden, keine U+2013/U+2014
- Nichts unter backend/src/findling oder php/ berührt, Baumhash-Ratsche unberührt

## Deviations from Plan

Keine inhaltlichen. Anmerkung: Die neuen Fehlermeldungen in docker.yml nutzen wie im Plan verlangt `::error::`; die bestehenden wngerman-Meldungen im selben Schritt sind schlichte `echo`-Zeilen und blieben unverändert.

## Threat Flags

Keine neue Angriffsfläche über das Threat-Register hinaus (T-21-SC, T-21-02-01 bis -03 umgesetzt: Pin mit Epoche, Pin-Test, test -s plus 0444 plus CI-Lizenzprüfung, noninteractive).

## Self-Check: PASSED

- backend/Dockerfile enthält `wdutch=1:2.20.19+1-3` genau einmal, `COPYING.wdutch` und `DEBIAN_FRONTEND=noninteractive` im wdutch-RUN
- Commits 948f94f und a6af39b vorhanden
