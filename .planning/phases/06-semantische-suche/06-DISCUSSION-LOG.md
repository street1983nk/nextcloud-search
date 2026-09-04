# Phase 6: Semantische Suche - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-04
**Phase:** 06-semantische-suche
**Areas discussed:** Embedding-Umfang und Laufzeit, Vektorspeicher und Ausweichpfad, Ranking und Treffer-Anzeige, Embedding-Zeitpunkt und Ehrlichkeit

---

## Embedding-Umfang und Laufzeit

| Option | Description | Selected |
|--------|-------------|----------|
| Erste 1.024 Token (Empfohlen) | ~2 Chunks je Dokument, Erstindex-Zuwachs 7-24 h statt 54-180 h, als Einstellung aufdrehbar | ✓ |
| Alles einbetten | ~968.000 Chunks, 54-180 h Zuwachs auf der 4-GB-ARM-Box | |
| Erste 512 Token | 1 Chunk, oft nur Briefkopf und Betreff | |
| Nach Messung B entscheiden | Owner-Checkpoint waehrend der Ausfuehrung | |

**User's choice:** Erste 1.024 Token
**Notes:** Preis akzeptiert: ehrliche Store-Aussage zur Abdeckung des Dokumentanfangs.

| Option | Description | Selected |
|--------|-------------|----------|
| e5-small, potion nur Notfall (Empfohlen) | Deutsch-Qualitaet belegt, int8-Verlust praktisch null | ✓ (nach Freitext) |
| Beide umschaltbar bauen | zwei Testpfade, zwei Schemata, Reindex bei Wechsel | |
| Gleich potion nehmen | rechenfrei, Qualitaetsluecke unbelegt, SEM-01-Aenderung | |

**User's choice:** Freitext: "ich moechte beste qualitaet, fr und english sollen auch beruecksichtigt werden" — nach Gegenueberstellung e5-small gegen e5-base (+0,9 nDCG gegen 2x Speicher / 2-3x Laufzeit) bestaetigt: e5-small bleibt, Testset dreisprachig DE/EN/FR, potion nur dokumentierter Notausgang.
**Notes:** Mehrsprachigkeit DE/EN/FR ist damit ausdrueckliche Anforderung an das Welle-0-Testset.

---

## Vektorspeicher und Ausweichpfad

| Option | Description | Selected |
|--------|-------------|----------|
| int8 in sqlite-vec (Empfohlen) | exakt, eine Datei, ein Backup; bei ~100k Chunks 38 MB je Scan | ✓ |
| Bit-Vektoren grob + int8 fein | Faktor 8-20, aber beide Fassungen speichern | |
| usearch (HNSW) | logarithmisch, aber zweiter Persistenzpfad + Crash-Sicherheit selbst bauen | |

**User's choice:** int8 brute force in sqlite-vec v0.1.9 (exakt gepinnt)

| Option | Description | Selected |
|--------|-------------|----------|
| Schnitt + einbacken (Empfohlen) | Abstraktionsschnitt (3 Operationen) + .so im Abbild festhalten (Muster APPSTORE_SHA) | ✓ |
| Nur exakt pinnen | billig, Ausweichpfad bleibt ein Absatz Doku | |
| Gleich usearch nehmen | alle usearch-Kosten fuer ein Nicht-Problem bei 100k Chunks | |

**User's choice:** Schnitt + einbacken
**Notes:** Hintergrund: sqlite-vec seit 18.05.2026 ohne Commit, 204 offene Vorgaenge.

---

## Ranking und Treffer-Anzeige

| Option | Description | Selected |
|--------|-------------|----------|
| Maximum (Empfohlen) | bester Chunk bestimmt Dokumentrang, laengenneutral | ✓ |
| Summe der besten n | bevorzugt lange Dokumente | |
| Anzahl in den Top-k | robust, grob | |

**User's choice:** Maximum

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, so uebernehmen (Empfohlen) | k=60, Fenster 100, Gewichte 1:1, semantisch senkbar, stille Stellschrauben | ✓ |
| Semantik gedaempft starten | Gewicht < 1,0 als Vorgabe | |

**User's choice:** RRF-Standardwerte uebernehmen
**Notes:** Vorbehalt bleibt: Fenstertiefe gegen Vorfilter-Selektivitaet in der Phase pruefen.

| Option | Description | Selected |
|--------|-------------|----------|
| Bester Chunk als Ausschnitt (Empfohlen) | char_start/char_end speichern, Schnitt aus body_de nach Recheck | ✓ |
| Kein Snippet | Treffer ohne Textvorschau | |
| Dokumentanfang zeigen | erklaert den Treffer nicht | |

**User's choice:** Bester Chunk als Ausschnitt

| Option | Description | Selected |
|--------|-------------|----------|
| Nur in der Diagnose-Route (Empfohlen) | Suchweg bleibt karg (Sicherheitseigenschaft) | ✓ |
| Gar nicht | Diagnose kann Semantik-Wirkung nicht zeigen | |
| Im Suchweg mitgeben | neue Aussage vor dem Recheck | |

**User's choice:** Nur in der Diagnose-Route

---

## Embedding-Zeitpunkt und Ehrlichkeit

| Option | Description | Selected |
|--------|-------------|----------|
| Zweite Spur danach (Empfohlen) | Volltext/OCR nach ~10 h nutzbar, Semantik fuellt 7-24 h nach; OCR-Zweitspur-Muster | ✓ |
| Ein Durchgang | nichts nutzbar bevor alles fertig | |
| Nur neue Dateien | Bestand bekaeme nie Vektoren | |

**User's choice:** Zweite Spur (Backfill aus gespeichertem body_de, ohne Re-Download)

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, alle drei (Empfohlen) | Dauer als Messwert, Abdeckungsaussage, neue RSS-Zahl ersetzt die alte | ✓ |
| Nur RSS-Zahl, Rest weglassen | Fragen kaemen als Reviews zurueck | |

**User's choice:** Alle drei Store-Aussagen zugesagt

---

## Claude's Discretion

- Chunkgroesse/Ueberlappung innerhalb des 1.024-Deckels, Chargengroesse, Sequenzlaenge
- vectors.db eigene Datei oder state.db (nach Welle-0-Proben)
- Namen und Bereichspruefung der neuen Einstellungen
- onnxruntime-Sitzungsoptionen / fastembed-Durchreichung
- Wellen-Zuschnitt der Phase

## Deferred Ideas

None — discussion stayed within phase scope.
