---
phase: 11-haertung-und-store-einreichung-v1-1
plan: 06
subsystem: messung
tags: [di-10-01, di-10-02, box-anfahrt, kostendeckel, lastwerkzeug, sprachfaelle]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: "scripts/ops/search_load.py mit EmptyResultGroup, min_hits und hits_per_request (Plan 11-02)"
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: "98b-sprachfaelle.sh mit Fremdbestand-Vorpruefung und dreiwertigem Urteil, 00-ablauf.md mit der vorher aufgeschriebenen Erwartung (Plan 11-03)"
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: "der 52.111er Messindex auf der AWS-Box, die Vergleichszahlen des 10.09. und die Diagnose 98b-sprachfaelle-diagnose.txt"
provides:
  - "DI-10-01 geschlossen: der neue failures-Zaehler ist gegen eine unabhaengige Zaehlung im Nextcloud-Protokoll aufgerechnet, 16 plus 14 gleich 30"
  - "DI-10-02 NICHT geschlossen, mit Beleg: die Vorpruefung misst einen Antwortdeckel von 26 und kann die Schwelle 64 nie erreichen"
  - "sieben Rohdateien und der Bericht unter docs/measurements/2026-09-werkzeugfixe/"
  - "die Box ist angehalten, 1,97 h und 0,2285 USD gegen den Deckel 4 h / 0,50 USD"
affects: [11-09, 11-11, 11-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zwei unabhaengige Zaehlungen derselben Sache, und wo sie abweichen, wird die zweite Ursache gemessen statt die Abweichung geglaettet"
    - "Protokollzaehlung nach reqId statt nach Zeile: ein abgebrochener Aufruf hinterlaesst zwei Zeilen, app_api und findling"
    - "Eine verfehlte Erwartung wird als verfehlt berichtet, und das Messskript wird waehrend seines eigenen Laufs nicht nachgebessert"
    - "Rohdaten byteidentisch ueber sha256 auf beiden Seiten, Passwort-Gegenprobe vor jedem Commit"

key-files:
  created:
    - docs/measurements/2026-09-werkzeugfixe/README.md
    - docs/measurements/2026-09-werkzeugfixe/rohdaten/01-lastwerkzeug-stufe16.json
    - docs/measurements/2026-09-werkzeugfixe/rohdaten/02-lastwerkzeug-stufe08.json
    - docs/measurements/2026-09-werkzeugfixe/rohdaten/03-nc-protokoll-abbrueche.txt
    - docs/measurements/2026-09-werkzeugfixe/rohdaten/04-bestand-vor-der-messung.txt
    - docs/measurements/2026-09-werkzeugfixe/rohdaten/05-sprachfaelle.txt
    - docs/measurements/2026-09-werkzeugfixe/rohdaten/06-kosten.txt
    - docs/measurements/2026-09-werkzeugfixe/rohdaten/07-fremdbestand-gegenprobe.txt
    - docs/measurements/2026-09-werkzeugfixe/skripte/71-protokoll.py
    - docs/measurements/2026-09-werkzeugfixe/skripte/72-fremdbestand.py
  modified: []

key-decisions:
  - "Die Abbruchbedingung 52.111/37/0 war verletzt (gemessen 52.137/44/6) und wurde NICHT wegerklaert: die Anfahrt hielt an, der Ist-Stand ging in die Rohdatei, und der Owner entschied neu. Die Differenz von 39 ist der Sprachfall-Korpus, der Lastkorpus steht unveraendert bei 49.980 indexiert"
  - "Waehrend der Rueckfrage lief die Box weiter statt angehalten zu werden: ein Start wechselt die Adresse und macht die ganze Ruestfolge erneut faellig, also waere das Anhalten teurer gewesen als die 0,002 USD je Minute"
  - "Die Zaehlung im Protokoll erfolgt nach reqId und nicht nach Zeile. Eine Zeilenzaehlung haette 28 statt 14 ergeben, weil jeder Abbruch zwei Zeilen hinterlaesst"
  - "Die Lueckenerklaerung wurde gemessen und nicht vermutet: der Begriff Mahnung traegt im Lastkorpus 0 Treffer, und die Rotation der Begriffe gibt ihm auf Stufe 16 genau 16 Auftritte"
  - "Die Gegenprobe zur Vorpruefung steht als eigene Rohdatei 07 und nicht als Anhang an 05: die Ausgabe des Messskripts bleibt unberuehrt, damit der Ausdruck NICHT MESSBAR nicht durch erklaerenden Text in eine Datei geraet, in der ihn das Skript nicht geschrieben hat"
  - "05-sprachfaelle.txt behaelt ihren Box-Pfad in der Kopfzeile, weil die Rohdatei des 10.09. denselben traegt und eine nachbearbeitete Messrohdatei jede Zahl daneben unbelegt macht"

patterns-established:
  - "Eine Abbruchbedingung, deren Pruefbefehl die genannte Zahl bauartbedingt nicht liefern kann, ist ein Planfehler und keine Formalie"
  - "Eine Messgroesse, die am selben Deckel haengt wie das, worueber sie urteilen soll, kann ihre Schwelle nie erreichen"

requirements-completed: []

# Metrics
duration: 2h 40min
completed: 2026-09-10
---

# Phase 11 Plan 06: Die eine Box-Anfahrt für die zwei Werkzeug-Fixe Summary

**Der neue Zähler des Lastwerkzeugs ist gegen eine unabhängige Zählung im Nextcloud-Protokoll aufgerechnet und geht auf (16 Anfragen ohne Treffer plus 14 Abbrüche ergeben die gemeldeten 30), während der Fix am Sprachfall-Skript seine eigene Schwelle nicht erreichen kann, weil die Route jede Antwort bei 26 deckelt: DI-10-01 ist geschlossen, DI-10-02 nicht.**

## Performance

- **Duration:** 2 h 40 min insgesamt, davon 1,97 h Box-Laufzeit
- **Box:** gestartet 2026-09-10T21:51:06Z, angehalten 23:49:11Z
- **Kosten:** 0,2285 USD von 0,50 USD freigegeben, keine Überschreitung
- **Tasks:** 4 von 4
- **Files created:** 10

## Accomplishments

- **Die Freigabe stand vor der ersten Minute.** Der Owner hat den Deckel 4 h / 0,50 USD am 10.09. bestätigt, die Zeile steht in `docs/measurements/2026-09-werkzeugfixe/README.md`, und `box.env` trug zu diesem Zeitpunkt keinen neuen Startzeitpunkt. Die Kostenrechnung kam aus den in `aws_box.sh` gepinnten Sätzen: 0,0978 Instanz plus 0,013041 Speicher plus 0,0050 Adresse gleich 0,1158 USD je Stunde.
- **Drei bekannte Fallen der Anfahrtsliste haben zugeschlagen, alle drei vorher aufgeschrieben.** Der Pin in `/etc/hosts` zeigte auf 172.18.0.9, während der Apache-Container auf 172.18.0.4 lag; nachgezogen und mit `getent` geprüft. Der Container war nach dem Maschinenstart nicht von AppAPI gestartet, also lief die DI-05-36-Heilung. Die harte Grenze von 2 GiB wurde aus der cgroup zurückgelesen und nicht aus der Zusage.
- **Die Abbruchbedingung ist eingetreten, und sie wurde nicht wegerklärt.** Gemessen wurden 52.137 indexiert, 44 übersprungen, 6 fehlgeschlagen statt 52.111 / 37 / 0. Die Anfahrt hielt an, der Ist-Stand ging nach `rohdaten/04-bestand-vor-der-messung.txt`, und der Owner entschied neu. Der Beleg lag der Rückfrage bei: die Differenz beträgt genau 39, gehört über die `acl`-Tabelle dem Konto `sprachfall`, und die sechs fehlgeschlagenen sind die sechs absichtlich kaputten Dateien des Referenzkorpus. Der Lastkorpus steht unverändert bei 49.980 indexiert und 20 übersprungen.
- **Messblock A ist gefahren und aufgerechnet.** Stufe 16 meldet 30 Fehlschläge, alle `EmptyResultGroup`, bei 4,88 Treffern je Anfrage über 160 Anfragen. Stufe 8 meldet 9 Fehlschläge bei 5,33 Treffern je Anfrage über 80 Anfragen. Das Protokoll trägt im Fenster der Stufe 16 vierzehn abgebrochene Vorgänge und im Fenster der Stufe 8 keinen einzigen.
- **Die Lücke zwischen 30 und 14 ist gemessen und nicht vermutet.** Der Begriff `Mahnung` trägt im Lastkorpus keinen einzigen Treffer, ohne Last in 486 Millisekunden gemessen; er fällt unter `--min-hits 1` und zählt als `EmptyResultGroup`, obwohl nichts abbricht. Die Rotation gibt ihm auf Stufe 16 genau 16 Auftritte, auf Stufe 8 acht, bei Nebenläufigkeit 1 einen. Damit gehen zwei der drei Stufen exakt auf: 16 plus 14 gleich 30, und 1 plus 0 gleich 1.
- **Eine Zeilenzählung wäre eine doppelte gewesen.** Ein abgebrochener Aufruf hinterlässt zwei Protokollzeilen, eine von `app_api` mit dem cURL-Text und eine von `findling`, die ihn weiterreicht. `71-protokoll.py` zählt deshalb nach `reqId` und weist beide Zeilenzahlen zur Kontrolle aus.
- **Messblock B ist gefahren, mit Rückgabewert 17.** `FRIST=60 RUNDEN=10 CI_LAUF=34530208024`, das Konto `sprachfall` existierte noch, die 39 Dateien wurden nicht neu aufgebaut. Bilanz: `sprachfaelle bestanden 6 von 10, davon 0 nicht messbar`, `ci-beleg: integration.yml Lauf 34530208024`.
- **Warum DI-10-02 offen bleibt, ist belegt.** Die Vorprüfung meldet für die vier Begriffe der roten Fälle je 26 Treffer, also unter der Schwelle 64. Die Gegenprobe in `rohdaten/07-fremdbestand-gegenprobe.txt` zeigt, dass dieselbe Route jedem geprüften Begriff exakt 26 Treffer liefert, bei Tiefe 64, 200 und 2000, und exakt 6 bei Tiefe 5. Die Zahl hängt weder am Begriff noch an der Tiefe: sie ist ein Deckel der Antwort. Eine Größe, die bei 26 stehen bleibt, kann die Schwelle 64 nicht überschreiten, also urteilt das Skript wieder zweiwertig und die vier Fälle sind rot wie am 10.09.
- **Die Box ist angehalten, unabhängig aus der API bestätigt.** `aws_box.sh status` meldet `stopped`, `address none`. Laufzeit 1,97 h, Kosten 0,2285 USD, beide aus `box.env` zurückgelesen und in `rohdaten/06-kosten.txt` dem Deckel gegenübergestellt.

## Die Erwartungen aus 00-ablauf.md, ohne Nachbesserung

| Nr | Erwartung | Ergebnis |
|---|---|---|
| E1 | Stufe 16 zeigt `failures > 0` | **eingetreten**, 30 |
| E2 | Stufe 16 unter Stufe 8 bei den Treffern je Anfrage | **eingetreten**, 4,88 gegen 5,33; der Abstand ist mit 0,45 kleiner als die 1,09 vom 10.09. |
| E3 | Stufe 8 zeigt `failures == 0` | **verfehlt**, 9. Acht gehen auf den Begriff ohne Treffer, einer bleibt offen |
| E4 | Beide Zählungen stimmen überein | **wörtlich verfehlt**, 30 gegen 14; nach Aufschlüsselung der zweiten Ursache deckungsgleich |
| E5 | Vier Fälle als nicht messbar | **verfehlt**, null Fälle |
| E6 | Möglicherweise ein fünfter | entfällt, Fall 7 ist grün |
| E7 | Die übrigen grün mit Fremdbestand 0 | **teils**, fünf grüne Fälle tragen 0, Fall 7 trägt 26 und ist trotzdem grün |
| E8 | Bilanz `6 von 10, davon 4 nicht messbar` | **verfehlt**, gemessen `6 von 10, davon 0 nicht messbar` |

Keine dieser Erwartungen wurde nach der Messung angepasst, und keine hat eine zweite Anfahrt ausgelöst.

## Deviations from Plan

### Owner-Entscheidungen

**1. Abbruchbedingung eingetreten, Fortsetzung freigegeben**
- **Gefunden in:** Task 2, Zustandsprüfung
- **Sachverhalt:** Der Bestand lautete 52.137 / 44 / 6 statt 52.111 / 37 / 0
- **Vorgehen:** Anfahrt angehalten, Beleg erhoben (Verdikte je Konto, die sechs kaputten Dateien mit Grund), Ist-Stand in die Rohdatei geschrieben und committet, Entscheidung dem Owner vorgelegt
- **Ergebnis:** Der Owner hat die Fortsetzung freigegeben, die Abweichung steht im Bericht
- **Commit:** 1f65d7f

### Auto-fixed Issues

**2. [Rule 2 - Fehlende Aussage] Die Zählung der Protokollabbrüche war doppelt**
- **Gefunden in:** Task 2, Schritt 5
- **Problem:** Die erste Fassung von `71-protokoll.py` zählte Zeilen und meldete 28 statt 14. Jeder abgebrochene Aufruf hinterlässt zwei Zeilen
- **Fix:** Zählung nach `reqId`, beide Zeilenzahlen zur Kontrolle daneben
- **Commit:** 66b803b

**3. [Rule 2 - Fehlende Aussage] Die Abweichung der Zählungen hätte ohne Grund dagestanden**
- **Gefunden in:** Task 2, nach Schritt 5
- **Problem:** Der Plan verlangt, dass eine Abweichung mit einer Vermutung über den Grund dasteht. 30 gegen 14 ohne Erklärung erfüllt das nicht
- **Fix:** Zwei Zusatzmessungen von zusammen rund zwei Minuten Box-Zeit: alle zehn Begriffe einzeln ohne Last, und ein Lauf bei Nebenläufigkeit 1. Beide in der Rohdatei beschriftet
- **Commit:** 66b803b

**4. [Rule 2 - Fehlende Aussage] Der Befund zu DI-10-02 wäre eine Behauptung geblieben**
- **Gefunden in:** Task 3
- **Problem:** Dass die Vorprüfung die Schwelle nicht erreichen kann, ist eine starke Aussage. Ohne Messung über mehrere Tiefen und mehrere Begriffe ist sie unbelegt
- **Fix:** `72-fremdbestand.py` und die siebte Rohdatei `07-fremdbestand-gegenprobe.txt`
- **Commit:** 8ae4e9b

**5. [Rule 3 - Blockierendes Problem] Die zwei neuen Skripte brachen das Messskript-Gate**
- **Gefunden in:** Task 4, Verifikation
- **Problem:** `test_the_script_of_this_run_starts_with_a_shebang` wurde für beide neuen Dateien rot
- **Fix:** `#!/usr/bin/env python3` als erste Zeile, danach 251 von 251 grün
- **Commit:** 34682a2

### Abweichungen von den Acceptance-Kriterien

**6. `grep -c "NICHT MESSBAR" 05-sprachfaelle.txt` ergibt 0 statt mindestens 1**
- Das ist kein Fehler der Ausführung, sondern das Messergebnis: der Fremdbestand bleibt unter der Schwelle, also schreibt das Skript dieses Urteil nicht. Der Ausdruck wurde ausdrücklich nicht durch erklärenden Text in die Datei gebracht, weil das Gate damit grün geworden wäre, ohne dass die Messung es hergibt.

**7. Ein Maschinenpfad steht in `05-sprachfaelle.txt`**
- Die Kopfzeile nennt `korpus: /home/ubuntu/work/wf/repo/testdata/corpus`. Die Rohdatei des 10.09. trägt an derselben Stelle denselben Pfad ihres Laufs. Die Datei bleibt unbearbeitet, weil eine nachträglich bearbeitete Messrohdatei jede Zahl daneben unbelegt macht.

**8. Eine siebte Rohdatei und zwei Skripte mehr als der Plan listet**
- `07-fremdbestand-gegenprobe.txt`, `71-protokoll.py` und `72-fremdbestand.py`. Ohne sie stünden die beiden zentralen Zahlen dieses Laufs ohne Beleg da.

## Was offen bleibt

- **DI-10-02 ist nicht geschlossen.** Die Vorprüfung braucht eine Messgröße, die nicht am selben Deckel hängt wie die Fälle: die Zahl der Dokumente im Index, die den Begriff tragen, statt der Zahl der Treffer, die die Route herausgibt. Das ist eine Änderung am Skript und keine Messung, und sie ist in dieser Anfahrt bewusst unterblieben.
- **Eine leere Antwort auf Stufe 8 ohne Protokollspur.** Passt zu DI-07-03, ist aber nicht nachgewiesen.
- **DI-10-04 bleibt ungeklärt** und braucht einen Volllauf über rund 26 Stunden.
- **Der Upgrade-Beweis lag nicht in dieser Anfahrt** und liegt in Plan 11-07, in CI.
- **Die Box ist angehalten, nicht abgebaut.** Der Abbau ist Plan 11-12 mit eigener Bestätigung (D-03).

## Verification

- Sieben Rohdateien unter `docs/measurements/2026-09-werkzeugfixe/rohdaten/`, jede mit sha256 auf Box und im Repository gleich
- `aws_box.sh status` meldet `stopped`, unabhängig aus der API gelesen
- Kosten 0,2285 USD unter dem Deckel 0,50 USD, Laufzeit 1,97 h unter 4,00 h
- Kein Diff unter `docs/measurements/2026-09-vergleichsmessung-m7g/`
- Passwort-Gegenprobe für `lasttest` und `admin` über das ganze Laufverzeichnis: sauber
- Vokabular-Gate über den Bericht: 0 Treffer, keine Gedankenstriche
- `pytest`: 2012 passed, 15 skipped (Grundlinie 2002 plus 10 neue Gate-Fälle für die zwei Skripte)
- `ruff check` und `ruff format --check` über `backend` und `scripts`: grün
- `pyright`: 0 errors, `vulture`: leer

## Self-Check: PASSED
