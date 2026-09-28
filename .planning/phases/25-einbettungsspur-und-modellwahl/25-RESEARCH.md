# Phase 25: Einbettungsspur und Modellwahl - Research

**Researched:** 2026-09-28
**Domain:** Zweiter asynchroner Nebenläufer im selben Prozess (asyncio + to_thread), Art-Filter am PHP-Anspruch mit Rückwärtsverträglichkeit, SQLite-WAL mit mehreren Verbindungen, Abbruchsemantik der Warteschlange, Gewichtspräzision mit Nachladeweg (GitHub-Release, sha256, atomares Schreiben)
**Confidence:** HIGH für Codebefunde (Zeilen gelesen), PHP-Bindungsverhalten und fp32-Artefakt (verifiziert); MEDIUM für Entwurf der Nebenläufigkeit (aus Code abgeleitet, nicht gebaut); LOW für den fp32-Laufzeitspeicher (ungemessen)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Vorentscheide aus Phase 24, die hier tragen und NICHT neu verhandelt werden: D-24-01 (Weg B, OCS-Route, Abfrage je Runde), D-24-02 (Fehler = letztes bekanntes Profil, sonst Sparsam), D-24-05 (fp32 = Nachladen bei Opt-in, Digest-Pruefung, klares Verdikt offline, Start laedt nie etwas), D-24-07 (gespeicherte Wahl bleibt bei Schrumpfung, gewaehlt vs. wirksam gemeldet). Siehe `.planning/phases/24-owner-tor-profil-ger-st-und-marken-reparatur/24-CONTEXT.md`.

#### fp32-Wahl und Kopplung ans Profil (MOD-02)
- **D-25-01 (Owner, 28.09.2026):** fp32 ist in den Profilen Standard und Leistung waehlbar, in Sparsam nie. Die RAM-Schranke der Slot-Formel rechnet den fp32-Mehrbedarf ein.
- **D-25-02 (Owner, 28.09.2026):** Bis zur Settings-UI (Phase 27) setzt der Admin die Praezision ueber einen EIGENEN occ-Schluessel (Arbeitsname `model_precision`, Werte `int8` | `fp32`, Default int8), getrennt vom Profil-Schluessel. Gelesen ueber dieselbe OCS-Route bzw. denselben Abfrageweg wie das Profil (Weg B, D-24-01), mit derselben Fehlersemantik (D-24-02: letzter bekannter Wert, sonst int8) und geschlossener Wertemenge.
- **D-25-03 (Owner, 28.09.2026):** Die Praezision wechselt NIE automatisch, weil jeder Wechsel ein kompletter Vektor-Reindex ist. Faellt die wirksame Stufe durch Hardware-Schrumpfung auf Sparsam (D-24-07), bleibt fp32 aktiv; nur die Slots folgen Sparsam. Die Statusroute meldet den Zustand (sinngemaess "fp32 gewaehlt, Box knapp").
- **D-25-04 (Owner, 28.09.2026):** Scheitert das Beschaffen von fp32 (offline, Proxy, falscher Digest), bleibt int8 aktiv, kein Reindex, klares Verdikt ("fp32 nicht verfuegbar, int8 bleibt aktiv"). Kein automatisches Wiederholen im Hintergrund; ein neuer Versuch nur auf erneute Admin-Aktion.

#### fp32-Quelle und Offline-Weg
- **D-25-05 (Owner, 28.09.2026):** Download-Quelle ist ein Asset im eigenen GitHub-Release (street1983nk/nextcloud-search), sha256 fest im Code. Keine zweite Quelle, kein HuggingFace-Rueckfall. Der Download passiert nur auf die ausdrueckliche Admin-Wahl, nie beim Start und nie im Hintergrund (Projektregel: kein Telemetrie-Phoning, Modell nicht beim Start laden).
- **D-25-06 (Owner, 28.09.2026):** Offline-Weg: Legt ein Admin die fp32-Datei selbst ins persistente Verzeichnis und stimmt der Digest, wird sie ohne Download genutzt (Zielgruppe abgeschottete Behoerdennetze, SIB-Box/openDesk). Falscher Digest = dasselbe Verdikt wie D-25-04.

#### Suche waehrend des Vektor-Reindex
- **D-25-07 (Owner, 28.09.2026):** Waehrend der Neueinbettung antwortet die lexikalische Suche vollstaendig, die semantische Haelfte nur aus bereits in der neuen Praezision eingebetteten Dokumenten und waechst mit dem Fortschritt. Kein Blau/Gruen (keine zwei Modelle gleichzeitig im RAM, kein doppelter Vektorbestand). int8- und fp32-Vektoren mischen sich nie (T-24-02, Marke aus Plan 24-01).
- **D-25-08 (Owner, 28.09.2026):** Die Adminseite zeigt Praezision plus Fortschritt (sinngemaess "Modell fp32, Neueinbettung 42 % (12.300 von 29.100)"). Quelle sind die bestehenden embedded-Zaehler der Statusroute; die Anzeige laeuft ueber die bestehende Statusflaeche, nicht ueber die neue Settings-UI (Phase 27).

#### Rueckweg fp32 zu int8
- **D-25-09 (Owner, 28.09.2026):** Wechselt der Admin zurueck auf int8, wird die fp32-Datei geloescht (Platte frei), auch eine selbst abgelegte (Owner hat die Variante "nur heruntergeladene loeschen" ausdruecklich nicht gewaehlt). Ein erneuter Wechsel auf fp32 laedt neu bzw. braucht eine neu abgelegte Datei. Der Rueckwechsel loest wie jeder Praezisionswechsel den Vektor-Reindex aus.

### Claude's Discretion
- Abbruchsemantik zweier Nebenlaeufer, Kill/Neustart mitten in beiden Spuren ohne Zeilenverlust und ohne Doppeleinbettung, gleichzeitige state.db-Zugriffe ohne Fehlerverdikte (Research-Flag der Roadmap).
- Form des Art-Filters am PHP-Anspruch (KIND embed) und der Companion-Aenderung; die Aenderung erscheint erst mit Release 1.4.0 (K6), der Container muss mit einem Companion ohne Art-Filter weiterlaufen.
- Form der RAM-Bedingung fuer den Start der Einbettungsspur in Standard/Leistung (gegen formula_memory_bytes bzw. die cgroup-Grenze) und das Warteverhalten.
- Mitnahme des idle-Guards fuer EmbeddingModel.release() aus dem Phase-23-Backlog: mit zwei Nebenlaeufern auf der geteilten Engine akut; der Plan-Schnitt entscheidet die Aufnahme.
- Asset-Name, Upload-Weg des fp32-Assets und Ablagepfad im persistenten Verzeichnis; Umgang mit einem Praezisionswechsel, waehrend noch ein Reindex laeuft.
- Genaue Texte der Verdikte und Statusfelder (Code Englisch, Seitentexte in den Sprachkatalogen erst mit Phase 27).

### Deferred Ideas (OUT OF SCOPE)
- Blau/Gruen-Reindex (alte Vektoren bis zum Abschluss aktiv): verworfen fuer die Zielhardware (doppelter RAM und Plattenplatz), nicht vorgemerkt.
- Automatisches Wiederholen eines gescheiterten fp32-Downloads: verworfen (D-25-04).

#### Reviewed Todos (not folded)
- Issue #18 Fix-Kandidaten (JPG-Verdikt, HEIF, Download-Groessenpruefung): passt nicht zum Umfang von Phase 25 (Trefferquote 0,2, nur Stichwort); wartet weiter auf budachsts Antwort, Slot-Entscheid (Phase 29 oder Einschub) beim Owner.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PAR-01 | Einbettungsspur als eigener Nebenläufer (H1): eigener Anspruch mit Art-Filter (PHP-Route, KIND embed), berührt den Tantivy-Writer nicht, wirkt ab 2 Kernen | Pattern 1 (Spur-Parameter `lane` mit Echo, verifiziertes Ignorieren fremder Parameter durch den Dispatcher), Pattern 2 (EmbeddingTrack als Eigentümer, `stored_body` ohne Writer), Pattern 3 (EmbedRunner nach dem Reconcile-Muster), Befund "ab 2 Kernen" in Pitfall 11 |
| PAR-04 | IDX-08 in Sparsam wörtlich (OCR und Einbettung nie gleichzeitig), in Standard/Leistung RAM-Bedingung | Pattern 3 (Parken, Übergabe inline/parallel, Track-Sperre), Pattern 4 (statische plus Live-Bedingung gegen `anon`), Teststrategie T1 bis T3 |
| MOD-02 | Admin wählt int8 (Default) oder fp32; Vektor-Reindex, Suche antwortet weiter, Adminseite zeigt Zustand; fp32 über den Tor-Lieferweg; ohne fp32-Wunsch kein Laufzeitspeicher | Pattern 8 (Lesen über die Profilroute, Zustandsautomat, Beschaffung, Engine-Tausch an der Spurgrenze, Rückweg), Pattern 9 (Statusfelder), Pitfalls 5 bis 9, Open Questions 1 bis 4 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.13 + uv, alle Befehle über `uv run`; Gates vor jedem Commit lokal grün: ruff-Vollregelsatz inkl. `ruff format --check`, pyright basic (lokal `PYRIGHT_PYTHON_FORCE_VERSION=latest` wie CI), vulture `--min-confidence 80`.
- Code, Bezeichner, Kommentare Englisch; echte Umlaute nur in deutscher Prosa, nie in Code, Keywords, URLs, YAML. Keine Em-/En-Dashes, keine Emojis.
- "Modell ins Image backen, kein Download beim Start" bleibt; D-24-05/D-25-05 präzisieren: nur die ausdrückliche Admin-Aktion lädt, nie der Start, nie der Hintergrund.
- Kein Telemetrie-Phoning; Logs nennen Typnamen und Zähler, nie Werte, Pfade oder Nutzertexte (T-02-107, T-02-13/14).
- Security/Privacy: Berechtigungsdurchgriff strikt; keine Inhalte verlassen den Server (der fp32-Download sendet nichts außer einem GET auf eine feste URL).
- Store-Regel: eine Messzahl (730,2 MB), Gate `test_store_metadata.py` unverändert; das Abbild ändert sich in dieser Phase nicht (fp32 kommt nicht ins Abbild).
- Nach der Phase Security-, Bug- und Performance-Audit; Befunde vor Abschluss fixen.
- Owner-Regeln: Fremde PRs/Issues nicht selbst schließen; OSS-Commits als street1983nk; Release-Upload des fp32-Assets ist eine Owner-Handlung (Checkpoint).
- Keine Project Skills vorhanden (`.claude/skills/`, `.agents/skills/` fehlen).

## Summary

Heute ist die Einbettung ein Zweig derselben seriellen Schleife: `run_once` (`worker/poller.py:732`) holt einen Anspruch über alle sechs Arten (PHP `QueueService::claim`, `QueueService.php:212-298`, Arten in der Reihenfolge von `QueueMapper::KINDS`, `QueueMapper.php:75-82`), und eine `embed`-Zeile läuft in `_handle` (`poller.py:972`) nach `_embed_the_body` (`poller.py:1263`). Diese Methode greift an drei Stellen auf Gegenstände der Indexspur zu, die ein zweiter Nebenläufer nicht teilen darf: sie liest den Text über `self._writer_or_die().stored_body` (`poller.py:1330`, also über das Objekt des Tantivy-Writers), sie schreibt Rechte über dieselbe state.db-Verbindung wie die Indexspur (`poller.py:1328`), und sie schreibt Vektoren über dieselbe vectors.db-Verbindung, über die auch der Löschpfad schreibt. Beide Store-Klassen öffnen explizite `BEGIN IMMEDIATE`-Transaktionen auf **einer** Verbindung (`store/repo.py:802`, `store/vectors.py:415`); zwei Threads auf derselben Verbindung verschränken ihre Transaktionen, und der Docstring von `open_store` benennt genau das als unsicher (`repo.py:1553-1557`). Der sichere Schnitt ist deshalb: eine **eigene Einbettungsspur mit eigenen Verbindungen** nach dem Muster der Reconcile-Aufgabe (eigener Client, eigene state.db-Verbindung, `worker/reconcile.py:172-208`), Text über einen eigenen Lese-Handle statt über den Writer, und die Vektor-Marke samt Driftkette **im selben seriellen Eigentümer wie das Einbetten**.

Der Art-Filter braucht eine kleine Companion-Änderung, und die Rückwärtsverträglichkeit ist der eigentliche Punkt: Der Nextcloud-Dispatcher bindet nur deklarierte Methodenparameter und **verwirft unbekannte Anfrageparameter still** (verifiziert in `lib/private/AppFramework/Http/Dispatcher.php`, stable33). Ein Container, der einem 1.3-Companion `?kinds=embed` schickt, bekäme also einen vollen Anspruch über alle Arten zurück, ohne jede Fehlermeldung. Deshalb muss der neue Companion den Filter **im Antwortkörper bestätigen** (Echo), und der Nebenläufer darf nur laufen, wenn das Echo gesehen wurde. Empfohlen ist ein Parameter `lane` mit geschlossener Menge (`all`, `index`, `embed`) statt einer Artliste, weil PHP wiederholte Schlüssel ohne `[]` auf den letzten Wert reduziert und eine geschlossene Menge die Validierung trivial macht.

Für MOD-02 ist das fp32-Artefakt eindeutig und verifiziert: `onnx/model.onnx` aus `intfloat/multilingual-e5-small` an Revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, 470.268.510 Byte, sha256 `ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665`, bereits im `Dockerfile:144-145` als Eingang der int8-Quantisierung gepinnt. Der Owner lädt genau diese Datei als Asset eines eigenen, unveränderlichen GitHub-Releases hoch; der Container lädt sie per httpx (Proxy-Umgebungsvariablen werden standardmäßig beachtet), folgt der Umleitung von `github.com` auf `release-assets.githubusercontent.com` (verifiziert, 302), prüft den Digest beim Streamen, schreibt atomar (`.part`, fsync, `os.replace`). Der gefährlichste Befund liegt nicht im Download, sondern im Zusammenspiel: Eine Präzisionsentscheidung, die vor dem ersten erfolgreichen Lesen der Companion-Antwort "int8" annimmt, löst auf einer fp32-Box nach jedem Start mit kurzem Gateway-Aussetzer einen kompletten Reindex aus. Der Startzustand der Präzision muss aus lokalen Fakten kommen (Marke plus verifizierte Datei), nicht aus dem Default.

**Primary recommendation:** Einbettung in eine eigene Klasse `EmbeddingTrack` ziehen (eigene state.db- und vectors.db-Verbindung, eigener Index-Lese-Handle, Eigentümer von Cutter, Engine-Präzision, Marke und Driftkette), sie in Sparsam inline aus der Hauptschleife und in Standard/Leistung aus einem `EmbedRunner`-Task mit Anspruch `lane=embed` treiben, gegenseitig ausgeschlossen durch eine Track-Sperre und durch Parken; fp32 als Zustandsautomat mit lokalem Startzustand, Download nur bei beobachtetem Wechsel int8 zu fp32 in diesem Prozess.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Spur-Filter am Anspruch (`lane`) und Echo | PHP-Companion (`QueueController::getDocuments`, `QueueService::claim`) | Container (`nc/client.py`, `nc/queue.py`) | Nur die PHP-Seite kennt die Arten-Reihenfolge und die Sperrfristen; der Container fordert an und prüft das Echo |
| Präzisionsschlüssel `model_precision` speichern und validieren | PHP (`SettingsService`, appconfig) | occ als Schreibweg bis Phase 27 | D-25-02, gleiches Muster wie `profile` |
| Präzision ausliefern | PHP (`ProfileController`, Feld in derselben Antwort) | , | eine Abfrage je Runde, gleiche Fehlersemantik (D-24-02) |
| Einbettungsarbeit holen, einbetten, quittieren | Container, `EmbedRunner` (Standard/Leistung) bzw. Hauptschleife (Sparsam) | , | PAR-01; IDX-08 in Sparsam wörtlich |
| Vektor-Marke, Driftkette, Engine-Tausch | Container, `EmbeddingTrack` (derselbe serielle Eigentümer wie das Einbetten) | Hauptschleife nur in Sparsam als Treiber | Pitfall 5: sonst mischen sich int8 und fp32 (T-24-02) |
| RAM-Bedingung | Container, neutrales Modul (reine Funktion plus Live-Leser) | Phase 26 Speicherwächter baut darauf auf | PAR-04; nur der Container sieht seine cgroup |
| fp32 beschaffen (Download, Ablage, Digest, Löschen) | Container, `embed/weights.py` (Datei) plus Netzaufruf in `nc/client.py` | Owner lädt Asset hoch (Release) | Gate A erlaubt httpx nur in `nc/client.py` |
| Präzision und Fortschritt melden | Container, `GET /status` | PHP `AdminViewService::backend()` reicht durch; Seitentext Phase 27 (siehe Open Question 1) | D-25-08 |

## Standard Stack

Keine neuen Pakete. Alles mit dem bestehenden Stack.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | 0.28.1 (`pyproject.toml:12`, `uv.lock`) | fp32-Download, Streaming, Proxy aus der Umgebung | bereits Abhängigkeit; `trust_env` ist standardmäßig an, `HTTPS_PROXY`, `NO_PROXY`, `SSL_CERT_FILE` werden beachtet [CITED: python-httpx.org/environment_variables] |
| hashlib (stdlib) | Python 3.13 | sha256 beim Streamen | kein zweiter Lesedurchgang über 470 MB |
| sqlite3 (stdlib) | Python 3.13, `threadsafety == 3` (`repo.py:607-614`) | eigene Verbindungen je Spur, WAL, `busy_timeout` 10 s | Muster Reconcile (`repo.py:1540-1560`) |
| asyncio (stdlib) | 3.13 | zweiter Task, `asyncio.Lock` als Track-Sperre, `asyncio.to_thread` | Hausregel "nichts Blockierendes auf dem Loop" (`poller.py:41-46`) |
| onnxruntime | 1.30.0 (`pyproject.toml:50`) | Session auf fp32-Datei | `Run()` auf einer Session aus mehreren Threads ist nach Aussage der Maintainer sicher (Kommentar `embed/model.py:422-432`) |
| tantivy | 0.26.x | eigener Lese-Handle über `open_index` (`index/open.py:143`), nie `.writer()` | Muster der Leseseite (`api/resources.py:714`) |

**Installation:** keine.

**Version verification:** httpx 0.28.1 steht in `uv.lock:288-289` [VERIFIED: uv.lock]; keine neue Registry-Abfrage nötig, da keine neue Abhängigkeit.

## Package Legitimacy Audit

Diese Phase installiert keine externen Pakete. slopcheck nicht nötig; Audit entfällt.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
 Nextcloud-Warteschlange (findling_queue, eine Zeile je file_id, UNIQUE)
        |                                                    |
  GET /queues/documents?n=32&max_bytes=..&lane=index   GET /queues/documents?n=8&max_bytes=MAX&lane=embed
  (Standard/Leistung; in Sparsam OHNE lane = 1.3-Draht)       (nur wenn Echo gesehen und Spur nicht geparkt)
        |  Antwort {"files":{..},"lane":"index"}              |  Antwort {"files":{..},"lane":"embed"}
        v                                                    v
 +-------- Hauptschleife (Poller, Task 1) ---------+   +---------- EmbedRunner (Task 2) -------------+
 | profile+precision lesen (eine OCS-Abfrage)      |   | Tor: wirksam != economy? Echo gesehen?      |
 | Spur entscheiden: runner aktiv? -> lane=index    |   |      RAM-Bedingung (statisch + live anon)?  |
 |                   sonst        -> ohne lane      |   |   nein -> parken (Hauptschleife bettet ein) |
 | content/ocr/acl/delete/metadata                  |   |   ja   -> Track-Sperre nehmen               |
 |  -> IndexBatchWriter.add (einziger Writer)       |   |   claim(lane=embed)                          |
 |  -> commit -> Verdikte (eigene state.db-Verb.)   |   |   je Zeile: EmbeddingTrack.embed_row         |
 |  -> requeue ocr / embed -> ack                   |   |   ack (nur done) -> Sperre frei              |
 | in Sparsam: embed-Zeilen inline, unter Sperre    |   |   leere Runde -> Markenschritt (Drift,     |
 +---------------------+----------------------------+   |     Bänder zu 500, Präzisionstausch)        |
                       |                                +---------------------+-----------------------+
                       |   beide nutzen EINEN EmbeddingTrack (Sperre = gegenseitiger Ausschluss)
                       v                                                      v
            vectors.db (Löschpfad, eigene Verbindung)   EmbeddingTrack: eigene state.db-Verbindung (replace_acl, meta),
            state.db  (Verdikte, eigene Verbindung)     eigene vectors.db-Verbindung (replace_chunks, forget_all),
                                                        eigener Index-Lese-Handle (stored_body, reload), Cutter,
                                                        Engine (int8 aus dem Abbild | fp32 aus dem Volume)

 Präzision (neutraler Zustand, precision.py):
   gewählt (Companion, D-25-02)  +  lokaler Startzustand (Marke + verifizierte Datei)  ->  gewünscht
   gewünscht fp32 und Datei fehlt und Wechsel int8->fp32 in DIESEM Prozess beobachtet -> Beschaffung (Task, Thread)
   Beschaffung: GET github.com/.../releases/download/<tag>/<asset> -302-> release-assets.githubusercontent.com
                -> .part, sha256 beim Streamen, Größendeckel, fsync, os.replace  | Fehler -> Verdikt, int8 bleibt
   Tausch nur an der Spurgrenze (keine Zeile in Arbeit): forget_all -> Cursor -> Marke(aktiv) -> Engine tauschen -> alte freigeben
   Rückweg int8: dieselbe Kette, danach fp32-Datei löschen (D-25-09)

 Status (GET /status, ADMIN): model{chosen, active, verdict, reembedRunning, embedded/indexed}, lane{mode, reason}
```

### Recommended Project Structure
```
backend/src/findling/
├── worker/poller.py      # Hauptschleife; Einbettung nur noch als Delegation an EmbeddingTrack; lane-Entscheid je Runde
├── worker/embedding.py   # NEU: EmbeddingTrack (Eigentümer) und EmbedRunner (Task 2, Muster worker/reconcile.py)
├── precision.py          # NEU, neutral wie profile.py: Precision (StrEnum), gewählt/aktiv/Verdikt, note_chosen_precision
├── memory_guard.py       # NEU, neutral: reine RAM-Bedingung + Live-Leser (memory.stat anon, memory.max, MemAvailable)
├── embed/weights.py      # NEU: Ablagepfad, Digest-Prüfung, atomares Schreiben, Aufräumen, Löschen (kein httpx)
├── embed/engine.py       # Halter gekeyt auf (Tokenizer-Verzeichnis, Gewichtspfad); swap_engine(); release_if_idle
├── embed/model.py        # EmbeddingModel mit weights_path und precision; release(idle_seconds=...) Idle-Guard
├── nc/client.py          # claim_documents(lane=...), read_profile (unverändert), fetch_release_asset (GET-Stream)
├── nc/queue.py           # ClaimResult.lane_honored; Profilantwort liefert (profile, precision)
├── index/writer.py       # stored_body als freie Funktion über ein Index-Objekt; Plattenboden als Helfer
├── profile.py            # _compute(hardware, chosen, precision): fp32-Mehrbedarf im Speicherterm
├── api/status.py         # ModelReport + LaneReport, in _volume() UND _of() übertragen
└── main.py               # Lifespan: zweiter Task, stand_down/arm für beide, Freigabe-Task fragt den Track
php/lib/
├── Controller/QueueController.php   # getDocuments(..., string $lane = 'all'), 400 bei unbekannter Spur, Echo
├── Service/QueueService.php         # LANES (geschlossen), claim($limit, $budget, $lane)
├── Controller/ProfileController.php # Antwort {"profile":..,"precision":..}
└── Service/SettingsService.php      # KEY_MODEL_PRECISION, PRECISIONS, PRECISION_DEFAULT, modelPrecision()
```

### Pattern 1: Spur-Parameter am Anspruch mit Echo (PAR-01, K6)
**What:** `GET /queues/documents` bekommt einen dritten Parameter `lane` aus einer geschlossenen Menge: `all` (Default, Verhalten 1.3), `index` (alle Arten außer `embed`), `embed` (nur `embed`). Die Antwort trägt **immer** `"lane": "<angewandte Spur>"`.

**Why so (belegt):**
- Der Dispatcher liest nur deklarierte Parameter: `foreach ($this->reflector->getParameters() as $param => $default) { $value = $this->request->getParam($param, $default); ... }` [VERIFIED: nextcloud/server stable33 `lib/private/AppFramework/Http/Dispatcher.php`]. Ein 1.3-Companion ignoriert `lane` still und liefert alle Arten. Ohne Echo kann der Container das nicht erkennen.
- Eine Artliste als wiederholter Query-Schlüssel (`kinds=a&kinds=b`) kommt in PHP als letzter Wert an; `kinds[]=` wäre nötig und ist fehleranfällig [ASSUMED: PHP-Standardverhalten von parse_str]. Eine geschlossene Menge wird wie `kind` im Requeue geprüft (`QueueController.php:301`).
- Die Reihenfolge der Arten (Priorität D-04) bleibt in `QueueMapper::KINDS`; `claim` filtert die Schleife nur (`QueueService.php:241`).
- `KIND_BATCH` und `LOCK_TIMEOUTS` bleiben unverändert (Paritätstests `test_config.py:560-567` bleiben grün). `LOCK_TIMEOUTS[embed] = 1800` ist mit einem reinen Einbettungsanspruch konservativ, schadet aber nicht.

**Container-Verhalten gegen einen alten Companion (K6):**
- In Sparsam sendet der Container **kein** `lane` (Draht bytegleich zu 1.3; `test_queue_client.py:159` prüft die Parameter heute exakt).
- In Standard/Leistung sendet die Hauptschleife `lane=index` nur, wenn der EmbedRunner aktiv ist. Fehlt das Echo, hat ein alter Companion geantwortet: die Hauptschleife hat dann `embed`-Zeilen bekommen und bettet sie inline ein (heutiges Verhalten, korrekt), und `lane_supported` bleibt falsch.
- Der EmbedRunner fordert nie an, solange in diesem Prozess kein Echo gesehen wurde. Zusätzlich (Verteidigung in der Tiefe): fehlt das Echo in **seiner** Antwort, gibt er alle erhaltenen Zeilen per `unlock` zurück (Rückerstattung der Zustellung, `QueueMapper.php:803-808`) und parkt für die Prozesslebensdauer.

**Beispiel (PHP):**
```php
// Source: Muster QueueController.php:104-133 und :301 (closed list check)
public function getDocuments(int $n = self::DEFAULT_BATCH_FILES, int $max_bytes = self::DEFAULT_BATCH_BYTES, string $lane = QueueService::LANE_ALL): DataResponse {
	$foreign = $this->rejectForeignCaller();
	if ($foreign !== null) {
		return $foreign;
	}
	if (!in_array($lane, QueueService::LANES, true)) {
		return $this->badLane(); // 400, value never logged
	}
	// ... limit/budget as today
	$files = $this->queueService->claim($limit, $budget, $lane);
	return new DataResponse(['files' => $files, 'lane' => $lane]);
}
```

### Pattern 2: EmbeddingTrack als einziger Eigentümer der zweiten Spur
**What:** Alles, was heute in `Poller` die zweite Spur ausmacht, wandert in eine Klasse `EmbeddingTrack` (`worker/embedding.py`): `_wire_the_second_track` (`poller.py:1685`), `_build_the_cutter` (`:1756`), `release_cutter` (`:1860`), `_cutter_cooling_down` (`:1907`), `_embed_ready` (`:1925`), `_needs_vectors` (`:1230`), `_embed_the_body` (`:1263`), der Markenschritt `_keep_the_vector_stock_in_step` bis `_next_backlog_band` (`:2019-2198`).

**Was sich dabei ändert, und warum:**
1. **Eigene Verbindungen.** Die Spur öffnet ihre eigene state.db-Verbindung (existierende Datei, nie anlegen, nie säen; Muster `worker/reconcile.py:172-187`) und ihre eigene vectors.db-Verbindung (`open_vectors`). Der Poller behält seine vectors.db-Verbindung für den Löschpfad (`attach_vectors`, `poller.py:1675`; `drop_document`, `index/writer.py:337-351`). Grund: `BEGIN IMMEDIATE` ist je Verbindung (`repo.py:802-810`, `vectors.py:415-423`); zwei Threads auf einer Verbindung würden "cannot start a transaction within a transaction" werfen oder, schlimmer, fremde Statements in die eigene Transaktion ziehen und per ROLLBACK verwerfen [ASSUMED: sqlite3-Semantik; der Docstring `repo.py:1553-1557` nennt die Gefahr ausdrücklich].
2. **Text ohne Writer.** `IndexBatchWriter.stored_body` (`index/writer.py:353-386`) nutzt nur `self._index` (reload plus Searcher), nie den `IndexWriter`. Als freie Funktion `stored_body(index, schema, file_id)` herausziehen; die Methode delegiert. Die Spur hält einen eigenen Index-Handle aus `open_index` (`index/open.py:143`), wie die Leseseite (`api/resources.py:714`), und ruft nie `.writer()`. Erfüllt "berührt den Tantivy-Writer nicht" wörtlich und übersteht `stand_down`, bei dem der Poller `_writer = None` setzt (`poller.py:662`), wo `_writer_or_die()` heute werfen würde.
3. **Plattenboden ohne Writer.** `disk_is_tight` (`index/writer.py:401-409`) als Helfer über Verzeichnis und `min_free_bytes` bereitstellen; eine Zahl, ein Verzeichnis (T-06-36 bleibt).
4. **Konstruktor-Injektion bleibt.** `Poller(vectors=, chunker=, model=)` reicht an den Track durch, damit die 1.827 Zeilen `test_embedding_track.py` im Refactor-Plan grün bleiben (verhaltensgleiche Welle).

### Pattern 3: EmbedRunner, Parken und gegenseitiger Ausschluss (PAR-01, PAR-04)
**What:** Ein zweiter langlebiger Task nach dem Reconcile-Muster (`worker/reconcile.py`: eigener Client über `client_factory`, `arm`/`silence`/`run`, `_guarded_reconcile` in `main.py:340-357`). Er öffnet nichts, bevor er das erste Mal aktiv wird (Sparsam bleibt Wert für Wert heutiger Container, PROF-02, Store-Zahl).

**Tor je Runde (in dieser Reihenfolge):**
1. `profile.snapshot().effective` ist `standard` oder `performance`, sonst parken.
2. `lane_supported` wurde in diesem Prozess gesehen, sonst parken (alter Companion).
3. RAM-Bedingung erfüllt (Pattern 4), sonst parken mit Grund `waiting_for_memory`.
4. Track-Sperre (`asyncio.Lock`) nehmen, `claim(limit=EMBED_CLAIM_BATCH, max_bytes=MAX_BATCH_BYTES, lane="embed")`, Zeilen einbetten, quittieren, Sperre freigeben.

**Übergabe zwischen inline und parallel (IDX-08 wörtlich in Sparsam):**
- Die Hauptschleife entscheidet je Runde nach `note_chosen` (`poller.py:751`): Ist der Runner aktiv, schickt sie `lane=index`; ist er geparkt, schickt sie keinen Filter und bettet `embed`-Zeilen inline ein, unter derselben Track-Sperre.
- Wird die wirksame Stufe economy, während der Runner mitten in einer Runde ist, wartet die Hauptschleife **vor ihrem Anspruch** auf das Parken des Runners (`asyncio.Event`, begrenzt durch eine Runner-Runde von rund 18 s nach `test_config.py:590-600`). Der Runner prüft sein Tor zusätzlich je Zeile und gibt den Rest seines Anspruchs per `unlock` zurück. Damit gibt es ab dem Wechsel keine Überlappung von OCR und Einbettung mehr, auch nicht für eine Runde.
- Die Warteschlange liefert den zweiten Ausschluss gratis: `file_id` ist eindeutig und ein Anspruch ist eine bedingte Aktualisierung mit Token (`QueueMapper.php:12-21`, `:389-399`). Zwei Nebenläufer halten nie dieselbe Datei gleichzeitig, außer nach Ablauf einer Sperrfrist.

**Warum Sperre plus Parken und nicht nur eines:** Die Sperre verhindert, dass zwei Treiber den Track gleichzeitig nutzen (Cutter, Engine-Tausch, Markenschritt). Das Parken verhindert, dass in Sparsam OCR neben Einbettung läuft. Beides zusammen ist die wörtliche Lesart von IDX-08.

**embed_slots:** `ProfileValues.embed_slots` ist 1 (Standard) bzw. 2 (Leistung) (`config.py:873`, `:886`). Zwei gleichzeitige Zeilen teilen den Chunker, dessen Tokenizer der Maintainer nicht als threadsicher zusagt (`embed/model.py:418-420`). Empfehlung: Slots als `asyncio.Semaphore` über die Zeilen eines Anspruchs, Chunker-Aufruf und Vektor-Schreiben je unter einer Track-internen Sperre, Graphlauf parallel (die Engine sperrt nur das Encoding). Siehe Open Question 3.

### Pattern 4: RAM-Bedingung, statisch und live (PAR-04)
**Statisch (aus der Momentaufnahme, ohne Messung):** Der Speicherterm der Slotformel (`profile.py:173-176`) bekommt den fp32-Mehrbedarf und die Aktivierungsspitze der Einbettung abgezogen. Bedingung: `memory_term >= ocr_slots` (die Formel wurde nicht durch `max(1, ...)` künstlich auf einen Slot gehoben). `MAIN_PROCESS_BASELINE_BYTES` (1.257,5 MiB, `config.py:862`) enthält Gewichte, Tokenizer und Cutter bereits, weil er während einer Einbettungsphase gemessen wurde; der parallele Zusatz ist im Kern die Aktivierung (+26,4 MB gemessen, `docs/embeddings.md:595`) plus, bei fp32, der Gewichtsmehrbedarf.

**Live (je Runner-Runde, billig):** Mit Grenze (`memory.max` gesetzt): `headroom = memory.max - anon` aus `memory.stat`. Ohne Grenze: `MemAvailable` aus `/proc/meminfo`. Bedingung: `headroom >= reserve + EMBED_ACTIVATION_BYTES` (+ Ladekosten von Cutter und Gewichten, wenn noch nicht geladen). **`anon`, nicht `memory.current`:** `memory.current` zählt den Seitencache der Tantivy-mmap mit, der zurückgefordert werden kann; das Projekt misst durchgängig `anon` (Store-Zahl, `rss_sampler.sh`). Pitfall 3 aus Phase 24 (Profil flattert gegen die eigene Modelllast) gilt hier nicht, weil es keine Profilentscheidung ist, sondern eine Zulassung je Runde; gegen Flattern: nach einem Nein mindestens die Runner-Pause warten.

**Verhalten bei Nein:** Der Runner parkt mit Grund, die Hauptschleife bettet seriell ein (IDX-08-Verhalten wie Sparsam). Das erfüllt "sonst wartet sie" für die Spur und verhindert, dass die semantische Hälfte auf einer knappen Box nie gefüllt wird. Siehe Open Question 2, falls der Owner stattdessen "Zeilen warten" will.

**Ort:** `memory_guard.py`, neutral (stdlib, `hardware.py`-Leser, injizierbare Pfade wie `hardware.detect`), damit Phase 26 den Speicherwächter darauf baut.

### Pattern 5: Abbruchsemantik zweier Nebenläufer (Kill, Neustart, Sperrfristen)
**Was heute schon trägt (belegt):**
- Mindestens einmal ausliefern: eine nicht quittierte Zeile kommt nach `LOCK_TIMEOUTS[kind]` zurück (`QueueMapper.php:136-143`); Zustellungen zählen (`claimBatch` erhöht `retries`, `:395`), `unlock` erstattet zurück (`:803-808`).
- Höchstens einmal einbetten: `replace_chunks` löscht und schreibt die Chunks einer Datei in **einer** Transaktion (`vectors.py:425-459`); eine Wiederholung ersetzt, verdoppelt nie (Test `test_a_second_write_of_the_same_file_does_not_double_the_stock`, `test_embedding_track.py:865`).
- Driftkette ist wiederholbar: leeren, Cursor, Marke, Bänder; jeder Abbruch dazwischen wird beim nächsten Leerlauf wieder aufgenommen (`poller.py:2143-2173`).

**Was mit dem zweiten Nebenläufer neu dazukommt:**
1. **Unbehandelte Ausnahme hält Zeilen.** `Poller.run` fängt jede Ausnahme (`poller.py:724-729`), gibt die gehaltenen Zeilen aber nicht zurück; die nächste Runde überschreibt `_held` (`:802`). Die Zeilen laufen in die Sperrfrist und verbrauchen eine Zustellung; nach drei solchen Runden endet eine gesunde Datei als `failed(repeatedly_stuck)` (`QueueService.php:256-260`). Genau das wäre das "Fehlerverdikt" aus Success Criterion 3, sobald ein `sqlite3.OperationalError: database is locked` auftritt. **Beide Treiber müssen SQLite-Fehler wie `_abort` behandeln** (`poller.py:1953-1979`): Zeilen per `unlock` zurück, Pause, kein Verdikt.
2. **Übergabe gibt fremde Zeilen frei.** `requeueAs` setzt `locked_at` auf frei, auch für eine Zeile, die gerade jemand hält (`QueueMapper.php:632`). Läuft die Driftkette in der Hauptschleife, während der Runner eine Zeile hält, bettet der Runner diese Datei womöglich mit der **alten** Präzision nach `forget_all` ein und quittiert die neue Vorlage weg (Pitfall 5). Deshalb gehört der Markenschritt in den Track-Eigentümer, der zu dem Zeitpunkt nichts hält.
3. **`unlock_held` beim Herunterfahren.** Nach Schritt 3b und vor der Quittung enthält `_held` der Hauptschleife auch die gerade übergebenen Zeilen (`poller.py:802`, `:865-866`); ein `unlock_held` in diesem Fenster (`main.py:931-932`) gibt Zeilen frei, die der Runner inzwischen hält. Folge: eine doppelte, idempotente Einbettung, kein Verlust. Empfehlung: nach erfolgreichem Requeue die übergebenen Queue-IDs aus `_held` nehmen.
4. **Neustart:** Beide Spuren sind zustandslos bis auf Warteschlange, state.db und vectors.db. Ein Kill mitten in beiden: Indexspur ist durch Commit-vor-Quittung gedeckt (Modulkopf `poller.py:1-32`), Einbettungsspur durch `replace_chunks` plus Sperrfrist 1800 s. Ein sauberer Stopp gibt die Zeilen beider Spuren zurück (Runner braucht ein eigenes `unlock_held` im Lifespan-Abbau, `main.py:921-934`).
5. **Rebuild (Verzeichnistausch):** `_stand_the_poller_down` (`main.py:434-481`) kennt nur den Poller. Der Runner hält einen Index-Handle auf das alte Verzeichnis und muss mit herunterfahren (gleiches `stand_down`-Muster: stilllegen, auf die Runde warten, Zeilen zurück, Handle abgeben) und mit `_arm_the_poller` (`main.py:484-496`) wieder bewaffnet werden.

### Pattern 6: SQLite unter zwei Schreibern
- WAL ist gesetzt (`repo.py:576-593`), `busy_timeout` 10 s auf beiden Datenbanken (`repo.py:217`, `vectors.py:112`), `synchronous = NORMAL` für Schreibverbindungen (`repo.py:638`).
- Zwei Schreibverbindungen auf einer Datei sind unter WAL sicher, weil SQLite sie serialisiert; `BEGIN IMMEDIATE` wartet auf die Schreibsperre im Rahmen des `busy_timeout` statt mitten in der Transaktion auf SQLITE_BUSY zu laufen (Präzedenz Reconcile, `repo.py:1540-1560`).
- Schreibmenge je Spur: Hauptschleife `record`/`replace_acl`/`tombstone`/`refresh_meta` (je Datei eine kurze Transaktion), Einbettungsspur `replace_acl` je Zeile und `write_meta` (Marke, Cursor). vectors.db: Hauptschleife `drop_vectors`, Einbettungsspur `replace_chunks`/`forget_all`. Alles Millisekunden; 10 s werden nicht erreicht [ASSUMED: aus der Transaktionsgröße, nicht gemessen].
- Unterschiedliche Meta-Schlüssel: Marken des Volltextindex schreibt nur die Hauptschleife (`_stamp_if_rebuilt`), `embedding_version` und `embedding_backlog` nur der Track.

### Pattern 7: Idle-Guard in `EmbeddingModel.release()` (Mitnahme, Empfehlung: aufnehmen)
**Warum jetzt akut:** `release_if_idle` liest `last_use` zweimal (`engine.py:471-490`), die eigentliche Freigabe `held.release()` prüft unter ihrer eigenen Sperre aber nur `_in_flight` (`model.py:660-672`). Zwischen der zweiten Lesung (unter `engine._LOCK`) und `release()` (unter `model._lock`) kann eine Einbettung beginnen und enden; mit Suche plus Einbettungsspur plus Hauptschleife gibt es jetzt drei Nutzer statt zwei. Zusätzlich prüft der Freigabe-Task nur `poller.busy` (`main.py:408-417`) und ruft `poller.release_cutter()`; der Cutter gehört künftig dem Track.

**Kleinste sichere Form:** `release(self, *, idle_seconds: float | None = None) -> bool` prüft unter `self._lock` zusätzlich `last_use` gegen `idle_seconds`; `release_if_idle` übergibt `ttl_seconds`. Der Freigabe-Task fragt `track.busy` (Zeile in Arbeit, egal welcher Treiber) und ruft `track.release_cutter()`. Test: Einbettung zwischen zweiter Lesung und `release()` einschieben (Monkeypatch am Übergang), Freigabe muss `False` liefern.

### Pattern 8: Präzision (MOD-02)
**8a. Lesen (D-25-02).** Die Profilroute antwortet `{"profile": ..., "precision": ...}` (`ProfileController.php:54-72` erweitern; `SettingsService::modelPrecision()` nach dem Muster `profile()`, `SettingsService.php:270-284`, geschlossene Menge `PRECISIONS = ['int8', 'fp32']`, Default `int8`, `reject()` ohne Wert). Eine OCS-Abfrage je Runde wie bisher, kein neuer Pfad, Gate B (`test_php_trust_boundary.py:314`) und Read-only-Gate unverändert. Container: `DocumentQueue` liefert beide Werte aus einer Antwort, jeder fällt einzeln auf `None` bei fehlend oder unbekannt (T-24-16-Muster, `nc/queue.py:505-524`). Paritätstest wie `test_profile_wire.py:20-49` für `PRECISIONS`.

**8b. Zustand (neutrales Modul `precision.py`).**
- `chosen`: zuletzt erfolgreich gelesener Wert (D-24-02-Semantik), `None` vor dem ersten Lesen.
- `honored`: fp32 nur, wenn das **gewählte** Profil (nicht das wirksame) `standard` oder `performance` ist (D-25-01 "wählbar"; D-25-03 "Schrumpfung behält fp32"). Ein fp32-Wunsch unter gewähltem Profil economy wird nicht beschafft, Verdikt `fp32_not_in_economy`.
- `active`: was die Engine tatsächlich lädt, `int8` oder `fp32`.
- **Startzustand aus lokalen Fakten, nicht aus dem Default:** Beim ersten Markenschritt nach dem Start ist `active = fp32` genau dann, wenn die gespeicherte Marke `.../fp32` trägt UND die Datei am Ablagepfad liegt UND ihr Digest stimmt. Sonst `int8`. Bis zum ersten erfolgreichen Lesen der Companion-Antwort ändert sich `active` nicht (Pitfall 6).
- **Download-Auslöser:** nur ein in diesem Prozess beobachteter Übergang des gewählten Werts von `int8` auf `fp32`. Ein Prozess, der beim ersten Lesen schon `fp32` sieht, nutzt eine vorhandene, verifizierte Datei (Offline-Weg D-25-06) und lädt sonst nichts, Verdikt `fp32_unavailable` mit Hinweis auf erneutes Wählen. So gibt es keinen Download beim Start und kein Wiederholen nach Neustart (D-24-05, D-25-04). Siehe Open Question 4.

**8c. Beschaffung.**
- Quelle: ein eigenes, unveränderliches Release im Repo `street1983nk/nextcloud-search` mit einem Tag nur für das Modell (Vorschlag `model-e5-small-fp32-614241f`), Asset `multilingual-e5-small-fp32-614241f.onnx`, dazu die MIT-Lizenzdatei. Unveränderliche Releases sperren Tag und Assets und erzeugen eine Release-Attestation [CITED: docs.github.com/.../immutable-releases]. Ein Asset darf bis 2 GiB groß sein [CITED: docs.github.com/.../about-releases]. Upload durch den Owner (Checkpoint), nicht durch Claude.
- Konstanten im Code: URL, `FP32_SHA256 = "ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665"`, `FP32_BYTES = 470_268_510` [VERIFIED: HuggingFace API, tree onnx an Revision 614241f; identisch mit `Dockerfile:144-145`].
- Netzaufruf in `nc/client.py` (Gate A: httpx nur dort, `test_readonly_gate.py:57`), als GET-Stream (Invariante 3 beurteilt nur schreibende Methoden). Eigener Client ohne AppAPI-Header, `follow_redirects=True` mit höchstens drei Sprüngen, nur `https`, nur Hosts `github.com` und `release-assets.githubusercontent.com` (verifiziert: 302 dorthin, signierte URL mit kurzer Laufzeit). `trust_env` bleibt an (Proxy aus der Umgebung). Größendeckel: mehr als `FP32_BYTES` Byte bricht ab (Muster `_stream_file`, `client.py:245-253`).
- Datei-Seite in `embed/weights.py` (kein httpx): Ablagepfad `${APP_PERSISTENT_STORAGE}/models/multilingual-e5-small-fp32/model.onnx` (neben `dict/`, `config.py:1399-1404`); vorher freien Platz prüfen (`FP32_BYTES + min_free_bytes`); schreiben nach `model.onnx.part` im selben Verzeichnis, sha256 beim Schreiben, `fsync`, `os.replace`; `.part`-Reste beim Start löschen (Muster `_clear_scratch`, `poller.py:2387-2398`); Digest einer vorhandenen Datei einmal je Prozess im Thread prüfen und Ergebnis an `(size, mtime_ns)` merken. Gate-A-Invariante 2 verbietet die Bezeichner `mkdir`, `move`, `copy`, `delete` außerhalb freigegebener Paare (`test_readonly_gate.py:63-121`): für das Verzeichnis entweder ein neues Ausnahmepaar `("embed/weights.py", "mkdir")` in eigenem Schritt mit Begründung, oder `os.makedirs` meiden und das Verzeichnis über `open_store`-Muster anlegen; `os.replace` und `Path.unlink` sind erlaubt.
- Laufzeit: 470 MB bei 10 MB/s sind rund 47 s; die Beschaffung läuft als eigener Task (Thread für Datei-IO), blockiert keine Runde; der Status meldet `downloading`.

**8d. Engine-Tausch an der Spurgrenze (D-25-07).**
- `EmbeddingModel` bekommt `weights_path` und `precision`; `_artifacts_present` prüft Tokenizer im Abbild-Verzeichnis und Gewichte am Gewichtspfad (heute beides in einem Verzeichnis, `model.py:291-299`). Der Halter in `engine.py` wird auf `(tokenizer_dir, weights_path)` gekeyt (`engine.py:144-168`).
- Tausch nur durch den Track-Eigentümer, unter der Track-Sperre, ohne Zeile in Arbeit, in dieser Reihenfolge: `forget_all` → Cursor `0` → Marke `embedding_mark(..., weights=<neue aktive>)` → Halter tauschen (neue Suchen nutzen sofort das neue Modell) → alte Engine freigeben (bei laufender Suche `release()` wiederholen, bis `_in_flight == 0`; die lokale Referenz der Suche hält das Objekt bis zum Ende am Leben, `model.py:536-547`) → Leseseite benachrichtigen (`marks_stamped`, `poller.py:459`).
- Nie zwei Modelle geladen: das neue lädt erst bei der nächsten Einbettung (faul), die alte Freigabe kommt vorher. Die Suche bettet ihre Anfrage während des Reindex mit der neuen Präzision ein und findet nur bereits neu eingebettete Dokumente (D-25-07).
- Wechsel während eines laufenden Reindex: neuer Wechsel = dieselbe Kette, der Cursor beginnt wieder bei `0` (Discretion; einfach und korrekt, weil der Bestand ohnehin geleert wird).
- IN-02: `embedding_mark(model, *, tokens, weights)` ohne Default (`vectors.py:271`); beide Aufrufer (`poller.py:2111`, `api/resources.py:265`) übergeben `active` aus dem Präzisionszustand.

**8e. Rückweg (D-25-09).** Gewählt `int8` bei aktivem `fp32`: dieselbe Kette mit `int8`, danach die Datei am Ablagepfad löschen (auch selbst abgelegt), dann Verdikt leeren. Auf Linux ist das Löschen einer geöffneten oder gemappten Datei unkritisch.

**8f. Slotformel (D-25-01).** `profile._compute` bekommt die Präzision; ist fp32 gewünscht und honoriert, zieht der Speicherterm `FP32_EXTRA_BYTES` ab (`profile.py:173-176`). Die Konstante ist ungemessen (Assumption A1); Wave 0 misst sie.

**8g. Wer ohne fp32-Wunsch zahlt nichts.** Kein Import von `embed/weights.py` oder des Download-Pfads im Startweg, kein zusätzlicher Halter, keine Prüfung einer Datei, die nicht existiert (ein `stat`). Test: nach dem Start ohne fp32-Wunsch ist `embed.weights` nicht in `sys.modules` bzw. kein Digest wurde gerechnet.

### Pattern 9: Statusfelder (D-25-03, D-25-08)
- Neues verschachteltes Modell `ModelReport` in `StatusResponse` (`api/status.py:169`): `precisionChosen` (`int8`|`fp32`|None), `precisionActive`, `precisionVerdict` (geschlossene Menge, z. B. `""`, `downloading`, `fp32_unavailable`, `fp32_not_in_economy`, `fp32_on_a_tight_box`), `reembedRunning` (Cursor `embedding_backlog` nicht leer). Fortschritt = bestehende Zähler `embedded` (Dokumente mit Vektor, `status.py:421-466`) gegen `indexed`.
- `LaneReport`: `mode` (`inline`|`parallel`), `reason` (`economy`|`companion_without_lane`|`waiting_for_memory`|`""`).
- In `_volume()` setzen UND in `_of()` übertragen (Pitfall 2 aus Phase 24, `status.py:469-538`), `FIELDS` in `test_status_endpoint.py:74` erweitern, IN-03-Parität für `PROFILE_VALUE_KEYS` gleich mitnehmen.

### Anti-Patterns to Avoid
- **Den Runner die Poller-Verbindungen mitbenutzen lassen:** verschränkte `BEGIN IMMEDIATE` auf einer Verbindung (Pattern 2).
- **`stored_body` über `self._writer_or_die()` im Runner:** berührt das Writer-Objekt und wirft nach `stand_down`.
- **Markenschritt in der Hauptschleife, Einbettung im Runner:** Mischbestand (Pitfall 5).
- **Artliste als wiederholter Query-Schlüssel:** PHP liest den letzten Wert.
- **Filter ohne Echo vertrauen:** ein 1.3-Companion ignoriert ihn still.
- **Präzision vor dem ersten Lesen auf int8 setzen und die Marke dagegen prüfen:** löscht den fp32-Bestand nach einem Aussetzer (Pitfall 6).
- **`memory.current` als Belegung:** zählt Seitencache mit.
- **Download beim ersten Lesen nach dem Start:** automatisches Wiederholen durch die Hintertür.
- **Profilwert `embed_slots` > 1 mit geteiltem Chunker ohne Sperre.**

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Zweiter Nebenläufer | eigene Task-Verwaltung | Muster `Reconcile` (`worker/reconcile.py`) plus `_guarded_reconcile` (`main.py:340`) | arm/silence/run, eigener Client, eigene state.db-Verbindung sind erprobt |
| Zeilen ohne Urteil zurückgeben | eigene Rückgabe | `DocumentQueue.unlock` (`nc/queue.py:448`) mit Rückerstattung (`QueueMapper.php:784`) | DI-05-23: sonst `failed(repeatedly_stuck)` |
| Vektor-Reindex bei Präzisionswechsel | neue Kette | `_answer_the_vector_drift` (`poller.py:2143`) im Track | Reihenfolge ist sicherheitsrelevant und getestet (`test_embedding_track.py:1250-1299`) |
| Download-Streaming mit Deckel | eigene Schleife ohne Kontextmanager | `client.stream(...)` wie `_stream_file` (`client.py:221-254`) | Verbindung wird bei Ausnahme sauber zurückgegeben |
| Integritätsprüfung | Größenvergleich | sha256 über den Strom, fest im Code | D-25-05; Größe allein ist kein Beweis |
| Atomisches Ersetzen | Kopieren und Umbenennen in zwei Schritten | `.part` + `fsync` + `os.replace` im selben Verzeichnis | kein halber Stand nach Kill |
| Einzelwerte aus der Umgebung | neuer Parser | `_bounded_int_from_environment` (`config.py`) | Vertrag "warnt, fällt zurück, loggt keinen Wert" |
| Profil-/Präzisionsfehler vom Companion | Versionsprüfung | Muster `DocumentQueue.profile()` (jede Ausnahme → None) | im Upgrade-Fenster erprobt |

**Key insight:** Alles Riskante dieser Phase liegt an Grenzen, die heute implizit durch "es gibt nur einen Nebenläufer" gesichert sind: eine SQLite-Verbindung, ein Halter der Zeilen, ein Treiber des Markenschritts. Die Arbeit ist, diese Annahmen explizit zu machen, nicht neue Mechanik zu erfinden.

## Runtime State Inventory

MOD-02 berührt gespeicherten Zustand, deshalb vollständig:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | state.db meta `embedding_version` (int8-Marke bytegleich zu 1.3.x, fp32 mit `/fp32`), `embedding_backlog` (Cursor); vectors.db `chunks`; neu: fp32-Datei unter `${APP_PERSISTENT_STORAGE}/models/multilingual-e5-small-fp32/model.onnx` | keine Migration; Code-Regel: Marke immer aus der aktiven Präzision; Startzustand aus Marke plus Datei |
| Live service config | appconfig `findling/model_precision` neu (occ bis Phase 27); `findling/profile` besteht | Leser validiert (geschlossene Menge); Uninstall löscht per `deleteApp` alle Schlüssel (Phase-24-Befund `test_uninstall_contract.py:258`) |
| OS-registered state | None, verifiziert: keine Dienst- oder Aufgabenregistrierung | none |
| Secrets/env vars | keine neue Variable; `HTTPS_PROXY` wird von httpx gelesen, ist aber in `info.xml` nicht deklariert und damit über AppAPI nicht setzbar (Phase-24-Befund: nicht deklarierte Namen werden ignoriert) | dokumentieren (Offline-Weg D-25-06 ist der Weg für Proxy-Netze); siehe Open Question 5 |
| Build artifacts | Abbild unverändert (fp32 nicht im Abbild); GitHub-Release-Asset ist ein neues externes Artefakt | Owner-Checkpoint: Asset hochladen, Release unveränderlich machen |

## Common Pitfalls

### Pitfall 1: Alter Companion ignoriert den Filter still
**What goes wrong:** Der Runner fordert `lane=embed` an, bekommt `content`- und `ocr`-Zeilen und behandelt sie als Einbettung oder lässt sie liegen.
**Why it happens:** Der Dispatcher bindet nur deklarierte Parameter (verifiziert).
**How to avoid:** Echo `"lane"` in jeder Antwort des neuen Companions; Runner nur nach gesehenem Echo; fehlt das Echo in seiner eigenen Antwort, alle Zeilen `unlock` und für die Prozesslebensdauer parken.
**Warning signs:** Runner meldet eingebettete Zeilen mit anderer Art; Status `lane.reason` bleibt leer, obwohl der Companion 1.3 ist.

### Pitfall 2: Geteilte SQLite-Verbindung zwischen zwei Threads
**What goes wrong:** "cannot start a transaction within a transaction" oder ein ROLLBACK verwirft fremde Schreibvorgänge.
**Why it happens:** `BEGIN IMMEDIATE` je Verbindung (`repo.py:804`, `vectors.py:417`); `check_same_thread=False` (`repo.py:630`) hebt die Python-Wache auf, nicht die Transaktionsgrenze.
**How to avoid:** Eigene Verbindungen für den Track; Test mit zwei Threads, die gleichzeitig `replace_acl` und `record` schreiben, jeder über seine Verbindung.
**Warning signs:** `OperationalError` im Log mit Typnamen, Zeilen kommen nach 1800 s wieder.

### Pitfall 3: Ausnahme im Runner verbraucht Zustellungen
**What goes wrong:** `database is locked` oder ein anderer Fehler endet im generischen Zweig; gehaltene Zeilen werden nicht zurückgegeben und laufen nach drei Runden in `failed(repeatedly_stuck)`.
**Why it happens:** `Poller.run` gibt `_held` im Ausnahmezweig nicht frei (`poller.py:724-729`, `:802`).
**How to avoid:** Im Runner (und für SQLite-Fehler auch in der Hauptschleife) `_abort`-Semantik: `unlock`, Pause. Test mit injiziertem `OperationalError`.
**Warning signs:** `failed(repeatedly_stuck)` auf gesunden Dateien in der Fehlerliste.

### Pitfall 4: Tausch der Freigabe-Prüfung vergessen
**What goes wrong:** Der Freigabe-Task gibt Gewichte oder Cutter frei, während der Runner eine Zeile bearbeitet (er prüft nur `poller.busy`, `main.py:409`).
**How to avoid:** `track.busy` prüfen, `track.release_cutter()` rufen, Idle-Guard in `release()` (Pattern 7).

### Pitfall 5: Mischbestand durch getrennte Treiber
**What goes wrong:** Hauptschleife erkennt Drift, leert den Bestand und schreibt die fp32-Marke, während der Runner eine Datei mit der int8-Engine einbettet und nach `forget_all` schreibt; `requeueAs` hat die Zeile zudem freigegeben, der Runner quittiert sie weg.
**Why it happens:** `requeueAs` löst fremde Sperren (`QueueMapper.php:632`); Marke (state.db) und Vektoren (vectors.db) liegen in zwei Dateien, keine gemeinsame Transaktion.
**How to avoid:** Markenschritt, Driftkette und Engine-Tausch nur im Track-Eigentümer, unter der Track-Sperre, ohne Zeile in Arbeit.
**Warning signs:** `embedded` erreicht nach einem Wechsel nicht `indexed`; T-24-02 verletzt ohne Fehlermeldung.

### Pitfall 6: Präzision vor dem ersten Lesen auf int8 gesetzt
**What goes wrong:** Nach einem Neustart mit kurzem Gateway-Aussetzer rechnet der Markenschritt `wanted = int8` gegen eine gespeicherte fp32-Marke: Drift, kompletter Reindex, danach nach dem ersten Lesen wieder fp32: zweiter Reindex.
**Why it happens:** D-25-02 "sonst int8" wörtlich auf den aktiven Zustand angewandt.
**How to avoid:** Startzustand aus Marke plus verifizierter Datei; der Markenschritt läuft erst, wenn der Präzisionszustand "gesetzt" ist; "sonst int8" gilt nur, wenn lokal nichts auf fp32 deutet. Test: fp32-Marke plus gültige Datei, Profilroute wirft, Leerlaufrunde, kein `forget_all`.

### Pitfall 7: Seitencache als Speicherbelegung
**What goes wrong:** Mit `memory.current` sieht die RAM-Bedingung auf einer Box mit großem Index nie Luft; der Runner parkt dauerhaft.
**How to avoid:** `anon` aus `memory.stat` gegen `memory.max`; ohne Grenze `MemAvailable`.

### Pitfall 8: Umleitung und Proxy beim Download
**What goes wrong:** `follow_redirects=False` (Muster des Gateway-Clients, `client.py:201-207`) scheitert an der 302 von GitHub; oder ein Proxy lässt `github.com` durch, aber nicht `release-assets.githubusercontent.com`.
**How to avoid:** Eigener Client mit begrenzter Umleitung auf zwei erlaubte Hosts, ohne Zugangsdaten; im Verdikt und in `docs/embeddings.md` beide Hosts nennen; Offline-Weg dokumentieren.

### Pitfall 9: Gate A und Gate-A-Invariante 2
**What goes wrong:** `import httpx` in `embed/weights.py` oder `Path.mkdir` im neuen Modul macht `test_the_real_package_has_no_violations` rot.
**How to avoid:** Netz in `nc/client.py`; Verzeichnisanlage entweder als bewusstes Ausnahmepaar in eigenem Schritt (Muster `INVARIANT_2_EXCEPTIONS`, `test_readonly_gate.py:113-121`) oder über einen Weg ohne verbotenen Bezeichner.

### Pitfall 10: Baum-Hash-Pins und parallele Wellen
**What goes wrong:** Jeder Plan, der eine Datei unter `backend/src/findling` oder `php/` ändert, verschiebt `PACKAGE_TREE_HASH_TODAY` (`test_measurement_scripts.py:1286`) bzw. `PHP_TREE_HASH_TODAY` (`:671`); zwei parallele Python-Pläne kollidieren in derselben Zeile, und neue Dateien ändern `PACKAGE_FILES_TODAY` (`:1285`) bzw. `PHP_FILES_TODAY` (`:670`).
**How to avoid:** Wie in Phase 24: jeder Plan aktualisiert die Zeile mit Kommentar; nach jedem Wellen-Merge einmal neu messen ("Measured again after the wave merge"). Neue Module zählen (`worker/embedding.py`, `precision.py`, `memory_guard.py`, `embed/weights.py` = vier neue Python-Dateien).

### Pitfall 11: "Wirkt ab 2 Kernen" gegen die Vorschlagsschwellen
**What goes wrong:** Erwartung, der Runner laufe auf 2-Kern-Boxen. `effective = min(chosen, suggested)` (`profile.py:147-150`, `:270-279`) und Standard wird erst ab 3 Kernen und 6 GB vorgeschlagen (`config.py:906-909`). Auf 2 Kernen ist die wirksame Stufe immer economy, der Runner parkt.
**How to avoid:** Im Plan und in `docs/profiles.md` festhalten: Der Nebenläufer ist ab 2 Kernen technisch lauffähig, wird aber über D-24-06/D-24-07 erst ab 3 Kernen und 6 GB wirksam. Kein Widerspruch zu PAR-01, aber eine Doku-Pflicht. Für Tests Hardware injizieren (`note_hardware` mit 4 Kernen, 16 GB).

### Pitfall 12: Fakes ohne neue Parameter
**What goes wrong:** Vier Fakes mit `def claim(` (`test_poller.py`, `test_embedding_track.py`, `test_acl_prefilter.py`) und vier mit `def profile(` kennen `lane` bzw. die Präzisionsantwort nicht; `run_once` endet im Generalfang mit "unexpected TypeError".
**How to avoid:** Alle Fakes im selben Plan wie die Signaturänderung anpassen (Phase-24-Pitfall 7).

## Code Examples

### Claim mit Spur und Echo (Container)
```python
# Source: Muster nc/client.py:327-343 und nc/queue.py:365-405
async def claim_documents(nc: AsyncNextcloudApp, *, limit: int, max_bytes: int, lane: str | None = None) -> object:
    params: dict[str, object] = {"n": limit, "max_bytes": max_bytes}
    if lane is not None:
        # Omitted for "all": an economy container speaks the 1.3 wire byte for byte.
        params["lane"] = lane
    return await nc._session.ocs("GET", "/ocs/v2.php/apps/findling/queues/documents", params=params)

# in DocumentQueue.claim, before the early return for an empty answer:
payload = _mapping(answer)
echoed = payload.get("lane") if payload is not None else None
lane_honored = isinstance(echoed, str) and echoed in LANES and (lane is None or echoed == lane)
```

### Runner-Runde mit Abbruchsemantik
```python
# Source: Muster Poller.run_once (poller.py:732-901) und _abort (:1953-1979)
async def run_once(self) -> str:
    if not self._gate_open():                      # economy, no echo yet, memory tight
        self._parked.set()
        return LANE_PARKED
    async with self._track.lock:                   # mutual exclusion with the inline driver
        self._parked.clear()
        claim = await self._queue.claim(limit=EMBED_CLAIM_BATCH, max_bytes=MAX_BATCH_BYTES, lane=LANE_EMBED)
        if claim.unavailable:
            return self._retreat()
        if not claim.lane_honored:                 # an old companion answered despite the echo seen before
            await self._queue.unlock([job.queue_id for job in claim.jobs])
            self._lane_supported = False
            return LANE_PARKED
        if not claim.jobs:
            await self._track.keep_the_vector_stock_in_step(self._queue)   # mark, drift, precision swap
            return ROUND_EMPTY
        self._held = {job.queue_id for job in claim.jobs}
        done: list[int] = []
        try:
            for job in claim.jobs:
                if not self._gate_open():         # economy arrived mid claim: stop after this row
                    break
                await self._track.embed_row(job, done)
        except (sqlite3.Error, DiskTight):
            await self._queue.unlock(sorted(self._held))   # refund, never a verdict (DI-05-23)
            self._held.clear()
            return ROUND_PAUSED
        rest = sorted(self._held - set(done))
        await self._queue.acknowledge(done, {}, {})
        await self._queue.unlock(rest)                     # rows not reached go back unjudged
        self._held.clear()
        return ROUND_WORKED
```
(Skizze: `acknowledge` nimmt Queue-IDs; `done` enthält Queue-IDs wie heute in `_embed_the_body`, `poller.py:1319-1372`.)

### Idle-Guard
```python
# Source: embed/model.py:634-675, Erweiterung nach 23-REVIEW WR-02 (deferred)
def release(self, *, idle_seconds: float | None = None) -> bool:
    global _UNLOAD_COUNT
    with self._lock:
        if self._engine is None or self._in_flight:
            return False
        if idle_seconds is not None:
            stamp = self._last_use
            if stamp is not None and time.monotonic() - stamp < idle_seconds:
                return False              # used since the caller's last reading
        self._engine = None
        _UNLOAD_COUNT += 1
    _return_free_pages_to_the_system()
    return True
```

### fp32-Strom mit Digest und Deckel
```python
# Source: Muster nc/client.py:221-254; Datei-Seite in embed/weights.py
async def fetch_release_asset(url: str, sink: IO[bytes], *, cap: int) -> str:
    """Stream one release asset into the sink and return its sha256. GET only, no credential."""
    digest = hashlib.sha256()
    written = 0
    async with httpx.AsyncClient(follow_redirects=True, max_redirects=3, timeout=_timeout()) as client:
        async with client.stream("GET", url) as response:
            if response.url.host not in _ASSET_HOSTS or response.url.scheme != "https":
                raise AssetRefused
            response.raise_for_status()
            async for chunk in response.aiter_bytes(CHUNK_SIZE):
                written += len(chunk)
                if written > cap:
                    raise AssetRefused
                digest.update(chunk)
                await asyncio.to_thread(sink.write, chunk)
    return digest.hexdigest()
```

## Validierungs- und Teststrategie (Fokusfrage 9)

`workflow.nyquist_validation` ist `false` (`.planning/config.json`), daher kein formaler Validation-Architecture-Abschnitt; die Teststrategie folgt trotzdem, weil die Success Criteria Nachweise verlangen.

| Framework | Wert |
|---|---|
| Python | pytest mit `asyncio_mode = "auto"` (`backend/pyproject.toml`), Aufruf `uv run pytest -q`; Einzeltest `uv run pytest -q tests/test_embedding_runner.py -x` |
| PHP | PHPUnit nur in CI (`.github/workflows/php.yml`), lokal kein PHP (verifiziert: `php` fehlt) |
| Linux-CI | Job `gates` auf `ubuntu-24.04` (`python.yml:94-175`), öffentliche Runner mit 4 vCPU [CITED: Vorarbeit 1.4, docs.github.com]; arm64 nur per Dispatch/Schedule |

| Nr. | Nachweis | Art | Datei (neu = Wave-Lücke) |
|---|---|---|---|
| T1 | Sparsam: OCR- und Einbettungsintervalle überlappen nie (Recorder mit Start/Ende je Zeile; gemischter Anspruch ocr+embed; Runner-Task läuft mit, parkt) | Einheit, plattformunabhängig | `tests/test_embedding_runner.py` (neu) |
| T2 | Standard: Überlappung deterministisch (Fake-OCR blockiert, bis der Fake-Embedder "gestartet" meldet; Zeitdeckel = Fehlschlag) | Einheit, plattformunabhängig | dieselbe Datei |
| T3 | Linux-CI, >= 2 Kerne: echte CPU-Arbeit in beiden Spuren (OCR-Fake als Kindprozess mit CPU-Schleife, Einbettung als CPU-Last im Thread); Überlappung der Intervalle und Summe CPU-Zeit > Wandzeit | `skipif(sys.platform != "linux" or os.process_cpu_count() < 2)` | dieselbe Datei |
| T4 | Wechsel Standard → economy mitten in einer Runner-Runde: ab dem Wechsel keine Überlappung, Rest des Anspruchs per `unlock` zurück | Einheit | dieselbe Datei |
| T5 | RAM-Bedingung: reine Funktion mit Fake-cgroup (`memory.max`, `memory.stat anon`) und Fake-meminfo; Nein → Parken mit Grund, Hauptschleife bettet inline | Einheit | `tests/test_memory_guard.py` (neu) |
| T6 | Kill nach Anspruch vor `replace_chunks`, Kill nach `replace_chunks` vor Quittung, Kill in beiden Spuren: nach Ablauf der Sperrfrist (Fake-Queue modelliert Ablauf) steht jede Datei einmal im Index und hat genau einen Chunksatz | Einheit/Integration mit echter state.db und vectors.db | `tests/test_embedding_runner.py` |
| T7 | Zwei Schreibverbindungen: eine hält `BEGIN IMMEDIATE` 200 ms, die andere schreibt erfolgreich nach Wartezeit; injizierter `OperationalError` im Runner → `unlock`, kein Verdikt | Einheit | `tests/test_store_repo.py` bzw. Runner-Test |
| T8 | Alter Companion: Antwort ohne Echo → Runner gibt alles per `unlock` zurück und parkt; Hauptschleife bettet inline | Einheit | Runner-Test |
| T9 | Präzision: Drift in beide Richtungen mit echtem Präzisionswechsel, Marke aus der aktiven Präzision; Startzustand fp32 bei Aussetzer ohne `forget_all`; Download scheitert → int8 bleibt, kein `forget_all`; falscher Digest → Verdikt; Sideload mit richtigem Digest → kein Netz; Rückweg löscht Datei | Einheit mit `httpx.MockTransport` | `tests/test_precision.py`, `tests/test_weights.py` (neu) |
| T10 | Idle-Guard: Nutzung zwischen zweiter Lesung und `release()` → False | Einheit | `tests/test_embed_engine.py` |
| T11 | PHP: `lane` geschlossen, 400 bei Unbekanntem, Echo in jeder Antwort, `embed`-Spur liefert nur embed, `index` nie embed; `precision` in der Profilantwort, 500 ohne Werte | PHPUnit | `php/tests/Unit/QueueServiceTest.php`, `ProfileControllerTest.php` |
| T12 | Paritäten: `LANES` PHP/Python, `PRECISIONS` PHP/Python (textuell wie `test_profile_wire.py`), `KIND_BATCH`/`LOCK_TIMEOUTS` unverändert grün | Einheit | `tests/test_profile_wire.py`, `tests/test_config.py` |
| T13 | Ohne fp32-Wunsch: kein Digest gerechnet, kein Download-Modul importiert, Sparsam-Pin (`test_config.py:312-320`, INDEX_WORKERS) grün, Draht ohne `lane` bytegleich | Einheit | bestehende plus neue Asserts |

**Bestehende Gates, die grün bleiben müssen:** `test_config.py:312-320` (INDEX_WORKERS = 1, kein Knopf), `test_config.py:560-600` (KIND_BATCH/LOCK_TIMEOUTS-Parität, Einbettungsanspruch unter Sperrfrist), `test_info_xml_defaults.py` (keine neue Env-Variable nötig), `test_readonly_gate.py:578-591` (genau vier Schreibpfade; `lane` ist ein GET-Parameter), `test_php_trust_boundary.py` (keine neue Route), `test_store_metadata.py` (RESIDENT_FIGURE), `test_upgrade_compatibility.py` (int8-Marke), `test_measurement_scripts.py` (Baum-Hashes, Pitfall 10).

## Plan-Schnitt-Vorschlag (Wellen)

Serielle Sicherheitsbedingungen: (1) Kein Runner vor dem Track-Eigentümer mit eigenen Verbindungen. (2) Kein Präzisionstausch vor dem Track-Eigentümer. (3) Kein fp32-Download-Auslöser vor dem lokalen Startzustand. (4) Companion-Änderung und Container-Draht im Gleichstand (K6), aber der Container läuft mit beiden Companions.

| Welle | Plan | Inhalt | Abhängig von | Parallel mit |
|---|---|---|---|---|
| 0 | 25-01 | fp32-Laufzeitspeicher messen: im lokalen Abbild `:dev` (Docker vorhanden) Session auf int8 und fp32 laden, `RssAnon`-Sprung je drei Läufe, Einbettungsrate; Rohdaten nach `docs/measurements/2026-09-fp32-speicher/`; ergibt `FP32_EXTRA_BYTES` | , | 25-02, 25-03 |
| 0 | 25-02 | Idle-Guard `release(idle_seconds)` + Freigabe-Task-Test; IN-02 `weights` ohne Default (Aufrufer übergeben vorerst `WEIGHTS_INT8` ausdrücklich) | , | 25-01, 25-03 |
| 1 | 25-03 | PHP: `lane` (geschlossen, Echo, 400), `model_precision` in Settings + Profilantwort, PHPUnit; Python-Draht: `claim(lane=)`, `ClaimResult.lane_honored`, Präzisionsfeld lesen, alle Fakes, Paritätstests | , | 25-01, 25-02 (andere Dateien; Baum-Hash nach Merge neu messen) |
| 2 | 25-04 | Refactor verhaltensgleich: `EmbeddingTrack` aus `Poller` ziehen, `stored_body` als Funktion, Plattenboden-Helfer, eigene Verbindungen (in Tests injizierbar), Markenschritt im Track; alle bestehenden Tests grün | 25-02 | 25-05 |
| 2 | 25-05 | fp32-Beschaffung als Baustein: `embed/weights.py` (Pfad, Digest, atomar, Aufräumen, Löschen), `fetch_release_asset` in `nc/client.py`, `precision.py` Zustandsautomat (ohne Verdrahtung in den Track), `memory_guard.py` reine Funktionen; Checkpoint: Owner lädt Asset hoch und macht das Release unveränderlich | 25-01 (Konstante), 25-03 (Präzisionswert) | 25-04 |
| 3 | 25-06 | `EmbedRunner` + Lifespan (zweiter Task, stand_down/arm beide, Abbau mit `unlock_held`, Freigabe-Task fragt Track) + Spurentscheid der Hauptschleife + RAM-Bedingung verdrahtet + Tests T1 bis T8 | 25-03, 25-04, 25-05 | , |
| 4 | 25-07 | Präzision verdrahtet: Startzustand, Auslöser, Engine-Tausch an der Spurgrenze, Rückweg mit Löschen, Slotformel mit fp32-Mehrbedarf, Marke aus aktiv an beiden Stellen, Tests T9 | 25-06 | 25-08 teilweise |
| 4 | 25-08 | Status (`ModelReport`, `LaneReport`, `_of()`), PHP-Durchreichung in `AdminViewService::backend()`, Doku (`docs/embeddings.md` §8, `docs/profiles.md`, `docs/admin-page.md`, Offline-Weg mit Pfad und `docker cp`-Beispiel), IN-03 | 25-06 (Lane), 25-07 (Model-Felder) | nach 25-07 zusammenführen |

Wenn der Planer weniger Pläne will: 25-01 und 25-02 zusammen, 25-07 und 25-08 zusammen. 25-04 nicht mit 25-06 zusammenlegen: der verhaltensgleiche Refactor soll für sich grün sein, bevor Nebenläufigkeit dazukommt.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Einbettung als Zweig der seriellen Schleife (IDX-08 als Architektur) | IDX-08 als Sparsam-Regel plus RAM-Bedingung | v1.4 (PAR-04) | eigener Nebenläufer, gemessener Lohn bis +41 % der ersten Spur zurück (`docs/embeddings.md:571`) |
| Release-Assets veränderlich, Tag verschiebbar | Unveränderliche Releases mit Attestation | GitHub, 2025 [CITED] | fester Digest im Code plus gesperrtes Asset |
| `EmbeddingModel.release()` prüft nur `_in_flight` | zusätzlich Idle-Uhr unter der Modellsperre | diese Phase | TOCTOU WR-02 vollständig zu |

**Deprecated/outdated:**
- Kommentar `embed/model.py:326-332` ("IDX-08 keeps the two apart in time and not in space"): in Standard/Leistung nicht mehr wahr; mit Verweis auf PAR-04 nachtragen.
- `LOCK_TIMEOUTS[embed]`-Begründung (`QueueMapper.php:114-133`, "embed row travels in the same claim as OCR"): gilt nur noch für die Spur `all`; Kommentar ergänzen, Wert bleibt.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | fp32-Laufzeitspeicher ist ungemessen; der int8-Sprung liegt bei +391,9 MB für eine 118-MB-Datei, fp32 also vermutlich deutlich mehr als +352 MB | Pattern 8f, Plan 25-01 | Slotformel und RAM-Bedingung zu optimistisch; Wave 0 misst |
| A2 | Zwei SQLite-Schreibverbindungen erreichen den `busy_timeout` von 10 s nie (Millisekunden-Transaktionen) | Pattern 6 | seltene `database is locked`; durch Pitfall-3-Behandlung ohne Verdikt abgefangen |
| A3 | PHP reduziert `kinds=a&kinds=b` auf den letzten Wert | Pattern 1 | nur relevant, falls doch eine Liste gewählt wird |
| A4 | Tokenizer- und Chunker-Aufrufe sind nicht threadsicher genug für zwei Slots ohne Sperre | Pattern 3 | Slots=2 ohne Sperre gäbe seltene Fehler; mit Sperre nur weniger Parallelität |
| A5 | Die parallele Zusatzlast der Einbettung ist im Kern die Aktivierung (+26,4 MB), weil `MAIN_PROCESS_BASELINE_BYTES` Gewichte und Cutter enthält | Pattern 4 | RAM-Bedingung zu lax; Phase 28 misst am Produkt |
| A6 | GitHub leitet Release-Downloads dauerhaft auf `release-assets.githubusercontent.com` um (heute verifiziert, Host kann wechseln) | Pattern 8c | Host-Allowlist blockiert; Verdikt D-25-04, Offline-Weg bleibt |
| A7 | Ein geöffnetes oder gemapptes ONNX-Modell darf auf Linux gelöscht werden, ohne die laufende Session zu stören | Pattern 8e | Löschen erst nach Freigabe der alten Engine, was der Plan ohnehin vorsieht |

## Open Questions

1. **Adminseite: Text schon in Phase 25?**
   - What we know: SC4 und D-25-08 verlangen, dass die Adminseite Präzision und Fortschritt zeigt; die Discretion sagt "Seitentexte in den Sprachkatalogen erst mit Phase 27". Die Seite zeigt heute bereits den Anteil "auffindbar nach Bedeutung" (`AdminViewService.php:1379-1400`), der während des Reindex fällt und steigt.
   - What's unclear: ob eine sichtbare Zeile "Modell fp32, Neueinbettung 42 %" mit neuen Katalogtexten (16 Dateien, Katalog-Gates) in Phase 25 gehört.
   - Recommendation: Phase 25 liefert Statusfelder und die PHP-Durchreichung; die bestehende Anteilszahl trägt den Fortschritt sichtbar. Die Zeile mit dem Modellnamen kommt mit Phase 27. Vor dem Plan dem Owner kurz bestätigen lassen, weil SC4 wörtlich "Adminseite zeigt" sagt.
2. **RAM-Bedingung nicht erfüllt: seriell weiter oder Zeilen warten?**
   - Recommendation: seriell weiter (Runner parkt, Hauptschleife bettet inline), weil sonst eine knappe Box nie semantisch gefüllt wird. Entspricht "die Einbettungsspur wartet"; Owner-Bestätigung sinnvoll.
3. **`embed_slots = 2` in Leistung schon jetzt ehren?**
   - Recommendation: ja, mit Semaphore und zwei Track-internen Sperren (Chunker, Vektor-Schreiben); sonst meldet der Status einen Wert, den der Betrieb nicht hält. Alternative: Runner fest 1 und `PROFILE_PERFORMANCE_EMBED_SLOTS` auf 1 (kein Owner-Wert laut D-24-03).
4. **Was ist die "erneute Admin-Aktion" für einen neuen fp32-Versuch?**
   - What we know: Mit occ gibt es nur einen Schlüssel; derselbe Wert zweimal ist nicht unterscheidbar.
   - Recommendation: Übergang int8 → fp32, in diesem Prozess beobachtet (einmal `int8`, dann wieder `fp32` setzen). Erstes Lesen nach dem Start lädt nie. Im Verdikt und in der Doku genau so benennen; ab Phase 27 kann ein Knopf ein Anforderungszeichen schreiben.
5. **Proxy-Netze:** `HTTPS_PROXY` ist über AppAPI nicht setzbar, weil nicht in `info.xml` deklariert. Deklarieren (neue Store-sichtbare Variable, Gleichstandstest `test_info_xml_defaults.py`) oder Offline-Weg als Antwort?
   - Recommendation: Offline-Weg (D-25-06) ist die Antwort für abgeschottete Netze; keine neue Variable in Phase 25, Frage für Phase 29 (Härtung) notieren.
6. **fp32 aktiv und Admin wählt Profil economy:** D-25-01 ("in Sparsam nie wählbar") gegen D-25-03 ("wechselt nie automatisch").
   - Recommendation: ein neuer fp32-Wunsch unter economy wird nicht beschafft; ein bereits aktives fp32 bleibt, bis der Präzisionsschlüssel auf int8 steht (kein impliziter Reindex über den Profilschlüssel). Owner-Bestätigung, weil es zwei Owner-Entscheide gegeneinander auslegt.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | Gates, Tests | ✓ | 0.11.7 | , |
| Docker | Wave-0-Messung fp32-Speicher | ✓ | 29.5.2, Abbild `ghcr.io/street1983nk/findling_backend:dev` lokal | CI `measure.yml` |
| PHP lokal | PHPUnit | ✗ | , | CI `php.yml` |
| gh CLI | Release-Asset (Owner) | ✓ | 2.92.0 | Web-Oberfläche |
| Netz zu huggingface.co | Wave 0 (fp32-Datei für die Messung beschaffen) | ✓ (heute abgefragt) | , | , |
| Linux mit >= 2 Kernen | T3 | ✗ lokal (Windows), ✓ CI `ubuntu-24.04` | 4 vCPU | T1/T2 plattformunabhängig |

**Missing dependencies with no fallback:** keine.
**Missing dependencies with fallback:** PHP lokal (CI), Linux-Mehrkern lokal (CI).

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein | AppAPI-Signatur bleibt Credential; der fp32-Client trägt bewusst keine |
| V4 Access Control | ja | `lane` und `precision` nur über bestehende ExApp-Routen mit `rejectForeignCaller` zuerst (Gate B); `/status` bleibt ADMIN |
| V5 Input Validation | ja | `lane` und `model_precision` als geschlossene Mengen beidseitig; unbekannte `lane` → 400 ohne Wert im Log |
| V6 Cryptography | ja | sha256 aus hashlib, fester Digest im Code, nie selbst gebaut |
| V10 Malicious Code / Supply Chain | ja | ein Asset, eine Quelle, unveränderliches Release, Digest vor Nutzung, Größendeckel, Host-Allowlist bei Umleitung |
| V12 Files and Resources | ja | Ablage nur unter `APP_PERSISTENT_STORAGE`, fester Name, `.part` + `os.replace`, Platz vorher prüfen |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Manipuliertes Modell (Asset getauscht, MITM, Proxy) | Tampering | sha256 fest im Code, Prüfung beim Strom und vor jeder Nutzung, falscher Digest = Verdikt, Datei verworfen |
| Umleitung auf fremden Host | Tampering / Information Disclosure | Host-Allowlist, nur https, keine Zugangsdaten am Client |
| Platte volllaufen durch überlangen Strom | DoS | Größendeckel `FP32_BYTES`, Platzprüfung vorher |
| Fremde ExApp beansprucht Einbettungszeilen | Spoofing | `rejectForeignCaller` bleibt erste Anweisung |
| occ-Tippfehler im Präzisionsschlüssel | Tampering | Leser validiert, Default int8, Zähler ohne Wert |
| Telemetrie durch den Download | Information Disclosure | nur ein GET auf eine feste URL, nur auf Admin-Aktion, keine Kennung im Request |
| Speichererschöpfung durch parallele Spitzen | DoS | RAM-Bedingung, Sparsam wörtlich seriell |
| Zeilen enden als `failed(repeatedly_stuck)` | DoS (Integrität des Status) | `_abort`-Semantik bei SQLite-Fehlern im Runner |

## Sources

### Primary (HIGH confidence)
- Quelltext Findling, gelesen 28.09.2026: `worker/poller.py` (1-2438), `nc/queue.py` (1-565), `nc/client.py` (1-506), `embed/engine.py` (1-619), `embed/model.py` (1-724), `store/repo.py` (560-820, 1530-1622), `store/vectors.py` (95-112, 271-315, 370-480), `index/writer.py` (134-467), `index/open.py` (143-199), `profile.py`, `hardware.py`, `config.py` (630-920, 1210-1262, 1395-1415), `api/status.py` (100-609), `api/resources.py` (180-360, 855-915), `main.py` (170-500, 740-960), `backend/Dockerfile` (96-161)
- PHP: `php/lib/Controller/QueueController.php`, `php/lib/Service/QueueService.php` (1-420), `php/lib/Db/QueueMapper.php` (1-850), `php/lib/Controller/ProfileController.php`, `php/lib/Service/SettingsService.php` (80-110, 255-290)
- Tests: `test_readonly_gate.py` (1-375), `test_config.py` (290-600), `test_measurement_scripts.py` (Pins 431-443, 670-671, 1285-1286), `test_queue_client.py:159`, `test_profile_wire.py`, `test_php_trust_boundary.py:297-316`; `.github/workflows/python.yml` (90-190)
- [nextcloud/server stable33 Dispatcher.php](https://raw.githubusercontent.com/nextcloud/server/stable33/lib/private/AppFramework/Http/Dispatcher.php): nur deklarierte Parameter werden gebunden
- [HuggingFace API, intfloat/multilingual-e5-small, tree onnx @ 614241f](https://huggingface.co/api/models/intfloat/multilingual-e5-small/tree/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx): model.onnx 470.268.510 Byte, sha256 ca456c06...
- Eigene Probe: `curl -sI` auf einen GitHub-Release-Download, 302 nach `release-assets.githubusercontent.com`
- Planungsdokumente: 25-CONTEXT.md, 24-CONTEXT.md, 24-RESEARCH.md, 24-REVIEW.md (IN-02, IN-03, WR-02), 24-SECURITY.md, BL-F04-vorarbeit-2026-09-25.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, `docs/embeddings.md` (560-711)

### Secondary (MEDIUM confidence)
- [HTTPX Environment Variables](https://www.python-httpx.org/environment_variables/): Proxy- und SSL-Variablen, `trust_env` standardmäßig an
- [GitHub Docs: Immutable releases](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/immutable-releases): Tag und Assets gesperrt, Release-Attestation
- [GitHub Docs: About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases): Asset unter 2 GiB

### Tertiary (LOW confidence)
- PHP-Verhalten bei wiederholten Query-Schlüsseln (Trainingswissen, A3)
- fp32-Laufzeitspeicher (ungemessen, A1)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, keine neuen Abhängigkeiten
- Architecture: MEDIUM-HIGH, alle Grenzen im Code belegt; der Entwurf (Track, Runner, Sperre, Parken) ist abgeleitet, nicht gebaut
- Pitfalls: HIGH für 1 bis 5, 9, 10, 12 (Code/Quelle verifiziert), MEDIUM für 6, 7, 8, 11 (Auslegung bzw. Umgebung)
- fp32-Artefakt: HIGH (Größe und Digest gegen HF-API und Dockerfile); fp32-Speicher: LOW (Wave 0)

**Research date:** 2026-09-28
**Valid until:** rund 30 Tage oder bis ein Plan `poller.py`, `QueueService.php` oder `embed/engine.py` ändert; GitHub-Umleitungshost bei jedem Release-Upload gegenprüfen
