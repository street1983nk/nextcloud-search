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
- OCR for scanned PDFs and images: German, English, French
- Semantic search: finds documents through paraphrases
- Every result is permission-checked by Nextcloud
- No configuration: the first index run starts on its own
- Privacy: everything runs locally, no telemetry, nothing leaves your server

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Supported file types:
- PDF (scanned too), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images through OCR: JPEG, PNG, TIFF, WebP

Requirements:
- Nextcloud 33 to 35, apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB is enough, 103.2 MB idle, under a hard 2 GB limit (measured)
- CPU: 2 cores are enough, amd64 and arm64

## `<description lang="de">`

Was Findling kann:
- Volltextsuche über die normale Nextcloud-Suchleiste
- Texterkennung für gescannte PDFs und Bilder: Deutsch, Englisch, Französisch
- Semantische Suche: findet Dokumente auch über Umschreibungen
- Jeder Treffer wird von Nextcloud rechtegeprüft
- Keine Konfiguration: der erste Indexlauf startet von selbst
- Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server

Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server.

Unterstützte Dateitypen:
- PDF (auch gescannt), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Bilder per Texterkennung: JPEG, PNG, TIFF, WebP

Anforderungen:
- Nextcloud 33 bis 35, Apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB genügen, 103,2 MB im Leerlauf, unter einer harten 2-GB-Grenze (gemessen)
- CPU: 2 Kerne genügen, amd64 und arm64

## `<description lang="fr">`

Ce que Findling sait faire :
- Recherche plein texte dans la barre de recherche normale de Nextcloud
- Reconnaissance optique pour les PDF numérisés et les images : allemand, anglais, français
- Recherche sémantique : trouve les documents par des périphrases
- Chaque résultat est vérifié par Nextcloud selon vos droits
- Aucune configuration : la première indexation démarre d'elle-même
- Confidentialité : tout fonctionne localement, aucune télémétrie, rien ne quitte votre serveur

Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur.

Types de fichiers pris en charge :
- PDF (numérisés aussi), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images par reconnaissance optique : JPEG, PNG, TIFF, WebP

Prérequis :
- Nextcloud 33 à 35, applications : AppAPI, Findling Backend (External Apps), Findling
- RAM : 4 Go suffisent, 103,2 Mo au repos, sous une limite stricte de 2 Go (mesuré)
- CPU : 2 cœurs suffisent, amd64 et arm64

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
- Privacy: everything runs locally, no telemetry, nothing leaves your server

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Supported file types:
- PDF (scanned too), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images through OCR: JPEG, PNG, TIFF, WebP

Requirements:
- Nextcloud 33 to 35, apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB is enough, 103.2 MB idle, under a hard 2 GB limit (measured)
- CPU: 2 cores are enough, amd64 and arm64

## `<description lang="de">`

Was Findling Backend ist:
- Die External App hinter der Such-App Findling: Textauszug, Texterkennung und der Suchindex
- Läuft komplett in Ihrer eigenen Instanz und tut ohne die App Findling nichts
- Verändert nie Ihre Dateien
- Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server

Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server.

Unterstützte Dateitypen:
- PDF (auch gescannt), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Bilder per Texterkennung: JPEG, PNG, TIFF, WebP

Anforderungen:
- Nextcloud 33 bis 35, Apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB genügen, 103,2 MB im Leerlauf, unter einer harten 2-GB-Grenze (gemessen)
- CPU: 2 Kerne genügen, amd64 und arm64

## `<description lang="fr">`

Ce qu'est Findling Backend :
- L'External App derrière l'application de recherche Findling : extraction de texte, reconnaissance optique et index
- Fonctionne entièrement dans votre propre instance et ne fait rien sans l'application Findling
- Ne modifie jamais vos fichiers
- Confidentialité : tout fonctionne localement, aucune télémétrie, rien ne quitte votre serveur

Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur.

Types de fichiers pris en charge :
- PDF (numérisés aussi), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images par reconnaissance optique : JPEG, PNG, TIFF, WebP

Prérequis :
- Nextcloud 33 à 35, applications : AppAPI, Findling Backend (External Apps), Findling
- RAM : 4 Go suffisent, 103,2 Mo au repos, sous une limite stricte de 2 Go (mesuré)
- CPU : 2 cœurs suffisent, amd64 et arm64

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

Der Owner hat beide Fassungen im Wortlaut gesehen und Fassung B gewählt, den
Messsatz dreisprachig entschieden und die französischen Texte ohne Änderung
abgenommen. Zur Prozentzahl kam kein Einwand, es bleibt bei 85,1 Prozent, und
die 52.111 bleibt die Zahl des Laufs, den der Satz beschreibt. Was damit nach
außen geht, steht oben in den sechs Texten und in den drei READMEs; danach wird
es nicht mehr angefasst, weil der Store-Text unveränderlich mit dem Release
reist.
