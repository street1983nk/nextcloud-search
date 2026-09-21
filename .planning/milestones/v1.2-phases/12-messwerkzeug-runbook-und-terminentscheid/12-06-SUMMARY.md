---
phase: 12-messwerkzeug-runbook-und-terminentscheid
plan: 06
subsystem: measurement-tooling
tags: [cron, messbedingung, fail-closed, wirkungszweig, ablaufplan, posix-sh, mess-06]

# Dependency graph
requires:
  - phase: 12-messwerkzeug-runbook-und-terminentscheid
    provides: "73-bestand-sonde.py und das v1.2-Laufverzeichnis (Plan 12-04), 98c-sprachfaelle.sh mit dem Exit-Code-Katalog 15 bis 24 (Plan 12-05)"
  - phase: 10-vergleichsmessung-v1-1
    provides: "93-nullstand.sh (Urteil in eine Datei, Abbruch unter der tee-Pipeline) und 96b-waechter.sh (Beobachtungsschleife mit Deckel und gezaehlten Lesungen)"
provides:
  - "97-cron-vorpruefung.sh: zweiteiliger Cron-Check, Konfigurationszweig vor dem Lauf und Wirkungszweig waehrend des Laufs, beide fail-closed"
  - "Pflichtzeile cron-intervall-ist plus Abbruch 25/26: ein Lauf ohne protokolliertes Intervall gilt als unvollstaendig (D-07)"
  - "Gemessener Scheibenabstand (min, median, max) mit Deckel 420 s und Abbruch 27/28 (D-08)"
  - "00-ablauf.md: Ablaufplan des v1.2-Laufs mit vorher aufgeschriebener Erwartung E1 bis E7 und allen zwoelf Rueckgabewerten"
affects: [12-08, 15-messphase-eine-box-anfahrt]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zweiteiliger Check: Konfiguration vor dem Lauf, Wirkung waehrend des Laufs; die Konfiguration allein haette den Befund vom 10.09. verfehlt"
    - "Quellenkette mit Erklaerzeile je Wette, die teuerste Quelle zuletzt, und die Quelle selbst als Protokollzeile"
    - "Protokollblock: Pflichtzeilen werden gedruckt UND in eine Arbeitsdatei mitgeschrieben, damit ein Bericht sie als Block zitieren kann"
    - "Eine Lesung zaehlt erst, wenn ihr Statusblock da ist; eine leere Ausgabe ist kein leerer Arbeitsvorrat"

key-files:
  created:
    - docs/measurements/2026-09-v12-messung/skripte/97-cron-vorpruefung.sh
    - docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md
  modified: []

key-decisions:
  - "Der Wirkungszweig ist nicht optional: der v1.1-Befund war NOMINAL 5 min und EFFEKTIV 12 min, ein reiner Konfigurationscheck haette gruen gemeldet"
  - "Die dritte Intervallquelle (Abstand zweier lastcron-Lesungen) steht zuletzt, weil sie eine Messung ist und SOLL_INTERVALL Sekunden kostet"
  - "Ticken die beiden lastcron-Lesungen nicht auseinander, nennt die Quelle keine Zahl: der Takt ist dann groesser als das Soll, aber welcher, sagt sie nicht"
  - "Die Ruecklesung des Solls fragt nur die beiden Konfigurationsquellen erneut, nicht die Messquelle"
  - "Der Schritt, der das Soll setzt, ist als in Phase 15 erstmals vollzogen markiert, statt Gewissheit vorzutaeuschen"
  - "Ableseabstand 120 s wie beim Statusbeobachter, und das Intervall ist Pflichtzeile: zwei Reihen haben in v1.1 zwei Prozentzahlen fuer denselben Sachverhalt erzeugt"

patterns-established:
  - "Ein Skript mit zwei Zweigen fuehrt beide Zweige unter EINER tee-Pipeline und trennt die Abbrueche darunter nach Zweig"
  - "Eine Quelle, die eine Zahl nicht nennen kann, schweigt und uebergibt an die naechste; erst das Schweigen aller Quellen ist der Abbruch"

requirements-completed: []  # MESS-04 und MESS-06 bleiben offen: sie tragen auch 12-08 und Phase 15
requirements-advanced: [MESS-04, MESS-06]

# Metrics
duration: 20min
completed: 2026-09-14
---

# Phase 12 Plan 06: Zweiteilige Cron-Vorpruefung und der Ablaufplan des v1.2-Laufs Summary

**Das Cron-Intervall ist ab jetzt eine im Skript durchgesetzte Messbedingung statt einer Zeile in einer Checkliste: der Konfigurationszweig protokolliert das Intervall vor dem Lauf und bricht ohne es ab, und der Wirkungszweig misst waehrend des Laufs den tatsaechlichen Abstand zwischen zwei Zulaufscheiben, also genau die Groesse, die am 10.09.2026 nominal richtig und effektiv falsch war.**

## Performance

- **Duration:** rund 20 min
- **Started:** 2026-09-14T17:18Z
- **Completed:** 2026-09-14T17:38Z
- **Tasks:** 3 von 3
- **Files modified:** 2 (beide neu, 415 und 150 Zeilen)

## Accomplishments

- `97-cron-vorpruefung.sh` entstand als neue Datei im v1.2-Laufverzeichnis, mit der Aufrufform `<vorher|waehrend>`; ein Aufruf ohne Zweig oder mit einem unbekannten Zweig druckt die Benutzung und endet mit 2.
- Der Kopf nennt den Befund mit seinen Zahlen (5,85 h von 26,6 h ohne Arbeitsvorrat, 194 von 812 Lesungen, Baseline 0,10 h, rund 870 Zeilen je Scheibe alle rund 12 Minuten) und die Lesart, die den zweiten Zweig erzwingt: ein Check, der nur die Konfiguration liest, haette am 10.09.2026 GRUEN gemeldet, waehrend der Befund vorlag.
- Der Exit-Code-Katalog setzt den Katalog des Laufverzeichnisses fort statt ihn zu verschieben: 15 bis 24 bleiben bei `98c-sprachfaelle.sh`, neu sind 25 (keine Quelle lesbar), 26 (Intervall weicht ab), 27 (Wirkungszweig ohne Zahl) und 28 (Scheibenabstand ueber dem Deckel), dazu 2 fuer den falschen Aufruf.
- Der Zweig `vorher` fragt drei Quellen der Reihe nach, jede mit einer Erklaerzeile, welche Wette sie darstellt: die Schlafdauer der Cron-Schleife im All-in-One-Container, die crontab des Wirts fuer den Dienstnutzer und, zuletzt und am langsamsten, den Abstand zweier `lastcron`-Lesungen im Abstand von `SOLL_INTERVALL`. Die dritte traegt im Kommentar, dass sie bereits eine Messung und keine Konfiguration ist.
- Die drei Pflichtzeilen `cron-modus-ist`, `cron-intervall-quelle` und `cron-intervall-ist` werden gedruckt UND in eine Arbeitsdatei mitgeschrieben und am Ende als zitierbarer Block ausgegeben.
- Der Zweig `waehrend` faehrt `occ findling:index` genau einmal je Runde, erkennt eine Zulaufscheibe am Anstieg des Arbeitsvorrats und schreibt `scheiben-erkannt`, `scheibenabstand-min`, `-median`, `-max`, `vorrat-null-in <n>-von-<m>-lesungen` und `ablesereihe-intervall`.
- Alle vier Abbrueche stehen unterhalb der `tee`-Pipeline (Zeilen 356, 370, 378 und 390; die erste Pipeline endet in Zeile 266), mit der Begruendung als Kommentar daneben: der Rueckgabewert einer Pipeline gehoert zu `tee`.
- `00-ablauf.md` traegt die fuenf Abschnitte des Analogs, benennt beide Befunde mit Zahlen und Fundstelle, fuehrt fuenf Schritte mit Rohdatei und Aussage, schreibt die Erwartung E1 bis E7 vor der Messung auf und listet alle zwoelf Rueckgabewerte mit Bedingung, Greifstelle und Folge.

## Task Commits

1. **Task 1: Konfigurationszweig des Cron-Checks, fail-closed** - `09498fc` (feat)
2. **Task 2: Wirkungszweig des Cron-Checks** - `3edb94f` (feat)
3. **Task 3: Ablaufplan 00-ablauf.md des v1.2-Laufverzeichnisses** - `bfe7a9a` (docs)

**Plan metadata:** siehe Schlusscommit dieses Plans (docs)

## Files Created/Modified

- `docs/measurements/2026-09-v12-messung/skripte/97-cron-vorpruefung.sh` (neu, 415 Zeilen) - Kopf mit Befund, Quellenliste, Zwei-Runden-Regel des Systemcrons und Exit-Code-Katalog; Benutzungshinweis und Zweigwahl; Variablenkopf ohne Maschinenpfad (`SKRIPTE`, `REPO`, `OUT`, `ZIEL`, `NEXTCLOUD`, `CRON_CONTAINER`, `CRON_SKRIPT`, `DIENSTNUTZER`, `SOLL_INTERVALL`, `TOLERANZ_PROZENT`, `INTERVALL`, `DECKEL`, `WIRKUNGS_DECKEL`); passwortloser `occ`-Wrapper, `vorrat_von`, `protokoll`, drei Quellenfunktionen; beide Zweige je unter einer `tee`-Pipeline; vier Abbrueche darunter; Fertigzeile `97-CRON-VORPRUEFUNG-FERTIG`
- `docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md` (neu, 150 Zeilen) - Kopf mit den zwei Saetzen vorweg und dem Hinweis zur Schreibweise; Befundtabelle; Schrittfolge mit der Abbruchzeile 52.111 / 37 / 0 / 3.9Gi / 2 Kerne / aarch64; Erwartung E1 bis E7 mit dem woertlich uebernommenen Satz, dass nach der Messung nichts angepasst wird; Abbruchtabelle 15 bis 19 und 22 bis 28; Nach dem Lauf mit der Zeile zum Vokabular-Gate

## Decisions Made

- **Der Wirkungszweig ist Pflicht und nicht Beigabe.** Der Research-Befund 4 ist eindeutig: der Takt war NOMINAL 5 Minuten und EFFEKTIV rund 12 Minuten. Ein Check, der nur `backgroundjobs_mode`, den Cron-Container oder die crontab liest, erfuellt MESS-06 dem Buchstaben nach und verfehlt den Befund. Deshalb hat das Skript zwei Zweige, und der zweite hat seinen eigenen Deckel und seinen eigenen Abbruch.
- **Die teuerste Quelle steht zuletzt.** Die beiden Konfigurationsquellen kosten einen Container-Aufruf. Die dritte Quelle kostet `SOLL_INTERVALL` Sekunden, weil sie zweimal `lastcron` liest, und sie ist bereits eine Messung. Sie wird nur gefragt, wenn die beiden billigen Quellen schweigen, und die Ruecklesung des Solls wiederholt sie nicht.
- **Eine Quelle, die nicht auseinanderrueckt, nennt keine Zahl.** Ticken die beiden `lastcron`-Lesungen nicht auseinander, ist der Takt groesser als das Soll, aber welcher Wert er hat, sagt diese Quelle nicht. Sie schweigt dann, das Urteil heisst `unlesbar`, und der Lauf endet mit 25. Eine geratene Zahl waere schlimmer als keine.
- **Zehn Prozent Toleranz, als Variable mit Begruendung.** `TOLERANZ_PROZENT` laesst die Schwankung eines Cron-Laufs durch, der seine Arbeit noch beendet, und haelt die 720 Sekunden des v1.1-Befundes sicher draussen (zugelassen sind 270 bis 330 s).
- **Der Ableseabstand ist 120 s und steht im Protokoll.** Dieselbe Aufloesung wie `96d-statusbeobachter.py`. Die Zeile `ablesereihe-intervall` ist Pflicht, weil die beiden Reihen des v1.1-Laufs (194 von 812 gegen 62 von 325 Lesungen) rund 24 gegen 19 Prozent fuer denselben Sachverhalt ergeben haben; welche Reihe die Protokollzahl liefert, gehoert neben die Zahl (Annahme A1, ausdruecklich nicht gesichert).
- **Der Ablaufplan nennt fuenf Schritte statt vier.** Die vier Schritte des Plans stehen unveraendert; davor steht die Zustandspruefung, weil die woertlich zu uebernehmende Abbruchzeile (52.111 indexiert, 37 uebersprungen, 0 fehlgeschlagen, 3.9Gi, 2 Kerne, aarch64) an genau diesem Schritt haengt und die Anfahrt beendet, bevor sie nennenswert Geld kostet.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die Feldpruefung der ersten Intervallquelle uebersprang die haeufigste Schreibweise**
- **Found during:** Task 2 (isolierter Lauf des Zweiges `vorher` gegen eine gestellte Cron-Schleife)
- **Issue:** Die erste Fassung suchte das Feld hinter `sleep` und verlangte reine Ziffern. In einer Schleife, die auf EINER Zeile steht (`while true; do php -f ...; sleep 720; done`), heisst das Feld aber `720;` und nicht `720`. Die Quelle schwieg dann stumm, der Lauf fiel auf die dritte Quelle durch und bezahlte deren Frist von `SOLL_INTERVALL` Sekunden; im Test haengte der Lauf sichtbar fuenf Minuten, ohne dass ein Fehler zu sehen war.
- **Fix:** Gelesen wird jetzt ueber einen Ausdruck (`match` auf `sleep[ \t]+[0-9]+`, dann alle Nichtziffern entfernt) statt ueber Felder. Der Kommentar daneben nennt den Grund.
- **Files modified:** docs/measurements/2026-09-v12-messung/skripte/97-cron-vorpruefung.sh
- **Verification:** derselbe isolierte Lauf meldet danach `cron-intervall-quelle aio-cron-container` und `cron-intervall-ist 720`, Rueckgabewert 26; mit einer Schleife ueber mehrere Zeilen und `sleep 300` Rueckgabewert 0 und Fertigzeile
- **Committed in:** 3edb94f

**2. [Rule 2 - Missing critical] Eine gescheiterte Statusabfrage waere als leerer Arbeitsvorrat gezaehlt worden**
- **Found during:** Task 2 (Beobachtungsschleife)
- **Issue:** `vorrat_von` summiert ueber `awk` und druckt `sum + 0`, also 0 auch fuer eine Ausgabe ohne Statusblock. Ein `occ`-Aufruf, der scheitert (Container weg, Instanz im Wartungsmodus), haette damit die Zahl `vorrat-null-in n-von-m-lesungen` erhoeht, also genau die Kennzahl verfaelscht, aus der in v1.1 die 5,85 h gerechnet worden sind.
- **Fix:** Eine Lesung gilt erst als auswertbar, wenn der Block `Work stock` in der Ausgabe steht; sonst heisst sie `unklar`, zaehlt weder als Lesung noch als Nullstand und beeinflusst die Scheibenerkennung nicht. Das folgt dem `unklar`-Muster von `96b-waechter.sh`.
- **Files modified:** docs/measurements/2026-09-v12-messung/skripte/97-cron-vorpruefung.sh
- **Verification:** isolierter Lauf mit gestellter Statusausgabe (Folge 0, 0, 870, 870, 0, 1740) liefert `scheiben-erkannt 2`, `vorrat-null-in 3-von-6-lesungen` und einen bestimmten Median; ein Lauf mit dauerhaft leerem Vorrat endet mit `scheibenabstand-median unbestimmbar` und Rueckgabewert 27
- **Committed in:** 3edb94f

**3. [Rule 2 - Projektregel schlaegt Wortlaut] Die Schlusszeile zum Vokabular-Gate steht mit echten Umlauten**
- **Found during:** Task 3 (Ablaufplan)
- **Issue:** Der Plan laesst zwei Saetze woertlich aus dem Analog uebernehmen. Das Analog schreibt "laeuft ... ueber ... nach aussen" in ASCII, die Projektregel verlangt in deutscher Prosa echte Umlaute.
- **Fix:** Der Satz zur Erwartung ("Dieser Abschnitt ist der Grund ... wird nach der Messung **nicht** angepasst") traegt keinen Umlaut und steht woertlich. Die Zeile zum Vokabular-Gate steht wortgleich, aber in der Schreibweise dieses Projekts. ASCII bleibt genau dort, wo ein Pruefmuster darauf zeigt: in der Tabellenueberschrift "Die Aussage, an der der Schritt haengt" und in der uebernommenen Abbruchzeile "52.111 indexiert, 37 uebersprungen, 0 fehlgeschlagen". Der Kopf der Datei sagt das, wie im Runbook aus 12-07.
- **Files modified:** docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md
- **Verification:** der Verifikationsbefehl von Task 3 meldet GRUEN (alle fuenf Ueberschriften, 52.111, Vokabular-Gate, beide Skriptnamen, kein CR, kein U+2014, kein U+2013)
- **Committed in:** bfe7a9a

---

**Total deviations:** 3 auto-fixed (1 Bug, 2 fehlende Pflichtteile beziehungsweise Regelvorrang)
**Impact on plan:** Kein Scope-Zuwachs. Zwei Abweichungen schliessen Pfade, auf denen der Check eine falsche Zahl protokolliert oder die teuerste Quelle grundlos bezahlt haette; die dritte betrifft die Schreibweise zweier uebernommener Saetze.

## Issues Encountered

- **Die Namen der beiden Cron-Quellen sind Wetten und stehen als solche da.** `CRON_CONTAINER` und `CRON_SKRIPT` tragen Vorgaben auf die Bauform von All-in-One; ob die Schleife dort und unter diesem Namen liegt, ist ohne Box nicht zu klaeren. Antwortet die Quelle nicht, ist das kein Abbruch, sondern der Uebergang zur naechsten Quelle. Der Kommentar sagt beides.
- **Der Erstvollzug steht aus.** Es gibt in dieser Phase keine Box. Geprueft wurde ohne sie: `sh -n`, der Aufruf ohne und mit falschem Argument (beide Rueckgabewert 2 und Benutzungshinweis), sowie vier isolierte Laeufe gegen einen gestellten `sudo`-Ersatz, die alle vier Abbruchpfade und den gruenen Pfad treffen: 25 (keine Quelle antwortet), 26 (Quelle nennt 720 s gegen ein Soll von 300 s), 27 (weniger als zwei Scheiben, Median `unbestimmbar`), 28 (Median ueber dem Deckel) und 0 (Quelle nennt 300 s, Fertigzeile). Der Lauf gegen einen echten Container gehoert zu Phase 15.
- **Der Schritt, der das Soll setzt, ist gelesen und nicht gefahren.** Das Skript druckt die beiden dafuer noetigen Befehle aus und markiert den Schritt ausdruecklich als in Phase 15 erstmals vollzogen; die Ruecklesung laeuft, das Setzen bleibt ein Handgriff auf der Box.
- **Gates gefahren:** `pytest tests/test_measurement_scripts.py` 219 bestanden (214 aus 12-05 plus fuenf neue parametrisierte Faelle fuer `97-cron-vorpruefung.sh`: Wagenruecklauf, Gedankenstrich, Shebang, Maschinenpfad, Passwort auf der Kommandozeile), dazu `sh -n` ueber beide Zweige. `ruff`, `pyright` und `vulture` wurden nicht gefahren: dieser Plan hat keine Python-Datei angefasst.

## User Setup Required

Keine.

## Next Phase Readiness

- Der Exit-Code-Katalog dieses Laufverzeichnisses steht jetzt bei 28. Plan 12-08 und Phase 15 setzen bei 29 fort.
- Fuer Phase 15 gilt die Reihenfolge aus `00-ablauf.md`: Zustandspruefung, `97-cron-vorpruefung.sh vorher`, Bestandsvorlauf der Sonde, `98c-sprachfaelle.sh`, und `97-cron-vorpruefung.sh waehrend` neben dem Volllauf. Sobald ein Skript gefahren ist, gehoert ein sha256-Waechter darueber in `test_measurement_scripts.py`.
- Das Runbook aus 12-07 und der Ablaufplan aus diesem Plan greifen ineinander: das Runbook baut die Box auf und rechnet den Deckel, der Ablaufplan sagt, was in welcher Reihenfolge darauf laeuft und woran abgebrochen wird.
- Offen bleibt bewusst: der Wirkungszweig endet am Rundendeckel und nicht an einer Endeerkennung; er laeuft neben dem Volllauf und wird von dessen Waechter zeitlich eingerahmt, nicht von sich selbst.

## Self-Check: PASSED

- `docs/measurements/2026-09-v12-messung/skripte/97-cron-vorpruefung.sh` existiert (415 Zeilen, Shebang `#!/bin/sh` mit LF, `sh -n` ohne Befund)
- `docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md` existiert (150 Zeilen, alle fuenf Abschnittsueberschriften vorhanden)
- Alle drei Commits sind in `git log` auffindbar: `09498fc`, `3edb94f`, `bfe7a9a`
- Keine der beiden Dateien traegt einen Wagenruecklauf, ein U+2014, ein U+2013, einen Maschinenpfad oder ein Passwort auf einer Kommandozeile; das Wort "archiv" kommt in keiner von beiden vor
- Die vier Abbrueche stehen unterhalb der ersten `tee`-Pipeline (266 gegen 356, 370, 378, 390)

---
*Phase: 12-messwerkzeug-runbook-und-terminentscheid*
*Completed: 2026-09-14*
