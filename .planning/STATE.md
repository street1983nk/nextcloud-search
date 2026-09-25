---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Sprachausbau
status: executing
stopped_at: 20-01 gebaut und committet (51e0ea4, 5389009), BLOCKIERENDER CHECKPOINT: Owner-Sichtprobe des Vorher-Nachher-Belegs steht aus
last_updated: "2026-09-25T05:45:00.000Z"
last_activity: 2026-09-25 -- 20-01 ausgefuehrt, Checkpoint offen
progress:
  total_phases: 7
  completed_phases: 3
  total_plans: 38
  completed_plans: 30
  percent: 43
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-23, Start Milestone v1.3)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 20 (ui-kataloge) laeuft; 20-01 gebaut, wartet auf die Owner-Sichtprobe

## Current Position

Phase: 20 (ui-kataloge-es-it-nl-pt), 1 of 9 gebaut; Phase 19 COMPLETE 25.09.2026
Status: 20-01 (Pluralschluessel-Fix der sechs Bestandskataloge) ist gebaut und committet
(51e0ea4 Scanner, 5389009 Kataloge), aber NICHT abgenommen: der blockierende Checkpoint
Task 3 wartet auf die Owner-Sichtprobe. Alle fuenf Pluralschluessel stehen in de/de_DE/fr
(json und js) jetzt als _<singular>_::_<plural>_, die Zahl 202 ist unveraendert, 5 geaenderte
Zeilen je Datei, kein Baumhash bewegt. Gemessen an der laufenden Instanz: vorher antworteten
de und fr ab n=2 mit "2 days", jetzt mit "2 Tage" und "2 jours" (Vorher-Haelfte neu erhoben
aus den HEAD~1-Bytes unter der Wegwerf-App-ID l10nprobe, beides am 25.09. auf derselben
Nextcloud). Suite 2877 passed / 15 skipped, ruff/pyright/vulture gruen. NICHT gepusht.
KAT-01 bleibt ungehakt: die Anforderung verlangt zehn neue Dateien, nicht die Bestandsreparatur.
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
Last activity: 2026-09-25 -- 20-01 ausgefuehrt, Owner-Checkpoint offen

Progress: [████......] 43% (3 von 7 Phasen)

## Naechster Schritt

**Dem Owner die Sichtprobe von 20-01 vorlegen** (Abschnitt "CHECKPOINT" in
.planning/phases/20-ui-kataloge-es-it-nl-pt/20-01-SUMMARY.md): die sechs Zeilen der
Sondenausgabe und die Frage, ob die Reparatur der bestehenden de/fr-Kataloge gewollt ist.
Antwort "approved" -> pushen und mit 20-02 weiterfahren. Danach die restlichen sieben Plaene
der Phase 20, dann Phase 21 (nl-Komposita, eigenes Tor, streichbar) und Phase 22
(Messanfahrt BL-F03).
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

- **Beim Owner offen (NEU 25.09., blockiert Phase 20):** Sichtprobe zu Plan 20-01. Der
  Pluralschluessel-Fix aendert die BESTEHENDEN deutschen und franzoesischen Kataloge und geht
  damit ueber den Phasenauftrag hinaus; kein Wortlaut ist angefasst, nur der Schluesselname.
  Vorher-Nachher-Beleg und die drei Pruefpunkte stehen in 20-01-SUMMARY.md.

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
Stopped at: 20-01 ausgefuehrt und committet (51e0ea4, 5389009), SUMMARY geschrieben, Gates lokal gruen, NICHT gepusht; angehalten am blockierenden Checkpoint Task 3 (Owner-Sichtprobe des Vorher-Nachher-Belegs)
Resume file: .planning/phases/20-ui-kataloge-es-it-nl-pt/20-01-SUMMARY.md (naechster Schritt: Owner-Antwort einholen, dann pushen und 20-02 starten)
