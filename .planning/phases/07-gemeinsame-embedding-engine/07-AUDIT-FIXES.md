---
phase: 07-gemeinsame-embedding-engine
kind: audit-fixes
base: 14a10d5
branch: exec/07-audit-fixes
befunde: 10
zusatzbefund: "CI-Rot auf 14a10d5, integration.yml, index-search-e2e auf mysql und pgsql"
commits: 11
completed: 2026-09-08
---

# Phase 7: die Audit-Befunde, behoben

Elf Commits auf `exec/07-audit-fixes`, Basis `14a10d5`. Zehn davon sind die
Befunde des Audits in der vorgegebenen Reihenfolge, einer ist die Ursache des
roten Integrationslaufs, der auf demselben Stand schon vorher rot war.

Vor jedem Commit lokal grün: `ruff check`, `ruff format --check`, `pytest -q`,
`pyright`, `vulture --min-confidence 80`, dazu `php -l` auf jeder geänderten
PHP-Datei und `node --check` auf `admin.js`. Die Workflow-Datei ist zusätzlich
mit `yaml.safe_load` gegengelesen.

## Befund, Commit, Nachweis

| Befund | Commit | Wie verifiziert |
|---|---|---|
| HIGH-1: fehlgeschlagener Schneiderbau dauerhaft aus | `2ef4ab0` | Neuer Fall `test_a_build_that_threw_is_tried_again_after_the_cooldown`: Bau wirft, `_embed_ready` ist falsch, Zeitstempel um `LOAD_RETRY_SECONDS` zurückgesetzt, danach verspricht die Spur wieder und der nächste Bau gelingt. Der alte Fall prüft zusätzlich, dass es die Karenz und nicht das dauerhafte Nein ist. |
| MEDIUM-2: `engine_state()` kennt den Fehlschlag nicht | `5191997` | Drei Fälle in `test_embed_engine.py`: Fehlschlag meldet `waiting_for_retry` statt `cold`, ein gelungener Bau nimmt die Meldung zurück, fehlendes Modell schlägt beides. Die Zusicherung "baut nichts, lädt nichts" wird über den neuen Zweig mitgeprüft. |
| MEDIUM-5: fehlende Artefakte verlieren den Vektorbestand | `4f67130` | Fall umbenannt in `..._promises_nothing_and_keeps_the_stock` plus neuer Fall, der auf einem Container ohne Modell einen Tombstone setzt und prüft, dass die Vektoren mitgehen (D-21). Die beiden alten D-21-Wächter sind unangetastet. |
| PERF-F1: Thread-Sprung pro Zeile | `e69779d` | Zwei Fälle: die zweite Zeile ruft `_build_the_cutter` nicht mehr auf, und eine Zeile innerhalb der Karenz ruft ihn auch nicht auf, wird aber wie vorher quittiert. Gezählt über einen Zähler um die gebundene Methode. |
| LOW-6: `shared_model()` außerhalb des try | `aafaf18` | Neuer Fall lässt den Halter werfen und prüft, dass weder `_chunker` noch `_model` gesetzt sind und die Karenz greift. |
| MEDIUM-3: Engine-Zeile hinter `hasDenominator` | `5715953` | Neues Gate `test_the_engine_line_is_not_hidden_behind_a_denominator_that_does_not_exist_yet` hält beide Hälften an beide Regeln. `php -l`, `node --check`. |
| MEDIUM-4: Kaltstart-Wanduhr ohne Zusicherung | `d4c20c8` | `yaml.safe_load` grün; der verschachtelte Heredoc der Zählfunktion lokal in einer Bash ausgeführt und mit `count=0` beantwortet. |
| LOW-7: `measure()` erbt den Engine-Halter | `fafa503` | Neuer Fall lädt vorher eine Engine in den Halter und verlangt danach wieder genau einen Ladevorgang. Gegenprobe: mit auskommentiertem `forget_the_engine()` ist der Fall rot. |
| LOW-8: Wort-Tor prüft nur die Wortzahl | `832a859` | `yaml.safe_load` grün; die drei `grep`-Tore lokal gegen fünf Zeilen laufen lassen (sauber, Anführungszeichen, führendes Minus, Doppelpunkt, Bindestrich im Wort). |
| PERF-F2: `artifacts_present` pro Poll | `51e432e` | Drei Fälle: fünf Abfragen kosten eine Dateisystemfrage, ein vorhandenes Modell wird weiter jedes Mal gefragt, und ein gelungener Schneiderbau vergisst das gemerkte Nein. |
| Zusatz: CI-Rot auf `14a10d5` | `75d20da` | Textuelles Gate `test_a_dirty_row_is_never_moved_to_the_embedding_track` in `test_queue_client.py`, in der Form der übrigen Gates über die PHP-Hälfte in derselben Datei. `php -l`. |

## Was inhaltlich entschieden wurde

**Die Dreiteilung des Schneiderbaus.** `_can_build_the_cutter` ist ersetzt durch
`_cutter_absent` (dauerhaft, fehlende Artefakte) und `_cutter_failed_at`
(Zeitstempel, geworfener Bau), genau wie `EmbeddingModel._load` es für die
Gewichte hält. Die Karenz ist dieselbe Konstante, weil es derselbe Fehler eine
Schicht höher ist: auf der Zielkiste ist es ein MemoryError, während 544,3 MB
unter einem harten 2-GB-Deckel ankommen.

**Der Rückweg in den Engine-Zustand ist eine Meldung, kein zweiter Zeitstempel.**
Der Poller gibt seinen eigenen Stempel per `note_cutter_failure()` an
`embed/engine.py` weiter. Damit gibt es eine Uhr und zwei Leser, statt zweier
Uhren, die auseinanderlaufen können. Ein sechstes Protokollwort war nicht nötig:
`waiting_for_retry` hat jetzt zwei Quellen und bleibt ein Wort, also kein
l10n-Churn. Weil die Meldung eine Modul-Variable ist, räumt eine
`autouse`-Fixture in `conftest.py` sie vor und nach jedem Testfall weg; sonst
entschiede ein Poller-Fall, was drei Dateien später auf der Verwaltungsseite
steht.

**Die Reihenfolge der Verdikte ist gleich geblieben.** Abgeschaltet, fehlendes
Modell, Karenz, geladen, kalt. Die Frage nach dem fehlenden Modell wird jetzt
von derjenigen Quelle beantwortet, die sie beantworten kann: der Halter, wenn es
ihn gibt, sonst die Dateifrage. Das hält "fehlendes Modell schlägt Karenz" auch
für den leeren Halter, und der leere Halter ist genau der Fall, um den es geht.

**Die Sichtbarkeitsregel der Engine-Zeile.** Der Block erscheint bei einem
Nenner ODER bei einem Wort über die Engine. Die Zeile über den fehlenden Anteil
hat dafür den Nenner in ihre eigene Regel bekommen, genau wie die entsprechende
Zeile im ersten Block: ein Block, der nur wegen der Engine-Zeile da ist, darf
nicht behaupten, ein Anteil sei nicht ausrechenbar. Kein neues Element, kein
neuer Satz, keine l10n-Änderung.

## Abweichungen

**LOW-7, der Ladezähler wird nicht zurückgesetzt.** Der Auftrag nennt "Halter +
Ladezähler leeren". `reset()` leert den Halter, die Meldung der zweiten Spur und
das gemerkte Nein über die Artefakte, aber nicht `_LOAD_COUNT`. Grund: jeder
Aufrufer von `load_count()` liest die Zahl als Differenz gegen eine selbst
genommene Grundlinie, also braucht sie niemand auf null, und ein Zähler, der
genullt werden kann, ist einer, mit dem ein Gate sich selbst grün nullen könnte.
Der Nachweis "ein Ladevorgang pro Prozess" bleibt damit monoton. Der Fall zu
LOW-7 ist trotzdem rot, wenn der Reset fehlt, also kostet die Entscheidung keine
Schärfe.

**Zwei Commits nachträglich geordnet.** Der Commit zu MEDIUM-3 war bereits
geschrieben, als `ruff format --check` einen Anführungszeichenstil in dem neuen
Testfall beanstandete. Statt einen elften Reparatur-Commit anzuhängen, ist der
Commit zu MEDIUM-3 per `--amend` korrigiert und der Commit zu MEDIUM-4 danach
neu gesetzt worden, damit jeder Commit für sich grün ist. Nichts war gepusht,
die Reihenfolge ist unverändert.

**Der Branch heißt `exec/07-audit-fixes`.** Das ist der im Auftrag genannte
Name und nicht das `worktree-agent-*`-Schema der Executor-Regeln; die
Schutzregel gegen Commits auf `main` und Konsorten ist eingehalten.

## CI-Rot auf 14a10d5

Der Lauf `34224425281` (Push von `14a10d5`) ist rot, und zwar vor allen
Änderungen dieses Zweiges. Job `index-search-e2e`, Schritt "The moved file is
found by its last content and carries no failed verdict", auf mysql und auf
pgsql, sqlite grün.

### Was das Protokoll hergibt

- 12:11:53 findet die Suche `mutationalpha`, die Datei ist mit ihrer ersten
  Fassung im Index.
- 12:11:55 bis 12:12:05 werden neun weitere Fassungen geschrieben, die letzte
  ist die einzige mit `mutationbeta`.
- Danach protokolliert der Container genau vier Durchgänge: indexiert,
  eingebettet, indexiert, eingebettet. Dann fünf Minuten lang nichts als
  `/search`.
- Am Ende: Arbeitsvorrat `scheduled 0`, `handed to the worker 0`, Zustand der
  Datei `indexed`, und `mutationbeta` findet nichts.

Der Container hat also zwei Inhaltszeilen bekommen und beide abgearbeitet, und
die Warteschlange ist leer. Die letzten Schreibvorgänge haben keine Zeile
hinterlassen. Das ist kein Zeitproblem und keine Speicherenge, sondern ein
verlorener Vermerk.

### Die Ursache im Code

`QueueMapper::refreshExisting` setzt `dirty = true`, wenn eine Zeile beschrieben
wird, während der Container sie hält. Genau dafür ist die Spalte da: die Bytes,
über die diese Runde urteilt, sind schon veraltet, also darf die Quittung die
Zeile nicht löschen (H4 des Phase-2-Audits). `QueueMapper::acknowledge` hält sich
daran.

`QueueMapper::requeueAs` hielt sich nicht daran. Die Übergabe an die zweite Spur
setzte `kind`, `retries` und `locked_at` und sah den Vermerk nicht an. Der
weitere Weg:

1. Inhaltszeile wird beansprucht, die Beanspruchung löscht `dirty`.
2. Während der Container die Datei holt, wird sie neu geschrieben:
   `dirty = true`.
3. Der Durchgang indexiert den alten Text und übergibt die Zeile an `embed`.
   `requeueAs` lässt `dirty` stehen, gibt die Zeile aber frei.
4. Der Einbettungsdurchgang beansprucht die Zeile, und **die Beanspruchung
   löscht `dirty`**. Die zweite Spur holt nie eine Datei, sie zerlegt den
   gespeicherten Text des Index, merkt also nichts.
5. Die Quittung löscht die Zeile, weil sie sauber aussieht. Der Schreibvorgang
   ist weg, bis der nächtliche Abgleich ihn Stunden später findet.

Damit ist H4 über die abhängige Spur wieder aufgebaut, und zwar seit der
Übergabe an `embed` (Plan 06-07). Der Fall braucht ein Zusammentreffen: ein
Schreibvorgang muss ankommen, während eine Inhaltszeile beansprucht ist, und der
Durchgang muss mit einer Übergabe enden. Deshalb ist er nicht in jedem Lauf und
nicht auf jeder Datenbank rot.

Der Kaltstart-Neustart des Paraphrase-Schritts macht das Zusammentreffen
wahrscheinlicher, weil er die Durchgänge des Containers mitten in das
Schreibfenster der Mutation legt.

### Die Behebung

`75d20da`. Eine schmutzige Zeile wird nicht auf eine abhängige Spur geschoben,
sondern dort freigegeben, wo sie ist: Vermerk gelöscht, Beanspruchung gelöst,
`kind` unverändert, Versuchszähler auf null. Der nächste Inhaltsdurchgang holt
die neuen Bytes, indexiert sie und übergibt die Zeile dann. Beide Anweisungen
entscheiden über den Vermerk in der Datenbank, weil zwischen einem Lesen und
einem Schreiben genau der Schreibvorgang landen kann, um den es geht; die
Umschaltung läuft zuerst, damit eine Zeile, die dazwischen schmutzig wird, von
`refreshExisting` ohnehin wieder auf `content` gehoben wird.

Der Versuchszähler geht mit auf null, aus einem stärkeren Grund als bei der
Umschaltung: der Durchgang hat seine Arbeit getan und beendet, die Zeile kommt
nur zurück, weil jemand geschrieben hat. Acht Schreibvorgänge hintereinander
würden eine kerngesunde Datei sonst in `failed(repeatedly_stuck)` laufen lassen,
und genau das prüft derselbe CI-Schritt in seiner zweiten Hälfte.

### Was die Fixes 1, 3 und 4 damit zu tun haben

Nichts. Sie wurden geprüft und scheiden aus:

- HIGH-1 und PERF-F1 betreffen den Bau des Zerlegers. Im roten Lauf ist der Bau
  gelungen, die zweite Spur hat in beiden Durchgängen eingebettet.
- MEDIUM-5 betrifft einen Container ohne Modell. Im Lauf liegt das Modell
  vorhanden im Abbild, und 26 von 26 Dokumenten tragen Vektoren.

Was aus dem Audit trotzdem hilft, ist MEDIUM-4: der Neustart darf jetzt nur bei
leerer Einbettungs-Warteschlange stattfinden, und die Wanduhr sagt selbst, ob
sie kalt war. Das nimmt dem Schritt zwei stille Fehlerquellen, die die Suche
nach dieser Ursache erschwert haben.

### Offen

Der Nachweis am lebenden System steht aus: die Mutations-Strecke lässt sich
lokal nicht nachstellen, weil sie eine Nextcloud mit mysql oder pgsql und den
WebDAV-Weg braucht. Der nächste Integrationslauf auf diesem Zweig ist die
Gegenprobe. Geht er grün, ist die Ursache bestätigt; bleibt er rot, ist die
nächste Spur die Reihenfolge von Beanspruchung und Ereignis auf der
Nextcloud-Seite.
