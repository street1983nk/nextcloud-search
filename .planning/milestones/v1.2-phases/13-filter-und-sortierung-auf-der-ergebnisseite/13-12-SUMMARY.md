---
phase: 13-filter-und-sortierung-auf-der-ergebnisseite
plan: 12
subsystem: ci
tags: [integration, paritaet, filter, sortierung, rechtegrenze, testregister, filt-05]

requires:
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 09
    provides: "die Ergebnisseite versteht types und sort in der Adresse und schreibt die Trefferzeilen weiterhin als findling-hit-<n>"
  - phase: 09-eigene-ergebnisseite
    plan: 06
    provides: "ask_page im Job search-parity und die dritte Frage jeder Vergleichsrunde"
provides:
  - "ask_page nimmt einen vierten, optionalen Parameter: weitere Adressparameter der Ergebnisseite"
  - "compare reicht ihn als sechstes Argument durch, die bestehenden Aufrufe bleiben byteweise gleich"
  - "Szenario 11 (types=text) und 12 (sort=newest): mengenneutral, beide Richtungen scharf, --expect-min unveraendert bei 3"
  - "Szenario 13 (types=images): direkte Messung der Wegnahme plus eine verneinte Frage fuer die extra-Richtung, gehalten von einer Kontrollfrage"
  - "docs/testing.md: zehn Registerzeilen fuer die Gates der Phase und ein Absatz zur Arbeitsteilung"
affects: [13-13]

tech-stack:
  added: []
  patterns:
    - "Ein optionales letztes Argument erweitert eine Vergleichsfunktion, ohne einen einzigen bestehenden Aufruf anzufassen: mit ${6:-} bleibt jede aeltere Zeile im Log wie zuvor"
    - "Eine Frage, die der symmetrische Vergleich nicht tragen kann, wird daneben gemessen und nicht in das Vergleichswerkzeug hineinverhandelt (dasselbe Muster wie content_hits in Szenario 8)"
    - "Ein Waechter, dessen Zaehlung in einer Kommandosubstitution gelesen wird, braucht eine eigene Funktion: ein exit in einer Substitution verlaesst die Subshell und nicht den Schritt"

key-files:
  created: []
  modified:
    - .github/workflows/integration.yml
    - docs/testing.md

key-decisions:
  - "Das dritte Szenario des Plans ist so, wie der Plan es beschreibt, nicht ausdrueckbar: der Filter erreicht nur die Seite und keine der beiden OCS-Routen, also meldet parity_diff bei einem wegnehmenden Filter zu Recht page-missing. Die Wegnahme wird deshalb direkt gemessen, scripts/ci/parity_diff.py bleibt unangetastet"
  - "Die Kontrollfrage des dritten Szenarios laeuft unter types=text und nicht unter types=images: unter einem wegnehmenden Filter wuerde die Seite des Kollegen aus demselben Grund von seinem Dialog abweichen"
  - "Die Logzeile von Szenario 10 sagte 'of ten' und war nach diesem Plan falsch; eine falsche Zahl im CI-Log ist ein Befund und keine Formalie"
  - "Jedes der sechs Oberflaechen-Gates bekommt eine eigene Registerzeile statt einer Sammelzeile: sie verhindern sechs verschiedene Dinge, und der Satz 'was es nicht beweist' ist bei jedem ein anderer"

patterns-established:
  - "Was ein Gate nicht beweist, wird im Register aus dem Docstring des Gates uebernommen und nicht neu formuliert: zwei Fassungen desselben Vorbehalts driften auseinander, und die im Register ist die, die zitiert wird"

requirements-completed: []  # FILT-05 traegt 13-13, die Abnahme steht aus

duration: 21min
completed: 2026-09-17
---

# Phase 13 Plan 12: Paritaetsszenarien fuer Filter und Sortierung Summary

**Der Paritaetsjob fragt die Ergebnisseite jetzt auch mit Typfilter und mit Sortierung, mit denselben Schwellwerten und in beiden Richtungen, und das dritte, wegnehmende Szenario zeigt, dass es diese Form gar nicht geben konnte: der Filter erreicht nur die Seite und keine der beiden OCS-Routen, also wird die Wegnahme daneben gemessen statt in das Vergleichswerkzeug hineinverhandelt.**

## Performance

- **Duration:** 21 min
- **Tasks:** 2
- **Commits:** 2

## Was gebaut wurde

### Task 1: Drei Paritaetsszenarien (`efa44a9`)

`ask_page` nimmt ein viertes, optionales Argument: weitere Adressparameter der
Ergebnisseite in Drahtform, etwa `types=text` oder `types=text&sort=newest`. Sie
werden an die Adresse gehaengt, sonst bewegt sich an der Funktion nichts, und
die Antwort wird weiterhin aus den Zeilen-IDs `findling-hit-<n>` gelesen. Die
Adresse wird nur bei nichtleerem Argument um `?` plus Parameter ergaenzt; `curl
-G` haengt seine eigene kodierte Abfrage dann mit `&` an, also muss keine der
beiden Haelften von der anderen wissen.

`compare` reicht das als sechstes Argument durch (`"${6:-}"`). Jeder bestehende
Aufruf mit fuenf Argumenten erzeugt damit exakt dieselben drei Anfragen wie
zuvor, was lokal mit gestubbtem `curl` nachgefahren wurde (siehe Verification).

Drei neue Schritte nach Szenario 10, weil sie weder Mitgliedschaft noch Freigabe
noch Datei aendern und deshalb nur gestoert werden koennen, nie selbst stoeren:

1. **Szenario 11, `types=text`.** Alle Markerdateien des Fixtures sind `.txt`,
   und die Gruppe `text` in `TYPE_GROUPS` (`backend/src/findling/query/
   rewrite.py`) fuehrt `txt`, also muss die eingeengte Seite dieselbe Menge
   beantworten wie der uneingeengte Dialog. Beide Richtungen bleiben scharf,
   `--expect-min` bleibt bei 3 wie im ungefilterten Szenario 1.
2. **Szenario 12, `sort=newest`.** Nicht Szenario 11 mit anderem Parameter:
   unter einem Sortiermodus betritt `candidates()` das Fusionsfenster gar nicht
   und antwortet aus `_sorted_round`, das den Index in Datumsordnung laeuft und
   den Rechte-Vorfilter `_permit()` in einer eigenen Schleife ruft. Zwei Zweige,
   zwei Aufrufe des Vorfilters, und nur eine Frage unter Sortierung erreicht den
   zweiten. Die Menge bewegt sich nicht, nur ihre Reihenfolge.
3. **Szenario 13, `types=images`.** Siehe Befund unten. Gemessen wird in drei
   Teilen: die Wegnahme direkt (drei Trefferzeilen ohne, keine mit dem Filter,
   und die leere Antwort muss der Leerzustand der Seite sein und nicht ihr
   Fehlerblock), die `extra`-Richtung ueber eine verneinte Frage mit
   `--expect-min 0`, und eine Kontrollfrage im selben Moment mit drei Treffern,
   die diese Null ehrlich haelt.

Jeder der drei Schritte traegt einen Kommentar, der sagt, was er beweist und was
nicht. `scripts/ci/parity_diff.py` und `backend/tests/test_parity_diff.py` sind
unveraendert, mit leerem Diff nachgewiesen.

### Task 2: Das Testregister zieht nach (`53b24e5`)

Neuer Abschnitt in `docs/testing.md`, in Form und Spaltenschnitt der bestehenden
Phasenabschnitte: zehn Registerzeilen, je mit "was es verhindert" und "was es
nicht beweist".

- eine Zeile fuer `test_search_fields_lockstep.py` (13-03),
- sechs Zeilen fuer die sechs Oberflaechen-Gates aus 13-10, einzeln und nicht
  gesammelt, weil sie sechs verschiedene Dinge verhindern,
- drei Zeilen fuer die drei neuen Paritaetsszenarien.

Die Saetze in der dritten Spalte sind aus den Docstrings der Gates uebernommen
und nicht neu formuliert. Darunter steht der Absatz zur Arbeitsteilung: die
Rechtegrenze halten `test_php_acl_boundary.py` und `test_php_trust_boundary.py`,
beide in dieser Phase unberuehrt (zuletzt in 09-03 angefasst, per `git log`
geprueft); die Paritaetsszenarien belegen die Wirkung gegen eine echte
Nextcloud; die Oberflaechen-Gates sagen zu Rechten gar nichts. Keines ersetzt
eines der anderen.

Keine Zahl, kein Suchbegriff und kein Pfad einer realen Instanz in den neuen
Zeilen.

## Deviations from Plan

### Befund: das dritte Szenario ist in der geplanten Form nicht ausdrueckbar

Der Plan beschreibt Szenario 3 so: `types=images` auf dem `.txt`-Fixture, "die
erwartete Findling-Menge ist leer, `--expect-min 0` fuer diese Menge, und der
Lauf belegt allein die `extra`-Richtung". Am realen Baum geht das nicht auf, und
der Plan hat den Fall selbst vorgesehen ("ist das ein Befund fuer die SUMMARY und
kein Grund, die Rot-Faehigkeit des Werkzeugs anzufassen").

Der Grund in einem Satz: **der Filter erreicht nur die Seite.** `ask()` fragt die
beiden OCS-Provider, und weder `providers/files/search` noch
`providers/findling/search` kennt `types` oder `sort`; nur `ask_page` traegt die
Parameter. Unter `types=images` antwortet die Seite also mit nichts, waehrend der
Suchdialog weiterhin drei Dateien zeigt, und `compare_page` meldet die Differenz
als `page-missing`. Dieses Urteil ist richtig: die zwei Wege in dieselbe Suche
haben wirklich zwei verschiedene Mengen beantwortet. Ein `--expect-min 0` aendert
daran nichts, denn `--expect-min` greift erst, wenn beide Richtungen leer sind;
die Wegnahme laeuft in die `missing`-Halfte und macht den Lauf rot.

Zwei Wege standen offen. Das Werkzeug lernt eine Ausnahme fuer den Fall, dass
jemand die Differenz gemeint hat, oder die Wegnahme wird daneben gemessen. Der
erste haette genau die Schaerfe gekostet, fuer die das Werkzeug gehalten wird,
und haette `test_parity_diff.py` nachgezogen. Also der zweite, in derselben Form,
die Szenario 8 fuer seine Fragen bereits benutzt: zwei kleine Funktionen im
Schritt, `page_answered` und `page_rows`, und daneben zwei gewoehnliche
`compare`-Aufrufe fuer die `extra`-Richtung und ihre Kontrolle.

Was dabei staerker geworden ist als geplant: die Wegnahme wird jetzt **belegt**
(drei Zeilen ohne, keine mit dem Filter) statt nur erwartet, und die leere
Antwort muss der Leerzustand der Seite sein und nicht ihr Fehlerblock, was ein
`--expect-min 0`-Vergleich gar nicht haette unterscheiden koennen.

Was schwaecher ist: die `extra`-Richtung unter dem wegnehmenden Filter wird ueber
einen Nutzer belegt, der diese Dateien ohnehin nicht sehen darf, also ueber drei
leere Mengen. Das ist dieselbe Form, die der Job in `received-share-denied`,
`team-folder-outsider` und `link-share-colleague` schon achtmal benutzt, und sie
wird hier wie dort von einer Kontrollfrage ehrlich gehalten. Fuer den Besitzer
unter dem wegnehmenden Filter ist die `extra`-Richtung nur trivial erfuellt,
weil seine Seite leer ist; dass sie leer ist, ist die direkte Messung daneben.

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die Logzeile von Szenario 10 zaehlte falsch**

- **Found during:** Task 1
- **Issue:** Der letzte `echo` von Szenario 10 lautete "scenario 10 of ten". Mit
  den drei neuen Szenarien ist diese Zahl falsch, und eine falsche Zahl im
  CI-Log ist in diesem Repository ein Befund und keine Formalie.
- **Fix:** "of ten" zu "of thirteen". Die neuen Schritte schliessen mit
  "scenario 11 of thirteen", "scenario 12 of thirteen" und "scenario 13 of
  thirteen" an.
- **Files modified:** `.github/workflows/integration.yml`
- **Commit:** `efa44a9`

Die Zusage des Plans, die bestehenden Szenarien blieben unveraendert, gilt
weiter: Anzahl, Reihenfolge und Schwellwerte sind unberuehrt. Der Diff entfernt
genau fuenf Zeilen, drei davon im Rumpf von `ask_page` und `compare`, eine der
`ask_page`-Aufruf selbst und diese Logzeile.

### Wahlentscheidungen innerhalb des Plans

- **Die Kontrollfrage des dritten Szenarios laeuft unter `types=text`.** Unter
  `types=images` waere auch die Seite des Kollegen leer und sein Dialog nicht,
  also waere die Kontrolle aus demselben Grund rot wie das Szenario, das sie
  kontrollieren soll.
- **`page_answered` und `page_rows` sind zwei Funktionen und nicht eine.** Der
  Zaehler wird in einer Kommandosubstitution gelesen, und ein `exit` in einer
  Substitution verlaesst die Subshell und nicht den Schritt. Ein Waechter im
  Zaehler haette also genau dann nicht gegriffen, wenn er gebraucht wird. Der
  Kommentar sagt das, und eine lokale Probe faehrt es nach.
- **Die sechs Oberflaechen-Gates bekommen sechs Zeilen.** Der Plan laesst beides
  zu; eine Sammelzeile haette sechs verschiedene Vorbehalte zu einem verruehrt.

## Verification

Auf dieser Maschine gibt es kein PHP und die Docker-Engine laeuft nicht, der Job
selbst laeuft also erst in CI. Als Ersatznachweis wurde gemessen und nicht
behauptet:

| Nachweis | Ergebnis |
|---|---|
| YAML mit echtem Parser (PyYAML 6.0.3) geladen, Job `search-parity` vorhanden | gruen, 28 Schritte, 13 Szenario-Schritte |
| `bash -n` ueber jeden der 25 `run:`-Rumpfe des Jobs | gruen |
| `bash -n` ueber den Inhalt des `parity.sh`-Heredocs, den die Pruefung der Schritte nicht sieht | gruen |
| `ask_page` und `compare` mit gestubbtem `curl` und `python3` ausgefuehrt | gruen: der Fuenf-Argument-Aufruf baut die Adresse byteweise wie zuvor, der Sechs-Argument-Aufruf haengt die Parameter nur an die Seite, beide OCS-Routen bleiben uneingeengt |
| `page_answered` und `page_rows` gegen vier gestellte Antworten | gruen: drei Zeilen werden als 3 gezaehlt, der Leerzustand als 0 ohne Fehler, der Fehlerblock und ein Loginformular halten den Schritt an, und der Waechter laeuft vor dem Zaehler |
| Pruefblock Task 1: `types=text` (5), `sort=newest` (2), `types=images` (6), `expect-min` (7) | gruen |
| `scripts/ci/parity_diff.py` und `backend/tests/test_parity_diff.py` unveraendert | gruen, leerer Diff |
| Pruefblock Task 2: `test_search_fields_lockstep` und `search-parity` in `docs/testing.md`, keine Gedankenstriche | gruen |
| Jeder im Register genannte Gate-Name existiert im Baum | gruen, einzeln geprueft |
| Backend-Suite vollstaendig | gruen, 2126 passed, 15 skipped |
| `test_php_acl_boundary.py`, `test_php_trust_boundary.py`, `test_parity_diff.py`, `test_workflow_pins.py`, `test_guest_parity.py` einzeln | gruen, 111 passed |
| Vokabular-Gate, Gedankenstriche, Emojis in beiden Dateien | gruen; die fuenf Treffer des gesperrten Stammes in `docs/testing.md` sind das englische Wort in Bestandszeilen (06.1-12, 06.1-16, Messprotokoll) und fallen unter die Ausnahme E-H2 |

Die drei lokalen Proben liefen als Wegwerfskripte im Arbeitsbaum und wurden vor
dem Commit wieder entfernt; der Baum enthaelt nach jedem Commit genau die zwei
Dateien des Plans.

### Was die CI noch entscheiden muss

Der massgebliche Nachweis kommt aus dem Lauf. Zwei Punkte sind dort zuerst
anzusehen:

1. Ob die Seite unter `types=text` wirklich dieselben drei Treffer zeigt. Die
   Zuordnung `.txt` zur Gruppe `text` steht in `TYPE_GROUPS` und wurde gelesen;
   ob der Weg von der Adresse bis zum Index sie durchtraegt, sagt erst der Lauf.
2. Ob die Seite unter `sort=newest` dieselbe Menge zeigt. Drei Dateien mit fast
   gleichem Zeitstempel sind fuer die Menge egal, fuer die Reihenfolge nicht,
   und die Reihenfolge prueft dieses Szenario bewusst nicht.

## Known Stubs

Keine. Beide Dateien sind vollstaendig; was fehlt, ist ein CI-Lauf und die
Abnahme in 13-13.

## Threat Flags

Keine neue Angriffsflaeche: dieser Plan aendert eine CI-Datei und ein Dokument,
keine Route, keinen Schreibpfad, kein Paket.

| Threat ID | Umsetzung |
|---|---|
| T-13-57 | drei Szenarien stellen die `extra`-Richtung unter Filter und unter Sortierung scharf; die beiden Grenz-Gates sind unveraendert und gruen |
| T-13-58 | `--expect-min` bleibt Pflicht und bleibt bei 11 und 12 auf dem Wert des ungefilterten Szenarios; die einzige 0 steht im wegnehmenden Szenario, ist im Kommentar begruendet und wird von einer Kontrollfrage mit drei Treffern gehalten |
| T-13-59 | `scripts/ci/parity_diff.py` unveraendert, mit leerem Diff nachgewiesen; die Rot-Faehigkeit und ihre drei Gegenproben sind unberuehrt |
| T-13-60 | akzeptiert wie geplant; die neuen Schritte geben Trefferzahlen eines synthetischen Fixtures aus und keinen Dateinamen |
| T-13-61 | `docs/testing.md` nennt keinen Pfad und keinen Suchbegriff einer realen Instanz |
| T-13-SC | kein Paket installiert |

## Fuer 13-13

Offen und bewusst offen gelassen:

- **FILT-05 ist nicht als erfuellt markiert.** Der Plan verlangt das
  ausdruecklich, und die Abnahme steht aus.
- **Der Paritaetsjob ist lokal nicht gelaufen.** Die beiden Punkte oben sind
  das, was im ersten CI-Lauf zuerst anzusehen ist.
- **Die `extra`-Richtung unter einem wegnehmenden Filter wird ueber leere Mengen
  belegt.** Wer das schaerfer will, braucht ein Fixture mit zwei Dateitypen, also
  eine Bilddatei neben den Textdateien; dann waere `types=images` ein Szenario
  mit nichtleerer Menge und symmetrisch vergleichbar. Das ist eine
  Fixture-Erweiterung (`EXPECTED_JUDGED` und der Bau der Markerdateien) und kein
  Nachtrag zu diesem Plan.

## Self-Check: PASSED

- `.github/workflows/integration.yml` FOUND
- `docs/testing.md` FOUND
- `.planning/phases/13-filter-und-sortierung-auf-der-ergebnisseite/13-12-SUMMARY.md` FOUND
- Commit `efa44a9` FOUND
- Commit `53b24e5` FOUND
