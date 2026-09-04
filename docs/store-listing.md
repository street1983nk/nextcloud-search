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

Dieses Repository führt kein Vokabular-Gate. Gesucht wurde am 04.09.2026 in
`backend/tests` und in `scripts/ci`: es gibt Gate A bis Gate C, das
Lockstep-Gate, das Paritäts-Gate und die Wortlisten-Prüfung des deutschen
Kompositum-Wörterbuchs, aber keine Prüfung gegen eine Liste verbotener
Projektbegriffe. Es gilt daher die Regel des Owners für öffentliche Artefakte.
Der dort gesperrte Projektbegriff für einen Aufbewahrungsort kommt in der
deutschen und in der französischen Fassung unten nicht vor: sie sprechen von
einer Sicherung, von komprimierten Dateien und vom Quellcode, wo eine
naheliegende Formulierung ihn benutzt hätte. Die englische Fassung bräuchte ihn
als Dateityp-Bezeichnung, kommt unten aber ebenfalls ohne aus, weil keiner der
sechs Texte einzelne Dateitypen aufzählt.

## Die gemessene Zahl

Der Satz mit der Messung stammt aus Plan 05-14 und wird hier zitiert, nicht neu
formuliert. Er steht an drei Orten in derselben Form: in `README.md`, in
`php/appinfo/info.xml` und in `backend/appinfo/info.xml`, jeweils in der
englischen Fassung. Das Gate prüft diese Gleichheit, weil drei Orte für eine
Zahl sonst auseinanderlaufen und die Store-Beschreibung der Ort ist, an dem es
niemandem auffällt.

> A full index and OCR run over 50,000 files and 20 GB on a 4-GB box peaked at
> 429 MB of resident anonymous memory, under a hard 2 GB limit enforced by the
> kernel, with no OOM kill.

Dazu gehört in jeder Sprache der Zusatz aus dem Messbericht: die Maschine war
x86, die Wiederholung auf ARM steht aus, und `docs/performance.md` nennt jede
Zahl, die sie ersetzen wird. Eine zweite Zahl kommt nicht dazu, und gerundet
wird nichts.

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

What it costs in memory, measured: A full index and OCR run over 50,000 files
and 20 GB on a 4-GB box peaked at 429 MB of resident anonymous memory, under a
hard 2 GB limit enforced by the kernel, with no OOM kill. The machine was x86
and the repetition on ARM hardware is still open; the report docs/performance.md
in the source code carries the method, the curve and every figure that
repetition will replace.

Privacy: everything runs locally in your own instance. No file content ever
leaves the server, and there is no telemetry of any kind, not even a version
check. What is stored, so that nobody has to guess: the text extracted from
every indexed document is kept in the backend app's own volume, because the
short excerpts shown under a search result are cut out of it on demand. A
backup of that volume therefore contains the text of your indexed documents,
and the index is not encrypted at rest, which is a matter for the host it runs
on.

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

Was es an Arbeitsspeicher kostet, gemessen: Ein vollständiger Index- und
Texterkennungslauf über 50.000 Dateien und 20 GB auf einer 4-GB-Box hatte seine
Spitze bei 429 MB anonymem Arbeitsspeicher, unter einer harten Grenze von 2 GB,
die der Kernel durchsetzt, und ohne einen einzigen Abschuss wegen
Speichermangels. Die Maschine war x86, die Wiederholung auf ARM-Hardware steht
aus; der Bericht docs/performance.md im Quellcode nennt die Methode, die Kurve
und jede Zahl, die diese Wiederholung ersetzen wird.

Datenschutz: Alles läuft lokal in Ihrer eigenen Instanz. Kein Dateiinhalt
verlässt den Server, und es gibt keinerlei Telemetrie, nicht einmal eine
Versionsabfrage. Was gespeichert wird, damit niemand raten muss: Der aus jedem
indexierten Dokument gewonnene Text liegt im eigenen Datenspeicher der
Backend-App, weil die kurzen Auszüge unter einem Suchtreffer bei Bedarf daraus
geschnitten werden. Eine Sicherung dieses Datenspeichers enthält damit den Text
Ihrer indexierten Dokumente, und der Index ist im Ruhezustand nicht
verschlüsselt, was Sache des Wirtssystems ist.

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

Ce que cela coûte en mémoire, mesuré : une indexation complète avec
reconnaissance optique portant sur 50 000 fichiers et 20 Go sur une machine de
4 Go a culminé à 429 Mo de mémoire anonyme résidente, sous une limite stricte de
2 Go imposée par le noyau, et sans la moindre interruption pour manque de
mémoire. La machine était en x86, la répétition sur du matériel ARM reste à
faire ; le rapport docs/performance.md dans le code source donne la méthode, la
courbe et chaque chiffre que cette répétition remplacera.

Confidentialité : tout fonctionne localement dans votre propre instance. Aucun
contenu de fichier ne quitte le serveur, et il n'y a aucune télémétrie, pas même
une vérification de version. Ce qui est conservé, pour que personne n'ait à le
deviner : le texte extrait de chaque document indexé est gardé dans le volume
propre de l'application backend, parce que les courts extraits affichés sous un
résultat de recherche y sont découpés à la demande. Une sauvegarde de ce volume
contient donc le texte de vos documents indexés, et l'index n'est pas chiffré au
repos, ce qui relève de l'hôte sur lequel il tourne.

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

What it costs in memory, measured: A full index and OCR run over 50,000 files
and 20 GB on a 4-GB box peaked at 429 MB of resident anonymous memory, under a
hard 2 GB limit enforced by the kernel, with no OOM kill. The machine was x86
and the repetition on ARM hardware is still open; the report docs/performance.md
in the source code carries the method, the curve and every figure that
repetition will replace.

Privacy: everything runs locally in this container on your own machine. No file
content ever leaves the server, and there is no telemetry of any kind, not even
a version check. What is stored, so that nobody has to guess: the text extracted
from every indexed document is kept in this app's own volume, because the short
excerpts shown under a search result are cut out of it on demand. A backup of
that volume, including the ones an all-in-one setup takes, therefore contains
the text of your indexed documents, and the index is not encrypted at rest,
which is a matter for the host it runs on.

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

Was es an Arbeitsspeicher kostet, gemessen: Ein vollständiger Index- und
Texterkennungslauf über 50.000 Dateien und 20 GB auf einer 4-GB-Box hatte seine
Spitze bei 429 MB anonymem Arbeitsspeicher, unter einer harten Grenze von 2 GB,
die der Kernel durchsetzt, und ohne einen einzigen Abschuss wegen
Speichermangels. Die Maschine war x86, die Wiederholung auf ARM-Hardware steht
aus; der Bericht docs/performance.md im Quellcode nennt die Methode, die Kurve
und jede Zahl, die diese Wiederholung ersetzen wird.

Datenschutz: Alles läuft lokal in diesem Container auf Ihrer eigenen Maschine.
Kein Dateiinhalt verlässt den Server, und es gibt keinerlei Telemetrie, nicht
einmal eine Versionsabfrage. Was gespeichert wird, damit niemand raten muss: Der
aus jedem indexierten Dokument gewonnene Text liegt im eigenen Datenspeicher
dieser App, weil die kurzen Auszüge unter einem Suchtreffer bei Bedarf daraus
geschnitten werden. Eine Sicherung dieses Datenspeichers, auch die einer
All-in-One-Installation, enthält damit den Text Ihrer indexierten Dokumente, und
der Index ist im Ruhezustand nicht verschlüsselt, was Sache des Wirtssystems
ist.

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

Ce que cela coûte en mémoire, mesuré : une indexation complète avec
reconnaissance optique portant sur 50 000 fichiers et 20 Go sur une machine de
4 Go a culminé à 429 Mo de mémoire anonyme résidente, sous une limite stricte de
2 Go imposée par le noyau, et sans la moindre interruption pour manque de
mémoire. La machine était en x86, la répétition sur du matériel ARM reste à
faire ; le rapport docs/performance.md dans le code source donne la méthode, la
courbe et chaque chiffre que cette répétition remplacera.

Confidentialité : tout fonctionne localement dans ce conteneur, sur votre propre
machine. Aucun contenu de fichier ne quitte le serveur, et il n'y a aucune
télémétrie, pas même une vérification de version. Ce qui est conservé, pour que
personne n'ait à le deviner : le texte extrait de chaque document indexé est
gardé dans le volume propre de cette application, parce que les courts extraits
affichés sous un résultat de recherche y sont découpés à la demande. Une
sauvegarde de ce volume, y compris celle que prend une installation
tout-en-un, contient donc le texte de vos documents indexés, et l'index n'est
pas chiffré au repos, ce qui relève de l'hôte sur lequel il tourne.

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
- **Keine Zusage über semantische Suche.** Sie kommt mit Phase 6 in denselben
  Store-Eintrag; ein Text, der sie heute verspricht, wäre eine Zusage ohne
  Beleg.
- **Keine zweite Messzahl und keine gerundete Verbesserung.** Es gibt einen
  gemessenen Satz, und der steht oben.
- **Keine Screenshot-Zeilen.** Die Bilder entstehen in Plan 05-18; ein leeres
  `screenshot`-Element würde den Upload mit einem Serverfehler beenden.
