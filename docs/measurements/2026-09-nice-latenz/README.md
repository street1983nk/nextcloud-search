# Live-Latenzprobe nice 10 (D-26-12 Teil 2), 29.09.2026

Einmalige Probe: Was bringt nice 10 für die Extraktionskinder (D-26-11) unter OCR-Last, getrennt für die Findling-Suche und für status.php?

## Aufbau

- Harness: `scripts/dev/compose-harp.yaml` (Nextcloud 34.0.3, HaRP, ExApp-Container vom Deploy-Daemon erzeugt), Docker Desktop auf WSL2, i5-1335U, 12 vCPU, 8 GB. Details in `raw/machine.txt`.
- A: Abbild vom Commit `c6868c21` (letzter Stand vor dem ersten Code-Commit der Phase 26), Digest `sha256:648f4763b4c6d3b35bc35379358453401dc26b4b615b4396f59b24066f73286d`, Kinder mit nice 0.
- B: Abbild vom Commit `46572f4d` (Phase 26 nach Welle 4, enthält `dbf8af19` nice 10), Digest `sha256:74ff1e9ba57988949541780b90ef1c9c62428349084af3a84399fdc8ae8f7428`, Kinder mit nice 10.
- Beide in Sparsam (nichts gesetzt), also ein OCR-Slot. Kein Testschalter im Produkt; der Unterschied kommt allein aus den zwei Abbildern.
- ExApp-Container in beiden Läufen per `docker update --cpus 1` auf einen Kern begrenzt (Messaufbau, kleine Box wie in Issue #19). Ohne die Grenze konkurriert ein einzelnes OCR-Kind auf 12 vCPU mit nichts.
- Last: 200 synthetische Scans (219 Seiten) plus 20 Text-PDFs aus `build_load_corpus.py`, Seed `d-26-12-latenz`, ein Testkonto. Gemessen erst, als tesseract lief; jede Rohdatei trägt eine Stichprobe davor und danach (tesseract in 4 bis 9 von 10 Sekunden gesehen, in A immer mit nice 0, in B immer mit nice 10). Der ExApp-Container lag während der Reihen bei rund 100 Prozent seines einen Kerns.
- Probe: `scripts/ops/latency_probe.py`, je Reihe 200 Anfragen im Abstand von 0,5 s, Zeitdeckel 5 s, vom Windows-Host gegen `http://localhost:8096`. Suche und status.php nacheinander, jeweils eigene Reihe.

## Ergebnis

| Reihe | Anfragen | p50 ms | p95 ms | max ms | Fehler |
|---|---|---|---|---|---|
| A Suche (nice 0) | 200 | 286,9 | 547,1 | 5000,0 | 1 (Zeitdeckel) |
| B Suche (nice 10) | 200 | 275,0 | 554,3 | 2349,5 | 0 |
| A status.php (nice 0) | 200 | 28,8 | 42,0 | 1645,9 | 0 |
| B status.php (nice 10) | 200 | 28,5 | 40,0 | 69,8 | 0 |

Rohdaten: `raw/A-search.txt`, `raw/B-search.txt`, `raw/A-status.txt`, `raw/B-status.txt`.

## Befund

- Findling-Suche: p50 und p95 liegen in A und B innerhalb weniger Prozent, ein Unterschied ist in dieser Probe nicht belegbar. Nur der Ausreißer fehlt in B: A hatte eine Anfrage am 5-s-Zeitdeckel, B keine und ein Maximum von 2,3 s. Eine Einzelanfrage je 200 ist kein Beleg, nur ein Hinweis.
- status.php: p50 und p95 praktisch gleich. Der A-Ausreißer von 1,6 s ist ein Einzelwert.
- Grenze: nice wirkt nur innerhalb derselben cgroup. Der Scheduler teilt die CPU zuerst zwischen den Containern und erst innerhalb eines Containers nach nice. status.php läuft im Nextcloud-Container und profitiert deshalb nicht von nice im Findling-Container; der Schutz der Nextcloud über Container bleibt die Slotzahl (Sparsam: ein Slot).
- Wahrscheinlicher Grund, warum auch die Suche kaum profitiert: Ein großer Teil der Suchzeit fällt in PHP auf der Nextcloud-Seite an (Rechteprüfung, zweiter Aufruf für Auszüge), und dieser Container war nicht ausgelastet. Im Findling-Container konkurriert die Suche außerdem mit der Einbettung, die im Hauptprozess mit nice 0 läuft (D-26-11 lässt den Hauptprozess bewusst unverändert).

## Grenzen der Probe

- Eine Maschine, ein Lauf je Variante, x86 unter WSL2 statt einer ARM-Box. Keine Leerlaufreihe ohne OCR als Vergleich.
- Die Last der Nextcloud-Seite (PHP-Prozesspool) war gering; auf einer Box, auf der Nextcloud und Findling sich ohne Containergrenze die CPU teilen, kann das Bild anders aussehen.
- In B kamen die Skelettdateien des Testkontos dazu (nach der ersten Anmeldung angelegt); die OCR-Last war in beiden Reihen durchgehend vorhanden.

Zahlbeleg für die Issue-#19-Antwort; die Antwort wird erst nach Owner-Freigabe gepostet.
