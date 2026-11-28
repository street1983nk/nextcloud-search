# Project Milestones: Findling (Nextcloud Zero-Config-Suche)

## v1.8 Findling 1.7.1 (Shipped: 2026-11-28)

**Delivered:** Findling 1.7.1 im Nextcloud App Store (beide Apps; Tag v1.7.1 auf a3c94c16, Release 46086508768 immutable mit zweimal Verified OK, store-submit 46089033695 mit 2x HTTP 201, Store-API beide Apps 1.7.1 am 28.11. 01:22 UTC): Patch-Release mit den fünf LOW/INFO-Punkten aus Phase 45 und #63, ohne neue Funktion und ohne Migration.

**Phases completed:** 46 (1 Phase, 12 Pläne)

**Timeline:** 27.11. bis 28.11.2026 (82 Commits, 204 Dateien, +4.387 / -141 Zeilen)

**Key accomplishments:**

- Hilfesatz der ausgeschlossenen Ordner nennt in allen neun Sprachen das Beispiel seines Feldes (EXCL-07); Enter in Ordner- und Musterfeld fügt wie der Knopf hinzu, ohne eine IME-Eingabe zu stören (EXCL-08)
- Fehlerliste unter 360 px mit dem Zustand unter dem Grund, kein Umbruch mitten im Wort bei 320 px hell und dunkel (ADM-05)
- Meldungen zu * und ? nennen ihr Beispiel in der Sprache der Seite; Pfad statt leerer Zeile bei leerem Ausschnitt in der Unified Search (#63)
- CI: Wörterbuch-Download mit Zeitlimit und Wiederholung (PRUEF-05), "Store upgrade 2b" urteilt erst nach der leeren Queue (PRUEF-06)
- Volltest DE/EN/FR, gemeinsame Abnahme, Signatur-Probe, secure-phase vor dem Tag (22 IDs, zwei Beleglücken per Docker-Fenster und Owner-Korrektur geschlossen, unabhängig nachgeprüft), Release-Threats nach dem Tag (29 IDs, threats_open 0) (REL-08)

**Nachweise:** kein v1.8-MILESTONE-AUDIT; Nachweise: 46-SECURITY.md, 46-AUDIT.md, 46-ABNAHME.md, 46-VOLLTEST.md, docs/store-listing.md "# Release 1.7.1 (28.11.2026)".

**Vorbehalte:** Phase 46 ohne VERIFICATION-Datei (Abnahme über SECURITY, AUDIT, ABNAHME und VOLLTEST); die automatische Prüfung von 46-12 Task 1 ist wegen dreier Planfehler rot (46-12-SUMMARY.md); PR #60 (body_zh, Schema 3 auf 4) wartet auf das Review für 1.8.0; #63 offen bis zur Rückmeldung des Melders.

Known deferred items at close: 13 (see STATE.md Deferred Items, unverändert seit v1.6)

---

## v1.7 Findling 1.7.0 (Shipped: 2026-11-26)

**Delivered:** Findling 1.7.0 im Nextcloud App Store (beide Apps; Tag v1.7.0 auf 22f98ef2, Release 45895635994 immutable mit zweimal Verified OK, store-submit 45898491529 mit 2x HTTP 201, Store-API beide Apps 1.7.0 am 27.11. 00:18 und 00:29 UTC): Ausschluss je externem Speicher mit Anzeige freier Plätze (#45), Traditional Chinese (PRs #56, #57 von foolfitz), Lesen unter dem Wasserzeichen von Nextcloud Office als Besitzer ohne Umgehung der Sperre (#59), Abgleich ohne Bremse durch Nachzählung und lange Warteschlange plus Rückfallsicherung für kreisende Dateien (#25), kurze Store-Texte mit Link auf die Doku; vorher die PHP-Sicherheits-Gates aus Phase 42 Kriterium 3.

**Phases completed:** 44 bis 45 (2 Phasen, 37 Pläne)

**Timeline:** 21.11. bis 27.11.2026 (240 Commits, 274 Dateien, +42.105 / -1.679 Zeilen)

**Key accomplishments:**

- Phase 44: Psalm mit Taint-Analyse gegen OCP 33, 34 und 35 (Befunde aus SARIF selbst gezählt), php-cs-fixer mit nextcloud/coding-standard, zizmor und actionlint, je mit Positivkontrolle rot; Strukturgate gegen stilles Entfernen (PRUEF-02 bis 04)
- Ausschluss je externem Speicher (nur Admin-Speicher, Nutzerspeicher folgen dem Hauptschalter), freie Plätze für Ordner und Muster, Platzhalter-Hinweise in 18 Katalogen (#45, EXCL-04 bis 06)
- zh_TW-Katalog und Admin-Seite unter zh_Hant_TW inklusive Rückfall auf root.lang; 33 eigene zh_TW-Sätze zum Gegenlesen an foolfitz (#53, #56, #57, KAT-03/04)
- #59: Besitzer zuerst, erneutes Öffnen als Besitzer nur bei belegter Secure-View-Ablehnung, eigener Grund policy_blocked ("Blocked by a rule"), keine Textausschnitte unter Secure View; vorher/nachher über den Update-Weg 1.6.5 auf 1.7.0 live belegt (COMP-05)
- #25: Nachzählung hält den Abgleich nicht mehr auf (Mindestabstand sechs Stunden), Rückhalt höchstens zweimal das Intervall, nie neben einem Crawl; OCR-Übergabe derselben Bytes nach drei Durchläufen als failed(repeatedly_stuck) (IDX-09 bis 11)
- Kurze Store-Texte DE/EN/FR beider Apps nach Owner-Freigabe, verlagerte Inhalte in README und Doku mit Gates (STORE-03/04); Launch-Härtung, zweiter Volltest DE/EN/FR, secure-phase vor dem Tag (91 Threats, threats_open 0), Release-Threats nach dem Tag nachgeprüft (REL-07)

**Nachweise:** kein v1.7-MILESTONE-AUDIT; Nachweise: 44-SECURITY.md, 45-SECURITY.md, 45-AUDIT.md, 45-ABNAHME.md, 45-VOLLTEST.md, docs/store-listing.md "# Release 1.7.0 (26.11.2026)".

**Vorbehalte:** Phasen 44 und 45 ohne VERIFICATION-Datei (Abnahme über SECURITY, AUDIT, ABNAHME und VOLLTEST); fünf LOW/INFO-Punkte für 1.7.1 (I-45-10-04, I-45-10-06, I-45-10-07, I-45-10-08, I-45-12-01); #45, #59, #25 warten auf Bestätigung der Melder, PR #60 (body_zh) auf den Rebase; Dedup Weg B weiter offen.

Known deferred items at close: 13 (see STATE.md Deferred Items, unverändert seit v1.6)

---
## v1.6 Store-Sichtbarkeit und Betriebs-Feinschliff (Shipped: 2026-11-16)

**Delivered:** Findling 1.6.0 bis 1.6.5 im Nextcloud App Store (beide Apps; 1.6.0 am 29.10. über store-submit 40868132102 mit 2x HTTP 201, Tag v1.6.0 auf 91a0603f; zuletzt 1.6.5 am 16.11. über 43801394739, Tag v1.6.5 auf 06a0d7c8): Anzeigename "Findling Search" mit discussion-Link und Cross-Promo-Satz zum MCP Connector, Zertifikatsrotation ohne Re-Register und ohne Container-Neustart (#33), Erklärsatz und Stand-Hinweis an den Ausschluss-Zählern, Dedup Weg C, Backup-Pause-Schalter (#37), PHP-Sicherheits-Gates für die Companion-App, Löschlauf unabhängig vom Quiet-Gate und Zählung pro Dokument über die Freigabe-Identität (#25).

**Phases completed:** 37 bis 43 (7 Phasen, 63 Pläne)

**Timeline:** 28.10. bis 21.11.2026 (468 Commits, 400 Dateien, ~74.000 Zeilen)

**Key accomplishments:**

- Owner-Tor in einer Remote-Runde (D-37-01 bis D-37-09), Store-Sichtbarkeit mit Gates für IDs, Namen, discussion-Link und Cross-Promo-Satz in beiden info.xml (STORE-01/02, DEDUP-01)
- Tunnel-Wächter vor frpc: x509 erkennen, ratenbegrenzt mit Abhilfe melden, gedeckelter Neustart nur bei geänderten Dateien; CI-Probe mit echter CA-Neuausstellung und Positivkontrolle, Heilung in 8 bis 19 s (ZERT-01/02, #33)
- Ausschluss-Anzeige in 16 Katalogen, Dedup Weg C (Abdeckung je Schlüssel), Messung A6/A7 in CI, Weg A verworfen und Weg B auf v1.7 vertagt; Umlaut-Fixes in drei docs-Dateien, IN-01 bis IN-06 entschieden (ANZE-01/02, DEDUP-02, DOCS-01/02)
- 1.6.0 mit Audit-Gate 0 CRIT/HIGH/MEDIUM, Upgrade-Strecke ab v1.5.0, Issue-#36-Paket und Owner-GO (REL-06); Nachaudit 40-NACHAUDIT.md, Fixes F-40N-01..04 in 1.6.2
- 1.6.2: Backup-Pause über occ und Admin-Schalter (WAL-Checkpoint, Tantivy-Commit, übersteht Neustarts), Backup-Doku DE/EN/FR, embeddedLeftOut über 100 000 (#25, #37)
- Phase 42: Routen-Attribut-Gate gegen den Router des Servers als Orakel, composer validate/audit, lokales PHPUnit; Kriterium 3 (Psalm Taint, php-cs-fixer, zizmor, actionlint) als eigene Phase in v1.7 zugesagt
- 1.6.3: Löschlauf mit eigenem Stempel, Dokumentschlüssel Format 2 über die Freigabe-Identität, Abnahmetest mit sieben Beinen auf Samba-Harness; 1.6.4 Update-Fix #51, 1.6.5 Sicherheits-Update opentelemetry-api

**Nachweise:** kein v1.6-MILESTONE-AUDIT; Nachweise: Phase-VERIFICATIONs 41/42, 40-NACHAUDIT, Store-Belege docs/store-listing.md.

**Vorbehalte:** 38-VERIFICATION und 39-VERIFICATION stehen auf human_needed (Owner-Kommunikation und UI-Sichtung, kein Code-Gap; #33 am 08.11. geschlossen), 40-VERIFICATION auf gaps_found (geschlossen über 40-NACHAUDIT.md und 41-01, Restpunkte in deferred-items.md), Phase 43 ohne VERIFICATION-Datei (Abnahme über 43-ABNAHME.md und 43-AUDIT.md); 1.6.3 der Begleit-App wurde aus dem Store entfernt und durch 1.6.4 ersetzt; Dedup Weg B und Kriterium 3 aus Phase 42 nach v1.7.

Known deferred items at close: 13 (see STATE.md Deferred Items)

---

## v1.5 Umsteiger-Release (Shipped: 2026-10-28)

**Delivered:** Findling 1.5.0 im Nextcloud App Store (beide Apps, Submission-Lauf 39598694849 mit 2x HTTP 201 am 21.10., Tag v1.5.0 auf 6c953a76; 1.5.1 als Nachzuegler ebenfalls im Store): Tschechisch als siebte Suchsprache (Stoppliste aus Lucene, cs ausserhalb Snowball, OCR-Option ces), sechs neue Dateitypen (DOC, XLS, Mails/EML, ZIP mit Auszug der inneren Datei, HEIC/HEIF) samt Nachholweg fuer Bestandsinstallationen, Typ- und Ordnerfilter in der Unified Search, Ausschlussmuster mit bitparallelem Matcher (#22) und sichtbare Grenzwerte (#21), dreisprachige Umstiegs-Seite vom fulltextsearch-Framework mit Admin-Banner bei Parallelbetrieb, Aehnliche-Dokumente-Ansicht, Launch-Haertung mit boesartigem Formatkorpus (blocked_malicious ueber die ganze Kette) und bewiesener Upgrade-Strecke.

**Phases completed:** 30 bis 36 (7 Phasen, 79 Plaene)

**Timeline:** 06.10. bis 28.10.2026 (402 Commits, 626 Dateien, ~100.000 Zeilen inkl. Mess-Rohdaten)

**Key accomplishments:**

- Tschechisch end-to-end: Schema 3 mit body_cs als 14. Feld, Re-Analyse ohne Neu-Einbettung in beide Richtungen in CI bewiesen (Store upgrade 6/7), Platzzuwachs gemessen 0,29 bis 0,36 unter dem 0,40-Budget
- Sechs neue Formate in reinem Python mit eigener Haertung: FIB/Clx-Leser fuer DOC nach [MS-DOC], CFB-Kettenpruefung vor xlrd (Endlosschleifen-Befund), Mail-Vorzaehlung deklarierter Boundaries, ZIP mit einem Budget ueber alle Ebenen (Quine-, Overlap- und Traversal-Abwehr), HEIF-Speicherschaetzung mit mallopt-Deckel; Nachholweg recheck_1_5_0 holt Bestandsurteile in 303 s nach
- Unified-Search-Filter ohne zweites Rechtemodell: Ordner-Scope ueber Mountliste plus Recheck in PHP, versteckter FilterProvider gegen Scheingruppen, Team-Folder-ACL-Faelle in CI belegt; Messregel vor der Messung (FOLDER_MAX_ROUNDS 12 aus Korpus 1000+11)
- Ausschlussmuster als geschlossene Sprache (32 Muster zu 60 Zeichen, elf Fehlercodes, kein fnmatch/preg/eval), Differenztest gegen die byte-gleiche 1.4.2-Fixture, Weg A (Kehrjob) und Weg C (Abgleich) live belegt
- Launch-Haertung Phase 36: Korpus aus sieben Angriffsfamilien (64 Faelle) durch das Sandbox-Kind, ZIP-/Paket-/XML-Signaturen als skipped(blocked_malicious), M-32-02 geschlossen (Karenz 30 Tage fuer verschwundene Storages mit CI-Integrationstest), Zert-Lift Pillow 13/certifi, Fremdinstallation und Upgrade-Strecke v1.4.3 -> 1.5.0 gruen, Owner-Abnahme per Playwright-Runde ("okok")
- Release-Disziplin: Audit 36 mit 0 CRIT/HIGH/MEDIUM, Code-Review 0 Critical (2 Warnings gefixt), Verifier 5/5, Submission 2x HTTP 201 mit externer Gegenprobe

**Vorbehalte:** L-36-05/L-36-06 (Anzeigetext "Bewusst ausgelassen: 0", Zaehler-Verzoegerung nach Ausschlussmuster) und der #25-Dedup-Rest bewusst nach 1.6 vertagt; Review-Infos IN-01 bis IN-06 der Phase 36 als 1.6-Kandidaten; Docker auf der Entwicklerbox defekt (Phase-33/34-Audit-Tests laufen nur in CI); Zert-Rotation Issue #33 offen.

Known deferred items at close: 10 (see STATE.md Deferred Items)

---

## v1.4 Leistungsprofile (Shipped: 2026-10-06)

**Delivered:** Findling 1.4.0 im Nextcloud App Store (beide Apps, Submission-Lauf 37473805519 mit 2x HTTP 201, Tag v1.4.0 auf 99326ae2): Leistungsprofile als Opt-in (Sparsam bleibt unveraenderter Default; Standard gibt hoechstens die halbe Box frei, Leistung alles bis auf einen Kern), parallele OCR-Slots mit Speicherwaechter, parallele Einbettungsspur, Modellwahl int8/fp32, Settings-Oberflaeche mit Vorab-Pruefung, dazu alle sechs oeffentlich zugesagten #18-Fixklassen und die selbsttaetige Nachpruefung der Altbestaende nach dem Upgrade.

**Phases completed:** 24 bis 29 (6 Phasen, 78 Plaene, 175 Tasks)

**Timeline:** 27.09. bis 06.10.2026 (10 Tage, 651 Commits, 697 Dateien; die grosse Zeilenzahl ist ueberwiegend Mess-Rohdaten der Abnahme-Anfahrt)

**Key accomplishments:**

- Profil-Geruest als Anteils-Formel (economy/standard/performance) mit Hardware-Erkennung und Vorschlag, Sparsam gepinnt Wert fuer Wert; der D-24-04-Anteils-Satz steht woertlich in allen sechs Store-Texten und wird per Gate (SHARE_SENTENCE_DE/EN/FR) gesichert
- Parallelitaet in zwei Spuren: Einbettung als eigener Nebenlaeufer (PHP-Art-Filter, K6-gekoppelt) und N OCR-Slots mit KIND_BATCH-Companion, Drosselung, oom_score_adj-Kindern und selbsttaetiger Profil-Rueckstufung; Vorab-Pruefung ("Uebernehmen und pruefen") mit N-Slot-Probe und Verdikt in der ersten echten Settings-Flaeche
- Abnahme-Anfahrt: 18-Zellen-Matrix (ARM+x86, drei Profile) am gebauten Produkt, jedes Zaehltor exakt 5000, Kosten 34,64 von 59,43 USD, kompletter Abbau mit Sweep ueber 17 Regionen auf 0; OCR_SLOT_COST_BYTES per Owner-Wort auf 250 MiB, Vollindex-Term (6 KiB je Datei) in Phase 29 in die Laufzeit-Slotrechnung verdrahtet
- Die #18-Geschichte: 6.685 Fehlurteile einer Nutzer-Instanz gemeinsam mit dem Melder in fuenf Klassen zerlegt und alle fuenf in 1.4.0 geliefert (Sidecar-Skip ._/~$, TIFF-Shim inkl. In-Memory-SF0-Patch bis 32 MiB und Pillow-Upstream-Issue #10139, JPEG-draft-Decode mit Header-Vorabschaetzung, OLE/CFB-Sniff stdlib-only, Download-Groessenpruefung mit Retry); Fehlerklasse je Datei in /diagnose, occ und Admin-Karte; Altbestands-Nachpruefung in Baendern hinter dem Companion-Faehigkeitssignal (verdicts=2, skipped-Rueckfall nie auf corrupt)
- Upgrade-Strecke 1.3.2 auf 1.4.0 Ende zu Ende in CI bewiesen (Saat: AppleDouble-Sidecar + Grau+Extra-TIFF; alle zehn Zusicherungen, keine Neu-Einbettung, economy nach dem Upgrade, Recheck-Marke done); Migration verwirft backend_app_version
- Release-Disziplin: Audit 0 CRIT / 0 HIGH (F-29-01 DoS im SF0-Patch vor Release gefixt), Owner-Abnahme per gemeinsamer Playwright-Runde mit echten Testdateien, Tag-Laeufe 7/7 gruen, Signaturen doppelt verifiziert, Submission 2x HTTP 201, sechs oeffentliche Antworten am Release-Tag; secure-phase 28 = 71/71, secure-phase 29 = 65/65

**Vorbehalte:** Vier box-gebundene Feldbelege bewusst auf die naechste Anfahrt vertagt (D-29-11: Fall-1-Belege, fp32-Rueckkehr-Vollstaendigkeit, Fall-2-Feldlauf, 250-MiB-Feldlauf); F-29-03 (Dateicache mit falscher Groesse endet als repeatedly_stuck) als 1.4.1-Kandidat dokumentiert; Issues #15/#18/#19/#21/#22 bewusst offen, bis der Melder bestaetigt; Kostenzahl 34,09 vs 34,64 USD in zwei Doku-Stellen uneinheitlich (beide im Deckel).

---

## v1.3 Sprachausbau (Shipped: 2026-09-27)

**Delivered:** Findling 1.3.0 im Nextcloud App Store (beide Apps, Submission-Lauf 36304007154 mit 2x HTTP 201, Tag v1.3.0 auf 744d7e4): lexikalische Suche in Spanisch, Italienisch, Niederlaendisch und Portugiesisch mit Re-Analyse-Umbau statt Vollreindex, UI in fuenf neuen Katalogen (es/it/nl/pt_BR/pt_PT), niederlaendische Komposita-Zerlegung, alle offenen Boxzahlen aus v1.2 nachgemessen, Kaltstart-Fix (erste Suche antwortet lexikalisch statt leer).

**Phases completed:** 17 bis 23 (7 Phasen, 69 Plaene, 83 Tasks)

**Timeline:** 23.09. bis 27.09.2026 (5 Tage, 475 Commits, 585 Dateien, ~119.400 Zeilen hinzugefuegt)

**Key accomplishments:**

- Vier Analyseketten es/it/nl/pt messend abgenommen (ascii_fold-Position je Sprache gemessen entschieden, nicht uebernommen), tantivy auf 0.26.2 gepinnt, Sprach-Positivliste statt Rust-Panic; das Schema traegt immer sechs Koerperfelder, befuellt wird nur nach FINDLING_LANGUAGES, Werkseinstellung bleibt de,en
- Re-Analyse-Umbau (index/rebuild.py): Bestandsindex wandert ohne Download, OCR oder Neu-Einbettung ins neue Schema; wiederaufnahmefaehig nach Neustart, Platzpruefung vorab, der alte Index bedient Anfragen bis zum atomaren Tausch; Sprachmenge als sechster Versionsmerker, Bestandsinstallationen mit de,en upgraden ohne Umbau; CI beweist beide Richtungen (UPGRADE_FROM_TAG=v1.2.0, spanische Kette 0-0-1)
- Frageseite erst nach bewiesenem Umbauweg freigeschaltet: der Feldplan haengt an den gespeicherten Marken des geoeffneten Index statt an einer Konstante, Boosts der neuen Felder unterhalb body_en (Grenze 0,81 gemessen), Anti-Feature Spracherkennung als Quelltext-Waechter in der Suite
- UI in fuenf neuen Katalogen (es, it, nl, pt_PT, pt_BR) mit je 202 Schluesseln im Gleichstand; der Pluralschluessel-Fix macht die DE/FR-Plurale erstmals korrekt; niederlaendische Komposita via wdutch/OpenTaal-Wortliste mit eigener Digest-Marke (Umbau nur bei aktivem nl, gemeentebelastingen ueber belasting)
- Messanfahrt BL-F03: fuenf offene v1.2-Zahlen plus zwei neue v1.3-Zahlen (Indexgroesse bei sechs befuellten Feldern, Umbau-Wandzeit gegen 19 h 20 min Vollreindex) plus BL-F04-Basiszahlen aus EINER Anfahrt unter Kostendeckel (Plan 15,95 h / 2,83 USD), dismax auf Messbasis dokumentiert verworfen, Owner-Abnahme 26.09. mit Nachanfahrt 22-13
- Haertung und Release 1.3.0: Kaltstart-Fix (Kaltsuche 973 ms MIT Treffern statt 0, kein Vorwaermen), fastembed-Pin raus mit Absenz-Check im Abbild (HART-04), gone-Reparatur-Migration mit Upgrade-CI-Beweis, Grenzliste des Sprachausbaus in Store-Text und Doku (HART-05), Audit 0 CRIT / 0 HIGH, Submission 2x HTTP 201, secure-phase 23 SECURED 46/46

**Vorbehalte:** Ladefenster D-08 nur in CI gemessen, nicht auf Zielhardware (akzeptiert als AR-23-01); Store-Rendering der Texte nicht nachgesehen (Zwei-Tempi-Cache). Offene Artefakte beim Close: keine (die zwei Debug-Sessions upgrade5/upgrade6 am 27.09. mit deploy-harp-Beleg 36305643230 resolved).

---

## v1.2 Messbeleg und Ausbau (Shipped: 2026-09-21)

**Delivered:** Findling 1.2.0 im Nextcloud App Store (beide Apps, Submission-Lauf 35618848300 mit 2x HTTP 201): Filter und Sortierung auf der Ergebnisseite, Modell-Entladung im Leerlauf hinter einem ab Werk ausgeschalteten Schalter, 6 OCR-Sprachen, alle offenen Messbelege des Milestones aus der einen bezahlten Box-Anfahrt, Upgrade-Beweis 1.1.0 auf 1.2.0 live in CI.

**Phases completed:** 12 bis 16 (5 Phasen, 63 Plaene, 123 Tasks)

**Timeline:** 14.09. bis 21.09.2026 (8 Tage, 317 Commits, 308 Dateien, ~86.700 Zeilen hinzugefuegt)

**Key accomplishments:**

- stable35-Terminentscheid am Stichtag vollzogen: NC 35 final (v35.0.0 vom 15.09.), Beweislauf 35095805558 mit allen vier Matrixaesten gruen, der stable35-Ast von deploy-harp ist seither muss-gruen
- Filter (sechs Typgruppen plus Zeitraum) und Datums-Sortierung auf der Ergebnisseite: im Backend genau eine Occur.Must-Klausel an der geparsten Abfrage, in PHP ein readonly-Wertobjekt mit geschlossenen Wertelisten, die Rechtegrenze in Zahl, Reihenfolge und Ort unveraendert
- Modell-Entladung im Leerlauf: beide Speicherhalter werden zusammen freigegeben (Median 100,0 Prozent des Modellspeichers zurueck ans Betriebssystem, an der laufenden Instanz 376 MB nach 75 s), Schalter ab Werk aus, die erste Suche danach antwortet lexikalisch statt zu laden, sechster Diagnosezustand "unloaded" in drei Sprachen sichtbar
- Messphase mit einer bezahlten Box-Anfahrt: alle offenen Messbelege des Milestones erhoben (Ergebnis in docs/performance.md), das Runbook dabei zum ersten Mal vollzogen, Kostendeckel 46 Stunden / 5,40 USD eingehalten, Owner-Abnahme am 21.09.2026
- Haertung: drei Flake-Staemme geschlossen (u.a. enge 423-Wiederholung, cold-engine-Wettlauf), Geheimnis-Gate ueber docs/, A4 ueber den gruenen arm64-CI-Ast (10/10 Sprachfaelle ohne Fremdbestand), Upgrade-Beweis 1.1.0 auf 1.2.0 Ende zu Ende in CI, 6 OCR-Sprachen; Audit 0 CRIT / 0 HIGH / 2 MED (behoben) / 5 LOW (Verdikte)
- Store-Einreichung v1.2.0: Tag auf f827145 mit 7/7 gruenen Tag-Laeufen, Release zweifach signaturverifiziert, Submission 2x HTTP 201, beide Store-Seiten zeigen 1.2.0; Belegkette in docs/audits/2026-09-phase-16/README.md Abschnitt 9 (inkl. 401-Zwischenfall der doppelt gefeuerten Token-Rotation, L-16-05)

**Vorbehalte:** A1/A3 ohne Zielhardware-Nachmessung (benannt in der Phase-16-Verifikation). Offene Artefakte beim Close: keine (Audit sauber, drei alte Debug-Sessions am 21.09. formal geschlossen, Fixes waren laengst committet).

---

## v1.1 Qualitaet und Effizienz (Shipped: 2026-09-11)

**Delivered:** Findling 1.1.0 im Nextcloud App Store: 85 Prozent weniger Grundlast (691,8 auf 103,2 MB), deutsche Komposita-Zerlegung ueber eine lizenzgeklaerte Wortliste, eigene Ergebnisseite mit Paginierung, vollstaendiger franzoesischer Katalog, alles belegt durch eine Vergleichsmessung gegen die v1.0-Baseline auf derselben Zielhardware.

**Phases completed:** 7 bis 11 (5 Phasen, 37 Plaene, 75 Tasks)

**Key accomplishments:**

- Gemeinsame Embedding-Engine: Grundlast im Leerlauf von 691,8 auf 103,2 MB (minus 588,6 MB), Kaltstart im p95-Budget, Engine-Zustand in der Diagnose sichtbar
- Deutsche Komposita ohne Prefix-Behelf: split_compound mit wngerman-Wortliste (GPL-2+, 276.496 Eintraege), CI-Sprachfaelle die ohne Splitter rot werden, Wortlisten-Digest erzwingt Reindex
- Eigene Ergebnisseite: alle Treffer mit Paginierung, Rueckkehr ohne Listenverlust, dieselbe Berechtigungsgrenze wie die Unified Search (Paritaetstest deckt die Route mit ab)
- Vergleichsmessung auf der AWS-Box: 52.111 Dokumente ohne OOM, 19 Berichtsabschnitte Zeile fuer Zeile neben der v1.0-Baseline, inklusive der 13 Zahlen die nicht besser wurden (Laufzeit +40,9 Prozent benannt statt weggelassen)
- Store-Einreichung v1.1.0 mit Upgrade-Beweis 1.0.3 auf 1.1.0 Ende zu Ende in CI (dabei echten Produktfehler stumme-Suche-nach-Minor-Upgrade gefunden und per Migration gefixt), FR-Katalog 174 Schluessel vom Owner als Muttersprachler abgenommen
- Box abgebaut, Korpus als EBS-Snapshot snap-03f1d1d9ad9262704 gesichert (51,6 GiB, laufende Kosten von 9,39 auf ~2,9 USD/Monat)

**Stats:**

- 5 Phasen, 37 Plaene, 75 Tasks
- 4 Tage (08.09.2026 bis 11.09.2026)
- Git range: 1c737e6 -> 891bc6d (Tag v1.1.0), 265 Commits, 567 Dateien, +87.818/-1.774 Zeilen

**Known deferred items at close:** 3 Debug-Sessions (siehe STATE.md Deferred Items; alle drei gehoeren zu laengst gefixten CI-Befunden, nur der Session-Status blieb offen)

**What's next:** v1.2 (uebergeben: DI-10-02/DI-11-01 Sprachfall-Vorpruefung, DI-10-04 Volllauf-Analyse, DI-11-02/03/05/06, Untersuchung der vier regressiven Laststufen, Snapshot-Wiedervorlage, stable35-RE-CHECK 16.09.)

## v1.0 Volltext, OCR und semantische Suche (Shipped: 2026-09-07)

**Delivered:** Findling 1.0.0 im Nextcloud App Store: Zero-Config-Suche (Volltext + OCR + Semantik) als ExApp-Paar, Treffer in der Unified Search, komplett on-prem.

**Phases completed:** 1 bis 6 + 06.1 (103 Plaene, 102 Summaries; 05-19 ersetzt durch 06.1-15)

**Key accomplishments:**

- Praezedenzlose Kombination IProvider + exAppRequest-Proxy bewiesen und im Store (zwei signierte Apps)
- Tantivy-Index mit deutschem Stemming, SQLite-ACL-Vorfilter, finaler PHP-Recheck als Sicherheitsgrenze
- OCR strikt index-only, Semantik mit Distanzriegel + Einwortregel, 7 deutsche Sprachfaelle in CI
- Betriebsversprechen auf Zielhardware belegt: 51.961 Docs auf 4 GB/arm64, anon-Spitze 1.838 MB, 0 failed
- Launch-Haertung 06.1 (24 Plaene): Resilience-Ratsche, HaRP-Drift-Probe, drei Audits, Fremdinstallation

**Stats:**

- 7 Phasen, 103 Plaene
- 24 Tage von Projektstart (15.08.2026) bis Store (07.09.2026)
- Git range: fc4e7e5 -> 1c737e6 (Tags v1.0.0 bis v1.0.3)

**Known deferred items at close:** 2 Debug-Sessions (siehe STATE.md Deferred Items)

**What's next:** v1.1 Qualitaet + Effizienz (gemeinsame Embedding-Engine, Komposita-Wortliste, Ergebnisseite, Vergleichsmessung auf der AWS-Box)

---
