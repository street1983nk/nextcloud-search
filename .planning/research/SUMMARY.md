# Project Research Summary

**Projekt:** Findling (Nextcloud Zero-Config-Suche)
**Domain:** Milestone v1.3 "Sprachausbau" - lexikalische Suche es/it/nl/pt via Tantivy-Sprachfelder, Schema-/Migrations-Umbau, UI-Kataloge, Messphase BL-F03
**Researched:** 2026-09-23
**Confidence:** HIGH fuer Tantivy-Verhalten, Schema-Mechanik und die meisten Pitfalls (alles gegen die installierte `tantivy==0.26.0`/`0.26.2` und den Quellcode dieses Repos gemessen). MEDIUM fuer einzelne Nextcloud-Katalogfragen (aus dem Serverquellbaum gelesen, nicht gegen eine laufende Instanz geprueft). Ein zentraler Punkt (Filterreihenfolge `ascii_fold`) ist zwischen den vier Forschern **nicht** einheitlich und wird unten als offener Entscheid behandelt, nicht geglaettet.

## Executive Summary

v1.3 ist kein Feature im herkoemmlichen Sinn, sondern ein **Schema-Sprung auf einem produktiven Bestandsindex**, und genau darin liegt die ganze Schwierigkeit des Milestones. Tantivy selbst bringt fuer Spanisch, Italienisch, Niederlaendisch und Portugiesisch bereits alles mit, was gebraucht wird (Snowball-Stemmer und -Stoppwortlisten, BSD-3-Clause, AGPL-vertraeglich): es muss kein einziges neues Paket installiert werden, nur ein Patch-Upgrade von `tantivy` 0.26.0 auf 0.26.2 (behebt einen Rust-Panic bei unbekannten Sprachnamen und einen Union-Scorer-Bug). Die eigentliche Arbeit ist Code in diesem Repo: vier neue Analyseketten, vier neue Schemafelder, ein Umbauweg fuer Bestandsindizes und zehn neue Katalogdateien.

Der empfohlene Ansatz in einem Satz: **Sechs Schemafelder immer im Schema, befuellt nur nach `FINDLING_LANGUAGES` (Modell A, derselbe Text in jedes aktive Feld, keine Spracherkennung), und der Indexumbau laeuft als Re-Analyse aus dem alten, gespeicherten `body_de` heraus statt als Vollreindex ueber Nextcloud.** Das verwandelt einen geschaetzten 19-Stunden-Vollreindex in einen Ein-bis-drei-Stunden-Umbau, ohne Download, ohne erneutes OCR, ohne Neuberechnung der Vektoren. Alle drei Feature-Researcher und der Architektur-Researcher kommen unabhaengig zu demselben Feldmodell und lehnen Spracherkennung uebereinstimmend als Anti-Feature ab (kurze Dateinamen, OCR-Rauschen, gemischtsprachige Dokumente, und vor allem: eine falsch erkannte Sprache ist ein stiller, durch nichts angezeigter Totalausfall fuer dieses Dokument).

Das groesste Risiko ist ein **Totalausfall-Pfad, der heute schon im Code angelegt ist und durch drei unabhaengige Messungen bestaetigt wurde**: Ein tantivy-Index oeffnet auf einer Bestandsinstallation immer sein altes, persistiertes Schema; ein neues Feld im Code erreicht dieses Verzeichnis nie von selbst. Schreibseitig verschwindet der Wert dann lautlos (`Document.from_dict` verwirft unbekannte Felder ohne Fehler), leseseitig wirft `parse_query_lenient` bei einem unbekannten Feldnamen einen `ValueError`, den der Suchpfad abfaengt und als leere, degradierte Antwort zurueckgibt - auf jeder Bestandsinstallation wuerde **jede** Suche, nicht nur die neuen Sprachen, dauerhaft leer laufen, mit nur einer WARNING-Zeile im Log. Die Gegenmassnahme ist architektonisch klar: Schema-Erweiterung und Freischaltung der neuen Suchfelder muessen in getrennten Phasen liegen, mit einem funktionierenden, geprueften Umbauweg dazwischen, und die bestehende Upgrade-Beweisstrecke in CI muss umgedreht (nicht entschaerft) werden, weil sie heute exakt das Gegenteil dessen behauptet, was v1.3 tut.

## Key Findings

### Recommended Stack

Kein neues PyPI- oder Systempaket. Einzige Aenderung: `tantivy` 0.26.0 -> 0.26.2 (Patch-Sprung, `index_format v7` unveraendert, kein zusaetzlicher Reindex-Ausloeser). Snowball-Stemmer und -Stoppwortlisten fuer alle vier Sprachen sind in tantivy einkompiliert (BSD-3-Clause, AGPL-vertraeglich). Eine eigene, aus `stopwords.rs` erzeugte Ergaenzungsliste gefalteter Stoppwoerter (77 es / 10 it / 30 pt / 0 nl, insgesamt 117 Woerter) schliesst die Luecke, die die Faltung sonst in den Stoppwortlisten reisst. Sprach-Erkennung (lingua, fasttext, py3langid, langdetect, pycld3) wurde geprueft und einstimmig abgelehnt: zu gross fuers RAM-Budget, Lizenzfragen (fasttext-Modell CC BY-SA 3.0), fehlende ARM-Wheels, oder eine ungeklaerte numpy-Abhaengigkeit.

**Core technologies:**
- `tantivy` 0.26.2 - Suchmaschine, Analysekette, Stemmer, Stoppwoerter - bringt alles Noetige mit, Upgrade behebt Panic-Risiko und einen Union-Scorer-Bugfix
- Snowball-Stemmer/-Stoppwortlisten (in tantivy) - Stammformbildung und Stoppwortentfernung es/it/nl/pt - kein Modell, kein RAM-Zuwachs, BSD-3-Clause
- Eigene gefaltete Ergaenzungs-Stoppwortliste (117 Woerter) - schliesst die Luecke zwischen Akzentfaltung und Stoppwortvergleich - maschinell aus `stopwords.rs` erzeugt und per Hash-Test gehalten

### Expected Features

**Must have (table stakes):**
- Vier Analyseketten es/it/nl/pt mit Snowball-Stemmer und eingebauter Stoppwortliste
- Sechs Koerperfelder im Schema, **immer alle**, befuellt nur nach `FINDLING_LANGUAGES` (Werkseinstellung bleibt `de,en`)
- Schema-Migration, die das Indexverzeichnis wirklich neu anlegt (nicht nur eine Versionsmarke setzt)
- Reindex/Umbau nur bei tatsaechlich eingeschalteter neuer Sprache, Bestandsinstallationen mit `de,en` bleiben unberuehrt
- Feld-Boosts fuer die vier neuen Felder unter `body_en` (z. B. 0,6-0,8), sonst summieren sich Treffer ueber sechs Felder falsch auf
- Sprachfaelle je Sprache in CI, ohne Fremdbestand (Muster `2026-09-a4-sprachfaelle-ci`)
- UI-Kataloge es/it/nl/pt, **199 Schluessel** (nicht 174 - die Zahl ist zwischen Phase 11 und heute viermal gestiegen, im Plan aus der Datei zaehlen, nicht uebernehmen)
- Warnung beim Start, wenn `FINDLING_LANGUAGES` eine Sprache fuehrt, die `FINDLING_OCR_LANGUAGES` nicht abdeckt
- Dokumentierte Grenzen (ano/ano fallen zusammen, pt-Rechtschreibreform wird nicht vereinheitlicht, Komposita nur de/nl)

**Should have (differenzierend):**
- Niederlaendische Komposita-Zerlegung (`split_compound`, lizenzkonform via Debian `wdutch`/OpenTaal, BSD-3-Clause + CC-BY-3.0) - kein Konkurrenzprodukt im Selfhost-Segment kann das fuer Niederlaendisch, aber es ist so gross wie der Rest des Milestones zusammen (zweite Wortliste, zweiter 23-MB-Automat, eigene Digest-Marke) -> **eigene Phase mit eigenem Tor**, nicht in die Sprachfelder-Phase hineinschieben
- `disjunction_max_query` statt Score-Summierung - erst nach einer Messung der Rangverschiebung auf echten Daten

**Defer (v1.4+):**
- Franzoesisches Koerperfeld (FR hat OCR+Katalog, aber keine lexikalische Kette - auffaellige Luecke, aber ausserhalb des Ziels dieses Milestones)
- Getrennte pt_BR/pt_PT-Wortlaute fuer die Suche selbst
- Niederlaendische Betonungsakzente als eigene `custom_stopword`-Liste

**Anti-Features (explizit ablehnen):**
- Automatische Spracherkennung, Dokument- oder Anfrageseite (stiller Totalausfall bei Fehlerkennung, RAM-/Lizenzkosten, Anfragen haben im Schnitt 2,4 Terme - zu kurz fuer Erkennung)
- Sprachumschalter/Sprach-Chip in der UI (widerspricht Zero-Config)
- Alle sechs Sprachen ab Werk an (68-90 % mehr Indexplatz fuer jede Bestandsinstallation ohne Nachfrage)
- Ein gemeinsames multilinguales Feld statt Feld je Sprache (unter-/uebersteemt in allen gemischten Faellen)
- Index je Sprache statt Feld je Sprache (mehrere Writer-Locks, mehrere Merges, Ergebnis-Fusion von Hand)
- Komposita-Zerlegung fuer es/it/pt (romanische Sprachen komponieren nicht wie de/nl, ein Zerleger faende dort nichts oder trennt falsch)
- Muttersprachler-Abnahme als Pflicht-Gate fuer alle vier Kataloge (kein Muttersprachler verfuegbar; stattdessen maschinell + Community-Review mit datiertem Vorbehalt, wie beim FR-Katalog)

### Architecture Approach

Die Kernerkenntnis ist strukturell: `DEFAULT_LANGUAGES` hat im Code praktisch nur **einen** Verbraucher (`writer.py:166`), waehrend die echte Sprachbindung an sechs fest verdrahteten Stellen haengt (Analyzer-Namen, Schema-Feldliste, Tokenizer-Registrierung, Suchfeldliste/-boosts, Snippet-Feld, Benchmark). Wer nur die Konstante erweitert, aendert nichts. Ein Tantivy-Index persistiert sein Schema bei der Erzeugung und oeffnet ein Bestandsverzeichnis **immer** mit dessen altem Schema - das ist die Wurzel des Totalausfall-Risikos. Der Ausweg ist eine Re-Analyse-Migration: Weil `body_de` (und implizit `body_en`) als einzige gespeicherte Textkopie im Schema stehen (`stored=True`), laesst sich ein komplett neuer Index mit den sechs Feldern **aus dem alten Index heraus** neu schreiben, ohne Nextcloud, OCR oder Einbettung erneut anzufassen. Der Vektorbestand (`vectors.db`, `sqlite-vec`) bleibt davon unberuehrt, weil er sprachneutral ist und ueber Zeichenoffsets in `body_de` indiziert, die sich durch den Umbau nicht verschieben.

**Major components:**
1. `index/analyzer.py` - vier neue Analyseketten (Fabrik statt vier Funktionen), `ANALYZER_VERSION`-Sprung
2. `index/schema.py` / `index/open.py` - Schema waechst auf 13 Felder, immer vollstaendig gebaut, `SCHEMA_VERSION`-Sprung, vier neue Tokenizer-Registrierungen
3. **`index/rebuild.py` (neu)** - die zentrale neue Komponente: Re-Analyse-Umbau aus dem alten Verzeichnis, Platzpruefung, Wiederaufnahmefaehigkeit, Rueckfall auf Vollreindex
4. `query/rewrite.py` - Feldliste/Boosts werden vom Merker `schema_version` abhaengig gemacht, nicht mehr Konstante (verhindert, dass neue Felder in Anfragen auftauchen, bevor der Umbau fertig ist)
5. `php/lib/Migration/Version001300Date...` - Pflicht-Lockstep-Migration (Kopie des v1.2-Musters), **nicht** der Ort des eigentlichen Indexumbaus (der laeuft im Container als Lifespan-Aufgabe, nicht in `occ upgrade`)
6. `php/l10n/` - zehn neue Katalogdateien (es, it, nl, pt_PT, pt_BR je `.json`/`.js`, da Nextcloud kein `pt` kennt)

Bauordnungs-Prinzip (aus der Architekturrecherche): Schema-Erweiterung und Freischaltung der Query-Feldliste duerfen **nicht im selben Schritt** passieren - dazwischen muss der Umbau fertig und bewiesen sein.

### Critical Pitfalls

1. **Schema erreicht den Bestandsindex nie, Suche antwortet danach dauerhaft leer** - gemessen in zwei Varianten (stiller Datenverlust beim Schreiben, `ValueError` beim Lesen, vom Suchpfad zu leerer Antwort verschluckt). Vermeidung: dritter Zweig in `open_index()`, der bei Feldabweichung den Neubau ausloest statt zu oeffnen; Test gegen ein **wirklich vorhandenes** Alt-Schema-Verzeichnis, nicht gegen ein frisches.
2. **Reindex als volle Neuextraktion statt Re-Analyse** - 19h20 Vollreindex vs. geschaetzt 1-3h Umbau aus dem gespeicherten Text. Vermeidung: Re-Analyse-Pfad, wiederaufnehmbar, mit eigener Platzpruefung (zwei Indexverzeichnisse gleichzeitig, `MIN_FREE_BYTES` reicht nicht).
3. **Die bestehende Upgrade-Beweisstrecke in CI wird entschaerft statt umgedreht** - sie behauptet heute woertlich "kein Merker bewegt sich", was v1.3 absichtlich verletzt. Vermeidung: neuer, zusaetzlicher Pruefschritt mit umgekehrten Behauptungen (Schema bewegt sich um genau eine Stufe, Banner erscheint und verschwindet, alte Trefferzahlen bleiben nach dem Umbau gleich, ein neu gefundenes spanisches Dokument beweist den echten Zugewinn); der alte Schritt bleibt fuer index-kompatible Minors erhalten.
4. **`ascii_fold`-Position in der Kette** - siehe eigener Abschnitt unten, offener Entscheid zwischen den Forschern.
5. **Unvalidierter Sprachname bringt den Container per Rust-Panic zu Fall** - `Filter.stopword("romanian")` o.ae. wirft in 0.26.0 einen `PanicException`, keine handhabbare Exception. Vermeidung: geschlossene Positivliste (Muster `OCR_LANGUAGE_ALLOWLIST`), Upgrade auf 0.26.2 macht daraus wenigstens einen `ValueError`.
6. **Sprachauswahl fehlt in den Versionsmarken** - ein Admin, der nachtraeglich `nl` einschaltet, bekommt ohne eigene Marke keinen Rebuild-Hinweis; nur neu angefasste Dateien bekommen niederlaendische Terme, der Bestand bleibt dauerhaft lueckenhaft, ohne dass irgendwo ein Hinweis erscheint. Vermeidung: `languages` als sechster Merker in `expected_versions()`.
7. **Suche ist waehrend des Umbaus leer, ohne Ankuendigung** - Vermeidung: alter Index bedient Anfragen weiter, bis der neue fertig ist (Grund fuer den Zwei-Verzeichnisse-Ansatz statt Ueberschreiben); Banner mit Fortschritt statt des heutigen Reindex-Banners (das faelschlich zu `occ findling:index --restart` aufruft, was 19h Vollcrawl statt des billigen Umbaus ausloesen wuerde).

## Der offene Entscheid: Position von `ascii_fold` in der Kette

Die vier Recherchen widersprechen sich hier, und der Widerspruch wird bewusst **nicht geglaettet**, weil alle drei Positionen mit eigenen Messungen belegt sind, die jeweils unterschiedliche Wortpaare pruefen.

**Position 1 - STACK.md: `lowercase -> ascii_fold -> stopword -> custom_stopword(gefaltet) -> remove_long -> stemmer`.**
Beleg: Akzentierte und ASCII-Eingabe liefern in dieser Kette immer denselben Term (`informacion` mit Akzent / `informacion` ohne -> beide `informacion`), aber akzentuierte Stoppwoerter (`estan`, `mas`, `tambem`, `nao`, jeweils mit Akzent im Original) ueberleben die Stoppwortliste, weil die Liste exakt vergleicht und nach dem Falten nicht mehr trifft. Die vorgeschlagene Loesung ist eine zusaetzliche, bereits gefaltete Ergaenzungsliste (`Filter.custom_stopword`, 77/10/30/0 Woerter aus `stopwords.rs` erzeugt), die genau diese Luecke schliesst.

**Position 2 - PITFALLS.md (Pitfall 4): `ascii_fold` gehoert **hinter** den Stemmer: `lowercase -> stopword -> remove_long -> stemmer -> ascii_fold`.**
Beleg: Bei Faltung **vor** dem Stemmer bleibt die akzentuierte Singularform (mit Akzent auf dem o) als unveraendertes Wort ohne Stammform stehen, waehrend die zugehoerige Pluralform korrekt gestemmt wird - zwei Formen desselben Lemmas landen auf verschiedenen Termen, weil die romanischen Snowball-Algorithmen die akzentuierte Endung fuer ihre Suffixregeln brauchen. Faltung **nach** dem Stemmer liefert in derselben Messung beide Formen korrekt auf denselben Stamm. Zusaetzlich: Faltung vor dem Stoppwortfilter laesst das italienische Wort fuer "warum" (mit Akzent) als Muellterm durch, weil die Stoppwortliste exakt vergleicht.

**Position 3 - FEATURES.md (M2): Faltung gehoert **hinter** die Stoppwortliste**, mit derselben Begruendung wie Pitfall 4 (Stoppwortlisten vergleichen akzentuiert und exakt; fruehes Falten laesst mehrere Reststoppwoerter durch, gemessen 3 Lecks fuer pt, 2 fuer es, 1 fuer it). FEATURES.md nennt ausserdem einen Gegenfall: Niederlaendische Betonungsakzente sind unakzentuiert selbst Stoppwoerter und werden nur entfernt, wenn zuerst gefaltet wird - FEATURES empfiehlt trotzdem die einheitliche Reihenfolge Stoppwortfilter-dann-Faltung und raet, den niederlaendischen Sonderfall ueber eine kleine `custom_stopword`-Liste zu loesen, falls er je auffaellt.

**Wo sich die drei tatsaechlich unterscheiden:** Einigkeit besteht, dass Faltung **hinter** dem rohen Stoppwortfilter erfolgen sollte (Position 2 und 3 sind sich hier einig, Position 1 widerspricht mit einer Ergaenzungsliste als Reparatur). Der eigentliche Streitpunkt ist die Position **relativ zum Stemmer**: STACK.md hat in einer eigenen Messung (Reihenfolge Stoppwortfilter, Laengenfilter, Stemmer, dann Faltung) einen Fall gefunden, in dem Falten nach dem Stemmer portugiesische Formen **auseinanderreisst** (die akzentuierte und die unakzentuierte Schreibung desselben Wortes ergeben nach dieser Kette zwei verschiedene Stammformen), waehrend PITFALLS.md exakt an derselben Stelle in der Kette einen Fall gefunden hat, in dem Falten nach dem Stemmer spanische/portugiesische Singular- und Pluralformen **zusammenfuehrt**. Beide Messungen koennen gleichzeitig wahr sein (unterschiedliche Wortpaare, unterschiedliche Flexionsformen desselben Lemmas reagieren unterschiedlich auf den Snowball-Algorithmus), was bedeutet: **keine der drei Ketten ist ueber alle relevanten Wortpaare hinweg fehlerfrei**, ohne dass es bislang eine Messung gibt, die alle drei Faelle gleichzeitig gegen dieselbe Kette prueft.

**Empfehlung fuer den Plan:** Die erste Bau-Phase des Milestones (Analyseketten/Sprachtabelle) entscheidet die Kettenreihenfolge je Sprache **messend**, nicht durch Auswahl einer der drei Quellen. Dafuer werden die Testfaelle aus allen drei Dokumenten zu einer einzigen Tabellentest-Suite zusammengefuehrt, mindestens:
- spanisches Wortpaar Singular/Plural fuer "Information" (Stemming-Konsistenz)
- dasselbe spanische Wort in akzentuierter und unakzentuierter Schreibung (Akzent-Konvergenz)
- portugiesisches Wortpaar Singular/Plural fuer "Information" (Stemming-Konsistenz)
- dasselbe portugiesische Wort in akzentuierter und unakzentuierter Schreibung (Akzent-Konvergenz)
- spanisches "Jahr" akzentuiert/unakzentuiert (Akzent-Konvergenz bei kurzem Wort)
- italienisches "warum" akzentuiert/unakzentuiert und als Stoppwort
- niederlaendisches "een/één" (Betonungsakzent vs. Stoppwort)
- akzentuierte Stoppwoerter es/pt gegen die jeweilige Stoppwortliste

Erst wenn eine Kette (ggf. mit einer Ergaenzungsliste wie in STACK.md) alle diese Paare gleichzeitig korrekt behandelt, gilt die Reihenfolge als abgenommen. Das ist die Stelle, an der `ANALYZER_VERSION` erhoeht wird, und die Messtabelle wird der Abnahmetest fuer Pitfall 4.

## Weitere Konsenspunkte (fraktionsuebergreifend bestaetigt)

- **Upgrade-Pfad ist heute ein Totalausfall-Risiko:** `parse_query_lenient` wirft `ValueError` bei einem unbekannten Feldnamen, der Suchpfad faengt das ab und liefert eine leere, degradierte Antwort - auf jeder Bestandsinstallation wuerde jede Suche leer laufen, nicht nur die neuen Sprachen. Alle vier Recherchen benennen das als das groesste Einzelrisiko.
- **Re-Analyse-Umbau statt Vollreindex:** Weil `body_de`/`body_en` gespeichert sind, kann der neue Index direkt aus dem alten Index gelesen und neu geschrieben werden. Geschaetzt 1-3 Stunden statt der gemessenen 19h20 fuer einen Vollreindex ueber 52.137 Dokumente.
- **Schema traegt immer alle Sprachfelder**, Befuellung wird ausschliesslich ueber `FINDLING_LANGUAGES` gesteuert. Werkseinstellung bleibt `de,en`. Ein leeres Schemafeld kostet nachweislich (gemessen) null Byte und null Millisekunden.
- **Katalogzahl ist 199 Schluessel, nicht 174** (bzw. 197 als Zwischenstand aus Phase 13) - die Zahl beim Planstart aus `php/l10n/de.json` zaehlen, nicht aus der Milestone-Beschreibung uebernehmen.
- **Nextcloud kennt kein `pt`**, nur `pt_BR` und `pt_PT` - zehn statt acht neue Katalogdateien (je zwei Dateien fuer Portugiesisch, `.json` + `.js`).
- **`nplurals=3` fuer es/it/pt** (Standard-gettext-Form, abweichend von der franzoesischen Zwei-Formen-Regel, die im Repo als `FRENCH_PLURAL_FORM` verdrahtet ist), `nl` bleibt bei `nplurals=2; plural=(n != 1);`. Pluralregeln muessen aus den `core/l10n/<lang>.json`-Kerndateien der Ziel-Nextcloud gelesen werden, nicht aus dem Gedaechtnis kopiert.
- **Niederlaendische Komposita** brauchen `Filter.split_compound` mit einer eigenen Wortliste (Debian `wdutch`/OpenTaal, BSD-3-Clause + CC-BY-3.0, lizenzrechtlich guenstiger als die deutsche `wngerman`-Liste). Das ist ein bewusster, eigenstaendiger Entscheid, der den Schnitt des Milestones sprengen kann, und wird deshalb als eigene Phase mit eigenem Tor behandelt, nicht stillschweigend mitgezogen.
- **tantivy-Pin 0.26.0 -> 0.26.2:** `Filter.stopword()` mit einer Sprache ohne eingebaute Liste ist in 0.26.0 ein Rust-Panic (`PanicException`), in 0.26.2 ein sauberer `ValueError`. Zusaetzlich ein Union-Scorer-Bugfix, relevant weil die Suche jetzt breitere `Should`-Gruppen baut.
- **Estnischer Stemmer wird von tantivy nicht unterstuetzt** (`ValueError: Unsupported language: estonian`) - muss aktiv an die Buerokratt/OS2ai-Outreach-Spur kommuniziert werden, bevor dort falsche Erwartungen entstehen.
- **Keine Spracherkennung, weder fuer Dokumente noch fuer Suchanfragen** - als Anti-Feature einstimmig bestaetigt (kurze Texte, OCR-Rauschen, gemischtsprachige Dokumente, stiller Fehler bei Falscherkennung, RAM-/Lizenzkosten fuer Modelle).
- **`deploy-harp.yml`-Upgrade-Strecke braucht eine zweite, umgedrehte Pruefstrecke**, nicht entschaerfte Zusicherungen. Die heutige Strecke beweist "nichts hat sich bewegt" - v1.3 verletzt das absichtlich und muss stattdessen beweisen "der Umbau lief vollstaendig und ohne Datenverlust ab".

## Implications for Roadmap

Basierend auf der kombinierten Recherche ist die vorgeschlagene Phasenstruktur eine **Abhaengigkeitskette mit einem Owner-Tor am Anfang und zwei parallelisierbaren Straengen in der Mitte**, keine freie Reihenfolge:

### Phase 1: Owner-Tor - Reindex-Weg, Feldmodell, Sprachmarke
**Rationale:** `test_upgrade_compatibility.py` verbietet ausdruecklich, den bestehenden Test gruen zu "reparieren"; ein roter Test hier ist laut Kommentar im Code "keine Reparatur, sondern eine Frage an den Owner". Ohne diese Entscheidung darf kein Code geschrieben werden, der D-04 (Index-Kompatibilitaet ueber Minor-Spruenge) verletzt.
**Delivers:** schriftlicher Entscheid zu: Umbauweg (Re-Analyse empfohlen), Feldmodell A/B/C (A empfohlen), ob `FINDLING_LANGUAGES` Deutsch/Englisch abschalten darf, ob Sprachmenge sechster Versionsmerker wird, Katalogprozess (maschinell + Community-Review, kein Muttersprachler-Pflichtgate).
**Addresses:** Grundsatzfragen aus FEATURES.md Teil 2, ARCHITECTURE.md Teil C.
**Avoids:** Pitfall "Schema erhoehen und den Rebuild spaeter bauen" (Nie-Fall der Technical-Debt-Tabelle).

### Phase 2: Analyseketten und Sprachtabelle
**Rationale:** Muss vor dem Schema stehen, weil `ANALYZER_VERSION` und die Feldliste von den fertigen Ketten abhaengen; darf aber die Query-Seite noch nicht oeffnen.
**Delivers:** vier Analyseketten es/it/nl/pt, **die Kettenreihenfolge messend entschieden** (siehe offener Entscheid oben, zusammengefuehrte Testfaelle aus allen drei Recherchedokumenten als Abnahmekriterium), geschlossene Sprachnamen-Positivliste gegen den Rust-Panic, Owner-Entscheid zu niederlaendischen Komposita schriftlich festgehalten.
**Uses:** tantivy 0.26.2, Snowball-Stemmer/-Stoppwoerter, ggf. gefaltete Ergaenzungsliste.
**Implements:** `index/analyzer.py`-Erweiterung.

### Phase 3: Schema, Marken und Umbauweg
**Rationale:** Die riskanteste und architektonisch wichtigste Phase. Muss den vollstaendigen Re-Analyse-Umbau liefern, bevor irgendein Query-Code die neuen Felder anspricht.
**Delivers:** Schema waechst auf 13 Felder (immer vollstaendig gebaut), `SCHEMA_VERSION`-Sprung, neues Modul `index/rebuild.py` (Durchlauf aus altem Index, Platzpruefung, Wiederaufnahmefaehigkeit, Rueckfall auf Vollreindex), `languages` als sechster Versionsmerker, PHP-Migration `Version001300Date...` (Lockstep-Muster, nicht der Ort des eigentlichen Umbaus).
**Addresses:** Pitfalls 1, 2, 6, 7.
**Avoids:** stille Datenverlust-/Totalausfall-Pfade.

### Phase 4: Frageseite aufdrehen
**Rationale:** Erst nachdem Phase 3 bewiesen ist, duerfen `DEFAULT_FIELDS`/`FIELD_BOOSTS` von Konstanten zu einer vom `schema_version`-Merker abhaengigen Funktion werden - das ist die Sicherheitsbedingung, kein Optimierungsdetail.
**Delivers:** schema-abhaengige Feldliste, Feld-Boosts fuer die vier neuen Felder (unter `body_en`).
**Implements:** `query/rewrite.py`-Umbau.

### Phase 5a: Beweisstrecke drehen (CI) / Phase 5b: UI-Kataloge es/it/nl/pt (parallel)
**Rationale:** Beide haengen an nichts aus dem Indexstrang und koennen parallel zu Phase 1-4 laufen, wenn der Indexstrang am Owner-Tor wartet - der einzige echte Parallelpfad des Milestones.
**Delivers (5a):** zweiter, umgedrehter Pruefschritt in `deploy-harp.yml` neben dem bestehenden (nicht als Ersatz), `UPGRADE_FROM_TAG` auf `v1.2.0`. **Delivers (5b):** zehn neue Katalogdateien (es, it, nl, pt_PT, pt_BR mal json/js), 199-Schluessel-Gate generalisiert, Pluralregeln aus den Nextcloud-Kerndateien gelesen.
**Addresses:** Pitfall 3, Katalogfallen.

### Phase 6: Messanfahrt BL-F03
**Rationale:** Alle synthetischen Zahlen (Indexgroesse, Umbaudauer) sind ausdruecklich als Schaetzung markiert und gehoeren auf den echten Korpus-Snapshot, bevor der Owner final freigibt.
**Delivers:** echte Indexgroesse mit sechs befuellten Feldern, echte Umbaudauer ueber 52.137 Dokumente, beide Zahlen in `docs/performance.md`.

### Phase 7: Haertung und Store-Einreichung 1.3.0
**Rationale:** Standardabschluss nach dem Muster vorheriger Milestones.
**Delivers:** Fremdinstallations- und Upgrade-Strecke gruen, Store-Text (Faktenliste, Owner-Abnahme), `min-version`/`max-version` geprueft.

### Optionale Phase (nach Bestaetigung): Niederlaendische Komposita-Zerlegung
Eigenes Tor, eigener Umfang (zweite Wortlistenquelle, zweiter ca. 23-MB-Automat, eigene Digest-Marke, eigene Rezeptmessung) - faellt bei Terminnot als Ganzes, nicht halb.

### Phase Ordering Rationale

- Die Reihenfolge Phase 2 -> 3 -> 4 ist eine Sicherheitsbedingung, keine Aufwandsgruppierung: zwischen "Schema erweitert" und "Umbau fertig" liegt auf jeder Bestandsinstallation ein Zeitfenster, in dem eine geoeffnete Query-Feldliste zum Totalausfall fuehrt.
- Phase 1 (Owner-Tor) steht bewusst vor jeder Codearbeit, weil mehrere nachgelagerte Entscheidungen (Feldmodell, Umbauweg, Sprachmarke) sonst implizit durch die erste geschriebene Zeile getroffen wuerden.
- Phase 5a/5b sind der einzige Parallelpfad und sollten im Plan als solcher markiert werden, damit Wartezeit am Owner-Tor nicht zu Leerlauf wird.
- Die niederlaendische Komposita-Zerlegung ist bewusst aus dem Kernpfad herausgeschnitten, weil sie laut FEATURES.md etwa so gross ist wie der Rest des Milestones zusammen.

### Research Flags

Phasen, die vermutlich `/gsd:plan-phase --research-phase <N>` brauchen:
- **Phase 2 (Analyseketten):** die Kettenreihenfolge ist zwischen den vier Rechercheuren uneinheitlich (siehe offener Entscheid); die Phase selbst muss die messende Abnahme liefern, bevor sie als "Standardmuster" gelten kann.
- **Phase 3 (Schema/Umbauweg):** neue Architekturkomponente ohne Vorbild im Repo (`index/rebuild.py`); Wiederaufnahmefaehigkeit und Platzpruefung unter Abbruchbedingungen sind nicht triviale Fragen.
- **Niederlaendische Komposita (optionale Phase):** eigene Rezeptmessung wie beim deutschen Kompositasplitter noetig, RAM-Kosten und Lizenzlage muessen vor dem Bau geklaert sein.

Phasen mit etabliertem Muster (Research-Phase vermutlich verzichtbar):
- **Phase 4 (Frageseite):** reiner Umbau einer Konstante zu einer merker-abhaengigen Funktion, Muster bereits im Code vorgezeichnet.
- **Phase 5a (CI-Beweisstrecke):** Struktur des bestehenden `deploy-harp.yml`-Schritts ist das Vorbild, nur die Behauptungsrichtung dreht sich.
- **Phase 5b (Kataloge):** das FR-Katalogmuster (`docs/l10n-french.md`, vier bestehende Gates) ist direkt uebertragbar.
- **Phase 6 (Messanfahrt):** BL-F03 ist ein bestehendes, dokumentiertes Messverfahren.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Gegen die installierte `tantivy`-Bibliothek selbst gemessen (Sprachmatrix, Panic vs. ValueError, Index-Format), PyPI-Metadaten fuer alle geprueften Alternativen abgefragt. MEDIUM nur fuer Uebersetzungswerkzeuge (kein Laufzeitpfad, geringes Risiko). |
| Features | HIGH fuer eigene Messungen und Quellcode, MEDIUM fuer Nutzererwartung aus Fremdprodukten (Paperless-ngx, Elastic, Meilisearch - aus Doku/Foren abgeleitet, nicht erhoben). |
| Architecture | HIGH fuer alle Integrationspunkte (Datei und Zeile benannt) und die drei kritischen Verhaltensmessungen. MEDIUM fuer zwei Punkte: Nextcloud-Sprachcodes fuer Portugiesisch und die tatsaechliche Umbaudauer auf der Zielhardware (beide als VERIFIZIEREN markiert, gehoeren in Phase 6/BL-F03). |
| Pitfalls | HIGH fuer alles "gemessen" (gegen `tantivy 0.26.0` und den Quelltext dieses Repos), MEDIUM fuer die Nextcloud-Katalogpunkte (aus `nextcloud/server` master gelesen, nicht gegen laufende Instanz geprueft). |

**Overall confidence:** HIGH fuer die technische Machbarkeit und die Risikolage, MEDIUM fuer einzelne Detailentscheidungen, die absichtlich als offene Punkte an die Planung bzw. den Owner weitergereicht werden (siehe unten).

### Gaps to Address

- **Die Position von `ascii_fold` relativ zum Stemmer ist zwischen den Recherchen uneinheitlich** (siehe eigener Abschnitt oben) - muss in Phase 2 durch eine zusammengefuehrte Testtabelle messend entschieden werden, nicht durch Auswahl einer Quelle.
- **`pt` vs. `pt_BR`/`pt_PT` fuer den Dateiladepfad der App-Kataloge** ist MEDIUM-Konfidenz (aus dem Quellbaum gelesen) - vor der Uebersetzungsarbeit an einer Test-Nextcloud mit `ls core/l10n/` verifizieren.
- **Absolute Indexgroesse und Umbaudauer bei sechs befuellten Feldern** sind nur an synthetischem/Belletristik-Korpus gemessen (relative Faktoren HIGH, absolute Megabyte/Stunden MEDIUM) - gehoeren in die Messphase BL-F03 am echten Korpus-Snapshot.
- **Ob `FINDLING_LANGUAGES` Deutsch/Englisch abschalten darf** ist ein Produktentscheid, kein technischer - gehoert ins Owner-Tor (Phase 1).
- **Niederlaendische Komposita-Zerlegung** ist bewusst ausgeklammert und braucht eine eigene Go/No-Go-Entscheidung, sonst wird die bewusste Nicht-Entscheidung spaeter als Versehen gelesen.
- **Estnischer Stemmer nicht verfuegbar** - muss in der Kommunikation mit der Buerokratt/OS2ai-Outreach-Spur beruecksichtigt werden (Fakt steht, nur die Kommunikation ist offen).

## Sources

### Primary (HIGH confidence)
- `quickwit-oss/tantivy-py` und `quickwit-oss/tantivy`, Tag 0.26.2: `src/tokenizer.rs`, `src/tokenizer/stop_word_filter/stopwords.rs`, `CHANGELOG.md` - Sprachmatrix, Stoppwortzahlen, Lizenztext, Bugfixes
- Eigene Ausfuehrung gegen `tantivy==0.26.0` (Backend-venv) und `tantivy==0.26.2` (Wegwerf-Umgebung), 23.09.2026 - Filterreihenfolge, Panic vs. ValueError, Index-Format, Schema-Mismatch-Verhalten, Re-Analyse-Machbarkeit
- Repo selbst: `backend/src/findling/config.py`, `index/*.py`, `query/rewrite.py`, `api/*.py`, `store/repo.py`, `worker/poller.py`, `php/lib/Migration/Version001200Date20260921000000.php`, diverse `backend/tests/*.py`, `.github/workflows/deploy-harp.yml`, `backend/appinfo/info.xml`
- `docs/performance.md`, `docs/l10n-french.md`, `.planning/BACKLOG.md` (BL-F02/BL-F03)
- Nextcloud Developer Manual (Translations, `translationtool.phar`)
- Debian trixie Paketmetadaten (`wdutch`, `dutch` 1:2.20.19+1-3, Lizenz)

### Secondary (MEDIUM confidence)
- `nextcloud/server` master, `core/l10n/` - Sprachcodes und Pluralregeln, aus dem Quellbaum gelesen, nicht gegen laufende Instanz geprueft
- Paperless-ngx-Doku und Diskussion #8293 - Vergleichsprodukt, eine Stemmer-Sprache pro Index
- Elastic-Blog und Meilisearch-Doku zu Multi-Language-Strategien - Per-Field-Muster, ausdruecklich Warnung vor Anfrage-Spracherkennung

### Tertiary (LOW confidence)
- Solr Reference Guide / Lucene-SnowballFilter-Doku - als Gegenbeispiel fuer die verbreitete, aber fuer romanische Snowball-Algorithmen widerlegte Regel "Normalisierung vor Stemming"

---
*Research completed: 2026-09-23*
*Ready for roadmap: yes, mit einem offenen messenden Entscheid (ascii_fold-Position) als erster Arbeitsschritt in Phase 2*
