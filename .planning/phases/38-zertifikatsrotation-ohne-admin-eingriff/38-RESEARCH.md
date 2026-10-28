# Phase 38: Zertifikatsrotation ohne Admin-Eingriff - Research

**Researched:** 2026-10-28
**Domain:** HaRP/FRP-Tunnel (frpc 0.61.1 im Backend-Container), AppAPI-Zertifikatsverteilung, CI-Probe in deploy-harp.yml
**Confidence:** HIGH (alle tragenden Aussagen am Quelltext von frp v0.61.1, nextcloud/HaRP main, nextcloud/app_api master und am echten Log aus Issue #33 belegt)

## Summary

Die Kernfrage der Phase hat eine harte Antwort, und sie veraendert den Zuschnitt: **Die frischen Zertifikate kommen nie von selbst in den laufenden Backend-Container.** /certs/frp im Container ist kein Mount, sondern eine Kopie, die HaRP per Docker-API (`PUT /containers/{name}/archive`) genau einmal hineinschreibt, und AppAPI loest das nur in `deployExAppHarp()` aus, also bei `app_api:app:register` und `app_api:app:update` [VERIFIED: app_api lib/DeployActions/DockerActions.php:199, lib/Command/ExApp/Register.php:176, Update.php:213; HaRP haproxy_agent.py `_install_frp_certificates`]. Die offizielle HaRP-README sagt es woertlich: "remove and install each ExApp again, because ExApps embed the certificates at install time" [CITED: github.com/nextcloud/HaRP README.md Zeile 256]. Ein Container, der bei einem x509-Fehler "/certs/frp neu einliest und frpc neu startet", liest dieselben veralteten Dateien und scheitert identisch. ZERT-01 ist in der woertlichen Form fuer den Issue-#33-Fall **nicht erfuellbar** ohne Mitwirkung von AppAPI/HaRP oder Admin.

Zweite harte Antwort: **frpc 0.61.1 liest Zertifikat, Schluessel und CA bei jedem Verbindungsversuch neu von der Platte** (`realConnect()` ruft pro Dial `transport.NewClientTLSConfig(certFile, keyFile, trustedCaFile)`, das `tls.LoadX509KeyPair` und `os.ReadFile` ausfuehrt) und versucht mit `loginFailExit = false` endlos weiter, Backoff bis 20 s [VERIFIED: frp v0.61.1 client/connector.go:147-175, pkg/transport/tls.go:27-130, client/service.go:182-225]. Sobald jemand die drei Dateien im Container ersetzt, heilt der Tunnel innerhalb von ca. 20 s **ohne** frpc-Neustart und ohne Container-Neustart. Ein frpc-Neustart bringt nur dann etwas, wenn sich der **TLS-Modus** aendert (Start ohne lesbare Zertifikate, Konfig ohne Pfade geschrieben, Dateien kommen spaeter). Ein Neustart bei unveraenderten Dateien ist wirkungslos und waere genau der Neustart-Sturm, den ZERT-02 verbietet.

Dritte Antwort, zur Ursache: HaRP erzeugt die CA "harp.nc" nur, wenn /certs/frp im HaRP-Container fehlt (`if [ ! -d "/certs/frp" ]`, Gueltigkeit 5000 Tage, keine automatische Rotation) [VERIFIED: HaRP start.sh:266-345]. Eine "Rotation beim Neustart" passiert also nur, wenn HaRPs /certs nicht persistent ist. Genau das war bei TrueNAS der Fall und ist seit 27.10.2026 upstream behoben (truenas/apps PR #6254 "community/nextcloud: fix harp certs", gemergt, fuegt `harp_container.add_storage("/certs", ...)` hinzu) [VERIFIED: gh pr view 6254 --repo truenas/apps].

**Primary recommendation:** Phase 38 baut einen kleinen, gedeckelten Tunnel-Waechter in harp_connect.sh (bash statt exec): frpc-Ausgabe durchreichen und x509 erkennen, /certs/frp periodisch und bei jedem x509-Fehler auf Aenderung pruefen, frpc **nur bei geaenderten und stabilen Dateien** neu starten (mit Mindestabstand und Stundendeckel), bei unveraenderten Dateien eine klare, ratenbegrenzte Logzeile mit Abhilfe ausgeben. Dazu ein dokumentierter Reparaturweg ohne Unregister/Register (drei Dateien vom HaRP- in den Backend-Container kopieren, Tunnel heilt ohne Neustart), bewiesen in einer neuen deploy-harp-Probe mit echter CA-Neuausstellung. ZERT-01 muss vor dem Plan mit dem Owner umformuliert werden (siehe Open Question 1).

## User Constraints

Kein 38-CONTEXT.md vorhanden (Phasenordner leer, kein discuss-phase gelaufen). Bindend sind daher: ROADMAP-Erfolgskriterien Phase 38, REQUIREMENTS ZERT-01/02, STATE.md-Hinweis "Beweis in CI, weil Docker auf der Entwicklerbox haengt", Auftragsrahmen "kleinster robuster Mechanismus, Release 1.6.0 am 29.10."

## Project Constraints (from CLAUDE.md)

- Code, Kommentare, Logzeilen Englisch; keine Em-Dashes (U+2014/U+2013) nirgends; echte Umlaute nur in deutscher Prosa, nie in Code; .planning-Dokumente mit ASCII-Umschrift
- Qualitaetsgates: ruff-Vollregelsatz, pyright basic, vulture, lokal gruen vor Commit (gilt fuer neue Python-Tests)
- Security/Privacy: keine Inhalte verlassen den Server, keine Telemetrie; Shared Key und Schluesselmaterial nie im Log
- Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Abschluss fixen
- Commits als Owner (street1983nk), keine Claude-Trailer (Memory-Regel); vor "Closes #33" erst kurz im Issue antworten; GitHub-Antworten kurz und menschlich
- init.sh-Philosophie (im Code dokumentiert): kein stilles Neustarten abgestuerzter Prozesse; "gesund aussen, kaputt innen" vermeiden

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ZERT-01 | Backend uebersteht CA-Neuausstellung ohne Unregister/Register; bei x509-Fehler /certs/frp neu einlesen, frpc neu starten, Verbindung kommt selbsttaetig wieder | Selbstheilung ist nur moeglich, wenn die Dateien im Container ersetzt werden (AppAPI tut das nur bei register/update). frpc liest pro Dial neu, heilt also nach Dateitausch von selbst. Umsetzbar: Waechter mit Modus-Wechsel-Neustart plus Reparaturweg ohne Re-Register. Formulierung braucht Owner-Entscheid (OQ1) |
| ZERT-02 | Beleg (Test/CI-Probe mit rotiertem Zertifikat), begrenzt (kein Neustart-Sturm), Doku, Antwort im Issue #33 | CI-Rotation: `docker exec appapi-harp rm -rf /certs/frp` + `docker restart appapi-harp` erzeugt echte neue CA. Positivkontrolle: Tunnel bleibt nachweislich tot bis zum Dateitausch. Deckel: Neustart nur bei Dateiaenderung, Mindestabstand, Stundendeckel; Log ratenbegrenzt |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CA/Zertifikate erzeugen | HaRP-Container (start.sh) | Host-Storage (/certs-Volume) | Nur HaRP haelt ca.key; Persistenz entscheidet, ob ein Neustart rotiert |
| Zertifikate in ExApp-Container verteilen | AppAPI (deployExAppHarp) -> HaRP (install_certificates) | Admin (manueller Kopierweg) | Einziger offizieller Ausloeser ist register/update |
| Tunnel aufbauen und wiederholen | frpc im Backend-Container | - | frpc liest Dateien pro Dial, Backoff intern |
| Modus-Wechsel, Erkennung, Diagnose-Log, Neustart-Deckel | harp_connect.sh (Waechter) | init.sh (Lebensdauer-Kopplung) | Einzige Stelle, die Konfig schreibt und frpc-Ausgabe sieht |
| Beweis | deploy-harp.yml (echte HaRP-Instanz) | pytest mit Stub-frpc (Logik) | Docker lokal unbrauchbar, nur CI |

## Ist-Zustand im Code (Frage 1)

[VERIFIED: Lesen der Dateien]

- `backend/docker/init.sh` (bash, PID 1) startet `harp_connect.sh &` und `entrypoint.sh &`, wartet mit `wait -n -p`. Endet harp_connect mit 0: "no HaRP tunnel in this deployment", App laeuft allein weiter. Endet es mit !=0: Container wird gestoppt ("the HaRP tunnel died with status N"). Bewusst **kein** Neustart einzelner Prozesse (Kommentar Zeilen 10-16).
- `backend/docker/harp_connect.sh` (`#!/bin/sh`, set -eu) ist **One-Shot**: prueft Env (Exit 78 bei Luecken), waehlt TLS-Modus genau einmal beim Start (mTLS wenn client.crt/client.key/ca.crt lesbar, sonst TLS ohne Client-Zertifikat, oder Klartext nur mit FINDLING_HARP_PLAINTEXT=1), schreibt /app/run/frpc.toml (umask 077, chmod 600, enthaelt HP_SHARED_KEY) mit `loginFailExit = false`, dann `exec /usr/local/bin/frpc -c ...`. Danach ist frpc selbst das Kind von init.sh.
- Folge: frpc beendet sich bei x509 **nie** (loginFailExit=false, endlose Wiederholung), init.sh merkt nichts, der Container bleibt "running", Heartbeat von aussen tot. Genau das Bild im Issue #33.
- `install_frpc.sh`: frp **0.61.1**, aus nextcloud/HaRP Commit d9d36438 vendored, SHA-256 je Architektur.
- Dockerfile: Skripte nach /app/docker/, `chmod 0755`; /certs/frp vorab angelegt, Besitzer findling (uid 1000), Modus 0700; `USER findling`.

## Wie sich der x509-Fehler zeigt (Frage 2)

[VERIFIED: echtes Log FlattusBlastus, Issue #33, frpc 0.61.1; Quelltext client/service.go:295-298]

```
[I] [client/service.go:295] [runid] try to connect to server...
[W] [client/service.go:298] [runid] connect to server error: tls: failed to verify certificate: x509: certificate signed by unknown authority (possibly because of "crypto/rsa: verification error" while trying to verify candidate authority certificate "harp.nc")
[W] [client/service.go:298] [runid] connect to server error: session shutdown
```

- Exit-Code: keiner, frpc laeuft weiter.
- Zwei Muster wechseln sich ab: `x509: certificate signed by unknown authority` (frpc prueft das neue Server-Zertifikat gegen die alte ca.crt) und `session shutdown` (frps lehnt das alte Client-Zertifikat ab bzw. bricht ab). `session shutdown` tritt auch in anderen Lagen auf (im selben Issue-Log beim Start ohne Client-Zertifikat) und taugt **allein nicht** als Signal.
- Das Klammer-Suffix "candidate authority certificate \"harp.nc\"" ist das Go-Merkmal "gleicher CA-Name, andere Signatur", also genau die Neuausstellung.
- Erkennungsmuster: Teilstring `x509: ` in Zeilen mit `connect to server error:`. Deckt auch Ablauf ab (`x509: certificate has expired or is not yet valid`) [ASSUMED: Go-Fehlertext fuer Ablauf, nicht im Lauf gesehen].
- Intervall: Wiederholung ca. alle 20 s (Log: 18:13:03, :22, :42, 18:14:02 ...), x509 etwa jede dritte Zeile.
- frpc liest die Dateien bei jedem Versuch neu (siehe Summary), es fehlt also kein "Reload"; es fehlen neue Dateien.

## Wo kommen frische Zertifikate her (Frage 5, entscheidend)

[VERIFIED: Quelltext]

| Schritt | Wer | Wann |
|---------|-----|------|
| CA + server.crt + client.crt erzeugen | HaRP start.sh | nur wenn /certs/frp im HaRP-Container fehlt |
| Dateien in ExApp-Container schreiben | HaRP `docker_exapp_install_certificates` -> `_install_frp_certificates` (tar per `PUT /containers/{name}/archive?path=/`) | nur auf Aufruf von AppAPI |
| Aufruf ausloesen | AppAPI `DockerActions::updateCertsHarp()` | nur in `deployExAppHarp()`, aufgerufen von `occ app_api:app:register` und `occ app_api:app:update` (Update nur bei neuer Version) |

- Kein Mount, keine Aktualisierung bei HaRP-Neustart, kein Heartbeat-Pfad, der Zertifikate nachliefert. Ein Container-Neustart aendert nichts (Dateien liegen in der beschreibbaren Schicht und bleiben die alten).
- HaRP-README, Abschnitt Zertifikatsablauf: "stop HaRP, delete its /certs/frp folder and start it again ... then remove and install each ExApp again, because ExApps embed the certificates at install time" [CITED: github.com/nextcloud/HaRP/blob/main/README.md].
- HaRP-Issue #107 "Concern about renewal of certificates" ist geschlossen, nur mit "I will take a look" beantwortet; keine Rotationsfunktion gebaut [VERIFIED: gh issue view 107 --repo nextcloud/HaRP].
- **Fazit: Fall "Zertifikate kommen nur bei register" gilt.** Echte Selbstheilung ohne Admin braucht AppAPI/HaRP-Mitwirkung (z. B. HaRP verteilt beim Neuerzeugen der CA an alle laufenden nc_app_*-Container neu). Das ist ein Upstream-Vorschlag, nicht in 1.6.0 lieferbar.

### Verworfener Weg: Container holt sich die Zertifikate selbst

Technisch denkbar: Der Container kennt `HP_SHARED_KEY`, und das ist **derselbe Schluessel** wie AppAPIs HaRP-Passwort (`$harpEnvVars['HP_SHARED_KEY'] = decrypt($deployConfig['haproxy_password'])`) [VERIFIED: DockerActions.php:1100-1103]. Damit koennte er `POST /exapps/app_api/docker/exapp/install_certificates` an HaRP schicken (Header `harp-shared-key`, `docker-engine-port`), HaRP wuerde die aktuellen Dateien in den Container legen [VERIFIED: haproxy_agent.py handle_app_api_request:998-1016]. **Nicht empfohlen**, weil:
- der Container HaRPs HTTP-Adresse (8780 oder Nextcloud-Frontproxy /exapps/) und den docker-engine-port des Daemons (24000 nur beim gebuendelten) nicht kennt, also raten muesste;
- er HaRPs Steuer-API benutzen wuerde, die laut HaRP-Kommentar "only meant for HaRP itself" ist; ein Store-Review und die NC-Maintainer wuerden das zu Recht beanstanden; Fehlversuche loesen HaRPs Bruteforce-Sperre fuer die IP aus;
- bei entfernten Docker-Engines deren eigener frpc ebenfalls veraltet ist, der Weg also gerade dort nicht traegt.

## Standard Stack

Keine neuen Pakete. Alles mit Bordmitteln des Images.

| Komponente | Version | Zweck | Status |
|-----------|---------|-------|--------|
| frpc | 0.61.1 (gepinnt) | Tunnel | behalten |
| bash | aus python:3.13-slim-trixie | Waechter (read -t, wait -n, Traps) | im Image vorhanden (init.sh ist bash) [VERIFIED: init.sh Shebang] |
| sha256sum (coreutils) | Image | Fingerabdruck der drei Dateien | vorhanden [VERIFIED: Dockerfile nutzt sha256sum nur in Build-Stages; coreutils ist in slim-Basis enthalten, ASSUMED fuer Runtime-Stage, im Plan per `docker run ... sha256sum --version` pruefen] |
| mkfifo (coreutils) | Image | frpc-Ausgabe an Waechter | wie oben [ASSUMED] |
| shellcheck | Ubuntu-Runner | statische Pruefung | [ASSUMED: auf ubuntu-24.04-Runnern vorinstalliert; Plan prueft mit `shellcheck --version`, sonst `apt-get install shellcheck`] |

### Frage 6: frpc-Pin behalten

- Aktuell ist frp v0.71.1 (14.10.2026); HaRP main nutzt selbst 0.71.1 [VERIFIED: gh release list fatedier/frp; HaRP Dockerfile ARG FRP_VERSION=0.71.1].
- v0.71.1 baut die TLS-Konfig weiterhin pro Dial in `realConnect()` neu, es gibt **keine** zusaetzliche Cert-Reload-Funktion, die uns etwas abnimmt [VERIFIED: v0.71.1 client/connector.go:183-197]. Relevante Aenderung dazwischen: #5205 prueft den Rueckgabewert von `AppendCertsFromPEM` (leere/halbe ca.crt gibt klaren Fehler statt stillem leeren Pool) [VERIFIED: compare v0.61.1...v0.71.1]. Fuer unseren Fall ohne Wirkung (beides fuehrt zu einem Fehlversuch und Wiederholung).
- **Empfehlung: Pin 0.61.1 fuer 1.6.0 behalten.** Ein Bump verlangt neue Prueftsummen, neue Quelle (HaRP vendored 0.61.1 nicht mehr am gepinnten Commit-Pfad, Upstream-Release statt HaRP-Spiegel) und eine eigene Sicherheitsbewertung; das ist ein eigener Backlog-Punkt nach dem Release.

## Architecture Patterns

### System Architecture Diagram

```
 HaRP-Neustart ohne persistentes /certs
        |
        v
 HaRP start.sh: /certs/frp fehlt -> neue CA "harp.nc", neues server.crt, client.crt
        |
        v
 frps (HaRP) verlangt Client-Zertifikat der NEUEN CA ----+
                                                         |
 Backend-Container                                       |
 init.sh (PID 1) --- wait -n --+-- entrypoint.sh (uvicorn, unix socket)
                               |
                               +-- harp_connect.sh (NEU: Waechter, laeuft weiter)
                                     |  schreibt frpc.toml (Modus aus Lesbarkeit)
                                     |  startet frpc, liest dessen Ausgabe ueber FIFO
                                     v
                                   frpc --dial pro Versuch, liest /certs/frp neu--> frps
                                     |                                   (x509 / session shutdown)
                                     v
                         Waechter-Schleife (read -t POLL):
                           Zeile -> durchreichen; enthaelt "x509: " -> Fingerabdruck pruefen
                           Timeout -> Fingerabdruck pruefen
                             |-- unveraendert -> KEIN Neustart; ratenbegrenzte Abhilfe-Logzeile
                             |-- geaendert, 2x stabil, Abstand ok, Deckel ok
                             |      |-- Modus gleich (mTLS->mTLS): nur loggen, frpc heilt selbst
                             |      |-- Modus anders (ohne Zert -> mTLS): Konfig neu, frpc neu starten
                             |-- Deckel erreicht -> eine Zeile, keine weiteren Neustarts
                           frpc endet unerwartet -> Waechter endet mit frpc-Code (!=0) -> init.sh stoppt Container (wie heute)

 Admin-Reparatur (Doku):  docker exec <harp> cat /certs/frp/X | docker exec -i nc_app_findling_backend sh -c 'cat > tmp && mv tmp X'
        -> Dateien geaendert -> naechster frpc-Dial (<= ~20 s) mit neuer CA -> Tunnel heilt, kein Re-Register, kein Neustart
```

### Pattern 1: Waechter in harp_connect.sh statt exec

**What:** Konfig-Schreiben als Funktion; frpc im Hintergrund mit Ausgabe in eine FIFO unter /app/run (0700, Besitzer findling); Hauptschleife `IFS= read -r -t "$poll" line <&3`. Timeout (Rueckgabe >128) = Abfragezeitpunkt, EOF = frpc beendet.
**When to use:** nur im HaRP-Zweig (HP_SHARED_KEY gesetzt, nicht FINDLING_HARP_PLAINTEXT=1).
**Skizze** (bash, Namen frei waehlbar, Planer entscheidet):

```bash
#!/bin/bash
# ... bestehende Pruefungen, Exit 0 / 78 unveraendert ...
fingerprint() {   # never logged, only compared
	cat "${CERT_DIR}/ca.crt" "${CERT_DIR}/client.crt" "${CERT_DIR}/client.key" 2>/dev/null | sha256sum | cut -d' ' -f1
}
start_frpc() {
	write_config            # chooses TLS mode from readability, as today
	running_mode=${TLS_MODE}; running_fp=$(fingerprint)
	"${FRPC_BIN}" -c "${FRPC_CONFIG}" >"${FIFO}" 2>&1 &
	frpc_pid=$!
	exec 3<"${FIFO}"
}
trap 'stopping=1; kill -TERM "${frpc_pid}" 2>/dev/null' TERM INT
start_frpc
while :; do
	if IFS= read -r -t "${POLL_SECONDS}" line <&3; then
		printf '%s\n' "${line}"
		case ${line} in *"connect to server error:"*"x509: "*) on_x509 ;; esac
		maybe_check_files     # also on lines, rate limited by $SECONDS
	elif (( $? > 128 )); then
		maybe_check_files
	else
		break                 # EOF: frpc is gone
	fi
done
wait "${frpc_pid}"; rc=$?
(( stopping )) && exit 0
# frpc ended on its own. Never exit 0 here: init.sh reads 0 as "no HaRP".
(( rc == 0 )) && rc=1
echo "harp_connect: frpc exited with status ${rc}" >&2
exit "${rc}"
```

### Pattern 2: Neustart nur bei Dateiaenderung, gedeckelt

- Neustart-Bedingung (alle): Fingerabdruck != dem des laufenden frpc; derselbe Fingerabdruck in zwei aufeinanderfolgenden Pruefungen (Entprellung gegen halb geschriebene Dateien); alle drei Dateien lesbar; seit dem letzten Neustart >= MIN_GAP (Vorschlag 60 s); Neustarts in der laufenden Stunde < CAP (Vorschlag 6).
- Neustart nur, wenn sich der TLS-Modus aendert. Bei gleichem Modus reicht frpcs eigener Neu-Dial; ein Neustart schadet zwar nicht, verkuerzt aber nur die Heilzeit. Planer-Entscheid: Empfehlung **immer neu starten bei geaenderten stabilen Dateien** (einheitlich, Heilzeit sofort statt bis 20 s, unabhaengig von frpc-Interna), weil der Deckel den Sturm ohnehin ausschliesst.
- x509 bei unveraenderten Dateien: **nie** Neustart. Logzeile mit Abhilfe, ratenbegrenzt: erste sofort, dann nach 5, 15, 60 min, danach stuendlich.
- Deckel erreicht: eine Zeile "restart cap reached, frpc keeps retrying on its own", keine weiteren Neustarts in dieser Stunde.

### Pattern 3: Logzeilen nach Hausregel

Prefix `harp_connect:`; nie Shared Key, nie Dateiinhalte, nie Fingerabdruecke des Schluessels; Pfad /certs/frp darf genannt werden (heutige Zeilen tun das). Vorschlag Wortlaut (Englisch, ein Satz Ursache, ein Satz Abhilfe, Verweis auf Doku-Abschnitt):
- `harp_connect: the tunnel certificate is no longer accepted by HaRP (x509), HaRP was most likely restarted without its /certs volume and issued a new CA; frpc keeps retrying and picks up new files in /certs/frp by itself; see docs/<datei>.md#<anker> to copy them in or re-register the app`
- `harp_connect: the certificate files in /certs/frp changed, restarting frpc with mutual TLS (restart N of at most 6 this hour)`
- `harp_connect: restart cap reached ...`

### Anti-Patterns to Avoid

- **frpc bei jedem x509 neu starten:** liest dieselben Dateien, scheitert identisch, erzeugt den Sturm. frpc wiederholt ohnehin.
- **Container beenden bei x509, damit Docker neu startet:** Restart-Policy `unless-stopped` startet denselben Container mit denselben alten Dateien; Endlosschleife, und AppAPI verteilt dabei nichts neu.
- **Waechter endet mit 0 unter HaRP:** init.sh deutet 0 als "kein HaRP", App laeuft unerreichbar weiter. Jeder Ausgang ausser Stop-Signal muss != 0 sein.
- **Pipeline `frpc | while read`** in sh: PID von frpc nicht sauber greifbar, Exit-Code geht verloren, Signale erreichen frpc nicht. FIFO plus Hintergrund-PID nehmen.
- **Selbstabruf bei HaRP mit dem Shared Key** (siehe oben, verworfen).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Zertifikate neu laden | eigenes Reload/Watch in frpc-Nachbau, inotify | frpcs Neu-Lesen pro Dial | bereits eingebaut, belegt im Quelltext |
| Wiederholungs-Backoff | eigene Schleife um frpc | frpc `loginFailExit=false` (1 s bis 20 s, Jitter) | vorhanden; eigener Backoff verdoppelt nur |
| Zertifikatsverteilung | Container ruft HaRP-Steuer-API | AppAPI register/update oder dokumentierter Admin-Kopierweg; Upstream-Vorschlag | Vertrauensgrenze, Ratespiel um Adresse/Port |
| Prozessaufsicht | supervisor o. ae. | init.sh + Waechter in bash | Hausentscheid gegen supervisor (58 MB) |

## Runtime State Inventory

Kein Rename/Refactor; Abschnitt nur kurz, weil Zustand ausserhalb des Repos die Ursache ist:
- Stored data: keine Aenderung. Nichts.
- Live service config: HaRP-/certs beim Nutzer (nicht persistent = Ursache). Keine Repo-Aktion, nur Doku.
- OS-registered state: keiner. Nichts.
- Secrets/env vars: HP_SHARED_KEY unveraendert, bleibt nur in frpc.toml (600). Nichts zu migrieren.
- Build artifacts: neues Image mit neuem harp_connect.sh; laufende 1.5.x-Container bekommen den Waechter erst mit dem Update auf 1.6.0 (das Update ruft deployExAppHarp und verteilt dabei **ebenfalls frische Zertifikate**, ein betroffener Nutzer ist nach dem Update also ohnehin geheilt).

## Common Pitfalls

### Pitfall 1: Positivkontrolle verwechselt
**What goes wrong:** Kriterium 2 verlangt "ohne die neue Logik bleibt der Tunnel tot". Nach Dateitausch heilt aber auch das **alte** Image (frpc liest pro Dial), sofern es im mTLS-Modus gestartet ist.
**How to avoid:** Positivkontrolle ist "ohne neue Dateien bleibt der Tunnel tot" (Beobachtungsfenster nach der Rotation, Suche schlaegt fehl, x509 im Log, RestartCount unveraendert). Der Mehrwert des Waechters (Modus-Wechsel, Deckel, Diagnose) wird im pytest mit Stub-frpc bewiesen, inklusive Gegenprobe (Stub ohne Waechter-Logik bzw. Neustart-Zaehler).

### Pitfall 2: Halb geschriebene Dateien
**What goes wrong:** Kopierweg schreibt ca.crt vor client.crt; frpc dialt dazwischen mit gemischtem Satz, Waechter startet mit halbem Satz neu.
**How to avoid:** Kopierweg per temp + mv je Datei; Waechter verlangt zweimal gleichen Fingerabdruck.

### Pitfall 3: Dateirechte beim Kopieren
**What goes wrong:** `docker cp` legt Dateien als root an, client.key (bei HaRP evtl. 0600) wird fuer uid 1000 unlesbar; Waechter faellt in "not readable".
**How to avoid:** Kopierweg ueber `docker exec -i nc_app_findling_backend sh -c 'cat > ...'`; docker exec laeuft als Image-User findling, Dateien gehoeren ihm. Nicht `docker cp` empfehlen. [ASSUMED: genaue Modus-Bits von HaRPs openssl-Ausgabe nicht gemessen; HaRPs eigener tar-Weg setzt TarInfo-Default 0644 root, darum funktioniert die Erstinstallation.]

### Pitfall 4: Signale und Exit-Codes gegenueber init.sh
**What goes wrong:** Ohne `exec` empfaengt harp_connect das TERM von init.sh; ohne Trap bleibt frpc haengen, docker stop dauert 10 s; ein Exit 0 nach frpc-Absturz taeuscht "kein HaRP" vor.
**How to avoid:** Trap leitet TERM an frpc weiter; nach Stop-Signal Exit 0 (init.sh ignoriert dann ohnehin), sonst immer != 0. init.sh-Kommentarblock zu "kein Neustart" um den einen bewussten, gedeckelten Neustartfall ergaenzen.

### Pitfall 5: read -t und Zeilenflut
**What goes wrong:** Bei vielen Logzeilen laeuft `read -t` nie in den Timeout, Dateipruefung faellt aus.
**How to avoid:** Pruefung zusaetzlich zeitgesteuert ueber `$SECONDS` bei jeder Zeile.

### Pitfall 6: CI-Rotation trifft auch den Docker-Engine-Tunnel
**What goes wrong:** Nach HaRP-Neustart ist der _ping-Weg erst nach einigen Sekunden da (gemessen 3 bis 4 s, Kommentar "Start HaRP"); occ-Aufrufe davor scheitern.
**How to avoid:** Nach `docker restart appapi-harp` dieselbe _ping-Schleife wie im Schritt "Start HaRP" (45 x 2 s).

### Pitfall 7: Suche geht ueber nginx-Frontproxy und HaRP
**What goes wrong:** Unterscheidet nicht "Tunnel tot" von "HaRP noch nicht bereit".
**How to avoid:** Totzustand erst nach erfolgreichem _ping feststellen; dann muessen x509-Zeilen im Container-Log seit dem Neustart-Zeitstempel stehen und die Kanariensuche keinen Treffer liefern.

## Code Examples

### CI-Probe (neuer deploy-harp-Schritt, Form)

Platz: direkt nach "Search over the ordinary OCS route", **ohne `if:`** (alle vier Beine, inkl. arm64), damit die Rotation auf der frischen Installation laeuft und danach alles wieder gesund ist. Alternative ans Ende vor "The drift probe" ist schlechter, weil spaetere Schritte auf einen gesunden Tunnel bauen und die Drift-Probe ohnehin neu deployt.

```bash
# Source: Muster aus "Start HaRP" (Zeilen 566-614) und RestartCount-Probe (Zeile 5702)
container="${EXAPP_CONTAINER}"
restarts_before=$(docker inspect --format '{{.RestartCount}}' "${container}")
started_before=$(docker inspect --format '{{.State.StartedAt}}' "${container}")
ca_before=$(docker exec appapi-harp sha256sum /certs/frp/ca.crt | cut -d' ' -f1)

# 1. Echte Neuausstellung: HaRP erzeugt neu, weil /certs/frp fehlt (start.sh:266)
rotated=$(date -u +%Y-%m-%dT%H:%M:%SZ)
docker exec appapi-harp rm -rf /certs/frp
docker restart appapi-harp
# ... _ping-Schleife wie in "Start HaRP" ...
ca_after=$(docker exec appapi-harp sha256sum /certs/frp/ca.crt | cut -d' ' -f1)
[ "${ca_before}" != "${ca_after}" ] || { echo "HaRP did not issue a new CA"; exit 1; }

# 2. Positivkontrolle: ohne neue Dateien bleibt der Tunnel tot (Fenster ca. 60 s)
#    - mindestens 2 Zeilen 'x509: ' seit ${rotated} im Container-Log
#    - Kanariensuche liefert keinen Treffer
#    - Waechter-Zeile "no longer accepted by HaRP" genau einmal, Neustart-Zeilen 0
#    - RestartCount und StartedAt unveraendert

# 3. Reparatur ohne unregister/register
for f in ca.crt client.crt client.key; do
  docker exec appapi-harp cat "/certs/frp/${f}" \
    | docker exec -i "${container}" sh -c "cat > /certs/frp/.${f}.new && mv /certs/frp/.${f}.new /certs/frp/${f}"
done

# 4. Heilung: Kanariensuche (wie Schritt "Search over the ordinary OCS route") antwortet
#    binnen 90 s; 'login to server success' seit ${rotated}; RestartCount und StartedAt
#    unveraendert; app_api:app:list unveraendert; Waechter-Neustartzeilen <= 1
```

Hinweis: `appapi-harp` ist im CI-Schritt "Start HaRP" fest benannt, `${RUNNER_TEMP}/certs` ist als /certs gemountet; `rm -rf` im Container braucht kein sudo auf dem Runner.

### pytest fuer die Waechterlogik (python.yml, Linux)

- Neue Testdatei z. B. `backend/tests/test_harp_connect_supervisor.py`, `skipif(sys.platform == "win32")`.
- Startet `bash backend/docker/harp_connect.sh` mit `HP_SHARED_KEY`, `HP_FRP_ADDRESS`, `HP_FRP_PORT`, `APP_PORT`, `APP_ID`, `HP_FRP_CERT_DIR=<tmp>`, `FINDLING_RUN_DIR=<tmp>` (beides gibt es schon) und einem Stub-frpc (kleines Skript, das x509-Zeilen druckt und schlaeft, und seine Startanzahl in eine Datei schreibt).
- Dafuer braucht das Skript eine Uebersteuerung des frpc-Pfads und des Pruefintervalls (z. B. `FINDLING_FRPC_BIN`, `FINDLING_HARP_CERT_POLL_SECONDS`). Planer-Entscheid; Empfehlung: zulassen, nicht dokumentieren, Kommentar warum (Admin kontrolliert den Container ohnehin, kein neuer Angriffsweg).
- Faelle: (a) x509 bei unveraenderten Dateien -> 0 Neustarts, Abhilfezeile 1x; (b) Dateien werden lesbar (Start ohne Zertifikat) -> genau 1 Neustart, Konfig enthaelt danach certFile/keyFile/trustedCaFile; (c) Dateien wechseln 20x schnell -> Neustarts <= Deckel; (d) Stub endet mit 0 -> Skript endet != 0; (e) TERM -> Stub bekommt TERM, Skript endet 0; (f) Shared Key erscheint in keiner Ausgabezeile; (g) Gegenprobe mit Positivkontrolle: derselbe Test gegen eine Variante ohne Deckel (Parameter) zaehlt mehr Neustarts.
- `bash -n` und shellcheck ueber harp_connect.sh und init.sh als Gate (Muster `bash -n` existiert in test_upgrade_seed_steps.py).
- Optional Vertragstest wie test_language_proof_steps.py: der neue deploy-harp-Schritt existiert und traegt kein `if:`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TrueNAS-HaRP ohne persistentes /certs | `add_storage("/certs", harp_certs)` | truenas/apps #6254, gemergt 2026-10-27 | Ursache fuer den Melder behoben; nach dem TrueNAS-App-Update startet HaRP mit leerem neuem Dataset und erzeugt **einmal** neue Zertifikate, danach stabil [ASSUMED: leeres Dataset beim ersten Start] |
| frp 0.61.1 | frp 0.71.1 (HaRP main) | 2026-10-14 | keine Cert-Reload-Neuerung; Pin behalten |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Go-Text bei Ablauf `x509: certificate has expired or is not yet valid` | Frage 2 | gering, Muster `x509: ` ist allgemein |
| A2 | sha256sum, mkfifo in der Runtime-Stage vorhanden | Standard Stack | Plan bricht; vorab per CI-Image-Probe pruefen |
| A3 | shellcheck auf ubuntu-24.04-Runnern vorinstalliert | Standard Stack | Gate-Schritt muss installieren |
| A4 | Rechte der HaRP-Zertifikatsdateien (docker cp -> root, ggf. 0600) | Pitfall 3 | Doku-Rezept falsch; darum docker-exec-Rezept, in CI belegt |
| A5 | Neues TrueNAS-Dataset fuehrt einmalig zu neuer CA | State of the Art | Issue-Antwort ungenau |
| A6 | AppAPI deaktiviert die ExApp nicht bei Heartbeat-Ausfall waehrend der Rotation | CI-Probe | CI zeigt es; ggf. app:list-Pruefung anpassen |

## Open Questions

1. **ZERT-01-Wortlaut (Owner-Entscheid vor dem Plan).**
   - What we know: Im Issue-#33-Fall gibt es im Container keine neuen Dateien; kein Container-Mechanismus kann ohne AppAPI/HaRP oder Admin heilen.
   - Recommendation: umformulieren zu "Der Container erkennt die Neuausstellung, meldet sie mit Abhilfe im Log, uebernimmt neue Zertifikate in /certs/frp ohne Re-Register und ohne Neustart (auch Moduswechsel), gedeckelt; der Admin repariert mit einem dokumentierten Kopierbefehl statt unregister/register; Upstream-Vorschlag an nextcloud/HaRP fuer automatische Neuverteilung". Der Selbstabruf ueber HaRPs Steuer-API ist als Option fuer den Owner aufgefuehrt, aber nicht empfohlen.
2. **Upstream-Vorschlag an HaRP (Issue oder PR).** HaRP koennte beim Neuerzeugen von /certs/frp an alle laufenden `nc_app_*`-Container `_install_frp_certificates` aufrufen. Empfehlung: Entwurf als Phasenartefakt, Owner sendet (Regel: Claude postet nicht ungefragt). Nicht release-kritisch.
3. **Doku-Ort.** docs/certificates.md behandelt App-Signaturzertifikate, passt nicht. Empfehlung: Abschnitt in docs/install-check.md oder neue Datei docs/harp-tunnel.md (Sprache wie Nachbardateien), Inhalt: Ursache (HaRP-/certs nicht persistent), Vorbeugung (Volume fuer /certs; TrueNAS ab #6254), Erkennen (Logzeile), Reparatur (Kopierbefehl mit Platzhalter fuer den HaRP-Containernamen, da TrueNAS anders benennt), Rueckfall (unregister/register ohne --rm-data, Daten bleiben), Hinweis: Update auf 1.6.0 verteilt ebenfalls frische Zertifikate.
4. **Issue-#33-Antwort (kurz, menschlich, Englisch).** Kernpunkte: TrueNAS-Fix #6254 persistiert HaRPs Zertifikate; nach dessen Update einmal neu registrieren oder Kopierbefehl; 1.6.0 meldet den Zustand klar im Log und uebernimmt neue Dateien ohne Re-Register. Antwort vor "Closes #33"; Entwurf dem Owner zeigen.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker lokal | Laufzeitbeweis | haengt (STATE.md) | - | nur CI |
| gh CLI | Issue/PR-Recherche, CI-Laeufe | ja | - | - |
| GitHub Actions ubuntu-24.04 + arm64-Runner | deploy-harp, python.yml | ja (bestehende Matrix) | - | - |
| HaRP-Image (gepinnter Digest) | Rotation in CI | ja | sha256:603fdf5c... | - |

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | ja (mTLS des Tunnels) | Kein Rueckfall auf schwaecheren Modus durch den Waechter; nur Wechsel "ohne Client-Zert -> mTLS", nie umgekehrt, nie Klartext |
| V5 Input Validation | ja | Dateien nur auf Lesbarkeit/Fingerabdruck pruefen, Inhalt geht an frpc; Logzeilen aus frpc unveraendert durchreichen (kein eval) |
| V6 Cryptography | ja | Keine eigene Kryptographie; sha256sum nur als Aenderungserkennung |
| V7 Logging | ja | Shared Key, Schluesselinhalt, Schluessel-Hash nie loggen; Test (f) |

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Neustart-Sturm durch boesartig flatternde Dateien | DoS | Entprellung, Mindestabstand, Stundendeckel |
| Waechter faellt auf TLS ohne Client-Zert zurueck, wenn Dateien verschwinden | Spoofing | Nur Aufwaertswechsel; Verschwinden nur loggen |
| Missbrauch HP_SHARED_KEY gegen HaRP-Steuer-API | Elevation | Weg bewusst nicht gebaut |
| FIFO/Konfig fuer andere lesbar | Info Disclosure | /app/run 0700, umask 077 beibehalten |

## Sources

### Primary (HIGH confidence)
- fatedier/frp Tag v0.61.1: client/connector.go (realConnect, NewClientTLSConfig pro Dial), pkg/transport/tls.go, client/service.go (loopLoginUntilSuccess, keepControllerWorking, Backoff 20 s, Logzeilen 295/298)
- fatedier/frp v0.71.1 client/connector.go; Compare v0.61.1...v0.71.1 (TLS-Commits)
- nextcloud/HaRP main (09a8222, 0.4.7+): start.sh (Erzeugung nur ohne /certs/frp, 5000 Tage, frps tls.force + trustedCaFile), haproxy_agent.py (docker_exapp_install_certificates, _install_frp_certificates, handle_app_api_request), haproxy.cfg.template, README.md Zeile 256, Dockerfile (frp 0.71.1)
- nextcloud/app_api master (cc8f8b0, 2026-10-27): lib/DeployActions/DockerActions.php (deployExAppHarp, updateCertsHarp, HP_SHARED_KEY-Env), lib/Command/ExApp/Register.php, Update.php
- Issue street1983nk/nextcloud-search#33 (echtes frpc-Log mit x509-Zeilen)
- truenas/apps #6228 (Diskussion) und PR #6254 (gemergt 2026-10-27)
- Repo-Dateien: backend/docker/harp_connect.sh, init.sh, install_frpc.sh, backend/Dockerfile, .github/workflows/deploy-harp.yml

### Secondary (MEDIUM)
- nextcloud/HaRP Issue #107 (Rotationssorge, ohne Umsetzung geschlossen)

## Metadata

**Confidence breakdown:**
- Zertifikatsfluss AppAPI/HaRP: HIGH, Quelltext beider Projekte plus README woertlich
- frpc-Verhalten (Neu-Lesen pro Dial, kein Exit, Backoff): HIGH, Quelltext plus echtes Log
- Waechter-Design: MEDIUM, Entwurf, Beweis erst in CI
- CI-Probe-Machbarkeit: HIGH fuer Rotation (start.sh-Bedingung), MEDIUM fuer Zeitbudget

**Research date:** 2026-10-28
**Valid until:** 2026-11-27 (HaRP/AppAPI bewegen sich; vor Upstream-Vorschlag erneut lesen)
