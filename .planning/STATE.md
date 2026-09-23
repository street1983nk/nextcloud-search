---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Sprachausbau
status: planning
last_updated: "2026-09-23T08:18:23.445Z"
last_activity: 2026-09-23
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-21 after v1.2)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Kein aktiver Milestone. v1.2 ist geliefert und archiviert; als naechstes Marketing-Termine, Wiedervorlagen, dann /gsd:new-milestone.

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-09-23 — Milestone v1.3 started

## Termine und Owner-Checkpoints

- **22.09.2026 09:00: LinkedIn-Post** Findling 1.2.0 + Connector 0.2.1. Text
  freigegeben (Moin + Duzen, ohne "meine"), Bilder in Desktop/release-post/.
  Posten per Playwright, Muster in reference_linkedin_feed_posting.

- **Forum-Post** haengt in der Discourse-Moderation (Konto street1983nk);
  Plan B bei Ablehnung: Antwort im Bestandsthread t/249031.

- **Beim Owner offen:** Store-Token-Rotation (apps.nextcloud.com/account/token);
  Outlook-Entwurf an Denny (admin@infranode.dev/Drafts) senden; InfraNode
  ntfy-401-Entscheid.

## Wiedervorlagen (Stand nach den Owner-Entscheiden vom 21.09.2026 abends)

- Q5 Korpus-Snapshot: ENTSCHIEDEN 21.09. (drittes bewusstes Behalten), bleibt
  im Standard-Tier (~2,85 USD/Monat, einzige laufende Box-Kostenstelle,
  Marke purpose=findling-corpus-keep). Neu vorlegen erst, wenn die naechste
  Anfahrt mehr als ~3 Monate entfernt liegt (dann Archive-Tier rechnen) oder
  beim naechsten Milestone-Close.

- Messanfahrt-Buendel: ENTSCHIEDEN 21.09., kommt als Messphase in den
  NAECHSTEN Milestone; vollstaendig beschrieben als BL-F03 in BACKLOG.md
  (M-01-Zahl, 92c/99d-Wirkung, Bodensatz-Zyklus 2, 6 Fehlschlaege + 44
  Uebersprungene, Kaltstartlatenz; grob 6-10 Boxstunden, Rechenblatt vor
  Start).

- Findling-Pro-Entscheid: VERTAGT auf 03.11.2026 (8 Wochen nach v1.0-Launch,
  Go-Kriterium >=10 Grenzen-Anfragen oder 1 Pilotkunde >250 Nutzer).
  Stand 21.09.: NULL Signale (650 Mails admin-Postfach geprueft, keine
  GitHub-Issues). Fake-Door wird verstaerkt: Issue-Entwurf liegt in
  Desktop/fake-door/connector-enterprise-issue-ENTWURF.md, POSTEN ERST NACH
  OWNER-FREIGABE.

- ISV-Nachfass Fabrice Mous: Owner-Entscheid 21.09. "noch warten";
  Wiedervorlage 25.09.2026, dann Nachfass-Entwurf anbieten.

- Connector Issue #8 (piAreSquare, 21.09., "Added file upload and download
  ability"): Community-Beitrag zur geparkten Connector-Spur, zeitnah sichten.

- L-16-04-Kommentarfix beim naechsten Workflow-Plan (paths-Filter gilt nicht
  fuer Tag-Pushes, zwei Workflow-Kommentare berichtigen).

- Aufraeumbefunde aus der Recherche: fastembed gepinnt aber nicht importiert,
  numpy als indirekte Abhaengigkeit.

- Systemplatten-Skripte Phasen 5-6.1: Repo-Aufnahme erst nach
  Geheimnis-Durchsicht.

## Offene Blocker

- Kill-Kriterium: kuendigt Nextcloud eine Elasticsearch-freie Volltextsuche
  mit OCR an, wird das Projekt neu bewertet. **Geprueft 21.09.2026: NICHT
  ausgeloest** (NC GmbH modernisiert nur den ES-Stack, kein neues Backend,
  kein OCR). Weiter quartalsweise searchvox und
  files_fulltextsearch_tesseract beobachten; Ende September einmalig die
  Conference-Nachberichte.

## Deferred Items

Die drei bei v1.1-Close deferred gefuehrten Debug-Sessions
(kill-resume-di-05-36-red, parity-login-probe-404,
store-install-5-routes-probe) sind am 21.09.2026 formal auf resolved
gesetzt; die Fixes waren laengst gemerged und die Tag-Laeufe auf v1.2.0
bestaetigen sie (7/7 gruen). Keine offenen Deferred Items.

## Session Continuity

Last session: 2026-09-21
Stopped at: Milestone-Abschluss v1.2 (Archivierung, PROJECT-Review,
ROADMAP-Reorganisation, Retrospektive)
Resume file: keine

## Operator Next Steps

- 22.09. 09:00: LinkedIn-Post (siehe Termine)
- Danach: /gsd:new-milestone fuer den naechsten Zyklus
