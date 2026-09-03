---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 03
subsystem: infra
tags: [reconcile, queue, sqlite, tantivy, httpx, throughput, php]

# Dependency graph
requires:
  - phase: 03-aktualit-t-und-ocr
    provides: "ETag-Abgleich, Slice-Route, Give-up-Regel in QueueService::claim"
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "Pro-Datei-Diagnose und Fehlerliste, die das Verdikt anzeigen"
provides:
  - "Verdikt-Übergabe: die Slice-Route liefert state und reason je Datei, eine Abfrage je Seite"
  - "Store.give_up: der Container merkt sich ein Endurteil gegen den ETag der Seite"
  - "Endgültige Aufgabe-Regel: kein Abgleichzyklus reiht eine aufgegebene Datei erneut ein"
  - "MAX_DELIVERIES mit ausgeschriebener Claim-Arithmetik, drei Auslieferungen"
  - "Aufgegebene Queue-Zeilen kosten den Batch keinen Platz und kein Byte Budget"
  - "1-MiB-Blöcke im Download, gemessen 763 auf 48 Thread-Übergaben je 50 MB"
  - "Konservative Bytebuchhaltung im Writer ohne zweite UTF-8-Kopie je Dokument"
  - "bench.batch_full und fill_seconds im Messwerkzeug"
affects: [05-ARM-Lasttest, 05-Messbericht, 05-Volllauf, 06-Semantik]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Verdikt-Übergabe in der Seite statt je Datei (ein IN-Query je Slice)"
    - "Ein Endurteil wird an den ETag gebunden, nicht an die fileid"
    - "Durchsatzkonstanten tragen ihre Rechnung samt Messwerten im Kommentar"
    - "Textgates über PHP-Quellen halten Arithmetik und Reihenfolge fest"

key-files:
  created: []
  modified:
    - php/lib/Service/QueueService.php
    - php/lib/Service/FileStateService.php
    - php/lib/Controller/ReconcileController.php
    - backend/src/findling/worker/reconcile.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/nc/files.py
    - backend/src/findling/nc/client.py
    - backend/src/findling/index/writer.py
    - backend/src/findling/index/bench.py
    - backend/tests/test_reconcile.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_files_client.py
    - backend/tests/test_gateway_client.py
    - backend/tests/test_index_writer.py
    - docs/reconcile.md
    - docs/ocr.md

key-decisions:
  - "Form A und Form B kombiniert: PHP liefert das Verdikt in der Slice-Seite (kein zweiter Roundtrip je Datei), der Container speichert es gegen den ETag in seiner files-Tabelle (Bindung an die Dateiversion ohne PHP-Migration)"
  - "Das Verdikt wird nur geglaubt, solange der Container die Datei gar nicht kennt; danach entscheidet sein eigener Zustand"
  - "Die Grenze bleibt bei drei Auslieferungen (getRetries() > MAX_DELIVERIES); die vierte Auslieferung des Audits ist der Reaper-Claim, der nichts ausliefert und jetzt auch kein Budget mehr kostet"
  - "Bytebuchhaltung als konservative Obergrenze (4 Byte je Codepoint, exakt bei ascii) statt zweiter Vollkodierung; BATCH_MAX_BYTES ist exakt der Worst Case des Dateideckels, der Leerpunkt verschiebt sich daher nicht"
  - "should_flush entfällt, die Batch-Regel zieht in bench.batch_full, ihren einzigen Aufrufer"

patterns-established:
  - "Verdikt-Übergabe: Codes und Zahlen wandern in der ohnehin gelesenen Seite, nie als Abfrage je Datei"
  - "Endurteil an die Dateiversion binden: der ETag der Seite ist der Träger, ein neuer ETag hebt das Urteil auf"
  - "Durchsatzänderung nur mit Zahlenpaar und mit der Grenze der Messung"

requirements-completed: [PKG-03]

# Metrics
duration: 45 min
completed: 2026-09-03
---

# Phase 5 Plan 03: Endgültige Aufgabe-Regel und zwei Durchsatzposten Summary

**Ein `failed(repeatedly_stuck)` erreicht jetzt die Container-Datenbank, gebunden an den ETag der Seite, sodass der nächtliche Abgleich dieselbe kaputte Datei nicht mehr endlos einreiht; dazu 1-MiB-Downloadblöcke (763 auf 48 Thread-Übergaben je 50 MB) und eine Bytebuchhaltung ohne zweite UTF-8-Kopie (529 us auf 0,7 us je Dokument am Zeichendeckel).**

## Performance

- **Duration:** 45 min
- **Started:** 2026-09-03T08:52:00Z (ungefähr, Zeitnahme nachträglich aus dem ersten Commit abgeleitet)
- **Completed:** 2026-09-03T09:36:33Z
- **Tasks:** 2 (je RED und GREEN, also 4 Commits)
- **Files modified:** 16

## Accomplishments

- **Die inhaltlich schwerste Position des Inventars ist geschlossen** (Gruppe-B-IN-03).
  Die Aufgabe-Regel läuft in `QueueService::claim`, die Queue-Zeile verschwindet
  dabei, und der Container erfuhr davon nichts. Jetzt trägt die Slice-Route
  `state` und `reason` je Zeile (eine Abfrage je Seite, keine je Datei), und der
  Abgleich merkt sich ein Endurteil in seiner eigenen `files`-Tabelle gegen den
  ETag der Seite. Zwei aufeinanderfolgende Zyklen erzeugen keine Queue-Zeile
  mehr; ein neuer ETag reiht wieder ein.
- **Die Auslieferungszahl ist unmissverständlich.** `MAX_ATTEMPTS` heißt jetzt
  `MAX_DELIVERIES`, der Docblock schreibt die Claim-Arithmetik Zeile für Zeile
  aus (der Claim zählt selbst hoch, also ist die vierte Auslieferung der
  Reaper), und ein Quellgate hält sowohl die Zahl als auch die Richtung des
  Vergleichs fest.
- **Eine aufgegebene Zeile kostet den Batch nichts mehr.** Die beiden
  Abschreibungen (`repeatedly_stuck`, `gone`) werden entschieden, bevor die
  Zeile gegen Zeilen- und Bytebudget verrechnet wird, sonst verkleinert eine
  Handvoll dauerhaft steckender Dateien jede Runde echter Arbeit.
- **Zwei gemessene Durchsatzposten** mit Zahl davor und danach, siehe unten.
- **Toter Code raus:** die Batch-Regel des Writers hatte in der Produktion keinen
  Aufrufer (der Poller committet je Claim) und wird jetzt dort geführt, wo sie
  gebraucht wird, im Messwerkzeug.

## Task Commits

1. **Task 1 RED: zwei rote Abgleich-Fälle** , `2666221` (test)
2. **Task 1 GREEN: Verdikt-Übergabe, ETag-Bindung, Auslieferungszahl** , `5957d75` (feat)
3. **Task 2 RED: Blockgröße und Bytebuchhaltung** , `1e68214` (test)
4. **Task 2 GREEN: 1-MiB-Blöcke und Byte-Obergrenze** , `e967a99` (perf)

_Kein REFACTOR-Commit: in beiden Zyklen war nach GREEN nichts aufzuräumen, was
nicht schon Teil der Änderung war._

## Die vier Messwerte

Alle auf derselben Maschine (Windows 11, dieselbe Session, keine parallele
Last), Median aus drei Läufen, Skripte im Scratchpad (`m_download.py`,
`m_writer.py`), beide vor und nach der Änderung mit identischem Codepfad.

### Download, 50-MB-Körper durch `fetch_file_stream`

| | Blockgröße | Thread-Übergaben | Median |
|---|---|---|---|
| davor | 65.536 | 763 | 573 ms |
| danach | 1.048.576 | 48 | 346 ms |

Läufe danach: 345,9 / 372,9 / 337,9 ms. Die Übergabezahl ist exakt
`ceil(50.000.000 / Blockgröße)` und bestätigt die Schätzung der Recherche
("rund 800 Hops"). Der Speicherpreis ist eine Blockgröße je laufendem Download,
bei `INDEX_WORKERS=1` also genau ein Mebibyte.

### Indexseite, Bytebuchhaltung je Dokument

| | Buchhaltung am Zeichendeckel (524.288 Zeichen) | erzeugte Kopie |
|---|---|---|
| davor | 529,5 us | 538.085 Byte je Dokument |
| danach | 0,7 us | keine |

**Und die Grenze dieser Messung, ausdrücklich:** der Volllauf über 1000
Dokumente (je 4412 Zeichen) misst 2889 ms davor und 3874 ms danach, bei einer
Streuung von 2849 bis 5117 ms über die Läufe. Die Änderung ist in diesem Lauf
rechnerisch etwa 4 ms von 3000 und damit im Rauschen; wer die Zahlenpaare
nebeneinanderlegt, darf aus dem Fülllauf **keinen** Rückschluss ziehen. Belegbar
ist die Buchhaltung selbst, und belegbar ist der Wegfall einer halben Megabyte
großen Zwischenallokation je Dokument, was auf einer 4-GB-Box der eigentliche
Posten ist. Das Messwerkzeug `bench.py` gibt seit dieser Änderung `fill_seconds`
aus (gemessen: 3,672 s für 1000 Dokumente), damit der Messbericht der Phase die
Schreibseite überhaupt zitieren kann.

## Files Created/Modified

- `php/lib/Service/QueueService.php` , `MAX_ATTEMPTS` wird `MAX_DELIVERIES = 3`
  mit ausgeschriebener Claim-Arithmetik; die beiden Abschreibungen stehen vor
  der Verrechnung gegen Zeilen- und Bytebudget.
- `php/lib/Service/FileStateService.php` , neu `verdictsFor()`: die Verdikte
  einer ganzen Seite in einer Abfrage, gebändert wie `QueueMapper::DELETE_BAND`,
  Antwort sind nur Codes.
- `php/lib/Controller/ReconcileController.php` , `withVerdicts()` hängt `state`
  und `reason` an jede Zeile der Seite; Klassen- und Methoden-Docblock nennen die
  neue Antwortform.
- `backend/src/findling/nc/files.py` , `FileRow` trägt `state` und `reason`,
  beide optional, damit eine Companion-App eine Version zurück sich genau wie
  vorher verhält; ein nicht lesbarer Code liest als "kein Verdikt".
- `backend/src/findling/worker/reconcile.py` , `_stale_of` wird `_compare`: es
  trennt Arbeit von Verdikten, schreibt die Verdikte weg und zählt sie
  (`RoundResult.given_up`, Logzeile `given_up=`).
- `backend/src/findling/store/repo.py` , `Store.give_up()` samt `_GIVE_UP_SQL`:
  zweiter, engster Schreiber der `files`-Tabelle; Paar gegen die geschlossene
  Liste geprüft, Pfad bleibt leer, `attempts` unberührt, Grabstein wird gehoben.
  Der `open_store`-Docblock nennt den zweiten Schreibweg und das Rennen, das er
  ermöglicht.
- `backend/src/findling/nc/client.py` , `CHUNK_SIZE` auf 1 MiB mit den gemessenen
  Zahlen und der Aussage, dass der Bytedeckel unverändert am selben Byte greift.
- `backend/src/findling/index/writer.py` , Bytebuchhaltung als konservative
  Obergrenze, `pending_bytes` als öffentliche Eigenschaft, Batch-Prädikat und die
  beiden nicht mehr gebrauchten Konstruktorparameter entfernt.
- `backend/src/findling/index/bench.py` , `batch_full()` als öffentliche Regel mit
  beiden Deckeln als Argumente, `fill_seconds` und `fill_documents` im Bericht.
- `backend/tests/test_reconcile.py` , die zwei geforderten Fälle plus drei
  Quellgates (Auslieferungszahl, Verrechnungsreihenfolge, Übergabekanal).
- `backend/tests/test_store_repo.py` , fünf Fälle für `give_up`: ETag-Bindung,
  Zählerruhe, Pfaderhalt, Grabsteinhebung, Zurückweisung eines Paares außerhalb
  der Liste.
- `backend/tests/test_files_client.py` , Seite ohne Codes, Seite mit Codes, Code
  in falschem Typ.
- `backend/tests/test_gateway_client.py` , Blockgröße als Konstante, Übergaben je
  Mebibyte, Deckel mitten im Block.
- `backend/tests/test_index_writer.py` , Dateideckel, Bytedeckel, Konservativität
  über fünf Schriftbreiten, exakter ascii-Fall, Löschung ohne Bytes,
  Buchhaltungs-Reset nach Commit.
- `docs/reconcile.md` , die vierte Grenze des Abgleichs auf Deutsch, samt der
  Ursache der Dauerlast.
- `docs/ocr.md` , der neue Konstantenname.

## Decisions Made

### Die gewählte Form: A und B zusammen, mit Begründung

Der Plan ließ zwei Wege offen und gab dem den Vorzug, der keinen zweiten
Roundtrip je Datei einführt. Beide Wege allein reichen nicht:

- **Form A allein** (PHP schreibt das Verdikt und liefert es im Leseweg mit)
  hätte das Urteil nicht an die Dateiversion binden können.
  `findling_file_state` führt keinen ETag, und die Zeile sagt nach einer
  Änderung der Datei weiterhin `repeatedly_stuck`. Der Abgleich hätte die neuen
  Bytes für immer aus dem Index gelassen, also genau das Versprechen gebrochen,
  für das er existiert (D-02). Eine ETag-Spalte in `findling_file_state` wäre
  eine Migration plus eine geänderte `record()`-Signatur an allen Aufrufern
  gewesen.
- **Form B allein** (der Container merkt es sich selbst) war unmöglich: der
  Container erfährt von der Aufgabe nichts, weil die Zeile nie ausgeliefert und
  nie quittiert wird, und D-01 verbietet einen zweiten Weckkanal.

Gewählt ist daher die Kombination, und sie erfüllt die Vorzugsregel des Plans:
**kein zweiter Roundtrip je Datei.** Die Verdikte einer Seite kosten *eine*
zusätzliche `IN`-Abfrage über bis zu 2000 Primärschlüssel, neben der Abfrage,
die die Seite ohnehin liest. Der ETag, gegen den das Urteil gilt, ist der, den
die Seite gerade geliefert hat. Die Entscheidung ist an drei Stellen im Code
begründet: `Store.give_up`, `_GIVE_UP_SQL` und `Reconcile._compare`.

**Die Feinheit, die die Regel erst richtig macht:** das Verdikt wird nur
geglaubt, solange der Container die Datei *gar nicht* kennt. Sobald er eine
Zeile hält, entscheidet sein eigener Zustand. Ohne diese Einschränkung hätte
eine alte Nextcloud-Zeile eine geänderte Datei dauerhaft unterdrückt, und der
Requeue von Hand hätte einen Sonderweg gebraucht; so wirkt er ohne eine Zeile
Code, weil er die Datei über die Warteschlange ausliefert und der Poller danach
ein echtes Verdikt schreibt.

### Die Auslieferungszahl: der Befund war ein Zählstreit, nicht ein Off-by-one

Der Plan verlangte, `getRetries() > 3` auf drei Auslieferungen zu korrigieren.
Beim Nachrechnen am Code steht folgendes fest, und es ist der Grund, warum der
Vergleich `>` geblieben ist:

- Im Code stand nie ein Literal. Die Bedingung lautete
  `getRetries() > self::MAX_ATTEMPTS` mit `MAX_ATTEMPTS = 3`; die Grep-Kriterium
  `getRetries() > 3` war also schon vorher 0.
- `retries` wird **vom Claim selbst** in der Datenbank hochgezählt
  (`QueueMapper::claimBatch`, `retries + 1`). Die Zeile, die die Regel liest,
  enthält die gerade laufende Ausgabe schon. Claim 1 bis 3 liefern aus, Claim 4
  liest 4, liefert **nicht** aus und schreibt das Endurteil.
- Es gab also drei echte Auslieferungen. Auf `>=` umzustellen hätte sie auf zwei
  gesenkt, also den Off-by-one in die andere Richtung gebaut, und der Plan warnt
  ausdrücklich davor, dass "der nächste Leser die Grenze erneut um eins
  verschiebt".

Was das Audit als "vierte Auslieferung" gezählt hat, ist der Reaper-Claim. Der
ist unvermeidbar (die Erschöpfung wird nur beim Zugreifen entdeckt), **aber er
kostete etwas**: er wurde gegen Zeilenzahl und Bytebudget des Batches
verrechnet. Genau das ist jetzt behoben. Die Änderung besteht damit aus drei
Teilen: umbenannte Konstante, ausgeschriebene Arithmetik im Docblock, und der
Reaper-Claim kostet keine echte Arbeit mehr. Ein Quellgate
(`test_the_give_up_rule_delivers_three_times_and_not_four`) hält Zahl und
Vergleichsrichtung fest und ist gegen zwei Schmutzproben (`>=` und Literal)
selbstgeprüft.

### Bytebuchhaltung: Obergrenze statt Messung, und warum sich nichts verschiebt

Der Plan erlaubte eine Schätzung, wenn sie konservativ ist. Gewählt: exakt für
ascii (`str.isascii()` ist in CPython ein gespeichertes Flag, kein Scan), sonst
vier Byte je Codepoint. Der Leerpunkt verschiebt sich dadurch nicht, und das ist
Arithmetik: `BATCH_MAX_BYTES` ist 67.108.864, und das ist genau
`BATCH_FILES (32) * MAX_TEXT_CHARS (524.288) * 4`. Der Bytedeckel ist also der
Worst Case des Dateideckels; für jedes Dokument, das diese App annimmt, greift
der Dateideckel zuerst, vorher wie nachher. `WRITER_HEAP_BYTES` und
`BATCH_MAX_BYTES` behalten damit ihre Bedeutung in der RAM-Budgetrechnung
(Pitfall 10).

`should_flush` ist entfernt. **vulture hat es bei `--min-confidence 80` nie
gemeldet** , es war eine benutzte Property, nur eben ausschließlich vom
Messwerkzeug, und genau deshalb hat es zwei Phasen überlebt. Mit ihm entfielen
die beiden Konstruktorparameter `batch_files` und `batch_max_bytes`, die sonst
unbenutzt gewesen wären (und die vulture *dann* gemeldet hätte).

## Deviations from Plan

### Auto-fixed und begründete Abweichungen

**1. [Rule 2 - Missing Critical] Das Verdikt wird nur bei völlig unbekannter Datei geglaubt**
- **Found during:** Task 1
- **Issue:** Die im Plan beschriebene Regel ("der Abgleich überspringt eine Datei
  mit endgültigem Verdikt") hätte eine geänderte Datei dauerhaft unterdrückt, weil
  die Nextcloud-Zeile nach der Änderung weiterhin `repeatedly_stuck` sagt. Das
  ist ein Bruch der D-02-Garantie und wäre stiller Dokumentverlust.
- **Fix:** Das Verdikt wird nur übernommen, solange der Container keine Zeile für
  die Datei hält; danach entscheidet der ETag-Vergleich wie bei jeder anderen
  Datei. Der zweite geforderte Testfall belegt es.
- **Files modified:** backend/src/findling/worker/reconcile.py
- **Verification:** `test_a_new_etag_lifts_the_final_verdict_and_requeues_the_file`
- **Committed in:** 5957d75

**2. [Rule 2 - Missing Critical] Der Grabstein wird beim Wegschreiben gehoben**
- **Found during:** Task 1
- **Issue:** `known_etags` blendet Grabsteine aus. Ohne Heben hätte jeder Zyklus
  dieselbe Zeile erneut geschrieben, also eine stille Endlosschleife von
  Schreibvorgängen.
- **Fix:** `_GIVE_UP_SQL` setzt `deleted_at = NULL`, wie der Upsert in `record()`.
- **Files modified:** backend/src/findling/store/repo.py
- **Verification:** `test_give_up_lifts_a_tombstone`
- **Committed in:** 5957d75

**3. [Rule 1 - Bug] Der Reaper-Claim verkleinerte jeden Batch echter Arbeit**
- **Found during:** Task 1
- **Issue:** Der aufgegebene und der verschwundene Datensatz wurden gegen
  Zeilenzahl und Bytebudget verrechnet, obwohl sie nichts ausliefern.
- **Fix:** Beide Abschreibungen stehen jetzt vor der Verrechnung.
- **Files modified:** php/lib/Service/QueueService.php
- **Verification:** `test_a_row_that_is_given_up_costs_the_batch_no_slot_and_no_budget`
- **Committed in:** 5957d75

**4. [Rule 3 - Blocking] Testpfade und `php -l` gegen den Worktree statt gegen den Hauptbaum**
- **Found during:** Task 1 und 2
- **Issue:** Die `<automated>`-Blöcke des Plans nennen absolute Pfade unter
  `/c/Users/Student/nextcloud-search/backend`, also den Hauptbaum. Dieser Lauf
  ist ein paralleler Worktree; ein Lauf gegen den Hauptbaum hätte fremden Code
  geprüft.
- **Fix:** Alle Kommandos im Worktree ausgeführt.
- **Files modified:** keine
- **Verification:** `git rev-parse --abbrev-ref HEAD` ist `worktree-agent-05-03`,
  alle Läufe aus dem Worktree-`backend`.
- **Committed in:** entfällt (Vorgehen, keine Codeänderung)

**5. [Rule 3 - Blocking] `php -l` in einem eigenen Container statt im Dev-Stack**
- **Found during:** Verifikation
- **Issue:** Das Akzeptanzkommando lautet
  `docker compose -f scripts/dev/compose.yaml exec -T app ...`. Der laufende
  Stack (`findling-nextcloud`) bindet `../../php` **des Hauptbaums** ein und wird
  parallel von einem Schwester-Executor benutzt; er hätte den falschen Code
  geprüft, und ein `compose up` aus dem Worktree hätte über `container_name`
  kollidiert.
- **Fix:** `docker run --rm -v <worktree>/php:/app:ro php:8.3-cli` mit demselben
  `find ... | xargs -0 -n1 php -l`.
- **Files modified:** keine
- **Verification:** 33 von 33 Dateien melden ausschließlich "No syntax errors
  detected" (Zählung gegen `find | wc -l` gegengeprüft).
- **Committed in:** entfällt

**6. [Abweichung, dokumentiert] Kein `deferred-items.md` angelegt**
- **Issue:** Die eine offene Verifikation (unten) gehört normalerweise dorthin.
- **Fix:** Sie steht hier in einem eigenen Abschnitt. Eine neue Datei im
  Phasenordner hätte beim Merge mit den Schwester-Worktrees dieser Welle
  kollidiert, weil mehrere Agenten dieselbe Datei angelegt hätten.

---

**Total deviations:** 3 auto-fixed (2 Missing Critical, 1 Bug) und 3 begründete
Verfahrensabweichungen.
**Impact on plan:** Kein Scope Creep. Die drei Auto-Fixes sind Korrektheits- und
Sicherheitsbedingungen der Regel, die der Plan verlangt hat; ohne die ersten zwei
hätte die Regel Dokumente verloren beziehungsweise stillschweigend jede Nacht
geschrieben.

## Nicht erfüllte Akzeptanzbedingung (offene Verifikation)

Ein Akzeptanzpunkt von Task 1 ist **nicht** erfüllt und wird nicht als erfüllt
ausgegeben:

> "Auf dem lokalen Stack nachgestellt und protokolliert: eine absichtlich
> unlesbare Datei wird dreimal ausgeliefert, landet als failed mit Grund
> repeatedly_stuck in der Diagnose, und zwei aufeinanderfolgende Abgleichzyklen
> erzeugen keine neue Queue-Zeile."

**Warum nicht:** Der lokale Stack ist in `scripts/dev/compose.yaml` mit festem
`container_name: findling-nextcloud` definiert und bindet `../../php` des
Hauptbaums ein. Er läuft gerade und wird parallel von einem Schwester-Executor
dieser Welle benutzt. Ein Lauf gegen ihn hätte den PHP-Code des Hauptbaums
geprüft (also nicht diese Änderung), und ein zweiter Stack aus dem Worktree
hätte über Containernamen und Port kollidiert. Dazu braucht die Kette eine
AppAPI-Registrierung des Backends und einen absichtlich sterbenden Worker.

**Was stattdessen belegt ist:**
- Die zwei geforderten Abgleich-Fälle laufen gegen eine echte SQLite-State-DB
  und beweisen "zwei Zyklen, keine Queue-Zeile" sowie "neuer ETag reiht wieder
  ein".
- `Store.give_up` ist mit fünf Fällen gegen die echte Datenbank geprüft.
- Drei Quellgates halten die PHP-Hälfte fest: Auslieferungszahl und
  Vergleichsrichtung, Verrechnungsreihenfolge, Existenz des Übergabekanals.
- `php -l` über alle 33 Dateien der App ist grün.

**Wo es nachzuholen ist:** im ARM-Volllauf dieser Phase (D-02/D-05). Das ist die
Umgebung, in der dieser Defekt überhaupt sichtbar wird, und der Messbericht ist
der Ort, an dem "keine wiederkehrenden Queue-Zeilen für aufgegebene Dateien"
als Beobachtung stehen kann. Empfehlung an den Planner der Volllauf-Pläne
(05-01/05-02 und die Messbericht-Pläne): diese Kette als Störfall-Drill
aufnehmen.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: schema | backend/src/findling/store/repo.py | Zweiter Schreiber der `files`-Tabelle (Reconcile-Verbindung). Kein Schemawechsel, keine neue Spalte, kein `SCHEMA_VERSION`-Bump; das Rennen mit dem Poller ist auf eine wiederholte Vergleichsrunde begrenzt und im `open_store`-Docblock benannt. |
| threat_flag: boundary | php/lib/Controller/ReconcileController.php | Die Slice-Antwort trägt zwei zusätzliche Felder über die Grenze. Beide sind Codes aus der geschlossenen, driftgeprüften Liste; kein Pfad, kein Titel, kein Zeitstempel. Der Container weist alles zurück, was kein String ist. |

Die drei mitigate-Positionen des Threat-Registers sind erfüllt: T-05-11 (Deckel
mitten im Block, `test_a_byte_cap_inside_a_block_still_cuts_the_download_off`),
T-05-12 (konservative Buchhaltung über fünf Schriftbreiten), T-05-13 (Verdikt an
den Dateizustand gebunden, `test_a_new_etag_lifts_the_final_verdict_and_requeues_the_file`).
T-05-SC ist trivial erfüllt: kein Paket installiert, nur Konstanten und
Buchhaltung in bereits gepinnten Modulen.

## Known Stubs

Keine. Jede geänderte Stelle ist verdrahtet und getestet; es gibt keinen
Platzhalter und keinen leeren Rückgabewert, der auf einen späteren Plan wartet.

## Issues Encountered

- **Der Fülllauf des Writers kann die Änderung nicht auflösen.** Erwartet, aber
  erst nach der Messung belegbar: die Streuung auf dieser Maschine ist ±1000 ms
  bei einem Effekt von rund 4 ms. Gelöst, indem beide Zahlenpaare mit ihrer
  Grenze berichtet werden statt eines geglätteten Einzelwerts, und indem die
  Buchhaltung selbst separat gemessen wurde (dort ist der Effekt Faktor 750).
- **Der bekannte Windows-Commit-Flake** ("An IO error occurred: Zugriff
  verweigert (os error 5)") traf das Messskript beim ersten Lauf. Er ist in
  `bench._commit` dokumentiert; das Skript hat denselben Retry bekommen, der
  Produktionscode bleibt unberührt.
- **`should_flush` im Docblock** hätte das Akzeptanz-Grep verletzt (es prüft die
  Datei, nicht nur den Code). Der historische Verweis ist umformuliert, ohne den
  Bezug zu verlieren.

## User Setup Required

Keine. Es ändern sich keine Umgebungsvariablen und keine externen Dienste.
`FINDLING_BATCH_FILES` und `FINDLING_BATCH_MAX_BYTES` behalten Name und
Bedeutung.

## Next Phase Readiness

- Der Volllauf kann starten: die Dauerlast, die den Messbericht verrauscht hätte,
  ist weg, und die zwei Durchsatzposten, die auf 20 GB zählen, sind vor dem Lauf
  behoben.
- Für den Messbericht liegen vier Zahlen bereit, jede mit der Grenze ihrer
  Messung, plus `fill_seconds` als neue Kennzahl des Messwerkzeugs.
- **Lockstep-Hinweis für die Release-Pläne:** die zwei neuen Slice-Felder sind
  vorwärts- und rückwärtskompatibel (fehlend liest als "kein Verdikt"), die
  Wirkung der Regel setzt aber ein Paar aus neuer PHP-App und neuem Container
  voraus. Bei D-11 (Lockstep) ist das ohnehin gegeben und braucht keine
  Versionsprüfung.
- **Ein Punkt bleibt offen** und ist oben ausführlich begründet: die nachgestellte
  Kette auf einem laufenden Stack. Sie gehört in den ARM-Volllauf.

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-03*
