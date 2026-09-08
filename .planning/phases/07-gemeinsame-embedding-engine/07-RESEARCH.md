# Phase 7: Gemeinsame Embedding-Engine - Research

**Researched:** 2026-09-08
**Domain:** Prozessweiter Speicherhaushalt der ExApp (onnxruntime, tokenizers, semantic-text-splitter), Kaltstartlatenz der semantischen Suche
**Confidence:** HIGH fuer die Bestandsaufnahme, MEDIUM fuer die Restluecke, HIGH fuer die Messbarkeit

---

## Lesehilfe: wie Aussagen in diesem Bericht gekennzeichnet sind

Dieser Bericht widerspricht an keiner Stelle einem abgenommenen Messbericht, aber er verschiebt
den Schwerpunkt der Phase. Deshalb traegt jede belastbare Aussage ihre Herkunft.

| Marke | Bedeutung |
|---|---|
| `[VERIFIED: <Quelle>]` | In dieser Sitzung mit einem Werkzeug gegen eine autoritative Quelle geprueft (Repo-Code mit Datei:Zeile, Workflow-Datei, installiertes Paket) |
| `[CITED: <URL>]` | Aus offizieller Dokumentation zitiert |
| `[MEASURED: <Messreihe>]` | Zahl aus einer Messreihe dieses Repositoriums, mit Rohdatei benannt |
| `[BERECHNET]` | Aus gemessenen Zahlen gerechnet, nicht selbst gemessen. Die Rechnung steht dabei |
| `[HYPOTHESE]` | Plausible Erklaerung einer gemessenen Zahl, in dieser Sitzung nicht belegbar. Braucht eine Messung, bevor daraus ein Plan wird |
| `[ASSUMED]` | Trainingswissen, nicht geprueft |

---

## Summary

**EFF-01 ist im Code fertig gebaut und dreifach abgesichert.** Alle vier Pfade, die im
ausgelieferten Container eine Embedding-Instanz brauchen, ziehen sie aus
`embed/engine.py::shared_model()`: die Suche, die Ausschnitte, die Diagnose und der Arbeiter.
Es gibt im gesamten `backend/src/findling/` keine zweite Konstruktionsstelle von
`EmbeddingModel` ausser der einen im Halter selbst. Der Beweis haengt nicht an einer
Speichermessung, sondern an einem Zaehler (`load_count()`), an sieben Unit-Tests und an einem
CI-Tor (`findling.tools.one_load` in `resilience.yml`), dessen Rotwerden in drei Testfaellen
mit Monkeypatch bewiesen ist. Success Criterion 1 der Roadmap ist damit heute erfuellt und
belegbar, ohne dass irgendetwas gebaut wird.

**EFF-02 ist ebenfalls schon gemessen, nur steht die Zahl nicht als solche im Bericht.** Die
Nachmessung vom 07.09.2026 hat als Allererstes eine einzelne semantische Suche gegen einen
Container gefahren, der noch nie eine gesehen hatte. Die Rohdatei
`rohdaten/64-stufe-01.json` weist dafuer **max 1.332,1 ms** aus, gegen ein Budget von 2.500 ms,
Fehler null. Die warme Entsprechung derselben Box ist 481,6 ms. Der Kaltstartaufschlag ist damit
**rund 850 ms**, und er faellt in den Aufruf, den `Provider.php` bei 1,5 s abschneidet. Die
Marge ist real, aber sie ist duenner als das 2.500-ms-Budget vermuten laesst, und genau das
gehoert in den Beleg.

**Die eigentliche Restluecke liegt nicht beim Modell, sondern beim Tokenizer und beim
Splitter.** Die Schritt-fuer-Schritt-Grundlast der Nachmessung
(`rohdaten/63-grundlast.txt`) zeigt: `11-tokenizer-gelesen` kostet **+269,4 MB**,
`12-chunker-gebaut-und-gefahren` noch einmal **+274,3 MB**, zusammen 543,7 MB von 693 MB
Grundlast. Die Modellgewichte selbst kommen mit +391,9 MB erst bei der ersten Einbettung
dazu. Beide Posten gehoeren allein dem Arbeiter, und sie werden heute **eifrig** im ersten
Durchlauf bezahlt (`worker/poller.py:1420`), auch in einem Container, der nie eine Zeile
einzubetten hat. Das ist der einzige Hebel dieser Groessenordnung, der noch offen ist.

**Primary recommendation:** Phase 7 wird ein **Beleg-Plan plus ein Messplan**, kein Umbauplan.
Zuerst wird EFF-01 mit Datei:Zeile und Zaehler abgehakt und EFF-02 aus den vorhandenen
Rohdaten samt seiner echten Grenze (1,5 s je Aufruf, nicht 2,5 s) belegt und in CI gegen
Rueckschritt gesichert. Parallel wird die 543,7-MB-Frage in einem Container gemessen, statt
sie zu vermuten. Nur wenn diese Messung einen Posten ueber 100 MB freilegt, entsteht ein
dritter, kleiner Gap-Plan. Ein Entladen des Modells nach Leerlauf wird ausdruecklich nicht
empfohlen: es senkt die Gesamtspitze nachweislich nicht und gefaehrdet EFF-02.

---

## User Constraints

**Es gibt keine CONTEXT.md fuer diese Phase.** `.planning/phases/07-gemeinsame-embedding-engine/`
enthaelt ausser dieser Datei nichts. `[VERIFIED: Verzeichnislisting]`

Die verbindlichen Vorgaben stammen deshalb aus ROADMAP.md, REQUIREMENTS.md und CLAUDE.md und
stehen unter "Project Constraints" und "Phase Requirements".

Ein Punkt aus dem v1.0-Bestand wirkt wie eine gesetzte Entscheidung und muss vom Planner als
solche behandelt werden:

> **Locked Decision (Phase 6, STATE.md:159):** "Zwei Tokenizer-Instanzen aus derselben Datei,
> weil `enable_truncation` eine Eigenschaft des Objekts ist: eine geteilte Instanz haette den
> 1.024-Token-Deckel aus D-01 still auf 512 halbiert."
> `[VERIFIED: .planning/STATE.md:159]`

Die naheliegendste Sparidee ("nur noch ein Tokenizer-Objekt") ist damit **verboten**. Sie ist
zusaetzlich vom Upstream-Projekt abgeraten: die Dokumentation von `semantic-text-splitter`
weist ausdruecklich darauf hin, dass ein Tokenizer mit aktiver Truncation die Chunkgroesse
still deckelt. `[CITED: https://pypi.org/project/semantic-text-splitter/]`

---

## Phase Requirements

| ID | Beschreibung | Was die Recherche dazu beitraegt |
|----|--------------|----------------------------------|
| EFF-01 | Suche und Indexer nutzen eine gemeinsame Embedding-Engine-Instanz; das Modell wird pro Prozess hoechstens einmal geladen | Vollstaendige Bestandsaufnahme mit Datei:Zeile in Teil 1. Ergebnis: gebaut, getestet, in CI gesichert. Es gibt keinen offenen Codepfad. Die Phase belegt es und baut es nicht |
| EFF-02 | Die erste semantische Suche nach Leerlauf haelt das p95-Suchbudget von 2,5 s ein | Die Zahl liegt bereits vor (1.332,1 ms, Teil 2). Die Recherche legt zusaetzlich die schaerfere Grenze frei, an der es wirklich haengt: `REQUEST_TIMEOUT_SECONDS = 1.5` in `ExAppService.php`. Teil 5 nennt drei Wege, das reproduzierbar ohne die AWS-Box zu sichern |

---

## Project Constraints (aus CLAUDE.md)

| Direktive | Herkunft | Wirkung auf diese Phase |
|---|---|---|
| Audit-Gate nach jeder Phase (Security, Bugs, Performance), Befunde ab MEDIUM vor Abschluss gefixt | Owner-Regel 15.08.2026 | Gilt auch fuer eine reine Beleg-Phase |
| Deutsche Projektkommunikation, keine Em-Dashes, echte Umlaute nur in Prosa, nie in Code | Constraints | Alle Planartefakte und Berichte dieser Phase |
| Python-Qualitaetsgates: ruff-Vollregelsatz, pyright basic, vulture, lokal gruen vor Commit | Constraints | Jede Codeaenderung dieser Phase |
| Hardware-Ziel 4 bis 8 GB RAM, ARM-tauglich, CPU-only, RAM-Budget hart einplanen | Constraints | Der Grund, warum diese Phase ueberhaupt existiert |
| Kein Telemetrie-Phoning, keine Inhalte verlassen den Server | Security/Privacy | Ein Messwerkzeug dieser Phase darf nichts senden und keinen Text protokollieren |
| Berechtigungskette wird nicht verdoppelt | Sequenz-Zwang 4 der Roadmap | Diese Phase fasst weder Vorfilter noch PHP-Recheck an |
| RAM-Budget-Tabelle nennt fuer onnxruntime + e5-small int8: "0 bei lazy_load=True, 250 bis 400 MB Spitze" | CLAUDE.md, Abschnitt RAM-Budget | Die gemessenen +391,9 MB liegen am oberen Rand dieser Vorgabe, sind also erwartungsgemaess. Die 543,7 MB fuer Tokenizer und Chunker stehen in der Budget-Tabelle **gar nicht** |

Der letzte Punkt ist der wichtigste Befund gegen die eigene Planung: das RAM-Budget des
Projekts kennt einen Posten "onnxruntime + Modell" und einen Posten "Tantivy Writer", aber
keinen Posten "Tokenizer und Splitter". Gemessen ist dieser Posten groesser als das Modell.

---

## Architectural Responsibility Map

| Faehigkeit | Primaerer Tier | Sekundaerer Tier | Begruendung |
|---|---|---|---|
| Halten der einen Modellinstanz | Container, Modul `embed/` | keiner | `embed/engine.py` gehoert weder der Leseseite noch dem Arbeiter, genau damit die Abhaengigkeitsrichtung `worker -> embed` erhalten bleibt und nicht `worker -> api` entsteht |
| Einbettung einer Suchzeile | Container, Leseseite (`api/search.py`, `api/snippets.py`, `api/diagnose.py`) | keiner | Alle drei ziehen ueber `resources.query_model()` |
| Einbettung von Dokument-Chunks | Container, Arbeiter (`worker/poller.py`) | keiner | Zweite Spur, laeuft der Volltextspur nach |
| Zerlegung in Chunks (Tokenizer + Splitter) | Container, **nur** Arbeiter | keiner | Die Leseseite fasst den Chunker nie an. `_rank_chunks` in `index/search.py:582` arbeitet ueber `vectors.best_chunk_for` und braucht keinen Splitter |
| Zeitbudget der Suche | PHP, `Search/Provider.php` | PHP, `Service/ExAppService.php` | 2.500 ms fuer die ganze Ergebnisgruppe, 1.500 ms je Containeraufruf. Der Container kennt beide Zahlen nicht und darf sie nicht kennen |
| Anzeige des Engine-Zustands | PHP, Adminseite und `occ findling:diagnose` | Container, `/status` und `/diagnose` | Heute zeigt die Adminseite nur die Abdeckung (`embedded`, `embeddedPercent`), nicht den Ladezustand der Engine. Siehe Teil 4 |

**Warum diese Karte hier steht:** Zeile vier ist der Hebel dieser Phase. Der teuerste
Speicherposten des Containers gehoert einem einzigen Tier, und dieses Tier bezahlt ihn heute
zu einem Zeitpunkt, zu dem noch nicht feststeht, ob er gebraucht wird.

---

## Teil 1: Bestandsaufnahme EFF-01, mit Datei und Zeile

### 1.1 Der Halter

`backend/src/findling/embed/engine.py:58` definiert `shared_model()`. Der Halter ist eine
Modulglobale `_ENGINE` (Zeile 51), geschluesselt nach `settings().embed_model_dir`, geschuetzt
von einem `threading.RLock` (Zeile 55). Die einzige Konstruktion von `EmbeddingModel` in der
Auslieferung steht in Zeile 76 bis 80. `[VERIFIED: backend/src/findling/embed/engine.py]`

Der Aufruf laedt nichts. Der Modulkopf sagt es ausdruecklich (Zeile 66 bis 68), und der Code
belegt es: `EmbeddingModel.__init__` (`embed/model.py:298`) setzt nur Felder, die Artefakte
werden erst in `_load()` (`embed/model.py:405`) gelesen, und `_load` wird erst aus `_embed`
gerufen (`embed/model.py:369`). `[VERIFIED: backend/src/findling/embed/model.py]`

### 1.2 Alle Aufrufstellen, vollstaendig

Gesucht wurde mit `grep -rn "shared_model\|EmbeddingModel(" backend/src backend/tests scripts`,
also ueber den gesamten Quellbaum ohne `.venv`. `[VERIFIED: ripgrep ueber backend/src, backend/tests, scripts]`

| Pfad | Datei:Zeile | Woher die Engine kommt | Bewertung |
|---|---|---|---|
| Suche (Kandidatenrunde) | `api/search.py:232` | `resources.query_model()` | geteilt |
| Ausschnitte (Snippets) | `api/snippets.py:153` | `resources.query_model()` | geteilt |
| Diagnose (Herkunft eines Treffers) | `api/diagnose.py:187` | `resources.query_model()` | geteilt |
| Weiterreicher der Leseseite | `api/resources.py:270` | `return shared_model()` | geteilt, keine eigene Globale mehr |
| Arbeiter, zweite Spur | `worker/poller.py:1491` | `self._model = shared_model()` | geteilt |
| Beleg-Werkzeug | `tools/one_load.py:265, 272, 280` | liest nur `load_count()`, baut nichts | Beleg |

**Es gibt keinen weiteren Pfad.** Die einzigen anderen Konstruktionen von `EmbeddingModel` im
Baum stehen in `backend/tests/` und in `scripts/dev/vector_distances.py:812`. Beide sind
Werkzeuge und laufen nie im ausgelieferten Container:
`scripts/` liegt nicht im Laufzeit-Abbild, und `embed/bench.py` steuert onnxruntime direkt an,
ohne `EmbeddingModel`. `[VERIFIED: backend/Dockerfile, Stage-Aufbau; ripgrep]`

**Der Extraktions-Kindprozess laedt kein Modell.** In `backend/src/findling/extract/` kommt
weder `embed` noch `EmbeddingModel` vor. Der im Semantiklauf beobachtete Spawn-Kindprozess mit
69 MB traegt also keine Gewichte. `[VERIFIED: ripgrep ueber backend/src/findling/extract/]`

### 1.3 Der Zaehler und die Tests

`embed/model.py:143` stellt `load_count()` bereit, hochgezaehlt genau einmal je wirklich
gelesenem Artefaktpaar in `_load()` (`embed/model.py:454`). Das ist der Beweis ohne Uhr, den
Success Criterion 1 verlangt. `[VERIFIED: backend/src/findling/embed/model.py]`

`backend/tests/test_embed_engine.py` haelt sieben Faelle, davon vier direkt fuer EFF-01:

- `test_the_search_and_the_track_get_the_same_engine` (Zeile 194)
- `test_another_model_directory_gets_another_engine` (Zeile 206)
- `test_two_threads_get_one_engine_and_pay_for_one_load` (Zeile 227)
- `test_the_second_track_and_the_read_side_wire_the_same_object` (Zeile 269)

`[VERIFIED: backend/tests/test_embed_engine.py]`

### 1.4 Das CI-Tor, und warum es ein Zaehler ist und kein Byte

`findling.tools.one_load` baut ein eigenes Volumen, indexiert ein Dokument, faehrt **eine
echte Suchrunde** ueber `api/search.py::one_round` und verdrahtet **danach** die zweite Spur
ueber `Poller._wire_the_second_track`. Vier Zaehler muessen auf eins stehen; jeder andere Wert
ist ein benannter Befund mit Exit 1. `[VERIFIED: backend/src/findling/tools/one_load.py:265-330]`

Die Reihenfolge ist die Leerlaufsperre: die Suchseite muss die Ladezahl **allein** auf eins
bringen, sonst meldet der Lauf eine Null und faellt, statt still gruen zu sein.
`[VERIFIED: one_load.py Modulkopf, Zeile 22-38]`

Das Tor haengt in `.github/workflows/resilience.yml`, Schritt "One engine and one constituent
list per process" (Zeile 1417 bis 1431), im Job `measurements` auf `ubuntu-24.04`, also amd64.
`[VERIFIED: .github/workflows/resilience.yml]`

Die Faehigkeit rot zu werden ist bewiesen, nicht behauptet: `backend/tests/test_one_load.py`
holt in drei Faellen die Regressionen per Monkeypatch zurueck
(`test_it_goes_red_when_the_search_side_builds_its_own_engine` Zeile 173,
`..._when_the_word_list_is_read_a_second_time` Zeile 198,
`..._when_the_search_never_reaches_the_model` Zeile 212).
`[VERIFIED: backend/tests/test_one_load.py]`

Warum kein Speicherdeckel: der Messcontainer in `resilience.yml` startet auf einem leeren
`APP_PERSISTENT_STORAGE`, `read_side()` antwortet `None`, und die Suche kehrt um, bevor sie
Wortliste, Automat oder Modell erreicht. Gemessen wurden dort 241.172 und 503.316 Byte
Unterschied, also Rauschen. Ein Deckel darueber waere ein Tor, das fuer die Sache, die es
benennt, gar nicht rot werden kann. `[VERIFIED: .github/workflows/resilience.yml, Kommentar Zeile 1385-1403]`

### 1.5 Fazit Teil 1

**EFF-01 ist erledigt.** Kein Codepfad im ausgelieferten Container baut eine zweite
`EmbeddingModel`-Instanz. Success Criterion 1 ist mit einem Zaehler, sieben Unit-Tests, drei
Rotbeweisen und einem CI-Tor auf jedem Push belegt. Die Phase muss diesen Beleg
zusammenschreiben, nicht ihn herstellen.

**Eine Praezisierung gehoert in den Beleg, damit er nicht mehr verspricht als er haelt:**
"eine Engine" heisst eine `EmbeddingModel`-Instanz, also **ein** Satz Gewichte und **eine**
onnxruntime-Sitzung. Es heisst **nicht** "ein Tokenizer-Objekt im Prozess". Davon gibt es
mindestens zwei, mit voller Absicht (Teil 3).

---

## Teil 2: Bestandsaufnahme EFF-02, und die Grenze, an der es wirklich haengt

### 2.1 Die Zahl liegt vor

Skript `64-spitze.sh` der Nachmessung hat als erste Handlung des Laufs genau eine semantische
Suche gegen einen Container gefahren, der in diesem Start noch nie eine gesehen hatte. Die
Rohdatei dazu:

| Groesse | Wert | Quelle |
|---|---|---|
| Anfragen | 3, davon die erste kalt | `rohdaten/64-stufe-01.json` |
| Fehler | 0 | ebenda |
| p50 | 465,3 ms | ebenda |
| **p95 / max** | **1.332,1 ms** | ebenda |
| Budget | 2.500 ms, `p95_within_budget: true` | ebenda |
| Warme Entsprechung, gleiche Box, 10 Runden | p95 481,6 ms | `rohdaten/67-stufe-1.json` |

`[MEASURED: docs/measurements/2026-09-nachmessung-m7g/rohdaten/64-stufe-01.json, 67-stufe-1.json]`

Der Weg war die OCS-Route ueber Apache, HaRP und AppAPI, also der Weg eines Nutzers und nicht
ein Aufruf in den Container hinein. `[VERIFIED: scripts/ops/search_load.py, Modulkopf]`

**Der Kaltstartaufschlag ist damit 1.332,1 minus 481,6, also rund 850 ms.** `[BERECHNET]`
Er passt zur Speicherbeobachtung derselben Sekunde: anon springt von 694,3 MB auf 1.116,6 MB,
also +422,3 MB, und das sind die Gewichte. `[MEASURED: rohdaten/64-spitze.txt]`

### 2.2 Die schaerfere Grenze: 1,5 Sekunden je Aufruf

Das 2.500-ms-Budget ist nicht die Schranke, gegen die eine kalte Suche zuerst laeuft.

- `php/lib/Search/Provider.php:57`: `BUDGET_NANOSECONDS = 2_500_000_000`, die Wanduhr fuer
  die **ganze Ergebnisgruppe**.
- `php/lib/Service/ExAppService.php:89`: `REQUEST_TIMEOUT_SECONDS = 1.5`, die Decke fuer
  **einen einzelnen** Containeraufruf, und jeder Aufruf schrumpft zusaetzlich auf
  `secondsLeft($deadline)` (`Provider.php:258` und `:412`, `secondsLeft` bei `:504`).
- Eine Suche macht **zwei** Aufrufe: `searchCandidates` und `snippets`. Der erste steht in
  einer Schleife und kann mehrfach laufen, wenn der Recheck Treffer einer Seite entfernt
  (`Provider.php:248-258`).

`[VERIFIED: php/lib/Search/Provider.php, php/lib/Service/ExAppService.php]`

Der Ladevorgang steht unter dem Lock (`embed/model.py:369`: `with self._lock: engine = self._load()`),
also warten gleichzeitige Suchen hinter genau einem Laden.
`[VERIFIED: backend/src/findling/embed/model.py]`

**Was daraus folgt, als Rechnung und nicht als Messung:** die 850 ms Ladezeit fallen innerhalb
des ersten Containeraufrufs an, dessen Decke 1.500 ms ist. Gemessen wurden 1.332,1 ms
**einschliesslich** PHP-Weg, der Aufruf ist also nicht abgeschnitten worden, und 1.168 ms des
Gesamtbudgets blieben uebrig. Die Marge zur Aufrufdecke ist aber kleiner als die Marge zum
Gesamtbudget, und sie schrumpft mit der Nebenlaeufigkeit, weil das Laden serialisiert:

| Stufe | warm p95 gemessen | plus 850 ms Laden | gegen 2.500 ms |
|---|---|---|---|
| 1 | 481,6 ms | 1.332 ms (**gemessen**) | haelt |
| 4 | 1.009,4 ms | rund 1.859 ms | haelt knapp |
| 8 | 1.915,0 ms | rund 2.765 ms | **gerissen** |

`[BERECHNET aus rohdaten/67-stufe-*.json; nur die erste Zeile ist gemessen]`

Das ist kein heutiger Fehler: heute laedt das Modell genau einmal je Prozessleben, also trifft
der Fall "kalt und acht gleichzeitige Suchen" praktisch nur den ersten Augenblick nach einem
Containerstart. Es ist aber die entscheidende Zahl gegen jede Form von Modell-Entladung
(Teil 3.4).

### 2.3 Was "nach Leerlauf" heute bedeutet

Es gibt im Code keinen Pfad, der eine geladene Engine wieder freigibt. `_ENGINE` wird nur
ersetzt, wenn sich `embed_model_dir` aendert (`embed/engine.py:74`), und `EmbeddingModel._engine`
wird nach einem erfolgreichen Laden nie wieder auf `None` gesetzt; ein geworfener Batch behaelt
die Engine ausdruecklich (`embed/model.py:385-392`). `[VERIFIED: backend/src/findling/embed/]`

**"Erste Suche nach Leerlauf" hat deshalb heute genau eine nichttriviale Lesart: die erste
Suche nach einem Containerstart.** Genau die ist mit 1.332,1 ms gemessen. Der Planner sollte
diese Lesart in der Formulierung des Kriteriums festschreiben, sonst misst die Phase einen
Zustand, den das Produkt nicht kennt.

Eine zweite, kleinere Lesart bleibt: der Seitencache. Nach langem Leerlauf koennen der
Tantivy-Index und die 64 MB `vectors.db` aus dem Cache gefallen sein, und der Brute-Force-Scan
liest sie neu. Die Nachmessung weist den Abstand zwischen `anon` und `memory.current` mit rund
86 MB aus, konstant ueber alle Nebenlaeufigkeitsstufen. `[MEASURED: Nachmessung Abschnitt 5]`
Die Wave-0-Reihe hat kalte und warme Scanlatenz bereits getrennt gemessen
(`measure.yml`, Schritt "C, scan latency", mit `--privileged --user 0` und `drop_caches`).
`[VERIFIED: .github/workflows/measure.yml:266-295]` Das ist ein bereits vorhandenes Werkzeug
und kein neuer Bau.

### 2.4 Fazit Teil 2

**EFF-02 ist der Zahl nach erfuellt, aber der Beleg fehlt an der richtigen Stelle.** Die Zahl
liegt in einer Rohdatei und nicht im Bericht; sie ist auf arm64 gemessen, waehrend Success
Criterion 4 eine amd64-Zahl verlangt; und die Grenze, an der sie wirklich haengt, ist im
Messbericht gar nicht genannt. Das sind drei Beleglucken und kein Baubedarf.

---

## Teil 3: Die Restluecke, und warum sie nicht beim Modell liegt

### 3.1 Der Befund aus der Schritt-fuer-Schritt-Grundlast

`rohdaten/63-grundlast.txt`, Abschnitt C, misst RSS nach jedem Startschritt in einem eigenen
Prozess auf der ARM-Box:

| Schritt | RSS danach | Zuwachs |
|---|---|---|
| `00-leerer-prozess` | 12,9 MB | |
| `06-poller-importiert` | 68,0 MB | +41,2 MB |
| `09-wortliste-gelesen-276496` | 92,2 MB | +21,9 MB |
| `10-deutscher-automat-gebaut` | 134,3 MB | +42,1 MB |
| **`11-tokenizer-gelesen`** | **403,8 MB** | **+269,4 MB** |
| **`12-chunker-gebaut-und-gefahren-2`** | **678,0 MB** | **+274,3 MB** |
| `13-modell-objekt-gebaut-lazy` | 678,0 MB | +0,0 MB |
| `14-erste-einbettung-gewichte-geladen` | 1.069,9 MB | +391,9 MB |
| `15-lange-einbettung-aktivierungen` | 1.096,3 MB | +26,4 MB |

`[MEASURED: docs/measurements/2026-09-nachmessung-m7g/rohdaten/63-grundlast.txt]`

Zwei Zahlen springen heraus. **543,7 MB von 678 MB Grundlast entstehen in genau zwei
Schritten**, die beide nichts mit den Modellgewichten zu tun haben. Und Schritt 13 kostet
exakt null, was den faulen Bau der Engine unabhaengig bestaetigt.

### 3.2 Was in diesen beiden Schritten wirklich passiert

`worker/poller.py:1462-1491` verdrahtet die zweite Spur in dieser Reihenfolge:

1. `open_vectors(resolved.vectors_db)` (Zeile 1464)
2. `open_tokenizer(resolved.embed_model_dir)` (Zeile 1465) - das ist Schritt 11
3. `make_splitter(tokenizer, ...)` (Zeile 1466) - das ist der erste Teil von Schritt 12
4. `shared_model()` (Zeile 1491) - kostet nichts, Schritt 13

`[VERIFIED: backend/src/findling/worker/poller.py]`

`open_tokenizer` (`embed/model.py:192`) importiert `tokenizers` **innerhalb der Funktion** und
baut dann `Tokenizer.from_file`. Die +269,4 MB sind also Modulimport **plus** erste Instanz,
und die beiden sind in dieser Messung nicht getrennt. `[VERIFIED: backend/src/findling/embed/model.py:192-204]`

`make_splitter` (`embed/chunker.py:67`) ruft
`TextSplitter.from_huggingface_tokenizer(tokenizer, chunk_tokens, overlap=overlap)` aus
`semantic_text_splitter 0.32.0`, einer Rust-Erweiterung.
`[VERIFIED: backend/.venv/Lib/site-packages/semantic_text_splitter/, __init__.pyi:94]`
Der Modulkopf des Projekts sagt dazu selbst: "building it hands the whole tokenizer across the
language boundary. The shipped `tokenizer.json` weighs 17 MB."
`[VERIFIED: backend/src/findling/embed/chunker.py:70-73]`

**`[HYPOTHESE]`** Die +274,3 MB von Schritt 12 sind zu einem grossen Teil eine zweite
Materialisierung des Tokenizers auf der Rust-Seite des Splitters, nicht der Preis des zweimal
gefahrenen Chunkers. Dafuer spricht die Groessengleichheit mit Schritt 11 (269,4 gegen 274,3).
Dagegen spricht, dass der Schritt "gebaut UND gefahren, zweimal" heisst und beides zusammen
misst.

**Diese Hypothese ist in dieser Sitzung nicht pruefbar.** Die Modellartefakte liegen nur im
Abbild, nicht im Arbeitsbaum: `FINDLING_EMBED_MODEL_DIR` ist lokal leer, und es liegt keine
`tokenizer.json` auf der Maschine. `[VERIFIED: Umgebungsvariable und Dateisuche]` Die
Dokumentation von `semantic-text-splitter` aeussert sich zum Kopierverhalten nicht
`[CITED: https://github.com/benbrandt/text-splitter]`, und die Ankuendigungs-Diskussion des
Features ebenfalls nicht `[CITED: https://github.com/benbrandt/text-splitter/discussions/22]`.

**Sie ist aber billig pruefbar**, und zwar in genau dem Werkzeug, das die Zahl erzeugt hat:
Schritt 11 und 12 werden in fuenf Schritte zerlegt (Modulimport allein, erste
Tokenizer-Instanz, Splitterbau, ein Chunkerlauf, zweiter Chunkerlauf) und der Lauf wird im
Abbild wiederholt. Das kostet einen Containerstart und keine Box.

### 3.3 Der eifrige Bau, und warum er die eigentliche Luecke ist

`worker/poller.py:1420`:

```
if self._owns_resources and self._embed_enabled and self._vectors is None:
    self._wire_the_second_track()
```

Das steht in `_open()`, also im **ersten Durchlauf** des Pollers, unabhaengig davon, ob je eine
Einbettungszeile ankommt. `[VERIFIED: backend/src/findling/worker/poller.py:1402-1431]`

Damit bezahlt **jeder** Container mit eingeschalteter Einbettung die 543,7 MB dauerhaft, auch
einer, dessen Bestand vollstaendig eingebettet ist und der nur noch sucht. Genau dieser
Zustand ist der Normalfall einer laufenden Installation: die zweite Spur ist eine
nachlaufende Spur, die irgendwann fertig ist.

Die Leseseite braucht davon nichts. Sie fasst den Chunker nie an; die Rangfolge der Chunks
laeuft ueber `vectors.best_chunk_for` (`index/search.py:612`). `[VERIFIED: backend/src/findling/index/search.py]`

**Der Hebel ist deshalb nicht "weniger laden", sondern "spaeter laden":** die Verdrahtung der
zweiten Spur wandert von "erster Durchlauf" nach "erste Einbettungszeile". Das ist genau das
Muster, das `shared_model()` und `EmbeddingModel._load()` fuer die Gewichte bereits anwenden,
und es waere in derselben Datei die dritte Anwendung derselben Regel.

Was dabei zu klaeren ist und was der Planner nicht ueberspringen darf:

1. `_embed_ready` (`poller.py:1494`) wird **vor** dem Herausgeben einer Zeile gefragt, damit
   Zeilen nicht auf eine Spur wandern, die nicht laufen kann. Ein fauler Bau muss diese
   Zusage erhalten, sonst entsteht die `failed(repeatedly_stuck)`-Schleife, die der Kommentar
   dort ausdruecklich beschreibt.
2. `self._store.attach_vectors(self._vectors)` (`poller.py:1422`) und
   `_open_writer(self._store, vectors=self._vectors)` (`poller.py:1425`) haengen am
   Vektorbestand. Der Loeschpfad braucht ihn (D-21). **Der Vektorbestand darf also nicht faul
   werden, nur Tokenizer und Splitter duerfen es.** Das ist eine Aufteilung von
   `_wire_the_second_track` in zwei Haelften und keine Verschiebung des Ganzen.
3. Das CI-Tor `one_load` verdrahtet die zweite Spur direkt (`one_load.py:220`) und liest danach
   `worker._model` und `worker._chunker`. Ein fauler Chunker macht diese Stelle rot, wenn sie
   nicht mitgezogen wird. Das ist kein Argument dagegen, sondern eine Aufgabe im Plan.

### 3.4 Modell-Entladung nach Leerlauf: nein, mit Zahlen

Die Idee steht in REQUIREMENTS.md unter "Future Requirements" als Alternative zu EFF-01, "nur
falls die gemeinsame Engine nicht reicht". `[VERIFIED: .planning/REQUIREMENTS.md]` Sie wurde
in Plan 06.1-02 schon einmal als "Bauform B" verworfen. `[VERIFIED: 06.1-02-SUMMARY.md, Decisions Made]`

Die Nachmessung liefert jetzt die Zahlen, die diese Ablehnung endgueltig machen:

1. **Sie senkt die Gesamtspitze nicht.** Die Spitze liegt bei 1.812,7 MB in der OCR-Phase, und
   in dieser Phase laeuft die Einbettung mit: 4,3 s je Datei "inklusive Abholen, OCR,
   Einbettung und Schreiben". `[MEASURED: Nachmessung Abschnitt 4]` Ein Entladetimer entlaedt
   genau dann nichts.
2. **Sie senkt die Grundlast kaum.** Von den 693,4 MB Grundlast gehoeren null MB den
   Modellgewichten: Schritt 13 der Aufschluesselung kostet 0,0 MB, die Gewichte kommen erst
   bei der ersten Einbettung. Was entladbar waere, ist nicht das, was im Leerlauf liegt.
   `[MEASURED: rohdaten/63-grundlast.txt]`
3. **Sie kostet EFF-02 direkt.** Jedes Entladen macht die naechste Suche wieder zur kalten
   Suche mit rund 850 ms Aufschlag unter einem Lock, gegen eine Aufrufdecke von 1.500 ms und
   ein Gruppenbudget von 2.500 ms. Bei acht gleichzeitigen Suchen reisst die Rechnung das
   Budget. `[BERECHNET, Teil 2.2]`

**Empfehlung: Modell-Entladung bleibt in "Future Requirements" und wird in dieser Phase nicht
geplant.** Der Beleg-Plan sollte die drei Punkte oben festhalten, damit die Idee nicht in
Phase 10 oder 11 erneut auftaucht.

### 3.5 Was am Modell selbst noch offen waere, und warum es hier nicht hingehoert

Die +391,9 MB der Gewichte sind der Preis eines int8-quantisierten e5-small mit
abgeschalteter Arena (`enable_cpu_mem_arena=False`, Entscheidung aus 06-05). Kleiner wuerde er
nur durch ein anderes Modell oder eine andere Quantisierung, und beides aendert die
Trefferqualitaet und erzwingt einen vollstaendigen Reindex von 51.961 Dokumenten. Das ist ein
eigenes Milestone-Thema und keine Aufgabe von EFF-01.
`[VERIFIED: .planning/STATE.md, Phase-6-Entscheide; CLAUDE.md Abschnitt 4]`

---

## Teil 4: Success Criterion 3, die halb offene Zusage

Kriterium 3 lautet: "Faellt die Engine aus oder fehlt das Modell, liefert die Suche
unveraendert Volltexttreffer statt eines Fehlers, und der Admin sieht den Zustand in der
Diagnose."

**Erste Haelfte: belegt.** `EmbedOutcome.unavailable()` (`embed/model.py:172`) fuehrt in
`index/search.py:216-225` dazu, dass die semantische Liste leer bleibt und die Verschmelzung
zur Identitaet auf der lexikalischen Rangfolge wird. Ein fehlendes Verzeichnis wird dauerhaft
gemerkt (`_absent`, `embed/model.py:431`), ein geworfenes Oeffnen nur fuer
`LOAD_RETRY_SECONDS = 300` (`embed/model.py:132`, Auswertung bei `:426`). Beides ist in
`test_embed_engine.py` mit drei Faellen abgedeckt (Zeilen 336, 356, 376).
`[VERIFIED: backend/src/findling/embed/model.py, backend/tests/test_embed_engine.py]`

**Zweite Haelfte: nur teilweise.** Was der Admin heute sieht:

| Ort | Zeigt | Zeigt nicht |
|---|---|---|
| Adminseite, `AdminViewService.php:1343-1355` | `embedded`, `embeddedPercent`, also die Abdeckung | ob die Engine geladen ist, fehlt oder in der Karenzzeit steht |
| `StatusResponse`, `api/status.py:102-162` | `embedded`, `note` (nur ueber die Vektor-Datenbank: `NO_VECTORS_YET`, `VECTORS_UNREADABLE`) | kein Feld fuer den Engine-Zustand |
| `occ findling:diagnose` je Datei, `AdminViewService.php:709` | das Verdikt aus `state.db`, also auch `embedding_unavailable` | nur fuer eine Datei, die den Fall schon getroffen hat |

`[VERIFIED: php/lib/Service/AdminViewService.php, backend/src/findling/api/status.py, backend/src/findling/worker/poller.py:1078,1108]`

Der Weg zum Befund ist also da, aber er fuehrt ueber eine Einzeldatei-Diagnose. Ein Admin, der
nur die Seite ansieht, sieht "eingebettet: 0 Prozent" und kann nicht unterscheiden zwischen
"das Modell fehlt", "das Laden ist gescheitert und wird in 300 Sekunden erneut versucht" und
"die zweite Spur ist noch nicht dazugekommen".

**Bewertung:** Das ist eine echte, kleine Luecke gegen Kriterium 3, aber es ist eine
Diagnose-Luecke und keine Speicher-Luecke. Sie ist billig zu schliessen (ein Feld auf
`StatusResponse`, gespeist aus `EmbeddingModel.loaded` und `_absent` beziehungsweise
`_load_failed_at`, plus eine Zeile auf der Adminseite) und sie beruehrt keine
Sicherheitsflaeche. Der Planner entscheidet, ob sie in diese Phase gehoert oder als
Backlog-Punkt zu Phase 11 wandert. Meine Empfehlung steht in Teil 6.

---

## Teil 5: Wie EFF-02 ohne die AWS-Box reproduzierbar gemessen wird

### 5.1 Was ohne die Box zur Verfuegung steht

| Mittel | Wo | Traegt das Modell? | Architektur | Eignung |
|---|---|---|---|---|
| `resilience.yml`, Job `measurements` | GitHub, `ubuntu-24.04` | ja, `findling_backend:measure` | amd64 | Hier haengt das `one_load`-Tor schon. `[VERIFIED: resilience.yml:1199-1431]` |
| `measure.yml`, Matrix mit `ubuntu-24.04-arm` | GitHub | ja, Abbild per Digest | **arm64** | Der einzige Weg zu einer arm64-Zahl ohne AWS. `[VERIFIED: .github/workflows/measure.yml:79-80]` |
| `integration.yml`, Job `walking-skeleton` | GitHub, `ubuntu-24.04` | ja | amd64 | Der einzige Weg mit **echter Nextcloud und echtem PHP-Weg**, also der einzige, an dem das 2,5-s-Budget ueberhaupt gemessen werden darf. `[VERIFIED: .github/workflows/integration.yml:102-247]` |
| `scripts/dev/compose.yaml`, `compose-harp.yaml` | lokal, WSL2 | ja | amd64 | Wiederholbar von Hand, gut fuer die einmalige Berichtszahl |
| `findling.tools.one_load` | ueberall, im Prozess | ja | beides | Baut sich sein Volumen selbst, faehrt eine echte Suchrunde. `[VERIFIED: one_load.py]` |

### 5.2 Drei Wege, nach Kosten sortiert

**Weg A, der billigste und ehrlichste: die Ladedauer als eigene Zahl, nicht als Latenzdeckel.**

`findling.tools.one_load` faehrt bereits eine echte Suchrunde gegen ein selbst gebautes Volumen
und bringt dabei die Ladezahl von null auf eins. Die Wanduhr um genau diesen Aufruf ist die
Kaltstartzahl, ohne dass irgendetwas neu gebaut werden muss: `drive_the_search_side()`
(`one_load.py:209`) klammert `one_round`. Der Report bekommt ein siebtes Feld.

Was daraus **kein** Tor werden darf: ein Millisekundendeckel auf einem geteilten
GitHub-Runner. Genau diese Falle hat `resilience.yml` fuer den Speicher schon einmal
ausgeschlagen, mit der Begruendung, ein Tor duerfe nicht fuer Rauschen rot werden
`[VERIFIED: resilience.yml:1385-1403]`; das Spiegelbild waere ein Zeittor, das fuer
Runner-Last rot wird. Die Zahl wird also **berichtet** und in der Reihe gesammelt, so wie die
`rss first-search-growth-bytes`-Reihe daneben.

Ein Tor, das trotzdem rot werden **kann** und darf: der Kaltstart darf nicht mehr als **einen**
Ladevorgang kosten und die kalte Suche muss ein Ergebnis liefern. Beides zaehlt `one_load`
heute schon.

**Weg B, die belastbare Zahl fuer den Bericht: eine kalte Suche ueber den echten PHP-Weg.**

`integration.yml`, Job `walking-skeleton`, hat Nextcloud, beide Haelften, einen registrierten
ExApp und eine Suche als Testnutzer (`- name: Search as the test user`, Zeile 206). Ein
zusaetzlicher Schritt, der vor jeder anderen Suche genau eine zweiwortige semantische Zeile
absetzt und die Wanduhr dazu ausgibt, liefert die amd64-Entsprechung zu den 1.332,1 ms und
damit die Zahl, die Success Criterion 4 verlangt.

Zwei Vorbedingungen, die der Planner nicht uebersehen darf:

1. Es muss ein Dokument mit Vektoren geben, sonst ist `side.vectors` leer und die Suche
   erreicht das Modell nie. Der Job indexiert einen Korpus, aber die zweite Spur laeuft
   nachlaufend; der Schritt muss auf `embedded >= 1` warten, nicht nur auf `indexed`.
2. Die Zeile muss **zwei Woerter** haben. Seit dem Nachtrag 06.1-20 bleibt eine einwortige
   Zeile lexikalisch (`api/search.py:215-223`, `rewritten.one_term`), und ein einwortiger
   Test wuerde die Regel messen statt das Laden. `one_load` hat exakt diese Falle schon
   dokumentiert und benutzt deshalb `QUERY = "Vertrag Monate"` (`one_load.py:100-103`).
   `[VERIFIED: backend/src/findling/tools/one_load.py, backend/src/findling/api/search.py]`

**Weg C, die arm64-Entsprechung ohne AWS:** `measure.yml` laeuft schon auf `ubuntu-24.04-arm`
und zieht das arm64-Abbild per Digest. Ein Messschritt dort liefert eine arm64-Kaltstartzahl
zum Vergleich mit den 1.332,1 ms der Box. Der Workflow ist `workflow_dispatch`-only und
schreibt seine Rohdaten als Artefakt, passt also zur Kultur "Messung nicht bei jedem Push".
`[VERIFIED: .github/workflows/measure.yml, Modulkopf Zeile 8-24]`

### 5.3 Was keiner dieser Wege leisten kann, und das gehoert in den Bericht

- **Keine 51.961 Dokumente.** Die Kaltstartzahl aus CI misst das Laden der Gewichte, nicht den
  Brute-Force-Scan ueber 145.854 Chunks. Der Anteil des Scans an den 481,6 ms warm ist auf der
  Box gemessen, in CI nicht.
- **Keine 2 vCPU und keine 4 GB.** GitHub-Runner sind groesser. `--cpuset-cpus 0,1` und
  `--memory` koennen das annaehern (`measure.yml` tut es fuer die Wave-0-Reihe), aber eine
  Annaeherung ist keine Zielhardware.
- **Kein Anspruch auf p95.** Drei oder zehn Anfragen auf einem geteilten Runner ergeben kein
  p95. Die Zahl, die CI liefert, ist eine **Kaltstartdauer**, und sie ist als solche zu
  benennen. Das p95 gehoert nach Phase 10.

---

## Teil 6: Empfehlung fuer den Schnitt der Phase

### 6.1 Was in die Phase gehoert

**Plan 07-01: Der Beleg (klein, kein Produktionscode).**

- EFF-01 mit Datei:Zeile abhaken, wie in Teil 1, einschliesslich der Praezisierung "eine
  Engine heisst eine Sitzung und ein Satz Gewichte, nicht ein Tokenizer-Objekt".
- EFF-02 aus `64-stufe-01.json` in den Bericht heben, zusammen mit der Aufrufdecke von 1,5 s
  und der Nebenlaeufigkeitsrechnung aus Teil 2.2.
- Die Ablehnung der Modell-Entladung mit den drei Zahlen aus Teil 3.4 festschreiben, damit sie
  nicht wiederkehrt.
- Der Zielort ist ein Abschnitt in `docs/performance.md` (dort steht die Nachmessung bereits
  ab Zeile 2996) plus ein Eintrag in `.planning/STATE.md`.

**Plan 07-02: Die amd64-Zahl und das Rueckschritt-Tor.**

- `one_load` bekommt die Kaltstartdauer als siebte Zahl (Weg A). Bericht, kein Deckel.
- `integration.yml` bekommt eine kalte semantische Suche ueber den echten PHP-Weg (Weg B), mit
  den zwei Vorbedingungen aus Teil 5.2.
- Ergebnis: die amd64-Zahl, die Success Criterion 4 verlangt, und die Aussage, an welcher
  Stelle der Unterschied anfaellt. Nach heutigem Stand lautet diese Aussage: **Suchphase minus
  712,6 MB, Grundlast unveraendert, Gesamtspitze minus 25,1 MB**, und die Gesamtspitze gehoert
  inzwischen der OCR-Phase.

**Plan 07-03: Die Messung der 543,7 MB (Teil 3.2), und nur bei Befund ein Bau.**

- Schritt 11 und 12 der Grundlast-Aufschluesselung in fuenf Schritte zerlegen und im Abbild
  fahren. Das Skript existiert bereits (`63-grundlast.sh`), es wird nur feiner gemacht.
- **Abbruchbedingung im Plan verankern:** liegt kein einzelner Posten ueber 100 MB, endet die
  Phase hier mit einem dokumentierten Befund, und der faule Bau wandert in den Backlog. Liegt
  einer darueber, folgt der Bau nach Teil 3.3, mit den drei dort genannten Auflagen.
- Grund fuer die Reihenfolge: dieses Repository hat in 06.1-02 schon einmal einen Posten aus
  einem abgenommenen Messbericht falsifiziert, bevor er gefixt wurde ("der zweite deutsche
  Zerlegungsautomat existiert nicht"). Dasselbe Muster gehoert hierher.

**Offen zur Entscheidung: der Engine-Zustand in der Diagnose (Teil 4).** Er gehoert dem
Wortlaut nach zu Kriterium 3 dieser Phase. Er ist billig, aber er beruehrt PHP und Python
gleichzeitig, und Phase 11 faehrt ohnehin noch einmal alle Audits. Meine Empfehlung: **in diese
Phase aufnehmen**, als vierten, kleinen Plan, weil ein Kriterium der Phase sonst mit "halb"
abgeschlossen wird und das in Phase 10 niemandem mehr auffaellt.

### 6.2 Was ausdruecklich nicht in die Phase gehoert

| Nicht hier | Warum | Wohin |
|---|---|---|
| p95-Messung ueber den vollen Korpus | Braucht 51.961 Dokumente und die Zielhardware; die Box wird genau einmal angefahren | Phase 10 |
| Der Vergleich Zeile fuer Zeile gegen die v1.0-Baseline | MESS-03, ausdruecklich Phase 10 | Phase 10 |
| Die 250 MB teurere OCR-Phase mit drei Sprachen | Weder EFF-01 noch EFF-02; es ist eine OCR-Entscheidung aus Plan 06.1-21 | Phase 10 benennt sie, Phase 11 traegt sie in den Store-Text |
| Ein anderes Modell oder eine andere Quantisierung | Aendert die Trefferqualitaet und erzwingt einen Reindex ueber 51.961 Dokumente | Eigenes Milestone |
| Modell-Entladung nach Leerlauf | Teil 3.4, mit Zahlen abgelehnt | Bleibt "Future Requirement" |
| Anfassen des ACL-Vorfilters oder des PHP-Rechecks | Sequenz-Zwang 4 der Roadmap | Nirgends in v1.1 |
| Ein Millisekunden-Deckel als CI-Tor | Wuerde fuer Runner-Last rot werden, nicht fuer die benannte Sache | Nirgends |

---

## Don't Hand-Roll

| Problem | Nicht bauen | Stattdessen | Warum |
|---|---|---|---|
| Beweisen, dass das Modell einmal geladen wird | Eine RSS-Messung mit Schwellwert | `load_count()` plus `findling.tools.one_load` | Ein Zaehler unterscheidet einen Cache-Treffer von einem billigen zweiten Laden; keine Speichermessung auf einem geteilten Runner kann das. Steht so im Modulkopf von `one_load.py` |
| Ein Volumen fuer eine Messung aufsetzen | Ein neues Seed-Skript | `one_load.seed_volume()` | Baut Index, `state.db`, ACL-Zeile und leeren Vektorbestand in einem Aufruf |
| Suchlast erzeugen | Ein eigenes curl-Bundle | `scripts/ops/search_load.py` | Geht ueber die OCS-Route, liest `anon` und `memory.current` mit, kennt das Budget und sagt selbst, dass es nichts zusagt |
| RSS ueber die Zeit abtasten | Ein eigener Sampler | `scripts/ops/rss_sampler.sh` plus `rss_digest.py` | In beiden Messreihen bereits benutzt, Ausgabeformat ist bekannt |
| Kalten Seitencache erzwingen | `sync` und Hoffnung | Das Muster aus `measure.yml`, Schritt C: `--privileged --user 0` und `drop_caches`, mit `cold_not_enforced` als Befund statt als Fehler | Ein Kaltlauf, der nicht kalt war, muss sich selbst melden |
| Grundlast Schritt fuer Schritt aufschluesseln | Ein neues Skript | `docs/measurements/2026-09-nachmessung-m7g/skripte/63-grundlast.sh` verfeinern | Die Vergleichbarkeit mit der Nachmessung haengt daran, dass es dasselbe Skript ist |

---

## Common Pitfalls

### Fallstrick 1: Einwortige Testzeilen messen die Regel, nicht das Laden

**Was schiefgeht:** Ein Test sucht "Vertrag", erwartet ein Laden und bekommt keins.
**Warum:** Seit dem Nachtrag 06.1-20 bleibt eine einwortige Zeile lexikalisch
(`api/search.py:230`, `rewritten.one_term`). Ebenso schalten Anfuehrungszeichen, ein Minus,
ein Feld, ein Dateityp und `titleOnly` die semantische Haelfte ab.
**Vermeidung:** Immer zwei Woerter, beide im Dokumenttext. `one_load` macht es vor.
**Warnzeichen:** `engine_loads_after_search = 0`.

### Fallstrick 2: Auf einem leeren Volumen messen

**Was schiefgeht:** Die Suche kehrt um, bevor sie Wortliste, Automat oder Modell erreicht, und
jede Zahl danach ist gruen fuer nichts.
**Warum:** `read_side()` antwortet `None`, wenn `state.db` oder das Indexverzeichnis fehlen
(`api/resources.py:300`).
**Vermeidung:** Volumen seeden. Die Reihenfolge im Tor ist die Leerlaufsperre: erst die
Suchseite, die allein auf eins kommen muss, dann der Arbeiter.
**Warnzeichen:** Ein Speicherunterschied im Kilobyte-Bereich, wie die 241 KB und 503 KB, die
`resilience.yml` als Rauschen benennt.

### Fallstrick 3: Die 2,5 Sekunden fuer die Grenze halten

**Was schiefgeht:** Ein Plan sichert 2.500 ms ab und uebersieht, dass ein einzelner
Containeraufruf schon bei 1.500 ms abgeschnitten wird, und dass der Kandidatenaufruf mehrfach
laufen kann.
**Vermeidung:** Beide Zahlen nennen, `Provider.php:57` und `ExAppService.php:89`, und den
Kaltstartaufschlag gegen die kleinere pruefen.
**Warnzeichen:** Ein Lauf mit null Fehlern und trotzdem fehlender Findling-Gruppe im Ergebnis.

### Fallstrick 4: Aus dem Zaehler eine Zusage ueber Tokenizer machen

**Was schiefgeht:** "Eine Engine je Prozess" wird als "ein Tokenizer je Prozess" gelesen, und
jemand legt die beiden Instanzen zusammen.
**Warum:** `enable_truncation` ist eine Eigenschaft des Objekts. Eine geteilte Instanz haette
den 1.024-Token-Deckel aus D-01 still auf 512 halbiert; die zweite Haelfte jedes langen
Dokuments wuerde aufhoeren zu existieren, ohne dass irgendwo etwas faellt.
`[VERIFIED: backend/src/findling/embed/model.py:192-204, .planning/STATE.md:159]`
Der Upstream warnt vor derselben Sache. `[CITED: https://pypi.org/project/semantic-text-splitter/]`
**Vermeidung:** Die Formulierung im Beleg praezisieren, bevor sie in Store-Text oder Bericht
wandert.

### Fallstrick 5: Einen Zeitdeckel als CI-Tor bauen

**Was schiefgeht:** Das Tor wird rot, wenn der Runner ausgelastet ist, und irgendwann hebt
jemand den Deckel, statt den Befund zu lesen.
**Vermeidung:** Zeit berichten, Zaehler und Struktur torieren. Dieses Repository hat die
Begruendung dafuer bereits ausformuliert (`resilience.yml`, Kommentar vor dem Ratschenschritt).

### Fallstrick 6: Den Vektorbestand mit faul machen

**Was schiefgeht:** Beim fauleren Bau der zweiten Spur wandert `open_vectors` mit nach hinten,
und der Loeschpfad findet keinen Bestand mehr, weil `attach_vectors` mit `None` lief.
**Warum:** `poller.py:1422` und `:1425` haengen am Vektorbestand; ein Grabstein muss die
Vektoren seiner Datei mitnehmen (D-21).
**Vermeidung:** `_wire_the_second_track` in zwei Haelften teilen. Nur Tokenizer und Splitter
werden faul, der Bestand bleibt eifrig.

---

## Runtime State Inventory

Diese Phase ist keine Umbenennung und keine Migration. Die Kategorien werden trotzdem
ausdruecklich beantwortet, weil ein moeglicher fauler Bau (Teil 3.3) das Verhalten eines
laufenden Containers aendert.

| Kategorie | Gefunden | Handlung |
|---|---|---|
| Gespeicherte Daten | Keine. Weder Vektorschema noch `state.db` noch `analyzer_version` werden beruehrt. `embedding_version` bleibt unveraendert, also kein Reindex | keine |
| Konfiguration lebender Dienste | Keine. Kein n8n, kein Datadog, keine externen Dienste in diesem Produkt | keine |
| OS-registrierter Zustand | Keine. Die Indexierung wird ueber AppAPI bewaffnet, nicht ueber Task Scheduler oder systemd | keine |
| Secrets und Umgebungsvariablen | `FINDLING_EMBED_ENABLED` und `FINDLING_EMBED_MODEL_DIR` bleiben unveraendert. `[VERIFIED: backend/src/findling/config.py:1082,1092]` | keine |
| Bauartefakte und Abbilder | Das Laufzeit-Abbild traegt Modell und Tokenizer als Konstanten der Modellstage. Eine Codeaenderung dieser Phase erzwingt einen Abbild-Neubau vor jeder Messung, und Abbild und Arbeitsbaum muessen per Baumhash uebereinstimmen, wie in der Nachmessung. `[VERIFIED: backend/Dockerfile; Nachmessung Abschnitt 1]` | Baumhash-Beweis in jeden Messplan |
| Angehaltene AWS-Box | Angehalten, nicht abgebaut. Der Datentraeger wurde am 07.09. teilweise zerstoert; `occ findling:index --restart` ist eingestellt, der naechste Start faehrt rund 19 Stunden Neuaufbau. `[MEASURED: Nachmessung Abschnitt 12a]` | **Nicht anfassen in Phase 7.** Gehoert Phase 10 |

---

## Environment Availability

| Abhaengigkeit | Gebraucht fuer | Verfuegbar | Fassung | Ausweichweg |
|---|---|---|---|---|
| Modellartefakte lokal (`tokenizer.json`, `model.onnx`) | Die Messung aus Teil 3.2 lokal fahren | **nein** | `FINDLING_EMBED_MODEL_DIR` ist leer, keine `tokenizer.json` auf der Maschine | Im Abbild messen, so wie `63-grundlast.sh` es tut |
| `onnxruntime` | Sitzung | ja, im venv | 1.29.0 | keiner noetig |
| `tokenizers` | Tokenizer | ja, im venv | 0.23.2 | keiner noetig |
| `semantic_text_splitter` | Splitter | ja, im venv | 0.32.0 | keiner noetig |
| Docker auf der Entwicklungsmaschine | Abbild bauen und messen | vorausgesetzt (WSL2, `scripts/dev/compose.yaml`) | nicht geprueft | CI |
| GitHub-Runner amd64 | Weg A und Weg B | ja | `ubuntu-24.04` | keiner |
| GitHub-Runner arm64 | Weg C | ja | `ubuntu-24.04-arm`, bereits in `measure.yml` benutzt | AWS-Box, aber die gehoert Phase 10 |
| AWS-Box m7g.large | p95 ueber den vollen Korpus | angehalten, Owner-Deckel 8 Stunden | | **Nicht in dieser Phase anfahren** |

**Fehlend ohne Ausweichweg:** keins.
**Fehlend mit Ausweichweg:** die lokalen Modellartefakte. Alles, was sie braucht, laeuft im
Abbild oder in CI.

---

## Standard Stack

Diese Phase fuehrt **keine neue Abhaengigkeit** ein. Empfohlen wird ausdruecklich, keine
hinzuzufuegen: alles Noetige liegt im Baum.

| Baustein | Fassung | Zweck | Herkunft |
|---|---|---|---|
| `onnxruntime` | 1.29.0 | Inferenzsitzung | `backend/.venv/Lib/site-packages/onnxruntime-1.29.0.dist-info` `[VERIFIED: Verzeichnislisting]` |
| `tokenizers` | 0.23.2 | Tokenizer, beide Instanzen | ebenda `[VERIFIED]` |
| `semantic_text_splitter` | 0.32.0 | Chunkgrenzen ueber echte Token | ebenda `[VERIFIED]` |
| `tantivy` | 0.26.0 | Lexikalischer Index | CLAUDE.md, Kernentscheidungen |
| `sqlite-vec` | 0.1.9 | Vektorbestand, int8, Brute Force | CLAUDE.md, Kernentscheidungen |

### Package Legitimacy Audit

**Nicht anwendbar.** Diese Phase installiert kein externes Paket. Alle oben genannten Fassungen
sind bereits im gepinnten Lockfile und im Abbild und wurden in v1.0 eingefuehrt und geprueft.
Sollte der Planner wider Erwarten ein Paket aufnehmen wollen, gilt das Gate aus dem
Projektstandard: Registry-Pruefung im richtigen Oekosystem, `slopcheck`, und ein
`checkpoint:human-verify` vor dem Install.

---

## Code Examples

### Der Halter, wie er heute steht

```python
# Quelle: backend/src/findling/embed/engine.py:58-82
def shared_model() -> EmbeddingModel:
    global _ENGINE

    resolved = settings()
    with _LOCK:
        if _ENGINE is not None and _ENGINE[0] == resolved.embed_model_dir:
            return _ENGINE[1]
        model = EmbeddingModel(
            resolved.embed_model_dir,
            batch_size=resolved.embed_batch_size,
            sequence_len=resolved.embed_sequence_len,
        )
        _ENGINE = (resolved.embed_model_dir, model)
        return model
```

### Die Stelle, an der der eifrige Bau haengt

```python
# Quelle: backend/src/findling/worker/poller.py:1420-1425
if self._owns_resources and self._embed_enabled and self._vectors is None:
    self._wire_the_second_track()
# Der Loeschpfad der Zustandsdatenbank braucht denselben Handle: ein Grabstein
# muss die Vektoren seiner Datei mitnehmen (D-21).
self._store.attach_vectors(self._vectors)
```

Ein fauler Bau muss **oberhalb** dieser Zeile den Vektorbestand behalten und nur Tokenizer und
Splitter verschieben.

### Das Muster, nach dem ein Zeittor **nicht** gebaut wird

```yaml
# Quelle: .github/workflows/resilience.yml, Kommentar vor dem Ratschenschritt
# So die Reihe bleibt eine Beobachtung, die Laeufe dieses Workflows sammeln sie,
# und das Tor ueber die beiden Ersparnisse ist ein Zaehler im Schritt darunter.
# Ein geerbter Deckel waere schlechter gewesen als keiner.
```

---

## State of the Art

| Frueherer Stand | Heutiger Stand | Wann geaendert | Bedeutung |
|---|---|---|---|
| Suchseite und Arbeiter bauen je eine `EmbeddingModel`-Instanz | Beide ziehen aus `shared_model()` | Plan 06.1-02, 06.09.2026 | 276 MB dauerhaft weg, in der Suchphase gemessen 712,6 MB |
| Ein geworfenes Oeffnen wird dauerhaft als "Modell fehlt" gemerkt | Fehlende Artefakte dauerhaft, geworfenes Oeffnen nur `LOAD_RETRY_SECONDS = 300` | Plan 06.1-17 nach dem Bug-Audit | Ein Container, dem kurz die Luft ausging, bekommt seine Semantik ohne Neustart zurueck |
| Der Lock haelt ueber den ganzen Aufruf | Der Lock haelt nur ueber Laden und Tokenizer, der Graph laeuft ausserhalb | Plan 06.1-17 nach dem Perf-Audit M1 | Eine Suche wartet auf eine Charge und nicht auf ein ganzes Dokument |
| Die Spitze gehoert der ersten semantischen Suche | Die Spitze gehoert der OCR-Phase mit drei Sprachen | Nachmessung 07.09.2026 | Jeder weitere Speicherfix am Modell zielt auf die falsche Stelle |
| Der Messbericht nennt einen zweiten deutschen Zerlegungsautomaten als Posten | Es gibt ihn nicht, `_CACHED_GERMAN` ist ein prozessweiter Cache mit Zaehler | Plan 06.1-02, Falsifikation vor Umbau | Muster fuer Teil 3.2 dieser Recherche |

**Ueberholt und nicht wiederzubeleben:**

- "Die Semantik kostet 595 MB Grundlast" aus 06-11 in der Lesart "das Modell liegt im
  Leerlauf im Speicher". Es liegt nicht: Schritt 13 kostet 0,0 MB. Die 595 MB sind zum
  groessten Teil Tokenizer und Splitter.
- "Ein Entladetimer spart 276 MB an der Spitze." Falsch, seit die Spitze der OCR-Phase gehoert.

---

## Assumptions Log

| # | Aussage | Abschnitt | Risiko, wenn falsch |
|---|---|---|---|
| H1 | Die +274,3 MB von Schritt 12 sind zu einem grossen Teil eine zweite Materialisierung des Tokenizers im Splitter, nicht der Preis des Chunkerlaufs | Teil 3.2 | Ein Gap-Plan zielte auf die falsche Stelle. **Deshalb steht die Messung vor dem Bau, mit Abbruchbedingung** |
| H2 | Die +269,4 MB von Schritt 11 sind Modulimport plus erste Instanz, nicht die Instanz allein | Teil 3.2 | Der erwartete Gewinn eines faulen Baus waere kleiner als gedacht. Dieselbe Messung klaert es mit |
| B1 | Kaltstartaufschlag rund 850 ms, gerechnet aus 1.332,1 minus 481,6 | Teil 2.1 | Die Rechnung mischt drei kalte Anfragen mit zehn warmen. Die Richtung stimmt, die zweite Stelle nicht |
| B2 | Bei acht gleichzeitigen Suchen wuerde ein Kaltstart das Budget reissen (rund 2.765 ms) | Teil 2.2 | Ein Argument gegen die Entladung waere schwaecher. Die anderen zwei Argumente tragen allein |
| A1 | `scripts/` liegt nicht im Laufzeit-Abbild, `vector_distances.py` laeuft also nie im Container | Teil 1.2 | Es gaebe doch einen Pfad mit eigener Instanz. Leicht gegen `backend/Dockerfile` nachpruefbar; die Stage-Beschreibung sagt "nichts von ihnen" ausser venv, frpc und Modell |
| A2 | Der Splitter des Chunkers laesst sich hinter die erste Einbettungszeile schieben, ohne die `_embed_ready`-Zusage zu verletzen | Teil 3.3 | Zeilen koennten in die `repeatedly_stuck`-Schleife laufen. Die drei Auflagen in Teil 3.3 sind genau dafuer da |

---

## Open Questions

1. **Wieviel von den 543,7 MB ist wirklich verschiebbar?**
   - Bekannt: die beiden Schritte kosten zusammen 543,7 MB, gemessen auf arm64.
   - Unklar: die Aufteilung in Modulimport, erste Instanz, Splitterkopie und Chunkerlauf.
   - Empfehlung: Plan 07-03 mit Abbruchbedingung bei 100 MB. Messen im Abbild, nicht lokal.

2. **Gilt die Aufteilung auf amd64 genauso?**
   - Bekannt: die Tokenzahlen sind architekturunabhaengig (06-02, auf das letzte Token
     geprueft). Der Speicherverbrauch ist es nicht zwingend.
   - Empfehlung: dieselbe feinere Messung in beiden Matrix-Aesten von `measure.yml` fahren.
     Kostet zwei Containerlaeufe.

3. **Gehoert der Engine-Zustand in `StatusResponse` in diese Phase?**
   - Bekannt: Kriterium 3 verlangt ihn, heute liefert nur die Einzeldatei-Diagnose den Befund.
   - Unklar: ob der Owner eine PHP-Aenderung in einer Phase will, die sonst reiner Beleg ist.
   - Empfehlung: aufnehmen, als eigener kleiner Plan. Sonst gilt ein Phasenkriterium als
     erfuellt, das es nur halb ist.

4. **Soll `one_load` die Kaltstartdauer melden, oder gehoert sie in `integration.yml`?**
   - Beide. `one_load` liefert sie billig auf jedem Push als Reihe, `integration.yml` liefert
     die eine belastbare Zahl ueber den echten PHP-Weg.
   - Empfehlung: Weg A als Reihe, Weg B als Berichtszahl. Weg C nur, wenn eine
     arm64-Entsprechung im Bericht stehen soll.

5. **Wie lautet die Kernaussage der Phase, wenn nichts gebaut wird?**
   - Vorschlag: "Die gemeinsame Engine steht seit dem 06.09.2026 und ist auf jedem Push
     abgesichert. Sie spart in der Suchphase 712,6 MB und an der Gesamtspitze 25,1 MB, weil die
     Spitze inzwischen der OCR-Phase gehoert. Die erste semantische Suche eines frisch
     gestarteten Containers antwortete auf der Zielhardware in 1.332,1 ms gegen ein Budget von
     2.500 ms."
   - Das ist eine Faktenliste nach der Kurztext-Regel und traegt eine Zahl im Text.

---

## Sources

### Primaer (HIGH confidence, in dieser Sitzung gegen den Baum geprueft)

- `backend/src/findling/embed/engine.py`, `embed/model.py`, `embed/chunker.py`
- `backend/src/findling/api/resources.py`, `api/search.py`, `api/snippets.py`, `api/diagnose.py`, `api/status.py`
- `backend/src/findling/worker/poller.py`, `index/search.py`, `tools/one_load.py`, `config.py`
- `backend/tests/test_embed_engine.py`, `backend/tests/test_one_load.py`
- `php/lib/Search/Provider.php`, `php/lib/Service/ExAppService.php`, `php/lib/Service/AdminViewService.php`
- `.github/workflows/resilience.yml`, `measure.yml`, `integration.yml`
- `backend/Dockerfile`
- `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `CLAUDE.md`

### Messreihen dieses Repositoriums (HIGH, Rohdaten benannt)

- `docs/measurements/2026-09-nachmessung-m7g/README.md` und
  `rohdaten/63-grundlast.txt`, `rohdaten/64-spitze.txt`, `rohdaten/64-stufe-01.json`,
  `rohdaten/67-stufe-1.json`
- `docs/measurements/2026-09-05-semantiklauf-m7g/README.md`, Abschnitt "Der Befund, der die
  Spitze erklaert"
- `.planning/milestones/v1.0-phases/06.1-launch-haertung-vor-der-store-abgabe/`:
  `06.1-02-SUMMARY.md`, `06.1-04-SUMMARY.md`, `06.1-AUDIT-BUGS.md`, `VERIFICATION.md`

### Sekundaer (MEDIUM, offizielle Dokumentation)

- [semantic-text-splitter auf PyPI](https://pypi.org/project/semantic-text-splitter/) - Hinweis,
  dass ein Tokenizer mit aktiver Truncation die Chunkgroesse deckelt
- [benbrandt/text-splitter](https://github.com/benbrandt/text-splitter) - Quelle und API
- [text-splitter, Diskussion 22](https://github.com/benbrandt/text-splitter/discussions/22) -
  Ankuendigung der Hugging-Face-Unterstuetzung; **enthaelt keine Aussage zum Kopierverhalten**

### Nicht gefunden, ausdruecklich vermerkt

- Keine offizielle Aussage dazu, ob `from_huggingface_tokenizer` den Tokenizer auf die
  Rust-Seite kopiert oder eine Referenz haelt. Deshalb ist H1 eine Hypothese und keine
  Feststellung, und deshalb steht die Messung vor dem Bau.

---

## Metadata

**Konfidenz im Einzelnen:**

- Bestandsaufnahme EFF-01: **HIGH**. Vollstaendige Suche ueber den Baum, jede Aufrufstelle mit
  Datei:Zeile, Zaehler, Tests und CI-Tor gelesen.
- Bestandsaufnahme EFF-02: **HIGH** fuer die Zahl (Rohdatei gelesen), **HIGH** fuer die
  1,5-s-Aufrufdecke (beide PHP-Konstanten gelesen), **MEDIUM** fuer die
  Nebenlaeufigkeitsrechnung (gerechnet, nicht gemessen).
- Restluecke: **MEDIUM**. Die 543,7 MB sind gemessen, die Zuordnung ist es nicht. Genau
  deshalb ist der empfohlene Plan eine Messung mit Abbruchbedingung.
- Ablehnung der Modell-Entladung: **HIGH**. Drei unabhaengige Gruende, zwei davon gemessen.
- Messbarkeit ohne die Box: **HIGH**. Alle drei Wege stehen auf vorhandenen Workflows und
  vorhandenen Werkzeugen.
- Diagnose-Luecke aus Kriterium 3: **HIGH**. `StatusResponse` vollstaendig gelesen, kein Feld
  vorhanden.

**Recherchedatum:** 2026-09-08
**Gueltig bis:** rund 30 Tage. Die Aussagen haengen am Repo-Stand und an zwei Messreihen, nicht
an einem beweglichen Oekosystem. Aendert jemand `worker/poller.py`, `embed/` oder
`resilience.yml`, ist Teil 1 neu zu pruefen.
