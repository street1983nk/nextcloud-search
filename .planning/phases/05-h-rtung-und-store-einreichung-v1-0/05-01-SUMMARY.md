---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 01
subsystem: infra
tags: [harp, appapi, docker, github-actions, compose, deploy, exapp, mutual-tls]

# Dependency graph
requires:
  - phase: 01-walking-skeleton
    provides: die Kanarien-Antwort des Containers und die OCS-Suchroute, an der der Lauf-Beweis haengt
  - phase: 02-suche-und-index
    provides: die Composite Action setup-test-nc und den Jobrumpf der Integrationsjobs
provides:
  - CI-Job deploy-harp: Installation ueber einen Deploy-Daemon mit HaRP, mit Digest-gepinntem HaRP-Image und lokaler Registry
  - lokaler compose-Stack scripts/dev/compose-harp.yaml fuer denselben Weg auf der Entwicklungsmaschine
  - Composite Action kann eine Nextcloud ohne ExApp-Registrierung aufbauen (register-exapp) und kennt pgsql
  - belegte Befehlsform der HaRP-Daemon-Registrierung (nextcloud_url ist die HaRP-Adresse)
  - Image bringt /certs/frp fuer die HaRP-Zertifikate mit, damit der Tunnel mit mutual TLS zustande kommt
affects: [05-08 Versionsmatrix und Uninstall-Beweis, 05-09 Paritaetsjob, 05-10 ARM- und AIO-Lauf, PKG-03]

# Tech tracking
tech-stack:
  added:
    - ghcr.io/nextcloud/nextcloud-appapi-harp (Digest-gepinnt, amd64 und arm64)
    - registry:2 als lokale Registry im Job und im lokalen Ablauf
  patterns:
    - Fremdimages per Index-Digest pinnen, Tag und Datum der Aufloesung im Kommentar
    - Deploy-Beweis mit drei getrennten Feststellungen, leere Ausgabe ist rot
    - temporaere info.xml nur fuer die Registrierung, Quelldatei bleibt unangetastet und wird geprueft

key-files:
  created:
    - .github/workflows/deploy-harp.yml
    - scripts/dev/compose-harp.yaml
    - .planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md
  modified:
    - .github/actions/setup-test-nc/action.yml
    - docs/dev-setup.md
    - backend/Dockerfile

key-decisions:
  - "Die HaRP-Daemon-Registrierung traegt die HaRP-Adresse als nextcloud_url, nicht die Adresse von Nextcloud: AppAPI bildet im HaRP-Betrieb {nextcloud_url}/exapps/{appId}"
  - "Das Laufzeitimage bringt /certs/frp mit, im Besitz des unprivilegierten App-Nutzers; der OS-Trust-Store bleibt root und die update-ca-certificates-Meldung bleibt stehen"
  - "exapp-version der Composite Action kommt aus backend/appinfo/info.xml statt aus einem Vorgabewert, der neben der Datei alt wird"
  - "compose-harp.yaml nutzt FINDLING_HARP_PORT (Vorgabe 8096) statt FINDLING_PORT, damit Alltagsstack und Store-Weg gleichzeitig laufen koennen"
  - "Der CI-Lauf von deploy-harp.yml ist noch nicht belegt; der lokale compose-Lauf ist der ausgefuehrte Beweis (DI-05-01)"

patterns-established:
  - "Digest-Pinnung eines Fremdimages an genau einer Stelle je Ort (env HARP_IMAGE, compose-Dienst), beide Zeichenketten identisch"
  - "Eingaben einer Composite Action gehen ueber env: in die Shell und werden gegen eine feste Werteliste geprueft (Sec-L7)"
  - "Ein Beweisschritt behandelt eine leere Ausgabe als Fehlschlag, nach dem Muster resilience.yml:502-511"

requirements-completed: [PKG-03]

# Metrics
duration: 75min
completed: 2026-09-03
---

# Phase 5 Plan 01: HaRP-Deploy-Durchstich Summary

**Findling installiert sich erstmals auf dem Weg einer Store-Installation: ein Deploy-Daemon zieht das Image aus einer Registry, erzeugt Container und Datenvolume, und die Kanarien-Suche ueber die normale OCS-Route liefert genau einen Treffer aus diesem Container. Zwei Defekte, die diesen Weg vorher unmoeglich machten, sind gefunden und behoben.**

## Performance

- **Duration:** ca. 75 min
- **Started:** 2026-09-03T08:52:00Z
- **Completed:** 2026-09-03T10:07:00Z
- **Tasks:** 3 von 3
- **Files modified:** 6 (3 neu, 3 geaendert)

## Accomplishments

- Der Deploy-Weg ist zum ersten Mal in diesem Repo gelaufen, und zwar vollstaendig: Daemon-Registrierung mit `--harp`, Image-Pull aus einer lokalen Registry, Container `nc_app_findling_backend`, Volume `nc_app_findling_backend_data`, `ExApp findling_backend deployed successfully`, und ein Kanarien-Treffer ueber `/ocs/v2.php/search/providers/findling/search` mit der Unterzeile `produced inside container findling_backend at 2026-09-03T10:05:20+00:00 for user testuser`.
- Zwei Defekte gefunden, die genau der Durchstich sichtbar machen sollte, und beide behoben (siehe Deviations): die fehlende Schreibmoeglichkeit fuer die HaRP-Zertifikate im Image und die falsche `nextcloud_url` der Daemon-Registrierung.
- Nebenbelegt fuer Plan 05-08: `occ app_api:app:unregister findling_backend --rm-data` entfernt Container UND Volume rueckstandsfrei (nach dem Aufruf antworten `docker ps -a` und `docker volume ls` mit den Filtern leer).
- Die Composite Action kann jetzt eine Nextcloud ohne ExApp-Registrierung liefern, kennt `pgsql` (Vorbereitung des AIO-Lauf-Dialekts) und meldet die App-Version aus der `info.xml` als Ausgabe.

## Task Commits

1. **Task 1: Composite Action ohne erzwungene manual-install-Registrierung** - `489fdf5` (feat)
2. **Task 2: deploy-harp installiert das Backend ueber den Deploy-Daemon** - `c8da34f` (feat)
3. **Task 3: derselbe Weg lokal, compose-Stack plus Doku** - `a11f34f` (feat)
4. **Korrektur beider gefundener Defekte** - `58585ba` (fix)

## Files Created/Modified

- `.github/workflows/deploy-harp.yml` (neu) - Job `deploy-harp`: lokale Registry, HaRP per Index-Digest, temporaere info.xml unter `RUNNER_TEMP`, Daemon- und ExApp-Registrierung, drei getrennte Beweis-Feststellungen, Kanarien-Suche, Log-Artefakt, Kommentarstelle fuer den Uninstall-Beweis aus 05-08.
- `scripts/dev/compose-harp.yaml` (neu) - zweiter lokaler Stack: Nextcloud plus HaRP plus Docker-Socket, HaRP-Image mit demselben Digest wie der Job, `HP_SHARED_KEY` ohne Vorgabewert, eigener Port.
- `.github/actions/setup-test-nc/action.yml` - neue Eingaben `register-exapp` und `nextcloud-host` (beide gegen eine Werteliste geprueft), `pgsql`/`pdo_pgsql` und ein `pgsql`-Installationszweig, `exapp-version` aus der `info.xml` plus Ausgabe, alle Eingabewerte ueber `env:` in die Shell.
- `docs/dev-setup.md` - deutscher Abschnitt "Der Store-Installationsweg lokal (HaRP)": Zweck, Befehlsfolge, Beweis, Abbau, Grenze, der Satz zum Docker-Socket und die beiden gemessenen Fallen.
- `backend/Dockerfile` - `/certs/frp` im Besitz des App-Nutzers, mit der Messung und der bewusst nicht gemachten Aenderung am Trust-Store im Kommentar.
- `.planning/phases/.../deferred-items.md` (neu) - DI-05-01 bis DI-05-03.

## Decisions Made

- **`nextcloud_url` ist die HaRP-Adresse.** `DockerActions::resolveExAppUrl` bildet im HaRP-Betrieb `{nextcloud_url}/exapps/{appId}`; HaRP ist der Eingang und leitet alles ausser `/exapps` an `NC_INSTANCE_URL` weiter. Derselbe Wert erreicht den Container als `NEXTCLOUD_URL`, der Rueckweg laeuft also ebenfalls durch HaRP. Damit ist `--net host` im CI-Job nicht mehr die tragende Zutat, bleibt aber drin, weil der Container die veroeffentlichte HaRP-Adresse auf `localhost` sehen muss.
- **Trust-Store bleibt root.** HaRP scheitert im Container an `update-ca-certificates`; das bleibt so, weil frpc die CA ueber `trustedCaFile` liest und ein von der Anwendung beschreibbarer Trust-Store das groessere Problem waere (DI-05-02).
- **Eigene Portvariable im zweiten Stack.** Der Plan nannte "derselbe FINDLING_PORT-Mechanismus mit anderem Vorgabewert"; umgesetzt als `FINDLING_HARP_PORT` mit Vorgabe 8096, weil die Doku des Alltagsstacks `FINDLING_PORT=8090` exportiert und eine gemeinsame Variable beide Staende auf denselben Port legen wuerde. 8096 statt 8095, weil 8095 auf dieser Maschine belegt war.
- **Containername mit Projektpraefix.** `findling-harp-proxy` statt `appapi-harp` im lokalen Stack, weil eine Entwicklungsmaschine mehrere AppAPI-Aufbauten haelt; im compose-Netz wird der Dienstname `harp` adressiert.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Das Laufzeitimage kann die HaRP-Zertifikate nicht aufnehmen**
- **Found during:** Task 3, beim ersten echten Lauf des Deploy-Weges
- **Issue:** HaRP legt die Tunnel-Zertifikate per `docker exec` in den ExApp-Container, und dieser exec laeuft als Image-Nutzer, also als unprivilegierter `findling` (uid 1000). Ohne vorhandenes, beschreibbares `/certs` scheitert das mit `mkdir: cannot create directory '/certs': Permission denied`. `harp_connect.sh` findet danach kein lesbares Zertifikat, faellt auf TLS ohne Client-Zertifikat zurueck, und der frp-Server weist jeden Login mit `EOF` ab. Der Container laeuft, die App antwortet auf ihrem Socket, und sie ist unerreichbar. Damit war der Store-Installationsweg fuer Findling grundsaetzlich nicht begehbar, unabhaengig von diesem Plan.
- **Fix:** `backend/Dockerfile` legt `/certs/frp` an, im Besitz von `findling:findling` und mit Modus 0700. Der OS-Trust-Store bleibt bewusst unberuehrt (DI-05-02).
- **Files modified:** `backend/Dockerfile`
- **Verification:** Erst mit einem abgeleiteten Probe-Image belegt, dann mit dem geaenderten Repository-Dockerfile wiederholt: `docker run --entrypoint sh` zeigt `drwx------ findling findling /certs /certs/frp`, und der Lauf loggt `harp_connect: client certificates in /certs/frp, configuring the tunnel with mutual TLS` gefolgt von `login to server success` und `start proxy success`.
- **Committed in:** `58585ba`

**2. [Rule 1 - Bug] Die recherchierte Daemon-Registrierung adressiert die ExApp am falschen Ort**
- **Found during:** Task 3, `heartbeat check failed` bei laufendem, gesundem Container
- **Issue:** Pattern 1 der Recherche und der `<interfaces>`-Block des Plans registrieren den Daemon mit der Adresse von Nextcloud als `nextcloud_url`. Im HaRP-Betrieb bildet AppAPI die ExApp-Adresse aber als `{nextcloud_url}/exapps/{appId}` [VERIFIED: `DockerActions::resolveExAppUrl`, in der laufenden app_api-Installation gelesen], sodass jeder Heartbeat beim Webserver landet: `GET http://app/exapps/findling_backend/heartbeat` antwortet mit 404, und die Installation endet in `heartbeat check failed`. Der CI-Job haette genauso versagt.
- **Fix:** `deploy-harp.yml` registriert `http://localhost:8780` als `nextcloud_url`, die Doku `http://harp:8780`, jeweils mit der Begruendung daneben.
- **Files modified:** `.github/workflows/deploy-harp.yml`, `docs/dev-setup.md`
- **Verification:** Nach der Korrektur meldet dieselbe Befehlsfolge `ExApp findling_backend deployed successfully`, `app_api:app:list` zeigt `[enabled]`, und die Suche liefert genau einen Kanarien-Treffer.
- **Committed in:** `58585ba` (Workflow), `a11f34f` (Doku)

**3. [Rule 2 - Missing Critical] Doku sagt, wie der Schluessel zurueckkommt**
- **Found during:** Task 3, jeder zweite compose-Befehl brach ab
- **Issue:** `HP_SHARED_KEY` hat in der compose-Datei absichtlich keinen Vorgabewert, weshalb auch ein `exec` oder `logs` ohne gesetzte Variable schon beim Auswerten der Datei abbricht. Eine Anleitung, die das nicht sagt, produziert genau diesen Abbruch beim ersten Nachschauen.
- **Fix:** Abschnitt in `docs/dev-setup.md` mit dem `docker inspect`-Einzeiler, der den Schluessel aus dem laufenden Stack zurueckholt, plus dem Hinweis, dass jede Shell ihn braucht.
- **Files modified:** `docs/dev-setup.md`
- **Verification:** Der Einzeiler wurde in diesem Lauf mehrfach genau so benutzt.
- **Committed in:** `a11f34f`

---

**Total deviations:** 3 auto-fixed (2 Bugs, 1 fehlende kritische Angabe)
**Impact on plan:** Ohne die ersten beiden waere das Ergebnis dieses Plans ein Workflow gewesen, der beim ersten Lauf rot wird, und ein Produkt, das sich aus dem Store nicht installieren laesst. Beide Aenderungen sind klein und belegt; `backend/Dockerfile` liegt ausserhalb der `files_modified`-Liste des Plans, aber kein anderer Plan dieser Phase fasst die Datei an, also entsteht kein Konflikt in der Welle.

## Issues Encountered

- **`docker manifest inspect` liefert Plattform-Digests, nicht den Index-Digest.** Der Index-Digest kommt aus `docker buildx imagetools inspect --format '{{.Manifest.Digest}}'`; nur er gilt auf amd64 UND arm64, was diese Phase auf der ARM-Box braucht.
- **Beweis fuer die Beweglichkeit des `release`-Tags, ungeplant geliefert:** das auf dieser Maschine bereits vorhandene HaRP-Image traegt `sha256:3b33565...`, die Registry loest denselben Tag heute auf `sha256:603fdf5...` auf. Ein Deploy-Beweis auf dem Tag waere nicht wiederholbar.
- **Der Kanarien-Lauf brauchte drei Anlaeufe**, jeweils mit `--rm-data` dazwischen: Probe-Image ohne Fix (Tunnel abgewiesen), Probe-Image mit vorab angelegtem `/certs` (Tunnel steht, Heartbeat 404), Repository-Image mit Fix und korrigierter Daemon-Adresse (vollstaendiger Beweis).
- **Der lokale Stack wurde vollstaendig abgebaut** (`--rm-data`, `compose down -v`, Registry und Probe-Images entfernt, `.dev/harp` geloescht). Die vorhandene Umgebung des Owners (Alltagsstack, MCP-Connector-Stack) wurde nicht angefasst; die lokale Registry lief deshalb auf Port 5010 statt 5000.

## Offene Verifikation

- **Der CI-Lauf von `deploy-harp.yml` ist noch nicht belegt** (DI-05-01). `gh workflow run` war aus dem Worktree nicht moeglich: der Zweig ist nur lokal, und `workflow_dispatch` bietet nur Workflows des Vorgabezweigs an. Ersatzbelege: `actionlint` ist gruen, das YAML laedt, der Digest ist gegen die Registry aufgeloest, und die gesamte Befehlsfolge lief lokal durch. Der Workflow hat Push-Trigger auf `backend/**`, `php/appinfo/**` und seinen eigenen Pfad, der erste Lauf passiert also nach dem Merge von selbst und muss angesehen werden. Nur zwei Dinge haben lokal kein Gegenstueck: die Registry auf Port 5000 des Runners und die `--net host`-Variante der Daemon-Registrierung.
- Die bestehenden Aufrufer in `integration.yml` und `resilience.yml` uebergeben `register-exapp` nicht und laufen unveraendert; sie erben allerdings die neue `exapp-version` (0.3.0 aus der info.xml statt 0.1.0), was gewollt ist und ab 05-07 gebraucht wird.

## Known Stubs

Keine. Der Job und der Stack sind vollstaendig; die Matrix bleibt bewusst bei einer Serverversion, mit Kommentar auf Plan 05-08.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: privilege | `backend/Dockerfile` | Neues Verzeichnis `/certs/frp` im Container ist fuer den App-Nutzer beschreibbar und nimmt den privaten Schluessel des Tunnels auf (Modus 0700). Bewertung: T-05-02 der Plan-Registers akzeptiert HaRPs Bauart; hier weitet sich nichts nach aussen, aber ein Angreifer mit Codeausfuehrung im Container kann den Tunnel-Schluessel lesen, was vorher am fehlenden Verzeichnis scheiterte und den Tunnel gleich mit. |
| threat_flag: network | `.github/workflows/deploy-harp.yml`, `scripts/dev/compose-harp.yaml` | HaRP wird zum Eingang: `{nextcloud_url}/exapps/*` laeuft ueber HaRP, und der Container erreicht Nextcloud durch HaRP. Das ist AppAPIs Bauart und war im Threat-Register des Plans nicht als Datenweg benannt. |

## User Setup Required

Keine externe Konfiguration. Wer den lokalen Stack fahren will, braucht Docker und ein selbst erzeugtes `HP_SHARED_KEY`; beides steht in `docs/dev-setup.md`.

## Next Phase Readiness

- **Plan 05-08 kann aufsetzen:** der Job existiert, die Beweis-Schritte nennen Container und Volume namentlich und schreiben den Volumenamen in die Jobzusammenfassung, und die Einhaengestelle fuer den Uninstall-Beweis ist als Kommentar markiert. Dass `--rm-data` Container und Volume raeumt, ist bereits lokal gemessen.
- **Plan 05-09 und der AIO-Lauf** muessen die korrigierte Daemon-Adresse verwenden (DI-05-03). Auf der Miet-Box waere derselbe Fehler ein verlorener Tag.
- **Blocker:** keiner. Offen bleibt nur die Sichtung des ersten CI-Laufs nach dem Merge.

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-03*

## Self-Check: PASSED

Alle sechs genannten Dateien liegen im Arbeitsbaum, alle fuenf Commits sind in
der Zweighistorie, und `.planning/STATE.md` sowie `.planning/ROADMAP.md` sind in
dieser Zweigspanne unveraendert (der Orchestrator schreibt sie).
