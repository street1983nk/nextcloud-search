# Die Store-Texte beider Apps, in einer Quelle

Die `info.xml` ist die Registrierung im App Store, und sie ist zweimal
vorhanden, einmal je Hälfte. Ein dreisprachiger Text, der in zwei XML-Dateien
gepflegt wird, läuft auseinander, sobald jemand nur eine der beiden anfasst.
Die Nachzieh-Regel aus D-12, nach der jede Änderung an einem Text alle drei
Sprachen mitnimmt, braucht deshalb einen Ort, an dem alle drei Fassungen
nebeneinander stehen und vergleichbar sind. Das ist diese Datei.

Die Texte unten sind die Vorlage, aus der beide `info.xml` ihre Elemente
beziehen, wortwörtlich. Wer hier etwas ändert, ändert es in der zugehörigen
`info.xml` mit; `backend/tests/test_store_metadata.py` prüft mechanisch, was
sich daran mechanisch prüfen lässt.

## Die Regeln, die für jeden Text unten gelten

| Regel | Woher sie kommt |
|---|---|
| `name` und `summary` sind höchstens 128 Zeichen lang | `l10n-string` in der Store-XSD |
| `description` hat keine Längengrenze, darf aber nicht leer sein | `l10n-text` über `non-empty-string` |
| Sprachcode ist `de`, `fr` oder gar keiner; `de_DE` ist kein gültiger Wert | die Liste in `l10n-code` |
| Diese Regel gilt für die Store-Texte in `info.xml` und **nicht** für die Übersetzungskataloge unter `php/l10n/`. Dort ist `de_DE` gültig und seit dem 09.09.2026 auch vorhanden: Nextcloud führt `de` und `de_DE` als zwei Sprachen im Nutzerprofil, und eine App ohne `de_DE` ist für jeden untranslated, der die Sie-Form gewählt hat | die zwei Listen sind zwei Dinge; Befund B der Abnahme von Phase 9 |
| Je Elementart darf ein Sprachcode nur einmal vorkommen | `uniqueNameL10n`, `uniqueSummaryL10n`, `uniqueDescriptionL10n` |
| Kein Element bleibt leer | ein leeres Element löst beim Upload einen Serverfehler aus, gemessen am Schwesterprojekt |
| Keine Backticks und keine Tabellen in einer Beschreibung | der Store rendert Markdown anders als das Repository |
| Keine Gedankenstriche, keine Emojis, echte Umlaute, echte Akzente | die Typografie-Regel dieses Projekts |
| Genau EIN Satz Querverweis auf den MCP Connector | D-12 erfuellt seit 07.09.2026: der Content-Hit-Fidelity-Test (Connector-PR #2) misst die Rechte-Treue |

Die englische Fassung steht in einem Element **ohne** `lang`-Attribut. Die XSD
setzt für ein fehlendes Attribut den Vorgabewert `en` ein, ein zusätzliches
`lang="en"` wäre also ein doppelter Sprachcode und würde die Eindeutigkeit
verletzen.

## Zum Vokabular öffentlicher Artefakte

Seit Plan 06.1-13 führt dieses Repository ein Vokabular-Gate. Es steht in
`backend/tests/test_store_metadata.py` neben den übrigen Store-Zusicherungen,
und seine Reichweite ist Entscheidung E-H2 vom 06.09.2026: Die Regel gilt für
deutsche Prosa in den öffentlichen Texten, der englische Fachausdruck in einem
technischen Kommentar einer ausgelieferten Datei ist ausdrücklich ausgenommen.
Die Ausnahme steht im Kopf des Gates und wird von einem eigenen Fall belegt,
damit sie beim nächsten Streit nicht nur behauptet ist. Bis zum 04.09.2026 gab
es keine solche Prüfung; das war der Befund DI-05-32, und er ist mit E-H2
geschlossen.

Der gesperrte Projektbegriff für einen Aufbewahrungsort kommt in der deutschen
und in der französischen Fassung unten nicht vor: sie sprechen von einer
Sicherung, von komprimierten Dateien und vom Quellcode, wo eine naheliegende
Formulierung ihn benutzt hätte. Die englische Fassung bräuchte ihn als
Dateityp-Bezeichnung, kommt unten aber ebenfalls ohne aus, weil keiner der
sechs Texte einzelne Dateitypen aufzählt. Diese Datei zählt im Gate mit jeder
Zeile, nicht nur mit ihren deutschen Absätzen; welche Zählung ein Fall benutzt,
sagt er selbst.

## Die Form der Texte, Owner-Entscheid vom 07.09.2026

Die erste eingereichte Fassung (1.0.0) trug den Messbericht im Store-Text und
war damit ein Vielfaches so lang wie die Beschreibungen vergleichbarer Apps.
Der Owner hat am 07.09.2026 entschieden: Die Store-Beschreibung ist eine kurze
Faktenliste aus genau drei Blöcken, was die App kann, welche Dateitypen sie
liest, und was sie an Hardware braucht (RAM, CPU, Architekturen,
Nextcloud-Fenster). Keine Messgeschichten, keine Erzählabsätze. Die
Dateitypenliste kommt aus der Allowlist in
`backend/src/findling/extract/dispatch.py`, die Hardware-Zeilen aus den
Messungen; wer die Zahlen will, findet sie in `docs/performance.md` und
`docs/embeddings.md`.

Der gemessene Satz von Plan 06-11 lebte seit diesem Entscheid nur noch in
`README.en.md`, und das Gate `test_store_metadata.py` band ihn dort fest.
Im Store-Text stand als einzige Zahl die schlichte Hardware-Zusage (4 GB
genügen, harte 2-GB-Grenze, gemessen), und die Herkunftsregel bleibt: keine
Zahl im Text, die nicht im Quellcode belegt ist, gerundet wird nichts.

## Nachtrag vom 11.09.2026: die eine Kernzahl im Store-Text

Der Owner hat am 11.09.2026 die Fassung B des Entwurfs unten gewählt. Die
RAM-Zeile beider Hälften nennt seitdem zusätzlich die Grundlast im Leerlauf mit
103,2 MB, dreisprachig, und sonst ändert sich an den sechs Texten nichts. Die
Kurztext-Regel bleibt gewahrt, weil es bei genau einer Zahl bleibt. Der datierte
Alt-Neu-Vergleich (691,8 MB auf 103,2 MB, minus 85,1 Prozent, gemessen am
10.09.2026) steht in allen drei READMEs und nicht im Store-Text, und die
Mess-Vorbehalte stehen im Bericht und in `docs/performance.md` (D-06, D-08).

Mit derselben Entscheidung ist der Messsatz dreisprachig geworden: er steht seit
dem 11.09.2026 in `README.en.md`, `README.md` und `README.fr.md`, und
`scan_measured_sentence` hält alle drei Wortlaute fest, je ein Aufruf je Datei.
Die Gleichläufigkeit der drei READMEs ist damit eine Maschine und keine Regel
mehr.

## Nachtrag vom 21.09.2026: die Messzahl der Fassung 1.2.0 (Entscheid E1)

Entscheid E1 der Phase 16 ist gesperrt: **731,9 MB nach Nutzung ersetzt die
103,2 MB an allen neun Stellen**, also in den sechs Store-Texten und in den
drei READMEs. Die Messgröße ist dabei eine andere geworden, und das ist der
ganze Punkt dieses Nachtrags: 103,2 MB war die Grundlast im Leerlauf mit nie
geladenem Modell, 731,9 MB ist der residente Stand des Containers, nachdem
einmal eingebettet und wieder entladen wurde. Herkunft: Marke C der Messung
vom 21.09.2026, Rohdatei
`docs/measurements/2026-09-v12-messung/rohdaten/94b-grundlast-rueckkehr.txt`,
gefahren auf einer AWS `m7g.large` mit nativem arm64 gegen das ausgelieferte
v1.2-Abbild, gerechnet über `anon` aus `memory.stat`. Die Begründung des
Owners: das ist die Zahl, die ein Selfhoster auf seiner 4-GB-Box wirklich
sieht, und sie verschweigt den Bodensatz nicht.

Die Kurztext-Regel bleibt gewahrt, weil es bei genau einer Messzahl je Text
bleibt. Die 4 GB und die harte 2-GB-Grenze sind Anforderungen und keine
Messzahlen; die 103,2 kommt in keinem der sechs Texte mehr vor, statt neben
der neuen Zahl zu stehen.

**Stand dieser Datei:** Die sechs Texte unten sind die Fassung 1.4.0, vom
Owner am 06.10.2026 abgenommen (Abschnitt "Entwurf 1.4.0 (Phase 29)") und in
Plan 29-12 am 06.10.2026 wörtlich in beide `info.xml` übernommen. Vorlage und
beide `info.xml` sind damit wortgleich; ein Unterschied zwischen ihnen ist
Drift. Die Messzahl ist 730,2 MB (D-09), in den sechs Texten und in den drei
READMEs. Der Entwurf mit allen Gegenüberstellungen steht unten im Abschnitt
"Entwurf 1.4.0 (Phase 29)", der vorige im Abschnitt "Entwurf v1.3.0".

---

# App 1: `findling` (PHP-Begleit-App, Store-Bereich "Apps")

## `<name>`

| Sprache | Element | Text |
|---|---|---|
| Englisch | `<name>` | Findling |
| Deutsch | `<name lang="de">` | Findling |
| Französisch | `<name lang="fr">` | Findling |

Der Name ist ein Eigenname und in allen drei Sprachen derselbe. Er steht
trotzdem dreimal da: die Nachzieh-Regel prüft, ob eine Elementart eine Sprache
verloren hat, und eine Elementart, die nur eine Sprache führt, wäre von einer,
die zwei davon eingebüßt hat, nicht zu unterscheiden. Der eingefrorene Name
steht in `docs/store-identity.md` und wird hier nicht neu erfunden.

## `<summary>`

| Sprache | Element | Text | Länge |
|---|---|---|---|
| Englisch | `<summary>` | Zero-config full text, OCR and semantic search for your files | 61 von 128 |
| Deutsch | `<summary lang="de">` | Volltextsuche, Texterkennung und semantische Suche ohne Konfiguration | 69 von 128 |
| Französisch | `<summary lang="fr">` | Recherche plein texte, OCR et recherche sémantique sans configuration | 69 von 128 |

## `<description>` (Englisch, ohne `lang`-Attribut)

What Findling does:
- Full text search in the normal Nextcloud search bar
- OCR for scanned PDFs and images: nine languages available, German, English and French are the default
- Semantic search: finds documents through paraphrases
- Every result is permission-checked by Nextcloud
- No configuration: the first index run starts on its own
- Performance profiles: Economy by default, Standard and Performance after a pre-check of the hardware
- Search model: int8 built in, the more accurate fp32 can be downloaded once under Standard and Performance
- Privacy: everything runs locally, no telemetry, nothing leaves your server
- Search languages: German and English by default, Spanish, Italian, Dutch and Portuguese available

Known limitations:
- Spanish: año and ano are treated as the same word
- Portuguese: spellings before and after the spelling reform are not unified
- Compound words are split for German and Dutch only
- French has no full text analysis chain for document text

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Supported file types:
- PDF (scanned too), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images through OCR: JPEG, PNG, TIFF, WebP

Requirements:
- Nextcloud 33 to 35, apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB is enough, 730.2 MB resident after an index run, under a hard 2 GB limit (measured)
- CPU: 2 cores are enough, amd64 and arm64

Without any change on your side, Findling keeps running as economically as before. Anyone with more hardware can use a profile to free at most half of the box (Standard profile) or everything but one core (Performance profile).

Enterprise support and paid add-ons: request a quote at admin@infranode.dev

## `<description lang="de">`

Was Findling kann:
- Volltextsuche über die normale Nextcloud-Suchleiste
- Texterkennung für gescannte PDFs und Bilder: neun Sprachen verfügbar, voreingestellt sind Deutsch, Englisch und Französisch
- Semantische Suche: findet Dokumente auch über Umschreibungen
- Jeder Treffer wird von Nextcloud rechtegeprüft
- Keine Konfiguration: der erste Indexlauf startet von selbst
- Leistungsprofile: Sparsam voreingestellt, Standard und Leistung nach einer Vorab-Prüfung der Hardware
- Suchmodell: int8 eingebaut, das genauere fp32 unter Standard und Leistung einmalig ladbar
- Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server
- Suchsprachen: Deutsch und Englisch voreingestellt, Spanisch, Italienisch, Niederländisch und Portugiesisch verfügbar

Bekannte Grenzen:
- Spanisch: año und ano gelten als dasselbe Wort
- Portugiesisch: Schreibweisen vor und nach der Rechtschreibreform werden nicht vereinheitlicht
- Zusammengesetzte Wörter werden nur für Deutsch und Niederländisch zerlegt
- Französisch hat keine eigene Analysekette für den Dokumenttext

Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server.

Unterstützte Dateitypen:
- PDF (auch gescannt), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Bilder per Texterkennung: JPEG, PNG, TIFF, WebP

Anforderungen:
- Nextcloud 33 bis 35, Apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB genügen, 730,2 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
- CPU: 2 Kerne genügen, amd64 und arm64

Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware hat, gibt per Profil höchstens die Hälfte der Box frei (Profil Standard) oder alles bis auf einen Kern (Profil Leistung).

Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev

## `<description lang="fr">`

Ce que Findling sait faire :
- Recherche plein texte dans la barre de recherche normale de Nextcloud
- Reconnaissance optique pour les PDF numérisés et les images : neuf langues disponibles, allemand, anglais et français par défaut
- Recherche sémantique : trouve les documents par des périphrases
- Chaque résultat est vérifié par Nextcloud selon vos droits
- Aucune configuration : la première indexation démarre d'elle-même
- Profils de performance : Économe par défaut, Standard et Performance après une vérification préalable du matériel
- Modèle de recherche : int8 intégré, le fp32 plus précis se télécharge une fois sous Standard et Performance
- Confidentialité : tout fonctionne localement, aucune télémétrie, rien ne quitte votre serveur
- Langues de recherche : allemand et anglais par défaut, espagnol, italien, néerlandais et portugais disponibles

Limites connues :
- Espagnol : año et ano sont traités comme le même mot
- Portugais : les graphies d'avant et d'après la réforme orthographique ne sont pas unifiées
- Les mots composés ne sont découpés que pour l'allemand et le néerlandais
- Le français n'a pas de chaîne d'analyse plein texte pour le contenu des documents

Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur.

Types de fichiers pris en charge :
- PDF (numérisés aussi), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images par reconnaissance optique : JPEG, PNG, TIFF, WebP

Prérequis :
- Nextcloud 33 à 35, applications : AppAPI, Findling Backend (External Apps), Findling
- RAM : 4 Go suffisent, 730,2 Mo résidents après une indexation, sous une limite stricte de 2 Go (mesuré)
- CPU : 2 cœurs suffisent, amd64 et arm64

Sans aucune intervention, Findling continue de fonctionner aussi sobrement qu'avant. Avec plus de matériel, un profil libère au plus la moitié de la machine (profil Standard) ou tout sauf un cœur (profil Performance).

Support entreprise et modules payants : demande de devis à admin@infranode.dev

---

# App 2: `findling_backend` (External App, Store-Bereich "External Apps")

## `<name>`

| Sprache | Element | Text |
|---|---|---|
| Englisch | `<name>` | Findling Backend |
| Deutsch | `<name lang="de">` | Findling Backend |
| Französisch | `<name lang="fr">` | Findling Backend |

Auch hier ein Eigenname, aus demselben Grund dreimal aufgeführt. Die App-Id
`findling_backend` und dieser Name sind in `docs/store-identity.md`
eingefroren.

## `<summary>`

| Sprache | Element | Text | Länge |
|---|---|---|---|
| Englisch | `<summary>` | Search backend for Findling: text extraction, OCR and the index | 63 von 128 |
| Deutsch | `<summary lang="de">` | Suchdienst für Findling: Textauszug, Texterkennung und der Index | 64 von 128 |
| Französisch | `<summary lang="fr">` | Service de recherche pour Findling : extraction de texte, OCR et index | 70 von 128 |

## `<description>` (Englisch, ohne `lang`-Attribut)

What Findling Backend is:
- The External App behind the Findling search app: text extraction, OCR and the search index
- Runs entirely inside your own instance and does nothing without the Findling app
- Never modifies your files
- Performance profile and search model are chosen on the admin page of the Findling app
- Privacy: everything runs locally, no telemetry, nothing leaves your server
- Search languages: German and English by default, Spanish, Italian, Dutch and Portuguese available

Known limitations:
- Spanish: año and ano are treated as the same word
- Portuguese: spellings before and after the spelling reform are not unified
- Compound words are split for German and Dutch only
- French has no full text analysis chain for document text

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Supported file types:
- PDF (scanned too), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images through OCR: JPEG, PNG, TIFF, WebP

Requirements:
- Nextcloud 33 to 35, apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB is enough, 730.2 MB resident after an index run, under a hard 2 GB limit (measured)
- CPU: 2 cores are enough, amd64 and arm64

Without any change on your side, Findling keeps running as economically as before. Anyone with more hardware can use a profile to free at most half of the box (Standard profile) or everything but one core (Performance profile).

Enterprise support and paid add-ons: request a quote at admin@infranode.dev

## `<description lang="de">`

Was Findling Backend ist:
- Die External App hinter der Such-App Findling: Textauszug, Texterkennung und der Suchindex
- Läuft komplett in Ihrer eigenen Instanz und tut ohne die App Findling nichts
- Verändert nie Ihre Dateien
- Leistungsprofil und Suchmodell werden in der Verwaltung der App Findling gewählt
- Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server
- Suchsprachen: Deutsch und Englisch voreingestellt, Spanisch, Italienisch, Niederländisch und Portugiesisch verfügbar

Bekannte Grenzen:
- Spanisch: año und ano gelten als dasselbe Wort
- Portugiesisch: Schreibweisen vor und nach der Rechtschreibreform werden nicht vereinheitlicht
- Zusammengesetzte Wörter werden nur für Deutsch und Niederländisch zerlegt
- Französisch hat keine eigene Analysekette für den Dokumenttext

Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server.

Unterstützte Dateitypen:
- PDF (auch gescannt), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Bilder per Texterkennung: JPEG, PNG, TIFF, WebP

Anforderungen:
- Nextcloud 33 bis 35, Apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB genügen, 730,2 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
- CPU: 2 Kerne genügen, amd64 und arm64

Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware hat, gibt per Profil höchstens die Hälfte der Box frei (Profil Standard) oder alles bis auf einen Kern (Profil Leistung).

Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev

## `<description lang="fr">`

Ce qu'est Findling Backend :
- L'External App derrière l'application de recherche Findling : extraction de texte, reconnaissance optique et index
- Fonctionne entièrement dans votre propre instance et ne fait rien sans l'application Findling
- Ne modifie jamais vos fichiers
- Le profil de performance et le modèle de recherche se choisissent dans la page d'administration de l'application Findling
- Confidentialité : tout fonctionne localement, aucune télémétrie, rien ne quitte votre serveur
- Langues de recherche : allemand et anglais par défaut, espagnol, italien, néerlandais et portugais disponibles

Limites connues :
- Espagnol : año et ano sont traités comme le même mot
- Portugais : les graphies d'avant et d'après la réforme orthographique ne sont pas unifiées
- Les mots composés ne sont découpés que pour l'allemand et le néerlandais
- Le français n'a pas de chaîne d'analyse plein texte pour le contenu des documents

Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur.

Types de fichiers pris en charge :
- PDF (numérisés aussi), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images par reconnaissance optique : JPEG, PNG, TIFF, WebP

Prérequis :
- Nextcloud 33 à 35, applications : AppAPI, Findling Backend (External Apps), Findling
- RAM : 4 Go suffisent, 730,2 Mo résidents après une indexation, sous une limite stricte de 2 Go (mesuré)
- CPU : 2 cœurs suffisent, amd64 et arm64

Sans aucune intervention, Findling continue de fonctionner aussi sobrement qu'avant. Avec plus de matériel, un profil libère au plus la moitié de la machine (profil Standard) ou tout sauf un cœur (profil Performance).

Support entreprise et modules payants : demande de devis à admin@infranode.dev

---

## Was in den sechs Texten oben bewusst nicht steht

Dieser Abschnitt ist die Begründung und gehört nicht in eine `info.xml`. Er
nennt den ausgeschlossenen Gegenstand beim Namen, weil eine Regel, die ihren
Gegenstand verschweigt, von niemandem nachgeprüft werden kann.

- **Nur EIN Satz zum MCP Connector, und keine RAG-Wortwahl.** Der
  Querverweis ist seit 07.09.2026 erlaubt (Fidelity-Test bestanden und
  gemergt), bleibt im Store aber ein einzelner Satz in schlichter Sprache;
  das RAG-Vokabular gehoert in die READMEs, nicht in den Store (Begruendung
  im Connector-BACKLOG BL-01).
- **Kein Vergleich mit einer anderen Suchlösung.** Eine App, die sich über die
  Konkurrenz definiert, sagt nichts über sich selbst.
- **Kein beworbenes Tokenlimit.** Die Abdeckungsaussage steht als Anteil im
  Text; der Deckel selbst ist keine beworbene Einstellung (D-01), und eine
  Tokenzahl sagt niemandem etwas.
- **Keine gerundete Verbesserung und keine Hochrechnung.** Jede Zahl in den
  Texten ist gemessen und steht mit ihrer Messreihe in `docs/performance.md`
  oder `docs/embeddings.md`; die datierte Vergleichszahl vom 05.09.2026 ist
  Teil der zwei ehrlichen Sätze und keine zweite Zusage.

---

# Entwurf v1.1.0, abgenommen am 11.09.2026

Dieser Abschnitt war der Entwurf, den der Owner vor der Einreichung gesehen hat.
Er bleibt als Begründung stehen, weil eine Entscheidung ohne die Fassungen, die
zur Wahl standen, später nicht nachvollziehbar ist. Er gehört zu Plan 11-09 und
legte genau zwei Entscheidungen vor, Teil 2 und Teil 3, dazu die französischen
Texte als zweiten Teil des FR-Gates (D-07). Die Abnahmezeile steht am Ende
dieses Abschnitts; die sechs Texte oben sind nachgezogen.

Jede Zahl unten stammt aus `docs/measurements/2026-09-vergleichsmessung-m7g/`
und nennt ihre Rohdatei. Gemessen am 09. und 10.09.2026 auf einer AWS
`m7g.large` mit nativem arm64, 4 GB Maschinenspeicher, harte Containergrenze
2 GiB.

| Größe | Vorwert v1.0 (Lauf 06-11 vom 05.09.2026) | v1.1 (10.09.2026) | Rohdatei |
|---|---|---|---|
| indexierte Dokumente | Vorwert 51.961 | **52.111** | `rohdaten/48-vektorbestand.txt` |
| Spitze des anonymen Speichers | Vorwert 1.813 MB | **1.764,2 MB** | `rohdaten/00-ende.txt`, aus `rohdaten/96-volllauf.csv` |
| Grundlast im Leerlauf | Vorwert 691,8 MB | **103,2 MB** | `rohdaten/94-grundlast.txt` |
| harte Grenze | 2 GiB | unverändert | `rohdaten/07-oom-beweis.txt` |

Eine Einordnung, damit die 52.111 nicht als veralteter Wert gelesen wird: Plan
11-06 hat auf derselben Box später 52.137 / 44 / 6 gemessen. Die Differenz von
39 Dateien ist der Referenzkorpus des Sprachfall-Kontos, der **nach** der
Vergleichsmessung hochgeladen wurde. Der Messsatz beschreibt den Lauf, den er
beschreibt, und behält deshalb die 52.111.

## Teil 1: Der Messsatz für README.en.md

Kein Entscheid, nur zur Durchsicht. Der bestehende Satz mit zwei getauschten
Werten, die harte Grenze bleibt. Diese Stelle ist die einzige maschinell
gehaltene: `MEASURED_SENTENCE` in `backend/tests/test_store_metadata.py` wird in
derselben Änderung nachgezogen, sonst ist das Gate rot.

> On a 4-GB ARM64 box with 52,111 indexed documents and the semantic search
> active, the container peaked at 1,764 MB of resident anonymous memory, under a
> hard 2 GB limit enforced by the kernel.

Darunter genau eine Zeile mit dem Vorher-Nachher der Grundlast, mit Datum und
Verweis auf den Bericht:

> Idle base load fell from 691.8 MB in v1.0 to 103.2 MB in v1.1, minus 85.1 per
> cent (measured 2026-09-10, method and raw data in docs/performance.md).

Zur Prozentzahl, damit sie nicht später auffällt: 588,6 von 691,8 MB sind
85,1 Prozent. Der Plan nennt "minus 85 Prozent", die Herkunftsregel dieses
Projekts rundet nichts, also steht hier 85,1. Wer die glatte Zahl vorzieht, sagt
es an diesem Checkpoint.

## Teil 2: Der Store-Text, Fassung A gegen Fassung B

Die Frage in einem Satz: Trägt die `info.xml` die eine neue Kernzahl, oder steht
sie nur im README, auf das der Store-Eintrag verweist?

Der Unterschied betrifft **eine Zeile in sechs Texten**, nämlich die RAM-Zeile im
Block Anforderungen beider Hälften, dreisprachig. Alles andere bleibt in beiden
Fassungen Wort für Wort so, wie es oben steht: die Faktenliste, die Dateitypen,
der eine Satz zum MCP Connector, der Datenschutzabsatz.

Der Verweis auf das README ist in beiden Fassungen derselbe und schon vorhanden:
der `<website>`-Eintrag beider `info.xml` zeigt auf das Repository und damit auf
`README.en.md`. Eine zusätzliche Verweiszeile im Beschreibungstext wäre eine
dritte Fassung und wird hier nicht vorgeschlagen.

### Fassung A: beide `info.xml` bleiben unverändert

Die eine Kernzahl steht im README, der Store-Eintrag verweist darauf. Das ist die
auslegungsärmste Lesart des Owner-Entscheids vom 07.09.2026, nach dem die
Store-Beschreibung eine kurze Faktenliste ohne Messgeschichte ist. Der Diff
beider `info.xml` bleibt leer, und der Grund steht mit Datum in dieser Datei.

Die RAM-Zeile, wörtlich, in beiden Hälften gleich:

> Englisch: RAM: 4 GB is enough, the container runs under a hard 2 GB limit (measured)
>
> Deutsch: RAM: 4 GB genügen, der Container läuft unter einer harten 2-GB-Grenze (gemessen)
>
> Französisch: RAM : 4 Go suffisent, le conteneur reste sous une limite stricte de 2 Go (mesuré)

### Fassung B: beide `info.xml` tragen die eine Kernzahl

Die Zeile mit den Anforderungen nennt zusätzlich die Grundlast im Leerlauf,
dreisprachig, und sonst ändert sich nichts. Die Kurztext-Regel bleibt gewahrt,
weil es bei genau einer Zahl bleibt. `docs/store-listing.md` zieht als Vorlage
nach, also stehen dieselben Worte in sechs Texten und in dieser Datei.

Die RAM-Zeile, wörtlich, in beiden Hälften gleich:

> Englisch: RAM: 4 GB is enough, 103.2 MB idle, under a hard 2 GB limit (measured)
>
> Deutsch: RAM: 4 GB genügen, 103,2 MB im Leerlauf, unter einer harten 2-GB-Grenze (gemessen)
>
> Französisch: RAM : 4 Go suffisent, 103,2 Mo au repos, sous une limite stricte de 2 Go (mesuré)

## Teil 3: Wird der Messsatz dreisprachig?

Heute trägt nur `README.en.md` den vollen Messsatz. `README.md` und
`README.fr.md` tragen die qualitative Zusage, und kein Gate hält die drei READMEs
gegeneinander: ihre Gleichläufigkeit ist heute eine Regel in `CLAUDE.md` und
keine Maschine.

Der Wortlaut für alle drei Sprachen, damit hier entschieden und nicht übersetzt
wird. Englisch steht schon so da, siehe Teil 1.

> Deutsch: Auf einer 4-GB-ARM64-Box mit 52.111 indexierten Dokumenten und
> aktiver semantischer Suche lag die Spitze des Containers bei 1.764 MB
> residentem anonymem Speicher, unter einer harten 2-GB-Grenze, die der Kernel
> durchsetzt.
>
> Französisch: Sur une machine ARM64 de 4 Go avec 52 111 documents indexés et la
> recherche sémantique active, le conteneur a atteint un pic de 1 764 Mo de
> mémoire anonyme résidente, sous une limite stricte de 2 Go imposée par le
> noyau.

Die Folge, in einem Satz: Wird der Messsatz dreisprachig, bekommt
`scan_measured_sentence` drei Wortlaute statt einem, je ein Aufruf je Datei, und
die Gleichläufigkeit der drei READMEs ist danach eine Maschine statt einer Regel
in `CLAUDE.md`. Bleibt er einsprachig, ändert sich am Gate nichts, und die
beiden anderen READMEs behalten ihre qualitative Zusage.

**Unabhängig von dieser Entscheidung** bekommen alle drei READMEs die datierte
Vorher-Nachher-Zeile zur Grundlast, weil D-06 den datierten Vergleich im README
verlangt:

> Deutsch: Die Grundlast im Leerlauf ist von 691,8 MB in v1.0 auf 103,2 MB in
> v1.1 gefallen, minus 85,1 Prozent (gemessen am 10.09.2026, Methode und
> Rohdaten in docs/performance.md).
>
> Französisch: La charge de base au repos est passée de 691,8 Mo en v1.0 à
> 103,2 Mo en v1.1, moins 85,1 pour cent (mesuré le 10.09.2026, méthode et
> données brutes dans docs/performance.md).

## Zum FR-Gate, zweiter Teil (D-07)

Kein Entscheid über eine Fassung, sondern die Lesepflicht des Owners. Der erste
Teil, der Katalog aus `fr.json` und `fr.js`, ist in Plan 11-05 abgenommen. Der
zweite Teil sind die Texte, die mit dem Release nach außen gehen:

- die beiden französischen `<summary>` oben, "Recherche plein texte, OCR et
  recherche sémantique sans configuration" und "Service de recherche pour
  Findling : extraction de texte, OCR et index"
- die beiden französischen `<description>` oben, vollständig, mit dem Satz zum
  MCP Connector und dem Absatz "Confidentialité"
- die französische RAM-Zeile aus Teil 2, in der gewählten Fassung
- `README.fr.md` vollständig, besonders "Prérequis", "Confidentialité" und
  "Mesures"
- die französische Grundlast-Zeile aus Teil 3, und bei "dreisprachig" auch der
  französische Messsatz

Die Wortwahl-Entscheide aus `docs/l10n-french.md` gelten unverändert: "le
service" für das Backend, "passage" für einen Lauf, "Mo" statt "MB",
"reconnaissance optique" für OCR.

## Was in den Entwürfen der Store-Texte bewusst nicht steht (D-08)

Dieser Abschnitt nennt die ausgeschlossenen Gegenstände beim Namen, weil eine
Regel, die ihren Gegenstand verschweigt, von niemandem nachgeprüft werden kann.
Er ist selbst kein Store-Text.

- **Die zehn Sprachfälle mit ihrem Ergebnis 6 von 10.** Erstmessung ohne
  v1.0-Entsprechung, und die Nachmessung vom 10.09. zeigt, dass der Messaufbau
  und nicht die Sprachverarbeitung die vier roten Fälle erzeugt hat. Gehört in
  den Bericht, Abschnitt d der Kernaussage, und in `docs/performance.md`.
- **Die Laufzeit von 26 h 37 min.** Sie ist eine Untergrenze, weil beim Anstoß
  schon 1.653 Dateien im Index lagen. Gehört in den Bericht.
- **Vier von fünf Laststufen regressiv.** Die Zusage steht auf Stufe 8 und hält,
  aber ihre Reserve fällt von 585,0 auf 374,5 ms. Gehört in den Bericht und in
  `docs/performance.md`.
- **`memory.events max` 21.939 und der Kaltstart über der Aufrufdecke.** Zwei
  Zahlen, die ohne ihre Methode das Gegenteil dessen sagen, was sie bedeuten.
  Gehören in den Bericht.

## Gegengelesen: die RAM-Budget-Tabelle in CLAUDE.md

Die Zeile "Tokenizer und Splitter, 544 MB" läuft **nicht** gegen die neue
Grundlastaussage. Dieselbe Zeile führt im Ruhezustand den Wert "0 bei faulem
Bau" und sagt im Klartext, dass die 544 MB erst beim ersten Chunkerlauf
anfallen, faul gebaut seit Plan 07-03. Die 103,2 MB sind die Grundlast im
Leerlauf mit nie geladenem Modell, also genau der Zustand, den die Spalte
Ruhezustand beschreibt. Kein Widerspruch, keine Änderung nötig. `CLAUDE.md`
wird in diesem Plan nicht angefasst: die Datei trägt GSD-verwaltete
Abschnittsmarken.

## Die Abnahme

Textabnahme: 2026-09-11, Fassung B, Messsatz dreisprachig, FR-Gate Teil 2 von 2 abgenommen (D-06, D-07, D-08)

Einreichung freigegeben: 2026-09-11 (D-10)

Eingereicht: 2026-09-11, Tag v1.1.0 auf 891bc6d, Release-Lauf 34573687101,
Submission-Lauf 34573857157, findling HTTP 201 und findling_backend HTTP 201

Das Release trägt genau vier Assets: findling.tar.gz (282.432 Byte),
findling.tar.gz.sig, findling_backend.tar.gz (28.524 Byte) und
findling_backend.tar.gz.sig. Eingereicht wurden genau diese, weil
store-submit.yml die Release-URL übergibt und nichts ein zweites Mal baut.

Vor der Einreichung geprüft und nicht angenommen (Pitfall 10): der
Manifestindex ghcr.io/street1983nk/findling_backend:1.1.0 liegt als
application/vnd.oci.image.index.v1+json mit linux/amd64
(sha256:a2b9aef78e321d582983…) und linux/arm64 (sha256:ae58d93005dc18849c3b…)
in der Registry, anonym abgefragt.

Gegenprobe von außen: apps.nextcloud.com/apps/findling und
apps.nextcloud.com/apps/findling_backend nennen beide 1.1.0. Die große
apps.json unter ?version=34.0.0 führte kurz nach der Einreichung noch bis
1.0.3, das ist ihr Cache und kein Befund; sie wird nicht im Minutentakt
abgefragt.

Freigegeben auf dem Release-Commit 891bc6d, mit allen sechs Workflows grün
(PHP 34571130182, Python 34571130132, Multi-arch 34571130185, Integration
34571130129, Resilience 34571130176, HaRP 34571130221 mit allen vier Ästen).
Das Auditfrontmatter weist `critical: 0` und `high: 0` aus, offen sind nur
LOW-Befunde. Zwei Punkte gehen ausdrücklich mit und sind keine Blocker:
DI-10-02, weil die Vorprüfung an demselben Antwortdeckel hängt wie die Fälle,
über die sie urteilen soll, und DI-11-06, das Fenster ohne Drift-Urteil
zwischen einem Update und dem ersten Blick auf die Einstellungsseite, mit
Zieladresse v1.2. Der stable35-RE-CHECK vom 16.09.2026 bleibt eigener
Merkposten; die Einreichung wartet nach D-10 nicht darauf.

Der Owner hat beide Fassungen im Wortlaut gesehen und Fassung B gewählt, den
Messsatz dreisprachig entschieden und die französischen Texte ohne Änderung
abgenommen. Zur Prozentzahl kam kein Einwand, es bleibt bei 85,1 Prozent, und
die 52.111 bleibt die Zahl des Laufs, den der Satz beschreibt. Was damit nach
außen geht, steht oben in den sechs Texten und in den drei READMEs; danach wird
es nicht mehr angefasst, weil der Store-Text unveränderlich mit dem Release
reist.

## Nachtrag vom 11.09.2026: der Angebot-anfordern-Kontakt

Nachtrag zu den Texten oben, auf ausdrücklichen Owner-Auftrag vom 11.09.2026
und damit die einzige Änderung an der abgenommenen Fassung B, die nach der
Abnahme noch vorgenommen wurde. Der Auftrag lautete wörtlich, einen
Angebot-anfordern-Link einzubauen; entschieden wurden der Ort (Store-Text,
die drei READMEs und das Store-Flag) und die Adresse admin@infranode.dev.

Je eine Zeile steht als eigener Absatz am Ende aller sechs Store-Texte:

- EN: Enterprise support and paid add-ons: request a quote at admin@infranode.dev
- DE: Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev
- FR: Support entreprise et modules payants : demande de devis à admin@infranode.dev

Die Adresse steht als Text und nicht als mailto-Verweis: der Store rendert
zwar Markdown-Links, und ob er einen mailto-Verweis genauso sauber ausgibt,
ist nicht geprüft. Eine Adresse, die als Text dasteht, funktioniert in jedem
Fall.

Dazu ein kurzer Abschnitt in allen drei READMEs, der sagt, was geplant ist,
und nicht, was es schon gibt: Findling bleibt AGPL, die bezahlten
Zusatzmodule und der Support mit zugesagten Reaktionszeiten sind geplant und
noch nicht verfügbar. Ein Fake-Door-Text, der etwas als gebaut ausgäbe, wäre
in dem Moment gelogen, in dem jemand darauf antwortet.

Der Messsatz ist unberührt: die neue Zeile nennt keine Messgröße, und die
85,1 Prozent und die 52.111 stehen unverändert dort, wo sie standen.

Nicht im Repository zu erledigen und deshalb hier nur benannt: das Flag
"Enterprise support" im Store-Konto, für beide Findling-Apps, nach der
Einreichung zu setzen, nach dem Muster des Connectors vom 24.08.2026.

**Nachgetragen am 21.09.2026, Plan 16-11:** Diese drei Zeilen standen seit dem
11.09.2026 in beiden `info.xml`, aber nicht in den sechs Texten oben, sondern
nur hier. Die Vorlage war damit an einer Stelle kürzer als das, was
ausgeliefert ist, und wer die sechs Texte wörtlich übernommen hätte, hätte die
Zeile gelöscht. Auf Owner-Entscheid vom 21.09.2026 steht sie jetzt als eigener
Absatz am Ende aller sechs Texte oben, im Wortlaut dieses Nachtrags und ohne
eine Silbe Änderung. Der Text der Apps ändert sich dadurch nicht, die Vorlage
wird nur deckungsgleich mit dem, was seit 1.1.0 im Store steht.

Abnahme des Nachtrags: 2026-09-11, Wortlaute EN, DE und FR wie eingebaut,
Commit fb371a0 (D-07)

Der Owner hat die drei Store-Zeilen und die drei README-Abschnitte im
Wortlaut gesehen und ohne Änderung abgenommen. Damit ist auch der
französische Teil dieses Nachtrags abgenommen, in derselben Disziplin wie
das FR-Gate vom selben Tag: keine französische Zeile geht ungesehen nach
außen.

---

# Entwurf v1.2.0, Plan 16-11, dem Owner vorgelegt am 21.09.2026

Dieser Abschnitt ist der Textentwurf, den der Owner vor der Einreichung von
1.2.0 sieht. Er steht hier und nicht in einer Planungsdatei, weil der
Store-Text mit dem Release reist und danach nicht mehr editierbar ist: die
Fassungen, die zur Wahl standen, gehören neben den Text, der gewonnen hat.
Geändert wird an vier Stellen, und jede hat ihre eigene Regel.

## Teil 1: die RAM-Zeile der sechs Store-Texte

Eine Zeile, sechsmal, dreisprachig. Alles andere der sechs Texte bleibt Wort
für Wort, wie es oben steht.

Alt (1.1.0, abgenommen am 11.09.2026):

> Englisch: RAM: 4 GB is enough, 103.2 MB idle, under a hard 2 GB limit (measured)
>
> Deutsch: RAM: 4 GB genügen, 103,2 MB im Leerlauf, unter einer harten 2-GB-Grenze (gemessen)
>
> Französisch: RAM : 4 Go suffisent, 103,2 Mo au repos, sous une limite stricte de 2 Go (mesuré)

Neu (Entwurf 1.2.0, oben schon eingesetzt):

> Englisch: RAM: 4 GB is enough, 731.9 MB resident after an index run, under a hard 2 GB limit (measured)
>
> Deutsch: RAM: 4 GB genügen, 731,9 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
>
> Französisch: RAM : 4 Go suffisent, 731,9 Mo résidents après une indexation, sous une limite stricte de 2 Go (mesuré)

Das Wort "im Leerlauf" ist bewusst verschwunden und durch die Messgröße
ersetzt: "resident nach einem Indexlauf" sind vier Wörter, und sie sagen
genau, wann die Zahl gilt. Ein Selfhoster liest daran ab, dass dies nicht die
Zahl direkt nach dem Start ist, sondern die des Containers, der einmal
gearbeitet hat. Die Spitze während des Laufs ist eine dritte Größe und steht
nicht im Store-Text, sondern im Messsatz der READMEs.

## Teil 2: die Sprachzeile der drei Texte der ersten Hälfte

Das Abbild trägt seit Plan 16-10 neun OCR-Sprachen statt drei, und der
Standard bleibt bei dreien. Ein Text, der neun Sprachen so nennt, als wären
sie alle eingeschaltet, wäre falsch; einer, der weiter drei nennt, verschweigt
sechs. Der Entwurf nennt beides in einer Zeile.

Alt:

> Englisch: OCR for scanned PDFs and images: German, English, French
>
> Deutsch: Texterkennung für gescannte PDFs und Bilder: Deutsch, Englisch, Französisch
>
> Französisch: Reconnaissance optique pour les PDF numérisés et les images : allemand, anglais, français

Neu (Entwurf 1.2.0, oben schon eingesetzt):

> Englisch: OCR for scanned PDFs and images: nine languages available, German, English and French are the default
>
> Deutsch: Texterkennung für gescannte PDFs und Bilder: neun Sprachen verfügbar, voreingestellt sind Deutsch, Englisch und Französisch
>
> Französisch: Reconnaissance optique pour les PDF numérisés et les images : neuf langues disponibles, allemand, anglais et français par défaut

Die neun Namen stehen absichtlich nicht im Store-Text: neun Sprachnamen in
einer Zeile sind länger als der Block, in dem sie stehen, und die Owner-Regel
vom 07.09.2026 will eine Faktenliste. Die Zahl neun ist keine Messzahl,
sondern ein Bestand, und bricht die Ein-Zahl-Regel deshalb nicht. Wer die
Namen sucht, findet sie in den READMEs und in der Beschreibung der Einstellung
`FINDLING_OCR_LANGUAGES`, beide unten im Wortlaut.

## Teil 3: die Grundlast-Zeile der drei READMEs

Heute steht dort ein Vergleich: 691,8 MB in v1.0 auf 103,2 MB in v1.1, minus
85,1 Prozent. **Dieser Vergleich trägt die neue Zahl nicht.** 103,2 MB war die
Grundlast im Leerlauf, 731,9 MB ist der residente Stand nach einem Indexlauf
mit entladenem Modell. Eine Prozentzahl zwischen zwei verschiedenen
Messgrößen wäre falsch, und zwar in die günstige Richtung falsch: sie
verspräche einen Rückgang, der so nie gemessen wurde. Die Zeile wird deshalb
nicht nachgerechnet, sondern ersetzt.

Alt:

> Englisch: Idle base load fell from 691.8 MB in v1.0 to 103.2 MB in v1.1, minus 85.1 per cent (measured 2026-09-10, method and raw data in docs/performance.md).
>
> Deutsch: Die Grundlast im Leerlauf ist von 691,8 MB in v1.0 auf 103,2 MB in v1.1 gefallen, minus 85,1 Prozent (gemessen am 10.09.2026, Methode und Rohdaten in docs/performance.md).
>
> Französisch: La charge de base au repos est passée de 691,8 Mo en v1.0 à 103,2 Mo en v1.1, moins 85,1 pour cent (mesuré le 10.09.2026, méthode et données brutes dans docs/performance.md).

Neu (Entwurf 1.2.0, Übernahme in Plan 16-12):

> Englisch: After an index run, with the model unloaded, the container sits at 731.9 MB of resident memory (measured 2026-09-21 on an m7g.large arm64 box against the shipped v1.2 image, method and raw data in docs/performance.md).
>
> Deutsch: Nach einem Indexlauf steht der Container mit entladenem Modell bei 731,9 MB residentem Speicher (gemessen am 21.09.2026 auf einer m7g.large mit arm64 gegen das ausgelieferte v1.2-Abbild, Methode und Rohdaten in docs/performance.md).
>
> Französisch: Après une indexation, le modèle déchargé, le conteneur reste à 731,9 Mo de mémoire résidente (mesuré le 21.09.2026 sur une machine m7g.large arm64 avec l'image v1.2 livrée, méthode et données brutes dans docs/performance.md).

Jede Sprache schreibt ihre Zahlen so, wie sie Zahlen schreibt: 731.9 MB
englisch, 731,9 MB deutsch, 731,9 Mo französisch. Der alte Vergleich
verschwindet nicht aus der Welt: er bleibt in `docs/performance.md` gültig für
die Bedingungen, unter denen er entstand (Messung vom 10.09.2026, Grundlast im
Leerlauf, Modell nie geladen), und er steht unten im Änderungsprotokoll mit
Datum.

## Teil 4: der Spitzen-Satz bleibt unverändert

Der Messsatz der drei READMEs nennt 52.111 Dokumente und 1.764 MB aus der
v1.1-Anfahrt. Er wird **nicht** angefasst, und das ist eine Entscheidung und
kein Vergessen: der v1.2-Lauf hat die Spitze eines Volllaufs nicht neu
gemessen. Wer die Dokumentzahl auf die 52.137 der v1.2-Box nachzöge, ohne die
Spitze mitzunehmen, mischte zwei Läufe in einem Satz, und der Satz behauptete
danach eine Messung, die es nicht gibt. Der nächste Leser, der an dieser
Stelle ansetzt, findet hier den Grund, warum die Zahl aussieht, als sei sie
stehen geblieben. `MEASURED_SENTENCE`, `MEASURED_SENTENCE_DE` und
`MEASURED_SENTENCE_FR` in `backend/tests/test_store_metadata.py` bleiben damit
ebenfalls unberührt.

## Teil 5: die Fundstellen, Stelle für Stelle

Zwei Listen, weil zwei verschiedene Angaben wandern. Maßgeblich ist der
Wortlaut und nicht die Stelle.

**Die Messzahl 731,9 MB, neun Stellen (Entscheid E1):**

| Datei | Sprache | Was dort steht |
|---|---|---|
| `php/appinfo/info.xml` | EN | die RAM-Zeile des Blocks Requirements |
| `php/appinfo/info.xml` | DE | die RAM-Zeile des Blocks Anforderungen |
| `php/appinfo/info.xml` | FR | die RAM-Zeile des Blocks Prérequis |
| `backend/appinfo/info.xml` | EN | dieselbe Zeile, zweite Hälfte |
| `backend/appinfo/info.xml` | DE | dieselbe Zeile, zweite Hälfte |
| `backend/appinfo/info.xml` | FR | dieselbe Zeile, zweite Hälfte |
| `README.en.md` | EN | die Grundlast-Zeile im Block Requirements |
| `README.md` | DE | die Grundlast-Zeile im Block Anforderungen |
| `README.fr.md` | FR | die Grundlast-Zeile im Block Prérequis |

**Die Sprachangabe, elf Stellen (aus Plan 16-10):** die drei Sprachzeilen aus
Teil 2 in `php/appinfo/info.xml`, dieselben drei in dieser Datei, die drei
Zeilen der READMEs und zwei Stellen in `backend/appinfo/info.xml`, nämlich der
Kommentar über dem OCR-Block und die Beschreibung von
`FINDLING_OCR_LANGUAGES`. Die Store-Texte der zweiten Hälfte zählen die
Sprachen nicht auf und bleiben unberührt.

Der Wortlaut der READMEs, dort dürfen die Namen stehen:

> Englisch: OCR for scanned PDFs and images: nine languages available (German, English, French, Spanish, Italian, Dutch, Portuguese, Danish, Estonian), German, English and French switched on by default
>
> Deutsch: Texterkennung für gescannte PDFs und Bilder: neun Sprachen verfügbar (Deutsch, Englisch, Französisch, Spanisch, Italienisch, Niederländisch, Portugiesisch, Dänisch, Estnisch), voreingestellt sind Deutsch, Englisch und Französisch
>
> Französisch: Reconnaissance optique pour les PDF numérisés et les images : neuf langues disponibles (allemand, anglais, français, espagnol, italien, néerlandais, portugais, danois, estonien), allemand, anglais et français activés par défaut

Der Wortlaut der zwei Stellen in `backend/appinfo/info.xml`, englisch, weil
die Datei dort englisch ist:

> Kommentar über dem OCR-Block: the engine and nine language models are inside the image, and German, English and French are switched on.
>
> Beschreibung von `FINDLING_OCR_LANGUAGES`, der eine Satz mit der Aufzählung: Only the languages this image carries are accepted, which today are deu (German), eng (English), fra (French), spa (Spanish), ita (Italian), nld (Dutch), por (Portuguese), dan (Danish) and est (Estonian); anything else is ignored with a warning in the log and never reaches the engine.

Der Rest beider Beschreibungen bleibt unverändert, besonders der Satz, dass
die Reihenfolge zählt und die erste Sprache am schwersten wiegt.

## Teil 6: die Store-Bilder, offene Frage Q-6 der Recherche

Kein Textentscheid, aber derselbe Termin. Die drei Bilder in `store/media/`
stammen vom 07.09.2026, also aus der 1.0.0-Zeit. Seitdem hat das Produkt drei
sichtbare Änderungen bekommen: die eigene Ergebnisseite mit Navigationseintrag
(Phase 9), die Filter- und Sortierzeile (Phase 13) und den sechsten
Engine-Zustand auf der Verwaltungsseite (Phase 14). `screenshot-admin.png`
zeigt die Verwaltungsseite in ihrem damaligen Stand.

- **a) Bilder bleiben.** Kein Aufwand, aber die Verwaltungsseite im Store
  zeigt einen Stand, den 1.2 so nicht mehr hat.
- **b) Bilder werden erneuert.** Eigener Plan in Welle 6, vor der Abgabe:
  Wegwerf-Aufbau, eigens erzeugter Bestand, Playwright, Sichtprobe.

Unabhängig von der Wahl wird die Größentabelle in `store/media/README.md`
nachgezogen: sie nennt bis heute die Größen der abgelösten Dateien, und diese
Wiedervorlage steht seit dem 07.09.2026 offen.

## Die Abnahme

Textabnahme 1.2.0: **2026-09-21, abgenommen im vorgelegten Wortlaut.** Der
Owner hat die sechs Texte und die drei README-Zeilen in allen drei Sprachen
gesehen und ohne Änderung abgenommen, einschliesslich der neuen Messzahl, der
weggefallenen Prozentzahl und der Sprachzeile "neun verfügbar, drei
voreingestellt".

Zu Q-6, im Wortlaut: **"Bilder bleiben."** Es gibt keinen Plan für neue
Store-Bilder in dieser Phase. Die Größentabelle in `store/media/README.md` wird
unabhängig davon in Plan 16-12 nachgezogen, weil sie die Größen der abgelösten
Dateien nennt.

Zur Enterprise-Zeile, im Wortlaut: **in die sechs Texte aufnehmen**, damit die
Vorlage deckungsgleich mit beiden `info.xml` ist. Eingearbeitet am 21.09.2026,
Wortlaut unverändert, siehe den Nachtrag weiter unten.

Die Übernahme in beide `info.xml` und die drei READMEs ist Plan 16-12 und
findet nach dieser Abnahme statt.

---

# Entwurf v1.3.0, Plan 23-03, dem Owner vorgelegt am 27.09.2026

Dieser Abschnitt ist der Textentwurf, den der Owner vor der Einreichung von
1.3.0 sieht. Die sechs Texte oben tragen bis zur Übernahme weiter die Fassung
1.2.0, und beide `info.xml` und die drei READMEs ebenso; die wörtliche
Übernahme ist Plan 23-07 und findet erst nach der Abnahme statt. Wer in diesem
Fenster einen Unterschied zwischen diesem Abschnitt und einer `info.xml`
findet, hat den erwarteten Zwischenstand vor sich und keine Drift.

Gesperrt und hier nur umgesetzt sind vier Owner-Entscheide der Phase 23: D-05
(Changelog-Zeile mit Dank an budachst, Store-Text frei von #14), D-06 (vier
Grenzen als Kurzliste im Store-Text und wortgleich in der Doku), D-09 (die eine
Messzahl ist 730,2 MB) und D-11 (eine Faktenzeile zu den Indexsprachen direkt
vor der Grenzliste). Geändert wird in den sechs Texten an genau drei Stellen:
eine neue Zeile, ein neuer Block, eine getauschte Zahl. Alles andere bleibt
Wort für Wort, wie es oben steht.

## Teil 1: die Sprachzeile (D-11)

Eine Zeile je Text, als letzter Spiegelstrich des ersten Blocks ("What Findling
does:", "What Findling Backend is:" und ihre Gegenstücke), damit sie
unmittelbar vor dem neuen Grenzblock steht. Keine Zahl, keine Kürzel. Die
Zeile nennt den Werkzustand (Deutsch und Englisch voreingestellt) und die vier
zuschaltbaren Sprachen, so wie die OCR-Zeile seit 1.2.0 "verfügbar" und
"voreingestellt" trennt.

> Englisch: Search languages: German and English by default, Spanish, Italian, Dutch and Portuguese available
>
> Deutsch: Suchsprachen: Deutsch und Englisch voreingestellt, Spanisch, Italienisch, Niederländisch und Portugiesisch verfügbar
>
> Französisch: Langues de recherche : allemand et anglais par défaut, espagnol, italien, néerlandais et portugais disponibles

Die Suchsprachen und die OCR-Sprachen sind zwei Einstellungen
(`FINDLING_LANGUAGES` und `FINDLING_OCR_LANGUAGES`, siehe
`docs/language-analyzers.md`). Die erste Hälfte trägt deshalb beide Zeilen
nebeneinander: die OCR-Zeile sagt, welche Scans gelesen werden, die Sprachzeile,
in welchen Sprachen der Text danach durchsucht wird. Französisch steht in der
OCR-Zeile und nicht in der Sprachzeile, und genau diesen Unterschied erklärt
der vierte Grenzpunkt.

## Teil 2: die Known limitations (D-06)

Ein eigener Block im Listenstil der Beschreibung, direkt nach dem ersten Block
und vor dem Satz zum MCP Connector. Genau vier Spiegelstriche in dieser
Reihenfolge, ohne MB-Angabe, ohne Backticks, ohne Tabellen.

> Englisch:
>
> Known limitations:
> - Spanish: año and ano are treated as the same word
> - Portuguese: spellings before and after the spelling reform are not unified
> - Compound words are split for German and Dutch only
> - French has no full text analysis chain for document text
>
> Deutsch:
>
> Bekannte Grenzen:
> - Spanisch: año und ano gelten als dasselbe Wort
> - Portugiesisch: Schreibweisen vor und nach der Rechtschreibreform werden nicht vereinheitlicht
> - Zusammengesetzte Wörter werden nur für Deutsch und Niederländisch zerlegt
> - Französisch hat keine eigene Analysekette für den Dokumenttext
>
> Französisch:
>
> Limites connues :
> - Espagnol : año et ano sont traités comme le même mot
> - Portugais : les graphies d'avant et d'après la réforme orthographique ne sont pas unifiées
> - Les mots composés ne sont découpés que pour l'allemand et le néerlandais
> - Le français n'a pas de chaîne d'analyse plein texte pour le contenu des documents

Die Herkunft je Punkt, damit keiner behauptet ist: (1)
`docs/language-analyzers.md`, Absatz "`año` equals `ano`, a bought recall";
(2) derselbe Text, "No Portuguese orthographic unification"; (3) "Compounds are
German and Dutch" und `docs/dutch-analyzer.md`; (4) der Absatz über die zwei
Einstellungen am Anfang derselben Datei, der sagt, dass Französisch in diesem
Bau keine Kette hat. Die englische Liste steht zeichengleich in
`docs/language-analyzers.md` unter "Known limitations (short list, HART-05)",
damit das Gate aus Plan 23-07 beide Stellen vergleichen kann.

Die französische Typografie folgt den bestehenden FR-Texten: Leerzeichen vor
dem Doppelpunkt, wie in "Ce que Findling sait faire :" und "Prérequis :".

## Teil 3: die Messzahl (D-09)

731,9 MB wird an jeder Fundstelle zu 730,2 MB: englisch 730.2 MB, deutsch
730,2 MB, französisch 730,2 Mo. Die Messgröße bleibt dieselbe wie in 1.2.0,
nur das gemessene Abbild ist ein anderes: Marke C1 der v1.3-Anfahrt vom
26.09.2026, residenter Stand nach einem Einbettungszyklus und Ruhezeit mit
entladenem Modell, gerechnet über `anon` aus `memory.stat`, AWS `m7g.large`
mit nativem arm64 (`docs/performance.md`, Abschnitt "Die v1.3-Anfahrt vom
26.09.2026", Nachtrag "der Bodensatz im zweiten Zyklus", Rohdatei
`docs/measurements/2026-09-v13-messung/rohdaten/94c-bodensatz-zyklen.txt`).

Die RAM-Zeile der sechs Texte, alt und neu:

> Alt, Englisch: RAM: 4 GB is enough, 731.9 MB resident after an index run, under a hard 2 GB limit (measured)
>
> Neu, Englisch: RAM: 4 GB is enough, 730.2 MB resident after an index run, under a hard 2 GB limit (measured)
>
> Alt, Deutsch: RAM: 4 GB genügen, 731,9 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
>
> Neu, Deutsch: RAM: 4 GB genügen, 730,2 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
>
> Alt, Französisch: RAM : 4 Go suffisent, 731,9 Mo résidents après une indexation, sous une limite stricte de 2 Go (mesuré)
>
> Neu, Französisch: RAM : 4 Go suffisent, 730,2 Mo résidents après une indexation, sous une limite stricte de 2 Go (mesuré)

Die Zeile der drei READMEs, alt und neu. Mit der Zahl wandern das Datum und
das Abbild; das Wort "ausgelieferte" fällt weg, weil das gemessene v1.3-Abbild
das Abbild der Anfahrt ist und nicht das Release-Abbild 1.3.0:

> Alt, Englisch: After an index run, with the model unloaded, the container sits at 731.9 MB of resident memory (measured 2026-09-21 on an m7g.large arm64 box against the shipped v1.2 image, method and raw data in docs/performance.md).
>
> Neu, Englisch: After an index run, with the model unloaded, the container sits at 730.2 MB of resident memory (measured 2026-09-26 on an m7g.large arm64 box against the v1.3 image, method and raw data in docs/performance.md).
>
> Alt, Deutsch: Nach einem Indexlauf steht der Container mit entladenem Modell bei 731,9 MB residentem Speicher (gemessen am 21.09.2026 auf einer m7g.large mit arm64 gegen das ausgelieferte v1.2-Abbild, Methode und Rohdaten in docs/performance.md).
>
> Neu, Deutsch: Nach einem Indexlauf steht der Container mit entladenem Modell bei 730,2 MB residentem Speicher (gemessen am 26.09.2026 auf einer m7g.large mit arm64 gegen das v1.3-Abbild, Methode und Rohdaten in docs/performance.md).
>
> Alt, Französisch: Après une indexation, le modèle déchargé, le conteneur reste à 731,9 Mo de mémoire résidente (mesuré le 21.09.2026 sur une machine m7g.large arm64 avec l'image v1.2 livrée, méthode et données brutes dans docs/performance.md).
>
> Neu, Französisch: Après une indexation, le modèle déchargé, le conteneur reste à 730,2 Mo de mémoire résidente (mesuré le 26.09.2026 sur une machine m7g.large arm64 avec l'image v1.3, méthode et données brutes dans docs/performance.md).

**Die Fundstellen, Stelle für Stelle, neun Stellen:**

| Datei | Sprache | Was dort steht |
|---|---|---|
| `php/appinfo/info.xml` | EN | die RAM-Zeile des Blocks Requirements |
| `php/appinfo/info.xml` | DE | die RAM-Zeile des Blocks Anforderungen |
| `php/appinfo/info.xml` | FR | die RAM-Zeile des Blocks Prérequis |
| `backend/appinfo/info.xml` | EN | dieselbe Zeile, zweite Hälfte |
| `backend/appinfo/info.xml` | DE | dieselbe Zeile, zweite Hälfte |
| `backend/appinfo/info.xml` | FR | dieselbe Zeile, zweite Hälfte |
| `README.en.md` | EN | die Zeile nach dem Messsatz im Block Requirements |
| `README.md` | DE | die Zeile nach dem Messsatz im Block Anforderungen |
| `README.fr.md` | FR | die Zeile nach dem Messsatz im Block Prérequis |

Dazu die Vorlage selbst, die sechs Texte oben in dieser Datei, und
`RESIDENT_FIGURE` in `backend/tests/test_store_metadata.py`, das die Zahl
mechanisch festhält; beide wechseln in Plan 23-07 mit.

Wenn ROADMAP und D-09 von "drei Stellen" sprechen, sind die drei
Artefaktgruppen gemeint: der README-Satz, die PHP-Hälfte und die
Backend-Hälfte. Jede einzelne Fundstelle in jeder der drei Gruppen wechselt,
also alle neun der Tabelle, und keine bleibt auf 731,9 MB stehen.

Der Messsatz der READMEs (52.111 Dokumente, 1.764 MB Spitze) bleibt
unverändert, aus demselben Grund wie in 1.2.0 (Teil 4 des Entwurfs v1.2.0):
auch die v1.3-Anfahrt hat die Spitze eines Volllaufs nicht neu gemessen.

## Teil 4: die sechs Texte 1.3.0 im Wortlaut

Vollständig, damit sie nebeneinander gelesen werden können. `<name>` und
`<summary>` beider Hälften bleiben unverändert und stehen deshalb nicht noch
einmal hier.

### App 1: `findling`, `<description>` (Englisch, ohne `lang`-Attribut)

What Findling does:
- Full text search in the normal Nextcloud search bar
- OCR for scanned PDFs and images: nine languages available, German, English and French are the default
- Semantic search: finds documents through paraphrases
- Every result is permission-checked by Nextcloud
- No configuration: the first index run starts on its own
- Privacy: everything runs locally, no telemetry, nothing leaves your server
- Search languages: German and English by default, Spanish, Italian, Dutch and Portuguese available

Known limitations:
- Spanish: año and ano are treated as the same word
- Portuguese: spellings before and after the spelling reform are not unified
- Compound words are split for German and Dutch only
- French has no full text analysis chain for document text

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Supported file types:
- PDF (scanned too), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images through OCR: JPEG, PNG, TIFF, WebP

Requirements:
- Nextcloud 33 to 35, apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB is enough, 730.2 MB resident after an index run, under a hard 2 GB limit (measured)
- CPU: 2 cores are enough, amd64 and arm64

Enterprise support and paid add-ons: request a quote at admin@infranode.dev

### App 1: `findling`, `<description lang="de">`

Was Findling kann:
- Volltextsuche über die normale Nextcloud-Suchleiste
- Texterkennung für gescannte PDFs und Bilder: neun Sprachen verfügbar, voreingestellt sind Deutsch, Englisch und Französisch
- Semantische Suche: findet Dokumente auch über Umschreibungen
- Jeder Treffer wird von Nextcloud rechtegeprüft
- Keine Konfiguration: der erste Indexlauf startet von selbst
- Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server
- Suchsprachen: Deutsch und Englisch voreingestellt, Spanisch, Italienisch, Niederländisch und Portugiesisch verfügbar

Bekannte Grenzen:
- Spanisch: año und ano gelten als dasselbe Wort
- Portugiesisch: Schreibweisen vor und nach der Rechtschreibreform werden nicht vereinheitlicht
- Zusammengesetzte Wörter werden nur für Deutsch und Niederländisch zerlegt
- Französisch hat keine eigene Analysekette für den Dokumenttext

Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server.

Unterstützte Dateitypen:
- PDF (auch gescannt), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Bilder per Texterkennung: JPEG, PNG, TIFF, WebP

Anforderungen:
- Nextcloud 33 bis 35, Apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB genügen, 730,2 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
- CPU: 2 Kerne genügen, amd64 und arm64

Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev

### App 1: `findling`, `<description lang="fr">`

Ce que Findling sait faire :
- Recherche plein texte dans la barre de recherche normale de Nextcloud
- Reconnaissance optique pour les PDF numérisés et les images : neuf langues disponibles, allemand, anglais et français par défaut
- Recherche sémantique : trouve les documents par des périphrases
- Chaque résultat est vérifié par Nextcloud selon vos droits
- Aucune configuration : la première indexation démarre d'elle-même
- Confidentialité : tout fonctionne localement, aucune télémétrie, rien ne quitte votre serveur
- Langues de recherche : allemand et anglais par défaut, espagnol, italien, néerlandais et portugais disponibles

Limites connues :
- Espagnol : año et ano sont traités comme le même mot
- Portugais : les graphies d'avant et d'après la réforme orthographique ne sont pas unifiées
- Les mots composés ne sont découpés que pour l'allemand et le néerlandais
- Le français n'a pas de chaîne d'analyse plein texte pour le contenu des documents

Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur.

Types de fichiers pris en charge :
- PDF (numérisés aussi), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images par reconnaissance optique : JPEG, PNG, TIFF, WebP

Prérequis :
- Nextcloud 33 à 35, applications : AppAPI, Findling Backend (External Apps), Findling
- RAM : 4 Go suffisent, 730,2 Mo résidents après une indexation, sous une limite stricte de 2 Go (mesuré)
- CPU : 2 cœurs suffisent, amd64 et arm64

Support entreprise et modules payants : demande de devis à admin@infranode.dev

### App 2: `findling_backend`, `<description>` (Englisch, ohne `lang`-Attribut)

What Findling Backend is:
- The External App behind the Findling search app: text extraction, OCR and the search index
- Runs entirely inside your own instance and does nothing without the Findling app
- Never modifies your files
- Privacy: everything runs locally, no telemetry, nothing leaves your server
- Search languages: German and English by default, Spanish, Italian, Dutch and Portuguese available

Known limitations:
- Spanish: año and ano are treated as the same word
- Portuguese: spellings before and after the spelling reform are not unified
- Compound words are split for German and Dutch only
- French has no full text analysis chain for document text

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Supported file types:
- PDF (scanned too), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images through OCR: JPEG, PNG, TIFF, WebP

Requirements:
- Nextcloud 33 to 35, apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB is enough, 730.2 MB resident after an index run, under a hard 2 GB limit (measured)
- CPU: 2 cores are enough, amd64 and arm64

Enterprise support and paid add-ons: request a quote at admin@infranode.dev

### App 2: `findling_backend`, `<description lang="de">`

Was Findling Backend ist:
- Die External App hinter der Such-App Findling: Textauszug, Texterkennung und der Suchindex
- Läuft komplett in Ihrer eigenen Instanz und tut ohne die App Findling nichts
- Verändert nie Ihre Dateien
- Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server
- Suchsprachen: Deutsch und Englisch voreingestellt, Spanisch, Italienisch, Niederländisch und Portugiesisch verfügbar

Bekannte Grenzen:
- Spanisch: año und ano gelten als dasselbe Wort
- Portugiesisch: Schreibweisen vor und nach der Rechtschreibreform werden nicht vereinheitlicht
- Zusammengesetzte Wörter werden nur für Deutsch und Niederländisch zerlegt
- Französisch hat keine eigene Analysekette für den Dokumenttext

Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server.

Unterstützte Dateitypen:
- PDF (auch gescannt), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Bilder per Texterkennung: JPEG, PNG, TIFF, WebP

Anforderungen:
- Nextcloud 33 bis 35, Apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB genügen, 730,2 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
- CPU: 2 Kerne genügen, amd64 und arm64

Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev

### App 2: `findling_backend`, `<description lang="fr">`

Ce qu'est Findling Backend :
- L'External App derrière l'application de recherche Findling : extraction de texte, reconnaissance optique et index
- Fonctionne entièrement dans votre propre instance et ne fait rien sans l'application Findling
- Ne modifie jamais vos fichiers
- Confidentialité : tout fonctionne localement, aucune télémétrie, rien ne quitte votre serveur
- Langues de recherche : allemand et anglais par défaut, espagnol, italien, néerlandais et portugais disponibles

Limites connues :
- Espagnol : año et ano sont traités comme le même mot
- Portugais : les graphies d'avant et d'après la réforme orthographique ne sont pas unifiées
- Les mots composés ne sont découpés que pour l'allemand et le néerlandais
- Le français n'a pas de chaîne d'analyse plein texte pour le contenu des documents

Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur.

Types de fichiers pris en charge :
- PDF (numérisés aussi), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images par reconnaissance optique : JPEG, PNG, TIFF, WebP

Prérequis :
- Nextcloud 33 à 35, applications : AppAPI, Findling Backend (External Apps), Findling
- RAM : 4 Go suffisent, 730,2 Mo résidents après une indexation, sous une limite stricte de 2 Go (mesuré)
- CPU : 2 cœurs suffisent, amd64 et arm64

Support entreprise et modules payants : demande de devis à admin@infranode.dev

## Teil 5: der Text der Umgebungsvariable `FINDLING_EMBED_IDLE_RELEASE_SECONDS`

Die Beschreibung steht in `backend/appinfo/info.xml` und reist mit dem Release
wie die Store-Texte. Nach dem Kaltstart-Fix (D-01) gilt für jeden Schalterwert:
die erste Suche nach einem Start oder einer Freigabe antwortet aus dem
Volltext, das Modell wird im Hintergrund geladen, die Semantik greift ab der
nächsten Suche. Der alte Text sagt das nur für die Freigabe und nennt 0
"off", was nach dem Fix nur noch "nie freigeben" heißt. Englisch, weil die
Datei dort englisch ist.

Alt (1.2.0):

> A whole number of seconds, and 0 is the default and means off. Any other value has to lie between 60 and 86400; anything outside that range falls back to the default. When the model has been idle for this long, the container gives up the tokenizer, the splitter and the inference session, and the memory they hold goes back to the machine. The first search afterwards answers from the full text side while the model is warmed up again in the background, so nobody waits for it. A quarter of an hour, so 900, is a reasonable value to start with.

Neu (Entwurf 1.3.0):

> A whole number of seconds, and 0 is the default and means the model is never released. Any other value has to lie between 60 and 86400; anything outside that range falls back to the default. When the model has been idle for this long, the container gives up the tokenizer, the splitter and the inference session, and the memory they hold goes back to the machine. Whatever the value, the first search after a start or a release answers from the full text side while the model is loaded in the background, so nobody waits for it, and the semantic side joins from the next search on. A quarter of an hour, so 900, is a reasonable value to start with.

`<display-name>` ("Release the model after idle seconds") und `<default>` (0)
bleiben unverändert. Der XML-Kommentar über der Variable (die Freigabe sei aus,
weil der Preis der ersten Suche nach einer Freigabe noch nicht gemessen sei)
ist kein Store-Text; ihn zieht der Plan des Kaltstart-Fixes nach, zusammen mit
`docs/admin-page.md`.

## Teil 6: die Changelog-Zeile und die Antwort in Issue #14 (D-05)

Die Changelog-Zeile für die GitHub-Release-Notiz 1.3.0, englisch, eine Zeile:

> Files in team folders (groupfolders) that were wrongly skipped as deleted are now indexed, and the update requeues the affected entries once; thanks to budachst for the report (#14).

Die Antwort in Issue #14, englisch, **nur Entwurf**: gepostet wird erst nach
dem Release (Plan 23-09) und nur mit dem Wort des Owners.

> Findling 1.3.0 contains the fix: files in team folders are no longer skipped as deleted. The update requeues every entry that was marked this way once, so nothing has to be done by hand, and the first scan afterwards takes a little longer. Thanks for the detailed report.

Der Store-Kurztext und die sechs Beschreibungen bleiben frei von #14.

## Teil 7: was bewusst nicht drin steht

Dieser Abschnitt nennt die ausgeschlossenen Gegenstände beim Namen, weil eine
Regel, die ihren Gegenstand verschweigt, von niemandem nachgeprüft werden kann.
Er ist selbst kein Store-Text.

- **Kein Wort zu #14 in den Store-Texten.** Der Fix steht in der
  Changelog-Zeile und in der Antwort im Issue (D-05). Eine Store-Beschreibung
  ist eine Faktenliste über die App und kein Änderungsverlauf.
- **Keine zweite Messzahl.** Weder die C2-Zahl des zweiten Zyklus noch der
  Bodensatz, die Spitze der Abtastreihe oder die Umbauzeit stehen in den
  Texten. Die Grenzliste trägt keine MB-Angabe, und die Sprachzeile nennt keine
  Zahl.
- **Keine Messgeschichte.** Kein Vergleich 731,9 gegen 730,2 MB im Store-Text;
  der Vergleich steht nur im Änderungsprotokoll unten.
- **Nur die vier Grenzen aus D-06.** `docs/language-analyzers.md` führt
  weitere gemessene Grenzen (Auszug ohne Fragment bei einem Treffer allein über
  ein neues Sprachfeld, die Zahlklasse mit akzentuierter Endung, unregelmäßige
  Plurale, fünf Funktionswörter). Sie bleiben in der Doku, weil D-06 die
  Kurzliste auf vier Punkte festlegt.
- **Kein Wort zum Kaltstart-Fix in den Store-Texten.** Er ändert das Verhalten
  und nicht die Faktenliste; er steht im Text der Umgebungsvariable (Teil 5).

## Die Abnahme

Textabnahme 1.3.0: **2026-09-27, im Wortlaut: "Text abgenommen".** Der Owner
hat die sechs Texte, den Text der Umgebungsvariable, die Changelog-Zeile und
den Entwurf der Antwort in Issue #14 gesehen und wie vorgelegt abgenommen.

Zu den drei Fragen des Checkpoints, je im Wortlaut der Auswahl:

- **F1, der vierte Grenzpunkt: "So lassen".** Er bleibt "French has no full
  text analysis chain for document text", in DE und FR wie oben.
- **F2, die Auszug-Grenze in `docs/language-analyzers.md`: "Ankündigung
  anpassen".** Die Grenze "A hit found through a new language field alone
  comes back without an excerpt" bleibt in der Doku und wird nicht mehr für
  den Store-Text angekündigt; die Kurzliste bleibt bei den vier Punkten aus
  D-06. Eingearbeitet am 27.09.2026.
- **F3, das gemessene Abbild: "Ja, reicht".** Die Formulierung "gegen das
  v1.3-Abbild" mit dem Messdatum 26.09.2026 bleibt; eine Nachmessung am
  Release-Abbild 1.3.0 gibt es nicht.

Die Antwort in Issue #14 bleibt ein Entwurf, bis das Release steht; gepostet
wird sie in Plan 23-09 und nur mit dem Wort des Owners. Die Übernahme in beide
`info.xml` und die drei READMEs ist Plan 23-07 und findet nach dieser Abnahme
statt.

Übernommen in Plan 23-07 am 27.09.2026: die sechs Texte aus Teil 4 zeichengleich
in beide `info.xml` und in die sechs Texte oben in dieser Datei, der Text aus
Teil 5 in `backend/appinfo/info.xml`, die README-Zeile aus Teil 3 in alle drei
READMEs. `RESIDENT_FIGURE` in `backend/tests/test_store_metadata.py` steht auf
730.2, und ein Gate hält die vier Grenzen, die Sprachzeile und die englische
Liste in `docs/language-analyzers.md` fest.

---

# Änderungsprotokoll der Messzahl in den Store-Texten

Eine ersetzte Zahl ohne Nachtrag lässt später nicht mehr erkennen, was früher
gemessen wurde und unter welchen Bedingungen es galt. Deshalb steht jede
Ablösung hier mit Datum, Plan und Messgröße, und nicht nur der jeweils letzte
Stand.

| Datum | Plan | Was sich ändert | Abgelöste Zahl und ihre Messgröße | Neue Zahl und ihre Messgröße | Grundlage |
|---|---|---|---|---|---|
| 11.09.2026 | 11-09 | die RAM-Zeile der sechs Store-Texte bekommt erstmals eine Kernzahl | keine Zahl im Text | 103,2 MB, Grundlast im Leerlauf mit nie geladenem Modell, gemessen am 10.09.2026 auf m7g.large, Rohdatei `2026-09-vergleichsmessung-m7g/rohdaten/94-grundlast.txt` | Owner-Entscheid vom 11.09.2026, Fassung B |
| 21.09.2026 | 16-11 | die RAM-Zeile der sechs Store-Texte und die Grundlast-Zeile der drei READMEs | 103,2 MB, Grundlast im Leerlauf mit nie geladenem Modell; bleibt für genau diese Bedingungen gültig und steht weiter in `docs/performance.md` | 731,9 MB, residenter Stand nach einem Indexlauf mit entladenem Modell, gemessen am 21.09.2026 auf m7g.large mit arm64 gegen das ausgelieferte v1.2-Abbild, Rohdatei `2026-09-v12-messung/rohdaten/94b-grundlast-rueckkehr.txt` (Marke C) | Entscheid E1 der Phase 16, gesperrt am 21.09.2026 |
| 27.09.2026 (Entwurf, gilt ab der Übernahme in Plan 23-07) | 23-03 | die RAM-Zeile der sechs Store-Texte und die Zeile nach dem Messsatz der drei READMEs | 731,9 MB, residenter Stand nach einem Indexlauf mit entladenem Modell, gemessen am v1.2-Abbild; bleibt für das v1.2-Abbild gültig und steht weiter in `docs/performance.md` | 730,2 MB, dieselbe Messgröße (Marke C1, `anon`, m7g.large mit arm64), gemessen am 26.09.2026 am v1.3-Abbild, Rohdatei `2026-09-v13-messung/rohdaten/94c-bodensatz-zyklen.txt`, Quelle `docs/performance.md`, Abschnitt "Die v1.3-Anfahrt vom 26.09.2026" | Entscheid D-09 der Phase 23, gesperrt am 27.09.2026 |

Drei Sätze, die zu diesem zweiten Eintrag gehören und ohne die er falsch
gelesen werden kann:

1. **Es ist kein Anstieg von 103,2 auf 731,9.** Die beiden Zahlen messen nicht
   dasselbe. Ein Container, der noch nie eingebettet hat, steht am 21.09.2026
   auf 103,9 MB (Marke A derselben Messung) und bestätigt die alte Zahl damit
   fast genau. Was der Store-Text ab 1.2.0 zeigt, ist der Zustand danach.
2. **Der Alt-Neu-Vergleich der READMEs fällt ersatzlos weg**, samt der 85,1
   Prozent. Eine Prozentzahl zwischen zwei Messgrößen wäre eine Verbesserung,
   die nie gemessen wurde. Der alte Vergleich bleibt in `docs/performance.md`
   an seinem Datum stehen.
3. **Die Spitze eines Volllaufs ist unberührt.** 52.111 Dokumente und 1.764 MB
   stammen aus der v1.1-Anfahrt, und der v1.2-Lauf hat sie nicht neu gemessen.
   Wer den Messsatz anfasst, misst vorher.

Zum dritten Eintrag, ebenfalls ein Satz, ohne den er falsch gelesen werden
kann: **1,7 MB weniger sind keine Verbesserung**, sondern zwei Abbilder in
derselben Messgröße, und die Nachanfahrt vom selben Tag hat für C1 729,3 MB
gelesen. Die Zahl wechselt, weil der Store-Text das Abbild beschreiben soll,
das er begleitet, und 731,9 MB bleibt für das v1.2-Abbild richtig.

---

## Entwurf 1.4.0 (Phase 29)

Plan 29-02, dem Owner vorgelegt am 06.10.2026. Dieser Abschnitt sammelt alle
Außentexte von 1.4.0 an einer Stelle, damit der Owner einmal liest: die sechs
Store-Beschreibungen, die README-Zeilen, die Labels der neuen Urteile, zwei
Variablentexte, die Release-Notiz, fünf Issue-Antworten und das
Pillow-Upstream-Issue. Nichts davon ist übernommen, gepostet oder
veröffentlicht. Die Übernahme in beide `info.xml`, die READMEs, die Kataloge
und `backend/appinfo/info.xml` ist Plan 29-12 und folgt erst der Abnahme; die
Release-Notiz geht mit dem Tag in Plan 29-15 hinaus; die Antworten und das
Pillow-Issue postet Plan 29-16, erst nach dem Release und nach einer erneuten
Freigabe des Owners.

Bis zur Übernahme tragen beide `info.xml`, die READMEs und die sechs Texte oben
in dieser Datei weiter die Fassung 1.3.2. Ein Unterschied zwischen diesem
Abschnitt und einer `info.xml` ist in diesem Fenster der erwartete
Zwischenstand und keine Drift.

Gesperrt und hier nur umgesetzt: D-24-04 (der Anteils-Satz, deutsch wörtlich),
die Owner-Regel vom 07.09.2026 (Faktenliste, eine Messzahl), der Owner-Entscheid
aus 28-11 ("store=kein Fall": die eine Messzahl bleibt 730,2 MB, `RESIDENT_FIGURE`
bleibt "730.2") und D-29-11 (keine Box-Feldbelege versprechen).

## Teil 1: die Anteils-Aussage (D-24-04)

Deutsch, wörtlich aus `24-CONTEXT.md` (D-24-04), zeichengleich und nicht
umformuliert:

> Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware hat, gibt per Profil höchstens die Hälfte der Box frei (Profil Standard) oder alles bis auf einen Kern (Profil Leistung).

Vorschlag Englisch, zur wörtlichen Abnahme (offene Frage (a) in Teil 9). Die
Profilnamen folgen dem englischen Katalog (Economy, Standard, Performance), und
"box" folgt der englischen Verwaltungsseite ("How much of this box Findling may
use"):

> Without any change on your side, Findling keeps running as economically as before. Anyone with more hardware can use a profile to free at most half of the box (Standard profile) or everything but one core (Performance profile).

Vorschlag Französisch, zur wörtlichen Abnahme. Die Profilnamen folgen dem
französischen Katalog (Économe, Standard, Performance), und "machine" folgt
der französischen Verwaltungsseite ("cette machine"):

> Sans aucune intervention, Findling continue de fonctionner aussi sobrement qu'avant. Avec plus de matériel, un profil libère au plus la moitié de la machine (profil Standard) ou tout sauf un cœur (profil Performance).

## Teil 2: die sechs Texte 1.4.0 im Wortlaut

Geändert wird gegenüber 1.3.2 an genau drei Stellen je Text, alles andere
bleibt Wort für Wort:

1. Zwei neue Spiegelstriche im ersten Block (findling: Profile und Suchmodell;
   findling_backend: ein Spiegelstrich, wo beides gewählt wird). Sie stehen vor
   der Datenschutz-Zeile, damit die Sprachzeile wie seit 1.3.0 die letzte Zeile
   unmittelbar vor "Known limitations" bleibt.
2. Der Satz aus Teil 1 als eigener Absatz direkt nach dem Block
   "Requirements" und vor der Enterprise-Zeile, weil er von der Hardware
   handelt.
3. Sonst nichts: die RAM-Zeile mit der einen Messzahl 730.2 MB / 730,2 MB /
   730,2 Mo bleibt unverändert, ebenso die Grenzliste, der Connector-Satz und
   die Dateitypen.

Die neuen Zeilen tragen keine Zahl; "int8" und "fp32" sind Modellnamen und
keine Messwerte.

Länge gegen 1.3.2, gezählt in Zeichen je Text (Selbstprüfung unten): findling
EN 1.509 auf 1.949, DE 1.645 auf 2.040, FR 1.780 auf 2.225; findling_backend
EN 1.398 auf 1.715, DE 1.499 auf 1.781, FR 1.628 auf 1.971. Jeder Text wächst
um ein Fünftel bis gut ein Viertel, und mehr als die Hälfte davon ist der
gesperrte Satz aus Teil 1.

### App 1: `findling`, `<description>` (Englisch, ohne `lang`-Attribut)

What Findling does:
- Full text search in the normal Nextcloud search bar
- OCR for scanned PDFs and images: nine languages available, German, English and French are the default
- Semantic search: finds documents through paraphrases
- Every result is permission-checked by Nextcloud
- No configuration: the first index run starts on its own
- Performance profiles: Economy by default, Standard and Performance after a pre-check of the hardware
- Search model: int8 built in, the more accurate fp32 can be downloaded once under Standard and Performance
- Privacy: everything runs locally, no telemetry, nothing leaves your server
- Search languages: German and English by default, Spanish, Italian, Dutch and Portuguese available

Known limitations:
- Spanish: año and ano are treated as the same word
- Portuguese: spellings before and after the spelling reform are not unified
- Compound words are split for German and Dutch only
- French has no full text analysis chain for document text

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Supported file types:
- PDF (scanned too), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images through OCR: JPEG, PNG, TIFF, WebP

Requirements:
- Nextcloud 33 to 35, apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB is enough, 730.2 MB resident after an index run, under a hard 2 GB limit (measured)
- CPU: 2 cores are enough, amd64 and arm64

Without any change on your side, Findling keeps running as economically as before. Anyone with more hardware can use a profile to free at most half of the box (Standard profile) or everything but one core (Performance profile).

Enterprise support and paid add-ons: request a quote at admin@infranode.dev

### App 1: `findling`, `<description lang="de">`

Was Findling kann:
- Volltextsuche über die normale Nextcloud-Suchleiste
- Texterkennung für gescannte PDFs und Bilder: neun Sprachen verfügbar, voreingestellt sind Deutsch, Englisch und Französisch
- Semantische Suche: findet Dokumente auch über Umschreibungen
- Jeder Treffer wird von Nextcloud rechtegeprüft
- Keine Konfiguration: der erste Indexlauf startet von selbst
- Leistungsprofile: Sparsam voreingestellt, Standard und Leistung nach einer Vorab-Prüfung der Hardware
- Suchmodell: int8 eingebaut, das genauere fp32 unter Standard und Leistung einmalig ladbar
- Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server
- Suchsprachen: Deutsch und Englisch voreingestellt, Spanisch, Italienisch, Niederländisch und Portugiesisch verfügbar

Bekannte Grenzen:
- Spanisch: año und ano gelten als dasselbe Wort
- Portugiesisch: Schreibweisen vor und nach der Rechtschreibreform werden nicht vereinheitlicht
- Zusammengesetzte Wörter werden nur für Deutsch und Niederländisch zerlegt
- Französisch hat keine eigene Analysekette für den Dokumenttext

Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server.

Unterstützte Dateitypen:
- PDF (auch gescannt), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Bilder per Texterkennung: JPEG, PNG, TIFF, WebP

Anforderungen:
- Nextcloud 33 bis 35, Apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB genügen, 730,2 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
- CPU: 2 Kerne genügen, amd64 und arm64

Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware hat, gibt per Profil höchstens die Hälfte der Box frei (Profil Standard) oder alles bis auf einen Kern (Profil Leistung).

Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev

### App 1: `findling`, `<description lang="fr">`

Ce que Findling sait faire :
- Recherche plein texte dans la barre de recherche normale de Nextcloud
- Reconnaissance optique pour les PDF numérisés et les images : neuf langues disponibles, allemand, anglais et français par défaut
- Recherche sémantique : trouve les documents par des périphrases
- Chaque résultat est vérifié par Nextcloud selon vos droits
- Aucune configuration : la première indexation démarre d'elle-même
- Profils de performance : Économe par défaut, Standard et Performance après une vérification préalable du matériel
- Modèle de recherche : int8 intégré, le fp32 plus précis se télécharge une fois sous Standard et Performance
- Confidentialité : tout fonctionne localement, aucune télémétrie, rien ne quitte votre serveur
- Langues de recherche : allemand et anglais par défaut, espagnol, italien, néerlandais et portugais disponibles

Limites connues :
- Espagnol : año et ano sont traités comme le même mot
- Portugais : les graphies d'avant et d'après la réforme orthographique ne sont pas unifiées
- Les mots composés ne sont découpés que pour l'allemand et le néerlandais
- Le français n'a pas de chaîne d'analyse plein texte pour le contenu des documents

Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur.

Types de fichiers pris en charge :
- PDF (numérisés aussi), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images par reconnaissance optique : JPEG, PNG, TIFF, WebP

Prérequis :
- Nextcloud 33 à 35, applications : AppAPI, Findling Backend (External Apps), Findling
- RAM : 4 Go suffisent, 730,2 Mo résidents après une indexation, sous une limite stricte de 2 Go (mesuré)
- CPU : 2 cœurs suffisent, amd64 et arm64

Sans aucune intervention, Findling continue de fonctionner aussi sobrement qu'avant. Avec plus de matériel, un profil libère au plus la moitié de la machine (profil Standard) ou tout sauf un cœur (profil Performance).

Support entreprise et modules payants : demande de devis à admin@infranode.dev

### App 2: `findling_backend`, `<description>` (Englisch, ohne `lang`-Attribut)

What Findling Backend is:
- The External App behind the Findling search app: text extraction, OCR and the search index
- Runs entirely inside your own instance and does nothing without the Findling app
- Never modifies your files
- Performance profile and search model are chosen on the admin page of the Findling app
- Privacy: everything runs locally, no telemetry, nothing leaves your server
- Search languages: German and English by default, Spanish, Italian, Dutch and Portuguese available

Known limitations:
- Spanish: año and ano are treated as the same word
- Portuguese: spellings before and after the spelling reform are not unified
- Compound words are split for German and Dutch only
- French has no full text analysis chain for document text

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Supported file types:
- PDF (scanned too), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images through OCR: JPEG, PNG, TIFF, WebP

Requirements:
- Nextcloud 33 to 35, apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB is enough, 730.2 MB resident after an index run, under a hard 2 GB limit (measured)
- CPU: 2 cores are enough, amd64 and arm64

Without any change on your side, Findling keeps running as economically as before. Anyone with more hardware can use a profile to free at most half of the box (Standard profile) or everything but one core (Performance profile).

Enterprise support and paid add-ons: request a quote at admin@infranode.dev

### App 2: `findling_backend`, `<description lang="de">`

Was Findling Backend ist:
- Die External App hinter der Such-App Findling: Textauszug, Texterkennung und der Suchindex
- Läuft komplett in Ihrer eigenen Instanz und tut ohne die App Findling nichts
- Verändert nie Ihre Dateien
- Leistungsprofil und Suchmodell werden in der Verwaltung der App Findling gewählt
- Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server
- Suchsprachen: Deutsch und Englisch voreingestellt, Spanisch, Italienisch, Niederländisch und Portugiesisch verfügbar

Bekannte Grenzen:
- Spanisch: año und ano gelten als dasselbe Wort
- Portugiesisch: Schreibweisen vor und nach der Rechtschreibreform werden nicht vereinheitlicht
- Zusammengesetzte Wörter werden nur für Deutsch und Niederländisch zerlegt
- Französisch hat keine eigene Analysekette für den Dokumenttext

Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server.

Unterstützte Dateitypen:
- PDF (auch gescannt), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Bilder per Texterkennung: JPEG, PNG, TIFF, WebP

Anforderungen:
- Nextcloud 33 bis 35, Apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB genügen, 730,2 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
- CPU: 2 Kerne genügen, amd64 und arm64

Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware hat, gibt per Profil höchstens die Hälfte der Box frei (Profil Standard) oder alles bis auf einen Kern (Profil Leistung).

Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev

### App 2: `findling_backend`, `<description lang="fr">`

Ce qu'est Findling Backend :
- L'External App derrière l'application de recherche Findling : extraction de texte, reconnaissance optique et index
- Fonctionne entièrement dans votre propre instance et ne fait rien sans l'application Findling
- Ne modifie jamais vos fichiers
- Le profil de performance et le modèle de recherche se choisissent dans la page d'administration de l'application Findling
- Confidentialité : tout fonctionne localement, aucune télémétrie, rien ne quitte votre serveur
- Langues de recherche : allemand et anglais par défaut, espagnol, italien, néerlandais et portugais disponibles

Limites connues :
- Espagnol : año et ano sont traités comme le même mot
- Portugais : les graphies d'avant et d'après la réforme orthographique ne sont pas unifiées
- Les mots composés ne sont découpés que pour l'allemand et le néerlandais
- Le français n'a pas de chaîne d'analyse plein texte pour le contenu des documents

Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur.

Types de fichiers pris en charge :
- PDF (numérisés aussi), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images par reconnaissance optique : JPEG, PNG, TIFF, WebP

Prérequis :
- Nextcloud 33 à 35, applications : AppAPI, Findling Backend (External Apps), Findling
- RAM : 4 Go suffisent, 730,2 Mo résidents après une indexation, sous une limite stricte de 2 Go (mesuré)
- CPU : 2 cœurs suffisent, amd64 et arm64

Sans aucune intervention, Findling continue de fonctionner aussi sobrement qu'avant. Avec plus de matériel, un profil libère au plus la moitié de la machine (profil Standard) ou tout sauf un cœur (profil Performance).

Support entreprise et modules payants : demande de devis à admin@infranode.dev

## Teil 3: die README-Zeilen, die sich ändern

Nur zwei Stellen je README: zwei neue Spiegelstriche am Ende von "Was Findling
kann" (und ihren Gegenstücken) und ein neuer Spiegelstrich am Ende von
"Anforderungen" mit dem Satz aus Teil 1. Der Messsatz (52.111 Dokumente,
1.764 MB Spitze) und die Zeile mit 730,2 MB bleiben unverändert. Die Zeilen
sind hier ungebrochen; der Umbruch auf die Zeilenlänge der READMEs ist
Satzarbeit in Plan 29-12.

`README.md`, neu am Ende von "Was Findling kann":

> - Leistungsprofile: Sparsam voreingestellt, Standard und Leistung nach einer Vorab-Prüfung der Hardware
> - Suchmodell: int8 eingebaut, das genauere fp32 unter Standard und Leistung einmalig ladbar

`README.md`, neu am Ende von "Anforderungen":

> - Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware hat, gibt per Profil höchstens die Hälfte der Box frei (Profil Standard) oder alles bis auf einen Kern (Profil Leistung).

`README.en.md`, neu am Ende von "What Findling does":

> - Performance profiles: Economy by default, Standard and Performance after a pre-check of the hardware
> - Search model: int8 built in, the more accurate fp32 can be downloaded once under Standard and Performance

`README.en.md`, neu am Ende von "Requirements":

> - Without any change on your side, Findling keeps running as economically as before. Anyone with more hardware can use a profile to free at most half of the box (Standard profile) or everything but one core (Performance profile).

`README.fr.md`, neu am Ende von "Ce que Findling sait faire":

> - Profils de performance : Économe par défaut, Standard et Performance après une vérification préalable du matériel
> - Modèle de recherche : int8 intégré, le fp32 plus précis se télécharge une fois sous Standard et Performance

`README.fr.md`, neu am Ende von "Prérequis":

> - Sans aucune intervention, Findling continue de fonctionner aussi sobrement qu'avant. Avec plus de matériel, un profil libère au plus la moitié de la machine (profil Standard) ou tout sauf un cœur (profil Performance).

## Teil 4: Labels und Abhilfen der neuen Urteile

Die drei neuen Codes sind seit Plan 29-01 gebaut, alle drei unter `skipped`
(siehe Teil 9 (b)). Der Wortlaut unten ist der vorläufige aus 29-01, so wie er
heute in `AdminViewService::REASON_TEXT` und den Katalogen steht; der Entwurf
schlägt ihn unverändert zur Abnahme vor. Die Abnahme gilt für Englisch und
Deutsch; die übrigen sechs Kataloge (fr, es, it, nl, pt_BR, pt_PT) folgen dem
englischen Text wie bisher.

| Code | Label EN | Label DE | Abhilfe EN | Abhilfe DE |
|---|---|---|---|---|
| `system_file` | System or helper file | System- oder Hilfsdatei | None. macOS metadata files (._) and Office lock files (~$) carry no document content. | Keine. macOS-Metadateien (._) und Office-Sperrdateien (~$) enthalten keinen Dokumentinhalt. |
| `legacy_format` | Old Office format under a new name | Altes Office-Format unter neuem Namen | Save the file again in the current Office format (.docx, .xlsx, .pptx). | Datei im aktuellen Office-Format (.docx, .xlsx, .pptx) neu speichern. |
| `unsupported_variant` | Image variant that cannot be read | Bildvariante, die nicht gelesen werden kann | None. The image uses an encoding the image library does not support. | Keine. Das Bild nutzt eine Kodierung, die die Bildbibliothek nicht unterstützt. |

Passwortgeschützte Office-Dateien unter OOXML-Endung (Plan 29-08) bekommen das
bestehende Urteil `encrypted` mit dem bestehenden Label "Password protected"
und brauchen keinen neuen Text.

**Die neu gefasste Abhilfe von `out_of_memory`.** Heute steht dort "The next
run tries again. If it happens again, lower the size cap." Der Größen-Cap
("Largest file to read") hilft bei Bildern nicht: ein kleines JPEG mit vielen
Megapixeln braucht mehr Speicher als ein großes PDF (Research Pitfall 7). Die
Stellschraube ist der Adressraum je Dokument. Der erste Satz bleibt
unverändert, nur der zweite wechselt:

> Alt, Englisch: The next run tries again. If it happens again, lower the size cap.
>
> Neu, Englisch: The next run tries again. If it happens again, give each document more memory: deploy Findling Backend with a larger FINDLING_EXTRACT_ADDRESS_SPACE_BYTES, for example 1073741824 (1 GiB).
>
> Alt, Deutsch: Wird beim nächsten Lauf erneut versucht. Bei Wiederholung den Größen-Cap senken.
>
> Neu, Deutsch: Wird beim nächsten Lauf erneut versucht. Bei Wiederholung jedem Dokument mehr Speicher geben: Findling Backend mit einem größeren FINDLING_EXTRACT_ADDRESS_SPACE_BYTES bereitstellen, zum Beispiel 1073741824 (1 GiB).

Hinweis für die Abnahme, nicht geprüft und deshalb nicht umgeschrieben: Ob der
erste Satz "The next run tries again" für `out_of_memory` stimmt, hat dieser
Plan nicht nachgelesen. In #18 steht öffentlich, dass ein Urteil an der
Dateiversion klebt; die Nachprüfung aus 29-09 holt `out_of_memory` einmal nach
dem Upgrade zurück. Wenn der Satz falsch ist, gehört die Korrektur in 29-12 und
braucht ein Wort des Owners.

**Vorschlag aus 29-06, offen geblieben: die Fehlerklasse auf der
Verwaltungskarte.** Die Diagnose-Antwort trägt seit 29-06 das Feld
`errorClass` (nur bei `failed`), sichtbar heute nur in `occ findling:diagnose`.
Eine sichtbare Zeile auf der Karte braucht ein neues Label in 16 Katalogen.
Vorschlag, falls der Owner es in 1.4.0 will (Umsetzung dann in 29-12):

> Englisch: Error class
>
> Deutsch: Fehlerklasse
>
> Französisch: Classe d'erreur

Ohne Wort des Owners bleibt die Karte, wie sie ist, und die Fehlerklasse steht
nur in `occ findling:diagnose`.

## Teil 5: zwei Variablentexte in `backend/appinfo/info.xml`

Englisch, weil die Datei dort englisch ist. `<display-name>` und `<default>`
bleiben bei beiden unverändert.

**`FINDLING_MAX_CELLS` (D-29-03, #21).** Seit 29-03 deklariert, mit vorläufigem
Text. Vorgeschlagen ist der vorläufige Text plus ein Satz, der in #21 sonst als
Frage zurückkäme: ein neuer Wert holt eine schon übersprungene Tabelle nicht
von selbst zurück.

> Vorläufig (29-03): A whole number of cells per spreadsheet file. The default of 200000 reads ordinary workbooks and keeps a single export with a million rows from taking the machine down. A larger file is skipped with the reason too_many_cells rather than indexed in part. Anything that is not a positive whole number falls back to the default.
>
> Neu (Entwurf 1.4.0): A whole number of cells per spreadsheet file. The default of 200000 reads ordinary workbooks and keeps a single export with a million rows from taking the machine down. A larger file is skipped with the reason too_many_cells rather than indexed in part. Anything that is not a positive whole number falls back to the default. A new value applies to the files read from then on; a spreadsheet already skipped is read again when it changes.

**`FINDLING_EXTRACT_ADDRESS_SPACE_BYTES` (Research Pitfall 7).** Der Satz "Only
one document is read at a time, so the number is the peak and not a multiple"
aus 1.3.2 ist ab 1.4.0 falsch und ist seit 29-03 vorläufig ersetzt. Der Entwurf
fasst den Schluss genauer und nimmt eine zweite Änderung von 1.4.0 auf: große
JPEGs werden seit 29-07 verkleinert dekodiert und erreichen den Deckel kaum
noch.

> Alt (1.3.2): A whole number of bytes. It caps the address space of the process that reads one document, so a broken or hostile file cannot take the machine down with it. The default of 536870912 (512 MB) reads every office document and every scanned page at 300 dpi. Very large photos, around 40 megapixels and up, need more and otherwise end as failed with the reason out_of_memory; 1073741824 (1 GiB) reads them. Only one document is read at a time, so the number is the peak and not a multiple.
>
> Neu (Entwurf 1.4.0): A whole number of bytes. It caps the address space of the process that reads one document, so a broken or hostile file cannot take the machine down with it. The default of 536870912 (512 MB) reads every office document and every scanned page at 300 dpi. Very large PNG and TIFF images, around 40 megapixels and up, need more and otherwise end as failed with the reason out_of_memory; 1073741824 (1 GiB) reads them. Large JPEGs are decoded at reduced scale and rarely reach the cap. The cap holds for each reading process on its own: under Economy one document is read at a time, under Standard and Performance several are read side by side, and each of them may take this much.

Hinweis für die Abnahme: Die Schwelle "around 40 megapixels" ist die gemessene
Zahl aus 1.3.2 und stammt aus der Zeit vor dem verkleinerten JPEG-Weg; für
PNG und TIFF ist sie nicht neu gemessen. Der Entwurf schränkt sie deshalb auf
PNG und TIFF ein und sagt für JPEG nur "rarely", ohne Zahl.

## Teil 6: die Release-Notiz v1.4.0 (englisch, Faktenliste)

Owner-Regel vom 02.10.2026: GitHub-Releases mit englischer Beschreibung als
Faktenliste. Sie geht mit dem Tag in Plan 29-15 hinaus.

> Findling 1.4.0. Both apps need to be on 1.4.0.
>
> - Performance profiles: Economy (the default, unchanged behaviour), Standard and Performance. A pre-check of the hardware runs before a profile takes effect; under Standard and Performance, OCR can run in several slots, as many as the box carries.
> - Search model: int8 stays built in; the more accurate fp32 can be chosen under Standard and Performance and is then downloaded once, with a digest check.
> - Reading and OCR processes run at lowered priority and are the first candidates for the kernel's out-of-memory killer; a reading process killed from outside is retried instead of recorded as damaged (#15, #18, #19).
> - macOS AppleDouble files (`._*`) and Office lock files (`~$*`) are skipped as "System or helper file" and leave the index (#18, #22).
> - A download that arrives shorter than the file is retried instead of recorded as damaged (#18).
> - Greyscale TIFFs with an extra channel marked ExtraSamples 0 or 1 are read (#18).
> - TIFFs with SampleFormat 0 are read: uncompressed ones directly, compressed ones (LZW, Deflate) up to 32 MiB through a corrected copy in memory; larger ones get "Image variant that cannot be read" (#18).
> - Floating point TIFFs (SampleFormat 3, including Float16) get "Image variant that cannot be read" instead of "File damaged" (#18).
> - Large JPEGs are decoded at reduced scale; a header estimate turns the remaining memory cap hits into out_of_memory instead of corrupt (#18).
> - Office files with a .docx, .xlsx or .pptx name that are OLE containers are named "Password protected" or "Old Office format under a new name" (#18).
> - The exception class of the reader is stored for each failed file and shown by `occ findling:diagnose` (#18).
> - After the upgrade, files with verdicts of the fixed classes are re-checked once, with no manual cleanup (#18, #22).
> - `FINDLING_MAX_CELLS` is declared as a deploy option (#21).
> - The slot calculation accounts for the size of the index.
>
> Thanks to budachst for the reports and for the patient diagnosis work behind most of this release (#15, #18, #19, #21, #22).

Die Zeile zur Fehlerklasse nennt nur `occ findling:diagnose`; kommt die Zeile
auf der Verwaltungskarte (Teil 4) dazu, ergänzt 29-15 "and on the admin page".

## Teil 7: die Antworten in den Issues #15, #18, #19, #21, #22

Englisch, Ich-Form, kurz. **Nur Entwurf:** gepostet wird in Plan 29-16, nach
dem Release und erst nach einer erneuten Freigabe des Owners. Kein Issue wird
dabei geschlossen; wo eine Antwort das Schließen anbietet, entscheidet
budachst. Vor dem Entwurf wurde jeder Verlauf ganz gelesen (06.10.2026);
nichts, was budachst schon beantwortet hat, wird erneut gefragt, das Setup
(NC 33.0.8, groupfolders, Gruppen mit "/") ebenfalls nicht.

Zwei Korrekturen an früheren eigenen Kommentaren stehen ausdrücklich in den
Entwürfen, weil der gebaute Stand von ihnen abweicht:

- In #18 stand zweimal "profiles size the ceiling". Gebaut ist das nicht: die
  Profile bestimmen die Zahl der Slots, der Adressraum je Dokument bleibt
  `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES` (`config.py`, kein Bezug in
  `profile.py`).
- In #18 stand für Gleitkomma-TIFFs "real error stored". Gebaut ist die
  Fehlerklasse nur für `failed`-Urteile (29-06); `unsupported_variant` ist
  `skipped` (29-01) und trägt keine Klasse. In #22 stand "excluded by a rule";
  gebaut ist "System or helper file" (29-05, Begründung dort: `excluded` ist
  ein Live-Zeichen der PHP-Seite und wird nie gespeichert).

### #15 (Scanning skips files/folders with funny chars/emojies)

> Findling 1.4.0 is in the store. For this issue it changes two things: a reading process that is killed or restarted from outside is retried instead of counting as a failed attempt, and the reading processes run at lowered priority.
>
> I have to be honest about the limit, though: we never found out why file 1441501 got stuck on your instance (no restart, no kernel kill, no crash in the logs), so I cannot promise that 1.4.0 fixes that file. "Stuck repeatedly" is also not part of the automatic re-check after the upgrade. The quickest test is to rename or re-upload that one PDF once after updating both apps. If it ends as "stuck repeatedly" again, the output of `occ findling:diagnose 1441501` would help me. If it gets indexed, I would close this issue, if that is fine with you.

### #18 (Files marked as corrupted, when they're not)

> Findling 1.4.0 is in the store, with the fixes from this thread:
>
> - `._*` sidecars and `~$*` lock files are skipped as "System or helper file" and leave the index. (In #22 I called this "excluded by a rule"; it got its own label instead, because "excluded" stays reserved for the folders you exclude yourself.)
> - Greyscale TIFFs with an extra channel marked ExtraSamples 0 or 1, your Golfpreis class, are now read.
> - TIFFs with SampleFormat 0 are read from 1.4.0 on: uncompressed ones directly, compressed ones (LZW, Deflate) through a corrected copy in memory; that copy is only made up to a file size of 32 MiB, and a larger compressed SampleFormat-0 TIFF gets the verdict `unsupported_variant` instead of `corrupt`. Floating point TIFFs (SampleFormat 3, including Float16) are not decoded and get `unsupported_variant` as well. Your disguised PNG is in that last group.
> - Large JPEGs are decoded at reduced scale, and a header estimate turns the remaining memory cap hits into `out_of_memory` instead of `corrupt`.
> - Office files under .docx/.xlsx/.pptx names that are OLE containers are named "Password protected" or "Old Office format under a new name".
> - A download that arrives shorter than the file is retried instead of recorded as damaged.
> - For every `failed` file, `occ findling:diagnose` now shows the exception class of the reader.
> - Already recorded verdicts of the fixed classes (`corrupt`, `out_of_memory` and every sidecar) are re-checked once after the upgrade, with no manual cleanup. The re-check starts when both apps are on 1.4.0 and runs in batches alongside the normal index work, so on your instance it will take a while.
>
> Two corrections to what I wrote earlier. First, the profiles do not size the memory ceiling per document: they decide how many documents are read side by side, and the ceiling stays `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES`. For your large print images, raising it (for example to 1073741824) is still the lever for PNG and TIFF images. Second, for the floating point TIFFs no error class is stored: they get the verdict `unsupported_variant`, which is a "skipped" state, and the class is only kept for "failed" ones.
>
> Not in 1.4.0: decoding floating point TIFFs (still only something I will evaluate), a separate "truncated" verdict, and a HEIF/HEIC path for misnamed files. I have not run 1.4.0 against a corpus like yours, so if you post a fresh "failed by reason" snapshot once the re-check has run through, I will read it against this list. I will also open an issue at Pillow for the missing greyscale entries and link it here.

### #19 (Findling admin UI can't connect to backend while scanning)

> Findling 1.4.0 is in the store. The OCR and reading processes now run at lowered priority, so the status call and Nextcloud itself get the CPU first while OCR is busy; that competition for the CPU is what delayed the answers you saw. On your 8 vCPU host the admin page now also offers the Standard and Performance profiles, which run several OCR jobs side by side after a pre-check of the box; Economy stays the default. If the "cannot connect" message still shows up during OCR after the upgrade, let me know which profile is active.

### #21 (Make more config options available in admin UI)

> Findling 1.4.0 declares `FINDLING_MAX_CELLS` as a deploy option (default 200000 cells per spreadsheet), so it can now be set when Findling Backend is deployed, the same way as `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES`. One thing to know: a new value applies to files read from then on; spreadsheets already skipped with "too many cells" are read again when they change. Showing these limits on the admin page is not in 1.4.0; I keep this issue open for that part.

### #22 (More options for excluding files/folders from scanning)

> Findling 1.4.0 skips macOS AppleDouble files (`._*`) automatically, and Office lock files (`~$*`) as well, with no setting. One correction to my earlier comment: they get the verdict "System or helper file", not "Excluded by a rule", because that label stays reserved for the folders you exclude yourself. Files of this kind that are already in the error list are re-checked once after the upgrade and leave it on their own. Bundles (.key and the like) are not handled specially in 1.4.0; my question above, which files from inside a bundle show up and with which reason, is still open whenever you get to it.

## Teil 8: das Pillow-Upstream-Issue (englisch)

Issue zuerst, ein PR erst nach Rückmeldung (Research, State of the Art). Die
Repro-Datei wird im Skript selbst erzeugt; keine Datei, kein Pfad und kein Name
aus #18. Das Skript ist am 06.10.2026 lokal gegen Pillow 12.3.0 gelaufen und
lieferte genau die unten zitierte Ausgabe (Speicheradressen gekürzt).
Gepostet wird in Plan 29-16 nach erneuter Freigabe.

Nicht im Issue, bewusst: die TIFF-Orientierung aus `deferred-items.md`
(Tag 274 = 6). Sie ist lokal beobachtet, aber nicht als Pillow-Fehler
nachgewiesen; ob sie ein eigenes Issue wird, entscheidet der Owner nach einer
Prüfung.

Titel:

> TIFF: greyscale with one extra sample fails to open when ExtraSamples is 0 (unspecified) or 1 (associated alpha)

Text:

> **What did you do?**
>
> Opened a contiguous 8-bit greyscale TIFF with two samples per pixel (PhotometricInterpretation 1, SamplesPerPixel 2, BitsPerSample (8, 8)) whose ExtraSamples tag is 0 (unspecified data) or 1 (associated alpha). Files of this shape come out of older scan and print tools.
>
> **What did you expect to happen?**
>
> The file opens, as it does with ExtraSamples 2 (mode `LA`). With 1 a premultiplied mode such as `La` would fit; with 0 the extra channel could be dropped or kept without alpha meaning.
>
> **What actually happened?**
>
> `PIL.UnidentifiedImageError: cannot identify image file`, raw and LZW alike.
>
> **What are your OS, Python and Pillow versions?**
>
> - OS: Windows 11 (the same failure was seen on Linux in a Debian trixie container)
> - Python: 3.13
> - Pillow: 12.3.0
>
> ```python
> import io
> import struct
>
> import PIL
> from PIL import Image
>
>
> def grey_with_extra_sample(extra_samples: int, compression: str | None) -> bytes:
>     """A 2-sample greyscale TIFF whose ExtraSamples tag (338) is set to the given value."""
>     buffer = io.BytesIO()
>     Image.new("LA", (64, 48), (128, 255)).save(buffer, "TIFF", compression=compression)
>     data = bytearray(buffer.getvalue())
>     order = {b"II": "<", b"MM": ">"}[bytes(data[:2])]
>     (ifd,) = struct.unpack(order + "I", data[4:8])
>     (count,) = struct.unpack(order + "H", data[ifd : ifd + 2])
>     for index in range(count):
>         entry = ifd + 2 + 12 * index
>         tag, kind, _ = struct.unpack(order + "HHI", data[entry : entry + 8])
>         if tag == 338:
>             assert kind == 3  # SHORT, stored inline
>             data[entry + 8 : entry + 10] = struct.pack(order + "H", extra_samples)
>             return bytes(data)
>     raise AssertionError("no ExtraSamples tag written")
>
>
> print("Pillow", PIL.__version__)
> for compression in (None, "tiff_lzw"):
>     for extra in (0, 1, 2):
>         try:
>             with Image.open(io.BytesIO(grey_with_extra_sample(extra, compression))) as image:
>                 image.load()
>                 result = f"ok, mode {image.mode}"
>         except Exception as error:
>             result = f"{type(error).__name__}: {error}"
>         print(f"compression={compression or 'raw'} ExtraSamples={extra}: {result}")
> ```
>
> Output:
>
> ```
> Pillow 12.3.0
> compression=raw ExtraSamples=0: UnidentifiedImageError: cannot identify image file <_io.BytesIO object at 0x...>
> compression=raw ExtraSamples=1: UnidentifiedImageError: cannot identify image file <_io.BytesIO object at 0x...>
> compression=raw ExtraSamples=2: ok, mode LA
> compression=tiff_lzw ExtraSamples=0: UnidentifiedImageError: cannot identify image file <_io.BytesIO object at 0x...>
> compression=tiff_lzw ExtraSamples=1: UnidentifiedImageError: cannot identify image file <_io.BytesIO object at 0x...>
> compression=tiff_lzw ExtraSamples=2: ok, mode LA
> ```
>
> `OPEN_INFO` in `TiffImagePlugin.py` has `(II|MM, 1, (1,), 1, (8, 8), (2,)) -> ("LA", "LA")` but no entry for ExtraSamples 0 or 1 with the same layout. #9514 already ignores unspecified extra samples for PlanarConfiguration 2; this is the contiguous case. Mapping 0 to `LA` would be wrong, since unspecified data is not alpha, so I would suggest a raw mode `LX` for mode `L`, analogous to the existing `PX` for palette images (unpack the grey byte, skip the extra one). For 1, `La` seems the natural target.
>
> Would a PR along these lines be welcome? I am happy to prepare one with test images if the direction is right.

Zum letzten Absatz: Die Aussage zu `PX` und zum fehlenden Eintrag ist in der
Research gegen Pillow main geprüft (`TiffImagePlugin.py`, `Unpack.c`); dass
`La` für ExtraSamples 1 der richtige Zielmodus ist, ist ein Vorschlag und nicht
gemessen. Der Satz zum Debian-Container gibt den Feldbefund aus #18 wieder,
ohne Datei oder Instanz zu nennen; wenn der Owner ihn nicht will, fällt er
ersatzlos weg.

## Teil 9: die Owner-Abnahme in einer Liste

**Offen, zur Entscheidung:**

- **(a) Die englische und die französische Fassung des D-24-04-Satzes**
  (Research Open Question 3). Vorschlag in Teil 1, wörtlich abzunehmen oder zu
  ändern. Der deutsche Satz steht fest und wird nicht berührt. Übernahme in
  29-12 in beide `info.xml` und die READMEs.

**Zur Ratifizierung, bereits gebaut** nach den Empfehlungen, die als
Owner-Vorgabe gelten (29-RESEARCH.md, Open Questions RESOLVED; CONTEXT-Ergänzung
vom 06.10.2026). Hier wird nicht neu entschieden, sondern bestätigt, was schon
im Code steht; eine Ablehnung ist möglich und hat jeweils die genannte Folge.

- **(b) `system_file`, `legacy_format` und `unsupported_variant` sind
  `skipped`, nicht `failed`.** Umgesetzt in Plan 29-01 (Codes unter
  `State.SKIPPED` in allen fünf Kopien und 16 Katalogen), genutzt von 29-05,
  29-07 und 29-08. Folge für den Admin: diese Dateien erscheinen nicht im
  Fehlerzähler, sondern bei den übersprungenen. Folge einer Ablehnung: ein
  neuer Fix-Plan vor 29-12, der die Codes nach `failed` verlegt, samt
  K6-Rückfall, Paritätstests und Katalogen.
- **(c) Die Starlette-Warnung wird per gezieltem `filterwarnings`-Eintrag
  beseitigt, nicht mit `httpx2`.** Umgesetzt in Plan 29-03 (pyproject-Filter
  plus Erstimport in conftest, `httpx2` nicht im Lock). Grund: `httpx2` ist neu
  und von slopcheck als [SUS] eingestuft, und neue Abhängigkeiten nur mit
  Grund. Folge einer Ablehnung: ein neuer Fix-Plan vor 29-12, der `httpx2` als
  Dev-Abhängigkeit nach einer Paketprüfung durch den Owner aufnimmt.
- **(d) `ocr_failed` bleibt außerhalb der Nachprüfung nach dem Upgrade.**
  Umgesetzt in Plan 29-09 (Auswahl ohne `ocr_failed`, per Test gesichert);
  Begründung im Audit 29-14: der verkleinerte JPEG-Weg ändert das Bild der
  Engine nicht, die bekommt ohnehin höchstens 3500 px. Folge einer Ablehnung:
  ein neuer Fix-Plan vor 29-12, der `ocr_failed` in `_RECHECK_FAILED` aufnimmt.
- **(e) Die Grenze von D-29-06(b), wie in Teil 7 benannt** (Ergebnis des
  Prüf-Schritts aus 29-07): TIFFs mit SampleFormat 0 werden ab 1.4.0 gelesen,
  unkomprimiert direkt und komprimiert (LZW, Deflate) über eine korrigierte
  Kopie im Arbeitsspeicher; diese Kopie wird nur bis 32 MiB Dateigröße
  angelegt, ein größeres komprimiertes SampleFormat-0-TIFF bekommt das Urteil
  `unsupported_variant` statt `corrupt`. Gleitkomma-TIFFs (SampleFormat 3,
  auch Float16) werden nicht dekodiert und bekommen ebenfalls
  `unsupported_variant`. Umgesetzt in Plan 29-07 (`_normalise_sample_format`,
  `_SF0_PATCH_MAX_BYTES`). Folge einer Ablehnung: ein neuer Fix-Plan vor 29-12,
  der entweder die 32-MiB-Grenze verschiebt (Speicherpreis: kurzzeitig zwei
  Kopien) oder komprimiertes SampleFormat 0 ganz auf `unsupported_variant`
  stellt; der Satz in Teil 6, Teil 7 und hier wechselt dann mit.

**Außerdem im Entwurf, zur Kenntnis bei der Lektüre** (keine eigene Frage,
aber jede Zeile ist eine Owner-Entscheidung, wenn er sie ändern will): die zwei
neuen Spiegelstriche je Text und ihr Platz (Teil 2), die Abhilfe von
`out_of_memory` samt dem ungeprüften ersten Satz (Teil 4), der Vorschlag
"Error class" für die Verwaltungskarte (Teil 4), die Einschränkung der
40-Megapixel-Schwelle auf PNG und TIFF (Teil 5), die zwei Korrekturen an
früheren #18-Kommentaren und die eine an #22 (Teil 7), der Debian-Satz im
Pillow-Issue (Teil 8).

### Selbstprüfung gegen die Gates (06.10.2026)

Die sechs Beschreibungen aus Teil 2 wurden in eine `info.xml`-Hülle je App
gesetzt und mit `scan_one_measured_figure` und `scan_resident_figure_of_an_info`
aus `backend/tests/test_store_metadata.py` geprüft; der ganze Abschnitt
"Entwurf 1.4.0" wurde auf U+2013 und U+2014 und auf das Emoji-Muster des Gates
geprüft.

Ergebnis: Beide Hüllen ohne Befund; jede der sechs Beschreibungen trägt genau
eine Messzahl (EN 730.2 MB, DE 730,2 MB, FR 730,2 Mo). Der D-24-04-Satz steht
in beiden deutschen Texten zeichengleich mit `24-CONTEXT.md`. Der Abschnitt
enthält kein U+2013, kein U+2014 und kein Emoji. Teil 8 nennt weder budachst
noch einen Datei-, Pfad- oder Containernamen aus #18. "SampleFormat" steht in
Teil 7 und in Teil 9. `backend/tests/test_store_metadata.py` läuft über die
ganze Datei grün (76 passed); der erste Lauf hatte das gesperrte Wort der
Vokabelregel in der #18-Antwort gefunden, es ist ersetzt.

## Die Abnahme 1.4.0

Textabnahme 1.4.0: **2026-10-06, im Wortlaut: "ok abgenommen".** Der Owner
hat den Entwurf Teil 1 bis 9 gesehen und wie vorgelegt abgenommen; das Wort
kam über den Orchestrator von Phase 29 an den Checkpoint von Plan 29-02.

- **(a) EN- und FR-Fassung des D-24-04-Satzes: wie vorgeschlagen
  abgenommen.** Englisch und Französisch stehen damit wörtlich fest, so wie in
  Teil 1; der deutsche Satz bleibt unverändert.
- **(b) bis (e): ratifiziert.** `skipped` für die drei neuen Codes (29-01), der
  `filterwarnings`-Eintrag statt `httpx2` (29-03), `ocr_failed` außerhalb der
  Nachprüfung (29-09) und die Grenze von D-29-06(b) wie in Teil 7 (29-07). Kein
  Fix-Plan vor 29-12 nötig.
- **Die drei offenen Punkte zum Lesen bleiben wie im Entwurf:** die Abhilfe von
  `out_of_memory` (Teil 4), die 40-Megapixel-Schwelle nur für PNG und TIFF
  (Teil 5) und der Satz zum Linux-Container im Pillow-Issue (Teil 8).
- Der Vorschlag "Error class" für die Verwaltungskarte (Teil 4) ist mit dem
  Entwurf abgenommen; ob 29-12 die Zeile einbaut, folgt dem Umfang von 29-12.

Änderungen des Owners am Entwurf: keine.

Die wörtliche Übernahme in beide `info.xml`, die drei READMEs, die Labels und
Kataloge und die zwei Variablentexte ist Plan 29-12. Die Release-Notiz geht
mit dem Tag in 29-15 hinaus. Die fünf Issue-Antworten und das Pillow-Issue
bleiben Entwürfe, bis 29-16 sie nach dem Release und nach einer erneuten
Freigabe des Owners postet.
