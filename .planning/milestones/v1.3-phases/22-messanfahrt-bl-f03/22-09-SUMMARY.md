---
phase: 22-messanfahrt-bl-f03
plan: 09
subsystem: messanfahrt
tags: [box, b4, typwechsel, abbau, kosten, deckel, v13]
requires:
  - "22-08 (00-FERTIG mit b4 vorbereitet, Box gestoppt, Grub-Drop-in mem=4G entfernt)"
provides:
  - "B4-Kurve auf m7g.4xlarge: W3 N 1, 2, 4, 8, 12, 16 und embed.bench T 1, 2, 4, 8 als Rohdaten"
  - "Box abgebaut, Verbleib null über 17 Regionen, Schlüsselpaar und A-Record weg"
  - "Kosten 2,32 h / 0,4716 USD gegen Deckel 24 h / 3,76 USD gehalten"
  - "Lückenbericht README 6.9, Kaltstart mit Trefferpflicht braucht Nachfreigabe (D-02)"
affects:
  - "22-10 (MESS-09 aus 98d, unverändert)"
  - "22-11 (Bericht: B4-Auswertung, Lücken Kaltstart, 94c-Spitze, B5-RAM; Prüfsummen der gefahrenen Fassungen inklusive 00-typwechsel.sh und 00-wegwerf.sh b4)"
  - "nächste Anfahrt: Aufbau aus dem Korpus-Snapshot, Vorbedingung Schlüsselpaar erfüllt"
tech-stack:
  added: []
  patterns:
    - "Restminuten für B4 ab dem AWS-Start gerechnet (86 minus verstrichene Minuten), damit der Deckel nicht ab dem Skriptstart zählt"
    - "Kostenrohdatei vor dem destroy committet und gepusht, Verbleib danach angehängt"
key-files:
  created:
    - docs/measurements/2026-09-v13-messung/rohdaten/00-wegwerf-b4.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/B4-FERTIG
    - docs/measurements/2026-09-v13-messung/rohdaten/b4-slots-{1,2,4,8,12,16}.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/b4-bench-{1,2,4,8}.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/93-kosten-und-verbleib.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/07-abbau.txt
  modified:
    - docs/measurements/2026-09-v13-messung/rohdaten/00-typwechsel.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/00-lauf.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/00-timer.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/00-lauf-protokoll.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/99-ntfy-watch.log
    - docs/measurements/2026-09-v13-messung/README.md
decisions:
  - "B4 gefahren: B4_GEPLANT=ja (F4 3,955), kein harter Stopp, Restdeckel 21,98 h trägt den B4-Posten 1,44 h"
  - "DECKEL_REST_MINUTEN auf der Box auf 84 gesetzt (86 ab dem AWS-Start 13:20:56Z), Timer 14:45:42Z vor dem Deckelende 14:46:56Z; kein absolutes Nachziehen nötig"
  - "B4-Kosten aus den Stempeln (1.069 s, obere Schranke) mal 0,800141 USD/h, nicht aus BOX_LAST_UPTIME_COST_USD"
  - "Kein Ende-Snapshot (Owner-Freigabe 1.5); Korpus-Snapshot bleibt bis zur Wiedervorlage beim Milestone-Close"
metrics:
  duration: "ca. 35 min (13:20Z bis 13:55Z), Box-Laufzeit 17,8 min"
  completed: 2026-09-26
  tasks: 2
  files: 20
---

# Phase 22 Plan 09: B4 auf m7g.4xlarge, Abbau, Kosten und Lückenbericht Summary

B4 lief auf m7g.4xlarge ohne Rückfall, mit 16 Kernen, ohne Speichergrenze und ohne laufenden Container, und endete mit 0. Die Kurve ist fast linear: W3 von 0,263 auf 4,172 Seiten/s bei N = 16, embed.bench von 2.242 auf 13.485 Token/s bei T = 8. Danach ist die Box ohne Ende-Snapshot abgebaut, nichts ist übrig geblieben. Die ganze Anfahrt kostete 2,32 Boxstunden und 0,4716 USD, der Deckel liegt bei 24 h / 3,76 USD und ist gehalten.

## Aufgaben

| Task | Name | Commits | Ergebnis |
| ---- | ---- | ------- | -------- |
| 1 | B4 fahren oder Entfall begründen | 8ed671c | `typwechsel-hin` 13:20:59Z, `B4-FERTIG` 13:34:39Z mit 0, Selbstabschaltung nach der Abholung 13:37:43Z, `typwechsel-zurueck` mit `typ-ist m7g.large`, `b4-laufzeit-s 1069` |
| 2 | Abbau, Kosten, Lückenbericht, Commit | 38f2307 (Kosten vor dem Abbau, gepusht), 4bafbe3 | `destroy` mit 0 um 13:41:10Z, Tag-Sweep und `InvalidKeyPair.NotFound` zurückgelesen, A-Record entfernt, README 6.7 bis 6.9 |

## B4

| N | pages/s (Median) | T | tokens/s (p50) |
|---:|---:|---:|---:|
| 1 | 0,263 | 1 | 2.242,2 |
| 2 | 0,526 | 2 | 4.283,7 |
| 4 | 1,052 | 4 | 7.609,6 |
| 8 | 2,102 | 8 | 13.484,8 |
| 12 | 3,150 | | |
| 16 | 4,172 | | |

`b4-grenze keine`, `b4-kernel-mem ungesetzt`, nicht gekürzt. Die Auswertung folgt in 22-10/22-11.

## Kosten

- m7g.large 2,02 h mal 0,115841 = 0,2340 USD
- B4 0,2969 h mal 0,800141 = 0,2376 USD (von Hand, Pitfall 9: `aws_box.sh stop` hätte 0,0334 gemeldet)
- `gesamt 2,32 h 0,4716 USD`, `deckel stunden 24,00 h / 3,76 USD gehalten`
- Die Platten bei gestoppter Box kosteten 0,0831 USD (obere Schranke) und liegen außerhalb des Deckels. Mit ihnen sind es 0,5547 USD.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Restminuten ab dem AWS-Start statt 86 ab dem Skriptstart**
- **Found during:** Task 1
- **Issue:** Hätte `DECKEL_REST_MINUTEN=86` gegolten, hätte `00-lauf.sh b4` die 86 Minuten erst ab seinem eigenen Start gezählt. Die Minuten zwischen dem AWS-Start und dem Skriptstart wären dann über den B4-Posten hinaus gelaufen.
- **Fix:** In der Laufwertedatei der Box stand der Wert 84, gerechnet als 86 Minuten ab 13:20:56Z minus die verstrichenen Minuten. Der Timer stand damit auf 14:45:42Z und lag vor dem Deckelende 14:46:56Z. Belegt ist das in 00-typwechsel.txt (Handnotizen) und in 00-timer.txt.
- **Commit:** 8ed671c

**2. [Rule 2 - Missing] known_hosts für die neue Adresse**
- **Found during:** Task 1
- **Issue:** Nach dem Typwechsel hatte die Box eine neue Adresse, und 00-abholen.sh verweigert den Start ohne passenden Eintrag.
- **Fix:** Der Hostschlüssel ist per `ssh-keyscan` gegen die vorhandenen Einträge geprüft (derselbe Schlüssel). Erst danach kam der Eintrag für die neue Adresse ins Zustandsverzeichnis, außerhalb des Repos.

**3. [Rule 2 - Missing] Kostenrohdatei vor dem Abbau gepusht**
- **Found during:** Task 2
- **Fix:** Runbook 8 Schritt 2 verlangt die Historie vor dem Abbau auf `origin`. Deshalb ist 93 in zwei Teilen entstanden: Kosten in 38f2307 (gepusht), dann der Verbleib nach dem `destroy` in 4bafbe3.

**4. [Rule 1 - Bug] Scheinbare Uptimes in box.env nicht gezählt**
- **Found during:** Task 2
- **Issue:** `00-typwechsel.sh hin` rief `aws_box.sh stop` gegen die schon gestoppte Box. Dabei entstand eine Scheinuptime von 0,70 h (LaunchTime bis zum Aufruf). `zurueck` meldete B4 zum m7g.large-Satz.
- **Fix:** Beide Zeilen stehen in 93, Teil 2, mit dem Vermerk, dass sie nicht gezählt werden. Die Rechnung nimmt nur die sechs echten Uptimes und die B4-Stempel.

Die Bewaffnung (`app_api` disable/enable, `backendReachable true`) ist bewusst entfallen. B4 läuft ohne Produkt, und `00-lauf.sh b4` hält alle Container an (Pitfall 8). 00-ablauf.md verlangt vor B4 keine Bewaffnung.

## Deferred Issues

- **Lücke Kaltstartlatenz mit Trefferpflicht (MESS-07, Pflichtzahl):** Der Stand ist unverändert seit 22-08. README 6.9 hält fest: "Nachfreigabe durch den Owner noetig (D-02)". Die Nachmessung kostet rund 0,24 USD, alle drei Lücken zusammen rund 0,34 USD. Vorher muss in 22-10/22-11 die Ursache geklärt sein, sonst liefert eine Nachmessung wieder 0 Treffer.
- Nebenlücken sind die 94c-Spitze (32) und B5-RAM (50), beide keine Pflichtzahlen.
- `aws_box.sh stop` sollte eine schon gestoppte Box erkennen und dann keine Uptime schreiben. Das ist ein kleiner Werkzeugbefund, hier nicht gefixt.
- Prüfsummen der gefahrenen Fassungen (00-ablauf.md Abschnitt 5) folgen in 22-11. Dazu gehören jetzt auch `00-typwechsel.sh` und `00-wegwerf.sh` (b4).

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: rohdaten/b4-slots-1,2,4,8,12,16.txt, b4-bench-1,2,4,8.txt, B4-FERTIG, 00-wegwerf-b4.txt
- FOUND: 00-typwechsel.txt mit typwechsel-hin-laeuft, typwechsel-zurueck-gestoppt, typ-ist m7g.large
- FOUND: 93-kosten-und-verbleib.txt mit `gesamt`, `deckel ... gehalten` und der Verbleibzeile mit viermal 0
- FOUND: 07-abbau.txt mit Tag-Sweep und InvalidKeyPair.NotFound
- FOUND: README 6.8 "Kosten und Deckel", 6.9 "Luecken"
- FOUND: 8ed671c, 38f2307, 4bafbe3
- test_public_artifacts.py grün (mit den v13-Werkzeugtests 657 passed)
