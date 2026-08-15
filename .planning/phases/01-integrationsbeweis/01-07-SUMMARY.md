---
phase: 01-integrationsbeweis
plan: 07
subsystem: packaging
tags: [docker, multi-arch, harp, frpc, supervisord, ghcr, appstore, info-xml, ci]

# Dependency graph
requires:
  - phase: 01-04
    provides: "Lauffaehige ExApp mit AppAPI-Handshake, die das Image verpackt"
  - phase: 01-02
    provides: "uv-Projekt backend/ mit uv.lock und exakten Pins"
provides:
  - "Multi-Stage-Image auf python:3.13-slim-trixie, digest-gepinnt, mit uv-gebautem venv"
  - "HaRP-Prozessbaum: supervisord startet app und frpc, frpc 0.61.1 mit SHA256-Pruefung je Architektur"
  - "backend/appinfo/info.xml mit docker-install, einer USER-Route und environment-variables"
  - "CI-Gate auf dem echten Store-Validierungsweg (xsltproc pre-info.xslt | xmllint --schema info.xsd) fuer beide info.xml"
  - "Nativer Multi-Arch-Build amd64 plus arm64 mit Rauchprobe je Architektur und Manifest-Merge nach ghcr"
affects: [01-08, phase-02-indexierung, phase-05-release]

# Tech tracking
tech-stack:
  added:
    - "supervisor (Debian trixie) als Prozessbaum im Image"
    - "frp 0.61.1 (nur frpc) aus einem gepinnten Commit in nextcloud/HaRP"
    - "docker/build-push-action 7.3.0, docker/setup-buildx-action 4.2.0, docker/login-action 4.6.0"
  patterns:
    - "Basisimages per Index-Digest pinnen, nicht per Tag, damit derselbe Ausdruck auf amd64 und arm64 aufloest"
    - "Der einzige Bestandteil ohne Paketmanager (frpc) traegt eine SHA256-Erwartung je Architektur im Skript"
    - "Rauchprobe vor dem Push: ein kaputtes Image wird ein roter Build, kein Registry-Vorfall"
    - "Push by digest je Runner, Manifest erst im Merge-Job ueber imagetools, damit Provenance erhalten bleibt"
    - "Store-Metadaten werden auf dem Transformationsweg validiert, nie direkt gegen das Schema"

key-files:
  created:
    - backend/Dockerfile
    - backend/.dockerignore
    - backend/docker/install_frpc.sh
    - backend/docker/harp_connect.sh
    - backend/docker/entrypoint.sh
    - backend/docker/supervisord.conf
    - backend/appinfo/info.xml
    - .github/workflows/docker.yml
    - .gitattributes
  modified:
    - .github/workflows/php.yml

key-decisions:
  - "APP_HOST wird im Image auf 0.0.0.0 gesetzt: der Default der Bibliothek ist 127.0.0.1, damit antwortet ein veroeffentlichter Port im Container nichts. Unter HaRP ist der Wert wirkungslos, weil dort ein Unix-Socket bedient wird"
  - "install_frpc.sh laeuft in der Runtime-Stage wie im Plan, curl und ca-certificates bleiben danach im Image (Diagnosewert, Paketmanager-Herkunft)"
  - "uv sync laeuft mit --no-editable, damit die Runtime-Stage nur das venv braucht und der Quellbaum nicht ins Image muss"
  - "frpc-Pruefsummen wurden gegen zwei unabhaengige Quellen bestaetigt: die in nextcloud/HaRP eingelagerten Tarballs sind byteidentisch zum Upstream-Release fatedier/frp v0.61.1"
  - "Die frpc-Konfiguration wird mit umask 077 geschrieben und auf 0600 gesetzt, weil sie den HP_SHARED_KEY enthaelt"
  - ".gitattributes erzwingt LF fuer sh, conf, Dockerfile und .dockerignore: die Entwicklungsmaschine checkt mit autocrlf aus, ein CRLF-Shebang haette das Image beim naechsten Checkout unstartbar gemacht"
  - "Der Versionstag bleibt aus: das Manifest traegt dev und den Commit-SHA, der Versionstag gehoert in Phase 5"

patterns-established:
  - "Jede neue Action wird mit Commit-SHA und Versionskommentar eingetragen, Tags gelten als beweglich"
  - "Workflows werden vor dem Commit mit actionlint plus shellcheck gegengelesen, nicht erst in der CI"
  - "Lokale Vorabpruefung fehlender Werkzeuge laeuft in einem Wegwerf-Container statt ueber eine Installation auf dem Rechner"

requirements-completed: [PKG-01]

# Metrics
duration: 41 min
completed: 2026-08-15
---

# Phase 1 Plan 07: Multi-Arch-Image, HaRP-Prozessbaum und Store-Metadaten Summary

**Ein digest-gepinntes Multi-Stage-Image, das unter supervisord die Anwendung und frpc fuehrt, dazu ein nativer amd64- und arm64-Build mit Rauchprobe vor jedem Push und ein CI-Gate, das beide info.xml auf genau dem Weg prueft, den der App Store geht.**

## Was gebaut wurde

| Task | Ergebnis | Commit |
|------|----------|--------|
| 1 | Dockerfile, .dockerignore und vier Skripte fuer den HaRP-Prozessbaum | `639dc8d` |
| 2 | backend/appinfo/info.xml plus app-metadata-Job in php.yml | `f0ca2b7` |
| 3 | .github/workflows/docker.yml mit Matrix, Rauchprobe und Manifest-Merge | `524fb12` |

### Der Prozessbaum

`supervisord` fuehrt zwei Programme. `app` startet die Anwendung aus dem gebauten venv, `frpc` laeuft ueber `harp_connect.sh`. Ohne `HP_SHARED_KEY` schreibt `harp_connect.sh` eine Zeile und beendet sich mit 0; `exitcodes=0` in der supervisord-Konfiguration sorgt dafuer, dass das als erwartet gilt und keine Neustartschleife ausloest. Damit laeuft derselbe Container unveraendert im manual-install-Modus und unter HaRP.

Beide Programme loggen nach stdout und stderr, also zeigt `docker logs` den gesamten Baum. Die erste Zeile des Entrypoints nennt den Bindungsmodus. Das ist die Zeile, die die teuerste Frage einer ExApp-Installation beantwortet: laeuft der Prozess nicht, oder lauscht er dort, wo niemand hinschaut.

### frpc als einziger Bestandteil ohne Paketmanager

`install_frpc.sh` wertet `uname -m` aus, laedt die passende Datei von einem gepinnten Commit in `nextcloud/HaRP` und vergleicht die SHA256-Summe gegen einen im Skript hinterlegten Erwartungswert. Bei Abweichung bricht der Build ab. Nur `frpc` wird ausgepackt, `frps` ist die Serverhaelfte und hat in einem Anwendungsimage nichts zu suchen.

| Architektur | SHA256 des Tarballs |
|-------------|---------------------|
| amd64 | `bff260b68ca7b1461182a46c4f34e9709ba32764eed30a15dd94ac97f50a2c40` |
| arm64 | `af6366f2b43920ebfe6235dba6060770399ed1fb18601e5818552bd46a7621f8` |

Gegenprobe mit einem anderen Muster als der Umsetzung: beide Summen wurden zusaetzlich gegen das Upstream-Release `fatedier/frp v0.61.1` gerechnet und sind dort identisch. Die in HaRP eingelagerten Dateien sind also nicht umgepackt, sondern die Originalveroeffentlichung.

### Store-Metadaten und das echte Gate

`backend/appinfo/info.xml` traegt den `external-app`-Block mit `docker-install` auf `ghcr.io/street1983nk/findling_backend:0.1.0`, genau eine Route (`search`, POST, `USER`) und `FINDLING_LOG_LEVEL` als Umgebungsvariable. Der Schutz vor Anmeldeversuchen ist auf `[401]` begrenzt; `[500]` haette einen Backend-Fehler in eine Sperre der Instanz-Adresse verwandelt.

Der neue Job `app-metadata` in `php.yml` stellt den Store-Weg nach: `xsltproc pre-info.xslt "$f" | xmllint --noout --schema info.xsd -`, beide Dateien von einem festen Commit-SHA in `nextcloud/appstore`. Der Job druckt zusaetzlich das normalisierte Dokument und behauptet aktiv, dass der `routes`-Block dabei verschwindet. Das ist kein Fehler, sondern die Begruendung fuer eine Regel in Phase 5: weil die Store-Datenbank die Routen nie sieht, liest AppAPI sie aus dem Release-Archiv, und der Tarball muss die info.xml unveraendert enthalten.

### Multi-Arch ohne Emulation

`docker.yml` baut `linux/amd64` auf `ubuntu-24.04` und `linux/arm64` auf einem nativen arm-Runner. Es gibt keine Emulationsaktion im Workflow. Je Architektur laufen zwei Builds: erst lokal mit `load` und anschliessender Rauchprobe gegen `/heartbeat`, danach der Push per Digest. Der Merge-Job holt beide Digests als Artefakt, baut das Manifest mit `imagetools create` und prueft danach, dass `linux/amd64` und `linux/arm64` beide gefuehrt werden.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] Zeilenenden haetten das Image beim naechsten Checkout unstartbar gemacht**

- **Found during:** Task 1, beim Staging
- **Issue:** Die Entwicklungsmaschine hat `core.autocrlf` aktiv. Git meldete beim `git add` fuer alle Skripte "LF will be replaced by CRLF the next time Git touches it". Ein CRLF-Shebang laesst den Kernel nach einem Interpreter suchen, dessen Name auf ein Wagenrueckalufzeichen endet. Der lokale Build war gruen, der naechste Checkout haette ein Image erzeugt, das nicht startet.
- **Fix:** `.gitattributes` im Repo-Wurzelverzeichnis mit `text eol=lf` fuer `*.sh`, `*.conf`, `Dockerfile` und `.dockerignore`, danach `git add --renormalize`.
- **Files modified:** `.gitattributes`
- **Verification:** `file backend/docker/*.sh` meldet weiterhin "POSIX shell script, ASCII text executable" ohne CRLF-Vermerk; der Build nach dem Commit ist gruen.
- **Commit:** `639dc8d`

**2. [Rule 2 - Missing critical] APP_HOST musste im Image gesetzt werden**

- **Found during:** Task 1
- **Issue:** `run_app` faellt ohne `APP_HOST` auf `127.0.0.1` zurueck. In einem Container heisst das "von niemandem erreichbar": der Akzeptanztest des Plans veroeffentlicht Port 10035 und fragt den Heartbeat von aussen ab, das haette nie geantwortet.
- **Fix:** `ENV APP_HOST=0.0.0.0` im Dockerfile mit Begruendung im Kommentar. Unter HaRP ist der Wert wirkungslos, weil dort ein Unix-Socket bedient wird.
- **Files modified:** `backend/Dockerfile`
- **Verification:** `curl -sf http://127.0.0.1:10035/heartbeat` liefert `{"status":"ok"}` gegen den lokal gestarteten Container.
- **Commit:** `639dc8d`

**3. [Rule 2 - Missing critical] Der HP_SHARED_KEY lag in einer weltlesbaren Datei**

- **Found during:** Task 1
- **Issue:** Das Referenzmuster schreibt `/frpc.toml` ohne Rechtebeschraenkung. Die Datei enthaelt den geteilten Schluessel des Tunnels (Bedrohung T-01-27).
- **Fix:** `umask 077` vor dem Schreiben plus `chmod 600` danach. Der Schluessel erscheint in keiner Log-Zeile.
- **Files modified:** `backend/docker/harp_connect.sh`
- **Verification:** `grep -n 'umask\|chmod 600' backend/docker/harp_connect.sh`
- **Commit:** `639dc8d`

**4. [Rule 1 - Bug] Das Wort im Kommentar liess ein Akzeptanzkriterium durchfallen**

- **Found during:** Task 1
- **Issue:** Ein erklaerender Kommentar enthielt die Portfreigabe-Anweisung als Wort, damit lieferte `grep -c 'EXPOSE' backend/Dockerfile` eine 1 statt der geforderten 0.
- **Fix:** Kommentar umformuliert, ohne die Aussage zu verlieren.
- **Files modified:** `backend/Dockerfile`
- **Verification:** `grep -c 'EXPOSE' backend/Dockerfile` liefert 0, danach erneuter gruener Build.
- **Commit:** `639dc8d`

**5. [Rule 1 - Bug] shellcheck-Befund im Merge-Job**

- **Found during:** Task 3
- **Issue:** actionlint meldete SC2046 auf der `imagetools create`-Zeile.
- **Fix:** Die Wortaufteilung ist dort beabsichtigt (jede Digest-Datei wird eine weitere Quellreferenz), also ein gezieltes `# shellcheck disable=SC2046` mit Begruendung statt einer Umbau-Kruecke.
- **Files modified:** `.github/workflows/docker.yml`
- **Verification:** `actionlint` laeuft ohne Ausgabe durch.
- **Commit:** `524fb12`

### Nicht auto-fixbar: die CI-Kriterien sind erst nach dem Push pruefbar

Drei Akzeptanzkriterien und die gesamte Plan-Verifikation setzen einen abgeschlossenen CI-Lauf voraus. Dieser Executor darf nicht pushen, also sind sie hier vorbereitet und lokal so weit vorweggenommen, wie es ohne GitHub geht.

| Kriterium | Lokaler Ersatzbeweis | Pruefbefehl nach dem Push |
|-----------|----------------------|---------------------------|
| `php.yml` gruen | Beide info.xml wurden mit den gepinnten Store-Dateien in einem Wegwerf-Container validiert, beide melden "validates" | `gh run list --workflow=php.yml --limit 1 --json conclusion -q '.[0].conclusion'` |
| `docker.yml` gruen | amd64-Build und Rauchprobe lokal bestanden, actionlint sauber | `gh run list --workflow=docker.yml --limit 1 --json conclusion -q '.[0].conclusion'` |
| Manifest fuehrt beide Plattformen | arm64 lokal nicht baubar ohne Emulation, die der Plan ausdruecklich verbietet | `docker buildx imagetools inspect ghcr.io/street1983nk/findling_backend:dev` |

Die arm64-Haelfte des Beweises kann nur der native Runner erbringen. Genau deshalb steht sie im Workflow und nicht im lokalen Ablauf.

**Total deviations:** 5 auto-fixed (1x Rule 3 Blocker, 2x Rule 2 fehlende kritische Funktion, 2x Rule 1 Bug). **Impact:** Keine Abweichung vom Plan-Ziel. Zwei der fuenf (Zeilenenden, APP_HOST) waren stumme Startfehler, die erst auf einer fremden Maschine bzw. im Container aufgefallen waeren.

## Authentication Gates

Keine. Der Push nach ghcr laeuft ueber das ohnehin vorhandene Workflow-Token mit `packages: write`, ein zusaetzliches Geheimnis war nicht noetig.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Bedrohungsmodells des Plans. Die drei zutreffenden Eintraege sind umgesetzt: T-01-26 durch die SHA256-Pruefung je Architektur, T-01-SC2 durch Digest-Pins auf Basisimage und uv-Image plus SHA-Pins auf allen Actions, T-01-27 durch `umask 077` und `chmod 600` auf der frpc-Konfiguration, T-01-28 durch `[401]` ohne `[500]`, T-01-29 durch `imagetools` statt Handbau des Manifests.

## Zu erledigen, sobald das Paket zum ersten Mal in ghcr liegt

Ein frisch angelegtes ghcr-Paket ist privat. Der Store kann ein privates Image nicht ziehen, also muss die Sichtbarkeit einmal von Hand auf oeffentlich gestellt werden:
`https://github.com/users/street1983nk/packages/container/findling_backend/settings`
Der Merge-Job schreibt diesen Hinweis am Ende in sein Protokoll, damit er nicht in einer Dokumentation verschwindet.

## Issues Encountered

Keine offenen. Der lokale Rechner hat kein `xsltproc` und kein `xmllint`; beides wurde in einem Wegwerf-Container ausgefuehrt, statt den Rechner zu veraendern.

## Next Phase Readiness

Bereit fuer 01-08. Das Image ist verteilbar, die Store-Metadaten liegen vor und beide CI-Gates warten nur auf den Push durch den Orchestrator.

## Self-Check: PASSED

- Alle zehn erzeugten bzw. geaenderten Dateien liegen auf der Platte (`ls -1` ueber die vollstaendige Liste, keine fehlt)
- Drei Task-Commits vorhanden: `639dc8d`, `f0ca2b7`, `524fb12`
- Alle lokal pruefbaren Akzeptanzkriterien bestanden, die drei CI-abhaengigen sind oben mit Pruefbefehl dokumentiert
- `must_haves`-Marker gegengeprueft: `python:3.13-slim-trixie` im Dockerfile, `aarch64` in install_frpc.sh, `ghcr.io` in info.xml, `ubuntu-24.04-arm` in docker.yml, `harp_connect` in supervisord.conf
