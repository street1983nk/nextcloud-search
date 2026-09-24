---
phase: 18-schema-marken-und-umbauweg
plan: 10
subsystem: api
tags: [status, admin-ui, banner, l10n, rebuild, languages, LEX-03, LEX-06]

# Dependency graph
requires:
  - phase: 18-schema-marken-und-umbauweg
    provides: "Plan 18-09: rebuild_progress als Prozesswert, rebuild_the_index mit der Vorpruefung may_rebuild; Plan 18-06: RebuildVerdict mit needed_bytes und free_bytes; Plan 18-07: reset_read_side vor dem Tausch"
  - phase: 07-semantische-haelfte-sichtbar
    provides: "engineState als Vorbild eines Prozesswerts in GET /status und als Vorbild eines Paars aus Zahl und Zustand auf der Adminseite"
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "Bannerliste mit vier Schluesseln je Eintrag, Renderrahmen mit hidden und eigenem span, shown()/text() im Script"
provides:
  - "backend/src/findling/api/status.py mit languagesActive, languagesFilled, rebuildRunning, rebuildDone, rebuildTotal und rebuildBlockedBytes"
  - "backend/src/findling/api/resources.py mit filled_languages() hinter FILLED_TTL_SECONDS, geleert von reset_read_side"
  - "backend/src/findling/index/rebuild.py mit rebuild_blocked_bytes() als Prozesswert der verweigerten Vorpruefung"
  - "php/templates/admin.php mit findling-banner-rebuild und findling-banner-rebuild-space neben dem Reindex-Banner, plus findling-languages"
  - "Sechs Katalogdateien im Gleichstand bei 202 Schluesseln"
  - "Ratsche: Python-Baumhash 657ab156 bei 56 Dateien, PHP-Baumhash 65c14416 bei 66 Dateien"
affects: [18-11, 18-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine teure Messung fuer die Adminseite bekommt einen eigenen TTL neben _DEGRADED, nicht dessen Fenster: die Kosten und die Aenderungsgeschwindigkeit sind verschieden"
    - "Das Ereignis, das eine gecachte Aussage wirklich falsch macht, leert den Cache direkt, statt das Fenster abzuwarten (reset_read_side leert _FILLED)"
    - "Ein zweites Banner neben dem ersten statt eines Banners mit zwei Saetzen: zwei gegenlaeufige Ratschlaege duerfen sich nicht eine Id teilen"
    - "Vertragsscanner ueber Template und Script als Paar, mit Selbsttest gegen leere Proben, wie bei engineState und der zweiten Deckungszahl"

key-files:
  created: []
  modified:
    - backend/src/findling/api/status.py
    - backend/src/findling/api/resources.py
    - backend/src/findling/index/rebuild.py
    - backend/tests/test_status_endpoint.py
    - backend/tests/test_read_side.py
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
    - php/lib/Service/AdminViewService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/de.json
    - php/l10n/de.js
    - php/l10n/de_DE.json
    - php/l10n/de_DE.js
    - php/l10n/fr.json
    - php/l10n/fr.js
    - docs/l10n-french.md

key-decisions:
  - "languagesFilled steht in GET /status und nicht in der Diagnoseroute, gegen die Empfehlung der Recherche; der Beleg dafuer steht unten samt Kostenvorbehalt und TTL-Cache"
  - "Sechs neue Felder statt der im Plan genannten vier beziehungsweise fuenf; die Verhaltensbeschreibung nennt sechs, und rebuildBlockedBytes ist ohne die drei Fortschrittswerte nicht lesbar"
  - "Keines der sechs Felder geht ueber optionalCounter(): jedes hat einen Ruhewert, den ein Container im Ruhezustand meldet, also traegt null keine Unterscheidung mit Folge"
  - "rebuild_blocked_bytes() ist ein Prozesswert nach dem Vorbild von rebuild_progress(), kein Feld im RebuildVerdict: der Verdikt wird pro Lauf gebaut, die Adminseite fragt lange danach"
  - "Der Fehlbetrag ist needed + floor - free und nicht needed - free: wer genau die Differenz zum Bedarf freigibt, kauft sich einen pausierten Indexer"
  - "Der $size-Formatter ist im Template nach oben gewandert statt ein zweites Mal geschrieben zu werden"

patterns-established:
  - "Ein neuer Cache im Lesepfad wird in derselben Aenderung in reset_read_side eingetragen; der Beweis dafuer haengt am Zaehler eines gestellten Searchers und nicht an einer Zeitmessung"
  - "Der Vertragstest gegen ein neues Bannerpaar prueft die Id in beiden Haelften und den Satz, der NICHT darin steht, ueber eine Zaehlung statt ueber ein Verbot"

requirements-completed: [LEX-03, LEX-06]

# Metrics
duration: ~70min
completed: 2026-09-24
---

# Phase 18 Plan 10: Der Umbau wird sichtbar Summary

**Sechs neue Statusfelder tragen Sprachstand, Umbaufortschritt und Platzverdikt aus dem Container auf die Adminseite, wo zwei neue Banner neben dem Reindex-Banner stehen und der neue Text ausdruecklich keinen Vollreindex empfiehlt; drei Saetze in sechs Katalogdateien im Gleichstand, Schluesselzahl von 199 auf 202 mit Begruendungsabsatz.**

## Performance

- **Duration:** ~70 min
- **Completed:** 2026-09-24
- **Tasks:** 3 (Task 1 als TDD-Zyklus RED/GREEN, Task 2 und Task 3 je ein atomarer Commit)
- **Files created:** 0, **modified:** 17

## Accomplishments

- **Sechs neue Felder in `StatusResponse`, jedes mit Vorgabewert und Begruendungsabsatz.** `languagesActive` sagt ausdruecklich, dass es die Menge ist, unter der das Verzeichnis gebaut wurde, und nicht die, die der Container gerade wuenscht: wer die beiden verwechselt, liest waehrend eines Umbaus den Auftrag als erledigt. `languagesFilled` ist die Gegenprobe aus dem Index selbst. `rebuildRunning`, `rebuildDone` und `rebuildTotal` beschreiben den Lauf, `rebuildBlockedBytes` den Grund, warum er nicht lief.
- **Die Fuellstandsprobe sitzt hinter einem eigenen TTL.** `resources.filled_languages()` fragt `terms_with_prefix(feld, "", limit=1)` fuer die sechs Koerperfelder in Schemafeldreihenfolge, gecacht unter `index_dir` und unter `_LOCK`, nach der Bauart von `_DEGRADED`. Das Fenster ist `FILLED_TTL_SECONDS = 30.0` und nicht die fuenf Sekunden von `_DEGRADED`: die Messung ist teurer (ein Lauf ueber das ganze Termwoerterbuch je Feld) und die Antwort aendert sich langsamer (nur beim Tausch eines Verzeichnisses oder bei den ersten Dokumenten einer neuen Kette).
- **`reset_read_side()` leert den neuen Cache mit.** Das ist die Halbzeile, die das Fenster erst vertretbar macht: das eine Ereignis, das die Aussage wirklich falsch macht, ist der Tausch des Verzeichnisses, und der leert den Cache direkt, statt dreissig Sekunden lang die Ketten des stillgelegten Verzeichnisses zu melden.
- **Der Fehlbetrag der Vorpruefung wird veroeffentlicht.** `rebuild_blocked_bytes()` traegt `needed + floor - free`, gesetzt genau im Verweigerungszweig von `rebuild_the_index` und zu Beginn jedes Laufs auf 0 zurueckgesetzt. Der Boden steckt im Fehlbetrag und wird nicht herausgerechnet, mit dem Satz daneben, warum: wer genau die Differenz zum Bedarf freigibt, tauscht eine Verweigerung gegen einen pausierten Indexer.
- **Zwei neue Banner, neben dem Reindex-Banner und nie an seiner Stelle.** `findling-banner-rebuild` nennt den Fortschritt, sagt, dass die Suche weiter antwortet, und nennt bewusst keinen Befehl; `findling-banner-rebuild-space` nennt die fehlende Bytezahl und `FINDLING_REBUILD_FALLBACK=fullreindex` als den Weg, der keinen Platz braucht. Die Zaehlung von `occ findling:index --restart` in `admin.php` steht unveraendert auf 1.
- **Die Sprachdiagnose als eine Zeile mit beiden Listen.** `findling-languages` steht im Deckungsblock und traegt Namen statt Anzahlen, mit dem Kommentar an Ort und Stelle, warum das hier andersherum ist als im Log: eine Logzeile nennt den Variablennamen und nie den Wert, eine Seite, deren Leser entscheiden muss, ob eine Suche leer ausgehen kann, braucht die Codes.
- **Je neuer Schluessel genau eine Zeile in `AdminViewService::backend()`,** und ein Absatz, warum keiner davon ueber `optionalCounter()` geht: jeder hat einen Ruhewert, den ein Container im Ruhezustand meldet, also waere null eine Unterscheidung ohne Folge, bezahlt mit zwoelf Nullpruefungen in Template und Script.
- **Vier neue Vertragstests.** Beide Banner-Ids in Template und Script (mit Selbsttest gegen leere Proben, der fuenf beziehungsweise vier Befunde erwartet), die Zaehlung des Restart-Befehls, die Sprachdiagnose in allen drei Haelften, und genau eine Zeile je Schluessel im Service.
- **Sechs Kataloge im Gleichstand bei 202 Schluesseln.** Die Zahl wurde vor dem Eintragen erneut aus `de.json` gezaehlt (199, wie im Plan notiert), drei Saetze kamen dazu, `de_DE.*` ist byteweise die Kopie von `de.*`, Franzoesisch ist aus der Tabelle in `docs/l10n-french.md` gegossen und traegt dort den datierten Vorbehalt vom 24.09.2026.
- **Beide Baumhashes bewegt,** je mit einem neuen Absatz der Kommentarkette: Python 657ab156 bei unveraenderten 56 Dateien, PHP 65c14416 bei unveraenderten 66 Dateien.
- Volle Suite **2712 passed / 15 skipped**, alle vier Gates gruen.

## Task Commits

1. **Task 1 RED: die fuenf neuen Statusfelder, sechs fallende Faelle** - `8691499` (test)
2. **Task 1 GREEN: Sprachstatus, Umbaufortschritt und Platzverdikt in GET /status** - `eed23ff` (feat)
3. **Task 2: das sechste und siebte Banner, die Sprachzeile und die sechs neuen Schluessel** - `9e8f0e2` (feat)
4. **Task 3: sechs Kataloge im Gleichstand bei 202, beide Baumhashes bewegt** - `42dd961` (chore)

## Files Created/Modified

- `backend/src/findling/api/status.py` - sechs Felder in `StatusResponse`, gefuellt in `_volume()` und durchgereicht in `_of()`; `languagesActive` wird dort vom gespeicherten Merker ueberschrieben, wenn es einen gibt.
- `backend/src/findling/api/resources.py` - `FILLED_TTL_SECONDS`, `_FILLED`, `filled_languages()`; `reset_read_side()` leert den vierten Cache mit; `read_side()` fragt das Verzeichnis, bevor es `Index.exists` fragt.
- `backend/src/findling/index/rebuild.py` - `_BLOCKED_BYTES`, `rebuild_blocked_bytes()`, `_note_blocked_bytes()`; zwei Aufrufpunkte in `rebuild_the_index`.
- `backend/tests/test_status_endpoint.py` (814 auf 1022 Zeilen) - sechs neue Faelle samt `_CountingIndex`/`_CountingSearcher` und dem Helfer fuer eine zweite befuellte Kette.
- `backend/tests/test_read_side.py` - ein Fall fuer die Zustandsdatenbank ohne Indexverzeichnis.
- `backend/tests/test_admin_ui_contract.py` - `scan_rebuild_banners` mit Selbsttest, die Zaehlung des Restart-Befehls, die Sprachdiagnose ueber drei Dateien, genau eine Zeile je Schluessel, und die auf 202 gehobene Zahl mit dem fuenften Absatz.
- `backend/tests/test_measurement_scripts.py` - sechsundzwanzigster Absatz der Python-Kette, erster Absatz der PHP-Kette seit dem 21.09.2026, beide Hashes.
- `php/lib/Service/AdminViewService.php` - sechs Zeilen in `backend()`, Docblock von neunzehn auf fuenfundzwanzig Felder, Absatz zur Nicht-Ausnahme.
- `php/templates/admin.php` - vier neue Variablen, zwei Bannereintraege, die Sprachzeile, und der `$size`-Formatter nach oben verschoben.
- `php/js/admin.js` - `shown()` fuer beide Banner, `text()` fuer den Fortschrittssatz und die Platzwarnung, `text()` und `shown()` fuer die Sprachzeile.
- `php/l10n/*.json`, `php/l10n/*.js` - drei Saetze in allen sechs Dateien.
- `docs/l10n-french.md` - drei Tabellenzeilen und der Nachtrag vom 24.09.2026.

## Decisions Made

- **Begruendete Abweichung von 18-RESEARCH.md, mit Beleg.** Die Recherche empfiehlt, `languagesFilled` nicht in `GET /status` zu fuehren, weil `/status` "bei jedem Tastendruck der Unified Search" mitlaufe. Am Baum vom 24.09.2026 nachgeprueft: `grep -rn "'/status'" php/lib backend/src` liefert genau einen Aufrufer, `AdminViewService.php`, also die Adminseite; die Unified Search laeuft ueber `/search` und `/snippets`. Der Kostenvorbehalt der Recherche bleibt trotzdem gueltig, weil die Adminseite alle fuenf Sekunden pollt und die Probe ueber das ganze Termwoerterbuch jedes Feldes laeuft, und genau deshalb liegt die Probe hinter `FILLED_TTL_SECONDS`.
- **Sechs Felder und nicht fuenf.** Der Plan nennt an einer Stelle vier, an einer anderen fuenf; die Verhaltensbeschreibung von Task 1 nennt `languagesActive`, `languagesFilled`, `rebuildRunning`, `rebuildDone`, `rebuildTotal` und `rebuildBlockedBytes`, also sechs. Umgesetzt sind sechs, weil `rebuildBlockedBytes` ohne die drei Fortschrittswerte nicht lesbar ist: dieselbe Null bedeutet "kein Umbau noetig" und "Umbau laeuft gerade", und erst `rebuildRunning` trennt die beiden.
- **`rebuild_blocked_bytes()` ist ein Prozesswert und kein Feld im `RebuildVerdict`.** Das Verdikt entsteht einmal je Lauf und ist nach der Rueckkehr von `rebuild_the_index` nicht mehr erreichbar; die Adminseite fragt Stunden spaeter. Ein Wert auf der Platte waere die Zahl, die dem Volume widersprechen kann, was derselbe Einwand ist, den `rebuild_progress()` gegen einen Zaehler in `state.db` erhebt.
- **Die Vorgabe wird zu Beginn des Laufs zurueckgesetzt und danach nicht wieder.** Eine Verweigerung steht bis zum naechsten Start, weil nichts dazwischen sie unwahr macht: der Umbau wird einmal je Start versucht, und ein Banner, das nach dreissig Sekunden verschwindet, ist genau dann weg, wenn der Admin wieder auf die Seite sieht.
- **Der `$size`-Formatter ist nach oben gewandert.** Die Platzwarnung steht in der Bannerliste von Block eins, die gebaut wird, bevor die Variablen von Block zwei existieren. Ein zweiter Verschluss mit derselben Einheitentabelle waere genau die Drift, gegen die der erste geschrieben wurde; der Kommentar an der Stelle sagt das.
- **Zwei Banner statt eines mit zwei Saetzen.** Laufender Umbau und verweigerter Umbau treten nie zugleich auf, aber sie verlangen Gegensaetzliches vom Leser (warten gegen handeln), und ein Banner, dessen Satz zwischen den beiden wechselt, haette eine Id fuer zwei Ratschlaege.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `read_side()` konnte werfen, obwohl ihr Vertrag genau das ausschliesst**

- **Found during:** Task 1, beim ersten gruenen Lauf der Statusfaelle
- **Issue:** `Index.exists(str(pfad))` wirft `ValueError("Directory does not exist")` fuer einen Pfad, den es nicht gibt, statt `False` zu antworten. Die Kurzschlussbedingung `not state_db.is_file() or not Index.exists(...)` erreicht diesen Aufruf, sobald eine Zustandsdatenbank da ist, und das `try` darunter beginnt eine Anweisung zu spaet. Ein Volume in genau diesem Zustand ist gewoehnlich (ein Kill zwischen dem ersten Zustandsschreiben und dem ersten Commit hinterlaesst es), und die Unified Search fragt alle Anbieter parallel: ein Anbieter, der wirft, kostet dem Nutzer die ganze Suche. Sichtbar wurde es, weil `/status` diese Funktion ab jetzt fragt; drei vorhandene Statusfaelle fielen daran rot.
- **Fix:** Das Verzeichnis wird gefragt, bevor `Index.exists` gefragt wird, in zwei getrennten Zweigen mit je einem Satz dazu.
- **Files modified:** `backend/src/findling/api/resources.py`, `backend/tests/test_read_side.py` (Regressionsfall)
- **Commit:** `eed23ff`

**2. [Rule 2 - Missing critical functionality] Der neue Cache haette den Tausch ueberlebt**

- **Found during:** Task 1, beim Schreiben von `filled_languages`
- **Issue:** Der Plan nennt den TTL-Cache, nicht seine Leerung. `reset_read_side()` leert `_OPEN`, `_MARKS` und `_DEGRADED`, weil alle drei das Indexverzeichnis beschreiben und einen `rename` ueberleben. `_FILLED` ist von den vieren der, den ein Umbau am direktesten falsch macht: der Lauf existiert, um neue Ketten zu fuellen, und ohne die Leerung haette die Adminseite dreissig Sekunden lang die Ketten des stillgelegten Verzeichnisses gemeldet, also genau in dem Moment das Falsche, in dem die Zeile gelesen wird.
- **Fix:** `_FILLED = None` in `reset_read_side()`, Docstring erweitert, und der Testfall prueft es ueber den Zaehler statt ueber die Uhr.
- **Files modified:** `backend/src/findling/api/resources.py`, `backend/tests/test_status_endpoint.py`
- **Commit:** `eed23ff`

**3. [Rule 3 - Blocking] `$size` war in Block eins nicht erreichbar**

- **Found during:** Task 2
- **Issue:** Die Platzwarnung gehoert in die Bannerliste von Block eins, der `$size`-Verschluss stand unter den Variablen von Block zwei, also mehrere hundert Zeilen spaeter.
- **Fix:** Der Verschluss steht jetzt neben `$count`, mit dem Absatz, warum er umgezogen ist.
- **Files modified:** `php/templates/admin.php`
- **Commit:** `9e8f0e2`

### Bewusste Auslegung des Plans

- **Kein Feld ueber `optionalCounter()`.** Der Plan sagt: "Ein Wert, der 'der Container hat nichts gesagt' von 'der Container sagt null' trennen muss, geht ueber `optionalCounter()`." Geprueft, und keiner der sechs muss: jedes Feld hat einen Ruhewert, den ein laufender Container meldet, waehrend nichts passiert, und ein Container, der den Schluessel nicht kennt, ist aus Sicht der Seite in genau dieser Lage. Der Absatz steht im Docblock von `backend()`.
- **Die Sprachzeile steht im Deckungsblock und nicht im Diagnosebereich.** Der Plan nennt "den vorhandenen Diagnosebereich"; `#findling-diagnosis` ist die Einzeldateisuche und beantwortet eine Frage zu einer Datei, waehrend die Sprachzeile eine Aussage ueber den ganzen Index ist. Sie steht deshalb bei den anderen Aussagen ueber den Index, neben dem Deckungsgrad und ueber dem semantischen Block, wo auch die Zustandszeile der Engine steht.

## Was dieser Plan ausdruecklich nicht tut

- **Keine Messung der Probe auf einem grossen Index.** Der Kostenvorbehalt der Recherche (A4: `terms_with_prefix` mit leerem Praefix auf 52.000 Dokumenten) ist nicht nachgemessen worden; der TTL-Cache ist die Antwort darauf und nicht die Messung. Bleibt ein Kandidat fuer eine Messphase.
- **Kein PHPUnit-Fall fuer die sechs neuen Schluessel.** Auf dieser Maschine gibt es kein PHP; die PHP-Haelfte wird vom Python-Vertragsgate geprueft, das genau eine Zeile je Schluessel und die Id in beiden Haelften verlangt.
- **Keine Sichtprobe der Seite.** Dass das Fortschrittsbanner waehrend eines gestellten Umbaus erscheint und danach verschwindet, folgt aus dem Aufbau und aus `rebuild_progress()`, das nach dem Lauf in den Ruhezustand zurueckfaellt; die Sichtprobe gehoert an den Phasen-Checkpoint.
- **Keine Owner-Abnahme der drei franzoesischen Wortlaute.** Sie stehen mit datiertem Vorbehalt in `docs/l10n-french.md` und sind maschinell geprueft.

## Threat-Dispositionen

| Threat ID | Umsetzung |
|---|---|
| T-18-10-01 | Die neuen Werte sind Sprachcodes, Zahlen und ein Flag; `test_the_answer_carries_only_numbers_and_version_marks` laeuft unveraendert ueber die ganze Antwort und findet keinen Pfad und keinen Dokumentnamen |
| T-18-10-02 | Keine neue Route, keine Aenderung an `appinfo/info.xml`; die Felder reisen auf der vorhandenen ADMIN-Route |
| T-18-10-03 | `FILLED_TTL_SECONDS` mit Cache unter `_LOCK`, Schluessel `index_dir`; der Testfall zaehlt die Aufrufe am gestellten Searcher und belegt sechs statt zwoelf |
| T-18-10-04 | Beide Banner schreiben ihren Satz ueber `text(...)` in das eigene `span`, also ueber `textContent`; beide Zahlen laufen vorher durch `whole()` und `size()`, PHP-seitig durch `$count()` und `$size()`, und beide Sprachlisten durch `PlainText::bounded` in `AdminViewService::text()` |
| T-18-10-05 | Eigener Bannertext ohne `occ findling:index --restart`, und der Gate zaehlt das Vorkommen im Template auf genau 1 und im Script auf 0 |
| T-18-10-SC | Kein Paket installiert, keine Bewegung an `composer.json` oder `pyproject.toml` |

## Verification

- `uv run pytest -q` - 2712 passed, 15 skipped
- `uv run pytest -q tests/test_status_endpoint.py tests/test_read_side.py` - 63 passed
- `uv run pytest -q tests/test_admin_ui_contract.py` - 50 passed
- `uv run pytest -q tests/test_measurement_scripts.py` - 376 passed
- `uv run ruff check` - All checks passed
- `uv run ruff format --check` - 133 files already formatted
- `uv run pyright` - 0 errors, 0 warnings, 0 informations
- `uv run vulture` - keine Meldung
- `40b-baumhash.py backend/src/findling "**/*.py"` - `dateien: 56`, `baumhash: 657ab15620295e9716a7998efe213907fb1431ded81caf04e8fa8763b2519cce`
- `40b-baumhash.py php "**/*.php"` - `dateien: 66`, `baumhash: 65c1441674f431fab1936139ed583d232cc0c2e22c9563f3b5b29d1036c81357`
- Katalogzahl aus der Datei gezaehlt: `len(json.load(de.json)["translations"])` ergibt 202, die harte Zahl im Gate steht auf 202
- `cmp php/l10n/de.json php/l10n/de_DE.json` und `cmp php/l10n/de.js php/l10n/de_DE.js` - byteweise gleich
- `grep -c "occ findling:index --restart" php/templates/admin.php` - 1, unveraendert gegenueber dem Stand vor diesem Plan
- must_haves: `languagesActive` in `api/status.py` (viermal) und in `AdminViewService.php` (genau eine Zeile), `findling-banner-rebuild` in `templates/admin.php` und in `js/admin.js`
- RED-Lauf vor dem GREEN-Commit belegt: 17 fallende Faelle, davon sechs neue
- Keine Em-Dashes und keine En-Dashes in den 17 geaenderten Dateien (Zeichenpruefung auf U+2014 und U+2013)
- `git diff --diff-filter=D --name-only HEAD~4 HEAD` leer, keine Datei geloescht

## Known Stubs

Keine. Jedes der sechs Felder hat einen Produktivleser in derselben Aenderung, jeder neue Bannertext hat seinen Eintrag in allen sechs Katalogen, und keine Zeile der Seite zeigt einen Platzhalter.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat Models des Plans: keine neue Route, kein neues Schema, keine neue Vertrauensgrenze, kein neuer Netzpfad. Die einzige neue Leseoperation ist `terms_with_prefix` auf einem bereits geoeffneten Index dieses Containers.

## Self-Check: PASSED

- `backend/src/findling/api/status.py` enthaelt `languagesActive`, `languagesFilled`, `rebuildRunning`, `rebuildDone`, `rebuildTotal` und `rebuildBlockedBytes`
- `backend/src/findling/api/resources.py` enthaelt `FILLED_TTL_SECONDS` und `def filled_languages`
- `backend/src/findling/index/rebuild.py` enthaelt `def rebuild_blocked_bytes`
- `php/templates/admin.php` enthaelt `findling-banner-rebuild`, `findling-banner-rebuild-space` und `findling-languages`
- `php/js/admin.js` flippt beide Banner und schreibt beide Saetze
- Sechs Katalogdateien vorhanden, 202 Schluessel, Zwillinge byteweise gleich
- Commits `8691499`, `eed23ff`, `9e8f0e2`, `42dd961` im Log gefunden
- Keine Datei geloescht, Arbeitsbaum nach dem letzten Task-Commit sauber
