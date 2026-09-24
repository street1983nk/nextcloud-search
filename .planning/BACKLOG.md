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

**STAND 23.09.2026: Bausteine 2 und 3 IN MILESTONE v1.3 AUFGENOMMEN** (Owner-Entscheid
23.09., REQ LEX-01..08 / KAT-01..02 / KOMP-01, Phasen 17 bis 21). Korrektur aus der
v1.3-Research: die Kataloge haben 199 Schluessel (nicht 174), Nextcloud kennt kein
'pt', nur pt_BR/pt_PT. Dieser Eintrag bleibt nur als Herkunftsbeleg stehen.

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

## BL-F03: Messanfahrt-Buendel, die fuenf offenen Boxzahlen

**STAND 23.09.2026: IN MILESTONE v1.3 AUFGENOMMEN** (Phase 22, REQ MESS-07..09,
plus zwei neue Messauftraege: Indexgroesse bei sechs Sprachfeldern, Wandzeit des
Re-Analyse-Umbaus). Dieser Eintrag bleibt nur als Herkunftsbeleg stehen.

**Auslöser:** Owner-Entscheid 21.09.2026 beim v1.2-Abschluss: das Buendel wird
als Messphase in den NAECHSTEN Milestone aufgenommen, keine eigenstaendige
Anfahrt vorher. Der Korpus-Snapshot `snap-03f1d1d9ad9262704` bleibt dafuer
bewusst im Standard-Tier stehen (dritter bewusster Behalten-Entscheid,
~2,85 USD/Monat).

Die fuenf Punkte, alle nur auf einer Box messbar, alle mit Herkunftsbeleg:

1. **M-01-Zahl:** die Dauer des inneren Aufrufs auf Zielhardware. Die
   Instrumentierung steht seit Plan 16-06 (`SLOW_CALL_LOG_MILLISECONDS`),
   die Zahl fehlt. Quelle: `docs/audits/2026-09-phase-16/README.md`
   Abschnitt 5.5, Verdikt "teilerfuellt".
2. **Wirkungsnachmessung 92c/99d:** die Nachfolgefassungen
   `92c-wechsel.sh` (occ-Rueckgabewert) und `99d-filter-sortierung.sh`
   (Passwort aus Datei) sind boxlos gruen, auf einer Box nie gelaufen
   (L-03/L-04, Auflage A1).
3. **Bodensatz-Zyklus 2:** senkt eine zweite Entladung den Bodensatz von
   628,0 MB? Messbericht v1.2 Abschnitt 10 Punkt 7: gefahren wurde genau
   ein Zyklus.
4. **Die 6 Fehlschlaege und 44 uebersprungenen Dateien** der Endzahl
   52.137/44/6 einzeln benennen (Messbericht Abschnitt 10 Punkt 4);
   vermutlich reicht Volume mounten + DB/Log lesen, kein Reindex.
5. **Kaltstartlatenz sauber:** der Messrequest von DI-07-02 traf einen
   Leerbegriff (`EmptyResultGroup`); anon-Spitze und Wandzeit stehen, die
   Latenzaussage nicht (Messbericht Abschnitt 10 Punkt 6).

**Aufwandsschaetzung (grob, VOR der Phase durch ein Rechenblatt zu ersetzen):**
6-10 Boxstunden auf m7g.large aus dem Snapshot, ca. 1,0-1,5 USD; kein
Volllauf noetig. Runbook-Disziplin gilt: Rechenblatt + Deckel VOR dem Start
zur Owner-Freigabe, Cron-Intervall-Gate, Digest-Wechsel, Rohdaten committen.
Dazu aus dem Messbericht Punkt 11: kein Werkzeug-Fix der v1.2-Anfahrt ist in
seiner Wirkung nachgemessen; diese Anfahrt ist genau dafuer da.


## BL-F04: Leistungsprofile mit Vorab-Pruefung (OCR-Power, Modellwahl, Test vor dem Speichern)

**Ausloeser:** Reddit-Kommentar von ayhamoo am 24.09.2026 unter dem Findling-Post
(Screenshot beim Owner, sinngemaess: OCR-Einstellungen fuer mehr Leistung, er hat
Headroom; besseres Embeddings-Modell; die UI soll Aenderungen VOR dem Speichern
testen). Zweiter Nachfrage-Beleg dieser Art nach den Sprachwuenschen (BL-F02).
Owner-Steuerung 24.09.: viele Nutzer haben heute groessere Boxen als 4 GB,
das beruecksichtigen und mehr Geschwindigkeit ermoeglichen.

**OWNER-ENTSCHEID 24.09.2026: GESETZT als naechstes Vorhaben nach v1.3**
("im anschluss machen wir den punkt mit den grossen boxen"). Damit ist
BL-F04 der Kern des naechsten Milestones (v1.4), kein blosser Kandidat mehr.
Beim /gsd:new-milestone nach dem v1.3-Abschluss zuerst diesen Eintrag laden.

**Kern des Vorhabens:**

1. **Leistungsprofile** statt Einzelschrauben: Sparsam (heutiger Default,
   4-GB-Versprechen unveraendert) / Standard / Leistung (8-GB+-Boxen).
   Ein Profil buendelt: INDEX_WORKERS, OCR-Seitendeckel/DPI/Timeout,
   Tantivy-heap_size/num_threads, Embedding-Batchgroesse und -threads.
   Vorbild: Abschnitt "Stack Patterns by Variant" in CLAUDE.md, dort steht
   die 8-GB-Schablone schon.
2. **Modellwahl** als Teil des Leistungsprofils: e5-small int8 (Default) vs.
   fp32; groessere Modelle (z.B. jina-v2-base-de) nur nach RAM-Messung und
   Lizenzpruefung. HARTE FOLGE: Modellwechsel = Vektor-Reindex (Dimension/
   Quantisierung), Umbau-Mechanik aus Phase 18 (rebuild.py) hilft NICHT,
   weil vectors.db betroffen ist, nicht der Tantivy-Index.
3. **Vorab-Pruefung ("Test vor dem Speichern"):** Probelauf vor dem
   Uebernehmen: Modell laedt, RAM-Schaetzung gegen die Box, eine Probeseite
   OCR mit den neuen Werten, Verdikt in der UI. Passt zur Messkultur des
   Projekts und faengt die 4-GB-Boxen ab, bevor sie sich totkonfigurieren.
4. **Admin-UI**: erste echte Settings-Seite; bisher bewusst nur
   environment-variables (Zero-Config). Zero-Config bleibt gewahrt, wenn
   die Profile optional sind und der Default unveraendert bleibt.

**Bewusst offen:** freier Core vs. Pro-Schiene (ISV-Entscheid 03.11.);
Empfehlung: Profile in den freien Core, das ist die Selfhoster-Zielgruppe.

**Vorbedingungen:** v1.3 geliefert; RAM-Messungen je Profil auf echter
Hardware (Messphasen-Muster); UI-Phase mit ui-phase-Gate.

