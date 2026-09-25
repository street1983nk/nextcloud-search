---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Sprachausbau
status: executing
stopped_at: Phase 19, alle neun Plaene fertig (19-09 Doku und gruener CI-Lauf 36074155306), offen: Phasenverifikation und Audit
last_updated: "2026-09-25T00:40:00.000Z"
last_activity: 2026-09-25 -- 19-09 ausgefuehrt (Doku der Frageseite, CI-Lauf 36074155306 auf allen vier Aesten gruen, Laufzeit 172 s eingetragen)
progress:
  total_phases: 7
  completed_phases: 2
  total_plans: 38
  completed_plans: 29
  percent: 32
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-23, Start Milestone v1.3)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 19 (frageseite-freischalten), alle Plaene ausgefuehrt, Verifikation und Audit offen; Phase 20 geplant

## Current Position

Phase: 19 (frageseite-freischalten), EXECUTING, Plan 9 of 9 ausgefuehrt; Phase 20 (ui-kataloge) geplant, 0 of 9
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
bestanden / 15 uebersprungen. 19-09 fertig (d8cd69a, 4ea3f20, 71cf028, da3858e):
docs/language-analyzers.md traegt den Abschnitt "What a question searches" mit vier
Absaetzen (die gespeicherte languages-Marke entscheidet und nicht die
Umgebungsvariable; die Feldliste haengt am Merker schema_version und das Tor faellt
geschlossen; es gibt keine Spracherkennung, und der Grund, warum keine gebraucht wird,
steht daneben; eine einwoertige Frage wird allein aus dem Wortindex beantwortet), dazu
einen Known-limits-Eintrag zum leeren Textauszug (index/search.py:875, gemessen 24.09.)
und zwei neue Messzahlen (Kippgrenze 0,81 und 0,26 us je doc_freq-Sonde). DER LAUF IST
EINGEHOLT UND GRUEN: 36074155306, alle vier Matrixaeste erfolgreich, der
Sprachbeweisschritt viermal gelaufen und viermal erfolgreich, auf dem arm64-Ast vier
OCS-Treffer und vier Ergebnisseiten-Treffer, und die Kette 0, 0, 1 steht im Protokoll
von Store upgrade 3, 5 und 6. Die gemessene Laufzeit des Sprachbeweises (172 s auf
arm64, 73/41/32 s auf den drei amd64-Aesten) steht als Zahl im Budgetkommentar, das
Budget bleibt unveraendert bei 600. Der erste Lauf (36072411846) war rot und hat einen
echten Fehler gefunden: Store upgrade 4 registrierte die aufgeruestete Haelfte mit der
sechssprachigen Entwicklerdatei aus 19-07, der Container lief also mit sechs Sprachen
gegen ein Volume ohne languages-Marke, die Generation wurde gehoben und drei
D-04-Zusicherungen rissen; der Fix baut info-upgrade.xml mit der ausgelieferten
Vorgabe de,en (71cf028).
Planung 24.09.: Research b2ef69f,
Pattern-Karte, Plaene 51525d5, Checker PASS, Warnungen behoben 3c35186. Phase 20 geplant
(a8d40fd, Checker PASS, f32bdec). Phase 18 davor KOMPLETT (12/12, CI-Beweis 36026836087).
Audit der Phase 19 (19-REVIEW.md, 1H/5M/7L) behoben am 25.09.2026 in 6f35cbe..7f75456:
H-19-01 und alle fuenf MEDIUM gefixt, sechs der sieben LOW gefixt, L-19-05 misst die
Loeschverzoegerung und warnt, statt ohne gemessenes Budget zu gaten, L-19-03 bewusst
abgelehnt mit Begruendung im Code; jeder Befund ein eigener Commit mit nachgezogener
Ratsche, Gates und volle Suite (2875/15) vor jedem Commit gruen, nichts gepusht.
Regression aus dem Audit-Erstfix 252ada4 (M-19-05) behoben in ff0f5cf: seitdem stempelte auf
einer frischen Instanz niemand mehr die Marken schema_version und languages, der Feldplan fiel
dauerhaft auf de,en zurueck und die CI-Strecke "Language proof" war in Lauf 36086044755 auf
allen vier Aesten rot; der Erststempel steht jetzt in index/open.py::stamp_a_new_directory vor
der Erzeugung des Verzeichnisses, zwei neue Faelle halten ihn fest, Suite 2877/15 gruen.
Last activity: 2026-09-25 -- Audit-Befunde der Phase 19 behoben (6f35cbe..7f75456, 8 Commits)

Progress: [███.......] 32% (2 von 7 Phasen)

## Naechster Schritt

Phase 19 ist gebaut: alle neun Plaene ausgefuehrt, der Beweis eingeholt. Der Audit nach
der Owner-Regel vom 15.08.2026 ist gefahren UND behoben (19-REVIEW.md, Commits
6f35cbe..7f75456); offen ist daraus nur der Nachlauf der CI (Push steht aus) und die
PHP-Seite von M-19-03, die in den Plan gehoert, der die Adminseite besitzt (Phase 20).
Der letzte offene Abschlussschritt ist damit die Phasenverifikation
(`/gsd:verify-phase 19`); sie hat alles, was sie braucht: Laufnummer
36074155306, vier gruene Aeste (stable33/amd64, stable34/amd64, stable34/arm64,
stable35/amd64), der Sprachbeweis viermal erschienen und viermal erfolgreich, die
Kette 0, 0, 1 in Store upgrade 3, 5 und 6.
Der REQUIREMENTS-Haken fuer LEX-05 ist weiterhin NICHT gesetzt, und das ist kein
Versehen: die Traceability-Tabelle haekt eine Anforderung bei der Phasenverifikation
mit Laufnummer ab (so stehen LEX-02 bis LEX-08 dort, alle mit CI 36026836087).
Inhaltlich ist LEX-05 vollstaendig, denn 19-09 hat die letzte offene Bedingung, den
gruenen Lauf, geliefert.
Die vier Nachtraege aus 19-07 und 19-08 sind ALLE erledigt: die gemessene Laufzeit
steht im Budgetkommentar (da3858e); der Parameter query statt term ist in
19-RESEARCH.md als datierter Vermerk berichtigt (4ea3f20), waehrend 19-07-PLAN.md
bewusst unberuehrt bleibt, weil ein Plan ein historisches Artefakt ist und der Fund in
19-07-SUMMARY steht; der leere Textauszug steht unter Known limits; und die
Ein-Wort-Bedingung steht als vierter Absatz des neuen Abschnitts.
Danach oder parallel: `/gsd:execute-phase 20` (UI-Kataloge; Wellen 1 und 9 sind
Checkpoints, 20-01 Pluralfix der sechs Bestandskataloge braucht die Owner-Sichtprobe).
Phase-20-Planung 24.09.: 9 Plaene in 9 Wellen (a8d40fd), Checker PASS, Fussabdruck
strikt getrennt von Phase 19 (php/l10n/**, test_admin_ui_contract.py, docs/l10n-*.md,
python.yml + integration.yml). Groesster Research-Fund: Pluralschluessel aller sechs
Bestandskataloge im falschen Format (de/fr antworten bei n=2 mit "2 days"), Fix ist
Welle 1.
Entscheide der Planung, die die Ausfuehrung getragen haben: it-Beweis ueber neue
Flexionsfamilie (19-02), "befuellt" = languages-Marke (19-03), EIN ungegateter
CI-Schritt mit vier Ergebnisseiten-Abrufen (19-07), AST-Waechter-Ersatz im selben
Commit (19-01).

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

- Eine Beweisdatei, die eine Strecke fuer sich baut, wird von einer anderen Strecke
  mitbenutzt (19-09). Plan 19-07 setzte die Sprachvorgabe in der temporaeren
  info-citest.xml der Entwicklerstrecke, und "Store upgrade 4" registriert die
  aufgeruestete Haelfte mit derselben Datei: der aufgeruestete Container lief mit sechs
  Sprachen gegen ein Volume ohne languages-Marke, die Generation wurde gehoben und drei
  D-04-Zusicherungen rissen (Lauf 36072411846). Der Container hat sich richtig
  verhalten, die Beweisstrecke hat die falsche Frage gestellt. Zwei Regeln daraus: wer
  eine gemeinsam genutzte Datei aendert, sucht ihre Leser (grep -n info-citest.xml)
  statt sich zu erinnern, und ein Lauf, der auf drei von vier Aesten gruen ist, kann
  trotzdem eine tragende Zusage reissen, weil die tragenden Zusagen auf genau einem
  Ast stehen.

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
  (dokumentieren statt beheben). Die Doku ist mit 19-09 geschrieben (docs/language-analyzers.md,
  Known limits); eine Behebung waere ein eigener Plan und braucht den Owner-Entscheid, ob es ein
  Mangel ist. Phase 23 nimmt den Punkt in die veroeffentlichte Grenzenliste (REL-03 Kriterium 2).

## Deferred Items

Keine offenen Deferred Items (die drei Debug-Sessions aus v1.1 sind am 21.09.2026 formal
auf resolved gesetzt).

## Session Continuity

Last session: 2026-09-25
Stopped at: 19-09 abgeschlossen und committet (d8cd69a, 4ea3f20, 71cf028, da3858e), SUMMARY geschrieben, CI-Lauf 36074155306 gruen auf 4/4, alles gepusht
Resume file: .planning/phases/19-frageseite-freischalten/19-09-SUMMARY.md (naechster Schritt: Verifikation und Audit der Phase 19)
