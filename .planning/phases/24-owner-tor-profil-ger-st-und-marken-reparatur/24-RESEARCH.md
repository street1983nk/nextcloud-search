# Phase 24: Owner-Tor, Profil-Gerüst und Marken-Reparatur - Research

**Researched:** 2026-09-27
**Domain:** Konfigurationsschichtung (Python, lru_cache), OCS-Route im PHP-Companion, AppAPI-Umgebungsmechanik, cgroup-v2-Hardwareerkennung, Vektor-Marke `embedding_version`
**Confidence:** HIGH für Codebefunde und AppAPI-Mechanik (Quelltext gelesen, cgroup im Findling-Abbild gemessen), MEDIUM für Formelkonstanten (gemessen, aber aus Einzelanfahrt)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Owner-Tor vollzogen am 27.09.2026.** Alle drei Tor-Entscheide (Success Criterion 1) sind gefallen; ab jetzt darf Code geschrieben werden, der Profilweg, Anteile und Lieferweg berührt.

#### Profil-Weg in den Container (Owner-Tor Teil 1, PROF-03)
- **D-24-01 (Owner, 27.09.2026):** Weg B aus der Vorgänger-Research 6.4: Die PHP-Seite bekommt eine OCS-Route (Muster `queues/documents/stats`), der Container fragt das Profil einmal je Runde ab. Live-Wechsel ohne Container-Neustart; die Adminseite speichert das Profil PHP-seitig (appconfig). Der `config.settings()`-lru_cache muss dafür geschichtet werden (statische Werte vs. Profilwerte). Weg A (Umgebungsvariable, Neustart) und Weg C (Datei im Persistenzpfad) sind verworfen.
- **D-24-02 (Owner, 27.09.2026):** Fehlersemantik der Profilabfrage: Der Container merkt sich das zuletzt erfolgreich gelesene Profil für die laufende Prozesslebensdauer; war noch nie eines lesbar (Erststart, Companion ohne Route), läuft Sparsam. Kein Flattern bei kurzen Gateway-Aussetzern, fail-safe beim Erststart.
- Bereits gelockt (REQUIREMENTS PROF-03): Eine gesetzte Umgebungsvariable überstimmt das Profil sichtbar (eine Wahrheit).

#### Anteile und Store-Satz (Owner-Tor Teil 2, PROF-01)
- **D-24-03 (Owner, 27.09.2026):** Anteile nach Research-Vorschlag 3.2: Standard = 50 % der Kerne / 40 % des Speichers, OCR-Obergrenze 4 Slots; Leistung = Kerne minus 1 / 60 % des Speichers, OCR-Obergrenze 16 Slots. Sparsam bleibt fest 1 Slot ohne Anteile (gepinnt). Slotzahl nach der Regel aus Vorarbeit 3.1: `OCR-Slots = max(1, min(floor(Anteil_Kerne x C - r), floor((M_frei - Grundlinie - Reserve) / Kosten_je_Slot)))`.
- **D-24-04 (Owner, 27.09.2026, WÖRTLICH für den 1.4.0-Store-Text):** "Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware hat, gibt per Profil höchstens die Hälfte der Box frei (Profil Standard) oder alles bis auf einen Kern (Profil Leistung)." Dieser Satz reist mit Release 1.4.0 (REL-04) und wird nicht umformuliert.

#### fp32-Lieferweg (Owner-Tor Teil 3, MOD-02/K7)
- **D-24-05 (Owner, 27.09.2026):** Nachladen bei Opt-in. int8 bleibt wie heute ins Abbild gebacken (Zero-Config unverändert, kein +352 MB für alle). fp32 wird erst geladen, wenn der Admin es ausdrücklich wählt: Download ins persistente Verzeichnis mit Digest-Prüfung, klares Verdikt bei Offline/Proxy ("fp32 nicht verfügbar, int8 bleibt aktiv"). Die Regel "Modell ins Image backen, kein Download beim Start" (CLAUDE.md) bleibt gewahrt: der START lädt weiterhin nichts, nur die ausdrückliche Admin-Aktion lädt. K7-Neuprüfungs-Vorbehalt der Nicht-Spaltung wird nicht berührt. (Der Bau des Nachladewegs selbst liegt in Phase 25/MOD-02; Phase 24 legt nur den Weg fest und baut die Marke.)

#### Vorschlags-Schwellen und Rückstufung (HW-01)
- **D-24-06 (Owner, 27.09.2026):** Vorschlags-Schwellen nach Research 3.2: Standard wird ab 6 GB und 3 Kernen vorgeschlagen, Leistung ab 12 GB und 6 Kernen, darunter Sparsam. Nur Vorschlag über die Statusroute, nie automatisches Hochschalten.
- **D-24-07 (Owner, 27.09.2026):** Bei Hardware-Schrumpfung bleibt das GESPEICHERTE Profil stehen; der Container arbeitet selbsttätig auf der größten noch passenden Stufe und meldet beides (gewählt vs. wirksam) über die Statusroute an die Seite. Wächst die Hardware wieder, gilt ohne Zutun wieder das gewählte Profil. Kein stilles Umschreiben von Admin-Entscheidungen.

### Claude's Discretion
- Download-Quelle und Signatur-/Digest-Mechanik des fp32-Nachladens (Researcher prüft; Festlegung spätestens im Phase-25-Plan, Phase 24 dokumentiert den Entscheid nur).
- Technischer Schnitt der lru_cache-Schichtung in `config.py` (statisch vs. profilabhängig) und die genaue Form der OCS-Route.
- Form der Marken-Erweiterung in `store/vectors.py` (heute `model/int8/384/tokens`, `vectors.py:273`), solange gilt: alte Marke ohne Präzisionsangabe wird als int8 gelesen und löst KEINEN Reindex aus (Schnittentscheid Roadmap 27.09., verhindert 5-h-Zwangs-Reindex bei allen Beständen).

### Deferred Ideas (OUT OF SCOPE)
- Bau des fp32-Nachladewegs (Download, Digest, Entladen) , Phase 25 (MOD-02); Phase 24 dokumentiert nur den entschiedenen Weg und baut die Marke
- N-Slot-Berechnung wird in Phase 24 nur als Formel + gemeldete Werte gebaut (Success Criterion 2); echte Slots kommen mit Phase 25/26
- idle-Guard `EmbeddingModel.release()` , Mitnahme-Kandidat Phase 25 (steht schon in ROADMAP)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PROF-01 | Drei Profile als Anteils-Formel an erkannten Kernen/Speicher mit Obergrenzen (Slot-Regel 3.1) | Abschnitt "Pattern 2: Profil-Resolver", gemessene Formelkonstanten (r = 0,25, Slot-Kosten rund 235 MiB) in "Formelkonstanten"; Deutungsfrage Leistung-Term in Open Question 1 |
| PROF-02 | Sparsam Default, Wert für Wert gegen heutige Konstanten gepinnt; Store-Zahl wandert nicht | "Pattern 1: Schichtung" (Settings bleibt unangetastet), Pin-Test-Muster `test_config.py:298`, Gate `test_store_metadata.py:356` |
| PROF-03 | Profilweg per Owner-Tor (Weg B); gesetzte Umgebungsvariable überstimmt sichtbar | "Pattern 3: OCS-Route", "Pattern 4: Poller-Abfrage", **Pitfall 1 (AppAPI injiziert jeden deklarierten Default)**, verifiziert im AppAPI-Quelltext |
| HW-01 | cgroup-bewusste Erkennung, Vorschlag ohne Umschalten, Rückfall auf größte passende Stufe | "Pattern 5: Hardware-Erkennung", im Findling-Abbild gemessen (`process_cpu_count` ignoriert `--cpus`), Pitfall 3 (Selbst-Rückstufung durch eigene Modelllast) |
| MOD-01 | Marke trägt Gewichtspräzision; alte Marke = int8, kein Reindex | "Pattern 6: Marke", Präzision nur bei fp32 anhängen (int8-Marke bytegleich), Gold-Ratchet nach `test_upgrade_compatibility.py` |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.13 + uv (lokales System-Python defekt); alle Python-Befehle über `uv run`.
- Qualitätsgates vor jedem Commit lokal grün: ruff-Vollregelsatz (`ruff==0.16.8`, inkl. `ruff format --check`), pyright basic (`pyright==1.1.414`; Memory-Regel: lokal mit `PYRIGHT_PYTHON_FORCE_VERSION=latest` wie CI), vulture (`vulture==2.16`). Executoren bekommen die Gates in den Auftrag.
- Code, Bezeichner, Kommentare Englisch; echte Umlaute nur in deutscher Prosa, nie in Code, Keywords, URLs, YAML. Projektdoku Deutsch, keine Em-/En-Dashes, keine Emojis.
- Security/Privacy: kein Telemetrie-Phoning, Logs nennen Variablennamen, nie Werte (T-02-13/T-02-14); Berechtigungsdurchgriff strikt.
- "Modell ins Image backen, kein Download beim Start" bleibt (D-24-05 bestätigt).
- Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Abschluss fixen.
- Store-Regel: eine Messzahl (730,2 MB), Gate `test_store_metadata.py` (`RESIDENT_FIGURE`) bleibt unverändert.
- GSD-Workflow: Änderungen nur über GSD-Befehle.
- Keine Project Skills vorhanden (`.claude/skills/`, `.agents/skills/` fehlen).

## Summary

Die Phase besteht aus fünf fast unabhängigen Bausteinen, die sich an drei Stellen berühren: dem neuen neutralen Profil-Zustand (gelesen von Poller und Statusroute), der Statusroute (Payload-Erweiterung) und dem PHP-Companion (eine neue ExApp-Route plus ein Leser in `SettingsService`). Der wichtigste nicht offensichtliche Befund betrifft PROF-03: **AppAPI setzt jede in `info.xml` deklarierte Umgebungsvariable mit ihrem `<default>` in den Container** (`ExAppEnvVarsHelper::normalizeAndValidate`, `'value' => $default`, gleich in stable32/33/main) und speichert diese vollständige Liste als Deploy-Option, die bei jedem Update erneut angewendet wird. "Die Variable ist gesetzt" ist also für jede deklarierte Variable IMMER wahr. Eine naive Regel "gesetzt überstimmt Profil" würde z. B. `FINDLING_OCR_MAX_PAGES=30` jedes Profil überstimmen lassen. Die tragfähige Regel lautet: **eine Umgebungsvariable überstimmt, wenn ihr gültiger Wert vom deklarierten Default abweicht**; dazu gehört ein neuer Gleichstandstest `info.xml`-Default gegen `config.py`-Konstante.

Für die lru_cache-Schichtung (Research-Flag Kern) ist der beste Schnitt, `settings()` **gar nicht anzufassen**: 96 Aufrufstellen, der `hasattr(settings(), "index_workers")`-Test und die im `spawn`-Kind neu aufgelösten Settings (`extract/sandbox.py:59`) sprechen dagegen, Profilwerte in `Settings` zu legen. Stattdessen entsteht ein neutrales Modul (z. B. `findling/profile.py` plus `findling/hardware.py`, importierbar von `worker` und `api`, weil `worker` nichts aus `api` importieren darf) mit einem Prozess-Zustand: Hardware einmal beim Start (Lifespan, vor jedem Modellladen), gewähltes Profil je Runde vom Poller, beides als unveränderliche Momentaufnahme. Phase 24 verdrahtet KEINEN Profilwert in den Betrieb; sie rechnet und meldet. Damit ist der Sparsam-Pin trivial grün und die Store-Zahl kann nicht wandern.

Für MOD-01 ist die sicherste Form: `embedding_mark()` bekommt einen Präzisionsparameter und liefert **für int8 exakt die heutige Zeichenkette** (`multilingual-e5-small/int8/384/1024`), nur fp32 hängt einen fünften Teil an. Weil der Poller (`poller.py:2108`, `stored != wanted`) und die Leseseite (`resources.py:265`) die Marke per exaktem Stringvergleich prüfen, ist "alte Marke = int8, kein Reindex" dann eine Eigenschaft der Konstruktion statt einer Normalisierungslogik an zwei Stellen. Die cgroup-Erkennung ist im Findling-Abbild gemessen: `os.process_cpu_count()` folgt `--cpuset-cpus`, ignoriert aber `--cpus` (12 statt 1,5), `/proc/meminfo` zeigt im Container den Host, AppAPI-Daemons haben per Default kein `resourceLimits` (A9 bestätigt, zusätzlich belegt durch `runbook-messbox.md:410`).

**Primary recommendation:** `settings()` unverändert lassen; neues neutrales Profil-/Hardware-Modul mit injizierbaren Pfaden; OCS-Route `GET /profile` in eigenem `ProfileController` nach Gate-B-Muster; Überstimmung = "gültig und abweichend vom deklarierten Default"; Marke int8 bytegleich, fp32 mit Suffix.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Profil speichern (appconfig) | PHP-Companion (`SettingsService`) | occ `config:app:set` als Zweitzugang in Phase 24 | D-24-01: Adminseite speichert PHP-seitig; Settings-UI kommt erst Phase 27 |
| Profil ausliefern | PHP-Companion (OCS-Route, ExApp-geschützt) | , | Container zieht (Backpressure-Prinzip des Projekts), niemand schiebt |
| Profil je Runde lesen, letztes merken | Container, Poller (`run_once`) über `DocumentQueue` | , | D-24-01/-02; `DocumentQueue.top_up()` ist das Muster für "Route fehlt im alten Companion" |
| Hardware erkennen | Container, Lifespan beim Start | , | nur der Container sieht seine cgroup; einmal vor Modellladen (Pitfall 3) |
| Profilwerte rechnen, Überstimmung auflösen | Container, neutrales Modul | `config.py` (Konstanten, Leser) | eine Wahrheit; `config.py` bleibt Heimat aller Zahlen |
| Melden (erkannt, vorgeschlagen, gewählt, wirksam, Werte) | Container, `GET /status` | PHP `AdminViewService::backend()` erst Phase 27 | ADMIN-Route besteht; UI ist Phase 27 |
| Präzision in der Vektor-Marke | Container, `store/vectors.py` | Poller + `api/resources.py` als Konsumenten | beide vergleichen exakt; Konstruktion statt Normalisierung |

## Standard Stack

Keine neuen Pakete. Alles mit Bordmitteln des bestehenden Stacks:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `os.process_cpu_count` | Python 3.13 (Abbild 3.13.x) | Affinitätsmaske | [VERIFIED: im Findling-Abbild gemessen] folgt cpuset, nicht cpu.max |
| stdlib `pathlib` / `dataclasses(frozen, slots)` / `enum.StrEnum` | 3.13 | cgroup-Dateien, Momentaufnahmen, geschlossene Profilmenge | Hausstil (`Settings` ist `frozen=True, slots=True`) |
| FastAPI/pydantic (bestehend) | wie `uv.lock` | Payload-Erweiterung `StatusResponse` | bestehende Route |
| nc_py_api `nc._session.ocs` (bestehend) | >= 0.30.3 | GET der neuen OCS-Route | Muster `client.py:414` (`queue_stats`) |
| Nextcloud `OCP\IAppConfig` (bestehend) | NC 33 bis 35 | Profil-Ablage | Muster `SettingsService` |

**Installation:** keine.

## Package Legitimacy Audit

Diese Phase installiert keine externen Pakete. slopcheck nicht nötig; Audit entfällt.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
 Admin (Phase 24: occ config:app:set findling profile --value=standard; Phase 27: Settings-UI)
        |
        v
 appconfig findling/profile  --(SettingsService::profile(), geschlossene Menge, sonst Default)--+
                                                                                                |
 Container-Start (Lifespan, to_thread, VOR Modellladen)                                         |
   hardware.detect(/sys/fs/cgroup, /proc/meminfo, process_cpu_count, arch)                      |
        |                                                                                        |
        v                                                                                        v
 +------------------ neutraler Prozess-Zustand (findling/profile.py) ------------------+  GET /ocs/v2.php/apps/findling/profile
 |  hardware (fix je Prozess)                                                          |  (ExAppRequired, rejectForeignCaller)
 |  chosen  (zuletzt erfolgreich gelesen | None = nie)  <-- Poller.run_once je Runde <--+  404/Fehler -> None -> letzter Wert bleibt
 |  suggested = fits(hardware)                                                          |
 |  effective = min(chosen or ECONOMY, fits(hardware))        (D-24-07)                 |
 |  values    = resolve(effective, hardware, environ)  -> je Wert Quelle: profile|env   |
 +------------------------------------------+-------------------------------------------+
                                            |
                          Momentaufnahme lesen (kein Laden, kein Schreiben)
                                            v
                         GET /status (ADMIN) -> StatusResponse.profile {...}
                                            |
                         (Phase 27) PHP AdminViewService::backend() -> Seite

 Phase 24 verdrahtet values NICHT in Poller/Writer/Sandbox. Betrieb bleibt Sparsam-identisch.

 Getrennt davon (MOD-01):
 Poller Leerlauf-Runde -> embedding_mark(model, tokens, weights) == gespeicherte Marke ?
    int8: bytegleich zu heute -> kein Drift -> kein Reindex
    fp32: ".../fp32" -> Drift -> forget_all -> Marke -> Bänder zu 500 (bestehende Kette)
```

### Recommended Project Structure
```
backend/src/findling/
├── config.py            # UNVERÄNDERTES settings(); neue Konstanten (Profilanteile, Schwellen, Formelkonstanten) mit Herleitung
├── hardware.py          # NEU: detect(), Hardware-Momentaufnahme, reine Parser, injizierbare Pfade
├── profile.py           # NEU: Profile (StrEnum), ProfileValues, resolve(), fits(), Prozess-Zustand
├── nc/client.py         # + read_profile(): Pfad als Stringliteral im Aufruf (Gate A)
├── nc/queue.py          # + DocumentQueue.profile(): jede Exception -> None (Muster top_up)
├── worker/poller.py     # + je Runde queue.profile() -> Zustand
├── api/status.py        # + StatusResponse.profile (verschachteltes Modell), in _volume() UND _of()
├── store/vectors.py     # embedding_mark(..., weights=WEIGHTS_INT8)
└── main.py              # Lifespan: Hardware einmal erkennen (vierte Startaussage)
php/lib/
├── Controller/ProfileController.php  # NEU: GET /profile, OCSController, Gate-B-Muster
└── Service/SettingsService.php       # + KEY_PROFILE, profile() mit geschlossener Menge
```

### Pattern 1: Schichtung ohne Eingriff in `settings()`
**What:** `settings()` bleibt `@lru_cache(maxsize=1)` und die statische Schicht (Umgebung plus Konstanten). Profilabhängige Werte leben in einem eigenen, nicht gecachten Accessor, der aus der Zustands-Momentaufnahme rechnet.
**Why (belegt):**
- 96 Aufrufstellen von `settings()` in `src` bleiben unberührt [VERIFIED: grep].
- `test_config.py:305` prüft `not hasattr(settings(), "index_workers")`; Profilfelder in `Settings` würden das Architektur-Tabu verwischen.
- Das Extraktionskind startet per `spawn` (`extract/sandbox.py:59`) und löst `config.settings()` aus der geerbten Umgebung neu auf (`sandbox.py:291`, `ocr.py:119`). Ein live gewechselter Profilwert im Elternprozess erreicht das Kind nie über `settings()`. **Konsequenz für Phase 25/26:** profilabhängige OCR-Werte (`ocr_max_pages`) müssen dem Kind ausdrücklich übergeben werden (Pipe-Argument oder Umgebung beim Spawn). Für Phase 24 nur dokumentieren.
- `conftest.py:400` leert den Settings-Cache; der neue Zustand braucht eine eigene Reset-Funktion für Tests (autouse-Fixture), sonst leckt ein gewähltes Profil in den nächsten Test.

### Pattern 2: Profil-Resolver als reine Funktion
**What:** `resolve(profile, hardware, environ) -> Resolution(values: ProfileValues, sources: Mapping[str, str])`. Reine Funktion, keine I/O; der Zustand ruft sie.
**Werte-Tabelle** (Vorarbeit 3.2, D-24-03): Sparsam = heutige Konstanten; Standard/Leistung nach Anteilsregel. Phase 24 rechnet mindestens `ocr_slots`; die übrigen Zeilen (Text-Slots, onnx-Threads, Writer-Heap/Threads, Batch, `OCR_MAX_PAGES`, Speicherwächter-Reserve) empfiehlt sich als Daten gleich mitzuführen, damit Phase 25/26 nur verdrahten. Sparsam-Zeile wird aus den bestehenden Konstanten gebaut, nicht aus neuen Literalen.
**Sparsam-Pin (PROF-02):** Test nach Muster `test_config.py:298`/`test_defaults_are_the_measured_numbers`: jeder Wert der Sparsam-Zeile gegen das Literal UND gegen die Konstante: `INDEX_WORKERS == 1`, `WRITER_HEAP_BYTES == 50_000_000`, Tantivy `num_threads == 1` (`index/writer.py:176`, `rebuild.py:576`), onnx `THREADS == 2` (`embed/model.py:113`), `EMBED_BATCH_SIZE == 2`, `OCR_MAX_PAGES == 30`, `OCR_DPI == 300`, `OCR_CLAIM_BATCH == 2`, OCR-Slots 1, Text-Slots 1, Einbettung in derselben Schleife.

### Pattern 3: OCS-Route im Companion (Muster `queues/documents/stats`)
**What:** Neuer `ProfileController extends OCSController`, eine Methode `GET /profile`. Attribute voll qualifiziert (Gate B zählt sie textuell), `rejectForeignCaller()` als erste Anweisung.
**Ablage:** `SettingsService::KEY_PROFILE = 'profile'`, `profile(): string` liest `getValueString(Application::APP_ID, KEY_PROFILE, 'economy')` und prüft gegen die geschlossene Menge; Unbekanntes (z. B. occ-Tippfehler) ergibt den Default plus gezählte Warnung ohne Wert (Muster `SettingsService::reject()`). `saveProfile()` gehört in Phase 27; in Phase 24 reicht occ als Weg, denn `SettingsService`-Kommentar (Zeile 262 bis 265) benennt occ bereits als zweiten, ungeprüften Zugang, deshalb validiert der Leser.
**Uninstall:** `AppUninstallStep` löscht per `deleteApp(APP_ID)` alle Schlüssel; kein Zusatz nötig [VERIFIED: `test_uninstall_contract.py:258`].
**Gate B:** `test_php_trust_boundary.py` prüft jede `ApiRoute` automatisch (ExAppRequired, NoCSRFRequired, `rejectForeignCaller` zuerst); Anti-Vakuitäts-Schranke ist `>= 13`, eine Route mehr bricht nichts.

### Pattern 4: Poller liest je Runde, Fehler = letzter Wert
**What:** `DocumentQueue.profile() -> str | None` fängt JEDE Exception (Companion 1.3.x antwortet 404) und loggt auf debug, exakt wie `top_up()` (`nc/queue.py:475-501`). Der Poller ruft es in `run_once` direkt nach `self._open` und VOR `claim`, weil ab Phase 26 die Anspruchsgröße vom Profil abhängt. `None` oder ein Wert außerhalb der geschlossenen Menge ändert den Zustand nicht (D-24-02).
**Latenz:** Nur ein bewaffneter Poller fragt. Leere Runden haben Backoff bis 120 s (`POLL_COOLDOWN_MAX_SECONDS`), eine lange OCR-Runde bis rund 2 x 780 s. Ein Wechsel wird also nach Sekunden bis rund 25 min wirksam; das in der Doku so benennen.
**Read-only-Gate:** GET braucht keinen Eintrag in `OCS_WRITE_ALLOWLIST` (`test_readonly_gate.py:239`, Test `test_write_allowlist_has_exactly_four_entries` bleibt grün), der Pfad muss aber Stringliteral im Aufruf in `client.py` sein.
**Testfakes:** 8 Stellen übergeben `queue_factory=`; Fakes in `test_poller.py` und `test_embedding_track.py` brauchen die neue Methode, sonst endet `run_once` in der Generalausnahme von `run()` und der Test sieht nur "unexpected AttributeError".

### Pattern 5: Hardware-Erkennung, injizierbar und einmal je Start
**What:** `detect(cgroup_root=Path("/sys/fs/cgroup"), meminfo=Path("/proc/meminfo"), cpu_count=os.process_cpu_count, machine=platform.machine) -> Hardware`.
- Kerne `C = min(process_cpu_count(), quota/period)` aus `cpu.max` (`"max 100000"` = keine Quote, `"150000 100000"` = 1,5). Als Gleitkomma behalten, für die Formel und für Schwellen; gemeldet zusätzlich ganzzahlig (mindestens 1).
- Speicher: `memory.max` (`"max"` = keine Grenze). Mit Grenze: `min(memory.max, MemAvailable)`; ohne: `MemAvailable`. `MemTotal` zusätzlich melden.
- cgroup v1 als billiger Rückfall (`cpu/cpu.cfs_quota_us` = -1 unbegrenzt, `memory/memory.limit_in_bytes`, Wert größer `MemTotal` = unbegrenzt) [ASSUMED: v1 auf NC-33-Hosts selten].
- Jede nicht lesbare Datei ergibt "unbekannt" und nie eine Ausnahme (Hausregel "unbrauchbare Eingabe stoppt nie den Container").
- Zeitpunkt: Lifespan in `main.py` als vierte Startaussage per `asyncio.to_thread`, vor Bewaffnung und vor jedem Modellladen (es gibt kein Vorwärmen, D-03/D-08). Ergebnis für die Prozesslebensdauer einfrieren.
**Messung dieser Sitzung** (Findling-Abbild `:dev`, Docker 29.5.2, cgroup v2, `--entrypoint python`):

| docker run | `process_cpu_count` | `cpu.max` | `memory.max` | `/proc/meminfo` MemTotal |
|---|---:|---|---|---|
| ohne Optionen | 12 | `max 100000` | `max` | Host (7,97 GB) |
| `--memory 2g --cpus 1.5` | **12** | `150000 100000` | `2147483648` | **Host**, nicht 2 GiB |
| `--cpuset-cpus 0,1` | **2** | `max 100000` | `max` | Host |

`/proc/self/cgroup` zeigt `0::/`, also privater cgroup-Namensraum: die Dateien liegen direkt in `/sys/fs/cgroup` [VERIFIED].

**Testbarkeit:** Fake-cgroup-Bäume per `tmp_path` (Dateien `cpu.max`, `memory.max`, `meminfo` schreiben) und `cpu_count=lambda: 16` injizieren. Läuft auch auf Windows, weil keine echte `/sys` gelesen wird. Das Muster existiert im Repo (`scripts/ops/ocr_slot_probe.py:71` `CGROUP`, Parameter `root: Path = CGROUP`; `FINDLING_CGROUP_ROOT` in `cpu_sampler.sh`). Simulierte Schrumpfung (Success Criterion 4) = zweiter Fake-Baum mit kleineren Werten, gewähltes Profil Leistung, erwartetes `effective` Standard bzw. Sparsam.

### Pattern 6: Marke mit Präzision, int8 bytegleich
**What:**
```python
WEIGHTS_INT8: Final = "int8"
WEIGHTS_FP32: Final = "fp32"
WEIGHT_PRECISIONS: Final = frozenset({WEIGHTS_INT8, WEIGHTS_FP32})

def embedding_mark(model: str, *, tokens: int, weights: str = WEIGHTS_INT8) -> str:
    base = f"{model}/{ELEMENT_TYPE}/{EMBEDDING_DIMENSIONS}/{tokens}"
    if weights == WEIGHTS_INT8:
        # The mark every installation up to 1.3.x carries, byte for byte: int8 weights are
        # spelled by absence so that an upgrade never sees a drift (MOD-01, no forced re-embed).
        return base
    if weights not in WEIGHT_PRECISIONS:
        raise ValueError("unknown weight precision")
    return f"{base}/{weights}"
```
**Warum so und nicht "immer fünf Teile plus Normalisierung":** Verglichen wird exakt an zwei Stellen (`poller.py:2108`, `resources.py:265` über `store.version_mismatch`). Eine Normalisierung müsste an beiden Stellen und in `Store.version_mismatch` greifen; vergisst eine davon den Fall, entsteht genau der 5-h-Zwangs-Reindex (Poller) oder ein falsches "degraded" (Leseseite). Bytegleichheit macht beides unmöglich.
**Achtung Begriff:** `ELEMENT_TYPE = "int8"` (`vectors.py:87`) ist der Typ der GESPEICHERTEN Vektoren (Quantisierung der Ausgabe per `to_int8`, `embed/model.py:243`), nicht die Gewichtspräzision. Beide Modelle (int8- und fp32-Gewichte) schreiben int8-Vektoren. Der Kommentar in `embedding_mark` ("the quantisation of its output") muss deshalb um die Gewichte ergänzt werden, sonst liest der nächste Leser das vorhandene `int8` als Gewichtsangabe.
**Quelle der Präzision:** In Phase 24 ruft jeder Aufrufer mit `WEIGHTS_INT8` (nur int8 ist gebacken, `MODEL_FILE = "model.onnx"`, `embed/model.py:99`). Ab Phase 25 muss die Präzision aus dem TATSÄCHLICH geladenen Modell kommen, nicht aus dem Wunsch (Verdikt "fp32 nicht verfügbar, int8 bleibt aktiv" darf keine fp32-Marke schreiben).
**Upgrade-Test:** Gold-Ratchet im Stil von `test_upgrade_compatibility.py` ("ein roter Test ist eine Owner-Frage"): `embedding_mark(EMBEDDING_MODEL, tokens=1024) == "multilingual-e5-small/int8/384/1024"`. Verhaltenstest in `test_embedding_track.py`: gespeicherte 1.3-Marke, Poller-Leerlaufrunde, kein `forget_all`, kein Requeue `embed`; Gegenprobe mit fp32-Marke löst die Kette `forget_all -> write mark -> requeue` aus (Kette ist in `test_embedding_track.py:1137` bereits als Muster vorhanden). Die bestehende Zusicherung `test_read_side.py:238` (Wert bytegleich) bleibt unverändert grün und ist selbst ein Beleg.

### Anti-Patterns to Avoid
- **Profilfelder in `Settings` oder zweiter lru_cache um einen Profil-Leser:** friert den Live-Wechsel wieder ein oder bricht das `index_workers`-Tabu.
- **"Variable gesetzt" = `name in os.environ`:** unter AppAPI immer wahr (Pitfall 1).
- **Profil in der Statusroute nachladen:** `status.py` ist ausdrücklich nebenwirkungsfrei ("reading it builds nothing and loads nothing", T-07-04); die Route liest nur die Momentaufnahme.
- **Hardware je Runde neu messen:** `MemAvailable` sinkt durch Findlings eigene Modelllast (Pitfall 3).
- **Normalisierende Markenvergleiche:** siehe Pattern 6.
- **Profilwerte in Phase 24 in Writer/Poller/Sandbox verdrahten:** Scope Phase 25/26, und der Sparsam-Pin würde erst dann aussagekräftig; in Phase 24 nur rechnen und melden.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Zahlen aus Umgebung lesen | neuen Parser | `_bounded_int_from_environment` und Geschwister (`config.py:959`) | Warnungs- und Fallback-Vertrag, Logs ohne Werte |
| "Route fehlt im alten Companion" | eigene Versionsprüfung | Muster `DocumentQueue.top_up()` (jede Exception -> Rückfallwert, debug-Log) | im Upgrade-Fenster erprobt |
| Vektor-Reindex bei Präzisionswechsel | eigene Kette | bestehende Drift-Kette `_answer_the_vector_drift` (`poller.py:2133`) | Reihenfolge leeren, Cursor, Marke ist sicherheitsrelevant und getestet |
| ExApp-Routenschutz | eigene Prüfung | `rejectForeignCaller()` plus Gate B | Gate prüft Reihenfolge textuell |
| Präzisions-Normalisierung | Vergleichsfunktion | bytegleiche int8-Marke | nichts zu vergessen |
| CPU-Zählung | `os.cpu_count()` | `process_cpu_count()` plus `cpu.max`, Minimum | gemessen: `cpu_count` meldet Host |

**Key insight:** Fast alles, was diese Phase braucht, existiert als Muster im Repo; die Risiken liegen in Annahmen über die Umgebung (AppAPI-Defaults, cgroup, eigene Speicherlast), nicht im Code.

## Formelkonstanten (gemessen seit der Vorarbeit)

Die Vorarbeit setzte r und Kosten_je_Slot als ungemessen an. Die v1.3-Anfahrt vom 26.09.2026 hat sie geliefert (`docs/performance.md:4737-4829`):

| Größe | Wert | Quelle |
|---|---|---|
| r (Kernbelegung neben dem Container während OCR) | **0,25** Kerne | B1, m7g.large [VERIFIED: performance.md:4755] |
| Kosten je OCR-Slot | rund **235 MiB** (Sandbox-Kind 136,4 plus tesseract 98,8 MiB) | B2/B3 [VERIFIED: performance.md:4767-4777]; Vorarbeit-Band 200 bis 680 MB bleibt als Vorbehalt (K2), Phase 28 misst am Produkt |
| Grundlinie Hauptprozess | `RssAnon` höchstens 1.257,5 MiB (mit Gewichten, Entladeschalter 0) | B2 [VERIFIED: performance.md:4766] |
| Skalierung OCR-Slots | Faktor 15,86 bei 16 Kernen | B4 [VERIFIED] |
| Reserve | Standard 20 %, Leistung 15 % (Speicherwächter) | Vorarbeit 3.2 [ASSUMED: Vorschlag, keine Messung] |

Beispielrechnung (Standard, D-24-03 wörtlich, r = 0,25): 4 Kerne ergeben `floor(0,5 x 4 - 0,25) = 1` Slot, 5 Kerne 2, 8 Kerne 3, ab 9 Kernen die Obergrenze 4. **Standard bringt also erst ab 5 Kernen mehr als einen OCR-Slot**; das ist gewollt konservativ, sollte aber in der Plan-Doku stehen, damit niemand es für einen Fehler hält.

## Common Pitfalls

### Pitfall 1: AppAPI setzt jeden deklarierten Default als echte Umgebungsvariable
**What goes wrong:** Regel "gesetzte Variable überstimmt Profil" greift immer, Profile wirken für deklarierte Knöpfe nie (heute betroffen: `FINDLING_OCR_MAX_PAGES`, Default 30; Standard/Leistung wollen 100/150).
**Why it happens:** `ExAppEnvVarsHelper::normalizeAndValidate` setzt `'value' => $default` für jede Variable und verwirft nur leere Werte; die volle Liste wird als Deploy-Option gespeichert (`DockerActions.php:106/208`) und bei `app_api:app:update` erneut angewendet. Gleiches Verhalten in stable32 und stable33 (`ExAppService.php:299-323`) [VERIFIED: GitHub-Quelltext nextcloud/app_api]. Folge zusätzlich: Ein späteres Entfernen des `<default>` aus `info.xml` hilft Bestandsinstallationen NICHT, deren gespeicherte Deploy-Option trägt weiter "30".
**How to avoid:** Überstimmung = gültiger Wert UND verschieden vom deklarierten Default. Helfer z. B. `_explicit_int(name, default, bounds) -> int | None` auf Basis der bestehenden Leser (None bei leer, ungültig oder gleich Default). Neuer Gleichstandstest: jeder `<default>` in `backend/appinfo/info.xml` gleich der Konstante in `config.py` (heute existiert kein solcher Test [VERIFIED: grep]).
**Consequence to document:** Ein Admin, der unter Leistung ausdrücklich 30 Seiten will, bekommt 150; er müsste 29 oder 31 setzen. In der `<description>` von `FINDLING_OCR_MAX_PAGES` einen Satz dazu vorsehen (Store-Text-Regel: kurz).
**Warning signs:** Status meldet für alle Werte Quelle `env`, obwohl niemand etwas gesetzt hat.
**Nebenbefund:** Nicht deklarierte Variablen (z. B. `FINDLING_WRITER_HEAP_BYTES`, `FINDLING_EMBED_BATCH_SIZE`) lassen sich über AppAPI gar nicht setzen ("overrides for undeclared names are ignored"), nur per Hand am Docker.

### Pitfall 2: Statusfelder gehen in `_of()` verloren
**What goes wrong:** Neues Feld in `_volume()` gesetzt, aber `_of()` (`status.py:371-435`) baut `StatusResponse` Feld für Feld neu; mit vorhandener state.db verschwindet das Feld still auf Default.
**How to avoid:** Ein verschachteltes Modell `profile: ProfileReport` (ein Übertrag in `_of()`), `FIELDS` in `test_status_endpoint.py:74` erweitern (die Menge wird an zehn Stellen exakt geprüft), und je ein Test für den Zweig ohne und mit state.db.

### Pitfall 3: Selbst verursachte Rückstufung über MemAvailable
**What goes wrong:** Erkennung je Runde oder nach dem ersten Einbetten: die Gewichte (Ladesprung rund 422 MB) und der Tokenizer (rund 544 MB) senken `MemAvailable`, der Container hält sich für geschrumpft und stuft sich zurück; das Profil flattert.
**How to avoid:** Einmal im Lifespan vor jedem Laden messen und einfrieren (HW-01 sagt "beim Start"). "Hardware wächst wieder" (D-24-07) wirkt dann beim nächsten Start; so dokumentieren.

### Pitfall 4: Einheiten der Schwellen
**What goes wrong:** Eine nominelle 8-GB-Box meldet `MemTotal` rund 7,7 GiB und im AIO-Leerlauf `MemAvailable` um 5,5 bis 6 GiB; gegen "6 GB" in GiB gelesen schlägt sie Sparsam vor.
**How to avoid:** Schwellen als Byte-Konstanten mit benannter Einheit in `config.py`; Messgröße für Schwellen festlegen (Open Question 2).

### Pitfall 5: Leistung-Term widerspricht dem Store-Satz
**What goes wrong:** D-24-03 wörtlich: `floor(Anteil_Kerne x C - r)` mit Anteil_Kerne x C = C - 1 ergibt `floor(C - 1,25)` = C - 2 Slots. Der gelockte Store-Satz D-24-04 sagt "alles bis auf einen Kern".
**How to avoid:** Vor dem Bau festhalten, wie der Leistung-Term zu lesen ist (Open Question 1).

### Pitfall 6: Profilwechsel erreicht das Sandbox-Kind nicht
**What goes wrong:** (Phase 25/26) `ocr_max_pages` wird im `spawn`-Kind aus der Umgebung gelesen.
**How to avoid:** In Phase 24 nur dokumentieren (Merker für 25/26); Phase 24 verdrahtet nichts.

### Pitfall 7: Fakes ohne neue Queue-Methode
**What goes wrong:** Poller-Tests werden rot mit "unexpected AttributeError" oder, schlimmer, laufen in einen Pfad, der das Profil stillschweigend nie liest.
**How to avoid:** Alle Fakes in einem Plan anpassen; ein Test, dass ein Fake ohne Route (Exception) den letzten Wert behält und beim Erststart Sparsam liefert.

### Pitfall 8: vulture und ungenutzte Profilwerte
**What goes wrong:** Felder der Wertetabelle, die erst Phase 25/26 liest, meldet vulture als tot.
**How to avoid:** Über die Statusroute ausgeben (dann gelesen) oder bewusst in der vulture-Allowlist mit Begründung; nicht die Gates lockern.

## Code Examples

### cpu.max und memory.max lesen (injizierbar, nie werfend)
```python
# Source: Muster scripts/ops/ocr_slot_probe.py:71-117, Format laut Messung dieser Sitzung
def cpu_quota(root: Path) -> float | None:
    """Cores the cgroup quota allows, None when there is no quota or it cannot be read."""
    try:
        quota, period = (root / "cpu.max").read_text(encoding="ascii").split()
    except (OSError, ValueError):
        return None
    if quota == "max" or not quota.isdigit() or not period.isdigit() or int(period) == 0:
        return None
    return int(quota) / int(period)

def memory_limit(root: Path) -> int | None:
    try:
        raw = (root / "memory.max").read_text(encoding="ascii").strip()
    except OSError:
        return None
    return int(raw) if raw.isdigit() else None  # "max" means no limit

def meminfo_bytes(path: Path, key: str) -> int | None:
    try:
        for line in path.read_text(encoding="ascii").splitlines():
            name, _, rest = line.partition(":")
            if name == key:
                return int(rest.split()[0]) * 1024  # kB in /proc/meminfo
    except (OSError, ValueError, IndexError):
        return None
    return None
```

### Profilabfrage im Queue-Wrapper
```python
# Source: Muster backend/src/findling/nc/queue.py:475-501 (top_up)
async def profile(self) -> str | None:
    """The profile the admin stored, or None when it could not be read.

    A companion older than 1.4.0 answers 404 here; that must cost one debug
    line and leave the last known profile in force (D-24-02), never the poller.
    """
    try:
        answer = await read_profile(self._nc)
    except Exception:
        LOGGER.debug("could not read the profile")
        return None
    value = (_mapping(answer) or {}).get("profile")
    return value if isinstance(value, str) and value in PROFILE_NAMES else None
```

### PHP-Route
```php
// Source: Muster php/lib/Controller/QueueController.php:323-339
#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'GET', url: '/profile')]
public function profile(): DataResponse {
	$foreign = $this->rejectForeignCaller();
	if ($foreign !== null) {
		return $foreign;
	}
	return new DataResponse(['profile' => $this->settingsService->profile()]);
}
```
`rejectForeignCaller()` ist heute `private` in `QueueController`; entweder in den neuen Controller kopieren (Gate B verlangt den Aufruf als erste Anweisung, nicht eine gemeinsame Implementierung) oder in einen Trait ziehen. Kopie ist der kleinere Eingriff in freigegebenen Code.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `os.cpu_count()` im Container | `os.process_cpu_count()` (3.13) plus `cpu.max` | Python 3.13 | `process_cpu_count` sieht nur die Affinität; die Quote bleibt Handarbeit (CPython-Issue #149452 offen) |
| AppAPI ohne Ressourcengrenzen | Daemon-Konfig `resourceLimits` (`memory`, `nanoCPUs`), Default `null` | vorhanden in app_api stable33/34/35 | Grenzen möglich, aber nur wenn der Admin sie am Daemon setzt; `nanoCPUs` erscheint im Container als `cpu.max`-Quote |

## Runtime State Inventory

Keine Umbenennungsphase im engeren Sinn, aber MOD-01 berührt gespeicherten Zustand:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `state.db` meta `embedding_version` = `multilingual-e5-small/int8/384/<tokens>` auf jeder Bestandsinstallation; `vectors.db` | KEINE Migration: int8-Marke bleibt bytegleich (Pattern 6) |
| Live service config | appconfig `findling/profile` neu; bestehende AppAPI-Deploy-Optionen tragen alle deklarierten Defaults | Code-Regel "abweichend vom Default" (Pitfall 1), keine Datenänderung |
| OS-registered state | None, verifiziert: keine Task-/Dienstregistrierung betroffen | none |
| Secrets/env vars | keine neue Variable; `FINDLING_OCR_MAX_PAGES` ändert nur ihre Überstimmungssemantik | Beschreibung in `info.xml` ergänzen |
| Build artifacts | None, das Abbild ändert sich nur um Code | none |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | cgroup v1 ist auf NC-33-Hosts selten, Rückfall reicht billig | Pattern 5 | Erkennung meldet "unbegrenzt" auf v1-Hosts mit Grenze; Vorschlag zu groß, aber nie automatisch geschaltet |
| A2 | HaRP reicht `resource_limits` des Daemons an Docker durch | State of the Art | nur relevant, wenn Admins Grenzen setzen; Erkennung liest ohnehin die cgroup |
| A3 | Reserve 20 %/15 % als Anteil von `Anteil_Speicher x M` | Formelkonstanten | Slotzahl leicht anders; Phase 28 misst |
| A4 | Die Konstante `Kosten_je_Slot = 235 MiB` ist repräsentativ | Formelkonstanten | am oberen Band (680 MB) zu viele Slots gemeldet; Phase 24 meldet nur, verdrahtet nichts |
| A5 | Wire-Namen der Profile englisch (`economy`, `standard`, `performance`) | Pattern 3 | reine Namensfrage; UI-Texte kommen aus Katalogen (Phase 27) |

## Open Questions (RESOLVED)

1. **Leistung-Kernterm: C - 1 oder C - 1 - r?** RESOLVED: Owner-Entscheid D-24-08 (27.09.2026), Empfehlung uebernommen: Leistung `C - 1` ohne r-Abzug, Standard mit r-Abzug.
   - What we know: D-24-03 nennt die Formel mit `- r` und "Kerne minus 1"; wörtlich ergibt das C - 2 Slots. D-24-04 (wörtlicher Store-Satz) verspricht "alles bis auf einen Kern".
   - Recommendation: Für Leistung den Kernterm als `C - 1` lesen (der eine freie Kern deckt das gemessene r = 0,25 ab), für Standard `floor(0,5 x C - r)` wörtlich. Das als datierte Deutung im Plan festhalten und dem Owner kurz zur Bestätigung zeigen, weil es den Store-Satz betrifft.
2. **Messgröße für die Vorschlags-Schwellen (6 GB/12 GB):** RESOLVED: siehe 24-CONTEXT.md Nachentscheid (Research-Empfehlungen uebernommen). `MemAvailable` (wörtlich HW-01) schlägt auf typischen 8-GB-AIO-Boxen eher Sparsam vor; `MemTotal` bzw. `memory.max` trifft das Owner-Bild "Box mit 6 GB".
   - Recommendation: Schwellen gegen `memory.max`, sonst `MemTotal`; Slotformel gegen `min(memory.max, MemAvailable)`. Beide Werte melden. Planer entscheidet, bei Zweifel Owner-Rückfrage.
3. **PHP-Durchreichung der neuen Statusfelder schon in Phase 24?** `AdminViewService::backend()` baut Felder einzeln neu, neue Container-Felder erscheinen dort nicht von selbst.
   - Recommendation: in Phase 27 (UI) mitbauen; Phase 24 liefert nur die Container-Payload, wie die Roadmap sagt.
4. **Upgrade-Nachweis zusätzlich in CI?** Die Store-Upgrade-Schritte in `deploy-harp.yml` prüfen `vectors.db` bytegleich (Schritt 6, Zeile 5135).
   - Recommendation: Unit-Ratchet plus Verhaltenstest reichen für Phase 24; eine CI-Zusicherung "Marke vor und nach Upgrade gleich" in Phase 29 (Härtung) aufnehmen.
5. **fp32-Download-Quelle und Digest (Discretion, Festlegung Phase 25):** Nicht Teil der Bauarbeit hier. Vorbefund: Das Abbild quantisiert int8 aus `onnx/model.onnx` des HF-Repos `intfloat/multilingual-e5-small`, adressiert per Commit (`Dockerfile:97`); dieselbe Datei an derselben Commit-Adresse ist die naheliegende fp32-Quelle mit festem SHA-256 im Code [ASSUMED, in Phase 25 zu prüfen].

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | alle Python-Gates und Tests | ja | 0.11.7 | , |
| Docker (cgroup v2) | optionale Container-Probe der Erkennung | ja | 29.5.2, cgroup v2 | Fake-Bäume in Unit-Tests |
| Findling-Abbild lokal | Probe wie in dieser Sitzung | ja (`findling_backend:dev`, `:1.1.0`) | , | , |
| PHP lokal | PHPUnit der Companion-Route | nein | , | CI-Job `php.yml` (PHPUnit gegen nextcloud/server-Checkout), `php -l` im Container |

**Missing dependencies with no fallback:** keine.
**Missing dependencies with fallback:** PHP lokal (CI führt PHPUnit aus).

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein | AppAPI-Signatur bleibt Credential |
| V3 Session Management | nein | , |
| V4 Access Control | ja | `ExAppRequired` plus `rejectForeignCaller` (Gate B) auf `GET /profile`; `/status` bleibt `access_level ADMIN`; Schreibweg in Phase 24 nur occ (Serverzugang), Admin-FrontpageRoute erst Phase 27 |
| V5 Input Validation | ja | Profilname als geschlossene Menge beidseitig (PHP-Leser und Container); Zahlen über bestehende Bereichsprüfer |
| V6 Cryptography | nein (Phase 24) | fp32-Digest erst Phase 25 |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Fremde ExApp liest/fälscht Profil | Spoofing/Information Disclosure | `rejectForeignCaller`, nur Lesen, Antwort enthält nur den Profilnamen |
| Manipulierter appconfig-Wert (occ) | Tampering | Leser validiert, Unbekanntes = Default, Warnung ohne Wert |
| Hardwaredaten nach außen | Information Disclosure | nur ADMIN-Statusroute, keine Telemetrie (Projektregel) |
| Profil zwingt Box in OOM | Denial of Service | Phase 24 verdrahtet nichts; wirksam = min(gewählt, passend) |

## Sources

### Primary (HIGH confidence)
- Quelltext Findling, gelesen 27.09.2026: `backend/src/findling/config.py` (1-90, 850-1365), `api/status.py` (ganz), `worker/poller.py` (427-456, 700-891, 1634-1673, 2009-2188), `nc/client.py` (300-493), `nc/queue.py` (470-543), `store/vectors.py` (70-99, 244-275), `api/resources.py` (235-290), `main.py` (652-771), `extract/sandbox.py` (59, 291); `php/lib/Controller/QueueController.php`, `php/lib/Service/SettingsService.php`, `php/lib/Service/AdminViewService.php` (1797-1870); Tests `test_config.py`, `test_status_endpoint.py:74`, `test_readonly_gate.py:239`, `test_php_trust_boundary.py`, `test_admin_ui_contract.py:2161`, `test_read_side.py:229-258`, `test_upgrade_compatibility.py`; `backend/appinfo/info.xml`
- `docs/performance.md:4737-4854` (BL-F04-Basiszahlen der v1.3-Anfahrt), `docs/embeddings.md` §8, `docs/admin-page.md`, `docs/runbook-messbox.md:410`
- nextcloud/app_api Quelltext via GitHub-API: `lib/Service/ExAppEnvVarsHelper.php` (main), `lib/Service/ExAppService.php` (stable32 299-323, stable33 301-323), `lib/DeployActions/DockerActions.php` (106, 158-166, 208, 567-573), `src/constants/daemonTemplates.js` (`resourceLimits: {memory: null, nanoCPUs: null}`)
- Eigene Messung im Findling-Abbild (Docker 29.5.2, cgroup v2): `process_cpu_count`, `cpu.max`, `memory.max`, `/proc/meminfo` unter drei `docker run`-Varianten

### Secondary (MEDIUM confidence)
- [CPython Issue #149452: os.process_cpu_count() should take cgroups CPU limitations into account](https://github.com/python/cpython/issues/149452), deckt sich mit eigener Messung
- [CPython Issue #80235: os.cpu_count() in containers](https://github.com/python/cpython/issues/80235)

### Tertiary (LOW confidence)
- keine

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, keine neuen Abhängigkeiten, nur Bordmittel
- Architecture: HIGH, alle Muster im Repo belegt, AppAPI-Verhalten im Quelltext dreier Zweige gelesen
- Pitfalls: HIGH für 1, 2, 3, 6, 7 (Code/Quelltext/Messung), MEDIUM für 4 und 5 (Deutungsfragen, an den Owner)
- Formelkonstanten: MEDIUM, gemessen in einer Anfahrt, Band-Vorbehalt K2 bleibt

**Research date:** 2026-09-27
**Valid until:** rund 30 Tage oder bis Phase 25 `poller.py`, `status.py` oder `info.xml` ändert; AppAPI-Befund bei jedem AppAPI-Major neu prüfen
