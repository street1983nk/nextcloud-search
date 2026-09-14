---
phase: 12-messwerkzeug-runbook-und-terminentscheid
plan: 03
subsystem: infra
tags: [aws, ec2, ebs, snapshot, shell, pytest, ops]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: "achter Unterbefehl snapshot in aws_box.sh und der Korpus-Snapshot snap-03f1d1d9ad9262704"
provides:
  - "neunter Unterbefehl restore in scripts/ops/aws_box.sh: Volume aus dem Korpus-Snapshot erzeugen, umtaggen, anhaengen"
  - "lesend bestaetigte Annahme A3: der Snapshot existiert, ist completed und traegt purpose=findling-corpus-keep"
  - "Usage-Gate und zwei Reihenfolge-Zusicherungen fuer restore in backend/tests/test_ops_scripts.py"
  - "Rohdatei mit den erwarteten Ausgaben der drei lesenden AWS-Proben fuer das Runbook"
affects: [12-runbook-messbox, 15-messphase-eine-box-anfahrt]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lesende Bestaetigung vor jeder kostenpflichtigen Erzeugung (describe vor create)"
    - "Umtaggen mit Rueckleseprobe als Pflichtschritt im Unterbefehl statt als Runbook-Zeile"

key-files:
  created:
    - docs/measurements/2026-09-v12-messung/rohdaten/01-aws-lesende-proben.txt
  modified:
    - scripts/ops/aws_box.sh
    - backend/tests/test_ops_scripts.py

key-decisions:
  - "restore endet beim Anhaengen; das Mounten bleibt ein nummerierter Runbook-Block und kein AWS-Aufruf"
  - "Die Snapshotkennung ist Argument, sonst CORPUS_SNAPSHOT_ID aus box.env, sonst die gepinnte Konstante CORPUS_SNAPSHOT_DEFAULT; nie gesucht"
  - "Skript und Gate-Test gingen in EINEN Commit, weil ein Commit dazwischen das Usage-Gate rot faerbt (Pitfall 8)"

patterns-established:
  - "Rueckleseprobe nach create-tags: ein angenommener API-Aufruf sagt nicht, was die Ressource danach traegt"
  - "Fail-closed gegen geerbte Tags: der Unterbefehl bricht ab, solange KEEP_TAG_VALUE noch am Volume haengt"

requirements-completed: []  # MESS-04 bleibt offen: es traegt auch 12-04 bis 12-08
requirements-advanced: [MESS-04]

# Metrics
duration: 25min
completed: 2026-09-14
---

# Phase 12 Plan 03: Unterbefehl restore und lesende AWS-Proben Summary

**`aws_box.sh restore` baut das 60-GB-Volume aus `snap-03f1d1d9ad9262704`, taggt es gegen die geerbte Keep-Markierung um, liest die Tags zurueck und haengt es an; Annahme A3 ist lesend bestaetigt statt vermutet.**

## Performance

- **Duration:** rund 25 min
- **Started:** 2026-09-14T16:17Z
- **Completed:** 2026-09-14T16:42Z
- **Tasks:** 3 von 3
- **Files modified:** 3 (1 neu, 2 geaendert)

## Accomplishments

- Drei kostenlose lesende AWS-Proben gefahren: der Korpus-Snapshot existiert, steht auf `completed` bei 100 Prozent, kommt von einem 60-GB-Volume mit 55.415.668.736 Byte geschriebener Bloecke und traegt `purpose=findling-corpus-keep`. Der D-09-Hauptpfad des Runbooks ruht damit auf einer Tatsache.
- `cmd_restore` in `scripts/ops/aws_box.sh`: lesende Bestaetigung vor jeder Erzeugung, Aufnahme eines vorhandenen nicht angehaengten Volumes statt zweiter Erzeugung, `create-volume --snapshot-id` in der Zone der Box, Pflicht-Umtaggen mit `describe-tags`-Rueckleseprobe, Waiter der CLI, Zustandsdatei angehaengt mit `umask 077`.
- Die vier mitwandernden Stellen nachgezogen: Kopfkommentar (neun Eintraege), `# Usage:`-Kopfzeile, `usage()` und der `case`-Block samt Meldung.
- Gate-Test auf neun Unterbefehle umbenannt und zwei Reihenfolge-Zusicherungen ergaenzt, die die zwei bekannten Fallen des Snapshot-Wegs festschreiben statt sie zu beschreiben.

## Task Commits

1. **Task 1: Die drei kostenlosen lesenden AWS-Proben fahren und festhalten** - `b8aadc7` (docs)
2. **Task 2 und Task 3 gemeinsam: Unterbefehl restore plus Usage-Gate und restore-Zusicherungen** - `3ce1374` (feat)

**Plan metadata:** siehe Schlusscommit dieses Plans (docs)

## Files Created/Modified

- `docs/measurements/2026-09-v12-messung/rohdaten/01-aws-lesende-proben.txt` (neu) - die drei lesenden Proben mit Kommandozeile, Antwort und Schlusszeile je Abschnitt; Kontokennung als `<konto>`, Befundblock am Ende
- `scripts/ops/aws_box.sh` - neuer Unterbefehl `restore`, neue Konstante `CORPUS_SNAPSHOT_DEFAULT`, Usage und Kopf auf neun Unterbefehle
- `backend/tests/test_ops_scripts.py` - `test_the_aws_tool_names_its_nine_subcommands_in_the_usage` plus `test_the_aws_restore_reads_the_snapshot_before_it_creates_anything` und `test_the_aws_restore_retags_the_volume_and_reads_the_tags_back`

## Decisions Made

- **Drei Quellen fuer die Snapshotkennung, in dieser Reihenfolge:** Argument, `CORPUS_SNAPSHOT_ID` aus `box.env`, gepinnte Konstante. Gesucht wird nie: ein `restore`, das sich den neuesten Snapshot mit dem Keep-Tag holt, baut irgendwann stillschweigend ein Volume aus einer fremden Aufnahme.
- **`--size` ausgeschrieben statt aus dem Snapshot geerbt,** zusammen mit dem Abbruch bei `VolumeSize > VOLUME_SIZE_GB`. Eine geprueft Zahl ist mehr wert als eine geerbte, und die API wuerde eine zu kleine Bestellung erst nach der Anfrage abweisen.
- **Das Umtaggen laeuft auf beiden Pfaden,** auch fuer ein aufgenommenes Volume, und die Rueckleseprobe und nicht der Rueckgabewert von `create-tags` entscheidet.
- **`restore` endet beim Anhaengen.** Das Mounten bleibt ein Handgriff auf der Box und ein nummerierter Runbook-Block.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Task 2 und Task 3 in EINEN Commit gelegt statt in zwei**
- **Found during:** Task 2 (Unterbefehl restore)
- **Issue:** Der Plan schneidet Skript und Gate-Test in zwei Tasks, verlangt aber im Objective und im must_have "das Repository ist in sich stimmig", dass beide in derselben Aenderung wandern. Ein Commit nur mit `aws_box.sh` haette `test_the_aws_tool_names_its_eight_subcommands_in_the_usage` rot hinterlassen, und `python.yml` laeuft auf `scripts/**` an, also waere dieser Commit auf main rot in CI gelandet (Pitfall 8, PATTERNS Reihenfolge-Hinweis 2).
- **Fix:** Beide Dateien zusammen als `3ce1374` committet; die Aufgaben selbst wurden vollstaendig und in der geplanten Reihenfolge ausgefuehrt.
- **Files modified:** scripts/ops/aws_box.sh, backend/tests/test_ops_scripts.py
- **Verification:** `pytest tests/test_ops_scripts.py` gruen (65 bestanden), `ruff check .` und `ruff format --check .` gruen ueber Backend und `../scripts`
- **Committed in:** 3ce1374

**2. [Rule 2 - Missing Critical] Die `# Usage:`-Kopfzeile dreizeilig umgebaut**
- **Found during:** Task 2 (Unterbefehl restore)
- **Issue:** Das Abnahmekriterium verlangt die Zeichenkette `usage: aws_box.sh <prices|create|volume|restore|status|stop|start|snapshot|destroy>` woertlich auch in der Kopfzeile. Die alte Kopfzeile schob die beiden Anmeldenamen zwischen `Usage:` und `aws_box.sh`, die geforderte Zeichenkette konnte dort gar nicht stehen.
- **Fix:** Kopfzeile auf `aws_box.sh <subcommand>` gekuerzt, darunter zwei Zeilen Begruendung und die Usage-Zeile woertlich wie in `usage()`. Die Anmeldenamen bleiben im Kopf erhalten, ohne dass eine zweite expandierende Stelle entsteht.
- **Files modified:** scripts/ops/aws_box.sh
- **Verification:** `test_the_aws_tool_demands_both_credentials_and_never_prints_them` bleibt gruen (genau eine expandierende Zeile je Name), die Zeichenkette steht zweimal in der Datei
- **Committed in:** 3ce1374

---

**3. [Rule 1 - Bug] MESS-04 wieder auf offen gesetzt**
- **Found during:** State-Updates nach Task 3
- **Issue:** `requirements mark-complete MESS-04` hakte das Requirement in `REQUIREMENTS.md` ab. MESS-04 traegt aber auch die Plaene 12-04 bis 12-08 (Diagnose-Route-Vorpruefung, Runbook-Erstfassung, Cron-Vorpruefung). Ein abgehaktes Requirement, dessen groesserer Teil noch fehlt, ist genau die Zahl, an der eine Phase fuer fertig gehalten wird.
- **Fix:** `.planning/REQUIREMENTS.md` zurueckgesetzt; im Summary-Frontmatter steht `requirements-completed: []` und daneben `requirements-advanced: [MESS-04]`.
- **Files modified:** keine (Ruecknahme einer Aenderung)
- **Verification:** `git diff .planning/REQUIREMENTS.md` ist leer, MESS-04 steht weiter auf Pending
- **Committed in:** nicht committet, die Aenderung wurde vor dem Commit zurueckgenommen

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 missing critical, 1 bug)
**Impact on plan:** Kein Scope-Zuwachs. Die erste Abweichung betrifft nur den Commit-Schnitt, die zweite ist die woertliche Erfuellung eines Abnahmekriteriums des Plans, die dritte nimmt eine falsche Buchung im Requirements-Stand zurueck.

## Issues Encountered

Keine. Alle drei Proben liefen im ersten Anlauf, der Befund war positiv, die Flag-Datei `SNAPSHOT-BEFUND-NEGATIV.txt` wurde nicht angelegt und der Plan lief vollstaendig durch.

Anmerkung zur Pruefbarkeit: `restore` ist nur auf den Verweigerungspfaden wirklich ausgefuehrt worden (belegtes `VOLUME_ID` in der Zustandsdatei, Aufruf ohne Unterbefehl). Der Erzeugungspfad ist absichtlich nicht gefahren worden, weil er kostenpflichtige Ressourcen anlegt; sein Erstvollzug ist Phase 15. Abgesichert ist er ueber `sh -n`, die Reihenfolge-Zusicherungen und die woertliche Uebernahme der Bloecke aus `cmd_volume`.

## User Setup Required

Keine. Die AWS-Anmeldung lag vor und ist gueltig (Annahme A4 damit nebenbei bestaetigt).

## Next Phase Readiness

- Der Wiederaufbau-Hauptpfad des Runbooks (D-09) hat jetzt ein Werkzeug und eine belegte Tatsachengrundlage. Plan 12-04 kann die Kommandobloecke und die erwarteten Ausgaben aus `01-aws-lesende-proben.txt` woertlich uebernehmen.
- Fuer das Deckel-Rechenblatt steht die Zahlenbasis: 0.0978 USD je Stunde fuer die Box, 0.0952 USD je GB und Monat fuer gp3, 0.0050 USD je Stunde fuer die oeffentliche Adresse, zusammen 0.1158 USD netto je Stunde bei 100 GB Platte.
- Offen bleibt, was der Plan bewusst offen laesst: der Erzeugungspfad von `restore` wird in Phase 15 erstvollzogen, und der Snapshot-Entscheid (loeschen oder guenstiger lagern, rund 2,9 USD je Monat) faellt nach v1.2.

## Self-Check: PASSED

Alle drei genannten Dateien existieren auf der Platte, beide Commit-Kennungen sind in `git log` auffindbar, und die Flag-Datei `SNAPSHOT-BEFUND-NEGATIV.txt` existiert wie gefordert nicht.

---
*Phase: 12-messwerkzeug-runbook-und-terminentscheid*
*Completed: 2026-09-14*
