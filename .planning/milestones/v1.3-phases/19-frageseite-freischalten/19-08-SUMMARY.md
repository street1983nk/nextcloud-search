---
phase: 19-frageseite-freischalten
plan: 08
subsystem: ci
tags: [upgrade-strecke, deploy-harp, spanisch, vorher-nachher, snapshot, textgate]

# Dependency graph
requires:
  - phase: 19-frageseite-freischalten
    provides: "field_plan_for(marks, index) und ReadSide.field_plan aus 19-03, also die Feldliste aus den gespeicherten Marken statt aus dem Code"
  - phase: 19-frageseite-freischalten
    provides: "das Formenpaar alemana/alemanes und das Auswahlkriterium aus 19-06 und 19-07"
  - phase: 18-schema-und-umbau
    provides: "den Umbau, den schema_version-Merker und die Schritte Store upgrade 2 bis 6 von deploy-harp"
provides:
  - ".github/workflows/deploy-harp.yml: eine spanische Datei im Korpus der Bestandsinstallation, indexiert unter v1.2.0 in ein Schema ohne body_es"
  - ".github/workflows/deploy-harp.yml: ein neunter Snapshotwert unter dem eigenen Schluessel spanish, ueber den vorhandenen Zaehler term_hits"
  - ".github/workflows/deploy-harp.yml: die Kette 0, 0, 1 ueber drei Schritte, mit je eigener Fehlermeldung"
  - "backend/tests/test_language_proof_steps.py: das Textgate bewacht die Vorbedingung, den eigenen Schluessel und die drei Zusicherungen"
affects: [19-09 Doku und CI-Lauf einholen]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Term, der vorher nought antworten SOLL, bekommt einen eigenen Snapshotschluessel; die Vorbedingung ueber .terms wird nicht aufgeweicht"
    - "Ein Treffer am Ende einer Strecke ist ohne Gegenbeweis am Anfang nicht von der unveraenderten Abwesenheit eines Treffers zu unterscheiden"
    - "Die Ein-Wort-Regel von api/search.py ist die Bedingung, unter der eine Null in einer hybriden Suche ueberhaupt eine Aussage ueber Felder sein kann"
    - "Nennt ein Schrittname eine Zahl von Zusicherungen, wandert die Zahl mit der Zusicherung"

key-files:
  created: []
  modified:
    - .github/workflows/deploy-harp.yml
    - backend/tests/test_language_proof_steps.py

key-decisions:
  - "Der spanische Wert steht als eigener Schluessel auf oberster Ebene des Snapshots und nicht als vierter Eintrag in .terms: die Vorbedingung [.terms[]] | all(. == 1) steht zweimal im Workflow und wuerde an einem Term brechen, der vorher null sein SOLL"
  - "Die Frage ist EIN Wort, und das ist die tragende Bedingung des ganzen Beweises: api/search.py beantwortet eine einwoertige Zeile allein aus dem Wortindex (Ein-Term-Regel aus 06.1-20), also kann kein semantischer Nachbar die spanische Datei in die Antwort bringen, solange das Feld fehlt"
  - "Zusicherung 2 und 3 setzen fail=1 statt exit 1, weil beide Schritte ausdruecklich jede ihrer Zusicherungen fahren und am Ende mit exit 1 enden; ein Abbruch bei der ersten Abweichung wuerde verbergen, welche gebrochen ist"
  - "Zusicherung 3 prueft nur .spanish == 1 gegen den Nachher-Stand und wiederholt die Null nicht ein drittes Mal: die zwei Gegenbeweise stehen in Store upgrade 3 und in Zusicherung 7 von Store upgrade 5, und der Plan verlangt genau zweimal gegen 0 und einmal gegen 1"
  - "Der Dateiname upgrade-carta-es.txt traegt keine Form von aleman, sonst haette das name-Feld des Schemas die Frage beantwortet, die das Koerperfeld beantworten soll"

requirements-completed: []
# LEX-05 bleibt ungehakt, genau wie nach 19-06 und 19-07. Dieser Plan liefert die
# Upgrade-Haelfte des Beweises; was fehlt, ist der gruene Lauf, und den holt 19-09
# ein. Ein Haken hier waere eine Behauptung ueber einen Lauf, den es noch nicht gibt.

# Metrics
duration: 42min
completed: 2026-09-25
---

# Phase 19 Plan 08: Der spanische Vorher-Nachher-Beweis Summary

**Eine spanische Datei liegt im Korpus der Bestandsinstallation, wird unter v1.2.0 in ein Schema ohne
`body_es` indexiert, und die Frage nach `alemanes` bringt erst null, nach dem Upgrade weiterhin null
und nach dem Umbau genau einen Treffer: die Kette 0, 0, 1 ueber drei Schritte, ohne dass die
Vorbedingung `[.terms[]] | all(. == 1)` angefasst wird**

## Performance

- **Duration:** rund 42 min
- **Started:** 2026-09-25T09:20:00Z
- **Completed:** 2026-09-25T10:02:00Z
- **Tasks:** 3
- **Files modified:** 2 (beide geaendert, keine neu)

## Accomplishments

- **Die spanische Datei liegt im Korpus der Bestandsinstallation.** "Store upgrade 2" legt
  `upgrade-carta-es.txt` in das Konto von `testuser`, auf demselben Weg wie der Referenzkorpus und vor
  demselben `files:scan --all` und `findling:index --restart`. Sie faellt damit unter dasselbe
  `expected=$(find data/testuser/files -type f | wc -l)` und unter dieselbe Leerlaufschleife; es gibt
  keine zweite Wartemechanik.
- **Das Formenpaar ist gemessen und nicht gewaehlt.** Das Dokument traegt `alemana`, gefragt wird nach
  `alemanes`, und von den ausgelieferten Ketten fuehrt NUR die spanische die beiden auf einen
  gemeinsamen Term (`aleman`) zusammen (19-RESEARCH M-5, 24.09.2026). Ein Paar wie `informacion` gegen
  `informaciones` haette die englische Kette gefaltet und waere schon vor Phase 19 gruen gewesen. Der
  Kommentarblock ueber der Datei sagt das mit Quelle.
- **Die uebrigen Woerter folgen der Regel des Fuellkorpus.** Keines traegt Belehrung, Auszug,
  Erinnerung, florpel oder findling-canary, und keines zerlegt sich in ein Konstituent, das eines davon
  traegt. Der Dateiname traegt ausserdem keine Form von `aleman`, sonst haette das `name`-Feld die Frage
  beantwortet, die das Koerperfeld beantworten soll. Die drei vorhandenen Termzusicherungen direkt
  hinter dem Leerlaufen pruefen das ohnehin, statt es anzunehmen.
- **Der neunte Snapshotwert steht unter einem eigenen Schluessel.** `snapshot()` ruft den vorhandenen
  Zaehler `term_hits alemanes`, legt das Ergebnis erst in eine Shellvariable, beendet den Snapshot bei
  einem Leerwert mit der Rohantwort im Protokoll und baut erst danach mit dem einen `jq -n` das Objekt
  (T-18-12-03). Der Schluessel heisst `spanish` und steht auf oberster Ebene, NICHT in `.terms`. Der
  Kommentar daneben nennt den Grund und die zwei Stellen, an denen die Vorbedingung steht.
- **Drei Zusicherungen, und sie sind eine Kette.** "Store upgrade 3" verlangt 0 auf der
  Bestandsinstallation (Gegenbeweis), "Store upgrade 5" verlangt in einer neuen, siebten Zusicherung
  weiterhin 0 nach dem Upgrade und vor dem Umbau (die CI-Haelfte von Erfolgskriterium 2), und "Store
  upgrade 6" verlangt in einer zehnten Zusicherung genau 1 nach dem Umbau. Jede der drei endet im
  Fehlerfall in `::error::` mit dem gelesenen Wert, und beide Schritte enden mit `exit 1`.
- **Die Zaehlungen sind mitgezogen worden.** Der Schrittname heisst jetzt "Store upgrade 5, the seven
  assurances after the upgrade", die Abschlusszeilen lauten "all seven assurances hold" und "all ten
  assurances hold", und die vier Kommentarstellen, die in "Store upgrade 6" von neun sprachen, sprechen
  von zehn. Name und Inhalt laufen nicht auseinander.
- **Beide Zusammenfassungen nennen den Uebergang.** "Store upgrade 5" schreibt, dass die spanische
  Frage weiterhin null antwortet, weil die Feldliste am gespeicherten Merker haengt; "Store upgrade 6"
  schreibt den Weg von 0 auf 1 samt der beiden Zwischenstaende.
- **Die Vorbedingung ist unveraendert.** `grep -cF '[.terms[]] | all(. == 1)'` ist weiterhin 2, und der
  Diff zeigt an beiden Stellen keine Zeile.
- **Das Textgate hat sieben Faelle dazubekommen** (19 auf 26, alle bestanden, 0,10 s). Drei neue
  Aussagen, drei neue gestellte Muster, je ein Fall, der an seinem Muster rot wird.
- **Volle Suite 2857 bestanden / 15 uebersprungen** (vorher 2850/15), die vier Qualitaetsgates lokal
  gruen.

## Task Commits

1. **Task 1: Die spanische Datei und der neunte Snapshotwert** - `f0ceef6` (ci)
2. **Task 2: Drei Zusicherungen ueber die Strecke** - `c5a450c` (ci)
3. **Task 3: Das Textgate um die Upgrade-Haelfte erweitern** - `8ac2626` (test)

**Plan metadata:** siehe docs-Commit unten

## Files Created/Modified

- `.github/workflows/deploy-harp.yml` (GEAENDERT), vier Stellen:
  - "Store upgrade 2": der Kommentarblock und die spanische Datei hinter dem Kopieren des
    Referenzkorpus (+42 Zeilen).
  - `snapshot()` in "Store upgrade 3": der neunte Wert mit Leerwertpruefung und Kommentarblock, ein
    `--argjson spanish` in der Argumentliste und der Schluessel `spanish` im `jq -n`-Objekt
    (+31 Zeilen).
  - "Store upgrade 3": die erste Zusicherung hinter der Termvorbedingung, plus die berichtigte
    Abschlusszeile (+11 Zeilen, 1 geaendert).
  - "Store upgrade 5" und "Store upgrade 6": die siebte und die zehnte Zusicherung, die zwei
    Zusammenfassungszeilen und die sechs Stellen, an denen eine Zahl von Zusicherungen steht
    (+57 Zeilen, 8 geaendert).
- `backend/tests/test_language_proof_steps.py` (GEAENDERT), 519 auf 757 Zeilen: drei Absaetze im
  Modulkopf, sechs neue Konstanten samt `_TERMS_OBJECT`, drei Scanner, drei Faelle gegen den echten
  Baum, die Erweiterung von `_CLEAN` um einen Schnappschussblock und drei Zusicherungsstellen, drei
  gestellte Muster und drei Faelle, die an ihnen rot werden.

Keine weitere Datei im Diff. `backend/src/findling`, `php/`, `backend/appinfo/info.xml`,
`backend/pyproject.toml` und `backend/uv.lock` stehen in keinem der drei Commits; die Ratschen
`PACKAGE_TREE_HASH_TODAY`, `PACKAGE_FILES_TODAY` und `PHP_TREE_HASH_TODAY` sind unberuehrt, und es ist
kein Paket installiert worden.

## Decisions Made

- **Eigener Schluessel statt vierter Termeintrag.** Die Vorbedingung `[.terms[]] | all(. == 1)` steht
  zweimal im Workflow und verlangt genau eine Datei je Term. Ein Term, der vorher null antworten SOLL,
  passt dort nicht hinein, und der billige Weg waere gewesen, die Vorbedingung aufzuweichen. Sie ist
  aber der Grund, warum die Zusicherungen hinter ihr etwas bedeuten; deshalb steht der spanische Wert
  daneben, und deshalb bewacht das Gate aus Task 3 die Zahl der Vorkommen.
- **Die Frage ist EIN Wort, und das traegt den ganzen Beweis.** Die Suche ist hybrid, und der
  Messbericht `docs/measurements/2026-09-06-vektordistanzen` sagt ausdruecklich, dass einwoertige Proben
  bei 68 bis 77 auf der int8-L2-Skala landen, also unter der Obergrenze von 86,5: waere die Vektorseite
  im Spiel, koennte die spanische Datei schon vor dem Umbau als naechster Nachbar von `alemanes` in die
  Antwort kommen, und die 0 waere rot geworden, ohne dass etwas kaputt ist. Sie ist nicht im Spiel,
  weil `api/search.py` eine einwoertige Zeile allein aus dem Wortindex beantwortet (Ein-Term-Regel aus
  Plan 06.1-20, `lexical_only = ... or rewritten.one_term or ...`). Diese Bedingung stand weder im Plan
  noch in RESEARCH; sie steht jetzt als eigener Absatz im Kommentarblock ueber der Datei, weil eine
  spaetere Zwei-Wort-Frage den Beweis lautlos in eine Aussage ueber Distanzen verwandeln wuerde.
- **`fail=1` statt `exit 1` in den Schritten 5 und 6.** Beide Schritte sagen in ihrem eigenen
  Kommentarkopf, warum jede ihrer Zusicherungen gefahren wird und keine abbricht, und beide enden mit
  `exit 1`, sobald `fail` gesetzt ist. Die Akzeptanzbedingung des Plans ("endet im Fehlerfall mit
  `::error::` und `exit 1`") ist damit in der Sache erfuellt; der Schritt endet mit `exit 1` und die
  Meldung traegt `::error::` und den gelesenen Wert. Ein `exit 1` an Ort und Stelle haette die
  bestehende Bauart beider Schritte gebrochen.
- **Zusicherung 3 prueft nur die 1.** Die Null vor dem Umbau ein drittes Mal zu pruefen waere eine
  dritte Stelle gegen 0 gewesen, und der Plan verlangt genau zwei. Der Nachher-Stand wird gegen 1
  geprueft, der Vorher-Stand steht in der Erfolgsmeldung als gelesene Zahl, und die beiden Gegenbeweise
  stehen dort, wo sie den Zustand messen, ueber den sie sprechen.
- **Alle drei Zusicherungen fragen `jq -e`.** Die zweite und die dritte waren im ersten Anlauf reine
  Shellvergleiche; sie sind auf `jq -e '.spanish == 0'` und `jq -e '.spanish == 1'` umgestellt worden,
  damit die drei Stellen als eine Kette lesbar sind und ein Textgate sie zaehlen kann, ohne drei
  verschiedene Schreibweisen zu kennen.
- **Der Dateiname traegt keine Form von `aleman`.** `upgrade-carta-es.txt`. Das Schema sucht eine
  blanke Frage auch ueber `name` und `title`; ein Name wie `carta-alemana.txt` haette den Treffer nach
  dem Umbau womoeglich ueber das Namensfeld erzeugt, und der Beweis haette ueber das Koerperfeld nichts
  gesagt.
- **Das Gate nimmt die drei neuen Aussagen NICHT in `CLAIMS` auf.** `CLAIMS` ist die Liste, die der
  Fehlschlagpfad ausgibt, wenn der Beweisschritt von 19-07 nicht gefunden wird. Die drei neuen Aussagen
  handeln von der Upgrade-Strecke und nicht von jenem Schritt: ein umbenannter Beweisschritt darf sie
  nicht verstummen lassen, und sie duerfen ihn nicht teurer machen, als er verschweigt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Die Ein-Wort-Bedingung steht als eigener Absatz im Workflow**
- **Found during:** Task 1, vor dem Schreiben der Datei
- **Issue:** Der Plan und RESEARCH Pattern 7a behaupten die Null vor dem Umbau, ohne die Suche als
  hybrid zu beruecksichtigen. `docs/measurements/2026-09-06-vektordistanzen` sagt ausdruecklich, dass
  eine einwoertige Anfrage auf der int8-L2-Skala bei 68 bis 77 landet und die Obergrenze bei 86,5 liegt:
  waere die Vektorseite fuer diese Frage gebaut worden, waere die spanische Datei der naechste Nachbar
  von `alemanes` gewesen und die drei Zusicherungen haetten 1, 1, 1 gemessen statt 0, 0, 1. Die
  Strecke haette rot ausgesehen, obwohl nichts kaputt ist, und der Befund waere in 19-09 an einem
  bezahlten CI-Lauf aufgeschlagen.
- **Fix:** Nachgesehen statt angenommen: `backend/src/findling/api/search.py` setzt
  `lexical_only = bool(rewritten.operators) or rewritten.one_term or title_only or sort != "relevance"`
  und baut fuer eine einwoertige Zeile gar keine `SemanticSide`. Die Bedingung traegt also, und sie
  traegt genau so lange, wie die Frage ein Wort bleibt. Der Kommentarblock ueber der spanischen Datei
  sagt das jetzt in einem eigenen Absatz mit Quelle und mit dem Satz, was eine Zwei-Wort-Frage aus dem
  Beweis machen wuerde.
- **Files modified:** keine zusaetzlichen
- **Verification:** `grep -n "one_term" backend/src/findling/api/search.py` weist die Regel nach; der
  Absatz steht in "Store upgrade 2".
- **Committed in:** `f0ceef6`

**2. [Rule 3 - Blocking] Die Bauart des `printf` ersetzt durch eine Klammergruppe**
- **Found during:** Task 1
- **Issue:** Die naheliegende Form `printf '%s\n' 'Zeile eins' 'Zeile zwei' > datei` braucht
  Zeilenfortsetzungen mit Rueckstrich, und die haben den ersten Schreibversuch in eine einzige,
  kaputte Zeile verwandelt (Werkzeugweg, nicht Shell). Eine Datei, die falsch geschrieben wird, faellt
  erst im CI auf.
- **Fix:** `{ echo '...'; echo '...'; } > datei`, ohne einen einzigen Rueckstrich. Gleiches Ergebnis,
  und der Block ist in `bash -n` geprueft. Alle folgenden Bearbeitungen des Workflows laufen ueber ein
  Python-Skript, das mit dem Write-Werkzeug geschrieben und danach geloescht wird.
- **Files modified:** keine zusaetzlichen
- **Verification:** `bash -n` ueber alle extrahierten `run`-Bloecke des Auftrags, Rueckgabecode 0.
- **Committed in:** `f0ceef6`

**3. [Rule 1 - Bug] Der Kommentar zum eigenen Schluessel machte das Gate falsch**
- **Found during:** Task 1, beim ersten Zaehlen
- **Issue:** Der erste Entwurf des Kommentars schrieb die Vorbedingung woertlich aus. Danach stand
  `[.terms[]] | all(. == 1)` dreimal in der Datei, die Akzeptanzbedingung des Plans verlangt zwei, und
  das Textgate aus Task 3 haette die dritte Stelle als aufgeweichte Vorbedingung gemeldet.
- **Fix:** Der Kommentar beschreibt die Vorbedingung ("die Vorbedingung, dass jeder Eintrag dieses
  Objekts mit genau einer Datei antwortet") und nennt die zwei Schritte, in denen sie steht, statt sie
  auszuschreiben. Derselbe Griff wie bei Deviation 4 von 19-07 und aus demselben Grund.
- **Files modified:** keine zusaetzlichen
- **Verification:** `grep -cF '[.terms[]] | all(. == 1)'` ist 2.
- **Committed in:** `f0ceef6`

**4. [Rule 3 - Blocking] Zusicherung 2 und 3 auf `jq -e` umgestellt**
- **Found during:** Task 2
- **Issue:** Im ersten Anlauf lasen beide den Wert mit `jq -r` in eine Shellvariable und verglichen mit
  `[ "${spanish}" != "0" ]`. Damit stand `.spanish == 0` nur einmal in der Datei, die Akzeptanzbedingung
  des Plans spricht von drei Stellen "zweimal gegen 0 und einmal gegen 1", und ein Textgate haette drei
  Schreibweisen kennen muessen, um sie zu finden.
- **Fix:** Beide fragen jetzt `jq -e '.spanish == 0'` beziehungsweise `jq -e '.spanish == 1'` und lesen
  den Wert nur noch fuer die Meldung. Dieselbe Form wie die vorhandene Bannerpruefung von "Store upgrade
  5".
- **Files modified:** keine zusaetzlichen
- **Verification:** `grep -cF '.spanish == 0'` ist 2, `grep -cF '.spanish == 1'` ist 1.
- **Committed in:** `c5a450c`

**5. [Rule 3 - Blocking] Der Kommentar von Zusicherung 1 gekuerzt**
- **Found during:** Task 2
- **Issue:** Der `run`-Block von "Store upgrade 3" ist mit 19838 Zeichen der drittlaengste der Datei,
  und die neue Zusicherung brachte ihn auf 20799. GitHub kappt einen `run`-Block bei 21000 Zeichen,
  sobald er einen `${{ }}`-Ausdruck traegt; dieser Block traegt keinen, also greift die Grenze nicht,
  aber 201 Zeichen Luft sind keine.
- **Fix:** Der Kommentar von fuenf auf vier Zeilen gekuerzt, ohne eine Aussage zu verlieren. Der Block
  steht bei 20726 Zeichen. Der Hinweis fuer den naechsten Plan steht unter "Deferred Issues".
- **Files modified:** keine zusaetzlichen
- **Verification:** ueber `yaml.safe_load` gemessen: "Store upgrade 3" 20726 Zeichen, kein `${{`;
  "Store upgrade 5" 11402 Zeichen MIT `${{` (weit unter der Grenze); "Store upgrade 6" 29789 Zeichen,
  kein `${{`.
- **Committed in:** `c5a450c`

**6. [Rule 3 - Blocking] ISC004 im neuen Scanner**
- **Found during:** Task 3, beim ersten `ruff check`
- **Issue:** Eine implizite Zeichenkettenverkettung direkt in einer Liste. Dieselbe Beanstandung wie in
  19-07, an derselben Stelle der Bauart.
- **Fix:** Die Meldung in eine Variable `finding` gehoben und `[finding]` zurueckgegeben, wie es
  `scan_matrix` schon tut.
- **Files modified:** keine zusaetzlichen
- **Verification:** `uv run ruff check .`: All checks passed.
- **Committed in:** `8ac2626`

---

**Total deviations:** 6 auto-fixed (1 Rule 1, 1 Rule 2, 4 Rule 3), keine Rule-4-Vorlage an den Owner.
**Impact on plan:** Kein Scope-Zuwachs und keine zusaetzliche Datei. Deviation 1 ist die einzige, die
eine stillschweigende Annahme des Plans beruehrt; sie aendert nichts an der Umsetzung, sondern schreibt
die Bedingung auf, unter der die Umsetzung stimmt. Deviation 4 und 5 sind Formsachen, die die
Akzeptanzbedingungen woertlich erfuellen.

## Threat Flags

Keine neue Angriffsflaeche. Der Plan legt keine Route an, oeffnet keinen Netzpfad und installiert kein
Paket. Die fuenf Eintraege des Registers:

- **T-19-08-01 (Zeitfenster zwischen Upgrade und Umbau):** Zusicherung 7 von "Store upgrade 5" misst
  genau dieses Fenster. Der spanische Wert ist danach 0, und die drei Bestandsterme bringen in
  Zusicherung 1 desselben Schritts weiterhin je genau eine Datei.
- **T-19-08-02 (Treffer ohne Gegenbeweis):** Zusicherung 1 in "Store upgrade 3" belegt die 0 auf der
  Bestandsinstallation, und sie steht vor dem Upgrade, nicht daneben.
- **T-19-08-03 (die Vorbedingung):** eigener Snapshotschluessel statt vierter Termeintrag, zwei
  unveraenderte Vorkommen, und ein Textgate, das beides mit je einer Gegenprobe haelt.
- **T-19-08-04 (Wortwahl des Beweises):** `alemanes` gegen `alemana` ist gemessen (19-RESEARCH M-5) das
  Paar, das nur die spanische Kette zusammenfuehrt. Die Quelle steht im Kommentar, nicht nur im Plan.
- **T-19-08-SC (Paketinstallation):** entfaellt mangels Gegenstand, `backend/pyproject.toml` und
  `backend/uv.lock` stehen nicht im Diff.

## Known Stubs

Keiner. Alles, was dieser Plan behauptet, steht im Workflow und im Gate; was noch fehlt, ist der Lauf,
und der gehoert ausdruecklich zu 19-09.

## Deferred Issues

- **"Store upgrade 3" steht bei 20726 Zeichen.** Die 21000-Zeichen-Grenze von GitHub greift nur fuer
  einen `run`-Block, der einen `${{ }}`-Ausdruck traegt, und dieser traegt keinen. Wer dort je einen
  Matrixausdruck hineinschreibt, muss den Block vorher kuerzen oder die Werte wie "Store upgrade 6" ueber
  einen `env:`-Block hereinreichen. Gehoert in die Kleinigkeitenliste von STATE.md, nicht in diesen
  Plan.

## Issues Encountered

- Der erste Schreibversuch des Workflows ueber eine Bash-Heredoc hat Rueckstriche verschluckt und aus
  einer dreizeiligen `printf`-Kette eine kaputte Zeile gemacht. Siehe Deviation 2. Ab Task 1 laufen alle
  Bearbeitungen ueber ein Python-Skript, das mit dem Write-Werkzeug geschrieben wird; die Skripte sind
  im jeweiligen Commit geloescht.
- Die Annahme des Plans, die spanische Frage bringe vor dem Umbau null, haengt an einer Bedingung, die
  im Plan nicht steht. Siehe Deviation 1. Sie traegt, aber sie traegt nur fuer einwoertige Fragen.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **19-09 (Doku und Lauf)** hat jetzt vier Nachtraege: die drei aus 19-07 (gemessene Laufzeit in den
  RE-MEASURE-Absatz ueber `LANGUAGE_PROOF_BUDGET_SECONDS`, der Parameter `query` statt `term` in Doku und
  RESEARCH, der leere Textauszug als Grenze in `docs/language-analyzers.md`) und einer aus diesem Plan:
  die Ein-Wort-Bedingung des spanischen Beweises gehoert neben die Beschreibung der Upgrade-Strecke,
  damit sie nicht nur im Workflow steht.
- **Der Lauf selbst steht aus.** Dieser Plan holt ihn ausdruecklich nicht ein. Die drei Zusicherungen
  sind so gebaut, dass ein roter Lauf sagt, welche Haelfte fehlt: 0 nach dem Umbau heisst Umbau oder
  Feldplan, ein Treffer vor dem Umbau heisst Wortwahl oder Vektorseite.
- **LEX-05** bleibt ungehakt, siehe Frontmatter.

## Verification

- `uv run pytest -q tests/test_language_proof_steps.py --no-header`: **26 bestanden**, 0,10 s (vorher
  19).
- `uv run pytest -q` aus `backend/`: **2857 bestanden, 15 uebersprungen, 0 Fehlschlaege** (vorher
  2850/15).
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 138 files already
  formatted.
- `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src tests --min-confidence 80`: keine Befunde.
- Der Workflow ist gueltiges YAML: ueber `yaml.safe_load` gelesen, ein Auftrag `deploy-harp`,
  50 Schritte, die acht Schritte "Store upgrade 0" bis "Store upgrade 6" sind vollstaendig da.
- Jeder `run`-Block des Auftrags ist ein gueltiges Shellskript (`bash -n`, nach Ersetzen der
  `matrix`-Ausdruecke), Rueckgabecode 0 fuer alle.
- Akzeptanzkriterien einzeln geprueft:
  - Task 1: `grep -c "alemana"` = 4 Zeilen und `grep -c "alemanes"` = 12 Zeilen (verlangt: je
    mindestens 1); `grep -cF '[.terms[]] | all(. == 1)'` = 2 und der Ausdruck steht im Diff nicht;
    `spanish: $spanish` steht im `jq -n`-Objekt auf oberster Ebene und nicht im `terms`-Objekt
    (maschinell ueber den Blockleser des Gates geprueft); `grep -c "REBUILD_LANGUAGES: 'es,de,en'"` = 1;
    die spanische Datei enthaelt keines der fuenf verbotenen Woerter.
  - Task 2: drei Stellen pruefen den spanischen Wert, `grep -cF '.spanish == 0'` = 2 und
    `grep -cF '.spanish == 1'` = 1; jede der drei traegt `::error::` mit dem gelesenen Wert, und alle
    drei Schritte enden mit `exit 1`; "Store upgrade 6" schreibt eine Zeile in `GITHUB_STEP_SUMMARY`,
    die den Uebergang von 0 auf 1 nennt; der Diff dieser beiden Bloecke enthaelt ausser den
    Zusicherungszahlen (sechs auf sieben, neun auf zehn) nur Hinzufuegungen.
  - Task 3: `uv run pytest -q tests/test_language_proof_steps.py --no-header` meldet 26 bestanden
    (verlangt: mindestens acht); `grep -c "import yaml"` = 0; das Modul traegt ein gestelltes Muster
    `_FOURTH_TERM` mit dem spanischen Wert als viertem `.terms`-Eintrag und
    `test_a_fourth_term_inside_the_terms_object_is_reported` wird daran rot; die volle Suite ist gruen
    und die vier Qualitaetsgates sind lokal gruen.
- `git diff --name-only` ueber die drei Commits nennt genau `.github/workflows/deploy-harp.yml` und
  `backend/tests/test_language_proof_steps.py`. Kein Commit loescht eine Datei
  (`git diff --diff-filter=D` ueber die Spanne ist leer). `backend/src/findling`, `php/`,
  `backend/appinfo/info.xml`, `backend/pyproject.toml` und `backend/uv.lock` stehen in keinem davon.
- Kein Em-Dash in den beiden Dateien, kein Nicht-ASCII-Zeichen in beiden, maschinell geprueft.

---
*Phase: 19-frageseite-freischalten*
*Completed: 2026-09-25*

## Self-Check: PASSED

Die beiden geaenderten Dateien liegen auf der Platte, die drei Commits `f0ceef6`, `c5a450c` und
`8ac2626` stehen in der Historie und nennen zusammen genau diese zwei Dateien, keiner von ihnen
loescht etwas, der Haken fuer 19-08 steht in ROADMAP.md (und die Fortschrittszeile der Phase ist auf
8/9 nachgezogen, sie stand auf 5/9), und STATE.md ist von Hand nachgezogen (Frontmatter, Position,
naechster Schritt mit den vier Nachtraegen fuer 19-09, zwei neue Eintraege unter den Entscheidungen,
eine neue Kleinigkeit und die Sitzungsfortschreibung). Kein Em-Dash in STATE.md, ROADMAP.md, dem
Workflow, dem Testmodul oder dieser Datei; kein Nicht-ASCII-Zeichen in den beiden Codedateien. Das
Arbeitsverzeichnis traegt ausser den Planungsdateien nichts Offenes; die drei Einmal-Skripte, ueber die
der Workflow bearbeitet wurde, sind vor ihrem jeweiligen Commit geloescht worden.
