# Requirements: Findling (Nextcloud Zero-Config-Suche)

**Defined:** 2026-08-15
**Core Value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.

## v1 Requirements

v1 = ein Produkt, zwei Releases: **v1.0** (Volltext + OCR, Store-Einreichung vor Jahresende 2026) und **v1.1** (Semantik, 4-6 Wochen danach). SEM-Requirements sind v1.1, alles andere v1.0.

### Integration (PHP-Companion)

- [ ] **COMP-01**: Nutzer sieht Findling-Treffer in der Unified Search (Web-UI und OCS-Clients) über einen `IProvider` (NICHT `IExternalProvider`, der ist default-aus)
- [ ] **COMP-02**: ExApp holt Dateiinhalte über einen `#[ExAppRequired]`-Endpunkt der PHP-App (`getUserFolder($userId)->getFirstNodeById($fileId)` als Stream), Rechteprüfung inklusive
- [ ] **COMP-03**: PHP-App nimmt alle indexrelevanten Ereignisse auf (Datei create/update/delete/move/rename, Share- und Unshare-Ereignisse) und stellt sie in die Pull-Queue; ein einziger Ereignisweg, keine Doppel-Pfade
- [ ] **COMP-04**: Suchanfrage-Fluss: ExApp liefert Kandidaten-`fileid`s mit Scores, PHP macht den finalen Berechtigungs-Recheck pro Treffer, erst danach werden Snippets gerendert

### Indexer

- [ ] **IDX-01**: Erstindex crawlt pro Mount (User-Homes + Team Folders default AN, External Storage default AUS), jede Datei wird genau einmal verarbeitet, egal wie viele Nutzer sie sehen
- [ ] **IDX-02**: Indexer überlebt `docker kill` mitten im Lauf: Fortschritt liegt in der Datenbank, Neustart setzt fort statt neu zu beginnen (Abnahmetest genau so)
- [ ] **IDX-03**: Pull-Queue mit Zeilen-Locks: Worker pollen die PHP-Queue, verarbeiten, quittieren; Backpressure entsteht natürlich (Muster context_chat)
- [ ] **IDX-04**: Periodischer ETag-Abgleich gegen die Nextcloud-Dateiliste garantiert Index-Konsistenz auch bei komplett verlorenen Events (Abnahmetest: Events blockiert, ein Abgleichzyklus, Index korrekt)
- [ ] **IDX-05**: Löschungen und Unshares entfernen Inhalte und ACL-Einträge zeitnah aus dem Index
- [ ] **IDX-06**: Zero-Config-Defaults mit Leitplanken: Dokument-Allowlist (PDF, Office, OpenDocument, Text/Markdown), 50-MB-Extraktions-Cap, OCR-Seitenlimit pro Dokument, keine Videos/Archive; `failed`/`skipped` sind sichtbare Erstklasse-Zustände, nie stumm
- [ ] **IDX-07**: Nur-Lesen-Invariante: Nutzerdateien werden NIE verändert; OCR arbeitet auf Kopien im Scratch; CI-Prüfsummen-Gate belegt es
- [ ] **IDX-08**: `INDEX_WORKERS=1` als Architektur: OCR-Spitze (300-600 MB) und Embedding-Spitze (250-400 MB) laufen nie gleichzeitig; 4-GB-Box kippt nicht

### Suche

- [ ] **SRCH-01**: Volltextsuche mit deutschem Stemming, Stopwörtern und Komposita-Zerlegung (Tantivy 0.26) plus Englisch; Umlaut-Folding
- [ ] **SRCH-02**: Treffer-Snippets mit Hervorhebung, erzeugt erst NACH bestandener Rechteprüfung (Snippets sind Daten)
- [ ] **SRCH-03**: Suchoperatoren: Phrasen ("..."), +/- , Filter für Dateiname vs. Inhalt und Dateityp
- [ ] **SRCH-04**: Berechtigungs-Parität: automatisierter Paritätstest gegen die native Nextcloud-Suche über 6 Rechteszenarien (eigene Dateien, empfangener Share, entzogener Share, Team Folder, Gruppenwechsel, eingeschränkter Nutzer)

### OCR

- [ ] **OCR-01**: Gescannte PDFs und Bilder werden beim Indexieren automatisch per OCR erfasst (pypdfium2-Rendering + tesseract-Subprozess, Sprachen DE+EN), rein index-seitig
- [ ] **OCR-02**: Text-Layer-Erkennung: Dokumente mit vorhandenem Text werden extrahiert, nicht erneut OCR-t; Seiten-Timeouts und RAM-Deckel pro OCR-Job

### Semantik (v1.1)

- [ ] **SEM-01**: Lokale Embeddings (multilingual-e5-small, MIT, int8 selbst quantisiert, ins Image gebacken, `HF_HUB_OFFLINE=1`) mit Hybrid-Ranking (RRF) über Volltext- und Vektor-Treffer
- [ ] **SEM-02**: Vektor-Suche läuft durch dieselbe ACL-Kette (SQLite-Vorfilter + PHP-Recheck) wie die Volltextsuche
- [ ] **SEM-03**: Vektor-Schema erst nach Lasttest festgezurrt (sqlite-vec Alpha; Ausweichpfad Bit-Vektoren/usearch dokumentiert)

### Admin-Erlebnis

- [ ] **ADM-01**: Statusseite: Indexfortschritt, Deckungsgrad (indexierte vs. indexierbare Dateien), Fehlerliste
- [ ] **ADM-02**: Pro-Datei-Diagnose: Admin kann für jede Datei sehen, warum sie (nicht) auffindbar ist (zu groß, Typ nicht unterstützt, OCR fehlgeschlagen, wartet in Queue)
- [ ] **ADM-03**: Vorab-Schätzung vor dem Erstindex: X Dateien, davon Y OCR-nötig, geschätzte Dauer und Platz
- [ ] **ADM-04**: Ausschluss-Regeln und Toggles: Ordner-Ausschlüsse, Größen-Cap, Team Folders / External Storage an/aus

### Packaging & Store

- [ ] **PKG-01**: Multi-Arch-Image (amd64 + arm64), Debian-slim-Basis (keine musl-Wheels für tantivy/onnxruntime), Modell eingebacken
- [ ] **PKG-02**: Beide App-IDs (`findling` ExApp + Companion) vor dem ersten Bau-Commit eingefroren, beide CSRs sofort bei Baustart eingereicht
- [ ] **PKG-03**: Lauffähig auf einer 4-GB-ARM-Box (Lasttest belegt), Nextcloud 32-34 (max-version 35), HaRP-Deploy auf docker-compose UND AIO getestet
- [ ] **PKG-04**: Uninstall-Cleanup: Unregister entfernt Queue-Tabellen, Preferences und (nach Bestätigung) das Index-Volume
- [ ] **PKG-05**: v1.0-Store-Einreichung (Volltext + OCR) vor Jahresende 2026; signierte Releases, info.xml XSD-validiert

## v2 Requirements

Deferred. Nicht in v1 bauen.

- **V2-01**: Standalone-Modus ohne AppAPI (eigener Container + App-Passwort) für Managed Hosting ohne Deploy-Daemon
- **V2-02**: Weitere OCR-/Analyzer-Sprachen als nachladbare Pakete
- **V2-03**: Pro-Schiene (mögliche Kandidaten: Mandanten-Reports, SSO-Feinheiten, Priorisierungs-Policies), nur bei Traktion
- **V2-04**: Index-Verschlüsselung at rest als Opt-in
- **V2-05**: Optionales OCR-Textlayer-Zurückschreiben als Opt-in (strikt getrennt vom Indexpfad)

## Out of Scope

| Ausschluss | Grund |
|---|---|
| Elasticsearch/OpenSearch-Backends | genau die Setup-Qual, die das Produkt beseitigt |
| RAG/Chat-Antworten über Dokumente | Context-Chat/Assistant-Terrain; wir liefern Suche, keine Antworten |
| Externe Cloud-Embeddings/APIs | Privacy-Versprechen: alles lokal im Container |
| Indexierung fremder Quellen (Mail-Server, externe S3, Websites) | v1 ist Nextcloud-Files |
| Schreibende Eingriffe in Nutzerdateien (auch OCR-Layer) in v1 | Nur-Lesen-Invariante, Alt-App-Trauma (gelöschte PDFs) |
| `IExternalProvider` | in der Such-UI default-aus, killt Zero-Config |
| Eigenes Rechtemodell in Python | PHP-Recheck ist die einzige Sicherheitsgrenze; kein zweites, driftendes Modell |

## Traceability

Jedes v1-Requirement ist genau einer Phase zugeordnet. Abdeckung: 30 von 30, keine Waisen, keine Doppelungen.
Release-Schnitt: Phasen 1 bis 5 = v1.0 (Volltext + OCR), Phase 6 = v1.1 (Semantik).

| Requirement | Kurzbeschreibung | Phase | Release | Status |
|---|---|---|---|---|
| COMP-01 | Treffer in der Unified Search via IProvider | Phase 1 (Integrationsbeweis) | v1.0 | Pending |
| COMP-02 | Content-Gateway: ExApp holt Dateiinhalte per ExAppRequired-Endpunkt | Phase 1 (Integrationsbeweis) | v1.0 | Pending |
| COMP-03 | Alle indexrelevanten Ereignisse in die Pull-Queue, ein einziger Weg | Phase 3 (Aktualität und OCR) | v1.0 | Pending |
| COMP-04 | Suchfluss: Kandidaten aus der ExApp, finaler PHP-Recheck vor Snippets | Phase 2 (Indexkern und Volltextsuche) | v1.0 | Pending |
| IDX-01 | Erstindex crawlt pro Mount, jede Datei genau einmal | Phase 2 (Indexkern und Volltextsuche) | v1.0 | Pending |
| IDX-02 | Indexer überlebt docker kill, Fortschritt in der Datenbank | Phase 2 (Indexkern und Volltextsuche) | v1.0 | Pending |
| IDX-03 | Pull-Queue mit Zeilen-Locks und natürlicher Backpressure | Phase 2 (Indexkern und Volltextsuche) | v1.0 | Pending |
| IDX-04 | Periodischer ETag-Abgleich garantiert Konsistenz ohne Events | Phase 3 (Aktualität und OCR) | v1.0 | Pending |
| IDX-05 | Löschungen und Unshares räumen Inhalte und ACL-Einträge | Phase 3 (Aktualität und OCR) | v1.0 | Pending |
| IDX-06 | Zero-Config-Defaults mit Leitplanken, failed/skipped sichtbar | Phase 2 (Indexkern und Volltextsuche) | v1.0 | Pending |
| IDX-07 | Nur-Lesen-Invariante mit CI-Prüfsummen-Gate | Phase 1 (Integrationsbeweis) | v1.0 | Pending |
| IDX-08 | INDEX_WORKERS=1, OCR- und Embedding-Spitze nie gleichzeitig | Phase 2 (Indexkern und Volltextsuche) | v1.0 | Pending |
| SRCH-01 | Volltextsuche mit deutschem Stemming, Stoppwörtern, Umlaut-Folding | Phase 2 (Indexkern und Volltextsuche) | v1.0 | Pending |
| SRCH-02 | Snippets erst nach bestandener Rechteprüfung | Phase 2 (Indexkern und Volltextsuche) | v1.0 | Pending |
| SRCH-03 | Suchoperatoren: Phrase, +/-, Dateiname/Inhalt, Dateityp | Phase 2 (Indexkern und Volltextsuche) | v1.0 | Pending |
| SRCH-04 | Berechtigungs-Paritätstest über 6 Rechteszenarien | Phase 5 (Härtung und Store-Einreichung v1.0) | v1.0 | Pending |
| OCR-01 | OCR für gescannte PDFs und Bilder, automatisch, index-seitig | Phase 3 (Aktualität und OCR) | v1.0 | Pending |
| OCR-02 | Text-Layer-Erkennung, Seiten-Timeouts, RAM-Deckel pro Job | Phase 3 (Aktualität und OCR) | v1.0 | Pending |
| SEM-01 | Lokale Embeddings mit RRF-Hybrid-Ranking | Phase 6 (Semantische Suche, Release v1.1) | v1.1 | Pending |
| SEM-02 | Vektor-Suche durch dieselbe ACL-Kette | Phase 6 (Semantische Suche, Release v1.1) | v1.1 | Pending |
| SEM-03 | Vektor-Schema erst nach Lasttest festgezurrt | Phase 6 (Semantische Suche, Release v1.1) | v1.1 | Pending |
| ADM-01 | Statusseite: Fortschritt, Deckungsgrad, Fehlerliste | Phase 4 (Admin-Sichtbarkeit und Diagnose) | v1.0 | Pending |
| ADM-02 | Pro-Datei-Diagnose mit Grund | Phase 4 (Admin-Sichtbarkeit und Diagnose) | v1.0 | Pending |
| ADM-03 | Vorab-Schätzung vor dem Erstindex | Phase 4 (Admin-Sichtbarkeit und Diagnose) | v1.0 | Pending |
| ADM-04 | Ausschluss-Regeln und Toggles | Phase 4 (Admin-Sichtbarkeit und Diagnose) | v1.0 | Pending |
| PKG-01 | Multi-Arch-Image auf Debian-slim, Modell eingebacken | Phase 1 (Integrationsbeweis) | v1.0 | Pending |
| PKG-02 | Beide App-IDs eingefroren, beide CSRs eingereicht | Phase 1 (Integrationsbeweis) | v1.0 | Pending |
| PKG-03 | Lauffähig auf 4-GB-ARM, NC 32-34, HaRP auf compose und AIO | Phase 5 (Härtung und Store-Einreichung v1.0) | v1.0 | Pending |
| PKG-04 | Uninstall-Cleanup | Phase 5 (Härtung und Store-Einreichung v1.0) | v1.0 | Pending |
| PKG-05 | v1.0-Store-Einreichung vor Jahresende 2026 | Phase 5 (Härtung und Store-Einreichung v1.0) | v1.0 | Pending |

### Abdeckung pro Phase

| Phase | Requirements | Anzahl |
|---|---|---|
| 1 | COMP-01, COMP-02, IDX-07, PKG-01, PKG-02 | 5 |
| 2 | COMP-04, IDX-01, IDX-02, IDX-03, IDX-06, IDX-08, SRCH-01, SRCH-02, SRCH-03 | 9 |
| 3 | COMP-03, IDX-04, IDX-05, OCR-01, OCR-02 | 5 |
| 4 | ADM-01, ADM-02, ADM-03, ADM-04 | 4 |
| 5 | SRCH-04, PKG-03, PKG-04, PKG-05 | 4 |
| 6 | SEM-01, SEM-02, SEM-03 | 3 |
| **Summe** | | **30** |

---
*Last updated: 2026-08-15 after roadmap traceability mapping*
