# Phase 40: Owner-Abnahme 1.6.0

Grundlage: 40-OWNER-VORLAGE.md (Commit 62334434; Blöcke A1 bis A3, B, C, D1, E1/E2, G1 bis G3, F). Eine Runde, gestellt vom Koordinator als gebündelte AskUserQuestion-Runde mit einer Rückfrage zum Store-Text.

GO: ja
Zitat: A1, A2, A3, G2: "Alle wie vorgeschlagen (Empfohlen)"; B: "Zeig sie mir", nach Vorlage beider Beschreibungen (de, Hinweis auf en/fr) samt Version, Doku-Links und Discussion-Link 249775: "Ok"; C: übernehmen wie in der Vorlage (sinngemäß, laut Koordinator); D1, E1/E2, G1: "Alle wie empfohlen"; G3: "so lassen" (vorher entschieden); F: "GO"
Datum: 2026-10-29 11:48
Kanal: Claude-Code-Sitzung des Koordinators, gebündelte AskUserQuestion-Runde plus Rückfrage zum Store-Text (Uhrzeit = Übermittlung an den Ausführenden, die Owner-Antwort lag davor am selben Tag)
Frage: Owner-Abnahme Findling 1.6.0: Wie entscheidest du A1-A3, B, C, D1, E1, G1-G3 und das GO (F)? Vorlage: .planning/phases/40-haertung-und-store-einreichung-1-6-0/40-OWNER-VORLAGE.md

Das GO deckt Tag v1.6.0 und die Einreichung beider Apps.

## Urteil je Punkt

| Punkt | Urteil |
|---|---|
| A1 Mehrfachzählungs-Satz | (a) angenommen |
| A2 Satz bei null ausgelassen | (a) angenommen |
| A3 Hinweis nach Regeländerung | (a) angenommen |
| B Store-Text 1.6.0 | (a) so einreichen, Beschreibungen wie 1.5.1, CHANGELOG [1.6.0] unverändert |
| C Release-Notiz v1.6.0 | (a) übernommen, sechs Punkte |
| D1 F-40-06 | (a) accept für 1.6.0, Lösung in v1.7 |
| E1/E2 historische Umlaute | (a) eigener Doku-Commit nach dem Release |
| G1 Kandidat F | (a) bestätigt |
| G2 Anzeige-Satz D | (a) bestätigt, Unschärfe bei Häufungs-Eskalation auf der v1.7-Merkliste |
| G3 #36-Kommentar 6492666744 | (a) so lassen |
| F GO | (a) GO für Tag und Einreichung |

Keine Abweichung, also keine Änderung an Katalogen, info.xml oder Notiz vor dem Tag. Umgesetzt in Task 3: Abschnitt "# Entwurf v1.6.0 (Gesamttext), abgenommen am 29.10.2026" in docs/store-listing.md mit Gate `scan_full_text_1_6_0` (Commit 91a0603f).

## Schon entschieden, nur protokolliert

| Datum | Entscheid | Quelle |
|---|---|---|
| 28.10.2026 | 1.6.0 wird verzögert und trägt das Fix-Paket zu Issue #36; die 1.6.1-Frage entfällt | deferred-items.md, 40-06-PLAN.md |
| 29.10.2026 | kein PHP-404 bei kaputten Share-Mounts (E-40-06-03 gestrichen, Gateway bleibt bei 500) | 40-06-SUMMARY.md, Abschnitt Entscheidungen |
| 29.10.2026 | gehäufte gleiche Fehler eskalieren ohne Gutschrift (W-1) | 40-06-SUMMARY.md, Nachtrag nach Verifikation |
| 29.10.2026 | Fix-Antworten in Issues erst nach dem Store-Release | 40-06-SUMMARY.md, Abschnitt Issue #36 |

## Tag-Kopf

Tag-Kopf: 91a0603f2b69213037c0d8ac2101121f9ba767b2
Läufe: 40860811496 Python gates, 40860811483 HaRP deploy, 40860811469 Integration, 40860811447 Resilience, 40860811482 Multi-arch image, 40860811457 Security scans, 40860811488 OpenSSF Scorecard (alle success, `scripts/ci/head_green.sh` Exit 0 am 29.10.2026); PHP and store metadata gates per Zitat 40834773386 auf 4ed0f846, `git diff --stat 4ed0f846 91a0603f -- php backend/appinfo .github/workflows/php.yml .github/workflows/release.yml scripts/dev/validate_info_xml.sh` leer.

Der Tag-Kopf ist der letzte Commit außerhalb .planning (`git log -1 --format=%H -- . ':!.planning'`).
