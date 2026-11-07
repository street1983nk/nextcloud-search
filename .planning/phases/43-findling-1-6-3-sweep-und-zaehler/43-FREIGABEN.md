# Phase 43: Owner-Freigaben für Push, Merge, Tag, Dispatch, Kommentar

Je Gegenstand genau eine Maschinenzeile (Bindende Vorgaben in 43-02-PLAN.md). Kanal: Claude Code Terminal, über den Koordinator.

Owner-Vorgabe vor dem Push: "Erst fixen, dann pushen (Empfohlen)", also zuerst der Befund G1 aus dem 43-07-Checkpoint (gespeicherte Ruhe des Prüflaufs überlebt einen Neustart) als fix(43-16).

Freigabe Push 43-07: "Ja, auf main pushen" (2026-11-07 14:29, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-07: "Ja, starten" (2026-11-07 14:29, Claude Code Terminal) Entscheid: ja

Umfang: genau ein Push des entstandenen HEAD (43-01 bis 43-07 plus Fix) auf origin main, genau ein Dispatch von "Coverage end to end" nach grünen Push-Läufen. Kein Tag, kein Release, kein Store. Jeder weitere Push oder Dispatch braucht eine neue Freigabe.

Freigabe Push 43-07 Fix 1: "Ja, pushen und dann E2E" (2026-11-07 15:00, Claude Code Terminal) Entscheid: ja

Umfang Fix 1: genau ein Push von e65e34c3 (20fafb7e und e65e34c3: Fixture-Pfad im phpunit-Job, Controller-Double, sechs geprüfte Routen); derselbe Wortlaut deckt zusammen mit "Ja, starten" genau einen Dispatch von "Coverage end to end", wenn alle acht Push-Workflows grün sind.
