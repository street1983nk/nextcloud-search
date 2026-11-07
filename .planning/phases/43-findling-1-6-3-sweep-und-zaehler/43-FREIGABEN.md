# Phase 43: Owner-Freigaben für Push, Merge, Tag, Dispatch, Kommentar

Je Gegenstand genau eine Maschinenzeile (Bindende Vorgaben in 43-02-PLAN.md). Kanal: Claude Code Terminal, über den Koordinator.

Owner-Vorgabe vor dem Push: "Erst fixen, dann pushen (Empfohlen)", also zuerst der Befund G1 aus dem 43-07-Checkpoint (gespeicherte Ruhe des Prüflaufs überlebt einen Neustart) als fix(43-16).

Freigabe Push 43-07: "Ja, auf main pushen" (2026-11-07 14:29, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-07: "Ja, starten" (2026-11-07 14:29, Claude Code Terminal) Entscheid: ja

Umfang: genau ein Push des entstandenen HEAD (43-01 bis 43-07 plus Fix) auf origin main, genau ein Dispatch von "Coverage end to end" nach grünen Push-Läufen. Kein Tag, kein Release, kein Store. Jeder weitere Push oder Dispatch braucht eine neue Freigabe.

Freigabe Push 43-07 Fix 1: "Ja, pushen und dann E2E" (2026-11-07 15:00, Claude Code Terminal) Entscheid: ja

Umfang Fix 1: genau ein Push von e65e34c3 (20fafb7e und e65e34c3: Fixture-Pfad im phpunit-Job, Controller-Double, sechs geprüfte Routen); derselbe Wortlaut deckt zusammen mit "Ja, starten" genau einen Dispatch von "Coverage end to end", wenn alle acht Push-Workflows grün sind.

Vollzug: Push 53090f80 (Freigabe Push 43-07), Push e65e34c3 (Freigabe Push 43-07 Fix 1), alle acht Push-Workflows auf e65e34c3 grün; genau ein Dispatch "Coverage end to end" auf main, Lauf 42381671975 (gedeckt durch Freigabe Dispatch 43-07 und Fix 1), rot wegen des Harness (Speicher-Suche local::%), Korrektur c2037b29 lokal, nicht gepusht.

Freigabe Push und Dispatch 43-07 Fix 2: "Ja, pushen und E2E (Empfohlen)" (2026-11-07, Claude Code Terminal) Entscheid: ja

Umfang Fix 2: genau ein Push von 22f6f441, c2037b29, 5c30b0f9 plus dieser Freigabezeile auf origin main, genau ein Dispatch von "Coverage end to end", wenn alle Push-Workflows grün sind.
