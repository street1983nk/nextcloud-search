---
phase: 12-messwerkzeug-runbook-und-terminentscheid
verified: 2026-09-16T13:13:29Z
status: passed
score: 11/11 must-haves verified
overrides_applied: 0
---

# Phase 12: Messwerkzeug, Runbook und Terminentscheid - Verification Report

**Phase Goal:** Das Messwerkzeug, das Runbook und der fristgebundene Versionsentscheid stehen fest, bevor die eine bezahlte Box-Anfahrt beginnt
**Verified:** 2026-09-16T13:13:29Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Fremdbestands-Vorpruefung misst ueber die Diagnose-Route (`ranked_sides`) statt der gedeckelten OCS-Route, Schwelle 64 wird ueberhaupt pruefbar | VERIFIED | `docs/measurements/2026-09-v12-messung/skripte/73-bestand-sonde.py:36-38,102-125` importiert `ranked_sides`, `read_side`, `build_query` aus dem Produktionscode und misst `side.index.searcher().search(rewritten.query, 1, count=True).count` im Container-Prozess (ungedeckelt, keine Route, kein Prozessgrenzuebertritt). `SCHWELLE = 64` (Zeile 59) statt der alten OCS-Deckelung 26. Von `98c-sprachfaelle.sh` Abschnitt 0 aufgerufen |
| 2 | `aws_box.sh` baut ein Volume aus `snap-03f1d1d9ad9262704` ohne manuelle Nacharbeit auf der Box | VERIFIED | `scripts/ops/aws_box.sh:404-590` `cmd_restore`: liest Snapshot-ID (Argument/`CORPUS_SNAPSHOT_ID`/gepinnte Konstante), verifiziert Snapshot-Status und Groesse, findet/erzeugt Volume, taggt es um mit Rueckleseprobe, wartet (`ec2 wait volume-available`/`volume-in-use`), haengt es an die Instanz an, schreibt `VOLUME_FROM_SNAPSHOT` in `box.env`. Endet bewusst beim Attach (Mount ist laut D-09/D-10 ein Runbook-Schritt). Annahme A3 lesend bestaetigt in `docs/measurements/2026-09-v12-messung/rohdaten/01-aws-lesende-proben.txt` (Snapshot completed, 100%, 60GB, `purpose=findling-corpus-keep`) |
| 3 | `docs/runbook-messbox.md` beschreibt Anfahrt, Messreihenfolge, Vergleichbarkeitsbedingungen und Abbau vollstaendig, waehrend der Anfahrt muss kein Werkzeug mehr geaendert werden | VERIFIED | Datei hat 1008 Zeilen, 9 Abschnitte (1 Geltung, 2 Deckel-Rechenblatt, 3 Vorbedingungen, 4 Aufbau, 5 Zustandspruefung, 6 Vergleichbarkeitsbedingungen, 7 Messreihenfolge mit Abbruchpfaden, 8 Abbau-Checkliste, 9 Kostenfuehrung), 24 Copy-paste-Kommandobloecke (48 Fence-Marker). Abschnitt 2 rechnet den Deckel nach (36h07 Planwert, 0,115841 USD/h, 41,54h, 4,8653 USD, stimmt mit Review-Nachrechnung ueberein). Abschnitt 7 fuehrt alle zwoelf Rueckgabewerte (15-19, 22-28) deckungsgleich mit dem tatsaechlichen Exit-Code-Katalog der Skripte |
| 4 | Cron-Intervall der Zielinstanz ist Pflichtfeld im Messprotokoll; ein Lauf ohne protokolliertes Intervall gilt als unvollstaendig | VERIFIED | `docs/measurements/2026-09-v12-messung/skripte/97-cron-vorpruefung.sh`: Zweig `vorher` liest den Takt aus drei Quellen, schreibt Pflichtzeile `cron-intervall-ist`, bricht mit Exit 25 (keine Quelle) bzw. 26 (>10% Abweichung vom Soll 300s) ab — beide Abbrueche liegen unterhalb der `tee`-Pipeline und sind damit erzwungen, nicht nur dokumentiert. Zweig `waehrend` misst den tatsaechlichen Scheibenabstand mit fruehem Befund-Abbruch bei zwei aufeinanderfolgenden Ueberschreitungen und regulaerem Ende bei leerem Vorrat (WR-02-Fix, Zeilen 293-390) |
| 5 | stable35-Fenster-Entscheid ist bis zum 16.09.2026 getroffen und mit Begruendung dokumentiert | VERIFIED | `.planning/phases/12-messwerkzeug-runbook-und-terminentscheid/12-STABLE35-ENTSCHEID.md` Abschnitt "Vollzug am 16.09.2026": Zweig a (NC 35 final, v35.0.0 vom 15.09.2026, prerelease=false UND draft=false gegengeprueft), Beweislauf 35095805558 (workflow_dispatch, Commit ae59435) live per `gh run view` bestaetigt: `conclusion=success`, stable35-Ast `deploy-harp (stable35, 8.3, true, ubuntu-24.04)` = success. `.github/workflows/deploy-harp.yml:214-233` traegt den fortgeschriebenen Kommentar mit Run-ID, `tolerate-failure: false`. Regelbetriebslauf 35097678552 (Push-Trigger auf Commit 1fa32f6, nach dem Flip) live gegengeprueft: `conclusion=success`, stable35-Ast jetzt `(stable35, 8.3, false, ubuntu-24.04)` = success — bestaetigt den muss-gruen-Zustand unter Alltagsbedingungen |

**Score:** 5/5 ROADMAP-Erfolgskriterien verifiziert

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| MESS-04 | 12-01/03/04/05/07/08 | Werkzeug und Runbook vor der Anfahrt (Diagnose-Route, `aws_box.sh restore`, Runbook-Erstfassung) | SATISFIED | Truths 1-3 oben; `REQUIREMENTS.md:27` als `[x] Complete` markiert, Traceability-Tabelle Zeile 69 "Complete" |
| MESS-06 | 12-06/07/08 | Cron-Intervall vor jedem Messlauf protokolliert, Vergleichbarkeitsbedingungen im Runbook | SATISFIED | Truth 4 oben plus Runbook Abschnitt 6 (fuenf protokollpflichtige Vergleichbarkeitsgroessen); `REQUIREMENTS.md:29` `[x] Complete` |
| HART-03 | 12-01/02 | stable35-Fenster-Entscheid RE-CHECK 16.09.2026 vollzogen und dokumentiert | SATISFIED | Truth 5 oben; `REQUIREMENTS.md:35` `[x] Complete`, Traceability-Tabelle Zeile 74 "Complete" |

Keine Waisen: alle drei der Phase zugeordneten Requirements sind in Plan-Frontmatter (`requirements:` Felder von 12-01/02/06) referenziert und in REQUIREMENTS.md korrekt abgehakt.

### Code-Review-Fixes (12-REVIEW.md, 2 Critical + 5 Warnings)

| ID | Befund | Status | Beleg im Code |
|---|---|---|---|
| CR-01 | 98c bricht bei nicht fahrbarer Sonde nicht vor dem Upload ab | FIXED | `98c-sprachfaelle.sh:346-356` fruehes `exit 1` nach Abschnitt-0-Fehlschlag, zusaetzlich `user:add`-Fehlpfad Zeilen 383-391 mit kontrolliertem `exit 1`. Commit `bbbf550` |
| CR-02 | Work-stock-Guard fehlt in der Arbeitsvorrat-Schleife von 98c | FIXED | `98c-sprachfaelle.sh:442-456` `grep -q '^Work stock'`-Guard mit `unklar`-Sentinel, identisch zum Muster in 97. Commit `4b7afb9` |
| WR-01 | cmd_restore kann fremdes/leeres Volume anhaengen | FIXED | `aws_box.sh:481` Filter `Name=snapshot-id,Values=$snapshot_id`, Zeilen 488-499 Abbruch bei mehr als einem Kandidaten statt stillschweigender Neuerzeugung. Commit `e41adb5` |
| WR-02 | Wirkungszweig von 97 kann Anfahrt nicht anhalten (immer volle 27h) | FIXED | `97-cron-vorpruefung.sh:304-390` frueher Befund-Abbruch bei `BEFUND_ABSTAENDE` aufeinanderfolgenden Ueberschreitungen, regulaeres Ende bei `NULL_RUNDEN_ENDE` leeren Runden. Commit `fe39cc8` |
| WR-03 | 98c laesst Instanz bei Abbruch in Abschnitt 1 mit geleertem skeletondirectory zurueck | FIXED | `98c-sprachfaelle.sh:359-391` (Marke vor dem Setzen, fail-safe `user:add`-Pfad), zusaetzlich Ruecksetzung unterhalb der Pipeline `98c-sprachfaelle.sh:770-777`, greift bei jedem Abbruchpfad. Commit `f889273` |
| WR-04 | Keine Verhaltens-Tests fuer Verweigerungspfade von 98c/97 | FIXED | `backend/tests/test_measurement_scripts.py:1250-1288` zwei neue boxlose Tests (`test_the_v12_fassung_refuses_a_run_without_a_ci_run_number`, `test_the_cron_precheck_refuses_a_run_without_a_known_branch`), beide laufen gruen. Commit `5b29a2d` |
| WR-05 | Veralteter Kommentar/tote Matrix-Mechanik in deploy-harp.yml | FIXED | Kommentar in `deploy-harp.yml:214-229` beschreibt den heutigen Zustand (Ersatztext Option a aus 12-02 eingesetzt), keine veraltete `tolerate-failure`-Referenz mehr. Commit `249d945` |

Alle sieben Befunde sind mit dedizierten Commits behoben; der Commit-Zug `bbbf550..249d945` ist im Git-Log lueckenlos nachvollziehbar (`git log --oneline` bestaetigt).

### Automated Verification Run

| Check | Command | Result | Status |
|---|---|---|---|
| Phase-12-Skript- und Ops-Tests | `uv run pytest tests/test_measurement_scripts.py tests/test_ops_scripts.py tests/test_lockstep_versions.py -q` | 316 passed, 1 warning (unrelated httpx-Deprecation) | PASS |
| Beweislauf stable35 (Option a, vor Flip) | `gh run view 35095805558 --json jobs` | stable35-Job `(stable35, 8.3, true, ubuntu-24.04)` conclusion=success | PASS |
| Regelbetriebslauf stable35 (nach Flip) | `gh run view 35097678552 --json jobs` | stable35-Job `(stable35, 8.3, false, ubuntu-24.04)` conclusion=success | PASS |
| Em-/En-Dash-Gate | `grep` auf U+2014/U+2013 in Runbook, Skripten, deploy-harp.yml, aws_box.sh | keine Treffer | PASS |
| Vokabular-Gate ("Archiv") | `grep -i archiv` in Runbook und Skripten | keine Treffer | PASS |
| Debt-Marker (TBD/FIXME/XXX) | `grep` ueber alle Phase-12-Dateien | keine Treffer | PASS |
| Git-Arbeitsverzeichnis | `git status --short` | keine unversionierten Aenderungen | PASS |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `.planning/ROADMAP.md` | 66, 77 | `Plans: 7/8 plans executed` und `- [ ] 12-02-PLAN.md` noch unabgehakt, obwohl 12-02 am 16.09. vollstaendig ausgefuehrt, committet (`ae59435`, `795744f`, `1fa32f6`) und in `REQUIREMENTS.md`/`STATE.md` korrekt als abgeschlossen gefuehrt ist | WARNING (Doku-Drift, kein funktionaler Mangel) | Rein kosmetisch: die tatsaechliche Erfuellung ist ueber REQUIREMENTS.md, STATE.md, Git-Log und live gepruefte CI-Laeufe zweifelsfrei belegt. Sollte vor Phase-13-Start noch nachgezogen werden, blockiert aber den Phase-12-Abschluss nicht |

Kein Blocker-Anti-Pattern gefunden. Keine TBD/FIXME/XXX-Marker, keine Platzhalter-Reste (`<...>`) in den vollzogenen Dateien, keine Stub-Returns, keine leeren Handler.

### Human Verification Required

Keine offenen Punkte. Der einzige Owner-Checkpoint der Phase (12-02 Task 3, stable35-Vollzug) ist laut SUMMARY bereits innerhalb der Planausfuehrung durchlaufen worden (Owner gab "Variante 1" frei, danach erfolgte der Flip-Commit `795744f`); die Abfolge ist am Commit-Zeitstempel und der Commit-Reihenfolge nachvollziehbar und wird durch den live gepruefte Regelbetriebslauf 35097678552 bestaetigt.

### Gaps Summary

Keine harten Luecken. Einzige Abweichung ist die veraltete Fortschrittszeile/Checkbox in `.planning/ROADMAP.md` (siehe Anti-Patterns), die den tatsaechlichen, code- und CI-belegten Abschluss von Phase 12 nicht spiegelt. Das ist ein Dokumentationsnachtrag, kein Wiedereroeffnungsgrund fuer die Phase.

---

_Verified: 2026-09-16T13:13:29Z_
_Verifier: Claude (gsd-verifier)_
