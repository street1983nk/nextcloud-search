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

## DI-05-30 (Plan 05-18): Zwei Saetze der Verwaltungsseite stehen ohne Trennung aneinander

**Found during:** Plan 05-18, beim Aufnehmen des Verwaltungs-Screenshots fuer
den Store.

**Was:** `php/templates/admin.php:244` gibt `Deliberately left out: %s` aus und
Zeile 245 setzt unmittelbar `Those files are too large, ...` daneben. Im
gerenderten Absatz liest das als ein Satz: "Deliberately left out: 0 Those files
are too large, of a type Findling does not read, or excluded by a rule." Die
Zahl und der Anfang des naechsten Satzes stossen ohne Punkt zusammen. Dasselbe
gilt fuer die deutsche Fassung in `php/l10n/de.js` und `php/l10n/de.json`
("Bewusst ausgelassen: %s").

**Warum es mehr ist als eine Kleinigkeit:** Der Absatz steht in
`store/media/screenshot-admin.png`, also in einem oeffentlichen Store-Bild, und
er ist die erste Zeile, die ein Betrachter unter dem Deckungsgrad liest.

**Warum nicht hier erledigt:** `php/templates/admin.php` und die beiden
l10n-Dateien stehen nicht in den `files_modified` dieses Plans, und ein
paralleler Ausfuehrer arbeitet in derselben Welle genau an den
Verwaltungs-Vorlagen. Eine Zeile in einer fremden Datei aus einem Worktree ist
die Art Konflikt, die diese Liste vermeiden soll.

**Wohin es gehoert:** in den Plan, der die Verwaltungsseite ohnehin anfasst
(05-20), oder in den Phase-Review. Der Umfang: ein Punkt hinter `%s` in drei
Dateien, und danach das Store-Bild neu aufnehmen, weil es den alten Wortlaut
zeigt.

## DI-05-31 (Plan 05-18): `.gitattributes` fuehrt `store/media` nicht

**Found during:** Plan 05-18, beim Ablegen der drei Store-Bilder.

**Was:** `.gitattributes` erzwingt `-text` ausdruecklich fuer
`testdata/corpus/**` und `testdata/fonts/**`, mit der Begruendung, dass ein
Checkout dort keinen einzigen Vertragsbyte umschreiben darf. Die drei Bilder
unter `store/media` sind Artefakte derselben Art: sie sind byte-genau, sie sind
oeffentlich, und ihre Adresse steht in beiden `info.xml`. Eine Regel dafuer gibt
es nicht.

**Warum es heute nichts kaputt macht:** eine PNG-Datei enthaelt NUL-Bytes, also
erkennt die eigene Heuristik von Git sie als binaer und laesst sie in Ruhe. Die
beiden gefuehrten Verzeichnisse stehen genau deshalb dort, weil ihre PDF-Dateien
diese Eigenschaft NICHT haben.

**Warum nicht hier erledigt:** `.gitattributes` steht nicht in den
`files_modified` dieses Plans, sie ist gemeinsames Gut mehrerer Plaene dieser
Phase, und DI-05-12 haelt bereits eine zweite offene Aenderung an derselben
Datei.

**Wohin es gehoert:** in denselben Plan, der DI-05-12 erledigt, oder in den
Phase-Review. Eine Zeile `store/media/** -text` genuegt.

## DI-05-32 (Plan 05-18): Ein gesperrter Begriff steht in einem oeffentlichen Kommentar

**Found during:** Plan 05-18, bei der Typografie- und Vokabularpruefung der
geaenderten Dateien.

**Was:** Die Regel des Owners fuer oeffentliche Artefakte sperrt einen
bestimmten deutschen Begriff fuer einen Aufbewahrungsort. Plan 05-17 hat
festgehalten, dass er in keiner der sechs Store-Fassungen vorkommt. Die Pruefung
dieses Plans hat ihn als englisches Wort in einem Kommentar gefunden:
`backend/appinfo/info.xml`, Zeile 13, im Absatz ueber das Release-Paket. Der
Kommentar reist im Release-Paket mit und ist damit oeffentlich.

**Warum es eine Frage und keine Behebung ist:** Ob die Regel den englischen
Fachausdruck fuer ein Paket ueberhaupt trifft, ist eine Entscheidung des Owners
und keine Zeile in einer Datei. Trifft sie ihn, dann trifft sie ihn nicht nur
hier: der Release-Plan dieser Phase spricht durchgehend davon, und die Antwort
muss vor diesem Plan stehen, nicht danach.

**Warum nicht hier erledigt:** der Fund ist aelter als dieser Plan, er liegt
ausserhalb der Aenderung, die dieser Plan an derselben Datei vornimmt, und eine
Umbenennung ohne die Entscheidung waere geraten.

**Wohin es gehoert:** in den Phase-Review, zusammen mit der Frage, ob dieses
Repository das Vokabular-Gate ueberhaupt mechanisch fuehren soll; heute fuehrt
es keines, das ist der Befund von Plan 05-17.

## DI-05-33 (Plan 05-18): Der CI-Probelauf von release.yml ist noch nicht gefahren

**Found during:** Plan 05-18, Task 3.

**Was fehlt:** Die Abnahmebedingung "Ein Probelauf ueber `workflow_dispatch` ist
gruen" ist NICHT erfuellt, und sie war aus diesem Worktree nicht erfuellbar.
`workflow_dispatch` setzt voraus, dass die Workflow-Datei auf einem Zweig im
entfernten Repository liegt. Dieser Ausfuehrer darf nicht pushen, also existiert
`release.yml` fuer GitHub noch nicht.

**Was stattdessen belegt ist.** Jeder Schritt des Workflows wurde am 04.09.2026
auf dieser Maschine gefahren (`scratchpad/shots/rehearse-release.sh`), mit zwei
benannten Ersetzungen: Wegwerf-Schluessel mit denselben Subjects wie die echten
(`CN=findling`, `CN=findling_backend`), und `occ` aus dem laufenden
Nextcloud-34.0.3-Container statt aus einem frischen `nextcloud/server`-Checkout.
Ergebnis, Ende zu Ende gruen:

| Beweis | Wert |
|---|---|
| Store-Validierungspfad ueber beide gestagte `info.xml` | `- validates` |
| `occ integrity:sign-app` | `Successfully signed`, `signature.json` 10697 Bytes |
| Companion-Archiv | 220913 Bytes, 67 Eintraege, ein Top-Level `findling/` |
| Backend-Archiv | 26807 Bytes, 5 Eintraege, ein Top-Level `findling_backend/` |
| Beide Release-Signaturen | 684 base64-Zeichen, `openssl dgst -verify` sagt `Verified OK` |
| Ausschlussliste | kein `tests`, `vendor`, `phpunit.xml`, `composer.json`, `composer.lock` |
| Gegenprobe | ein absichtlich mit `tests`, `phpunit.xml` und `composer.json` gebautes Archiv wird von derselben Schleife gefangen |
| Alle 23 `run`-Bloecke | `bash -n` ohne Fehler |
| Beide Zertifikate | live geholt, Subject und Fingerprint stimmen mit der Tabelle in `docs/certificates.md` |

**Was daran offen bleibt, und zwar genau das und nichts weiter:**

1. Dass `APP_PRIVATE_KEY` und `BACKEND_PRIVATE_KEY` im Lauf wirklich in die
   Schluesseldateien geraten. Der Owner hat bestaetigt, dass beide Secrets
   liegen; ob der Inhalt ein brauchbarer RSA-Schluessel ist, sieht erst der
   Lauf. Der Workflow bricht mit eigener Meldung ab, wenn eine Variable leer
   ist.
2. Dass der `nextcloud/server`-Checkout auf `stable34` ein `occ` liefert, das
   signiert. Lokal gegen 34.0.3 belegt, also dieselbe Familie, aber nicht
   dieselbe Quelle.
3. `actions/upload-artifact` mit den vier Dateien.
4. `gh release create`. Bleibt beim Probelauf ausdruecklich unausgefuehrt, das
   ist der Owner-Entscheid vom 04.09.2026 und T-05-77.
5. Die `timeout-minutes: 20` sind eine benannte Schaetzung, siehe DI-05-34.

**Wohin es gehoert:** in den Plan, der den Zweig merged, oder in Plan 05-19, der
den Tag setzt und den Lauf ohnehin ausloest. Der Befehl danach:

```
gh workflow run release.yml --ref main
```

## DI-05-34 (Plan 05-18): `timeout-minutes` von release.yml ist geschaetzt, nicht gemessen

**Found during:** Plan 05-18, Task 3.

**Was:** Plan 05-13 hat die Regel gesetzt, dass jede Deadline die Messung nennt,
aus der sie stammt, oder ausdruecklich sagt, dass es keine gibt.
`.github/workflows/release.yml` sagt es ausdruecklich: die 20 Minuten sind aus
dem `phpunit`-Job von `php.yml` abgeleitet (Server-Checkout mit Submodulen, ein
wenig ueber drei Minuten) plus den Messwerten des `app-metadata`-Jobs (12 bis 36
Sekunden), grosszuegig verdreifacht.

**Warum nicht hier erledigt:** Es gibt keinen Lauf, aus dem eine Messung kommen
koennte, und der Grund dafuer steht als DI-05-33.

**Wohin es gehoert:** in denselben Vorgang, der DI-05-33 schliesst. Nach dem
ersten gruenen Lauf den Absatz durch die gemessene Spanne ersetzen, wie es die
sechs anderen Workflow-Dateien halten.
