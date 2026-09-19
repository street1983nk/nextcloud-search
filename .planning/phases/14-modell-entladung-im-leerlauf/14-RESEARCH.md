# Phase 14: Modell-Entladung im Leerlauf , Research

**Recherchiert:** 2026-09-19
**Domain:** RSS-Rückgabe eines langlebigen Python-Containers (onnxruntime + tokenizers + glibc), Leerlauf-Erkennung in einer asyncio-Lifespan, Degradationspfad des Suchwegs
**Confidence:** HIGH für die Integrationspunkte (direkt am Quellcode dieses Repos gelesen, Dateien und Zeilen benannt), HIGH für die Speicher-Mechanik (in dieser Sitzung im Basis-Image gemessen), MEDIUM für die aarch64-Zahlen (nur emuliert gemessen, siehe Abschnitt 3.3)

---

## Summary

Die Phase hat fünf Anforderungen, aber nur eine echte Unbekannte, und die ist in dieser
Sitzung **gemessen und beantwortet worden**: gibt der Container den Speicher nach einem
Loslassen an das Betriebssystem zurück. Die Antwort ist ja, aber nur mit `malloc_trim(0)`.
Ein `gc.collect()` allein gibt zwischen 5 und 20 Prozent zurück, `malloc_trim(0)` danach
gibt 92 bis 99 Prozent des Tokenizers und den Löwenanteil der Sitzung zurück. Damit ist
das Risiko aus MEM-04 nicht beseitigt (der Vorprüflauf auf Zielarchitektur bleibt Pflicht
und ist Erfolgskriterium 1), aber es ist von "könnte das ganze Feature entwerten" auf
"bestätige die Zahl auf aarch64" geschrumpft.

Der zweite Befund ist nicht Speicher, sondern Zeit. Der eigene Messbericht belegt für den
10.09.2026 eine Kaltstart-Suche von 1.838,4 ms gegen eine harte Aufrufdecke von 1.500 ms,
mit `cURL error 28` im Nextcloud-Protokoll und HTTP 200 plus leerer Trefferliste für den
Nutzer. Eine Entladung im Leerlauf macht aus diesem Einzelvorfall ein Alltagsereignis,
falls der Suchpfad weiterhin synchron lädt. Der Umbau dagegen ist klein und liegt an einer
Naht, die es schon gibt: `EmbeddingModel.embed_query` darf nicht mehr laden dürfen,
`EmbedOutcome.unavailable()` ist der bereits getestete Weg zu rein lexikalischen Treffern
(D-19), und das Nachwärmen gehört in dieselbe Lifespan-Aufgabe, die auch entlädt.

Der dritte Befund ist der Ort der Vorprüfung. Es braucht **keine bezahlte Box**:
`.github/workflows/measure.yml` ist bereits eine manuell ausgelöste Messwerkstatt, die mit
`ubuntu-24.04-arm` (`role: target`) gegen das ausgelieferte Image läuft, `--privileged`
und `drop_caches` bereits benutzt und ihre Ergebnisse als Artefakt ablegt. Eine vierte
Messung "D, RSS-Rückgabe" in dieser Datei ist der billigste und ehrlichste Weg zu
Erfolgskriterium 1, und sie kostet Runner-Minuten statt Dollar.

**Primary recommendation:** Wave 1 ist der Vorprüflauf (`findling.embed.bench --mode
rss-release` plus Messung D in `measure.yml`, aarch64-Lauf, Ergebnis dokumentiert), und
erst sein Ergebnis gibt Wave 2 frei. Wave 2 baut in dieser Reihenfolge: ein Schalter in
`config.py`, ein `release()` an beiden Haltern, eine dritte asyncio-Aufgabe in
`main.lifespan`, der Nicht-Lade-Zweig in `embed_query`, das Nachwärmen, und zuletzt die
Neuformulierung von `tools/one_load.py` samt Gate. Die engineState-Wortwahl ist ein
Owner-Checkpoint und wird hier bewusst nicht entschieden.

---

## Project Constraints (from CLAUDE.md)

| Direktive | Quelle | Folge für diese Phase |
|---|---|---|
| Hardware-Ziel 4 bis 8 GB RAM, ARM-tauglich, CPU-only, RAM-Budget hart einplanen | Constraints | Die Zielzahl ist eine aarch64-Zahl, keine x86-Zahl |
| Python-Qualitätsgates: ruff-Vollregelsatz, pyright basic, vulture, CI-Gates, lokal grün VOR Commit | Constraints | Jeder Plan endet mit dem lokalen Gate-Lauf; `ctypes`-Aufruf braucht einen pyright-tauglichen Typ |
| Code Englisch, Projektkommunikation Deutsch, keine Em-Dashes, echte Umlaute nur in deutscher Prosa, nie in Code | Constraints | Neue Konstanten und Variablennamen Englisch; die Admin-Sätze Deutsch in den Katalogen |
| Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Phase-Abschluss fixen | Owner-Regeln 15.08.2026 | Ein Audit-Plan gehört ans Phasenende |
| Launch-Härtung vor der Store-Abgabe, nicht nur Happy Path | Owner-Regeln 06.09.2026 | Gilt in Phase 16, nicht hier, aber die Fehlerpfade dieser Phase (libc ohne `malloc_trim`, Entladung während Indexlauf) gehören schon hier getestet |
| Keine Inhalte verlassen den Server, keine Telemetrie | Constraints | Die Messausgabe darf keinen Suchtext und keinen Dateinamen tragen (T-02-14, T-06-06) |
| Basis-Image `python:3.13-slim-trixie` | Kernentscheidungen | glibc, also `malloc_trim` vorhanden; der Schutzschalter bleibt trotzdem Pflicht |

---

## Phase Requirements

| ID | Beschreibung (gekürzt) | Research Support |
|---|---|---|
| MEM-01 | Eine Umgebungsvariable, TTL in Sekunden, 0 = aus, ab Werk aus | Abschnitt 6 (Konfiguration): Namensdissens aufgelöst, `_bounded_int_from_environment` reicht **nicht**, Precedent `_overlap_from_environment` benannt, info.xml-Block ist die 16. Variable |
| MEM-02 | Beide Speicherhalter frei (Engine UND Poller-Cutter/Tokenizer) | Abschnitt 4 (zwei Halter, zwei Freigaben) plus die gemessenen Zahlen in Abschnitt 3; der Poller-Halter ist der **größere** |
| MEM-03 | Erste Suche nach Entladung lexikalisch innerhalb 1,5 s, Nachwärmen im Hintergrund | Abschnitt 5 (Degradationsnaht in `embed_query`, drei Aufrufer, Single-Flight-Warm) plus der Belegvorgang vom 10.09.2026 |
| MEM-04 | Vorprüflauf belegt RSS-Rückgabe auf Zielhardware VOR dem Bau, negatives Ergebnis ist legitim | Abschnitt 3 (in dieser Sitzung gemessen) plus Abschnitt 3.4 (`measure.yml` Messung D als kostenloser aarch64-Weg) |
| MEM-05 | one_load-Zusage neu formuliert, Admin-Seite zeigt den Zustand, Gate prüft die neue Zusage | Abschnitt 7 (die Zusage in Zahlen), Abschnitt 8 (Owner-Checkpoint Wortwahl, beide Zweige mit Preis, **nicht entschieden**) |

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|---|---|---|---|
| Leerlauf-Uhr und Auslöser | Backend, `main.lifespan` (asyncio) | , | Nur die Lifespan hat den Lebenszyklus mit Stopp-Event; der Poller scheidet aus, weil ein stummgeschalteter Poller `run_once` nie wieder betritt (`poller.py:543`) |
| Freigabe der Suchseite | Backend, `embed/model.py` + `embed/engine.py` | , | Der Halter ist der einzige Ort, der über Laden entscheidet; Entladen gehört an dieselbe Stelle |
| Freigabe der Indexseite | Backend, `worker/poller.py` | `embed/engine.py` fragt nicht hinein | Abhängigkeitsrichtung: `worker/` importiert aus `embed/`, nie umgekehrt. Der Poller lässt selbst los |
| Lexikalische Antwort bei kalter Engine | Backend, `embed/model.py::embed_query` | `index/search.py` (bestehender D-19-Zweig) | Eine Naht statt drei: `api/search.py`, `api/snippets.py` und `api/diagnose.py` bauen je eine `SemanticSide` |
| Nachwärmen im Hintergrund | Backend, dieselbe Lifespan-Aufgabe | `api/search.py` als Auslöser auf dem Loop | Die Aufgabe hat den Loop und das Stopp-Event; der Route-Handler hat den Anlass |
| Anzeige des Zustands | PHP, `AdminViewService` + `admin.php` + `admin.js` | Backend liefert nur das Protokollwort | Der Container meldet nie einen Text, den ein Admin liest (T-07-01) |
| RSS-Messung | CI, `.github/workflows/measure.yml` auf `ubuntu-24.04-arm` | `embed/bench.py` als Werkzeug im Image | Zielarchitektur ohne bezahlte Box; die Box (Phase 15) misst danach nur noch das A/B des Schalters |

---

## 3. Der Vorbefund: was in dieser Sitzung gemessen wurde

### 3.1 Was gemessen wurde und wie

Ein Wegwerfcontainer auf dem Basis-Image `python:3.13-slim-trixie`, mit den echten
Artefakten aus `.dev/model/` (`tokenizer.json` 17.082.730 Bytes, `model.onnx` 118.101.091
Bytes) schreibgeschützt eingehängt, `onnxruntime==1.30.0` und `tokenizers` frisch
installiert, `enable_cpu_mem_arena = False` wie in `_open_session`, `VmRSS` aus
`/proc/self/status` nach dem Muster von `index/wordlist.py::rss_bytes`.
[VERIFIED: eigener Lauf, 2026-09-19, Docker 29.5.2]

Das ist derselbe Aufbau wie `scripts/dev/measure_wordlist.sh` ihn für die Wortliste
benutzt, und es ist das Muster, das der Vorprüflauf übernehmen sollte.

### 3.2 Die Zahlen auf x86_64 (nativ)

| Schritt | RSS | Delta |
|---|---:|---:|
| 00 Interpreter | 9,4 MB | , |
| 01 `import tokenizers` | 15,9 MB | +6,5 |
| 02 `Tokenizer.from_file` (0,57 s) | 298,6 MB | **+282,7** |
| 03 ein `encode` | 298,8 MB | +0,2 |
| 04 Tokenizer losgelassen + `gc.collect()` | 241,9 MB | **,56,9 (20,1 %)** |
| 05 `malloc_trim(0)` , Rückgabewert 1 | **18,7 MB** | **,223,2 (79,0 %)** |
| 06 `import onnxruntime, numpy` | 49,5 MB | +30,8 |
| 07 `InferenceSession` (0,66 s) | 182,1 MB | +132,6 |
| 08 erster `run` (0,004 s) | 475,9 MB | **+293,8 (Aktivierungen)** |
| 09 nach 20 weiteren `run` | 475,9 MB | +0,0 |
| 10 Sitzung + Tokenizer losgelassen + `gc.collect()` | 349,3 MB | ,126,6 |
| 11 `malloc_trim(0)` , Rückgabewert 1 | **61,6 MB** | **,287,7** |

**Rest nach vollständiger Entladung: 61,6 MB gegen 49,5 MB Import-Grundlinie, also 12,1 MB,
die nicht zurückkommen.** [VERIFIED: eigener Lauf]

### 3.3 Die Zahlen auf aarch64 (emuliert, qemu)

| Schritt | RSS | Delta |
|---|---:|---:|
| 00 Interpreter | 32,9 MB | , (qemu-Aufschlag rund 23 MB) |
| 02 Tokenizer geladen (2,00 s) | 329,3 MB | +285,5 |
| 04 losgelassen + `gc.collect()` | 315,3 MB | **,14,0 (nur 4,9 %)** |
| 05 `malloc_trim(0)` | **53,6 MB** | **,261,7 (91,7 %)** |
| 07 `InferenceSession` (6,99 s) | 327,5 MB | +190,2 |
| 08 erster `run` (0,841 s) | 618,2 MB | +290,7 |
| 10 losgelassen + `gc.collect()` | 529,1 MB | ,89,8 |
| 11 `malloc_trim(0)` | 200,2 MB | ,328,9 |

**Diese Zahlen sind nicht zitierfähig.** qemu-Emulation trägt eigene Übersetzungspuffer,
die mit ausgeführtem Code wachsen; der Rest von 62,9 MB über der Import-Grundlinie ist
mit hoher Wahrscheinlichkeit zum großen Teil qemu und nicht onnxruntime. Auch die Zeiten
(6,99 s für die Sitzung) sind Emulationszeiten. Was die Emulation **trotzdem** zeigt und
was architekturunabhängig ist: die Aufteilung zwischen `gc.collect()` und `malloc_trim(0)`
ist auf aarch64 noch deutlicher als auf x86_64. [VERIFIED: eigener Lauf, mit der genannten
Einschränkung]

### 3.4 Die drei Schlussfolgerungen, die daraus für den Plan folgen

1. **`malloc_trim(0)` ist der wirksame Schritt, nicht die Politur.** Ein Entlader, der nur
   `del` plus `gc.collect()` macht, gibt zwischen 5 und 20 Prozent zurück und wäre genau
   der Fall aus Pitfall 10 ("die Zahl fällt um zwanzig Megabyte statt um vierhundert").
   Die Reihenfolge Referenzen lösen, `gc.collect()`, `malloc_trim(0)` ist nicht
   verhandelbar, und der Rückgabewert von `malloc_trim` (1 = es wurde etwas zurückgegeben)
   gehört in die Messausgabe.
2. **Der Aktivierungsspeicher des ersten `run` bleibt liegen und kommt erst mit der
   Entladung zurück.** +293,8 MB beim ersten `run`, +0,0 MB über zwanzig weitere, und er
   verschwindet nicht von selbst, obwohl `enable_cpu_mem_arena = False` gesetzt ist. Das
   ist die quantitative Begründung dafür, dass die Messgröße "Rückkehr zur Grundlast nach
   einem Indexlauf" heißt und nicht "Grundlast minus X": nach einem Indexlauf steht genau
   dieser Posten im Container.
3. **Ein Bodensatz bleibt und muss im Bericht stehen.** Die Modulimporte von onnxruntime
   und numpy (30,8 MB auf x86_64) kommen nie zurück, weil die Module geladen bleiben. Die
   Entladung führt also nicht auf die Grundlast eines Containers, der nie eingebettet hat,
   sondern auf diese plus den Import-Bodensatz. Der Store-Text darf das nicht
   verschweigen.

### 3.5 Wo der Vorprüflauf laufen soll (Erfolgskriterium 1, "Zielhardware")

`.github/workflows/measure.yml` ist bereits die Messwerkstatt dieses Projekts
[VERIFIED: Datei gelesen]:

- `workflow_dispatch`-only, also kein Lauf auf jedem Push
- Matrix mit `arch: arm64 / runner: ubuntu-24.04-arm / role: target` und dem Kommentar
  "The target hardware of this app is a small ARM box. This is the number the phase is
  decided on"
- zieht das **ausgelieferte** Image per Digest aus ghcr.io, baut nichts neu
- schreibt `machine.txt` mit Runner, `uname -m`, Kernel, `nproc`, Image-Digest, Commit
- benutzt bereits `--privileged` und `--user 0` für `drop_caches` (Messung C), mit
  ausgeschriebener Begründung für die Flags
- lädt alles als Artefakt hoch, das von Hand nach `docs/measurements/` kopiert wird

Eine **Messung D, RSS-Rückgabe** in dieser Datei ist damit der direkte Weg zu Kriterium 1:
Zielarchitektur, ausgeliefertes Image, dokumentierte Maschine, null Dollar. Die bezahlte
Box in Phase 15 misst danach nur noch das, was sie wirklich allein kann: das A/B über den
MEM-01-Schalter auf einem echten Bestand, mit und ohne warmen Seitencache.

**Achtung, Vergleichbarkeit:** `ubuntu-24.04-arm` ist ein 4-Kern-Runner und nicht
`m7g.large`. Die **Rückgabequote** (Prozent des Geladenen, das zurückkommt) ist die
übertragbare Größe; die **Ladezeit in Millisekunden** ist es nicht und muss weiterhin von
der Box kommen, weil sie den Default der TTL und die 1,5-Sekunden-Frage entscheidet.

---

## 4. Die zwei Speicherhalter und wie jeder losgelassen wird (MEM-02)

### 4.1 Wo sie stehen

| Halter | Datei | Was daran hängt | Gemessener Preis |
|---|---|---|---|
| Suchseite | `embed/model.py::EmbeddingModel._engine` (`model.py:319`) | `_Engine(encoder, session, accepted, outputs)`, ein frozen dataclass mit Tokenizer-Instanz und ORT-Sitzung | Tokenizer 265,8 MB, Sitzung plus Aktivierungen laut 3.2 rund 426 MB |
| Indexseite | `worker/poller.py::_chunker` + `_model` (`poller.py:416-417`) | Die Closure `cut` hält `tokenizer` und `splitter`; `_model` ist dieselbe Instanz wie in der Suchseite | Tokenizer-Instanz 2 = 216,6 MB, Splitterbau 273,1 MB, fünf Posten zusammen 542,8 MB |

Quelle der Postenzahlen: `docs/measurements/2026-09-grundlast-fein/README.md` und
`docs/measurements/2026-09-vergleichsmessung-m7g/README.md` Abschnitt 5.2
[VERIFIED: eigene Messberichte, gelesen]

**Der größere Posten ist der Poller-Halter, nicht die Suchseite.** Wer nur `_engine`
freigibt, liefert auf einer Box, die einmal indexiert hat, die halbe Zahl. Das ist die
inhaltliche Begründung für MEM-02.

### 4.2 Die Indexseite ist einfacher, als sie aussieht

`_build_the_cutter` (`poller.py:1564`) baut `tokenizer` und `splitter` als lokale
Variablen und schließt sie in die Funktion `cut` ein, die dann `self._chunker` wird.
Es reicht also:

```python
self._chunker = None   # die Closure faellt, mit ihr tokenizer und splitter
self._model = None
```

Beides zusammen, nie eines von beiden: `_embed_ready` und der Kopf von
`_build_the_cutter` lesen das Paar, und ein halb entladener Cutter würde beiden
"gebaut" antworten (`poller.py:1705`). Der Wiederaufbau braucht keinen neuen Code:
`_build_the_cutter` kehrt am Kopf zurück, wenn beides gesetzt ist, und baut sonst
neu (`poller.py:1130` ruft ihn bereits bedingt auf).

**Was beim Entladen nicht angefasst werden darf:** `_cutter_absent` (Eigenschaft der
Installation) und `_cutter_failed_at` (der laufende Cooldown). Beide zurückzusetzen wäre
Anti-Pattern 7 aus ARCHITECTURE.md und würde eine Abkühlphase still abbrechen.

### 4.3 Die Suchseite und warum sie keinen Umbau der Sperren braucht

`_embed` bindet die Engine unter dem Lock an eine lokale Variable und lässt `run()`
bewusst außerhalb des Locks laufen (`model.py:421-433`). Wird `self._engine` in genau
diesem Moment aus einem anderen Thread auf `None` gesetzt, hält die lokale Referenz das
`_Engine`-Objekt am Leben, bis die Funktion zurückkehrt. Referenzzählung, kein Segfault,
keine neue Sperre. [VERIFIED: Quellcode gelesen; die Zusage des onnxruntime-Maintainers zu
`Run()` aus mehreren Threads steht als Kommentar an derselben Stelle]

Was die Freigabe trotzdem braucht:

1. **Unter `self._lock`**, damit sie sich nicht mit `_load()` überkreuzt.
2. **Eine Identitätsprüfung**, damit eine Freigabe, die mit einem gleichzeitigen Laden
   kollidiert, nicht die frisch geladene Engine wegwirft. Das ist keine Theorie: das
   Nachwärmen aus MEM-03 läuft parallel zur Entlade-Aufgabe.
3. **Der Aufruf aus der Lifespan-Aufgabe über `asyncio.to_thread`**, damit `gc.collect()`
   und `malloc_trim` nie den Event Loop und damit `/heartbeat` anhalten. Das ist die
   ausgeschriebene Hausregel im Kopf von `worker/poller.py` und in `run_once`.
4. **Ein Aktivitätszähler**, wenn die Freigabe mehr tut als loslassen. Sie tut mehr: sie
   ruft `gc.collect()` und `malloc_trim`. Der bestehende RLock deckt den Graphlauf
   absichtlich nicht ab, also braucht es einen eigenen Zähler (hoch beim Betreten von
   `_embed`, runter beim Verlassen) und eine Freigabe nur bei Stand null. Das ist Pitfall
   11 Punkt 3 und es ist der einzige Punkt, an dem diese Phase eine neue Invariante
   einführt.

---

## 5. Der Weg der ersten Suche nach einer Entladung (MEM-03)

### 5.1 Was heute passiert und warum es am 10.09.2026 gerissen ist

```
Nextcloud Unified Search / Ergebnisseite
        |  ExAppService::REQUEST_TIMEOUT_SECONDS = 1.5   (php/lib/Service/ExAppService.php:95)
        |  PAGE_REQUEST_TIMEOUT_SECONDS          = 1.5   (:122)
        v
POST /search  (api/search.py::search, async)
        |  asyncio.to_thread
        v
one_round()  (api/search.py:203, synchron)
        |
        +-- lexical_only ?  ja --> nur Volltext, Engine wird nie gefragt
        |
        +-- nein --> SemanticSide(model=resources.query_model())   (:285)
                         |
                         v
                  candidate_round -> _sides -> semantic.model.embed_query()
                         |                       (index/search.py:251 und :767)
                         v
                  EmbeddingModel._embed -> self._load()   <== HIER wird synchron geladen
                         |
                         +-- Artefakte lesen: 0,57 s Tokenizer + 0,66 s Sitzung (x86, warm)
                         |   auf kaltem Seitencache und ARM deutlich mehr
                         v
                  Antwort kommt nach 1.838,4 ms zurueck  --> Decke 1.500 ms gerissen
                         |
                         v
        cURL error 28, HTTP 200, Ergebnisgruppe ohne Containerteil, null Treffer
```

Belegt in `docs/measurements/2026-09-vergleichsmessung-m7g/README.md` Abschnitte 9.2,
19.4 und 19.10: 1.838,4 ms gegen 1.500 ms (Marge ,338,4 ms), `cURL error 28` im
Nextcloud-Protokoll um `2026-09-10T14:05:17Z`, letzter Containerstart 29 Stunden her,
Seitencache kalt. Auf **leerem** Bestand lag die Marge schon bei ,50,4 ms.
[VERIFIED: eigener Messbericht]

Der unangenehmere Teil desselben Abschnitts: das Lastwerkzeug meldete für Stufe 16
`"failures": 0` bei 17 abgebrochenen Containeraufrufen, weil die Route mit HTTP 200
antwortet. **Ein Abbruch ist von außen unsichtbar.** Wer die Entladung baut, ohne diesen
Pfad zu ändern, bekommt eine Regression, die kein Gate und kein Lastwerkzeug meldet.

### 5.2 Die empfohlene Naht: eine Stelle statt drei

Drei Aufrufer bauen eine `SemanticSide`: `api/search.py:285`, `api/snippets.py:204`,
`api/diagnose.py:213`. Eine Bedingung an allen drei Stellen wäre dreimal dasselbe und die
Stelle, an der die vierte vergessen wird.

Die Naht liegt tiefer und es gibt sie schon: `embed_query` und `embed_passages` sind
bereits getrennte Einstiege in dasselbe `_embed` (`model.py:398-406`), und sie brauchen
genau **gegensätzliches** Verhalten:

- `embed_passages` (Indexseite) **muss** laden dürfen. Nach einer Entladung ist die
  nächste Zeile des Indexlaufs der richtige Moment, die Gewichte wiederzuholen, und dort
  gibt es keine 1,5-Sekunden-Decke.
- `embed_query` (Suchseite) darf **nicht** laden, solange die Entladung eingeschaltet ist.
  Sie antwortet `EmbedOutcome.unavailable()`, `_rank_chunks` gibt eine leere Liste zurück,
  RRF wird zur Identität auf der lexikalischen Liste, und der Nutzer bekommt
  Volltexttreffer. Das ist D-19, der Pfad existiert, ist getestet und wird von einem
  Container ohne Modell täglich benutzt (`index/search.py:251-262`).

Vorschlag für die Signatur, im Stil der Datei:

```python
def _embed(self, texts: Sequence[str], *, prefix: str, may_load: bool = True) -> EmbedOutcome:
    ...
    with self._lock:
        engine = self._engine if not may_load else self._load()
    if engine is None:
        return EmbedOutcome.unavailable()
```

**Wichtig und beim Planen zu entscheiden:** `may_load=False` für `embed_query` darf nur
gelten, wenn der Schalter aus MEM-01 gesetzt ist. Sonst ändert sich auch das Verhalten der
allerersten Suche eines Containers, der nie entlädt, und das ist ein Eingriff in
ausgeliefertes Verhalten außerhalb des Schalters. (Gegenargument, das der Owner hören
sollte: genau diese allererste Suche ist der Vorfall vom 10.09.2026, und sie unbedingt
nicht-blockierend zu machen, würde ihn generell abstellen. Das wäre aber eine
Verhaltensänderung ohne Schalter, also eine eigene Entscheidung.)

**Nebenwirkung, die im Plan stehen muss:** `api/diagnose.py` (`ranked_sides`) ist die
Route, über die das Messwerkzeug seit Phase 12 die Fremdbestands-Vorprüfung misst
(MESS-04). Nach einer Entladung meldet sie eine leere semantische Seite. Das Runbook der
Phase 15 muss das wissen, sonst misst die eine Anfahrt einen Nullwert und nennt ihn Befund.

### 5.3 Das Nachwärmen und die Single-Flight-Bedingung

Wer stößt das Laden an, nachdem `embed_query` es verweigert hat?

| Variante | Bewertung |
|---|---|
| Die Entlade-Aufgabe merkt es beim nächsten Takt | Bei 30 bis 60 s Takt ist auch die zweite Suche des Nutzers noch kalt. Zu langsam |
| `threading.Thread(daemon=True)` aus `one_round` heraus | Neuer Lebenszyklus neben der Lifespan, kein Stopp-Event. Gegen die Hausregel |
| `asyncio.Event` aus dem Worker-Thread setzen | Braucht `loop.call_soon_threadsafe`, also den Loop im Modul. Möglich, aber eine Kopplung mehr |
| **`asyncio.create_task(asyncio.to_thread(warm))` im async Route-Handler** | **Empfohlen.** `api/search.py::search` läuft auf dem Loop, direkt nach dem `to_thread`. Kein Threadsafety-Problem, das Stopp-Verhalten ist das der Lifespan |
| FastAPI `BackgroundTasks` | Funktioniert und ist idiomatisch, läuft aber erst **nach** der Antwort. Als Zweitbester zu nennen |

Die Single-Flight-Bedingung ist das, was Erfolgskriterium 5 wörtlich verlangt ("genau ein
Laden je warmem Fenster"). Zwei Ebenen greifen ineinander:

1. `_load()` läuft unter `self._lock` und kehrt am Kopf zurück, wenn `self._engine is not
   None` (`model.py:467`). Zehn gleichzeitige Warmläufe erhöhen `_LOAD_COUNT` also
   **einmal**. Die Zusage ist damit schon heute strukturell erfüllt.
2. Zehn gleichzeitige Warmläufe blockieren trotzdem zehn Threadpool-Threads am Lock. Ein
   Flag (`_WARMING`) im Halter, gesetzt und gelöscht unter `_LOCK`, ist billig und spart
   das. Empfohlen, aber es ist Effizienz und nicht Korrektheit.

**Das Rennen, das wirklich zählt:** Warmlauf und Entlade-Aufgabe gleichzeitig. Die
Entladung muss die Identität prüfen ("ist das noch dieselbe `_Engine`, die ich beim
Prüfen der Uhr gesehen habe") und die Leerlauf-Uhr muss vom Warmlauf mitgesetzt werden,
sonst entlädt der nächste Takt sofort wieder, was das Ladepaar frisst, das gerade bezahlt
wurde.

---

## 6. Leerlauf-Erkennung und Konfiguration (MEM-01)

### 6.1 Die dritte Aufgabe in der Lifespan

`main.lifespan` startet heute zwei langlebige Aufgaben, beide mit einem `asyncio.Event`
als Stoppsignal: `_POLLER.run(stop_indexing)` (`main.py:306-308`) und
`_guarded_reconcile(_RECONCILE, stop_reconcile)` (`main.py:315-319`). Beide werden im
`finally` mit `stop_*.set()` plus `asyncio.wait_for(asyncio.shield(...))` beendet
(`main.py:~370`). Eine dritte nach demselben Muster ist der belegte Weg.

```
main.lifespan
  |
  +-- Task 1  Poller.run(stop_indexing)
  +-- Task 2  _guarded_reconcile(stop_reconcile)        (nur wenn eingeschaltet)
  +-- Task 3  _idle_release(stop_release)       NEU     (nur wenn TTL > 0)
         |
         |  while not stop.is_set():
         |     await _pause(tick, stop)              # Muster von worker._pause
         |     if warm_wanted:  await to_thread(warm)
         |     if monotonic() - last_use > ttl and poller_is_idle:
         |         await to_thread(release_both)     # gc.collect + malloc_trim
         v
```

**Nicht in den Leerlaufzweig des Pollers.** Ein stummgeschalteter Poller (`silence()`)
wartet in `run()` auf `self._armed` und betritt `run_once` nie wieder (`poller.py:543-545`).
Genau dieser Container, der nicht indexiert und nur gelegentlich durchsucht wird, ist der
Fall, für den die Entladung gebaut wird. [VERIFIED: Quellcode gelesen]

**Die zweite Bedingung ist keine Feinheit.** Mitten in einem Indexlauf zu entladen heißt,
die Gewichte Sekunden später wieder zu laden. Der Poller führt seinen Leerlaufzustand
bereits (`_idle_announced`, `armed`, `cooldown`), und `main.active_poller()` gibt die
Instanz her (`main.py:113`). Die Aufgabe kann also fragen, ohne dass `embed/` in
`worker/` hineinruft.

**Die Leerlauf-Uhr** gehört nach `EmbeddingModel`, gesetzt in `_embed` (eine Zeile, deckt
Suche und Indexspur zugleich ab, weil beide durch diese Methode gehen), und muss vom
Warmlauf mitgesetzt werden.

### 6.2 Die Variable: der Namensdissens und wie er aufzulösen ist

STACK.md und ARCHITECTURE.md nennen unterschiedliche Namen. Das ist der Punkt, den MEM-01
ausdrücklich vor dem Bau festgelegt haben will.

| Kandidat | Quelle | Argument dafür | Argument dagegen |
|---|---|---|---|
| `FINDLING_EMBED_IDLE_SECONDS` | STACK.md B.9 | Kürzer; "idle seconds" ist die gängige Formulierung | Sagt nicht, was nach den Sekunden passiert. Ein Admin könnte es für einen Timeout halten |
| `FINDLING_EMBED_IDLE_RELEASE_SECONDS` | ARCHITECTURE.md B, `EMBED_IDLE_RELEASE_SECONDS` | Nennt Bedingung und Wirkung; passt zu `release()` im Code | Länger; 35 Zeichen |

**Empfehlung: `FINDLING_EMBED_IDLE_RELEASE_SECONDS`.** Begründung aus dem eigenen Bestand:
die 15 bereits dokumentierten Variablen in `backend/appinfo/info.xml` nennen alle Wirkung
und nicht nur Bedingung (`FINDLING_RECONCILE_MIN_INTERVAL_HOURS`,
`FINDLING_OCR_PAGE_SECONDS`, `FINDLING_RECONCILE_QUIET_MAX`), und die Kommentarzeile dort
sagt ausdrücklich: "Every name below is spelled exactly as backend/src/findling/config.py
reads it". Es ist aber eine Empfehlung, keine Entscheidung; der Plan soll sie in einem
Satz festhalten. [CITED: backend/appinfo/info.xml, Kommentarblock vor
`<environment-variables>`]

### 6.3 Der Leser, und warum `_bounded_int_from_environment` **nicht** reicht

`_bounded_int_from_environment(name, default, bounds)` prüft `low <= value <= high` und
fällt sonst auf den Default zurück (`config.py:775-788`). Für diese Variable ist das
falsch, und zwar in beide Richtungen:

- Mit `bounds = (0, 86400)` wäre `3` gültig. Eine TTL von drei Sekunden ist ein Container,
  der pausenlos lädt und entlädt, und bei dynamischem `M_MMAP_THRESHOLD` wird er über die
  Zyklen schlechter, nicht besser.
- Mit `bounds = (60, 86400)` wäre `0` ungültig und fiele auf den Default zurück, also auf
  **an**. Ein Admin, der abschalten will, bekäme die Funktion.

Die Datei hat für genau diesen Fall bereits zwei maßgeschneiderte Leser:
`_hour_from_environment` (`config.py:826`) und `_overlap_from_environment`
(`config.py:849`), und der Docstring von `_bounded_float_from_environment` schreibt den
Grund für die Aufspaltung selbst aus ("Zero is a legitimate answer here"). Der Plan
braucht also einen dritten Leser nach demselben Muster: **0 ist erlaubt und bedeutet aus,
alles andere muss im gemessenen Bereich liegen, sonst Default plus Warnzeile mit dem
Variablennamen.** [VERIFIED: config.py gelesen]

### 6.4 Der Werksstand

Ab Werk aus, also Default `0`. Das ist Erfolgskriterium 2 und es hat zwei Gründe, die
beide in den Kommentar gehören: der A/B-Beleg der einen Box-Anfahrt braucht beide
Stellungen, und ein Feature, dessen Wiederaufwärm-Kosten noch nicht gemessen sind, darf
auf Bestandsinstallationen nicht von selbst angehen.

Ein Vorschlagswert für Admins, die ihn einschalten, gehört in die `<description>` der
info.xml und ist heute geraten: 900 s. Er wird erst nach der Box-Anfahrt eine Messung.

### 6.5 Die info.xml

`backend/appinfo/info.xml` führt heute **15** Variablen in `<environment-variables>`, und
**keine einzige** davon ist eine `FINDLING_EMBED_*`-Variable. Diese wäre die sechzehnte
und die erste ihrer Familie. [VERIFIED: Datei gelesen, `grep -c` gezählt] Das ist relevant,
weil der Block dadurch einen neuen Sammelkommentar brauchen könnte, so wie der
Reconcile-Block einen hat, und weil `FINDLING_EMBED_ENABLED` heute nur in
`docs/admin-page.md` steht und in der info.xml fehlt. Ob das als Beifang mitgenommen wird,
ist eine Planentscheidung; es ist ein Härtungskandidat und kein Requirement.

---

## 7. Die neu formulierte one_load-Zusage (MEM-05, technischer Teil)

### 7.1 Was heute zugesichert wird und warum es falsch wird

`tools/one_load.py` fährt in fester Reihenfolge: Indexseite, dann Suchseite, dann zweite
Spur, und verlangt für jeden Zähler exakt `EXPECTED = 1` (`one_load.py:133, 337-370`). Die
Reihenfolge ist die Anti-Leerlauf-Klausel: die Suchseite muss den Zähler selbst auf eins
bringen, damit eine Messung, die das Modell nie erreicht hat, mit null durchfällt statt
still grün zu werden.

`_LOAD_COUNT` ist bewusst monoton und wird von `engine.reset()` ausdrücklich **nicht**
genullt, mit ausgeschriebener Begründung: "a counter that can be zeroed is one a gate could
zero itself green with" (`engine.py::reset` Docstring).

Mit einer Entladung ist "genau ein Laden je Prozess" wörtlich falsch. Das Gate hat dann
zwei Ausgänge, die beide schlecht sind: rot, obwohl das Produkt richtig arbeitet, oder
grün, weil sein Messfenster kürzer ist als die Leerlauffrist, und beweist damit eine
Eigenschaft, die das Produkt nicht mehr hat.

### 7.2 Die Zusage, die Erfolgskriterium 5 wörtlich verlangt

> "nie zwei Engines gleichzeitig, genau ein Laden je warmem Fenster"

In Zählern ausgedrückt, mit `_LOAD_COUNT` weiterhin monoton und einem neuen, ebenfalls
monotonen `_UNLOAD_COUNT`:

| Invariante | Ausdruck | Was sie ausschließt |
|---|---|---|
| Nie zwei Engines | `0 <= loads , unloads <= 1` zu jedem Zeitpunkt | Die 276 MB aus Plan 06.1-02, jetzt auch im Entladezyklus |
| Ein Laden je warmem Fenster | `loads , unloads == 1` nach einem Warmlauf, unverändert nach einem zweiten | Dass nebenläufige Warmläufe je eine Sitzung bauen |
| Kein Grünnullen | beide Zähler monoton, nicht rücksetzbar | Ein Gate, das sich selbst grün nullt |

`_LOAD_COUNT` bleibt also, was es ist, und die Aussage wird zur **Differenz**. Die
Rot-Fähigkeit des umgebauten Gates muss per Mutation am echten Baum bewiesen werden;
`backend/tests/test_one_load.py` hat dafür drei Muster
(`test_it_goes_red_when_the_search_side_builds_its_own_engine`,
`test_it_goes_red_when_the_word_list_is_read_a_second_time`,
`test_it_goes_red_when_the_search_never_reaches_the_model`) und braucht mindestens zwei
neue: eine Entladung, die zwei Engines hinterlässt, und ein Warmlauf-Rennen, das zweimal
lädt.

### 7.3 Die betroffenen Stellen

| Ort | Änderung |
|---|---|
| `backend/src/findling/embed/model.py` | `_UNLOAD_COUNT`, `unload_count()`, `release()`, Leerlauf-Uhr, `may_load` |
| `backend/src/findling/embed/engine.py` | `release_if_idle()`, Zähler-Weiterreichung, Warm-Flag, ggf. sechster Zustand |
| `backend/src/findling/tools/one_load.py` | Modulkopf, `Report`-Felder, `findings()`, vierte Phase "entladen und nachladen" |
| `backend/tests/test_one_load.py` | zwei neue Mutationsfälle |
| `.github/workflows/resilience.yml` Schritt "One engine and one constituent list per process" | Der erklärende Text unter dem Schritt nennt heute "one embedding engine per process (plan 06.1-02, 276 MB)". Der Satz wird falsch und steht im Fehlerpfad, den ein Mensch liest |
| `backend/tests/test_embed_engine.py`, `test_embed_model.py` | Freigabe im Leerlauf, Freigabe bei laufender Arbeit (darf nichts kaputtmachen), Nachladen, Erhalt von `_absent` und `_load_failed_at` über eine Freigabe hinweg |

---

## 8. Owner-Checkpoint: die engineState-Wortwahl (MEM-05)

**Hier wird nichts entschieden.** Die beiden Recherchedokumente dieses Projekts
widersprechen sich, und die Roadmap benennt das als Owner-Checkpoint. Was diese Recherche
beisteuert, ist der genaue Preis beider Zweige, damit die Entscheidung mit Zahlen
getroffen wird statt mit Geschmack.

### 8.1 Der heutige Stand, nachgezählt

`ENGINE_STATES` ist eine `frozenset` mit fünf Wörtern (`engine.py`), gespiegelt als
`private const ENGINE_STATES` in `AdminViewService.php:177`, und zu **sechs** Sätzen
gemacht: fünf in der Zuordnung plus einer für "der Container meldet nichts". Diese sechs
stehen doppelt, in `php/templates/admin.php:66-72` und wortgleich in `php/js/admin.js`.
[VERIFIED: alle vier Dateien gelesen]

**Die Gates, die genau das halten** (in `backend/tests/test_admin_ui_contract.py`):

1. `test_both_halves_of_the_page_map_the_same_state_to_the_same_sentence` , Template und
   Skript müssen dieselbe Zuordnung haben, und `set(template) == set(ENGINE_STATES)` wird
   gegen den **importierten** Satz aus dem Container geprüft
2. `test_the_six_sentences_of_the_engine_line_are_in_the_german_catalogue` , enthält ein
   hartes `assert len(sentences) == 6`
3. `test_all_six_catalogues_carry_the_same_keys` , über `L10N_CATALOGUES = (de.json,
   de.js, de_DE.json, de_DE.js, fr.json, fr.js)`
4. `test_every_french_value_carries_a_french_wording` , ein aus `de.js` kopierter
   französischer Wert wird erkannt

Dazu `test_the_two_translation_files_carry_the_same_keys` und
`test_the_german_catalogue_covers_both_german_language_codes`.

**Sechs Katalogdateien, und die Zahl 6 steht als Literal in Gate 2.** Das ist die
"Kostenfolge sechs Stellen und vier Katalog-Gates" aus der Roadmap, jetzt an Datei und
Zeile belegt.

### 8.2 Zweig A: `cold` wiederverwenden

Vertreten von STACK.md B.9 und PITFALLS.md Pitfall 13.

- **Kosten:** null. `engine_state()` liefert nach der Entladung von selbst wieder `cold`,
  weil `held.loaded` falsch wird und keiner der vorrangigen Zweige greift (`engine.py`,
  Reihenfolge der Antworten). Kein Gate wird rot, kein Katalog wird angefasst.
- **Der Satz, der dann dasteht:** "Das Modell wird beim ersten Bedarf geladen. Das ist der
  Normalfall." Das ist für einen entladenen Container sachlich wahr.
- **Was der Admin nicht sieht:** dass die nächste Suche das Nachladen kostet, und dass
  dieser Container das regelmäßig tut. Wer auf die Seite schaut, weil die Suche sich
  komisch anfühlt, findet die Erklärung nicht.
- **Ausgleichsvorschlag aus derselben Quelle:** die Information "es war schon einmal
  geladen" als getrennte **Zahl** auf der Admin-Seite (Freigabezähler), nicht als Wort.
  Eine Zahl fällt nicht unter `ENGINE_STATES` und löst kein Katalog-Gate aus, braucht aber
  trotzdem einen Satz drumherum, der in die Kataloge muss. Der Preis ist also nicht null,
  nur kleiner.

### 8.3 Zweig B: ein sechstes Wort `unloaded`

Vertreten von ARCHITECTURE.md B.6.

- **Kosten, vollständig aufgezählt:** `ENGINE_STATES` in `engine.py`; `ENGINE_STATES` in
  `AdminViewService.php:177`; ein Satz in `admin.php`; derselbe Satz in `admin.js`; sechs
  Katalogdateien in drei Sprachen (de, de_DE, fr, je `.json` und `.js`), wobei der
  französische Wortlaut vom Gate auf echtes Französisch geprüft wird; das Literal `6` in
  `test_the_six_sentences_of_the_engine_line_are_in_the_german_catalogue` wird `7`; dazu
  `docs/admin-page.md` (Tabelle mit der Spalte "Was ein Admin tun kann") und der Absatz
  darunter, der heute ausdrücklich schreibt "also gibt es dafür kein sechstes Wort".
- **Was er einbringt:** der Milestone verlangt, die Wiederaufwärm-Kosten "zu messen und
  auszuweisen". Ausweisen heißt, dass der Admin "noch nie gelesen" von "zum Sparen
  freigegeben, die nächste Suche kostet das Nachladen" unterscheiden kann.
- **Die Falle dabei** (PITFALLS 13): ein Container, der das neue Wort meldet, und eine
  PHP-Hälfte, die es noch nicht kennt, zeigt den Ausweichsatz "Dieser Container meldet den
  Zustand des Modells noch nicht", was wie ein kaputtes Backend aussieht. Die beiden
  Hälften reisen als Paar (`REL-02` verlangt den Gleichschritt), aber ein Admin kann sie
  getrennt aktualisieren. Wer Zweig B nimmt, braucht dafür einen Satz im Plan.
- **Dritter Weg, der beiden Seiten etwas gibt und hier nur benannt, nicht empfohlen wird:**
  das Wort `cold` behalten und den Satz dahinter um einen zweiten Halbsatz erweitern, der
  nur unter eingeschalteter Entladung erscheint. Kosten: keine neue Zustandsvokabel, aber
  eine bedingte Satzwahl in zwei Hälften, was Gate 1 (beide Hälften bilden gleich ab)
  schwieriger prüfbar macht. Wahrscheinlich das Schlechteste von dreien, gehört aber auf
  den Tisch, damit die Entscheidung vollständig ist.

### 8.4 Was der Checkpoint braucht, um entscheidbar zu sein

1. Die Zahl aus dem Vorprüflauf. Wenn die Entladung wenig zurückgibt und entsprechend
   selten eingeschaltet wird, ist ein sechstes Wort für einen seltenen Zustand teuer.
2. Den Entscheid, ob der Freigabezähler ohnehin auf die Seite kommt. Wenn ja, trägt er
   einen Teil der Information, die Zweig B rechtfertigt.
3. Die Kenntnis, dass die Entscheidung **vor** dem Bau des Zustandsteils fallen muss und
   nicht danach: `ENGINE_STATES` wird von einem Gate importiert, also zieht jede spätere
   Änderung die vier Katalog-Gates erneut.

---

## 9. Standard Stack

Keine neue Abhängigkeit. Keine Zeile in `backend/pyproject.toml`, kein `composer require`,
kein npm, kein Build-Schritt.

### Core (alles Stdlib oder bereits im Repo)

| Baustein | Herkunft | Zweck | Warum kein Paket |
|---|---|---|---|
| `ctypes.CDLL("libc.so.6").malloc_trim(0)` | Stdlib | Freie Seiten an das Betriebssystem zurückgeben | Es gibt kein Paket dafür; das Basis-Image ist glibc |
| `gc.collect()` | Stdlib | Referenzzyklen im Python-Wrapper lösen | , |
| `time.monotonic()` | Stdlib | Leerlauf-Uhr | Die Uhr, die `LOAD_RETRY_SECONDS` schon benutzt |
| `asyncio.Event` + `asyncio.sleep` + `asyncio.to_thread` | Stdlib | Dritte langlebige Aufgabe im Muster der zwei bestehenden | APScheduler, `threading.Timer`, Cron im Container: alle drei ein neuer Lebenszyklus für eine `while`-Schleife mit `sleep` |
| `rss_bytes()` | `index/wordlist.py:351` | RSS aus `/proc/self/status` | psutil ist ein Paket für eine Zahl; der Kommentar dort begründet es |
| `scripts/ops/rss_sampler.sh`, `rss_digest.py` | eigener Bestand | cgroup-Zeitreihe je Container, beide Treiberlayouts | , |
| `embed/bench.py` | eigener Bestand | Messwerkzeug im Image, hat `--mode`-Struktur | Der Vorprüflauf wird ein vierter Modus |

### Versionsstand, geprüft

| Paket | Stand im Repo | Bemerkung |
|---|---|---|
| `onnxruntime` | `==1.30.0` (`backend/pyproject.toml:44`) | **Eingefroren bis nach Phase 15.** Keinen Sprung vorschlagen; ein Runtime-Wechsel erzwingt Modellqualitäts-Gates und ARM-Wheel-Prüfung neu und macht jede Vergleichsmessung ungültig [VERIFIED: pyproject.toml gelesen; Vorgabe aus Auftrag und REQUIREMENTS "Out of Scope"] |
| `tokenizers` | über die Kette | Rust-Seite, also glibc-Heap, also `malloc_trim`-abhängig (in 3.2/3.3 gemessen) |
| `python:3.13-slim-trixie` | Basis-Image | glibc, `malloc_trim` vorhanden und in dieser Sitzung mit Rückgabewert 1 bestätigt |

**Hinweis zu STACK.md:** dort steht `onnxruntime 1.29.0` als Repo-Stand. Das ist
überholt, `pyproject.toml` pinnt heute `1.30.0`. Der Plan sollte sich auf die Datei
stützen, nicht auf das Recherchedokument.

### Alternatives Considered

| Empfohlen | Alternative | Wann die Alternative besser ist |
|---|---|---|
| In-Prozess-Entladung + `malloc_trim` | Embedding-Kindprozess, der beendet wird | Nur wenn der Vorprüflauf zeigt, dass der RSS nicht zurückkommt. Die in 3.2 gemessenen Zahlen sprechen dagegen, dass es dazu kommt. Preis: widerruft teilweise EFF-01/02, braucht Vektor-Transport über die Prozessgrenze, macht den Kaltstart teurer und verschärft damit MEM-03 |
| In-Prozess-Entladung | jemalloc/mimalloc per `LD_PRELOAD` | **Nie hier.** Ein fremder Allokator betrifft tantivy, SQLite, tesseract und ORT gleichzeitig und macht jede bestehende Messung ungültig. Steht in REQUIREMENTS "Out of Scope". ORT#26831 berichtet zudem, dass mimalloc dort nichts geholfen hat |
| Dritte asyncio-Aufgabe | APScheduler, `threading.Timer` | Nie. Steht in REQUIREMENTS "Out of Scope" |
| `rss_bytes()` | psutil | Nie. Steht in REQUIREMENTS "Out of Scope" |
| `measure.yml` Messung D auf `ubuntu-24.04-arm` | Vorprüflauf auf der bezahlten Box | Nur wenn eine Zahl gebraucht wird, die der CI-Runner nicht geben kann (Ladezeit in ms auf m7g.large mit kaltem Seitencache). Die Rückgabequote kann der Runner geben |
| `may_load=False` in `embed_query` | Bedingung an allen drei `SemanticSide`-Aufrufern | Nie. Drei Stellen sind die Stelle, an der die vierte vergessen wird |
| `session.use_device_allocator_for_initializers` | , | **Nichts ergänzen.** Wirkungslos, solange `enable_cpu_mem_arena=False` gesetzt ist: die Initializer laufen dann ohnehin über malloc/new |

---

## 10. Package Legitimacy Audit

**Diese Phase installiert kein einziges neues Paket.** Es gibt keine Zeile für
`pyproject.toml`, keine für `composer.json` und keine für npm. Alles, was gebraucht wird,
ist Stdlib (`ctypes`, `gc`, `time`, `asyncio`) oder steht bereits im Repo.

| Package | Registry | Disposition |
|---|---|---|
| , | , | Keine neue Abhängigkeit in dieser Phase |

**Packages removed due to slopcheck [SLOP] verdict:** keine (keine Kandidaten)
**Packages flagged as suspicious [SUS]:** keine (keine Kandidaten)

Die bestehende Kette (`onnxruntime==1.30.0`, `tokenizers`, `tantivy`, `sqlite-vec`,
`semantic-text-splitter`) wird nicht angefasst und ist bis nach Phase 15 eingefroren. Ein
Aufräumbefund aus der v1.2-Recherche bleibt offen und ist **kein** Teil dieser Phase:
`fastembed==0.8.0` ist gepinnt, wird aber in `backend/src/` nirgends importiert.

---

## 11. Bestandsaufnahme: alle Stellen, die diese Phase berührt

Analog zur Runtime-State-Inventur für Umbenennungen, weil MEM-05 dieselbe Form hat: eine
Zusage, die an mehreren Stellen gleichzeitig steht.

| Kategorie | Gefunden | Handlung |
|---|---|---|
| **Backend-Code** | `config.py` (Konstante, Bereich, Leser), `embed/model.py` (Uhr, `release`, Zähler, `may_load`), `embed/engine.py` (`release_if_idle`, Warm-Flag, ggf. Zustand), `worker/poller.py` (`release_cutter`, Leerlauf-Auskunft), `main.py` (dritte Aufgabe, Stopp-Event, Aufräumen im `finally`), `api/search.py` (Nachwärm-Auslöser) | Code-Änderung |
| **Messwerkzeug** | `tools/one_load.py` (Modulkopf, Report, findings, vierte Phase), `embed/bench.py` (neuer Modus) | Code-Änderung |
| **CI** | `.github/workflows/resilience.yml` Schritt "One engine and one constituent list per process" (der Erklärtext nennt die alte Zusage), `.github/workflows/measure.yml` (Messung D) | Datei-Änderung |
| **PHP-Hälfte** | nur bei Zweig B: `AdminViewService.php:177`, `admin.php:66`, `admin.js` | Abhängig vom Owner-Checkpoint |
| **Kataloge** | nur bei Zweig B: `php/l10n/{de,de_DE,fr}.{json,js}`, sechs Dateien | Abhängig vom Owner-Checkpoint |
| **Store- und Admin-Dokumentation** | `backend/appinfo/info.xml` (16. Variable), `docs/admin-page.md` (Zustandstabelle plus der Absatz, der heute "kein sechstes Wort" schreibt), `docs/embeddings.md`, `docs/performance.md` | Datei-Änderung |
| **Messdokumentation** | neues Verzeichnis `docs/measurements/2026-09-entladung-vorpruefung/` mit `skripte/00-ablauf.md` (vorher notierte Erwartung), nach dem Muster der bestehenden Messläufe | Neu anzulegen |
| **Runbook Phase 15** | `docs/runbook-messbox.md` muss den A/B-Schalter und die Nebenwirkung auf `ranked_sides` kennen | Datei-Änderung, gehört in diese Phase, nicht erst in 15 |
| **Gespeicherte Daten** | keine. Die Entladung ändert kein Schema, keinen Index, keine Vektoren, keine Migration. `SCHEMA_VERSION` bleibt unberührt, kein Reindex | keine |
| **Laufende Fremdkonfiguration** | keine. Weder AppAPI noch Nextcloud speichern etwas über den Engine-Zustand | keine |
| **Secrets/Env** | eine neue Variable, keine Umbenennung einer bestehenden. Keine Secret-Rotation | keine |

---

## 12. Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---|---|---|---|
| Wiederkehrender Takt im Container | `threading.Timer`, eigener Scheduler, Cron im Image | Dritte asyncio-Aufgabe mit `asyncio.Event` als Stopp, nach dem Muster von `Poller.run` und `_guarded_reconcile` | Die Lifespan hat den Lebenszyklus; ein Timer-Thread umgeht das bestehende Stopp-Event und überlebt den Shutdown |
| Lexikalische Antwort bei kalter Engine | Eine neue Antwortform, ein neues Verdikt, ein Sonderpfad in der Fusion | `EmbedOutcome.unavailable()` plus leere Vektorliste; RRF wird zur Identität auf der lexikalischen Liste (D-19) | Der Pfad ist gebaut, getestet, wird täglich von Containern ohne Modell benutzt und kostet nichts |
| Thread-Sicherheit um die Freigabe | Eine Sperre um `session.run()` | Die lokale Referenz in `_embed` plus `self._lock` nur um das Nullsetzen | Eine Sperre um den Graphlauf wurde in 06.1-17 ausgebaut, gemessen 0,561 s bis 2,562 s Wartezeit je Suche |
| Speicher messen | psutil, ein Speicher-Ceiling in CI | `rss_bytes()` plus Zähler; `scripts/ops/rss_sampler.sh` für die Zeitreihe | Ein Ceiling auf einem geteilten Runner geht für Runner-Last rot und nicht für die benannte Sache. Die ausgeschriebene Begründung steht im Kopf von `tools/one_load.py` |
| RSS-Rückgabe erzwingen | Allokator tauschen, Speicher-Grenzen setzen | `gc.collect()` + `ctypes malloc_trim(0)` mit `try/except (OSError, AttributeError)` | In 3.2 und 3.3 gemessen: es wirkt. Ein fremder Allokator würde tantivy, SQLite und tesseract mitnehmen |
| Zustandswort für die Admin-Seite | Ein Wort im Container erfinden und die PHP-Seite nachziehen | Erst den Owner-Checkpoint, dann den Satz, dann die sechs Kataloge, in dieser Reihenfolge | `ENGINE_STATES` wird von einem Gate importiert; jede spätere Änderung zieht vier Katalog-Gates erneut |

**Key insight:** Diese Phase besteht fast vollständig aus dem Wiederverwenden von Nähten,
die dieses Repository schon hat. Jeder Ort, an dem die Versuchung aufkommt, etwas Neues zu
bauen, hat ein Vorbild im Baum: die dritte Aufgabe hat zwei Geschwister, der
Degradationspfad ist D-19, das Messwerkzeug ist `embed/bench.py`, die Wegwerfmessung ist
`measure_wordlist.sh`, die Zielarchitektur ist `measure.yml`.

---

## 13. Common Pitfalls

### Pitfall 1: Nur `gc.collect()`, kein `malloc_trim`

**Was schiefgeht:** Das Log sagt "entladen", `held.loaded` ist falsch, die Admin-Seite
sagt `cold`, und `anon` im Container fällt um 14 bis 57 MB statt um 260 bis 290.
**Warum:** glibc behält freigegebene Blöcke in der Arena. Rust-seitige Allokationen
(Tokenizer, Splitter) laufen über genau diesen Allokator. In 3.2 gab `gc.collect()` allein
20,1 Prozent zurück, in 3.3 nur 4,9 Prozent.
**Vermeiden:** Reihenfolge Referenzen lösen, `gc.collect()`, `malloc_trim(0)`. Der
Rückgabewert gehört in die Messausgabe.
**Warnzeichen:** Die Ersparnis liegt unter 100 MB. Dann wurde `malloc_trim` nicht gerufen
oder hat `0` zurückgegeben.

### Pitfall 2: `ctypes.CDLL("libc.so.6")` ohne Schutzschalter

**Was schiefgeht:** Auf einer libc ohne `malloc_trim` (musl, eine fremde Basis) wirft der
Entlader, die Lifespan-Aufgabe stirbt, und je nach Bauform nimmt sie die Suche mit.
**Vermeiden:** `try/except (OSError, AttributeError)` mit stillem No-Op, einmal gewarnt.
Das ist dieselbe Haltung, die `extract/ocr.py` gegenüber einem fehlenden tesseract
einnimmt.
**Warnzeichen:** Ein Test, der nur auf dem Basis-Image läuft. Der Schutzschalter braucht
einen eigenen Fall, in dem `CDLL` wirft.

### Pitfall 3: Entladen mitten im Indexlauf

**Was schiefgeht:** Die Gewichte fallen, und sechs Sekunden später lädt die nächste Zeile
sie wieder. Über einen Volllauf hinweg wird die Entladung zum Kostenfaktor statt zur
Ersparnis, und die Laufzeit steigt, ohne dass irgendwo etwas rot wird.
**Warum:** Die Leerlauf-Uhr allein reicht nicht, wenn ein Indexlauf gerade zwischen zwei
Batches steht.
**Vermeiden:** Zweite Bedingung "Poller ist nicht an Arbeit" über `main.active_poller()`
und den Leerlaufzustand, den der Poller schon führt. Dazu ein Aktivitätszähler in `_embed`
und Freigabe nur bei Stand null.
**Warnzeichen:** `unload_count` steigt während eines Volllaufs mehr als einmal.

### Pitfall 4: Der Suchpfad lädt weiter synchron

**Was schiefgeht:** Jede erste Suche nach einer Ruhephase reißt die 1,5-Sekunden-Decke,
der Nutzer sieht HTTP 200 mit null Treffern und keine Fehlermeldung, im
Nextcloud-Protokoll steht `cURL error 28`. Die Unified Search fragt bei jedem Tastendruck.
**Warum:** `embed_query` geht durch `_embed` und dort durch `_load()`.
**Vermeiden:** `may_load=False` für `embed_query`, Nachwärmen im Hintergrund.
**Warnzeichen, und das ist die Falle in der Falle:** Das Lastwerkzeug meldet null
Fehlschläge, weil die Route mit HTTP 200 antwortet. Der Fingerabdruck steht in den
**Trefferzahlen je Anfrage** (5,40 auf den grünen Stufen gegen 4,16 auf Stufe 16), nicht
in der Fehlerspalte. Ein Test für diese Phase muss also Treffer zählen und nicht Fehler.

### Pitfall 5: Die falsche Messgröße im Store-Text

**Was schiefgeht:** Die Ersparnis wird als "Grundlast minus X" gerechnet. Die Grundlast
von 103,2 MB ist aber seit der faulen Bauweise von 07-03 bereits **ohne** Modell und
Cutter gemessen. Die Zahl wäre erfunden.
**Vermeiden:** Die Messgröße heißt "Rückkehr zur Grundlast nach einem Indexlauf", und sie
heißt so schon im Vorprüflauf, nicht erst im Bericht. Dazu der Import-Bodensatz aus 3.4
Punkt 3, der nie zurückkommt.
**Warnzeichen:** Eine Zahl im Store-Text, die höher ist als die gemessene Differenz
zwischen "vor der Entladung" und "nach der Entladung".

### Pitfall 6: Die Zahl aus der Testumgebung wird die Zahl des Produkts

**Was schiefgeht:** Die Entladung ist in Unit-Tests grün, die Zahl kommt von x86_64 mit
warmem Seitencache, und auf ARM mit kaltem Cache sieht sie anders aus. Der Wert schwankt
zwischen zwei Läufen um mehr als die behauptete Ersparnis.
**Vermeiden:** Vorprüflauf auf `ubuntu-24.04-arm`, mehrere Zyklen, Maschine dokumentiert.
**Warnzeichen:** Ein einziger Lauf. Die dynamische `M_MMAP_THRESHOLD`-Anpassung von glibc
lässt vermuten, dass Zyklus 5 nicht aussieht wie Zyklus 1. **Fünf Zyklen messen, nicht
einen.** [CITED: man7.org mallopt(3); nicht selbst gemessen]

### Pitfall 7: Das one_load-Gate wird still entwertet

**Was schiefgeht:** Das Gate bleibt grün, weil sein Messfenster kürzer ist als die
Leerlauffrist, und beweist damit eine Eigenschaft, die das Produkt nicht mehr hat.
**Vermeiden:** Vierte Phase im Werkzeug (entladen und nachladen), Zusage als Differenz
`loads , unloads`, Rot-Fähigkeit per Mutation belegt.
**Warnzeichen:** Das Gate wurde angefasst, aber `test_one_load.py` hat keinen neuen
Mutationsfall.

### Pitfall 8: `_absent` oder `_load_failed_at` beim Entladen mit zurücksetzen

**Was schiefgeht:** Ein Container ohne Modell fängt wieder an, bei jeder Suche zu staten;
ein laufender Cooldown wird still abgebrochen, und ein kaputter Graph wird wieder einmal
pro Dokument geöffnet statt zwölfmal pro Stunde.
**Vermeiden:** Die Freigabe fasst **nur** `_engine` an. Drei Merker bleiben stehen:
`_absent`, `_load_failed_at`, und auf der Poller-Seite `_cutter_absent` und
`_cutter_failed_at`. Ein Test je Merker.

### Pitfall 9: Die Diagnose-Route meldet nach einer Entladung eine leere semantische Seite

**Was schiefgeht:** `api/diagnose.py::ranked_sides` ist das Werkzeug, mit dem Phase 12 die
Fremdbestands-Vorprüfung misst (MESS-04). Nach einer Entladung mit `may_load=False`
antwortet die semantische Seite leer, und die eine Box-Anfahrt misst einen Nullwert und
nennt ihn Befund.
**Vermeiden:** Entweder die Diagnose-Route darf laden (sie hat keine 1,5-Sekunden-Decke,
sie ist keine Nutzerroute), oder das Runbook schreibt einen Aufwärmschritt vor. **Das ist
eine Entscheidung, die in den Plan gehört**, und sie berührt Phase 15 direkt.

---

## 14. Code Examples

### 14.1 Die Freigabe, vollständig

```python
# Quelle: Rezeptur aus STACK.md B.3, in dieser Sitzung im Basis-Image gemessen
import ctypes
import gc

_TRIM_UNAVAILABLE_WARNED = False


def _return_free_pages_to_the_system() -> None:
    """Hand whole free pages back, and stay silent where the libc has no way to.

    gc.collect() alone returned 20 per cent on x86_64 and 5 per cent on aarch64
    in the pre-check of 2026-09-19; malloc_trim(0) returned the rest. The order
    matters: a trim before the collect finds the blocks still referenced.
    """
    gc.collect()
    try:
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except (OSError, AttributeError):
        # A libc without malloc_trim is a supported container, not a failure.
        # Same stance extract/ocr.py takes towards a missing tesseract.
        pass
```

### 14.2 Die Freigabe am Halter der Suchseite

```python
# Quelle: Bauform aus dem bestehenden _load() in embed/model.py
def release(self) -> bool:
    """Let go of weights and tokenizer, and say whether there was anything to let go of.

    The three remembered facts stay: an absent model directory, a load that
    threw and is inside its cooldown, and the warning flag of a thrown batch
    are properties of this installation or of a moment, and neither of them is
    what a release is about.
    """
    global _UNLOAD_COUNT
    with self._lock:
        if self._engine is None:
            return False
        if self._in_flight:           # a batch is running, its local reference
            return False              # holds the engine anyway; try again next tick
        self._engine = None
        _UNLOAD_COUNT += 1
    _return_free_pages_to_the_system()
    return True
```

### 14.3 Die Uhr im bestehenden Einstieg

```python
# In _embed, neben dem bestehenden Lock-Block (model.py:421)
with self._lock:
    engine = self._load() if may_load else self._engine
    self._last_use = time.monotonic()
if engine is None:
    return EmbedOutcome.unavailable()      # D-19, der Pfad existiert
```

### 14.4 Die dritte Aufgabe, im Muster der zwei bestehenden

```python
# Quelle: main.py:306-319 (Poller.run und _guarded_reconcile), poller._pause
async def _release_when_idle(stop_event: asyncio.Event) -> None:
    """Let go of both holders once nothing has embedded for the configured span."""
    ttl = settings().embed_idle_release_seconds
    while not stop_event.is_set():
        await _pause(RELEASE_TICK_SECONDS, stop_event)
        try:
            if engine.warm_wanted():
                await asyncio.to_thread(engine.warm)
                continue
            poller = active_poller()
            if poller is not None and poller.armed and not poller.idle:
                continue
            # to_thread, because gc.collect and malloc_trim block, and a blocked
            # loop is a container that stops answering /heartbeat while its own
            # log looks perfectly healthy.
            await asyncio.to_thread(engine.release_if_idle, ttl)
        except Exception as error:
            LOGGER.error("the release task ended in an unexpected %s", type(error).__name__)
```

### 14.5 Der Vorprüflauf, als Messung D in measure.yml

```yaml
# Quelle: Bauform der Schritte A, B und C in .github/workflows/measure.yml
      # Measurement D, and it is the one this phase is decided on. Four marks per
      # cycle and five cycles, because glibc adjusts M_MMAP_THRESHOLD upward as
      # large blocks are freed, so cycle 5 is not cycle 1. Numbers only, never a
      # token and never a file name (T-06-06).
      - name: D, RSS returned by a release
        env:
          TARGET: ${{ steps.image.outputs.target }}
        run: |
          docker run --rm --network none --cpuset-cpus 0,1 \
            --entrypoint python "${TARGET}" \
            -m findling.embed.bench --mode rss-release --cycles 5 --threads 2 \
            | tee "${OUT}/rss-release.txt"
```

Die vier Marken je Zyklus, die der Modus schreiben muss:

| Marke | Bedeutung |
|---|---|
| `baseline` | vor dem ersten Laden, nach den Modulimporten |
| `loaded` | nach Tokenizer, Sitzung, Splitter und einem `run` (der Aktivierungsspeicher gehört dazu) |
| `after_gc` | nach Loslassen und `gc.collect()`, **ohne** `malloc_trim` |
| `after_trim` | nach `malloc_trim(0)`, mit dessen Rückgabewert |

Dass `after_gc` getrennt ausgewiesen wird, ist kein Luxus: es ist der Beleg dafür, dass
`malloc_trim` den Unterschied macht, und damit der Beleg dafür, dass der Schutzschalter
aus Pitfall 2 kein toter Zweig ist.

---

## 15. State of the Art

| Alter Stand | Neuer Stand | Wann | Wirkung |
|---|---|---|---|
| "genau ein Laden je Prozess" (Plan 06.1-02) | "nie zwei Engines gleichzeitig, genau ein Laden je warmem Fenster" | diese Phase | `tools/one_load.py`, sein Gate und zwei Mutationstests |
| Grundlast ist die Messgröße | "Rückkehr zur Grundlast nach einem Indexlauf" ist die Messgröße | seit der Vergleichsmessung m7g | Der Store-Text darf keine Differenz zur Startgrundlast nennen |
| Die erste Suche lädt synchron | Die erste Suche nach einer Ruhephase antwortet lexikalisch und wärmt nach | diese Phase, hinter dem Schalter | `embed_query` bekommt `may_load` |
| `onnxruntime 1.29.0` (so steht es in STACK.md) | `onnxruntime==1.30.0` im `pyproject.toml` | vor dieser Phase | Eingefroren bis nach Phase 15; STACK.md ist an dieser Stelle überholt |

**Überholt oder veraltet:**

- STACK.md B.9 behauptet `FINDLING_EMBED_IDLE_SECONDS` als Variablennamen; ARCHITECTURE.md
  nennt einen anderen. Der Dissens ist ungelöst und MEM-01 verlangt die Festlegung.
- STACK.md nennt `onnxruntime 1.29.0` als Repo-Stand. `pyproject.toml` sagt `1.30.0`.
- `docs/admin-page.md` schreibt heute wörtlich "also gibt es dafür kein sechstes Wort". Der
  Satz steht über `waiting_for_retry` und ist dort korrekt, liest sich aber nach Zweig B
  wie eine Aussage über die Entladung. Er braucht dann eine Präzisierung.

---

## 16. Environment Availability

| Dependency | Gebraucht für | Verfügbar | Version | Fallback |
|---|---|---|---|---|
| Docker (linux/amd64) | Wegwerfcontainer für lokale Vorproben | ja | 29.5.2, OSType linux, x86_64 | keiner nötig |
| Docker mit `--platform linux/arm64` (qemu) | grobe aarch64-Gegenprobe | ja, funktioniert | , | Nur Orientierung, Zahlen nicht zitierfähig |
| `.dev/model/model.onnx` + `tokenizer.json` | jede lokale Speichermessung | ja | 118,1 MB / 17,1 MB, Stand 08.09.2026 | keiner nötig |
| GitHub Actions `ubuntu-24.04-arm` | Vorprüflauf auf Zielarchitektur | ja, in `measure.yml` und `python.yml:150` in Gebrauch | , | keiner nötig |
| ghcr.io-Image `findling_backend:dev` | Messung gegen das ausgelieferte Image | ja, `measure.yml` zieht es per Digest | , | Notfalls lokal bauen, misst dann ein Image, das niemand installiert |
| Test-Nextcloud auf Port 8090 + Backend auf 10035 | Ende-zu-Ende-Prüfung des Degradationspfads | ja, `docs/dev-setup.md`, `scripts/dev/register-exapp.sh` | NC im Container, Backend als Host-Prozess | keiner nötig |
| `uv` 0.11.7 | Testlauf, Gates | ja, laut `docs/dev-setup.md` Voraussetzungsliste | 0.11.7 | keiner |
| AWS-Box (m7g.large) | Ladezeit in ms bei kaltem Seitencache, A/B des Schalters | **Phase 15, nicht hier** | , | Für diese Phase nicht nötig, siehe 3.5 |

**Fehlende Abhängigkeiten ohne Fallback:** keine.
**Fehlende Abhängigkeiten mit Fallback:** keine. Die einzige Zahl, die diese Phase nicht
selbst erzeugen kann (Ladezeit auf m7g.large mit kaltem Seitencache), ist ausdrücklich in
Phase 15 verortet und blockiert den Bau nicht: der TTL-Default ist bis dahin ein
Vorschlagswert und der Schalter steht ab Werk auf aus.

---

## 17. Security Domain

Die Phase hat eine kleine, aber nicht leere Angriffsfläche. `security_enforcement` ist in
`.planning/config.json` nicht gesetzt, gilt also als eingeschaltet.

### Anwendbare ASVS-Kategorien

| ASVS-Kategorie | Trifft zu | Standard-Kontrolle in diesem Projekt |
|---|---|---|
| V2 Authentication | nein | Die Phase fügt keine Route hinzu |
| V3 Session Management | nein | , |
| V4 Access Control | nein, aber mit Vorbehalt | Der ACL-Vorfilter und der finale PHP-Recheck sind unberührt. **Zu prüfen ist jedoch, dass die lexikalische Degradation keine Kandidaten an den Vorfiltern vorbei ausliefert.** Der D-19-Pfad tut das heute nicht, weil er nur die Vektorliste leert; ein Test dafür gehört trotzdem in den Paritätslauf |
| V5 Input Validation | **ja** | Die neue Umgebungsvariable geht durch einen bereichsgeprüften Leser, fällt bei Unsinn auf den Default zurück und stoppt den Container nie (T-02-74). Das ist die etablierte Form in `config.py` |
| V6 Cryptography | nein | , |
| V7 Error Handling and Logging | **ja** | Die Log-Zeilen der Entladung dürfen keinen Suchtext, keinen Dateinamen und keine Trefferzahl tragen (T-02-14). Nur der Typname eines Fehlers, so wie `_warn` es macht |
| V12 Files and Resources | **ja** | `ctypes.CDLL` lädt eine Systembibliothek per festem Namen (`libc.so.6`), nicht aus einem Pfad, der aus Konfiguration kommt |

### Bekannte Bedrohungsmuster für diesen Stack

| Muster | STRIDE | Standard-Gegenmaßnahme |
|---|---|---|
| TTL sehr klein gesetzt, Container lädt und entlädt pausenlos | Denial of Service (durch den Admin, versehentlich) | Bereichsgeprüfter Leser mit einer sinnvollen Untergrenze; `0` als einziger Sonderwert |
| Suchlast gegen einen entladenen Container, jede Anfrage startet einen Warmlauf | Denial of Service | Single-Flight-Flag; `_load()` unter dem Lock erledigt den Rest strukturell |
| `ctypes.CDLL` mit einem Pfad aus der Umgebung | Elevation of Privilege | Fester Name `libc.so.6`, nie ein konfigurierbarer Pfad. Der Schutzschalter fängt nur `OSError` und `AttributeError`, nicht alles |
| Speicherzahlen im Log verraten Bestandsgröße | Information Disclosure | Die Messwerte gehören ins Messartefakt, nicht ins Container-Log. Eine Zeile "entladen" ohne Zahl reicht der Diagnose |
| Ein Gate, das sich selbst grün nullt | Repudiation | Beide Zähler bleiben monoton und nicht rücksetzbar; die Rot-Fähigkeit wird per Mutation belegt |

---

## 18. Assumptions Log

| # | Behauptung | Abschnitt | Risiko, wenn falsch |
|---|---|---|---|
| A1 | Die in 3.2 gemessene Rückgabequote überträgt sich näherungsweise auf natives aarch64 | 3.3, 3.5 | Das ganze Feature kann auf der Zielarchitektur wenig bringen. **Genau deshalb ist der Vorprüflauf Erfolgskriterium 1 und Wave 1** |
| A2 | `ubuntu-24.04-arm` ist ein tragfähiger Stellvertreter für m7g.large bei der Rückgabe**quote** (nicht bei Zeiten) | 3.5 | Die Quote könnte maschinenabhängig sein. Gegenmaßnahme: Phase 15 misst die Box-Zahl im A/B und der Bericht nennt beide |
| A3 | `FINDLING_EMBED_IDLE_RELEASE_SECONDS` ist der bessere Name | 6.2 | Kosmetisch, aber die Variable ist ausgeliefert und nicht mehr umbenennbar. Braucht Owner-Bestätigung |
| A4 | 900 s ist ein brauchbarer Vorschlagswert für die TTL | 6.4 | Geraten. Wird erst nach Phase 15 eine Messung. Schaden begrenzt, weil ab Werk aus |
| A5 | Der Poller-Leerlaufzustand ist von der Lifespan-Aufgabe sauber abfragbar, ohne die Abhängigkeitsrichtung zu brechen | 6.1 | `main.active_poller()` existiert und gibt die Instanz her; ob `armed` und ein Leerlauf-Merkmal ausreichen oder ein neues Property nötig ist, ist beim Bau zu klären |
| A6 | `may_load=False` deckt alle drei `SemanticSide`-Aufrufer ab | 5.2 | Falls ein vierter Aufrufer `embed_passages` für eine Suche benutzt, greift die Naht nicht. Am Baum geprüft: es gibt heute keinen |
| A7 | Fünf Lade-Entlade-Zyklen reichen, um den `M_MMAP_THRESHOLD`-Effekt sichtbar zu machen | Pitfall 6 | Zahl aus STACK.md übernommen, nicht selbst gemessen. Falls zu wenig, zeigt der Vorprüflauf eine flache Kurve und man erhöht |
| A8 | `enable_cpu_mem_arena=False` bleibt die richtige Einstellung auch mit Entladung | 9 | In 3.2 mit dieser Einstellung gemessen, also belegt für diese Konfiguration. Die Gegeneinstellung wurde nicht gemessen |
| A9 | Die vier Katalog-Gates und das Literal `6` sind die vollständige Kostenfolge eines sechsten Worts | 8.1 | Am Baum nachgezählt, aber `vulture` und `pyright` könnten weitere Stellen aufdecken. Der Plan sollte einen Gesamtlauf als Gegenprobe vorsehen |

---

## 19. Open Questions

1. **Gilt `may_load=False` nur bei eingeschaltetem Schalter oder immer?**
   - Bekannt: Der Vorfall vom 10.09.2026 war die allererste Suche eines Containers, der
     nie entladen hatte. Die Naht würde ihn generell abstellen.
   - Unklar: Ob eine Verhaltensänderung an der ersten Suche **außerhalb** des Schalters
     gewollt ist. MEM-01 sagt "ab Werk aus", MEM-03 sagt "der Vorfall darf nicht zum
     Regelfall werden".
   - Empfehlung: Als benannte Entscheidung in den ersten Plan, mit der Empfehlung, es
     zunächst an den Schalter zu binden und den Generalfall als Backlog-Punkt zu führen.
     Sonst misst die eine Box-Anfahrt zwei Änderungen auf einmal.

2. **Darf die Diagnose-Route (`ranked_sides`) laden?**
   - Bekannt: Sie hat keine 1,5-Sekunden-Decke und ist keine Nutzerroute; das Messwerkzeug
     der Phase 12 hängt an ihr.
   - Unklar: Ob ein Ladevorgang aus einer Diagnose heraus akzeptabel ist, wo `engine_state`
     ausdrücklich nichts laden darf.
   - Empfehlung: Ja, laden lassen, weil ein Messwerkzeug messen können muss; und im
     Runbook festhalten, dass ein Diagnoseaufruf den Container aufwärmt und deshalb vor
     einer Kaltmessung nicht gemacht werden darf.

3. **Wie genau lautet die Leerlauf-Auskunft des Pollers?**
   - Bekannt: `armed`, `cooldown`, `_idle_announced`, `_held` existieren.
   - Unklar: `_idle_announced` ist ein Log-Merker und kein Zustand (er wird bei `arm()`
     zurückgesetzt), taugt also nicht als Bedingung. Ein sauberes `busy`-Property fehlt.
   - Empfehlung: Ein kleines, ausdrücklich benanntes Property am Poller, das der Entlader
     liest, statt einen Log-Merker zweckzuentfremden.

4. **Wird der Freigabezähler auf der Admin-Seite ausgewiesen?**
   - Bekannt: Er ist die Alternative zu einem sechsten Zustandswort (Zweig A, 8.2).
   - Unklar: Ob eine Zahl ohne Wort einem Admin etwas sagt.
   - Empfehlung: Gehört mit in den Owner-Checkpoint, weil er die Kosten von Zweig A
     mitbestimmt.

5. **Wie viele Zyklen, und mit welcher Toleranz, gilt die Vorprüfung als bestanden?**
   - Bekannt: Ein negatives Ergebnis ist ein legitimer Ausgang (MEM-04).
   - Unklar: Wo die Grenze liegt. "Rückgabe unter 50 Prozent des Geladenen" wäre ein
     Vorschlag, ist aber ungesetzt.
   - Empfehlung: Die Erwartung **vor** dem Lauf in `skripte/00-ablauf.md` notieren, so wie
     die bestehenden Messläufe es tun. Eine Schwelle, die nach der Zahl festgelegt wird,
     ist keine Schwelle.

---

## 20. Sources

### Primary (HIGH confidence)

- **Eigener Messlauf, 2026-09-19**, Docker 29.5.2, `python:3.13-slim-trixie`,
  `onnxruntime==1.30.0`, echte Artefakte aus `.dev/model/`: die Tabellen in 3.2 und 3.3
- **Eigener Quellcode**, gelesen in dieser Sitzung: `backend/src/findling/embed/engine.py`,
  `embed/model.py`, `config.py`, `main.py`, `worker/poller.py`, `tools/one_load.py`,
  `api/search.py`, `api/snippets.py`, `api/diagnose.py`, `index/search.py`,
  `index/wordlist.py`, `backend/tests/test_admin_ui_contract.py`,
  `backend/tests/test_one_load.py`, `backend/tests/test_embed_engine.py`,
  `backend/appinfo/info.xml`, `php/lib/Service/ExAppService.php`,
  `php/lib/Service/AdminViewService.php`, `php/templates/admin.php`, `php/js/admin.js`,
  `.github/workflows/measure.yml`, `.github/workflows/resilience.yml`,
  `scripts/dev/measure_wordlist.sh`, `docs/dev-setup.md`, `docs/admin-page.md`
- **Eigene Messberichte**: `docs/measurements/2026-09-vergleichsmessung-m7g/README.md`
  (Abschnitte 5, 9.2, 9.3, 19.4, 19.10), `docs/measurements/2026-09-grundlast-fein/README.md`
- **Eigene Recherchedokumente v1.2**: `.planning/research/STACK.md` Teil B,
  `.planning/research/ARCHITECTURE.md` Teil B, `.planning/research/PITFALLS.md`
  Pitfalls 10 bis 14, 17

### Secondary (MEDIUM confidence, aus den Recherchedokumenten übernommen, hier nicht neu geprüft)

- microsoft/onnxruntime Issue #14590, Maintainer-Aussage "del just removes a reference ...
  you might need to trigger python garbage collection"
- microsoft/onnxruntime Issue #26831 (offen), RSS wächst trotz `ReleaseSession` und
  `ReleaseEnv`, Arena an und aus ohne Wirkung, mimalloc ohne Wirkung, gemeldet gegen 1.23.2
- man7.org `malloc_trim(3)`, "since glibc 2.8 this function frees memory in all arenas and
  in all chunks with whole free pages"
- man7.org `mallopt(3)`, dynamische `M_MMAP_THRESHOLD`-Anpassung, `DEFAULT_MMAP_THRESHOLD_MAX`

### Tertiary (LOW confidence, kennzeichnungspflichtig)

- Die aarch64-Zahlen aus 3.3 sind **emuliert** und tragen qemu-Aufschlag. Sie belegen die
  Richtung (gc allein gibt fast nichts zurück, `malloc_trim` gibt fast alles zurück) und
  keine einzige zitierfähige Absolutzahl.

---

## Metadata

**Confidence breakdown:**

- Integrationspunkte im eigenen Baum: **HIGH**, jede Aussage an Datei und Zeile belegt
- Speicher-Mechanik `gc.collect` + `malloc_trim`: **HIGH** auf x86_64, in dieser Sitzung
  im Basis-Image mit den echten Artefakten gemessen
- Speicher-Mechanik auf aarch64: **MEDIUM**, Richtung bestätigt, Absolutzahlen offen; der
  Vorprüflauf in `measure.yml` schließt die Lücke ohne Kosten
- Degradationspfad und 1,5-Sekunden-Frage: **HIGH**, Vorfall und Zahlen aus dem eigenen
  Messbericht, Code-Naht am Baum belegt
- Kostenfolge des sechsten Zustandsworts: **HIGH**, Gates und Katalogdateien nachgezählt
- TTL-Default und Ladezeit auf der Box: **LOW**, geraten, gehört nach Phase 15
- Variablenname: **MEDIUM**, Empfehlung mit Begründung aus dem eigenen Bestand, aber
  Owner-Bestätigung nötig

**Research date:** 2026-09-19
**Valid until:** rund 30 Tage. Der einzige schnell alternde Teil ist der onnxruntime-Stand,
und der ist bis nach Phase 15 ausdrücklich eingefroren.
