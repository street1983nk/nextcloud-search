# Phase 22: Messanfahrt BL-F03 - Context

**Gathered:** 2026-09-25
**Status:** Ready for planning

<domain>
## Phase Boundary

EINE bezahlte Box-Anfahrt (m7g.large aus Snapshot snap-03f1d1d9ad9262704) liefert:
die fuenf offenen v1.2-Boxzahlen (M-01-Zahl, Wirkungsnachmessung 92c/99d,
Bodensatz-Zyklus 2, die 6 Fehlschlaege und 44 uebersprungenen Dateien einzeln
benannt, Kaltstartlatenz ohne Leerbegriff), die zwei neuen v1.3-Zahlen
(Indexgroesse bei sechs Sprachfeldern, Wandzeit des Re-Analyse-Umbaus gegen
19 h 20 min Vollreindex), den disjunction_max-Entscheid auf Messbasis (MESS-09)
UND die BL-F04-Mitmessposten B1-B5 samt B4-Typwechsel. Zusatzauftrag: die drei
Messwerkzeuge W1-W3 boxlos bauen und W4 (CI-arm64-Vorabkurve) VOR dem
Rechenblatt fahren. Alles nach Runbook-Disziplin (docs/runbook-messbox.md).

</domain>

<decisions>
## Implementation Decisions

### Deckel und Abbruchregel
- **D-01:** Kostendeckel im Rechenblatt: **24 Boxstunden / ~3,00 USD**
  (Rechenwert 11-17 h plus ~40% Reserve). Der Deckel steht als eigene Zeile im
  Rechenblatt, B4 als eigener Deckelposten darin (~1,25 h / ~1,00 USD).
- **D-02:** Bei Erreichen des Deckels: **HARTER STOPP** der Box (Kosten enden
  sofort), fehlende Messungen werden als LUECKEN im Messbericht dokumentiert,
  der Owner entscheidet anhand des Berichts ueber eine Nachfreigabe. Keine
  stillschweigende Verlaengerung.

### B4-Entscheidungsregel (CI-Vorabkurve)
- **D-03:** W4 (CI-arm64, 4 Kerne) laeuft VOR dem Rechenblatt. Regel fuer B4:
  Slot-Faktor >= 1,5 auf der CI-Kurve heisst **B4 wird gefahren** (also auch im
  Zwischenbereich 1,5-3,0; Owner-Steuerung: Mehrheit der Nutzer hat viele
  Kerne, Kosten nur ~1 USD). Nur unter 1,5 entfaellt B4 (und BL-F04-Stufe 2
  kippt, siehe Research Abschnitt 5 K1).

### disjunction_max-Folge (MESS-09)
- **D-04:** Faellt die Messung FUER disjunction_max aus, wird die Umsetzung
  **noch in Phase 22 gebaut** (Suchpfad-Aenderung, beweisbar ueber CI und
  lokale Suite, KEINE neue Box-Anfahrt dafuer). Kriterium 4 gilt woertlich:
  umgesetzt oder dokumentiert verworfen. Phase 23 haertet den Endstand.

### Zeitnot-Prioritaet auf der Box
- **D-05:** Streichreihenfolge bei knapper Boxzeit: zuerst faellt **B7**
  (NL-Automat, kann komplett in CI), dann **B5** (onnx-Kombis, CI-Naeherung
  existiert), dann **B4** (eigener Deckelposten), dann **B2/B3** (OCR-Slots).
  Die BL-F03-Pflichtzahlen (Erfolgskriterien 2-3) und **B1** (kostet 0 min
  Zusatzzeit) fallen NIE; sie sind der Zweck der Phase.

### Claude's Discretion
- Reihenfolge der Messungen innerhalb der Anfahrt (Research Abschnitt 1.5 als
  Startpunkt), Blockzuschnitt, Auswertungsformat der Rohdaten, Gestaltung des
  Rechenblatts (Praezedenz v1.2-Messanfahrt).
- Gestrichene Posten B8/B9/B10 bleiben gestrichen (Research-Begruendung).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Mitmessliste und Mehrkern-Rechnung (WICHTIGSTE QUELLE)
- `.planning/research/BL-F04-vorarbeit-2026-09-25.md` , Abschnitt 1 ist die
  verbindliche Mitmessliste (B1-B7 mit Messrezepten, Boxzeiten, Werkzeugen
  W1-W4, CI-zuerst-Aufteilung 1.4, Reihenfolge 1.5); Abschnitt 2 die
  Mehrkern-Rechnung, Abschnitt 5 die Kill-Kriterien (K1).

### Herkunft der fuenf Boxzahlen
- `.planning/BACKLOG.md` , Eintrag BL-F03 (die fuenf Punkte mit
  Herkunftsbelegen, Aufwandsschaetzung 6-10 Boxstunden).
- `docs/performance.md` , Zielort aller Zahlen; traegt den RAM-Nachtrag vom
  25.09. (24-25 MB NL-Automat) und den Wiederaufwaerm-Nachtrag vom 21.09.

### Runbook und Praezedenz
- `docs/runbook-messbox.md` , Abschnitte 2 (Box, Satz 0,115841 USD/h,
  Wechselpfad-Fallen 2.1) und 4 (Korpus-Snapshot); Runbook-Disziplin ist
  Erfolgskriterium 5.
- `docs/measurements/2026-09-v12-messung/` , Praezedenz der v1.2-Anfahrt
  (Rechenblatt-Form, Deckelfuehrung, Rohdaten-Ablage, Cron-Intervall-Gate).

### MESS-09-Startpunkt
- `docs/language-analyzers.md` , traegt die 19-04-Messung (Rangkipppunkt 0,81
  gegen ausgelieferte 0,6), Startpunkt des disjunction_max-Entscheids.

### Werkzeug-Vorbilder
- `scripts/ops/rss_sampler.sh` , bleibt UNVERAENDERT (CSV ist
  Vergleichsgrundlage); W1/W2 folgen seinem Muster (Pfadbildung,
  verweigern statt Nullen).
- `.github/workflows/measure.yml` , Wegwerf-Container-Muster desselben
  Digests; W4 wird hier erweitert (ubuntu-24.04-arm).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/ops/rss_sampler.sh`: Muster fuer W1 (cpu_sampler.sh) und W2
  (proc_anon_sampler.sh); selbst nicht anfassen.
- `python -m findling.embed.bench` (`--threads`, `--mode tokens-per-second`):
  existiert, traegt B5 und den onnx-Teil von B4.
- `extract/sandbox.py:287` (`ExtractionWorker`): Baustein fuer W3
  (ocr_slot_probe.py).
- Synthetischer Scan-Generator (Reproduzieren-Abschnitt in
  docs/performance.md): Scan-Material fuer B2/B3, NIE Nutzerdateien.

### Established Patterns
- Kein BL-F04-Block darf eine BL-F03-Messung veraendern: keine
  Umgebungsvariable des Produktcontainers vor Abschluss aller
  BL-F03-Schritte, BL-F04-Bloecke danach oder im getrennten Container.
- Hart verdrahtete Achsen (onnx THREADS=2, tantivy num_threads=1,
  OMP_THREAD_LIMIT=1) sind NUR ueber Wegwerf-Container messbar.
- T-02-14: Messwerkzeuge geben nie Textinhalte oder Nutzerpfade aus, nur
  Zahlen und Prozessnamen.
- Messskripte werden im CI-arm64-Runner erstprobt, damit der Erstvollzug
  nicht in die bezahlte Boxzeit faellt (Lehre Phase 15).

### Integration Points
- W4 haengt in `.github/workflows/measure.yml` (neuer arm-Lauf).
- Owner-Checkpoint VOR dem Boxstart: Rechenblatt mit Deckel 24 h / ~3,00 USD,
  Mitmessposten und B4-Zeile, plus W4-Kurvenergebnis (D-03-Regel angewandt).
- Verzahnung (Owner 25.09.): Messlaeufe laufen unbeaufsichtigt auf der Box,
  waehrend die Phase-23-Haertung lokal laeuft.

</code_context>

<specifics>
## Specific Ideas

- Der Deckel ist bewusst EIN Betrag (24 h / ~3,00 USD) mit B4 als benannter
  Position darin; keine gestaffelten Teilfreigaben.
- Harter Stopp heisst: Box anhalten ist der Abbruchmechanismus, nicht das
  Ende der Auswertung; committete Rohdaten bis zum Stopp werden normal
  ausgewertet.

</specifics>

<deferred>
## Deferred Ideas

- Tantivy `num_threads` als v1.4-Hebel fuer den Umbauweg (haengt an B6-Ergebnis;
  Vergleichsmessung gehoert in CI, nicht auf die Box) , Research Abschnitt 1.2.
- Marken-Reparatur vectors.py (Gewichts-Praezision in embedding_version) —
  bereits im v1.4-Umfang (Owner 25.09.).

</deferred>

---

*Phase: 22-Messanfahrt BL-F03*
*Context gathered: 2026-09-25*
