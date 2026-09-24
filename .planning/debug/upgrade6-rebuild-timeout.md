---
status: awaiting_human_verify
trigger: "deploy-harp Lauf 35997241359, Job stable34/ubuntu-24.04, Block 'Store upgrade 6': nach dem Containerneubau aus docker inspect mit FINDLING_LANGUAGES=es,de,en meldet der Schritt nach 300 s und 133 Runden 'the rebuild did not finish within REBUILD_BUDGET_SECONDS=300'; die Containerlogs zeigen frpc in einer Reconnect-Schleife mit 'connect to server error: EOF' und 'session shutdown'"
created: 2026-09-24
updated: 2026-09-24
---

## Current Focus

reasoning_checkpoint:
  hypothesis: "Der zweite Befund (Lauf 36001341420, Zusicherung 3 und 5 rot) hat NICHTS mit einem Cache zu tun und alles mit der Groesse des Umbaufensters: rebuildRunning kommt ungecacht aus dem Prozess, das Fenster ist aber nur so lang, wie das Tragen der Dokumente dauert, und das dauert bei dem 29-Dokumente-Korpus dieser Strecke Bruchteile einer Sekunde. Das Fenster ist damit kuerzer als eine Leserunde, egal wie fein die Schleife taktet."
  confirming_evidence:
    - "backend/src/findling/api/status.py 295-301: rebuildRunning/Done/Total kommen aus rebuild_progress(), also aus dem Modulglobal _PROGRESS von index/rebuild.py; hinter FILLED_TTL_SECONDS=30 sitzt ausschliesslich languagesFilled, hinter _DEGRADED (5 s) die Entartungsprobe. Kein TTL beruehrt rebuildRunning."
    - "php/lib/Service/AdminViewService.php 453-497: overview() ruft exAppService->adminGet('/status') bei JEDEM Aufruf; weder AdminViewService noch ExAppService halten eine ICache- oder statische Schicht."
    - "index/rebuild.py 482-527: running=true wird beim Eintritt in die Bandschleife gesetzt und im finally auf _AT_REST zurueckgenommen. Das beobachtbare Fenster IST die Tragezeit, nicht die ganze Umbaufolge (Oeffnen, Retire, Swap, Marken sind unsichtbar)."
    - "Eigene Messung 24.09. mit der echten transfer_documents auf diesem Rechner (tantivy 0.26.2, drei Sprachen de,en,es, synthetische 300k-Kompositaliste): die Tragezeit haengt an der TEXTMENGE, nicht an der Dokumentzahl. 0,29 bis 0,59 s je MB Koerpertext; 400 winzige Dokumente tragen in 0,21 s. Deckungsgleich mit dem Modulkopf von rebuild.py (3000 Dokumente zu je 2,5 kB, vier Ketten, 4,39 s = 0,585 s/MB)."
    - "testdata/corpus sind 497 kB DATEIEN (PDFs, Scans, Bilder), der daraus extrahierte Koerpertext ist ein Bruchteil davon: das Fenster dieser Strecke liegt bei ~0,1 bis 0,3 s."
    - "Lauf 36001341420, Zeitstempel: docker start 13:02:26.345, Schleifenende 13:02:28.678 nach 2 Runden. Eine Overview-Leserunde bei gesundem Backend kostet dagegen nur ~50 ms (13:02:25.934 App-Passwort, 13:02:25.986 Leserprobe bestanden), die Runden waren also nicht der Engpass, sondern das Hochlaufen des Containers gegen ein Fenster, das dabei schon vorbei war."
  falsification_test: "Wenn der aufgestockte Korpus (29 + 64 Dokumente zu je 500 000 Zeichen = rund 32 MB Koerpertext) das Fenster NICHT auf mehrere Sekunden verlaengert, also die Schleife weiterhin kein rebuildRunning true liest, ist die Mengenrechnung falsch und der Engpass liegt woanders."
  fix_rationale: "Das Fenster wird an der Wurzel vergroessert: der Umbau traegt Text, also bekommt er Text. 64 Fuelldokumente zu je 500 000 Zeichen kosten beim Umbau rund 8 s (gemessen: 29 kleine + 64 grosse = 7,81 s), beim Indexieren aber fast nichts, weil EMBED_TOKEN_CAP=1024 die Einbettung JE DOKUMENT deckelt (drei Chunks pro Dokument, egal wie lang es ist) und MAX_TEXT_CHARS=524288 den Koerper je Dokument begrenzt. Genau diese Asymmetrie ist der Hebel: Fensterlaenge waechst mit der Textmenge, Indexierkosten wachsen mit der Dokumentzahl. Keine Zusicherung wird entschaerft, REBUILD_BUDGET_SECONDS bleibt bei 300."
  blind_spots: "Ob die semantische Haelfte der Suche die Fuelldokumente in das Band um den besten Treffer (VECTOR_DISTANCE_BAND=14,0) zieht und die drei Begriffe dann mehr als eine Datei zurueckgeben; deshalb steht direkt hinter dem Entladen eine eigene Pruefung der drei Begriffe, die den Fuellkorpus beim Namen nennt. Ob der Laeufer schneller traegt als dieser Rechner (dann kuerzeres Fenster, bei 2x immer noch ~4 s und damit ~15 Leserunden)."

hypothesis: "Das Umbaufenster ist die Tragezeit der Dokumente und skaliert mit der Koerpertextmenge (0,3 bis 0,6 s je MB). Mit dem heutigen Korpus ist es kuerzer als eine Leserunde. Ein Cache ist NICHT im Spiel."
test: "Korpus vor dem Sprachwechsel um 64 Textdokumente zu je 500 000 Zeichen aufstocken (32 MB Koerpertext), ueber denselben Weg wie der Referenzkorpus (cp nach data/testuser/files, occ files:scan, occ findling:index --restart, dieselbe Entladeschleife)"
expecting: "Das Fenster liegt dann bei rund 4 bis 8 s, die Schleife sieht in 15 bis 30 Runden rebuildRunning true, Zusicherung 3 und 5 halten; die Zusicherungen 4, 6 und 9 vergleichen weiterhin exakt, weil beide Momentaufnahmen NACH dem Aufstocken gezogen werden"
next_action: "Owner-Bestaetigung durch einen deploy-harp-Lauf auf diesem Stand: 'Store upgrade 2' muss den Fuellkorpus im Budget entladen und die drei Begriffe weiterhin mit je einer Datei beantworten, 'Store upgrade 6' muss alle neun Zusicherungen halten und die Zahl der Runden mit rebuildRunning true ausweisen"

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

- timestamp: 2026-09-24
  checked: "Die Cachefrage zuerst: woher kommt rebuildRunning in der Overview-Antwort? backend/src/findling/api/status.py 288-309, backend/src/findling/index/rebuild.py 298-312 und 482-527, backend/src/findling/api/resources.py 96 und 486-505, php/lib/Service/AdminViewService.php 453-497 und 1805-1845, php/lib/Service/ExAppService.php"
  found: |
    rebuildRunning, rebuildDone und rebuildTotal kommen aus rebuild_progress(), und das ist
    eine Leseoperation auf dem Modulglobal _PROGRESS, das die Bandschleife zwischen zwei
    Baendern setzt. Kein TTL, kein Schluessel, keine Uhr.
    FILLED_TTL_SECONDS = 30.0 gehoert zu resources.filled_languages() und damit AUSSCHLIESSLICH
    zu languagesFilled; _DEGRADED mit 5 s gehoert zur Entartungsprobe. Beide fassen die vier
    Umbauwerte nicht an.
    Die PHP-Seite haelt ebenfalls nichts fest: overview() ruft adminGet('/status') bei jedem
    Aufruf, backend() dekodiert nur, und weder AdminViewService noch ExAppService kennen
    ICacheFactory oder ein statisches Feld.
  implication: |
    Der TTL-Verdacht ist widerlegt. Die Schleife wuerde rebuildRunning true sehen, wenn es
    true WAERE, waehrend sie liest. Der Gegner ist nicht der Cache, sondern die Laenge des
    Fensters.

- timestamp: 2026-09-24
  checked: "Wie lang ist das Fenster? index/rebuild.py 482-527 (wo running true gesetzt und zurueckgenommen wird) plus eine eigene Messung mit der echten transfer_documents auf diesem Rechner (backend/.venv, tantivy 0.26.2, Sprachen de,en,es, synthetische Kompositaliste mit 300000 Eintraegen)"
  found: |
    running=true steht genau um die Bandschleife: davor das Oeffnen beider Verzeichnisse,
    danach wait_merging_threads, Retire, Swap und die Marken. Das beobachtbare Fenster ist
    also die reine Tragezeit.
    Gemessen (Tragezeit, drei Sprachen):
      400 Dokumente zu je   3 kB (1,2 MB)   0,21 s   -> die Dokumentzahl kostet fast nichts
      200 Dokumente zu je  20 kB (4,0 MB)   1,15 s
      100 Dokumente zu je 100 kB (10 MB)    1,81 s
      29 kleine + 32 grosse (16,1 MB)       3,32 s
      29 kleine + 64 grosse (32,1 MB)       7,81 s
    Das sind 0,25 bis 0,6 s je MB Koerpertext; der Modulkopf von rebuild.py nennt fuer 3000
    Dokumente zu je 2,5 kB und vier Ketten 4,39 s, also 0,585 s/MB: dieselbe Groessenordnung
    aus zwei unabhaengigen Messungen.
  implication: |
    Das Fenster haengt an der TEXTMENGE und nicht an der Dokumentzahl. Der heutige Korpus sind
    497 kB Dateien (PDFs, Scans, Bilder) und damit deutlich weniger Koerpertext: das Fenster
    liegt bei ein bis drei Zehntelsekunden. Mehr kleine Dokumente einzuspielen wuerde daran
    nichts aendern, 400 winzige Dokumente bringen 0,21 s.

- timestamp: 2026-09-24
  checked: "Was kostet mehr Text auf der Indexierseite? backend/src/findling/config.py 241 (MAX_TEXT_CHARS), 583 (EMBED_TOKEN_CAP), backend/src/findling/embed/chunker.py 27-33 und 81-121, docs/measurements/2026-09-vergleichsmessung-m7g/00-kernaussage.md 180-190"
  found: |
    MAX_TEXT_CHARS = 524288 begrenzt den Koerper JE DOKUMENT, EMBED_TOKEN_CAP = 1024 begrenzt
    die Einbettung JE DOKUMENT, und der Deckel greift laut Chunker-Kopf VOR dem Schnitt: ein
    Dokument wird auf seine ersten 1024 Token gekuerzt und daraus werden zwei bis drei Chunks,
    unabhaengig von seiner Laenge. Die gemessenen Durchsaetze der Vergleichsmessung sind
    31,6 bis 45,7 Dokumente je Minute mit OCR und rund 170 je Minute fuer die Einbettung allein.
  implication: |
    Die Kosten der beiden Seiten stehen quer zueinander: die Fensterlaenge waechst mit der
    TEXTMENGE, die Indexierkosten wachsen mit der DOKUMENTZAHL. Grosse Textdateien sind damit
    der billige Weg zu einem langen Fenster: 64 Dokumente zu je 500000 Zeichen kosten beim
    Indexieren 64 Dokumente (drei Chunks je Stueck) und beim Umbau rund 8 s.

- timestamp: 2026-09-24
  checked: "Kann die Leseschleife nicht einfach dichter takten? Schrittlog Lauf 36001341420, Zeitstempel 13:02:24.75 bis 13:02:31.75, und .github/workflows/deploy-harp.yml 3899-3971"
  found: |
    Eine Overview-Leserunde kostet bei gesundem Backend rund 50 ms (13:02:25.9348 App-Passwort,
    13:02:25.9865 die bestandene Leserprobe dahinter), eine Momentaufnahme mit drei Suchen und
    einem docker exec 0,23 s. Die Schleife pausiert bereits nur 0,2 s und laeuft damit mit
    rund vier Runden je Sekunde. Die zwei Runden des Laufs sind kein Taktproblem: die erste
    lief gegen einen Container, der noch hochfuhr (nicht-200 kostet sleep 1), und als die
    zweite antwortete, war der Umbau von zwei Zehntelsekunden laengst vorbei.
  implication: |
    Ein feinerer Leser ist nicht der Hebel, und ein Hammer auf HaRP waere er erst recht nicht.
    Selbst mit 50 ms Takt bleibt die Zusicherung 5 unmoeglich, weil der Kanarienvogel eine
    Suche UND eine zweite Leserunde INNERHALB des Fensters braucht. Das Fenster muss groesser
    werden, nicht der Leser schneller.

## Resolution

root_cause: |
  ZWEI Ursachen hintereinander, beide in der CI-Strecke und keine im Produkt.

  1. (Lauf 35997241359, behoben mit bce9908 und 7fa4c21) Der Containerneubau rekonstruiert den
     ExApp-Container aus seinem eigenen docker inspect. docker inspect beschreibt Image, Netz,
     Environment, Mounts und Labels, aber nicht die Schreibschicht. HaRP legt die drei
     Tunnelzertifikate (/certs/frp/client.crt, client.key, ca.crt) jedoch erst NACH dem Erzeugen
     des Containers per docker exec genau dort ab. docker rm -f loescht sie mit, der neue
     Container findet kein lesbares Clientzertifikat, harp_connect.sh konfiguriert den Tunnel
     ohne mTLS, der frp-Server weist jeden Login mit EOF ab. Die Beobachtungsschleife las
     300 s lang backendReachable false.

  2. (Lauf 36001341420, der Rest) Der Tunnel steht wieder, die Strecke laeuft bis zu den
     Zusicherungen, und jetzt zeigt sich, was Punkt 1 verdeckt hatte: das Umbaufenster ist
     kuerzer als eine Leserunde. rebuildRunning ist nur waehrend der Bandschleife von
     transfer_documents true, und die Tragezeit haengt an der Koerpertextmenge, nicht an der
     Dokumentzahl (0,25 bis 0,6 s je MB, zweifach gemessen). Der Referenzkorpus sind 39 Dateien
     mit wenig extrahiertem Text, also rund zwei Zehntelsekunden Fenster. Zusicherung 3
     (Banner gesehen) und Zusicherung 5 (Kanarienvogel im Fenster) hatten nichts zu messen.
     KEIN Cache: rebuildRunning kommt ungecacht aus dem Prozess, FILLED_TTL_SECONDS=30 deckt
     nur languagesFilled.
fix: |
  1. Commit bce9908: die Zertifikate werden vor dem docker rm -f aus dem alten Container geholt
     und vor dem ERSTEN Start des neuen wieder hineingelegt (docker create, docker cp,
     docker start).
  2. Commit 7fa4c21: backendReachable wird getrennt vom Fortschritt gelesen; war es nie true,
     nennt der Fehler den Tunnel statt den Umbau.
  3. Commit dieser Runde, fix(18-12): "Store upgrade 2" legt neben den Referenzkorpus einen
     Fuellkorpus aus 64 Textdateien zu je 500019 Zeichen (rund 32 MB Koerpertext), ueber genau
     denselben Weg wie der Referenzkorpus (cp nach data/testuser/files, occ files:scan,
     occ findling:index --restart, dieselbe Entladeschleife, deren expected sich aus
     find ... | wc -l selbst nachzieht). Damit liegt das Umbaufenster bei rund 4 bis 8 s und
     die Schleife bekommt 15 bis 30 Leserunden hinein.
     Direkt hinter dem Entladen pruefen die drei Begriffe Belehrung, Auszug und Erinnerung
     erneut auf genau eine Datei, damit ein semantisches Durchschlagen des Fuellkorpus dort
     auffaellt, wo es verursacht wird.
     Die Leseschleife zaehlt zusaetzlich die Runden mit rebuildRunning true und weist sie im
     Log, in der Fehlermeldung von Zusicherung 3 und in der Zusammenfassung aus, damit die
     naechste Dimensionierung eine Zahl hat und keinen Eindruck.
     Kein Produktcode angefasst, keine Zusicherung entfernt oder entschaerft, beide Budgets
     unveraendert (REBUILD_BUDGET_SECONDS 300, UPGRADE_DRAIN_BUDGET_SECONDS 900).
verification: |
  - Cachefrage am Code geklaert (status.py, rebuild.py, resources.py, AdminViewService.php,
    ExAppService.php): rebuildRunning ist ungecacht, nur languagesFilled sitzt hinter dem TTL.
  - Dimensionierung gemessen, nicht geschaetzt: die echte transfer_documents mit tantivy 0.26.2,
    drei Sprachen und einer 300000-Eintraege-Kompositaliste traegt 29 kleine plus 64 grosse
    Dokumente (32,1 MB) in 7,81 s und 29 plus 32 (16,1 MB) in 3,32 s; 400 winzige Dokumente in
    0,21 s. Gegenprobe aus fremder Quelle: der Modulkopf von rebuild.py nennt 0,585 s je MB.
  - Budgetfrage am echten Lauf belegt statt geraten: "Store upgrade 2" brauchte in Lauf
    36001341420 34 s von 900 s (13:01:09Z bis 13:01:43Z), der ganze Job 14 min 46 s von 45.
    Die Aufstockung kostet nach Rechnung 60 bis 120 s, also bleibt beides unveraendert.
  - Der Generator des Fuellkorpus lokal ausgefuehrt: 500019 Byte je Datei, unter
    MAX_TEXT_CHARS=524288, kein Treffer auf belehr, auszug, erinner, florpel oder findling.
  - YAML: yaml.safe_load der ganzen Datei laeuft durch.
  - Kappen-Check: die beiden run-Bloecke ueber 15000 Zeichen ("Store upgrade 3" 18417,
    "Store upgrade 6" 27945) enthalten kein ${{ , GitHub wertet sie also nicht als Template
    und die 21000-Zeichen-Grenze greift nicht. "Store upgrade 2" liegt bei 8061 Zeichen.
  - bash -n auf den extrahierten run-Bloecken von "Store upgrade 2" und "Store upgrade 6":
    fehlerfrei.
  - Kein Python beruehrt, also keine Python-Gates faellig.
  OFFEN und nur auf dem Laeufer messbar: ob die semantische Haelfte die Fuelldokumente in das
  Band um den besten Treffer zieht (die neue Pruefung hinter dem Entladen sagt es), und wie
  viele Leserunden das Fenster auf dem Laeufer wirklich hergibt (die neue Zeile "the banner was
  up in N of those rounds" sagt es).
files_changed:
  - .github/workflows/deploy-harp.yml

---
**VERIFIED 24.09.2026:** deploy-harp-Lauf 36006893151 GRUEN auf allen vier
Matrix-Aesten. "Store upgrade 5" haelt alle sechs Zusicherungen (Bestand
unberuehrt, languages-Marke legitim abwesend), "Store upgrade 6" alle neun
(Umbau beobachtet, Schema genau eine Stufe, Sprachmarke de,en,es,
Vektorbestand byteidentisch). Beide Wurzelursachen bestaetigt behoben.
