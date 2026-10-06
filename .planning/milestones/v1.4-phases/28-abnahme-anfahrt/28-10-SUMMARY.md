---
phase: 28-abnahme-anfahrt
plan: 10
subsystem: messung
tags: [abnahme-anfahrt, abbau, aws, tag-sweep, a-record, kosten, mess-10]
requires:
  - phase: 28-09
    provides: alle Zellen abgeholt und committet, beide Boxen geparkt, 90-kosten.txt bis 34,09 USD
provides:
  - "90-kosten.txt: Schlusszahlen-Tabelle je Instanztyp nach Runbook 2.6, committet vor dem Abbau (d4835808); Verbleib nach dem Abbau, Schlussstand 34,13 USD gegen Deckel 59,43 USD"
  - "08-abbau-boxen.txt: Sicherung beider box.env, beide destroy-Läufe, SG-Reihenfolge, InvalidKeyPair.NotFound, A-Record entfernt, Tag-Sweep 17 Regionen x 2 Tagwerte, Bestand 0/0/0/0, korpus-snapshot vorhanden ja"
  - "AWS-Konto ohne Instanz, Volume, Adresse, Schlüsselpaar, eigene AMI; einziger Kostenposten ist der Korpus-Snapshot"
affects: [28-11, 28-12, 28-13]
tech-stack:
  added: []
  patterns:
    - "Abbau-Rohdatei in zwei Commits: Abschnitte 0 bis 3 (Zustand, Sicherung, Schlusszahlen) vor dem ersten destroy, Abbau und Nachweis danach"
    - "Tag-Treffer nach dem Abbau nach Art zurücklesen: Instanz terminated, Volume InvalidVolume.NotFound"
key-files:
  created:
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/08-abbau-boxen.txt
  modified:
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/90-kosten.txt
decisions:
  - "Owner-Signal 05.10.2026 per Auswahlfrage: \"Ja, beide abbauen\" (Option abbau)"
  - "Rückgabe 1 des x86-destroy als Fehlalarm des Tag-Sweeps eingestuft (gemeinsames Schlüsselpaar fehlt in der shared-Liste), nach unabhängiger Rücklesung mit ARM weitergemacht"
  - "Sicherheitstimer D-28-14 (Deckel x 1,20) nie ausgelöst; die zwei vorgezogenen Kettentimer (Lauf 3, Lauf 6) und der box.env-Leerlaufvermerk 13,26 h sind keine Deckel-Auslöser"
metrics:
  duration: "2026-10-05T17:33Z bis 17:55Z (rund 22 min)"
  completed: 2026-10-05
requirements: [MESS-10]
---

# Phase 28 Plan 10: Abbau beider Boxen Summary

Beide Messboxen (ARM m7g.4xlarge, x86 c7a.8xlarge) samt Datenvolumes, gemeinsamer Security Group, Schlüsselpaar und A-Record nach Runbook Abschnitt 8 abgebaut und per Rücklesung belegt; Schlusszahlen 34,13 USD gegen Deckel 59,43 USD vorher committet; nur der Korpus-Snapshot bleibt bis 28-13.

## Owner-Signal Task 1

Wörtlich (05.10.2026, per Auswahlfrage über den Koordinator): **"Ja, beide abbauen"** (Option "abbau").

## Ablauf

- **Schlusszahlen vor dem Abbau (Runbook 2.6):** Tabelle je Typ in `90-kosten.txt`, Gegenprobe mit `02-rechenblatt.py stand` (34,09 USD, Rest 25,34). Je Typ: m7g.large 3,7010, m7g.4xlarge 8,4273, c7a.xlarge 2,1848, c7a.2xlarge 2,5859, c7a.4xlarge 6,2147, c7a.8xlarge 9,8727, geparkt 1,1041 USD. Sicherheitstimer nicht ausgelöst. Satzhinweis: 0,234260 USD/h aus der Statusabfrage ist der reine Instanzsatz; gerechnet wurde mit 0,252301 = Instanz + 100 GB gp3 + IPv4.
- **Sicherung (Schritt 5):** `~/.findling-loadtest/{x86,arm}/box.env.vor-abbau`, je mit cmp und sha256 im Protokoll. Commit d4835808 **vor** dem ersten destroy.
- **x86 zuerst (17:38:46Z bis 17:39:20Z):** Instanz und Datenvolume weg, `security group kept, still used by another instance`, Schlüsselpaar bleibt. Rückgabe 1, siehe Abweichung 1.
- **ARM danach (17:40:00Z bis 17:40:42Z):** Instanz, Volume, Security Group und Schlüsselpaar weg, Rückgabe 0, box.env entfernt.
- **Rücklesung:** beide Instanzen terminated, beide Datenvolumes `InvalidVolume.NotFound`, SG `InvalidGroup.NotFound`, Schlüsselpaar `InvalidKeyPair.NotFound`. Systemplatten fielen über DeleteOnTermination.
- **A-Record:** über den Zonen-Zugang des Betreiber-Werkzeugkastens gelöscht (wie beim Setzen), Rücklesung 0 Records, zwei öffentliche Resolver antworten NXDOMAIN. Lokal kein hosts-Eintrag.
- **Tag-Sweep 17 Regionen x 2 Tagwerte:** überall 0, außer eu-central-1 corpus-keep 1 (Snapshot) und 6 nachhängende phase5-Tags (2 Instanzen terminated, 4 Volumes NotFound).
- **Bestand 17 Regionen:** 0 Instanzen, 0 Volumes, 0 Adressen, 0 Schlüsselpaare, 0 AMIs, genau 1 Snapshot.
- **Acceptance:** `describe-instances` mit tag findling-phase5 und Zuständen pending/running/stopping/stopped liefert 0.
- **Schlussstand nach dem Abbau:** Parkstempel mit dem Ende des jeweiligen destroy geschlossen, 34,13 USD, Rest 25,30 USD, Satz 0 USD/h.

## Commits

| Task | Commit | Inhalt |
|------|--------|--------|
| 2a (vor destroy) | d4835808 | Schlusszahlen-Tabelle in 90-kosten.txt, 08-abbau-boxen.txt Abschnitte 0 bis 3 |
| 2b (nach destroy) | 754fa75c | Abbau-Protokoll mit Rücklesungen, Sweep, A-Record; Verbleib in 90-kosten.txt |

Task 1 war der Owner-Checkpoint, ohne eigenen Commit; das Signal steht hier und im Kopf von 08-abbau-boxen.txt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Rückgabe 1 beim ersten destroy (x86), Fehlalarm des Tag-Sweeps**
- **Gefunden bei:** Task 2, x86-destroy
- **Problem:** `aws_box.sh destroy` meldete das gemeinsame Schlüsselpaar als Überbleibsel und endete mit 1, obwohl es zwei Zeilen vorher absichtlich stehen gelassen wurde. Ursache: in `cmd_destroy` führt `shared="$others $other_volumes $group_id"` das Schlüsselpaar nicht.
- **Prüfung statt Vermutung:** unabhängige Rücklesung: x86-Instanz terminated, x86-Datenvolume weg, übrig nur das gemeinsame Paar und die zwei ARM-Volumes. Alle zerstörenden Teilschritte waren gelungen, also kein gescheiterter Abbauschritt. Der ARM-Abbau lief danach mit Rückgabe 0 und nahm das Paar mit.
- **Folge:** die x86-box.env blieb stehen. Sie war byte-gleich mit der Sicherung (cmp) und wurde nach dem zweiten Abbau von Hand entfernt (17:47:55Z).
- **Nicht gefixt:** `scripts/ops/aws_box.sh` gehört nicht zu den Dateien dieses Plans (parallele Executoren). Offen als Werkzeugfix, siehe Deferred Issues.

**2. [Rule 3 - Blocking] AWS-Zugang für aws_box.sh**
- Wie in 28-06: Sitzung des Profils infranodedev per `aws configure export-credentials` in die Umgebung, über einen temporären, nicht committeten Wrapper. Der Wrapper ersetzt in jeder Ausgabe die Kennungen durch Platzhalter. Alle Hilfsdateien sind danach gelöscht.

## Deferred Issues

- `aws_box.sh cmd_destroy`: das gemeinsame Schlüsselpaar in die `shared`-Liste des Tag-Sweeps aufnehmen. Dann endet der erste von zwei Abbauten mit 0 und lässt box.env nicht stehen. Das Runbook (Abschnitt 8, Schritt 6, Nachtrag 30.09.) erwartet beim ersten Abbau genau dieses Ergebnis.
- Korpus-Snapshot: Löschung nach den SC4-Entscheiden in 28-13 (Runbook 8 Schritt 6b, Checkpoint C6).

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche. T-28-52 (Sweep 17 Regionen, beide Tagwerte), T-28-53 (A-Record entfernt, NXDOMAIN belegt), T-28-54 (Schlusszahlen und Sicherung vor dem Abbau committet), T-28-55 (x86 zuerst, SG geschont) und T-28-56 (Platzhalter, Gate grün) sind umgesetzt.

## Self-Check: PASSED

- FOUND: docs/measurements/2026-10-abnahme-anfahrt/rohdaten/08-abbau-boxen.txt
- FOUND: docs/measurements/2026-10-abnahme-anfahrt/rohdaten/90-kosten.txt
- FOUND: d4835808, 754fa75c
- Gate `tests/test_public_artifacts.py`: 55 passed
