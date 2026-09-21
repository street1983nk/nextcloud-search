# Phase 12: Messwerkzeug, Runbook und Terminentscheid - Context

**Gathered:** 2026-09-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Alles, was VOR der einen bezahlten Box-Anfahrt (Phase 15) fertig sein muss, ohne
Box: die Fremdbestands-Vorpruefung misst ueber die Diagnose-Route statt der
gedeckelten OCS-Route, `aws_box.sh` kann ein Volume aus dem Korpus-Snapshot
`snap-03f1d1d9ad9262704` bauen, `docs/runbook-messbox.md` entsteht als
Erstfassung, das Cron-Intervall wird zur durchgesetzten Messbedingung, und der
fristgebundene stable35-Fenster-Entscheid faellt bis zum 16.09.2026.
Requirements: MESS-04, MESS-06, HART-03. Waehrend der Anfahrt in Phase 15 darf
kein Werkzeug mehr geaendert werden muessen; das ist der Massstab dieser Phase.

</domain>

<decisions>
## Implementation Decisions

### stable35-Entscheid (HART-03, Frist 16.09.2026)
- **D-01:** Ist NC 35 am 16.09. final, wird das Versionsfenster GLEICH in v1.2.0
  auf max NC 35 gehoben (kein separates 1.1.x nur fuers Fenster).
- **D-02:** Beweisgrundlage der Hebung: NC-35-final-Check PLUS die bestehende
  deploy-harp-Fremdinstallations-/Upgrade-Strecke gruen gegen stable35. Der
  Release-Status allein reicht nicht.
- **D-03:** Ist NC 35 am 16.09. noch nicht final: Entscheid dokumentieren
  (Fenster bleibt), neuen RE-CHECK-Termin setzen (spaetestens vor der
  Phase-16-Einreichung erneut pruefen); Phase 12 gilt damit als erfuellt.

### Budget-Grundlage der Anfahrt (fuer Phase 15 vorbereitet)
- **D-04:** Der Wirkungsbeleg-Volllauf laeuft gegen den VOLLKORPUS (52.111
  Dokumente), direkt vergleichbar mit v1.0-Baseline und v1.1-Lauf. KEIN
  Teilkorpus-Werkzeug in Phase 12. Konsequenz: der Deckel-Vorschlag fuer
  Phase 15 muss realistisch sein (>= 31 h / ~3,59 USD; letzter Volllauf allein
  26 h 37 min plus ~3,5 h Ruestzeit).
- **D-05:** Ein Deckel-Rechenblatt (Zeitposten, Kostenposten, Empfehlung) wird
  FESTER Runbook-Bestandteil: vor jeder Anfahrt wird der Deckel aus den zuletzt
  gemessenen Posten neu gerechnet; die Owner-Freigabe am Phase-15-Checkpoint
  bekommt damit eine belegte Zahlbasis.
- **D-06:** Zielinstanz bleibt m7g.large (ARM, Vergleichbarkeit mit Baseline und
  v1.1; Hetzner-ARM/CAX weiterhin nicht beschaffbar).

### Cron-Intervall-Regel (MESS-06)
- **D-07:** Das Cron-Intervall wird FESTGENAGELT UND PROTOKOLLIERT: der
  Anfahrt-Ablauf setzt den Systemcron der Messinstanz explizit auf 5 Minuten
  und protokolliert den Ist-Zustand (12 statt 5 Minuten kosteten in v1.1
  ~5,85 h Leerlauf und verfaelschten den Laufzeitvergleich).
- **D-08:** Durchsetzung FAIL-CLOSED IM SKRIPT: ein Vorpruefschritt im
  Anfahrt-/Messskript bricht ab, wenn das Intervall nicht stimmt oder nicht
  protokolliert ist. Eine Runbook-Checkliste allein reicht nicht (menschliche
  Schritte werden vergessen, das war die v1.1-Falle).

### Runbook-Zuschnitt (MESS-04)
- **D-09:** Umfang: Hauptpfad ist der WIEDERAUFBAU AUS DEM SNAPSHOT
  (snap-03f1d1d9ad9262704), der in Phase 15 erstvollzogen wird. Der
  Neuaufbau-von-null steht nur als Verweis auf die bestehenden Messberichte,
  wird nicht ausgearbeitet (ungetesteter Text waere Ballast).
- **D-10:** Form: nummerierte Copy-paste-Kommandobloecke mit erwarteten
  Ausgaben/Pruefpunkten je Schritt. Der Erstvollzug in Phase 15 validiert das
  Runbook woertlich.
- **D-11:** Abbau und Kostenfuehrung sind PFLICHTTEILE des Runbooks:
  Abbau-Checkliste (Snapshot pruefen, destroy, Tag-Sweep ueber Regionen),
  box.env-Kostenpflege und das Deckel-Rechenblatt aus D-05. Der Abbau war
  schon zweimal die Falle (cmd_destroy-Tag-Sweep; destroy loescht box.env).

### Claude's Discretion
- Technischer Zuschnitt der neuen Fremdbestands-Messgroesse ueber die
  Diagnose-Route (`ranked_sides`, arbeitet ohne Vorfilter): Skript-Design,
  ob 98b angepasst oder ersetzt wird, Schwellen-Semantik (Schwelle 64 muss
  pruefbar werden, alte Deckelung war 26).
- Design des neuen `aws_box.sh`-Unterbefehls fuer Volume-aus-Snapshot
  (Namensgebung, Parameter, Sicherheitspruefungen).
- Dokumentationsort und Form des stable35-Entscheids (Vermerk in
  deploy-harp.yml plus Entscheidungsnotiz; Details frei).
- Ob der Cron-Fail-closed-Check als eigenes Skript oder als Schritt in einem
  bestehenden Anfahrtskript lebt.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Recherche-Basis v1.2 (Befunde mit Datei:Zeile-Belegen)
- `.planning/research/SUMMARY.md` — Synthese; Abschnitt "Phase 1: Werkzeug und Runbook" und Disagreement 4 (Box-Budget-Konflikt) sind fuer diese Phase massgeblich
- `.planning/research/ARCHITECTURE.md` — Teil C: was die Messphase aus scripts/ops und docs/measurements wiederverwendet; Befund zur gedeckelten OCS-Route vs Diagnose-Route
- `.planning/research/PITFALLS.md` — Pitfalls 15 (Deckel kleiner als der Lauf), 16 (Cron-Intervall/Vergleichbarkeit), 18 (Werkzeug waehrend des Laufs geaendert)

### Messgeschichte und Werkzeuge
- `docs/measurements/2026-09-vergleichsmessung-m7g/README.md` — der 19-Abschnitte-Bericht der v1.1-Messung; Quelle der Zeit-/Kostenposten fuer das Rechenblatt
- `docs/measurements/2026-09-werkzeugfixe/README.md` — Werkzeugfixe vom 10.09. inkl. Fremdbestands-Vorpruefung (Exit 19/22/23, dreiwertig)
- `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/98b-sprachfaelle.sh` (bzw. Nachfolgefassung in 2026-09-werkzeugfixe/) — die umzustellende Vorpruefung
- `scripts/ops/aws_box.sh` — start/stop/status/snapshot/destroy; hier fehlt Volume-aus-Snapshot
- `scripts/ops/search_load.py` — Lastwerkzeug, seit 10.09. gefixt und geeicht; NICHT mehr anfassen (Vergleichbarkeit)
- `C:/Users/Student/.findling-loadtest/box.env` — Kosten-/Instanzstand ausserhalb des Repos (keine Geheimnisse); AWS-Creds: `C:/Users/Student/.findling-aws.env`

### stable35-Entscheid
- `.github/workflows/deploy-harp.yml` — traegt den RE-CHECK-Vermerk vom 16.09. und die Fremdinstallations-/Upgrade-Strecke (Beweisgrundlage D-02)
- `.planning/milestones/v1.1-phases/11-haertung-und-store-einreichung-v1-1/11-CONTEXT.md` — D-11 (Fenster blieb bewusst stehen, Entscheid v2-a)

### Uebergebene Befunde
- `.planning/milestones/v1.1-phases/*/deferred-items.md` — DI-10-02/DI-11-01 (Sprachfall-Vorpruefung misst Routen-Deckel statt Bestand) mit Belegstellen

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `aws_box.sh`: kann start/stop/status/snapshot/destroy; der neue Unterbefehl haengt sich an die bestehende Struktur (Muster: snapshot als 8. Unterbefehl in 11-12)
- Fremdbestands-Vorpruefung (dreiwertig GRUEN/ROT/NICHT MESSBAR, Exit 19/22/23, fail-closed) aus 2026-09-werkzeugfixe: das Grundmuster bleibt, nur die Messgroesse wechselt auf die Diagnose-Route
- Diagnose-Route mit `ranked_sides` (arbeitet ausdruecklich ohne Vorfilter) als neue Messquelle
- Drei bestehende Messberichte als Quellmaterial fuer die Runbook-Erstfassung

### Established Patterns
- Box-Anfahrten IMMER via aws_box.sh mit Owner-Freigabe + Kostendeckel VOR dem Start
- Messregel seit 10.09.: ein Skript, das waehrend seines eigenen Laufs nachgebessert wird, macht jede Zahl daneben unbelegt; deshalb liegt diese Phase komplett VOR der Anfahrt
- Executor-Muster: sequenziell auf main, Basis-SHA pinnen, blockierende Owner-Checkpoints; Git-Identitaet NIE uebersteuern

### Integration Points
- CI-Pfadfilter: reine docs/scripts-Aenderungen triggern nicht alle Workflows; Pins-Gate und Ruff-Gates gelten auch fuer scripts/
- deploy-harp.yml: stable35-Ast fuer den D-02-Beweis; Vorsicht Uninstall-Gate-Schwellen (Befund A aus 11-11)

</code_context>

<specifics>
## Specific Ideas

- Der Massstab der Phase stammt aus dem Bericht vom 10.09.: waehrend der
  bezahlten Anfahrt darf kein Werkzeug mehr angefasst werden. Alles, was
  Phase 15 braucht, muss hier fertig, getestet und committet sein.
- Das Deckel-Rechenblatt soll die Posten des v1.1-Laufs woertlich uebernehmen
  (38 min Anfahrt, 26 h 37 min Volllauf, ~2 h 50 min Nachmessungen) und daraus
  die Empfehlung >= 31 h / ~3,59 USD ableiten; die Freigabe selbst faellt am
  Phase-15-Checkpoint.

</specifics>

<deferred>
## Deferred Ideas

- Teilkorpus-Werkzeug (bewusst verkleinerter Wirkungsbeleg): abgelehnt fuer
  v1.2 (D-04), bleibt Option fuer spaetere Messkampagnen, falls Kosten je
  wichtiger werden als Vergleichbarkeit.
- Neuaufbau-von-null-Runbook: nur Verweis (D-09); voll ausarbeiten erst, wenn
  der Snapshot je geloescht wird (Wiedervorlage nach v1.2).

</deferred>

---

*Phase: 12-messwerkzeug-runbook-und-terminentscheid*
*Context gathered: 2026-09-14*
