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

Wird von der Roadmap gefüllt.

---
*Last updated: 2026-08-15 after initial definition*
