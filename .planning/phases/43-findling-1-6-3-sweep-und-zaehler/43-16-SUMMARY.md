---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 16
subsystem: backend (store, nc, worker)
tags: [doc-key, issue-25, d-43-14, backfill, verify]
requires:
  - 43-15 (GET /reconcile/doc-keys, docKey in den Aufträgen, DOC_KEY_BAND = 200)
provides:
  - "files.doc_key (TEXT, nullable) und Index files_storage_doc_key (storage_id, doc_key)"
  - "Store.set_doc_keys, missing_doc_keys, existing_doc_keys, doc_keys_missing, doc_keys_unresolved, reset_doc_keys; repo.valid_doc_key, repo.DOC_KEY_NONE"
  - "FileMeta.doc_key, QueueJob.doc_key"
  - "nc/files.py: DOC_KEY_BAND, DocKeyAnswer, FileList.doc_keys; nc/client.py: doc_keys"
  - "worker/doc_keys.py: DocKeyBackfill, note_coverage_call(), doc_keys_corrected(), DOC_KEY_MARK = doc_key_backfill_after"
affects:
  - 43-03 (Zählung über doc_key, Sentinel '' als Einzeldokument)
  - 43-04 (/coverage ruft note_coverage_call(), liest doc_keys_missing/doc_keys_unresolved/doc_keys_corrected)
  - 43-12 (K1: Durchsatz unten)
tech-stack:
  added: []
  patterns:
    - "additive Spalte per ALTER TABLE vor schema.sql, in BEGIN IMMEDIATE (zwei Schreiber, eine Spalte)"
    - "eigener Hintergrundtask mit Reconcile-Schnittstelle (arm/silence/hold_for_backup/in_flight), am Pause-Koordinator über attach_reconcile"
key-files:
  created:
    - backend/src/findling/worker/doc_keys.py
    - backend/tests/test_doc_keys.py
  modified:
    - backend/src/findling/store/repo.py
    - backend/src/findling/store/schema.sql
    - backend/src/findling/nc/queue.py
    - backend/src/findling/nc/files.py
    - backend/src/findling/nc/client.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/main.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Backfill als eigener Task in main.py, nicht im Reconcile: läuft auch bei abgeschaltetem Reconcile, sonst bliebe /coverage dauerhaft counting"
  - "Spalte vor executescript per ALTER TABLE, weil der neue Index in schema.sql die Spalte braucht"
  - "Dreimal unvollständig: Halbierung sofort in derselben Runde bis zu Einzel-IDs; übrig bleibende IDs bekommen '' (set aside)"
  - "Prüflauf zählt auch '' -> Schlüssel und Schlüssel -> '' (absent) als Korrektur; set-aside-IDs behalten im Prüflauf ihren Wert"
  - "docKeysCorrected ist ein Prozesszähler (kein Meta-Schlüssel, STOPP-Regel); die Ruhe-Merkmal-Info 'Durchlauf hatte Korrektur' liegt im Speicher"
  - "Ruhepause = 86.400 s ab Durchlaufende (Format idle<epoch> im verify-Teil des Meta-Werts)"
  - "embed-Aufträge schreiben keinen doc_key (urteilen nichts); content, ocr, metadata über record/refresh_meta, acl über set_doc_keys"
metrics:
  duration: "ca. 95 min (davon ca. 15 min Volltestsuite)"
  completed: 2026-11-07
  tasks: 2
  files: 10
---

# Phase 43 Plan 16: Dokumentschlüssel je Zeile und begrenzter Backfill Summary

Der Container speichert jetzt je Zeile `files.doc_key` (sha256-hex des internen Pfads aus PHP), übernimmt ihn aus jedem Auftrag und füllt Altzeilen bandweise über `GET /reconcile/doc-keys` nach; ein stetiger Prüflauf ersetzt veraltete Schlüssel. Kein Reindex, `SCHEMA_VERSION` bleibt "2".

## Umsetzung

- **Schema:** schema.sql trägt `doc_key TEXT` und `files_storage_doc_key`. `open_store` ruft vorher `_add_doc_key_column` (PRAGMA table_info, ALTER TABLE nur bei fehlender Spalte, in BEGIN IMMEDIATE). Kein neues Merkmal, keine Zeile geändert, Kommentar an SCHEMA_VERSION.
- **Intake:** `QueueJob.doc_key` aus `docKey` (nur `^[0-9a-f]{64}$`, eigener Prüfer in nc/queue.py, kein Store-Import), `_meta_of` reicht ihn als `FileMeta.doc_key` weiter. `record` schreibt `COALESCE(excluded.doc_key, files.doc_key)`, `refresh_meta` `COALESCE(?, doc_key)`, der acl-Zweig `set_doc_keys` bei vorhandenem Schlüssel (W4). Der Store prüft das Muster ein zweites Mal.
- **Lesen:** `FileList.doc_keys` in Bändern zu `DOC_KEY_BAND = 200` (Parität zum PHP-`DOC_KEY_BAND`, Test), ids als ein Komma-Wert. 404 -> `route_missing`, andere Fehler -> None mit Klassenname. Nur gefragte IDs, nur Hex-Werte; `unanswered`/`complete` gegen die gefragten IDs (W8). Leeres `keys` darf als `[]` kommen.
- **Worker:** `DocKeyBackfill` (25 Bänder je Runde, 1 s Pause, Tick 300 s). Meta `doc_key_backfill_after` = `<gen>:<cursor>:<verify>` bzw. `idle<epoch>`, Zweiteilform wird gelesen und dreiteilig geschrieben. Abweichende oder fehlende Generation: `reset_doc_keys()` einmal. Missing > 0: Backfill, sonst Prüflauf. Cursor nach jedem Band; leerer Rest hinter dem Cursor bei missing > 0: zurück auf 0 (R2). 404: Cooldown 300, 600, 1200, 2400, 3600 s, eine Logzeile je Stufe, Ende durch `note_coverage_call()` nach dem 404 (W3, W11). Unvollständig: Runde unavailable, beim dritten Mal Halbierung bis Einzel-IDs, Rest '' plus Warnzeile "set aside" (W12, W15). Prüflauf: Abweichung überschreiben, `docKeysCorrected`, voller Durchlauf ohne Korrektur ruht einen Tag, mit Korrektur sofort von vorn; setzt nie NULL. Backup-Pause zwischen Bändern. Logzeilen nur Zahlen.
- **main.py:** `_DOC_KEYS = DocKeyBackfill()`, `_PAUSE.attach_reconcile(_DOC_KEYS)`, in `_armable_tasks`, `_guarded_doc_keys`, Stopp mit `RECONCILE_STOP_SECONDS` und `aclose()`.

## Für 43-03/43-04

- Zählung: `doc_key IS NULL` = fehlt (counting), `''` = Einzeldokument über (storage_id, file_id).
- /coverage: `note_coverage_call()` bei jedem Aufruf; `Store.doc_keys_missing()`, `Store.doc_keys_unresolved()`, `doc_keys_corrected()` (Prozesszähler).

## TDD

- RED 94484ae1: tests/test_doc_keys.py, Sammelfehler (ImportError, Modul fehlt). Ruff war grün nur mit einem `noqa: I001` (Sortierung kannte das Modul noch nicht), im GREEN-Commit wieder entfernt; pyright/vulture im RED-Stand naturgemäß rot.
- GREEN 308e8ebb: 63 passed in tests/test_doc_keys.py.

## Gates und Tests

- ruff check: All checks passed; ruff format --check: 250 files already formatted; pyright (latest): 0 errors; vulture: leer.
- Volltestsuite seriell mit den --ignore aus 40-01 (6 GB frei): `test_[a-m]*` 3276 passed, 43 skipped; `test_[n-r]*` 1982 passed, 278 skipped; `test_[s-z]*` 1565 passed, 10 skipped. (Ein erster Lauf `test_[n-z]*` lief in mein 590-s-Timeout bei 93 % ohne einen Fehler, darum geteilt neu.)
- Baumhash PACKAGE: 81 -> 82 Dateien, c9147c42... -> 91a917c4030491f1ea37c746384cc21396157d293e89b00552087c851d6827a4. Zweimal gerechnet (Rezept 40b-baumhash.py und find | LC_ALL=C sort | tr -d '\r' | sha256sum), Positivkontrolle über `git archive HEAD` vor dem Schritt: c9147c42. PHP-Paare unberührt.

## Messung Backfill-Durchsatz (K1 in 43-12)

Skript im Scratchpad, 190.000 Zeilen ohne Schlüssel, Fake-Route ohne Netz, Windows-Laptop, parallel zur Testsuite (also eher pessimistisch):
- ohne Pause: 38 Runden, 950 Bänder in 31,8 s, also rund 1.790 Bänder/min reine Container-Kosten; Runde im Mittel 0,81 s, höchstens 3,2 s (erste Runde mit Generations-Reset).
- erster Prüflauf-Runde (5.000 Zeilen): 0,06 s.
- im Betrieb (25 Bänder, 1 s Pause, Tick 300 s): rund 25 Bänder je 325 s, also etwa 4,6 Bänder/min oder 5.000 Zeilen je Runde; 190.000 Zeilen in 38 Runden, rund 3,4 h plus PHP-Zeit je Band (eine getFileByIds-Abfrage über 200 IDs). Ein voller Prüfdurchlauf dauert gleich lang, danach ruht er einen Tag.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] nc/client.py und worker/poller.py nicht in files_modified**
- client.py braucht die Aufruffunktion `doc_keys` (die Lesefunktion darf nur dort die Session ansprechen); poller.py musste `doc_key` in `_meta_of` und im acl-Zweig weitergeben, sonst käme der Auftragsschlüssel nie an. Commit 308e8ebb.

**2. [Rule 1 - Bug] Testaufbau**
- Ein eigener Test vergaß den Meta-Wert und lief deshalb in den Generations-Reset; Test korrigiert (GREEN-Commit), Implementierung unverändert.

**3. Abweichung in der Form**
- Plan nennt `set_doc_keys(keys, absent)`, `missing_doc_keys(after, limit)`, `existing_doc_keys(after, limit)`: umgesetzt als Keyword-Argumente `after=`, `limit=`.
- Die `/coverage`-Route selbst entsteht erst in 43-04; hier nur der Haken `note_coverage_call()` und die Zähler. Der Test für W11 ruft den Haken direkt.
- embed-Aufträge schreiben keinen doc_key (keine Urteils-Schreibstelle im Poller); der Prüflauf deckt den Fall ab.

Sonst Plan wie geschrieben.

## Threat Flags

Keine neue Oberfläche außer der GET-Route aus 43-15 (nur IDs hinaus, nur Hex herein, Muster doppelt geprüft).

## Hinweise

- STATE.md/ROADMAP.md nicht angefasst (Koordinator, wie 43-02/43-15). 43-FREIGABEN.md existiert noch nicht, nicht angelegt. Nichts gepusht.

## Self-Check: PASSED

- backend/src/findling/worker/doc_keys.py und backend/tests/test_doc_keys.py vorhanden; grep-Prüfungen des Plans (doc_key_backfill_after, `DOC_KEY_GENERATION: Final = 1`, "doc key verify", `DOC_KEY_INCOMPLETE_RETRIES: Final = 3`, `SCHEMA_VERSION: Final = "2"`) treffen.
- Commits 94484ae1 (test) und 308e8ebb (feat) im Log, Autor street1983nk <k.cherif@outlook.de>, kein Trailer, 0 Treffer für closes/fixes/resolves #N, keine Löschungen.
