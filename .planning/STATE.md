---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: "**Goal**: Die Betriebsversprechen sind auf echter Zielhardware belegt statt behauptet, und v1.0"
status: executing
stopped_at: Phase 6 context gathered
last_updated: "2026-09-05T03:24:23.547Z"
last_activity: 2026-09-05
progress:
  total_phases: 2
  completed_phases: 0
  total_plans: 33
  completed_plans: 20
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-15)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 6 — Semantische Suche

## Current Position

Phase: 6 (Semantische Suche) — EXECUTING
Plan: 2 of 12
Status: Ready to execute
Last activity: 2026-09-05

Progress: [██████░░░░] 61%

## Performance Metrics

**Velocity:**

- Total plans completed: 46
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 8 | - | - |
| 02 | 14 | - | - |
| 03 | 14 | - | - |
| 04 | 10 | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 04 P01 | 12 min | 2 tasks | 3 files |
| Phase 04 P02 | 10 min | 2 tasks | 7 files |
| Phase 04 P03 | 47 min | 3 tasks | 15 files |
| Phase 04 P04 | 25 min | 3 tasks | 9 files |
| Phase 04 P05 | 21 min | 3 tasks | 12 files |
| Phase 04 P06 | 22 min | 3 tasks | 9 files |
| Phase 04 P07 | 25 min | 3 tasks | 16 files |
| Phase 04 P08 | 33 min | 3 tasks | 16 files |
| Phase 04 P09 | 22 min | 3 tasks | 14 files |
| Phase 04 P10 | 19 min plus Sichtprobe | 3 tasks | 11 files |
| Phase 06 P01 | 35min | 3 tasks | 14 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: EIN Store-Erstrelease 1.0.0 mit Volltext, OCR und Semantik. Phasen 1 bis 5 stellen den einreichungsbereiten Zustand her (D-09), Phase 6 ergänzt die Semantik, die Abgabe ist Abschluss von Phase 6 (D-08), hart vor Jahresende 2026 (D-10). Die frühere Staffelung v1.0 jetzt und v1.1 vier bis sechs Wochen später ist überholt und nur noch Fallback
- Roadmap: ACL-Tabelle liegt im ersten Storage-Schema (Phase 2), nicht nachgerüstet
- Roadmap: Integrationsbeweis (IProvider + exAppRequest) steht vor jedem Feature, App-IDs und beide CSRs in Phase 1
- Engine: Tantivy 0.26 plus SQLite-ACL-Vorfilter, finaler PHP-Recheck ist die Sicherheitsgrenze
- OCR strikt index-only, Nutzerdateien werden nie verändert (CI-Prüfsummen-Gate ab Phase 1)
- [Phase 04]: Gate B kennt zwei Routenklassen: ApiRoute (ExApp, ExAppRequired plus rejectForeignCaller) und FrontpageRoute (Admin, kein Zugriffsattribut). Begruendung: Phase 4 legt den ersten PHP-Controller ohne ExAppRequired an; die Klassentrennung musste vor dem Controller stehen, sonst steht der Baum zwischendurch rot
- [Phase 04]: Eine Route mit beiden Attributnamen gilt als Admin-Route. Begruendung: die Admin-Klasse ist die strengere, also wird Vermischung gemeldet statt durchgelassen
- [Phase 04]: php/templates wird per .gitkeep offengehalten, statt den find-Pfad des php -l-Jobs tolerant zu machen. Begruendung: jede tolerante Schreibweise laesst das Gate stumm weniger pruefen als es behauptet
- [Phase 04]: Der Container meldet maxFileBytes aus settings() auch ohne Zustandsdatenbank, damit die PHP-Einstellung an den wirklich durchgesetzten Deckel geklemmt wird
- [Phase 04]: Die Aufteilung der Wahrheit steht woertlich in beiden Docblocks: skipped, failed und die Fehlerliste aus findling_file_state, indexed, truncated, Platz und Versionsmarken aus dem Container
- [Phase 04]: access_level ADMIN deckt nur den AppAPI-Proxy-Weg; der wirksame Schutz der Admin-Seite ist die PHP-Route ohne NoAdminRequired
- [Phase 04]: Der Override-Attribut-Verzicht in den neuen Settings-Klassen: PHP 8.3 gegen die deklarierte min-version 8.2
- [Phase 04]: Die Statuszeile nennt keine Restzeit, solange kein kalibrierter Durchsatz existiert (kein Schaetzwert, der wie eine Messung aussieht)
- [Phase 04]: indexedDisplay waehlt zwischen Container- und Nextcloud-Zahl statt zu verrechnen, damit keine Kachel wegen einer gescheiterten Abfrage auf 0 springt
- [Phase 04]: Stockt-Schwelle 1800 Sekunden, sechs verpasste Runden des Fuenf-Minuten-Systemcrons
- [Phase 04]: SettingsController erweitert Controller und nicht OCSController, damit die Route ausserhalb des OCS-Raums bleibt
- [Phase 04]: Der Nenner des Deckungsgrads entsteht im Crawl (filesSeen minus overCap minus excluded) und nie aus einer zweiten Abfrage; die Subtraktion steht genau einmal in AdminViewService
- [Phase 04]: Idempotenz der Scan-Zaehler nach Variante (a): beginStorage setzt die Zeile bei last_file_id gleich 0 zurueck; der Cursor-Vergleich je Datei wurde verworfen
- [Phase 04]: pdf_seen ist eine eigene Spalte, weil der OCR-Anteil vor dem Lauf ein Intervall ist und keine Zahl
- [Phase 04]: percent ist auch bei stummem Backend null; 0 Prozent Deckung wird nie als Aussage gerendert
- [Phase 04]: Alle Gestalten des Deckungsgrad-Blocks liegen im Markup und werden ueber hidden geschaltet, damit die Kopfzahl ohne Neuladen erscheinen kann und das Skript kein Markup baut
- [Phase 04]: Top-Level-Schluessel indexable entfaellt aus overview(); die Zahl lebt nur noch unter coverage
- [Phase 04]: Der Durchsatz wird gemessen statt vorhergesagt: GET /rates meldet Text- und OCR-Rate getrennt ueber ein geklemmtes Fenster, und die Seite rechnet daraus hoch (ARM-Faktor unbekannt)
- [Phase 04]: Startwerte sind ein eigenes Feld (startupValues) und keine stille Annahme; die Seite beschriftet die Dauer entsprechend
- [Phase 04]: Der OCR-Anteil bleibt ein Intervall, bis die Haelfte der indexierbaren Dateien ein Verdikt hat (MEASURED_OCR_FROM_JUDGED_PERCENT)
- [Phase 04]: Der Platzbedarf entsteht aus backend.indexBytes durch backend.docs und nicht aus dem Quotienten von /rates, damit die Zahl einen gescheiterten /rates-Aufruf ueberlebt
- [Phase 04]: Bei firstIndexDone wird /rates nicht mehr aufgerufen, weil der Block nicht gerendert wird
- [Phase 04]: Ohne gezaehlte Dateien zeigt Block 2 keine Nullzeile, sondern nur den Zaehl-Hinweis
- [Phase 04]: Die Label- und Abhilfe-Abbildung fuehrt 20 Grundcodes, obwohl FileStateService::REASONS 19 hat: excluded steht schon im UI-Vertrag und kommt mit Plan 04-08 in alle drei Grundlisten
- [Phase 04]: page() liest einen null-Grund als kein Filter; MAX_PAGE 50 und 20 Beispiele je Gruppe sind Auflösungskosten und ausdruecklich nicht der MAX_LIST_LENGTH-Gotcha aus CR-01
- [Phase 04]: Beispielpfade werden im Poll nie neu gebaut, nur die Gruppenzahlen, damit geoeffnete Gruppen und Tastaturfokus erhalten bleiben
- [Phase 04]: Aufklapp-Buttons liegen hidden im Markup und werden vom Skript sichtbar gemacht: ohne JavaScript alle Gruppen offen und kein totes Bedienelement
- [Phase 04]: Vorrangregel als Kette ueber sechs benannte Stufen; der Container wird einmal vor der Kette gefragt: Stufe 1 braucht den Grabstein, um geloescht von nie gesehen zu trennen, Stufe 5 das Verdikt; zwei Aufrufe waeren ein zweiter Roundtrip fuer dieselbe Antwort
- [Phase 04]: Wartet oder laeuft entscheidet die Restsperrzeit, nicht eine leere Sperrspalte: Eine freie Zeile traegt die Epoche statt NULL (Perf-Audit H3) und ein abgelaufener Anspruch ist ohne Schreibvorgang wieder frei
- [Phase 04]: App-Version bleibt bei 0.3.0, obwohl der Container eine fuenfte Route bekam: Plan 04-05 hat beide Haelften schon angehoben und beide Plaene liegen im selben Release; ein zweiter Bump haette docker.yml gegen ein nie geschnittenes Git-Tag laufen lassen
- [Phase 04]: Der Ausschluss wird von den Aufrufern angewandt, nicht von der Aufzaehlung: getFilesInMount und getFileSlice liefern jede Zeile, Crawl und Event-Listener rufen den einen Helfer isExcluded. Ein Filter in getFilesInMount haette den Crawl an einem ausgeschlossenen Ordner beendet, die Kachel Ausgeschlossen dauerhaft auf 0 gehalten und die Raeumung von Plan 04-09 gegen genau ihren Zielordner wirkungslos gemacht; ein Filter in getFileSlice haette ueber die final-Marke des Reconcile den Index eines ganzen Mounts geleert.
- [Phase 04]: Kein Config-Lexicon registriert: die Schnittstelle wurde innerhalb des Versionsfensters 32 bis 35 umbenannt, und eine Klassenreferenz, die nur auf einem Teil der Server aufloest, waere ein fataler Fehler beim Booten statt eines fehlenden Komforts. SettingsService und ExclusionService validieren stattdessen defensiv in beide Richtungen.
- [Phase 04]: The clearing of a new exclusion covers every mount the app walks, not only home mounts: The enforcement compares a prefix relative to the root of every mount in the list, and clearing fewer mounts than the crawl excludes would leave index content that nothing removes
- [Phase 04]: The diagnosis is fed the internal path plus the storage instead of the display path: A Team Folder file arrives as TeamX/x.pdf in the display space and as x.pdf in the space the crawl compares, so the display path would be a second path space
- [Phase 04, Sichtprobe]: Erfolgskriterium 3 ist trotz Wortlaut-Abweichung angenommen: die Seite sagt "Vorlaeufige Zahl, X von Y Speicherorten sind durchgezaehlt" statt der D-05-Formulierung und nennt zusaetzlich ausdruecklich, dass auf keine Bestaetigung gewartet wird. D-05 ist der Sache nach erfuellt (Owner-Entscheidung a)
- [Phase 04, Sichtprobe]: Sichtprobe 4 wird per Gap-Closure geschlossen: Skip-Verdikte des Containers werden nicht pro Datei uebergeben, nur Fehler; die Fehlerliste kann sie deshalb nicht gruppieren, die Pro-Datei-Diagnose beantwortet sie sehr wohl (Owner-Entscheidung b, DI-04-03)
- [Phase 04, Sichtprobe]: Ein Ausschluss ist kein Fehler: Kachel, gesenkter Nenner und Diagnose sind der Nachweis, die Fehlerliste bleibt eine Liste von Fehlern (Owner-Entscheidung c zu Sichtprobe 7)
- [Phase 04, Sichtprobe]: Jeder Block besitzt seine eigene [hidden]-Regel, weil eine spezifische display-Regel die User-Agent-Regel des Attributs schlaegt; das Attribut ist seit 04-03 der einzige Schaltmechanismus der Seite
- [Phase 04, Sichtprobe]: Eine Zahl, die die Seite zu halten verspricht, wird dort gemerkt, wo sie wahr war (SettingsService::rememberIndexedCount in appconfig, Schreiben nur bei Aenderung), statt aus einer Tabelle neu berechnet zu werden, die sie bauartbedingt nicht enthaelt
- [Phase 6]: 06-01: A12 positiv, vec0-KNN laeuft unter PRAGMA query_only = 1 auf amd64 und arm64; die Leseseite von repo.py behaelt ihr Pragma
- [Phase 6]: 06-01: A13 positiv, die CPython-Uebersetzung im Abbild traegt enable_load_extension; keine eigene Python-Uebersetzung noetig
- [Phase 6]: 06-01: load_extension muss vor PRAGMA query_only laufen, und sqlite-vec braucht vec_int8() an der Aufrufstelle statt eines nackten Blobs
- [Phase 6]: 06-01: onnx ist eine reine Baugruppe (dependency-group quantize), weil onnxruntime.quantization es importiert und die Laufzeit es nicht tragen soll
- [Phase 6]: 06-01: der Docker-Bau braucht ab jetzt --build-context scripts=./scripts, weil die Modellstufe scripts/dev/quantize_model.py ruft

### Pending Todos

[From .planning/todos/pending/ , ideas captured during sessions]

None yet.

### Blockers/Concerns

- Baustart erst nach der Store-Einreichung des Schwesterprojekts nextcloud-mcp-connector (September 2026), Solo-Kapazität
- Kill-Kriterium aktiv: Nextcloud GmbH hat fulltextsearch am 12.08.2026 reaktiviert. Kündigt sie eine Elasticsearch-freie Suche mit OCR an, wird das Projekt neu bewertet (Nextcloud Conference September beobachten)
- CSR-Vorlaufzeit für zwei getrennte App-Store-Einträge ist ein bekanntes Terminrisiko aus dem Schwesterprojekt
- RAM-Spitzen auf ARM sind bisher nur geschätzt, Messlauf steht in Phase 5 aus
- Zwei benannte Luecken aus der Sichtprobe 04-10, beide in .planning/phases/04-admin-sichtbarkeit-und-diagnose/deferred-items.md mit ihrer Schliessform: DI-04-03 (Skip-Verdikte pro fileid uebergeben, damit die Fehlerliste die vier Container-Gruende gruppieren kann) und DI-04-04 (Versionsmarken nach abgeschlossenem Neuaufbau neu stempeln, sonst kann der Reindex-Banner die eigene Abhilfe nie einloesen)
- Das Pruefsummen-Gate ueber das Referenzkorpus nach der Live-Raeumung steht aus und gehoert in die Phasen-Verifikation (Gate A auf Quellcode-Ebene ist gruen, die Write-Allowlist unveraendert bei drei Eintraegen)

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-09-05T03:23:58.470Z
Stopped at: Phase 6 context gathered
Resume file: None
