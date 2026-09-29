# Roadmap: Findling

## Milestones

- [x] **v1.0 Volltext, OCR und semantische Suche** -- Shipped 2026-09-07 (Phasen 1-6 + 06.1, Archiv: .planning/milestones/v1.0-ROADMAP.md)
- [x] **v1.1 Qualitaet und Effizienz** -- Shipped 2026-09-11 (Phasen 7 bis 11, Archiv: .planning/milestones/v1.1-ROADMAP.md)
- [x] **v1.2 Messbeleg und Ausbau** -- Shipped 2026-09-21 (Phasen 12 bis 16, Archiv: .planning/milestones/v1.2-ROADMAP.md)
- [x] **v1.3 Sprachausbau** -- Shipped 2026-09-27 (Phasen 17 bis 23, Archiv: .planning/milestones/v1.3-ROADMAP.md)
- [ ] **v1.4 Leistungsprofile** -- in Arbeit (Phasen 24 bis 29)

## Phases

<details>
<summary>v1.0 Volltext, OCR und semantische Suche (Phasen 1-6 + 06.1) -- SHIPPED 2026-09-07</summary>

Details im Archiv: .planning/milestones/v1.0-ROADMAP.md (103 Plaene, Store-Einreichung 1.0.0, Tags v1.0.0 bis v1.0.3)

</details>

<details>
<summary>v1.1 Qualitaet und Effizienz (Phasen 7-11) -- SHIPPED 2026-09-11</summary>

- [x] Phase 7: Gemeinsame Embedding-Engine (4/4 Plaene) -- completed 2026-09-08
- [x] Phase 8: Deutsche Komposita ohne Behelf (5/5 Plaene) -- completed 2026-09-08
- [x] Phase 9: Eigene Ergebnisseite (8/8 Plaene) -- completed 2026-09-09
- [x] Phase 10: Vergleichsmessung auf der AWS-Box (7/7 Plaene) -- completed 2026-09-10
- [x] Phase 11: Haertung und Store-Einreichung v1.1 (13/13 Plaene) -- completed 2026-09-11

Details im Archiv: .planning/milestones/v1.1-ROADMAP.md

</details>

<details>
<summary>v1.2 Messbeleg und Ausbau (Phasen 12-16) -- SHIPPED 2026-09-21</summary>

- [x] Phase 12: Messwerkzeug, Runbook und Terminentscheid (8/8 Plaene) -- completed 2026-09-16
- [x] Phase 13: Filter und Sortierung auf der Ergebnisseite (13/13 Plaene) -- completed 2026-09-19
- [x] Phase 14: Modell-Entladung im Leerlauf (12/12 Plaene) -- completed 2026-09-19
- [x] Phase 15: Messphase, eine Box-Anfahrt (16/16 Plaene) -- abgenommen 2026-09-21, Auflagen A1 bis A4 an Phase 16
- [x] Phase 16: Haertung und Store-Einreichung v1.2.0 (14/14 Plaene) -- completed 2026-09-21, v1.2.0 im Store (2x HTTP 201)

Details im Archiv: .planning/milestones/v1.2-ROADMAP.md

</details>

<details>
<summary>v1.3 Sprachausbau (Phasen 17-23) -- SHIPPED 2026-09-27</summary>

- [x] Phase 17: Owner-Tor und Analyseketten (8/8 Plaene) -- completed 2026-09-23
- [x] Phase 18: Schema, Marken und Umbauweg (12/12 Plaene) -- completed 2026-09-24
- [x] Phase 19: Frageseite freischalten (9/9 Plaene) -- completed 2026-09-25
- [x] Phase 20: UI-Kataloge es/it/nl/pt (9/9 Plaene) -- completed 2026-09-25
- [x] Phase 21: Niederlaendische Komposita (9/9 Plaene) -- completed 2026-09-25
- [x] Phase 22: Messanfahrt BL-F03 (13/13 Plaene) -- completed 2026-09-26
- [x] Phase 23: Haertung und Store-Einreichung 1.3.0 (9/9 Plaene) -- completed 2026-09-27, v1.3.0 im Store (2x HTTP 201)

Details im Archiv: .planning/milestones/v1.3-ROADMAP.md

</details>

### v1.4 Leistungsprofile (in Arbeit)

**Milestone-Ziel:** Findling passt seine Geschwindigkeit der Hardware an: Wer mehr als die 4-GB-Referenzbox hat, bekommt per Profil-Opt-in Parallelität (Einbettungsspur plus N OCR-Slots), das 4-GB-Versprechen bleibt der unveränderte Default. Abschluss: Store-Release 1.4.0.

- [x] **Phase 24: Owner-Tor, Profil-Gerüst und Marken-Reparatur** - Grundsatzentscheide schriftlich, dann Profile als Anteils-Formel, Hardware-Erkennung mit Vorschlag, Sparsam gepinnt, Vektor-Marke kennt die Gewichtspräzision (completed 2026-09-28)
- [x] **Phase 25: Einbettungsspur und Modellwahl** - Einbettung als eigener Nebenläufer (H1) mit PHP-Art-Filter, IDX-08 neu gefasst, int8/fp32 wählbar (completed 2026-09-28)
- [x] **Phase 26: N OCR-Slots und Speicherwächter** - Mehrere OCR-Slots (H2) mit KIND_BATCH-Companion, Drosselung und selbsttätiger Profil-Rückstufung (completed 2026-09-29)
- [x] **Phase 27: Vorab-Prüfung und Settings-Oberfläche** - Erste echte Settings-Fläche mit "Übernehmen und prüfen" (N-Slot-Probe, Verdikt), acht Sprachkataloge (completed 2026-09-29)
- [ ] **Phase 28: Abnahme-Anfahrt** - RAM-Messung je Profilstufe am gebauten Produkt auf echter Hardware, Deckel vorab freigegeben
- [ ] **Phase 29: Härtung und Store-Einreichung 1.4.0** - Launch-Härtung der Parallelpfade, Audits, signiertes App-Paar im Store

**Ausführungsreihenfolge und Sicherheitsbedingung:** 24 -> 25 -> 26 -> 27 -> 28 -> 29, streng seriell, und zwar aus Sicherheitsgründen, nicht aus Aufwandsgründen. Die Marken-Reparatur (MOD-01) steht in Phase 24 VOR jedem Modellschalter (Phase 25), sonst mischen sich int8- und fp32-Vektoren still (K8). H1 (Phase 25) kommt vor H2 (Phase 26), weil er den Tantivy-Writer nicht berührt und auf jeder Box ab 2 Kernen wirkt. Die N-Slot-Probe der Vorab-Prüfung (Phase 27) setzt N Slots voraus (Phase 26). Die Abnahme-Anfahrt (Phase 28) misst das gebaute Produkt, bevor ein Release die Stufen anbietet (Owner-Auflage 24.09.). PHP-Kopplung (K6): Art-Filter am Anspruch reist mit Phase 25, KIND_BATCH/LOCK_TIMEOUTS mit Phase 26, beide Companion-Änderungen erscheinen erst mit dem gemeinsamen Release 1.4.0. Nach jeder Phase Security-, Bug- und Performance-Audit (Owner-Regel 15.08.), Befunde vor Phasenabschluss fixen.

**Rückfall bei Killer K1** (Skalierung bleibt aus, CI-4-Kern-Faktor unter 1,5): Phase 26 schrumpft auf das Belegen und Dokumentieren des Befunds, v1.4 liefert Profil-Gerüst, Hardware-Vorschlag, Einbettungsspur und Vorab-Prüfung ohne N-Slot-Teil (Vorarbeit Abschnitt 5). Die Entscheidung fällt datiert vor dem Bau von H2.

## Phase Details

### Phase 24: Owner-Tor, Profil-Gerüst und Marken-Reparatur

**Goal**: Die Grundsatzentscheide des Milestones sind schriftlich gefallen, bevor Code sie implizit trifft; danach kennt der Container Profile als Anteils-Formel an der erkannten Hardware, schlägt ein Profil vor, ohne umzuschalten, und die Vektor-Marke erkennt einen Präzisionswechsel.
**Depends on**: Phase 23 (v1.3.0 im Store)
**Requirements**: PROF-01, PROF-02, PROF-03, MOD-01, HW-01
**Success Criteria** (was WAHR sein muss):

  1. Ein datierter Owner-Entscheid liegt vor zu: Weg des Profils in den Container (Wege A/B/C aus der Vorgänger-Research 6.4), Anteile je Profil im Owner-Wortlaut (einschließlich des späteren Store-Satzes "Findling nimmt höchstens X der Box") und fp32-Lieferweg (ins Abbild oder Nachladen, K7). Vor diesem Entscheid wird kein Code geschrieben, der Profilweg, Anteile oder Lieferweg berührt.
  2. Ein Admin setzt eines der drei Profile Sparsam/Standard/Leistung über den entschiedenen Weg, und der Container meldet die daraus berechneten Werte (Slotzahl nach der Regel aus Vorarbeit 3.1, mit Obergrenzen); eine gesetzte Umgebungsvariable überstimmt das Profil sichtbar (eine Wahrheit).
  3. Ohne jedes Zutun läuft Sparsam: der Pin-Test vergleicht Sparsam Wert für Wert mit den heutigen Konstanten (Muster test_config.py/INDEX_WORKERS), und die Store-Messzahl sowie das Gate test_store_metadata.py bleiben unverändert.
  4. Die Statusroute meldet erkannte Kerne, Speicher und Architektur cgroup-bewusst (process_cpu_count plus cpu.max, memory.max sonst MemAvailable) und das vorgeschlagene Profil, ohne etwas umzuschalten; bei simulierter Hardware-Schrumpfung fällt der Container selbsttätig auf die größte noch passende Stufe zurück und meldet das.
  5. Ein int8/fp32-Wechsel desselben Modells löst den automatischen Vektor-Reindex aus statt Vektoren still zu mischen; eine Bestandsinstallation mit alter Marke (ohne Präzisionsangabe) wird als int8 erkannt und NICHT neu eingebettet (Upgrade-Test).

**Plans**: 6 plans in 3 Wellen

Plans:
**Wave 1**

- [x] 24-01-PLAN.md , Vektor-Marke mit Gewichtspräzision, int8 bytegleich, Upgrade-Test (MOD-01), Welle 1
- [x] 24-02-PLAN.md , Profilkonstanten, Überstimmungsleser, cgroup-Hardware-Erkennung, Gleichstand info.xml (PROF-01, PROF-03, HW-01), Welle 1
- [x] 24-04-PLAN.md , PHP: SettingsService::profile() und OCS-Route GET /profile (PROF-03), Welle 1

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 24-03-PLAN.md , Profil-Resolver, Prozess-Zustand, Sparsam-Pin (PROF-01, PROF-02, HW-01), Welle 2

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 24-05-PLAN.md , Profilabfrage je Poller-Runde, fehlertolerant, Gleichstand PHP/Python (PROF-03), Welle 3
- [x] 24-06-PLAN.md , Hardware im Lifespan, Profilblock in /status, Owner-Tor in docs/profiles.md (HW-01, PROF-01, PROF-03), Welle 3

**Research-Flag**: ja (Wege A/B/C gegen lru_cache in config.py und AppAPI-Umgebungsmechanik; cgroup-Erkennung unter HaRP ungeprüft, Annahme A9)

### Phase 25: Einbettungsspur und Modellwahl

**Goal**: Auf Boxen mit Profil Standard oder Leistung läuft die Einbettung als eigener Nebenläufer neben der OCR, ohne den Tantivy-Writer zu berühren, und der Admin kann zwischen e5-small int8 und fp32 wählen, während die Suche durch den Vektor-Reindex hindurch weiter antwortet.
**Depends on**: Phase 24 (Profil-Gerüst und Marken-Reparatur müssen stehen)
**Requirements**: PAR-01, PAR-04, MOD-02
**Success Criteria** (was WAHR sein muss):

  1. In Standard/Leistung holt ein eigener Nebenläufer Einbettungsarbeit über einen eigenen Anspruch mit Art-Filter (PHP-Route, KIND embed, Companion-Änderung in dieser Phase) und schreibt nur in vectors.db; in Linux-CI auf 2 und mehr Kernen überlappt die Einbettung nachweislich mit laufender OCR.
  2. In Sparsam laufen OCR und Einbettung nachweislich nie gleichzeitig (IDX-08 wörtlich, Test); in Standard/Leistung startet die Einbettungsspur parallel zur OCR nur, solange die RAM-Bedingung gegen die cgroup-Grenze erfüllt ist, sonst wartet sie.
  3. Ein Neustart oder Kill mitten in beiden Spuren verliert keine Warteschlangenzeile und bettet nichts doppelt ein; gleichzeitige Zugriffe auf state.db führen nicht zu Fehlerverdikten.
  4. Der Admin wählt im Profil int8 (Default) oder fp32; nach dem Wechsel läuft der Vektor-Reindex, die Suche antwortet lexikalisch weiter und die Adminseite zeigt den Zustand; fp32 kommt über den am Tor entschiedenen Lieferweg, und eine Box ohne fp32-Wunsch zahlt dafür keinen Laufzeitspeicher.

**Plans**: 12 plans in 6 Wellen

Plans:
**Wave 1**

- [x] 25-01-PLAN.md , fp32-Laufzeitspeicher messen, Owner lädt das fp32-Asset als unveränderliches Release hoch (MOD-02), Welle 1, Checkpoint
- [x] 25-02-PLAN.md , Idle-Guard in release(), Gewichtspfad und ladefreier Engine-Tausch, IN-02 Marke ohne Default (MOD-02, PAR-01), Welle 1
- [x] 25-03-PLAN.md , PHP: Spur-Filter lane mit Echo, Präzisionsschlüssel model_precision in der Profilantwort (PAR-01, MOD-02), Welle 1
- [x] 25-04-PLAN.md , PHP: Statuszeile Präzision plus Neueinbettung, acht Kataloge (MOD-02, D-25-13), Welle 1

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 25-05-PLAN.md , Container-Draht: claim(lane), Echo, companion_choice, Präzisionsnamen, Gleichstand PHP/Python, Fakes (PAR-01, MOD-02), Welle 2

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 25-06-PLAN.md , fp32-Beschaffung (fetch_release_asset, embed/weights.py) und memory_guard (MOD-02, PAR-04), Welle 3
- [x] 25-07-PLAN.md , Refactor: EmbeddingTrack mit eigenen Verbindungen und Lese-Handle, verhaltensgleich (PAR-01), Welle 3
- [x] 25-08-PLAN.md , Präzisions-Automat, fp32-Term in der Slotformel, Konstanten der RAM-Bedingung (MOD-02, PAR-04), Welle 3

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 25-09-PLAN.md , EmbedRunner, Spurentscheid, IDX-08 in Sparsam, RAM-Bedingung, Abbruchsemantik, Tests T1 bis T8 (PAR-01, PAR-04), Welle 4

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 25-10-PLAN.md , Lifespan: zweiter Task, Abbau mit Zeilenrückgabe, Rebuild, Freigabe über den Track (PAR-01, PAR-04), Welle 5
- [x] 25-11-PLAN.md , Präzision verdrahtet: Startzustand, Beschaffung, Engine-Tausch, Rückweg mit Löschen (MOD-02), Welle 5

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 25-12-PLAN.md , Status model/lane, IN-03, Doku inklusive Offline-Weg, letzte Pin-Messung (MOD-02, PAR-01, PAR-04), Welle 6

**Research-Flag**: ja (Abbruchsemantik zweier Nebenläufer, state.db-Kollisionen, Art-Filter am PHP-Anspruch)
**Mitnahme-Kandidat (kein REQ)**: idle-Guard für EmbeddingModel.release() aus dem Phase-23-Backlog; mit einem zweiten Nebenläufer auf der geteilten Engine wird er hier akut, der Plan-Schnitt prüft die Aufnahme.

### Phase 26: N OCR-Slots und Speicherwächter

**Goal**: Auf Mehrkern-Boxen teilt sich die OCR-Spur auf N Slots auf, die Zusagen "mindestens einmal ausliefern, höchstens einmal indexieren" halten unter Parallelität, und ein Speicherwächter bremst, bevor der Container stirbt.
**Depends on**: Phase 25 (Einbettungsspur und RAM-Bedingung stehen)
**Requirements**: PAR-02, PAR-03
**Success Criteria** (was WAHR sein muss):

  1. In Standard/Leistung lesen N OCR-Slots gleichzeitig (Semaphore, N Sandbox-Kinder mit je eigener Pipe und eigenem Zähler, Sperre um IndexBatchWriter.add()); der Anspruch liefert mindestens N OCR-Zeilen (KIND_BATCH[ocr] >= N, Sperrfrist-Ableitung neu gefasst, Companion-Änderung in dieser Phase).
  2. Ein Kill mitten in einer halben Staffel mit N >= 4 und der anschließende Neustart führen dazu, dass jede Datei genau einmal im Index steht und keine Zeile verloren ist (Test in Linux-CI).
  3. Der Durchsatzfaktor N Slots gegen Sparsam ist auf dem arm64-CI-Runner gemessen und dokumentiert (Rauschgrenze 1,05 aus Vorarbeit 2.5); Sparsam liest weiterhin mit genau einem Slot, der Pin-Test bleibt grün.
  4. Bei knapper cgroup drosselt der Speicherwächter die Slotzahl; wiederholtes memory.events max oder ein OOM-Kill senkt das Profil selbsttätig um eine Stufe, und Statusroute und Adminseite nennen Stufe und Ursache.

**Plans**: 14 plans in 6 Wellen

Plans:
**Wave 1**

- [x] 26-01-PLAN.md , Kind-Härtung nice 10 und oom_score_adj 1000, ChildKilled/EngineKilled, halt() (PAR-02, PAR-03, D-26-11, D-26-12, D-26-16), Welle 1
- [x] 26-02-PLAN.md , PHP: KIND_BATCH_INDEX_LANE ocr 32 nur im Lane index, profile_confirmed in der Profil-Route (PAR-02, PAR-03, D-26-04/05/13/14), Welle 1
- [x] 26-03-PLAN.md , Zeilen je Slot in config, memory_events, guard.py (Drossel, Eskalation, Kappe, Token), Kappe in profile.effective (PAR-02, PAR-03), Welle 1
- [x] 26-05-PLAN.md , PHP-Adminseite: Wächter-, Rückweg- und Drosselzeile, acht Kataloge (PAR-03, D-26-01/02/04), Welle 1

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 26-04-PLAN.md , Writer-Sperre, SlotPool und SlotGate mit eigenem Executor, Pins nach Welle 1 (PAR-02), Welle 2
- [x] 26-07-PLAN.md , embed_slots 2 in Leistung wirksam, Sperren um Chunker und Schreibaufrufe (PAR-02, D-25-12), Welle 2
- [x] 26-08-PLAN.md , Status: GuardReport im Vertrag der Adminseite, Vertragstest (PAR-03), Welle 2

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 26-06-PLAN.md , Poller-Staffel unter N Slots: Zeilenbeschnitt, Tasks, Barriere; confirmed und Paritätstests (PAR-02, PAR-03, D-26-05/06/07/13/14), Welle 3

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 26-09-PLAN.md , Drossel je Runde, Kill-Meldung, Solo-Wiederholung, Mehr-Slot-Merker, Token-Abgleich (PAR-02, PAR-03, D-26-02/16), Welle 4
- [x] 26-10-PLAN.md , Wächter-Task mit Persistenz in state.db, Unrein-Ende, Lifespan (PAR-03, D-26-01/03/04/15/16), Welle 4

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 26-11-PLAN.md , Kill-Test beider Fälle in Linux-CI mit N = 4 (PAR-02, PAR-03, D-26-08, SC2), Welle 5
- [x] 26-12-PLAN.md , Messleiter 1/2/4 (slot_ladder.py, measure.yml) und Doku der Phase (PAR-02, PAR-03, D-26-09, SC3), Welle 5
- [x] 26-13-PLAN.md , Live-Latenzprobe nice auf dem nc35-Harness mit Owner-Abnahme (PAR-02, D-26-12), Welle 5, Checkpoint

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 26-14-PLAN.md , Push-Entscheid, CI-Belege einsammeln (SC2, SC3, PHPUnit), Owner-Abnahme (PAR-02, PAR-03), Welle 6, Checkpoint

**Research-Flag**: ja (OOM-Kette R1, Abbruch halber Staffeln, Sperrfristen bei KIND_BATCH[ocr] = 2N)

### Phase 27: Vorab-Prüfung und Settings-Oberfläche

**Goal**: Der Admin sieht auf einer ersten echten Settings-Fläche erkannte Hardware, Vorschlag und Verdikt, und ein Profil wird erst gespeichert, nachdem eine echte Probe auf DIESER Box "passt" gesagt hat.
**Depends on**: Phase 26 (die N-Slot-Probe setzt N Slots voraus)
**Requirements**: PRUEF-01, UI-01
**Success Criteria** (was WAHR sein muss):

  1. Die Adminseite zeigt ein Auswahlfeld mit genau den drei Profilen und eine Hinweisfläche mit erkannten Kernen/Speicher, vorgeschlagenem Profil und den Knöpfen "Übernehmen und prüfen" und "Bei Sparsam bleiben"; ohne Klick bleibt Sparsam, einen Erweitert-Bereich gibt es nicht (ADM-04).
  2. "Übernehmen und prüfen" fährt eine echte Probe (N-Slot-Probe am OCR-Pfad mit mitgelieferter synthetischer Scanseite, RAM-Rechnung mit gemessenen Slot-Kosten, bei fp32-Wunsch Modell-Probe) und zeigt "passt", "passt knapp" oder "passt nicht" mit benannter Ursache; gespeichert wird nur bei "passt".
  3. Die Probe wird vor dem Start gegen die Speichergrenze gerechnet und kann selbst kein OOM auslösen; es läuft höchstens eine Probe gleichzeitig, mit Zeitdeckel, und ein Nicht-Admin erreicht Probe- und Profilroute nicht (access_level ADMIN, Test).
  4. Alle neuen Texte stehen in allen acht Sprachkatalogen (16 Dateien) im Gleichstand, die Katalog-Gates sind grün.

**Plans**: 16 plans in 7 Wellen
**UI hint**: yes (ui-phase-Gate: UI-SPEC vor dem Plan-Schnitt, Projektkonvention)

Plans:
**Wave 1**

- [x] 27-01-PLAN.md , UI-SPEC-Delta D-27-20 und SC1-Wortlaut "Bei Sparsam bleiben" mit Owner-Bestätigung (UI-01, PRUEF-01, D-27-11/20), Welle 1, Checkpoint
- [x] 27-02-PLAN.md , probe.py: Codes, Snapshot, Rechnung mit Vorab-Toren, Haltesignal, Deckel, Scanseite mit Digest-Pin (PRUEF-01, D-27-06/07/08), Welle 1
- [x] 27-03-PLAN.md , IN-01 atomarer Wächter-Snapshot, IN-02 Submit unter Sperre, shed_idle, Escalation.rebase (PRUEF-01, D-27-19), Welle 1
- [x] 27-04-PLAN.md , PHP: SettingsService (profileStored, needsProbe, saveProfile, Probe-Ablage), ExAppService adminSend/adminState (PRUEF-01, UI-01, D-27-09), Welle 1

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 27-05-PLAN.md , Indexierungs-Pause in Poller und EmbedRunner, Wächter-Aussetzung während der Probe (PRUEF-01, D-27-05/15), Welle 2
- [x] 27-06-PLAN.md , fp32-Modellprobe im gehärteten Spawn-Kind (PRUEF-01, D-27-02), Welle 2
- [x] 27-07-PLAN.md , ProbeService mit Commit-Bindung, ProfileSettingsController mit drei Admin-Routen, Gate B (PRUEF-01, UI-01, D-27-04/08/10/12), Welle 2
- [x] 27-08-PLAN.md , AdminViewService: Token raus, guardConfirmable, Profil-, Probe-, Env- und Reindex-Felder (UI-01, D-27-12/14/18), Welle 2

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 27-09-PLAN.md , Probe-Orchestrator probe_run: Einzelflug, Pause, Download, Messteil, Aufräumen, Neustart (PRUEF-01, D-27-02/04/06/07/14/16/17), Welle 3
- [x] 27-10-PLAN.md , Template und CSS: Block Leistungsprofil, occ-Zeile raus, SC1/ADM-04-Gates (UI-01, D-27-01/03/11/12), Welle 3

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 27-11-PLAN.md , Container: Router /probe und /probe/state (ADMIN), Statusblock probe, model.chunks, Lifespan (PRUEF-01), Welle 4
- [x] 27-12-PLAN.md , admin.js: Probe-Start, Poll 2000 ms, Verdikt, Abwärtswege, Maps, Fokus (UI-01, PRUEF-01, D-27-01/03/08/09), Welle 4

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 27-13-PLAN.md , Acht Kataloge (16 Dateien) im Gleichstand, Vollständigkeits-Gate (UI-01, SC4, D-27-20), Welle 5
- [x] 27-14-PLAN.md , Doku (occ ohne Probe, D-27-13) und Live-Nicht-Admin-Schritt in integration.yml (SC3), Welle 5

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 27-15-PLAN.md , Live-Lauf auf dem nc35-Harness mit Owner-Abnahme der Fläche (PRUEF-01, UI-01), Welle 6, Checkpoint

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 27-16-PLAN.md , Push-Entscheid, CI-Belege, Owner-Abnahme der Phase (PRUEF-01, UI-01), Welle 7, Checkpoint

### Phase 28: Abnahme-Anfahrt

**Goal**: Für jede Profilstufe steht eine auf echter Hardware gemessene RAM-Spitze und ein Durchsatz des gebauten Produkts fest, bevor ein Release die Stufe anbietet.
**Depends on**: Phase 27 (gebautes Produkt mit allen Profilen und Probe)
**Requirements**: MESS-10
**Success Criteria** (was WAHR sein muss):

  1. Rechenblatt und Kostendeckel lagen VOR dem Boxstart beim Owner und sind datiert freigegeben; die Anfahrt bleibt unter dem Deckel.
  2. Für Sparsam, Standard und Leistung stehen gemessene RAM-Spitze und Erstindex-Durchsatz auf Referenzbox und Mehrkern-Box in docs/performance.md, mit committeten Rohdaten; Sparsam weicht nicht von der Store-Messzahl ab.
  3. Die Runbook-Disziplin ist eingehalten und belegt: Cron-Intervall-Gate, Digest-Wechsel, Abbau nach Runbook.
  4. Die gemessenen Slot-Kosten fließen in Formel und Probe zurück; eine Stufe, deren Messung die Rechnung nicht trägt, wird korrigiert oder im Release nicht angeboten (Owner-Entscheid dokumentiert).

**Plans**: 14 plans in 9 Wellen

Plans:
**Wave 1**

- [x] 28-01-PLAN.md , Teilkorpus-Regel, Rechenblatt, Slot-Kosten-Auswertung, Ablauf mit Erwartungen je Zelle (MESS-10), Welle 1
- [ ] 28-02-PLAN.md , Zelle, Probe über die Produktroute, Kette mit Deckel-Prüfung und Sicherheitstimer (MESS-10), Welle 1
- [ ] 28-03-PLAN.md , aws_box.sh Satztabelle je Typ und SG-Schonung, Typwechsel mit Zieltyp (MESS-10), Welle 1
- [ ] 28-04-PLAN.md , Runbook x86/USD-Deckel/Abbau bis null Snapshots, lokale x86-Vorprobe (MESS-10), Welle 1

**Wave 2**

- [ ] 28-05-PLAN.md , Owner-Tor C1: Vorbedingungen, Rechenblatt mit Tagessätzen, datierte Deckel-Freigabe (SC1), Welle 2

**Wave 3 bis 6 (bezahlte Anfahrt, seriell)**

- [ ] 28-06-PLAN.md , Referenzbox m7g.large: Aufbau, Digest, Cron-Gate, Sparsam voll, Store-Messgröße, Zwischenstand, Welle 3
- [ ] 28-07-PLAN.md , Teilkorpus, drei Zellen m7g.large, drei Zellen m7g.4xlarge, Welle 4
- [ ] 28-08-PLAN.md , Owner-Tor x86, Aufbau und Machbarkeitstor c7a.xlarge, vier Zellen inkl. fp32, Welle 5
- [ ] 28-09-PLAN.md , c7a.2xlarge, c7a.4xlarge (fp32), c7a.8xlarge, Schlusszahlen, Welle 6

**Wave 7 bis 9**

- [ ] 28-10-PLAN.md , Boxabbau mit Owner-Bestätigung und Nachweis, Welle 7
- [ ] 28-11-PLAN.md , Auswertung, Bericht, Owner-Entscheide SC4/Store-Zahl, Kapitel docs/performance.md (SC2), Welle 7
- [ ] 28-12-PLAN.md , SC4: OCR_SLOT_COST_BYTES gemessen, Tests neu gerechnet, Baumhash-Pin, Texte, Welle 8
- [ ] 28-13-PLAN.md , Snapshot-Löschung mit Owner-Bestätigung, null Kosten belegt, Welle 8
- [ ] 28-14-PLAN.md , Push-Entscheid, CI-Belege, Owner-Abnahme, Welle 9
**Research-Flag**: nein (Runbook und Werkzeuge W1 bis W4 aus Phase 22 liegen vor)

### Phase 29: Härtung und Store-Einreichung 1.4.0

**Goal**: Findling 1.4.0 steht als signiertes App-Paar im Store, mit gehärteten Parallelpfaden und einer Anteils-Aussage im Owner-Wortlaut.
**Depends on**: Phase 28
**Requirements**: REL-04
**Success Criteria** (was WAHR sein muss):

  1. Die Launch-Härtung deckt die Rand- und Fehlerpfade der Parallelität ab (OOM mitten in N Slots, Kill beider Spuren, Hardware-Schrumpfung, Profilwechsel und Modellwechsel mitten im Vektor-Reindex, Umgebungsvariable gegen Profil) und ist grün; das Audit steht auf 0 CRIT / 0 HIGH, MEDIUM behoben, LOW dokumentiert entschieden.
  2. Fremdinstallation auf frischer Nextcloud und die Upgrade-Strecke 1.3.0 auf 1.4.0 sind Ende zu Ende grün; eine Bestandsinstallation landet in Sparsam ohne Neu-Einbettung und ohne Umbau.
  3. Beide Apps tragen 1.4.0 (PHP-Kopplung K6), sind signiert, und die Submission liefert 2x HTTP 201.
  4. Die Store-Texte sind gate-konform (Faktenliste, eine Messzahl) und enthalten die Anteils-Aussage im Owner-Wortlaut; der Owner hat sie vor der Abgabe abgenommen.

**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-6 + 06.1 (Archiv) | v1.0 | 103/103 | Complete | 2026-09-07 |
| 7-11 (Archiv) | v1.1 | 37/37 | Complete | 2026-09-11 |
| 12-16 (Archiv) | v1.2 | 63/63 | Complete | 2026-09-21 |
| 17-23 (Archiv) | v1.3 | 69/69 | Complete | 2026-09-27 |
| 24. Owner-Tor, Profil-Gerüst und Marken-Reparatur | v1.4 | 6/6 | Complete    | 2026-09-28 |
| 25. Einbettungsspur und Modellwahl | v1.4 | 12/12 | Complete    | 2026-09-28 |
| 26. N OCR-Slots und Speicherwächter | v1.4 | 14/14 | Complete    | 2026-09-29 |
| 27. Vorab-Prüfung und Settings-Oberfläche | v1.4 | 16/16 | Complete    | 2026-09-29 |
| 28. Abnahme-Anfahrt | v1.4 | 1/14 | In Progress|  |
| 29. Härtung und Store-Einreichung 1.4.0 | v1.4 | 0/? | Not started | - |

## Nach v1.3 (Wiedervorlage)

Offene Punkte, die bewusst NICHT in v1.3 lagen (Kandidaten fuer v1.4 und spaeter; v1.4-Fokus laut Owner-Linie: BL-F04 SPEED, Vorarbeit-Research und Basiszahlen liegen vor):

- Franzoesisches Koerperfeld (FR hat OCR und Katalog, aber keine lexikalische Kette; v1.4-Kandidat)
- Getrennte pt_BR/pt_PT-Wortlaute fuer die Suche selbst
- Niederlaendische Betonungsakzente als eigene `custom_stopword`-Liste
- Sortierung nach Name oder Groesse (Fast-Field, SCHEMA_VERSION-Sprung; koennte kuenftig mit einem ohnehin faelligen Umbau reisen)
- Mimetype-Gruppen aus `files.mime`, geplantes Vorwaermen
- Pro-Schiene (Index-Verschluesselung, External Storage; ISV-Entscheid 03.11.)
- Estnisch/Daenisch lexikalisch nicht moeglich (tantivy kennt keinen estonian-Stemmer): muss aktiv an die Buerokratt/OS2ai-Outreach-Spur kommuniziert werden, bevor dort falsche Erwartungen entstehen
- Snapshot `snap-03f1d1d9ad9262704`: Wiedervorlage beim Milestone-Close (Stand 27.09.: bleibt im Standard-Tier, dritter Behalten-Entscheid, ~2,85 USD/Monat; naechste Wiedervorlage beim v1.4-Close)
- Deferred aus Phase 23: F-23-04 (v1.4-Backlog), idle-Guard EmbeddingModel.release() (v1.4), IN-01..03 dokumentiert

Aktiver Blocker unabhaengig vom Milestone: Kill-Kriterium Nextcloud Conference (kuendigt Nextcloud eine Elasticsearch-freie Volltextsuche mit OCR an, wird das Projekt neu bewertet; geprueft 21.09.2026, nicht ausgeloest).

---
*Created: 2026-09-08. v1.1 archiviert: 2026-09-11. v1.2 archiviert: 2026-09-21. v1.3 archiviert: 2026-09-27. v1.4-Roadmap: 2026-09-27.*
