---
phase: 19-frageseite-freischalten
plan: 07
subsystem: ci
tags: [sprachbeweis, deploy-harp, arm64, ergebnisseite, textgate, ungegatet]

# Dependency graph
requires:
  - phase: 19-frageseite-freischalten
    provides: "field_plan_for(marks, index) und ReadSide.field_plan aus 19-03, also eine Instanz, die ihre Frage aus den gespeicherten Marken baut"
  - phase: 19-frageseite-freischalten
    provides: "die vier Formenpaare und der dritte Ketten-Ausschluss aus 19-06"
  - phase: 18-schema-und-umbau
    provides: "die sechs Koerperfelder im Schema und die Startwarnung ueber FINDLING_OCR_LANGUAGES"
provides:
  - ".github/workflows/deploy-harp.yml: die Entwicklerstrecke installiert mit de,en,es,it,nl,pt"
  - ".github/workflows/deploy-harp.yml: ein ungegateter Schritt mit vier Dateien, vier OCS-Suchen und vier Ergebnisseiten-Abrufen"
  - "backend/tests/test_language_proof_steps.py: das Textgate, das den Schritt ungegatet haelt"
  - "Der erste CI-Schritt dieses Repos, der die Route der Ergebnisseite ueberhaupt beruehrt"
affects: [19-08 spanischer Vorher-Nachher-Beweis, 19-09 Doku und Laufzeiteintrag]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Beweis ueber alle vier Matrixaeste steht in einem Schritt OHNE if, und ein Textgate haelt das fest"
    - "Die Vorbedingung steht zuerst: eine Probe, die auf der falschen Instanz laufen koennte, prueft die Instanz bevor sie irgendetwas behauptet"
    - "Die Zusicherung bezieht sich auf den Treffer und nie auf den Textauszug, weil ein reiner Sprachfeld-Treffer gemessen ohne Auszug zurueckkommt"
    - "Was der Beweis in die Nutzerablage legt, nimmt er wieder heraus, damit spaetere Zusicherungen ihren gemessenen Bestand behalten"

key-files:
  created:
    - backend/tests/test_language_proof_steps.py
  modified:
    - .github/workflows/deploy-harp.yml

key-decisions:
  - "Die Sprachvorgabe wird in der temporaeren info.xml der Entwicklerstrecke gesetzt und nirgends sonst: diese Strecke ist ungegatet, ihre Instanz baut den Index von Anfang an mit sechs Feldern, und der Store-Durchgang bleibt bei der ausgelieferten Vorgabe de,en"
  - "Der Ergebnisseiten-Abruf fragt ?query= und nicht das im Plan stehende ?term=, weil PageController::term() getParam('query') liest; mit ?term= haette der Schritt die leere Startseite geprueft und waere gruen gewesen, ohne etwas zu belegen"
  - "Die Akzente der niederlaendischen und der portugiesischen Beweisdatei stehen als Oktal-Escapes im printf, nicht als Bytes: deploy-harp.yml ist heute reines ASCII, und ein Sprachbeweis ist kein Grund, das zu beenden"
  - "Die vier Beweisdateien werden am Ende des Schritts wieder geloescht, damit die Drei-Term-Vorbedingung der Upgrade-Strecke ihren gemessenen Bestand behaelt"
  - "Die Vorbedingung liest die Adminuebersicht mit einem eigenen, im Schritt gebauten Leser, weil overview.sh erst im Schritt danach entsteht"

requirements-completed: []
# LEX-05 bleibt ungehakt, genau wie nach 19-06. Dieser Plan liefert den CI-Schritt;
# was noch fehlt, ist der gruene Lauf, und den holt 19-09 ein. Ein Haken hier waere
# eine Behauptung ueber einen Lauf, den es noch nicht gibt.

# Metrics
duration: 48min
completed: 2026-09-25
---

# Phase 19 Plan 07: Der ungegatete CI-Sprachbeweis Summary

**Ein Schritt ohne `if:` laedt vier Dokumente auf eine echte Nextcloud mit sechs Sprachen, findet je Sprache die Stammform ueber die gewoehnliche Unified Search und holt denselben Treffer noch einmal von der Ergebnisseite, die bis heute kein CI-Schritt dieses Repos beruehrt hatte**

## Performance

- **Duration:** rund 48 min
- **Started:** 2026-09-25T08:05:00Z
- **Completed:** 2026-09-25T08:53:00Z
- **Tasks:** 3
- **Files modified:** 2 (1 geaendert, 1 neu)

## Accomplishments

- **Die Entwicklerstrecke faehrt sechs Sprachen.** Der Schritt "Build the temporary info.xml that
  points at the local registry" bekommt einen vierten `sed`-Ausdruck, der `<default>de,en</default>`
  auf `<default>de,en,es,it,nl,pt</default>` setzt. Davor steht eine eigene Zeile, die abbricht, wenn
  die Zeichenkette nicht genau einmal in der Quelldatei steht (`grep -cF`, Befund mit `grep -n
  '<default>'` im Fehlerpfad). Die `grep -E`-Protokollzeile fuehrt die Sprachzeile jetzt neben
  Registry, Image und Tag, damit im Lauf steht, womit installiert wurde.
- **Die Quelldatei ist nachweislich unberuehrt.** `backend/appinfo/info.xml` steht in keinem der drei
  Commits, `grep -c '<default>de,en</default>'` ist dort weiterhin 1, und die vorhandene Zeile
  `git -C findling-src diff --quiet -- backend/appinfo/info.xml` bleibt stehen.
- **Die drei uebrigen `app_api:app:register`-Aufrufe der Entwicklerstrecke speisen alle aus der
  temporaeren Datei** und erben die Sprachmenge, also war nichts zu tun. Im Einzelnen: die Driftprobe
  baut sich `info-drift.xml` per `sed` aus `info-citest.xml` (Zeile 793 in der Fassung vor diesem
  Plan), "Uninstall 2" (1074) und "Uninstall 5" (1196) uebergeben `info-citest.xml` direkt. Der
  Store-Durchgang registriert mit `STORE_INFO_XML` aus dem signierten Archiv und bleibt bei `de,en`.
- **Der neue Schritt "Language proof, the four new chains answer on the ordinary search route" steht
  zwischen "Search over the ordinary OCS route" und "The drift probe both directions share" und
  traegt keine `if:`-Zeile.** Maschinell geprueft ueber den YAML-Baum: er ist Schritt 13 von 50, seine
  Schluessel sind genau `name` und `run`, seine Nachbarn sind die beiden genannten.
- **Die Vorbedingung steht zuerst und faellt geschlossen.** Der Schritt holt sich ein App-Passwort auf
  den zwei Wegen, die `overview.sh` weiter unten nimmt (occ-Unterbefehl, sonst die OCS-Route, weil
  stable33 den Unterbefehl nicht kennt), liest
  `index.php/apps/findling/admin/overview` und bricht ab, wenn `.backend.languagesActive` nicht
  woertlich `de,en,es,it,nl,pt` meldet. Ohne diese Zeile koennte der ganze Beweis ueber eine Instanz
  mit `de,en` laufen und trotzdem gruen aussehen.
- **Vier Dokumente, vier Formenpaare, je eines, das nur die eigene Kette zusammenfuehrt** (RESEARCH
  M-5 und M-6): es `alemana` gegen `alemanes` ueber `aleman`, it `informazione` gegen `informazioni`
  ueber `inform`, nl `beinvloed` mit Trema gegen `beinvloeden` ueber `beinvloed`, pt `paises` mit Akut
  gegen `pais` ueber `pais`. Alle vier Suchwoerter sind reines ASCII. Die uebrigen Woerter der vier
  Saetze ueberschneiden sich nicht untereinander, weshalb jede der vier Suchen die eine Datei benennen
  kann, die sie zurueckbringen muss.
- **Die Pollschleife hat die Bauart von "Store install 7".** Eigenes Budget
  `LANGUAGE_PROOF_BUDGET_SECONDS` im env-Block des Jobs, je Runde `php -f cron.php`, danach je noch
  offener Sprache eine OCS-Suche; die Schleife verlaesst sich, sobald alle vier antworten, und schlaeft
  nie vor der ersten Abfrage. Der Fehlerpfad gibt je offener Sprache die letzte Antwort aus, dazu den
  letzten Cron-Lauf und sechzig Zeilen Containerlog, und sagt ausdruecklich, dass ein gerissenes Budget
  ein Befund ist und kein Grund, es zu heben (T-06.1-52).
- **Die Zusicherung prueft `entries | length` und nie die Unterzeile des ersten Eintrags**, mit einem
  Absatz an der Stelle, der sagt warum (RESEARCH M-4: der Auszug wird aus `body_de` geschnitten, und
  eine Frage, die den Dokumentterm nur ueber die spanische Kette trifft, hat in der deutschen nichts zu
  markieren). Danach behauptet ein eigener Durchgang je Sprache den Dateinamen in
  `.ocs.data.entries[0].title`.
- **Die Ergebnisseite wird zum ersten Mal von der CI beruehrt**: vier Literalzeilen, je eine Sprache,
  `curl -u testuser:... 'http://localhost:8080/index.php/apps/findling/?query=<Suchwort>'`. Geprueft
  werden Statuscode und der Dateiname im HTML, nie der Textauszug. Siehe Deviation 1 zum Parameter.
- **`backend/tests/test_language_proof_steps.py` steht mit 519 Zeilen und 19 bestandenen Faellen.**
  Textgate ohne YAML-Abhaengigkeit, mit `_CLEAN` als sauberem Muster und `_GATED` und `_EXCERPT` als
  zwei gestellten Mustern, an denen die beiden tragenden Aussagen rot werden. Die zwei gegateten
  Schritte werden als Gegenbeispiel gelesen: verlieren sie ihre `if:`-Zeile, meldet das Gate, dass es
  selbst kaputt ist, und nicht, dass der Workflow heil ist.
- **Volle Suite 2850 bestanden / 15 uebersprungen** (vorher 2831/15), die vier Qualitaetsgates lokal
  gruen.

## Task Commits

1. **Task 1: Die Entwicklerstrecke faehrt sechs Sprachen** - `e7fcd0b` (ci)
2. **Task 2: Der ungegatete Sprachbeweis, vier Dateien, vier Suchen, vier Ergebnisseiten-Abrufe** - `251c86c` (ci)
3. **Task 3: Ein Textgate haelt den Schritt ungegatet** - `368ecf5` (test)

**Plan metadata:** siehe docs-Commit unten

## Files Created/Modified

- `.github/workflows/deploy-harp.yml` (GEAENDERT) - drei Stellen: der vierte `sed`-Ausdruck samt
  Vorpruefung und Kommentarblock im Schritt "Build the temporary info.xml" (+43 Zeilen), das Budget
  `LANGUAGE_PROOF_BUDGET_SECONDS` mit RE-MEASURE-Absatz im env-Block des Jobs, und der neue Schritt
  "Language proof, ..." mit 270 Zeilen zwischen der OCS-Suche und der Driftprobe (+326 Zeilen).
- `backend/tests/test_language_proof_steps.py` (NEU) - 519 Zeilen, 19 Faelle. Modulkopf,
  `PROOF_STEP`, `GATED_STEPS`, `DOCUMENTS`, `QUESTIONS`, `PAGE_CALL`, `CLAIMS`, der Schrittleser
  `collect_steps`, die drei Scanner (`scan_proof_step`, `scan_counter_sample`, `scan_matrix`), das
  zusammenfassende `scan`, neun Faelle gegen den echten Baum und zehn gegen die drei gestellten Muster.

Keine weitere Datei im Diff. `backend/src/findling` und `php/` sind nicht angefasst, also bleiben
`PACKAGE_TREE_HASH_TODAY`, `PACKAGE_FILES_TODAY` und `PHP_TREE_HASH_TODAY` unberuehrt; die Ratsche
ist nicht beruehrt worden. `backend/pyproject.toml` und `backend/uv.lock` stehen nicht im Diff, es ist
kein Paket installiert worden.

## Decisions Made

- **Die Sprachvorgabe steht in der temporaeren info.xml der Entwicklerstrecke.** Drei Gruende, alle
  drei im Kommentarblock des Schritts: die Strecke ist ungegatet und laeuft auf allen vier Aesten; die
  Instanz baut ihren Index von Anfang an mit sechs Koerperfeldern, der Beweis kostet also keine
  Umbauzeit und wiederholt nicht die Aussage von "Store upgrade 6"; und der Store-Durchgang bleibt
  unberuehrt, weil er aus dem signierten Archiv registriert.
- **`?query=` statt `?term=`.** Siehe Deviation 1. Der Parameter ist der einzige Punkt, an dem der Plan
  sich am Code geirrt hat, und der Irrtum waere still gewesen: `?term=` antwortet mit 200 und der
  leeren Startseite.
- **Die Akzente als Oktal-Escapes.** `deploy-harp.yml` enthaelt heute kein einziges Nicht-ASCII-Zeichen
  (maschinell geprueft). `\303\257` und `\303\255` schreiben dieselben UTF-8-Bytes in die Datei, die
  der Container liest, ohne diese Eigenschaft der Workflow-Datei aufzugeben. Der Kommentar nennt beide
  Zeichen beim Namen, damit niemand die Escapes entziffern muss.
- **Die vier Beweisdateien werden wieder geloescht.** Siehe Deviation 3. Der Beweis ist mit der
  Zusammenfassungszeile vollstaendig, und was danach in der Nutzerablage bliebe, waere ein Fremdbestand
  fuer Zusicherungen, die ihn nie gemessen haben.
- **Das Formenpaar der Suche steht zweimal im Gate.** `DOCUMENTS` prueft den Dateinamen
  (`language-proof-es.txt`) statt des blossen Sprachcodes, und `QUESTIONS` prueft `term=<Wort>` und
  `?query=<Wort>` statt des blossen Wortes: `es` steht in jedem zweiten englischen Satz und `pais` steht
  im akzentuierten `paises` des portugiesischen Dokuments. Eine Pruefung, die nicht rot werden kann,
  waere keine.
- **Das Gate liest die zwei gegateten Schritte mit.** Ohne sie waere "der Beweisschritt traegt kein
  `if:`" an dem Tag wahr, an dem kein Schritt der Datei mehr eines traegt, und das Gate waere aus dem
  falschen Grund gruen. Die Fehlermeldung sagt deshalb ausdruecklich, dass ein Befund dort ein Befund
  ueber das Gate ist.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die Ergebnisseite liest `query` und nicht `term`**
- **Found during:** Task 2 (beim Lesen von `php/lib/Controller/PageController.php` vor dem Schreiben
  der vier Abrufe)
- **Issue:** Der Plan schreibt die Abrufe woertlich als
  `curl ... 'http://localhost:8080/index.php/apps/findling/?term=<Suchwort>'`, und die Akzeptanzbedingung
  zaehlt `apps/findling/?term=` viermal. `PageController::term()` liest aber
  `$this->request->getParam('query', '')` (`php/lib/Controller/PageController.php:340`), und kein
  Parameter namens `term` wird auf dieser Route irgendwo gelesen. Ein Abruf mit `?term=alemanes` haette
  200 geantwortet und die leere Startseite gerendert, also genau die Form eines gruenen Schritts, der
  nichts beweist. Dieselbe Verwechslung steht in RESEARCH Pattern 7c, von dort hat der Plan sie
  uebernommen.
- **Fix:** Die vier Abrufe fragen `?query=`. Der Kommentarblock ueber ihnen nennt die Codestelle mit
  Zeilennummer und sagt, was `?term=` geantwortet haette. Die Zusicherung darunter ist das, was den
  Irrtum unmoeglich macht: eine leere Startseite traegt keinen Dateinamen, also waere der Schritt mit
  dem falschen Parameter rot geworden statt still gruen. Das Textgate aus Task 3 zaehlt `PAGE_CALL =
  "apps/findling/?query="` viermal und behauptet zusaetzlich je Suchwort, dass die Ergebnisseite genau
  damit gefragt wird.
- **Files modified:** keine zusaetzlichen
- **Verification:** `grep -c 'apps/findling/?query=' .github/workflows/deploy-harp.yml` ist 4;
  `grep -c "'query'" php/lib/Controller/PageController.php` weist die Leseseite nach.
- **Committed in:** `251c86c` (Workflow) und `368ecf5` (Gate)

**2. [Rule 3 - Blocking] Die Vorbedingung baut ihren eigenen Uebersichtsleser**
- **Found during:** Task 2 (beim Einsortieren des Schritts)
- **Issue:** Der Plan verlangt, dass der Schritt `index.php/apps/findling/admin/overview` liest. Der
  vorhandene Helfer `${RUNNER_TEMP}/overview.sh` wird aber erst im Schritt DANACH geschrieben ("The
  drift probe both directions share"), und der Schritt davor zu stehen ist genau die Anforderung des
  Plans. Ein Aufruf des Helfers waere an der fehlenden Datei gescheitert.
- **Fix:** Der Schritt holt sich sein App-Passwort selbst, auf denselben zwei Wegen und in derselben
  Reihenfolge wie `overview.sh` und der `fast_overview`-Helfer in "Store upgrade 6" (occ-Unterbefehl
  zuerst, OCS-Route als Rueckfall, weil stable33 den Unterbefehl nicht kennt), und ruft die Uebersicht
  mit `-H 'OCS-APIRequest: true'` direkt. Rund zwanzig Zeilen, kein zweiter Weg zur Uebersicht, sondern
  dieselbe Mechanik an einer Stelle, an der der Helfer noch nicht existiert. Der Wert des Passworts
  wird nie ausgegeben, nur seine Laenge, wie in den beiden Vorbildern.
- **Files modified:** keine zusaetzlichen
- **Verification:** Der Schritt bricht mit `exit 1` ab, wenn kein Passwort zu bekommen ist, wenn die
  Uebersicht nicht 200 antwortet oder wenn `languagesActive` nicht woertlich `de,en,es,it,nl,pt` ist.
  Das Textgate zaehlt `languagesActive` im Rumpf.
- **Committed in:** `251c86c`

**3. [Rule 2 - Missing critical] Die vier Beweisdateien werden am Ende wieder geloescht**
- **Found during:** Task 2 (beim Pruefen, welche spaeteren Schritte denselben Nutzer sehen)
- **Issue:** Der ganze Workflow ist EIN Job mit EINER Nextcloud auf Port 8080 und EINEM Nutzer
  `testuser`. Was der neue Schritt in dessen Ablage legt, sehen alle spaeteren Strecken. "Store upgrade
  2" behauptet, dass `Belehrung`, `Auszug` und `Erinnerung` je genau EINE Datei zurueckbringen, und der
  Kommentar dieses Schritts sagt selbst, dass die Suche hybrid ist und dass es eine Messung und keine
  Herleitung ist, ob ein fremdes Dokument innerhalb des semantischen Bandes von 14,0 landet. Vier
  fremdsprachige Briefe im Bestand haetten diese Frage einem Beweis gestellt, der sie nie gestellt hat.
  Dieselbe Vorbedingung steht zweimal als `[.terms[]] | all(. == 1)` (Zeilen 3133 und 3790 der alten
  Zaehlung), und RESEARCH sagt ausdruecklich, dass sie nicht aufgeweicht werden darf.
- **Fix:** Nach der Zusammenfassungszeile nimmt der Schritt die vier Dateien ueber WebDAV wieder
  heraus und bricht ab, wenn eine Loeschung nicht 200 oder 204 antwortet. Der Kommentar nennt den
  Grund und den Schritt, um den es geht. Der Papierkorb liegt unter `files_trashbin` und damit
  ausserhalb des Verzeichnisses, das der Crawler laeuft.
- **Files modified:** keine zusaetzlichen
- **Verification:** Der Beweis selbst ist zu diesem Zeitpunkt vollstaendig: acht Zusicherungen (vier
  OCS-Treffer mit Dateinamen, vier Ergebnisseiten mit Dateinamen) stehen ueber der Loeschung.
- **Committed in:** `251c86c`

**4. [Rule 3 - Blocking] Der Kommentar an der Zusicherung nennt die Unterzeile nicht beim Namen**
- **Found during:** Task 3 (beim ersten Lauf des Gates gegen den echten Baum)
- **Issue:** Der Plan verlangt beides: einen Kommentar an der Zusicherung, der sagt, dass die
  Unterzeile bewusst nicht geprueft wird, UND ein Gate, das `entries[0].subline` im Rumpf des Schritts
  verbietet. Ein Kommentar, der die Zeichenkette ausschreibt, macht das Gate rot.
- **Fix:** Der Kommentar beschreibt die Zeichenkette ("never the subline of the first entry") und sagt
  in einem eigenen Satz, dass das Gate genau nach diesem zweiten Namen sucht und deshalb hier
  beschrieben statt geschrieben wird. Inhalt und Begruendung sind vollstaendig erhalten, die
  Zusicherung des Gates bleibt scharf.
- **Files modified:** keine zusaetzlichen
- **Verification:** `EXCERPT_ASSERTION not in body` ist gruen, und
  `test_an_assertion_on_the_excerpt_is_reported` zeigt an `_EXCERPT`, dass die Pruefung rot werden kann.
- **Committed in:** `251c86c`

**5. [Rule 2 - Missing critical] Der Schritt stoesst die Indexierung selbst an**
- **Found during:** Task 2
- **Issue:** Der Plan beschreibt Upload und Pollschleife, aber nicht, wodurch die vier Dateien
  ueberhaupt in die Arbeitsliste kommen. Auf der Entwicklerstrecke lief die Zero-Config-Kette beim
  Aktivieren der App, also moeglicherweise lange bevor diese Dateien in der Ablage lagen; die Schleife
  haette dann ihr ganzes Budget gegen eine leere Warteschlange gefahren und waere mit einem Befund
  ueber die Suche geendet, der in Wahrheit einer ueber die Kette gewesen waere.
- **Fix:** `timeout 300 ./occ findling:index --restart --no-interaction` zwischen Upload und Schleife,
  mit demselben Kommentar und demselben Grund, den derselbe Aufruf in "Store upgrade 2" traegt.
  `--no-interaction`, weil occ diese Shell als interaktiv behandelt und die Rueckfrage sonst auf Nein
  verfiele.
- **Files modified:** keine zusaetzlichen
- **Verification:** Der Aufruf steht vor der Schleife und nach dem Upload; die Zero-Config-Zusicherung
  von "Store install 7" ist nicht beruehrt, weil deren Marke auf `OCC_LOG` erst in jenem Schritt selbst
  genommen wird.
- **Committed in:** `251c86c`

---

**Total deviations:** 5 auto-fixed (1 Rule 1, 2 Rule 2, 2 Rule 3), keine Rule-4-Vorlage an den Owner.
**Impact on plan:** Kein Scope-Zuwachs und keine zusaetzliche Datei. Deviation 1 ist die einzige, die
eine Planaussage korrigiert statt ergaenzt, und sie macht den Beweis von einem stillen gruenen zu einem
echten. Fuer 19-09 gilt: die Frontmatter dieses Plans und RESEARCH Pattern 7c nennen den Parameter
`term`; die Doku muss `query` sagen.

## Threat Flags

Keine neue Angriffsflaeche. Der Plan legt keine Route an, oeffnet keinen Netzpfad und installiert kein
Paket. Die sieben Eintraege des Registers:

- **T-19-07-01 (ein Schritt, der nur auf einem Ast laeuft):** kein `if:`, maschinell geprueft ueber den
  YAML-Baum, und `backend/tests/test_language_proof_steps.py` haelt es fest, mit den zwei gegateten
  Schritten als Gegenbeispiel.
- **T-19-07-02 (Beweis auf der falschen Instanz):** die Vorbedingung liest `.backend.languagesActive`
  und endet mit `exit 1`, und sie steht vor dem ersten Upload.
- **T-19-07-03 (ausgeliefertes info.xml):** die Ersetzung trifft nur `${RUNNER_TEMP}/info-citest.xml`,
  die vorhandene `git diff --quiet`-Zeile bleibt stehen, und `git show --name-only` der drei Commits
  nennt `backend/appinfo/info.xml` nicht.
- **T-19-07-04 (Jobdeadline):** eigenes Budget neben `timeout-minutes: 45`, die Schleife verlaesst sich
  beim Treffer, und der Fehlertext sagt, dass ein Ueberlauf ein Befund ist.
- **T-19-07-05 (Protokoll):** ausgegeben werden Statuscodes, Rundenzahlen und Dateinamen.
  `TESTUSER_PASS` steht nur in den curl-Zeilen, das App-Passwort nur in seiner Laenge.
- **T-19-07-06 (Ergebnisseiten-Abruf, accept):** unveraendert. `PageController::index` traegt
  `NoCSRFRequired` seit v1.1, der Abruf nutzt den bestehenden Zustand und oeffnet nichts.
- **T-19-07-SC (Paketinstallation):** entfaellt mangels Gegenstand, `backend/pyproject.toml` und
  `backend/uv.lock` stehen nicht im Diff.

## Known Stubs

Einer, und er ist im Plan vorgesehen: die gemessene Laufzeit des Schritts steht noch nicht als Zahl im
Kommentarblock ueber `LANGUAGE_PROOF_BUDGET_SECONDS`. Dort steht stattdessen ein eigener Absatz mit
dem Wort RE-MEASURE, der sagt, dass die Zahl nach dem ersten gruenen Lauf nachgetragen wird. Der
Nachtrag gehoert zu 19-09, das den CI-Lauf ohnehin einholt; die Roadmapzeile von 19-09 nennt ihn
("Lauftzeit eingetragen").

## Issues Encountered

- Der Plansatz zum Parameter der Ergebnisseite ist falsch. Siehe Deviation 1. Er stammt aus RESEARCH
  Pattern 7c, dort steht dieselbe Zeile; beide Stellen sind beim Schreiben von 19-09 zu berichtigen.
- Die Akzeptanzbedingung von Task 2 verlangt woertlich, dass `apps/findling/?term=` genau viermal
  vorkommt. Erfuellt ist sie in der Sache und nicht im Wortlaut: viermal `apps/findling/?query=`.
- Der Schrittleser des Gates musste zweimal angefasst werden. `re.findall` ohne `re.MULTILINE` findet
  in einem mehrzeiligen Rumpf nichts, weil `$` dort das Ende der Zeichenkette meint; die
  Nicht-Ueberlappungsprobe zaehlt jetzt Zeilen mit `match` statt Treffer mit `findall`. Der Fall war
  von Anfang an da und hat genau das getan, wofuer er da ist.
- `ruff` hat zwei Stellen beanstandet, beide Formsache: eine implizite Zeichenkettenverkettung in einer
  Liste (ISC004) und ein Anfuehrungszeichenstil in einem der gestellten Muster. Beide behoben, bevor
  committet wurde.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **19-08 (spanischer Vorher-Nachher-Beweis)** ist nicht beruehrt: der liegt in der Upgrade-Strecke und
  braucht einen eigenen Schluessel im Sondenbericht, weil sein Term vorher 0 Treffer haben SOLL. Was
  dieser Plan ihm mitgibt, ist die Zusicherung, dass die Drei-Term-Vorbedingung ihren Bestand behaelt
  (Deviation 3), und das Muster der Formenpaarwahl.
- **19-09 (Doku und Lauf)** hat drei Nachtraege aus diesem Plan: die gemessene Laufzeit in den
  Kommentarblock des Budgets, der Parameter `query` statt `term` in Doku und RESEARCH, und der leere
  Textauszug als Grenze in `docs/language-analyzers.md` (Annahme A5, unveraendert offen).
- **Der Lauf selbst steht aus.** Dieser Plan holt ihn ausdruecklich nicht ein; hier zaehlen das Textgate
  und die lokale Suite. Erst 19-09 sieht den gruenen Lauf.
- **LEX-05** bleibt ungehakt, siehe Frontmatter.

## Verification

- `uv run pytest -q tests/test_language_proof_steps.py --no-header`: **19 bestanden**, 0,08 s.
- `uv run pytest -q` aus `backend/`: **2850 bestanden, 15 uebersprungen, 0 Fehlschlaege** (vorher
  2831/15).
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 138 files already
  formatted.
- `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src tests --min-confidence 80`: keine Befunde.
- Der Workflow ist gueltiges YAML und der Schritt sitzt richtig: ueber `yaml.safe_load` gelesen,
  50 Schritte, der Beweisschritt ist Nummer 13, sein Vorgaenger heisst "Search over the ordinary OCS
  route", sein Nachfolger "The drift probe both directions share", seine Schluessel sind `name` und
  `run` (also kein `if`), und `env.LANGUAGE_PROOF_BUDGET_SECONDS` ist 600.
- Beide veraenderten `run`-Bloecke sind syntaktisch gueltige Shellskripte (`bash -n`, nach Ersetzen
  der beiden `matrix`-Ausdruecke).
- Die Oktal-Escapes erzeugen die richtigen Bytes: `printf ... be\303\257nvloed` liefert `be` gefolgt
  von `303 257`, und der portugiesische Satz liest sich nach `iconv -f utf-8 -t utf-8` als
  `... outros paises ...` mit Akut.
- Akzeptanzkriterien einzeln geprueft:
  - Task 1: `grep -c "de,en,es,it,nl,pt" .github/workflows/deploy-harp.yml` = 1 (verlangt: mindestens
    1), die Zeile steht im Schritt "Build the temporary info.xml"; `grep -c "<default>de,en</default>"
    backend/appinfo/info.xml` = 1; `git diff --name-only` nennt `backend/appinfo/info.xml` nicht; die
    Einmaligkeitspruefung steht als eigene Zeile mit `exit 1`.
  - Task 2: der Schritt steht zwischen den beiden genannten und traegt kein `if:`;
    `grep -c "LANGUAGE_PROOF_BUDGET_SECONDS"` = 3 (verlangt: mindestens 2); `entries | length` steht
    zweimal im Rumpf, `entries[0].subline` null mal; `languagesActive` steht viermal im Rumpf, in einer
    Vorbedingung, die mit `exit 1` endet; `grep -c "apps/findling/?query="` = 4 (Deviation 1); `sleep`
    steht nur am Ende der Schleifenrunde und nie vor der ersten Abfrage; die vier Suchwoerter sind
    reines ASCII, und die ganze Datei enthaelt kein einziges Nicht-ASCII-Zeichen.
  - Task 3: `grep -c "import yaml"` = 0; drei Zeichenkettenkonstanten als gestellte Muster (`_CLEAN`,
    `_GATED`, `_EXCERPT`), die letzten beiden mit je einem Fall, der an ihnen rot wird;
    `grep -c "ubuntu-24.04-arm"` = 5 (verlangt: mindestens 1); der Modullauf meldet 19 bestanden
    (verlangt: mindestens fuenf).
- `git show --name-only` der drei Commits nennt genau `.github/workflows/deploy-harp.yml` (zweimal) und
  `backend/tests/test_language_proof_steps.py` (einmal); keiner der drei loescht eine Datei
  (`git diff --diff-filter=D` ueber die Spanne ist leer).
- Kein Em-Dash in den beiden Dateien, maschinell geprueft.

---
*Phase: 19-frageseite-freischalten*
*Completed: 2026-09-25*

## Self-Check: PASSED

Die geaenderte und die neue Datei liegen auf der Platte, die drei Commits `e7fcd0b`, `251c86c` und
`368ecf5` stehen in der Historie und nennen zusammen genau diese zwei Dateien, keiner von ihnen
loescht etwas, der Haken fuer 19-07 steht in ROADMAP.md, und STATE.md ist von Hand nachgezogen
(Position, Status, naechster Schritt mit den drei Nachtraegen fuer 19-09, Sitzungsfortschreibung und
ein neuer Eintrag unter den Entscheidungen). Kein Em-Dash in STATE.md, ROADMAP.md, dem Workflow, dem
Testmodul oder dieser Datei. Das Arbeitsverzeichnis traegt ausser den Planungsdateien nichts Offenes.
