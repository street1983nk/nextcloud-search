# Feature Research

**Domain:** Mehrsprachige lexikalische Suche in einer selbstgehosteten Dokumentensuche, Ausbau um Spanisch, Italienisch, Niederlaendisch und Portugiesisch
**Researched:** 2026-09-23 (Milestone v1.3 Sprachausbau)
**Confidence:** HIGH fuer alles, was ich in der ausgelieferten tantivy-Fassung selbst gemessen habe, fuer den eigenen Quellcode und fuer die offizielle Doku der Vergleichsprodukte. MEDIUM fuer die Nutzererwartung aus Fremdprodukten, weil sie aus Konfigurationsoberflaechen und Foren abgeleitet und nicht erhoben ist.

Untersucht ist nur das Neue: die vier zusaetzlichen Sprachen der LEXIKALISCHEN Suche und die UI-Kataloge. Volltext de/en, deutsche Komposita, Semantik (kann die vier Sprachen bereits), OCR in neun Sprachen (Positivliste seit 1.2.0), Ergebnisseite mit Filtern und Sortierung, Berechtigungs-Durchgriff und EN/DE/FR gelten als gebaut.

---

## Teil 0: Eigene Messungen, die diese Recherche tragen

Fuenf Befunde stammen nicht aus Fremdquellen, sondern aus Laeufen gegen `tantivy 0.26.0` in `backend/.venv` dieses Repos, also gegen genau die Fassung, die ausgeliefert wird. Sie stehen vorn, weil sie mehrere Zeilen der Tabellen weiter unten erklaeren und weil sie mehrere Entwuerfe ausschliessen.

### M1. tantivy traegt alle vier Sprachen, Stemmer und Stoppwortliste (HIGH)

`Filter.stemmer` nimmt 18 Sprachen, `Filter.stopword` 13, und es/it/nl/pt sind in beiden Mengen. Es braucht also keine Fremdbibliothek, keine eigene Stoppwortliste und keinen eigenen Stemmer. Quelle: `quickwit-oss/tantivy-py`, `src/tokenizer.rs` und die API-Doku, dazu der eigene Lauf.

### M2. ascii_fold muss HINTER die Stoppwortliste, nicht davor (HIGH, gemessen)

Die eingebauten Stoppwortlisten tragen echte Akzente und vergleichen exakt. Wer vorher faltet, laesst Stoppwoerter durch. Gemessen an einem Satz je Sprache:

| Sprache | Reihenfolge `fold` dann `stop` | Reihenfolge `stop` dann `fold` |
|---|---|---|
| Portugiesisch | `nao, ha, contrat, enta, tamb, aqu` | `contrat, enta, aqu` |
| Spanisch | `mas, aun, contrat, aqui, si, funcion` | `aun, contrat, aqui, funcion` |
| Italienisch | `perc, contratt, gia, uffic` | `contratt, gia, uffic` |

Portugiesisch leckt drei Stoppwoerter, Spanisch zwei, Italienisch eines. Das ist genau die Begruendung, die im Kopf von `backend/src/findling/index/analyzer.py` fuer die deutsche Kette schon steht. **Die vorhandene englische Kette faltet vor der Stoppwortliste** (`lowercase, ascii_fold, stopword("english"), remove_long, stemmer`). Fuer Englisch ist das folgenlos, weil die englische Liste keine Akzente traegt. Wer diese Kette fuer die vier neuen Sprachen kopiert, baut den Fehler ein. Das ist die wahrscheinlichste Einzelfalle dieses Milestones.

Gegenrichtung, ehrlich benannt: Niederlaendisch ist der einzige Fall, in dem `fold` vor `stop` besser waere. Die Betonungsakzente des Niederlaendischen (`hét`, `zó`, `vóór`) sind unakzentuiert Stoppwoerter und ueberleben die Liste sonst. Gemessen: `hét` wird bei `fold` dann `stop` entfernt, bei `stop` dann `fold` bleibt `het` stehen. Ein Streutoken gegen drei geleckte Stoppwoerter: die Reihenfolge bleibt einheitlich `stop` dann `fold`, und die niederlaendischen Betonungsformen gehoeren in eine kleine `custom_stopword`-Liste, wenn sie jemals stoert.

### M3. ascii_fold ist fuer es und pt zwingend, fuer it und nl gleichgueltig (HIGH, gemessen)

Ohne Faltung erzeugen die akzentuierte und die unakzentuierte Schreibweise desselben Wortes verschiedene Terme, und zwar nicht nur bei Sonderzeichen:

| Wort | mit `ascii_fold` | ohne |
|---|---|---|
| `información` / `informacion` | `informacion` / `informacion` | `inform` / `informacion` |
| `faturação` / `faturacao` | `faturaca` / `faturaca` | `fatur` / `faturaca` |
| `ação` / `acao` | `aca` / `aca` | `açã` / `aca` |
| `città` / `citta` | `citt` / `citt` | `citt` / `citt` |
| `coördinatie` / `coordinatie` | `coordinatie` / `coordinatie` | `coordinatie` / `coordinatie` |

Der spanische und der portugiesische Snowball-Stemmer entfernen Akzente nur dort, wo sie auf einer abgetrennten Endung sitzen. Der niederlaendische entfernt sie selbst, der italienische hat hier nichts zu tun. Also: `ascii_fold` in allen vier Ketten, hinter der Stoppwortliste.

Der Preis, damit er dokumentiert und nicht entdeckt wird: `año` und `ano` werden derselbe Term (`ano`), `niña` und `nina` ebenfalls (`nin`). Das ist die uebliche und ueberall akzeptierte Abwaegung in einer Dokumentensuche: mehr Recall, ein paar Wortpaare weniger Praezision. Die Faltung gilt auf beiden Seiten, Index und Anfrage, also bleibt die Suche in sich schluessig.

### M4. Italienische Elision funktioniert ohne eigenen Filter (HIGH, gemessen)

Elasticsearch braucht dafuer einen `elision`-Filter, tantivy hat keinen, und er wird hier nicht gebraucht: `Tokenizer.simple()` trennt am Apostroph, und die Snowball-Stoppwortliste fuehrt die elidierten Formen ausdruecklich als eigene Eintraege (`dell | di + l'`, `nell | in + l'`, `sull | su + l'`, `agl | a + gl'`). Gemessen:

- `dell'anno la fatturazione elettronica dei contratti` gibt `anno, fattur, elettron, contratt`
- `l'ufficio nell'edificio` gibt `uffic, edific`

Kein Artikelrest im Index. Italienisch ist damit die billigste der vier Sprachen.

### M5. Niederlaendische Komposita bleiben ganz, und `split_compound` loest das (HIGH, gemessen)

Niederlaendisch ist wie Deutsch eine zusammenschreibende Sprache, und der Snowball-Stemmer zerlegt nichts. Ohne Zerleger findet niemand `belasting` in `gemeentebelastingen`. Mit einer Miniatur-Konstituentenliste und den niederlaendischen Fugen (`s`, `en`, `e`) im selben Kettenbau wie beim Deutschen:

| Wort | ohne Zerleger | mit Zerleger |
|---|---|---|
| `verzekeringsmaatschappij` | `verzekeringsmaatschappij` | `verzeker, maatschappij` |
| `gemeentebelastingen` | `gemeentebelast` | `gemeent, belast` |
| `woningbouwvereniging` | `woningbouwveren` | `woning, bouw, veren` |
| `arbeidsovereenkomst` | `arbeidsovereenkomst` | `arbeid, overeenkomst` |
| `jaarrekening` | `jaarreken` | `jar, reken` |
| `huurcontract` | `huurcontract` | `hur, contract` |

Sechs von sechs Verwaltungskomposita kommen auseinander. Die Mechanik traegt also unveraendert. Dazu die Lizenzlage, und sie ist besser als im deutschen Fall: Debian trixie fuehrt `wdutch` aus dem Quellpaket `dutch` 1:2.20.19+1-3, es installiert `/usr/share/dict/dutch` und `/usr/share/dict/nederlands`, stammt von OpenTaal und traegt **BSD-3-Clause und CC-BY-3.0** (geprueft im Debian-`copyright`). Beide sind permissiv und damit ohne die GPL-Kaskade vertraeglich, die beim deutschen `wngerman` noetig war.

### M6. Der Index waechst um rund zwei Drittel, aber nur bei eingeschalteten Sprachen (HIGH, aus dem eigenen Kopf von `schema.py`)

Gemessen ist dort: der Index waechst auf das 0,374-fache des extrahierten Textes mit Dokumentspeicher und auf das 0,076-fache ohne ihn. Heute liegt der Index also bei etwa 0,45 (ein gespeichertes `body_de` plus ein ungespeichertes `body_en`). Vier weitere ungespeicherte Koerperfelder kosten 4 mal 0,076, also 0,304. Das ergibt rund 0,754, ein Zuwachs von etwa 68 Prozent.

Das ist eine Plattenzahl, keine RAM-Zahl (tantivy liest per mmap), und sie faellt nur an, wo ein Feld auch befuellt wird. Ein leeres Schemafeld kostet fast nichts. Genau daraus folgt die Bauform in Teil 2.

---

## Teil 1: Wie vergleichbare Produkte es machen, und was Nutzer davon erwarten

| Produkt | Modell | Spracherkennung | Query-Zeit | Konfidenz |
|---|---|---|---|---|
| **Paperless-ngx** (dieselbe Engine, dieselbe Zielgruppe) | **EINE** Stemmer-Sprache fuer den ganzen Index | keine; `PAPERLESS_SEARCH_LANGUAGE`, sonst abgeleitet aus `PAPERLESS_OCR_LANGUAGE` | eine Kette, keine Wahl; Wechsel der Einstellung baut den Index beim naechsten Start neu | HIGH (offizielle Doku) |
| **Elasticsearch / OpenSearch** | Feld je Sprache (multi-field) oder Index je Sprache | Sprachidentifikation in der Ingest-Pipeline moeglich, `lang_ident_model_1` | `multi_match` ueber alle Sprachfelder, mit Feld-Boosts; Anfrage wird ausdruecklich NICHT sprach-erkannt | HIGH (Elastic-Blog + Referenz) |
| **Meilisearch** | ein Index, Erkennung je Feld ueber `whatlang` | automatisch je Dokument, einschraenkbar ueber `localizedAttributes` | `locales` je Anfrage, sonst Erkennung | HIGH (offizielle Doku) |
| **Nextcloud fulltextsearch_elasticsearch** | Analyzer nicht konfigurierbar, nur der Tokenizer | keine | keine | MEDIUM (PR #57, Forenpraxis) |
| **Findling heute** | zwei Sprachfelder, **derselbe Text in beide**, kein Dokument wird zugeordnet | keine | OR ueber `body_de`, `body_en`, `name`, `title`, mit Boosts 1,0 / 0,8 / 3,0 / 2,0 | HIGH (eigener Code) |

### Was daraus folgt, in vier Saetzen

**Findling liegt bereits ueber dem direkten Wettbewerber.** Paperless-ngx, der Marktfuehrer im selbstgehosteten Dokumentenmanagement und die naechste Vergleichsgroesse, kann genau eine Stemmer-Sprache. Findling kann zwei und behandelt beide gleichzeitig. Die Nutzererwartung in diesem Segment ist also eher niedrig, und der Ausbau auf sechs ist Vorsprung, nicht Nachholen.

**Das Muster, das Findling schon faehrt, ist das, das Elastic empfiehlt.** "Ein Feld je Sprache, denselben Text ueberall hinein, zur Anfragezeit ueber alle Felder" ist die Per-Field-Strategie, und ihr ausdruecklicher Vorteil ist der Umgang mit gemischtsprachigen Dokumenten. Der Ausbau ist damit eine Fortsetzung und keine Kehrtwende. Das ist die wichtigste Nachricht dieser Recherche fuer den Zuschnitt.

**Ein gemeinsames multilinguales Feld ist ueberall verworfen.** Ein Analyzer ueber gemischten Text unter-stemmt die einen Sprachen und ueber-stemmt die anderen, und der Recall sinkt in allen. Das steht so in mehreren unabhaengigen Elastic-Leitfaeden.

**Die Anfrage wird nirgends sprach-erkannt, und das ist der wichtigste Einzelbefund.** Elastic schreibt es aus: Suchanfragen haben im Mittel 2,4 Terme, Sprachidentifikation braucht mehr als 50 Zeichen. Meilisearch sagt es in der eigenen Doku ueber die eigene Automatik ("short or partial inputs are harder to identify correctly"). Wer die Suchzeile erkennen laesst, baut eine Suche, die bei kurzen Woertern wuerfelt.

### Was Nutzer bei gemischtsprachigen Bestaenden erwarten

Der Bestand einer typischen Nextcloud ist gemischt, und zwar innerhalb einzelner Dateien: ein Angebot mit niederlaendischem Anschreiben und englischen Positionen, ein Lebenslauf, ein Vertrag mit spanischem Rumpf und englischen Anlagen. Die Diskussion #8293 bei Paperless-ngx zeigt, wie Nutzer damit heute umgehen, wenn die Suche es nicht kann: sie weichen auf Tags und Metadaten aus und legen sich eine Ablagesprache zurecht. Das ist ein Umgehungsverhalten, kein Wunsch.

Die Erwartung selbst ist einfach und unausgesprochen: **ich tippe ein Wort und die Datei kommt, egal in welcher Sprache sie geschrieben ist, und ich sage vorher nichts.** Genau das liefert die Per-Field-Strategie ohne Erkennung. Jede Bauform, die vom Nutzer oder vom Admin eine Zuordnung verlangt, bricht diese Erwartung an der Stelle, an der sie am haeufigsten zutrifft.

---

## Teil 2: Die drei Entwurfsfragen, beantwortet

### Frage 1: Sprachfelder je Dokument oder ein multilinguales Feld?

**Sprachfelder, sechs Stueck, und das Schema traegt sie immer.**

Die zweite Haelfte ist die eigentliche Empfehlung und sie faellt aus dem eigenen Code: `FINDLING_LANGUAGES` steuert heute nicht das Schema, sondern nur, ob `body_en` **befuellt** wird (`IndexBatchWriter._index_english`). Das Schema hat immer beide Felder. Dieses Muster traegt unveraendert auf sechs:

- Das Schema hat in jeder Installation dieselben sechs Koerperfelder. Es gibt nur eine Schemafassung, also nur eine Migration und keine instanzabhaengigen Schemata.
- Befuellt werden nur die Felder, die die Instanz eingeschaltet hat. Der Zuwachs aus M6 zahlt nur, wer ihn bestellt.
- Ein leeres Feld kostet keine Posting-Liste und faellt zur Anfragezeit sofort durch.

### Frage 2: Spracherkennung je Dokument?

**Nein. Weder automatisch noch aus Dateimetadaten.** Ausfuehrlich als Anti-Feature unten. Die Kurzfassung: derselbe Text geht in alle eingeschalteten Felder, wie heute. Das ist genau die Eigenschaft, die gemischtsprachige Dokumente ueberhaupt erst findbar macht, und sie kostet nichts ausser Plattenplatz, den M6 beziffert.

Dateimetadaten sind zusaetzlich keine Quelle: Nextcloud fuehrt kein Sprachfeld an einer Datei, ein `dc:language` in einem PDF ist in der Praxis fast immer die Oberflaechensprache des schreibenden Programms, und ein Ordnername wie `/NL/` ist eine Konvention, keine Aussage.

### Frage 3: In welchen Sprachfeldern wird zur Anfragezeit gesucht?

**In allen befuellten, nie in der Nutzersprache.** Drei Gruende, der dritte ist der wichtigste:

1. Die Nutzersprache der Oberflaeche sagt nichts ueber die Sprache der gesuchten Datei. Ein niederlaendischer Admin mit englischer Nextcloud-Oberflaeche ist der Normalfall, nicht die Ausnahme.
2. Die Anfrage laesst sich nicht erkennen (Teil 1).
3. Findling faehrt es heute schon so, und der Berechtigungs-, Offset- und Paritaetsbau darunter kennt genau einen Suchpfad. Eine zweite, sprachabhaengige Feldmenge waere eine zweite Variante, durch die jede Sicherheitszusage erneut gefuehrt werden muesste.

**Aber es gibt einen gemessenen Haken, und er ist neu bei sechs Feldern.** Der Parser baut aus einem blossen Wort ein ODER ueber alle Standardfelder, und tantivy **summiert** die Scores der passenden Teilanfragen. Das ist Elasticsearch-`most_fields`-Verhalten. Gemessen, wie viele der sechs Ketten fuer dieselbe Frage zugleich treffen:

| Dokument enthaelt | Anfrage | passende Teilanfragen |
|---|---|---|
| `contratos` | `contrato` | 3 von 6 (en, es, pt) |
| `facturas` | `factura` | 3 von 6 (en, es, pt) |
| `rekeningen` | `rekening` | 3 von 6 (de, es, nl) |
| `documentos` | `documento` | 3 von 6 (en, es, pt) |
| `informatie` | `informatie` | **6 von 6** |

Ein Dokument, dessen Wort alle Ketten unveraendert durchlaesst, bekommt bis zum Sechsfachen des Beitrags eines Dokuments, das nur in der richtigen Sprachkette trifft. Das ist die falsche Richtung: der sprachrichtige Treffer soll gewinnen. Bei zwei Feldern war das ein Rauschen, bei sechs ist es eine messbare Rangverschiebung.

Zwei Hebel, beide vorhanden:
- **Feld-Boosts senken.** `FIELD_BOOSTS` fuehrt `body_en` schon auf 0,8. Die vier neuen gehoeren darunter, etwa 0,6, mit der ausdruecklichen Begruendung, dass sie Zusatzsprachen und nicht Leitsprachen sind.
- **`Query.disjunction_max_query`.** tantivy-py hat sie (geprueft in der installierten Fassung). Sie ist das `best_fields` der Elastic-Welt und summiert nicht. Der Preis ist, dass die Anfrage dann je Feld gebaut statt vom Parser erzeugt wird, also ein Eingriff in `query/rewrite.py` mitsamt Filter-Praefixen, Umlautvarianten und Tiefenbegrenzung. Kein Pflichtstueck fuer v1.3, aber der richtige naechste Schritt, wenn eine Messung die Verschiebung zeigt.

---

## Teil 3: Feature Landscape

### Table Stakes (ohne diese fuehlt sich der Sprachausbau unfertig an)

| Feature | Warum erwartet | Komplexitaet | Notes |
|---|---|---|---|
| Vier Analysatorketten es/it/nl/pt, Snowball-Stemmer plus eingebaute Stoppwortliste | Ohne Stemming findet `contratos` das Wort `contrato` nicht. Das ist der ganze Grund, warum die Sprache im Schema steht | NIEDRIG | M1: tantivy bringt alles mit. Vier Funktionen nach dem Muster von `english_analyzer()` |
| Reihenfolge `lowercase, stopword, ascii_fold, remove_long, stemmer` | M2 und M3. Falsche Reihenfolge leckt Stoppwoerter oder trennt Akzentschreibweisen | NIEDRIG | Weicht bewusst von der vorhandenen englischen Kette ab. Braucht einen Test je Sprache mit genau den Saetzen aus M2 |
| Sechs Koerperfelder im Schema, immer alle, befuellt nur nach `FINDLING_LANGUAGES` | Ein Schema je Installation, sonst gibt es so viele Indexformen wie Konfigurationen | NIEDRIG | Muster existiert (`_index_english`). Nur verallgemeinern |
| `FINDLING_LANGUAGES` bleibt bei `de,en` ab Werk | Bestandsinstallationen duerfen durch ein Minor-Upgrade nicht langsamer oder groesser werden. Linie D-04 | NIEDRIG | Deckt sich mit dem OCR-Entscheid vom 21.09.: neun angeboten, drei ab Werk |
| Schema-Migration, die das Indexverzeichnis wirklich neu anlegt | `open_index` oeffnet ein vorhandenes Verzeichnis mit dessen ALTEM Schema. Vier neue Felder erreichen eine Bestandsinstallation sonst nie, und die Suche im neuen Feld ist stumm | **HOCH** | Der einzige echte Risikoposten. Details unten bei den Abhaengigkeiten |
| Reindex nur, wenn eine neue Sprache wirklich eingeschaltet wird | Ein Zwangs-Reindex fuer jede Bestandsinstallation, nur damit vier leere Felder entstehen, waere ein Tagewerk Rechenzeit fuer null Nutzen | MITTEL | `start_rebuild_on_drift` traegt das bereits, aber die Driftmarken muessen sprachabhaengig werden |
| Sprachfaelle je Sprache in CI, ohne Fremdbestand | Der einzige Beweis, dass eine Sprache wirklich geht. Das Muster steht in `docs/measurements/2026-09-a4-sprachfaelle-ci/` | MITTEL | Braucht Korpusdateien je Sprache. Der Reddit-Nutzer, der Hilfe angeboten hat (BL-F02), ist genau dafuer einzuplanen |
| UI-Kataloge es/it/nl/pt | Wer die Suche in seiner Sprache bekommt, erwartet die Oberflaeche dazu | MITTEL | **197 Schluessel, nicht 174.** BL-F02 nennt die alte Zahl; `docs/l10n-french.md` zaehlt 197 aus `de.json`, davon 37 mit printf-Direktiven und 5 mit Pluralformen |
| Dokumentierte Grenzen je Sprache | Eine Suche, die eine Grenze verschweigt, erzeugt einen Fehlerbericht statt einer Erwartung | NIEDRIG | Drei Saetze: `año`/`ano` fallen zusammen, portugiesische Schreibung vor 1990 wird nicht vereinheitlicht, Komposita nur fuer de und nl |

### Differenzierer (nicht erwartet, aber wertvoll)

| Feature | Wertversprechen | Komplexitaet | Notes |
|---|---|---|---|
| **Niederlaendische Komposita-Zerlegung** | Der eine Hebel, der Niederlaendisch von "stemmt" auf "findet" hebt. M5: sechs von sechs Verwaltungskomposita. Kein Produkt im Selfhost-Segment kann das fuer Niederlaendisch, und die NL-Outreach-Spur (GovChat-NL) ist offen | **HOCH** | Braucht eine eigene Rezeptmessung wie fuer Deutsch (Fenstergrenzen, Fugen, Fehltrennungen), eine zweite Wortlistenquelle im Abbild, einen zweiten Automaten (RAM!) und eine eigene Digest-Marke. Nicht in den 5 bis 10 PT enthalten, die BL-F02 fuer Baustein 2 schaetzt |
| Permissive Lizenz der niederlaendischen Liste | BSD-3-Clause und CC-BY-3.0 statt der GPL-Kaskade des deutschen Falls. Weniger Lizenztext, weniger Erklaerungsbedarf | NIEDRIG | Nebenertrag von M5, gehoert in THIRD-PARTY.md |
| `disjunction_max_query` statt Score-Summe | Der sprachrichtige Treffer gewinnt gegen den Zufallstreffer in vier Ketten. Wird erst bei sechs Feldern sichtbar | MITTEL bis HOCH | Eingriff in `query/rewrite.py`. Erst nach einer Messung, siehe Frage 3 |
| Warnung, wenn `FINDLING_LANGUAGES` und `FINDLING_OCR_LANGUAGES` auseinanderlaufen | Wer `body_es` einschaltet, aber `deu+eng+fra` OCR fahren laesst, indexiert aus spanischen Scans Rauschen und sucht darin sauber. Das ist ein stiller Totalausfall | NIEDRIG | Paperless-ngx leitet die Suchsprache aus der OCR-Sprache ab. Ableiten waere hier zu viel (siehe offene Fragen), warnen ist billig und richtig |
| Ein `pt`-Katalog statt zweier | Nextcloud kuerzt `pt_BR` und `pt_PT` auf `pt`, wenn kein exakter Treffer da ist (`LanguageIterator`, Fall 3). Ein Katalog bedient beide | NIEDRIG | MEDIUM-Konfidenz fuer den Dateiladepfad, siehe offene Fragen. Ein Test auf der Test-Nextcloud klaert es in Minuten |

### Anti-Features (klingen richtig, sind es nicht)

| Feature | Warum gewuenscht | Warum problematisch | Stattdessen |
|---|---|---|---|
| **Automatische Spracherkennung je Dokument** | "Dann kostet der Index nicht das Sechsfache" | Gemischtsprachige Dokumente sind in einer Nextcloud der Normalfall, und eine Zuordnung macht sie in der zweiten Sprache unauffindbar. Eine Falscherkennung ist stumm: die Datei ist da, sie taucht nur nie auf. Dazu eine Bibliothek plus Modell im RAM-Budget einer 4-GB-Box, und jede Verbesserung der Erkennung erzwingt einen Reindex | Derselbe Text in alle eingeschalteten Felder, Menge ueber `FINDLING_LANGUAGES` deckeln. Der Plattenzuwachs aus M6 ist der Preis, und er ist der guenstigere |
| **Spracherkennung der Suchanfrage** | "Dann suchen wir nur im richtigen Feld und sparen Rechenzeit" | 2,4 Terme im Mittel gegen mehr als 50 Zeichen Bedarf. Elastic raet ausdruecklich ab, Meilisearch dokumentiert die eigene Schwaeche. Eine Suche, die bei kurzen Woertern wuerfelt, ist schlimmer als eine, die immer alles absucht | Immer alle befuellten Felder, Rangordnung ueber Feld-Boosts |
| **Sprachumschalter oder Sprach-Chip in der Suchoberflaeche** | "Der Nutzer weiss doch, was er sucht" | Er weiss es nicht: die Sprache der Datei ist nicht die Sprache des Suchenden. Der Umschalter waere eine Pflichteinstellung in einem Produkt, dessen Kernversprechen "niemand muss etwas einstellen" lautet. Dazu 4 bis 6 neue Katalogschluessel mal sechs Sprachen und ein Parameter, der durch die Berechtigungsgrenze reisen muesste | Kein Schalter. Wenn eine Sprache stoert, schaltet der Admin sie im Container aus |
| **Alle sechs Sprachen ab Werk an** | "Zero-Config heisst doch: geht sofort" | 68 Prozent mehr Indexplatz und die Score-Aufsummierung aus Frage 3 fuer jede Instanz, die fuenf der sechs Sprachen nie sieht. Und ein Zwangs-Reindex fuer jede Bestandsinstallation | Angeboten und nicht Standard, genau wie die neun OCR-Sprachen seit 1.2.0. Derselbe Entscheid, dieselbe Begruendung |
| **Ein gemeinsames multilinguales Koerperfeld** | "Ein Feld ist billiger als sechs" | Ein Analyzer ueber gemischten Text unter-stemmt die einen und ueber-stemmt die anderen. Verworfen in allen gefundenen Leitfaeden | Feld je Sprache |
| **Index je Sprache** | Das andere Elastic-Muster | Sechs tantivy-Verzeichnisse, sechs Writer-Locks, sechs Mergevorgaenge und eine Zusammenfuehrung der Rangordnungen von Hand, auf einer 4-GB-Box. Und gemischtsprachige Dokumente muessten in mehrere Indexe | Ein Index, sechs Felder |
| **Komposita-Zerlegung fuer es, it, pt** | "Was fuer Deutsch gut ist, ist fuer alle gut" | Romanische Sprachen bilden Zusammensetzungen getrennt oder mit Praeposition (`contrato de arrendamiento`). Ein Zerleger findet dort nichts zu trennen und produziert nur Fehltrennungen. Rezept B des deutschen Falls zeigt, wohin das fuehrt | Nur de und nl. Ausdruecklich in die Doku, damit die Frage nicht wiederkommt |
| **Muttersprachler-Abnahme als Gate fuer alle vier Kataloge** | Das war das FR-Gate | Vier Muttersprachler gibt es nicht, und das Gate haette den Milestone auf unbestimmte Zeit geblockt. BL-F02 sieht das schon so | Maschinell erzeugt, gegen dieselben vier Katalog-Gates gepruegt wie FR, dazu ein sichtbarer Hinweis "Uebersetzung ohne Muttersprachlerabnahme, Korrekturen willkommen" mit Link auf das Repo. Der Reddit-Faden ist die Rezension |
| **Nutzung der Nextcloud-Oberflaechensprache als Suchsprache** | "Die Information ist doch da" | Sie ist da und sie ist falsch. Siehe Frage 3 | Ignorieren |

---

## Teil 4: Feature Dependencies

```
[Vier Analysatorketten es/it/nl/pt]
    |
    +--requires--> [Reihenfolge stopword vor ascii_fold]        (M2/M3, sonst leckende Stoppwoerter)
    |
    +--requires--> [Vier neue Koerperfelder im Schema]
                        |
                        +--requires--> [SCHEMA_VERSION-Sprung]
                        |                   |
                        |                   +--requires--> [Migration, die das INDEXVERZEICHNIS neu anlegt]
                        |                                        |
                        |                                        +--requires--> [Version00XX00Date...-Migration
                        |                                                        der PHP-Haelfte, Pflicht je Minor]
                        |
                        +--requires--> [ANALYZER_VERSION-Sprung]
                        |
                        +--enhances--> [Feld-Boosts fuer die vier neuen Felder]
                                            |
                                            +--enhances--> [disjunction_max_query]   (optional, nach Messung)

[Niederlaendische Komposita-Zerlegung]
    |
    +--requires--> [wdutch im Abbild]                (Dockerfile, THIRD-PARTY.md, Lizenztext)
    +--requires--> [Rezeptmessung wie 2026-09-komposita-rezept-a]
    +--requires--> [Zweiter Automat + eigener Fugen-Satz {s, en, e}]
    +--requires--> [EIGENE Digest-Marke, getrennt von wordlist_hash]
    +--conflicts--> [RAM-Budget der 4-GB-Box]        (23 MB je Automat, dauerhaft)

[Sprachfaelle je Sprache in CI]
    +--requires--> [Korpusdateien je Sprache in testdata/corpus]
    +--requires--> [Vier Analysatorketten]

[UI-Kataloge es/it/nl/pt]
    +--independent--  (kein technischer Zwang zur Suchseite, kann parallel laufen)
    +--requires--> [Entscheid pt vs pt_BR vs pt_PT]

[OCR es/it/nl/pt]  ---- ist seit 1.2.0 da, aber NICHT Standard ----> [Warnung bei Divergenz]
```

### Abhaengigkeiten im Klartext

**Die Migration ist der eine harte Posten, und sie ist gefaehrlicher als sie aussieht.** `open_index` macht `Index.open(path) if Index.exists(path) else Index(build_schema(), path)`. Eine Bestandsinstallation oeffnet also ihr altes Zwei-Feld-Schema und behaelt es fuer immer. Vier neue Felder in `build_schema()` erreichen sie nicht. Und dann passiert genau das, was dieses Projekt schon einmal getroffen hat: die Suche im neuen Feld ist **stumm**, nicht kaputt. Die Migration muss das Verzeichnis loeschen und neu anlegen, nicht nur die Generation erhoehen. `start_rebuild_on_drift` erhoeht die Generation und macht jedes Verdikt veraltet, aber es baut kein Verzeichnis neu; das ist der Unterschied zwischen "die Dokumente werden noch einmal gelesen" und "sie werden in ein Schema geschrieben, das die Felder hat".

**Eine Falle in der Driftmarke.** `expected_versions()` fuehrt `wordlist_hash` als Marke. Kommt eine niederlaendische Liste dazu und geht ihr Digest in dieselbe Marke ein, loest sie einen Rebuild bei **jeder** Installation aus, auch bei denen, die nie Niederlaendisch einschalten. Die niederlaendische Liste braucht eine eigene Marke, und diese Marke darf nur gesetzt sein, wenn `nl` befuellt wird.

**Die OCR-Haelfte ist da, aber nicht scharf.** Seit 1.2.0 traegt das Abbild `tesseract-ocr-spa/-ita/-nld/-por`, Standard bleibt `deu+eng+fra`. Wer `body_es` einschaltet und die OCR nicht mitzieht, indexiert aus spanischen Scans Buchstabensalat. Das ist kein Fehler, den jemand meldet, weil es wie "der Scan war halt schlecht" aussieht.

---

## Teil 5: MVP fuer v1.3

### Liefern (v1.3)

- [ ] Vier Analysatorketten es/it/nl/pt in der gemessenen Filterreihenfolge, mit je einem Test aus den Saetzen von M2 und M3 - ohne sie gibt es das Feature nicht
- [ ] Sechs Koerperfelder im Schema, befuellt nach `FINDLING_LANGUAGES`, Werkseinstellung bleibt `de,en` - die Bauform, die den Zuwachs aus M6 nur den Bestellern berechnet
- [ ] `SCHEMA_VERSION`- und `ANALYZER_VERSION`-Sprung plus Migration, die das Indexverzeichnis neu anlegt, plus `Version00XX00Date...` der PHP-Haelfte - Pflicht je Minor-Sprung, und der stumme Ausfall waere sonst genau hier
- [ ] Reindex nur bei tatsaechlich eingeschalteter neuer Sprache, Bestandsinstallationen mit `de,en` bleiben unberuehrt - Linie D-04
- [ ] Feld-Boosts fuer die vier neuen Felder unter `body_en`, mit begruendendem Kommentar - der billige Teil der Antwort auf die Score-Aufsummierung
- [ ] Sprachfaelle je Sprache in CI, Muster `2026-09-a4-sprachfaelle-ci`, ohne Fremdbestand - der einzige Beweis, dass eine Sprache geht
- [ ] Warnung beim Start, wenn `FINDLING_LANGUAGES` eine Sprache fuehrt, die `FINDLING_OCR_LANGUAGES` nicht hat - eine Zeile gegen einen stillen Totalausfall
- [ ] UI-Kataloge es/it/nl/pt, 197 Schluessel, gegen die vier vorhandenen Katalog-Gates - Baustein 3 aus BL-F02
- [ ] Grenzenabschnitt in der Doku, dreisprachig im Store-Text nur als Verweis - Kurztext-Regel des Owners

### Nach Bestaetigung (v1.3, wenn der Zuschnitt traegt)

- [ ] **Niederlaendische Komposita-Zerlegung** samt Rezeptmessung - Ausloeser: der Milestone haelt Termin und die NL-Spur (GovChat-NL) bleibt warm. **Empfehlung: als eigene Phase mit eigenem Tor schneiden, nicht in die Sprachfelder-Phase hineinschieben.** Es ist eine zweite Wortlistenquelle, ein zweiter Automat im RAM-Budget und eine eigene Messreihe, also ungefaehr so gross wie alles andere zusammen. Wenn es nicht passt, faellt es als Ganzes und nicht halb

### Spaeter (v1.4+)

- [ ] `disjunction_max_query` - erst wenn eine Messung die Rangverschiebung aus Frage 3 auf echten Daten zeigt. Vorher ist es ein Eingriff in `query/rewrite.py` ohne Beleg
- [ ] Franzoesisches Koerperfeld - auffaellige Luecke: FR hat OCR und Katalog, aber keine lexikalische Kette. Sobald sechs Felder stehen, ist das siebte fast umsonst, aber es gehoert nicht in einen Milestone, der es nicht im Ziel fuehrt
- [ ] Niederlaendische Betonungsakzente als `custom_stopword` - nur wenn jemand es meldet
- [ ] Getrennte Wortlaute fuer pt_BR und pt_PT - erst wenn ein Nutzer aus einem der beiden Raeume sich meldet

---

## Teil 6: Priorisierung

| Feature | Nutzwert | Aufwand | Prioritaet |
|---|---|---|---|
| Vier Analysatorketten, richtige Filterreihenfolge | HOCH | NIEDRIG | P1 |
| Sechs Felder im Schema, Befuellung nach Einstellung | HOCH | NIEDRIG | P1 |
| Migration mit echtem Verzeichnisneubau | HOCH (sonst stumm) | HOCH | P1 |
| Reindex nur bei eingeschalteter Sprache | HOCH | MITTEL | P1 |
| Sprachfaelle je Sprache in CI | HOCH (Beweis) | MITTEL | P1 |
| Feld-Boosts der neuen Felder | MITTEL | NIEDRIG | P1 |
| Warnung bei Sprach-/OCR-Divergenz | MITTEL | NIEDRIG | P1 |
| UI-Kataloge es/it/nl/pt | MITTEL | MITTEL | P1 |
| Grenzen dokumentiert | MITTEL | NIEDRIG | P1 |
| Niederlaendische Komposita | HOCH (fuer NL) | HOCH | P2 |
| `disjunction_max_query` | MITTEL | MITTEL bis HOCH | P3 |
| Franzoesisches Koerperfeld | MITTEL | NIEDRIG | P3 |
| Getrennte pt_BR/pt_PT-Wortlaute | NIEDRIG | MITTEL | P3 |

---

## Teil 7: Offene Fragen fuer die Planung

1. **Wird der Reindex bei eingeschalteter Sprache erzwungen oder angeboten?** Ein Volllauf ueber 52.000 Dateien ist auf der Zielhardware ein Tagewerk. Vorschlag: erzwingen, aber mit dem vorhandenen Banner und dem Generationsmechanismus, also sichtbar und fortsetzbar, und die Suche bleibt waehrenddessen auf dem alten Index benutzbar. Muss gegen `start_rebuild_on_drift` geprueft werden, das heute in dieselbe Richtung arbeitet.
2. **Wird `FINDLING_LANGUAGES` aus `FINDLING_OCR_LANGUAGES` abgeleitet, wie Paperless-ngx es tut?** Zero-Config spraeche dafuer. Dagegen spricht, dass eine bestehende Instanz mit `FINDLING_OCR_LANGUAGES=spa+deu` dann bei einem Minor-Upgrade unangekuendigt einen Reindex ausloest. Empfehlung: **nicht ableiten, nur warnen.** Owner-Entscheid.
3. **`pt`, `pt_BR` oder `pt_PT` fuer den Katalog?** `LanguageIterator` kuerzt auf `pt`, ein Katalog wuerde also beide bedienen. Das ist fuer den Sprachiterator HIGH und fuer den Dateiladepfad der App-Kataloge MEDIUM. Auf der Test-Nextcloud in Minuten zu klaeren, und das gehoert vor die Uebersetzungsarbeit, nicht danach.
4. **Traegt das RAM-Budget einen zweiten Komposita-Automaten?** Der deutsche kostet dauerhaft rund 23 MB. Ein niederlaendischer kommt obendrauf, aber nur auf Instanzen mit `nl`. Die RAM-Tabelle in CLAUDE.md braucht eine Zeile, und die Messphase BL-F03 koennte sie mitnehmen.
5. **Wie gross wird der Index wirklich?** M6 rechnet mit 0,076 je Feld aus einem deutschen Korpus. Ob ein spanisches Koerperfeld ueber deutschem Text denselben Faktor hat, ist nicht gemessen. Wenn die Messphase BL-F03 ohnehin faehrt, ist die Indexgroesse bei sechs eingeschalteten Sprachen eine billige sechste Zahl.

---

## Sources

**Eigene Messungen, 2026-09-23** (HIGH, gegen `tantivy 0.26.0` in `backend/.venv`)
- M2 bis M5: Filterreihenfolge, Akzentfaltung, italienische Elision, niederlaendische Kompositazerlegung, Ueberlappung der Ketten. Skripte sind Einzeiler ueber `TextAnalyzerBuilder`, jederzeit wiederholbar

**Eigener Quellcode und eigene Messberichte** (HIGH)
- `backend/src/findling/index/analyzer.py`, `index/schema.py`, `index/open.py`, `index/writer.py`, `query/rewrite.py`, `config.py`
- `docs/measurements/2026-09-a4-sprachfaelle-ci/README.md`, `docs/l10n-french.md`, `docs/german-analyzer.md`
- `.planning/BACKLOG.md` BL-F02 und BL-F03

**tantivy** (HIGH)
- `quickwit-oss/tantivy-py`, `src/tokenizer.rs` und `docs/api/tantivy/tantivy.md`: 18 Stemmer-Sprachen, 13 Stoppwortlisten, acht Filter, `Query.disjunction_max_query`
- snowballstem.org, italienische Stoppwortliste: elidierte Formen als eigene Eintraege
- snowballstem.org, portugiesischer Algorithmus: vereinheitlicht die Schreibungen vor und nach 1990 nicht

**Paperless-ngx** (HIGH, offizielle Doku)
- docs.paperless-ngx.com/configuration: `PAPERLESS_SEARCH_LANGUAGE` (eine Stemmer-Sprache, abgeleitet aus `PAPERLESS_OCR_LANGUAGE`, Wechsel baut den Index neu), `PAPERLESS_ADVANCED_FUZZY_SEARCH_THRESHOLD`
- Diskussion #8293: wie Nutzer heute mit gemischtsprachigen Bestaenden umgehen (MEDIUM)

**Elastic** (HIGH fuer die Strategie, MEDIUM fuer Sekundaerartikel)
- elastic.co/blog/multilingual-search-using-language-identification-in-elasticsearch: per-field gegen per-index, ausdrueckliche Warnung vor Sprachidentifikation der Anfrage (2,4 Terme, mehr als 50 Zeichen noetig)
- elastic.co/search-labs/blog/compound-word-search
- pulse.support und neverblink.ai Wissensbasen zu multi_match, `most_fields` gegen `best_fields`, Indexgroesse bei N Sprachfeldern (MEDIUM, Sekundaerquellen)

**Meilisearch** (HIGH, offizielle Doku)
- meilisearch.com/docs/capabilities/indexing/how_to/handle_multilingual_data: `localizedAttributes`, `locales`, dokumentierte Schwaeche der Automatik bei kurzen Texten

**Nextcloud** (HIGH)
- `nextcloud/server` stable34, `apps/files/l10n/`: Sprachcodes, es und it und nl vorhanden, Portugiesisch nur als `pt_BR` und `pt_PT`
- `nextcloud/server`, `lib/private/L10N/LanguageIterator.php`: Kuerzung von `pt_BR` auf `pt` als Rueckfallstufe
- `nextcloud/fulltextsearch_elasticsearch` PR #57: nur Tokenizer konfigurierbar, kein Analyzer (MEDIUM)

**Debian** (HIGH)
- packages.debian.org/trixie/wdutch und sources.debian.org `dutch` 1:2.20.19+1-3 `debian/copyright`: OpenTaal, BSD-3-Clause und CC-BY-3.0, installiert `/usr/share/dict/dutch` und `/usr/share/dict/nederlands`

---
*Feature research fuer: mehrsprachige lexikalische Suche, Milestone v1.3 Sprachausbau*
*Researched: 2026-09-23*
