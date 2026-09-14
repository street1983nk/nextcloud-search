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

- [ ] **Phase 12: Messwerkzeug, Runbook und Terminentscheid** - Werkzeug und Runbook stehen fest, bevor die bezahlte Box laeuft; stable35-Entscheid faellt fristgerecht
- [ ] **Phase 13: Filter und Sortierung auf der Ergebnisseite** - Nutzer grenzt Treffer nach Typ und Zeitraum ein und sortiert nach Datum, ohne die Semantik oder die Rechtegrenze zu verlieren
- [ ] **Phase 14: Modell-Entladung im Leerlauf** - Container gibt beide Speicherhalter nach Leerlauf frei, hinter einem ab Werk ausgeschalteten Schalter
- [ ] **Phase 15: Messphase, eine Box-Anfahrt** - Wirkungsbeleg, Laststufen, Sprachfaelle und Wiederaufwaerm-Kosten in einer einzigen bezahlten Anfahrt
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

**Plans:** 6/8 plans executed

Plans:
**Wave 1**

- [x] 12-01-PLAN.md: stable35-Entscheid: beide Zweige vor der Frist ausformuliert
- [x] 12-03-PLAN.md: aws_box.sh restore (Volume aus Snapshot) plus Usage-Gate und lesende AWS-Proben
- [x] 12-04-PLAN.md: In-Container-Bestandssonde, neues Laufverzeichnis, Gate- und CI-Pfadfilter-Erweiterung

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 12-02-PLAN.md: stable35-Entscheid am 16.09.2026 vollziehen (terminlich isoliert, Owner-Checkpoint)
- [x] 12-05-PLAN.md: 98c-sprachfaelle.sh: Nachfolgefassung mit Rangsemantik und Abschnitt 3b
- [x] 12-07-PLAN.md: Runbook Teil 1: Geltung, Deckel-Rechenblatt, Vorbedingungen, Aufbau, Zustandspruefung

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 12-06-PLAN.md: Cron-Vorpruefung fail-closed (Konfigurations- und Wirkungszweig) plus Ablaufplan des Laufs

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 12-08-PLAN.md: Runbook Teil 2: Vergleichbarkeitsbedingungen, Messreihenfolge, Abbau, Kostenfuehrung

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

**Plans**: TBD
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

**Owner-Checkpoint**: engineState-Wortwahl (MEM-05) wird in dieser Phase entschieden, nicht vorweggenommen
**Plans**: TBD

### Phase 15: Messphase, eine Box-Anfahrt

**Goal**: Die eine bezahlte Anfahrt liefert alle offenen Messbelege des Milestones und vollzieht dabei das Runbook zum ersten Mal
**Depends on**: Phase 12 (Werkzeug und Runbook fest), Phase 14 (Schalter fuer den A/B-Beleg); Phase 13 sollte stehen, damit die Sortierung auf grossem Bestand mitgeprueft wird
**Requirements**: MESS-05
**Success Criteria** (was wahr sein muss):

  1. Der Zeit-/Kostendeckel ist vor dem Start neu gerechnet und vom Owner freigegeben (mindestens 31 h / rund 3,59 USD oder bewusst verkleinerter Teilkorpus); ohne Freigabe startet die Anfahrt nicht
  2. Der DI-10-04-Wirkungsbeleg liegt als Volllauf gegen den Korpus-Snapshot mit Top-up-Fix vor, mit protokolliertem Cron-Intervall und Vergleichbarkeitsbedingungen
  3. Die vier regressiven Laststufen sind untersucht und je Stufe entschieden: behoben, erklaert oder bewusst hingenommen
  4. Die Sprachfall-Messung laeuft ohne den 52.111er-Fremdbestand und liefert Zahlen ueber der bisherigen Deckelung (DI-10-02/DI-11-01, neue Messgroesse)
  5. Die Wiederaufwaerm-Kosten der Entladung sind gemessen und ausgewiesen (warm/kalt, mit/ohne Seitencache, A/B ueber den MEM-01-Schalter); die Box ist danach wieder abgebaut

**Plans**: TBD

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

**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-6 + 06.1 (Archiv v1.0) | v1.0 | 103/103 | Complete | 2026-09-07 |
| 7. Gemeinsame Embedding-Engine | v1.1 | 4/4 | Complete | 2026-09-08 |
| 8. Deutsche Komposita ohne Behelf | v1.1 | 5/5 | Complete | 2026-09-08 |
| 9. Eigene Ergebnisseite | v1.1 | 8/8 | Complete | 2026-09-09 |
| 10. Vergleichsmessung auf der AWS-Box | v1.1 | 7/7 | Complete | 2026-09-10 |
| 11. Haertung und Store-Einreichung v1.1 | v1.1 | 13/13 | Complete | 2026-09-11 |
| 12. Messwerkzeug, Runbook und Terminentscheid | v1.2 | 6/8 | In Progress|  |
| 13. Filter und Sortierung auf der Ergebnisseite | v1.2 | 0/? | Not started | - |
| 14. Modell-Entladung im Leerlauf | v1.2 | 0/? | Not started | - |
| 15. Messphase, eine Box-Anfahrt | v1.2 | 0/? | Not started | - |
| 16. Haertung und Store-Einreichung v1.2.0 | v1.2 | 0/? | Not started | - |

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
