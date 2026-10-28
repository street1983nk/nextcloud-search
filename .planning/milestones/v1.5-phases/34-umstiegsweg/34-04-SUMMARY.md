---
phase: 34-umstiegsweg
plan: 04
subsystem: docs-store-text
tags: [umst-03, readme, store-listing, changelog, text-gate]
requires:
  - 34-02 (migration pages docs/migrate-from-fulltextsearch{,.en,.fr}.md, gate test_migration_path.py)
  - 34-03 (admin banner, named in the CHANGELOG)
provides:
  - README sections "Umstieg von fulltextsearch" / "Switching from fulltextsearch" / "Passer de fulltextsearch à Findling" before Installation
  - store draft "# Entwurf v1.5.0 (Teil Phase 34)" with v1.5.0 tag links per description language
  - CHANGELOG Unreleased/Added: migration page and admin banner
  - gate functions scan_readme, scan_draft, scan_digits, strip_urls, store_languages
affects:
  - 34-05 (owner acceptance presentation of the store draft)
  - REL-05 / phase 36 (info.xml gets the store line, tag v1.5.0 makes the links resolve)
tech-stack:
  added: []
  patterns:
    - link targets masked before the wording compare, so wording and target are one finding each
    - store languages read from both info.xml, not assumed
key-files:
  created: []
  modified:
    - backend/tests/test_migration_path.py
    - README.md
    - README.en.md
    - README.fr.md
    - docs/store-listing.md
    - CHANGELOG.md
decisions:
  - "README nach O9 Variante 2 (eigener Abschnitt vor Installation), Wortlaut zeichengleich aus 34-WORTLAUT (C)"
  - "Kopfsatz des Entwurfs: Owner-Abnahme offen (REL-05) plus Vermerk, dass der Wortlaut am 19.10.2026 abgenommen ist"
  - "CI lief wie in 34-03 auf dem gepushten Agentenzweig, Remote-Zweig danach gelöscht; Push auf main bleibt beim Orchestrator"
metrics:
  duration: "ca. 50 min"
  completed: 2026-10-19
  tasks: 2
  files: 6
---

# Phase 34 Plan 04: README-Verweise, Store-Entwurf, CHANGELOG Summary

Die drei READMEs verlinken die Umstiegs-Seite ihrer Sprache in einem kurzen Abschnitt vor "Installation", `docs/store-listing.md` trägt den Entwurf der Phase 34 mit Tag-URL je Beschreibungssprache, der CHANGELOG nennt Seite und Banner; ein erweitertes Gate in `test_migration_path.py` hält das alles.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Gate für README-Verweise und Entwurfsabschnitt rot schreiben | f182e57b |
| 2 | README-Zeilen, Store-Entwurf, CHANGELOG, Gates grün, Push, CI | 15f4bdfa |

## Was gebaut ist

- README.md / README.en.md / README.fr.md: je ein Abschnitt (Überschrift plus eine Zeile) aus 34-WORTLAUT (C) Variante 2, relativer Link auf die Seite der eigenen Sprache, keine Zahl. Sonst nichts an den READMEs geändert.
- `docs/store-listing.md`: Abschnitt `# Entwurf v1.5.0 (Teil Phase 34)` nach Phase 33, Kopfsatz "Owner-Abnahme offen, Teil von REL-05; info.xml wird erst nach der Abnahme geändert, die READMEs verlinken die Seite seit Phase 34.", Tabelle en/de/fr mit der Store-Zeile aus (D) und absoluter Tag-URL `blob/v1.5.0/docs/migrate-from-fulltextsearch{.en,,.fr}.md`, Satz "Tag-Links lösen erst mit v1.5.0 auf; vor der Einreichung prüfen.", Teil 2 zu den README-Zeilen.
- `CHANGELOG.md` Unreleased/Added: zwei englische Einträge (Migrationsseite dreisprachig, Admin-Banner bei aktivem fulltextsearch oder files_fulltextsearch).
- Beide `info.xml` unverändert.

## Gate

- `scan_readme`: Überschrift genau einmal, direkt gefolgt von "## Installation", Abschnittstext gleich dem Wortlaut (Linkziele maskiert), keine Zahl, kein Phase-35-Wortlaut; `scan_readme_links`: eigene Sprachseite genau einmal, fremde Sprachseite je ein Fund.
- `scan_draft`: Abschnitt genau einmal, Kopfsatz, je Sprache aus `store_languages()` (gelesen aus beiden info.xml: de, en, fr) eine Zeile mit Wortlaut und genau der Tag-URL, keine Zahl nach `strip_urls`, außerhalb der Zeilen kein relativer und kein blob/main-Link, kein Phase-35-Wortlaut.
- Selbsttests: Musterentwurf und Muster-README sauber; Zahl nur in URL sauber, Zahl in der Prosa ein Fund; Abschnitt entfernt ein Fund; Tag-URL auf blob/main ein Fund; Kopfsatz fehlt ein Fund; README.md auf englische Seite ein Fund; Phase-35-Wortlaut im README gefunden. 11 `test_mutated_*` insgesamt.
- Verbotsscan aus 34-02 liest README*.md und docs/** ohnehin, also auch die neuen Zeilen.

Rot vor den Texten (Task 1):

```
FAILED tests/test_migration_path.py::test_readme_sections_link_the_page_of_their_language
  README.md: no single section '## Umstieg von fulltextsearch'
  README.md: no link to docs/migrate-from-fulltextsearch.md
  (dto. README.en.md, README.fr.md)
FAILED tests/test_migration_path.py::test_draft_section_of_phase_34_carries_a_tag_link_per_language
  docs/store-listing.md: no single section '# Entwurf v1.5.0 (Teil Phase 34)'
2 failed, 22 passed
```

Lokal nach Task 2: volle Suite `5734 passed, 252 skipped` (18 min), ruff check, ruff format, pyright (0 errors), vulture, `reuse lint` grün; `test_store_metadata.py` und `test_public_artifacts.py` grün; `git diff --check` sauber.

## CI

HEAD `15f4bdfa` auf dem Zweig `worktree-agent-ad168a98c733a1430`, alle Läufe grün:

| Workflow | Lauf |
|---|---|
| Python gates | 39230381342 |
| Integration | 39230381488 |
| Resilience | 39230381437 |
| HaRP deploy | 39230381198 |

"PHP and store metadata gates" wurde nicht ausgelöst (kein PHP und keine info.xml geändert, Pfadfilter).

## Deviations from Plan

**1. [Worktree-Modus] Push auf den Agentenzweig statt auf main**
- Wie in 34-03: als paralleler Worktree-Agent schreibe ich main nicht. Gepusht wurde der Agentenzweig, CI grün, Remote-Zweig danach gelöscht. Auf main laufen die Workflows nach Merge und Push durch den Orchestrator erneut.

Sonst wie geplant.

## Known Stubs

Keine. Die Tag-Links lösen erst mit Tag v1.5.0 auf (bewusst, REL-05); das Gate prüft, dass die Zieldateien im Repo liegen.

## Threat Flags

Keine neue Oberfläche.

## Offene Punkte

- 34-05: Store-Entwurf dem Owner zur Release-Abnahme vorlegen (REL-05).
- Phase 36: Store-Zeile in die sechs Beschreibungen beider info.xml, Tag-Links nach dem Tag prüfen.

## Self-Check: PASSED
