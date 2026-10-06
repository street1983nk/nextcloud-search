---
phase: 28-abnahme-anfahrt
plan: 06
subsystem: messung
tags: [abnahme-anfahrt, referenzbox, m7g.large, sparsam, store-zahl, mess-10]
requires:
  - phase: 28-05
    provides: Owner-Freigabe Deckel 59,43 USD, Sätze, Vorbedingungen
provides:
  - "Aufbauprotokoll 03-aufbau-arm.txt: Blöcke 1 bis 13b, Baumhash gleich c87a0239, Cron-Gate, vorpruefung-stop-ja"
  - "Rohdaten S-voll (m7g.large, economy/int8, Grenze 2g, 52.137 Dateien) mit Auswertung"
  - "Rohdaten 94c mit Bewertung: C1 743,9 MB, sparsam-store-toleranz innerhalb"
  - "Kostenstempel 90-kosten.txt: bisher 2,47 USD gegen Deckel 59,43 USD, Box geparkt"
affects: [28-07, 28-08, 28-11]
tech-stack:
  added: []
  patterns: ["AWS-Zugangsdaten per aws configure export-credentials aus dem Profil in die Umgebung, nie auf die Box"]
key-files:
  created:
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/03-aufbau-arm.txt
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/m7g.large/00-shutdown-beleg.txt
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/m7g.large/S-voll/10-auswertung.txt
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/m7g.large/94c/94c-bewertung.txt
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/m7g.large/94c/94c-bodensatz-zyklen.txt
  modified:
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/90-kosten.txt
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/11-probe-route.py
decisions:
  - "Owner-Signal Task 3 (01.10.2026): weiter mit 28-07"
  - "C1 743,9 MB liegt innerhalb 715,6 bis 744,8 MB; der Store-Text bleibt (D-28-10), die Randlage ist vermerkt"
metrics:
  duration: "S-voll 19,58 h unbeaufsichtigt, 94c-Ablauf 7 min, Box-Laufzeit gesamt 21,25 h"
  completed: 2026-10-01
requirements: [MESS-10]
---

# Phase 28 Plan 06: Referenzbox m7g.large, Vollzelle Sparsam und Store-Messgröße C1 Summary

Referenzbox m7g.large auf dem Abbild zu c87a0239 aufgebaut (Baumhash belegt, Cron-Gate gefahren), Sparsam über den vollen Korpus (52.137 Dateien) in 19,58 h ohne OOM-Neustartspur gemessen, C1 = 743,9 MB innerhalb des Bands um 730,2 MB, Box geparkt bei 2,47 USD.

## Ergebnisse

- **C1 (94c, zwei Zyklen, Ruhezeit 120 s):** A 110,7 MB, **C1 743,9 MB**, C2 759,5 MB, zyklus2-minus-c1 15,6 MB. Gegen 730,2 MB +13,7 MB (+1,88 Prozent): `sparsam-store-toleranz innerhalb`.
  **Ausdrücklich vermerkt:** C1 liegt nur 0,9 MB unter der Obergrenze 744,8 MB. Frühere Messungen derselben Box lagen bei 729,3 bis 731,9 MB (731,9 v1.2, 730,2 und 729,3 v1.3). Der Abstand von rund 12 bis 15 MB zu diesen Werten ist nicht erklärt.
- **S-voll:** Volltextspur 18,72 h (indexed 52137 um 2026-10-01T12:59:28Z, rund 2.785 Dateien je Stunde), beide Spuren 19,58 h (embedded gleich indexed zweimal um 13:50:46Z). anon-Spitze der cgroup 1.875,8 MB (1.788,9 MiB) gegen 2.048 MiB; memory.peak berührte die Grenze (Seitencache eingeschlossen). Grundlast nach 120 s Ruhe: anon 1.624.530.944 Byte. Guard durchgehend economy, throttled false, slotsInForce 1.
- **OOM:** keine Neustartspur (memory.peak nie zurückgesetzt, anon ohne Einbruch, Statusreihe stetig, backendReachable durchgehend true, Hauptprozess pid 8 durchgehend). Eine OOM-Schlusszeile fehlt, siehe Lücken.
- **Kosten:** Lauf 1 21,0219 h = 2,4352 USD, geparkt 0,9014 h = 0,0118 USD, Lauf 2 (94c) 0,2275 h = 0,0264 USD. `02-rechenblatt.py stand`: bisher 2,47 USD, Deckel 59,43 USD, Rest 56,96 USD. Box gestoppt (AWS: stopped, 2026-10-01T15:02:45Z).

## Shutdown nach S-voll: reguläres Kettenende

Die Box fuhr um 13:54:59Z selbst herunter. Belegt (`rohdaten/m7g.large/00-shutdown-beleg.txt`):

- `00-kette.txt`: `zelle-ende S-voll rueckgabe 0 2026-10-01T13:52:48Z`, `kette-ende 2026-10-01T13:52:48Z bisher 2.4310`
- `10-zelle.txt`: `ende vorrat 0 embedded gleich indexed zweimal 2026-10-01T13:50:46Z`, `10-ZELLE-FERTIG S-voll`; kein `00-DECKEL-ERREICHT`, keine `kette-abbruch`-Zeile
- Journal `-b -1`: 13:52:48 sudo `shutdown -h +2`, logind `power off at 13:54:48`, 13:54:59 `poweroff.target`; `last -x`: `shutdown system down ... 13:54`
- Auslöser: `00-kette.sh` Zeile 297 (Regel 3, Kettenende). Sicherheitstimer stand auf 2026-10-26T08:31:31Z.

**Befund:** Der Laufwert `STOPP_AM_ENDE=nein` aus den Plan-Interfaces wird von `00-kette.sh` nicht gelesen; das Kettenende stoppt die Box unbedingt. Unschädlich, weil Zelle, Nachlauf und Abholbereitschaft vor dem Stopp fertig waren und ein Stopp kein Abbau ist. Für die Matrix-Zellen heißt das: nach jeder Kette ist ein Neustart mit Bewaffnung (Block 10 bis 12) nötig.

## Lücken in den Rohdaten

1. `S-voll/anon.csv` (Prozessreihe) endet 2026-10-01T06:07:48Z mit `reason=container gone`, obwohl der Container weiterlief (rss.csv derselben cgroup bis zum Ende). Deckung 11,9 von 19,6 h. Ursache und Fix sind Vorbereitung für 28-07 (eigener Commit nach diesem SUMMARY).
2. OOM-Schlusszeile fehlt: `10-zelle.sh` schreibt weder OOMKilled noch RestartCount; nach dem Stopp nicht mehr lesbar. Ergänzung ebenfalls Vorbereitung für 28-07.
3. OCR-Seiten je Sekunde sind aus diesen Rohdaten nicht direkt ablesbar und nicht berechnet.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] AWS-Zugangsdaten für aws_box.sh**
- aws_box.sh verlangt AWS_ACCESS_KEY_ID in der Umgebung; die Sitzung des Profils infranodedev per `aws configure export-credentials` exportiert (Region eu-central-1). Keine Umgehung des Logins.

**2. [Rule 3 - Blocking] known_hosts nach Adresswechsel**
- Neue Adresse nach dem Start; ed25519-Hostschlüssel gegen den gespeicherten verglichen (gleich), dann eingetragen.

**3. [Rule 3 - Blocking] Cloudflare-A-Record loadtest umgesetzt**
- Record zeigte noch auf die Adresse vor dem Stopp; per Zonen-API auf die neue Instanzadresse gesetzt (2026-10-01T14:53:46Z, TTL 120, nicht proxied), Runbook Block 10. Nach dem Stopp zeigt er wieder ins Leere; beim nächsten Start neu setzen, nach dem Abbau entfernen (28-09).

**4. [Rule 3 - Blocking] Bewaffnung vor 94c**
- Nach dem Maschinenstart Block 11/12: disable/enable, Grenze 2147483648/0, backendReachable true. Entladefrist per 92e auf 120 und danach zurück auf 0 (beide Rückgabe 0).

**5. [Rule 1] Gate-Fund in eigener Belegdatei**
- Die Journalzeile mit `USER=`/`PWD=` schlug im Gate an (schluesselwort-mit-wert); in Prosa umformuliert.

Frühere Abweichungen von Task 1 (Probe-Route liest Guard-Felder aus dem backend-Block, 774dd247; Kettenlauf 1 endete mit 69 am Tor) stehen in 03-aufbau-arm.txt.

## Owner-Signal Task 3

Wörtlich (über den Koordinator, 01.10.2026): "weiter" mit 28-07.

## Commits

- 8a473c45 docs(28-06): reference box m7g.large built, image c87a0239 proven, cron gate
- 774dd247 fix(28-06): probe route reads the guard fields out of the backend block
- 56862f5d docs(28-06): chain run 1 ended at the gate, fix on the box, run 2 triggered
- aad6763d docs(28-06): S-voll and 94c on m7g.large, C1 743.9 MB inside the band

## Self-Check: PASSED

- 94c-bewertung.txt, 00-shutdown-beleg.txt, 10-auswertung.txt, 90-kosten.txt vorhanden; Commits 8a473c45, 774dd247, 56862f5d, aad6763d im Log; Gate test_public_artifacts.py 55 passed.

## Nachtrag: Vorbereitung 28-07 (Lücke anon.csv, OOM-Schlusszeile)

- **Ursache, belegt bis zur Skriptstelle:** `scripts/ops/proc_anon_sampler.sh:92` (`docker exec ... || return 1`) zusammen mit `:131-132` (`if ! rows=$(sample); then finish 'container gone'`): ein einziger fehlgeschlagener `docker exec` beendete die Reihe mit `container gone`, ohne den Container erneut zu fragen. Der Container lief weiter (rss.csv derselben cgroup bis 13:52Z, memory.peak nie zurückgesetzt).
- **Art des Fehlschlags, Indizien:** `anon.log` enthält nach der Kopfzeile keine Meldung, also kein Fehler des Docker-Daemons (der schriebe "Error response from daemon" bzw. "OCI runtime exec failed"); die innere Shell endet wegen `|| true` nur bei Tod durch Signal ungleich 0. Um 06:07:40 bis 06:07:47Z fiel der Dateicache der cgroup von 223 auf 82 MB bei memory.current rund 2,03 GB von 2,147 GB: Speicherdruck an der Grenze. Das Kernel-Journal des S-voll-Boots (oom-kill-Zeile) ist nicht gelesen, weil die AWS-Sitzung bei der Kurzstart-Absicht abgelaufen war; Box blieb gestoppt.
- **Fix:** Sampler schreibt jeden Fehlschlag mit Rückgabewert nach stderr, fragt den Container erneut und endet nur bei `container gone`, `container replaced` oder `container unreadable` (FINDLING_ANON_MAX_FAILURES in Folge, Vorgabe 30); Abschlusszeile zählt `failed=`. Commits a06dff96 (RED), 30a9c757 (GREEN), 79e927ff (Stil).
- **OOM-Schlusszeile:** `10-zelle.sh` schreibt vor dem Sampler-Stopp `oom oomkilled .. restartcount .. containerstart .. memory-events oom .. oom_kill ..`. Commit 7adfed5b, Positivkontrolle schlägt gegen das alte Skript fehl.
- **Vor 28-07:** die Box trägt noch den alten Stand der Skripte; die lokalen Commits müssen vor der nächsten Zelle auf den Box-Klon (nicht gepusht).

## Nachtrag 01.10.2026, 18:05Z: Kernel-Journal des S-voll-Boots (Frage OOM um 06:07Z)

- **Kein OOM.** `journalctl --list-boots`: S-voll ist Boot -2 (16:54:56Z bis 13:54:59Z, Kernel 7.0.0-1012-aws). `journalctl -k -b <Boot -2>` mit `grep -iE 'oom|killed process|out of memory'`: 0 Treffer im Fenster 06:00 bis 06:15Z (143 Kernzeilen gelesen), 0 Treffer im ganzen Boot.
- **Tatsächliche Ursache der anon.csv-Lücke: unattended-upgrades.** 06:06:59 `Starting apt-daily-upgrade.service`, 06:07:40 Upgrade libc6 2.39-0ubuntu8.8 auf 8.9, 06:07:41 `systemd[1]: Reexecuting.`, 06:07:49.556 `Stopped containerd.service`, 06:07:50.460 dockerd `Error running exec ... dial unix:///run/containerd/containerd.sock: timeout`, 06:07:50.661 `Started containerd.service`. Die Shims liefen weiter, die Container also auch; genau dieser eine fehlgeschlagene `docker exec` beendete den Sampler. Die frühere Vermutung "Speicherdruck an der Grenze" ist damit widerlegt.
- **Nebenbefund:** derselbe Lauf installierte 06:07:55 bis 06:08:31 linux-image-7.0.0-1013-aws. 94c und alle Zellen ab 28-07 laufen auf 7.0.0-1013-aws, S-voll lief auf 7.0.0-1012-aws. Vermerkt, nicht bewertet.
- Belegzeilen: `rohdaten/m7g.large/S-voll/10-auswertung.txt`, Abschnitt "nachtrag 2026-10-01T18:05Z".
