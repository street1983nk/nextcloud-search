---
phase: 22-messanfahrt-bl-f03
plan: 02
subsystem: messwerkzeuge
tags: [ops, box, docker, sqlite, messung, v13]
requires: []
provides:
  - "92d-wechsel.sh: Abbildwechsel ohne --rm-data, occ upgrade mit Rückgabewert (40), Bestandstor 52111/37/0 (41)"
  - "92e-umgebung.sh: Containerneubau aus docker inspect mit genau einem Schalter (42 Grenze, 43 Gestalt/Neubau)"
  - "90e-einzelliste.py: read-only Einzelliste skipped/failed und Markentor (0/44/45)"
  - "91m-langsame-aufrufe.py: M-01-Leser je Zeitfenster, unklar statt 0"
  - "V13_RUN_DIR im engen Geltungsbereich der Messskript-Regeln"
affects:
  - "22-06 (Generalprobe der vier Werkzeuge gegen die lokale Test-Nextcloud)"
  - "Ablaufskript der Anfahrt (00-lauf.sh): ruft 92d als ersten Wechsel, 92e für MESS-08 und 94c, 90e als Phase-0-Tor, 91m je Stufe"
tech-stack:
  added: []
  patterns:
    - "Tor, das eine Marke für das Bestehen verlangt (fail-closed), statt eine für das Scheitern"
    - "Endmarke am Blockende gegen stille Subshell-Abbrüche unter set -eu"
    - "Lauf eines Box-Werkzeugs gegen ein nachgestelltes sudo/docker auf PATH, mit gepflanztem Geheimnis"
key-files:
  created:
    - docs/measurements/2026-09-v13-messung/skripte/92d-wechsel.sh
    - docs/measurements/2026-09-v13-messung/skripte/92e-umgebung.sh
    - docs/measurements/2026-09-v13-messung/skripte/90e-einzelliste.py
    - docs/measurements/2026-09-v13-messung/skripte/91m-langsame-aufrufe.py
    - backend/tests/test_v13_wechsel.py
    - .planning/phases/22-messanfahrt-bl-f03/deferred-items.md
  modified:
    - backend/tests/test_measurement_scripts.py
decisions:
  - "92d: PHP-Hälfte und occ upgrade stehen VOR dem unregister (im Modus 'requires upgrade' fehlt app_api:app); die Instanzzählung steht unmittelbar über dem unregister"
  - "92d-Bestandstor: indexiert aus der state.db des laufenden Containers (read-only), übersprungen/fehlgeschlagen aus occ findling:index, weil die PHP-Hälfte indexed nie schreibt"
  - "90e-Markentor folgt den zwei gelockerten Vergleichen des Stores (index_version als Untergrenze, tantivy_version nach index_format); 44 gewinnt gegen 45"
  - "92e trägt die HaRP-Tunnelzertifikate unter /certs/frp mit, wenn der Container sie hat; Netz aus NetworkMode, nie --network host"
metrics:
  duration: "ca. 30 min"
  completed: 2026-09-25
  tasks: 2
  files: 7
---

# Phase 22 Plan 02: Box-Werkzeuge 92d, 92e, 90e, 91m Summary

Vier Box-Werkzeuge im neuen Laufverzeichnis docs/measurements/2026-09-v13-messung/skripte/: 92d wechselt das Abbild, ohne das Snapshot-Volumen zu leeren, und prüft danach das Bestandstor 52.111 / 37 / 0; 92e baut den Produktcontainer mit genau einer geänderten Umgebungsvariable neu; 90e liefert read-only die Einzelliste und das Markentor; 91m zählt die M-01-Zeilen. Alle unter Wächtern in test_v13_wechsel.py, das Verzeichnis im engen Geltungsbereich.

## Aufgaben

| Task | Name | Commit | Dateien |
| ---- | ---- | ------ | ------- |
| 1 | 92d-wechsel.sh und 92e-umgebung.sh mit Wächtern | 9686b1e | 92d-wechsel.sh, 92e-umgebung.sh, test_measurement_scripts.py, test_v13_wechsel.py |
| 2 | 90e-einzelliste.py und 91m-langsame-aufrufe.py | 0701cca | 90e-einzelliste.py, 91m-langsame-aufrufe.py, test_v13_wechsel.py |

## Was entstanden ist

- **92d-wechsel.sh:** Kopie von 92c mit Kopf "NACHFOLGEFASSUNG von docs/measurements/2026-09-nachfolgefassungen/skripte/92c-wechsel.sh", NOT_DRIVEN-Satz, Abschnitten "Die zwei Aenderungen gegen 92c" und "Was ausdruecklich gleich bleibt". Keine Code-Zeile trägt `--rm-data` (auch keine echo-Zeile). Phase B: PHP-Hälfte, Schritt 7b `occ upgrade` in eigene Datei unter WORK mit Zeile `occ-upgrade-rueckgabewert`, dann Zählung + unregister ohne Schalter (`unregister-rueckgabewert`, `volumen-nach-unregister`), Registrierung, Grenze, Entladeschalter, Baumhash im Container, neuer Schritt 17 Bestandstor. Unter der Pipeline: 40, 37, 36, 39, 36, 41. 92c und das v1.2-Verzeichnis sind unverändert.
- **92e-umgebung.sh:** Argument NAME=WERT, nur FINDLING_LANGUAGES ([a-z,]) und FINDLING_EMBED_IDLE_RELEASE_SECONDS ([0-9]); FINDLING_OCR_LANGUAGES in genau einer Verweigerungszeile. Felder über `docker inspect --format` (kein jq), Entrypoint/Cmd gegen das Abbild (sonst 43 vor jedem `docker rm`), env-Datei 600 unter WORK, Mounts (volume/bind), Labels, Restart-Policy, NetworkMode, Argumente über `set --`, `docker rm -f`, `docker create`, `docker start`, `docker update --memory=2g --memory-swap=2g`, cgroup-Rücklesen (sonst 42), `schalter-ist`, `entladeschalter-ist`, `neubau-fertig`. Ausgegeben werden nur Namen der Umgebung.
- **90e-einzelliste.py:** `liste` (JSON: Zählung je state, Einzelliste mit file_id, endung, groesse, state, reason, kein Pfad), `marken` (jede Marke als `marke <name> <wert>`, Urteil 0/44/45, 2 bei fehlender meta-Tabelle oder kaputter Erwartung). Annahme A5 aufgelöst: `files.file_id` existiert (Primärschlüssel, Nextcloud-fileid).
- **91m-langsame-aufrufe.py:** `--log --von --bis --stufe`, Kontext unter `data`, `context` oder oben, Zeitfenster inklusive, Ausgabe `stufe`, `aufruf`, `maximum`, `kaputte-zeilen`; unlesbares Log ergibt `stufe <n> langsame-aufrufe unklar`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Bestandstor liest indexiert nicht aus occ findling:index**
- **Found during:** Task 1
- **Issue:** Der Plan sagt "occ findling:index lesen" für alle drei Zahlen. Die PHP-Hälfte schreibt indexed nie (IndexCommand.php: "indexed is counted by the backend container and never written here, so it stays 0"); das Tor wäre auf der Box immer mit 41 gescheitert.
- **Fix:** indexiert per read-only SQLite-Abfrage (`?mode=ro`) auf `$APP_PERSISTENT_STORAGE/state.db` im laufenden Container; übersprungen und fehlgeschlagen weiter aus `occ findling:index`.
- **Commit:** 9686b1e

**2. [Rule 2 - Korrektheit] Bestandstor fail-closed, Endmarke in 92e**
- **Found during:** Task 1
- **Issue:** Ein unerwarteter Abbruch im tee-Block unter `set -eu` verlässt nur die Subshell; ein Tor mit Scheitern-Marke hätte dann mit 0 geendet (Klasse L-03).
- **Fix:** 92d verlangt die Marke `bestand-bestanden`, sonst 41. 92e setzt am Blockende `block-durchgelaufen`, sonst 43; `docker create`/`start`/`update` sind einzeln abgefangen.
- **Commit:** 9686b1e

**3. [Rule 2 - Korrektheit] 92e trägt die HaRP-Tunnelzertifikate mit**
- **Found during:** Task 1
- **Issue:** Die Muster-Notiz sagt, der /certs/frp-Block entfalle, weil die Box ohne HaRP-Tunnel laufe. Der Daemon der Box ist harp_aio; trägt der Container Zertifikate, verlöre ein Neubau aus dem Abbild sie (Befund CI-Lauf 35997241359).
- **Fix:** Sind die drei Dateien lesbar, werden sie per `docker cp` vor dem Start in den neuen Container getragen; sonst Zeile `tunnel-zertifikate keine`.
- **Commit:** 9686b1e

**4. [Rule 1 - Bug] Markentor folgt den gelockerten Vergleichen des Stores**
- **Found during:** Task 2
- **Issue:** Reine Gleichheit hätte einen gesunden Stand (index_version über der Erwartung, tantivy-Patchrelease mit gleichem index_format) als 44 gemeldet; Store.version_mismatch behandelt beide nicht als Abweichung.
- **Fix:** index_version als Untergrenze, tantivy_version nach dem index_format-Teil, beide getestet.
- **Commit:** 0701cca

### Weitere Anpassungen

- Die zweite Zählung heißt in 92d `nextcloud-instanzen-vor-unregister` statt `-vor-rm-data`; im Kopf begründet.
- 92d: Neubau-Reihenfolge PHP-Hälfte, occ upgrade, unregister, register (Runbook Nachtrag Block 13b); im Kopf als Teil von Änderung 2 beschrieben.
- Die Vorgaben des Bestandstors (BESTAND_INDEXIERT/UEBERSPRUNGEN/FEHLGESCHLAGEN) sind Stellschrauben, damit die Generalprobe in 22-06 lokal fahren kann; auf der Box gelten 52111/37/0.

### TDD Gate Compliance

Beide Tasks tragen tdd="true"; Werkzeug und Wächter sind je Task in einem Commit gelandet, es gibt keine getrennten test(...)-Commits. Die Wächter liefen vor dem Commit grün, darunter drei Läufe von 92e gegen ein nachgestelltes sudo/docker.

## Verification

- `ruff check .`, `ruff format --check .`, pyright (latest) 0 Fehler, vulture sauber; ruff check/format auch für das v13-Skriptverzeichnis grün
- pytest tests/test_v13_wechsel.py tests/test_measurement_scripts.py tests/test_public_artifacts.py: 499 passed
- `grep -v '^#' 92d-wechsel.sh | grep -c -- "--rm-data"` = 0; `occ-upgrade-rueckgabewert` 3 Treffer; `exit 41` vorhanden; `V13_RUN_DIR` 5 Treffer in test_measurement_scripts.py
- `git diff --quiet HEAD -- docs/measurements/2026-09-nachfolgefassungen docs/measurements/2026-09-v12-messung`: unverändert
- Alle vier Skripte mit Modus 100755 im Index; `sh -n` für beide Shell-Skripte grün
- Keine Änderung unter backend/src/findling oder php/, daher kein Baumhash-Bump. MESS-07 und MESS-08 bleiben offen (erst nach der Anfahrt). Kein Push, keine Box.

## Known Stubs

Keine.

## Threat Flags

Keine neuen Flächen außerhalb des Threat-Modells: T-22-05 bis T-22-09 sind umgesetzt und getestet (kein --rm-data, env-Datei 600 und nur Namen, Einzelliste ohne Pfad, mode=ro ohne schreibendes SQL, 91m nur time/path/innerMs/ceilingMs).

## Self-Check: PASSED

- FOUND: 92d-wechsel.sh, 92e-umgebung.sh, 90e-einzelliste.py, 91m-langsame-aufrufe.py, test_v13_wechsel.py
- FOUND: 9686b1e, 0701cca
