---
phase: 12-messwerkzeug-runbook-und-terminentscheid
plan: 07
subsystem: docs
tags: [runbook, ops, aws, ebs, snapshot, kosten, messung]

# Dependency graph
requires:
  - phase: 12-messwerkzeug-runbook-und-terminentscheid
    provides: "neunter Unterbefehl restore in aws_box.sh und die drei lesenden AWS-Proben aus Plan 12-03"
provides:
  - "docs/runbook-messbox.md, Abschnitte 1 bis 5: Geltungsbereich und Geheimnisregel, Deckel-Rechenblatt, Vorbedingungen ohne Box-Zeit, dreizehn nummerierte Aufbaubloecke, Zustandspruefung mit Abbruchbedingung"
  - "Deckel-Empfehlung fuer Phase 15 aus belegten Posten gerechnet: 42 h und 4,90 USD netto, Untergrenze 31 h und 3,59 USD"
  - "Platzhalter- und Geheimnisregel fuer ein Betriebsrunbook im oeffentlichen Repositorium"
affects: [12-08-runbook-abschnitte-6-bis-9, 15-messphase-eine-box-anfahrt]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Jeder Aufbaublock traegt eine Zeile Erwartete Ausgabe; was nicht trockengeprueft werden konnte, traegt die Marke in Phase 15 erstmals vollzogen statt einer Gewissheit"
    - "Platzhaltertabelle statt Werten: eine oeffentliche Betriebsanleitung nennt Pfade und Variablennamen, nie Adressen oder Kennungen"
    - "Das Kostenrechenblatt steht VOR der ersten Kommandozeile und fuehrt eine leere Ist-Spalte, die der Lauf selbst fuellt"

key-files:
  created:
    - docs/runbook-messbox.md
  modified: []

key-decisions:
  - "Abschnittsueberschriften bewusst ohne Umlaute, weil Pruefungen und Verweise auf sie zeigen; der Fliesstext traegt durchgehend echte Umlaute, und der Kopf der Datei sagt das"
  - "Deckel-Empfehlung 42 h / 4,90 USD aus acht Zeitposten plus 15 Prozent Zuschlag, statt die v1.1-Summe zu uebernehmen; der Volllauf steht mit 26 h 37 min im Plan und nicht mit einem erhofften kleineren Wert"
  - "Die CIDR-Schreibweise fuer das ganze Internet steht als Platzhalter <ganzes-netz> und nicht ausgeschrieben, weil die Geheimnisregel jede IPv4-Schreibweise in dieser Datei ausschliesst"

requirements-completed: []  # MESS-04 bleibt offen: die Abschnitte 6 bis 9 fehlen (Plan 12-08)
requirements-advanced: [MESS-04]  # MESS-06 steht im Plankopf, wird aber erst von Abschnitt 6 in 12-08 getragen

# Metrics
duration: 20min
completed: 2026-09-14
---

# Phase 12 Plan 07: Runbook der Messbox, Abschnitte 1 bis 5 Summary

**`docs/runbook-messbox.md` beginnt beim Handaufbau der abgebauten Maschine statt bei `aws_box.sh start`, rechnet den Deckel vor der ersten Kommandozeile aus acht belegten Posten neu (42 h / 4,90 USD) und beendet eine Anfahrt an sechs Ablesestellen, bevor sie nennenswert Geld kostet.**

## Performance

- **Duration:** rund 20 min
- **Started:** 2026-09-14T17:20Z
- **Completed:** 2026-09-14T17:40Z
- **Tasks:** 2 von 2
- **Files modified:** 1 (neu), 613 Zeilen

## Accomplishments

- **Abschnitt 1** macht den Umfangsschock zur Reihenfolge: die Box ist seit dem 11.09.2026 abgebaut und nicht geparkt, es gibt keine `box.env`, und die Tabelle sagt je Unterbefehl, was ohne sie passiert. Was im Snapshot liegt und was nicht, steht als zwei getrennte Listen; der Neuaufbau von null steht nur als Verweis auf drei Messberichte mit Pfad (D-09).
- **Abschnitt 2** ist das Deckel-Rechenblatt (D-05): acht Zeitposten mit den Spalten Planwert, Quelle und leerer Ist-Spalte, der Handaufbau ausdruecklich als Schaetzung (Annahme A8), die sechs gepinnten Kostensaetze, die Deckel-Geschichte in drei Zeilen, der Rechenweg als Formel und die Zeile, wohin die Schlusszahlen VOR dem Abbau geschrieben werden.
- **Abschnitt 3** listet neun Vorbedingungen, die null Box-Minuten kosten, jede mit Pruefung und mit dem Satz, warum sie vorher faellt.
- **Abschnitt 4** traegt dreizehn nummerierte Copy-paste-Bloecke (D-10) von der Security Group bis zur Zaehlung der Nextcloud-Instanzen, jeder mit einer Zeile `Erwartete Ausgabe`, dazu eine Platzhaltertabelle und die Tabelle der wiederkehrenden Handgriffe mit den Spalten `Offener Punkt`, `Handgriff` und `Warum`.
- **Abschnitt 5** uebernimmt die Abbruchzeile woertlich (52.111 indexiert, 37 uebersprungen, 0 fehlgeschlagen, 3.9Gi, 2 Kerne, aarch64), nennt die sechs Ablesestellen einzeln und macht die Resume-Falle zu einem Abbruchpfad statt zu einer Empfehlung.
- Die Geheimnisregel ist nicht nur behauptet, sondern durchgesetzt: die Datei enthaelt kein IPv4-Muster, keine lebende Instanz- oder Volumekennung und keine Kontokennung. Beide Tasks sind gegen die automatisierte Pruefung des Plans gruen gelaufen.

## Task Commits

1. **Task 1: Abschnitte 1 bis 3, Geltungsbereich, Deckel-Rechenblatt, Vorbedingungen** - `1f5bff1` (docs), 230 Zeilen
2. **Task 2: Abschnitte 4 und 5, Aufbau in nummerierten Bloecken und Zustandspruefung** - `8afc813` (docs), 383 Zeilen ergaenzt

**Plan metadata:** siehe Schlusscommit dieses Plans (docs)

## Files Created/Modified

- `docs/runbook-messbox.md` (neu, 613 Zeilen) - Abschnitte 1 bis 5 des Betriebsrunbooks; die Abschnitte 6 bis 9 (Vergleichbarkeitsbedingungen mit dem Cron-Intervall, Messreihenfolge, Abbau-Checkliste, Kostenfuehrung) folgen in Plan 12-08

## Decisions Made

- **Der Deckel-Vorschlag rechnet neu statt zu uebernehmen.** Die PITFALLS-Empfehlung von mindestens 31 h und rund 3,59 USD ist genau das, was der v1.1-Lauf VERBRAUCHT hat, bei kleinerem Arbeitsumfang. Das Rechenblatt weist die vier neuen Posten der Phase 15 aus (Erstvollzug des Wiederaufbaus, vier regressive Laststufen, Wiederaufwaerm-Messung in vier Auspraegungen, Sprachfall-Messung mit der neuen Messgroesse), den einen guenstiger werdenden (Korpus-Neuaufbau entfaellt) und kommt auf 36 h 07 min Planwerte plus 15 Prozent Zuschlag: **42 h und 4,90 USD netto**, mit 31 h / 3,59 USD als ausgewiesener Untergrenze.
- **Der Volllauf steht mit 26 h 37 min im Plan.** Ob der Top-up-Fix ihn verkuerzt, ist die zu beweisende Frage und keine Planungsgrundlage. Genau diese Vorwegnahme hat den v1.1-Deckel gerissen, und der Satz steht so in der Tabelle.
- **Der Erstvollzug ist als solcher markiert.** Elf der dreizehn Bloecke tragen die Marke `in Phase 15 erstmals vollzogen`. Nicht markiert sind Block 5 (die drei Rueckgabewerte `3.9Gi`, `2`, `aarch64` sind in drei frueheren Laeufen gemessen), Block 12 (`2147483648` ist gemessen und wird zurueckgelesen) und Block 13 (die Zaehlung ist trivial und ihr Schadensfall belegt). Block 6 trennt ausdruecklich: der lesende Teil ist am 14.09.2026 gefahren, der erzeugende nicht.
- **Die Snapshotkennung bleibt im Klartext, alles andere nicht.** Sie steht bereits in mehreren committeten Dateien und ist ohne Zugang zum Konto nutzlos; Adressen, Instanz- und Volumekennungen und die Kontokennung stehen als Platzhalter mit einem Satz, woher der Wert kommt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Projektregel schlaegt Planwortlaut] Das Wort "Archiv" kommt in der Datei nicht vor**

- **Found during:** Task 1 (Abschnitt 3) und Task 2 (Block 9)
- **Issue:** Der Plan nennt `home-ubuntu-work.tar.gz` an mehreren Stellen "das Passwortarchiv". `docs/` ist ein oeffentliches Artefakt, und das Vokabular-Gate des Projekts verbietet dort den Wortstamm.
- **Fix:** Durchgehend "die Sicherung der Systemplatte" beziehungsweise "die Passwortsicherung"; die Sache, der Pfad und die Warnung sind unveraendert. Das Abnahmekriterium ("Abschnitt 3 nennt ... das Passwortarchiv") ist inhaltlich erfuellt, Zeile 2 der Vorbedingungstabelle.
- **Files modified:** docs/runbook-messbox.md
- **Verification:** `grep -in "archiv" docs/runbook-messbox.md` liefert nichts
- **Committed in:** 1f5bff1, 8afc813

---

**2. [Rule 3 - Blocking] Abschnittsueberschriften ohne Umlaute, mit einem Satz im Kopf, der das erklaert**

- **Found during:** Task 1, vor der ersten Zeile
- **Issue:** Die Projektregel verlangt echte Umlaute in deutscher Prosa. Die automatisierte Pruefung beider Tasks greppt aber woertlich `## 1. Wofuer dieses Runbook gilt`, `## 4. Aufbau, in nummerierten Bloecken` und `## 5. Zustandspruefung mit Abbruchbedingung`. Beides zugleich ist nicht moeglich.
- **Fix:** Die Ueberschriften stehen exakt wie gefordert und wirken damit als Bezeichner, auf die Pruefungen und Verweise zeigen. Der gesamte Fliesstext, alle Tabellen und alle Erlaeuterungen tragen echte Umlaute. Ein eigener Absatz im Kopf der Datei sagt genau das, damit der naechste Leser die Mischung nicht fuer eine Nachlaessigkeit haelt.
- **Files modified:** docs/runbook-messbox.md
- **Verification:** beide `<automated>`-Bloecke des Plans melden GRUEN
- **Committed in:** 1f5bff1

---

**3. [Rule 2 - Missing Critical] Die CIDR-Schreibweise fuer das ganze Internet steht als Platzhalter**

- **Found during:** Task 2 (Block 1)
- **Issue:** Das Rezept aus `cmd_create` schreibt die offenen Regeln mit der ausgeschriebenen CIDR-Notation fuer das gesamte Internet. Diese Schreibweise ist ein IPv4-Muster und faellt damit durch die Geheimnispruefung des Plans (T-12-30), die genau dieses Muster verbietet. Dasselbe gilt fuer die beiden Bruecken-Adressen, mit denen die Vorlage den `/etc/hosts`-Fallstrick erklaert.
- **Fix:** Eine Platzhaltertabelle am Kopf des Abschnitts 4 mit fuenf Eintraegen (`<eigene-adresse>/32`, `<ganzes-netz>`, `<vpc>`/`<sg>`/`<subnetz>`, `<box>`, `<uuid>`) und je einem Satz, woher der Wert kommt. Der Fallstrick der wandernden Bruecken-Adresse ist ohne Zahlen erzaehlt und verliert dadurch nichts.
- **Files modified:** docs/runbook-messbox.md
- **Verification:** `grep -Eq '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b'` findet nichts in der Datei
- **Committed in:** 8afc813

---

**4. [Rule 2 - Missing Critical] Block 1 fuehrt vier Regeln statt der drei aus `cmd_create`**

- **Found during:** Task 2 (Block 1)
- **Issue:** Das Rezept im Skript kennt SSH, TCP 80 und TCP 443. UDP 443 fehlt dort, ist aber seit DI-05-35 Pflicht: der Apache des AIO-Abbilds kuendigt HTTP/3 ueber einen Alt-Svc-Kopf an, und ein Klient, der dem Kopf folgt, laeuft ohne UDP 443 in eine Zeitueberschreitung, bevor er auf TCP zurueckfaellt.
- **Fix:** Vierte Regel im Kommandoblock, dazu der Satz, dass sie neu gegenueber `cmd_create` ist, mit Begruendung. Die erwartete Ausgabe nennt vier `SecurityGroupRules`-Eintraege, davon einen mit `"IpProtocol": "udp"`.
- **Files modified:** docs/runbook-messbox.md
- **Verification:** Abnahmekriterium "Block 1 nennt UDP 443 mit dem Verweis auf DI-05-35" erfuellt
- **Committed in:** 8afc813

---

**Total deviations:** 4 auto-fixed (1 Projektregel, 1 blocking, 2 missing critical)
**Impact on plan:** Kein Scope-Zuwachs. Drei der vier Abweichungen setzen Regeln durch, die der Plan selbst in seinem Threat Model und seinen Abnahmekriterien fordert; die vierte loest einen Konflikt zwischen Projektregel und Planwortlaut auf, ohne eine Aussage zu veraendern.

## Issues Encountered

Keine. Beide Tasks liefen im ersten Anlauf gruen durch die automatisierte Pruefung.

Anmerkung zur Pruefbarkeit, und sie gehoert an diese Stelle: **dieses Runbook ist gelesen und nicht gefahren.** Elf der dreizehn Aufbaubloecke tragen die Marke `in Phase 15 erstmals vollzogen`. Die erwarteten Ausgaben stammen aus drei Quellen, jede mit Pfad in der Datei genannt: dem Rezept in `scripts/ops/aws_box.sh::cmd_create`, den Rohdaten des Abbaulaufs vom 11.09.2026 und den lesenden AWS-Proben vom 14.09.2026 aus Plan 12-03. Ein Block, dessen Ausgabe aus einem Skript abgeleitet ist, ist keine Gewissheit, und die Datei behauptet das an keiner Stelle.

## Known Stubs

Keine. Die leere Spalte "Ist (Phase 15)" der Zeitposten-Tabelle ist ausdruecklich so gewollt und im Text begruendet: sie wird waehrend der Anfahrt gefuellt, und der naechste Lauf rechnet gegen die gefuellte Spalte statt gegen die Planwerte.

## User Setup Required

Keine fuer diesen Plan. Fuer Phase 15 nennt Abschnitt 3 des Runbooks neun Vorbedingungen, von denen zwei Owner-Handlungen sind: der Zugang zur DNS-Verwaltung fuer den A-Record `loadtest.infranode.dev` (Zeile 8) und die Freigabe des neu gerechneten Deckels mit Datum (Zeile 9).

## Next Phase Readiness

- Plan 12-08 setzt bei Abschnitt 6 auf. Die Form steht: nummerierte Bloecke, je eine Zeile `Erwartete Ausgabe`, die Marke `in Phase 15 erstmals vollzogen` fuer Ungefahrenes, Platzhalter statt Werten. Die Platzhaltertabelle in Abschnitt 4 gilt fuer die ganze Datei und muss nicht wiederholt werden.
- MESS-04 bleibt offen, weil die Abschnitte 6 bis 9 fehlen. MESS-06 steht im Kopf dieses Plans, wird aber von Abschnitt 6 (Cron-Intervall als protokollpflichtige Vergleichbarkeitsgroesse) getragen und damit erst von 12-08.
- Fuer den Phase-15-Checkpoint liegt eine belegte Zahl vor: 42 h und 4,90 USD netto, Untergrenze 31 h und 3,59 USD. Die Freigabe faellt dort und nicht hier.

## Self-Check: PASSED

- `docs/runbook-messbox.md` existiert, 613 Zeilen.
- Beide Commit-Kennungen sind in `git log` auffindbar: `1f5bff1` und `8afc813`.
- Beide `<automated>`-Bloecke des Plans melden GRUEN.
- `grep -c '^### Block '` liefert 13, `grep -c 'Erwartete Ausgabe'` liefert 15 (dreizehn Bloecke, die Zustandspruefung, der erklaerende Satz im Kopf des Abschnitts 4).
- Vokabular-Gate: `grep -in "archiv"` liefert nichts. Keine IPv4-Schreibweise, kein U+2014, kein U+2013, keine Emojis.

---
*Phase: 12-messwerkzeug-runbook-und-terminentscheid*
*Completed: 2026-09-14*
