---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Messbeleg und Ausbau
status: executing
stopped_at: Completed 12-05-PLAN.md
last_updated: "2026-09-14T17:07:03.546Z"
last_activity: 2026-09-14, Plan 12-05 abgeschlossen (98c-sprachfaelle.sh mit Rangsemantik und Abschnitt 3b)
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 8
  completed_plans: 4
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-11)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 12: messwerkzeug-runbook-und-terminentscheid

## Current Position

Phase: 12 (messwerkzeug-runbook-und-terminentscheid), EXECUTING
Plan: 12-01, 12-03, 12-04 und 12-05 abgeschlossen, 4 von 8 Plaenen des Milestones
Status: Ready to execute
Progress: [█████░░░░░] 50%
Last activity: 2026-09-14, Plan 12-05 abgeschlossen (98c-sprachfaelle.sh mit Rangsemantik und Abschnitt 3b)

Hinweis zur Reihenfolge: 12-02 ist fristgebunden (stable35-Vollzug am 16.09.) und
laeuft deshalb nach 12-03.

## Entscheide aus der Ausfuehrung

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

- **Vor der Box-Anfahrt**: neu gerechneter Zeit-/Kostendeckel vom Owner freigegeben (MESS-05, Phase 15); der 26-h-Vorschlag reisst rechnerisch, Empfehlung mindestens 31 h / rund 3,59 USD oder bewusst Teilkorpus
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

Last session: 2026-09-14T17:07:03.530Z
Stopped at: Completed 12-05-PLAN.md
Resume file: None
