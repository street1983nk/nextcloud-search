# Requirements: Findling Milestone v1.3 "Sprachausbau"

**Defined:** 2026-09-23
**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten, ohne dass der Admin irgendetwas konfigurieren muss.
**Scope-Entscheid Owner 23.09.2026:** Lexikalischer Sprachausbau es/it/nl/pt + UI-Kataloge + Messanfahrt BL-F03 + Aufräumbefunde + Release 1.3.0; Extras NL-Komposita (eigene Phase mit eigenem Tor) und disjunction_max-Entscheid (erst Messung) beide REIN.

## v1.3 Requirements

### Lexikalischer Sprachausbau (LEX)

- [ ] **LEX-01**: Nutzer findet spanische, italienische, niederländische und portugiesische Dokumente über Stammformen (vier Analyseketten mit Snowball-Stemmer und Stoppwortliste). Die Position von `ascii_fold` in der Kette wird je Sprache MESSEND abgenommen (der Widerspruch zwischen den Research-Dokumenten ist als offener Entscheid dokumentiert; Abnahmekriterium ist die zusammengeführte Testfall-Tabelle aus STACK/FEATURES/PITFALLS, inkl. información/informaciones, informação/informações, perché, één)
- [ ] **LEX-02**: Das Schema führt IMMER alle sechs Körperfelder; befüllt wird nur nach `FINDLING_LANGUAGES`, Werkseinstellung bleibt `de,en`. Bestandsinstallationen mit `de,en` bleiben unberührt (D-04-Linie); leere Felder kosten gemessen nichts
- [ ] **LEX-03**: Ein Bestandsindex wandert per Re-Analyse-Umbau aus den gespeicherten Feldern in das neue Schema (neues Modul `index/rebuild.py`): kein Download, kein OCR, keine Neu-Einbettung; `vectors.db`/`state.db` unberührt. Der Umbau ist wiederaufnahmefähig nach Neustart und prüft den Plattenplatz vorab (zwei Indexverzeichnisse gleichzeitig, `MIN_FREE_BYTES` anpassen)
- [ ] **LEX-04**: Schema-Erweiterung und Query-Freischaltung liegen in getrennten Phasen mit bewiesenem Umbauweg dazwischen: Die Suche funktioniert auf Bestandsinstallationen in JEDEM Zwischenzustand (der heutige Totalausfall-Pfad `parse_query_lenient`-ValueError -> dauerhaft leere degraded-Antwort darf nie erreichbar sein). Migration `Version001300Date...` wie bei jedem Minor-Sprung
- [ ] **LEX-05**: Die Anfrage durchsucht genau die aktiven Sprachfelder mit Feld-Boosts unterhalb `body_en`; KEINE Spracherkennung, weder dokument- noch anfrageseitig (Anti-Feature, einstimmig)
- [ ] **LEX-06**: Admin sieht in der Diagnose, welche Sprachen aktiv und befüllt sind; beim Start warnt Findling, wenn `FINDLING_LANGUAGES` eine Sprache führt, die die OCR-Sprachen nicht abdecken (Buchstabensalat-Falle)
- [ ] **LEX-07**: `tantivy` auf 0.26.2 gepinnt (stopword-Panic wird ValueError, Union-Scorer-Fix, index_format v7 unverändert); Sprachnamen laufen über eine Positivliste analog `OCR_LANGUAGE_ALLOWLIST`
- [ ] **LEX-08**: CI beweist beides: Sprachfälle je neuer Sprache ohne Fremdbestand (Muster A4/2026-09) UND eine umgedrehte Upgrade-Beweisstrecke in `deploy-harp.yml` (Umbau findet statt, Suche liefert danach in alter und neuer Sprache; die bestehende "kein Reindex"-Strecke wird um die Gegenrichtung ergänzt, nicht entschärft; `UPGRADE_FROM_TAG` auf v1.2.0)

### Niederländische Komposita (KOMP, eigene Phase mit eigenem Tor)

- [ ] **KOMP-01**: Nutzer findet niederländische Komposita über ihre Glieder (`gemeentebelastingen` über `belasting`) via `split_compound` mit `wdutch`/OpenTaal-Wortliste (BSD-3-Clause + CC-BY-3.0, lizenzklar); eigene Digest-Marke (löst NUR bei aktivem Niederländisch einen Rebuild aus, nie bei Bestandsinstallationen ohne nl), RAM-Budget des zweiten Automaten (~23 MB) vor dem Bau gemessen. Fällt bei Terminnot als Ganzes, nicht halb

### UI-Kataloge (KAT)

- [ ] **KAT-01**: UI-Kataloge für es, it, nl, pt_BR und pt_PT im Gleichstand mit EN/DE/FR (Schlüsselzahl aus `de.json` ZÄHLEN, Stand Research 199, nicht die 174 aus dem Backlog); Nextcloud kennt kein `pt`, also zehn neue Dateien (php + backend); `nplurals=3` für es/it/pt_BR/pt_PT korrekt, Gates parametrisiert statt vier Kopien des FR-Blocks
- [ ] **KAT-02**: Übersetzungen maschinell erstellt plus Review mit datiertem Vorbehalt (FR-Muster; Muttersprachler-Gate ausdrücklich NICHT Pflicht); der pt-Sprachcode-Ladepfad der App-Kataloge wird VOR der Übersetzungsarbeit an der laufenden Test-Nextcloud verifiziert

### Messphase (MESS, Fortsetzung ab MESS-06)

- [ ] **MESS-07**: EINE Box-Anfahrt liefert das BL-F03-Bündel: M-01-Zahl (innerer Aufruf auf Zielhardware), Wirkungsnachmessung 92c/99d auf der Box, Bodensatz-Zyklus 2, die 6 Fehlschläge und 44 übersprungenen Dateien einzeln benannt, Kaltstartlatenz sauber (kein Leerbegriff). Rechenblatt + Kostendeckel VOR dem Start zur Owner-Freigabe; Runbook-Disziplin (Cron-Intervall-Gate, Digest-Wechsel, Rohdaten committen)
- [ ] **MESS-08**: Dieselbe Anfahrt misst die neuen v1.3-Zahlen: reale Indexgröße bei sechs befüllten Sprachfeldern am Korpus-Snapshot und Wandzeit des Re-Analyse-Umbaus (Schätzung 1 bis 3 h gegen 19 h 20 min Vollreindex belegen)
- [ ] **MESS-09**: Der disjunction_max-Entscheid fällt auf Messbasis: Rangverschiebung `disjunction_max_query` gegen Score-Summe auf echten Daten; bei belegtem Vorteil umgesetzt, sonst dokumentiert verworfen

### Härtung und Release (HART/REL, Fortsetzung ab HART-03/REL-02)

- [ ] **HART-04**: Aufräumbefunde geschlossen: `fastembed==0.8.0`-Pin geklärt (unbenutzt entfernen oder Import belegen), `numpy` sauber deklariert oder als Abhängigkeit eliminiert
- [ ] **HART-05**: Dokumentierte Grenzen des Sprachausbaus in Doku und Store-Text (año/ano fallen zusammen, pt-Rechtschreibreform wird nicht vereinheitlicht, Komposita nur de/nl, FR hat weiterhin kein Körperfeld)
- [ ] **REL-03**: v1.3.0 eingereicht: signiertes App-Paar, Ende-zu-Ende-Upgrade-Beweis 1.2.0 auf 1.3.0 in CI (inkl. Umbau-Fall), Store-Texte gate-konform mit Owner-Abnahme, Submission mit 2x HTTP 201

## Future Requirements (deferred)

- Französisches Körperfeld (FR hat OCR + Katalog, aber keine lexikalische Kette; benannte Lücke, v1.4-Kandidat)
- Getrennte pt_BR/pt_PT-Wortlaute für die Suche selbst
- Niederländische Betonungsakzente als eigene custom_stopword-Liste
- Sortierung nach Name oder Größe (Fast-Field, SCHEMA_VERSION-Sprung; könnte künftig mit einem ohnehin fälligen Umbau reisen)
- Mimetype-Gruppen aus `files.mime`, geplantes Vorwärmen, Pro-Schiene (Verschlüsselung, External Storage; ISV-Entscheid 03.11.)

## Out of Scope

- Automatische Spracherkennung (dokument- wie anfrageseitig): stiller Totalausfall bei Fehlerkennung, RAM/Lizenz/ARM-Probleme aller Kandidaten, Anfragen im Mittel 2,4 Terme
- Sprachumschalter/Sprach-Chip in der UI (widerspricht Zero-Config)
- Alle sechs Sprachen ab Werk an (68 bis 90 % Indexwachstum ohne Nachfrage)
- Ein gemeinsames multilinguales Feld oder ein Index je Sprache (unter-/überstemmt bzw. Writer-Locks und Ergebnis-Fusion von Hand)
- Komposita-Zerlegung für es/it/pt (romanische Sprachen komponieren nicht wie de/nl)
- Estnisch/Dänisch lexikalisch (estonian-Stemmer von tantivy nicht unterstützt; OCR dan/est fährt seit v1.2.0 mit, das deckt die EU-Outreach-Zusagen)

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| LEX-01 | Phase 17 (Owner-Tor und Analyseketten) | Pending |
| LEX-07 | Phase 17 (Owner-Tor und Analyseketten) | Pending |
| LEX-02 | Phase 18 (Schema, Marken und Umbauweg) | Pending |
| LEX-03 | Phase 18 (Schema, Marken und Umbauweg) | Pending |
| LEX-04 | Phase 18 (Schema, Marken und Umbauweg) | Pending |
| LEX-06 | Phase 18 (Schema, Marken und Umbauweg) | Pending |
| LEX-08 | Phase 18 (Schema, Marken und Umbauweg) | Pending |
| LEX-05 | Phase 19 (Frageseite freischalten) | Pending |
| KAT-01 | Phase 20 (UI-Kataloge es/it/nl/pt) | Pending |
| KAT-02 | Phase 20 (UI-Kataloge es/it/nl/pt) | Pending |
| KOMP-01 | Phase 21 (Niederländische Komposita) | Pending |
| MESS-07 | Phase 22 (Messanfahrt BL-F03) | Pending |
| MESS-08 | Phase 22 (Messanfahrt BL-F03) | Pending |
| MESS-09 | Phase 22 (Messanfahrt BL-F03) | Pending |
| HART-04 | Phase 23 (Härtung und Store-Einreichung 1.3.0) | Pending |
| HART-05 | Phase 23 (Härtung und Store-Einreichung 1.3.0) | Pending |
| REL-03 | Phase 23 (Härtung und Store-Einreichung 1.3.0) | Pending |

**Abdeckung:** 17 von 17 v1.3-Requirements einer Phase zugeordnet, keine Waise, keine Doppelung.

**Anmerkung zu LEX-08:** Die umgedrehte Upgrade-Beweisstrecke und die Sprachfälle je Sprache
gehören zur Phase 18, weil sie den Umbauweg beweisen. Auf Feldebene sind sie dort grün; die
Hebung derselben Sprachfälle auf den normalen Suchweg (Unified Search und Ergebnisseite) ist
Erfolgskriterium 1 von Phase 19, weil die Frageseite vorher bewusst geschlossen bleibt.

---
*Erstellt: 2026-09-23 aus Research (Commit 035c5df) und Owner-Scope-Entscheid.*
*Traceability ergänzt: 2026-09-23 durch die Roadmap v1.3 (Phasen 17 bis 23).*
