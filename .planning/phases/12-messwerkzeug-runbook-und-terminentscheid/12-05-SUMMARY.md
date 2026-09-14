---
phase: 12-messwerkzeug-runbook-und-terminentscheid
plan: 05
subsystem: measurement-tooling
tags: [messskript, sprachfaelle, rangsemantik, rrf, di-10-02, di-11-01, posix-sh]

# Dependency graph
requires:
  - phase: 12-messwerkzeug-runbook-und-terminentscheid
    provides: "73-bestand-sonde.py, das v1.2-Laufverzeichnis und der enge Geltungsbereich der Messskript-Gates (Plan 12-04)"
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: "98b-sprachfaelle.sh als Vorlage, das dreiwertige Urteil und DRIVEN_FASSUNG_RULE"
provides:
  - "98c-sprachfaelle.sh: die zehn Sprachfaelle, dreiwertig beurteilt am Rang der eigenen Datei statt an einer gedeckelten Trefferzahl"
  - "Abschnitt 3b: Rangmessung nach Upload und Indexierung, Kennungen aus dem Antwortkopf OC-FileId"
  - "Exit-Code 24 fuer eine Rangmessung ohne Datei-Kennungen, fail-closed unter der tee-Pipeline"
affects: [12-06-cron-vorpruefung, 12-07-runbook, 15-messphase-eine-box-anfahrt]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Messgroesse im Prozess erheben statt ueber eine Route (T-02-93), jetzt auch im Fahrer des Laufs"
    - "Eigene Datei-Kennungen aus dem Antwortkopf des Uploads, ohne zweite Abfrage"
    - "Eine Zuordnung Fall/Begriff/Datei als ein Here-Document, in eine Arbeitsdatei geschrieben, von beiden Schleifen gelesen"

key-files:
  created:
    - docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh
  modified: []

key-decisions:
  - "Die Messbarkeit entscheidet der kleinere der beiden Raenge; ist keine der beiden Angaben eine Zahl, gilt ausserhalb"
  - "rang-erhoben ja steht erst, wenn die Sonde im zweiten Lauf wirklich durchgelaufen ist, nicht schon bei vorhandenen Kennungen"
  - "Die Zusicherungen und jq-Ausdruecke der zehn Faelle bleiben woertlich wie in 98b, nur die Erklaerkommentare sind deutsch"
  - "Abschnitt 3b steht zwischen Indexierung und Faellen: der Rang ist erst messbar, wenn die eigene Datei existiert und indexiert ist"

patterns-established:
  - "Nachfolgefassung eines Messskripts: neue Datei, neues Laufverzeichnis, Kopfabsatz nennt die gefahrene Fassung und ihren Waechter"
  - "Ein Wort statt einer Zahl (ausserhalb, keine-kennung) wird vor jedem Schwellenvergleich abgefangen, nie hineingerechnet"

requirements-completed: []  # MESS-04 bleibt offen: es traegt auch 12-06 bis 12-08
requirements-advanced: [MESS-04]

# Metrics
duration: 15min
completed: 2026-09-14
---

# Phase 12 Plan 05: 98c-sprachfaelle.sh mit Rangsemantik und Abschnitt 3b Summary

**Die Messbarkeit der zehn Sprachfaelle haengt ab jetzt am Rang der eigenen Datei in den beiden Ranglisten, gemessen im Prozess des Containers, und nicht mehr an einer Trefferzahl, die bei 26 gedeckelt war und die Schwelle 64 nie erreichen konnte.**

## Performance

- **Duration:** rund 15 min
- **Started:** 2026-09-14T16:52Z
- **Completed:** 2026-09-14T17:07Z
- **Tasks:** 3 von 3
- **Files modified:** 1 (neu, 778 Zeilen)

## Accomplishments

- `98c-sprachfaelle.sh` entstand als neue Datei im v1.2-Laufverzeichnis. `98b-sprachfaelle.sh` und `98-sprachfaelle.sh` sind byteweise unberuehrt (nachgerechnet: `ef74a070...c85669` bei 35.344 Byte und `5f9607fc...ade1d`), die Hausregel `DRIVEN_FASSUNG_RULE` ist eingehalten.
- Abschnitt 0 misst den Bestand im Prozess: `docker cp` traegt die Sonde in den Container, `docker exec` faehrt sie mit dem Python der Anwendung. Es wird keine Route und kein Konto gefragt, also ueberquert keine Trefferzahl eine Prozessgrenze (T-02-93, T-12-20).
- Abschnitt 3b ist die einzige strukturelle Aenderung gegenueber `98b` und steht zwischen Indexierung und Faellen, mit dem Grund im Kommentar: der Rang ist erst messbar, wenn die eigene Datei existiert und indexiert ist.
- Die eigenen Kennungen kommen aus dem Antwortkopf `OC-FileId` jedes Uploads, rein numerisch (Instanz-Suffix und Auffuell-Nullen abgeschnitten), und reisen ausschliesslich in der Umgebung: `export DATEI_IDS`, `sudo --preserve-env=DATEI_IDS docker exec -e DATEI_IDS`.
- `messbar()` kennt drei Gruende der Nichtmessbarkeit (Rang nicht erhoben, eigene Datei in keiner der beiden Listen, Rang groesser als die Schwelle 64) und traegt die RRF-Begruendung als Kommentar: wer in BEIDEN Listen vor der eigenen Datei liegt, liegt mit beiden Summanden vor ihr und damit auch in der fusionierten Liste.
- Alle Abbrueche stehen unter der `tee`-Pipeline, in der Reihenfolge 19, 24, 15, 16, 23, 17 (Zeilen 736 bis 775, die Pipeline endet in Zeile 720). Keine Verweigerung verschwindet als Zeile in einer Rohdatei (T-12-23).
- Die zehn Faelle tragen ihre Zusicherungen und `jq`-Ausdruecke woertlich aus `98b`, samt der zweiten Suche mit dem Ausschluss-Operator in Fall 6. Die Bilanzzeile nennt weiterhin zwei Zahlen.

## Task Commits

1. **Task 1: Kopf, Exit-Codes, Variablen, Hilfsfunktionen und Abschnitt 0 ueber die Sonde** - `ee150a5` (feat)
2. **Task 2: Abschnitte 1 bis 3, mit Erfassung der eigenen Datei-Kennungen** - `82ac9ba` (feat)
3. **Task 3: Abschnitt 3b Rangmessung, die zehn Faelle, Bilanz und Abbrueche** - `5b4a78d` (feat)

**Plan metadata:** siehe Schlusscommit dieses Plans (docs)

## Files Created/Modified

- `docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh` (neu, 778 Zeilen) - Kopf mit der Nachfolgebegruendung, dem Befund der gedeckelten 26 und der Herleitung der Schwelle 64; Exit-Code-Katalog 15 bis 24; Variablenkopf ohne Maschinenpfad, neu `CONTAINER`, `SONDE`, `RANG_SCHWELLE`; `occ`-Wrapper, `vorrat_von`, `rang_aus_sonde`, `search`, `fail`, `messbar`, `urteil`; Abschnitte 0, 1, 2, 3, 3b, 4, Bilanz, 5, Skelett-Rueckgabe; sechs Abbruchpruefungen unter der Pipeline; Fertigzeile `98C-SPRACHFAELLE-FERTIG`

## Decisions Made

- **Der kleinere der beiden Raenge ist die Zahl des Urteils.** Die Fusion stellt die eigene Datei nicht schlechter als ihre bessere der beiden Positionen; die schlechtere waere also ein zu strenges Urteil und die Summe keine Position. Ist keine der beiden Angaben eine Zahl (`ausserhalb`, `keine-kennung`), wird `ausserhalb` geschrieben und nie gegen die Schwelle gerechnet.
- **Der Schluessel der Zeilensuche traegt das ganze geklammerte Feld.** `begriff='bescheid'` wuerde sonst auch die Zeile von `begriff='type:pdf bescheid'` treffen; die beiden Faelle 6 und 7 haetten dieselbe Zahl bekommen, ohne dass es auffiele. Isoliert gegen eine gestellte Sondenausgabe geprueft.
- **`rang-erhoben ja` erst nach einem erfolgreichen zweiten Sondenlauf.** Der Plan verlangt das Urteil an den Kennungen; fail-closed ist strenger und richtig: Kennungen ohne gefahrene Sonde ergeben keinen einzigen Rang, und alle zehn Faelle hiessen dann NICHT MESSBAR aus dem falschen Grund. Exit 24 faengt beide Faelle ab.
- **Das Here-Document der Zuordnung steht NICHT in Anfuehrungszeichen** und wird einmal in `$WORK/zuordnung` geschrieben. Die Dateinamen sind oben Variablen, damit eine Umbenennung an einer Stelle bricht; beide Schleifen des Abschnitts lesen dieselbe Arbeitsdatei, es bleibt also bei einem einzigen Here-Document mit zehn Zeilen.
- **Erklaerkommentare deutsch, Zusicherungstexte englisch.** Die Meldungstexte und `jq`-Ausdruecke der zehn Faelle sind woertlich aus `98b` uebernommen, damit die Rohdateien beider Fassungen Zeile fuer Zeile vergleichbar bleiben; die Prosa daneben folgt der Sprache dieses Laufverzeichnisses (wie `73-bestand-sonde.py`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Der Verifikationsbefehl von Task 1 verbietet die Zeichenkette, die der Plan im Kopf verlangt**
- **Found during:** Task 1 (Verifikation)
- **Issue:** Der Plan laesst den Wegfall von `FREMD_SCHWELLE` begruenden und prueft gleichzeitig mit `! grep -q 'FREMD_SCHWELLE'` ueber die ganze Datei. Ein Kommentar, der die alte Variable beim Namen nennt, faerbt die eigene Verifikation rot.
- **Fix:** Der Kommentar nennt sie jetzt der Sache nach ("die alte Schwelle des Fremdbestands, samt ihrer Tiefe"). Die Begruendung bleibt vollstaendig, der Bezeichner kommt nicht mehr vor.
- **Files modified:** docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh
- **Verification:** Verifikationsbefehl von Task 1 meldet GRUEN
- **Committed in:** ee150a5

**2. [Rule 2 - Missing critical] `messbar()` faengt jedes Wort ab, nicht nur `ausserhalb`**
- **Found during:** Task 1 (Urteilsfunktionen)
- **Issue:** Der Plan nennt drei Faelle: leer, `ausserhalb`, Zahl ueber der Schwelle. Die Sonde kennt aber auch `keine-kennung`, und `[ "$rang" -gt 64 ]` auf ein Wort ist unter `set -eu` ein Laufzeitfehler mitten im Lauf.
- **Fix:** Ein `case`-Zweig auf `*[!0-9]*` faengt jedes nicht numerische Wort ab und nennt es in der Meldung. Die drei Gruende des Plans bleiben unterscheidbar.
- **Files modified:** docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh
- **Verification:** isolierter Lauf der Funktion gegen 12, 87, `ausserhalb` und eine leere Datei liefert genau ein messbares Ergebnis und drei benannte Gruende
- **Committed in:** ee150a5

**3. [Rule 2 - Missing critical] Ein gescheiterter zweiter Sondenlauf setzte sonst trotzdem `rang-erhoben ja`**
- **Found during:** Task 3 (Abschnitt 3b)
- **Issue:** Nach dem Wortlaut des Plans haengt das Urteil allein an der Frage, ob Kennungen erhoben wurden. Faellt der Sondenlauf aus, gibt es dennoch keinen einzigen Rang, und der Lauf liefe mit zehn NICHT MESSBAR bis zur Bilanz durch, statt mit 24 zu enden.
- **Fix:** `rang-erhoben ja` wird erst nach dem erfolgreichen `docker exec` geschrieben; beide Ursachen (keine Kennung, keine Sonde) enden unter der Pipeline mit 24, und die Meldung nennt beide.
- **Files modified:** docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh
- **Verification:** Verifikationsbefehl von Task 3 meldet GRUEN, `exit 24` steht in Zeile 745 unter der Pipeline (Zeile 720)
- **Committed in:** 5b4a78d

---

**Total deviations:** 3 auto-fixed (1 blockierend, 2 fehlende Pflichtteile)
**Impact on plan:** Kein Scope-Zuwachs. Eine Abweichung betrifft einen Kommentartext gegen den Pruefbefehl des Plans, zwei schliessen Pfade, auf denen der Lauf sonst mit einer falschen Aussage weitergelaufen waere.

## Issues Encountered

- **`PWFILE` bleibt im Variablenkopf, ohne gelesen zu werden.** Der Plan fuehrt die Variable in der Liste, die Vorpruefung braucht aber kein zweites Konto-Passwort mehr, seit sie keine Route fragt. Sie steht mit genau diesem Kommentar da, weil der Boxplan sie uebergibt und ein Lauf, der sie setzt, daran nicht scheitern soll. Wer sie spaeter entfernt, entfernt nichts, was noch etwas tut.
- **Der Erstvollzug steht weiter aus.** Es gibt in dieser Phase keine Box. Geprueft wurde ohne sie: `sh -n`, ein echter Lauf bis zur Verweigerung (kein `CI_LAUF`, Rueckgabewert 22, keine Ausgabe, keine Datei im Zielverzeichnis), sowie isolierte Laeufe der beiden neuen Auswerteteile gegen gestellte Eingaben (Rangzeile der Sonde mit beiden Zahlen, mit einer Zahl, mit zwei Worten; Antwortkopf `OC-FileId: 00000023oc9mn3rmbkgs` mit Wagenruecklauf ergibt `23`). Der Lauf gegen einen echten Container gehoert zu Phase 15.
- **Gates gefahren:** `pytest tests/test_measurement_scripts.py` 214 bestanden (209 aus 12-04 plus fuenf neue parametrisierte Faelle fuer `98c`: Wagenruecklauf, Gedankenstrich, Shebang, Maschinenpfad, Passwort auf der Kommandozeile), dazu die ruff-Aufrufkette der CI (`check .` und `format --check .` im Backend, beides zusaetzlich mit `--config pyproject.toml ../scripts`), alle vier gruen. `pyright` und `vulture` wurden nicht erneut gefahren: dieser Plan hat keine Python-Datei angefasst.

## User Setup Required

Keine.

## Next Phase Readiness

- Plan 12-06 kann den Exit-Code-Katalog bei 25 fortsetzen; 24 ist mit "Abschnitt 3b konnte keine Datei-Kennungen erheben" vergeben.
- Die Cron-Vorpruefung aus 12-06 findet in `98c` das Muster vor, nach dem sie sich richten kann: Urteil in eine Datei im Arbeitsverzeichnis schreiben, im Block nur drucken, unter der Pipeline abbrechen.
- Fuer Phase 15 gilt: `98c` wird gefahren und danach nicht mehr angefasst. Sobald sie gefahren ist, gehoert ein sha256-Waechter ueber sie in `test_measurement_scripts.py`, wie ihn `98` und `98b` tragen.
- Offen bleibt bewusst: die Sonde saettigt beide Fensterzahlen bei 100, was die Lesart der Fensterbelegung oberhalb davon begrenzt; der Rang selbst ist davon nicht betroffen, solange die eigene Datei im Fenster steht.

## Self-Check: PASSED

- `docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh` existiert (778 Zeilen, Shebang `#!/bin/sh` mit LF, `sh -n` ohne Befund)
- Alle drei Commits sind in `git log` auffindbar: `ee150a5`, `82ac9ba`, `5b4a78d`
- `98b-sprachfaelle.sh` und `98-sprachfaelle.sh` tragen unveraendert ihre gepinnten Pruefsummen
- Die Datei traegt keinen Wagenruecklauf, kein U+2014, kein U+2013, keinen Maschinenpfad und kein Passwort auf einer Kommandozeile

---
*Phase: 12-messwerkzeug-runbook-und-terminentscheid*
*Completed: 2026-09-14*
