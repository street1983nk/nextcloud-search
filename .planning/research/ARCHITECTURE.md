# Architecture Research

**Domain:** Nextcloud-ExApp für Datei-Suche (OCR + Volltext + Semantik), ein Container plus PHP-Companion
**Researched:** 2026-08-15
**Confidence:** HIGH für Integrationsprotokoll und Referenzmuster (direkt aus dem Quellcode von `nextcloud/context_chat`, `nextcloud/context_chat_backend`, `nextcloud/app_api`, `cloud-py-api/nc_py_api`, `nextcloud/server` verifiziert), MEDIUM für die Storage-Layout-Empfehlung (sqlite-vec ist noch Alpha)

---

## Executive Summary der Architektur-Entscheidungen

Sechs Entscheidungen tragen dieses System. Alle sechs sind unten begründet.

| # | Entscheidung | Kurzbegründung |
|---|--------------|----------------|
| 1 | **Pull statt Push**: der Container holt Arbeit aus einer OCS-Queue der PHP-App ab | Backpressure kommt gratis, PHP-Cron kann nicht timeouten, Absturz-Resume ist trivial |
| 2 | **Crawl pro Mount, nicht pro Nutzer**, Cursor auf `fileid` | Groupfolder werden einmal statt N-mal indexiert, Resume ist ein Integer |
| 3 | **Berechtigungen als Join-Tabelle im Index**, nicht als Rückfrage an Nextcloud zur Abfragezeit | Suchlatenz bleibt konstant, Zugriffsänderungen kosten keine Neuberechnung von Embeddings |
| 4 | **Inhalts-Gateway in der PHP-App** (`GET /files/{fileId}?userId=`), kein WebDAV aus dem Container | Nextcloud löst die Rechte selbst auf, kein Passwort, kein App-Token, kein Impersonation-Bastel |
| 5 | **Eine SQLite-Datei** für FTS5, Vektoren, Dokumentmapping und ACL | Der ACL-Filter wird zu einem SQL-Join statt zu einer Materialisierung in der Anwendungsschicht |
| 6 | **`IProvider`, niemals `IExternalProvider`** in der PHP-App | `IExternalProvider` ist in der Unified-Search-UI standardmäßig ausgeschaltet, das zerstört Zero-Config |

---

## Standard Architecture

### System Overview

```
┌───────────────────────────────────────────────────────────────────────────┐
│                     NEXTCLOUD (PHP-Prozess)                               │
├───────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ SearchProv.  │  │ Event-       │  │ Crawl-Jobs   │  │ Admin-        │  │
│  │ (IProvider)  │  │ Listener     │  │ (BG-Jobs)    │  │ Settings      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                 │                 │                  │          │
│         │                 ▼                 ▼                  │          │
│         │          ┌─────────────────────────────────┐         │          │
│         │          │ QUEUE-TABELLEN in oc_ (files,   │         │          │
│         │          │ actions) mit Lock-Spalte        │         │          │
│         │          └────────────────┬────────────────┘         │          │
│         │                           │                          │          │
│         │          ┌────────────────▼────────────────┐         │          │
│         │          │ OCS-API, alle #[ExAppRequired]  │◄────────┘          │
│         │          │  GET/DELETE /queues/documents   │                    │
│         │          │  GET/DELETE /queues/actions     │                    │
│         │          │  GET /files/{fileId}?userId=    │  Inhalts-Gateway   │
│         │          │  GET /queues/*/stats            │                    │
│         │          └────────────────▲────────────────┘                    │
└─────────┼───────────────────────────┼─────────────────────────────────────┘
          │ exAppRequest(appId,       │ nc.ocs(...) mit
          │   route, userId)          │ AUTHORIZATION-APP-API
          ▼                           │
┌───────────────────────────────────────────────────────────────────────────┐
│                  AppAPI-TRANSPORT (Proxy /apps/app_api/proxy/*, HaRP)     │
│  Header hin: AA-VERSION, EX-APP-ID, EX-APP-VERSION, AUTHORIZATION-APP-API │
└───────────────────────────────────────────────────────────────────────────┘
          │                           ▲
          ▼                           │
┌───────────────────────────────────────────────────────────────────────────┐
│                     ExApp-CONTAINER (Python 3.13, FastAPI)                │
├───────────────────────────────────────────────────────────────────────────┤
│  HTTP-Ebene (schnell, synchron, unter 2 s)                                │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ /search    │ │ /enabled   │ │ /status    │ │ /heartbeat │              │
│  └─────┬──────┘ └────────────┘ └─────┬──────┘ └────────────┘              │
├────────┼──────────────────────────────┼──────────────────────────────────┤
│  Worker-Ebene (langlebige Threads, unabhaengig von HTTP-Timeouts)         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ Fetcher    │ │ Extract-   │ │ OCR-Pool   │ │ Embed-Pool │              │
│  │ (Polling)  │→│ Pool       │→│ (RAM-Cap)  │→│ (ONNX)     │              │
│  └────────────┘ └────────────┘ └────────────┘ └─────┬──────┘              │
│  ┌────────────┐                                     │                     │
│  │ Action-    │ (Zugriffs- und Loeschauftraege)     │                     │
│  │ Fetcher    │─────────────────────────────────────┤                     │
│  └────────────┘                                     ▼                     │
├───────────────────────────────────────────────────────────────────────────┤
│  Storage-Ebene: $APP_PERSISTENT_STORAGE                                   │
│  ┌──────────────────────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ index.db (SQLite, WAL)       │ │ state.db │ │ models/  │ │ tmp/     │  │
│  │  documents, chunks, fts,     │ │ Fortschr.│ │ ONNX     │ │ OCR-     │  │
│  │  vec_chunks, acl             │ │ Fehler   │ │ Tessdata │ │ Scratch  │  │
│  └──────────────────────────────┘ └──────────┘ └──────────┘ └──────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Verantwortung | Typische Umsetzung |
|-----------|---------------|--------------------|
| **SearchProvider (PHP)** | Registriert sich in der Unified Search, übersetzt `ISearchQuery` in einen ExApp-Aufruf, baut `SearchResultEntry`-Objekte inklusive Snippet und Datei-Link | `OCP\Search\IProvider`, registriert via `$context->registerSearchProvider()`; Proxy via `IAppApiFunctions::exAppRequest($appId, '/search', $userId, 'POST', $params)` |
| **Event-Listener (PHP)** | Fängt Datei- und Share-Ereignisse ab und schreibt Queue-Zeilen | `OCP\Files\Events\Node\*`, `OCP\Share\Events\ShareCreatedEvent`, `ShareDeletedEvent`, `UserMountAddedEvent`, `UserMountRemovedEvent`, `UserDeletedEvent` |
| **Crawl-Jobs (PHP)** | Initialer Vollcrawl je Mount, Cursor auf `fileid`, plant sich selbst neu ein | `QueuedJob` plus `IJobList::scheduleAfter()` mit `last_file_id` im Job-Argument |
| **Queue-Tabellen (PHP/DB)** | Persistenter, transaktionaler Arbeitsvorrat mit Lock-Spalte | Eigene `oc_*`-Tabellen mit `QBMapper`; getrennte Spuren für Dateien und für Aktionen |
| **OCS-Queue-API (PHP)** | Der einzige Weg, auf dem der Container Arbeit und Inhalte bekommt | `OCSController` mit `#[ApiRoute]` und `#[ExAppRequired]` |
| **Inhalts-Gateway (PHP)** | Liefert Dateibytes im Nutzerkontext als Stream | `IRootFolder->getUserFolder($userId)->getFirstNodeById($fileId)->fopen('r')` in einer `StreamResponse` |
| **Fetcher-Thread (Python)** | Zieht Batches aus der Queue, verteilt sie, quittiert per DELETE | Endlosschleife mit `nc.ocs()` und `POLLING_COOLDOWN`, `ProcessPoolExecutor` für die CPU-Arbeit |
| **Extract-Pool** | MIME-Erkennung, Text aus PDF/Office/Text, Entscheidung ob OCR nötig | Prozess-Pool, harte Zeit- und Speichergrenzen je Datei |
| **OCR-Pool** | Eigene Spur, eigene Parallelität, eigenes RAM-Budget | Getrennter Pool, sonst blockiert ein 300-Seiten-Scan alles andere |
| **Embed-Pool** | Chunking und Vektorisierung | ONNX/CPU, feste Batchgröße, Modell aus `models/` |
| **Storage-Layer (Python)** | Einzige Schreib- und Lesestelle für `index.db` | Dünne Repository-Klasse, alle Statements handgeschrieben, kein ORM |
| **Search-Endpoint (Python)** | Hybrid-Retrieval plus ACL-Filter plus Snippet-Erzeugung | Zwei Kandidatenlisten, RRF-Fusion, Snippet aus FTS5 `snippet()` |
| **Admin-Status** | Fortschritt, Rückstand, Fehler | PHP-Settings-Seite liest `/queues/*/stats` lokal und `/status` per Proxy |

---

## Recommended Project Structure

Ein Monorepo mit zwei Artefakten. Getrennte Repos kosten bei einem Solo-Entwickler nur Synchronisationsaufwand, und die Versionen beider Teile müssen ohnehin im Gleichschritt laufen. Context Chat erzwingt sogar Gleichheit von Major- und Minor-Version beider Hälften.

```
nextcloud-search/
├── php/                              # Companion-App, Artefakt fuer den App Store
│   ├── appinfo/
│   │   ├── info.xml                  # App-ID, NC-Kompatibilitaet, Abhaengigkeit auf app_api
│   │   └── routes.php                # nicht-OCS-Routen (Settings)
│   ├── lib/
│   │   ├── AppInfo/Application.php   # registerSearchProvider + registerEventListener
│   │   ├── Search/Provider.php       # IProvider, ruft die ExApp
│   │   ├── Controller/
│   │   │   ├── QueueController.php   # #[ExAppRequired]: Queue + Inhalts-Gateway
│   │   │   └── StatusController.php  # Admin-Statuszahlen
│   │   ├── Listener/
│   │   │   ├── FileListener.php      # Node-Events
│   │   │   ├── ShareListener.php     # Share-Events
│   │   │   └── UserDeletedListener.php
│   │   ├── BackgroundJobs/
│   │   │   ├── StorageCrawlJob.php   # ein Job je Mount, Cursor auf fileid
│   │   │   ├── SchedulerJob.php      # startet fehlende Crawl-Jobs nach
│   │   │   └── ReconcileJob.php      # periodischer Abgleich gegen Event-Verluste
│   │   ├── Db/                       # QueueFile, QueueAction plus Mapper
│   │   ├── Service/
│   │   │   ├── StorageService.php    # Mounts, Dateien je Mount, Nutzer je fileId
│   │   │   ├── QueueService.php      # Einfuegen, Deduplizieren, Zaehlen
│   │   │   └── ExAppService.php      # der einzige Ort mit exAppRequest
│   │   └── Migration/                # Tabellen + fehlende Indizes
│   └── tests/
│
├── backend/                          # ExApp-Container
│   ├── main.py                       # FastAPI-App, Lifespan, Thread-Start
│   ├── src/ncsearch/
│   │   ├── api/
│   │   │   ├── search.py             # POST /search
│   │   │   ├── lifecycle.py          # /enabled, /heartbeat, /init
│   │   │   └── status.py             # GET /status fuer die Admin-Seite
│   │   ├── workers/
│   │   │   ├── fetcher.py            # Dokument-Queue-Polling
│   │   │   ├── actions.py            # Zugriffs- und Loeschauftraege
│   │   │   └── pools.py              # Pool-Groessen aus dem RAM-Budget
│   │   ├── pipeline/
│   │   │   ├── detect.py             # MIME, Groesse, OCR-Bedarf
│   │   │   ├── extract.py            # PDF, Office, Text
│   │   │   ├── ocr.py                # OCRmyPDF/Tesseract-Aufruf
│   │   │   ├── chunk.py              # Chunking mit Overlap
│   │   │   └── embed.py              # ONNX-Embeddings
│   │   ├── storage/
│   │   │   ├── schema.sql            # das Schema als Datei, nicht im Code
│   │   │   ├── index_repo.py         # einzige Schreibstelle
│   │   │   ├── acl_repo.py           # Zugriffs-Tabelle
│   │   │   └── state_repo.py         # Fortschritt, Fehler, Retry-Zaehler
│   │   ├── retrieval/
│   │   │   ├── fts.py                # FTS5-Kandidaten
│   │   │   ├── vector.py             # Vektor-Kandidaten
│   │   │   ├── fuse.py               # RRF
│   │   │   └── snippet.py            # Trefferausschnitt
│   │   └── nc/
│   │       ├── client.py             # nc_py_api-Session
│   │       └── content.py            # Inhalts-Gateway-Abruf
│   ├── Dockerfile                    # multi-arch, tesseract, ghostscript
│   └── tests/
│
└── .planning/
```

### Structure Rationale

- **`php/lib/Service/ExAppService.php`:** genau eine Datei darf `exAppRequest` aufrufen. Sonst verstreut sich die Fehlerbehandlung (Timeouts, 503, Retry-Header) über Provider, Controller und Jobs.
- **`backend/src/ncsearch/storage/`:** die Storage-Schicht ist das einzige Modul, das SQL kennt. Wenn das Vektor-Backend später getauscht werden muss (sqlite-vec ist Alpha), ist das ein Modul und nicht das halbe Projekt.
- **`backend/src/ncsearch/workers/` getrennt von `api/`:** die Worker leben in Threads mit eigener Lebensdauer, die API-Handler nicht. Diese Trennung im Code sichtbar zu machen verhindert, dass jemand langlaufende Arbeit in einen HTTP-Handler legt.
- **`schema.sql` als Datei:** Migrationen und Schema-Diffs werden lesbar, und man kann das Schema in einem Review beurteilen, ohne Python zu lesen.

---

## Architectural Patterns

### Pattern 1: Pull-basierte Indexierungs-Queue (Reverse Queue)

**Was:** Nextcloud schiebt keine Arbeit in den Container. Die PHP-App füllt nur Queue-Tabellen. Der Container hat langlebige Worker-Threads, die per OCS einen Batch abholen, verarbeiten und danach per DELETE quittieren. Nicht quittierte Zeilen bleiben gesperrt und werden nach Ablauf des Locks erneut ausgeliefert.

**Wann:** Immer, wenn die Verarbeitung teuer und in der Dauer schwankend ist. OCR einer 300-Seiten-Scan-PDF dauert Minuten. Das darf nie in einem HTTP-Request oder in einem PHP-Cron-Lauf hängen.

**Trade-offs:**
- Plus: Backpressure ist automatisch. Der Container zieht nur so viel, wie er schafft. Auf einer 4-GB-ARM-Box ist das der einzige Mechanismus, der wirklich hält.
- Plus: Absturz-Resume ist trivial. Ein Kill mitten in der Verarbeitung bedeutet nur, dass ein Lock abläuft und die Zeile erneut kommt. Die Verarbeitung muss idempotent sein, was sie ohnehin sein sollte.
- Plus: Keine AppAPI-Proxy-Timeouts auf dem heißen Pfad.
- Minus: Polling erzeugt Grundlast, auch wenn nichts zu tun ist. Mit einer Abkühlzeit von 15 bis 30 Sekunden bei leerer Queue ist das vernachlässigbar.
- Minus: Die Queue liegt in der Nextcloud-Datenbank, also zahlt der Admin ihre Größe mit. Bei 200k Dateien im Initialcrawl sind das kurzzeitig 200k Zeilen. Das ist trotzdem die richtige Stelle, weil es transaktional zum Dateisystem-Zustand passt.

**So macht es Context Chat, verifiziert im Quellcode:**
```python
# context_chat_backend/task_fetcher.py, files_indexing_thread
while True:
    q_items_res = nc.ocs('GET', '/ocs/v2.php/apps/context_chat/queues/documents',
                         params={'n': batch_size})
    if not q_items.files and not q_items.content_providers:
        sleep(POLLING_COOLDOWN)
        continue
    # ... verarbeiten im ProcessPoolExecutor ...
    nc.ocs('DELETE', '/ocs/v2.php/apps/context_chat/queues/documents/',
           json={'files': done_ids, 'content_providers': []})
```

**Empfohlene Erweiterung für uns:** Der Batchbezug soll nach Kosten gewichtet sein, nicht nach Stückzahl. Ein Parameter `max_bytes` zusätzlich zu `n` verhindert, dass ein Batch aus 64 großen PDFs den Speicher sprengt. Context Chat hat das nicht und begrenzt nur die Einzeldateigröße auf 100 MB.

### Pattern 2: Crawl pro Mount mit Integer-Cursor

**Was:** Der Initialcrawl iteriert nicht über Nutzer, sondern über Einträge in `oc_mounts`. Je Mount läuft ein eigener Hintergrundjob, der `oc_filecache` mit `storage = ? AND fileid > ? ORDER BY fileid ASC LIMIT ?` liest und den zuletzt gesehenen `fileid` als Job-Argument für den nächsten Lauf zurückschreibt.

**Wann:** Immer beim Initialcrawl und beim periodischen Abgleich.

**Trade-offs:**
- Plus: Ein Groupfolder, der 50 Nutzern gemountet ist, wird einmal gecrawlt, nicht 50-mal. Das ist der Unterschied zwischen brauchbar und unbrauchbar auf kleinen Instanzen.
- Plus: Der Resume-Zustand ist ein einziger Integer je Mount. Kein Snapshot, keine Bloom-Filter, keine Marker-Dateien.
- Plus: Die Ausschlüsse (`files_versions/`, `files_trashbin/`, MIME-Whitelist, Größengrenzen) laufen als SQL-Prädikat und nicht als Python-Filter nach dem Netzwerktransfer.
- Minus: Man muss die relevanten Mount-Typen kennen. Context Chat pflegt dafür eine Whitelist `ALLOWED_MOUNT_TYPES` plus `HOME_MOUNT_TYPES` und muss bei Home-Mounts den Root auf den `files`-Ordner umbiegen, weil der Storage-Root darüber liegt.
- Minus: External Storages, die nicht im Filecache stehen, werden nicht gefunden. Das ist die dokumentierte Grenze, nicht ein Fehler.

**Struktur (aus `StorageCrawlJob`, verifiziert):**
```php
const BATCH_SIZE = 2000;
protected function run($argument): void {
    $lastFileId = $argument['last_file_id'] ?? 0;
    foreach ($this->storageService->getFilesInMount($storageId, $rootId, $lastFileId, self::BATCH_SIZE) as $fileId) {
        $this->queue->insertIntoQueue(/* ... */);
    }
    $this->jobList->scheduleAfter(self::class, $this->time->getTime() + $interval,
        ['storage_id' => $storageId, 'root_id' => $rootId, 'last_file_id' => $lastSeenFileId]);
}
```

### Pattern 3: Berechtigungen als Join-Tabelle im Index

Das ist die wichtigste Entscheidung des Projekts. Die vollständige Abwägung steht im eigenen Abschnitt weiter unten. Die Kurzform:

**Was:** Der Index enthält neben Dokumenten und Chunks eine schmale Tabelle `acl(uid, source_id)`. Beim Indexieren liefert die PHP-App zu jeder Datei die vollständige Liste der Nutzer, die sie sehen können. Bei Zugriffsänderungen werden nur Zeilen dieser Tabelle gesetzt oder gelöscht, ohne Neuextraktion und ohne neue Embeddings.

**Wann:** Bei jeder mandantenfähigen Suche über geteilte Inhalte.

**Trade-offs:**
- Plus: Zugriffsänderungen sind billig. Ein neuer Share auf einen Ordner mit 5.000 Dateien kostet 5.000 kleine Inserts, nicht 5.000 OCR-Läufe.
- Plus: Die Suchlatenz ist konstant und unabhängig davon, wie viele Dateien der Nutzer sehen darf.
- Minus: Fanout. Ein Groupfolder mit 100k Dateien und 20 Mitgliedern ergibt 2 Mio. ACL-Zeilen. In SQLite mit einem zusammengesetzten Primärschlüssel sind das grob 60 bis 80 MB. Für die Zielgröße tragbar, aber es ist die Tabelle, die zuerst groß wird.
- Minus: Die Wahrheit liegt jetzt an zwei Orten. Ohne periodischen Abgleich driftet der Index gegen die Realität.

### Pattern 4: Inhalts-Gateway statt WebDAV-Impersonation

**Was:** Der Container lädt Dateibytes nicht per WebDAV, sondern von einem `#[ExAppRequired]`-Endpunkt der PHP-App, der `fileId` und `userId` entgegennimmt und den Inhalt als Stream zurückgibt. Nextcloud löst die Rechte dabei selbst auf, weil der Zugriff über `getUserFolder($userId)` läuft.

**Wann:** Für jeden Inhaltsabruf im Indexierungspfad.

**Trade-offs:**
- Plus: Der Container braucht kein Nutzerpasswort, kein App-Token und keine WebDAV-Session. Der einzige Credential ist das AppAPI-Shared-Secret.
- Plus: Wenn die Datei zwischen Enqueue und Abruf gelöscht oder der Share entzogen wurde, liefert der Endpunkt sauber 404 statt Bytes, auf die niemand mehr ein Anrecht hat. Das ist ein eingebauter Sicherheits-Recheck.
- Plus: Der Zugriff über `fileId` ist umbenennungsfest. Pfade sind es nicht.
- Minus: Der Bytestrom läuft durch den PHP-Prozess. Bei sehr großen Dateien belegt das einen PHP-Worker. Deswegen gehört eine harte Größenobergrenze in den Crawl-Filter und nicht erst in den Container.

**Verifizierte Referenz (`QueueController::getFileContents`):**
```php
#[ExAppRequired]
#[ApiRoute(verb: 'GET', url: '/files/{fileId}')]
public function getFileContents(IRootFolder $rootFolder, int $fileId, string $userId) {
    $file = $rootFolder->getUserFolder($userId)->getFirstNodeById($fileId);
    if (!$file instanceof \OCP\Files\File) {
        return new DataResponse(['error' => '...'], Http::STATUS_NOT_FOUND);
    }
    return new Http\StreamResponse($file->fopen('r'));
}
```

### Pattern 5: Zweistufiges Retrieval mit RRF-Fusion

**Was:** Zwei unabhängige Kandidatenlisten, eine aus FTS5 mit BM25, eine aus der Vektorsuche, werden mit Reciprocal Rank Fusion zusammengeführt: `score(d) = Summe über Methoden von 1 / (k + rang(d))`, `k` typischerweise 60. Der Berechtigungsfilter wird direkt in beide Teilabfragen gezogen, nicht erst danach angewendet.

**Wann:** Sobald semantische Suche dazukommt. Vorher ist der FTS5-Zweig allein die vollständige Antwort.

**Trade-offs:**
- Plus: RRF braucht keine kalibrierten Scores. BM25-Werte und Kosinusdistanzen sind nicht vergleichbar, Ränge schon. Das erspart eine Gewichtungs-Einstellung, die man ohne Bruch des Zero-Config-Versprechens gar nicht anbieten könnte.
- Plus: Fällt ein Zweig aus (Modell nicht geladen, Vektorindex noch im Aufbau), degradiert die Suche sauber auf den anderen Zweig. Genau das braucht man während des Initialcrawls.
- Minus: RRF ignoriert die Stärke eines Treffers. Ein exakter Dateinamentreffer und ein mittelmäßiger Volltexttreffer können auf demselben Rang landen. Gegenmittel ist ein kleines, festes Feldgewicht (Titel und Pfad höher als Fließtext) innerhalb des BM25-Zweigs, nicht in der Fusion.

**Skizze:**
```sql
-- Zweig A: BM25, ACL direkt im Join
SELECT c.chunk_id, bm25(fts) AS rank
FROM fts JOIN chunks c ON c.rowid = fts.rowid
         JOIN acl a ON a.source_id = c.source_id
WHERE fts MATCH :q AND a.uid = :uid
ORDER BY rank LIMIT :n;

-- Zweig B: Vektor, Ueberfetch plus ACL-Filter, danach Nachschlag falls unterbesetzt
SELECT v.rowid, v.distance
FROM vec_chunks v
WHERE v.embedding_bit MATCH vec_quantize_binary(:qvec) AND k = :overfetch;
```

### Pattern 6: Suchproxy in der PHP-App

**Was:** Der `IProvider` in der PHP-App ist dünn. Er nimmt `ISearchQuery`, ruft die ExApp und bildet die Antwort auf `SearchResultEntry` ab.

**Wichtig und ehrlich:** Für diese konkrete Kombination gibt es **keine** Referenzimplementierung. Context Chat registriert selbst **keinen** Search-Provider (verifiziert in `lib/AppInfo/Application.php`, dort stehen ausschließlich `registerEventListener`-Aufrufe). Bewiesen sind nur die beiden Hälften getrennt: der Proxy-Aufruf `exAppRequest` in Context Chat und `registerSearchProvider` in rund zwanzig Standard-Apps. Die Verbindung beider ist unsere eigene Arbeit und damit das größte Integrationsrisiko des Projekts. Deswegen steht sie im Bauplan an erster Stelle.

```php
final class Provider implements IProvider {
    public function getId(): string { return 'ncsearch'; }
    public function getName(): string { return $this->l10n->t('File contents'); }
    public function getOrder(string $route, array $routeParameters): int {
        return str_starts_with($route, 'files.') ? -5 : 25;
    }
    public function search(IUser $user, ISearchQuery $query): SearchResult {
        $res = $this->exApp->request('/search', $user->getUID(), [
            'query'  => $query->getTerm(),
            'limit'  => $query->getLimit(),
            'cursor' => $query->getCursor(),
        ]);
        return SearchResult::paginated($this->getName(), $entries, $res['cursor']);
    }
}
```

`IExternalProvider` (seit Nextcloud 32) darf **nicht** implementiert werden. Das Interface markiert Provider, die Anfragen an Dritte weiterreichen, und solche Provider sind im Unified-Search-Dialog per Schalter standardmäßig **ausgeschaltet**. Unsere Daten verlassen den Server nicht, also ist `IProvider` sowohl sachlich richtig als auch die einzige Variante, bei der ein frisch installierter Nutzer sofort Treffer sieht.

---

## Data Flow

### Fluss 1: Initiale Indexierung

```
SchedulerJob
   → je Mount aus oc_mounts ein StorageCrawlJob
        → SELECT fileid FROM oc_filecache WHERE storage=? AND fileid>cursor
             AND mimetype IN (...) AND size BETWEEN 1 AND MAX
             AND path NOT LIKE '%files_versions/%' AND NOT LIKE '%files_trashbin/%'
        → INSERT INTO oc_ncsearch_queue (storage_id, root_id, file_id)
        → scheduleAfter(self, now + interval, ['last_file_id' => n])
                                    │
        Container-Fetcher ──────────┘
   GET /queues/documents?n=64&max_bytes=64MB
        → PHP sperrt die Zeilen, baut je Zeile ein Source-Objekt
          {userIds[], sourceId, title, modified, mime, size, content: null}
   GET /files/{fileId}?userId=<erster Nutzer mit Zugriff>   (Bytes)
        → detect → extract → (OCR falls noetig) → chunk → embed
        → BEGIN; upsert documents, chunks, fts, vec_chunks, acl; COMMIT
   DELETE /queues/documents/  {files: [dbId, ...]}
```

Der `Source`-Datensatz enthält bewusst `content: null` für Dateien. Metadaten und Inhalt reisen getrennt. Das hält die Queue-Antwort klein und erlaubt, den teuren Byte-Abruf erst dann zu machen, wenn ein Worker frei ist.

### Fluss 2: Suche

```
Nutzer tippt in der Unified Search
   → Nextcloud ruft alle IProvider parallel
   → unser Provider: exAppRequest('/search', userId, {query, limit, cursor})
   → AppAPI-Proxy setzt AUTHORIZATION-APP-API = base64("<uid>:<secret>")
   → Container liest die uid aus dem Header, nimmt sie NICHT aus dem Body
        → FTS5-Zweig  (JOIN acl WHERE uid = ?)   ─┐
        → Vektor-Zweig (Ueberfetch + ACL-Filter) ─┤→ RRF → Top-N
        → snippet() je Treffer, Highlight-Marker
   → Antwort: [{fileId, path, title, snippet, score, mtime}], cursor
   → Provider baut SearchResultEntry mit Datei-Link und Vorschaubild-URL
```

Die Nutzer-Identität kommt **ausschließlich** aus dem AppAPI-Header. Ein `userId` im Request-Body wäre eine offene Rechteumgehung für jeden, der den Proxy erreicht.

### Fluss 3: Zugriffsänderung

```
ShareCreatedEvent / ShareDeletedEvent / UserMountAdded / UserMountRemoved
   → PHP ermittelt betroffene fileIds (bei Ordnern rekursiv, gebatcht)
   → StorageService::getUsersForFileId() via IUserMountCache
        (liefert die vollstaendige aktuelle Nutzerliste, nicht ein Delta)
   → INSERT INTO oc_ncsearch_actions (type='access_decl', source_id, user_ids)
                                    │
   Container-Action-Fetcher ────────┘
   GET /queues/actions?n=512
        → DELETE FROM acl WHERE source_id=?;
          INSERT INTO acl(uid, source_id) VALUES ... ON CONFLICT DO NOTHING;
   DELETE /queues/actions/
```

**Deklarativ statt inkrementell.** Die Aktion transportiert den Sollzustand ("diese Nutzer dürfen"), nicht die Änderung ("Nutzer X kam dazu"). Context Chat nennt das `UpdateAccessOp` mit einer deklarativen Variante und hat genau dafür den eigenen Ereignistyp `access_update_decl`. Der Grund ist zwingend: inkrementelle Deltas gehen bei jedem verlorenen Ereignis dauerhaft schief und lassen sich nicht reparieren. Ein deklarativer Sollzustand heilt sich bei der nächsten Zustellung selbst.

### Fluss 4: Löschung und Entzug

```
BeforeNodeDeletedEvent  (BEFORE, nicht AFTER!)
   → fileIds einsammeln, solange der Knoten noch existiert
   → Aktion 'delete' mit sourceIds, in Baenden zu 500
        → DELETE FROM documents WHERE source_id IN (...)
          (chunks, vec_chunks, acl folgen per ON DELETE CASCADE,
           FTS5 braucht ein explizites Delete)

Unshare  → nur acl-Zeilen fallen weg, das Dokument bleibt indexiert,
           solange irgendein Nutzer es noch sehen darf
Letzter Nutzer weg → verwaistes Dokument. Ein Aufraeumlauf loescht Dokumente
                     ohne acl-Zeile, nicht der Unshare-Pfad selbst.
UserDeletedEvent → Aktion 'delete_user', danach Verwaisten-Aufraeumung
```

Der `BeforeNodeDeletedEvent` statt `NodeDeletedEvent` ist kein Detail. Nach dem Löschen ist der Ordnerinhalt nicht mehr aufzählbar, und bei einem gelöschten Ordner braucht man die Kinder.

### Fluss 5: Abgleich (der Fluss, den man gerne vergisst)

```
ReconcileJob, taeglich, mit Cursor wie der Crawl
   → vergleicht je Mount-Fenster oc_filecache gegen /status/known?storage=&from=&to=
   → im Filecache, nicht im Index      → in die Dokument-Queue
   → im Index, nicht im Filecache      → in die Loesch-Queue
   → mtime weicht ab                   → in die Dokument-Queue
```

Ereignisse sind verlustbehaftet. `occ files:scan`, direkte Manipulation des Storage, External Storages, ein Container, der beim Ereignis gerade unten war: alles erzeugt stille Lücken. Ohne diesen Job wird der Index still falsch, und "still falsch" ist bei einer Suche der schlimmste Zustand, weil niemand es merkt.

---

## Permission-True Search: die Abwägung

Die Frage ist, wo die Zugriffswahrheit lebt. Es gibt drei belegte Modelle.

| Modell | Wer macht es | Index enthält | Kosten Suche | Kosten Zugriffsänderung | Risiko |
|--------|--------------|---------------|--------------|-------------------------|--------|
| **A: Denormalisierte Felder im Dokument** | fulltextsearch_elasticsearch | `owner`, `users[]`, `groups[]`, `circles[]`, `links[]` je Dokument | Ein boolescher Filter, sehr günstig | Dokument-Update je Änderung, in Elasticsearch ein Reindex des Dokuments | Gruppenwechsel eines Nutzers ist billig (die Gruppe steht im Dokument), aber jede Share-Änderung schreibt Dokumente neu |
| **B: Separate Zugriffstabelle mit Join** | context_chat (`access_list(uid, source_id)`) | Chunks plus eine schmale ACL-Tabelle | Join, günstig, **wenn** er im SQL bleibt | Nur Zeilen setzen oder löschen, keine Neuberechnung | Fanout der Tabelle; Context Chats konkrete Umsetzung skaliert schlecht, siehe unten |
| **C: Filter zur Abfragezeit gegen Nextcloud** | niemand in diesem Ökosystem | Nur Inhalte | Pro Suche ein Rückruf plus Nachschlagschleife | Null | Latenz und Nachschlag-Kaskaden; bei 100k Dateien unbrauchbar |

**Modell C scheidet aus.** Um 20 sichtbare Treffer zu liefern, müsste man Kandidaten holen, Nextcloud fragen, verwerfen, nachholen. Bei einem Nutzer mit geringer Sichtbarkeitsquote läuft das in eine unbegrenzte Schleife. Zusätzlich ruft jede einzelne Suche zurück in den PHP-Prozess, der ohnehin der Engpass ist.

**Modell A gegen Modell B.** Beide sind Denormalisierung zur Indexzeit, sie unterscheiden sich nur in der Granularität des Schreibvorgangs. In einer Engine ohne Teil-Update (Elasticsearch, Tantivy) muss man Modell A nehmen, weil ein Dokument-Update ohnehin ein vollständiges Neuschreiben ist. Dort ist die Auflösung von Gruppen und Circles sogar ein echter Vorteil: eine Gruppenmitgliedschaft ändert kein einziges Dokument.

In SQLite ist Modell B klar besser: eine ACL-Zeile ist ein Insert, ein Dokument-Rewrite wäre ein Delete plus Reindex des FTS-Eintrags plus Vektorzeilen. Und weil FTS5, Vektoren und ACL in **derselben Datei** liegen, ist der Filter ein gewöhnlicher Join und nicht ein Datentransport zwischen zwei Systemen. Das ist das eigentliche Argument für das Einzeldatei-Layout.

**Empfehlung: Modell B, mit einer expliziten Korrektur an Context Chats Umsetzung.**

Context Chat macht in `pgvector.py::doc_search` folgendes, verifiziert im Quellcode:

```python
# 1. ALLE Chunk-IDs des Nutzers nach Python holen
stmt = (sa.select(DocumentsStore.chunks)
        .join(AccessListStore, AccessListStore.source_id == DocumentsStore.source_id)
        .filter(AccessListStore.uid == user_id))
chunk_ids = [str(c) for res in session.execute(stmt).fetchall() for c in res.chunks]
# 2. Vektorsuche mit IN (...) ueber diese Liste, in Baenden,
#    weil Postgres bei 65535 Query-Parametern die Grenze zieht
for i in range(0, len(chunk_ids), PG_BATCH_SIZE):
    ...
```

Das ist der Anti-Pattern, den wir nicht kopieren dürfen. Ein Nutzer mit 100k sichtbaren Dateien und fünf Chunks je Datei materialisiert 500.000 UUIDs im Python-Speicher, bei jeder einzelnen Tastatureingabe in der Suchleiste. Die Batch-Schleife ist der sichtbare Beweis, dass das Muster an seine Grenze gestoßen ist. Für eine 4-GB-Box ist es sofort tödlich.

**Unsere Fassung:** Der Filter bleibt im SQL.

```sql
-- Volltextzweig: der ACL-Join ist Teil derselben Abfrage
SELECT c.source_id, c.chunk_no, snippet(fts, 0, '<b>', '</b>', '...', 24) AS snip,
       bm25(fts, 3.0, 1.0) AS score
FROM fts
JOIN chunks c ON c.rowid = fts.rowid
JOIN acl   a ON a.source_id = c.source_id AND a.uid = :uid
WHERE fts MATCH :q
ORDER BY score
LIMIT :n;
```

Für den Vektorzweig funktioniert dieser Join so nicht, weil `vec0` seine KNN-Abfrage selbst begrenzt. Drei Bausteine lösen das, in dieser Reihenfolge der Bevorzugung:

1. **Überfetch und Nachfiltern.** `k = limit * 8` abfragen, dann per ACL-Join reduzieren. Wenn zu wenig übrig bleibt, `k` verdoppeln und wiederholen, höchstens zweimal. Im Regelfall, in dem ein Nutzer den größten Teil dessen sieht, was in seinen Mounts liegt, trifft die erste Runde.
2. **Partition-Key auf `storage_id`.** `vec0` kann den Vektorindex intern nach einem Schlüssel sharden, ausdrücklich für mandantenfähige Abfragen gedacht. Da jede Datei genau einem Storage gehört und ein Nutzer nur eine Handvoll Mounts hat, lässt sich der Scan auf die Shards der eigenen Mounts begrenzen. Das ist die saubere Lösung des Selektivitätsproblems und passt exakt zu Nextclouds Mount-Modell.
3. **Binärquantisierung für den Scan.** `vec0` unterstützt Bit-Vektoren mit Hamming-Distanz. Bei 384 Dimensionen sind das 48 Byte je Chunk statt 1.536 Byte. 500.000 Chunks belegen im Scan 24 MB statt 768 MB. Der lineare Scan (sqlite-vec hat keinen ANN-Index) wird dadurch erst tragbar. Die genaue Reihenfolge stellt ein Rerank der besten paar hundert Kandidaten gegen int8-quantisierte Vektoren her.

Die Kombination aus 1 und 3 ist Pflicht für v1. Baustein 2 ist die dokumentierte Reserve, falls das Fanout in der Praxis weh tut.

**Bei 100k Dateien und mehr, konkret:**

| Größe | ACL-Zeilen (Annahme 3 Nutzer je Datei) | ACL-Tabelle | Bit-Vektoren (5 Chunks/Datei) | Verhalten |
|-------|----------------------------------------|-------------|-------------------------------|-----------|
| 10k Dateien | 30k | ca. 1 MB | 2,4 MB | Alles im Seiten-Cache, Suche unter 50 ms |
| 100k Dateien | 300k | ca. 12 MB | 24 MB | Weiterhin unkritisch, Scan im zweistelligen Millisekundenbereich |
| 1M Dateien | 3 Mio. | ca. 110 MB | 240 MB | Grenze des Einzeldatei-Ansatzes auf einer 4-GB-Box; Partition-Key wird Pflicht, sonst wird der lineare Scan sichtbar |

Der ehrliche Vorbehalt: die 1M-Zeile ist eine Hochrechnung aus Datenmengen, nicht aus einem Lasttest. Ein Benchmark mit synthetischen 100k Dokumenten gehört in die Phase, in der der Vektorindex gebaut wird, und zwar bevor das Schema festgezurrt wird.

---

## Storage Layout im Container-Volume

Alles unter `$APP_PERSISTENT_STORAGE` (nc_py_api liefert den Pfad über `nc_py_api.ex_app.persistent_storage()`, mit einem Cache-Verzeichnis als Rückfallebene).

```
$APP_PERSISTENT_STORAGE/
├── index.db              # SQLite, WAL: der gesamte Suchindex
├── index.db-wal
├── index.db-shm
├── state.db              # SQLite: Betriebszustand, getrennt vom Index
├── models/
│   ├── embed/            # ONNX-Modell + Tokenizer, beim ersten Start geholt
│   └── .lock             # verhindert paralleles Nachladen bei mehreren Workern
├── tmp/
│   └── ocr/              # Scratch je OCR-Lauf, harte Gesamtgroessengrenze
├── logs/                 # JSONL, rotierend
└── _version.info         # Schema- und App-Version fuer Migrationen
```

### `index.db`, Tabellen

| Tabelle | Inhalt | Warum hier |
|---------|--------|------------|
| `documents` | `source_id` (PK, z. B. `files__<fileId>`), `file_id`, `storage_id`, `path`, `title`, `mime`, `size`, `mtime`, `content_hash`, `indexed_at`, `ocr_used` | Die Zuordnung der Dokument-IDs. `content_hash` erlaubt, ein Neuschreiben ohne Inhaltsänderung zu überspringen |
| `chunks` | `chunk_id` (PK), `source_id` (FK, CASCADE), `chunk_no`, `text`, `vec_i8` (BLOB für Rerank) | Chunk-Ebene, weil Treffer und Snippet auf Chunks liegen, Rechte aber auf Dokumenten |
| `fts` | FTS5-Virtualtabelle, `external content` auf `chunks` | External Content spart die doppelte Textkopie; Preis ist, dass Deletes explizit gespiegelt werden müssen |
| `vec_chunks` | `vec0`-Virtualtabelle, `embedding_bit bit[384]`, optional Partition-Key `storage_id` | Bit-Vektoren für den Scan, Rerank gegen `chunks.vec_i8` |
| `acl` | `(uid, source_id)`, zusammengesetzter Primärschlüssel, zusätzlicher Index auf `source_id` | Der Index auf `source_id` ist für den Löschpfad nötig, der Primärschlüssel für den Suchpfad |

### `state.db`, getrennt

| Tabelle | Inhalt |
|---------|--------|
| `progress` | Je Mount: gesehen, indexiert, übersprungen, Zeitpunkt |
| `failures` | `source_id`, Fehlerklasse, Versuche, `retry_after`, letzter Fehlertext |
| `settings` | Effektive Laufzeitwerte (Poolgrößen, erkanntes RAM-Budget) |

**Warum zwei Dateien.** Der Betriebszustand wird viel häufiger geschrieben als der Index. In derselben Datei würde jedes Fortschritts-Update das WAL des Index aufblähen und mit den Lesern der Suche konkurrieren. Getrennt kann man `state.db` zudem bedenkenlos löschen: ein Neuaufbau kostet einen Abgleichlauf, keinen Neuindex.

**SQLite-Pragmas, nicht verhandelbar:** `journal_mode=WAL` (Leser blockieren Schreiber nicht, sonst hängt die Suche während des Crawls), `busy_timeout` großzügig (mehrere Worker-Threads schreiben), `synchronous=NORMAL` (unter WAL ausreichend, spart auf ARM-Boxen mit SD-Karte spürbar Ein- und Ausgabe).

**Der eine Schreiber.** SQLite hat einen globalen Schreiblock je Datenbank. Alle Worker dürfen parallel rechnen, aber der Index-Commit gehört hinter eine einzige Schreiber-Queue mit Sammel-Transaktionen von 50 bis 200 Dokumenten. Ein Commit je Dokument bringt eine Box mit SD-Karte zum Kriechen.

### Alternative, ehrlich benannt

Tantivy statt FTS5 mit einem separaten Vektorspeicher wäre reifer als sqlite-vec (0.26.0 vom April 2026 gegenüber 0.1.10-alpha.4 vom Mai 2026). Der Preis ist genau die Eigenschaft, die dieses Projekt braucht: der ACL-Join ist dann nicht mehr eine SQL-Zeile, sondern eine Zusammenführung in der Anwendungsschicht über zwei Systeme, also der Context-Chat-Anti-Pattern per Konstruktion. Wenn die Alpha-Reife von sqlite-vec ein Ausschlusskriterium ist, dann ist die richtige Antwort nicht Tantivy, sondern FTS5 allein plus eine eigene, sehr kleine Bit-Vektor-Tabelle mit Hamming-Distanz als benutzerdefinierter SQLite-Funktion. Das ist überschaubar viel Code und hält den Join intakt. Die endgültige Wahl gehört in STACK.md, das Layout-Argument bleibt davon unberührt.

---

## PHP-Companion zu ExApp: das Protokoll

### Richtung PHP zu ExApp

```php
$this->appApi->exAppRequest(
    'ncsearch',           // appId
    '/search',            // Route, muss in info.xml <routes> deklariert sein
    $userId,              // wird zu AUTHORIZATION-APP-API: base64("<uid>:<secret>")
    'POST',
    ['query' => $term, 'limit' => 20, 'cursor' => $cursor],
);
```

Gesetzte Header (aus `nc_py_api/_session.py` und der AppAPI-Dokumentation verifiziert):

| Header | Wert |
|--------|------|
| `AA-VERSION` | Mindestversion der AppAPI |
| `EX-APP-ID` | App-ID, muss der eigenen entsprechen, sonst weist der Container ab |
| `EX-APP-VERSION` | Version des Containers |
| `AUTHORIZATION-APP-API` | `base64("<userid>:<app_secret>")`, leerer Nutzerteil bedeutet Systemkontext |

Routen werden in `info.xml` unter `<external-app><routes>` deklariert, mit `url` (Regex), `verb`, `access_level` (PUBLIC, USER, ADMIN), `headers_to_exclude` und `bruteforce_protection`. Von außen laufen sie über `/apps/app_api/proxy/*`. Für uns: `/search` als USER, `/status` als ADMIN, nichts als PUBLIC.

**Antwortform `/search`:**
```json
{
  "results": [
    {"fileId": 12345, "sourceId": "files__12345",
     "path": "Documents/contract.pdf", "title": "contract.pdf",
     "snippet": "... a <b>notice period</b> of three months ...",
     "score": 0.0312, "mtime": 1755200000, "matchType": "hybrid"}
  ],
  "cursor": "eyJvIjoyMH0=",
  "degraded": {"vector": false, "reason": null}
}
```

Das Snippet kommt **fertig markiert** aus dem Container, weil nur dort der Chunktext liegt. Die PHP-Seite darf es nicht neu berechnen, sonst braucht sie den Inhalt und die Trennung ist hinfällig. `degraded` sagt der Admin-Seite ehrlich, wenn gerade nur ein Zweig läuft, etwa während des Initialcrawls oder solange das Modell nicht geladen ist.

### Richtung ExApp zu PHP

Der Container ruft ausschließlich die OCS-Endpunkte der eigenen PHP-App, alle mit `#[ExAppRequired]`. Dieses Attribut aus `OCP\AppFramework\Http\Attribute` ist die Zugangssperre: nur eine registrierte ExApp mit gültigem AppAPI-Secret kommt durch, kein Browser, kein normaler Nutzer.

| Endpunkt | Verb | Zweck |
|----------|------|-------|
| `/queues/documents/` | GET | Batch holen, sperrt die Zeilen |
| `/queues/documents/` | DELETE | Quittieren |
| `/queues/actions/` | GET, DELETE | Zugriffs- und Löschaufträge |
| `/files/{fileId}` | GET | Inhaltsstrom im Nutzerkontext |
| `/queues/*/stats` | GET | Zähler für die Admin-Seite |

### Fehler- und Rückstau-Signale

Context Chat verwendet einen eigenen Antwortheader `cc-retry: true`, an dem die PHP-Seite erkennt, ob ein Fehler wiederholbar ist. Das ist ein sinnvolles Muster: HTTP-Statuscodes allein unterscheiden nicht zwischen "Datei kaputt, nie wieder versuchen" und "Container gerade überlastet". Für uns:

| Signal | Bedeutung | Reaktion |
|--------|-----------|----------|
| `x-ncsearch-retry: true` bei 503 | Container überlastet oder Modell lädt | Zeile entsperren, `retry_after` setzen, Polling-Intervall verdoppeln |
| 4xx ohne Retry-Header | Dokument dauerhaft unverarbeitbar | In `failures` schreiben, quittieren, nie erneut anfassen |
| Timeout beim Inhaltsabruf | PHP-Seite unter Last | Zeile entsperren, exponentiell zurückziehen |

---

## Zugriff im Nutzerkontext und Ausbreitung von Löschungen

**Wie der Container an Inhalte kommt.** Nicht per WebDAV. Der Container hat kein Nutzer-Credential, und AppAPI stellt keine Impersonation im Sinne einer echten Nutzersession bereit: `AUTHORIZATION-APP-API` trägt eine Nutzer-ID, und AppAPI prüft nur, dass dieser Nutzer existiert und aktiv ist, bevor es ihn als aktiven Nutzer setzt. Das reicht für OCS-Aufrufe im Nutzerkontext. Für den Dateizugriff ist der eigene Gateway-Endpunkt trotzdem die bessere Wahl: er ist ein Aufruf statt eines WebDAV-Handshakes, er umgeht die Pfadauflösung über Namen komplett, weil er auf `fileId` arbeitet, und er ist die Stelle, an der der Rechte-Recheck kostenlos mitpassiert.

Nebenbefund zur Klarstellung: `exAppRequestWithUserInit` ist seit AppAPI 3.0.0 als veraltet markiert und ruft intern dasselbe wie `exAppRequest` auf. Wer alte Beispiele findet, sollte sie nicht übernehmen.

**Als welcher Nutzer.** Die PHP-App wählt beim Bauen des Queue-Eintrags einen beliebigen Nutzer, der die Datei sehen kann. Context Chat nimmt dafür `getMountsForStorageId(...)[0]->getUser()->getUID()`. Das ist der Abrufkontext. Die Rechte-Wahrheit für die Suche steht davon unabhängig in `userIds` und landet in der `acl`-Tabelle. Diese Trennung ist wichtig: **wer lesen darf, um zu indexieren** und **wer finden darf** sind zwei verschiedene Fragen.

**Wie Löschungen und Entzüge ankommen.**

| Ereignis | Quelle | Wirkung im Index |
|----------|--------|------------------|
| Datei gelöscht | `BeforeNodeDeletedEvent` | Dokument samt Chunks, FTS-Einträgen, Vektoren, ACL fällt weg |
| Ordner gelöscht | `BeforeNodeDeletedEvent` plus rekursive Sammlung | wie oben, gebatcht zu 500 |
| In den Papierkorb | erscheint als Rename in `files_trashbin/` | Pfadfilter greift, Dokument wird entfernt |
| Aus dem Papierkorb zurück | Rename heraus | erneut in die Queue |
| Umbenannt oder verschoben | `NodeRenamedEvent` | Pfad-Update, kein Reindex (die `fileId` bleibt), Rechte neu ermitteln |
| Share entzogen | `ShareDeletedEvent`, `UserMountRemovedEvent` | Nur `acl`-Zeilen; das Dokument bleibt für andere Berechtigte |
| Nutzer gelöscht | `UserDeletedEvent` | Alle `acl`-Zeilen des Nutzers, danach Verwaisten-Aufräumung |
| Nichts davon ausgelöst (occ, External Storage, Container war unten) | keine | Erst der Abgleichlauf repariert es |

**Ein Punkt, der leicht übersehen wird:** Der AppAPI-Events-Listener ist für Freigabe-Ereignisse nutzlos. Er kennt nach aktuellem Stand der Dokumentation genau einen `eventType` `node_event` mit den Subtypen `NodeCreatedEvent`, `NodeTouchedEvent`, `NodeWrittenEvent`, `NodeDeletedEvent`, `NodeRenamedEvent`, `NodeCopiedEvent`. Die App `webhook_listeners` deckt dieselben Node-Ereignisse plus System-Tags und Kalender ab, aber **ebenfalls keine Share-Ereignisse**. Freigaben und Mount-Änderungen sind also nur über einen normalen PHP-`IEventListener` in der Companion-App zu bekommen. Das ist ein hartes Argument dafür, die gesamte Ereignisaufnahme in PHP zu machen und den AppAPI-Events-Listener gar nicht erst zu verwenden: zwei Ereigniswege mit unterschiedlicher Semantik und unterschiedlicher Zustellgarantie zu betreiben bedeutet mehr Fehlerquellen bei null Gewinn.

---

## Scaling Considerations

| Größe | Anpassungen |
|-------|-------------|
| **bis 10k Dateien, 1 bis 5 Nutzer** | Nichts. Ein Fetcher-Thread, zwei Extract-Prozesse, ein OCR-Prozess, ein Embed-Prozess. Der komplette Index passt in den Seiten-Cache. Initialcrawl unter einer Stunde, dominiert von OCR. |
| **10k bis 200k Dateien, 5 bis 50 Nutzer** | Poolgrößen aus dem erkannten RAM-Budget ableiten, nicht aus der Zahl der Kerne. OCR bekommt eine eigene, kleinere Parallelität als die Textextraktion. Sammel-Commits von 100 Dokumenten. Crawl-Intervall drosselbar machen, damit der Admin die Erstindexierung über Nacht schieben kann. Das ist die Zielzone dieses Produkts. |
| **ab 500k Dateien oder mehr als 100 Nutzer** | Der lineare Vektorscan wird sichtbar: Partition-Key auf `storage_id` aktivieren. Der ACL-Fanout wird zum größten Objekt: prüfen, ob ein mountbasiertes Modell den nutzerbasierten Join ersetzen sollte. Ehrlicher Hinweis für die Roadmap: diese Größe liegt außerhalb der Zielhardware, und der richtige Umgang damit ist eine dokumentierte Grenze, keine Architektur, die dafür im Voraus verbogen wird. |

### Scaling Priorities

1. **Erster Engpass: OCR-Durchsatz beim Initialcrawl.** Eine gescannte Seite kostet auf ARM leicht eine bis drei Sekunden. 10.000 Scan-Seiten sind Stunden. Die Lösung ist nicht mehr Parallelität, die verbietet das RAM-Budget, sondern Priorisierung: erst alle Dateien mit vorhandener Textschicht indexieren, damit die Suche schnell nützlich wird, und OCR als Nachzügler-Spur mit niedrigerer Priorität laufen lassen. Der Nutzer sieht dann nach Minuten erste Treffer statt nach Stunden.
2. **Zweiter Engpass: SQLite-Schreiblock.** Sichtbar, wenn die Suche während des Crawls stockt. Lösung: WAL, ein einziger Schreiber-Thread, Sammel-Transaktionen. Nicht: eine zweite Datenbank.
3. **Dritter Engpass: PHP-Worker beim Inhalts-Gateway.** Sichtbar bei vielen großen Dateien parallel. Lösung: Gleichzeitigkeit der Abrufe im Container per Semaphore begrenzen, nicht über die Poolgröße, und ein `max_bytes` je Batch.
4. **Vierter Engpass: Vektorscan.** Erst jenseits der Zielgröße. Lösung: Partition-Key, dann Bit-Vektoren mit kleinerer Dimension über Matryoshka-Kürzung.

---

## Anti-Patterns

### Anti-Pattern 1: Alle zugreifbaren IDs in die Anwendungsschicht holen

**Was gemacht wird:** ACL-Join in SQL, Ergebnis nach Python, dann Vektorsuche mit `id IN (<500.000 Werte>)`. Genau das tut `context_chat` heute.
**Warum falsch:** Speicherverbrauch und Latenz wachsen linear mit dem, was der Nutzer sehen darf, nicht mit dem, was er sucht. Die Batch-Schleife um die Parametergrenze herum ist das Eingeständnis.
**Stattdessen:** Filter im SQL lassen, Überfetch plus Nachschlag für den KNN-Zweig, Partition-Key als Reserve.

### Anti-Pattern 2: Push-Indexierung aus dem PHP-Prozess

**Was gemacht wird:** Ein Hintergrundjob liest die Datei und schickt den Inhalt synchron per POST an den Container.
**Warum falsch:** Kein Backpressure. Der Cron-Lauf blockiert an OCR. Timeouts im AppAPI-Proxy erzeugen halb verarbeitete Zustände, die niemand aufräumt. Bei einem Container-Neustart mitten im Lauf ist unklar, was ankam.
**Stattdessen:** Pull, mit Lock und Quittung.

### Anti-Pattern 3: Ausschließlich auf Ereignisse vertrauen

**Was gemacht wird:** Nach dem Initialcrawl hält man den Index nur über Ereignisse aktuell.
**Warum falsch:** `occ files:scan`, External Storages, direkte Manipulation des Storage und jeder Container-Ausfall erzeugen stille Lücken. Ein Suchindex, der still unvollständig ist, ist schlimmer als gar keiner, weil das Ausbleiben eines Treffers als "gibt es nicht" gelesen wird.
**Stattdessen:** Täglicher Abgleichlauf mit demselben Mount-Cursor-Muster wie der Crawl.

### Anti-Pattern 4: `IExternalProvider` implementieren

**Was gemacht wird:** Man liest, dass das Backend "extern" ist, und implementiert das passend klingende Interface.
**Warum falsch:** Das Interface bedeutet "fragt Dritte", nicht "läuft in einem anderen Prozess". Solche Provider sind im Unified-Search-Dialog per Schalter standardmäßig ausgeschaltet. Der Nutzer installiert und sieht nichts. Das ist der direkte Widerspruch zum Kernversprechen des Produkts.
**Stattdessen:** `IProvider`. Wenn später Filter gewünscht sind, `IFilteringProvider` ergänzen.

### Anti-Pattern 5: Ein zweiter Serverprozess im Container

**Was gemacht wird:** Elasticsearch, Meilisearch oder Qdrant als Sidecar oder per Supervisor im selben Image.
**Warum falsch:** Der Grundspeicherbedarf frisst das 4-GB-Budget auf, bevor eine Datei indexiert ist. AppAPI liefert einen Container mit einem Volume; ein zweites Serverleben darin bedeutet eigenen Lebenszyklus, eigene Migrationen, eigenes Backup, eigene Absturzursachen. Das ist exakt die Konfigurationslast, die das Produkt abschaffen will.
**Stattdessen:** Eingebettete Engine im Prozess.

### Anti-Pattern 6: Nutzer-ID aus dem Request-Body

**Was gemacht wird:** Der `/search`-Endpunkt nimmt `{"userId": "...", "query": "..."}`.
**Warum falsch:** Wer den Proxy erreicht, sucht als beliebiger Nutzer. Das ist ein vollständiger Bruch des Berechtigungs-Durchgriffs, und er fällt in keinem funktionalen Test auf.
**Stattdessen:** Die Nutzer-ID ausschließlich aus `AUTHORIZATION-APP-API` lesen. Wenn eine Nutzer-ID im Body ankommt: 400 zurückgeben, nicht ignorieren, damit der Fehler früh sichtbar wird.

### Anti-Pattern 7: OCR im selben Worker wie die Textextraktion

**Was gemacht wird:** Ein Pool, der alles macht.
**Warum falsch:** Head-of-Line-Blocking. Ein 300-Seiten-Scan hält alle Slots, während tausende billige Textdateien warten. Der Nutzer sieht stundenlang nichts.
**Stattdessen:** Getrennte Spuren, getrennte Poolgrößen, Textdateien zuerst.

### Anti-Pattern 8: OCR-Scratch außerhalb des Volumes und ohne Deckel

**Was gemacht wird:** Ghostscript und Tesseract schreiben nach `/tmp` im Container-Dateisystem.
**Warum falsch:** Die Zwischenprodukte einer großen Scan-PDF sind ein Vielfaches der Quelldatei. Ein volles Container-Dateisystem ist ein schwer zu diagnostizierender Ausfall, und der Admin sieht ihn nicht in Nextcloud.
**Stattdessen:** `tmp/ocr/` im Volume, harte Gesamtgrößengrenze, Aufräumen im `finally`, und beim Start die Reste des letzten Absturzes löschen.

### Anti-Pattern 9: Crawl pro Nutzer

**Was gemacht wird:** Für jeden Nutzer dessen Home durchlaufen.
**Warum falsch:** Geteilte Ordner und Groupfolder werden N-mal gelesen, N-mal per OCR verarbeitet und N-mal eingebettet. Bei 20 Nutzern auf einem gemeinsamen Ordner ist das ein Faktor 20 auf der teuersten Operation im System.
**Stattdessen:** Pro Mount crawlen, Nutzerliste getrennt als ACL führen.

---

## Integration Points

### Externe Berührungspunkte

| Punkt | Muster | Fallstricke |
|-------|--------|-------------|
| AppAPI-Registrierung und Handshake | `/init`, `/enabled`, `/heartbeat` per nc_py_api | Die App muss `/enabled` sauber beantworten, bevor irgendein anderer Endpunkt Sinn ergibt. Aktivieren und Deaktivieren muss die Worker-Threads schlafen legen, nicht nur eine Flagge setzen. |
| AppAPI-Proxy und HaRP | `/apps/app_api/proxy/*` | HaRP ist der aktuelle Deploy-Weg; `context_chat_backend` bringt dafür ein `harp_connect.sh` mit. Ältere Anleitungen zum Deploy-Daemon sind überholt. |
| Unified Search | `IProvider` in PHP | Alle Provider laufen parallel; ein langsamer Provider bremst die gesamte Suchleiste. Harte Obergrenze auf den ExApp-Aufruf, im Zweifel leeres Ergebnis statt Warten. |
| Nextcloud-Datenbank | `oc_filecache`, `oc_mounts` über `IQueryBuilder` | Nur lesend, nie direkt schreiben. Neuere Server-Versionen bieten eine `IFileAccess`-Abstraktion, ältere nicht: beide Pfade vorhalten, wie es Context Chat mit `getMountsOld` und `getFilesInMountOld` tut. |
| `IUserMountCache` | `getMountsForFileId`, `getMountsForStorageId` | Die einzige belastbare Quelle für "wer sieht diese Datei". Nicht über die Share-API rekonstruieren, das verfehlt Groupfolder und externe Mounts. |
| App Store | `info.xml`, signiertes Release | Die App-ID ist an das Zertifikat gebunden und muss vor dem ersten Bau-Commit feststehen. Zwei Artefakte (PHP-App und ExApp) bedeuten zwei Store-Einträge mit gekoppelten Versionen. |

### Interne Grenzen

| Grenze | Kommunikation | Bemerkung |
|--------|---------------|-----------|
| PHP-App zu ExApp | HTTP über AppAPI-Proxy, ausschließlich in `ExAppService` gekapselt | Die einzige Stelle mit Timeout-, Retry- und Degradationslogik |
| ExApp zu PHP-App | OCS, `#[ExAppRequired]`, ausschließlich in `nc/client.py` gekapselt | Alle Endpunkte idempotent, weil Quittungen verloren gehen können |
| Fetcher zu Pipeline | Queue im Prozess mit Kostenbudget | Nicht nach Stückzahl begrenzen, sondern nach Bytes und geschätzter OCR-Last |
| Pipeline zu Storage | Repository-Klasse, ein Schreiber-Thread | Die einzige Stelle mit SQL. Vektor-Backend austauschbar halten, sqlite-vec ist Alpha |
| Retrieval zu Storage | Lesend, eigene Verbindung | Getrennte Verbindung mit `query_only`, damit ein Fehler im Suchpfad nie schreiben kann |

---

## Build Order: der wandelnde Skelettbau

Die Reihenfolge folgt einem Prinzip: **das unbewiesenste Stück zuerst, das teuerste Stück zuletzt.** Unbewiesen ist die Kombination aus `IProvider` und ExApp-Proxy, denn genau die macht keine bestehende App. Teuer, aber vollständig kalkulierbar sind OCR und Embeddings.

| Reihenfolge | Baustein | Warum hier | Bewiesen zu Ende, wenn |
|-------------|----------|------------|------------------------|
| **1** | ExApp-Skeleton plus PHP-Companion plus `IProvider`, der einen **fest verdrahteten** Treffer aus dem Container zurückgibt | Das ist das einzige Integrationsrisiko ohne Vorbild. Es mit zwanzig Zeilen zu beantworten statt nach zehn Wochen ist der ganze Sinn eines Skeletts. Schließt zugleich Namensgebung und App-ID ab, die vor dem Zertifikat feststehen müssen. | In der Nextcloud-Suchleiste erscheint ein Treffer, der nachweislich aus dem Container kommt |
| **2** | Queue-Tabellen, OCS-Queue-API, Inhalts-Gateway, Crawl-Job je Mount, Fetcher-Thread, der die Bytes nur zählt | Der komplette Transportweg, ohne jede Intelligenz. Danach ist die Frage beantwortet, ob Dateien vollständig und wiederaufsetzbar im Container ankommen. Die Admin-Statuszahlen fallen als Nebenprodukt ab. | Ein Crawl über 10.000 Dateien läuft durch, ein `docker restart` mittendrin verliert nichts und dupliziert nichts |
| **3** | Storage-Schicht mit **vollständigem Schema inklusive `acl`**, Textextraktion, FTS5-Index, echter `/search`-Endpunkt mit ACL-Join und Snippet | Ab hier ist es ein benutzbares Produkt: Volltextsuche über Dateiinhalte. Die `acl`-Tabelle und der Filter gehören **hierhin und nicht später**: Berechtigungen nachträglich in ein Indexschema einzuziehen ist ein Neuschreiben, kein Feature. | Zwei Testnutzer mit überlappenden Freigaben finden genau das, was sie sehen dürfen, und nichts darüber hinaus |
| **4** | Event-Listener (Node und Share), deklarative Zugriffsaktionen, Löschpfad, Abgleichlauf | Erst wenn der Index stimmt, lohnt es sich, ihn aktuell zu halten. Der Abgleichlauf gehört in dieselbe Phase wie die Ereignisse, sonst wird er nie gebaut. | Anlegen, Ändern, Umbenennen, Löschen, Teilen und Entziehen sind innerhalb einer Minute im Suchergebnis sichtbar; ein absichtlich verpasstes Ereignis wird vom Abgleich repariert |
| **5** | OCR als eigene Worker-Spur, Priorität hinter der Textextraktion, RAM- und Zeitdeckel, Scratch im Volume | Rein additiv. Fällt OCR aus, funktioniert die Suche unverändert weiter. Genau deshalb kommt es nach dem Kern und nicht davor. | Eine gescannte PDF ist findbar; ein 300-Seiten-Scan blockiert die Indexierung normaler Dateien nachweislich nicht |
| **6** | Embeddings, Vektortabelle, Hybrid-Ranking mit RRF, Degradation auf reine Volltextsuche | Der teuerste und am stärksten hardwareabhängige Teil. Er baut auf einem Schema auf, das sich in Phase 3 bis 5 bereits bewährt hat. Der Lasttest über 100k synthetische Dokumente gehört hierhin, bevor das Vektorschema fest ist. | Semantische Treffer erscheinen; bei fehlendem Modell degradiert die Suche sauber statt zu scheitern |
| **7** | Multi-Arch-Image, RAM-Autoerkennung, Admin-Statusseite, Store-Einreichung (CSR, `info.xml`, signiertes Release) | Verpackung zum Schluss, aber die App-ID stand seit Phase 1 fest. Die Vorlaufzeit für die CSR ist früh einzuplanen. | Installation aus dem Store auf einer 4-GB-ARM-Box, kein Konfigurationsschritt nötig, erste Treffer innerhalb weniger Minuten |

**Zwei Reihenfolge-Entscheidungen, die begründet gehören:**

Die `acl`-Tabelle steht in Phase 3, nicht in Phase 4. Man könnte argumentieren, dass ein Einzelnutzer-Test ohne Rechtefilter schneller zu Ergebnissen führt. Er führt aber zu einem Schema ohne Zugriffsdimension, und jede Zeile Retrieval-Code, die danach entsteht, muss beim Nachziehen angefasst werden. Der Berechtigungs-Durchgriff ist zudem eine Sicherheitseigenschaft, und Sicherheitseigenschaften, die man nachrüstet, hat man in der Regel lückenhaft.

OCR steht vor den Embeddings, obwohl OCR das aufwendigere Stück ist. Grund: OCR erweitert nur den Textkorpus und ändert am Schema nichts. Embeddings bringen eine neue Tabelle, einen neuen Abfragezweig, eine neue Ranking-Stufe und die größte Hardwareabhängigkeit mit. Das gehört auf einen Unterbau, der bereits durch echte Nutzung gelaufen ist.

---

## Confidence und offene Punkte

| Aussage | Confidence | Grundlage |
|---------|------------|-----------|
| Pull-basierte Queue ist das aktuelle Muster von Context Chat | HIGH | `task_fetcher.py` und `QueueController.php` im Quellcode gelesen |
| AppAPI-Header und `exAppRequest`-Signatur | HIGH | `nc_py_api/_session.py`, `app_api/lib/PublicFunctions.php`, offizielle Dokumentation |
| AppAPI kann keinen Search-Provider registrieren | HIGH | Kein entsprechender Controller in `app_api/lib/Controller`, kein Eintrag in der Fähigkeitsliste der ExApp-Dokumentation |
| Context Chat registriert selbst keinen Search-Provider | HIGH | `context_chat/lib/AppInfo/Application.php` enthält nur `registerEventListener` |
| `IExternalProvider` ist standardmäßig ausgeschaltet | HIGH | Quellkommentar in `lib/public/Search/IExternalProvider.php`, seit 32.0.0 |
| Weder AppAPI-Events noch `webhook_listeners` liefern Share-Ereignisse | HIGH | Beide Ereignislisten in der offiziellen Dokumentation geprüft |
| Crawl pro Mount mit `fileid`-Cursor | HIGH | `StorageCrawlJob.php` und `StorageService.php` gelesen |
| Context Chats Vektor-ACL-Filter materialisiert alle Chunk-IDs | HIGH | `vectordb/pgvector.py::doc_search` gelesen, inklusive der Batch-Schleife um die Postgres-Parametergrenze |
| fulltextsearch denormalisiert `owner`/`users`/`groups`/`circles` ins Dokument | HIGH | `fulltextsearch_elasticsearch/lib/Service/SearchMappingService.php::generateSearchQueryAccess` gelesen |
| Einzeldatei-SQLite-Layout ist die richtige Wahl | MEDIUM | Logisch schlüssig aus dem ACL-Join-Argument, aber sqlite-vec steht bei 0.1.10-alpha.4 (Mai 2026); nicht durch eine Produktivinstallation belegt |
| Bit-Vektoren machen den linearen Scan tragbar | MEDIUM | sqlite-vec dokumentiert Binärquantisierung und Hamming-Distanz; die Größenrechnung ist meine, nicht gemessen |
| Partition-Key auf `storage_id` löst das Selektivitätsproblem | MEDIUM | `vec0`-Partition-Keys sind für Mandantenfähigkeit dokumentiert; die Abbildung auf Nextcloud-Mounts ist mein Vorschlag ohne Präzedenzfall |
| Zahlen der Skalierungstabelle | LOW | Hochrechnung aus Datenmengen, kein Lasttest. Gehört in Phase 6 gemessen, bevor das Vektorschema fest wird |

**Was in einer späteren, phasenspezifischen Recherche zu klären ist:**

- Ob `SearchResultEntry` ein vorgerendertes Snippet mit Markup darstellen kann oder ob die Unified-Search-UI HTML in der Subline entfernt. Falls sie es entfernt, muss das Snippet unmarkiert geliefert werden, und die Hervorhebung entfällt oder wandert in ein Attribut.
- Wie sich der AppAPI-Proxy bei parallelen Suchanfragen verhält und welche Timeout-Obergrenze in der Unified Search real gilt.
- Ob `vec0`-Partition-Keys mit Bit-Vektoren kombinierbar sind. Beides sind vergleichsweise neue Funktionen derselben Alpha-Version.
- Verhalten bei Groupfolders im Detail: ob `IUserMountCache` bei verschachtelten Groupfolder-Rechten die effektive Sichtbarkeit korrekt auflöst oder ob eine zusätzliche Abfrage der Groupfolder-App nötig ist.

---

## Sources

**Quellcode, direkt gelesen (höchste Verlässlichkeit):**
- `nextcloud/context_chat`: `lib/AppInfo/Application.php`, `lib/Controller/QueueController.php`, `lib/Service/LangRopeService.php`, `lib/Service/StorageService.php`, `lib/Service/ActionScheduler.php`, `lib/Listener/FileListener.php`, `lib/Listener/ShareListener.php`, `lib/BackgroundJobs/StorageCrawlJob.php`, `lib/Type/Source.php`, `lib/Type/FsEventType.php`
- `nextcloud/context_chat_backend`: `context_chat_backend/task_fetcher.py`, `context_chat_backend/vectordb/pgvector.py`, `context_chat_backend/controller.py`
- `nextcloud/fulltextsearch_elasticsearch`: `lib/Service/SearchMappingService.php`
- `nextcloud/server`: `lib/public/Search/IProvider.php`, `IExternalProvider.php`, `IFilteringProvider.php`
- `nextcloud/app_api`: `lib/PublicFunctions.php`, `lib/Controller/`
- `cloud-py-api/nc_py_api`: `nc_py_api/_session.py`, `nc_py_api/ex_app/misc.py`, `nc_py_api/ex_app/defs.py`, `nc_py_api/files/__init__.py`

**Offizielle Dokumentation:**
- https://docs.nextcloud.com/server/stable/developer_manual/exapp_development/tech_details/Authentication.html
- https://docs.nextcloud.com/server/stable/developer_manual/exapp_development/tech_details/api/events_listener.html
- https://docs.nextcloud.com/server/stable/developer_manual/exapp_development/tech_details/api/routes.html
- https://docs.nextcloud.com/server/stable/developer_manual/digging_deeper/search.html
- https://docs.nextcloud.com/server/stable/admin_manual/webhook_listeners/index.html
- https://docs.nextcloud.com/server/stable/admin_manual/ai/app_context_chat.html

**Ergänzend (mittlere Verlässlichkeit):**
- https://alexgarcia.xyz/sqlite-vec/guides/binary-quant.html
- https://alexgarcia.xyz/blog/2024/sqlite-vec-metadata-release/index.html
- https://alexgarcia.xyz/blog/2024/sqlite-vec-hybrid-search/index.html
- https://simonwillison.net/2024/Oct/4/hybrid-full-text-search-and-vector-search-with-sqlite/
- https://silvio-nextcloud-exapp-architecture.pgs.sh/
- https://autoize.com/technical-deep-dive-into-nextcloud-context-chat/

---
*Architecture research for: Nextcloud-Suche-ExApp (OCR + Volltext + Semantik)*
*Researched: 2026-08-15*
