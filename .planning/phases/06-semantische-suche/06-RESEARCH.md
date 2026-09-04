# Phase 6: Semantische Suche - Research

**Recherchiert:** 2026-09-04
**Domäne:** Vektorsuche und Hybrid-Ranking in einem embedded Python-Container auf 4-GB-ARM
**Konfidenz gesamt:** MEDIUM-HIGH für die Codebasis-Befunde, MEDIUM für die Laufzeit- und Speicherrechnungen (gerechnet, nicht gemessen)

**Diese Datei trifft keine Entscheidungen.** Sie legt sie entscheidungsreif vor. Der
Abschnitt "Offene Fragen für den Discuss" am Ende ist das eigentliche Ergebnis.

---

## Lesehilfe: wie Zahlen in diesem Bericht gekennzeichnet sind

| Kennzeichen | Bedeutung |
|---|---|
| **gemessen** | aus `docs/performance.md` oder aus dem Code dieses Repositories, mit Fundstelle |
| **belegt** | von einer externen Quelle mit Datum, Link steht bei der Aussage und in "Quellen" |
| **geschätzt** | von mir gerechnet, mit vollständigem Rechenweg und genannter Unsicherheitsbandbreite |

Es steht keine einzige Zahl in diesem Bericht, die nicht einer dieser drei Klassen
zugeordnet ist. Wo eine Messung fehlt, steht das Wort "fehlt" und nicht eine
plausible Zahl.

---

## Die drei Sätze, die den Rest erklären

1. **Die Rechtekette ist an genau einer Stelle anzudocken, und die Stelle
   existiert bereits.** `findling.index.search.candidates()` ist die einzige
   Funktion, aus der Kandidaten-IDs den Container verlassen, und sie ruft den
   ACL-Vorfilter selbst auf. Wer den Vektorzweig innerhalb dieser Funktion
   verschmilzt, erfüllt Kriterium 2 strukturell statt durch Disziplin. Jede
   andere Verdrahtung, insbesondere eine zweite Route, macht den Paritätstest aus
   Phase 5 für den Vektorzweig blind.

2. **Der Arbeitsspeicher ist nicht der harte Punkt. Die Laufzeit ist es.** Der
   Volllauf hat 428,6 MB Spitze gegen eine harte Grenze von 2,0 GB gemessen
   (`docs/performance.md`, 04.09.2026), es bleiben also 1.619 MB Luft, und alle
   Posten des Vektorzweigs zusammen liegen nach meiner Rechnung bei 180 bis
   580 MB. Kriterium 5 ist beim Speicher plausibel. Das Embedding des vollen
   Textes desselben Korpus kostet dagegen nach zwei unabhängigen Rechnungen
   **54 bis 180 Stunden** auf der Zielbox, gegen 10 h 14 min, die der gesamte
   bisherige Indexlauf gebraucht hat.

3. **Die 250.000-Chunk-Schwelle ist nicht zu hoch angesetzt, sondern zu
   niedrig getroffen.** Der gemessene Korpus trägt 27.067 Textzeichen je
   Dokument. Bei voller Chunkung ergibt das rund 966.000 Chunks für 50.000
   Dokumente, also fast das Vierfache der Schwelle. Die Frage im Discuss lautet
   deshalb nicht "reicht brute force bis 250.000", sondern "wie viel Text je
   Dokument bekommt überhaupt einen Vektor".

---

## Teil 1: Wo die Semantik in der Codebasis andockt

### 1.1 Der heutige Schreibweg, Datei für Datei

| Schritt | Datei und Funktion | Was dort passiert |
|---|---|---|
| Auftragsannahme | `backend/src/findling/worker/poller.py`, `Poller` (Zeile 267) | holt Aufträge aus der PHP-Queue, ein Worker (IDX-08) |
| Extraktion | `backend/src/findling/extract/dispatch.py` | liefert `ExtractionOutcome` mit `.text`, bereits auf `MAX_TEXT_CHARS` gekappt |
| Sammeln | `poller.py::Poller._collect()` (Zeile 939) | bündelt Verdikte einer Charge |
| Umformen | `poller.py::_record_of()` (Zeile 1243) | baut aus `job` plus `outcome.text` einen `IndexRecord` |
| Schreiben | `backend/src/findling/index/writer.py`, `IndexBatchWriter.add()` (Zeile 210) | löscht erst per `file_id`, fügt dann hinzu; das macht die Wiederzustellung idempotent |
| Quittieren | `poller.py::Poller._record_verdicts()` (Zeile 982) | schreibt Verdikt und ruft `store.replace_acl()` |
| Festschreiben | `writer.py::IndexBatchWriter.flush()` (Zeile 301) | ein `commit()` je Charge, Plattenplatzprüfung davor |

**Der Einhängepunkt für die Vektoren ist `_record_of` beziehungsweise die Stelle
unmittelbar davor.** Dort liegt `outcome.text` als bereits gekappter, bereits
beurteilter Volltext vor, dort ist die `file_id` bekannt, und dort läuft der
einzige Indexworker. Das Chunken, das Embedden und das Schreiben der Vektoren
gehören in dieselbe Charge wie der Tantivy-Schreibvorgang.

**Was das für IDX-08 bedeutet:** OCR und Embedding können durch die Bauweise
nicht gleichzeitig auftreten, weil beide im selben, einzigen Worker liegen und
`INDEX_WORKERS = 1` in `config.py` (Zeile 57) ausdrücklich keine Umgebungsvariable
liest. Der Kommentar dort nennt die Embedding-Spitze bereits mit 250 bis 400 MB;
das ist eine Projektschätzung vom Baubeginn, die dieser Bericht in Teil 3 prüft.

**Ein Detail, das leicht übersehen wird:** Modellgewichte sind Dauerlast,
Aktivierungen sind Spitze. `INDEX_WORKERS=1` verhindert, dass sich die
*Aktivierungen* des Embeddings mit der OCR-Spitze treffen. Die geladenen
Modellgewichte liegen aber während der OCR-Spitze weiterhin im Speicher, sofern
die Sitzung nicht aktiv entladen wird. Das ist keine Verletzung von IDX-08, aber
es ist ein Posten, den die Formulierung "nie gleichzeitig" nicht abdeckt und der
in der Rechnung in Teil 3 einzeln steht.

### 1.2 Das Storage-Schema

**Datei:** `backend/src/findling/store/schema.sql`, geladen von
`backend/src/findling/store/repo.py` über `_SCHEMA_FILE` (Zeile 44).

Tabellen heute: `meta`, `files`, `acl`, `reconcile`, `mounts`.
`SCHEMA_VERSION` steht auf `"1"` (repo.py Zeile 50).

Zwei Stellen im Bestand sind für Phase 6 vorbereitet worden und stehen so
im Quelltext:

- `schema.sql` über der `meta`-Tabelle: *"Their names are open on purpose,
  because phase 6 adds an embedding version and must not need a migration to do
  so."* Eine `embedding_version`-Marke braucht also keine Schemaänderung an
  `meta`, nur einen neuen Schlüssel.
- `repo.py` Kopfkommentar: *"The one module in Findling that contains SQL."*
  Das ist eine Architekturaussage. Aller `vec0`-SQL gehört nach `repo.py` oder in
  ein Geschwistermodul unter `store/` mit derselben Disziplin, nicht verstreut in
  den Vektorzweig.

**Was neu dazukommt (Vorschlag zur Entscheidung, kein Beschluss):**

```sql
-- Die Vektoren selbst, in einer vec0-Virtualtabelle.
CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vectors USING vec0(
    embedding int8[384]
);

-- Die Brücke von einer Chunk-Zeile zurück auf Datei und Textstelle.
-- char_start und char_end sind kein Luxus: sie sind der einzige Weg,
-- fuer einen rein semantischen Treffer ein Snippet zu erzeugen (siehe 1.5).
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id   INTEGER PRIMARY KEY,   -- gleich dem rowid in chunk_vectors
    file_id    INTEGER NOT NULL,
    ordinal    INTEGER NOT NULL,
    char_start INTEGER NOT NULL,
    char_end   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS chunks_file ON chunks (file_id);
```

`SCHEMA_VERSION` steigt damit auf `"2"`, und `Store.version_mismatch()`
(repo.py Zeile 486) sowie `api/resources.py::expected_marks()` (Zeile 93) und
`version_version_drift()` (Zeile 120) tragen die neue `embedding_version`-Marke.

**Ein Befund, der Arbeit auslöst:** `repo.py::_connect()` (Zeile 427) ruft
**kein** `enable_load_extension`. sqlite-vec ist eine ladbare Erweiterung, also
muss diese Funktion für beide Verbindungsarten erweitert werden. Auf der
Leseseite steht `PRAGMA query_only = 1` (Zeile 452), und ob eine
`vec0`-KNN-Abfrage unter `query_only` läuft, ist zu prüfen: `vec0` legt
Schattentabellen an und könnte Temporärschreibvorgänge brauchen. Das ist eine
Fünf-Minuten-Probe und gehört an den Anfang der Phase, weil ein "nein" die
gesamte Leseseitenarchitektur berührt.

Zweiter Befund derselben Art: die CPython-Übersetzung im Abbild muss
`--enable-loadable-sqlite-extensions` tragen. Für die offiziellen
`python:3.13-slim`-Abbilder ist das üblicherweise der Fall, geprüft ist es in
diesem Projekt nicht. Auch das ist eine Ein-Zeilen-Probe im Abbild.

### 1.3 Die ACL-Kette, vollständig

Das ist der Teil, an dem Kriterium 2 hängt. Die Kette in ihrer heutigen Form,
Glied für Glied:

```
PHP: Provider::search()                    php/lib/Search/Provider.php:184
  |  Schleife ueber MAX_ROUNDS = 3         Provider.php:65, Schleife ab 247
  |  Zeitbudget 2,5 s                      Provider.php:57 BUDGET_NANOSECONDS
  v
HTTP POST /search (AppAPI-Proxy, signierter Header traegt die Identitaet)
  v
Python: api/search.py::search()            api/search.py:213
  |  Nutzer-ID ausschließlich aus         api/search.py:219 current_user_id(nc)
  |  Depends(anc_app), nie aus dem Body    api/search.py:80 extra="forbid"
  v
api/search.py::one_round()                 api/search.py:174
  |  faengt JEDE Exception, antwortet      api/search.py:199-203
  |  dann leer mit degraded=True
  v
query/rewrite.py::build_query()            rewrite.py:218
  v
index/search.py::candidates()              index/search.py:92
  |  Scanschleife, gebremst durch          index/search.py:125
  |  SEARCH_SCAN_MAX = 10.000              config.py:166
  |
  +--> store.prefilter_visible(uid, ids)   index/search.py:156   <=== VORFILTER
  |                                        repo.py:922
  |    SELECT file_id FROM acl
  |    WHERE uid IN (?, '*') AND file_id IN (...)
  |    Baender zu 1000                     repo.py:_ACL_BAND = 75
  |    '*' = ACL_ANY_USER, gedeckelte Nutzerliste, weitet absichtlich
  v
Antwort: nur fileId, score, mtime          api/search.py:96 class Candidate
         kein Name, kein Pfad, kein Text
  v
PHP: Recheck je Kandidat                   Provider.php:227 getUserFolder()
     $userFolder->getFirstNodeById()       Provider.php:342   <=== SICHERHEITSGRENZE
  v
HTTP POST /snippets (nur fuer Ueberlebende)
  v
index/search.py::snippets_for()            index/search.py:277
  |  ruft prefilter_visible ERNEUT als     index/search.py:299
  |  erste Handlung, vor dem ersten Byte Text
  v
SnippetGenerator gegen FIELD_BODY_DE       index/search.py:303
```

**Die eine richtige Stelle für den Vektorzweig ist innerhalb von
`candidates()`, oberhalb des `prefilter_visible`-Aufrufs.** Konkret: eine
zweite Rangliste aus dem Vektorspeicher erzeugen, mit RRF gegen die
Tantivy-Rangliste verschmelzen, und die *eine* verschmolzene ID-Liste an
`prefilter_visible` übergeben. Dann gilt Kriterium 2 nicht, weil jemand daran
gedacht hat, sondern weil es keinen zweiten Ausgang gibt.

**Drei Fallen, die diese Stelle mit sich bringt:**

**Falle A, die Schleifenform.** `candidates()` zieht heute inkrementell:
`while len(permitted) < needed and raw_cursor < scan_cap` (Zeile 125). Die
Schleife holt einen Brocken, filtert, holt den nächsten. RRF braucht dagegen
beide Ranglisten bis zu einer festen Tiefe (bei Elasticsearch heißt dieser
Parameter `rank_window_size`), bevor überhaupt ein Rang feststeht. Die
Schleifenform muss sich also ändern: erst ein festes Fenster aus beiden Quellen,
dann verschmelzen, dann vorfiltern, dann seitenweise ausgeben. Das ist eine echte
Umbauentscheidung und keine Ergänzung, und sie berührt `SEARCH_SCAN_MAX`.

**Falle B, die Offset-Semantik.** Der Kopfkommentar von `index/search.py`
(Zeilen 15 bis 20) begründet ausführlich, warum `offset` erlaubte Kandidaten
zählt und nie rohe Treffer: der Abstand zweier roher Cursor minus der
ausgelieferten Kandidaten ist ein Zähler für fremde Dokumente, das ist das
Zähl-Orakel T-02-93. Diese Eigenschaft muss die RRF-Verschmelzung überleben.
Sie ist eine Sicherheitseigenschaft, kein Komfort.

**Falle C, das Snippet für einen rein semantischen Treffer.** `snippets_for()`
erzeugt den Ausschnitt über `SnippetGenerator` aus der *lexikalischen* Anfrage
gegen `FIELD_BODY_DE` (Zeile 303). Ein Treffer, der nur über den Vektorzweig
kommt, hat per Definition keine wörtliche Übereinstimmung, also liefert der
Generator ein leeres Fragment. Der Code fängt das ab (*"a hit without a snippet
is still a hit"*, Zeile 296), aber für einen semantischen Treffer ist das der
Normalfall und nicht die Ausnahme. Kriterium 1 verlangt, dass der Nutzer das
Dokument über eine Umschreibung *findet*; ein Treffer ohne jede Textvorschau
erfüllt das formal und enttäuscht praktisch. **Deshalb gehören `char_start` und
`char_end` in die `chunks`-Tabelle**: der Ausschnitt des am besten passenden
Chunks lässt sich damit direkt aus dem gespeicherten `body_de` schneiden. Das ist
eine Schema-Konsequenz, die sich nur aus dem Code ergibt, nicht aus der Roadmap.

### 1.4 Der Löschweg, und warum er sicherheitsrelevant ist

Wenn ein Dokument verschwindet oder ein Share entzogen wird, müssen seine
Vektoren mit. Sonst antwortet ein gelöschtes Dokument weiter auf semantische
Anfragen, und der Vorfilter fängt das nur ab, solange die `acl`-Zeilen auch
wirklich verschwinden. Die betroffenen Stellen:

| Stelle | Datei | Was ergänzt werden muss |
|---|---|---|
| `IndexBatchWriter.drop_document()` | `index/writer.py:251` | Vektoren derselben `file_id` löschen |
| `Store.tombstone()` | `repo.py:700` | dito |
| `Store.forget_acl()` | `repo.py:966` | (ACL bleibt die Grenze, Vektoren separat) |
| `Store.reset_for_reindex()` | `repo.py:779` | Vektortabelle leeren |
| `IndexBatchWriter.add()` | `index/writer.py:224` | löscht heute per Query nach `file_id`; das Vektor-Pendant muss ebenso erst löschen und dann einfügen, sonst verdoppeln sich Chunks bei Wiederzustellung |

Die Wiederzustellung ist real: `writer.py` erklärt im Kopf (Zeilen 17 bis 22),
dass eine Charge, die nach dem Commit und vor der Quittierung abbricht, erneut
kommt. Ein Vektorschreibweg ohne vorheriges Löschen erzeugt dann Dubletten, die
den Bestand still aufblähen und die Rangliste verzerren.

### 1.5 Das Degradieren (Kriterium 3)

Der Mechanismus existiert und ist scharf: `api/search.py::one_round()` fängt
**jede** Ausnahme und antwortet mit einer leeren Runde plus `degraded=True`
(Zeilen 198 bis 203). Die Begründung im Code: die Unified Search fragt alle
Anbieter gleichzeitig, und wer eine Ausnahme wirft, kostet den Nutzer die
gesamte Suche.

**Genau dieser Mechanismus ist für Kriterium 3 zu grob.** Fehlt das Modell,
fällt der Vektorzweig aus oder ist die Erweiterung nicht geladen, dann darf das
nicht in dem `except` von `one_round` landen, denn dort wird die Antwort
**leer**. Kriterium 3 verlangt aber "liefert die Suche unverändert
Volltext-Ergebnisse statt einen Fehler".

Der Vektorzweig braucht deshalb einen **eigenen** `try/except` weiter innen, der
eine leere Vektorliste zurückgibt und die RRF-Verschmelzung damit zu einer
Identitätsabbildung auf die Tantivy-Liste macht. Der Ausfall wird protokolliert
und über `degraded` sichtbar, aber die lexikalische Antwort steht. Das ist eine
kleine Änderung mit großer Wirkung, und sie gehört als eigener Testfall in die
Abnahme ("Modelldatei umbenennen, suchen, Volltexttreffer erwarten").

### 1.6 Was auf der PHP-Seite passieren müsste: nichts

Wenn die RRF-Verschmelzung im Container stattfindet, bleibt `Provider.php`
unverändert. Das hat drei Vorteile, die im Discuss gegen jede Alternative
aufzuwiegen sind:

- Der Paritätstest aus Phase 5 (SRCH-04, Plan 05-09) testet weiterhin exakt die
  Route, die der Nutzer benutzt, und deckt damit den Vektorzweig automatisch mit
  ab.
- Die Lockstep-Versionierung (D-11) bekommt keinen neuen Vertragsbestandteil.
- Der Privacy-Vertrag Container zu PHP ("nur fileids, Zahlen und Codes") bleibt
  unverändert, weil ein Vektortreffer dieselbe `Candidate`-Form hat.

Das einzige Feld, über das man reden könnte, ist eine Herkunftsmarkierung je
Treffer ("lexikalisch", "semantisch", "beides"). Sie wäre für die Diagnose
nützlich und ist zugleich eine neue Aussage über ein Dokument, das der Recheck
noch nicht bestätigt hat. Steht als Frage im Discuss.

---

## Teil 2: Die benannten Unbekannten aus dem Research-Flag

### 2.1 sqlite-vec: Ist es weiterhin Alpha?

**Ja, und die Lage hat sich seit dem 15.08.2026 nicht verbessert, sondern
verharrt.**

| Frage | Antwort | Beleg |
|---|---|---|
| Letzte stabile Fassung | v0.1.9 | GitHub Releases API, abgerufen 04.09.2026: `v0.1.9`, `published_at 2026-03-31`, `prerelease=false` |
| Neuere Veröffentlichungen | nur Alphas | `v0.1.10-alpha.1` bis `alpha.4`, letzte am **18.05.2026**, alle `prerelease=true` |
| Letzter Commit im Repo | **2026-05-18** | GitHub Repo-API, Feld `pushed_at` |
| Offene Vorgänge | 204 | GitHub Repo-API, `open_issues_count` |
| Sterne | 8.074 | GitHub Repo-API |
| Lizenz | Apache-2.0 | GitHub Repo-API, `license.spdx_id` |
| Auf PyPI verfügbar | v0.1.9 als neueste | PyPI JSON-API, abgerufen 04.09.2026 |

**Die Zahl, auf die es ankommt: seit dem 18.05.2026 ist kein Commit mehr in das
Repository geflossen. Das sind zum Zeitpunkt dieser Recherche dreieinhalb
Monate.** Bei einem Projekt, das der Autor ausdrücklich als pre-v1 führt, ist das
ein Betriebsrisiko und kein Detail. Die Formulierung, die dieses Projekt aus dem
fulltextsearch-Trauma gelernt hat, gilt hier gegen den eigenen Baustein:
Verwaisung erkennt man an der Commit-Kurve, nicht an der Ankündigung.

Das heißt nicht "nicht benutzen". Es heißt: exakt pinnen (v0.1.9, nicht `>=`),
und im Discuss eine bewusste Antwort auf die Frage geben, was passiert, wenn in
zwei Jahren ein SQLite-Wechsel die Erweiterung bricht. Der Ausweichpfad ist
deshalb kein Anhang, sondern ein Teil der Entscheidung.

**Reifegrad und bekannte Grenzen**

| Grenze | Aussage | Beleg |
|---|---|---|
| Kein ANN-Index | v0.1.x ist ausschließlich brute force | Alex Garcia, Ankündigungsartikel zu v0.1.0: *"will be brute-force search only, which slows down on large datasets (>1M w/ large dimensions)"* |
| ANN geplant, nicht geliefert | Tracking-Vorgang #25 weiter **offen**, zuletzt 13.06.2026 aktualisiert, 18 Kommentare | GitHub Issues API, abgerufen 04.09.2026 |
| OFFSET ist teuer | Paginierung über OFFSET bedeutet KNN mit `k = LIMIT + OFFSET` | sqlite-vec Vorgang #165 |
| Speicherformate | float, int8, binary (bit) | offizielle Dokumentation |
| Metadaten- und Partitionsspalten | vorhanden in `vec0` | STACK.md vom 15.08.2026, in dieser Sitzung **nicht** gegenverifiziert, daher hier als ASSUMED geführt |

**Verhalten bei großen Tabellen:** Der Autor nennt selbst ">1M mit hohen
Dimensionen" als die Grenze, an der brute force spürbar wird. Unser Fall liegt
bei 384 Dimensionen und, nach der Rechnung in Teil 4, bei rund 966.000 Chunks
für 50.000 Dokumente bei voller Chunkung. Das ist genau die Größenordnung, die
der Autor als Grenze benennt. Das ist kein Zufall, sondern der Kern dieser
ganzen Phase.

**ARM64:** verfügbar und unproblematisch. Die Rad-Dateien von v0.1.9 auf PyPI,
abgerufen am 04.09.2026:

```
sqlite_vec-0.1.9-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
sqlite_vec-0.1.9-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux1_x86_64.whl
sqlite_vec-0.1.9-py3-none-macosx_11_0_arm64.whl
sqlite_vec-0.1.9-py3-none-macosx_10_6_x86_64.whl
sqlite_vec-0.1.9-py3-none-win_amd64.whl
```

`py3-none` bedeutet: keine Bindung an eine CPython-ABI, Python 3.13 also
unkritisch. `manylinux_2_17` ist deutlich älter als die glibc von Debian trixie,
passt also. Der Weg in die Python-Umgebung im Container ist eine gewöhnliche
Zeile in `backend/pyproject.toml` mit exakter Version; ein Systempaket oder ein
Eigenbau ist nicht nötig.

Die zwei Voraussetzungen, die **nicht** aus dem Rad kommen und geprüft werden
müssen, stehen in Abschnitt 1.2: `enable_load_extension` in `_connect()`, und ob
die CPython-Übersetzung im Abbild ladbare Erweiterungen überhaupt zulässt.

### 2.2 Die 250.000-Chunk-Schwelle: welche Messung sie entscheidet

**Woher die Zahl kommt:** aus `research/STACK.md` vom 15.08.2026, dort
ausdrücklich als "Schätzung, MEDIUM" gekennzeichnet. Sie ist nie gemessen worden.

**Was sie eigentlich behauptet:** dass ein voller brute-force-Scan über 250.000
int8-Vektoren zu 384 Dimensionen noch schnell genug für eine interaktive Suche
ist. 250.000 × 384 Byte = 96 MB Vektordaten je Scan.

**Der Maßstab, gegen den "schnell genug" zu prüfen ist, steht im eigenen Code
und ist bisher nirgends mit der Vektorsuche verknüpft worden:**
`php/lib/Search/Provider.php` führt `BUDGET_NANOSECONDS = 2_500_000_000`
(2,5 Sekunden für die gesamte Suche) und `MAX_ROUNDS = 3`. Eine Nutzersuche kann
also bis zu **drei** Container-Runden auslösen, und jede Runde würde einen
Vektorscan enthalten. Ein Scan von 300 ms bedeutet im schlechtesten Fall 900 ms
allein für die Vektorseite, zusätzlich zu Proxy-Umläufen und Recheck.

**Die Messung, die die Frage billig entscheidet:**

1. Zufallsvektoren erzeugen, keine echten Daten, kein Modell, kein Korpus:
   N int8-Vektoren zu 384 Dimensionen in eine `vec0`-Tabelle, für
   N in {50.000, 200.000, 500.000, 1.000.000}.
2. Je Größe 100 KNN-Abfragen mit k=50 fahren, p50 und p95 messen.
3. Zweimal: einmal mit warmem Seitencache, einmal nach `echo 3 >
   /proc/sys/vm/drop_caches`. Der Unterschied ist die Aussage, nicht der
   Mittelwert.
4. Auf **aarch64**, weil die Rechenschleife von sqlite-vec und die
   Speicherbandbreite architekturabhängig sind. Jede aarch64-Maschine tut es,
   auch die GitHub-ARM-Läufer aus `docker.yml`, die laut 05-CONTEXT.md bereits
   nativ arm64 bauen.

**Aufwand:** ein Skript von etwa dreißig Zeilen, Laufzeit wenige Minuten,
keine Abhängigkeit von Modell, Korpus oder Nextcloud. **Das ist die billigste
hochwertige Messung der ganzen Phase und gehört in Welle 0**, vor jede
Schema-Festlegung. Kriterium 4 verlangt genau das ("Vektorschema erst nach einem
Lasttest festgezurrt").

**Abbruchkriterium, das der Discuss festlegen sollte:** eine Obergrenze für den
Vektoranteil je Runde, aus dem 2,5-Sekunden-Budget hergeleitet. Ein Vorschlag
zur Diskussion: 300 ms p95 je Runde, das lässt bei drei Runden 900 ms für die
Vektorseite und 1,6 s für alles andere.

**Was die Messung nicht beantwortet:** wie viele Chunks tatsächlich entstehen.
Das beantwortet Teil 4, und die Antwort dort verschiebt die Frage erheblich.

### 2.3 Ausweichpfad: Bit-Vektoren und usearch

Das sind zwei verschiedene Ausweichpfade, und sie sind unterschiedlich teuer.
Die Roadmap nennt sie in einem Atemzug; der Discuss sollte sie trennen.

**Ausweich 1: Bit-Vektoren, weiterhin in sqlite-vec**

| Posten | Bewertung |
|---|---|
| Was sich ändert | Spaltentyp `bit[384]` statt `int8[384]`, Distanz wird Hamming statt Cosinus, plus eine Binarisierung des Vektors beim Schreiben und beim Fragen |
| Kosten | gering: ein Datentyp, eine Distanzfunktion, kein zweiter Persistenzpfad, kein neues Paket, dieselbe Datenbank, dasselbe Backup |
| Gewinn Platz | Faktor 8 gegenüber int8: 48 statt 384 Byte je Vektor |
| Gewinn Zeit | Faktor 8 beim Datentransport, zusätzlich ist Hamming über popcount deutlich billiger als ein Skalarprodukt; geschätzt insgesamt Faktor 8 bis 20 |
| Verlust | Qualität. Wie viel, ist für e5-small auf Deutsch **nicht belegt**; ich habe dazu keine Messung gefunden und erfinde keine |
| Übliche Gegenmaßnahme | zweistufig: binär grob vorsortieren, die besten 10 mal k dann mit den int8-Vektoren nachrechnen. Das setzt voraus, dass beide Fassungen gespeichert werden, kostet also Platz statt ihn zu sparen, und rettet dafür den Großteil der Qualität |

**Ausweich 2: usearch**

| Posten | Bewertung | Beleg |
|---|---|---|
| Aktuelle Fassung | 2.26.2, hochgeladen **31.08.2026** | PyPI JSON-API, 04.09.2026 |
| Lizenz | Apache-2.0 | PyPI-Metadaten |
| aarch64 und cp313 | ja: `usearch-2.26.2-cp313-cp313-manylinux_2_26_aarch64.manylinux_2_28_aarch64.whl` | PyPI-Dateiliste |
| Wartungslage | 55 Artefakte im aktuellen Release, Veröffentlichung vier Tage vor dieser Recherche | PyPI |
| Verfahren | HNSW, also approximativ statt exakt | Projektdokumentation, in dieser Sitzung nicht einzeln geprüft |

Der Wartungsvergleich ist deutlich und gehört in die Entscheidung: usearch hat
vor vier Tagen veröffentlicht, sqlite-vec vor dreieinhalb Monaten zuletzt
committet.

**Was der Wechsel zu usearch kostet:**

- Ein **zweiter Persistenzpfad** neben SQLite. Heute gibt es genau eine Datei
  mit Betriebszustand, ein Backup, eine Konsistenzquelle. Danach gibt es zwei,
  die zueinander passen müssen. Das ist derselbe Klassenfehler, gegen den
  `repo.py` im Kopfkommentar mit dem Argument "kein zweiter Ort, der den
  Rückstand zu kennen behauptet" ausdrücklich schreibt.
- **Eigene ID-Verwaltung.** usearch kennt `key -> vector`, die Zuordnung auf
  `file_id` und Chunk-Ordinal muss daneben in SQLite liegen, und beide müssen
  Abbrüche gemeinsam überleben.
- **Crash-Sicherheit.** SQLite bringt WAL und `synchronous = NORMAL` mit
  (`repo.py:456`), ein HNSW-Index im Arbeitsspeicher bringt das nicht. Ein
  `docker kill` mitten im Lauf ist bei diesem Projekt ein Abnahmekriterium
  (IDX-02) und keine theoretische Möglichkeit.
- **Löschungen.** HNSW-Graphen mögen Löschungen nicht; sie hinterlassen
  üblicherweise Grabsteine, und der Graph muss periodisch neu gebaut werden.
  Bei einer App, deren Kernversprechen "entzogener Share verschwindet zeitnah"
  lautet (IDX-05), ist das ein Entwurfsproblem und keine Wartungsaufgabe.
  Die Entschärfung: der Vektorindex ist **nicht** die Sicherheitsgrenze, der
  PHP-Recheck ist es. Ein Grabstein zu viel kostet einen Kandidaten, kein Leck.
  Das muss trotzdem jemand explizit entscheiden und aufschreiben.

**Was der Wechsel bringt:** logarithmische statt lineare Suchzeit. Bei 966.000
Chunks ist das der Unterschied zwischen "371 MB je Abfrage lesen" und "ein paar
tausend Vektoren besuchen".

**Meine Einschätzung zur Reihenfolge:** Bit-Vektoren sind billig und sollten in
der Messung aus 2.2 gleich mitgemessen werden (dieselben Zufallsdaten, zweiter
Spaltentyp, zehn Zeilen mehr im Skript). usearch ist teuer und sollte erst
gezogen werden, wenn die Messung zeigt, dass auch Bit-Vektoren das Budget
reißen. Die Entscheidung gehört aber dem Owner.

### 2.4 multilingual-e5-small: Lizenz, Größe, Dimensionen, Deutsch, int8

Alle folgenden Werte am 04.09.2026 direkt über die HuggingFace-API abgefragt.

| Eigenschaft | Wert | Beleg |
|---|---|---|
| Lizenz | **MIT** | HF-API, `cardData.license = "mit"`, Tag `license:mit` |
| Dimensionen | 384 | Modellkarte, in STACK.md verifiziert |
| Parameter | rund 117,6 Mio | gerechnet: fp32-ONNX 470.268.510 Byte / 4 |
| Kontextfenster | 512 Token | XLM-RoBERTa-Architektur |
| Downloads | 12.207.955 | HF-API |
| Zuletzt geändert | 2026-04-02 | HF-API |

**Die Dateigrößen, exakt** (HF-API mit `?blobs=true`, 04.09.2026):

| Datei | Byte | entspricht |
|---|---|---|
| `onnx/model.onnx` (fp32) | 470.268.510 | 448,5 MiB |
| `onnx/model_O4.onnx` | 235.052.531 | 224,2 MiB |
| `onnx/model_qint8_avx512_vnni.onnx` | 118.346.824 | 112,9 MiB |
| `onnx/tokenizer.json` | 17.082.730 | 16,3 MiB |
| `onnx/sentencepiece.bpe.model` | 5.069.051 | 4,8 MiB |

**Damit ist die Rechnung aus STACK.md ("rund 120 MB statt rund 470 MB")
bestätigt**: 470.268.510 / 4 = 117.567.128, und die von intfloat gelieferte
int8-Datei wiegt 118.346.824 Byte. Der Faktor ist exakt vier, was bedeutet: bei
dieser Quantisierung wurde **auch die Einbettungstabelle** quantisiert.

**Und genau daran hängt ein Risiko, das bisher niemand benannt hat.** Die
Einbettungstabelle des Modells hat 250.002 × 384 = 96.000.768 Parameter. Das
sind **81,7 Prozent aller Parameter**. Die eigentliche Transformer-Rechnung
läuft auf den verbleibenden rund 21,6 Mio.

Konsequenz für den Plan "selbst quantisieren mit
`onnxruntime.quantization.quantize_dynamic`": wenn dieser Aufruf die
`Gather`-Operation der Einbettungstabelle **nicht** mit quantisiert, bleibt die
Tabelle fp32, und das Ergebnis wiegt rund 384 MB statt 118 MB. Der Unterschied
sind 266 MB dauerhafter Arbeitsspeicher und 266 MB Abbildgröße.

**Die Prüfung ist trivial und muss in den Bauablauf:** nach dem
Quantisierungsschritt die Dateigröße gegen einen Erwartungswert prüfen und den
Bau abbrechen, wenn sie wesentlich über etwa 130 MB liegt. Zwei Zeilen im
Dockerfile, und sie fangen den teuersten stillen Fehler dieser Phase.

**Qualität auf Deutsch, und was int8 kostet**

Das ist die Frage, zu der ich die belastbarste externe Messung gefunden habe.
Elastic hat `intfloat/multilingual-e5-small` int8-quantisiert und gegen das
Original gemessen (Modellkarte `elastic/multilingual-e5-small-optimized`,
abgerufen 04.09.2026). NDCG@10 auf MIRACL, Original zuerst:

| Sprache | fp32 | int8 | Änderung |
|---|---|---|---|
| **Deutsch (de)** | **0,75862** | **0,75992** | **+0,17 Prozent** |
| Russisch (ru) | 0,80309 | 0,79668 | -0,80 Prozent |
| Arabisch (ar) | 0,82778 | 0,82017 | -0,92 Prozent |
| Spanisch (es) | 0,81672 | 0,81350 | -0,39 Prozent |
| Thai (th) | 0,85072 | 0,84316 | -0,89 Prozent |
| Yoruba (yo) | 0,56193 | 0,48934 | -12,9 Prozent |

Auf englischen BEIR-Datensätzen außerhalb der Domäne fällt es deutlicher aus:
SCIFACT 0,677 auf 0,65484 (-3,4 Prozent), FIQA 0,33126 auf 0,31734 (-4,2
Prozent), nfcorpus 0,31004 auf 0,30126 (-2,8 Prozent).

**Lesart, ehrlich:** für **Deutsch** kostet die int8-Quantisierung des Modells
nach dieser Messung praktisch nichts. Der Vorbehalt gehört dazu: Elastic
quantisiert "per-layer unter denselben Bedingungen wie ELSERv2", und das ist
nicht dasselbe Verfahren wie ein nackter `quantize_dynamic`-Aufruf. Die Zahl ist
ein starkes Indiz, kein Beweis für unser Verfahren. Das deutsche Testset aus dem
Research-Flag ("fp32 gegen int8") bleibt deshalb sinnvoll, aber es entscheidet
jetzt eine Frage mit bekannter, wahrscheinlicher Antwort und ist kein Risiko
mehr, das die Phase gefährdet.

**Zweite, davon getrennte Quantisierung: die der gespeicherten Vektoren.** Das
ist eine andere Sache als die Modellquantisierung und wird oft verwechselt.
Elastic hat auch das gemessen (Blogartikel zu skalarer Quantisierung): über
BEIR-Datensätze hinweg ein durchschnittlicher relativer Rückgang von
**1,05 Prozent** in NDCG@10 beim Umstieg von fp32- auf int8-Vektoren, und
ausdrücklich der Hinweis, dass E5 dabei ein schwieriger Fall sei, weil seine
Vektoren wenig Winkelvarianz und vergleichsweise niedrige Dimension haben.
Für unseren Fall heißt das: int8 für die *Speicherung* ist gut belegt und kostet
etwa ein Prozent. Für **Bit**-Vektoren habe ich keine vergleichbare Zahl
gefunden und trage deshalb keine ein.

**Trägt der Plan "selbst quantisieren, HF_HUB_OFFLINE=1, ins Abbild backen"?**

Ja, mit drei Auflagen:

1. Die Größenprüfung nach der Quantisierung (siehe oben). Ohne sie ist der Plan
   still brüchig.
2. Die x86-Falle ist real und in dieser Sitzung bestätigt: die von intfloat
   mitgelieferte int8-Datei heißt `model_qint8_avx512_vnni.onnx`, trägt AVX512-VNNI
   also im Namen und ist auf ARM nicht zu gebrauchen. Der Bau muss vom fp32-Original
   ausgehen und selbst quantisieren, genau wie STACK.md schreibt.
3. Die Präfixe. E5 erwartet `"query: "` vor der Anfrage und `"passage: "` vor
   dem Abschnitt. Bei einem selbst registrierten Modell übernimmt fastembed das
   **nicht** automatisch. STACK.md nennt das "die häufigste stille Fehlerquelle
   in diesem Baustein", und das deckt sich mit meinem Eindruck. Das gehört als
   eigener Test in die Phase, nicht als Kommentar in den Code: eine
   Anfrage mit und ohne Präfix gegen dasselbe Dokument, die Rangfolge muss sich
   unterscheiden.

Zu `HF_HUB_OFFLINE=1`: das ist der richtige Griff, aber er ist ein Netz und kein
Beweis. Der Beweis ist ein Test, der den Container **ohne Netzwerkzugang**
startet und eine semantische Suche fahren lässt. Die CI kann das (Netzwerk im
Testschritt abklemmen), und es ist die einzige Prüfung, die das
Zero-Config-Versprechen für diesen Baustein wirklich belegt.

**Die Nebenwirkungen von fastembed auf den Abhängigkeitsbaum** (PyPI, 04.09.2026,
fastembed 0.8.0, hochgeladen 23.03.2026, Apache-2.0, weiterhin die neueste
Fassung):

| Neue Abhängigkeit | Bedingung |
|---|---|
| `onnxruntime` | für Python 3.13: `>1.21.0, !=1.24.0, !=1.24.1` |
| `numpy` | für Python 3.13: `>=2.1.0` |
| `tokenizers` | `<1.0, >=0.15` |
| `huggingface-hub` | `<2.0, >=0.20` |
| `requests` | `<3.0, >=2.31` |
| `pillow` | für Python 3.13: `<13.0, >=11.0.0` |

Die Pillow-Bedingung ist mit dem bestehenden Pin `pillow==12.3.0` in
`backend/pyproject.toml` verträglich. `huggingface-hub` und `requests` sind
**neue Netzwerkbibliotheken in einem Container, der nichts nach draußen
sprechen darf**. Das ist kein Ausschlussgrund, aber es ist eine Aussage im
Store-Text (D-12, Privacy-Block) und ein Prüfpunkt für den Offline-Test.

`onnxruntime` ist aktuell bei **1.29.0** (PyPI, hochgeladen 17.08.2026), das
aarch64-cp313-Rad wiegt 20,8 MB (`onnxruntime-1.29.0-cp313-cp313-manylinux_2_28_aarch64.whl`).
STACK.md hatte noch 1.28.0 vorgesehen; 1.29.0 erfüllt die fastembed-Bedingung
ebenfalls.

`semantic-text-splitter` (Chunking) steht bei **0.32.0**, MIT, hochgeladen
16.06.2026, mit `semantic_text_splitter-0.32.0-cp310-abi3-manylinux_2_28_aarch64.whl`.
Die `abi3`-Markierung heißt: ein Rad für alle Python-Fassungen ab 3.10.

### 2.5 RRF: Formel und die Parameter, die festzulegen sind

**Die Formel**, wörtlich aus der Elasticsearch-Referenz (abgerufen 04.09.2026):

```
score = 0.0
for q in queries:
    if d in result(q):
        score += 1.0 / ( k + rank( result(q), d ) )
return score
```

`rank` beginnt bei **1**, nicht bei 0. Das ist der häufigste Implementierungsfehler
und verschiebt die Gewichte um einen ganzen Rangplatz.

**Die Parameter, die eine Entscheidung brauchen:**

| Parameter | Übliche Vorgabe | Beleg | Was die Wahl bewirkt |
|---|---|---|---|
| `k` (rank_constant) | **60** | Elasticsearch-Referenz: *"Defaults to 60"* | klein: die vorderen Ränge dominieren stark. groß: die Liste wird flacher, hintere Ränge zählen mehr |
| Fenstertiefe | bei ES gleich `size` | Elasticsearch-Referenz zu `rank_window_size` | wie viele Treffer je Quelle überhaupt in die Verschmelzung gehen. Zu klein heißt: ein Dokument, das lexikalisch auf Rang 300 und semantisch auf Rang 2 steht, verliert seinen semantischen Rang nie |
| Gewichte je Quelle | **existieren bei Elasticsearch nicht**: *"Each child retriever carries an equal weight"* | Elasticsearch-Referenz | wir bauen selbst und können sie einführen. STACK.md schlägt `lexical=1.0, semantic=1.0` mit Konfigurierbarkeit vor, damit ein Admin die Semantik dämpfen kann, ohne sie abzuschalten |
| Chunk auf Dokument | keine Vorgabe | **kein Standard, eigene Entscheidung** | siehe unten, das ist der eigentlich schwierige Parameter |

**Der Parameter, den die Literatur nicht liefert und den dieses Projekt
zwingend selbst festlegen muss: die Aggregation von Chunks auf Dokumente.**
Tantivy rankt Dokumente. Der Vektorspeicher rankt Chunks. Bevor RRF überhaupt
etwas verschmelzen kann, müssen die Chunk-Ränge in eine Dokument-Rangliste
übersetzt werden. Die üblichen Verfahren:

| Verfahren | Wirkung |
|---|---|
| Maximum: der beste Chunk bestimmt den Rang des Dokuments | einfach, robust, bevorzugt aber kein Dokument dafür, dass es mehrfach passt |
| Summe über die besten n Chunks | belohnt Dokumente, die durchgängig zum Thema passen |
| Anzahl der Chunks in den Top-k | robust gegen Ausreißer, verliert Feinabstufung |

Ohne diese Festlegung ist die RRF-Verschmelzung nicht implementierbar. Sie steht
weder in der Roadmap noch in STACK.md und ist deshalb eine der Fragen im Discuss.
Meine Neigung geht zum Maximum, weil es das einzige Verfahren ist, das mit
**gekappter** Chunkung (siehe Teil 4) nicht systematisch lange Dokumente
bevorzugt. Aber es ist eine Owner-Entscheidung.

Ein **Cross-Encoder-Reranker** bleibt ausgeschlossen (STACK.md, 15.08.2026): er
kostet je Anfrage eine weitere Transformer-Inferenz auf der CPU. Nach den
Laufzeitrechnungen in Teil 3 ist das auf dieser Box offensichtlich nicht
vertretbar; der Ausschluss ist damit inzwischen belegter als er es im August war.

---

## Teil 3: Das RAM-Budget, und der Befund, der die Fragestellung dreht

### 3.1 Der Ausgangspunkt ist gemessen, nicht geschätzt

Aus `docs/performance.md`, Stand 04.09.2026, Generalprobe cpx22 (x86, 4 GB,
2 geteilte vCPU, AIO über HaRP, PostgreSQL 18.6):

| Größe | Wert | Art |
|---|---|---|
| Grenzwert, gegen den geprüft wird | **2,0 GB** `anon` | Festlegung |
| Findling im Volllauf über 50.000 Dateien | **428,6 MB Spitze** | gemessen |
| Dauer des Volllaufs | 10 h 14 min 14 s | gemessen |
| Härtungsprobe unter harter Grenze | 2 GB, `memory.events` durchgehend null | gemessen |
| Grundlast AIO plus HaRP | 345 MB | gemessen |
| Nutzbarer Speicher der Box | 3.814 MB | gemessen |
| Rest für Kernel und Seitencache bei 2,0 GB | 1.421 MB | gerechnet, in performance.md |
| Dateien indexiert / mit OCR | 50.068 / 10.134 | gemessen |
| Textzeichen im Index | **1.355.205.169** | gemessen |
| Index nach dem Lauf | 761.374.910 Byte (15.207 Byte je Dokument) | gemessen |

**Der freie Raum unter der Grenze beträgt 2.048 − 428,6 = 1.619,4 MB.**

Die ARM-Zeile fehlt noch und läuft laut Owner bis morgen. Alles Folgende gilt
unter dem Vorbehalt, dass die ARM-Zahl in derselben Größenordnung liegt.

### 3.2 Was der Vektorzweig an Speicher hinzufügt

| Posten | Art | Wert | Rechenweg beziehungsweise Quelle |
|---|---|---|---|
| Modellgewichte int8, dauerhaft | geschätzt | 120 bis 160 MB | Datei 118,3 MB (belegt) plus Sitzungsstrukturen von onnxruntime; Bandbreite aus dem Unterschied zwischen mmap und Kopie in die Arena |
| Modellgewichte, falls die Einbettungstabelle **nicht** quantisiert wird | geschätzt | 390 bis 430 MB | 96,0 Mio Parameter fp32 = 384 MB plus 21,6 Mio int8 = 21,6 MB |
| Tokenizer, dauerhaft | geschätzt | 60 bis 120 MB | `tokenizer.json` 16,3 MiB auf der Platte; die aufgebaute Struktur der Rust-Bibliothek ist erfahrungsgemäß ein Mehrfaches. Bandbreite bewusst weit |
| Aktivierungen, Spitze, Charge 8 zu 512 Token | geschätzt | 150 bis 300 MB | Aufmerksamkeitsmatrix je Sequenz je Schicht: 12 Köpfe × 512 × 512 × 4 Byte = 12,58 MB; Arena hält etwa zwei Schichten gleichzeitig; 8 × 12,58 × 2 = 201 MB. FFN-Zwischenschicht: 512 × 1.536 × 4 = 3,15 MB je Element je Schicht, 8 × 3,15 × 2 = 50 MB |
| Aktivierungen, Spitze, Charge 2 zu 512 Token | geschätzt | 40 bis 80 MB | dieselbe Rechnung mit 2 statt 8 |
| Aktivierungen, Charge 8 zu **256** Token | geschätzt | 45 bis 90 MB | die Aufmerksamkeitsmatrix geht quadratisch: 256² statt 512² ist Faktor 4 |
| Vektordaten im Scan | **nicht `anon`** | siehe 3.4 | landet im Dateicache derselben cgroup, `memory.current` zählt ihn, `anon` nicht |
| sqlite-vec Erweiterung selbst | geschätzt | unter 5 MB | reines C ohne Abhängigkeiten |

### 3.3 Die Summe, und die ehrliche Antwort auf Kriterium 5

| Lage | Rechnung | Neue Spitze |
|---|---|---|
| **günstig** (int8 vollständig, Charge 2, Sequenz 256) | 428,6 + 120 + 60 + 40 | **649 MB** |
| **erwartet** (int8 vollständig, Charge 8, Sequenz 512) | 428,6 + 140 + 90 + 220 | **879 MB** |
| **ungünstig** (int8 vollständig, obere Bandbreiten) | 428,6 + 160 + 120 + 300 | **1.009 MB** |
| **Havariefall** (Einbettungstabelle nicht quantisiert, obere Bandbreiten) | 428,6 + 430 + 120 + 300 | **1.279 MB** |

**Antwort: Kriterium 5 ist beim Arbeitsspeicher plausibel, und zwar deutlich.**
Selbst der Havariefall bleibt mit 1.279 MB rund 770 MB unter der Grenze von
2,0 GB. Die vier Rechnungen sind geschätzt, aber ihr Ausgangswert von 428,6 MB
ist gemessen, und die Zuschläge sind einzeln hergeleitet.

Zwei Einschränkungen gehören dazu:

- **Die 428,6 MB stammen von x86.** Die ARM-Zahl fehlt. Sollte sie deutlich
  höher liegen, verschiebt sich alles hier um denselben Betrag.
- **Die Modellgewichte liegen während der OCR-Spitze mit im Speicher.** Der
  Volllauf hat seine 428,6 MB in der OCR-Phase erreicht; darauf kommen 180 bis
  280 MB Dauerlast des Modells, auch wenn gerade nicht eingebettet wird. Das ist
  in den Tabellenzeilen oben bereits enthalten.

### 3.4 Der Posten, der in `anon` nicht auftaucht und trotzdem existiert

`docs/performance.md` erklärt (Zeilen 299 bis 303), dass `memory.current` und
`memory.peak` den Dateicache mitzählen, `anon` dagegen nicht, und dass die
Store-Aussage deshalb auf `anon` beruht.

Für den Vektorzweig heißt das: ein voller brute-force-Scan zieht die
Vektordaten in den Dateicache derselben cgroup. Bei 966.000 Chunks zu int8 sind
das **371 MB**, die in der Store-Zahl **nicht** erscheinen, aber real um die
1.421 MB konkurrieren, die für Kernel und Seitencache eingeplant sind, und die
gleichzeitig der Seitencache eines 20-GB-Korpus gern hätte. Der Kernel gibt
Dateicache unter Druck zurück, es ist also kein Speichertod-Risiko, aber es ist
ein Grund, warum ein Scan auf einer belasteten Box langsamer sein kann als in
der Messung aus 2.2 mit warmem Cache. Deshalb steht dort die Anweisung, kalt und
warm zu messen.

### 3.5 Der eigentliche harte Punkt: die Laufzeit

Hier dreht sich die Fragestellung der Phase.

**Eingangsgröße, gemessen:** 1.355.205.169 Textzeichen über 50.068 Dokumente.

**Umrechnung in Token, geschätzt:** der XLM-RoBERTa-SentencePiece-Tokenizer mit
250.002 Einträgen erzeugt auf deutscher Prosa nach meiner Einschätzung rund
**3,5 Zeichen je Token**, mit einer Bandbreite von 3,0 bis 4,0. Deutsch liegt
wegen seiner Komposita am unteren Rand mehrsprachiger Tokenizer. *Diese Zahl ist
geschätzt und in dreißig Sekunden messbar; siehe 3.7.*

→ 1.355.205.169 / 3,5 = **387,2 Mio Token**

**Rechnung 1, über den Rechenaufwand:**

- Parameter gesamt: 470.268.510 / 4 = 117,57 Mio (belegt über die Dateigröße)
- davon Einbettungstabelle: 250.002 × 384 = 96,00 Mio (gerechnet)
- also Nicht-Einbettung: 21,57 Mio (gerechnet)
- Aufwand je Token: 2 × 21,57 Mio = 43,1 MFLOP, plus Aufmerksamkeitsanteil bei
  400 Token Sequenz: 12 Schichten × 2 × 400 × 384 = 3,7 MMAC = 7,4 MFLOP
  → **rund 50 MFLOP je Token** (gerechnet)
- Gesamt: 387,2 Mio × 50 MFLOP = **1,94 × 10^16 FLOP**
- Durchsatz auf 2 geteilten Ampere-Kernen: **geschätzt 30 bis 100 GFLOP/s**.
  Die Bandbreite ist weit, weil dynamische int8-Quantisierung die Aktivierungen
  in fp32 belässt und der Gewinn bei kleinen Matrizen (384 Spalten) begrenzt ist.
- → **54 bis 180 Stunden**, Mittelwert bei 50 GFLOP/s: **108 Stunden**

**Rechnung 2, unabhängig, über den Token-Durchsatz:**

- e5-small auf 2 geteilten ARM-Kernen: **geschätzt 800 bis 2.000 Token je
  Sekunde**, hergeleitet aus dem Verhältnis zu MiniLM-L6 (halb so viele
  Schichten, gleiche Breite) auf gewöhnlicher CPU-Hardware, mit einem Abschlag
  für geteilte vCPU
- 387,2 Mio / 1.400 Token/s = 276.000 s = **77 Stunden**

**Beide Rechnungen landen bei Tagen, nicht bei Stunden.** Sie sind unabhängig
voneinander hergeleitet und weichen um weniger als den Faktor zwei ab. Das ist
für zwei Schätzungen dieser Art eine bemerkenswerte Übereinstimmung, und sie
macht das Ergebnis belastbarer als jede der beiden allein.

**Zum Vergleich: der gesamte bisherige Indexlauf mit OCR über dieselben 50.000
Dateien hat 10 h 14 min gedauert. Das volle Embedding kostet das Fünf- bis
Achtzehnfache davon.**

**Das ist der harte Punkt dieser Phase, und er steht nicht in der Roadmap.**
Kriterium 5 fragt nach Stabilität ("bleibt stabil"), und die Antwort darauf ist
ja. Die Frage, die niemand gestellt hat, ist die nach der Dauer, und dort lautet
die Antwort: ein Erstindex mit vollem Embedding läuft auf der Zielbox mehrere
Tage. Für eine App, deren Kernversprechen "Zero-Config, es läuft einfach los"
lautet, ist das eine Produktaussage und keine Fußnote.

### 3.6 Die Hebel, wenn es eng wird

Nach Wirkung geordnet. Die ersten drei wirken auf die Laufzeit, die letzten
vier auf den Speicher.

| Hebel | Wirkung auf die Laufzeit | Preis |
|---|---|---|
| **1. Nur die ersten N Token je Dokument einbetten** | linear und gewaltig. Bei 512 Token je Dokument: 50.068 × 512 = 25,6 Mio Token, das sind **6,6 Prozent** der vollen Menge → geschätzt **3,6 bis 12 Stunden**. Bei 1.024 Token: **7 bis 24 Stunden** | ein langes Dokument ist nur über seinen Anfang semantisch auffindbar. Für Behördenpost, Rechnungen und Ratsvorlagen ist das oft genau richtig, für ein Handbuch ist es falsch |
| **2. Statische Einbettungen statt Transformer** (`minishlab/potion-multilingual-128M`) | dramatisch. Statische Einbettungen sind Tabellensuche plus Mittelung: 387,2 Mio Token × 256 Additionen = 9,9 × 10^10 Operationen, dazu die Tokenisierung. Geschätzt **Minuten bis eine Stunde** für den ganzen Korpus | Qualität deutlich unter e5-small. Wie viel, ist **nicht belegt**; ich habe dafür keine deutsche Retrieval-Messung gefunden |
| **3. Embedding als nachgelagerte Spur** | ändert die Gesamtdauer nicht, aber die gefühlte: Volltext und OCR sind nach 10 Stunden fertig und nutzbar, die Semantik füllt sich über Tage nach | Deckungsgrad wird für zwei Spuren getrennt geführt, die Statusseite braucht eine zweite Zahl (ADM-01 berührt) |
| 4. Chargengröße 2 statt 8 | keine | Spitze der Aktivierungen sinkt von 150-300 MB auf 40-80 MB, Durchsatz sinkt leicht |
| 5. Sequenzlänge 256 statt 512 | leicht positiv | Aufmerksamkeitsmatrix geht quadratisch, Spitze sinkt um Faktor 4; mehr Chunks je Dokument |
| 6. `enable_cpu_mem_arena=False` beziehungsweise `arena_extend_strategy=kSameAsRequested` | leicht negativ | die onnxruntime-Arena gibt Speicher nicht an das Betriebssystem zurück, die Spitze wird sonst zur Dauerlast. Ob fastembed diese Sitzungsoptionen durchreicht, ist **zu prüfen** |
| 7. Modell nach Ruhe entladen | keine | `lazy_load=True` lädt erst beim ersten Gebrauch; ein Entladen nach Ruhe wäre Eigenbau |

**Zu Hebel 2, weil er in STACK.md nur als Notausgang für 2-GB-Boxen geführt
wird und durch diese Rechnung erheblich attraktiver wird**, hier die geprüften
Eckdaten (HuggingFace-API, 04.09.2026):

| Eigenschaft | Wert |
|---|---|
| Lizenz | **MIT** |
| `hidden_dim` | **256** (aus `config.json`) |
| `seq_length` | 1.000.000, also praktisch unbegrenzt: **kein 512-Token-Fenster, keine Chunkung nötig** |
| Tokenizer | `BAAI/bge-m3` |
| `onnx/model.onnx` | 512.365.657 Byte (fp32; als reine Tabelle int8-quantisierbar auf rund 128 MB) |
| `tokenizer.json` | 18.616.131 Byte |
| Downloads | 63.391 |
| Zuletzt geändert | 2026-04-07 |

Der Nebeneffekt ist bemerkenswert: ohne Kontextfenster entfällt die Chunkung
als Zwang. Man kann ein Dokument als **einen** Vektor führen, und dann sind es
50.068 Vektoren zu 256 Dimensionen statt 966.000 zu 384. Der brute-force-Scan
schrumpft von 371 MB auf 12,8 MB, und die ganze 250.000er-Diskussion löst sich
auf.

Der Preis ist Qualität, und zwar unbekannt viel. Deshalb steht das hier als
Option mit ehrlicher Lücke und nicht als Empfehlung.

### 3.7 Die drei billigen Messungen, die alle Schätzungen dieses Berichts ersetzen

Alle drei brauchen weder die Box 3.65.24.222 noch Nextcloud noch einen Korpus in
Nextcloud. Sie gehören in Welle 0 der Phase.

**Messung A, Zeichen je Token.** Den XLM-R-Tokenizer über ein Megabyte echten
deutschen Text aus `testdata/` laufen lassen, Zeichen durch Token teilen.
**Aufwand: fünf Zeilen, dreißig Sekunden.** Ersetzt die 3,5 aus 3.5 durch eine
Messung und korrigiert damit unmittelbar die Chunk-Anzahl, die Plattengröße und
die Laufzeitrechnung.

**Messung B, Token je Sekunde.** Das quantisierte Modell im arm64-Abbild laden,
200 Chunks zu 400 Token einbetten, Zeit stoppen. **Aufwand: zwanzig Zeilen,
fünf Minuten.** Ersetzt die Bandbreite "54 bis 180 Stunden" durch eine Zahl.
Diese Messung entscheidet, ob die Phase in ihrer heutigen Form durchführbar ist,
und sie sollte deshalb die **allererste** Aufgabe der Phase sein.

**Messung C, Scan-Latenz gegen Chunk-Anzahl.** Wie in 2.2 beschrieben.
**Aufwand: dreißig Zeilen, wenige Minuten.** Entscheidet über brute force
gegen Bit-Vektoren gegen usearch und damit über das Schema.

Zusammen unter einer Stunde Arbeit. Danach steht in diesem Bericht keine
geschätzte Zahl mehr an einer Stelle, an der eine Entscheidung hängt.

---

## Teil 4: Bytes je Dokument (Kriterium 4)

### 4.1 Die Eingangsgröße ist gemessen

**27.067 Textzeichen je Dokument** (1.355.205.169 / 50.068, aus
`docs/performance.md`, 04.09.2026, Volllauf).

Die Fußnote aus dem Bericht gilt und ist hier besonders wichtig: der Korpus ist
synthetisch, und *"ein echter Bestand mit demselben Byteumfang trägt mehr Text
und erzeugt einen größeren Index."* Alle folgenden Zahlen sind also eher eine
Untergrenze als eine Obergrenze.

### 4.2 Chunks je Dokument

Bei 3,5 Zeichen je Token (geschätzt, Messung A entscheidet):
27.067 / 3,5 = **7.733 Token je Dokument**.

| Chunkgröße | Überlappung | Effektiver Vorschub | Chunks je Dokument | bei 50.068 Dokumenten |
|---|---|---|---|---|
| 512 Token | 0 | 512 | 15,1 | 756.000 |
| 400 Token | 0 | 400 | 19,3 | **968.000** |
| 400 Token | 50 Token | 350 | 22,1 | 1.106.000 |
| 256 Token | 0 | 256 | 30,2 | 1.512.000 |
| 512 Token, **gekappt auf 2** | 0 | - | 2,0 | 100.136 |
| 512 Token, **gekappt auf 1** | 0 | - | 1,0 | 50.068 |

**Der Vergleich mit der Schwelle:** 250.000 Chunks entsprechen genau 5,0 Chunks
je Dokument bei 50.000 Dokumenten. Der gemessene Korpus trägt bei 400 Token je
Chunk aber 19,3. **Die Schwelle wird bei voller Chunkung um den Faktor 3,9
überschritten.** Sie ist damit nicht falsch berechnet, sondern sie beschreibt
ein Mengengerüst, das dieser Korpus nicht hat.

### 4.3 Bytes je Chunk und je Dokument

Zusammensetzung je Chunk:

- Vektordaten: Dimensionen × Byte je Komponente
- `vec0`-Verwaltung: **geschätzt 8 Byte** (rowid) plus Gültigkeitsbit
- Zeile in `chunks` mit Index auf `file_id`: **geschätzt 40 Byte**
  (chunk_id, file_id, ordinal, char_start, char_end plus B-Tree-Anteil)
- → Overhead zusammen **geschätzt 48 Byte je Chunk**

| Variante | Byte je Vektor | + Overhead | je Chunk | je Dokument bei 19,3 Chunks | **bei 50.068 Dokumenten** |
|---|---|---|---|---|---|
| fp32, 384 Dim | 1.536 | 48 | 1.584 | 30,6 kB | **1,53 GB** |
| **int8, 384 Dim** | 384 | 48 | **432** | **8,34 kB** | **418 MB** |
| bit, 384 Dim | 48 | 48 | 96 | 1,85 kB | 92,8 MB |
| int8, 256 Dim (potion) | 256 | 48 | 304 | 5,87 kB | 294 MB |

Und die gekappten Varianten, weil sie im Discuss die eigentlichen Kandidaten sind:

| Variante | je Dokument | bei 50.068 Dokumenten |
|---|---|---|
| int8 384, gekappt auf 2 Chunks | 864 Byte | **43,3 MB** |
| int8 384, gekappt auf 1 Chunk | 432 Byte | **21,6 MB** |
| int8 256 (potion), 1 Vektor je Dokument | 304 Byte | **15,2 MB** |
| bit 384, gekappt auf 2 Chunks | 192 Byte | 9,6 MB |

**Auf die SQLite-Füllrate der Seiten sind etwa 10 Prozent aufzuschlagen**
(geschätzt; `vec0` legt Vektoren in Blöcken zu üblicherweise 1.024 Zeilen ab, die
Verwaltung amortisiert sich also gut, die Seitenfüllung bleibt aber unter 100
Prozent).

### 4.4 Was das für die Plattengröße bedeutet

Der Vergleichswert ist gemessen: der Tantivy-Index nach dem Volllauf wiegt
**761.374.910 Byte**, also 726 MiB für 50.068 Dokumente.

| Variante | Vektoren | Zuwachs gegenüber dem heutigen Index |
|---|---|---|
| fp32, volle Chunkung | 1,53 GB | **+206 Prozent** |
| int8, volle Chunkung | 418 MB | **+55 Prozent** |
| int8, gekappt auf 2 Chunks | 43 MB | +5,7 Prozent |
| bit, volle Chunkung | 93 MB | +12 Prozent |
| potion, 1 Vektor je Dokument | 15 MB | +2,0 Prozent |

**Die Plattengröße ist in keiner Variante das Problem.** Selbst fp32 mit voller
Chunkung passt neben einem 20-GB-Korpus auf ein 50-GB-Volume. Kriterium 4
verlangt die Kennzahl, und die Kennzahl lautet für die naheliegendste Variante:

> **8,34 kB je Dokument bei int8, 384 Dimensionen und voller Chunkung**
> (27.067 Zeichen je Dokument gemessen, 3,5 Zeichen je Token geschätzt,
> 400 Token je Chunk ohne Überlappung, 48 Byte Overhead je Chunk geschätzt)

Was **wohl** das Problem ist, ist nicht der Platz, sondern was auf diesem Platz
je Abfrage gelesen werden muss: 418 MB Vektordaten bei jedem vollen
brute-force-Scan, bis zu dreimal je Nutzersuche (`MAX_ROUNDS = 3`). Das ist die
Zahl, die Messung C beantworten muss.

---

## Runtime State Inventory

Phase 6 ist keine Umbenennung und keine Migration, aber sie berührt bestehenden
Laufzeitzustand. Deshalb die Kategorien, jede ausdrücklich beantwortet:

| Kategorie | Befund | Nötige Handlung |
|---|---|---|
| Gespeicherte Daten | Der bestehende Index in `$APP_PERSISTENT_STORAGE` (Tantivy-Verzeichnis plus `state.db`). Ein Schema-Sprung von `"1"` auf `"2"` betrifft jede vorhandene Installation | Entscheidung: fügt Phase 6 nur Tabellen hinzu (dann genügt das `IF NOT EXISTS` in `schema.sql`, kein Reindex), oder ändert sie Bestehendes? Nach heutigem Stand: **nur Hinzufügen**, also kein Reindex des Volltextes nötig. Das ist eine wertvolle Eigenschaft und sollte bewusst erhalten bleiben |
| Laufende Dienstkonfiguration | keine. Findling hat keine externe Dienstkonfiguration außerhalb des Repos | keine |
| Vom Betriebssystem registrierter Zustand | keine. Die App läuft ausschließlich als Container über AppAPI/HaRP | keine |
| Geheimnisse und Umgebungsvariablen | Neu: `HF_HUB_OFFLINE=1` und ein fester `cache_dir` im Dockerfile. Keine Geheimnisse. Die neuen Abhängigkeiten `huggingface-hub` und `requests` bringen Netzwerkfähigkeit in einen Container, der offline bleiben soll | Offline-Test in der CI (Netzwerk im Testschritt abklemmen) |
| Bauartefakte | Das Abbild wächst um Modell (rund 118 MB bei gelungener Quantisierung), Tokenizer (rund 22 MB) und die Räder onnxruntime (20,8 MB), fastembed, sqlite-vec, semantic-text-splitter. **Geschätzt 200 bis 260 MB Zuwachs.** performance.md warnt ausdrücklich: die Box hat nur 40 GB Systemplatte, und Abbilder liegen seit Docker 29 unter `/var/lib/containerd`, nicht im `data-root` | Abbildgröße nach dem Bau prüfen; die containerd-Korrektur aus 05-14 gilt weiter |

---

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---|---|---|---|
| Text in Token-Fenster zerlegen | eigener Splitter über Zeichenzahl | `semantic-text-splitter` 0.32.0 gegen den echten Tokenizer | Zeichenzahl trifft das 512-Token-Fenster nicht; zu lange Chunks werden still abgeschnitten und verlieren Inhalt, ohne dass etwas auffällt |
| Vektorähnlichkeit rechnen | Schleife in Python oder numpy über alle Vektoren | `vec0`-KNN in C | eine numpy-Schleife über 966.000 Vektoren zieht den ganzen Bestand als Array in den Prozessspeicher, und genau das ist die Zeile, die die 2-GB-Grenze reißt |
| Modell int8 quantisieren | eigene Skalierung | `onnxruntime.quantization.quantize_dynamic` | Kalibrierung, Achsenwahl und Operatorabdeckung sind je Operator verschieden; ein Eigenbau trifft die Einbettungstabelle mit hoher Wahrscheinlichkeit nicht |
| Ranglisten verschmelzen | Score-Normalisierung von BM25 gegen Cosinus | RRF | BM25-Werte sind korpusabhängig und unbeschränkt, Cosinus liegt in [-1, 1]. Jede Normalisierung braucht Kalibrierung je Bestand und driftet mit ihm. RRF ignoriert Werte und nutzt nur Ränge |
| Rechteprüfung im Vektorzweig | eine eigene Sichtbarkeitsprüfung für Vektortreffer | `Store.prefilter_visible` plus PHP-Recheck, unverändert | PROJECT.md führt "eigenes Rechtemodell in Python" ausdrücklich unter Out of Scope: *"kein zweites, driftendes Modell"* |

---

## Common Pitfalls

### Fallstrick 1: Der Vektorzweig als zweite Route

**Was schiefgeht:** eine eigene `/search_semantic`-Route oder eine Verschmelzung
auf der PHP-Seite.
**Warum es passiert:** es ist der kürzere Weg zum ersten funktionierenden
Ergebnis.
**Folge:** Kriterium 2 hängt an Disziplin statt an Struktur, und der
Paritätstest aus Phase 5 wird für den Vektorzweig blind, weil er die andere
Route testet.
**Vermeidung:** Verschmelzung ausschließlich innerhalb von
`index/search.py::candidates()`, oberhalb des `prefilter_visible`-Aufrufs.
**Frühwarnzeichen:** eine neue Route in `api/`, oder ein zweiter Aufruf von
`prefilter_visible` an einer dritten Stelle.

### Fallstrick 2: Die Einbettungstabelle bleibt fp32

**Was schiefgeht:** `quantize_dynamic` quantisiert nur `MatMul`, nicht `Gather`.
**Warum es passiert:** 81,7 Prozent der Parameter dieses Modells stecken in der
Einbettungstabelle, und das sieht man dem Aufruf nicht an.
**Folge:** 266 MB mehr im Abbild und dauerhaft im Arbeitsspeicher, ohne dass
irgendetwas fehlschlägt.
**Vermeidung:** Größenprüfung im Dockerfile, Abbruch über etwa 130 MB.
**Frühwarnzeichen:** die quantisierte Datei wiegt rund 390 MB statt rund 118 MB.

### Fallstrick 3: Die E5-Präfixe fehlen

**Was schiefgeht:** `"query: "` und `"passage: "` werden nicht gesetzt, weil
fastembed sie nur für eingebaute Modelle automatisch ergänzt und das Modell hier
selbst registriert wird.
**Folge:** die Retrieval-Qualität fällt messbar ab, ohne dass etwas
fehlschlägt. STACK.md nennt es "die häufigste stille Fehlerquelle in diesem
Baustein".
**Vermeidung:** eigener Test, der dieselbe Anfrage mit und ohne Präfix gegen
dasselbe Dokument fährt und einen Rangunterschied verlangt.

### Fallstrick 4: Der Vektorausfall macht die Suche leer statt lexikalisch

**Was schiefgeht:** der Vektorfehler landet im `except Exception` von
`one_round` (api/search.py:199), und das antwortet mit einer **leeren** Runde.
**Folge:** Kriterium 3 ist verletzt: fehlt das Modell, findet die Suche gar
nichts mehr, statt Volltext zu liefern.
**Vermeidung:** eigener, engerer `try/except` um den Vektorabruf, der eine leere
Vektorliste liefert.
**Frühwarnzeichen:** ein Test "Modelldatei umbenennen, suchen" fehlt in der
Abnahme.

### Fallstrick 5: Chunk-Dubletten nach Wiederzustellung

**Was schiefgeht:** die Vektoren werden eingefügt, ohne vorher die alten Chunks
derselben `file_id` zu löschen.
**Warum es passiert:** `IndexBatchWriter.add()` löscht heute selbst (writer.py:224),
das Vektor-Pendant muss dasselbe tun und tut es nicht von allein.
**Folge:** eine Charge, die nach dem Commit und vor der Quittierung abbricht,
kommt erneut (writer.py, Kopfkommentar) und verdoppelt die Chunks. Der Bestand
bläht sich still auf und die Rangliste verzerrt sich.
**Vermeidung:** `DELETE FROM chunks WHERE file_id = ?` plus Löschung der
zugehörigen `vec0`-Zeilen als erste Handlung jedes Schreibvorgangs.

### Fallstrick 6: Der Chunk-auf-Dokument-Schritt fehlt

**Was schiefgeht:** RRF wird auf Chunk-Ränge angewendet, ohne vorher auf
Dokumente zu aggregieren.
**Folge:** ein langes Dokument mit zwanzig mittelmäßigen Chunks schlägt ein
kurzes mit einem perfekten Chunk, und das Ranking bevorzugt systematisch Länge.
**Vermeidung:** die Aggregationsregel wird vor der Implementierung festgelegt
(siehe Discuss-Frage 6).

### Fallstrick 7: Der rein semantische Treffer hat kein Snippet

Siehe Abschnitt 1.3, Falle C. Vermeidung: `char_start` und `char_end` in der
`chunks`-Tabelle, Ausschnitt aus dem gespeicherten `body_de` schneiden.

---

## Package Legitimacy Audit

slopcheck stand lokal zur Verfügung und ist gelaufen (`slopcheck install
--ecosystem pypi ...`, 04.09.2026). Ergebnis der Prüfung: **5 gescannt,
5 OK**. Der anschließende Installationsversuch von slopcheck brach ab, weil
`pip` in dieser Windows-Umgebung nicht im Pfad liegt; das betrifft die
Installation, nicht die Prüfung.

| Paket | Registry | Fassung | Veröffentlicht | Lizenz | aarch64 | slopcheck | Verdikt |
|---|---|---|---|---|---|---|---|
| `sqlite-vec` | PyPI | 0.1.9 | 2026-03-31 | Apache-2.0 | ja, `manylinux_2_17_aarch64`, `py3-none` | OK | freigegeben, **exakt pinnen**; Wartungsrisiko siehe 2.1 |
| `fastembed` | PyPI | 0.8.0 | 2026-03-23 | Apache-2.0 | reines Python | OK | freigegeben |
| `onnxruntime` | PyPI | 1.29.0 | 2026-08-17 | MIT | ja, `cp313 manylinux_2_28_aarch64`, 20,8 MB | OK | freigegeben |
| `usearch` | PyPI | 2.26.2 | 2026-08-31 | Apache-2.0 | ja, `cp313 manylinux_2_28_aarch64` | OK | nur Ausweichpfad, nicht im Standardweg |
| `semantic-text-splitter` | PyPI | 0.32.0 | 2026-06-16 | MIT | ja, `cp310-abi3 manylinux_2_28_aarch64` | OK | freigegeben |

**Entfernt wegen [SLOP]:** keine.
**Als [SUS] markiert:** keine.

Herkunft der Paketnamen: alle fünf stammen aus `research/STACK.md` vom
15.08.2026, das sie seinerzeit aus der jeweiligen offiziellen Dokumentation
belegt hat. Alle fünf wurden in dieser Sitzung gegen die PyPI-API auf Existenz,
Fassung, Lizenz und Radplattform gegengeprüft. `sqlite-vec` zusätzlich gegen die
GitHub-API.

**Modelle** (keine PyPI-Pakete, deshalb separat):

| Modell | Lizenz | Belegt über | Verdikt |
|---|---|---|---|
| `intfloat/multilingual-e5-small` | MIT | HF-API, `cardData.license`, 12,2 Mio Downloads | freigegeben |
| `minishlab/potion-multilingual-128M` | MIT | HF-API, 63.391 Downloads | Option, siehe Hebel 2 |
| `Xenova/multilingual-e5-small` | **kein Lizenzfeld** | STACK.md, 15.08.2026 | **nicht verwenden**, Lizenzunschärfe in einem verteilten AGPL-Release |
| `jinaai/jina-embeddings-v3` | **CC BY-NC** | STACK.md, 15.08.2026 | **ausgeschlossen**, nicht kommerziell verteilbar |

---

## Environment Availability

Geprüft wurde ausschließlich auf der Entwicklungsmaschine. **Die Box
3.65.24.222 wurde weder gelesen noch beschrieben**, wie angewiesen.

| Abhängigkeit | Gebraucht für | Vorhanden | Fassung | Ausweich |
|---|---|---|---|---|
| `uv` | Python-Arbeit lokal | ja | 0.11.7 | keiner nötig |
| `slopcheck` | Paketprüfung | ja | gelaufen, 5 OK | Kennzeichnung als ASSUMED |
| globales `python3`/`pip3` | - | **nein** (bekannter Defekt, Memory `reference_python_global_kaputt_uv.md`) | - | `uv` |
| aarch64-Maschine für Messungen A/B/C | die drei Messungen aus 3.7 | **fehlt zum jetzigen Zeitpunkt** | - | die arm64-Läufer aus `docker.yml` bauen laut 05-CONTEXT.md nativ; oder die AWS-Box nach Abschluss des laufenden Volllaufs |
| AWS-Box m7g.large 3.65.24.222 | - | **gesperrt bis zum Abschluss des ARM-Volllaufs von 05-21** | - | - |

**Fehlende Abhängigkeit ohne Ausweich:** keine.
**Fehlende Abhängigkeit mit Ausweich:** eine aarch64-Maschine für die
Vormessungen. Der Ausweich über die CI-Läufer ist tragfähig und kostet nichts;
er misst allerdings auf anderer ARM-Hardware als der Zielbox, was für Messung C
(Latenz) eine Einschränkung ist und für Messung A (Zeichen je Token) keine.

---

## Security Domain

| ASVS-Kategorie | Betroffen | Standardkontrolle in diesem Kontext |
|---|---|---|
| V2 Authentifizierung | nein | unverändert: Identität ausschließlich aus dem signierten AppAPI-Header (`api/search.py:219`) |
| V3 Sitzungsverwaltung | nein | keine Sitzungen im Container |
| V4 Zugriffskontrolle | **ja, zentral** | zwei Stufen unverändert: `prefilter_visible` als Beschleuniger, `getFirstNodeById()` als Grenze. Der Vektorzweig darf keine dritte Stufe einführen |
| V5 Eingabevalidierung | ja | `SearchRequest` mit `extra="forbid"`; neue Konfigurationswerte (Chunkgröße, RRF-k, Tiefe) brauchen dieselben Bereichsprüfungen wie `SEARCH_OFFSET_MAX` heute |
| V6 Kryptographie | nein | keine neue Kryptographie |

| Bedrohung | STRIDE | Minderung |
|---|---|---|
| Zähl-Orakel über den Offset (T-02-93) | Information Disclosure | Offsets zählen erlaubte Kandidaten, nie rohe Treffer. **Muss die RRF-Verschmelzung überleben** (Falle B in 1.3) |
| Confused Deputy über die Snippet-Route | Elevation of Privilege | `snippets_for()` ruft `prefilter_visible` als erste Handlung (index/search.py:299). Bleibt unverändert; eine Snippet-Erzeugung aus Chunk-Offsets muss **hinter** dieser Prüfung liegen |
| Vektortreffer als Existenzaussage | Information Disclosure | `Candidate` trägt weiterhin nur `fileId`, `score`, `mtime`. Eine Herkunftsmarkierung "semantisch" wäre eine neue Aussage über ein noch nicht bestätigtes Dokument (siehe Discuss-Frage 8) |
| Verwaiste Vektoren nach Löschung oder Unshare | Information Disclosure | Löschweg aus 1.4 vollständig verdrahten. Die `acl`-Zeilen bleiben die Grenze, aber verwaiste Vektoren kosten Rechenzeit und verzerren die Rangliste |
| Denial of Service über die Scan-Tiefe | Denial of Service | `SEARCH_SCAN_MAX = 10.000` deckelt heute die lexikalische Seite. Die Vektorseite braucht einen eigenen Deckel, sonst ist ein voller Scan über 966.000 Chunks bei jeder Anfrage die Standardlast |
| Netzwerkfähigkeit durch neue Abhängigkeiten | Information Disclosure | `huggingface-hub` und `requests` kommen mit fastembed. `HF_HUB_OFFLINE=1` plus ein CI-Test ohne Netzwerkzugang |

---

## State of the Art

| Bisherige Annahme (Stand 15.08.2026) | Stand heute (04.09.2026) | Wirkung |
|---|---|---|
| sqlite-vec: stabil v0.1.9, danach Alphas | unverändert, **aber seit 18.05.2026 kein Commit mehr** | Wartungsrisiko höher als angenommen; Ausweichpfad wird wichtiger |
| onnxruntime 1.28.0 vorgesehen | 1.29.0 (17.08.2026) verfügbar und mit fastembed verträglich | Pin nachziehen |
| usearch 2.26.0 | 2.26.2 (31.08.2026) | aktiv gewartet, Kontrast zu sqlite-vec |
| int8-Modellquantisierung: Qualitätsverlust unbekannt | für **Deutsch** belegt: MIRACL de NDCG@10 0,75862 gegen 0,75992 | Risiko praktisch entfallen |
| 250.000 Chunks als Schwelle | Der gemessene Korpus erzeugt bei voller Chunkung **968.000** | Die Schwellendiskussion wird zur Chunkungsdiskussion |
| RAM ist der harte Punkt | Gemessene 428,6 MB gegen 2,0 GB Grenze; Vektorzweig braucht 180 bis 580 MB | **Der harte Punkt ist die Laufzeit, nicht der Speicher** |
| potion-multilingual als Notausgang für 2-GB-Boxen | 256 Dimensionen, **kein Kontextfenster**, Einbettung praktisch rechenfrei | Wird durch das Laufzeitproblem zu einem ernsthaften Hauptkandidaten |

**Überholt und nicht mehr zu verwenden:**
- `intfloat/.../model_qint8_avx512_vnni.onnx` auf ARM (Dateiname in dieser Sitzung bestätigt)
- `hnswlib` (letztes Release 12/2023, keine aarch64- und keine cp313-Räder, aus STACK.md)
- `jinaai/jina-embeddings-v3` (CC BY-NC)

---

## Assumptions Log

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---|---|---|
| A1 | 3,5 Zeichen je Token für Deutsch mit dem XLM-R-Tokenizer | 3.5, 4.2 | Chunk-Anzahl, Plattengröße und Laufzeit skalieren alle linear damit. **Messung A entscheidet in dreißig Sekunden** |
| A2 | 30 bis 100 GFLOP/s effektiv auf 2 geteilten Ampere-Kernen | 3.5 | Die Aussage "54 bis 180 Stunden" steht und fällt damit. **Messung B entscheidet in fünf Minuten** |
| A3 | 800 bis 2.000 Token/s als unabhängige Gegenrechnung | 3.5 | dito, ebenfalls Messung B |
| A4 | 48 Byte Overhead je Chunk (vec0-rowid plus `chunks`-Zeile mit Index) | 4.3 | bei int8 rund 11 Prozent der Gesamtgröße; bei Bit-Vektoren 50 Prozent. Nur dort relevant |
| A5 | Aktivierungsspitze 150 bis 300 MB bei Charge 8 zu 512 Token | 3.2 | Bei einem Faktor 3 daneben wäre die erwartete Spitze 1,5 GB statt 879 MB und die Grenze in Sicht |
| A6 | Modellgewichte belegen 120 bis 160 MB RSS bei 118 MB Datei | 3.2 | moderat, Bandbreite bereits weit gefasst |
| A7 | Tokenizer belegt 60 bis 120 MB RSS bei 16,3 MiB Datei | 3.2 | moderat |
| A8 | `vec0` unterstützt Metadaten- und Partitionsspalten | 2.1 | aus STACK.md übernommen, in dieser Sitzung nicht gegengeprüft. Nur relevant, falls die ACL-Vorauswahl in die Vektorabfrage gezogen werden soll, was nach 1.3 nicht empfohlen wird |
| A9 | `quantize_dynamic` erfasst die Einbettungstabelle nicht zwingend | 2.4, Fallstrick 2 | Die Größenprüfung im Dockerfile fängt beide Fälle ab, ob die Annahme stimmt oder nicht |
| A10 | Die ARM-Spitze liegt in derselben Größenordnung wie die gemessenen 428,6 MB auf x86 | 3.1, 3.3 | Der ARM-Volllauf läuft und liefert die Zahl morgen. Bis dahin steht jede Speicherrechnung dieses Berichts unter diesem Vorbehalt |
| A11 | fastembed reicht onnxruntime-Sitzungsoptionen durch (Arena-Verhalten) | 3.6, Hebel 6 | Falls nicht, muss onnxruntime direkt angesteuert werden statt über fastembed. Das ist Aufwand, kein Blocker |
| A12 | `vec0`-KNN läuft unter `PRAGMA query_only = 1` | 1.2 | Falls nicht, muss die Leseseitenarchitektur geändert werden. **Fünf-Minuten-Probe, gehört in Welle 0** |
| A13 | Die CPython-Übersetzung im Abbild erlaubt ladbare SQLite-Erweiterungen | 1.2 | Falls nicht, braucht das Abbild eine eigene Python-Übersetzung. Das wäre teuer. **Ein-Zeilen-Probe, gehört in Welle 0** |

---

## Quellen

### Primär, HIGH-Konfidenz

**Aus dieser Codebasis** (gelesen am 04.09.2026):
- `backend/src/findling/index/search.py` , `candidates()` (Z. 92), `snippets_for()` (Z. 277), Kopfkommentar zur Offset-Semantik (Z. 15-20)
- `backend/src/findling/store/repo.py` , `prefilter_visible()` (Z. 922), `_connect()` (Z. 427), `SCHEMA_VERSION` (Z. 50), `ACL_ANY_USER` (Z. 99)
- `backend/src/findling/store/schema.sql` , vollständig, inklusive des Phase-6-Kommentars an der `meta`-Tabelle
- `backend/src/findling/api/search.py` , `one_round()` (Z. 174), `Candidate` (Z. 96), Degradierverhalten (Z. 198-203)
- `backend/src/findling/index/writer.py` , `add()` (Z. 210), `drop_document()` (Z. 251), `flush()` (Z. 301)
- `backend/src/findling/worker/poller.py` , `_record_of()` (Z. 1243), `_collect()` (Z. 939), `_record_verdicts()` (Z. 982)
- `backend/src/findling/config.py` , `INDEX_WORKERS` (Z. 57), `MAX_TEXT_CHARS` (Z. 117), `WRITER_HEAP_BYTES` (Z. 132), `SEARCH_SCAN_MAX` (Z. 166)
- `php/lib/Search/Provider.php` , `BUDGET_NANOSECONDS` (Z. 57), `MAX_ROUNDS` (Z. 65), `getFirstNodeById()` (Z. 342)
- `docs/performance.md` , sämtliche gemessenen Zahlen in Teil 3 und 4, Stand 04.09.2026
- `.planning/research/STACK.md` , Abschnitte 2 und 4, Stand 15.08.2026

**Externe Abfragen** (alle am 04.09.2026, jeweils Einzelabfragen, keine Bursts):
- GitHub REST API, `repos/asg017/sqlite-vec/releases`, `/issues/25`, Repo-Metadaten , Ratenlimit unauthentifiziert 60 Anfragen je Stunde, verbraucht: 3
- PyPI JSON-API und Simple-Index , `sqlite-vec`, `usearch`, `fastembed`, `onnxruntime`, `semantic-text-splitter` , verbraucht: 6, sequenziell
- HuggingFace API , `intfloat/multilingual-e5-small` (zweimal, einmal mit `?blobs=true`), `minishlab/potion-multilingual-128M`, zwei Rohdateien , verbraucht: 5, sequenziell
- Elasticsearch-Referenz, Reciprocal Rank Fusion , Formel, `rank_constant`-Vorgabe 60, `rank_window_size`, Gewichtungsverhalten
- Modellkarte `elastic/multilingual-e5-small-optimized` , MIRACL- und BEIR-Zahlen fp32 gegen int8

### Sekundär, MEDIUM-Konfidenz
- Alex Garcia, Ankündigungsartikel sqlite-vec v0.1.0 , "brute-force only", ">1M mit hohen Dimensionen"
- sqlite-vec Vorgang #165 , OFFSET-Kosten bei KNN
- Elastic Search Labs, Artikel zur Bewertung skalarer Quantisierung , 1,05 Prozent durchschnittlicher relativer NDCG@10-Rückgang bei int8-Vektoren

### Tertiär, LOW-Konfidenz, zur Validierung markiert
- Die Behauptung, `vec0` unterstütze Partitions- und Metadatenspalten (A8): aus STACK.md, in dieser Sitzung nicht gegengeprüft
- Die Angabe zur Verfahrensart von usearch (HNSW): allgemein bekannt, in dieser Sitzung nicht gegen die Projektdokumentation geprüft

---

## Offene Fragen für den Discuss

Das ist der Zweck dieser Vorarbeit. Neun Fragen, jede mit Optionen und meiner
Empfehlung samt Begründung. **Keine davon ist entschieden.**

---

### Frage 1: Wie viel Text je Dokument bekommt einen Vektor?

**Das ist die Frage, an der die ganze Phase hängt.** Sie entscheidet über
Laufzeit, Chunk-Anzahl, Speicherverfahren und die Kennzahl aus Kriterium 4
gleichzeitig.

| Option | Chunks bei 50.068 Dok. | Laufzeit (geschätzt, Messung B ersetzt sie) | Platte | Was der Nutzer bekommt |
|---|---|---|---|---|
| **A: alles** | 968.000 | 54 bis 180 h | 418 MB | jede Stelle jedes Dokuments semantisch auffindbar |
| **B: erste 1.024 Token** (2 Chunks) | 100.136 | 7 bis 24 h | 43 MB | Anfang jedes Dokuments auffindbar |
| **C: erste 512 Token** (1 Chunk) | 50.068 | 3,6 bis 12 h | 22 MB | dito, knapper |
| **D: alles, aber statisch** (potion) | 50.068 (1 je Dok.) | Minuten bis 1 h | 15 MB | ganzes Dokument abgedeckt, aber gröber |

**Meine Empfehlung: B, erste 1.024 Token je Dokument, mit einem Schalter für
den Deckel.**

Begründung: Option A verdoppelt bis verachtzehnfacht die Dauer eines Erstindex,
der heute schon zehn Stunden braucht. Für eine App, deren Kernversprechen
"Installieren und es läuft" lautet, ist ein Erstindex von mehreren Tagen ein
Produktproblem, kein technisches. Option C ist zu knapp: 512 Token sind bei 3,5
Zeichen je Token rund 1.800 Zeichen, also weniger als eine Seite, und viele
Dokumente haben auf der ersten halben Seite nur Briefkopf und Betreff. Option B
liegt bei rund 3.600 Zeichen, also gut einer Seite, und trifft damit den Fall,
für den die Zielgruppe diese App installiert: Behördenpost, Rechnungen,
Protokolle, Ratsvorlagen. Der Deckel gehört als Einstellung nach außen, damit
ein Betreiber mit Zeit und Hardware auf A hochdrehen kann, ohne dass die Vorgabe
kleine Boxen bestraft.

Der Preis ist ehrlich zu benennen und gehört in den Store-Text: **die
semantische Suche deckt den Anfang jedes Dokuments ab, nicht seinen ganzen
Inhalt.** Die Volltextsuche deckt weiterhin alles ab. Das ist eine verständliche
Aussage und deutlich besser als eine unausgesprochene Lücke.

**Vorbedingung:** Messung B (Token je Sekunde) fährt vor dieser Entscheidung.
Wenn sie 3.000 Token/s statt 1.400 zeigt, wandert Option A wieder in Reichweite.

---

### Frage 2: e5-small oder potion-multilingual als Vorgabe?

| Option | Für | Gegen |
|---|---|---|
| **e5-small int8** | auf Retrieval trainiert, Qualität auf Deutsch belegt (MIRACL de 0,759), int8-Verlust belegt nahe null, MIT | Transformer-Inferenz, damit das gesamte Laufzeitproblem aus Frage 1 |
| **potion-multilingual-128M** | praktisch rechenfrei, kein Kontextfenster, ganzes Dokument in einem Vektor, MIT | Qualität deutlich niedriger, **wie viel ist nicht belegt**; 512 MB fp32-Tabelle (int8 rund 128 MB) als Dauerlast |
| **beides, umschaltbar** | Betreiber wählt | zwei Wege zu testen, zwei Vektorschemata (384 gegen 256 Dimensionen), Modellwechsel erzwingt Reindex |

**Meine Empfehlung: e5-small als Vorgabe, potion nicht in v1.0.**

Begründung: die Qualitätslücke von potion ist unbekannt, und "unbekannt" ist in
einem Erstrelease ein schlechter Tausch gegen eine Laufzeit, die sich mit
Frage 1 ohnehin auf sieben bis vierundzwanzig Stunden drücken lässt. Der
Vorbehalt: falls Messung B am oberen Ende landet und selbst Option C aus Frage 1
noch über einen Tag braucht, kehrt sich das um. Dann ist potion nicht der
Notausgang, sondern die einzige Variante, die das Zero-Config-Versprechen hält.
**Diese Entscheidung sollte deshalb erst nach Messung B fallen.**

---

### Frage 3: brute force, Bit-Vektoren oder usearch?

| Option | Für | Gegen |
|---|---|---|
| **int8 brute force in sqlite-vec** | eine Datei, ein Backup, eine Konsistenzquelle, exakte Ergebnisse | 418 MB je Scan bei voller Chunkung; sqlite-vec seit 18.05.2026 ohne Commit |
| **Bit-Vektoren in sqlite-vec** | Faktor 8 bis 20 schneller und kleiner, gleiche Datei, gleiche Bibliothek | Qualitätsverlust **nicht belegt**; ohne Nachrangierung riskant |
| **Bit grob plus int8 fein** | rettet den Großteil der Qualität, gewinnt den Großteil der Zeit | beide Fassungen speichern, also mehr Platz statt weniger |
| **usearch HNSW** | logarithmisch statt linear, aktiv gewartet (31.08.2026) | zweiter Persistenzpfad, eigene ID-Verwaltung, Crash-Sicherheit selbst zu bauen, Löschungen als Grabsteine |

**Meine Empfehlung: int8 brute force in sqlite-vec, unter der Bedingung, dass
Frage 1 auf B oder C fällt.** Bei 100.136 Chunks sind das 38 MB je Scan; das ist
weit unter der Schwelle, um die dieser Absatz überhaupt geführt wird, und die
gesamte Diskussion löst sich auf. Bit-Vektoren und usearch bleiben dokumentierte
Ausweichpfade, wie Kriterium 4 es verlangt, und werden nicht gebaut.

Fällt Frage 1 dagegen auf A, dann sind es 371 MB je Scan bei bis zu drei Runden
je Suche, und dann entscheidet Messung C.

**Das Wartungsrisiko von sqlite-vec ist davon unabhängig und gehört separat
beantwortet** (siehe Frage 9).

---

### Frage 4: Wie tief geht die RRF-Verschmelzung, und mit welchen Parametern?

Festzulegen sind vier Werte:

| Parameter | Vorschlag | Begründung |
|---|---|---|
| `k` (rank_constant) | **60** | Vorgabe von Elasticsearch, belegt; kein Grund, davon abzuweichen, bevor etwas gemessen ist |
| Fenstertiefe je Quelle | **100** | tief genug, dass ein semantisch starkes Dokument seinen lexikalischen Rang 300 überleben kann, flach genug für das 2,5-Sekunden-Budget |
| Gewicht lexikalisch | **1,0** | |
| Gewicht semantisch | **1,0**, per Einstellung senkbar | ein Admin muss die Semantik dämpfen können, ohne sie abzuschalten. Elasticsearch bietet gar keine Gewichte; wir bauen selbst und können es besser machen |

**Meine Empfehlung: diese vier Werte so übernehmen und als Einstellungen nach
außen führen, aber nicht auf der Admin-Seite bewerben.** Sie sind Stellschrauben
für den Fehlerfall, keine Konfigurationsaufgabe. Das Zero-Config-Versprechen
verlangt, dass niemand sie anfassen muss.

Ein Vorbehalt: die Fenstertiefe 100 ist geschätzt. Sie interagiert mit
`SEARCH_SCAN_MAX = 10.000` und mit der Selektivität des Vorfilters, für die
`index/search.py` einen gemessenen Extremfall nennt (31 von 400 Kandidaten
überlebten in der Phase-2-Untersuchung). Bei dieser Selektivität liefert ein
Fenster von 100 je Quelle unter zehn erlaubte Treffer. Das ist zu prüfen.

---

### Frage 5: Wie entsteht das Snippet für einen rein semantischen Treffer?

| Option | Für | Gegen |
|---|---|---|
| **A: gar nicht** | nichts zu bauen, der Code fängt es bereits ab | der Nutzer sieht einen Treffer ohne jede Textvorschau, und bei semantischen Treffern ist das der Normalfall |
| **B: Ausschnitt aus `char_start`/`char_end` des besten Chunks** | zeigt genau die Stelle, die semantisch gepasst hat | zwei Zahlen mehr je Chunk, ein zweiter Ausschnittsweg neben dem `SnippetGenerator` |
| **C: Anfang des Dokuments** | trivial | sagt nichts darüber, warum das Dokument getroffen hat |

**Meine Empfehlung: B.** Die zwei Zahlen kosten 8 Byte je Chunk, also unter zwei
Prozent der Chunk-Größe bei int8, und sie sind die einzige Möglichkeit, dem
Nutzer zu zeigen, *warum* ein Dokument ohne das gesuchte Wort in der Liste steht.
Ohne diese Erklärung wirkt ein semantischer Treffer wie ein Fehler. Wichtig: der
Ausschnitt entsteht in `snippets_for()`, also **nach** dem `prefilter_visible`
und nach dem PHP-Recheck, wie jeder andere Ausschnitt auch.

---

### Frage 6: Wie werden Chunk-Ränge auf Dokumente aggregiert?

Ohne diese Regel ist RRF nicht implementierbar (siehe 2.5).

| Option | Wirkung |
|---|---|
| **Maximum**: bester Chunk bestimmt den Dokumentrang | einfach, robust, längenneutral |
| **Summe der besten n** | belohnt durchgängige Themennähe, bevorzugt lange Dokumente |
| **Anzahl in den Top-k** | robust gegen Ausreißer, grob |

**Meine Empfehlung: Maximum.** Zwei Gründe. Erstens ist es das einzige
Verfahren, das keine systematische Längenverzerrung einführt, und bei einer
gekappten Chunkung nach Frage 1 hätten Dokumente ohnehin sehr ähnliche
Chunk-Zahlen, womit die anderen Verfahren wenig zusätzliche Information
liefern. Zweitens macht es die Rückverfolgung trivial: der Chunk, der den Rang
bestimmt hat, ist genau der, dessen Ausschnitt Frage 5 anzeigt.

---

### Frage 7: Wann läuft das Embedding, während des Erstindex oder danach?

| Option | Für | Gegen |
|---|---|---|
| **A: im selben Durchgang** | ein Lauf, ein Fortschrittsbalken, ein Deckungsgrad | der Erstindex dauert um die Embedding-Zeit länger; nichts ist nutzbar, bevor alles fertig ist |
| **B: zweite Spur danach** | Volltext und OCR sind nach zehn Stunden fertig und nutzbar, die Semantik füllt sich nach | zweiter Deckungsgrad auf der Statusseite (berührt ADM-01), zweite Zustandsspur in `files` |
| **C: nur für neue und geänderte Dateien, Bestand nie** | kostet nichts | die Semantik greift auf einem bestehenden Bestand praktisch nie, das Versprechen ist wertlos |

**Meine Empfehlung: B, zweite Spur.**

Begründung: die Architektur hat dafür bereits ein Vorbild. Phase 3 hat die
OCR-Zweitspur genau so gebaut (`skipped/no_text_layer` ist laut `repo.py` die
Liste, die Phase 3 abarbeitet, und `poller.py::_goes_to_the_ocr_track()` ist der
Verteiler). Eine Embedding-Zweitspur nach demselben Muster ist ein bekanntes
Verfahren in dieser Codebasis und kein neuer Entwurf. Der Nutzer bekommt eine
funktionierende Suche nach zehn Stunden und eine bessere nach weiteren sieben bis
vierundzwanzig, statt nach null Stunden nichts und nach dreißig alles.

Der Preis ist die zweite Zahl auf der Statusseite. Nach dem Produktversprechen
dieses Projekts ("der Admin erkennt den Zustand vor dem Nutzer") ist diese Zahl
allerdings kein Preis, sondern ein Gewinn.

---

### Frage 8: Bekommt ein Treffer eine Herkunftsmarkierung?

Also: erfährt die PHP-Seite, ob ein Kandidat lexikalisch, semantisch oder aus
beiden Quellen stammt?

| Option | Für | Gegen |
|---|---|---|
| **A: nein** | `Candidate` bleibt bei drei Feldern; der Kommentar in `api/search.py` verteidigt genau diese Kargheit ausdrücklich | Diagnose und Store-Screenshots können nicht zeigen, dass die Semantik wirkt |
| **B: ja, im Suchweg** | Diagnose, Admin-Seite, ein sichtbarer Beleg für Kriterium 1 | eine neue Aussage über ein Dokument, das der Recheck noch nicht bestätigt hat |
| **C: ja, aber nur in der Diagnose-Route** | Nutzen ohne Risiko im Suchweg | zwei Wege, die dasselbe wissen müssen |

**Meine Empfehlung: C.** Der Suchweg bleibt unverändert karg, weil sein
Kopfkommentar diese Kargheit als Sicherheitseigenschaft begründet und weil eine
Markierung dort keinen Nutzen hat, der das Risiko rechtfertigt. Die
Diagnose-Route aus Phase 4 (`api/diagnose.py`) ist dagegen admin-seitig, läuft
nicht je Treffer und ist genau der Ort, an dem "warum steht dieses Dokument in
der Liste" hingehört.

---

### Frage 9: Was passiert, wenn sqlite-vec verwaist?

Das Repo hat seit dem 18.05.2026 keinen Commit mehr, 204 offene Vorgänge, und
der ANN-Vorgang #25 ist seit Jahren offen. Dieses Projekt existiert, weil
`fulltextsearch` verwaist ist. Die Frage darf deshalb nicht unbeantwortet
bleiben.

| Option | Für | Gegen |
|---|---|---|
| **A: hinnehmen, exakt pinnen, dokumentieren** | die Erweiterung ist reines C ohne Abhängigkeiten und funktioniert, solange die SQLite-Erweiterungs-ABI stabil bleibt, was sie historisch ist | ein Bruch käme ohne Vorwarnung und ohne jemanden, der ihn behebt |
| **B: von Anfang an usearch** | aktiv gewartet | alle Kosten aus 2.3, für ein Problem, das bei gekappter Chunkung gar nicht auftritt |
| **C: A, plus ein Abstraktionsschnitt** | der Vektorspeicher liegt hinter einer schmalen Schnittstelle (`speichere`, `loesche`, `finde_aehnliche`), ein Austausch ist dann eine Datei und kein Umbau | etwas Mehrarbeit im Entwurf, sonst nichts |
| **D: A, plus die Erweiterung selbst mitliefern** | die `.so` liegt im Abbild, PyPI-Ausfall oder Zurückziehen des Pakets treffen uns nicht | eine Fremdbinärdatei im Abbild, Lizenz- und Herkunftsangabe in `THIRD-PARTY.md` nötig |

**Meine Empfehlung: C, und im gleichen Zug D.**

Zu C: der Abstraktionsschnitt kostet fast nichts, weil der Vektorspeicher
ohnehin nur drei Operationen braucht, und er ist die einzige Maßnahme, die den
Ausweichpfad aus Kriterium 4 von einer Absichtserklärung in etwas Belastbares
verwandelt. "Ausweichpfad dokumentiert" heißt dann "Ausweichpfad ist eine
Datei", nicht "Ausweichpfad ist ein Absatz".

Zu D: das Rad ist ohnehin `py3-none` und enthält nur die vorgebaute
Bibliothek. Sie im Abbild festzuhalten statt sie beim Bau zu ziehen, ist keine
zusätzliche Abhängigkeit, sondern dieselbe, nur festgenagelt. Das Projekt macht
das bei `APPSTORE_SHA` bereits genauso.

---

### Nachtrag: was der Discuss zusätzlich beschließen sollte

Drei Dinge, die keine Optionsfrage sind, aber eine ausdrückliche Zusage
brauchen:

1. **Die drei Vormessungen A, B und C aus 3.7 laufen vor der Schema-Festlegung.**
   Kriterium 4 verlangt es ("erst nach einem Lasttest festgezurrt"), und sie
   kosten zusammen unter einer Stunde. Ohne sie plant der Planner gegen dreizehn
   geschätzte Zahlen aus dem Assumptions Log.

2. **Die RSS-Store-Zahl wird nach Phase 6 mit aktiver Semantik erneut belegt.**
   D-09 sagt das bereits zu. Nach den Rechnungen in Teil 3 wird sie steigen, von
   428,6 MB auf geschätzt 650 bis 1.000 MB. Der Store-Text aus D-06 ("Volllauf
   50k Dateien auf 4-GB-ARM, Peak X GB") muss diese Zahl tragen, nicht die alte.

3. **Die Laufzeitaussage gehört in den Store-Text.** Wenn der Erstindex mit
   Semantik sieben bis vierundzwanzig Stunden länger dauert als ohne, ist das
   eine Zahl, die ein Selfhoster vor der Installation wissen will. Dieses
   Projekt hat sich bei jeder anderen Zahl für Ehrlichkeit entschieden; hier
   sollte es nicht anders sein.

---

*Recherchiert: 2026-09-04*
*Gültig bis: etwa 2026-10-04 für die Paketfassungen, unbegrenzt für die
Codebasis-Befunde, bis zur ARM-Messung morgen für alle Speicherrechnungen*
*Die Box 3.65.24.222 wurde für diese Recherche weder gelesen noch beschrieben.*
*Es wurde nichts committet.*
