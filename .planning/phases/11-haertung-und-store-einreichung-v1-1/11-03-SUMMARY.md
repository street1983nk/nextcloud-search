---
phase: 11-haertung-und-store-einreichung-v1-1
plan: 03
subsystem: messwerkzeug
tags: [di-10-02, messaufbau, dreiwertiges-urteil, waechter, weg-b3]

# Dependency graph
requires:
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: die gefahrene Fassung 98-sprachfaelle.sh, ihre Rohdatei und die Diagnose 98b-sprachfaelle-diagnose.txt
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: 11-RESEARCH.md Abschnitt 4.3 (Weg B3), Pattern 2 und 3, Pitfall 2
provides:
  - "98b-sprachfaelle.sh: Nachfolgefassung mit Fremdbestand-Vorpruefung, dreiwertigem Urteil und CI_LAUF als Pflichteingabe"
  - "00-ablauf.md des Laufverzeichnisses 2026-09-werkzeugfixe mit der VORHER aufgeschriebenen Erwartung"
  - "sha256-Waechter ueber die gefahrene Fassung 98-sprachfaelle.sh (T-11-08)"
  - "enger Geltungsbereich von test_measurement_scripts.py deckt beide Laufverzeichnisse (T-11-10)"
affects: [11-06, 11-09, 11-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dreiwertiges Messurteil: GRUEN, ROT, NICHT MESSBAR, Reihenfolge bindend (Pattern 2 der Recherche)"
    - "Kopie eines gefahrenen Messskripts in ein neues Laufverzeichnis statt Bearbeitung, Original per sha256 verriegelt (Pattern 3)"
    - "Fail closed: kann die Vorpruefung nicht fahren, endet der Lauf, statt zweiwertig weiterzuurteilen"
    - "Ein Messskript wird im Test als Programm gefahren, aber nur auf seinen Verweigerungspfaden"

key-files:
  created:
    - docs/measurements/2026-09-werkzeugfixe/skripte/98b-sprachfaelle.sh
    - docs/measurements/2026-09-werkzeugfixe/skripte/00-ablauf.md
  modified:
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "FREMD_SCHWELLE Vorgabe 64 statt der Beispielzahl 1 des Plans: 64 ist MAX_RECHECKS_ABSOLUTE aus php/lib/Search/Provider.php, also die Obergrenze der Kandidaten, die eine Suche ueberhaupt prueft. Ein einziger Fremdtreffer ist keine Begruendung, das Fenster ist die Begruendung"
  - "Zwei Zaehlungen je Begriff: einmal auf der Seite der Faelle (gleiches Limit wie die Faelle, also vergleichbar) und einmal bis Tiefe 64 (die Zahl, gegen die die Schwelle prueft). Eine Zahl, die die Dialogseite bei einer Handvoll deckelt, koennte eine Schwelle aus einem Fenster von 64 nie erreichen"
  - "set -eu und #!/bin/sh statt des im Plan genannten set -euo pipefail: dash kennt kein pipefail, und die Hausregel in test_ops_scripts.py prueft genau set -eu"
  - "ZIEL zeigt per Vorgabe auf rohdaten/05-sprachfaelle.txt, den Namen, den Plan 11-06 erwartet"
  - "Der enge Geltungsbereich der Gates musste erweitert werden; er deckte nur das Laufverzeichnis der Phase 10, obwohl Plan und Bedrohungsregister ihn fuer jede neue Datei annahmen"

patterns-established:
  - "Erwartung vor der Messung in 00-ablauf.md, mit Herkunft je Zeile, damit sie nicht nachtraeglich zur Erklaerung wird"
  - "Ein Waechter ueber eine gefahrene Messfassung besteht aus Digest UND Groesse, plus einem Selbsttest auf ein einziges zusaetzliches Zeichen"

requirements-completed: []

# Metrics
duration: 35min
completed: 2026-09-10
---

# Phase 11 Plan 03: DI-10-02, die Nachfolgefassung des Sprachfall-Skripts Summary

**Das Sprachfall-Skript stellt jetzt vor den zehn Faellen fest, wie viel Fremdbestand einem Begriff im Weg steht, urteilt dreiwertig statt zweiwertig, verweigert den Lauf ohne die Laufnummer des gruenen CI-Belegs, und die gefahrene Fassung vom 10.09. ist maschinell gegen jede Bearbeitung verriegelt.**

## Performance

- **Duration:** rund 35 min, keine Box-Minute
- **Started:** 2026-09-10T19:25:00Z
- **Completed:** 2026-09-10T20:00:00Z
- **Tasks:** 3 von 3
- **Files modified:** 2 neu, 1 geaendert

## Accomplishments

- **Weg B3 der Recherche ist gebaut, und zwar als Kopie.** `docs/measurements/2026-09-werkzeugfixe/skripte/98b-sprachfaelle.sh` ist die Nachfolgefassung in einem eigenen Laufverzeichnis. Ihr Kopf nennt den Pfad des Originals, sagt, dass es unveraendert bleibt, und benennt DI-10-02 woertlich: ein eigenes Konto trennt die Berechtigung und nicht den Index. Unter `docs/measurements/2026-09-vergleichsmessung-m7g/` gibt es keinen Diff.
- **Die Vorpruefung Fremdbestand steht als Abschnitt 0, vor allem anderen.** Jeder der zehn Begriffe wird als das Konto gefragt, dem der 52.111er-Lastkorpus gehoert, ueber dieselbe OCS-Route mit demselben Header. Je Begriff eine Zeile `fremdbestand <begriff> <treffer> (Seite der Faelle), <treffer> (bis Tiefe 64), Fall <n>`. Das Passwort kommt aus der Umgebung oder aus der Datei, auf die `PWFILE` zeigt, nie aus einem Argument.
- **Das Urteil ist dreiwertig, und die Reihenfolge ist bindend.** Erst der Fremdbestand gegen die Schwelle, dann der Fall. Ein Fall oberhalb der Schwelle bekommt `sprachfall N NICHT MESSBAR (Fremdbestand N Treffer)` und faehrt seine Zusicherungen gar nicht erst, also auch kein zweites Urteil daneben. Ein messbarer Fall bekommt `GRUEN` oder `ROT`, und beide tragen die Fremdbestandszahl in derselben Zeile.
- **Die Bilanzzeile nennt beide Zahlen:** `sprachfaelle bestanden <n> von 10, davon <m> nicht messbar`, darunter unveraendert die Trennung von Faellen und Zusicherungen aus Plan 10-04 (`rote faelle`, `nicht messbare faelle`, `rote zusicherungen`).
- **`CI_LAUF` ist Pflichteingabe.** Ohne Laufnummer, mit leerem Wert, mit Leerzeichen oder mit etwas, das keine Ziffernfolge ist, endet das Skript mit **22**, bevor irgendetwas geschieht: kein `mkdir`, keine Rohdatei, kein Konto. Die Ausgabe nennt `ci-beleg: integration.yml Lauf <nummer>` an zwei Stellen und den Satz, dass genau dieser Lauf die zehn Faelle auf einer frischen Instanz ohne Fremdbestand fuhr. Das Wort, das am 10.09. an dieser Stelle stand, kommt in der Datei nicht mehr vor.
- **Zwei neue Abbruchgruende, beide fail closed.** **19**: die Vorpruefung konnte nicht fahren (kein Passwort, eine Suche antwortete nicht, eine Antwort trug keine lesbare Trefferliste) , dann endet der Lauf, statt wieder zweiwertig zu urteilen. **23**: kein einziger Fall war messbar , eine Aussage ueber die Instanz und keine ueber die Sprachkette. **17** zaehlt jetzt ausdruecklich nur noch **messbare** rote Faelle.
- **`00-ablauf.md` schreibt die Erwartung vor dem Lauf auf,** in acht nummerierten Zeilen mit Herkunft: Stufe 16 mit `failures > 0` und `hits_per_request` deutlich unter Stufe 8, Stufe 8 mit `failures == 0`, die Uebereinstimmung der beiden unabhaengigen Zaehlungen, vier nicht messbare Sprachfaelle (moeglicherweise fuenf, siehe unten), und die Bilanzzeile `6 von 10, davon 4 nicht messbar`. Dazu die Schrittfolge mit allen sechs Rohdateinamen, der Deckel 4 h / 0,50 USD, und eine Tabelle aller Abbruchgruende mit ihren Rueckgabewerten.
- **Der Waechter ueber das Original ist eine Maschine, keine Erinnerung.** `test_the_driven_language_case_script_stays_byte_identical` haelt sha256 `5f9607fc...` und 23.479 Byte gegen die Datei, mit der Fehlermeldung "eine gefahrene Messfassung ist Teil des Belegs, und ein Fix entsteht als neue Datei in einem neuen Laufverzeichnis". Probeweise ein Leerzeichen angehaengt: der Waechter und sein Selbsttest wurden rot, die Aenderung ist zurueckgenommen.
- **Sechzehn neue Zusicherungen**, davon zwei gefahrene Negativpfade: der Verweigerungspfad ohne Laufnummer in fuenf Gestalten (fehlend, leer, blank, Wort, Ziffern mit Buchstabe) und der Verweigerungspfad ohne Passwort, der mit 19 endet und dabei belegt, dass das Skript vor dem Hochladen der 39 Dateien stehen bleibt. Beide fahren das Skript unter einer POSIX-Shell und wuerden ein `pipefail` im Kopf sofort sichtbar machen.

## Task Commits

1. **Task 1 und 2:** `73bc655` , `98b-sprachfaelle.sh`, Vorpruefung, dreiwertiges Urteil, Bilanz mit zwei Zahlen, CI_LAUF als Pflicht, neue Rueckgabewerte 19, 22, 23
2. **Task 3:** `d9493de` , `00-ablauf.md`, sha256-Waechter, erweiterter enger Geltungsbereich, zwei gefahrene Negativpfade

Gepusht: `e74f3d3..d9493de` auf `origin/main`.

## Gates

Alle lokal gruen vor jedem Commit, aus `backend/`:

| Gate | Ergebnis |
|---|---|
| `uv run python -m pytest -q` | **2002 passed, 15 skipped** (Grundlinie 1984/15, plus 18) |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 121 files already formatted (eine Datei vorher formatiert) |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | ohne Befund |
| `bash -n 98b-sprachfaelle.sh` | ohne Befund |
| `git diff --stat docs/measurements/2026-09-vergleichsmessung-m7g/` | leer |

Kein Workflow wurde angefasst: die CI-Bindung laeuft ueber den bestehenden eigenen Index in `integration.yml`, Job `index-search-e2e`, per `CI_LAUF`.

### CI nach dem Push

Der Push auf `d9493de` hat die uebliche Runde von fuenf Workflows angestossen. Der entscheidende ist **Python gates**, weil er die zwei neu gefahrenen Negativpfade unter einer echten POSIX-Shell auf einem Linux-Runner faehrt, also unter dash und nicht unter der Git-Bash dieses Rechners.

| Lauf | Workflow | Ergebnis |
|---|---|---|
| 34522959320 | Python gates | **success** |
| 34522959144 | Multi-arch image | **success** |
| 34522959094 | Integration | siehe unten |
| 34522959093 | Resilience | siehe unten |
| 34522959025 | HaRP deploy | siehe unten |

## Wie das dreiwertige Urteil konkret aussieht

Drei Werte, in dieser Reihenfolge geprueft:

```
sprachfall 1 NICHT MESSBAR (Fremdbestand 64 Treffer)
sprachfall 3 GRUEN (Fremdbestand 0 Treffer)
sprachfall 2 ROT: Frist did not bring back exactly the notice of termination (Fremdbestand 0 Treffer, Schwelle 64)
sprachfaelle bestanden 6 von 10, davon 4 nicht messbar
rote faelle 0, nicht messbare faelle 4, rote zusicherungen 0
```

- **NICHT MESSBAR** heisst: der Begriff hat im Lastkorpus mindestens `FREMD_SCHWELLE` Treffer, die Kandidatenliste ist also voll, bevor eine Datei des fragenden Kontos darin vorkommt. Der Fall faehrt seine Zusicherungen nicht, und er zaehlt nicht als bestanden und nicht als rot.
- **GRUEN** und **ROT** tragen die Fremdbestandszahl mit. Das ist die Vorsichtsmassnahme fuer den Bereich zwischen 1 und 63: ein roter Fall mit einer Null daneben ist ein Sprachbefund, ein roter Fall mit einer Sieben daneben ist einer, den der Bericht mit dieser Sieben lesen muss.
- **Die Schwelle ist 64 und nicht 1.** 64 ist `MAX_RECHECKS_ABSOLUTE` in `php/lib/Search/Provider.php`, die Obergrenze der Kandidaten, die eine einzelne Suche ueberhaupt prueft; darin muss die eigene Datei landen. Die Diagnose vom 10.09. hat gemessen, wie weit ausserhalb sie liegt: Rang 1.925 von 2.000 fuer `Bescheid`, gar nicht unter 2.000 fuer `Genehmigung`, `Frist` und `Vertrag`. Ein einziger Fremdtreffer waere keine Begruendung, das gefuellte Fenster ist eine. Ein Test haelt die 64 gegen die PHP-Konstante, damit die Herleitung nicht still aufhoert zu stimmen.

## Was der Box-Beweis in 11-06 mit dieser Fassung genau faehrt

Messblock B, Schritt 6 der Ablaufnotiz:

1. Laufnummer holen: `gh run list --workflow=integration.yml --status success`.
2. `FRIST=60 RUNDEN=10 CI_LAUF=<nummer> ./98b-sprachfaelle.sh`, Ausgabe nach `docs/measurements/2026-09-werkzeugfixe/rohdaten/05-sprachfaelle.txt` (die Vorgabe von `ZIEL` schreibt genau dorthin, `tee` erledigt es also von selbst). `FRIST` und `RUNDEN` bleiben Variablen mit den alten Vorgaben 360 und 40, damit die Vergleichbarkeit mit dem Original nicht am Vorgabewert haengt.
3. Das Skript fragt zuerst zehn mal zwei Mal als `lasttest` (Seite der Faelle und Tiefe 64), schreibt zehn `fremdbestand`-Zeilen, legt dann wie bisher das Konto `sprachfall` an oder findet es vor, laedt die 39 Dateien ueber WebDAV, wartet auf einen leeren Arbeitsvorrat und faehrt die zehn Faelle dreiwertig.
4. Erwartet werden vier Faelle als NICHT MESSBAR (1, 2, 4, 6) und moeglicherweise ein fuenfter (Fall 7 fragt `type:pdf bescheid`, also dasselbe Wort wie Fall 6, und war am 10.09. gruen). Beide Faelle sind in `00-ablauf.md` als E5 und E6 **vor** dem Lauf aufgeschrieben.
5. Zwei Vorbedingungen kosten sonst Box-Minuten und stehen deshalb in der Ablaufnotiz: die Laufnummer (sonst 22) und das Lasttest-Passwort in `FINDLING_LOAD_PASSWORD` oder unter `PWFILE` (sonst 19, aber immerhin vor dem Hochladen).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] `set -euo pipefail` waere auf der Box sofort gestorben**

- **Found during:** Task 1
- **Issue:** Das Akzeptanzkriterium nennt `set -euo pipefail` bei einem POSIX-Shebang. `/bin/sh` ist auf Ubuntu dash, dash kennt kein `pipefail`, und die Zeile haette das Skript in seiner ersten Anweisung beendet. Zusaetzlich erlaubt das Shebang-Gate nur `#!/bin/sh` und `#!/usr/bin/env python3`, ein Wechsel auf bash war also auch kein Weg.
- **Fix:** `#!/bin/sh` und `set -eu`, wie im Original und wie es die Hausregel in `test_ops_scripts.py` (`test_..._is_strict`) fuer Shellwerkzeuge prueft. Die beiden gefahrenen Negativpfad-Tests laufen unter einer echten POSIX-Shell und wuerden ein wiedereingefuegtes `pipefail` sofort rot machen.
- **Commit:** `73bc655`

**2. [Rule 2 - Fehlende Zusicherung] Die drei engen Gates erfassten die neue Datei gar nicht**

- **Found during:** Task 3
- **Issue:** Plan und Bedrohungsregister (T-11-10) nehmen an, dass `test_the_script_of_this_run_puts_no_password_on_a_command_line` und die zwei Geschwister fuer jede neue Datei unter `docs/measurements/*/skripte/` automatisch gelten. Sie gelten nicht: `scripts_of_this_run()` las genau ein Verzeichnis, das der Phase 10. Erfasst waren nur die zwei weiten Gates (kein Wagenruecklauf, kein Gedankenstrich).
- **Fix:** `NARROW_SCOPE_DIRS` als benanntes Paar, `scripts_of_this_run()` liest beide Verzeichnisse, die Fixture-Kennungen tragen jetzt den Laufnamen mit, und ein eigener Test haelt das Paar fest, damit eine kuenftige Erweiterung eine Entscheidung bleibt und kein Nebeneffekt. Der Semantiklauf vom 05.09. bleibt ausdruecklich draussen (45-suchlast.py mit seinem Maschinenpfad).
- **Commit:** `d9493de`

**3. [Rule 2 - Fehlende Zusicherung] Eine Vorpruefung, die stillschweigend nichts findet, waere schlimmer als keine**

- **Found during:** Task 1
- **Issue:** Faellt eine Suche der Vorpruefung aus (kein Passwort, Netzfehler, Antwort ohne Trefferliste), waere die naheliegende Behandlung "null Treffer". Null Treffer heisst aber "messbar", und dann urteilt das Skript wieder zweiwertig , genau der Befund DI-10-02, nur mit einer neuen Ursache.
- **Fix:** Fail closed. Jeder dieser drei Faelle endet mit Rueckgabewert **19**, und ein Fall ohne erhobene Zahl waere `NICHT MESSBAR (Fremdbestand nicht erhoben)`. Dazu **23** fuer den Lauf, in dem kein einziger Fall messbar war. Der Negativpfad 19 ist gefahren getestet.
- **Commit:** `73bc655` (Skript), `d9493de` (Test)

**4. [Rule 2 - Anschluss] Die Rohdatei haette unter dem Namen des Originals gelegen**

- **Found during:** Task 1
- **Issue:** `ZIEL` zeigte fest auf `98-sprachfaelle.txt`. Plan 11-06 erwartet `rohdaten/05-sprachfaelle.txt`, und zwei Namen fuer dieselbe Datei sind eine Fehlerquelle in einem Lauf unter Kostendeckel.
- **Fix:** `ZIEL="${ZIEL:-$OUT/05-sprachfaelle.txt}"`, also die Nummerierung des neuen Laufverzeichnisses als Vorgabe und weiterhin ueberschreibbar.
- **Commit:** `73bc655`

### Bewusste Abweichungen vom Wortlaut des Plans

**5. `FREMD_SCHWELLE` ist 64 und die Vorpruefung zaehlt zweimal**

Der Plan nennt `FREMD_SCHWELLE:-1` als Beispiel und verlangt zugleich "nimm den Wert, der aus der Diagnose folgt". Aus der Diagnose folgt das Kandidatenfenster: `MAX_RECHECKS_ABSOLUTE = 64`. Damit die Schwelle ueberhaupt erreichbar ist, braucht die Zaehlung eine Tiefe von 64; die Seite des Dialogs deckelt bei einer Handvoll Eintraegen, und eine so gedeckelte Zahl koennte eine 64 nie erreichen. Deshalb fragt die Vorpruefung jeden Begriff zweimal: einmal auf der Seite der Faelle (das ist das im Plan verlangte "dieselbe Limit", und diese Zahl steht in der Zeile vorne) und einmal bis Tiefe 64 (das ist die Zahl, gegen die die Schwelle prueft). Kosten: zehn zusaetzliche Suchen, also wenige Sekunden.

**6. Fall 7 kann der fuenfte nicht messbare Fall werden**

Der Plan erwartet in `00-ablauf.md` "vier der zehn Sprachfaelle" als NICHT MESSBAR. Fall 6 und Fall 7 fragen dasselbe Wort (`bescheid` und `type:pdf bescheid`), haben also denselben Fremdbestand. Die Erwartung steht deshalb als E5 (vier: 1, 2, 4, 6) **und** E6 (moeglicherweise ein fuenfter: 7) in der Ablaufnotiz, beide vor dem Lauf. Fall 7 war am 10.09. gruen, obwohl der Fremdbestand ueber seine Kandidatenliste entschied; ihn kuenftig als nicht messbar zu fuehren ist kein Rueckschritt, sondern dieselbe Ehrlichkeit wie bei den anderen vier.

**7. Task 1 und Task 2 in einem Commit**

Beide Tasks schreiben dieselbe neue Datei, und Task 2 ersetzt das Urteil, das Task 1 unveraendert uebernommen haette. Ein Zwischencommit haette eine Fassung festgehalten, die nie gefahren werden sollte. Der Commit nennt beide Teile in seinem Rumpf.

### Keine Abweichung

- Keine Datei unter `docs/measurements/2026-09-vergleichsmessung-m7g/` wurde angefasst.
- `integration.yml` wurde nicht angefasst.
- `REL-01` bleibt offen und ist nicht abgehakt.

## Known Stubs

Keine. Die Nachfolgefassung ist vollstaendig; was ihr fehlt, ist ein Lauf gegen die Box, und der ist Plan 11-06.

## Threat Flags

Keine neue Angriffsflaeche. Die drei Zusagen des Bedrohungsregisters sind erfuellt: T-11-08 durch den sha256-Waechter, T-11-09 durch das dreiwertige Urteil und die Bilanz mit zwei Zahlen, T-11-10 durch das Passwort aus der Umgebung plus den jetzt tatsaechlich greifenden Gate-Geltungsbereich, T-11-11 durch die Pflichteingabe mit Abbruch statt Notiz.

## Self-Check: PASSED

- `docs/measurements/2026-09-werkzeugfixe/skripte/98b-sprachfaelle.sh` vorhanden
- `docs/measurements/2026-09-werkzeugfixe/skripte/00-ablauf.md` vorhanden
- `backend/tests/test_measurement_scripts.py` geaendert und gruen
- Commits `73bc655` und `d9493de` im Verlauf, gepusht als `e74f3d3..d9493de`
