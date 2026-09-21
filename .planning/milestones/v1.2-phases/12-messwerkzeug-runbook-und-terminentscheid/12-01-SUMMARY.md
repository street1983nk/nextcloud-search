---
phase: 12-messwerkzeug-runbook-und-terminentscheid
plan: 01
subsystem: infra
tags: [ci, github-actions, deploy-harp, nextcloud-35, versionsfenster, entscheidungsnotiz]

requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: "Vorentscheid V-2 (Fenster bleibt 33 bis 35, Flag bleibt), RE-CHECK-Vermerk in deploy-harp.yml mit Nachfolge-Adresse Plan 11-11"
provides:
  - "Entscheidungsnotiz 12-STABLE35-ENTSCHEID.md mit Beleglage zum stable35-Fenster (HART-03)"
  - "Option a (D-01/D-02) und Option b (D-03) vollstaendig ausformuliert, vor dem Stichtag"
  - "Zwei kopierfertige YAML-Ersatztexte fuer .github/workflows/deploy-harp.yml"
  - "Vollzugs-Abschnitt mit sechs Feldern und siebenschrittiger Checkliste fuer den 16.09.2026"
  - "Feststellung mit Beleg: beide info.xml stehen bereits auf max-version 35, dort ist nichts zu tun"
affects: [12-02-stable35-vollzug, 16-haertung-und-store-einreichung-v1-2]

tech-stack:
  added: []
  patterns:
    - "Fristgebundener Entscheid: beide Zweige vor dem Stichtag ausformulieren, am Stichtag nur lesen und einsetzen"
    - "Platzhalter-Konvention fuer erst am Stichtag bekannte Tatsachen (FINAL-TAG, FINAL-DATUM, RUN-ID bzw. NEUESTE-35-MARKE, NEUESTE-FREIGABE, NEUER-RE-CHECK)"

key-files:
  created:
    - .planning/phases/12-messwerkzeug-runbook-und-terminentscheid/12-STABLE35-ENTSCHEID.md
  modified: []

key-decisions:
  - "Der Entscheid wird als eigene Notiz im Phasenordner gefuehrt, nicht nur als YAML-Kommentar (Ermessensspielraum aus 12-CONTEXT.md)"
  - "Der Ersatztext von Option a ersetzt den gesamten Bereich Zeile 211 bis 273, weil auch der einleitende Zweig-Hinweis mit der Freigabe von NC 35 unwahr wird"
  - "Neue Nachfolge-Adresse bei Option b ist die Store-Einreichung der Phase 16, der neue RE-CHECK-Termin der Tag davor; damit haengt der Entscheid an einem Arbeitsschritt statt an einem Kalendereintrag"

patterns-established:
  - "Entscheidungsnotiz nach der Form von 11-VORENTSCHEIDE.md: Was festgestellt ist, Was unklar ist, Leitplanke, Option a, Option b"
  - "Extrapolationen werden ausdruecklich als solche gekennzeichnet und tragen keinen Entscheid"

requirements-completed: []  # HART-03 ist vorbereitet, aber erst nach dem Vollzug in Plan 12-02 (16.09.2026) erfuellt

duration: 14min
completed: 2026-09-14
---

# Phase 12 Plan 01: stable35-Fenster-Entscheid Summary

**Beide Zweige des fristgebundenen stable35-Entscheids liegen zwei Tage vor der Frist fertig ausformuliert vor, inklusive zweier kopierfertiger YAML-Ersatztexte fuer deploy-harp.yml und einer siebenschrittigen Vollzugs-Checkliste.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-09-14T16:32:00Z
- **Completed:** 2026-09-14T16:46:00Z
- **Tasks:** 2
- **Files modified:** 1 (neu angelegt)

## Accomplishments

- Beleglage mit Datei-und-Zeile-Nachweisen: das deklarierte Versionsfenster steht bereits auf `min-version="33" max-version="35"` (`php/appinfo/info.xml:219`, `backend/appinfo/info.xml:225`). Die Notiz sagt ausdruecklich, dass D-01 ("auf max NC 35 heben") in den `info.xml` nichts zu tun laesst, damit kein Folgeplan eine erledigte Aufgabe aufnimmt.
- Offener Punkt sauber eingegrenzt: ausschliesslich der Matrixeintrag `server-version: stable35` mit `tolerate-failure: true` und der RE-CHECK-Kommentarblock in `.github/workflows/deploy-harp.yml` (Zeilen 211 bis 273).
- Releasestand vom 14.09.2026 als Tabelle belegt (v35.0.0rc4 prerelease, v34.0.4 Freigabe, v33.0.9 Freigabe), plus Existenz beider `stable35`-Zweige und der Zeitplan-Zusatz "date not final".
- Drei Leitplanken festgeschrieben, allen voran `backend/tests/test_lockstep_versions.py:387`: der Matrixeintrag darf nicht entfernt werden, nur sein Flag darf fallen.
- Zwei wortwoertlich einsetzbare YAML-Ersatztexte (Option a: Absatz entfaellt, `tolerate-failure: false`; Option b: Flag bleibt, Terminzeile umgeschrieben, Vermerkskette fortgeschrieben) mit klar erkennbaren Platzhaltern fuer die erst am Stichtag bekannten Tatsachen.
- Vollzugs-Abschnitt mit sechs leeren Feldern und einer Checkliste in genau sieben Schritten, die Plan 12-02 abarbeitet.

## Task Commits

Each task was committed atomically:

1. **Task 1: Entscheidungsnotiz mit Beleglage und beiden Optionen anlegen** - `ac2e425` (docs)
2. **Task 2: Beide YAML-Ersatztexte und die Vollzugs-Checkliste ergaenzen** - `d8b6324` (docs)

## Files Created/Modified

- `.planning/phases/12-messwerkzeug-runbook-und-terminentscheid/12-STABLE35-ENTSCHEID.md` (267 Zeilen) - Beleglage, beide Optionen, beide YAML-Ersatztexte, Vollzugs-Abschnitt mit Checkliste

## Decisions Made

- **Ersatztext Option a umfasst auch den einleitenden Zweig-Hinweis.** Der Plan nennt den RE-CHECK-Absatz; der Hinweis darueber ("stable35 exists in both repositories ... The line has an expiry date: once Nextcloud 35 is released ... this comment stops being true") wird mit derselben Freigabe unwahr. Der Ersatztext deckt deshalb den zusammenhaengenden Bereich Zeile 211 bis 273 ab, damit Plan 12-02 einen einzigen Block ersetzt statt zweier verstreuter Stellen.
- **Option b wird als zwei benannte Eingriffe beschrieben** (Terminzeile umschreiben, neuen Vermerk vor `tolerate-failure: true` einfuegen) statt als ein Vollersatz des 60-Zeilen-Blocks. So bleibt die vorhandene Vermerkskette unangetastet, was das Fortschreibemuster der Datei genau so verlangt.
- **Der Matrixeintrag steht im Ersatztext von Option a vollstaendig mit** (`php-version: '8.3'`, `runner: ubuntu-24.04`), damit die Leitplanke aus `test_lockstep_versions.py:387` beim Kopieren nicht versehentlich verletzt wird.

## Deviations from Plan

Die beiden Tasks selbst liefen exakt wie geschrieben. Zwei Korrekturen betrafen
die Zustandsfuehrung nach den Tasks:

### Auto-fixed Issues

**1. [Rule 1 - Bug] HART-03 war verfrueht als Complete markiert**
- **Found during:** State-Updates nach Task 2
- **Issue:** Die Plan-Frontmatter nennt `requirements: [HART-03]`, also setzte `requirements.mark-complete` die Anforderung in `.planning/REQUIREMENTS.md` auf erledigt. HART-03 verlangt aber einen "vollzogenen und dokumentierten" Entscheid; Plan 12-01 bereitet ihn nur vor, der Vollzug faellt am 16.09.2026 in Plan 12-02, das dieselbe Anforderung traegt.
- **Fix:** Die Aenderung an `.planning/REQUIREMENTS.md` wurde zurueckgenommen (HART-03 steht wieder auf Pending). In dieser Zusammenfassung steht `requirements-completed: []` mit Begruendung, und `STATE.md` haelt beim 16.09.-Termin ausdruecklich fest, dass HART-03 erst nach dem Vollzug erfuellt ist.
- **Files modified:** .planning/REQUIREMENTS.md (zurueckgesetzt), .planning/STATE.md
- **Verification:** `grep HART-03 .planning/REQUIREMENTS.md` zeigt wieder `- [ ]` und `| HART-03 | Phase 12 | Pending |`
- **Committed in:** Metadaten-Commit dieses Plans

**2. [Rule 2 - Missing Critical] Em-Dashes in der von der Zustandsverwaltung geschriebenen STATE.md**
- **Found during:** State-Updates nach Task 2
- **Issue:** Die Zustandsverwaltung schrieb zwei Zeilen, in denen ein U+2014 den Phasennamen von seinem Zusatz trennte (Current focus und Current Position). Em-Dashes sind im Projekt gesperrt.
- **Fix:** Beide Zeilen auf Doppelpunkt beziehungsweise Komma umgeschrieben, dabei auch die von der Zustandsverwaltung geleerte Fortschritts- und Aktivitaetszeile wieder mit Inhalt versehen.
- **Files modified:** .planning/STATE.md
- **Verification:** `grep` auf U+2014 und U+2013 in `STATE.md` und `ROADMAP.md` liefert keinen Treffer
- **Committed in:** Metadaten-Commit dieses Plans

---

**Total deviations:** 2 auto-fixed (1 Bug, 1 fehlende Pflichtregel)
**Impact on plan:** Kein Scope Creep. Beide Korrekturen betreffen nur die
Zustandsdateien, nicht die Artefakte des Plans.

## Issues Encountered

None. Alle Belegwerte lagen ueber den `<interfaces>`-Block des Plans und Befund 5 der Recherche vor; es war keine eigene Erkundung und kein API-Aufruf noetig.

## Known Stubs

Der Abschnitt `## Vollzug am 16.09.2026` traegt bewusst leere Felder ("(offen)") und die YAML-Ersatztexte tragen bewusst Platzhalter (`<FINAL-TAG>`, `<FINAL-DATUM>`, `<RUN-ID>`, `<NEUESTE-35-MARKE>`, `<NEUESTE-FREIGABE>`, `<NEUER-RE-CHECK>`). Das ist kein unfertiger Zustand, sondern der Zweck des Plans: diese Stellen sind erst am 16.09.2026 bekannt und werden von Plan 12-02 gefuellt. Das Erfolgskriterium des Plans benennt genau diese sechs Platzhalter als die einzigen offenen Stellen.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 12-02 kann am 16.09.2026 ohne Entwurfsarbeit vollziehen: Releasestand lesen, Zweig bestimmen, Block kopieren, Platzhalter ersetzen, Felder fuellen, Owner-Bestaetigung einholen.
- Bei Option a ist zusaetzlich ein gruener `deploy-harp`-Lauf gegen stable35 noetig (D-02); er kostet Wartezeit, kein Geld. Befund A aus Plan 11-11 (Uninstall-Gate-Schwellen) ist als Lesehilfe fuer einen roten Lauf in der Notiz vermerkt.
- Offen und nicht entscheidbar vor dem Stichtag: ob NC 35 am 16.09.2026 tatsaechlich final wird. Der offizielle Zeitplan nennt das Datum selbst als nicht endgueltig, Option b ist deshalb gleichwertig ausgearbeitet.

## Self-Check: PASSED

- `.planning/phases/12-messwerkzeug-runbook-und-terminentscheid/12-STABLE35-ENTSCHEID.md` FOUND (267 Zeilen, min_lines 90 erfuellt)
- Commit `ac2e425` FOUND
- Commit `d8b6324` FOUND
- Automatisierte Verifikation aus Task 1 und Task 2: beide GRUEN (Option a/b, `max-version="35"`, `test_lockstep_versions.py`, `v35.0.0rc4`, `tolerate-failure: false`, `<RUN-ID>`, `<NEUER-RE-CHECK>`, `## Vollzug am 16.09.2026`, keine U+2014/U+2013)
- Vokabular-Gate: das gesperrte Wort kommt in der Notiz nicht vor (0 Treffer)

---
*Phase: 12-messwerkzeug-runbook-und-terminentscheid*
*Completed: 2026-09-14*
