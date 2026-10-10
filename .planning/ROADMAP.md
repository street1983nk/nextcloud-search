# Roadmap: Findling

## Milestones

- [x] **v1.0 Volltext, OCR und semantische Suche** -- Shipped 2026-09-07 (Phasen 1-6 + 06.1, Archiv: .planning/milestones/v1.0-ROADMAP.md)
- [x] **v1.1 Qualitaet und Effizienz** -- Shipped 2026-09-11 (Phasen 7 bis 11, Archiv: .planning/milestones/v1.1-ROADMAP.md)
- [x] **v1.2 Messbeleg und Ausbau** -- Shipped 2026-09-21 (Phasen 12 bis 16, Archiv: .planning/milestones/v1.2-ROADMAP.md)
- [x] **v1.3 Sprachausbau** -- Shipped 2026-09-27 (Phasen 17 bis 23, Archiv: .planning/milestones/v1.3-ROADMAP.md)
- [x] **v1.4 Leistungsprofile** -- Shipped 2026-10-06 (Phasen 24 bis 29, Archiv: .planning/milestones/v1.4-ROADMAP.md)
- [ ] **v1.5 Umsteiger-Release** -- in Arbeit (Phasen 30 bis 36)

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

<details>
<summary>v1.4 Leistungsprofile (Phasen 24-29) -- SHIPPED 2026-10-06</summary>

- [x] Phase 24: Owner-Tor, Profil-Geruest und Marken-Reparatur (6/6 Plaene) -- completed 2026-09-28
- [x] Phase 25: Einbettungsspur und Modellwahl (12/12 Plaene) -- completed 2026-09-28
- [x] Phase 26: N OCR-Slots und Speicherwaechter (14/14 Plaene) -- completed 2026-09-29
- [x] Phase 27: Vorab-Pruefung und Settings-Oberflaeche (16/16 Plaene) -- completed 2026-09-29
- [x] Phase 28: Abnahme-Anfahrt (14/14 Plaene) -- completed 2026-10-06, Owner-Abnahme "approved", secured 71/71
- [x] Phase 29: Haertung und Store-Einreichung 1.4.0 (16/16 Plaene) -- completed 2026-10-06, v1.4.0 im Store (2x HTTP 201), secured 65/65

Details im Archiv: .planning/milestones/v1.4-ROADMAP.md

</details>

### v1.5 Umsteiger-Release (Phasen 30-36) -- in Arbeit

**Milestone-Ziel:** Wer heute fulltextsearch mit Elasticsearch betreibt, findet keinen Grund mehr zu bleiben.

**Reihenfolge-Logik:** Alle Schema- und Markenaenderungen des Milestones (tschechisches Koerperfeld, eventuelle Felder fuer Archiv-Mitglieder) fallen in Phase 30 in EINEM Schritt, damit ein Re-Analyse-Umbau hoechstens einmal faellt. Die Formate (Phase 31) bauen auf diesem eingefrorenen Schema auf und bringen nur den Nachholweg fuer bisher uebersprungene Dateien mit. Die Umstiegs-Doku (Phase 34) kommt nach den Funktionsphasen, weil ihr Funktionsvergleich nur Geliefertes nennen darf. Die Stretch-Phase 35 kann ohne Release-Risiko ganz oder teilweise entfallen.

- [ ] **Phase 30: Owner-Tor, Schema und Tschechisch** - Offene Owner-Entscheide klaeren, Schema/Marken fuer v1.5 einmalig festlegen, Tschechisch fuer OCR und lexikalische Suche
- [ ] **Phase 31: Neue Formate und Nachholweg** - .eml, ZIP-Inhalte, .doc, .xls, HEIC indexierbar; Altbestand wird nach dem Upgrade selbsttaetig nachgeholt; F-29-03 behoben
- [ ] **Phase 32: Filter in der Unified Search** - Dateityp- und Ordnerfilter direkt in der Nextcloud Unified Search
- [ ] **Phase 33: Ausschlussmuster und Admin-Feinschliff** - Platzhalter-Ausschluesse inkl. Mac-Bundles (#22), Grenzwerte sichtbar (#21), Hardware-Hinweis umformuliert
- [ ] **Phase 34: Umstiegsweg** - Umstiegs-Seite dreisprachig, Admin-Hinweis bei parallelem fulltextsearch, Verlinkung aus README und Store-Text
- [ ] **Phase 35: Stretch: Aehnliche Dokumente und Spikes** - Aehnliche Dokumente ueber vorhandene Vektoren, granite-Messbericht, #25-Dedup-Designnotiz (entfaellt bei Bedarf ohne Release-Risiko)
- [ ] **Phase 36: Haertung und Store-Einreichung 1.5.0** - Launch-Haertung mit boesartigem Formatkorpus und Upgrade-Strecke 1.4.2 -> 1.5.0, danach Einreichung beider Apps

## Phase Details

### Phase 30: Owner-Tor, Schema und Tschechisch
**Goal**: Alle offenen Owner-Entscheide des Milestones sind getroffen, das Schema fuer v1.5 steht in einem einzigen Schritt fest, und Admins koennen Tschechisch fuer OCR und lexikalische Suche einschalten
**Depends on**: Nichts (erste Phase des Milestones; baut auf v1.4.2 auf)
**Requirements**: CZ-01, CZ-02, CZ-03
**Owner-Tor (vor jedem Bau)**: Ausschlussmuster-Syntax (Platzhalter-Dialekt, Grenzen fuer Zahl und Laenge, Verhaeltnis zu den bestehenden Praefix-Ausschluessen; fuer Phase 33), Quelle und Lizenz der tschechischen Stoppwortliste (fuer CZ-02), Trefferdarstellung "Archiv + innere Datei" und ob dafuer ein Schemafeld noetig ist (fuer FMT-02, damit der Schemaschritt hier mitfaellt), Umfang des Nachholwegs FMT-06 (welche Urteile werden nachgeholt).
**Success Criteria** (what must be TRUE):
  1. Admin kann `ces` als OCR-Sprache waehlen; ein tschechischer Scan liefert danach Treffer, und die Bau-Pruefung im Image weist das Sprachpaket nach (Weg wie dan/est)
  2. Admin kann `cs` lexikalisch einschalten; nach dem Re-Analyse-Umbau findet eine tschechische Anfrage mit und ohne Akzente (z. B. "smlouva" / "Smlouvě" in Kleinschreibung gefaltet) das Dokument, Stoppwoerter erzeugen keine Treffer, die Stoppwortliste traegt einen Lizenzbeleg im Repo
  3. Eine Bestandsinstallation ohne `cs` upgradet von 1.4.2 ohne Umbau und ohne Neu-Einbettung; Beweis in der Upgrade-CI-Strecke (UPGRADE_FROM_TAG=v1.4.2), Umbau in beide Richtungen fuer `cs` ebenfalls in CI bewiesen
  4. Das Schema traegt nach dieser Phase alle Felder, die v1.5 braucht (auch fuer Archiv-Mitglieder, falls im Tor so entschieden); spaetere v1.5-Phasen aendern weder Schema noch Indexmarken
  5. Die Grenze "tschechische Suche ohne Stammformreduktion" steht in der Doku (dreisprachig) und in der Grenzliste
**Plans**: 9 plans
Plans:
- [x] 30-01-PLAN.md: Tschechische Stoppliste aus Lucene 10.5.2 (gefaltet, Ausnahmen geprüft, Lizenzbeleg) und stemmerlose Kette cs
- [x] 30-02-PLAN.md: OCR-Sprache ces im Image, Allowlist, Bau-Prüfung und Bild-Beweis
- [x] 30-03-PLAN.md: Schema-2-Layout einfrieren, Ratsche ("2","3")/("1","3"), Pflicht-Fix _of_the_marks, Prüfzeile A5
- [x] 30-04-PLAN.md: Sprache cs, Feld body_cs, SCHEMA_VERSION 3, GOLD_V1_5
- [x] 30-05-PLAN.md: pytest-Beweis: Bestand ohne Umbau, cs an und aus, Feldebene, Messung A2
- [x] 30-06-PLAN.md: Upgrade-Strecke auf v1.4.2, Bestand de,en ohne Umbau in deploy-harp
- [x] 30-07-PLAN.md: deploy-harp Store upgrade 6/7: cs an und wieder aus
- [x] 30-08-PLAN.md: Doku, Grenzliste mit fünf Einträgen, Store-Texte und READMEs
- [ ] 30-09-PLAN.md: Security-, Bug- und Performance-Audit der Phase, Befunde fixen, 30-AUDIT.md
**UI hint**: yes

### Phase 31: Neue Formate und Nachholweg
**Goal**: Nutzer finden Inhalte aus Mails, ZIP-Archiven, Legacy-Word/-Excel und iPhone-Fotos, und Bestandsinstallationen holen bisher uebersprungene Dateien nach dem Upgrade von selbst nach
**Depends on**: Phase 30 (eingefrorenes Schema, Tor-Entscheide zu Archiv-Darstellung und Nachholumfang)
**Requirements**: FMT-01, FMT-02, FMT-03, FMT-04, FMT-05, FMT-06, POL-02
**Success Criteria** (what must be TRUE):
  1. Nutzer findet eine `.eml`-Datei ueber Betreff, Absender, Empfaenger und Textinhalt (auch wenn die Mail nur einen HTML-Teil hat)
  2. Nutzer findet Text aus einer Datei in einem ZIP-Archiv, der Treffer zeigt Archiv und innere Datei; eine Zip-Bombe (Tiefe, Gesamtgroesse, Dateianzahl oder Kompressionsrate ueber der Grenze) endet als sichtbares Skip-Urteil, der Container laeuft weiter
  3. Nutzer findet Text aus `.doc`, `.xls` und HEIC/HEIF-Fotos (OCR) ohne LibreOffice im Image, auf amd64 und arm64; `.xls` haelt dieselbe Zellgrenze wie XLSX, nicht lesbare OLE-Varianten enden als benanntes Skip-Urteil
  4. Nach dem Upgrade von 1.4.2 werden Dateien, die bisher als `legacy_format` bzw. nicht unterstuetzt uebersprungen wurden, ohne Admin-Eingriff nachgeholt; Beweis in der Upgrade-CI-Strecke mit Saatdateien, ohne Vollreindex und ohne Neu-Einbettung des Restbestands
  5. Eine Datei mit veralteter Groesse im Dateicache endet nicht mehr als `repeatedly_stuck`, sondern wird gelesen oder mit benanntem Urteil uebersprungen (F-29-03, Regressionstest)
**Plans**: TBD

### Phase 32: Filter in der Unified Search
**Goal**: Nutzer koennen direkt in der Nextcloud Unified Search nach Dateityp und Ordner filtern, ohne die Ergebnisseite zu oeffnen
**Depends on**: Phase 30 (Schema eingefroren)
**Requirements**: USRCH-01, USRCH-02, USRCH-03
**Success Criteria** (what must be TRUE):
  1. Nutzer waehlt in der Unified Search einen der sechs Typfilter des Findling-Providers und sieht nur Treffer dieses Typs
  2. Nutzer schraenkt die Suche auf einen Ordner ein und sieht nur Treffer aus diesem Ordner und seinen Unterordnern; Treffer ohne Leserecht erscheinen weiterhin nie (finaler PHP-Recheck unveraendert)
  3. Unbekannte, leere oder manipulierte Filterwerte werden ignoriert: die Suche liefert dieselben Treffer wie ohne Filter, nie eine leere Liste oder einen Fehler (Regressionstest auf PHP- und Backend-Seite)
**Plans**: TBD
**UI hint**: yes

### Phase 33: Ausschlussmuster und Admin-Feinschliff
**Goal**: Admins koennen Pfade per Platzhalter ausschliessen (inklusive Mac-Bundles aus #22) und sehen die wirksamen Grenzwerte auf der Admin-Seite
**Depends on**: Phase 30 (Tor-Entscheid zur Ausschlussmuster-Syntax)
**Requirements**: EXCL-01, EXCL-02, EXCL-03, POL-01, POL-03
**Success Criteria** (what must be TRUE):
  1. Admin pflegt auf der Admin-Seite Muster wie `*.photoslibrary` oder `*/node_modules/*`; bestehende Praefix-Ausschluesse aus 1.4.2 wirken nach dem Upgrade unveraendert weiter
  2. Mit einer einzigen Regel verschwindet ein Mac-Bundle-Ordner (z. B. `.photoslibrary`) komplett aus dem Index, auch bereits indexierte Treffer daraus
  3. Ausgeschlossene Dateien erscheinen in Status und Diagnose als "excluded", nie als Fehler; zu viele, zu lange oder Regex-artige Eingaben werden mit verstaendlicher Meldung abgelehnt (kein ReDoS)
  4. Admin sieht Zellgrenze, Adressraum, Groessengrenze und OCR-Seitendeckel nur lesend auf der Admin-Seite, mit Hinweis, wie sie geaendert werden (#21)
  5. Der Hardware-Hinweis ("This box has fewer cores...") ist in allen Katalogen verstaendlich umformuliert, die Katalog-Gates bleiben gruen
**Plans**: TBD
**UI hint**: yes

### Phase 34: Umstiegsweg
**Goal**: Ein Admin mit fulltextsearch/Elasticsearch findet einen klaren, ehrlichen Weg zu Findling und wird gewarnt, solange beide parallel laufen
**Depends on**: Phasen 31, 32, 33 (Funktionsvergleich nennt nur Geliefertes)
**Requirements**: UMST-01, UMST-02, UMST-03
**Success Criteria** (what must be TRUE):
  1. Admin findet die Seite "Von fulltextsearch/Elasticsearch umsteigen" auf Deutsch, Englisch und Franzoesisch mit Abschalt-Schritten, Funktionsvergleich als Faktenliste und dem Wortlaut "OCR ohne Dateiaenderung und ohne Elasticsearch"; die Formulierung "einzige OCR" kommt nirgends vor (Gate)
  2. Ist fulltextsearch oder files_fulltextsearch parallel aktiv, sieht der Admin auf der Findling-Admin-Seite einen Hinweis mit Folge (doppelte Treffer) und Link auf die Umstiegs-Seite; ohne die alten Apps erscheint nichts
  3. README (de/en/fr) und Store-Textentwurf verlinken die Umstiegs-Seite, der Entwurf haelt die Kurztext-Regel und liegt dem Owner zur Abnahme vor
**Plans**: TBD
**UI hint**: yes

### Phase 35: Stretch: Aehnliche Dokumente und Spikes
**Goal**: Nutzer koennen zu einem Treffer aehnliche Dokumente abrufen, und fuer v1.6 liegen belastbare Entscheidungsvorlagen zu granite und #25-Dedup vor; die Phase kann ganz oder teilweise entfallen, ohne den Release zu gefaehrden
**Depends on**: Phase 30 (unabhaengig von 31 bis 34; Reihenfolge nur aus Kapazitaetsgruenden vor der Haertung)
**Requirements**: STR-01, STR-02, STR-03
**Success Criteria** (what must be TRUE):
  1. Nutzer klickt auf der Ergebnisseite bei einem Treffer "Aehnliche Dokumente" und bekommt Vektor-Nachbarn aus dem bestehenden Index; Dokumente ohne Leserecht erscheinen nie (PHP-Recheck), ohne Index-, Schema- oder Modellaenderung
  2. Ein Messbericht granite-embedding-97m-multilingual-r2 gegen e5-small (deutscher Korpus, Trefferqualitaet, CPU-Latenz amd64 und arm64, RAM, eigener int8-Build) liegt unter docs/measurements/ mit klarer Empfehlung fuer v1.6; das ausgelieferte Modell bleibt e5-small
  3. Eine Designnotiz zu #25-Dedup je Mount-Config (fileid-Mapping vs. per-User-Crawl, ACL-Folgen) liegt als Entscheidungsvorlage fuer den Owner vor
**Plans**: TBD
**UI hint**: yes

### Phase 36: Haertung und Store-Einreichung 1.5.0
**Goal**: Findling 1.5.0 ist ueber den Happy Path hinaus gehaertet und beide Apps sind nach Owner-Abnahme im Store eingereicht
**Depends on**: Phase 34 (Phase 35, soweit geliefert)
**Requirements**: HART-06, REL-05
**Success Criteria** (what must be TRUE):
  1. Audit Security/Bugs/Performance endet mit 0 CRIT / 0 HIGH; boesartige Archive (Bomben, Pfad-Traversal, Verschachtelung), Mails und OLE-Dateien aus einem Testkorpus enden als benannte Urteile ohne Absturz und ohne Speicherueberlauf
  2. Upgrade-Strecke 1.4.2 -> 1.5.0 laeuft in CI Ende zu Ende gruen (Nachholweg, Ausschluesse, ohne Umbau bei Werkssprachen) und eine Fremdinstallation auf frischer Nextcloud funktioniert
  3. Owner hat Store-Text und Produkt in einer gemeinsamen Playwright-Runde mit echten Testdateien abgenommen
  4. Beide Apps 1.5.0 sind eingereicht (2x HTTP 201), der Beleg steht in docs/store-listing.md
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-6 + 06.1 (Archiv) | v1.0 | 103/103 | Complete | 2026-09-07 |
| 7-11 (Archiv) | v1.1 | 37/37 | Complete | 2026-09-11 |
| 12-16 (Archiv) | v1.2 | 63/63 | Complete | 2026-09-21 |
| 17-23 (Archiv) | v1.3 | 69/69 | Complete | 2026-09-27 |
| 24-29 (Archiv) | v1.4 | 78/78 | Complete | 2026-10-06 |
| 30. Owner-Tor, Schema und Tschechisch | v1.5 | 8/9 | In Progress|  |
| 31. Neue Formate und Nachholweg | v1.5 | 0/? | Not started | - |
| 32. Filter in der Unified Search | v1.5 | 0/? | Not started | - |
| 33. Ausschlussmuster und Admin-Feinschliff | v1.5 | 0/? | Not started | - |
| 34. Umstiegsweg | v1.5 | 0/? | Not started | - |
| 35. Stretch: Aehnliche Dokumente und Spikes | v1.5 | 0/? | Not started | - |
| 36. Haertung und Store-Einreichung 1.5.0 | v1.5 | 0/? | Not started | - |

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
*Created: 2026-09-08. v1.1 archiviert: 2026-09-11. v1.2 archiviert: 2026-09-21. v1.3 archiviert: 2026-09-27. v1.4-Roadmap: 2026-09-27. v1.5-Roadmap: 2026-10-10.*
