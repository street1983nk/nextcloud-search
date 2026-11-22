---
phase: 45-findling-1-7-0
plan: 01
subsystem: l10n, admin-ui
tags: [pr-merge, zh_TW, locale, changelog]
requires: []
provides:
  - "PR #57 (Locale-Fix) und PR #56 (zh_TW-Katalog) auf main, foolfitz als Autor"
  - "locale() schreibt dataset.locale und root.lang gleich um (replace(/_/g, '-'))"
  - "PRODUCT.md und drei CHANGELOGs nennen zh_TW (#56) und den Locale-Fix (#57)"
affects: [45-04, 45-05, 45-06, 45-15]
tech-stack:
  added: []
  patterns: ["Merge fremder PRs nur mit --merge --match-head-commit auf den geprüften Kopf"]
key-files:
  created:
    - .planning/phases/45-findling-1-7-0/45-PR-REVIEW.md
    - .planning/phases/45-findling-1-7-0/45-FREIGABEN.md
  modified:
    - php/js/admin.js
    - backend/tests/test_admin_locale.py
    - PRODUCT.md
    - CHANGELOG.md
    - CHANGELOG.de.md
    - CHANGELOG.fr.md
decisions:
  - "PR #57 und PR #56 als Merge-Commits auf die geprüften Köpfe gemergt (Owner 'Go', 2026-11-22 01:04 UTC)"
  - "docs/l10n-chinese.md bleibt englisch (Owner 'Go')"
  - "Task 3b entfiel: zh_TW trägt alle 366 Schlüssel von de.json"
metrics:
  duration: "ca. 20 min (Fortsetzung ab Task 2)"
  completed: 2026-11-22
---

# Phase 45 Plan 01: PRs #56/#57 gemergt, root.lang-Nachtrag, Sprach- und Changelog-Einträge Summary

Beide Fork-PRs von foolfitz sind nach Owner-Freigabe auf den geprüften Kopf gemergt; locale() schreibt nun auch den Rückfall root.lang mit jedem Unterstrich um, und PRODUCT.md sowie die drei CHANGELOGs nennen Traditional Chinese und den Locale-Fix.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Beide PRs prüfen, Prüfbericht | 017e6d8a (vor Rebase 2ac440ce) | 45-PR-REVIEW.md |
| 2 | Owner-Freigabe je PR | 72838dd3 (vor Rebase 8285d2af) | 45-FREIGABEN.md |
| 3 | Merges + Nachträge | Merge 8cd9a0b4 (#57), Merge edc08233 (#56), ebd924cf (3a), f6eff1a1 (3c) | admin.js, test_admin_locale.py, PRODUCT.md, CHANGELOG*.md |

- Merges: `gh pr merge 57 --merge --match-head-commit 168b6b13...` und `gh pr merge 56 --merge --match-head-commit 51690b2a...`; Köpfe vor dem Merge erneut abgefragt, unverändert. Gegenprobe: beide Kopf-Commits haben Autor foolfitz.
- Danach `git pull --rebase origin main`: die zwei lokalen Planungs-Commits liegen jetzt über den Merges (neue Hashes siehe Tabelle).
- 3a: `(root.lang || '').replace(/_/g, '-')`; zwei neue Tests (root.lang 'zh_Hant_TW' / 'sr_Latn_RS' / 'pt_BR' ohne eigene Locale, dataset 'pt_BR') plus Positivkontrolle mit zwei Fehl-Mustern (root.lang unverändert, nur erster Unterstrich), beide fallen auf 'en'. Rot-Beweis: gegen das ungepatchte admin.js scheitern beide neuen Tests (2 failed, 6 passed).
- 3b: übersprungen, Schlüsselvergleich auf dem gemergten Stand: de 366, zh_TW 366, fehlend keine.
- 3c: PRODUCT.md "neun Sprachen ... Traditional Chinese (zh_TW ...)"; CHANGELOG.md/.de/.fr unter [Unreleased] je ein Added- und ein Fixed-Punkt.

## Verifikation

- Python-Gates in backend/: ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün.
- `pytest tests/test_admin_locale.py tests/test_admin_ui_contract.py tests/test_changelog_translations.py tests/test_unified_search_plugin.py tests/test_phase34_audit.py`: 287 passed, 12 skipped.
- Keine closes/fixes/resolves-Wörter, keine U+2013/U+2014 in CHANGELOGs und PRODUCT.md, keine Claude-Session-Zeile in den letzten Commits.
- PR #56 und #57: Status MERGED. Kein Kommentar auf GitHub (D-45-16).

## Deviations from Plan

None - plan executed exactly as written. (Die Commits 3a/3c liegen nur lokal; Push gebündelt in 45-06, dafür ist eine eigene Freigabe nötig.)

## Known Stubs

Keine.

## Self-Check: PASSED

- Dateien vorhanden: 45-PR-REVIEW.md, 45-FREIGABEN.md, admin.js, test_admin_locale.py, PRODUCT.md, CHANGELOG*.md.
- Commits vorhanden: 017e6d8a, 72838dd3, 8cd9a0b4, edc08233, ebd924cf, f6eff1a1.
