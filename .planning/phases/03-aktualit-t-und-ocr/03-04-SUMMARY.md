---
phase: 03-aktualit-t-und-ocr
plan: 04
subsystem: api
tags: [nextcloud, php, event-listener, background-job, share, acl, queue, python, sqlite]

# Dependency graph
requires:
  - phase: 02-indexkern-und-volltextsuche
    provides: "ACL-Vorfilter mit replace_acl und Index acl_file, is_unchanged-Schnellpfad, Bug-Audit M1"
  - phase: 03-aktualit-t-und-ocr
    provides: "Plan 03-01, Spalte kind, Claim-Reihenfolge acl/delete/metadata/content/ocr, KIND_ACL in QueueMapper, FileEventListener"
  - phase: 03-aktualit-t-und-ocr
    provides: "Plan 03-02, kind-Verzweigung in Poller._handle, describe-Verzweigungspunkt"
  - phase: 03-aktualit-t-und-ocr
    provides: "Plan 03-03, delete-Zweig vor usersFor, Feldprüfung je Art in nc/queue.py, Löschkette im Poller"
provides:
  - "QueueService::describe beantwortet kind=acl, eine leere Nutzerliste ist die Nutzlast und kein Grund zum Verwerfen"
  - "nc/queue.py kennt KIND_ACL; acl und delete sind die Arten ohne Knoten (_KINDS_WITHOUT_A_NODE)"
  - "Poller._replace_access: ein deklaratives replace_acl, kein Byte, kein store.record"
  - "Der is_unchanged-Schnellpfad schreibt die Rechte neu, Bug-Audit M1 geschlossen"
  - "ShareEventListener für ShareCreatedEvent, ShareDeletedEvent und ShareDeletedFromSelfEvent"
  - "SubtreeExpandJob: Teilbaum in Bändern, Cursor im Job-Argument, Nachfolger selbst geplant"
  - "FileEventListener plant den Teilbaum-Job bei Mount-Wechsel eines Ordners und bei gelöschtem Ordner"
affects: [03-05 OCR-Claim, 03-07 requeueAs, 03-12 ETag-Abgleich, 04 Diagnoseseite]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zwei Ereigniswege, zwei Listener: der Datei-Listener beantwortet was in der Datei steht, der Share-Listener wer sie finden darf"
    - "Ein Ereignis über einen Teilbaum wird geplant statt ausgeführt: der Job bändert, was der Klick des Nutzers nicht tragen kann"
    - "Geschlossene Liste erlaubter Arten je Mechanismus (EXPANDABLE_KINDS) statt einer Prüfung gegen alle Arten"
    - "Sicherheitseinordnung als Kommentar an der Stelle, an der sie missverstanden würde: veralteter Vorfilter kostet Trefferqualität, nicht Vertraulichkeit"

key-files:
  created:
    - php/lib/Listener/ShareEventListener.php
    - php/lib/BackgroundJobs/SubtreeExpandJob.php
  modified:
    - php/lib/Service/QueueService.php
    - php/lib/Listener/FileEventListener.php
    - php/lib/AppInfo/Application.php
    - backend/src/findling/nc/queue.py
    - backend/src/findling/worker/poller.py
    - backend/tests/test_poller.py
    - backend/tests/test_acl_prefilter.py
    - backend/tests/test_queue_client.py

key-decisions:
  - "Die Ausnahme wird als Liste der Arten ohne Knoten geführt (_KINDS_WITHOUT_A_NODE), nicht als kind != delete: eine später hinzukommende Art gilt damit zunächst als knotenpflichtig, und das ist die sichere Richtung dieses Irrtums"
  - "Der Schnellpfad schreibt die ACL in Schritt 1 statt in Schritt 3, weil er Schritt 3 gar nicht erreicht; ein Schreibvorgang gegen eine Datei, die die Runde ohnehin gelesen hat"
  - "SubtreeExpandJob nimmt nur acl und delete an; content wäre ein Neu-Crawl und ist Sache des ETag-Abgleichs"
  - "Die Deadline steht am Schleifenanfang statt am Ende (Bug-Audit M4 nicht wiederholt)"
  - "Beide Löschereignisse laufen durch dieselbe Weiche, IJobList::add dedupliziert über das Argument"
  - "Ein wiederhergestellter Ordner bleibt bewusst dem ETag-Abgleich überlassen, mit Kommentar im Code und Eintrag in deferred-items.md"

patterns-established:
  - "Mount-Identität über getNumericStorageId vergleichen, nie über den Mount-Pfad: eine Umbenennung ändert den Pfad, nicht den Mount"
  - "Ein Auftrag ohne Bytes geht mit size 0 in die Queue, damit er kein Byte-Budget verbraucht (gilt jetzt für delete und acl)"
  - "Ein Auftrag ohne Verdikt läuft nie über store.record, sonst zählt attempts und die Aufgeben-Regel schlägt auf einem Erfolg zu"

requirements-completed: [COMP-03, IDX-05]

# Metrics
duration: 40min
completed: 2026-09-01
---

# Phase 3 Plan 04: Share und Teilbaum Summary

**Rechteänderungen haben jetzt ihren eigenen, billigen Weg in den Vorfilter: Share und Unshare werden acl-Aufträge, die kein Byte kosten und kein Verdikt überschreiben, die leere Nutzerliste eines Unshare ist dabei die Nutzlast und kein Fehler, und eine Ordner-Operation über tausend Dateien wird zu tausend Aufträgen in Bändern statt zu einem Ereignis, das 999 davon verschluckt.**

## Performance

- **Duration:** rund 40 min reine Ausführung
- **Started:** 2026-09-01T11:05Z
- **Completed:** 2026-09-01T11:45Z
- **Tasks:** 3 (Task 1 nach RED/GREEN, also 4 Commits)
- **Files modified:** 11 (2 neu, 9 geändert)

## Accomplishments

- **Die zweite Hälfte von Pitfall 4 ist geschlossen.** `describe()` hat bisher mit derselben `null`-Rückgabe zwei verschiedene Dinge gesagt, und Plan 03-03 hat davon nur den Löschfall geheilt. Nach einem Unshare liefert `usersFor()` eine leere Liste, die Zeile fiel als `skipped(gone)` heraus, und die alten ACL-Zeilen blieben stehen. Der `acl`-Zweig steht jetzt direkt neben dem `delete`-Zweig, gibt `{fileId, storageId, kind, userIds}` zurück und behandelt die leere Liste als das, was sie ist: der Zielzustand.
- **Ein acl-Auftrag kostet einen Schreibvorgang.** `Poller._replace_access` ruft ausschliesslich `store.replace_acl(file_id, user_ids)` über `asyncio.to_thread`. Kein Gateway-Aufruf, keine Scratch-Datei, kein Sandbox-Kind, und ausdrücklich kein `store.record`: das würde `attempts` hochzählen und das Verdikt überschreiben, sodass drei Unshares derselben Datei als `failed(repeatedly_stuck)` endeten, obwohl jeder von ihnen funktioniert hat. Genau deshalb darf diese Art laut D-04 auch vor jedem Inhaltsjob drankommen.
- **Bug-Audit M1 ist erledigt, und zwar hart in dieser Phase.** Der `is_unchanged`-Schnellpfad quittierte eine unveränderte Datei ohne einen einzigen Schreibvorgang. Eine Rechteänderung, die als Inhaltsjob ankommt, und das ist der Normalfall bei jedem Crawl und jedem Schreibvorgang auf eine geteilte Datei, erreichte den Vorfilter deshalb nie. Der Schnellpfad schreibt die Rechte jetzt ebenfalls neu, mit einem eigenen Test.
- **Freigeben und Entziehen erreichen die Queue.** `ShareEventListener` behandelt `ShareCreatedEvent`, `ShareDeletedEvent` und `ShareDeletedFromSelfEvent`. Die dritte Klasse ist die, an die man nicht denkt: der Empfänger entfernt die Freigabe aus seiner eigenen Ansicht, und ohne diese Zeile bekäme genau er die Datei weiterhin angeboten. Alle drei Signaturen wurden vor der Verwendung gegen die Quelle im laufenden Test-Nextcloud geprüft (`lib/public/Share/Events/`, `getShare(): IShare`), nicht aus dem Gedächtnis übernommen.
- **Eine Ordner-Operation ist ein Ereignis über tausend Dateien, und das ist jetzt gebändert.** `SubtreeExpandJob` spiegelt `StorageCrawlJob`: Bänder von 250, Wanduhr-Deckel von 30 s, Transaktionsband von 250, Cursor im Job-Argument (IDX-02), selbst geplanter Nachfolger, Kettenende genau dann, wenn hinter dem Cursor nichts mehr liegt. Ein unbrauchbares Argument wird mit einer Warnung verworfen statt sich ewig neu zu planen (T-03-404).
- **Der Ordnerfall hängt an drei Stellen.** Der Share-Listener plant den Job für einen freigegebenen Ordner, der Datei-Listener für einen Ordner, der die Mount-Grenze überschritten hat, und für einen gelöschten Ordner (`kind=delete`). Innerhalb desselben Mounts geschieht weiterhin nichts, mit der Begründung aus Plan 03-02 im Kommentar.
- **Die Sicherheitseinordnung steht dreimal im Code**, an jeder Stelle, an der sie sonst missverstanden würde: im Zweig von `describe()`, im Docstring von `_replace_access` und im Klassenkopf des Share-Listeners. Es entsteht kein Leck, weil Snippets erst nach dem PHP-Recheck über `getFirstNodeById()` entstehen. Ein veralteter Vorfilter kostet Trefferqualität und Rechenzeit, nicht Vertraulichkeit. Ohne diesen Satz wird die Einordnung später entweder zur Panik oder zur Nachlässigkeit.

## Task Commits

1. **Task 1: ACL-Auftrag durch beide Seiten, leere Liste inbegriffen**
   - `35227b3` (test) , sieben fehlschlagende Tests in `test_poller.py`, `test_acl_prefilter.py` und `test_queue_client.py`
   - `a947214` (feat) , `acl`-Zweig in `describe`, `KIND_ACL` im Queue-Client, `Poller._replace_access`, ACL im Schnellpfad (M1)
2. **Task 2: Share-Listener** , `e626c6b` (feat)
3. **Task 3: Teilbaum-Job für Ordner-Operationen** , `e3de49a` (feat)

**Plan-Metadaten:** dieses SUMMARY (docs-Commit im selben Branch)

## Files Created/Modified

- `php/lib/Listener/ShareEventListener.php` (neu) , drei Share-Ereignisse auf einen Zweig, Datei wird `acl`-Zeile, Ordner wird Teilbaum-Job, alles in `try/catch` über `\Throwable`, Log nur mit dem Fehlertypnamen. Der Klassenkopf nennt die Sicherheitseinordnung und die bewusst offene Grenze Gruppenwechsel.
- `php/lib/BackgroundJobs/SubtreeExpandJob.php` (neu) , `QueuedJob` im Muster von `StorageCrawlJob`. Konstantenblock mit Begründung, Argumentvalidierung inklusive geschlossener Artenliste, Transaktionsband, Zeitdeckel am Schleifenanfang, Cursor im Argument, Nachfolgerplanung. Log führt Zähler, Storage-Id, Ancestor und Cursor, nie einen Pfad.
- `php/lib/Service/QueueService.php` , der `acl`-Zweig in `describe()` neben dem `delete`-Zweig, mit dem Kommentar, warum die leere Liste hier die Nutzlast ist.
- `php/lib/Listener/FileEventListener.php` , `IJobList` im Konstruktor, `queueRename` bekommt Quelle und Ziel und unterscheidet Mount-intern von Mount-übergreifend, neue Weiche `queueDeletion` für Datei und Ordner, gemeinsamer Planer `expand()`. Der Restore-Zweig sagt jetzt, warum ein wiederhergestellter Ordner dem ETag-Abgleich gehört.
- `php/lib/AppInfo/Application.php` , zweite Registrierungsschleife für die drei Share-Ereignisse, mit der Begründung, warum es zwei Listener und zwei Listen sind.
- `backend/src/findling/nc/queue.py` , `KIND_ACL`, `KINDS` um die vierte Art erweitert, `_KINDS_WITHOUT_A_NODE` als die Liste der Ausnahmen von der Feldprüfung.
- `backend/src/findling/worker/poller.py` , `KIND_ACL`-Zweig direkt hinter dem Löschzweig, neue Methode `_replace_access`, `replace_acl` im `is_unchanged`-Schnellpfad.
- `backend/tests/test_poller.py` , `_permission_change()` als Auftragsbauer ohne Datei, vier Tests: keine Bytes, kein `record`, Reihenfolge der Schritte, Schnellpfad schreibt die ACL (M1). `_job()` nimmt jetzt eine Nutzerliste entgegen.
- `backend/tests/test_acl_prefilter.py` , `test_unshare_with_empty_user_list_clears_the_prefilter`, durch den ganzen Poller-Pfad statt nur gegen `replace_acl`, gefragt aus der Sicht des Nutzers, dem die Freigabe entzogen wurde.
- `backend/tests/test_queue_client.py` , `ACL_SOURCE`, drei Tests dazu; `acl` ist aus der Liste der unbekannten Arten heraus.
- `.planning/phases/03-aktualit-t-und-ocr/deferred-items.md` , zwei Einträge (Sichtprobe, wiederhergestellter Ordner).

## Decisions Made

- **Die Feldprüfung im Queue-Client nennt die Ausnahmen, nicht die Regel.** Statt `kind != KIND_DELETE` steht dort jetzt `kind not in _KINDS_WITHOUT_A_NODE`. Der Unterschied zeigt sich bei der nächsten Art: `ocr` braucht Mimetype, Grösse und einen Lesenutzer wie ein Inhaltsjob, und mit einer Liste der Ausnahmen gilt sie automatisch als knotenpflichtig, bis jemand ausdrücklich etwas anderes entscheidet. Das ist die sichere Richtung dieses Irrtums.
- **`SubtreeExpandJob` nimmt nur `acl` und `delete`.** `content` und `ocr` wären ein Neu-Crawl eines Teilbaums, dessen Bytes niemand angefasst hat, und `metadata` würde Namen neu schreiben, die sich nicht geändert haben: die Nachkommen eines umbenannten Ordners behalten ihren eigenen Namen. Eine geschlossene Liste ist zugleich der zweite Teil der Argumentvalidierung, denn ein Job mit einer sinnlosen Art würde die Queue mit Aufträgen füllen, für die im Container kein Zweig existiert.
- **Der Zeitdeckel wird am Schleifenanfang geprüft.** `StorageCrawlJob` prüft ihn am Ende, und Bug-Audit M4 hält fest, dass ein `continue` davor den Deckel aushebelt. Der neue Job wiederholt das nicht. Die Reihenfolge kostet nichts: der Cursor steht auf dem letzten wirklich bearbeiteten Eintrag, also setzt der Nachfolger genau dort auf.
- **Beide Löschereignisse laufen durch dieselbe Weiche.** `NodeDeletedEvent` und `MoveToTrashEvent` rufen jetzt `queueDeletion()`, das für einen Ordner den Teilbaum-Job plant und für eine Datei die `delete`-Zeile schreibt. `IJobList::add` dedupliziert über das Argument, also plant ein in den Papierkorb verschobener Ordner einen Job und nicht zwei.
- **Mount-Identität über `getNumericStorageId()`.** Die Frage "hat der Ordner den Mount gewechselt" lässt sich nicht über den Mount-Pfad beantworten, weil eine Umbenennung genau diesen Pfad ändert, ohne dass sich an den Rechten etwas ändert. Die numerische Storage-Id ist dieselbe Grösse, mit der die Queue und der Crawl arbeiten.
- **Ein wiederhergestellter Ordner bleibt offen, aber benannt.** Seine Nachkommen bräuchten Inhaltsjobs, und Inhaltsjobs verteilt dieser Job bewusst nicht. Der Fall gehört dem ETag-Abgleich aus Plan 03-12, der ihn als "lokal als gelöscht markiert, in der Seite wieder vorhanden" ohnehin behandeln muss. Der Grund steht als Kommentar im Restore-Zweig und als Eintrag in `deferred-items.md`, damit aus einer Entscheidung keine Lücke wird.
- **Die ACL im Schnellpfad wird in Schritt 1 geschrieben.** Der Schnellpfad erreicht Schritt 3 nie, also gibt es dort keine Alternative. Sicher ist es aus demselben Grund wie beim Löschen: der Schreibvorgang ist deklarativ und idempotent, und die Quittung bleibt das Letzte, was passiert.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `test_queue_client.py` musste mit angefasst werden**

- **Found during:** Task 1 (ACL-Auftrag durch beide Seiten)
- **Issue:** Die Datei stand nicht in `files_modified`, enthielt aber `test_a_kind_this_container_does_not_know_is_a_content_job`, das ausdrücklich behauptet, ein `acl`-Auftrag laufe die Inhaltsroute. Sobald `KIND_ACL` in `KINDS` steht, ist diese Behauptung falsch und der Test rot. Die Suite wäre nach Task 1 nicht grün geworden.
- **Fix:** `acl` aus der Liste der unbekannten Arten entfernt, Kommentar auf den neuen Stand gebracht, und die drei Tests für das acl-Quellobjekt dort ergänzt, wo `DELETE_SOURCE` aus Plan 03-03 schon steht: leere Nutzerliste kommt durch, gefüllte Nutzerliste kommt in Reihenfolge an, unbrauchbare `fileId` fliegt weiterhin raus.
- **Files modified:** `backend/tests/test_queue_client.py`
- **Verification:** `uv run python -m pytest -q` , 540 passed, 1 skipped. Die Datei steht in keinem anderen Plan dieser Welle, es gibt also keine Überschneidung mit dem parallelen Executor.
- **Committed in:** `35227b3` (RED) und `a947214` (GREEN)

**2. [Rule 2 - Missing Critical] Der Teilbaum-Job prüft auch die Art seines Arguments**

- **Found during:** Task 3 (Teilbaum-Job)
- **Issue:** Der Plan nennt für die Argumentvalidierung Storage und Ancestor. Die Art steht aber ebenfalls im Argument und wandert ungeprüft in jede Zeile, die der Job schreibt. Ein Job mit `kind = ''` oder mit einer Art, für die es im Container keinen Zweig gibt, hätte einen ganzen Teilbaum in unbrauchbare Queue-Zeilen verwandelt, und zwar gebändert, wiederaufsetzbar und über mehrere Läufe hinweg. Das ist derselbe Schaden, den T-03-404 für den Endlosfall beschreibt, nur schreibend.
- **Fix:** `EXPANDABLE_KINDS` als geschlossene Liste mit Begründung, geprüft in derselben Bedingung wie Storage und Ancestor, Abbruch mit Warnung.
- **Files modified:** `php/lib/BackgroundJobs/SubtreeExpandJob.php`
- **Verification:** `php -l` grün; die Prüfung steht in derselben `if`-Bedingung wie die beiden Ids, es gibt also keinen zweiten Pfad daran vorbei.
- **Committed in:** `e3de49a` (Task-3-Commit)

**3. [Rule 1 - Bug] Der Papierkorb-Zweig hätte den gelöschten Ordner weiterhin verschluckt**

- **Found during:** Task 3 (Teilbaum-Job)
- **Issue:** Der Plan nennt nur `NodeDeletedEvent` für den Ordnerfall. `MoveToTrashEvent` rief aber weiterhin `queue()`, und `queue()` steigt für einen Ordner wortlos aus. Auf einer Instanz mit aktivem Papierkorb feuern beide Ereignisse, das eine früher als das andere; wäre nur eines der beiden umgestellt worden, hinge das Ergebnis an einer Reihenfolge, die niemand garantiert.
- **Fix:** Beide Ereignisse rufen dieselbe Weiche `queueDeletion()`. Doppelte Planung kostet nichts, weil `IJobList::add` über das Argument dedupliziert.
- **Files modified:** `php/lib/Listener/FileEventListener.php`
- **Verification:** `php -l` grün; `grep -c 'SubtreeExpandJob' php/lib/Listener/FileEventListener.php` liefert 4, die Weiche ist an einer Stelle gebündelt.
- **Committed in:** `e3de49a` (Task-3-Commit)

---

**Total deviations:** 3 auto-fixed (1 blockierend, 1 fehlende kritische Funktionalität, 1 Bug)
**Impact on plan:** Keine Erweiterung des Umfangs. Der erste Punkt war die Bedingung dafür, dass die Suite nach Task 1 überhaupt grün ist, die beiden anderen sind Korrektheitsbedingungen für das erklärte Ziel des Plans. Ausser `test_queue_client.py` und `deferred-items.md` wurde keine Datei ausserhalb der neun des Plans angefasst.

## Issues Encountered

- **Ein Abnahmekriterium ist wörtlich nicht erfüllbar.** Task 1 verlangt, dass `grep -n "acl" -A 20 backend/src/findling/worker/poller.py` keinen Aufruf von `store.record` enthält. Der einzige Treffer ist Zeile 704 in `_record_verdicts`, wo `store.replace_acl` und `store.record` für einen **Inhaltsjob** direkt untereinander stehen, so wie sie es seit Phase 2 tun und weiterhin müssen. Die Absicht des Kriteriums ist geprüft und erfüllt: der acl-Zweig selbst ist frei von `record`, nachgewiesen mit `awk '/async def _replace_access/,/async def _rewrite_metadata/' ... | grep -c "record("` , Ergebnis 0.
- **Zeilenenden.** `core.autocrlf` steht auf `true`, während die PHP-Dateien mit LF im Arbeitsbaum liegen. Die beiden neuen Dateien wurden ebenfalls mit LF geschrieben, git meldet beim Hinzufügen die übliche Warnung. Der Bestand bleibt damit einheitlich.
- **Keine PHP-Testebene im Repo.** Die Tasks 2 und 3 sind im Plan als `tdd="true"` markiert, es gibt in diesem Projekt aber keine phpunit-Einrichtung, und die Abnahmekriterien beider Tasks bestehen ausschliesslich aus `php -l` und Greps. Sie wurden deshalb wie Task 3 aus Plan 03-03 als je ein `feat`-Commit ausgeführt. Die Verhaltensbehauptungen der beiden Tasks sind über den Container-Pfad getestet (Poller und Vorfilter) sowie über die Greps abgesichert; was fehlt, ist die Nextcloud-Seite, und die steht als Sichtprobe in `deferred-items.md`.

## Offene Prüfung (nicht erledigt)

Das letzte Abnahmekriterium von Task 3 ist eine **Sichtprobe im Test-Nextcloud**: Ordner mit mehreren Dateien freigeben, als Empfänger nach einem Wort aus einer der Dateien suchen und sie finden, danach Freigabe entziehen und keinen Treffer mehr bekommen. Sie konnte hier aus denselben zwei harten Gründen nicht laufen wie in Plan 03-03: der Container `findling-nextcloud` bindet die PHP-App aus dem Haupt-Checkout ein, den ein Wave-Executor nicht anfassen darf, und der ExApp-Container mit dem Poller läuft nicht. Der Punkt steht in `deferred-items.md` und gehört in den phasenweiten Integrationsschritt. Alle automatisierbaren Kriterien der drei Tasks sind erfüllt und geprüft.

## Threat Flags

Keine. Die Fläche dieses Plans ist im Bedrohungsregister vollständig erfasst (T-03-401 bis T-03-406). Die Nutzerliste stammt ausschliesslich aus `usersFor()` auf der PHP-Seite, also aus derselben Quelle wie beim Crawl (T-03-402), und die Auftragsquelle bleibt die App-eigene Queue hinter der ExApp-Grenze.

## Known Stubs

Keine.

## User Setup Required

Keine.

## Verification

- `cd backend && uv run python -m pytest -q` , **540 passed, 1 skipped** (vorher 532)
- `uv run ruff check .` , grün
- `uv run ruff format --check .` , 62 Dateien formatiert
- `uv run pyright` , 0 errors, 0 warnings, 0 informations
- `uv run vulture src tests --min-confidence 80` , grün
- `find lib -name '*.php' -print0 | xargs -0 -n1 php -l` in `php:8.3-cli` , grün, alle 20 Klassen
- Greps aus den Abnahmekriterien: `Application.php` 3 Share-Klassen; `ShareEventListener.php` 1x `implements IEventListener`, 1x `'acl'`, 3x `SubtreeExpandJob`, 2 Treffer auf `group`, kein Log mit Namen; `SubtreeExpandJob.php` 9 Konstantentreffer, 1x `scheduleAfter` hinter der Prüfung auf gesehene Einträge, 2x `last_file_id`, kein Log mit Pfad; `FileEventListener.php` 4x `SubtreeExpandJob`
- `git diff --diff-filter=D --name-only 3f16b9e HEAD` , leer, der Plan hat keine Datei gelöscht

## Next Phase Readiness

- **Plan 03-05 (OCR)** ist nicht betroffen; die Claim-Reihenfolge und die Batch-Grössen je Art standen bereits aus Plan 03-01.
- **Plan 03-07 (requeueAs)** kann `_KINDS_WITHOUT_A_NODE` als Muster für die Frage übernehmen, welche Felder eine Art wirklich braucht. `ocr` bleibt bewusst knotenpflichtig.
- **Plan 03-12 (ETag-Abgleich)** erbt zwei benannte Fälle: der wiederhergestellte Ordner und die Nachkommen eines Ordners, dessen Papierkorb geleert oder abgeschaltet ist. Beides steht als Kommentar im Code und in `deferred-items.md`.
- **Phase 4 (Diagnose)** bekommt mit `SubtreeExpandJob` einen zweiten Job, der `SchedulerJob::LAST_JOB_RUN` fortschreibt, die Anzeige "wann lief zuletzt ein Job dieser App" bleibt also auch dann ehrlich, wenn gerade kein Crawl läuft.

## Self-Check: PASSED

Alle elf genannten Dateien liegen vor, alle fünf Commits sind im Branch
`worktree-agent-03-04` auffindbar, und der Plan hat keine einzige Datei gelöscht.

---
*Phase: 03-aktualit-t-und-ocr*
*Completed: 2026-09-01*
