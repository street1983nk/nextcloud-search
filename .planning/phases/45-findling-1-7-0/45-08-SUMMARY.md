---
phase: 45-findling-1-7-0
plan: 08
subsystem: release (info.xml beider Apps, Update-Probe, deploy-harp, CHANGELOG DE/EN/FR)
tags: [rel-07, kat-03, version, changelog, owner-freigabe]
requires: [45-07]
provides:
  - "findling und findling_backend tragen 1.7.0 (zwei version, ein image-tag), Doku-Links auf blob/v1.7.0"
  - "Update-Probe 'Store update in one process' startet auch aus v1.6.4 und v1.6.5"
  - "CHANGELOG [1.7.0] in EN/DE/FR mit #45, #56, #57"
  - "Zwei Owner-Freigabezeilen (Version, Changelog) in 45-FREIGABEN.md"
affects: [45-09, 45-11, 45-14]
tech-stack:
  added: []
  patterns: ["Bump-Muster 43-08 ohne Migration", "je Release-Schritt eine eigene Owner-Freigabezeile"]
key-files:
  created:
    - .planning/phases/45-findling-1-7-0/45-08-SUMMARY.md
  modified:
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - scripts/ci/update_in_process_proof.sh
    - .github/workflows/deploy-harp.yml
    - CHANGELOG.md
    - CHANGELOG.de.md
    - CHANGELOG.fr.md
    - .planning/phases/45-findling-1-7-0/45-FREIGABEN.md
key-decisions:
  - "Owner-Antwort A (2026-11-22 05:01 UTC): Version 1.7.0 ja, CHANGELOG 1.7.0 ja"
  - "Datumsregel: Liegt der Tag später als 2026-11-22, passt 45-14 das Datum von [1.7.0] in CHANGELOG.md, CHANGELOG.de.md und CHANGELOG.fr.md auf das Tag-Datum an (von Antwort A gedeckt)"
  - "UPGRADE_FROM_TAG v1.5.0 in deploy-harp.yml bleibt (langer Upgrade-Weg)"
requirements-completed: [KAT-03]
metrics:
  duration: "ca. 45 min ohne Wartezeit auf die Freigaben"
  completed: 2026-11-22
---

# Phase 45 Plan 08: Version und CHANGELOG 1.7.0 Summary

Beide Apps auf 1.7.0 (Version, Image-Tag, Doku-Links), Update-Probe ab v1.6.4/v1.6.5, CHANGELOG 1.7.0 dreisprachig; Version und CHANGELOG je mit eigener Owner-Freigabe abgenommen, alles lokal.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Bump 1.7.0, Update-Probe ab 1.6.5, CHANGELOG-Entwurf, STOPP-Prüfung | 93996a4b (Version), 53a11d81 (CHANGELOG drei Sprachen) |
| - | STATE am Checkpoint | cea12573 |
| 2 | Owner-Freigabe Version 1.7.0 | efd0deb3 (gemeinsam mit Task 3) |
| 3 | Owner-Freigabe CHANGELOG 1.7.0 | efd0deb3 |

## Freigaben

```
Freigabe Version 45-08: "A" (2026-11-22 05:01, Claude-Code-Chat) Entscheid: ja
Freigabe Changelog 45-08: "A" (2026-11-22 05:01, Claude-Code-Chat) Entscheid: ja
```

Zeit in UTC. Antwort A deckt auch die Datumsregel.

## Datumsregel für 45-14 (Tag)

CHANGELOG.md, CHANGELOG.de.md und CHANGELOG.fr.md tragen `## [1.7.0] - 2026-11-22`. Wird der Tag v1.7.0 an einem späteren Tag gesetzt, passt 45-14 vor dem Tag das Datum in allen drei Dateien auf das Tag-Datum an (test_changelog_translations.py danach grün). Diese Anpassung ist von der Freigabe A gedeckt, braucht also keine neue Changelog-Freigabe.

## STOPP-Prüfung (wörtlich)

```
$ git diff --stat v1.6.5..HEAD -- php/lib/Migration
(leer)
$ git diff --stat v1.6.5..HEAD -- backend/src/findling/store/schema.sql backend/src/findling/store/vectors.sql backend/src/findling/index/schema.py
(leer)
```

Keine Migration, keine Schemaänderung seit v1.6.5.

## Verifikation

- Freigabezeilen Version und Changelog passen auf die Regex der Plan-verify
- `uv run --no-sync python -m pytest -q tests/test_changelog_translations.py tests/test_lockstep_versions.py tests/test_store_metadata.py tests/test_upgrade_seed_steps.py`: 290 passed
- Keine Gedankenstriche in 45-FREIGABEN.md; CHANGELOG ohne closes/fixes-Wörter (Task 1)
- Kein Push, kein Tag, kein Kommentar

## Deviations from Plan

- Die Tests test_lockstep_versions.py, test_upgrade_seed_steps.py und test_store_metadata.py pinnten 1.6.5 nicht und blieben unverändert (im Plan als "nachziehen, wo sie 1.6.5 pinnen" vorgesehen).
- Task 2 und Task 3 wurden über eine gemeinsame Owner-Frage (Antwort A) abgenommen; die zwei Freigabezeilen stehen trotzdem getrennt, Commit gemeinsam (efd0deb3).

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: 93996a4b, 53a11d81, cea12573, efd0deb3
- FOUND: .planning/phases/45-findling-1-7-0/45-FREIGABEN.md mit beiden Zeilen
