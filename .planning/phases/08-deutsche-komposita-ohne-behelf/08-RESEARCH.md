# Phase 8: Deutsche Komposita ohne Behelf - Research

**Researched:** 2026-09-08
**Domain:** Tokenisierung deutscher Komposita in Tantivy 0.26.0 (`Filter.split_compound`), Konstituentenliste aus `wngerman`, Reindex-Kopplung ueber Versionsmarken
**Confidence:** HIGH fuer die Bestandsaufnahme (alles gegen Quellcode und laufenden Analyzer geprueft), HIGH fuer die zentrale Messung (im echten Debian-Abbild gegen die echte Liste gefahren), MEDIUM fuer die Bauempfehlung (sie braucht einen Owner-Entscheid, weil sie ein Erfolgskriterium der Roadmap beruehrt)

---

## Lesehilfe: wie Aussagen in diesem Bericht gekennzeichnet sind

Dieser Bericht widerspricht der Phasenbeschreibung an zwei Stellen. Deshalb traegt jede
belastbare Aussage ihre Herkunft.

| Marke | Bedeutung |
|---|---|
| `[VERIFIED: <Quelle>]` | In dieser Sitzung mit einem Werkzeug geprueft (Repo-Code mit Datei:Zeile, laufender Analyzer, Debian-Paket im Wegwerf-Container) |
| `[MEASURED: <Lauf>]` | Zahl aus einem Messlauf dieser Sitzung oder aus einer abgenommenen Messreihe des Repositoriums, mit Quelle |
| `[CITED: <URL>]` | Aus offizieller Dokumentation zitiert |
| `[ASSUMED]` | Aus Trainingswissen, in dieser Sitzung nicht geprueft. Braucht Bestaetigung, bevor daraus ein Plan wird |

Umlaute stehen in dieser Datei in deutscher Prosa und in Sprachdaten (Suchbegriffe,
Wortlisteneintraege). Codebezeichner und Dateipfade bleiben ASCII, wie es die Projektregel
verlangt.

---

## Summary

**Die Phasenbeschreibung sucht einen Prefix-Behelf, den es nicht gibt.** Der ausgelieferte
Suchweg von der PHP-Companion-App bis zur Tantivy-Query wurde in dieser Sitzung Datei fuer
Datei durchgegangen. Es steht dort keine Prefix-Query, keine Wildcard, keine `FuzzyTermQuery`
und kein manuelles Anhaengen von Teilwortvarianten. `Filter.split_compound` mit der
mitgelieferten `wngerman`-Liste ist auf `body_de` registriert und greift auf beiden Seiten,
beim Indexieren und beim Query-Parsen, weil beide Seiten denselben registrierten Analyzer
benutzen. Vier der fuenf Erfolgskriterien der Phase sind im ausgelieferten Stand bereits
erfuellt oder brauchen nur noch eine Kleinigkeit.

**Die echte Luecke liegt woanders, und sie ist unangenehmer.** Erfolgskriterium 1 nennt
woertlich den Fall "Genehmigung findet Baugenehmigung". Dieser Fall ist mit Rezept A
nachweislich unerreichbar, und der Grund ist strukturell und gemessen: `Baugenehmigung` hat
genau 14 Zeichen, steht selbst in `/usr/share/dict/ngerman` und faellt damit in das
Laengenfenster 4 bis 14 von Rezept A. Ein Eintrag, der selbst in der Liste steht, wird nie
zerlegt, weil der Splitter leftmost-longest greift. Selbst wenn man ihn entfernt, scheitert
die Zerlegung weiter, weil das noetige Teilwort `bau` nur drei Zeichen hat und die Untergrenze
`MIN_LEN = 4` es ausschliesst. Das ist derselbe dokumentierte Grenzfall wie "Vertrag findet
Mietvertrag" (`docs/german-analyzer.md`, "Known limits"), aber er trifft haeufiger, als die
Doku vermuten laesst: von 21 in dieser Sitzung geprueften Verwaltungskomposita zerfallen
**sieben nicht**, und es sind genau die kurzen, alltaeglichen, die Nutzer tippen.

**Alle naheliegenden Reparaturen wurden gemessen und alle sind schlechter.** Drei
Rezeptvarianten sind im echten Debian-Abbild gegen die echte 276.496-Eintraege-Liste gefahren
worden. Jede loest einzelne Faelle und zerstoert dabei andere, teils katastrophal: bei einem
Fenster ab drei Zeichen verliert die 63 Zeichen lange Kompositum-Fahne ihre Zerlegung
vollstaendig und wird von `remove_long(48)` aus dem Index geworfen, das Dokument ist dann
unter keinem seiner Teile mehr auffindbar. Mehr Eintraege bedeuten also nicht mehr Zerlegung.
Dieses nicht-monotone Verhalten ist der schaerfste Befund der Recherche.

**Primaerempfehlung:** Die Phase baut **keine** Rezeptaenderung. Sie schreibt den gemessenen
Befund fest, holt einen Owner-Entscheid zum Wortlaut von Erfolgskriterium 1 ein, zieht die
heute funktionierenden Kompositafaelle als benannte, rotwerdende Testfaelle in das
CI-Sprachfall-Set ein und baut den einen fehlenden Beweis: einen Test, der den **Weg** ueber
`split_compound` belegt statt nur das Ergebnis (Erfolgskriterium 2). Falls der Owner
Erfolgskriterium 1 woertlich haben will, gibt es genau eine technisch saubere Bauoption, und
sie kostet ein zusaetzliches Indexfeld, einen `SCHEMA_VERSION`-Sprung und einen vollen
Reindex; sie steht unten als Muster 2.

---

## Phase Requirements

| ID | Beschreibung (aus REQUIREMENTS.md) | Wie die Recherche das traegt |
|----|-------------|------------------|
| QUAL-01 | Deutsche Komposita werden ueber eine lizenzkonforme Wortliste zerlegt (Tantivy `split_compound`); die Lizenz der Liste ist AGPL-kompatibel und dokumentiert | **Bereits erfuellt.** Bestandsaufnahme 1, 3, 6 unten: Liste gebaut, im ausgelieferten Weg registriert, Lizenz in Repo (`THIRD-PARTY.md`, `docs/german-analyzer.md`) und im Abbild (`/usr/local/share/findling/COPYING.wngerman`). Die Phase muss hier nur belegen, nicht bauen |
| QUAL-02 | Suchen nach Teilwoertern finden zusammengesetzte Woerter, belegt durch Testfaelle im CI-Sprachfall-Set | **Teilweise erfuellt.** Sprachfall 1 in `integration.yml` faehrt "Genehmigung findet Grundstücksverkehrsgenehmigung" und ist gruen. Die Luecke: nur ein einziger Kompositafall im CI-Set, und der Fall aus Erfolgskriterium 1 ("Baugenehmigung") ist nicht baubar. Siehe "Die zentrale Messung" |
| QUAL-03 | Der offene Endungsvergleich der Verdikte gegen den Generator ist durchgefuehrt und dokumentiert; Befunde fliessen als Testfaelle ein | **Fast erfuellt.** Der Vergleich ist gefahren und bestanden (`docs/measurements/2026-09-nachmessung-m7g/README.md`, Abschnitt 7). Die Luecke: die beiden Befunde ("20 `too_large`-CSV mit Absicht", "`no_text_layer` ist ein voruebergehendes Verdikt") sind dokumentiert, aber nicht als Testfall eingezogen und nicht ausdruecklich als bewusst offen benannt. Das ist Erfolgskriterium 5, und es ist der kleinste Rest der ganzen Phase |

---

## Architectural Responsibility Map

| Faehigkeit | Primaere Schicht | Sekundaere Schicht | Begruendung |
|------------|-----------------|--------------------|-------------|
| Zerlegung deutscher Komposita | Tantivy-Analyzerkette im ExApp-Prozess (`index/analyzer.py`) | keine | Die Zerlegung ist Teil der Tokenisierung und muss auf Index- und Query-Seite identisch sein. Eine zweite Stelle waere ein zweiter Textraum |
| Beschaffung und Fassung der Wortliste | Abbildbau (`backend/Dockerfile`) plus Aufbereitung im Prozess (`index/wordlist.py`) | Datentraeger (`$APP_PERSISTENT_STORAGE/dict/`) | Die Rohliste kommt aus einem Debian-Paket, nie aus dem Netz zur Laufzeit. Das gefilterte Artefakt liegt auf dem Datentraeger, damit der Start nicht jedes Mal 0,25 s filtert |
| Erkennung eines Wortlistenwechsels | Zustandsdatenbank plus `index/open.py::expected_versions` | Statusseite in PHP (`wordlistHash`) | Nur die Zustandsdatenbank kennt die Marke, mit der der bestehende Index wirklich gebaut wurde. Der Vergleich gehoert dorthin, wo beide Seiten vorliegen |
| Erzwingen des Reindex | Poller (`worker/poller.py`, `start_rebuild_on_drift`) | keine | Nur der Poller kann die lokale Generation heben und damit jedes gespeicherte Verdikt veralten lassen |
| Query-Aufbereitung (Filter, Umlautvarianten) | `query/rewrite.py` im Container | keine | Die Zeile muss vor dem Parser aufbereitet werden, und der Parser lebt im Container |
| Berechtigungsgrenze | PHP-Companion (finaler Recheck) | SQLite-ACL-Vorfilter im Container | Unveraendert. Diese Phase fasst sie nicht an |

---

## Bestandsaufnahme: die neun Auftraege, beantwortet

### 1. Ist `Filter.split_compound` im ausgelieferten Weg registriert, oder existiert der Code nur?

**Er ist registriert und er greift.** `[VERIFIED: Repo-Code]`

Die Kette steht in `backend/src/findling/index/analyzer.py:160-170`:

```python
TextAnalyzerBuilder(Tokenizer.simple())
    .filter(Filter.lowercase())
    .filter(Filter.split_compound(list(constituents)))
    .filter(Filter.custom_stopword(list(FUGEN)))
    .filter(Filter.stopword("german"))
    .filter(Filter.remove_long(MAX_TOKEN_CHARS))
    .filter(Filter.stemmer("german"))
    .build()
```

Die Registrierung ist an das Oeffnen des Index gekoppelt, `backend/src/findling/index/open.py:98`:

```python
index.register_tokenizer(TOKENIZER_DE, cached_german_analyzer(wordlist_hash(constituents), constituents))
```

`open_index` ist die einzige Stelle, die einen Index oeffnen darf. Ein Test laeuft ueber das
Paket und meldet jede zweite Stelle, die `Index(...)` oder `Index.open(...)` ruft
(`backend/tests/test_index_open.py`). `[VERIFIED: Repo-Code, index/open.py:1-15]`

Die zwei Aufrufer im laufenden Betrieb, beide mit der echten Liste:

| Seite | Datei:Zeile | Aufruf |
|---|---|---|
| Schreiben (Poller) | `backend/src/findling/worker/poller.py:335-336` | `artifact = build_artifact(); index = open_index(resolved.index_dir, artifact.entries)` |
| Lesen (Suche) | `backend/src/findling/api/resources.py:315` | `index = open_index(resolved.index_dir, build_artifact().entries)` |

Es gibt **einen** Aufrufer mit leerer Liste: `backend/src/findling/tools/index_status.py:111`
ruft `open_index(directory, ())`. Das ist ein Diagnosewerkzeug, das nur Metadaten liest und
nie sucht; es liegt ausserhalb des Suchwegs. Trotzdem ist es die einzige Stelle im Repo, an
der ein Index ohne Konstituentenliste geoeffnet wird, und der Plan sollte einen Satz dazu
enthalten, warum das unschaedlich ist. `[VERIFIED: Repo-Code]`

### 2. Gibt es im ausgelieferten Suchweg einen Prefix-Behelf?

**Nein.** `[VERIFIED: Repo-weite Suche ueber Python und PHP]`

Der Weg vollstaendig:

```
Unified Search (Nextcloud)
  -> php/lib/Search/Provider.php:187   $term = trim($query->getTerm())        [unveraendert weitergereicht]
  -> php/lib/Search/Provider.php:258   $this->exApp->searchCandidates(...)    [AppAPI-Proxy]
  -> backend/src/findling/api/search.py:194   rewritten = build_query(side.index, text, title_only=...)
  -> backend/src/findling/query/rewrite.py:317 build_query()
       Schritt 1  Tiefenwaechter fuer Klammern (SEARCH_QUERY_MAX_DEPTH)
       Schritt 2  carried_operators() / carries_one_term()  auf der Rohzeile
       Schritt 3  normalize() -> NFC
       Schritt 4  extract_filters()      schneidet "type:" heraus
       Schritt 5  add_umlaut_variants()  "kuendigung" -> "(kuendigung OR kündigung)"
       Schritt 6  index.parse_query_lenient(..., conjunction_by_default=True, allow_regexes=False)
  -> Tantivy-Query gegen body_de / body_en / name / title
```

In keinem dieser Schritte entsteht eine Prefix-, Wildcard- oder Fuzzy-Query. Die
Umlautvariante (`add_umlaut_variants`) ist die einzige Umschreibung, sie erzeugt eine
`OR`-Alternative ueber zwei vollstaendige Terme und ist ausdruecklich als
Nicht-Woerterbuch-Mechanik dokumentiert (`query/rewrite.py:107-125`). Regulaere Ausdruecke
sind ausgeschaltet (`allow_regexes=False`, `query/rewrite.py:389`). `[VERIFIED: Repo-Code]`

Auf der PHP-Seite wird der Suchbegriff nur getrimmt und weitergereicht; es gibt dort keine
Termmanipulation. `[VERIFIED: php/lib/Search/Provider.php:187]`

**Konsequenz fuer die Planung:** Der Satz "wo noch ein Prefix-Behelf steht" in der
Roadmap-Phasenbeschreibung stammt aus dem Semantiklauf vom 05.09.2026 und ist durch die
Arbeit der Phase 06.1 ueberholt. Es gibt nichts zurueckzubauen. Erfolgskriterium 2 verlangt
darum nur noch **den Beweis**, nicht den Umbau.

### 3. Welcher Analyzer liegt auf welchem Feld, und greift die Zerlegung beim Indexieren, beim Query-Parsen oder in beiden?

**In beiden, und zwar zwangslaeufig.** `[VERIFIED: Repo-Code plus laufender Analyzer]`

Das Schema speichert nur den **Namen** eines Tokenizers, nie den Tokenizer selbst
(`index/analyzer.py:75-80`). `open_index` registriert vier Namen:

| Name | Kette | Felder |
|---|---|---|
| `de` | simple, lowercase, `split_compound`, `custom_stopword(FUGEN)`, `stopword("german")`, `remove_long(48)`, `stemmer("german")` | `body_de` |
| `en` | simple, lowercase, `ascii_fold`, `stopword("english")`, `remove_long(48)`, `stemmer("english")` | `body_en` |
| `name` | simple, lowercase, `ascii_fold`, `remove_long(60)` | `name`, `title` |
| `stored_only` | simple, `remove_long(1)`, verwirft jeden Token | `path` |

`parse_query_lenient` benutzt fuer jedes Feld genau den Analyzer, der unter dem im Schema
hinterlegten Namen registriert ist. Weil Index- und Leseseite beide durch `open_index` gehen,
ist die Kette auf beiden Seiten dieselbe Objektidentitaet (per-Prozess-Singleton ueber
`cached_german_analyzer`, `index/analyzer.py:196-210`).

Praktisch heisst das fuer den Kompositafall:

```
Indexieren:  "Die Grundstücksverkehrsgenehmigung wurde erteilt."
             -> grundstuck, verkehr, genehm            (drei Terme im Index)
Abfragen:    "Genehmigung"
             -> genehmigung  (steht selbst in der Liste, wird nicht zerlegt)
             -> genehm       (Stemmer)                 -> Termtreffer
```

`[MEASURED: Lauf dieser Sitzung im Debian-Abbild, siehe unten]`

Der bestehende Test, der genau diesen Weg absichert, ist
`backend/tests/test_index_open.py:218` (`test_the_registered_german_chain_splits_compounds`).
Er schreibt ein Dokument mit "Kündigungsfrist" und fragt "frist" ab. Er beweist damit den Weg
schon zu einem guten Teil, aber er hat keine Gegenprobe: er wuerde auch dann gruen bleiben,
wenn eine kuenftige Aenderung die Zerlegung durch eine Prefix-Query ersetzte. Das ist die
Luecke aus Erfolgskriterium 2 ("ein Test belegt den Weg statt nur das Ergebnis").

### 4. Was hat der Endungsvergleich aus QUAL-03 ergeben?

**Bestanden, ohne eine einzige unerklaerte Abweichung.**
`[MEASURED: docs/measurements/2026-09-nachmessung-m7g/README.md, Abschnitt 7]`

Der Vergleich lief in zwei Haelften: der Generator aus dem Samen `phase5-full` gerechnet
(`skripte/66-generator-endungen.py`, 50.000 Dateien), der Bestand aus `state.db` gelesen
(`skripte/68-bestand-endungen.py`). Dreizehn Endungen, Summe 50.000 gegen 49.980 indexiert
plus 20 uebersprungen.

| Befund | Anzahl | Stand heute |
|---|---|---|
| `csv` uebersprungen mit `too_large` | 20 | Absicht, es ist die Generatorkategorie `oversize`. Dokumentiert, **kein Testfall** |
| Die 37 Verdikte aus 06-11 vollstaendig zugeordnet | 37 | Deckungsgleich. Dokumentiert, kein Testfall noetig |
| Nebenbefund: `no_text_layer` ist ein voruebergehendes Verdikt | n/a | Dokumentiert, **kein Testfall**, und **nicht ausdruecklich als bewusst offen benannt** |

**Was fuer Erfolgskriterium 5 fehlt:** genau zwei Entscheidungen, jede in einem Satz. Fuer die
20 `oversize`-CSV: entweder ein Testfall, der `too_large` gegen den 50-MB-Deckel prueft (ein
solcher existiert moeglicherweise schon in `backend/tests/test_extract_errors.py`, das muss
der Plan pruefen), oder die ausdrueckliche Feststellung, dass der Messbericht der Beleg ist.
Fuer den `no_text_layer`-Nebenbefund: entweder ein Testfall, der belegt, dass eine Datei nach
dem zweiten Durchgang `indexed` traegt, oder die ausdrueckliche Feststellung, dass das
bewusst offen bleibt. **Ohne diese zwei Saetze ist QUAL-03 formal nicht abgeschlossen,
obwohl die Messung laengst bestanden ist.**

### 5. Wo liegt das CI-Sprachfall-Set und welche Kompositafaelle stehen drin?

`.github/workflows/integration.yml:1403`, Job-Schritt "The seven German language cases, as the
owner". Sieben Faelle, jeder mit eigener Fehlermeldung, jeder gegen die echte OCS-Route mit
echtem Nutzer. `[VERIFIED: Repo-Code]`

| # | Fall | Suchbegriff | Traegt Kompositum? | Stand |
|---|---|---|---|---|
| 1 | Kompositum ueber einen Bestandteil | `Genehmigung` | **ja**, `Grundstücksverkehrsgenehmigung` in `09-bescheid.pdf` | gruen, prueft zusaetzlich Trefferzahl, Dateiname, Textausschnitt und Markup-Freiheit |
| 2 | Zweites Kompositum, anderes Format | `Frist` | **ja**, `Kündigungsfrist` in `10-kuendigung.docx` | gruen |
| 3 | Ausgeschriebener Umlaut | `Mueller` | nein | gruen |
| 4 | Nominalflexion | `Vertrag` findet `Verträge` | nein | gruen |
| 5 | Phrase | `"drei Monate"` | nein | gruen |
| 6 | Ausschluss plus Kontrolle | `bescheid -frist` | nein | gruen |
| 7 | Dateityp | `type:pdf bescheid` | nein | gruen |

Dazu die Gegenprobe: ein zweiter Nutzer sucht `Genehmigung` und findet genau die eine
freigegebene Datei (`integration.yml:1497`).

**Nichts ist rot, nichts ist geskippt.** Die Luecke ist die Breite: zwei Kompositafaelle,
beide mit langen, seltenen Woertern. Der Fall aus Erfolgskriterium 1 (kurzes, alltaegliches
Kompositum) fehlt, und er ist, wie unten gezeigt, nicht baubar.

Die Python-Suite ergaenzt das mit sechzehn Kompositafaellen Token fuer Token
(`backend/tests/test_analyzer.py:69-92`, `COMPOUNDS`) und zehn Woertern, die nicht zerfallen
duerfen (`UNSPLIT`, Zeile 96-107). Die Fixture dafuer ist die gemessene Teilmenge der echten
Liste (`backend/tests/fixtures/constituents_de.txt`, 172 Eintraege), verifiziert byteidentisch
zur echten Liste fuer genau diese Eingaben. `[VERIFIED: Repo-Code, Docstring test_analyzer.py:1-19]`

### 6. Was steht in `docs/german-analyzer.md`, und was fehlt fuer Erfolgskriterium 3?

**Erfolgskriterium 3 ist vollstaendig erfuellt.** `[VERIFIED: Repo-Code plus Container-Lauf]`

| Anforderung | Wo erfuellt |
|---|---|
| Lizenz im Repo | `THIRD-PARTY.md:28-42`, `docs/german-analyzer.md`, Abschnitt "Licence and provenance" |
| Herkunft im Repo | Debian-Paket `wngerman` 20161207-15, Quellpaket `igerman98`, Upstream Björn Jacke, Maintainer Roland Rosenfeld |
| Fassung im Repo | `20161207-15`, exakt gepinnt im Dockerfile |
| Lizenztext im Abbild | `backend/Dockerfile:206-211`: `apt-get install -y --no-install-recommends wngerman=20161207-15`, dann `test -s /usr/share/doc/wngerman/copyright` und `install -D -m 0444 ... /usr/local/share/findling/COPYING.wngerman` |
| AGPL-Vertraeglichkeit begruendet | `docs/german-analyzer.md`: GPL-2+ erlaubt den Wechsel auf GPLv3, GPLv3 ist mit AGPL-3.0 vertraeglich. Die drei Pflichten sind einzeln aufgezaehlt |
| Pruefbarkeit | `THIRD-PARTY.md:259` nennt den Befehl, der Zeilenzahl und Lizenzkopf im Abbild nachsieht |

Gegengeprueft im Wegwerf-Container: `/usr/share/dict/ngerman` hat **356.010 Zeilen**, exakt die
Zahl aus der Doku. `[MEASURED: docker run python:3.13-slim-trixie, apt-get install wngerman, 2026-09-08]`

Der Plan muss hier **nichts bauen**, nur belegen. Ein sinnvoller Beleg waere ein CI-Schritt,
der im gebauten Abbild prueft, dass `COPYING.wngerman` existiert und nicht leer ist. Ob ein
solcher Schritt schon existiert, ist offen (siehe Open Questions).

### 7. Wie ist die Reindex-Mechanik heute gebaut, und wo kaeme ein Wortlisten-Digest hin?

**Der Wortlisten-Digest steht bereits neben `schema_version` und `analyzer_version`.
Erfolgskriterium 4 ist gebaut und getestet.** `[VERIFIED: Repo-Code plus Testdateien]`

`backend/src/findling/index/open.py:126-140`:

```python
def expected_versions(digest: str) -> dict[str, str]:
    return {
        "schema_version": str(SCHEMA_VERSION),      # 1
        "index_version": str(INDEX_VERSION),        # 1, lokale Generation
        "analyzer_version": str(ANALYZER_VERSION),  # 1
        "wordlist_hash": digest,                    # <- die Marke aus Kriterium 4
        "tantivy_version": TANTIVY_VERSION,         # "tantivy v0.26.0, index_format v7"
    }
```

Der Digest wird ueber die **gefilterte** Liste gebildet, nicht ueber die Quelldatei
(`index/wordlist.py::wordlist_hash`). Begruendung steht im Code: ein Debian-Punktrelease, das
nur Zeilen umsortiert, darf keinen Reindex erzwingen; ein geaendertes Fenster muss.

Die Kette bis zum sichtbaren Reindex:

| Schritt | Ort | Was passiert |
|---|---|---|
| 1 Marken erwarten | `worker/poller.py:321` | `expected = expected_versions(build_artifact().digest)` beim Start |
| 2 Marken saeen | `worker/poller.py:322` | `open_store(..., meta=expected)` fuellt nur fehlende Marken, ueberschreibt nie |
| 3 Drift erkennen | `worker/poller.py:323` | `start_rebuild_on_drift(store, expected)` |
| 4 Generation heben | `index/open.py:169-200` | `index_version` plus 1, dazu ein Fingerabdruck `rebuild_for`, damit ein Neustart mitten im Umbau nicht neu zaehlt |
| 5 Verdikte veralten | `store/repo.py::is_unchanged` | Jede Datei wird beim naechsten Crawl wirklich neu gelesen |
| 6 Banner anzeigen | `api/status.py:334`, `api/resources.py::version_drift` | `wordlistHash` und `reindexRequired` gehen an die PHP-Statusseite (`AdminViewService.php:1806`) |
| 7 Marken stempeln | `index/open.py::stamp_after_rebuild` | Erst wenn kein lebendes Verdikt mehr eine aeltere Generation traegt |

Bestehende Tests: `test_index_open.py:296, 399, 512`, `test_status_endpoint.py:391`,
`test_store_repo.py:127, 173, 190`, `test_read_side.py:266`, `test_index_status.py:94`.
`[VERIFIED: Repo-Code]`

**Konsequenz fuer die Planung:** Erfolgskriterium 4 ist **nicht zu bauen**. Der Plan muss es
belegen und darf hoechstens die Beweisfuehrung schaerfen, etwa mit einem Ende-zu-Ende-Fall,
der eine Wortliste austauscht und das Banner auf der Statusseite erscheinen sieht.

### 8. Was bedeutet Phase 7 fuer diese Phase?

**Weniger als der Name vermuten laesst, und das ist wichtig.** `[VERIFIED: Phase-7-SUMMARY-Dateien]`

Der "faule Bau" aus Plan 07-03 betrifft `_build_the_cutter`, also **Tokenizer, Splitter und
Engine der zweiten Spur**. Der dort gemeinte "Splitter" ist der `semantic-text-splitter`, der
Dokumente in Chunks schneidet, **nicht** der Kompositasplitter dieser Phase. Die
300-Sekunden-Karenz (`LOAD_RETRY_SECONDS`) gehoert zur Embedding-Engine nach einem
gescheiterten Laden und beruehrt die Analyzerkette nicht.
`[VERIFIED: 07-03-SUMMARY.md:18, 127; 07-04-SUMMARY.md:112, 170]`

Was Phase 7 fuer diese Phase trotzdem bedeutet:

- **Das Speicherbudget ist eng und dokumentiert.** Die Grundlast liegt bei 693,4 MB, die
  Gesamtspitze bei 1.812,7 MB `[MEASURED: 2026-09-nachmessung-m7g, Abschnitte 3 und 14]`. Das
  deutsche Automat kostet gemessen 41,4 MiB im `full`-Rezept und 7,3 MiB im `nouns`-Rezept
  `[MEASURED: docs/german-analyzer.md, Tabelle "Measured numbers"]`. Jede Rezeptaenderung
  dieser Phase veraendert diese Zahl und gehoert damit in die Vergleichsmessung der Phase 10.
- **Der Wortlisten-Digest-Check beim Start ist billig und faellt nicht unter den faulen Bau.**
  `build_artifact()` liest das Artefakt vom Datentraeger (0,25 s beim Bauen, danach ein
  Dateilesen plus Digestvergleich) und hat einen eigenen Prozess-Cache mit Zaehler
  (`wordlist.py::read_count`). Der 41-MiB-Automat entsteht erst in `open_index`, also im
  Poller beim Start und auf der Leseseite bei der ersten Suche. Ein zusaetzlicher
  Digest-Vergleich beim Start kostet daher **nichts Neues**.
- **Der Budgetposten fehlt in CLAUDE.md.** Die RAM-Tabelle kennt "Tokenizer und Splitter"
  nicht, obwohl der Posten gemessen groesser ist als das Modell
  `[VERIFIED: 07-03-SUMMARY.md:258-259]`. Wenn diese Phase am Automaten dreht, gehoert der
  Posten nachgetragen.
- **Ein offener Punkt der Phase 7 grenzt an:** DI-07-02, `REQUEST_TIMEOUT_SECONDS = 1.5` in
  `php/lib/Service/ExAppService.php:89` deckelt jeden Containeraufruf. Ein groesserer Automat
  verlangsamt die erste Suche nach dem Start. Wenn diese Phase die Liste vergroessert, muss
  der Plan das gegen diese Decke rechnen.

### 9. `Filter.split_compound`-Semantik in tantivy-py 0.26.0

Signatur, gelesen im installierten Paket `[VERIFIED: backend/.venv/Lib/site-packages/tantivy/tantivy.pyi:648]`:

```python
class Filter:
    @staticmethod
    def split_compound(constituent_words: list[str]) -> Filter: ...
```

Verhalten, in dieser Sitzung gegen den laufenden Filter gemessen
`[MEASURED: backend/.venv, tantivy 0.26.0, 2026-09-08]`:

| Eigenschaft | Befund | Beleg |
|---|---|---|
| Volldekomposition noetig | Ja. Laesst sich der Token nicht restlos in aufeinanderfolgende Listentreffer zerlegen, bleibt er **unveraendert** | `chain(["brot","automat"]).analyze("Brotbackautomat")` -> `['brotbackautomat']` |
| Originaltoken bei Erfolg | Wird **verworfen**, nur die Teile bleiben | `chain(["dampf","schiff","fahrt"]).analyze("Dampfschifffahrt")` -> `['dampf','schiff','fahrt']` |
| Grossschreibung | **Case-sensitiv.** Ohne `lowercase` davor greift der Filter gar nicht | `Filter.split_compound(liste).analyze("Baugenehmigung")` ohne `lowercase` -> `['Baugenehmigung']` |
| Mindestlaenge im Filter | **Keine.** Die Untergrenze entsteht ausschliesslich aus unserer Liste (`MIN_LEN = 4`) | Doku nennt keine, gemessen greift ein Dreizeichen-Eintrag |
| Ganzwort in der Liste | Der Token bleibt ganz, weil leftmost-longest den ganzen Token als einen Treffer nimmt | `chain(base + ["bau", "baugenehmigung"]).analyze("Baugenehmigung")` -> `['baugenehmigung']` |
| Stellung zum Stemmer | Muss **vor** dem Stemmer stehen, ein gestemmtes Kompositum trifft keinen Listeneintrag mehr | dokumentiert und getestet, `test_analyzer.py` |

Offizielle Formulierung: "Words only will be split if they can be fully decomposed into
consecutive matches into the given dictionary."
`[CITED: https://docs.rs/tantivy/latest/tantivy/tokenizer/struct.SplitCompoundWords.html]`

**Ranking-Folge, ausdruecklich:** Weil der Originaltoken bei erfolgreicher Zerlegung
verschwindet, steht das ganze Kompositum **nicht** im Index. Eine Suche nach dem ganzen Wort
funktioniert trotzdem, weil die Query-Seite denselben Analyzer benutzt und dieselben Teile
erzeugt. Sie funktioniert aber als **Konjunktion ueber die Teile**
(`conjunction_by_default=True`, `query/rewrite.py:388`) und nicht als ein Term. Ein Dokument,
das zufaellig alle Teile an verschiedenen Stellen traegt, kann deshalb neben dem Dokument
stehen, das das ganze Wort traegt. Das ist der Preis der Zerlegung und ist heute nirgends
dokumentiert. `[VERIFIED: Repo-Code plus gemessene Filtersemantik]`

---

## Die zentrale Messung: warum "Genehmigung findet Baugenehmigung" nicht baubar ist

Alle Zahlen dieses Abschnitts stammen aus einem Lauf im echten Basisabbild
`python:3.13-slim-trixie` mit dem echten Paket `wngerman=20161207-15` und
`tantivy==0.26.0`, gegen die echte 356.010-Zeilen-Datei.
`[MEASURED: docker run, 2026-09-08, Skript im Scratchpad dieser Sitzung]`

### Der Befund in einem Satz

`Baugenehmigung` hat 14 Zeichen und steht selbst in `/usr/share/dict/ngerman`. Rezept A haelt
alle Woerter der Laenge 4 bis 14, also wird `baugenehmigung` selbst ein Listeneintrag, und ein
Eintrag wird nie zerlegt.

```
Baugenehmigung: 1   (grep -c -ix in /usr/share/dict/ngerman)
Bau:            1
Genehmigung:    1
Mietvertrag:    1
Bebauungsplan:  1
```

Selbst wenn man `baugenehmigung` aus der Liste entfernt, scheitert die Zerlegung weiter, weil
`bau` nur drei Zeichen hat und durch `MIN_LEN = 4` ausgeschlossen ist. Beide Wege sind
gemessen:

```
Liste ohne "bau", ohne "baugenehmigung":  Baugenehmigung -> ['baugenehmigung']
Liste mit  "bau", ohne "baugenehmigung":  Baugenehmigung -> ['bau', 'genehmigung']
Liste mit  "bau", mit  "baugenehmigung":  Baugenehmigung -> ['baugenehmigung']
```

### Die Reichweite des Problems ist groesser als dokumentiert

Von 21 in dieser Sitzung mit Rezept A geprueften Verwaltungskomposita zerfallen **sieben
nicht**. Die Doku spricht von "14 von 16", aber ihre sechzehn sind lange, seltene Woerter.
Die kurzen, haeufigen sind die, die Nutzer tippen, und die stehen mit hoher Wahrscheinlichkeit
selbst in `ngerman`.

| Kompositum | Rezept A (ausgeliefert) | Ueber ein Teilwort auffindbar? |
|---|---|---|
| Grundstücksverkehrsgenehmigung | `grundstuck, verkehr, genehm` | ja |
| Kündigungsfrist | `kundig, frist` | ja |
| Sitzungsvorlage | `sitzung, vorlag` | ja |
| Haushaltssatzung | `haushalt, satzung` | ja |
| Jahresabschluss | `jahr, abschluss` | ja |
| Betriebskostenabrechnung | `betriebskost, abrechn` | ja |
| Krankenversicherung | `krank, versicher` | ja |
| Rechnungsnummer | `rechnung, numm` | ja |
| Datenschutzgrundverordnung | `datenschutz, grund, verordn` | ja |
| Bundesausbildungsförderungsgesetz | `bund, ausbild, forder, gesetz` | ja |
| Rindfleisch...uebertragungsgesetz (63 Z.) | sechs Token | ja |
| Dampfschifffahrt | `dampfschiff, fahrt` | ja |
| Aufenthaltserlaubnis | `aufenthalt, erlaubnis` | ja |
| Gewerbeanmeldung | `gewerb, anmeld` | ja |
| **Mietvertrag** | `mietvertrag` | **nein** (dokumentiert) |
| **Bebauungsplan** | `bebauungsplan` | **nein** (dokumentiert) |
| **Baugenehmigung** | `baugenehm` | **nein**, neu |
| **Bauantrag** | `bauantrag` | **nein**, neu |
| **Baukosten** | `baukost` | **nein**, neu |
| **Arbeitsvertrag** | `arbeitsvertrag` | **nein**, neu |
| **Steuerbescheid** | `steuerbescheid` | **nein**, neu |

Alle zehn Woerter aus `UNSPLIT` bleiben in Rezept A unversehrt. Die Praezision ist also
einwandfrei; der Verlust liegt allein bei der Trefferausbeute.

**Ein achter, bisher nirgends dokumentierter Fall:** Die ASCII-Transkription eines Kompositums
wird von **keinem** Rezept zerlegt. `Grundstuecksverkehrsgenehmigung` (ausgeschriebene
Umlaute) ergibt in jeder gemessenen Variante `grundstuecksverkehrsgenehm`, ein einziger Token.
Die Query-Seite bildet zwar Umlautvarianten (`add_umlaut_variants`), aber die **Index**-Seite
tut das nicht. Ein Dokument, das Umlaute ausgeschrieben traegt, etwa aus einem Altsystem oder
einem OCR-Lauf mit verlorenen Umlautpunkten, ist deshalb ueber seine Teilwoerter nicht
auffindbar. Das ist eine reale Luecke fuer deutsche Altbestaende und gehoert entweder als
Testfall oder als benannter Grenzfall in die Doku.

### Die drei gemessenen Reparaturversuche, und warum alle schlechter sind

| Variante | Eintraege | Loest | Zerstoert |
|---|---|---|---|
| **A** 4..14, alle Woerter (ausgeliefert) | 276.496 | Grundlage | 7 der 21 nicht zerlegt |
| **A2** A ohne selbst zerlegbare Eintraege | 109.857 | Bebauungsplan, Arbeitsvertrag | `Steuerbescheid` -> `teu, bescheid`; `Datenschutzgrundverordnung` -> `dat, schutz, ...`; `Haushaltssatzung` -> `haus, halt, satzung`; `Betriebskostenabrechnung` zerfaellt zu `betrieb, kost, abrechn` (genau die Uebersplittung von Rezept D). **Baugenehmigung weiterhin nicht** |
| **A3** 3..14, alle Woerter | 277.074 | Baukosten | `Kündigungsfrist` -> `kundig, sfr`; **`Rindfleisch...gesetz` -> `[]`, das Dokument verschwindet** |
| **A4** 3..14 ohne selbst zerlegbare Eintraege | 86.718 | **Baugenehmigung, Bauantrag, Baukosten**, Arbeitsvertrag, Bebauungsplan | `Sitzungsvorlage` zerfaellt nicht mehr; `Bundesausbildungsförderungsgesetz` -> `bund, sau, bildung, ...`; `Gewerbeanmeldung` -> `gew, erb, anmeld`; `Haushaltssatzung` -> `hau, halt, satzung`; `Steuerbescheid` -> `teu, bescheid`; **`Rindfleisch...gesetz` -> `[]`** |

Bemerkenswert: in **keiner** Variante zerfaellt eines der zehn Alltagswoerter aus `UNSPLIT`.
Ein Test, der nur `UNSPLIT` prueft, wuerde jede dieser Verschlechterungen durchwinken. Das ist
die genaue Form des falschen Sicherheitsgefuehls, vor dem der Docstring von
`test_analyzer.py` warnt.

### Der schaerfste Befund: mehr Eintraege koennen weniger Zerlegung bedeuten

Gegengeprueft mit ausgeschaltetem `remove_long`, damit die Ursache eindeutig ist:

```
Rezept A  (4..14): 9 Token, laengster 13 Zeichen
   ['rindfleisch','etikettierung','s','überwachung','s','aufgaben','übertragung','s','gesetz']
Rezept A3 (3..14): 1 Token, laengster 63 Zeichen
   ['rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz']
```

Die Zerlegung **scheitert** bei A3, sie wird nicht etwa nur anders. Danach greift
`remove_long(48)` und wirft den 63-Zeichen-Token weg, das Ergebnis ist die leere Tokenliste
und das Dokument ist unter keinem seiner sechs Teile mehr auffindbar. Ursache ist das
leftmost-longest-Verhalten der zugrundeliegenden Automatensuche: ein laengerer Treffer weiter
links kann den Weg in eine Sackgasse fuehren, aus der es keinen Rueckweg gibt. Weder `rin`
noch `ung` sind in A3 enthalten, es ist also kein trivialer Fragmenttreffer, sondern ein
echter Pfadwechsel.

**Fuer die Planung heisst das:** Jede Aenderung an der Liste ist eine Aenderung mit
unvorhersehbarem Vorzeichen. Sie darf nur gegen eine breite, gemessene Fallsammlung gefahren
werden, und die Fallsammlung muss beide Richtungen pruefen, gewonnene und **verlorene**
Zerlegungen.

---

## Empfehlung: was diese Phase bauen sollte

### Was sie nicht bauen sollte

- **Keine Rezeptaenderung.** Alle vier gemessenen Varianten sind netto schlechter. Eine
  Aenderung erzwingt zusaetzlich einen vollen Reindex (Digest wandert), kostet auf der
  Zielhardware Stunden und muesste in Phase 10 neu gemessen werden.
- **Keinen Prefix-Behelf, keine Wildcard, keine Fuzzy-Query** als Ersatz. Erfolgskriterium 2
  schliesst das ausdruecklich aus, und die Recherche hat gezeigt, dass heute keiner existiert.
- **Keine Synonymliste.** `docs/german-analyzer.md` hat das bereits mit Begruendung
  abgelehnt (zweite Datei, zweite Lizenz, wirkt auf jede Sprache, der erste Eintrag zieht
  hundert nach).

### Was sie bauen sollte, in der Reihenfolge des Nutzens

1. **Den Owner-Entscheid zu Erfolgskriterium 1 einholen.** Der Wortlaut "Genehmigung findet
   Baugenehmigung" ist mit Rezept A nicht erfuellbar. Drei Wege stehen offen, und die
   Entscheidung gehoert nicht dem Planer: (a) das Kriterium auf einen belegbaren Fall
   umformulieren, (b) die dokumentierte Grenze annehmen und den Fall als benannten
   Nicht-Fall in die Doku ziehen, (c) Muster 2 unten bauen. Der Plan muss diesen Entscheid
   als `checkpoint:human-verify` fuehren, bevor irgendetwas an der Tokenisierung entsteht.
2. **Den Wegbeweis fuer Erfolgskriterium 2.** Ein Test, der belegt, dass die Zerlegung ueber
   `split_compound` laeuft und nicht ueber eine Prefix-Query. Muster 1 unten.
3. **Das CI-Sprachfall-Set um belegbare Kompositafaelle verbreitern.** Heute zwei von sieben.
   Kandidaten mit gemessener Zerlegung: `Satzung` findet `Haushaltssatzung`, `Abschluss`
   findet `Jahresabschluss`, `Versicherung` findet `Krankenversicherung`. Jeder neue Fall
   braucht ein Wort, das in genau einer Korpusdatei steht (`UNIQUE_TERMS` in
   `scripts/dev/build_corpus.py` erzwingt das).
4. **Den Regressionswaechter ueber die Zerlegung.** Eine Fallsammlung mit erwarteten Tokens
   fuer die 21 Komposita oben, die rot wird, sobald eine bisher funktionierende Zerlegung
   verloren geht. `test_analyzer.py::COMPOUNDS` ist die vorhandene Form; sie muss um die
   sieben Nicht-Faelle als ausdrueckliche Negativzeilen und um den 63-Zeichen-Fall als
   "darf nie leer werden" ergaenzt werden.
5. **Die zwei fehlenden Saetze fuer QUAL-03.** Siehe Bestandsaufnahme 4.
6. **Die Doku nachziehen.** `docs/german-analyzer.md`, Abschnitt "Known limits": die Liste der
   nicht zerlegbaren Alltagskomposita, der ASCII-Transkriptionsfall und der
   Nicht-Monotonie-Befund gehoeren dorthin, jeder mit seiner Messung.

---

## Architecture Patterns

### Systemdiagramm: der Weg eines Suchbegriffs bis zum Term

```
Nutzer tippt "Genehmigung" in die Unified Search
        |
        v
[Nextcloud Unified Search] ruft alle Provider parallel, Gruppenbudget 2.500 ms
        |
        v
[PHP: Search/Provider.php]  trim(term), sonst keine Manipulation
        |  exAppRequest, hartes Timeout 1.500 ms je Aufruf
        v
[FastAPI: api/search.py::one_round]
        |
        v
[query/rewrite.py::build_query]
        |  Klammertiefe? --> zu tief: leere Query, Ende
        |  Operatoren und Einwortfrage auf der ROHZEILE lesen
        |  NFC-Normalisierung
        |  "type:"-Filter herausschneiden
        |  Umlautvarianten: kuendigung -> (kuendigung OR kündigung)
        v
[Index.parse_query_lenient]  waehlt je Feld den REGISTRIERTEN Analyzer
        |
        +--> body_de: Analyzer "de"
        |       simple -> lowercase -> split_compound(276.496) -> custom_stopword(FUGEN)
        |       -> stopword(german) -> remove_long(48) -> stemmer(german)
        |       "genehmigung" bleibt ganz (steht in der Liste) -> "genehm"
        |
        +--> body_en: Analyzer "en"      (boost 0.8)
        +--> name/title: Analyzer "name" (boost 3.0 / 2.0)
        v
[index/search.py::candidates]  BM25 plus Vektorseite, RRF-Verschmelzung
        |
        v
[SQLite-ACL-Vorfilter]  Beschleunigung, keine Grenze
        |
        v
[PHP: finaler Recheck ueber getUserFolder()]  <-- die Sicherheitsgrenze
        |
        v
Trefferliste

Auf der Schreibseite dieselbe Kette, dasselbe Analyzer-Objekt:
[worker/poller.py] -> [index/open.py::open_index] -> [index/writer.py]
   "Die Grundstücksverkehrsgenehmigung wurde erteilt."
   -> grundstuck, verkehr, genehm   (drei Terme, das Ganzwort steht NICHT im Index)
```

### Muster 1: den Weg beweisen, nicht das Ergebnis (Erfolgskriterium 2)

**Was:** Ein Test, der gruen bleibt, wenn die Zerlegung ueber `split_compound` laeuft, und
**rot** wird, wenn jemand sie durch eine Prefix-Query oder eine andere Umschreibung ersetzt.

**Wann:** Genau einmal, in `backend/tests/test_index_open.py` neben
`test_the_registered_german_chain_splits_compounds`.

**Warum ein Trefferzaehler dafuer nicht reicht:** `_hits(index, "frist") == 1` waere auch mit
einer Prefix-Query gruen. Der Test muss die Aussage machen, die nur die Zerlegung erfuellt.

Drei Bausteine, die zusammen den Weg festnageln:

```python
# a) Negativkontrolle: dieselbe Kette OHNE den Splitter findet das Teilwort nicht.
#    Beweist, dass der Treffer aus split_compound kommt und aus nichts anderem.
def test_without_the_splitter_the_constituent_finds_nothing(index_dir: Path) -> None:
    ...

# b) Die Query-Seite erzeugt genau die Terme der Index-Seite, nicht mehr.
#    Beweist, dass beide Seiten denselben Analyzer benutzen.
def test_query_and_index_side_produce_the_same_terms(...) -> None:
    analyzer = cached_german_analyzer(digest, constituents)
    assert analyzer.analyze("Kündigungsfrist") == ["kundig", "frist"]
    assert analyzer.analyze("Frist") == ["frist"]

# c) Die Gegenprobe gegen einen Behelf: ein Wort, das ein PRAEFIX des Kompositums ist,
#    aber kein Konstituent, darf NICHT treffen.
#    Eine Prefix-Query wuerde hier treffen, split_compound nicht.
def test_a_mere_prefix_of_the_compound_does_not_hit(index_dir: Path) -> None:
    _write(index, body="Die Kündigungsfrist beträgt drei Monate.")
    assert _hits(index, "kündigungsf") == 0     # Praefix, kein Konstituent
    assert _hits(index, "frist") == 1           # Konstituent
```

Baustein (c) ist der eigentliche Waechter. Er ist billig, er braucht kein neues Werkzeug, und
er wird genau dann rot, wenn jemand einen Prefix-Behelf einbaut.

**Ergaenzend, als Strukturwaechter:** ein Test, der die Filterkette aus dem Syntaxbaum von
`index/analyzer.py` liest und `split_compound` an Position 2 erwartet. Das Repo hat dieses
Muster bereits (`test_analyzer.py::normalize_callers` liest den Syntaxbaum). Damit wird auch
eine Umstellung der Reihenfolge rot, nicht nur ein Entfernen.

### Muster 2: das zweite Indexfeld, falls Erfolgskriterium 1 woertlich gefordert wird

**Was:** Ein zusaetzliches, nur indexiertes (nicht gespeichertes) Feld `body_de_parts` ueber
denselben Text, mit einer aggressiveren Kette (Variante A4: Fenster 3 bis 14, ohne selbst
zerlegbare Eintraege), aufgenommen in `DEFAULT_FIELDS` mit **niedrigem** Boost.

**Warum das die einzige saubere Bauoption ist:** Die Mis-Splits der aggressiven Variante
(`teu, bescheid`, `sau, bildung`) landen dann nicht im Hauptfeld. `body_de` bleibt exakt und
hoch gewichtet, das Zusatzfeld liefert nur zusaetzliche Trefferausbeute mit kleinem Gewicht.
Ein Mis-Split kostet dann Rauschen weit unten in der Liste statt Praezision oben.

Gemessen liefert A4 fuer die heute fehlenden Faelle:

```
Baugenehmigung -> ['bau', 'genehm']
Bauantrag      -> ['bau', 'antrag']
Baukosten      -> ['bau', 'kost']
Arbeitsvertrag -> ['arbeit', 'vertrag']
Bebauungsplan  -> ['bebau', 'plan']
```

**Der Preis, ehrlich benannt:**

| Kostenposten | Groessenordnung | Quelle |
|---|---|---|
| `SCHEMA_VERSION` von 1 auf 2 | erzwingt vollen Reindex des Volltextbestands | `index/open.py::expected_versions` |
| Reindex auf der Zielhardware | Stunden, der gedeckelte Erstindex lag bei 2 h 58 min bis 4 h 09 min auf nativem aarch64 | `[MEASURED: STATE.md, 06-02]` |
| Zweiter Automat im Prozess | zusaetzliche Grundlast, A4 hat 86.718 Eintraege gegen 276.496 | `[MEASURED: dieser Lauf]`, Groessenordnung nach `docs/german-analyzer.md` grob 10 bis 15 MiB `[ASSUMED]` |
| Indexwachstum | ein zweites Textfeld ueber denselben Inhalt, ohne Positionen | **ungemessen**, gehoert in eine Wave-0-Messung |
| Phase 10 | die Vergleichsmessung muss danach laufen, nicht davor | Sequenz-Zwang 1 der Roadmap |

**Empfehlung:** Nur bauen, wenn der Owner Erfolgskriterium 1 woertlich will, und dann mit
einer eigenen Messung des Indexwachstums vor dem Bau.

### Anti-Muster

- **Die Liste "aufraeumen", ohne die Zerlegung zu messen.** Rezept B ist die Variante, die
  sich aufdraengt, und die messbar schlechteste (7 von 16, echte Mis-Splits). Sie steht mit
  Namen und Messung in `wordlist.py` und `docs/german-analyzer.md`, damit sie nicht
  zurueckkommt.
- **Die Liste falten.** Ein auf ASCII gefaltete Liste trifft nie, und das Scheitern ist
  **still**: jeder Test, der nur "irgendwas kam zurueck" prueft, bleibt gruen.
- **`remove_long` vor den Splitter ziehen.** Gemessen: der 63-Zeichen-Fall wird dann zur
  leeren Tokenliste. Tantivys eigener Standardanalyzer macht genau diesen Fehler.
- **Zwei Analyzer-Instanzen im Prozess.** 41,4 MiB pro Stueck auf einer 4-GB-Box. Der
  Singleton (`cached_german_analyzer`) und sein Zaehler (`build_count()`) sind die Ratsche.
- **Den Digest ueber die Quelldatei bilden.** Dann erzwingt jede Debian-Neusortierung einen
  mehrstuendigen Reindex ohne jede Verhaltensaenderung.
- **Einen Kompositafall in das CI-Set nehmen, ohne ihn vorher gegen die echte Liste zu
  messen.** Die Fixture ist eine Teilmenge; ein Fall, der gegen die Fixture funktioniert,
  kann gegen die echte Liste scheitern, und umgekehrt.

---

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---|---|---|---|
| Kompositazerlegung | Eigener Splitter in Python | `Filter.split_compound` in der Tantivy-Kette | Nur ein Filter in der registrierten Kette wirkt auf **beiden** Seiten. Ein Python-Splitter waere ein zweiter Textraum und liefe der Query-Seite davon |
| Deutsche Stoppwoerter | Eigene Liste | `Filter.stopword("german")` | Die eingebaute Liste traegt echte Umlaute und vergleicht exakt; das ist der Grund fuer ihre Stellung in der Kette |
| Deutsches Stemming | Eigene Endungsregeln | `Filter.stemmer("german")` (Snowball) | Faltet Umlaute und scharfes s selbst, deshalb braucht die deutsche Kette kein `ascii_fold` |
| Reindex-Erzwingung | Neue Marke, neuer Vergleich | `expected_versions` plus `start_rebuild_on_drift` | Der Mechanismus ist gebaut, getestet und bis zur PHP-Statusseite durchgezogen. Eine zweite Stelle, die einen Drift zu kennen behauptet, laeuft am ersten verlorenen Schreibvorgang auseinander |
| Wortliste beschaffen | Download zur Laufzeit | Debian-Paket, exakt gepinnt, im Abbild | Zero-Config bricht bei Firewall, Proxy oder Offline-Installation. Dieselbe Regel wie beim Embedding-Modell |
| Umlautbehandlung auf der Query-Seite | Ausnahmeliste pflegen | Die bewusst dumme Tabelle in `umlaut_variants` | Eine Ausnahmeliste ist ein Woerterbuch, und ein zweites Woerterbuch driftet vom ersten weg. Der Docstring sagt das ausdruecklich |
| Synonyme (Jänner/Januar) | Synonymdatei | Nicht bauen, dokumentiert ablehnen | Zweite Datei, zweite Lizenz, wirkt auf jede Sprachkette, der erste Eintrag zieht hundert nach |

**Kerneinsicht:** In dieser Domaene ist die teure Entscheidung nicht der Code, sondern die
**Datei**. Die Konstituentenliste entscheidet jeden Term im Index, und ihre Wirkung ist
nicht-monoton. Jede Aenderung an ihr ist eine Datenmigration mit Reindex, keine Codeaenderung.

---

## Common Pitfalls

### Pitfall 1: Mehr Listeneintraege ergeben weniger Zerlegung

**Was schiefgeht:** Ein Eintrag wird hinzugefuegt, um einen Fall zu loesen, und ein ganz
anderer Fall verliert seine Zerlegung vollstaendig.
**Warum:** leftmost-longest-Matching kann in eine Sackgasse laufen, aus der es keinen Rueckweg
gibt. Scheitert die Volldekomposition, bleibt der Token ganz; ist er dann laenger als
`remove_long(48)`, verschwindet er komplett.
**Vermeidung:** Jede Listenaenderung gegen die volle Fallsammlung fahren, in **beide**
Richtungen (gewonnene und verlorene Zerlegungen), und den 63-Zeichen-Fall als
"darf nie leer werden" mitfuehren.
**Warnzeichen:** Ein Kompositum-Test, der die leere Tokenliste zurueckbekommt.
`[MEASURED: dieser Lauf, Rezept A3]`

### Pitfall 2: Ein Test, der nur `UNSPLIT` prueft, winkt jede Verschlechterung durch

**Was schiefgeht:** Die zehn Alltagswoerter bleiben in **allen** vier gemessenen Varianten
unversehrt, waehrend die Zerlegungsqualitaet massiv einbricht.
**Warum:** `UNSPLIT` prueft Praezision, nicht Trefferausbeute. Die Rezeptaenderungen kosten
Trefferausbeute.
**Vermeidung:** Der Regressionswaechter muss die erwarteten Tokens Zeile fuer Zeile
festnageln, so wie `COMPOUNDS` es tut, nicht nur "hat nicht zerfallen".
**Warnzeichen:** Ein Testlauf, der nach einer Listenaenderung vollstaendig gruen ist.
`[MEASURED: dieser Lauf]`

### Pitfall 3: Ein kurzes, haeufiges Kompositum steht selbst in `ngerman`

**Was schiefgeht:** Ein plausibler CI-Fall wird formuliert und ist von vornherein nicht
erfuellbar, weil das Wort im Fenster 4 bis 14 liegt und damit selbst Listeneintrag ist.
**Warum:** `ngerman` ist eine Rechtschreibliste und traegt zehntausende gebraeuchliche
Komposita.
**Vermeidung:** Vor jedem neuen CI-Kompositafall im Wegwerf-Container messen:
```bash
docker run --rm python:3.13-slim-trixie sh -c \
  'apt-get update -qq && apt-get install -y --no-install-recommends wngerman >/dev/null \
   && grep -c -ix "Baugenehmigung" /usr/share/dict/ngerman'
```
Ein Ergebnis von `1` bei einer Wortlaenge zwischen 4 und 14 heisst: dieser Fall ist mit
Rezept A nicht baubar.
**Warnzeichen:** Der Analyzer gibt genau einen Token zurueck, und der ist der gestemmte
Ganzwortstamm (`baugenehm`).

### Pitfall 4: Der Splitter greift ohne `lowercase` gar nicht

**Was schiefgeht:** Eine Umstellung der Filterreihenfolge schaltet die Zerlegung stumm ab.
**Warum:** `split_compound` vergleicht bytegenau; die Liste ist kleingeschrieben.
`[MEASURED: dieser Lauf, `Filter.split_compound(...)` ohne `lowercase` liefert `['Baugenehmigung']`]`
**Vermeidung:** Der Strukturwaechter aus Muster 1 prueft die Position im Syntaxbaum.

### Pitfall 5: Die Fixture ist nicht die Liste

**Was schiefgeht:** Ein Fall funktioniert in der Python-Suite und faellt in CI oder im Betrieb
um, oder umgekehrt.
**Warum:** `backend/tests/fixtures/constituents_de.txt` hat 172 Eintraege, die echte Liste
276.496. Die Fixture enthaelt nur die Eintraege, die in den bestehenden Testeingaben
vorkommen. Sie enthaelt zum Beispiel **kein** `bau` und **kein** `baugenehmigung`.
**Vermeidung:** Jeder neue Kompositafall wird zuerst gegen die echte Liste im Container
gemessen, dann wird die Fixture um die noetigen Eintraege erweitert, dann wird geprueft, dass
beide dieselben Tokens liefern. Der Docstring von `test_analyzer.py` beschreibt genau dieses
Verfahren.
**Warnzeichen:** Ein Fall, der in der Fixture nicht zerlegt, aber im Container schon (oder
umgekehrt).

### Pitfall 6: Der Digest wandert unbeabsichtigt und erzwingt einen Reindex

**Was schiefgeht:** Eine harmlos wirkende Aenderung an `load_constituents` oder an `FUGEN`
aendert die gefilterte Liste, damit `wordlist_hash`, damit `expected_versions`, und jeder
bestehende Index geht in einen mehrstuendigen Umbau.
**Warum:** Genau dafuer ist die Marke da, und das ist richtig so.
**Vermeidung:** Der Plan muss ausdruecklich sagen, ob eine Aufgabe den Digest bewegt. Bewegt
sie ihn, gehoert der Reindex in die Aufgabenbeschreibung, nicht in eine Ueberraschung. Der
gemessene Digest von Rezept A ist
`b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0`
(`docs/german-analyzer.md`) und laesst sich mit `scripts/dev/measure_wordlist.sh` nachpruefen.

### Pitfall 7: `no_text_layer` ist ein Zwischenstand

**Was schiefgeht:** Ein Testfall oder ein Messskript liest die Verdikttabelle, waehrend
Arbeitsvorrat da ist, und sieht `skipped:no_text_layer` fuer Dateien, die wenige Minuten
spaeter `indexed` tragen.
**Warum:** Der erste Durchgang stellt fest, dass kein Textlayer da ist, legt die Datei als
OCR-Arbeit wieder vor, und erst der zweite Durchgang indexiert.
**Vermeidung:** Verdikte nur bei leerem Arbeitsvorrat lesen.
`[MEASURED: 2026-09-nachmessung-m7g, Abschnitt 7, Nebenbefund]`. Dieser Befund ist genau
einer der beiden offenen Punkte aus Erfolgskriterium 5.

---

## Code Examples

### Die Zerlegung gegen die echte Liste messen, ohne die Entwicklungsmaschine zu beruehren

```bash
# /usr/share/dict/ngerman gibt es nur im Debian-Abbild. Das Repo hat dafuer bereits
# scripts/dev/measure_wordlist.sh; fuer eine einmalige Frage reicht dieser Aufruf.
docker run --rm -v "$PWD/probe:/probe" python:3.13-slim-trixie sh -c '
  apt-get update -qq >/dev/null 2>&1
  apt-get install -y --no-install-recommends wngerman >/dev/null 2>&1
  pip install -q tantivy==0.26.0 >/dev/null 2>&1
  python /probe/recipe_probe.py'
```

### Die Kette so bauen, wie der ausgelieferte Weg sie baut

```python
# Quelle: backend/src/findling/index/analyzer.py:160-170
from tantivy import Filter, TextAnalyzerBuilder, Tokenizer

analyzer = (
    TextAnalyzerBuilder(Tokenizer.simple())
    .filter(Filter.lowercase())                       # MUSS vor dem Splitter stehen
    .filter(Filter.split_compound(list(constituents)))
    .filter(Filter.custom_stopword(list(FUGEN)))      # sonst landet ein nacktes "s" im Index
    .filter(Filter.stopword("german"))                # braucht ungefaltete Tokens
    .filter(Filter.remove_long(MAX_TOKEN_CHARS))      # MUSS nach dem Splitter stehen
    .filter(Filter.stemmer("german"))                 # MUSS zuletzt stehen
    .build()
)
```

### Die Marken, die einen Reindex erzwingen

```python
# Quelle: backend/src/findling/index/open.py:126-140
def expected_versions(digest: str) -> dict[str, str]:
    return {
        "schema_version": str(SCHEMA_VERSION),
        "index_version": str(INDEX_VERSION),
        "analyzer_version": str(ANALYZER_VERSION),
        "wordlist_hash": digest,          # Erfolgskriterium 4, bereits vorhanden
        "tantivy_version": TANTIVY_VERSION,
    }
```

### Nachsehen, ob ein Kandidat fuer einen CI-Kompositafall ueberhaupt baubar ist

```bash
docker run --rm python:3.13-slim-trixie sh -c '
  apt-get update -qq >/dev/null 2>&1
  apt-get install -y --no-install-recommends wngerman >/dev/null 2>&1
  for w in Baugenehmigung Haushaltssatzung Jahresabschluss Krankenversicherung; do
    printf "%s (%s Zeichen): in ngerman = " "$w" "${#w}"
    grep -c -ix "$w" /usr/share/dict/ngerman || true
  done'
# Steht das Wort drin UND ist es 4 bis 14 Zeichen lang, wird es nie zerlegt.
```

---

## Runtime State Inventory

Diese Phase ist kein Rename, aber ein Wortlistenwechsel ist eine Datenmigration. Die Tabelle
steht deshalb hier, verkuerzt auf die Kategorien, die wirklich betroffen sind.

| Kategorie | Gefunden | Noetige Handlung |
|---|---|---|
| Gespeicherte Daten | Der Tantivy-Index auf dem Datentraeger traegt Terme, die mit der heutigen Liste erzeugt wurden. Die Zustandsdatenbank `state.db` traegt die Marke `wordlist_hash` mit dem Digest, unter dem sie gebaut wurden | Bei jeder Listenaenderung: **Datenmigration** (voller Reindex), nicht nur Codeaenderung. Der Mechanismus dafuer ist gebaut (`start_rebuild_on_drift`) |
| Artefakt auf dem Datentraeger | `$APP_PERSISTENT_STORAGE/dict/de-full.txt` plus `de-full.txt.sha256`. Ein alter Datentraeger kann noch ein `de.txt` ohne Variantennamen tragen, das nichts mehr liest | Keine. Der Fail-closed-Vergleich in `build_artifact` baut bei jeder Unstimmigkeit neu. Kostet einmalig 0,25 s |
| Konfiguration im laufenden Dienst | `FINDLING_COMPOUND_DICT` steht in `backend/appinfo/info.xml` als Umgebungsvariable und ist damit vom Admin in der Nextcloud-Oberflaeche setzbar. Ein Wechsel `full` nach `nouns` aendert den Digest und erzwingt einen Reindex | Der Plan muss pruefen, ob dieser Wechsel heute sichtbar einen Reindex ausloest oder still bleibt. Der Code sieht richtig aus (`artifact_path` traegt die Variante seit Bug-Audit H2 aus 06.1-17), aber ein Ende-zu-Ende-Beleg fehlt |
| Betriebssystemzustand | Keiner. Die Wortliste ist eine Datei im Abbild, nichts registriert sie irgendwo | Keine. Geprueft durch Lesen von `backend/Dockerfile:200-215` |
| Geheimnisse, Umgebungsvariablen | Keine beruehrt | Keine |
| Bauartefakte | Das Abbild traegt `/usr/share/dict/ngerman` und `/usr/local/share/findling/COPYING.wngerman`. Beide entstehen im Bau und wandern nicht mit einem Quellcode-Rename | Keine, solange die Paketfassung `20161207-15` gepinnt bleibt |

---

## Project Constraints (aus CLAUDE.md)

| Vorgabe | Wirkung auf diese Phase |
|---|---|
| Python-Qualitaetsgates: ruff-Vollregelsatz, pyright basic, vulture, lokal gruen vor Commit | Jede neue Testdatei und jede Aenderung an `analyzer.py`/`wordlist.py` muss die Gates lokal bestehen. `backend/.venv` ist vorhanden |
| Code Englisch, Prosa Deutsch, keine Em-Dashes | Neue Testnamen und Docstrings auf Englisch, wie der Bestand. Doku-Ergaenzungen in `docs/german-analyzer.md` folgen der dortigen Sprachmischung |
| Echte Umlaute nur in deutscher Prosa, nie in Code | Umlaute in Testdaten sind **Daten** und erlaubt (der Bestand macht das ausdruecklich so, `test_analyzer.py:16-19`). Bezeichner bleiben ASCII |
| Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde ab MEDIUM vor Abschluss fixen | Gilt auch hier. Bei einer Rezeptaenderung ist das Performance-Audit nicht optional, weil der Automat 41,4 MiB kostet |
| Sicherheitsgrenze nicht verdoppeln | Diese Phase fasst weder ACL-Vorfilter noch PHP-Recheck an |
| Launch-Haertung vor der Store-Abgabe | Betrifft Phase 11, nicht diese |
| Kurztext-Regel fuer Aussentexte | Betrifft nur Doku, die nach aussen geht. `docs/german-analyzer.md` ist Entwicklerdoku und darf ausfuehrlich bleiben |
| GSD-Workflow-Zwang: keine Direktbearbeitung ausserhalb eines GSD-Kommandos | Der Plan dieser Phase ist der Weg fuer jede Aenderung |

---

## Environment Availability

| Abhaengigkeit | Gebraucht fuer | Vorhanden | Fassung | Ausweich |
|---|---|---|---|---|
| Docker | Messung gegen die echte `wngerman`-Liste, Abbildbau | ja | 29.5.2 | keiner, ohne Docker ist die echte Liste nicht messbar |
| `python:3.13-slim-trixie` mit `wngerman` | dito | ja, im Lauf dieser Sitzung geholt | `wngerman` 20161207-15, 356.010 Zeilen | keiner |
| tantivy 0.26.0 (Python) | Analyzerkette lokal fahren | ja, `backend/.venv/Lib/site-packages/tantivy` | 0.26.0 | keiner |
| `backend/.venv` mit Projektabhaengigkeiten | Python-Suite lokal fahren | ja | siehe `backend/uv.lock` | keiner |
| `/usr/share/dict/ngerman` auf der Entwicklungsmaschine | echte Liste ohne Container | **nein**, Windows-Maschine | n/a | Wegwerf-Container, so wie `scripts/dev/measure_wordlist.sh` es macht |
| GitHub-Runner fuer `integration.yml` | Der Beleg des CI-Sprachfall-Sets | nur nach dem Zusammenfuehren auf `main` | n/a | Die Python-Suite lokal, plus ein Lauf auf `main` danach. Dasselbe Muster wie DI-07-01 |
| AWS-Box | Vergleichsmessung | angehalten, gehoert zu Phase 10 | n/a | Diese Phase braucht sie nicht |

**Fehlende Abhaengigkeiten ohne Ausweich:** keine.
**Fehlende Abhaengigkeiten mit Ausweich:** die Debian-Wortliste lokal, Ausweich ist der
Wegwerf-Container und im Repo bereits als Muster etabliert.

---

## Package Legitimacy Audit

**Diese Phase installiert keine neuen Pakete.** Sie arbeitet ausschliesslich mit bereits
gepinnten Abhaengigkeiten (`tantivy==0.26.0`) und einem bereits gepinnten Debian-Paket
(`wngerman=20161207-15`).

| Paket | Registry | Fassung | Herkunft | Verwendung in dieser Phase | Verfuegung |
|---|---|---|---|---|---|
| `tantivy` | PyPI | 0.26.0 (2026-04-29) | bereits in `backend/pyproject.toml` und `uv.lock` gepinnt, sdist-Hash im Lockfile | unveraendert genutzt | Bestand, kein Neu-Install |
| `wngerman` | Debian trixie | 20161207-15 | bereits in `backend/Dockerfile:206` exakt gepinnt, Lizenz im Abbild geprueft | unveraendert genutzt | Bestand, kein Neu-Install |

**Wegen slopcheck-Verdikt entfernte Pakete:** keine, weil keine vorgeschlagen werden.
**Als verdaechtig markierte Pakete:** keine.

Sollte der Plan wider Erwarten ein neues Paket brauchen, gilt das Gate unveraendert: erst
slopcheck, erst danach ein Vorschlag.

---

## State of the Art

| Frueherer Stand | Heutiger Stand | Wann geaendert | Bedeutung |
|---|---|---|---|
| "Der ausgelieferte Suchweg benutzt einen Prefix-Behelf" (Semantiklauf 05.09.2026, Grundlage der Roadmap-Phasenbeschreibung) | Kein Behelf im Suchweg, `split_compound` greift auf beiden Seiten | Phase 06.1, Plaene 06.1-04 und 06.1-17 | Die Phase hat weniger zu bauen als geplant, aber eine andere Luecke |
| "14 von 16 Komposita ueber ein Teilwort auffindbar" (`docs/german-analyzer.md`) | Stimmt fuer die sechzehn gemessenen, langen Woerter. Fuer kurze Alltagskomposita ist die Quote deutlich schlechter: 7 von 21 nicht auffindbar | dieser Lauf, 08.09.2026 | Die dokumentierte Grenze ist breiter als ihre Formulierung vermuten laesst |
| Wortlisten-Digest als offener Punkt (T-02-11) | Als `wordlist_hash` in `expected_versions`, mit Reindex-Kette bis zur PHP-Statusseite | Phase 2, gehaertet in Phase 4 und 06.1 | Erfolgskriterium 4 ist gebaut, nicht zu bauen |
| Endungsvergleich offen (Annahme A10 aus 06-11) | Gefahren und bestanden, dreizehn Endungen, keine unerklaerte Abweichung | 07.09.2026, Nachmessung m7g Abschnitt 7 | QUAL-03 braucht nur noch zwei Entscheidungssaetze |

**Veraltet und nicht mehr benutzen:**

- Die Formulierung "wo noch ein Prefix-Behelf steht" aus der Roadmap-Phasenbeschreibung. Sie
  beschreibt einen Zustand vor Phase 06.1.
- Die Annahme, `FINDLING_COMPOUND_DICT` sei wirkungslos. Das war bis Bug-Audit H2 aus Plan
  06.1-17 so; seither traegt der Artefaktname die Variante.

---

## Security Domain

Diese Phase beruehrt Tokenisierung und Tests, keine neue Angriffsflaeche. Die relevanten
Kategorien sind schmal, aber nicht leer.

| ASVS-Kategorie | Trifft zu | Standardkontrolle im Bestand |
|---|---|---|
| V2 Authentifizierung | nein | Unveraendert, laeuft ueber Nextcloud und AppAPI |
| V3 Sitzungen | nein | Unveraendert |
| V4 Zugriffskontrolle | **indirekt ja** | Die Berechtigungsgrenze bleibt der finale PHP-Recheck. Eine Aenderung an der Tokenisierung darf die Kandidatenmenge veraendern, nie die Filterung. Der bestehende Paritaetstest (`test_parity_diff.py`, `test_guest_parity.py`) ist die Ratsche |
| V5 Eingabevalidierung | **ja** | Die Suchzeile ist Nutzereingabe. `build_query` faengt jede Parserbeschwerde ab, statt eine Ausnahme zu werfen (`query/rewrite.py:317-330`), der Klammertiefenwaechter steht **vor** dem Parser (Security-Audit C2), regulaere Ausdruecke sind aus |
| V6 Kryptografie | nein, ausser Digest | `hashlib.sha256` fuer den Wortlisten-Digest. Kein Sicherheitsprimitiv, nur eine Identitaet. Nie selbst bauen |
| V7 Fehlerbehandlung und Protokollierung | **ja** | Die Fehlerliste des Parsers zitiert die Eingabe und darf deshalb nie ueber `LOGGER.debug` hinaus. `wordlist.measure` und `analyzer.measure` geben ausdruecklich **nur Zahlen** aus, nie einen Token und nie ein Wort (T-02-14) |

| Bedrohungsmuster | STRIDE | Standardgegenmassnahme |
|---|---|---|
| Nutzerinhalt landet ueber ein Messskript im Protokoll | Information Disclosure | Messmodus gibt nur Zahlen aus, dokumentiert in `wordlist.py` und `analyzer.py`. Jeder neue Messpfad dieser Phase muss dieselbe Regel einhalten |
| Suchbegriff im Betriebsprotokoll | Information Disclosure | Parserbeschwerden nur auf `debug`, nie auf `info` |
| Tief geschachtelte Klammern in der Suchzeile stuerzen den Prozess ab | Denial of Service | `SEARCH_QUERY_MAX_DEPTH`, geprueft auf der **Rohzeile**, vor dem Parser |
| Regulaerer Ausdruck aus der Suchleiste | Denial of Service | `allow_regexes=False` |
| Sehr langer Token (base64-Blob) blaeht den Index | Denial of Service | `remove_long(48)`, aber **nach** dem Splitter, sonst verschwinden lange deutsche Woerter |
| Eine getauschte Wortliste laesst Index und Query still auseinanderlaufen | Tampering | Fail-closed-Pruefung in `build_artifact` (Digestdatei muss genau die Datei beschreiben, die daliegt), plus Cache-Schluessel aus Digest, Groesse und Aenderungszeit |

---

## Assumptions Log

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---|---|---|
| A1 | Ein zweiter Automat der Variante A4 (86.718 Eintraege) kostet grob 10 bis 15 MiB dauerhaft | Muster 2 | Die Grundlast steigt staerker als geplant, Phase 10 misst eine Verschlechterung. Messbar mit `scripts/dev/measure_wordlist.sh` vor dem Bau |
| A2 | Ein zusaetzliches, nur indexiertes Textfeld ueber denselben Inhalt vergroessert den Tantivy-Index sichtbar, aber nicht um mehr als die Groessenordnung des bestehenden `body_de`-Anteils | Muster 2 | Der Index passt nicht mehr in das Platzbudget der Zielbox. Muss vor dem Bau gemessen werden, nicht geschaetzt |
| A3 | Es gibt heute keinen CI-Schritt, der die Anwesenheit von `COPYING.wngerman` im gebauten Abbild prueft | Bestandsaufnahme 6 | Der Plan baut einen Schritt doppelt. Billig zu pruefen: `grep -rn COPYING .github/workflows/` |
| A4 | Der Wechsel `FINDLING_COMPOUND_DICT=full` nach `nouns` loest heute sichtbar einen Reindex aus | Runtime State Inventory | Ein Admin schaltet die Variante um, Index und Query-Parser laufen still auseinander. Der Code sieht richtig aus, ein Ende-zu-Ende-Beleg fehlt |
| A5 | Die 20 `too_large`-CSV aus dem Endungsvergleich haben bereits einen Testfall in `backend/tests/test_extract_errors.py` | Bestandsaufnahme 4 | Erfolgskriterium 5 bleibt offen, obwohl es abgehakt aussieht. Billig zu pruefen |
| A6 | `tools/index_status.py` mit leerer Konstituentenliste ist unschaedlich, weil es nur Metadaten liest und nie sucht | Bestandsaufnahme 1 | Ein Diagnosewerkzeug liefert falsche Auskunft ueber einen Index, den es nicht richtig oeffnen kann. Billig zu pruefen durch Lesen der Datei |

---

## Open Questions (RESOLVED)

Alle fuenf Fragen sind mit Abschluss der Phase 08 beantwortet (Stand 08.09.2026):

1. RESOLVED: Owner-Entscheid a am 08.09.2026 (08-01-SUMMARY.md, Task 3): Kriterium 1 wurde
   auf die messbar zerlegbaren Faelle umformuliert, keine Rezeptaenderung. "Baugenehmigung"
   steht als benannte Grenze in docs/german-analyzer.md.
2. RESOLVED: 08-04 hat das Set von 7 auf 10 Faelle erweitert (Belehrung nach Audit-Fix H-01
   statt Vereinbarung, Auszug, Erinnerung), alle vorher gegen die echte Liste gemessen;
   test_corpus_terms.py haelt die CI-Begriffe gegen Korpus und Fallliste.
3. RESOLVED: Der Schritt fehlte; 08-03 hat ihn in docker.yml gebaut (Lizenz, Fassung
   20161207-15, 356010 Zeilen, Modus 444 im veroeffentlichten Abbild).
4. RESOLVED: 08-03 belegt den Variantenwechsel Ende zu Ende bis reindexRequired
   (test_switching_the_dictionary_variant_asks_for_a_reindex), inkl. Audit-Korrektur
   der Fixture-Falle (Test war zunaechst aus dem falschen Grund gruen).
5. RESOLVED: 08-04 traegt den ASCII-Transkriptionsfall im COMPOUNDS-Waechter, 08-05
   dokumentiert die Grenze als "Spelled out umlauts on the index side" in
   docs/german-analyzer.md; der OCR-Fall Ubermittlungsprotokoll ist als Fall 48 gemessen.

(Die urspruenglichen Fragen bleiben darunter im Wortlaut stehen.)

1. **Soll Erfolgskriterium 1 woertlich gelten?**
   - Was wir wissen: "Genehmigung findet Baugenehmigung" ist mit Rezept A gemessen
     unerreichbar, und alle vier gemessenen Rezeptvarianten sind netto schlechter.
   - Was unklar ist: ob der Owner das Kriterium als Beispiel oder als Zusage liest.
   - Empfehlung: `checkpoint:human-verify` an den Anfang der Phase. Ohne diesen Entscheid
     kann der Planer nicht zwischen "Doku plus Tests" und "zweites Indexfeld plus Reindex"
     waehlen, und der Unterschied ist eine Phase gegen ein Wochenende.

2. **Wie viele Kompositafaelle soll das CI-Sprachfall-Set tragen?**
   - Was wir wissen: heute zwei von sieben, beide gruen, beide mit langen Woertern.
   - Was unklar ist: ob "die weiteren Kompositafaelle" aus Erfolgskriterium 1 eine Zahl meint.
   - Empfehlung: drei zusaetzliche, alle vorher gegen die echte Liste gemessen. Jeder braucht
     ein Wort, das in genau einer Korpusdatei steht.

3. **Prueft die CI heute die Lizenzdatei im Abbild?**
   - Was wir wissen: `THIRD-PARTY.md:259` nennt den Befehl von Hand.
   - Was unklar ist: ob `docker.yml` oder `integration.yml` das automatisch tun.
   - Empfehlung: `grep -rn "COPYING" .github/workflows/` in Wave 0, ein Schritt nur wenn er
     fehlt.

4. **Loest ein Wechsel von `FINDLING_COMPOUND_DICT` heute sichtbar einen Reindex aus?**
   - Was wir wissen: der Artefaktname traegt die Variante seit Bug-Audit H2 aus 06.1-17, die
     Digeste der beiden Varianten sind verschieden und beide in der Doku notiert.
   - Was unklar ist: ob ein Test das Ende zu Ende belegt.
   - Empfehlung: ein Testfall, der beide Varianten nacheinander faehrt und die Drift auf der
     Statusseite sieht. Das ist gleichzeitig der schaerfere Beleg fuer Erfolgskriterium 4.

5. **Was passiert mit Dokumenten, die Umlaute ausgeschrieben tragen?**
   - Was wir wissen: `Grundstuecksverkehrsgenehmigung` wird von **keinem** Rezept zerlegt.
     Die Query-Seite bildet Umlautvarianten, die Index-Seite nicht.
   - Was unklar ist: wie haeufig das im Zielbestand ist.
   - Empfehlung: als benannten Grenzfall in `docs/german-analyzer.md`, "Known limits", plus
     ein Testfall, der die heutige Antwort festnagelt. Nicht in dieser Phase bauen.

---

## Sources

### Primaer (HIGH)

- Quellcode dieses Repositoriums, in dieser Sitzung gelesen: `backend/src/findling/index/{analyzer,wordlist,open,schema,search}.py`, `backend/src/findling/query/rewrite.py`, `backend/src/findling/api/{resources,search,status}.py`, `backend/src/findling/worker/poller.py`, `backend/src/findling/config.py`, `php/lib/Search/Provider.php`, `backend/Dockerfile`
- Testdateien: `backend/tests/{test_analyzer,test_wordlist,test_index_open,test_query_rewrite,test_snippet_offsets,test_store_repo}.py`, `backend/tests/fixtures/constituents_de.txt`
- `.github/workflows/integration.yml`, Schritt "The seven German language cases, as the owner" (Zeile 1403 ff.)
- `backend/.venv/Lib/site-packages/tantivy/tantivy.pyi`, tantivy 0.26.0, Signatur von `Filter.split_compound`
- Messlauf dieser Sitzung: `python:3.13-slim-trixie` plus `wngerman=20161207-15` plus `tantivy==0.26.0`, vier Rezeptvarianten gegen 21 Komposita und 18 Nicht-Komposita, plus Gegenprobe zum 63-Zeichen-Fall ohne `remove_long`
- `docs/german-analyzer.md`, `THIRD-PARTY.md`, `testdata/CORPUS.md`
- `docs/measurements/2026-09-nachmessung-m7g/README.md`, Abschnitte 7, 11 und 14
- `.planning/phases/07-gemeinsame-embedding-engine/{07-03-SUMMARY.md,07-04-SUMMARY.md,07-AUDIT-FIXES.md,deferred-items.md}`
- `.planning/{ROADMAP.md,REQUIREMENTS.md,STATE.md}`, `CLAUDE.md`

### Sekundaer (MEDIUM-HIGH)

- `https://docs.rs/tantivy/latest/tantivy/tokenizer/struct.SplitCompoundWords.html`, Semantik der Volldekomposition. Gegen den laufenden Filter nachgemessen und bestaetigt

### Tertiaer (LOW)

- keine. Kein Befund dieses Berichts steht auf einer unbestaetigten Websuche

---

## Metadata

**Konfidenz im Einzelnen:**

- Bestandsaufnahme des Suchwegs: **HIGH**. Jede Aussage traegt eine Datei und eine Zeile, der
  Weg wurde in beide Richtungen gelesen (von der PHP-Route abwaerts und von `split_compound`
  aufwaerts zu allen Aufrufern)
- `split_compound`-Semantik: **HIGH**. Gegen den installierten Filter gemessen, zusaetzlich
  gegen die offizielle Doku gehalten
- Die zentrale Messung (Baugenehmigung, vier Rezepte): **HIGH**. Im echten Basisabbild mit
  dem echten Debian-Paket und der echten Fassung gefahren, der Nicht-Monotonie-Befund
  zusaetzlich mit abgeschaltetem `remove_long` gegengeprueft
- Zustand von QUAL-01 und Erfolgskriterium 3: **HIGH**. Lizenzweg im Dockerfile, im Repo und
  im Container geprueft
- Zustand von Erfolgskriterium 4: **HIGH**. Code plus sieben Testfundstellen
- Zustand von QUAL-03: **HIGH** fuer die Messung, **MEDIUM** fuer die Frage, was formal noch
  fehlt (haengt an A5)
- Kosten von Muster 2: **LOW-MEDIUM**. Der Reindex ist gemessen, das Indexwachstum und die
  zweite Automatengroesse sind geschaetzt (A1, A2) und gehoeren vor den Bau gemessen

**Recherchedatum:** 2026-09-08
**Gueltig bis:** 2026-10-08 fuer die Bestandsaufnahme (der Code ist eingefroren, solange keine
Phase daran arbeitet). Die Messungen gegen `wngerman 20161207-15` und `tantivy 0.26.0` sind
an diese beiden Fassungen gebunden und ueberleben jeden Wechsel einer der beiden nicht.
