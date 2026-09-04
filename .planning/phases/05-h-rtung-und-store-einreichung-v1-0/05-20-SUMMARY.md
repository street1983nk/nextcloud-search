---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 20
subsystem: infra
tags: [queue, backpressure, low-disk, ocr, reconcile, admin-page, l10n, phpunit]

# Dependency graph
requires:
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: die drei Befunde des Volllaufs aus Plan 05-14, mit ihrem Mechanismus, ihren Zahlen und dem Nachtrag zu Drill 3 in docs/performance.md
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: die Aufgabe-Regel des Abgleichs und die ETag-Bindung des Endurteils aus Plan 05-03
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: die Statusseite und ihren Skip-Kanal aus Plan 05-07 und 05-11
provides:
  - Eine Plattenpause kostet den Arbeitsvorrat nichts mehr, weil eine unbeurteilt zurueckgegebene Zeile ihre Auslieferung zurueckbekommt
  - Der naechtliche Abgleich holt gestrandete Scans selbst zurueck, statt sie fuer immer liegen zu lassen
  - Die Statusseite behauptet waehrend eines langen OCR-Nachlaufs keinen Stillstand mehr, weil der Fortschritt des Containers in das Urteil eingeht
  - Drei dauerhafte Gates fuer diese drei Aussagen, davon zwei in Python und eines in PHPUnit
affects: [arm-volllauf-cax11, 05-17-store-beschreibung, phase-review]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Nachstellung, die eine fremde Haelfte simuliert, liest die Regeln dieser Haelfte aus deren Quelltext statt sie abzuschreiben: dann wird das Modell rot, wenn das Original sich bewegt, statt still ein System zu modellieren, das niemand mehr betreibt"
    - "Zwei Zeitpunkte statt einem, wenn zwei Haelften arbeiten koennen: das Urteil ueber Stillstand nimmt den spaeteren, und der Satz auf der Seite nennt beide"
    - "Arithmetik aus einer Methode mit zwoelf Mitspielern in eine statische, reine Methode ziehen, damit sie einen Unit-Test bekommt statt ein Dutzend Doubles"

key-files:
  created:
    - php/tests/Unit/AdminViewServiceTest.php
  modified:
    - php/lib/Db/QueueMapper.php
    - php/lib/Service/QueueService.php
    - php/lib/Service/AdminViewService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/de.json
    - php/l10n/de.js
    - backend/src/findling/worker/reconcile.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/nc/queue.py
    - backend/tests/test_poller.py
    - backend/tests/test_reconcile.py
    - backend/tests/test_admin_ui_contract.py
    - docs/reconcile.md

key-decisions:
  - "Die Rueckgabe ist der dritte Kanal, den DI-05-23 fuer noetig hielt: der Container kann ueber unlock sehr wohl sagen, dass er nicht angefangen hat, und die ehrliche Aenderung ist, diesen Satz gelten zu lassen, statt einen zweiten dafuer zu erfinden"
  - "Die Rueckgabe der Auslieferung gilt fuer jeden Aufruf von unlock und nicht nur fuer die Plattenpause: Pause, ausgefallenes Gateway und geordnetes Herunterfahren sind dieselbe Aussage, und eine Regel fuer einen der drei haette die anderen beiden weiter Arbeit abschreiben lassen"
  - "Der Heilungszweig des Abgleichs ist an vier Bedingungen gebunden, damit aus einer Reparatur kein naechtlicher Download jedes Scans der Instanz wird"
  - "Das Stillstands-Urteil rechnet mit dem indexed-Zaehler und nicht mit einem Zeitstempel des Containers: ein Zeitstempel waere die direktere Messung und zugleich eine zweite Uhr, und beide Zeitpunkte des Vergleichs sollen von der Uhr von Nextcloud kommen"
  - "Die erste Beobachtung einer Instanz gilt ausdruecklich nicht als Fortschritt, weil ein seit einer Woche haengender Container sonst einen Sprung von null auf fuenfzigtausend als Bewegung verkaufen wuerde"
  - "Kein PHPUnit-Test durch overview() hindurch: zwoelf blind geschriebene Doubles auf einer Maschine ohne PHP sind eine Wette auf die CI, also wurde die Entscheidung als reine statische Methode herausgezogen und diese geprueft"

patterns-established:
  - "Ein Gate, das eine fremde Sprache liest, bringt einen Selbsttest mit: dem Helfer werden ein Quelltext mit der Regel und einer ohne sie gezeigt, damit er beweisen kann, dass er die beiden unterscheidet"
  - "Wenn ein Satz auf der Verwaltungsseite eine Ursache benennt, muss die Messung dahinter genau diese Ursache messen; sonst wird der Satz geaendert und nicht die Messung geschont"

requirements-completed: [SRCH-04]

# Metrics
duration: 35min
completed: 2026-09-04
---

# Phase 5 Plan 20: Die drei Befunde des Volllaufs, geschlossen Summary

**Eine Plattenpause verbraucht das Wiederholungsbudget nicht mehr, gestrandete Scans holt der naechtliche Abgleich selbst zurueck, und die Statusseite wirft dem Container keinen Stillstand mehr vor, waehrend er tausende Dokumente schreibt: drei Befunde aus zehn Stunden Volllauf, jeder mit einem Gate, das ihn nicht wiederkommen laesst.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-09-04T11:34:00Z
- **Completed:** 2026-09-04T12:09:00Z
- **Tasks:** 3, davon einer als RED/GREEN-Paar
- **Files modified:** 16, davon 1 neu (ohne diesen SUMMARY)

## Accomplishments

- **Der schwerste Befund ist an der Wurzel behoben, und die Wurzel war eine Zeile Zaehlerei.** `QueueMapper` zaehlt die Wiederholung bei der Ausgabe, was fuer den Fall richtig ist, fuer den die Aufgeben-Regel gebaut wurde: eine Zeile, die ausgegeben wird und nie zurueckkommt, meldet nirgends einen Fehlschlag und wuerde ohne Deckel ewig kreisen. Eine Zeile, die zurueckgegeben WIRD, ist der genaue Gegenfall, und `unlock` gibt die Auslieferung jetzt mit der Zeile zusammen zurueck. Damit kostet eine Pause Zeit und nie Arbeit.
- **Die Nachstellung ist ein Zustandsautomat und kein Skript.** Der Fall ist eine Folge und keine einzelne Antwort: dieselben Zeilen werden immer wieder ausgegeben, und was zaehlt, ist was der Zaehler zwischen den Ausgaben tut. `_WorkStock` in `backend/tests/test_poller.py` bildet die Nextcloud-Haelfte nach, liest ihre drei Regeln aber aus dem PHP-Quelltext, und fuehrt dreissig Zeilen durch zehn Durchgaenge Plattenknappheit, mit den Zahlen des zweiten Durchgangs von Drill 3. Vorher rot mit `assert 'empty' == 'paused_low_disk'`, also genau an der Stelle, an der der Vorrat abgeschrieben war.
- **Die zweite Haelfte des Banners gilt jetzt auch.** Der Test hoert nicht bei "nichts abgeschrieben" auf: die Platte wird wieder frei, niemand tut irgendetwas, und derselbe Poller indexiert im naechsten Durchgang alle dreissig Dateien. Das ist die Zusage "Indexing is paused so the index stays intact", zu Ende gelesen.
- **Die Dateien, die vor dem Fix gestrandet sind, bleiben nicht liegen.** Das Paar `skipped(no_text_layer)` hier und `failed(repeatedly_stuck)` dort ist keine Einigkeit, sondern eine verlorene Uebergabe an die OCR-Spur, und beide bisherigen Regeln des Abgleichs schwiegen dazu, jede aus einem fuer sich richtigen Grund. Der Abgleich erkennt das Paar jetzt vor beiden Regeln und reiht die Datei wieder ein. Vier Bedingungen halten die Reparatur eng, und vier Tests halten jede einzelne davon.
- **Die Statusseite misst, was ihr Satz behauptet.** `stalledFor` ist das Alter der spaeteren von zwei Bewegungen, dem letzten Hintergrundauftrag dieser App und dem gewachsenen indexed-Zaehler des Containers. In der Messung aus 05-14 waere damit aus acht Stunden falscher Anschuldigung keine einzige geworden, und wenn wirklich beide Haelften stehen, sagt die Seite es weiter, nur mit einem Satz, der beide nennt.
- **Alle Gates gruen, lokal und nachpruefbar.** 965 Python-Tests (vorher 955), ruff, ruff format, pyright und vulture sauber, und `php -l` ueber alle 37 PHP-Dateien in einem Wegwerf-Container. Die acht Behauptungen des neuen PHPUnit-Tests wurden zusaetzlich mit echtem PHP gegen die echte Methode durchgerechnet, weil die Suite selbst nur in CI laufen kann.

## Task Commits

1. **Task 1, RED: die Plattenpause nachgestellt** - `0ac1a4c` (test)
2. **Task 1, GREEN: die Rueckgabe gibt die Auslieferung zurueck** - `084347d` (fix)
3. **Task 2: der Abgleich heilt die verlorene Uebergabe** - `2b6cefe` (fix)
4. **Task 3: das Stillstands-Urteil zaehlt beide Haelften** - `c5af364` (fix)
5. **Notizen: DI-05-27 bis DI-05-29, DI-05-23 als erledigt vermerkt** - `2ec979f` (docs)

**Plan-Metadaten:** dieser SUMMARY (docs)

## Files Created/Modified

- `php/lib/Db/QueueMapper.php`: `unlock` gibt die Auslieferung zurueck, vor der Freigabe und mit einer WHERE-Grenze statt `GREATEST`, weil die drei Dialekte sich dort unterscheiden und in einer WHERE-Klausel nicht. Der Kommentar an `claimBatch` traegt jetzt die zweite Haelfte seines eigenen Satzes.
- `php/lib/Service/QueueService.php`: der Docblock von `MAX_DELIVERIES` sagt, was der Zaehler seit diesem Plan bedeutet, mit der gemessenen Zahl daneben.
- `php/lib/Service/AdminViewService.php`: der gemerkte Zaehler wird vor dem Ueberschreiben gelesen, `backendProgressAt` haelt den Zeitstempel der letzten Bewegung des Containers in appconfig, `progressStamp` ist die reine Entscheidung dahinter, und `stalledFor` entsteht aus dem spaeteren der beiden Zeitpunkte.
- `php/templates/admin.php`, `php/js/admin.js`, `php/l10n/de.json`, `php/l10n/de.js`: der Stillstandssatz nennt beide Haelften, wortgleich in Vorlage, Skript und Katalog.
- `php/tests/Unit/AdminViewServiceTest.php`: acht Faelle auf beiden Seiten der Grenze, ohne ein einziges Double.
- `backend/src/findling/worker/reconcile.py`: `HANDOVER_STATE` und `HANDOVER_REASON`, der Zweig in `_compare` vor beiden bisherigen Regeln und `_is_a_stranded_handover` mit seinen vier Bedingungen.
- `backend/src/findling/worker/poller.py`, `backend/src/findling/nc/queue.py`: die Docstrings von `_abort` und `DocumentQueue.unlock` sagen, was die andere Haelfte mit einer Rueckgabe tut, weil dieser Container davon abhaengt.
- `backend/tests/test_poller.py`: `_WorkStock`, die Nachstellung, das Textgate auf `unlock` und der Selbsttest des Helfers, der die Regel liest.
- `backend/tests/test_reconcile.py`: sechs Faelle, zwei fuer die Heilung und vier fuer ihre Grenzen.
- `backend/tests/test_admin_ui_contract.py`: der Satz in drei Dateien und die drei Zeilen der Verdrahtung, inklusive der Reihenfolge von Lesen und Schreiben.
- `docs/reconcile.md`: ein eigener Abschnitt zur verlorenen Uebergabe, mit der Tabelle der beiden Urteile, den vier Bedingungen und `occ findling:index --restart` als Zweitweg.

## Decisions Made

- **Die Rueckgabe ist der dritte Kanal.** DI-05-23 liest die Abhilfe so, dass die Quittierung einen dritten Kanal braucht, weil der Container "ich habe gar nicht erst angefangen" nicht sagen kann. Er kann es: die Rueckgabe ist genau dieser Satz, und sie existiert seit Phase 2 fuer den geordneten Neustart. Diesen Satz gelten zu lassen ist billiger und ehrlicher, als einen zweiten Weg zu bauen, ihn zu sagen.
- **Die Rueckgabe gilt fuer alle drei Aufrufer.** Plattenpause, ausgefallenes Content-Gateway und Herunterfahren sind dieselbe Aussage ueber die Zeile. Eine Regel nur fuer die Pause haette den Ausfall des Gateways weiter Arbeit abschreiben lassen, und zwar aus einem Grund, der mit der Datei nichts zu tun hat. Was weiterhin zaehlt, ist die Ausgabe, aus der nie eine Rueckgabe wird, und das ist genau die Zeile, fuer die der Deckel gebaut wurde.
- **Ein Container, der ewig pausiert, kreist ewig.** Das ist die gewollte Lesart: solange die Platte knapp ist, bleibt der Vorrat erhalten, die Zeilen stehen als wartend auf der Seite, und das Banner nennt die Ursache. Nichts geht verloren und nichts wird beurteilt.
- **Vier Bedingungen fuer die Heilung.** Gleicher ETag, das Uebergabe-Urteil des Containers, die Abschreibung auf der Nextcloud-Seite und eingeschaltetes OCR. Ohne die letzte waere eine Instanz mit `FINDLING_OCR_ENABLED=false` jede Nacht dabei, jeden Scan herunterzuladen, um zu demselben Urteil zu kommen; ohne die zweite waere `failed(corrupt)` neben der Abschreibung wieder die Dauerlast aus IN-03, nur durch eine neue Tuer.
- **Zaehler statt Zeitstempel.** Der Container weiss genau, wann er zuletzt geurteilt hat, und ein Feld in der Statusantwort waere die direktere Messung. Es waere auch eine zweite Uhr: zwei Container, zwei Zeitzonen, ein driftender Wirt, und der Vergleich antwortet ohne sichtbaren Grund "in der Zukunft". Der Zaehler ist eine Zahl, die die Seite gegen eine Zahl vergleicht, die sie selbst geschrieben hat, und beide Zeitpunkte kommen von der Uhr von Nextcloud. `backend/src/findling/api/status.py` wurde deshalb nicht angefasst, obwohl der Plan sie in `files_modified` fuehrt.
- **Nur Wachstum ist Fortschritt, und die erste Beobachtung ist keiner.** Ein gefallener Zaehler ist ein Neuaufbau, ein stehender sagt nichts, und ein Sprung von null auf fuenfzigtausend ist die erste Antwort, die diese Instanz je gesehen hat. Die Bedingung kostet auf einer frischen Installation genau einen Poll, also fuenf Sekunden, und danach nichts.
- **Der Schluessel des Fortschritts liegt in `AdminViewService` und nicht in `SettingsService`.** Er ist dieselbe Art Wert wie `SchedulerJob::LAST_JOB_RUN` direkt daneben: eine Messung, wann zuletzt etwas passiert ist, geschrieben von dieser Seite und gelesen von niemandem sonst. Die vier Schalter drueben sind die Felder, die ein Admin aendern kann, und dieser ist keiner.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Der Satz auf der Statusseite beschuldigte weiterhin allein die Hintergrundauftraege**

- **Found during:** Task 3
- **Issue:** Das Urteil zaehlt seit diesem Plan beide Haelften, der Satz "Indexing has not progressed for %s. Background jobs may not be running." nannte aber weiter nur eine. Damit haette die Seite im einzigen Fall, in dem sie noch Stillstand meldet, dem falschen Verdaechtigen die Schuld gegeben, und genau diese Diskrepanz zwischen Messung und Satz ist der Kern von DI-05-22.
- **Fix:** Neuer Satz in Vorlage, Skript und beiden Katalogen: "Indexing has not progressed for %s. Neither a background job nor the backend finished anything in that time." Der alte Schluessel ist aus beiden Katalogen entfernt und wird von einem Gate namentlich als abwesend gefordert.
- **Files modified:** php/templates/admin.php, php/js/admin.js, php/l10n/de.json, php/l10n/de.js, backend/tests/test_admin_ui_contract.py
- **Verification:** `test_all_three_files_carry_the_same_sentence_about_a_stall` und die bestehende Schluesselparitaet der beiden Kataloge, beide gruen
- **Committed in:** `c5af364`

**2. [Rule 3 - Blocking] Der Plan verlangt ein Gate fuer Task 3, nennt dafuer aber zwei Dateien, die dazu nichts sagen koennen**

- **Found during:** Task 3
- **Issue:** `files_modified` fuehrt `backend/tests/test_status_endpoint.py` und `php/tests/Unit/GatewayControllerTest.php`. Die erste prueft die Statusroute des Containers, die von dieser Aenderung nicht beruehrt wird; die zweite ist die Doppelung des Content-Gateways, und ein Test der Verwaltungsseite darin waere an der falschen Stelle abgelegt.
- **Fix:** Der behaviorale Test steht in `php/tests/Unit/AdminViewServiceTest.php`, neu und dort, wo ihn jemand sucht. Das Textgate steht in `backend/tests/test_admin_ui_contract.py`, also in der Datei, die `AdminViewService.php` ohnehin schon liest. Beide Dateien liegen ausserhalb der `files_modified` des Plans und ausserhalb der Dateien des parallel laufenden Plans 05-17.
- **Files modified:** php/tests/Unit/AdminViewServiceTest.php (neu), backend/tests/test_admin_ui_contract.py
- **Verification:** Textgate lokal gruen; die acht Behauptungen des PHPUnit-Tests zusaetzlich mit echtem PHP gegen die echte Methode durchgerechnet, alle acht `true`
- **Committed in:** `c5af364`

**3. [Rule 2 - Missing Critical] `progressStamp` als statische, reine Methode herausgezogen**

- **Found during:** Task 3
- **Issue:** Das Abnahmekriterium verlangt einen Test auf beiden Seiten der Grenze. Durch `overview()` hindurch waeren das zwoelf Doubles samt Statusantwort und Scan-Statistik, blind geschrieben auf einer Maschine ohne PHP, mit `failOnWarning` und `failOnRisky` in der Suite. Ohne Extraktion haette es entweder keinen Test oder eine Wette auf die CI gegeben.
- **Fix:** Die Arithmetik ist eine statische Methode mit fuenf Zahlen, die Ein- und Ausgabe von appconfig bleibt in der Seite. Die Schreibbedingung wird dadurch nebenbei praeziser: geschrieben wird, wenn die Antwort sich vom gespeicherten Wert unterscheidet.
- **Files modified:** php/lib/Service/AdminViewService.php
- **Verification:** acht Faelle in PHPUnit, alle acht mit echtem PHP gegengerechnet
- **Committed in:** `c5af364`

---

**Total deviations:** 3 auto-fixed (2 fehlende Notwendigkeit, 1 blockierend)
**Impact on plan:** Kein zusaetzlicher Umfang, kein neues Paket, keine Aenderung an einer Datei des parallel laufenden Plans. Zwei der drei betreffen die Frage, wo der Test von Task 3 hingehoert, und die dritte ist der Satz, den die geaenderte Messung verlangt.

## Issues Encountered

- **Ein Python-Test kann eine PHP-Regel nicht selbst pruefen, und ein Modell, das sie abschreibt, prueft sich selbst.** Geloest mit dem Muster, das dieses Repository schon fuehrt (`test_reconcile.py` liest `MAX_LIST_LENGTH` aus dem PHP-Quelltext): die Nachstellung liest beide Regeln, die Auslieferungsgrenze und die Rueckgabe, aus den beiden PHP-Dateien. Damit war der Test vor dem Fix aus dem richtigen Grund rot und ist danach aus dem richtigen Grund gruen, und er wird rot, wenn die Regel drueben wieder verschwindet. Der Helfer, der die schwerere der beiden Regeln liest, bekommt einen Selbsttest mit einem Quelltext mit und einem ohne die Regel.
- **`_unlock_body` schnitt beim ersten Versuch zu viel heraus.** Der Schnitt bis zum naechsten `public function` nimmt den Docblock der folgenden Methode mit, und eine Behauptung ueber die Reihenfolge zweier Bezeichner haette dann in einem fremden Kommentar fuendig werden koennen. Der Schnitt endet jetzt an der ersten schliessenden Klammer auf einer Tabulatorebene, also am Ende der Methode.
- **PHPUnit laeuft in diesem Projekt nur in CI**, und das steht als Tatsache im Job und in `docs/testing.md`. Ersatzweise wurden `php -l` ueber alle PHP-Dateien und die acht Behauptungen des neuen Tests in einem Wegwerf-Container mit echtem PHP 8.2 ausgefuehrt. Was damit nicht geprueft ist, ist die Verdrahtung von PHPUnit selbst, also Attribute, Namensraum und Datenlieferant; die drei sind aus den fuenf vorhandenen Testklassen uebernommen.
- **Die Berichtigung aus 05-14 ist nachgeprueft und stimmt bereits.** Die einzige Stelle in der Doku, die "Container laeuft, indexiert nicht" beschreibt, ist `docs/performance.md` ab Zeile 1625, und sie nennt seit dem Nachtrag von 05-14 `findling.main.enabled_handler` als Ursache und entlastet den HaRP-Schluessel ausdruecklich. `docs/dev-setup.md` erwaehnt `HP_SHARED_KEY` nur beim Hochfahren des Stacks und behauptet nichts ueber die Indexierung. Keine Aenderung noetig.

## User Setup Required

Keine.

## Next Phase Readiness

- **Der ARM-Volllauf kann starten und pruefen, was hier geaendert wurde.** Drei Dinge sollte er ausdruecklich ablesen: nach einer Plattenpause den Wert von `retries` in `oc_findling_queue` fuer die Zeilen, die unterwegs waren (Erwartung: unveraendert, DI-05-27); nach einem Kill mitten im OCR-Nachlauf, ob eine gestrandete Datei nach dem naechsten Abgleich wieder indexiert ist; und ueber die Laufzeit die Spalte `runState` der Statusseiten-Reihe, die in der x86-Messung acht Stunden lang `stalled` sagte (Erwartung: `running`).
- **Offen und benannt:** DI-05-27 (die Rueckgabe ist nicht gegen einen echten Datenbankdialekt geprueft), DI-05-28 (eine geheilte Datei bleibt in der Fehlerliste stehen, die alte Frage aus DI-05-14 und DI-05-21 durch eine neue Tuer) und DI-05-29 (nur die Entscheidung des Stillstands-Urteils hat einen Unit-Test, nicht ihre Verdrahtung).
- **Nicht angefasst, mit Absicht:** `.planning/STATE.md`, `.planning/ROADMAP.md`, `README.md`, beide `appinfo/info.xml`, `docs/store-listing.md` und `backend/tests/test_store_metadata.py`, also die Dateien des parallel laufenden Plans 05-17. `docs/performance.md` ebenfalls nicht: der Bericht beschreibt eine Messung von gestern, und sein Satz "Notiert als DI-05-23, nicht behoben" war zum Zeitpunkt der Messung wahr. Der Verweis auf die Behebung gehoert in den ARM-Bericht.

## Self-Check: PASSED

| Pruefung | Ergebnis |
|---|---|
| `php/tests/Unit/AdminViewServiceTest.php` | vorhanden, 113 Zeilen |
| `php/lib/Db/QueueMapper.php`, `php/lib/Service/AdminViewService.php`, `backend/src/findling/worker/reconcile.py` | vorhanden und geaendert |
| `docs/reconcile.md` | vorhanden, neuer Abschnitt zur verlorenen Uebergabe |
| Commits `0ac1a4c`, `084347d`, `2b6cefe`, `c5af364`, `2ec979f` | alle im Log |
| `uv run pytest` | 965 bestanden, 11 uebersprungen (vorher 955) |
| `ruff check`, `ruff format --check`, `pyright`, `vulture` | alle sauber |
| `php -l` ueber `php/lib` und `php/tests` | 37 Dateien, keine Beanstandung |
| Die acht Behauptungen des PHPUnit-Tests, mit echtem PHP nachgerechnet | acht mal `true` |
| Schluesselparitaet `de.json` gegen `de.js` | gleich |
| Em-Dash, En-Dash, Emoji in allen geaenderten Dateien | keine |
| `.planning/STATE.md`, `.planning/ROADMAP.md`, `README.md`, `appinfo/info.xml` | nicht angefasst |
| Dateien des parallelen Plans 05-17 | nicht angefasst |

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-04*
