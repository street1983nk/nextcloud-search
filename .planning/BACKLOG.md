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
