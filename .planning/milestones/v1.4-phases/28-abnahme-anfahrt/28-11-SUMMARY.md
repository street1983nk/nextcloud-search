---
phase: 28-abnahme-anfahrt
plan: 11
subsystem: messung
status: complete
tags: [abnahme-anfahrt, auswertung, slotkosten, sc4, mess-10]
requires:
  - phase: 28-09
    provides: Matrix komplett, 18 Zellen, Rohdaten aller Boxen, Kosten 34,09 von 59,43 USD
provides:
  - "auswertung.txt: eine Zeile je Zelle (18) aus 12-slotkosten.py mit Urteil getragen ja/nein und Gegenprobe"
  - "README.md des Messordners: Bericht mit Abbild-Digests gegen den c87a0239-Pin, Tabellen je Zelle, Kandidaten OCR_SLOT_COST_BYTES, SC4-Fallliste, Owner-Entscheide vom 05.10.2026"
  - "docs/performance.md: Kapitel Abnahme-Anfahrt v1.4 (Phase 28) mit RAM-Spitze und Durchsatz je Box und Profil, Verweis auf den Messordner (SC2)"
affects: [28-12, 29]
tech-stack:
  added: []
  patterns:
    - "Hauptprozess-Anteil der Rechnung = Rechnung minus Slots x 235; Vergleich mit dem Hauptprozess-Maximum trennt Slot- von Hauptprozessposten"
key-files:
  created:
    - docs/measurements/2026-10-abnahme-anfahrt/auswertung.txt
    - docs/measurements/2026-10-abnahme-anfahrt/README.md
  modified:
    - docs/performance.md
decisions:
  - "OCR_SLOT_COST_BYTES wird 250 MiB = 262.144.000 Byte (Owner 05.10.2026); FP32_EXTRA_BYTES bleibt 367 MiB; Umsetzung 28-12"
  - "SC4-Fälle Zellen 11, 16, 17, 20, 21: Formel nachziehen, keine Stufe gestrichen (Owner 05.10.2026)"
  - "S-voll (+19,9 %): Formel nachziehen per Vollindex-Term, 28-12 legt den Umfang vor dem Bau vor (Owner 05.10.2026)"
  - "Store-Zahl C4: kein Fall, C1 743,9 MB im Band, RESIDENT_FIGURE 730.2 bleibt (Owner 05.10.2026)"
metrics:
  duration: "05.10.2026, rund 1,5 h Task 1 plus rund 0,5 h Task 2 und 3, keine Boxzeit"
  completed: 2026-10-05
requirements: [MESS-10]
---

# Phase 28 Plan 11: Auswertung und Bericht der Abnahme-Anfahrt Summary

**Status: complete.** Alle 18 Zellen sind mit `12-slotkosten.py` ausgewertet, die SC4-Fälle hat der Owner am 05.10.2026 entschieden (Slotwert 250 MiB, alle sechs Fälle "Formel nachziehen", kein Store-Fall), und docs/performance.md trägt das Kapitel "Abnahme-Anfahrt v1.4 (Phase 28)" mit Verweis auf die Rohdaten.

Ergebnis der Auswertung: 12 getragen, 6 nicht getragen (S-voll +19,9 %, dazu 11, 16, 17, 20, 21 auf x86). Alle 11 Proben `fits`, alle von der Messung bestätigt. C1 743,9 MB liegt im Band. Der Hauptprozess wächst mit der Slotzahl, die Slots selbst liegen bei mehreren Slots unter 235 MiB.

## Tasks

### Task 1: Auswertung aller Zellen und Bericht (Commit 91357168, SUMMARY-Zwischenstand 18e19b6c)

- `auswertung.txt`: Kopf mit Felddefinitionen, je Zelle eine Zeile (anon, peak, Rechnung, Grenze, Abweichung, getragen, VmHWM-Paar, RssAnon-Paar, anon je Slot, Hauptprozess, r, OCR-Fenster, Seiten/s, Dateien/h, Laufzeiten, Leerlauf, Wächter, OOM, Probe, erzwungen, Reserve-Ersatzmaß, Gegenprobe), Kandidatenblock, Hauptprozess-Block, SC4-Liste, C1, darunter die Rohausgaben von `12-slotkosten.py slots`, `rechnung --gemessen-bytes` und `fp32`.
- `README.md`: 14 Abschnitte im Hausstil der v1.3-Messung.
- Gates: `test_public_artifacts.py` 55 grün; die drei Tests am Messordner 594 grün.

### Task 2: Owner-Entscheide SC4 und Store-Zahl (Commit 9a4dcc52)

Entschieden am 05.10.2026 per Auswahlfrage in der Session. Signal wörtlich:

> je-fall: 11=nachziehen, 16=nachziehen, 17=nachziehen, 20=nachziehen, 21=nachziehen, S-voll=nachziehen (Vollindex-Term, Umfang legt 28-12 vor), wert=250 MiB, store=kein Fall

- `OCR_SLOT_COST_BYTES`: 250 MiB = 262.144.000 Byte (entspricht Hauptprozess-Zuschlag +15 MiB je Slot, trägt alle 17 Teilkorpus-Zellen inklusive fp32-Zelle 11, Slotzahlen auf 8-GiB-Boxen unverändert). `FP32_EXTRA_BYTES` 367 MiB bleibt.
- Zellen 11, 16, 17, 20, 21: Formel nachziehen, Umsetzung 28-12.
- S-voll: Formel nachziehen, 28-12 legt einen Vollindex-Term vor (Zuschlag 133,8 MiB), Umfang vor dem Bau beim Owner.
- Store-Zahl (C4): kein Fall, `RESIDENT_FIGURE` "730.2" bleibt.
- Ausformuliert in README Abschnitt 14 "Owner-Entscheide".

### Task 3: Kapitel in docs/performance.md (Commit f1cbdc03)

- Neues Kapitel "Abnahme-Anfahrt v1.4 (Phase 28)" vor "Reproduzieren": Maschinen und Quelle mit Link auf `docs/measurements/2026-10-abnahme-anfahrt/`, Tabelle je Box und Profil (15 Teilkorpus-Zellen: anon, Rechnung, getragen, Dateien/h, OCR-Seiten/s), fp32 mit beiden Datenpunkten, Sparsam-voll und C1 gegen 730,2 MB mit Toleranzurteil, Kosten je Slot gegen 235 MiB, Gegenprobe der Probe, Owner-Entscheide mit Datum.
- Inhaltsübersicht: die Datei hat keine, nichts ergänzt. Keine Store-Texte geändert.
- Gates: `test_public_artifacts.py` und `test_store_metadata.py` 131 grün; keine Em- oder En-Dashes in beiden Dateien; keine Box-Adressen im neuen Kapitel.

## Abweichungen vom Plan

1. **18 statt 21 Zellen:** Zellen 3, 4, 10 vom Owner gestrichen (Quick 261003-d3y), Grund im README Abschnitt 1.
2. **Abbild-Stand:** drei Stände statt c87a0239 durchgehend (c87a0239 für 1 und 2, f73566c1 für 5 und 6, 18602c48 für 7 bis 21), Digests, Baumhashes und Änderungsumfang im README Abschnitt 2.
3. **[Befund] S-voll nicht getragen:** anon 1.788,9 gegen Grenze 1.641,8 MiB (+19,9 %); sechster SC4-Fall, vom Owner entschieden.
4. **[Befund] Maß des Kandidaten:** Die Plan-Regel nennt das VmHWM-Paar "dasselbe Maß wie B2", B2 ist aber ein RssAnon-Paar. Vorgelegt wurden 448, 391 und 250 MiB; der Owner wählte 250 MiB.
5. **Reserve am Tiefpunkt nicht gesampelt:** für die Gegenprobe ein Ersatzmaß (Box-RAM minus 1 GiB minus anon), im README offen benannt.
6. **Leerlaufanteil über 10 % in 8 Zellen:** nur im Anlauf (cron-gebunden), als "im Anlauf zulaufgebunden" benannt.
7. **Kosten:** Schlusstabelle nach Runbook 2.6 gehört zu 28-10.
8. **Helfer:** Ableitungen über `12-slotkosten.py` hinaus liefen über ein temporäres, nicht committetes Hilfsskript; Definitionen im Kopf von `auswertung.txt`.
9. **README in Task 2 statt Task 3 ausformuliert:** Der Abschnitt "Owner-Entscheide" ist mit dem Entscheid-Commit vollständig ausformuliert; Task 3 änderte nur docs/performance.md.

## Known Stubs

Keine.

## Self-Check: PASSED

- docs/measurements/2026-10-abnahme-anfahrt/auswertung.txt: FOUND
- docs/measurements/2026-10-abnahme-anfahrt/README.md: FOUND (Abschnitt 14 gefüllt)
- docs/performance.md: FOUND (Kapitel mit Verweis "2026-10-abnahme-anfahrt")
- Commits 91357168, 18e19b6c, 9a4dcc52, f1cbdc03: FOUND
