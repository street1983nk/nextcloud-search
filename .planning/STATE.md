---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Sprachausbau
status: planning
stopped_at: Phase 22 context gathered
last_updated: "2026-09-25T20:07:59.133Z"
last_activity: 2026-09-25
progress:
  total_phases: 7
  completed_phases: 5
  total_plans: 47
  completed_plans: 47
  percent: 71
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-23, Start Milestone v1.3)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 22, Messanfahrt BL-F03 (vorher secure-phase 21)

## Current Position

Phase: 22
Plan: Not started
Status: Ready to plan (secure-phase 21 ERLEDIGT 25.09., SECURED 32/32, de8e128)

Aktueller Stand: PHASE 21 KOMPLETT 25.09.2026 (9/9 Plaene, goal-backward verified passed 9/9,
phase.complete gelaufen, STATE von Hand nachgezogen). Niederlaendische Komposita sind Ende-zu-
Ende verdrahtet: wdutch 1:2.20.19+1-3 gepinnt im Abbild (CC-BY-3.0 in THIRD-PARTY.md, vier
Abbildpruefungen in docker.yml), wordlist_nl.py mit Rezept B 4-14 (Faltung vor Zerlegung,
Fugenlaute s/e/en, fail-closed ueber Digest, nur Digest im Speicher), Splitterkette hinter der
Faltung mit Cache und Lock, siebte Marke wordlist_hash_nl in Store und Index-Tier (nie
vorbelegt, nur hinter Verzeichnistausch), Band-Umbau beantwortet jede nl-Drift OHNE Vollreindex
(D-08: fullreindex-Ausweg stempelt nicht; Poller-Fix answered_elsewhere nach Owner-Entscheid,
CI-Zusicherung 8 auf "keine Drift-Zeile" umgestellt), alle Aufrufer uebergeben die Marke
ausdruecklich (AST-Gates mit Gegenprobe), index_status meldet wordlistHashNl, Messwerkzeug
scripts/dev/measure_compounds_nl.sh reproduziert die Researchzahlen exakt (316.740 Eintraege,
21/28 Komposita ueber ihr Glied, 32/33 Waechter). CI-Sprachbeweis Fall nlc
(gemeentebelastingen/belasting) GRUEN auf allen vier Matrixzeilen, Store upgrade 5 "all seven
assurances hold" (D-09 in CI belegt). Push d074075..3563715, fuenf CI-Laeufe gruen
(36157139922 HaRP deploy, 36157139819, 36157139949, 36157139966, 36157140005).
Code-Review 1C/2W/5I: CR-01 (UnicodeDecodeError vor Digest-Vergleich, Container-Startschleife)
GEFIXT inkl. deutschem Zwilling wordlist.py, WR-01 (Lock um Automaten-Cache, Thread-Test)
GEFIXT, WR-02 (Band-Rebuild auch im enabled_handler) GEFIXT, IN-02/03 mitgenommen, IN-01
bewusst teilweise (voller Fix braeuchte eigenen Driftnamen, der keinen Rebuild ausloest),
IN-04/05 dokumentiert offen. Suite nach Fixes 2985 passed / 15 skipped, alle Gates gruen.
Review-Fixes und Abschluss-Doku sind NOCH NICHT gepusht (Push d074075..3563715 war der
Owner-Checkpoint; die Fix-Commits 24c33fa..66c2ade plus Tracking liegen lokal).
RAM-BEFUND 21-04: zweiter Automat kostet produktnah 24,2-25,3 MB statt 17,6 MB der Research
(glibc gibt freigegebenen Speicher nicht zurueck); Budget haelt: 1.838,0 gegen 2.000 MB,
Reserve 162 MB; performance.md nennt den produktnahen Wert. Offener Doku-Befund: Messbericht
21-04 Abschnitt 4.3 nennt 41,9 MB fuer den deutschen Automaten, Quelle grundlast-fein sagt
42,1 MB; performance.md zitiert korrekt 42,1.

Vorheriger Stand (20-09): Schritt "The result page answers in every new language (core lang)" im Job search-parity,
530bb7c docs/l10n-catalogues.md Abschnitt "Stand nach Phase 20", c5102d1 SUMMARY). Der Schritt
liest den Erwartungswert zur Laufzeit aus apps/findling/l10n/<code>.json, prueft je Code es, it,
nl, pt_PT, pt_BR Anwesenheit des uebersetzten Titels UND Abwesenheit von "Search your file
contents", setzt die Nutzersprache per trap zurueck. ERSTER ECHTER LAUF GRUEN (Push d52d2e5, Run 36126493024, Beleg in 20-09-SUMMARY.md nachgetragen). Sichtprobe per
Playwright an findling-nextcloud: fuenf Sprachen, Adminseite plus drei Ergebnisseiten, 0
englische Reste aus Findling, Pluralform bei n=16 sichtbar, en-Gegenprobe 37 Funde; Owner
"approved" 25.09.2026. Ausgangswert admin=de, testuser=de wiederhergestellt, git status leer.
Instanz-Eingriffe: occ upgrade (Findling 1.1.0 auf 1.2.0, stand seit 21.09. aus) und Backend
per register-exapp.sh neu gestartet. Suite nach Review-Fixes 2881 passed / 15 skipped, Gates gruen. Gepusht bis 9e5d0eb, alle 11 CI-Laeufe beider Pushes gruen. Code-Review 0C/3W/3I, WR-01..03 gefixt (cde0aab, 245f020, 69c7186), IN-01..03 dokumentiert offen.

Vorheriger Stand: 20-08 (der brasilianisch-portugiesische Katalog) ist gebaut und committet (592980d
pt_BR.json plus pt_BR.js, f79254c Gate, cd38e2d docs/l10n-portuguese.md, ca4f6a9 SUMMARY).
Eigene Wortlaute statt Kopie: arquivo, usuario, tela, senha, lixeira, planilhas, conteiner,
Gerundium; run = a execucao, worker = o processo de indexacao (anders als pt_PT). 72 von 202
Werten gleich pt_PT, keiner kuenstlich verschieden. Pluralwerte drei Formen, Form 1 gleich
Form 2, NICHT die Millionenform der Kerndatei. L10N_CATALOGUES fuehrt SECHZEHN Eintraege.
VALUES_THAT_MAY_EQUAL_THEIR_KEY["pt_BR"] gemessen: Findling, PDF. NEU:
PORTUGUESE_WORDINGS_THAT_MUST_DIFFER (elf Schluessel mit Wortpaar), scan_named_difference,
test_the_two_portuguese_catalogues_are_two; Gegenprobe mit pt_PT-Kopie = elf Funde. Kein
Textgleichheits-Gate. Docstring-Absatz zum Sprung von sechs auf sechzehn Katalogen. Doku
vierspaltig mit zweitem datierten Vorbehalt (20-08), der aus 20-07 unveraendert. Vokabular-Gate
ueber der Doku gruen (Prognose bestaetigt). Suite 2880 passed / 15 skipped, ruff/pyright/vulture
gruen. KAT-01 und KAT-02 ABGEHAKT (alle zehn Dateien stehen). NICHT gepusht.

Vorheriger Stand: 20-07 (der europaeisch-portugiesische Katalog) ist gebaut und committet (e3fc290
pt_PT.json plus pt_PT.js, 2824a4b Gate-Eintrag, 7ae78d6 docs/l10n-portuguese.md). DREI Commits,
wie bei Niederlaendisch: der Rule-3-Fix am Vokabular-Gate war wieder nicht noetig.
php/l10n/pt_PT.json und pt_PT.js fuehren dieselben 202 Schluessel wie de.json, fuenf Pluralwerte
mit DREI Formen (Form 1 gleich Form 2), pluralForm
nplurals=3; plural=(n == 0 || n == 1) ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;
zeichengleich aus docs/l10n-catalogues.md. L10N_CATALOGUES fuehrt jetzt VIERZEHN Eintraege.
VALUES_THAT_MAY_EQUAL_THEIR_KEY["pt_PT"] fuehrt ZWEI begruendete Eintraege (Findling, PDF),
gemessen per Lauf mit leerem Mapping: vier Funde, zwei Schluessel ueber zwei Dateien. Das ist
die KUERZESTE Liste des Baums, gleichauf mit Spanisch; %1$s in %2$s faellt weg, weil das
Portugiesische em schreibt, und Spreadsheets faellt weg, weil es folhas de calculo heisst.
docs/l10n-portuguese.md (566 Zeilen, neun Abschnitte PLUS "Was diese Kataloge nicht leisten",
202 Tabellenzeilen in drei Spalten) traegt den datierten Vorbehalt vom 25.09.2026 mit dem Satz
"von keinem Muttersprachler gelesen". Es gibt KEINE php/l10n/pt.json und keine pt.js, und es
gibt KEIN Textgleichheits-Gate pt_PT gegen pt_BR. Das Gate hat KEINE Logikaenderung gebraucht:
56 Zufuegungen, 0 Loeschungen (it 39, nl 55, pt_PT 56; der Unterschied ist jedes Mal der
Begruendungsabsatz). Suite 2879 passed / 15 skipped, ruff/pyright/vulture gruen. NICHT gepusht.
BEFUND 1: die schaerfere Gegenprobe des Pluralregel-Scanners ist gefahren. pt_PT mit der
SPANISCHEN Regel liefert einen Fund, obwohl sich die beiden Regeln nur im Vorderzweig
unterscheiden (n == 1 ? 0 gegen (n == 0 || n == 1) ? 0). Das ist der wahrscheinliche Fehler,
nicht die deutsche Regel, und das Gate faengt ihn.
BEFUND 2: das Vokabular-Gate faellt ueber docs/l10n-portuguese.md NICHT (0 Stammtreffer), wie
bei nl und anders als bei es (61) und it (9). Das Portugiesische schreibt Datei als ficheiro
und Speicherort als armazenamento. Die Prognose aus 20-04 stimmt damit zweimal in Folge. Fuer
pt_BR in 20-08 lautet sie ebenfalls "kein Treffer" (arquivo faengt mit arqu an), und das ist
eine NEUE Prognose, die gemessen gehoert.
BEFUND 3: zwei der vier Varietaetsproben aus dem Plan (ecra, a transferir) haben in diesem
Katalog keinen Gegenstand, weil kein Schluessel von einem Bildschirm oder einem laufenden
Download spricht. Die Doku sagt das mit gezaehlten Werten, statt eine Pruefung vorzutaeuschen;
ficheiro steht 56 mal, utilizador 1 mal, arquivo/usuario/tela je 0 mal.
KAT-01 und KAT-02 bleiben ungehakt (beide umfassen zehn Katalogdateien, acht stehen).

Vorheriger Stand: 20-06 (der niederlaendische Katalog) ist gebaut und committet (3f76cdc nl.json plus
nl.js, e7ed056 Gate-Eintrag, d40e335 docs/l10n-dutch.md). DREI Commits statt vier: der
Rule-3-Fix am Vokabular-Gate, den 20-04 und 20-05 brauchten, war hier nicht noetig.
php/l10n/nl.json und nl.js fuehren dieselben 202 Schluessel wie de.json, fuenf Pluralwerte mit
ZWEI Formen (nicht drei wie es/it), pluralForm nplurals=2; plural=(n != 1); zeichengleich aus
docs/l10n-catalogues.md und zeichengleich mit der deutschen Regel. L10N_CATALOGUES fuehrt jetzt
ZWOELF Eintraege. VALUES_THAT_MAY_EQUAL_THEIR_KEY["nl"] fuehrt VIER begruendete Eintraege
(Findling, %1$s in %2$s, PDF und Spreadsheets), gemessen per Lauf mit leerem Mapping: acht
Funde, vier Schluessel ueber zwei Dateien. Spreadsheets ist der Eintrag, den weder Spanisch
noch Italienisch hat. docs/l10n-dutch.md (534 Zeilen, neun Abschnitte, 202 Tabellenzeilen)
traegt den datierten Vorbehalt vom 25.09.2026 mit dem Satz "von keinem Muttersprachler
gelesen". Das Gate hat KEINE Logikaenderung gebraucht: 55 Zufuegungen, 0 Loeschungen (mehr als
die 39 bei Italienisch, und der Unterschied ist vollstaendig der Begruendungsabsatz). Suite
2879 passed / 15 skipped, ruff/pyright/vulture gruen. NICHT gepusht.
BEFUND 1: die gestellte Gegenprobe aus 20-02 ist eingeloest, und zwar ueber eine Sprache, die
es jetzt wirklich gibt. scan_plural_rule("nl.json","nl",GERMAN_PLURAL_FORM) liefert [],
dieselbe Zeichenkette fuer es liefert zwei Funde, und eine FREMDE Regel fuer nl liefert weiter
einen Fund: das Gate ist fuer nl nicht blind geworden.
BEFUND 2: das Vokabular-Gate faellt ueber docs/l10n-dutch.md NICHT (0 Stammtreffer), anders als
bei Spanisch (61) und Italienisch (9). Das Niederlaendische schreibt Datei als bestand und
Speicherort als opslag. Die Prognose aus 20-04 stimmte fuer nl; gemessen wurde sie trotzdem.
Fuer pt in 20-07 lautet sie weiter "kein Treffer", Stand: einmal bestaetigt, zweimal knapp
daneben.
BEFUND 3: zwei niederlaendische Pluralwerte tragen zweimal denselben Wortlaut (%n uur und
en nog %n). Das ist korrekt und kein Kopierfehler: Massangaben bleiben nach einem Zahlwort im
Singular (twee uur), und der zweite Satz traegt kein beugbares Hauptwort.
KAT-01 und KAT-02 blieben dort ungehakt (beide umfassen zehn Katalogdateien, sechs standen).

Vorheriger Stand: 20-05 (der italienische Katalog) ist gebaut und committet (ecf8bd2 it.json plus it.js,
fff9aba Gate-Eintrag, e6185c9 docs/l10n-italian.md, 42f6add Rule-3-Fix am Vokabular-Gate).
php/l10n/it.json und it.js fuehren dieselben 202 Schluessel wie de.json, fuenf Pluralwerte mit
drei Formen (Form 1 gleich Form 2), pluralForm mit nplurals=3 zeichengleich aus
docs/l10n-catalogues.md und zeichengleich mit der spanischen Regel. L10N_CATALOGUES fuehrt
jetzt ZEHN Eintraege. VALUES_THAT_MAY_EQUAL_THEIR_KEY["it"] fuehrt DREI begruendete Eintraege
(Findling, PDF und %1$s in %2$s), gemessen per Lauf mit leerem Mapping: einer mehr als
Spanisch, weil das Italienische dieselbe Praeposition schreibt wie das Englische.
docs/l10n-italian.md (477 Zeilen, neun Abschnitte, 202 Tabellenzeilen) traegt den datierten
Vorbehalt vom 25.09.2026 mit dem Satz "von keinem Muttersprachler gelesen". Das Gate hat KEINE
Logikaenderung gebraucht: 39 Zufuegungen, 0 Loeschungen. Suite 2879 passed / 15 skipped,
ruff/pyright/vulture gruen. NICHT gepusht.
BEFUND 1 (Rule 3): eine alleinstehende <code>.json macht die Suite kaputt, nicht nur rot. Das
Pluralregel-Gate liest zu jeder vorhandenen .json die .js unbedingt und faellt mit
FileNotFoundError. Deshalb stehen it.json und it.js in EINEM Commit; der Gate-Eintrag bleibt
ein eigener. MITZUNEHMEN IN 20-06 BIS 20-08: derselbe Commit-Zuschnitt.
BEFUND 2 (Rule 3, behoben): das Vokabular-Gate fiel auch ueber der italienischen Doku, aber
ueber einem ANDEREN Wort als vorhergesagt: nicht ueber dem Wort fuer Datei (das Italienische
benutzt dort das englische Wort), sondern ueber dem fuer den Speicherort, neun Treffer. Ein
zehnter Treffer war die echte deutsche Form in einer Erklaerzeile und ist umformuliert und
nicht mitentschuldigt worden. MITZUNEHMEN: das Gate laufen lassen und die Treffer lesen, statt
der Prognose der Vorgaengersprache zu glauben; sie ging zweimal knapp daneben.

Vorheriger Stand: 20-04 (der spanische Katalog) ist gebaut und committet (7dd61fd es.json, c61955d es.js
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
Last activity: 2026-09-25

Progress: [███████...] 71% (5 von 7 Phasen)

## Naechster Schritt

**discuss/plan-phase 22** (secure-phase 21 ERLEDIGT 25.09.: SECURED 32/32, drei
akzeptierte Restrisiken AR-21-01..03, Commit de8e128; alle Phase-21-Commits gepusht)
(Messanfahrt BL-F03; beim Planen die Mitmessliste aus
.planning/research/BL-F04-vorarbeit-2026-09-25.md einarbeiten plus Rechenblatt der
Boxstunden VOR Start, Owner-Beschluss 25.09.). Phase 21 ist KOMPLETT: Verifikation passed
9/9, Review 1C/2W gefixt, CI-Beweis nlc und Store upgrade 5 gruen.
Die Bloecke darunter sind Herleitung.

Vorher: **20-09 ausfuehren** (CI-Sprachbeweis je Code in integration.yml, Sichtprobe in fuenf
Sprachen als Checkpoint, Schlussabschnitt).

Vorher: **20-08 ausfuehren** (brasilianisches Portugiesisch: pt_BR.json und pt_BR.js als EIGENE
Wortlaute und ausdruecklich KEINE Kopie von pt_PT, Eintrag in L10N_CATALOGUES und in
VALUES_THAT_MAY_EQUAL_THEIR_KEY, das UNTERSCHIEDS-Gate ueber die benannten Woerter statt eines
Textgleichheits-Gates, und die Spalte PT_BR in docs/l10n-portuguese.md, die die Tabelle von drei
auf vier Spalten hebt). Danach 20-09, dann Phase 21 (nl-Komposita, eigenes Tor, streichbar) und
Phase 22 (Messanfahrt BL-F03).
Mitzunehmen in 20-08, aus 20-04 bis 20-07 gemessen:

1. Die .json und die .js einer Sprache gehoeren in EINEN Commit. Das Pluralregel-Gate liest zu
   jeder vorhandenen php/l10n/<code>.json die zugehoerige .js unbedingt; eine alleinstehende
   .json faellt mit FileNotFoundError, also ist der Zwischenstand keine halbe Arbeit, sondern
   eine kaputte Suite. Der Gate-Eintrag bleibt ein eigener Commit. In 20-07 ist das erneut
   nachgefahren worden (pt_PT.js beiseitegelegt, Absturz reproduziert, Datei zurueckgelegt).

2. Jede neue Sprache braucht einen eigenen Eintrag in VALUES_THAT_MAY_EQUAL_THEIR_KEY, sonst
   faellt das Vollstaendigkeitsgate mit dem Sprachcode. Die Liste wird gefunden (Lauf mit
   leerem Mapping) und nicht geraten; es hatte zwei Schluessel, pt_PT zwei, it drei, nl vier,
   fr fuenf. Bei nl kam Spreadsheets dazu, und zwar NICHT bei den Woertern, bei denen man es
   erwartet haette (file heisst bestand, folder heisst map): die Groesse war vorhersagbar, der
   Schluessel nicht. Bei pt_PT faellt %1$s in %2$s weg, weil das Portugiesische em schreibt.

3. Beim Vokabular-Gate in tests/test_public_artifacts.py wird gemessen und nicht prognostiziert.
   Die Vorhersage aus 20-04 stimmte fuer it in der Wirkung, aber im falschen Wort, und fuer nl
   und pt_PT ganz (je 0 Treffer, kein AUSNAHMEN-Eintrag noetig). Fuer pt_BR lautet die Prognose
   ebenfalls "kein Treffer", weil arquivo mit arqu anfaengt; Stand: zweimal bestaetigt, zweimal
   knapp daneben.

4. Ein echter Treffer der gesperrten deutschen Form wird umformuliert und nie mit dem
   Dateieintrag mitentschuldigt: die Ausnahme gilt je Datei und deckt sonst genau den Fehler,
   den die Familie fangen soll.

5. Die Giessform aus 20-01 zuerst gegen den unveraenderten Bestand pruefen (cast(alt) == alt,
   inzwischen zwoelf von zwoelf), dann erst schreiben. Listenwerte muessen einzeilig gefaltet
   werden; der erste Anlauf in 20-07 lief mit null von zwoelf, genau daran. Das Giessskript
   bleibt ausserhalb des Arbeitsbaums.

6. Ein literales Prozentzeichen wird %% geschrieben, besser noch umformuliert.
7. Fuer 20-08 eigens: es gibt KEIN Textgleichheits-Gate pt_PT gegen pt_BR, und der
   Kommentarabsatz ueber L10N_PT_PT_JSON sagt das ausdruecklich. Das Gegenstueck ist ein Gate
   ueber die BENANNTEN Unterschiede. Zwei der vier Probewoerter des Plans (ecra gegen tela,
   a transferir gegen baixando) kommen im Katalog gar nicht vor; ein Unterschieds-Gate, das
   sie prueft, prueft nichts. Tragfaehig sind ficheiro gegen arquivo (56 Stellen), utilizador
   gegen usuario (1 Stelle) und die fuenf weiteren Varietaetswoerter, die 20-07 aufgenommen
   hat: palavra-passe gegen senha, reciclagem gegen lixeira, registo gegen registro,
   folhas de calculo gegen planilhas, texto integral gegen texto completo.
Offene Kleinigkeit aus 19: zwei DEFAULT_FIELDS-Prosastellen in
backend/src/findling/store/repo.py Zeilen 128 und 1448 (naechster src-Plan nimmt sie mit).

## Performance Metrics

**Velocity:** v1.2 lieferte 63 Plaene in 5 Phasen (8 Tage). Fuer v1.3 noch keine Messwerte.

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 20 | 9 | - | - |
| 21 | 9 | 1 Tag | - |

## Accumulated Context

### Entscheidungen, die v1.3 tragen

- Ein CI-Sprachbeweis liest seinen Erwartungswert aus dem Katalog und traegt die Abwesenheit
  des englischen Quellsatzes als eigentliche Zusicherung (20-09). Ein Satz in der YAML waere
  eine Behauptung ueber den Wortlaut von gestern; ein Katalog, der nur halb geladen wird, faellt
  erst an der Abwesenheitspruefung. Geteilter Instanzzustand (Nutzersprache) wird per trap
  zurueckgesetzt, und eine Rest-Suche bekommt eine en-Gegenprobe, sonst beweist ihre Null nichts.

- Zwei Varietaeten werden durch ein POSITIVES Gate zwei gehalten (20-08):
  PORTUGUESE_WORDINGS_THAT_MUST_DIFFER nennt elf Schluessel mit Wortpaar, statt einer
  Mindestzahl unterschiedlicher Werte (mit Zufallsabweichungen erfuellbar) und statt eines
  Textgleichheits-Gates (wuerde eine Varietaet einfrieren). Ein Listenschluessel, der in einem
  Katalog fehlt, ist selbst ein Fund.

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

- Ein Katalogpaar ist ein Commit und nicht zwei (20-05). Das Pluralregel-Gate laeuft ueber die
  Codes von PLURAL_FORM_OF, die heute eine .json haben, und liest zu jedem die .js unbedingt.
  Eine alleinstehende it.json bringt es nicht rot zum Fallen, sondern zum Absturz
  (FileNotFoundError, 1 failed / 51 passed). Plan 20-04 hat diesen Zwischenstand committet, hier
  ist er vermieden. Die Alternative, das Gate an den Zwischenstand anzupassen, waere die
  Logikaenderung gewesen, die dieser Plan gerade beweisen sollte nicht zu brauchen.

- Eine Parametrisierung ist erst bewiesen, wenn eine zweite neue Sprache sie nicht anfasst
  (20-05). Der Gate-Diff fuer Italienisch zeigt 39 Zufuegungen und 0 Loeschungen, verteilt auf
  Konstantenpaar, Tupel-Eintrag und Ausnahmeliste; kein Scanner, kein Testrumpf, keine Zahl im
  Testnamen. Das ist die Zahl, an der 20-06 bis 20-08 sich messen lassen muessen.

- Die Anrede einer Uebersetzung folgt Zeile fuer Zeile der Quelle (20-05). Der deutsche Katalog
  wechselt zwischen Infinitivanweisung und Sie-Form; das Italienische kann beides, also wechselt
  es mit. So bleibt der Wechsel eine Eigenschaft der Quelle statt eine Nachlaessigkeit der
  Uebersetzung, und wer ihn vereinheitlichen will, findet die Stellen im deutschen Katalog.

- Eine gestellte Gegenprobe wird eingeloest, sobald es die Sprache gibt, fuer die sie gestellt
  wurde (20-06). 20-02 hat scan_plural_rule sprachbewusst gemacht, weil nl die deutsche
  Regelzeichenkette zu Recht fuehrt; der Beleg dafuer war bis 20-06 ein Testrumpf ohne Datei.
  Jetzt steht der Dreifachaufruf: nl mit der deutschen Zeichenkette liefert [], es mit
  derselben liefert zwei Funde, und nl mit einer FREMDEN Regel liefert weiter einen Fund. Die
  dritte Zeile ist die tragende: ein Gate, das fuer eine Sprache blind geworden waere, haette
  dieselbe erste Zeile geliefert.

- Ein Sonderfall, der wie ein Fehler aussieht, steht an beiden Orten, an denen ihn jemand
  dafuer halten koennte (20-06): im Kommentarabsatz des Gates und in der Sprachdoku, jeweils
  mit der ausdruecklichen Bitte, den Scanner nicht zu reparieren. Der Absatz ist der Grund,
  warum der nl-Gate-Diff 55 Zeilen hat und der it-Diff 39; die Parametrisierung selbst ist bei
  beiden unberuehrt geblieben, und nl war die erste neue Sprache mit abweichender Formenzahl.

- Zwei gleiche Formen in einem Pluralwert koennen die richtige Uebersetzung sein (20-06).
  %n uur steht im Niederlaendischen zweimal gleich, weil Massangaben nach einem Zahlwort im
  Singular bleiben (twee uur, drie kilometer); bei minuut und dag gilt das nicht. Wer so etwas
  fuer einen Kopierfehler haelt, "repariert" eine korrekte Zeile.

- Eine Datei, die jedes Gate passiert und die niemand laedt, wird nicht gebaut (20-07). Der
  Kern kennt den Code pt nicht, getL10nFilesForApp kuerzt pt_PT nicht auf pt, und ein Nutzer
  kann auf pt nicht stehen; eine php/l10n/pt.json waere deshalb Arbeit ohne Leser. Das Verbot
  ist ein Abnahmekriterium und kein Hinweis, und der gemessene Grund steht an beiden Orten, an
  denen jemand ihn suchen wuerde: docs/l10n-catalogues.md Abschnitt 1 und der Kommentarabsatz
  ueber L10N_PT_PT_JSON.

- Ein Codepaar kann zwei Wortlautsaetze tragen statt zweimal denselben (20-07). pt_PT und
  pt_BR sind das ausdrueckliche Gegenteil von de und de_DE, deren Textgleichheit ein Gate
  haelt. Ein Textgleichheits-Gate fuer das portugiesische Paar wird deshalb NICHT gebaut; es
  wuerde eine der beiden Varietaeten dauerhaft in den falschen Woertern festhalten. Das
  positive Gegenstueck ist ein Gate ueber die benannten Unterschiede und gehoert zu 20-08,
  wenn die zweite Datei existiert.

- Eine Gegenprobe wird mit der AEHNLICHSTEN fremden Regel gefahren und nicht mit der
  auffaelligsten (20-07). Fuer nl war die deutsche Zeichenkette die richtige Probe, weil nl
  sie zu Recht fuehrt; fuer pt_PT ist es die spanische, die sich nur im Vorderzweig
  unterscheidet (n == 1 ? 0 gegen (n == 0 || n == 1) ? 0) und beide Male nplurals=3 mit
  derselben Millionenklausel traegt. Gemessen: ein Fund. Das ist der wahrscheinliche Fehler,
  und ein Gate, das nur grobe Unterschiede findet, haette ihn durchgelassen.

- Eine Probe, die im Gegenstand keinen Gegenstand hat, wird als solche benannt (20-07). Zwei
  der vier Varietaetsproben des Plans (ecra, a transferir) kommen im Katalog nicht vor, weil
  kein Schluessel von einem Bildschirm oder einem Download spricht. Die Doku zaehlt die Werte
  aus (56, 1, kommt nicht vor, kommt nicht vor), statt vier Pruefungen zu behaupten, von denen
  zwei leerlaufen. Die Wortwahltabelle nennt die beiden Woerter trotzdem, damit der naechste
  solche Schluessel nicht in der falschen Varietaet hereinkommt.

- Eine Tabelle, die spaeter eine Spalte bekommt, bekommt sie spaeter und nicht leer (20-07).
  docs/l10n-portuguese.md fuehrt heute drei Spalten und einen Hinweis unmittelbar ueber der
  Tabelle, der Plan 20-08 nennt. Eine leere vierte Spalte sieht aus wie 202 vergessene
  Uebersetzungen.

- Ein Wortstamm-Gate auf einer Sprache stolpert ueber die Homographen einer anderen (20-04,
  bestaetigt und berichtigt in 20-05). Fuer Italienisch traf es nicht das Wort fuer Datei (das
  Italienische benutzt dort das englische Wort), sondern das fuer den Speicherort. Die Prognose
  der Vorgaengersprache sagt die Wirkung voraus und nicht das Wort; gelesen wird die Fundliste.
  Und ein echter Treffer der deutschen Form wird umformuliert, nicht mitentschuldigt: der
  Entwurf trug einen, die Zaehlung ging danach von zehn auf neun zurueck.
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

Last session: 2026-09-25T20:07:59.113Z
Stopped at: Phase 22 context gathered
Resume file: .planning/phases/22-messanfahrt-bl-f03/22-CONTEXT.md
