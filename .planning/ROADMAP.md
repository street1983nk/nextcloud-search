# Roadmap: Findling

## Milestones

- [x] **v1.0 Volltext, OCR und semantische Suche** -- Shipped 2026-09-07 (Phasen 1-6 + 06.1, Archiv: .planning/milestones/v1.0-ROADMAP.md)
- [ ] **v1.1 Qualitaet und Effizienz** -- in Arbeit (Phasen 7 bis 11)

---

# Milestone v1.1: Qualitaet und Effizienz

## Overview

v1.1 baut kein neues Produkt, sondern macht das ausgelieferte spuerbar besser und schlanker, und belegt das mit einer Messung statt mit einer Behauptung. Die Nummerierung setzt v1.0 fort: dort endete die Arbeit bei Phase 06.1, hier beginnt sie bei Phase 7.

Die Reihenfolge folgt einem Zwang, der nicht verhandelbar ist: **die Vergleichsmessung braucht die fertige Engine.** Alles, was den Speicherbedarf, die Tokenisierung oder den Suchweg veraendert (Phasen 7, 8, 9), steht deshalb vor dem Lauf auf der AWS-Box (Phase 10). Die Box ist angehalten, der Korpus liegt dort, und jeder Neustart kostet Laufzeit und Geld: sie wird einmal angeschaltet, wenn es nichts mehr zu messen gibt, das sich danach noch aendert. Die Store-Einreichung (Phase 11) ist der Abschluss, weil ein Store-Text die Zahlen aus dem Messbericht traegt und nach der Abgabe nicht mehr editierbar ist.

Die Phasen sind bewusst klein und einzeln nutzbar geschnitten. Grund ist das Kill-Kriterium: kuendigt Nextcloud auf der Conference im September eine Elasticsearch-freie Volltextsuche mit OCR an, wird das Projekt neu bewertet. Nach jeder einzelnen Phase steht ein Zustand, der fuer sich genommen ein Release wert waere, statt eines halben Umbaus.

**Wichtiger Vorbehalt zur Ausgangslage:** Drei Anforderungen dieses Milestones (EFF-01, QUAL-01, QUAL-03) haben in v1.0 bereits erhebliche Vorarbeit bekommen, die in der Milestone-Beschreibung noch nicht abgebildet ist (Plaene 06.1-02, 06.1-04, 06.1-18). Jede betroffene Phase beginnt deshalb mit einer Bestandsaufnahme gegen den Quellcode, nicht mit einem Neubau. Details stehen bei den Phasen unter "Bestand aus v1.0".

## Phasen-Konvention (gilt fuer jede Phase dieses Milestones)

- **Audit-Gate (Owner-Regel 15.08.2026):** Nach jeder Phase laufen Security-, Bug- und Performance-Audit. Befunde ab MEDIUM werden vor dem Phasen-Abschluss gefixt, LOW wird dokumentiert entschieden. Eine Phase gilt ohne dieses Gate nicht als abgeschlossen.
- **Sicherheitsgrenze:** Die Berechtigungskette bleibt unveraendert (SQLite-ACL-Vorfilter im Container, finaler PHP-Recheck als Grenze). Keine Phase dieses Milestones darf eine zweite Grenze aufmachen.
- **Kurztext-Regel (Owner-Regel 07.09.2026):** Jeder nach aussen sichtbare Text (Store, README) ist eine kurze Faktenliste; der Entwurf geht vor dem Release an den Owner.

## Phases

**Phase Numbering:**

- Integer phases (7, 8, 9): Planned milestone work
- Decimal phases (7.1, 7.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 7: Gemeinsame Embedding-Engine** - Das Modell liegt pro Prozess genau einmal im Speicher, ohne dass die erste Suche nach Leerlauf langsamer wird (completed 2026-09-08)
- [x] **Phase 8: Deutsche Komposita ohne Behelf** - Wer ein Teilwort sucht, findet das zusammengesetzte Wort, ueber eine lizenzgeklaerte Wortliste statt ueber einen Prefix-Behelf
 (completed 2026-09-08)
- [ ] **Phase 9: Eigene Ergebnisseite** - Der Nutzer verliert die Trefferliste nicht mehr, wenn er einen Treffer oeffnet
- [ ] **Phase 10: Vergleichsmessung auf der AWS-Box** - Die Verbesserung steht als Zahl neben der v1.0-Baseline, Zeile fuer Zeile
- [ ] **Phase 11: Haertung und Store-Einreichung v1.1** - v1.1 ist getestet jenseits des Happy Path und als signiertes App-Paar im Store

## Phase Details

### Phase 7: Gemeinsame Embedding-Engine

**Goal**: Findling kommt auf derselben Box mit weniger Speicher aus, weil Suche und Indexer sich eine Modellinstanz teilen, und der Nutzer merkt davon nichts ausser dem freien Speicher.
**Depends on**: Nichts (erste Phase des Milestones, setzt den ausgelieferten Stand 1.0.x voraus)
**Requirements**: EFF-01, EFF-02
**Bestand aus v1.0**: Plan 06.1-02 hat `backend/src/findling/embed/engine.py::shared_model()` eingefuehrt, Plan 06.1-04 eine RSS-Ratsche in CI. Die Nachmessung vom 07.09.2026 weist den Effekt in der Suchphase mit -712,6 MB aus, an der Gesamtspitze nur mit -25,1 MB. Die Phase beginnt mit der Bestandsaufnahme, welche Aufrufstellen die geteilte Instanz heute wirklich benutzen und welche noch eine eigene bauen; erst danach wird gebaut.
**Success Criteria** (what must be TRUE):

  1. In einem Container, in dem Indexierung und Suche beide gelaufen sind, sind die Modellgewichte genau einmal geladen; ein Test, der rot werden kann, zaehlt die Ladevorgaenge und faellt bei einer zweiten Instanz
  2. Ein Nutzer sucht semantisch als Erster nach einer Leerlaufphase und bekommt die Antwort innerhalb des p95-Budgets von 2,5 Sekunden, gemessen und nicht geschaetzt
  3. Faellt die Engine aus oder fehlt das Modell, liefert die Suche unveraendert Volltexttreffer statt eines Fehlers, und der Admin sieht den Zustand in der Diagnose
  4. Der Speicherunterschied zum Stand 1.0.x ist auf amd64 als Zahl belegt und benennt ausdruecklich, an welcher Stelle er anfaellt (Grundlast, Suchphase oder Gesamtspitze)

**Plans**: 4 Plaene in 4 Wellen

Plans:
**Wave 1**

- [x] 07-01-PLAN.md , Beleg EFF-01 und EFF-02 im Messbericht, ohne Produktionscode (Welle 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 07-02-PLAN.md , die amd64-Kaltstartzahl ueber den echten PHP-Weg und das Rueckschritt-Tor (Welle 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 07-03-PLAN.md , die Grundlast-Restluecke aus Tokenizer und Splitter, gemessen mit Abbruchbedingung (Welle 3)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 07-04-PLAN.md , der Engine-Zustand in der Diagnose, Kriterium 3 ganz statt halb (Welle 4)

### Phase 8: Deutsche Komposita ohne Behelf

**Goal**: Ein Nutzer, der ein Teilwort eintippt, findet die Dokumente mit dem zusammengesetzten Wort, und die Wortliste dahinter ist lizenzrechtlich sauber und dokumentiert.
**Depends on**: Phase 7 (die Analyzer-Kette liegt im selben Prozess wie die Engine; erst ist der Speicherweg geklaert, dann wird an der Tokenisierung gedreht)
**Requirements**: QUAL-01, QUAL-02, QUAL-03
**Bestand aus v1.0**: `backend/src/findling/index/wordlist.py` traegt Rezept A aus dem Debian-Paket `wngerman` (276.496 Eintraege, GPL-2+ und damit AGPL-3.0-vertraeglich, Herkunft in `docs/german-analyzer.md`), `index/analyzer.py` ruft `Filter.split_compound`. Der Endungsvergleich aus QUAL-03 ist in `docs/measurements/2026-09-nachmessung-m7g/` Abschnitt 7 gefahren. Die Recherche vom 08.09.2026 (08-RESEARCH.md) hat den Suchweg Datei fuer Datei geprueft: es gibt keinen Prefix-Behelf, `split_compound` greift auf Index- und Frageseite, und die Kriterien 3 und 4 sind gebaut. Die Phase belegt den Bestand, verbreitert das CI-Sprachfall-Set und schliesst die zwei offenen Saetze aus QUAL-03; eine Rezeptaenderung ist gemessen ausgeschlossen.
**Success Criteria** (what must be TRUE):

  1. Ein Nutzer sucht ein Teilwort und findet Dokumente, in denen **nur** das zusammengesetzte Wort steht: "Belehrung" findet "Rechtsmittelbelehrung", "Auszug" findet "Grundbuchsauszug", "Erinnerung" findet "Zahlungserinnerung"; diese Faelle und die weiteren Kompositafaelle stehen im CI-Sprachfall-Set und koennen rot werden. Das Wort "nur" ist gemessen und nicht behauptet: jeder dieser Suchbegriffe steht im Korpus ausschliesslich innerhalb seines Kompositums, und die ausgelieferte Kette ohne `Filter.split_compound` findet fuer keinen von ihnen eine Datei (Messung 08.09.2026 gegen die echte Debian-Liste; der Waechter dazu ist `test_a_ci_term_finds_nothing_once_the_splitter_is_taken_out`). Das frueher hier zuerst genannte Beispiel ("Vereinbarung" findet "Pachtvereinbarung") ist als Kriterium zurueckgezogen, weil dieselbe Datei "Vereinbarung" auch eigenstaendig fuehrt und der Fall damit auch ohne Splitter gruen bleibt; es steht als benanntes Gegenbeispiel in `testdata/CORPUS.md`. Der davor genannte Fall ("Genehmigung" findet "Baugenehmigung") ist gemessen nicht baubar, weil "Baugenehmigung" selbst ein Eintrag der Wortliste ist, und wird als benannte Grenze in `docs/german-analyzer.md` gefuehrt (Owner-Entscheid a vom 08.09.2026, Messung in `docs/measurements/2026-09-komposita-rezept-a/`)
  2. Die Zerlegung laeuft im ausgelieferten Suchweg ueber `split_compound` mit der mitgelieferten Wortliste, nicht ueber eine Prefix-Query; ein Test belegt den Weg statt nur das Ergebnis
  3. Lizenz, Herkunft und Fassung der Wortliste stehen im Repo und im Abbild, und die Vertraeglichkeit mit AGPL-3.0 ist begruendet aufgeschrieben
  4. Ein Wechsel der Wortliste erzwingt sichtbar einen Reindex (Digest neben `schema_version` und `analyzer_version`), statt Index und Query-Parser still auseinanderlaufen zu lassen
  5. Der Endungsvergleich der Verdikte gegen den Generator ist abgeschlossen dokumentiert, jede Abweichung hat einen Namen, und jeder Befund ist als Testfall eingezogen oder als bewusst offen benannt

**Plans**: 5 Plaene in 4 Wellen

Plans:
**Wave 1**

- [x] 08-01-PLAN.md , Messgrundlage gegen die echte Wortliste plus Owner-Entscheid zum Wortlaut von Erfolgskriterium 1 (Welle 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 08-02-PLAN.md , der Wegbeweis fuer Erfolgskriterium 2: Negativkontrolle, Praefix-Gegenprobe, Strukturwaechter (Welle 2)
- [x] 08-03-PLAN.md , Lizenz und Wortlistenfassung im veroeffentlichten Abbild, Variantenwechsel Ende zu Ende (Welle 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 08-04-PLAN.md , Regressionswaechter ueber gewonnene und verlorene Zerlegungen, drei neue CI-Sprachfaelle (Welle 3)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 08-05-PLAN.md , QUAL-03 formal schliessen und die gemessenen Grenzen in die Doku ziehen (Welle 4)

### Phase 9: Eigene Ergebnisseite

**Goal**: Der Nutzer kann in allen Treffern seiner Suche blaettern und einen Treffer oeffnen, ohne die Liste zu verlieren, und sieht dabei genau die Dateien, die er auch in der Unified Search sieht.
**Depends on**: Phase 8 (die Seite zeigt dieselben Treffer wie die Unified Search; die Rangfolge wird nicht mitten in der Arbeit an der Tokenisierung eingefroren)
**Requirements**: UI-01, UI-02, UI-03
**Success Criteria** (what must be TRUE):

  1. Ein Nutzer wechselt aus der Unified Search mit einem Klick auf eine Findling-Ergebnisseite, die alle Treffer seiner Suche zeigt statt der gekuerzten Liste
  2. Der Nutzer erreicht Treffer jenseits der ersten Seite ueber eine Paginierung, ohne die Suche neu zu tippen
  3. Der Nutzer oeffnet einen Treffer und kommt auf dieselbe Seite derselben Trefferliste zurueck, mit derselben Suche und derselben Position
  4. Die Ergebnisseite zeigt genau die Dateien, die die Unified Search zeigt: derselbe ACL-Vorfilter, derselbe finale PHP-Recheck, keine zweite Sicherheitsflaeche; der bestehende Paritaetstest deckt die neue Route mit ab
  5. Ist das Backend gestoppt oder antwortet es nicht, zeigt die Seite eine klare Meldung statt einer leeren Liste oder eines Fehlers

**Plans**: 8 Plaene in 7 Wellen
**UI hint**: yes

Plans:
**Wave 1**

- [x] 09-01-PLAN.md , Zeitbudget der Seitenroute messen und den Per-Call-Deckel parametrieren (Welle 1)
- [x] 09-02-PLAN.md , Gate B lernt die Nutzerseiten-Routenklasse, Gate C die drei fehlenden Verbote (Welle 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 09-03-PLAN.md , der geteilte Recheck-Dienst, der Zaehl-Gate und die Offset-Decke (Welle 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 09-04-PLAN.md , PageController mit dem URL-Vertrag und der Highlight-Zerleger (Welle 3)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 09-05-PLAN.md , Template, Stil, Skript und die 24 Copy-Elemente (Welle 4)

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 09-06-PLAN.md , Navigationseintrag, Einstieg aus dem Suchdialog, Gate C auf die Seitendateien (Welle 5)

**Wave 6** *(blocked on Wave 5 completion)*

- [ ] 09-07-PLAN.md , der Paritaetstest deckt die neue Route mit (Welle 6)

**Wave 7** *(blocked on Wave 6 completion)*

- [ ] 09-08-PLAN.md , Sichtproben, UI-SPEC-Nachzug, vertagte FR-Wortlaute und die drei Audits (Welle 7)

### Phase 10: Vergleichsmessung auf der AWS-Box

**Goal**: Die Verbesserungen aus den Phasen 7 bis 9 stehen als Zahlen neben der v1.0-Baseline auf derselben Zielhardware, einschliesslich der Zahlen, die nicht besser geworden sind.
**Depends on**: Phasen 7, 8 und 9 (die Messung braucht die fertige Engine; die Box wird einmal angeschaltet, wenn sich am gemessenen Stand nichts mehr aendert)
**Requirements**: MESS-01, MESS-02, MESS-03
**Success Criteria** (what must be TRUE):

  1. Ein Lauf auf der AWS-Box mit dem vorhandenen v1.0-Korpus (51.961 Dokumente) weist die RSS-Ersparnis der gemeinsamen Engine gegen die v1.0-Baseline aus, mit dem Beleg, dass Abbild und Arbeitsbaum derselbe Stand sind
  2. Der Lauf zeigt keine Regression: p95-Suchlatenz und die zehn deutschen CI-Sprachfaelle bleiben im v1.0-Rahmen, und jede Verschlechterung ist benannt statt weggelassen
  3. Der Messbericht liegt in `docs/measurements` in der Struktur des v1.0-Berichts, sodass jede Zahl neben ihrer Entsprechung steht und Zeile fuer Zeile vergleichbar ist
  4. Die Rohdaten und Skripte des Laufs liegen im Repo, der Lauf ist wiederholbar beschrieben, und die Box ist danach wieder angehalten

**Plans**: TBD

### Phase 11: Haertung und Store-Einreichung v1.1

**Goal**: v1.1 steht als signiertes App-Paar im Nextcloud App Store, nachdem es jenseits des Happy Path getestet wurde und der Owner die Texte abgenommen hat.
**Depends on**: Phase 10 (die Store-Aussage traegt Zahlen aus dem Messbericht und ist nach der Abgabe nicht mehr editierbar)
**Requirements**: REL-01
**Success Criteria** (what must be TRUE):

  1. Beide Apps tragen dieselbe Version, sind signiert, und eine frische Nextcloud im Versionsfenster installiert sie aus den Release-Artefakten auf amd64 und arm64 und findet ohne Handgriff Inhalte
  2. Ein Upgrade von 1.0.x auf 1.1.0 laesst den bestehenden Index entweder unangetastet oder verlangt sichtbar einen Reindex; ein stiller Verlust von Indexinhalt kommt nicht vor
  3. Security-, Bug- und Performance-Audit sind erneut gefahren, alle Befunde ab MEDIUM gefixt, LOW dokumentiert entschieden
  4. Die Store-Texte sind kurze Faktenlisten nach der Kurztext-Regel, der Owner hat den Entwurf vor der Einreichung gesehen und abgenommen
  5. v1.1 ist eingereicht, und die Release-Artefakte im Repo entsprechen dem, was eingereicht wurde

**Plans**: TBD

## Progress

**Execution Order:**
Phasen laufen in numerischer Reihenfolge: 7 -> 8 -> 9 -> 10 -> 11

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 7. Gemeinsame Embedding-Engine | 4/4 | Complete    | 2026-09-08 |
| 8. Deutsche Komposita ohne Behelf | 5/5 | Complete   | 2026-09-08 |
| 9. Eigene Ergebnisseite | 5/8 | In Progress|  |
| 10. Vergleichsmessung auf der AWS-Box | 0/? | Not started | - |
| 11. Haertung und Store-Einreichung v1.1 | 0/? | Not started | - |

## Requirement Coverage

12 von 12 v1.1-Requirements sind genau einer Phase zugeordnet, keine Waisen, keine Doppelungen.

| Phase | Requirements | Anzahl |
|-------|--------------|--------|
| 7 | EFF-01, EFF-02 | 2 |
| 8 | QUAL-01, QUAL-02, QUAL-03 | 3 |
| 9 | UI-01, UI-02, UI-03 | 3 |
| 10 | MESS-01, MESS-02, MESS-03 | 3 |
| 11 | REL-01 | 1 |

## Sequenz-Zwaenge (nicht verhandelbar)

1. Die Vergleichsmessung (Phase 10) kommt nach jeder Code-Aenderung, die Speicher, Tokenisierung oder Suchweg beruehrt. Eine Messung auf einem Stand, der sich danach noch aendert, ist keine Messung, sondern ein Zwischenstand mit Berichtsform.
2. Die AWS-Box wird einmal angeschaltet und danach wieder angehalten. Korpus und Datentraeger liegen dort; jeder zusaetzliche Lauf kostet Laufzeit, und ein verlorener Datentraeger kostet die Vergleichbarkeit zur v1.0-Baseline.
3. Die Store-Einreichung (Phase 11) ist der Abschluss, nicht der Anfang: der Store-Text traegt die Zahlen des Messberichts und reist unveraenderlich mit dem Release.
4. Die Berechtigungskette wird in keiner Phase verdoppelt. Die Ergebnisseite (Phase 9) benutzt den bestehenden Vorfilter und den bestehenden finalen PHP-Recheck.
5. Nach jeder Phase laufen die drei Audits, und Befunde ab MEDIUM werden vor dem Abschluss gefixt (Owner-Regel 15.08.2026).
6. Kill-Kriterium bleibt aktiv: kuendigt Nextcloud eine Elasticsearch-freie Volltextsuche mit OCR an (Nextcloud Conference September), wird das Projekt neu bewertet. Die Phasen sind deshalb klein und einzeln releasefaehig geschnitten.

## Offene Punkte fuer die Phasenplanung

- **Phase 7 und 8 beginnen mit einer Bestandsaufnahme gegen den Quellcode.** Die Milestone-Beschreibung stammt aus dem Semantiklauf vom 05.09.2026; die Phase 06.1 hat danach an denselben Stellen gearbeitet. Was schon steht, wird belegt und abgehakt, nicht neu gebaut.
- **Phase 9 ist die einzige Phase mit sichtbarer Oberflaeche** und der Kandidat fuer `/gsd:ui-phase`. Offen fuer die Planung: eigene Vue-Seite in der PHP-App gegen `IInAppSearch`, und wie die Paginierung mit dem ACL-Recheck zusammengeht, wenn der Recheck Treffer einer Seite entfernt.
- **Phase 10 braucht einen Wiederanlaufpfad fuer die Box** (Instanz, Datentraeger, Abbild-Digest), bevor sie startet.

---
*Created: 2026-09-08*
