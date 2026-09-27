# Phase 23: Härtung und Store-Einreichung 1.3.0 - Research

**Researched:** 2026-09-26
**Domain:** Release-Härtung einer Nextcloud-ExApp (Python/FastAPI-Backend plus PHP-Companion): Kaltstart-Ladepfad, PHP-Migration, Abhängigkeitsbereinigung, Store-Texte, signierte Einreichung
**Confidence:** HIGH für Codebefunde (alle mit Datei:Zeile), MEDIUM für das Laufzeitverhalten des Hintergrundladens auf der Zielbox (GIL-Befund aus Quelltext belegt, Dauer auf der Box nicht gemessen)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Kaltstart-Fix V-22-01/V-22-02 (Owner 26.09.)
- **D-01:** Der Kaltstart-Befund wird IN 1.3.0 gefixt, auf BEIDEN Routen (/search und /snippets). Fix-Weg: die erste Suche nach Neustart antwortet sofort rein lexikalisch (Tantivy, unter dem 1,5-s-Deckel) und stoesst das Laden der Modellgewichte im Hintergrund an; Semantik greift ab der naechsten Anfrage. NIE eine leere Treffergruppe wegen Modell-Ladens.
- **D-02:** /snippets bekommt zusaetzlich die Einwortregel, die /search schon kennt: fuer einwortige Anfragen wird die semantische Seite gar nicht erst aufgebaut (kein query_may_load fuer Einwort-Zeilen).
- **D-03:** KEIN Vorwaermen beim Containerstart. Das Lazy-Load-Prinzip bleibt: RAM-Kosten der Gewichte (~250-400 MB) fallen erst bei der ersten semantischen Nutzung an (4-GB-Boxen-Budget).

#### Alte gone-Zeilen (Issue #14)
- **D-04:** Die 1.3.0-Migration reiht ALLE als skipped(gone) markierten Eintraege einmalig neu ein (Reparaturlauf beim Upgrade). Der neue ACL-Code (Merge 257caac) sortiert sie dann korrekt: indexieren oder ehrlich unreadable/gone. Kein manueller Eingriff fuer Betroffene noetig; Preis ist ein einmalig laengerer Scan nach dem Upgrade.

#### Release-Text-Zuschnitt
- **D-05:** Issue-14-Fix: eigene Changelog-Zeile mit Dank an budachst und Verweis auf #14. Nach dem Release eine kurze Antwort im Issue (1.3.0 enthaelt Fix plus Reparaturlauf). Der Store-Kurztext bleibt frei davon (Faktenlisten-Regel).
- **D-06:** HART-05-Grenzen: alle vier Punkte als Kurzliste ("Known limitations") IM Store-Text UND identisch in der Doku: (1) ano und ano fallen zusammen, (2) pt-Rechtschreibreform wird nicht vereinheitlicht, (3) Komposita nur fuer de und nl, (4) Franzoesisch hat kein Koerperfeld. Erfuellt HART-05 woertlich; bleibt Faktenliste.

#### Audit-Tiefe
- **D-07:** Security-Audit VOLL ueber die ganze App (wie vor jeder Abgabe). Bug- und Performance-Audit GEZIELT auf die seit 1.2.0 geaenderten Pfade: Schema/Marken/Umbauweg (18), Frageseite (19), Kataloge es/it/nl/pt (20), NL-Komposita (21), Kaltstart-Fix und gone-Reparaturlauf (23). Begruendung: Phasen 17-22 hatten je eigene Audits. Endstand bleibt 0 CRIT / 0 HIGH, MEDIUM behoben, LOW dokumentiert entschieden.

### Claude's Discretion
- Mechanik des Hintergrundladens (Task/Lock-Zuschnitt, Doppelstart-Schutz) und Nachweis (Test + Nachmessung der Kaltstartroute in CI).
- Zuschnitt des Reparaturlaufs (Migrationsschritt vs. Startup-Job), solange er einmalig laeuft und idempotent ist.
- HART-04-Weg: fastembed==0.8.0-Pin entfernen oder Import belegen, numpy sauber deklarieren oder eliminieren; Ergebnis muss die Abhaengigkeitsliste dem Container-Ist angleichen.
- Reihenfolge der Haertungsschritte; E2E-Strecken nach dem probe-92d.yml-Muster.
- Kleine offene Doku-Befunde mitnehmen (Messbericht 21-04 Abschn. 4.3: 41,9 statt 42,1 MB).

### Deferred Ideas (OUT OF SCOPE)
- Erstindex-Beschleunigung (BL-F04) bleibt v1.4; budachsts Beschleunigungsfrage aus Issue/Reddit reist dort.
- FR-Koerperfeld, pt_BR/pt_PT-Wortlaute, NL-Betonungsakzente, Sortierung Name/Groesse, Mimetype-Gruppen, Pro-Schiene: unveraendert auf der Nach-v1.3-Liste der ROADMAP.
- Snapshot `snap-03f1d1d9ad9262704`: Wiedervorlage beim Milestone-Close (ROADMAP).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HART-04 | Aufräumbefunde geschlossen: `fastembed==0.8.0`-Pin geklärt, `numpy` sauber deklariert oder eliminiert | Abschnitt "HART-04": fastembed wird nirgends importiert; Entfernen streicht 6 Pakete, `tokenizers` und `numpy` müssen dafür direkte Kanten werden |
| HART-05 | Dokumentierte Grenzen des Sprachausbaus in Doku und Store-Text | Abschnitt "HART-05": Wortlaut-Quellen in `docs/language-analyzers.md:438-483`, Gates in `test_store_metadata.py` (genau eine Messzahl je Beschreibung) |
| REL-03 | v1.3.0 eingereicht: signiertes App-Paar, Upgrade-Beweis 1.2.0 auf 1.3.0 in CI inkl. Umbau-Fall, Store-Texte gate-konform mit Owner-Abnahme, 2x HTTP 201 | Abschnitt "Release-Strecke": drei Versionsstellen, bestehende CI-Äste Store install 0-7 / Store upgrade 0-6 in `deploy-harp.yml`, `probe-92d.yml` mit `from_tag=v1.2.0`, Ablauf nach Präzedenz 16-07/16-09/16-11/16-13/16-14 |
</phase_requirements>

## Summary

Die Phase ist zu großen Teilen Wiederholung einer bewährten Release-Strecke (Phase 16, v1.2.0: Bump plus Migration, Upgrade-Beweis, Store-Texte, Audit, Abgabe), aber mit zwei echten Produktänderungen, die beide tiefer greifen, als CONTEXT.md vermuten lässt.

**Der Kaltstart-Fix ist mechanisch fast fertig, hat aber zwei versteckte Fallen.** Der Hintergrund-Warmlauf existiert bereits vollständig (`request_warm`/`warm_wanted`/`warm` in `embed/engine.py:486-582`, Auslösung im Handler `api/search.py:385-398`), ist aber an Schalter > 0 gekettet (`query_may_load` gibt bei Schalter 0 `True` zurück, `engine.py:406`; `warm_wanted` verweigert bei Schalter 0, `engine.py:525-529`). Der Fix ist im Kern: `query_may_load` immer `False`, die Schalter-0-Sperre in `warm_wanted` entfernen, `/snippets` die Einwortregel geben. Falle 1: Ein Suchaufruf mit `may_load=False` wartet heute trotzdem auf das Modell-Lock, solange der Warmlauf lädt (`embed/model.py:526-527`, das Laden läuft unter `self._lock`); ohne lockfreien Schnellpfad reißt die zweite Anfrage den Deckel weiter. Falle 2 (aus Quelltext belegt): onnxruntime 1.30.0 hält beim Anlegen der `InferenceSession` den GIL (kein `gil_scoped_release` in `py::init` und `initialize_session`, nur in `run`). Ein Hintergrundthread im selben Prozess friert damit für die Ladedauer die Ereignisschleife und alle Anfragethreads ein. Das erklärt den Rohdatenbefund der Nachanfahrt: eine einwortige, rein lexikalische `/search` riss mit 1.505,4 ms, während die Gewichte luden.

**Der gone-Reparaturlauf gehört in eine neue PHP-Migration, und er muss die gone-Zeilen löschen, nicht nur neu einreihen.** Die #14-Fehlurteile stehen in `oc_findling_file_state` (PHP-Seite, geschrieben von `QueueService::claim` über `finish()`). `revokeFailures` nimmt ausschließlich `failed` zurück (`FileStateService.php:318-334`), und diese Seite schreibt nie `indexed`: ein neu eingereihtes, danach erfolgreich indexiertes File trüge sonst für immer weiter `skipped(gone)` auf der Statusseite. Dazu kommt: `requeueAs` legt fehlende Queue-Zeilen selbst an (`QueueMapper.php:662-676`), die Migration braucht also keine Containerverbindung.

**Die Release-Strecke hat mehr CI, als ihr Titel verlangt, und drei CI-Stellen brechen durch den Kaltstart-Fix.** Frische Installation (Store install 0-7) und Upgrade 1.2.0 auf Baum inkl. Umbau (Store upgrade 0-6, `UPGRADE_FROM_TAG: v1.2.0`) stehen in `deploy-harp.yml`. Brechen werden: die Paraphrase-Kaltsuche in `integration.yml:1709-1855` (erwartet einen Vektortreffer in der ERSTEN Suche nach Neustart), der Offline-Beweis `tests/probe_image_search.py` in `docker.yml` (baut ein eigenes `EmbeddingModel`, der geteilte Halter bleibt kalt) und das Werkzeug `tools/one_load.py` samt `resilience.yml`-Gate (erwartet, dass `one_round` selbst lädt).

**Primary recommendation:** Kaltstart-Fix als eigener erster Plan mit lockfreiem `may_load=False`-Schnellpfad und Warmstart erst NACH dem Senden der Antwort; gone-Reparatur als neue Migration `Version001300Date2026092x000000` (requeue plus Löschen der gone-Zeilen in einer Transaktion); HART-04 als Entfernen des Pins mit `tokenizers==0.23.2` und `numpy==2.5.2` als direkte Kanten; danach Bump, Texte, Audit, Abgabe nach dem Muster von Phase 16.

## Project Constraints (from CLAUDE.md)

- Python 3.13 plus uv (lokales System-Python defekt); CI und Dockerfile nutzen uv **0.11.7** mit `uv sync --frozen` (`.github/workflows/python.yml:114,119`, `backend/Dockerfile:35,48,53`).
- Qualitätsgates lokal grün VOR Commit: ruff (Vollregelsatz laut `pyproject.toml:104`), `ruff format --check`, pyright basic (lokal mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, Owner-Regel 19.09.), vulture min-confidence 80, pytest. Referenzstand nach Merge 257caac: 3324 bestanden / 15 übersprungen (STATE.md).
- Owner-Regel 07.09.: Store-Texte und READMEs sind kurze Faktenlisten, höchstens eine Messzahl, Details nur als Verweis auf `docs/`; Textentwurf vor Release dem Owner zeigen.
- Owner-Regel 06.09.: Launch-Härtung (Fehler-/Randpfade, Rechte, Neustart/Upgrade/Migration, kaputte Dateien, Ressourcengrenzen, Fremdinstallation, Store-Vorgaben, alle Audits) VOR der Abgabe; Abgabe erst nach Owner-Abnahme.
- Owner-Regel 15.08.: nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Abschluss fixen.
- Code und Bezeichner Englisch; deutsche Prosa mit echten Umlauten; keine Gedankenstriche (U+2013, U+2014), keine Emojis; das Wort für Aufbewahrungsort ("arch"+"iv") ist in öffentlichen Artefakten gesperrt (`test_store_metadata.py:195`).
- Security/Privacy: Berechtigungs-Durchgriff strikt, keine Inhalte verlassen den Server, keine Telemetrie; Logzeilen tragen Typnamen und Zähler, nie Suchtext (T-06-27, T-14-22).
- OSS-Commits nur als `street1983nk <k.cherif@outlook.de>`, keine Claude-Trailer (Owner-Regel 25.08.).
- GSD-Workflow: Änderungen nur über `/gsd-execute-phase`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Kaltstart: lexikalisch antworten, Gewichte im Hintergrund laden | API / Backend (Python-Container, `embed/engine.py`, `api/search.py`, `api/snippets.py`) | PHP-Companion (Deckel 1,5 s in `ExAppService.php:95,122`, unverändert) | Die Entscheidung, ob eine Anfrage laden darf, liegt an genau einer Stelle (`query_may_load`); der Deckel ist PHP-seitig und bleibt |
| Einwortregel auf /snippets | API / Backend (`api/snippets.py`) | , | Gleiche Regel wie `api/search.py:313`, gleicher `build_query`-Ausgang `rewritten.one_term` |
| gone-Reparaturlauf | Database / Storage (PHP-Migration auf `oc_findling_file_state` und `oc_findling_queue`) | API / Backend (Poller verarbeitet die eingereihten Zeilen normal) | Die Fehlurteile stehen in der PHP-Tabelle; die Migration läuft ohne Container (Muster `Version001300Date20260924000000`) |
| HART-04 Abhängigkeitsliste | Build (pyproject, uv.lock, Image) | Doku (THIRD-PARTY.md) | Rein deklarativ, kein Laufzeitpfad ändert sich |
| HART-05 Grenzen | Store-Metadaten (beide `info.xml`), Doku (`docs/store-listing.md`, `docs/language-analyzers.md`) | Gate `test_store_metadata.py` | Text reist mit dem Release und ist danach nicht editierbar |
| Signierung, Einreichung | CI (`release.yml`, `store-submit.yml`) | Owner (Tag, Dispatch, Abnahme) | Schlüssel und Token verlassen den GitHub-Secret-Store nicht |

## Standard Stack

Keine neuen Bibliotheken. Die Phase arbeitet ausschließlich mit dem gepinnten Bestand.

### Core (betroffen)
| Library | Version | Purpose | Status in dieser Phase |
|---------|---------|---------|------------------------|
| onnxruntime | 1.30.0 | Inferenz (`backend/pyproject.toml:44`) | unverändert; GIL-Verhalten beim Laden ist planungsrelevant [VERIFIED: onnxruntime v1.30.0 `onnxruntime/python/onnxruntime_pybind_state.cc:2921-2977` ohne `gil_scoped_release`, `run` mit Release ab Zeile 3013] |
| tokenizers | 0.23.2 | Tokenizer, direkt importiert (`embed/model.py:66,269`, `embed/chunker.py:49`, `embed/bench.py:68`) | wird direkte Kante, heute nur transitiv über fastembed [VERIFIED: backend/uv.lock:152 und :1008] |
| numpy | 2.5.2 | Feeds für die Session (`embed/model.py:708`, `embed/bench.py:446`) | wird direkte Kante, bleibt ohnehin über onnxruntime im Image [VERIFIED: backend/uv.lock:529, onnxruntime-Abhängigkeiten] |
| fastembed | 0.8.0 | heute gepinnt (`pyproject.toml:38`), aber nirgends importiert | entfernen [VERIFIED: grep über backend/src, backend/tests, scripts: kein `import fastembed`/`from fastembed`] |
| FastAPI/Starlette | fastapi 0.141.1, starlette >= 1.0.1 | `BackgroundTasks` als Werkzeug für "Warmstart nach dem Senden" | unverändert |

**Installation:** keine. Nach dem pyproject-Edit: `cd backend && uv lock` mit uv 0.11.7, dann `uv sync --frozen`.

## Package Legitimacy Audit

Diese Phase installiert keine neuen externen Pakete. `tokenizers` und `numpy` werden von transitiven zu direkten Kanten, auf exakt den Versionen, die `backend/uv.lock` heute schon festhält (0.23.2, 2.5.2); sie sind seit Phase 6 im Image. Entfernt werden `fastembed`, `loguru`, `mmh3`, `py-rust-stemmers`, `requests`, `urllib3`.

| Package | Registry | Source Repo | slopcheck | Disposition |
|---------|----------|-------------|-----------|-------------|
| tokenizers 0.23.2 | PyPI | github.com/huggingface/tokenizers | nicht gelaufen (kein Neuzugang) | Approved, bereits im Lockfile |
| numpy 2.5.2 | PyPI | github.com/numpy/numpy | nicht gelaufen (kein Neuzugang) | Approved, bereits im Lockfile |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## HART-04: fastembed und numpy

### Befund
- `fastembed` wird von keinem Modul importiert; alle Treffer sind Kommentare/Docstrings (`embed/model.py:38-43,75`, `embed/bench.py:378-385`, `backend/Dockerfile:123,363,484`, `docker.yml:343`, `tests/probe_image_search.py:11`). Das Projekt hat onnxruntime und tokenizers direkt verdrahtet (`embed/model.py:302-340`). [VERIFIED: grep]
- `numpy` wird direkt importiert (`embed/model.py:708`, `embed/bench.py:446`, dazu 7 Testdateien), steht aber nicht in `pyproject.toml`. [VERIFIED: grep]
- `tokenizers` wird ebenso direkt importiert und hängt heute nur an fastembed (`uv.lock:152`). **Wer fastembed ohne Ersatzkante streicht, verliert tokenizers aus dem Image und damit die ganze Semantik.** [VERIFIED: uv.lock]

### Was das Streichen bewirkt (aus `backend/uv.lock`)
| Paket | Bleibt? | Warum |
|---|---|---|
| fastembed, loguru, mmh3, py-rust-stemmers | fällt weg | nur von fastembed gezogen (`uv.lock:144-153`) |
| requests, urllib3 | fällt weg | requests nur von fastembed, urllib3 nur von requests (`uv.lock:898-905`) |
| huggingface-hub, tqdm | **bleibt** | `tokenizers` hängt an `huggingface-hub` (`uv.lock:1012`), hub zieht tqdm (`uv.lock:333`) |
| numpy | bleibt | onnxruntime hängt daran |
| pillow | bleibt | direkte Kante (`pyproject.toml:28`) |

Folge für die Doku: `HF_HUB_OFFLINE=1` bleibt nötig (hub bleibt im Image), die Begründung in `backend/Dockerfile:484` und `docker.yml:343` ("arrive through fastembed") ist dann falsch und muss auf "durch tokenizers" umgestellt werden. `THIRD-PARTY.md:208` (fastembed-Zeile) und `:235-243` (requests als Netzbibliothek) werden falsch; dieselbe Tabelle nennt außerdem noch `onnxruntime 1.29.0`, gepinnt ist 1.30.0 (`pyproject.toml:44`), ein mitzunehmender Altbefund.

### Empfohlener Weg
1. `pyproject.toml`: Zeile 38 und ihren Kommentar entfernen; `"tokenizers==0.23.2"` und `"numpy==2.5.2"` mit Begründungskommentar (direkt importiert, Kante nicht dem Zufall eines Transitivpfads überlassen) eintragen. Kommentar zu onnxruntime (`:39-43`) nennt "under fastembed", umformulieren.
2. `uv lock` mit uv 0.11.7 laufen lassen, `uv.lock` committen.
3. Beweis "Container-Ist": im Image `python -c "import importlib.util,sys; sys.exit(importlib.util.find_spec('fastembed') is not None)"` und dasselbe für requests; als Prüfschritt in `docker.yml` neben den bestehenden Abbildprüfungen.

## Architecture Patterns

### Datenfluss Kaltstart heute und nach dem Fix

```
Unified Search (PHP, Deckel 1,5 s je Aufruf)
   |
   v
POST /search ──> one_round (Thread) ──> build_query ──> lexical_only?
   |                                        |             ja: nur Tantivy
   |                                        |             nein: SemanticSide(may_load=query_may_load())
   |                                        |                    |
   |                                        |    HEUTE Schalter 0: may_load=True -> lädt im Request (V-22-01)
   |                                        |    NACH FIX: may_load=False -> Halter kalt -> embedding_unavailable
   |                                        |              -> RRF = Identität auf lexikalischer Liste
   |                                        └──> request_warm() setzt _WARM_WANTED
   v
Handler: warm_wanted()? ──ja──> Warmlauf (to_thread(warm)) ──> _load unter model._lock
   |                                    (GIL gehalten während InferenceSession-Aufbau)
   v
Antwort an PHP (lexikalische Kandidaten)
   |
   v
POST /snippets ──> excerpts ──> NACH FIX: one_term/lexical_only -> keine SemanticSide
                               sonst SemanticSide(may_load=False) -> Auszug aus Generator
```

### Pattern 1: query_may_load bleibt die eine Stelle, antwortet aber immer False
**What:** `embed/engine.py:367-406`. Die Funktion ist laut eigenem Docstring die einzige Stelle, die die drei Aufrufer fragen (`api/search.py:311`, `api/snippets.py:229`; `api/diagnose.py` fragt bewusst nicht und lädt weiter). Der Docstring sagt wörtlich, der allgemeine Fall "is carried as a backlog item" (`engine.py:387-388`). Dieser Backlog-Fall ist D-01.
**Konsequenz:** `warm_wanted` (`engine.py:525-529`) verweigert heute bei Schalter 0 mit Verweis auf `query_may_load`; dieser Zweig muss fallen, sonst lädt bei Schalter 0 nie jemand im Hintergrund. `main.py:796-798` startet den Tick-Task nur bei Schalter > 0; bei Schalter 0 bleibt allein der Handlerweg `api/search.py:385-398`, und der reicht.
**Was bleibt:** Doppelstart-Schutz ist schon da und zweistufig: `_WARMING`-Flag (`engine.py:569-572`) und strukturell `_load` kehrt zurück, wenn der Halter gebunden ist (`model.py:582ff`). Tests dazu existieren (`test_embed_engine.py:1277`, zehn parallele `warm()`).

### Pattern 2: lockfreier Schnellpfad für may_load=False
**What:** `EmbeddingModel._embed` nimmt `self._lock` auch für `may_load=False` (`model.py:526-527`). Der Warmlauf hält dasselbe Lock über das ganze `_load`. Eine zweite Suche während des Ladens wartet also die Ladezeit ab, obwohl sie nie laden darf.
**Empfehlung:** vor dem Lock `if not may_load and self._engine is None: return EmbedOutcome.unavailable()` (Referenzlesen ist in CPython atomar). Den `_last_use`-Stempel dabei nicht setzen; er zählt nur für einen gebundenen Halter (`engine.py:455-461`). Ein Test mit echtem Lock: Thread A hält `model._lock` (Stand-in für `_load`), Thread B ruft `embed_query(..., may_load=False)` und muss in < 50 ms `available is False` liefern.

### Pattern 3: Warmlauf erst nach dem Senden der Antwort
**What:** onnxruntime 1.30.0 hält beim Konstruktor und `initialize_session` den GIL (Quelle oben). Ein per `asyncio.create_task(asyncio.to_thread(warm))` gestarteter Lauf (`api/search.py:396`) kann den GIL greifen, bevor Starlette die Antwort geschrieben hat, und hält ihn für die Dauer von Import plus Sessionaufbau.
**Empfehlung:** den Warmlauf über FastAPI `BackgroundTasks` anhängen. Starlette führt Hintergrundaufgaben erst nach dem vollständigen Senden der Antwort aus. Der Kommentar in `api/search.py:385-395` hat genau diese Eigenschaft damals als Nachteil gewertet ("runs only after the response has gone out"); unter dem GIL-Befund ist sie der Vorteil. Alternative mit gleicher Wirkung: vor dem Laden `await asyncio.sleep(0)` reicht NICHT, weil das Schreiben der Antwort erst nach dem Return des Handlers beginnt.
**Restrisiko, ehrlich benennen:** Anfragen, die WÄHREND des Ladens eintreffen (nächster Tastendruck, der `/snippets`-Aufruf derselben Suche), stehen still, solange der GIL gehalten wird. `/snippets` degradiert dabei weich (Treffer bleibt, Unterzeile fällt auf den Pfad zurück; CI-Beleg `integration.yml` Schritt "A slow backend costs the excerpt, not the hit and not the budget"), eine zweite `/search` im Ladefenster kann aber am Deckel leer enden. D-01 ("NIE eine leere Treffergruppe wegen Modell-Ladens") ist damit für die ERSTE Anfrage erreichbar, für eine Anfrage im Ladefenster nicht garantierbar. Siehe Open Question 1.

### Pattern 4: Einwortregel auf /snippets (D-02)
**What:** `api/snippets.py:223-230` baut die `SemanticSide` für jede Zeile; der Kommentar `:204-210` begründet ausdrücklich, warum die Regeln der Suchroute hier NICHT gelesen werden (ein bestätigter reiner Vektortreffer verlöre sonst seinen Auszug).
**Warum D-02 dem nicht widerspricht:** Für eine einwortige Zeile hat `/search` gar keine Vektorliste gebaut (`api/search.py:313`), es gibt also keinen reinen Vektortreffer, dem ein Auszug fehlen könnte. Dasselbe gilt für Operatoren und `titleOnly`. Empfehlung: `rewritten.one_term` (Pflicht nach D-02) und gleich `rewritten.operators` und `title_only` wie in `api/search.py:313` prüfen; `sort` gibt es auf `/snippets` bewusst nicht (`snippets.py:109-113`). Der Kommentar `:204-210` muss umgeschrieben werden, sonst behauptet er das Gegenteil des Codes.

### Pattern 5: gone-Reparatur als eigene PHP-Migration (D-04)
**Wo die Zeilen stehen:** `oc_findling_file_state`, `state='skipped' AND reason='gone'`. Geschrieben von `QueueService::claim` über `finish()` (`QueueService.php:258-266`, `:998-1001`) für `SKIP_GONE` (`:128`, `:727-729`) und von der Quittung, wenn der Poller `skipped(gone)` meldet (Poller bei Gateway-404: `worker/poller.py:984-989`, `:1110-1112`). Vor 257caac lieferte `readerOf` auch dann `gone`, wenn nur der gewählte Leser die Datei nicht erreichte (Diff von d1f5110). Index auf `state` existiert (`Version001000Date20260816000000.php:124`).
**Warum Migration und nicht Startup-Job:** Die Zeilen liegen in der Nextcloud-Datenbank; der Container kennt die #14-Fälle meist gar nicht (PHP hat die Queue-Zeile quittiert, bevor der Container sie sah). Eine Nextcloud-Migration läuft genau einmal je Instanz (Buchführung in `oc_migrations`), braucht keinen erreichbaren Container und entspricht dem Muster und den Regeln von `Version001300Date20260924000000.php` (kein Containeraufruf, gegen Doppellauf gesichert, Klassen- und Dateiname zeichengleich). Ein Backend-Startup-Job bräuchte eine neue PHP-Route und eine eigene Versionsmarke.
**Neue Datei statt Erweiterung:** Der Klassenkommentar der bestehenden 1.3.0-Migration sagt wörtlich "This file stays what it is: ten lines that drop one key". Empfehlung: `php/lib/Migration/Version001300Date2026092X000000.php` (Datum des Entstehungstags, Präzedenz 16-07), sortiert nach der bestehenden.
**Ablauf in `postSchemaChange`, eine Transaktion je Band:**
1. `SELECT file_id FROM findling_file_state WHERE state='skipped' AND reason='gone'` in Bändern (Band 1000 wie `QueueMapper::DELETE_BAND`, `QueueMapper.php:185`).
2. `QueueMapper::requeueAs($band, KIND_CONTENT)`: setzt vorhandene Zeilen auf content (außer `delete`), legt fehlende mit `storage_id=0, root_id=0` an; `describe()` repariert die Nullen beim Claim aus dem Mountpunkt (`QueueMapper.php:662-676`, `QueueService.php` WR-01-Absatz).
3. **Dieselben gone-Zeilen aus `findling_file_state` löschen.** Grund: `revokeFailures` löscht nur `failed` (`FileStateService.php:318-334`) und diese Seite schreibt nie `indexed` (Klassenkommentar `FileStateService.php:14-47`). Ohne Löschen trüge eine jetzt indexierte Datei weiter `skipped(gone)`. Bleibt die Datei wirklich weg, schreibt der nächste Claim `gone` neu; ist sie unlesbar, `unreadable`.
4. Ausgabe über `IOutput::info` nur als Zahl ("requeued N files once judged gone"), keine Kennungen, kein Pfad.
**Idempotenz:** Ein zweiter Lauf (Nextcloud spielt eine Migration nach abgebrochenem Upgrade erneut ab) findet nur noch echte gone-Zeilen, die der erste Lauf hervorgebracht hat, und reiht sie erneut ein; der Claim entscheidet sie ohne Download über `usersFor()` sofort wieder als `gone` (`QueueService.php:727-729`). Kosten eines Wiederholungslaufs: eine Mount-Cache-Abfrage je Datei.
**Kosten des Erstlaufs:** je Datei ein Queue-Insert, beim Claim `usersFor` plus bis zu 20 Leserversuche (`MAX_READER_TRIES`), für lesbare Dateien Download, Extraktion, Index, Einbettung, also genau die Arbeit, die ohne #14 angefallen wäre. Anzahl je Instanz unbekannt: die Messbox hatte 44 übersprungene insgesamt bei 52.137 indexierten (performance.md, v1.3-Anfahrt), budachsts Instanz ist nicht vermessen.
**Nebenbefund zur Einordnung:** Der nächtliche Abgleich reiht Dateien, die der Container nicht kennt und die nicht `failed(repeatedly_stuck)` tragen, ohnehin als stale ein (`worker/reconcile.py:460-483`). Viele #14-Fälle heilt 1.3.0 also auch ohne Migration, aber erst nach einem Abgleichzyklus und nur, wenn die Seitenliste der Mounts die Team-Folder-Datei führt. D-04 macht es sofort und deterministisch; der Nebenbefund ist ein Argument für die Harmlosigkeit, nicht gegen den Plan.

### Anti-Patterns to Avoid
- **Reparatur ohne Löschen der gone-Zeilen:** Statusseite behauptet weiter "gelöscht" für indexierte Dateien.
- **Reparatur in der bestehenden Migration `Version001300Date20260924000000`:** bricht deren eigenen Klassenvertrag und vermischt zwei Gründe in einem Test.
- **Containeraufruf aus einer Migration:** läuft im Wartungsmodus ohne Nutzer, Container kann gerade neu starten (Klassenkommentar `Version001300Date20260924000000.php`).
- **fastembed streichen ohne tokenizers-Kante:** Semantik fällt still auf `embedding_unavailable`, Suche bleibt lexikalisch, nichts wird rot außer den Semantik-Beweisen.
- **Warmlauf per `create_task` vor dem Senden belassen:** GIL-Halt kann die erste Antwort selbst verzögern.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Nach-Antwort-Hintergrundarbeit | eigenen Thread, eigene Queue | FastAPI `BackgroundTasks` bzw. bestehendes `warm()` | zweiter Lebenszyklus neben der Lifespan ohne Stopp-Ereignis (Argument `api/search.py:390-392`) |
| Doppelstart-Schutz | neues Lock | `_WARMING` plus `_load`-Kopfprüfung (`engine.py:569-582`, `model.py:582ff`) | bereits getestet (`test_embed_engine.py:1277`) |
| Neu einreihen | eigenes INSERT in `oc_findling_queue` | `QueueMapper::requeueAs` | kennt `delete`-Vorrang, `dirty`-Zeilen, Zähler-Reset, MySQL-Rowcount-Falle (`QueueMapper.php:560-608`) |
| Upgrade-E2E | neue Workflow-Datei | `deploy-harp.yml` Store upgrade 0-6 und `probe-92d.yml` mit `from_tag=v1.2.0` | beide existieren, grün, mit Bestandstor |
| Store-Einreichung | curl vom Arbeitsplatz | `store-submit.yml` per `workflow_dispatch` mit `tag=v1.3.0` | Token und Schlüssel bleiben im Secret-Store |

## Runtime State Inventory

Die Phase ist kein Rename, aber D-04 ist eine Datenmigration; deshalb die fünf Kategorien.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `oc_findling_file_state` Zeilen `skipped/gone` (PHP-DB, Anzahl je Instanz unbekannt); ggf. dieselben Dateien als `skipped/gone` in der Container-`state.db` (`files`-Tabelle), wenn der Poller sie per Gateway-404 urteilte | Datenmigration (neue PHP-Migration). Container-seitig keine Aktion: der erneute Durchlauf überschreibt per `record()`-Upsert |
| Live service config | `oc_appconfig findling/backend_app_version` (wird von der bestehenden 1.3.0-Migration gelöscht) | keine neue |
| OS-registered state | keine; der Container wird von AppAPI/HaRP registriert, Registrierung trägt `image-tag` aus `backend/appinfo/info.xml:236` | Bump auf 1.3.0 |
| Secrets/env vars | `APPSTORE_TOKEN`, `APP_PRIVATE_KEY`, `BACKEND_PRIVATE_KEY` im GitHub-Secret-Store (`store-submit.yml:78-81`); Token wurde am 26.09. für Connector 0.3.0 erfolgreich benutzt (201) | vor dem Dispatch nicht verändernde Gültigkeitsprobe (L-16-05-Muster: leerer Rumpf auf die Release-Route, 400 heißt gültig, 401 überholt) |
| Build artifacts | `ghcr.io/street1983nk/findling_backend:1.3.0` existiert noch nicht; `findling.tar.gz`/`findling_backend.tar.gz` im Repo-Wurzelverzeichnis sind lokale Altreste | Tag-Push baut Image; lokale Tarballs nicht committen |

## Release-Strecke (REL-03)

### Versionsstellen (drei, im Gleichschritt, ein Commit)
- `php/appinfo/info.xml:125` `<version>1.2.0</version>`
- `backend/appinfo/info.xml:142` `<version>1.2.0</version>`
- `backend/appinfo/info.xml:236` `<image-tag>1.2.0</image-tag>`
Gate: `backend/tests/test_lockstep_versions.py:159` ("two halves and the image tag carry the same version"). `release.yml:177-188` prüft auf dem Tag, dass beide `info.xml` gleich dem Tag sind. `backend/pyproject.toml:3` `version = "0.1.0"` ist keine Release-Stelle (wird nirgends ausgeliefert, `APP_VERSION=0.1.0` in `integration.yml`). [VERIFIED: grep]

### Ledger-Pflicht bei jeder Code-Änderung
Jede Byte-Änderung unter `backend/src` bewegt `PACKAGE_TREE_HASH_TODAY` (`backend/tests/test_measurement_scripts.py:1195-1196`), jede unter `php/**/*.php` (inkl. Tests) `PHP_FILES_TODAY`/`PHP_TREE_HASH_TODAY` (`:658-659`). Neue Migration plus Test heben `PHP_FILES_TODAY` von 70 auf 72. Jede Verschiebung bekommt einen datierten Kommentarabsatz im Stil von `:690-800`.

### E2E-Strecken, die es schon gibt
| Strecke | Ort | Was nach dem Bump passiert |
|---|---|---|
| Fremdinstallation frisch | `deploy-harp.yml:1818-2607` Store install 0-7 (Archive bauen und signieren, Companion aus Paketdatei, anonymer Pull, ExApp aus Paketdatei, Suche ohne Konfiguration), Matrix amd64 plus arm64 | läuft auf jedem Push |
| Upgrade 1.2.0 auf Baum | `deploy-harp.yml:2920-4356` Store upgrade 0-5, `UPGRADE_FROM_TAG: v1.2.0` (`:113`) | nach dem Bump läuft der Zweig "echtes App-Update" (`:3901-3908`); vorher der Gleichstand-Zweig |
| Umbau-Fall | `deploy-harp.yml:4356` Store upgrade 6 "the rebuild a changed language set orders" | Umbau über Sprachwechsel auf dem Upgrade-Volumen |
| Upgrade auf Container-Nextcloud mit 92d | `probe-92d.yml`, Dispatch, Eingang `from_tag` (Vorgabe v1.1.0, `:49-53`) | nach dem Bump mit `from_tag=v1.2.0` dispatchen: dann gibt es einen echten Versionsschritt (der Kopfkommentar `:26-32` sagt, warum er vorher nicht einer war); `occ upgrade` Exit 3 zählt als gelungen (bbf929e) |

### Zusicherung, die der Reparaturlauf berühren kann
`deploy-harp.yml:4190-4200` (Store upgrade 5, Block 3) verlangt `unchanged` für `.nextcloud.skipped` und `.nextcloud.scheduled` ("something requeued work nobody asked for"). Der CI-Korpus (39 Referenzdateien plus Füllkorpus, `:3086ff`) enthält nach Lesart des Schritts keine gone-Zeile, die Migration wäre dort ein No-op, die Zusicherung hält, beweist aber auch nichts über D-04. Siehe Open Question 3.

### Einreichungsablauf (Präzedenz 16-14, Belegkette acht Zeilen)
1. Owner-Abnahme Härtung (Audit-README) und Store-Text-Entwurf.
2. Annotierter Tag `v1.3.0` auf den geprüften Kopf; keine Vorbereitungscommits danach (16-14 key-decisions).
3. Sieben Tag-Läufe lesen (Release, PHP, Multi-arch, HaRP deploy, Python, Integration, Resilience), jeden einzeln benennen.
4. Anhänge prüfen: vier Dateien, `Verified OK` zweimal, Größe gegen 20.971.520 B.
5. Manifestindex `findling_backend:1.3.0` anonym mit amd64 und arm64 prüfen, VOR der Einreichung.
6. Token-Gültigkeitsprobe (400/401), dann `store-submit.yml` mit `tag=v1.3.0`, `register=false`; Erfolg ist `HTTP 201` zweimal (`store-submit.yml:139-163`; der Schritt akzeptiert 200|201, Beleg ist der Wortlaut).
7. Gegenprobe beider App-Seiten einzeln, nicht die Katalogdatei.
8. Danach: Antwort in Issue #14 (D-05), `UPGRADE_FROM_TAG` NICHT in dieser Phase bewegen (erst wenn v1.3.0 der Ausgangspunkt des nächsten Sprungs ist).

## HART-05 und Store-Texte

### Wortlaut-Quellen der vier Grenzen
| Grenze | Quelle | Stand |
|---|---|---|
| año und ano fallen zusammen | `docs/language-analyzers.md:438-443` | vorhanden, englisch |
| keine pt-Rechtschreibvereinheitlichung | `docs/language-analyzers.md:468-475` | vorhanden |
| Komposita nur de und nl | `docs/language-analyzers.md:477-483` | vorhanden |
| Französisch ohne Körperfeld | `docs/language-analyzers.md:74-75` ("French has no chain in this build at all") | nur beiläufig; eine ausdrückliche Grenzzeile fehlt |
Die Datei kündigt die Kurzfassung selbst an: "The short version for HART-05 is written in phase 23 and is put to the owner before it is published" (`docs/language-analyzers.md:500-505`). Die `docs/l10n-*.md` sind Kataloge der UI-Wortlaute und tragen die Grenzen NICHT; sie sind für HART-05 kein Zielort.

### Gates, die der Text treffen muss
- Genau eine Messzahl je Beschreibung: `MEASURED_FIGURE = r"\d+(?:[.,]\d+)?\s(?:MB|Mo)\b"` (`test_store_metadata.py:372`), Prüfung `:987`. Die Grenzliste darf also keine MB-Angabe tragen.
- Keine Backticks, keine Tabellen, keine Gedankenstriche, echte Akzente (`docs/store-listing.md:15-32`); "año" mit ñ ist erlaubt und gewollt.
- Drei Sprachen je Hälfte (EN ohne `lang`, `de`, `fr`), Vorlage und beide `info.xml` wortgleich (`docs/store-listing.md:10-13`).
- Die Messzahl 731,9 MB steht an neun Stellen (sechs Store-Texte, drei READMEs; `docs/store-listing.md:728-740`). ROADMAP und PROJECT.md sagen "drei Stellen" (PROJECT.md:86); das ist die Zählung vor E1 (README.en.md plus beide info.xml) und veraltet.

### Messzahl für 1.3.0
v1.3-Anfahrt: C1 730,2 MB, C2 760,8 MB, Nachanfahrt C1 729,3 MB (`docs/performance.md`, Abschnitt "Der Bodensatz im zweiten Zyklus"). Die 731,9 MB sind v1.2-Abbild. Siehe Open Question 2.

### Changelog
Es gibt keine CHANGELOG-Datei im Repo; die Release-Notiz entsteht mit dem GitHub-Release. D-05 verlangt eine eigene Zeile mit Dank an budachst und Verweis auf #14. Der Planner sollte den Changelog-Text als Teil des Owner-Entwurfs vorlegen.

## Audit-Zuschnitt (D-07)

Produktpfade mit Änderungen seit `v1.2.0` (`git diff --stat v1.2.0..HEAD`, 35 Dateien, +5479/-206):
- Phase 18 bis 21: `index/rebuild.py` (+1307), `index/open.py`, `index/schema.py`, `index/analyzer.py`, `index/stopwords.py`, `index/wordlist_nl.py`, `index/writer.py`, `store/repo.py`, `api/resources.py` (+686), `api/status.py`, `query/rewrite.py`, `config.py`, `main.py` (+436), `worker/poller.py`, `backend/Dockerfile` (+33, wdutch), `php/templates/admin.php`, `php/js/admin.js`, `php/lib/Migration/Version001300Date20260924000000.php`.
- **Nicht in der D-07-Liste, aber seit 1.2.0 geändert:** der #14-Fix 257caac: `PathResolverService.php` (+475), `QueueService.php` (+130), `SearchService.php` (+75), `GatewayController.php`, `AdminViewService.php`, `FileStateService.php`. Der Security-Audit deckt sie ohnehin (voll), für Bug/Perf empfiehlt sich, sie ausdrücklich in den gezielten Umfang zu nehmen, weil der Fix außerhalb einer GSD-Phase mit eigenem Audit gemergt wurde (STATE.md: Merge-Branch, lokale Gates grün, kein Phasenaudit genannt). Siehe Open Question 4.
- Phase 23 selbst: `embed/engine.py`, `embed/model.py`, `api/search.py`, `api/snippets.py`, neue Migration, pyproject/uv.lock.
Hausform des Berichts: `docs/audits/2026-09-phase-16/README.md` (Härtungsmatrix acht Zeilen, Gate-Protokoll, ASVS, Geheimnis-Gegenprobe, Performance, Befundliste, Belegkette).

## Common Pitfalls

### Pitfall 1: Die Paraphrase-Kaltsuche in integration.yml wird rot
**What goes wrong:** `integration.yml:1709-1855` startet den Container neu und verlangt, dass die ERSTE Suche mit `PARAPHRASE_TERM` (lexikalisch nachweislich 0 Treffer, `:1680-1682`) `10-kuendigung.docx` findet. Nach dem Fix antwortet die erste Suche lexikalisch, also leer.
**How to avoid:** Schritt umbauen: erste kalte Suche muss HTTP 200 und innerhalb des Budgets antworten (Zahl wird weiter nur gedruckt), dann `engineState` über `/status` bis `loaded` abwarten, dann dieselbe Suche muss die Paraphrase finden. Das ist zugleich die geforderte CI-Nachmessung der Kaltstartroute. Zusätzlich die Dauer des Warmlaufs loggen (Zahl, kein Text).
**Warning signs:** `the paraphrase found nothing at all` im Integrationslauf.

### Pitfall 2: Der Offline-Beweis in docker.yml wird rot
**What goes wrong:** `tests/probe_image_search.py:205-225` bettet mit einem eigenen `EmbeddingModel`, `ask()` geht dann durch `one_round` mit dem geteilten Halter (`:284-300`), der kalt ist. Nach dem Fix liefert die Paraphrase dort nichts.
**How to avoid:** vor `semantic = ask(...)` den geteilten Halter warm machen, am ehrlichsten über den Produktweg `request_warm(); warm()` oder `resources.query_model().embed_query(..., may_load=True)`; Kommentar sagt warum.

### Pitfall 3: tools/one_load.py und sein Resilience-Gate werden rot
**What goes wrong:** `tools/one_load.py:286` und `:347-395` erwarten, dass `drive_the_search_side()` die Ladezahl von 0 auf 1 hebt ("This round is the one that brings the engine loads from zero to one") und nach der Freigabe wieder lädt. `resilience.yml:1430-1447` und `tests/test_one_load.py` hängen daran.
**How to avoid:** den Suchseitentreiber um den Handlerweg ergänzen (`if warm_wanted(): warm()`), damit er misst, was ein echter Aufrufer auslöst; `cold_search_ms` heißt danach anders oder misst Suche plus Warmlauf getrennt.

### Pitfall 4: Tests, die das alte Schalter-0-Verhalten festschreiben
`test_embed_engine.py:842-853` (`query_may_load` bleibt True bei 0), `:1200-1211` (kein Warmlauf bei 0), `test_search_endpoint.py:701-716` (Handler startet bei 0 nichts). Diese Fälle drehen sich um; die Gegenprobe (genau ein Lauf, kein Lauf bei geladenem Halter, keiner ohne Modell) bleibt. Doku mit derselben Aussage: `docs/admin-page.md:138` ("wer die Nachladekosten nicht will, setzt ... auf 0"), `docs/embeddings.md:760-840`, Docstrings `engine.py:377-388`, `:505-529`, `api/search.py:300-310`, `api/snippets.py:204-222`.

### Pitfall 5: Lock-Wartezeit trotz may_load=False
Siehe Pattern 2. Ohne Schnellpfad wartet jede Suche im Ladefenster auf `model._lock`. Belegt ist nur, dass die zweite Anfrage in der Nachanfahrt riss; ob Lock oder GIL, trennt die Rohdatei nicht (`rohdaten-nachanfahrt/m01-langsame-aufrufe-kaltstart-einwort.txt`: `/snippets 1510.5` um 16:45:50Z, `/search 1505.4` um 16:45:51Z; die zweite Suche war einwortig, also ohne Modellbezug, was eher für GIL/CPU spricht).

### Pitfall 6: uv.lock bleibt alt
`uv sync --frozen` prüft nicht, ob das Lockfile zum pyproject passt. Ein pyproject ohne neues Lockfile installiert in CI und Image weiter fastembed. Prüfung: `uv lock --check` lokal (uv 0.11.7) vor dem Commit; optional als Gate.

### Pitfall 7: Die Migration läuft auch auf frischen Instanzen
Nextcloud führt bei Neuinstallation alle Migrationen aus. Auf leerer Tabelle muss der Schritt ein sauberes No-op mit einer Infozeile sein (Muster `Version001300Date20260924000000::postSchemaChange`). Klassen- und Dateiname zeichengleich, sonst läuft sie still nie (PITFALLS.md, 16-07).

### Pitfall 8: Grenzliste ohne Sprachkontext
Die Store-Texte nennen heute keine einzige Indexsprache (`docs/store-listing.md:146-214`); eine Zeile "Portuguese spelling reform is not unified" ohne vorherige Nennung von es/it/nl/pt liest sich wie ein Fehlerbericht über eine nicht beworbene Funktion. Siehe Open Question 5.

## Code Examples

### Lockfreier Schnellpfad (Skizze, Ort `embed/model.py:511ff`)
```python
# Source: eigener Code, embed/model.py _embed; Schnellpfad vor dem Lock
if not may_load and self._engine is None:
    # A search may not load and nothing is bound: the verdict is known
    # without waiting for a load that holds the lock (V-22-01).
    return EmbedOutcome.unavailable()
with self._lock:
    engine = self._load() if may_load else self._engine
    ...
```

### Warmlauf nach dem Senden (Skizze, Ort `api/search.py:359ff`)
```python
# Source: FastAPI BackgroundTasks, Starlette runs them after the response is sent
from fastapi import BackgroundTasks

@ROUTER.post("/search")
async def search(body: SearchRequest, nc: ..., background: BackgroundTasks) -> SearchResponse:
    ...
    if warm_wanted():
        background.add_task(warm)  # sync function, run in the threadpool after the answer
```
Hinweis: Die `_WARM_TASKS`-Menge (`api/search.py:66-72`) und die Tests, die auf sie warten (`test_search_endpoint.py:763-767`), müssen dann mitwandern.

### Reparatur-Migration (Skizze)
```php
// Source: Muster Version001300Date20260924000000.php; QueueMapper::requeueAs
public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
    $total = 0;
    foreach ($this->goneBands() as $band) {          // SELECT file_id ... state='skipped' AND reason='gone'
        $this->db->beginTransaction();
        try {
            $this->queueMapper->requeueAs($band, QueueMapper::KIND_CONTENT);
            $this->deleteGoneVerdicts($band);         // DELETE ... state='skipped' AND reason='gone' AND file_id IN (...)
            $this->db->commit();
        } catch (\Throwable $e) {
            $this->db->rollBack();
            throw $e;
        }
        $total += count($band);
    }
    $output->info($total === 0 ? 'no gone verdicts to repair' : sprintf('requeued %d files once judged gone', $total));
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Schalter 0: erste semantische Suche lädt im Request | nach Fix: jede Suche lexikalisch ohne Gewichte, Laden im Hintergrund | Phase 23 | Verhalten bei jedem Containerstart ändert sich (Owner-entschieden, D-01) |
| `readerOf` meldet gone, wenn der erste Leser nicht erreicht | gone nur bei leerer Nutzerliste, sonst unreadable | 257caac (26.09.) | Altzeilen brauchen D-04 |
| fastembed als Laufzeitpaket | onnxruntime plus tokenizers direkt | seit Phase 6 im Code, Pin blieb | HART-04 schließt die Lücke |

**Deprecated/outdated:**
- `THIRD-PARTY.md:208,235-243`: fastembed- und requests-Absatz, dazu onnxruntime 1.29.0 statt 1.30.0.
- PROJECT.md:86 "eine Messzahl steht an drei Stellen": seit E1 neun Stellen.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `tokenizers.Tokenizer.from_file` hält den GIL ebenfalls (pyo3 ohne `allow_threads`) | Pattern 3 | gering; das Ladefenster wäre dann nur kürzer als angenommen |
| A2 | Starlette führt `BackgroundTasks` erst nach vollständigem Senden aus, und PHP-cURL erhält die Antwort dadurch vor dem Laden | Pattern 3 | mittel; dann schützt der Umbau die erste Anfrage nicht und die CI-Nachmessung zeigt es |
| A3 | Der CI-Korpus des Upgrade-Asts enthält keine gone-Zeile | Release-Strecke | gering; sonst geht Zusicherung 3 rot und zeigt die Wirkung der Migration an |
| A4 | Das Ladefenster auf der m7g.large liegt bei grob 0,5 bis 1,8 s | Pattern 3 | mittel; abgeleitet aus dem Vorfall 1.838,4 ms (Suche inkl. Laden) und den 95b-Werten, nicht getrennt gemessen |
| A5 | `APPSTORE_TOKEN` ist zum Abgabezeitpunkt noch gültig | Runtime State | gering; die Probe vor dem Dispatch fängt es |

## Open Questions (RESOLVED, Owner-Nachentscheide 27.09., festgehalten als D-08 bis D-11 in 23-CONTEXT.md)

> Aufloesung: OQ1 -> D-08 (Restrisiko akzeptiert, KEIN Schnellpfad in model.py; Plaene 23-01/23-04). OQ2 -> D-09 (730,2 MB; 23-03/23-07). OQ3 -> D-10 (PHPUnit UND Upgrade-CI; 23-05/23-06). OQ4 -> Claude's Discretion in CONTEXT (ja, #14-Fix im Audit; 23-08). OQ5 -> D-11 (Sprachzeile ja; 23-03/23-07). OQ6 -> Claude's Discretion (Quelle je Zahl nennen; 23-03).

1. **Reicht "erste Anfrage geschützt" für D-01?**
   - What we know: Warmlauf nach dem Senden schützt die erste Antwort; im Ladefenster (GIL gehalten) können folgende Anfragen den Deckel reißen; `/snippets` degradiert weich, eine zweite `/search` kann leer enden.
   - What's unclear: wie lang das Fenster auf der Box ist; ob der Owner das Restrisiko hinnimmt.
   - Recommendation: umsetzen (Schnellpfad plus nach dem Senden), in CI die Warmlaufdauer loggen, das Restrisiko im Owner-Checkpoint vor der Abgabe benennen. Weitere Verkürzung (vorab optimiertes Modell per `SessionOptions.optimized_model_filepath` beim Image-Bau) nur als Messfrage, nicht in dieser Phase ohne Owner.

2. **Welche Messzahl trägt 1.3.0: 731,9 MB (v1.2-Abbild) oder 730,2 MB (v1.3-Abbild, C1)?**
   - What we know: beide gemessen, gleiche Messgröße (Marke C, anon, m7g.large). Gate hält `RESIDENT_FIGURE = "731.9"` (`test_store_metadata.py:347`).
   - Recommendation: dem Owner im Textentwurf vorlegen; Empfehlung 730,2 MB, weil sie das ausgelieferte Abbild misst, mit Eintrag im Änderungsprotokoll `docs/store-listing.md:807ff`. Beibehalten ist ebenso vertretbar; dann Satz im Protokoll, warum.

3. **Soll D-04 in CI positiv bewiesen werden?**
   - Recommendation: PHPUnit-Fälle für die neue Migration (leere Tabelle, gone-Zeilen werden eingereiht und gelöscht, andere Gründe bleiben, zweiter Lauf wirft nicht, keine Containerabhängigkeit im Konstruktor) wie `Version001300Date20260924000000Test.php`. Ein E2E-Beweis im Upgrade-Ast (vor dem Upgrade eine gone-Zeile für eine indexierte Datei pflanzen, danach Zusicherung 3 um genau diese Datei bereinigt prüfen) ist stärker, greift aber in eine sorgfältig begründete Zusicherung ein; nur mit eigener Begründung im Kommentar.

4. **Gehört der #14-Fix in den gezielten Bug-/Perf-Audit?**
   - Recommendation: ja, als sechster Pfad neben 18 bis 21 und 23; er ist seit 1.2.0 geändert und ohne eigenes Phasenaudit gemergt. Der Owner hat D-07 als Liste formuliert; eine kurze Rückfrage oder ein Vermerk im Audit reicht.

5. **Nennt der Store-Text die neuen Indexsprachen?**
   - What we know: D-06 legt die Grenzliste fest; eine Sprachzeile ist nicht entschieden; PITFALLS.md:502 und :725 empfehlen sie.
   - Recommendation: im Entwurf als eigene Vorschlagszeile kennzeichnen (Owner-Regel "nur erbetene Änderungen, Extras als Vorschlag"), etwa "Search languages: German and English by default, Spanish, Italian, Dutch and Portuguese available", dreisprachig, ohne Zahl.

6. **Messbericht 21-04, 41,9 gegen 42,1 MB.**
   - What we know: `docs/measurements/2026-09-komposita-nl/README.md:194` nennt 41,9 MB (Quelle Vergleichsmessung, `2026-09-vergleichsmessung-m7g/README.md:215`), `docs/performance.md:4497` zitiert 42,1 MB (grundlast-fein, arm64 nativ).
   - Recommendation: im Bericht die Quelle der Zahl nennen statt still anzugleichen; beide sind Messungen verschiedener Läufe.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | Lockfile, Gates | ✓ | 0.11.7 (gleich CI) | , |
| gh | Laufliste, Dispatch, Release | ✓ | 2.92.0 | , |
| docker | lokale Image-Probe | ✓ | 29.5.2 | CI `docker.yml` |
| php | `php -l` lokal | ✗ | , | `nextcloud:35`-Image wie bei 257caac, sonst CI `php.yml` |
| CI auf main | alle Strecken | ✓ | letzter Push 257caac: 6/6 grün | , |

**Missing dependencies with no fallback:** keine.
**Hinweis:** Das Repo ist ein Git-Worktree auf Windows mit CRLF; die Packstufe verweigert lokal korrekt (16-14), Paketbytes entstehen erst im Tag-Lauf.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein (unverändert, AppAPI-Header) | , |
| V4 Access Control | ja, voll prüfen | Endfilter in PHP (`SearchService` Recheck), Prefilter im Container; #14-Pfade (`PathResolverService`, `GatewayController`, `QueueService::readerOf`) neu seit 1.2.0 |
| V5 Input Validation | ja | Pydantic `extra="forbid"` auf beiden Routen; Migration ohne Fremdeingabe, QueryBuilder mit Parametern |
| V6 Cryptography | ja (Signierung) | `openssl dgst -sha512` in `release.yml`, `integrity:sign-app`; nie selbst gebaut |
| V7 Logging | ja | Warmlauf und Migration loggen nur Zähler und Typnamen (T-14-22, `WARM_TEXT` konstant) |
| V12 Ressourcen | ja | Reparaturlauf erzeugt einmalig Arbeit proportional zur gone-Zahl; Warmlauf bleibt einmal je Fenster (`_WARMING`) |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Suchtext im Log über den Warmlauf | Information Disclosure | nur `WARM_TEXT` geht durchs Modell (`engine.py:108-113`) |
| Warmlauf-Sturm pro Tastendruck | Denial of Service | `_WARMING` plus `_load`-Kopf, Test mit zehn parallelen Läufen |
| Gateway liefert Bytes eines nicht lesbaren Knotens (#14-Nachbarschaft) | Information Disclosure | 257caac: Gateway nur für lesbaren Knoten; im Security-Audit gegenprüfen |
| Store-Token oder Schlüssel in Datei/Log | Information Disclosure | Secret-Store, Cleanup-Schritt `store-submit.yml:165-167`, Geheimnis-Gate |

## Sources

### Primary (HIGH confidence)
- Repository, Stand 0c28b59: alle Datei:Zeile-Angaben oben (engine.py, model.py, search.py, snippets.py, main.py, QueueService.php, QueueMapper.php, FileStateService.php, Migrationen, pyproject.toml, uv.lock, Workflows, docs/)
- onnxruntime v1.30.0, `onnxruntime/python/onnxruntime_pybind_state.cc` Zeilen 2921-2977 und 3013-3016, per curl gelesen: kein GIL-Release beim Sessionaufbau, Release in `run`
- Rohdaten `docs/measurements/2026-09-v13-messung/rohdaten-nachanfahrt/m01-langsame-aufrufe-kaltstart-einwort.txt`, `95c-kaltstart-einwort.txt`

### Secondary (MEDIUM confidence)
- [microsoft/onnxruntime Issue #27063](https://github.com/microsoft/onnxruntime/issues/27063): GIL während Sessioninitialisierung, Januar 2026, ohne Fix geschlossen
- [onnxruntime Python API](https://onnxruntime.ai/docs/api/python/api_summary.html)

### Tertiary (LOW confidence)
- keine

## Metadata

**Confidence breakdown:**
- Standard stack / HART-04: HIGH, Lockfile und grep
- Architektur Kaltstart: HIGH für Codepfade, MEDIUM für Laufzeitwirkung auf der Box
- gone-Reparatur: HIGH, Schreib- und Lesepfade vollständig gelesen
- Release-Strecke: HIGH, Präzedenz 16-07 bis 16-14 und bestehende Workflows
- Pitfalls: HIGH, jede CI-Bruchstelle mit Zeile

**Research date:** 2026-09-26
**Valid until:** 2026-10-10 (Release-Strecke stabil; Token und CI-Stand vor der Abgabe neu prüfen)
