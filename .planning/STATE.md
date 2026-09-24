---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Sprachausbau
status: executing
stopped_at: Phase 19, Plan 19-08 fertig (spanischer Vorher-Nachher-Beweis), naechster Plan 19-09
last_updated: "2026-09-25T10:05:00.000Z"
last_activity: 2026-09-25 -- 19-08 ausgefuehrt (spanischer Vorher-Nachher-Beweis in der Upgrade-Strecke, Kette 0, 0, 1)
progress:
  total_phases: 7
  completed_phases: 2
  total_plans: 38
  completed_plans: 28
  percent: 32
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-23, Start Milestone v1.3)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 19 (frageseite-freischalten), Ausfuehrung laeuft; Phase 20 geplant

## Current Position

Phase: 19 (frageseite-freischalten), EXECUTING, Plan 8 of 9; Phase 20 (ui-kataloge) geplant, 0 of 9
Status: Ausfuehrung Phase 19 laeuft (9 Plaene in 6 Wellen). 19-01 fertig (82bf2b1): die drei
Modulkonstanten DEFAULT_FIELDS/TITLE_ONLY_FIELDS/FIELD_BOOSTS sind ein Wert (FieldPlan,
LEGACY_PLAN), build_query nimmt plan keyword-only mit dem Bestandsplan als Vorgabewert, der
AST-Waechter aus test_schema_generations.py ist weg und test_query_fields_plan.py steht an
seiner Stelle. 19-02 fertig (10917a0): chain_cases_it.txt traegt eine Flexionsfamilie, die Messung
ist neu gefahren (Rueckgabecode 0, it 14/56 auf 15/60, Summe 65/573 auf 66/577), der Messbericht hat
einen Abschnitt "Nachlauf vom 24.09.2026", EXPECTED_FAMILY_SCORES steht auf den gemessenen Zahlen und
it ist von FOLDED nach SEPARATED gewandert. 19-03 fertig (354ef27): SCHEMA_MARK steht neben
LANGUAGES_MARK, field_plan_for(marks, index) rechnet den Feldplan aus den zwei gespeicherten
Marken des Verzeichnisses (Tor faellt geschlossen, doc_freq-Sonde als Gegenprobe, wirft nie),
ReadSide traegt field_plan und reset_read_side verwirft ihn mit den Handles, die drei
Aufrufstellen reichen plan=side.field_plan durch. 19-04 fertig (459fc20, c4d7cbc): die
Rangprobe zu Erfolgskriterium 3 steht in backend/tests/test_field_plan_ranking.py, acht
Faelle auf einem echten Index mit drei Dokumenten und sechs befuellten Koerperfeldern.
Der bessere englische Treffer steht bei den ausgelieferten Gewichten vorn, die Gegenprobe
mit allen vier Zusatzgewichten auf 1,0 kippt den Rang, und die gemessene Kippgrenze ist
TIPPING_BOOST = 0,81 (Sweep ueber 101 Werte, 24.09.2026, tantivy 0.26.2). BODY_BOOST bleibt
bei 0,6, der Abstand zur Grenze betraegt 0,21; also keine Datei unter backend/src/findling
angefasst und die Ratsche unberuehrt. 19-05 fertig (0b59fca): der Anti-Feature-Waechter
backend/tests/test_no_language_detection.py haelt die vier Aussagen aus RESEARCH Pattern 5
fest (field_plan_for nimmt keinen Anfragetext, build_query liest den Plan nur aus seinem
Parameter, weder pyproject.toml noch uv.lock fuehrt ein Erkennungspaket, das Wireformat-Gate
wird genannt statt wiederholt), zehn Faelle, jede Aussage mit Gegenprobe, jeder Leser faellt
geschlossen. Erfolgskriterium 4 der Roadmap ist damit belegt. 19-06 fertig (6c20b11):
backend/tests/test_language_cases_query_path.py hebt die vier Sprachfaelle von der
Feldebene auf den normalen Suchweg, 37 Faelle, null uebersprungen. Die Frage laeuft durch
build_query mit einem Feldplan, der Fallindex traegt den Bestand einer echten Instanz
(derselbe Text in body_de, body_en und dem Feld der Sprache), und deshalb muss das
Formenpaar von der eigenen Kette zusammengefuehrt und von der englischen UND der deutschen
getrennt werden. Je Sprache zwei Gegenproben: ein Plan ohne body_<code> verliert die andere
Form, und dieselbe state.db mit schema_version auf 1 ergibt LEGACY_PLAN und verliert sie
auch. Volle Suite 2831 bestanden / 15 uebersprungen. 19-07 fertig (e7fcd0b, 251c86c,
368ecf5): die Entwicklerstrecke von deploy-harp.yml installiert mit de,en,es,it,nl,pt
(vierter sed-Ausdruck in der temporaeren info.xml, mit Einmaligkeitspruefung; die
Quelldatei und der Store-Durchgang unberuehrt), und zwischen "Search over the ordinary
OCS route" und der Driftprobe steht ein Schritt OHNE if-Zeile, der auf allen vier
Matrixaesten laeuft: Vorbedingung auf languagesActive, vier Dokumente ueber WebDAV, vier
Formenpaare, die nur die eigene Kette zusammenfuehrt, Pollschleife mit eigenem Budget
LANGUAGE_PROOF_BUDGET_SECONDS, Zusicherung auf entries | length und nie auf den
Textauszug, danach vier Abrufe der Ergebnisseite, die bis dahin kein CI-Schritt dieses
Repos beruehrt hatte. backend/tests/test_language_proof_steps.py haelt das fest (19
Faelle, Textgate ohne YAML, die zwei gegateten Store-upgrade-Schritte als Gegenbeispiel).
Volle Suite 2850 bestanden / 15 uebersprungen. 19-08 fertig (f0ceef6, c5a450c,
8ac2626): die Upgrade-Strecke traegt den spanischen Vorher-Nachher-Beweis. "Store
upgrade 2" legt upgrade-carta-es.txt in das Konto von testuser, indexiert unter
v1.2.0 in ein Schema ohne body_es; snapshot() holt den Trefferstand ueber den
vorhandenen Zaehler term_hits und legt ihn unter dem EIGENEN Schluessel spanish ab,
nicht als vierten Eintrag in .terms, weil die Vorbedingung [.terms[]] | all(. == 1)
zweimal im Workflow steht und an einem Term braeche, der vorher null sein SOLL. Drei
Zusicherungen bilden die Kette: 0 auf der Bestandsinstallation (Store upgrade 3), 0
nach dem Upgrade und vor dem Umbau (siebte Zusicherung von Store upgrade 5, die
CI-Haelfte von Erfolgskriterium 2), 1 nach dem Umbau (zehnte Zusicherung von Store
upgrade 6). Die Zusicherungszahlen in Schrittnamen und Protokollzeilen sind
mitgezogen. backend/tests/test_language_proof_steps.py haelt die drei neuen Aussagen
fest (19 auf 26 Faelle, drei gestellte Muster, je eine Gegenprobe). Volle Suite 2857
bestanden / 15 uebersprungen.
Planung 24.09.: Research b2ef69f,
Pattern-Karte, Plaene 51525d5, Checker PASS, Warnungen behoben 3c35186. Phase 20 geplant
(a8d40fd, Checker PASS, f32bdec). Phase 18 davor KOMPLETT (12/12, CI-Beweis 36026836087).
Last activity: 2026-09-25 -- 19-08 ausgefuehrt (spanischer Vorher-Nachher-Beweis in der Upgrade-Strecke, Kette 0, 0, 1)

Progress: [███.......] 32% (2 von 7 Phasen)

## Naechster Schritt

Weiter in Phase 19 mit dem letzten Plan 19-09 (Doku der Frageseite und ihrer Grenzen,
CI-Lauf einholen, Laufzeit eintragen). Der REQUIREMENTS-Haken fuer LEX-05 ist
weiterhin NICHT gesetzt: 19-06 hat die Testebene, 19-07 den ungegateten CI-Schritt und
19-08 die Upgrade-Haelfte geliefert, aber den gruenen Lauf holt erst 19-09 ein, und der
Haken gehoert der Phase-Verifikation.
VIER Nachtraege fuer 19-09, drei aus 19-07 und einer aus 19-08: die gemessene Laufzeit
des Sprachbeweisschritts gehoert als Zahl in den RE-MEASURE-Absatz ueber
LANGUAGE_PROOF_BUDGET_SECONDS; der Parameter der Ergebnisseite heisst query und nicht
term (PageController::term() liest getParam('query'), Zeile 340; PLAN und RESEARCH
Pattern 7c sagen beide term und sind zu berichtigen); der leere Textauszug bei einem
reinen Sprachfeld-Treffer gehoert als Grenze nach docs/language-analyzers.md; und die
Ein-Wort-Bedingung des spanischen Upgrade-Beweises gehoert neben die Beschreibung der
Upgrade-Strecke, weil sie heute nur im Workflowkommentar steht. Danach oder parallel:
`/gsd:execute-phase 20` (UI-Kataloge; Wellen 1 und 9 sind Checkpoints, 20-01 Pluralfix
der sechs Bestandskataloge braucht die Owner-Sichtprobe). Phase-20-Planung 24.09.:
9 Plaene in 9 Wellen (a8d40fd), Checker PASS, Fussabdruck strikt getrennt von Phase 19
(php/l10n/**, test_admin_ui_contract.py, docs/l10n-*.md, python.yml + integration.yml).
Groesster Research-Fund: Pluralschluessel aller sechs Bestandskataloge im falschen Format
(de/fr antworten bei n=2 mit "2 days"), Fix ist Welle 1.
Entscheide der Planung, die die Ausfuehrung tragen: it-Beweis ueber neue Flexionsfamilie
(19-02), "befuellt" = languages-Marke (19-03), EIN ungegateter CI-Schritt mit vier
Ergebnisseiten-Abrufen (19-07), AST-Waechter-Ersatz im selben Commit (19-01).

## Performance Metrics

**Velocity:** v1.2 lieferte 63 Plaene in 5 Phasen (8 Tage). Fuer v1.3 noch keine Messwerte.

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

## Accumulated Context

### Entscheidungen, die v1.3 tragen

- Feldliste und Boost-Abbildung einer Anfrage sind EIN Wert (`FieldPlan`), nie zwei
  Konstanten: `parse_query_lenient` wirft die ValueError gemessen auch fuer `field_boosts`
  (19-RESEARCH M-1). Der Vorgabewert von `build_query(plan=...)` ist der eingefrorene
  Bestandsplan und niemals etwas aus `settings()`.

- 19-01 wurde als EIN Commit gefahren statt als drei: die Ratschenregel (Aenderung unter
  backend/src/findling zieht PACKAGE_TREE_HASH_TODAY im selben Commit nach) und die
  Uebergabebedingung aus 18-03 (Waechter faellt und sein Ersatz wird im selben Commit
  genannt) lassen keinen gruenen Zwischenstand zu.

- Der Feldplan haengt an `ReadSide` und bekommt keinen eigenen Prozesscache (19-03): die
  Invalidierung durch `reset_read_side()` und der Generationsschutz aus Audit M-18-02 existieren
  dort bereits, und ein dritter Cache neben `_DEGRADED` und `_FILLED` waere die dritte
  Generationsfalle. Quelle des Plans sind ausschliesslich die zwei gespeicherten Marken
  `schema_version` und `languages`, nie `settings().languages` (T-18-05-01).

- Erfolgskriterium 3 ist belegt, aber nicht weiter als es traegt (19-04): tantivy summiert die
  Feldbeitraege, Boosts daempfen die Summe und beseitigen sie nicht. Gemessen auf der Rangprobe
  kippt der Rang bei einem Zusatzgewicht von 0,81; die ausgelieferten 0,6 liegen 0,21 darunter.
  Diese Zahl ist der Startpunkt fuer den disjunction_max-Entscheid in Phase 22 (MESS-09) und
  gehoert per 19-09 nach docs/language-analyzers.md.

- Ein Sprachfall auf dem normalen Suchweg braucht drei Ketten (19-06): der Fallindex traegt
  den Bestand einer echten Instanz (derselbe Text in body_de, body_en und dem Feld der
  Sprache, so wie index/writer.py schreibt), also beweist ein Formenpaar nur dann etwas,
  wenn die eigene Kette es zusammenfuehrt und die englische UND die deutsche es trennen.
  Ein Index, der nur das Sprachfeld befuellt, macht den Ausschluss folgenlos und den Fall
  wertlos. Wer eine fuenfte Sprache aufnimmt, braucht zuerst eine Flexionsfamilie in der
  Fixture, dann die Messung, dann das Zaehlgate (Weg von 19-02).

- Ein CI-Beweis ueber alle vier Matrixaeste steht in einem Schritt OHNE if-Zeile, und ein
  Textgate haelt das fest (19-07). "Store upgrade 5" und "Store upgrade 6" tragen beide
  matrix.runner == 'ubuntu-24.04' und laufen auf drei von vier Aesten gar nicht; ein
  Beweis dort waere gruen und wuerde ueber arm64 nichts sagen. Das Gate liest die zwei
  gegateten Schritte als Gegenbeispiel mit: verlieren sie ihre if-Zeile, ist das Gate
  kaputt und nicht der Workflow heil. Dazu zwei Regeln, die dieser Schritt vormacht: die
  Vorbedingung (languagesActive) steht VOR der ersten Behauptung, und was ein Beweis in
  die Nutzerablage legt, nimmt er wieder heraus, damit spaetere Zusicherungen ihren
  gemessenen Bestand behalten.

- Ein Term, der vorher NULL antworten soll, bekommt einen eigenen Snapshotschluessel
  (19-08). Die Vorbedingung [.terms[]] | all(. == 1) steht zweimal in deploy-harp.yml und
  verlangt genau eine Datei je Term; sie aufzuweichen, damit ein neuer Term hineinpasst,
  waere der billige Weg und wuerde jede Zusicherung dahinter bedeutungslos machen. Dazu
  zwei Regeln, die dieser Plan vormacht: ein Treffer am Ende einer Strecke ist ohne
  Gegenbeweis am Anfang nicht von der unveraenderten Abwesenheit eines Treffers zu
  unterscheiden, und nennt ein Schrittname eine Zahl von Zusicherungen, wandert die Zahl
  mit der Zusicherung.

- Eine Null in einer hybriden Suche ist nur unter einer Bedingung eine Aussage ueber
  Felder (19-08): api/search.py beantwortet eine EINWOERTIGE Zeile allein aus dem
  Wortindex (lexical_only ... or rewritten.one_term ..., Ein-Term-Regel aus 06.1-20).
  Waere die Vektorseite im Spiel, laege die spanische Datei als naechster Nachbar von
  alemanes unter der Obergrenze 86,5 (docs/measurements/2026-09-06-vektordistanzen:
  einwoertige Proben landen bei 68 bis 77) und die Strecke haette 1, 1, 1 gemessen statt
  0, 0, 1. Wer eine solche Probe je auf zwei Woerter erweitert, verwandelt sie lautlos in
  eine Aussage ueber Distanzen.

- D-04-Linie (v1.1): index-kompatibel ueber Minor-Spruenge. v1.3 verletzt sie bewusst und
  nur fuer Instanzen, die eine neue Sprache einschalten; der Bruch braucht den Owner-Entscheid
  in Phase 17.

- Riskantester Pfad des Milestones: Schema erreicht den Bestandsindex nie, Suche antwortet
  danach dauerhaft leer (`parse_query_lenient`-ValueError zu leerer degraded-Antwort).
  Gegenmassnahme ist die Phasentrennung 18 (Schema und Umbau) gegen 19 (Frageseite).

- Re-Analyse-Umbau statt Vollreindex: geschaetzt 1 bis 3 h gegen gemessene 19 h 20 min.
- Keine Spracherkennung, weder dokument- noch anfrageseitig (Anti-Feature, einstimmig).
  Seit 19-05 strukturell festgehalten statt nur beschlossen: die Funktion, die den Feldplan
  baut, nimmt keinen Parameter entgegen, der ein Anfragetext ist oder einer sein kann, also
  ist eine Erkennung der Anfrage nicht verboten, sondern nicht anschliessbar
  (backend/tests/test_no_language_detection.py, 0b59fca).
- Katalogzahl beim Planstart aus `php/l10n/de.json` ZAEHLEN (Stand Research 199, nicht 174).

### Termine und Owner-Checkpoints

- **Beim Owner offen:** Store-Token-Rotation (apps.nextcloud.com/account/token);
  Outlook-Entwurf an Denny senden; InfraNode ntfy-401-Entscheid.

- **Forum-Post** haengt in der Discourse-Moderation (Konto street1983nk);
  Plan B bei Ablehnung: Antwort im Bestandsthread t/249031.

- **ISV-Nachfass Fabrice Mous:** Wiedervorlage 25.09.2026, dann Nachfass-Entwurf anbieten.
- **Findling-Pro-Entscheid:** vertagt auf 03.11.2026 (Go-Kriterium >=10 Grenzen-Anfragen
  oder 1 Pilotkunde >250 Nutzer; Stand 21.09.: null Signale).

- **Connector Issue #8** (piAreSquare): Community-Beitrag zur geparkten Connector-Spur,
  zeitnah sichten.

- **Korpus-Snapshot** snap-03f1d1d9ad9262704 bleibt im Standard-Tier (~2,85 USD/Monat) und
  wird fuer die Messphase 22 gebraucht; Wiedervorlage beim v1.3-Close.

### Offene Blocker

- Kill-Kriterium: kuendigt Nextcloud eine Elasticsearch-freie Volltextsuche mit OCR an,
  wird das Projekt neu bewertet. Geprueft 21.09.2026: NICHT ausgeloest. Ende September
  einmalig die Conference-Nachberichte ansehen, danach quartalsweise.

### Mitzunehmende Kleinigkeiten

- L-16-04-Kommentarfix beim naechsten Workflow-Plan (paths-Filter gilt nicht fuer
  Tag-Pushes, zwei Workflow-Kommentare berichtigen).

- Systemplatten-Skripte Phasen 5-6.1: Repo-Aufnahme erst nach Geheimnis-Durchsicht.
- Estnischer Stemmer nicht verfuegbar: aktiv an die Buerokratt/OS2ai-Spur kommunizieren.

- Zwei Prosastellen nennen noch den gefallenen Namen `DEFAULT_FIELDS`: `store/repo.py:128`
  und `:1448`. Die beiden Stellen in `tests/test_language_cases_field_level.py` sind am 24.09.
  mit 19-02 erledigt. 19-03 hat `repo.py` bewusst NICHT angefasst: sein Fussabdruck ist auf acht
  Dateien festgelegt und die Verifikation verlangt genau diese acht; `LEGACY_LANGUAGES` wird von
  dort nur importiert. Wartet weiter auf den naechsten Plan, der `store/repo.py` ohnehin oeffnet.

- Der run-Block "Store upgrade 3" in deploy-harp.yml steht bei 20726 Zeichen. GitHub kappt
  einen run-Block bei 21000 Zeichen, aber NUR wenn er einen ${{ }}-Ausdruck traegt, und
  dieser traegt keinen. Wer dort je einen Matrixausdruck hineinschreibt, muss den Block
  vorher kuerzen oder die Werte wie "Store upgrade 6" ueber einen env:-Block hereinreichen.

- Leerer Textauszug bei einem reinen Sprachfeld-Treffer: der `SnippetGenerator` haengt fest an
  `FIELD_BODY_DE` (`index/search.py:875`), gemessen in 19-RESEARCH M-4. Gefuehrt als Annahme A5
  (dokumentieren statt beheben); Doku gehoert zu 19-09, eine Behebung waere ein eigener Plan und
  braucht den Owner-Entscheid, ob es ein Mangel ist.

## Deferred Items

Keine offenen Deferred Items (die drei Debug-Sessions aus v1.1 sind am 21.09.2026 formal
auf resolved gesetzt).

## Session Continuity

Last session: 2026-09-25
Stopped at: 19-08 abgeschlossen und committet (f0ceef6, c5a450c, 8ac2626), SUMMARY geschrieben
Resume file: .planning/phases/19-frageseite-freischalten/19-09-PLAN.md
