# 45-STORE-VORLAGE: kurze Store-Texte für 1.7.0 (Plan 45-11, STORE-03)

Stand 26.11.2026, nach der Abnahme der Härtung 45-10. Zur Freigabe durch den
Owner. Der Store-Text reist mit dem Release und ist danach nicht editierbar.

**Empfehlung:** die sechs Beschreibungen unten so freigeben. Sie halbieren den
Text (rund 1.200 bis 1.500 statt 2.300 bis 2.900 Zeichen) und liegen damit
zwischen context_chat und recognize. Was wegfällt, steht schon seit Plan 45-07
in den drei READMEs und wird dort geprüft (Liste der Verlagerungen unten).
Datenschutz-Satz, Connector-Satz und Umstiegs-Link sind wörtlich wie in 1.6.5.
Namen und Summaries bleiben unverändert.

## Längenvergleich

Store-API einmal abgefragt: `curl -s https://apps.nextcloud.com/api/v1/apps.json`
am 2026-11-26T18:42:31Z (1017 Apps). Gezählt: Zeichen der Beschreibung, ohne
Rand-Leerzeilen. Die Vergleichs-Apps führen nur Englisch; die ExApps
(context_chat_backend, findling_backend) stehen nicht in dieser Liste.

| App | Sprache | Zeichen |
|---|---|---|
| context_chat 5.6.0 (Zwei-App-Muster wie Findling) | en | 610 |
| files_fulltextsearch_tesseract 32.0.0 (OCR zur Volltextsuche) | en | 357 |
| fulltextsearch 35.0.1 | en | 62 |
| recognize 9.0.9 (KI-App mit Langtext) | en | 3148 |
| findling alt (1.6.5, im Store) | en | 2517 |
| findling alt (1.6.5, im Store) | de | 2662 |
| findling alt (1.6.5, im Store) | fr | 2884 |
| findling_backend alt (main, Stand 1.6.5) | en | 2284 |
| findling_backend alt (main, Stand 1.6.5) | de | 2403 |
| findling_backend alt (main, Stand 1.6.5) | fr | 2631 |
| findling neu (Entwurf) | en | 1279 |
| findling neu (Entwurf) | de | 1329 |
| findling neu (Entwurf) | fr | 1473 |
| findling_backend neu (Entwurf) | en | 1212 |
| findling_backend neu (Entwurf) | de | 1215 |
| findling_backend neu (Entwurf) | fr | 1375 |

Rund die Hälfte jedes neuen Texts sind die drei festen Kernsätze und die zwei
Links; kürzer geht es nur, wenn einer davon fällt.

## Die sechs Entwürfe

### findling, en

```
Full text, OCR and semantic search for your Nextcloud files, in the normal search bar and without configuration.

What Findling does:
- Full text search in the normal Nextcloud search bar
- OCR for scanned PDFs and images
- Semantic search: finds documents through paraphrases
- Every result is permission-checked by Nextcloud
- No configuration: the first index run starts on its own

Privacy: everything runs locally, no telemetry, nothing leaves your server

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Requirements:
- Nextcloud 33 to 35, apps: AppAPI (HaRP as the deploy target), Findling Backend (External Apps), Findling
- RAM: 4 GB is enough
- CPU: 2 cores are enough, amd64 and arm64

Switching from fulltextsearch/Elasticsearch: [steps in the documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/docs/migrate-from-fulltextsearch.en.md)

Documentation: [README on GitHub](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/README.en.md)

Enterprise support and paid add-ons: request a quote at admin@infranode.dev
```

### findling, de

```
Volltextsuche, Texterkennung und semantische Suche für Ihre Nextcloud-Dateien, in der normalen Suchleiste und ohne Konfiguration.

Was Findling kann:
- Volltextsuche über die normale Nextcloud-Suchleiste
- Texterkennung für gescannte PDFs und Bilder
- Semantische Suche: findet Dokumente auch über Umschreibungen
- Jeder Treffer wird von Nextcloud rechtegeprüft
- Keine Konfiguration: der erste Indexlauf startet von selbst

Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server

Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server.

Anforderungen:
- Nextcloud 33 bis 35, Apps: AppAPI (HaRP als Deploy-Ziel), Findling Backend (External Apps), Findling
- RAM: 4 GB genügen
- CPU: 2 Kerne genügen, amd64 und arm64

Umstieg von fulltextsearch/Elasticsearch: [Schritte in der Dokumentation](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/docs/migrate-from-fulltextsearch.md)

Dokumentation: [README auf GitHub](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/README.md)

Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev
```

### findling, fr

```
Recherche plein texte, OCR et recherche sémantique pour vos fichiers Nextcloud, dans la barre de recherche normale et sans configuration.

Ce que Findling sait faire :
- Recherche plein texte dans la barre de recherche normale de Nextcloud
- Reconnaissance optique pour les PDF numérisés et les images
- Recherche sémantique : trouve les documents par des périphrases
- Chaque résultat est vérifié par Nextcloud selon vos droits
- Aucune configuration : la première indexation démarre d'elle-même

Confidentialité : tout fonctionne localement, aucune télémétrie, rien ne quitte votre serveur

Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur.

Prérequis :
- Nextcloud 33 à 35, applications : AppAPI (HaRP comme cible de déploiement), Findling Backend (External Apps), Findling
- RAM : 4 Go suffisent
- CPU : 2 cœurs suffisent, amd64 et arm64

Passer de fulltextsearch/Elasticsearch à Findling : [étapes dans la documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/docs/migrate-from-fulltextsearch.fr.md)

Documentation : [README sur GitHub](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/README.fr.md)

Support entreprise et modules payants : demande de devis à admin@infranode.dev
```

### findling_backend, en

```
The External App behind the Findling search app: text extraction, OCR and the search index.

What Findling Backend is:
- Runs entirely inside your own instance and does nothing without the Findling app
- Never modifies your files
- Performance profile and search model are chosen on the admin page of the Findling app

Privacy: everything runs locally, no telemetry, nothing leaves your server

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Requirements:
- Nextcloud 33 to 35, apps: AppAPI (HaRP as the deploy target), Findling Backend (External Apps), Findling
- RAM: 4 GB is enough
- CPU: 2 cores are enough, amd64 and arm64

Switching from fulltextsearch/Elasticsearch: [steps in the documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/docs/migrate-from-fulltextsearch.en.md)

Documentation: [README on GitHub](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/README.en.md)

Enterprise support and paid add-ons: request a quote at admin@infranode.dev
```

### findling_backend, de

```
Die External App hinter der Such-App Findling: Textauszug, Texterkennung und der Suchindex.

Was Findling Backend ist:
- Läuft komplett in Ihrer eigenen Instanz und tut ohne die App Findling nichts
- Verändert nie Ihre Dateien
- Leistungsprofil und Suchmodell werden in der Verwaltung der App Findling gewählt

Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server

Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server.

Anforderungen:
- Nextcloud 33 bis 35, Apps: AppAPI (HaRP als Deploy-Ziel), Findling Backend (External Apps), Findling
- RAM: 4 GB genügen
- CPU: 2 Kerne genügen, amd64 und arm64

Umstieg von fulltextsearch/Elasticsearch: [Schritte in der Dokumentation](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/docs/migrate-from-fulltextsearch.md)

Dokumentation: [README auf GitHub](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/README.md)

Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev
```

### findling_backend, fr

```
L'External App derrière l'application de recherche Findling : extraction de texte, reconnaissance optique et index.

Ce qu'est Findling Backend :
- Fonctionne entièrement dans votre propre instance et ne fait rien sans l'application Findling
- Ne modifie jamais vos fichiers
- Le profil de performance et le modèle de recherche se choisissent dans la page d'administration de l'application Findling

Confidentialité : tout fonctionne localement, aucune télémétrie, rien ne quitte votre serveur

Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur.

Prérequis :
- Nextcloud 33 à 35, applications : AppAPI (HaRP comme cible de déploiement), Findling Backend (External Apps), Findling
- RAM : 4 Go suffisent
- CPU : 2 cœurs suffisent, amd64 et arm64

Passer de fulltextsearch/Elasticsearch à Findling : [étapes dans la documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/docs/migrate-from-fulltextsearch.fr.md)

Documentation : [README sur GitHub](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/README.fr.md)

Support entreprise et modules payants : demande de devis à admin@infranode.dev
```

## Liste der Verlagerungen

Alles, was die Beschreibungen abgeben, steht seit Plan 45-07 (Commits fdfe1b70,
907baa2f) in README.md, README.en.md und README.fr.md. Die Abschnitte sind am
26.11.2026 in allen drei Dateien nachgesehen.

| Inhalt (bisher im Store-Text) | README-Abschnitt de / en / fr | Gate aus 45-07 |
|---|---|---|
| Filter nach Dateityp oder Ordner | Was Findling kann / What Findling does / Ce que Findling sait faire | keiner (README-Liste) |
| Texterkennung: zehn Sprachen, drei voreingestellt | wie oben | keiner (README-Liste) |
| Ähnliche Dokumente ("Similar documents") | wie oben | test_the_similar_documents_line_stands_once_in_every_readme; test_the_similar_documents_line_stands_in_all_six_descriptions_and_the_changelog (test_phase36_audit.py, liest die READMEs) |
| Ordner oder Muster wie *.photoslibrary ausschließen | wie oben | keiner (README-Liste) |
| Leistungsprofile, Suchmodell int8/fp32 | wie oben | keiner (README-Liste) |
| Suchsprachen | wie oben, letzter Punkt | test_the_language_line_stands_right_before_the_limitations_in_all_three_readmes |
| Die fünf bekannten Grenzen | Bekannte Grenzen / Known limitations / Limites connues | test_every_readme_carries_the_five_known_limitations_under_its_heading; test_the_english_known_limitations_of_the_readme_stand_verbatim_in_the_doc |
| Formatliste | Unterstützte Dateitypen / Supported file types / Types de fichiers pris en charge | test_every_readme_names_the_formats_of_1_5_in_its_file_type_section |
| Messzahl (730,2 MB resident, harte 2-GB-Grenze) | Anforderungen / Requirements / Prérequis | test_the_measured_figure_stands_once_in_every_readme_in_the_spelling_of_its_language |
| Share-Satz ("Ohne Zutun läuft Findling ...") | Anforderungen / Requirements / Prérequis | test_the_share_sentence_stands_in_the_readme_of_its_language |

Die Doku-Links der Entwürfe zeigen auf die ganzen READMEs
(`blob/v1.7.0/README.md`, `README.en.md`, `README.fr.md`), ohne Anker; alle
drei Dateien existieren. Die Umstiegs-Links zeigen wie heute auf
`docs/migrate-from-fulltextsearch.md`, `.en.md`, `.fr.md`; alle drei
existieren. Beide Linkziele lösen erst nach dem Tag v1.7.0 auf.

Neu gegenüber 1.6.5 (nicht wörtlich übernommen):

- der einleitende Satz je App (findling: aus der Summary abgeleitet;
  findling_backend: bisher erster Listenpunkt)
- "(HaRP als Deploy-Ziel)" in der Anforderungszeile, Wortlaut aus den READMEs
- die Zeile "Dokumentation: [README auf GitHub](...)" je Sprache
- der Datenschutz-Satz steht als eigene Zeile statt als Listenpunkt, Wortlaut
  unverändert (Gate PRIVACY_MARKERS bleibt grün)
- Texterkennung ohne Sprachangabe ("für gescannte PDFs und Bilder")

## Diff-Auszug alt/neu (findling, de)

```diff
+Volltextsuche, Texterkennung und semantische Suche für Ihre Nextcloud-Dateien, in der normalen Suchleiste und ohne Konfiguration.
+
 Was Findling kann:
 - Volltextsuche über die normale Nextcloud-Suchleiste
-- Filter nach Dateityp oder Ordner direkt in der Nextcloud-Suche
-- Texterkennung für gescannte PDFs und Bilder: zehn Sprachen verfügbar, voreingestellt sind Deutsch, Englisch und Französisch
+- Texterkennung für gescannte PDFs und Bilder
 - Semantische Suche: findet Dokumente auch über Umschreibungen
-- Ähnliche Dokumente: ein Link an jedem Treffer der Ergebnisseite listet Dateien mit verwandtem Inhalt
 - Jeder Treffer wird von Nextcloud rechtegeprüft
 - Keine Konfiguration: der erste Indexlauf startet von selbst
-- Ordner oder Muster wie *.photoslibrary vom Index ausschließen
-- Leistungsprofile: Sparsam voreingestellt, Standard und Leistung nach einer Vorab-Prüfung der Hardware
-- Suchmodell: int8 eingebaut, das genauere fp32 unter Standard und Leistung einmalig ladbar
-- Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server
-- Suchsprachen: Deutsch und Englisch voreingestellt, Spanisch, Italienisch, Niederländisch, Portugiesisch und Tschechisch verfügbar
-
-Umstieg von fulltextsearch/Elasticsearch: [Schritte in der Dokumentation](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/docs/migrate-from-fulltextsearch.md)
 
-Bekannte Grenzen:
-- Spanisch: año und ano gelten als dasselbe Wort
-- Portugiesisch: Schreibweisen vor und nach der Rechtschreibreform werden nicht vereinheitlicht
-- Zusammengesetzte Wörter werden nur für Deutsch und Niederländisch zerlegt
-- Französisch hat keine eigene Analysekette für den Dokumenttext
-- Tschechisch: keine Stammformreduktion, gebeugte Formen gelten als eigene Wörter
+Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server
 
 Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server.
 
-Unterstützte Dateitypen:
-- PDF (auch gescannt), DOC, DOCX, PPTX, XLS, XLSX, ODT, ODS, ODP
-- HTML, RTF, TXT, Markdown, CSV, Mails (EML)
-- ZIP-Dateien: die enthaltenen Dateien, ohne Texterkennung
-- Bilder per Texterkennung: JPEG, PNG, TIFF, WebP, HEIC
-
 Anforderungen:
-- Nextcloud 33 bis 35, Apps: AppAPI, Findling Backend (External Apps), Findling
-- RAM: 4 GB genügen, 730,2 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
+- Nextcloud 33 bis 35, Apps: AppAPI (HaRP als Deploy-Ziel), Findling Backend (External Apps), Findling
+- RAM: 4 GB genügen
 - CPU: 2 Kerne genügen, amd64 und arm64
 
-Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware hat, gibt per Profil frei: höchstens die Hälfte der Maschine, auf der das Backend läuft (Profil Standard), oder alles bis auf einen Kern (Profil Leistung).
+Umstieg von fulltextsearch/Elasticsearch: [Schritte in der Dokumentation](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/docs/migrate-from-fulltextsearch.md)
+
+Dokumentation: [README auf GitHub](https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/README.md)
 
 Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev
```

Die anderen fünf Beschreibungen ändern sich nach demselben Muster;
findling_backend verliert zusätzlich die Listenpunkte "Filter", "Ähnliche
Dokumente", "Ordner oder Muster" und "Suchsprachen", der bisherige erste
Listenpunkt wird zum einleitenden Satz.

## Prüfungen des Entwurfs

- Kern je Beschreibung (Skript im Scratchpad, Vergleich gegen die heutige
  info.xml derselben Sprache): Datenschutz-Satz, Connector-Satz, Umstiegs-Zeile
  und Enterprise-Zeile je genau einmal und zeichengleich; Doku-Link auf das
  README der eigenen Sprache genau einmal. Keine Messzahl, keine Grenzen,
  keine Formatliste, kein Share-Satz, keine Zeile Ähnliche Dokumente.
- Keine U+2013, keine U+2014, keine Emojis.
- Umlaut-Audit der deutschen Entwürfe (Wörter mit ae, oe, ue, ss): Treffer
  nur "KI-Assistenten" und "verlässt", beide richtig. Kein ASCII-Ersatz.
- Kein Wort aus der Sperrliste der Store-Texte (BLOCKED_TERM).

## Offene Punkte für die Freigabe

1. Enterprise-Zeile: bleibt im Entwurf (gehört nicht zum Kern von D-45-14,
   steht aber auch nicht auf der Verlagerungsliste). Streichen spart rund 80
   Zeichen je Text.
2. RAM- und CPU-Zeile ohne Messzahl ("4 GB genügen", "2 Kerne genügen")
   bleiben als Anforderung; der Gate zählt sie nicht als Messzahl.
3. Datenschutz-Satz als eigene Zeile statt Listenpunkt (Wortlaut gleich).
