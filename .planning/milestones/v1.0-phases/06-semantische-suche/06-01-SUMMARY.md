---
phase: 06-semantische-suche
plan: 01
subsystem: infra
tags: [fastembed, onnxruntime, sqlite-vec, semantic-text-splitter, onnx, docker, quantisierung, multilingual-e5-small, vec0]

# Dependency graph
requires:
  - phase: 02-store-und-index
    provides: "store/repo.py mit _connect und PRAGMA query_only = 1, die Leseseite, auf die A12 zielt"
  - phase: 03-ocr
    provides: "das Muster der fail-closed Datenstufe im Dockerfile (wngerman, tesseract) und THIRD-PARTY.md"
provides:
  - "vier exakt gepinnte Pakete des semantischen Pfads plus onnx als reine Baugruppe"
  - "ein Abbild, das ein selbst quantisiertes int8-Modell (118.101.091 Byte) und vec0.so an festen Pfaden traegt, ohne Netzwerk zur Laufzeit"
  - "ein Bau-Gatter, das eine nicht quantisierte Einbettungstabelle abfaengt, bevor 266 MB ins Abbild wandern"
  - "die beantworteten Annahmen A12 und A13, auf amd64 und arm64, mit ihrer Konsequenz"
  - "FINDLING_EMBED_MODEL_DIR, FINDLING_VEC0_PATH und HF_HUB_OFFLINE als Abbildkonstanten"
affects: [06-04 Vektorspeicher und Schema, 06-05 Einbettungen, 06-10 Offline-Test, jeder Plan der gegen vec0 programmiert]

# Tech tracking
tech-stack:
  added: [fastembed 0.8.0, onnxruntime 1.29.0, sqlite-vec 0.1.9, semantic-text-splitter 0.32.0, onnx 1.22.0 (nur Bauzeit), intfloat/multilingual-e5-small]
  patterns:
    - "Baugruppe statt Abhaengigkeit: onnx in [dependency-groups].quantize, damit es die Laufzeitstufe nie erreicht"
    - "zweiseitiges Groessenfenster als Bau-Gatter, das rot werden kann und dabei die Ausgabedatei loescht"
    - "benannter Docker-Bau-Kontext fuer Werkzeuge ausserhalb von backend/, statt einer zweiten Kopie der Datei"
    - "Probe mit zwei Auffuehrungsformen: pytest lokal, einfaches Skript im Abbild, in dem pytest fehlt"

key-files:
  created:
    - scripts/dev/quantize_model.py
    - backend/tests/test_vec_extension_probe.py
    - backend/docker/licenses/COPYING.sqlite-vec
    - backend/docker/licenses/COPYING.multilingual-e5-small
    - docs/measurements/2026-09-05-welle0-proben/README.md
  modified:
    - backend/Dockerfile
    - backend/pyproject.toml
    - backend/uv.lock
    - THIRD-PARTY.md
    - .github/workflows/docker.yml

key-decisions:
  - "A12 ist positiv: vec0-KNN laeuft unter PRAGMA query_only = 1 auf amd64 und arm64, die Leseseite von repo.py behaelt ihr Pragma und Plan 06-04 aendert daran nichts"
  - "A13 ist positiv: die CPython-Uebersetzung im Abbild traegt enable_load_extension, eine eigene Python-Uebersetzung wird nicht gebraucht"
  - "load_extension muss VOR PRAGMA query_only laufen, weil das Laden selbst eine Zustandsaenderung der Verbindung ist"
  - "sqlite-vec leitet den Elementtyp nicht aus der Spaltendeklaration ab: vec_int8() gehoert an die Aufrufstelle, sonst wird ein Blob als float32 gelesen"
  - "onnx wird gebraucht, weil onnxruntime.quantization es importiert und onnxruntime selbst nicht davon abhaengt; es bleibt eine reine Baugruppe"
  - "scripts/dev/quantize_model.py bleibt an seinem Pfad und kommt ueber einen benannten Bau-Kontext ins Abbild, statt nach backend/ dupliziert zu werden"
  - "sentencepiece.bpe.model reist mit, obwohl der fastembed-Vertrag es nicht verlangt; die Pflichtmenge ist config.json, tokenizer.json, tokenizer_config.json, special_tokens_map.json"
  - "die vec0-Pruefsumme ist architekturabhaengig und wird ueber TARGETARCH ausgewaehlt; eine unbekannte Architektur bricht den Bau ab statt die Pruefung zu ueberspringen"

patterns-established:
  - "Messbericht vor Schemafestlegung: eine Annahme aus dem Assumptions Log wird beantwortet, bevor eine Tabelle entsteht"
  - "Jedes Gatter bekommt seinen Gegenbeweis: das Groessenfenster wird gegen ein Miniaturmodell rot gefahren, die Erweiterungsprobe gegen einen absichtlich falschen Pfad"

requirements-completed: [SEM-01]

# Metrics
duration: 35min
completed: 2026-09-05
---

# Phase 6 Plan 01: Bausteine der semantischen Suche Summary

**Ein Abbild, das ein selbst aus fp32 quantisiertes int8-Modell (118.101.091 Byte, Faktor 3,98) und vec0.so an festen Pfaden offline bereithaelt, mit einem Bau-Gatter gegen die stille 266-MB-Falle, und die auf beiden Architekturen beantworteten Annahmen A12 und A13.**

## Performance

- **Duration:** rund 35 min
- **Started:** 2026-09-05T02:51:00Z
- **Completed:** 2026-09-05T03:25:00Z
- **Tasks:** 3 von 3
- **Files modified:** 14 (5 neu, 9 geaendert)

## Accomplishments

- **Die teuerste stille Falle der Phase ist nicht eingetreten und ist ab jetzt bewacht.** `quantize_dynamic` hat die Einbettungstabelle mitquantisiert: 470.268.510 Byte hinein, 118.101.091 Byte heraus, Verhaeltnis 3,98 zu 1. Der erwartete Wert war 117.567.128, die von intfloat gelieferte int8-Datei wiegt 118.346.824. Waere die Tabelle mit ihren 81,7 Prozent aller Parameter fp32 geblieben, laege das Ergebnis bei rund 384 MB, und **nichts** haette fehlgeschlagen. Das Gatter faengt beide Richtungen ab und ist als rot fahrbar belegt.
- **A12 und A13 sind aktenkundig, bevor ein Vektorschema existiert.** Beide positiv, auf amd64 und auf arm64, in jedem Lauf mit abgeklemmtem Netzwerk. Die Leseseite behaelt `PRAGMA query_only = 1`; die Entwurfsentscheidung, die ein Nein erzwungen haette, entfaellt.
- **Das Abbild spricht fuer Modell und Erweiterung nicht nach draussen.** Sechs Dateien einer festgenagelten Modellfassung, jede gegen eine sha256 im selben `RUN` geprueft, die fp32-Datei im Bau geloescht, `HF_HUB_OFFLINE=1` und zwei feste Pfade in der Laufzeitstufe.
- **Zwei Befunde fuer Plan 06-04 fielen nebenbei ab:** die Reihenfolge `load_extension` vor `query_only`, und `vec_int8()` an der Aufrufstelle statt eines nackten Blobs.

## Task Commits

1. **Task 1: Vier neue Kanten, exakt gepinnt, jede mit ihrer Begruendung** - `ace8616` (feat)
2. **Task 2: Das Modell selbst quantisieren und mit der Erweiterung ins Abbild backen** - `a6f780c` (feat)
3. **Task 3: Die zwei Fuenf-Minuten-Proben, A12 und A13, aktenkundig** - `7f0157f` (test)

## Files Created/Modified

- `scripts/dev/quantize_model.py` - quantisiert fp32 nach int8 und verweigert ein Ergebnis ausserhalb von 100 MB bis 130 MiB; loescht die Ausgabedatei bei Verletzung, damit ein spaeteres COPY nichts aufsammeln kann
- `backend/Dockerfile` - neue Modellstufe (sechs Dateien, sechs Pruefsummen, Quantisierung, fp32 geloescht), vec0-Kopie mit Pruefsumme je Architektur, drei neue ENV-Zeilen, Kopf auf zwei Downloads gehoben
- `backend/pyproject.toml` - vier neue direkte Kanten mit `==`, plus die Baugruppe `quantize` mit `onnx==1.22.0`
- `backend/uv.lock` - aufgeloest, 74 Pakete
- `THIRD-PARTY.md` - neuer Abschnitt fuer den semantischen Pfad: vier Pakete, zwei mitgeschleppte Netzwerkbibliotheken, das Modell, und warum `usearch` nicht darinsteht
- `backend/docker/licenses/COPYING.sqlite-vec` - Apache-2.0 woertlich aus `LICENSE-APACHE` am Tag `v0.1.9`
- `backend/docker/licenses/COPYING.multilingual-e5-small` - MIT-Text plus die Herkunft der Lizenzangabe, weil das Modellrepositorium keine Lizenzdatei fuehrt
- `backend/tests/test_vec_extension_probe.py` - die Proben A13 (Gatter) und A12 (Messung), lauffaehig als Testdatei und als Skript
- `docs/measurements/2026-09-05-welle0-proben/README.md` - Datum, Architektur, Abbildkennung, Kommandozeile, Antwort, Konsequenz, fuer beide Proben
- `.github/workflows/docker.yml` - `build-contexts: scripts=./scripts` und der Probenschritt gegen den veroeffentlichten Digest auf beiden Architekturen
- `.github/workflows/resilience.yml`, `.github/workflows/deploy-harp.yml`, `docs/ocr.md`, `docs/dev-setup.md` - dieselbe Bau-Kontext-Flagge, damit kein bestehender Aufrufer bricht

## Der Zuwachs der Abbildgroesse

Gemessen mit `du -sxk /` im laufenden Container, also an der Groesse, die die
Systemplatte der Box wirklich fuellt, und beide Male mit demselben Verfahren:

| Stand | Groesse |
|---|---|
| vor diesem Plan (`b6199d7`, eigener Bau) | 385.560 KiB, rund 394,8 MB |
| nach diesem Plan | 722.652 KiB, rund 740,0 MB |
| **Zuwachs** | **337.092 KiB, rund 345,2 MB** |

Aufgeschluesselt:

| Anteil | Groesse |
|---|---|
| Modellverzeichnis (int8 118 MB, tokenizer.json 17 MB, sentencepiece 5 MB, Konfiguration) | 136.988 KiB |
| Zuwachs der virtuellen Umgebung (onnxruntime 67 MB, numpy mit numpy.libs 70 MB, semantic-text-splitter 18 MB, tokenizers, hf-xet, protobuf) | 198.472 KiB |
| vec0.so und die zwei Lizenztexte | 164 KiB |

**Einordnung, ehrlich:** die Recherche erwartete 200 bis 260 MB, es sind 345 MB
geworden. Die Abweichung liegt **nicht** am Modell, das mit 137 MB genau so
schwer ist wie vorhergesagt, sondern an der Python-Abhaengigkeitshuelle, die die
Recherche zu niedrig angesetzt hat. Der Wert bleibt unter der Grenze von 400 MB,
ab der ein Befund vorliegt, und er deutet weder auf eine nicht quantisierte
Einbettungstabelle noch auf ein versehentlich mitkopiertes fp32-Modell hin:
beides ist getrennt geprueft (`find / -xdev -name '*.onnx' -size +200M` findet
nichts, und genau eine .onnx-Datei liegt im Groessenfenster). Fuer die 40-GB-
Systemplatte der Box, auf der Abbilder seit Docker 29 unter
`/var/lib/containerd` liegen, ist das einzuplanen, aber unkritisch; die
containerd-Korrektur aus Plan 05-14 gilt unveraendert weiter.

## Decisions Made

- **A12 positiv, also bleibt die Leseseite, wie sie ist.** Der Ablauf ist genau der spaetere: Tabelle mit `int8[384]`, 512 Vektoren, Verbindung zu, Datei wieder auf, Erweiterung laden, `PRAGMA query_only = 1`, fuenf Nachbarn. Auf beiden Architekturen fuenf Treffer.
- **Die Reihenfolge ist die eigentliche Erkenntnis.** `load_extension` ist selbst eine Aenderung am Verbindungszustand und muss vor `query_only` passieren. Wer es andersherum macht, bekommt ein Nein, das wie ein Nein auf A12 aussieht und keines ist.
- **`vec_int8()` gehoert an die Aufrufstelle.** sqlite-vec liest einen 384-Byte-Blob ohne Markierung als float32 und weist ihn ab. Der Fehler ist reproduziert, im Messbericht festgehalten und im Test kommentiert, damit Plan 06-04 ihn nicht ein zweites Mal findet.
- **`onnx` ist eine Baugruppe, keine Abhaengigkeit.** 19 MB Graphmanipulation, die der Suchpfad nie aufruft, gehoeren nicht in ein Abbild, das auf einer 4-GB-Box laeuft.
- **Die vec0-Pruefsumme ist je Architektur eingetragen, nicht weggelassen.** Beide Werte stammen aus den beiden manylinux-Raedern von sqlite-vec 0.1.9, deren eigene sha256 mit der in `uv.lock` uebereinstimmt. Eine Architektur ohne eingetragene Summe bricht den Bau ab.
- **Der Messbericht nennt seinen Vorbehalt.** Die arm64-Zahlen stammen aus einem emulierten Bau. Emuliert ist die Befehlssatzarchitektur, nicht die Software: es laufen die echten aarch64-Binaerdateien von CPython, SQLite und vec0.so, und genau darauf zielen A12 und A13. Ueber Geschwindigkeit sagt der Bericht deshalb nichts.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `scripts/dev/quantize_model.py` liegt ausserhalb des Bau-Kontextes**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt das Skript an `scripts/dev/quantize_model.py` und verlangt zugleich, dass die Modellstufe von `backend/Dockerfile` es aufruft. Der Bau-Kontext ist aber `./backend` (`docker.yml` Z. 154, und ebenso in `resilience.yml`, `deploy-harp.yml` und zwei Dokumentationsstellen). Eine Datei ausserhalb des Kontextes ist fuer `COPY` nicht erreichbar; die im Plan angegebene Verifikationszeile haette so nicht laufen koennen.
- **Fix:** Ein benannter zusaetzlicher Bau-Kontext (`--build-context scripts=./scripts`, im Dockerfile `COPY --from=scripts dev/quantize_model.py`). Die Alternativen waren, den Kontext auf die Wurzel zu heben (jede `COPY`-Zeile und alle fuenf Aufrufer, plus ein neues .dockerignore) oder die Datei nach `backend/` zu duplizieren (zwei Fassungen desselben Gatters, die auseinanderlaufen koennen). Der benannte Kontext kostet fuenf einzeilige Aenderungen und laesst die im Plan festgeschriebene Artefaktzeile unangetastet.
- **Files modified:** backend/Dockerfile, .github/workflows/docker.yml, .github/workflows/resilience.yml, .github/workflows/deploy-harp.yml, docs/ocr.md, docs/dev-setup.md
- **Verification:** Bau auf amd64 und emuliertem arm64 gruen; ohne die Flagge bricht der Bau an der `COPY`-Zeile ab statt spaeter.
- **Committed in:** `a6f780c`

**2. [Rule 3 - Blocking] `onnxruntime.quantization` importiert `onnx`, das keine Abhaengigkeit von onnxruntime ist**

- **Found during:** Task 2
- **Issue:** `from onnxruntime.quantization import quantize_dynamic` endet mit `ModuleNotFoundError: No module named 'onnx'`. Ohne dieses Paket ist der zentrale Schritt des Plans nicht ausfuehrbar. Der Plan sieht es nirgends vor.
- **Fix:** `onnx==1.22.0` als eigene Gruppe `[dependency-groups].quantize`, die weder `uv sync --no-dev` in der Baustufe noch das schlichte `uv sync` des Gates-Jobs installiert. Die Modellstufe fordert sie mit `--group quantize` an; die Laufzeitstufe kopiert ihre virtuelle Umgebung aus der Baustufe und sieht sie nie.
- **Legitimitaet vor dem Pin geprueft** (Owner-Regel, und die Ausnahme fuer Paketinstallationen in den Abweichungsregeln): PyPI-API am 05.09.2026 abgefragt. `onnx` 1.22.0, hochgeladen 2026-06-15, Lizenz Apache-2.0, Repositorium `github.com/onnx/onnx`, `requires_python >=3.10`, Rad `cp312-abi3-manylinux_2_28_aarch64` deckt Python 3.13 auf der ARM-Seite ab. Das ist die Referenzimplementierung des ONNX-Formats und das Schwesterpaket von onnxruntime, kein Fund aus einer Suche. Die Installation ist nicht fehlgeschlagen, es gab also keinen Anlass fuer ein Prueftor.
- **Files modified:** backend/pyproject.toml, backend/uv.lock, backend/Dockerfile
- **Verification:** `uv lock --check` gruen, Quantisierung laeuft in beiden Bauten durch, `onnx` ist in keiner Laufzeitstufe.
- **Committed in:** `a6f780c`

**3. [Rule 1 - Bug] Die Probe schrieb int8-Vektoren, die sqlite-vec als float32 las**

- **Found during:** Task 3
- **Issue:** `INSERT INTO chunk_vectors(rowid, embedding) VALUES (?, ?)` mit einem 384-Byte-Blob endet mit `OperationalError: Inserted vector for the "embedding" column is expected to be of type int8, but a float32 vector was provided.` sqlite-vec leitet den Elementtyp nicht aus der Spaltendeklaration ab.
- **Fix:** `vec_int8(?)` beim Schreiben und beim `MATCH`. Der Befund ist im Test kommentiert und im Messbericht als eigener Abschnitt festgehalten, weil Plan 06-04 sonst dieselbe halbe Stunde noch einmal ausgibt.
- **Files modified:** backend/tests/test_vec_extension_probe.py, docs/measurements/2026-09-05-welle0-proben/README.md
- **Verification:** Probe gruen, fuenf Nachbarn, auf beiden Architekturen.
- **Committed in:** `7f0157f`

**4. [Rule 1 - Bug] Das Skript beschriftete eine Konstante mit der Herleitung des jeweiligen Eingabewerts**

- **Found during:** Task 2
- **Issue:** Die Zeile `expected {EXPECTED_BYTES} bytes after a complete int8 pass ({source_size} / 4)` druckte die Konstante 117.567.128 und daneben die Division der tatsaechlichen Eingabe. Bei jeder anderen Eingabe als dem echten Modell ergab das eine falsche Aussage, die beim Rotfahren des Gatters gegen ein Miniaturmodell sofort sichtbar wurde.
- **Fix:** Zwei getrennte Zeilen: die Konstante, fuer die das Fenster gemessen wurde, und ein Viertel der vorliegenden Eingabe.
- **Files modified:** scripts/dev/quantize_model.py
- **Verification:** Abbild danach neu gebaut, Ausgabe stimmt in beiden Faellen.
- **Committed in:** `a6f780c`

### Abweichungen, die keine Autoreparatur sind, sondern eine Auslegung des Plans

**5. `usearch` erscheint als Wort im Kommentar der sqlite-vec-Zeile**

Die Handlungsanweisung von Task 1 verlangt ausdruecklich, dass der Kommentar an
der sqlite-vec-Zeile sagt, wo der Ausweichpfad beschrieben ist. Das
Abnahmekriterium derselben Aufgabe verlangt, dass `usearch` in
`backend/pyproject.toml` nicht vorkommt. Beides gleichzeitig geht nicht.
Gewaehlt wurde die Handlungsanweisung, weil der Sinn des Kriteriums ist, dass
das Paket **nicht installiert** wird, und das ist geprueft: `usearch` steht in
keiner Abhaengigkeitszeile von `pyproject.toml` und als Paket nicht in
`uv.lock`.

**6. `sentencepiece.bpe.model` reist mit, obwohl fastembed es nicht verlangt**

Der Plan traegt auf, die Pflichtmenge aus dem fastembed-Vertrag abzulesen. Das
ist geschehen: `fastembed/common/preprocessor_utils.py::load_tokenizer`
verlangt `config.json`, `tokenizer.json`, `tokenizer_config.json` und
`special_tokens_map.json`. `sentencepiece.bpe.model` steht nicht darin, ist aber
in der Dateiliste des Plans genannt. Es wird geholt, geprueft und mitgeliefert
(4,8 MB), und im Dockerfile steht der Satz, dass es das eine Stueck ist, das ein
spaeterer Plan wieder streichen kann.

---

**Total deviations:** 4 autorepariert (2 blockierend, 2 Fehler), 2 Auslegungen
**Impact on plan:** Keine Ausweitung des Umfangs. Die zwei blockierenden Punkte waren beide Voraussetzungen dafuer, dass der zentrale Schritt des Plans ueberhaupt laufen kann; die zwei Fehler waren in der eigenen, in diesem Plan geschriebenen Arbeit.

## Issues Encountered

- **Der Vergleichsstand fuer die Groessenmessung existierte nicht mehr als Abbild.** Geloest ueber einen abgetrennten `git worktree` auf `b6199d7`, dort gebaut, gemessen, Arbeitsbaum wieder entfernt. Kein `git stash`, kein Zuruecksetzen des Hauptbaums.
- **`docker image inspect --format '{{.Size}}'` und `docker images` liefern unter Docker 29 mit containerd-Speicher nicht dasselbe Mass**, je nachdem ob ein Abbild schon entpackt ist. Beide Zahlen der Tabelle oben stammen deshalb aus `du -sxk /` im laufenden Container, was ohnehin die Zahl ist, die die Systemplatte betrifft.
- **Der Bind-Mount der Testdatei ins Abbild braucht `MSYS_NO_PATHCONV=1`** unter Git Bash, sonst baut die Shell den Pfad um. Betrifft nur die Entwicklungsmaschine; in `docker.yml` steht `${GITHUB_WORKSPACE}`.

## Offene Verifikation

Ein Punkt der Abnahme laesst sich in dieser Ausfuehrung nicht abschliessen und
ist bewusst offen benannt: **ein gruener Lauf von `docker.yml` auf beiden
Architekturen**. Der Executor darf nicht pushen, und der Probenschritt laeuft
gegen den veroeffentlichten Digest, den erst ein Lauf nach dem Push erzeugt. Was
statt dessen belegt ist: dieselbe Probe, mit demselben Kommando und demselben
`--network none`, gegen ein amd64- und ein arm64-Abbild aus demselben
Dockerfile, beide Antworten im Messbericht. Der erste Lauf nach dem Push des
Orchestrators ist die Bestaetigung, und er kann nur an der Umgebung scheitern,
nicht an der Antwort.

## User Setup Required

None - keine externe Konfiguration noetig. Das Abbild braucht fuer Modell und
Erweiterung kein Netzwerk und keinen Schluessel.

## Next Phase Readiness

- **Plan 06-04 kann sein Schema entwerfen.** Die zwei Fragen, die es beruehrt haetten, sind beantwortet: `query_only` bleibt, und `_connect` braucht `enable_load_extension` fuer beide Verbindungsarten (heute ruft es das nirgends).
- **Plan 06-05 findet das Modell an `FINDLING_EMBED_MODEL_DIR` und die Erweiterung an `FINDLING_VEC0_PATH`.** Beide Werte sind Abbildkonstanten; die Settings-Felder, die sie lesen, gehoeren in 06-05 und existieren noch nicht.
- **Zwei Punkte fuer die Nachfolger, damit sie nicht doppelt gefunden werden:** `vec_int8()` an der Aufrufstelle, und die E5-Praefixe `"query: "` und `"passage: "`, die fastembed bei einem selbst registrierten Modell **nicht** automatisch setzt (Fallstrick 3 der Recherche, noch offen).
- **Kein Blocker.** Der Zuwachs von 345 MB ist gemessen, eingeordnet und unter der Befundgrenze.

## Self-Check: PASSED

Alle fuenf angelegten Dateien liegen auf der Platte, alle vier Commits stehen in
`git log`. Zusaetzlich geprueft: `uv lock --check` gruen, `ruff`, `ruff format`,
`pyright` und `vulture` gruen, `pytest -q` mit 989 bestandenen und 11
uebersprungenen Tests, und `test_workflow_pins.py` gruen nach den drei
Workflow-Aenderungen.

---
*Phase: 06-semantische-suche*
*Completed: 2026-09-05*
