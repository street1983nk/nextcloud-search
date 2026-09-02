# Phase 4: Admin-Sichtbarkeit und Diagnose - Context

**Gathered:** 2026-09-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 macht den Betriebszustand der Suche für den Admin sichtbar, bevor Nutzer etwas vermissen. Vier Lieferungen: (1) Statusseite mit Indexfortschritt, Deckungsgrad (indexierte vs. indexierbare Dateien) und Fehlerliste (ADM-01), (2) Pro-Datei-Diagnose: für jede Datei den Grund ihres Zustands nennen (ADM-02), (3) Vorab-Schätzung vor dem Erstindex: Anzahl Dateien, OCR-Anteil, erwartete Dauer und Platzbedarf (ADM-03), (4) Toggles: Ordner-Ausschlüsse, Größen-Cap, Team Folders und External Storage an/aus, der nächste Lauf hält sich daran (ADM-04). KEINE neuen Index-Fähigkeiten, KEIN Lasttest/Store-Härtung (Phase 5), KEINE Semantik (Phase 6). Die Zahlen-Basis existiert aus Phase 2/3 (Verdikt-System, /status-Route, FileStateService); Phase 4 baut die Sichtbarkeit darauf.

</domain>

<decisions>
## Implementation Decisions

### UI-Ort und Technik
- **D-01:** Die Admin-Seite lebt als eigene Sektion "Findling" in den Nextcloud-Verwaltungseinstellungen, registriert von der PHP-Companion-App (ISettings + Section). Der PHP-Controller proxied die Zahlen der ExApp (/status plus neue Diagnose-/Schätz-Routen). KEINE eigene ExApp-UI (kein ui.top_menu), kein zweites UI-Universum.
- **D-02:** Frontend ist Vanilla JS + PHP-Template + Nextcloud-CSS. KEIN npm/Build-Step im Companion-Repo (bleibt reines PHP). Umfang der Seite: Zahlen, Tabelle, Formulare; das trägt ohne Framework.

### Fehlerliste und Pro-Datei-Diagnose
- **D-03:** Der Privacy-Grundsatz aus status.py bleibt Vertragsbestandteil: der Container liefert nur fileids, Zustände, Gründe und Zahlen, NIE Dateinamen oder Pfade. Die PHP-Seite löst fileid zu Pfad zur Anzeigezeit auf (Besitzersicht); die Fehlerliste zeigt dem Admin lesbare Pfade.
- **D-04:** Die Diagnose-Eingabe (ADM-02) akzeptiert Pfad ODER fileid in einem Feld; zusätzlich verlinkt jeder Fehlerlisten-Eintrag direkt in die Diagnose. Grund-Taxonomie = bestehende Verdikt-Reasons beidseitig gespiegelt (FileStateService::REASONS), inklusive `indexed(truncated)` aus Phase-3-D-08; neuer Grund `excluded` für D-06.

### Vorab-Schätzung
- **D-05:** Kein Bestätigungs-Gate: der Erstindex startet weiter von selbst (Zero-Config-Kernversprechen). Die Schätzung entsteht als schneller Metadaten-Scan VOR der ersten Extraktion (Anzahl + Größe aus der NC-Dateiliste, OCR-Anteil per MIME-/Textlayer-Heuristik, Dauer aus den gemessenen Phase-3-Raten, Platzbedarf) und steht ab Minute 1 informativ auf der Statusseite, aktualisiert sich mit dem Fortschritt. Lesart des Roadmap-Kriteriums "vor dem Erstindex": D-05 gewinnt als spätere ausdrückliche Entscheidung; die Schätzung erscheint ab Minute 1 mit Beschriftung "vorläufig, Scan läuft" (der Verifier prüft gegen diese Formulierung, nicht gegen ein Blockier-Gate).

### Toggle-Mechanik
- **D-06:** Ordner-Ausschlüsse sind Pfad-Präfixe (Liste von Ordner-Pfaden, Präfix-Match). BEWUSST keine Glob-/Regex-Muster: erklärbar, kein Fehlbedienungsrisiko bei der Zero-Config-Zielgruppe. Ausgeschlossene Dateien erscheinen in der Diagnose mit Grund `excluded`, nicht stumm. Pfadraum (Owner-Bestätigung 02.09. nach Research): Präfixe gelten NUR in User-Homes, relativ zum files-Ordner (z.B. "Archiv", "Backups"), und wirken in allen Homes; Team Folders und External Storage steuern sich ausschließlich über ihren eigenen Ganz-oder-nichts-Schalter, dort keine Pfad-Präfixe.
- **D-07:** Ein neuer Ausschluss räumt Bestand AKTIV: der nächste Lauf/Reconcile entfernt Inhalte und ACL-Einträge unter dem Präfix aus dem Index. Der Index spiegelt die Regeln immer; keine Geisterinhalte. Mechanik konsistent mit der Unshare-/Lösch-Räumung aus Phase 3.
- **D-08:** Toggle-Satz genau nach ADM-04: Ordner-Ausschlüsse, Größen-Cap (heute FINDLING_MAX_FILE_BYTES), Team Folders an/aus (Default AN), External Storage an/aus (Default AUS). Gespeichert PHP-seitig (appconfig); der Container übernimmt die Werte beim nächsten Lauf ("der nächste Lauf hält sich daran"), kein Live-Neustartzwang.

### Claude's Discretion
- Transportweg der Settings von PHP zum Container (Mitgabe beim Queue-Poll vs. eigener Config-Endpunkt) und Cache-/Invalidierungsmechanik.
- Details der Schätz-Heuristik (OCR-Anteil, Raten) und die Aktualisierungs-Kadenz der Statusseite (Polling-Intervall der UI).
- Fehlerlisten-Pagination, Sortierung, Obergrenzen (MAX_LIST_LENGTH-Gotcha aus CR-01 beachten).
- Zuschnitt der neuen ExApp-Routen (Diagnose per fileid, estimate) und deren Response-Schemas; ADMIN-Access-Level in info.xml wie bei /status.
- Ob ein occ-Kommando als Zweitzugang zur Diagnose dazukommt (nice-to-have, kein Muss).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Projekt und Vorphasen
- `.planning/PROJECT.md` — Key Decisions: Pro-Datei-Diagnose + Vorab-Schätzung sind in v1.0 gesetzt, sie SIND das Anti-Silent-Failure-Versprechen; Zero-Config-Constraint
- `.planning/phases/03-aktualit-t-und-ocr/03-CONTEXT.md` — D-08 (`indexed(truncated)` muss in der Phase-4-Diagnose ausgewiesen werden), Verdikt-Hooks, Queue-/Reconcile-Entscheide
- `.planning/research/PITFALLS.md` — Deckungsgrad als Statusmaß, failed/skipped sichtbar; woran fulltextsearch starb

### Bestehender Code (Verträge, an die Phase 4 andockt)
- `backend/src/findling/api/status.py` — Modul-Docstring ist der Privacy-Vertrag der Statuszahlen (nur Zahlen, nie Namen); StatusResponse-Schema; ADMIN-Access-Level-Muster
- `php/lib/Service/FileStateService.php` — STATES/REASONS-Listen (beidseitig gespiegelt) und counts(); die Grund-Taxonomie der Diagnose
- `backend/src/findling/tools/index_status.py` — Zweitzugang zu denselben Zahlen ohne signierten Header (CI/Shell)

### Betriebsdokumentation
- `docs/dev-setup.md` — lokale Sichtprobe (Port 8090, testuser/kollegin, Korpus)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- GET /status (api/status.py): fertige Zahlenquelle (indexed/skipped/failed/aclRows/docs/Versionen) über die Read-only-DB-Verbindung — die Statusseite konsumiert das, keine zweite Zähllogik
- FileStateService (php): Tabelle findling_file_state mit STATES/REASONS und counts() — PHP-seitige Hälfte der Diagnose existiert
- tools/index_status.py: gleiche Zahlen als CLI-JSON — Muster für Abnahmen/CI der neuen Routen
- QueueController/ReconcileController (php): Muster für neue ExApp-gesicherte Endpunkte (#[ExAppRequired]), Migration-Muster Version001000Date*
- config.py: FINDLING_MAX_FILE_BYTES (Größen-Cap existiert als Env), FINDLING_RECONCILE_* (Räum-Andockpunkt für D-07)
- worker/reconcile.py + store/repo.py (replace_acl, Tombstones): die Räum-Mechanik, die D-07 wiederverwendet

### Established Patterns
- Verdikte statt Exceptions, Reason-Liste beidseitig identisch — neue Reasons (excluded) MÜSSEN in beiden Listen landen
- Fortschritt/Zustand in der DB, nie im Prozessspeicher — Schätzung und Deckungsgrad rechnen aus DB-Zahlen
- Fail-closed-Gates: Gate A (Nur-Lesen) und Gate B (Prüfsummen) bleiben grün; die Admin-Seite ist reine Lese-Sicht plus Config-Schreiben, kein neuer Pfad auf Nutzerdateien
- ADMIN-Access-Level in appinfo/info.xml für Admin-Routen (Muster /status)

### Integration Points
- php/lib/AppInfo/Application.php: Registrierung von Settings-Section + ISettings (neu)
- Neuer PHP-SettingsController: proxied ExApp-Routen, löst fileids zu Pfaden auf, schreibt appconfig
- ExApp: neue Routen für Pro-Datei-Diagnose (fileid) und Schätzung; Poller/Reconcile lesen die Toggle-Werte
- Crawl (StorageCrawlJob) und Queue-Judge: Ausschluss-Präfixe und Caps müssen an der Quelle greifen (nicht erst nach Download)

</code_context>

<specifics>
## Specific Ideas

- Erfolgskriterien wörtlich aus der Roadmap: (1) Statusseite ohne Log-Lektüre, (2) beliebige Datei angeben und den Grund genannt bekommen, (3) Schätzung VOR dem Erstindex sichtbar, (4) Umschalten wirkt im nächsten Lauf
- ROADMAP §Research-Flags: "Statusseiten-Muster (Phase 4)" ist als etabliert markiert — Research kann laut Roadmap entfallen, `/gsd:plan-phase 4 --skip-research` ist eine legitime Option
- Deckungsgrad ist DIE Kopfzahl der Seite (Pitfalls-Lehre): indexierte gegen indexierbare Dateien, nicht rohe Counts

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (Betriebsthema außerhalb der Phase, am 02.09. direkt erledigt: Dependabot-PRs #4/#5 gemergt, GitHub-Ruleset protect-main aktiv.)

</deferred>

---

*Phase: 04-admin-sichtbarkeit-und-diagnose*
*Context gathered: 2026-09-02 via discuss-phase (verkürzter Modus wie Phase 3: nur Fragen mit Nutzer-Mehrwert, Rest dokumentierte Defaults)*
