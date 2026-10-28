---
phase: 39-ausschluss-anzeige-dedup-umfang-und-doku-hygiene
verified: 2026-10-28T00:00:00Z
status: human_needed
score: 5/5 success criteria verified
gaps: []
human_verification:
  - test: "Owner nimmt die Saetze aus 39-01-SUMMARY.md Abschnitt 'Saetze fuer die Owner-Runde Phase 40' ab (Mehrfachzaehlungs-Satz neu, Satz bei 0 ausgelassen, Hinweis nach Regelaenderung; en/de/fr, es/it/nl/pt maschineller Entwurf)"
    expected: "Owner bestaetigt Wortlaut in Phase 40"
    why_human: "Textabnahme durch den Owner, kein Code-Gap"
  - test: "Admin-Seite im Browser: Karte 'Bewusst ausgelassen: 0' mit Erklaersatz, Hinweis nach Aenderung eines Ausschlussmusters"
    expected: "Satz sichtbar, Hinweis verschwindet nach dem naechsten Zaehllauf"
    why_human: "UI-Darstellung (UI hint: yes), PHP-Tests laufen nur in CI"
---

# Phase 39 Verification

**Verdict: PASSED (mit offenen Human-Items fuer Phase 40)**
Verified against main at ca03c7b2 (= origin/main; b1637efa is its parent).

## Success criteria

| SC | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1 | Erklaersatz bei 0, 16 Kataloge | VERIFIED | Key "Nothing is left out on purpose right now" in php/l10n 8x .json + 8x .js (= 16 Dateien, alle Sprachen); de.json:15 traegt den deutschen Satz. Katalog-Tests (test_admin_ui_contract.py) gruen. |
| 2 | Hinweis nach Regelaenderung | VERIFIED | Key "The exclusion rules were changed..." 8x json + 8x js; AdminViewService::rulesPendingNow() (php/lib/Service/AdminViewService.php:2039) verdrahtet bei :770; SettingsService::KEY_RULES_CHANGED_AT. Alter Mehrfachzaehlungs-Satz ersetzt: 0 Treffer in php/, backend/ (auch test_admin_ui_contract.py); nur Nachtrag-Zitate in docs/l10n-*.md (Aenderungsprotokoll). |
| 3 | Weg C, Messung A6/A7, D-39-01/02, Weg B vertagt | VERIFIED | status.py: leaveOut-Parameter, indexedLeftOut/embeddedLeftOut nur mit Parameter (exclude_if=_absent); pytest test_status_leave_out + test_status_endpoint gruen. Kein Weg-B-Code (kein content_hash-Lookup in backend/src). A7: test_phase39_a7_counter.py gruen. A6: gh run 40716240639 "SMB ACL measurement" completed/success (Commit 59f93e49). 39-DEDUP-ERGEBNIS.md haelt Owner-Antwort woertlich "Wie empfohlen (Recommended)", D-39-01 = b (Weg A nicht gebaut), D-39-02 = vertagt v1.7 mit Begruendung und Startpunkt. Konsistent mit D-37-01..04. |
| 4 | Echte Umlaute in 3 Docs | VERIFIED | Treffer fuer ueber/fuehrt/Groesse/fuer in dev-setup/embeddings/install-check: ueber/fuer-Muster nur in dev-setup.md:263 (Dateiname 11-uebersicht.odt, Code) und :394-396 (Kommentar in nginx-Codeblock). "Bahnhofstrasse" bleibt unveraendert (docs/german-analyzer.md). Umlaut-Zaehlung: embeddings 90, install-check 73, dev-setup 13. |
| 5 | IN-01..IN-06 entschieden und umgesetzt | VERIFIED | 39-IN-ENTSCHEIDE.md: sechs Entscheide (IN-01..05 fix, IN-06 accept mit Begruendung). archive.too_many_entries (archive.py:318) einzige Kopie, odf.py/office.py importieren sie; _ZIP_TRAVERSAL (archive.py:137, :464); Waisen-Stempel vanished_storages in drop_orphan_bookmarks (Tests gruen). |

## Spot-checks run
`pytest -q` test_status_leave_out, test_status_endpoint, test_phase39_a7_counter, test_extract_signatures, test_extract_archive, test_store_vanished, test_measurement_scripts, test_admin_ui_contract: **1066 passed**.
Baumhashes: test_measurement_scripts.py ist in den 39-01-Code-Commits (cec671e0, 15a8fb11, a225dd97, 9ebd1917, c8770e01, 510086b0, 077d63ba..) und im 39-03-Code-Commit d27256bf angefasst, also zusammen mit dem Code bewegt.

## CI / Push
- origin/main enthaelt alle 39-x-Commits (HEAD == origin/main).
- Python gates auf 297b69ba: success (Security, Integration, Resilience, Multi-arch ebenfalls success; HaRP deploy zum Pruefzeitpunkt in_progress, Phase 38, nicht 39).
- PHP and store metadata gates auf f440a00a: success. (Python gates dort cancelled, durch Nachfolge-Push ersetzt; 297b69ba gruen.)

## Findings (nicht blockierend)
- WARNING (Doku): REQUIREMENTS.md Traceability-Tabelle zeigt ANZE-01, ANZE-02, DOCS-01, DOCS-02 noch "Pending" (Z. 60-65), waehrend die Checkboxen abgehakt sind; nur DEDUP-02 steht "Complete". Bei der Phasenabnahme auf Complete setzen.
- INFO: dev-setup.md:394-396 deutscher Kommentar im Codeblock mit ae/ue/oe-Ersatz ("fuer", "ueber", "Domaenen"); Codeblock, daher von DOCS-01 ("Prosa") nicht erfasst. Optional angleichen.
- INFO: ROADMAP-Progress-Zeile Phase 39 steht noch "Verifikation offen", mit der Abnahme aktualisieren.
- INFO: Untracked backend/.coverage und .claude/worktrees/* (Altlasten, nicht committen).
- INFO: Nicht lokal ausgefuehrt (Vorgabe): PHP-Tests und docker-Module; PHP-Seite nur ueber CI-Gate auf f440a00a belegt.

## Human verification
Siehe Frontmatter: (1) Owner-Abnahme der Saetze in Phase 40 (Abschnitt "Saetze fuer die Owner-Runde Phase 40" in 39-01-SUMMARY.md existiert, Zeile 149); (2) Sichtpruefung der Admin-Seite.
