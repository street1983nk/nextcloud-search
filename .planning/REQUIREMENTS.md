# Requirements: Milestone v1.6 Store-Sichtbarkeit und Betriebs-Feinschliff

**Defined:** 2026-10-28 (Owner-Ansagen 22.-28.10.2026; Owner-Linie "mache dich an die arbeit mit 1.5 danach 1.6")
**Core Value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Milestone-Ziel:** Findling uebersteht den HaRP-Zertifikatswechsel ohne Admin-Eingriff, ist im Store besser auffindbar und raeumt die aus v1.5 vertagten Feinschliff-Punkte ab.
**Grundlage:** Issue #33 (FlattusBlastus), 36-REVIEW.md (L-36-05/06, IN-01..06), 35-DEDUP-NOTIZ.md (Weg B, D1-D4), Store-Strategie 24.10., Umlaut-Audit 28.10.; keine Domain-Recherche (kein neues Feature-Terrain).

## v1.6 Requirements

### Zertifikatsrotation (ZERT, Issue #33, Zeittreiber)

- [ ] **ZERT-01**: Backend uebersteht die HaRP-Zertifikatsrotation (Neuausstellung der CA "harp.nc", z. B. nach HaRP-Neustart) ohne Unregister/Register: bei einem x509-Fehler des frpc-Tunnels liest der Container /certs/frp neu ein und startet frpc neu; die Verbindung kommt selbsttaetig wieder
- [ ] **ZERT-02**: Die Selbstheilung ist belegt (Test oder CI-Probe mit rotiertem Zertifikat) und begrenzt (kein Neustart-Sturm: Backoff oder Versuchsdeckel); der Weg ist in der Doku beschrieben und dem Melder im Issue #33 geantwortet

### Ausschluss-Anzeige (ANZE, aus 36-REVIEW L-36-05/06)

- [ ] **ANZE-01**: Admin versteht die Karte "Bewusst ausgelassen: 0": neben der Zahl steht ein Erklaersatz, was "bewusst ausgelassen" umfasst (alle 16 Kataloge im Gleichstand)
- [ ] **ANZE-02**: Nach einer Ausschlussmuster-Aenderung zeigt der Zaehler keinen irrefuehrenden Zwischenstand: die Verzoegerung bis zum naechsten Kehr-/Abgleichslauf ist am Zaehler erkennbar (Hinweis oder Stand-Zeitpunkt)

### Dedup (DEDUP, Issue #25, Designnotiz Weg B)

- [ ] **DEDUP-01**: Owner-Tor: die vier Fragen D1-D4 der 35-DEDUP-NOTIZ.md sind entschieden (Weg-Wahl, Weg-A-Opt-in, Weg-C-Vorziehen, Messung A6/A7); die Entscheide stehen im Phasen-Kontext
- [ ] **DEDUP-02**: Der entschiedene Umfang ist umgesetzt: mindestens Weg C (billige Ergaenzung laut Notiz); Weg B nur, wenn D1 = (a) und der Bau in den Release-Zeitrahmen passt, sonst dokumentiert vertagt

### Doku-Hygiene (DOCS, Umlaut-Audit 28.10.)

- [ ] **DOCS-01**: docs/dev-setup.md, docs/embeddings.md und docs/install-check.md tragen echte Umlaute und ß in deutscher Prosa (kein ss-statt-ß, kein fuer/ueber); Testkorpus-Begriffe (z. B. "Bahnhofstrasse", Gesetzes-Langwoerter) bleiben unveraendert
- [ ] **DOCS-02**: Review-Infos IN-01 bis IN-06 aus 36-REVIEW.md sind gesichtet und je als "fix in v1.6" oder "accept mit Begruendung" entschieden; Fixes sind umgesetzt

### Store-Sichtbarkeit (STORE, Strategie 24.10.)

- [ ] **STORE-01**: Die App heisst im Store sichtbar "Findling Search" (Anzeigename in info.xml beider Apps, GO vom 22.10.); App-IDs bleiben unveraendert
- [ ] **STORE-02**: Beide info.xml tragen den discussion-Link auf den Forum-Thread 249775; die Store-Texte tragen den Cross-Promo-Satz zum Nextcloud MCP Connector (Kurztext-Regel, Owner-Abnahme des Wortlauts vor Release)

### Release (REL)

- [ ] **REL-06**: Findling 1.6.0 ist nach Owner-Abnahme im Store eingereicht (beide Apps, 2x HTTP 201 mit Beleg); UPGRADE_FROM_TAG steht auf v1.5.0, die Upgrade-Strecke 1.5.x -> 1.6.0 ist in CI gruen; Audit-Gate der Abschlussphase bestanden

## Future Requirements (nicht v1.6)

- granite-Modellwechsel (nur mit Bedingung, Verdikt 35-11)
- Kleiner Reranker, CLIP-Bildsuche (SigLIP2), whisper.cpp-Transkription als Opt-in
- Franzoesisches Koerperfeld; Sortierung nach Name/Groesse (Schema-Sprung); Mimetype-Gruppen aus files.mime
- Pro-Schiene (Index-Verschluesselung, External Storage; ISV-Entscheid 03.11.)

## Out of Scope

- Weg A der Dedup-Notiz als Standard (Rechte-Risiko; hoechstens Admin-Opt-in je Mount-Config, Entscheid D2 am Owner-Tor)
- Neue Dateiformate oder Sprachen (v1.5 hat geliefert; naechster Ausbau erst mit neuem Bedarf)
- Elasticsearch/OpenSearch, RAG/Chat, externe Cloud-Embeddings, fremde Quellen (unveraendert, siehe PROJECT.md)

## Traceability

Gefuellt vom Roadmap-Schritt am 2026-10-28. Abdeckung: 11/11 v1.6-Anforderungen je genau einer Phase zugeordnet.

| REQ-ID | Phase | Status |
|--------|-------|--------|
| ZERT-01 | Phase 38 | Pending |
| ZERT-02 | Phase 38 | Pending |
| ANZE-01 | Phase 39 | Pending |
| ANZE-02 | Phase 39 | Pending |
| DEDUP-01 | Phase 37 | Pending |
| DEDUP-02 | Phase 39 | Pending |
| DOCS-01 | Phase 39 | Pending |
| DOCS-02 | Phase 39 | Pending |
| STORE-01 | Phase 37 | Pending |
| STORE-02 | Phase 37 | Pending |
| REL-06 | Phase 40 | Pending |
