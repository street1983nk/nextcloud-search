# Phase 3: Aktualität und OCR - Context

**Gathered:** 2026-09-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 hält den Index aktuell und macht gescannte Dokumente durchsuchbar. Drei Lieferungen: (1) EIN Ereignisweg über die PHP-App in die bestehende Pull-Queue für create/update/delete/move/rename plus Share/Unshare (COMP-03), (2) periodischer ETag-Abgleich als Konsistenzgarantie auch bei komplett verlorenen Events (IDX-04) samt Lösch-/Unshare-Räumung (IDX-05), (3) OCR für gescannte PDFs und Bilder, rein index-seitig, mit Text-Layer-Erkennung und harten Deckeln (OCR-01/02). KEINE Admin-UI (Phase 4), KEINE Embeddings (Phase 6), KEIN Lasttest (Phase 5). Originaldateien werden NIE angefasst; Abnahmetest der Roadmap: nach einem OCR-Lauf über defekte/ungewöhnliche PDFs sind alle Originale bitweise unverändert.

</domain>

<decisions>
## Implementation Decisions

### Aktualitäts-Kadenz
- **D-01:** Ziel-Latenz für neue/geänderte/umbenannte Dateien: unter 1 Minute. Weg: PHP-Event-Listener -> enqueue in die bestehende Queue -> Poller mit bestehender Kadenz (Cooldown 15-120 s). KEIN neuer Push-/Weckkanal.
- **D-02:** ETag-Abgleich läuft nächtlich einmal voll (außerhalb der Nutzungszeit), Events tragen die Aktualität tagsüber. Abnahmetest wörtlich aus der Roadmap: Events blockiert, EIN Abgleichzyklus, Index korrekt.
- **D-03:** Der Abgleich setzt aus, solange Erstindex/OCR-Rückstau läuft (Queue über Schwelle), und startet erst bei ruhiger Queue. Schwellwert ist Claude-Diskretion.
- **D-04:** Rechteänderungen (Unshare, Delete) haben Vorrang vor Inhaltsänderungen in der Queue: ACL-Updates sind billig (kein Download, keine Extraktion) und ihre Sicherheitswirkung soll sichtbar schnell sein, auch bei langem OCR-Rückstau. (Der PHP-Recheck schützt ohnehin sofort; es geht um Kandidaten/Snippets im Container.)

### OCR-Umfang und Reihenfolge
- **D-05:** OCR erfasst PDFs ohne Textlayer PLUS gängige Bildformate: JPG, PNG, TIFF, WebP. Kein HEIC/BMP/GIF (Decoder-Angriffsfläche im Sandbox-Kind, wenig Nutzen). Plausibilitäts-Deckel, damit nicht jedes Urlaubsfoto durch tesseract läuft (z.B. Mindestauflösung/Seitenverhältnis-Heuristik; Details Claude-Diskretion).
- **D-06:** Text-Layer-Erkennung (OCR-02): Dokumente mit vorhandenem Textlayer werden extrahiert, NIE erneut OCR-t. Das bestehende Verdikt `skipped(no_text_layer)` aus Phase 2 ist der vorbereitete Übergabepunkt.
- **D-07:** Erstindex in zwei Spuren: alle Textdokumente zuerst (Suche nach Stunden nutzbar), OCR-Jobs als zweite, nachlaufende Spur. Ein PDF ohne Textlayer wird automatisch zum OCR-Job statt endgültig skipped.

### OCR-Deckel und Verdikte
- **D-08:** Limit gerissen (Seiten, Zeit, RAM) -> TEILINDEXIEREN als `indexed(truncated)` statt überspringen: die ersten N Seiten werden auffindbar, die Phase-4-Diagnose weist den Zustand aus. Muster existiert (RTF/Text-Cap aus Phase 2).
- **D-09 (Owner-Auftrag DACH-OCR, gesetzt):** Tesseract-Sprachen deu+eng; Schweizer Schreibweise (ss statt ß) und österreichische Varianten müssen im Zusammenspiel mit der deutschen Analyzer-Kette auffindbar sein; deu_frak (Fraktur) als OPTION, default AUS; DACH-Testkorpus (deutsche, teils gescannte Ratsvorlagen-PDFs) als Abnahmegrundlage.

### Lösch-Verhalten
- **D-10:** Papierkorb = sofort raus aus den Treffern. Löschen entfernt die Datei zeitnah (gleiche Latenzklasse wie D-01) aus Kandidaten und ACL; Wiederherstellen macht sie wieder auffindbar (ACL-/State-Update, Reindex nur wenn nötig). Entspricht der nativen Files-Suche.

### Claude's Discretion
- Listener-Mechanik (IEventListener-Auswahl, Event-Liste, Debouncing bei Massenoperationen wie Ordner-Move), solange EIN Ereignisweg über die Queue gilt.
- ETag-Abgleich-Algorithmus (Mount-Rotation, Cursor-Wiederverwendung aus StorageCrawlJob), Queue-Ruhe-Schwelle für D-03.
- Konkrete OCR-Deckel-Zahlen (Seitenlimit, Zeit pro Seite, RAM), abgestimmt auf die Sandbox-Grenzen aus Phase 2 (RLIMIT_AS 512 MB, Timeout 120 s); LOCK_TIMEOUT der Queue ggf. je Job-Art anheben (OCR-Jobs dauern länger als 900 s?).
- Prioritäts-Mechanik in der Queue (Spalte vs. getrennte Bänder) für D-04/D-07.
- Bild-Plausibilitäts-Heuristik für D-05.
- OCR-Ausführung im bestehenden Sandbox-Kind (setsid/killpg und Gruppen-Kill sind aus dem Phase-2-Audit bereits vorbereitet; tesseract als Subprozess des Kindes).

### Aus den Phase-2-Audits in diese Phase verschoben
- Bug/Perf-Mediums M1/M2/M5/M8/M9 (poller to_thread beim Öffnen, verdicts-Text freigeben, usersFor-Cap, getUserFolder-Cache, MAX_LIST_LENGTH) und Lows nach Gelegenheit.
- Sec-L4 (CI-Gate für die ExApp-Vertrauensgrenze der Queue-Routen), L5 (isReadable-Check im Provider), L6 (getMessage im Log), L2 (script/style im XHTML-Zweig).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Projekt und Vorphasen
- `.planning/PROJECT.md` — Key Decisions (OCR strikt index-only, Sprachen DE+EN, INDEX_WORKERS=1), Kill-Kriterium, Constraints
- `.planning/phases/02-indexkern-und-volltextsuche/02-CONTEXT.md` — gelockte Engine-/Queue-/Extraktions-Entscheide, an die Phase 3 andockt
- `.planning/research/PITFALLS.md` — Events nur Beschleuniger + ETag-Abgleich als Garantie; woran fulltextsearch starb
- `.planning/research/STACK.md` — pypdfium2-Rendering + tesseract-Subprozess (KEIN OCRmyPDF im Indexpfad)

### Audits (Betriebsgrenzen, an denen OCR andocken muss)
- `.planning/phases/02-indexkern-und-volltextsuche/02-AUDIT-SECURITY.md` — Sandbox-Härtung (Secrets-Shedding, killpg), Bomben-/Byte-Deckel-Muster
- `.planning/phases/02-indexkern-und-volltextsuche/02-AUDIT-PERF.md` — verschobene Mediums (M1/M2/M5/M8/M9), Sandbox-/Queue-Messwerte
- `.planning/phases/02-indexkern-und-volltextsuche/02-AUDIT-BUGS.md` — dirty-Semantik der Queue, Generation-Mechanik (Bug-H4/H5-Fixes)

### Betriebsdokumentation
- `docs/dev-setup.md` — lokale Sichtprobe (Port 8090, testuser/kollegin, Korpus)
- `docs/german-analyzer.md` — dokumentierte Grenzen der deutschen Kette (relevant für CH-ss/AT-Varianten in D-09)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Pull-Queue (php/lib/Db/QueueMapper.php): idempotentes enqueue mit dirty-Semantik, Batch-Claim mit Token, is_update-Flag — Events docken hier an, kein zweiter Weg
- StorageCrawlJob (php/lib/BackgroundJobs/): Mount-Crawl mit fileid-Cursor und Transaktionsbändern — Basis/Vorbild für den ETag-Abgleich
- Sandbox-Kind (backend/src/findling/extract/sandbox.py): RLIMIT_AS, Timeout, Recycling, setsid/killpg, Secrets-Shedding — tesseract läuft als Subprozess GENAU hier drin
- Verdikt-System (extract/errors.py): `skipped(no_text_layer)` existiert als Phase-3-Hook; `indexed(truncated)` als Muster für D-08
- Store (store/repo.py): replace_acl (Unshare-Pfad), index_version-Generation, is_unchanged-Schnellpfad
- Writer (index/writer.py): Upsert löscht per delete_documents_by_term — Löschpfad (D-10) nutzt denselben Mechanismus; ACHTUNG dokumentierter I64/U64-Gotcha

### Established Patterns
- Ein Worker, eine Extraktion (IDX-08): OCR reiht sich in dieselbe Ein-Worker-Disziplin ein, keine Parallel-Spitzen auf 4-GB-Boxen
- Fortschritt in der DB, nie im Prozessspeicher (docker-kill-Abnahmetest, Resilience-CI-Gate existiert)
- Fail-closed-Gates: Gate A (Nur-Lesen) und Gate B (Korpus-Prüfsummen) MÜSSEN grün bleiben — OCR darf keinerlei Schreibpfad auf Nutzerdateien einführen
- Verdikte statt Exceptions über die Prozessgrenze; Reason-Liste beidseitig identisch (PHP FileStateService::REASONS muss neue Reasons spiegeln)

### Integration Points
- PHP-Listener -> QueueService::enqueue (existiert); neue Event-Typen brauchen ggf. Queue-Spalten (Migration im Muster Version001000Date20260901000000)
- Poller `_handle` -> judge/dispatch -> Sandbox: OCR-Route als neuer dispatch-Zweig hinter der Text-Layer-Erkennung
- tesseract + Sprachpakete (deu, eng, optional deu_frak) müssen ins Multi-arch-Image (Dockerfile + CI-Image-Workflow)

</code_context>

<specifics>
## Specific Ideas

- DACH-Testkorpus: echte deutsche Ratsvorlagen-PDFs (lang, teils gescannt) plus gezielte Fälle für CH-Schreibweise (Strasse/Straße) und AT-Varianten (Jänner) — Abnahme über auffindbare Suchbegriffe, nicht über OCR-Rohtext
- Abnahmetest IDX-04 wörtlich: Events blockiert, ein Abgleichzyklus, Index korrekt
- Abnahmetest OCR: Korpus mit defekten/ungewöhnlichen PDFs, danach alle Originale bitweise unverändert (Gate B), kein Job über Seiten-/Zeit-/RAM-Deckel

</specifics>

<deferred>
## Deferred Ideas

- Statusseite/Diagnose-UI inkl. OCR-Fortschritt und Vorab-Schätzung: Phase 4 (die Verdikt-Daten entstehen JETZT)
- Embeddings/Hybrid-Ranking: Phase 6
- Lasttest 100k+ und ARM-RSS-Kurve: Phase 5
- Mail-Anhänge/externe Quellen: nach v1

</deferred>

---

*Phase: 03-aktualit-t-und-ocr*
*Context gathered: 2026-09-01 via discuss-phase (verkürzter Modus auf Owner-Wunsch: nur Fragen mit Nutzer-Mehrwert, Rest dokumentierte Defaults)*
