# Backlog

Entschiedene Vorhaben, die noch keiner Phase zugeordnet sind. Vor der Planung einer
neuen Phase mit `/gsd:review-backlog` durchgehen.

Phasen-Befunde gehören NICHT hierher, sondern in die `deferred-items.md` der
jeweiligen Phase. Hier steht, was nach dem Release ansteht.

## BL-F01: Synergie-Banner mit dem MCP Connector, prominent auf beiden Seiten

**Auslöser:** Findling ist als 1.0.0 im App Store. Nicht vorher.

Wichtig zum Zeitpunkt: es gibt kein eigenes v1.0. Nach D-08 und D-11 erscheint ein
Store-Erstrelease 1.0.0 mit Volltext, OCR und semantischer Suche. Genau das ist der
richtige Moment für dieses Banner, denn die semantische Hälfte macht die Aussage
erst vollständig wahr. Vor Phase 6 wäre die Aussage die schwächere über einen
lexikalischen Index mit OCR.

**Gegenstück:** BL-01 im Repo des Connectors
(`nextcloud-mcp-connector/.planning/BACKLOG.md`). Dort steht der Wortlaut ausführlich
begründet; dieser Eintrag ist die Findling-Seite derselben Sache.

**STAND 21.09.2026: ERLEDIGT, und die Zusage hat seit Plan 16-12 ein Gate.**
Der eine Schluss-Satz, der am 07.09.2026 noch offen war, steht seit Commit
`1c737e6` ("feat: the retrieval layer sentence on both store pages, 1.0.3") in
den Store-Texten beider Hälften, dreisprachig, also an sechs Stellen; dazu die
drei Fassungen in `docs/store-listing.md`, zusammen neun. Ausgeliefert ist er
mit Release 1.0.3, und im Tag `v1.1.0` war er dabei (`git show
v1.1.0:php/appinfo/info.xml` führt ihn). Wer hier ansetzt, arbeitet an einer
Aufgabe, die seit 1.0.3 fertig ist.

Was bis zum 21.09.2026 gefehlt hat, war nicht der Satz, sondern seine
Prüfung: `test_store_metadata.py` hielt den Datenschutzabsatz aus D-12 fest und
den Querverweis nicht, also hätte eine Textpflege ihn stumm entfernen können.
Plan 16-12 baut das Gate. Es prüft die ANZAHL und nicht die Anwesenheit, weil
die Regeltabelle in `docs/store-listing.md` genau EINEN Querverweis erlaubt und
ein zweiter Satz die Regel ebenso verletzt wie ein fehlender; Selbsttests für
null und für zwei stehen daneben. Requirement HART-02 ist damit materiell und
maschinell erfüllt.

**STAND 07.09.2026 (überholt am 21.09.2026, siehe oben):** Alle drei Blocker
sind gefallen (BL-02 gemergt und in CI gemessen, BL-15 im Connector-PR #3, D-12
damit erfuellt). Die README-Haelfte ist umgesetzt (Branch
feat/bl-f01-connector-banner, Banner in allen drei READMEs mit Link auf den
Fidelity-Test). OFFEN NUR NOCH: der eine Schluss-Satz in den Store-Texten
beider Haelften, der faehrt mit dem naechsten regulaeren Release mit
(Store-Text reist mit dem Release; kein Release nur fuer einen Satz).

**Blockiert durch drei Dinge:**

1. **D-12 dieser Phase:** Die Synergie darf im Store-Text nicht behauptet werden,
   bevor der Content-Hit-Fidelity-Test bestanden ist. Laut Synergie-Entscheid vom
   15.08. gilt das auch für READMEs und Pitches.
2. **BL-02 des Connectors:** genau dieser Test. Alice findet einen Marker, der nur im
   INHALT steht, Bob findet ihn nicht, und der Treffer ist nachweislich ein
   Inhalts- und kein Namenstreffer. Erst danach ist die Aussage eine gemessene
   Tatsache.
3. **BL-15 des Connectors:** Der Connector schickt heute in jeder
   `unified_search`-Antwort mit, dass Inhalte nicht indexiert seien. Solange das so
   ist, widerspricht ein Banner der eigenen Werkzeugausgabe an der einzigen Stelle,
   die eine Maschine liest.

**Was zu tun ist:** Owner-Vorgabe vom 04.09.2026, "prominent auf beide Seiten". Ein
Banner weit oben in `README.md`, dazu die Doku-Seiten, gespiegelt vom Connector.

Der Wortlaut ist hier festgehalten und nicht dem Tag überlassen: Es heißt
**Retrieval-Schicht für ein eigenes RAG**, und ausdrücklich NICHT "das ist ein
RAG-System". RAG hat drei Teile, und die Generation liefert keines der beiden
Produkte; das Modell ist immer der Client. Wer "RAG-System" liest, erwartet ein
fertiges Ding mit Chat-Oberfläche und mitgeliefertem Modell, und diese Lücke
zwischen Erwartung und Lieferung landet in den Store-Bewertungen. Fünf ehrliche
Bewertungen in 90 Tagen sind der stärkste Ranking-Hebel, den es gibt.

Vorn steht deshalb die Eigenschaft, die fertige RAG-Produkte fast immer falsch
machen: **die Rechtetreue je Nutzer**. Die übliche Bauform indexiert alles unter
einem Dienstkonto in einen Vektorspeicher und leckt quer über Nutzer hinweg. Hier
tragen der ACL-Vorfilter und der finale PHP-Recheck, hinter der Impersonation des
Connectors. Der Assistent sieht genau das, was dieser Nutzer sehen darf, und keinen
Satz mehr. Das ist selten, es ist messbar, und es ist die erste Frage eines
Datenschutzbeauftragten.

Entwurf für die deutsche Fassung:

    Findling + Nextcloud MCP Connector = die Retrieval-Schicht für dein eigenes RAG.
    Findling macht den Inhalt deiner Dokumente durchsuchbar, Scans eingeschlossen,
    und 1.0.0 ergänzt die semantische Suche. Der Connector reicht diese Treffer an
    jeden MCP-Client weiter, mit exakt den Rechten des anfragenden Nutzers. Das
    Modell bringst du mit, und kein Inhalt verlässt deinen Server.

**Zielgruppen bewusst getrennt:** Das Akronym gehört ins README und in die
Doku-Seiten, wo Entwickler lesen und danach suchen. Die Store-Texte behalten ihre
einfache Sprache ("Search the inside of your documents") und bekommen höchstens
einen Schlusssatz; sie liegen in `docs/store-listing.md` und in beiden `info.xml`,
dreisprachig nach D-12, und die Übersetzungen sind mitzuziehen. Ein
Nextcloud-Administrator im Mittelstand sucht nicht nach RAG, und Nextcloud
vermarktet mit Assistant und context_chat selbst etwas RAG-artiges. Ein frontaler
Vergleich mit einer First-Party-Funktion hilft uns nicht.

**Bewusst nicht:** kein direkter Draht vom Connector zum Findling-Index, also kein
eigenes MCP-Werkzeug gegen die Datenbank. Alles läuft über die Unified Search, damit
Nextcloud die einzige Berechtigungsgrenze bleibt. Das verlangen beide Threat-Models.

**Was der Store hergibt, am 04.09.2026 gegen das gepinnte Schema geprüft**
(APPSTORE_SHA `5c4373d7`, `nextcloudappstore/api/v1/release/info.xsd`):

- Es gibt **kein Feld** dafür. Das Schema kennt info, id, name, summary,
  description, version, licence, author, namespace, types, documentation, category,
  website, discussion, bugs, repository, screenshot, donation, dependencies und die
  technischen Registrierungen. Kein `related`, kein `works-with`, kein `recommend`,
  kein `suggest`. Es wird also Prosa in der `<description>`, es gibt kein
  Widget für verwandte Apps, und **auf der Seite der anderen App entsteht kein
  automatischer Rückverweis**. Beide Seiten tragen ihren eigenen Satz, genau
  deshalb gibt es BL-01 auf der Connector-Seite.
- Die `<description>` rendert Markdown, also Überschriften, Links und Listen. Der
  Store-Text des Connectors nutzt das schon und verlinkt aus einem Abschnitt
  "Weiterführendes" in allen drei Sprachen den n8n-Guide. Ein solcher Abschnitt ist
  der natürliche Ort für den Findling-Querverweis.
- Platz ist reichlich: die drei Beschreibungen des Connectors liegen bei etwa 4400
  (en), 4900 (de) und 5200 (fr) Zeichen. Unser Gate begrenzt `name` und `summary`
  auf 128 Zeichen und die Beschreibung überhaupt nicht. Verboten bleiben in jedem
  Fall Em-Dash, En-Dash und Emoji (Gate) sowie Backticks und Tabellen (Projektregel).

**Release-Reihenfolge, und das ist die Falle:** Der Store-Text kommt aus der
`info.xml` des hochgeladenen Releases. Er lässt sich nicht nachträglich bearbeiten,
er reist mit einer Version. Im Connector-Repo trägt der n8n-Store-Text genau diesen
Vermerk, "kommt mit 0.1.12".

Für uns heißt das: unser Banner kann nur mit 1.0.0 selbst in den Store, nicht später
nachgeschoben werden. Und der Connector braucht **ein Release nach unserem 1.0.0**,
nur um seinen Querverweis zu tragen. Da 0.1.12 nach dem ISV-Call am 14.09.2026
ausgeliefert werden soll, würde ein Verweis dort auf eine Store-Seite zeigen, die es
noch nicht gibt. Zwei Auswege, zu entscheiden wenn die Termine stehen: der Verweis
wartet auf 0.1.13, oder er zeigt auf das GitHub-Repository statt auf die
Store-Seite, was jederzeit gilt. Auf keinen Fall stillschweigend einen toten
Store-Link ausliefern.

**Warum überhaupt:** Jedes der beiden Produkte schließt die größte Lücke des
anderen. Findling ohne Client ist ein Suchfeld, der Connector ohne Findling erzählt
jedem Assistenten, dass Inhalte nicht indexiert sind. Zusammen sind sie die
Retrieval-Hälfte eines lokalen RAG, und zwar die Hälfte, die man schwer kaufen kann:
die rechtekorrekte.

## BL-F02: Sprachausbau Spanisch, Italienisch, Niederlaendisch, Portugiesisch

**Anlass:** Reddit-Rueckmeldungen nach dem Findling-Post (14./15.09.2026),
mehrere Nutzer wuenschen sich diese vier Sprachen. Ein Nutzer hat Hilfe
angeboten und wurde vom Owner auf direkten Kontakt verwiesen; wenn es so weit
ist, als Tester fuer echte Korpora in diesen Sprachen einplanen.

**STAND 21.09.2026: Baustein 1 ist geliefert und faehrt in v1.2.0 mit.**
Owner-Entscheid am Tor des Plans 16-10 (strukturierte Rueckfrage, Antwort im
Wortlaut "Mitfahren"). Das Abbild installiert seitdem `tesseract-ocr-spa`,
`-ita`, `-nld`, `-por`, `-dan` und `-est`, alle `1:4.1.0-2`, alle
`Architecture: all` aus `tesseract-lang`, jede mit einer eigenen
`--list-langs`-Pruefung beim Bau; `OCR_LANGUAGE_ALLOWLIST` hat neun Eintraege,
`OCR_DEFAULT_LANGUAGES` bleibt bei `deu+eng+fra`. Der Multi-Arch-Bau ist
gefahren und gruen (`docker.yml` Lauf 35597353780, amd64 und arm64). Die
Zusage aus dem EU-Outreach an OS2ai, GovChat-NL und Buerokratt ist damit
eingeloest, sobald v1.2.0 veroeffentlicht ist. **Offen bleiben Bausteine 2
(lexikalische Sprachfelder mit Migration) und 3 (UI-Kataloge)**; beide gehen
wie vorgesehen nach v1.3 und sind unten unveraendert beschrieben. Belege:
`.planning/phases/16-haertung-und-store-einreichung-v1-2-0/16-10-SUMMARY.md`.

**Ehrlicher Ist-Stand:** Die semantische Seite kann die vier Sprachen HEUTE
schon, multilingual-e5-small ist mehrsprachig. Es fehlen drei Bausteine, und
sie sind sehr unterschiedlich teuer:

1. **OCR (klein, 1 bis 2 PT):** tesseract-ocr-spa/ita/nld/por im Dockerfile
   (gleiche tesseract-lang-Quelle und Versionslogik wie deu/eng/fra, siehe
   die dortigen Pin-Kommentare) plus `OCR_LANGUAGE_ALLOWLIST` und
   `OCR_DEFAULT_LANGUAGES`-Entscheid in backend/src/findling/config.py plus
   Tests. Fasst den Index NICHT an.
2. **Lexikalische Suche (mittel, grob 5 bis 10 PT):** `DEFAULT_LANGUAGES`
   ("de","en") sind Schema-Felder im Tantivy-Index. Neue Sprachfelder heissen
   Schema-Aenderung, also Migration (Merker: jeder Minor-Sprung braucht eine
   `Version00XX00Date...`-Migration, sonst stumme Suche) und faktisch
   Reindex-Frage. Komposita-Zerlegung entfaellt, ist Deutsch-Spezifikum.
3. **UI-Kataloge (klein je Sprache, niedrige Prioritaet):** je 174 Schluessel;
   das FR-Gate war Muttersprachler-Abnahme, die fuer diese vier fehlt. Eher
   maschinell plus Community-Review, getrennt entscheiden.

**Einordnung (Owner-Entscheid 15.09.2026):**
- **In v1.2.0 mitnehmbar:** NUR Baustein 1 (OCR), als Kandidat fuer Phase 16,
  und dort erst NACH der Phase-15-Messanfahrt einbauen: der Werkzeugstand ist
  protokollpflichtige Vergleichbarkeitsbedingung des Messlaufs (gleiche Logik,
  aus der Dependabot-PR #9 gehalten wird). Beim Phase-16-Planen pruefen, ob es
  ohne Terminrisiko fuer die Store-Einreichung passt; im Zweifel faellt es in
  BL-F02-Folgerelease.
- **v1.3 direkt nach v1.2.0:** Baustein 2 als eigener kleiner Milestone
  "Sprachausbau Sued/West" mit sauberer Migration; Baustein 3 dort mit
  entscheiden.

**Erweiterung 15.09.2026 (EU-Outreach-Zusagen, Owner):** Zusaetzlich zu
es/it/nl/pt kommen DAENISCH (dan) und ESTNISCH (est) in Baustein 1 (OCR):
in den Outreach-Entwuerfen an OS2ai (DK), GovChat-NL (NL) und Buerokratt (EE)
ist OCR fuer die jeweilige Sprache als "naechstes Release" zugesagt.
tesseract-ocr-dan und tesseract-ocr-est existieren in derselben
tesseract-lang-Quelle. Die Zusage bindet Baustein 1 an das naechste Release
nach Versand der Mails.

**Warum nicht mehr in v1.2:** Milestone ist mit 17 Requirements geschnitten
und approved, stable35-Frist haengt drin, und eine Schema-Aenderung vor der
Phase-15-Messung zerstoert den v1.1-Vergleich (D-04-Linie).
