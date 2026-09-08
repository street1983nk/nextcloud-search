---
phase: 03-aktualit-t-und-ocr
plan: 07
subsystem: queue-rueckkanal
tags: [ocr, queue, requeue, sicherheitsgate, allowlist, zweispurigkeit, tdd]
requires:
  - "03-01: die kind-Spalte, die Claim-Reihenfolge, KIND_RANK mit content und ocr auf gleichem Rang, LOCK_TIMEOUTS je Art"
  - "03-04: der ACL-Zweig im Poller, an dessen Muster sich der Uebergabefall einreiht"
  - "02-10: die ersten beiden Allowlist-Eintraege als Formvorbild fuer den dritten"
provides:
  - "OCS_WRITE_ALLOWLIST mit dem dritten und letzten Eintrag, begruendet und mit zwei Negativtests plus Laengentest"
  - "POST /queues/documents/requeue in QueueController, mit geschlossener Artenpruefung gegen QueueMapper::KINDS"
  - "QueueMapper::requeueAs: Art umstellen, retries auf 0, Sperre frei, fehlende Zeilen anlegen, Loeschung nie ueberschreiben"
  - "nc/client.requeue_documents und DocumentQueue.requeue als definierte Ergebnisse statt Ausnahmen"
  - "Der Uebergabefall im Poller: skipped(no_text_layer) wird zur OCR-Spur statt zur Quittung"
affects:
  - "03-09 (verdrahtet die OCR-Route; ab dann liefert die zweite Spur echten Text statt derselben Feststellung)"
  - "03-10 (Bildzweig: dieselbe Route, kind=ocr, sobald Bild-Mimetypes queuebar sind)"
  - "03-12 (Abgleich: nutzt dieselbe Route mit kind=content und legt Zeilen fuer Funde ohne Queue-Zeile an)"
  - "03-14 (CI-Gate der ExApp-Vertrauensgrenze deckt dann auch requeue ab)"
  - "Phase 4 (Statusseite: RoundResult.requeued ist die Zahl der nachlaufenden Spur)"
tech-stack:
  added:
    - "keine neue Abhaengigkeit"
  patterns:
    - "Aufweichung eines Sicherheitsgates als eigener Commit mit benannter Bedrohung, erreichbaren Tabellen und Negativtest"
    - "Pfad als Zeichenkettenliteral am Aufrufort, weil das Gate ihn als ast.Constant liest"
    - "Zeilen vor dem Schreiben lesen statt affected rows zu glauben (MySQL meldet geaenderte, nicht getroffene Zeilen)"
    - "Ein Verdikt, das weder quittiert noch als Fehler gilt: der dritte Ausgang von _collect"
key-files:
  created:
    - ".planning/phases/03-aktualit-t-und-ocr/03-07-SUMMARY.md"
  modified:
    - "backend/tests/test_readonly_gate.py"
    - "php/lib/Controller/QueueController.php"
    - "php/lib/Db/QueueMapper.php"
    - "php/lib/Service/QueueService.php"
    - "backend/src/findling/nc/client.py"
    - "backend/src/findling/nc/queue.py"
    - "backend/src/findling/worker/poller.py"
    - "backend/tests/test_queue_client.py"
    - "backend/tests/test_poller.py"
key-decisions:
  - "requeueAs ueberschreibt kind=delete nie: eine Loeschung, die von einem Requeue zurueckgenommen wird, laesst das Dokument fuer immer im Index (Pitfall-3-Klasse)"
  - "Dieselben Bytes werden genau einmal uebergeben: ohne diese Bremse kreist eine ocr-Zeile bis Plan 03-09 endlos, mit jedes Mal zurueckgesetztem Versuchszaehler (T-03-704)"
  - "Angelegte Zeilen tragen storage_id und root_id als 0, weil die Route nur Datei-Ids kennt; Plan 03-12 muss die Signatur erweitern, wenn es die Felder braucht"
  - "KIND_OCR steht in nc/queue.py, aber nicht in KINDS: fragen darf der Container danach heute, ausfuehren erst ab Plan 03-09"
  - "Das Verdikt wird trotz Uebergabe aufgezeichnet, weil es die Wahrheit ueber die Textspur ist und die naechste Runde daran erkennt, dass die Datei schon uebergeben wurde"
patterns-established:
  - "Ein dritter Ausgang in _collect (weder done noch failed) fuer Zeilen, die weiterleben sollen"
  - "Laengentest auf eine Sicherheits-Allowlist als Ratsche gegen den vierten Eintrag"
requirements-completed: [OCR-01, COMP-03]
duration: ca. 40 Minuten
completed: 2026-09-01
---

# Phase 3 Plan 07: Der Rückweg zur OCR-Spur

**Ein gescanntes PDF endet nicht mehr als übersprungen, sondern wandert über den dritten und letzten Schreibweg des Containers auf die nachlaufende OCR-Spur, mit zurückgesetztem Versuchszähler und ohne dass die Zeile dabei doppelt behandelt wird.**

## Performance

- **Dauer:** ca. 40 Minuten
- **Tasks:** 3 (alle mit TDD-Gates)
- **Commits:** 5 (zwei RED, drei GREEN)
- **Geänderte Dateien:** 9, exakt die aus `files_modified`
- **Tests:** 572 grün (4 übersprungen), davon 11 neue

## Was gebaut wurde

### Task 1: Gate A um genau einen Pfad, als eigener Schritt

`OCS_WRITE_ALLOWLIST` hat jetzt drei Einträge. Der dritte,
`/ocs/v2.php/apps/findling/queues/documents/requeue`, steht unter einem
Begründungsblock in derselben Form wie die beiden aus Plan 02-10: warum es ihn
gibt (ohne ihn bleibt ein gescanntes PDF für immer skipped, was D-07 gerade
verbietet), was er erreicht (`findling_queue` und sonst nichts, keine
Nutzerdatei, kein Weg ins Dateisystem), welche Bedrohung er trägt (T-03-701
Tampering, T-03-702 für den fremden Aufrufer) und dass dies nach heutigem Stand
der letzte Schreibweg ist.

Drei Tests rahmen ihn ein. Der positive zeigt, dass ein POST auf genau diesen
Pfad kein Verstoß ist. Der negative läuft über drei Nachbarn des Pfades
(`.../requeue/all`, `.../requeues`, derselbe Pfad mit angehängtem Leerzeichen)
und zusätzlich über die Variante, bei der der Pfad in einer Modulkonstante
versteckt ist: die meldet weiterhin "an unknown path", was die Mechanik ist, auf
der die ganze Liste ruht. Der dritte schreibt die Länge auf drei fest und ist
eine Ratsche: ein vierter Eintrag fällt hier auf, also genau in dem Moment, in
dem man die drei Pflichten noch einfordern kann.

Der Commit dieses Tasks berührt keine andere Datei, RED und GREEN getrennt.

### Task 2: Die Requeue-Route in der PHP-App

`QueueMapper::requeueAs(array $fileIds, string $kind): int` verarbeitet die Liste
in `DELETE_BAND`-Bändern wie die übrigen Mehrfachschreiber. Je Band:

1. Die vorhandenen Zeilen werden mit ihrer heutigen Art gelesen. Nicht die Zahl
   der betroffenen Zeilen zu glauben ist Absicht: MySQL meldet geänderte statt
   getroffener Zeilen, also sähe eine Zeile, die die Art schon trägt, wie eine
   fehlende aus und die Antwort wäre kleiner als die Wahrheit.
2. Ein UPDATE setzt `kind`, `retries = 0` (Pitfall 11, mit dem Satz als
   Kommentar) und `locked_at` auf die Frei-Marke, also gibt die Sperre frei.
3. Fehlende Zeilen werden über `insertIgnoreConflict` angelegt, weil der Abgleich
   aus Plan 03-12 Dateien findet, die nie in der Queue standen.

`kind = delete` wird dabei nie überschrieben, weder in der PHP-Auswahl noch in der
WHERE-Bedingung (die zweite für die Zeile, die zwischen Lesen und Schreiben zur
Löschung wird). Das ist keine Kür: `delete` ist das absorbierende Element von
`KIND_RANK`, und ein Requeue, der eine Löschung zurücknimmt, lässt das Dokument
für immer im Index stehen.

`QueueController::requeue` folgt `unlockDocuments` Zeile für Zeile: die drei
Attribute voll qualifiziert, `rejectForeignCaller()` als erste Anweisung,
`intList()` mit `MAX_LIST_LENGTH` für die Datei-Ids, `kind` gegen
`QueueMapper::KINDS` als geschlossene Liste (`in_array` mit `true`, kein Regex),
`try/catch` mit generischer Meldung nach außen, Rückgabe `{requeued: n}`. Der
Parameter `kind` ist bewusst `mixed`: dann entscheidet die Prüfung und nicht die
Typkonvertierung des Dispatchers. Ein unbekannter Wert bekommt `badKind()`, das
den Wert nicht protokolliert, aus demselben Grund wie `badList()`.

Der Klassen-Docstring nennt jetzt fünf Endpunkte und drei Schreibwege, mit dem
Halbsatz, wofür der dritte da ist.

### Task 3: Die Übergabe im Container

`nc/client.py` bekommt `requeue_documents(nc, *, file_ids, kind)` in der Form der
vier vorhandenen Aufrufe, mit dem Pfad als Zeichenkettenliteral direkt im Aufruf.
`nc/queue.py` legt die dünne Schicht darüber: leere Liste heißt kein Aufruf, ein
Transportfehler wird zu `CallResult(ok=False)` und einer Logzeile mit einer Zahl.

Im Poller entscheidet `_goes_to_the_ocr_track` je Datei, und `_collect` bekommt
einen dritten Ausgang: weder `done` noch `failed`. Quittieren heißt löschen, also
wäre eine Zeile, die zugleich quittiert und umgestellt wird, in derselben Runde
aus der Queue verschwunden, in der die OCR-Spur Arbeit auf sie gelegt hat. Der
Requeue selbst läuft in `run_once` als Schritt 3b: nach dem Commit, nach den
Verdikten, vor der Quittung. Ein Abbruch dort kostet eine erneute
Textlayer-Prüfung und sonst nichts.

Bei `FINDLING_OCR_ENABLED=false` bleibt alles wie bisher, mit dem Grund im
Kommentar: eine Instanz ohne OCR soll das ehrliche Verdikt sehen statt Zeilen,
die auf eine Spur warten, die es dort nicht gibt.

## Verifikation

| Gate | Ergebnis |
|---|---|
| `uv run python -m pytest -q` | 572 passed, 4 skipped |
| `uv run pytest tests/test_readonly_gate.py -q` (als `python -m pytest`) | 24 passed |
| `uv run ruff check .` / `ruff format --check .` | Exit 0, 65 Dateien formatiert |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | Exit 0, keine Ausgabe |
| `find lib -name '*.php' -print0 \| xargs -0 -n1 php -l` (php:8.3-cli) | No syntax errors, 20 Dateien |
| `grep -c 'queues/documents/requeue' backend/tests/test_readonly_gate.py` | 8 (gefordert mindestens 2) |
| `grep -c 'def test_write_allowlist_has_exactly_three_entries'` | 1 |
| `grep -Ec 'def test_writing_ocs_call_to_another_path'` | 2 (gefordert mindestens 1) |
| `grep -ci 'threat'` in test_readonly_gate.py | 4 (gefordert mindestens 2) |
| `grep -c "url: '/queues/documents/requeue'"` | 1 |
| `ExAppRequired` in QueueController | 4 vorher, 5 nachher (plus 1) |
| `grep -c 'QueueMapper::KINDS'` in QueueController | 1 |
| `grep -c 'function requeueAs'` / retries innerhalb der ersten 30 Zeilen | 1 / ja (Zeile 21 nach der Signatur) |
| `grep -ci 'three write'` in QueueController | 2 |
| `grep -c 'queues/documents/requeue'` in nc/client.py | 1, keine Pfadkonstante daneben |
| `grep -c 'no_text_layer\|NO_TEXT_LAYER'` in poller.py | 3 |
| `test_no_text_layer_is_requeued_and_not_acknowledged` / `..._stays_skipped_when_ocr_is_off` | je 1, beide grün |

Die Sichtprobe an einer echten Instanz (Datei hochladen, Queue-Zeile von content
auf ocr, retries auf 0) steht noch aus; sie gehört zum Integrationslauf, den Plan
03-09 mit der verdrahteten OCR-Route fährt. Der Testkorpus ist unverändert
(`git status --porcelain testdata/` leer).

## Abweichungen vom Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Funktionalität] Dieselben Bytes werden nur einmal übergeben**

- **Gefunden bei:** Task 3
- **Problem:** Der Plan verlangt den Requeue bei jedem `skipped(no_text_layer)`.
  Die zurückgestellte Zeile kommt aber als `ocr`-Zeile wieder, und
  `nc/queue._kind` bildet eine Art ohne Zweig auf `content` ab, also läuft bis
  Plan 03-09 wieder die Textroute, erzeugt wieder dasselbe Verdikt und würde
  wieder übergeben. Da `requeueAs` den Versuchszähler jedes Mal zurücksetzt,
  greift auch die Aufgeberegel nie: eine Endlosschleife, genau die Bedrohung
  T-03-704 aus dem Register dieses Plans, nur eine Runde weiter gedacht.
- **Fix:** `_goes_to_the_ocr_track` liest vor der Übergabe die Zustandszeile. Ist
  dort bereits `skipped(no_text_layer)` mit demselben Inhalts-Hash vermerkt, wird
  quittiert statt übergeben. Der Hash ist Teil der Frage, also werden geänderte
  Bytes wieder übergeben. Sobald Plan 03-09 die OCR-Route verdrahtet, greift die
  Bremse gar nicht mehr, weil die zweite Spur dann `indexed` oder ein anderes
  Verdikt liefert.
- **Test:** `test_the_same_bytes_are_handed_over_once_and_then_judged` (zwei
  Runden, ein Requeue).
- **Dateien:** `backend/src/findling/worker/poller.py`, `backend/tests/test_poller.py`

**2. [Rule 2 - Fehlende kritische Funktionalität] Ein Requeue nimmt keine Löschung zurück**

- **Gefunden bei:** Task 2
- **Problem:** `requeueAs` setzt die Art laut Plan unbedingt. Wird eine Datei
  gelöscht, während ihre Zeile beansprucht ist, hebt `refreshExisting` die Art auf
  `delete` (das absorbierende Element). Der danach eintreffende Requeue auf `ocr`
  hätte die Löschung überschrieben, und das Dokument wäre für immer im Index
  geblieben, also derselbe Defekt wie Pitfall 3.
- **Fix:** `delete` wird sowohl beim Auswählen der umstellbaren Zeilen als auch in
  der WHERE-Bedingung ausgeschlossen; die zweite Prüfung deckt die Zeile ab, die
  zwischen Lesen und Schreiben zur Löschung wird.
- **Dateien:** `php/lib/Db/QueueMapper.php`

**3. [Rule 3 - Blockierendes Problem] Kein PHP auf dem Entwicklungsrechner**

- **Gefunden bei:** Task 2
- **Problem:** `php -l` ist lokal nicht vorhanden, das Abnahmekriterium verlangt
  es.
- **Fix:** Lauf in `php:8.3-cli` mit `MSYS_NO_PATHCONV=1` und read-only
  gemountetem `php/`, so wie es Plan 03-08 vorgemacht hat.
- **Verifikation:** 20 Dateien, keine Syntaxfehler.

**4. [Rule 1 - Werkzeugregel] Ruff SIM300 im Längentest**

- **Gefunden bei:** Task 1
- **Problem:** `assert OCS_WRITE_ALLOWLIST == {...}` gilt dem Regelsatz als
  Yoda-Bedingung.
- **Fix:** Literal nach links, wie von ruff vorgeschlagen; dieselbe Aussage.

---

**Summe:** 4 Abweichungen, alle automatisch behoben (2 fehlende Absicherungen, 1
Werkzeugfrage, 1 Linterregel).
**Wirkung auf den Plan:** keine Scope-Ausweitung. Beide inhaltlichen Abweichungen
setzen Dispositionen aus dem Bedrohungsregister dieses Plans um (T-03-704 und die
Aufwertungsregel aus 03-01).

## Entscheidungen

- **Angelegte Zeilen tragen 0 für storage_id und root_id.** Die Route kennt
  Datei-Ids und eine Art, mehr nicht. Alles, was der Container über die Datei
  sieht, löst `describe()` beim Claim aus dem Node auf; diese beiden Felder sind
  die Ausnahme, sie kommen aus der Zeile. Heute ist das folgenlos, weil
  `storage_id` im Index nur gespeichert und nirgends gefiltert wird. Plan 03-12
  ist der einzige Aufrufer, der Zeilen anlegt, und muss die Signatur erweitern,
  wenn er die Felder braucht; der Kommentar an der Stelle sagt das.
- **`KIND_OCR` in `nc/queue.py`, aber nicht in `KINDS`.** `KINDS` beantwortet,
  welchen Zweig eine beanspruchte Zeile ziehen darf, und einen OCR-Zweig gibt es
  erst mit Plan 03-09. Danach fragen darf der Container heute schon.
- **Das Verdikt wird trotz Übergabe aufgezeichnet.** Es ist die Wahrheit über die
  Textspur, und die nächste Runde erkennt daran, dass diese Datei schon übergeben
  wurde. Auf der Statusseite steht eine übergebene Datei damit vorübergehend als
  `skipped(no_text_layer)`, bis die zweite Spur sie überschreibt; das ist genauer
  als jede Alternative, die "läuft noch" behauptet, ohne es zu wissen.
- **`RoundResult.requeued`.** Die nachlaufende Spur braucht eine eigene Zahl:
  weder `skipped` noch `acknowledged` beschreibt eine Zeile, die weiterlebt.
- **`kind` als `mixed` im Controller.** Damit entscheidet die geschlossene Liste
  und nicht die Typkonvertierung des Dispatchers, was bei `declare(strict_types=1)`
  sonst eine zweite, unsichtbare Prüfung wäre.

## Bekannte Stubs

Keine im Sinne von nicht verdrahtetem Code. Was fehlt, ist der Verbraucher: bis
Plan 03-09 die OCR-Route verdrahtet, läuft eine `ocr`-Zeile die Inhaltsroute und
endet nach der einmaligen Übergabe als `skipped(no_text_layer)`. Das ist der
dokumentierte Zwischenstand, kein Platzhalter im Code, und die Bremse aus
Abweichung 1 sorgt dafür, dass er still bleibt statt zu kreisen.

## Threat Flags

Keine neue Angriffsfläche außerhalb des Registers. Die sechs Dispositionen sind
umgesetzt:

| Threat | Umsetzung |
|---|---|
| T-03-701 | Genau ein zusätzlicher Literalpfad, eigener Commit, Begründungsblock mit erreichbaren Tabellen, zwei Negativtests und der Längentest auf drei |
| T-03-702 | `ExAppRequired` voll qualifiziert plus `rejectForeignCaller()` als erste Anweisung; das CI-Gate dafür kommt mit Plan 03-14 |
| T-03-703 | `in_array($kind, QueueMapper::KINDS, true)`, kein Regex, keine lokale Kopie; unbekannte Art wird mit 400 abgewiesen |
| T-03-704 | Nur `requeueAs` schaltet content auf ocr, `KIND_RANK` verbietet den Rückweg, und der Container übergibt dieselben Bytes genau einmal |
| T-03-705 | `intList()` mit `MAX_LIST_LENGTH`, Verarbeitung in `DELETE_BAND`-Bändern, Antwort ist eine Zahl |
| T-03-706 | `retries = 0` im selben UPDATE, das die Art setzt |

## TDD Gate Compliance

| Task | RED | GREEN | REFACTOR |
|---|---|---|---|
| 1 | `94b7369` (Allowlist hat 2 statt 3 Einträge, der Pfad ist ein Verstoß) | `696833d` | nicht nötig |
| 2 | keiner: die PHP-App hat keine Testsuite (kein `php/tests`, keine phpunit.xml). Die Gates sind `php -l` und die Greps des Plans, wie in den Plänen 03-01 bis 03-04 | `e185669` | nicht nötig |
| 3 | `1d6b04e` (`DocumentQueue.requeue` und `RoundResult.requeued` existieren nicht) | `b252df3` | nicht nötig |

Jedes RED war aus dem beabsichtigten Grund rot: in Task 1 fehlte der Eintrag, in
Task 3 die Methode und das Feld. Nach jedem GREEN waren alle Gates ohne
Nacharbeit grün, deshalb gibt es keinen REFACTOR-Commit.

## Commits

| Commit | Typ | Inhalt |
|---|---|---|
| 94b7369 | test | RED: der dritte Schreibweg ist noch verboten |
| 696833d | sec | GREEN: Allowlist-Eintrag mit Bedrohung, Tabellen und Begründung |
| e185669 | feat | Requeue-Route: `requeueAs`, Controller, Service, Docstring auf drei Schreibwege |
| 1d6b04e | test | RED: Übergabe an die OCR-Spur, sechs Behauptungen |
| b252df3 | feat | GREEN: `requeue_documents`, die Queue-Schicht, Schritt 3b im Poller |

## Was die nächsten Pläne davon haben

- **03-09** findet die zweite Spur bereits gefüllt vor: es muss nur noch
  `Route.OCR` im Dispatcher und den Zweig im Poller ergänzen. Sobald die
  `ocr`-Zeile echten Text liefert, greift die Einmal-Bremse nicht mehr, und
  `KIND_OCR` gehört dann in `KINDS`.
- **03-10** braucht für den Bildzweig keine neue Route: dieselbe Übergabe, nur mit
  Bild-Mimetypes als Auslöser.
- **03-12** bekommt genau die Semantik, die der Abgleich braucht: `requeueAs` legt
  Zeilen für Funde ohne Queue-Zeile an. Wenn der Abgleich `storage_id` und
  `root_id` mitgeben will, ist die Signatur der Ort dafür.
- **Phase 4** kann `RoundResult.requeued` als "wartet auf Texterkennung" ausweisen.

## Self-Check: PASSED

- Alle neun geänderten Dateien stehen in `git diff --name-only e1e7dc4..HEAD`, keine zehnte.
- Alle fünf Commit-Hashes stehen im Log von `worktree-agent-03-07`.
- Keine Löschungen: `git diff --diff-filter=D --name-only e1e7dc4..HEAD` ist leer.
- Weder `.planning/STATE.md` noch `.planning/ROADMAP.md` sind im Diff, kein Push.
- Arbeitsverzeichnis sauber, keine unversionierten Dateien.

---

*Phase: 03-aktualit-t-und-ocr, Plan 07*
*Abgeschlossen: 2026-09-01*
