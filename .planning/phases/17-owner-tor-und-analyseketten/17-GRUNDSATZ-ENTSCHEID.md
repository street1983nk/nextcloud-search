# Phase 17: Grundsatzentscheide des Milestones v1.3 (LEX-01, LEX-07)

**Angelegt:** 2026-09-23 (Plan 17-01, Task 1)
**Zweck:** Dieses Dokument formuliert alle acht Entscheide VOR der Vorlage
vollstaendig aus, inklusive der fertigen Ersatztexte fuer jede betroffene Datei.
Am Vorlagetag wird nur noch gelesen, welcher Zweig greift, und der zugehoerige
Text eingesetzt; an diesem Tag wird kein Satz mehr entworfen. Folgeplaene
zitieren die Optionskennung (Beispiel `E-17-7 Option a`) und nie eine
Zusammenfassung.

---

## Die Frage

Duerfen die sechs Grundsatzentscheide des Milestones v1.3 so fallen, wie die
Recherche sie empfiehlt, und darf die Vergleichsregel fuer `tantivy_version`
gelockert werden?

---

## Was festgestellt ist

Alle Angaben in diesem Abschnitt sind am 2026-09-23 am eigenen Baum gelesen oder
am selben Tag selbst gemessen.

**Die Versionsmarke traegt den vollen Banner.**
`backend/src/findling/index/open.py:61-67` setzt
`TANTIVY_VERSION: Final[str] = tantivy.__version__`, und das ist nicht die
Nummer, sondern die ganze Zeile `"tantivy v0.26.0, index_format v7"`. Der
Kommentar darueber nennt diesen Messwert woertlich.
`backend/src/findling/index/open.py:123-141` schreibt ihn in
`expected_versions()` als Marke `tantivy_version` neben `schema_version`,
`index_version`, `analyzer_version` und `wordlist_hash`. Der Docstring derselben
Funktion begruendet das so: tantivy verspricht nicht, dass sein Plattenformat
seine eigenen Releases ueberlebt.

**Verglichen wird auf Gleichheit.**
`backend/src/findling/store/repo.py:631-669` (`Store.version_mismatch`) laeuft
ueber die erwarteten Marken und meldet jede, deren gespeicherter Wert nicht
zeichengleich ist. Die einzige heutige Ausnahme steht in derselben Schleife:
`index_version` wird ueber `_generation_at_least`
(`backend/src/findling/store/repo.py:1299`) als Untergrenze statt als Gleichheit
gelesen. Eine zweite Ausnahme dieser Bauart ist also kein neues Muster, sondern
das vorhandene an einer zweiten Stelle.

**Die Folge eines Patch-Sprungs.** Weil die Marke den Banner traegt und der
Vergleich auf Gleichheit laeuft, wuerde allein der Sprung von 0.26.0 auf 0.26.2
auf jeder Bestandsinstallation den vollen Crawl ausloesen: gemessen 19 h 20 min
fuer 52.137 Dokumente.

**Das Indexformat ist in beiden Fassungen dasselbe.** Gemessen am 2026-09-23:
`index_format v7` gilt in 0.26.0 UND in 0.26.2. Ein mit 0.26.0 geschriebener
Index ist mit 0.26.2 zu oeffnen und zu durchsuchen (`num_docs=1 hits=1`), und
derselbe Test laeuft rueckwaerts genauso, was den Rueckweg eines missglueckten
Upgrades offenhaelt. Die Tokenisierung von sieben Ketten (de mit Splitter, en,
name, es, it, nl, pt) ueber 32 Woerter, zusammen 224 Zeilen Ausgabe, ist zwischen
beiden Fassungen `diff`-gleich.

**Die Panic-Klasse ist benannt und klein.** Gemessen sind es genau fuenf
Sprachen: `arabic, greek, romanian, tamil, turkish`. Das ist die Differenz der
beiden Mengen, die tantivy fuehrt: 18 Sprachen haben einen Stemmer, 13 haben eine
eingebaute Stoppwortliste. In 0.26.0 stuerzt die Rust-Seite dabei mit
`PanicException` ab, in 0.26.2 kommt ein `ValueError`. Der Fehler tritt beim
`build()` auf, nicht bei der Filterkonstruktion; ein Test, der nur
`Filter.stopword(...)` baut, ist gruen und beweist nichts.

**Die Kettenmessung liegt vor.** 65 Formfamilien, 573 geordnete Paare aus
getippter Form und Form im Dokument. `fold frueh` (Kette A+) trifft 467 Paare,
`fold spaet` (Kette C+) trifft 463. Ohne gefaltete Ergaenzungsliste lecken die
eingebauten Stoppwortlisten: 77 spanische, 10 italienische, 0 niederlaendische
und 30 portugiesische Woerter erzeugen trotzdem einen Term. Die gefaltete
Ergaenzungsliste ist damit unabhaengig von der Faltposition Pflicht, und das ist
das einzige Messergebnis, das keine Abwaegung braucht.

**Der `ignore`-Eintrag fuer tantivy existiert bereits.** `.github/dependabot.yml`
traegt ihn am Dateiende, im Block `package-ecosystem: uv`, mit Owner-Datum
2026-09-21 und allen drei `update-types`. Er muss also nicht angelegt werden.
Seine Begruendung lautet heute woertlich "tantivy carries index format v7 from
0.26.2 on, which means a reindex on every installation that already runs", und
diese Begruendung ist durch die eigene Messung vom 2026-09-23 widerlegt: v7 gilt
schon in 0.26.0, das Format wechselt beim Sprung gar nicht. Der Eintrag bleibt
richtig, sein Begruendungstext wird mit dem Entscheid berichtigt.
Ausdruecklich festgehalten: `17-RESEARCH.md` irrt an genau dieser Stelle
zweimal. Abschnitt 4.1 fuehrt `.github/dependabot.yml` mit "kein `ignore`-Eintrag
fuer tantivy (Phase-16-Vorschlag, nie umgesetzt)", Abschnitt 4.4 mit "kein
Eintrag". Beides war beim Lesen des Baumes am 2026-09-23 falsch.

**Der "Union-Scorer-Bugfix in 0.26.2" ist nicht belegbar.** In den Release Notes
von `quickwit-oss/tantivy-py` zu 0.26.2 ist er nicht auffindbar, und der Sprung
enthaelt keinen Bump des Rust-Kerns tantivy, nur serde, serde_json, chrono,
pyo3-build-config, itertools und futures. Er wird aus jeder Begruendung
gestrichen und erscheint in dieser Vorlage nicht als Argument.

### Die sieben Stellen, die der Pin-Sprung rot macht

| Ort | Ist-Zustand am 23.09.2026 | Zielzustand bei E-17-7 Option a (lockern) | Zielzustand bei Option b (Pin bleibt) |
|---|---|---|---|
| `backend/tests/test_upgrade_compatibility.py`, `GOLD_V1_0_AND_V1_1["tantivy_version"]` | `"0.26.0"`, geprueft als Teilzeichenkette des Banners | `GOLD_INDEX_FORMAT`, also `"index_format v7"`; die Probe fragt dann nach dem Format und nicht nach der Patchnummer | unveraendert `"0.26.0"` |
| `backend/tests/test_upgrade_compatibility.py`, `TANTIVY_PIN` | `"tantivy==0.26.0"`, verglichen gegen `backend/pyproject.toml` | `"tantivy==0.26.2"` | unveraendert |
| `backend/tests/test_upgrade_compatibility.py`, `GOLD_INDEX_FORMAT` | `"index_format v7"` | unveraendert, **bleibt gruen**, weil v7 in beiden Fassungen gilt | unveraendert, bleibt gruen |
| `.github/workflows/deploy-harp.yml`, Job "Store upgrade 5", Zusicherung 2 (Zeilen 3288-3291) | `tantivyVersion` laeuft in der `for`-Schleife der fuenf unveraenderten Marken mit | `tantivyVersion` verlaesst die Schleife und bekommt eine eigene Pruefung nach dem Muster von Zusicherung 6: diese Marke DARF sich bewegen, und zwar genau von 0.26.0 nach 0.26.2 | unveraendert |
| `.github/workflows/deploy-harp.yml`, dieselbe Stelle, Zusicherung 4 (kein Reindex-Banner) | `.reindexBanner` muss falsch sein | unveraendert, muss gruen bleiben; sie ist der Beweis, dass die Lockerung wirkt | unveraendert |
| `.github/workflows/deploy-harp.yml`, dieselbe Stelle, Zusicherung 5 (keine Zeile "built by different code") | kein `start_rebuild_on_drift` im Containerlog | unveraendert, muss gruen bleiben | unveraendert |
| `.github/dependabot.yml`, Begruendungskommentar ueber dem `ignore`-Block | "tantivy carries index format v7 from 0.26.2 on, which means a reindex" | berichtigt: v7 gilt in 0.26.0 und 0.26.2, gemessen am 2026-09-23; der Pin bewegt sich weiterhin nur mit Absicht | berichtigt, aber ohne Pin-Bewegung: die falsche Formatbehauptung faellt trotzdem |

---

## Was unklar ist

Zwei Dinge, und nur diese zwei. Alles andere ist gemessen.

1. **Die Risikoneigung des Owners gegenueber einer gelockerten Marke (E-17-7).**
   Wer die `index_format`-Haelfte entscheiden laesst, gibt eine Absicherung auf:
   tantivy koennte die Tokenisierung aendern, ohne das Format zu aendern. Die
   Messung vom 2026-09-23 zeigt, dass es beim Sprung 0.26.0 auf 0.26.2 nicht
   passiert ist; sie kann nichts ueber kuenftige Fassungen sagen. Ob dieser
   Restschatten tragbar ist, ist keine Messfrage.
2. **Der Widerspruch gegen die einheitliche Kettenreihenfolge (E-17-8).**
   Spanisch isoliert spricht mit 4 von 208 Paaren fuer `fold spaet`. Ob dieser
   Abstand eine zweite Kettenform im Modul rechtfertigt, ist eine Abwaegung
   zwischen Messwert und Einheitlichkeit, keine Tatsache.

---

## Die Leitplanke, die fuer alle Optionen gilt

Ohne diese Definition blockiert das Tor die ganze Phase, weil "vor diesem
Entscheid kein Code, der D-04 beruehrt" als "vor diesem Entscheid kein Code"
gelesen wird.

> **D-04 beruehren heisst genau dreierlei: eine der fuenf Versionsmarken
> (`schema_version`, `index_version`, `analyzer_version`, `wordlist_hash`,
> `tantivy_version`) bewegen, ein Schemafeld anlegen, oder die Query-Feldliste
> erweitern. Nicht mehr und nicht weniger.**

Daraus folgt, was vor dem Tor laufen darf:

| Arbeit | Vor dem Tor? | Grund |
|---|---|---|
| Kettenmessung, Sonde, Fixtures, Messbericht | ja | veraendert keine Marke, kein Feld, keine Query |
| `docs/language-analyzers.md` | ja | Dokumentation |
| `LANGUAGE_ALLOWLIST` plus Paritaetstest | ja | die Konstante wird von nichts gelesen, solange die Fabrik nicht daran haengt |
| Die vier Analyse-Funktionen anlegen, **ohne** sie zu registrieren | ja, mit Vorsicht | sie aendern keine bestehende Kette; `ANALYZER_VERSION` bleibt deshalb auf 1. Der Modulkopf sagt "Any change to a chain below has to raise ANALYZER_VERSION", und eine hinzugefuegte, nirgends registrierte Kette ist keine Aenderung an einer bestehenden. Das gehoert als Satz in den Modulkopf, sonst hebt der naechste Leser die Marke aus Vorsicht und loest genau das aus, was Erfolgskriterium 4 verbietet |
| tantivy-Pin bewegen | **nein** | bewegt `tantivy_version`, siehe die Tabelle der sieben Stellen |
| `english_analyzer()` in die gemeinsame Fabrik ueberfuehren | ja, wenn tokenidentisch | `Filter.custom_stopword([])` ist gemessen ein No-op; der Beweis gehoert als Test dazu, sonst ist es eine stille Aenderung der englischen Tokenisierung |
| Hash der gefalteten Ergaenzungsliste | ja, aber NUR als Testwert | ein Hash in `expected_versions()` waere eine sechste Marke und damit ein Reindex auf jeder Bestandsinstallation |

---

## Die acht Entscheide

**E-17-7 wird als erste Frage der Vorlage gestellt**, weil alle Plaene mit
tantivy-Bezug daran haengen: 17-07 und 17-08 laufen ueberhaupt nur in einem der
beiden Zweige, und die Formulierung von LEX-07 haengt am selben Entscheid. Die
uebrigen sieben werden danach in der Reihenfolge E-17-1 bis E-17-6 und E-17-8
gelesen.

### E-17-1: Wandert ein Bestandsindex per Re-Analyse aus den gespeicherten Feldern in das neue Schema, oder per Vollreindex ueber Nextcloud?

**Empfehlung:** Option a, Re-Analyse aus den gespeicherten Feldern.

**Beleg:** Der Vollreindex ist gemessen 19 h 20 min fuer 52.137 Dokumente; die
Re-Analyse ist auf 1 bis 3 h geschaetzt, weil sie weder herunterlaedt noch OCR
noch Einbettung wiederholt, und wird in MESS-08 nachgemessen. Bei der Re-Analyse
bleiben `vectors.db` und `state.db` unberuehrt. ARCHITECTURE.md, PITFALLS Nr. 2
und alle vier Recherchen sind hier einig.

#### Option a: Re-Analyse aus den gespeicherten Feldern

- **Greift, wenn** der Owner den Umbauweg ueber die gespeicherten Felder waehlt.
- **Beweisgrundlage:** die gemessenen 19 h 20 min der Gegenoption, die
  unberuehrten `vectors.db` und `state.db`, und die Nachmessung in MESS-08.
- **Vollzug:** Phase 18 baut `index/rebuild.py`; die umgedrehte Beweisstrecke
  (`UPGRADE_FROM_TAG=v1.2.0`) in `deploy-harp.yml` zeigt den vollstaendigen Lauf.
  In Phase 17 faellt dazu keine Zeile Code an.

#### Option b: Vollreindex ueber Nextcloud

- **Greift, wenn** der Owner den einfacheren Weg dem kuerzeren vorzieht und die
  Ausfallzeit auf Bestandsinstallationen in Kauf nimmt.
- **Beweisgrundlage:** der Pfad existiert bereits (`start_rebuild_on_drift`
  plus Reindex-Banner plus `occ findling:index --restart`), es waere kein neuer
  Code, sondern nur ein bewusst ausgeloester bekannter Vorgang.
- **Vollzug:** Phase 18 entfaellt bis auf Schema und Marken; die Zusage
  "kein Reindex" faellt, und die Store-Beschreibung von 1.3.0 muss den Umbau
  ankuendigen.

### E-17-2: Traegt das Schema alle sechs Koerperfelder immer, und entscheidet `FINDLING_LANGUAGES` nur die Befuellung?

**Empfehlung:** Option a, Modell A, sechs Koerperfelder immer im Schema.

**Beleg:** Leere Felder kosten gemessen null Byte auf der Platte. Die
Alternativen (ein Index je Sprache, ein multilinguales Sammelfeld) sind in
STACK-Messung, FEATURES und ARCHITECTURE einstimmig abgelehnt.

#### Option a: Sechs Felder immer im Schema, Befuellung nach `FINDLING_LANGUAGES`

- **Greift, wenn** der Owner Modell A bestaetigt.
- **Beweisgrundlage:** null Byte fuer leere Felder, ein einziges
  Indexverzeichnis, ein einziges `schema_version`, und das Zuschalten einer
  Sprache bleibt eine Befuellungsfrage statt einer Schemafrage.
- **Vollzug:** Phase 18 legt die vier neuen Felder an und hebt `schema_version`
  um genau eine Stufe; Phase 19 oeffnet die Query-Feldliste.

#### Option b: Ein Index je Sprache

- **Greift, wenn** der Owner leere Schemafelder grundsaetzlich ablehnt.
- **Beweisgrundlage:** keine leeren Felder, aber n Indexverzeichnisse, n
  Writer-Heaps und eine Trefferzusammenfuehrung ueber Indexgrenzen hinweg, die
  es heute nicht gibt.
- **Vollzug:** Phase 18 und Phase 19 werden neu geplant; die RRF-Zusammen-
  fuehrung und das RAM-Budget der 4-GB-Box muessen neu gerechnet werden.

### E-17-3: Darf `FINDLING_LANGUAGES` Deutsch und Englisch abschalten?

**Empfehlung:** Option a, ja, erlauben.

**Beleg:** `backend/src/findling/config.py:1002-1015` (`_languages()`) erlaubt
heute schon `FINDLING_LANGUAGES=de`, filtert gegen `DEFAULT_LANGUAGES` und faellt
nur bei leerem Ergebnis zurueck. `DEFAULT_LANGUAGES = ("de", "en")`
(`config.py:80`) bleibt die Werkseinstellung. Eine spanische Behoerde soll nicht
zwei unbenutzte Felder befuellen; das Abschalten ist ohnehin derselbe Vorgang
wie das Zuschalten, weil sich in beiden Faellen der Sprachmerker bewegt.

#### Option a: Abschalten erlauben, Werkseinstellung bleibt `de,en`

- **Greift, wenn** der Owner die freie Sprachwahl bestaetigt.
- **Beweisgrundlage:** das heutige Verhalten von `_languages()`, das den Fall
  bereits zulaesst, und die Tatsache, dass Bestandsinstallationen ohne gesetzte
  Variable unveraendert `de,en` bekommen.
- **Vollzug:** Phase 18 haengt die Kettenfabrik und die Befuellung an die
  gelesene Sprachmenge; der Diagnosepfad zeigt aktive und befuellte Sprachen.

#### Option b: `de` und `en` als erzwungener Boden

- **Greift, wenn** der Owner einen erklaerbaren Mindestzustand ueber die
  Platzersparnis stellt.
- **Beweisgrundlage:** einfacher zu erklaeren und zu unterstuetzen; kostet
  Bestandsinstallationen nichts, weil sie ohnehin `de,en` fuehren, und kostet
  neuen Installationen Platz fuer zwei nie befuellte Felder.
- **Vollzug:** Phase 18 ergaenzt `_languages()` um den Boden und einen Test, der
  ihn festhaelt; sonst aendert sich an der Planung nichts.

### E-17-4: Wird die Sprachmenge ein sechster Versionsmerker in `expected_versions()`?

**Empfehlung:** Option a, ja, als nach Schemafeldreihenfolge normalisierte
Zeichenkette.

**Beleg:** `backend/src/findling/index/open.py:123-141` fuehrt heute fuenf
Marken. Ohne sechste Marke bemerkt keine Bestandsinstallation, dass sich die
Sprachmenge geaendert hat, und der Umbau unterbleibt genau dann, wenn er noetig
waere. Die Normalisierung ist Pflicht, weil `"es,de"` und `"de,es"` dieselbe
Menge sind; `config.py:1002-1015` normalisiert heute schon auf die
Schemafeldreihenfolge.

#### Option a: Sechster Merker, normalisiert, mit Auflage

- **Greift, wenn** der Owner den Merker will.
- **Beweisgrundlage:** die fuenf vorhandenen Marken und ihr Vergleichsmuster in
  `Store.version_mismatch`; die Normalisierung verhindert, dass eine umsortierte
  Umgebungsvariable einen Umbau ausloest.
- **Vollzug:** Phase 18 ergaenzt `expected_versions()`, den Lockstep-Test und die
  Saat; Phase 17 fasst `expected_versions()` nicht an.

**Auflage, ohne die diese Option ihr eigenes Ziel verfehlt:** Eine Marke, die auf
keiner Bestandsinstallation existiert, liest `Store.version_mismatch`
(`backend/src/findling/store/repo.py:637`) als Abweichung, denn dort steht
woertlich "A mark that was never written counts as diverging". Der neue Merker
wuerde also auf jeder Bestandsinstallation genau den Reindex ausloesen, den er
verhindern soll. Er muss deshalb entweder beim Oeffnen gesaet werden (Muster
`_DEFAULT_META` in `open_store()`) oder sein Fehlen muss als `"de,en"` gelesen
werden. Die Umsetzung samt Test gehoert in Phase 18.

#### Option b: Kein sechster Merker

- **Greift, wenn** der Owner die fuenf Marken nicht erweitern will.
- **Beweisgrundlage:** kein neues Saatproblem, kein sechster Eintrag im
  Lockstep-Muster; dafuer muss der Umbau an einer anderen Stelle erkannt werden,
  und das waere ein zweites, unabhaengiges Gedaechtnis neben den Marken.
- **Vollzug:** Phase 18 erkennt die geaenderte Sprachmenge ueber einen eigenen
  Zustand in `state.db` statt ueber `expected_versions()`; der Lockstep-Test
  bleibt bei fuenf Marken.

### E-17-5: Reicht fuer die neuen Kataloge maschinelle Uebersetzung plus Community-Review mit datiertem Vorbehalt, ohne Muttersprachler-Gate?

**Empfehlung:** Option a, ja, nach dem FR-Muster.

**Beleg:** `docs/l10n-french.md` traegt genau dieses Muster: maschinell erzeugt,
Wortwahl-Entscheide dokumentiert, datierter Review-Vorbehalt im Katalog, und die
Auslieferung wartet nicht auf einen Muttersprachler. KAT-02 fordert den
Vorbehalt, nicht das Gate.

#### Option a: Maschinell plus Community-Review mit datiertem Vorbehalt

- **Greift, wenn** der Owner das FR-Muster fuer es, it, nl, pt_PT und pt_BR
  uebernimmt.
- **Beweisgrundlage:** das ausgelieferte franzoesische Katalogpaar und sein
  Vorbehalt; die Schluesselzahl-Gates fangen Luecken, nicht Wortwahl.
- **Vollzug:** Phase 20 (Parallelpfad) erzeugt zehn Katalogdateien und traegt je
  Katalog den datierten Vorbehalt ein.

#### Option b: Muttersprachler-Gate vor der Auslieferung

- **Greift, wenn** der Owner keine unbegutachtete Sprache ausliefern will.
- **Beweisgrundlage:** hoehere Textqualitaet; Preis ist eine Abhaengigkeit von
  Freiwilligen, die den Termin von 1.3.0 nicht kennt.
- **Vollzug:** Phase 20 liefert die Kataloge, aber Phase 23 (Store-Einreichung)
  bekommt ein zusaetzliches blockierendes Tor je Sprache.

### E-17-6: Bleiben die niederlaendischen Komposita im Scope des Milestones?

**Empfehlung:** Option a, im Scope behalten, endgueltiges Tor in Phase 21.

**Beleg:** KOMP-01 und ROADMAP Phase 21. Phase 21 haengt an Phase 19 und ist
als Ganzes streichbar; das Sturzkriterium ist der Termin, nicht die Machbarkeit.

#### Option a: Im Scope behalten, Tor in Phase 21

- **Greift, wenn** der Owner die Entscheidung an den Terminstand von Phase 21
  binden will.
- **Beweisgrundlage:** Phase 21 steht hinter Phase 19 und beruehrt keinen
  anderen Strang; ein spaeter Sturz kostet nichts ausser der Planung.
- **Vollzug:** Phase 21 wird geplant und faellt bei Terminnot **als Ganzes**,
  nicht halb: eine halb eingebaute Kompositazerlegung waere eine Kette ohne
  Messabnahme und damit schlechter als keine.

#### Option b: Jetzt streichen

- **Greift, wenn** der Owner den Termin von 1.3.0 hoeher gewichtet als die
  niederlaendische Trefferqualitaet.
- **Beweisgrundlage:** Phase 21 entfaellt vollstaendig, der Milestone wird
  kuerzer und die niederlaendische Kette bleibt beim reinen Stemmer, der laut
  Messung ohnehin selbst faltet.
- **Vollzug:** ROADMAP verliert Phase 21, KOMP-01 wandert in den Backlog nach
  v1.3.

### E-17-7: Darf die Vergleichsregel fuer `tantivy_version` gelockert werden, sodass nur noch die `index_format`-Haelfte entscheidet?

**Empfehlung:** Option a, lockern.

**Beleg:** Die vier Messungen vom 2026-09-23 (siehe "Was festgestellt ist") und
die vorhandene Praezedenz: `index_version` ist in
`backend/src/findling/store/repo.py:665-667` schon heute eine Untergrenze statt
einer Gleichheit, und zwar an genau derselben Stelle im Code.

#### Option a: Lockern, Banner speichern, Format vergleichen

- **Greift, wenn** der Owner die gelockerte Vergleichsregel freigibt.
- **Beweisgrundlage:** vier eigene Messungen vom 2026-09-23. Erstens: der Banner
  lautet in beiden Fassungen auf `index_format v7`. Zweitens: ein mit 0.26.0
  geschriebener Index laesst sich mit 0.26.2 oeffnen und durchsuchen, und der
  Kreuzlesetest laeuft auch rueckwaerts, was den Rueckweg eines missglueckten
  Upgrades offenhaelt. Drittens: die Tokenisierung von sieben Ketten ueber 32
  Woerter, 224 Zeilen Ausgabe, ist zwischen beiden Fassungen `diff`-gleich.
  Viertens: die Raedermatrix auf PyPI fuehrt fuer 0.26.2 weiterhin cp313
  manylinux_2_17 fuer aarch64 UND x86_64, der ARM-Zielpfad bleibt also bedient
  (weggefallen sind nur die free-threaded cp313t-Raeder).
- **Was dabei aufgegeben wird:** die Absicherung "tantivy koennte die
  Tokenisierung aendern, ohne das Format zu aendern". Sie wird ersetzt durch die
  Tabellen- und Waechtertests, die diese Phase ohnehin baut: die Kettenfabrik mit
  AST-Waechter aus Plan 17-03, die Sonde und die Rohdaten aus Plan 17-05 und die
  Formfamilien-Gates aus Plan 17-06. Eine geaenderte Tokenisierung wird damit
  sofort rot, und zwar an der Stelle, die sie beschreibt, statt als
  Versionsmarke, die nur sagt, dass sich irgendetwas bewegt hat.
- **Was ausdruecklich NICHT geht:** den Pin bewegen und die Marke unveraendert
  behaupten. Wer die Gold-Werte "anpasst", ohne die Vergleichsregel zu aendern,
  behauptet gegenueber jeder Bestandsinstallation etwas, das der laufende Code
  nicht einhaelt.
- **Vollzug:** Plan 17-07 aendert `Store.version_mismatch` und die Gold-Werte
  samt vierter Selbstprobe; Plan 17-08 bewegt den Pin, die CI-Zusicherung, den
  dependabot-Kommentar und `THIRD-PARTY.md`. Beide Plaene laufen erst nach dem
  Vollzugseintrag unten.

#### Option b: Pin bleibt auf 0.26.0

- **Greift, wenn** der Owner die Marke unangetastet lassen will.
- **Beweisgrundlage:** Die Panic-Frage traegt den Sprung allein nicht: die
  Positivliste `LANGUAGE_ALLOWLIST` (Plan 17-02) schliesst die fuenf Sprachen
  `arabic, greek, romanian, tamil, turkish` vollstaendig aus, und auf dem
  heutigen Pfad ist die Panic ohnehin unerreichbar, weil `_languages()` keinen
  fremden Namen durchreicht. Der Sprung waere damit eine Bequemlichkeit, kein
  Muss.
- **Preis:** LEX-07 muss umformuliert werden, weil es heute `tantivy` auf 0.26.2
  festschreibt; Erfolgskriterium 3 der Phase verliert seine zweite Haelfte.
  `Index.is_compatible()` aus 0.26.2 steht Phase 18 dann nicht zur Verfuegung
  (was kein Verlust ist, weil es das Schema gar nicht prueft).
- **Vollzug:** Plan 17-07 und Plan 17-08 entfallen ersatzlos; stattdessen wird
  LEX-07 in `REQUIREMENTS.md` umformuliert und der falsche Begruendungstext in
  `.github/dependabot.yml` trotzdem berichtigt.

### E-17-8: Bekommen alle vier neuen Sprachen dieselbe Kettenreihenfolge `fold frueh`? (Kenntnisnahme mit Widerspruchsmoeglichkeit)

Dieser Punkt wird **als Kenntnisnahme vorgelegt, nicht als offene Frage**: LEX-01
macht die Messung zum entscheidenden Instrument, und die Messung liegt vor. Der
Owner kann widersprechen; ohne Widerspruch gilt Option a.

**Empfehlung:** Option a, einheitlich `fold frueh` (Kette A+,
`low, fold, stop, CSTOP, long, stem`).

**Beleg:** 65 Formfamilien, 573 geordnete Paare. `fold frueh` trifft 467,
`fold spaet` trifft 463. Aufgeschluesselt: Spanisch allein spricht mit 4 von 208
Paaren fuer `fold spaet`, Italienisch mit 2 von 56 und Portugiesisch mit 6 von
228 fuer `fold frueh`, Niederlaendisch ist unentschieden, weil der
niederlaendische Stemmer selbst faltet.

#### Option a: Einheitlich `fold frueh` fuer es, it, nl und pt

- **Greift, wenn** der Owner nicht widerspricht.
- **Beweisgrundlage:** vier Begruendungen. Erstens: der Abstand liegt in beiden
  Richtungen unter drei Prozentpunkten und beruht in Spanisch auf genau einer
  Wortklasse (`aleman`/`alemanes`). Zweitens: `fold frueh` ist die Form der schon
  ausgelieferten englischen Kette, und `Filter.custom_stopword([])` ist gemessen
  ein No-op (13 Testwoerter, identische Tokens mit und ohne), also bedient eine
  einzige Fabrik `en`, `es`, `it`, `nl` und `pt`, ohne die englische
  Tokenisierung um ein Byte zu verschieben. Drittens: das Produkt liest OCR, und
  ein Scan, dem der Akzent verlorengeht, bleibt bei `fold frueh` unter der
  korrekten Schreibweise auffindbar, bei `fold spaet` nicht. Viertens:
  `fold spaet` erzeugt in it und nl zusaetzlich Terme, die keine Anfrage je
  erreichen kann.
- **Der Preis, den der Owner mit unterschreibt:** Zwei dokumentierte Verluste.
  Spanisch findet `informacion` nicht ueber `informaciones` und umgekehrt (die
  ganze Klasse auf `-cion`), und Portugiesisch trennt `informacao` von
  `informacoes`, und zwar in jeder Kette. Beide gehen nach HART-05 in
  `docs/language-analyzers.md`.
- **Vollzug:** Plan 17-03 baut eine Fabrik fuer alle fuenf Ketten; Plan 17-06
  macht die Formfamilien-Zahlen zu Gates und schreibt das Verdikt datiert in die
  Doku.

#### Option b: Widerspruch, Spanisch auf `fold spaet`

- **Greift, wenn** der Owner der Messzahl fuer Spanisch den Vorrang vor der
  Einheitlichkeit gibt.
- **Beweisgrundlage:** Spanisch gewinnt isoliert 4 von 208 Paaren (1,9 Punkte),
  in der zweiten, unabhaengigen Stichprobe 4 von 137 (2,9 Punkte). Der Waisenplatz
  wandert dabei nur: bei `fold spaet` faellt die flach getippte Singularform aus,
  bei `fold frueh` die korrekt geschriebene Pluralform.
- **Preis:** zwei Kettenformen im Modul, zwei Regeln statt einer, und die
  spanische Kette laesst sich nicht mehr aus derselben Fabrik wie die englische
  bedienen.
- **Vollzug:** Plan 17-03 baut zwei Fabriken; Plan 17-06 fuehrt je Sprache
  getrennte Sollwerte, und `docs/language-analyzers.md` erklaert, warum eine
  Sprache aus der Reihe faellt.

---

## Die fertigen Ersatztexte

Alle sechs Bloecke sind wortwoertlich einsetzbar. Die Plaene 17-07 und 17-08
kopieren den Text und ersetzen darin nur den Platzhalter `<VORLAGETAG>` durch
das Datum des Vollzugs. Die Sprache der Kommentare im Code, im YAML und in
`THIRD-PARTY.md` bleibt Englisch, wie der jeweilige Bestand.

Alle sechs Stellen gelten fuer **E-17-7 Option a**. Unter **Option b** gilt je
Stelle "keine Aenderung", mit einer Ausnahme, die unten bei
`.github/dependabot.yml` steht; dazu kommt in beiden Faellen der Satz, dass unter
Option b **LEX-07 umformuliert werden muss**, weil es heute `tantivy` auf 0.26.2
festschreibt.

### backend/pyproject.toml

**Heute** (Zeile 13, im `dependencies`-Block):

```toml
    "tantivy==0.26.0",
```

**Ersatztext unter E-17-7 Option a:**

```toml
    "tantivy==0.26.2",
```

Die Zeile wird von Hand geaendert, `backend/uv.lock` NICHT: der Lock bewegt sich
ausschliesslich ueber `uv lock --upgrade-package tantivy` aus `backend/`.

**Unter Option b:** keine Aenderung. LEX-07 muss umformuliert werden.

### backend/tests/test_upgrade_compatibility.py

**Heute** (Zeilen 42 bis 77, gekuerzt auf die drei Stellen, die sich bewegen):

```python
GOLD_V1_0_AND_V1_1 = {
    "schema_version": "1",
    "index_version": "1",
    "analyzer_version": "1",
    "tantivy_version": "0.26.0",
}

TANTIVY_MARK = "tantivy_version"

# The index format of tantivy 0.26.0. It is the half of the banner that decides
# whether the files on disk can still be opened at all.
GOLD_INDEX_FORMAT = "index_format v7"

TANTIVY_PIN = "tantivy==0.26.0"
```

**Ersatztext unter E-17-7 Option a.** `GOLD_INDEX_FORMAT` wandert dabei VOR das
Woerterbuch, weil das Woerterbuch es nun liest:

```python
# The index format both pinned tantivy releases report. It is the half of the
# banner that decides whether the files on disk can still be opened at all, and
# since the owner decision E-17-7 option a of <VORLAGETAG> it is also the half
# the store compares. Measured on 2026-09-23: 0.26.0 and 0.26.2 both report
# "index_format v7", an index written by one opens and answers under the other
# in both directions, and the tokenisation of seven chains over 224 lines is
# identical between them.
GOLD_INDEX_FORMAT = "index_format v7"

GOLD_V1_0_AND_V1_1 = {
    "schema_version": "1",
    "index_version": "1",
    "analyzer_version": "1",
    "tantivy_version": GOLD_INDEX_FORMAT,
}

TANTIVY_MARK = "tantivy_version"

# The pin the banner above grows out of. Named here because a moved pin and a
# moved mark are the same event seen from two sides. The patch number may move
# with a decision behind it; the format half above may not.
TANTIVY_PIN = "tantivy==0.26.2"
```

**Die vierte Selbstprobe**, die zu `test_the_drift_reader_fires_on_a_staged_sample`
dazukommt, unmittelbar hinter der Probe `holding`:

```python
    same_format_other_patch = drift_findings(
        {**holding, "tantivy_version": "tantivy v0.26.2, index_format v7"}
    )
    assert same_format_other_patch == [], same_format_other_patch
```

**Was stehen bleibt:** Der Modulkopfsatz "**A red test here is not a repair, it
is a question for the owner.**" bleibt woertlich unveraendert, samt dem Absatz,
der ihn traegt. Er wird durch diesen Entscheid nicht widerlegt, sondern eingeloest:
die Frage ist gestellt und beantwortet worden, statt den Test gruen zu
reparieren. Ebenfalls unveraendert bleiben `WNGERMAN_PIN`, `ALL_MARKS`, die
Funktion `drift_findings` und die drei vorhandenen Selbstproben.

**Unter Option b:** keine Aenderung. LEX-07 muss umformuliert werden.

### backend/src/findling/store/repo.py

**Heute** (Zeilen 660 bis 669, die Vergleichsschleife in
`Store.version_mismatch`):

```python
        stored = self.read_meta()
        diverging = []
        for key, value in expected.items():
            current = stored.get(key)
            if current == value:
                continue
            if key == "index_version" and _generation_at_least(current, value):
                continue
            diverging.append(key)
        return diverging
```

**Ersatztext unter E-17-7 Option a**, die dritte `if`-Zeile nach dem Vorbild der
`index_version`-Ausnahme:

```python
        stored = self.read_meta()
        diverging = []
        for key, value in expected.items():
            current = stored.get(key)
            if current == value:
                continue
            if key == "index_version" and _generation_at_least(current, value):
                continue
            if key == "tantivy_version" and _index_format_matches(current, value):
                continue
            diverging.append(key)
        return diverging
```

**Der Hilfsvergleicher**, gebaut nach dem Muster von `_generation_at_least`
(`backend/src/findling/store/repo.py:1299`) und unmittelbar daneben abgelegt:

```python
def _index_format_matches(stored: str | None, expected: str) -> bool:
    """True when both banners name the same index format.

    The banner reads "tantivy v0.26.0, index_format v7", and only its second half
    decides whether the files on disk can still be opened. A banner without that
    half is a divergence, never a pass: a mark that cannot be read cannot be shown
    to match the current code.
    """
    marker = "index_format "
    if stored is None:
        return False
    here = stored.find(marker)
    there = expected.find(marker)
    if here < 0 or there < 0:
        return False
    return stored[here:] == expected[there:]
```

**Der neue Docstring-Absatz** in `Store.version_mismatch`, im Ton des
vorhandenen `index_version`-Absatzes und direkt hinter ihm:

```
    ``tantivy_version`` is the other mark that is not an equality. It stores the
    full banner, because that is what a diagnosis needs, but only its
    ``index_format`` half decides whether the files on disk can still be opened.
    Measured on 2026-09-23: tantivy 0.26.0 and 0.26.2 both report
    ``index_format v7``, an index written by one opens and answers under the
    other in both directions, and the tokenisation of seven chains over 224 lines
    is identical. A patch release that keeps the format is therefore not a drift.
    The assurance this gives up, a changed tokenisation behind an unchanged
    format, is held by the chain tables of phase 17 instead (owner decision
    E-17-7 option a of <VORLAGETAG>).
```

**Unter Option b:** keine Aenderung. LEX-07 muss umformuliert werden.

### .github/workflows/deploy-harp.yml

**Heute** (Job "Store upgrade 5, the six assurances after the upgrade",
Zusicherung 2, Zeilen 3288 bis 3291):

```bash
          echo "--- 2, the same five marks (D-04) ---"
          for mark in schemaVersion indexVersion analyzerVersion wordlistHash tantivyVersion; do
            unchanged ".marks.${mark}" "a version mark moved, and a moved mark is a full reindex on every installation in the field (D-04)"
          done
```

**Ersatztext unter E-17-7 Option a.** `tantivyVersion` verlaesst die Schleife der
unveraenderten Marken und bekommt daneben eine eigene Pruefung nach dem Muster
von Zusicherung 6 ("diese Marke DARF sich bewegen, und zwar genau von X nach Y"):

```bash
          echo "--- 2, the same four marks, and the fifth one may move (D-04) ---"
          for mark in schemaVersion indexVersion analyzerVersion wordlistHash; do
            unchanged ".marks.${mark}" "a version mark moved, and a moved mark is a full reindex on every installation in the field (D-04)"
          done

          # tantivyVersion is the one mark that MAY move, and only in its patch
          # number. The store compares the index format half since the owner
          # decision E-17-7 option a of <VORLAGETAG>, so that is what this asserts:
          # a moved format half is still a full reindex in the field, a moved
          # patch number behind an unchanged format half is the upgrade working.
          was=$(jq -r '.marks.tantivyVersion' "${before}")
          now=$(jq -r '.marks.tantivyVersion' "${after}")
          if [ "${was#*index_format }" != "${now#*index_format }" ]; then
            echo "::error::the index format half of tantivyVersion went from ${was} to ${now}, and that is a full reindex on every installation in the field (D-04)"
            fail=1
          elif [ "${was}" = "${now}" ]; then
            echo "unchanged  .marks.tantivyVersion = ${was}   (the engine banner did not move at all)"
          else
            echo "moved on purpose  .marks.tantivyVersion ${was} to ${now}, same index format half (E-17-7 option a)"
          fi
```

**Der Zusammenfassungsblock** (Zeile 3356) wird mitgeaendert:

```bash
            echo "- unchanged: the hits for Belehrung, Auszug and Erinnerung, four of the five index marks and the index format half of the fifth, the document counts, the work stock"
```

**Was woertlich stehen bleibt und gruen bleiben MUSS:** Zusicherung 4 (kein
Reindex-Banner, `.reindexBanner` falsch) und Zusicherung 5 (keine Zeile "built by
different code" im Containerlog). Diese beiden sind der eigentliche Beweis, dass
die Lockerung wirkt: sie sagen, dass auf einer echten Instanz nach dem Upgrade
kein Umbau begann. Wer sie anfasst, hat den Beweis abgeschafft statt ihn gefuehrt.

**Unter Option b:** keine Aenderung. LEX-07 muss umformuliert werden.

### .github/dependabot.yml

**Der `ignore`-Block wird NICHT neu angelegt.** Er steht bereits am Dateiende im
Block `package-ecosystem: uv`, mit allen drei `update-types`, und bleibt
unveraendert. Geaendert wird ausschliesslich der Begruendungskommentar darueber.

**Heute:**

```yaml
    # tantivy carries index format v7 from 0.26.2 on, which means a reindex on
    # every installation that already runs. The pin therefore only ever moves on
    # purpose and together with a reindex plan (owner decision of 2026-09-21).
```

**Ersatztext unter E-17-7 Option a:**

```yaml
    # tantivy stays pinned, and the pin only ever moves on purpose. The reason
    # written here on 2026-09-21 said "index format v7 from 0.26.2 on, which
    # means a reindex", and that reading is wrong: measured on 2026-09-23, 0.26.0
    # and 0.26.2 both report "index_format v7", an index written by one opens and
    # answers under the other in both directions, and the tokenisation of seven
    # chains over 224 lines is identical. What a bump really moves is the version
    # mark, and since <VORLAGETAG> only the index format half of that mark is
    # compared (owner decision E-17-7 option a, which supersedes the owner
    # decision of 2026-09-21 rather than deleting it). The rule therefore stands
    # for a better reason than the one it was written with: a grouped weekly pull
    # request is the wrong place to move the engine of the search.
```

Die beiden folgenden Absaetze des heutigen Kommentars (der Hinweis auf die
Kommandoantwort in Pull Request #10 und darauf, dass diese Regel deshalb hier in
einer Datei steht) bleiben woertlich stehen.

**Unter Option b:** Der Begruendungskommentar wird **trotzdem** berichtigt, denn
die Formatbehauptung ist unabhaengig vom Pin falsch. Der Ersatztext lautet dann
gleich, ohne den Satz zur gelockerten Vergleichsregel und mit dem Zusatz, dass
der Pin auf 0.26.0 bleibt. LEX-07 muss umformuliert werden.

### THIRD-PARTY.md

**Heute**, Tabellenzeile 138 im Abschnitt "Python packages of the extraction and
index path":

```markdown
| `tantivy` | 0.26.0 | MIT | github.com/quickwit-oss/tantivy-py | `/app/.venv/lib/python3.13/site-packages/tantivy` |
```

und der Begruendungsabsatz darunter (Zeilen 151 bis 156), der den Tag `0.26.0`
zweimal nennt.

**Ersatztext unter E-17-7 Option a**, Tabellenzeile:

```markdown
| `tantivy` | 0.26.2 | MIT | github.com/quickwit-oss/tantivy-py | `/app/.venv/lib/python3.13/site-packages/tantivy` |
```

Begruendungsabsatz, mit auf `0.26.2` gezogenem Tag und dem neuen Satz zu den
Stoppwortlisten:

```markdown
`tantivy` is the one entry whose licence is **not** readable from its PyPI
metadata: the 0.26.2 release carries neither a `license` field nor a licence
classifier. The MIT text is in `LICENSE` of the tagged upstream repository
(`quickwit-oss/tantivy-py`, tag `0.26.2`), and the Rust crate the bindings wrap
is MIT as well. It is written down here so the next reader does not have to
repeat the search.

The Snowball stop word lists the analyzers of this app use for German, English,
Spanish, Italian, Dutch and Portuguese are BSD-3-Clause, they are compiled into
the same extension module and are not a separate dependency, and the folded
supplementary list shipped in this repository is derived from them.
```

**Unter Option b:** keine Aenderung an der Versionsangabe. Der Satz zu den
Snowball-Stoppwortlisten wird trotzdem ergaenzt, weil die Ketten dieser Phase sie
unabhaengig vom Pin benutzen. LEX-07 muss umformuliert werden.

---

## Vollzug am <Datum>

Leer angelegt von Plan 17-01 (Task 3). Gefuellt von Plan 17-04 am Vorlagetag.
Bis dahin bleiben alle Felder auf `,`.

- **Datum:** ,
- **Gelesener Stand:** ,

  | Gelesen | Stand am Vorlagetag |
  |---|---|
  | `backend/pyproject.toml`, tantivy-Pin | , |
  | `backend/tests/test_upgrade_compatibility.py`, `GOLD_V1_0_AND_V1_1["tantivy_version"]` | , |
  | `.github/dependabot.yml`, `ignore`-Block fuer tantivy | , |
  | Volle Suite aus `backend/` | , |

- **Greifender Zweig je Entscheid:** ,

  | Entscheid | Option | Begruendung des Owners |
  |---|---|---|
  | E-17-1 Umbauweg | , | , |
  | E-17-2 Feldmodell | , | , |
  | E-17-3 Abschaltbarkeit von de und en | , | , |
  | E-17-4 Sprachmenge als sechster Merker | , | , |
  | E-17-5 Katalogprozess | , | , |
  | E-17-6 Niederlaendische Komposita | , | , |
  | E-17-7 Vergleichsregel `tantivy_version` | , | , |
  | E-17-8 Einheitliche Kettenreihenfolge | , | , |

- **Beleg:** ,
- **Vollzogen am / durch Plan:** ,

### Vollzugs-Checkliste

1. Entscheiddokument vorlegen (Plan 17-04), mit E-17-7 als erster Frage.
2. Freigabe eintragen oder die benannten Aenderungen einarbeiten und erneut
   vorlegen; ohne Freigabe wird kein Requirement als erfuellt gemeldet.
3. Den Vollzugsabschnitt oben datiert fuellen: Datum, gelesener Stand,
   greifender Zweig je Entscheid mit Begruendung, Beleg, Plannummer.
4. Erst danach `backend/src/findling/store/repo.py` und
   `backend/tests/test_upgrade_compatibility.py` anfassen (Plan 17-07).
5. Danach `uv lock --upgrade-package tantivy` und `uv sync` aus `backend/`
   fahren, nie eine Handkante an `backend/uv.lock` (Plan 17-08).
6. Volle Suite und alle Gates fahren (`uv run python -m pytest -q`,
   `uv run ruff check`, `uv run ruff format --check`, `uv run pyright`,
   `uv run vulture`); ein roter Lauf ist ein Befund und wird gelesen, bevor
   irgendetwas geaendert wird.
7. CI-Zusicherung in `.github/workflows/deploy-harp.yml`, den
   Begruendungskommentar in `.github/dependabot.yml` und `THIRD-PARTY.md`
   nachziehen, jeweils mit dem Messbeleg vom 2026-09-23 im Kommentar.
