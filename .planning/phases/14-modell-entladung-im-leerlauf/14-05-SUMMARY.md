---
phase: 14-modell-entladung-im-leerlauf
plan: 05
subsystem: infra
tags: [memory, embeddings, onnxruntime, malloc-trim, ctypes, degradation, tdd]

# Dependency graph
requires:
  - phase: 14-modell-entladung-im-leerlauf
    provides: Der Vorprueflauf 14-02 und der Owner-Entscheid "freigegeben" vom 19.09.2026
  - phase: 06.1-geteilte-engine
    provides: Die eine geteilte Engine, der RLock, der den Graphlauf bewusst nicht deckt, und die drei unterschiedenen Fehlerarten
provides:
  - EmbeddingModel.release(), die Freigabe der Suchseite samt Rueckgabe der freien Seiten
  - _return_free_pages_to_the_system(), gc.collect vor malloc_trim, mit Schutzschalter
  - unload_count(), der monotone Zaehler neben load_count()
  - EmbeddingModel.last_use(), die Leerlauf-Uhr beider Spuren in einer Zeile
  - Der Aktivitaetszaehler _in_flight, die einzige neue Invariante dieser Phase
  - Der Schalter may_load an embed_query und _embed, die untere Haelfte von MEM-03
affects: [14-06, 14-07, 14-08, 14-10, 15-boxmessung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Rueckgabe von Speicher an das Betriebssystem laeuft ausserhalb jeder Sperre, weil sie blockiert"
    - "Ein Schalter und die Regel, die ihn wirft, werden in zwei Plaenen gebaut: erst der Schalter mit unveraenderter Vorgabe, dann die Regel"
    - "Eine libc ohne malloc_trim ist ein unterstuetzter Container, kein Fehler: dieselbe Haltung, die extract/ocr.py gegenueber einem fehlenden tesseract einnimmt"

key-files:
  created: []
  modified:
    - backend/src/findling/embed/model.py
    - backend/tests/test_embed_model.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Die Docstring-Zahlen der Aufteilung kommen aus dem Vorprueflauf (15 bis 19 Prozent gc, 80 bis 85 Prozent Trim) und nicht aus dem aelteren Vorrecherche-Absatz des Research (20 und 5 Prozent), weil der Plan ausdruecklich den Vorprueflauf als Quelle nennt"
  - "Der Aktivitaetszaehler wird im selben Lock-Block hochgezaehlt, in dem die Engine gebunden wird, und nicht danach: zwischen Binden und Zaehlen laege sonst ein Fenster, in dem eine Freigabe gc.collect und malloc_trim auf dem Heap eines startenden Batches laufen liesse"
  - "Keine Identitaetspruefung in release(): sie gehoert zum Nachwaermen aus MEM-03 und damit in 14-06/14-07, und heute kann kein zweiter Weg eine Engine laden, ohne im selben Lock-Block den Zaehler zu erhoehen"
  - "Die drei gemerkten Tatsachen werden zusaetzlich am Syntaxbaum gehalten: release schreibt genau ein Attribut, _engine; die Verhaltenstests allein koennen zwei der drei nur ueber eine Freigabe pruefen, die False antwortet"
  - "REQUIREMENTS.md bleibt unberuehrt: MEM-02 fehlt noch der Aufrufer (14-07), MEM-03 fehlt die obere Haelfte (das Nachwaermen)"

patterns-established:
  - "Ein Stand-in fuer ctypes als ganzes Modulattribut statt eines setattr auf das echte ctypes: der Testlauf bleibt ohne globale Nebenwirkung und deckt beide Fehlerarten des Schutzschalters"
  - "Eine Reihenfolge wird doppelt gehalten, zur Laufzeit aufgezeichnet und im Quelltext gelesen: die Aufzeichnung belegt, was einmal geschah, die Quelltextpruefung, was beim naechsten Mal geschieht"

requirements-completed: []  # MEM-02 und MEM-03 bleiben offen, Begruendung im Abschnitt Requirements

# Metrics
duration: 20min
completed: 2026-09-19
---

# Phase 14 Plan 05: Der Halter der Suchseite laesst los Summary

**Der zweite Speicherhalter kann ab jetzt losgelassen werden, und er gibt die Seiten wirklich zurueck: `release()` loest die Gewichte, sammelt und trimmt in dieser Reihenfolge ausserhalb jeder Sperre, laesst die drei gemerkten Tatsachen stehen und verweigert sich, solange ein Batch laeuft.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-09-19T13:47:00Z
- **Completed:** 2026-09-19T14:07:00Z
- **Tasks:** 3 von 3
- **Files modified:** 3 (kein neues Modul, keine neue Abhaengigkeit, beide Importe Stdlib)

## Accomplishments

### Vier Zugaenge, und keiner davon wird hier gerufen

`embed/model.py` hat vier neue Faehigkeiten und null neue Aufrufer. Das ist die
Absicht des Plans und sie ist nachgeprueft: `grep -rn 'release()'
backend/src/findling/` zeigt ausser der Definition nichts. Die Regel, wann
entladen wird, kommt in 14-06, der Takt in 14-07.

| Zugang | Was er ist | Wer ihn lesen wird |
|---|---|---|
| `last_use() -> float \| None` | die Leerlauf-Uhr, gesetzt in `_embed` | die Regel aus 14-06 |
| `_in_flight` | der Aktivitaetszaehler, die einzige neue Invariante der Phase | `release` selbst |
| `release() -> bool` | Loslassen, sammeln, trimmen, zaehlen | die dritte Lifespan-Aufgabe aus 14-07 |
| `may_load` an `embed_query` | die untere Haelfte von MEM-03 | die Degradationsnaht aus 14-08 |
| `unload_count() -> int` | der monotone Gegenzaehler zu `load_count()` | die A/B-Messung der Phase 15 |

### Eine Zeile deckt beide Spuren

Die Uhr steht in `_embed` und nicht in den beiden oeffentlichen Einstiegen,
weil beide durch `_embed` gehen. Stuende sie in `embed_query` allein, saehe ein
Container mitten im Indexlauf fuer den Entlader leer aus und verloere die
Gewichte, die die naechste Zeile braucht. Sie steht ausserdem **unter** der
bestehenden Leerpruefung: ein leerer Batch ist die normale Antwort fuer ein
Dokument ohne Text, und ein Lauf ueber ein Verzeichnis voller Bilder darf den
Leerlauf nicht mit Dokumenten beenden, die gar keinen Text hatten.

### Der Trim ist der wirksame Schritt, und das steht jetzt im Docstring

Die Aufteilung ist keine Behauptung, sondern der gemessene Befund des
Vorprueflaufs vom 19.09.2026 (`docs/measurements/2026-09-entladung-vorpruefung/`,
Abschnitt 3, Erwartung E3):

| Schritt | Anteil der Ladung |
|---|---|
| `gc.collect()` allein | 15,1 bis 18,2 Prozent |
| `malloc_trim(0)` danach | 80,2 bis 84,9 Prozent |

Damit ist der Schutzschalter um `ctypes.CDLL` kein toter Zweig, sondern die
Stelle, an der auf einer fremden libc vier Fuenftel der Rueckgabe ausfallen. Er
faengt ausschliesslich `(OSError, AttributeError)`, nie `Exception`, warnt genau
einmal je Prozess und nennt dabei nur den Klassennamen, keinen Pfad und keine
Speicherzahl (T-14-14, T-14-18). Der Bibliotheksname steht als Literal im Code
und kommt an genau einer Stelle vor.

### Die Freigabe laeuft in zwei Haelften, und die Grenze ist das Lock

Unter `self._lock` passiert das Loslassen und das Zaehlen; `gc.collect()` und
der Trim laufen **ausserhalb**. Beide blockieren, und ein gehaltenes Lock wuerde
jede gleichzeitige Suche mitblockieren (T-14-16). Der Aufrufer aus 14-07 legt
die ganze Methode zusaetzlich in `asyncio.to_thread`, damit der Event Loop und
mit ihm `/heartbeat` nie stehen bleibt.

Die Freigabe verweigert sich in zwei Faellen, und beide antworten `False`, ohne
etwas zu tun: kein Halter ohne Engine (das ist der haeufigste Fall, denn der
Aufrufer laeuft auf einem Takt) und kein laufender Batch. Der zweite ist
T-14-15: die lokale Referenz in `_embed` haelt das Objekt ohnehin am Leben, es
wuerde also nichts brechen, aber `gc.collect()` und `malloc_trim` liefen ueber
den Heap, in dem dieser Batch gerade alloziert. Ein ausgelassener Takt ist
billiger.

### Die drei gemerkten Tatsachen, von zwei Seiten gehalten

Ein fehlendes Modellverzeichnis, ein Laden in seiner Abkuehlung und der
Warnmerker eines geworfenen Batches ueberleben jede Freigabe (Pitfall 8). Die
Verhaltenstests koennen zwei davon nur ueber eine Freigabe pruefen, die `False`
antwortet: ein Halter mit abwesenden Artefakten hat nie eine Engine, ein Laden,
das geworfen hat, hinterlaesst auch keine. Deshalb steht daneben ein Gate am
Syntaxbaum, das die Luecke von der anderen Seite schliesst: `release` schreibt
genau ein Attribut, und es heisst `_engine`. Dasselbe Muster haelt den Zaehler:
im ganzen Modul gibt es eine Initialisierung `_UNLOAD_COUNT = 0` und ein
`_UNLOAD_COUNT += 1`, sonst nichts, das den Namen schreibt (T-14-17).

### may_load ist ein Schalter und keine Regel

`_embed(..., may_load: bool = True)` und `embed_query(..., *, may_load: bool =
True)`. Der Vorgabewert haelt jedes bestehende Verhalten byteweise, was die
volle Suite belegt: 2179 bestanden, keine Anpassung an einem einzigen
bestehenden Fall noetig. `embed_passages` bekommt den Schalter **nicht**, und
der Docstring sagt warum: ueber einem Indexlauf steht keine 1,5-Sekunden-Decke,
und nach einer Entladung ist die naechste Zeile des Laufs der richtige Moment,
die Gewichte wiederzuholen. `grep -c 'from findling.config' model.py` ist 0: die
Datei liest keine Einstellung, sie traegt nur den Schalter.

## Task Commits

1. **Task 1 (RED): Die Faelle der Uhr, des Zaehlers und des Schalters** - `64f2f3a` (test)
2. **Task 1 (GREEN): Uhr, Aktivitaetszaehler und may_load** - `90f345a` (feat)
3. **Task 2 (RED): Die Faelle der Freigabe und der drei Tatsachen** - `d5a2a82` (test)
4. **Task 2 (GREEN): release, Entladezaehler, Rueckgabe der Seiten** - `8055795` (feat)
5. **Task 3: Schutzschalter, Reihenfolge und das Gate am Syntaxbaum** - `9b6d078` (test)

## TDD Gate Compliance

Beide Tasks mit `tdd="true"` sind in der Reihenfolge RED, GREEN gefahren, und
beide RED-Laeufe sind rot gewesen, bevor eine Zeile Produktivcode entstand:

| Task | RED-Beleg | GREEN-Beleg |
|---|---|---|
| 1 | 8 failed, 18 passed; `AttributeError: 'EmbeddingModel' object has no attribute 'last_use'` und `TypeError: embed_query() got an unexpected keyword argument` | 26 passed |
| 2 | Sammelfehler `ImportError: cannot import name 'unload_count'` | 34 passed |

Ein REFACTOR-Schritt war in beiden Faellen nicht noetig; es gibt also bewusst
keinen `refactor`-Commit.

## Tests

20 neue Faelle, alle im selben `tests/test_embed_model.py`, und **keiner von
ihnen** traegt den Skip-Marker fuer `FINDLING_EMBED_MODEL_DIR`. Die Zahl der
Skips der vollen Suite ist unveraendert bei 15; die beiden Skips dieser Datei
sind die zwei alten Faelle gegen das echte Modell.

| Block | Faelle |
|---|---|
| Uhr, Zaehler, `may_load` | 8 |
| Freigabe, Zaehler, die drei Tatsachen | 8 |
| Schutzschalter, Reihenfolge, Syntaxbaum-Gate | 4 |

Zwei Bauformen sind neu in dieser Datei:

- **Der libc-Ausfall.** `model_module.ctypes` wird als Ganzes gegen ein
  `SimpleNamespace` getauscht, einmal mit einem `CDLL`, das `OSError` wirft, und
  einmal mit einem, das ein Objekt ohne `malloc_trim` liefert. Kein `setattr`
  auf das echte `ctypes`, also keine globale Nebenwirkung. Beide Faelle pruefen:
  `release()` gibt `True`, die Engine ist weg, genau eine Warnung faellt, und
  der zweite Durchgang warnt nicht noch einmal.
- **Die Reihenfolge.** Zur Laufzeit aufgezeichnet (`["collect",
  "malloc_trim(0)"]`) und zusaetzlich im Quelltext gelesen. Die Aufzeichnung
  belegt, was einmal geschah; die Quelltextpruefung, was beim naechsten Mal
  geschieht.

Dazu eine tickende Uhr als Stand-in fuer `time`, weil `time.monotonic` auf einer
schnellen Maschine zweimal dieselbe Zahl antworten kann und ein Test, der die
Uhr vorwaerts erwartet, dann aus einem fremden Grund rot waere.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die Zahlen des Docstrings kommen aus dem Vorprueflauf, nicht aus der Vorrecherche**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt im Action-Block, der Docstring nenne "die
  gemessene Aufteilung aus dem Vorprueflauf", setzt in derselben Klammer aber
  die Zahlen "rund ein Fuenftel auf x86_64 und rund ein Zwanzigstel auf
  aarch64". Diese beiden Zahlen stammen aus den Vorrecherche-Abschnitten 3.2 und
  3.3 des Research und aus dessen Code-Beispiel 14.1, also von vor dem Lauf. Der
  Vorprueflauf selbst hat 15,1 bis 18,2 Prozent fuer `gc.collect()` gemessen,
  auf beiden Aesten, und die 5 Prozent fuer aarch64 damit widerlegt.
- **Fix:** Der Docstring nennt 15 bis 19 Prozent fuer den Collect und 80 bis 85
  fuer den Trim und verweist auf `docs/measurements/2026-09-entladung-vorpruefung/`,
  Abschnitt 3. Ein Docstring mit einer widerlegten Zahl ist eine Fehlinformation
  an der Stelle, an der spaeter jemand die Wirksamkeit des Schrittes beurteilt.
- **Files modified:** backend/src/findling/embed/model.py
- **Commit:** `8055795`

**2. [Rule 2 - Fehlende notwendige Funktionalitaet] Der Aktivitaetszaehler steht im Lock-Block, nicht dahinter**

- **Found during:** Task 1
- **Issue:** Der Plan sagt "hochgezaehlt direkt nach dem Lock-Block" und im
  selben Satz "beides unter `self._lock`". Beides zugleich geht nur mit einem
  zweiten `with self._lock:` unmittelbar danach, und dazwischen laege ein
  Fenster: die Engine ist gebunden, der Zaehler steht noch auf null, und eine
  Freigabe aus einem anderen Thread duerfte in genau diesem Moment
  `gc.collect()` und `malloc_trim` auf dem Heap eines startenden Batches laufen
  lassen. Das ist der Zustand, den der Zaehler verhindern soll.
- **Fix:** Das Hochzaehlen steht im selben Lock-Block, in dem `engine` gebunden
  wird, und das Herunterzaehlen in einem `finally` mit eigenem Lock. Der
  Kommentar sagt, warum es dort steht.
- **Files modified:** backend/src/findling/embed/model.py
- **Commit:** `90f345a`

**3. [Rule 3 - Blocker] Baumhash der Messwerkstatt zweimal nachgezogen**

- **Found during:** Task 1 und Task 2
- **Issue:** `tests/test_measurement_scripts.py` haelt einen sha256 ueber alle 54
  Dateien des Python-Pakets. `embed/model.py` hat in beiden Tasks seine Bytes
  geaendert; die Datei steht nicht in `files_modified` des Plans, aber die
  Projektregel verlangt den Nachzug im selben Commit.
- **Fix:** `PACKAGE_TREE_HASH_TODAY` auf
  `99e4899cf7be43711169f180ae0fab6c5b0df50ada46a8d8daf475ef866e1938` (Task 1)
  und danach auf
  `d339fb07db1e8b6d7b23460308a8effcab3ff1bd4c0e99838e75efb23f90ff81` (Task 2),
  je mit einem Absatz in der Form der fuenf vorhergehenden Eintraege. Die
  Dateizahl bleibt 54.
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Commits:** `90f345a`, `8055795`

### Bewusst nicht getan

- **Keine Identitaetspruefung in `release()`.** Abschnitt 4.3 Punkt 2 des
  Research nennt sie, der Plan schreibt sie nicht vor, und heute kann sie nicht
  greifen: jeder Weg, der eine Engine laedt, geht durch `_embed` und erhoeht im
  selben Lock-Block den Aktivitaetszaehler. Sie wird gebraucht, sobald das
  Nachwaermen aus MEM-03 neben der Entlade-Aufgabe laeuft, also in 14-06 oder
  14-07. Als Hinweis fuer den dortigen Planer festgehalten, nicht als
  stillschweigende Auslassung.
- **`REQUIREMENTS.md` unberuehrt** (siehe naechster Abschnitt).

## Requirements

`requirements: [MEM-02, MEM-03]` steht im Frontmatter des Plans. Keines der
beiden wird hier abgehakt, und das folgt der Lehre aus 14-01 und 14-04:

- **MEM-02** verlangt, dass nach Ablauf der Frist **beide** Halter frei sind,
  belegt an der Rueckkehr zur Grundlast. Der Halter der Indexseite kann seit
  14-04 loslassen, der der Suchseite seit diesem Plan, aber **niemand ruft
  beide**. Der Aufrufer ist 14-07.
- **MEM-03** hat zwei Haelften. Die untere, `may_load`, steht jetzt. Die obere,
  das Nachwaermen im Hintergrund samt Single-Flight, liegt in 14-06 und 14-08.
  Ein halbes Requirement abzuhaken heisst, es nie wieder anzusehen.

## Threat Flags

Keine. Die Phase hat fuer genau diese Datei einen eigenen Threat-Block, und die
fuenf Eintraege sind umgesetzt: T-14-14 (Literal statt Pfad, enger `except`),
T-14-15 (Aktivitaetszaehler), T-14-16 (Sammeln und Trimmen ausserhalb des
Locks), T-14-17 (monotoner Zaehler, am Syntaxbaum gehalten), T-14-18 (nur der
Klassenname im Log). T-14-SC: keine neue Abhaengigkeit, `ctypes` und `gc` sind
Stdlib.

## Known Stubs

Keine. Alles, was dieser Plan baut, ist vollstaendig und getestet; dass es noch
keinen Aufrufer hat, ist die ausgeschriebene Absicht des Plans und kein Stub.

## Gates

| Gate | Ergebnis |
|---|---|
| `uv run ruff check .` | gruen |
| `uv run ruff format --check .` | gruen, 122 Dateien |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | gruen |
| `uv run pytest tests/test_embed_model.py -q` | 38 bestanden, 2 uebersprungen |
| `uv run pytest -q` (VOLLE Suite) | **2179 bestanden, 15 uebersprungen**, 179 s |

Kein PHP angefasst, also keine Ersatzpruefung noetig.

## Verification

| Punkt des Plans | Ergebnis |
|---|---|
| Alle sechs Gate-Stufen gruen | ja, Tabelle oben |
| `grep -c 'from findling.config' embed/model.py` | 0 |
| `grep -rn 'release()' backend/src/findling/` ausser der Definition | leer, dieser Plan verdrahtet nichts |
| `grep -c 'libc.so.6' embed/model.py` | 1, als Literal, nie aus `os.environ` |
| `except`-Zweig faengt nur `(OSError, AttributeError)` | ja, Zeile 206 |
| `_UNLOAD_COUNT = 0` genau einmal | ja, Zeile 161, plus ein `+= 1` in `release` |
| Nur die beiden Plan-Dateien veraendert | plus `tests/test_measurement_scripts.py`, siehe Abweichung 3 |

## Next

14-06 baut die Regel ueber diesem Schalter: `query_may_load`, `release_if_idle`
und das Single-Flight des Nachwaermens. Zwei Hinweise wandern dorthin: die
Identitaetspruefung in `release()` wird gebraucht, sobald das Nachwaermen neben
der Entlade-Aufgabe laeuft, und `last_use()` antwortet `None` fuer einen Halter,
der noch nie gearbeitet hat, was kein Leerlauf ist und in der Regel eigens
behandelt gehoert.

## Self-Check: PASSED

Alle drei genannten Quelldateien und die Zusammenfassung liegen auf der Platte,
alle sechs Commit-Hashes stehen in der Historie.
