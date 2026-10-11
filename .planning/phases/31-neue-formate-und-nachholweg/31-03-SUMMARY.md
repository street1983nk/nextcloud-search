---
phase: 31-neue-formate-und-nachholweg
plan: 03
subsystem: Download-Pfad (nc/client.py, worker/poller.py)
tags: [pol-02, f-29-03, d-29-04, shortread, stale-size, a8]
requires:
  - phase: 31-02
    provides: "docs/formats.md (hier um einen Abschnitt erweitert)"
provides:
  - "ShortRead mit written und content_hash (Konstruktor mit Schlüsselwörtern, Meldung unverändert)"
  - "_fetch_file: zweimal gleich kurz (Länge und Hash) = echte Datei, Scratch des zweiten Versuchs wird weitergereicht, kein dritter Download"
  - "docs/formats.md Abschnitt 'Stale file cache size' mit Logzeile und Restrisiko A8"
affects: [31-11 Nachholweg (holt bereits als repeatedly_stuck aufgegebene Zeilen nach, D-31-02), 36 REL-05]
tech-stack:
  added: []
  patterns: ["Ausnahme mit Feldern, die der Aufrufer aus seiner eigenen Senke füllt (Client zählt, Poller hasht)"]
key-files:
  created: []
  modified:
    - backend/src/findling/nc/client.py
    - backend/src/findling/worker/poller.py
    - backend/tests/test_poller.py
    - backend/tests/test_gateway_client.py
    - backend/tests/test_measurement_scripts.py
    - docs/formats.md
    - backend/tests/test_public_artifacts.py (Nebencommit)
    - php/lib/Service/AdminViewService.php (Nebencommit, nur Kommentar)
decisions:
  - "Keine Längenausnahme (auch genau 1 MiB zweimal gleich gilt als echte Datei); Restrisiko A8 in Docstring, docs/formats.md und hier benannt; Owner-Veto möglich"
  - "Der Client hasht nicht; _stream_into wirft ShortRead neu mit written und content_hash aus dem _HashingSink, damit verglichen wird, was wirklich in der Senke ankam"
  - "Die Größe des _Read ist die tatsächliche (written), damit Extraktor und judge (0 Bytes -> empty_file) die echte Datei sehen; _meta_of behält die Größe aus dem Dateicache"
metrics:
  duration: "ca. 85 min (davon 11 min volle Suite lokal, ca. 20 min CI)"
  completed: 2026-10-11
  tasks: 2
  files: 8
---

# Phase 31 Plan 03: Veraltete Dateigröße im Dateicache (POL-02) Summary

Kommt eine Datei zweimal kürzer als die Dateicache-Größe, aber mit gleicher Bytezahl und gleichem Inhalts-Hash, wird der zweite Download als die echte Datei extrahiert und bekommt ein normales Urteil, statt nach drei Auslieferungen als `failed(repeatedly_stuck)` zu enden; zwei verschiedene kurze Antworten bleiben der vorübergehende Fehler von D-29-04.

## Task 1: Regressionstests F-29-03 (RED)

- Neue Attrappe `_AnswerGateway` in test_poller.py (eine vorbereitete Antwort je Aufruf, ShortRead wie der Client, wenn kürzer als `expected`), Hilfsfunktion `_text_of(length, last=...)`.
- Neue Tests in test_poller.py:
  - `test_the_same_short_answer_twice_is_the_file_and_gets_its_verdict` (700 von 1000, indexed, genau zwei Downloads, Hash in state.db, Scratch leer, Logzeile wörtlich, kein Name/Pfad/file id in Logzeilen)
  - `test_two_different_short_answers_stay_a_passing_fault_without_a_verdict[different-length|same-length-different-bytes]` (700/650 und 700/700 mit anderem letzten Byte)
  - `test_a_short_read_that_leaves_the_fetch_carries_the_numbers_of_the_sink`
  - `test_an_empty_answer_twice_is_an_empty_file_and_never_stuck` (0/0 bei 10 -> failed empty_file)
  - `test_the_same_short_answer_of_exactly_one_mebibyte_is_the_file_as_well` (1 048 576 bei 2 000 000)
  - `test_an_ocr_row_with_the_same_short_answer_twice_is_read` (OCR-Spur, Extraktor bekommt Größe 700)
  - `test_the_stale_file_cache_size_is_documented_with_its_limit` (Doku-Abschnitt nennt A8, repeatedly_stuck und dieselbe Logzeile wie der Code)
- test_gateway_client.py: `test_a_short_read_carries_the_byte_count_and_a_place_for_the_hash`.
- RED, Schritt 1 (ohne jede Codeänderung): 12 failed, 9 passed; alle neuen Fälle und die vier bestehenden Short-Tests rot an `TypeError` (Schlüsselwort `written` fehlt), der Gateway-Test an `AttributeError: 'ShortRead' object has no attribute 'written'`.
- RED, Schritt 2 (nur ShortRead-Felder eingebaut, Poller unverändert): **5 failed, 16 passed**, rot am Verhalten: `..._same_short_answer_twice_is_the_file...` (`assert 0 == 1`, indexed), `..._carries_the_numbers_of_the_sink` (`assert '' == 'ac65018a...'`), `..._empty_answer_twice...` (`failed 0 == 1`), `..._exactly_one_mebibyte...` (`indexed 0 == 1`), `..._ocr_row_with_the_same_short_answer...` (`[] == [700]`).

## Task 2: Vergleich beider Versuche (GREEN)

- client.py: `ShortRead(message, *, written, content_hash="")`; `_stream_file` übergibt `written`. Docstring nennt POL-02 und dass der Poller den Hash füllt.
- poller.py: `_stream_into` fängt ShortRead und wirft ihn neu mit `sink.written` und `sink.content_hash` (`from cut`). `_fetch_once(job, *, same_as=None)`: bei ShortRead mit gleicher `(written, content_hash)` wie `same_as` bleibt die Scratch-Datei, Rückgabe `_Read(path, size=written, content_hash)`, Logzeile `the file cache names a stale size, the same %d of %d bytes arrived twice` (written, job.size); sonst wie bisher verwerfen und weiterwerfen. `_fetch_file` reicht den ersten ShortRead als `same_as` an den zweiten Versuch. Docstring mit F-29-03, POL-02 und Restrisiko A8; die Kommentare an beiden Rückgabe-ohne-Urteil-Stellen sagen "zwei verschiedene kurze Antworten".
- docs/formats.md: Abschnitt `## Stale file cache size` (was passiert, die Logzeile, die Grenze A8).
- GREEN: 21 passed über die Short-/Stale-Fälle; volle Suite lokal **5017 passed, 25 skipped** (636 s).
- Gegenproben (je zurückgesetzt, danach wieder 21 passed):
  - Vergleich auf "immer echte Datei" (`if same_as is not None:`): 6 rot, darunter beide `two_different_short_answers`-Fälle, die drei bestehenden "stays short"-Tests und `..._numbers_of_the_sink`.
  - Vergleich nur nach Länge: `[same-length-different-bytes]` rot.
  - Zusätzliche Logzeile mit `job.title`: `assert 'Gehaltsabrechnung' not in 'probe Gehaltsabrechnung Mueller.txt'` rot.
  - Doku-Überschrift umbenannt: `test_the_stale_file_cache_size_is_documented_with_its_limit` rot (`IndexError`).
- Akzeptanz: `grep content_hash` trifft client.py und poller.py; `grep "1_048_576\|1048576" poller.py` leer; `## Stale file cache size` in docs/formats.md nennt A8.
- PACKAGE_TREE_HASH_TODAY `ee635770...90b13dd` (74 Dateien) mit Journalabsatz "Plan 31-03 (POL-02, F-29-03)".

## Restrisiko A8 (Entscheid nach Plan-Check, Owner-Veto möglich)

Gleich kurz und gleicher Hash gilt immer als echte Datei, ohne Längenausnahme. Ein Proxy, der jede Antwort byte-genau an derselben Stelle kappt, liefert zweimal dasselbe; die Datei wird dann mit dem gekappten Inhalt indexiert statt aufgegeben. Erkennbar an der Logzeile mit beiden Zahlen; Abhilfe ist der Proxy. #18 Fall 2 (Ursprung von D-29-04) schnitt nicht reproduzierbar gleich ab [ASSUMED]. Benannt im Docstring von `_fetch_file` und in docs/formats.md.

## Nebencommit (Zählungen in Kommentaren)

- Gezählt mit dem Scanner des Gates selbst (`matches_of(VOCABULARY_FAMILY, text_of(...))`), Positivkontrolle auf dem Stand vor 31-02 (0b78d646): Spanisch 79, Italienisch 10, also die Zahlen aus 31-02. Auf HEAD: **Spanisch 84** (31-02 brachte fünf Treffer dazu; alle sind archivo/archivos), **Italienisch 10** (archivio 1, archiviazione 9). Die Ausnahmegründe sagen jetzt 84 und ten; der zehnte italienische Treffer kam laut Verlauf mit 1429eebc (#25, 09.10.2026, Wort archiviazione), der Grund nennt das.
- AdminViewService.php REASON_TEXT: 25 Codes, deckungsgleich mit FileStateService::REASONS (25) und dem Python-Enum Reason (25). Docblock sagt "Twenty-five codes", nennt den Drift-Test der Backend-Seite, "twenty calls" -> "twenty-five calls". PHP_TREE_HASH_TODAY `0d4206ab...af079a0` (90 Dateien) mit Journalabsatz.
- Gates vor dem Commit: ruff, format, pyright, vulture grün; test_measurement_scripts, test_public_artifacts, test_admin_ui_contract 704 passed; test_extract_errors, test_v14_zelle 137 passed.

## Commits

| Commit | Inhalt |
|---|---|
| 4bd227a7 | fix(31-03): a stale file cache size no longer ends as repeatedly_stuck |
| 441637e7 | chore: stale counts in two comments follow the code |

## Gates und CI

- Lokal vor 4bd227a7: ruff check grün, ruff format (201 Dateien) grün, pyright latest 0 Fehler, vulture grün, volle Suite 5017 passed, 25 skipped.
- Push `4ae97302..441637e7` (beide Commits), alle acht success: Python gates **38098844595** (5028 passed, 14 skipped), PHP and store metadata gates **38098844716**, Integration **38098844728**, Resilience **38098844772**, HaRP deploy **38098844641**, Multi-arch image **38098844643**, Security scans 38098844615, OpenSSF Scorecard 38098844742.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Bestehende Short-Attrappe hätte nach dem Fix den falschen Fall geprüft**
- **Found during:** Task 1
- **Issue:** `_ShortGateway` schnitt bei jedem Versuch identisch nach 5 Bytes ab. Nach POL-02 ist das eine veraltete Cache-Größe und keine Störung; die drei "stays short"-Tests hätten dann nicht mehr D-29-04 geprüft.
- **Fix:** Jeder Schnitt endet ein Byte früher als der vorige (5, dann 4); Docstring sagt warum. Die Tests selbst sind unverändert und sind in der ersten Gegenprobe rot geworden.
- **Commit:** 4bd227a7

**2. Hash kommt aus dem Poller, nicht aus dem Client**
- Der Plan sagt "beim Werfen den Hash des _HashingSink mitgeben"; der Sink lebt in poller.py, `_stream_file` kennt ihn nicht. Deshalb wirft `_stream_into` ShortRead neu mit den Zahlen des Sinks; der Client lässt `content_hash` leer. Kein doppeltes Hashen.

**3. Zusatztests:** OCR-Spur und Doku-an-Code-Bindung, nicht im Plan, aber derselbe `_fetch_file`.

**4. Nebencommit:** Spanisch ist 84 statt der im Auftrag genannten 79 (79 war der Stand vor 31-02, oben belegt).

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-31-06 (nur Länge UND Hash, Test je Fall, Gegenprobe "nur Länge" rot), T-31-07 (Logzeile nur Zahlen, caplog-Test, Gegenprobe rot), T-31-08 (genau zwei Downloads, Tests zählen Aufrufe) umgesetzt; T-31-06b (A8) akzeptiert und dokumentiert.

## Requirements

POL-02 wirkt im Code und ist getestet (Inhalts- und OCR-Spur). Bereits als `repeatedly_stuck` aufgegebene Zeilen holt erst 31-11 nach (D-31-02).

## Offene Punkte

- Owner-Veto zu A8 möglich (dann Längenausnahme aus dem ersten Planstand).
- 31-11 nimmt die repeatedly_stuck-Zeilen in den Nachholweg.

## Self-Check: PASSED

client.py, poller.py, docs/formats.md und diese SUMMARY vorhanden; Commits 4bd227a7 und 441637e7 in der Historie, origin/main auf 441637e7; alle acht CI-Läufe success.
