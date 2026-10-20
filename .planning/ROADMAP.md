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

- [x] **Phase 30: Owner-Tor, Schema und Tschechisch** - Offene Owner-Entscheide klaeren, Schema/Marken fuer v1.5 einmalig festlegen, Tschechisch fuer OCR und lexikalische Suche
- [x] **Phase 31: Neue Formate und Nachholweg** - .eml, ZIP-Inhalte, .doc, .xls, HEIC indexierbar; Altbestand wird nach dem Upgrade selbsttaetig nachgeholt; F-29-03 behoben
- [x] **Phase 32: Filter in der Unified Search** - Dateityp- und Ordnerfilter direkt in der Nextcloud Unified Search
- [x] **Phase 33: Ausschlussmuster und Admin-Feinschliff** - Platzhalter-Ausschluesse inkl. Mac-Bundles (#22), Grenzwerte sichtbar (#21), Hardware-Hinweis umformuliert
- [x] **Phase 34: Umstiegsweg** - Umstiegs-Seite dreisprachig, Admin-Hinweis bei parallelem fulltextsearch, Verlinkung aus README und Store-Text (completed 2026-10-19)
- [x] **Phase 35: Stretch: Aehnliche Dokumente und Spikes** - Aehnliche Dokumente ueber vorhandene Vektoren, granite-Messbericht, #25-Dedup-Designnotiz (entfaellt bei Bedarf ohne Release-Risiko) (completed 2026-10-20)
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
- [x] 30-09-PLAN.md: Security-, Bug- und Performance-Audit der Phase, Befunde fixen, 30-AUDIT.md

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

**Plans**: 15 plans (seriell, eine Welle je Plan)
Plans:

- [x] 31-01-PLAN.md: olefile, xlrd, pillow-heif gepinnt, Lizenzbelege (x265/libheif/libde265), THIRD-PARTY-Altversionen korrigiert, Imagegröße gemessen
- [x] 31-02-PLAN.md: Skip-Code archive_limit, allgemeineres unsupported_variant, l10n-Kette (16 Dateien + 5 Dokus), Verdict-Generation 3 mit weiter gültiger 2
- [x] 31-03-PLAN.md: POL-02, zweimal gleich kurz mit gleichem Hash = echte Datei (F-29-03)
- [x] 31-04-PLAN.md: .eml-Extraktor (Kopfzeilen, Text, HTML-only, Anhänge nur Namen)
- [x] 31-05-PLAN.md: .doc-Extraktor über olefile und Piece Table, Sniff, benannte Urteile
- [x] 31-06-PLAN.md: .xls-Extraktor mit XLSX-Zellgrenze, OLE-Word/Excel unter OOXML-Namen lesen
- [x] 31-07-PLAN.md: HEIC/HEIF im Bildpfad, RAM-Messung amd64/arm64, Speicherfaktor, Image-Probe
- [x] 31-08-PLAN.md: ZIP-Extraktor, EOCD-Vorprüfung, Grenzwerte gemessen (D-31-07), Bombenkorpus
- [x] 31-09-PLAN.md: Auszug nennt die innere Datei (ohne Schemafeld)
- [x] 31-10-PLAN.md: Freischaltung beider Allowlists, Typgruppen (zip in keiner), Minor-Migration 1.5
- [x] 31-11-PLAN.md: einmaliger Nachholweg recheck_1_5_0 (Teil A state.db inkl. repeatedly_stuck, Teil B Abgleich)
- [x] 31-12-PLAN.md: deploy-harp: Saat der neuen Formate unter v1.4.2, Aufzeichnung vor dem Upgrade
- [x] 31-13-PLAN.md: deploy-harp: Store upgrade 5 Altbestand/Saat getrennt, L-30-03, Strecke 0 bis 7 grün
- [x] 31-14-PLAN.md: docs/formats.md, Store-Text-Entwurf v1.5.0 (Teil Phase 31) zur Abnahme REL-05
- [x] 31-15-PLAN.md: Security-, Bug- und Performance-Audit mit bösartigem Formatkorpus, Befunde fixen

### Phase 32: Filter in der Unified Search

**Goal**: Nutzer koennen direkt in der Nextcloud Unified Search nach Dateityp und Ordner filtern, ohne die Ergebnisseite zu oeffnen
**Depends on**: Phase 30 (Schema eingefroren)
**Requirements**: USRCH-01, USRCH-02, USRCH-03
**Success Criteria** (what must be TRUE):

  1. Nutzer waehlt in der Unified Search einen der sechs Typfilter des Findling-Providers und sieht nur Treffer dieses Typs
  2. Nutzer schraenkt die Suche auf einen Ordner ein und sieht nur Treffer aus diesem Ordner und seinen Unterordnern; Treffer ohne Leserecht erscheinen weiterhin nie (finaler PHP-Recheck unveraendert)
  3. Unbekannte, leere oder manipulierte Filterwerte werden ignoriert: die Suche liefert dieselben Treffer wie ohne Filter, nie eine leere Liste oder einen Fehler (Regressionstest auf PHP- und Backend-Seite)

**Plans**: 8 plans (seriell, eine Welle je Plan)
Plans:

- [x] 32-01-PLAN.md: Typfilter serverseitig (FilterDefinition types, gemeinsamer Parser, Tür mit types, D-05 umgedreht), Paritätstest und leere Liste im Backend
- [x] 32-02-PLAN.md: Ordnerfilter in PHP (folder, Folder::get, Vorauswahl über Koordinaten, Recheck im Unterbaum, fail-open)
- [x] 32-03-PLAN.md: Ordnerbudget gemessen (enger Ordner, Treffer tief im Ranking), Konstanten belegt
- [x] 32-04-PLAN.md: Listener auf jeder angemeldeten Seite, Vanilla-Plugin mit sieben Filtereinträgen, Vertragstest
- [x] 32-05-PLAN.md: l10n-Kette der vier neuen Sätze (16 Kataloge, 5 Dokus)
- [x] 32-06-PLAN.md: deploy-harp auf 33/34/35/arm64, Gruppenordner und Share in team-folder-acl, Doku und Store-Entwurf Teil Phase 32
- [x] 32-07-PLAN.md: Owner-Abnahme gemeinsam per Playwright (Checkpoint), Wortlaut nachziehen
- [x] 32-08-PLAN.md: Security-, Bug- und Performance-Audit mit Korpus manipulierter Filterwerte, Befunde fixen

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

**Plans**: 11 plans (seriell, eine Welle je Plan)
Plans:

- [x] 33-01-PLAN.md: Wortlaut-Entwurf en/de/fr (Musterliste, Meldungen je Code, Grenzblock, Änderungshinweis, Hardware-Satz), Owner-Abnahme (Checkpoint) (abgenommen 13.10.2026, 45c00a2f)
- [x] 33-02-PLAN.md: ExclusionService mit Mustern (exclusion_patterns, Codes, NFC, bitparalleler Matcher, hasRules an drei Guards), Gate D, ExclusionServiceTest (75f5f29e, 3c1d5a97)
- [x] 33-03-PLAN.md: Container: Weg C im Abgleich (D-33-01), Statusfelder maxCells und extractAddressSpaceBytes (eff4a9bf)
- [x] 33-04-PLAN.md: Weg A: ExclusionSweepJob beim Speichern neuer Muster, Urteilszeilen in beiden Räumwegen gelöscht (B2) (14d6b591)
- [x] 33-05-PLAN.md: Admin-Seite: Liste Excluded patterns, Routen mit zwei Listen, Meldung je Code, zahlenlose Bestätigung, Diagnose-Abhilfe (2aa25e56)
- [x] 33-06-PLAN.md: Admin-Seite: Grenzblock nur lesend mit Änderungshinweis, B3-Satz ersetzt, Doku-Abschnitt (72d1c032)
- [x] 33-07-PLAN.md: l10n-Kette (16 Kataloge, 5 Dokus), Hardware-Satz POL-03, Regelblock-Gate, Schlüsselzahl (0fb85deb)
- [x] 33-08-PLAN.md: Doku (admin-page.md, reconcile.md), CHANGELOG, Store-Entwurf Teil Phase 33 (Abnahme REL-05) (57739fe8)
- [x] 33-09-PLAN.md: Nachweis EXCL-02 auf 8090 über Weg A und Weg C mit Positivkontrolle und Gegenprobe
- [x] 33-10-PLAN.md: Owner-Abnahme gemeinsam per Playwright (Checkpoint), Wortlaut nachziehen (fr-Einheiten Mo, 18.10.2026); Anforderungen hakt 33-11 ab
- [x] 33-11-PLAN.md: Security-, Bug- und Performance-Audit (Matcher-Orakel, Schreibpfad, Kehrjob), Befunde fixen (H-33-01 ff4deaa9, H-33-02 3657bb43, sechs LOW entschieden; EXCL-01..03, POL-01, POL-03 Complete)

**UI hint**: yes

### Phase 34: Umstiegsweg

**Goal**: Ein Admin mit fulltextsearch/Elasticsearch findet einen klaren, ehrlichen Weg zu Findling und wird gewarnt, solange beide parallel laufen
**Depends on**: Phasen 31, 32, 33 (Funktionsvergleich nennt nur Geliefertes)
**Requirements**: UMST-01, UMST-02, UMST-03
**Success Criteria** (what must be TRUE):

  1. Admin findet die Seite "Von fulltextsearch/Elasticsearch umsteigen" auf Deutsch, Englisch und Franzoesisch mit Abschalt-Schritten, Funktionsvergleich als Faktenliste und dem Wortlaut "OCR ohne Dateiaenderung und ohne Elasticsearch"; die Formulierung "einzige OCR" kommt nirgends vor (Gate)
  2. Ist fulltextsearch oder files_fulltextsearch parallel aktiv, sieht der Admin auf der Findling-Admin-Seite einen Hinweis mit Folge (doppelte Treffer) und Link auf die Umstiegs-Seite; ohne die alten Apps erscheint nichts
  3. README (de/en/fr) und Store-Textentwurf verlinken die Umstiegs-Seite, der Entwurf haelt die Kurztext-Regel und liegt dem Owner zur Abnahme vor

**Plans**: 6 plans
Plans:

- [x] 34-01-PLAN.md: Wortlaut-Entwurf de/en/fr (Seite, Hinweis, README- und Store-Zeile) und blockierender Owner-Checkpoint O2-O7, O9, O10
- [x] 34-02-PLAN.md: Abschalt-Schritte auf 8090 belegt, drei Umstiegs-Seiten, Gate test_migration_path.py
- [x] 34-03-PLAN.md: ParallelSearchService (isEnabledForAnyone) mit PHPUnit, Warnbanner mit Sprach-Link, l10n-Kette, Linkgate verallgemeinert
- [x] 34-04-PLAN.md: README-Verweise de/en/fr, Store-Entwurf Teil Phase 34, CHANGELOG, Gate-Erweiterung
- [x] 34-05-PLAN.md: Gemeinsame Playwright-Abnahme auf 8090 mit simuliertem App-Flag (D-34-02)
- [x] 34-06-PLAN.md: Security-, Bug- und Performance-Audit, UMST-01 bis UMST-03 abhaken

**UI hint**: yes

### Phase 35: Stretch: Aehnliche Dokumente und Spikes

**Goal**: Nutzer koennen zu einem Treffer aehnliche Dokumente abrufen, und fuer v1.6 liegen belastbare Entscheidungsvorlagen zu granite und #25-Dedup vor; die Phase kann ganz oder teilweise entfallen, ohne den Release zu gefaehrden
**Depends on**: Phase 30 (unabhaengig von 31 bis 34; Reihenfolge nur aus Kapazitaetsgruenden vor der Haertung)
**Requirements**: STR-01, STR-02, STR-03
**Success Criteria** (what must be TRUE):

  1. Nutzer klickt auf der Ergebnisseite bei einem Treffer "Aehnliche Dokumente" und bekommt Vektor-Nachbarn aus dem bestehenden Index; Dokumente ohne Leserecht erscheinen nie (PHP-Recheck), ohne Index-, Schema- oder Modellaenderung
  2. Ein Messbericht granite-embedding-97m-multilingual-r2 gegen e5-small (deutscher Korpus, Trefferqualitaet, CPU-Latenz amd64 und arm64, RAM, eigener int8-Build) liegt unter docs/measurements/ mit klarer Empfehlung fuer v1.6; das ausgelieferte Modell bleibt e5-small
  3. Eine Designnotiz zu #25-Dedup je Mount-Config (fileid-Mapping vs. per-User-Crawl, ACL-Folgen) liegt als Entscheidungsvorlage fuer den Owner vor

**Plans**: 13 plans
Plans:
**Wave 1**

- [x] 35-01-PLAN.md: Wortlaut de/en/fr der Ähnlich-Ansicht, Owner-Abnahme (D-35-08)
- [x] 35-02-PLAN.md: Entscheidungsvorlage #25-Dedup je Mount-Config (STR-03)
- [x] 35-03-PLAN.md: granite-Vorbereitung: deutsches Testset auf 120, Entscheidungsregel vor der Messung, Owner-Abnahme

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 35-04-PLAN.md: centroid und Distanzlauf Dokument gegen Dokument, SIMILAR_CEILING

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 35-05-PLAN.md: Container-Route /similar (vectors_of, similar_candidates, Ratschen)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 35-06-PLAN.md: PHP-Rechtegrenze: ExAppService::similarCandidates, SearchService::similar, SimilarOutcome

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 35-07-PLAN.md: Ergebnisseite: Textlink je Treffer, Ähnlich-Ansicht, PHP-Baumhash

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 35-13-PLAN.md: Wortlaut der Ähnlich-Ansicht in 16 Katalogen und fünf Tabellen, Rendering-Probe auf 8090 (Welle direkt nach 35-07)

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 35-08-PLAN.md: Gemeinsame Playwright-Abnahme der Ähnlich-Ansicht auf 8090

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 35-09-PLAN.md: granite lokal: Pooling-Schalter, Artefakte, int8-Build, Qualität, amd64-Latenz, Image-Zuwachs

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 35-10-PLAN.md: granite arm64 auf m7g nach Owner-Freigabe, Hochrechnung Neu-Einbettung, Abbau

**Wave 10** *(blocked on Wave 9 completion)*

- [x] 35-11-PLAN.md: granite-Messbericht mit Opt-in-Bewertung und Empfehlung für v1.6

**Wave 11** *(blocked on Wave 10 completion)*

- [ ] 35-12-PLAN.md: Security-, Bug- und Performance-Audit, Anforderungen abhaken

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
  5. M-32-02 behoben (Owner 13.10.2026): Dokumente geloeschter Nutzer verlassen den Index beim naechsten Abgleich; Dokumente verschwundener externer Speicher nach 30 Tagen Karenz; Beleg auf einer Instanz mit Positivkontrolle

**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-6 + 06.1 (Archiv) | v1.0 | 103/103 | Complete | 2026-09-07 |
| 7-11 (Archiv) | v1.1 | 37/37 | Complete | 2026-09-11 |
| 12-16 (Archiv) | v1.2 | 63/63 | Complete | 2026-09-21 |
| 17-23 (Archiv) | v1.3 | 69/69 | Complete | 2026-09-27 |
| 24-29 (Archiv) | v1.4 | 78/78 | Complete | 2026-10-06 |
| 30. Owner-Tor, Schema und Tschechisch | v1.5 | 9/9 | Complete | 2026-10-10 |
| 31. Neue Formate und Nachholweg | v1.5 | 15/15 | In Progress (Verifikation offen) | - |
| 32. Filter in der Unified Search | v1.5 | 8/8 | Executed, verification pending | - |
| 33. Ausschlussmuster und Admin-Feinschliff | v1.5 | 11/11 | Executed, verification pending | - |
| 34. Umstiegsweg | v1.5 | 6/6 | Complete   | 2026-10-19 |
| 35. Stretch: Aehnliche Dokumente und Spikes | v1.5 | 13/13 | Complete   | 2026-10-20 |
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
