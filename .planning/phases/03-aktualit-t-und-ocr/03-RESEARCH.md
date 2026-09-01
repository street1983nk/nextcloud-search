# Phase 3: Aktualität und OCR - Research

**Researched:** 2026-09-01
**Domain:** Nextcloud-Ereignisse und Hintergrundjobs (PHP), Index-Konsistenzabgleich, OCR-Pipeline (pypdfium2-Rendering plus Tesseract-Subprozess) im gehärteten Sandbox-Kind
**Confidence:** HIGH für Code-Befunde und Nextcloud-APIs, MEDIUM-HIGH für OCR-Betriebsgrenzen (Zahlen brauchen einen Messlauf)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Aktualitäts-Kadenz**
- **D-01:** Ziel-Latenz für neue/geänderte/umbenannte Dateien: unter 1 Minute. Weg: PHP-Event-Listener -> enqueue in die bestehende Queue -> Poller mit bestehender Kadenz (Cooldown 15-120 s). KEIN neuer Push-/Weckkanal.
- **D-02:** ETag-Abgleich läuft nächtlich einmal voll (außerhalb der Nutzungszeit), Events tragen die Aktualität tagsüber. Abnahmetest wörtlich aus der Roadmap: Events blockiert, EIN Abgleichzyklus, Index korrekt.
- **D-03:** Der Abgleich setzt aus, solange Erstindex/OCR-Rückstau läuft (Queue über Schwelle), und startet erst bei ruhiger Queue. Schwellwert ist Claude-Diskretion.
- **D-04:** Rechteänderungen (Unshare, Delete) haben Vorrang vor Inhaltsänderungen in der Queue: ACL-Updates sind billig (kein Download, keine Extraktion) und ihre Sicherheitswirkung soll sichtbar schnell sein, auch bei langem OCR-Rückstau. (Der PHP-Recheck schützt ohnehin sofort; es geht um Kandidaten/Snippets im Container.)

**OCR-Umfang und Reihenfolge**
- **D-05:** OCR erfasst PDFs ohne Textlayer PLUS gängige Bildformate: JPG, PNG, TIFF, WebP. Kein HEIC/BMP/GIF (Decoder-Angriffsfläche im Sandbox-Kind, wenig Nutzen). Plausibilitäts-Deckel, damit nicht jedes Urlaubsfoto durch tesseract läuft (z.B. Mindestauflösung/Seitenverhältnis-Heuristik; Details Claude-Diskretion).
- **D-06:** Text-Layer-Erkennung (OCR-02): Dokumente mit vorhandenem Textlayer werden extrahiert, NIE erneut OCR-t. Das bestehende Verdikt `skipped(no_text_layer)` aus Phase 2 ist der vorbereitete Übergabepunkt.
- **D-07:** Erstindex in zwei Spuren: alle Textdokumente zuerst (Suche nach Stunden nutzbar), OCR-Jobs als zweite, nachlaufende Spur. Ein PDF ohne Textlayer wird automatisch zum OCR-Job statt endgültig skipped.

**OCR-Deckel und Verdikte**
- **D-08:** Limit gerissen (Seiten, Zeit, RAM) -> TEILINDEXIEREN als `indexed(truncated)` statt überspringen: die ersten N Seiten werden auffindbar, die Phase-4-Diagnose weist den Zustand aus. Muster existiert (RTF/Text-Cap aus Phase 2).
- **D-09 (Owner-Auftrag DACH-OCR, gesetzt):** Tesseract-Sprachen deu+eng; Schweizer Schreibweise (ss statt ß) und österreichische Varianten müssen im Zusammenspiel mit der deutschen Analyzer-Kette auffindbar sein; deu_frak (Fraktur) als OPTION, default AUS; DACH-Testkorpus (deutsche, teils gescannte Ratsvorlagen-PDFs) als Abnahmegrundlage.

**Lösch-Verhalten**
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

### Deferred Ideas (OUT OF SCOPE)

- Statusseite/Diagnose-UI inkl. OCR-Fortschritt und Vorab-Schätzung: Phase 4 (die Verdikt-Daten entstehen JETZT)
- Embeddings/Hybrid-Ranking: Phase 6
- Lasttest 100k+ und ARM-RSS-Kurve: Phase 5
- Mail-Anhänge/externe Quellen: nach v1
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Beschreibung | Wodurch die Recherche das trägt |
|----|--------------|---------------------------------|
| COMP-03 | PHP-App nimmt alle indexrelevanten Ereignisse auf (create/update/delete/move/rename, Share/Unshare) und stellt sie in die Pull-Queue; ein einziger Weg | Muster 1 (Listener über `registerEventListener` auf die typisierten `OCP\Files\Events\Node\*`- und `OCP\Share\Events\*`-Klassen, verifizierte Klassenliste), Muster 2 (Job-Arten in der Queue), Pitfall 1 (Massenoperationen sind EIN Event über einem Teilbaum), Pitfall 2 (`is_unchanged` verschluckt Umbenennungen), Befund B4 (Ordner-Umbenennung braucht gar keinen Index-Schreibvorgang) |
| IDX-04 | Periodischer ETag-Abgleich garantiert Konsistenz ohne Events | Muster 3 (Abgleich als Container-Pull über eine neue Lese-Route, Lösch-Erkennung lokal), Pitfall 5 (`maintenance_window_start` ist per Default AUS, "nächtlich" ist nicht geschenkt), Code-Beispiel 3 |
| IDX-05 | Löschungen und Unshares räumen Inhalte und ACL-Einträge zeitnah | Muster 2 (`kind=delete` und `kind=acl` müssen `describe()` überleben), Pitfall 3 (heute fällt eine gelöschte Datei als `skipped(gone)` still aus der Queue und der Container erfährt nie davon), Pitfall 4 (leere `userIds` sind bei ACL-Jobs ein legitimes Ergebnis) |
| OCR-01 | OCR für gescannte PDFs und Bilder, automatisch, index-seitig | Muster 4 (Render-Pipeline pypdfium2 -> PGM/PNG -> tesseract auf stdin), Standard Stack (keine neuen PyPI-Pakete nötig, nur Debian-Sprachpakete), Pitfall 6 bis 9 |
| OCR-02 | Text-Layer-Erkennung, Seiten-Timeouts, RAM-Deckel pro Job | Befund B1 (`skipped(no_text_layer)` existiert bereits als Übergabepunkt), Muster 5 (Deckel-Kaskade: Seiten, Zeit je Seite, Gesamtdeadline im Kind, RLIMIT_AS), Pitfall 10 (RLIMIT_AS wird vom Enkel geerbt) |
</phase_requirements>

## Summary

Phase 3 ist zu ungefähr zwei Dritteln eine PHP- und Protokollphase und nur zu einem Drittel OCR. Der OCR-Teil ist technisch der am besten vorbereitete: das Sandbox-Kind aus Phase 2 hat bereits `setsid` plus `killpg` (genau für einen hängenden tesseract-Enkel gebaut), `RLIMIT_AS`, Recycling und die Verdikt-Grammatik samt `skipped(no_text_layer)` als Übergabepunkt. Es kommt kein einziges neues PyPI-Paket dazu: Pillow 12.3.0 liegt bereits als transitive Abhängigkeit von python-pptx im `uv.lock` und im Venv, pypdfium2 rastert Seiten mit derselben Bibliothek, die schon den Text zieht. Neu sind ausschließlich vier Debian-Pakete im Image (`tesseract-ocr`, `-deu`, `-eng`, optional `-frk`).

Der schwierige Teil ist die Aktualität. Drei Befunde aus der Codebasis verschieben den Zuschnitt deutlich gegenüber der naiven Erwartung. Erstens: die Queue-Zeile ist heute strikt "eine Datei, ein Inhaltsjob". Löschungen und Unshares passen da nicht hinein, weil `QueueService::describe()` eine verschwundene Datei nicht mehr auflösen kann, die Zeile still als `skipped(gone)` wegwirft und der Container von der Löschung nie erfährt. IDX-05 ist damit nicht "ein Event mehr", sondern eine Job-Art-Spalte in `findling_queue` plus je ein eigener Pfad in `describe()`, im Poller und im Store. Zweitens: der `is_unchanged`-Schnellpfad im Poller quittiert eine unveränderte Datei ohne jeden Index-Schreibvorgang. Eine umbenannte Datei hat identischen Inhaltshash, also würde ein naiv erneut eingereihter Rename genau nichts bewirken, und Erfolgskriterium 1 der Phase wäre still verletzt. Drittens, und das entschärft das Ganze wieder: `body_de` ist im Tantivy-Schema **stored**, und `FIELD_PATH` wird zwar geschrieben, aber von keiner Abfrage gelesen und im Provider nie angezeigt (Titel und Pfad kommen aus dem Nextcloud-Knoten). Daraus folgt, dass eine Ordner-Umbenennung überhaupt keinen Index-Schreibvorgang braucht und eine Datei-Umbenennung als reiner Metadaten-Job ohne Download und ohne Extraktion erledigt werden kann, indem der gespeicherte Text aus dem Index zurückgelesen und mit neuem Namen erneut geschrieben wird.

Für IDX-04 empfiehlt sich der Abgleich als **Container-Pull** über eine neue Lese-Route der PHP-App statt als PHP-Aufruf in die ExApp: die Lösch-Erkennung ("im Zustand, aber nicht mehr in der Nextcloud-Liste") ist nur dort billig, wo beide Listen liegen, und `findling_file_state` kennt gar keine `indexed`-Zeilen, weil Phase 2 nur Fehlzustände dorthin schreibt. Ein einziger neuer Schreibpfad (Requeue) deckt danach sowohl den Abgleich als auch die OCR-Zweitspur aus D-07 ab. Zwei Betriebsfallen sind zu benennen: `maintenance_window_start` steht per Default auf 100 und ist damit **aus**, "nächtlich" ist auf einer Zero-Config-Instanz also nicht geschenkt; und `OMP_THREAD_LIMIT=1` ist auf einer Zweikern-Box laut Tesseract-FAQ nicht Feintuning, sondern der Unterschied zwischen brauchbar und unbenutzbar.

**Primary recommendation:** Eine Job-Art-Spalte (`kind`) in `findling_queue` als tragende Struktur einführen (`content`, `metadata`, `acl`, `delete`, `ocr`), den Claim danach in fester Reihenfolge bedienen (acl -> delete -> metadata -> content -> ocr, was D-04 und D-07 zugleich erfüllt), den ETag-Abgleich als Container-Pull über eine neue Lese-Route bauen, und OCR als vierten Dispatch-Zweig im bestehenden Sandbox-Kind mit `tesseract - - -l deu+eng` auf stdin ohne jede Zwischendatei.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Ereignisse aufnehmen (create/update/delete/move/rename) | PHP-Companion (Nextcloud-Prozess) | - | Nur der Nextcloud-Prozess sieht den Event-Dispatcher; die ExApp bekommt Ereignisse ausdrücklich nur unzuverlässig und asynchron (PITFALLS 5) |
| Share- und Unshare-Ereignisse aufnehmen | PHP-Companion | - | `OCP\Share\Events\*` existiert nur dort; Rechte bleiben grundsätzlich PHP-seitig (Out-of-Scope-Regel "kein zweites Rechtemodell in Python") |
| Teilbaum-Auflösung bei Ordner-Operationen | PHP-Companion (QueuedJob) | - | Nur PHP hat `IFileAccess::getByAncestorInStorage`; der Container kennt keine Nextcloud-Dateiliste |
| Arbeitsvorrat, Priorität, Idempotenz | PHP-Companion (`findling_queue`) | - | IDX-03 ist gesetzt: die Queue liegt in Nextcloud, der Container zieht. Eine zweite Queue im Container wäre die zweite Wahrheitsquelle, die das Projekt ausdrücklich vermeidet |
| Nächtliche Terminierung / Slicing | PHP-Companion (TimedJob/QueuedJob) | Container (Ruhe-Gate) | Cron gehört Nextcloud; ob es ruhig genug ist, weiß der Container am besten (eigener OCR-Rückstau) |
| ETag-Vergleich und Lösch-Erkennung | Container (state.db) | PHP (liefert Seiten der Dateiliste) | Die Menge "indexiert" liegt nur im Container; `findling_file_state` führt keine `indexed`-Zeilen |
| Textlayer-Erkennung | Container, Sandbox-Kind | - | Braucht pypdfium2 am geöffneten Dokument, existiert bereits |
| Rasterung und OCR | Container, Sandbox-Kind (tesseract als Enkel) | - | Nur dort gelten RLIMIT_AS, Deadline, setsid/killpg und die Nur-Lesen-Invariante |
| Index- und ACL-Räumung | Container (writer + store) | - | Der Container besitzt Tantivy-Index und ACL-Vorfilter |
| Finale Rechteentscheidung | PHP-Companion (Provider-Recheck) | - | Unverändert die einzige Sicherheitsgrenze (COMP-04) |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pypdfium2` | 5.13.0 (bereits gepinnt) | Seiten rastern (`page.render(scale=..., grayscale=True, draw_annots=False)`) | Dieselbe Bibliothek liefert schon den Textlayer; kein zweiter PDF-Stack, kein Ghostscript, keine AGPL-Falle [VERIFIED: Signatur und Parameter aus `backend/.venv/.../pypdfium2/_helpers/page.py` gelesen] |
| `pillow` | 12.3.0 (bereits im `uv.lock`, transitiv über python-pptx) | Bilddateien öffnen, Header prüfen, EXIF-Rotation, Skalierung, PNG-Kodierung | Steht schon im Lock und im Venv; nur der direkte Pin in `pyproject.toml` fehlt [VERIFIED: `uv.lock` Zeile 404, `.venv/Lib/site-packages/PIL` vorhanden] |
| `tesseract-ocr` (Debian) | 5.5.0-1 (amd64), 5.5.0-1+b1 (arm64) in trixie | OCR-Engine als Subprozess des Sandbox-Kindes | Bereits Stack-Entscheidung; arm64-Paket verifiziert vorhanden [VERIFIED: packages.debian.org/trixie/tesseract-ocr und .../arm64/tesseract-ocr/download] |
| `tesseract-ocr-deu`, `tesseract-ocr-eng` | 1:4.1.0-2, `Architecture: all` | Sprachdaten deutsch und englisch | `Architecture: all`, also bitgleich auf amd64 und arm64; kein Laufzeit-Download, Zero-Config bleibt heil [VERIFIED: packages.debian.org/trixie] |
| `tesseract-ocr-osd` | 1:4.1.0-2 | Orientierungs- und Skripterkennung | Wird von `tesseract-ocr` empfohlen und für `--psm 1` gebraucht; klein, `Architecture: all` [VERIFIED: packages.debian.org/trixie] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tesseract-ocr-frk` | 1:4.1.0-2 | Fraktur-Modell, Sprachcode **`frk`** | Nur wenn die Fraktur-Option aus D-09 eingeschaltet wird. **Wichtig: das Paket `tesseract-ocr-deu-frak` existiert in trixie nicht** (Antwort: "No such package"); der aus tesseract 3 stammende Sprachcode `deu_frak` ist tot, in tesseract 4/5 heißt das Modell `frk`, in neueren tessdata-Ständen `deu_latf`. Debian liefert `frk`. [VERIFIED: packages.debian.org/trixie für alle vier Namen abgefragt] |
| `tesseract-ocr-script-frak` | 1:4.1.0-2 | Skript-Modell Fraktur (Alternative zu `frk`) | Nur als Rückfallebene, falls `frk` auf dem DACH-Korpus schlechter trifft |
| `fonts-dejavu-core` (Debian) | trixie | Deterministische Schrift für den Korpusbau | Nur im Bau-Schritt des Testkorpus, nicht im Laufzeitimage. Siehe Pitfall 12 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| tesseract als Subprozess | `pytesseract` | Reiner `subprocess`-Wrapper mit Zwischendatei auf Platte, keine Kontrolle über Deadline pro Seite, keine stdin-Nutzung. Für ein Kind, das ohnehin schon Prozesse und Limits verwaltet, purer Ballast. [ASSUMED] |
| tesseract als Subprozess | `tesserocr` (libtesseract-Bindings) | Schneller (kein Prozessstart je Seite), aber der OCR-Absturz nimmt dann das Sandbox-Kind mit statt nur den Enkel, und `killpg` verliert seinen Zweck. Widerspricht direkt der Härtung aus dem Phase-2-Audit. [ASSUMED] |
| pypdfium2-Rasterung | OCRmyPDF | Schreibt per Design ein neues PDF, eigene Parallelisierung, große Abhängigkeitskette. In STACK.md bereits verworfen, und Pitfall 3 der Projektrecherche ist genau diese Klasse. |
| Tesseract | RapidOCR 3.9.2 | Besser auf schief fotografierten Belegen, schlechter auf sauberen deutschen Scans. Als späterer Zusatzpfad für Bilddateien denkbar, nie als Ersatz. [CITED: .planning/research/STACK.md] |
| PNG-Kodierung via Pillow | PGM/PNM (P5) von Hand aus dem Graustufen-Puffer | Spart die PNG-Kodierung (bei 300 dpi A4 wenige zehn Millisekunden gegen mehrere Sekunden OCR, also irrelevant) und eine Pillow-Abhängigkeit im PDF-Zweig. Leptonica liest PNM. Als Messoptimierung dokumentieren, nicht als Startpunkt. |

**Installation:**

```bash
# Dockerfile, runtime-Stage, im Muster des wngerman-Blocks (Version pinnen, Lizenz mitnehmen)
apt-get install -y --no-install-recommends \
    tesseract-ocr=5.5.0-1 \
    tesseract-ocr-deu=1:4.1.0-2 \
    tesseract-ocr-eng=1:4.1.0-2 \
    tesseract-ocr-osd=1:4.1.0-2
# optional, nur wenn die Fraktur-Option gebaut wird:
#   tesseract-ocr-frk=1:4.1.0-2
```

Achtung beim Pinnen: `tesseract-ocr` ist architekturabhängig und trägt auf arm64 die Binary-NMU-Version `5.5.0-1+b1`. Ein harter `=5.5.0-1` bricht den arm64-Bau. Entweder ohne Version pinnen und stattdessen den Basis-Image-Digest als Anker nehmen (so wie der Rest des Images es bereits tut), oder je Architektur unterschiedlich pinnen. Die `Architecture: all`-Sprachpakete lassen sich dagegen gefahrlos hart pinnen. [VERIFIED: packages.debian.org/trixie/arm64/tesseract-ocr/download liefert `tesseract-ocr_5.5.0-1+b1_arm64.deb`]

Lizenzpflichten: tesseract ist Apache-2.0, die traineddata-Modelle ebenfalls Apache-2.0. Beides muss in `THIRD-PARTY.md` und, im Muster des `wngerman`-Blocks, als Lizenztext ins Image. [ASSUMED für die genaue Lizenzdatei-Lage im Debian-Paket, vor dem Bau gegen `/usr/share/doc/tesseract-ocr/copyright` prüfen]

**Version verification:**

```bash
# Python-Seite: nichts Neues zu prüfen, pillow steht bereits im Lock
grep -A2 'name = "pillow"' backend/uv.lock     # -> 12.3.0
# Debian-Seite:
curl -s https://packages.debian.org/trixie/tesseract-ocr | grep -o "Package: tesseract-ocr ([^)]*)"
```

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `pillow` 12.3.0 | PyPI | Projekt seit 2010, Release 2026-07-01 | sehr hoch (Top-20 PyPI) | github.com/python-pillow/Pillow | `[OK]` | Bereits transitiv im Lock, nur direkt pinnen |
| `tesseract-ocr` 5.5.0-1 | Debian trixie main | Paket seit vor 2010 | Debian-Archiv | github.com/tesseract-ocr/tesseract | n/a (kein PyPI/npm) | Genehmigt, über Debian-Archiv verifiziert |
| `tesseract-ocr-deu` / `-eng` / `-osd` / `-frk` 1:4.1.0-2 | Debian trixie main | seit bookworm unverändert | Debian-Archiv | github.com/tesseract-ocr/tessdata (via `tesseract-lang`) | n/a | Genehmigt, `Architecture: all` verifiziert |

**Packages removed due to slopcheck [SLOP] verdict:** keine
**Packages flagged as suspicious [SUS]:** keine

Belege: `slopcheck install pillow` meldet `[OK] pillow (pypi)`, `1 OK`. PyPI-JSON bestätigt Name, Version 12.3.0, Lizenz MIT-CMU, Source `github.com/python-pillow/Pillow` und ein `cp313 manylinux_2_28_aarch64`-Wheel. Die Debian-Pakete sind keine Registry-Pakete im Sinne des Slopsquatting-Risikos; sie wurden einzeln gegen packages.debian.org/trixie geprüft, inklusive der negativen Antwort für `tesseract-ocr-deu-frak` ("No such package").

**Netto neue PyPI-Abhängigkeiten dieser Phase: null.** Das ist der wichtigste Satz dieses Abschnitts.

## Architecture Patterns

### System Architecture Diagram

```
                       NEXTCLOUD-PROZESS (PHP-Companion)                                CONTAINER (ExApp)
                                                                          |
  Nutzeraktion                                                            |
  (Web, WebDAV,                                                           |
   Desktop, occ)                                                          |
        |                                                                 |
        v                                                                 |
  View/Node-API                                                           |
        |                                                                 |
        v                                                                 |
  HookConnector  --dispatch-->  OCP\Files\Events\Node\*                    |
                                OCP\Share\Events\*                         |
                                OCA\Files_Trashbin\Events\NodeRestoredEvent|
                                        |                                  |
                                        v                                  |
                            +---------------------------+                  |
                            |  IndexEventListener       |                  |
                            |  (ein Ereignisweg)        |                  |
                            +------------+--------------+                  |
                                         |                                 |
                    Datei? ------------->+                                 |
                    Ordner? --> SubtreeExpandJob (QueuedJob, Baender)      |
                                         |                                 |
                                         v                                 |
                            +---------------------------+                  |
                            |  QueueService::enqueue    |                  |
                            |  findling_queue           |                  |
                            |  + kind (NEU)             |                  |
                            +------+-------------+------+                  |
                                   ^             |                         |
                                   |             | claim(kind)             |
        StorageCrawlJob -----------+             | GET /queues/documents   |
        (Erstindex, Phase 2)       |             +------------------------>|  Poller
                                   |                                       |    |
        ReconcileFeedController ---+                                        |    | Reihenfolge:
        GET /files/slice (NEU, Lesen) <---------------------------------+   |    | acl -> delete
                                   |                                    |   |    | -> metadata
        POST /queues/documents/requeue (NEU, Schreiben) <------------+   |   |    | -> content -> ocr
                                                                     |   |   |    v
                                                                     |   |   |  +---------------------+
                                                                     |   |   |  | Dispatch nach kind  |
                                                                     |   |   |  +----+-----+-----+----+
                                                                     |   |   |       |     |     |
                                                     acl/delete: kein Download <-----+     |     |
                                                                     |   |   |             |     |
                                              metadata: Doc aus Index lesen <-------------+     |
                                                     (body_de ist stored)                       |
                                                                     |   |   |                  |
                                                                     |   |   |   content/ocr:   |
                                                                     |   |   |   GET /gateway   v
                                                                     |   |   |  +--------------------+
                                                                     |   |   |  | Scratch-Datei      |
                                                                     |   |   |  +---------+----------+
                                                                     |   |   |            |
                                                                     |   |   |            v
                                                                     |   |   |  +--------------------+
                                                                     |   |   |  | Sandbox-Kind       |
                                                                     |   |   |  | setsid, RLIMIT_AS  |
                                                                     |   |   |  +---------+----------+
                                                                     |   |   |            |
                                                                     |   |   |   PDF: pypdfium2 Text
                                                                     |   |   |     |
                                                                     |   |   |     +-- Textlayer da? --> indexed
                                                                     |   |   |     |
                                                                     |   |   |     +-- nein --> Requeue als ocr
                                                                     |   |   |
                                                                     |   |   |   OCR-Job:
                                                                     |   |   |     pypdfium2.render(grayscale)
                                                                     |   |   |       oder Pillow (Bilddatei)
                                                                     |   |   |            |
                                                                     |   |   |            v  Bytes auf stdin
                                                                     |   |   |     +--------------------+
                                                                     |   |   |     | tesseract (Enkel)  |
                                                                     |   |   |     | OMP_THREAD_LIMIT=1 |
                                                                     |   |   |     +---------+----------+
                                                                     |   |   |            | Text auf stdout
                                                                     |   |   |            v
                                                                     |   |   |     Verdikt je Seite,
                                                                     |   |   |     Gesamtdeadline -> truncated
                                                                     |   |   |            |
                                                                     |   |   |            v
                                                                     |   |   |  Writer (commit) -> Store
                                                                     |   |   |            |
        DELETE /queues/documents  <----------------------------------+---+---+------------+  ack
```

Der Rückweg vom Container in die Nextcloud-Datenbank besteht damit aus **drei** Schreibrouten statt zwei: `DELETE /queues/documents`, `POST /queues/documents/unlock` und neu `POST /queues/documents/requeue`. Jede weitere Route kostet einen Eintrag in `OCS_WRITE_ALLOWLIST` in `backend/tests/test_readonly_gate.py`, und zwar mit den drei dort geforderten Pflichten: benannte Bedrohung, Aussage über die erreichbaren Tabellen, Negativtest. Die Lese-Route `GET /files/slice` braucht keinen Allowlist-Eintrag, weil Gate A nur schreibende HTTP-Methoden bewertet.

### Recommended Project Structure

```
php/lib/
├── Listener/
│   ├── FileEventListener.php        # Node-Events -> QueueService, ein Weg
│   └── ShareEventListener.php       # Share/Unshare -> ACL-Jobs
├── BackgroundJobs/
│   ├── SubtreeExpandJob.php         # Ordner-Operation in Baendern aufloesen
│   └── ReconcileScheduleJob.php     # nur der naechtliche Takt, kein Vergleich
├── Controller/
│   ├── QueueController.php          # + requeue()
│   └── ReconcileController.php      # GET /files/slice, nur lesend
├── Db/QueueMapper.php               # + kind, + claimBatch(kind), + requeueAs()
├── Migration/Version001000Date2026MMDD000000.php
└── Service/QueueService.php         # describe() je Job-Art

backend/src/findling/
├── extract/
│   ├── ocr.py                       # NEU: tesseract-Aufruf, Deckel, Verdikte
│   ├── raster.py                    # NEU: pypdfium2- und Pillow-Rasterung
│   ├── dispatch.py                  # + Route.OCR, + Bild-Mimetypes
│   └── errors.py                    # + neue Reasons
├── index/writer.py                  # + drop_document(), + add_from_stored()
├── store/repo.py                    # + etag, + tombstone, + reconcile-Abfragen
└── worker/
    ├── poller.py                    # Dispatch nach Job-Art
    └── reconcile.py                 # NEU: Abgleichlauf gegen /files/slice
```

### Pattern 1: Ein Listener, typisierte Events, `registerEventListener` in `register()`

**Was:** Die Ereignisse werden nicht über den AppAPI-`events_listener` bezogen, sondern über den normalen Nextcloud-Event-Dispatcher in der PHP-App. `Application::register()` registriert die Listener; `boot()` ist dafür der falsche Ort (die vorhandene Klasse dokumentiert das bereits für den Search-Provider).

**Wann:** Immer. Der AppAPI-Weg ist laut Nextcloud-Doku ausdrücklich asynchron und "more like a notification system", deckt Shares gar nicht ab und wäre der zweite Ereignisweg, den COMP-03 verbietet.

**Verifizierte Klassenliste (Branch `stable32`):**

`OCP\Files\Events\Node\`: `NodeCreatedEvent`, `NodeWrittenEvent`, `NodeTouchedEvent`, `NodeDeletedEvent`, `NodeRenamedEvent`, `NodeCopiedEvent`, dazu die sechs `BeforeNode*Event`-Gegenstücke und `BeforeNodeReadEvent`. [VERIFIED: GitHub-API-Verzeichnislisting nextcloud/server@stable32 lib/public/Files/Events/Node]

`OCP\Share\Events\`: `ShareCreatedEvent`, `ShareDeletedEvent`, `ShareDeletedFromSelfEvent`, `ShareAcceptedEvent`, `BeforeShareCreatedEvent`, `BeforeShareDeletedEvent`, `VerifyMountPointEvent`. [VERIFIED: dito, lib/public/Share/Events]

`OCA\Files_Trashbin\Events\`: `MoveToTrashEvent`, `NodeRestoredEvent`, `BeforeNodeRestoredEvent`. [VERIFIED: dito, apps/files_trashbin/lib/Events]

**Warum das für alle Schreibwege trägt:** `OC\Files\Node\HookConnector` hängt an den alten `\OC\Files\Filesystem`-Signalen und übersetzt sie in genau diese typisierten Events. Da `View` diese Signale auf jedem Schreibpfad auslöst, erreichen WebDAV, Desktop-Client, Weboberfläche und `occ` denselben Listener. [VERIFIED: nextcloud/server@stable32 lib/private/Files/Node/HookConnector.php, Methoden `postWrite`, `postCreate`, `postDelete`, `postRename`]

**Signatur:** `IRegistrationContext::registerEventListener(string $event, string $listener, int $priority = 0)`, seit NC 20. Ein Listener für eine Event-Klasse, die es auf der Instanz nicht gibt (Trashbin deaktiviert), ist harmlos: der Dispatcher vergleicht Klassennamen als Zeichenketten. [VERIFIED: lib/public/AppFramework/Bootstrap/IRegistrationContext.php]

### Pattern 2: Job-Art als Spalte, Priorität als Claim-Reihenfolge

**Was:** `findling_queue` bekommt eine Spalte `kind`. Der Claim fragt je Art getrennt, in fester Reihenfolge.

| kind | Auslöser | Kosten im Container | Braucht Knoten? |
|------|----------|---------------------|-----------------|
| `acl` | Share/Unshare, Gruppenwechsel | `replace_acl`, kein Download | nein, nur `usersFor()` |
| `delete` | NodeDeleted, Reconcile-Fund | Doc aus Index, ACL vergessen, Tombstone | **nein, darf es auch nicht** |
| `metadata` | Rename/Move einer Datei | Doc aus Index lesen, mit neuem Namen erneut schreiben | ja |
| `content` | Create/Write, Erstindex, ETag-Abweichung | Download, Extraktion | ja |
| `ocr` | PDF ohne Textlayer, Bilddatei | Download, Rasterung, tesseract | ja |

**Warum eine Reihenfolge statt einer Prioritätszahl:** die vorhandene `claimBatch` ist ein bedingtes UPDATE über eine Kandidatenliste, die `findling_q_free (locked_at, id)` direkt beantwortet. Eine Prioritätsspalte in `ORDER BY` würde diesen Index entwerten und einen zweiten brauchen. Ein Filter `WHERE kind = ?` in Kandidatenabfrage und Claim ist billiger, macht D-04 zu einer expliziten Schleife im Poller und erlaubt zugleich unterschiedliche Batch-Größen je Art, was für OCR zwingend ist (siehe Pitfall 11).

**Zusammenführungsregel beim Konflikt (kritisch):** `enqueue` ist über den Unique-Index auf `file_id` idempotent, also treffen sich zwei Arten in einer Zeile. Die Regel muss "Aufwertung, nie Abwertung" sein, mit der Ordnung `acl < metadata < content` und `delete` als absorbierendem Element. `ocr` ist Sonderfall: eine Zeile, die schon `ocr` ist, darf von `content` **nicht** zurückgeworfen werden, sonst kreist ein textloses PDF ewig zwischen den beiden Arten. Empfehlung: `ocr` verhält sich wie `content` in der Ordnung, und nur `requeueAs()` (also der Container nach der Textlayer-Prüfung) darf `content -> ocr` schalten.

**Migration:** exakt im Muster von `Version001000Date20260901000000` (jede Änderung mit `hasColumn`/`hasIndex` geschützt, Klassenname zeichengleich mit dem Dateinamen, Datenumschrift in `postSchemaChange`). Bestehende Zeilen bekommen `kind = 'content'`.

### Pattern 3: ETag-Abgleich als Container-Pull

**Was:** Der Container fährt den Abgleich, die PHP-App liefert nur Seiten ihrer Dateiliste.

**Ablauf je Scheibe:**

1. Der Container prüft sein Ruhe-Gate (D-03): `queue.stats().scheduled` unter der Schwelle **und** kein OCR-Rückstau in der eigenen `files`-Tabelle. Sonst nichts tun.
2. `GET /ocs/v2.php/apps/findling/mounts` liefert die Mounts (`storage_id`, `root_id`, `overridden_root`) aus `StorageService::getMounts()`.
3. `GET /ocs/v2.php/apps/findling/files?storage=&root=&after=&limit=` liefert eine nach `file_id` aufsteigende Seite aus `StorageService::getFilesInMount()` mit `{fileId, etag, size, mtime, mime}` und einem `final`-Kennzeichen, wenn weniger als `limit` Zeilen kamen.
4. Der Container vergleicht gegen `files`:
   - `file_id` unbekannt oder `etag` abweichend -> in die Requeue-Liste
   - lokal vorhanden mit `storage_id = S` und `after < file_id <= letzte_id_der_seite` (bei `final` ohne obere Grenze), aber nicht in der Seite -> **gelöscht**, sofort lokal räumen (Doc aus dem Index, ACL vergessen, Tombstone)
5. `POST /ocs/v2.php/apps/findling/queues/documents/requeue` mit `{fileIds: [...], kind: "content"}`.
6. Cursor in `state.db` fortschreiben, nächste Scheibe.

**Warum nicht andersherum (PHP ruft die ExApp an):** drei Gründe, in aufsteigender Härte. Erstens kennt `findling_file_state` gar keine `indexed`-Zeilen; Phase 2 schreibt dort nur Fehl- und Übersprungzustände, also kann PHP allein "im Index, aber nicht mehr da" nicht bilden. Ein Nachrüsten wäre eine zweite Wahrheitsquelle über denselben Sachverhalt, was das Projekt an mehreren Stellen ausdrücklich ablehnt. Zweitens hat ein Hintergrundjob keinen Nutzer, `exAppRequest(..., ?string $userId = null, ...)` erlaubt das zwar, aber die ExApp müsste dafür eine Route mit `access_level` PUBLIC führen und die heutige Aussage "drei Routen, das ist die ganze erreichbare Oberfläche" fiele. Drittens braucht der OCR-Übergabepunkt aus D-07 den Requeue-Schreibpfad ohnehin; der Abgleich nutzt ihn dann mit, statt einen zweiten Mechanismus zu erfinden.

**Preis, der zu dokumentieren ist:** der Abgleich-Cursor liegt damit im Container und nicht in der Nextcloud-Datenbank, anders als der Crawl-Cursor (IDX-02). Das ist vertretbar, weil ein verlorener Abgleich-Cursor eine Wiederholung kostet und nie Arbeit: der Abgleich ist reine Reparatur und vollständig idempotent. Das gehört als Satz in die Modul-Dokumentation, sonst liest es sich später wie ein Versehen.

**Nachweis für den Abnahmetest (IDX-04 wörtlich):** Events blockieren lässt sich am billigsten durch Deregistrieren der Listener über eine Testvariable oder durch einen Integrationsschritt, der die Datei direkt über `occ files:scan` beziehungsweise am Listener vorbei anlegt. Danach genau ein Abgleichzyklus, danach Indexzustand prüfen. Der Schritt gehört in `.github/workflows/integration.yml` neben den bestehenden End-to-End-Job.

### Pattern 4: OCR im Sandbox-Kind, tesseract auf stdin

**Was:** Der OCR-Zweig ist ein weiterer `Route`-Fall in `dispatch._run_route`. Er rastert Seite für Seite und schickt jede Seite als kodiertes Bild auf `stdin` an `tesseract - - -l deu+eng`, liest den Text von `stdout`.

**Warum stdin und nicht eine Zwischendatei:** tesseract liest laut Handbuch von `stdin`, wenn die Eingabe `stdin` oder `-` ist, und schreibt nach `stdout`, wenn OUTPUTBASE `stdout` oder `-` ist. Das spart eine Datei mit Nutzerinhalt auf der Platte je Seite (Datenschutz und Volumen) und eine ganze Klasse Aufräumfehler auf dem Fehlerpfad. [VERIFIED: tesseract(1) Handbuch, tesseract-ocr/tesseract doc/tesseract.1.asc]

**Rasterung:** `page.render(scale=dpi/72, grayscale=True, draw_annots=False)` liefert eine `PdfBitmap` mit `mode == "L"`, einem Kanal, dazu `width`, `height`, `stride` und `buffer`. Wichtig: `stride` kann größer als `width` sein, die Zeilen sind also gepolstert und müssen beim Kodieren zeilenweise geschnitten werden. [VERIFIED: pypdfium2 5.13.0, `_helpers/page.py` und `_helpers/bitmap.py`, `internal/consts.py` mit `FPDFBitmap_Gray -> "L"`]

**Warum Graustufen:** ein Viertel des Speichers gegenüber BGRA. A4 bei 300 dpi ist 2480 x 3508 Pixel, also rund 8,7 MB in Graustufen gegen rund 35 MB in BGRA. Tesseract binarisiert intern mit Otsu, Farbe bringt ihm nichts. [CITED: tesseract-ocr.github.io/tessdoc/ImproveQuality.html zur internen Binarisierung; die Speicherarithmetik ist Rechnung, kein Zitat]

**Warum 300 dpi:** "Tesseract works best on images which have a DPI of at least 300 dpi". [CITED: tesseract-ocr.github.io/tessdoc/ImproveQuality.html]

**Pflicht-Umgebungsvariable:** `OMP_THREAD_LIMIT=1`. Die Tesseract-FAQ sagt wörtlich, dass vier Threads auf einer Zweikern-Maschine "slow down things significantly", und dass ein Thread den Mehrprozess-Overhead beseitigt. Das Hardware-Ziel des Projekts ist genau diese Klasse. Zusätzlich `-c tessedit_do_invert=0`, das die FAQ ausdrücklich als "extra speed" nennt. [CITED: tesseract-ocr.github.io/tessdoc/FAQ.html]

**Aufrufform:**

```
tesseract - - -l deu+eng --oem 1 --psm 3 -c tessedit_do_invert=0
```

`--oem 1` (nur LSTM) explizit, weil die Debian-traineddata den Legacy-Motor nicht mitbringt und der Auto-Modus sonst eine Rückfallebene sucht, die es nicht gibt. [ASSUMED für die Debian-traineddata-Herkunft; per `tesseract --list-langs` und einem Testlauf im Bau-Image zu bestätigen]

### Pattern 5: Deckel-Kaskade statt einem Timeout

Vier Deckel greifen ineinander, und die Reihenfolge ist die Aussage:

| Ebene | Wert (Startvorschlag) | Wer erzwingt | Was passiert beim Reißen |
|-------|----------------------|--------------|--------------------------|
| Seiten je Dokument | 30 (OCR), gegen 500 im Textzweig | `ocr.py` | Schleife endet, `indexed(truncated)` |
| Zeit je Seite | 30 s | `subprocess.run(timeout=...)` | Seite wird verworfen, Schleife läuft weiter |
| Weiche Gesamtdeadline im Kind | 600 s | `time.monotonic()`-Prüfung in der Seitenschleife | Schleife endet, `indexed(truncated)` |
| Harte Deadline des Elternteils | 660 s (OCR-Job), 120 s (Textjob) | `pipe.poll(timeout)` plus `killpg` | `failed(timeout)`, Kind wird ersetzt |
| Adressraum | 512 MB (`RLIMIT_AS`) | Kernel, vom Enkel geerbt | `MemoryError` -> `failed(out_of_memory)` |

Der Kern von D-08 ist, dass die drei oberen Ebenen ein **teilindexiertes** Ergebnis liefern und nur die beiden unteren ein Scheitern. Die harte Deadline muss deshalb strikt über der weichen liegen, sonst tötet der Elternteil das Kind, bevor es seinen Teiltext abliefern konnte, und `indexed(truncated)` kommt in der Praxis nie vor.

`EXTRACT_TIMEOUT_SECONDS` ist heute ein einziger Wert in `config.py` und wird im `ExtractionWorker`-Konstruktor gebunden. Für zwei Deadlines braucht `_ask` einen Timeout je Job, nicht je Worker. Das ist eine kleine, aber echte Signaturänderung an einem gehärteten Modul.

### Anti-Patterns to Avoid

- **Eine Methode `delete`, `move`, `copy` oder `trash` irgendwo im Python-Paket.** Gate A (`backend/tests/test_readonly_gate.py`, `FORBIDDEN_IDENTIFIERS`) prüft diese Bezeichner in **jedem** Modul, nicht nur im Client. Der Löschpfad muss also `drop_document`, `forget`, `purge` oder ähnlich heißen. `delete_documents_by_query` ist unproblematisch, weil der Bezeichner nicht `delete` lautet.
- **Eine neue OCS-Schreibroute als Nebenwirkung eines Features.** `OCS_WRITE_ALLOWLIST` verlangt für jeden Eintrag eine benannte Bedrohung, eine Aussage über erreichbare Tabellen und einen Negativtest. Die Erweiterung gehört in einen eigenen Schritt und einen eigenen Commit, so wie Plan 02-10 es vorgemacht hat.
- **OCR über einen Bibliotheks-Binding statt über einen Subprozess.** Damit stirbt bei einem tesseract-Absturz das Sandbox-Kind statt des Enkels, und die in Phase 2 eigens gebaute `setsid`/`killpg`-Gruppenkill-Konstruktion wird sinnlos.
- **Den Rename über den normalen Inhaltsjob laufen lassen.** Siehe Pitfall 2: der `is_unchanged`-Schnellpfad quittiert ihn wirkungslos.
- **Löschungen über `describe()` laufen lassen.** Siehe Pitfall 3: die Zeile fällt als `skipped(gone)` heraus und der Container erfährt nie davon.
- **Bilder ungeprüft an tesseract geben.** Ohne Pillow-Deckel ist eine 40000 x 40000-PNG-Bombe ein `MemoryError` im Kind statt eines Verdikts.
- **`Image.MAX_IMAGE_PIXELS` auf `None` setzen.** Das ist der klassische Stack-Overflow-Rat und schaltet genau die Bombenprüfung ab, die hier gebraucht wird. Stattdessen den Wert bewusst auf das eigene Budget setzen.

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---------|--------------------|-------------|-------|
| Ereignisse aus Nextcloud beziehen | Eigenes Polling über den File-Cache oder eigene Hooks | `registerEventListener` auf `OCP\Files\Events\Node\*` | `HookConnector` deckt bereits alle Schreibwege ab, inklusive WebDAV und Desktop-Client |
| Teilbaum einer Ordner-Operation auflösen | Eigene rekursive Pfadabfrage | `IFileAccess::getByAncestorInStorage` (schon in `StorageService` gekapselt) | Liefert nach `file_id` sortiert, mit Mime-Filter in der Abfrage, und ist die einzige API, die das Projekt zulässt |
| Nächtlicher Takt | Eigener Scheduler, eigener Thread | `TimedJob` mit `setInterval` plus `setTimeSensitivity(IJob::TIME_INSENSITIVE)`, dazu ein eigenes 24-Stunden-Gate | NC entscheidet über `maintenance_window_start`; siehe aber Pitfall 5 |
| PDF-Seite rastern | Eigener Renderer, Ghostscript, pdftoppm | `pypdfium2` `page.render()` | Bereits gepinnte Abhängigkeit, dieselbe Engine wie im Textzweig |
| Bild öffnen, drehen, skalieren, Bombe abwehren | Eigener Header-Parser | Pillow: `Image.open` (lazy), `ImageOps.exif_transpose`, `Image.thumbnail`, `Image.MAX_IMAGE_PIXELS` | Pillow liest den Header, ohne zu dekodieren, und hat die Bombenprüfung eingebaut |
| Zeitdeckel um einen Subprozess | Eigener Wachthread, `signal.alarm` | `subprocess.run(timeout=...)` innerhalb des Kindes plus der bestehende `killpg` im Elternteil | Der Modul-Docstring von `sandbox.py` erklärt bereits, warum `signal.alarm` und `concurrent.futures` hier nicht funktionieren |
| Text aus dem Index zurücklesen | Eigenen Textcache neben dem Index | `Searcher.doc(DocAddress).to_dict()` auf `body_de` (stored) | Der Index ist die einzige gespeicherte Kopie des Textes im System, und sie ist zugreifbar |
| Idempotenz der Queue | Eigenes Select-vor-Insert | Vorhandenes `enqueue` mit `insertIgnoreConflict` und dirty-Semantik | Das Muster ist bereits gegen die PostgreSQL-Transaktionsfalle und gegen die Lost-Update-Rennen aus Bug-Audit H4 gehärtet |

**Key insight:** In dieser Phase liegt fast alles, was man bauen möchte, schon im Repository. Der Hebel liegt nicht im Erfinden, sondern im Erkennen: `skipped(no_text_layer)`, `etag`, `ocr_used` und `deleted_at` sind bereits vorhandene, leere Spalten und Verdikte, die Phase 2 ausdrücklich für Phase 3 angelegt hat, und `body_de` stored plus ein nirgends abgefragtes `FIELD_PATH` machen zwei der drei gefürchteten Umbenennungsfälle zu Nicht-Problemen.

## Runtime State Inventory

| Kategorie | Gefundene Posten | Erforderliche Aktion |
|-----------|------------------|----------------------|
| Gespeicherte Daten | `findling_queue` (neue Spalte `kind`, Altzeilen brauchen einen Default), `findling_file_state` (neue Reason-Codes, sonst unverändert), Container-`state.db` `files.etag`/`ocr_used`/`deleted_at` (Spalten existieren, sind leer), Tantivy-Index (Dokumente bleiben gültig) | Nextcloud-Migration im Muster `Version001000Date20260901000000`; **keine** `SCHEMA_VERSION`- oder `INDEX_VERSION`-Anhebung nötig, solange keine Tantivy-Feldänderung hinzukommt. Falls doch ein Feld nötig wird: das erzwingt einen vollständigen Reindex und muss als eigene Entscheidung geplant werden |
| Laufende Dienstkonfiguration | Keine externe Dienstkonfiguration außerhalb von git. Die App-Konfiguration liegt in `IAppConfig` (`SchedulerJob::LAST_JOB_RUN`) und in den ExApp-Umgebungsvariablen der `backend/appinfo/info.xml` | Neue OCR-Umgebungsvariablen (`FINDLING_OCR_*`) müssen sowohl in `config.py` als auch im `<environment-variables>`-Block der Backend-`info.xml` landen, sonst sieht der Admin sie nie |
| OS-registrierter Zustand | Nextcloud-Hintergrundjobs in `oc_jobs`: `SchedulerJob`, `StorageCrawlJob` mit Cursor im Argument. Ein neuer Abgleich-Job kommt hinzu | Registrierung über `AppInstallStep` beziehungsweise `IJobList`; beim Deinstallieren gehören die neuen Jobs in den Uninstall-Cleanup (PKG-04, Phase 5) |
| Secrets und Umgebungsvariablen | `APP_SECRET`, `HP_SHARED_KEY`, `NEXTCLOUD_URL`, `AA_VERSION` werden vom Sandbox-Kind abgeworfen (`_shed_secrets`) | Unverändert. **Aber:** der tesseract-Enkel erbt die Umgebung des Kindes. Nach dem Shedding ist dort nichts Sensibles mehr, das ist genau der Grund, warum das Shedding in Phase 2 vorgezogen wurde. Neu zu setzen ist `OMP_THREAD_LIMIT=1` und gegebenenfalls `TESSDATA_PREFIX` |
| Bau-Artefakte | Multi-Arch-Image (`backend/Dockerfile`, `.github/workflows/docker.yml`), Basis-Image per Digest gepinnt, `wngerman` per Version gepinnt | tesseract-Pakete kommen als vierter apt-Block dazu; der Digest-Pin des Basis-Image bleibt der Anker. Imagegröße steigt (traineddata deu+eng+osd sind zusammen im zweistelligen MB-Bereich), was für PKG-01/PKG-03 relevant ist und einmal gemessen werden sollte |

## Common Pitfalls

### Pitfall 1: Eine Ordner-Operation ist genau ein Event über tausend Dateien

**Was schiefgeht:** Ein Nutzer benennt einen Ordner mit 10000 Dateien um, verschiebt ihn oder löscht ihn. Es kommt **ein** `NodeRenamedEvent` beziehungsweise **ein** `NodeDeletedEvent` für den Ordnerknoten. Wer nur den Knoten aus dem Event einreiht, hat 9999 Dateien im falschen Zustand.

**Warum:** Der `HookConnector` übersetzt genau die Signale, die `View` auslöst, und `View::rename`/`View::rmdir` lösen sie für den Ordner aus, nicht rekursiv für die Kinder.

**Wie vermeiden, in drei Stufen:**
1. Für **Umbenennung/Verschiebung innerhalb desselben Mounts** ist gar nichts zu tun, siehe Pitfall 2 und der Befund zu `FIELD_PATH`. Die Kinder behalten Namen und Inhalt; nur `files.path` im Container veraltet, und dieses Feld wird von keiner Abfrage gelesen. Ein billiges Präfix-`UPDATE` in SQLite reicht, wenn man es überhaupt will.
2. Für **Verschiebung über eine Mount-Grenze** (etwa in einen Team Folder) ändern sich Berechtigungen. Hier ist ein `SubtreeExpandJob` (QueuedJob im Muster von `StorageCrawlJob`, Bänder von 250, Zeitdeckel 30 s, plant seinen Nachfolger selbst) nötig, der `kind=acl`-Jobs einreiht.
3. Für **Löschung** gilt: der Papierkorb bewahrt die `fileid` und die Cache-Einträge, nur unter einem anderen Elternknoten derselben Storage. `getByAncestorInStorage(storageId, ordnerFileId, ...)` findet die Nachkommen also auch nach dem Löschen noch. Bei deaktiviertem Papierkorb oder geleertem Papierkorb sind sie wirklich weg, und dann trägt der ETag-Abgleich das Ergebnis nach. Genau dafür ist er da.

**Warnzeichen:** Ein Integrationstest, der nur einzelne Dateien umbenennt und verschiebt, ist grün und beweist nichts.

### Pitfall 2: Der `is_unchanged`-Schnellpfad verschluckt jede Umbenennung

**Was schiefgeht:** `Poller._handle` fragt nach dem Download `store.is_unchanged(file_id, content_hash)` und quittiert bei `True` sofort, ohne `writer.add` und ohne `store.record`. Eine umbenannte Datei hat exakt denselben Inhaltshash. Ein Rename, der als gewöhnlicher `content`-Job eingereiht wird, bewirkt daher **nichts**: weder `name` noch `title` im Index noch `path`/`title` im Zustandsspeicher werden aktualisiert. Erfolgskriterium 1 der Phase wäre still verletzt.

**Warum:** `is_unchanged` prüft `content_hash`, `state = 'indexed'`, `index_version` und `deleted_at IS NULL`, aber keine Metadaten. Das war in Phase 2 richtig, weil dort Metadaten nur mit Inhalt zusammen ankamen.

**Wie vermeiden:** eigener Job `kind=metadata`, der gar nicht erst herunterlädt. Er liest das gespeicherte Dokument aus dem Index (`body_de` ist `stored`), baut einen `IndexRecord` mit neuem `name`, `title`, `path`, `ext`, `mtime` und demselben Text, und ruft `writer.add`, das ohnehin per Term-Löschung ersetzt. Danach `store.record` mit den neuen Metadaten und unverändertem Verdikt. Kein Gateway-Aufruf, keine Extraktion, kein Sandbox-Kind.

**Warnzeichen:** Ein Test, der nach einer Umbenennung nach dem **Inhalt** sucht, ist grün. Es muss nach dem **neuen Dateinamen** gesucht werden, denn `FIELD_NAME` trägt Boost 3.0 und ist das Feld, das sich ändert.

### Pitfall 3: Eine gelöschte Datei fällt heute still aus der Queue

**Was schiefgeht:** `QueueService::claim()` ruft `describe()`, und `describe()` gibt `null` zurück, sobald `usersFor()` leer ist oder `getFirstNodeById()` nichts findet. Die Zeile wird dann als `skipped(gone)` quittiert und gelöscht. Der Container bekommt sie nie zu sehen. Für eine gelöschte Datei heißt das: sie bleibt für immer im Tantivy-Index und in der ACL-Tabelle. Das ist exakt der Zustand, den IDX-05 verbietet, und die Codebasis produziert ihn heute zuverlässig.

**Warum:** Der Pfad wurde für den Erstindex gebaut, wo "die Datei ist weg" tatsächlich bedeutet "es gibt nichts zu tun".

**Wie vermeiden:** `describe()` verzweigt nach `kind`. Für `kind = delete` wird kein Knoten aufgelöst, keine Nutzerliste gebildet, kein Mount gebraucht; das Quellobjekt ist `{fileId, kind: "delete"}` und sonst nichts. Auch `nc/queue.py::_job()` muss das durchlassen: die heutige Fassung verwirft Einträge ohne Nutzer.

**Warnzeichen:** Der Abnahmetest löscht eine Datei und sucht danach als **anderer** Nutzer. Nur so sieht man den Unterschied zwischen "der PHP-Recheck filtert es weg" (was ohnehin passiert) und "es ist wirklich aus dem Index raus".

### Pitfall 4: Eine leere Nutzerliste ist beim Unshare das richtige Ergebnis

**Was schiefgeht:** Nach einem Unshare hat eine Datei möglicherweise keinen sichtbaren Nutzer mehr in der Menge, die der Vorfilter kennt. `usersFor()` liefert `[]`, `describe()` gibt `null`, die Zeile fällt als `skipped(gone)` heraus, und die alten ACL-Zeilen bleiben stehen. Der Vorfilter liefert dann weiterhin Kandidaten für einen Nutzer, der nichts mehr sehen darf.

**Warum:** Dieselbe `null`-Rückgabe bedeutet in `describe()` zwei verschiedene Dinge.

**Wie vermeiden:** Für `kind = acl` ist eine leere `userIds`-Liste eine legitime Nutzlast, kein Fehler. Der Container ruft dann `replace_acl(file_id, [])`, was alle Zeilen dieser Datei löscht. Zusätzlich darf ein ACL-Job **nicht** über `store.record()` laufen, denn das würde `attempts` hochzählen und das Verdikt überschreiben.

**Sicherheitseinordnung, damit die Dringlichkeit stimmt:** Es entsteht kein Leck. Snippets werden erst nach bestandenem Recheck gerendert, und der Recheck löst über `getFirstNodeById()` auf. Ein veralteter Vorfilter kostet Trefferqualität und Rechenzeit, nicht Vertraulichkeit. Genau so steht es auch in D-04. Diese Einordnung gehört in den Code-Kommentar, sonst wird sie später zur Panik oder zur Nachlässigkeit.

### Pitfall 5: "Nächtlich" ist auf einer Zero-Config-Instanz nicht geschenkt

**Was schiefgeht:** Man markiert den Abgleichjob als `TIME_INSENSITIVE` und glaubt, Nextcloud führe ihn nur im Wartungsfenster aus. Auf einer frisch installierten Instanz läuft er stattdessen mittags.

**Warum:** `cron.php` liest `maintenance_window_start` mit dem Default **100**, und die Einschränkung greift nur bei `$startHour <= 23`. Ohne ausdrückliche Admin-Konfiguration gibt es also kein Wartungsfenster. [VERIFIED: nextcloud/server@stable32 cron.php, Zeilen 125 bis 145]

**Wie vermeiden, dreifach:**
1. Trotzdem `setTimeSensitivity(IJob::TIME_INSENSITIVE)` setzen, damit gut konfigurierte Instanzen den Nutzen haben.
2. Ein eigenes 24-Stunden-Gate über `IAppConfig` führen ("letzter vollständiger Zyklus"), sonst läuft der Abgleich bei jedem Cron-Durchlauf.
3. Vor allem: das Ruhe-Gate aus D-03 und die Scheiben-Disziplin des `StorageCrawlJob` (30 s Wanduhr, 5 s bis zum Nachfolger) so bauen, dass es auch mittags nicht stört. Ein Abgleich, der nur nachts erträglich ist, ist ein Abgleich, den ein Admin abschaltet.
4. In `docs/` und in der Store-Beschreibung erwähnen, dass `maintenance_window_start` die Last verschiebt. Das ist ein Hinweis, keine Pflichtkonfiguration, sonst bricht Zero-Config.

### Pitfall 6: Ein Urlaubsfoto ist von einem fotografierten Dokument nicht unterscheidbar

**Was schiefgeht:** D-05 will einen Plausibilitätsdeckel, damit nicht jedes Foto durch tesseract läuft. Es gibt keine Heuristik, die ein abfotografiertes Protokoll von einem Strandbild trennt, ohne beides zu lesen.

**Wie vermeiden, ehrlich:** Nicht so tun, als gäbe es sie. Was die Heuristik wirklich leisten kann, ist das Aussortieren dessen, was ganz sicher kein Dokument ist, plus das Deckeln der Kosten:

| Regel | Startwert | Wirkung |
|-------|-----------|---------|
| Mindest-Kantenlänge | lange Kante unter 640 px | Icons, Avatare, Thumbnails, Signaturbilder -> `skipped(image_not_ocrable)` |
| Seitenverhältnis | lange durch kurze Kante über 8 | Banner, Trennlinien, Panoramen -> gleiches Verdikt |
| Pixelobergrenze | über 50 Megapixel | `skipped(too_large)`, und `Image.MAX_IMAGE_PIXELS` auf denselben Wert, damit Pillow selbst abbricht statt zu dekodieren |
| Herunterskalieren | lange Kante über 3500 px -> `thumbnail()` | Ein Handyfoto mit 12 MP kostet dann so viel wie eine A4-Seite bei 300 dpi |
| Nachbedingung | unter 20 erkannte Zeichen | `skipped(empty_text)` mit `ocr_used = 1`, das Bild landet nicht im Index |

Die letzte Zeile ist die eigentliche Antwort auf D-05: das Foto darf tesseract kosten, aber es darf den Index nicht verschmutzen, und Phase 4 kann über `ocr_used` plus `empty_text` genau ausweisen, wie viel Zeit dafür draufging.

**Zusatz, der oft vergessen wird:** `ImageOps.exif_transpose()` vor allem anderen. Ein hochkant fotografiertes Dokument mit EXIF-Orientierung 6 kommt sonst um 90 Grad gedreht bei tesseract an, und das Ergebnis ist Zeichensalat. Mehrseitige TIFF (Faxarchive) brauchen zusätzlich `n_frames` und denselben Seitendeckel wie PDFs.

### Pitfall 7: Der Sprachcode `deu_frak` existiert nicht mehr

**Was schiefgeht:** D-09 nennt `deu_frak`. Ein `apt-get install tesseract-ocr-deu-frak` bricht den Bau ("No such package"), ein `-l deu+deu_frak` bricht den Lauf.

**Warum:** `deu_frak` ist der Sprachcode aus tesseract 3. Ab tesseract 4 heißt das Fraktur-Modell `frk`, in neueren tessdata-Ständen `deu_latf`. Debian trixie liefert über `tesseract-lang` 1:4.1.0-2 die Pakete `tesseract-ocr-frk` und `tesseract-ocr-script-frak`. [VERIFIED: packages.debian.org/trixie, alle vier Namen einzeln abgefragt]

**Wie vermeiden:** Die Option heißt nach außen weiter "Fraktur" (das ist die Nutzersprache), intern wird `frk` gesetzt. Die Umgebungsvariable sollte `FINDLING_OCR_LANGUAGES` mit Default `deu+eng` sein und gegen eine Allowlist der tatsächlich installierten Sprachen geprüft werden, sonst macht ein Tippfehler im Admin-Formular jede OCR unbrauchbar. Das Muster für "unbrauchbare Eingabe degradiert auf den Default mit einer Warnung" steht bereits in `config.py::_languages()`.

### Pitfall 8: Schweizer ss und österreichische Varianten, was wirklich funktioniert

**Was schiefgeht:** Man baut eine Sonderbehandlung für ß gegen ss und misst hinterher, dass sie nichts bewirkt hat, oder man verspricht, dass "Januar" auch "Jänner" findet.

**Was tatsächlich gilt (nachgelesen, nicht angenommen):**
- Die deutsche Analyzer-Kette hat **kein** `ascii_fold`. Der Snowball-Stemmer für Deutsch faltet Umlaute und das scharfe s selbst. Die Testtabelle in `docs/german-analyzer.md` führt "Strasse (with sharp s)" auf das Token `strass`. Damit landen "Straße" und "Strasse" auf demselben Term, und die Schweizer Schreibweise ist ohne jede Zusatzarbeit auffindbar. [VERIFIED: `docs/german-analyzer.md` und `backend/src/findling/index/analyzer.py`, Filterkette ohne `ascii_fold` im deutschen Zweig]
- Auf der Abfrageseite gibt es zusätzlich `UMLAUTS = (("ue","ü"),("oe","ö"),("ae","ä"),("ss","ß"))` in `query/rewrite.py`, also eine Variantenbildung für den ausgeschriebenen Umlaut. [VERIFIED: `backend/src/findling/query/rewrite.py`, Zeile 42]
- "Jänner" wird zu `janner` gestemmt und ist unter "Jänner" auffindbar. Ein Treffer auf "Jänner" bei einer Suche nach "Januar" ist **kein** Analyzer-Problem, sondern Synonymie, und die ist in v1 nicht gebaut.

**Wie vermeiden:** Der Abnahmetest für D-09 prüft, was auch gilt: ein Schweizer Dokument mit "Strasse" ist über "Straße" auffindbar und umgekehrt; ein österreichisches Dokument mit "Jänner" ist über "Jänner" auffindbar. Die Nichtabdeckung "Januar findet Jänner" gehört als bewusste, dokumentierte Grenze in `docs/german-analyzer.md`, im Muster der drei bereits dort stehenden Grenzen D2, D3 und "Compounds, die selbst in der Liste stehen".

**Der eigentliche DACH-Risikopunkt liegt woanders:** nicht in der Analyzer-Kette, sondern in der OCR-Qualität. Tesseract mit `deu` verwechselt bei schlechten Scans regelmäßig ß mit B, ü mit ii und die Ligaturen. Deshalb muss der Abnahmetest über **auffindbare Suchbegriffe** laufen, nicht über einen Vergleich des OCR-Rohtextes, genau wie es in CONTEXT.md unter "Specific Ideas" steht. Ein Rohtext-Diff wäre ein Test gegen die tesseract-Version und würde bei jedem Debian-Punktrelease rot.

### Pitfall 9: Die Textlayer-Schwelle ist heute eine ungemessene Annahme

**Was schiefgeht:** `_MIN_CHARS_PER_PAGE = 25` in `pdf.py` entscheidet, welche PDFs OCR bekommen. Der Kommentar dort sagt ausdrücklich, dass es eine Annahme (A2) ist, gemessen an genau zwei Korpusdateien (63 Zeichen gegen 0), und dass Phase 3 die Zahl an echten Dokumenten nachziehen soll.

**Warum das jetzt teuer wird:** Ab dieser Phase ist die Fehlklassifikation nicht mehr symmetrisch billig. Ein Text-PDF, das fälschlich in die OCR-Spur geht, kostet ab jetzt echte Minuten CPU je Dokument statt nichts.

**Wie vermeiden:** Die Schwelle einmal gegen den DACH-Korpus messen und die Zahl mit der Messung im Kommentar ersetzen. Zwei Verfeinerungen sind billig und lohnen sich: den Zeichenanteil je Seite statt über das Dokument bewerten (steht schon so im Code) und eine Datei nur dann als reines Scan-PDF werten, wenn ein ausreichender Anteil der geprüften Seiten unter der Schwelle liegt. Ein Vertragsdokument mit Textlayer und drei eingescannten Anhangseiten ist der Realfall, den beide Extreme falsch behandeln.

### Pitfall 10: `RLIMIT_AS` wird vom Enkel geerbt, und OpenMP reserviert Adressraum

**Was schiefgeht:** Das Sandbox-Kind setzt `RLIMIT_AS` auf 512 MB. Ein per `subprocess` gestarteter tesseract erbt dieses Limit als eigenes Prozesslimit. Reißt tesseract es, stirbt der Enkel, nicht das Kind, und das Kind sieht nur einen Exitcode ungleich null. Ein `MemoryError` im Kind kommt in dem Fall gar nicht vor, also greift die Recycling-Regel 3 nicht, und das Verdikt wäre ohne Sonderbehandlung ein nichtssagendes `failed(corrupt)`.

**Zweiter Teil:** `RLIMIT_AS` zählt virtuellen Adressraum, nicht residenten Speicher. OpenMP-Laufzeiten reservieren je Thread einen Stack und Arenen, glibc gibt freigegebene Arenen nicht zurück. `OMP_THREAD_LIMIT=1` reduziert das deutlich und ist damit doppelt begründet: Geschwindigkeit auf zwei Kernen **und** Adressraum.

**Wie vermeiden:**
- Exitcode und `stderr`-Länge auswerten und auf eigene Verdikte abbilden: Signal-Tod oder Exitcode ungleich null -> `failed(ocr_failed)`; `subprocess.TimeoutExpired` -> Seite verwerfen und weiter, bei allen Seiten -> `failed(timeout)`; ausführbare Datei nicht gefunden -> `failed(ocr_unavailable)`.
- `stderr` **nicht** in den Log schreiben. Tesseract schreibt dort Dateinamen und Warnungen mit Inhaltsbezug, und die Regel "der Log trägt Zähler und Reason-Codes, sonst nichts" (T-02-107) gilt hier genauso.
- Das 512-MB-Limit ist eine Annahme für tesseract und muss einmal gegen eine A4-Seite bei 300 dpi gemessen werden. Wenn es nicht reicht, ist die richtige Antwort ein eigener, höherer `RLIMIT_AS` für den OCR-Enkel über `preexec_fn` beziehungsweise ein separater Wert im Kind, nicht ein pauschales Anheben für alle Extraktionen.

### Pitfall 11: Ein OCR-Batch von 32 Dateien sprengt den Claim-Lock

**Was schiefgeht:** `BATCH_FILES = 32` und `QueueMapper::LOCK_TIMEOUT = 900`. Ein OCR-Job darf laut Deckel-Kaskade bis zu 600 s dauern. 32 davon sind über fünf Stunden, der Claim läuft nach 15 Minuten aus, die Zeilen erscheinen wieder als `scheduled`, `retries` wird beim nächsten Claim hochgezählt, und `MAX_ATTEMPTS = 3` beendet sie als `failed(repeatedly_stuck)`, obwohl gerade in Ordnung an ihnen gearbeitet wird.

**Warum das nicht auffällt:** Bei `INDEX_WORKERS = 1` gibt es keinen zweiten Abnehmer, der die abgelaufene Zeile wirklich wegnimmt. Der Schaden ist zunächst nur ein falscher Zähler auf der Statusseite und ein hochgezähltes `retries`, und beides sieht man erst, wenn die dritte Runde die Datei abschießt.

**Wie vermeiden (beides, nicht eines von beiden):**
- Batchgröße je Job-Art: `ocr` mit 1, höchstens 2 Dateien je Claim. Dann liegt ein Batch mit 600 s sicher unter 900 s.
- `LOCK_TIMEOUT` je Job-Art, mit einem höheren Wert für `ocr` (Vorschlag 1800 s). Der Docstring der Konstante sieht das ausdrücklich vor ("OCR in phase 3 raises this value or splits it per kind of job").
- Der `retries`-Zähler muss beim Requeue von `content` nach `ocr` zurückgesetzt werden, sonst startet die OCR-Spur mit einem verbrauchten Versuch.

**Warnzeichen:** `failed(repeatedly_stuck)` taucht ausgerechnet auf den großen Scans auf.

### Pitfall 12: Ein Testkorpus, der sich nicht reproduzierbar bauen lässt

**Was schiefgeht:** `scripts/dev/build_corpus.py` baut den heutigen Korpus mit reiner Standardbibliothek, ausdrücklich damit er nicht verrottet. Für OCR braucht man aber gerenderten Text in einem Bild, und den kann die Standardbibliothek nicht erzeugen. Wer schnell zu `ImageFont.load_default(size=40)` greift, bekommt Aileron Regular mit laut Pillow-Doku "a more limited character set" und eine Schrift, die sich mit der Pillow-Version ändern kann. Umlaute und ß sind genau das Risiko. [CITED: pillow.readthedocs.io ImageFont, `load_default(size)` seit 10.1.0]

**Wie vermeiden:** Die Schrift so pinnen, wie das Projekt bereits die Wortliste pinnt: `fonts-dejavu-core` in der pinnenden Version, Rendering im selben Basis-Image, Digest der erzeugten Datei notiert. Vor dem ersten Korpusbau einmal prüfen, dass "Straße Jänner Grundstücksverkehrsgenehmigung" ohne Ersatzkästchen gerendert wird. Der Korpus wird ohnehin als Binärdatei eingecheckt, also zahlt man den Aufwand einmal.

**Der Korpus muss nach dieser Phase enthalten:** ein mehrseitiges Scan-PDF mit deutscher Verwaltungsprosa, ein gemischtes PDF (Textlayer plus gescannter Anhang, für Pitfall 9), ein Schweizer Dokument mit "Strasse", ein österreichisches mit "Jänner", je eine JPG/PNG/TIFF/WebP-Datei, ein mehrseitiges TIFF, ein Bild unter der Plausibilitätsschwelle, ein absichtlich um 90 Grad EXIF-gedrehtes Foto und mindestens zehn defekte PDFs für Gate B. Die beiden vorhandenen kaputten Dateien (`06-zero-bytes.pdf`, `07-password-protected.pdf`) sind ein Anfang, nicht das Ziel.

### Pitfall 13: Gate B misst nur, was es angefasst hat

**Was schiefgeht:** Der Prüfsummenlauf in `.github/workflows/integration.yml` friert Dateiliste, Prüfsummen und Metadaten ein und vergleicht sie danach. Wenn der OCR-Lauf die neuen Korpusdateien gar nicht erreicht (weil der Mime-Typ auf der PHP-Seite nicht in `StorageService::ALLOWED_MIMETYPES` steht), ist Gate B grün und beweist nichts.

**Wie vermeiden:** Die Bild-Mimetypes müssen an **zwei** Stellen ergänzt werden, `php/lib/Service/StorageService.php::ALLOWED_MIMETYPES` und `backend/src/findling/extract/dispatch.py::ALLOWED_MIMETYPES`, und der Integrationsjob muss zusätzlich prüfen, dass die neuen Dateien tatsächlich ein Verdikt bekommen haben (Zähler ungleich null), bevor die Prüfsummen etwas aussagen. Die beiden Listen driften sonst auseinander, und `dispatch.py` sagt zu dieser Doppelung bereits ausdrücklich, dass sie "die Zeile ist, die an dem Tag noch hält, an dem jemand den Deckel nur auf einer Seite anhebt".

### Pitfall 14: Drei Orte für jeden neuen Reason-Code

**Was schiefgeht:** Ein neuer Reason wird in `extract/errors.py` ergänzt, der Container produziert ihn, `FileStateService::record()` verwirft ihn still (weil er nicht in `REASONS` steht), und die Datei bekommt am Ende gar kein Verdikt.

**Wie vermeiden:** Jeder neue Reason gehört in derselben Änderung an drei Stellen:
1. `backend/src/findling/extract/errors.py` (`Reason` und `STATE_REASONS`)
2. `backend/src/findling/store/repo.py` (`STATE_REASONS`, wortgleich)
3. `php/lib/Service/FileStateService.php` (`REASONS`)

Ein Test vergleicht die ersten beiden bereits. Für die dritte gibt es keinen automatischen Abgleich; das wäre ein billiges neues Gate (Python-Test, der die PHP-Konstante per Regex liest), und es liegt inhaltlich neben Sec-L4, das ohnehin in dieser Phase fällig ist.

**Vorschlag für die neuen Codes, bewusst sparsam:**

| Code | Zustand | Wofür |
|------|---------|-------|
| `image_not_ocrable` | skipped | Bild unter der Plausibilitätsschwelle (Pitfall 6) |
| `ocr_failed` | failed | tesseract mit Exitcode ungleich null oder per Signal beendet |
| `ocr_unavailable` | failed | tesseract oder die traineddata fehlen im Image |

Bewusst **nicht** neu: `empty_text` für "OCR lief, fand nichts", `timeout` für die harte Deadline, `out_of_memory` für `RLIMIT_AS`, `truncated` für jeden Teilindex nach D-08. Vier bestehende Codes decken die vier häufigsten OCR-Ausgänge ab, und jeder zusätzliche Code kostet Phase 4 eine deutsche Beschriftung.

## Code Examples

### Beispiel 1: Listener-Registrierung (PHP)

```php
// php/lib/AppInfo/Application.php, in register(), nicht in boot()
// Quelle: nextcloud/server@stable32 lib/public/AppFramework/Bootstrap/IRegistrationContext.php
public function register(IRegistrationContext $context): void {
    $context->registerSearchProvider(Provider::class);

    // Ein Listener fuer alle Node-Ereignisse. Die Unterscheidung passiert dort,
    // damit "ein einziger Ereignisweg" nicht nur eine Absicht ist, sondern eine
    // Stelle im Code, an der man sie nachzaehlen kann.
    foreach ([
        \OCP\Files\Events\Node\NodeCreatedEvent::class,
        \OCP\Files\Events\Node\NodeWrittenEvent::class,
        \OCP\Files\Events\Node\NodeTouchedEvent::class,
        \OCP\Files\Events\Node\NodeDeletedEvent::class,
        \OCP\Files\Events\Node\NodeRenamedEvent::class,
        \OCP\Files\Events\Node\NodeCopiedEvent::class,
    ] as $event) {
        $context->registerEventListener($event, FileEventListener::class);
    }

    // Der Wiederherstellungs-Event gehoert einer App. Ein Listener auf eine
    // Klasse, die es auf dieser Instanz nicht gibt, ist harmlos: der Dispatcher
    // vergleicht Zeichenketten.
    $context->registerEventListener(
        \OCA\Files_Trashbin\Events\NodeRestoredEvent::class,
        FileEventListener::class,
    );

    foreach ([
        \OCP\Share\Events\ShareCreatedEvent::class,
        \OCP\Share\Events\ShareDeletedEvent::class,
        \OCP\Share\Events\ShareDeletedFromSelfEvent::class,
    ] as $event) {
        $context->registerEventListener($event, ShareEventListener::class);
    }
}
```

### Beispiel 2: Metadaten-Job ohne Download (Python)

```python
# backend/src/findling/index/writer.py, neue Methode
# Quelle: tantivy 0.26.0 tantivy.pyi (Searcher.doc, Document.to_dict),
#         backend/src/findling/index/schema.py (body_de ist stored)
def stored_body(self, file_id: int) -> str | None:
    """Den gespeicherten Text eines Dokuments zurueckholen.

    Das ist der Grund, warum eine Umbenennung keinen Download braucht: body_de
    ist das einzige gespeicherte Textfeld des ganzen Systems, und es ist genau
    der Text, den der Snippet-Generator ohnehin daraus liest.
    """
    searcher = self._index.searcher()
    hits = searcher.search(
        Query.term_query(self._schema, FIELD_FILE_ID, file_id), limit=1
    ).hits
    if not hits:
        return None
    _score, address = hits[0]
    values = searcher.doc(address).to_dict().get(FIELD_BODY_DE, [])
    return str(values[0]) if values else None
```

### Beispiel 3: Lösch-Erkennung im Abgleich (Python, SQL)

```python
# backend/src/findling/store/repo.py
# Die obere Grenze ist der Grund, warum die Seite ein final-Kennzeichen braucht:
# ohne sie waere jede Datei hinter dem Seitenende faelschlich "geloescht".
_GONE_IN_RANGE_SQL: Final = """
SELECT file_id FROM files
 WHERE storage_id = ?
   AND file_id > ?
   AND (? = 1 OR file_id <= ?)
   AND deleted_at IS NULL
"""

def gone_in_range(
    self, storage_id: int, after: int, upto: int, final: bool, present: set[int]
) -> list[int]:
    rows = self._connection.execute(
        _GONE_IN_RANGE_SQL, (storage_id, after, 1 if final else 0, upto)
    ).fetchall()
    return [row[0] for row in rows if row[0] not in present]
```

### Beispiel 4: Eine Seite rastern und OCR-en (Python)

```python
# backend/src/findling/extract/ocr.py
# Quellen: pypdfium2 5.13.0 _helpers/page.py (render-Signatur, grayscale, draw_annots),
#          _helpers/bitmap.py und internal/consts.py (FPDFBitmap_Gray -> "L", stride),
#          tesseract(1) (stdin/stdout ueber "-"),
#          tesseract-ocr.github.io/tessdoc/FAQ.html (OMP_THREAD_LIMIT, tessedit_do_invert)
import os
import subprocess
from io import BytesIO

_SCALE_300_DPI = 300 / 72


def _page_to_png(document, number: int) -> bytes:
    page = document[number]
    try:
        bitmap = page.render(scale=_SCALE_300_DPI, grayscale=True, draw_annots=False)
        try:
            from PIL import Image

            # frombuffer statt frombytes waere hier falsch: die Zeilen sind auf
            # stride gepolstert, also wird zeilenweise geschnitten.
            raw = bytes(bitmap.buffer)
            rows = b"".join(
                raw[y * bitmap.stride : y * bitmap.stride + bitmap.width]
                for y in range(bitmap.height)
            )
            image = Image.frombytes("L", (bitmap.width, bitmap.height), rows)
            sink = BytesIO()
            image.save(sink, format="PNG", compress_level=1)
            return sink.getvalue()
        finally:
            bitmap.close()
    finally:
        page.close()


def _ocr_page(png: bytes, languages: str, seconds: float) -> str | None:
    """Der Text einer Seite, oder None wenn diese eine Seite nicht ging.

    stderr wird eingesammelt und weggeworfen, nie geloggt: tesseract schreibt
    dort Dateinamen und inhaltsnahe Warnungen, und der Log dieses Projekts
    traegt Zaehler und Reason-Codes, sonst nichts (T-02-107).
    """
    environment = {**os.environ, "OMP_THREAD_LIMIT": "1"}
    try:
        finished = subprocess.run(
            [
                "tesseract", "-", "-",
                "-l", languages,
                "--oem", "1",
                "--psm", "3",
                "-c", "tessedit_do_invert=0",
            ],
            input=png,
            capture_output=True,
            timeout=seconds,
            env=environment,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        raise
    if finished.returncode != 0:
        return None
    return finished.stdout.decode("utf-8", errors="replace")
```

### Beispiel 5: Nächtlicher Takt, der auch ohne Wartungsfenster erträglich ist (PHP)

```php
// php/lib/BackgroundJobs/ReconcileScheduleJob.php
// Quelle: nextcloud/server@stable32 lib/public/BackgroundJob/TimedJob.php,
//         cron.php (maintenance_window_start hat den Default 100, also aus)
class ReconcileScheduleJob extends TimedJob {
    public function __construct(ITimeFactory $time, /* ... */) {
        parent::__construct($time);
        $this->setInterval(3600);
        // Auf gut konfigurierten Instanzen schiebt das den Lauf ins
        // Wartungsfenster. Auf einer frisch installierten tut es nichts,
        // weil maintenance_window_start per Default 100 ist. Deshalb steht
        // die eigentliche Bremse unten und nicht hier.
        $this->setTimeSensitivity(IJob::TIME_INSENSITIVE);
    }
}
```

## State of the Art

| Alter Ansatz | Aktueller Ansatz | Wann geändert | Bedeutung hier |
|--------------|------------------|---------------|----------------|
| Legacy-Filesystem-Hooks (`\OC\Files\Filesystem::signal_post_*`) direkt abonnieren | Typisierte Events `OCP\Files\Events\Node\*`, gespeist vom `HookConnector` | Seit NC 20 der Weg, Legacy-Signale existieren nur noch als Innenleben | Der Listener abonniert die typisierten Klassen und bekommt trotzdem alle Schreibwege |
| `deu_frak` als Fraktur-Sprachcode | `frk` (tesseract 4/5, Debian), `deu_latf` in neueren tessdata | tesseract 4.0 (2018), tessdata-Umbenennung ~2021 | D-09 muss übersetzt werden, sonst bricht der Bau |
| OCR erzeugt ein durchsuchbares PDF | OCR erzeugt Text für einen Index, das Original wird nie angefasst | Projektentscheidung, gegen die dokumentierte Datenverlustklasse von `files_fulltextsearch_tesseract` | Kein Rückschreibpfad, Gate B beweist es von außen |
| `exAppRequestWithUserInit()` | `exAppRequest()` | Deprecated seit AppAPI 3.0.0 | Falls doch ein PHP-nach-Container-Aufruf gebaut wird |

**Veraltet oder überholt:**
- Der AppAPI-`events_listener` (`node_event` mit sechs Subtypen) als Aktualitätsmechanismus: deckt Shares nicht ab, ist laut Doku ausdrücklich unzuverlässig und wäre der zweite Ereignisweg, den COMP-03 ausschließt.
- `Image.MAX_IMAGE_PIXELS = None` als Antwort auf `DecompressionBombError`: schaltet genau die Prüfung ab, die hier gebraucht wird.

## Assumptions Log

| # | Behauptung | Abschnitt | Risiko, wenn falsch |
|---|------------|-----------|---------------------|
| A1 | Tesseract kommt mit 512 MB `RLIMIT_AS` für eine A4-Seite bei 300 dpi in Graustufen aus | Pattern 5, Pitfall 10 | Jeder OCR-Job scheitert am Adressraum. Muss vor der Umsetzung mit einem Messlauf im Bau-Image beantwortet werden, das ist die wichtigste offene Zahl der Phase |
| A2 | Die Deckel-Startwerte (30 Seiten, 30 s je Seite, 600 s weich) passen zu einer 4-GB-ARM-Box | Pattern 5 | Erstindex dauert unerträglich lange oder bricht zu früh ab. Messung gehört in diese Phase, die ARM-Kurve erst in Phase 5 |
| A3 | Debians tesseract-traineddata sind LSTM-Daten, `--oem 1` ist deshalb korrekt | Pattern 4 | `--oem 1` schlägt fehl oder liefert schlechtere Ergebnisse. Ein `tesseract --list-langs` und ein Testlauf im Bau-Image klären es in Minuten |
| A4 | Der Papierkorb erhält die Cache-Einträge der Nachkommen, sodass `getByAncestorInStorage` nach einem Ordner-Löschen noch enumeriert | Pitfall 1 | Ordner-Löschungen werden erst vom nächtlichen Abgleich erfasst statt sofort. Kein Sicherheitsproblem (der Recheck schützt), aber eine Abweichung von D-10, die dokumentiert werden müsste |
| A5 | Leptonica im Debian-tesseract liest WebP | Pattern 4, D-05 | WebP-Bilder scheitern. Umgehung wäre trivial: Pillow dekodiert und liefert PNG an tesseract, was ohnehin für alle Bildformate der einfachere Weg ist |
| A6 | `pytesseract` und `tesserocr` sind für diesen Einsatz die schlechteren Optionen | Alternatives Considered | Nur Aufwand, kein Risiko |
| A7 | Die Lizenzdateien der tesseract-Pakete liegen unter `/usr/share/doc/tesseract-ocr/copyright` und den Sprachpaket-Entsprechungen | Standard Stack | Der Bau bricht am `test -s`, was der gewollte Fehlerzeitpunkt ist |
| A8 | Ein 24-Stunden-Gate plus Ruhe-Gate reicht als Ersatz für ein echtes Wartungsfenster | Pitfall 5 | Der Abgleich läuft zur Unzeit. Abgemildert durch die 30-Sekunden-Scheiben |

## Open Questions

1. **Wie viel Adressraum braucht tesseract wirklich?**
   - Was wir wissen: `RLIMIT_AS` ist 512 MB, wird vom Enkel geerbt, STACK.md schätzt die OCR-Spitze auf 300 bis 600 MB je Seite bei 300 dpi.
   - Was unklar ist: ob 512 MB virtueller Adressraum reichen; die Schätzung in STACK.md ist RSS, nicht VA, und `OMP_THREAD_LIMIT=1` verändert beides.
   - Empfehlung: erster Umsetzungsschritt der Phase ist ein Messlauf im Bau-Image über eine A4-Seite bei 300 dpi mit `ulimit -v 524288`. Das Ergebnis entscheidet, ob der OCR-Enkel ein eigenes, höheres Limit bekommt.

2. **Wird der Abgleich-Cursor container- oder Nextcloud-seitig geführt?**
   - Was wir wissen: IDX-02 verlangt Fortschritt in der Datenbank, der Crawl-Cursor liegt im Job-Argument in Nextcloud.
   - Was unklar ist: ob ein containerseitiger Abgleich-Cursor als Bruch dieser Regel gilt oder als zulässige Ausnahme (der Abgleich ist reine, idempotente Reparatur).
   - Empfehlung: containerseitig in `state.db`, mit einem ausdrücklichen Absatz im Modul-Docstring. Falls die Regel streng gelesen werden soll, kann der Cursor auch als Antwortfeld der Requeue-Route zurückgeschrieben werden, das ist eine Zeile mehr.

3. **Wird `_MIN_CHARS_PER_PAGE` in dieser Phase neu vermessen, und mit welchem Korpus?**
   - Was wir wissen: `pdf.py` fordert die Nachmessung ausdrücklich ein und nennt sie Annahme A2.
   - Was unklar ist: ob der DACH-Korpus früh genug fertig ist, um sie zu speisen.
   - Empfehlung: die Messung an den Korpusbau koppeln, nicht an die OCR-Umsetzung. Sonst wird die Zahl "später" nachgezogen und bleibt für immer bei 25.

4. **Reicht `getFilesInMount` für die Abgleich-Seite, oder braucht sie einen eigenen Query?**
   - Was wir wissen: `getByAncestorInStorage` liefert `ICacheEntry` mit `getEtag()`, nach `file_id` sortiert, mit Mime-Filter in der Abfrage.
   - Was unklar ist: ob der Mime-Filter beim Abgleich stört. Eine Datei, deren Typ sich geändert hat, fällt dadurch aus der Seite und wird korrekt als gelöscht behandelt. Eine Datei, die auf der PHP-Seite erlaubt, auf der Python-Seite aber nicht erlaubt ist, würde dagegen jede Nacht einmal aufgeräumt und wieder eingereiht.
   - Empfehlung: Mime-Filter beibehalten und die beiden Allowlists in einem CI-Gate gegeneinander prüfen (siehe Pitfall 13). Das schließt den Fall aus, statt ihn zu behandeln.

5. **Wie wird "Events blockiert" im Abnahmetest hergestellt?**
   - Was wir wissen: Der Test steht wörtlich in Roadmap und CONTEXT.md.
   - Was unklar ist: der sauberste Weg. Kandidaten: eine Umgebungsvariable, die `register()` die Listener überspringen lässt (ehrlich, aber Testcode im Produktionspfad); die Datei per `occ files:scan` direkt in den Cache bringen (näher am echten Fall "Massenoperation ohne Events"); die App kurz deaktivieren und wieder aktivieren.
   - Empfehlung: `occ files:scan` beziehungsweise ein Schreibweg, der die App gar nicht erst geladen hat. Das prüft zusätzlich genau den Realfall, an dem fulltextsearch gescheitert ist.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | Bau des ExApp-Image, Test-Nextcloud, Gate B | ja | 29.5.2 | - |
| uv | Python-Gates, Lockfile | ja | 0.11.7 | - |
| Python (Host) | nur Hilfsskripte | teilweise | 3.13.1, global defekt (bekannte Projektnotiz) | `uv run` statt System-Python, so wie bisher |
| tesseract (Host) | nichts | nein | - | Läuft ausschließlich im Container; für einen schnellen Sprachtest reicht `docker run --rm python:3.13-slim-trixie` |
| PHP (Host) | nichts | nein | - | PHP-Gates laufen in CI und im Test-Nextcloud-Container, so wie bisher |
| slopcheck | Paketprüfung | ja | über uv-Tool installiert | - |

**Fehlende Abhängigkeiten ohne Ausweichweg:** keine.
**Fehlende Abhängigkeiten mit Ausweichweg:** tesseract und PHP auf dem Host, beide nur im Container gebraucht.

## Security Domain

### Anwendbare ASVS-Kategorien

| ASVS-Kategorie | Trifft zu | Standard-Kontrolle in dieser Phase |
|----------------|-----------|------------------------------------|
| V2 Authentication | nein | Unverändert AppAPI-Signatur plus `rejectForeignCaller()` in jedem neuen Controller |
| V3 Session Management | nein | Die neuen Routen sind sitzungslos, `NoCSRFRequired` ist dort korrekt, weil die Berechtigung der signierte AppAPI-Header ist |
| V4 Access Control | **ja** | ACL-Jobs ändern den Vorfilter. Die Sicherheitsgrenze bleibt der PHP-Recheck (COMP-04). Neue Routen tragen `ExAppRequired` **und** den `EX-APP-ID`-Vergleich |
| V5 Input Validation | **ja** | Alles vom Container kommt durch geschlossene Listen: Job-Art gegen ein Enum, Reason gegen `FileStateService::REASONS`, IDs gegen `intList()`. Bilder gegen die Pillow-Deckel |
| V6 Cryptography | nein | Keine neue Kryptographie |
| V12 Files and Resources | **ja** | Nur-Lesen-Invariante (IDX-07), Gate A statisch, Gate B über Prüfsummen; OCR bekommt keinerlei Schreibpfad, tesseract schreibt nichts, weil es auf stdout ausgibt |
| V14 Configuration | **ja** | Neue Umgebungsvariablen degradieren auf gemessene Defaults statt zu werfen, im Muster von `config.py` |

### Bekannte Bedrohungsmuster für diesen Stack

| Muster | STRIDE | Standard-Gegenmaßnahme |
|--------|--------|------------------------|
| Argument-Injection in den tesseract-Aufruf | Tampering / Elevation | Argumentliste, niemals `shell=True`; die Sprachliste gegen die Allowlist der installierten Sprachen prüfen, nie unverändert aus der Umgebung durchreichen |
| Bilddekoder-Bombe (riesige Deklaration, geringe Datei) | Denial of Service | `Image.MAX_IMAGE_PIXELS` bewusst setzen, Header vor dem Dekodieren lesen; strukturell dasselbe Muster wie der bereits vorhandene `EXTRACT_ARCHIVE_MEMBER_MAX_BYTES` |
| PDF-Bombe (wenige Bytes, riesige Seitenzahl oder Seitenfläche) | Denial of Service | Seitendeckel vor der Schleife, Skalierung an eine Zielkantenlänge statt an ein festes dpi binden, `RLIMIT_AS` als letzter Halt |
| Hängender tesseract-Enkel hält den Worker-Platz | Denial of Service | `subprocess.run(timeout=)` im Kind, `killpg` im Elternteil, beides bereits vorhanden. Sec-L3 wurde in Phase 2 genau dafür vorgezogen |
| Pfad- oder Inhaltsleck über `stderr` von tesseract | Information Disclosure | `stderr` einsammeln und verwerfen, nie loggen. Gilt zusätzlich für Sec-L6 (`getMessage()` im Log), das in dieser Phase ohnehin fällig ist |
| Ausweitung der OCS-Schreib-Allowlist als Nebenwirkung | Tampering | Eigener Schritt, eigener Commit, benannte Bedrohung, Negativtest; das Verfahren steht bereits in `test_readonly_gate.py` |
| Veralteter ACL-Vorfilter nach Unshare | Information Disclosure (mitigiert) | Kein Leck, weil Snippets erst nach dem Recheck gerendert werden; trotzdem vorrangige Job-Art (D-04), damit Trefferlisten nicht lügen |
| Fremde ExApp ruft die neuen Queue-Routen | Spoofing | `rejectForeignCaller()` in jeder neuen Methode, plus Sec-L4: das CI-Gate für genau diese Vertrauensgrenze ist in dieser Phase geplant und deckt dann auch die neuen Routen ab |
| Ereignisse mit fremdem Nutzerkontext | Elevation | Der Listener entscheidet nichts über Rechte, er reiht nur `fileid` ein. Die Auflösung passiert später in `describe()` mit der Mount-Liste, so wie beim Crawl |

## Project Constraints (from CLAUDE.md)

Bindende Vorgaben aus `CLAUDE.md`, gegen die der Plan geprüft werden muss:

- **Nur-Lesen-Invariante:** Nutzerdateien werden nie verändert, OCR arbeitet auf Kopien im Scratch, CI-Prüfsummen-Gate belegt es. Kein Codepfad in dieser Phase darf das aufweichen.
- **`INDEX_WORKERS = 1`:** OCR-Spitze und Embedding-Spitze treffen sich nie. Die Konstante liest ausdrücklich keine Umgebungsvariable.
- **OCR-Deckel als Stack-Vorgabe:** "100 Seiten pro Datei, 300 dpi, 30 s Timeout pro Seite" steht in STACK.md unter "Stack Patterns by Variant". Der hier vorgeschlagene Seitendeckel von 30 ist strenger; die Abweichung ist eine bewusste Entscheidung (kürzere OCR-Jobs halten die Claim-Sperre ein, siehe Pitfall 11) und gehört als solche in den Plan, nicht als stille Änderung.
- **Sprachen DE plus EN**, alles lokal, kein Telemetrie-Phoning, kein Laufzeit-Download.
- **Qualitätsgates:** ruff-Vollregelsatz über das **ganze** Repo, pyright basic, vulture, lokal grün vor dem Commit. Die ruff-Gruppe ASYNC ist im Poller scharf; jeder neue blockierende Aufruf gehört in `asyncio.to_thread`.
- **Sprache:** Code und README englisch, Projektkommunikation deutsch, keine Em-Dashes, echte Umlaute nur in deutscher Prosa und nie in Bezeichnern.
- **Repo:** öffentlich auf GitHub `street1983nk` (privates Konto), nicht Akara-GitLab.
- **Lizenz AGPL-3.0**, jede neue Abhängigkeit muss kompatibel sein und in `THIRD-PARTY.md` erscheinen (tesseract Apache-2.0, Pillow MIT-CMU, beide unproblematisch).
- **Doku-Seite mitziehen:** nach API- oder Verhaltensänderung `docs/` und die OpenAPI-Beschreibung anpassen. Neue Verdikte und die neue Route betreffen beides.
- **Nach jedem Edit committen**, keine Claude-Attribution in Commits.
- **GSD-Workflow:** Änderungen laufen über `/gsd:execute-phase`, nicht als direkte Repo-Edits.

## Sources

### Primär (HIGH confidence)

- Codebasis `C:\Users\Student\nextcloud-search`, gelesen: `php/lib/Db/QueueMapper.php`, `php/lib/Service/QueueService.php`, `php/lib/Service/FileStateService.php`, `php/lib/Service/StorageService.php`, `php/lib/BackgroundJobs/StorageCrawlJob.php`, `php/lib/AppInfo/Application.php`, `php/lib/Controller/QueueController.php`, `php/lib/Service/ExAppService.php`, `php/lib/Search/Provider.php`, `php/lib/Migration/Version001000Date20260901000000.php`, `php/appinfo/info.xml`, `backend/src/findling/extract/{sandbox,dispatch,errors,pdf}.py`, `backend/src/findling/{config}.py`, `backend/src/findling/index/{schema,writer,analyzer}.py`, `backend/src/findling/query/rewrite.py`, `backend/src/findling/store/{repo.py,schema.sql}`, `backend/src/findling/nc/queue.py`, `backend/src/findling/worker/poller.py`, `backend/tests/test_readonly_gate.py`, `backend/Dockerfile`, `backend/pyproject.toml`, `backend/uv.lock`, `docs/german-analyzer.md`, `scripts/dev/build_corpus.py`, `testdata/`
- `nextcloud/server@stable32`: `lib/public/Files/Events/Node/` (Verzeichnislisting), `lib/public/Share/Events/` (Verzeichnislisting), `apps/files_trashbin/lib/Events/` (Verzeichnislisting), `lib/private/Files/Node/HookConnector.php`, `lib/public/AppFramework/Bootstrap/IRegistrationContext.php`, `lib/public/BackgroundJob/{IJob,TimedJob}.php`, `cron.php`
- `nextcloud/app_api@main`: `lib/PublicFunctions.php` (`exAppRequest`-Signatur, `exAppRequestWithUserInit` deprecated)
- pypdfium2 5.13.0, installiert im Projekt-Venv: `_helpers/page.py` (`render`-Signatur inklusive `grayscale`, `draw_annots`), `_helpers/bitmap.py` (`buffer`, `stride`, `mode`, `to_pil`), `internal/consts.py` (`FPDFBitmap_Gray -> "L"`)
- tantivy 0.26.0 `tantivy.pyi`: `Searcher.doc(DocAddress) -> Document`, `Document.to_dict`, `Document.get_all`
- packages.debian.org/trixie: `tesseract-ocr` (5.5.0-1, arm64 `5.5.0-1+b1`), `tesseract-ocr-deu`, `-eng`, `-osd`, `-frk`, `-script-frak` (alle 1:4.1.0-2); negative Antwort "No such package" für `tesseract-ocr-deu-frak` und `tesseract-ocr-deu-latf`
- sources.debian.org API: Quellpaket `tesseract-lang` 1:4.1.0-2 in trixie
- PyPI JSON-API für `pillow`: 12.3.0, MIT-CMU, `cp313 manylinux_2_28_aarch64`-Wheel
- `slopcheck install pillow`: `[OK] pillow (pypi)`

### Sekundär (MEDIUM confidence)

- tesseract-ocr.github.io/tessdoc/FAQ.html: `OMP_THREAD_LIMIT=1`, Verhalten auf Zweikern-Maschinen, `-c tessedit_do_invert=0`
- tesseract-ocr.github.io/tessdoc/ImproveQuality.html: mindestens 300 dpi, interne Otsu-Binarisierung
- tesseract(1) Handbuch (Debian, `tesseract-ocr/tesseract` `doc/tesseract.1.asc`): `stdin`/`stdout` über `-`, Formate über Leptonica
- pillow.readthedocs.io ImageFont: `load_default(size)` seit 10.1.0, bundled Aileron Regular mit eingeschränktem Zeichensatz
- Projekteigene Recherche: `.planning/research/PITFALLS.md` (Pitfalls 3, 4, 5), `.planning/research/STACK.md`, `.planning/phases/02-*/02-AUDIT-{SECURITY,PERF,BUGS}.md`

### Tertiär (LOW confidence, Validierung nötig)

- Behauptung, Debians traineddata seien LSTM-Daten und `--oem 1` daher korrekt (A3): nur aus Kenntnis der tessdata-Historie, nicht am Paket geprüft
- Verhalten des Papierkorbs bezüglich Cache-Einträgen der Nachkommen (A4): plausibel aus der Storage-Wrapper-Architektur, nicht am Code von `files_trashbin` verifiziert
- WebP-Unterstützung der Debian-Leptonica (A5)

## Metadata

**Confidence breakdown:**

- Standard Stack: HIGH. Alle Pakete gegen packages.debian.org beziehungsweise PyPI und das eigene `uv.lock` verifiziert, inklusive der negativen Antwort für `deu_frak`.
- Architektur und Integrationspunkte: HIGH. Jede Aussage über die bestehende Codebasis stammt aus gelesenem Code, nicht aus Zusammenfassungen. Die Nextcloud-Event-Klassen sind gegen `stable32` verifiziert.
- Betriebsgrenzen der OCR (Adressraum, Zeiten, Seitenzahl): MEDIUM. Die Struktur der Deckel-Kaskade ist begründet, die konkreten Zahlen sind Startwerte und brauchen einen Messlauf (A1, A2). Das ist die einzige Stelle, an der diese Recherche etwas offen lässt, was der Plan schließen muss.
- Pitfalls: HIGH für die aus dem Code abgeleiteten (1 bis 4, 9, 11, 13, 14), MEDIUM für die aus externen Quellen abgeleiteten (5 bis 8, 10, 12).

**Research date:** 2026-09-01
**Valid until:** 2026-10-01 für die Debian- und Nextcloud-Befunde (stabile Zweige); die Codebasis-Befunde gelten, solange Phase 2 nicht angefasst wird.
