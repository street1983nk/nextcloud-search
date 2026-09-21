# Roadmap: Findling

## Milestones

- [x] **v1.0 Volltext, OCR und semantische Suche** -- Shipped 2026-09-07 (Phasen 1-6 + 06.1, Archiv: .planning/milestones/v1.0-ROADMAP.md)
- [x] **v1.1 Qualitaet und Effizienz** -- Shipped 2026-09-11 (Phasen 7 bis 11, Archiv: .planning/milestones/v1.1-ROADMAP.md)
- [ ] **v1.2 Messbeleg und Ausbau** -- Phasen 12 bis 16, gestartet 2026-09-14

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

### v1.2 Messbeleg und Ausbau (aktiv)

- [x] **Phase 12: Messwerkzeug, Runbook und Terminentscheid** - Werkzeug und Runbook stehen fest, bevor die bezahlte Box laeuft; stable35-Entscheid faellt fristgerecht (completed 2026-09-16)
- [x] **Phase 13: Filter und Sortierung auf der Ergebnisseite** - Nutzer grenzt Treffer nach Typ und Zeitraum ein und sortiert nach Datum, ohne die Semantik oder die Rechtegrenze zu verlieren
- [x] **Phase 14: Modell-Entladung im Leerlauf** - Container gibt beide Speicherhalter nach Leerlauf frei, hinter einem ab Werk ausgeschalteten Schalter (completed 2026-09-19)
- [x] **Phase 15: Messphase, eine Box-Anfahrt** - Wirkungsbeleg, Laststufen, Sprachfaelle und Wiederaufwaerm-Kosten in einer einzigen bezahlten Anfahrt (abgenommen 21.09.2026, Auflagen A1 bis A4 an Phase 16)
- [ ] **Phase 16: Haertung und Store-Einreichung v1.2.0** - Haertungen, Store-Texte, Upgrade-Beweis und Einreichung 1.2.0

**Bauordnung (harte Abhaengigkeiten, aus der Recherche uebernommen):** 12 vor 15 (ein waehrend der Anfahrt korrigiertes Skript entwertet seine eigene Messung), Backend vor PHP innerhalb von Phase 13 (`extra="forbid"` macht einen unbekannten Parameter zu HTTP 400 und damit zur stummen leeren Suche), 14 vor 15 (die eine Anfahrt muss die Entladung per Schalter A/B mitmessen), 16 zuletzt (fuehrt die Ergebnisse aus 13 bis 15 in Store-Texte und Upgrade-Beweis).

**Abweichung von der Recherche (begruendet):** Die Recherche schlaegt M2 (Backend Filter/Sortierung) und M3 (PHP-Ergebnisseite) als zwei Phasen vor. Beide sind hier zu Phase 13 zusammengefasst, weil jede einzelne FILT-Anforderung end-to-end formuliert ist (FILT-01/02/03 brauchen Backend-Feld UND Oberflaeche, FILT-05 die Paritaet ueber beide Haelften); eine Trennung wuerde dieselbe Anforderung auf zwei Phasen aufteilen und die 1:1-Zuordnung brechen. Die Granularitaet steht auf `coarse`, was die Buendelung zusaetzlich stuetzt. Die harte Reihenfolge Backend vor PHP bleibt als verbindliche Planreihenfolge innerhalb von Phase 13 erhalten.

### Termingebundene Entscheide

| Entscheid | Frist | Phase | Anmerkung |
|-----------|-------|-------|-----------|
| stable35-Fenster (HART-03, Entscheid v2-a) | **16.09.2026** | Phase 12 | Deshalb in der ersten Phase verankert, nicht in der Haertungsphase: die Frist liegt zwei Tage nach Milestone-Start und darf nicht auf das Milestone-Ende warten |
| Box-Zeit-/Kostendeckel neu gerechnet und freigegeben (MESS-05) | vor dem Start der Anfahrt | Phase 15 | Owner-Checkpoint, Anfahrt startet ohne Freigabe nicht |
| engineState-Wortwahl (`cold` wiederverwenden vs sechstes Wort `unloaded`, MEM-05) | vor dem Bau des Zustandsteils | Phase 14 | Owner-Checkpoint, echter Dissens zwischen den Recherchedokumenten, Kostenfolge sechs Stellen + vier Katalog-Gates |

## Phase Details

### Phase 12: Messwerkzeug, Runbook und Terminentscheid

**Goal**: Das Messwerkzeug, das Runbook und der fristgebundene Versionsentscheid stehen fest, bevor die eine bezahlte Box-Anfahrt beginnt
**Depends on**: Nichts (erste Phase des Milestones, keine Box noetig)
**Requirements**: MESS-04, MESS-06, HART-03
**Success Criteria** (was wahr sein muss):

  1. Die Fremdbestands-Vorpruefung misst ueber die Diagnose-Route (`ranked_sides`) und liefert Trefferzahlen oberhalb der alten Deckelung von 26, sodass die Schwelle 64 ueberhaupt pruefbar wird
  2. `aws_box.sh` baut ein Volume aus `snap-03f1d1d9ad9262704` ohne manuelle Nacharbeit auf der Box
  3. `docs/runbook-messbox.md` beschreibt Anfahrt, Messreihenfolge, Vergleichbarkeitsbedingungen (Korpus, Werkzeugstand, Instanztyp) und Abbau so vollstaendig, dass waehrend der Anfahrt kein Werkzeug mehr geaendert werden muss
  4. Das Cron-Intervall der Zielinstanz ist Pflichtfeld im Messprotokoll: ein Lauf ohne protokolliertes Intervall gilt als unvollstaendig
  5. Der stable35-Fenster-Entscheid ist bis zum 16.09.2026 getroffen und mit Begruendung dokumentiert

**Plans:** 8/8 plans complete

Plans:
**Wave 1**

- [x] 12-01-PLAN.md: stable35-Entscheid: beide Zweige vor der Frist ausformuliert
- [x] 12-03-PLAN.md: aws_box.sh restore (Volume aus Snapshot) plus Usage-Gate und lesende AWS-Proben
- [x] 12-04-PLAN.md: In-Container-Bestandssonde, neues Laufverzeichnis, Gate- und CI-Pfadfilter-Erweiterung

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 12-02-PLAN.md: stable35-Entscheid am 16.09.2026 vollziehen (terminlich isoliert, Owner-Checkpoint)
- [x] 12-05-PLAN.md: 98c-sprachfaelle.sh: Nachfolgefassung mit Rangsemantik und Abschnitt 3b
- [x] 12-07-PLAN.md: Runbook Teil 1: Geltung, Deckel-Rechenblatt, Vorbedingungen, Aufbau, Zustandspruefung

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 12-06-PLAN.md: Cron-Vorpruefung fail-closed (Konfigurations- und Wirkungszweig) plus Ablaufplan des Laufs

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 12-08-PLAN.md: Runbook Teil 2: Vergleichbarkeitsbedingungen, Messreihenfolge, Abbau, Kostenfuehrung

### Phase 13: Filter und Sortierung auf der Ergebnisseite

**Goal**: Nutzer grenzen Treffer nach Dateityp und Zeitraum ein und sortieren nach Datum, ohne die semantische Suchhaelfte oder die Rechtegrenze zu verlieren
**Depends on**: Nichts inhaltlich (parallel zu Phase 12 moeglich); intern verbindlich: Backend-Felder vor PHP-Oberflaeche
**Requirements**: FILT-01, FILT-02, FILT-03, FILT-04, FILT-05
**Success Criteria** (was wahr sein muss):

  1. Nutzer filtert auf der Ergebnisseite nach den sechs Typgruppen (PDF, Dokumente, Tabellen, Praesentationen, Bilder, Text); eine Paraphrasensuche findet unter aktivem Filter dasselbe Dokument wie ohne Filter, und gefilterte Seiten sind voll besetzt statt halbleer, weil der Filter vor dem Fusionsfenster wirkt
  2. Nutzer waehlt zwischen Relevanz (Standard), "Zuletzt geaendert" und "Aelteste zuerst"; gleiche Zeitstempel ergeben ueber `file_id` eine stabile Reihenfolge, und unter Sortierung wird kein Zeitstempel als Relevanz ausgewiesen
  3. Ein im Unified-Search-Dialog gesetzter Datumsfilter laesst Findling-Treffer stehen statt sie kommentarlos zu verwerfen; since/until grenzen auch auf der Ergebnisseite ein
  4. Filter und Sortierung stehen in der URL, sind sichtbar und einzeln entfernbar; jede Aenderung landet auf Seite 1, ein fremder Cursorpfad wird abgewiesen
  5. Der Paritaetstest deckt die neuen Parameter ab: kein gefilterter oder sortierter Treffer umgeht den ACL-Vorfilter oder den finalen PHP-Recheck

**Plans:** 12/13 plans executed

Plans:
**Welle 1**

- [x] 13-01-PLAN.md: Ein Filtervokabular und zwei Abfrageklauseln in query/rewrite.py

**Welle 2** *(wartet auf Welle 1)*

- [x] 13-02-PLAN.md: Sortierzweig und Filter auf der semantischen Haelfte in index/search.py

**Welle 3** *(wartet auf Welle 2)*

- [x] 13-03-PLAN.md: Wire-Felder, Grenzen, Moduswechsel und Gleichstands-Gate

**Welle 4** *(wartet auf Welle 3)*

- [x] 13-04-PLAN.md: SearchFilters und die zwei Ruempfe an den Container

**Welle 5** *(wartet auf Welle 4)*

- [x] 13-05-PLAN.md: Aenderungsdatum aus dem bestaetigten Knoten, Filter durch SearchService

**Welle 6** *(wartet auf Welle 5)*

- [x] 13-06-PLAN.md: Datumsfilter des Unified-Search-Dialogs (getSupportedFilters)
- [x] 13-07-PLAN.md: Geschlossene Adresswerte, Schnellbereiche in der Nutzer-Zeitzone, Filterobjekt der Seite

**Welle 7** *(wartet auf Welle 6)*

- [x] 13-08-PLAN.md: Adressen ohne Cursor, Fingerabdruck fp und die Bausteine der Filterleiste

**Welle 8** *(wartet auf Welle 7)*

- [x] 13-09-PLAN.md: Filterleiste, Datumszeile und der vierte Leerzustand im Template

**Welle 9** *(wartet auf Welle 8)*

- [x] 13-10-PLAN.md: Stil der Chips und die Text-Gates der neuen Bedienung
- [x] 13-12-PLAN.md: Paritaet: die neuen Parameter an der Rechtegrenze (FILT-05)

**Welle 10** *(wartet auf Welle 9)*

- [x] 13-11-PLAN.md: Kataloge: 23 Schluessel, Gate-Zahl 197, drei G2-Ausnahmen

**Welle 11** *(wartet auf Welle 10)*

- [ ] 13-13-PLAN.md: Abnahme: Gesamtlauf, Audit und die 17 Sichtproben (Owner-Checkpoint)

**UI hint**: yes

### Phase 14: Modell-Entladung im Leerlauf

**Goal**: Der Container gibt nach Leerlauf beide Speicherhalter frei, hinter einem ab Werk ausgeschalteten Schalter, ohne dass die erste Suche danach langsamer wird
**Depends on**: Nichts inhaltlich (unabhaengig von Phase 13), muss aber vor Phase 15 fertig sein
**Requirements**: MEM-01, MEM-02, MEM-03, MEM-04, MEM-05
**Success Criteria** (was wahr sein muss):

  1. Ein Vorprueflauf weist die tatsaechliche RSS-Rueckgabe (gc.collect + malloc_trim) auf Zielhardware aus, BEVOR die Funktion fertig gebaut wird; ein negatives Ergebnis wird als "gemessen, Ergebnis negativ" dokumentiert statt ausgeliefert
  2. Admin schaltet die Entladung ueber genau eine benannte Umgebungsvariable ein (TTL in Sekunden, 0 = aus), ab Werk aus, damit die eine Box-Anfahrt A/B messen kann
  3. Nach Ablauf der TTL sind beide Speicherhalter frei (Embedding-Engine UND Poller-Cutter/Tokenizer), belegt an der Messgroesse "Rueckkehr zur Grundlast nach einem Indexlauf"
  4. Die erste Suche nach einer Entladung liefert innerhalb der 1,5-Sekunden-Decke lexikalische Treffer und waermt das Modell im Hintergrund nach; kein cURL-error-28-Fall wie am 10.09.2026
  5. Die Admin-Seite zeigt den Engine-Zustand nach der neu formulierten one_load-Zusage (nie zwei Engines gleichzeitig, genau ein Laden je warmem Fenster), und das Gate prueft genau diese Zusage

**Owner-Checkpoint**: engineState-Wortwahl (MEM-05) ist am 19.09.2026 entschieden (Zweig B, sechstes Wort `unloaded`, siehe 14-CONTEXT.md) und in Plan 14-09 vollzogen. Die zwei weiteren Checkpoints sind beide gefallen: das Tor des Vorprueflaufs (14-02, freigegeben) und die Abnahme (14-12, "abgenommen" am 19.09.2026, einschliesslich des franzoesischen Wortlauts und des Vorschlagswerts 900 s). MEM-02 bleibt ausdruecklich offen: sein Beleg entsteht auf der Box der Phase 15.

**Plans:** 12/12 plans executed

Plans:
**Welle 1**

- [x] 14-01-PLAN.md: Vorprueflauf-Werkzeug, Erwartung vor dem Lauf, Messschritt E in measure.yml

**Welle 2** *(wartet auf Welle 1; DAS TOR DER PHASE)*

- [x] 14-02-PLAN.md: Vorprueflauf fahren, Bericht, Owner-Tor (negativ beendet die Phase)

**Welle 3** *(wartet auf das Tor)*

- [x] 14-03-PLAN.md: FINDLING_EMBED_IDLE_RELEASE_SECONDS, eigener Leser, sechzehnte Variable
- [x] 14-04-PLAN.md: Poller: busy-Property und release_cutter (der groessere Halter)
- [x] 14-05-PLAN.md: embed/model.py: Uhr, Aktivitaetszaehler, release, malloc_trim, may_load

**Welle 4** *(wartet auf Welle 3)*

- [x] 14-06-PLAN.md: embed/engine.py: query_may_load, release_if_idle, warm und das Single-Flight

**Welle 5** *(wartet auf Welle 4)*

- [x] 14-07-PLAN.md: Die dritte Lifespan-Aufgabe, beide Halter je Takt
- [x] 14-08-PLAN.md: Degradationsnaht auf den zwei Nutzerrouten und das Nachwaermen

**Welle 6** *(wartet auf Welle 5)*

- [x] 14-09-PLAN.md: Das sechste Wort `unloaded`: Container, PHP, sechs Kataloge, admin-page.md
- [x] 14-10-PLAN.md: one_load-Zusage neu, vierte Phase, zwei Mutationsfaelle, resilience.yml

**Welle 7** *(wartet auf Welle 6)*

- [x] 14-11-PLAN.md: embeddings.md, performance.md und das Runbook der Box-Anfahrt

**Welle 8** *(wartet auf Welle 7)*

- [x] 14-12-PLAN.md: Abnahme: Gesamtlauf, Audit-Durchgang, sieben Sichtproben (Owner-Checkpoint, abgenommen 19.09.2026)

### Phase 15: Messphase, eine Box-Anfahrt

**Goal**: Die eine bezahlte Anfahrt liefert alle offenen Messbelege des Milestones und vollzieht dabei das Runbook zum ersten Mal
**Depends on**: Phase 12 (Werkzeug und Runbook fest), Phase 14 (Schalter fuer den A/B-Beleg); Phase 13 steht, und die Sortierung bekommt nach dem Owner-Entscheid vom 19.09.2026 einen eigenen Messblock (D-01)
**Requirements**: MESS-05
**Success Criteria** (was wahr sein muss):

  1. Der Zeit-/Kostendeckel ist vor dem Start neu gerechnet und vom Owner freigegeben (mindestens 31 h / rund 3,59 USD oder bewusst verkleinerter Teilkorpus); ohne Freigabe startet die Anfahrt nicht
  2. Der DI-10-04-Wirkungsbeleg liegt als Volllauf gegen den Korpus-Snapshot mit Top-up-Fix vor, mit protokolliertem Cron-Intervall und Vergleichbarkeitsbedingungen
  3. Die vier regressiven Laststufen sind untersucht und je Stufe entschieden: behoben, erklaert oder bewusst hingenommen
  4. Die Sprachfall-Messung laeuft ohne den 52.111er-Fremdbestand und liefert Zahlen ueber der bisherigen Deckelung (DI-10-02/DI-11-01, neue Messgroesse)
  5. Die Wiederaufwaerm-Kosten der Entladung sind gemessen und ausgewiesen (warm/kalt, mit/ohne Seitencache, A/B ueber den MEM-01-Schalter); die Box ist danach wieder abgebaut

**Plans:** 16/16 plans complete

**Welle A, ohne Box-Zeit** *(Welle 1 bis 6)*

- [x] 15-01-PLAN.md: Elf Werkzeuge byteweise uebernehmen, Kopie-Waechter
- [x] 15-02-PLAN.md: Runbook: Deckel neu gerechnet (46 h / 5,40 USD), Block 13b Abbildwechsel, drop_caches, Schritte 6b und 8b
- [x] 15-03-PLAN.md: 95b-wiederaufwaermen.sh, vier Auspraegungen, Abbrueche 29 bis 31
- [x] 15-04-PLAN.md: 94b-grundlast-rueckkehr.sh, der MEM-02-Block
- [x] 15-05-PLAN.md: 99c-filter-sortierung.sh, der Owner-Messblock D-01
- [x] 15-06-PLAN.md: 92b-wechsel.sh, Abbildwechsel per Digest mit Baumhash-Beweis
- [x] 15-07-PLAN.md: 00-ablauf.md auf zehn Schritte, Erwartungen E8 bis E14, neun Vorbedingungen

**Welle B, der Owner-Checkpoint** *(Welle 7)*

- [x] 15-08-PLAN.md: Deckelfreigabe mit Datum (blockierend; ohne sie startet nichts)

**Welle C, die begleitete Anfahrt** *(Welle 8 bis 13)*

- [x] 15-09-PLAN.md: Aufbau Bloecke 1 bis 13 plus Abbildwechsel
- [x] 15-10-PLAN.md: Zustandspruefung, Abbruchtor, Nullstandsbeleg, Bestandssonde
- [x] 15-11-PLAN.md: Volllauf detached mit beiden Cron-Zweigen
- [x] 15-12-PLAN.md: Laststufen mit je einem Verdikt, Filter- und Sortierblock, Sprachfaelle
- [x] 15-13-PLAN.md: Wiederaufwaerm-A/B, MEM-02-Block, Entscheid zum Vorschlagswert 900 s
- [x] 15-14-PLAN.md: Endmessungen, Kostenzeilen, Abbau mit Tag-Sweep

**Welle D, nach dem Abbau** *(Welle 14 bis 15)*

- [x] 15-15-PLAN.md: Bericht, Runbook-Nachtraege, sechs Pruefsummen-Waechter
- [x] 15-16-PLAN.md: performance.md, Audit der Phase, MESS-05 und MEM-02, Abnahme (Owner-Checkpoint, abgenommen 21.09.2026 mit Auflagen; Kriterium 4 nicht erfuellt, Nacherfuellung = Auflage A4)

### Phase 16: Haertung und Store-Einreichung v1.2.0

**Goal**: Die Ergebnisse des Milestones stehen gehaertet, belegt und im Gleichschritt im Store
**Depends on**: Phase 13, Phase 14, Phase 15 (Messzahlen und Funktionsumfang muessen feststehen)
**Requirements**: HART-01, HART-02, REL-02
**Success Criteria** (was wahr sein muss):

  1. DI-11-02/03/05/06 sind abgearbeitet oder dokumentiert entschieden, inklusive des flatternden pgsql-Asts (HTTP 423: bei rot erst wiederholen)
  2. Der BL-F01-Schlusssatz zur Connector-Synergie steht in EN/DE/FR in den Store-Texten beider Haelften, alle vier Katalog-Gates gruen, keine Em-Dashes, keine Backticks oder Tabellen
  3. Das Upgrade 1.1.0 auf 1.2.0 ist Ende zu Ende in CI bewiesen, mit Migration `Version001200Date...`, und die Suche ist nach dem Sprung nicht stumm
  4. Die neue Messzahl steht im Gleichschritt an drei Stellen (README.en.md und beide info.xml)
  5. v1.2.0 ist als signiertes App-Paar eingereicht, zweimal HTTP 201

**Backlog-Kandidat (beim Planen pruefen, kein Requirement):** BL-F02 Baustein 1, OCR-Pakete spa/ita/nld/por. Nur NACH der Phase-15-Messanfahrt einbauen (Werkzeugstand ist Vergleichbarkeitsbedingung) und nur ohne Terminrisiko fuer die Einreichung; sonst Folgerelease.

**Plans:** 7/14 plans complete

Plans:
**Welle 1**

- [x] 16-01-PLAN.md: Flake-Haertung (DI-11-05, L-11), Flake-Register, tantivy-Ignoranweisung (completed 2026-09-21)
- [x] 16-02-PLAN.md: Das Geheimnis- und Vokabular-Gate ueber docs/ (A2, Teil 1) (completed 2026-09-21)
- [x] 16-03-PLAN.md: Nachfolgefassungen 92c und 99d plus Waechter (A1) (completed 2026-09-21)
- [x] 16-04-PLAN.md: DI-11-02/03/06 entschieden, L-07 behoben, deferred-items (completed 2026-09-21)

**Welle 2** *(wartet auf Welle 1)*

- [x] 16-05-PLAN.md: Bereinigung der 58 Altfunde und des gesperrten Worts, Restliste (A2, Teil 2) (completed 2026-09-21)
- [x] 16-06-PLAN.md: Instrumentierung des inneren Aufrufs in ExAppService (A3, M-01) (completed 2026-09-21)

**Welle 3** *(fertig)*

- [x] 16-07-PLAN.md: Versionsbump 1.2.0 und Migration Version001200Date... (completed 2026-09-21)
- [x] 16-08-PLAN.md: A4 ueber den arm64-CI-Ast, Beleg und Owner-Checkpoint (completed 2026-09-21)

**Welle 4** *(laeuft)*

- [ ] 16-09-PLAN.md: Upgrade-Beweis 1.1.0 auf 1.2.0, neue sechste Zusicherung
- [ ] 16-10-PLAN.md: BL-F02 Baustein 1, sechs OCR-Sprachen, mit Abbruchpfad (Owner-Tor)

**Welle 5** *(wartet auf Welle 4)*

- [ ] 16-11-PLAN.md: Textentwurf der sechs Store-Texte, Owner-Checkpoint (Messzahl, Bilder)

**Welle 6** *(wartet auf Welle 5)*

- [ ] 16-12-PLAN.md: Textuebernahme, Messzahl-Gate und Connector-Gate, Medien

**Welle 7** *(wartet auf Welle 6)*

- [ ] 16-13-PLAN.md: Launch-Haertung, Phasenaudit, Owner-Abnahme

**Welle 8** *(wartet auf Welle 7)*

- [ ] 16-14-PLAN.md: Token-Rotation, Tag, Einreichung 2x HTTP 201, Zustandspflege

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-6 + 06.1 (Archiv v1.0) | v1.0 | 103/103 | Complete | 2026-09-07 |
| 7. Gemeinsame Embedding-Engine | v1.1 | 4/4 | Complete | 2026-09-08 |
| 8. Deutsche Komposita ohne Behelf | v1.1 | 5/5 | Complete | 2026-09-08 |
| 9. Eigene Ergebnisseite | v1.1 | 8/8 | Complete | 2026-09-09 |
| 10. Vergleichsmessung auf der AWS-Box | v1.1 | 7/7 | Complete | 2026-09-10 |
| 11. Haertung und Store-Einreichung v1.1 | v1.1 | 13/13 | Complete | 2026-09-11 |
| 12. Messwerkzeug, Runbook und Terminentscheid | v1.2 | 8/8 | Complete    | 2026-09-16 |
| 13. Filter und Sortierung auf der Ergebnisseite | v1.2 | 13/13 | Complete | 2026-09-19 |
| 14. Modell-Entladung im Leerlauf | v1.2 | 12/12 | Complete | 2026-09-19 |
| 15. Messphase, eine Box-Anfahrt | v1.2 | 16/16 | Complete | 2026-09-21 |
| 16. Haertung und Store-Einreichung v1.2.0 | v1.2 | 8/14 | In Progress | - |

## Nach v1.2 (Wiedervorlage)

Offene Punkte, die bewusst NICHT in v1.2 liegen:

- Snapshot-Wiedervorlage `snap-03f1d1d9ad9262704` nach v1.2 (loeschen oder Archive-Tier, rund 2,9 USD/Monat)
- Sortierung nach Name oder Groesse (neues Fast-Field, SCHEMA_VERSION-Sprung, Vollreindex auf Bestandsinstallationen)
- Mimetype-Gruppen aus `files.mime` statt Endung, nur bei nachgewiesenem Genauigkeitsbedarf
- Geplantes Vorwaermen nach Zeitplan
- Index-Verschluesselung mit Key-Rotation und External Storage (SMB, S3) mit ACL-Mapping, beide Pro-Schiene
- Aufraeumbefunde aus der Recherche: `fastembed==0.8.0` gepinnt aber nirgends importiert, `numpy` als indirekte, nicht deklarierte Abhaengigkeit
- Systemplatten-Skripte Phasen 5-6.1: Repo-Aufnahme erst nach Geheimnis-Durchsicht

Aktiver Blocker unabhaengig vom Milestone: Kill-Kriterium Nextcloud Conference September (kuendigt Nextcloud eine Elasticsearch-freie Volltextsuche mit OCR an, wird das Projekt neu bewertet).

---
*Created: 2026-09-08. v1.1 archiviert: 2026-09-11. v1.2 geplant: 2026-09-14.*
