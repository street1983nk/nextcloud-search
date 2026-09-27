# Phase 22: Messanfahrt BL-F03 - Pattern Map

**Mapped:** 2026-09-25
**Files analyzed:** 22 neue oder geänderte Dateien
**Analogs found:** 21 / 22 (einzig das Ablaufskript mit Deckel-Timer hat nur ein Teilvorbild)

Grundregel für alle Box-Werkzeuge (Präzedenz, gilt für jede Zeile unten): Kommentare und Protokollzeilen ASCII, keine Em- oder En-Dashes, kein CR, `#!/bin/sh` + `set -eu` oder `#!/usr/bin/env python3`, jede Stellschraube als `VAR="${VAR:-vorgabe}"`, keine Maschinenpfade (`/home/`, `sys.path.insert`), kein Passwort auf einer Kommandozeile, Ausgabe nur Zahlen, Kennungen, Prozessnamen (T-02-14).

## File Classification

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Vorbild | Qualität |
|---|---|---|---|---|
| `scripts/ops/cpu_sampler.sh` (W1) | utility (Sampler) | streaming (Zeitreihe, CSV) | `scripts/ops/rss_sampler.sh` | exakt |
| `scripts/ops/proc_anon_sampler.sh` (W2) | utility (Sampler) | streaming | `scripts/ops/rss_sampler.sh` | exakt (Form), Datenquelle neu |
| `scripts/ops/ocr_slot_probe.py` (W3) | utility (Probe) | batch | `extract/sandbox.py:287` (`ExtractionWorker`) + `scripts/ops/search_load.py` (Kopf, stdlib, Shebang) | role-match |
| `.github/workflows/measure.yml` (W4 + B7) | config (CI) | batch | `measure.yml` Schritte B und D (Zeilen 254-267, 338-350) | exakt |
| `backend/tests/test_ops_scripts.py` (W1-W3 aufnehmen) | test | statisch + Verhalten | eigene Zeilen 104-146, 702-788 | exakt |
| `docs/measurements/<JJJJ-MM>-v13-messung/skripte/92d-wechsel.sh` | Box-Werkzeug | request-response (occ, docker) | `2026-09-nachfolgefassungen/skripte/92c-wechsel.sh` | exakt (Nachfolgefassung) |
| `.../92e-umgebung.sh` (Containerneubau mit Env) | Box-Werkzeug | transform (inspect -> create) | `.github/workflows/deploy-harp.yml:4510-4611` + `92c` Schritt 11 | role-match |
| `.../90e-einzelliste.py` | Box-Werkzeug (Leser) | file-I/O, read-only SQLite | `2026-09-nachmessung-m7g/skripte/68-bestand-endungen.py` | exakt |
| `.../91m-langsame-aufrufe.py` (M-01-Leser) | Box-Werkzeug (Leser) | file-I/O, JSON-Zeilen | `2026-09-v12-messung/skripte/96c-lesen.py` + `68-bestand-endungen.py` | role-match |
| `.../94c-bodensatz-zyklen.sh` | Box-Werkzeug | batch (Zyklen, Marken) | `2026-09-v12-messung/skripte/94b-grundlast-rueckkehr.sh` | exakt (Nachfolgefassung) |
| `.../95c-kaltstart.sh` | Box-Werkzeug | request-response (Nutzerroute) | `2026-09-v12-messung/skripte/95b-wiederaufwaermen.sh` | exakt (Nachfolgefassung) |
| `.../98d-dismax-probe.py` | Box-Werkzeug (Probe im Container) | batch, In-Prozess | `2026-09-v12-messung/skripte/73-bestand-sonde.py` + `backend/tests/test_field_plan_ranking.py:189-288` | exakt |
| `.../00-lauf.sh` (Ablauf + `shutdown -h`) | Box-Werkzeug (Orchestrierung) | event-driven, detached | `2026-09-v12-messung/skripte/96-volllauf.sh` | partial (Timer neu) |
| `.../00-ablauf.md` (Erwartungen E1..En, dismax-Regel, Abbruchwerte ab 40) | doc | - | `2026-09-v12-messung/skripte/00-ablauf.md` (Abschnitte 1-5) | exakt |
| `docs/measurements/<JJJJ-MM>-v13-messung/README.md` | doc (Bericht) | - | `2026-09-v12-messung/README.md` | exakt |
| `backend/tests/test_measurement_scripts.py` (neue Wächter, `NARROW_SCOPE_DIRS`, 92c/99d-Umstellung, ggf. Ratsche) | test | statisch | eigene Zeilen 92, 106-108, 343-350, 2563-2647, 2750-2780, 2877-2912, 2944-2980, 1096-1097 | exakt |
| `backend/tests/test_dismax_probe.py` | test | Unit gegen Sechs-Feld-Index | `backend/tests/test_field_plan_ranking.py` | exakt |
| `backend/src/findling/query/rewrite.py` (nur falls MESS-09 positiv, D-04) | service (Query-Bau) | transform | eigene Zeilen 575-717 | exakt |
| `backend/tests/test_query_rewrite.py`, `test_field_plan_ranking.py`, `test_search_endpoint.py` (Fälle, falls positiv) | test | - | bestehende Dateien | exakt |
| `docs/performance.md` (Abschnitt v1.3-Anfahrt + Nachträge) | doc | - | `docs/performance.md:4158-4455` (v1.2-Anfahrt, Nachträge) | exakt |
| `docs/language-analyzers.md` (dismax-Entscheid) | doc | - | eigener Abschnitt "What a question searches"/"Measured numbers" | exakt |
| `docs/runbook-messbox.md` (Nachträge) | doc | - | eigene Nachtrag-Abschnitte (2.1 "Nachtrag vom 21.09.") | exakt |

## Pattern Assignments

### `scripts/ops/cpu_sampler.sh` (W1, utility, streaming)

**Analog:** `scripts/ops/rss_sampler.sh` (169 Zeilen, UNVERÄNDERT lassen, CONTEXT)

**Kopf und Aufruf** (Zeilen 31-63): Usage-Zeile im Kopf, Pflichtargument Containername, Intervall als ganze Sekunden, `exit 2` bei falscher Benutzung.
```sh
set -eu

PREFIX='findling-rss'
DEFAULT_INTERVAL=5

NAME="${1:-}"
INTERVAL="${2:-$DEFAULT_INTERVAL}"
OUTPUT="${3:-}"
...
case "$INTERVAL" in
    '' | *[!0-9]*)
        echo "rss_sampler: the interval has to be a whole number of seconds, got '$INTERVAL'" >&2
        exit 2
```
Für W1: `PREFIX='findling-cpu'`, eigener Präfix, damit `grep '^findling-cpu '` aus einem gemeinsamen Log filtert (Kopf Zeilen 25-29).

**Pfadbildung der cgroup, beide Treiber** (Zeilen 72-104), wörtlich übernehmen, nur `memory.stat` durch `cpu.stat` ersetzen:
```sh
if ! CONTAINER_ID=$(docker inspect -f '{{.Id}}' "$NAME" 2>/dev/null); then
    echo "rss_sampler: docker does not know a container called '$NAME'" >&2
    exit 1
fi
CGROUP_ROOT="${FINDLING_CGROUP_ROOT:-/sys/fs/cgroup}"
CGROUP=''
for candidate in \
    "$CGROUP_ROOT/system.slice/docker-$CONTAINER_ID.scope" \
    "$CGROUP_ROOT/docker/$CONTAINER_ID"; do
    if [ -r "$candidate/memory.stat" ]; then
        CGROUP="$candidate"
        break
    fi
done
if [ -z "$CGROUP" ]; then
    echo "rss_sampler: no readable memory.stat for container $NAME" >&2
    ...
    exit 1
fi
```
Die Tests prüfen genau die Zeichenketten `system.slice/docker-` und `/docker/$CONTAINER_ID` (`test_ops_scripts.py:127-131`), also die Variable `CONTAINER_ID` so benennen. `FINDLING_CGROUP_ROOT` ist die Attrappen-Naht für einen Verhaltenstest.

**Abtastung** (Research-Skizze, Zeilen 409-415 in 22-RESEARCH.md, gegen `sample()` Zeilen 126-136 gebaut):
```sh
usage=$(awk '$1 == "usage_usec" { print $2 }' "$CGROUP/cpu.stat")
box=$(awk '$1 == "cpu" { print $2+$3+$4+$5+$6+$7+$8+$9, $5 }' /proc/stat)   # gesamt, idle
printf '%s,%s,%s\n' "$(date +%s)" "$usage" "$box"
```

**Schluss und Verweigerung** (Zeilen 106-112 `emit`, 141-154 `finish` + `trap finish INT TERM`, 156-169 Schleife). Pflichtsätze, die ein Test verlangt (Muster `test_the_sampler_refuses_rather_than_writing_zeroes`, Zeile 141-145): eine "no readable cpu.stat"-Meldung und "not one sample was written". Zusätzlich (Pitfall 4): verschwindet die cgroup beim Containerneubau, schreibt W1 eine klare Schlusszeile statt unter `set -eu` stumm zu sterben, also vor jedem Lesen `[ -r "$CGROUP/cpu.stat" ] || finish`.

---

### `scripts/ops/proc_anon_sampler.sh` (W2, utility, streaming)

**Analog:** `scripts/ops/rss_sampler.sh`, gleiche Blöcke wie W1 (Argumente Zeilen 42-63, Werkzeugprüfung 65-70, `emit`/`finish`/`trap` 106-169).

**Unterschied:** keine cgroup, sondern `docker exec` in den Container und je PID `/proc/<pid>/status` mit den Feldern `Name`, `RssAnon`, `VmHWM`. **Nie `cmdline`** (T-02-14: Argumente können Pfade tragen). Die Existenzprüfung des Containers wie Zeilen 74-79. Ein Test soll `cmdline` im Text verbieten, analog `DOCKER_MEMORY_SHORTCUT not in text` (`test_ops_scripts.py:134-138`).

---

### `scripts/ops/ocr_slot_probe.py` (W3, utility, batch)

**Analog A (Form):** `scripts/ops/search_load.py`, erzwungen durch `test_ops_scripts.py:702-788`: Shebang `#!/usr/bin/env python3\n`, kein Dash/CR, keine Maschinenpfade (`machine_shapes`), nur Standardbibliothek außerhalb von `findling` (Test `imported_packages(...) - set(sys.stdlib_module_names)`, Zeilen 779-788; für W3 muss die Ausnahme `findling` benannt werden, weil die Probe im Abbild läuft).

**Analog B (Kern):** `backend/src/findling/extract/sandbox.py:287-344`
```python
class ExtractionWorker:
    def __init__(self, *, max_files: int | None = None, timeout_seconds: float | None = None) -> None:
    ...
    def run(self, path: str, mime: str, size: int, *, route: str | None = None,
            timeout_seconds: float | None = None) -> ExtractionOutcome:
        outcome = self._ask((_JOB_EXTRACT, path, mime, size, route), timeout_seconds)
    ...
    def stop(self) -> None:
```
Aufruf je Slot: `worker.run(path, "application/pdf", size, route="ocr")` (`Route.OCR = "ocr"`, `dispatch.py:69`); `route` ist bewusst ein String (Docstring Zeilen 327-331). Je Thread ein eigener `ExtractionWorker`, am Ende `stop()`. CPU-Zeit aus `cpu.stat` der eigenen cgroup, nicht `RUSAGE_CHILDREN` (Research, Alternatives). Ausgabe: `arch`, sichtbare CPUs (`os.sched_getaffinity(0)`), Seiten je Sekunde je N, keine Textinhalte.

**Scan-Material:** `build_load_corpus.py` (`build_scan_single`, `_scan_pdf(rng, 8)`, Zeilen 1031-1069) im Abbild, nie Nutzerdateien.

---

### `.github/workflows/measure.yml` (W4 + B7, config)

**Analog:** dieselbe Datei.

**Muster Wegwerf-Container mit cpuset und gemountetem Skript** (Schritt D, Zeilen 338-350):
```yaml
      - name: D, the base load step by step
        env:
          TARGET: ${{ steps.image.outputs.target }}
          DIGEST: ${{ steps.image.outputs.digest }}
        run: |
          docker run --rm --network none \
            -e FINDLING_MEASURE_DIGEST="${DIGEST}" \
            -e FINDLING_MEASURE_IMAGE="${TARGET}" \
            -e FINDLING_MEASURE_ROLE="${{ matrix.role }}" \
            -v "${GITHUB_WORKSPACE}/docs/measurements/2026-09-grundlast-fein/skripte:/skripte:ro" \
            --entrypoint /app/.venv/bin/python "${TARGET}" \
            /skripte/01-grundlast-fein.py \
            | tee "${OUT}/01-grundlast-fein-${{ matrix.arch }}.txt"
```
W3 wird so gemountet (`${GITHUB_WORKSPACE}/scripts/ops:/ops:ro`), weil `scripts/ops` nicht im Abbild liegt; `--cpuset-cpus 0` für N = 1 und `--cpuset-cpus 0-3` für N = 4 (F4-Definition, Open Question 4).

**Muster Schleife über Kombinationen** (Schritt B, Zeilen 254-267) für `embed.bench --threads 1, 2, 4`:
```yaml
          for combination in "2 256" "2 512" "8 256" "8 512"; do
            set -- ${combination}
            echo "::group::batch $1 sequence $2"
            docker run --rm --network none --cpuset-cpus 0,1 \
              --entrypoint python "${TARGET}" \
              -m findling.embed.bench --mode tokens-per-second \
              --batch "$1" --sequence "$2" --threads 2 \
              | tee "${OUT}/tokens-per-second-b$1-s$2.txt"
            echo "::endgroup::"
          done
```
**Pflichten:** Actions nur per SHA (Zeilen 112-117, `test_workflow_pins.py` Regel 5), Eingaben über `env:` und Musterprüfung (Zeilen 126-150), `--network none`, Artefakt-Upload Zeilen 406-412. Neuer Lauf nur auf `ubuntu-24.04-arm`: entweder eigener Job oder `if: matrix.arch == 'arm64'` am neuen Schritt; das Maschinenblatt (Zeilen 174-196) gehört dazu. B7-Sonde aus `docs/measurements/2026-09-komposita-nl/` nach demselben Mount-Muster.

---

### `backend/tests/test_ops_scripts.py` (W1-W3 aufnehmen)

**Analog:** eigene Datei.
- Konstanten wie Zeilen 48-52 ergänzen (`CPU_SAMPLER`, `PROC_ANON_SAMPLER`, `OCR_SLOT_PROBE`).
- Parameterliste der Shell-Regeln erweitern (Zeile 104):
```python
@pytest.fixture(params=[RSS_SAMPLER, HETZNER_BOX, AWS_BOX], ids=lambda path: path.name)
def script(request: pytest.FixtureRequest) -> Path:
```
  Damit greifen Shebang, Dash/CR und `set -eu` (Zeilen 109-124) automatisch.
- Treiber-Layout und Verweigerung nach Zeilen 127-146.
- W3 nach den Python-Regeln Zeilen 702-788 (Shebang, Dash, `machine_shapes`, Importe).
- Selbsttest jedes Textgates mit gestagter Probe (Muster Zeile 763-771).

---

### `.../92d-wechsel.sh` (Box-Werkzeug, request-response)

**Analog:** `docs/measurements/2026-09-nachfolgefassungen/skripte/92c-wechsel.sh` (658 Zeilen). Kopie mit genau zwei Änderungen: **kein `--rm-data`**, und Schritt 1b `occ upgrade` mit gelesenem Rückgabewert.

**Kopf einer Nachfolgefassung** (Zeilen 1-31): "Dies ist die NACHFOLGEFASSUNG von <voller Pfad>", Satz "DIESE FASSUNG IST NICHT GEFAHREN" bis zum Lauf, "Die eine Aenderung gegen 92c", "Was ausdruecklich gleich bleibt" (Zeilen 33-48: Rückgabewerte 2, 36, 37, 38, 39 ohne Umhängen, Fristen, Vorgaben).

**Pflichtangabe vor jeder Rohdatei** (Zeilen 206-227):
```sh
case "${ABBILD_DIGEST:-}" in
'')
    echo "92c-wechsel: ABBILD_DIGEST ist nicht gesetzt oder leer" >&2
    benutzung
    exit 2
    ;;
sha256:*) ;;
*)
    echo "92c-wechsel: ABBILD_DIGEST traegt nicht die Gestalt sha256:<hex>" >&2
```

**Vorgaben und OUT** (Zeilen 233-240): `OUT` MUSS vom Ablaufskript auf das neue Laufverzeichnis gesetzt werden (Pattern 2 der Research), `WERKZEUGE` zeigt weiter auf `2026-09-v12-messung/skripte` (40b-Baumhash).
```sh
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
WERKZEUGE="${WERKZEUGE:-$SKRIPTE/../../2026-09-v12-messung/skripte}"
```

**Der zu ändernde Block** (Zeilen 474-480), in 92d ohne Schalter; Zählung der Instanzen bleibt:
```sh
        occ app_api:app:unregister "$APP_ID" --rm-data 2>&1 ||
            occ app_api:app:unregister "$APP_ID" --rm-data --force 2>&1 || true
```

**occ-Rückgabewert außerhalb der tee-Kette** (Zeilen 527-539), für `occ upgrade` genau so nachbauen:
```sh
        registerlog=$(mktemp "$WORK/92c-register.XXXXXX")
        register_status=0
        occ app_api:app:register "$APP_ID" "$DAEMON" \
            --info-xml /tmp/92c-info-box.xml --wait-finish >"$registerlog" 2>&1 ||
            register_status=$?
        cat "$registerlog"
        printf 'registrierung-rueckgabewert %s\n' "$register_status"
        if [ "$register_status" -eq 0 ]; then
            echo "registrierung-gelungen ja"
        else
            echo "registrierung-gelungen nein"
            : >"$WORK/registrierung-fehlt"
        fi
```

**Grenze aus der cgroup zurücklesen** (Zeilen 542-556), **Entladeschalter-Zeile** (558-572), **Baumhash im laufenden Container** (585-612).

**Abbrüche unterhalb der Pipeline** (Zeilen 623-658):
```sh
} 2>&1 | tee "$ZIEL"
...
if [ -f "$WORK/registrierung-fehlt" ]; then
    echo "92c-wechsel: der occ-Aufruf der Registrierung ist gescheitert (L-03)" >&2
    exit 36
fi
...
echo "92C-WECHSEL-FERTIG"
```
Neuer Abbruch für gescheiterten `occ upgrade`: neue Zahl ab 40 (Pattern 4), nicht umhängen. Zusätzliches Tor nach Registrierung: 52.111 / 37 / 0 aus `occ findling:index` ablesen.

---

### `.../92e-umgebung.sh` (Containerneubau mit geänderter Env)

**Analog:** `.github/workflows/deploy-harp.yml:4510-4611` ("Store upgrade 6").

**Entrypoint/Cmd gegen das Abbild** (4515-4523), **Env filtern und ersetzen** (4525-4537, nur Namen ausgeben, weil `APP_SECRET` in der Umgebung steht):
```sh
          jq -r '.[0].Config.Env[]' "${spec}" > "${RUNNER_TEMP}/rebuild-env-all.list"
          grep -v '^FINDLING_LANGUAGES=' "${RUNNER_TEMP}/rebuild-env-all.list" > "${envfile}" || true
          ...
          printf 'FINDLING_LANGUAGES=%s\n' "${REBUILD_LANGUAGES}" >> "${envfile}"
          cut -d= -f1 "${envfile}" | sort | tr '\n' ' '
```
**Mounts und Labels** (4539-4558), **create/start** (4588-4611):
```sh
          run_args=(--name "${container}" --network host --env-file "${envfile}")
          ...
          docker rm -f "${container}" > /dev/null
          docker create "${run_args[@]}" "${image}" > /dev/null
          docker start "${container}" > /dev/null
```
**Anpassungen für die Box:** `#!/bin/sh` statt bash-Arrays (POSIX-Regel der Box-Skripte, also Argumente über `set --` sammeln); `--network` aus `.HostConfig.NetworkMode` übernehmen statt `host` verlangen (Annahme A4); `/certs/frp`-Block (4560-4586) entfällt, die Box läuft ohne HaRP-Tunnel. Danach 92c-Schritt 11 (`docker update --memory=2g --memory-swap=2g`, cgroup zurücklesen, Zeilen 542-556) und Entladeschalter-Zeile (558-572). Variable Schalter: `FINDLING_LANGUAGES` und `FINDLING_EMBED_IDLE_RELEASE_SECONDS` (für 94c), nie `FINDLING_OCR_LANGUAGES` (Anti-Pattern).

---

### `.../90e-einzelliste.py` (Leser, read-only SQLite)

**Analog:** `docs/measurements/2026-09-nachmessung-m7g/skripte/68-bestand-endungen.py` (97 Zeilen).

**Imports, read-only, Schema-Gegenprobe** (Zeilen 24-55):
```python
from __future__ import annotations

import argparse
import json
import posixpath
import sqlite3
import sys
...
    connection = sqlite3.connect(f"file:{arguments.database}?mode=ro", uri=True)
    columns = [row[1] for row in connection.execute("pragma table_info(files)")]
    for needed in ("path", "state", "reason"):
        if needed not in columns:
            print(f"the column {needed} is not in files, the schema moved", file=sys.stderr)
            return 2
```
Für 90e `file_id` in die Pflichtliste aufnehmen (Annahme A5) und die Abfrage aus der Research übernehmen:
```python
"select file_id, path, state, reason from files"
" where state in ('skipped', 'failed') and deleted_at is null order by state, file_id"
```
**Ausgabe** als JSON wie Zeilen 73-92 (`spalten_von_files` mitgeben); Pfad nur als Endung über `extension_of` (Zeilen 34-38) plus Größe, kein voller Pfad. Wirtspfad der DB: `/mnt/findling/docker/volumes/nc_app_findling_backend_data/_data/state.db` (`71-ocrphase.sh:86`). Außerdem Markenlesung (`meta`) im selben read-only-Muster für das Phase-0-Tor.

---

### `.../91m-langsame-aufrufe.py` (M-01-Leser, JSON-Zeilen)

**Analog A:** `2026-09-v12-messung/skripte/96c-lesen.py` (Zeilen 32-100): "unklar" statt 0 für Unbekanntes, `json.loads` je Zeile mit `except ValueError`, Typprüfung `isinstance(value, bool) or not isinstance(value, int | float)` (Zeilen 42-52).
**Analog B:** `68-bestand-endungen.py` für `argparse` und JSON-Ausgabe.

**Quelle der Zeile** (`php/lib/Service/ExAppService.php:763-768`):
```php
		if ($innerMs >= self::SLOW_CALL_LOG_MILLISECONDS) {
			$this->logger->info('Findling: slow backend call', [
				'path' => $path,
				'innerMs' => $innerMs,
				'ceilingMs' => round($timeout * 1000, 1),
			]);
```
Filter: Meldung `Findling: slow backend call`, Zeitfenster je Stufe (Argumente `--von`/`--bis` UTC), Ausgabe Anzahl, Werte, Maximum gegen `ceilingMs`. Pitfall 5: die Zeile ist `info`, `loglevel` vorher lesen, auf 1 setzen, danach zurück; Gegenprobe (Kaltstartsuche muss eine Zeile erzeugen). Keine Nutzerdaten: nur `path` (Route), `innerMs`, `ceilingMs`, Zeitstempel.

---

### `.../94c-bodensatz-zyklen.sh` (Nachfolgefassung von 94b)

**Analog:** `2026-09-v12-messung/skripte/94b-grundlast-rueckkehr.sh` (723 Zeilen, prüfsummengeschützt in `DRIVEN_V12_FASSUNGEN`, nicht anfassen).

**Helfer zum Übernehmen** (Zeilen 286-326): `anon_von`, `mb_von`, `differenz_mb` ("unbestimmt" statt 0), `protokoll` (schreibt zusätzlich in `$WORK/protokollblock`).
```sh
differenz_mb() {
    case "${1:-}${2:-}" in
    '' | *[!0-9]*)
        printf 'unbestimmt\n'
        return 0
        ;;
    esac
    awk -v links="$1" -v rechts="$2" 'BEGIN { printf "%.1f\n", (links - rechts) / 1048576 }'
}
```
**Marke A nach Neustart** (Zeilen 472-500), **Zyklus: WebDAV-Upload + files:scan + Warten auf eingebettet und Vorrat 0** (Zeilen 503-549):
```sh
        BASISORDNER="$ADRESSE/remote.php/dav/files/$BENUTZER"
        curl -sS -o /dev/null -K "$CURLRC" -X MKCOL "$BASISORDNER/$ORDNER" || true
        ...
            code=$(curl -sS -o /dev/null -w '%{http_code}' -K "$CURLRC" \
                -T "$pfad" "$BASISORDNER/$ZIELORDNER/$name" || echo 000)
        ...
        occ files:scan --path="/$BENUTZER/files/$ZIELORDNER" 2>&1 | tail -4 || true
```
**Änderung gegen 94b:** zwei Zyklen hintereinander (Marken C1, C2) **ohne Containerneubau dazwischen**; Messgröße C2 minus A und C2 minus C1. Abbruchwerte 29, 31, 32, 33 behalten (`BASELOAD_RETURN_ABORTS`, Test Zeile 145), neue ab 40. Schalter 120 s über 92e setzen, danach zurück auf 0.

---

### `.../95c-kaltstart.sh` (Nachfolgefassung von 95b/95-spitze)

**Analog:** `2026-09-v12-messung/skripte/95b-wiederaufwaermen.sh` (658 Zeilen, prüfsummengeschützt).

**Suche gegen die Nutzerroute, Werte in Arbeitsdateien** (Zeilen 300-324):
```sh
suche() {
    antwort=$(curl -sS -G -K "$CURLRC" \
        -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
        --data-urlencode "term=$1" --data-urlencode "limit=$LIMIT" \
        -o "$WORK/$2.json" -w '%{time_total} %{http_code}' \
        "$ADRESSE/ocs/v2.php/search/providers/findling/search" 2>/dev/null || printf '0 000')
    printf '%s\n' "$antwort" | awk '{printf "%d\n", ($1 * 1000) + 0.5}' >"$WORK/$2.ms"
    printf '%s\n' "$antwort" | awk '{print $2}' >"$WORK/$2.code"
    treffer_in "$WORK/$2.json" >"$WORK/$2.treffer"
}
```
**Kalt herstellen auf dem Wirt** (Zeilen 557-563):
```sh
            sync
            echo 3 | sudo tee /proc/sys/vm/drop_caches
            free -h
```
**Begriff mit Vorgabe** (Zeile 161): `BEGRIFF="${BEGRIFF:-Bescheid Antrag}"` (lieferte in 95b 26 Treffer). **Neu:** Treffer > 0 in der ersten Suche ist Pflicht, sonst ganzer Kaltzyklus erneut, höchstens 3; nach dem dritten Fehlschlag Abbruchwert ab 40 unterhalb der Pipeline (Muster Zeilen 628-658). Keine Vorprobe über die Diagnose-Route (Abbruch 30, Runbook 7.2).

---

### `.../98d-dismax-probe.py` (Probe im Produktcontainer)

**Analog A:** `2026-09-v12-messung/skripte/73-bestand-sonde.py` (171 Zeilen): läuft per `docker cp` + `docker exec /app/.venv/bin/python`, importiert die echten Produktfunktionen, druckt nur Zahlen und Kennungen.
```python
from findling.api.resources import query_model, read_side
from findling.config import settings
from findling.index.search import SemanticSide, ranked_sides
from findling.query.rewrite import build_query
...
    side = read_side()
    if side is None:
        return KEINE_SEITE
    rewritten = build_query(side.index, text, title_only=False)
    ...
    bestand = side.index.searcher().search(rewritten.query, 1, count=True).count
```
Regel des Kopfes (Zeilen 22-26): kein zweiter Weg zu den Ranglisten, also Plan über `field_plan_for`, Index über `open_index` (registriert die Ketten). Ausgaberegel `zeile()` (Zeilen 128-135): ausgerichtet, mit grep herausziehbar. Abbruch `return 2` bei fehlendem Index (Zeilen 148-150).

**Analog B:** `backend/tests/test_field_plan_ranking.py:240-288` für die Planvarianten und die Ranglisten:
```python
def _order(index: Index, text: str, plan: FieldPlan) -> list[int]:
    rewritten = build_query(index, text, plan=plan)
    ...
    for _, address in searcher.search(rewritten.query, len(DOCUMENTS)).hits:
        value = searcher.doc(address).get_first(FIELD_FILE_ID)
```
Altplan = `LEGACY_PLAN` (`rewrite.py:139-157`). Per-Wort-dismax aus Research "Code Examples" (Zeilen 394-407). Kennzahlen: Überlappung@10, RBO@10, Treffermengengleichheit (muss exakt gelten), Median-Laufzeit. Begriffe: `TERMS` aus `search_load.py:156`, Sprachfälle aus `98c-sprachfaelle.sh`. Hinweis Zeilen 109-113 der Sonde: unter `docs/measurements/**/skripte/` läuft weder ruff noch pyright.

---

### `.../00-lauf.sh` (Ablauf, detached, harter Stopp)

**Analog:** `2026-09-v12-messung/skripte/96-volllauf.sh` (205 Zeilen), nur Teilvorbild.

**Vorgaben aus dem eigenen Ort** (Zeilen 52-79), **Passwort aus Datei in die Umgebung** (Zeilen 86-87, nie auf eine Kommandozeile):
```sh
FINDLING_ADMIN_PASSWORD=$(sudo cat "$PWFILE")
export FINDLING_ADMIN_PASSWORD
```
**Detached starten, voll umgeleitet** (Zeilen 113-119, 199-203):
```sh
    setsid nohup sudo sh "$SAMPLER" "$CONTAINER" "$SAMPLER_INTERVALL" "$CSV" \
        >"$OUT/96-sampler.log" 2>&1 </dev/null &
...
setsid nohup sh "$MELDEKETTE" warten >"$OUT/96e-ntfy-watch.log" 2>&1 </dev/null &
sh "$MELDEKETTE" start || true
```
**Blockstempel:** `date -u +'<block>-start %Y-%m-%dT%H:%M:%SZ'` beim Betreten und Verlassen (Muster 92c Zeilen 330, 462, 622). **Meldekette:** `96e-ntfy-watch.sh senden <titel> <text> [prio]` (Kopf Zeilen 23-25). **Abbrüche unterhalb der tee-Pipeline** (Zeilen 182-194). **Neu, ohne Vorbild:** `sudo shutdown -h +<Restminuten>` beim Start, Restzeit nach dem B4-Neustart neu setzen; vorher `describe-instance-attribute --attribute instanceInitiatedShutdownBehavior` lesend prüfen (Annahme A2). Nach jedem 92e-Neubau `rss_sampler.sh` und W1 neu starten, Rohdatei je Containerleben (Pitfall 4).

---

### `.../00-ablauf.md` und `README.md` des Laufverzeichnisses

**Analog:** `2026-09-v12-messung/skripte/00-ablauf.md` mit den Abschnitten "1. Was dieser Lauf misst", "2. Die Schrittfolge", "3. Die Erwartung, vorher aufgeschrieben", "4. Woran der Lauf abgebrochen wird" (Katalog 15-39 vergeben, neue ab 40), "5. Nach dem Lauf" (Prüfsummenregel). Überschriften ohne Umlaute. Erwartungen E1..En VOR der ersten Boxminute committen, Urteile nur `gehalten`, `verfehlt`, `nicht entschieden`. Hier stehen die dismax-Entscheidungsregel (Open Question 3), F4-Definition (Open Question 4), Umbau-Planwert 3 h, Indexfaktor rund 2,5. README-Vorbild: `2026-09-v12-messung/README.md` mit Freigabezeile "Anfahrt freigegeben: <Datum>, Deckel ...".

---

### `backend/tests/test_measurement_scripts.py` (Wächter)

**Analog:** eigene Datei (3013 Zeilen). Konkrete Stellen:
- **Neues Laufverzeichnis in den engen Geltungsbereich** (Zeile 92):
```python
NARROW_SCOPE_DIRS = (RUN_DIR, FIX_RUN_DIR, V12_RUN_DIR, SUCCESSOR_RUN_DIR)
```
  plus Konstante `V13_RUN_DIR` neben Zeile 69; der Test `test_the_narrow_scope_covers_the_four_run_directories...` (Zeile 1887) wächst auf fünf.
- **Nachfolgefassung zeigt auf Vorgänger** (Zeilen 2944-2952):
```python
    text = SUCCESSOR_IMAGE_SWITCH.read_text(encoding="utf-8")
    assert "docs/measurements/2026-09-v12-messung/skripte/92b-wechsel.sh" in text
    assert "L-03" in text
    assert SUCCESSOR_IMAGE_SWITCH.parent != V12_IMAGE_SWITCH.parent
    assert NOT_DRIVEN in text
```
  Für 92d: 92c-Pfad im Kopf, und `switches_that_run(code) == []` (Helfer Zeilen 2590-2602) als Beweis "kein `--rm-data`".
- **Reihenfolge von occ-Aufruf, Prüfung, Filter, Merken, Verweigern** (Zeilen 2964-2980) für `occ upgrade` in 92d.
- **Abbruchwerte je Teil** mit `the_three_parts_of`/`the_two_halves_of` und `aborts_of` (Zeilen 2563-2623, 2185, 2750-2780), jeweils mit gestagter Probe.
- **Verweigerung ohne Box** mit `a_boxless_run` (Zeilen 2094-2124, Anwendung 2626-2647): Rückgabe 2, "Benutzung:" auf stderr, leeres `tmp_path`.
- **Nach der Anfahrt:** 92c und 99d bekommen Prüfsummen-Wächter nach `DRIVEN_V12_FASSUNGEN` (Zeilen 343-350) und Mutationsprobe (2897-2911); der `NOT_DRIVEN`-Satz bleibt byteweise im Kopf stehen. Jede auf der Box gefahrene v1.3-Fassung bekommt ein eigenes Prüfsummen-Dict nach demselben Muster.
- **Ratsche, nur falls `rewrite.py` sich ändert** (Zeilen 1085-1097): neuer datierter Absatz über der Konstante, `PACKAGE_TREE_HASH_TODAY` im selben Commit, `PACKAGE_FILES_TODAY` bleibt 57, wenn keine Datei hinzukommt.

---

### `backend/tests/test_dismax_probe.py` (Unit, Sechs-Feld-Index)

**Analog:** `backend/tests/test_field_plan_ranking.py:189-221` (Fixture), 230-257 (Pläne), 271-288 (Rangliste).
```python
@pytest.fixture(scope="module")
def probe_index(tmp_path_factory: pytest.TempPathFactory) -> Index:
    index = open_index(tmp_path_factory.mktemp("field-plan-ranking"), CONSTITUENTS)
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    for file_id, probe in DOCUMENTS.items():
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        ...
        for field in BODY_FIELD.values():
            document.add_text(field, probe.body)
```
Feld für Feld, nie per Keyword (Docstring Zeilen 197-199: I64 in U64 lässt tantivy panicken). Kernaussage: per-Wort-dismax und Summe liefern dieselbe Treffermenge; ganze-Zeile-dismax verliert Dokument 1 (Research-Probe, Zeilen 279-285).

---

### `backend/src/findling/query/rewrite.py` (nur bei positivem MESS-09, D-04)

**Analog:** eigene Funktion `build_query` (Zeilen 575-717). Einhängepunkt ist der Parseraufruf:
```python
    parsed, errors = index.parse_query_lenient(
        rewritten,
        default_field_names=searched,
        field_boosts=dict(plan.boosts),
        conjunction_by_default=True,
        allow_regexes=False,
    )
    ...
    filter_query = _filter_clause(index, extensions, since, until)
    if filter_query is not None:
        parsed = Query.boolean_query([(Occur.Must, parsed), (Occur.Must, filter_query)])
```
Per-Wort-Zweig je Feld mit denselben vier Parser-Einstellungen (Modulkopf Zeilen 9-25 begründet jede; `allow_regexes=False` ist Sicherheitskontrolle), darüber `Query.disjunction_max_query`, über die Wörter `Occur.Must`, Filter unverändert. Rückfall auf den heutigen Weg bei Operatoren, Phrasen, Klammern und Umlautvarianten: `operators = carried_operators(text)` und `one_term = carries_one_term(text)` stehen schon in Zeilen 634-635. Fehlerliste nur `LOGGER.debug` (Zeilen 699-702). Imports `Occur, Query` sind bereits da (Zeile 39). Die Fail-closed-Regel von `plan` (Docstring Zeilen 611-617) bleibt. Aufrufer ohne Änderung: `api/search.py:248`, `api/snippets.py:187`, `api/diagnose.py:198`.

---

### `docs/performance.md`, `docs/language-analyzers.md`, `docs/runbook-messbox.md`

**Analog performance.md:** Abschnitt "## Die v1.2-Anfahrt vom 20. und 21.09.2026" (Zeile 4158) mit "### Nachtrag vom <Datum>: <Thema>" (Zeilen 4178, 4230, 4273, 4312, 4368, 4408). Neuer Abschnitt "## Die v1.3-Anfahrt vom ..." vor "## Reproduzieren" (Zeile 4456); Berichtigungen (z. B. "tesseract nutzt beide Kerne", Zeile 2886) als datierter Nachtrag, nicht als Ersetzung. Kostenteil unter "## Was der Test gekostet hat" (Zeile 3695). Der Verifier greift nach `v1.3-Anfahrt`.
**Analog language-analyzers.md:** Abschnitte "What a question searches" und "Measured numbers" (19-04-Messung, Kipppunkt 0,81).
**Analog Runbook:** Nachtrag-Abschnitte wie 2.1 "Nachtrag 21.09.".

## Shared Patterns

### Abbrüche unterhalb der tee-Pipeline
**Source:** `92c-wechsel.sh:623-658`, `95b-wiederaufwaermen.sh:626-658`, `96-volllauf.sh:180-194`
**Apply to:** 92d, 92e, 94c, 95c, 00-lauf.sh
Urteile im Block nur als Arbeitsdatei unter `$WORK` (`: >"$WORK/<befund>"`), Abbruch erst unter `} 2>&1 | tee "$ZIEL"` mit `if [ -f "$WORK/<befund>" ]; then ... exit NN; fi`. `sh` kennt kein `pipefail`. Neue Abbruchwerte ab 40, fortlaufend, im `00-ablauf.md` Abschnitt 4 katalogisiert. `WORK=$(mktemp -d); chmod 700 "$WORK"; trap 'rm -rf "$WORK"' EXIT` (92c Zeilen 289-291).

### cgroup-Lesen statt Docker-Client
**Source:** `92c-wechsel.sh:311-323` (`scope_von`, `cgroup_wert`, Kennung jedes Mal neu lesen), `rss_sampler.sh:81-104`
**Apply to:** W1, 92d, 92e, 94c, 95c
```sh
scope_von() {
    cid=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER" 2>/dev/null || true)
    [ -n "${cid:-}" ] || return 1
    printf '/sys/fs/cgroup/system.slice/docker-%s.scope\n' "$cid"
}
cgroup_wert() {
    pfad=$(scope_von) || {
        printf 'unlesbar\n'
        return 0
    }
    sudo cat "$pfad/$1" 2>/dev/null || printf 'unlesbar\n'
}
```
"unlesbar"/"unbestimmt"/"unklar" statt 0, überall.

### occ und Instanzzählung
**Source:** `92c-wechsel.sh:293-306`
**Apply to:** 92d, 94c, 95c, 00-lauf.sh
```sh
occ() {
    sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
}
```
Zählung `nextclouds_zaehlen` unmittelbar vor jedem `--rm-data` (Test `switches_without_their_count`, Abstand höchstens 10 Zeilen, `THE_COUNT_IS_IMMEDIATE`).

### Neubau verliert Grenze und Schalter
**Source:** `92c-wechsel.sh:542-572`
**Apply to:** 92d, 92e, jeder Neubau im Ablauf
`docker update --memory=2g --memory-swap=2g`, dann `memory.max` = 2147483648 und `memory.swap.max` = 0 aus der cgroup, dann `entladeschalter-ist`-Zeile.

### Probe im Container
**Source:** `92c-wechsel.sh:601-604`, `73-bestand-sonde.py`
**Apply to:** 98d, W3 auf der Box (B3/B5 im Wegwerf-Container)
```sh
sudo docker cp "$WERKZEUGE/40b-baumhash.py" "$CONTAINER:/tmp/40b-baumhash.py"
sudo docker exec "$CONTAINER" /app/.venv/bin/python /tmp/40b-baumhash.py ...
```
Wegwerf-Container immer `--network none`, `--cpuset-cpus` explizit (`measure.yml:250-253` begründet es).

### Nachfolgefassung statt Bearbeitung
**Source:** Kopf `92c-wechsel.sh:1-65`, Wächter `test_measurement_scripts.py:2930-2980`, `DRIVEN_FASSUNG_RULE` (Zeile 317-319)
**Apply to:** 92d, 94c, 95c; nach der Anfahrt 92c, 99d und alle gefahrenen v1.3-Fassungen

### Geheimnis- und Artefaktregel
**Source:** `backend/tests/test_public_artifacts.py`, `test_measurement_scripts.py` (`passwords_on_a_command_line`, `machine_shapes_in_code`, Zeilen 1693-1812)
**Apply to:** jede Datei unter `docs/` und `scripts/ops/`, besonders Rohdaten (Brückenadressen, `0.0.0.0` aus Container-Logs)

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|---|---|---|---|
| Deckel-Timer in `00-lauf.sh` (`shutdown -h +N`, Neusetzen nach B4) | Orchestrierung | event-driven | Kein Werkzeug hat bisher die Box selbst angehalten; Research Pattern 6 und Annahme A2 sind die Grundlage, lesende Vorprüfung per AWS CLI Pflicht |

Teilweise ohne Vorbild: die Datenquelle von W2 (`/proc/<pid>/status` per `docker exec`) und der Slot-Parallelbetrieb in W3 (N Threads je eigenem `ExtractionWorker`); die Form beider hat aber exakte Vorbilder.

## Metadata

**Analog search scope:** `scripts/ops/`, `docs/measurements/2026-09-v12-messung/skripte/`, `docs/measurements/2026-09-nachfolgefassungen/skripte/`, `docs/measurements/2026-09-nachmessung-m7g/skripte/`, `.github/workflows/measure.yml`, `.github/workflows/deploy-harp.yml`, `backend/src/findling/query/rewrite.py`, `backend/src/findling/extract/sandbox.py`, `php/lib/Service/ExAppService.php`, `backend/tests/test_ops_scripts.py`, `backend/tests/test_measurement_scripts.py`, `backend/tests/test_field_plan_ranking.py`, `docs/performance.md`
**Files scanned:** 17
**Pattern extraction date:** 2026-09-25
