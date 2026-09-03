---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 09
subsystem: ci
tags: [srch-04, parity, permissions, github-actions, groupfolders, security-gate]

# Dependency graph
requires:
  - phase: 02-suche-und-index
    provides: die Composite Action setup-test-nc, den Jobrumpf der Integrationsjobs und das Muster aus Share, Crawl und Warteschleife
  - phase: 03-aktualit-t-und-ocr
    provides: den ACL-Vorfilter, die Share-Ereignisse und den Teilbaum-Job, deren Wirkung dieser Job misst
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: 05-01, die Composite Action mit geprueften Eingaben (Muster fuer install-groupfolders)
provides:
  - scripts/ci/parity_diff.py, symmetrischer Mengenvergleich zweier fileid-Listen mit getrennter Benennung von missing und extra
  - CI-Job search-parity, sechs Rechteszenarien als Dauergate, mit ausdruecklichem Trefferdeckel und Negativprobe
  - Composite Action kann Team Folders installieren (install-groupfolders, ab Werk aus)
  - belegter Befund, dass ein Gruppenwechsel den ACL-Vorfilter nicht ueber die Share-Ereignisse erreicht
affects: [05-08 Versionsmatrix, 05-19 Gastnutzer-Sichtprobe, SRCH-04, Phase-Review]

# Tech tracking
tech-stack:
  added:
    - nextcloud/groupfolders (Team Folders) in der CI-Instanz dieses einen Jobs, App Store zuerst, Release-Tarball als Ausweichweg
  patterns:
    - Ein Vergleichswerkzeug meldet beide Richtungen getrennt und benennt jede als das, was sie ist
    - Antivakuitaetsklausel als Pflichtargument (--expect-min) statt als Kommentar
    - Negativprobe mit umgekehrtem Exitcode als eigener Schritt, damit das Gate nachweislich rot werden kann
    - Ein CLI-Werkzeug wird im Test als Unterprozess gefahren, weil Exitcode und Ausgabe der Vertrag sind

key-files:
  created:
    - scripts/ci/parity_diff.py
    - backend/tests/test_parity_diff.py
  modified:
    - .github/workflows/integration.yml
    - .github/actions/setup-test-nc/action.yml
    - .planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md

key-decisions:
  - "Ein Gruppenwechsel loest kein Share-Ereignis aus, also gibt es keinen Teilbaum-Job anzustossen: Szenario 5 misst stattdessen zuerst die Paritaet bei absichtlich veraltetem Vorfilter und bringt ihn danach mit einem Crawl-Durchgang nach, mit Deadline abgewartet"
  - "limit=100 steht woertlich in ask() statt in einer Variablen, weil es dieselbe Zahl ist wie der hochgesetzte Serverdeckel und beide eine Entscheidung sind"
  - "Der Test faehrt parity_diff.py als Unterprozess statt es ueber den Pfad zu importieren: der Exitcode ist der Vertrag, den der Job benutzt"
  - "Ordnernamen tragen einen Bindestrich und damit nie einen Marker, weil die native Antwort auch Ordner enthaelt und ein Ordner keine fileid im Findling-Index hat"
  - "Der Job haengt am Ende der Datei, damit die vier bestehenden Jobs zeilenweise unveraendert bleiben (0 entfernte Zeilen gegen den Ausgangsstand)"

patterns-established:
  - "Antivakuitaet als Pflichtargument: ein Vergleich ohne Inhalt ist ein eigener Fehlschlag mit eigenem Exitcode, nicht ein Erfolg"
  - "Jede Rechte-Feststellung wird in beide Richtungen gestellt: der Satz haengt an der Kombination aus 'findet seines' und 'findet fremdes nicht'"
  - "Eine neue Eingabe der Composite Action wird gegen eine feste Werteliste geprueft und ist ab Werk aus (Sec-L7, Muster aus 05-01)"

requirements-completed: [SRCH-04]

# Metrics
duration: 55min
completed: 2026-09-03
---

# Phase 5 Plan 09: Rechte-Paritaetstest als Dauergate Summary

**Findling zeigt einem Nutzer ab jetzt nachweisbar genau die Dateien, die die native Nextcloud-Suche demselben Nutzer zeigt: sechs Rechteszenarien vergleichen zwei fileid-Mengen in beide Richtungen, ein verpasster Treffer und ein zusaetzlicher Treffer werden getrennt benannt, und ein eigener Schritt belegt, dass das Gate wirklich rot wird.**

## Performance

- **Duration:** ca. 55 min
- **Tasks:** 3 von 3
- **Files modified:** 5 (2 neu, 3 geaendert)
- **Commits:** 4 Aufgaben-Commits plus dieser Abschluss

## Accomplishments

- **Der Mengenvergleich ist ein Werkzeug mit eigener Pruefung geworden.** `scripts/ci/parity_diff.py` liest aus zwei OCS-Antworten die Menge der `ocs.data.entries[].attributes.fileId`, bildet `missing` als native minus findling und `extra` als findling minus native, und schreibt fuer jede Richtung eine eigene Zeile, die sagt, was der Fall bedeutet: ein verpasster Treffer ist ein Funktionsfehler, ein zusaetzlicher Treffer ein Sicherheitsfehler an der Rechtegrenze. Neun Testfaelle in `backend/tests/test_parity_diff.py` decken beide Richtungen, beide gleichzeitig, den leeren Vergleich, die kaputte Antwort, die Abwesenheit von Pfaden und Titeln in der Ausgabe und die Beschraenkung auf die Standardbibliothek ab.
- **Zwei Wege, auf denen der Test gruen werden koennte, ohne etwas zu beweisen, sind zugemauert.** `--expect-min` ist Pflicht: zwei leere Mengen sind nur mit ausdruecklicher Nullerwartung ein Erfolg, und uebereinstimmende Mengen unterhalb der Erwartung enden als `parity inconclusive` mit eigenem Exitcode. Eine Antwort, die kein gueltiges JSON ist oder die Struktur nicht hat, wird nie zur leeren Menge, sondern zu einem dritten Exitcode mit der Nennung der betroffenen Seite.
- **Der Job `search-parity` fragt beide Provider mit demselben Aufruf.** Eine einzige `ask`-Funktion, deren einziger unterschiedlicher Parameter die Route ist (`providers/files/search` gegen `providers/findling/search`), jeweils mit `limit=100`; der Serverdeckel `unified_search_max_results_per_request` wird vorher auf 100 gesetzt und zurueckgelesen, mit einer eigenen Fehlermeldung, falls er es nicht ist.
- **Alle sechs Szenarien laufen, jedes in beide Richtungen.** Eigene Dateien, empfangener Share (plus die Gegenfrage nach dem nicht geteilten Ordner), entzogener Share (Empfaenger findet nichts, Eigentuemer weiterhin alles), Team Folder (zwei Gruppenmitglieder finden alles, der Aussenstehende nichts), Gruppenwechsel (entfernter Nutzer nichts, verbliebenes Mitglied alles), eingeschraenkter Nutzer (findet seinen einen Ordner, und keinen der vier fremden Marker).
- **Die Negativprobe ist ausgefuehrt und nicht nur eingebaut.** Der Schritt wurde lokal vollstaendig durchgespielt: eine hinzugefuegte fileid fuehrt zu `extra`, eine entfernte zu `missing`, und ein weiterer Lauf hat belegt, dass der Schritt selbst rot wird, wenn `parity_diff` in einem der beiden Faelle gruen bliebe.
- **Ein Befund, der ohne dieses Szenario unentdeckt geblieben waere:** ein Gruppenwechsel erreicht den ACL-Vorfilter nicht ueber die Share-Ereignisse. Siehe Deviations und DI-05-08.

## Task Commits

1. **Task 1 (RED): der Selbsttest des Vergleichs** - `f6253d5` (test)
2. **Task 1 (GREEN): das Werkzeug** - `1313da5` (feat)
3. **Task 2: der Job mit vier Szenarien und dem Trefferdeckel** - `03ed145` (feat)
4. **Task 3: Team Folder, Gruppenwechsel und die Negativprobe** - `ee6c0b0` (feat)

## Files Created/Modified

- `scripts/ci/parity_diff.py` (neu, 196 Zeilen) - CLI mit `--scenario`, `--native`, `--findling`, `--expect-min`. Vier Exitcodes: 0 Paritaet, 1 Paritaetsverletzung, 2 inhaltsloser Vergleich, 3 unlesbare Antwort. Nur Standardbibliothek (argparse, json, sys, pathlib), weil das Werkzeug mit dem Systempython des Runners neben curl und occ laeuft.
- `backend/tests/test_parity_diff.py` (neu, 9 Faelle) - faehrt das Werkzeug als Unterprozess. Die Antwort-Fixtures tragen in jedem Eintrag einen Pfad und einen Titel, damit der Fall "die Ausgabe enthaelt keinen Pfad" eine Messung und keine Absichtserklaerung ist.
- `.github/workflows/integration.yml` (+581 Zeilen, 0 entfernte gegen den Ausgangsstand) - neuer Job `search-parity` am Dateiende: Aufbau, Deckel, Marker-Fixtures, drei Shares, Team Folder, Crawl, Warteschleife, sechs Szenarien, Negativprobe, Fehlerdiagnose.
- `.github/actions/setup-test-nc/action.yml` (+61 Zeilen) - neue Eingabe `install-groupfolders` (ab Werk `false`, gegen die Werteliste geprueft) und ein Installationsschritt: `occ app:install groupfolders --force` zuerst, sonst der Release-Tarball der zur Serverversion passenden Hauptlinie (20 fuer NC 32, 21 fuer NC 33, 22 fuer NC 34, am 03.09.2026 gegen die Release-Liste von `nextcloud-releases/groupfolders` geprueft). Welcher Weg genommen wurde, steht im Log.
- `.planning/phases/.../deferred-items.md` - DI-05-07 bis DI-05-09.

## Decisions Made

- **Die Route statt der Provider-Id als Argument von `ask`.** Beide vollstaendigen Routen stehen damit woertlich in der Datei, was die Abnahmebedingung verlangt, und es bleibt trotzdem bei genau einem curl-Aufruf fuer beide Seiten. Zwei Aufrufe waeren die Stelle, an der die zwei Fragen anfangen sich zu unterscheiden.
- **`limit=100` steht woertlich, nicht in einer Variablen.** Es ist dieselbe Zahl, auf die der Serverdeckel gesetzt wird; ein Kommentar an beiden Stellen sagt, dass es eine Entscheidung ist. Eine dritte Stelle waere ein Ort mehr, an dem die Zahl auseinanderlaufen kann.
- **Ordnernamen mit Bindestrich, Marker ohne.** `parity-own` enthaelt nicht `parityown`. Das ist keine Kosmetik: die native Antwort enthaelt auch Ordner, ein Ordner hat eine fileid, und Findling indiziert keine Ordner, also waere ein nach seinem Marker benannter Ordner ein dauerhaft fehlender Treffer.
- **Die Marker-Dateien des Team Folders werden ueber WebDAV hochgeladen.** Ein Team Folder liegt nicht unter dem Home eines Nutzers, und sein Ablageort ist Sache der groupfolders-App. Ein Upload als Gruppenmitglied ist der ehrliche Weg und der einzige, der nicht veraltet, wenn diese App ihre Ablage aendert. Die Zahl der angekommenen Dateien wird zurueckgefragt.
- **Der Test faehrt das Werkzeug als Unterprozess.** Der Plan nannte einen Import ueber den Pfad; `conftest.py` kennt dafuer kein Muster, das Werkzeug liegt ausserhalb des `src`-Layouts, und der Vertrag, den der Job benutzt, ist der Exitcode und die Woerter in der Ausgabe. Ein Import haette eine Funktion geprueft und genau diesen Vertrag ungeprueft gelassen.
- **Kein OCR-Motor in diesem Job.** Jede Fixture ist eine Textdatei, denn der Marker muss fuer beide Seiten lesbar sein, und eine gescannte Seite ist gerade der Fall, in dem die native Seite bauartbedingt blind ist. Das spart die Installation und rund die Haelfte der Laufzeit der Nachbarjobs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Szenario 5 kann den Teilbaum-Job nicht anstossen, weil ein Gruppenwechsel keinen erzeugt**

- **Found during:** Task 3, beim Lesen von `ShareEventListener` und `SubtreeExpandJob`
- **Issue:** Der Plan (und die Recherche, Pattern 2, Szenario 5) nimmt an, das Vorfilter-Update nach einem Gruppenwechsel komme "ueber die Share-Ereignisse und den Teilbaum-Job". Das ist nicht so. `ShareEventListener` abonniert `ShareCreatedEvent`, `ShareDeletedEvent` und `ShareDeletedFromSelfEvent`, und keines davon feuert, wenn ein Nutzer eine Gruppe verlaesst: der Share hat sich nicht geaendert. Der Klassenkommentar des Listeners benennt diese Grenze ausdruecklich. Ein Schritt, der hier `background-job:worker SubtreeExpandJob` anstoesst und in einer Warteschleife auf dessen Wirkung wartet, haette auf einen Job gewartet, den niemand plant, und die Warteschleife waere bis zur Deadline gelaufen.
- **Fix:** Szenario 5 stellt jetzt zwei Fragen statt einer. Die erste wird sofort nach `group:removeuser` gestellt, waehrend der Vorfilter den entfernten Nutzer noch fuehrt; sie misst damit den Satz, auf dem die ganze Architektur ruht, naemlich dass der Vorfilter nicht die Rechtegrenze ist, sondern der Recheck in `Provider`. Waere dieser Satz falsch, erschiene der Fall genau hier als `extra`. Danach wird der Vorfilter ausdruecklich nachgezogen, und zwar mit einem Crawl-Durchgang: er schreibt die Zugriffsliste jeder Datei aus dem Mount-Cache neu, also aus derselben Quelle, die auch der Ereignisweg liest. Abgewartet wird mit Deadline und laufender Ausgabe, kein Schlafbefehl auf Verdacht. Erst danach die zweite Frage, plus die Gegenrichtung fuer das verbliebene Gruppenmitglied.
- **Warum das kein Fehlschlag des Jobs ist:** Der Plan sagt, ein anders ausfallendes A7 sei ein Befund und der Job solle dann fehlschlagen. Fehlschlagen muesste er, wenn die Paritaet verletzt waere; sie ist es nicht, weil der Recheck den Fall traegt. Der Befund ist die Ursache der Verzoegerung, nicht eine Verletzung von D-21, und er ist als DI-05-08 aufgeschrieben statt als rote Zeile.
- **Files modified:** `.github/workflows/integration.yml`
- **Verification:** Quelltext gelesen (`php/lib/Listener/ShareEventListener.php`, Zeilen 46 bis 52 und 86 bis 99); die Ereignisliste der App enthaelt keinen Gruppen-Listener.
- **Committed in:** `ee6c0b0`

**2. [Rule 2 - Missing Critical] Die Composite Action hatte den vorgesehenen Weg fuer groupfolders noch nicht**

- **Found during:** Task 3, beim Lesen von `action.yml`
- **Issue:** Der Plan verweist auf "die Eingabe fuer groupfolders aus Plan 05-01". 05-01 hat `register-exapp` und `nextcloud-host` ergaenzt, eine Eingabe fuer groupfolders gibt es nicht, und es gibt in der Action auch keinen Installationsweg fuer eine Nextcloud-App aus dem Store, an dem man sich haette entlanghangeln koennen.
- **Fix:** Eingabe `install-groupfolders` nach dem Muster der beiden anderen: gegen die Werteliste `true|false` geprueft, ueber `env:` in die Shell gereicht, ab Werk `false`, und der Installationsschritt haengt an `if: inputs.install-groupfolders == 'true'`. Damit installieren die vier bestehenden Jobs sie nicht, was durch ihre unveraenderten Aufrufe belegt ist.
- **Files modified:** `.github/actions/setup-test-nc/action.yml`
- **Verification:** YAML laedt, die Eingabe hat den Vorgabewert `false`, die Aufrufe der vier bestehenden Jobs sind unveraendert (`git diff` gegen den Ausgangsstand zeigt fuer sie keine Zeile).
- **Committed in:** `ee6c0b0`

**3. [Rule 3 - Blocking] Der Testrahmen des Werkzeugs, weil das Repo kein Muster dafuer hat**

- **Found during:** Task 1
- **Issue:** Der Plan gibt vor, der Test importiere das Werkzeug ueber den Pfad, und verweist auf `conftest.py`. Dort steht kein solches Muster; das Repo hat bisher nur ein Skript unter `scripts/ci/` und keinen Test dazu. Ein Import ueber `importlib.util.spec_from_file_location` waere zudem mit dem pyright-Gate im Streit, weil ein Attributzugriff auf `ModuleType` in `basic` als Fehler gilt.
- **Fix:** Der Test faehrt das Werkzeug mit `sys.executable` als Unterprozess (`# noqa: S603 - an argument list, never a shell`, das vorhandene Muster aus `extract/ocr.py`) und prueft Exitcode und Ausgabe.
- **Files modified:** `backend/tests/test_parity_diff.py`
- **Verification:** `ruff`, `ruff format`, `pyright`, `vulture` und die 879 Tests der Gesamtsuite sind gruen.
- **Committed in:** `f6253d5`

---

**Total deviations:** 3 auto-fixed (1 falsche Annahme im Plan mit Quelltextbeleg, 1 fehlende Vorarbeit, 1 blockierender Rahmen)
**Impact on plan:** Ohne die erste waere Szenario 5 ein Schritt geworden, der bis zu seiner Deadline auf einen nie geplanten Job wartet und danach eine Aussage macht, die er nicht gemessen hat. Die beiden anderen sind Handwerk.

## Issues Encountered

- **Die Abnahmebedingung verlangt beide Routen woertlich in der Datei.** Die erste Fassung baute die URL aus einer Provider-Id zusammen (`providers/$1/search`), womit weder `providers/files/search` noch `providers/findling/search` im Text stand und die automatische Pruefung des Plans fehlschlug. Aufgeloest, indem `ask` die vollstaendige Route bekommt: beide Zeichenketten stehen jetzt woertlich da, und es bleibt bei einem einzigen curl-Aufruf.
- **`ruff` haelt jede Konstante mit `SECRET` im Namen fuer ein Passwort (S105).** Die Fixture-Konstanten heissen jetzt `PRIVATE_PATH` und `PRIVATE_TITLE`.
- **Zwei Testfaelle waren in der RED-Runde aus dem falschen Grund gruen:** ein fehlendes Skript laesst den Interpreter mit Exitcode 2 abbrechen, was zufaellig dem Code fuer den inhaltslosen Vergleich entspricht, und eine leere Ausgabe enthaelt naturgemaess keinen Pfad. Beide Faelle verlangen jetzt zusaetzlich den Szenarionamen in der Ausgabe; danach waren alle neun rot.
- **`actionlint` ist auf dieser Maschine nicht vorhanden.** Ersatz: die Datei laedt als YAML, jeder `run`-Block des neuen Jobs ist einzeln mit `bash -n` geprueft, und die per Here-Dokument erzeugte `parity.sh` wurde materialisiert und ebenfalls geprueft.

## Offene Verifikation

- **Der CI-Lauf des Jobs `search-parity` ist noch nicht gesehen worden (DI-05-07).** Aus demselben Grund wie DI-05-01: der Zweig ist nur lokal, und `workflow_dispatch` bietet nur Workflows des Vorgabezweigs an. Ersatzbelege siehe unten. Offen bleiben genau die Teile ohne lokales Gegenstueck: dass `occ app:install groupfolders` auf dem Runner durchgeht, dass `occ config:app:set --type=integer` die Option kennt, und die tatsaechlichen Trefferzahlen der sechs Szenarien.
- **Was stattdessen ausgefuehrt wurde:** die neun Faelle des Werkzeugs plus die 879 Tests der Gesamtsuite; sieben Handaufrufe des Werkzeugs ueber die Abnahmebedingungen (gleiche Mengen mit `--expect-min 3` gleich 0, fehlende fileid gleich 1 mit `missing`, zusaetzliche fileid gleich 1 mit `extra`, zwei leere Mengen mit `--expect-min 1` gleich 2, dieselben mit 0 gleich 0, kaputtes JSON gleich 3); ein Durchlauf von `compare` gegen einen curl-Ersatz, der belegt, dass eine Paritaetsverletzung den Schritt mit Exitcode 1 abbricht; und der Negativprobe-Schritt vollstaendig, mit echtem `jq` und echtem `parity_diff.py`, in beiden Richtungen, samt der Gegenprobe, dass der Schritt rot wird, wenn das Werkzeug gruen bliebe.

## Known Stubs

Keine. Alle sechs Szenarien sind gebaut und keines ist als Platzhalter angelegt. Szenario 6b, der Gastnutzer, gehoert per D-22 ausdruecklich nicht in diese Matrix, sondern als manuelle Probe zu Plan 05-19.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: schema | `.github/actions/setup-test-nc/action.yml` | Mit `install-groupfolders: true` kommt ein zusaetzlicher Mount-Provider (`OCA\GroupFolders\Mount\MountProvider`) in die Testinstanz. Das ist gewollt und der Gegenstand von Szenario 4, veraendert aber, was der Crawl in diesem einen Job walkt; die Eingabe ist deshalb ab Werk aus. Kein Bezug zum Auslieferungsstand, die App wird nur in der CI-Instanz eines Laufs installiert. |

## User Setup Required

Keine. Der Job braucht keine Zugangsdaten, keine Netzfreigabe ausser dem Nextcloud App Store beziehungsweise GitHub Releases fuer groupfolders, und keine Konfiguration.

## Next Phase Readiness

- **SRCH-04 ist erfuellt, sobald der erste Lauf gesehen ist.** Der Job existiert, laeuft bei jedem Commit auf `php/**`, `backend/**`, `scripts/ci/**` und den Workflow selbst, und benennt je Szenario die Zahl der verglichenen fileids.
- **Plan 05-08 (Versionsmatrix) sollte wissen:** dieser Job bleibt bewusst bei `stable34`, und der Kommentar in seinem Kopf sagt warum. Wer die Matrix verbreitert, muss die groupfolders-Hauptlinien im Ausweichweg der Action mitziehen (20 fuer 32, 21 fuer 33, 22 fuer 34, 23 waere fuer NC 35 zu pruefen).
- **Plan 05-19 (Gastnutzer)** hat mit `parity.sh` und `parity_diff.py` bereits das Werkzeug fuer die manuelle Probe von Szenario 6b; die Prozedur ist dieselbe, nur der Nutzer ein anderer.
- **Blocker:** keiner.

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-03*

## Self-Check: PASSED

Alle sechs genannten Dateien liegen im Arbeitsbaum, alle fuenf Commits sind in
der Zweighistorie, und `.planning/STATE.md` sowie `.planning/ROADMAP.md` sind in
dieser Zweigspanne unveraendert (der Orchestrator schreibt sie). Die vier
bestehenden Jobs von `integration.yml` zeigen gegen den Ausgangsstand null
entfernte Zeilen.
