# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.1, Qualitaet und Effizienz

**Shipped:** 2026-09-11
**Phases:** 5 | **Plans:** 37 | **Commits:** 265

### What Was Built

- Gemeinsame Embedding-Engine: Grundlast 691,8 auf 103,2 MB, belegt statt behauptet (Vergleichsmessung auf identischer Zielhardware, korpus-gleich und baumhash-gleich nachgewiesen)
- Deutsche Komposita ueber split_compound mit lizenzgeklaerter wngerman-Wortliste; CI-Sprachfaelle, die ohne den Splitter rot werden (Wegbeweis statt Ergebnisbeweis)
- Eigene Ergebnisseite mit Paginierung hinter der bestehenden Berechtigungsgrenze, dreisprachig EN/DE/FR (174 Katalogschluessel, vier Katalog-Gates)
- Vergleichsmessbericht in 19 Abschnitten mit eigenem Abschnitt "Was dieser Lauf nicht besser gemacht hat" (13 benannte Verschlechterungen)
- Store-Release 1.1.0 mit Ende-zu-Ende-Upgrade-Beweis 1.0.3 auf 1.1.0 in CI; Box abgebaut, Korpus als EBS-Snapshot

### What Worked

- Bestandsaufnahme vor Neubau: Phasen 7 und 8 begannen mit dem Beleg dessen, was v1.0/06.1 schon gebaut hatte; Phase 8 wurde dadurch fast reine Beweisarbeit statt Umbau
- Checkpoint-Plaene mit Owner-Deckel fuer jede Box-Anfahrt (Stunden + USD): beide Anfahrten blieben unter dem Deckel, keine Kostenueberraschung
- Wellen ohne Box-Zeit vor die Anfahrt ziehen (Werkzeugluecken, Skriptset, Ablaufplan als Datei mit Urteilszeile): der 19-h-Lauf lief nachts allein durch
- "Rot-Faehigkeit belegen" als Standard: Gates und Tests wurden per Mutation am echten Baum bewiesen, bevor sie zaehlten
- Haertung jenseits des Happy Path fand erneut echte Produktfehler, die kein Test fand (stumme Suche nach Minor-Upgrade; "Deutsch (Sie)" fiel auf Englisch zurueck)

### What Was Inefficient

- Die Volllauf-Laufzeit stieg um 40,9 Prozent und die Ursachenanalyse musste auf v1.2 vertagt werden; die Messphase haette eine Zulauf-Beobachtung von Anfang an einplanen sollen (vorrat=0 in 62/325 Lesungen erst nachtraeglich gefunden)
- DI-10-02 (Sprachfall-Messung gegen Fremdbestand) wurde zweimal angefasst und ist trotzdem nicht geschlossen: die Route deckelt jede Antwort bei 26, die Schwelle liegt bei 64; das Skript kann seine eigene Messfrage auf dieser Topologie nicht beantworten
- Der Vorfall vom 11.09. (Executor committete 4x mit fremder Git-Identitaet) kostete eine filter-branch-Bereinigung samt Force-Push; die Regel stand in Memory, aber nicht im Executor-Prompt
- Drei Debug-Sessions blieben formal offen, obwohl die Fixe laengst gemerged waren; Sessions werden nach dem Fix nicht als resolved gestempelt

### Patterns Established

- Jeder Minor-Versionssprung braucht eine PHP-Migration (Muster Version001100Date20260911000000), sonst sucht die Bestandsinstallation stumm ins Leere
- Eine Messzahl steht an genau drei Stellen (README.en.md + beide info.xml) und ein Gate haelt die Wortlaute zusammen
- Store-Tag nie verschieben; kaputte Store-Version in-place reparieren (Update-Endpunkt, 200 = Erfolg) und zusaetzlich eine neue Version nachschieben, damit Bestandsinstallationen das Update sehen
- Owner-Muttersprachler-Gate fuer FR als blockierender Checkpoint in zwei Teilen (Katalog, dann Store-Texte)
- Box-Arbeit: einmal anfahren, Deckel nennen, Rohdaten committen vor dem Lauf, Snapshot vor Abbau, Nichtexistenz-Nachweise nach Abbau
- Pre-commit-Hook sperrt fremde Git-Identitaeten in beiden Repos; die Regel gehoert zusaetzlich woertlich in jeden Executor-Prompt

### Key Lessons

1. Messberichte gewinnen ihre Glaubwuerdigkeit aus dem Abschnitt ueber das, was schlechter wurde; der Owner nahm den Bericht ohne Beanstandung ab, gerade weil die 13 Verschlechterungen benannt waren
2. Ein Erfolgskriterium mit dem Wortlaut "keine Regression" ehrlich als "teilweise belegt" fuehren ist billiger als es schoenzurechnen; die offene Haelfte wurde sauber an v1.2 uebergeben
3. Werkzeuge, die Ausfaelle als Erfolge zaehlen (Lastwerkzeug, Stufe 16), entwerten ganze Messreihen; Zaehler immer gegen eine unabhaengige Quelle aufrechnen (Nextcloud-Protokoll)
4. CI-Beweise schlagen Box-Beweise, wo beides geht: der Upgrade-Beweis lief komplett in deploy-harp, die Box war nur noch fuer die zwei Werkzeug-Fixe noetig

### Cost Observations

- Modellmix: Executor/Planner/Researcher opus, Checker/Verifier sonnet (model_profile quality)
- AWS-Kosten des Milestones: ~3,83 USD Box-Laufzeit (31,05 h Phase 10 + 1,97 h Phase 11) + Snapshot ~2,9 USD/Monat laufend
- 4 Kalendertage fuer 37 Plaene; die teuerste Einzelposition war der 26h41min-Volllauf (detached, eine Nacht)

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 7 (1-6 + 06.1) | 103 | Launch-Haertungsphase 06.1 als Muster etabliert; Audit-Gate je Phase |
| v1.1 | 5 (7-11) | 37 | Erste Phase mit CONTEXT.md (discuss-phase); Checkpoint-Plaene mit Kostendeckel; Bestandsaufnahme vor Neubau |

### Cumulative Quality

| Milestone | Tests | Bemerkung |
|-----------|-------|-----------|
| v1.0 | ~1.750 Python + PHP-Suite | 51.961 Docs auf Zielhardware, 0 failed |
| v1.1 | ~2.000 Python + 185 PHP | 52.111 Docs ohne OOM; 6 CI-Workflows inkl. Fremdinstallation + Upgrade |

### Top Lessons (Verified Across Milestones)

1. Die Haertungsphase jenseits des Happy Path findet in jedem Milestone echte Produktfehler, die die Testsuite nicht fand (v1.0: 06.1-Befunde; v1.1: stumme Suche nach Minor-Upgrade, Sprachfallback)
2. Owner-Checkpoints mit hartem Deckel (Kosten, Wortlaute, Einreichung) verhindern teure Alleingaenge, ohne die Autonomie der Wellen zu bremsen
3. Beweis-Tests, deren Rot-Faehigkeit per Mutation belegt ist, sind die einzigen, deren Gruen etwas bedeutet
