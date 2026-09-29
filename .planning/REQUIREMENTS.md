# Requirements: Findling Milestone v1.4 "Leistungsprofile"

**Defined:** 2026-09-27
**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten, ohne dass der Admin irgendetwas konfigurieren muss.
**Scope-Entscheid Owner (24./25.09., bestaetigt 27.09.2026):** BL-F04 als Kern von v1.4: Leistungsprofile mit Anteils-Formeln, Nebenlaeufigkeit als Kernfall (Einbettungsspur + N OCR-Slots), Hardware-Erkennung mit Vorschlag, Vorab-Pruefung vor dem Speichern, Modellwahl BLEIBT drin (gegen die Research-Empfehlung), keine App-Spaltung. Default bleibt das 4-GB-Versprechen.
**Grundlage:** .planning/research/BL-F04-vorarbeit-2026-09-25.md (+ Vorgaengerin BL-F04-worker-skalierung.md) und die Basiszahlen B1-B5 der Phase-22-Anfahrt (docs/performance.md); CI-Slot-Faktor F4 = 3,955, die Mehrkern-Skalierung ist real.

## v1.4 Requirements

### Leistungsprofile (PROF)

- [x] **PROF-01**: Admin waehlt eines von drei Profilen (Sparsam/Standard/Leistung); ein Profil ist eine Anteils-Formel an erkannten Kernen und Speicher mit Obergrenzen, keine feste Slotzahl (Slot-Regel aus Vorarbeit Abschnitt 3.1: `OCR-Slots = max(1, min(floor(Anteil_Kerne x C - r), floor((M_frei - Grundlinie - Reserve) / Kosten_je_Slot)))`)
- [x] **PROF-02**: Sparsam bleibt der Default und ist Wert fuer Wert gegen die heutigen Konstanten gepinnt (Test nach dem Muster test_config.py/INDEX_WORKERS); die Store-Messzahl wandert nicht
- [x] **PROF-03**: Der Weg des Profils in den Container ist per Owner-Tor entschieden (Wege A/B/C aus der Vorgaenger-Research 6.4); eine gesetzte Umgebungsvariable ueberstimmt das Profil (eine Wahrheit)

### Parallelitaet (PAR)

- [x] **PAR-01**: Die Einbettungsspur laeuft als eigener Nebenlaeufer (H1): eigener Anspruch mit Art-Filter (PHP-Route, KIND embed), beruehrt den Tantivy-Writer nicht, wirkt ab 2 Kernen
- [x] **PAR-02**: N OCR-Slots (H2): Semaphore, N Sandbox-Kinder mit je eigener Pipe und eigenem Zaehler, Sperre um IndexBatchWriter.add(), KIND_BATCH[ocr] >= N; die Zusagen "mindestens einmal ausliefern, hoechstens einmal indexieren" halten unter Parallelitaet
- [x] **PAR-03**: Ein Speicherwaechter drosselt Slots bei knapper cgroup; wiederholtes memory.events max oder ein OOM-Kill senkt das Profil selbsttaetig um eine Stufe, sichtbar gemeldet
- [x] **PAR-04**: IDX-08 neu gefasst: in Sparsam woertlich (OCR und Einbettung nie gleichzeitig), in Standard/Leistung als RAM-Bedingung des Speicherwaechters

### Hardware-Erkennung (HW)

- [x] **HW-01**: Der Container erkennt beim Start Kerne/Speicher/Architektur (cgroup-bewusst: process_cpu_count + cpu.max, memory.max sonst MemAvailable), meldet erkannt und vorgeschlagenes Profil ueber die Statusroute an die Adminseite und schaltet NICHTS um; bei Hardware-Schrumpfung faellt er selbsttaetig auf die groesste noch passende Stufe zurueck und sagt das auf der Seite

### Vorab-Pruefung (PRUEF)

- [ ] **PRUEF-01**: "Uebernehmen und pruefen" faehrt vor dem Speichern eine echte Probe (N-Slot-Probe am OCR-Pfad, RAM-Rechnung mit gemessenen Slot-Kosten, bei fp32-Wunsch Modell-Probe) und liefert ein Verdikt (passt / passt knapp / passt nicht, mit benannter Ursache); erst bei "passt" wird das Profil gespeichert. Die Probe wird vorher gegen die Grenze gerechnet (sonst ist die Probe selbst das OOM), es laeuft eine Probe gleichzeitig, mit Zeitdeckel, Route nur access_level ADMIN

### Modellwahl (MOD)

- [x] **MOD-01**: Die Vektor-Marke traegt die Gewichtspraezision (embedding_version-Erweiterung in store/vectors.py): ein int8/fp32-Wechsel desselben Modells loest den automatischen Vektor-Reindex aus statt still alte und neue Vektoren zu mischen; wird VOR jedem Modellschalter gebaut
- [x] **MOD-02**: Admin waehlt e5-small int8 (Default) oder fp32 als Teil des Leistungsprofils; der fp32-Lieferweg (ins Abbild vs. Nachladen, Risiko K7) faellt am Owner-Tor; waehrend des Vektor-Reindex antwortet die Suche lexikalisch weiter und die Seite zeigt den Zustand

### Admin-UI (UI)

- [ ] **UI-01**: Erste echte Settings-Flaeche: Profilauswahl (geschlossene Menge) plus Hinweisflaeche fuer Erkennung/Vorschlag/Verdikt, ADM-04 gewahrt (ein Auswahlfeld plus Hinweis, kein Erweitert-Bereich), Texte in allen acht Sprachkatalogen im Gleichstand (16 Dateien)

### Messung und Release (MESS/REL, Fortsetzung ab MESS-10/REL-04)

- [ ] **MESS-10**: Abnahme-Anfahrt am gebauten Produkt: RAM-Messung je Profilstufe auf echter Hardware, BEVOR die Settings-UI die Stufe anbietet (Owner-Auflage 24.09.); Rechenblatt + Kostendeckel VOR dem Boxstart zur Owner-Freigabe, Runbook-Disziplin (Cron-Intervall-Gate, Digest-Wechsel, Rohdaten committen)
- [ ] **REL-04**: v1.4.0 eingereicht: beide Apps in gleicher Version (PHP-Kopplung K6: KIND_BATCH/Art-Filter sind Companion-Release), Haertung + Audits wie gehabt, Store-Texte gate-konform mit Owner-Abnahme (inkl. Anteils-Aussage "Findling nimmt hoechstens X der Box" im Owner-Wortlaut)

## Future Requirements (deferred)

- Franzoesisches Koerperfeld (benannte Luecke seit v1.3)
- jina-v2-base-de oder andere Modelle mit fremder Dimension (Schemawechsel der vec0-Tabelle)
- Seiten-Parallelitaet innerhalb einer Datei (H4; fuer grosse Korpora deckt H2 dasselbe ab)
- Tantivy num_threads fuer den UMBAU-Weg (nur falls B6 zeigt, dass der Umbau einkernig und lang ist)
- Nachholweg fuer indexed(truncated) nach OCR_MAX_PAGES-Erhoehung
- F-23-04 (Phase-23-Backlog), idle-Guard EmbeddingModel.release() (Kandidat: Roadmap fuehrt ihn als Mitnahme-Kandidat in Phase 25, kein REQ; Plan-Schnitt entscheidet)

## Out of Scope

- App-Spaltung in zwei Store-Apps (Owner 25.09.: "wir spalten nicht"; doppelte Wartung, Entscheidungslast, Reindex-Zwang, ~95 % identische Codebasis)
- Zwang zu einem Profil oder Autoumschaltung nach oben (Default bleibt das 4-GB-Versprechen, Vorschlag statt Zwang)
- GPU-Stack/Torch (wuerde den Neupruefungs-Vorbehalt der Nicht-Spaltung ausloesen)
- Pro-Schiene (ISV-Entscheid 03.11.)
- Skalierung von tesseract ueber Threads (OMP_THREAD_LIMIT=1 bleibt; Skalierung nur ueber Prozesse/Slots)

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROF-01 | Phase 24 | Complete |
| PROF-02 | Phase 24 | Complete |
| PROF-03 | Phase 24 | Complete |
| MOD-01 | Phase 24 | Complete |
| HW-01 | Phase 24 | Complete |
| PAR-01 | Phase 25 | Complete |
| PAR-04 | Phase 25 | Complete |
| MOD-02 | Phase 25 | Complete |
| PAR-02 | Phase 26 | Complete |
| PAR-03 | Phase 26 | Complete |
| PRUEF-01 | Phase 27 | Pending |
| UI-01 | Phase 27 | Pending |
| MESS-10 | Phase 28 | Pending |
| REL-04 | Phase 29 | Pending |

**Coverage:** 14/14 v1.4-Requirements zugeordnet, keine Waisen, keine Doppelungen.

---
*Erstellt: 2026-09-27 aus BL-F04-Vorarbeit (25.09.) und Owner-Scope-Bestaetigung. Traceability: 2026-09-27 (Roadmap v1.4, Phasen 24 bis 29).*
