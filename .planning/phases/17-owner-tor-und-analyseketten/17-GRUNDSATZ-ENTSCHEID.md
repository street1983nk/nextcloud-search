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

Wird in Task 2 dieses Plans gefuellt.

---

## Die fertigen Ersatztexte

Wird in Task 3 dieses Plans gefuellt.

---

## Vollzug am <Datum>

Wird in Task 3 dieses Plans leer angelegt und von Plan 17-04 gefuellt.

### Vollzugs-Checkliste

Wird in Task 3 dieses Plans gefuellt.
