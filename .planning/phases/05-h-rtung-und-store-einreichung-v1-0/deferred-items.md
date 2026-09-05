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

## DI-05-07-A: `scripts/dev/compose.yaml` lässt sich aus einem Worktree nicht zweimal fahren

**Found during:** Plan 05-07, beim Live-Nachstellen der Versionsdrift.

**Was:** Die Datei trägt `name: findling-dev` und
`container_name: findling-nextcloud`, beide fest. Ein Wave-Executor, der den
Alltagsstack für seine eigene Änderung braucht, kann ihn deshalb nicht starten:
der Name kollidiert mit dem laufenden Stack des Haupt-Checkouts, und
`docker compose -f <worktree>/scripts/dev/compose.yaml exec app ...` landet
wegen des gleichen Projektnamens in genau diesem fremden Stack. Damit ist auch
`scripts/dev/register-exapp.sh` aus einem Worktree nicht als Ganzes ausführbar,
obwohl das Skript sonst nichts vom Haupt-Checkout braucht: sein `COMPOSE_FILE`
zeigt auf diese Datei.

**Was stattdessen gemacht wurde:** eine Wegwerf-Kopie der Compose-Datei im
Scratchpad mit eigenem Projektnamen, eigenem Containernamen, eigenem Port und
absolutem Bind auf das Worktree-`php`. Damit lief der volle Beweis (siehe
05-07-SUMMARY.md), und der Stack wurde danach mit `down -v` restlos entfernt.

**Warum nicht hier erledigt:** die Änderung wäre entweder ein Projektname aus
einer Umgebungsvariablen (dann verliert `register-exapp.sh` seinen festen
Containerbezug nicht, `container_name` müsste ebenfalls weichen) oder ein
zweites Compose-Profil. Beides fasst `scripts/dev/compose.yaml` an, die nicht in
`files_modified` dieses Plans steht, und der Alltagsstack des Owners läuft
gerade daraus.

**Wohin es gehört:** in einen Plan, der ohnehin an den Dev-Stacks arbeitet, oder
in den Phase-Review. Der billige Teil wäre `name: ${FINDLING_PROJECT:-findling-dev}`
plus ein Wegfall von `container_name`; `register-exapp.sh` adressiert den Dienst
ohnehin über `docker compose exec app`.

## DI-05-07-B: Die Versionsdrift wird erst nach dem ersten Blick auf die Statusseite wirksam

**Found during:** Plan 05-07, beim Entwurf der Suchseite der Lockstep-Prüfung.

**Was:** Die PHP-Hälfte erfährt die Version des Containers ausschließlich aus
`GET /status`, und diese Route ruft genau ein Ort auf: die Admin-Seite. Der
Suchweg liest deshalb den zuletzt gemerkten Wert aus appconfig
(`ExAppService::KEY_BACKEND_VERSION`), statt pro Tastendruck einen Roundtrip zu
bezahlen. Auf einer Instanz, auf der niemand die Einstellungsseite geöffnet hat,
steht dort nichts, und die Suche verhält sich wie vorher. Gemessen und in der
Zusammenfassung protokolliert: erste Suche vor jedem Statusabruf liefert den
Kanarienvogel-Treffer, nach dem ersten Seitenaufruf liefert dieselbe Suche 200
mit null Treffern und die Warnung im Log.

**Warum das kein Fehler ist:** die Alternative wäre entweder ein Statusabruf pro
Suche oder ein neuer Hintergrundauftrag. Das erste kostet einen Roundtrip pro
Tastendruck der Unified Search, das zweite ist ein Job mit eigenem Zeitplan für
eine Frage, die sich nur beim Update ändert. Fail-open ist außerdem die
richtige Richtung: eine Instanz ohne Kenntnis darf nicht schlechter suchen als
vorher (T-05-27).

**Wohin es gehört:** in den Plan, der den Poller oder den Scheduler dieser
Hälfte anfasst. Ein Satz im `SchedulerJob`, der den Statusabruf einmal pro
Cron-Runde mitnimmt, würde die Lücke ohne neuen Job schließen. Bis dahin ist die
Statusseite der Weg, auf dem ein Admin den Zustand ohnehin sucht.
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

## DI-05-10 (in 05-09-SUMMARY.md als DI-05-07 gefuehrt): Der CI-Lauf des Jobs `search-parity` ist noch nicht gesehen worden

**Found during:** Plan 05-09, beim letzten Abnahmekriterium von Task 2 und
Task 3.

**Was:** Beide Kriterien verlangen einen grünen Lauf des neuen Jobs auf einem
GitHub-Runner. Das ist aus dem Ausführungs-Worktree aus denselben zwei Gründen
nicht möglich wie bei DI-05-01: der Zweig `worktree-agent-05-09` existiert nur
lokal, und `workflow_dispatch` bietet nur Workflows des Vorgabezweigs an.

**Was stattdessen belegt ist.** Die Datei lädt als YAML, jeder einzelne
`run`-Block des Jobs ist mit `bash -n` syntaktisch geprüft, die per Here-Dokument
erzeugte `parity.sh` wurde materialisiert und ebenfalls geprüft, und die beiden
Funktionen, auf denen alles ruht, sind gegen einen curl-Ersatz durchgespielt
worden: eine Paritätsverletzung bricht den Schritt mit Exitcode 1 ab, eine
Übereinstimmung nicht. Der Negativprobe-Schritt wurde vollständig ausgeführt
(echtes `jq`, echtes `parity_diff.py`) und meldet beide Richtungen; zusätzlich
wurde belegt, dass er selbst rot wird, wenn `parity_diff` grün bliebe.

**Was offen bleibt.** Genau die Teile, die kein lokales Gegenstück haben: dass
`occ app:install groupfolders` auf dem Runner durchgeht (sonst greift der
Tarball-Zweig, und welcher Weg genommen wurde, steht im Log), dass
`occ config:app:set core unified_search_max_results_per_request --type=integer`
auf stable34 die Option kennt, und die tatsächlichen Trefferzahlen der sechs
Szenarien. Der Workflow hat Push-Trigger auf `scripts/ci/**`, `php/**`,
`backend/**` und seinen eigenen Pfad, der erste Lauf passiert also nach dem
Merge von selbst und muss angesehen werden.

## DI-05-11 (in 05-09-SUMMARY.md als DI-05-08 gefuehrt): Ein Gruppenwechsel erreicht den ACL-Vorfilter erst über den nächsten Crawl

**Found during:** Plan 05-09, beim Bau von Szenario 5.

**Was:** Der Plan nimmt an, das Vorfilter-Update nach einem Gruppenwechsel komme
über die Share-Ereignisse und den Teilbaum-Job. Das ist nicht so, und
`ShareEventListener` sagt es in seinem eigenen Klassenkommentar: die drei
abonnierten Ereignisse sind `ShareCreatedEvent`, `ShareDeletedEvent` und
`ShareDeletedFromSelfEvent`, und keines davon feuert, wenn ein Nutzer eine
Gruppe verlässt, weil sich der Share selbst nicht geändert hat. Es gibt also
keinen Teilbaum-Job, den man anstoßen könnte.

**Warum das kein Sicherheitsbefund ist:** die Sicherheitsgrenze ist der Recheck
in `Provider`, der jeden Kandidaten über `getUserFolder()->getFirstNodeById()`
auflöst. Ein veralteter Vorfilter kostet Ergebnisqualität und Rechenzeit, nicht
Vertraulichkeit. Genau das misst Szenario 5 jetzt ausdrücklich: die erste
Vergleichsfrage wird gestellt, während der Vorfilter den entfernten Nutzer noch
führt, und die Parität hält.

**Was offen bleibt:** ein Nutzer, der einer Gruppe BEITRITT, findet die Inhalte
der Gruppe erst nach dem nächsten Crawl beziehungsweise nachdem eine
Inhaltsaufgabe die Datei ohnehin angefasst hat. Der Klassenkommentar nennt den
ETag-Abgleich als Träger; der Abgleich wird aber über eine geänderte ETag
ausgelöst, und eine Mitgliedschaft ändert keine. Die billige Behebung wäre ein
Listener auf `OCP\Group\Events\UserAddedEvent` und `UserRemovedEvent`, der die
Mounts der Gruppe als `acl`-Teilbäume einreiht. Das ist ein neuer Listener und
gehört in einen eigenen Plan.

**Wohin es gehört:** in den Phase-Review oder in einen Folgeplan, der an der
Ereigniskette arbeitet.

## DI-05-12 (in 05-09-SUMMARY.md als DI-05-09 gefuehrt): `.gitattributes` führt `*.py` nicht, und CI-Skripte tragen eine Shebang

**Found during:** Plan 05-09, beim Anlegen von `scripts/ci/parity_diff.py`.

**Was:** `.gitattributes` erzwingt `eol=lf` für `*.sh`, `*.yml`, `*.yaml`,
`*.conf`, `Dockerfile` und `.dockerignore`, nicht aber für `*.py`. Auf der
Entwicklungsmaschine ist `core.autocrlf` an, also liegen `slow_backend.py` und
jetzt auch `parity_diff.py` mit CRLF im Arbeitsbaum. Beide tragen eine
Shebang-Zeile.

**Warum es heute nichts kaputt macht:** beide werden als `python3 <datei>`
aufgerufen, und Python liest universelle Zeilenenden. Erst ein direkter Aufruf
über die Shebang (`./scripts/ci/parity_diff.py`) würde am Wagenrücklauf hinter
`python3` scheitern, mit genau der Fehlermeldung, die die Kopfzeile von
`.gitattributes` beschreibt.

**Warum nicht hier erledigt:** `.gitattributes` steht nicht in `files_modified`
dieses Plans, die Datei ist gemeinsames Gut mehrerer Pläne dieser Phase, und die
Änderung würde die Zeilenenden aller Python-Dateien des Repositories in einem
Commit umschreiben.

**Wohin es gehört:** in einen Plan, der ohnehin an der Werkzeugkette arbeitet,
oder in den Phase-Review. Eine Zeile `*.py text eol=lf` genügt.

## DI-05-13 (Plan 05-11): Der Rückzug des Pollers bleibt für die Statusseite unsichtbar, und zwar aus einem neuen Grund

**Found during:** Plan 05-11, bei der Prüfung von DI-05-08, das ausdrücklich an
diesen Plan adressiert war.

**Was DI-05-08 verlangt:** Die Statusseite soll zeigen, dass der Container sich
von einer Warteschlange zurückgezogen hat, die nicht antwortet, und warum.

**Warum es hier nicht erledigt wurde, mit einem Argument, das DI-05-08 noch nicht
kannte.** Der Hauptfall, für den der Rückzug gebaut ist, ist die halb entfernte
Installation aus D-17: die Nextcloud-Hälfte ist weg, der Container läuft weiter.
In genau diesem Fall gibt es keine Statusseite mehr, auf der ein Banner stehen
könnte, denn die Seite ist Teil der entfernten App. Der Rückzug wäre also
sichtbar in allen Fällen ausser dem, für den er existiert.

Es bleibt ein zweiter, kleinerer Fall: die App ist installiert, die Seite
rendert, und die Queue-Aufrufe scheitern trotzdem, etwa nach einer
Secret-Rotation von AppAPI oder bei einem Datenbankfehler. Dort wäre die Anzeige
echten Wert wert, weil die Seite heute nur "Die Indexierung kommt seit %s nicht
voran" sagt und damit die Hintergrundaufträge beschuldigt, die in Ordnung sind.

**Was dafür nötig wäre, und warum es nicht in diesen Plan passt.** Ein neues Feld
in `GET /status`, also `backend/src/findling/api/status.py`, die nicht in den
`files_modified` dieses Plans steht. Dazu kommt, dass `status.report()` heute
eine reine Funktion des Datenträgers und der Zustandsdatenbank ist und den Poller
gar nicht kennt: die beiden Zähler des Rückzugs liegen auf dem Poller-Objekt, das
`findling.main` hält, und `main` importiert den Status-Router, nicht umgekehrt.
Das ist keine Zeile, sondern eine Entscheidung darüber, wie Laufzeitzustand des
Pollers in eine Antwort kommt, die bisher nur Persistiertes meldet.

**Wohin es gehört:** in einen Plan, der `status.py` ohnehin anfasst, oder in den
Phase-Review. Die billigste ehrliche Form wäre ein Feld `queueUnansweredRounds`
neben `lowDisk`, gespeist aus dem Poller über einen Zugriff wie
`active_poller()`, plus ein weiterer Eintrag in der Bannerliste aus Plan 04-03.
Bis dahin steht der Rückzug im Protokoll des Containers und in
`docs/uninstall.md`.

## DI-05-14 (Plan 05-11): Ein Verdikt in `findling_file_state` wird nie zurückgenommen

**Found during:** Plan 05-11, beim Bau des Skip-Kanals.

**Was:** `FileStateService::record` schreibt genau eine Zeile je Datei und
überschreibt sie, wenn ein neues Verdikt kommt. Ein Verdikt zu LÖSCHEN kann
niemand. Wird eine Datei erst als `failed` oder `skipped` beurteilt und später
erfolgreich indexiert, bleibt die alte Zeile stehen: `indexed` ist die Zahl des
Containers und wird in diese Tabelle grundsätzlich nicht geschrieben, also gibt
es kein Verdikt, das die alte Zeile ersetzen könnte. Die Datei erscheint dauerhaft
in der Fehlerliste, obwohl sie durchsuchbar ist.

**Wie alt der Befund ist:** älter als dieser Plan. Er gilt seit Phase 2 für alle
`failed`-Gründe, etwa `timeout` und `gateway_error`, die beim nächsten Lauf
gutgehen. Dieser Plan verbreitert ihn um die `skipped`-Gründe des Containers.

**Was dieser Plan dagegen getan hat:** den einen Fall ausgeschlossen, in dem die
Veralterung nicht die Ausnahme, sondern der Normalfall wäre. Eine Datei, die an
die OCR-Spur übergeben wird, meldet kein Verdikt; sonst stünde jeder Scan der
Instanz dauerhaft unter "Kein Text im Dokument". Gemessen und in
05-11-SUMMARY.md protokolliert: nach einem Lauf über das Referenzkorpus gibt es
keine Gruppe `no_text_layer`.

**Warum nicht hier behoben:** Die Behebung ist eine dritte Liste in der
Quittierung, in der der Container die Dateien nennt, die er in diesem Durchgang
als indexiert beurteilt hat, damit die andere Hälfte deren Zeile löscht. Das ist
eine Erweiterung des Protokolls zwischen beiden Hälften und keine Zeile in einer
Datei, und der Plan nennt ausdrücklich eine zweite Liste. Aus der Zahl `done`
lässt sich das NICHT ableiten: dort stehen auch `acl`- und `delete`-Aufträge, die
über den Inhalt einer Datei nichts aussagen, und ein Löschen auf dieser Grundlage
würde ein gültiges Verdikt wegen einer Rechteänderung verwerfen.

**Wohin es gehört:** in den Phase-Review oder in einen Folgeplan, der an der
Quittierung arbeitet. Bis dahin räumt ein `occ findling:index --restart` auf,
weil der Neuaufbau jede Datei neu beurteilt.

## DI-05-16: Die Provenance des veroeffentlichten Images ist unsigniert

**Found during:** Plan 05-13, bei der Beantwortung von Sec-L9.

**Was:** Der veroeffentlichte Index von
`ghcr.io/street1983nk/findling_backend:dev` traegt je Plattform eine
Provenance-Bescheinigung, das ist am 03.09.2026 gegen die Registry geprueft und
seit diesem Plan ein Gate im merge-Job von `docker.yml`. Inhalt: eine
in-toto-Aussage mit `predicateType https://slsa.dev/provenance/v1`, erzeugt von
buildkit, mit Quellrepository, Commit und den aufgeloesten Digests der
Basisimages. Das ist ein Pruefpfad und keine Unterschrift. `gh attestation
verify` kann sie nicht pruefen, weil dieser Befehl eine GitHub Artifact
Attestation erwartet, also `actions/attest-build-provenance` mit
`id-token: write`, und diesen Schritt gibt es in `docker.yml` nicht.

**Warum das nicht hier erledigt wurde:** Eine echte Signatur ist keine Zeile.
Sie braucht `id-token: write` in einem Workflow, der heute ausdruecklich nur
`contents: read` und `packages: write` fuehrt und dessen Kommentar diese
Sparsamkeit begruendet, sie braucht eine Aussage darueber, was ein Nutzer damit
prueft und wo diese Anleitung steht, und sie beruehrt den Veroeffentlichungsweg,
der in dieser Phase ohnehin noch von der Release-Arbeit angefasst wird.

**Wohin es gehoert:** in den Plan, der den Release-Weg besitzt (Tag `v1.0.0`,
D-26), oder in den Phase-Review. Der Umfang: ein Schritt
`actions/attest-build-provenance` im merge-Job, `id-token: write` in den
Berechtigungen, und ein Absatz in der Doku, der den Pruefbefehl nennt. Bis dahin
gilt die Aussage der Datei genau so, wie sie dort steht.

## DI-05-10 ist beantwortet (aus Plan 05-13)

Der ausstehende CI-Lauf des Jobs `search-parity` aus DI-05-10 ist gesehen: Lauf
33766125632 auf dem Zweig `worktree-agent-05-13`, gruen in 5,6 Minuten, und
derselbe Job war schon im Lauf 33761279279 auf `main` gruen. Damit sind auch die
drei dort offen gebliebenen Teile beantwortet: `occ app:install groupfolders`
geht auf dem Runner durch, `occ config:app:set core
unified_search_max_results_per_request --type=integer` kennt die Option auf
stable34, und die sechs Szenarien liefern ihre Trefferzahlen. Der Eintrag oben
bleibt als Fundstelle stehen, dieser Absatz ist seine Erledigung.

## DI-05-17 (Plan 05-15): Die Unit-Suite laeuft nur gegen eine der vier Serverversionen

**Found during:** Plan 05-15, beim Zuschnitt des Jobs `phpunit`.

**Was:** Der neue Job checkt `stable34` aus, weil der Plan "denselben Zweig, den
die Integrationsjobs benutzen" vorgibt und weil die PHPUnit-Hauptversion daran
haengt: `nextcloud/server` fuehrt `phpunit/phpunit ^11.5` in
`vendor-bin/phpunit/composer.json` auf `stable34` und `^10.5.35` auf `stable32`.
Die uebrigen Gates dieser Phase fahren dagegen eine Matrix ueber 32, 33, 34 und
35 (D-07, D-23). Die Unit-Suite prueft also gegen genau eine der vier
Schnittstellenversionen.

**Warum das heute nicht viel kostet:** Die Suite mockt Schnittstellen und ruft
keine Serverimplementierung. Was zwischen zwei Serverversionen abweichen kann,
ist die Signatur einer gemockten Methode, etwa `Folder::getFirstNodeById` oder
`IUserMountCache::getMountsForUser`. Eine Signaturaenderung faellt heute in den
Integrationsjobs auf, allerdings erst dort und nicht in Sekunden.

**Warum nicht hier erledigt:** Eine Matrix ueber vier Serverversionen bedeutet
vier PHPUnit-Hauptversionen, denn die Bindung an das Bootstrap des Servers ist
genau der Grund, aus dem die Version nicht frei gewaehlt wird. Ein
`composer.lock` je Serverzweig oder eine Aufloesung ohne Lockdatei im Job ist
eine Entscheidung ueber die Bezugsdisziplin dieses Projekts und keine Zeile in
einer Datei; der Paketbezug selbst steht unter einem Owner-Gate.

**Wohin es gehoert:** in Plan 05-16, der die Suite ohnehin verbreitert, oder in
den Phase-Review. Der billige Zwischenschritt waere ein zweiter Job auf
`stable32` mit PHPUnit 10 und einem eigenen Lockfile, und die ehrliche Frage
davor ist, ob eine Signaturabweichung in OCP innerhalb eines
Nextcloud-Versionsfensters ueberhaupt vorkommt.

## DI-05-18 (Plan 05-16): DI-05-17 bleibt offen, aber die ehrliche Frage davor ist beantwortet

**Found during:** Plan 05-16, bei der Pruefung von DI-05-17, das ausdruecklich an
diesen Plan adressiert war.

**Was DI-05-17 verlangt:** eine Matrix der Unit-Suite ueber `stable32` bis
`stable35`, weil die uebrigen Gates dieser Phase eine fahren und die Suite nur
gegen `stable34` laeuft.

**Was hier stattdessen gemessen wurde.** DI-05-17 nennt selbst eine Vorfrage:
kommt eine Signaturabweichung in OCP innerhalb des Versionsfensters ueberhaupt
vor. Fuer die Schnittstellen, die diese Suite tatsaechlich doppelt, ist sie am
03.09.2026 gegen alle vier Zweige von `nextcloud/server` erhoben und lautet
nein. Identisch auf 32, 33, 34 und 35:

| Datei | Signatur |
|---|---|
| `lib/public/Files/Folder.php` | `getFirstNodeById(int $id): ?Node` |
| `lib/public/Files/Config/IUserMountCache.php` | `getMountsForUser(IUser $user)` |
| `lib/public/Http/Client/IResponse.php` | `getBody()`, `getStatusCode(): int` |
| `lib/public/Files/Cache/IFileAccess.php` | `getByFileIds(array $fileIds): array` |

Das ist kein Beweis fuer die Zukunft, aber es ist die Antwort auf die Frage, die
DI-05-17 stellt: der heutige Nutzen einer vierfachen Suite waere null, und der
Preis waeren vier PHPUnit-Hauptversionen und vier Lockdateien.

**Warum nicht hier erledigt:** unveraendert der Grund aus DI-05-17, und dieser
Plan bringt keinen neuen. Ein zweiter Lauf auf `stable32` braucht PHPUnit 10 als
zweite gepinnte Abhaengigkeit, und ein Paketbezug steht in dieser Phase unter
einem Owner-Gate (siehe 05-15-SUMMARY.md). Das ist eine Entscheidung ueber die
Bezugsdisziplin und keine Zeile in einer Datei, und sie gehoert nicht in einen
Plan, dessen Gegenstand sechs Verhaltensweisen sind.

**Wohin es gehoert:** in den Phase-Review. Die Tabelle oben ist das Material fuer
die Entscheidung; wer sie trifft, sollte sie fuer die dann gedoppelten
Schnittstellen erneut erheben, weil diese Suite seit 05-16 auch `IRequest` und
`File::fopen` doppelt.

## DI-05-19 (in 05-10-SUMMARY.md als DI-05-07 gefuehrt): Zwei Doku-Seiten sollten auf `docs/performance.md` verweisen

**Found during:** Plan 05-10, beim Anlegen des Messberichts.

**Was:** `docs/admin-page.md` (Zeile 219) begründet eine Schätzung mit einem
amd64-Laptopkern und sagt dazu "die Zielhardware ist eine ARM-Box"; genau diese
Box ist ab jetzt in `docs/performance.md` beschrieben. `docs/ocr.md` verweist im
Abschnitt "Was diese Seite nicht misst" auf Messungen, die der Volllauf liefern
wird. Beide Stellen gewinnen durch einen Einzeiler auf den neuen Bericht.

**Warum nicht hier erledigt:** keine der beiden Dateien steht in
`files_modified` von 05-10, beide werden in dieser Phase von anderen Plänen
angefasst, und ein Querverweis aus einem parallel laufenden Worktree wäre ein
Konflikt in einer Datei, deren eigentliche Änderung anderswo liegt. Außerdem
lohnt der Verweis erst, wenn der Bericht Zahlen trägt und nicht nur seine
Methode.

**Wohin es gehört:** in den Plan, der den Volllauf auswertet (05-14), oder in
den Phase-Review.

## DI-05-20: Ein Mount, den es beim ersten Durchgang noch nicht gab, fehlt im Nenner des Deckungsgrads

**Found during:** Plan 05-12, Task 1, auf der Box.

**Was:** Der erste Durchgang schreibt je Mount eine Zeile in
`oc_findling_scan_stats`, und der Deckungsgrad bildet seinen Nenner aus genau
diesen Zeilen. Ein Nutzer, der nach dem Durchgang angelegt wird, bekommt keine
Zeile. Seine Dateien kommen ueber den Vergleichslauf trotzdem in den Index, also
waechst der Zaehler, waehrend der Nenner steht. Gemessen auf der Box: 88
indexierte Dokumente gegen 49 indexierbare, angezeigt als hundert Prozent, weil
die Kachel deckelt. Nach `occ findling:index --restart -n` stimmen beide Zahlen
(88 von 104, 84 Prozent).

**Warum nicht hier erledigt:** Der Zustand heilt von selbst, spaetestens mit dem
naechtlichen Vergleich, und er verfaelscht keine Messung dieses Plans. Die
Abhilfe waere dagegen eine Aenderung an der Frage, welche Mounts der Nenner
zaehlt, also am Deckungsgrad selbst: entweder legt der Vergleichslauf die fehlende
Zeile an, oder der Nenner kommt nicht mehr aus `scan_stats`, sondern aus der
Mount-Liste. Beides ist eine Entscheidung ueber die Bedeutung der Kachel und
keine Zeile in einer Datei, also Rule 4 und nicht Rule 1.

**Wohin es gehoert:** in den Phase-Review, zusammen mit der Frage, ob ein
Deckungsgrad ueber hundert Prozent lieber sichtbar sein sollte als gedeckelt: die
gedeckelten hundert Prozent sind die einzige Anzeige, die aussieht wie ein
fertiger Index, obwohl gerade ein Mount fehlt.

## DI-05-21: Ein Fehlschlag bleibt in der Fehlerliste stehen, auch wenn die Datei danach indexiert wird

**Found during:** Plan 05-12, Task 2, auf der Box, nach der Korrektur des
xlsx-Befunds.

**Was:** `QueueService::acknowledge()` schreibt Zeilen in
`oc_findling_file_state` nur fuer Fehlschlaege und fuer Uebersprungene. Die
erfolgreich indexierten Dateien reisen in `$queueIds` und schreiben dort
bewusst nichts, weil das Endverdikt "indexiert" der Container zaehlt. Also
raeumen sie auch ihre alte Zeile nicht weg. Gemessen: nach der Korrektur meldet
der Container 587 indexiert und 0 fehlgeschlagen, waehrend die Nextcloud-Seite
weiterhin 32 `failed(corrupt)` fuehrt und `occ findling:diagnose` fuer eine
dieser Dateien "Datei beschaedigt" nennt, obwohl dieselbe Datei ueber die Suche
zu finden ist.

**Warum nicht hier erledigt:** Die Abhilfe ist keine Zeile, sondern eine
Entscheidung darueber, was die Zustandstabelle bedeutet. Loescht die
Quittierung die Zeilen der Dateien in `$queueIds`, dann ist die Fehlerliste
immer der aktuelle Stand, aber die Nextcloud-Seite verliert die Spur eines
Fehlschlags, der sich beim naechsten Versuch wiederholt, und die Aufgeben-Regel
nach drei Versuchen haengt an genau dieser Spur. Bleibt es, wie es ist, ist die
Liste nach jeder erfolgreichen Wiederholung falsch. Dazu kommt, dass die
Zustandstabelle keinen Zeitstempel des Verdikts fuehrt, an dem sich "alt"
ablesen liesse. Das ist Rule 4 und nicht Rule 1, und es beruehrt PHP-Seite,
Container-Vertrag und die Anzeige zugleich.

**Wohin es gehoert:** in den Phase-Review, und zwar vor dem Volllauf in 05-14
zur Kenntnis: der Volllauf sollte auf einer geraeumten Zustandstabelle starten,
sonst traegt sein Fehlerbericht die 32 Zeilen dieses Trockenlaufs weiter, obwohl
die Dateien indexiert sind.

**Erledigt fuer den Volllauf:** Plan 05-14 hat die drei Tabellen vor dem Lauf
geraeumt (`TRUNCATE oc_findling_queue, oc_findling_file_state,
oc_findling_scan_stats`) und den Datenspeicher der ExApp mit `--rm-data`
geloescht. Der Befund selbst bleibt offen, siehe DI-05-23, der ihn von einer
anderen Seite trifft.

## DI-05-22: Die Statusseite sagt acht Stunden lang "kommt nicht voran", waehrend sie 6.500 Dokumente indexiert

**Found during:** Plan 05-14, im Volllauf ueber 50.000 Dateien auf der Box.

**Was:** `AdminViewService::runState` liest `stalled`, wenn Arbeit wartet und der
letzte Hintergrundauftrag DIESER App laenger als `STALLED_AFTER_SECONDS` (1800)
zurueckliegt. Die Seite zeigt dann "Indexing has not progressed for %s. Background
jobs may not be running."

Im Volllauf war der Crawl um 2026-09-04T01:30:49Z fertig, danach hatte diese App
keinen Hintergrundauftrag mehr auszufuehren, und der Zeitstempel stand still. Der
Container arbeitete bis 09:27:25Z weiter und indexierte in dieser Zeit rund 6.500
Dokumente, quittiert aber ueber OCS und nicht ueber einen Hintergrundauftrag. Von
02:01Z bis 09:27Z, also **acht Stunden und ueber die Mehrheit der Laufzeit**, stand
`runState` auf `stalled` und `stalledFor` wuchs auf ueber 30.000 Sekunden, waehrend
der Deckungsgrad in derselben Reihe von 82 auf 99 Prozent stieg. Belegt in
`docs/measurements/2026-09-04-volllauf-cpx22/statusseite.csv`, 130 Aufnahmen.

**Warum es auf einer gewoehnlichen Instanz nicht auffaellt:** dort enden Crawl und
Inhaltsarbeit ungefaehr gleichzeitig. Der Fall entsteht erst, wenn der
OCR-Nachlauf laenger ist als der Crawl, und das ist genau das Lastprofil der
Zielhardware: 20 Prozent Scans auf einer 4-GB-Box machen den Nachlauf zu 77
Prozent der Laufzeit.

**Warum nicht hier behoben:** die Abhilfe ist eine Entscheidung darueber, welche
Groesse `stalled` messen soll. Der Fortschritt der Warteschlange waere die
naheliegende Antwort (ein Zaehler, der sich seit einer halben Stunde nicht bewegt
hat), aber damit misst die Kachel nicht mehr das, was ihr Text behauptet, naemlich
die Hintergrundauftraege. Beides zugleich zu sagen braucht ein zweites Feld und
einen zweiten Satz. Das beruehrt `AdminViewService`, den Text der Seite und die
Bannerliste aus Plan 04-03, also drei Orte und keine Zeile.

**Wohin es gehoert:** in den angekuendigten Fix-Plan dieser Phase, vor 05-17 und
vor dem ARM-Volllauf, damit der ARM-Lauf das korrigierte Verhalten prueft. Der
billige Zwischenschritt waere, den Vergleichslauf so zu planen, dass er auch
waehrend eines langen OCR-Nachlaufs regelmaessig laeuft, denn dann bewegt sich
`lastJobRun` wieder und die Regel stimmt von selbst.

## DI-05-23: Eine kurze Plattenknappheit schreibt den gesamten Vorrat ab, der gerade unterwegs ist

**Found during:** Plan 05-14, Stoerfall-Drill 3 auf der Box, in zwei unabhaengigen
Durchgaengen.

**Was:** Wird der freie Platz unter `MIN_FREE_BYTES` (500 MB) gedrueckt, pausiert
der Container richtigerweise und gibt seine Ladung unbeurteilt zurueck ("index
paused, free space below the floor, N rows handed back"). Die Nextcloud-Seite
zaehlt aber die Wiederholung **bei der Ausgabe** hoch, nicht beim Fehlschlag:
`QueueMapper` schreibt `retries + 1` beim Holen, mit dem Kommentar "Handing a row
out is the attempt, so retries is counted here". Ein Durchgang des Pollers dauert
wenige Sekunden, `QueueService::MAX_DELIVERIES` steht auf 3, also ist das
Wiederholungsbudget einer Zeile nach rund zwanzig Sekunden Plattenknappheit
aufgebraucht. Danach schreibt `QueueService` sie als `failed(repeatedly_stuck)` ab
und gibt sie nicht mehr aus.

**Gemessen, zweimal, mit demselben Verhaeltnis:**

| Durchgang | Zeilen beim Arbeiter, als die Platte knapp wurde | Dauer der Pause | abgeschrieben |
|---|---|---|---|
| 1 (2026-09-04T10:15:41Z) | 2 | 3 min 25 s | 2 |
| 2 (2026-09-04T11:13:25Z) | 30 | 1 min 38 s | 30 |

Im zweiten Durchgang waren 60 Dateien hochgeladen worden: 30 wurden indexiert, 28
nie an den Container uebergeben und als `repeatedly_stuck` abgeschrieben, 2 blieben
im Container auf `skipped(no_text_layer)` stehen, weil ihr Inhaltsverdikt schon
geschrieben war und die Quittierung, aus der der OCR-Auftrag entstanden waere,
nicht mehr kam.

**Warum das mehr ist als eine Unschoenheit:** die Oberflaeche sagt in derselben
Minute "Little disk space left. Indexing is paused so the index stays intact."
Der Index bleibt tatsaechlich heil und die Suche laeuft weiter, das ist in
demselben Drill belegt. Der Arbeitsvorrat bleibt aber nicht heil, und genau davon
sagt das Banner nichts. Auf einer 4-GB-Box mit einem knappen Datentraeger, also
der Zielumgebung dieses Produkts, ist eine halbe Minute Knappheit kein
Ausnahmefall.

**Was den Schaden begrenzt:** die Dateien sind nicht unbemerkt weg. Sie stehen
namentlich in der Fehlerliste der Verwaltungsseite, `occ findling:diagnose` nennt
sie, und `occ findling:index --restart` faengt sie wieder ein. Der naechtliche
Vergleich holt sie ausdruecklich NICHT zurueck: `repeatedly_stuck` ist genau das
Verdikt, mit dem eine aufgegebene Datei vom Vergleich ausgenommen wird
(`ReconcileController`, IN-03 aus Phase 3).

**Was ausdruecklich NICHT die Ursache ist:** der `docker kill` aus Drill 1. Sein
Verdacht lag naeher, weil er zeitlich davorlag, und er ist entlastet: seine 13
unterwegs befindlichen Zeilen kamen entweder ueber die gewoehnliche Wiederholung
zurueck oder, im Fall der beiden OCR-Auftraege, nach dem Ablauf ihrer
1800-Sekunden-Sperre. Der Abschuss hat keine einzige Datei gekostet.

**Warum nicht hier behoben:** die Abhilfe ist keine Zeile und sie beruehrt beide
Haelften. Drei Wege sind denkbar, und die Wahl ist eine Entscheidung ueber die
Bedeutung von `retries`:

1. Eine Rueckgabe wegen Plattenknappheit belastet die Wiederholung nicht. Dann
   braucht die Quittierung einen dritten Kanal neben Fehlschlag und
   Uebersprungenem, denn heute kann der Container "ich habe gar nicht erst
   angefangen" nicht sagen.
2. Der Poller holt nichts, solange die Platte knapp ist. Dann muss er das vor dem
   Holen wissen, und heute merkt er es erst beim Schreiben.
3. `MAX_DELIVERIES` zaehlt Zeit statt Ausgaben. Dann verliert die Aufgeben-Regel
   ihre einfache Bedeutung.

**Wohin es gehoert:** in den angekuendigten Fix-Plan dieser Phase, vor 05-17 und
vor dem ARM-Volllauf, damit der ARM-Lauf das korrigierte Verhalten prueft. Er
gehoert zusammen mit DI-05-21 entschieden, weil beide an
`QueueService::acknowledge` und an der Frage haengen, was eine Zeile in der
Zustandstabelle bedeutet.

## DI-05-24 (Plan 05-17): `docs/testing.md` kennt das neue Store-Gate noch nicht

**Found during:** Plan 05-17, beim Bau von `backend/tests/test_store_metadata.py`.

**Was:** `docs/testing.md` fuehrt im Abschnitt "Die textuellen Gates ueber die
PHP-Quellen" eine Tabelle, in der jedes Gate mit dem Satz steht, was es
verhindert. Das neue Gate ueber die Store-Texte steht dort nicht, und
`docs/store-listing.md` wird in der Doku dieses Repositories bisher von keiner
Seite verlinkt. Beides zusammen heisst: wer die Gate-Landschaft ueber die
Dokumentation kennenlernt, erfaehrt weder von der Nachzieh-Regel noch von dem
Ort, an dem die drei Sprachfassungen nebeneinander stehen.

**Warum nicht hier erledigt:** `docs/testing.md` steht nicht in den
`files_modified` dieses Plans, und ein paralleler Ausfuehrer arbeitet in
derselben Welle an anderen Dateien; eine Zeile in einer fremden Datei aus einem
Worktree ist genau die Art Konflikt, die diese Liste vermeiden soll.

**Wohin es gehoert:** in den Plan, der `docs/testing.md` ohnehin anfasst, oder in
den Phase-Review. Der Umfang: eine Tabellenzeile fuer
`test_store_metadata.py` und ein Verweis auf `docs/store-listing.md` in der
Doku-Uebersicht.

## DI-05-25 (Plan 05-17): Der Store-Validierungspfad hat kein lokales Werkzeug

**Found during:** Plan 05-17, beim Nachfahren der XSD-Pruefung vor dem Commit.

**Was:** `.github/workflows/php.yml` prueft beide `info.xml` mit `xsltproc` und
`xmllint` gegen die unter `APPSTORE_SHA` gepinnte Fassung von `pre-info.xslt`
und `info.xsd`. Auf der Entwicklungsmaschine gibt es keines der beiden
Werkzeuge, und es gibt im Repository kein Skript, das den Pfad ersatzweise
faehrt. Ein Schema-Fehler faellt damit fruehestens auf dem Runner auf, und bei
der Einreichung waere er teuer.

**Was stattdessen gemacht wurde:** ein Wegwerf-Abbild aus `php:8.2-cli` mit
`xsltproc` und `libxml2-utils`, dazu die beiden gepinnten Dateien im
Scratchpad geholt. Damit lief der volle Pfad lokal, fuer beide Dateien, mit dem
Ergebnis `validates`. Das Abbild ist nicht Teil des Repositories und ueberlebt
diesen Plan nicht.

**Warum nicht hier erledigt:** ein Skript unter `scripts/dev/` waere eine neue
Datei ausserhalb der `files_modified` dieses Plans, und die Frage, ob es ein
Container-Aufruf oder eine Abhaengigkeit sein soll, beruehrt die
Bezugsdisziplin, die in dieser Phase unter einem Owner-Gate steht.

**Wohin es gehoert:** in den Plan, der die Release-Artefakte baut (D-26), oder in
den Phase-Review. Der billige Weg: `scripts/dev/validate-info-xml.sh`, das die
beiden gepinnten Dateien holt und den Pfad in einem Container faehrt, plus eine
Zeile in `docs/testing.md`.

**Behoben in Plan 05-20**, in beiden Haelften und auf zwei Wegen: `unlock` gibt
die Auslieferung zurueck, damit eine Pause den Vorrat gar nicht erst kostet, und
der naechtliche Abgleich holt das Paar `skipped(no_text_layer)` plus
`failed(repeatedly_stuck)` zurueck, damit die Dateien, die vor dem Fix gestrandet
sind, nicht liegen bleiben. Der Eintrag oben bleibt als Fundstelle stehen. Was
DI-05-21 offen laesst, bleibt offen und steht jetzt als DI-05-28 unten.

## DI-05-27 (Plan 05-20): Die Rueckgabe der Auslieferung ist nirgends gegen eine echte Datenbank geprueft

**Found during:** Plan 05-20, Task 1, beim Bau des Gates zu DI-05-23.

**Was:** Der Fix ist eine SQL-Anweisung, `retries - 1` mit einer WHERE-Grenze
gegen negative Werte, und geprueft wird er von zwei Seiten, die beide keine
Datenbank anfassen. `backend/tests/test_poller.py` stellt den Vorrat als
Zustandsautomat nach und liest die Regel dabei aus dem PHP-Quelltext, und ein
Textgate haelt die Anweisung selbst. Was keiner von beiden sieht: ob die
Anweisung auf SQLite, MariaDB und PostgreSQL dasselbe tut. Das ist genau die
Frage, wegen der die Grenze eine WHERE-Bedingung ist und kein `GREATEST`.

**Warum nicht hier erledigt:** Die PHPUnit-Suite dieses Projekts arbeitet mit
Doubles und laeuft ausdruecklich nur in CI (docs/testing.md und der Kommentar
des Jobs `phpunit`), auf der Entwicklungsmaschine gibt es kein PHP. Ein Test des
Query Builders waere ein Mock des Query Builders und wuerde die eigene
Nachbildung pruefen; ein Test gegen eine echte Datenbank ist ein
Integrationsjob und keine Zeile in einer Datei.

**Wohin es gehoert:** in den ARM-Volllauf, der ohnehin das korrigierte Verhalten
validieren soll, und in den Integrationsjob. Die billigste Form dort: die Platte
knapp machen, dreissig Zeilen unterwegs, danach `retries` in `oc_findling_queue`
ablesen. Bis dahin traegt die Nachstellung die Aussage ueber den Mechanismus und
nicht ueber den Dialekt.

## DI-05-28 (Plan 05-20): Eine geheilte Datei bleibt in der Fehlerliste der Verwaltungsseite stehen

**Found during:** Plan 05-20, Task 2, beim Zuschnitt des Heilungszweigs.

**Was:** Der Abgleich holt das gestrandete Paar zurueck, der Container liest die
Datei neu, die OCR-Spur indexiert sie, und danach ist sie ueber die Suche zu
finden. Die Zeile `failed(repeatedly_stuck)` in `oc_findling_file_state` nimmt
davon niemand zurueck: `indexed` ist die Zahl des Containers und wird in diese
Tabelle grundsaetzlich nicht geschrieben. Die Verwaltungsseite fuehrt die Datei
also weiter unter "Stuck repeatedly", waehrend sie durchsuchbar ist, und
`occ findling:diagnose` sagt in Stufe vier dasselbe.

**Wie neu das ist:** gar nicht. Es ist DI-05-14 und DI-05-21, erreicht durch eine
neue Tuer. Neu ist nur, dass diese Tuer ab jetzt regelmaessig benutzt wird: vor
Plan 05-20 blieb die Datei unindexiert und die Fehlerzeile war richtig, ab jetzt
wird sie indexiert und die Fehlerzeile ist falsch.

**Warum nicht hier erledigt:** unveraendert der Grund aus DI-05-21. Die Abhilfe
ist eine Entscheidung darueber, was eine Zeile der Zustandstabelle bedeutet, und
sie beruehrt die Quittierung, den Container-Vertrag und die Anzeige zugleich. Sie
gehoert nicht in einen Plan, dessen Gegenstand drei Befunde eines Volllaufs sind.

**Wohin es gehoert:** in den Phase-Review, zusammen mit DI-05-14 und DI-05-21,
die dieselbe Frage von den anderen zwei Seiten stellen.

## DI-05-29 (Plan 05-20): Die Verdrahtung des Stillstands-Urteils hat keinen Unit-Test, nur die Entscheidung darin

**Found during:** Plan 05-20, Task 3.

**Was:** `AdminViewService::progressStamp` ist statisch und rein, und
`php/tests/Unit/AdminViewServiceTest.php` prueft sie auf beiden Seiten der
Grenze. Was daneben steht und nicht geprueft ist, ist die Verdrahtung in
`overview()`: dass der gemerkte Zaehler VOR dem Ueberschreiben gelesen wird, dass
`stalledFor` aus dem spaeteren der beiden Zeitpunkte entsteht und dass die
Schreiboperation nur bei einer Aenderung passiert. Ein Textgate in
`backend/tests/test_admin_ui_contract.py` haelt die drei Zeilen an ihrem Platz;
was sie tun, prueft niemand.

**Warum nicht hier erledigt:** `overview()` ruft zwoelf Mitspieler auf, und ein
Test durch diese Methode hindurch waere ein Dutzend Doubles samt Statusantwort
und Scan-Statistik, um zu fragen, was ein um eins gewachsener Zaehler bedeutet.
Auf einer Maschine ohne PHP ist so ein Test ausserdem blind geschrieben, und ein
blind geschriebener Test mit einem Dutzend Doubles ist eine Wette auf die CI.

**Wohin es gehoert:** in den Plan, der die PHPUnit-Suite als naechstes
verbreitert, oder in den Phase-Review. Der billige Zwischenschritt waere, die
drei Zeilen von `overview()` in eine eigene, ebenfalls statische Methode zu
ziehen, die vier Zahlen bekommt und eine zurueckgibt.

## DI-05-32 (Plan 05-21): Der ARM-Volllauf steht aus, weil cax11 nicht buchbar ist

**Found during:** Plan 05-21, Task 1, beim ersten create.

**Was:** Am 04.09. gegen 12:20Z ist `cax11` in keiner Region dieses Kontos
buchbar. Zwei echte create-Versuche, `hel1` und `nbg1`, wurden mit
`invalid_input: unsupported location for server type` abgewiesen. Es wurde nichts
angelegt: die Suche nach dem Kennzeichen `purpose=findling-phase5` liefert ueber
Server, Volumes und Firewalls null Treffer, und es gibt keine Zustandsdatei.

**Die Falle, die eine Stunde gekostet haette:** die beiden Auskuenfte der API
widersprechen sich. `/datacenters` fuehrt cax11 als verfuegbar in `hel1-dc2` und
`nbg1-dc3`; die Flagge am Servertyp selbst steht in allen drei europaeischen
Regionen auf `false`. Die Flagge hat recht, und die Gegenprobe ist `cpx22`, das
dort auf `true` steht und tags zuvor wirklich gelaufen ist. `/datacenters` wird
nicht mehr gepflegt, weil man auf seine Auskunft nicht mehr handeln kann: das
Feld `datacenter` eines create ist seit dem 16.12.2025 abgeschafft und antwortet
mit `datacenter is deprecated and cannot be used anymore`. Das Werkzeug fragt den
Endpunkt seither nur noch, um den Widerspruch zu melden, statt ihm zu glauben.

**Warum nicht hier erledigt:** das ist Kapazitaet und kein Fehler. Sie kommt ohne
Ankuendigung zurueck und verschwindet ebenso.

**Wohin es gehoert:** in denselben Plan, sobald die Kapazitaet da ist. Eine
Warteschleife im Kratzverzeichnis fragt jede Minute und legt die Box selbst an,
sobald `hel1` oder `nbg1` frei wird; ihr Protokoll liegt in
`scratchpad/cax11-watch.log`. Faellt sie aus, ist der Handgriff
`scripts/ops/hetzner_box.sh prices`, gefolgt von `create`.

**Erledigt, aber anders: die Kapazitaet kam nicht.** Der Owner hat am
04.09. beim Anbieter angerufen, und die Auskunft lautet, dass die arm-Knappheit
Monate laeuft. Diese Auskunft schlaegt jede Lesung der API, und damit ist die
Warteschleife oben gegenstandslos; sie ist beendet und hat nichts angelegt. Der
ARM-Lauf zieht auf eine AWS-Box mit ausdruecklicher CAX11-Paritaet um:
`m7g.large`, 2 vCPU Graviton3, `eu-central-1c`, Ubuntu 24.04 arm64, und der
Arbeitsspeicher vom Kernel auf 4 GB gedeckelt, weil der Typ 8 GB traegt. Der
Deckel sitzt als Drop-in `/etc/default/grub.d/99-mem4g.cfg`, er erweitert
`GRUB_CMDLINE_LINUX_DEFAULT` statt es zu ersetzen, und er ist auf der Box
gegengelesen: `free -h` 3.9Gi, `nproc` 2, `uname -m` aarch64. Das Werkzeug dazu
ist `scripts/ops/aws_box.sh`, und `scripts/ops/hetzner_box.sh` steht wieder auf
`cpx22`, der Maschine, die mit ihm wirklich gelaufen ist. Der Befund oben bleibt
als Fundstelle stehen, samt dem Widerspruch der beiden Endpunkte, denn der gilt
weiter.

## DI-05-33 (Plan 05-21): Der Workers-Vergleich ist ohne Produktaenderung nicht messbar

**Found during:** Plan 05-21, bei der Vorbereitung der Zusatzmessung.

**Was:** Der Owner hat am 04.09. eine Zusatzmessung `INDEX_WORKERS=2`
freigegeben. `backend/src/findling/config.py:52` macht sie ohne Eingriff
unmoeglich, und zwar mit Absicht: "One indexing worker, always. [...] This is not
a tuning knob and deliberately reads no environment variable, so that making it
one is a code change somebody has to defend in review." Die Begruendung daneben
ist genau die Groesse, um die dieser ganze Lauf gefuehrt wird: OCR steht bei 300
bis 600 MB je Seite, das Einbettungsmodell bei 250 bis 400 MB, und auf der 4-GB-
Box duerfen die beiden Spitzen sich nie treffen.

**Warum nicht hier erledigt:** noch gibt es keine Box. Der Vorschlag fuer den
Bericht, sobald es eine gibt: die Begruendung aus IDX-08 woertlich zitieren und
benennen, was ein zweiter Worker architektonisch kostet, statt eine Zahl zu
liefern, die niemand einsetzen darf. Wenn nach Volllauf und Drills noch Box-Zeit
bleibt, dazu eine eng begrenzte Wegwerf-Messung auf dem kurzen Drill-Vorrat, klar
als Experiment gekennzeichnet und niemals ins Produkt eingecheckt: sie beantwortet
die Speicherhaelfte der Frage in zwanzig Minuten und gefaehrdet die Hauptmessung
nicht.

**Wohin es gehoert:** in Task 2 und Task 3 dieses Plans.

**Stand 04.09. nachmittags:** die Box steht (siehe die Erledigung von DI-05-32),
also gilt der Vorschlag von oben unveraendert und mit einem Zusatz: die
Wegwerf-Messung laeuft in einem eigenen Abbild mit einem eigenen Kennzeichen, das
nur auf der Box existiert und mit ihr geloescht wird, und der Bericht fuehrt sie
in einem eigenen Abschnitt neben der Hauptmessung, nicht in derselben Tabelle.

**Stand 05.09., erledigt.** Die Zusatzmessung ist gefahren, in einem
Wegwerf-Abbild `localhost:5000/findling_backend:05-21-arm-wegwerf-workers2`, das
mit der Box geloescht wird. Der Eingriff ist eine Schicht ueber dem gemessenen
Abbild, die genau eine Zeile ersetzt; der Beweis dafuer steht im Bericht als
Baumhash: ueber alle Python-Dateien unterscheiden sich die beiden Abbilder, ohne
`config.py` sind sie identisch. Der Arbeitsbaum ist nicht angefasst worden,
`INDEX_WORKERS` steht dort unveraendert auf 1. Ergebnis und Einordnung stehen in
`docs/performance.md` in einem eigenen Abschnitt neben der Hauptmessung.

## DI-05-34 (Plan 05-21): Die Endkosten des AWS-Laufs sind gerechnet und nicht abgelesen

**Found during:** Plan 05-21, Task 1, beim Bau der Kostenzeile von `aws_box.sh`.

**Was:** Der IAM-Nutzer dieses Laufs traegt `AmazonEC2FullAccess` und sonst
nichts. Damit fehlen ihm zwei Dinge, die die Kostenzeile des Berichts gern
gehabt haette. `pricing:GetProducts` fehlt, also kann das Werkzeug die Preise
nicht wie die Hetzner-Fassung aus der Konto-API holen; die Antwort ist ein
`AccessDeniedException`, der den Nutzer und die Aktion nennt. Und `ce:*`
beziehungsweise der Zugriff auf die Abrechnung fehlt ebenfalls, also ist auch die
Schlusszahl nicht abrufbar.

**Was stattdessen gemacht wurde, und warum das reicht:** die Saetze kommen aus
der oeffentlichen Preisliste desselben Anbieters, die ohne Anmeldung erreichbar
ist, gefiltert am 04.09. gegen die Fassung `20260903195206` fuer `eu-central-1`
(EC2) und `20260831092232` (VPC), wirksam ab 01.09.:

| Posten | Satz | Quelle |
|---|---|---|
| m7g.large, On Demand, Linux | 0,0978 USD je Stunde | AmazonEC2, eu-central-1 |
| gp3, bereitgestellter Speicher | 0,0952 USD je GB und Monat | AmazonEC2, eu-central-1 |
| oeffentliche IPv4, in Benutzung | 0,0050 USD je Stunde | AmazonVPC, eu-central-1 |

Alle drei sind Netto-USD und damit **nicht** dasselbe Mass wie die
Brutto-EUR-Tabelle der Hetzner-Haelfte des Berichts. Der Bericht sagt das, statt
die beiden Tabellen in einen Vergleich zu stellen, den keine von beiden traegt.
Die gefilterten Zeilen liegen als Rohdaten neben der Messreihe.

**Warum nicht hier erledigt:** eine zusaetzliche Richtlinie an einem
IAM-Nutzer ist eine Entscheidung des Owners ueber Rechte in seinem Konto und
keine Zeile in einer Datei. Sie ist fuer diesen Lauf auch nicht noetig: die
Laufzeit ist auf die Sekunde bekannt, die Saetze sind belegt, und das Produkt aus
beiden ist genauer als ein Abrechnungsposten, der erst Tage spaeter erscheint.

**Wohin es gehoert:** in den Phase-Review, mit einer Zeile in der
Zugangsbeschreibung. Der billige Weg fuer einen naechsten Lauf: dem Nutzer
`pricing:GetProducts` erlauben, dann kann `aws_box.sh prices` die Saetze wieder
live lesen, so wie die Hetzner-Fassung es tut.

## DI-05-35 (Plan 05-21): Ein angekuendigtes HTTP/3, das nicht erreichbar ist, kostet dem Poller einen Durchgang

**Found during:** Plan 05-21, Task 2, beim ersten Anlauf des Volllaufs auf der Box.

**Was:** Der Apache von All-in-One kuendigt HTTP/3 an. Gemessen an dieser
Instanz:

```
HTTP/2 200
alt-svc: h3=":443"; ma=2592000
```

Der Container spricht mit der Nextcloud-Haelfte ueber die oeffentliche Adresse,
und sein HTTP-Klient nimmt diese Ankuendigung an. Ist UDP 443 gefiltert, was in
einer gewoehnlichen Firewall der Normalfall ist, scheitert der Aufstieg, und der
Klient gibt den Fehlschlag nach oben, statt zurueck auf HTTP/2 zu fallen:

```
WARNING:urllib3._async.connectionpool:Retrying (Retry(total=0, ...)) after
connection broken by 'MustDowngradeError('The server yielded its support for
HttpVersion.h3 through the Alt-Svc header while unable to do so. ...')':
/ocs/v2.php/apps/findling/queues/documents?n=32&max_bytes=67108864&format=json
WARNING:findling.worker.poller:the queue did not answer, next attempt in 30 s
```

**Wie schlimm es wirklich ist, gemessen und nicht geschaetzt:** ein Durchgang je
Prozessleben. Die Gegenprobe mit wieder gesperrtem UDP 443, dreimal
hintereinander aus dem Container heraus, bleibt anschliessend auf HTTP/2 und
liefert dreimal 200; der Klient merkt sich also, dass h3 nicht geht. Mit
offenem UDP 443 steigt der zweite Aufruf auf h3 und bleibt dort. Der Poller
verliert im schlechten Fall also einen Durchgang und 15 Sekunden, nicht mehr.

**Warum es trotzdem hier steht:** der eine verlorene Durchgang ist der
Holen-Aufruf, und die Nextcloud-Haelfte zaehlt die Wiederholung **bei der
Ausgabe** (DI-05-23). Trifft der Fehlschlag eine Antwort, die die andere Seite
schon geschrieben hat, sind diese Zeilen unterwegs und ihre Wiederholung ist
verbraucht. Die Wahrscheinlichkeit ist klein, die Folge ist die aus DI-05-23.

**Was in diesem Lauf daraus wurde:** UDP 443 ist in der Security Group geoeffnet,
weil die Anleitung von All-in-One genau das verlangt (443 TCP **und** UDP) und
die Messung damit den Weg eines richtig eingerichteten Servers nimmt. Die
Generalprobe lief mit gesperrtem UDP und hat den Fall nicht gesehen, wohl weil
die damalige Fassung von AIO die Ankuendigung noch nicht sandte.

**Warum nicht hier behoben:** die Abhilfe ist eine Entscheidung ueber die
Netzwerkpolitik des Klienten und keine Zeile. Denkbar sind drei Wege: h3 im
Klienten ausschalten, ihm ein Wiederholungsbudget geben, das den Rueckfall
selbst faehrt, oder die Ankuendigung ignorieren. Das beruehrt jeden Aufruf des
Containers an die Nextcloud-Haelfte, also Poller, Quittierung und Abgleich.

**Wohin es gehoert:** in den Plan, der den HTTP-Klienten des Containers besitzt,
oder in den Phase-Review. Dazu ein Satz in `docs/dev-setup.md` oder in der
Installationsdoku: wer AIO betreibt, oeffnet 443 auch als UDP.

## DI-05-36 (Plan 05-21): Ein Neustart des Containers, der nicht von AppAPI kommt, stellt die Indexierung dauerhaft still

**Found during:** Plan 05-21, Task 2, unmittelbar nach dem Anstoss des
Volllaufs. Der Befund ist der schwerste dieses Laufs.

**Was:** Der Poller wird im Lifespan **stillgestellt** erzeugt, und bewaffnet
wird er ausschliesslich von `enabled_handler()`, also von dem Aufruf
`PUT /enabled?enabled=1`, den AppAPI sendet. Beides ist gut begruendet und im
Quelltext begruendet: ein abgeschalteter Container, der weiter Arbeit einsammelt,
ist der Klassiker der Integrationsliste, und ein Container, der vor dem
Einschalten noch keinen tantivy-Riegel haelt, kann ohne Sperre ausgeliefert
werden.

Die Folge ist, dass **jeder** Start des Containers, der nicht von AppAPI kommt,
einen Container hinterlaesst, der Suchen beantwortet, auf der Statusseite als
erreichbar erscheint, seine Fassung meldet, und nie wieder eine Datei indexiert.
Gemessen auf der Box, mit 4048 wartenden Zeilen in der Warteschlange:

```
17:45:02Z  occ findling:index  ->  scheduled 4048, handed to the worker 0
           Containerprotokoll: keine Zeile des Pollers, kein Fehler, nichts
17:46:23Z  occ app_api:app:disable + enable
17:46:40Z  der Container holt Dateien, GET /ocs/v2.php/apps/findling/files/...
```

Ausgeloest hat es hier ein `docker restart` von Hand, bei der Pruefung des
HTTP/3-Wegs. Das ist der harmlose Fall. Die beiden, die zaehlen, sind:

1. **Ein Neustart der Maschine.** Der Container kommt mit seiner Restart-Regel
   von selbst hoch, AppAPI sendet nichts, und die Indexierung bleibt aus, bis
   ein Verwalter die ExApp von Hand neu einschaltet. Auf einem Selfhoster-Server
   ist ein Neustart nach einem Update der Normalfall, und niemand schaut danach
   auf den Deckungsgrad.
2. **Ein Speichertod.** Wird der Container vom Kernel beendet, startet Docker
   ihn nach seiner Regel neu, und danach gilt dasselbe. Genau dieser Fall ist
   der Gegenstand dieses Berichts.

Was den Schaden begrenzt: die Suche laeuft weiter, der Index bleibt heil, und
`occ findling:index` zeigt den Vorrat, der sich nicht bewegt. Nach Plan 05-20
sagt die Statusseite in dieser Lage auch nicht mehr faelschlich "kommt nicht
voran" wegen der Hintergrundauftraege, sondern misst den Fortschritt der
Warteschlange; sie hat also die richtige Zahl, um es zu zeigen.

**Warum nicht hier behoben:** die Abhilfe ist eine Entscheidung darueber, woher
ein frisch gestarteter Container weiss, ob er eingeschaltet ist, und sie hat
mehrere Kandidaten mit verschiedenen Nachteilen. Den Zustand im Datenspeicher
merken und beim Start selbst bewaffnen: dann bewaffnet sich ein Container, den
ein Verwalter gerade abgeschaltet hat, nach einem Neustart wieder von selbst.
Beim Start die Nextcloud-Haelfte fragen: dann haengt der Start an einem Aufruf
nach draussen, und ein Container ohne Antwort muss sich entscheiden. Auf die
erste Antwort der Warteschlange warten und daraus schliessen: dann ist die
Unterscheidung zwischen abgeschaltet und entfernt weg, die Plan 05-08 gerade
eingebaut hat. Das ist Rule 4 und keine Zeile, und es beruehrt `main.py`, den
Poller, den Abgleich und den Vertrag mit AppAPI.

**Wohin es gehoert:** in den Phase-Review, und zwar mit Vorrang. Fuer den
Volllauf dieses Plans ist der Fall behandelt: der Sampler laeuft unter einer
Aufsicht, die ihn nach einem Containerwechsel neu startet, und der Drill 1
(Abschuss des Containers) prueft ausdruecklich, ob die Indexierung von selbst
weiterlaeuft oder ob sie genau diesen Handgriff braucht. Was der Drill dazu
findet, steht im Messbericht.

**Stand 05.09., gemessen:** Drill 1 und Drill 1b dieses Plans haben beide Faelle
ausgeloest und protokolliert, die Belege liegen in
`docs/measurements/2026-09-04-volllauf-m7g/22-drill1.txt` und `25-neustart.txt`.

| Fall | Beobachtung |
|---|---|
| `docker start` nach `docker kill` | Container laeuft, beantwortet Suchen (HTTP 200, fuenf Treffer, 759 ms), 122 s lang kein einziger Durchgang des Pollers |
| Neustart der ganzen Maschine | Container kommt nach der Regel `unless-stopped` von selbst hoch, 10 Minuten und 40 Sekunden lang **null** Durchgaenge des Pollers bei 130 wartenden Zeilen |
| Heilung in beiden Faellen | `occ app_api:app:disable` und `enable`, 3 Sekunden, erste neue Datei nach 10 Sekunden |

Zwei Zusaetze aus der Messung, die den Befund praeziser machen.

**Der erste macht ihn schwerer.** Die Verwaltungsseite kann diese Lage nicht
anzeigen. In der Beobachtung nach dem Neustart meldet sie `runState running`,
`stalledFor 0`, `backendReachable true`, waehrend der Container zehn Minuten
lang nichts getan hat. Das ist kein Fehler der Korrektur aus 05-20, sondern ihre
gewollte Grenze: das Stillstands-Urteil nimmt die spaetere von zwei Bewegungen,
damit ein langer OCR-Nachlauf nicht faelschlich als Stillstand gilt, und eine
der beiden Bewegungen (der Hintergrundauftrag von Nextcloud) ist immer frisch.
Die Aussage aus dem Absatz oben, die Seite habe "die richtige Zahl, um es zu
zeigen", ist damit widerlegt: sie hat die Zahl, aber die Regel, die sie
auswertet, kann zwischen "beide Haelften stehen" und "nur die Container-Haelfte
steht" nicht unterscheiden. Wer den Befund behebt, sollte deshalb pruefen, ob
die Seite denselben Zustand auch anzeigen koennen muss.

**Der zweite macht ihn kleiner.** Ein Messfehler auf dem Weg dorthin ist es
wert, festgehalten zu werden: der erste Durchgang von Drill 1b hat "der Poller
arbeitet wieder von selbst" gemeldet, weil der Vergleichswert 30 Sekunden vor
dem Herunterfahren genommen wurde und der Container in diesen 30 Sekunden noch
zwei Dateien fertig gemacht hat. Ein Zustand, der zum falschen Zeitpunkt
abgelesen wurde, sieht aus wie eine Bewegung. Gemessen wurde deshalb an der Zahl
der Durchgaenge im Protokoll, also an einer Handlung statt an einem Zustand.

**Wohin es gehoert, unveraendert:** in den Phase-Review, mit Vorrang.

## DI-05-37 (Plan 05-21): INDEX_WORKERS steuert nichts, es beschreibt nur

**Found during:** Plan 05-21, Task 4, bei der Zusatzmessung mit zwei
Indexarbeitern.

**Was:** `backend/src/findling/config.py:57` legt `INDEX_WORKERS = 1` fest, mit
einer ausfuehrlichen Begruendung daneben (IDX-08) und einem eigenen Test, der
verhindert, dass daraus eine Umgebungsvariable wird. Die Konstante wird von
keiner einzigen Stelle des Programms gelesen:

```
$ grep -rn INDEX_WORKERS backend/src/findling --include=*.py
backend/src/findling/config.py:57:INDEX_WORKERS = 1
backend/src/findling/extract/text.py:75:# ... and INDEX_WORKERS is 1, so a crafted ...
backend/src/findling/nc/client.py:101:# INDEX_WORKERS at one that is exactly one mebibyte ...
```

Eine Definition und zwei Kommentare. Die Serialitaet, die die Zahl beschreibt,
kommt aus der Form des Pollers: ein Nebenlaeufer, und in ihm die Schleife
`for job in claim.jobs` in `poller.py`, die eine Datei nach der anderen
abarbeitet.

**Gemessen:** ein Wegwerf-Abbild mit `INDEX_WORKERS = 2` hat gegen dasselbe
Abbild mit 1 keinen Unterschied ergeben. 200 Scans, zweimal, 802 s gegen 799 s,
und dieselbe Zeichenzahl auf das Zeichen. Das ist kein knappes Ergebnis, sondern
dieselbe Arbeit zweimal.

**Warum das trotzdem eine Konstruktion und kein Fehler ist:** die Zahl ist eine
Zusage in Schriftform. Sie steht dort, damit jemand, der die Serialitaet
aufheben will, sie anfassen und im Review begruenden muss, und der Test daneben
bewacht genau das. Der Preis dieser Konstruktion ist erst durch die Messung
sichtbar geworden: wer die Konstante hochsetzt, bekommt kein schnelleres
Programm, sondern ein Programm, das ueber sich etwas Falsches sagt.

**Vorschlag, klein und ohne Verhaltensaenderung:** den Docstring der Konstante
um einen Satz ergaenzen, der sagt, wo die Serialitaet wirklich herkommt
(`Poller._round`, die Schleife ueber `claim.jobs`), und dass diese Zahl sie
beschreibt statt sie zu setzen. Wer sie eines Tages zu einem Schalter macht,
findet dann in derselben Zeile, welche Schleife er dafuer anfassen muss.

**Wohin es gehoert:** in den Phase-Review, geringe Dringlichkeit. Es ist kein
Fehlverhalten, sondern eine Stelle, an der ein Leser etwas Falsches annehmen
kann.

## DI-05-38 (Plan 05-21): Die Verwaltungsseite kann einen stillstehenden Container nicht anzeigen

**Found during:** Plan 05-21, Drill 1b, der Neustart der Maschine.

**Was:** Waehrend der Container zehn Minuten lang keinen einzigen Durchgang
gemacht hat und 130 Zeilen warteten, meldete die Verwaltungsseite `runState
running`, `stalledFor 0` und `backendReachable true`. Das ist die gewollte
Grenze der Korrektur aus 05-20: `stalledFor` ist das Alter der **spaeteren** von
zwei Bewegungen, dem letzten Hintergrundauftrag dieser App und dem gewachsenen
indexed-Zaehler des Containers. Solange die Hintergrundauftraege von Nextcloud
laufen, ist eine der beiden Bewegungen immer frisch.

Die Regel kann also "beide Haelften stehen" erkennen und "nur die
Container-Haelfte steht" nicht. Vor 05-20 war es genau umgekehrt, und das war
schlimmer: da hat sie acht Stunden lang einen Stillstand behauptet, waehrend der
Container 6.500 Dokumente schrieb.

**Warum es hier nicht behoben wird:** die Abhilfe ist keine Zeile, sondern eine
Entscheidung ueber die Bedeutung der Kachel. Zwei Zustaende brauchen zwei
Aussagen, und die Seite hat heute eine. Denkbar waere ein zweiter Satz, der nur
dann erscheint, wenn Vorrat wartet, die Nextcloud-Haelfte sich bewegt und der
Zaehler des Containers ueber mehrere Poll-Abstaende steht; das ist genau die
Lage aus DI-05-36 und waere ein Hinweis auf sie.

**Zusammenhang:** DI-05-38 ist die Anzeige-Haelfte von DI-05-36. Wer DI-05-36
behebt, also einen frisch gestarteten Container von selbst bewaffnet, macht
DI-05-38 in fast allen Faellen gegenstandslos. Wer DI-05-36 nicht behebt,
braucht DI-05-38 dringend, denn dann ist die Seite der einzige Ort, an dem ein
Verwalter den Zustand ueberhaupt bemerken koennte.

**Wohin es gehoert:** in den Phase-Review, zusammen mit DI-05-36 und nach ihm.
