---
phase: 35-stretch-aehnliche-dokumente-und-spikes
verified: 2026-10-20T00:00:00Z
status: passed
score: 3/3 roadmap-Kriterien und 11/11 Owner-Entscheide verifiziert
overrides_applied: 0
re_verification: false
gaps: []
human_verification: []
---

# Phase 35: Verifikationsbericht

**Ziel:** Ähnliche Dokumente zu einem Treffer abrufbar; belastbare Entscheidungsvorlagen zu granite und #25-Dedup für v1.6; Phase streichbar ohne Release-Risiko.
**Stand:** Endstand 6cd225ec, Re-Verifikation: nein (erste Verifikation).
**Methode:** Code, Messordner und Abnahmeprotokolle direkt gelesen; SUMMARY-Behauptungen nicht als Beleg gewertet.

## Observable Truths

| # | Wahrheit | Status | Beleg |
|---|---|---|---|
| 1 | Link "Ähnliche Dokumente" je Treffer; Vektor-Nachbarn aus bestehendem Index; PHP-Recheck; keine Index-/Schema-/Modelländerung | VERIFIED | siehe unten |
| 2 | Messbericht granite gegen e5 mit Empfehlung für v1.6; ausgeliefertes Modell bleibt e5 | VERIFIED | siehe unten |
| 3 | Designnotiz #25-Dedup als Entscheidungsvorlage | VERIFIED | siehe unten |

### 1. STR-01 Ähnliche Dokumente

- `php/templates/search.php`: `a.findling-hit__similar` (Z. 541) als eigenes Element nach dem Zeilen-Link, aria-Label mit Titel, GET-Link (`similarUrl`); Kopf "Similar to: %s" (Z. 239), Rückweg (Z. 251), Leer- und Nicht-verfügbar-Zustand (Z. 592-598). Entspricht D-35-01..04.
- Recheck in PHP: `SearchService::similar` (Z. 551-653): Quelle zuerst über `readableFile` (Z. 581) VOR dem Containeraufruf (Z. 589); jeder Nachbar erneut über `readableFile` (Z. 641); Deckel `SIMILAR_MAX_HITS = 10`, `MAX_RECHECKS`, Deadline; Quelle wird ein zweites Mal verworfen.
- Container: `backend/src/findling/api/similar.py`: Identität nur aus AppAPI-Header, `extra="forbid"`, Vorfilter auf der Quelle vor dem Lesen der Vektoren, nur IDs, keine Distanz; Route nicht in `info.xml` (Test vorhanden). Kein Modelllauf.
- Kein Schema-/Index-/Modellwechsel: Diff `5a66ba1e..HEAD` in `store/vectors.py` ist nur eine lesende Abfrage `vectors_of` (+23 Zeilen, kein DDL); `backend/Dockerfile` ohne Diff; `EMBEDDING_MODEL` unverändert e5.
- `SIMILAR_CEILING = 54.5` (`config.py:977`) deckt sich mit dem Messbericht `2026-10-aehnlich-distanzen` Abschnitt 10.2 (alle 70 Fassungspaare darunter, alle 3660 Unbeteiligten darüber); Regel vor Rohdaten (Audit B6).
- Kataloge: "Similar documents to %s" in allen 16 Dateien unter `php/l10n/` (8 json + 8 js) vorhanden.
- Gegenproben (selbst ausgeführt): `tests/test_similar_endpoint.py` 17 passed, `tests/test_phase35_audit.py` + `tests/test_php_acl_boundary.py` 16 passed. Volle Suite und 7 CI-Läufe laut Auftrag grün (nicht neu ausgeführt).
- Rechtegrenze live belegt im Audit (S1-S4, unabhängiges SQL-Orakel): fremde byte-gleiche Kopie erscheint nie; fremd, gelöscht, unbekannt byte-identisch (2204 Bytes); kein 500 bei Fremdeingaben.
- Owner-Abnahme UI: Wortlaut 19.10. (`35-WORTLAUT.md` Abschnitt E, "Abgenommen (alle Empfehlungen)"), Playwright-Runde 20.10. (`35-08-ABNAHME.md`, 8 Proben grün, "Abgenommen"). D-35-08 eingehalten.

### 2. STR-02 granite-Messbericht

- `docs/measurements/2026-10-granite-vergleich/README.md`: Regel (a)-(d) in Abschnitt 1 vor der Messung, Owner-Abnahme Abschnitt 7 (19.10.), Audit B7 bestätigt Regelabschnitt unverändert seit Regel-Commit.
- Alle geforderten Dimensionen vorhanden: deutscher Korpus 120 Fälle (D-35-10, e5 im selben Lauf neu), Qualität je Sprache plus Paarvergleich (Abschn. 9, 10), Latenz amd64 und arm64 (12), RAM arm64 (13), eigener int8-Build byte-reproduzierbar (11), Image-Zuwachs 71,1 MB gzip (14), Neu-Einbettung 5 h 14 min (15), Kosten 0,0362 USD gegen Deckel 0,60 USD (16), Abbau gegengeprüft.
- Pflichtpunkte vom 10.10. in Abschnitt 19 einzeln bewertet; Verdikt (Abschn. 18-20): "Wechsel nur mit Bedingung", (a) verfehlt (p = 0,0944), (b)-(d) erfüllt; Empfehlung klar und regelkonform formuliert, keine stille Wahl.
- Ausgeliefertes Modell bleibt e5-small (Dockerfile ohne Diff, Marke unverändert).
- m7g-Miete: wörtliche Freigabe in `rohdaten/02-rechenblatt-freigabe.txt` vorhanden (D-35-05).

### 3. STR-03 Dedup-Notiz

- `35-DEDUP-NOTIZ.md`: Sachstand, Nextcloud-Fakten, drei Wege (A fileid-Mapping, B per-User-Crawl mit Hash-Wiederverwendung, C nur Zählung), Vergleich, Empfehlung (B Standard, A nur Opt-in mit Warnsatz, C sofort), Owner-Entscheidungen D1-D4 mit Optionen, Annahmen A5-A7, ACL-Folgen behandelt.
- D-35-09 eingehalten: nur interne Vorlage, kein Issue-Kommentar, kein Bau. Sperrlistenprüfung gegen Issue-Namen: 0 Treffer (Audit S8, mit Positivkontrolle).

## Requirements Coverage

| ID | Plan-Quelle | Status | Evidenz |
|---|---|---|---|
| STR-01 | 35-01, 35-05..08 | SATISFIED | Wahrheit 1 |
| STR-02 | 35-03, 35-04/04B, 35-09..11 | SATISFIED | Wahrheit 2 |
| STR-03 | 35-02 | SATISFIED | Wahrheit 3 |

REQUIREMENTS.md: STR-01..03 auf `[x]` und "Complete" (Z. 51-53, 106-108). Keine verwaisten Requirements für Phase 35.

## Owner-Entscheide D-35-01..11

Alle eingehalten (01-04 UI per Template-Beleg und Playwright, 05/11 Messaufbau und Rohdaten, 06/07/10 Korpus und Regel vor Messung, 08 Wortlaut-Plan, 09 Notiz ohne Kommentar).

## Audit

`35-AUDIT.md`: status fixed, 0 CRITICAL/HIGH/MEDIUM, 6 LOW behandelt (4 gefixt, 2 begründet akzeptiert, T-35-15 akzeptiert). Offene Punkte nur für Phase 36 benannt (L-35-06 httpx-INFO-Level).

## Anti-Patterns

| Datei | Befund | Schwere |
|---|---|---|
| `docs/measurements/2026-10-granite-vergleich/README.md` Z. 20-23 | Einleitungssatz "Bis Plan 35-11 trägt er nur Regel und Methode; die Abschnitte ab 8 entstehen in 35-09 bis 35-11" ist überholt (Ergebnisse stehen im Bericht) | Info, kein Blocker |

Keine TBD/FIXME/XXX-Marker geprüft in den gelesenen Phase-Dateien (similar.py, SearchService-Ausschnitt). Keine Stubs, Daten fließen (Audit S2/P2 mit echtem Bestand 1031 Chunks).

## Human Verification

Keine offen: alle vier Owner-Checkpoints (Wortlaut, Messregel, Playwright, m7g-Miete) sind mit Datum und Wortlaut dokumentiert.

## Fazit

Phasenziel erreicht. Keine Lücken, keine Blocker. Die Phase bleibt streichbar: Produktdiff ist die Ähnlich-Ansicht ohne Schema-, Index- oder Modelländerung.

_Verifiziert: 2026-10-20 (gsd-verifier)_
