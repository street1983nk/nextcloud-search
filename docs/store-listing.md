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

**Stand dieser Datei:** Die sechs Texte unten sind seit dem 21.09.2026 der
Entwurf für 1.2.0 und noch nicht ausgeliefert. Beide `info.xml` und die drei
READMEs tragen bis zur Abnahme weiter die Fassung mit 103,2 MB; die wörtliche
Übernahme ist Plan 16-12 und findet erst nach der Owner-Abnahme statt. Wer in
diesem Fenster einen Unterschied zwischen dieser Datei und einer `info.xml`
findet, hat den erwarteten Zwischenstand vor sich und keine Drift. Der Entwurf
mit allen Gegenüberstellungen steht unten im Abschnitt "Entwurf v1.2.0".

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
- Privacy: everything runs locally, no telemetry, nothing leaves your server

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Supported file types:
- PDF (scanned too), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images through OCR: JPEG, PNG, TIFF, WebP

Requirements:
- Nextcloud 33 to 35, apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB is enough, 731.9 MB resident after an index run, under a hard 2 GB limit (measured)
- CPU: 2 cores are enough, amd64 and arm64

Enterprise support and paid add-ons: request a quote at admin@infranode.dev

## `<description lang="de">`

Was Findling kann:
- Volltextsuche über die normale Nextcloud-Suchleiste
- Texterkennung für gescannte PDFs und Bilder: neun Sprachen verfügbar, voreingestellt sind Deutsch, Englisch und Französisch
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
- RAM: 4 GB genügen, 731,9 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
- CPU: 2 Kerne genügen, amd64 und arm64

Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev

## `<description lang="fr">`

Ce que Findling sait faire :
- Recherche plein texte dans la barre de recherche normale de Nextcloud
- Reconnaissance optique pour les PDF numérisés et les images : neuf langues disponibles, allemand, anglais et français par défaut
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
- RAM : 4 Go suffisent, 731,9 Mo résidents après une indexation, sous une limite stricte de 2 Go (mesuré)
- CPU : 2 cœurs suffisent, amd64 et arm64

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
- Privacy: everything runs locally, no telemetry, nothing leaves your server

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Supported file types:
- PDF (scanned too), DOCX, PPTX, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV
- Images through OCR: JPEG, PNG, TIFF, WebP

Requirements:
- Nextcloud 33 to 35, apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB is enough, 731.9 MB resident after an index run, under a hard 2 GB limit (measured)
- CPU: 2 cores are enough, amd64 and arm64

Enterprise support and paid add-ons: request a quote at admin@infranode.dev

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
- RAM: 4 GB genügen, 731,9 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
- CPU: 2 Kerne genügen, amd64 und arm64

Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev

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
- RAM : 4 Go suffisent, 731,9 Mo résidents après une indexation, sous une limite stricte de 2 Go (mesuré)
- CPU : 2 cœurs suffisent, amd64 et arm64

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

# Änderungsprotokoll der Messzahl in den Store-Texten

Eine ersetzte Zahl ohne Nachtrag lässt später nicht mehr erkennen, was früher
gemessen wurde und unter welchen Bedingungen es galt. Deshalb steht jede
Ablösung hier mit Datum, Plan und Messgröße, und nicht nur der jeweils letzte
Stand.

| Datum | Plan | Was sich ändert | Abgelöste Zahl und ihre Messgröße | Neue Zahl und ihre Messgröße | Grundlage |
|---|---|---|---|---|---|
| 11.09.2026 | 11-09 | die RAM-Zeile der sechs Store-Texte bekommt erstmals eine Kernzahl | keine Zahl im Text | 103,2 MB, Grundlast im Leerlauf mit nie geladenem Modell, gemessen am 10.09.2026 auf m7g.large, Rohdatei `2026-09-vergleichsmessung-m7g/rohdaten/94-grundlast.txt` | Owner-Entscheid vom 11.09.2026, Fassung B |
| 21.09.2026 | 16-11 | die RAM-Zeile der sechs Store-Texte und die Grundlast-Zeile der drei READMEs | 103,2 MB, Grundlast im Leerlauf mit nie geladenem Modell; bleibt für genau diese Bedingungen gültig und steht weiter in `docs/performance.md` | 731,9 MB, residenter Stand nach einem Indexlauf mit entladenem Modell, gemessen am 21.09.2026 auf m7g.large mit arm64 gegen das ausgelieferte v1.2-Abbild, Rohdatei `2026-09-v12-messung/rohdaten/94b-grundlast-rueckkehr.txt` (Marke C) | Entscheid E1 der Phase 16, gesperrt am 21.09.2026 |

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
