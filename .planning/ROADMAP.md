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
- [x] **Phase 9: Eigene Ergebnisseite** - Der Nutzer verliert die Trefferliste nicht mehr, wenn er einen Treffer oeffnet (completed 2026-09-09)
- [x] **Phase 10: Vergleichsmessung auf der AWS-Box** - Die Verbesserung steht als Zahl neben der v1.0-Baseline, Zeile fuer Zeile (abgeschlossen 2026-09-10; Kriterium 2 ausdruecklich nur teilweise belegt, siehe Phasenblock)
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

- [x] 09-06-PLAN.md , Navigationseintrag, Einstieg aus dem Suchdialog, Gate C auf die Seitendateien (Welle 5)

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 09-07-PLAN.md , der Paritaetstest deckt die neue Route mit (Welle 6)

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 09-08-PLAN.md , Sichtproben, UI-SPEC-Nachzug, vertagte FR-Wortlaute und die drei Audits (Welle 7)

### Phase 10: Vergleichsmessung auf der AWS-Box

**Goal**: Die Verbesserungen aus den Phasen 7 bis 9 stehen als Zahlen neben der v1.0-Baseline auf derselben Zielhardware, einschliesslich der Zahlen, die nicht besser geworden sind.
**Depends on**: Phasen 7, 8 und 9 (die Messung braucht die fertige Engine; die Box wird einmal angeschaltet, wenn sich am gemessenen Stand nichts mehr aendert)
**Requirements**: MESS-01, MESS-02, MESS-03
**Success Criteria** (what must be TRUE):

  1. [x] Ein Lauf auf der AWS-Box mit dem vorhandenen v1.0-Korpus (51.961 Dokumente) weist die RSS-Ersparnis der gemeinsamen Engine gegen die v1.0-Baseline aus, mit dem Beleg, dass Abbild und Arbeitsbaum derselbe Stand sind , **BELEGT** in Bericht Abschnitt 5 (Grundlast 103,2 MB gegen 691,8 MB, minus 588,6 MB), Abschnitt 2 (`korpus-gleich ja`, Pruefsumme `bcbef9b2...`, 50.000 Dateien, 20.208.046.426 Byte) und Abschnitt 1 (`baumhash-gleich ja`, drei Baumhashes, 54 Dateien identisch in Abbild und Arbeitsbaum). Der Bestand 52.111 minus 150 Drill-Dateien ergibt exakt die 51.961 der Baseline (Abschnitt 15.3)
  2. [~] Der Lauf zeigt keine Regression: p95-Suchlatenz und die zehn deutschen CI-Sprachfaelle bleiben im v1.0-Rahmen, und jede Verschlechterung ist benannt statt weggelassen , **TEILWEISE BELEGT.** Erfuellt ist die zweite Haelfte: Bericht Abschnitt 19 fuehrt jede Verschlechterung in eigener Ueberschrift, dreizehn an der Zahl. Nicht erfuellt ist der Wortlaut "keine Regression": **vier von fuenf Laststufen sind regressiv** (plus 5,8 / 11,0 / 13,4 / 17,5 Prozent, alle ueber dem Rauschband), die Zusage auf Stufe 8 haelt mit 2.125,5 ms gegen 2.500 ms, aber ihre Reserve faellt von 585,0 auf 374,5 ms (Abschnitt 8). Die Sprachfaelle stehen auf 6 von 10, und die Diagnose weist nach, dass es **kein Sprachdefekt** ist, sondern der Messaufbau (Abschnitt 12, DI-10-02); der CI-Beleg auf amd64 ist gruen (Lauf 34339346666). **Was fehlt und wohin es gehoert:** eine Sprachfall-Messung, die nicht gegen einen 52.111er-Fremdbestand laeuft (DI-10-02, Phase 11), und die Entscheidung, ob die Latenzregression der vier Stufen hingenommen oder untersucht wird (Phase 11, Haertung)
  3. [x] Der Messbericht liegt in `docs/measurements` in der Struktur des v1.0-Berichts, sodass jede Zahl neben ihrer Entsprechung steht und Zeile fuer Zeile vergleichbar ist , **BELEGT** durch `docs/measurements/2026-09-vergleichsmessung-m7g/README.md`: 19 Abschnitte in der Folge des v1.0-Berichts, drei bis vier Vergleichsspalten je Tabelle (Posten, 06-11, Nachmessung beziehungsweise 05-21, dieser Lauf, Differenz), 154 Verweise auf Rohdateien, jede Zahl ohne Entsprechung als Erstmessung ausgewiesen
  4. [x] Die Rohdaten und Skripte des Laufs liegen im Repo, der Lauf ist wiederholbar beschrieben, und die Box ist danach wieder angehalten , **BELEGT**: 60 Rohdateien unter `rohdaten/` und 11 Skripte unter `skripte/`, jede in Bericht Abschnitt 18 mit einem Satz gefuehrt; `skripte/00-ablauf.md` beschreibt in Abschnitt 2 die geplante und in Abschnitt 2b die gefahrene Reihenfolge mit jeder Abweichung und ihrem Grund. Die Box ist nach der Berichtsabnahme angehalten worden, Stoppzeitpunkt und Endkosten in Bericht Abschnitt 17.1 und `rohdaten/93-kosten-und-verbleib.txt`; der **Abbau** ist auf Owner-Entscheid vom 10.09.2026 ausdruecklich nicht Teil dieser Phase

**Plans**: 7 Plaene in 7 Wellen

Die Wellen 1 bis 4 kosten keine Box-Minute und stehen bewusst vor der Anfahrt: sie schliessen die zwei Werkzeugluecken, die die Recherche belegt hat (der leere Baumhash-Beweis in beiden Vorlaeuferberichten, die fehlende Zeilenende-Regel fuer die Python-Messskripte), holen die native arm64-Feinmessung ohne Box nach (DI-07-04) und bauen das vollstaendige Skriptset. Die Box wird einmal angeschaltet (Sequenz-Zwang 2), und der Neuaufbau des Index nach dem Volumenvorfall vom 07.09. ist nicht Ruestzeit, sondern die Messung selbst.

Plans:
**Wave 1**

- [x] 10-01-PLAN.md , die zwei gefundenen Werkzeugluecken: Zeilenende-Regel und Baumhash-Beweis mit eigener Rohdatei (Welle 1, ohne Box-Zeit)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 10-02-PLAN.md , DI-07-04: die native arm64-Feinmessung per workflow_dispatch, und die vier Spalten nachgezogen (Welle 2, ohne Box-Zeit)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 10-03-PLAN.md , Ablaufplan und das Skriptset vor dem Volllauf: Bestand, Korpus, Abbildwechsel, Nullstand, Grundlast, erste Suche, Lastreihe (Welle 3, ohne Box-Zeit)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 10-04-PLAN.md , das Skriptset des abgesetzten Laufs plus die drei neuen Messbloecke: Sprachfaelle, Seitenroute, Rundenzaehlung (Welle 4, ohne Box-Zeit)

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 10-05-PLAN.md , Anfahrt-Freigabe, die Zahlen vor dem Volllauf, und der Lauf abgesetzt angestossen (Welle 5, Checkpoint-Plan)

**Stand nach Welle 5 (2026-09-10):** Der Volllauf ist durch. Grundlast im Leerlauf **103,2 MB gegen 691,8 MB**, **52.111 Dokumente** indexiert und eingebettet (37 uebersprungen, 0 fehlgeschlagen, ohne OOM, `RestartCount=0`), Laufzeit **hoechstens 26 h 41 min gegen 18 h 56 min**. Zwei Zahlen sind nicht besser geworden und werden im Bericht so gefuehrt: die Laufzeit (plus 40,9 Prozent) und `memory.events max` (**21.939 gegen 2.796**, mit `memory.peak` gleich der harten Grenze). Zu Erfolgskriterium 1: der Korpus ist byteweise derselbe (`korpus-gleich ja`), die 52.111 statt 51.961 sind zwei Drill-Verzeichnisse vom 07.09. im Baum des indexierten Nutzers (`ocrdrei` 120 plus `neustart` 30). **Die Box hat noch rund 2,1 Stunden unter dem 30-Stunden-Deckel**, also braucht Welle 6 entweder einen straffen Lauf oder einen angehobenen Deckel.

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 10-06-PLAN.md , die Messungen nach dem Lauf, DI-07-02 und DI-07-03, das Kernaussage-Blatt, Abnahme der Zahlen, Box angehalten (Welle 6, Checkpoint-Plan)

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 10-07-PLAN.md , der Messbericht in 19 Abschnitten, die Nachzuege in den Projektdokumenten, die drei Audits, Berichtsabnahme (Welle 7, Checkpoint-Plan)

**Stand nach Welle 7 (2026-09-10):** Der Messbericht liegt unter `docs/measurements/2026-09-vergleichsmessung-m7g/README.md`, 19 Abschnitte, 154 Verweise auf Rohdateien, Abschnitt 19 "Was dieser Lauf nicht besser gemacht hat" mit dreizehn benannten Punkten. `docs/performance.md` fuehrt eine Zeile in "Stand dieses Berichts", einen eigenen Abschnitt "Die Vergleichsmessung v1.1 gegen v1.0" und den vierten Verbleib der Box; der Zeiger, der seit dem 08.09. auf Phase 10 zeigte, ist abgeloest. `CLAUDE.md` traegt seit dem Owner-Entscheid vom 10.09. die Zeile "Tokenizer und Splitter" in der RAM-Budget-Tabelle. **DI-07-02 ist gemessen und mit negativer Marge an Phase 11 uebergeben; der Messteil von DI-07-03 ist geschlossen.** Fuenf neue Befunde stehen in `deferred-items.md` dieser Phase, darunter **DI-10-01**: das Lastwerkzeug zaehlt 17 abgebrochene Containeraufrufe der Stufe 16 als Erfolge. **Erfolgskriterium 2 ist nur teilweise belegt** und oben als solches gefuehrt.

**Abgeschlossen am 2026-09-10.** Der Owner hat den Bericht abgenommen, ohne eine Zahl zu beanstanden, und drei Dinge entschieden: der Nachzug in `README.md` und `docs/store-listing.md` faellt in **Phase 11** zusammen mit der Store-Text-Abnahme (eine Textrunde statt zwei, gefuehrt als DI-10-03 mit dem Merker, dass eine Messzahl an drei Stellen steht); **Erfolgskriterium 2 bleibt "teilweise belegt"** und wird nicht schoengerechnet; keine Nacharbeit auf der Box noetig. Danach ist die Box angehalten worden: `BOX_STOPPED_ISO=2026-09-10T16:22:50Z`, **31,05 Stunden und 3,5969 USD netto**, also unter dem angehobenen Deckel von 34 Stunden und 4,00 USD. Zustand `stopped` um 16:23:15Z aus der API geprueft. **Angehalten, nicht abgebaut**; der Abbau ist ein eigener Entscheid mit eigenem Plan in Phase 11.

### Phase 11: Haertung und Store-Einreichung v1.1

**Goal**: v1.1 steht als signiertes App-Paar im Nextcloud App Store, nachdem es jenseits des Happy Path getestet wurde und der Owner die Texte abgenommen hat.
**Depends on**: Phase 10 (die Store-Aussage traegt Zahlen aus dem Messbericht und ist nach der Abgabe nicht mehr editierbar)
**Requirements**: REL-01
**Vorbedingung aus Phase 9**: Der vollstaendige franzoesische Katalog (alle Zeichenketten der App, `fr.json` **und** `fr.js`, Schluesselvergleich auf zwei Sprachpaare erweitert) ist Vorbedingung der Abgabe; die 24 vorbereiteten Wortlaute der Ergebnisseite und die Begruendung der Vertagung stehen in `docs/l10n-french.md`. , **Stand 2026-09-11 (Plan 11-05): der Text ist geschrieben und abgenommen, die Dateien fehlen noch.** `docs/l10n-french.md` traegt eine dreispaltige Tabelle Schluessel/DE/FR ueber alle **174** Katalogschluessel (173 Zeilen plus `Findling` als benannte Ausnahme), 24 Wortlaute woertlich aus Phase 9 und **149 neu**, mit Wortwahl-, Typografie- und Pluralabschnitt davor und der benannten G2-Ausnahmenliste darunter. Der Owner hat sie als franzoesischer Muttersprachler am **2026-09-11 ohne eine einzige Korrektur** abgenommen; die Abnahmezeile steht datiert in derselben Datei und nennt sich ausdruecklich **Teil 1 von 2 (Katalog)** von D-07. Offen bleiben `fr.json` und `fr.js` samt der vier Gates G1 bis G4 (Plan 11-08) und die Textabnahme Teil 2 (Plan 11-09). Befund fuer 11-08: `Findling` ist Schluessel 1 von 174 in `de.json` und muss den Wert `Findling` tragen, sonst geht G1 rot. , **Stand 2026-09-11 (Plan 11-08): die Vorbedingung ist eingeloest.** `php/l10n/fr.json` und `php/l10n/fr.js` liegen im Baum, mechanisch aus der Tabelle gegossen, mit `Findling` als Schluessel 1 und der franzoesischen Pluralregel in beiden Dateien. Der Schluesselvergleich umfasst jetzt sechs Katalogdateien (G1), dazu kommen G2 Vollstaendigkeit gegen eine benannte Ausnahmenliste, G3 Platzhalter-Paritaet als Multimenge ueber alle Pluralformen und G4 die Pluralregel; das Dash- und Emoji-Gate liest die Kataloge mit. Offen bleibt nur noch die Textabnahme Teil 2 (Plan 11-09).
**Success Criteria** (what must be TRUE):

  1. Beide Apps tragen dieselbe Version, sind signiert, und eine frische Nextcloud im Versionsfenster installiert sie aus den Release-Artefakten auf amd64 und arm64 und findet ohne Handgriff Inhalte , **Stand 2026-09-10 (Plan 11-04): die Strecke steht.** `deploy-harp.yml` faehrt die Fremdinstallation auf amd64 **und nativ auf `ubuntu-24.04-arm`** (Lauf 34525240422, alle vier Aeste gruen) und kann die beiden Archive vom GitHub-Release laden statt sie lokal zu bauen (Lauf 34526436580 mit `release_tag=v1.0.3`, alle vier Aeste gruen, Zero-Config-Treffer nach einer cron-Runde). Offen bleibt nur, dass es die Artefakte von **v1.1.0** sind: das setzt Plan 11-11
  2. Ein Upgrade von 1.0.x auf 1.1.0 laesst den bestehenden Index entweder unangetastet oder verlangt sichtbar einen Reindex; ein stiller Verlust von Indexinhalt kommt nicht vor , **Stand 2026-09-11 (Plan 11-07): der Ende-zu-Ende-Beweis faehrt in CI.** `deploy-harp.yml` installiert auf dem Ast `stable34/ubuntu-24.04` beide Haelften aus den **echten v1.0.3-Release-Assets**, indexiert den 39-Datei-Korpus, bringt die Installation auf den HEAD-Stand (Dateitausch plus `occ upgrade`, Container ohne die Datenflagge neu registriert) und sichert sechs Dinge zu (Lauf **34546421219**, alle vier Aeste gruen): dieselben Trefferzahlen fuer `Belehrung`, `Auszug` und `Erinnerung` (je 1), dieselben fuenf Indexmarken, dieselben Dokumentzahlen (docs 29, indexed 29, skipped 7, failed 6), leerer Arbeitsvorrat, **kein Reindex-Banner**, **keine `start_rebuild_on_drift`-Zeile**, und als Gegenprobe der Navigationseintrag, der vorher fehlte und nachher da ist. Der Reindex-Zweig von D-05 wird bewusst NICHT gefahren; seine Abwesenheit ist die Zusicherung, und das steht im Workflow. Offen bleibt nur, dass die neue Haelfte die Version **1.1.0** traegt: bis Plan 11-11 steht in beiden `info.xml` weiterhin 1.0.3, und der Block hat fuer den Tag des Bumps bereits den zweiten Zweig
  3. Security-, Bug- und Performance-Audit sind erneut gefahren, alle Befunde ab MEDIUM gefixt, LOW dokumentiert entschieden , **ERFUELLT, Stand 2026-09-11 (Plan 11-10).** `docs/audits/2026-09-phase-11/README.md` faehrt alle sechs zutreffenden ASVS-Kategorien einzeln, auch die beiden nicht beruehrten, und belegt sie am Diff statt an einer Meinung: V4 mit drei Belegzeilen (`MAX_ROUNDS` unveraendert 3, `isReadable()` die einzige Berechtigungsfrage, `reduceIds` nicht angefasst) und dem maschinellen Schnitt, der im Diff von `Provider.php` **keine ausfuehrbare Zeile** findet; V5 mit 348 durchgesehenen FR-Werten und -Schluesseln (null spitze Klammern, null Ampersand, null Platzhalterabweichungen); V6 mit vier Zusicherungen ueber die Signaturkette; V14 mit arm64-Ast, Release-Asset-Modus, SHA-Pins und HaRP-Digest. **Der einzige Befund ab MEDIUM ist M-01 (DI-07-03) und war bei Planbeginn gebaut** (Plan 11-13, Entscheid v1-a vom 10.09.2026, Belegstelle `11-13-SUMMARY.md`). Elf LOW sind dokumentiert entschieden: L-05 (DI-10-05) und L-06 (DI-11-04) in diesem Lauf behoben, L-01 bis L-04 hingenommen mit Wiedervorlagebedingung, L-07 bis L-11 mit Zieladresse weitergereicht. Darin enthalten: die von diesem Kriterium verlangte Entscheidung ueber die **vier regressiven Laststufen** (hingenommen fuer v1.1.0, untersucht in der v1.2-Messplanung) und die ehrliche Feststellung, dass **DI-10-02 nicht geschlossen ist**
  4. Die Store-Texte sind kurze Faktenlisten nach der Kurztext-Regel, der Owner hat den Entwurf vor der Einreichung gesehen und abgenommen
  5. v1.1 ist eingereicht, und die Release-Artefakte im Repo entsprechen dem, was eingereicht wurde

**Plans**: 13 Plaene in 8 Wellen

Die Wellen 1 bis 3 kosten keine Box-Minute. Zwei Owner-Fragen stehen bewusst vorn (Plan 11-01): der Umfang von DI-07-03 entscheidet, ob der franzoesische Katalog 173 oder 174 Schluessel traegt, und die Lesart von D-11 entscheidet ueber ausgelieferte Metadaten. Die EINE Box-Anfahrt (D-01, Deckel rund 4 h / 0,50 USD) beweist nur die zwei Werkzeug-Fixe; der Upgrade-Beweis liegt in CI, weil eine zweite Nextcloud am Mess-Docker nach D-02 ausgeschlossen ist. Der Abbau der Box ist ein eigener Plan mit eigener Bestaetigung (D-03). Plan 11-13 ist bedingt: er baut die Abhilfe zu DI-07-03 und laeuft nur, wenn der Owner in 11-01 die Option v1-a waehlt; bei v1-b wird er dokumentiert uebersprungen. Weil er den 174. Katalogschluessel setzt, den 11-05 aus der Datei zaehlt, steht er vor 11-05, und die Wellen 3 bis 7 ruecken um eine Stelle nach hinten.

Plans:
**Wave 1**

- [x] 11-01-PLAN.md , Vorentscheide: DI-07-03-Umfang und die Lesart von D-11 zum Versionsfenster (Welle 1, Checkpoint-Plan)
- [x] 11-02-PLAN.md , Werkzeug-Fix DI-10-01 (--min-hits, hits_per_request) und die Ratsche gegen die D-04-Zusage (Welle 1)
- [x] 11-03-PLAN.md , DI-10-02: Nachfolgefassung des Sprachfall-Skripts mit Fremdbestand-Vorpruefung und dreiwertigem Urteil (Welle 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 11-04-PLAN.md , deploy-harp: nativer arm64-Ast und der Modus, der Release-Assets laedt (Welle 2)
- [x] 11-06-PLAN.md , die EINE Box-Anfahrt: Freigabe mit Deckel, Messblock A und B, Box wieder angehalten (Welle 2, Checkpoint-Plan). DI-10-01 geschlossen, DI-10-02 NICHT geschlossen, 1,97 h und 0,2285 USD unter dem Deckel
- [x] 11-13-PLAN.md , SCHARF seit Entscheid v1-a vom 10.09.2026 (11-VORENTSCHEIDE.md): der Zustand "Kandidaten vom Recheck verworfen" im Dienst, auf der Ergebnisseite und als 174. Katalogschluessel (Welle 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 11-05-PLAN.md , die vollstaendige FR-Uebersetzungstabelle und das FR-Gate, Teil 1 (Welle 3, Checkpoint-Plan). 173 Tabellenzeilen ueber 174 Schluessel, 149 neue Wortlaute, am 11.09.2026 vom Owner ohne Korrektur abgenommen; Platzhalter-Paritaet ueber 34 Schluessel maschinell 0 Abweichungen, kein U+2019, kein Gedankenstrich, kein geschuetztes Leerzeichen, fuenf Pluralschluessel mit je zwei Formen nach `nplurals=2; plural=(n > 1);`
- [x] 11-07-PLAN.md , der Upgrade-Beweis 1.0.3 auf 1.1.0 Ende zu Ende in deploy-harp, stable34 (Welle 3). Lauf 34546421219 gruen im ersten Anlauf, sechs Zusicherungen, Index Ziffer fuer Ziffer unveraendert, der Block kostet 1 min 32 s bei 32 min 21 s Abstand zu `timeout-minutes: 45`

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 11-08-PLAN.md , fr.json und fr.js aus der abgenommenen Tabelle, plus die vier Katalog-Gates (Welle 4). Beide Dateien mechanisch gegossen, 174 Schluessel in der Reihenfolge von `de.json`, fuenf Pluralschluessel mit je zwei Formen und `nplurals=2; plural=(n > 1);` in beiden; G1 Schluesselgleichheit ueber sechs Dateien, G2 gegen eine benannte Ausnahmenliste, G3 Platzhalter-Paritaet als Multimenge, G4 die Pluralregel, dazu das auf die Kataloge ausgedehnte Dash-Gate; zehn Mutationen am echten Baum belegen die Rot-Faehigkeit

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 11-09-PLAN.md , Store-Texte mit den v1.1-Zahlen, Text-Abnahme und FR-Gate, Teil 2 (Welle 5, Checkpoint-Plan)

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 11-10-PLAN.md , die drei Audits der Phase und die vier geerbten Befunde entschieden (Welle 6). `docs/audits/2026-09-phase-11/README.md`, Umfang `721bde6..HEAD`, 55 Dateien, 46 Commits; **0 CRITICAL, 0 HIGH, 1 MEDIUM, 11 LOW**. Anders als Phase 10 aendert diese Phase Produktionscode (15 Dateien unter `php/`, acht davon im Companion-Paket). `fixed: [M-01, L-05, L-06]`, `still_open: [L-07, L-08, L-09, L-10, L-11]`, alle fuenf LOW mit Verdikt und Zieladresse. Zwei Fixe im eigenen Lauf, beide ohne Produktionscode: `ab39d37` vollzieht DI-10-05 im Kopf von `measure.yml`, `2e8502b` behebt DI-11-04 im Artefaktnamen von `deploy-harp.yml`. DI-10-02 bleibt ehrlich offen und ist mit DI-11-01 zusammengelegt. HaRP deploy 34557178548 auf `4becbbc` gruen in allen vier Aesten; neuer Befund L-11 (DI-11-05), der flatternde pgsql-Ast, hingenommen mit Merker fuer 11-11

**Wave 7** *(blocked on Wave 6 completion)*

- [ ] 11-11-PLAN.md , Versionsbump in einem Commit, Tag, ghcr-Pruefung, Store-Submission (Welle 7, Checkpoint-Plan)

**Wave 8** *(blocked on Wave 7 completion)*

- [ ] 11-12-PLAN.md , EBS-Snapshot, gesicherte Historie und der Abbau der Box (Welle 8, Checkpoint-Plan)

## Progress

**Execution Order:**
Phasen laufen in numerischer Reihenfolge: 7 -> 8 -> 9 -> 10 -> 11

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 7. Gemeinsame Embedding-Engine | 4/4 | Complete    | 2026-09-08 |
| 8. Deutsche Komposita ohne Behelf | 5/5 | Complete   | 2026-09-08 |
| 9. Eigene Ergebnisseite | 8/8 | Complete   | 2026-09-09 |
| 10. Vergleichsmessung auf der AWS-Box | 7/7 | Complete    | 2026-09-10 |
| 11. Haertung und Store-Einreichung v1.1 | 11/13 | In Progress|  |

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
