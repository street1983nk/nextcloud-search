---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 12
subsystem: audit
status: complete
completed: 2026-10-20
requirements: [STR-01, STR-02, STR-03]
key-files:
  created:
    - .planning/phases/35-stretch-aehnliche-dokumente-und-spikes/35-AUDIT.md
    - backend/tests/test_phase35_audit.py
  modified:
    - backend/src/findling/worker/embedding.py
    - backend/tests/test_embedding_track.py
    - backend/tests/test_measurement_scripts.py
    - scripts/dev/register-exapp.sh
    - docs/measurements/2026-10-aehnlich-distanzen/README.md
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md
decisions:
  - "Owner-Wort 20.10.2026: auch LOW-Befunde werden behandelt (vier Fixes, zwei begruendete Accepts)"
  - "L-35-01: unknown-Marke liefert bei leerem Bestand nach (Cursor vor Marke, Drift-Reihenfolge); teilgefuellter Bestand wartet bewusst weiter"
---

# Phase 35 Plan 12: Audit Summary

Security-, Bug- und Performance-Audit der Phase 35 geschlossen: 0 CRITICAL, 0
HIGH, 0 MEDIUM, 6 LOW, alle behandelt. Rechtegrenze der Aehnlich-Ansicht live
mit unabhaengigem SQL-Orakel belegt, Kosten weit unter den Budgets, die
Messberichte halten ihre Regeln. STR-01 bis STR-03 abgehakt.

## Tasks

| Task | Inhalt | Commits |
|---|---|---|
| 1+2 | Proben S1-S9, B1-B8, P1-P5, Bericht, 5 Quelltext-Regressionstests | 65abd529 (nach den Fixes committet, Bericht direkt mit status fixed) |
| 3 | Behandlung aller LOW, Abhaken, Abschluss | 5a98eee0, 0e1e42f9, c2b402cb, Abschluss-Commit |

## Kernergebnisse

- **S1/S2 (Rechtegrenze):** fremde Quelle loest keinen Containeraufruf aus
  (Logzaehlung 16 vor, 16 nach); byte-gleiche Fremdkopie erscheint nie als
  Nachbar, Orakel per SQL auf oc_filecache/oc_share; eigene Kopie erscheint
  (B5), Quelle nie.
- **S3:** geloescht, fremd und nicht existent byte-identisch (3 x 2 204 B).
- **S5:** /similar direkt 401/401/400, nicht in info.xml.
- **S7:** XSS-Titel escaped im h1, 0 rohe Tags.
- **Performance:** Ergebnisseite +9,0 ms p50 fuer 25 Aehnlich-Links;
  Aehnlich-Ansicht p50 82,9 ms / p95 101,2 ms (Budget 3,0 s); Containeraufruf
  p50 6,8 ms / p95 10,7 ms (Decke 1,5 s); hoechstens 31 readableFile je
  Ansicht.
- **Befunde:** L-35-01 gefixt (unknown-Marke, Produktpfad, Regressionstest,
  Baumhash-Journal Plan 35-12), L-35-04/L-35-05 gefixt (register-exapp.sh:
  Stale-Probe liest jetzt auch die bewusst undeklarierten Inhaltsrouten aus
  den API-Quellen; Regex-Anker-Fehler hatte den Reuse-Zweig zu totem Code
  gemacht, beide live gegengeprueft), L-35-03 gefixt (Massluecke am Wert 54,5
  dokumentiert), L-35-02 accept (Poller-Abholung beschraenkt auf 120/300 s,
  Requeue-Route intern), L-35-06 accept (httpx-INFO nennt fileid/userId,
  Bestand, Pruefpunkt Phase 36), T-35-15 accept (Verdraengungsklasse der
  gewoehnlichen semantischen Runde).

## Deviations from Plan

- **Bericht nicht erst "offen" committet:** die Fixes liefen vor dem
  Bericht-Commit, der Bericht traegt von Anfang an status fixed; kein xfail
  noetig, weil kein Befund MEDIUM+ und die LOW-Fixes sofort gruen belegt
  wurden (RED/GREEN im Bericht dokumentiert).
- **P1 ueber Template-Tausch:** "ohne Aehnlich-Links" wurde durch das
  Basis-Template 5a66ba1e im Bind-Mount gemessen (Opcache-Wirksamkeit je
  Richtung per Linkzaehlung abgewartet), danach per git checkout
  zurueckgesetzt; dokumentierter Dev-Eingriff.
- **P4 aus Quelltext plus PHPUnit-Mock-Zaehlung (CI)** statt Instrumentierung;
  Begruendung im Bericht.
- **Volle Suite lokal nicht erneut gefahren:** der RAM-Waechter hatte den
  Hintergrundlauf der Welle 10 gestoppt; das Gate liefert die CI (Python
  gates fahren die volle Suite je Push), Laufnummern im Abschlussvermerk.
- **Owner-Wort waehrend des Audits:** "auch low befunde muessen behandelt
  werden"; umgesetzt wie oben.

## Self-Check: PASSED

- 35-AUDIT.md status fixed, kein xfail in test_phase35_audit.py (5 Tests).
- REQUIREMENTS.md: drei Zeilen STR-01 bis STR-03 auf [x], Traceability
  Complete.
- Proben-Uploads geloescht (21644 im Lauf, 21645/21646 per WebDAV 204),
  Template zurueckgesetzt, Backend laeuft mit Modell weiter.
