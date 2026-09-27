---
phase: 17-owner-tor-und-analyseketten
plan: 01
subsystem: planning
tags: [owner-tor, entscheiddokument, tantivy, versionsmarken, d-04, lex-01, lex-07]

# Dependency graph
requires:
  - phase: 12-messwerkzeug-runbook-und-terminentscheid
    provides: "12-STABLE35-ENTSCHEID.md als Formvorlage eines Owner-Tors (Kopfmuster, Ist/Soll-Tabelle, Vollzugsmuster, Checkliste)"
  - phase: 17-owner-tor-und-analyseketten
    provides: "17-RESEARCH.md mit den acht Entscheiden, den vier tantivy-Messbelegen und der Tabelle was vor dem Tor laufen darf"
provides:
  - "17-GRUNDSATZ-ENTSCHEID.md: acht vollstaendig ausformulierte Entscheide E-17-1 bis E-17-8 mit je zwei Optionen"
  - "Scharfe Definition von D-04 beruehren plus acht Zeilen, welche Arbeit vor dem Tor laufen darf"
  - "Ist/Soll-Tabelle der sieben Stellen, die der tantivy-Pin-Sprung rot macht"
  - "Sechs wortwoertlich einsetzbare Ersatztextbloecke fuer pyproject.toml, test_upgrade_compatibility.py, repo.py, deploy-harp.yml, dependabot.yml und THIRD-PARTY.md"
  - "Leerer, datierbarer Vollzugsabschnitt und siebenschrittige Vollzugs-Checkliste"
affects: [17-02, 17-03, 17-04, 17-05, 17-06, 17-07, 17-08, 18-schema-marken-und-umbauweg, 20-ui-kataloge, 21-niederlaendische-komposita]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Owner-Tor nach dem Muster von 12-STABLE35-ENTSCHEID.md: alle Zweige vor der Vorlage ausformuliert, am Vorlagetag wird nur gelesen"
    - "Optionskennung als Zitierform (E-17-7 Option a) statt Zusammenfassung"

key-files:
  created:
    - .planning/phases/17-owner-tor-und-analyseketten/17-GRUNDSATZ-ENTSCHEID.md
  modified: []

key-decisions:
  - "E-17-7 wird als erste Frage der Vorlage gestellt, weil 17-07 und 17-08 und die Formulierung von LEX-07 daran haengen"
  - "D-04 beruehren ist auf genau drei Vorgaenge festgelegt: eine der fuenf Versionsmarken bewegen, ein Schemafeld anlegen, die Query-Feldliste erweitern"
  - "Der Hash der gefalteten Ergaenzungsliste darf nur Testwert sein, nie sechste Marke, sonst Reindex auf jeder Bestandsinstallation"
  - "Der ignore-Eintrag in .github/dependabot.yml existiert bereits (Owner-Datum 2026-09-21); nur sein Begruendungskommentar ist sachlich falsch und wird berichtigt"
  - "Der Union-Scorer-Bugfix in 0.26.2 ist unbelegt und wird aus jeder Begruendung gestrichen"

patterns-established:
  - "Entscheidfeldfolge: Empfehlung, Beleg, Option a und b je mit Greift-wenn, Beweisgrundlage, Vollzug"
  - "Ersatztexte tragen den Platzhalter <VORLAGETAG>, den der vollziehende Plan durch das Datum ersetzt"

requirements-completed: [LEX-01, LEX-07]

# Metrics
duration: 25min
completed: 2026-09-23
---

# Phase 17 Plan 01: Owner-Tor als Entscheiddokument Summary

**Acht vorlagereife Grundsatzentscheide E-17-1 bis E-17-8 mit je zwei Optionen, einer scharfen D-04-Leitplanke und sechs wortwoertlich einsetzbaren Ersatztexten fuer den tantivy-Sprung**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-23T17:00:00Z
- **Completed:** 2026-09-23T17:25:25Z
- **Tasks:** 3
- **Files modified:** 1 (neu angelegt)

## Accomplishments

- `17-GRUNDSATZ-ENTSCHEID.md` (803 Zeilen) nach dem Muster von `12-STABLE35-ENTSCHEID.md` angelegt: Kopfblock, Die Frage, Was festgestellt ist, Was unklar ist, Leitplanke, Die acht Entscheide, Die fertigen Ersatztexte, Vollzug, Checkliste.
- Alle acht Entscheide so ausformuliert, dass am Vorlagetag kein Satz mehr entworfen werden muss: 16 Optionen mit je `Greift, wenn`, `Beweisgrundlage` und `Vollzug` (welcher Plan der Phase 17 oder 18 den Zweig ausfuehrt).
- Die sieben Stellen, die der Pin-Sprung rot macht, stehen als Ist/Soll-Tabelle mit vier Spalten (Ist, Ziel bei Option a, Ziel bei Option b) im Dokument, jede Zeile mit einer Datei aus dem Baum.
- Sechs Ersatztextbloecke sind einsetzbar, inklusive des Hilfsvergleichers `_index_format_matches` nach dem Muster von `_generation_at_least`, der eigenen `tantivyVersion`-Pruefung in `deploy-harp.yml` nach dem Muster von Zusicherung 6 und der vierten Selbstprobe im Gold-Test.
- Zwei Irrtuemer der Recherche sind im Dokument ausdruecklich berichtigt: der `ignore`-Eintrag in `.github/dependabot.yml` existiert bereits (RESEARCH 4.1 und 4.4 sagen das Gegenteil), und der "Union-Scorer-Bugfix in 0.26.2" ist in den Release Notes nicht auffindbar.

## Task Commits

Jede Aufgabe wurde einzeln committet:

1. **Task 1: Geruest, Feststellungen und die Leitplanke "D-04 beruehren"** , `476ed46` (docs)
2. **Task 2: Die acht Entscheide E-17-1 bis E-17-8 ausformulieren** , `e604dc9` (docs)
3. **Task 3: Fertige Ersatztexte, leerer Vollzugsabschnitt und Checkliste** , `f489314` (docs)

## Files Created/Modified

- `.planning/phases/17-owner-tor-und-analyseketten/17-GRUNDSATZ-ENTSCHEID.md` , das Owner-Tor der Phase: acht Entscheide, sechs Ersatztexte, leerer Vollzugsabschnitt, siebenschrittige Checkliste.

Kein Quelltext des Backends, kein Workflow und keine Lizenzdatei wurden angefasst;
`git status --porcelain backend/ .github/ THIRD-PARTY.md` ist leer.

## Decisions Made

- **Zeilennummern aus dem Baum statt aus der Recherche.** `THIRD-PARTY.md` traegt die tantivy-Tabellenzeile auf 138 und den Begruendungsabsatz auf 151 bis 156, nicht auf 139 und 150 bis 155 wie im Plan genannt. Im Dokument stehen die gelesenen Nummern.
- **`GOLD_INDEX_FORMAT` wandert im Ersatztext vor `GOLD_V1_0_AND_V1_1`.** Anders liesse sich die Konstante nicht als Gold-Wert der Marke einsetzen, weil sie heute nach dem Woerterbuch definiert ist. Der Ersatztext sagt das ausdruecklich.
- **`.github/dependabot.yml` wird auch unter E-17-7 Option b berichtigt.** Die Formatbehauptung ist unabhaengig vom Pin falsch; ein stehengelassener falscher Begruendungstext waere eine Falle fuer den naechsten Leser. Der Plan liess fuer Option b "keine Aenderung" zu, die Leitplanke des Dokuments verlangt aber Belegtreue.
- **Der Satz zu den Snowball-Stoppwortlisten gilt in beiden Zweigen.** Die Ketten dieser Phase benutzen sie unabhaengig vom Pin, also gehoert der Lizenzsatz auch dann in `THIRD-PARTY.md`, wenn der Pin stehen bleibt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Falsche Zeilennummern fuer THIRD-PARTY.md aus dem Plan uebernommen**
- **Found during:** Task 3
- **Issue:** Der Plan nennt Zeile 139 fuer die tantivy-Tabellenzeile und 150 bis 155 fuer den Begruendungsabsatz. Gelesen am 2026-09-23 stehen sie auf 138 und 151 bis 156. Eine falsche Fundstelle in einem Dokument, aus dem ein spaeterer Plan wortwoertlich kopiert, ist ein Fehler, der sich fortpflanzt.
- **Fix:** Die gelesenen Nummern stehen im Ersatztextblock.
- **Files modified:** `.planning/phases/17-owner-tor-und-analyseketten/17-GRUNDSATZ-ENTSCHEID.md`
- **Verification:** `sed -n 130,160p THIRD-PARTY.md` zeigt die Tabellenzeile auf 138.
- **Committed in:** `f489314`

**2. [Rule 2 - Missing Critical] Berichtigung des dependabot-Kommentars auch unter E-17-7 Option b**
- **Found during:** Task 3
- **Issue:** Der Plan sah fuer Option b je Stelle "keine Aenderung" vor. Fuer `.github/dependabot.yml` waere das falsch: der Kommentar behauptet, `index_format v7` komme erst ab 0.26.2, und diese Behauptung ist durch die eigene Messung widerlegt, unabhaengig davon, ob der Pin sich bewegt.
- **Fix:** Der Block fuer Option b sagt ausdruecklich, dass der Begruendungstext trotzdem berichtigt wird, ohne den Satz zur gelockerten Vergleichsregel. Derselbe Gedanke gilt fuer den Snowball-Lizenzsatz in `THIRD-PARTY.md`.
- **Files modified:** `.planning/phases/17-owner-tor-und-analyseketten/17-GRUNDSATZ-ENTSCHEID.md`
- **Verification:** Beide Abschnitte tragen den Option-b-Absatz; die Leitplanke des Dokuments bleibt widerspruchsfrei.
- **Committed in:** `f489314`

---

**Total deviations:** 2 auto-fixed (1 Bug, 1 Missing Critical)
**Impact on plan:** Beide betreffen die Belegtreue des Dokuments, aus dem spaetere Plaene wortwoertlich kopieren. Kein Scope Creep, kein Quelltext beruehrt.

## Issues Encountered

Keine. Die Bash-Sandbox dieses Worktrees lehnt zusammengesetzte Kommandos ab, deshalb wurden die Verifikationsketten der drei Aufgaben in Einzelkommandos zerlegt und einzeln gefahren; die geprueften Bedingungen sind dieselben.

## Verification

- Acht Ueberschriften in der vorgegebenen Reihenfolge, gepruefte Abschnittsfolge ueber `grep -n "^#\+ "`.
- `grep -cE "^### E-17-[1-8]:"` gleich 8, `^#### Option a:` gleich 8, `^#### Option b:` gleich 8.
- `Greift, wenn` 16 mal, `Beweisgrundlage` 16 mal, `Vollzug:` 16 mal.
- Das woertliche Zitat "A mark that was never written counts as diverging" ist vorhanden; `custom_stopword` ist vorhanden.
- Alle sechs betroffenen Dateipfade sind im Dokument genannt; `## Vollzug am`, `### Vollzugs-Checkliste`, "ein roter Lauf ist ein Befund" und `uv lock --upgrade-package tantivy` sind vorhanden.
- 803 Zeilen (verlangt: mindestens 200), keine Em-Dashes (U+2013 und U+2014 per Python geprueft), keine Emojis, deutsche Prosa mit echten Umlauten.
- `git status --porcelain` zeigt ausserhalb von `.planning/` nichts.

## Known Stubs

Der Abschnitt `## Vollzug am <Datum>` ist absichtlich leer und traegt in allen
Feldern `,`. Das ist kein Stub im Sinne fehlender Funktionalitaet, sondern das
vom Muster geforderte Format: Plan 17-04 fuellt ihn am Vorlagetag. Ebenso ist der
Platzhalter `<VORLAGETAG>` in den sechs Ersatztexten gewollt; er wird von den
Plaenen 17-07 und 17-08 ersetzt.

## User Setup Required

None. Der Owner-Entscheid selbst wird von Plan 17-04 als Checkpoint vorgelegt.

## Next Phase Readiness

- Die Plaene 17-02, 17-03, 17-05 und 17-06 duerfen sofort laufen: die Leitplanke stellt fest, dass Positivliste, Kettenfabrik ohne Registrierung, Messung und Dokumentation D-04 nicht beruehren.
- Die Plaene 17-07 und 17-08 sind blockiert, bis Plan 17-04 den Vollzugsabschnitt datiert gefuellt hat.
- Phase 18 kann E-17-1, E-17-2, E-17-3 und E-17-4 als Optionskennung zitieren; die Saat-Auflage zum sechsten Merker steht ausformuliert in E-17-4 Option a.

## Self-Check: PASSED

- `.planning/phases/17-owner-tor-und-analyseketten/17-GRUNDSATZ-ENTSCHEID.md` , vorhanden.
- `.planning/phases/17-owner-tor-und-analyseketten/17-01-SUMMARY.md` , vorhanden.
- Commits `476ed46`, `e604dc9`, `f489314` , alle drei in `git log` gefunden.

---
*Phase: 17-owner-tor-und-analyseketten*
*Completed: 2026-09-23*
