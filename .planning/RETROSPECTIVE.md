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

## Milestone: v1.2, Messbeleg und Ausbau

**Shipped:** 2026-09-21
**Phases:** 5 (12-16) | **Plans:** 63 | **Commits:** 317

### What Was Built

- Dateityp-Filter (sechs Typgruppen), Zeitraumfilter und Datums-Sortierung auf der Ergebnisseite: im Backend genau eine Occur.Must-Klausel, Sortierung als rein lexikalischer Modus (Score 0.0), in PHP ein readonly-Wertobjekt; Rechtegrenze in Zahl, Reihenfolge und Ort unveraendert
- Modell-Entladung im Leerlauf hinter TTL-Schalter (ab Werk aus): beide Speicherhalter zusammen, sechster Diagnosezustand "unloaded" dreisprachig, erste Suche nach Entladung antwortet lexikalisch unter der 1,5-s-Decke
- Eine bezahlte Box-Anfahrt lieferte alle offenen Messbelege (Wirkungsbeleg-Volllauf 19 h 20 min, vier Laststufen-Verdikte, Sprachfaelle, Wiederaufwaerm-Kosten in vier Auspraegungen) und vollzog dabei das Runbook zum ersten Mal
- 6 OCR-Sprachen (Positivliste von neun, Standard deu+eng+fra), stable35-Fenster-Entscheid am Stichtag vollzogen
- Store-Release 1.2.0 mit Ende-zu-Ende-Upgrade-Beweis 1.1.0 auf 1.2.0 in CI; Tag auf f827145 mit 7/7 gruenen Tag-Laeufen, Submission 2x HTTP 201

### What Worked

- Messgroessen VOR dem Bau festschreiben: MEM-02 wurde an "Rueckkehr zur Grundlast nach einem Indexlauf" gemessen statt an "Grundlast minus X", und ein Gate verbietet die bequemere Groesse im Quelltext, auch im Kommentar
- Fristgebundene Entscheide in die ERSTE Phase verankern, mit beiden Zweigen vorab fertig ausformuliert: der stable35-Entscheid war am Stichtag reiner Checklisten-Vollzug
- Owner-Deckel erneut eingehalten: 25,75 h / 2,98 USD verbraucht gegen freigegebene 46 h / 5,40 USD; die Anfahrt endete an Ablesestellen, nicht am Geld
- Vorbehalte, die mit dem Haken nicht verschwinden: jede Traceability-Zeile traegt ihren benannten Rest (z.B. Store-Rendering nicht nachgesehen, Haken haengt am zweiten Dispatch), nichts wurde stillschweigend rund gemacht
- Phase 16 mit 14 Plaenen in acht Wellen an einem Tag, weil jede Welle ihre Gates lokal gruen abschloss, bevor die naechste startete

### What Was Inefficient

- Die Token-Rotation vor der Einreichung feuerte doppelt, der erste Dispatch endete mit HTTP 401 (L-16-05); die Marke haette vor dem Setzen gegen die Schnittstelle geprueft werden muessen, was danach als Muster etabliert wurde (leerer Aufruf: 400 = gueltig, 401 = ueberholt)
- Der erste Fix des Flake-Stamms single-flight-zeit trug nicht (M-16-01); erst der zweite Fix ist unter Tag-Last gruen. Ein Flake-Fix ist erst belegt, wenn der Stamm unter echter Parallel-Last erneut gruen war
- Die Annahme, GitHub wende den paths-Filter auf Tag-Pushes an, stand in zwei Workflow-Kommentaren und ist falsch (L-16-04, mit zwei Laufnummern widerlegt); Kommentarfix wartet auf den naechsten Workflow-Plan
- Drei Debug-Sessions blieben ZUM ZWEITEN MAL formal offen, obwohl die Fixe laengst gemerged waren; erst der Milestone-Close hat sie gestempelt. Der Stempel gehoert an den Fix-Commit, nicht ans Milestone-Ende
- Die Sprachfall-Messung ohne Fremdbestand war auf der Box topologisch unmoeglich (der Korpus-Snapshot IST der Fremdbestand); die Nacherfuellung lief als Auflage A4 ueber den arm64-CI-Ast. Die Messfrage haette vor der Anfahrt gegen die Topologie geprueft werden koennen

### Patterns Established

- Messgroesse vor dem Bau festschreiben und die bequemere Groesse per Gate im Quelltext verbieten
- Abbild-Wechsel auf der Box per Digest statt ueber den wandernden :dev-Zeiger; der Baumhash entscheidet, nicht der Digest; --rm-data darf im Quelltext nicht ohne seine Zaehlung unmittelbar darueber stehen
- Zugangsmarken vor dem Setzen gegen die Schnittstelle pruefen (leerer Aufruf der Release-Route: 400 = gueltig, 401 = ueberholt)
- Fristgebundene Entscheide als eigener Plan in der ersten Phase, beide Zweige vorab ausformuliert
- Auflagen einer Abnahme im Wortlaut als Auftraege an die Folgephase notieren, nie als erledigt fuehren

### Key Lessons

1. Ein Haken in der Traceability-Tabelle darf einen Vorbehalt tragen, aber nie einen verstecken: die v1.2-Tabelle nennt bei vier Requirements den Rest, der mit dem Haken nicht verschwindet, und der Owner nahm genau deshalb ohne Rueckfragen ab
2. Sekundenketten mit externem Zustand (Token-Rotation, Store-Submission) brauchen eine Gegenprobe VOR der teuren Aktion, nicht danach
3. Eine Messfrage gehoert vor der Anfahrt gegen die Topologie geprueft: "ohne Fremdbestand messen" war auf einer Box, deren Korpus der Fremdbestand ist, keine Messung, sondern ein Widerspruch
4. Debug-Sessions beim Merge des Fixes auf resolved stempeln; das ist jetzt zweimal (v1.1 und v1.2) liegengeblieben und beide Male erst beim Close aufgefallen

### Cost Observations

- Modellmix: model_profile quality (Executor/Planner/Researcher opus, Checker/Verifier sonnet)
- AWS-Kosten des Milestones: 2,9831 USD Box-Laufzeit (25,75 h, eine Anfahrt) + Snapshot ~2,9 USD/Monat laufend (Owner-Entscheid: behalten)
- 8 Kalendertage fuer 63 Plaene (14.09. bis 21.09.); Phase 16 mit 14 Plaenen an einem Tag

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 7 (1-6 + 06.1) | 103 | Launch-Haertungsphase 06.1 als Muster etabliert; Audit-Gate je Phase |
| v1.1 | 5 (7-11) | 37 | Erste Phase mit CONTEXT.md (discuss-phase); Checkpoint-Plaene mit Kostendeckel; Bestandsaufnahme vor Neubau |
| v1.2 | 5 (12-16) | 63 | Messgroessen vor dem Bau festgeschrieben (Gate gegen die bequemere Groesse); fristgebundener Entscheid in Phase 1 verankert; eine Anfahrt fuer alle Belege |

### Cumulative Quality

| Milestone | Tests | Bemerkung |
|-----------|-------|-----------|
| v1.0 | ~1.750 Python + PHP-Suite | 51.961 Docs auf Zielhardware, 0 failed |
| v1.1 | ~2.000 Python + 185 PHP | 52.111 Docs ohne OOM; 6 CI-Workflows inkl. Fremdinstallation + Upgrade |
| v1.2 | 2.491 Python + PHP-Suite | 7/7 Tag-Laeufe gruen; Entladung belegt (377,5 MB Rueckkehr zur Grundlast); Audit 0 CRIT / 0 HIGH |

### Top Lessons (Verified Across Milestones)

1. Die Haertungsphase jenseits des Happy Path findet in jedem Milestone echte Produktfehler, die die Testsuite nicht fand (v1.0: 06.1-Befunde; v1.1: stumme Suche nach Minor-Upgrade, Sprachfallback; v1.2: ueberholte Zugangsmarke, nicht tragender Flake-Fix)
2. Owner-Checkpoints mit hartem Deckel (Kosten, Wortlaute, Einreichung) verhindern teure Alleingaenge, ohne die Autonomie der Wellen zu bremsen
3. Beweis-Tests, deren Rot-Faehigkeit per Mutation belegt ist, sind die einzigen, deren Gruen etwas bedeutet
4. Debug-Sessions gehoeren beim Merge des Fixes auf resolved gestempelt, nicht beim Milestone-Close (in v1.1 und v1.2 liegengeblieben)
