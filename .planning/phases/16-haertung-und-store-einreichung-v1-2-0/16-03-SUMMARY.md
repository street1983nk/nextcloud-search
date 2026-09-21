---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 03
subsystem: measurement-tooling
tags: [nachfolgefassung, l-03, l-04, auflage-a1, messwerkzeug, pytest, shell]

# Dependency graph
requires:
  - phase: 15-messphase-eine-box-anfahrt
    provides: die sechs gefahrenen Messfassungen mit ihren Pruefsummen, die Befunde L-03 und L-04 und die Regel, dass eine gefahrene Fassung nicht editiert wird
  - phase: 16-haertung-und-store-einreichung-v1-2-0
    provides: das Geheimnis- und Vokabular-Gate ueber docs/ aus Plan 16-02, in dessen Ausnahmeliste die neue Datei einen Eintrag braucht
provides:
  - docs/measurements/2026-09-nachfolgefassungen/skripte/92c-wechsel.sh, die Nachfolgefassung von 92b mit gepruefter Phase-B-Registrierung
  - docs/measurements/2026-09-nachfolgefassungen/skripte/99d-filter-sortierung.sh, die Nachfolgefassung von 99c mit der Passwortdatei
  - vier Waechter in backend/tests/test_measurement_scripts.py, je Fassung einer fuer die Herkunft und einer fuer die behobene Eigenschaft
  - das neue Laufverzeichnis als vierter Eintrag in NARROW_SCOPE_DIRS
affects: [16-12-phasenaudit, 16-13-launch-haertung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Nachfolgefassung statt Edit: neue Nummer, neues Laufverzeichnis, Kopf nennt die Vorgaengerin mit vollem Pfad und den Befund"
    - "Nicht-gefahren-Satz in Versalien im Kopf jeder ungemessenen Fassung, damit eine Rohdatei-freie Datei niemals fuer gemessen gehalten wird"
    - "Kopie statt Neuschrift: cp und danach genau benannte Stellen, weil ein neu getippter Text an hundert Stellen anders und an einer davon falsch waere"
    - "Ein Waechter je Fassung reicht nicht: einer haelt die Herkunft, einer die behobene Eigenschaft, sonst koennte ein Nachfolger auf sein Original zeigen und den Fix nicht tragen"

key-files:
  created:
    - docs/measurements/2026-09-nachfolgefassungen/skripte/92c-wechsel.sh
    - docs/measurements/2026-09-nachfolgefassungen/skripte/99d-filter-sortierung.sh
  modified:
    - backend/tests/test_measurement_scripts.py
    - backend/tests/test_public_artifacts.py

key-decisions:
  - "Der gescheiterten Registrierung faellt der Rueckgabewert 36 zu und keine neue Zahl. 36 traegt in 92b bereits den Fall, dass der Container nach der Registrierung auf einer fremden Abbildkennung laeuft; eine gescheiterte Registrierung bedeutet dasselbe, naemlich einen Stand, den der Baumhash nicht belegt hat. Eine einmal vergebene Zahl wird nicht umgehaengt (Entscheid 15-02)"
  - "Dem fehlenden Passwort in 99d faellt die 2 zu, die Zahl, die dieses Laufverzeichnis der fehlenden Pflichtangabe gibt (92b und ABBILD_DIGEST). Keine neue Zahl, keine dritte Form"
  - "Der Plan nennt 98c-sprachfaelle.sh als Vorbild fuer das Lesen der Passwortdatei. 98c fuehrt die Variable PWFILE, liest sie aber ausdruecklich NICHT mehr (Kopfkommentar dort). Uebernommen ist deshalb der NAME von 98c, wie das Abnahmekriterium es verlangt, und die LESEFORM von 95-spitze.sh, 96b-waechter.sh und 97-nebenlaeufigkeit.sh desselben Laufverzeichnisses, mit der Reihenfolge Umgebung zuerst und Datei danach nach dem Vorbild von 98b-sprachfaelle.sh"
  - "Das Passwort wandert in 99d in keine Shellvariable. Beide Quellen schreiben unmittelbar in das Feld unter WORK, weil eine Zuweisung an eine Variable und ein spaeteres printf zwei Zeilen waeren, die unter set -x den Wert zeigen. Das ist strenger als das Vorbild und billiger als die Diskussion darueber"
  - "Die beiden Baumhash-Werkzeuge bleiben im Laufverzeichnis der Anfahrt und wandern nicht mit. 92c erreicht sie ueber die neue Variable WERKZEUGE mit Vorgabe; ohne sie suchte 92c die zwei Dateien neben sich und braeche mit 36 ab, obwohl nichts fehlte als ein Pfad"
  - "DRIVEN_V12_FASSUNGEN bleibt bei sechs Eintraegen mit unveraenderten Pruefsummen. Ein siebter Eintrag wuerde eine Fassung einfrieren, die nie gefahren ist, und sie damit ins selbe Regal stellen wie die, die gefahren sind"

patterns-established:
  - "Eine Nachfolgefassung braucht zwei Waechter: Herkunft (Vorgaengerin mit vollem Pfad, Befund, Nicht-gefahren-Satz) und behobene Eigenschaft (Textprobe ueber die Zeilenfolge)"

requirements-completed: []
requirements-partial:
  - "A1: die beiden Werkzeugbefunde L-03 und L-04 haben ihre Nachfolgefassungen, statisch abgenommen. Die Wirkung ist NICHT nachgemessen, und das ist die dokumentierte Grenze dieser Auflage"

# Metrics
duration: 95 min
completed: 2026-09-21
---

# Phase 16 Plan 03: Die zwei Nachfolgefassungen der Auflage A1 Summary

Die zwei Werkzeugbefunde der Anfahrt haben ihre Nachfolgefassungen: `92c-wechsel.sh` bricht ab, wenn der `occ`-Aufruf der Phase B scheitert, statt mit 0 zu enden, und `99d-filter-sortierung.sh` liest das Passwort auch aus der Passwortdatei. Beide liegen in einem neuen Laufverzeichnis, beide nennen ihre Vorgaengerin mit vollem Pfad, und die sechs gefahrenen Fassungen sind byteweise unberührt.

## DIESE BEIDEN FASSUNGEN SIND NICHT NACHGEMESSEN

Das ist die dokumentierte Grenze der Auflage A1 und gehört an den Anfang.

Auf dieser Maschine gibt es keine POSIX-Shell mit Docker und keine Box; die
bezahlte Box der Phase 15 ist am 21.09.2026 abgebaut worden. Das
Abnahmekriterium der beiden Dateien war deshalb **Form, Prüfsumme und statische
Analyse**: Kopfform nach dem Muster der bestehenden Nachfolgefassungen,
Syntaxprüfung mit `sh -n`, die drei Zusagen des engen Kreises (kein Passwort auf
einer Kommandozeile, keine Maschinenform außerhalb von Kommentaren, kein
Wagenrücklaufzeichen) und vier neue Wächter über die behobenen Eigenschaften.
Keine dieser Prüfungen hat je einen Container gestartet, eine Registrierung
gefahren oder eine Seite geholt.

Was die beiden Fassungen wirklich bewirken, misst erst die nächste Anfahrt
(Pitfall 7). Neben ihnen liegt keine Rohdatei, und es wird auch keine geben, bis
jemand sie fährt. Der Satz steht in Versalien im Kopf jeder der beiden Dateien
(`DIESE FASSUNG IST NICHT GEFAHREN`), und ein Wächter je Fassung hält ihn dort
fest, damit er nicht beim nächsten Umbau verschwindet.

## Was gebaut wurde

### 92c-wechsel.sh, die Phase-B-Pipeline mit gepruefter Registrierung (L-03)

`docs/measurements/2026-09-nachfolgefassungen/skripte/92c-wechsel.sh`,
sha256 `60ee8ec710e7324ca1a82709924bf1ef8830f908b0fd4c36559f84d7886742d2`,
35.825 Byte. Entstanden als `cp` von
`docs/measurements/2026-09-v12-messung/skripte/92b-wechsel.sh`.

Der Befund: in 92b stand der Aufruf `occ app_api:app:register` in dem Block,
dessen Ausgabe über `tee` in die Rohdatei läuft. Der Rückgabewert einer Pipeline
gehört ihrem letzten Befehl, also `tee`, und `sh` kennt kein `pipefail`. Ein
gescheiterter Aufruf verließ deshalb nur die Subshell, die Verweigerungen
unterhalb der Pipeline fanden keine Arbeitsdatei vor, und das Werkzeug endete mit
0. Genau das ist im ersten Lauf der Anfahrt geschehen: Rückgabewert 0, ohne dass
die Registrierung stattgefunden hatte.

Die Änderung: der Aufruf schreibt in eine Datei unter `WORK` (`mktemp`, fällt mit
dem bestehenden `trap` weg), sein Rückgabewert wird unmittelbar danach in
`register_status` geprüft und bei ungleich null als Arbeitsdatei
`registrierung-fehlt` vermerkt, und erst danach läuft die Ausgabe durch den
Filter in die Rohdatei. Unterhalb der Pipeline steht die neue Verweigerung an
ihrem Platz in der Reihenfolge des Ablaufs, zwischen der zweiten Instanzzählung
und der Speichergrenze, mit **exit 36**.

Zwei neue Zeilen im Protokoll: `registrierung-rueckgabewert` und
`registrierung-gelungen`. Beide stehen im Kopf in der Liste der Zeilen, die
dieses Werkzeug schreibt, weil ein Bericht nach Namen greift.

### 99d-filter-sortierung.sh, das Passwort aus der Passwortdatei (L-04)

`docs/measurements/2026-09-nachfolgefassungen/skripte/99d-filter-sortierung.sh`,
sha256 `84f572b3aa4c51a18bd419cb4a379f6d62cae0f6f2d9d97d60d836d5089f12bb`,
34.205 Byte. Entstanden als `cp` von
`docs/measurements/2026-09-v12-messung/skripte/99c-filter-sortierung.sh`.

Der Befund ist kein Sicherheitsdefekt, sondern ein Bruch der Einheitlichkeit: die
Umgebung ist nach V14 die erlaubte Form und bleibt es, aber 99c kannte sie als
einzige Quelle, während die übrigen Werkzeuge desselben Laufverzeichnisses
daneben `PWFILE` lesen. Ein Lauf, der die Datei hinterlegt und die Variable nicht
gesetzt hatte, meldete sich still als niemand an, und die Anmeldeseite antwortet
schnell: im Protokoll stünden hübsche Zahlen für eine Messung, die nie
stattgefunden hat.

Die Änderung: `PWFILE` mit der Vorgabe der drei Nachbarwerkzeuge, Umgebung
zuerst und Datei danach, und ein leeres Feld nach beiden Quellen ist eine
Verweigerung mit **exit 2** und der Benutzung auf stderr, bevor die erste Anfrage
läuft. Der Wert wandert dabei in keine Shellvariable: beide Quellen schreiben
unmittelbar in `$WORK/pwfeld` (Modus 600, ohne abschließenden Zeilenumbruch),
damit auch eine Zeile unter `set -x` nichts hergibt.

### Vier Waechter und ein vierter Eintrag im engen Kreis

`backend/tests/test_measurement_scripts.py`:

- `SUCCESSOR_RUN_DIR` kommt als vierter Eintrag in `NARROW_SCOPE_DIRS`, mit
  Begründung im Kommentar und fortgeschriebenem Docstring von
  `scripts_of_this_run`: der Grund ist 99d selbst, dessen ganzer Gegenstand die
  Herkunft eines Passworts ist.
- `test_the_successor_of_the_image_switch_points_at_the_driven_fassung_and_lives_beside_it`
  und dasselbe für 99d: Vorgängerin mit vollem Pfad, Befund (L-03 bzw. L-04),
  anderes Verzeichnis als die Vorgängerin, Nicht-gefahren-Satz.
- `test_the_successor_of_the_image_switch_checks_the_occ_return_before_the_filter`:
  Textprobe über die Zeilenfolge nach dem Muster von
  `test_the_successor_checks_the_foreign_stock_before_the_first_case`. Aufruf vor
  Prüfung vor Filter vor Vermerk vor Verweigerung, die Aufrufzeile trägt kein
  Rohrzeichen, die Umleitung in die Datei steht da, und der Block der
  Verweigerung trägt `exit 36`.
- `test_the_successor_of_the_filter_sort_tool_reads_the_password_out_of_the_password_file`:
  der Pfadvariablenname ist der von 98c, die gefahrene Fassung 99c trägt ihn
  nachweislich nicht, die Umgebung steht vor der Datei, und das Feld wird zweimal
  auf Leere geprüft.

`DRIVEN_V12_FASSUNGEN` ist unverändert: sechs Einträge, sechs unveränderte
Prüfsummen, und ein Kommentar über den neuen Wächtern sagt ausdrücklich, warum
die zwei neuen Dateien dort nicht hineingehören.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] 92c fand die zwei Baumhash-Werkzeuge nicht**

- **Found during:** Task 1
- **Issue:** 92b ruft `sh "$SKRIPTE/40b-baumhash.sh"` und kopiert
  `$SKRIPTE/40b-baumhash.py` in den Container. `SKRIPTE` leitet sich aus dem Ort
  der Datei ab, und in einem neuen Laufverzeichnis liegen die beiden Werkzeuge
  nicht. 92c wäre mit 36 abgebrochen, obwohl nichts gefehlt hätte als ein Pfad.
  Die beiden Werkzeuge mitzukopieren war keine Option: sie sind selbst gefahrene
  Fassungen und bleiben, wo sie liegen.
- **Fix:** neue Variable `WERKZEUGE` mit Vorgabe auf das Laufverzeichnis der
  Anfahrt, in der Hausform dieser Dateien (Vorgabe mit Kommentar darüber), und
  eine eigene Begründung im Kopf.
- **Files modified:** `docs/measurements/2026-09-nachfolgefassungen/skripte/92c-wechsel.sh`
- **Commit:** bd10eeb

**2. [Rule 3 - Blocking issue] Das Geheimnis-Gate aus 16-02 wurde durch 99d rot**

- **Found during:** Task 3, volle Suite
- **Issue:** `test_public_artifacts.py` meldete 99d in der Familie
  `schluesselwort-mit-wert`. Der Treffer sitzt in der aus 99c wörtlich
  übernommenen Zeile `[ -n "${token:-}" ]`, also in einer POSIX-Vorgabe-Ersetzung
  ohne Wert. 99c selbst steht aus demselben Grund seit 16-02 auf der
  Ausnahmeliste.
- **Fix:** ein Ausnahmeeintrag für den neuen Pfad mit eigenem Grund, in der Form
  der Liste (Pfad plus Familie, kein einziger Wert). Die Zeile selbst wurde nicht
  angefasst, weil sie eine dritte Änderung an der Kopie gewesen wäre.
- **Files modified:** `backend/tests/test_public_artifacts.py`
- **Commit:** fc8afba

**3. [Rule 2 - Missing critical functionality] Der eigene Name der beiden Fassungen**

- **Found during:** Task 1 und Task 2
- **Issue:** Die Kopien hätten `92b-wechsel.txt`, `92b-info-box.xml`,
  `99c-filter-sortierung.txt` geschrieben und sich in jeder Fehlermeldung
  `92b-wechsel:` beziehungsweise `99c-filter-sortierung:` genannt. Eine Rohdatei
  hätte damit ein Werkzeug genannt, das sie nicht geschrieben hat.
- **Fix:** mechanische Umbenennung der Selbstbezüge im Rumpf, genau die
  Umbenennung, die 92b gegenüber 92-wechsel.sh vorgenommen hat. Im Kopf jeder
  Datei als eigener Absatz benannt, damit sie nicht als dritte Sachänderung
  gelesen wird.
- **Files modified:** beide neuen Dateien
- **Commits:** bd10eeb, 3bc7925

### Abweichung vom Plan-Wortlaut, ohne Fix

**98c-sprachfaelle.sh ist nicht das Vorbild, das der Plan beschreibt.** Der Plan
verlangt für 99d die Anmeldung "genau nach dem Vorbild in `98c-sprachfaelle.sh`
desselben Laufverzeichnisses: derselbe Variablenname für den Pfad, dieselbe
Prüfung auf Existenz und Lesbarkeit, derselbe Abbruchcode bei Fehlen". 98c
**führt** die Variable `PWFILE`, **liest** sie aber ausdrücklich nicht mehr; ihr
Kopfkommentar sagt das wörtlich ("Diese Fassung liest sie NICHT mehr: die
Vorprüfung fragt keine Route und braucht deshalb kein zweites Konto-Passwort").
Ein Abbruchcode für ein fehlendes Passwort existiert dort nicht.

Umgesetzt ist deshalb: der **Name** von 98c, wie das Abnahmekriterium ihn
ausdrücklich fordert, und die **Leseform** der drei Werkzeuge desselben
Laufverzeichnisses, die sie wirklich lesen (`95-spitze.sh`, `96b-waechter.sh`,
`97-nebenlaeufigkeit.sh`, alle drei mit derselben Vorgabe), plus die Reihenfolge
Umgebung-vor-Datei von `98b-sprachfaelle.sh`, dem einzigen Werkzeug im
Repositorium, das beide Quellen führt. Der Abbruchcode ist die 2 dieses
Laufverzeichnisses und keine neue Zahl. Das steht so im Kopf von 99d.

## Verification

| Prüfung | Ergebnis |
|---|---|
| `sh -n` über beide neuen Dateien | grün |
| Kein Wagenrücklaufzeichen, `#!/bin/sh` als erste Zeile | grün |
| `git diff --stat` nennt weder 92b noch 99c | leer, beide byteweise unberührt |
| `DRIVEN_V12_FASSUNGEN` | unverändert, 6 Einträge, 6 Prüfsummen |
| `pytest tests/test_measurement_scripts.py -q -k "92c or 99d or successor"` | 25 passed |
| `ruff check tests`, `ruff format --check tests` | grün |
| `PYRIGHT_PYTHON_FORCE_VERSION=latest pyright` | 0 errors, 0 warnings |
| `vulture src tests --min-confidence 80` | grün |
| Volle Suite vorher | 2444 passed, 15 skipped |
| Volle Suite nachher | **2458 passed, 15 skipped** |

Die Skipzahl ist unverändert. Die 14 neuen Fälle sind 4 neue Wächter plus 10
parametrisierte Fälle, die der weite und der enge Kreis über die beiden neuen
Dateien ziehen (je 2 im weiten Kreis, je 3 im engen).

## Known Stubs

Keine.

## Threat Flags

Keine neue Oberfläche außerhalb des `<threat_model>` des Plans. T-16-09
(gefahrene Fassung wird entwertet), T-16-10 (Passwort auf einer Kommandozeile)
und T-16-11 (nicht gefahrene Fassung wird für gemessen gehalten) sind je mit dem
im Plan vorgesehenen Mittel behandelt und je durch einen Fall abgesichert.
T-16-SC ist gegenstandslos: keine neue Abhängigkeit, kein Paketinstall.

## Was offen bleibt

- Die Wirkung beider Fixe ist ungemessen. Sie gehört an den Anfang des
  Runbook-Abschnitts der nächsten Anfahrt.
- Die vier übrigen Werkzeugbefunde der Anfahrt (L-05 bis L-08) sind von diesem
  Plan nicht berührt.
- Das Laufverzeichnis `2026-09-nachfolgefassungen` trägt kein `00-ablauf.md`. Die
  beiden anderen Laufverzeichnisse haben eines; hier wäre es die Beschreibung
  eines Laufs, den es nicht gibt. Sollte die nächste Anfahrt aus diesem
  Verzeichnis fahren, entsteht es dort mit den Zahlen jenes Laufs.

## Self-Check: PASSED

Beide neuen Dateien, beide geänderten Gate-Dateien und diese SUMMARY liegen auf
der Platte; die drei Commits bd10eeb, 3bc7925 und fc8afba stehen im Log.
