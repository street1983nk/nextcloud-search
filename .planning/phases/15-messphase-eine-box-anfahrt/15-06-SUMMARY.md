---
phase: 15-messphase-eine-box-anfahrt
plan: 06
subsystem: measurement-tooling
tags: [messwerkzeug, d-04, abbildwechsel, digest, baumhash, rm-data, cgroup, box-anfahrt]

# Dependency graph
requires:
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-01, das Laufverzeichnis, der Kopie-Waechter und TOOLS_THE_MEASUREMENT_ORDER_NAMES
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-02, Block 13b des Runbooks und die Rueckgabewerte 36 bis 39
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-03, die Hausform des Werkzeugs und die Position der Abbrueche unterhalb der Pipeline
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-04, die Doppelbelegung einer Rueckgabezahl
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-05, a_boxless_run und das Muster der gestellten Probe im Gate
  - phase: 10-vergleichsmessung-m7g
    provides: 92-wechsel.sh und 40b-baumhash.sh, der Aufrufvertrag des Baumhashbeweises
  - phase: 14-entladeschalter
    provides: FINDLING_EMBED_IDLE_RELEASE_SECONDS, die Stellung, die jede Registrierung wegwirft
provides:
  - docs/measurements/2026-09-v12-messung/skripte/92b-wechsel.sh, der Abbildwechsel per Digest, Rueckgabewerte 2, 36, 37, 38, 39
  - sieben boxlose Testfaelle des Abbildwechsels in backend/tests/test_measurement_scripts.py
  - V12_IMAGE_SWITCH, REQUIRED_DIGEST, THE_COUNT_BEFORE_RM_DATA, THE_COUNT_IS_IMMEDIATE, THE_DANGEROUS_SWITCH, THE_TREE_HASH_PROOF, THE_CGROUP, THE_HARD_LIMIT_IN_BYTES, THE_LIMIT_OUT_OF_THE_CLIENT, IMAGE_SWITCH_ABORTS, VORLAUF_CUT als benannte Konstanten
  - DRIVEN_IMAGE_SWITCH mit sha256 und Bytezahl als Waechter ueber die gefahrene Vorgaengerin
  - the_three_parts_of(), switches_that_run(), switches_without_their_count(), aborts_of()
  - Block 13b des Runbooks auf dem Aufrufvertrag des Werkzeugs
affects: [15-07-ablauf, 15-09-anfahrt, 15-15-bericht, 15-16-phasenabschluss]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Werkzeug mit einer zerstoerenden Zeile zaehlt unmittelbar davor, und ein Gate haelt den Abstand und nicht nur das Vorhandensein"
    - "Eine Pflichtangabe ohne Vorgabewert wird geprueft, bevor ein Verzeichnis angelegt wird; ein Lauf, der vor seiner ersten Messung endet, schreibt nichts"
    - "Ein Werkzeug mit zwei Pipelines hat drei Positionen fuer Abbrueche, und welche davon ein Abbruch einnimmt, ist Teil seiner Bedeutung"

key-files:
  created:
    - docs/measurements/2026-09-v12-messung/skripte/92b-wechsel.sh
  modified:
    - backend/tests/test_measurement_scripts.py
    - docs/runbook-messbox.md

key-decisions:
  - "Das Abbild wird aus ABBILD_REPO und ABBILD_DIGEST zusammengesetzt; IMAGE ist keine zweite Stellschraube mehr, weil zwei Stellschrauben den Baumhash von der Registrierung trennen koennen"
  - "ABBILD_DIGEST hat keinen Vorgabewert und wird vor mkdir geprueft; fehlend, leer und formfremd enden alle mit 2 und ohne Rohdatei"
  - "Der Rueckgabewert 36 traegt zwei Faelle: den fehlenden Baumhash und die fremde Abbildkennung im Container nach der Registrierung"
  - "Die Zaehlung der Nextcloud-Instanzen steht zweimal in der Datei, einmal als Verweigerung der Phase A und einmal unmittelbar ueber dem Schalter"
  - "Eine unlesbare Zaehlung gilt als ungleich eins; 0 sieht aus wie eine Antwort und ist keine"
  - "Die gefahrene Vorgaengerin 92-wechsel.sh wird weder editiert noch kopiert, und ein sha256-Waechter haelt das fest"
  - "92b-wechsel.sh tritt in TOOLS_THE_MEASUREMENT_ORDER_NAMES ein, im selben Commit wie die Datei (17 auf 18)"

patterns-established:
  - "Ein Gate ueber eine gefaehrliche Zeile misst den Abstand zur Absicherung, weil ein Gate auf blosses Vorhandensein fuer eine angehaengte zweite Zeile gruen bliebe"
  - "Wo ein Registrierungsweg keinen Digest kennt, wird die Identitaet nach dem Vorgang aus dem Ergebnis zurueckgelesen und nicht vor dem Vorgang geglaubt"

requirements-completed: []

# Metrics
duration: 35 min
completed: 2026-09-19
---

# Phase 15 Plan 06: Der Abbildwechsel auf den v1.2-Stand Summary

**Die erste und teuerste Luecke der Recherche ist geschlossen: `92b-wechsel.sh` zieht das Abbild per Digest statt ueber den wandernden Zeiger `:dev`, laesst den Baumhash und nicht den Digest entscheiden, erzwingt die Kette PHP-Haelfte, Registrierung, harte Grenze aus der cgroup, und die gefaehrlichste Zeile der ganzen Anfahrt, `--rm-data`, kann im Quelltext nicht mehr ohne ihre Zaehlung unmittelbar darueber stehen.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-09-19T23:25:00Z
- **Completed:** 2026-09-20T00:00:00Z
- **Tasks:** 2 von 2
- **Files modified:** 3 (1 neu, 2 geaendert)

## Accomplishments

- **Der Widerspruch des Runbooks ist aufgeloest, und zwar in der Datei und nicht nur im Plan.** `baumhash-gleich nein` bleibt Haltebedingung des Laufs, UND es wird gewechselt: der Wechsel findet einmal statt, vor der ersten Messung, und er ist genau der Vorgang, der `baumhash-gleich ja` herstellt. Der Kopfkommentar sagt dazu den Satz, der die Regel fuer den Rest der Anfahrt traegt: ein Abbildwechsel waehrend der Messreihe ist kein Nachtrag, sondern ein zweiter Messgegenstand.
- **Das Abbild kommt per Digest, und der Digest ist Pflicht.** `ABBILD_DIGEST` hat keinen Vorgabewert. Fehlt sie, ist sie leer oder traegt sie nicht die Gestalt `sha256:<hex>`, endet das Werkzeug mit 2 und der Benutzung auf stderr, bevor `mkdir -p "$OUT"` gelaufen ist. Der Grund steht in der Benutzung selbst: `:dev` wandert mit jedem gruenen Lauf der Abbildstrecke, und deren Pfadfilter reicht bis in `backend/**`, also verschiebt schon eine neue Testdatei in genau diesem Verzeichnis den Zeiger, ohne eine Zeile des Abbilds zu aendern.
- **Der Digest ist die Notiz, der Baumhash der Beweis.** Nach dem Pull wird der Digest aus dem Abbild zurueckgelesen (`abbild-digest-ist`) und gegen den geforderten gehalten; eine Abweichung ist ein protokollierter BEFUND und keine Abbruchzeile. Entschieden wird an `40b-baumhash.sh`, das als Skript gerufen und nicht als Heredoc nachgebaut wird: drei verankerte `baumhash:`-Zeilen und `baumhash-gleich ja`, alles andere endet mit 36. Das ist Befund L-05 der Phase 11, und Abschnitt 6 des Runbooks sagt es woertlich.
- **Der Rueckgabewert 36 hat einen zweiten Fall bekommen, und der schliesst das letzte Loch.** AppAPI setzt `registry/image:tag` zusammen und kennt keinen Digest; registriert wird also ueber einen Tag, und ein Tag ist wieder ein wandernder Zeiger. Das Werkzeug legt das per Digest gezogene Abbild vor der Registrierung lokal auf genau diesen Tag und liest danach die Abbildkennung AUS DEM CONTAINER zurueck. Weicht sie ab, misst der Lauf einen anderen Stand als den geprueften, und das ist derselbe unbelegte Stand wie ein fehlender Baumhash.
- **Die Abhaengigkeitskette ist erzwungen und nicht beschrieben.** Erst die PHP-Haelfte in ein Verzeichnis, dessen Name gegen `PFLICHTNAME_PHP` geprueft und notfalls zurueckgestellt wird, weil unter jedem anderen Namen der Klassenlader nichts findet und nirgends eine Fehlermeldung steht. Dann die Registrierung. Dann die harte Grenze, aus der cgroup zurueckgelesen und nicht aus dem Docker-Klienten, mit 2147483648 in `memory.max` UND in `memory.swap.max`, sonst 39. Unmittelbar daneben die Stellung des Entladeschalters als `entladeschalter-ist`, weil sie bei jeder Registrierung genauso verloren geht wie die Grenze.
- **`--rm-data` kann nicht mehr ohne seine Zaehlung im Quelltext stehen.** Die Zaehlung steht zweimal in der Datei: in Phase A als Verweigerung vor der ersten veraendernden Zeile und in Phase B unmittelbar ueber dem Schalter. Die zweite ist nicht die Wiederholung der ersten, denn dazwischen liegen ein Pull und ein Baumhashlauf. Eine unlesbare Zaehlung gilt als ungleich eins: 0 sieht aus wie eine Antwort und ist keine, und beides fuehrt zu 37.
- **Die Abbrueche stehen an drei Positionen, und das Gate haelt alle drei.** `exit 2` oberhalb beider Pipelines, weil ein Streit ueber den Messgegenstand keine Rohdatei schreiben darf. 37, 38 und 36 zwischen den Pipelines, also nach den Ablesungen der Phase A und vor dem ersten veraendernden Befehl. 37, 39 und 36 unterhalb der zweiten Pipeline, weil der Rueckgabewert einer Pipeline, die in `tee` endet, zu `tee` gehoert.
- **Sieben boxlose Faelle belegen das, bevor die erste bezahlte Minute laeuft.** Zwei parametrisierte Verweigerungsfaelle (fehlende und leere Variable), das Abstandsgate ueber `--rm-data`, das cgroup-Gate, das Baumhash-Gate, das Positionsgate ueber drei Teile und der sha256-Waechter ueber die gefahrene Vorgaengerin. Jedes der Gates traegt seine gestellte Probe, und die des Abstandsgates ist die echte Datei mit einem angehaengten zweiten `--rm-data`.

## Task Commits

Each task was committed atomically:

1. **Task 1: 92b-wechsel.sh, der Abbildwechsel per Digest** - `db67193` (feat)
2. **Task 2: Boxlose Tests des Abbildwechsels** - `128ea16` (test)
3. **Abweichung: Block 13b auf den Aufrufvertrag gebracht** - `ccde0b2` (docs)

**Plan metadata:** siehe den docs-Commit dieses Plans

## Files Created/Modified

- `docs/measurements/2026-09-v12-messung/skripte/92b-wechsel.sh` - das Werkzeug des Blocks 13b, zwei Phasen, Rueckgabewerte 2, 36, 37, 38, 39
- `backend/tests/test_measurement_scripts.py` - elf neue Konstanten, vier Helfer, sechs Testfunktionen (sieben Faelle), `umgebung` als Parameter von `a_boxless_run`, `92b-wechsel.sh` in `TOOLS_THE_MEASUREMENT_ORDER_NAMES`, die Zahl im Waechter von 17 auf 18
- `docs/runbook-messbox.md` - Block 13b ruft ueber `ABBILD_DIGEST` statt ueber `IMAGE`, der Rueckgabewert 2 steht in der Tabelle, 36 traegt seinen zweiten Fall, Abschnitt 7.1 zieht nach

## Decisions Made

- **`IMAGE` ist keine Stellschraube mehr.** Die Vorgaengerin fuehrte `IMAGE` und die erwarteten Digests getrennt, und genau darin liegt der Fehlschlag T-10-13: ein Baumhash kann dann ein Abbild pruefen, waehrend die Registrierung darunter ein anderes faehrt. Hier folgt das Abbild aus `ABBILD_REPO@ABBILD_DIGEST`, und `40b-baumhash.sh` bekommt genau diesen Wert exportiert.
- **Die Gestalt des Digests wird mitgeprueft.** Der Plan verlangt 2 fuer die fehlende Variable. Ein halber oder vertippter Digest fiele sonst erst im Pull auf, also hinter der ersten Zeile der Rohdatei, und eine Rohdatei, die mit einem Fehlschlag beginnt, ist schwerer zu lesen als gar keine. Geprueft wird nur das Praefix `sha256:`, nicht die Laenge: eine Laengenpruefung waere eine Annahme ueber kuenftige Hashverfahren.
- **Eine unlesbare Zaehlung ist keine 0.** `nextclouds_zaehlen` liefert das Wort `unlesbar`, wenn `docker ps` nichts hergibt, und `unlesbar` ist ungleich 1, also verweigert das Werkzeug. Die Vorgaengerin schrieb in diesem Fall 0 in die Datei; 0 ist zufaellig auch die sichere Seite, aber sie sieht aus wie eine Antwort, und die Zeile der Rohdatei saehe dann aus wie eine Messung.
- **Die zweite Zaehlung ist kein Zierrat.** Zwischen der Zaehlung der Phase A und dem Schalter der Phase B liegen ein Pull und ein vollstaendiger Baumhashlauf, also Minuten. Eine Instanz, die in dieser Zeit startet, macht die erste Zaehlung zu einer Aussage ueber einen vergangenen Moment. Das Runbook sagt "unmittelbar davor", und das Gate misst genau das: die Zaehlung muss hoechstens zehn Codezeilen ueber dem Schalter stehen.
- **Das Gate misst den Abstand und nicht das Vorhandensein.** Ein Gate, das nur eine Zaehlung irgendwo oberhalb verlangt, bliebe gruen fuer ein zweites `--rm-data`, das jemand unten anhaengt, weil die Zaehlung der Phase A weit darueber steht. Die gestellte Probe ist deshalb die echte Datei mit genau dieser angehaengten Zeile.
- **Zeilen, die den Schalter nur nennen, zaehlen nicht als Schalter.** Beide Verweigerungen zitieren `--rm-data` auf stderr, weil eine Diagnose, die den verweigerten Befehl nicht nennt, eine halbe Diagnose ist. Das Gate filtert `echo`- und `printf`-Zeilen heraus, statt eine Zaehlung vor jede Fehlermeldung zu erzwingen.
- **Die Modellpruefung im Abbild bleibt, samt ihrem `sha256sum`.** Das Baumhash-Gate verbietet eine eigene Hashrechnung ueber den ARBEITSBAUM, nicht jede Hashrechnung: die `sha256sum` im Abbild liest die int8-Datei des Modells, also einen Abbildinhalt, und sie ist Beleg und keine zweite Baumhashrechnung. Das Gate prueft deshalb jede `sha256sum`-Zeile auf `$REPO`, `backend/src` und `/php`.
- **Das gezogene Abbild wird lokal auf den Tag gelegt.** Sonst haenge die Registrierung an dem Zeiger, den dieser Plan gerade loswerden will. Der Beweis bleibt trotzdem die Kennung aus dem Container: ein lokaler Tag ist eine Vorkehrung, kein Beleg.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Der Aufruf in Block 13b des Runbooks passt nicht mehr zum Werkzeug**

- **Found during:** Task 1
- **Issue:** Block 13b weist den Operator an, `IMAGE="ghcr.io/street1983nk/findling_backend@<digest>" ./92b-wechsel.sh` zu rufen. Der Plan verlangt dagegen `ABBILD_DIGEST` ohne Vorgabewert als Pflichtangabe. Beides zusammen haette bedeutet: der erste Aufruf auf der bezahlten Box endet mit 2, und der Operator sucht den Grund in einem Runbook, das ihn nicht nennt.
- **Fix:** Der Codeblock ruft ueber `ABBILD_DIGEST`, ein Absatz nennt die Pflichtangabe und begruendet das Fehlen des Vorgabewerts, und er sagt, warum `IMAGE` keine zweite Stellschraube ist. Die Tabelle der Rueckgabewerte hat `2` bekommen, `36` seinen zweiten Fall, `37` die unlesbare Zaehlung, und der Satz "vier eigene Rueckgabewerte" heisst jetzt "fuenf". Abschnitt 7.1 zieht bei `36` nach. Ausserdem verwies der Block auf den Kopf von `92-wechsel.sh`; gemeint ist der Kopf der Nachfolgefassung.
- **Files modified:** `docs/runbook-messbox.md`
- **Commit:** `ccde0b2`

**2. [Rule 2 - Missing critical functionality] Die Registrierung konnte den geprueften Stand wieder verlieren**

- **Found during:** Task 1
- **Issue:** Geprueft wird ein Digest, registriert wird ueber die `info.xml`, und die traegt einen Tag, weil AppAPI `registry/image:tag` zusammensetzt. Zwischen Pruefung und Messung liegt damit genau der wandernde Zeiger, den dieser Plan abschafft: ein `:dev`, das waehrend des Laufs weiterrueckt, laesst den Container auf einem anderen Abbild starten als dem, dessen Baumhash bewiesen wurde, und keine Zeile des Laufs saehe das.
- **Fix:** Das gezogene Abbild wird vor der Registrierung lokal auf den Tag der `info.xml` gelegt, und nach der Registrierung wird die Abbildkennung aus dem Container gelesen und gegen die des gezogenen Abbilds gehalten (`abbild-im-container-ist`, `abbild-im-container-gleich`). Weichen sie ab, endet der Lauf unterhalb der Pipeline mit 36, dem Rueckgabewert des unbelegten Stands. Das ist dieselbe Doppelbelegung, die 15-04 fuer 32 und 33 und 15-05 fuer 34 und 35 gewaehlt hat, und sie ist im Runbook nachgetragen.
- **Files modified:** `docs/measurements/2026-09-v12-messung/skripte/92b-wechsel.sh`, `docs/runbook-messbox.md`
- **Commit:** `db67193`, `ccde0b2`

**3. [Rule 2 - Missing critical functionality] Das neue Werkzeug fehlte in der Vollstaendigkeitsliste der Messreihenfolge**

- **Found during:** Task 1
- **Issue:** `TOOLS_THE_MEASUREMENT_ORDER_NAMES` fuehrt jedes Werkzeug, das die Messreihenfolge nennt, und 15-01 hat zugesagt, dass das Werkzeug des Plans 15-06 die Liste mit seinem eigenen Plan betritt. Ohne diesen Schritt waere Block 13b der eine Schritt der Anfahrt, dessen Datei niemand vermisst, wenn sie fehlt.
- **Fix:** `92b-wechsel.sh` steht in der Liste, die Zahl im Waechter ist von 17 auf 18 gezogen, und beide Kommentare sagen jetzt die Regel statt der Ausnahme: ein Name tritt im Commit ein, der die Datei anlegt. Im selben Commit wie die Datei (Projektregel).
- **Files modified:** `backend/tests/test_measurement_scripts.py`
- **Commit:** `db67193`

**4. [Rule 2 - Missing critical functionality] Der Pflichtname der PHP-Haelfte war nur eine Vorgabe**

- **Found during:** Task 1
- **Issue:** `PHP_APP` ist eine Umgebungsvariable mit der Vorgabe `findling`. Ueberschreibt jemand sie, findet der Klassenlader nichts, der Suchanbieter bleibt unsichtbar, und es gibt nirgends eine Fehlermeldung. Der Plan nennt das Verzeichnis, das `findling` heissen MUSS, also ist der Name eine Bedingung und keine Vorgabe.
- **Fix:** `PFLICHTNAME_PHP` steht daneben; weicht `PHP_APP` ab, wird der Name mit einer Zeile in der Rohdatei zurueckgestellt und die Kopie landet dort, wo sie gefunden wird. Die Zeile `php-verzeichnis-ist` protokolliert, was wirklich benutzt wurde.
- **Files modified:** `docs/measurements/2026-09-v12-messung/skripte/92b-wechsel.sh`
- **Commit:** `db67193`

### Abweichungen vom Wortlaut der Akzeptanzkriterien

- **`exit 2` steht nicht hinter der `tee`-Pipeline.** Das zweite Akzeptanzkriterium von Task 1 zaehlt `exit 2` mit den vier anderen auf und sagt "alle hinter der tee-Pipeline". Fuer `exit 2` ist das nicht erfuellbar und nicht gewollt: derselbe Plan verlangt in Task 2 ein leeres `tmp_path` nach dem verweigerten Aufruf, und die Pipeline schriebe die Rohdatei. Umgesetzt ist die Hausform aus 15-03, 15-04 und 15-05, und das Positionsgate haelt alle drei Teile.
- **Die harte Grenze wird aus dem Scope-Pfad der cgroup gelesen, nicht aus `/sys/fs/cgroup/memory.max`.** Das fuenfte Kriterium nennt den kurzen Pfad. Auf der Box liegt die Grenze eines Containers unter `/sys/fs/cgroup/system.slice/docker-<id>.scope/memory.max`; der kurze Pfad waere die Grenze der Wurzel und damit die der ganzen Maschine. Gelesen wird ueber `cgroup_wert`, wie in `93-nullstand.sh` und `99c-filter-sortierung.sh`, und das Gate haelt `/sys/fs/cgroup`, `memory.max`, `memory.swap.max` und `2147483648`.
- **Die Testdatei bewegt sich in beiden Commits.** Die Projektregel verlangt, dass `test_measurement_scripts.py` im selben Commit wie das neue Skript zieht; der Plan verlangt einen Commit je Task. Beides ist erfuellt, indem der Eintrag in die Werkzeugliste (17 auf 18) im Commit der Datei steht und die Gate-Familie im Commit des Tasks 2. Beide Commits sind fuer sich gruen.
- **Das Gate zur Zaehlung prueft den Abstand.** Task 2 verlangt, dass oberhalb jeder `--rm-data`-Zeile die Zaehlung steht. Die reine Anwesenheitspruefung waere gruen geblieben, als die zweite Zaehlung versuchsweise entfernt wurde, und ebenso fuer ein angehaengtes zweites `--rm-data`. Das Gate verlangt deshalb zusaetzlich, dass die naechste Zaehlung hoechstens zehn Codezeilen darueber steht, und die gestellte Probe zeigt es an der echten Datei.

## Runbook-Nachtraege fuer 15-15 (D-10)

Der Nachtrag dieses Plans ist bereits eingetragen und nicht angemeldet: Block 13b und Abschnitt 7.1 stehen auf dem Aufrufvertrag und den fuenf Rueckgabewerten des Werkzeugs (Commit `ccde0b2`). Fuer 15-15 bleibt daraus nur der Bericht ueber den Digest, der beim Lauf wirklich gezogen wurde.

## Known Stubs

Keine. Das Werkzeug erfindet keine Zahl: wo eine Quelle nicht antwortet, steht `unlesbar`, und `unlesbar` geht nirgends als Zahl durch, sondern fuehrt zu 37 (Zaehlung) oder zu einer protokollierten Zeile ohne Urteil (Entladeschalter, Containerstart).

## Issues Encountered

Ein Werkzeug, das die Box nicht hat, kann boxlos nur an seinen Verweigerungspfaden und an seinem Wortlaut geprueft werden. Nicht fahrbar sind hier: der Pull per Digest, der Baumhashlauf im Abbild, `unregister --rm-data`, die Registrierung, `docker update` und die cgroup. Belegt sind Syntax, Aufrufvertrag, die Position aller Abbrueche, die Zaehlung vor jedem Schalter, die Abwesenheit einer eigenen Baumhashrechnung, das Lesen der Grenze aus der cgroup statt aus dem Klienten und die Unversehrtheit der Vorgaengerin.

Eine zweite Grenze gehoert genannt: der zweite Fall des Rueckgabewerts 36 vergleicht die Abbildkennung des Containers mit der des gezogenen Abbilds. Auf einer Box, auf der AppAPI aus dem lokalen Registry-Spiegel des Snapshots zieht, kann diese Kennung legitim abweichen, wenn der Spiegel ein anderes Abbild fuehrt. Das ist kein Fehlalarm, sondern genau die Frage, die Block 13b stellt; der Ausweg auf der Box ist der Spiegel mit dem geprueften Abbild und nicht ein abgeschaltetes Gate.

## Verification

| Nr | Pruefung | Ergebnis |
|----|----------|----------|
| 1 | `sh -n` auf dem neuen Skript | GRUEN |
| 2 | `exit 2` oberhalb beider Pipelines, 36/37/38 zwischen ihnen, 36/37/39 darunter | GRUEN, Positionsgate mit gestellter Probe |
| 3 | Die Datei ruft `40b-baumhash.sh` als Skript und rechnet keinen Baumhash selbst | GRUEN, keine `sha256sum`-Zeile beruehrt `$REPO`, `backend/src` oder `/php` |
| 4 | `ABBILD_DIGEST` ohne Vorgabewert, `abbild-digest-ist` wird protokolliert | GRUEN, boxlose Verweigerung mit 2 fuer fehlend und leer |
| 5 | Grenze aus der cgroup, `memory.max` und `memory.swap.max`, Erwartung 2147483648 | GRUEN, und kein `HostConfig.Memory` im Code |
| 6 | Jede laufende `--rm-data`-Zeile hat die Zaehlung unmittelbar darueber | GRUEN, zwei Schalterzeilen, Abstand 4 und 5 Codezeilen |
| 7 | `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/92-wechsel.sh` unveraendert | GRUEN, sha256 `805d49fc...`, 15.705 Byte, `git status` leer |
| 8 | `git status --porcelain backend/appinfo/info.xml` | GRUEN, leer |
| 9 | `-k "image_switch"` waehlt mindestens sechs Faelle | GRUEN, 7 bestanden, 341 abgewaehlt |
| 10 | Gates ueber `NARROW_SCOPE_DIRS` fuer den neuen Pfad (Shebang, CR, Dash, Maschinenpfad, Passwort) | GRUEN, fuenf zusaetzliche Faelle |
| 11 | `ruff check`, `ruff format --check`, `pyright`, `vulture` | GRUEN, alle vier ohne Befund |
| 12 | Volle Suite aus `backend/`, Skipzahl unveraendert | GRUEN, 2.380 bestanden, **15 uebersprungen** (unveraendert gegen 15-01 bis 15-05) |
| 13 | Kein Em-Dash, kein Umlaut, kein Emoji im Skript | GRUEN, die Datei ist durchgehend ASCII |
| 14 | Zeilenenden wie bei den Geschwistern | GRUEN, LF, kein einziges CR |
| 15 | Kein Passwort in einem Argument, kein Maschinenpfad ausserhalb eines Vorgabewerts | GRUEN, das Werkzeug kennt gar kein Passwort |

Zur Testzahl: 2.368 im Stand 15-05, plus fuenf Faelle der engen Gate-Familien ueber den einen neuen Pfad, plus sieben neue Faelle ergibt 2.380. Die Rechnung geht ohne Rest auf, es ist also kein Fall stillschweigend verschwunden.

## Threat Flags

Keine neue Angriffsflaeche. Die vier Dispositionen des Bedrohungsregisters sind umgesetzt: T-15-15 (Pull per Digest, Digest zurueckgelesen, Baumhash als Beweis, Abbruch 36, dazu der zweite Fall von 36 fuer die Abbildkennung im Container), T-15-16 (Zaehlung unmittelbar vor jedem `--rm-data`, Abbruch 37, Gate ueber den Abstand im Quelltext, unlesbare Zaehlung gilt als ungleich eins), T-15-17 (harte Grenze aus der cgroup zurueckgelesen, beide Felder, Abbruch 39), T-15-SC (keine Abhaengigkeit wird installiert; das Skript ist POSIX-`sh` und nutzt `docker`, `git`, `sed`, `awk` und `grep`; `onnxruntime==1.30.0` bleibt eingefroren).

## User Setup Required

None. Der Owner-Checkpoint 15-08 (Deckelfreigabe) ist von diesem Plan nicht beruehrt und steht weiter vor Welle C. Was der Operator vor Block 13b braucht, ist die eine Angabe `ABBILD_DIGEST`, abgelesen aus der Abbildstrecke des Phase-14-Abschlusses.

## Next Phase Readiness

- **15-07** (`00-ablauf.md`) kann den Aufrufvertrag `ABBILD_DIGEST="sha256:<hex>" ./92b-wechsel.sh`, den Rohdateinamen `92b-wechsel.txt` und die Nebendatei `92b-info-box.xml` uebernehmen, dazu die Stellung des Wechsels VOR der Zustandspruefung aus Abschnitt 5.
- **15-09** (Anfahrt) findet Block 13b im Runbook auf dem Stand des Werkzeugs, einschliesslich der fuenf Rueckgabewerte.
- **15-15** (Bericht) nennt den wirklich gezogenen Digest aus der Rohdatei neben dem Baumhash und fuehrt beide getrennt: die Notiz und den Beweis.
- **MESS-05 bleibt ungetickt.** Dieser Plan baut das Werkzeug; das Requirement gehoert an das Phasenende (15-16), obwohl die Frontmatter des Plans es fuehrt.

## Self-Check: PASSED

- `docs/measurements/2026-09-v12-messung/skripte/92b-wechsel.sh` liegt auf der Platte.
- `backend/tests/test_measurement_scripts.py` liegt auf der Platte.
- `docs/runbook-messbox.md` liegt auf der Platte.
- `db67193`, `128ea16` und `ccde0b2` stehen in `git log`.
