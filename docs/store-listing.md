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
| Je Elementart darf ein Sprachcode nur einmal vorkommen | `uniqueNameL10n`, `uniqueSummaryL10n`, `uniqueDescriptionL10n` |
| Kein Element bleibt leer | ein leeres Element löst beim Upload einen Serverfehler aus, gemessen am Schwesterprojekt |
| Keine Backticks und keine Tabellen in einer Beschreibung | der Store rendert Markdown anders als das Repository |
| Keine Gedankenstriche, keine Emojis, echte Umlaute, echte Akzente | die Typografie-Regel dieses Projekts |
| Kein Querverweis auf den MCP Connector | D-12, erst nach dem Content-Hit-Fidelity-Test |

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

## Die gemessene Zahl

Der Satz mit der Messung stammt aus dem Semantik-Volllauf von Plan 06-11 und
ist mit der Nachmessung von Plan 06.1-18 auf die Zahl vom 07.09.2026 gezogen.
Er wird hier zitiert, nicht neu formuliert, und steht an drei Orten in
derselben Form: in `README.en.md`, in `php/appinfo/info.xml` und in
`backend/appinfo/info.xml`, jeweils in der englischen Fassung. Das Gate prüft
diese Gleichheit, weil drei Orte für eine Zahl sonst auseinanderlaufen und die
Store-Beschreibung der Ort ist, an dem es niemandem auffällt.

> On a 4-GB ARM64 box with 51,961 indexed documents and the semantic search
> active, the container peaked at 1,813 MB of resident anonymous memory, under
> a hard 2 GB limit enforced by the kernel.

Neben der Zahl stehen in jeder Sprache zwei ehrliche Sätze: Alle vier
Kernel-Zähler für Speicherdruck stehen auf null, auch der, der in der Messung
vom 05.09.2026 mit ihrer Spitze von 1.838 MB noch bei 2.796 stand; und der
größte Teil des Speichers ist inzwischen die Texterkennung, die drei Sprachen
liest, während die Suchphase 1.125 MB kostet.

Seit Plan 06-12 tragen die Texte dazu die zwei Zusagen aus D-17: die gemessene
Einbettungsdauer und die Abdeckungsaussage. Ihre Zahlen kommen aus
`docs/performance.md` und `docs/embeddings.md` und werden hier nicht neu
gerechnet; gerundet wird nichts, und eine Hochrechnung kommt nicht vor.

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
| Englisch | `<summary>` | Zero-config full text search for your files, including scanned documents | 72 von 128 |
| Deutsch | `<summary lang="de">` | Volltextsuche für Ihre Dateien ohne Konfiguration, gescannte Dokumente eingeschlossen | 85 von 128 |
| Französisch | `<summary lang="fr">` | Recherche plein texte sans configuration dans vos fichiers, documents numérisés compris | 87 von 128 |

## `<description>` (Englisch, ohne `lang`-Attribut)

Findling finds the contents of your documents from the normal search bar.

This app never modifies your files, and no content ever leaves your server.

Findling needs two more things to be installed: the app "AppAPI" and the
External App "Findling Backend", which does the reading and the indexing inside
your own instance.

Nothing has to be configured. The first index starts on its own and runs as a
background job, and scanned PDFs are read with OCR without a setting being
touched. If this server still uses the default AJAX cron, background jobs only
run while somebody is using the web interface, and the first index will trickle
along accordingly. Switching this instance to the system cron is the difference
between hours and weeks. "occ findling:index --status" shows how far it has
come.

The search also finds documents through a paraphrase instead of only exact
words: a query that describes a notice period finds the document even if the
word never occurs in it. The semantic search covers the beginning of each
document, and the full text search still covers everything; that beginning is,
measured, 12.5 percent of an average document of the measurement corpus. What
it costs in time, measured on the same box: embedding the 51,961 documents ran
alongside the OCR for the whole run and was finished 52 minutes after it, and
the full run took 18 h 04 min for full text and OCR and 18 h 56 min until the
last vector.

What it costs in memory, measured: On a 4-GB ARM64 box with 51,961 indexed
documents and the semantic search active, the container peaked at 1,813 MB of
resident anonymous memory, under a hard 2 GB limit enforced by the kernel. That
is the target hardware and not a stand in, and it was measured on 07.09.2026.
Two honest sentences belong next to the number: all four kernel counters for
memory pressure are zero, including the one that counts how often the kernel had
to push the container back against its limit, which stood at 2,796 in the
previous measurement of 05.09.2026 with its peak of 1,838 MB; and the largest
part of this memory is now the optical character recognition, which reads three
languages since 06.09.2026, while the search phase costs 1,125 MB. The report
docs/performance.md in the source code carries the method, the curve, the corpus
and the x86 rehearsal next to it.

Privacy: everything runs locally in your own instance. No file content ever
leaves the server, and there is no telemetry of any kind, not even a version
check. What is stored, so that nobody has to guess: the text extracted from
every indexed document is kept in the backend app's own volume, because the
short excerpts shown under a search result are cut out of it on demand. A
backup of that volume therefore contains the text of your indexed documents,
and the index is not encrypted at rest, which is a matter for the host it runs
on.

The semantic model ships inside the container image, and nothing is
downloaded on first start. Two network libraries, huggingface-hub and
requests, came into the container with the embedding library; the build
pipeline starts the image with the network switched off and runs a search
against it, which is the proof that none of this ever needs a connection. No
text, no vector and no query leaves the server.

## `<description lang="de">`

Findling findet den Inhalt Ihrer Dokumente über die gewöhnliche Suchleiste.

Diese App verändert Ihre Dateien nie, und kein Inhalt verlässt Ihren Server.

Findling braucht zwei weitere Installationen: die App "AppAPI" und die External
App "Findling Backend", die das Lesen und das Indexieren innerhalb Ihrer eigenen
Instanz erledigt.

Nichts muss eingerichtet werden. Der erste Indexlauf beginnt von selbst als
Hintergrundauftrag, und gescannte PDF-Dateien werden per Texterkennung gelesen,
ohne dass eine Einstellung angefasst wird. Läuft dieser Server noch mit dem
voreingestellten AJAX-Cron, arbeiten Hintergrundaufträge nur, solange jemand die
Weboberfläche benutzt, und der erste Indexlauf tröpfelt entsprechend dahin. Die
Umstellung dieser Instanz auf den System-Cron ist der Unterschied zwischen
Stunden und Wochen. "occ findling:index --status" zeigt, wie weit er gekommen
ist.

Die Suche findet Dokumente auch über eine Umschreibung statt nur über exakte
Wörter: Eine Anfrage, die eine Kündigungsfrist beschreibt, findet das Dokument
auch dann, wenn das Wort darin nicht vorkommt. Die semantische Suche deckt den
Anfang jedes Dokuments ab, die Volltextsuche weiterhin alles. Der Anfang
heißt, gemessen, 12,5 Prozent eines durchschnittlichen Dokuments des
Messkorpus. Was es an Zeit kostet, gemessen auf derselben Box: Die Einbettung
der 51.961 Dokumente lief den ganzen Lauf neben der Texterkennung mit und war
52 Minuten nach ihr fertig, und der Volllauf brauchte 18 h 04 min für Volltext
und Texterkennung und 18 h 56 min bis zum letzten Vektor.

Was es an Arbeitsspeicher kostet, gemessen: Auf einer 4-GB-Box mit ARM64,
51.961 indexierten Dokumenten und aktiver semantischer Suche hatte der Container
seine Spitze bei 1.813 MB anonymem Arbeitsspeicher, unter einer harten Grenze
von 2 GB, die der Kernel durchsetzt. Das ist die Zielhardware und kein Ersatz,
gemessen am 07.09.2026. Zwei ehrliche Sätze gehören neben die Zahl: Alle vier
Kernel-Zähler für Speicherdruck stehen auf null, auch der, der zählt, wie oft
der Kernel den Container gegen seine Grenze zurückdrängen musste, und der stand
in der vorigen Messung vom 05.09.2026 mit ihrer Spitze von 1.838 MB noch bei
2.796; und der größte Teil dieses Speichers ist inzwischen die Texterkennung,
die seit dem 06.09.2026 drei Sprachen liest, während die Suchphase 1.125 MB
kostet. Der Bericht docs/performance.md im Quellcode nennt die Methode, die
Kurve, den Korpus und daneben die x86-Generalprobe.

Datenschutz: Alles läuft lokal in Ihrer eigenen Instanz. Kein Dateiinhalt
verlässt den Server, und es gibt keinerlei Telemetrie, nicht einmal eine
Versionsabfrage. Was gespeichert wird, damit niemand raten muss: Der aus jedem
indexierten Dokument gewonnene Text liegt im eigenen Datenspeicher der
Backend-App, weil die kurzen Auszüge unter einem Suchtreffer bei Bedarf daraus
geschnitten werden. Eine Sicherung dieses Datenspeichers enthält damit den Text
Ihrer indexierten Dokumente, und der Index ist im Ruhezustand nicht
verschlüsselt, was Sache des Wirtssystems ist.

Das semantische Modell liegt im Abbild des Containers, und beim ersten Start
wird nichts heruntergeladen. Mit der Einbettungsbibliothek sind zwei
Netzwerkbibliotheken in den Container gekommen, huggingface-hub und requests;
der Bauablauf startet das Abbild mit abgeschaltetem Netzwerk und fährt eine
Suche dagegen, und das ist der Beleg, dass nichts davon je eine Verbindung
braucht. Kein Text, kein Vektor und keine Anfrage verlässt den Server.

## `<description lang="fr">`

Findling trouve le contenu de vos documents depuis la barre de recherche
habituelle.

Cette application ne modifie jamais vos fichiers, et aucun contenu ne quitte
votre serveur.

Findling a besoin de deux installations supplémentaires : l'application "AppAPI"
et l'External App "Findling Backend", qui se charge de la lecture et de
l'indexation à l'intérieur de votre propre instance.

Rien n'est à configurer. La première indexation démarre d'elle-même comme tâche
de fond, et les PDF numérisés sont lus par reconnaissance optique de caractères
sans qu'un seul réglage soit touché. Si ce serveur utilise encore le cron AJAX
par défaut, les tâches de fond ne s'exécutent que pendant qu'une personne se
sert de l'interface web, et la première indexation avance au compte-gouttes.
Basculer cette instance sur le cron système, c'est la différence entre des
heures et des semaines. "occ findling:index --status" montre où elle en est.

La recherche trouve aussi les documents par une périphrase et non seulement
par les mots exacts : une requête qui décrit un délai de préavis trouve le
document même si le mot n'y figure pas. La recherche sémantique couvre le
début de chaque document, et la recherche plein texte couvre toujours tout ;
ce début représente, mesuré, 12,5 pour cent d'un document moyen du corpus de
mesure. Ce que cela coûte en temps, mesuré sur la même machine : le calcul
des vecteurs des 51 961 documents a accompagné la reconnaissance optique
pendant tout le passage et s'est achevé 52 minutes après elle, et le passage
complet a demandé 18 h 04 min pour le plein texte et la reconnaissance
optique, et 18 h 56 min jusqu'au dernier vecteur.

Ce que cela coûte en mémoire, mesuré : sur une machine ARM64 de 4 Go, avec
51 961 documents indexés et la recherche sémantique active, le conteneur a
culminé à 1 813 Mo de mémoire anonyme résidente, sous une limite stricte de 2 Go
imposée par le noyau. C'est le matériel cible et non un remplaçant, mesuré le
07.09.2026. Deux phrases honnêtes accompagnent ce chiffre : les quatre compteurs
du noyau pour la pression mémoire sont à zéro, y compris celui qui compte
combien de fois le noyau a dû repousser le conteneur contre sa limite, qui était
à 2 796 lors de la mesure précédente du 05.09.2026 et de son pic de 1 838 Mo ;
et l'essentiel de cette mémoire revient désormais à la reconnaissance optique,
qui lit trois langues depuis le 06.09.2026, tandis que la phase de recherche
coûte 1 125 Mo. Le rapport docs/performance.md dans le code source donne la
méthode, la courbe, le corpus et, à côté, la répétition sur x86.

Confidentialité : tout fonctionne localement dans votre propre instance. Aucun
contenu de fichier ne quitte le serveur, et il n'y a aucune télémétrie, pas même
une vérification de version. Ce qui est conservé, pour que personne n'ait à le
deviner : le texte extrait de chaque document indexé est gardé dans le volume
propre de l'application backend, parce que les courts extraits affichés sous un
résultat de recherche y sont découpés à la demande. Une sauvegarde de ce volume
contient donc le texte de vos documents indexés, et l'index n'est pas chiffré au
repos, ce qui relève de l'hôte sur lequel il tourne.

Le modèle sémantique est contenu dans l'image du conteneur, et rien n'est
téléchargé au premier démarrage. Deux bibliothèques réseau, huggingface-hub
et requests, sont entrées dans le conteneur avec la bibliothèque de calcul
des vecteurs ; la chaîne de construction démarre l'image sans aucun réseau et
lance une recherche contre elle, ce qui prouve que rien de tout cela n'a
jamais besoin d'une connexion. Aucun texte, aucun vecteur et aucune requête ne
quitte le serveur.

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

This is the External App behind the Findling search app.

It extracts text from documents, runs OCR on scanned pages and maintains the
search index. All of that happens inside your own instance: no file content
ever leaves the server, and nothing is ever written back to your files.

This app does nothing on its own. It needs the app "AppAPI", which installs and
runs it, and the app "Findling", which puts the results into the normal search
bar and is the only caller of this backend. Once both are there, nothing has to
be configured: the first index starts by itself, and scanned documents are read
with OCR without a setting being touched.

The search also finds documents through a paraphrase instead of only exact
words: a query that describes a notice period finds the document even if the
word never occurs in it. The semantic search covers the beginning of each
document, and the full text search still covers everything; that beginning is,
measured, 12.5 percent of an average document of the measurement corpus. What
it costs in time, measured on the same box: embedding the 51,961 documents ran
alongside the OCR for the whole run and was finished 52 minutes after it, and
the full run took 18 h 04 min for full text and OCR and 18 h 56 min until the
last vector.

What it costs in memory, measured: On a 4-GB ARM64 box with 51,961 indexed
documents and the semantic search active, the container peaked at 1,813 MB of
resident anonymous memory, under a hard 2 GB limit enforced by the kernel. That
is the target hardware and not a stand in, and it was measured on 07.09.2026.
Two honest sentences belong next to the number: all four kernel counters for
memory pressure are zero, including the one that counts how often the kernel had
to push the container back against its limit, which stood at 2,796 in the
previous measurement of 05.09.2026 with its peak of 1,838 MB; and the largest
part of this memory is now the optical character recognition, which reads three
languages since 06.09.2026, while the search phase costs 1,125 MB. The report
docs/performance.md in the source code carries the method, the curve, the corpus
and the x86 rehearsal next to it.

Privacy: everything runs locally in this container on your own machine. No file
content ever leaves the server, and there is no telemetry of any kind, not even
a version check. What is stored, so that nobody has to guess: the text extracted
from every indexed document is kept in this app's own volume, because the short
excerpts shown under a search result are cut out of it on demand. A backup of
that volume, including the ones an all-in-one setup takes, therefore contains
the text of your indexed documents, and the index is not encrypted at rest,
which is a matter for the host it runs on.

The semantic model ships inside the container image, and nothing is
downloaded on first start. Two network libraries, huggingface-hub and
requests, came into the container with the embedding library; the build
pipeline starts the image with the network switched off and runs a search
against it, which is the proof that none of this ever needs a connection. No
text, no vector and no query leaves the server.

## `<description lang="de">`

Dies ist die External App hinter der Such-App Findling.

Sie gewinnt Text aus Dokumenten, liest gescannte Seiten per Texterkennung und
pflegt den Suchindex. All das geschieht innerhalb Ihrer eigenen Instanz: kein
Dateiinhalt verlässt den Server, und in Ihre Dateien wird nie etwas
zurückgeschrieben.

Diese App tut von sich aus nichts. Sie braucht die App "AppAPI", die sie
installiert und betreibt, und die App "Findling", die die Ergebnisse in die
gewöhnliche Suchleiste bringt und der einzige Aufrufer dieses Dienstes ist. Sind
beide vorhanden, muss nichts eingerichtet werden: Der erste Indexlauf beginnt
von selbst, und gescannte Dokumente werden per Texterkennung gelesen, ohne dass
eine Einstellung angefasst wird.

Die Suche findet Dokumente auch über eine Umschreibung statt nur über exakte
Wörter: Eine Anfrage, die eine Kündigungsfrist beschreibt, findet das Dokument
auch dann, wenn das Wort darin nicht vorkommt. Die semantische Suche deckt den
Anfang jedes Dokuments ab, die Volltextsuche weiterhin alles. Der Anfang
heißt, gemessen, 12,5 Prozent eines durchschnittlichen Dokuments des
Messkorpus. Was es an Zeit kostet, gemessen auf derselben Box: Die Einbettung
der 51.961 Dokumente lief den ganzen Lauf neben der Texterkennung mit und war
52 Minuten nach ihr fertig, und der Volllauf brauchte 18 h 04 min für Volltext
und Texterkennung und 18 h 56 min bis zum letzten Vektor.

Was es an Arbeitsspeicher kostet, gemessen: Auf einer 4-GB-Box mit ARM64,
51.961 indexierten Dokumenten und aktiver semantischer Suche hatte der Container
seine Spitze bei 1.813 MB anonymem Arbeitsspeicher, unter einer harten Grenze
von 2 GB, die der Kernel durchsetzt. Das ist die Zielhardware und kein Ersatz,
gemessen am 07.09.2026. Zwei ehrliche Sätze gehören neben die Zahl: Alle vier
Kernel-Zähler für Speicherdruck stehen auf null, auch der, der zählt, wie oft
der Kernel den Container gegen seine Grenze zurückdrängen musste, und der stand
in der vorigen Messung vom 05.09.2026 mit ihrer Spitze von 1.838 MB noch bei
2.796; und der größte Teil dieses Speichers ist inzwischen die Texterkennung,
die seit dem 06.09.2026 drei Sprachen liest, während die Suchphase 1.125 MB
kostet. Der Bericht docs/performance.md im Quellcode nennt die Methode, die
Kurve, den Korpus und daneben die x86-Generalprobe.

Datenschutz: Alles läuft lokal in diesem Container auf Ihrer eigenen Maschine.
Kein Dateiinhalt verlässt den Server, und es gibt keinerlei Telemetrie, nicht
einmal eine Versionsabfrage. Was gespeichert wird, damit niemand raten muss: Der
aus jedem indexierten Dokument gewonnene Text liegt im eigenen Datenspeicher
dieser App, weil die kurzen Auszüge unter einem Suchtreffer bei Bedarf daraus
geschnitten werden. Eine Sicherung dieses Datenspeichers, auch die einer
All-in-One-Installation, enthält damit den Text Ihrer indexierten Dokumente, und
der Index ist im Ruhezustand nicht verschlüsselt, was Sache des Wirtssystems
ist.

Das semantische Modell liegt im Abbild des Containers, und beim ersten Start
wird nichts heruntergeladen. Mit der Einbettungsbibliothek sind zwei
Netzwerkbibliotheken in den Container gekommen, huggingface-hub und requests;
der Bauablauf startet das Abbild mit abgeschaltetem Netzwerk und fährt eine
Suche dagegen, und das ist der Beleg, dass nichts davon je eine Verbindung
braucht. Kein Text, kein Vektor und keine Anfrage verlässt den Server.

## `<description lang="fr">`

Ceci est l'External App qui se trouve derrière l'application de recherche
Findling.

Elle extrait le texte des documents, lit les pages numérisées par reconnaissance
optique de caractères et tient à jour l'index de recherche. Tout cela se passe
à l'intérieur de votre propre instance : aucun contenu de fichier ne quitte le
serveur, et rien n'est jamais réécrit dans vos fichiers.

Cette application ne fait rien d'elle-même. Elle a besoin de l'application
"AppAPI", qui l'installe et la fait tourner, et de l'application "Findling", qui
place les résultats dans la barre de recherche habituelle et qui est le seul
appelant de ce service. Une fois les deux en place, il n'y a rien à configurer :
la première indexation démarre d'elle-même, et les documents numérisés sont lus
par reconnaissance optique sans qu'un seul réglage soit touché.

La recherche trouve aussi les documents par une périphrase et non seulement
par les mots exacts : une requête qui décrit un délai de préavis trouve le
document même si le mot n'y figure pas. La recherche sémantique couvre le
début de chaque document, et la recherche plein texte couvre toujours tout ;
ce début représente, mesuré, 12,5 pour cent d'un document moyen du corpus de
mesure. Ce que cela coûte en temps, mesuré sur la même machine : le calcul
des vecteurs des 51 961 documents a accompagné la reconnaissance optique
pendant tout le passage et s'est achevé 52 minutes après elle, et le passage
complet a demandé 18 h 04 min pour le plein texte et la reconnaissance
optique, et 18 h 56 min jusqu'au dernier vecteur.

Ce que cela coûte en mémoire, mesuré : sur une machine ARM64 de 4 Go, avec
51 961 documents indexés et la recherche sémantique active, le conteneur a
culminé à 1 813 Mo de mémoire anonyme résidente, sous une limite stricte de 2 Go
imposée par le noyau. C'est le matériel cible et non un remplaçant, mesuré le
07.09.2026. Deux phrases honnêtes accompagnent ce chiffre : les quatre compteurs
du noyau pour la pression mémoire sont à zéro, y compris celui qui compte
combien de fois le noyau a dû repousser le conteneur contre sa limite, qui était
à 2 796 lors de la mesure précédente du 05.09.2026 et de son pic de 1 838 Mo ;
et l'essentiel de cette mémoire revient désormais à la reconnaissance optique,
qui lit trois langues depuis le 06.09.2026, tandis que la phase de recherche
coûte 1 125 Mo. Le rapport docs/performance.md dans le code source donne la
méthode, la courbe, le corpus et, à côté, la répétition sur x86.

Confidentialité : tout fonctionne localement dans ce conteneur, sur votre propre
machine. Aucun contenu de fichier ne quitte le serveur, et il n'y a aucune
télémétrie, pas même une vérification de version. Ce qui est conservé, pour que
personne n'ait à le deviner : le texte extrait de chaque document indexé est
gardé dans le volume propre de cette application, parce que les courts extraits
affichés sous un résultat de recherche y sont découpés à la demande. Une
sauvegarde de ce volume, y compris celle que prend une installation
tout-en-un, contient donc le texte de vos documents indexés, et l'index n'est
pas chiffré au repos, ce qui relève de l'hôte sur lequel il tourne.

Le modèle sémantique est contenu dans l'image du conteneur, et rien n'est
téléchargé au premier démarrage. Deux bibliothèques réseau, huggingface-hub
et requests, sont entrées dans le conteneur avec la bibliothèque de calcul
des vecteurs ; la chaîne de construction démarre l'image sans aucun réseau et
lance une recherche contre elle, ce qui prouve que rien de tout cela n'a
jamais besoin d'une connexion. Aucun texte, aucun vecteur et aucune requête ne
quitte le serveur.

---

## Was in den sechs Texten oben bewusst nicht steht

Dieser Abschnitt ist die Begründung und gehört nicht in eine `info.xml`. Er
nennt den ausgeschlossenen Gegenstand beim Namen, weil eine Regel, die ihren
Gegenstand verschweigt, von niemandem nachgeprüft werden kann.

- **Kein Querverweis auf den MCP Connector.** D-12 verbietet die
  Synergie-Behauptung, solange der Content-Hit-Fidelity-Test nicht bestanden
  ist. Der Trigger dafür liegt im Backlog des Connectors, nicht hier.
- **Kein Vergleich mit einer anderen Suchlösung.** Eine App, die sich über die
  Konkurrenz definiert, sagt nichts über sich selbst.
- **Kein beworbenes Tokenlimit.** Die Abdeckungsaussage steht als Anteil im
  Text; der Deckel selbst ist keine beworbene Einstellung (D-01), und eine
  Tokenzahl sagt niemandem etwas.
- **Keine gerundete Verbesserung und keine Hochrechnung.** Jede Zahl in den
  Texten ist gemessen und steht mit ihrer Messreihe in `docs/performance.md`
  oder `docs/embeddings.md`; die datierte Vergleichszahl vom 05.09.2026 ist
  Teil der zwei ehrlichen Sätze und keine zweite Zusage.
