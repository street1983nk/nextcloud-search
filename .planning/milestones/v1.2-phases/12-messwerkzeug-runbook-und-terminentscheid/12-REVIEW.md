---
phase: 12-messwerkzeug-runbook-und-terminentscheid
reviewed: 2026-09-16T00:00:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - .github/workflows/deploy-harp.yml
  - .github/workflows/python.yml
  - backend/tests/test_measurement_scripts.py
  - backend/tests/test_ops_scripts.py
  - docs/measurements/2026-09-v12-messung/rohdaten/01-aws-lesende-proben.txt
  - docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md
  - docs/measurements/2026-09-v12-messung/skripte/73-bestand-sonde.py
  - docs/measurements/2026-09-v12-messung/skripte/97-cron-vorpruefung.sh
  - docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh
  - docs/runbook-messbox.md
  - scripts/ops/aws_box.sh
findings:
  critical: 2
  warning: 5
  info: 3
  total: 10
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-09-16
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Geprueft wurden die elf Dateien der Phase 12 (Diff-Basis `ac2e425^..HEAD`): der stable35-Flag-Ausbau in `deploy-harp.yml`, der Pfadfilter in `python.yml`, die erweiterten Gates in beiden Testdateien, die drei neuen Messskripte des v1.2-Laufverzeichnisses samt Ablaufplan und Rohdatei, das Runbook der Messbox und der neue `restore`-Unterbefehl in `aws_box.sh`. Querbezuege wurden verifiziert: die Sonde `73-bestand-sonde.py` benutzt `ranked_sides`, `read_side`, `build_query` und `RewrittenQuery.query is None` korrekt (RankedSides.lexical/semantic sind `list[int]`, die `in`/`index`-Pruefungen der Sonde passen); die awk-Schluessel `begriff='...'` in `98c` kollidieren nicht zwischen `bescheid` und `type:pdf bescheid`; die `create-tags`-Umtaggung in `cmd_restore` ueberschreibt den geerbten `purpose`-Tag korrekt (gleicher Key); die Zahlen des Deckel-Rechenblatts (36 h 07 min, 0,115841 USD/h, 41,54 h, 4,8653 USD) rechnen nach; keine Em-/En-Dashes in den neuen Dateien; Zeilenenden der Skripte sind LF und von `.gitattributes` gedeckt; keine Geheimnisse in den Rohdaten.

Zwei Befunde sind kritisch, beide in `98c-sprachfaelle.sh`: der dokumentierte Fruehabbruch bei nicht fahrbarer Sonde existiert im Skript nicht (Regression gegenueber 98b, drei Dokumentationsstellen behaupten das Gegenteil), und die Arbeitsvorrat-Schleife hat genau die Verfaelschung, die `97-cron-vorpruefung.sh` im selben Commit-Zug ausdruecklich als Falle benennt und abfaengt.

## Critical Issues

### CR-01: 98c bricht bei nicht fahrbarer Sonde NICHT vor dem Upload ab, obwohl drei Dokumente genau das zusichern

**File:** `docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh:329-348` (Abschnitt 0) und `:732-737` (Exit 19)
**Issue:** Schlaegt Abschnitt 0 fehl (Sonde fehlt, `docker cp` scheitert, Sonde laeuft nicht durch), schreibt das Skript nur `vorpruefung-gefahren nein` und **faehrt weiter**: Abschnitt 1 setzt `skeletondirectory` auf leer und setzt das Passwort eines ggf. bestehenden Kontos zurueck, Abschnitt 2 laedt 39 Dateien hoch, Abschnitt 3 schlaeft mindestens 360 s und pollt bis zu 40 Runden, danach laufen alle zehn Faelle. Erst unterhalb der `tee`-Pipeline faellt Exit 19. Die Vorgaengerfassung `98b-sprachfaelle.sh` faehrt ihre Vorpruefung VOR dem Pipeline-Block und bricht dort direkt mit 19 ab (Zeilen 300/314/318/325); der Test `test_the_successor_stops_when_the_foreign_stock_cannot_be_asked` pinnt fuer 98b ausdruecklich "It ended before the account section, so nothing on any box was touched". Drei Stellen dokumentieren dieses Verhalten auch fuer den v1.2-Lauf und sind damit falsch: `00-ablauf.md:115` und `docs/runbook-messbox.md:701` und `:724` ("Der Abbruch kommt vor dem Hochladen der 39 Dateien") sowie `00-ablauf.md:79` ("Beide Abbrueche kommen frueh und kosten Sekunden", was fuer Exit 24 ebenfalls nicht stimmt: er faellt erst nach Upload und Indexierung). Folge auf der bezahlten Box: eine gescheiterte Vorbedingung kostet Stunden Boxzeit und mutiert die Instanz (Konto-Passwort, Skeleton), bevor die Verweigerung faellt.
**Fix:** Im `else`-Zweig fehlt nichts, aber die drei Fehlzweige von Abschnitt 0 brauchen ein `exit` im Block. Der Kommentar in Zeile 345-347 begruendet das Weglassen mit "ein exit ... verliesse nur die Subshell", uebersieht aber: genau das ist das gewuenschte Verhalten. Ein `exit 1` im Block beendet die Subshell, ueberspringt Abschnitt 1 bis 5, `tee` schreibt die Rohdatei fertig, und der Block unterhalb der Pipeline liest `vorpruefung-gefahren nein` und endet mit 19, exakt wie bei 98b:
```sh
    else
        cat "$WORK/bestand-vorlauf.txt"
        echo 'vorpruefung-gefahren ja' >"$WORK/vorpruefung-urteil"
    fi
    cat "$WORK/vorpruefung-urteil"
    # NEU: die Subshell verlassen, wenn die Sonde nicht gefahren ist. Der
    # Rueckgabewert 19 faellt wie bisher unterhalb der Pipeline.
    if [ "$(cat "$WORK/vorpruefung-urteil")" != 'vorpruefung-gefahren ja' ]; then
        exit 1
    fi
```

### CR-02: Die Arbeitsvorrat-Schleife in 98c zaehlt einen gescheiterten occ-Aufruf als leeren Vorrat, exakt die Verfaelschung, die 97 im selben Plan abfaengt

**File:** `docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh:418-432`
**Issue:** `occ findling:index >"$WORK/status.txt" 2>&1 || true` gefolgt von `vorrat=$(vorrat_von "$WORK/status.txt")`. `vorrat_von` druckt `sum + 0`, also **0**, wenn die Ausgabe keinen `Work stock`-Block traegt (occ-Fehler, Container weg, sudo-Problem). Die Schleife bricht dann mit `vorrat -eq 0` ab und schreibt `arbeitsvorrat-leer ja`: Ein einziger transienter occ-Fehlschlag laesst den Lauf glauben, die Indexierung sei fertig. Die zehn Faelle laufen anschliessend gegen einen unfertigen Index, die OCR-Faelle 8 bis 10 werden rot aus dem falschen Grund (Exit 17 mit falscher Diagnose), und der Schutz von Exit 16 ist wirkungslos. `97-cron-vorpruefung.sh:301-309`, im selben Plan geschrieben, benennt genau diese Falle woertlich ("Ohne diese Frage haette ein gescheiterter Aufruf die Summe 0 geliefert und als leerer Arbeitsvorrat gezaehlt, also genau die Zahl verfaelscht") und prueft mit `grep -q '^Work stock'`. 98c laesst den Guard weg.
**Fix:** Denselben Guard wie in 97 einbauen:
```sh
        occ findling:index >"$WORK/status.txt" 2>&1 || true
        if grep -q '^Work stock' "$WORK/status.txt" 2>/dev/null; then
            vorrat=$(vorrat_von "$WORK/status.txt")
        else
            vorrat=unklar
        fi
        date -u +"indexierung runde=$runde vorrat=$vorrat %Y-%m-%dT%H:%M:%SZ"
        if [ "$vorrat" != unklar ] && [ "$vorrat" -eq 0 ]; then
            break
        fi
```
und unten `if [ "$vorrat" != unklar ] && [ "$vorrat" -eq 0 ]` fuer das `index-urteil` (eine `unklar`-Endlage ist `arbeitsvorrat-leer nein`).

## Warnings

### WR-01: cmd_restore kann ein fremdes (auch leeres) Volume anhaengen und schreibt dann eine falsche Herkunft in die Zustandsdatei

**File:** `scripts/ops/aws_box.sh` (cmd_restore, Wiederverwendungszweig; im Diff die Zeilen um `describe-volumes ... Name=tag:$TAG_KEY`)
**Issue:** Der Aufraeumzweig nimmt jedes unangehaengte Volume mit `purpose=findling-phase5` in der Zone, ohne zu pruefen, dass es aus dem angeforderten Snapshot stammt. Ein Ueberbleibsel von `cmd_volume` (leeres Volume, gleicher Tag, gleiche Zone, exakt das Szenario "create gelang, attach scheiterte", das der Kommentar selbst als Motivation nennt) wird kommentarlos angehaengt, und die Zustandsdatei bekommt anschliessend `# volume restored from a snapshot` und `VOLUME_FROM_SNAPSHOT=$snapshot_id`, also eine Herkunftsangabe, die fuer dieses Volume nie gestimmt hat. Das Runbook zitiert genau dieses Feld als Beleg, gegen welchen Korpus gemessen wurde (Abschnitt 9.1). Der Mount scheitert bei einem leeren Volume zwar sichtbar, aber die Diagnose zeigt dann auf das Dateisystem statt auf die Volume-Herkunft, und die Rohdatei traegt die falsche Zeile bereits.
**Fix:** Den describe-volumes-Filter um `"Name=snapshot-id,Values=$snapshot_id"` ergaenzen (oder das Feld `SnapshotId` des Treffers gegen `$snapshot_id` pruefen und bei Abweichung verweigern). Zusaetzlich: bei mehr als einem Treffer nicht stillschweigend neu erzeugen, sondern die Kandidaten nennen und abbrechen, wie es die uebrigen Verweigerungen dieses Skripts halten.

### WR-02: Der Wirkungszweig von 97 kann die Anfahrt nicht anhalten, obwohl Skript und Runbook das zusichern; er laeuft immer die vollen 27 Stunden

**File:** `docs/measurements/2026-09-v12-messung/skripte/97-cron-vorpruefung.sh:293-326` und `:403-412`; `docs/runbook-messbox.md:731`
**Issue:** Exit 28 ("die Anfahrt soll an dieser Stelle halten, statt eine unvergleichbare Laufzeit zu erzeugen") faellt erst, nachdem die Schleife alle `DECKEL`-Runden (Default 810 x 120 s = 27 h) durchlaufen hat, denn Median und Urteil entstehen ausschliesslich nach der Schleife. Der v1.1-Befund (Scheibenabstand ~720 s statt 300 s) waere also erst NACH der vollen, unvergleichbaren Laufzeit gemeldet, nicht statt ihrer. Umgekehrt: endet der Volllauf frueher als 27 h (die erhoffte Wirkung des Top-up-Fixes), pollt der Zweig trotzdem bis Runde 810 weiter; wer ihn abbricht (kill), bekommt weder Protokollblock noch Rueckgabewert, also gar kein Urteil, und die Pflichtzeilen aus Runbook Abschnitt 6.2 fehlen.
**Fix:** Zwei Ergaenzungen in der Schleife: (a) frueher Abbruch als Befund, sobald z. B. zwei aufeinanderfolgende gemessene Abstaende ueber `WIRKUNGS_DECKEL` liegen (Abstaende liegen ja bereits pro Scheibe in `$WORK/abstaende`); (b) ein regulaeres Schleifenende, wenn der Vorrat ueber N Runden 0 bleibt und der beobachtete Lauf damit vorbei ist, sodass Protokollblock und Urteil immer geschrieben werden. Beide Deckel als Variablen mit Vorgabe, im Stil der uebrigen.

### WR-03: 98c laesst bei einem Abbruch in Abschnitt 1 die Instanz mit geleertem skeletondirectory zurueck

**File:** `docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh:359, 369, 711-717`
**Issue:** Zeile 359 setzt `skeletondirectory` auf leer; die Ruecksetzung steht erst am Ende des Blocks (Zeile 711-717). Dazwischen ist `OC_PASS=... occ user:add ...` (Zeile 369) der einzige occ-Aufruf ohne `|| true`: schlaegt er fehl, beendet `set -e` die Subshell, alle folgenden Abschnitte inklusive der Skelett-Ruecksetzung entfallen, und die Messinstanz behaelt dauerhaft die geaenderte Konfiguration. Der `trap ... EXIT` raeumt nur `$WORK` und nicht die Instanz.
**Fix:** Entweder die Ruecksetzung fail-safe machen (den vorherigen Wert vor dem Setzen in eine Datei unter `$WORK` schreiben und die Ruecksetzung zusaetzlich unterhalb der Pipeline ausfuehren, wo sie jeden Blockausgang erreicht), oder `user:add` wie die Nachbarn mit explizitem Urteil abfangen, das den Block kontrolliert verlaesst.

### WR-04: Keine Verhaltens-Tests fuer die Verweigerungspfade von 98c und 97, obwohl die 98b-Pendants getestet sind und boxlos laufen wuerden

**File:** `backend/tests/test_measurement_scripts.py` (Plan 12-04-Erweiterung)
**Issue:** Fuer 98b existieren `test_the_successor_refuses_a_run_without_a_ci_run_number` (fuenf Formen von CI_LAUF, Exit 22, keine Rohdatei) und der Fail-closed-Test auf Exit 19. Die Nachfolgefassung 98c hat denselben Exit-22-Vertrag und fuenf neue Rueckgabewerte, `97-cron-vorpruefung.sh` hat den Usage-Vertrag (Exit 2) und die Exit-25-Logik, und beide Verweigerungen brauchen weder Box noch Netz (98c prueft CI_LAUF vor dem ersten sudo/docker/curl; 97 prueft den Zweig vor allem anderen). Getestet werden fuer das v1.2-Verzeichnis nur die drei Textgates (Shebang, Maschinenpfad, Passwort). Haette ein Exit-22-Test fuer 98c existiert, waere CR-01 als Abweichung vom 98b-Muster vermutlich aufgefallen; die Projektregel "Tests: alle Paths" verlangt die Fehlerpfade ausdruecklich. Die Pruefsummen-Waechter kommen laut `00-ablauf.md` Abschnitt 5 zurecht erst nach dem Fahren, die Verweigerungstests aber nicht.
**Fix:** Nach dem Muster von `a_run_of_the_successor` zwei parametrisierte Laeufe ergaenzen: 98c ohne/mit unbrauchbarem `CI_LAUF` (Erwartung Exit 22, leeres OUT) und `97-cron-vorpruefung.sh` ohne Zweig bzw. mit unbekanntem Zweig (Erwartung Exit 2, Usage auf stderr).

### WR-05: Veralteter Kommentar und tote Matrix-Mechanik in deploy-harp.yml nach dem Flag-Ausbau

**File:** `.github/workflows/deploy-harp.yml:126-128`
**Issue:** Ueber `continue-on-error: ${{ matrix.tolerate-failure }}` steht weiterhin: "The one entry that may fail is the one for a server version that is not released yet, and which one that is stands at the entry itself." Seit Plan 12-02 traegt kein Eintrag mehr `tolerate-failure: true` (Zeilen 187, 191, 209, 229 sind alle `false`), NC 35 ist released, und am stable35-Eintrag steht nichts dergleichen mehr. Der Kommentar behauptet also einen Zustand, den die Matrix nicht mehr hat; wer eine rote stable35-Zeile diagnostiziert, liest hier die falsche Auskunft. In diesem Repositorium sind Kommentare ausdruecklich Teil des Belegs (dasselbe Muster wird in Zeile 499-503 der Datei selbst als Korrekturfall benannt). Die Spalte `tolerate-failure` und die `continue-on-error`-Zeile sind zudem funktionslos geworden.
**Fix:** Entweder den Kommentar durch den heutigen Stand ersetzen ("seit 12-02 toleriert kein Eintrag ein Scheitern; die Spalte bleibt als Mechanik fuer die naechste unreleaste Serverversion stehen") oder Spalte samt `continue-on-error` entfernen und beim naechsten stable36-Eintrag neu einfuehren.

## Info

### IN-01: `docker exec sh -c "cat $CRON_SKRIPT"` expandiert die Variable ungequotet in der Container-Shell

**File:** `docs/measurements/2026-09-v12-messung/skripte/97-cron-vorpruefung.sh:173`
**Issue:** `sh -c "cat $CRON_SKRIPT"` unterliegt Word-Splitting und Interpretation in der Shell des Containers, falls ein Operator `CRON_SKRIPT` mit Leerzeichen oder Metazeichen setzt. Der Umweg ueber `sh -c` ist zudem unnoetig.
**Fix:** `sudo docker exec "$CRON_CONTAINER" cat "$CRON_SKRIPT" 2>/dev/null | awk ...`

### IN-02: `date +%s%N` ist GNU-spezifisch in einem #!/bin/sh-Skript

**File:** `docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh:531-533`
**Issue:** Auf einer Nicht-GNU-`date` (BusyBox) druckt `%N` das Literal `N`, und die anschliessende Arithmetik `$((($(date +%s%N) - start) / 1000000))` beendet die Subshell unter `set -eu` mitten in Fall 1. Auf der Ubuntu-Zielbox unkritisch, aber die Kopfzeile des Skripts verspricht Maschinenunabhaengigkeit.
**Fix:** Auf Sekundenaufloesung zurueckfallen (`date +%s`) oder die Millisekundenmessung als "nur mit GNU date" kennzeichnen und bei nicht-numerischer Ausgabe ueberspringen.

### IN-03: Docstring der Weitbereichs-Pruefung nennt "Four runs have scripts today", inzwischen sind es sechs

**File:** `backend/tests/test_measurement_scripts.py:886-904`
**Issue:** Die Untergrenzen-Assertion ist korrekt (Floor), aber der Docstring zaehlt vier Laufverzeichnisse, waehrend `2026-09-werkzeugfixe` und `2026-09-v12-messung` laengst Skripte tragen. Reine Doku-Drift innerhalb eines Tests, der Drift andernorts bewacht.
**Fix:** Docstring aktualisieren oder die Zahl streichen ("mindestens diese vier").

---

**Hinweis zur Pruefweite:** `deploy-harp.yml` (3288 Zeilen) wurde im geaenderten Bereich (Matrix, Zeilen 1-1025) vollstaendig und im Rest per Muster (`tolerate-failure`, `continue-on-error`, stale Verweise) geprueft; die uebrigen 2263 Zeilen sind in dieser Phase unveraendert. Alle anderen zehn Dateien wurden vollstaendig gelesen. Berechnungen des Deckel-Rechenblatts (Runbook 2.1, 2.3, 2.5, Schritt 9) wurden nachgerechnet und stimmen. Die Geheimnisregeln (T-05-17, T-10-27) sind in allen neuen Dateien eingehalten: Passwoerter reisen in Umgebung bzw. curlrc mit Modus 600, die Rohdatei maskiert die Kontokennung.

_Reviewed: 2026-09-16_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
