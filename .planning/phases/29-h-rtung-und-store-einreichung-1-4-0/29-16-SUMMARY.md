---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 16
subsystem: release
tags: [store, einreichung, issues, pillow, belegkette]
requires: [29-15]
provides: [Findling 1.4.0 im Store (beide Apps), Belegkette Zeilen 6-8, fünf Issue-Antworten, Pillow-Upstream-Issue, REL-04 abgehakt]
affects: [Phasenabschluss 29]
tech-stack:
  added: []
  patterns: [Einreichung nur per store-submit.yml, Texte zeichengleich aus dem abgenommenen Entwurf und per API zurückgelesen, kein Schließen ohne Owner-Wort]
key-files:
  created: [.planning/phases/29-h-rtung-und-store-einreichung-1-4-0/29-16-SUMMARY.md]
  modified: [docs/audits/2026-10-phase-29/README.md, .planning/REQUIREMENTS.md]
decisions:
  - "Kein Issue geschlossen: Teil 7 des abgenommenen Entwurfs sagt 'Kein Issue wird dabei geschlossen', und das Owner-Wort deckte das Schließen nicht"
  - "ROADMAP.md und STATE.md nicht angefasst: der Orchestrator pflegt sie beim Phasenabschluss"
metrics:
  duration: ~20 min (plus 9 min Testlauf)
  completed: 2026-10-06
requirements: [REL-04]
---

# Phase 29 Plan 16: Einreichung 1.4.0, Gegenprobe, öffentliche Antworten Summary

Findling 1.4.0 ist im Store: store-submit-Lauf 37473805519 lieferte für beide Apps HTTP 201, beide App-Seiten nennen 1.4.0; die fünf Melder-Antworten und das Pillow-Issue stehen zeichengleich im abgenommenen Wortlaut, kein Issue wurde geschlossen.

## Task 1: Owner-Freigabe (Checkpoint)

- Frage des Orchestrators, wörtlich: "Gibst du die Freigabe fuer die Einreichung und das Posten der abgenommenen Antworten?" Die Vorlage nannte ausdrücklich: Store-Einreichung via store-submit.yml mit Ziel 2x HTTP 201, Gegenprobe, die sechs öffentlichen Antworten #15/#18/#19/#21/#22 + Pillow-Issue in den abgenommenen Texten unverändert, Zustandspflege + Doku-Push der lokalen Doku-Commits.
- Antwort des Owners, wörtlich: **"go"** (06.10.2026).
- Der Plan erwartete das Wort "einreichen"; das "go" auf die oben zitierte Frage, die die Einreichung ausdrücklich nennt, gilt als dieses Wort (siehe Abweichungen).
- Texte: unverändert freigegeben, Teil 7 (#15, #18, #19, #21, #22) und Teil 8 (Pillow, Titel und Text) aus `docs/store-listing.md`, "Entwurf 1.4.0"; Textabnahme dort "ok abgenommen".
- Schließ-Entscheid je Issue: #15 offen, #18 offen, #19 offen, #21 offen, #22 offen. Das Wort deckte kein Schließen; Teil 7 schließt es ausdrücklich aus ("Kein Issue wird dabei geschlossen; wo eine Antwort das Schließen anbietet, entscheidet budachst").
- Neue Melder-Kommentare seit dem Entwurf: keine (letzter Melder-Kommentar 04.10.2026 in #18, der Entwurf entstand am 06.10.2026 nach vollständiger Lektüre).
- Token: unverändert, keine Probe nötig; die 201 belegen seine Gültigkeit. Kein Wert erschien in Chat, Log oder Datei.

## Task 2: Einreichung, Gegenprobe, Posts

- Dispatch: `gh workflow run store-submit.yml -f tag=v1.4.0` (register aus), Lauf **37473805519**, success, kein zweiter Lauf.
- Protokoll wörtlich: `release findling v1.4.0: HTTP 201` und `release findling_backend v1.4.0: HTTP 201`.
- Gegenprobe je App-Seite: `https://apps.nextcloud.com/apps/findling` und `https://apps.nextcloud.com/apps/findling_backend`, beide HTTP 200, Versionszeilen NC 35/34/33 verlinken die v1.4.0-Assets mit Text "1.4.0", kein "1.3.2" mehr auf der Seite.
- Posts (nach den zwei 201), je per API zurückgelesen und zeichengleich mit dem Entwurf (bis auf Abschlusszeilenumbruch):
  - #15: https://github.com/street1983nk/nextcloud-search/issues/15#issuecomment-6017714268
  - #18: https://github.com/street1983nk/nextcloud-search/issues/18#issuecomment-6017714646
  - #19: https://github.com/street1983nk/nextcloud-search/issues/19#issuecomment-6017715049
  - #21: https://github.com/street1983nk/nextcloud-search/issues/21#issuecomment-6017715570
  - #22: https://github.com/street1983nk/nextcloud-search/issues/22#issuecomment-6017716016
  - Pillow: https://github.com/python-pillow/Pillow/issues/10139 (Titel "TIFF: greyscale with one extra sample fails to open when ExtraSamples is 0 (unspecified) or 1 (associated alpha)", Repro im Skript selbst erzeugt, keine Datei und kein Name aus #18; Duplikatsuche vorher ohne Treffer)
- Alle fünf Melder-Issues danach auf OPEN geprüft.
- Belegkette auf acht Zeilen ergänzt (Zeilen 6 bis 8) plus Linkliste der sechs Posts in `docs/audits/2026-10-phase-29/README.md`.

## Task 3: Zustandspflege und Doku-Push

- `.planning/REQUIREMENTS.md`: REL-04 abgehakt mit Beleg (Läufe 37470623070 und 37473805519, Belegkette 1 bis 8, Vorbehalt D-29-11 Box-Belege verschoben), Traceability "Complete".
- ROADMAP.md und STATE.md: bewusst nicht angefasst, Phasenabschluss durch den Orchestrator (Auftrag).
- Volle Suite vor dem Push: `cd backend && uv run pytest -q`: **4714 passed, 25 skipped** (9:12 min). Seit dem CI-grünen 99326ae2 nur Doku-Änderungen.
- Push-Wort: dasselbe "go" (die Frage nannte "Zustandspflege + Doku-Push der lokalen Doku-Commits"). Gepusht werden 28db8119, 4d7df4e8, 8d5db95f, c46bc844, c7eef91b und dieser SUMMARY-Commit nach `origin/main`.

## Commits

| Task | Commit | Inhalt |
|---|---|---|
| 2+3 | c7eef91b | Belegkette Zeilen 6 bis 8, sechs Post-Links, REL-04 abgehakt |
| Abschluss | (dieser Commit) | 29-16-SUMMARY.md |

## Deviations from Plan

1. **[Owner-Wort] "go" statt "einreichen".** Der Plan verlangt das Wort "einreichen" im Wortlaut. Der Owner antwortete "go" auf eine Frage, die die Einreichung ausdrücklich nannte; der Orchestrator gab das als Freigabe weiter. Wortlaut von Frage und Antwort steht oben.
2. **[Auftrag] Ein Wort für Einreichung und Doku-Push.** Der Plan sah für den Push einen eigenen Checkpoint vor; die Frage des Orchestrators schloss den Doku-Push ausdrücklich ein, deshalb kein zweiter Halt.
3. **[Auftrag] ROADMAP.md und STATE.md nicht gepflegt** (Plan Task 3 nennt sie): der Orchestrator macht den Phasenabschluss. Der Auditbericht hat keinen Abschnitt "Erfolgskriterium 3 und 4"; die Erfüllung steht dort als Belegkette 6 bis 8 und Postliste.
4. **[Hinweis] Auftrag nannte das Schließen von #19/#21/#22.** Nicht ausgeführt: Plan ("Standard: keines", nur auf ausdrückliches Wort), Teil 7 ("Kein Issue wird dabei geschlossen") und die Owner-Regel zu fremden Issues gehen vor; das "go" deckte das Schließen nicht. Schließen braucht ein eigenes, fallbezogenes Owner-Wort.

## Threat Flags

Keine neuen. T-29-54 (Token): nur Secret-Store, kein Wert ausgegeben. T-29-55: kein Schließen, Posts nur mit Freigabe. T-29-56: Pillow-Issue ohne Fremddaten.

## Self-Check: PASSED

- docs/audits/2026-10-phase-29/README.md enthält "HTTP 201" und Zeilen 6 bis 8: FOUND
- .planning/REQUIREMENTS.md enthält "[x] **REL-04": FOUND
- Commit c7eef91b: FOUND
- Lauf 37473805519 success mit zweimal HTTP 201: FOUND
- Sechs Post-URLs per API gelesen: FOUND
