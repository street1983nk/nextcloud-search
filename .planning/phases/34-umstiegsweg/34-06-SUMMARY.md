---
phase: 34-umstiegsweg
plan: 06
subsystem: audit
tags: [umst-01, umst-02, umst-03, audit, security, performance, fact-check]
requires:
  - 34-01 bis 34-05 (Wortlaut, Seiten, Admin-Hinweis, READMEs/Store-Entwurf, Owner-Abnahme)
provides:
  - 34-AUDIT.md (geschlossen, status fixed)
  - backend/tests/test_phase34_audit.py (Quelltext-, Render-, Instanz-, Netz- und Mutationsproben)
  - UMST-01 bis UMST-03 Complete in REQUIREMENTS.md
affects:
  - Phase 36 (Tag-Links nach v1.5.0 prüfen, Store-Entwurf in REL-05, embeddings.md:497, 186 Abfragen je Poll)
tech-stack:
  added: []
  patterns:
    - token_get_all-Probe statt Regex-Gate, mit Positivkontrolle
    - echtes Template-Fragment mit Kern-p() und IL10N-Stub auf php:8.3-cli
    - Gate-Mutationen auf einer Baumkopie, Erwartung vor dem Lauf notiert
key-files:
  created:
    - .planning/phases/34-umstiegsweg/34-AUDIT.md
    - .planning/phases/34-umstiegsweg/deferred-items.md
    - backend/tests/test_phase34_audit.py
  modified:
    - docs/migrate-from-fulltextsearch.fr.md
    - .planning/REQUIREMENTS.md
decisions:
  - "L-34-02 gefixt: französische Pflichtformel in eine Zeile umbrochen, Wortlaut unverändert"
  - "L-34-01 accept: Geviertstriche in STATE.md stammen von gsd-sdk, STATE.md gehört dem Orchestrator"
  - "Katalog-Markup-Probe über das echte Template-Fragment statt einer Katalogkopie auf 8090 (Bind-Mount liegt im Hauptcheckout)"
  - "Netz- und Mutationsproben nur mit FINDLING_AUDIT34_NETWORK=1 bzw. FINDLING_AUDIT34_MUTATION=1, damit CI schnell bleibt"
metrics:
  duration: "ca. 1 h 20 min"
  completed: 2026-10-19
  tasks: 4
  files: 6
---

# Phase 34 Plan 06: Audit des Umstiegswegs Summary

Security-, Bug- und Performance-Audit von Phase 34 in vier getrennten Schritten, alle Proben gefahren und als Regressionstests in `backend/tests/test_phase34_audit.py` (39 Tests); kein Befund über LOW, ein LOW gefixt (französische Pflichtformel über einem Zeilenumbruch), ein LOW entschieden; UMST-01 bis UMST-03 abgehakt.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Sicherheit des Banners, des Links und der Texte | 59ef521e |
| 2 | Fehler, Randfälle und Faktenprüfung der Seiten | 2708d95d |
| 3 | Performance-Audit | 83532379 |
| 4 | Fix L-34-02 (RED, Fix, GREEN) | 151bc30b |
| 4 | Bericht schließen, Anforderungen abhaken | 3a3ca2b5 |

## Ergebnisse

- **Security:** Banner-Ausgaben nur über `p()`, href nur aus drei Literalen (token_get_all mit Positivkontrolle); Markup im Katalogwert rendert als Text; Nicht-Admin 403 auf Übersicht und Seite, anonym 401; keine Logzeile mit einer App-ID nach dreimaligem Flagwechsel; Store-Archiv enthält `ParallelSearchService.php` byte-gleich; REUSE 2758/2758.
- **Bugs:** Sprach-Map gleich dem Orakel für 14 Codes; Bannerentscheidung gleich der SQL-Wahrheit in sechs Fällen (inkl. Gruppenwert); alle elf Faktenaussagen der drei Seiten gleich App Store und GitHub am 19.10.2026 (13:21 UTC, curl/jq und httpx), nichts veraltet; sechs Gate-Mutationen machen je genau den erwarteten Test rot; jeder Befehl der Schritte ist im Protokoll 34-02 oder belegt markiert.
- **Performance (8090):** Poll Median 55,38 / 54,51 ms ohne/mit Flag (-1,6 %); Seite `load` +3,1 % bei gleichem erstem Byte; 186 Abfragen je Poll mit und ohne Flag, 0 durch `isEnabledForAnyone`; Pollantwort +23 Byte durch den Schlüssel.
- **CI** auf 3a3ca2b5 (Agentenzweig, danach remote gelöscht): Python gates 39264837383, Integration 39264837352, Resilience 39264837394, HaRP deploy 39264837414, alle grün; PHP-Workflow nicht ausgelöst (kein `php/`-Commit).
- Lokal vor dem Fix-Commit: 5761 passed, 264 skipped; ruff, ruff format, pyright 0, vulture leer. Audit-Modul gegen 8090 mit Netz und Mutation: 39 passed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Katalogkopie auf 8090 durch Renderprobe ersetzt**
- **Gefunden in:** Task 1
- **Problem:** Die Kataloge der Instanz liegen im Bind-Mount des Hauptcheckouts; ein Worktree-Agent darf dort nicht schreiben.
- **Lösung:** Das echte Banner-Fragment des Templates läuft auf `php:8.3-cli` mit einem `p()` wie im Kern und einem injizierten Katalogwert; Positivkontrolle mit rohem `p()`. Der Plan erlaubt diese Variante ("through the tokenizer probe or through 8090").

**2. [Worktree-Modus] ROADMAP.md und STATE.md nicht angefasst**
- Der Plan verlangt im letzten Task, ROADMAP.md und STATE.md von Hand nachzuziehen; laut Auftrag des Orchestrators gehören diese Dateien ihm. Nur REQUIREMENTS.md ist abgehakt. Der Orchestrator trägt nach: Phase 34 ausgeführt, Verifikation offen, Planhaken 34-01 bis 34-06; offene Punkte Phase 36 (siehe unten).

**3. [Worktree-Modus] Push auf den Agentenzweig statt auf main**
- Wie in 34-03: CI lief auf dem gepushten Agentenzweig, der Zweig ist danach remote gelöscht; der Push auf `main` folgt nach dem Merge durch den Orchestrator. Der letzte Docs-Commit (Laufnummern im Bericht, diese SUMMARY) ist nicht gepusht.

**4. Netz- und Mutationsproben hinter Schaltern**
- `FINDLING_AUDIT34_NETWORK=1` (App Store und GitHub) und `FINDLING_AUDIT34_MUTATION=1` (sechs Gate-Läufe auf einer Baumkopie): ohne Schalter übersprungen mit Grund, damit CI nicht vom Netz abhängt und nicht doppelt Gates fährt. Beide im Audit gefahren, Ergebnis im Bericht.

`backend/tests/test_measurement_scripts.py` ist unverändert, weil kein Fix `php/` berührt (kein Baumhash-Zug nötig).

## Offene Punkte (Pflichtvermerk und Phase 36)

- **`docs/embeddings.md:497`** trägt die historische Aussage "jahrelang verwaist" über fulltextsearch, in einer Doku, die von README und Seiten aus erreichbar ist. Sie widerspricht dem Pflegestand der Umstiegs-Seite ("fulltextsearch wird von Nextcloud gepflegt"). Laut 34-CONTEXT "Deferred" nicht in dieser Phase, nicht still geändert. Vorschlag: Owner-Frage, sonst Phase 36. Dieselbe Aussage steht in der Projektbeschreibung (CLAUDE.md/PROJECT.md).
- Tag-Links `blob/v1.5.0/docs/migrate-from-fulltextsearch{,.en,.fr}.md` nach dem Tag v1.5.0 prüfen (Phase 36).
- Store-Entwurf Phase 34 (`docs/store-listing.md`) in REL-05 übernehmen.
- 186 Datenbankabfragen je Pollaufruf, unabhängig von Phase 34 (`deferred-items.md`).
- An den Orchestrator: `.planning/STATE.md` trägt zwei Geviertstriche aus `gsd-sdk` (L-34-01).

## Known Stubs

Keine.

## Threat Flags

Keine. Das Audit fügt keine Produktoberfläche hinzu; die Proben laufen nur mit gesetzten Variablen gegen eine Dev-Instanz.

## Self-Check: PASSED

- 34-AUDIT.md, deferred-items.md, test_phase34_audit.py, 34-06-SUMMARY.md vorhanden
- Commits 59ef521e, 2708d95d, 83532379, 151bc30b, 3a3ca2b5 im Log
- `grep -cE "^- \[x\] \*\*(UMST-01|UMST-02|UMST-03)\*\*" .planning/REQUIREMENTS.md` = 3, Traceability dreimal Complete
- kein `xfail(strict=True` im Audit-Test
