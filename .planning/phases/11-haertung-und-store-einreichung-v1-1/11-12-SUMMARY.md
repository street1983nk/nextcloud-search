---
phase: 11-haertung-und-store-einreichung-v1-1
plan: 12
subsystem: infra
tags: [aws, ebs, snapshot, teardown, d-03, rel-01, kosten, aws_box]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: die Abgabe von v1.1.0 in beide Store-Haelften, aus 11-11, denn der Abbau folgt der Abgabe
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: die Werkzeug-Anfahrt und die Kostenrechnung der Box, aus 11-06
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: den Korpus und den Index auf vol-04c5b59fe9417babd, die der Snapshot sichert
provides:
  - "snap-03f1d1d9ad9262704: der Korpus der 52.111 Dokumente und der Index, completed und unabhaengig nachgelesen"
  - "aws_box.sh snapshot als achter Unterbefehl, mit Zustandspruefung, Waiter, unabhaengiger Nachlese und Nachtrag in die Zustandsdatei"
  - "ein destroy, das die Historie nicht mitnehmen kann und einen Tag-Treffer nicht fuer ein Urteil haelt"
  - "die vollstaendige Kosten- und Schadenshistorie der Box im Repositorium, nachdem box.env geloescht ist"
  - "drei Nichtexistenz-Nachweise plus den vierten fuer die Systemplatte, und einen Kostenueberblick ueber 17 Regionen"
affects: [v1.2-Messplanung, jede spaetere Messung auf einer ARM-Box]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Die Verifikation ist die unabhaengige Nachlese und nicht der Waiter: ein Waiter, der zurueckkehrt, sagt nur, dass die API aufgehoert hat pending zu antworten"
    - "Ein Werkzeug, das eine Zustandsdatei loescht, verlangt den Pfad einer nicht leeren Sicherung, statt auf Erinnerung zu bauen"
    - "Ein Tag-Treffer ist ein Hinweis und kein Urteil: describe-tags laeuft nach, und jeder Treffer wird nach seiner Art zurueckgelesen"
    - "Ein Unterbefehl, dessen Waiter ablaufen kann, braucht einen Weg, den vorhandenen Gegenstand nachzutragen, sonst ist die einzige Abhilfe eine zweite Rechnung"
    - "Eine Schaetzung wird durch die Messung ersetzt und nicht bestaetigt: 25 bis 40 GB geschaetzt, 51,6 GiB gemessen"

key-files:
  created:
    - docs/measurements/2026-09-werkzeugfixe/rohdaten/07-snapshot-und-abbau.txt
  modified:
    - scripts/ops/aws_box.sh
    - backend/tests/test_ops_scripts.py
    - docs/performance.md
    - .planning/phases/11-haertung-und-store-einreichung-v1-1/deferred-items.md

key-decisions:
  - "Der Snapshot traegt purpose=findling-corpus-keep und ausdruecklich nicht purpose=findling-phase5, damit der Tag-Sweep von destroy ihn nicht fuer eine Leiche haelt (Pitfall 6)"
  - "cmd_destroy verlangt FINDLING_STATE_BACKUP als Pfad einer existierenden, nicht leeren Sicherung und bricht vor dem ersten zerstoerenden Aufruf ab; die Sicherung ist die committete Rohdatei im Repositorium (Pitfall 7)"
  - "Der Waiter der CLI lief nach zehn Minuten bei 8 Prozent ab. Statt eines zweiten Snapshots bekam der Unterbefehl einen Verifikationsweg: snapshot <id> legt nichts an und traegt nur nach"
  - "Der Tag-Sweep meldete beide Volumes als Ueberbleibsel, waehrend die API fuer beide InvalidVolume.NotFound antwortete. Nicht die Strenge wurde gesenkt, sondern die Messgroesse berichtigt: jeder Treffer wird zurueckgelesen, und was nicht lesbar ist, bleibt ein Ueberbleibsel"
  - "Die Systemplatte traegt Material ohne Gegenstueck im Repositorium. Es ist vor dem Abbau gesichert worden, aber ausserhalb des Arbeitsbaums, weil dieses Repositorium oeffentlich ist und Protokolle einer Testinstanz eine eigene Durchsicht auf Geheimnisse brauchen"
  - "Der Snapshot bleibt dauerhaft (Owner-Auflage 11.09.), Wiedervorlage nach der v1.2-Messung: loeschen oder Archivstufe"

patterns-established:
  - "Reihenfolge als Sicherheit: sichern, pruefen, bestaetigen lassen, zerstoeren, und jeder Schritt steht fertig in der Rohdatei, bevor der naechste beginnt"
  - "Die Historie geht vor dem Abbau auf origin, nicht erst danach"
  - "Nach einer zerstoerenden Handlung wird ein Kostenueberblick erhoben und nicht behauptet"

requirements-completed: [REL-01]

# Metrics
duration: 3h 10min
completed: 2026-09-11
---

# Phase 11 Plan 12: Snapshot und Abbau der ARM-Box Summary

**Der Korpus der 52.111 Dokumente liegt in `snap-03f1d1d9ad9262704` (completed, 51,6 GiB), die Box ist mit vier Nichtexistenz-Nachweisen abgebaut, und die laufenden Kosten fallen von 9,39 auf 2,79 bis 2,99 USD je Monat.**

## Performance

- **Duration:** rund 3 h 10 min, davon 52 min Snapshot und 5 min laufende Box
- **Started:** 2026-09-11T07:45Z
- **Completed:** 2026-09-11T09:45Z
- **Tasks:** 3 von 3
- **Files modified:** 5 (1 neu, 4 geaendert)

## Accomplishments

### Task 1: der achte Unterbefehl

`aws_box.sh snapshot` legt einen Snapshot des Datenvolumens an, **verweigert die
Arbeit, solange die Instanz nicht `stopped` ist** (ein Snapshot eines
beschriebenen, angehaengten Datentraegers ist nur absturzkonsistent), wartet mit
dem Waiter der CLI statt mit einer eigenen Schleife, **liest den Zustand danach
unabhaengig zurueck** und traegt Kennung und Nachlese in die Zustandsdatei nach.

Zwei Fallen aus der Phasenrecherche sind im Werkzeug geschlossen:

- Der Snapshot traegt `purpose=findling-corpus-keep`. Unter
  `purpose=findling-phase5` haette der Tag-Sweep von `cmd_destroy` ihn als
  Ueberbleibsel gemeldet und einen richtigen Abbau rot enden lassen. `destroy`
  fragt den Ueberlebenden zusaetzlich ausdruecklich ab und nennt ihn, statt sich
  darauf zu verlassen, dass der Filter ihn nicht sieht.
- `cmd_destroy` verlangt `FINDLING_STATE_BACKUP`, prueft Existenz und Inhalt und
  bricht **vor** dem ersten zerstoerenden Aufruf ab. Ohne das haette `destroy`
  die gesamte Kosten- und Schadenshistorie der Box mitgenommen.

`test_the_aws_tool_names_its_seven_subcommands_in_the_usage` heisst jetzt
`..._eight_...` und zaehlt acht, wie der Plan es vorgesehen hat.

### Task 2: der Snapshot, die Historie, die Systemplatte

| Punkt | Ergebnis |
|---|---|
| Snapshot | `snap-03f1d1d9ad9262704`, `State=completed`, `Progress=100 %`, `VolumeId` stimmt, 07:47:07Z bis 08:38Z |
| Groesse | 55.415.668.736 Byte, also **51,6 GiB**. Die Schaetzung 25 bis 40 GB ist ersetzt, nicht bestaetigt |
| Satz | **0,054 USD je GB-Monat**, aus der oeffentlichen Bulk-Preisliste (`EUC1-EBS:SnapshotUsage`), nicht geschaetzt |
| Kosten | **2,79 bis 2,99 USD je Monat** gegen 9,39 USD geparkt, Ersparnis 6,40 bis 6,60 USD je Monat |
| box.env | vollstaendig in der Rohdatei gesichert und **vor** dem Abbau auf origin geschoben |
| Systemplatte | Instanz lief dafuer 0,08 h und kostete 0,0098 USD |

**Der Befund der Systemplatte lautet nicht nein.** 174 Dateien haben keinen
gleichnamigen Gegenpart im Repositorium; 22,9 der 24,6 MB sind zwei
Transportkopien des Repositoriums selbst, es bleiben rund 1,7 MB, und das sind
die **gefahrenen Skripte und Protokolle der Phasen 5, 6 und 6.1**. Der Grund war
niemandem bewusst: `docs/measurements/2026-09-04-volllauf-m7g/` fuehrt kein
`skripte/`, erst der Semantiklauf hat eines. Die Docker-Wurzel und damit die
lokale Registry liegen dagegen auf dem Datentraeger und sind im Snapshot.

Das Material ist vor dem Abbau gesichert worden, ausserhalb des Arbeitsbaums
(435 Eintraege, 3.971.065 Byte, sha256 `fad3e7ce...`), ohne die Passwortdateien
der Testinstanz.

### Task 3: der Abbau

Der Owner hat am 11.09.2026 mit "Ja, abbauen" bestaetigt, mit zwei Auflagen: der
Snapshot bleibt dauerhaft, und ausser ihm entstehen keine Kosten.

| Ressource | Nachweis |
|---|---|
| Instanz `i-06b1d913f5c6f669b` | `state=terminated` |
| Volume `vol-04c5b59fe9417babd` (60 GB Korpus) | `InvalidVolume.NotFound` |
| Volume `vol-0f3bea6ca1dab68ab` (40 GB System) | `InvalidVolume.NotFound` |
| Security Group `sg-0e782f5233d73a847` | `InvalidGroup.NotFound` |
| Snapshot nach dem Abbau | existiert, `completed`, beide Tags unveraendert |
| `destroy` Exit-Code | 0, also hat der Sweep den Snapshot nicht als Leiche gemeldet |

**Der Kostenueberblick, ueber alle 17 freigeschalteten Regionen erhoben und nach
dem Abbau:** keine Instanz ausser der terminierten, kein Datentraeger, keine
Elastic IP, keine eigene AMI, keine weitere Netzwerkschnittstelle, **genau ein
Snapshot**. Das Schluesselpaar `findling-loadtest` und die Default-Gruppe der VPC
bestehen weiter und kosten nichts.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockade] Der Waiter der CLI ueberlebt den Snapshot nicht**

- **Found during:** Task 2
- **Issue:** `aws ec2 wait snapshot-completed` gibt nach zehn Minuten auf. Der
  Snapshot stand da bei 8 Prozent und brauchte insgesamt 52 Minuten. Der
  Unterbefehl konnte nur anlegen, also waere die einzige Abhilfe ein zweiter
  Snapshot und eine zweite Rechnung gewesen.
- **Fix:** `aws_box.sh snapshot <id>` legt nichts an und macht nur den Rest:
  Nachlese, Pruefung der Zugehoerigkeit zum Datenvolumen, Eintrag in die
  Zustandsdatei. Die Verweigerung bei `State != completed` bleibt.
- **Files modified:** `scripts/ops/aws_box.sh`, `backend/tests/test_ops_scripts.py`
- **Commit:** ee30cbd

**2. [Rule 1 - Fehlalarm im entscheidenden Pruefschritt] Der Tag-Sweep haelt nachlaufende Tags fuer Ueberbleibsel**

- **Found during:** Task 3, erster Durchgang des Abbaus
- **Issue:** `destroy` endete mit Exit 1 und meldete beide Volumes als
  Ueberbleibsel, waehrend die API fuer beide `InvalidVolume.NotFound`
  antwortete. `describe-tags` liest aus einem Index, der nachlaeuft. Ein Abbau,
  der in jedem Schritt richtig war, sah fehlgeschlagen aus, und die
  Zustandsdatei blieb liegen.
- **Fix:** Der Sweep liest jeden Treffer nach seiner Art zurueck und zaehlt nur,
  was auch antwortet. Was nicht gelesen werden kann, bleibt ein Ueberbleibsel;
  ein Treffer eines anderen Typs als Instanz, Volume oder Gruppe wird nicht
  zurueck in die Unschuld gelesen.
- **Files modified:** `scripts/ops/aws_box.sh`, `backend/tests/test_ops_scripts.py`
- **Commit:** c99ce24

**3. [Rule 2 - drohender unwiederbringlicher Verlust] Die Systemplatte trug Material ohne Gegenstueck**

- **Found during:** Task 2, Schritt 4
- **Issue:** Der Plan hielt "nein" fuer die wahrscheinliche Antwort. Die
  mechanische Pruefung ergab das Gegenteil: die gefahrenen Skripte der Phasen 5
  bis 6.1 existieren nur auf der Systemplatte, und `terminate` haette sie
  mitgenommen.
- **Fix:** Sicherung vor dem Abbau, ausserhalb des Arbeitsbaums, ohne die
  Passwortdateien. Die Aufnahme ins oeffentliche Repositorium braucht eine
  eigene Durchsicht auf Geheimnisse und steht in `deferred-items.md`.
- **Files modified:** keine im Repositorium; Sicherung unter
  `C:/Users/Student/.findling-loadtest/systemplatte-2026-09/`
- **Commit:** 5e9e9bf (Befund und Nachweis in der Rohdatei)

## Verification

- `backend`: 2026 passed, 15 skipped (Grundlinie 2020 plus 6 neue Zusicherungen)
- `ruff check`, `ruff format --check`, `pyright` (0 errors), `vulture` je gruen
- `bash -n scripts/ops/aws_box.sh` ohne Befund
- `grep -c "findling-corpus-keep" scripts/ops/aws_box.sh` = 4 (gefordert: >= 2)
- `grep -c "wait snapshot-completed" scripts/ops/aws_box.sh` = 1, keine eigene
  Warteschleife daneben
- `..._seven_subcommands...` = 0 Treffer, `..._eight_subcommands...` = 1
- Die Nutzung nennt acht Unterbefehle, darunter `snapshot`

## Known Stubs

Keine.

## Self-Check: PASSED
