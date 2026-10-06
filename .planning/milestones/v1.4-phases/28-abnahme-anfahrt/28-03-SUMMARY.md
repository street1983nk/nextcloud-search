---
phase: 28-abnahme-anfahrt
plan: 03
subsystem: messung
tags: [abnahme-anfahrt, aws, satztabelle, typwechsel, x86, mess-10]
requires:
  - "28-02: 00-kette.sh liest VORPRUEFUNG=stop-ja"
provides:
  - "aws_box.sh: Satztabelle der sechs Typen, Typ aus describe-instances, Architektur je Familie, FINDLING_BOX_TYPE, SG- und Schlüsselschonung beim ersten Abbau"
  - "00-typwechsel.sh (v14): vorpruefung, wechsel <zieltyp>, preis <typ>..., quota [typ...]"
  - "backend/tests/test_v14_typwechsel.py: 44 boxlose Tests"
affects: [28-05]
tech-stack:
  added: []
  patterns:
    - "aws_box.sh als Programm gegen eine nachgestellte aws-Kommandozeile getestet, python3-Stub reicht an den Interpreter des Testlaufs durch"
    - "Preiskarte per stdin an Python, nicht als MSYS-Pfad"
key-files:
  created:
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/00-typwechsel.sh
    - backend/tests/test_v14_typwechsel.py
  modified:
    - scripts/ops/aws_box.sh
    - backend/tests/test_ops_scripts.py
decisions:
  - "stop parkt auch einen Typ ohne Satz, schreibt dann aber keine Kostenzahl und endet mit 1; Parken hängt nie an der Rechnung"
  - "destroy schont bei geteilter Security Group auch das Schlüsselpaar und nimmt die andere Instanz samt ihrer Volumes aus dem Tag-Sweep; der zweite Abbau nimmt beides"
  - "wechsel ohne Kapazität setzt den Typ auf den alten zurück, Box bleibt gestoppt, Rückgabe 55; kein Rückfall innerhalb der Matrix"
  - "Rückgabewerte 54 (Architekturwechsel verweigert) und 55 (Kapazität) neu gegenüber der v13-Fassung"
  - "preis braucht keine Zugangsdaten (öffentliche Karte); PYTHON überschreibbar, weil python3 auf der Entwicklungsmaschine ein Store-Platzhalter sein kann"
metrics:
  duration: "rund 55 min"
  completed: "2026-09-30"
  tasks: 2
  files: 4
---

# Phase 28 Plan 03: Werkzeuge der Entwicklungsmaschine für die x86-Matrix Summary

aws_box.sh rechnet stop und status mit dem Satz des Typs, den describe-instances meldet (Tabelle der sechs Typen aus der öffentlichen Preiskarte, unbekannter Typ endet rot ohne Zahl), kennt die Architektur je Familie und lässt beim ersten Abbau Security Group und Schlüsselpaar der zweiten Box stehen; das neue 00-typwechsel.sh wechselt nur innerhalb einer Familie und liest Satz, Quota und Zonenangebot kostenlos.

## Was gebaut wurde

- **aws_box.sh**
  - `INSTANCE_RATES` mit m7g.large 0.0978, m7g.4xlarge 0.7821, c7a.xlarge 0.23426, c7a.2xlarge 0.46852, c7a.4xlarge 0.93704, c7a.8xlarge 1.87408; Quelle (Preiskarte, Manifest 2026-09-25T17:45:21Z, gelesen 29.09.) im Kommentar. `PRICE_INSTANCE_HOURLY` ist weg.
  - status und stop lesen den Typ aus derselben describe-instances-Antwort (`reported_type`), schlagen nach (`instance_rate`) und nennen Typ und Satz in der Ausgabe; stop schreibt zusätzlich `BOX_LAST_UPTIME_TYPE` und `BOX_LAST_UPTIME_RATE_USD_H` in box.env.
  - prices druckt alle sechs Sätze und nennt die Preiskarte; Speicherzeile sagt nur bei m7g.large "capped to 4096 MiB".
  - create: `FINDLING_BOX_TYPE` (Standard m7g.large), Architektur aus der Familie (m7g arm64, c7a x86_64, sonst 2), Schritt 0 mit der kostenlosen `describe-images`-Lesung (arm64- bzw. amd64-Muster), `--instance-initiated-shutdown-behavior stop` im Rezept, für x86 kein erfundenes AMI (Platzhalter bzw. `FINDLING_BOX_IMAGE`), mem=4G nur bei m7g.large.
  - destroy fragt vor dem Löschen der Gruppe, welche nicht beendete Instanz sie noch trägt; gibt es eine: "security group kept, still used by another instance", Schlüsselpaar bleibt ebenfalls, andere Instanz und ihre Volumes zählen im Sweep nicht als Überbleibsel, box.env dieser Box wird entfernt.
- **00-typwechsel.sh** (v14, Laufverzeichnis): `vorpruefung` (52, Zeile `vorpruefung-stop-ja <UTC>`), `wechsel <zieltyp>` (nur die sechs Typen, sonst 2; Architekturwechsel 54 mit nur describe-Aufrufen; vorpruefung, aws_box.sh stop, modify, aws_box.sh start, Typ und Zustand zurückgelesen, 53 bei Abweichung; Zeile `typwechsel <alt> -> <neu> gestoppt <UTC> laeuft <UTC>` plus Epoche; Kapazität 55 ohne Rückfall), `preis <typ>...` (curl auf die Preiskarte, gzip erkannt an der Signatur, ein Satz je Typ, sonst 1), `quota [typ...]` (L-1216C47A und `describe-instance-type-offerings` in eu-central-1). Kennung und Adresse nur als Platzhalter in der Rohdatei, aws_box.sh-Ausgabe aufs Terminal. Index 100755.

## Commits

| Task | Commit | Art |
|---|---|---|
| 1 RED | 3d8ddab1 | test: Satztabelle, Architektur, geteilte Gruppe |
| 1 GREEN | 01558d15 | feat: aws_box.sh |
| 2 RED | 7dad3585 | test: Typwechsel mit Zieltyp |
| 2 GREEN | b1191dc5 | feat: 00-typwechsel.sh |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Kritisch] Tag-Sweep hätte den ersten Abbau rot beendet**
- **Found during:** Task 1
- **Issue:** Nur die Gruppe zu schonen reicht nicht: die zweite Instanz, ihre Volumes und die Gruppe tragen dasselbe Tag `purpose=findling-phase5`, der Sweep hätte sie als Überbleibsel gemeldet, box.env bliebe liegen.
- **Fix:** Die andere Instanz, ihre Volumes und die Gruppe laufen als `shared` am Sweep vorbei und werden benannt.
- **Commit:** 01558d15

**2. [Rule 2 - Kritisch] Schlüsselpaar beim ersten Abbau**
- **Found during:** Task 1
- **Issue:** destroy löscht seit L-07 immer das Schlüsselpaar; die Research nennt Gruppe und Schlüssel als gemeinsam genutzt.
- **Fix:** Bei geteilter Gruppe bleibt auch das Schlüsselpaar stehen; der zweite Abbau löscht und liest es zurück wie bisher.
- **Commit:** 01558d15

**3. [Rule 1 - Bug] Preiskarte als MSYS-Pfad**
- **Found during:** Task 2
- **Issue:** Python für Windows liest den `/tmp/...`-Pfad aus mktemp nicht; auf der Entwicklungsmaschine wäre `preis` immer gescheitert.
- **Fix:** Karte per stdin.
- **Commit:** b1191dc5

### Auslegung

- **unknown-type bei stop:** Die Box wird trotzdem gestoppt (Parken darf nie an einer Rechnung hängen), box.env bekommt Stoppzeit, Stunden und Typ, aber keine Kostenzeile; Rückgabe 1.
- **Kapazität:** "Box bleibt gestoppt" plus Rücksetzen auf den alten Typ, damit ein späterer Start nicht an derselben Knappheit scheitert; das ist kein Rückfall auf einen anderen Matrixtyp.
- **quota** ohne Typ liest alle sechs.

### Nicht erledigt, bewusst

- Zone bleibt in aws_box.sh fest `eu-central-1c`. Liefert `quota` für c7a kein Angebot in 1c (Annahme A7), braucht 28-05 eine kleine Werkzeugänderung oder V-X von Hand; nicht im Plan.
- Keine echten AWS-Aufrufe, keine Preiskarte live gelesen (Owner-Vorgabe).

## Known Stubs

Keine. 00-typwechsel.sh trägt "DIESE FASSUNG IST NICHT GEFAHREN"; sein Lauf ist Teil von 28-05.

## Threat Flags

Keine neue Fläche außerhalb des Registers: Zugangsdaten (T-28-12), Satztabelle (T-28-13), Architekturverweigerung (T-28-14), Gruppenschonung (T-28-15), vorpruefung (T-28-16), Platzhalter in der Rohdatei (T-28-17) sind umgesetzt und getestet. Der curl-Abruf der Preiskarte geht an einen öffentlichen Endpunkt ohne Zugangsdaten.

## Self-Check: PASSED

- Dateien vorhanden: scripts/ops/aws_box.sh, backend/tests/test_ops_scripts.py, docs/measurements/2026-10-abnahme-anfahrt/skripte/00-typwechsel.sh, backend/tests/test_v14_typwechsel.py
- Commits vorhanden: 3d8ddab1, 01558d15, 7dad3585, b1191dc5
- `grep -c c7a.8xlarge aws_box.sh` >= 1, `grep -c 1.87408` >= 1, `PRICE_INSTANCE_HOURLY` nicht mehr vorhanden; 00-typwechsel.sh im Index 100755, "NIE AUF DER BOX" genau 1
- Gates: pytest test_ops_scripts, test_v14_typwechsel, test_v13_wegwerf, test_public_artifacts, test_measurement_scripts, test_v14_zelle 805 passed; ruff check (inkl. ../scripts) und format grün; pyright (latest) 0 Fehler; vulture grün; `sh -n` beide Skripte
