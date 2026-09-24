---
status: awaiting_human_verify
trigger: "deploy-harp Lauf 35997241359, Job stable34/ubuntu-24.04, Block 'Store upgrade 6': nach dem Containerneubau aus docker inspect mit FINDLING_LANGUAGES=es,de,en meldet der Schritt nach 300 s und 133 Runden 'the rebuild did not finish within REBUILD_BUDGET_SECONDS=300'; die Containerlogs zeigen frpc in einer Reconnect-Schleife mit 'connect to server error: EOF' und 'session shutdown'"
created: 2026-09-24
updated: 2026-09-24
---

## Current Focus

reasoning_checkpoint:
  hypothesis: "HaRP legt die drei Tunnelzertifikate erst nach dem Erzeugen des Containers per docker exec in dessen Schreibschicht (/certs/frp). docker rm -f loescht sie, docker run stellt sie nicht wieder her, harp_connect.sh konfiguriert den Tunnel deshalb ohne Clientzertifikat und der frp-Server weist jeden Login mit EOF ab. Die App und der Umbau sind in Ordnung, nur der Weg von Nextcloud zum Backend ist tot."
  confirming_evidence:
    - "Containerlog des NEUEN Containers enthaelt 'the index rebuild ended: the rebuilt directory is in place and the two marks are current again' - der Umbau lief und war nach rund zwei Sekunden durch"
    - "Alle 133 Runden lesen backendReachable false und einen leeren backend-Block; languagesActive bleibt leer, deshalb greift die Abbruchbedingung nie"
    - "backend/Dockerfile 410-431 beschreibt genau diese Kette (HaRP schreibt die drei Dateien per docker exec, sonst 'the frp server then refuses every login with EOF') und legt /certs/frp im Image nur leer an"
    - "Die Mountliste des Neubaus nennt genau ein Volume und keinen /certs-Mount, die Zertifikate koennen also nur in der Schreibschicht gelegen haben"
    - "docs/dev-setup.md 490-497 und docs/install-check.md arm64-3 halten dieselbe Kette zweimal unabhaengig fest"
  falsification_test: "Wenn der neu erzeugte Container nach dem Einspielen der drei Zertifikate weiterhin 'connect to server error: EOF' meldet und backendReachable false bleibt, ist die Hypothese falsch"
  fix_rationale: "Die Rekonstruktion traegt Image, Netz, Environment, Mounts und Labels und uebersieht genau das, was nicht in docker inspect steht. Der Fix ergaenzt die fehlende Zutat an der Wurzel: die drei Dateien werden vor dem docker rm -f aus dem alten Container geholt und vor dem ERSTEN Start des neuen wieder hineingelegt (docker create, docker cp, docker start), denn frpc liest sie einmal beim Start. Keine Zusicherung wird entschaerft, das Budget bleibt bei 300 s."
  blind_spots: "Ob das Umbaufenster von rund zwei Sekunden gross genug ist, damit die Schleife rebuildRunning true UEBERHAUPT sieht, sobald der Tunnel wieder steht (Zusicherung 3 Mittelmessung und Zusicherung 5 Kanarienvogel) - das ist erst nach einem gruenen Tunnel messbar; ob HaRP die Zertifikate bei Ablauf rotiert und der Neubau dann eine veraltete Kopie einsetzt"

hypothesis: "H1 bestaetigt und praezisiert: HaRP legt die drei Tunnelzertifikate (/certs/frp/client.crt, client.key, ca.crt) NACH dem Erzeugen des Containers per docker exec in dessen SCHREIBSCHICHT. docker rm -f nimmt diese Schicht mit, das Image bringt /certs/frp nur leer mit. Der neu erzeugte Container findet kein lesbares Clientzertifikat, harp_connect.sh konfiguriert den Tunnel ohne mTLS, der frp-Server weist jeden Login mit EOF ab. Die App laeuft, der Umbau laeuft und ist nach rund zwei Sekunden durch, aber Nextcloud sieht backendReachable false und die Beobachtungsschleife liest 300 s lang einen leeren backend-Block."
test: "Log der 133 Runden gegen den Containerlog stellen; Dockerfile und harp_connect.sh auf die Herkunft von /certs/frp pruefen"
expecting: "Wenn die Hypothese stimmt: der Containerlog nennt den Umbau als abgeschlossen, die Ueberwachung nennt backendReachable false, und Repo-Dokumentation beschreibt genau diese Zertifikatsuebergabe"
next_action: "Owner-Bestaetigung durch einen deploy-harp-Lauf auf diesem Stand: Block 'Store upgrade 6' muss den Tunnel wiederbekommen (backendReachable true in den ersten Runden) und die neun Zusicherungen durchlaufen"

## Symptoms

expected: |
  Der Containerneubau mit FINDLING_LANGUAGES=es,de,en loest den Umbau des Indexverzeichnisses aus,
  die Beobachtungsschleife sieht rebuildRunning true, faengt die Kanarienvogelsuche im Fenster und
  verlaesst die Schleife, sobald rebuildRunning false und languagesActive de,en,es sind. Danach
  laufen die neun Zusicherungen.
actual: |
  1. Der Container wird um 12:22:36Z neu erzeugt, docker ps meldet ihn "Up Less than a second".
  2. 133 Runden lang antwortet die Uebersicht HTTP 200, aber mit "backendReachable": false und
     einem leeren backend-Block ("languagesActive":"", "rebuildRunning":false, alle Zaehler 0).
  3. Nach 300 s bricht der Schritt ab mit "the rebuild did not finish within
     REBUILD_BUDGET_SECONDS=300 after 133 rounds".
  4. Der ausgegebene Containerlog zeigt: uvicorn startet, der Umbau laeuft UND endet erfolgreich,
     danach frpc alle 10 s im Reconnect mit "connect to server error: EOF" bzw. "session shutdown".
errors: |
  ##[error]the rebuild did not finish within REBUILD_BUDGET_SECONDS=300 after 133 rounds
  [W] [client/service.go:298] connect to server error: EOF
  [W] [client/service.go:298] connect to server error: session shutdown
  "backendReachable":false
reproduction: deploy-harp Workflow, Job stable34/ubuntu-24.04, Block "Store upgrade 6", Lauf 35997241359
started: mit Plan 18-12, dem Schritt "Store upgrade 6" selbst; der Containerneubau ist neu in dieser Phase

## Eliminated

- hypothesis: "H2: der Umbau startet nicht, weil eine der drei Startbedingungen der Lifespan-Aufgabe (Marken, eigenes Volume, scharfgeschaltet) im CI-Kontext nicht erfuellt ist"
  evidence: |
    Der Containerlog des neuen Containers enthaelt alle Zeilen, die ein gestarteter und
    durchgelaufener Umbau schreibt:
      "WARNING:findling.api.resources:the index was built with different versions than this build
       produces, a reindex is required: languages"
      "INFO:findling:findling backend was enabled before this start, indexing continues without a switch"
      "INFO:findling:findling rebuilds the index directory the changed version marks ask for"
      "INFO:findling.index.rebuild:carried 29 documents over into the new index directory"
      "INFO:findling.index.rebuild:the rebuilt index directory is in place; the schema and language
       marks are current again"
      "INFO:findling:the index rebuild ended: the rebuilt directory is in place and the two marks
       are current again"
    Alle drei Bedingungen waren also erfuellt, der Enable-Merker hat den Neubau ueberlebt.
  timestamp: 2026-09-24

- hypothesis: "H3: der Umbau laeuft, ist aber langsamer als 300 s auf dem Laeufer"
  evidence: |
    Der Umbau war nach rund zwei Sekunden durch. Die frpc-Zeilen tragen Zeitstempel und klammern
    den Blockt der App-Logs ein: 12:22:36.346 vor dem uvicorn-Start, 12:22:38.482 nach
    "indexing is armed and the work stock is empty". Zwischen Containerstart (12:22:36Z) und dem
    Ende des Umbaus liegen keine drei Sekunden. Das Budget von 300 s ist nicht knapp, es wird nur
    nicht gemessen.
  timestamp: 2026-09-24

## Evidence

- timestamp: 2026-09-24
  checked: "Schrittlog Lauf 35997241359, Zeilen 522-668 (die Ausgabe nach ##[endgroup])"
  found: |
    Der abschliessend gedruckte probe_a-Koerper lautet u.a.
    {"...","backendReachable":false,"backend":{"indexed":0,...,"languagesActive":"",
     "languagesFilled":"","rebuildRunning":false,"rebuildDone":0,"rebuildTotal":0,...}}
    und "lockstep":{"state":"unknown","companion":"1.2.0","container":""}.
  implication: |
    Die Schleife hat in allen 133 Runden HTTP 200 bekommen, aber nie Daten aus dem Backend.
    Die Abbruchbedingung (running=false UND active=de,en,es) konnte nie greifen, weil active
    dauerhaft leer war. Der Abbruch ist ein Befund ueber die Erreichbarkeit, nicht ueber den Umbau.

- timestamp: 2026-09-24
  checked: ".github/workflows/deploy-harp.yml, Zeilen 3757-3846 (die Rekonstruktion)"
  found: |
    Getragen werden: Image, Netzwerkmodus (Pflicht host), Restart-Policy, Environment (eine
    Zeile geaendert), Mounts aus .Mounts[], Labels. Abgebrochen wird bei jeder unverstandenen
    Form. Die Schreibschicht des Containers ist NICHT Teil dieser Liste.
    Der Log bestaetigt es: "the mounts carried over:" nennt genau einen Eintrag,
    type=volume,source=nc_app_findling_backend_data,target=/nc_app_findling_backend_data.
    Es gibt also keinen Bind-Mount fuer /certs, die Zertifikate koennen nur in der
    Schreibschicht gelegen haben.
  implication: Der Neubau erzeugt einen Container ohne /certs/frp-Inhalt

- timestamp: 2026-09-24
  checked: "backend/Dockerfile, Zeilen 410-431 (Kommentar zu /certs/frp) und Zeile 439-441"
  found: |
    "/certs/frp  where HaRP installs the client certificate, its key and the CA of the tunnel.
     It creates the directory and writes the three files through docker exec, and that exec runs
     as the image user ... harp_connect.sh finds no readable certificate and falls back to TLS
     without a client certificate, and the frp server then refuses every login with EOF.
     The container is up, the app answers on its socket, and it is unreachable."
    Das Image legt /certs/frp nur leer an (mkdir -p, chown findling, chmod 0700).
  implication: |
    Die Fehlerbeschreibung im eigenen Dockerfile ist wortgleich mit dem beobachteten Symptom.
    Die Zertifikate kommen von HaRP nach dem Erzeugen, nicht aus dem Image.

- timestamp: 2026-09-24
  checked: "backend/docker/harp_connect.sh, Zeilen 17, 75-97"
  found: |
    CERT_DIR="${HP_FRP_CERT_DIR:-/certs/frp}"; der Zweig
    if [ -r "${CERT_DIR}/client.crt" ] && [ -r "${CERT_DIR}/client.key" ] && [ -r "${CERT_DIR}/ca.crt" ]
    schreibt transport.tls.certFile/keyFile/trustedCaFile in die frpc-Konfiguration, sonst laeuft
    der Tunnel ohne Clientzertifikat weiter.
  implication: Ohne die drei Dateien konfiguriert sich frpc selbst in den EOF-Zustand, ohne den Start abzubrechen

- timestamp: 2026-09-24
  checked: "docs/dev-setup.md Zeilen 490-497 und docs/install-check.md Zeile 524 (Befund arm64-3)"
  found: |
    dev-setup: "Der erste Start laeuft regulaer noch ohne Zertifikate (not readable by uid 1000),
    weil HaRP sie erst danach hineinlegt und den Container neu startet ... Steht mutual TLS aber
    in keiner Sequenz, hat HaRP sie nicht ablegen koennen, und der frp-Server weist den Tunnel ab,
    obwohl der Container laeuft und die App auf ihrem Socket antwortet."
    install-check arm64-3: dieselbe Kette einmal echt gemessen, inklusive "connect to server
    error: EOF".
  implication: |
    Die Uebergabe der Zertifikate nach dem Erzeugen ist dokumentiertes Verhalten von HaRP und
    wurde in diesem Projekt schon zweimal beobachtet. Der Neubau per docker run umgeht HaRP
    vollstaendig, also findet die Uebergabe nie statt.

- timestamp: 2026-09-24
  checked: "Der Diagnoseblock des Timeout-Zweigs, .github/workflows/deploy-harp.yml Zeile 3925-3932"
  found: |
    Gedruckt werden head -c 1000 von probe_a und docker logs | tail -n 80. Die 80 Zeilen bestehen
    fast vollstaendig aus der frpc-Reconnect-Schleife; die eine Zeile, die die Ursache benennt
    ("harp_connect: /certs/frp exists but client.crt, client.key or ca.crt is not readable ...",
    bzw. ihr Fehlen), steht am Kopf des Logs und faellt aus dem tail heraus.
  implication: |
    Der Schritt hat die richtige Beobachtung gemacht und die falsche Ueberschrift darueber
    gesetzt. Das ist ein zweiter, eigener Mangel der Strecke.

## Resolution

root_cause: |
  Der Containerneubau in "Store upgrade 6" rekonstruiert den ExApp-Container aus seinem eigenen
  docker inspect. docker inspect beschreibt Image, Netz, Environment, Mounts und Labels, aber
  nicht die Schreibschicht. HaRP legt die drei Tunnelzertifikate (/certs/frp/client.crt,
  client.key, ca.crt) jedoch erst NACH dem Erzeugen des Containers per docker exec genau dort ab.
  docker rm -f loescht sie mit der Schreibschicht, docker run erzeugt aus dem Image einen
  Container mit leerem /certs/frp, harp_connect.sh konfiguriert den Tunnel deshalb ohne
  Clientzertifikat, und der frp-Server weist jeden Login mit EOF ab.
  Folge: die App startet, der Umbau laeuft und endet nach rund zwei Sekunden korrekt, aber der
  Weg von Nextcloud zum Backend ist tot. Die Beobachtungsschleife liest den Fortschritt ueber
  die Uebersichtsroute der PHP-App, also ueber HaRP, sieht 133 Runden lang backendReachable false
  und faellt nach 300 s in den Timeout-Zweig, der den Befund als "der Umbau ist nicht fertig
  geworden" ueberschreibt.
  Kein Produktfehler: der Container, die App und der Umbau verhalten sich korrekt. Fehlerhaft ist
  allein die Rekonstruktion in der CI-Strecke.
fix: |
  1. .github/workflows/deploy-harp.yml, Block "Store upgrade 6", Containerneubau (Commit bce9908):
     Vor dem docker rm -f wird geprueft, dass der alte Container /certs/frp/client.crt,
     client.key und ca.crt lesbar traegt (docker exec laeuft als Image-Nutzer, also dieselbe
     Frage, die harp_connect.sh stellt); fehlt eine der drei, endet der Schritt mit eigener
     Meldung statt zu raten, nach der Form aller anderen Pruefungen dieser Rekonstruktion.
     Danach docker cp "${container}:/certs/frp" - in eine tar-Datei.
     Aus docker run wird docker create + docker cp - "${container}:/certs" + docker start, in
     genau dieser Reihenfolge, weil frpc /certs/frp einmal beim Hochlaufen liest. --detach faellt
     aus run_args weg (bei docker create ungueltig), rebuild_start wird jetzt unmittelbar vor
     docker start genommen.
  2. .github/workflows/deploy-harp.yml, Beobachtungsschleife und Timeout-Zweig (Commit 7fa4c21):
     backendReachable wird getrennt vom Fortschritt gelesen und in reachable gemerkt. War es nie
     true, nennt der Fehler den Tunnel des erzeugten Containers statt den Umbau und druckt die
     harp_connect-Zeilen aus dem KOPF des Containerlogs, die aus dem bestehenden tail -n 80
     herausfielen. Der Umbau-Spruch samt Budget-Satz bleibt fuer seinen Fall unveraendert.
  Kein Produktcode angefasst, keine Zusicherung entfernt oder entschaerft,
  REBUILD_BUDGET_SECONDS bleibt bei 300.
verification: |
  - Unabhaengige Gegenprobe des mechanischen Teils, ausserhalb der Strecke und mit einem anderen
    Muster als der Umsetzung: ein Wegwerf-Image (alpine, uid/gid 1000, /certs und /certs/frp auf
    0700 und dem Nutzer gehoerend) bildet die Form des Findling-Images nach, die drei Dateien
    werden wie von HaRP per docker exec als Image-Nutzer hineingeschrieben.
    Ergebnis: docker cp c:/certs/frp - liefert ein tar mit der Wurzel frp/ (frp/, frp/ca.crt,
    frp/client.crt, frp/client.key); docker cp - c:/certs gegen einen mit docker create
    erzeugten, NICHT gestarteten Container legt sie nach /certs/frp; nach docker start meldet der
    Container uid=1000(findling) und alle drei Dateien als lesbar, Eigentuemer 1000:1000 und
    Modus erhalten (client.key bleibt 0600). Genau die Bedingung, die harp_connect.sh Zeile 81
    abfragt.
  - YAML: yaml.safe_load der ganzen Datei laeuft durch.
  - Kappen-Check: der run-Block von "Store upgrade 6" ist 26704 Zeichen lang und enthaelt kein
    ${{ , GitHub wertet ihn also nicht als Template und die 21000-Zeichen-Grenze greift nicht.
    Kein anderer run-Block der Datei ueberschreitet die Grenze mit einem Ausdruck darin.
  - bash -n auf dem extrahierten run-Block: fehlerfrei, vor jedem der beiden Commits.
  - Kein Python beruehrt, also keine Python-Gates faellig.
  OFFEN und nur auf dem Laeufer messbar: ob der Umbau (rund zwei Sekunden) noch laeuft, wenn der
  Tunnel wieder steht, also ob die Schleife rebuildRunning true ueberhaupt zu sehen bekommt
  (Zusicherung 3 Mittelmessung, Zusicherung 5 Kanarienvogel).
files_changed:
  - .github/workflows/deploy-harp.yml
