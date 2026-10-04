---
status: resolved
trigger: "Nach vollstaendiger Erstindexierung plant der Container den gesamten Bestand ein zweites Mal ein (Lauf 8, 04.10.2026, Zelle L-T m7g.4xlarge, Abbruch 71 am Zaehltor mit 5427 statt 5000)"
created: 2026-10-04
updated: 2026-10-04
---

## Symptoms

DATA_START
- **Expected:** Nach Abarbeitung des gesamten Vorrats und vollstaendigem Crawl bleibt die Queue leer; bereits indexierte, unveraenderte Dateien werden nicht erneut eingeplant.
- **Actual:** Teilkorpus 5000/5000 eingebettet um 23:44:19Z. Unmittelbar danach Container-Meldung "work stock ran dry while the crawl is unfinished" und Nachschub-Anforderung. Danach kam der komplette Teilkorpus ERNEUT in oc_findling_queue (3037 Zeilen um 23:46Z, insgesamt 5000 Durchgaenge, alle mit Ergebnis "unchanged"). Die Zaehltor-Lesung bei Trigger+3600s fiel hinein: 5427 statt 5000, Abbruch 71.
- **Errors:** Keine Exceptions; die Log-Zeile "work stock ran dry while the crawl is unfinished" ist der Ausloeser-Marker.
- **Timeline:** Erstmals sichtbar in Lauf 8 (04.10.), weil dort der Worker (performance, 15 Slots) erstmals schneller war als der Crawl; in Lauf 7 und frueher lag der Crawl immer vorn, der Vorrat lief nie leer. Der Mechanismus existiert vermutlich seit Einfuehrung der Top-up-Route.
- **Reproduction:** Referenzaufbau der Abnahme-Anfahrt, Zelle L-T (performance/int8, 15 Slots) auf m7g.4xlarge; reproduziert sich, sobald der Vorrat vor Crawl-Ende leerlaeuft. Boxlos nachvollziehbar aus Code + committeten Rohdaten.
- **Belege:** docs/measurements/2026-10-abnahme-anfahrt/rohdaten/m7g.4xlarge/L-T-abbruch71-lauf8/ (insb. container-auszug.txt), 05-typwechsel-arm.txt Abschnitt Lauf 8, Commits e66ef86a/f432c5c7.
- **Verdachtsrichtungen (unbestaetigt):** first_index_scheduled/Crawl-Ende-Flag; StorageCrawlJob-Position (last_file_id) vs. Worker-Tempo; Top-up-Route, die den Crawl neu anstoesst oder von vorn laufen laesst.
- **Nutzer-Relevanz:** Auf grossen Instanzen (Millionen Dateien) ein kompletter sinnloser Zweitdurchgang mit "unchanged"-Durchgaengen nach der Erstindexierung (Cron-/DB-/CPU-Last).
- **Randbedingungen:** BOXLOS arbeiten (Box geparkt); Produkt-Fix erst nach bestaetigter Wurzelursache; TDD; nur lokal committen, kein Push.
DATA_END

## Current Focus

hypothesis: CONFIRMED. Der Reconcile (Container) laeuft waehrend der Erstindexierung, sobald der Vorrat unter die Ruhemarke 100 faellt, und liefert alle noch nicht gecrawlten Dateien als "stale" (requeue kind content). Der Crawl-Strang ist noch unterwegs (Cron-Takt) und erreicht die Teilkorpus-Dateien (hoechste file ids im lasttest-Home) erst 23:44Z; er stellt sie dann alle ein zweites Mal ein -> 5000 "unchanged".
test: TDD-Rot: Reconcile muss stehen bleiben, wenn die Stats-Antwort "crawling: true" meldet; QueueStats muss das Feld parsen.
expecting: neue Tests rot (Feld fehlt / Gate fehlt), bestehende gruen
next_action: ERLEDIGT (GREEN 04.10., Commits 13993fd9 + 01b1afce). Offen nur: PHPUnit in CI, Live-Nachweis bei der naechsten L-T-Anfahrt. Urspruenglicher Plan: (1) backend/src/findling/nc/queue.py: QueueStats.crawling: bool = False, DocumentQueue.stats parst payload.get("crawling") is True. (2) reconcile.py _quiet: stats.crawling -> Log "reconcile stands down, the crawl is unfinished" + ROUND_QUEUE_BUSY. (3) php CrawlAdvanceService: 3. Konstruktor-Param ILockingProvider $lockingProvider; public crawling(): bool = SchedulerJob-Zeile ODER Nicht-Recount-StorageCrawlJob-Zeile ODER isLocked(StorageCrawlJob::LOCK_NAME, LOCK_EXCLUSIVE). (4) QueueController::documentStats: array_merge(stats(), ['crawling' => crawlAdvanceService->crawling()]). (5) client.py queue_stats-Docstring + ggf. docs/reconcile.md. Gates: pytest gesamt, ruff, pyright (latest), vulture; PHP = CI-Vorbehalt.

tdd_checkpoint:
  test_file: "backend/tests/test_reconcile.py, backend/tests/test_queue_client.py, php/tests/Unit/CrawlAdvanceServiceTest.php, php/tests/Unit/QueueControllerTest.php"
  test_name: "test_reconcile_does_nothing_while_the_crawl_is_unfinished, test_a_crawl_that_starts_mid_round_stops_the_round_at_the_next_slice, test_stats_carries_whether_the_crawl_is_unfinished, test_a_stats_answer_without_a_true_crawling_flag_reads_as_no_crawl[4]; PHP: testNothingPlannedAndNoSliceRunningIsNoCrawl, testACrawlRowIsAnUnfinishedCrawl, testAWaitingSchedulerIsAnUnfinishedCrawl, testARunningSliceIsAnUnfinishedCrawl, testARecountRowAloneIsNoCrawl, testTheStatsCarryWhetherTheCrawlIsUnfinished, testAForeignExAppGetsNoStats"
  status: "green"
  failure_output: "AttributeError: 'QueueStats' object has no attribute 'crawling' / TypeError: QueueStats.__init__() got an unexpected keyword argument 'crawling'. Python: 34 failed, 92 passed (die 26 uebrigen Reconcile-Tests scheitern nur, weil _FakeQueue.stats jetzt crawling= uebergibt; werden mit dem Feld gruen). PHP nicht lokal lauffaehig (kein php), rot per Konstruktion: crawling() existiert nicht, Konstruktor hat 2 Params."

reasoning_checkpoint:
  hypothesis: "Der Zweitdurchgang entsteht, weil der Reconcile waehrend des unfertigen Crawls laeuft (Quiet-Gate misst nur die Vorratslaenge, nicht den Crawl-Zustand), jede noch nicht indexierte Datei als stale einreiht und der Crawl dieselben Dateien danach regulaer erneut einreiht."
  confirming_evidence:
    - "container-auszug.txt: Reconcile-stale-Summe 401 + 9x500 + 99 = 5000 = exakt das Teilkorpus, verteilt 22:51Z bis 23:41Z im 5-min-Takt"
    - "erste Reconcile-Runde 22:51:25Z walkte 106 Slices / 52549 Zeilen vor der ersten stale-Lieferung: Teilkorpus liegt am Ende der file-id-Reihe (Hardlinks nach dem loadtest-Bestand), also erreicht der file-id-geordnete Crawl es zuletzt"
    - "jede Folgerunde stale=500 bei 500er-Seite: keine dieser Dateien war dem Container bekannt, der Crawl hatte sie also noch nicht geliefert"
    - "Zweitwelle 23:44Z-23:50Z: claimed 5032, unchanged 5000, kein Reconcile-Round dazwischen (nur Stand-down 23:46:43Z) -> Quelle ist der Crawl (StorageCrawlJob enqueue, Selbstvorschub-Meldungen 23:44:19Z/23:49:28Z)"
    - "Lauf 7: Vorrat blieb ueber 100 (Crawl vorn), Reconcile stand down, kein Zweitdurchgang"
    - "reconcile.py _quiet: Kommentar 'An instance still working off its initial index ... must not also be walking its whole file list' - Absicht vorhanden, Messgroesse falsch"
  falsification_test: "Wenn der Crawl die Teilkorpus-Dateien vor 23:44Z selbst geliefert haette, haetten Reconcile-Seiten bekannte Dateien gesehen (stale < Seitenzahl) und die stale-Summe waere < 5000."
  fix_rationale: "Reconcile-Gate um 'Crawl unfertig' ergaenzen (Stats-Antwort meldet crawling = SchedulerJob- oder Crawl-Zeile vorhanden oder Crawl-Sperre gehalten). Dann liefert waehrend der Erstindexierung nur der Crawl; der Reconcile vergleicht erst nach Crawl-Ende und findet nur echte Abweichungen."
  blind_spots: "Kein Live-Nachweis (boxlos); PHP-Teil nicht lokal ausfuehrbar (CI); Fenster zwischen Zeilenentfernung und Nachfolger-Planung wird ueber die Sperre abgedeckt (isLocked), nicht live gemessen."

## Evidence

- timestamp: 2026-10-04
  checked: container-auszug.txt, alle reconcile-Zeilen
  found: "stale" je Runde 401 (22:51Z), 9x 500 (22:56Z bis 23:36Z), 99 (23:41Z); Summe 5000. Stand-down danach jeweils mit scheduled ~= dem gerade gelieferten Paket.
  implication: Der Reconcile, nicht der Crawl, hat das gesamte Teilkorpus beim ersten Mal geliefert.
- timestamp: 2026-10-04
  checked: backend/src/findling/worker/reconcile.py run_once/_walk/_quiet/_compare/_is_due
  found: Gate = nur stats.scheduled >= quiet_max (100); frischer Container ist sofort faellig (last_finished_at None); unbekannte Datei ohne excluded-Marke = stale -> requeue kind content, 500er-Seiten.
  implication: Waehrend der Erstindexierung ist jeder noch nicht gecrawlte Bestand "stale", sobald der Worker den Vorrat unter 100 leert.
- timestamp: 2026-10-04
  checked: php StorageCrawlJob/SchedulerJob/CrawlAdvanceService/IndexCommand
  found: Crawl walkt je Mount nach file id, enqueue idempotent nur gegen bestehende Queue-Zeile; nach Abarbeitung ist die Zeile weg, also neue Zeile -> Container meldet unchanged. Crawl-Kette lebt in oc_jobs bis seen===0.
  implication: Crawl liefert spaeter dieselben Dateien erneut; kein zweiter Crawl-Strang noetig fuer das Symptom.
- timestamp: 2026-10-04
  checked: 05-typwechsel-arm.txt Abschnitt Lauf 8 + 96d-status.jsonl
  found: Zweitwelle scheduled 3037 (23:46:26Z), durchgaenge summiert unchanged 5000; Lauf 7 Crawl lag vorn (scheduled 1586).
  implication: Konsistent: Symptom nur, wenn Vorrat < Ruhemarke waehrend Crawl unfertig.
- timestamp: 2026-10-04
  checked: Python-Verbraucher von DocumentQueue.stats
  found: einziger Verbraucher ist reconcile._quiet; PHP-Seite: QueueController::documentStats -> QueueService::stats (auch IndexCommand/AdminViewService, dort unberuehrt, wenn das Feld im Controller ergaenzt wird).
  implication: Feld "crawling" in der Stats-Antwort ist ein schmaler, rueckwaertskompatibler Draht (fehlt -> False -> altes Verhalten).

## Eliminated

- hypothesis: Top-up-Route startet den Crawl von vorn / zweiter Crawl-Strang (Lock-Verlierer plant alten Cursor neu)
  evidence: Nicht noetig fuer das Symptom: die erste Lieferung des Teilkorpus stammt vollstaendig (5000) aus dem Reconcile; der Crawl hat das Teilkorpus nur einmal geliefert (23:44Z ff.). Top-up nur Ausloeser-Marker, weil der Crawl tatsaechlich unfertig war.
  timestamp: 2026-10-04
- hypothesis: first_index_scheduled / AppInstallStep plant einen zweiten Crawl
  evidence: Flag wird von --restart gesetzt; nur IndexCommand/AppInstallStep/SchedulerJob planen; keine Spur eines zweiten SchedulerJob-Laufs noetig, da Zaehlung aufgeht.
  timestamp: 2026-10-04

## Resolution

root_cause: Das Quiet-Gate des Reconcile (backend/src/findling/worker/reconcile.py::_quiet) misst nur die Vorratslaenge (scheduled < 100), nicht ob der Crawl fertig ist. Ein frischer Container ist sofort reconcile-faellig. Leert der Worker den Vorrat schneller als der cron-getaktete Crawl liefert, walkt der Reconcile voraus, reiht jede noch nicht gecrawlte Datei als stale ein (Lauf 8: 401+9x500+99 = 5000 = ganzes Teilkorpus), und der Crawl reiht dieselben Dateien bei Erreichen erneut ein -> kompletter Zweitdurchgang mit "unchanged".
fix: Crawl-Zustand in die Stats-Antwort und ins Reconcile-Gate. PHP (13993fd9): CrawlAdvanceService::crawling() = SchedulerJob-Zeile ODER Nicht-Recount-StorageCrawlJob-Zeile ODER gehaltene Scheiben-Sperre (ILockingProvider::isLocked(StorageCrawlJob::LOCK_NAME, LOCK_EXCLUSIVE)); QueueController::documentStats liefert zusaetzlich 'crawling'. Container (01b1afce): QueueStats.crawling (nur JSON true zaehlt, fehlendes Feld = False = altes Verhalten); reconcile._quiet gibt bei crawling ROUND_QUEUE_BUSY mit Log "reconcile stands down, the crawl is unfinished" zurueck, vor der Ruhemarke; Gate laeuft vor jeder Scheibe. Doku docs/reconcile.md, Docstring client.queue_stats. Baum-Hashes neu gepinnt (PHP 88 Dateien, Paket 71 Dateien).
verification: TDD rot->gruen: test_reconcile.py + test_queue_client.py 126 passed (vorher 34 failed). Volle Suite 4428 passed, 25 skipped (nach Neu-Pinnen der zwei Baum-Hash-Tests; test_measurement_scripts.py 477 passed). ruff check + ruff format --check gruen, pyright latest 0 Fehler, vulture (src tests, min-confidence 80) gruen. PHP: kein lokales php/Docker -> PHPUnit (CrawlAdvanceServiceTest 5 neue Faelle, QueueControllerTest 2 neue Faelle) laeuft nur in CI (Vorbehalt). Kein Live-Nachweis (boxlos).
files_changed: [php/lib/Service/CrawlAdvanceService.php, php/lib/Controller/QueueController.php, php/tests/Unit/CrawlAdvanceServiceTest.php, php/tests/Unit/QueueControllerTest.php, backend/src/findling/nc/queue.py, backend/src/findling/nc/client.py, backend/src/findling/worker/reconcile.py, backend/tests/test_queue_client.py, backend/tests/test_reconcile.py, backend/tests/test_measurement_scripts.py, docs/reconcile.md]
