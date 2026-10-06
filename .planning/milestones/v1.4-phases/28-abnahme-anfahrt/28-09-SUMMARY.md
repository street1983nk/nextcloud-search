---
phase: 28-abnahme-anfahrt
plan: 09
subsystem: messung
tags: [abnahme-anfahrt, x86, c7a.2xlarge, c7a.4xlarge, c7a.8xlarge, fp32, typwechsel, mess-10]
requires:
  - phase: 28-08
    provides: x86-Box c7a.xlarge nach bestandenem Machbarkeitstor, Teilkorpus mit gleicher Prüfsumme, Zellen 8, 9, 11
provides:
  - "07-typwechsel-x86.txt: drei Typwechsel mit Stempel und Rücklesung (nproc 8/16/32), Zellen 12 bis 21, Zusammenfassung der x86-Hälfte"
  - "Rohdaten c7a.2xlarge (12 S-T, 13 St-T, 14 L-T), c7a.4xlarge (15 S-T, 16 St-T, 17 L-T, 18 St-fp32-T), c7a.8xlarge (19 S-T, 20 St-T, 21 L-T)"
  - "Zweiter fp32-Datenpunkt: Mehrbedarf 223,2 MiB bei 4 Slots, Zelle 18 getragen"
  - "Befund für SC4/C5: Zellen 16, 17, 20, 21 nicht getragen, Mehrbedarf im Hauptprozess auf x86 ab 4 Slots"
  - "90-kosten.txt bis zum Stopp: bisher 34,09 USD gegen Deckel 59,43 USD, Rest 25,34 USD, beide Boxen geparkt"
affects: [28-10, 28-11]
tech-stack:
  added: []
  patterns:
    - "Nach A-Record-Wechsel rund 3 min bis zum Kettenstart warten (TTL 120, alte Adresse beim Stopp freigegeben)"
    - "Log-Mitschnitt folgt Container-Kennung UND Startzeit (docker logs -t), sonst geht der Container bei der Bewaffnung verloren"
key-files:
  created:
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/c7a.2xlarge/
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/c7a.4xlarge/
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/c7a.8xlarge/
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/c7a.8xlarge-abbruch60-dns/
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/c7a.2xlarge-kette.log
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/c7a.4xlarge-kette.log
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/c7a.8xlarge-kette.log
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/c7a.8xlarge-abbruch60-dns-kette.log
  modified:
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/07-typwechsel-x86.txt
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/90-kosten.txt
decisions:
  - "Kettenstart-Abbruch 60 auf c7a.8xlarge als Umgebungsfehler (stale DNS) eingestuft, genau eine Wiederholung, rc 0"
  - "Produktbefund Lock-Timeout nach Rückkehr fp32 auf int8 nicht angefasst, Kandidat /gsd-debug beim Owner"
  - "Abbau und SC4/C5 bleiben Owner-Entscheide in 28-10 und 28-11"
metrics:
  duration: "04.10.2026 15:04:45Z bis 05.10.2026 16:04:27Z (c7a.2xlarge 5,31 h, c7a.4xlarge 6,51 h, c7a.8xlarge 5,22 h Boxzeit; dazwischen AWS-Login-Pause über Nacht, Box geparkt)"
  completed: 2026-10-05
requirements: [MESS-10]
---

# Phase 28 Plan 09: Typwechsel-Rest der x86-Matrix Summary

**Rückwirkender Close-out vom 05.10.2026:** Der Plan wurde am 04. und 05.10. vollständig ausgeführt (Commits laufen unter dem Label `docs(28-07)`), das SUMMARY wurde danach aus 07-typwechsel-x86.txt, 90-kosten.txt, STATE.md und den Commits geschrieben; es wurde dafür nichts neu gemessen.

Per Typwechsel derselben Instanz sind c7a.2xlarge, c7a.4xlarge (mit fp32) und c7a.8xlarge gemessen: zehn Zellen, alle rc 0, Zähltor je 5000, alle Proben fits und von der Messung bestätigt. Damit ist die Matrix komplett: 18 Zellen einschließlich S-voll aus 28-06, die Zellen 3, 4 und 10 hat der Owner gestrichen. Vier Zellen dieses Plans (16, 17, 20, 21) liegen über der Grenze 1,10 x Rechnung, zusammen mit Zelle 11 aus 28-08 also fünf x86-Zellen für den Owner-Entscheid SC4/C5. Beide Boxen sind geparkt, Stand 34,09 von 59,43 USD.

## Task-Stand

### Task 1: c7a.2xlarge und c7a.4xlarge (mit fp32)

- **Typwechsel c7a.xlarge auf c7a.2xlarge:** gestoppt 15:04:23Z, läuft 15:04:45Z, Rücklesung nproc 8, 15Gi, x86_64, Hostschlüssel 3 von 3 gleich, A-Record neu, `vorpruefung-stop-ja` 15:07:56Z, SATZ 0.486561. Kette 15:07:57Z bis 20:22:28Z, drei Zellen rc 0.
- **Stopp c7a.2xlarge und BLOCKED-Episode (Auth-Gate, kein Messfehler):** Die AWS-Sitzung lief um rund 16:30Z ab, `aws_box.sh stop` war nicht möglich. Die Box wurde von innen gestoppt (systemd-run poweroff, 20:23:38Z, Shutdown-Verhalten stop belegt). Nach dem Owner-Login am 05.10. bestätigte `aws_box.sh status` um 04:19Z `stopped, Client.InstanceInitiatedShutdown`. Die Nachtstunden laufen als Parkposten.
- **Typwechsel auf c7a.4xlarge:** läuft 04:20:37Z (`aws_box stop` darin ein Leerlauf auf der gestoppten Box), Rücklesung nproc 16, 30Gi, x86_64, `vorpruefung-stop-ja` 04:23:22Z, `--restart` Vorrat 0/0, SATZ 0.955081. Kette 04:24:05Z bis 10:47:39Z, vier Zellen rc 0. fp32 zuletzt, Nullstand vor der fp32-Probe, danach Abwärtsweg auf int8.

| Zelle | Box | Profil | Slots | anon-max MiB | Grenze MiB | Urteil |
|-------|-----|--------|-------|--------------|------------|--------|
| 12 S-T | c7a.2xlarge | economy/int8 | 1 | 1.535,3 | 1.641,8 | getragen |
| 13 St-T | c7a.2xlarge | standard/int8 | 3 | 2.181,9 | 2.270,3 | getragen |
| 14 L-T | c7a.2xlarge | performance/int8 | 7 | 3.374,0 | 3.468,3 | getragen |
| 15 S-T | c7a.4xlarge | economy/int8 | 1 | 1.534,7 | 1.641,8 | getragen |
| 16 St-T | c7a.4xlarge | standard/int8 | 4 | 2.591,6 | 2.528,8 | **nicht getragen** |
| 17 L-T | c7a.4xlarge | performance/int8 | 15 | 5.623,7 | 5.536,3 | **nicht getragen** |
| 18 St-fp32-T | c7a.4xlarge | standard/fp32 | 4 | 2.844,6 | 2.932,5 | getragen |

- **fp32 (Zelle 18):** Download live, 85.983.232 bis 470.268.510 von 470.268.510 Bytes in rund 10 s, keine Digest-Warnung, Probe fits (4 Slots), erzwungen nein. Mehrbedarf Hauptprozess 223,2 MiB gegen FP32_EXTRA_BYTES 367 MiB, getragen. Rückkehr auf int8 belegt (`99-rueckkehr-int8.txt`, `code=saved` HTTP 200, `storedPrecision=int8 profileSaved=economy`, 10:47:41Z bis 10:47:44Z).
- **fp32-Datenpunkte für SC4/C5:** c7a.xlarge (1 Slot) 509,7 MiB, Zelle 11 nicht getragen; c7a.4xlarge (4 Slots) 223,2 MiB, Zelle 18 getragen. Der Mehrbedarf ist eine Differenz zweier Hauptprozess-Maxima und hängt am int8-Gegenstück (hier 1.755,6 MiB, selbst über der Rechnung).
- Commits 9c077be9, a66d87b9, fd204866, 2b2e5b9b (c7a.2xlarge, Stand BLOCKED); c6fb8ff1, 9693d400, 7ab2b9e3, c3e11e1f (c7a.4xlarge).

### Task 2: c7a.8xlarge und Schlusszahlen

- **ARM-Box gestoppt vor dem Wechsel:** belegt per `aws_box.sh status` im ARM-Verzeichnis in 28-08 Schritt 0 (m7g.4xlarge `stopped`, 04.10.), danach kein Start der ARM-Box. Indirekt bestätigt: c7a.8xlarge braucht die ganze Quota von 32 vCPU, eine laufende m7g.4xlarge (16 vCPU) hätte den Start verhindert. Eine eigene Statuszeile unmittelbar vor diesem Wechsel steht nicht im Protokoll (siehe Abweichungen).
- **Typwechsel auf c7a.8xlarge:** gestoppt 10:51:02Z, läuft 10:51:23Z, Rücklesung nproc 32, 61Gi, x86_64, Hostschlüssel 3 von 3 gleich, A-Record neu (TTL 120, rund 10:51:45Z), `vorpruefung-stop-ja` 10:52:28Z, SATZ 1.892121.
- **Kettenstart-Abbruch 60 (Umgebung, DNS):** erster Start 10:52:51Z, S-T brach im Abwärtsweg ab ("die Instanz antwortet nicht (URLError)"). Ursache: A-Record rund 1 min vor dem Kettenstart umgesetzt, die alte Adresse war mit dem Stopp freigegeben; ab 10:55:14Z löste die Box korrekt auf. Der Abbruch lag vor Nullstand und Registrierung. Rohdaten beiseite (`c7a.8xlarge-abbruch60-dns/`), `--restart`, genau eine Wiederholung 10:55:35Z, rc 0 (e71fc0b0).

| Zelle | Profil | Slots | anon-max MiB | Grenze MiB | Urteil |
|-------|--------|-------|--------------|------------|--------|
| 19 S-T | economy/int8 | 1 | 1.534,3 | 1.641,8 | getragen |
| 20 St-T | standard/int8 | 4 | 2.560,2 | 2.528,8 | **nicht getragen** |
| 21 L-T | performance/int8 | 16 | 5.802,8 | 5.794,8 | **nicht getragen** |

- **Stopp:** Kette-Ende 16:03:44Z, Rohdaten geholt, `aws_box.sh stop`, BOX_STOPPED_ISO 16:04:26Z, AWS `stopped, User initiated 16:04:27 GMT`. Laufzeit 5,2178 h x 1,892121 = 9,8727 USD.
- **Kostenstand:** `02-rechenblatt.py stand --jetzt 2026-10-05T16:04:27Z`: bisher 34,09 USD gegen Deckel 59,43 USD, Rest 25,34 USD, beide Boxen geparkt. Boxstunden je Typ stehen als Stempelzeilen in `90-kosten.txt` (c7a.2xlarge 5,3147 h = 2,5859 USD, c7a.4xlarge 6,5068 h = 6,2145 USD, c7a.8xlarge 5,2178 h = 9,8727 USD).
- Commits 8bbba681, cef4cc9f, 2b1de2cb, 6022063c.

## Gesamtbild der x86-Hälfte (Zellen 8 bis 21 ohne 10)

- Alle 13 Zellen rc 0, alle Zähltore 5000, alle Proben fits und bestätigt (kein Wächtereingriff, kein OOM).
- Getragen: 8, 9, 12, 13, 14, 15, 18, 19. Nicht getragen: 11, 16, 17, 20, 21, je rund 10 bis 13 Prozent über der Rechnung.
- **Muster:** Ab 4 Slots liegt auf x86 der Hauptprozess über der Rechnung (St-T 1.640 bis 1.756 MiB, L-T 2.411 bis 2.530 MiB), die Slotkosten selbst liegen unter B2 (212 bis 232 MiB bei mehreren Slots, rund 295 MiB bei 1 Slot). Dieselben Zellen auf ARM m7g.4xlarge waren getragen (St-T 2.358,2, L-T 5.481,8 MiB).
- Crawl-Fix in allen sieben Zellen von c7a.4xlarge und c7a.8xlarge bestätigt (sechs Runden "crawl is unfinished", keine stale-Lieferung, ruhige Runde stale=0, unchanged 0, Selbstvorschub je einmal).

## Abweichungen vom Plan

1. **Fünf x86-Zellen nicht getragen (11 aus 28-08, 16, 17, 20, 21 hier):** offen als Owner-Entscheid SC4/C5 in 28-11, zusammen mit dem vertagten fp32-Entscheid und beiden fp32-Datenpunkten. Hier bewusst nicht entschieden.
2. **BLOCKED-Episode AWS-Login (04.10. rund 16:30Z bis 05.10. 04:19Z):** Stopp von innen statt per `aws_box.sh`, Bestätigung nach dem Owner-Login nachgeholt, Kosten der Nacht als Parkposten.
3. **DNS-Abbruch 60 auf c7a.8xlarge:** eine Wiederholung, rc 0. Merker fürs Runbook: nach dem A-Record-Wechsel rund 3 min bis zum Kettenstart warten (auf c7a.4xlarge lagen 3,5 min dazwischen, ohne Problem).
4. **Schlusszahlen nur teilweise in der Form von Runbook 2.6:** `90-kosten.txt` hat Stempel und Kosten je Typ sowie bisher, Deckel und Rest. Eine eigene Tabelle "Summe je Typ, Gesamtsumme, Differenz, Sicherheitstimer ausgelöst ja/nein" fehlt. Die Zahlen lassen sich aus den Stempelzeilen ableiten. Nachtragen vor dem Abbau in 28-10 (Runbook 2.6 verlangt sie vor dem Abbau).
5. **Kein eigener ARM-Status direkt vor dem c7a.8xlarge-Wechsel:** gestoppter Zustand belegt am 04.10., kein Start danach, Quota-Argument wie oben.
6. **Containerlog S-T auf c7a.2xlarge nicht gesichert:** Der lesende Mitschnitt verlor den Container bei der Bewaffnung (gleiche Kennung, Neustart). Ab St-T folgt der Mitschnitt Kennung und Startzeit. Werkzeugrand, kein Produkt.
7. **findling-registry (arm64) im Neustart-Kreis auf x86** (exec format error), auf `--restart=no` gestellt; wird auf x86 nicht gebraucht.

## Offene Produktbefunde (nicht angefasst)

- **Lock-Timeout nach Rückkehr fp32 auf int8 (Zelle 18):** 21 s nach der Rückkehr (10:48:05Z) "the precision of the embedding changed, the vector stock is being written again", sofort danach "could not move 500 files to the embed track, they run into the lock timeout" (`container-rueckkehr-int8.txt`). Gleiches Muster wie Lauf 9 aus 28-07 (zweimal 30 Dateien), hier ein voller 500er-Stapel. Vermutete Nutzerrelevanz: Nach einem Präzisionswechsel wartet das Neuschreiben der Vektoren stapelweise bis zum Lock-Ablauf (1.800 s). Ob der Vektorbestand vollständig neu geschrieben wird, ist nicht beobachtet, weil die Box zum Typwechsel ging. Kandidat /gsd-debug beim Owner.

## Offen beim Owner (gehört zu 28-10 und 28-11, nicht zu diesem Plan)

- Abbau-Entscheid (beide Boxen geparkt, A-Record zeigt verwaist auf die letzte x86-Adresse).
- SC4/C5 für die fünf nicht getragenen x86-Zellen und der fp32-Entscheid.

## Known Stubs

Keine (reine Mess- und Protokollartefakte).

## Self-Check: PASSED

- rohdaten/c7a.2xlarge/ (S-T, St-T, L-T), c7a.4xlarge/ (S-T, St-T, L-T, St-fp32-T), c7a.8xlarge/ (S-T, St-T, L-T), 07-typwechsel-x86.txt mit Zusammenfassung: FOUND
- 90-kosten.txt mit Stopp 16:04:27Z und bisher 34,09 gegen Deckel 59,43: FOUND
- Commits 9c077be9, a66d87b9, fd204866, 2b2e5b9b, c6fb8ff1, 9693d400, 7ab2b9e3, c3e11e1f, e71fc0b0, 8bbba681, cef4cc9f, 2b1de2cb, 6022063c: FOUND
