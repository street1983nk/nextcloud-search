---
phase: 14-modell-entladung-im-leerlauf
plan: 03
subsystem: infra
tags: [config, environment-variable, memory, onnxruntime, info-xml, appapi]

# Dependency graph
requires:
  - phase: 14-modell-entladung-im-leerlauf
    provides: Der Vorprueflauf 14-02 und der Owner-Entscheid "freigegeben" vom 19.09.2026
  - phase: 02-konfiguration
    provides: config.py als einziges Zuhause jeder Schranke, mit vier Lesern und der Hausregel "warnen statt anhalten"
provides:
  - settings().embed_idle_release_seconds, der Schalter aus MEM-01
  - Der dritte Leser _seconds_or_off_from_environment, bei dem die Null Antwort und nicht Tippfehler ist
  - Die sechzehnte Umgebungsvariable der info.xml, fuer Admins sichtbar
  - Der festgelegte Name FINDLING_EMBED_IDLE_RELEASE_SECONDS, an beiden Stellen byteweise gleich
affects: [14-04, 14-05, 14-06, 14-07, 15-boxmessung, 16-store-texte]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Wert, dessen Null eine Bedeutung traegt, bekommt einen eigenen Leser statt eines Bereichs, der die Null mitmeint"
    - "Der Unterschied zwischen aus und Tippfehler wird durch eine Mutationsprobe belegt und nicht durch einen Docstring behauptet"

key-files:
  created: []
  modified:
    - backend/src/findling/config.py
    - backend/tests/test_config.py
    - backend/tests/test_measurement_scripts.py
    - backend/appinfo/info.xml

key-decisions:
  - "Der Name ist FINDLING_EMBED_IDLE_RELEASE_SECONDS, nicht FINDLING_EMBED_IDLE_SECONDS: die 15 bestehenden Variablen nennen alle Wirkung und nicht nur Bedingung, und eine ausgelieferte Variable ist nicht mehr umbenennbar"
  - "Der Bereich heisst EMBED_IDLE_RELEASE_SECONDS_RANGE und nicht EMBED_IDLE_RELEASE_RANGE: der Plantext widersprach sich, die Hausform der Datei und das eigene Acceptance-Kriterium des Plans zeigen beide auf die erste Form"
  - "0 wird vor der Bereichspruefung durchgelassen; _bounded_int_from_environment ist fuer diese Variable aus beiden Richtungen falsch"
  - "Ab Werk 0, also aus, mit beiden Gruenden im Kommentar: der A/B-Beleg der einen Box-Anfahrt braucht beide Stellungen, und ungemessene Wiederaufwaerm-Kosten duerfen sich nicht selbst einschalten"
  - "FINDLING_EMBED_ENABLED wurde NICHT in die info.xml aufgenommen; der Befund steht als Kommentar fuer Phase 16"

patterns-established:
  - "Mutationsprobe als Abnahme eines Tests: der Leser wurde probeweise gegen _bounded_int_from_environment getauscht, genau ein Fall wurde rot, und das ist der Null-Fall"

requirements-completed: [MEM-01]

# Metrics
duration: 32min
completed: 2026-09-19
---

# Phase 14 Plan 03: Der Schalter FINDLING_EMBED_IDLE_RELEASE_SECONDS Summary

**Die Entladung hat ab jetzt genau einen benannten Schalter, er steht ab Werk auf aus, und die Null ist bei ihm keine kleine Zahl, sondern das Wort aus: ein eigener dritter Leser laesst sie vor der Bereichspruefung durch, damit ein Admin, der abschaltet, nicht die Funktion zurueckbekommt.**

## Performance

- **Duration:** 32 min
- **Started:** 2026-09-19T13:03:00Z
- **Completed:** 2026-09-19T13:35:00Z
- **Tasks:** 3 von 3
- **Files modified:** 4 (kein neues Modul, keine neue Abhaengigkeit)

## Accomplishments

### Der Namensdissens ist entschieden

STACK.md B.9 schlug `FINDLING_EMBED_IDLE_SECONDS` vor, ARCHITECTURE.md B
`EMBED_IDLE_RELEASE_SECONDS`. Gewaehlt ist
**`FINDLING_EMBED_IDLE_RELEASE_SECONDS`**, und die Begruendung kommt aus dem
eigenen Bestand statt aus Geschmack: die 15 bereits ausgelieferten Variablen der
info.xml nennen alle Wirkung und nicht nur Bedingung
(`FINDLING_RECONCILE_MIN_INTERVAL_HOURS`, `FINDLING_OCR_PAGE_SECONDS`), und eine
Variable, die einmal in einem Release stand, ist nicht mehr umbenennbar. Der Name
steht jetzt in `config.py` und in `appinfo/info.xml` byteweise gleich, was der
Kommentarblock jener Datei ausdruecklich verlangt.

### Die Null ist eine Antwort, nicht ein Tippfehler

`_bounded_int_from_environment` ist fuer diese Variable aus beiden Richtungen
falsch, und das ist der inhaltliche Kern des Plans:

| Bereich | Was passiert | Warum das falsch ist |
|---|---|---|
| `(0, 86400)` | `3` ist gueltig | Ein Container, der pausenlos laedt und entlaedt, und ueber die Zyklen schlechter wird, weil glibc `M_MMAP_THRESHOLD` dynamisch anhebt |
| `(60, 86400)` | `0` faellt auf den Default zurueck | Ein Admin, der abschalten will, bekommt die Funktion, und zwar ohne Fehlermeldung, weil stilles Zurueckfallen das Normalverhalten des Moduls ist |

Der neue Leser `_seconds_or_off_from_environment` beantwortet die Null **vor**
der Bereichspruefung. Damit darf der Bereich seine Untergrenze von 60 Sekunden
behalten, und der Aus-Zustand bleibt erreichbar. Alles andere folgt dem
Hausvertrag des Moduls: warnen mit dem Namen der Variablen, nie mit ihrem Wert,
und nie ein Container, der nicht startet (T-14-09, T-14-10).

Die acht Verhaltenszeilen des Plans sind alle belegt:

| Eingabe | Ergebnis | Warnung |
|---|---|---|
| nicht gesetzt | 0 | nein |
| `"0"` | 0 | **nein** |
| `"900"` | 900 | nein |
| `"  900  "` | 900 | nein |
| `"3"` | 0 | ja, mit Variablennamen |
| `"99999999"` | 0 | ja |
| `"neun"` | 0 | ja |
| `"-5"` | 0 | ja |

### Der Unterschied ist durch eine Mutationsprobe abgenommen

Ein Test, der nur zufaellig gruen ist, haelt nichts. Nach dem Schreiben der 14
Faelle wurde der Aufruf in `settings()` probeweise gegen
`_bounded_int_from_environment` getauscht und die Auswahl erneut gefahren:
**genau ein Fall wurde rot, und es war
`test_zero_is_the_off_position_of_the_idle_release_and_not_a_typo`.** Danach
wurde der Tausch zurueckgenommen und alle 14 liefen wieder gruen. Der Test hat
also Zaehne an genau der Stelle, an der der Plan sie verlangt.

### Ab Werk aus, mit beiden Gruenden im Kommentar

`EMBED_IDLE_RELEASE_SECONDS = 0`. Der Begruendungsabsatz nennt beide Gruende und
sagt bei beiden dazu, dass sie ablaufen und nicht ewig gelten: die eine bezahlte
Box-Anfahrt der Phase 15 muss das Merkmal gegen seine eigene Abwesenheit wiegen
und braucht dafuer beide Stellungen, und ein Merkmal, dessen
Wiederaufwaerm-Preis noch nicht gemessen ist, darf sich unter einer laufenden
und bereits eingestellten Installation nicht selbst einschalten. 900 s steht als
Vorschlagswert in der info.xml und ist bis zur Messung geraten; der Kommentar
sagt das.

### Die sechzehnte Variable

`backend/appinfo/info.xml` fuehrt jetzt 16 statt 15 Variablen. Der Eintrag traegt
`<default>0</default>`, nennt in der Beschreibung den Aus-Zustand, die Grenzen 60
und 86400 und den Vorschlagswert 900, und traegt **keine Messzahl der Ersparnis**
(Owner-Regel zu kurzen Produkttexten vom 07.09.2026). Ein Sammelkommentar
darueber haelt zwei Dinge fest: dies ist die erste `FINDLING_EMBED_`-Variable
dieser Datei, und `FINDLING_EMBED_ENABLED` wird hier **bewusst nicht**
mitgenommen, weil es ein Haertungskandidat und kein Requirement dieser Phase ist
und eine ausgelieferte Variable nie zurueckgenommen werden kann. Phase 16 findet
den Befund damit, statt ihn neu zu entdecken.

## Task Commits

1. **Task 1: Konstanten, Leser und Settings-Feld** - `584b24e` (feat)
2. **Task 2: Die Faelle des Lesers als Tests** - `b08725c` (test)
3. **Task 3: Die sechzehnte Variable in der info.xml** - `c85f826` (feat)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierender Widerspruch im Plan] Bereichsname auf die Hausform gebracht**

- **Found during:** Task 1
- **Issue:** Der Action-Block nennt die Konstante `EMBED_IDLE_RELEASE_RANGE`, das
  Acceptance-Kriterium desselben Tasks verlangt aber mindestens drei Zeilen mit
  `EMBED_IDLE_RELEASE_SECONDS` und nennt als dritte ausdruecklich "das Vorkommen
  im Bereichsnamen". Mit dem Namen aus dem Action-Block waren es zwei Zeilen, das
  Kriterium also unerfuellbar.
- **Fix:** Der Bereich heisst `EMBED_IDLE_RELEASE_SECONDS_RANGE`. Das ist auch die
  einzige Form, die die Datei kennt: `EMBED_TOKEN_CAP` / `EMBED_TOKEN_CAP_RANGE`,
  `EMBED_BATCH_SIZE` / `EMBED_BATCH_SIZE_RANGE`, `RECONCILE_HOUR` /
  `RECONCILE_HOUR_RANGE`. Der Plantext war der Ausreisser, nicht das Kriterium.
- **Files modified:** backend/src/findling/config.py
- **Verification:** `grep -c 'EMBED_IDLE_RELEASE_SECONDS' backend/src/findling/config.py` = 3
- **Commit:** `584b24e`

**2. [Rule 3 - Blocker] Baumhash der Messwerkstatt nachgezogen**

- **Found during:** Task 2, bei der vollen Suite
- **Issue:** `tests/test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_python_package`
  wurde rot. Das Gate haelt einen sha256 ueber alle 54 Dateien des Python-Pakets
  fest, und `config.py` hatte seine Bytes geaendert. Die Datei steht nicht in
  `files_modified` des Plans.
- **Fix:** `PACKAGE_TREE_HASH_TODAY` auf
  `9a8c8354ceeb1c2f88e06cca954de794de0576b23d97bec8f5ef8b4f328c6c20` gesetzt, mit
  einem Absatz in der Form der vier vorhergehenden Eintraege, der nennt, welche
  Datei sich geaendert hat und warum. Die Dateizahl bleibt 54, keine Datei kam
  und keine ging. Die historische Zahl `PACKAGE_TREE_HASH` aus den Rohdaten des
  Messlaufs bleibt unberuehrt; genau dafuer sind es zwei Konstanten.
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Verification:** volle Suite gruen, 2146 bestanden
- **Commit:** `b08725c`

**3. [Rule 2 - Fehlende notwendige Funktionalitaet] Die neue Variable in ENVIRONMENT**

- **Found during:** Task 2
- **Issue:** `test_config.py` fuehrt ein Tupel `ENVIRONMENT` mit jeder Variablen,
  die das Modul liest, und leert sie vor jedem Test. Der Kommentar darueber sagt
  den Grund: eine Entwicklermaschine, die eine davon exportiert hat, faerbt sonst
  einen roten Test gruen. Der Plan erwaehnt das Tupel nicht.
- **Fix:** `FINDLING_EMBED_IDLE_RELEASE_SECONDS` in `ENVIRONMENT` aufgenommen,
  hinter `FINDLING_EMBED_MODEL_DIR`.
- **Files modified:** backend/tests/test_config.py
- **Commit:** `b08725c`

**4. [Rule 1 - Owner-Regel] Beschreibung der info.xml gekuerzt**

- **Found during:** Task 3
- **Issue:** Der erste Entwurf hatte 673 Zeichen. Die 15 Nachbareintraege liegen
  zwischen 69 und 605, und der Plan verlangt "in Laenge und Tonlage der
  Nachbareintraege".
- **Fix:** Der Schlusssatz zur Begruendung der Untergrenze faellt weg; er stand
  nicht im vom Plan verlangten Inhalt und die Begruendung steht ohnehin am
  Konstantenblock in `config.py`. Jetzt 544 Zeichen, Grenzen und Vorschlagswert
  weiterhin genannt.
- **Files modified:** backend/appinfo/info.xml
- **Commit:** `c85f826`

**Total deviations:** 4 auto-fixed (2x Rule 3, 1x Rule 2, 1x Rule 1).
**Impact:** Keiner auf den Umfang. Drei der vier sind Gates und Konventionen des
Bestands, die der Plan nicht kannte; der vierte ist eine Owner-Regel. Keine
Architekturfrage, kein Rule-4-Fall.

## Authentication Gates

Keine.

## TDD Gate Compliance

Der Plan schneidet die Tasks nach Dateien: Task 1 darf ausschliesslich
`config.py` anfassen, Task 2 ausschliesslich `test_config.py`. Damit ist die
Commitfolge `test` vor `feat` nicht herstellbar, ohne die Dateigrenzen des Plans
zu brechen. Die Folge ist deshalb `feat` (584b24e) vor `test` (b08725c), und der
RED-Zustand wurde stattdessen vor Task 1 ausdruecklich festgestellt und
protokolliert:

```
hat Feld: False
hat Leser: False
hat Konstante: False
```

Die eigentliche Absicht der roten Stufe, ein Test der ohne die Umsetzung
scheitert, ist durch die Mutationsprobe oben belegt und damit staerker als eine
Reihenfolge von Commits: der Null-Fall wurde rot, sobald der Leser getauscht
wurde.

## Verification

| Punkt des Plans | Ergebnis |
|---|---|
| 1. ruff check, ruff format --check, pyright, vulture | gruen (122 Dateien formatiert, 0 Fehler, keine Funde) |
| 2. Volle Suite `uv run pytest -q` aus backend/ | **2146 bestanden, 15 uebersprungen** |
| 3. info.xml parst, 16 Variablen | 16, letzte ist FINDLING_EMBED_IDLE_RELEASE_SECONDS |
| 4. grep nennt beide Dateien | info.xml 1, config.py 1 |
| 5. Nichts unter embed/, worker/, api/, main.py | bestaetigt ueber `git diff --name-only` der drei Commits |

Geaenderte Dateien der drei Commits, vollstaendig: `backend/appinfo/info.xml`,
`backend/src/findling/config.py`, `backend/tests/test_config.py`,
`backend/tests/test_measurement_scripts.py`.

## Issues Encountered

Keine offenen. Die vier Abweichungen oben sind alle geschlossen.

## Known Stubs

`settings().embed_idle_release_seconds` wird von niemandem gelesen. Das ist so
geplant und kein Stub im Sinne einer halben Umsetzung: der Plan sagt ausdruecklich
"Der Wert wird hier gelesen und von niemandem benutzt; die Nutzer kommen in 14-06
und 14-07". Der Schalter ist vollstaendig, seine Wirkung ist der naechste Bau.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Registers. Die drei Eintraege des Plans
sind abgedeckt:

| Threat | Umsetzung |
|---|---|
| T-14-08 (sehr kleine TTL) | Untergrenze 60 im Bereich, `"3"` und `"59"` fallen als Testfaelle auf 0 und warnen |
| T-14-09 (unlesbarer Wert stoppt den Container) | Der Leser wirft nie, jeder Fehlerpfad endet im Default plus Warnzeile |
| T-14-10 (Wert im Log) | Ein eigener Testfall prueft ueber `caplog.messages`, dass keine Meldung den gelesenen Wert traegt |
| T-14-SC (Abhaengigkeiten) | Keine neue Abhaengigkeit, `pyproject.toml` unberuehrt |

## Next Phase Readiness

Bereit fuer **14-04**. Der Schalter steht, sein Name ist festgelegt und an beiden
Stellen gleich geschrieben, und die Plaene 14-06 und 14-07 koennen
`settings().embed_idle_release_seconds` ohne weitere Entscheidung lesen.

Fuer Phase 16 liegt ein Befund als Kommentar in `backend/appinfo/info.xml`
bereit: `FINDLING_EMBED_ENABLED` existiert im Code und in `docs/admin-page.md`,
aber nicht in der info.xml.

## Self-Check: PASSED

Alle vier geaenderten Dateien liegen auf der Platte, alle drei Commits
(584b24e, b08725c, c85f826) stehen im Log, und die fuenf Verifikationspunkte des
Plans sind einzeln nachgefahren und oben protokolliert.
