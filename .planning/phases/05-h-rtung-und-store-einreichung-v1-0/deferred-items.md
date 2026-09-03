# Deferred items of phase 05

Out of scope discoveries. Each one was found while executing a plan of this
phase, none of them was caused by the task at hand, and none of them was fixed
there. They are written down here so that they are not rediscovered from scratch.
Jeder Eintrag nennt den Plan, den Grund und den Ort, an den er gehört.

## DI-05-01: `deploy-harp.yml` has not run on a GitHub runner yet

**Found during:** 05-01, at the last acceptance criterion of task 2.

The acceptance criterion asks for a green run of the new workflow on the working
branch, triggered with `gh workflow run deploy-harp.yml`. That was not possible
from the execution worktree, for two reasons that have nothing to do with the
workflow itself: the branch `worktree-agent-05-01` exists only locally and is
never pushed by a parallel executor, and `workflow_dispatch` only offers a
workflow that is present on the default branch.

**What was done instead.** The whole path was executed locally against
`scripts/dev/compose-harp.yaml`, which is the same sequence of commands with two
addresses changed, and both defects it uncovered are fixed (see the plan summary).
`actionlint` passes on the file, the YAML loads, and the HaRP digest was resolved
against the registry.

**What is left.** The workflow has push triggers on `backend/**`,
`php/appinfo/**` and its own path, so the first run happens on its own once this
branch is merged. Someone has to look at that run. Two things can only fail
there, because they have no local counterpart: the local registry on port 5000
of the runner and the `--net host` variant of the daemon registration, which
replaces the compose network of the local run.

## DI-05-02: HaRP fails to update the OS trust store inside the ExApp container

**Found during:** 05-01, while measuring the HaRP install.

HaRP runs two commands in the freshly created ExApp container through
`docker exec`: it copies the tunnel certificates into `/certs/frp`, and it runs
`update-ca-certificates`. The exec runs as the image user, which is the
unprivileged `findling` (uid 1000), so the second command fails:

```
Certificate update command failed in container 'nc_app_findling_backend'.
Exit: 2, /usr/sbin/update-ca-certificates: 109: cannot create
/etc/ssl/certs/ca-certificates.crt.new: Permission denied
```

**Why it was not fixed.** The first command is the load bearing one and is fixed
in 05-01 (the image now carries `/certs/frp` owned by that user). The second one
writes the HaRP CA into the operating system trust store of the container, and
`docker/harp_connect.sh` never reads it: it points frpc at
`trustedCaFile = /certs/frp/ca.crt` explicitly. A trust store that the
application can rewrite is a worse problem than a log line, so making
`/etc/ssl/certs` writable for uid 1000 is deliberately not the answer.

**What is left.** Two questions for the plan that owns the ARM and AIO run: does
anything in the container ever need to trust the HaRP CA through the OS bundle
(today nothing does, because the only TLS client is frpc), and does the error
line have to be silenced so that an admin does not read it as a broken install.
The honest cheap answer is a sentence in `docs/uninstall.md` or
`docs/dev-setup.md` naming the line as expected.

## DI-05-03: 05-RESEARCH.md Pattern 1 registers the daemon with the wrong nextcloud url

**Found during:** 05-01, when the first install ended in `heartbeat check failed`.

Pattern 1 of `05-RESEARCH.md` (and the `<interfaces>` block of 05-01-PLAN.md that
quotes it) registers the HaRP daemon with `http://localhost:8080` as the
Nextcloud url, that is with the address of Nextcloud. In HaRP mode AppAPI
resolves the address of an ExApp as `{nextcloud_url}/exapps/{appId}`
[VERIFIED: `DockerActions::resolveExAppUrl`, read in the running instance of
app_api on 2026-09-03], because HaRP is the entry point: it forwards `/exapps`
into the frp tunnel and everything else to `NC_INSTANCE_URL`. With the address of
Nextcloud in that position every heartbeat goes to the web server, which answers
404, and the install ends with `heartbeat check failed` next to a healthy
container.

**What was done.** `deploy-harp.yml` and `docs/dev-setup.md` carry the corrected
form (`http://localhost:8780` and `http://harp:8780`) with the reason next to it.

**What is left.** Everything else in this phase that quotes Pattern 1 has to use
the corrected form: plan 05-08 (version matrix and uninstall proof), and above
all the AIO run on the rented ARM box, where the same mistake would cost hours in
a run that takes a day. `05-RESEARCH.md` itself is deliberately not rewritten,
because a research document records what was known when it was written; this
entry is the correction.

## DI-05-04: Ein Nachläufer der Löschexpansion kann eine sofortige Wiederherstellung wieder löschen

**Found during:** Plan 05-04.

**Was:** Die Löschung eines Ordners plant `SubtreeExpandJob` mit `kind=delete`,
und der Job arbeitet den Teilbaum in Bändern von 250 Einträgen ab, mit einem
Cursor im Jobargument und einem selbst geplanten Nachfolger. Holt ein Nutzer den
Ordner zurück, während diese Kette noch läuft, sieht der nächste Nachlaufer die
wiederhergestellten Dateien hinter seinem Cursor und reiht für sie
Löschaufträge ein. `KIND_RANK` macht `delete` zum absorbierenden Element, also
gewinnt die Löschung gegen die Inhaltsaufgabe, die die Wiederherstellung gerade
eingereiht hat. Die Dateien sind danach wieder aus dem Index heraus, und erst
der nächtliche Abgleich holt sie zurück.

**Wie eng das Fenster ist:** Die Kette endet, sobald ein Band leer
zurückkommt, und läuft im Abstand von fünf Sekunden. Der Fall braucht also einen
Ordner, der groß genug für mehrere Bänder ist, und eine Wiederherstellung
innerhalb dieser Sekunden. In der Nachstellung des Plans (drei Dateien, ein
Band) trat er nicht auf: der Nachläufer startete hinter der höchsten Datei-Id
und kam leer zurück, ohne etwas einzureihen.

**Warum nicht hier erledigt:** außerhalb des Plans, und die Behebung ist keine
Zeile. Sie braucht eine Entscheidung darüber, woran ein Teilbaum-Job erkennt,
dass sein Gegenstand nicht mehr gelöscht ist: ein Zeitstempel der Löschung im
Jobargument, gegen den der Job den Zustand des Ankers prüft, oder ein Abbruch,
sobald der Anker nicht mehr im Papierkorb liegt. Beides ist ein neues
Argumentfeld und damit eine Formatänderung an einem Job, der in dieser Phase
noch von anderen Plänen angefasst wird.

**Wohin es gehört:** in einen Folgeplan, der ohnehin an `SubtreeExpandJob`
arbeitet, oder in den Phase-Review. Bis dahin trägt der ETag-Abgleich den Fall,
was seiner Rolle als Sicherung entspricht.

## DI-05-05: Ein Kommentar in `integration.yml` nennt nur die Scans

**Found during:** Plan 05-04.

**Was:** Der Schritt "Wait until the queue is empty and every file has a
verdict" begründet seine Warteschleife mit "The scans reach the queue twice:
once as a content job, which ends as skipped(no_text_layer), and once more as an
ocr job". Seit diesem Plan gilt derselbe Satz für die vier Bildformate: sie
laufen ebenfalls zweimal durch die Warteschlange. Der Kommentar ist damit
unvollständig, die Schleife selbst bleibt richtig, weil sie auf eine leere
Warteschlange wartet und nicht auf eine feste Zahl von Durchgängen.

**Gemessen:** Ein Lauf über die sieben Bilder des Referenzkorpus braucht mit
dieser Änderung zwei Durchgänge statt einem (Durchgang 1: sieben Übergaben,
Durchgang 2: sechs indexiert, eines übersprungen). Die Endverdikte sind
unverändert, die Zahlen `EXPECTED_INDEXED`/`EXPECTED_SKIPPED`/`EXPECTED_FAILED`
des Gates also auch.

**Warum nicht hier erledigt:** `.github/workflows/integration.yml` steht nicht
in `files_modified` dieses Plans, und mehrere andere Pläne dieser Phase fassen
genau diese Datei an (NC-Versionsmatrix aus D-07 und D-23, Paritätstest aus
D-21). Eine reine Kommentaränderung aus einem parallel laufenden Worktree wäre
ein Konflikt in einer Datei, deren eigentliche Änderung anderswo liegt.

**Wohin es gehört:** in den Plan, der die Matrix in `integration.yml` umbaut.

## DI-05-06: Der Live-Lauf des OCR-Anteils auf dem vollständigen Stack

**Found during:** Plan 05-04.

**Was:** Das Abnahmekriterium von Task 1 nennt einen Lauf über die Bilddateien
des Referenzkorpus auf dem lokalen Stack, mit dem OCR-Anteil in den Zählern des
Containers und der Nennung auf der Statusseite.

**Was stattdessen gemessen wurde:** derselbe Lauf mit der echten Engine
(tesseract 5.5.0) im Laufzeitimage, gegen einen echten Tantivy-Index und eine
echte Zustandsdatenbank, mit dem Produktions-Extraktor hinter der
Prozessgrenze; Nextcloud war dabei ein Skript. Ergebnis in der Zusammenfassung
des Plans: vorher `text=6, ocr=0`, nachher `text=0, ocr=6`, alle sieben Zeilen
mit `ocr_used=1`. Nicht abgedeckt bleibt allein die Darstellung: dass die
Statusseite diesen Anteil auch anzeigt.

**Warum nicht hier erledigt:** die Statusseite braucht den registrierten
ExApp-Container am laufenden Nextcloud. Der lokale Stack dieses Repositories
bindet die PHP-App aus dem Haupt-Checkout ein, den ein Wave-Executor nicht
anfassen darf, und die HaRP-Stacks der Nachbar-Wellen gehören anderen Agenten.

**Wohin es gehört:** in den phasenweiten Integrationsschritt beziehungsweise in
den Messbericht der Phase (D-06), der den OCR-Anteil ohnehin auf echter Hardware
ausweisen muss.

## DI-05-07: Der lokale HaRP-Stack hängt beim `--wait-finish`, aus demselben Grund wie CI

**Found during:** 05-08, beim ersten Lauf des Deploy-Jobs auf einem Runner.

**Was:** Das Feld `nextcloud_url` einer HaRP-Daemon-Registrierung wird von AppAPI
zweimal benutzt, und die beiden Verwendungen ziehen in verschiedene Richtungen.
`DockerActions::resolveExAppUrl` bildet daraus die Adresse der ExApp als
`{nextcloud_url}/exapps/{appId}`, muss also HaRP erreichen; derselbe Wert geht
als `NEXTCLOUD_URL` an den Container, muss also Nextcloud erreichen. HaRP
bedient ausschließlich Pfade, die `/exapps/{appId}` enthalten: der SPOE-Agent
prüft das mit einem regulären Ausdruck und weist alles andere mit "Invalid
request path, cannot find AppID" ab.

Folge: mit der HaRP-Adresse in diesem Feld kann der Container seinen
Init-Status nie melden. `PUT /ocs/v1.php/apps/app_api/ex-app/status` antwortet
404, und `occ app_api:app:register --wait-finish` wartet genau auf diesen Status
(`ExAppService::waitInitStepFinish` schleift, bis `init` 100 erreicht). Der
Befehl schreibt vorher `ExApp ... deployed successfully` und hängt danach,
während Container, Suche und Heartbeat gesund sind.

**Was in diesem Plan daraus wurde:** der CI-Job stellt die Topologie her, für die
HaRP gebaut ist. Ein nginx auf Port 8090 leitet `/exapps` an HaRP und alles
andere an Nextcloud, und `nextcloud_url` ist diese eine Adresse. Damit läuft
`--wait-finish` durch, gemessen über alle vier Serverversionen (Lauf
33757405755).

**Was offen bleibt:** `scripts/dev/compose-harp.yaml` und der zugehörige
Abschnitt in `docs/dev-setup.md` registrieren weiterhin `http://harp:8780` als
`nextcloud_url`. Der lokale Weg hat also dieselbe Lücke, und die Beschreibung in
`docs/dev-setup.md`, HaRP leite "alles außer /exapps an NC_INSTANCE_URL weiter",
ist so nicht richtig. Beides gehört zusammen korrigiert, entweder mit einem
Frontproxy-Dienst in der compose-Datei oder mit einem Nextcloud-Image, dessen
Apache `/exapps` weiterreicht. Beide Dateien gehören Plan 05-01 und liegen
außerhalb der `files_modified` dieses Plans, deshalb hier statt dort.

**Wer es außerdem braucht:** Plan 05-10 (ARM- und AIO-Lauf). All-in-one bringt
den Frontproxy von Haus aus mit, dort ist die Adresse für `nextcloud_url` also
die Adresse von Nextcloud hinter dem Apache und ausdrücklich nicht die von HaRP.
Diese Korrektur ersetzt die Verkürzung aus DI-05-03, die den Fall
"Container meldet sich zurück" noch nicht kannte.

## DI-05-08: Zwei Wahrheiten über das Verhältnis von Warteschlange und Statusseite

**Found during:** 05-08, beim Bau des Rückzugspfads im Poller.

**Was:** Der Poller kennt jetzt zwei Zählwerke für Wartezeiten, das gewöhnliche
für eine leere Warteschlange (15 bis 120 Sekunden) und den Rückzug für eine
Warteschlange, die nicht antwortet (15 bis 300 Sekunden). Die Statusseite aus
Phase 4 zeigt weder das eine noch das andere: Sie kann einem Admin also nicht
sagen, dass der Container sich gerade zurückgezogen hat und warum.

**Warum nicht hier erledigt:** `php/templates/admin.php`, `php/js/admin.js` und
`backend/src/findling/api/status.py` gehören anderen Plänen dieser Phase
(05-07 und 05-11), und ein neues Feld in `/status` ist eine Absprache zwischen
beiden Hälften und keine Zeile in einer Datei.

**Wohin es gehört:** in Plan 05-11, der die Statusseite ohnehin anfasst. Der
Rückzug ist im Protokoll des Containers sichtbar und in `docs/uninstall.md`
beschrieben; das ist die Untergrenze und nicht das Ziel.
