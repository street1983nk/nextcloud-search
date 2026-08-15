# Phase 2: Indexkern und Volltextsuche - Context

**Gathered:** 2026-08-15
**Status:** Ready for planning
**Source:** Grilling-Interview 15.08. (PROJECT.md Key Decisions) + Projekt-Research + Phase-1-Learnings

<domain>
## Phase Boundary

Phase 2 macht aus dem Walking Skeleton ein benutzbares Produkt: echte Inhalte aus Nutzerdateien werden extrahiert, in Tantivy indexiert und mit deutscher Sprachqualität durchsuchbar, rechtegeprüft und abbruchfest. KEINE Events/Reconcile (Phase 3), KEIN OCR (Phase 3), KEINE Embeddings (Phase 6), KEINE Admin-UI (Phase 4). Der Kanarien-Treffer aus Phase 1 wird durch echte Treffer ersetzt oder ergänzt (Entscheid beim Planen: Kanarie darf als verstecktes Diagnose-Feature bleiben, solange sie normale Suchen nicht verschmutzt).

</domain>

<decisions>
## Implementation Decisions (locked, aus Grilling + Research)

### Engine und Sprache
- Volltext-Engine: Tantivy 0.26 embedded, mmap; Writer-Heap 50 MB, num_threads=1 (4-GB-Budget)
- Deutsch: Snowball-Stemmer "german" + deutsche Stopwörter + ascii_fold (Umlaut-Folding) + split_compound (Komposita; Wortliste beschaffen ist Teil der Phase, Lizenz prüfen); Englisch als zweites Feld/Pipeline
- Snippets: Klartext + Zeichenoffsets (Subline rendert kein HTML, Phase-1-Befund); Hervorhebung macht die PHP-Seite bzw. der Client mit den Offsets; Snippet-Erzeugung erst NACH bestandener Rechteprüfung (SRCH-02)
- Suchoperatoren: Phrasen, +/-, Filter Dateiname vs. Inhalt, Dateityp (SRCH-03)

### Berechtigungskette (Sicherheitsgrenze unverändert)
- SQLite-ACL-Tabelle (access_list: uid, fileid) als VORFILTER auf Kandidatenlisten (Überfetch + iteratives Nachfassen), finaler Recheck bleibt in PHP via getUserFolder()->getFirstNodeById() (COMP-04); NIE ein eigenes Rechtemodell in Python
- ACL gehört ins ERSTE Schema (nie nachrüsten); Schema führt eine Indexversion (Tantivy-Upgrades können Reindex erzwingen)

### Indexer-Betriebsmodell (die Anti-fulltextsearch-Invarianten)
- Pull-Queue: PHP führt die Queue (Tabelle), Worker der ExApp pollen, verarbeiten, quittieren; Zeilen-Locks; Backpressure natürlich (Muster context_chat, Quellcode-verifiziert)
- Crawl pro Mount, Cursor = fileid-Integer im Job-Zustand; jede Datei genau EINMAL egal wie viele Nutzer sie sehen (IDX-01); User-Homes + Team Folders default AN, External Storage default AUS
- Fortschritt in der DB, nie im Prozessspeicher: docker kill mitten im Lauf, Neustart, Fortsetzung an der Zustandsmarke = Abnahmetest (IDX-02)
- INDEX_WORKERS=1 als Architektur (IDX-08); OCR-/Embedding-Spuren kommen später in dieselbe Ein-Worker-Disziplin
- failed/skipped sind sichtbare Erstklasse-Zustände mit Grund (zu groß, Typ, Fehler); nie stumm (IDX-06); diese Zustände sind die Datenbasis für die Phase-4-Diagnose
- Zero-Config-Leitplanken: Dokument-Allowlist (PDF, Office, OpenDocument, Text/Markdown, RTF, HTML), 50-MB-Extraktions-Cap, openpyxl read_only + Zellcap 200k, keine Videos/Archive

### Extraktion (Stack-Research, gepinnt)
- pypdfium2 (PDF-Text), pypdf (Metadaten/Verschlüsselungs-Erkennung VOR pypdfium2), python-docx, python-pptx, openpyxl read_only, ODF via zipfile+lxml (KEIN odfpy), lxml.html, striprtf, charset-normalizer; passwortgeschützte PDFs -> skipped mit Grund
- Inhalte fließen ausschließlich über das Content-Gateway aus Phase 1 (fetch_file_stream, download2stream); Gate A (Nur-Lesen) und Gate B (Korpus-Prüfsummen) bleiben aktiv und dürfen nie verletzt werden

### Qualität und Umgebung
- Alle 5 Python-Gates vor jedem Commit lokal grün; CI-Erweiterungen folgen dem Phase-1-Muster (walking-skeleton + readonly-gate bleiben grün, neue Jobs für Index/Suche-E2E)
- Referenzkorpus testdata/corpus/ erweitern statt ersetzen (byteidentisch generiert, -text in .gitattributes beachten)
- KEIN lokales PHP; PHP-Verifikation via CI; lokale E2E-Proben über scripts/dev/ (FINDLING_PORT beachten, 8080 ist von der parallelen MCP-Session belegt, 8090 nehmen)

### Claude's Discretion
- Tantivy-Schema-Detail (Felder, DE/EN-Doppelfeld vs. Sprach-Erkennung), Chunking fürs Snippet-Fenster
- Queue-Schema und Quittungs-Protokoll im Detail; Wahl SQLite-Datei-Layout im Container-Volume
- Wie der Erstindex angestoßen wird (occ-Kommando der PHP-App vs. Auto-Start nach Registrierung; Zero-Config spricht für Auto-Start mit Vorab-Schätzungs-Hook für Phase 4)
- Umgang mit dem Kanarien-Treffer aus Phase 1

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/PROJECT.md` , Key Decisions, Kill-Kriterium, Constraints
- `.planning/research/SUMMARY.md`, `STACK.md`, `ARCHITECTURE.md`, `PITFALLS.md` , Projekt-Research (Engine-Entscheid, Pull-Queue, ACL-Abwägung, fulltextsearch-Sterbearten)
- `.planning/phases/01-integrationsbeweis/01-RESEARCH.md` , Integrationsprotokoll, Klartext-Snippet-Befund, exAppRequest-Fälle
- `.planning/phases/01-integrationsbeweis/*-SUMMARY.md` , was existiert (Provider, Gateway, Queue-freies Skeleton, CI-Jobs, Korpus, Gates A+B)
- `docs/store-identity.md`, `CLAUDE.md` , Identität und Projektregeln

</canonical_refs>

<specifics>
## Specific Ideas

- Deutsche Sprachqualität ist DAS Produktversprechen: Testfälle mit echten Komposita (z.B. "Grundstücksverkehrsgenehmigung" findbar über "Genehmigung"), Umlaut-Varianten (Muller/Müller/Mueller), Stemming (suchte/suchen)
- Testkorpus für Realismus: eigene Dokumente + Ratsvorlagen-PDFs (deutsch, lang, teils gescannt; OCR-Teile erst Phase 3)
- Abnahmetest wörtlich aus der Roadmap: docker kill mitten im Erstindex, Neustart, Fortsetzung ohne Fortschrittsverlust

</specifics>

<deferred>
## Deferred Ideas

- Events + ETag-Reconcile + Löschpfad: Phase 3 (aber: Schema soll Deletions-Verarbeitung nicht verbauen)
- OCR: Phase 3; Embeddings/RRF: Phase 6 (Schema embedding-ready, kein Umbau)
- Statusseite/Diagnose-UI: Phase 4 (aber failed/skipped-Daten entstehen JETZT)
- Lasttest 100k+: Phase 5

</deferred>

---

*Phase: 02-indexkern-und-volltextsuche*
*Context gathered: 2026-08-15 via Grilling + Projekt-Research + Phase-1-Learnings*
