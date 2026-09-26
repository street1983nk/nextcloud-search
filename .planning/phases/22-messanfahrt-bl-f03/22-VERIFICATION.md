---
phase: 22-messanfahrt-bl-f03
verified: 2026-09-26T00:00:00Z
status: passed
score: 6/6 must-haves verified (Roadmap-Erfolgskriterien), MESS-07/08/09 vollstaendig
overrides_applied: 0
---

# Phase 22: Messanfahrt BL-F03 Verification Report

**Phase Goal:** Die fuenf offenen Boxzahlen aus v1.2 und die zwei neuen v1.3-Zahlen stehen mit echtem Wert in docs/performance.md, aus EINER bezahlten Anfahrt.
**Verified:** 2026-09-26
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths (Roadmap-Erfolgskriterien 1-6)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Rechenblatt und Kostendeckel liegen VOR dem Boxstart beim Owner und sind freigegeben; Anfahrt bleibt unter dem Deckel, Rohdaten committet | VERIFIED | Commit `9ee4e70` (Freigabezeile, Laufwerte eingefroren) liegt vor der ersten Box-Aktion; README 6.8: Deckel 24 h / 3,76 USD gehalten, 21,68 h / 3,29 USD Reserve; 6.15: Nachanfahrt-Deckel 4 h / 0,50 USD gehalten (0,37 h / 0,0427 USD verbraucht). `git status --porcelain -- docs/measurements` leer laut Summaries, Rohdaten in `rohdaten/` (158 Dateien) und `rohdaten-nachanfahrt/` (27 Dateien) im Baum vorhanden und committet (verifiziert per `ls`) |
| 2 | Die fuenf offenen Zahlen stehen mit Wert und Datum in docs/performance.md (M-01 Zielhardware, 92c/99d-Wirkung, Bodensatz-Zyklus 2, 6 Fehlschlaege/44 uebersprungene einzeln benannt, Kaltstartlatenz ohne Leerbegriff) | VERIFIED | `docs/performance.md` Abschnitt "Die v1.3-Anfahrt vom 26.09.2026" (Zeile 4506ff, alle Nachtraege datiert 26.09.2026): M-01-Tabelle mit 5 Stufen; 92c/99d-Tabelle; Bodensatz A/C1/C2/Zyklus2; Einzelliste aller 6 fehlgeschlagenen und 44 uebersprungenen Dateien nach Kennung/Groesse/Grund; Kaltstartlatenz **2.617 ms, 26 Treffer** (kein Leerbegriff, aus der Nachanfahrt) |
| 3 | Die zwei neuen Zahlen stehen daneben: Indexgroesse bei sechs Sprachfeldern und Wandzeit des Re-Analyse-Umbaus gegen 19 h 20 min Vollreindex | VERIFIED | performance.md: Index de,en 786.508.818 Byte, sechs Felder 1.431.953.684 Byte (Faktor 1,82); Umbau-Wandzeit 581 s gegen 19 h 20 min (rund 120-mal kuerzer). Schaetzung 1-3 h damit als zu vorsichtig belegt (E9 gehalten, E8 verfehlt und dokumentiert) |
| 4 | disjunction_max-Entscheid faellt auf Messbasis: Rangverschiebung gegen Score-Summe auf echten Daten gemessen, Ergebnis umgesetzt oder dokumentiert verworfen | VERIFIED | README 6.10 (MESS-09 nach Regel E10): RBO@10-Median Summe 0,9531 gegen dismax_t00 0,8399 / dismax_t01 0,9633, Schwelle +0,05 von keiner Form erreicht; Entscheid **Summe**, dismax **verworfen**. Unabhaengig geprueft: `grep disjunction_max backend/src/findling/query/rewrite.py` liefert keinen Treffer -- Produktcode tatsaechlich unveraendert, Verwerfung ist real und nicht nur behauptet |
| 5 | Runbook-Disziplin gehalten (Cron-Intervall-Gate als erzwungene Messbedingung, Digest-Wechsel protokolliert), Owner nimmt die Messphase ab | VERIFIED | README Blocktabelle 6.6 traegt `cron-vorher`-Schritt vor der Messreihe; Box-Digest-Kandidat mit sha256 und Laufnummer protokolliert (Zeile 191); Freigabe-/Abnahmevermerk **"Abgenommen: 26.09.2026"** im README (Zeile 364), Owner woertlich "machen wir wie die empfehlung" und "weiter" (zweistufig, Nachanfahrt) |
| 6 | Dieselbe Anfahrt erhebt B1-B3+B5 (BL-F04-Basiszahlen) und B4 (Typwechsel m7g.4xlarge, Skalierungskurve); drei neue Messskripte vorab auf arm64-CI erprobt, rss_sampler.sh unveraendert, NL-Automat-RAM per CI | VERIFIED | performance.md "BL-F04-Basiszahlen": B1 (Kernbelegung je Phase-Tabelle), B2 (OCR-Charge), B3 (Faktor 1,97 zweiter Slot), B4 (Skalierungskurve N=1..16, T=1..8 auf m7g.4xlarge), B5 (Threads/Batch-Matrix, Nachanfahrt ergaenzt RAM 542-877 MB), B6/B7 (Umbau einkernig, NL-Automat 22,99 MB nativ arm64 im CI). `scripts/ops/cpu_sampler.sh`, `proc_anon_sampler.sh`, `ocr_slot_probe.py` existieren neu, `rss_sampler.sh` unveraendert (per `ls` verifiziert) |

**Score:** 6/6 Roadmap-Erfolgskriterien verifiziert

### Requirements Coverage (MESS-07, MESS-08, MESS-09)

| Requirement | Status | Evidence |
|---|---|---|
| MESS-07 | SATISFIED | Alle fuenf Boxzahlen plus Kaltstartlatenz mit Trefferpflicht stehen in performance.md; REQUIREMENTS.md Traceability-Tabelle traegt "Complete (26.09.2026, Kaltstart mit Treffern aus der Nachanfahrt 22-13, Einwort-Begriff; Hybrid-Fall als V-22-01 dokumentiert)" -- unabhaengig bestaetigt ueber 22-13-SUMMARY.md und Commit `ec15950` |
| MESS-08 | SATISFIED | Indexgroesse-Faktor 1,82 und Umbau-Wandzeit 581 s in performance.md und README 6.13 identisch |
| MESS-09 | SATISFIED | Entscheid Summe, dismax verworfen; unabhaengig geprueft ueber leeren Treffer bei `grep disjunction_max rewrite.py` |

Keine Waise: HART-04/05 und REL-03 gehoeren zu Phase 23 und bleiben dort korrekt als Pending gefuehrt.

### D-01 bis D-05 (Context-Entscheide) gegen den Code geprueft

| Entscheid | Prüfung | Ergebnis |
|---|---|---|
| D-01/D-02 (Deckel, harter Stopp) | `grep -n "sudo shutdown" 00-lauf.sh` | Absoluter Timer per `sudo shutdown -h +REST`, mehrfach zurueckgelesen; Deckel in beiden Anfahrten gehalten (README 6.8, 6.15) |
| D-03 (F4-Regel fuer B4) | README Abschnitt 5/6.7 | F4 = 3,955 im CI-Vorablauf, Regel "ab 1,5 wird B4 gefahren" angewandt, B4 tatsaechlich auf m7g.4xlarge gefahren (Rueckgabe 0) |
| D-04 (dismax-Fallback, kein neuer Boxlauf noetig) | siehe MESS-09 oben | Nicht ausgeloest, weil die Messung selbst entschied (Summe); Kriterium 4 "umgesetzt oder dokumentiert verworfen" damit woertlich erfuellt |
| D-05 (Streichreihenfolge B7→B5→B4→B2/B3) | `grep -n "zeit_fuer\|Streichlogik" 00-lauf.sh` | Funktion `zeit_fuer()` implementiert und an allen vier Bloecken (b4, b2, b3, b5) verdrahtet, in dieser Reihenfolge aufgerufen; nie ausgeloest (README 6.6: "Gestrichene Blöcke: keine"), also **wired aber ungenutzt** wie vom Kontext verlangt |

### BL-F04-Kontaminationsschutz (keine Vermischung mit BL-F03)

Unabhaengig geprueft (nicht nur Audit-Text vertraut): `git diff --stat fee701f..HEAD -- backend/src php .github/workflows/deploy-harp.yml` liefert eine leere Ausgabe -- der Produkt-Suchpfad ist ueber die gesamte Phase unveraendert geblieben. Damit sind BL-F04-Mitmessposten nachweislich reine Zusatzmessungen ohne Ruecckwirkung auf die BL-F03-Zahlen.

### CI-Beweis (unabhaengig via `gh run view` geprueft, nicht nur SUMMARY-Text)

| Run-ID | Workflow | Status (per `gh run view`) |
|---|---|---|
| 36249089269 | Python gates | ✓ grün |
| 36249089298 | Integration | ✓ grün |
| 36249089300 | Multi-arch image | ✓ grün |
| 36249089326 | Resilience | ✓ grün |
| 36249089333 | HaRP deploy | ✓ grün |
| 36257801874 | Python gates (Nachanfahrt-Commit) | ✓ grün |

Commits `79b5230`, `db1cfe6`, `e23780c`, `df6226e`, `0de526b`, `ea32513`, `ec15950` alle im Baum vorhanden (`git cat-file -t`), Autor `street1983nk`.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `.planning/ROADMAP.md` | 297, 314 | "TBD" | keine (Info) | Legitimer Platzhalter fuer Phase 23 ("Plans: TBD"), noch nicht geplant -- kein Befund |
| Diverse Skripte | mehrere | `mktemp ...XXXXXX` | keine (Info) | mktemp-Vorlagenmuster, kein Debt-Marker |
| `.planning/phases/22-messanfahrt-bl-f03/22-CONTEXT.md` | 147 | Em-Dash "—" in einer "Deferred Ideas"-Notiz | ⚠️ Warning (gering) | Gilt fuer Planungsartefakt (vom Kontext-Sammeln 25.09.), nicht fuer die in dieser Aufgabe geprueften Kern-Dokumente docs/performance.md, docs/measurements/.../README.md und docs/audits/.../README.md -- dort **keine** Em-Dashes gefunden (grep negativ) |

Keine CRITICAL/HIGH/MEDIUM-Funde in den produzierten Dokumenten. Der projekteigene Audit `docs/audits/2026-09-phase-22/README.md` (0 CRIT/0 HIGH/0 MEDIUM/8 LOW, davon 2 behoben und 6 bewusst offen dokumentiert) wurde gegengeprueft: Katalog-Werte, CI-Gates (ruff/pyright/vulture) und Produktcode-Unveraendertheit sind stichprobenartig unabhaengig bestaetigt.

### Human Verification Required

Keine. Alle Kernaussagen sind ueber Rohdateien, Commits und gruene CI-Laeufe belegbar und wurden unabhaengig (nicht nur ueber SUMMARY-Texte) nachvollzogen.

### Gaps Summary

Keine Gaps. Alle sechs Roadmap-Erfolgskriterien der Phase 22 sind mit echten, datierten Werten in docs/performance.md belegt und stammen nachweislich aus einer (plus einer kleinen freigegebenen Nachanfahrt zur Luecken-Schliessung) bezahlten Box-Anfahrt. Die drei in der Hauptanfahrt aufgetretenen Luecken (Kaltstart mit Trefferpflicht, Bodensatz-Spitze, RAM je onnx-Kombination) sind ueber die vom Owner zweistufig freigegebene Nachanfahrt 22-13 (Commits `0de526b`, `ea32513`, `ec15950`) vollstaendig geschlossen; dies ist in performance.md, im Messbericht (Abschnitt 6.15) und in REQUIREMENTS.md konsistent nachgezogen. Ein bekannter, vorbestehender Produktbefund (V-22-01, Auszugsroute laedt bei Entladeschalter 0 die Gewichte auch fuer Einwort-Suchen) ist korrekt als Backlog-Punkt fuer Phase 23 dokumentiert und wurde bewusst nicht in dieser Phase gefixt (Owner-Entscheid, Produktcode-Aenderung waere ausserhalb des Phasenauftrags).

---

*Verified: 2026-09-26*
*Verifier: Claude (gsd-verifier)*
