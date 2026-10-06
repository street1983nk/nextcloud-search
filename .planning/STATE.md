---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: Leistungsprofile
status: phase_complete
stopped_at: "PHASE 28 ABGENOMMEN + SECURED 71/71 (06.10.): T-28-69 geschlossen per nachtraeglicher Owner-Bestaetigung (woertlich 'ok weiter' auf die Doppel-Frage Push 3 + #24-Merge, dokumentiert in 28-14-SUMMARY Abschnitt Nachtraegliche Owner-Bestaetigung); Push der lokalen Commits freigegeben; NAECHSTES: Phase 29 planen"
last_updated: "2026-10-06T00:00:00.000Z"
last_activity: 2026-10-06
progress:
  total_phases: 6
  completed_phases: 5
  total_plans: 62
  completed_plans: 62
  percent: 86
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-27 after v1.3 milestone)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 28, Abnahme-Anfahrt

## Current Position

Phase: 28 (Abnahme-Anfahrt), in Ausführung
Plan: 14 of 14
Status: Phase 28 KOMPLETT und vom Owner abgenommen (06.10.); offen: Audits der Phase, dann Phase 29
Last activity: 2026-10-05

Progress: [█████████░] 87%

## Naechster Schritt

**28-11 KOMPLETT (05.10. abends): Auswertung, Bericht und Owner-Entscheide stehen.**
Owner-Signal 05.10.2026: "je-fall: 11=nachziehen, 16=nachziehen, 17=nachziehen, 20=nachziehen,
21=nachziehen, S-voll=nachziehen (Vollindex-Term, Umfang legt 28-12 vor), wert=250 MiB, store=kein Fall".
Die Pläne 28-07/08/09 sind per rückwirkendem Close-out abgeschlossen (SUMMARYs b0756181..bde88f84).
Bericht: docs/measurements/2026-10-abnahme-anfahrt/README.md (Abschnitt 14 Owner-Entscheide),
auswertung.txt, neues Kapitel "Abnahme-Anfahrt v1.4 (Phase 28)" in docs/performance.md.
Kein Probe-Widerspruch, kein Store-Zahl-Fall (C1 = 743,9 MB im Band), RESIDENT_FIGURE unverändert.

NÄCHSTER SCHRITT: 28-10 Abbau beider Boxen (Owner-Go "Ja, beide abbauen" liegt vor; wartet nur auf
frischen AWS-Login; vorher Schlusszahlen-Tabelle nach Runbook 2.6 in 90-kosten.txt nachtragen),
parallel/danach 28-12 Rückfluss (OCR_SLOT_COST_BYTES 235 -> 250 MiB = 262.144.000 Byte,
FP32_EXTRA_BYTES bleibt 367 MiB, Vollindex-Term-Vorlage für S-voll, Rechenbeispiele, Baumhash-Pin),
dann 28-13 Snapshot-Löschung (Owner-Checkpoint), 28-14 Abschluss mit Push-Entscheid C7
(Box-IPs in der lokalen Historie!). Debug-Session Embed-Lock-Timeout läuft separat (boxlos).

Vorheriger Stand (28-07 Messungen, Ergebnisse aller Zellen):
**28-07 MESSUNGEN KOMPLETT (05.10.): alle Messzellen der Matrix gemessen, x86-Hälfte fertig.**
NÄCHSTER SCHRITT: 28-08ff Auswertung/Bericht. OWNER-ENTSCHEID SC4/C5 (Checkpoint C5) offen für fünf
x86-Zellen über der Grenze 1,10 x Rechnung, dazu der vertagte fp32-Entscheid mit BEIDEN Datenpunkten.
Box c7a.8xlarge per aws_box.sh stop geparkt (16:04:27Z bestätigt), ARM-Box geparkt, Abbau-Entscheid
beim Owner. A-Record zeigt verwaist auf die letzte x86-Adresse. Kosten 34,09 von 59,43 USD (Rest 25,34).
Protokoll: 07-typwechsel-x86.txt (Abschnitte c7a.4xlarge, c7a.8xlarge, Zusammenfassung), 90-kosten.txt.

Ergebnisse 05.10. (anon-max / Grenze MiB, Methode des Zellenwerkzeugs):
- c7a.4xlarge: 15 S-T 1534,7/1641,8 getragen; 16 St-T (fits, 4 Slots) 2591,6/2528,8 NICHT getragen;
  17 L-T (fits, 15 Slots) 5623,7/5536,3 NICHT getragen; 18 St-fp32-T (fits, 4 Slots, Download live)
  2844,6/2932,5 getragen. Rückkehr int8 belegt.
- c7a.8xlarge: 19 S-T 1534,3/1641,8 getragen; 20 St-T (fits, 4 Slots) 2560,2/2528,8 NICHT getragen;
  21 L-T (fits, 16 Slots) 5802,8/5794,8 NICHT getragen.
- Alle Zähltore 5000, alle Proben fits und von der Messung bestätigt (kein Wächtereingriff, kein OOM).
- Muster: ab 4 Slots auf x86 liegt der HAUPTPROZESS über der Rechnung (St-T 1640 bis 1756 MiB, L-T 2411
  bis 2530 MiB; ARM m7g.4xlarge St-T 2358,2 und L-T 5481,8 getragen); Slotkosten 212 bis 232 MiB unter B2.
- fp32-Datenpunkte: c7a.xlarge (1 Slot) Mehrbedarf 509,7 MiB, Zelle 11 nicht getragen; c7a.4xlarge
  (4 Slots) Mehrbedarf 223,2 MiB, Zelle 18 getragen (gegen FP32_EXTRA_BYTES 367 MiB). Der Mehrbedarf
  ist eine Differenz zweier Hauptprozess-Maxima und hängt am int8-Gegenstück.
- Crawl-Fix in allen 7 Zellen bestätigt: 6 Runden "crawl is unfinished", keine stale-Lieferung,
  ruhige Runde stale=0, unchanged 0, Selbstvorschub je einmal.
- NEUER PRODUKTBEFUND (nicht angefasst): nach der Rückkehr fp32 -> int8 (10:48:05Z) "the precision of
  the embedding changed, the vector stock is being written again", sofort "could not move 500 files to
  the embed track, they run into the lock timeout" (container-rueckkehr-int8.txt). Gleiches Muster wie
  der Embed-Übergabe-Befund aus Lauf 9 (30 Dateien), hier ein voller 500er-Stapel beim
  Präzisionswechsel; Vollständigkeit des Neuschreibens nicht beobachtet. Kandidat /gsd-debug.
- Umgebung: erster Kettenstart c7a.8xlarge Abbruch 60 (abwaerts URLError), A-Record ~1 min vor dem
  Start umgesetzt (TTL 120), alte Adresse freigegeben; nach 10:55Z Auflösung korrekt, EINE Wiederholung
  rc 0. Merker fürs Runbook: nach A-Record-Wechsel ~3 min bis Kettenstart warten.

Vorgeschichte x86-Hälfte bis 04.10. (zuvor BLOCKED auf AWS-Login, am 05.10. 04:19Z Stopp bestätigt):

**28-07 x86-Hälfte BLOCKED (Auth-Gate, kein Messfehler): AWS-Sitzung abgelaufen (~16:30Z).**
OWNER: aws login (Rezept NEXT.md UPDATE 52), danach weiter mit:
  export FINDLING_LOADTEST_DIR=$HOME/.findling-loadtest/x86; aws_box.sh status (Stopp von innen
  20:23:38Z bestätigen); 00-typwechsel.sh wechsel c7a.4xlarge; known_hosts (Hostschlüssel gleich) +
  A-Record; auf der Box Laufwerte (BISHER_USD aus stand, SATZ_USD_H 0.955081, BOX_START_EPOCH,
  ZELLEN S-T St-T L-T St-fp32-T), ~/work/clog/mit.sh starten, für die fp32-Zelle ~/work/nach-kette.sh
  c7a.4xlarge St-fp32-T (Rückkehr int8), vorpruefung, --restart, Kette mit IMAGE_TAG=18602c48... und
  KORPUS_FRIST=3600; danach c7a.8xlarge (S-T St-T L-T).
Box c7a.2xlarge gestoppt (von innen, shutdown-Verhalten stop belegt), BOX_STOPPED_ISO von Hand in box.env.
ARM-Box weiter geparkt. A-Record zeigt verwaist auf die letzte x86-Adresse. Kosten 17,64 von 59,43 USD.

Ergebnisse x86 (Protokoll 07-typwechsel-x86.txt, Aufbau 06-aufbau-x86.txt):
- Machbarkeitstor c7a.xlarge BESTANDEN in 45 min (Abbilder per Snapshot-Index-Digest, Container einzeln
  neu erzeugt, PostgreSQL 18.6 auf x86_64, amcheck 656 B-Bäume vor/nach REINDEX rc 0, occ status, files:scan).
- c7a.xlarge: 8 S-T 1520,2/1641,8 getragen; 9 St-T (fits, 1 Slot) 1679,5/1753,3 getragen;
  11 St-fp32-T (fits, Download live, Digest im Produkt) 2172,5/2157,0 NICHT GETRAGEN, fp32-Mehrbedarf
  509,7 MiB gegen 367 -> SC4/C5 für den Owner. Rückkehr int8 belegt.
- c7a.2xlarge: 12 S-T 1535,3/1641,8 getragen; 13 St-T (fits, 3 Slots) 2181,9/2270,3 getragen;
  14 L-T (fits, 7 Slots) 3374,0/3468,3 getragen.
- Alle Zähltore 5000, alle Proben stimmen mit der Messung (kein Wächtereingriff, kein OOM).
- Crawl-Fix im Feld auf x86 bestätigt: nur "crawl is unfinished" während des Crawls, keine stale-Lieferung,
  ruhige Runde stale=0, unchanged 0. Lock-Timeout einmal (fp32, 2 Dateien), gutartig.
- Beobachtung: Slot-anon je Slot bei 1 Slot ~296 MiB (x86), bei 3 Slots 235,4, bei 7 Slots 212,5.
Deviation: 05-typwechsel-arm.txt und STATE.md trugen zwei Box-Adressen aus Lauf 8/9 (Gate rot),
durch den Legende-Platzhalter ersetzt (Commit 147a6ed8); die alten Werte stehen noch in der lokalen Historie.

Vorgeschichte x86-Hälfte Zwischenstand (04.10. 10:05Z bis 15:20Z): siehe Commits 1e1cb157, 4a45f184.

Vorgeschichte Lauf 9 (04.10.):
**28-07 Task 2: Lauf 9 (04.10. 04:32Z bis 06:15Z), Zelle 7 L-T auf m7g.4xlarge GEMESSEN. ARM-Hälfte KOMPLETT.**
Vorbereitung: Lauf-8-Stopp per aws_box.sh status bestätigt (InstanceInitiatedShutdown), Box-Klon auf
18602c48, Abbild 5ed5742c (Multi-Arch-Lauf 37176289187 zu 18602c48, Fix im Abbild belegt), Companion-App
aus php/ ersetzt (Baum gleich), A-Record umgesetzt, --restart (Vorrat 0/0), Kette 04:36:31Z.
Ergebnis: rc 0. Probe fits (Reserve 60,4 GB, Slots 15), erzwungen nein, wirksam performance, unter Last
slots=15, Wächter ohne Absenkung, OOM 0. Zähltor bestanden 5000 (vorrat-teilkorpus 30 = vorrat-global 30,
eingebettet 4970). Ende 06:08:11Z (Trigger bis Ende 1:30:37, Planwert 0:45).
anon-max (Methode des Zellenwerkzeugs: rss_sampler max_anon, trifft Lauf 7 exakt): 5481,8 MiB, Rechnung
5033,0, Grenze 5536,3, Urteil GETRAGEN (12-slotkosten.py). Lauf 8 nach derselben Methode 5591,4 (die
5630,3 waren eine andere Methode). Slot-anon je Slot 220,1 MiB (B2 235), Hauptprozess-max 2319,0 MiB.
CRAWL-FIX IM FELD BEWIESEN: (a) während des Crawls nur "stands down, the crawl is unfinished" (5 Runden
04:36 bis 04:56Z), danach busy-Runden, KEINE stale-Lieferung; erste ruhige Runde 05:38:48Z seen=57187
stale=0 (schließt auch den Lauf-8-Vorbehalt zum ruhigen Takt). (b) Zähltor exakt 5000 ja,
vorrat-teilkorpus 0 NEIN (30, siehe Befund). (c) keine unchanged-Zweitwelle: unchanged 0 über alle
225 Durchgänge, Selbstvorschub nur einmal vor dem Crawl-Vorrat.
NEUER PRODUKTBEFUND (nicht angefasst, Owner): Übergabe ocr -> embed lief zweimal in ein 60-s-Timeout
("could not move 30 files to the embed track, they run into the lock timeout", 05:02:56Z und 05:34:19Z,
je andere 30 Dateien); die Dateien hängen bis zum OCR-Lock-Ablauf (1800 s) und werden einmal neu
OCR-verarbeitet. Nutzerrelevanz: bis 30 min verzögerte Vollständigkeit am Ende, doppelte OCR für den
Stapel, kein Datenverlust. Ursache der Ausnahme unbelegt (queue.py requeue loggt ohne exc_info).
Stopp: Kette setzte am Ende shutdown -h +2 (poweroff 06:12:23Z) vor dem Abholen; kurzer Abholstart
06:13:05Z, aws_box.sh stop 06:15:06Z, BOX_STOPPED_ISO gesetzt, Box geparkt. A-Record zeigt verwaist auf
<adresse-der-box> des Abholstarts. Kosten 12,69 von 59,43 USD (Lauf 9: 1,6672 h + 0,0336 h).
Rohdaten: 05-typwechsel-arm.txt (Lauf 9), m7g.4xlarge/L-T/ mit container-auszug.txt, m7g.4xlarge-kette.log.
NÄCHSTER SCHRITT (nach Owner-Wort): x86-Hälfte c7a, Machbarkeitstor (amd64-Abbilder, PostgreSQL-Start,
REINDEX), dann Zellen 8 bis 21; offen für den Owner: Befund Embed-Übergabe-Timeout (/gsd-debug?).

Vorgeschichte Lauf 8 (04.10.):
**28-07 Task 2 BLOCKED: Lauf 8 (04.10. UTC 03.10. 22:45 bis 23:59), Zelle L-T auf m7g.4xlarge, Abbruch 71.**
Vorbereitung vollständig: Box-Klon auf bbd23578, Abbild 5242e47f (Multi-Arch zu bbd23578,
Baumhash a6ad7397 gleich), Companion-App aus php/ ersetzt, --restart, Kette 22:49:16Z. Probe fits
(Slots 15), wirksam performance, unter Last slots=15. Zähltor bei Trigger + 3600 s: vorrat-teilkorpus
427, vorrat-global 427, eingebettet 5000, Summe 5427, Abbruch 71 um 23:50:25Z.
RECONCILE-FIX IM FELD BELEGT: vorrat-global = vorrat-teilkorpus (Lauf 7 an derselben Stelle 549
ausgeschlossene Dateien), erste Reconcile-Runde seen=52549 stale=401 ohne die 549, findling:diagnose
einer loadtest-Datei = skipped/excluded. Vorbehalt: nach Teilkorpus-Ende keine ruhige Runde vor der
Lesung, der ruhige 300-s-Takt selbst ist nicht beobachtet.
NEUER BEFUND (Ursache des Abbruchs): Teilkorpus fertig 23:44:19Z (5000/5000), im selben Moment
Selbstvorschub ("work stock ran dry while the crawl is unfinished") und danach der GESAMTE
Teilkorpus ein zweites Mal im Vorrat (scheduled 3037 um 23:46:26Z; Durchgänge 23:44 bis 23:56:
claimed 5032, unchanged 5000). Ab 23:50Z kein weiterer Selbstvorschub, Vorrat 23:54Z 0. In Lauf 7
lag der Crawl dem Worker voraus, hier lief der Vorrat ab 22:51Z wiederholt leer (Worker mit 15
Slots schneller als der Crawl). Warum der Crawl nach dem letzten Stück als unfertig gilt und den
Teilkorpus erneut liefert, ist NICHT geklärt (CrawlAdvanceService/StorageCrawlJob nicht gelesen;
--restart räumt SchedulerJob und StorageCrawlJob sauber, NC-Cron lief nicht: letzter Background-Job
18:10). Nutzerrelevanz vermutlich: nach der Erstindexierung ein zweiter Komplettdurchgang über alle
Dateien (je Datei billig "unchanged", aber HTTP-Abrufe und Vorratsschub in Größe des Bestands).
Kein Umgebungsproblem, daher keine Wiederholung (Auftrag Punkt 6).
Optionen für den Owner: a) /gsd-debug zum zweiten Crawl-Durchgang (Produktbefund, empfohlen nach
Regel "Produkt-Fix vor Harness-Patch"), danach Lauf 9; b) Werkzeug: Zähltor zählt nur Vorrat, der
noch nicht eingebettet ist (Teilkorpus-Dateien ohne Endzustand), oder liest erst nach Vorrat 0;
c) KORPUS_FRIST für L-T kürzer/länger (nur Laufwert, fragil).
Hinweis anon-max (Zelle nicht gemessen): 5630,3 MiB um 23:40:10Z unter Last, Rechnung 5033,0,
Grenze 5536,3 (Methode Summe rssanon je Zeitpunkt, ganze Serie; dieselbe Methode gibt für Lauf 7
5451,9/5510,0 statt protokollierter 5420,0/5474,3). Wäre bei einer gemessenen Zelle SC4/C5.
Box: von innen gestoppt (shutdown -h +1, 23:58:45Z), weil aws_box.sh stop an der ABGELAUFENEN
AWS-Sitzung scheiterte; AWS-Bestätigung (aws_box.sh status) steht aus, Owner loggt ein.
A-Record zeigt auf <adresse-der-box> von Lauf 8 (verwaist). Kosten 11,27 von 59,43 USD (Lauf 8: 1,225 h = 0,98 USD).
Rohdaten: 05-typwechsel-arm.txt (Lauf 8), m7g.4xlarge/L-T-abbruch71-lauf8/ mit container-auszug.txt.
Danach (nach Owner-Wort): L-T erneut, dann x86-Hälfte c7a (Block 14, Machbarkeitstor).

Vorgeschichte Quick 261003-wxg (04.10.):
**28-07 Task 2: Blocker L-T GELÖST durch Quick 261003-wxg (Owner-Entscheid a + b, 03.10.).**
a) Produkt-Fix: die PHP-Hälfte markiert im File-Slice jede Datei, die eine Ausschlussregel von
heute trifft, live als skipped(excluded) (ExclusionService::isExcluded auf mountRelativePath, nie
gespeichert); der Container plant eine solche Datei nicht ein, solange er sie nicht kennt, und
speichert nichts (Regelaufhebung wirkt in der nächsten Runde; CR-01 bleibt). b) Zähltor zählt
den Vorrat pfadscharf aus oc_findling_queue (Lauf-7-Zahlen 5549 -> 5000). Commits 6dd65fc3,
63762caa, 12c659dd, NUR LOKAL. NÄCHSTER SCHRITT: Push (alle lokalen Commits) + CI (php -l,
PHPUnit ReconcileControllerTest, neues Container-Abbild) abwarten, dann Lauf 8 = Zelle L-T auf
m7g.4xlarge mit NEUEM Abbild UND neuer Companion-App aus php/ in custom_apps/findling der Box
(beide Hälften nötig, sonst bleibt der Schub); danach x86-Hälfte c7a (Block 14).

Vorgeschichte Lauf 7 (03.10.):
**28-07 Task 2 BLOCKED: Owner-Entscheid zur Zelle L-T auf m7g.4xlarge (Lauf 7, 03.10.).**
Lauf 7 (Start 11, Typwechsel auf m7g.4xlarge, Abbild d33bfcae von f73566c1, Companion ersetzt):
Zelle 5 S-T GEMESSEN (rc 0, Zaehltor 5000, 3:39 h, anon-max 1499,6 MiB gegen 1641,8),
Zelle 6 St-T GEMESSEN (rc 0, Probe fits Reserve 62,1 GB Slots 4, wirksam standard/4, Zaehltor 5000,
anon-max 2358,2 MiB gegen 2528,8). Zelle 7 L-T: Probe fits (Slots 15), wirksam performance/15, aber
ZWEIMAL Abbruch 71 mit 5549 (vorrat 549 + eingebettet 5000), der Teilkorpus war jeweils fertig.
Beleg (05-typwechsel-arm.txt): die 549 sind Dateien unter den Ordner-Ausschluessen (loadtest 500,
Templates/Photos/Beispiele 49, fileids 3 bis 2634), die der Reconcile in jeder ruhigen Runde neu
einplant (kein etag gespeichert, _compare haelt sie fuer stale), beim Containerstart und dann alle
~300 s. Die Lesung bei Trigger + 3600 s faellt strukturell ~17 s nach den 12. Takt; ist der
Teilkorpus vorher fertig (nur L-T auf 16 Kernen), sieht sie den Schub. Wiederholung (die eine
erlaubte) brach wie vorhergesagt identisch ab. PRODUKTBEFUND mit Nutzerrelevanz: bei Ausschluessen
im Leerlauf alle 5 min ein Schub ausgeschlossener Dateien, dauerhaft. Optionen fuer den Owner:
a) Produkt-Fix: Reconcile beachtet die Ausschluesse oder der Worker merkt sich das excluded-Verdikt
samt etag (empfohlen, Owner-Regel "Produkt-Fix vor Harness-Patch"; neues Abbild noetig, dann L-T neu),
b) Werkzeug: Zaehltor zaehlt auch den Vorrat teilkorpus-scharf (wie cvf fuer skipped/failed),
c) KORPUS_FRIST fuer L-T so waehlen, dass die Lesung zwischen zwei Takten liegt (nur Laufwert).
Box geparkt (aws_box.sh stop 18:51:09Z), 10,24 von 59,43 USD. Danach: L-T, dann x86-Haelfte c7a
(Block 14, Machbarkeitstor). Alle Commits NUR LOKAL (91b4eb94..754f83b6).

Vorgeschichte (Lauf 5, 02.10.):
Lauf 5 (02.10., Start 8, Kette 05:58:50Z): die Tor-Verschiebung 261002-af9 wirkt im Feld,
vorrat-tor altvorrat 0 BESTANDEN (05:59:00Z, zwischen Registrierung und Bewaffnung kann
kein Container nachschieben). Alle Tore bis zum Trigger grün (Grenze 2g/0, Baumhash ja,
Wirksamkeit economy slotsInForce 1). ABER: Zähltor nach 3600 s verfehlt mit 5041 statt
5000, Abbruch 71 um 06:59:16Z. Ursache belegt (243aabf9, 04-teilkorpus-arm.txt Lauf 5,
Dateiidentität gegen oc_filecache): der Teilkorpus selbst ist EXAKT vollständig
(vorrat 3535 + eingebettet 1465 = 5000); die 41 zuviel sind sämtlich Alt-Endzustände
AUSSERHALB des Teilkorpus in oc_findling_file_state (35 skipped + 6 failed: 20x too_large
loadtest/drill-CSVs, 9x Beispieldateien der Homes, 12x sprachfall corpus/*; updated_at
30.09./01.10., kein Eintrag unter files/teilkorpus). Diese Tabelle gehört der PHP-Hälfte
und überlebt --rm-data UND --restart (93i räumt nur oc_findling_queue); das Zähltor
summiert die globalen Zähler übersprungen/fehlgeschlagen mit. Die Formel aus 261001-vl0
war an Lauf 2 kalibriert, wo die 41 eine Crawl-Lücke zufällig exakt füllten. Optionen
für den Owner (Werkzeugänderung nur mit Owner-Wort, Runbook 7.1): a) Zähltor zählt nur
Zustände von Dateien unter files/teilkorpus (Pfadfilter im Werkzeug, kein Produkteingriff,
empfohlen), b) Produkt-Fix: --restart räumt auch oc_findling_file_state (Verlängerung
von 93i, ändert den Notfallhebel), c) oc_findling_file_state vor dem Kettenstart von
Hand leeren (Eingriff in Produktzustand). Stand: Box-Klon auf fcbb1273, Box von innen
gestoppt (shutdown 07:09:39Z, Stopp-Verhalten belegt) bei 3,21 USD (Deckel 59,43).
ACHTUNG: aws_box.sh stop steht aus, die AWS-Sitzung ist abgelaufen (Owner loggt ein);
BOX_STOPPED_ISO fehlt in box.env, Stoppzeit 07:09:39Z steht in 90-kosten.txt.

(28-06 fertig: S-voll 19,58 h, C1 743,9 MB innerhalb, Box geparkt; Owner-Signal "weiter".
28-05 fertig: Owner-Freigabe 30.09.2026, Deckel 119,82 h / 59,43 USD mit Anker, Timer 71,32 USD, Guthaben 104,11 USD; cb49fa70. 28-01 fertig: Teilkorpus, Rechenblatt, Slotkosten,
00-ablauf.md; b8e8c785. 28-02 fertig: 11-probe-route.py, 10-zelle.sh, 93b-nullstand.sh,
00-kette.sh, 59 boxlose Tests; 1976584a. 28-03 fertig: aws_box.sh Satztabelle/Architektur/
SG-Schonung, 00-typwechsel.sh mit Zieltyp; b1191dc5. 28-04 fertig: Runbook x86/USD-Deckel/
Abbau bis 0 Snapshots, Vorprobe "postgres ja abbilder ja"; 9d08f30f. Alles nur lokal).

Phase-27-Abschluss (2026-09-29): 16/16 Plaene in 7 Wellen; Owner-Abnahmen 27-01, 27-15
(gemeinsam per Playwright) und Phase ("ok abgenommen"); Push-Entscheid "push-now" =
106 Commits (d91305df..a8e3d7ea), HaRP-Routen-Ratsche um /probe und /probe/state
erweitert (2b9de323); Code-Review 1C/11W/7I, 12/12 gefixt (918f340d..d25c85e8);
Verifikation human_needed 4/4; zweiter Push bis c87a0239, alle sechs Workflows gruen
(PHPUnit 36596834116). Offen: fp32-Zweig nur automatisiert belegt; MT-Uebersetzungen
WR-02/WR-10 beim Release-Text lesen; WR-04-Rest (no_text_layer in "Uebersprungen")
nach Phase 29 verschoben. Quick 260929-kii (Deckungsgrad-Nenner) mitgereist.

Phase-26-Abschluss (2026-09-29): 14/14 Plaene in 6 Wellen, Verifikation passed 4/4;
Push-Entscheid Owner "Ja" = 229 Commits gepusht (cce78abd..d91305df), CI komplett gruen:
SC2-Kill-Test (Lauf 36522819711), PHPUnit 386 Tests (36522819728, erledigt auch
24-HUMAN-UAT Test 1 und die 25-03/25-04-Posten), arm64-Messleiter (36523219615,
Faktoren 2,000/1,979 gegen 1,05, Gesamt 3,958 = W4-Obergrenze, kein K1-Rueckfall).
Code-Review 1C/2W/4I: CR-01 halt-Rennfenster (91fefe8f), WR-01 unlock_held im
Catch-all (777f3a59), WR-02 Merker-Reihenfolge (15eb03d5) alle GEFIXT mit RED-Beleg;
IN-01..04 dokumentiert offen. Owner-Abnahmen: Latenzprobe D-26-12 (nice kappt
Ausreisser, p50/p95 unveraendert, Zahlbeleg-Grundlage fuer Issue #19) und Phase 26
gesamt. Entscheide D-26-01..16 in 26-CONTEXT.md. Commits nach dem Push wieder NUR LOKAL.

Phase-25-Abschluss (2026-09-28): 12/12 Plaene, Code-Review 0C/4W/4I, alle 4 Warnings
gefixt (00ecee3, 25ec895, 8ca5983, be2779c); Verifikation passed 4/4; Suite 3711 gruen.
fp32-Release model-e5-small-fp32-614241f live und immutable (Upload durch Orchestrator
im Owner-Auftrag, Gegenprobe committet). Entscheide D-25-01..15 in 25-CONTEXT.md.

Phase 24 secure (2026-09-28): SECURED 24/24 (22 mitigate, 2 accept AR-24-01/02), 29a6cd6.
AR-24-02 (Schreibweg nur occ) verliert mit der Schreibroute in Phase 27 seine Begruendung.

Phase-24-Abschluss (2026-09-28): Code-Review 0C/2W/6I, WR-01 (637c02b) und WR-02 (d0705e4)
gefixt; Verifikation 5/5 Kriterien (human_needed); Live-UAT bestanden mit einem Befund
(memory.max ueber MemTotal hob die Profilschwelle an), gefixt in b345fa3. Offen in
24-HUMAN-UAT.md nur Test 1: PHPUnit (php.yml) nach dem naechsten Push, Push-Entscheid beim Owner.

## Accumulated Context

### Entscheidungen

Volle Liste in PROJECT.md (Key Decisions) und .planning/milestones/v1.3-ROADMAP.md.
Fuer v1.4 unmittelbar tragend:

- Kein Vorwaermen beim Start, Ladefenster-Restrisiko akzeptiert (D-03/D-08, AR-23-01);
  ein Schnellpfad in model.py ist bewusst NICHT gebaut.

- dismax ist auf Messbasis verworfen (MESS-09); die Rangprobe-Grenze 0,81 steht in
  docs/language-analyzers.md.

- Sprachmenge ist sechster Versionsmerker, wird nie gesaet; Schema-1-Bestand ist designierter
  Zwischenzustand, keine Drift (Debug upgrade5, vierte Ausnahme in version_mismatch).

- Store-Regeln: eine Messzahl (730,2 MB), Gate test_store_metadata.py (RESIDENT_FIGURE),
  Tag im Store nie verschieben (v1.3.0 liegt auf 744d7e4).

- Roadmap v1.4 (27.09.): Reihenfolge 24 -> 29 streng seriell als Sicherheitsbedingung
  (MOD-01 vor jedem Modellschalter, H1 vor H2, N-Slot-Probe nach H2, Abnahme-Anfahrt vor
  Release). Rueckfall bei K1: Phase 26 schrumpft auf Befund, Entscheid datiert vor H2-Bau.

- 28-01 (29.09.): Teilkorpus-Bereiche und Seitenziehung als Kopie im Box-Skript (kein Pillow,
  kein sys.path), per Test gegen build_load_corpus gepinnt. Rechnung_anon zaehlt Gewichte,
  Schneider und eine Aktivierung nicht doppelt (in MAIN_PROCESS_BASELINE_BYTES aus B2),
  Spurreserve abgezogen. Deckel-Vorschlag 58,74 USD, mit Anker-Zelle 59,43 USD (Saetze
  29.09.), Freigabe durch den Owner offen (SC1, Checkpoint C1).

- 28-02 (29.09.): Zelle nutzt 93b-nullstand.sh (vier Quellen ohne Neuaufbau) statt
  93-nullstand.sh, weil 93 den Vorrat vor Probe und Wirksamkeit fuellte (Pitfall 2).
  Ende der Zelle zusaetzlich indexed > 0. Kette: Deckel vor jeder Zelle ohne shutdown
  (83, Box laeuft weiter), Timer bei Deckel x 1,20 bleibt stehen, fehlgeschlagene Zelle
  beendet die Kette (84) und zieht den Timer auf 60 min vor; Marke VORPRUEFUNG=stop-ja
  als Laufwert von Hand nach 00-typwechsel.sh vorpruefung.

- 28-03 (30.09.): aws_box.sh rechnet mit dem Satz des Typs aus describe-instances (Tabelle
  der sechs Typen, Preiskarte 29.09.); Typ ohne Satz: stop parkt trotzdem, schreibt keine
  Kostenzahl, endet 1. destroy schont bei geteilter Security Group auch das Schluesselpaar
  und nimmt die andere Instanz samt Volumes aus dem Tag-Sweep. 00-typwechsel.sh: nur
  innerhalb einer Familie (54), ohne Kapazitaet Typ zurueck und Box gestoppt (55), kein
  Rueckfall. Zone in aws_box.sh bleibt fest eu-central-1c (A7 offen fuer 28-05).

- 28-04 (30.09.): lokale Vorprobe arm64 nach amd64 (qemu, containerd-Store): postgres:18.6
  startet mit arm64-Datenverzeichnis, amcheck und REINDEX sauber, Signedness signed;
  amd64-Variante wird zu arm64-Tag nachgezogen. Ergebnis "postgres ja abbilder ja", Tor auf
  der Box bleibt Pflicht (AIO-glibc nicht geprueft). Runbook: Deckel in USD je Box-Satz,
  Block 7b fio, Block 14 x86-Box mit Tor 1 h 30, 7.3 Kette, Abbau bis 0 Snapshots
  (Snapshot erst nach SC4 und Owner-Wort C6). Zone 1c fuer c7a = Pruefpunkt Block 14 Schritt 0.

### Termine und Owner-Checkpoints

- **Issue #14 (budachst):** Antwort mit Zitat gepostet (issuecomment-5853918446), Issue bleibt
  OFFEN, bis budachst nach dem Upgrade bestaetigt. Nicht selbst schliessen (Owner-Regel).

- **Kill-Kriterium:** Ende September einmalig die Nextcloud-Conference-Nachberichte ansehen,
  danach quartalsweise. Zuletzt geprueft 21.09.2026: NICHT ausgeloest.

- **Findling-Pro-Entscheid:** vertagt auf 03.11.2026 (Go-Kriterium >=10 Grenzen-Anfragen oder
  1 Pilotkunde >250 Nutzer; Stand 21.09.: null Signale).

- **Korpus-Snapshot snap-03f1d1d9ad9262704:** bleibt im Standard-Tier (~2,85 USD/Monat,
  dritter Behalten-Entscheid); naechste Wiedervorlage beim v1.4-Close.

### Offene Blocker

- **OFFEN 04.10. (Lauf 8): zweiter Crawl-Durchgang über den fertigen Teilkorpus nach dem Selbstvorschub,
  L-T Abbruch 71 mit 5427 (vorrat-teilkorpus 427); Owner-Entscheid a/b/c, siehe Naechster Schritt.**
- **GELÖST 04.10. (Quick 261003-wxg, Owner-Entscheid a + b): Reconcile beachtet die Ausschlüsse,
  Zähltor-Vorrat teilkorpus-scharf.** Lauf 8 braucht neues Abbild + neue Companion-App.
  Ursprünglicher Befund:
- ~~**28-07 Lauf 7, Zelle L-T m7g.4xlarge, Abbruch 71 zweimal (03.10.):**~~ Reconcile plant die 549
  ausgeschlossenen Dateien in jeder ruhigen Runde neu ein, Zaehltor liest den Vorrat global.
  Box geparkt, 10,24 von 59,43 USD.

- **GELOEST 03.10. (Quick 261003-d3y): Owner-Entscheid P2 + Zellen 3/4/10 gestrichen.**
  Probe prüft die Vorschlags-Schwellen (nofit hardware_short), Zellenwerkzeug Abbruch 74.
  Ursprünglicher Befund:
- ~~**28-07 Zelle St-T, Abbruch 69 (Lauf 6, 02.10.):**~~ Probe sagt fits (2,03 GB verfuegbar,
  1,61 GB noetig), Profil standard gespeichert, wirksam blieb economy: profile.effective()
  deckelt auf suggest(), und suggest verlangt fuer Standard >= 6 GB UND >= 3 Kerne (Referenzbox:
  2 Kerne, 2 GB Grenze). Produktwiderspruch Probe vs. Wirksamkeit, auf der Admin-Seite sichtbar
  ("Fits" und zugleich "less hardware than the chosen profile needs"). Der geplante
  Erzwingen-Weg der Zellen 3/4 wird ebenso gedeckelt. Owner-Entscheid: Semantik D-24-07
  (Probe vor Schwelle oder Schwelle in die Probe) und Umgang mit den Zellen St-T/L-T auf
  m7g.large. Beleg 06545083, 04-teilkorpus-arm.txt Lauf 6. Box geparkt, 3,88 von 59,43 USD.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 261003-wxg | 28-07 Owner-Entscheid a+b: PHP markiert ausgeschlossene Dateien im File-Slice live als skipped(excluded) (isExcluded/mountRelativePath, nie gespeichert), Reconcile lässt unbekannte markierte Dateien liegen (Lauf 7: 549 alle ~300 s); Zähltor-Vorrat pfadscharf aus oc_findling_queue (5549 -> 5000) | 2026-10-04 | 12c659dd | Done (Python-Suite grün; php -l/PHPUnit = CI-Vorbehalt; Lauf 8 braucht neues Abbild + neue Companion-App) | [261003-wxg-reconcile-beachtet-ausschluesse-zaehltor](./quick/261003-wxg-reconcile-beachtet-ausschluesse-zaehltor/) |
| 261003-d3y | 28-07 D-24-07 P2: Probe prüft vor der Messung die Vorschlags-Schwellen über profile.suggest (nofit hardware_short, keine Pause/Download/Kinder), Ursache in PHP/JS/16 Katalogen; Zellen 3/4/10 gestrichen (18 Zellen), 10-zelle Abbruch 74 | 2026-10-03 | 3d1c6d72 | Done (4408 Tests grün, 2 lokale CRLF-Artefakte 11-probe-route.py; php -l = CI-Vorbehalt) | [261003-d3y-d-24-07-nachschaerfung-p2-probe-prueft-v](./quick/261003-d3y-d-24-07-nachschaerfung-p2-probe-prueft-v/) |
| 261002-cvf | 28-07 Zaehltor zaehlt zeit- und pfadscharf (Zaehlmarke vor dem Trigger, nur frische files/teilkorpus-Zustaende via psql; Beleg 5041 -> 5000, Kalibrierfalle 4959 -> 71) | 2026-10-02 | a2b0fcf9 | Done (545 Tests gruen) | [261002-cvf-zaehltor-teilkorpus-scharfe-zaehlquelle](./quick/261002-cvf-zaehltor-teilkorpus-scharfe-zaehlquelle/) |
| 261002-af9 | 28-07 Vorrats-Tor vor die Bewaffnung gezogen (Schritt vorrat-tor, Abbruch 73 beziffert Altbestand; 93b-rc-13 zurueckgebaut; Nachschub nach Bewaffnung bricht nicht mehr ab) | 2026-10-02 | c04e7431 | Done (543 Tests gruen) | [261002-af9-vorrats-tor-vor-die-bewaffnung-ziehen](./quick/261002-af9-vorrats-tor-vor-die-bewaffnung-ziehen/) |
| 261002-93i | 28-07 Blocker-Fix a+b: occ findling:index --restart raeumt den Arbeitsvorrat (QueueMapper/QueueService::clear(), Produkt-Fix fuer den Notfallhebel) + 93b-Nullstand urteilt ueber den Vorrat (rc 13) + 10-zelle Abbruch 73 vor Samplern/Trigger | 2026-10-02 | 599a74d2 | Done (65+477 Tests gruen; php -l/PHPUnit = CI-Vorbehalt) | [261002-93i-findling-restart-raeumt-arbeitsvorrat-nu](./quick/261002-93i-findling-restart-raeumt-arbeitsvorrat-nu/) |
| 261001-vl0 | 28-07 Zaehltor: Formel zaehlt eingebettet statt indexiert (Vorrat enthaelt offene Einbettungsauftraege), Leserace per Doppellesung stabilisiert, Beleg-Test 6937 -> 5000 + Positivkontrolle + Race-Test | 2026-10-01 | 6d114659 | Done (64 Tests gruen auf main) | [261001-vl0-findling-28-07-zaehltor-fix-formel-auf-e](./quick/261001-vl0-findling-28-07-zaehltor-fix-formel-auf-e/) |
| 260929-kii | Deckungsgrad-Nenner waechst mit neuen Dateien (ScanRecountJob, Nachzaehlung absolut, Satz statt Prozent bei Zaehler > Nenner) | 2026-09-29 | bbb4f406 | Verified | [260929-kii-deckungsgrad-nenner-waechst-mit-neuen-da](./quick/260929-kii-deckungsgrad-nenner-waechst-mit-neuen-da/) |
| 260929-s7p | Issue #14: Team-Folder-Dateien mit ACL als Mitglied lesen (ReaderContext), Datei-ID in der Fehlerliste, CI-Job team-folder-acl; Auslieferung als 1.3.1 | 2026-09-29 | 0556d06d | Needs Review (PHPUnit + CI-Job nach Push) | [260929-s7p-issue14-acl-reader-context](./quick/260929-s7p-issue14-acl-reader-context/) |

### Pending Todos

- 1 pending: Issue #18 Fix-Kandidaten einplanen (JPG-Verdikt, HEIF, Download-Groessenpruefung)
  -- wartet auf budachst-Antwort (issuecomment-5865917799), Slot-Entscheid beim Owner
  (.planning/todos/pending/2026-09-28-issue-18-jpg-verdikt-heif-download-fixes.md)

## Deferred Items

Aus Phase 23 (Details in phases-Archiv v1.3-phases/23-*/deferred-items.md):

- F-23-04 -> v1.4-Backlog.
- idle-Guard fuer EmbeddingModel.release() -> v1.4 (Mitnahme-Kandidat Phase 25, Plan-Schnitt prueft).
- IN-01..03 dokumentiert offen (23-REVIEW.md).
- Aufraeumen: Worktree nextcloud-search-worktrees/issue-14 plus Branch
  fix/issue-14-teamfolder-acl loeschen (Dateisperre pruefen).

Aeltere Merker:

- Zwei Prosastellen nennen noch `DEFAULT_FIELDS`: `store/repo.py:128` und `:1448`
  (naechster Plan, der repo.py ohnehin oeffnet, nimmt sie mit).

- Leerer Textauszug bei reinem Sprachfeld-Treffer (SnippetGenerator haengt an FIELD_BODY_DE,
  Annahme A5): seit v1.3 in der veroeffentlichten Grenzenliste; Behebung waere eigener Plan
  mit Owner-Entscheid.

- run-Block "Store upgrade 3" in deploy-harp.yml bei ~20,7k Zeichen: vor einem
  ${{ }}-Ausdruck dort erst kuerzen oder Werte per env:-Block hereinreichen.

- L-16-04-Kommentarfix beim naechsten Workflow-Plan (paths-Filter gilt nicht fuer Tag-Pushes).
- Systemplatten-Skripte Phasen 5-6.1: Repo-Aufnahme erst nach Geheimnis-Durchsicht.
- Estnischer Stemmer nicht verfuegbar: aktiv an die Buerokratt/OS2ai-Spur kommunizieren.
- Auditor-Hinweise aus 23-SECURITY.md (beide advisory): uv lock --check laeuft in keinem
  CI-Schritt; arm64-Manifestcheck war Einmal-Nachweis, store-submit.yml prueft ihn nicht selbst.

## Session Continuity

Last session: 2026-10-04T00:30:00.000Z
Stopped at: Quick 261003-wxg umgesetzt (3 lokale Commits); nächst Push + CI-Abbild + Lauf 8 L-T (neues Abbild + neue Companion-App), Box geparkt
Resume file: None

## Operator Next Steps

- /gsd:execute-phase 25 (25-01 wartet auf den Owner-Upload)
- Push-Entscheid (alles lokal); nach dem Push php.yml pruefen (24-HUMAN-UAT Test 1)
