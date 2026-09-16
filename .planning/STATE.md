---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Messbeleg und Ausbau
status: executing
stopped_at: Completed 12-08-PLAN.md
last_updated: "2026-09-14T17:48:00.000Z"
last_activity: 2026-09-14, Plan 12-08 abgeschlossen (Runbook Abschnitte 6 bis 9, MESS-04 und MESS-06 erfuellt)
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 8
  completed_plans: 7
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-11)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 12: messwerkzeug-runbook-und-terminentscheid

## Current Position

Phase: 12 (messwerkzeug-runbook-und-terminentscheid), COMPLETE
Plan: alle 8 Plaene abgeschlossen (12-01 bis 12-08)
Status: Phase complete, naechste Phase 13
Progress: [██████████] 100%
Last activity: 2026-09-16, Plan 12-02 abgeschlossen (stable35-Vollzug, Zweig a,
HART-03 erfuellt)

Phase 12 ist vollstaendig: 12-02 hat den stable35-Entscheid am Stichtag
vollzogen (Zweig a, Beweislauf 35095805558 gruen, deploy-harp-Flag gefallen).

## Entscheide aus der Ausfuehrung

- 12-02: Zweig a greift: v35.0.0 vom 15.09.2026 ist die erste 35er-Marke ohne
  Prerelease-Kennzeichen (prerelease=false UND draft=false, am 16.09. live
  gelesen). Nach D-02 trug der Release-Status allein nicht; der Beweislauf
  35095805558 lief am 16.09. auf dem Baum des Stichtags mit allen vier
  Matrixaesten gruen, ERST DANACH fiel `tolerate-failure` (Owner-Freigabe am
  Checkpoint, Variante 1). Der stable35-Ast von deploy-harp ist ab jetzt
  muss-gruen; ein roter Lauf ist ein Befund und kein Grund, das Flag
  zurueckzudrehen. Beide info.xml blieben unberuehrt (Fenster steht auf
  33 bis 35, D-01).

- 12-08: Das Runbook ist vollstaendig. Abschnitt 6 macht fuenf
  Vergleichbarkeitsgroessen protokollpflichtig (Zeilenstaende 52.111/37/0,
  Cron-Intervall 300 s, m7g.large mit `2147483648`, Zeit seit dem letzten
  Containerstart, Werkzeugstand als Baumhash), Abschnitt 7 gibt jedem der neun
  Messschritte seinen Abbruchpfad und fuehrt alle zwoelf Rueckgabewerte,
  Abschnitt 8 baut in neun Schritten ab (Endmessungen und Historie VOR jedem
  zerstoerenden Schritt, `FINDLING_STATE_BACKUP` vor `destroy`, Tag-Sweep ueber
  `findling-phase5` UND `findling-corpus-keep` danach), Abschnitt 9 fuehrt die
  Kosten ueber `box.env` und schliesst den Kreis zum Deckel-Rechenblatt (D-05).

- 12-08: Waehrend der bezahlten Anfahrt wird kein Werkzeug mehr geaendert. Ein
  Skript, das waehrend seines eigenen Laufs nachgebessert wird, macht jede Zahl
  daneben unbelegt; der Werkzeugstand steht als Baumhash unter den
  protokollpflichtigen Groessen.

- 12-08: MESS-04 und MESS-06 sind erfuellt und abgehakt. Beide sind als
  Werkzeug- und Runbook-Anforderungen formuliert und liegen damit vollstaendig
  in Phase 12; die Anwendung im gefahrenen Messlauf zaehlt in Phase 15 unter
  MESS-05. HART-03 bleibt offen bis zum Vollzug durch 12-02 am 16.09.

- 12-03: `aws_box.sh restore` nimmt die Snapshotkennung aus dem Argument, sonst
  aus `CORPUS_SNAPSHOT_ID` in `box.env`, sonst aus der gepinnten Konstante
  `CORPUS_SNAPSHOT_DEFAULT`. Gesucht wird sie nie.

- 12-03: Ein aus dem Snapshot erzeugtes Volume wird pflichtmaessig auf
  `purpose=findling-phase5` umgetaggt, mit `describe-tags`-Rueckleseprobe und
  Abbruch, solange der geerbte Keep-Tag noch haengt.

- 12-03: `restore` endet beim Anhaengen; das Mounten bleibt ein Runbook-Block.
- 12-03: Annahme A3 ist lesend bestaetigt (Snapshot completed, 100 Prozent,
  60 GB, Tag `purpose=findling-corpus-keep`), Beleg in
  `docs/measurements/2026-09-v12-messung/rohdaten/01-aws-lesende-proben.txt`.

- 12-04: Die Fremdbestandszahl entsteht als
  `searcher.search(query, 1, count=True).count` im Prozess des Containers. Keine
  Route, keine Zahl ueber eine Prozessgrenze, kein Produktionscode angefasst; das
  Zaehl-Orakel aus T-02-93 entsteht gar nicht erst.

- 12-04: Nichtmessbarkeit wird am Rang der eigenen Datei entschieden (in BEIDEN
  Ranglisten fehlend oder schlechter als 64). Bestand und Fensterbelegung stehen
  erklaerend daneben und sind nicht das Urteil.

- 12-04: `NARROW_SCOPE_DIRS` traegt drei Laufverzeichnisse, `98b-sprachfaelle.sh`
  bekommt einen eigenen sha256-Waechter, und `docs/measurements/**` steht in
  beiden Pfadlisten von `python.yml`.

- 12-05: Das Urteil der Sprachfaelle haengt am kleineren der beiden Raenge der
  eigenen Datei gegen die Schwelle 64. Ein Wort statt einer Zahl (`ausserhalb`,
  `keine-kennung`) gilt als ausserhalb und wird nie gegen die Schwelle
  gerechnet.

- 12-05: Die eigenen Datei-Kennungen kommen aus dem Antwortkopf `OC-FileId` des
  Uploads (ohne zweite Abfrage) und reisen ausschliesslich in der Umgebung
  (`DATEI_IDS`), nie in einem Argument.

- 12-07: Der Deckel-Vorschlag fuer Phase 15 wird neu gerechnet statt uebernommen:
  acht Zeitposten, Volllauf mit dem gemessenen Planwert 26 h 37 min und ohne
  Vorwegnahme einer Top-up-Verbesserung, plus 15 Prozent Zuschlag. Ergebnis
  **42 h und 4,90 USD netto**, ausgewiesene Untergrenze 31 h und 3,59 USD. Die
  Freigabe faellt am Phase-15-Checkpoint, nicht im Runbook.

- 12-07: Das Runbook nennt Pfade und Variablennamen, nie Werte. Die
  Snapshotkennung bleibt im Klartext (steht bereits committet, ohne Konto
  nutzlos); Adressen, Instanz- und Volumekennungen stehen als Platzhalter mit
  einem Satz, woher der Wert kommt. Die CIDR-Schreibweise fuer das ganze
  Internet ist deshalb `<ganzes-netz>`.

- 12-07: Abschnittsueberschriften des Runbooks stehen bewusst ohne Umlaute, weil
  Pruefungen und Verweise auf sie zeigen; der Fliesstext traegt echte Umlaute,
  und der Kopf der Datei sagt das. Das Wort "Archiv" kommt in der Datei nicht
  vor (Vokabular-Gate, `docs/` ist oeffentlich).

- 12-06: Das Cron-Intervall ist ab jetzt eine im Skript durchgesetzte
  Messbedingung. `97-cron-vorpruefung.sh` hat zwei Zweige: `vorher` liest den
  Takt aus drei Quellen der Reihe nach und schreibt die Pflichtzeile
  `cron-intervall-ist` (Abbruch 25, wenn keine Quelle antwortet, 26 bei mehr als
  zehn Prozent Abweichung vom Soll 300 s), `waehrend` misst den tatsaechlichen
  Scheibenabstand (Abbruch 27 ohne Zahl, 28 ueber dem Deckel 420 s). Ein reiner
  Konfigurationscheck haette am 10.09.2026 gruen gemeldet, waehrend der Befund
  vorlag (D-07, D-08).

- 12-06: Die Ablesereihe des Wirkungszweiges laeuft mit 120 s und nennt ihr
  Intervall als Pflichtzeile. In v1.1 haben zwei Reihen (194 von 812 gegen 62
  von 325 Lesungen) rund 24 gegen 19 Prozent fuer denselben Sachverhalt
  ergeben; die Zuordnung der Reihen zu den beiden Beobachtern ist Annahme A1 und
  ausdruecklich nicht gesichert.

- 12-06: Der Exit-Code-Katalog des v1.2-Laufverzeichnisses steht bei 28; 12-08
  und Phase 15 setzen bei 29 fort. Der Ablaufplan `00-ablauf.md` schreibt die
  Erwartung E1 bis E7 vor der Anfahrt auf und wird danach nicht mehr angepasst.

- 12-05: `rang-erhoben ja` steht erst nach einem erfolgreichen zweiten
  Sondenlauf. Beide Ursachen (keine Kennung, keine Sonde) enden mit Exit 24
  unter der `tee`-Pipeline. Der Exit-Code-Katalog steht damit bei 24; 12-06
  setzt bei 25 fort.

## Milestone-Reihenfolge v1.2

| Phase | Inhalt | Requirements |
|-------|--------|--------------|
| 12 | Messwerkzeug, Runbook und Terminentscheid (ohne Box) | MESS-04, MESS-06, HART-03 |
| 13 | Filter und Sortierung auf der Ergebnisseite (Backend vor PHP) | FILT-01..05 |
| 14 | Modell-Entladung im Leerlauf (Schalter ab Werk aus) | MEM-01..05 |
| 15 | Messphase, eine Box-Anfahrt | MESS-05 |
| 16 | Haertung und Store-Einreichung v1.2.0 | HART-01, HART-02, REL-02 |

Harte Abhaengigkeiten: 12 vor 15, Backend vor PHP innerhalb 13, 14 vor 15, 16 zuletzt.

## Termine und Owner-Checkpoints

- **16.09.2026**: stable35-Fenster-Entscheid (HART-03, Entscheid v2-a), verankert in Phase 12.
  Beide Zweige sind seit 14.09. fertig ausformuliert in
  `.planning/phases/12-messwerkzeug-runbook-und-terminentscheid/12-STABLE35-ENTSCHEID.md`
  (Plan 12-01); am Stichtag vollzieht Plan 12-02 nur noch nach der dortigen
  siebenschrittigen Checkliste. HART-03 ist erst nach diesem Vollzug erfuellt.

- **Vor der Box-Anfahrt**: neu gerechneter Zeit-/Kostendeckel vom Owner freigegeben (MESS-05, Phase 15); das Rechenblatt steht seit 14.09. in `docs/runbook-messbox.md` Abschnitt 2 und kommt auf **42 h / 4,90 USD netto**, Untergrenze 31 h / rund 3,59 USD. Der 26-h-Vorschlag reisst rechnerisch
- **Vor dem Bau des Zustandsteils**: engineState-Wortwahl `cold` vs sechstes Wort `unloaded` (MEM-05, Phase 14)
- **Vor dem Bau der Entladung**: Vorprueflauf zur tatsaechlichen RSS-Rueckgabe auf Zielhardware (MEM-04, Phase 14); negatives Ergebnis ist ein legitimer Ausgang

## Nach v1.2 (Wiedervorlage)

- Snapshot-Wiedervorlage snap-03f1d1d9ad9262704 (loeschen oder Archive-Tier, rund 2,9 USD/Monat)
- Aufraeumbefunde aus der Recherche: fastembed gepinnt aber nicht importiert, numpy als indirekte Abhaengigkeit
- Systemplatten-Skripte Phasen 5-6.1: Repo-Aufnahme erst nach Geheimnis-Durchsicht

## Offene Blocker

- Kill-Kriterium aktiv: kuendigt Nextcloud auf der Conference im September eine
  Elasticsearch-freie Volltextsuche mit OCR an, wird das Projekt neu bewertet

## Deferred Items

Items acknowledged and deferred at milestone close on 2026-09-11:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| debug | kill-resume-di-05-36-red | investigating | 2026-09-11 |
| debug | parity-login-probe-404 | verifying | 2026-09-11 |
| debug | store-install-5-routes-probe | verifying | 2026-09-11 |

Einordnung: alle drei Debug-Sessions gehoeren zu CI-Befunden, deren Fixe laengst
gemerged und gruen sind (parity-login-probe-404: Fix d604880, Probe fragt
/index.php/apps/findling/; store-install-5-routes-probe: Step auf
oc_ex_apps_routes umgebaut; kill-resume-di-05-36-red: DI-05-36 lief in Phase 10/11
gruen durch). Nur der Session-Status wurde nie auf resolved gesetzt.

## Session Continuity

Last session: 2026-09-14T17:47:20.805Z
Stopped at: Completed 12-08-PLAN.md
Resume file: None
