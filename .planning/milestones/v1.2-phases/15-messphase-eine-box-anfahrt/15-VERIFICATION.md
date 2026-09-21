---
phase: 15-messphase-eine-box-anfahrt
verified: 2026-09-21T23:50:00Z
status: passed
score: 5/5 must-haves verified (4 vollstaendig, 1 ueber ein dokumentiertes, vom Owner angenommenes Override)
overrides_applied: 1
overrides:
  - must_have: "Die Sprachfall-Messung laeuft ohne den 52.111er-Fremdbestand und liefert Zahlen ueber der bisherigen Deckelung (Erfolgskriterium 4 der Phase, DI-10-02/DI-11-01)"
    reason: "Auf der einen bezahlten Box war eine Messung ohne den Korpus-Snapshot als Fremdbestand nicht herstellbar, weil der Korpus-Snapshot selbst der Fremdbestand ist. Das Kriterium wurde dem Owner am Checkpoint 15-16 ausdruecklich als NICHT erfuellt vorgelegt, mit Audit-Befund L-09 und der Halbmessung ohne Fremdbestand aus dem CI-Lauf 35471225104 auf amd64 als einziger verfuegbarer Gegenprobe. Der Owner hat die Phase am 21.09.2026 im Wortlaut trotzdem angenommen ('ziel ist das wir den usern das best moegliche liefern') und die Nacherfuellung als Auflage A4 an Phase 16 verschoben (frische ARM-Box ohne Fremdbestand, Rechenblatt und Deckel vor Start)."
    accepted_by: "Owner, im Wortlaut dokumentiert in 15-16-SUMMARY.md und docs/audits/2026-09-phase-15/README.md Abschnitt 6"
    accepted_at: "2026-09-21"
---

# Phase 15: Messphase, eine Box-Anfahrt Verification Report

**Phase Goal:** Die eine bezahlte Anfahrt liefert alle offenen Messbelege des Milestones und vollzieht dabei das Runbook zum ersten Mal
**Verified:** 2026-09-21T23:50:00Z
**Status:** passed
**Re-verification:** No, initial verification

## Vorbemerkung zur Methode

Diese Verifikation misstraut den SUMMARY-Dateien standardmaessig und prueft
gegen die tatsaechlich committeten Artefakte: die Rohdaten der Anfahrt, den
Bericht, das Runbook, `docs/performance.md`, `.planning/REQUIREMENTS.md`,
`.planning/STATE.md`, `.planning/ROADMAP.md` und das Phasenaudit. Zusaetzlich
wurden zwei unabhaengige Proben gefahren, die keine SUMMARY zitiert:

1. Die volle Backend-Testsuite wurde in dieser Sitzung selbst ausgefuehrt
   (nicht aus einer SUMMARY abgeschrieben): **2394 bestanden, 15
   uebersprungen**, exakt die Zahl, die `docs/audits/2026-09-phase-15/README.md`
   und `.planning/STATE.md` fuer den Endstand nennen.
2. Die sha256-Pruefsummen und Byteanzahlen der sechs in `DRIVEN_V12_FASSUNGEN`
   eingefrorenen Werkzeuge wurden in dieser Sitzung selbst aus den Dateien auf
   der Platte berechnet und stimmen byteweise mit den Werten in
   `backend/tests/test_measurement_scripts.py` ueberein.

Die Box selbst existiert nicht mehr (Abbau 21.09.2026, `07-snapshot-und-abbau.txt`);
die Messungen sind nicht wiederholbar. Verifiziert wird deshalb gegen die
committeten Artefakte und nicht gegen einen neuen Boxlauf.

## Goal Achievement

### Observable Truths (Roadmap Success Criteria, Phase 15)

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Der Zeit-/Kostendeckel ist vor dem Start neu gerechnet und vom Owner freigegeben; ohne Freigabe startet die Anfahrt nicht | VERIFIED | `15-08-SUMMARY.md`: Owner-Entscheid im Wortlaut, "Freigegeben, 46 h / 5,40 USD" am 20.09.2026, vorgelegt mit zehn Postenzeilen und Vorgaengerstand. `docs/runbook-messbox.md` Abschnitt 2.1 rechnet dieselben zehn Posten auf 39 h 22 min nach (unabhaengig nachgerechnet in 15-02-SUMMARY.md: 150+90+60+1597+45+90+90+120+60+60 = 2362 min). Tatsaechlicher Verbrauch 25,75 h / 2,9831 USD, `rohdaten/93-kosten-und-verbleib.txt`, committet VOR dem Abbau (Commit df1d11c). Deckel gehalten: ja, mit 20,25 h / 2,42 USD Reserve. |
| 2 | Der DI-10-04-Wirkungsbeleg liegt als Volllauf gegen den Korpus-Snapshot mit Top-up-Fix vor, mit protokolliertem Cron-Intervall und Vergleichbarkeitsbedingungen | VERIFIED | Volllauf 2026-09-20T03:49:32Z bis 23:09:58Z, **19 h 20 min** (als Untergrenze gekennzeichnet), 52.137 Dokumente/Vektoren, kein OOM (`memory.peak` 2.044.096.512 Byte unter der Grenze 2.147.483.648). Cron-Intervall `cron-intervall-ist 300` mit Quelle `aio-cron-container`. Rohdateien vorhanden und inhaltlich konsistent mit dem Bericht: `rohdaten/96-volllauf.csv`, `96b-waechter.txt`, `96-oom-beweis.txt`, `97-cron-vorpruefung-vorher.txt`, `97-cron-vorpruefung-waehrend.txt`. Der Bericht weist die Wirkung der Top-up-Route selbst als NICHT entschieden aus (zwei moegliche Erklaerungen, Instanz und Abbild gleichzeitig gewechselt) und wird von Audit Abschnitt 5.3 gegen den vorab committeten Satz in `00-ablauf.md` (Commit 190d5c7, vor der Box) gegengeprueft: der Satz ist nach dem Lauf nicht umformuliert worden. |
| 3 | Die vier regressiven Laststufen sind untersucht und je Stufe entschieden: behoben, erklaert oder bewusst hingenommen | VERIFIED | Alle vier vormals regressiven Stufen (4, 8, 12, 16) unterschreiten ihre v1.1-Zahl bei gehaltener oder besserer Trefferdichte, Stufe 1 "nicht regressiv". `rohdaten/97-nebenlaeufigkeit.txt` und Bericht Abschnitt 5 sind wortgleich. Unabhaengige Gegenrechnung gegen `cURL error 28` im Nextcloud-Protokoll: null Treffer im Lastfenster, die Ausfallzaehlung des Werkzeugs damit bestaetigt. `search_load.py` laut `git status --porcelain` unveraendert. |
| 4 | Die Sprachfall-Messung laeuft ohne den 52.111er-Fremdbestand und liefert Zahlen ueber der bisherigen Deckelung (DI-10-02/DI-11-01) | **NICHT ERFUELLT, dokumentiertes Owner-Override** (siehe oben) | `rohdaten/05-sprachfaelle.txt`: gefahren wurde MIT dem Fremdbestand, weil der Korpus-Snapshot selbst der Fremdbestand ist; 5 von 10 Faellen "nicht messbar". Zweite Haelfte des Kriteriums (Zahlen ueber der alten Deckelung von 26) haelt: Bestandssonde 33.226 bis 51.965. Dem Owner am Checkpoint 15-16 ausdruecklich als nicht erfuellt vorgelegt (Audit-Befund L-09, `docs/audits/2026-09-phase-15/README.md` Abschnitt 6), Owner hat die Phase trotzdem angenommen, Nacherfuellung als Auflage A4 an Phase 16. |
| 5 | Die Wiederaufwaerm-Kosten der Entladung sind gemessen und ausgewiesen (warm/kalt, mit/ohne Seitencache, A/B ueber den MEM-01-Schalter); die Box ist danach wieder abgebaut | VERIFIED | Vier Auspraegungen gefahren (`95b-wiederaufwaermen-1..4.txt`): Entladung kostet nicht mehr als ein normaler Kaltstart (1.996<2.051 ms kalt, 1.418<1.613 ms warm). MEM-02: Rueckkehr zur Grundlast 377,5 MB (ueber der Schwelle 300 MB), `94b-grundlast-rueckkehr.txt`. Abbau vollzogen mit Rueckleseprobe je Ressourcenart gegen die API (`07-snapshot-und-abbau.txt`); Instanz, Datentraeger und Security Group verifiziert weg, Schluesselpaar nachtraeglich entfernt und verifiziert (`InvalidKeyPair.NotFound`), A-Record nach dem Abbau entfernt. Korpus-Snapshot bleibt gewollt stehen (Owner-Entscheid, zweifach bestaetigt). |

**Score:** 5/5 Erfolgskriterien mit Beleg abgeschlossen; 4 davon vollstaendig erfuellt, 1 (Nr. 4) ist dem Owner offen als nicht erfuellt vorgelegt und von ihm ausdruecklich angenommen worden. Kein Kriterium ist unbelegt oder unentschieden geblieben.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| MESS-05 | 15-01 bis 15-16 (abgehakt in 15-16) | EINE Box-Anfahrt liefert DI-10-04-Wirkungsbeleg, Laststufen-Untersuchung, Sprachfall-Messung, Wiederaufwaerm-Kosten; Deckel vorab freigegeben | SATISFIED, mit dem in Erfolgskriterium 4 benannten Vorbehalt | `.planning/REQUIREMENTS.md` Zeile 70: abgehakt mit Zahl und Rohdatei je Messauftrag; `.planning/STATE.md` Zeile 6 bestaetigt Owner-Abnahme 21.09.2026 |
| MEM-02 | Phase 14 (gebaut), Beleg in 15-04/15-13, abgehakt in 15-16 | Die Entladung gibt beide Speicherhalter frei, Beleg-Messgroesse "Rueckkehr zur Grundlast nach einem Indexlauf" | SATISFIED | `.planning/REQUIREMENTS.md` Zeile 65: `rueckkehr-zur-grundlast-mb = 377,5`, Marke B 1.109,4 MB minus Marke C 731,9 MB, ueber der Schwelle 300 MB; Rohdatei `rohdaten/94b-grundlast-rueckkehr.txt`, unabhaengig gegen `docs/performance.md` Abschnitt "Nachtrag vom 21.09.2026: MEM-02 an seiner Messgroesse" gegengeprueft |

Keine verwaisten Requirements: `.planning/REQUIREMENTS.md` weist Phase 15 genau
MESS-05 zu (Frontmatter aller 16 Plaene) und MEM-02 als Beleg-Requirement der
Phase 14, dessen Zahl in Phase 15 entsteht; beide sind in mindestens einem
Plan (15-01 bis 15-16 fuer MESS-05, 15-04/15-13/15-16 fuer MEM-02) gefuehrt und
im Requirements-Dokument abgehakt. MESS-06 (Cron-Protokoll) ist bewusst Phase
12 zugeordnet und in Phase 15 nur angewendet; das ist im Dokument selbst
begruendet (Zeile 82) und keine Luecke.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `docs/measurements/2026-09-v12-messung/skripte/*.sh`, `*.py` | 18 Werkzeuge der Messreihenfolge (11 uebernommen, 7 neu/vorbestehend) | VERIFIED | Alle 18 auf der Platte gefunden (`ls` in dieser Sitzung), inklusive `92b-wechsel.sh`, `94b-grundlast-rueckkehr.sh`, `95b-wiederaufwaermen.sh`, `99c-filter-sortierung.sh` |
| `docs/measurements/2026-09-v12-messung/rohdaten/*` | Rohdaten aller zehn Messschritte plus Aufbau/Abbau | VERIFIED | 40 Rohdateien vorhanden (`ls` in dieser Sitzung), Namen decken alle im Bericht referenzierten Dateien ab: `03-aufbau.txt`, `04-bestand-vor-der-messung.txt`, `05-sprachfaelle.txt`, `92b-wechsel.txt`, `93-kosten-und-verbleib.txt`, `94b-grundlast-rueckkehr.txt`, `95b-wiederaufwaermen-1..4.txt`, `96-volllauf.csv`, `96b-waechter.txt`, `97-nebenlaeufigkeit.txt`, `99c-filter-sortierung.txt`, `07-snapshot-und-abbau.txt`, `00-FERTIG` |
| `docs/measurements/2026-09-v12-messung/README.md` | Bericht mit Urteil je Erwartung (E1-E14), Verdikten, Kostenzeile | VERIFIED | 572 Zeilen, elf Abschnitte, 14 Urteile (11 gehalten, 3 verfehlt: E10, E12, E13), Kostenzeile mit "Deckel gehalten: ja", Abschnitt 10 mit elf Punkten "was dieser Lauf nicht besser gemacht hat" |
| `docs/runbook-messbox.md` | Ist-Spalte gefuellt, Block 13b, Nachtraege des Erstvollzugs | VERIFIED | 2041 Zeilen, 39 Fundstellen "in Phase 15 erstmals vollzogen", 14 Fundstellen "Block 13b", `drop_caches`-Befehl vorhanden (`echo 3 \| sudo tee /proc/sys/vm/drop_caches`, Zeile 1485) |
| `backend/tests/test_measurement_scripts.py` | `COPIED_TOOLS`, `TOOLS_THE_MEASUREMENT_ORDER_NAMES`, `DRIVEN_V12_FASSUNGEN` | VERIFIED | Alle drei Konstanten vorhanden; `COPIED_TOOLS` 11 Eintraege, `TOOLS_THE_MEASUREMENT_ORDER_NAMES` 18 Eintraege, `DRIVEN_V12_FASSUNGEN` 6 Eintraege mit sha256+Bytezahl, unabhaengig nachgerechnet (siehe Data-Flow Trace) |
| `docs/performance.md` | Fuenf datierte Nachtraege der v1.2-Anfahrt | VERIFIED | Abschnitt "Die v1.2-Anfahrt vom 20. und 21.09.2026" mit Nachtraegen zu DI-10-04, Laststufen, MEM-02, Wiederaufwaerm-Kosten, Filter/Sortierung, alle datiert 21.09.2026 |
| `docs/audits/2026-09-phase-15/README.md` | Gate-Protokoll, ASVS-Durchgang, Befundliste, fuenf Erfolgskriterien mit Beleg | VERIFIED | 473 Zeilen, Gate-Protokoll (2394/15 unabhaengig reproduziert), ASVS V2/V4/V6/V7/V14, Geheimnis-Gegenprobe mit acht Suchfamilien, 13 Befunde (0 CRITICAL, 0 HIGH, 2 MEDIUM, 11 LOW), Kriterientabelle mit Kriterium 4 ausdruecklich als "nicht erfuellt" |
| `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/ROADMAP.md` | MESS-05/MEM-02 abgehakt, Owner-Abnahme vermerkt | VERIFIED (mit einer Anmerkung, siehe Anti-Patterns) | REQUIREMENTS.md: beide `[x]` mit Zahl und Rohdatei; STATE.md Zeile 6: "Phase 15 abgeschlossen und vom Owner abgenommen (21.09.2026)"; ROADMAP.md Zeile 36 und Zeile 220 bestaetigen Abschluss; die Fortschrittstabelle am Dateiende (Zeile 280) ist stehen geblieben auf "15/16, In progress" und wurde bei 15-16 nicht mitgezogen |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `skripte/00-ablauf.md` (Erwartungen E1-E14, committet 19.09.2026) | `README.md` (Urteile) | wortgleiche Erwartung, Urteil danach | VERIFIED | `00-ablauf.md` traegt weiterhin Commit 190d5c7 aus Plan 15-07 und ist in der Anfahrt unberuehrt (bestaetigt in 15-15-SUMMARY.md Self-Check); der Bericht zitiert den Wortlaut ohne Aenderung |
| `docs/runbook-messbox.md` Abschnitt 7.1 (Rueckgabewerte) | `skripte/*.sh` (exit codes) | dieselben Nummern in Runbook und Werkzeug | VERIFIED | Stichprobe an `92b-wechsel.sh`: Rueckgabewerte 36-39 im Runbook UND im Skript vorhanden (per Summary-Beleg 15-06, durch Dateilesung dieser Sitzung nicht widerlegt) |
| `backend/tests/test_measurement_scripts.py::DRIVEN_V12_FASSUNGEN` | die sechs Werkzeugdateien auf der Platte | sha256 + Bytezahl | VERIFIED, unabhaengig nachgerechnet | Diese Sitzung hat sha256 und Bytelaenge aller sechs Dateien selbst berechnet: alle sechs Werte stimmen exakt mit dem Dictionary im Testcode ueberein (z. B. `92b-wechsel.sh`: `8d1f5199...`, 30400 Byte, identisch) |
| `.planning/REQUIREMENTS.md` (MEM-02) | `docs/measurements/2026-09-v12-messung/rohdaten/94b-grundlast-rueckkehr.txt` | Rohdatei als Beleg der Zahl | VERIFIED | REQUIREMENTS.md nennt exakt den Pfad und die Zahl 377,5; die Zahl erscheint identisch im Bericht (Abschnitt 8.2) und in `docs/performance.md` |
| `docs/audits/2026-09-phase-15/README.md` (Kriterium 4) | `15-16-SUMMARY.md` (Owner-Wortlaut) | dieselbe Einordnung "nicht erfuellt" | VERIFIED | Beide Dokumente fuehren dieselbe Bewertung, denselben Befund L-09 und denselben Verweis auf Auflage A4 |

### Data-Flow Trace (Level 4)

Diese Phase hat keine Rendering-Pipeline; die relevante Kette ist Messwerkzeug
zu Rohdatei zu Bericht zu Projektdokument. Zwei unabhaengige Proben wurden in
dieser Sitzung selbst gefahren, nicht aus einer SUMMARY abgeschrieben:

1. **Testsuite:** `uv run pytest -q` im Verzeichnis `backend/` lieferte
   **2394 bestanden, 15 uebersprungen** in 195,19 Sekunden. Das ist exakt die
   Zahl aus `docs/audits/2026-09-phase-15/README.md` und `.planning/STATE.md`.
   Ein isolierter Teillauf (`-k "driven_v12_fassung or byte_identical_to_their_original"`)
   lieferte **19 bestanden**, exakt 11 (COPIED_TOOLS) plus 8 (DRIVEN_V12_FASSUNGEN-Faelle).
2. **Pruefsummen:** sha256 und Byteanzahl der sechs eingefrorenen Werkzeuge
   wurden in dieser Sitzung per Skript aus den Dateien auf der Platte
   berechnet und stimmen mit den im Testcode hartcodierten Werten exakt
   ueberein. Das ist der schaerfste verfuegbare Beleg, dass die Rohdaten
   dieser Anfahrt tatsaechlich gegen die dort behaupteten Werkzeugfassungen
   entstanden sind, und nicht nur eine SUMMARY-Behauptung.

Beide Proben bestaetigen: der Bericht ist kein narrativer Text, sondern
gegen echte, nachpruefbare Artefakte geschrieben.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `.planning/ROADMAP.md` | 280 | Fortschrittstabelle nennt fuer Phase 15 weiterhin "15/16, In progress, -", waehrend Zeile 36 und Zeile 220 desselben Dokuments die Phase als abgeschlossen und abgenommen fuehren | LOW | Reine Dokumentationsinkonsistenz ohne Wirkung auf ein Erfolgskriterium oder ein Requirement; sollte bei Gelegenheit (z. B. beim Planen von Phase 16) nachgezogen werden |
| keine Debt-Marker | - | Kein `TBD`, `FIXME`, `XXX`, `TODO`, `HACK`, `PLACEHOLDER` in den von dieser Phase veraenderten Dateien (`docs/measurements/2026-09-v12-messung/`, `docs/runbook-messbox.md`, `docs/audits/2026-09-phase-15/`, `backend/tests/test_measurement_scripts.py`) | - | Gepruefte Gegenprobe ohne Fund |

Die 13 Auditbefunde der Phase selbst (M-01, M-02, L-01 bis L-11) sind kein
Gap dieser Verifikation: sie sind vom Audit-Bericht selbst offen benannt,
als Auflagen A1 bis A3 an Phase 16 weitergereicht oder in `deferred-items.md`
gefuehrt (L-10, das gesperrte Wort in einer Rohdatei, das nach der Anfahrt
bewusst nicht mehr redigiert wird). Keiner ist ein CRITICAL oder HIGH.

### Human Verification Required

Keine ausstehenden Punkte. Alle Stellen, die menschliches Urteil brauchten,
sind bereits waehrend der Phase am jeweiligen Owner-Checkpoint entschieden und
im Wortlaut dokumentiert worden:

- **15-08** (Deckelfreigabe, 20.09.2026): "Freigegeben, 46 h / 5,40 USD",
  plus drei Antworten (A-Record, Snapshot-Verbleib, verkuerzte Ruhezeit).
- **15-10** (Abbruchtor-Widerspruch, 20.09.2026): "Weiter, Korpus als Beleg."
- **15-13** (Vorschlagswert 900 s, 20.09.2026): "900 s bleibt + Vorbehalt
  (E14-Regel)."
- **15-14** (Snapshot-Verbleib nach dem Lauf, 21.09.2026): "Abbauen,
  Korpus-Snapshot behalten."
- **15-16** (Phasenabnahme, 21.09.2026): Abnahme im Wortlaut, inklusive der
  ausdruecklichen Annahme des nicht erfuellten Erfolgskriteriums 4 mit den
  Auflagen A1 bis A4 an Phase 16.

Diese Verifikation fuegt diesen Entscheidungen keine neue Nachfrage hinzu; sie
prueft nur, dass die Entscheidungen tatsaechlich dokumentiert und in den
Projektartefakten (REQUIREMENTS.md, STATE.md, ROADMAP.md, performance.md,
Audit) konsistent nachvollzogen worden sind, was der Fall ist.

### Gaps Summary

Kein blockierender Gap. Alle fuenf Erfolgskriterien der Phase haben eine
Zahl mit Rohdatei; vier sind erfuellt, das fuenfte (Sprachfall-Messung ohne
Fremdbestand) ist explizit als nicht erfuellt dokumentiert, dem Owner offen
vorgelegt und von ihm mit einer benannten Nacherfuellungs-Auflage (A4) an
Phase 16 angenommen worden. Das entspricht der im Auftrag dieser Verifikation
festgelegten Regel, dass ein so behandeltes Kriterium kein Gap ist.

Die beiden MEDIUM-Befunde des Phasenaudits (M-01: 1,5-Sekunden-Decke reisst
auf der Zielhardware auch ohne Entladung, aber ohne dass ein Abbruch
eintritt; M-02: die Geheimnisregel ist projektweit nirgends als Gate
gefahren und findet 58 Altfunde in fruehen Phasen) sind reale, aber bereits
benannte und an Phase 16 weitergereichte Punkte (Auflagen A2, A3); sie sind
kein unentdeckter Befund dieser Verifikation, sondern von der Phase selbst
sauber dokumentiert.

Einzige neue Beobachtung dieser Verifikation: die Fortschrittstabelle am
Ende von `.planning/ROADMAP.md` wurde bei Plan 15-16 nicht mitgezogen und
zeigt fuer Phase 15 weiterhin "In progress"/"15/16", waehrend der Rest des
Dokuments die Phase korrekt als abgeschlossen fuehrt. Das ist ein LOW-Fund
ohne Wirkung auf ein Erfolgskriterium und wird hier zur Kenntnis gegeben,
nicht als Blocker.

---

*Verified: 2026-09-21T23:50:00Z*
*Verifier: Claude (gsd-verifier)*
