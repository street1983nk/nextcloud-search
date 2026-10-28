---
phase: 34-umstiegsweg
verified: 2026-10-19
status: passed
score: 3/3 Erfolgskriterien
gaps: []
---

# Phase 34: Verifikation

**Ziel:** Ein Admin mit fulltextsearch/Elasticsearch findet einen klaren, ehrlichen Weg zu Findling und wird gewarnt, solange beide parallel laufen.
**Verdikt: passed.** Geprüft am Code auf main (HEAD 9108e5ca), nicht anhand der SUMMARYs.

## Erfolgskriterien

| # | Kriterium | Status | Beleg |
|---|-----------|--------|-------|
| 1 | Umstiegs-Seite de/en/fr mit Abschalt-Schritten, Faktenliste, Pflichtformel; "einzige OCR" nirgends | passed | Drei Dateien `docs/migrate-from-fulltextsearch{,.en,.fr}.md` (102/100/107 Zeilen), Sprachumschalter in Zeile 1 (de), Pflichtformel in de und en je einmal gefunden, fr trägt "l'OCR sans modifier les fichiers et sans Elasticsearch". Repo-weite Suche nach "einzige OCR": einziger Treffer `docs/performance.md:1025` ("keine einzige OCR-Seite", Messtabelle, keine Produktaussage, Phase-34-fremd). Gate `test_migration_path.py` grün. |
| 2 | Hinweis bei parallelem fulltextsearch mit Folge und Link; ohne alte Apps nichts | passed | `php/templates/admin.php:431` Block `findling-banner-parallel`, `hidden` wenn `!$parallelSearch`; Text nennt doppelte Treffer; Link `findling-banner__link` auf `$migrationDocsUrl`. `ParallelSearchService` nutzt `isEnabledForAnyone`, ist in `AdminViewService` eingebunden. Beide neuen l10n-Schlüssel in allen 16 Katalogen. CSS-Klasse in `php/css/admin.css:108`. `admin.js` greift den Block nicht an (serverseitig gerendert, PE-34-2). |
| 3 | README de/en/fr und Store-Entwurf verlinken die Seite; Kurztext-Regel; Owner-Abnahme | passed | README.md:70, README.en.md:67, README.fr.md:73, jeweils vor "## Installation". `docs/store-listing.md:2282` "# Entwurf v1.5.0 (Teil Phase 34)", Kopfzeile "Owner-Abnahme 19.10.2026". `34-05-ABNAHME.md:78` "Owner-Abnahme: 19.10.2026". |

## Weitere Prüfungen

- REQUIREMENTS.md: UMST-01, UMST-02, UMST-03 sind `[x]`, Traceability "Complete". ROADMAP: Phase 34 `[x]`.
- `34-AUDIT.md`: 0 CRITICAL/HIGH/MEDIUM, 2 LOW (L-34-02 gefixt mit Regressionstest, L-34-01 entschieden). Audit-Modul `backend/tests/test_phase34_audit.py` läuft.
- Gates: `uv run pytest tests/test_migration_path.py tests/test_admin_ui_contract.py tests/test_measurement_scripts.py tests/test_phase34_audit.py -q` ergibt 722 passed, 12 skipped (Netzwerk-/Mutationsproben und Instanzproben ohne Umgebungsvariablen, erwartet).
- Debt-Marker (TBD/FIXME/XXX) wurden nicht flächendeckend gescannt; das Audit deckt den Phase-Diff ab.

## Bewusste Abweichungen (keine Lücken)

- `info.xml` bis REL-05 (Phase 36) unverändert.
- Banner-Links zeigen auf `blob/v1.5.0`-Tag-URLs, auflösbar erst nach dem Tag (Phase 36).
- `docs/embeddings.md:497` Wortlaut aufgeschoben auf Phase 36; 186 DB-Abfragen je Poll der Admin-Seite stehen in `deferred-items.md` (Phase 36).

## Hinweise (keine Blocker)

- Untracked `backend/.coverage` im Arbeitsverzeichnis (Testlauf-Artefakt), nicht eingecheckt.
- Mensch-Verifikation: keine offen; visuelle Abnahme erfolgte durch den Owner am 19.10.2026 auf 8090.

## Lückenzusammenfassung

Keine.
