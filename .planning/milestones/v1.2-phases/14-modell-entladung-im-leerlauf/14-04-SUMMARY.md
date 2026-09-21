---
phase: 14-modell-entladung-im-leerlauf
plan: 04
subsystem: infra
tags: [memory, poller, tokenizer, splitter, embeddings, lazy-build, tdd]

# Dependency graph
requires:
  - phase: 14-modell-entladung-im-leerlauf
    provides: Der Vorprueflauf 14-02 und der Owner-Entscheid "freigegeben" vom 19.09.2026
  - phase: 07-semantische-haelfte
    provides: Der faule Bau des Cutters in _build_the_cutter, die drei Antworten ueber ihn und die Regel, dass die drei Teile zusammen reisen
provides:
  - Poller.busy, die ausdrueckliche Auskunft "dieser Durchgang ist an Arbeit"
  - Poller.release_cutter(), die Freigabe des Paares _chunker und _model
  - Die Zusage, dass _cutter_absent und _cutter_failed_at eine Freigabe ueberleben
  - Ein Quelltext-Gate, das die Halbheit ausschliesst, statt sie nur zu testen
affects: [14-05, 14-06, 14-07, 15-boxmessung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Bedingung, an der eine Entladung haengt, bekommt ein eigenes oeffentliches Property statt eines zweckentfremdeten Log-Merkers"
    - "Zusammengehoerende Felder werden gemeinsam freigegeben, und die Gemeinsamkeit wird am Syntaxbaum geprueft und nicht an einem Lauf"

key-files:
  created: []
  modified:
    - backend/src/findling/worker/poller.py
    - backend/tests/test_poller.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "busy antwortet bool(self._held) und nichts anderes: gehaltene Warteschlangenzeilen sind die einzige Groesse am Poller, die einen laufenden Durchgang bedeutet"
  - "Die Reihenfolge der drei Antworten in release_cutter ist busy zuerst, dann nichts zu tun, dann freigeben; die Arbeit schlaegt die Leere, weil Pitfall 3 teurer ist als eine ausgelassene Freigabe"
  - "Die Halbheit wird am Syntaxbaum ausgeschlossen: release_cutter darf genau _chunker und _model zuweisen, was zugleich das Gate gegen ein Zuruecksetzen der beiden Merker ist"
  - "Drei statt zwei Testdateien angefasst: test_measurement_scripts.py zieht den Baumhash des Pakets nach, wie es die Lehre aus 14-03 verlangt"

patterns-established:
  - "Ein Property, das eine Entladung freigibt, wird gegen einen echten Durchgang gemessen (busy waehrend record, nicht busy nach dem Ack) und nicht gegen eine Zuweisung"
  - "Ein Quelltest ueber ast.walk haelt eine Invariante ueber alle Zuweisungen einer Methode fest, wo ein Verhaltenstest nur die Faelle sieht, an die jemand gedacht hat"

requirements-completed: []  # MEM-02 bleibt offen bis 14-05 und 14-07, Begruendung im Abschnitt Requirements

# Metrics
duration: 22min
completed: 2026-09-19
---

# Phase 14 Plan 04: Die Indexseite laesst los Summary

**Der groessere der beiden Speicherhalter kann ab jetzt losgelassen werden: `release_cutter()` gibt das Paar `_chunker` und `_model` zusammen frei, nie eines von beiden, und `busy` sagt ausdruecklich, ob ein Durchgang gerade an Arbeit ist, statt dass ein Log-Merker die Antwort spielen muss.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-09-19T13:25:00Z
- **Completed:** 2026-09-19T13:47:00Z
- **Tasks:** 3 von 3
- **Files modified:** 3 (kein neues Modul, keine neue Abhaengigkeit)

## Accomplishments

### Der Log-Merker wird nicht mehr zweckentfremdet

`_idle_announced` sieht aus wie eine Antwort auf "arbeitest du gerade" und ist
keine. Er wird in `arm()` zurueckgesetzt und sagt, ob eine Zeile geschrieben
wurde. Ein Entlader, der ihn liest, entlaedt nach jedem Armieren einmal falsch,
und das ist Leitplanke 3 der 14-CONTEXT.md.

Das neue Property `busy` antwortet `bool(self._held)`. Die gehaltenen
Warteschlangenzeilen sind die einzige Groesse am Poller, die tatsaechlich
"dieser Durchgang steht mitten in Arbeit" bedeutet: `run_once` setzt sie direkt
nach dem Anspruch und leert sie an der Bestaetigung sowie in `unlock_held`. Der
Docstring nennt alle drei Alternativen beim Namen und sagt, warum keine von
ihnen taugt:

| Kandidat | Was er wirklich sagt |
|---|---|
| `_idle_announced` | ob eine Zeile geschrieben wurde, zurueckgesetzt bei jedem Armieren |
| `armed` | das Gegenteil der Frage: ein armierter Poller mit leerem Bestand ist genau der Container, fuer den die Entladung gebaut wird |
| `cooldown` | eine Wartezeit, und Warten ist keine Arbeit |

Dazu steht im Docstring, wer es liest: die dritte Lifespan-Aufgabe aus 14-07
ueber `main.active_poller()`. Damit bleibt die Abhaengigkeitsrichtung stehen,
`worker/` importiert aus `embed/` und nie umgekehrt; nachgeprueft mit
`grep -rn 'from findling.worker' backend/src/findling/embed/`, leer.

### Die Freigabe, beide Haelften oder keine

`release_cutter()` hat drei Antworten in dieser Reihenfolge:

1. **`busy` ist wahr** -> `False`, nichts angefasst. Pitfall 3 steht als
   Kommentar daneben: mitten im Indexlauf freizugeben heisst, die Gewichte
   Sekunden spaeter wieder zu laden; ueber einen Volllauf hinweg wird die
   Entladung zum Kostenfaktor statt zur Ersparnis, und nichts wird dabei rot.
2. **Beide Felder sind schon `None`** -> `False`. Es gab nichts loszulassen, und
   der Zaehler des Aufrufers in 14-07 bleibt dadurch ehrlich.
3. **Sonst** -> beide Felder auf `None`, untereinander, mit dem Kommentar, dass
   die Closure `cut` faellt und mit ihr `tokenizer` und `splitter`, und `True`.

Der Wiederaufbau braucht keinen neuen Code: der Kopf von `_build_the_cutter`
kehrt zurueck, wenn beide Felder stehen, und baut sonst neu; der Aufruf an der
Zeile 1130 ist bereits bedingt. Ein Testfall faehrt genau das nach: bauen,
freigeben, wieder bauen.

### Die drei gemerkten Tatsachen ueberleben

`release_cutter` fasst `_cutter_absent` (Eigenschaft der Installation) und
`_cutter_failed_at` (der laufende Cooldown) nicht an. Beides ist Pitfall 8 und
Anti-Pattern 7 aus ARCHITECTURE.md; die Symptome eines Zuruecksetzens stehen in
den Docstrings der zwei Testfaelle und nicht nur im Plan: ein Container ohne
Modell fing wieder an, bei jeder Zeile zu staten, und eine Abkuehlphase braeche
still ab.

Belegt ist das doppelt. Verhaltensseitig durch je einen Testfall, der den Wert
vor und nach der Freigabe vergleicht und bei der Abkuehlphase zusaetzlich
`_cutter_cooling_down` nach der Freigabe noch auf `True` sieht. Und
quelltextseitig durch `test_the_release_never_leaves_half_a_cutter_behind`: der
Test liest `release_cutter` ueber `ast.walk` und verlangt, dass die Methode
**genau** `_chunker` und `_model` zuweist. Eine Zuweisung an einen der beiden
Merker waere damit rot, bevor irgendein Verhaltenstest sie bemerkt.

### Keine zweite Stelle fuer die Seitenrueckgabe

`release_cutter` ruft keine Sammelrunde und keinen Trim. Nachgeprueft mit
`grep -c 'malloc_trim\|gc.collect' backend/src/findling/worker/poller.py`,
Ergebnis 0, und zwar auch in den Kommentaren: der Docstring umschreibt beide
Begriffe absichtlich, damit das Gate nicht an seiner eigenen Erklaerung rot
wird. Das Zurueckgeben der Seiten passiert genau einmal je Takt in
`embed/model.py` (Plan 14-05).

## Task Commits

1. **Task 1: Das busy-Property** (TDD)
   - `eaef683` test(14-04): die Faelle des busy-Property, gegen einen echten Durchgang (ROT, 5 Faelle)
   - `a92f4ca` feat(14-04): das busy-Property am Poller, ausdruecklich benannt (GRUEN)
2. **Task 2: release_cutter** (TDD)
   - `87d5ec5` test(14-04): die Faelle der Freigabe, beide Haelften und die zwei Merker (ROT, 7 Faelle)
   - `1c4a33e` feat(14-04): release_cutter am Poller, beide Haelften oder keine (GRUEN)
3. **Task 3: Die Tests, und was sie festhalten**
   - `eb7dba3` test(14-04): der Fall, der die Halbheit ausschliesst (13. Fall, volle Suite)

Eine Refactor-Stufe gab es nicht: beide Zugaenge sind in ihrer ersten gruenen
Form geblieben, weil an einer Property mit einer Zeile und einer Methode mit
drei Verzweigungen nichts aufzuraeumen war.

## Files Created/Modified

- `backend/src/findling/worker/poller.py` , das Property `busy` hinter `armed`
  und die Methode `release_cutter` hinter `_build_the_cutter`, beide mit ihrem
  Begruendungstext
- `backend/tests/test_poller.py` , 13 neue Faelle (5 zu `busy`, 7 zu
  `release_cutter`, 1 zur Halbheit) plus der Helfer `_with_a_built_cutter`; neu
  importiert wird `ast` fuer den Quelltest
- `backend/tests/test_measurement_scripts.py` , `PACKAGE_TREE_HASH_TODAY`
  zweimal nachgezogen (je einmal je Produktcode-Commit), mit je einem
  Begruendungsabsatz in der Hausform der Datei; 54 Dateien unveraendert

## Decisions Made

- **`busy` liest `_held` und nicht `run_once`-Zustand.** Ein eigenes Flag, das
  am Anfang und Ende des Durchgangs gesetzt wird, waere eine zweite Wahrheit
  ueber denselben Sachverhalt und muesste in jedem Abbruchpfad mitgepflegt
  werden. `_held` wird auf allen Wegen geleert, auch im `_abort` und in
  `unlock_held`, und ist damit die Groesse, die von sich aus stimmt.

- **Die Reihenfolge der drei Antworten in `release_cutter`.** `busy` wird vor
  der Frage nach dem Bestand geprueft, obwohl ein arbeitender Poller fast immer
  auch ein Paar hat. Grund: die Frage "darf ich ueberhaupt" ist teurer als die
  Frage "gibt es etwas", und ein `True` fuer einen arbeitenden Container waere
  der Fehler, der laut Pitfall 3 nirgends rot wird.

- **Die Halbheit wird am Syntaxbaum ausgeschlossen.** Der Plan verlangte einen
  Verhaltensfall; dazu kam ein Quelltest ueber `ast.walk`, der alle
  Attributzuweisungen der Methode einsammelt und auf genau `_chunker` und
  `_model` festlegt. Er ist zugleich das Gate der beiden
  Acceptance-Kriterien zu `_cutter_absent` und `_cutter_failed_at`, und er
  bleibt rot, wenn ein spaeterer Umbau ein drittes Feld anfasst, an das heute
  niemand denkt.

- **Der Verhaltensfall zur Halbheit laeuft ueber `_embed_ready` auf einem
  Container ohne Artefakte.** Dort ist ein gebautes Paar der einzig verbliebene
  Grund fuer ein Ja. Waere bei der Freigabe genau ein Feld gefallen, antwortete
  `_embed_ready` weiterhin mit Ja, Zeilen gingen an einen Zweig, der nicht
  laufen kann, und nichts wuerde dabei werfen.

- **Drei Testfaelle tragen einen erklaerenden Docstring** (Arbeit, und je einer
  je Merker), wie der Plan es verlangt. Die uebrigen tragen Kommentare, weil
  sie ein Verhalten festhalten und keinen Befund.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Der Baumhash des Python-Pakets musste mitwandern**

- **Found during:** Task 1 und Task 2 (je einmal)
- **Issue:** Jede Aenderung unter `backend/src/findling/` macht
  `test_the_recipe_reproduces_the_tree_hash_of_the_python_package` in
  `tests/test_measurement_scripts.py` rot. Der Plan nennt in `files_modified`
  nur `poller.py` und `test_poller.py`, und Verifikationspunkt 5 verlangt sogar
  ausdruecklich, dass nur diese zwei Dateien veraendert sind.
- **Fix:** `PACKAGE_TREE_HASH_TODAY` wurde in beiden Produktcode-Commits mit dem
  Originalrezept (`40b-baumhash.py`) neu gelesen und mit je einem
  Begruendungsabsatz in der Hausform der Datei nachgezogen. Die historische Zahl
  `PACKAGE_TREE_HASH` aus den Rohdaten blieb unberuehrt, ebenso die Dateizahl 54.
- **Files modified:** `backend/tests/test_measurement_scripts.py`
- **Verification:** `uv run pytest tests/test_measurement_scripts.py -q`, 230
  bestanden
- **Committed in:** `a92f4ca` und `1c4a33e` (jeweils im Task-Commit)

**2. [Rule 3 - Blocking] Drei Testnamen umbenannt, damit der Pruefbefehl des Plans sie sieht**

- **Found during:** Task 2
- **Issue:** Der `verify`-Block des Plans filtert mit
  `-k "release_cutter or cutter"`. Drei der sieben Faelle hiessen zunaechst
  `test_a_release_...` und wurden von diesem Filter nicht erfasst; der Befehl
  haette also nur vier von sieben Faellen gefahren und trotzdem gruen gemeldet.
- **Fix:** Umbenannt zu `test_a_cutter_release_while_the_pass_holds_rows_...`,
  `test_the_first_cutter_build_after_a_release_...` und
  `test_a_cutter_release_does_not_cut_a_running_cooldown_short`. Der Pruefbefehl
  erfasst jetzt alle sieben.
- **Files modified:** `backend/tests/test_poller.py`
- **Verification:** `uv run pytest tests/test_poller.py -q -k "release_cutter or cutter"`
  zeigt sieben Faelle statt vier
- **Committed in:** `87d5ec5` (im ROT-Commit)

**3. [Rule 3 - Blocking] Zeilenenden beim Anhaengen an test_poller.py**

- **Found during:** Task 1
- **Issue:** `test_poller.py` traegt CRLF; ein Anhaengen mit LF machte
  `ruff format --check` rot, ohne dass inhaltlich etwas zu formatieren gewesen
  waere. Das ist die bekannte CRLF-Falle dieser Maschine.
- **Fix:** Alle Schreibvorgaenge an den drei Dateien laufen byteweise mit
  Rueckwandlung nach CRLF.
- **Files modified:** `backend/tests/test_poller.py`
- **Verification:** `uv run ruff format --check`, 122 Dateien bereits formatiert
- **Committed in:** `eaef683`

---

**Total deviations:** 3 auto-fixed (3 blocking)
**Impact on plan:** Keine Umfangserweiterung. Befund 1 ist die in 14-03
festgehaltene Lehre, die der Plan erneut nicht kannte; Befund 2 macht den
Pruefbefehl des Plans erst wirksam; Befund 3 ist Werkzeugmechanik.

## Issues Encountered

Keine offenen.

Der Hinweis aus Befund 1 gilt weiter und gehoert vor 14-05, 14-06 und 14-07 in
die Dateiliste: `tests/test_measurement_scripts.py` ist die dritte Datei jedes
Plans, der Python-Produktcode anfasst. Verifikationspunkt 5 solcher Plaene
sollte sie ausdruecklich erlauben, statt sie als Abweichung zu erzwingen.

## Verification

| Punkt des Plans | Ergebnis |
|---|---|
| 1. ruff check, ruff format --check, pyright, vulture | gruen (122 Dateien formatiert, 0 Fehler, 0 Warnungen, keine Funde) |
| 2. Volle Suite `uv run pytest -q` aus backend/ | **2159 bestanden, 15 uebersprungen** (vorher 2146) |
| 3. `grep -c 'malloc_trim\|gc.collect'` in poller.py | **0** |
| 4. `grep -rn 'from findling.worker' backend/src/findling/embed/` | leer, die Abhaengigkeitsrichtung steht |
| 5. Nur poller.py und test_poller.py veraendert | **nicht gehalten**, siehe Abweichung 1: dazu `tests/test_measurement_scripts.py`. Nichts unter `embed/`, `api/` oder `main.py` |

Acceptance-Kriterien der drei Tasks, einzeln nachgefahren:

| Kriterium | Ergebnis |
|---|---|
| `Poller.busy` ist ein Property und gibt `bool` | ja, `return bool(self._held)` |
| `_idle_announced` wird in `busy` nicht verwendet | nur im Docstring genannt, keine Verwendung im Rumpf |
| Docstring nennt `_idle_announced` und sagt warum nicht | ja, dazu `armed` und `cooldown` |
| `Poller.release_cutter` existiert, gibt `bool`, ist synchron | ja, `def release_cutter(self) -> bool` |
| Keine Zuweisung an `_cutter_absent`/`_cutter_failed_at` in `release_cutter` | ja, durch den `ast`-Test erzwungen |
| Mindestens zwoelf neue Faelle (5 busy, 7 release_cutter) | **13** (5 + 7 + 1 zur Halbheit) |
| Drei Faelle mit Docstring, die Pitfall 3 beziehungsweise 8 benennen | ja, alle drei |
| Kein bestehender Fall geloescht oder geschwaecht | ja, 93 Faelle der Datei vorher, 106 nachher |

## Known Stubs

`Poller.busy` und `Poller.release_cutter()` werden von niemandem aufgerufen. Das
ist die ausdrueckliche Ansage des Plans ("Was dieser Plan NICHT tut: er ruft
`release_cutter()` nirgends auf") und kein Stub im Sinne einer halben Umsetzung:
beide Zugaenge sind vollstaendig, getestet und belegt. Der Aufrufer ist die
dritte Lifespan-Aufgabe aus 14-07, die Uhr dazu kommt aus 14-06.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Registers. Die vier Eintraege des
Plans sind abgedeckt:

| Threat | Umsetzung |
|---|---|
| T-14-11 (Freigabe mitten im Indexlauf) | `release_cutter` kehrt bei `busy` ohne Wirkung zurueck, ein Testfall haelt es fest; die zweite Bedingung liegt beim Aufrufer in 14-07 |
| T-14-12 (Zuruecksetzen der Merker) | Die Freigabe fasst nur das Paar an, je ein Verhaltensfall je Merker und dazu der `ast`-Test |
| T-14-13 (Blockierender Aufruf auf dem Event Loop) | Synchron, und der Docstring weist den Aufruf ueber `asyncio.to_thread` aus |
| T-14-SC (Abhaengigkeiten) | Keine neue Abhaengigkeit, `pyproject.toml` unberuehrt |

## Requirements

**MEM-02 wird hier NICHT abgehakt**, obwohl die Frontmatter des Plans sie nennt.
Der Wortlaut der Anforderung verlangt, dass die Entladung **beide**
Speicherhalter freigibt, Engine der Suchseite und Cutter der Indexseite, und
dass die Messgroesse "Rueckkehr zur Grundlast nach einem Indexlauf" belegt ist.
Dieser Plan baut die eine Haelfte und ruft sie ausdruecklich nirgends auf; die
zweite Haelfte ist 14-05, der Aufrufer ist 14-07.

Das ist die Lehre aus 14-01, die in STATE.md steht: eine Anforderung gehoert an
den Plan, der sie belegt, und nicht an den, der ihr Werkzeug baut. Damals hakte
der Zustandsbefehl MEM-04 ab, weil die Frontmatter sie nannte, und der Haken
musste zurueckgenommen werden. `REQUIREMENTS.md` traegt MEM-02 deshalb weiter
als `Pending`.

## User Setup Required

None - keine externe Konfiguration noetig.

## Next Phase Readiness

Bereit fuer **14-05**. Die Indexseite laesst los; was jetzt noch fehlt, ist die
Suchseite (`embed/model.py`, samt der einen Stelle, an der die Seiten
zurueckgegeben werden), die Uhr (14-06) und die Lifespan-Aufgabe, die beide
Halter zusammenfuehrt (14-07).

Fuer 14-07 steht der Vertrag fest: `main.active_poller()` liefert die Instanz,
`poller.busy` sagt, ob sie arbeitet, und `poller.release_cutter()` laeuft ueber
`asyncio.to_thread`. Der Rueckgabewert ist `True` genau dann, wenn wirklich ein
Paar gefallen ist, und taugt damit als Zaehlgrundlage fuer `unload_count`.

## Self-Check: PASSED

Alle drei geaenderten Dateien liegen auf der Platte. Die fuenf Commits
(`eaef683`, `a92f4ca`, `87d5ec5`, `1c4a33e`, `eb7dba3`) stehen im Log. Die fuenf
Verifikationspunkte und die acht Acceptance-Kriterien sind einzeln nachgefahren
und oben protokolliert; Punkt 5 ist mit der dokumentierten Abweichung 1 offen
ausgewiesen statt stillschweigend abgehakt.

---
*Phase: 14-modell-entladung-im-leerlauf*
*Completed: 2026-09-19*
