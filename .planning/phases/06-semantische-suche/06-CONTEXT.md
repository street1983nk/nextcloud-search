# Phase 6: Semantische Suche - Context

**Gathered:** 2026-09-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Der Nutzer findet Dokumente auch über Umschreibungen statt nur über exakte
Wörter (RRF-Hybrid aus Tantivy- und Vektor-Treffern), im selben RAM-Budget
(2,0-GB-Container-Deckel) und durch exakt dieselbe ACL-Kette wie die
Volltextsuche (SQLite-Vorfilter, dann finaler PHP-Recheck). Fällt der
Vektorzweig aus, liefert die Suche unverändert Volltext-Ergebnisse. Das
Vektorschema wird erst nach den Vormessungen festgezurrt (SEM-03), und der
Abschluss der Phase ist die gebündelte Store-Abgabe des Erstrelease 1.0.0
(D-08 aus 05-CONTEXT.md).

</domain>

<decisions>
## Implementation Decisions

### Embedding-Umfang und Modell (Owner 04.09.2026)
- **D-01:** Es werden die ERSTEN 1.024 TOKEN je Dokument eingebettet (etwa
  2 Chunks je Dokument, rund eine Seite Text). Der Deckel ist eine
  Einstellung und nach oben aufdrehbar (Betreiber mit Zeit und Hardware
  können auf volles Embedding gehen), wird aber nicht auf der Admin-Seite
  beworben. Erwarteter Erstindex-Zuwachs damit 7 bis 24 Stunden statt 54 bis
  180 Stunden (Messung B ersetzt die Schätzung).
- **D-02:** Modell bleibt multilingual-e5-small, int8 selbst quantisiert vom
  fp32-Original (die mitgelieferte int8-Datei ist AVX512-only und auf ARM
  unbrauchbar), ins Image gebacken, HF_HUB_OFFLINE=1 (SEM-01 unverändert).
  Owner-Wunsch "beste Qualität" ist gegen e5-base abgewogen: +0,9 nDCG@10
  rechtfertigt doppelten Vektorspeicher und 2-3x Embedding-Zeit nicht.
  - **D-02, Zusatz vom 05.09.2026 (Owner).** Der Text oben bleibt unverändert.
    Plan 06-03 hat die Qualität dreisprachig gemessen und die Abbruchregel (5
    Prozent relativer MRR-Rückgang) auf Französisch gerissen. Nach der
    Nachmessung auf 120 statt 42 französischen Fällen hat der Owner **den
    Messpunkt der Regel auf die ausgelieferte Kombination gelegt**, also
    int8-Modell mit int8-Vektoren: sie steht bei -3,59 Prozent und damit unter
    der Grenze, ihre Richtung ist mit p = 0,0172 belastbar. **D-02 gilt damit als
    bestanden.** Die isolierte Modellfassung bei fp32-Vektoren bleibt mit -6,87
    Prozent gemessen; sie wird nicht ausgeliefert und ist deshalb nicht der
    Punkt, an dem die Regel greift. Die Umdeutung des Messpunktes ist eine
    Owner-Entscheidung und ausdrücklich keine stille Regeländerung; die Grenze
    von 5 Prozent steht unverändert. Folgen: kein Umbau, keine fp32-Auslieferung,
    Store-Text-Zusage unverändert nach D-03 und D-17. Belege und Begründung:
    `docs/measurements/2026-09-05-modellqualitaet/README.md`, Abschnitt "Der
    Owner-Entscheid vom 05.09.2026: der Messpunkt der Abbruchregel".
- **D-03:** MEHRSPRACHIGKEIT IST ANFORDERUNG (Owner): Deutsch, Englisch UND
  Französisch. Das Welle-0-Testset (fp32 gegen int8) wird DREISPRACHIG
  DE/EN/FR aufgebaut (deutsche Basis: GermanQuAD-Stichprobe + DACH-Korpus aus
  Phase 3, plus EN- und FR-Stichproben). Qualität wird belegt, nicht
  behauptet.
- **D-04:** potion-multilingual wird NICHT gebaut. Es bleibt der dokumentierte
  Notausgang; nur falls Messung B katastrophal ausfällt (selbst der
  1.024-Deckel über einem Tag), gibt es einen Owner-Checkpoint zur
  Neubewertung.
- **D-05:** Die E5-Präfixe ("query: " / "passage: ") bekommen einen eigenen
  Test (Anfrage mit und ohne Präfix, Rangfolge muss sich unterscheiden), weil
  fastembed sie bei selbst registrierten Modellen nicht automatisch setzt.
- **D-06:** Größenprüfung nach der Quantisierung im Dockerfile: Bau bricht ab,
  wenn die int8-Datei wesentlich über ~130 MB liegt (fängt die
  nicht-quantisierte Einbettungstabelle, 81,7 % der Parameter).

### Vektorspeicher und Ausweichpfad (Owner 04.09.2026)
- **D-07:** Speicherung als int8-Vektoren (384 Dimensionen) in sqlite-vec,
  brute-force-KNN, exakt gepinnt auf v0.1.9 (kein >=; die 0.1.10-Alphas sind
  tabu). Bei ~100.000 Chunks (D-01) liest ein voller Scan ~38 MB.
- **D-08:** ABSTRAKTIONSSCHNITT: der Vektorspeicher liegt hinter einer
  schmalen Schnittstelle (speichere, lösche, finde_ähnliche); ein späterer
  Austausch (Bit-Vektoren, usearch) ist eine Datei, kein Umbau. Das ist die
  belastbare Form des SEM-03-Ausweichpfads.
- **D-09:** Die vorgebaute sqlite-vec-Bibliothek (.so aus dem py3-none-Rad)
  wird im Abbild festgehalten statt beim Bau von PyPI gezogen (Muster
  APPSTORE_SHA); Lizenz- und Herkunftsangabe in THIRD-PARTY.md. PyPI-Ausfall
  oder Paket-Rückzug treffen den Bau damit nicht.
- **D-10:** Bit-Vektoren und usearch werden NICHT gebaut, nur als
  Ausweichpfade dokumentiert (mit den Kosten/Nutzen-Befunden aus
  06-RESEARCH.md Abschnitt 2.3).

### Ranking und Treffer-Anzeige (Owner 04.09.2026)
- **D-11:** Chunk-auf-Dokument-Aggregation: MAXIMUM. Der beste Chunk bestimmt
  den Dokumentrang (längenneutral; der Rang-Chunk ist zugleich der
  Snippet-Chunk aus D-13).
- **D-12:** RRF-Parameter: k=60, Fenstertiefe 100 je Quelle, Gewichte
  lexikalisch 1,0 / semantisch 1,0; das semantische Gewicht ist per
  Einstellung senkbar (dämpfen ohne abschalten). Alles stille Stellschrauben,
  nicht auf der Admin-Seite beworben. rank beginnt bei 1 (häufigster
  Implementierungsfehler). VORBEHALT für die Phase: die Fenstertiefe 100
  interagiert mit der Vorfilter-Selektivität (gemessener Extremfall: 31 von
  400 Kandidaten überleben) und wird in der Phase geprüft.
- **D-13:** Snippet für rein semantische Treffer: char_start/char_end je Chunk
  werden gespeichert, der Ausschnitt des besten Chunks wird aus dem
  gespeicherten body_de geschnitten. Ausschließlich in snippets_for(), also
  NACH prefilter_visible und nach dem PHP-Recheck, wie jedes andere Snippet.
- **D-14:** Herkunftsmarkierung (lexikalisch/semantisch/beides) NUR in der
  Diagnose-Route aus Phase 4. Der Suchweg bleibt karg: Candidate trägt
  weiterhin nur fileId, score, mtime (dokumentierte Sicherheitseigenschaft).

### Embedding-Zeitpunkt und Ehrlichkeit (Owner 04.09.2026)
- **D-15:** Embedding läuft als ZWEITE SPUR nach dem Volltext/OCR-Lauf, nach
  dem Muster der OCR-Zweitspur aus Phase 3 (Backfill aus dem gespeicherten
  body_de, OHNE Re-Download der Dateien). Volltext und OCR sind nach ~10 h
  nutzbar, die Semantik füllt sich danach.
- **D-16:** Die Statusseite bekommt eine ZWEITE Deckungsgrad-Zahl für die
  Semantik-Spur (ADM-01-Erweiterung); der Admin sieht beide Spuren getrennt.
- **D-17:** Store-Text-Ehrlichkeit, alle drei zugesagt: (a) die
  Embedding-Dauer wird als gemessene Zahl aus dem Volllauf genannt, (b) die
  Abdeckungsaussage steht drin ("die semantische Suche deckt den Anfang jedes
  Dokuments ab, die Volltextsuche weiterhin alles"), (c) die RSS-Store-Zahl
  wird nach Phase 6 mit aktiver Semantik neu belegt und ersetzt die alte
  (bestätigt D-09 aus 05-CONTEXT.md).

### Gesetzte Zusagen aus der Recherche (keine Optionsfragen, verbindlich)
- **D-18:** Die drei Vormessungen laufen als WELLE 0 vor jeder
  Schema-Fixierung (SEM-03): A Zeichen je Token (deutscher Text, 30 s),
  B Token je Sekunde auf aarch64 (entscheidet die Laufzeitfrage), C
  Scan-Latenz gegen Chunk-Anzahl (int8 und bit, kalt und warm). Keine braucht
  die AWS-Box; die arm64-CI-Läufer genügen. Dazu die zwei
  Fünf-Minuten-Proben: läuft vec0-KNN unter PRAGMA query_only=1, und erlaubt
  die CPython-Übersetzung im Abbild ladbare Erweiterungen.
- **D-19:** Der Vektorzweig bekommt einen EIGENEN try/except innerhalb von
  candidates(): bei Ausfall (Modell fehlt, Erweiterung nicht geladen) wird
  die Vektorliste leer und RRF zur Identität auf der Tantivy-Liste;
  protokolliert und über degraded sichtbar, aber die lexikalische Antwort
  steht (Kriterium 3). Eigener Abnahmetest: Modelldatei umbenennen, suchen,
  Volltexttreffer erwarten.
- **D-20:** Verschmelzung AUSSCHLIESSLICH innerhalb von
  index/search.py::candidates(), oberhalb des prefilter_visible-Aufrufs.
  Keine zweite Route, keine Verschmelzung auf der PHP-Seite; Provider.php
  bleibt unverändert, der Paritätstest aus Phase 5 deckt den Vektorzweig
  damit automatisch mit ab (Kriterium 2 strukturell). Die Offset-Semantik
  (Zähl-Orakel T-02-93) muss die Verschmelzung überleben.
- **D-21:** Löschweg vollständig: drop_document, tombstone, reset_for_reindex
  und der add-Pfad löschen Vektoren/Chunks derselben file_id VOR dem
  Einfügen (Wiederzustellungs-Dubletten). Eigene vectors-Tabellen leben in
  derselben Storage-Disziplin (aller SQL unter store/), SCHEMA_VERSION steigt
  auf "2", embedding_version als neue meta-Marke; NUR additive
  Schemaänderung, kein Reindex des Volltextbestands.

### Claude's Discretion
- Exakte Chunkgröße/Überlappung innerhalb des 1.024-Token-Deckels (Messung A
  informiert), Chargengröße und Sequenzlänge der Inferenz (RAM-Hebel 4/5 aus
  06-RESEARCH.md 3.6).
- Ob die Vektoren in einer eigenen vectors.db oder in state.db liegen
  (Empfehlung der Recherche: eigene Datei, verwerfbar ohne Volltextverlust);
  Entscheidung nach den Welle-0-Proben.
- Name und Bereichsprüfung der neuen Einstellungen (Deckel, semantisches
  Gewicht) nach dem Muster von SEARCH_OFFSET_MAX.
- onnxruntime-Sitzungsoptionen (Arena-Verhalten, A11) und ob fastembed sie
  durchreicht oder onnxruntime direkt angesteuert wird.
- Zuschnitt der Arbeitspakete und Wellen innerhalb der Phase.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 6 direkt
- `.planning/phases/06-semantische-suche/06-RESEARCH.md` — die vollständige
  Recherche (04.09.2026): Andockpunkte mit Datei/Zeile, Paketprüfung,
  RAM/Laufzeit-Rechnungen, die drei Vormessungen, 7 Fallstricke, 13 Annahmen
  (A1-A13). Die 9 Discuss-Fragen dort sind durch DIESES Dokument entschieden.
- `.planning/ROADMAP.md` — Phase-6-Ziel + 5 Erfolgskriterien + Research-Flag
- `.planning/REQUIREMENTS.md` — SEM-01, SEM-02, SEM-03

### Übergreifende Entscheidungen
- `.planning/phases/05-h-rtung-und-store-einreichung-v1-0/05-CONTEXT.md` —
  D-08 (Bündel-Abgabe als Abschluss von Phase 6), D-09 (RSS-Zahl neu belegen),
  D-10 (Deadline + Staffelungs-Fallback), D-11 (Lockstep 1.0.0), D-12
  (Store-Text-Regeln), D-21/D-22 (Paritäts-Definition)
- `.planning/PROJECT.md` — Constraints (4-8 GB RAM, ARM, NC-Fenster, AGPL,
  Solo-Dev, Jahresende), Out of Scope (kein eigenes Rechtemodell in Python)

### Messgrundlagen und Betrieb
- `docs/performance.md` — alle gemessenen Zahlen (428,6 MB Spitze, 2,0-GB-
  Grenze, 27.067 Zeichen/Dokument, 1,355 Mrd. Zeichen, Indexgröße); die
  ARM-Zeile kommt aus dem laufenden 05-21-Volllauf dazu
- `docs/testing.md` — Gate-Landschaft; die neuen Gates (Offline-Start,
  Präfix-Test, Modell-Ausfall) reihen sich dort ein
- `THIRD-PARTY.md` — Ort für die sqlite-vec-Herkunftsangabe (D-09)

</canonical_refs>

<code_context>
## Existing Code Insights

(Vollständige Sondierung mit Zeilennummern in 06-RESEARCH.md Teil 1; hier die
Anker.)

### Reusable Assets
- `backend/src/findling/index/search.py::candidates()` — die EINZIGE Stelle,
  aus der Kandidaten den Container verlassen; ruft prefilter_visible selbst.
  Hier wird verschmolzen (D-20).
- OCR-Zweitspur aus Phase 3 (`poller.py::_goes_to_the_ocr_track()`,
  skipped/no_text_layer-Abarbeitung) — das Vorbild für die Embedding-Spur
  (D-15).
- `store/schema.sql` meta-Tabelle — ausdrücklich offen für die
  embedding_version-Marke, keine Migration nötig.
- Phase-4-Diagnose-Route (`api/diagnose.py`) — Ort der Herkunftsmarkierung
  (D-14).
- arm64-CI-Läufer aus `docker.yml` — führen die Welle-0-Messungen aus (D-18).

### Established Patterns
- Aller SQL lebt unter `store/` (repo.py-Disziplin) — gilt auch für vec0-SQL.
- Privacy-Vertrag Container->PHP (nur fileids, Zahlen, Codes) — ein
  Vektortreffer hat dieselbe Candidate-Form, der Vertrag bleibt unverändert.
- Offset zählt erlaubte Kandidaten, nie rohe Treffer (Zähl-Orakel T-02-93) —
  muss die RRF-Verschmelzung überleben (D-20).
- INDEX_WORKERS=1 liest absichtlich keine Env-Variable (config.py) — OCR- und
  Embedding-AKTIVIERUNGEN treffen sich nie; die Modellgewichte als Dauerlast
  sind in der RAM-Rechnung separat ausgewiesen (06-RESEARCH.md 3.2).

### Integration Points
- `poller.py::_record_of()` bzw. unmittelbar davor — Chunking+Embedding im
  Schreibweg, gleiche Charge wie der Tantivy-Schreibvorgang.
- `repo.py::_connect()` — braucht enable_load_extension für beide
  Verbindungsarten; query_only-Probe gehört an den Phasenanfang (D-18).
- `writer.py` add/drop_document, `repo.py` tombstone/reset_for_reindex — der
  Löschweg (D-21).
- Statusseite/AdminViewService — zweite Deckungsgrad-Zahl (D-16).

</code_context>

<specifics>
## Specific Ideas

- Owner-Formulierung zur Modellwahl: "beste Qualität, FR und Englisch sollen
  auch berücksichtigt werden" — eingelöst über das dreisprachige Testset
  (D-03) und die belegte Cross-Lingual-Stärke der e5-Familie, nicht über ein
  größeres Modell.
- Store-Aussage-Muster wie in Phase 5: ehrlich gemessene Zahl mit verlinktem
  Messbericht ("Volllauf 50k Dateien auf 4-GB-ARM, Peak X GB, Embedding-
  Nachlauf Y h").

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (potion-multilingual ist kein
Deferred-Feature, sondern ein dokumentierter Notausgang, siehe D-04.)

</deferred>

---

*Phase: 6-Semantische Suche*
*Context gathered: 2026-09-04*
