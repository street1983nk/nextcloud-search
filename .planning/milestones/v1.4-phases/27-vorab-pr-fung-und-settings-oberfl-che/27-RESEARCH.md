# Phase 27: Vorab-Prüfung und Settings-Oberfläche - Research

**Researched:** 2026-09-29
**Domain:** Container-Probe (Sandbox-Kinder, cgroup-Speicher, fp32-Beschaffung), Indexierungs-Pause, PHP-Schreibroute mit CSRF, Adminseite (Vanilla-JS), acht Sprachkataloge
**Confidence:** HIGH für Bestandscode und Muster (alles am Code belegt), MEDIUM für Probe-Rechnung und Zeitdeckel (Ableitung aus Messungen, nicht auf Zielhardware erprobt)

## Summary

Die Phase baut keinen neuen Parserpfad und keine neue Bibliothek ein. Alles, was die Probe braucht, liegt im Bestand: `SlotPool`/`ExtractionWorker` (gehärtete Spawn-Kinder, `sandbox.py:303-383`), `memory_guard.headroom_bytes()` (anon gegen memory.max, sonst MemAvailable, `memory_guard.py:71-89`), die Ladekosten-Rechnung des Einbettungs-Läufers (`EmbedRunner._need`, `worker/embedding.py:1658-1667`), die fp32-Beschaffung `procure_fp32` mit festem sha256 (`embed/weights.py:52-58, 288-313`) und die Wächter-Schwelle `GUARD_RESERVE_BYTES = OCR_SLOT_COST_BYTES = 235 MiB` (`config.py:889, 928`). Die Probe ist ein neuer Orchestrator, der diese Teile in fester Reihenfolge ruft, plus zwei neue Container-Routen, ein neuer PHP-Controller und ein neuer Block auf der Adminseite.

Drei Befunde prägen den Plan stärker als alles andere. **Erstens:** `access_level ADMIN` im Container schützt den Weg, den diese App geht, gar nicht; `PublicFunctions::exAppRequest` passiert die Prüfung nie (`SettingsController.php:75-80`, `test_php_trust_boundary.py` Pitfall 10). SC3 ("Nicht-Admin erreicht Probe- und Profilroute nicht") wird also durch den PHP-FrontpageRoute-Schutz (SecurityMiddleware, kein NoAdminRequired/NoCSRFRequired) plus Gate B plus ADMIN im info.xml als Tiefenverteidigung erfüllt, und der Test muss alle drei belegen. **Zweitens:** Der Container kann appconfig nicht schreiben (Gate A, `test_readonly_gate.py:248`, Allowlist ohne Profil). "Gespeichert wird nur bei passt" heißt daher: PHP schreibt, nachdem PHP selbst das Verdikt beim Container abgeholt und gegen den eigenen Startauftrag geprüft hat. Der Browser darf nie "passt" behaupten können. **Drittens:** Der Bestätigungs-Token des Wächters fließt heute in den Initial State und die Overview-JSON (`AdminViewService.php:1934`, `Settings/Admin.php:43`); mit D-27-12 muss er dort heraus und serverseitig beim Speichern nachgelesen werden.

Die fp32-Modellprobe kann NICHT im Hauptprozess laufen: der Gate `tools/one_load.py` verlangt "nie zwei Engines gleichzeitig" (`load_count - unload_count <= 1`), und ein Tausch der Hauptprozess-Engine würde Suchanfragen während der Probe mit fp32 gegen einen int8-Bestand einbetten. Sie läuft in einem eigenen Spawn-Kind nach dem Muster der Messung `docs/measurements/2026-09-fp32-speicher` (RssAnon vor Laden und nach erstem Batch, 8 Passagen auf Sequenzlänge 512). Dieses Kind kostet transient rund 820 MiB anon und braucht eine eigene Vorab-Rechnung.

**Primary recommendation:** Neuer neutraler Rechenkern `findling/probe.py` (ohne I/O, Muster `guard.py`), Orchestrator `findling/worker/probe_run.py`, Router `findling/api/probe.py` mit `^/probe$` (POST) und `^/probe/state$` (GET), beide ADMIN; PHP-Seite `ProfileSettingsController` (drei FrontpageRoutes) plus `ProbeService`, Ergebnis dauerhaft in appconfig, Sicherheitsabstand für "passt knapp" = `GUARD_RESERVE_BYTES`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Vorentscheide, die hier tragen und NICHT neu verhandelt werden: D-24-01 (Weg B: PHP speichert in appconfig, Container liest je Runde), D-24-02 (Lesefehler = letztes bekanntes Profil, sonst Sparsam), D-24-03 (Anteile, Obergrenzen Standard 4 / Leistung 16 Slots), D-24-06 (Vorschlags-Schwellen 6 GB/3 Kerne bzw. 12 GB/6 Kerne, nur Vorschlag), D-24-07 (gespeichertes Profil bleibt bei Schrumpfung, gewählt vs. wirksam sichtbar), D-25-01/03/04/05/09/10/14 (fp32 nur in Standard/Leistung wählbar, nie automatischer Wechsel, Download nur auf ausdrückliche Admin-Aktion aus dem eigenen GitHub-Release mit festem sha256, Rückweg zu int8 löscht die Datei, Offline-Ablage), D-26-01/04 (Wächter senkt nur die wirksame Stufe, Rückweg nur durch Admin-Aktion mit Bestätigungs-Token), ADM-04 (kein Erweitert-Bereich).

**fp32 auf der Fläche**
- **D-27-01 (Owner, 29.09.2026):** Die Genauigkeit erscheint als Häkchen unter dem Profil-Auswahlfeld ("Genaueres Suchmodell (fp32)", Arbeitstext), sichtbar nur bei Standard und Leistung. Die Probe testet Profil und Genauigkeit zusammen; gespeichert werden beide Schlüssel zusammen (Profil-Schlüssel und `model_precision`, D-25-02). Das ist ein Auswahlfeld plus eine Option, ADM-04 gilt als gewahrt.
- **D-27-02 (Owner, 29.09.2026):** Die fp32-Datei wird IN der Probe beschafft: Der Klick auf "Übernehmen und prüfen" mit gesetztem Häkchen ist die ausdrückliche Admin-Aktion im Sinne von D-25-05/D-25-14. Die Probe lädt die Datei (oder nimmt eine selbst abgelegte, D-25-06), prüft den Digest und misst das geladene Modell. Bei "passt" bleibt die Datei liegen und die Neueinbettung startet; bei "passt knapp"/"passt nicht" wird die Datei gelöscht und int8 bleibt aktiv (Platte frei, kein halber Zustand).
- **D-27-03 (Owner, 29.09.2026):** Setzen oder Entfernen des Häkchens zeigt eine Hinweiszeile mit Dokumentzahl und geschätzter Dauer der Neueinbettung (sinngemäß "Neueinbettung von 29.100 Dokumenten, geschätzt ca. 5 h; die Volltextsuche bleibt voll verfügbar"). Kein Bestätigungsdialog. Die Schätzung ist als Schätzung beschriftet (gleiche Linie wie die bestehende Dauer-Beschriftung in docs/admin-page.md).

**Probe-Ablauf**
- **D-27-04 (Owner, 29.09.2026):** Die Probe läuft im Hintergrund: Der Klick startet sie, die Seite fragt in kurzen Abständen nach und zeigt eine Fortschrittszeile (sinngemäß "Probe läuft: Modell laden ... OCR mit 4 Slots ..."). Das Ergebnis (Verdikt, Ursache, Zeitpunkt) ist nach einem Neuladen der Seite noch sichtbar. Kein synchroner Request bis zum Verdikt (Proxy-/Gateway-Timeouts, fp32-Download).
- **D-27-05 (Owner, 29.09.2026):** Während der Probe pausiert die Indexierung: Der Poller nimmt keine neue Staffel, eine laufende Staffel endet sauber (Zusagen aus Phase 26 halten), danach läuft alles weiter wie vorher. Die Probe misst die Box ohne mitlaufende Indexlast und kann zusammen mit ihr kein OOM auslösen (SC3).
- **D-27-06 (Owner, 29.09.2026):** Zeitdeckel zweigeteilt: Messteil (OCR und Modellprobe) fester Deckel in der Größenordnung 120 s; der fp32-Download einen eigenen Deckel in der Größenordnung 10 min mit eigenem Verdikt ("Download zu langsam" o. ä.). Endgültige Werte legt die Research fest. Höchstens eine Probe gleichzeitig (SC3).
- **D-27-07 (Owner, 29.09.2026):** Die N-Slot-Probe fährt zweistufig: erst EIN Slot auf der synthetischen Scanseite, das misst die echten Slot-Kosten auf DIESER Box; mit diesem Messwert rechnet die Probe vorab gegen die Speichergrenze, ob das Ziel-N passt; nur wenn ja, fährt sie N Slots gleichzeitig. Keine Leiter 1/2/.../N (sprengt den Zeitdeckel).

**Verdikt und Folgen**
- **D-27-08 (Owner, 29.09.2026):** "passt knapp" heißt: Die Rechnung geht auf, aber die Reserve liegt unter einem Sicherheitsabstand (Wert legt die Research fest, gegen Wächter-Schwellen aus Phase 26 abgestimmt). Folge: NICHT speichern; die Seite nennt Ursache und bietet an, die nächstniedrigere Stufe zu prüfen. Gespeichert wird ausschließlich bei "passt" (Anforderung PRUEF-01). Kein "Trotzdem übernehmen".
- **D-27-09 (Owner, 29.09.2026):** Wechsel auf Sparsam und der Wechsel fp32 zu int8 speichern sofort ohne Probe (weniger Last kann nicht "nicht passen"; das ist auch der Rückweg bei "passt nicht"). fp32 zu int8 zeigt die Reindex-Hinweiszeile (D-27-03). Leistung zu Standard ist KEIN sicherer Abwärtsweg und läuft durch die Probe.
- **D-27-10 (Owner, 29.09.2026):** Ein Verdikt verfällt nicht. Es gilt für den Moment des Speicherns; spätere Hardware-Änderungen deckt D-24-07 (wirksame Stufe folgt), Druck deckt der Wächter. Die Seite zeigt Datum und Ergebnis der letzten Probe.

**Texte und Rückwege**
- **D-27-11 (Owner, 29.09.2026):** Der zweite Knopf heißt "Bei Sparsam bleiben" statt "Beim sicheren Standard bleiben" (Roadmap SC1): Kollision mit dem Profilnamen "Standard". Der Wortlaut in ROADMAP.md SC1 wird beim Plan-Schnitt angepasst, der Sinn bleibt.
- **D-27-12 (Owner, 29.09.2026):** Nach einer Wächter-Absenkung nennt die Hinweisfläche beide Stufen und die Ursache und bietet "Erneut prüfen" an: Der Knopf fährt die Probe für das GEWÄHLTE Profil; bei "passt" gilt das als Admin-Bestätigung im Sinne von D-26-04 (Bestätigungs-Token über die Profil-Route). Die bisherige occ-Befehlszeile mit Token verschwindet von der Seite.
- **D-27-13 (Owner, 29.09.2026):** occ bleibt als dokumentierter zweiter Schreibweg für Profil und Genauigkeit (Automatisierung, kopflose Boxen). Die Doku sagt ausdrücklich, dass occ die Probe überspringt und dann nur der Wächter absichert; die UI ist der empfohlene Weg.
- **D-27-14 (Owner, 29.09.2026):** Umgebungsvariablen überstimmen nur Einzelwerte (`FINDLING_OCR_MAX_PAGES`, `FINDLING_OCR_DPI`, `FINDLING_EMBED_BATCH_SIZE`, `FINDLING_WRITER_HEAP_BYTES`, `profile.py:276`), nie das Profil oder die Slots. Das Auswahlfeld bleibt frei; die Hinweisfläche nennt überstimmte Werte samt Variable (sinngemäß "OCR-Auflösung 400 dpi durch FINDLING_OCR_DPI"). Die Probe rechnet und misst mit genau diesen wirksamen Werten (DPI und Seitenzahl treiben die Slot-Kosten).

### Claude's Discretion
- Ursachenliste bei "passt nicht"/"passt knapp" (Speicher, Slot-Kosten, Download, Digest, Zeitdeckel, Probe läuft schon, Container nicht erreichbar) als geschlossene Menge; Research legt fest, Anzeigewörter nur aus PHP-Katalogen (T-26-16-Muster).
- Form der Probe-Routen (Start, Stand abfragen) im Container und auf PHP-Seite, Speicherort des Probe-Ergebnisses (state.db oder appconfig), Poll-Intervall, Mechanik der Indexierungs-Pause im Poller.
- Sicherheitsabstand für "passt knapp", genaue Zeitdeckel, Herkunft und Größe der mitgelieferten synthetischen Scanseite (Import-Hygiene und Sandbox-Härtung aus Phase 26 gelten für die Probe-Kinder unverändert).
- Genaue Katalogtexte (Code Englisch; alle neuen Texte in allen acht Katalogen im Gleichstand, Katalog-Gates grün), Platzierung der Fläche auf der bestehenden Adminseite (UI-SPEC legt fest).
- Neues Bedrohungsregister für die Schreibroute: AR-24-02 verfällt mit dieser Phase (erste Schreibroute für das Profil); saveProfile als ADMIN-Frontpage-Route mit CSRF, geschlossene Wertemengen für Profil und Genauigkeit, Probe-Route access_level ADMIN im Container.

### Deferred Ideas (OUT OF SCOPE)
- Issue #18 Fix-Kandidaten (JPG-Verdikt, HEIF, Download-Größenprüfung): passt nicht zu dieser Phase (Trefferwert 0,2), wartet weiter auf budachsts Antwort und den Slot-Entscheid des Owners.
- Außerdem laut Phasengrenze: RAM-Messung je Profilstufe auf echter Hardware (Phase 28), Launch-Härtung und Release 1.4.0 (Phase 29), Erweitert-Bereich (ADM-04 bleibt), neue Profile oder Zwischenstufen.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRUEF-01 | "Übernehmen und prüfen" fährt vor dem Speichern eine echte Probe (N-Slot-Probe am OCR-Pfad, RAM-Rechnung mit gemessenen Slot-Kosten, bei fp32-Wunsch Modell-Probe), Verdikt passt/knapp/nicht mit Ursache; Speichern nur bei passt; Vorab-Rechnung gegen die Grenze; eine Probe gleichzeitig; Zeitdeckel; Route nur ADMIN | Muster 1 bis 6 (Ablauf, Rechnung, Pause, fp32, Commit-Bindung, Einzelflug), Ursachencodes, Security-Abschnitt, Test-Belege SC2/SC3 |
| UI-01 | Erste Settings-Fläche: Profilauswahl (geschlossene Menge) plus Hinweisfläche Erkennung/Vorschlag/Verdikt, ADM-04 gewahrt, Texte in 8 Sprachen / 16 Dateien im Gleichstand | Muster 7 und 8 (Datenfluss zur Fläche, Kataloge), UI-SPEC-Deltas, Pitfalls Token/Initial State, Katalog-Gates |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Code Englisch; deutsche Prosa mit echten Umlauten, nie Umlaute in Code, Keys, URLs, YAML.
- Keine Em-/En-Dashes (U+2014/U+2013), keine Emojis, Icons als SVG (Bestand: MDI-Pfade im Template).
- Qualitätsgates lokal grün vor Commit: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright` (lokal mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, Owner-Regel), `uv run vulture src tests --min-confidence 80`, `uv run pytest -q`; Skripte zusätzlich `ruff --config pyproject.toml ../scripts`.
- Python 3.13 + uv (System-Python defekt); PHP-Seite hat lokal kein PHP, PHPUnit läuft nur in CI (`.github/workflows/php.yml` Job `phpunit`), Syntax per `php -l` im Container.
- Security/Privacy: keine Inhalte verlassen den Server, kein Telemetrie-Phoning; Logs nur statische Sätze plus Typnamen/Zähler.
- Nach der Phase Security-, Bug- und Performance-Audit, Befunde vor Abschluss fixen.
- Kurze Produkttexte: Katalogsätze kurz, keine Erzählabsätze.
- K6: Companion-Änderungen reisen erst mit 1.4.0; Container muss mit altem Companion laufen und umgekehrt.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Profilwahl anzeigen, Knopfbeschriftung, Poll | Browser (admin.js) | PHP-Template (Z18 ohne JS) | Vanilla-JS schaltet nur `hidden`/Textknoten (Gate C), Markup liegt im Template |
| Admin-Schutz, CSRF, Wertemengen, Speichern in appconfig | PHP-Companion (ProfileSettingsController, SettingsService) | Container info.xml ADMIN (Tiefenverteidigung) | D-24-01 Weg B; exAppRequest umgeht ADMIN im Container, also ist PHP die wirksame Grenze |
| Commit-Bindung (nur "passt" speichert, nur der eigene Auftrag) | PHP (ProbeService) | Container liefert Verdikt + Id | Browser darf "passt" nicht behaupten können; Container darf appconfig nicht schreiben (Gate A) |
| Probe-Ablauf, Messung, Rechnung, Einzelflug, Zeitdeckel | Container (probe_run + probe) | Sandbox-Kinder, Modell-Kind | Nur der Container sieht cgroup, Kinder und Modell |
| Indexierungs-Pause und Wiederaufnahme | Container (Poller, EmbedRunner) | state.db meta (Neustart) | Pause ist Prozesszustand; Neustart hebt sie von selbst auf |
| fp32-Beschaffung, Digest, Löschen | Container (embed/weights.py) | Volume (models_dir) | Bestehender Baustein aus Phase 25 |
| Letztes Verdikt dauerhaft zeigen | PHP appconfig (profile_check) | Container state.db (laufende/letzte Probe) | Seite muss auch bei stummem Container rendern (Z14, Z18) |
| Wortlaut aller Codes | PHP-Kataloge (16 Dateien) + JS-Map | nichts | T-26-16: Container liefert nur Codes |

## Standard Stack

Keine neue Abhängigkeit. Alles ist Bestand.

### Core (Bestand, wiederverwenden)
| Baustein | Ort | Zweck in Phase 27 |
|----------|-----|-------------------|
| `ExtractionWorker`, `SlotPool` | `extract/sandbox.py:385`, `extract/pool.py:103` | OCR-Probe auf gehärteten Kindern (nice 10, oom_score_adj 1000, RLIMIT_AS, secrets geschält) |
| `memory_guard.headroom_bytes`, `admits` | `memory_guard.py:71-94` | Vorab-Rechnung und Stichproben während der Läufe |
| `guard.throttled_slots`, `GUARD_RESERVE_BYTES` | `guard.py:97-105`, `config.py:928` | Sicherheitsabstand für "passt knapp" abgestimmt auf die Drossel |
| `profile.resolve`, `ocr_slots`, `suggest` | `profile.py:202-301` | Ziel-N und wirksame Werte samt Quelle `env` |
| `EmbedRunner._need` (Ladekosten) | `worker/embedding.py:1658-1667` | Ausstehende Ladekosten (Cutter, Gewichte, fp32) in die Rechnung |
| `procure_fp32`, `fp32_verified`, `remove_fp32_weights` | `embed/weights.py:130-313` | Download mit Deckel, Digest, Offline-Datei, Aufräumen |
| `fetch_release_asset` | `nc/client.py:395` | Einziger erlaubter Netzweg (Gate A, invariant 1) |
| `IAppConfig::hasKey/getValueArray/setValueArray` | OCP, seit NC 29 [CITED: github.com/nextcloud/server stable33 lib/public/IAppConfig.php] | "kein Profil gespeichert" erkennen, Probe-Ergebnis ablegen |
| SecurityMiddleware | NC Core [CITED: nextcloud/server lib/private/AppFramework/Middleware/Security/SecurityMiddleware.php] | CSRF gilt ohne Verb-Ausnahme, also auch für GET-FrontpageRoutes; Admin-Pflicht ohne NoAdminRequired |

**Installation:** keine.

## Package Legitimacy Audit

Keine externen Pakete werden in dieser Phase installiert. slopcheck nicht nötig.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
Browser (admin.js)
  | POST /apps/findling/admin/profile/check {profile, precision}   (requesttoken, Admin-Sitzung)
  v
PHP ProfileSettingsController --validate closed sets--> ProbeService.start
  |   schreibt appconfig profile_check_pending {id?, profile, precision, uid, at}
  |   ExAppService.adminSend POST /probe  --AppAPI exAppRequest-->  Container
  |                                                                   |
  |                                               api/probe.py (Einzelflug, 202 | 409 busy | 503)
  |                                                                   v
  |                                               probe_run (asyncio Task)
  |                                                 1 pause:   hold Poller + EmbedRunner, warten bis Staffel endet
  |                                                 2 download/digest (nur fp32, eigener Deckel 600 s)
  |                                                 3 model:   Spawn-Kind int8 + Spawn-Kind fp32, RssAnon-Delta, Rate
  |                                                 4 ocr_one: frisches Kind, Scanseite, Headroom-Stichproben
  |                                                 5 calc:    need(N) gegen H0, Reserve gegen GUARD_RESERVE_BYTES
  |                                                 6 ocr_n:   nur wenn calc "passt": N frische Kinder parallel
  |                                                 7 cleanup: Kinder schließen, bei knapp/nicht fp32-Datei löschen,
  |                                                            Pause aufheben, Ergebnis in state.db meta
  |
  | GET /apps/findling/admin/profile/check  (alle 2000 ms während Z6)
  v
ProbeService.state --GET /probe/state--> {id, state, step, bytes, verdict, cause, numbers, target}
  |  state=done und id == pending.id und target == pending.target
  |     verdict fits  -> appconfig profile + model_precision (+ profile_confirmed bei Wächter-Fall) schreiben
  |     alle Verdikte -> appconfig profile_check {verdict, cause, numbers, at, committed}
  v
Browser: Verdikt-Karte (Z7/Z8/Z9), danach Status-Poll

Container nächste Runde: poller.run_once -> companion_choice -> note_chosen / note_chosen_precision / note_confirmation
  (Profil gilt ab der nächsten Indexrunde; fp32 aktiviert über fp32_ready ohne Download, D-25-06-Pfad)

Speichern ohne Probe (Z5): POST /apps/findling/admin/profile {profile, precision}
  -> PHP prüft "Abwärtsweg" serverseitig (Ziel economy, oder nur fp32->int8 bei gleichem Profil) -> appconfig
```

### Recommended Project Structure

```
backend/src/findling/
├── probe.py                 # NEU, neutral ohne I/O: Codes, Zustand, Rechnung (Muster guard.py/profile.py)
├── worker/probe_run.py      # NEU: Orchestrator (Pause, Download, Modell-Kind, OCR-Läufe, Cleanup)
├── embed/model_probe.py     # NEU: Spawn-Kind für die Modellprobe (gehärtet wie sandbox._child_main)
├── extract/probe_scan.pdf   # NEU: Kopie von testdata/corpus/13-ratsvorlage-scan.pdf, sha256 im Code gepinnt
├── api/probe.py             # NEU: ROUTER, POST /probe, GET /probe/state
├── worker/poller.py         # ÄNDERN: hold_for_probe()/release_probe_hold(), shed-idle am Pool
├── worker/embedding.py      # ÄNDERN: EmbedRunner hält während der Probe an
├── worker/watch.py          # ÄNDERN (Owner-Frage 1): Eskalation während der Probe stumm
└── api/status.py            # ÄNDERN: Block probe (Unterstützung, laufend), Rate für Reindex-Schätzung
backend/appinfo/info.xml     # zwei <route> ADMIN, Kommentar "Five routes" nachziehen
php/lib/Controller/ProfileSettingsController.php  # NEU: drei FrontpageRoutes
php/lib/Service/ProbeService.php                  # NEU: Start, Stand, Commit-Bindung, Ergebnis-Ablage
php/lib/Service/ExAppService.php                  # ÄNDERN: adminSend/adminState mit unterscheidbarer Fehlerform
php/lib/Service/SettingsService.php               # ÄNDERN: profileStored(), saveProfile(), saveConfirmation()
php/lib/Service/AdminViewService.php              # ÄNDERN: guardToken raus, guardConfirmable rein; profile/probe-Block
php/templates/admin.php, php/js/admin.js, php/css/admin.css
php/l10n/*.js, *.json (16 Dateien)
```

### Pattern 1: Probe-Ablauf mit geschlossenen Schrittcodes

**Schritte (Endliste, UI-SPEC bestätigt):** `pause`, `download`, `digest`, `model`, `ocr_one`, `calc`, `ocr_n`, `cleanup`. Kein weiterer Code. Reihenfolge:

1. `pause`: Poller und EmbedRunner halten (Muster 3), warten bis beide keine Runde mehr fahren. Eigener Deckel `PROBE_PAUSE_SECONDS = OCR_LOCK_TIMEOUT_SECONDS` (1800 s, `config.py:467`), weil eine Staffel per Konstruktion innerhalb der Lease endet (D-26-06). Überschreitung: Ursache `pause_timeout`.
2. `download` (nur Ziel fp32, fp32 nicht aktiv, keine geprüfte Datei da): `procure_fp32(models_dir, counting_fetch, min_free_bytes=...)` unter `asyncio.timeout(PROBE_DOWNLOAD_SECONDS=600)`. Fortschritt über einen Wrapper um `fetch`, der die Bytes des `write`-Callbacks zählt (`weights.py:239-243`). Abbruch per Deckel ist eine Cancellation; `procure_fp32` räumt die `.part` im `finally` (`weights.py:310-313`). Mapping: `unavailable` -> `download_failed`, `wrong_digest` -> `digest_mismatch`, `no_room` -> `disk_short`, Deckel -> `download_slow`.
3. `digest` (nur wenn eine abgelegte Datei da ist, D-25-06): `fp32_verified` in `asyncio.to_thread`; zählt in den Download-Deckel, nicht in den Messdeckel (470 MB Hash).
4. `model` (nur Ziel fp32 und fp32 nicht schon aktiv): Modell-Kind (Muster 4).
5. `ocr_one`: ein frisches Kind, Scanseite, Headroom-Stichproben (Muster 2).
6. `calc`: Rechnung (Muster 2). Ergebnis "nicht" oder "knapp" endet hier ohne N-Lauf.
7. `ocr_n`: nur wenn `calc` "passt" und N >= 2. N frische Kinder parallel.
8. `cleanup`: Kinder schließen, bei knapp/nicht und selbst geladener fp32-Datei `remove_fp32_weights`, Pause aufheben (immer, im `finally`), Ergebnis schreiben.

**Messdeckel:** `PROBE_MEASURE_SECONDS = 120` gilt für die Summe aus `model`, `ocr_one`, `calc`, `ocr_n` (ein `asyncio.timeout` um diesen Abschnitt; jeder Kinderauftrag bekommt `timeout_seconds = verbleibende Zeit`, damit `ExtractionWorker._ask` selbst tötet, `sandbox.py:543-557`). Begründung der 120 s: eine OCR-Seite kostet 2 bis 3 s (`docs/performance.md:125, 1202`: 2517 ms cpx22, 2,80 s je Seite), ein Kindstart mit Imports 0,5 bis 2 s auf ARM (`sandbox.py:18-22`), die Scanseite hat 3 Seiten, also ocr_one ca. 10 s, ocr_n bei N <= Kerne ähnlich plus Konkurrenz; zwei Modell-Kinder je ca. 5 bis 15 s (Laden + 1 Batch, Rate 3 bis 6 Passagen/s laut `docs/measurements/2026-09-fp32-speicher/README.md` §4). Summe schlimmstenfalls ca. 70 s. [ASSUMED: ARM-Zeiten für Modell-Kind, nicht gemessen]

### Pattern 2: Rechnung und Sicherheitsabstand (D-27-07, D-27-08)

Alle Größen in Byte, alle aus `probe.py` ohne I/O berechnet, damit sie unit-testbar sind.

- `N = profile.resolve(target, hardware, weights=target_precision).values.ocr_slots` (enthält Env-Überstimmungen und den fp32-Abzug der Formel, `profile.py:286-301`). Wichtig: Standard gibt auf 4 Kernen N = 1 (`config.py:942-945`); dann entfällt `ocr_n`.
- `H0 = headroom_bytes()` nach `pause`, nachdem der Pool seine freien Kinder abgegeben hat (neue Methode `SlotPool.shed_idle()`, stoppt nur Kinder der Freiliste). Unlesbar (None): Verdikt nicht, Ursache `memory_unknown`, ohne Lauf (Regel `admits`: unlesbar wird nie zugelassen, `memory_guard.py:92-94`).
- Vorab-Tor vor `ocr_one`: `H0 >= OCR_SLOT_COST_BYTES + GUARD_RESERVE_BYTES`, sonst `memory_short` ohne Lauf (die Probe darf selbst kein OOM sein, SC3).
- `c_mess = H0 - min(Headroom während ocr_one)`, Stichproben alle 200 ms in einem eigenen Daemon-Thread (nicht im Default-Executor, Issue-19-Regel, `pool.py:14-20`). Gemessen wird damit anon gegen die Grenze bzw. MemAvailable, genau die Größe, die Drossel und Wächter lesen.
- `c = max(c_mess, OCR_SLOT_COST_BYTES)`. Begründung: die Drossel rechnet mit der Konstante (`guard.py:97-105`); ein kleinerer Messwert würde "passt" sagen, während die Drossel im Betrieb schon kürzt. Der Messwert zählt nur nach oben (höhere DPI per `FINDLING_OCR_DPI`, D-27-14).
- `L` (ausstehende Ladekosten des Betriebs): nach `EmbedRunner._need` (`embedding.py:1658-1667`): `CUTTER_LOAD_BYTES` wenn der Cutter nicht gebaut ist; `EMBED_WEIGHTS_LOAD_BYTES` wenn die Engine nicht geladen ist; Modell-Mehrbedarf bei Wechsel auf fp32 (gemessen aus Muster 4, sonst `FP32_EXTRA_BYTES`); `embed_slots x EMBED_ACTIVATION_BYTES` bei parallelem Lauf; Differenz `writer_heap_bytes(target) - writer_heap_bytes(wirksam)` (Standard 128 MB, Leistung 256 MB gegen Sparsam 50 MB, `config.py:958, 971`). Die Leerlauf-Entladung (MEM-01) kann Modell und Cutter während der Probe gerade freigegeben haben; genau deshalb werden sie als ausstehend dazugerechnet.
- `need(N) = N x c + L`, `reserve = H0 - need(N)`.
  - `reserve < 0`: **nicht**, `memory_short` (Zahlen: N, need, H0). Liegt der Fehlbetrag allein am Modell-Mehrbedarf (need ohne fp32-Anteil passt): `model_memory`.
  - `0 <= reserve < GUARD_RESERVE_BYTES`: **knapp**, `reserve_thin` (Zahlen: reserve, 235 MiB). Kein N-Lauf.
  - sonst `ocr_n` fahren; danach `reserve_n = min(Headroom während ocr_n) - L`. Kind getötet (ChildKilled oder `failed(out_of_memory)`): **nicht**, `slot_killed`. `reserve_n < GUARD_RESERVE_BYTES`: **knapp**, `reserve_thin`. Sonst **passt**.
- **Warum genau `GUARD_RESERVE_BYTES` als Abstand:** Mit `reserve >= 235 MiB` und `c >= 235 MiB` gilt `H0 - L >= (N-1) x 235 MiB + 235 MiB`, also lässt `throttled_slots` alle N Slots zu (`guard.py:104-105`), und der Headroom fällt nicht unter die Schwelle, unter der ein steigendes `memory.events max` als Ereignis zählt (`guard.py:145`). Ein kleinerer Abstand hieße: gespeichert, aber sofort gedrosselt oder nach zwei Ereignissen abgesenkt. [VERIFIED: codebase]

### Pattern 3: Indexierungs-Pause (D-27-05)

**Nicht** `silence()`/`arm()` verwenden: `arm` gehört `enabled_handler` und dem Lifespan (`main.py:263-335`); eine Probe, die am Ende `arm()` ruft, würde ein zwischenzeitliches Abschalten der App überschreiben. Stattdessen ein eigenes Haltesignal:

- Neutrales Modul-Flag (z. B. in `probe.py`: `hold()`, `release()`, `held()`) oder je ein `asyncio.Event` auf `Poller` und `EmbedRunner`. `Poller.run` prüft vor `run_once` (`poller.py:796-806`) zusätzlich "gehalten" und wartet wie beim Armed-Flag mit `_first_of(release, stop_event)`. `EmbedRunner.run` genauso (`embedding.py:1494-1497`).
- Warten auf das Ende: `Poller.pass_in_flight` (`poller.py:675-677`) und `EmbedRunner._in_flight` bzw. `parked` (`embedding.py:1432-1433, 1521-1525`). Kein `unlock_held`, kein Writer-Close: die laufende Staffel endet regulär mit Quittung (Zusagen D-26-06/13 halten). Das unterscheidet die Pause von `stand_down` (`poller.py:679-745`).
- Economy bettet inline in der Staffel ein; dort deckt das Halten des Pollers die Einbettung mit ab.
- `Reconcile` braucht keine Pause (nur Queue-Abgleich ohne Extraktion).
- **Wiederaufnahme:** im `finally` des Orchestrators, auch bei Cancellation und Ausnahme. Neustart mitten in der Probe: der Halt ist reiner Prozesszustand, ein neuer Prozess startet ungehalten. state.db meta `probe_state` = `running` samt `probe_fp32_fetched` wird beim Start gelesen: Ergebnis "nicht, `interrupted`" setzen; eine von der Probe geholte fp32-Datei erst NACH dem ersten erfolgreichen Companion-Read löschen, und nur wenn der Schlüssel dann `int8` sagt (sonst hat PHP "passt" schon übernommen und der D-25-06-Pfad aktiviert die Datei ohne Download, `precision.py:231-234`).
- **multi_slot_pass:** die Probe setzt die Marke NICHT (`poller.py:1051`, `guard.py:54-66`). Ein Tod des Hauptprozesses während `ocr_n` soll keine Wächter-Absenkung "unclean_end" des gewählten Profils auslösen, denn die Last war die Probe und nicht das Profil. Die eigene Marke `probe_state` reicht.
- Rebuild in Arbeit (`main._a_rebuild_may_start`, `main.py:364`): Probe-Start ablehnen (Startcode `rebuilding`).

### Pattern 4: fp32-Modellprobe im eigenen Spawn-Kind (D-27-02)

- Nicht im Hauptprozess: Gate "nie zwei Engines" (`tools/one_load.py`, Zähler `load_count/unload_count` in `embed/model.py:147-176`), und ein Tausch der Haupt-Engine (`swap_engine`, `embed/engine.py:210`) würde Suchanfragen während der Probe mit fp32 einbetten.
- Neues Modul `embed/model_probe.py`, Spawn-Kontext wie `sandbox.SPAWN_CONTEXT`. Im Kind zuerst `setsid`, `os.nice(SANDBOX_NICE)`, `_lower_own_standing()`, `_shed_secrets()` (Funktionen aus `sandbox.py:187-250` wiederverwenden). **Kein** `RLIMIT_AS` von 512 MB (`config.py:232`): onnxruntime reserviert deutlich mehr virtuellen Adressraum, das Kind würde am Limit statt am Speicher scheitern. [ASSUMED: genauer AS-Bedarf von ORT nicht gemessen; Planer setzt entweder kein Limit oder ein großzügiges, begründetes]
- Methode wie die Messung, damit der Wert mit `FP32_EXTRA_BYTES` vergleichbar ist: `RssAnon` aus `/proc/self/status` vor dem Laden und nach dem ersten Batch aus 8 festen Passagen auf Sequenzlänge 512; Sitzungsoptionen wie `embed/model.py::_open_session` (`docs/measurements/2026-09-fp32-speicher/README.md` §3). Zwei Kinder nacheinander (int8, dann fp32), `extra_mess = delta_fp32 - delta_int8`; Rate in Passagen/s je Präzision fällt dabei ab (Grundlage der Reindex-Schätzung, Muster 8).
- Vorab-Tor vor dem Modell-Kind: `H0 >= MODEL_PROBE_CHILD_BYTES + GUARD_RESERVE_BYTES`, mit `MODEL_PROBE_CHILD_BYTES` aus der Messung (fp32 nach erstem Batch ca. 835980 KiB RssAnon, also rund 820 MiB inkl. Interpreter/ORT/Tokenizer). Sonst `model_memory` ohne Laden.
- Bekannter Preis: Das Kind braucht transient mehr als der Betrieb (Betrieb +367 MiB, Kind ca. 820 MiB). Boxen mit H0 zwischen ca. 840 MiB und ca. 1055 MiB würden die Modellprobe nicht bestehen, obwohl die Formel fp32 im Betrieb zuließe. Konservativ, im Sinne von SC3; in der Doku benennen.
- Nach `passt`: Datei bleibt, PHP schreibt `model_precision=fp32`; der Container sieht in der nächsten Runde den Wechsel int8 -> fp32, `decide(fp32_ready=True)` aktiviert ohne Download (`precision.py:231-234`), die Marke löst die Neueinbettung aus (Phase 24 MOD-01). Kein Eingriff in die Zustandsmaschine nötig; die Probe ruft `begin_procurement` NICHT.
- Bei knapp/nicht: `remove_fp32_weights` nur, wenn die Probe die Datei selbst geholt hat. Eine vom Admin abgelegte Datei (D-25-06) bleibt liegen. [Owner-Frage 3]

### Pattern 5: Commit-Bindung auf PHP-Seite

- **Start** (`POST /apps/findling/admin/profile/check`): Werte gegen `SettingsService::PROFILES`/`PRECISIONS` (strict `in_array`), fp32 nur mit standard/performance (D-25-01). Serverseitig prüfen, dass der Auftrag eine Probe braucht (Regel UI-SPEC "Probe nötig?"). Container-Start; bei 202 appconfig `profile_check_pending = {id, profile, precision, uid, startedAt}` (setValueArray).
- **Stand** (`GET /apps/findling/admin/profile/check`): Container `/probe/state` lesen, jedes Feld gegen seine geschlossene Menge prüfen (Muster `AdminViewService::guardCause`/`hexToken`, `AdminViewService.php:2068-2101`). Ist `state=done` und `id == pending.id` und `target == pending`, dann **einmalig** (idempotent über die Id):
  - `fits`: `profile` und `model_precision` schreiben; lag eine Wächterkappe vor und ist `target.profile == guard.chosen`, zusätzlich `profile_confirmed` = aktueller Token aus einem frischen `/status` (serverseitig, D-27-12). Ein anderes Profil hebt die Kappe ohnehin auf (`guard.note_confirmation`, `guard.py:243-250`).
  - jedes Verdikt: `profile_check = {id, profile, precision, verdict, cause, numbers, at, committed}`; `pending` löschen.
  - GET mit Schreibwirkung ist hier vertretbar, weil SecurityMiddleware CSRF auch bei GET prüft (keine Verb-Ausnahme, [CITED: SecurityMiddleware.php isInvalidCSRFRequired]) und die Wirkung nur den eigenen, vom Admin gestarteten Auftrag vollzieht.
- **Beim Seitenaufbau** (`Settings/Admin::getForm`, `Admin.php:38-43`) dieselbe idempotente Übernahme, damit ein geschlossener Tab (D-27-04) das "passt" nicht verliert.
- **Speichern ohne Probe** (`POST /apps/findling/admin/profile`): nur Abwärtswege (Ziel economy; oder gleiches Profil und nur fp32 -> int8). Alles andere 400 `probe_required`. "Bei Sparsam bleiben" schreibt economy auch dann, wenn economy schon gilt (UI-SPEC).
- **Zustand "kein Profil gespeichert" vs "Sparsam gespeichert":** `SettingsService::profileStored(): bool` über `IAppConfig::hasKey(APP_ID, KEY_PROFILE)`; `profile()` bleibt unverändert (Fallback economy, `SettingsService.php:314-328`).
- **Speicherort-Entscheid:** appconfig für das dauerhafte Ergebnis (PHP-eigen, rendert auch bei stummem Container, überlebt einen Volume-Verlust des Containers nicht nötig, weil nur Anzeige). state.db meta nur für die laufende und letzte Probe des Containers (Neustart, `interrupted`).

### Pattern 6: Einzelflug und Routenform im Container

- `api/probe.py`: `POST /probe` Body `{profile: Literal[...], precision: Literal["int8","fp32"]}` (pydantic, geschlossene Mengen zweites Mal). Antworten: 202 `{id}`; 409 `{state:"busy", id}`; 409 `{state:"rebuilding"}`; 503 wenn Lifespan/Poller fehlt; 422 ungültig (FastAPI-Standard). `GET /probe/state` liefert immer 200 mit `state ∈ {idle, running, done}`.
- Einzelflug: Modulzustand in `probe.py` plus `asyncio.Lock` beim Start; der Task wird wie `_EMBEDDING` usw. an den Lifespan gehängt (`main.py:92-105`), damit der Shutdown ihn cancelt und das `finally` die Pause aufhebt.
- Id: `secrets.token_hex(8)`; nie ein Pfad, nie ein Text im Ergebnis.
- info.xml: zwei `<route>` mit verankerten URLs `^/probe$` (POST, ADMIN) und `^/probe/state$` (GET, ADMIN), `bruteforce_protection [401]` wie der Bestand (`backend/appinfo/info.xml:307-348`). Getrennte URLs statt einer URL mit zwei Verben, weil jede Route genau ein `<verb>` trägt wie im Bestand. Kommentar "Five routes" (`info.xml:261`) auf sieben nachziehen.
- `ExAppService`: neue Methoden `adminSend(path, userId, body)` und `adminState(path, userId)` mit einer **unterscheidbaren** Antwortform `{kind: ok|unreachable|missing|busy|refused, body}`. `adminGet` taugt nicht, weil es jeden Fehler zu `null` macht (`ExAppService.php:595-644`) und Z14 (unerreichbar), Z15 (404 alte Version) und Z16 (409 belegt) dann nicht unterscheidbar wären. Timeout `ADMIN_REQUEST_TIMEOUT_SECONDS` (2,0 s) genügt, weil der Start sofort antwortet.

### Pattern 7: Datenfluss zur Fläche

- Statusblock `profile` existiert (Hardware, gewählt, vorgeschlagen, wirksam, Werte samt `sources`, `status.py:153-168, 360-394`). Neu: Block `probe` im Status (`supported: true`, `running: bool`, `step`), damit eine Seite ohne Klick weiß, ob der Container die Probe kann (Z15 vorab statt erst nach Klick) und ob in einem anderen Tab eine läuft (Z6 beim Aufruf).
- Env-Überstimmung (D-27-14): `sources` liegt schon im Status; PHP bildet je Feld mit Quelle `env` die Zeile aus Wert plus festem Variablennamen (Map in PHP, nicht vom Container), Variablenname in `<code>` per Marker-Schnitt wie bisher (`admin.php:286-291`).
- `guardToken` aus Overview und Initial State entfernen, stattdessen `guardConfirmable: bool` (`AdminViewService.php:1934`). Token nur noch serverseitig in `ProbeService` gelesen.

### Pattern 8: Reindex-Schätzung (D-27-03)

- Dokumentzahl: `indexed` (jede indexierte Datei wird neu eingebettet, `docs/embeddings.md` §11 "Während der Neueinbettung").
- Dauer = `chunks / rate`. `chunks`: neues Feld im Status-Block `model` (Zeilenzahl der Vektortabelle; `status._embedded` liest den Vektorbestand schon, `status.py:542`). `rate` in Passagen/s:
  1. gemessen in der letzten Probe auf dieser Box (Muster 4 liefert beide Präzisionen), im `profile_check` abgelegt;
  2. sonst keine Dauer, Kurzform der UI-SPEC (nur Dokumentzahl).
- Für fp32 -> int8 ohne Probe gilt dasselbe: Rate aus der letzten Probe, sonst Kurzform. Beschriftung "geschätzt", Formatierer `$span`/`span()` (eine Einheit). Die Messrate stammt aus dem ungünstigsten Batch (Sequenzlänge 512), die Schätzung liegt eher zu hoch; das ist die richtige Richtung.
- [Owner-Frage 4] ob zusätzlich eine im Betrieb gemessene Rate (Einbettungsspur zählt Passagen und Zeit) die Kurzform ersetzen soll.

### Anti-Patterns to Avoid

- **Browser meldet "passt" an die Schreibroute:** öffnet PRUEF-01 für jede manipulierte Anfrage. Commit nur aus dem Container-Ergebnis mit gebundener Id.
- **Probe ruft `poller.silence()/arm()`:** überschreibt Enable/Disable von AppAPI.
- **Modellprobe im Hauptprozess oder über `swap_engine`:** bricht one_load-Gate und bettet Suchanfragen falsch ein.
- **`adminGet` für Probe-Aufrufe:** verschluckt 404/409 zu null.
- **Probe nutzt die Leerlauf-Kinder des Poller-Pools für die Messung:** deren Importkosten sind schon in H0; die Messung würde die Kosten eines neuen Kindes unterschätzen. Frische Kinder, freie Pool-Kinder vorher abgeben.
- **Messdeckel über Pause und Download:** Pause kann Minuten dauern, Download bis 600 s; beide haben eigene Deckel.
- **Wortlaut aus dem Container:** jeder Code nur über PHP-Map und Katalog, unbekannt = Zeile verborgen.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Kind mit Deadline, Kill, Härtung | eigener subprocess-Wrapper | `ExtractionWorker`/`SlotPool` | Recycling-Regeln, ChildKilled vs. eigener Kill, Gruppenkill, secrets geschält |
| Speicher-Headroom | eigener cgroup-Leser | `memory_guard.headroom_bytes` | anon statt memory.current (Page-Cache der mmap-Index), MemAvailable-Fallback |
| fp32-Download | eigener HTTP-Download | `procure_fp32` + `fetch_release_asset` | Digest, Länge, fsync vor rename, `.part` bei jedem Ausgang weg, Gate A |
| Ladekosten | neue Konstantenliste | Muster `EmbedRunner._need` (in `probe.py` oder `memory_guard` neutral auslagern) | eine Schreibweise für dieselbe Rechnung |
| Slotzahl eines Profils | eigene Formel | `profile.resolve(...).values.ocr_slots` | Env, fp32-Abzug, Obergrenzen schon drin |
| Token-Prüfung | eigene Regex | `SettingsService::profileConfirmed`-Muster, `AdminViewService::hexToken` | `/D`-Anker gegen Newline (T-26-05) |
| Dauer-/Größenformat | neue Formatierer | `$span`/`$size`/`$count` im Template, `span()`/`size()` in admin.js | Gleichheit PHP/JS |

**Key insight:** Die Phase ist fast vollständig Verdrahtung. Jede Eigenbau-Stelle wäre eine zweite Schreibweise einer Regel, die heute genau eine hat.

## Runtime State Inventory

Keine Umbenennung; nur Neuzugänge und eine Entfernung.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | appconfig neu: `profile_check`, `profile_check_pending`; state.db meta neu: `probe_state`, `probe_id`, `probe_fp32_fetched`, letztes Ergebnis | Code; beim Deinstallieren: PHP-Keys fallen mit der App-Config, Uninstall-Vertrag prüfen (`test_uninstall_contract.py`) |
| Live service config | ExApp-Routen werden erst mit dem Update auf das neue Image/info.xml registriert (K6) | keine Datenmigration; Z15 deckt den alten Container |
| OS-registered state | keine, verifiziert (kein Cron, kein systemd in der Phase) | keine |
| Secrets/env vars | keine neuen; `profile_confirmed` bleibt Key, Token verlässt die Seite | Code: Token aus Overview/Initial State entfernen |
| Build artifacts | `extract/probe_scan.pdf` muss ins Paket (uv_build nimmt Nicht-.py-Dateien im Modul mit, Präzedenz `store/schema.sql`) | Test, dass die Datei im gebauten Image liegt und sha256 passt |
| Katalogschlüssel | `To lift the reduction after checking the memory: %1$s` in 16 Dateien | löschen, Ausnahmelisten der Gates mitziehen |

## Common Pitfalls

### Pitfall 1: ADMIN im Container gilt als Schutz
**What goes wrong:** Der Plan verlässt sich auf `access_level ADMIN`. **Why:** `exAppRequest` passiert `ExAppProxyController` nie (`SettingsController.php:75-80`). **How to avoid:** Schutz = PHP-FrontpageRoute ohne die vier verbotenen Attribute; Gate B (`test_php_trust_boundary.py`) plus neuer Test je info.xml-Block (Muster `test_diagnose_endpoint.py:582-595`). **Warning signs:** ein neuer Controller extends OCSController oder trägt `NoCSRFRequired`.

### Pitfall 2: Token wandert weiter in den Browser
**What goes wrong:** `guardToken` bleibt in Overview/Initial State, UI-SPEC-Regel "nie gerendert" verletzt, AR-26-02 bleibt fälschlich nötig. **How to avoid:** Feld durch `guardConfirmable` ersetzen, Test auf die JSON-Keys der Overview und des Bootstrap-States.

### Pitfall 3: Die Probe löst die Wächter-Absenkung des aktuellen Profils aus
**What goes wrong:** Ein im `ocr_n` vom Kernel getötetes Probe-Kind erhöht `memory.events oom_kill`; `GuardWatch` liest das im nächsten Tick als `oom_kill` und senkt das GEWÄHLTE (nicht das geprüfte) Profil ab (`guard.py:142-144`, `watch.py:204`). **How to avoid:** Eskalation während der Probe und einen Tick danach nur neu basieren (Basis setzen, nicht zählen). [Owner-Frage 1]

### Pitfall 4: Entladenes Modell täuscht Platz vor
**What goes wrong:** MEM-01 gibt Modell und Cutter im Leerlauf frei; die gerade pausierte Box sieht 900 MiB mehr Headroom als im Betrieb. **How to avoid:** `L` nach `_need`-Muster; Test mit Engine "released" und Cutter nicht gebaut.

### Pitfall 5: Pool-Kinder und Messung
**What goes wrong:** `ocr_one` auf einem wiederverwendeten Kind misst nur Seite + tesseract, nicht den Kindstart; N-Lauf auf den Poller-Kindern mischt Zustände. **How to avoid:** `SlotPool.shed_idle()` vor H0, danach eigener Probe-Pool mit frischen `ExtractionWorker`, am Ende `close()`.

### Pitfall 6: Profilwerte erreichen das Kind nicht
**What goes wrong:** Die Probe glaubt, sie messe mit `ocr_max_pages` 100/150 des Zielprofils. **Why:** Das Kind liest `settings()` aus seiner Umgebung (`ocr.py:151, 167`), Profilwerte sind nicht verdrahtet (`profile.py:34-37`). **How to avoid:** Probe misst mit dem, was der Betrieb tatsächlich nutzt: DPI und Seitendeckel aus der Umgebung (Env-Überstimmung wirkt, D-27-14). Die Seitenzahl treibt die Spitze kaum (Seiten laufen nacheinander), die DPI schon. So im Code-Kommentar festhalten.

### Pitfall 7: Aufräumen der fp32-Datei beim Neustart zu früh
**What goes wrong:** Start-Aufräumen löscht die Datei, bevor der Schlüssel gelesen ist; hatte PHP "passt" schon übernommen, fehlt die Datei und D-25-04 verbietet einen Neuversuch ohne Schlüsselwechsel. **How to avoid:** Löschen erst nach dem ersten erfolgreichen `companion_choice` und nur bei Schlüssel int8.

### Pitfall 8: Torn read von Wächter-Kappe und Token
**What goes wrong:** IN-01 aus 26-REVIEW: `guard.snapshot()` aus dem Worker-Thread kann neue Kappe mit altem Token lesen; PHP schreibt dann einen falschen Token (sichere Seite, aber "Erneut prüfen" wirkt scheinbar nicht). **How to avoid:** IN-01 in dieser Phase fixen (ein unveränderliches Snapshot-Objekt, atomarer Austausch wie `profile.py:370-374`). IN-02 (SlotPool.call-Rennfenster) ebenfalls, weil die Probe den Pool im Shutdown-Fenster nutzt.

### Pitfall 9: Katalog-Gates
**What goes wrong:** "Standard", "fp32", "OCR" sind in mehreren Sprachen wortgleich und fallen durch `test_every_catalogue_value_carries_a_wording_of_its_language`; ein `%` ohne Platzhalter bricht `test_no_catalogue_value_can_break_the_page`. **How to avoid:** Ausnahmen in `VALUES_THAT_MAY_EQUAL_THEIR_KEY` (`test_admin_ui_contract.py:580-682`) mit Begründung; `de_DE` spiegelt `de` (`:682`); JS- und JSON-Datei je Sprache gleich.

### Pitfall 10: Die Pause wirkt wie ein Hänger
**What goes wrong:** Eine OCR-Staffel läuft bis zu ca. 2 x 780 s je Slot (`poller.py:844-847`); die Seite zeigt lange "Indexstaffel abwarten". **How to avoid:** Schritt `pause` sichtbar, Deckel 1800 s mit `pause_timeout`; Doku nennt es. [Owner-Frage 2]

## Code Examples

### Ursachen- und Schrittcodes als geschlossene Menge (probe.py)
```python
# Source: Muster guard.py:48-52 (CAUSES) und precision.py:53-69 (VERDICTS)
STEPS: Final = ("pause", "download", "digest", "model", "ocr_one", "calc", "ocr_n", "cleanup")
VERDICT_FITS: Final = "fits"
VERDICT_NARROW: Final = "narrow"
VERDICT_NOFIT: Final = "nofit"
CAUSES_NARROW: Final = frozenset({"reserve_thin"})
CAUSES_NOFIT: Final = frozenset({
    "memory_short", "model_memory", "memory_unknown", "slot_killed", "timeout",
    "pause_timeout", "download_failed", "download_slow", "digest_mismatch",
    "disk_short", "interrupted", "probe_failed",
})
```

### Rechnung ohne I/O
```python
# Source: abgeleitet aus guard.throttled_slots (guard.py:97-105) und EmbedRunner._need (embedding.py:1658-1667)
def judge(*, slots: int, headroom: int, slot_cost: int, pending: int) -> tuple[str, str]:
    cost = max(slot_cost, OCR_SLOT_COST_BYTES)
    reserve = headroom - (slots * cost + pending)
    if reserve < 0:
        return VERDICT_NOFIT, "memory_short"
    if reserve < GUARD_RESERVE_BYTES:
        return VERDICT_NARROW, "reserve_thin"
    return VERDICT_FITS, ""
```

### PHP-Route (Admin-Klasse, Schutz durch Abwesenheit der Attribute)
```php
// Source: Muster SettingsController::saveRules (SettingsController.php:311-406)
#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'POST', url: '/admin/profile/check')]
public function startCheck(string $profile = '', string $precision = ''): DataResponse {
    if (!in_array($profile, SettingsService::PROFILES, true)
        || !in_array($precision, SettingsService::PRECISIONS, true)) {
        return new DataResponse(['started' => false, 'error' => 'invalid'], Http::STATUS_BAD_REQUEST);
    }
    return $this->probeService->start($profile, $precision, $this->userId());
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Profil nur per `occ config:app:set` | UI mit Probe, occ als dokumentierter Weg ohne Probe | Phase 27 | AR-24-02 verfällt, neues Register |
| Rückweg per occ-Zeile mit Token | Knopf "Erneut prüfen", Token serverseitig | Phase 27 (D-27-12) | AR-26-02 verfällt, Katalogschlüssel weg |
| fp32-Download beim Schlüsselwechsel (occ) | Download in der Probe, Aktivierung über D-25-06-Pfad | Phase 27 (D-27-02) | occ-Weg bleibt unverändert gültig |

## Ursachencodes, Startcodes, UI-SPEC-Deltas

**Verdikt-Ursachen (Endliste):** die acht der UI-SPEC plus fünf neue, jede braucht genau einen Satz:

| Code | Verdikt | DE (Vorschlag) | EN (Vorschlag) |
|---|---|---|---|
| `disk_short` | nicht | `Zu wenig Platz auf dem Datenträger für das fp32-Modell.` | `Not enough disk space for the fp32 model.` |
| `memory_unknown` | nicht | `Der verfügbare Speicher ließ sich nicht lesen.` | `The available memory could not be read.` |
| `interrupted` | nicht | `Die Prüfung wurde durch einen Neustart des Backends unterbrochen.` | `The check was interrupted by a restart of the backend.` |
| `pause_timeout` | nicht | `Die laufende Indexstaffel endete nicht innerhalb von %s.` | `The running indexing batch did not end within %s.` |
| `probe_failed` | nicht | `Die Prüfung brach mit einem Fehler ab.` | `The check stopped with an error.` |

**Startcodes (PHP an JS, keine Verdikte):** `started`, `busy` (Z16), `unreachable` (Z14), `unsupported` (Z15), `invalid`, `rebuilding` (neu, Satz nötig: DE `Der Index wird gerade neu aufgebaut. Die Prüfung ist danach möglich.`), `probe_required` (nur Schreibroute ohne Probe, kein UI-Satz, Programmierfehler-Schutz).

**Poll-Intervall:** 2000 ms (UI-SPEC-Vorschlag bestätigt; ein Poll ist ein GET durch AppAPI ohne Datenbankarbeit im Container).

**Zeitdeckel:** Messteil 120 s, Download inkl. Digest 600 s, Pause 1800 s.

**Sicherheitsabstand:** `GUARD_RESERVE_BYTES` (235 MiB), keine neue Konstante; ein Test pinnt die Gleichheit.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Messteil schlimmstenfalls ca. 70 s auf ARM, 120 s reichen | Pattern 1 | Probe endet auf langsamer ARM-Box mit `timeout`; Deckel in Phase 28 messen |
| A2 | Modell-Kind ohne 512-MB-RLIMIT_AS nötig (ORT reserviert mehr virtuellen Raum) | Pattern 4 | Kind scheitert am AS-Limit, Verdikt fälschlich `model_memory` |
| A3 | Headroom-Stichproben alle 200 ms fangen die Spitze von tesseract | Pattern 2 | Messwert zu niedrig; durch `max(c_mess, 235 MiB)` abgefedert |
| A4 | Scanseite 13-ratsvorlage-scan.pdf ist als Slot-Last repräsentativ genug | Pattern 2 | leichte Seite unterschätzt; Konstante als Untergrenze fängt das |
| A5 | ExApp-Route mit genau einem `<verb>` je Eintrag ist die sichere Form | Pattern 6 | keine, getrennte URLs funktionieren in jedem Fall |

## Open Questions (Owner-Fragen mit Empfehlung) (RESOLVED)

Alle sechs am 29.09.2026 vom Owner entschieden, siehe 27-CONTEXT.md D-27-15 bis D-27-20.

1. **Wächter während der Probe stumm schalten?** (RESOLVED: D-27-15) Ein vom Kernel getötetes Probe-Kind senkt sonst das gewählte Profil ab (Pitfall 3).
   - Empfehlung: Ja. Eskalation während der Probe und einen Tick danach nur neu basieren; die Indexierung ist pausiert, also gibt es keine Betriebslast, gegen die der Wächter schützen müsste. Die Probe meldet den Kill selbst als `slot_killed`.
2. **Pause-Deckel 1800 s akzeptabel?** (RESOLVED: D-27-16) Eine laufende OCR-Staffel kann im schlimmsten Fall bis zur Lease dauern.
   - Empfehlung: Ja, mit sichtbarem Schritt "Indexstaffel abwarten". Alternative wäre, die Staffel für die Probe abzubrechen; das widerspricht D-27-05 ("endet sauber").
3. **Vom Admin abgelegte fp32-Datei bei knapp/nicht löschen?** (RESOLVED: D-27-17) D-27-02 sagt "Datei gelöscht", D-25-06 schützt eine abgelegte Datei.
   - Empfehlung: Nur eine von der Probe selbst geholte Datei löschen; eine abgelegte bleibt (sonst muss der Admin sie auf einer Offline-Box erneut hineinkopieren). Die Karte sagt dann nicht "wieder gelöscht".
4. **Reindex-Dauer ohne vorherige Probe?** (RESOLVED: D-27-18)
   - Empfehlung: Kurzform ohne Dauer, bis eine Probe auf dieser Box eine Rate gemessen hat. Eine Betriebsrate aus der Einbettungsspur wäre möglich, kostet aber eine neue Messstelle im heißen Pfad.
5. **IN-01 und IN-02 aus 26-REVIEW in Phase 27 mitfixen?** (RESOLVED: D-27-19)
   - Empfehlung: Ja, beide liegen im Pfad der Probe (Token-Snapshot, Pool im Shutdown).
6. **Fünf neue Ursachensätze plus `rebuilding` in die UI-SPEC aufnehmen?** (RESOLVED: D-27-20)
   - Empfehlung: Ja, als UI-SPEC-Delta vor dem Plan-Schnitt; ohne sie zeigt die Seite in diesen Fällen nur Chip plus "Nichts gespeichert".

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | Python-Gates, Tests | ✓ | 0.11.7 | nein |
| Docker | Image-Build, cgroup-Tests | ✓ | 29.5.2 | CI |
| PHP lokal | php -l, PHPUnit | ✗ | nicht nötig | CI `php.yml` (Syntax + PHPUnit), `php -l` im Container |
| Node | nicht nötig (kein JS-Testlauf) | ✓ | 22.21.0 | nicht verwendet |
| cgroup v2 | echte Headroom-Messung | nur Linux/CI/Box | n/a | Windows-Tests mit injizierten Lesern (Muster `memory_guard`) |

**Missing dependencies with no fallback:** keine.
**Missing dependencies with fallback:** PHP lokal fehlt, CI deckt es.

## Test-Belege je Erfolgskriterium

(`workflow.nyquist_validation` ist `false`; daher keine vollständige Validation Architecture, nur die Zuordnung.)

| SC | Beleg | Art | Befehl / Ort |
|----|-------|-----|------|
| SC1 Auswahlfeld 3 Profile, zwei Knöpfe, ohne Klick Sparsam, kein Erweitert | Template-Vertrag: genau ein `select` mit drei `option`, IDs der UI-SPEC, kein Aufklapp-Element; Gate C (JS baut kein Markup) | pytest textuell | `uv run pytest -q tests/test_admin_ui_contract.py` |
| SC1 ohne Klick bleibt Sparsam | `profileStored()` false -> `profile()` economy, keine Schreibwirkung beim Rendern ohne pending | PHPUnit | `php/tests/Unit/SettingsServiceTest.php` (neu), `ProbeServiceTest.php` (neu) |
| SC2 echte Probe, Verdikte, Ursachen, Speichern nur bei passt | `probe.judge` Grenzfälle (reserve -1, 0, 234 MiB, 235 MiB), Schrittfolge mit Fakes (Pool, Headroom, Download), Commit nur bei `fits` und passender Id | pytest + PHPUnit | `tests/test_probe.py`, `tests/test_probe_run.py`, `ProbeServiceTest.php` |
| SC2 echte OCR auf echtem Kind | ocr_one mit echtem `ExtractionWorker` und der Scanseite, Text nicht leer | pytest (langsam, Linux) | Muster `test_sandbox.py`; Headroom injiziert |
| SC3 Vorab-Rechnung verhindert OOM | Vorab-Tor verweigert Lauf bei kleinem H0 (kein Kind gestartet, Zähler) | pytest | `tests/test_probe_run.py` |
| SC3 eine Probe gleichzeitig | zweiter Start 409 busy, Lock | pytest (TestClient) | `tests/test_probe_endpoint.py` |
| SC3 Zeitdeckel | Deckel über Fake-Kind `sleep`-Probe (`sandbox._run_probe`), Download-Deckel über hängenden Fake-Fetch | pytest | `tests/test_probe_run.py` |
| SC3 Pause und Wiederaufnahme | Poller hält, laufende Staffel endet mit Quittung, danach neue Staffel; Ausnahme im Probe-Task hebt Pause auf | pytest | `tests/test_poller.py` (erweitern) |
| SC3 ADMIN | info.xml-Blöcke `^/probe$`, `^/probe/state$` tragen ADMIN; Gate B für die neuen FrontpageRoutes; Live: Nicht-Admin bekommt 403 | pytest + CI-Integration | `tests/test_probe_endpoint.py`, `test_php_trust_boundary.py`, `.github/workflows/integration.yml` (neuer Schritt mit `occ user:add` und curl) |
| SC4 Kataloge | alle Katalog-Gates, entfernter Schlüssel fehlt in allen 16 Dateien, PHP/JS-Map-Gleichheit der Codes | pytest | `tests/test_admin_ui_contract.py` |
| nur Live/CI | echte cgroup-Messung, OOM-Kill eines Probe-Kinds, fp32-Download aus dem Release, ARM-Zeiten | CI Linux, Phase 28 | `resilience.yml`/`integration.yml`, Phase 28 Messbox |

**Wave 0:** neue Testdateien `test_probe.py`, `test_probe_run.py`, `test_probe_endpoint.py`, PHPUnit `ProbeServiceTest.php`, `ProfileSettingsControllerTest.php`, `SettingsServiceTest.php` (profileStored, Abwärtsweg-Prüfung).

## Security Domain

AR-24-02 verfällt. Neues Register für Schreibroute und Probe:

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | ja (indirekt) | Nextcloud-Sitzung; Container per AppAPI-Signatur (`AppAPIAuthMiddleware`, `main.py:1132`) |
| V3 Session Management | ja | CSRF über `requesttoken`, SecurityMiddleware ohne Verb-Ausnahme |
| V4 Access Control | ja | FrontpageRoute ohne NoAdminRequired/PublicPage/NoCSRFRequired/ExAppRequired (Gate B); info.xml ADMIN als Tiefenverteidigung |
| V5 Input Validation | ja | strict `in_array` gegen PROFILES/PRECISIONS in PHP, pydantic `Literal` im Container, Probe-Ergebnis in PHP gegen geschlossene Mengen und Zahlenbereiche |
| V6 Cryptography | ja (Integrität) | sha256-Pin von fp32 und Scanseite, `secrets.token_hex` für Probe-Id, `hash_equals`/`compare_digest` wo verglichen wird |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| CSRF auf Start/Speichern | Tampering | kein NoCSRFRequired, Gate B |
| Nicht-Admin startet Probe/speichert | EoP | Admin-Pflicht der SecurityMiddleware, Live-403-Test |
| Browser behauptet "passt" | Tampering | Commit nur aus Container-Ergebnis mit gebundener Id und Ziel |
| Probe-Dauerfeuer (Indexierung dauerhaft pausiert, Downloads) | DoS | Einzelflug, drei Deckel, Admin-only; fp32-Download entfällt bei geprüfter Datei |
| Download-Missbrauch | Tampering/Spoofing | feste URL, fester sha256 und Länge (`weights.py:52-58`), kein Nutzer-URL-Feld |
| Token-Leck | Info Disclosure | Token nicht mehr im Browser; nur serverseitig gelesen |
| Container-Wörter als Seitentext | Spoofing (XSS) | nur Codes, PHP/JS-Maps, `p()`/`textContent` |
| Probe-Kind als RCE-Ziel | EoP | Scanseite ist eigene, gepinnte Datei; Kinder gehärtet wie Phase 26; Modell-Kind schält secrets |
| Logs | Info Disclosure | statische Sätze, Typnamen, keine Werte/Pfade/URLs |

## Sources

### Primary (HIGH confidence)
- Bestandscode, am Code gelesen: `profile.py`, `memory_guard.py`, `guard.py`, `precision.py`, `extract/sandbox.py`, `extract/pool.py`, `worker/poller.py`, `worker/embedding.py`, `embed/weights.py`, `api/status.py`, `main.py`, `config.py`, `backend/appinfo/info.xml`, `php/lib/Controller/{Settings,Profile}Controller.php`, `php/lib/Service/{Settings,ExApp,AdminView}Service.php`, `php/templates/admin.php`, `php/js/admin.js`, `tests/test_php_trust_boundary.py`, `tests/test_readonly_gate.py`, `tests/test_admin_ui_contract.py`
- `docs/measurements/2026-09-fp32-speicher/README.md` (Methode, RssAnon-Werte, Raten)
- Nextcloud Server: `lib/private/AppFramework/Middleware/Security/SecurityMiddleware.php` (CSRF ohne Verb-Ausnahme, Admin-Pflicht), `lib/public/IAppConfig.php` stable33 (hasKey, getValueArray/setValueArray seit 29)

### Secondary (MEDIUM confidence)
- `docs/performance.md` Zeilen 125, 1202 (OCR-Sekunden je Seite) als Grundlage der Deckel

### Tertiary (LOW confidence)
- ARM-Dauer des Modell-Kinds und AS-Bedarf von onnxruntime (A1, A2), nicht gemessen

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, keine neue Abhängigkeit, alle Bausteine am Code belegt
- Architecture: HIGH für Routen/Commit/Pause, MEDIUM für die Rechnung (Ableitung, Phase 28 misst)
- Pitfalls: HIGH, alle an Codezeilen belegt

**Research date:** 2026-09-29
**Valid until:** 2026-10-29 (Bestand ändert sich nur durch diese Phase)
