---
phase: 37-owner-tor-und-store-sichtbarkeit
verified: 2026-10-28
status: passed
score: 4/4 success criteria, 3/3 requirements
---

# Phase 37 Verification

Verdict: PASSED. Verified against repo state, not SUMMARY claims.

| SC | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1 | D1-D4 decided, verbatim, consequences propagated (DEDUP-01) | VERIFIED | 37-OWNER-ENTSCHEIDE.md: owner answer quoted, 28.10.2026 ca. 13:0x, channel Remote Control; D-37-01..09 in table. ROADMAP phase 38 reworded per D-37-09 (goal + SC1-4); phase 39 SC3 holds Weg C first (D-37-03), Weg B (D-37-01), A6/A7 measurement (D-37-04), Weg A deferral (D-37-02). REQUIREMENTS ZERT-01/02 reworded with D-37-09; DEDUP-01 ticked. |
| 2 | Names + unchanged IDs, gated (STORE-01) | VERIFIED | php/appinfo/info.xml l.30-32: Findling Search / Suche / Recherche; backend l.79-81: Findling Backend x3; ids findling / findling_backend. Gate `test_both_info_files_keep_their_identity_the_app_ids_and_the_approved_names` plus mutation tests (changed id, name in one language, backend name). |
| 3 | Exactly one discussion link, URL reachable | VERIFIED | grep -c = 1 in both files; URL .../249775 between website and bugs (php l.218/225/226, backend l.222/229/230). curl -L: HTTP 200. Gates for missing, doubled, wrong URL, behind bugs. |
| 4 | Cross-promo sentence en/de/fr, draft with date | VERIFIED | Sentence in all six descriptions (php l.59/98/137, backend l.105/141/177), matches ENTSCHEIDE section 5 text; CONNECTOR_SENTENCES gate. docs/store-listing.md l.2711 "# Entwurf v1.6.0 (Teil Phase 37), abgenommen am 28.10.2026"; gate `test_the_draft_of_phase_37_...`. |

## Gates run

- `cd backend && uv run --no-sync pytest -q tests/test_store_metadata.py`: 110 passed.
- `ruff check tests/test_store_metadata.py`: All checks passed.
- Docker and full suite not run (as instructed).

## Commits

aee10169, 656bd585, 1f276c0e, c20d7c3d, e17ed7c5, 3bd78ac7 all present in main history; main == origin/main (3bd78ac7), pushed. Only untracked file: backend/.coverage (harmless).

## Requirements

DEDUP-01, STORE-01, STORE-02: SATISFIED, ticked in REQUIREMENTS.md and traceability table. ZERT-01/02 correctly remain Pending (phase 38). No orphaned requirements.

## Warnings (non-blocking)

- Commit 3bd78ac7 touched ROADMAP.md with 370 changed lines (301 ins / 201 del overall); likely line-ending or whitespace churn beyond the plan checkbox. Content of phase 37-40 sections checked and correct; consider confirming no unintended edits elsewhere.
- Store-text rule "keine RAG-Wortwahl" conflicts with the approved sentence; owner accepted knowingly (D-37-08), noted in ENTSCHEIDE.

## Gaps

None. No human verification items.
