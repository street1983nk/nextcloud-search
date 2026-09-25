# Roadmap: Findling

## Milestones

- [x] **v1.0 Volltext, OCR und semantische Suche** -- Shipped 2026-09-07 (Phasen 1-6 + 06.1, Archiv: .planning/milestones/v1.0-ROADMAP.md)
- [x] **v1.1 Qualitaet und Effizienz** -- Shipped 2026-09-11 (Phasen 7 bis 11, Archiv: .planning/milestones/v1.1-ROADMAP.md)
- [x] **v1.2 Messbeleg und Ausbau** -- Shipped 2026-09-21 (Phasen 12 bis 16, Archiv: .planning/milestones/v1.2-ROADMAP.md)
- [ ] **v1.3 Sprachausbau** -- Phasen 17 bis 23 (in Arbeit, Start 2026-09-23)

## Phases

<details>
<summary>v1.0 Volltext, OCR und semantische Suche (Phasen 1-6 + 06.1) -- SHIPPED 2026-09-07</summary>

Details im Archiv: .planning/milestones/v1.0-ROADMAP.md (103 Plaene, Store-Einreichung 1.0.0, Tags v1.0.0 bis v1.0.3)

</details>

<details>
<summary>v1.1 Qualitaet und Effizienz (Phasen 7-11) -- SHIPPED 2026-09-11</summary>

- [x] Phase 7: Gemeinsame Embedding-Engine (4/4 Plaene) -- completed 2026-09-08
- [x] Phase 8: Deutsche Komposita ohne Behelf (5/5 Plaene) -- completed 2026-09-08
- [x] Phase 9: Eigene Ergebnisseite (8/8 Plaene) -- completed 2026-09-09
- [x] Phase 10: Vergleichsmessung auf der AWS-Box (7/7 Plaene) -- completed 2026-09-10
- [x] Phase 11: Haertung und Store-Einreichung v1.1 (13/13 Plaene) -- completed 2026-09-11

Details im Archiv: .planning/milestones/v1.1-ROADMAP.md

</details>

<details>
<summary>v1.2 Messbeleg und Ausbau (Phasen 12-16) -- SHIPPED 2026-09-21</summary>

- [x] Phase 12: Messwerkzeug, Runbook und Terminentscheid (8/8 Plaene) -- completed 2026-09-16
- [x] Phase 13: Filter und Sortierung auf der Ergebnisseite (13/13 Plaene) -- completed 2026-09-19
- [x] Phase 14: Modell-Entladung im Leerlauf (12/12 Plaene) -- completed 2026-09-19
- [x] Phase 15: Messphase, eine Box-Anfahrt (16/16 Plaene) -- abgenommen 2026-09-21, Auflagen A1 bis A4 an Phase 16
- [x] Phase 16: Haertung und Store-Einreichung v1.2.0 (14/14 Plaene) -- completed 2026-09-21, v1.2.0 im Store (2x HTTP 201)

Details im Archiv: .planning/milestones/v1.2-ROADMAP.md

</details>

### v1.3 Sprachausbau (in Arbeit)

**Milestone-Ziel:** Die lexikalische Suche beherrscht Spanisch, Italienisch, Niederlaendisch und Portugiesisch (Tantivy-Sprachfelder mit sauberer Migration und bewiesenem Umbauweg), die UI spricht diese Sprachen, und die fuenf offenen Boxzahlen aus v1.2 werden nachgemessen. Abschluss: Store-Release 1.3.0.

- [x] **Phase 17: Owner-Tor und Analyseketten** - Grundsatzentscheide schriftlich, dann vier messend abgenommene Analyseketten es/it/nl/pt
 (completed 2026-09-23)

- [x] **Phase 18: Schema, Marken und Umbauweg** - Sechs Koerperfelder, Re-Analyse-Umbau aus dem Bestandsindex, Beweisstrecke umgedreht
 (completed 2026-09-24)

- [x] **Phase 19: Frageseite freischalten** - Die Anfrage erreicht die neuen Felder, erst nachdem der Umbau bewiesen ist (komplett 25.09.2026, Verifikation 4/4, Audit 1H/5M behoben, CI 36096526219 gruen 4/4)
- [x] **Phase 20: UI-Kataloge es/it/nl/pt** - Zehn neue Katalogdateien im Gleichstand mit EN/DE/FR (Parallelpfad) (completed 2026-09-25)
- [x] **Phase 21: Niederlaendische Komposita** - Eigenes Tor, faellt bei Terminnot als Ganzes (completed 2026-09-25)
- [ ] **Phase 22: Messanfahrt BL-F03** - Eine Box-Anfahrt fuer fuenf offene und zwei neue Zahlen
- [ ] **Phase 23: Haertung und Store-Einreichung 1.3.0** - Aufraeumbefunde, dokumentierte Grenzen, signiertes App-Paar im Store

**Ausfuehrungsreihenfolge und Sicherheitsbedingung:** 17 -> 18 -> 19 ist keine Aufwandsgruppierung, sondern eine Sicherheitsbedingung. Zwischen "Schema erweitert" und "Umbau fertig" liegt auf jeder Bestandsinstallation ein Zeitfenster, in dem eine geoeffnete Query-Feldliste zum Totalausfall fuehrt (`parse_query_lenient`-ValueError, vom Suchpfad zu einer dauerhaft leeren degraded-Antwort verschluckt). Phase 20 ist der einzige echte Parallelpfad und kann waehrend der Wartezeit am Owner-Tor laufen. Phase 21 haengt an Phase 19 und ist als Ganzes streichbar.

## Phase Details

### Phase 17: Owner-Tor und Analyseketten

**Goal**: Die Grundsatzentscheide des Milestones sind schriftlich gefallen, bevor eine Zeile Code sie implizit trifft, und die vier Analyseketten es/it/nl/pt sind messend abgenommen.
**Depends on**: Phase 16 (v1.2.0 im Store)
**Requirements**: LEX-01, LEX-07
**Success Criteria** (was WAHR sein muss):

  1. Ein datierter Owner-Entscheid liegt vor zu Umbauweg (Re-Analyse empfohlen), Feldmodell (sechs Felder immer im Schema), ob `FINDLING_LANGUAGES` Deutsch/Englisch abschalten darf, Sprachmenge als sechster Versionsmerker, Katalogprozess (maschinell plus Community-Review) und Go/No-Go fuer die niederlaendischen Komposita. Vor diesem Entscheid wird kein Code geschrieben, der D-04 beruehrt.
  2. Eine zusammengefuehrte Testfall-Tabelle aus STACK/FEATURES/PITFALLS ist je Sprache gruen: informacion/informaciones, informacao/informacoes (je akzentuiert und unakzentuiert), ano akzentuiert/unakzentuiert, italienisches "warum" als Stoppwort, niederlaendisches een/een mit Betonungsakzent, akzentuierte Stoppwoerter es/pt. Die Position von `ascii_fold` ist damit gemessen entschieden, nicht aus einer Quelle uebernommen, und das Verdikt je Sprache steht datiert in der Doku.
  3. Ein unbekannter oder nicht unterstuetzter Sprachname bringt den Container nicht per Rust-Panic zu Fall, sondern wird von einer geschlossenen Positivliste (Muster `OCR_LANGUAGE_ALLOWLIST`) beim Start abgewiesen; `tantivy` steht auf 0.26.2, `index_format v7` unveraendert.
  4. Eine Bestandsinstallation verhaelt sich nach dieser Phase unveraendert: kein neues Feld, keine bewegte Versionsmarke, volle Suite gruen.

**Plans**: 8 Pläne in 4 Wellen

Plans:

- [x] 17-01-PLAN.md: Owner-Tor als Entscheiddokument: acht Entscheide E-17-1 bis E-17-8 mit fertigen Ersatztexten
- [x] 17-02-PLAN.md: Sprach-Positivliste in config.py plus Doppelrichtungs-Paritätsgate gegen das laufende tantivy
- [x] 17-03-PLAN.md: Kettenfabrik snowball_analyzer(), gefaltete Ergänzungs-Stoppwortliste, AST-Wächter
- [x] 17-04-PLAN.md: Owner-Tor vorlegen (Checkpoint, blockiert 17-07/17-08), Vollzug datiert eintragen
- [x] 17-05-PLAN.md: Kettenmessung als wiederholbares Werkzeug: Sonde, Fixtures, Rohdaten, Messbericht
- [x] 17-06-PLAN.md: Messung wird Abnahme: Formfamilien-Gates, Stoppwort-Dichtheit, docs/language-analyzers.md
- [x] 17-07-PLAN.md: Vergleichsregel tantivy_version lockern (index_format-Hälfte), Gold-Werte mit Selbstproben
- [x] 17-08-PLAN.md: Pin auf tantivy==0.26.2, CI-Zusicherung, dependabot-Kommentar, THIRD-PARTY.md

**Research-Flag**: ja (`--research-phase 17`, die Kettenreihenfolge ist zwischen den vier Recherchen uneinheitlich)

### Phase 18: Schema, Marken und Umbauweg

**Goal**: Ein Bestandsindex wandert per Re-Analyse in das neue Sechs-Felder-Schema, ohne Download, ohne OCR, ohne Neu-Einbettung, und CI beweist den Weg in beide Richtungen.
**Depends on**: Phase 17
**Requirements**: LEX-02, LEX-03, LEX-04, LEX-06, LEX-08
**Success Criteria** (was WAHR sein muss):

  1. Eine Bestandsinstallation mit Werkseinstellung `de,en` findet nach dem Upgrade auf 1.3.0 genau dieselben Dokumente wie vorher, mit denselben Trefferzahlen; in KEINEM Zwischenzustand laeuft eine Suche leer (der ValueError-Pfad zu einer dauerhaft leeren degraded-Antwort ist nicht erreichbar). Migration `Version001300Date...` im Lockstep-Muster vorhanden.
  2. Ein Admin schaltet eine neue Sprache ein, und Findling baut den Index per Re-Analyse aus den gespeicherten Feldern um: `vectors.db` und `state.db` bleiben unberuehrt, der alte Index bedient Anfragen weiter, der Fortschritt steht im Banner (kein Aufruf zu `occ findling:index --restart`), und nach einem Neustart nimmt der Umbau wieder auf, statt von vorn zu beginnen.
  3. Reicht der Plattenplatz fuer zwei Indexverzeichnisse nicht, bricht der Umbau VOR dem Start mit klarer Meldung ab statt mitten im Lauf; der Rueckfall auf einen Vollreindex ist benannt und ausloesbar.
  4. Der Admin sieht in der Diagnose, welche Sprachen aktiv und welche befuellt sind, und bekommt beim Start eine Warnung, wenn `FINDLING_LANGUAGES` eine Sprache fuehrt, die die OCR-Sprachen nicht abdecken; die Sprachmenge ist sechster Merker in `expected_versions()`.
  5. CI beweist den Umbau: die bestehende "kein Reindex"-Strecke bleibt unveraendert bestehen, daneben steht eine zweite, umgedrehte Strecke in `deploy-harp.yml` (`UPGRADE_FROM_TAG=v1.2.0`), die zeigt, dass der Umbau vollstaendig lief, das Schema sich um genau eine Stufe bewegt hat, das Banner erschien und verschwand und keine alten Treffer verloren gingen. Die Sprachfaelle je neuer Sprache laufen in dieser Phase auf Feldebene ohne Fremdbestand (Muster A4/2026-09); ihre Hebung auf den normalen Suchweg ist Zusage von Phase 19.

**Plans**: 12 Plaene in 9 Wellen

Plans:

- [x] 18-01-PLAN.md: Dreizehn Felder, acht Ketten unbedingt registriert, SCHEMA_VERSION 2, Sperrklinke umgedreht
- [x] 18-02-PLAN.md: Befuellung nach FINDLING_LANGUAGES, _languages() filtert gegen SUPPORTED_LANGUAGES
- [x] 18-03-PLAN.md: Zwischenzustands-Beweis, Mengeninklusion plus AST-Waechter plus Schema-1-Fixture
- [x] 18-04-PLAN.md: Sprachfaelle es/it/nl/pt auf Feldebene, ohne Fremdbestand
- [x] 18-05-PLAN.md: Sechster Merker languages, Teilmengenregel, vier Aufrufstellen
- [x] 18-06-PLAN.md: index/rebuild.py, Vorpruefung, Bandlauf, zustandslose Wiederaufnahme
- [x] 18-07-PLAN.md: Verzeichnistausch, reset_read_side, eigene Stempelfunktion
- [x] 18-08-PLAN.md: Aufraeumpfad beim Start, vier Faelle plus Abfallfall
- [x] 18-09-PLAN.md: Lifespan-Aufgabe, Poller ruhigstellen, OCR-Startwarnung
- [x] 18-10-PLAN.md: Sprachstatus und Umbau-Banner auf der Adminseite, sechs Kataloge im Gleichstand
- [x] 18-11-PLAN.md: Lockstep-Migration Version001300Date... plus Unittest
- [x] 18-12-PLAN.md: UPGRADE_FROM_TAG auf v1.2.0, Store upgrade 6 mit neun Zusicherungen

**Research-Flag**: ja (`--research-phase 18`, `index/rebuild.py` ist eine neue Komponente ohne Vorbild im Repo; Wiederaufnahme und Platzpruefung unter Abbruchbedingungen sind nicht trivial)

### Phase 19: Frageseite freischalten

**Goal**: Nutzer findet Dokumente in den aktiven neuen Sprachen ueber die ganz normale Suche, und zwar erst, nachdem der Umbauweg bewiesen ist.
**Depends on**: Phase 18 (harte Sicherheitsbedingung, nicht verhandelbar)
**Requirements**: LEX-05
**Success Criteria** (was WAHR sein muss):

  1. Auf einer Instanz mit aktivem Spanisch findet der Nutzer ein spanisches Dokument ueber die Stammform seines Suchworts, in der Unified Search und auf der Ergebnisseite; derselbe Beweis laeuft je Sprache fuer it, nl und pt ueber den gruenen arm64-CI-Ast.
  2. Auf einer Instanz mit `de,en` aendert sich weder Trefferliste noch Reihenfolge: die Anfrage durchsucht ausschliesslich die aktiven und befuellten Felder, weil die Feldliste am `schema_version`-Merker haengt statt an einer Konstante.
  3. Ein Treffer in mehreren Sprachfeldern draengt sich nicht vor einen besseren englischen Treffer: die Boosts der vier neuen Felder liegen unterhalb `body_en`, belegt an einer Rangprobe.
  4. Es gibt keinen Spracherkennungspfad, weder dokument- noch anfrageseitig; ein Test haelt das Anti-Feature fest.

**Plans**: 9 Plaene in 6 Wellen

Plans:

- [x] 19-01-PLAN.md: FieldPlan als Wert, plan-Parameter, AST-Waechter der Phasengrenze ersetzt
- [x] 19-02-PLAN.md: it-Fixture waechst, Messung neu gefahren, Zaehlgate und Klassifizierung nachgezogen
- [x] 19-03-PLAN.md: Feldplan aus den zwei Marken, ReadSide.field_plan, drei Aufrufstellen
- [x] 19-04-PLAN.md: Rangprobe, Boosts unterhalb body_en mit Gegenprobe und gemessener Grenze
- [x] 19-05-PLAN.md: Anti-Feature-Waechter, keine Spracherkennung, vier Aussagen mit Gegenproben
- [x] 19-06-PLAN.md: Die vier Sprachfaelle auf dem normalen Suchweg, dritter Ketten-Ausschluss
- [x] 19-07-PLAN.md: Ungegateter CI-Sprachbeweis auf allen vier Aesten, plus Ergebnisseite
- [x] 19-08-PLAN.md: Spanischer Vorher-Nachher-Beweis in der Upgrade-Strecke, eigener Snapshotschluessel
- [x] 19-09-PLAN.md: Doku der Frageseite und ihrer Grenzen, CI-Lauf eingeholt, Laufzeit eingetragen

### Phase 20: UI-Kataloge es/it/nl/pt

**Goal**: Findling spricht in der Oberflaeche Spanisch, Italienisch, Niederlaendisch und Portugiesisch im Gleichstand mit EN/DE/FR.
**Depends on**: Nichts aus dem Indexstrang (Parallelpfad, laeuft neben Phase 17 bis 19)
**Requirements**: KAT-01, KAT-02
**Success Criteria** (was WAHR sein muss):

  1. Ein Nutzer, dessen Nextcloud auf es, it, nl, pt_BR oder pt_PT steht, sieht Findling vollstaendig in dieser Sprache, inklusive Fehler- und Diagnosetexte; keine englischen Reste.
  2. Jeder neue Katalog fuehrt dieselbe Schluesselzahl wie `de.json` (Zahl beim Planstart AUS DER DATEI gezaehlt, Stand Research 199, nicht die 174 aus dem Backlog); das Gate ist parametrisiert statt viermal kopiert und faellt rot, sobald ein Katalog zurueckbleibt.
  3. Die Pluralformen stimmen gegen die Kerndateien der Ziel-Nextcloud (`nplurals=3` fuer es/it/pt_BR/pt_PT, 2 fuer nl); sie sind gelesen, nicht erinnert.
  4. Der pt-Ladepfad ist VOR der Uebersetzungsarbeit an der laufenden Test-Nextcloud verifiziert; es liegen zehn Dateien (es, it, nl, pt_PT, pt_BR je json und js) am richtigen Ort (Messbefund Research 24.09.: alle unter php/l10n/, die ExApp laedt keine Kataloge; "fuer beide Apps" war eine korrigierte Fehlannahme).
  5. Jeder Katalog traegt einen datierten Review-Vorbehalt nach FR-Muster; kein Muttersprachler-Gate blockiert die Auslieferung.

**Plans**: 9 Plaene in 9 Wellen

Plans:

- [x] 20-01-PLAN.md: Pluralschluessel-Fix der sechs Bestandskataloge, Scanner teilt an `_::_`, Vorher-Nachher-Beleg (Checkpoint) -- gebaut 25.09.2026 (51e0ea4, 5389009), Owner-Go 25.09.2026
- [x] 20-02-PLAN.md: Ladepfad- und Pluralbeweis als docs/l10n-catalogues.md, PLURAL_FORM_OF je Sprachcode, php/l10n/** in python.yml -- gebaut 25.09.2026 (a283b7c, 1e6881f, 5b78e08)
- [x] 20-03-PLAN.md: Scanner parametrisiert statt kopiert, plus Prozent- und Pipe-Scanner gegen die zwei stillen Seitenzerstoerer -- gebaut 25.09.2026 (32f6e47, d2ddcb4, 106ce1e)
- [x] 20-04-PLAN.md: Spanisch, zwei Dateien, Gate-Eintrag, docs/l10n-spanish.md mit datiertem Vorbehalt -- gebaut 25.09.2026 (7dd61fd, c61955d, 64527aa, aa9f36a)
- [x] 20-05-PLAN.md: Italienisch, zwei Dateien, Gate-Eintrag, docs/l10n-italian.md mit datiertem Vorbehalt -- gebaut 25.09.2026 (ecf8bd2, fff9aba, e6185c9, 42f6add)
- [x] 20-06-PLAN.md: Niederlaendisch mit zwei Pluralformen und der zeichengleichen deutschen Regel als benanntem Sonderfall -- gebaut 25.09.2026 (3f76cdc, e7ed056, d40e335)
- [x] 20-07-PLAN.md: pt_PT, keine pt.json, docs/l10n-portuguese.md dreispaltig angelegt -- gebaut 25.09.2026 (e3fc290, 2824a4b, 7ae78d6)
- [x] 20-08-PLAN.md: pt_BR als eigene Varietaet, Unterschieds-Gate statt Textgleichheit, sechzehn Kataloge im Tupel -- gebaut 25.09.2026 (592980d, f79254c, cd38e2d)
- [x] 20-09-PLAN.md: CI-Sprachbeweis je Code in integration.yml, Sichtprobe in fuenf Sprachen (Checkpoint), Schlussabschnitt -- gebaut 25.09.2026 (1c80e26, 530bb7c, c5102d1), Sichtprobe vom Owner abgenommen

**UI hint**: nein (reine Katalogdateien zu bestehenden Oberflaechenelementen, kein neues Interface)

### Phase 21: Niederlaendische Komposita

**Goal**: Nutzer findet niederlaendische Komposita ueber ihre Glieder, oder die Phase faellt am eigenen Tor als Ganzes.
**Depends on**: Phase 19 (nl-Kette, Schema, Umbauweg und Frageseite muessen stehen)
**Requirements**: KOMP-01
**Success Criteria** (was WAHR sein muss):

  1. Vor dem ersten Codeschritt liegt ein datiertes Go/No-Go des Owners vor; bei No-Go faellt die Phase vollstaendig, ohne halbe Reste im Code oder in den Marken.
  2. Nutzer findet `gemeentebelastingen` ueber `belasting`; der zugehoerige CI-Sprachfall wird ohne Splitter rot.
  3. Lizenzlage (`wdutch`/OpenTaal, BSD-3-Clause + CC-BY-3.0) ist dokumentiert und das RAM-Budget des zweiten Automaten (rund 23 MB) ist VOR dem Bau gemessen; das Gesamtbudget auf der 4-GB-Box haelt.
  4. Eine eigene Digest-Marke loest den Umbau nur bei aktivem Niederlaendisch aus; eine Bestandsinstallation ohne nl sieht keinen Rebuild-Hinweis und keinen Lauf.

**Plans**: 9 Plaene in 7 Wellen

Plans:
**Wave 1**

- [x] 21-01-PLAN.md: Vorfragen per Test: D-08 fullreindex-Stempel und Poller-Drift-Falle (Fix: Band-Drift hebt keine Generation)
- [x] 21-02-PLAN.md: wdutch ins Abbild, docker.yml-Gate, THIRD-PARTY.md (CC-BY-3.0), Pin-Test
- [x] 21-08-PLAN.md: CI-Kompositumfall gemeentebelastingen/belasting im Language proof

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 21-03-PLAN.md: wordlist_nl.py (Rezept B 4-14, Liste freigegeben) und Splitterkette hinter der Faltung

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 21-04-PLAN.md: Messwerkzeug, Rezept- und RAM-Messung im Repo, Fixture, gemessene Tabellen-Tests

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 21-05-PLAN.md: siebte Marke wordlist_hash_nl in Store und open.py, Zustandstabelle als Tests, Upgrade-Gold

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 21-06-PLAN.md: Band-Umbau beantwortet die nl-Marke, alle expected_versions-Aufrufer, AST-Gate, index_status

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 21-07-PLAN.md: gated Registrierung der nl-Kette, alle open_index-Aufrufer, Re-Analyse-Beweis

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 21-09-PLAN.md: Doku, Budget, Schlusspruefung, Owner-Freigabe Push und CI-Beweis

**Research-Flag**: ja (`--research-phase 21`, eigene Rezeptmessung wie beim deutschen Splitter)

### Phase 22: Messanfahrt BL-F03

**Goal**: Die fuenf offenen Boxzahlen aus v1.2 und die zwei neuen v1.3-Zahlen stehen mit echtem Wert in docs/performance.md, aus EINER bezahlten Anfahrt.
**Depends on**: Phase 19 (und Phase 21, falls das Tor auf Go steht)
**Requirements**: MESS-07, MESS-08, MESS-09
**Success Criteria** (was WAHR sein muss):

  1. Rechenblatt und Kostendeckel liegen VOR dem Boxstart beim Owner und sind freigegeben; die Anfahrt bleibt unter dem Deckel, Rohdaten sind committet.
  2. Die fuenf offenen Zahlen stehen mit Wert und Datum in docs/performance.md: M-01-Zahl auf Zielhardware, Wirkungsnachmessung 92c/99d auf der Box, Bodensatz-Zyklus 2, die 6 Fehlschlaege und 44 uebersprungenen Dateien einzeln benannt, Kaltstartlatenz ohne Leerbegriff.
  3. Die zwei neuen Zahlen stehen daneben: reale Indexgroesse bei sechs befuellten Sprachfeldern am Korpus-Snapshot und Wandzeit des Re-Analyse-Umbaus, gegen die 19 h 20 min Vollreindex gestellt (die 1-bis-3-Stunden-Schaetzung ist damit belegt oder widerlegt).
  4. Der disjunction_max-Entscheid faellt auf Messbasis: die Rangverschiebung gegen die Score-Summe ist auf echten Daten gemessen, das Ergebnis ist umgesetzt oder dokumentiert verworfen.
  5. Die Runbook-Disziplin ist gehalten (Cron-Intervall-Gate als erzwungene Messbedingung, Digest-Wechsel protokolliert), und der Owner nimmt die Messphase ab.
  6. NEU (Owner 25.09.2026, BL-F04-Mitmessliste aus .planning/research/BL-F04-vorarbeit-2026-09-25.md Abschnitt 1): dieselbe Anfahrt erhebt die BL-F04-Basiszahlen B1-B3+B5 (Kernbelegung je Phase, OCR-Charge im Produkt, Speicher je zusaetzlichem OCR-Slot inkl. OMP_THREAD_LIMIT-Vergleich, onnx-Threads/Batch auf Graviton3) UND B4 (FREIGEGEBEN: Typwechsel m7g.4xlarge, Skalierungskurve 1/2/4/8/12/16 Kerne, ~1,25 h / ~1,00 USD; vorher entscheidet die kostenlose 4-Kern-CI-Kurve, ob B4 noch noetig ist). Die drei neuen Messskripte (cpu_sampler.sh, Speicher je Prozess, Slot-Probe) sind ZUSATZAUFTRAG dieser Phase, ohne Box baubar und vorab auf dem arm64-CI-Runner erprobt; rss_sampler.sh bleibt unveraendert. NL-Automat-RAM misst der CI-arm64-Runner, nicht die Box. Rechenblatt (Kriterium 1) MIT den Mitmessposten rechnen (+~2,7 h, +~1,30 USD gegenueber reinem BL-F03).

**Plans**: TBD

### Phase 23: Haertung und Store-Einreichung 1.3.0

**Goal**: Findling 1.3.0 steht als signiertes App-Paar im Store, mit ehrlich dokumentierten Grenzen des Sprachausbaus.
**Depends on**: Phase 22
**Requirements**: HART-04, HART-05, REL-03
**Success Criteria** (was WAHR sein muss):

  1. Die Aufraeumbefunde sind geschlossen: der `fastembed==0.8.0`-Pin ist entfernt oder sein Import belegt, `numpy` ist sauber deklariert oder als Abhaengigkeit eliminiert; die Abhaengigkeitsliste bildet ab, was der Container wirklich laedt.
  2. Ein Admin liest in Doku und Store-Text, was der Sprachausbau NICHT leistet: ano und ano fallen zusammen, die pt-Rechtschreibreform wird nicht vereinheitlicht, Komposita gibt es nur fuer de und nl, Franzoesisch hat weiterhin kein Koerperfeld.
  3. Fremdinstallation auf frischer Nextcloud und die Upgrade-Strecke 1.2.0 auf 1.3.0 inklusive Umbau-Fall sind Ende zu Ende gruen; das Audit nach der Haertung steht auf 0 CRIT / 0 HIGH, MEDIUM behoben, LOW dokumentiert entschieden.
  4. v1.3.0 ist eingereicht: beide Apps signiert, Submission mit 2x HTTP 201, Store-Texte gate-konform (Faktenliste, eine Messzahl an drei Stellen) und vom Owner vor der Abgabe abgenommen.

**Plans**: TBD

## Progress

**Ausfuehrungsreihenfolge:** 17 -> 18 -> 19 -> 21 -> 22 -> 23, Phase 20 parallel dazu.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-6 + 06.1 (Archiv) | v1.0 | 103/103 | Complete | 2026-09-07 |
| 7-11 (Archiv) | v1.1 | 37/37 | Complete | 2026-09-11 |
| 12-16 (Archiv) | v1.2 | 63/63 | Complete | 2026-09-21 |
| 17. Owner-Tor und Analyseketten | v1.3 | 8/8 | Complete   | 2026-09-23 |
| 18. Schema, Marken und Umbauweg | v1.3 | 12/12 | Complete   | 2026-09-24 |
| 19. Frageseite freischalten | v1.3 | 9/9 | Executing | - |
| 20. UI-Kataloge es/it/nl/pt | v1.3 | 9/9 | Complete    | 2026-09-25 |
| 21. Niederlaendische Komposita | v1.3 | 9/9 | Complete   | 2026-09-25 |
| 22. Messanfahrt BL-F03 | v1.3 | 0/TBD | Not started | - |
| 23. Haertung und Store-Einreichung 1.3.0 | v1.3 | 0/TBD | Not started | - |

## Requirement-Abdeckung v1.3

| Phase | Requirements |
|-------|--------------|
| 17 | LEX-01, LEX-07 |
| 18 | LEX-02, LEX-03, LEX-04, LEX-06, LEX-08 |
| 19 | LEX-05 |
| 20 | KAT-01, KAT-02 |
| 21 | KOMP-01 |
| 22 | MESS-07, MESS-08, MESS-09 |
| 23 | HART-04, HART-05, REL-03 |

17 von 17 v1.3-Requirements abgedeckt, keine Waise, keine Doppelung.

## Nach v1.3 (Wiedervorlage)

Offene Punkte, die bewusst NICHT in v1.3 liegen:

- Franzoesisches Koerperfeld (FR hat OCR und Katalog, aber keine lexikalische Kette; v1.4-Kandidat)
- Getrennte pt_BR/pt_PT-Wortlaute fuer die Suche selbst
- Niederlaendische Betonungsakzente als eigene `custom_stopword`-Liste
- Sortierung nach Name oder Groesse (Fast-Field, SCHEMA_VERSION-Sprung; koennte kuenftig mit einem ohnehin faelligen Umbau reisen)
- Mimetype-Gruppen aus `files.mime`, geplantes Vorwaermen
- Pro-Schiene (Index-Verschluesselung, External Storage; ISV-Entscheid 03.11.)
- Estnisch/Daenisch lexikalisch nicht moeglich (tantivy kennt keinen estonian-Stemmer): muss aktiv an die Buerokratt/OS2ai-Outreach-Spur kommuniziert werden, bevor dort falsche Erwartungen entstehen
- Snapshot `snap-03f1d1d9ad9262704`: Wiedervorlage beim Milestone-Close

Aktiver Blocker unabhaengig vom Milestone: Kill-Kriterium Nextcloud Conference (kuendigt Nextcloud eine Elasticsearch-freie Volltextsuche mit OCR an, wird das Projekt neu bewertet; geprueft 21.09.2026, nicht ausgeloest).

---
*Created: 2026-09-08. v1.1 archiviert: 2026-09-11. v1.2 archiviert: 2026-09-21. v1.3 aufgenommen: 2026-09-23.*
