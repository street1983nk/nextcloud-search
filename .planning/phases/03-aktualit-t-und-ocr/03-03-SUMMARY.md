---
phase: 03-aktualit-t-und-ocr
plan: 03
subsystem: api
tags: [tantivy, sqlite, nextcloud, php, event-listener, queue, delete, trashbin, python]

# Dependency graph
requires:
  - phase: 02-indexkern-und-volltextsuche
    provides: Tantivy-Upsert per Query.term_query, Zustandsspeicher mit Spalte deleted_at, ACL-Vorfilter mit Index acl_file
  - phase: 03-aktualit-t-und-ocr
    provides: "Plan 03-01, Spalte kind, Claim-Reihenfolge, KIND_DELETE in QueueMapper, FileEventListener"
  - phase: 03-aktualit-t-und-ocr
    provides: "Plan 03-02, QueueJob.kind mit geschlossener Liste, kind-Verzweigung in Poller._handle, describe-Verzweigungspunkt"
provides:
  - "IndexBatchWriter.drop_document(file_id), ein Dokument aus dem Index nehmen, Loeschung ueber das Schema"
  - "Ein Drop zaehlt in pending, damit ein reiner Loeschstapel ueberhaupt committet wird"
  - "Store.tombstone(file_id, at), deleted_at setzen, Verdikt bleibt lesbar"
  - "Der record-Upsert loescht deleted_at wieder, das ist der Wiederherstellungspfad"
  - "QueueService::describe beantwortet kind=delete vor usersFor, ohne Knoten und ohne Nutzerliste"
  - "nc/queue.py laesst einen delete-Auftrag ohne userIds, mime und size durch, verlangt aber eine brauchbare file_id"
  - "Poller._forget: drop_document, forget_acl, tombstone, ohne Gateway, ohne Sandbox-Kind, ohne store.record"
  - "NodeDeletedEvent und MoveToTrashEvent als delete-Zeile, NodeRestoredEvent als content-Zeile"
affects: [03-04 Share und Subtree, 03-07 requeueAs, 03-12 ETag-Abgleich, 04 Diagnoseseite]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eigene Job-Art statt Sonderfall: eine Auftragsart, die den Knoten nicht braucht und ihn auch nicht aufloesen darf"
    - "Tombstone statt Zeilenloeschung: die Zeile bleibt lesbar, deleted_at IS NULL in _IS_UNCHANGED_SQL macht sie wieder bearbeitbar"
    - "Wiederherstellung ohne zweiten Einstiegspunkt: der vorhandene Upsert hebt die Markierung auf"
    - "Der Loeschbeweis wird aus der Sicht eines fremden Nutzers gefuehrt, nie aus der des Loeschenden"

key-files:
  created: []
  modified:
    - backend/src/findling/index/writer.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/store/schema.sql
    - backend/src/findling/nc/queue.py
    - backend/src/findling/worker/poller.py
    - backend/tests/test_index_writer.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_acl_prefilter.py
    - backend/tests/test_queue_client.py
    - backend/tests/test_poller.py
    - php/lib/Service/QueueService.php
    - php/lib/Listener/FileEventListener.php
    - php/lib/AppInfo/Application.php

key-decisions:
  - "drop_document zaehlt in pending hoch, sonst antwortet flush() auf einen reinen Loeschstapel nothing_pending und die Loeschung bleibt uncommittet im Writer liegen"
  - "Kein revive(): _RECORD_SQL setzt deleted_at im ON-CONFLICT-Zweig auf NULL, ein zweiter Einstiegspunkt waere eine zweite Stelle, die daran denken muesste"
  - "forget_acl und tombstone laufen in Schritt 1 der Runde, nicht in Schritt 3, damit die Datei sofort aus dem Vorfilter faellt; die Quittung bleibt trotzdem das Letzte"
  - "Eine brauchbare file_id bleibt fuer jede Job-Art Pflicht, auch fuer delete, weil sie die ganze Nutzlast der Loeschung ist"
  - "Der Groessendeckel gilt fuer eine Loeschung nicht, weil er skipped(too_large) schreibt und das eine Aussage ueber eine vorhandene Datei ist"
  - "Eine Loeschung geht mit size 0 in die Queue, damit sie keinen Anteil am Byte-Budget eines Claims verbraucht"

patterns-established:
  - "Job-Art ohne Knoten: describe verzweigt VOR jeder Aufloesung, das Quellobjekt traegt nur fileId, storageId und kind"
  - "Kein store.record auf einem Auftrag ohne Verdikt, sonst zaehlt attempts hoch und die Aufgeben-Regel schlaegt auf einem Erfolg zu"
  - "Fehlende Felder je Art pruefen statt die Pruefung fuer alle zu lockern"

requirements-completed: [COMP-03, IDX-05]

# Metrics
duration: 25min
completed: 2026-09-01
---

# Phase 3 Plan 03: Löschen, Papierkorb und Wiederherstellen Summary

**Löschen ist eine eigene Job-Art geworden, die ohne Knoten und ohne Nutzerliste durch beide Seiten läuft: der Container nimmt das Dokument aus dem Tantivy-Index, vergisst die Rechtezeilen und setzt einen Tombstone, und der Beweis wird aus der Sicht eines zweiten Nutzers geführt statt aus der des Löschenden.**

## Performance

- **Duration:** rund 25 min reine Ausführung
- **Started:** 2026-09-01T09:45Z
- **Completed:** 2026-09-01T10:10Z
- **Tasks:** 3 (zwei davon nach RED/GREEN, also 5 Commits)
- **Files modified:** 13 (0 neu, 13 geändert)

## Accomplishments

- **Der Zustand, den IDX-05 verbietet, wird nicht mehr produziert.** Bisher rief `QueueService::claim()` immer `describe()`, und `describe()` gab `null` zurück, sobald `usersFor()` leer war oder der Knoten nicht mehr auflösbar war. Die Zeile wurde als `skipped(gone)` quittiert und gelöscht, der Container erfuhr von der Löschung nie, und die Datei blieb für immer im Index und in der ACL-Tabelle. Der `delete`-Zweig steht jetzt **vor** `usersFor()` und liefert `{fileId, storageId, kind}` und sonst nichts: kein `usersFor`, kein `getFirstNodeById`, kein Mount.
- **`IndexBatchWriter.drop_document(file_id)`** nimmt ein Dokument wirklich aus dem Index. Die Löschung geht über `Query.term_query` aus dem Schema, genau wie der Upsert in `add`. Der naheliegende Weg über `delete_documents_by_term` baut einen I64-Term, der die U64-Spalte `file_id` nie trifft: er wirft nichts, löscht nichts und meldet Erfolg. Ein Test belegt null Treffer nach dem Commit, ein zweiter prüft die Term-Bildung statisch.
- **`Store.tombstone(file_id, at)`** setzt `files.deleted_at` und lässt Verdikt, Grund und `attempts` unangetastet. Die Bedingung `deleted_at IS NULL` stand seit Phase 2 in `_IS_UNCHANGED_SQL`, und genau sie sorgt dafür, dass eine gelöschte Datei nicht als unverändert und damit unberührbar gilt.
- **Wiederherstellen braucht keine zweite Methode.** `_RECORD_SQL` setzt `deleted_at` im `ON CONFLICT`-Zweig auf `NULL`. Eine Datei, die erneut beurteilt wird, ist per Definition nicht gelöscht, und `NodeRestoredEvent` reiht sie schlicht als Inhaltsjob ein.
- **Der Poller-Zweig läuft vor jedem Byteabruf.** `drop_document`, `forget_acl`, `tombstone`, jeweils über `asyncio.to_thread`, dann die Quittung. Kein Gateway-Aufruf, keine Scratch-Datei, kein Sandbox-Kind, und ausdrücklich **kein** `store.record`: das würde `attempts` hochzählen und das Verdikt überschreiben, sodass drei Löschungen derselben Datei in die Aufgeben-Regel liefen und als `failed(repeatedly_stuck)` endeten, obwohl jede von ihnen erfolgreich war.
- **Der Abnahmetest sucht als fremder Nutzer.** `test_deleted_file_is_gone_for_another_user` indexiert eine Datei für `alice` und `bob`, löscht sie und fragt den Vorfilter danach für **beide**. Nur so unterscheidet sich "der PHP-Recheck filtert es weg" (was ohnehin passiert) von "es ist wirklich aus dem Index raus". Der Unterschied steht als Kommentar im Test.
- **D-10 gilt in beide Richtungen.** `NodeDeletedEvent` und `MoveToTrashEvent` erzeugen eine `delete`-Zeile, `NodeRestoredEvent` eine `content`-Zeile. Der Papierkorb ist für die Suche ein Löschen, genau wie in der nativen Files-Suche; ein Wartenauf das Leeren des Papierkorbs würde die Datei dreißig Tage lang in den Treffern lassen.

## Task Commits

Jeder Task wurde einzeln committet, die beiden TDD-Tasks in RED und GREEN:

1. **Task 1: Dokument aus Index, ACL und Zustand nehmen**
   - `1548d21` (test) , zehn fehlschlagende Tests für `drop_document`, `tombstone` und den Vorfilter
   - `f1757cd` (feat) , `drop_document`, `_TOMBSTONE_SQL`, `Store.tombstone`, `deleted_at = NULL` im Upsert
2. **Task 2: Löschauftrag ohne Knoten durch beide Seiten**
   - `a539e55` (test) , sechs fehlschlagende Tests in `test_poller.py` und `test_queue_client.py`
   - `23e687d` (feat) , `delete`-Zweig in `describe`, `KIND_DELETE` im Queue-Client, `Poller._forget`
3. **Task 3: Löschen, Papierkorb und Wiederherstellen im Listener** , `3a15837` (feat)

**Plan-Metadaten:** dieses SUMMARY (docs-Commit im selben Branch)

## Files Created/Modified

- `backend/src/findling/index/writer.py` , neue Methode `drop_document`, `pending` zählt jetzt Hinzufügungen **und** Löschungen, der Docstring nennt die Namensregel von Gate A und verweist auf die I64/U64-Messung im Modulkopf.
- `backend/src/findling/store/repo.py` , `_TOMBSTONE_SQL` als Modulkonstante mit Begründung, `Store.tombstone`, `deleted_at = NULL` im `ON CONFLICT`-Zweig von `_RECORD_SQL`, der Kommentar an `_IS_UNCHANGED_SQL` auf den neuen Stand gebracht.
- `backend/src/findling/store/schema.sql` , der Kommentar an `deleted_at` sagt nicht mehr "stays NULL".
- `backend/src/findling/nc/queue.py` , `KIND_DELETE`, `KINDS` um die dritte Art erweitert, `_job()` prüft die Pflichtfelder je Art statt für alle gleich; der Kommentar an der Prüfung nennt Pitfall 3 und 4 und sagt, warum diese eine Zeile die Löschung bisher verschluckt hat.
- `backend/src/findling/worker/poller.py` , `KIND_DELETE`-Zweig als erste Verzweigung in `_handle`, neue Methode `_forget`. Die vier nummerierten Schritte der Runde sind unangetastet.
- `backend/tests/test_index_writer.py` , fünf Tests: echte Löschung, Commit eines reinen Löschstapels, unbekannte id, geschlossener Writer, statische Prüfung der Term-Bildung.
- `backend/tests/test_store_repo.py` , fünf Tests: Tombstone setzen, Standardzeitpunkt, `is_unchanged` wird falsch, erneutes Verdikt hebt die Markierung auf, Tombstone auf eine unbeurteilte Datei.
- `backend/tests/test_acl_prefilter.py` , `test_prefilter_forgets_a_deleted_file`, gefragt für jeden Nutzer und nicht nur für einen.
- `backend/tests/test_queue_client.py` , `DELETE_SOURCE` als das Quellobjekt, das `describe()` jetzt baut, zwei Tests dazu; `delete` ist aus der Liste der unbekannten Arten heraus.
- `backend/tests/test_poller.py` , `_deletion()` als Auftragsbauer ohne Nutzer und ohne Mimetype, fünf Tests: fremder Nutzer, keine Bytes und kein Verdikt, kein `record`, Reihenfolge der Schritte, Löschung einer nie indexierten Datei.
- `php/lib/Service/QueueService.php` , der `delete`-Zweig in `describe()`, vollständig begründet, weil er die Umkehrung der bisherigen Logik ist.
- `php/lib/Listener/FileEventListener.php` , drei neue Zweige, `$isDeletion` in `queue()` mit zwei begründeten Ausnahmen (Mimetype-Allowlist und Größendeckel), der Ordner-Fall nennt jetzt Teilbaum-Job und ETag-Abgleich als Rücklage.
- `php/lib/AppInfo/Application.php` , drei Klassen mehr in der Ereignisschleife, der Kommentar sagt, warum ein Listener auf eine nicht vorhandene Trashbin-Klasse harmlos ist.

## Decisions Made

- **Ein Drop zählt in `pending`.** `flush()` steigt bei `_pending == 0` mit `nothing_pending` aus, ohne zu committen. Ein Stapel aus lauter Löschungen hätte damit kein einziges hinzugefügtes Dokument, die Löschung bliebe uncommittet im Writer liegen, und die Datei bliebe auffindbar, bis zufällig eine fremde Datei indexiert wird. Das ist derselbe Fehler wie gar nicht zu löschen, nur schwerer zu reproduzieren. `_pending_bytes` bleibt unberührt, weil eine Löschung keinen Text trägt.
- **Kein `revive()`.** Der Plan liess beides zu. Der Upsert setzte `deleted_at` bisher nicht zurück, also wurde die Zeile `deleted_at = NULL` in den `ON CONFLICT`-Zweig aufgenommen statt eine zweite Methode zu bauen. Ein zweiter Einstiegspunkt wäre eine zweite Stelle, an die jeder künftige Aufrufer denken müsste.
- **`forget_acl` und `tombstone` laufen in Schritt 1, nicht in Schritt 3.** So fällt die Datei sofort aus dem Vorfilter, was D-10 verlangt. Sicher ist es, weil die Quittung trotzdem das Letzte bleibt: ein Abbruch vor dem Commit gibt die Zeile zurück, und alle drei Schreibvorgänge sind idempotent (ein abwesendes Dokument löschen, nicht vorhandene Zeilen vergessen, `deleted_at` erneut setzen). Ein Test hält die Folge `forget_acl, tombstone, commit, acknowledge` fest.
- **Eine brauchbare `file_id` bleibt für jede Art Pflicht.** Bei einer Löschung ist sie die ganze Nutzlast; eine Null würde dem Index sagen, er solle ein Dokument vergessen, das niemand benannt hat. Nur `size`, `mime`, `userIds` und `fetchAs` dürfen bei `delete` fehlen.
- **Der Größendeckel gilt für eine Löschung nicht.** Er schreibt `skipped(too_large)`, und das ist eine Aussage über eine vorhandene Datei, die nicht indexiert wurde. Auf eine gelöschte Datei angewandt stünde der falsche Grund auf der Diagnoseseite, und schlimmer: die Löschung fiele weg, weil der Zweig mit `return` endet.
- **Eine Löschung geht mit `size` 0 in die Queue.** Sie bewegt keine Bytes, also darf sie auch keinen Anteil am Byte-Budget eines Claims verbrauchen; sonst füllten ein paar gelöschte grosse Dateien einen ganzen Stapel.
- **`NodeDeletedEvent` und `MoveToTrashEvent` bleiben beide registriert**, obwohl sie bei aktivem Papierkorb für dieselbe Operation feuern. `enqueue` ist über den Unique-Index auf `file_id` idempotent, der zweite Aufruf frischt die Zeile des ersten auf. Ohne Papierkorb feuert nur das eine, mit Papierkorb feuert das andere früher, und beides muss abgedeckt sein.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Ein Löschstapel wurde nie committet**

- **Found during:** Task 1 (Dokument aus Index, ACL und Zustand nehmen)
- **Issue:** `flush()` gibt bei `self._pending == 0` `FLUSH_NOTHING_PENDING` zurück, ohne `writer.commit()` zu rufen. Eine Runde, die nur Löschaufträge enthält, fügt kein Dokument hinzu. Die über `delete_documents_by_query` vorgemerkte Löschung wäre also im Writer liegen geblieben und erst mit einem späteren, fremden Commit wirksam geworden. Der Abnahmetest "keine Treffer nach dem Commit" wäre in genau dem Fall rot geworden, der in der Praxis der Normalfall ist: ein Nutzer löscht, sonst passiert nichts.
- **Fix:** `drop_document` zählt `self._pending` hoch. Der Docstring der Eigenschaft `pending` sagt jetzt "added or dropped" und nennt den Grund. `_pending_bytes` bleibt unberührt, weil eine Löschung keinen Text trägt und der Byte-Deckel eine Speichergrenze ist.
- **Files modified:** `backend/src/findling/index/writer.py`
- **Verification:** `test_a_dropped_document_makes_the_flush_commit_at_all` prüft `pending == 1` und `FLUSH_COMMITTED`.
- **Committed in:** `f1757cd` (Task-1-Commit)

**2. [Rule 2 - Missing Critical] Der Upsert hob den Tombstone nicht auf**

- **Found during:** Task 1 (Dokument aus Index, ACL und Zustand nehmen)
- **Issue:** Der Plan liess offen, ob das Zurücksetzen von `deleted_at` "ohnehin durch das Upsert in `_RECORD_SQL` geschieht". Es geschah nicht: der `ON CONFLICT DO UPDATE SET`-Zweig zählte `deleted_at` nicht auf. Eine wiederhergestellte Datei hätte die Markierung für immer behalten, `is_unchanged` hätte in jeder Runde `False` geantwortet, und der Container hätte sie bis zum nächsten Reindex bei jedem Durchgang erneut heruntergeladen und extrahiert. Erfolgskriterium "Eine wiederhergestellte Datei ist wieder auffindbar" wäre erfüllt gewesen, aber zum Preis dauerhafter Arbeit.
- **Fix:** `deleted_at = NULL` im `ON CONFLICT`-Zweig, mit dem Kommentar, warum es keine zweite Methode gibt.
- **Files modified:** `backend/src/findling/store/repo.py`
- **Verification:** `test_recording_a_file_again_lifts_its_tombstone` prüft `deleted_at is None` und `is_unchanged is True`.
- **Committed in:** `f1757cd` (Task-1-Commit)

**3. [Rule 2 - Missing Critical] Der Größendeckel hätte jede Löschung einer grossen Datei verschluckt**

- **Found during:** Task 3 (Löschen, Papierkorb und Wiederherstellen im Listener)
- **Issue:** Der Plan nennt nur den Wegfall der Mimetype-Prüfung. `queue()` prüft aber noch einen zweiten Deckel: eine Datei über `StorageCrawlJob::MAX_SIZE` wird als `skipped(too_large)` vermerkt, und der Zweig endet mit `return`. Auf einen Löschauftrag angewandt hätte das die Zeile gar nicht erst eingereiht, und jede grosse Datei wäre nach dem Löschen im Index geblieben. Zusätzlich hätte es das Verdikt einer Datei überschrieben, die schlicht nicht mehr da ist.
- **Fix:** `$isDeletion` steuert beide Ausnahmen, jede mit ihrer eigenen Begründung im Kommentar.
- **Files modified:** `php/lib/Listener/FileEventListener.php`
- **Verification:** `php -l` grün; der Zweig ist an einer Stelle gebündelt und die Begründung steht daneben.
- **Committed in:** `3a15837` (Task-3-Commit)

---

**Total deviations:** 3 auto-fixed (3 fehlende kritische Funktionalität, Rule 2)
**Impact on plan:** Alle drei sind Korrektheitsbedingungen für das erklärte Phasenziel, nicht Zusatzarbeit. Ohne die erste und die dritte wäre die Löschung in verbreiteten Fällen wirkungslos geblieben, ohne die zweite hätte jede wiederhergestellte Datei dauerhaft Arbeit erzeugt. Kein Scope Creep: keine Datei ausserhalb der zwölf des Plans angefasst, ausser `backend/src/findling/store/schema.sql`, wo nur ein veraltet gewordener Kommentar korrigiert wurde.

## Issues Encountered

- **`forget_acl` existierte bereits.** Plan 02-xx hatte die Methode samt Index `acl_file` schon gebaut. Statt sie neu zu schreiben wurde sie nur um den fehlenden Nachweis ergänzt: der Vorfilter wird nach der Räumung für **jeden** Nutzer gefragt, nicht nur für einen.
- **Zeilenenden in den PHP-Dateien.** Die beiden Listener-Dateien liegen mit LF im Arbeitsbaum, während `core.autocrlf` auf `true` steht. Die Bearbeitung lief über ein Skript, das die Zeilenenden unverändert lässt (`newline=""`); der Diff umfasst 85 hinzugefügte und 8 entfernte Zeilen und damit keine Masseänderung.

## Offene Prüfung (nicht erledigt)

Das letzte Abnahmekriterium von Task 3 ist eine **Sichtprobe im Test-Nextcloud**: Datei löschen, als zweiter Nutzer (`kollegin`) nach einem Wort aus dem Inhalt suchen, kein Treffer; Datei wiederherstellen, nach dem nächsten Poller-Durchgang wieder Treffer. Diese Prüfung konnte hier nicht laufen, und zwar aus zwei harten Gründen:

1. Der Container `findling-nextcloud` bindet die PHP-App aus dem **Haupt-Checkout** `C:\Users\Student\nextcloud-search\php` ein, nicht aus diesem Worktree. Den Haupt-Checkout darf ein Wave-Executor nicht anfassen.
2. Der ExApp-Container mit dem Python-Backend läuft derzeit nicht; ohne ihn gibt es keinen Poller-Durchgang.

Die Sichtprobe gehört damit hinter das Zusammenführen dieser Welle, in den phasenweiten Integrationsschritt. Sie ist zusätzlich in `deferred-items.md` dieses Phasenverzeichnisses vermerkt. Alle automatisierbaren Kriterien der drei Tasks sind erfüllt und geprüft.

## Threat Flags

Keine. Die Fläche, die dieser Plan hinzufügt, ist im Bedrohungsregister des Plans vollständig erfasst (T-03-301 bis T-03-305). Die Auftragsquelle bleibt ausschliesslich die App-eigene Queue hinter der ExApp-Grenze, und die `fileId` bildet der Listener aus dem Nextcloud-Ereignis, nie aus einer Nutzereingabe (T-03-302).

## Known Stubs

Keine.

## Verification

- `cd backend && uv run python -m pytest -q` , **532 passed, 1 skipped** (vorher 514)
- `uv run ruff check .` , grün
- `uv run ruff format --check .` , 62 Dateien formatiert
- `uv run pyright` , 0 errors, 0 warnings
- `uv run vulture src tests --min-confidence 80` , grün
- `find lib -name '*.php' -print0 | xargs -0 -n1 php -l` in `php:8.3-cli` , grün
- Gate A (`tests/test_readonly_gate.py`) grün: der neue Löschpfad trägt keinen verbotenen Bezeichner, die Methode heisst `drop_document`.
- Die Signaturen von `MoveToTrashEvent::getNode()` und `NodeRestoredEvent::getTarget()` wurden vor der Verwendung im laufenden Test-Nextcloud gegen die Quelle geprüft, nicht aus dem Gedächtnis übernommen.

## Next Phase Readiness

- **Plan 03-04 (Share und Subtree)** kann direkt aufsetzen: der Verzweigungspunkt in `describe()` ist gebaut und der `acl`-Zweig hängt sich an dieselbe Stelle; `_job()` prüft bereits je Art, sodass die leere Nutzerliste eines Unshare nur noch eine weitere Ausnahme in derselben Bedingung ist. `replace_acl(file_id, [])` existiert und ist getestet.
- **Plan 03-12 (ETag-Abgleich)** hat mit `drop_document`, `forget_acl` und `tombstone` genau die drei Aufräumschritte, die er nach einem Fund "lokal vorhanden, in der Seite nicht mehr da" braucht. Achtung: es gibt genau einen `IndexWriter` im Prozess, der Abgleich muss den des Pollers benutzen oder über die Queue gehen.
- **Phase 4 (Diagnose)** kann "war da, ist weg" ausweisen, weil die Zeile mit ihrem letzten Verdikt stehen bleibt und nur `deleted_at` trägt.
- **Bewusst offene Lücke:** ein gelöschter Ordner erzeugt weiterhin keine Zeile für seine Nachkommen. Der Weg dorthin ist der Teilbaum-Job aus Plan 03-04, die Rücklage der ETag-Abgleich aus 03-12. Beides steht als Kommentar im Code, nicht nur hier (T-03-305).

## Self-Check: PASSED

Alle dreizehn genannten Dateien liegen vor, alle sechs Commits sind im Branch
`worktree-agent-03-03` auffindbar, und der Plan hat keine einzige Datei gelöscht.

---
*Phase: 03-aktualit-t-und-ocr*
*Completed: 2026-09-01*
