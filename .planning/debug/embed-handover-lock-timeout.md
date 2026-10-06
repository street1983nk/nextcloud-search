---
status: resolved
trigger: "OCR-zu-Embed-Uebergabe laeuft in Lock-Timeouts: 'could not move N files to the embed track, they run into the lock timeout' (Lauf 9 m7g.4xlarge L-T zweimal 30 Dateien, exakt 60 s nach dem Commit; 05.10. c7a.4xlarge St-fp32-T voller 500er-Stapel direkt nach 'the precision of the embedding changed, the vector stock is being written again')"
created: 2026-10-05
updated: 2026-10-05
---

## Current Focus

hypothesis: "Fall 2 BELEGT: VECTOR_BACKLOG_BAND=500 (worker/embedding.py:149) ueberschreitet QueueController::MAX_LIST_LENGTH=256 (QueueController.php:82); intList (Z.438-441) lehnt jede Liste >256 mit HTTP 400 ab, die Wiederauslieferung nach einem Praezisionswechsel kommt bei >256 indexierten Dokumenten nie voran. Fall 1 (60 s) ist eine ANDERE Ursache, Mechanismus aus den Rohdaten nicht belegbar."
test: "Rot-Test: Parity VECTOR_BACKLOG_BAND <= PHP-MAX_LIST_LENGTH + Reproduktion mit 300 Dokumenten gegen eine Fake-Queue, die wie intList >256 ablehnt"
expecting: "Beide rot bei 500, gruen bei Band 200 (Muster REQUEUE_BAND, reconcile.py:136-148, CR-01)"
next_action: "Fall 2 gefixt (a0ac5aee, lokal). Owner-Entscheid zu Fall 1 abwarten (Vorlage unten); bei der naechsten Anfahrt Belege B1-B4 erheben."

owner_decision_fall1:
  frage: "Wie soll die OCR->Embed-Uebergabe auf einen gescheiterten requeue reagieren? (Ursache der 60 s unbelegt)"
  optionen:
    A: "Nichts aendern, nur die neue Diagnosezeile im naechsten Lauf auswerten. Pro: kein Verhaltensrisiko, Fix erst bei belegter Ursache. Contra: bis dahin weiter bis 30 min Verzug + doppelte OCR je Vorfall."
    B: "Ein sofortiger Wiederholversuch des requeue (gleicher Pass, kurze Pause). Pro: behebt transiente Transportfehler ohne 30-min-Haenger. Contra: verlaengert den Pass um bis zu einen weiteren Timeout; hilft nicht, falls die Ursache systematisch ist."
    C: "Gescheiterte Zeilen per unlock freigeben statt auf den OCR-Lock (1800 s) zu warten. Pro: Rueckkehr in Minuten. Contra: Zeilen bleiben kind ocr -> OCR wird trotzdem doppelt gemacht; unlock nutzt denselben Transport und kann ebenso scheitern."
    D: "Embed-Uebergabe bei Fehlschlag spaeter aus dem lokalen Zustand nachholen (Retry-Liste im Prozess, naechster Pass). Pro: keine doppelte OCR. Contra: neuer Zustand, Neustartverhalten zu klaeren, groesster Bau."
  empfehlung: "A jetzt (Diagnosezeile ist committet), danach je nach Befund B (Transport-Timeout) oder Ursachenfix serverseitig. Kein Bau ohne belegte Ursache."
  belege_naechste_anfahrt:
    B1: "Container-Log: neue Zeile 'could not hand N files to another track, <Typ> status=<x> after <s> s'"
    B2: "nextcloud.log UND Webserver-/PHP-FPM-Log (AIO-Apache, php error log) im Zeitfenster"
    B3: "env des ExApp-Containers: NPA_TIMEOUT, NPA_TIMEOUT_DAV, NEXTCLOUD_URL (Weg ueber HaRP/Proxy?)"
    B4: "Nach einem Praezisionswechsel: /status-Reihe bis embedded == indexed (5000) und EMBEDDING_BACKLOG_MARK == '' (meta), plus Anzahl 'could not hand' im Fenster"

reasoning_checkpoint:
  hypothesis: "Die Wiederauslieferung nach einem Praezisionswechsel scheitert, weil VECTOR_BACKLOG_BAND=500 groesser ist als QueueController::MAX_LIST_LENGTH=256 und intList jede laengere Liste mit HTTP 400 ablehnt"
  confirming_evidence:
    - "Fehler 23,9 ms nach dem Wechsel (container-rueckkehr-int8.txt), also Sofortablehnung, kein Timeout"
    - "Code: embedding.py:149 (500) vs QueueController.php:82 (256), intList Z.438-441 -> badList 400"
    - "Positivkontrolle: Wechsel bei indexed=0 (c7a.xlarge 12:31:46Z) ohne Fehler"
    - "Rot-Test reproduziert exakt die Feldmeldung 'could not move 300 files to the embed track'"
  falsification_test: "Mit Band 200 und einer Fake-Queue, die >256 ablehnt, muessten alle Dokumente uebergeben werden und der Cursor leer enden; bleibt der Test rot, ist die Hypothese falsch"
  fix_rationale: "Band unter die Vertragsdecke legen beseitigt die 400 an der Quelle; gleiches Muster wie REQUEUE_BAND (CR-01). Ein Parity-Test haelt beide Zahlen kuenftig zusammen"
  blind_spots: "Kein Feldlauf nach dem Fix; die nextcloud.log-Warnung 'rejected a malformed queue list' der c7a.4xlarge-Box ist nicht in den Rohdaten (direkter Serverbeleg fehlt). Fall 1 (60 s) bleibt davon unberuehrt"

tdd_checkpoint:
  test_file: "backend/tests/test_embedding_track.py"
  test_name: "test_a_band_of_the_redelivery_fits_under_the_list_ceiling_of_the_controller, test_a_precision_change_on_a_stock_above_the_list_ceiling_writes_every_document_again"
  status: "red"
  failure_output: "assert 500 <= 256 / every indexed document has to be handed back ... assert [] == [1, 2, 3, ...] (Log: could not move 300 files to the embed track)"

## Symptoms

expected: |
  Nach dem OCR-Commit werden die Dateien ohne Lock-Timeout in die Embed-Spur verschoben. Nach einem Praezisionswechsel (fp32 -> int8) wird der komplette Vektorbestand (5000 Dateien) neu geschrieben, belegbar.
actual: |
  Fall 1 (Lauf 9, 04.10., m7g.4xlarge, Zelle L-T): zweimal "could not move 30 files to the embed track, they run into the lock timeout" (05:02:56Z und 05:34:19Z, je ANDERE 30 Dateien, exakt 60 s nach dem Commit). Dateien haengen bis zum OCR-Lock-Ablauf (1800 s), werden einmal doppelt per OCR verarbeitet; kein Datenverlust, Bestand 30 min spaeter vollstaendig.
  Fall 2 (05.10., c7a.4xlarge, Zelle St-fp32-T): nach Rueckkehr fp32 -> int8 (10:48:05Z) "the precision of the embedding changed, the vector stock is being written again" und SOFORT "could not move 500 files to the embed track, they run into the lock timeout".
errors: |
  could not move 30 files to the embed track, they run into the lock timeout
  could not move 500 files to the embed track, they run into the lock timeout
reproduction: |
  Boxlos: nur committete Rohdaten und Code. KEINE Box anfahren, KEINE AWS-Kommandos.
  Belege:
  - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/m7g.4xlarge/L-T/container-auszug.txt
  - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/c7a.4xlarge/St-fp32-T/container-rueckkehr-int8.txt
  - weitere Dateien in denselben Zellordnern (Statusreihen, Zaehler, Kettenprotokoll)
started: "04.10.2026 (Lauf 9), erneut 05.10.2026"

## Auftrag und Regeln (vom Orchestrator)

- Arbeit DIREKT im Repo C:\Users\Student\nextcloud-search auf main, kein Worktree.
- NICHT anfassen (paralleler Executor): docs/measurements/README*, docs/performance.md, .planning/phases/28-*/28-11-SUMMARY.md.
- Vordiagnose-Hinweis: requeue-Pfad in backend/src/findling/.../queue.py protokolliert die Ausnahme ohne Details (Sofortmassnahmen-Kandidat: Ausnahme-Details ins Log). "Exakt 60 s nach dem Commit" deutet auf festen Lock-/Busy-Timeout.
- Prueffragen: Wer haelt den Lock waehrend der 30er/500er-Verschiebung? Warum kollidiert der Praezisionswechsel-Neuschreib mit der Uebergabe? Ist der OCR-Lock-Rueckfall 1800 s angemessen oder braucht die Uebergabe einen Retry statt Requeue?
- ZUSATZAUFTRAG (Pflicht): Vollstaendigkeit des Vektor-Neuschreibens nach der fp32-Rueckkehr pruefen (Statusreihen, Zaehler, Embed-Spur-Protokoll gegen Dateizahl 5000). Falls nicht belegbar: klar sagen und benennen, welcher Beleg bei der naechsten Anfahrt zu erheben ist.
- Fix nur bei BELEGTER Ursache; Reproduktion per Thread-/Lock-Test vor dem Fix (rot -> gruen).
- Gates lokal gruen VOR Commit (backend/, via uv): ruff Vollregelsatz, ruff format --check, pyright basic, vulture, pytest-Suite.
- Commits NUR LOKAL, NIEMALS push. Commit-Autor gemaess Repo-Konfiguration, keine Claude-Trailer. Keine Em-Dashes; Umlaute nur in deutscher Prosa; Code englisch.
- Echter Owner-Entscheid (Verhaltensaenderung mit Produktwirkung, mehrere gleichwertige Fix-Wege): NICHT selbst entscheiden, Status checkpoint, kompakte Vorlage zurueckgeben.
- Status resolved nur, wenn Fix committet UND belegt; sonst diagnosed/checkpoint.

## Eliminated

- hypothesis: "Fall 2 ist eine Lock-/Busy-Timeout-Kollision mit dem Vektor-Neuschreiben"
  evidence: "Fehler 23,9 ms nach dem Wechsel, kein Timeout; Ursache ist HTTP 400 aus intList (Liste 500 > 256)"
  timestamp: 2026-10-05

- hypothesis: "Fall 1 ist ein SQLite-busy_timeout im Container"
  evidence: "busy_timeout ist 10 s (store/repo.py:217), nicht 60 s; eine Ueberschreitung wuerfe in _record_verdicts und braeche den Pass ab, die Warnung kommt aber aus requeue"
  timestamp: 2026-10-05

- hypothesis: "Fall 1 hat dieselbe Ursache wie Fall 2 (Listenlaenge)"
  evidence: "Band 30 < 256; Fehler nach 60 s statt sofort; nextcloud.log ohne badList-Warnung"
  timestamp: 2026-10-05

## Evidence

- timestamp: 2026-10-05
  checked: Herkunft der Meldung
  found: "could not move ... they run into the lock timeout" kommt aus hand_over (worker/embedding.py:268-270), wenn DocumentQueue.requeue ok=False liefert (nc/queue.py:608-616, except Exception ohne Details). "lock timeout" benennt nur den RUECKFALL (Zeilenlock der Queue, OCR 1800 s), nicht die Ursache.
  implication: Die Meldung sagt nichts ueber einen Lock als Ursache; jede Ausnahme des OCS-POST fuehrt hierher.

- timestamp: 2026-10-05
  checked: Fall 2 Zeitstempel c7a.4xlarge/St-fp32-T/container-rueckkehr-int8.txt
  found: 10:48:05.144793Z "precision ... written again" -> 10:48:05.168664Z "could not hand 500 files" = 23,9 ms. Kein Timeout, sondern sofortige Fehlantwort.
  implication: Fall 2 ist keine Lock-/Timeout-Kollision.

- timestamp: 2026-10-05
  checked: Code PHP-Grenze vs Band
  found: VECTOR_BACKLOG_BAND = 500 (worker/embedding.py:149, Kommentar behauptet noch "companion writes them in bands of a thousand"); QueueController::MAX_LIST_LENGTH = 256 seit a32b4191 (2026-09-01); requeue() ruft intList (QueueController.php:307-310), intList gibt bei count>256 null -> badList() -> HTTP 400 (Z.438-441, 590-599); nc_py_api check_error wirft NextcloudException bei >=400 -> except Exception in nc/queue.py:610.
  implication: Jedes Band der Wiederauslieferung mit >256 Ids wird abgelehnt. _answer_the_vector_drift hat vorher forget_all() ausgefuehrt (embedding.py:1106) und den Cursor auf "0" gesetzt; der Cursor rueckt nur nach ok vor (Z.965-966), also liefert jeder Leerlauf-Schritt erneut dieselben 500 Ids -> wieder 400. Vektorbestand bleibt bei >256 indexierten Dokumenten LEER, endlos, waehrend die Marke "aktuell" sagt.

- timestamp: 2026-10-05
  checked: Praezedenzfall im Code
  found: reconcile.py:136-148 REQUEUE_BAND=200 mit exakt derselben Begruendung (CR-01, 7d334bf9, 2026-09-01), plus Parity-Test test_reconcile.py:579-582 gegen die PHP-Konstante. Fuer VECTOR_BACKLOG_BAND fehlt beides.
  implication: Gleiche Fehlerklasse, einmal gefixt; Fixweg etabliert (Band unter der Decke + Parity-Gate), kein neuer Produktentscheid.

- timestamp: 2026-10-05
  checked: Positivkontrolle c7a.xlarge/St-fp32-T/container-auszug.txt
  found: 12:31:46Z "precision of the embedding changed" OHNE Folgefehler; erster "pass finished" erst 12:40:38Z, also indexed=0 beim Wechsel -> Band leer, kein requeue-Aufruf. Bestehende Tests der Wiederauslieferung laufen mit 1-2 Dokumenten bzw. VECTOR_BACKLOG_BAND=1 (test_embedding_track.py:1692, 1726), nie >256.
  implication: Wechsel bei <=256 Dokumenten funktioniert; der Fehler haengt an der Bandgroesse.

- timestamp: 2026-10-05
  checked: Fall 1 Zeitstempel m7g.4xlarge/L-T/container-auszug.txt Z.403-406, 513-516
  found: Commit 05:01:56.012Z -> Warnung 05:02:56.016Z (60,004 s); Commit 05:33:19.587Z -> Warnung 05:34:19.593Z (60,006 s). Zwischen Commit und requeue nur _record_verdicts (lokales SQLite) und hand_over(ocr) mit leerer Liste (kein Aufruf); acknowledge danach ohne Aufruf (done leer, "pass finished" 34 us nach der Warnung). Band 30 < 256.
  implication: Der requeue-POST selbst dauerte ~60 s und scheiterte; nicht die Fall-2-Ursache.

- timestamp: 2026-10-05
  checked: Timeout-Quellen im Code
  found: SQLite busy_timeout 10 s. OCS laeuft ueber nc_py_api 0.30.3 -> niquests 3.21.0 AsyncSession mit timeout=NPA_TIMEOUT (Default 30, nc_py_api/options.py:21; im Repo nirgends gesetzt). Kein 60-s-Wert auf diesem Pfad.
  implication: 60 s = vermutlich 2 x 30 s (int-Timeout gilt fuer Connect UND Read) oder ein Webserver-/Proxy-Timeout; aus den Rohdaten NICHT entscheidbar.

- timestamp: 2026-10-05
  checked: Serverseite Fall 1 (rohdaten/05-typwechsel-arm.txt Z.205-213)
  found: nextcloud.log ohne Eintrag seit 04:36Z (weder 'could not requeue a batch' noch 'rejected a malformed queue list'); die 30 Dateien standen danach weiter als kind ocr, retries 1, liefen erst nach OCR-Lock-Ablauf neu.
  implication: requeueAs wurde serverseitig NICHT wirksam und PHP loggte keinen Fehler -> Anfrage erreichte PHP nicht (vollstaendig) oder wurde ausserhalb von Nextcloud abgebrochen. Ursache unbelegt; noetig: Ausnahmetyp, Statuscode, Dauer im Container-Log.

- timestamp: 2026-10-05
  checked: Zusatzauftrag Vollstaendigkeit nach fp32->int8 (99-rueckkehr-int8.txt, container-rueckkehr-int8.txt, 96d-status.jsonl)
  found: Letzte Uebersicht 10:47:44Z, also VOR dem Neuschreiben 10:48:05Z: indexed=5000 embedded=5000 storedPrecision=int8. Danach keine Statusreihe, kein Zaehler; Box gestoppt 10:51:02Z. Folgezellen c7a.8xlarge starten bei indexed=0 (S-T/96d-status.jsonl Z.1), unbeeinflusst.
  implication: Vollstaendigkeit NICHT belegbar; nach Code (Band 500 > 256) war das Neuschreiben sicher NICHT vollstaendig, es konnte nicht beginnen: Bestand per forget_all geleert, Wiederauslieferung endlos abgelehnt.

## Resolution

root_cause: |
  Fall 2 (BELEGT): VECTOR_BACKLOG_BAND=500 (worker/embedding.py:149) > QueueController::MAX_LIST_LENGTH=256 (php/lib/Controller/QueueController.php:82). intList lehnt jede Liste >256 mit HTTP 400 ab (Z.438-441 -> badList 590-599). Nach einem Praezisionswechsel leert _answer_the_vector_drift den Bestand (forget_all, embedding.py:1106), setzt den Cursor auf "0" und liefert Baender von 500 Ids aus; jedes wird abgelehnt, der Cursor rueckt nie vor (Z.965-966), der Vektorbestand bleibt bei >256 indexierten Dokumenten dauerhaft leer, waehrend die Marke "aktuell" sagt. Gleiche Fehlerklasse wie CR-01 (reconcile, REQUEUE_BAND=200), dort gefixt, hier uebersehen.
  Fall 1 (NICHT belegt): requeue-POST mit 30 Ids scheitert 60,00 s nach dem Commit, serverseitig ohne Log und ohne Wirkung (kind blieb ocr). Kein 60-s-Wert im Code; Kandidaten: niquests-Timeout (NPA_TIMEOUT 30, int gilt fuer Connect und Read), Webserver/Proxy. Unterscheidung erst mit der neuen Diagnosezeile moeglich.
fix: |
  1. VECTOR_BACKLOG_BAND 500 -> 200 (Kopfraum unter 256, Muster REQUEUE_BAND), Kommentar mit Feldbeleg korrigiert.
  2. Parity-Test VECTOR_BACKLOG_BAND <= PHP-MAX_LIST_LENGTH (liest die PHP-Konstante).
  3. Reproduktionstest: 300 Dokumente, Fake-Queue lehnt >256 ab wie intList -> alle Dokumente uebergeben, Cursor endet leer.
  4. Diagnose (verhaltensneutral): requeue-Warnung nennt Ausnahmetyp, status=<int|none>, Dauer; kein Ausnahmetext (T-24-19).
verification: |
  Rot vor dem Fix: 'assert 500 <= 256' und 'assert [] == [1, 2, 3, ...]' (Log: could not move 300 files to the embed track). Gruen nach dem Fix: test_embedding_track.py 71 passed, test_queue_client.py inkl. 2 neuer Diagnosetests gruen. Gates: ruff, ruff format --check, pyright (latest) 0 errors, vulture rc 0, pytest-Suite (siehe Commit).
files_changed:
  - backend/src/findling/worker/embedding.py
  - backend/src/findling/nc/queue.py
  - backend/tests/test_embedding_track.py
  - backend/tests/test_queue_client.py


## Owner-Entscheid Fall 1 (05.10.2026)

Signal per Auswahlfrage, woertlich: "A: Nur Diagnose". Es wird nichts gebaut; die neue
Diagnosezeile (Ausnahmetyp, HTTP-Status, Dauer) wird beim naechsten Vorfall ausgewertet.
Zeigt sie einen Transport-Timeout, wird Option B (Sofort-Retry) nachgeruestet, sonst wird
die Ursache serverseitig gesucht. Belege fuer die naechste Anfahrt stehen oben unter Offen.
Fall 2 ist mit a0ac5aee behoben (Band 200, Kopplungstest an MAX_LIST_LENGTH); der
Feldbeleg eines echten Laufs steht aus und reist mit der naechsten Anfahrt.


## Boxlose Vertiefung Phase 29 (06.10.2026, Plan 29-03)

Kein Verhaltensbau (Owner-Entscheid A). Geprüft wurde nur, was ohne Box prüfbar ist.

Stand der Diagnose (D-29-13, erledigt):

- `git show --stat a0ac5aee`: Commit liegt vor (queue.py, embedding.py, zwei Testdateien, Baumhash).
- `backend/src/findling/nc/queue.py:640`: "could not hand %d files to another track, %s status=%s after %.1f s" (Typ, Status, Dauer, nie der Ausnahmetext, T-24-19).
- `backend/src/findling/worker/embedding.py:276`: Folgezeile "could not move %d files to the %s track, they run into the lock timeout".
- `tests/test_queue_client.py`: beide Diagnosetests grün (89 passed), status=400 mit Dauer und status=none.

Messung der 60 s, lokal: ein Server auf 127.0.0.1 hält die Antwort zurück, gefahren wird der echte Pfad `DocumentQueue.requeue` (30 Ids) über nc_py_api 0.30.3 und niquests 3.21.0, `NPA_TIMEOUT=30` (Default, `nc_py_api/options.py:21`, als ein int an die AsyncSession, `_session.py:297`). Das Messskript lag nur temporär im Arbeitsbaum und ist nicht committet.

| Szenario | Dauer bis zum Fehlschlag | Ausnahmeklasse, Status in der Diagnosezeile |
|---|---|---|
| Server liest die Anfrage, antwortet nie | 30,1 s | NextcloudException status=408 (nc_py_api wandelt ReadTimeout in 408) |
| Statuszeile und Header kommen, der Body bleibt aus | 30,0 s | ConnectionError status=none |
| Antwort tröpfelt, ein Byte alle 20 s | nach 200 s noch offen (äußerer Wächter) | keine: der int gilt je Lesevorgang, nicht als Gesamtfrist |
| Verbindungsaufbau scheitert (TEST-NET 192.0.2.1) | 21,0 s | ConnectionError status=none (Windows gibt den SYN-Versuch vor den 30 s auf) |
| Backlog voll, nie akzeptiert (lokal) | 2,0 s | ConnectionError status=none (Windows antwortet mit Reset) |

Ergebnis zur Hypothese A7 ("30 s Connect plus 30 s Read = 60 s"): **in der einfachen Form widerlegt.** Eine einzelne Anfrage, deren Antwort ausbleibt, scheitert nach 30 s, nicht nach 60 s, und ohne Wiederholung (30,1 s). Ein gescheiterter Verbindungsaufbau beendet die Anfrage, ein Lese-Timeout kann sich daran nicht anschließen. Die gemessenen 60,004 s und 60,006 s aus Lauf 9 brauchen deshalb zwei aufeinanderfolgende Wartezeiten von 30 s (etwa zwei aufgelöste Adressen, deren Verbindungsaufbau je 30 s hängt), eine Gegenstelle, die unter 30 s Abstand Bytes liefert und nach 60 s abbricht (Proxy oder Webserver mit fester Frist), oder einen anderen `NPA_TIMEOUT` im Container. Welcher Fall vorliegt, sagt die Diagnosezeile beim nächsten Vorfall: `status=408 after 30` hieße "Antwort bleibt aus", `ConnectionError status=none after 60` hieße "Abbruch außerhalb des Clients", ein Wert um 60 zusammen mit status=408 spräche für `NPA_TIMEOUT=60` (Beleg B3).

Der Feldbeleg ist verschoben (D-29-11): Diagnosezeile, Server- und Webserver-Log und die env des Containers (B1 bis B3) werden bei der nächsten Anfahrt erhoben; vorher wird nichts gebaut.
