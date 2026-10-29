---
phase: 40-haertung-und-store-einreichung-1-6-0
plan: 06
verified: 2026-10-29T09:30:00Z
status: passed
score: 10/10 must-haves verified
code_head: 4ed0f846
docs_head: 0b7ea28b
overrides_applied: 0
warnings:
  - id: W-1
    topic: "Häufungs-Schwelle E-40-06-02 kann den #36-Loop bei gehäuften kaputten Dateien wieder herstellen"
    detail: "Liegen min(5, claimed) Dateien desselben kaputten Mounts im selben Pass (bei claimed >= 2), eskaliert der Pass zu _GatewayDown mit Gutschrift; der id-sortierte Claim holt denselben Kopf-Batch erneut, das give-up-Budget greift nie. Beispiele: Economy-OCR-Pass mit 2 Scans auf dem Mount, Queue-Rest von 2 bis 4 Dateien auf dem Mount, oder 5 von 32 nebeneinanderliegenden ids. Verhalten ist plangemäß (Spezifikation), das Restrisiko steht aber weder im Plan noch in der SUMMARY. Owner-Entscheid nötig."
  - id: W-2
    topic: "Grenzfall claimed 2 bis 4 und gemischte Status ohne Test im Repo"
    detail: "test_poller.py prüft 6/6 (eskaliert), 4/6 (bleibt Urteil) und 1/1 (keine Eskalation). Der min(5, claimed)-Zweig für claimed < 5 und die Nicht-Addition verschiedener Status sind ungetestet. Verifier-Sonde (temporär, nicht committet) belegt korrektes Verhalten: 2/2 und 3/3 eskalieren, 2/3 bleibt Urteil, 3x500+3x401 von 8 bleibt Urteil, 5x500 von 32 eskaliert."
---

# Plan 40-06: Verifikationsbericht (goal-backward)

**Ziel:** Issue #36 (budachst: eine Datei auf kaputtem Share-Mount, Gateway-500, Pass-Abbruch mit Gutschrift, Endlos-Loop) gelöst nach B/A/C/D/E plus Suchpfad-Härtung ohne PHP-404, dazu Kandidat F aus #19 (/status blockiert nie auf filled_languages).
**Geprüft:** Code-Kopf 4ed0f846 (HEAD = origin/main = 0b7ea28b, die beiden Doku-Commits danach berühren nur .planning).
**Status:** passed, mit zwei Warnungen (W-1 Owner-Entscheid, W-2 Testlücke).
**Re-Verifikation:** nein, erste Verifikation.

## Must-haves

| # | Must-have | Verdikt | Beleg |
|---|-----------|---------|-------|
| 1 | Gateway-Fehler für genau eine Datei (>= 400, nicht 404/998, nicht 502/503/504) endet failed/gateway_error, Rest des Passes normal, kein Unlock/Refund (B) | VERIFIED | Kette im Code: client.py:335-343 `_stream_file` (404/998 None, `_OUTAGE_STATUS` NextcloudException, sonst `raise GatewayRefused(status)`), fetch_file_stream:397-402 reicht durch; poller.py:2131-2139 `_fetch_once` fängt GatewayRefused VOR dem generischen `except Exception` (kein _GatewayDown), verwirft scratch, loggt Status+file id, re-raise; poller.py:1582-1596 Content-Zweig `_count_refusal` + `_collect(failed(GATEWAY_ERROR))` (kein unlock); poller.py:1761-1766 OCR-Zweig analog; `_collect` (:2227) sortiert in `failed` mit Reason, `_record_verdicts` schreibt store.record, `queue.acknowledge(done, failed, ...)` (:1274). Test `test_one_refused_file_is_a_verdict_and_the_rest_of_the_pass_goes_on` (3er-Batch, eine Datei 500): ROUND_WORKED, (indexed, failed) = (2, 1), acknowledged `[([91, 93], {92: "gateway_error"})]`, `unlocked == []`, Store-Zeile failed/gateway_error, Index enthält 4711/4713, Logzeile mit 500 und 4712, ohne Name/Pfad. Grün lokal. Client-Raster: `test_an_answer_about_one_file_is_a_refusal_with_its_status` [500,401,403,422,423] grün. OCR seriell und unter 2 Slots grün. |
| 2 | Echter Ausfall bleibt erkennbar: 502/503/504, Transportfehler und Häufung desselben Status -> gateway_unavailable mit Gutschrift, keine Urteile | VERIFIED (W-1, W-2) | `_OUTAGE_STATUS = {502,503,504}` (client.py:160); Transportfehler landen im `except Exception` -> `_GatewayDown` (poller.py:2140-2151); `_work` -> `_abort` (:1214-1217). Schwelle `_count_refusal` (:2332-2349): `claimed >= 2 and count >= min(5, claimed)` je Status, Zähler je Pass zurückgesetzt (:1175-1176). Tests grün: 503-Variante, ConnectError, 6x401 eskaliert (nichts acknowledged, alle unlocked), 4x500 von 6 bleibt Urteil, 1/1 eskaliert nie, test_a_proxy_answer_stays_an_outage [502,503,504]. Grenzfall claimed < 5 nur per Verifier-Sonde belegt (W-2). |
| 3 | HTTP-Status im Container-Log (A); 422-Zweig NC-seitig mit statischer Logzeile (E) | VERIFIED | poller.py:2146-2150 "content gateway did not deliver, %s with http status %d" (Wortanfang unverändert); :2136-2138 "content gateway refused one file, http status %d for file id %d". GatewayController.php:104-109 `warning('Findling: a file could not be opened for reading, answered 422', ['fileId' => $fileId])`. Tests: `test_the_outage_line_names_the_http_status` grün; `testAFileThatCannotBeOpenedAnswers422AndLeavesOneLogLine` in CI-PHPUnit (902 Tests OK, Lauf 40834773386). |
| 4 | Nach _abort ist der Writer-Puffer leer (C); Rollback unter Lock, Rollback-Fehler verhindert nie das Unlock | VERIFIED | writer.py:440-462 `rollback()` in `with self._lock`, `_require_open().rollback()`, Zähler auf 0. poller.py:2376-2386: Rollback per `asyncio.to_thread` in try/except Exception, danach unbedingt `queue.unlock(sorted(self._held))`. Tests grün: `test_an_aborted_pass_leaves_nothing_pending_in_the_writer` (pending 0, flush 0 Dokumente, Index leer), `test_an_abort_hands_the_rows_back_even_when_the_rollback_fails` (werfendes Double, unlocked [[91, 92]]), `test_a_rollback_drops_the_pending_batch_and_keeps_what_was_committed`, `test_the_writer_keeps_working_after_a_rollback`. |
| 5 | ROUND_GATEWAY_UNAVAILABLE sichtbar: Logzeile beim Abbruch, /status gatewayUnavailableSince, Satz auf der Admin-Seite (D) | VERIFIED | poller.py:2389-2393 WARNING + `_note_gateway_outage` (nur erster Abbruch der Strähne, :257-261); gelöscht bei ROUND_WORKED (:1277) und beiden ROUND_EMPTY-Ausgängen (:1062, :1075); ROUND_QUEUE_UNAVAILABLE lässt stehen. status.py:428 Feld, :626 Befüllung, :761 im State-DB-Zweig mitgetragen. AdminViewService.php:2756 `optionalCounter`; admin.php:300/590 Element mit `hidden` und statischem Satz; admin.js `gatewayLine` mit `t()` + `text()`/`shown()`, Feld im Fingerprint. Tests grün: Strähnen-Test, Leere-Queue-Test, beide BRANCHES in test_status_endpoint.py. |
| 6 | Budachst-Fall bleibt am Gateway 500 aus dem Throwable-Zweig, KEIN PHP-404 | VERIFIED | GatewayController.php hat keinen `use`/`catch` auf StorageNotAvailableException (grep ohne Kommentarzeilen: 0 Treffer, einziger Treffer ist der Kommentar :128). Throwable-Zweig nur um Kommentar ergänzt. Regressionstest `testAStorageThatIsNotAvailableAtTheOpenStaysA500AndNeverA404` (assertSame 500, assertNotSame 404, Logzeile "Findling: unknown error reading a file") und `testAnyOtherThrowableAtTheOpenIsStillA500` vorhanden, CI-PHPUnit OK (902 Tests, vorher 895 auf 631763b5). |
| 7 | Suche wirft bei kaputtem Mount kein 5xx; try/catch NUR an den drei SearchService-Suchstellen, readableFile/readableNode unverändert | VERIFIED | SearchService.php: catch an Suchschleife (:459-463), Ähnliche-Quelle (:604-608), Ähnliche-Kandidaten (:670-674), jeweils -> null. awk-Vergleich der Methodenkörper `readableFile` (3 Zeilen) und `readableNode` (7 Zeilen) gegen c75fb6cf: zeichengleich. test_php_acl_boundary.py grün. PHPUnit: drei Suchpfad-Fälle plus Gegenprobe `testTheSharedReadabilityQuestionStillThrowsOnABrokenMount` vorhanden, CI grün. |
| 8 | /status blockiert nie auf filled_languages: Cache sofort, single-flight-Hintergrund-Refresh, Messung außerhalb _LOCK, languagesFilledAsOf (F) | VERIFIED | resources.py:1026-1046 liest unter `_LOCK` nur `_FILLED`, startet bei Stale/Kaltstart `_start_fill_refresh` (Flag = Thread, :1060-1065). `_refresh_fill` (:1068-1105): `read_side()` (eigener kurzer Lock), `_measure_fill` OHNE Lock, Schreiben unter `_LOCK` nur bei gleicher Generation und index_dir und nie rückwärts, Flag im finally unter `_LOCK` gelöscht. Kaltstart definiert: `((), None)`. status.py:609-615 beide Felder aus einem Aufruf. Tests grün: `test_status_answers_at_once_while_a_fill_refresh_runs` (beide Polls < 2 s, paralleles read_side() < 2 s, genau ein Searcher), `test_the_measurement_does_not_hold_the_lock_of_the_reading_side` (`_LOCK.acquire` während der Messung gelingt), `test_a_stale_fill_level_is_answered_at_once_and_refreshed_once`, M-18-02-Test in test_read_side.py. |
| 9 | Beide Baumhash-Paare nachgezogen, `-k tree_hash` grün | VERIFIED | `pytest tests/test_measurement_scripts.py -k tree_hash`: 4 passed. Journalabsätze "Plan 40-06 (issue #36 A, B, C, D)", "Plan 40-06 (issue #19, candidate F)" und "the 422 log line, the search on a broken mount" vorhanden (verify-greps des Plans). |
| 10 | CHANGELOG [1.6.0] trägt #36-Fixes und Kandidat F ohne 404-Behauptung; deploy-harp.yml unberührt und grün | VERIFIED | [1.6.0]: Changed-Zeile #19, vier Fixed-Zeilen #36, kein "404". `git log c75fb6cf..HEAD -- .github/workflows/` leer (kein Workflow geändert). `gh run list --commit 4ed0f846`: alle 8 Workflows success (PHP and store metadata gates 40834773386, OpenSSF Scorecard 40834773542, Security scans 40834773406, Multi-arch image 40834773362, Python gates 40834773368, Integration 40834773510, Resilience 40834773614, HaRP deploy 40834773430). |

**Score:** 10/10

## Weitere Prüfpunkte des Auftrags

- **Testisolation:** backend/tests/conftest.py:460-487 `forget_the_gateway_outage` (`reset_gateway_outage()` vor und nach) und `quiesce_the_fill_refresh` (`join_fill_refresh()` vor und nach), beide `@pytest.fixture(autouse=True)`. VERIFIED.
- **l10n:** 16 Kataloge (8 .json + 8 .js) tragen den Satz, alle 5 docs/l10n-{french,spanish,italian,dutch,portuguese}.md, 0 Treffer in docs/l10n-catalogues.md. de/de_DE: "Das Content-Gateway hat beim letzten Indexierungslauf nicht geantwortet. Die betroffenen Dateien bleiben in der Warteschlange und werden erneut versucht; die Suche antwortet weiter." (der Satz enthält keine umlautpflichtigen Wörter, keine ASCII-Ersatzschreibung). Keine U+2013/U+2014 in den hinzugefügten Zeilen des gesamten Diffs c75fb6cf..4ed0f846. test_admin_ui_contract.py grün. VERIFIED.
- **Commit-Reihenfolge:** RED vor GREEN je Task (6b51f59d vor 6880fa1e, 3ef146d1 vor 910293ce, 2e4fad73 vor ab34d601), Autor durchgehend street1983nk <k.cherif@outlook.de>.
- **Schuld-Marker:** keine TBD/FIXME/XXX/TODO/HACK in hinzugefügten Zeilen unter backend/src, php/lib, php/js, php/templates.

## Lokale Testläufe (seriell, 1,56 GB frei, kein docker)

| Modul | Ergebnis |
|---|---|
| tests/test_poller.py | 210 passed, 1 skipped |
| tests/test_gateway_client.py + tests/test_index_writer.py | 86 passed |
| tests/test_status_endpoint.py + tests/test_read_side.py | 134 passed |
| tests/test_admin_ui_contract.py + tests/test_php_acl_boundary.py | 208 passed |
| tests/test_measurement_scripts.py -k tree_hash | 4 passed |
| Gezielte Auswahl (-rA, 26 Fälle B/A/C/D/F) | 26 passed |
| Verifier-Sonde Schwellen-Grenzfälle (temporär, gelöscht) | 5 passed |

PHPUnit nur in CI: Lauf 40834773386, Job "PHPUnit over the companion app", `OK (902 tests, 3994 assertions)`.

## Warnungen

### W-1: Gehäufte kaputte Dateien stellen den Loop wieder her (Owner-Entscheid)

Die Schwelle E-40-06-02 behandelt min(5, claimed) gleiche Ablehnungen (claimed >= 2) als Ausfall mit Gutschrift. Ein kaputter Re-Share enthält in der Regel mehr als eine Datei, und deren ids liegen oft nebeneinander. Dann gilt: der Pass eskaliert, die Zeilen gehen mit Gutschrift zurück, der id-sortierte Claim holt denselben Kopf-Batch, das give-up-Budget greift nie. Das ist genau die #36-Schleife, nur ab 5 betroffenen Dateien im 32er-Pass bzw. schon ab 2 bei kleinen Pässen (Economy-OCR mit 2 Scans, Queue-Rest von 2 bis 4 Dateien). Sichtbar ist es jetzt immerhin (gatewayUnavailableSince, Admin-Satz, Logzeile mit Status). Die Sonde belegt: 2 von 2 und 3 von 3 mit 500 enden als ROUND_GATEWAY_UNAVAILABLE mit Unlock.

Mögliche Auswege zur Entscheidung: Schwelle nur für 401/403 (Auth-Ausfall), 500 nie eskalieren; oder Eskalation erst ab einem Mindestanteil UND einer Mindestzahl (z. B. >= 5 und >= 50 % von claimed); oder nach N aufeinanderfolgenden eskalierten Pässen mit identischem Kopf-Batch die Gutschrift aussetzen. Der Plan und die SUMMARY nennen dieses Restrisiko nicht.

### W-2: Testlücke am Grenzfall der Schwelle

Kein Repo-Test deckt claimed 2 bis 4 (der `min(..., claimed)`-Zweig) und die Nicht-Addition verschiedener Status ab; ebenso keine Eskalation unter mehreren OCR-Slots. Das Verhalten stimmt laut Sonde, ein Regressionsschutz fehlt.

## Info (kein Befund)

- Kaltstart: languagesFilled steht bis zum ersten Refresh leer, die Admin-Zeile lautet dann "... de switched on, with text in the index." mit leerem Teil. Vorübergehend und in der SUMMARY für die Owner-Runde 40-04 genannt.
- Der Admin-Satz "did not answer" erscheint auch bei einer Häufungs-Eskalation (z. B. 401 für alles), obwohl das Gateway dann geantwortet hat. Wortlaut geht ohnehin in Block G der Owner-Runde.
- Der flush()-Docstring in writer.py ("the batch stays pending and the next flush commits it") stimmt nach einem PAUSED_LOW_DISK-Flush nicht mehr ganz, weil `_abort` den Puffer jetzt zurückrollt; die Zeilen kommen per Unlock zurück, also kein Datenverlust.
- Laut SUMMARY wurde in #36 bereits ein Fix-Link-Kommentar gepostet (6492666744), bevor der Owner "Fix-Link nach Store-Release" entschied. Nicht vom Verifier geprüft oder angefasst; Entscheidung liegt beim Owner.

---

_Verifiziert: 2026-10-29_
_Verifier: Claude (gsd-verifier)_
