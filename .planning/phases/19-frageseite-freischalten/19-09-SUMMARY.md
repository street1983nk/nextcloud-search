---
phase: 19-frageseite-freischalten
plan: 09
subsystem: docs
tags: [doku, known-limits, messzahlen, ci-lauf, arm64, budget, berichtigung]

# Dependency graph
requires:
  - phase: 19-frageseite-freischalten
    provides: "field_plan_for(marks, index) aus 19-03, also die Torreihenfolge, die der neue Abschnitt beschreibt"
  - phase: 19-frageseite-freischalten
    provides: "TIPPING_BOOST = 0.81 aus 19-04, die Zahl unter Measured numbers"
  - phase: 19-frageseite-freischalten
    provides: "den ungegateten Sprachbeweis aus 19-07 und die Kette 0, 0, 1 aus 19-08, also den Lauf, den dieser Plan einholt"
provides:
  - "docs/language-analyzers.md: Abschnitt 'What a question searches' mit vier Absaetzen (gespeicherte Marke statt Umgebungsvariable, schema_version als Tor, keine Spracherkennung, Ein-Wort-Regel)"
  - "docs/language-analyzers.md: ein neuer Known-limits-Eintrag zum leeren Textauszug und zwei neue Messzahlen"
  - ".github/workflows/deploy-harp.yml: die gemessene Laufzeit des Sprachbeweises als Zahl im Budgetkommentar"
  - ".github/workflows/deploy-harp.yml: die Upgrade-Strecke registriert wieder mit der ausgelieferten Sprachvorgabe"
  - "Der gruene Lauf 36074155306 auf allen vier Matrixaesten, mit dem Sprachbeweis viermal und der Kette 0, 0, 1"
affects: [19 Phasenverifikation (LEX-05-Haken), 22 Messphase (MESS-09), 23 Release (REL-03 Kriterium 2)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Doku wird gegen den Code geschrieben und nicht gegen den Plan: die Torreihenfolge stammt aus api/resources.py, nicht aus der Absicht"
    - "Ein Budgetkommentar traegt eine gemessene Zahl mit Laufnummer, Datum und Matrixast, und den Wert des langsamsten Astes"
    - "Ein Beweis-Lauf wird auf den Ast gelesen, auf dem er etwas kostet: der arm64-Ast ist hier zweimal so langsam wie die drei amd64-Aeste zusammen"
    - "Eine Berichtigung an einem Research-Dokument steht als datierter Vermerk neben dem Irrtum und ersetzt ihn nicht"

key-files:
  created:
    - .planning/phases/19-frageseite-freischalten/19-09-SUMMARY.md
  modified:
    - docs/language-analyzers.md
    - .github/workflows/deploy-harp.yml
    - .planning/phases/19-frageseite-freischalten/19-RESEARCH.md

key-decisions:
  - "Der neue Abschnitt traegt den englischen Titel 'What a question searches' und nicht den deutschen Arbeitstitel des Plans: docs/language-analyzers.md ist durchgehend englisch, und der Plan sagt selbst, dass die Datei englisch geschrieben ist"
  - "Die Ein-Wort-Bedingung aus 19-08 steht als vierter Absatz des neuen Abschnitts und nicht unter Known limits: sie ist eine Eigenschaft der Suche, die ein Admin kennen muss, und sie steht damit direkt neben der Beschreibung der Upgrade-Strecke, wo 19-08 sie haben wollte"
  - "Der Parameter-Irrtum wird in 19-RESEARCH als datierter Vermerk berichtigt und in 19-07-PLAN.md NICHT nachtraeglich geaendert: ein Plan ist ein historisches Artefakt, der Fund steht in 19-07-SUMMARY, und der Vermerk sagt, woher der Irrtum kam"
  - "LANGUAGE_PROOF_BUDGET_SECONDS bleibt bei 600, gemessen sind 172 s auf dem langsamsten Ast; das Budget ist gegen die Cron-Taktung dimensioniert und nicht gegen die Arbeit"
  - "LEX-05 bleibt ungehakt: die Traceability-Tabelle von REQUIREMENTS.md haekt eine Anforderung bei der Phasenverifikation mit Laufnummer ab (so steht LEX-02 bis LEX-08 dort), und dieser Plan liefert die Laufnummer, nicht die Verifikation"

requirements-completed: []
# LEX-05 bleibt ungehakt, genau wie nach 19-06, 19-07 und 19-08. Der gruene Lauf
# ist ab jetzt da (36074155306), und damit ist die letzte offene Bedingung
# erfuellt; der Haken selbst gehoert der Phasenverifikation, die ihn wie bei
# Phase 18 mit Laufnummer in die Traceability-Tabelle schreibt.

# Metrics
duration: 78min
completed: 2026-09-25
---

# Phase 19 Plan 09: Die Frageseite lesbar gemacht und ihr Beweis eingeholt Summary

**`docs/language-analyzers.md` sagt einem Admin jetzt, welche Felder eine Frage durchsucht, woran die
Feldliste haengt und was sie nicht leistet, und der Lauf 36074155306 belegt die Zusagen auf allen vier
Matrixaesten: der Sprachbeweis erscheint viermal, der spanische Wert wandert 0, 0, 1, und der Weg
dorthin ging ueber einen roten Lauf, der einen echten Fehler der Upgrade-Strecke gefunden hat**

## Performance

- **Duration:** rund 78 min
- **Started:** 2026-09-24T23:18:00Z
- **Completed:** 2026-09-25T00:36:00Z
- **Tasks:** 2 (plus drei Zusatzauftraege der Ausfuehrung)
- **Files modified:** 3 (alle geaendert, keine neu ausser dieser Summary)

## Accomplishments

- **Der Abschnitt "What a question searches" steht zwischen der Sprachumschaltung und der
  Ergaenzungsliste**, gebaut wie "Switching a language on, and when it takes effect": zwei Saetze
  Mechanik, dann vier fett eingeleitete Absaetze. Er ist gegen `backend/src/findling/api/resources.py`
  geschrieben und nicht gegen den Plan (T-19-09-01): die Torreihenfolge, die er beschreibt, ist die
  von `field_plan_for`, einschliesslich der `doc_freq`-Sonde hinter den Marken und des Satzes, dass
  ein einziges Feld, das wirft, den GANZEN Plan auf den Bestandsplan zurueckfallen laesst.
- **Die vier Absaetze im Einzelnen.** Erstens: die gespeicherte `languages`-Marke des Verzeichnisses
  entscheidet und nicht `FINDLING_LANGUAGES`, wer eine Sprache einschaltet, sucht erst nach dem Umbau
  in ihr. Zweitens: die Feldliste haengt am Merker `schema_version`, und das Tor faellt geschlossen,
  auch bei fehlender oder unbekannter Marke. Drittens: es gibt keine Spracherkennung, und der Grund,
  warum keine gebraucht wird, steht daneben (die Frage laeuft durch ALLE aktiven Felder, jedes
  analysiert sie mit seiner eigenen Kette, die Rangordnung macht der Feld-Boost mit 1,0 / 0,8 / 0,6).
  Viertens: eine einwoertige Frage wird allein aus dem Wortindex beantwortet, und genau daran haengt
  die Aussagekraft des spanischen Vorher-Nachher-Beweises.
- **Der neue Known-limits-Eintrag** steht an erster Stelle des Abschnitts, in der dortigen Form: fette
  Einleitung, gemessenes Beispiel mit den echten Termen (`alemanes` gegen ein Dokument mit `alemana`,
  Kontrollfrage `contrato`), die Codestelle `index/search.py:875` mit
  `SnippetGenerator.create(..., FIELD_BODY_DE)`, das Zitat aus dem Docstring ("a hit without a snippet
  is still a hit, and the subline falls back to the path on the PHP side"), dann die Alternative
  (ein Auszugspfad je Koerperfeld, also sechs gespeicherte Textkopien statt einer) und ihr Preis. Der
  Eintrag nennt sich selbst als einen der Punkte, die Phase 23 in Doku und Store-Text schreibt
  (REL-03 Kriterium 2).
- **Zwei neue Zahlen unter "Measured numbers"**, jede mit ihrem eigenen Messlauf und Datum, weil sie
  nicht aus dem Kettenlauf der Tabelle darueber stammen: die Kippgrenze 0,81 aus der Rangprobe
  (Sweep ueber 101 Werte, 24.09.2026, tantivy 0.26.2, `backend/tests/test_field_plan_ranking.py`) samt
  dem Satz, dass sie die Eingabe fuer den `disjunction_max`-Entscheid der Phase 22 ist und dass
  tantivy die Feldbeitraege summiert, Boosts sie also daempfen und nicht beseitigen; und die Kosten
  des Feldplans, ein `read_meta()` plus eine `doc_freq`-Sonde je Koerperfeld zu 0,26 us, einmal je
  Oeffnung und nicht je Anfrage.
- **Der Lauf ist eingeholt und er ist gruen: 36074155306, alle vier Matrixaeste erfolgreich**,
  einschliesslich `ubuntu-24.04-arm`. Der Schritt "Language proof, the four new chains answer on the
  ordinary search route" ist auf ALLEN VIER Aesten gelaufen und auf allen vieren erfolgreich, also
  nicht das Warnzeichen aus RESEARCH Pitfall 3.
- **Der arm64-Ast belegt die zweite Haelfte von Erfolgskriterium 1 woertlich.** Aus seinem Protokoll:
  `es|it|nl|pt: the ordinary search route brings back language-proof-<code>.txt`, danach
  `es|it|nl|pt: the result page carries language-proof-<code>.txt`, danach die vier Loeschungen mit
  HTTP 204. Vier Sprachen, zweimal je Sprache, auf dem Ast, den die gegateten Schritte nie sehen.
- **Die Kette 0, 0, 1 ist gemessen.** Im Ast stable34/amd64: `"spanish": 0` im Schnappschuss von
  "Store upgrade 3", `"spanish": 0` nach dem Upgrade in Zusicherung 7 von "Store upgrade 5"
  ("the Spanish question answers 0 hits after the upgrade, unchanged against the v1.2.0
  installation"), `"spanish": 1` nach dem Umbau in Zusicherung 10 von "Store upgrade 6" ("the question
  alemanes went from 0 to 1 hits across the rebuild").
- **Die gemessene Laufzeit steht als Zahl im Workflow.** Der RE-MEASURE-Absatz ist weg, an seiner
  Stelle stehen 172 s auf dem arm64-Ast von 36074155306 (23:45:38Z bis 23:48:30Z), daneben 73 s, 41 s
  und 32 s der drei amd64-Aeste und die 163 s desselben Astes im Lauf davor. `LANGUAGE_PROOF_BUDGET_SECONDS`
  ist NICHT erhoeht worden; das Budget von 600 ist gegen die Cron-Taktung dimensioniert, und der
  Abstand dazu steht jetzt als Zahl daneben statt als Vermutung.
- **Der erste Lauf war rot, und er hat einen echten Fehler gefunden** (Deviation 1): die
  Upgrade-Strecke registrierte die aufgeruestete Haelfte mit der sechssprachigen Entwicklerdatei aus
  19-07 und riss damit drei D-04-Zusicherungen. Der Befund steht unten, der Fix ist ein Commit, und
  der Lauf danach ist der gruene.
- **Drei Zusatzauftraege der Ausfuehrung erledigt:** die Berichtigung von RESEARCH Pattern 7c als
  datierter Vermerk, die Entscheidung gegen einen nachtraeglichen Planeingriff in 19-07-PLAN.md samt
  Begruendung, und die Ein-Wort-Bedingung aus 19-08 in der Grenzen-Doku.
- **Volle Suite 2857 bestanden / 15 uebersprungen**, unveraendert gegenueber 19-08, die vier
  Qualitaetsgates lokal gruen.

## Task Commits

1. **Task 1: Was die Frageseite durchsucht, und was sie nicht leistet** - `d8cd69a` (docs)
2. **Zusatzauftrag 1 und 2: die datierte Berichtigung von RESEARCH Pattern 7c** - `4ea3f20` (docs)
3. **Deviation 1: die Upgrade-Strecke registriert mit der ausgelieferten Sprachvorgabe** - `71cf028` (fix)
4. **Task 2: die gemessene Laufzeit im Budgetkommentar** - `da3858e` (ci)

**Plan metadata:** siehe docs-Commit unten

## Files Created/Modified

- `docs/language-analyzers.md` (GEAENDERT), +101 Zeilen an drei Stellen: der neue Abschnitt
  "What a question searches" vor "The supplement list", zwei Absaetze am Ende von "Measured numbers",
  ein Eintrag an der Spitze von "Known limits". Die Herkunftsangaben der Zeilen 8 bis 12 sind nur
  gelesen und nicht bewegt worden, wie der Plan es verlangt.
- `.github/workflows/deploy-harp.yml` (GEAENDERT), zwei Stellen: der Budgetkommentar ueber
  `LANGUAGE_PROOF_BUDGET_SECONDS` (RE-MEASURE-Absatz gegen zwoelf Zeilen gemessene Zahlen getauscht)
  und die Registrierung in "Store upgrade 4" (+31 Zeilen: Kommentarblock, zwei Einmaligkeitspruefungen,
  ein `sed` und die Protokollzeile).
- `.planning/phases/19-frageseite-freischalten/19-RESEARCH.md` (GEAENDERT), +12 Zeilen: der
  Berichtigungsvermerk unter Pattern 7c. Siehe Zusatzauftraege.

`backend/src/findling` und `php/` sind nicht angefasst, also sind `PACKAGE_TREE_HASH_TODAY`,
`PACKAGE_FILES_TODAY` und `PHP_TREE_HASH_TODAY` unberuehrt und die Ratsche ist nicht beruehrt.
`backend/pyproject.toml` und `backend/uv.lock` stehen in keinem der vier Commits, es ist kein Paket
installiert worden.

## Decisions Made

- **Der Abschnitt heisst "What a question searches".** Der Plan nennt ihn "Was die Frageseite
  durchsucht", und derselbe Plan sagt zwei Absaetze weiter, dass diese Datei englisch geschrieben ist
  und ASCII bleibt, soweit sie es heute ist. Eine deutsche Ueberschrift in einer durchgehend englischen
  Datei waere die Form des Plans gegen seinen eigenen Inhalt. Die Akzeptanzbedingungen verlangen den
  deutschen Wortlaut nicht, und die automatische Pruefung des Plans ist ein ODER ueber
  `schema_version`, das der Abschnitt zweimal traegt.
- **Die Ein-Wort-Bedingung steht im neuen Abschnitt und nicht unter Known limits.** Sie ist keine
  Grenze der Analyseketten, sondern eine Eigenschaft der hybriden Suche, die ein Admin kennen muss:
  eine Frage aus einem Wort verhaelt sich anders als eine aus dreien. Der Absatz sagt beides, die
  Eigenschaft und ihre Folge fuer den CI-Beweis, und er steht direkt hinter der Beschreibung der
  Upgrade-Strecke, wo 19-08 ihn haben wollte.
- **19-07-PLAN.md wird nicht nachtraeglich berichtigt.** Der Auftrag liess beide Wege offen. Ein Plan
  ist das Artefakt einer Planung und kein lebendes Dokument; wer ihn nachtraeglich richtigstellt, macht
  unsichtbar, dass die Ausfuehrung den Irrtum gefunden hat. Der Fund steht in `19-07-SUMMARY.md`
  (Deviation 1), die Quelle des Irrtums ist mit diesem Plan in `19-RESEARCH.md` berichtigt, und der
  Vermerk dort nennt den Plan beim Namen.
- **Das Budget wird nicht gesenkt, obwohl 600 gegen 172 grosszuegig aussieht.** Der Kommentarblock
  sagt seit 19-07, warum die Zahl gegen die Cron-Taktung dimensioniert ist und nicht gegen die
  Arbeitsmenge: die Zusage gilt einer Instanz, deren Systemcron alle fuenf Minuten laeuft und deren
  erster Durchgang den Lauf einreiht statt ihn zu beenden. Eine Senkung auf das Doppelte der Messung
  waere ein Budget gegen die schnellste Umgebung und wuerde auf einer langsamen Instanz reissen,
  ohne dass etwas kaputt ist.
- **Der Wert des langsamsten Astes steht vorn.** arm64 braucht mit 172 s mehr als die drei
  amd64-Aeste zusammen (73 + 41 + 32 = 146 s). Ein Budgetkommentar, der den Mittelwert oder den
  schnellsten Ast nennte, beschriebe eine Umgebung, in der das Budget nie reisst.
- **LEX-05 bleibt ungehakt.** Die Traceability-Tabelle von `REQUIREMENTS.md` traegt fuer LEX-02 bis
  LEX-08 "Complete (24.09.2026, Verifikation 5/5, CI 36026836087)", haekt eine Anforderung also bei der
  Phasenverifikation mit Laufnummer ab. Dieser Plan liefert die Laufnummer; das Abhaken ohne die
  Verifikation waere eine Behauptung ueber eine Pruefung, die noch nicht stattgefunden hat.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die Upgrade-Strecke registrierte mit der sechssprachigen Entwicklerdatei**
- **Found during:** Task 2, beim Einholen des ersten Laufs (36072411846)
- **Issue:** Der Lauf war auf drei Aesten gruen und auf dem Ast stable34/amd64 rot, und zwar in
  "Store upgrade 5" an drei Zusicherungen auf einmal: `.marks.indexVersion` wanderte von 1 auf 2,
  die Adminseite hob das Reindex-Banner, und der Containerlog trug die Zeile
  `start_rebuild_on_drift`. Das sind genau die drei Saetze, mit denen die Strecke die D-04-Linie
  haelt ("ein Upgrade unter der Werkseinstellung laesst eine Bestandsinstallation in Ruhe"). Die
  Ursache steht woertlich im hochgeladenen Containerlog:
  `WARNING:findling.api.resources:the index was built with different versions than this build
  produces, a reindex is required: languages`, dazu die Startwarnung, dass vier Sprachen ohne
  OCR-Abdeckung aktiv sind. "Store upgrade 4" registriert die aufgeruestete Haelfte mit
  `${RUNNER_TEMP}/info-citest.xml`, und genau diese Datei hat Plan 19-07 auf
  `<default>de,en,es,it,nl,pt</default>` gesetzt. AppAPI reicht die Umgebung der info.xml beim
  Registrieren in den Container, der aufgeruestete Container lief also mit sechs Sprachen gegen ein
  Volume, dessen Index gar keine `languages`-Marke traegt;
  `findling.store.repo._languages_are_legacy` liest sechs Sprachen gegen eine fehlende Marke
  korrekt als echten Unterschied, weil die Menge nicht in `de,en` liegt. Der Container hat sich also
  richtig verhalten, die Beweisstrecke hat die falsche Frage gestellt. Bemerkenswert: Zusicherung 7
  von 19-08 (der spanische Wert bleibt 0) hielt auch in diesem Lauf, der Fehler lag ausschliesslich
  in den D-04-Zusicherungen.
- **Fix:** "Store upgrade 4" baut sich vor der Registrierung `${RUNNER_TEMP}/info-upgrade.xml` per
  `sed` aus `info-citest.xml` und setzt die Sprachvorgabe auf die ausgelieferte `de,en` zurueck. Vor
  und hinter der Ersetzung steht je eine Einmaligkeitspruefung mit `grep -cF` und `exit 1`, der
  Kommentarblock nennt die Laufnummer, die Logzeile und den Grund, und die Protokollzeile fuehrt die
  Sprachvorgabe jetzt neben Registry, Image und Tag. Die Sprachumschaltung bleibt, wo sie hingehoert:
  in "Store upgrade 6", ueber die Umgebung des Containers und mit `REBUILD_LANGUAGES='es,de,en'`.
- **Files modified:** keine zusaetzlichen
- **Verification:** Lauf 36074155306 ist auf allen vier Aesten gruen, "Store upgrade 5" und
  "Store upgrade 6" sind beide erfolgreich (vorher: 5 rot, 6 uebersprungen), und die Kette 0, 0, 1
  steht im Protokoll. Der Workflow ist gueltiges YAML (50 Schritte, `yaml.safe_load`), jeder
  `run`-Block ist ein gueltiges Shellskript (`bash -n` ueber alle 46 Bloecke, Rueckgabecode 0), und
  "Store upgrade 4" steht bei 12905 Zeichen ohne `${{`-Ausdruck, also weit unter der
  21000-Zeichen-Grenze.
- **Committed in:** `71cf028`

**2. [Rule 3 - Blocking] Der Abschnittstitel ist englisch**
- **Found during:** Task 1
- **Issue:** Der Plan gibt den Titel als "Was die Frageseite durchsucht" vor und verlangt zwei
  Absaetze weiter, dass die Datei ASCII und englisch bleibt. Beides zusammen geht nicht.
- **Fix:** Der Abschnitt heisst "What a question searches". Siehe Entscheidungen; die automatische
  Pruefung des Plans (`grep -n "Was die Frageseite durchsucht\|schema_version"`) trifft ueber die
  zweite Haelfte, und die Akzeptanzbedingung verlangt einen Abschnitt, der `schema_version` als das
  Tor der Feldliste benennt, nicht einen deutschen Titel.
- **Files modified:** keine zusaetzlichen
- **Verification:** `grep -n "schema_version" docs/language-analyzers.md` findet die Zeile im neuen
  Abschnitt; `grep -ci "spracherkennung\|language detection"` ist 1 und der Kontext sagt, dass es
  keine gibt.
- **Committed in:** `d8cd69a`

**3. [Rule 2 - Missing critical] Der Fussabdruck waechst um 19-RESEARCH.md**
- **Found during:** Task 1, aus den Zusatzauftraegen der Ausfuehrung
- **Issue:** Die Verifikation des Plans verlangt, dass `git diff --name-only` genau
  `docs/language-analyzers.md` und `.github/workflows/deploy-harp.yml` nennt. Die Zusatzauftraege
  verlangen eine Berichtigung in `19-RESEARCH.md`, also eine dritte Datei.
- **Fix:** Die dritte Datei steht in einem eigenen Commit (`4ea3f20`), ist ein Planungsdokument und
  kein Codeartefakt, und sie ist hier als Abweichung benannt statt stillschweigend mitgenommen. Der
  Fussabdruck der beiden Codedateien ist unveraendert der des Plans.
- **Files modified:** `.planning/phases/19-frageseite-freischalten/19-RESEARCH.md`
- **Verification:** `git diff --name-only` ueber die vier Commits nennt genau diese drei Dateien.
- **Committed in:** `4ea3f20`

---

**Total deviations:** 3 auto-fixed (1 Rule 1, 1 Rule 2, 1 Rule 3), keine Rule-4-Vorlage an den Owner.
**Impact on plan:** Deviation 1 ist die einzige mit Gewicht, und sie ist der Grund, warum dieser Plan
einen roten Lauf kennt: die Aufgabe "den Lauf einholen" hat genau das geleistet, wofuer sie da ist.
Kein Scope-Zuwachs an Codedateien, eine zusaetzliche Planungsdatei.

## Zusatzauftraege der Ausfuehrung

1. **RESEARCH Pattern 7c berichtigt.** Der Vermerk steht unmittelbar unter dem falschen Absatz, traegt
   Datum und Plannummer, nennt `PageController::term()` mit
   `$this->request->getParam('query', '')` und der Zeilennummer 340, sagt, was `?term=alemanes`
   geantwortet haette, und grenzt ausdruecklich ab: der Satz zur OCS-Suchroute weiter oben bleibt
   richtig, dort heisst der Parameter wirklich `term`. Selbst nachgesehen statt uebernommen:
   `grep -c "getParam('query'" php/lib/Controller/PageController.php` ist 1,
   `grep -c "getParam('term'"` ist 0.
2. **19-07-PLAN.md bleibt unberuehrt.** Siehe Entscheidungen. Der Auftrag liess diesen Weg
   ausdruecklich zu, weil `19-07-SUMMARY.md` den Fund bereits nennt.
3. **Die Ein-Wort-Bedingung steht in der Grenzen-Doku.** Vierter Absatz des neuen Abschnitts, mit
   `lexical_only`, der Ein-Term-Regel aus 06.1-20, den gemessenen 68 bis 77 auf der int8-L2-Skala
   gegen die Obergrenze 86,5 und dem Satz, was eine Zwei-Wort-Frage aus dem Beweis machen wuerde.

## Threat Flags

Keine neue Angriffsflaeche. Der Plan legt keine Route an, oeffnet keinen Netzpfad und installiert kein
Paket. Die fuenf Eintraege des Registers:

- **T-19-09-01 (Doku beschreibt die Absicht statt des Codes):** der Abschnitt ist gegen
  `api/resources.py` geschrieben; die Torreihenfolge, die geschlossene Lesart einer fehlenden Marke
  und die `doc_freq`-Sonde stehen so in der Datei, wie sie im Code stehen.
- **T-19-09-02 (gruener Lauf ohne arm64):** der Sprachbeweis ist in allen vier Jobs von 36074155306
  gelaufen und in allen vieren erfolgreich, maschinell ueber `gh run view --json jobs` geprueft, und
  das Textgate aus 19-07 haelt die Abwesenheit der `if:`-Zeile weiterhin fest.
- **T-19-09-03 (Store- und Dokutexte, accept):** unveraendert. Dieser Plan schreibt nur
  `docs/language-analyzers.md`; die Grenzenliste des Releases gehoert Phase 23 und wird dort dem Owner
  vorgelegt. Der neue Known-limits-Eintrag sagt das selbst.
- **T-19-09-04 (Budget des CI-Schritts):** das Budget ist nicht angehoben worden, es ist auch nicht
  gerissen: 172 s von 600 auf dem langsamsten Ast.
- **T-19-09-SC (Paketinstallation):** entfaellt mangels Gegenstand, `backend/pyproject.toml` und
  `backend/uv.lock` stehen nicht im Diff.

## Known Stubs

Keiner. Der Stub aus 19-07 (der RE-MEASURE-Absatz im Budgetkommentar) ist mit `da3858e` eingeloest.

## Issues Encountered

- **Der erste Lauf war rot**, und der Fehler lag nicht dort, wo dieser Plan gearbeitet hat, sondern in
  einer Nebenwirkung von 19-07 auf die Upgrade-Strecke. Siehe Deviation 1. Zwei Beobachtungen, die
  ueber diesen Fall hinausgehen: eine Datei, die eine Strecke fuer sich baut, wird von einer anderen
  Strecke mitbenutzt, und der Suchpfad dafuer ist `grep -n info-citest.xml` und nicht das Gedaechtnis;
  und ein Lauf, der auf drei von vier Aesten gruen ist, kann trotzdem eine tragende Zusage reissen,
  weil die tragenden Zusagen hier auf genau einem Ast stehen.
- **Der Containerlog war die Quelle der Diagnose, nicht das Schrittprotokoll.** Die drei roten
  Zusicherungen nennen jeweils die Folge (Marke gewandert, Banner oben, Driftzeile da) und keine von
  ihnen die Ursache. Die Ursache stand in `upgrade-exapp.log` des hochgeladenen Artefakts, in einer
  Zeile, die den diagnostizierenden Namen der Marke ausschreibt.
- **Zweimal ein Werkzeugweg statt eines Fehlers im Inhalt.** Ein `sed` ueber einen Windows-Pfad hat das
  Schreibskript zerlegt, und ein Rueckstrich am Zeilenende innerhalb eines dreifach zitierten
  Python-Strings ist eine Zeilenfortsetzung, wenn der String nicht `r"""` ist: die erste
  Suchzeichenkette traf deshalb nichts. Beide Male half dieselbe Regel wie in 19-08: die Bearbeitung
  laeuft ueber ein Skript, das mit dem Write-Werkzeug geschrieben wird, und die Suchzeichenkette wird
  gegen die Datei geprueft, bevor sie ersetzt.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Die Phasenverifikation hat alles, was sie braucht:** Laufnummer 36074155306, vier gruene Aeste
  (stable33/amd64, stable34/amd64, stable34/arm64, stable35/amd64), der Sprachbeweis viermal
  erschienen und viermal erfolgreich, die Kette 0, 0, 1 im Protokoll von "Store upgrade 3", 5 und 6,
  und die vier Ergebnisseiten-Abrufe auf dem arm64-Ast.
- **LEX-05** ist damit inhaltlich vollstaendig und formal offen; der Haken gehoert der Verifikation,
  die ihn wie bei Phase 18 mit Laufnummer in die Traceability-Tabelle schreibt.
- **Phase 22 (MESS-09)** hat ihre Eingabe in `docs/language-analyzers.md` stehen und muss sie nicht
  aus einer Plan-Summary holen.
- **Phase 23 (REL-03 Kriterium 2)** findet die erste der zu veroeffentlichenden Grenzen unter
  "Known limits", ausgeschrieben mit Messung, Codestelle und Alternative.
- **Der Phasen-Audit (Security, Bugs, Performance) steht aus**, nach der Owner-Regel vom 15.08.2026.
  Er ist der Phasenabschlussschritt und nicht Teil dieses Plans.
- **Ein Nachlauf des Workflows lief zum Zeitpunkt dieser Summary**, ausgeloest vom Commit `da3858e`.
  Dieser Commit aendert ausschliesslich einen YAML-Kommentar im `env:`-Block, also keine Zeile, die
  ein Schritt ausfuehrt; der Beweis dieser Phase ist 36074155306.

## Verification

- **Der Lauf:** `gh run view 36074155306` meldet `conclusion: success` und vier Jobs, alle vier
  `success`: `deploy-harp (stable33, 8.2, false, ubuntu-24.04)`,
  `deploy-harp (stable34, 8.2, false, ubuntu-24.04)`,
  `deploy-harp (stable34, 8.2, false, ubuntu-24.04-arm)`,
  `deploy-harp (stable35, 8.3, false, ubuntu-24.04)`.
- **Der Sprachbeweis viermal:** der Schritt "Language proof, ..." steht in allen vier Jobs mit
  `conclusion: success`. Laufzeiten: arm64 172 s (23:45:38Z bis 23:48:30Z), stable34/amd64 73 s,
  stable33/amd64 41 s, stable35/amd64 32 s.
- **Die acht Zusicherungen des Beweises**, aus dem arm64-Protokoll: vier Zeilen "the ordinary search
  route brings back language-proof-<code>.txt" und vier Zeilen "the result page carries
  language-proof-<code>.txt", dazu vier Loeschungen mit HTTP 204.
- **Die Kette 0, 0, 1**, aus dem Protokoll von stable34/amd64: `"spanish": 0` in "Store upgrade 3",
  `"spanish": 0` in Zusicherung 7 von "Store upgrade 5", `"spanish": 1` in Zusicherung 10 von
  "Store upgrade 6" mit der Zeile "the question alemanes went from 0 to 1 hits across the rebuild".
- **Das Budget:** `grep -c "LANGUAGE_PROOF_BUDGET_SECONDS"` ist 3, der Wert steht unveraendert auf
  `'600'`, `grep -c "RE-MEASURE"` ist 0, und der Kommentarblock nennt Laufnummer, Datum, Matrixast
  und vier gemessene Werte.
- **Die Doku:** `grep -n "schema_version" docs/language-analyzers.md` findet die Zeile im neuen
  Abschnitt; der Known-limits-Eintrag nennt `FIELD_BODY_DE` und `index/search.py:875` und das
  gemessene leere Fragment; unter "Measured numbers" stehen 0,81 (24.09.2026) und 0,26 us
  (24.09.2026); `grep -ci "spracherkennung\|language detection"` ist 1.
- **Form:** kein Em-Dash in `docs/language-analyzers.md` (0 mal U+2014, 0 mal U+2013), die Datei
  behaelt ihre CRLF-Zeilenenden (481 CRLF, 0 alleinstehende LF) und ihren bisherigen
  Nicht-ASCII-Bestand (die akzentuierten Beispielwoerter); `.github/workflows/deploy-harp.yml` ist
  weiterhin reines ASCII (0 Bytes ueber 127).
- **Der Workflow:** gueltiges YAML ueber `yaml.safe_load`, ein Auftrag `deploy-harp` mit 50 Schritten,
  der Beweisschritt an Position 13, "Store upgrade 4" an 46 und "Store upgrade 5" an 47; jeder
  `run`-Block ist ein gueltiges Shellskript (`bash -n` ueber alle 46, Rueckgabecode 0 fuer alle).
- **Die Suite:** `uv run pytest -q` aus `backend/`: **2857 bestanden, 15 uebersprungen, 0
  Fehlschlaege**, unveraendert gegenueber 19-08. `tests/test_language_proof_steps.py` allein: 26
  bestanden.
- **Die Gates:** `uv run ruff check .` All checks passed; `uv run ruff format --check .` 138 files
  already formatted; `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` 0 errors, 0 warnings, 0
  informations; `uv run vulture src tests --min-confidence 80` keine Befunde.
- **Die Commits:** `git show --name-only` der vier Commits nennt genau `docs/language-analyzers.md`
  (einmal), `.planning/phases/19-frageseite-freischalten/19-RESEARCH.md` (einmal) und
  `.github/workflows/deploy-harp.yml` (zweimal); keiner von ihnen loescht eine Datei
  (`git diff --diff-filter=D` ueber die Spanne ist leer).

---
*Phase: 19-frageseite-freischalten*
*Completed: 2026-09-25*

## Self-Check: PASSED

Die drei geaenderten Dateien liegen auf der Platte, die vier Commits `d8cd69a`, `4ea3f20`, `71cf028`
und `da3858e` stehen in der Historie und nennen zusammen genau diese drei Dateien, keiner von ihnen
loescht etwas (`git diff --diff-filter=D` ueber die Spanne ist leer), der Haken fuer 19-09 steht in
ROADMAP.md und die Fortschrittszeile der Phase ist auf 9/9 nachgezogen (sie stand auf 8/9), und
STATE.md ist von Hand nachgezogen (Frontmatter, Position mit dem 19-09-Absatz, ein vollstaendig neu
geschriebener Abschnitt "Naechster Schritt", ein neuer Eintrag unter den Entscheidungen, die
erledigte Kleinigkeit zum Textauszug und die Sitzungsfortschreibung). Kein Em-Dash in STATE.md,
ROADMAP.md, der Doku, dem Workflow oder dieser Datei; der Workflow ist weiterhin reines ASCII. Das
Arbeitsverzeichnis traegt ausser den Planungsdateien nichts Offenes; die Einmal-Skripte, ueber die
Doku, Research und Workflow bearbeitet wurden, liegen ausserhalb des Repos im Temp-Verzeichnis und
stehen in keinem Commit.

Der Lauf, den der Commit `da3858e` ausgeloest hat (36076006854), lief zum Zeitpunkt dieser Zeile
noch. Er aendert nur einen YAML-Kommentar im `env:`-Block und keine Zeile, die ein Schritt ausfuehrt;
der Beweis dieser Phase bleibt 36074155306.
