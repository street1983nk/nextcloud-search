---
plan: 15-16
phase: 15-messphase-eine-box-anfahrt
status: complete
completed: 2026-09-21
subsystem: docs
tags: [performance, audit, requirements, owner-abnahme]
requires:
  - phase: 15-messphase-eine-box-anfahrt
    provides: "15-15: Bericht, Runbook-Nachtraege, Pruefsummen-Waechter"
provides:
  - "docs/performance.md mit den fuenf datierten Nachtraegen der v1.2-Anfahrt"
  - "docs/audits/2026-09-phase-15/README.md: Gate-Protokoll, ASVS, Geheimnis-Gegenprobe, 1 MEDIUM offen + 1 MEDIUM Verfahrensluecke, 11 LOW"
  - "MESS-05 und MEM-02 abgehakt, je mit Zahl und Rohdateiverweis"
  - "Owner-Abnahme der Phase 15 mit Auflagen A1 bis A4 an Phase 16"
affects: [16-haertung-und-store-einreichung]
tech-stack:
  added: []
  patterns: ["Abnahme-Auflagen als benannte Auftraege an die Folgephase, im Wortlaut"]
key-files:
  created: [docs/audits/2026-09-phase-15/README.md]
  modified: [docs/performance.md, .planning/REQUIREMENTS.md, .planning/STATE.md, .planning/ROADMAP.md]
key-decisions:
  - "Owner-Abnahme 21.09.2026 im Wortlaut, mit Nutzerwirkung als Prioritaet"
  - "Erfolgskriterium 4 als nicht erfuellt vorgelegt und nicht umgedeutet; Abnahme trotzdem erteilt, Nacherfuellung als Auflage A4"
  - "Top-up-A/B-Attribution bewusst NICHT beauftragt (keine Nutzerwirkung)"
requirements-completed: [MESS-05, MEM-02]
duration: ~34min (Tasks 1+2) + Checkpoint
---

# 15-16 SUMMARY: performance.md, Audit, zwei Haken, Owner-Abnahme

**Die Zahlen der Anfahrt stehen in docs/performance.md, die Phase hat ihr
Audit, MESS-05 und MEM-02 haengen je an einer Zahl, und der Owner hat die
Phase am 21.09.2026 abgenommen, mit Auflagen an Phase 16.**

## Task Commits

1. **Task 1: docs/performance.md fortschreiben** - `fb2f1ab` (docs)
2. **Task 2: Audit der Phase, Requirements und Zustand** - `6ed748d` (docs)
3. **Task 3: Abnahme der Phase (checkpoint:human-verify)** - dieser Commit

## Task 3: Die Abnahme, im Wortlaut

Vorgelegt wurden die fuenf Erfolgskriterien mit Urteil und Artefakt, die
Kostenzeile (46 h / 5,40 USD Deckel, 25,75 h / 2,98 USD Verbrauch, 20,25 h /
2,42 USD darunter), die Auditbefunde (kein CRITICAL, kein HIGH, M-01 und M-02
als MEDIUM weitergereicht, elf LOW) und die elf offenen Punkte des Berichts.

**Antwort des Owners (21.09.2026), im Wortlaut:**

> "ziel ist das wir den usern das best mögliche liefern"

Auf Rueckfrage hat der Owner dreierlei bestaetigt:

1. **Die Phase 15 ist abgenommen**, mit dem Satz oben als Auflage: die
   nutzerwirksamen offenen Punkte werden Auftraege an Phase 16.
2. **Die kleine Sprachfaelle-Anfahrt wird eingeplant** (frische ARM-Box ohne
   Fremdbestand, Rechenblatt und Deckel zur Freigabe VOR dem Start).
3. **Dependabot-PR #10 wird geschlossen** und tantivy per Ignore-Anweisung
   ausgenommen; der Pin bewegt sich nur noch bewusst, mit Reindex-Plan.

## Die fuenf Erfolgskriterien, je mit einem Wort

| # | Kriterium (Kurzform) | Urteil | Artefakt |
|---|---|---|---|
| 1 | Deckel vor Start gerechnet und freigegeben | erfuellt | 15-08-SUMMARY, Runbook Abschnitt 2 |
| 2 | DI-10-04-Wirkungsbeleg als Volllauf, Cron-Intervall protokolliert | erfuellt | rohdaten/96b-waechter.txt, 96-volllauf.csv, Bericht Abschnitt 2 und 4 |
| 3 | Vier Laststufen untersucht und je entschieden | erfuellt | rohdaten/97-nebenlaeufigkeit.txt, Bericht Abschnitt 5 |
| 4 | Sprachfaelle OHNE Fremdbestand, Zahlen ueber der Deckelung | **nicht erfuellt** | rohdaten/05-sprachfaelle.txt, Audit-Befund L-09 |
| 5 | Wiederaufwaerm-Kosten gemessen, Box abgebaut | erfuellt | rohdaten/95b-*, 07-snapshot-und-abbau.txt |

Kriterium 4 ist dem Owner als nicht erfuellt vorgelegt und nicht umgedeutet
worden: gefahren wurde MIT dem Fremdbestand, weil der Korpus-Snapshot der
Fremdbestand ist; fuenf der zehn Faelle blieben "nicht messbar". Die zweite
Haelfte des Kriteriums haelt (Bestandssonde 33.226 bis 51.965 statt Deckel 26).
Die Abnahme ist trotzdem erteilt; die Nacherfuellung ist Auflage A4.

## Die Auflagen, als benannte Auftraege an Phase 16

- **A1: Nachfolgefassungen 92c und 99d.** Die Phase-B-Pipeline von
  `92b-wechsel.sh` darf occ-Fehler nicht mehr verschlucken, und
  `99c-filter-sortierung.sh` liest das Passwort aus der Passwortdatei statt es
  in der Umgebung zu erwarten. Die gefahrenen Fassungen sind eingefroren
  (DRIVEN_V12_FASSUNGEN); Aenderungen nur als Nachfolgefassung mit neuer Nummer.
- **A2: Die Geheimnisregel als CI-Gate** plus Bereinigung oder ausdrueckliche
  Abnahme der 58 Altfunde aus den Phasen 5 bis 12 (Audit-Befund M-02).
- **A3: M-01-Instrumentierung.** Der innere Aufruf, dem die 1,5-s-Decke gilt,
  wird getrennt von der Gesamtdauer ausgewiesen. Die Instrumentierung entsteht
  auf der Dev-Maschine; die Zahl auf Zielhardware liefert erst die naechste Box.
- **A4: Die kleine Sprachfaelle-Anfahrt planen.** Frische ARM-Box ohne
  Fremdbestand, eigener Testkorpus, Rechenblatt und Deckel zur Owner-Freigabe
  vor dem Start. Ziel: Erfolgskriterium 4 (DI-10-02/DI-11-01) erfuellen.

**Bewusst nicht beauftragt** (Owner-Prioritaet Nutzerwirkung): die
Top-up-A/B-Attribution. Sie braeuchte zwei Vollaeufe mit gleichem Abbild und
aendert nichts an dem, was User erleben. Sie bleibt als Messauftrag fuer eine
etwaige spaetere Anfahrt notiert (Bericht Abschnitt 10, Punkt 2).

## Zur Kenntnis genommene Zahlen

- Bodensatz 628,0 MB nach einem Zyklus (Marke C-A); residenter Stand 731,9 MB
  nach Indexlauf mit entladenem Modell auf einer 4-GB-Box.
- Vorschlagswert 900 s: Owner-Wort vom 20.09. "900 s bleibt + Vorbehalt".
- Q5 bleibt die Wiedervorlage des Korpus-Snapshots (2,79 bis 2,99 USD/Monat),
  Entscheid nach v1.2 faellig.

## Deviations from Plan

None - Task 3 wie geschrieben als blockierender Checkpoint gefahren; die
Antwort liegt im Wortlaut vor, die Auflagen sind Auftraege an Phase 16 und
nicht als erledigt gefuehrt.

## Next Phase Readiness

Phase 15 ist abgeschlossen und abgenommen. Phase 16 (Haertung + Store 1.2.0)
ist NOCH NICHT geplant; sie startet mit vier benannten Auflagen (A1 bis A4),
den weitergereichten Auditbefunden (M-01, M-02, neun offene LOW) und dem
Grundsatz der Abnahme: den Usern das Bestmoegliche liefern.

---
*Phase: 15-messphase-eine-box-anfahrt*
*Completed: 2026-09-21*
