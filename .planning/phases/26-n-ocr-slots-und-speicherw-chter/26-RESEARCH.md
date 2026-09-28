# Phase 26: N OCR-Slots und Speicherwächter - Research

**Researched:** 2026-09-28
**Domain:** Prozess-Parallelität (spawn-Kinder, asyncio), Warteschlangen-Leasing (PHP/Python-Kopplung), Linux cgroup v2 Speicher-Ereignisse, Scheduler-Priorität
**Confidence:** HIGH für Code- und Kernel-Befunde (gelesen bzw. im Kernel-Quelltext verifiziert), MEDIUM für die Wächter-Schwellen (begründet, nicht gemessen)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Vorentscheide, die hier tragen und NICHT neu verhandelt werden: D-24-03 (Slotformel 3.1, Obergrenzen Standard 4 / Leistung 16, Sparsam fest 1 Slot), D-24-07 (gespeichertes Profil bleibt bei Schrumpfung, gewaehlt vs. wirksam gemeldet), D-25-11 (RAM-Bedingung nicht erfuellt = seriell weiter, nicht warten), D-25-12 (embed_slots = 2 fuer Leistung wird erst mit dieser Phase wirksam). Basis fuer den Waechter ist der Phase-25-Leser `memory_guard.headroom_bytes` (anon statt memory.current, cgroup-v1-Fallback auf MemAvailable).

#### Speicherwaechter: Eskalation und Rueckweg (PAR-03)
- **D-26-01 (Owner, 28.09.2026):** Nach dem Ausloeser senkt der Waechter NUR die wirksame Stufe, nie das gespeicherte Profil (D-24-07 gilt). Die Absenkung wird als EIGENER persistenter Merker abgelegt (z. B. appconfig-Schluessel ueber die bestehende Schreib-/Leseroute), damit sie einen Neustart nach OOM-Kill ueberlebt und keine Absturzschleife entsteht. Statusroute und Adminseite melden gewaehlt vs. wirksam plus Ursache.
- **D-26-02 (Owner, 28.09.2026):** Erste Eskalationsstufe (Slot-Drossel) ist rechnerisch je Runde: Vor jedem Staffel-Start prueft der Poller gegen `headroom_bytes`, ob ein weiterer Slot (Kosten_je_Slot + Reserve) passt; wenn nein, startet er weniger Kinder. Kein neues Kernelsignal noetig.
- **D-26-03 (Owner, 28.09.2026):** Ausloeser der Stufen-Absenkung: zwei memory.events-max-Ereignisse (Delta-Zaehlung) innerhalb eines gleitenden Fensters (Groessenordnung 10 Minuten, endgueltigen Wert legt die Research fest) ODER ein einzelner beobachteter OOM-Kill (Sandbox-Kind vom Kernel gekillt bzw. memory.events oom_kill steigt) senken sofort um eine Stufe.
- **D-26-04 (Owner, 28.09.2026):** Rueckweg nur durch Admin-Aktion: Der Absenk-Merker bleibt, bis der Admin das Profil neu setzt oder bestaetigt (occ, ab Phase 27 die Settings-UI mit Probe). Kein automatisches Anheben (kein Flattern); die Seite nennt Stufe, Ursache und den Rueckweg.

#### Anspruchsgroesse, Sperrfrist und K6-Uebergang (PAR-02)
- **D-26-05 (Owner, 28.09.2026):** KIND_BATCH[ocr] wird FEST auf 32 erhoeht (2 x Obergrenze 16 Slots Leistung): Doppelpuffer, damit Slots waehrend des naechsten Anspruchs Nachschub haben. Kein neuer Routen-Parameter; der Paritaetstest QueueService::KIND_BATCH gegen config.py bleibt einfach.
- **D-26-06 (Owner, 28.09.2026):** Sperrfrist-Neuableitung per Formel: Sperrfrist = ceil(Batchzeilen / wirksame Slots) x Datei-Zeitdeckel (aus OCR_MAX_PAGES x Seiten-Timeout) + Marge. Sparsam (1 Slot, 32 Zeilen) bekommt automatisch eine lange Frist, Leistung eine kurze. Die Formel lebt im Container.
- **D-26-07 (Owner, 28.09.2026):** Alter Companion (K6-Uebergangsfenster): adaptiv, Slots = min(N, gelieferte Zeilen). Der Poller startet nie mehr Kinder, als der Anspruch Zeilen geliefert hat; kein Versionscheck, kein Sonderpfad. Mit neuem Companion entfaltet sich N von selbst.
- **D-26-08 (Owner, 28.09.2026):** Der Kill-Test in Linux-CI (SC2, N >= 4) deckt BEIDE Faelle ab: (1) SIGKILL auf den Hauptprozess mitten in einer halben Staffel (der OOM-Kill-Fall) und (2) Kill eines einzelnen Sandbox-Kindes, waehrend die anderen weiterlaufen. Beide enden mit: jede Datei genau einmal im Index, keine Zeile verloren.

#### Messung des Durchsatzfaktors (SC3)
- **D-26-09 (Owner, 28.09.2026):** Phase 26 misst NUR in CI: Leiter 1 vs 2 vs 4 Slots auf dem arm64-CI-Runner (4 Kerne) mit dem bestehenden Messwerkzeug und Korpus der Phase-22-Anfahrt; der Zugewinn je Stufe wird gegen die Rauschgrenze 1,05 (Vorarbeit 2.5) gehalten, Rohdaten committet. Sparsam liest weiterhin mit genau einem Slot, der Pin-Test bleibt gruen.
- **D-26-10 (Owner, 28.09.2026, FESTGESCHRIEBEN FUER PHASE 28):** Die AWS-Matrix-Messung laeuft NICHT in Phase 26, sondern einmal in Phase 28 am gebauten Produkt (MESS-10, mit Rechenblatt und Kostendeckel vor dem Boxstart). Festgeschriebene Entscheide: Messbox auf AWS-Guthaben, Konto infranodedev 450315222812 (104,29 USD gueltig bis 04.09.2027; NICHT das Konto Cherif83); Matrix 4/8/16/32 Kerne x86 plus 16K-ARM m7g (Baseline-vergleichbar); vCPU-Quota eu-central-1 = 32, also seriell fahren (Erhoehung auf 48 nur, falls seriell zu langsam); Korpus-Snapshot snap-03f1d1d9ad9262704 bleibt bis dahin Messkorpus; NACH der Phase-28-Messung ALLES abbauen inklusive Snapshot (null laufende Kosten).

#### Slot-Prioritaet os.nice (A12, Issue #19)
- **D-26-11 (Owner, 28.09.2026):** os.nice kommt FEST in diese Phase (Feldbeleg Issue #19: UI-Timeout unter Indexlast). Umfang: NUR die N Sandbox-Kinder starten mit nice 10 (tesseract-Subprozesse erben die Stufe). Der Hauptprozess (Suche, API, Einbettung) bleibt normal; die Einbettung wird weiter ueber Threadzahl/Batchgroesse gezuegelt. Das nice gilt in ALLEN Profilen, auch Sparsam mit einem Slot (der #19-Beleg kam aus dem Ein-Slot-Betrieb).
- **D-26-12 (Owner, 28.09.2026):** Beleg zweiteilig: (1) CI-Zusicherung, dass jedes Kind mit der Stufe laeuft (inklusive Vererbung an tesseract); (2) einmalige Live-Latenzprobe auf dem nc35-Harness (status.php/Suche unter Volllast mit und ohne nice), Ergebnis in den Phasen-Beweis und als Zahlbeleg-Grundlage fuer die Issue-#19-Antwort.

### Claude's Discretion
- OOM-Kette R1 im Detail (memory.events-Semantik unter cgroup v2, Delta-Zaehlung, Verhalten in der HaRP-Umgebung, Verhalten auf v1-Hosts ohne Signal) und der endgueltige Fensterwert fuer D-26-03: Research legt fest.
- Abbruchsemantik halber Staffeln im Detail (Reihenfolge ack vs. Index-Commit unter N Slots, Zusammenspiel mit dem retries-Zaehler in QueueMapper), solange D-26-08 beweisbar haelt.
- Platzierung und Form der Semaphore, Aufteilung Anspruchszeilen -> Kinder (Work-Stealing vs. feste Zuteilung), Form der Sperre um IndexBatchWriter.add().
- Form der Sperren um die geteilte Embedding-Engine fuer embed_slots = 2 (D-25-12) und die Mitnahme des idle-Guards, falls Phase 25 ihn nicht abgedeckt hat.
- Genauer Schluesselname und Wertemenge des Absenk-Merkers (D-26-01), Wortlaut der Status-/Ursachen-Meldungen (Code Englisch; neue Seitentexte in allen acht Katalogen im Gleichstand, Katalog-Gate haelt).
- Schnitt des CI-Kill-Tests (Harness, Korpusgroesse, Laufzeitbudget) und der CI-Messleiter (D-26-09).

### Deferred Ideas (OUT OF SCOPE)
- AWS-Matrix-Messung, Quota-Erhoehung auf 48, Snapshot-Abbau: Phase 28 (D-26-10 haelt die Entscheide fest).
- Issue #18 Fix-Kandidaten (JPG-Verdikt, HEIF, Download-Groessenpruefung): weiterhin nicht Teil von v1.4-Phase-26; wartet auf budachsts Antwort, Slot-Entscheid beim Owner (pending todo vom 28.09.).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PAR-02 | N OCR-Slots (H2): Semaphore, N Sandbox-Kinder mit je eigener Pipe und eigenem Zaehler, Sperre um IndexBatchWriter.add(), KIND_BATCH[ocr] >= N; die Zusagen "mindestens einmal ausliefern, hoechstens einmal indexieren" halten unter Parallelitaet | Muster 1 bis 5 (Pool, Staffel, Writer-Sperre, Zeilenbeschnitt), Befund B (Genau-einmal-Analyse), Befund C (Sperrfrist), Pitfalls 1 bis 7, Kill-Test-Schnitt |
| PAR-03 | Ein Speicherwaechter drosselt Slots bei knapper cgroup; wiederholtes memory.events max oder ein OOM-Kill senkt das Profil selbsttaetig um eine Stufe, sichtbar gemeldet | Befund A (OOM-Kette R1), Muster 6 bis 8 (Drossel, Wächter-Task, Merker in state.db, Rückweg per Token), Pitfalls 8 bis 11 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Qualitätsgates: ruff-Vollregelsatz, `ruff format --check`, pyright basic, vulture (min-confidence 80), lokal grün vor Commit. pyright lokal mit `PYRIGHT_PYTHON_FORCE_VERSION=latest` (Owner-Regel 19.09.).
- Python 3.13 + uv; Code, Bezeichner und Log-Texte Englisch; echte Umlaute nur in deutscher Prosa, nie in Code, Keywords, Pfaden oder YAML.
- Hardware-Ziel 4 bis 8 GB RAM, ARM-tauglich, CPU-only; RAM-Budget hart einplanen.
- Security/Privacy: Berechtigungsdurchgriff strikt, keine Inhalte verlassen den Server, kein Telemetrie-Phoning. Log-Zeilen tragen nur Zähler und Reason-Codes, nie Pfad, Titel, Text (T-02-107, Grep-Test im Poller).
- Gate A (`tests/test_readonly_gate.py`): nur `nc/client.py` spricht Nextcloud; Bezeichner `delete`, `move`, `copy`, `upload`, `mkdir`, `makedirs`, `trash`, `set_user` sind paketweit verboten. Neue Namen danach wählen (Vorbild `drop_document`).
- Owner-Regel: nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Phasenabschluss fixen.
- Kurze Produkttexte: Adminseiten-Texte und docs knapp, Faktenliste; neue Seitentexte in allen acht Katalogen im Gleichstand.
- Sparsam wird Wert für Wert gegen die heutigen Konstanten gepinnt (PROF-02); die Store-Messzahl und `test_store_metadata.py` bleiben unverändert.
- Companion-Änderungen reisen erst mit Release 1.4.0 (K6); der Container muss bis dahin mit dem alten Companion laufen.
- Fremde PRs/Issues nicht eigenmächtig beantworten; die Issue-#19-Antwort erst nach Owner-Freigabe.

## Summary

Der heutige Poller ist eine asyncio-Schleife mit genau einem langlebigen spawn-Kind hinter der Fassade `extract_guarded` (Modul-Global `_WORKER`). Eine Runde ist: Anspruch, Zeilen seriell abarbeiten, **ein** Commit, Verdikte, Übergabe, Quittung. Diese Reihenfolge ist die tragende Invariante und bleibt unter N Slots unverändert; N Slots ändern nur Schritt 1 (die Extraktion der OCR-Zeilen läuft nebenläufig). "Höchstens einmal indexieren" hängt nicht an der Reihenfolge, sondern am Upsert in `IndexBatchWriter.add()` (Löschen per `file_id`-Term vor dem Einfügen) und an der Eindeutigkeit von `file_id` im Anspruch (Unique-Index der Warteschlange). "Mindestens einmal ausliefern" hängt am Lease der PHP-Seite und daran, dass die Quittung nach dem Commit kommt. Beides überlebt N Slots, **wenn** drei neue Löcher geschlossen werden: (1) ein einzeln gekilltes Kind oder ein gekillter tesseract-Enkel erzeugt heute ein falsches Endverdikt (`failed(corrupt)` bzw. `failed(ocr_failed)`), das die Zeile quittiert und die Datei verliert; (2) der tantivy-Writer und seine Zähler sind nicht threadsicher; (3) das Lease von 1800 s passt nicht zu 32 OCR-Zeilen bei wenigen Slots.

Die drei Research-Flags ergeben drei harte Befunde, die der Planer kennen muss. **Erstens (R1):** `memory.events max` zählt laut Kernel-Quelltext *vor* dem Reclaim, also auch dann, wenn nur Seitencache zurückgeholt wird. Das Projekt hat das selbst gemessen: `max` stand bei 2796, während alle Schadenszähler bei null blieben (`embed/engine.py`, Lastlauf 05.09.). Ein roher Delta-Zähler "2x max in 10 min" würde auf jeder Box mit gesetztem `memory.max` dauernd auslösen. Das Ereignis muss qualifiziert werden (Delta > 0 **und** anon-Headroom unter der Reserve). **Zweitens (Sperrfrist):** Das Lease wird ausschließlich in PHP durchgesetzt (`QueueMapper::LOCK_TIMEOUTS`, Vergleich bei jedem Anspruch). Ohne neuen Routen-Parameter kann der Container keine eigene Frist setzen. D-26-05 und D-26-06 lassen sich nur gemeinsam erfüllen, wenn die Formel im Container die Richtung umkehrt: aus dem festen Lease folgt, wie viele OCR-Zeilen er behält (2 je Slot), der Rest geht sofort per `unlock` (mit Retry-Erstattung) zurück. **Drittens (Anspruch):** `KIND_BATCH[ocr] = 32` ohne weitere Bedingung verändert den Sparsam-Anspruch (OCR frisst das Zeilenbudget, Einbettungszeilen verhungern im Lane `all`) und gibt einem 1.3-Container 32 OCR-Zeilen auf einmal. Die saubere Form ohne neuen Parameter ist `KIND_BATCH[ocr]` je Lane: 32 im Lane `index`, 2 im Lane `all`.

Zu os.nice (D-26-11) ein ehrlicher Befund: Unter Gruppen-Scheduling wirkt ein nice-Wert nur relativ zu Threads **derselben Task-Gruppe** (man 7 sched). Nextcloud läuft in allen Zielaufbauten (AIO, compose-harp) in einem **anderen Container, also einer anderen cgroup**. nice 10 in den Findling-Kindern schützt deshalb sicher den Findling-Hauptprozess (Suche für die Unified Search mit 2-s-Timeout, /status, Heartbeat), aber voraussichtlich **nicht** `status.php` des Nextcloud-Containers. Die Live-Probe D-26-12 muss beide Latenzen getrennt messen, sonst belegt sie das Falsche.

**Primary recommendation:** Pool aus N `ExtractionWorker`-Instanzen hinter einer asyncio-Slot-Schranke mit eigenem ThreadPoolExecutor; OCR-Zeilen nebenläufig, alles andere seriell wie heute; Writer mit `threading.Lock`; Kinder mit nice 10 und `oom_score_adj` 1000; von außen gekilltes Kind = kein Verdikt, sondern Solo-Wiederholung; Absenk-Merker in der eigenen `state.db` (nicht appconfig), Rückweg über einen Bestätigungs-Token im Profil-Route; Wächter-Ereignis = Tick mit `Δmax > 0` und anon-Headroom unter Reserve, Fenster 600 s.

## Architektonische Verantwortungskarte

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| OCR-Zeilen nebenläufig lesen (N Kinder) | Container: Worker (`worker/poller.py`) | Container: Extraktion (`extract/pool.py` neu, `extract/sandbox.py`) | Nur der Poller kennt Art und Frist eines Jobs; das Kind bleibt der einzige Ort, an dem Fremdbytes auf C-Bibliotheken treffen |
| Schreibsperre Index | Container: `index/writer.py` | - | Die Sperre gehört in die Klasse, die den nicht threadsicheren Writer und die Zähler hält |
| Anspruchsgröße je Art und Lane | Companion (PHP `QueueService::KIND_BATCH`) | Container spiegelt in `config.py` (Paritätstest) | Die PHP-Seite verteilt die Zeilen; der Container kann nur nehmen oder zurückgeben |
| Lease (Sperrfrist) | Companion (PHP `QueueMapper::LOCK_TIMEOUTS`) | Container: Zeilenbeschnitt nach Formel | PHP vergleicht `locked_at` bei jedem Anspruch; der Container hält seine Arbeit darunter |
| Slot-Drossel je Runde | Container: Poller + `memory_guard.headroom_bytes` | - | D-26-02 |
| OOM-Erkennung und Stufenabsenkung | Container: neues neutrales Modul `guard.py` + Wächter-Task | Container: Pool meldet Kind-Kills | Kernelzähler und Exitcodes sind nur im Container sichtbar |
| Persistenter Absenk-Merker | Container: eigene `state.db` (meta) | - | Übersteht Neustart und OOM-Kill; kein Schreibweg nach Nextcloud nötig (Gate A, AR-24-02) |
| Rückweg (Admin bestätigt) | Companion: appconfig-Schlüssel + Profil-Route | Container liest ihn je Runde | Nur Admins schreiben appconfig; der Container liest wie heute Profil und Präzision |
| Anzeige Stufe/Ursache | Container: `/status` Profilblock | Companion: Adminseite, acht Kataloge | Gleiche Linie wie D-24-07 (gewählt vs. wirksam) |
| nice/oom_score_adj der Kinder | Container: `_child_main` | - | Nur das Kind selbst kann sich ohne Privileg herabstufen |

## Standard Stack

### Core
Keine neue Abhängigkeit. Alles, was diese Phase braucht, ist Standardbibliothek oder schon im Projekt.

| Baustein | Version | Zweck | Warum |
|---------|---------|-------|-------|
| `multiprocessing` (spawn), `os.nice`, `os.getpriority` | Python 3.13 stdlib | N Kinder, Priorität, Test der Vererbung | bestehendes Muster in `extract/sandbox.py` [VERIFIED: codebase] |
| `concurrent.futures.ThreadPoolExecutor` (eigene Instanz) | stdlib | Warten auf Kind-Pipes ohne den Default-Executor der Suche zu blockieren | Default `max_workers = min(32, process_cpu_count()+4)` seit 3.13 [CITED: docs.python.org/3.13/library/concurrent.futures.html] |
| `asyncio.Condition` | stdlib | größenveränderliche Slot-Schranke (asyncio.Semaphore kann nicht schrumpfen) | [ASSUMED: stdlib-Verhalten, im Test absichern] |
| `threading.Lock` | stdlib | Sperre um `IndexBatchWriter.add/drop_document/flush`, um den Chunker und um SQLite-Schreibzugriffe der Einbettungsspur | [VERIFIED: codebase, gemeinsame Verbindungen mit `BEGIN IMMEDIATE`] |
| cgroup v2 `memory.events`, `memory.stat`, `/proc/self/oom_score_adj` | Kernel | Wächter-Signale, Opferwahl beim OOM | [VERIFIED: git.kernel.org mm/memcontrol.c, mm/oom_kill.c, fs/proc/base.c] |

### Alternatives Considered
| Statt | Möglich | Tradeoff |
|------------|-----------|----------|
| Eigener Pool aus `ExtractionWorker` | `multiprocessing.Pool` / `ProcessPoolExecutor` | Kann einen hängenden C-Aufruf nicht abbrechen, kein RLIMIT_AS je Kind, keine Recycling-Regeln; im Moduldoc von `sandbox.py` ausdrücklich verworfen [VERIFIED: codebase] |
| Zeilenbeschnitt im Container (Lease fest) | Lease-Parameter am Anspruch, PHP schreibt `locked_at` in die Zukunft | Erfüllt "Sparsam lange Frist" wörtlich, braucht aber einen neuen Routen-Parameter (gegen D-26-05), verlängert Sparsam-Runden auf Stunden (acl/delete warten, Pitfall 6) und sperrt nach einem OOM-Kill 32 Zeilen bis zu 8 h. Siehe Offene Frage O1 |
| qualifiziertes `max`-Ereignis | `memory.pressure` (PSI) als Auslöser | Besseres Signal, aber nicht das vom Owner gewählte; als Qualifizierer denkbar, nicht nötig |
| Merker in `state.db` | appconfig per `nc_py_api` `appconfig_ex` | Landet in der AppAPI-Tabelle der ExApp, die der Companion nicht über öffentliche API liest; bräuchte eine Schreibausnahme in Gate A. Nicht nötig |

**Installation:** keine.

## Package Legitimacy Audit

Diese Phase installiert keine externen Pakete. slopcheck wurde daher nicht gefahren.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (keine) | - | - | - | - | - | - |

**Packages removed due to slopcheck [SLOP] verdict:** keine
**Packages flagged as suspicious [SUS]:** keine

## Architecture Patterns

### Systemdiagramm (Datenfluss einer Staffel unter N Slots)

```
 Nextcloud-Warteschlange (PHP)
   claim(n=32, lane=index)  --KIND_BATCH je Lane-->  acl/delete/metadata/content/ocr (bis 32)
        |
        v
 Poller.run_once
   1. Drossel: S = min(profil.ocr_slots, guard.cap, 1 + floor((headroom - reserve)/cost), OCR-Zeilen + c)
   2. Zeilenbeschnitt: behalte min(OCR-Zeilen, 2 x S_ocr), Rest -> unlock (retries-1)  ----> PHP
   3. OCR-Tasks starten ---------------------------+
      je Task: Slot nehmen -> fetch (Gateway) ->   |   SlotPool (N ExtractionWorker, je eigene Pipe,
               pool.run (eigener Executor) --------+-->  eigener Zähler, nice 10, oom_score_adj 1000)
               -> writer.add (threading.Lock)      |        |  Kind -9 von außen?  --> ChildKilled
   4. übrige Zeilen seriell wie heute              |        v
      (content nutzt ebenfalls einen Slot)         |   Solo-Wiederholung nach der Barriere
   5. Barriere: alle OCR-Tasks fertig  <-----------+   (zweiter Kill -> failed(out_of_memory))
   6. flush (EIN Commit)  -> 7. Verdikte (state.db) -> 8. Übergabe ocr/embed -> 9. Quittung
        ^                                                                          |
        |                                                                          v
 Wächter-Task (Tick 15 s): memory.events + headroom  --Auslöser-->  guard.cap = Stufe-1
        ^   Pool meldet Kind-Kills                                   Merker in state.db meta
        |                                                            /status + Adminseite
 Profil-Route: profile, precision, confirmed(Token)  --Token passt-->  Merker löschen
```

### Empfohlene Dateistruktur

```
backend/src/findling/
├── extract/
│   ├── sandbox.py        # ExtractionWorker: nice/oom_score_adj im Kind, ChildKilled-Erkennung
│   └── pool.py           # NEU: SlotPool (thread-sichere Freiliste), SlotGate (asyncio, größenveränderlich)
├── guard.py              # NEU, neutral wie profile.py/lane.py: Stufe, Ursache, Token, Drosselzahl
├── memory_guard.py       # + memory_events(root) (v2, nie werfend, nie loggend)
├── profile.py            # effective() berücksichtigt guard.cap
├── worker/
│   ├── poller.py         # Staffel mit OCR-Tasks, Zeilenbeschnitt, Barriere, Solo-Wiederholung
│   ├── watch.py          # NEU: Wächter-Task (Tick, Fenster, Persistenz-Callback)
│   └── embedding.py      # EmbedRunner: bis zu embed_slots Zeilen nebenläufig
├── index/writer.py       # threading.Lock um add/drop_document/flush/Zähler
├── config.py             # OCR_ROWS_PER_SLOT, OCR_CLAIM_BATCH_INDEX_LANE, GUARD_*, SANDBOX_NICE ...
└── api/status.py         # Profilblock + GuardReport
php/lib/Service/QueueService.php   # KIND_BATCH[ocr] je Lane
php/lib/Service/SettingsService.php + Controller  # confirmed-Token in der Profil-Antwort
php/... AdminView/Template + l10n (8 Kataloge)
```

### Befund A: OOM-Kette R1 (memory.events, Erkennung, HaRP, v1)

**Semantik der Zähler** [VERIFIED: docs.kernel.org/admin-guide/cgroup-v2.html; git.kernel.org mm/memcontrol.c try_charge_memcg, mm/oom_kill.c __oom_kill_process]:
- `max`: "about to go over the max boundary". Im Quelltext wird `MEMCG_MAX` in `try_charge_memcg` **vor** `try_to_free_mem_cgroup_pages` gezählt, unabhängig davon, ob der Reclaim reicht. Auf einer Box mit gesetztem `memory.max`, deren Seitencache (tantivy-mmap, Scratch-Downloads) an der Grenze steht, steigt `max` bei jedem Laden über der Grenze. Projekteigener Beleg: `max` = 2796 bei null Schäden (`embed/engine.py` Zeile 10, `embed/model.py` Zeile 125) [VERIFIED: codebase].
- `oom`: Ladung nach allen Reclaim-Versuchen gescheitert, OOM-Pfad betreten (`mem_cgroup_oom`). Praktisch gleichzeitig mit `oom_kill`, also keine Vorwarnung.
- `oom_kill`: in `__oom_kill_process` per `memcg_memory_event_mm(mm, MEMCG_OOM_KILL)` für das **Opfer** gezählt, auch beim globalen OOM-Killer des Hosts ("killed by any kind of OOM killer"). Alle Felder sind hierarchisch.
- `high`: nur mit gesetztem `memory.high`; Docker setzt es nicht [ASSUMED].
- Die Datei existiert nur in Nicht-Root-cgroups. Im Container mit privatem cgroup-Namespace (Docker-Standard unter v2) ist `/sys/fs/cgroup` die eigene cgroup [ASSUMED: Docker-Standard, von Phase 24 für `memory.max` implizit bestätigt].

**Qualifiziertes Ereignis (Empfehlung für D-26-03):** Ein "max-Ereignis" ist ein Wächter-Tick, in dem `Δmax > 0` **und** `headroom_bytes()` kleiner als `GUARD_RESERVE_BYTES` (= `OCR_SLOT_COST_BYTES`, 235 MiB) ist. Nur dann drückt der Reclaim wirklich auf anonymen Speicher und nicht auf Seitencache. Zwei solche Ticks mit mindestens 60 s Abstand innerhalb von **600 s** senken um eine Stufe. Begründung des Fensters: Ein einzelner großer Scan erzeugt einen Schub von Ereignissen in Sekunden; zwei getrennte Schübe in zehn Minuten sind wiederkehrender Druck. Die Zählung je Tick (nicht je Zählerinkrement) macht die Schwelle unabhängig von der Rate des Kernels [MEDIUM: begründet, nicht gemessen; Fake-cgroup-Test Pflicht].

**OOM-Kill beobachtet** = Kind oder tesseract-Enkel endet mit SIGKILL, den der Elternteil nicht selbst geschickt hat (kein Timeout-Pfad), **und** (`Δoom_kill > 0` seit dem letzten Tick **oder** `memory.events` nicht lesbar). Ist der Zähler lesbar und steigt nicht, war es ein fremder Kill (z. B. der Test D-26-08 Fall 2): Solo-Wiederholung ja, Stufenabsenkung nein.

**Wen der Kernel tötet:** Die Opferwahl nimmt den Prozess mit der höchsten Badness (RSS plus `oom_score_adj`-Anteil). Der Hauptprozess hat rund 1257 MiB anon, ein Kind rund 136 MiB, tesseract rund 99 MiB (B2, `docs/performance.md` Nachtrag 26.09.) [VERIFIED: codebase]. Ohne Eingriff stirbt also der **Hauptprozess**, und der Container startet neu. Deshalb setzt jedes Kind vor allen Imports `oom_score_adj` auf 1000 (Erhöhen ist ohne Privileg erlaubt, Senken braucht CAP_SYS_RESOURCE [VERIFIED: fs/proc/base.c __set_oom_adj]; wird an tesseract vererbt). Dann trifft ein cgroup- oder Host-OOM zuerst ein Kind, der Hauptprozess überlebt, und der Pool sieht den Kill.

**HaRP/AppAPI:** AppAPI-Daemons setzen standardmäßig keine Speichergrenze (A9, `hardware.py` Moduldoc) [VERIFIED: codebase]. Dann ist `memory.max` = "max", `max` steigt nie, und es bleiben `oom_kill` (auch bei Host-OOM) und die Exitcodes der Kinder. Wenn eine Umgebung `memory.oom.group = 1` setzt (Kubernetes tut das unter v2, Docker nach Stand dieser Research nicht [ASSUMED]), stirbt beim OOM der ganze Container; dann greift nur der Unrein-Ende-Merker (Muster 7).

**Nach einem Neustart sind die Zähler weg:** Stirbt der Container, legt Docker die cgroup beim Start neu an; `memory.events` beginnt bei null [ASSUMED]. Ein OOM-Kill des Hauptprozesses ist nach dem Neustart deshalb nur über einen eigenen persistenten Merker erkennbar (Muster 7).

**cgroup v1:** `memory.events` fehlt. Wie `memory_guard` heute: bekannte Grenze, kein Ereignisleser; Erkennung nur über Exitcodes der Kinder (SIGKILL ohne Zählerbestätigung zählt dann als OOM-Kill). Optional ließe sich `memory.oom_control` (Feld `oom_kill`) lesen; nicht nötig für die Zusage.

### Befund B: "Mindestens einmal ausliefern, höchstens einmal indexieren" unter N Slots

Crash-Punkte einer Staffel, Stand Code [VERIFIED: codebase `worker/poller.py` Moduldoc und `_work`, `index/writer.py` `add`, `QueueMapper` `claimBatch/unlock/acknowledge`]:

| Kill-Zeitpunkt | Index | state.db | Warteschlange | Ergebnis nach Neustart |
|---|---|---|---|---|
| vor dem Commit (halbe Staffel, einige `add` erledigt) | letzter Commit, pending verworfen | unverändert | Zeilen gesperrt bis Lease-Ende, dann erneut (retries +1) | alles neu gelesen, je Datei ein Dokument |
| zwischen Commit und Verdikten | Dokumente drin | "unjudged" | gesperrt | Neuauslieferung, Upsert ersetzt: ein Dokument |
| zwischen Verdikten und Quittung | drin | `indexed` + Hash | gesperrt | Schnellpfad quittiert ohne Arbeit |

- Das Upsert (`delete_documents_by_query(term file_id)` vor `add_document`) wirkt auf alle Dokumente mit kleinerem Opstamp, auch auf committete Segmente [VERIFIED: codebase-Kommentar, gemessen in Plan 02]. Doppelte Dokumente entstehen nur, wenn **dieselbe** `file_id` zweimal nebenläufig geschrieben wird. Das ist innerhalb eines Anspruchs ausgeschlossen (Unique-Index auf `file_id`, eine Zeile je Datei), über Anspruchsgrenzen hinweg ebenfalls, weil genau ein Anspruchsnehmer für den Index-Lane existiert (der Einbettungs-Läufer nimmt nur `embed`). Mit der Writer-Sperre (Muster 3) ist das Paar Löschen/Einfügen zusätzlich atomar.
- **Neue Verlustquelle unter N Slots (Pitfall 1):** Heute führt ein unerwarteter Kind-Tod zu `failed(corrupt)` (`sandbox.py` `_ask`, EOFError-Zweig) und ein mit -9 beendeter tesseract zu `EngineFailed` und damit `failed(ocr_failed)` (`extract/ocr.py` Zeile 209). `failed` reist in der Quittung, die Zeile wird gelöscht. Mit einem Slot ist das Opfer der Verursacher. Mit N Slots tötet der OOM-Killer ein beliebiges Kind (das größte), also oft eine unschuldige Datei. Ohne Gegenmaßnahme wird eine Zeile verloren und SC2 Fall 2 fällt.
- **Retries unter N Slots:** Ein Kill des Hauptprozesses kostet jede Zeile der Staffel eine Auslieferung. Beschnittene Zeilen, die sofort per `unlock` zurückgehen, bekommen ihre Auslieferung erstattet (`QueueMapper::unlock` zieht `retries` ab) [VERIFIED: codebase]. Kollateralschaden je Kill also höchstens `2 x S - 1` Zeilen statt heute einer; die Stufenabsenkung nach jedem Kill (Leistung, Standard, Sparsam) begrenzt, wie oft dieselben Zeilen gemeinsam sterben können. Zeilen kehren nach Lease-Ende gemeinsam zurück (Reihenfolge `id ASC`), deshalb ist die Begrenzung über die Stufenabsenkung nötig.

### Befund C: Sperrfrist bei KIND_BATCH[ocr] = 32

- Das Lease lebt nur in PHP: `claimBatch` rechnet `cutoff = now - LOCK_TIMEOUTS[kind]` und behandelt ältere `locked_at` als frei; `refreshExisting` nutzt `max(LOCK_TIMEOUTS)` für die H4-Unterscheidung (frei vs. gerade in Arbeit) [VERIFIED: codebase `QueueMapper.php` 143-150, 272-323, 341-417]. Eine Arbeit, die länger als das Lease hält, öffnet das H4-Fenster wieder: Ein Schreibzugriff auf die Datei behandelt die Zeile als frei, löscht die Dirty-Markierung, und die Quittung löscht die Zeile mit der neuen Version (repariert erst der nächtliche Abgleich).
- Die Container-Ableitung `OCR_JOB_SECONDS_MAX = OCR_LOCK_TIMEOUT_SECONDS // OCR_CLAIM_BATCH - 2 x 60` ergibt bei 32 Zeilen **-64** und zerlegt `OCR_JOB_SECONDS_RANGE` (`config.py` 480, 490) [VERIFIED: codebase]. Die Ableitung muss auf "Zeilen je Slot" umgestellt werden.
- Zahlen: Datei-Zeitdeckel = harte Frist (`ocr_job_seconds` 600 + 60) + Download-Marge 60 = **720 s** (am Deckel 780 + 120 = 900 s). `OCR_MAX_PAGES x OCR_PAGE_SECONDS` = 30 x 30 = 900 s liegt über der weichen Jobfrist und wird von ihr begrenzt. Formel D-26-06 nach Zeilen aufgelöst: `rows_per_slot = floor(1800 / 720) = 2` (am Deckel ebenfalls 2). Bei S = 16 behält der Container 32 Zeilen, bei S = 1 zwei, also exakt den heutigen Sparsam-Anspruch.

### Muster 1: SlotPool und SlotGate

**Was:** `SlotPool` hält bis zu `N_max` `ExtractionWorker`-Instanzen in einer thread-sicheren Freiliste und startet Kinder faul. `run(path, mime, size, *, route, timeout_seconds)` ist die bisherige Fassadensignatur, damit Test-Fakes der Poller-Injektion (`extract: ExtractFile`) unverändert passen. `SlotGate` ist die asyncio-Schranke mit veränderlichem Limit (`asyncio.Condition`, `in_use < limit`), FIFO für Wartende, also Work-Stealing ohne feste Zuteilung.

**Wann:** immer; mit Limit 1 ist es der heutige Container.

```python
# Source: Muster extract/sandbox.py (ExtractionWorker), Empfehlung dieser Research
class SlotGate:
    """At most ``limit`` extraction jobs at once; the limit may shrink at any time."""

    def __init__(self, limit: int) -> None:
        self._limit = max(1, limit)
        self._in_use = 0
        self._changed = asyncio.Condition()

    async def set_limit(self, limit: int) -> None:
        async with self._changed:
            self._limit = max(1, limit)
            self._changed.notify_all()

    @contextlib.asynccontextmanager
    async def slot(self) -> AsyncIterator[None]:
        async with self._changed:
            await self._changed.wait_for(lambda: self._in_use < self._limit)
            self._in_use += 1
        try:
            yield
        finally:
            async with self._changed:
                self._in_use -= 1
                self._changed.notify_all()
```

Ein Schrumpfen wirkt beim nächsten Erwerb; laufende Kinder werden nie für eine Drosselung gekillt (Arbeit ginge verloren).

**Eigener Executor:** Die Wartezeit auf eine Kind-Pipe (bis 660 s) blockiert einen Thread. `asyncio.to_thread` nutzt den Default-Executor, den auch `/search`, `/snippets`, `/status` und die SQLite-Aufrufe teilen (`api/search.py` 365, `api/snippets.py` 261, `api/status.py` 681) [VERIFIED: codebase]. Bei 4 Kernen hat er 8 Threads; vier davon in OCR-Wartezeit halbieren die Suche. Der Pool bekommt einen eigenen `ThreadPoolExecutor(max_workers=N_max, thread_name_prefix="findling-slot")` und wird per `loop.run_in_executor` gerufen.

### Muster 2: Staffel mit OCR-Tasks und Barriere

1. Nach dem Anspruch `jobs` teilen: `ocr_jobs` (Art `ocr`) und `rest` (Anspruchsreihenfolge).
2. Zeilenbeschnitt (Muster 4) und sofortiges `unlock` des Überschusses; diese IDs verlassen `_held`.
3. Limit setzen: `min(S_gedrosselt, len(ocr_kept) + (1 if rest enthält Extraktionsjobs else 0))` (D-26-07).
4. OCR-Tasks starten: je Task `async with gate.slot()`: `_fetch_file`, `pool.run(..., route="ocr", timeout=hart)`, bei `INDEXED` `writer.add` in einem Thread (Sperre im Writer), Ergebnis als Verdikt-Datum zurück. Die Tasks berühren `state.db` **nicht** (gemeinsame Poller-Verbindung, siehe Pitfall 4).
5. `rest` seriell wie heute; ein Content-Job erwirbt ebenfalls einen Slot, bevor er extrahiert (Speicherbudget: nie mehr als N Kinder).
6. Barriere: `asyncio.gather(*tasks, return_exceptions=True)`, dann `_collect` je Ergebnis im Loop-Thread. Eine `_GatewayDown`- oder `_DiskTight`-Ausnahme führt nach der Barriere zu `_abort` (alle gehaltenen Zeilen zurück), wie heute.
7. Solo-Wiederholung für `ChildKilled`-Ergebnisse (Muster 5), dann Commit, Verdikte, Übergabe, Quittung **unverändert**.

Mit `S == 1` oder Lane `all` bleibt die Schleife byte-gleich die heutige (OCR in Anspruchsreihenfolge im selben Durchlauf), damit Sparsam unverändert bleibt. Einbettungszeilen im Lane `all` (Serien-Rückfall D-25-11) werden erst nach der Barriere eingebettet, damit OCR und Einbettung sich dort nicht überlappen.

### Muster 3: Writer-Sperre

`IndexBatchWriter` bekommt `self._lock = threading.Lock()` und hält ihn in `add`, `drop_document`, `flush`, `collect_garbage`, `close` und beim Lesen von `pending`/`pending_bytes`. Gründe: die Zähler `_pending`/`_pending_bytes` sind unbewacht (Vorgänger-R4) [VERIFIED: codebase], und tantivy-py gibt in `add_document` die GIL frei, der Writer ist ein veränderlich geliehenes Rust-Objekt; zwei Threads gleichzeitig ergeben bestenfalls einen Borrow-Fehler [ASSUMED: pyo3-Verhalten für `&mut self`-Methoden, nicht im tantivy-py-Quelltext nachgelesen]. Die Sperre in der Klasse ist sicherer als eine asyncio-Sperre im Poller, weil `add` immer über einen Thread gerufen wird.

### Muster 4: Zeilenbeschnitt statt Lease-Parameter (Sperrfrist D-26-06)

```python
# config.py (Container); Source: Befund C
OCR_LOCK_TIMEOUT_SECONDS = 1800          # mirror of QueueMapper::LOCK_TIMEOUTS[ocr], unchanged
OCR_CLAIM_BATCH = 2                      # mirror of KIND_BATCH[ocr] for lane all (Sparsam, 1.3 wire)
OCR_CLAIM_BATCH_INDEX_LANE = 32          # mirror of KIND_BATCH[ocr] for lane index (D-26-05)
OCR_ROWS_PER_SLOT = 2                    # rows one slot finishes inside one lease at the ceiling
OCR_JOB_SECONDS_MAX = OCR_LOCK_TIMEOUT_SECONDS // OCR_ROWS_PER_SLOT - 2 * OCR_HARD_DEADLINE_MARGIN_SECONDS  # 780, unchanged

def ocr_rows_to_keep(delivered: int, ocr_slots: int, file_cap_seconds: int) -> int:
    """D-26-06 solved for the rows: ceil(kept / slots) x cap + margin stays inside the lease."""
    per_slot = max(1, OCR_LOCK_TIMEOUT_SECONDS // file_cap_seconds)
    return min(delivered, max(1, ocr_slots) * per_slot)
```

`file_cap_seconds = settings().ocr_hard_deadline_seconds + OCR_HARD_DEADLINE_MARGIN_SECONDS`. Der Test `test_a_full_ocr_claim_at_the_ceiling_stays_under_the_lock_timeout` wird auf `OCR_ROWS_PER_SLOT` umgeschrieben; der Paritätstest liest beide PHP-Werte je Lane.

### Muster 5: Von außen gekilltes Kind = kein Verdikt

- `ExtractionWorker._ask`: nach `EOFError/OSError` das Kind joinen und `process.exitcode` prüfen. `-signal.SIGKILL` ohne eigenen Kill (der Timeout-Pfad kehrt vorher zurück) wird als `ChildKilled` (Ausnahme oder Sentinel, **kein** neuer Reason-Code, weil Reasons in der Quittung gegen die PHP-Liste validiert werden) an den Aufrufer gegeben. Andere Exitcodes (70 der `die`-Probe, -11) bleiben `failed(corrupt)`; der bestehende Test `test_an_unexpected_child_death_is_a_verdict_and_not_a_hang` bleibt grün.
- `extract/ocr.py`: `finished.returncode == -signal.SIGKILL` wird zu einer eigenen Ausnahme `EngineKilled`, die das Kind als "killed" meldet statt `EngineFailed`.
- Poller: `ChildKilled` zählt als Kill-Meldung an den Wächter; die Datei läuft nach der Barriere **allein** (Limit 1) noch einmal. Stirbt sie erneut, ist sie der Verursacher: `failed(out_of_memory)` (bestehender Reason). Waren beim Kill nur ein Kind beschäftigt (Sparsam), bleibt es beim heutigen Verdikt, damit Sparsam unverändert ist.

### Muster 6: Slot-Drossel je Runde (D-26-02)

```python
# Source: memory_guard.headroom_bytes (Phase 25), Empfehlung
def throttled_slots(target: int, headroom: int | None) -> int:
    """Slot 1 always runs (D-25-11); slot k needs (k - 1) x cost + reserve of headroom."""
    if target <= 1 or headroom is None:
        return 1
    extra = max(0, (headroom - GUARD_RESERVE_BYTES) // OCR_SLOT_COST_BYTES)
    return min(target, 1 + extra)
```

Konservativ: `headroom` zählt die ruhenden Kinder schon als belegt. Gelesen in einem Thread vor jedem Staffel-Start; Ergebnis (`slotsInForce`, `throttled`) an `guard` gemeldet.

### Muster 7: Wächter-Task, Merker, Unrein-Ende

- `worker/watch.py`: eigener Lifespan-Task, Tick 15 s (gleicher Takt wie der Einbettungs-Läufer), liest `memory_events()` und `headroom_bytes()` in einem Thread, führt die Deque qualifizierter Ticks (Befund A) und nimmt Kill-Meldungen des Pools thread-sicher entgegen (`loop.call_soon_threadsafe`).
- Auslöser: neue Kappe = eine Stufe unter der **wirksamen** Stufe, nie unter `economy`; in Sparsam nur Anzeige, keine Aktion (Vorarbeit 3.2: Wächter in Sparsam aus).
- Persistenz in `state.db` meta, eigene Verbindung (busy_timeout greift): `guard_cap`, `guard_cause`, `guard_since`, `guard_token` (32 Hex, `secrets.token_hex(16)`), `guard_chosen` (das zum Zeitpunkt gewählte Profil). Beim Start vor der ersten Runde gelesen, `profile.effective(chosen, fitting, cap)` berücksichtigt die Kappe.
- Unrein-Ende: Zu Beginn jeder Staffel mit S > 1 `multi_slot_pass = 1`, am Ende `0`. Der Lifespan schreibt beim **Beginn** des Herunterfahrens (vor allen Wartezeiten) `0`, damit ein SIGKILL nach Ablauf der Docker-Stop-Frist nicht als Unrein-Ende zählt. Findet der Start `1`, starb der Prozess ohne SIGTERM während einer Mehr-Slot-Staffel (OOM, `docker kill`, Stromausfall). Ob das als OOM-Kill zählt, ist Offene Frage O4.
- Ursachen als geschlossene Menge (Code Englisch): `memory_max_repeated`, `oom_kill`, `unclean_end`.

### Muster 8: Rückweg per Bestätigungs-Token (D-26-04)

- Companion: neuer appconfig-Schlüssel `profile_confirmed` (freier String, validiert als 32 Hex); die Profil-Route liefert ihn als `confirmed` neben `profile` und `precision`.
- Container: `companion_choice()` liest `confirmed`. Merker löschen, wenn `confirmed == guard_token` **oder** das gewählte Profil von `guard_chosen` abweicht (neue Entscheidung des Admins).
- Adminseite: "gewählt Leistung, wirksam Standard (Speicher knapp, 2x memory.events max)" plus Rückweg `occ config:app:set findling profile_confirmed --value=<token>`; Phase 27 schreibt den Token per Knopf.
- Alter Companion (1.3): keine Profil-Route, also ohnehin `economy`; der Merker ist dort wirkungslos. Kein Sonderpfad nötig.

### Muster 9: embed_slots = 2 (D-25-12)

`EmbedRunner._work` bettet bis zu `profile.snapshot().resolution.values.embed_slots` Zeilen nebenläufig ein (Tasks, Grenze per `asyncio.Semaphore`), weiterhin innerhalb der Track-Sperre der Runde (die Poller-Inline-Zeilen und der Markenschritt bleiben ausgeschlossen). Innerhalb der Runde nötig:
- `threading.Lock` um den Chunker-Aufruf (Tokenizer und semantic-text-splitter ohne Thread-Zusage; der Modell-Wrapper sperrt nur seinen eigenen Tokenizer) [VERIFIED: codebase-Kommentar `embed/model.py` 446-448 zu huggingface/tokenizers#1726].
- `asyncio.Lock` um die beiden SQLite-Schreibaufrufe `replace_acl` und `replace_chunks`: beide laufen über je **eine** Verbindung der Spur mit explizitem `BEGIN IMMEDIATE`; zwei Threads auf derselben Verbindung verschachteln Transaktionen [VERIFIED: codebase `store/repo.py` 630/804, `store/vectors.py` 381/419].
- onnxruntime `Run()` ist für eine Session aus mehreren Threads zugesagt (Kommentar `embed/model.py` 450-457) [VERIFIED: codebase]. Der idle-Guard (`_in_flight` unter Sperre, Phase 25 Plan 25-02) deckt zwei gleichzeitige Aufrufe bereits ab; keine Mitnahme nötig.
- Erwartung: Zwei gleichzeitige `Run()` teilen sich den Intra-op-Threadpool der Session; der Gewinn ist ungewiss [ASSUMED]. In die CI-Messleiter als Nebenzahl aufnehmen, nicht als Abnahmekriterium.

### Muster 10: os.nice und oom_score_adj im Kind (D-26-11)

In `_child_main` direkt nach `os.setsid()` und vor `_shed_secrets()`/Imports, nur `sys.platform != "win32"` (os.nice fehlt unter Windows, pyright prüft plattformabhängig):
- `os.nice(SANDBOX_NICE)` mit `SANDBOX_NICE = 10`; wird bei fork/exec an tesseract vererbt.
- best effort `Path("/proc/self/oom_score_adj").write_text("1000")`, `OSError` schlucken.
- best effort `Path("/proc/self/autogroup").write_text("10")`: Nach `setsid()` bildet das Kind eine eigene Autogroup; ohne CPU-cgroup-Controller wirkt nice sonst nur innerhalb dieser Gruppe (man 7 sched). Im Container mit CPU-Controller ist die Autogroup ohne Wirkung (`task_wants_autogroup` verlangt die Root-Task-Gruppe) [VERIFIED: kernel/sched/autogroup.c]. Rate-Limit-`EAGAIN` schlucken.

CI-Zusicherung: neuer Job-Typ im Kind-Protokoll (`_JOB_PRIORITY`), der `os.nice(0)` (liest ohne Änderung) und `/proc/self/oom_score_adj` zurückgibt; für den Enkel die bestehende `grandchild`-Probe, die seine PID liefert, und im Elternteil `os.getpriority(os.PRIO_PROCESS, pid) == 10`. Reihenfolge-Test wie `test_the_child_hardens_itself_before_the_parsers_load`.

### Anti-Patterns to Avoid
- **N gleiche Poller oder zwei Anspruchsnehmer im Index-Lane:** ein zweiter Nehmer holt abgelaufene Leases derselben Arbeit und indexiert doppelt nebenläufig. Genau ein Anspruch je Staffel.
- **Nachschub-Anspruch während die Staffel läuft ("echter Doppelpuffer"):** macht den Poller zum Konkurrenten seiner eigenen Leases. Nicht in dieser Phase.
- **Kinder für die Drossel killen:** verliert Arbeit, die schon Minuten lief. Nur neue Erwerbe verhindern.
- **`asyncio.to_thread` für Slot-Wartezeiten:** blockiert den Default-Executor der Suche.
- **Store-Zugriffe aus OCR-Tasks:** gemeinsame Poller-Verbindung, verschachtelte Transaktionen.
- **Neuer Reason-Code für "gekillt":** würde in die Quittung laufen und von der PHP-Validierung abgelehnt.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Prozess-Isolation je Job | eigenes fork/exec, `ProcessPoolExecutor` | N x `ExtractionWorker` | RLIMIT_AS, Deadline mit Gruppen-Kill, Recycling-Regeln, Import-Hygiene, Geheimnis-Abwurf sind dort gemessen und getestet |
| Headroom-Rechnung | eigener `memory.current`-Leser | `memory_guard.headroom_bytes` | anon statt Seitencache (Phase 25 Pitfall 7) |
| Rückgabe nicht bearbeiteter Zeilen | eigener "release"-Weg | bestehende `unlock`-Route | erstattet `retries` (DI-05-23) |
| Profil-Wirksamkeit | zweites "effective"-Feld | `profile.effective()` um die Kappe erweitern | eine Wahrheit, gleiche Linie D-24-07 |
| Persistenz | neuer Schreibweg nach Nextcloud | `Store.write_meta` in `state.db` | Gate A, kein Companion-Schreibpfad nötig |
| Zufallstoken | eigener Generator | `secrets.token_hex(16)` | kryptografisch, stdlib |

**Key insight:** Jede Garantie dieser Phase steht schon im Code (Upsert, Commit-vor-Quittung, Unlock-Erstattung, Kind-Isolation). Die Arbeit ist, sie unter Nebenläufigkeit nicht zu brechen, nicht neue zu bauen.

## Common Pitfalls

### Pitfall 1: Unschuldiges Kind stirbt, Datei bekommt ein Endverdikt
**What goes wrong:** OOM-Killer tötet ein beliebiges Kind oder dessen tesseract; `failed(corrupt)` bzw. `failed(ocr_failed)` reist in der Quittung, die Zeile ist weg.
**Why it happens:** `_ask` und `_read_page` unterscheiden SIGKILL nicht von anderen Fehlern.
**How to avoid:** Muster 5 (ChildKilled/EngineKilled, Solo-Wiederholung).
**Warning signs:** `ocr_failed`-Verdikte, die bei Wiederholung von Hand indexieren.

### Pitfall 2: `memory.events max` löst auf gesunden Boxen aus
**What goes wrong:** Jede Box mit gesetztem `memory.max` steigt dauernd, Stufe fällt ohne Not.
**Why it happens:** Zählung vor dem Reclaim, Seitencache der mmap zählt mit (Befund A).
**How to avoid:** qualifiziertes Ereignis (Δmax > 0 und anon-Headroom unter Reserve).
**Warning signs:** Absenkung mit Ursache `memory_max_repeated`, während `oom_kill` null bleibt.

### Pitfall 3: Hauptprozess ist das OOM-Opfer
**What goes wrong:** Container stirbt statt eines Kindes; Neustart mit denselben Slots, Absturzschleife.
**Why it happens:** Badness folgt RSS; der Hauptprozess ist fünfmal größer als ein Kind.
**How to avoid:** `oom_score_adj = 1000` in jedem Kind; Unrein-Ende-Merker als zweite Linie.
**Warning signs:** Unrein-Ende-Merker beim Start, `oom_kill` des neuen Containers bei null.

### Pitfall 4: Gemeinsame SQLite-Verbindung aus mehreren Threads
**What goes wrong:** "cannot start a transaction within a transaction" oder halbe Transaktionen.
**Why it happens:** `check_same_thread=False` erlaubt den Zugriff, serialisiert aber keine `BEGIN IMMEDIATE`-Blöcke.
**How to avoid:** OCR-Tasks ohne Store-Zugriff; in der Einbettungsspur `asyncio.Lock` um die Schreibaufrufe.
**Warning signs:** `ROUND_PAUSED_STORE_ERROR` unter Last.

### Pitfall 5: Default-Executor voll
**What goes wrong:** Suche und Snippets warten auf freie Threads, Unified Search läuft in den 2-s-Timeout (das Symptom von Issue #19).
**Why it happens:** Slot-Wartezeiten über `asyncio.to_thread`.
**How to avoid:** eigener Executor für den Pool (Muster 1). Beim Herunterfahren den Pool schließen (Kinder per Gruppen-Kill beenden), sonst wartet `shutdown_default_executor` bzw. der eigene Executor bis zu 660 s (`main.py` Kommentar M-18-07).
**Warning signs:** Suchlatenz steigt mit der Slotzahl, nicht mit der CPU-Last.

### Pitfall 6: Lange Sparsam-Runden durch 32 OCR-Zeilen
**What goes wrong:** Bei einem Slot und 32 Zeilen dauert eine Runde bis 8 h; acl- und delete-Zeilen warten so lange (D-04), ein Profilwechsel greift erst danach, ein OOM-Kill sperrt 32 Zeilen bis 8 h.
**Why it happens:** Anspruch und Quittung sind je Runde.
**How to avoid:** Zeilenbeschnitt (Muster 4) und `KIND_BATCH[ocr]` je Lane (Offene Frage O2).
**Warning signs:** `STAND_DOWN_SECONDS` (300 s) reißt, Rebuild startet nicht.

### Pitfall 7: Einbettung verhungert im Lane `all`
**What goes wrong:** Mit 32 OCR-Zeilen im Lane `all` bleibt vom Zeilenbudget (32) nichts für `embed`; heute kommen 2 OCR + 8 embed je Anspruch.
**Why it happens:** `QueueService::claim` verteilt ein gemeinsames Zeilenbudget in Artreihenfolge.
**How to avoid:** Lane `all` behält `KIND_BATCH[ocr] = 2`.
**Warning signs:** Vektorbestand wächst in Sparsam erst nach dem letzten Scan.

### Pitfall 8: nice wirkt nicht über cgroup-Grenzen
**What goes wrong:** Live-Probe zeigt keinen Gewinn bei `status.php`, das Ergebnis wird als "nice wirkungslos" gelesen.
**Why it happens:** Unter Gruppen-Scheduling zählt nice nur innerhalb der Task-Gruppe; Nextcloud ist ein anderer Container. Zwischen Containern entscheidet `cpu.weight` (je 100), das von innen nicht schreibbar ist [ASSUMED: cgroupfs im Container read-only].
**How to avoid:** Probe misst zwei Größen getrennt: Findling-Suche über die Unified Search (profitiert) und `status.php` (voraussichtlich nicht). Der Schutz der Nextcloud über Container hinweg bleibt die Slotzahl (Anteilsprinzip).
**Warning signs:** Issue-#19-Antwort verspricht mehr, als die Messung trägt.

### Pitfall 9: Unrein-Ende-Fehlalarm nach Updates
**What goes wrong:** Docker schickt nach der Stop-Frist (Standard 10 s) SIGKILL, der Lifespan wartet aber bis 30 s auf die Staffel; jedes Update während OCR senkt die Stufe.
**How to avoid:** Merker beim **Beginn** des Herunterfahrens löschen (Muster 7).

### Pitfall 10: Kill-Test braucht N >= 4, der Runner liefert es nicht
**What goes wrong:** Auf dem 4-Kern-Runner (16 GB) ergibt die Profilformel in Leistung höchstens 3 Slots und der Vorschlag deckelt auf Standard (1 Slot); der echte Nextcloud-Lauf in `resilience.yml` erreicht N >= 4 nicht.
**How to avoid:** Kill-Test als pytest-Harness mit injizierter Slotzahl (Poller-Konstruktor), echten Kindern, echtem Writer und echter `state.db`, Warteschlange als dateibasierter Fake mit PHP-Lease-Semantik. Kein Umgebungsschalter für Slots (INDEX_WORKERS-Tabu).

### Pitfall 11: Byte-Budget kappt OCR-Zeilen
**What goes wrong:** `max_bytes` 64 MiB kann bei großen Scans weniger als 2 x S Zeilen liefern.
**How to avoid:** D-26-07 (min(N, gelieferte Zeilen)) fängt es ab; kein Handlungsbedarf, aber in der Messleiter vermerken.

## Code Examples

### memory.events lesen (neutral, nie werfend)
```python
# Source: Muster memory_guard.anon_bytes; Feldnamen docs.kernel.org cgroup-v2
def memory_events(root: Path = CGROUP_ROOT) -> dict[str, int] | None:
    """The counters of memory.events, or None on cgroup v1, at the root or when unreadable."""
    try:
        raw = (root / "memory.events").read_text(encoding="ascii")
    except (OSError, ValueError):
        return None
    counters: dict[str, int] = {}
    for line in raw.splitlines():
        fields = line.split()
        if len(fields) == _STAT_FIELDS and fields[1].isdigit():
            counters[fields[0]] = int(fields[1])
    return counters or None
```

### Kind härten (Reihenfolge ist die Eigenschaft)
```python
# Source: extract/sandbox.py _child_main, erweitert
if sys.platform != "win32":
    os.setsid()
    os.nice(SANDBOX_NICE)
    _lower_own_standing()   # oom_score_adj 1000, autogroup 10, OSError ignored
_shed_secrets()
_limit_address_space(address_space_bytes)
_pin_native_thread_pools()
from findling.extract.dispatch import Route, extract
```

### Von außen gekilltes Kind erkennen
```python
# Source: extract/sandbox.py _ask, EOF-Zweig erweitert
except (EOFError, OSError):
    process.join(_JOIN_GRACE_SECONDS)
    killed = process.exitcode == -signal.SIGKILL
    self._recycle()
    if killed:
        raise ChildKilled   # not a verdict: the poller retries the file alone
    return ExtractionOutcome.failed(Reason.CORRUPT)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ein Kind, `extract_guarded`-Global | Pool aus N Kindern | diese Phase | Docstrings von `sandbox.py` (IDX-08-Satz, "one worker per process") nachziehen |
| `OCR_JOB_SECONDS_MAX` aus `KIND_BATCH[ocr]` | aus `OCR_ROWS_PER_SLOT` | diese Phase | Paritätstest je Lane |
| ThreadPoolExecutor-Default aus `os.cpu_count()` | aus `os.process_cpu_count()` | Python 3.13 | Default-Executor im Container kleiner als früher, Pitfall 5 wiegt schwerer |

**Deprecated/outdated:** Die Aussage in `sandbox.py`, genau eine Extraktion laufe gleichzeitig (IDX-08), gilt nur noch in Sparsam.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Docker setzt weder `memory.high` noch `memory.oom.group` für ExApp-Container | Befund A | oom.group = 1: ganzer Container stirbt, nur Unrein-Ende greift |
| A2 | Nach Container-Neustart beginnt `memory.events` bei null | Befund A | harmlos, der Merker ist ohnehin persistent |
| A3 | cgroupfs im Container read-only, `cpu.weight` nicht von innen setzbar | Pitfall 8 | wäre ein zusätzlicher Hebel für #19 |
| A4 | tantivy-py-Writer bei gleichzeitigen Aufrufen nicht sicher | Muster 3 | keiner, die Sperre ist wegen der Zähler ohnehin Pflicht |
| A5 | Zwei gleichzeitige onnx-`Run()` bringen wenig zusätzlichen Durchsatz | Muster 9 | embed_slots = 2 bringt mehr als erwartet; nur Messwert |
| A6 | Fensterwert 600 s, 60 s Abstand, Reserve 235 MiB trennen Druck von Rauschen | Befund A | Fehlalarm oder zu späte Absenkung; Fake-cgroup-Tests und Phase-28-Messung prüfen |
| A7 | `/proc/self/oom_score_adj` und `/proc/self/autogroup` im Container beschreibbar | Muster 10 | best effort, dann nur nice; Kill-Opfer wieder der Hauptprozess |
| A8 | `asyncio.Condition`-Schranke genügt als größenveränderliche Semaphore | Muster 1 | Test deckt es ab |

## Open Questions

1. **O1: Richtung der Sperrfrist-Formel (D-26-06)**
   - Was wir wissen: Das Lease setzt nur PHP durch; ohne neuen Parameter kann der Container keine eigene Frist setzen (Befund C).
   - Was unklar ist: ob der Owner "Sparsam bekommt eine lange Frist" wörtlich will (dann Lease-Parameter am Anspruch, gegen D-26-05, mit Pitfall 6) oder die Formel als Zeilenbeschnitt akzeptiert.
   - Empfehlung: Zeilenbeschnitt (Muster 4). Kurz beim Owner bestätigen lassen, bevor der Plan-Schnitt steht.

2. **O2: KIND_BATCH[ocr] je Lane**
   - Was wir wissen: fest 32 in allen Lanes ändert den Sparsam-Anspruch (Pitfall 7) und gibt 1.3-Containern 32 OCR-Zeilen.
   - Empfehlung: 32 im Lane `index`, 2 im Lane `all`. Kein neuer Parameter, der Lane existiert seit Phase 25. Serien-Rückfall (Lane `all`) nutzt dann höchstens 2 Slots; passt zur Lage "Speicher knapp". Owner-Bestätigung.

3. **O3: Qualifizierung des max-Ereignisses**
   - Empfehlung: Befund A. Wortlaut von D-26-03 bleibt ("zwei max-Ereignisse im Fenster"), das Ereignis wird definiert. Owner zur Kenntnis.

4. **O4: Unrein-Ende als OOM-Kill werten?**
   - Was wir wissen: Ein OOM-Kill des Hauptprozesses ist nach dem Neustart nicht mehr beobachtbar.
   - Empfehlung: Ja, aber nur für ein Ende ohne SIGTERM während einer Mehr-Slot-Staffel (sichere Richtung, Admin bestätigt). Owner-Entscheid, weil es über "beobachteter OOM-Kill" hinausgeht.

5. **O5: nc35-Harness für D-26-12**
   - Was unklar ist: Aufbau des Harness (Nextcloud-Container getrennt vom ExApp-Container wie in `compose-harp.yaml`?).
   - Empfehlung: Probe mit zwei Messreihen (Findling-Suche über Unified Search, `status.php`), je mit und ohne nice (Abschalten per Testschalter nur im Messaufbau, nicht im Produkt).

6. **O6: Push für CI-Belege**
   - SC2 (Linux-CI) und SC3 (arm64-Runner, `measure.yml` zieht das veröffentlichte Abbild) brauchen einen Push; 150+ Commits liegen nur lokal. Owner-Entscheid wie bei den PHPUnit-Läufen der Phasen 24/25.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | Gates, Tests | ja | 0.11.7 | - |
| Python | Tests | ja | 3.13.13 (lokal) | - |
| Docker (Linux, cgroup v2) | lokaler Kill-Test, Messleiter-Probe | ja | 29.5.2, CgroupVersion 2 | - |
| gh | Workflow-Start `measure.yml` | ja | 2.92.0 | - |
| GitHub-Runner ubuntu-24.04 (4 vCPU) | SC2 Kill-Test in CI | nur nach Push | - | lokal im Linux-Container (x86), gilt nicht als CI-Beleg |
| GitHub-Runner ubuntu-24.04-arm (4 vCPU, 16 GB) | SC3 Messleiter | nur nach Push und manuellem Start | - | keiner (qemu-Zahlen unbrauchbar, 21-RESEARCH) |
| tesseract | Messleiter im Abbild | im Produktabbild | 5.5.0 | Kill-Test ohne tesseract über die `sleep`-Probe durch den echten Pool |
| nc35-Harness | D-26-12 Live-Latenzprobe | unklar | - | compose-harp.yaml lokal |

**Missing dependencies with no fallback:** arm64-CI-Lauf ohne Push (SC3).
**Missing dependencies with fallback:** Linux-CI für SC2 (lokaler Linux-Container als Vorprüfung).

## Testschnitt (Validation ist in der Konfiguration abgeschaltet, deshalb nur die Pflichtteile)

- **Kill-Harness (D-26-08, SC2):** `tests/test_slots_kill.py`, nur Linux (`skipif`), Laufzeit unter 60 s (python.yml hat 15 min Deckel). Ein Kindprozess startet einen Poller mit `ocr_slots=4` injiziert, `extract` über den echten `SlotPool` mit `sleep`-Probe (kontrollierte Dauer, echte Kinder), echter Writer und `state.db` im tmp-Volume, Warteschlange als SQLite-Datei-Fake mit PHP-Semantik (retries beim Anspruch, Lease-Ablauf injiziert auf wenige Sekunden, Unlock-Erstattung, Quittung löscht, Dirty-Regel). Fall 1: SIGKILL auf den Harness, sobald mindestens zwei `add` erledigt und zwei Jobs in Arbeit sind (Markerdatei), Neustart auf demselben Volume, Abarbeiten; prüfen: je `file_id` genau ein Dokument (Term-Suche), Warteschlange leer, kein `failed`. Fall 2: während der Staffel ein Kind per `os.kill(pid, SIGKILL)`; prüfen: die Datei ist indexiert (Solo-Wiederholung), keine Stufenabsenkung, wenn der Fake-`oom_kill` nicht steigt.
- **Messleiter (D-26-09, SC3):** neuer Modus des bestehenden `scripts/ops/ocr_slot_probe.py` (`--mode poller`) oder eigenes `scripts/ops/slot_ladder.py`, der den echten `Poller.run_once` mit Fake-Warteschlange und lokalen Scans fährt (Korpus: synthetische Scans aus `build_load_corpus`, fester Seed wie W4, etwa 16 einseitige plus 4 achtseitige). Neuer Schritt im Job `slots` von `measure.yml` für S = 1, 2, 4 auf `--cpuset-cpus 0`, `0,1`, `0-3`, je 3 Runden; Faktor je Stufe gegen 1,05. Rohdaten nach `docs/measurements/2026-09-slot-leiter-ci/`, Nachtrag in `docs/performance.md`. Die W4-Rohkurve (Faktor 3,955 bei N = 4) ist die Obergrenze; die Produktkurve liegt wegen der seriellen Anteile darunter.
- **Wächter:** Fake-cgroup-Bäume (Muster `test_memory_guard.py`) für: kein Limit, v1, Δmax ohne Druck (keine Absenkung), zwei qualifizierte Ticks im Fenster (Absenkung), Ticks zu dicht (keine), oom_kill-Anstieg (sofort), Merker übersteht Neustart, Token löscht, Profilwechsel löscht.
- **Sparsam-Pin:** bestehender Pin bleibt; zusätzlich: Lane `all` ergibt byte-gleiche Anspruchs-Parameter und eine sequentielle Schleife.
- **Paritätstests:** `KIND_BATCH[ocr]` je Lane, `LOCK_TIMEOUTS[ocr]` unverändert, `confirmed`-Feld PHP/Python.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein | unverändert (AppAPI-Signatur) |
| V3 Session Management | nein | - |
| V4 Access Control | ja | Token nur über appconfig (Admin), Container liest nur; Gate A bleibt ohne neue Schreibpfade |
| V5 Input Validation | ja | `confirmed` als 32-Hex validiert, sonst None (Muster `companion_choice`); Ursachen und Stufen als geschlossene Mengen |
| V6 Cryptography | nein | `secrets.token_hex` ist kein Schutzmittel, nur Eindeutigkeit |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| N Kinder vergrößern die Angriffsfläche der Parser | Elevation | jedes Kind identisch gehärtet (Geheimnisabwurf, RLIMIT_AS, eigene Sitzung); Kinder berühren Nextcloud nie |
| Präparierte Dateien erzwingen wiederholte OOMs | Denial of Service | Absenkung ist die sichere Richtung; Solo-Wiederholung endet mit `failed(out_of_memory)`, keine Endlosschleife |
| Log-Leck über neue Meldungen | Information Disclosure | nur Zähler, Stufen, Ursachencodes; bestehender Grep-Test auf Pfade/Titel gilt auch für neue Module |
| Status verrät Token | Information Disclosure | `/status` ist ADMIN-Route; Token hat keine Wirkung außer dem Rückweg |

## Empfohlener Plan-Schnitt (Vorschlag)

- Welle 1: (a) Pool + Kind-Härtung (nice, oom_score_adj, ChildKilled, EngineKilled) mit Tests; (b) Writer-Sperre; (c) `memory_events` + `guard.py` neutral; (d) PHP: `KIND_BATCH` je Lane, `profile_confirmed` + Route, Paritätstests.
- Welle 2: Poller-Staffel (Zeilenbeschnitt, Tasks, Barriere, Solo-Wiederholung, Drossel, Unrein-Ende-Merker), `config.py`-Ableitung neu.
- Welle 3: Wächter-Task + Persistenz + Lifespan (Pool schließen, Merker beim Beginn des Herunterfahrens), embed_slots = 2 im Läufer.
- Welle 4: `/status` GuardReport, Adminseite + acht Kataloge, `docs/profiles.md`, `docs/ocr.md` (Lease-Rechnung).
- Welle 5: Kill-Harness (SC2), Messleiter-Werkzeug + `measure.yml` (SC3), Live-Latenzprobe (D-26-12, Checkpoint mit Owner).

## Sources

### Primary (HIGH confidence)
- Codebase: `extract/sandbox.py`, `extract/ocr.py`, `worker/poller.py`, `worker/embedding.py`, `embed/engine.py`, `embed/model.py`, `index/writer.py`, `memory_guard.py`, `hardware.py`, `profile.py`, `lane.py`, `config.py`, `store/repo.py`, `store/vectors.py`, `main.py`, `api/status.py`, `php/lib/Service/QueueService.php`, `php/lib/Db/QueueMapper.php`, `php/lib/Controller/QueueController.php`, `tests/test_config.py`, `tests/test_sandbox.py`, `.github/workflows/{python,measure,resilience}.yml`, `docs/performance.md` (Nachtrag 26.09.)
- git.kernel.org torvalds/linux: `mm/memcontrol.c` (try_charge_memcg: MEMCG_MAX vor Reclaim), `mm/oom_kill.c` (MEMCG_OOM_KILL im Opfer-memcg), `fs/proc/base.c` (__set_oom_adj), `kernel/sched/autogroup.c` (task_wants_autogroup nur Root-Task-Gruppe)
- docs.kernel.org/admin-guide/cgroup-v2.html: memory.events, memory.events.local, memory.oom.group, cpu.weight
- man7.org sched(7): Autogroup, nice unter Gruppen-Scheduling
- docs.python.org/3.13/library/concurrent.futures.html: max_workers-Default

### Secondary (MEDIUM confidence)
- `.planning/research/BL-F04-vorarbeit-2026-09-25.md` (Slot-Regel, Rauschgrenze, K1 bis K10), `25-RESEARCH.md` Pitfall 7

### Tertiary (LOW confidence)
- Docker-Standards zu memory.high, oom.group und cgroupfs-Mount (A1 bis A3), nicht in dieser Sitzung nachgelesen

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH, keine neuen Pakete, stdlib und Bestandsmuster
- Architektur: HIGH für Staffel/Upsert/Lease (Code gelesen), MEDIUM für Pool-Details (Entwurf)
- Pitfalls: HIGH für 1, 2, 4, 5, 6, 7 (Code bzw. Kernel verifiziert), MEDIUM für 3, 8, 9 (Kernel-Semantik verifiziert, Container-Umgebung angenommen)

**Research date:** 2026-09-28
**Valid until:** 2026-10-28 (Code-Befunde bis zum nächsten Umbau von Poller/Queue; Kernel-Semantik stabil)
