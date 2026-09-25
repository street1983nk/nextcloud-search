---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Sprachausbau
status: executing
stopped_at: 20-04 gebaut und committet (7dd61fd, c61955d, 64527aa, aa9f36a), Gates lokal gruen, NICHT gepusht
last_updated: "2026-09-25T10:05:00.000Z"
last_activity: 2026-09-25 -- 20-04 ausgefuehrt, Spanisch ausgeliefert
progress:
  total_phases: 7
  completed_phases: 3
  total_plans: 38
  completed_plans: 33
  percent: 45
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-23, Start Milestone v1.3)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 20 (ui-kataloge) laeuft; 20-01 abgenommen, 20-02 bis 20-04 gebaut

## Current Position

Phase: 20 (ui-kataloge-es-it-nl-pt), 4 of 9 gebaut; Phase 19 COMPLETE 25.09.2026
Status: 20-04 (der spanische Katalog) ist gebaut und committet (7dd61fd es.json, c61955d es.js
plus Gate-Eintrag, 64527aa docs/l10n-spanish.md, aa9f36a Rule-3-Fix am Vokabular-Gate).
php/l10n/es.json und es.js fuehren dieselben 202 Schluessel wie de.json, fuenf Pluralwerte mit
drei Formen (Form 1 gleich Form 2), pluralForm mit nplurals=3 zeichengleich aus
docs/l10n-catalogues.md. L10N_CATALOGUES fuehrt jetzt ACHT Eintraege, alle sechs Scanner nehmen
Spanisch mit. VALUES_THAT_MAY_EQUAL_THEIR_KEY["es"] fuehrt ZWEI begruendete Eintraege (Findling,
PDF), gefunden per Lauf mit leerem Mapping und nicht geraten; Page %s, Documents und Images
haben im Spanischen eigene Wortlaute. docs/l10n-spanish.md (409 Zeilen, neun Abschnitte, 202
Tabellenzeilen) traegt den datierten Vorbehalt vom 25.09.2026 mit dem Satz "von keinem
Muttersprachler gelesen". Im Katalog steht KEIN literales Prozentzeichen: der 100-Prozent-Satz
ist zu "el cien por cien" umformuliert. Suite 2879 passed / 15 skipped, ruff/pyright/vulture
gruen. NICHT gepusht.
BEFUND (Rule 3, behoben): das Vokabular-Gate in tests/test_public_artifacts.py haelt eine
Wortstamm-Sperre ueber docs/ und faellt ueber dem spanischen Wort fuer Datei (61 Treffer, alle
dasselbe Wort). Geloest ueber den vorgesehenen AUSNAHMEN-Eintrag mit eigenem Grund, nicht ueber
eine aufgeweichte Regex. MITZUNEHMEN IN 20-05: Italienisch fuehrt dasselbe Wort und braucht
denselben Eintrag; pt und nl nicht.
KAT-01 und KAT-02 bleiben ungehakt (beide umfassen zehn Katalogdateien, zwei stehen).

Vorheriger Stand: 20-03 (sprachunabhaengige Scanner, Prozent- und Pipe-Gate) ist gebaut und committet
(32f6e47 Ausnahmen je Sprachcode, d2ddcb4 die zwei neuen Scanner, 106ce1e Paritaet ueber alle
Kataloge plus Doku-Gate). Sechs Scanner laufen jetzt ueber L10N_CATALOGUES: Prosa,
Schluesselmenge, Vollstaendigkeit, Platzhalterparitaet, Prozentdisziplin, Pipe.
FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY ist VALUES_THAT_MAY_EQUAL_THEIR_KEY je Sprachcode
geworden, scan_french_completeness ist scan_completeness(name, catalogue, exceptions),
language_code_of(path) ist die einzige Zuordnung Datei zu Code, und eine Sprache ohne
Ausnahmeliste faellt mit Namen. Kein Testname und kein Scannername traegt noch einen
Sprachnamen oder eine Zahl, die beim naechsten Katalog falsch wird. Zwei Rot-Beweise gefahren
und zurueckgenommen (Scanner-Rumpf auf return [], fr-Zeile im Doku-Regelblock verfaelscht).
Suite 2879 passed / 15 skipped, ruff/pyright/vulture gruen. NICHT gepusht.
MITGENOMMEN: das Gate fuer die Zeichengleichheit docs/l10n-catalogues.md gegen PLURAL_FORM_OF
steht (test_the_rule_table_of_the_documentation_and_the_constant_are_one_string), der offene
Punkt aus 20-02 ist damit zu.
BEFUND: die Planannahme "kein deutscher Wert gleicht seinem englischen Schluessel" ist falsch,
de/de_DE fuehren vier (Findling, %1$s in %2$s, PDF, Text); sie stehen jetzt begruendet in der
Ausnahmetabelle. Fuer 20-04 bis 20-08: jede neue Sprache braucht dort einen Eintrag, sonst
faellt das Vollstaendigkeitsgate mit ihrem Code.
KAT-01 bleibt ungehakt (umfasst die zehn Katalogdateien selbst).

Vorheriger Stand: 20-02 (Ladepfad-Beweis, Pluralregeln, sprachbewusstes Gate) ist gebaut und committet
(a283b7c docs/l10n-catalogues.md, 1e6881f Gate, 5b78e08 python.yml). Der Ladepfad ist erneut
an der laufenden Instanz gefahren (pt laedt, pt_PT und pt_BR fallen auf en, also zehn Dateien),
die Pluralregeln sind auf NC 34.0.3 UND NC 35.0.0 gelesen und dort zeichengleich, und die
Formenwahl ist gemessen: PHP erreicht Form 2 nie, der Browser waehlt sie bei n=2, also werden
Form 1 und Form 2 wortgleich geschrieben. PLURAL_FORM_OF und FORM_COUNT_OF fuehren acht
Sprachcodes, scan_french_plural_rule ist weg, das Gate laeuft ueber jede vorhandene
php/l10n/<code>.json und nimmt die kommenden selbst mit. php/l10n/** steht in beiden
Pfadlisten von python.yml. Drei Rot-Beweise gefahren und zurueckgenommen. Suite 2877 passed /
15 skipped, ruff/pyright/vulture gruen. NICHT gepusht.
KAT-01 und KAT-02 bleiben ungehakt: beide umfassen die zehn Katalogdateien selbst.
LEHRE: eine PHP-Formenprobe ohne %n misst nichts (L10NString fuellt die Parameterliste nur bei
%n, ohne Parameter gibt der IdentityTranslator die mit Pipe verbundene Kette unveraendert
zurueck). Und die Planannahme "n=0 weicht fuer pt_PT und pt_BR ab" war halb falsch: nur pt_PT
weicht ab, Symfonys pt_BR-Regel behandelt die Null wie den Singular.

Vorheriger Stand: 20-01 (Pluralschluessel-Fix der sechs Bestandskataloge, 51e0ea4 + 5389009)
ist am 25.09.2026 vom Owner abgenommen worden (Antwort "weiter" auf die vorgelegte Sichtprobe).
Alle fuenf Pluralschluessel stehen in de/de_DE/fr (json und js) als _<singular>_::_<plural>_,
die Zahl 202 ist unveraendert, 5 geaenderte Zeilen je Datei, kein Baumhash bewegt.
LEHRE: das Giessrezept der Research schrieb Listenwerte dreizeilig, der Bestand schreibt sie
einzeilig; eine Giessform wird zuerst gegen den unveraenderten Bestand byteweise geprueft,
sonst bewegt der "Fuenf-Zeilen-Fix" 30 Zeilen je Datei.

Vorheriger Stand: Phase 19 KOMPLETT: 9/9 Plaene (Detail in den 19-0N-SUMMARY.md), Verifikation passed
(4/4 Kriterien, fb604bc), LEX-05 abgehakt, Audit 1H/5M behoben + 6/7 LOW gefixt (Bericht
8eac0f4, Fixes 6f35cbe..60dd3f3). Eine Audit-Fix-Regression (M-19-05 nahm einer frischen
Instanz den Erststempel der Verzeichnismarken; Folge: Feldplan blieb LEGACY, roter CI-Lauf
36086044755 auf 4/4) wurde gefunden und mit stamp_a_new_directory behoben (ff0f5cf, Rot-vor-
Fix-Beweis). Endstand-CI 36096526219 GRUEN 4/4 inkl. arm64. Suite 2877 passed / 15 skipped.
LEHRE: ein Audit-Fix, der einen Schreiber entfernt, braucht die Frage "wer schreibt das
sonst noch auf JEDEM Pfad" plus einen Frischinstanz-Fall, bevor er reist.
Last activity: 2026-09-25 -- 20-04 ausgefuehrt, keine offene Owner-Frage in Phase 20

Progress: [████......] 45% (3 von 7 Phasen)

## Naechster Schritt

**20-05 planen und ausfuehren** (Italienisch: zwei Dateien, Eintrag in L10N_CATALOGUES und in
VALUES_THAT_MAY_EQUAL_THEIR_KEY, docs/l10n-italian.md mit datiertem Vorbehalt). Danach 20-06
bis 20-09, dann Phase 21 (nl-Komposita, eigenes Tor, streichbar) und Phase 22 (Messanfahrt
BL-F03).
Mitzunehmen in 20-05 bis 20-08, aus 20-04 gemessen:
1. Jede neue Sprache braucht einen eigenen Eintrag in VALUES_THAT_MAY_EQUAL_THEIR_KEY, sonst
   faellt das Vollstaendigkeitsgate mit dem Sprachcode. Die Liste wird gefunden (Lauf mit
   leerem Mapping) und nicht geraten; fuer es waren es zwei Schluessel, nicht fuenf wie bei fr.
2. Italienisch braucht zusaetzlich einen AUSNAHMEN-Eintrag in tests/test_public_artifacts.py,
   Familie vokabular: das italienische Wort fuer Datei traegt denselben gesperrten Wortstamm
   wie das spanische. Portugiesisch und Niederlaendisch nicht.
3. Die Giessform aus 20-01 zuerst gegen den unveraenderten Bestand pruefen (cast(alt) == alt,
   sechs von sechs), dann erst schreiben. Listenwerte muessen einzeilig gefaltet werden.
4. Ein literales Prozentzeichen wird %% geschrieben, besser noch umformuliert.
Offene Kleinigkeit aus 19: zwei DEFAULT_FIELDS-Prosastellen in
backend/src/findling/store/repo.py Zeilen 128 und 1448 (naechster src-Plan nimmt sie mit).

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

- Ein Pluralschluessel heisst in einem Nextcloud-Katalog `_<singular>_::_<plural>_` und
  niemals blank (20-01). `L10N::n` baut diesen Bezeichner selbst und faellt sonst auf den
  englischen Quellstring zurueck; `@nextcloud/l10n` tut im Browser dasselbe. Findling hat
  die fuenf Schluessel seit dem ersten Katalog blank gefuehrt, gemessen antworteten de und
  fr bis zum 25.09.2026 ab n=2 mit "2 days". Die zehn neuen Kataloge der Plaene 20-04 bis
  20-08 erben dieses Format; wer ihn blank schreibt, liefert eine halb englische Seite aus.
  Zwei Folgeregeln: der Paritaetsscanner muss an der Marke teilen (sonst faellt er falsch
  rot), und die Paare stehen an der Aufrufstelle, nicht im Katalog.

- Eine Regel aus einer fremden Codebasis wird auf JEDER Version des eigenen Versionsfensters
  gelesen (20-02). Die acht pluralForm-Zeichenketten stehen auf NC 34.0.3 und NC 35.0.0
  zeichengleich; dass sie gleich sind, ist ein Ergebnis und keine ausgelassene Frage. Zwei
  Folgeregeln aus demselben Plan: ein Gate leitet seine Erwartung nicht aus der Zeichenkette
  ab, die es prueft (FORM_COUNT_OF steht als eigene Zahl da und wird nicht aus nplurals=
  geparst, sonst baut sich eine falsche Regel ihre eigene Erwartung), und ein sprachgebundener
  Vorwurf wird sprachbewusst, sobald eine zweite Sprache dieselbe Zeichenkette rechtmaessig
  fuehrt (nl traegt die deutsche Regel zu Recht; ein pauschales "traegt die deutsche Regel"
  waere fuer nl dauerhaft rot, und ein rotes Gate, das man zu Recht ignoriert, ist schlimmer
  als kein Gate).

- Ein Pfadfilter, der den Gegenstand eines Gates nicht enthaelt, macht das Gate unfaehig rot zu
  fallen (20-02). python.yml filterte auf backend/**, scripts/**, sich selbst und
  docs/measurements/**; die Katalog-Gates liegen in backend/tests/, ihr Gegenstand in
  php/l10n/. Ein reiner Katalogcommit startete php.yml und integration.yml und kein einziges
  Katalog-Gate. Der Eintrag wird mit einem YAML-Parser geprueft, nicht mit einer Textsuche.

- fr traegt im Gate die AUSGELIEFERTE Regel und nicht die Kernregel (20-02). NC 34 und 35
  fuehren Franzoesisch mit nplurals=3, Findling liefert seit 11-08 zwei Formen, korrekt in
  beiden Haelften und dreimal vom Owner abgenommen. Wer das je angleichen will, aendert
  Wortlaute ohne Nutzen. Genau diese eine Zeile ist der Grund, warum das Gate ein Mapping je
  Sprachcode braucht und keine zwei Konstanten.

- Eine Ausnahmeliste wird gefunden und nicht geraten (20-04). Das Vollstaendigkeitsgate laeuft
  einmal mit leerem Mapping, meldet seine Funde, und jeder gemeldete Schluessel wird einzeln
  beurteilt: gleicher Wortlaut richtig (Eintrag mit Grund) oder vergessener Wortlaut
  (uebersetzen). Fuer Spanisch waren es zwei und nicht die fuenf des Franzoesischen, weil
  Page %s, Documents und Images im Spanischen eigene Woerter haben. Eine Zahl waere hier die
  falsche Groesse gewesen.

- Ein Wortstamm-Gate auf einer Sprache stolpert ueber die Homographen einer anderen (20-04).
  Die Sperre des Vokabular-Gates sucht die deutsche Form eines Begriffs, also den Stamm ohne
  die englische Endung, und das spanische Wort fuer Datei faengt genau damit an; die neue
  Sprachdoku fiel mit 61 Treffern rot, keiner davon die gesuchte Form. Der Ausweg ist der
  benannte Eintrag mit eigenem Grund und ausdruecklich nicht die aufgeweichte Regex: die haette
  auch deutsche Zusammensetzungen verloren, und zwar in allen Dateien. Restrisiko benannt: die
  Ausnahme gilt je Datei und Familie, feiner kann die Liste heute nicht.

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

- **ERLEDIGT 25.09.:** Sichtprobe zu Plan 20-01 vom Owner abgenommen (Antwort "weiter"). Die
  Reparatur der bestehenden de/fr-Kataloge ist freigegeben, Phase 20 laeuft ohne offene
  Owner-Frage weiter. Vermerk in 20-01-SUMMARY.md, Zeile "OWNER-GO 25.09.2026".

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
Stopped at: 20-04 ausgefuehrt und committet (7dd61fd, c61955d, 64527aa, aa9f36a), SUMMARY geschrieben, Gates lokal gruen, NICHT gepusht; kein Checkpoint in diesem Plan
Resume file: .planning/phases/20-ui-kataloge-es-it-nl-pt/20-04-SUMMARY.md (naechster Schritt: 20-05 ausfuehren; der Orchestrator pusht gesammelt)
