# Phase 40: Owner-Abnahme 1.6.0

Grundlage: 40-OWNER-VORLAGE.md (Blöcke A1 bis A3, B, C, D1, E1, G1 bis G3, F). Eine Remote-Runde, gestellt vom Koordinator.

STAND: VORBEREITET, OWNER-RUNDE OFFEN. Die Maschinenzeilen unten sind Platzhalter und werden erst mit der Owner-Antwort gesetzt (Plan 40-04 Task 2). Bis dahin startet 40-05 nicht.

## Protokoll der Runde

GO-Zeile: <offen, wird zu "GO: ja" oder "GO: nein">
Zitat-Zeile: <offen, wörtlicher und ungekürzter Owner-Text>
Datum-Zeile: <offen, JJJJ-MM-TT HH:MM Ortszeit>
Kanal-Zeile: <offen, geplant: Remote Control (Claude-App, AskUserQuestion durch den Koordinator)>
Frage-Zeile: <offen, geplant: "Owner-Abnahme Findling 1.6.0: Wie entscheidest du A1-A3, B, C, D1, E1, G1-G3 und das GO (F)? Vorlage: .planning/phases/40-haertung-und-store-einreichung-1-6-0/40-OWNER-VORLAGE.md">

Das GO deckt Tag v1.6.0 und die Einreichung beider Apps.

## Schon entschieden, nur protokolliert

| Datum | Entscheid | Quelle |
|---|---|---|
| 28.10.2026 | 1.6.0 wird verzögert und trägt das Fix-Paket zu Issue #36; die 1.6.1-Frage entfällt | deferred-items.md, 40-06-PLAN.md |
| 29.10.2026 | kein PHP-404 bei kaputten Share-Mounts (E-40-06-03 gestrichen, Gateway bleibt bei 500) | 40-06-SUMMARY.md, Abschnitt Entscheidungen |
| 29.10.2026 | gehäufte gleiche Fehler eskalieren ohne Gutschrift (W-1) | 40-06-SUMMARY.md, Nachtrag nach Verifikation |
| 29.10.2026 | Fix-Antworten in Issues erst nach dem Store-Release | 40-06-SUMMARY.md, Abschnitt Issue #36 |

## Urteil je Punkt

<offen, folgt mit der Owner-Antwort: A1, A2, A3, B, C, D1, E1, G1, G2, G3, F>

## Tag-Kopf

<offen, Plan 40-04 Task 3: Maschinenzeile "Tag-Kopf: <40-stelliger sha>" und "Läufe: ..." erst nach head_green Exit 0>

Kopf bei Vorbereitung: Code-Kopf 23e54187 (head_green Exit 0, 40-06-SUMMARY), Doku 523f2253 (.planning) und 00a63edf (Umlaut-Fix docs/, CI siehe 40-OWNER-VORLAGE.md Block F).
