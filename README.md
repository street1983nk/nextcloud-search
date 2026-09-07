Deutsch | [English](README.en.md) | [Français](README.fr.md)

# Findling

Zero-Config-Volltextsuche und semantische Suche für Nextcloud.

Findling sorgt dafür, dass die Nextcloud-Suche findet, was in Ihren Dokumenten
steht, auch in gescannten PDFs, ohne Elasticsearch-Cluster und ohne eine einzige
Pflichteinstellung. Die Treffer erscheinen in der normalen Unified-Search-Leiste,
neben Dateien, Kontakten und Kalendereinträgen.

## Was sie findet

- **Wörter, die im Dokument stehen**, mit der deutschen Behandlung, die eine
  Suche braucht: Komposita über einen ihrer Bestandteile, Flexion, die
  ausgeschriebene Umlautvariante, Phrasen, Ausschlüsse und ein Dateityp-Filter.
- **Text auf gescannten Seiten**, per OCR, auf Deutsch, Englisch,
  Französisch und in den DACH-Schreibweisen. Die drei Sprachen sind ab Werk
  an, es ist keine Einstellung nötig. Die Suche selbst bleibt auf Deutsch und
  Englisch abgestimmt: eine französische Seite wird gelesen und gefunden, aber
  ohne französische Stammformen.
- **Dokumente, die Sie beschreiben statt zitieren.** Eine Anfrage, deren Wörter
  nicht im Dokument stehen, kann es trotzdem zurückbringen, weil ein lokales
  Embedding-Modell nach Bedeutung rankt, neben dem Wortindex.

Der ehrliche Satz zum dritten Punkt, und es ist derselbe Satz in beiden
Store-Beschreibungen: **die semantische Suche deckt den Anfang jedes Dokuments
ab, die Volltextsuche weiterhin alles davon.** Wie viel „der Anfang“ ist, hängt
vom Dokument ab, und auf dem gemessenen Korpus sind es 12,5 Prozent eines
durchschnittlichen Dokuments. Das Modell läuft im Container, auf der CPU, und
dafür verlässt kein Text die Maschine. Die Details, die gemessene Qualität in
drei Sprachen und die beiden Belege, dass der Container dafür kein Netzwerk
braucht, stehen in [docs/embeddings.md](docs/embeddings.md).

Nicht jede Anfrage bekommt diese zweite Liste, und die beiden Ausnahmen sind
Absicht. Eine Anfrage mit Anführungszeichen, einem Minus, einem Feldpräfix,
einem Dateityp oder einem der Grammatikwörter AND, OR und NOT wird allein vom
Wortindex beantwortet: wer so sucht, hat um Exaktheit gebeten, und eine nach
Bedeutung gerankte Liste weiß davon nichts. Auch eine Anfrage aus einem
einzigen Wort wird genauso beantwortet, weil ein einzelnes Wort messbar nicht
näher am Dokument liegt, das es meint, als ein unverwandtes Wort, und der
Kompositazerleger, der Stemmer und die Umlautvariante decken das bereits ab.
Zwei oder mehr Wörter ohne einen solchen Operator werden von beiden Hälften
zusammen beantwortet.

**Status: Härtung vor der ersten Store-Veröffentlichung, noch nicht
eingereicht.** Indexierung, OCR und Suche funktionieren und sind auf
gemieteter Hardware gemessen, siehe unten. Die Auslieferungsdateien beider
Apps werden vorbereitet, bis sie im Store stehen, bitte nicht auf einem
Produktivserver installieren.

## Das Zwei-App-Modell

Findling wird als zwei zusammengehörige Store-Einträge ausgeliefert:

| Teil | App-ID | Store-Bereich | Was er macht |
|------|--------|---------------|--------------|
| PHP-Companion | `findling` | Apps | Registriert den Suchanbieter und leitet Anfragen an das Backend weiter |
| Python-ExApp | `findling_backend` | External Apps | Führt Extraktion, OCR und den Suchindex im Container aus |

Beide Einträge müssen installiert sein und tragen immer dieselbe Major- und
Minor-Version. Der Companion ist bewusst winzig: er gehört zur Nextcloud-Seite,
samt Berechtigungsprüfung, weil Nextcloud keinen Suchanbieter aus einer
externen App registrieren kann. Der Container übernimmt die schwere Arbeit.

## Voraussetzungen

- Nextcloud 33 bis 35 (`min-version` 33, `max-version` 35). Nextcloud 32 ist
  mit der Entscheidung vom 2026-09-06 aus dem unterstützten Fenster
  herausgefallen: es verliert im September 2026 den Support, diese App wird im
  Dezember eingereicht, und eine App, die einen Server für sich beansprucht,
  den niemand mehr unterstützt, behauptet damit etwas, das sie nicht einlösen
  kann.
- Die AppAPI-App, mit HaRP als Deploy-Ziel
- Zielhardware: 4 bis 8 GB RAM, ARM64 und AMD64, nur CPU, keine GPU nötig

Das Projekt ist für Selfhoster und kleine Organisationen auf gewöhnlicher
Hardware gebaut, nicht für einen Suchcluster.

## Was es an Speicher kostet, gemessen

**Auf einer 4-GB-ARM64-Box mit 51.961 indexierten Dokumenten und aktiver
semantischer Suche erreichte der Container einen Spitzenwert von 1.813 MB
residentem anonymem Speicher, unter einem harten, vom Kernel durchgesetzten
2-GB-Limit. Die drei Kernel-Zähler für Speicherschaden (`oom`, `oom_kill`,
`oom_group_kill`) stehen auf null, und der vierte Zähler `max`, der zählt, wie
oft der Kernel den Container gegen sein Limit zurückdrängen musste, steht
ebenfalls auf null.** Gemessen am 07.09.2026
([docs/measurements/2026-09-nachmessung-m7g](docs/measurements/2026-09-nachmessung-m7g/)).

`max` wird hier ausgewiesen und nicht verschwiegen, weil er in der vorigen
Messung nicht null war: der Dateicache des Index drückte damals 2.796-mal gegen
das 2-GB-Limit. Kein Prozess wurde getötet, aber der Kernel musste arbeiten.
Diesmal musste er das kein einziges Mal.

**Die vorige Zahl, als Vergleich:** 1.838 MB, gemessen am 05.09.2026 im
Semantik-Volllauf
([docs/measurements/2026-09-05-semantiklauf-m7g](docs/measurements/2026-09-05-semantiklauf-m7g/)),
mit `max 2.796`. Der Grund der Differenz ist keine Messstreuung: die Suchseite
lud damals eine zweite Kopie des Modells zusätzlich zu der, die der Indexierer
hielt. Diese Kopie ist beseitigt, und die Suchphase ist dadurch von 1.838 MB auf
1.125 MB gefallen. Dass die Gesamtspitze nur um 25 MB gesunken ist, hat einen
eigenen Grund: sie entsteht inzwischen in der OCR-Phase und nicht mehr in der
Suche, und die OCR arbeitet seit dem 06.09.2026 mit drei Sprachen statt zwei.
Beide Zahlen stehen mit ihrem Datum und ihrer Begründung im Messbericht.

**Gleichzeitige Suchen:** bis zu **acht** halten auf dieser Box das Zeitbudget
von 2,5 Sekunden ein (95. Perzentil 1,9 s über 410 Anfragen). Ab zwölf reißt es.
Das ist eine Zahl über diese Box und diese Instanz: die Nextcloud-Suche fragt
alle Anbieter gleichzeitig, also setzt auch der PHP-Prozesspool der Instanz eine
Grenze, und der ist überall anders groß.

**Der Volllauf, aus dem der Bestand stammt:** 50.000 Dateien und 20 GB, 18 h
56 min bis zum letzten Vektor, ein 785 MB großer Wortindex und ein 69 MB großer
Vektorspeicher, und jede Datei mit einem Befund: 51.961 indexiert und mit
Embeddings versehen, 37 übersprungen mit benanntem Grund, **keine einzige
fehlgeschlagen**. Eine Nutzersuche während des Laufs antwortete beim 95.
Perzentil in 1,1 Sekunden, nach dem Lauf in 0,5 Sekunden.

Das sind Messungen und keine Schätzungen. Sie wurden auf arm64 mit 2 Kernen und
4 GB genommen, der Hardware, für die diese App gebaut ist. Diese Laufzeiten
stammen von der kleinsten unterstützten Zielhardware und sind bewusst die
Untergrenze: auf moderner, leistungsstarker Hardware läuft die Indexierung
erheblich schneller, dafür liegt aber keine eigene Messung vor. Ein ehrlicher
Satz gehört noch daneben: der größte Teil dieses Speichers ist die semantische
Suche, nicht die Indexierung. Derselbe Volllauf ohne Embeddings erreichte einen
Spitzenwert von 422 MB und brauchte 12 h 49 min auf derselben Maschine.

Methode, beide vollständigen Kurven, der Korpus, der vierteilige OOM-Beleg,
vier Ausfalltests auf derselben Maschine (`docker kill` während der OCR, ein
Neustart der gesamten Maschine, Backend weg, Festplatte fast voll), die
Aufschlüsselung dessen, was die semantische Suche im Leerlauf kostet, und
eine Nebenmessung mit einem zweiten Index-Worker stehen in
[docs/performance.md](docs/performance.md), einschließlich dessen, was jede
davon nicht beweist.

## Datenschutz

- Kein Dateiinhalt verlässt den Server. Extraktion, OCR, Indexierung und Suche
  laufen alle im Container auf Ihrer eigenen Maschine.
- Gespeichert wird der extrahierte Text. Der Text jedes indexierten Dokuments
  liegt im eigenen Datenbereich der Backend-App, weil die Ausschnitte, die
  unter einem Suchtreffer angezeigt werden, bei Bedarf daraus herausgeschnitten
  werden. Eine Sicherung dieses Datenbereichs enthält deshalb den Text Ihrer
  indexierten Dokumente, und der Index ist nicht verschlüsselt gespeichert,
  was Sache des Hosts ist, auf dem er läuft. Derselbe Absatz steht in beiden
  Store-Beschreibungen, in allen drei Sprachen.
- Keine Telemetrie. Die App telefoniert nicht nach Hause, nicht einmal für
  Versionsprüfungen.
- Nutzerdateien werden nie verändert. Jeder Dateizugriff läuft über ein nur
  lesendes Content-Gateway, und ein Prüfsummen-Gate in der CI belegt diese
  Invariante an einem Referenzkorpus.
- Berechtigungen werden von Nextcloud selbst durchgesetzt. Der finale
  Ergebnisfilter läuft in PHP gegen den Benutzerordner, damit der Index nie zu
  einem zweiten Berechtigungsmodell wird.

## Repository-Aufbau

```
php/               PHP-Companion-App, in der CI auf apps/findling gemappt
backend/           Python-ExApp, Paket unter backend/src/findling/
testdata/corpus/   Referenzkorpus für das nur lesende Prüfsummen-Gate
docs/              Prozess- und Betriebsdokumentation
.github/workflows/ CI: python, php, integration, docker
```

## Lizenz

AGPL-3.0-or-later. Siehe [LICENSE](LICENSE).
