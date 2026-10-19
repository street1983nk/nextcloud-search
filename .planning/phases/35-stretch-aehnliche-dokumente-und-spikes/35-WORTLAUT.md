# Phase 35: Wortlaut-Entwurf (de, en, fr)

Stand: 19.10.2026, Entwurf aus Plan 35-01 Task 1 auf Basis von Commit 5a66ba1e.
Status: **vom Owner abgenommen am 19.10.2026**, alle Empfehlungen übernommen (Abschnitt E).

Grundlage: 35-CONTEXT.md (D-35-01 sichtbarer Textlink je Treffer, D-35-02 Ansicht per GET-Parameter
`similar`, D-35-03 höchstens zehn Nachbarn als normale Trefferliste, D-35-04 Kopf "Ähnlich zu: ..." mit
Rückweg, D-35-08 Wortlaut vor Code und Katalogen), Planer-Entscheidungen PE-35-1 (keine Filter- und
Sortierzeile, kein Blättern, keine zweite Ebene), PE-35-2 (Link an jedem Treffer), PE-35-3 (zwei
Leerzustände ohne Zahl), 35-RESEARCH.md Pitfalls 4, 8 und 9, Open Questions 3 und 4.

Regeln für alle Zeilen:

- Französisch nach `docs/l10n-french.md`: ASCII-Apostroph, einfaches Leerzeichen vor `:`, `;`, `?`, `!`,
  kein geschütztes Leerzeichen.
- Deutsch in der Sie-Form wie der Katalogbestand ("Durchsuchen Sie den Inhalt Ihrer Dateien").
- Keine Zahl über Dateien, die der Nutzer nicht lesen darf: kein "3 von 10", kein "weitere ausgeblendet",
  keine Gesamtzahl der Nachbarn (Pitfall 8, T-35-01).
- Kein Wort über Rechte anderer und keine Unterscheidung zwischen unbekannter, fremder, gelöschter und
  nicht lesbarer Ausgangsdatei: ein einziger Satz für alle Fehlschläge (PE-35-3 (b)).
- Platzhalter wie im Bestand: `%s` bei einem Wert, `%1$s`/`%2$s` bei mehreren; der Platzhalter trägt
  ausschließlich den Titel einer Datei, die die Endfilterung (`SearchService::readableFile`) bereits
  freigegeben hat.
- Englische Quellschlüssel stehen so in der Tabelle, wie sie in `$l->t()` stehen werden.

## (A) Schlüsseltabelle

Neue Schlüssel (sechs Sätze plus eine Erklärzeile, damit sieben neue Schlüssel; Katalog-Schlüsselzahl 341
auf 348, sofern O4 und O6 wie empfohlen beantwortet werden):

| Schlüssel (en) | de | fr | Platzhalter | Ort |
|---|---|---|---|---|
| Similar documents | Ähnliche Dokumente | Documents similaires | keine | Ergebnisseite, Hit-Block (`search.php` um Zeile 482): sichtbarer Textlink je Treffer als eigenes `<a>` neben dem Zeilen-Link (D-35-01). Zusätzlich wiederverwendet als `aria-label` der Liste in der Ähnlich-Ansicht und als h1 im Zustand "Datei nicht verfügbar" (siehe B) |
| Similar documents to %s | Ähnliche Dokumente zu %s | Documents similaires à %s | `%s` = Titel des Treffers | Ergebnisseite, `aria-label` des Textlinks je Treffer (Pitfall 9: 25 gleichlautende Links sind in der Linkliste eines Screenreaders sonst ununterscheidbar); Muster wie `'%1$s in %2$s'` in `search.php:457` |
| Similar to: %s | Ähnlich zu: %s | Similaire à : %s | `%s` = Titel der Ausgangsdatei | Ähnlich-Ansicht, h1 (Block 1, `search.php:204-210`, neuer dritter Zweig), nur wenn die Ausgangsdatei lesbar ist |
| Back to the results | Zurück zu den Treffern | Retour aux résultats | keine | Ähnlich-Ansicht, Rückweg-Link direkt unter dem h1, in jedem Zustand der Ansicht (Treffer, beide Leerzustände, Banner); Ziel ist die Ergebnisseite mit dem mitgegebenen Suchbegriff und den Filtern (D-35-04); Form wie der Reset-Link `search.php:400-401` |
| No similar documents found | Keine ähnlichen Dokumente gefunden | Aucun document similaire trouvé | keine | Ähnlich-Ansicht, Leerzustand (a) ohne Nachbarn, h2 im Block `findling-empty` (`search.php:487-548`, neuer Zweig) |
| None of your other files is close enough in content. Files that have not yet been prepared for the semantic search, or that contain no text, have no similar documents. | Keine Ihrer anderen Dateien ist inhaltlich nah genug. Dateien, die noch nicht für die semantische Suche erfasst sind oder keinen Text enthalten, haben keine ähnlichen Dokumente. | Aucun de vos autres fichiers n'est assez proche par son contenu. Les fichiers qui ne sont pas encore pris en compte par la recherche sémantique ou qui ne contiennent pas de texte n'ont pas de documents similaires. | keine | Ähnlich-Ansicht, Leerzustand (a), Erklärsatz unter der h2 (PE-35-3 (a), Open Question 3) |
| This file is not available | Diese Datei ist nicht verfügbar | Ce fichier n'est pas disponible | keine | Ähnlich-Ansicht, Leerzustand (b), h2 im Block `findling-empty`; ein Zustand für unbekannte, fremde, gelöschte und nicht lesbare Ausgangsdatei und für einen ungültigen Wert von `similar` (PE-35-3 (b)) |
| Seitentitel des Browser-Tabs | entfällt | entfällt | , | Die Ergebnisseite setzt heute keinen Titel je Zustand (geprüft: kein `setPageTitle`, kein `pageTitle`, kein `document.title` in `php/`); der Tab trägt den Standardtitel von Nextcloud, die Ähnlich-Ansicht ebenso |

Bestand, wiederverwendet (kein neuer Schlüssel):

| Schlüssel (en) | de | fr | Ort in der Ähnlich-Ansicht |
|---|---|---|---|
| Similar documents (Bestand nach diesem Plan, siehe oben) | Ähnliche Dokumente | Documents similaires | `aria-label` der Liste `ol.findling-hits` statt "Search results"; h1 im Zustand (b) |
| %1$s in %2$s (Bestand, wiederverwendet) | %1$s in %2$s | %1$s dans %2$s | `aria-label` des Zeilen-Links je Nachbar |
| last opened (Bestand, wiederverwendet) | wie Bestand | wie Bestand | versteckter Satz je Nachbar, wie auf der Ergebnisseite |
| The search is not answering right now (Bestand, wiederverwendet) | Die Suche antwortet gerade nicht | La recherche ne répond pas pour le moment | Banner bei Backend-Ausfall (Block 2) |
| Findling could not reach its backend. Your files are unchanged. Try again in a moment, and tell your administrator if it stays that way. (Bestand, wiederverwendet) | wie Bestand | wie Bestand | Banner bei Backend-Ausfall |
| Try again (Bestand, wiederverwendet) | Erneut versuchen | Réessayer | Banner bei Backend-Ausfall; Ziel ist dieselbe Ähnlich-Adresse |
| Findling is not ready to search (Bestand, wiederverwendet) | Findling ist nicht suchbereit | Findling n'est pas prêt à rechercher | Banner bei Versionsdrift oder fehlendem Home-Ordner |
| The two halves of Findling report different versions. Your administrator has to update both together. (Bestand, wiederverwendet) | wie Bestand | wie Bestand | Banner bei Versionsdrift |

Nicht wiederverwendet, weil der Wortlaut nicht passt: "More results exist. Narrow the search to see them."
(die Ansicht hat keinen Suchbegriff zum Eingrenzen und keine Obergrenze außer zehn), "The index is still
being built, so results can be missing." (wäre in der Ansicht wahr, nennt aber "Treffer" zu einer Anfrage,
die der Nutzer nicht gestellt hat; Entscheid in O4), "Other files contain this word, but none that you may
open." (Wort über Rechte, in der Ähnlich-Ansicht ausgeschlossen).

Hinweise zur Tabelle:

- Der Erklärsatz von (a) ist in beiden Fällen wahr, die in denselben Leerzustand fallen: es gibt keine
  lesbaren Nachbarn unter der Schwelle, oder die Ausgangsdatei hat keine Vektoren. Er sagt "Ihrer anderen
  Dateien", also nichts über Dateien, die der Nutzer nicht lesen darf; fallen Nachbarn erst bei der
  Endfilterung weg, bleibt der Satz wahr, weil sie keine Dateien des Nutzers sind.
- Echte Kopien der Ausgangsdatei (gleicher Inhalt, andere Datei) erscheinen als Nachbarn (Pitfall 4); dazu
  kein eigener Satz, siehe O3.
- Das h1 "Ähnlich zu: %s" trägt den Titel ohne Anführungszeichen, weil D-35-04 die Doppelpunktform festlegt;
  die Ergebnisseite setzt den Suchbegriff in Anführungszeichen ("Treffer für „%s“"), ein Dateititel ist
  aber kein getippter Begriff.

## (B) Seitenbild in Worten

### Ergebnisseite (bestehende Ansicht), je Treffer

Reihenfolge innerhalb von `li.findling-hit`: der bestehende Zeilen-Link (Icon, Titel, Pfad, ggf. Datum,
Auszug) bleibt unverändert ein `<a>`; direkt darunter, außerhalb dieses Links, als eigenes `<a>` der
Textlink (D-35-01). Zwei Tabstopps je Treffer statt einem. Der Link steht an jedem Treffer, auch bei reinen
Namenstreffern und Bildern (PE-35-2), weil die Seite nicht weiß, welche Datei Vektoren hat.

| Sprache | sichtbarer Text unter Pfad/Auszug | vorgelesener Name (Beispiel Titel "Mietvertrag.pdf") |
|---|---|---|
| de | Ähnliche Dokumente | Ähnliche Dokumente zu Mietvertrag.pdf |
| en | Similar documents | Similar documents to Mietvertrag.pdf |
| fr | Documents similaires | Documents similaires à Mietvertrag.pdf |

### Ähnlich-Ansicht, Ausgangsdatei lesbar, Nachbarn vorhanden

1. h1: "Ähnlich zu: Mietvertrag.pdf" / "Similar to: Mietvertrag.pdf" / "Similaire à : Mietvertrag.pdf".
2. Rückweg-Link: "Zurück zu den Treffern" / "Back to the results" / "Retour aux résultats".
3. Suchformular des Kopfes: bleibt sichtbar, vorbelegt mit dem mitgegebenen Suchbegriff, ohne Begriff
   leer (eine neue Suche verlässt die Ansicht); keine eigene Beschriftung.
4. Kein Banner, solange das Backend antwortet.
5. Keine Filter- und Sortierzeile (PE-35-1).
6. Liste `ol.findling-hits` mit `aria-label` "Ähnliche Dokumente" / "Similar documents" /
   "Documents similaires": höchstens zehn Einträge, je Icon, Titel, Pfad, ohne Auszug (es gibt keinen
   Suchbegriff, der markiert werden könnte), ohne Datumszeile, ohne Ähnlich-Link (eine Ebene, PE-35-1),
   ohne Markierung und ohne Zahl (D-35-03).
7. Kein Pager.

### Ähnlich-Ansicht, Ausgangsdatei lesbar, keine Nachbarn (Leerzustand a)

1. h1 wie oben, Rückweg-Link wie oben.
2. Block `findling-empty`: h2 "Keine ähnlichen Dokumente gefunden" / "No similar documents found" /
   "Aucun document similaire trouvé", darunter der Erklärsatz aus Tabelle A.

### Ähnlich-Ansicht, Ausgangsdatei nicht verfügbar (Leerzustand b)

1. h1 "Ähnliche Dokumente" / "Similar documents" / "Documents similaires" (der Titel der Datei ist hier
   unbekannt oder darf nicht erscheinen; die Seite behält genau ein h1).
2. Rückweg-Link wie oben.
3. Block `findling-empty`: h2 "Diese Datei ist nicht verfügbar" / "This file is not available" /
   "Ce fichier n'est pas disponible", kein weiterer Satz.

### Ähnlich-Ansicht bei Backend-Ausfall

h1 wie im jeweiligen Zustand (bei unbekanntem Zustand der Ausgangsdatei die Form aus b), Rückweg-Link,
darunter der bestehende Fehler-Banner; kein Leerzustand neben dem Banner (dieselbe Entscheidung wie
`$showEmpty`, Pitfall 8).

## (C) Fragen an den Owner

**O1: Link an allen Treffern**
- (a) an jedem Treffer der Ergebnisseite, auch an reinen Namenstreffern und Bildern; der Leerzustand (a)
  trägt, wenn eine Datei keine Vektoren hat.
- (b) nur an Treffern mit Inhaltstreffer; die Seite bräuchte dafür ein neues Feld je Kandidat.
- Empfehlung: (a) wie PE-35-2; kein Vorwissen über Vektoren auf der Seite, keine neue Feldart.

**O2: Filter- und Sortierzeile in der Ansicht**
- (a) weg, ebenso Pager und ein zweiter Ähnlich-Link je Nachbar.
- (b) Filterzeile wie auf der Ergebnisseite.
- Empfehlung: (a) wie PE-35-1; höchstens zehn Nachbarn brauchen keine Eingrenzung, und mit einer Ebene
  bleibt der Rückweg eindeutig.

**O3: Echte Kopien als Nachbarn**
- (a) Kopien bleiben in der Liste, ohne eigenen Satz und ohne Markierung.
- (b) Kopien (gleicher Inhalt) ausblenden oder kennzeichnen.
- Empfehlung: (a); es sind andere Dateien des Nutzers, und eine Kennzeichnung bräuchte einen neuen Satz und
  eine Inhaltsgleichheitsprüfung, die zu STR-02 (Dedup-Notiz) gehört.

**O4: Ein oder zwei Leerzustände**
- (a) zwei: "Keine ähnlichen Dokumente gefunden" mit Erklärsatz, und "Diese Datei ist nicht verfügbar" als
  ein Zustand für alle Fehlschläge der Ausgangsdatei; der Bestandssatz "The index is still being built"
  erscheint in der Ansicht nicht.
- (b) ein einziger Zustand "Keine ähnlichen Dokumente gefunden" auch für eine nicht verfügbare Datei.
- (c) wie (a), aber ohne Erklärsatz unter "Keine ähnlichen Dokumente gefunden" (ein Schlüssel weniger).
- Empfehlung: (a) wie PE-35-3; (b) behauptet bei einer gelöschten Datei etwas Falsches, und der Erklärsatz
  nennt dem Nutzer den Grund, warum ein Bild oder ein frisch hochgeladenes Dokument keine Nachbarn hat.

**O5: Wortwahl des aria-Labels**
- (a) "Similar documents to %s" / "Ähnliche Dokumente zu %s" / "Documents similaires à %s" mit dem Titel.
- (b) "Similar documents to %1$s in %2$s" mit Titel und Pfad, wie das Label des Zeilen-Links.
- Empfehlung: (a); der Titel unterscheidet die Links in der Linkliste, der Pfad steht schon im Label des
  Zeilen-Links direkt davor, und ein kurzes Label ist schneller vorgelesen. Der Name enthält den sichtbaren
  Text am Anfang (WCAG 2.5.3).

**O6: Form des Rückwegs**
- (a) Link-Satz "Zurück zu den Treffern" / "Back to the results" / "Retour aux résultats", gestaltet wie der
  Reset-Link.
- (b) nur das Wort "Zurück" / "Back" / "Retour".
- (c) "Zurück zur Suche" / "Back to the search" / "Retour à la recherche", weil die Ansicht auch ohne
  Suchbegriff erreichbar ist (zum Beispiel über eine gespeicherte Adresse).
- Empfehlung: (a); der Satz sagt, wohin der Link führt, "Zurück" allein ist in der Linkliste ohne Ziel.
  Ohne mitgegebenen Suchbegriff führt der Link auf die leere Suchseite, und "Treffer" bleibt vertretbar,
  weil die Ansicht nur über einen Treffer verlinkt wird; wer (c) vorzieht, bekommt denselben Platz.

## (D) Vorab-Prüfung

Die Entwurfstexte aus A und B (alle de-, en- und fr-Zellen der Tabelle A und die Sätze aus B, ohne
Abschnitt C) lagen am 19.10.2026 als Scratch-Datei (21 Zeilen: sieben Schlüssel in drei Sprachen) vor und
wurden per `grep` geprüft, jede Prüfung mit einer Positivkontrolle auf einer eigens gebauten Trefferzeile:

- gesperrter Wortstamm aus `backend/tests/test_public_artifacts.py` (`BLOCKED_TERM`, Prüfung ohne Rücksicht
  auf Groß- und Kleinschreibung, auf der Scratch-Datei und auf den Abschnitten A und B dieser Datei): kein
  Fund (0 und 0); Positivkontrolle schlägt an (1).
- Ziffern `[0-9]` in den Zustandssätzen (h1, Rückweg, beide Leerzustände, Erklärsatz, Linktext,
  aria-Label; de/en/fr): kein Fund (0); Positivkontrolle 1. Zahlwörter de/en/fr von eins bis zwölf, hundert
  und die Artikel-Zahlwörter (`eins?`, `eine[mnrs]?`, `une?`, `one`) als ganze Wörter: kein Fund;
  Positivkontrolle auf "drei von zehn", "un fichier", "one file" schlägt dreimal an.
- Wörter `Recht|Berechtig|permission|droit` in den Zustandssätzen: kein Fund (0); Positivkontrolle auf
  "kein Leserecht" 1.
- Halbgeviert- und Geviertstriche (U+2013, U+2014) in der ganzen Datei: kein Fund (0); Positivkontrolle 1.

## (E) Owner-Abnahme

Owner-Abnahme: 19.10.2026, "Abgenommen (alle Empfehlungen)", alle Sätze wie vorgelegt, O1-O6 je Option a

Owner-Wort wörtlich: "Abgenommen" (19.10.2026, übermittelt über den Orchestrator von `/gsd:execute-phase`):
alle sieben Sätze aus Tabelle A wie vorgelegt, alle Fragen O1 bis O6 je Empfehlung (a). Tabelle A und
Abschnitt B gelten damit unverändert als **abgenommen**. Der vom Orchestrator vorgegebene Zeilentext enthielt
einen Geviertstrich; er steht hier mit Komma, weil die Datei nach Projektregel und Plan-Prüfung keine
Halbgeviert- oder Geviertstriche tragen darf.

### Folgen für 35-06 und 35-07

- O1 (a): der Textlink "Similar documents" mit `aria-label` "Similar documents to %s" steht an jedem
  Treffer der Ergebnisseite, auch an Namenstreffern und Bildern; 35-06 liefert dafür kein Feld über Vektoren,
  35-07 rendert den Link ohne Bedingung als eigenes `<a>` unter dem Zeilen-Link.
- O2 (a): die Ähnlich-Ansicht hat keine Filter- und Sortierzeile, keinen Pager und keinen Ähnlich-Link je
  Nachbar; 35-06 setzt die Filter-, Sortier- und Pager-Werte der Ansicht leer, 35-07 verzweigt Block 2b,
  Block 5 und den Ähnlich-Link auf die Ansicht.
- O3 (a): echte Kopien bleiben als Nachbarn, ohne Markierung und ohne eigenen Satz; keine
  Inhaltsgleichheitsprüfung in 35-06.
- O4 (a): zwei Leerzustände: "No similar documents found" mit dem Erklärsatz aus Tabelle A, und "This file
  is not available" als ein Zustand für unbekannte, fremde, gelöschte, nicht lesbare Ausgangsdatei und einen
  ungültigen Wert von `similar`; 35-06 liefert genau diese zwei Zustände an das Template, ohne Zahl;
  im Zustand "nicht verfügbar" ist das h1 "Similar documents"; "The index is still being built" erscheint
  in der Ansicht nicht; Backend-Ausfall nutzt die Bestandsbanner, kein Leerzustand daneben.
- O5 (a): `aria-label` des Textlinks nur mit dem Titel, Schlüssel "Similar documents to %s".
- O6 (a): Rückweg als Link-Satz "Back to the results", gestaltet wie der Reset-Link, in jedem Zustand der
  Ansicht direkt unter dem h1; Ziel ist die Ergebnisseite mit mitgegebenem Suchbegriff und Filtern, ohne
  Begriff die leere Suchseite.
- 35-07 verwendet die sieben englischen Schlüssel aus Tabelle A zeichengleich im Template; 35-13 übernimmt
  de und fr zeichengleich in die 16 Kataloge und fünf Sprachtabellen, Schlüsselzahl 341 auf 348.
