# Phase 35: Stretch: Ähnliche Dokumente und Spikes - Research

**Researched:** 2026-10-19
**Domain:** sqlite-vec-Nachbarabfrage auf Bestandsvektoren (Python-ExApp), serverseitiger Ansichtszweig der Ergebnisseite (PHP-Companion), Messbericht Embedding-Modell (onnxruntime, int8, amd64/arm64), Designnotiz Dedup externer Speicher
**Confidence:** HIGH für Bestand, Gates und Codepfade (Datei:Zeile, gelesen), HIGH für die granite-Fakten (HF-API und Konfigurationsdateien der festgenagelten Revision am 19.10.2026 abgerufen), HIGH für die Nextcloud-Fakten zu Storage-IDs (Quelltext stable34), MEDIUM für Abstandsschwellen und Laufzeiten (müssen gemessen werden)

Stand des Repos: `main` auf `a88de31f` (docs(state): record phase 35 context session).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Bedienung Aehnliche Dokumente (Owner-Entscheide 19.10.2026)
- **D-35-01:** Einstieg pro Treffer als sichtbarer Textlink "Aehnliche
  Dokumente" unter Pfad/Auszug. Eigenes Element im `<li>` NEBEN dem
  Zeilen-Link (die Trefferzeile ist heute EIN `<a>`); zweiter Tab-Stopp pro
  Treffer, kein verschachteltes Interaktivelement im Anker.
- **D-35-02:** Klick fuehrt auf eine neue Serveransicht: GET-Link auf dieselbe
  Ergebnisseite (Parameter in der Art `?similar=fileId`), serverseitig
  gerendert wie Filter und Sortierung heute. Kein neues JS-Muster, der
  Browser-Zurueck-Knopf traegt.
- **D-35-03:** Maximal 10 Nachbarn nach PHP-Rechte-Recheck, dargestellt als
  normale Hit-Liste (Icon, Titel, Pfad) ohne Suchbegriff-Markierung.
- **D-35-04:** Kopf der Aehnlich-Ansicht nennt die Ausgangsdatei ("Aehnlich
  zu: ...") und traegt einen Rueckweg-Link zur vorherigen Trefferliste.

#### granite-Messaufbau (Owner-Entscheide 19.10.2026)
- **D-35-05:** arm64-Messungen auf einer gemieteten AWS-m7g-Instanz, gleiche
  Basis wie docs/measurements/2026-09-vergleichsmessung-m7g. Der Owner gibt
  die Instanz frei (Miet-Start ist ein Checkpoint, nicht autonom).
- **D-35-06:** Qualitaetsvergleich auf dem bestehenden Messkorpus der
  bisherigen docs/measurements-Laeufe (Vergleichbarkeit mit frueheren Zahlen).
- **D-35-07:** Trefferqualitaet ueber feste Frage-Treffer-Paare, VOR der
  Messung definiert (Regel vor der Messung), automatisch auswertbar.

#### Wortlaut-Prozess (Owner-Entscheid 19.10.2026)
- **D-35-08:** Eigener Wortlaut-Plan am Phasenanfang wie 34-01: die neuen
  UI-Saetze (Link "Aehnliche Dokumente", Kopf "Aehnlich zu ...", Rueckweg,
  Leerzustand) werden dem Owner de/en/fr zur Abnahme vorgelegt, BEVOR sie in
  Code und die 16 Kataloge reisen.

#### Form der Dedup-Notiz (Owner-Entscheid 19.10.2026)
- **D-35-09:** Nur interne Entscheidungsvorlage (docs/ bzw. .planning/), kein
  Kommentar-Entwurf fuer Issue #25. Den v1.6-Entscheid faellt der Owner
  spaeter.

### Claude's Discretion
- Verhalten bei 0 Nachbarn (Leerzustand-Wortlaut geht durch den Wortlaut-Plan).
- Ob Filter/Sortier-Zeile in der Aehnlich-Ansicht erscheint.
- Aggregation Chunk-zu-Dokument bei den Vektor-Nachbarn (ein Dokument hat
  viele Chunks), Score-Schnitt, Ausschluss der Ausgangsdatei.
- Routen-/Parameterdesign und access_level der neuen ExApp-Route.
- Methodendetails des int8-Builds fuer granite und Messskript-Aufbau.
- Ablageort und Gliederung der Dedup-Notiz.

### Deferred Ideas (OUT OF SCOPE)
- Embedding-Wechsel auf granite r2: nur wenn STR-02 messbar gewinnt, Bau in
  v1.6 (steht so in REQUIREMENTS.md "Out of Scope").
- #25-Dedup-Bau: erst nach STR-03-Entscheid des Owners (v1.6).
- Kommentar-Entwurf fuer Issue #25: bewusst NICHT Teil dieser Phase (D-35-09).

Zusätzlich gesperrt (ROADMAP SC1, REQUIREMENTS STR-01/02): keine Index-, Schema- oder Modelländerung in v1.5; das ausgelieferte Modell bleibt e5-small.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Beschreibung | Research-Stütze |
|----|-------------|------------------|
| STR-01 | Nutzer ruft auf der Ergebnisseite zu einem Treffer "Ähnliche Dokumente" ab (Vektor-Nachbarn aus dem bestehenden Index, Rechte-Recheck in PHP) | Abschnitte "Architektur STR-01", Muster 1 bis 4, Pitfalls 1 bis 9, Gates-Tabelle. Kernbefund: Nachbarsuche braucht KEIN Modell (Vektor aus dem Bestand, lokal verifiziert), also kein Kaltstart- und kein RAM-Problem |
| STR-02 | Messbericht granite-embedding-97m-multilingual-r2 gegen e5-small (deutscher Korpus, Qualität, CPU-Latenz amd64+arm64, RAM, eigener int8-Build), Empfehlung v1.6; Pflichtpunkte 10.10.: Image-Zuwachs bei zwei Modellen, Dauer Neu-Einbettung auf 4-GB-ARM-Box, Opt-in-Vorschlag bewerten | Abschnitt "Architektur STR-02", granite-Fakten-Tabelle, Pitfalls 10 bis 17, Mess-Rezept mit vorhandenen Werkzeugen (`model_quality.py`, `quantize_model.py`, `findling.embed.bench`, RssAnon-Methode aus `2026-09-fp32-speicher`) |
| STR-03 | Designnotiz #25-Dedup je Mount-Config (fileid-Mapping vs. per-User-Crawl, ACL-Folgen), Entscheidungsvorlage v1.6 | Abschnitt "Architektur STR-03": Issue-Sachstand, Storage-ID-Format aus dem NC-Quelltext, Platzhalter-Ersetzung je Nutzer, ACL-Leck-Fall, Optionen A bis C |
</phase_requirements>

## Project Constraints (from CLAUDE.md und Owner-Regeln)

- Code Englisch; deutsche Prosa mit echten Umlauten, nie Umlaute in Code, URLs, Schlüsseln; keine Em- und En-Dashes (Gate "no dash" auf allen Seitendateien und Messskripten); keine Emojis.
- Python-Gates: ruff-Vollregelsatz, pyright basic (lokal mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`), vulture, Coverage-Gates; lokal grün VOR Commit. Lokal `PYTHONUTF8=1`.
- Kein PHP auf der Entwicklungsmaschine: PHPUnit läuft nur in CI; textuelle Gates in `backend/tests` sind die lokale Absicherung (`test_exapp_call_instrumentation.py` sagt das wörtlich).
- Berechtigungsdurchgriff strikt: Endfilterung in PHP über `SearchService::readableFile` (einzige Stelle mit `getFirstNodeById` und `isReadable`, gezählt von `test_php_acl_boundary.py`).
- Keine Inhalte verlassen den Server, keine Telemetrie; Logs ohne Pfade, Suchbegriffe, Nutzer-IDs.
- Nach jeder Phase Security-, Bug-, Performance-Audit; Befunde vor Abschluss fixen.
- UI-Abnahmen gemeinsam mit dem Owner per Playwright (kein UI-SPEC, Owner-Entscheid 19.10.).
- Messungen: Regel vor der Messung, Ablage `docs/measurements/YYYY-MM-thema/`, Rohdaten neben Skripten, gefahrene Skripte werden nicht nachträglich geändert.
- Commits nur als street1983nk, keine Claude-Trailer.
- Parallel nur mit genug RAM; unter ca. 4 GB frei seriell (betrifft Quantisierung und Qualitätsläufe lokal).
- Fremde Issues: keine Antwort ohne Owner-Wort (D-35-09 bestätigt: kein #25-Kommentar).

## Summary

**STR-01 ist kleiner, als es klingt, und billiger als die normale Suche.** Die int8-Vektoren lassen sich aus `vec0` zurücklesen (lokal mit sqlite-vec 0.1.9 belegt: `SELECT embedding FROM chunk_vectors WHERE rowid = ?` liefert den rohen 384-Byte-Blob, und genau dieser Blob kann direkt wieder als KNN-Anfrage dienen). Damit ist der Anfragevektor der Mittelwert der eigenen Chunk-Vektoren des Ausgangsdokuments, das Modell wird nie geladen, der Kaltstart-Riss der 1,5-s-Decke (api/search.py:294 bis 304) kann nicht auftreten, und der RAM-Preis ist ein einziger Vektorscan (37,8 ms p95 warm, 153,5 ms kalt auf arm64 bei 100.136 Chunks). Kein Schema, kein Index, kein Modell ändert sich. Der Weg ist: PHP prüft zuerst die Ausgangsdatei mit `readableFile`, fragt dann eine neue, nicht in `info.xml` deklarierte Container-Route `/similar` (wie `/search` und `/snippets`), der Container antwortet mit Datei-IDs ohne Score, PHP rechecked jede bis 10 übrig sind, die Seite rendert die bestehende Trefferliste ohne Auszüge.

**STR-02 hat einen gut vorbereiteten Boden, aber drei Fallen, die stumm falsche Zahlen erzeugen.** granite r2 ist Apache-2.0, ModernBERT, 384 Dimensionen (passt in `int8[384]`), CLS-Pooling statt Mittelwert, keine Präfixe, 180.000er Tokenizer mit Pad-Token `<|endoftext|>` statt `<pad>`. Das Messwerkzeug `scripts/dev/model_quality.py` poolt fest per Mittelwert und setzt E5-Präfixe, das Größengatter von `quantize_model.py` liegt bei 100 MB bis 130 MiB und würde die korrekt quantisierte granite-Datei (erwartet rund 97,5 MB = 390.004.608 / 4) als "zu klein" ablehnen. Für arm64 braucht es KEINEN Nextcloud-Wiederaufbau aus dem Snapshot: eine nackte m7g.large mit `mem=4G`, Docker, dem ausgelieferten Image und eingehängten Modelldateien misst Latenz, RAM und Einbettungsdurchsatz; die Neu-Einbettungsdauer wird aus dem Durchsatz auf einer festen Stichprobe des synthetischen Lastkorpus hochgerechnet.

**STR-03 ist im Kern eine ACL-Frage, und der Nextcloud-Quelltext beantwortet die Hälfte.** Die SMB-Storage-ID ist `smb::<auth-user>@<host>//<share>/<root>` (SMB.php:141, stable34), und `$user`-Platzhalter in Share und Root werden je Nutzer ersetzt (ConfigAdapter.php:64 bis 66). Duplikate entstehen also genau bei nutzerspezifischer Authentifizierung; der Dedup-Schlüssel muss Host, Share und Root NACH der Ersetzung sein, nie die Mount-Config-ID allein. Der gefährliche Fall: Nextcloud listet eine Datei im Baum von Nutzer B, aber der SMB-Server verweigert B das Lesen; ein fileid-Mapping würde B einen Auszug aus A's Lesung zeigen. Die Notiz stellt drei Wege (Kanon-Mapping, Inhalts-Hash-Wiederverwendung bei per-User-Crawl, nur Zählung entdoppeln) mit dieser Folge nebeneinander.

**Primary recommendation:** Sechs bis acht kleine Pläne, jeder einzeln streichbar: Wortlaut zuerst (D-35-08), dann Container-Route und PHP-Zweig getrennt, Messvorbereitung lokal vor dem Box-Checkpoint, Bericht, Dedup-Notiz (keine Abhängigkeit zu den anderen), gemeinsame Playwright-Abnahme, Audit.

## Architectural Responsibility Map

| Fähigkeit | Primäre Schicht | Sekundäre Schicht | Begründung |
|-----------|-----------------|-------------------|------------|
| Ausgangsdatei prüfen (darf der Nutzer sie lesen) | PHP-Companion (`SearchService`) | , | Einzige Rechtegrenze des Produkts; muss VOR dem Containeraufruf laufen, sonst ist `/similar` ein Orakel über fremde Dateien |
| Anfragevektor bilden (Mittel der Chunk-Vektoren) | Python-ExApp (`store/vectors.py` liest, `index/search.py` rechnet) | , | Wissen über Speicherformat bleibt in vectors.py (D-08); kein Modell nötig |
| KNN-Scan, Chunk-zu-Dokument, Ausgangsdatei raus, Schwelle | Python-ExApp (`index/search.py`, `index/fusion.py`) | , | `documents_from_chunks` und `near_enough` existieren schon als reine Funktionen |
| Vorfilter wer-sieht-was (Beschleunigung) | Python-ExApp (`_permit` in index/search.py) | , | Über den einen Helfer, damit die Zählgates gleich bleiben |
| Endgültiger Rechte-Recheck der Nachbarn | PHP-Companion (`SearchService::readableFile`) | , | Autorität; Titel/Pfad/Typ/Datum nur vom bestätigten Knoten |
| Ansichtszweig `?similar=`, Kopf, Rückweg-Link | PHP (`PageController`, `templates/search.php`) | Browser (bestehendes `search.js` unverändert) | Serverseitig gerendert wie Chips und Sortierung (D-35-02) |
| Wortlaut, 16 Kataloge, 5 Sprachtabellen | PHP l10n + docs/l10n-*.md | , | Bestehender Katalogprozess, Schlüsselzahl-Gate |
| granite-Messung Qualität/Latenz/RAM | Mess-Container (ausgeliefertes Image, `--network none`) | Gemietete m7g.large (arm64), Entwicklungsrechner (amd64) | Kein Produktcode wechselt das Modell |
| Dedup-Entscheidungsvorlage | Doku (`.planning/phases/35-*/`) | , | Kein Code in v1.5 |

## Standard Stack

Diese Phase installiert **kein neues Paket**, weder im Produkt noch für die Messung. Alles Nötige steht in `backend/uv.lock`:

| Baustein | Version (uv.lock) | Zweck in Phase 35 |
|----------|-------------------|-------------------|
| sqlite-vec | 0.1.9 | Rücklesen der int8-Vektoren, KNN mit gespeichertem Vektor [VERIFIED: lokaler Lauf mit `vec_version() = v0.1.9`] |
| onnxruntime | 1.31.0 | Inferenz beider Modelle in den Messläufen [VERIFIED: uv.lock] |
| tokenizers | 0.23.3 | e5- und granite-Tokenizer (`tokenizer.json`) [VERIFIED: uv.lock] |
| onnx (Gruppe `quantize`) | 1.23.2 | `quantize_dynamic` für den eigenen int8-Build [VERIFIED: pyproject.toml:117] |
| numpy | im Image | Pooling, Normalisierung in den Messskripten |

### Das Modellartefakt (kein Paket, sondern Download einer festgenagelten Revision)

| Fakt | Wert | Quelle |
|------|------|--------|
| Repo, Revision | `ibm-granite/granite-embedding-97m-multilingual-r2` @ `835ad14087e140460703cf0fae09f97d469d65c2` (lastModified 2026-05-18) | [VERIFIED: HF-API] |
| Lizenz | Apache-2.0 (cardData); **keine LICENSE-Datei im Repo** (wie bei e5: Text der Lizenz selbst beilegen) | [VERIFIED: HF-API Dateiliste] |
| Architektur | `ModernBertModel`, 12 Schichten, hidden 384, 12 Köpfe, lokale Aufmerksamkeit 128, global jede 3. Schicht | [VERIFIED: config.json] |
| Dimensionen | 384, also gleiche Spaltenbreite wie e5 (`int8[384]`) | [VERIFIED: config.json, 1_Pooling/config.json] |
| Pooling | CLS (`pooling_mode_cls_token: true`), danach Normalize | [VERIFIED: 1_Pooling/config.json, modules.json] |
| Präfixe | keine (`prompts: {query: "", document: ""}`) | [VERIFIED: config_sentence_transformers.json] |
| Tokenizer | 180.000 Einträge, `tokenizer.json` 25.301.672 Byte, sha256 `4f2842d5...582f`; Pad `<|endoftext|>` (id 179935), CLS `<|startoftext|>` (id 179934), Eingaben nur `input_ids`, `attention_mask` | [VERIFIED: tokenizer_config.json, config.json, HF-API] |
| Kontext | 32.768 Token | [VERIFIED: config.json] |
| fp32 ONNX | `onnx/model.onnx` 390.004.608 Byte, sha256 `68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70` | [VERIFIED: HF-API] |
| Fremd-int8 | `onnx/model_quint8_avx2.onnx` 98.247.878 Byte (x86-AVX2-Profil), `openvino/..._qint8_quantized.bin` 97.950.112 Byte | [VERIFIED: HF-API] |
| Herstellerzahl | MTEB Multilingual Retrieval 60,3 gegen 50,9 (e5-small); keine MIRACL- und keine Deutsch-Einzelzahl | [CITED: huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2] |
| Release | Modellkarte 29.04.2026 | [CITED: Modellkarte] |

**Installation:** keine. Für den int8-Build: `cd backend && uv run --group quantize python ../scripts/dev/quantize_model.py --input <fp32> --output <int8> --min-bytes <..> --max-bytes <..>`.

### Alternativen (bewusst nicht gewählt)

| Statt | Möglich | Warum nicht |
|-------|---------|-------------|
| Mittelwert-Vektor, ein Scan | je Chunk ein Scan, Minimum je Dokument | 2 bis 3 Scans statt einem; bei der 1024-Token-Kappe (D-01) hat ein Dokument nur 2 bis 3 Chunks, der Mittelwert verliert dort wenig. Als Messvariante im Wave-0-Distanzlauf zulässig |
| `quint8_avx2.onnx` von IBM | eigener `quantize_dynamic`-Lauf aus fp32 | Projektregel seit 06-01: ein Verfahren für beide Modelle, reproduzierbar, nicht x86-profiliert. Die IBM-Datei darf als Vergleichspunkt mitgemessen werden |
| Snapshot-Wiederaufbau der Messbox (Runbook) | nackte m7g.large mit Docker | Der Wiederaufbau ist der teure, nie ganz gefahrene Pfad (runbook-messbox.md 1.1); STR-02 braucht keine Nextcloud |

## Package Legitimacy Audit

Keine externen Pakete werden installiert. `uv.lock` bleibt unverändert; das granite-Artefakt ist ein Modelldownload von einer festgenagelten Revision mit sha256-Prüfung (Muster `backend/Dockerfile:138 bis 158`), kein Registry-Paket.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (keines) | , | , | , | , | nicht nötig | , |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architektur STR-01: Ähnliche Dokumente

### Datenfluss

```
Browser: Klick auf Textlink "Ähnliche Dokumente" im <li> eines Treffers
   |  GET /apps/findling/?query=..&page=..&cursors=..&fp=..&similar=<id>
   v
PageController::index
   |-- similar ungültig (keine Ziffernfolge, <= 0, zu lang) --> normale Ergebnisseite, still
   |-- similar gültig --> SearchService::similar(user, id, caps)
          |
          |-- readableFile(userFolder, id) == null --> Zustand "Datei nicht verfügbar"
          |       (gleich für: existiert nicht, fremd, gelöscht, kein Leserecht)
          |
          |-- ExAppService::similarCandidates(uid, id, limit, Restzeit, Decke)
          |       POST /similar {fileId, limit}   (AppAPI-signiert, nicht in info.xml)
          |       v
          |   ExApp api/similar.py --> index/search.py::similar_candidates
          |       1. _permit(store, uid, [Quelle])  leer --> []
          |       2. vectors.vectors_of(id)          leer --> []  (nie eingebettet)
          |       3. Mittelwert, normieren, to_int8
          |       4. vectors.nearest(vec, k=SCAN, k_max=SCAN)
          |       5. Chunks der Quelle raus, Schwelle (ceiling), documents_from_chunks
          |       6. _permit(store, uid, Top-Fenster) --> Datei-IDs, ohne Score
          |       v
          |   {candidates:[{fileId}], degraded}
          |
          |-- reduceIds (Storage-Vorauswahl) + readableFile je Kandidat, bis 10 oder Budget
          v
   SimilarOutcome(source: ApprovedHit, hits: list<ApprovedHit>, failure)
   v
templates/search.php: Kopf "Ähnlich zu: <Titel aus Knoten>", Rückweg-Link,
   bestehende <ol class="findling-hits"> ohne Auszug, ohne Filterzeile, ohne Blättern
```

### Komponenten und Dateien

| Datei | Änderung |
|-------|----------|
| `backend/src/findling/store/vectors.py` | neue Methode `vectors_of(file_id) -> list[bytes]` (Chunk-Vektoren in Ordinalreihenfolge); KEIN Wort über Rechte (Gate in test_semantic_boundary.py:287) |
| `backend/src/findling/index/search.py` | neue Funktion `similar_candidates(...)`, ruft `_permit` (nicht den Vorfilter direkt) |
| `backend/src/findling/api/similar.py` (neu) | `POST /similar`, `SimilarRequest` mit `extra="forbid"`, Nutzer nur aus `Depends(anc_app)`, `asyncio.to_thread`, alle Fehler als leere Antwort mit `degraded` |
| `backend/src/findling/main.py` | `APP.include_router(SIMILAR_ROUTER)` (bei main.py:1350) |
| `backend/src/findling/config.py` | Konstanten `SIMILAR_SCAN_CHUNKS`, `SIMILAR_CEILING` (gemessen, siehe Pitfall 3), ggf. `SIMILAR_WINDOW` |
| `backend/appinfo/info.xml` | **unverändert**: `/similar` wird wie `/search`, `/snippets` NICHT deklariert (Kommentar info.xml:283 bis 295 erweitern) |
| `php/lib/Service/ExAppService.php` | `similarCandidates(string $userId, int $fileId, int $limit, float $secondsLeft, float $ceilingSeconds): ?array`, über das bestehende `call()` |
| `php/lib/Service/SearchService.php` | `similar(IUser, int, SearchCaps): SimilarOutcome`, nutzt `readableFile`, `reduceIds`, `mountsOfUser` |
| `php/lib/Service/SimilarOutcome.php` (neu, optional) | Wertobjekt; alternativ `SearchOutcome` wiederverwenden plus Quelle |
| `php/lib/Controller/PageController.php` | Zweig in `index()`, Link-Bau je Treffer (`similarUrl`), Rückweg-URL; **keine neue Route** (sonst Gate test_php_trust_boundary.py) |
| `php/templates/search.php` | zweites `<a>` im `<li class="findling-hit">` nach `</a>` (search.php:483), Kopfblock, Leerzustände |
| `php/css/search.css` | Klasse für den Textlink (Seiten-Stylesheet, Gate "no dash" gilt) |
| `php/l10n/*.json, *.js` (16) und `docs/l10n-{french,spanish,italian,dutch,portuguese}.md` | neue Schlüssel aus dem Wortlaut-Plan |
| `php/tests/Unit/{PageControllerTest,SearchServiceTest,ExAppServiceTest}.php` | Fälle, laufen nur in CI |

### Muster 1: Anfragevektor aus dem Bestand

**Was:** Die Chunk-Vektoren des Ausgangsdokuments zurücklesen, als vorzeichenbehaftete Bytes deuten, mitteln, normieren und mit der Projekt-Funktion `to_int8` (embed/model.py:245) zurückquantisieren. Ein KNN-Scan.
**Warum Mittelwert:** ein Scan statt n; Dokumente haben unter D-01 nur 2 bis 3 Chunks (vectors.sql:25 bis 33).
**Wo:** Lesen in `store/vectors.py` (einzige Stelle mit vec0-Wissen, D-08), Rechnen in `index/search.py` (oder `fusion.py`, dort ist es eine reine Funktion und leicht testbar).

### Muster 2: Ein Recheck-Weg, keine zweite Grenze

`SearchService::similar` gehört in **dieselbe** Klasse wie `run()` und ruft `self::readableFile`. `test_php_acl_boundary.py` zählt nur direkte `getFirstNodeById`/`isReadable`-Aufrufe (RESOLUTION_REGISTER = {SearchService.php: 1}); Aufrufe von `readableFile` sind erlaubt (GatewayController, QueueService tun es schon). Zuerst die Quelle, dann die Nachbarn, Titel/Pfad/Mime/Datum nur vom bestätigten Knoten (SearchService.php:430 bis 458 als Vorlage).

### Muster 3: Undeklarierte Inhaltsroute

`/similar` ist eine Inhaltsroute im Sinne von info.xml:283 bis 295 (sie verrät über Nachbarschaft etwas über Dokumente). Nicht deklarieren, `CONTENT_ROUTES` in `test_info_xml_defaults.py:127` um `/similar` erweitern, `KNOWN_ROUTES` in `test_semantic_boundary.py:73` ergänzen (Ratsche mit Begründungssatz). Der Pfadname darf weder "semantic" noch "vector" enthalten (test_semantic_boundary.py:62), "similar" ist zulässig.

### Muster 4: Ansicht als GET-Zustand der bestehenden Seite

Der Link je Treffer trägt den kompletten Zustand der Ursprungsseite (`filterUrl`/`pageUrl` mit `page`, `cursors`, `fp`) plus `similar=<id>`. Der Rückweg-Link ist dieselbe Adresse ohne `similar`. `search.js` bleibt unverändert und funktioniert mit: der Klick auf den Textlink liegt innerhalb von `.findling-hit`, also schreibt der delegierte Handler (search.js:181 bis 186) die Zeile der Ausgangsdatei; beim Rückweg markiert `pageshow` genau diese Zeile. In der Ähnlich-Ansicht: keine Filter-/Sortierzeile (die Nachbarabfrage filtert nicht, die Zeile würde Wirkung vortäuschen), kein Blättern (max. 10), kein weiterer Ähnlich-Link je Nachbar (eine Ebene, Rückweg bleibt eindeutig) [Empfehlung, Claude's Discretion].

### Anti-Patterns

- **Vorfilter direkt in einer neuen Funktion von index/search.py aufrufen:** `test_search_library.py:309` zählt den Namen roh im Quelltext (auch Docstrings) == 2, `test_semantic_boundary.py:252` verlangt die Aufrufer `["_permit", "snippets_for"]`. Neue Funktion ruft `_permit`, und der Name des Vorfilters kommt in keinem neuen Kommentar dieser Datei vor.
- **Container zuerst fragen, Quelle danach prüfen:** macht `/similar` zum Orakel ("zu Datei 4711 gibt es Nachbarn").
- **Distanz oder Score über die Leitung:** `Neighbour` und `Candidate` sind bewusst inhaltsarm (D-14); die Antwort trägt nur Datei-IDs in Rangfolge.
- **Neue Controller-Route `/similar` in PHP:** `test_php_trust_boundary.py` zählt Routenattribute; der Zweig gehört in `index()`.
- **`snippets()` für die Nachbarn rufen:** braucht einen Suchbegriff (ExAppService.php:528 bis 531) und D-35-03 will keine Markierung.

## Architektur STR-02: granite-Messbericht

### Ablage und Ablauf

`docs/measurements/2026-10-granite-vergleich/` mit `README.md` (Regel vor der Messung als erster Abschnitt, vor dem ersten Lauf committet), `skripte/`, `rohdaten/`. Den neuen `skripte/`-Ordner in `NARROW_SCOPE_DIRS` (test_measurement_scripts.py:112) aufnehmen, dann gelten Shebang, kein Maschinenpfad, kein Passwort auf der Kommandozeile; die weite Regel (kein CR, kein Dash) gilt ohnehin.

| Schritt | Ort | Werkzeug (vorhanden) | Liefert |
|---------|-----|---------------------|---------|
| 0. Regel vor der Messung | Repo | README | Entscheidungsregel (siehe unten), feste Fälle, Kommandozeilen |
| 1. Artefakte holen und prüfen | Entwicklungsrechner | curl + sha256 (Muster Dockerfile:138 ff.) | fp32, tokenizer, configs der Revision `835ad140` |
| 2. int8-Build | Entwicklungsrechner, seriell | `quantize_model.py` mit eigenem Fenster | Größe, sha256, zweiter Lauf byteidentisch (Reproduzierbarkeit wie 2026-09-05) |
| 3. Qualität | Entwicklungsrechner, `--network none` | `model_quality.py` erweitert um `--pooling {mean,cls}` (Standard `mean`, damit alte Läufe gleich bleiben) | Recall@1/@5, MRR, `--per-case`, Paartest e5 gegen granite |
| 4. Latenz amd64 | Entwicklungsrechner, gepinnte Kerne (`--cpuset-cpus`), 2 Threads | `python -m findling.embed.bench --mode tokens-per-second` mit eingehängtem Modellordner, plus Einzelanfrage-Latenz (Suchpfad) | Token/s, ms je Anfrage p50/p95 |
| 5. Box-Checkpoint | Owner gibt m7g.large frei | `scripts/ops/aws_box.sh` (Preise, Status) | Instanz, `mem=4G`, Kostendeckel |
| 6. arm64 Latenz, RAM, Durchsatz | m7g.large, Container `--memory 2g`, 2 Threads | bench (Schritt 4), RssAnon-Methode aus `2026-09-fp32-speicher` Abschnitt 3 | wie 4, plus anon vor/nach Laden und erster Charge, `memory.peak` |
| 7. Neu-Einbettungsdauer | m7g.large | Einbettungsdurchsatz auf fester Stichprobe des Lastkorpus (`build_load_corpus.py --seed phase5`, Teilmenge per Seed festgelegt), Chunking je Modell-Tokenizer | Dokumente/min beider Modelle, Hochrechnung auf 52.111 Dokumente |
| 8. Image-Zuwachs | Entwicklungsrechner | Dateigrößen + `gzip -c | wc -c` je zugefügter Datei (Schichtabschätzung), optional Probe-Image | MB unkomprimiert/komprimiert für "zwei Modelle im Image" |
| 9. Bericht + Empfehlung + Opt-in-Bewertung | Repo | , | Verdikt v1.6 |

**Entscheidungsregel (Vorschlag für den README-Kopf, Owner kann vor der Messung ändern):** granite wird für v1.6 empfohlen, wenn (a) auf Deutsch die ausgelieferte Kombination int8-Modell/int8-Vektoren im Paarvergleich gegen e5 nicht schlechter ist und der Vorzeichentest über bewegte Fälle eine Verbesserung zeigt, (b) keine der drei Sprachen mehr als 5 Prozent relativen MRR-Rückgang gegen e5 zeigt (die D-02-Grenze aus 2026-09-05, Messpunkt ausgelieferte Kombination), (c) die anon-Spitze von Laden plus erster Charge unter der 2-GiB-Containergrenze mit dem bisherigen Abstand bleibt, (d) die Einzelanfrage auf arm64 kalt unter der 1,5-s-Decke bleibt. Sonst "kein Wechsel" oder "Wechsel nur mit Bedingung" mit Begründung.

**Feste Fälle (D-35-06, D-35-07):** `testdata/semantik/{de,en,fr}.jsonl` (42/42/120 Paare, Wortüberschneidungsverbot per Test, schon Grundlage von 2026-09-05). Vergleichbarkeit: e5-Zahlen werden im selben Lauf neu erhoben, nicht aus dem September-Bericht übernommen (anderes onnxruntime: 1.29.0 damals, 1.31.0 heute).

### Bewertung des Opt-in-Vorschlags: was der Bericht beantworten muss

"Neuinstallation Standard granite, Bestand optional per Opt-in mit Rückweg" berührt diese Stellen, die der Bericht einzeln bewerten sollte (Bau erst v1.6):
- Zwei Modelle im Image (Image-Zuwachs, Schritt 8); Lizenzdatei für granite wie `COPYING.multilingual-e5-small` (Dockerfile:383 bis 389), `THIRD-PARTY.md`, `test_third_party_versions.py`.
- Embedding-Marke: `embedding_mark` (vectors.py:271) trägt den Modellnamen, ein Wechsel ist also eine Drift, die bisher "alles neu einbetten" auslöst. Während der Neu-Einbettung sind e5-Bestand und granite-Anfrage unvergleichbar: entweder Semantik aus (nur Volltext), oder zweite `vectors.db` je Modell und atomarer Wechsel (Rückweg = alte Datei behalten; Platz: 438 Byte je Chunk, rund 44 MB je 100.000 Chunks).
- Chunker: anderer Tokenizer, andere Chunkgrenzen und -zahl; Pad-Token, Pooling und Präfixe im Modell-Wrapper (embed/model.py:83, 108, 316 bis 326, 767 bis 776) sind e5-fest.
- Distanzriegel neu kalibrieren (ceiling 86,5 und band 14,0 aus 2026-09-06 gelten nur für e5) und die neue Ähnlich-Schwelle aus STR-01 ebenso.
- Dauer der Neu-Einbettung auf der 4-GB-Box (Schritt 7) neben dem e5-Bezug: 26 h 37 min gekoppelt, rund 170 Dokumente/min Einbettung allein (vergleichsmessung-m7g Abschnitt 7).

## Architektur STR-03: Dedup-Designnotiz #25

**Ablage (Empfehlung):** `.planning/phases/35-stretch-aehnliche-dokumente-und-spikes/35-DEDUP-NOTIZ.md`. `.planning/` ist im öffentlichen Repo versioniert; "intern" heißt hier: nicht im Issue, nicht in der Nutzerdoku `docs/`. Daraus folgt: **keine Nutzernamen, Hostnamen oder Share-Namen aus dem Issue übernehmen** (dort stehen fünf Nutzernamen und `smb::mbozem@...`), nur aggregierte Zahlen.

### Sachstand aus Issue #25 (gelesen 19.10.2026)

| Fakt | Wert | Quelle |
|------|------|--------|
| Instanz des Melders | NC 34.0.4, Findling 1.4.1, 4 SMB-Shares je Nutzer eingebunden, 116 smb-Storages | Issue-Text |
| Nenner | 1.640.911 files_seen, davon 324.530 aus 10 eingefrorenen Storages, 1.316.381 live | Kommentar Melder |
| Urteilszeilen | 205.522 in `oc_findling_file_state` über 24 Storages, nur 39.209 eindeutige (Share, Pfad); 9.075 Pfade mit je 6 Kopien, 5.351 mit je 9 | Kommentar Melder |
| Bereits gefixt (1429eebc) | Nenner nur über Storages mit Mount; Seite nennt Mehrfachzählung, wenn sonst alles erklärt ist | Owner-Kommentar, docs/admin-page.md:130 bis 145 |
| Offen | "echte Dedup je Mount-Config, braucht zuerst die ACL-Antwort" | Owner-Kommentar |

### Nextcloud-Fakten, die die Notiz tragen

- SMB-Storage-ID: `'smb::' . <auth-user> . '@' . <host> . '//' . <share> . '/' . <root>` (apps/files_external/lib/Lib/Storage/SMB.php:137 bis 142, stable34) [VERIFIED: Quelltext]. Gleiche Share, andere Anmeldung = andere Storage = eigener Filecache-Baum = andere fileids.
- Platzhalter: `prepareStorageConfig` ersetzt `$user` u. a. in jeder Backend-Option je Nutzer (ConfigAdapter.php:64 bis 66) [VERIFIED: Quelltext]. Eine Mount-Config mit `$user` im Share oder Root zeigt je Nutzer **andere** Daten; ein Schlüssel nur aus der Mount-Config-ID würde fremde Inhalte verschmelzen.
- Authentifizierung: "Benutzername und Passwort" und "Globale Anmeldedaten" sind nicht nutzerspezifisch (eine Storage-ID für alle, kein Duplikat); "Log-in credentials (Session/Datenbank)" und "User entered" verbinden je Nutzer einzeln [CITED: docs.nextcloud.com/.../auth_mechanisms.html]. Session-Anmeldedaten erlauben kein Hintergrund-Scannen [CITED: ebd.].
- Findling indexiert je fileid; die ACL-Tabelle in state.db ordnet fileid zu Nutzern (Vorfilter), PHP rechecked je fileid.

### Die drei Wege, die die Notiz vergleicht

| Weg | Kern | ACL-Folge | Spart |
|-----|------|-----------|-------|
| A. fileid-Mapping (Kanon + Alias) | Schlüssel (Backend-Typ, Host, Share, Root nach Ersetzung, Pfad); eine Kopie wird gelesen und indexiert, andere fileids werden Alias; PHP übersetzt Kanon-ID in die eigene Alias-fileid des Fragenden und rechecked diese | **Leck-Fall:** Nextcloud listet die Datei in B's Baum (`isReadable` true), der SMB-Server verweigert B aber das Lesen; B bekäme Auszüge aus A's Lesung. Ohne ACL-Prüfung des Backends (SMB-Option "ACL prüfen", SMB.php:214) nicht ausschließbar | Lesen, OCR, Einbettung, Indexplatz |
| B. per-User-Crawl mit Inhalts-Hash-Wiederverwendung | Jede Kopie wird mit den Anmeldedaten ihres Nutzers geladen (beweist Leserecht), gehasht; gleicher Hash wie ein indexiertes Dokument mit gleichem Schlüssel: Text, Chunks und Vektoren werden unter der neuen fileid übernommen, keine OCR, keine Einbettung | ACL bleibt je fileid durch Konstruktion korrekt | OCR und Einbettung (der teure Teil), nicht Download und nicht Indexplatz |
| C. Nur die Zählung entdoppeln | Nenner und Zähler je Schlüssel zählen | keine | nichts an Arbeit, nur die Anzeige |

Empfehlung für die Notiz (Owner entscheidet): B als Standard (ACL-sicher), A nur als ausdrückliches Admin-Opt-in je Mount-Config ("alle Nutzer sehen auf dieser Share dieselben Rechte"), C sofort als billige Ergänzung. Der Melder hätte mit B rund 81 Prozent der OCR-/Einbettungsarbeit gespart (39.209 eindeutige gegen 205.522 Zeilen; Schätzung aus seinen Zahlen) [ASSUMED: Hochrechnung].

## Don't Hand-Roll

| Problem | Nicht bauen | Stattdessen | Warum |
|---------|-------------|-------------|-------|
| Chunk-zu-Dokument | neue Aggregation | `fusion.documents_from_chunks` (kleinste Distanz, Tie-Break chunk_id) | getestet, D-11, gleiche Ordnung wie die Suche |
| Abstandsgrenze | eigene Filterlogik | `fusion.near_enough` mit eigener `ceiling`, `band` = Ceiling (wirkt dann nicht) | Randfälle (leere Liste, Minimum statt erstes Element) schon gelöst |
| int8-Quantisierung des Anfragevektors | eigene Rundung | `embed.model.to_int8` | Klemmung gegen 128-Überlauf (model.py:254 bis 258) |
| Rechte-Recheck | eigene Knotenauflösung | `SearchService::readableFile` | einzige zugelassene Stelle, Gate |
| Storage-Vorauswahl | eigene Mount-Abfrage | `SearchService::reduceIds` + `mountsOfUser` | zwei Abfragen statt n |
| Proxy-Aufruf, Zeitbudget | eigener cURL | `ExAppService::call()` mit `secondsLeft`/`ceilingSeconds` | Größen-, Zeit- und Fehlerbehandlung, Instrumentierungs-Gate |
| int8-Modellbau | eigenes Quantisierungsskript | `scripts/dev/quantize_model.py` mit `--min-bytes/--max-bytes` | reproduzierbar belegt, Größengatter |
| Qualitätsmessung | neues Skript | `scripts/dev/model_quality.py` + Pooling-Schalter | gleiche Metriken und `--per-case` wie 2026-09-05 |
| Durchsatz | eigene Zeitschleife | `findling.embed.bench --mode tokens-per-second` | druckt Hardware mit, liest Eingabenamen aus der Session |
| RAM-Messung | ps/top | RssAnon-Methode `docs/measurements/2026-09-fp32-speicher` Abschnitt 3, cgroup `memory.peak` | vergleichbar mit allen früheren Zahlen |
| Box | Snapshot-Wiederaufbau | nackte m7g.large, `aws_box.sh prices/status`, Kostendeckel-Rechenblatt runbook-messbox.md Abschnitt 2 | Deckel-Disziplin bleibt, Aufwand fällt |

## Common Pitfalls

### Pitfall 1: Orakel über fremde Ausgangsdateien
**Was schiefgeht:** `/similar` wird mit einer fremden fileid gefragt, und die Ansicht unterscheidet "Datei fremd" von "Datei unbekannt" oder zeigt Nachbarn.
**Vermeidung:** PHP rechecked die Quelle vor dem Containeraufruf; ein einziger Zustand "nicht verfügbar" für alle Fehlschläge; der Container prüft die Quelle zusätzlich über `_permit` (Tiefenverteidigung).
**Warnzeichen:** ein PHPUnit-Fall, in dem `similarCandidates` aufgerufen wird, obwohl `getFirstNodeById` null liefert.

### Pitfall 2: Verdrängung durch fremde Nachbarn
**Was:** Der KNN-Scan liefert k Chunks über den ganzen Bestand; liegen die nächsten Chunks in fremden Dokumenten, fallen die eigenen aus dem Fenster und die Liste wird kürzer. Schwaches Signal "es gibt Fremdes, das ähnlich ist".
**Vermeidung:** großes `k` (der Scan kostet unabhängig von k dasselbe, vectors.py:488 bis 498), dann Vorfilter, dann Fenster; `k_max` explizit am Aufruf. Gleiche Klasse wie bei der normalen Semantik (Fenster 100), im Audit als bekannt benennen.

### Pitfall 3: Die Distanzschwelle der Suche passt nicht
**Was:** `ceiling` 86,5 und `band` 14,0 sind für Anfrage gegen Abschnitt mit E5-Präfixen gemessen (2026-09-06-vektordistanzen). Dokument gegen Dokument ("passage" gegen "passage") liegt auf einer anderen Verteilung; das Band würde eine Ähnlich-Liste auf den nächsten Cluster kürzen.
**Vermeidung:** eigener kleiner Distanzlauf in Wave 0 (Regel vor der Messung): Abstände Dokument-Mittel gegen Dokument auf `testdata/corpus` und den Passagen von `testdata/semantik`, daraus `SIMILAR_CEILING`; Band nicht verwenden. Ohne Schwelle füllt ein kleiner Bestand die Liste mit Unbeteiligtem (der Befund von CI-Lauf 34031891300 in neuer Form).

### Pitfall 4: Die Quelle als ihr eigener Nachbar, und echte Kopien
**Was:** Die Chunks der Quelle liegen bei Distanz nahe 0. Echte Kopien (gleicher Inhalt, andere fileid) ebenfalls.
**Vermeidung:** alle Treffer mit `file_id == Quelle` vor der Aggregation entfernen und `k` um die Chunkzahl der Quelle erhöhen. Kopien bleiben (sie sind andere Dateien des Nutzers); im Audit/Wortlaut erwähnen.

### Pitfall 5: Zählgates in index/search.py
**Was:** `test_search_library.py:309` zählt `prefilter_visible` roh == 2, auch in Docstrings; `test_semantic_boundary.py` verlangt Aufrufer `_permit` und `snippets_for`.
**Vermeidung:** nur `_permit` aufrufen, den Vorfilter-Namen in neuen Kommentaren nicht ausschreiben.

### Pitfall 6: Routen-Ratschen
**Was:** `KNOWN_ROUTES` (test_semantic_boundary.py:73) und `CONTENT_ROUTES` (test_info_xml_defaults.py:127) sind Ratschen; eine neue Route ohne Eintrag macht die Suite rot, ein Eintrag in info.xml öffnet sie für jeden Nutzer.
**Vermeidung:** beide Listen im selben Commit, info.xml nur im Kommentar.

### Pitfall 7: Baumhash-Ratschen und Schlüsselzahl
**Was:** `PHP_FILES_TODAY = 105`, `PHP_TREE_HASH_TODAY` (test_measurement_scripts.py:983) über `php/**/*.php` (inklusive `php/tests`); `PACKAGE_FILES_TODAY = 79`, `PACKAGE_TREE_HASH_TODAY` (Zeile 2032) über `backend/src/findling/**/*.py`. Neue Datei `api/similar.py` hebt 79 auf 80. Die Katalog-Schlüsselzahl steht bei **341** (test_admin_ui_contract.py, Absatz "It stands at 341 since 19.10.2026"), jede Änderung braucht den nächsten Absatz.
**Vermeidung:** je Plan, der php/ oder backend/src anfasst, Journalabsatz und neue Hash-Werte im selben Commit; Kataloge sind nicht im PHP-Baum (Rezept globt `*.php`).

### Pitfall 8: Leerzustände und Zählorakel auf der Seite
**Was:** `scan_page_template_for_an_unguarded_empty_state` und `scan_filter_row_for_a_counting_oracle` (test_admin_ui_contract.py um 1660 und 1790) prüfen search.php. Ein "3 von 10 ausgeblendet" wäre ein Zählorakel über fremde Dokumente.
**Vermeidung:** Leerzustände der Ähnlich-Ansicht hinter derselben Entscheidung wie Banner; keine Zahl über ausgefilterte Nachbarn.

### Pitfall 9: Gleichlautende Linktexte
**Was:** 25 Links "Ähnliche Dokumente" auf einer Seite sind für Screenreader in der Linkliste ununterscheidbar.
**Vermeidung:** `aria-label` mit Titel (Muster `'%1$s in %2$s'` in search.php:457), im Wortlaut-Plan mit abnehmen lassen.

### Pitfall 10: Größengatter lehnt korrektes granite-int8 ab
**Was:** `quantize_model.py` Standardfenster 100.000.000 bis 136.314.880 Byte; granite fp32 390.004.608 / 4 = 97.501.152 Byte, also unter der Untergrenze. Die Begründung im Skript (Einbettungstabelle 81,7 Prozent) gilt für e5; bei granite sind es 180.000 x 384 = 69,1 Mio. von 97,4 Mio. Parametern, rund 71 Prozent [VERIFIED: Rechnung aus config.json].
**Vermeidung:** Fenster per `--min-bytes`/`--max-bytes` am Aufruf, im README begründet (z. B. 85.000.000 bis 110.000.000); Gegenprobe "Tabelle blieb fp32" läge bei rund 300 MB. Standardwerte des Skripts nicht ändern (sie sichern das ausgelieferte e5).

### Pitfall 11: Mittelwert-Pooling und Präfixe auf granite
**Was:** `model_quality.py` poolt fest per Maske-Mittelwert (`mean_pool`, Zeile 224) und setzt `query: `/`passage: `; granite ist CLS ohne Präfixe. Ergebnis wären plausible, aber falsche Zahlen.
**Vermeidung:** Schalter `--pooling cls|mean` (Standard mean, bestehende Tests grün), granite immer mit `--prefixes off --pooling cls`; Positivkontrolle: granite mit mean muss messbar schlechter sein, sonst greift der Schalter nicht.

### Pitfall 12: Pad-Token
**Was:** Produktcode sucht `<pad>`, Rückfall `[PAD]` mit id 0 (model.py:108, 316 bis 326). granite hat `<|endoftext|>` (179935). Für die Messung irrelevant, solange die Attention-Maske mitgeht; für v1.6 ein stiller Fehler.
**Vermeidung:** Messskripte lesen das Pad-Token aus `tokenizer_config.json`; im Bericht als v1.6-Baupunkt aufführen.

### Pitfall 13: Sequenzlänge
**Was:** granite verträgt 32k Token, e5 512. Ein Vergleich bei unterschiedlicher Länge misst nicht dasselbe.
**Vermeidung:** Qualität und Durchsatz beider Modelle bei 512 (wie Produkt); granite bei 1024 nur als zusätzliche, klar getrennte Zeile.

### Pitfall 14: Vergleich gegen alte e5-Zahlen
**Was:** 2026-09-05 lief auf onnxruntime 1.29.0 und einem anderen Image; heute 1.31.0.
**Vermeidung:** e5 im selben Lauf neu messen, alte Zahlen nur als Plausibilität.

### Pitfall 15: Box-Kosten und Wiederaufbau
**Was:** Die September-Box existiert nicht mehr (runbook-messbox.md 1.1); der Snapshot-Pfad ist lang. Der v1.1-Deckel riss an einer unterschätzten Laufzeit.
**Vermeidung:** nackte Instanz, Deckel vorab nach runbook Abschnitt 2 rechnen, Owner-Freigabe als `checkpoint:human-action`, Rohdaten vor dem Abbau committen, Abbau mit Belegzeile.

### Pitfall 16: Neu-Einbettung hochrechnen statt 26 Stunden fahren
**Was:** Ein Volllauf kostet einen Tag Box; die Frage "wie lange" lässt sich aus dem Durchsatz beantworten, aber nur mit der Chunkzahl des jeweiligen Tokenizers.
**Vermeidung:** Stichprobe fest (Seed, Dateiliste im README), Chunking je Tokenizer bei 1024-Token-Kappe, Hochrechnung mit ausgewiesener Annahme; der gekoppelte September-Wert (26 h 37 min) bleibt Bezug für e5.

### Pitfall 17: Arbeitsspeicher der Entwicklungsmaschine
**Was:** unter 4 GB frei; `quantize_dynamic` auf 390 MB und zwei Modelle gleichzeitig können swappen und Zeiten verfälschen.
**Vermeidung:** alle lokalen Schritte seriell, Latenz lokal nur ohne Parallellast; Zeiten amd64 notfalls auf einer kleinen x86-Box (hetzner_box.sh vorhanden) und das im README begründen.

## Code Examples

### Vektoren zurücklesen (store/vectors.py)
```python
# Verifiziert lokal 19.10.2026 mit sqlite-vec 0.1.9: ein int8-vec0-Feld kommt als
# BLOB mit einem Byte je Dimension zurueck.
_VECTORS_OF_SQL: Final = """
SELECT v.embedding
FROM chunks AS c
JOIN chunk_vectors AS v ON v.rowid = c.chunk_id
WHERE c.file_id = ?
ORDER BY c.ordinal
"""

def vectors_of(self, file_id: int) -> list[bytes]:
    """The stored vectors of one document, in ordinal order, or an empty list."""
    return [bytes(row[0]) for row in self._conn.execute(_VECTORS_OF_SQL, (file_id,))]
```

### Mittelwert als Anfragevektor
```python
import math

from findling.embed.model import to_int8


def centroid(vectors: Sequence[bytes]) -> bytes | None:
    """Mean of int8 vectors, renormalised, back on the int8 scale of the stock."""
    if not vectors:
        return None
    sums = [0.0] * len(vectors[0])
    for vector in vectors:
        for index, byte in enumerate(vector):
            sums[index] += byte - 256 if byte > 127 else byte
    length = math.sqrt(sum(value * value for value in sums))
    if length == 0.0:
        return None
    return to_int8([value / length for value in sums])
```

### Ablauf im Container (index/search.py, Skizze)
```python
def similar_candidates(store: Store, vectors: VectorStore, uid: str, file_id: int, limit: int) -> list[int]:
    if not _permit(store, uid, [Candidate(file_id=file_id, score=0.0, mtime=0)]):
        return []
    query = centroid(vectors.vectors_of(file_id))
    if query is None:
        return []
    neighbours = vectors.nearest(query, SIMILAR_SCAN_CHUNKS, k_max=SIMILAR_SCAN_CHUNKS)
    hits = [
        ChunkHit(file_id=n.file_id, chunk_id=n.chunk_id, distance=n.distance)
        for n in neighbours
        if n.file_id != file_id
    ]
    near = near_enough(hits, ceiling=SIMILAR_CEILING, band=SIMILAR_CEILING)
    ranked = [Candidate(file_id=d.file_id, score=0.0, mtime=0) for d in documents_from_chunks(near)]
    return [c.file_id for c in _permit(store, uid, ranked)][:limit]
```

### Parameter in PHP (PageController, still verwerfen wie alle Adresswerte)
```php
private function similarId(): ?int {
	$raw = $this->request->getParam('similar', '');
	if (!is_string($raw) || preg_match('/^[1-9][0-9]{0,18}$/', $raw) !== 1) {
		return null;
	}
	$id = (int)$raw;
	return $id > 0 ? $id : null; // 19 digits can overflow to PHP_INT_MAX; still positive, still rechecked
}
```

### Textlink im Treffer (templates/search.php, nach dem Zeilen-Link)
```php
</a>
<a class="findling-hit__similar" href="<?php p($hit['similarUrl']); ?>"
	aria-label="<?php p($l->t('Similar documents to %s', [$title])); ?>"><?php p($l->t('Similar documents')); ?></a>
```
(Englische Quellschlüssel sind Platzhalter; der Wortlaut kommt aus dem Wortlaut-Plan.)

## State of the Art

| Alt | Aktuell | Wann | Folge |
|-----|---------|------|-------|
| multilingual-e5-small (XLM-R, 2023), Mittelwert-Pooling, Präfixe | granite-embedding-97m-multilingual-r2 (ModernBERT, 2026-04), CLS, ohne Präfixe, 32k Kontext | 29.04.2026 | v1.6-Kandidat; Herstellerzahl +9,4 Punkte MTEB ML Retrieval, eigene Messung nötig |
| sqlite-vec KNN nur mit Anfrage aus dem Modell | gespeicherter Vektor als Anfrage, `rowid IN (...)` im KNN funktioniert in 0.1.9 | lokal belegt | "Mehr davon" ohne Modell |

## Assumptions Log

| # | Annahme | Abschnitt | Risiko wenn falsch |
|---|---------|-----------|--------------------|
| A1 | Mittelwert der 2 bis 3 Chunk-Vektoren ist als Anfrage gut genug | STR-01 Muster 1 | schlechtere Nachbarn; Wave-0-Distanzlauf vergleicht Mittelwert gegen Minimum je Chunk |
| A2 | `quantize_dynamic` QInt8 läuft auf dem ModernBERT-Graphen durch und quantisiert auch die Gather-Tabelle (Ergebnis um 97,5 MB) | STR-02 Schritt 2 | Datei rund 300 MB oder Fehler; dann Befund statt Zahl, IBM-Datei als Vergleich |
| A3 | Das ONNX von IBM nimmt nur `input_ids` und `attention_mask` | STR-02 | Messskript muss Eingaben aus der Session lesen (bench tut das schon) |
| A4 | Eine nackte m7g.large ohne Nextcloud reicht für Latenz, RAM, Durchsatz | STR-02 Schritt 6 | Owner wünscht vollen Wiederaufbau, dann Deckel deutlich höher |
| A5 | Ersparnis rund 81 Prozent beim Melder mit Weg B | STR-03 | nur Hochrechnung aus Issue-Zahlen |
| A6 | SMB listet Dateien, die der Nutzer nicht lesen darf, ohne aktivierte ACL-Prüfung | STR-03 Weg A | wenn falsch, wird Weg A sicherer; im Text als Prüfpunkt für v1.6 |
| A7 | Ein Ähnlich-Ceiling lässt sich auf testdata/corpus und testdata/semantik sinnvoll ableiten (kleine Mengen) | Pitfall 3 | Schwelle zu weich/hart; Rückfall: 86,5 mit Vermerk, Owner-Frage |

## Open Questions (RESOLVED)

1. **Deutsches Testset 42 Fälle reicht für ein Verdikt?**
   - Bekannt: 2026-09-05 zeigte bei 42 Fällen t-Werte unter 1 für kleine Effekte; Französisch brauchte 120.
   - Unklar: ob der Owner vor der Messung `de.jsonl` auf 120 erweitern will (D-35-07 erlaubt es, wenn VOR der Messung; D-35-06 will Vergleichbarkeit, die ersten 42 bleiben unverändert).
   - Empfehlung: im Wortlaut-/Messvorbereitungs-Checkpoint als Frage stellen; Standard: 42 plus Vorzeichentest, Grenze offen benennen.
   - RESOLVED: D-35-10 (Owner 19.10.): das deutsche Set wächst vor der Messung auf rund 120 Paare, die ersten 42 bleiben unverändert, e5-small wird im selben Lauf neu gemessen (Umsetzung 35-03).
2. **amd64-Latenz auf dem Entwicklungsrechner oder auf einer Box?**
   - Empfehlung: Entwicklungsrechner mit gepinnten Kernen, wie Welle 0; nur bei RAM-Druck eine kleine x86-Box.
   - RESOLVED: D-35-11 (Owner 19.10.): amd64 auf dem Entwicklungsrechner, strikt seriell, Browser zu; nur arm64 auf der gemieteten m7g (Umsetzung 35-09, 35-10).
3. **Zustand "Quelle hat keine Vektoren" eigener Satz oder gleich "keine Nachbarn"?**
   - Empfehlung: gleicher Leerzustand mit erklärendem Satz (Datei noch nicht semantisch erfasst oder ohne Text); Wortlaut-Plan.
   - RESOLVED: PE-35-3 (35-01-PLAN.md): ein Leerzustand "keine ähnlichen Dokumente" mit erklärendem Satz, getrennt vom einen Zustand "Datei nicht verfügbar"; Wortlaut final im Owner-Checkpoint 35-01 (Frage O4).
4. **Ähnlich-Link auch bei Treffern der Namenssuche und bei Bildern ohne Text?**
   - Empfehlung: immer zeigen, der Leerzustand trägt; kein Vorab-Wissen über Vektoren auf der Seite (sonst neue Feldart im Kandidaten).
   - RESOLVED: PE-35-2 (35-01-PLAN.md): Link an jedem Treffer, auch Namenstreffer und Bilder, ohne Vorwissen über Vektoren; Wortlaut final im Owner-Checkpoint 35-01 (Frage O1).

## Environment Availability

| Abhängigkeit | Benötigt von | Verfügbar | Version | Rückfall |
|--------------|-------------|-----------|---------|----------|
| backend .venv mit sqlite-vec | STR-01 Tests, Wave-0-Probe | ja | sqlite-vec 0.1.9 | , |
| uv + Gruppe quantize | int8-Build | ja (lock) | onnx 1.23.2 | , |
| Docker Desktop | Qualitäts- und amd64-Läufe | laut früheren Berichten ja, nicht neu geprüft | , | uv-Lauf ohne Container |
| PHP/PHPUnit | PHP-Tests | **nein** (lokal) | , | CI (php.yml) |
| gh CLI | Issue-Lesen | ja | , | , |
| AWS-Konto, aws_box.sh | arm64-Messung | Skript ja, Box nein (abgebaut 11.09.) | , | blockierender Owner-Checkpoint |
| Freier RAM lokal | Quantisierung, Läufe | unter 4 GB | , | seriell, ggf. Box |
| HuggingFace erreichbar | Artefakte | ja (API am 19.10. abgefragt) | Rev. 835ad140 | , |

**Fehlend ohne Rückfall:** arm64-Hardware bis zur Owner-Freigabe (D-35-05).

## Security Domain

| ASVS | Gilt | Kontrolle |
|------|------|-----------|
| V2 Authentication | nein (bestehende NC-Session) | , |
| V3 Session | ja, unverändert | Seite ohne CSRF-Token nur lesend (PageController-Kopf) |
| V4 Access Control | **ja, zentral** | Quelle und jeder Nachbar über `readableFile`; Container-Vorfilter nur Beschleunigung; `/similar` nicht in info.xml |
| V5 Input Validation | ja | `similar` nur Ziffern, still verworfen; `SimilarRequest` `extra="forbid"`, `fileId ge=1`, `limit` 1 bis `SEARCH_LIMIT_MAX` |
| V7 Logging | ja | keine fileid, kein Pfad, kein Titel im Log (Muster api/search.py:342) |
| V12 Files | nein | , |

| Muster | STRIDE | Gegenmittel |
|--------|--------|-------------|
| Existenz-Orakel über fremde fileid | Information Disclosure | Quelle zuerst rechecken, ein Zustand für alle Fehlschläge |
| Verdrängungs-/Zählsignal | Information Disclosure | großes k, Vorfilter vor Fenster, keine Zahl auf der Seite |
| Identität im Body | Spoofing | Nutzer nur aus signiertem Header, `extra="forbid"` |
| Lastverstärkung über viele `similar`-Aufrufe | DoS | ein Scan je Aufruf, Zeitdecke 1,5 s, Seitenbudget 3,0 s; gleiche Größenordnung wie eine Suche |
| Dedup Weg A: Auszug aus fremder Lesung | Information Disclosure | in der Notiz als Hauptrisiko, Weg B als ACL-sicherer Standard |

## Empfohlene Planfolge (für den Planner)

1. **35-01 Wortlaut** (wie 34-01): Linktext, aria-Label, Kopf "Ähnlich zu: %s", Rückweg, Leerzustände (keine Nachbarn, Datei nicht verfügbar), ggf. Seitentitel; de/en/fr zur Abnahme; Checkpoint. Optional die Messfrage aus Open Question 1 mitstellen.
2. **35-02 Container** (`vectors_of`, `centroid`, `similar_candidates`, `/similar`, Gates `KNOWN_ROUTES`, `CONTENT_ROUTES`, Paket-Baumhash 80) plus Wave-0-Distanzlauf für `SIMILAR_CEILING` (eigenes Messverzeichnis, Regel vor der Messung).
3. **35-03 PHP und Seite** (ExAppService, SearchService::similar, PageController, Template, CSS, 16 Kataloge, 5 Tabellen, Schlüsselzahl 341 + n, PHP-Baumhash, PHPUnit in CI), abhängig von 35-01 und 35-02.
4. **35-04 granite lokal** (Artefakte, int8-Build, `--pooling`-Schalter, Qualität, amd64-Latenz, Image-Zuwachs).
5. **35-05 granite arm64** (blockierender Checkpoint Box-Freigabe und Deckel; Latenz, RAM, Durchsatz, Hochrechnung; Abbau).
6. **35-06 Bericht und Empfehlung** inkl. Opt-in-Bewertung.
7. **35-07 Dedup-Notiz** (unabhängig, kann parallel zu allem).
8. **35-08 Gemeinsame Playwright-Abnahme** auf 8090 (Host-Backend braucht den neuen Stand).
9. **35-09 Audit** (Security/Bugs/Performance).

## Sources

### Primary (HIGH)
- Repo `a88de31f`: `backend/src/findling/store/vectors.py`, `vectors.sql`, `index/search.py`, `index/fusion.py`, `api/search.py`, `embed/model.py`, `embed/bench.py`, `embed/model_probe.py`; `php/lib/Service/SearchService.php`, `ExAppService.php`, `Controller/PageController.php`, `templates/search.php`, `js/search.js`; `backend/appinfo/info.xml`; Tests `test_php_acl_boundary.py`, `test_semantic_boundary.py`, `test_search_library.py`, `test_info_xml_defaults.py`, `test_measurement_scripts.py`, `test_admin_ui_contract.py`; `scripts/dev/quantize_model.py`, `model_quality.py`, `build_load_corpus.py`; `docs/measurements/2026-09-05-modellqualitaet`, `2026-09-06-vektordistanzen`, `2026-09-vergleichsmessung-m7g`, `docs/runbook-messbox.md`, `docs/admin-page.md`
- Lokale Probe 19.10.2026: sqlite-vec 0.1.9, int8-Rücklesen als BLOB, KNN mit gespeichertem Vektor, `rowid IN` im KNN
- HF-API und Dateien der Revision `835ad14087e140460703cf0fae09f97d469d65c2`: config.json, 1_Pooling/config.json, modules.json, config_sentence_transformers.json, tokenizer_config.json, Dateigrößen und sha256
- nextcloud/server stable34: `apps/files_external/lib/Lib/Storage/SMB.php` (getId), `apps/files_external/lib/Config/ConfigAdapter.php` (prepareStorageConfig)
- GitHub Issue street1983nk/nextcloud-search#25 mit Kommentaren (gh, 19.10.2026)

### Secondary (MEDIUM)
- [granite Modellkarte](https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2), Herstellerzahlen MTEB
- [Nextcloud Admin Manual, Authentication mechanisms](https://docs.nextcloud.com/server/latest/admin_manual/configuration_files/external_storage/auth_mechanisms.html)

### Tertiary (LOW)
- [help.nextcloud.com, External Storage Permissions](https://help.nextcloud.com/t/external-storage-permissions/9853) (SMB-Server entscheidet die Rechte je Anmeldung)

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH, keine neuen Pakete, Versionen aus uv.lock, granite-Fakten aus der API
- Architektur STR-01: HIGH für Pfade und Gates, MEDIUM für die Schwelle (Messung nötig)
- Architektur STR-02: HIGH für Werkzeuge und Fallen, MEDIUM für Quantisierungsergebnis und Laufzeiten
- STR-03: HIGH für NC-Fakten und Issue-Zahlen, MEDIUM für das SMB-Lese-/Listungsverhalten
- Pitfalls: HIGH, überwiegend aus Gate-Quelltext und früheren Messberichten

**Research date:** 2026-10-19
**Valid until:** 2026-11-18 (granite-Repo kann neue Revisionen bekommen; Revision ist festgenagelt)
