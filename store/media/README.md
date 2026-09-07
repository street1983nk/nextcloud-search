# Die Bilder des Store-Eintrags

Drei Bilder, die im Store-Eintrag beider Hälften stehen. Der Store speichert
keine Bilder, sondern nur Adressen, deshalb liegen sie hier im öffentlichen
Repository und werden über `raw.githubusercontent.com` verlinkt. Welches Element
auf welches Bild zeigt, steht in beiden `appinfo/info.xml` mit der Begründung
daneben; die sechs Texte des Eintrags stehen in `docs/store-listing.md`.

## Größe und Grenze, Bild für Bild

Der Store nimmt je Bild höchstens 2 MiB an, also 2097152 Bytes. Ein Bild
darüber beendet die Einreichung, deshalb steht die Zahl hier neben jedem Bild
und nicht als Faustregel darunter.

| Bild | Größe | Grenze |
|---|---|---|
| `header.png` | 168515 Bytes (165 KiB) | 2 MiB je Bild |
| `screenshot-admin.png` | 159786 Bytes (156 KiB) | 2 MiB je Bild |
| `screenshot-search.png` | 277061 Bytes (271 KiB) | 2 MiB je Bild |

Die Zahlen sind nicht gepflegt, sondern geprüft: `backend/tests/test_store_metadata.py`
hält jede von ihnen gegen die Datei, die wirklich in diesem Verzeichnis liegt.
Wer ein Bild austauscht und die Zahl stehen lässt, bekommt ein rotes Gate mit
der heutigen Größe in der Meldung. Eine Zahl, die beim Tippen stimmte, ist
schlechter als gar keine.

## Die Live-Bestätigung der Adressen, 07.09.2026

Der Store speichert keine Bilder, sondern Adressen. Eine Adresse, hinter der
nichts liegt, besteht jede Schemaprüfung und ergibt auf der Store-Seite einen
leeren Rahmen, und das ist schlechter als kein Bild. `test_store_metadata.py`
prüft deshalb, dass jede `screenshot`-Adresse beider `info.xml` auf eine Datei
zeigt, die in diesem Verzeichnis liegt, und es prüft das bewusst **ohne Netz**:
ein Gate, das eine fremde Seite braucht, färbt den Bau rot, wenn jemand anderes
sie umbaut. Die Bestätigung, dass die Adresse auch von aussen antwortet, ist
deshalb einmalig und von Hand, und hier steht ihr Ergebnis.

Fünf Adressen, drei Dateien: die Companion-Hälfte nennt Kopfbild, Suchbild und
Verwaltungsbild, die Backend-Hälfte nennt Kopfbild und Verwaltungsbild. Geprüft
wurde je Datei, denn zwei gleiche Adressen sind eine Abfrage.

| Bild | Status | Inhaltstyp | Größe laut Antwort | Größe laut Tabelle oben | Maße |
|---|---|---|---|---|---|
| `header.png` | 200 | `image/png` | 168515 Bytes | 168515 Bytes | 1440 x 810 |
| `screenshot-admin.png` | 200 | `image/png` | 157081 Bytes | siehe Vermerk unten | 1440 x 1100 |
| `screenshot-search.png` | 200 | `image/png` | 113724 Bytes | siehe Vermerk unten | 1440 x 700 |

Abgerufen am 07.09.2026 um 11:19 UTC über `curl` gegen den Zweig `main` bei
Stand `94420f7`, also gegen genau die Adressen, die in beiden `info.xml` stehen.

**Vermerk vom 07.09.2026, Plan 06-12:** Die beiden Screenshots wurden am selben
Tag nach dieser Bestätigung neu erzeugt (Semantik im Bild, zweite Deckungszahl,
siehe die Abschnitte unten). Die Maße sind unverändert, die Größen laut Antwort
oben sind die der abgelösten Dateien. Die Adressen zeigen auf `main`; sobald der
Stand mit den neuen Bildern dort liegt, ist die Abfrage je Datei zu wiederholen
und diese Tabelle nachzuziehen. Für `header.png` gilt die Bestätigung unverändert.

Über den Statuscode hinaus ist noch zweierlei geprüft, weil ein Statuscode allein
nur sagt, dass etwas geantwortet hat:

1. **Es ist wirklich ein Bild.** Jede der drei Antworten beginnt mit der
   PNG-Signatur, und die Maße aus dem `IHDR`-Block stimmen mit den Maßen
   überein, die weiter unten je Bild stehen.
2. **Es ist wirklich dieses Bild.** Die heruntergeladenen Bytes haben dieselbe
   SHA-256-Summe wie die Dateien, die zum Zeitpunkt der Abfrage in diesem
   Verzeichnis lagen: `511f7bb3...` für `header.png` (unverändert gültig),
   `c1c3f9aa...` für das abgelöste Verwaltungsbild, `c644294c...` für das
   abgelöste Suchbild. Die heutigen Dateien tragen `1258e50a...`
   (`screenshot-admin.png`) und `568b0748...` (`screenshot-search.png`); gegen
   diese Summen läuft die Wiederholung der Abfrage nach dem nächsten Stand auf
   `main`.

Was diese Bestätigung nicht ist: ein Dauerzustand. Die Adressen zeigen auf den
Zweig `main` und nicht auf einen Tag, und das ist Absicht (die Begründung steht
in beiden `info.xml` neben den Elementen): ein kaputtes Bild soll mit einem
Commit zu reparieren sein und nicht mit einem neuen Release. Der Preis dieser
Wahl ist, dass ein Umbau von `main` die Bilder verschieben kann. Wer
`store/media` umbaut, prüft die drei Adressen danach erneut.

## Warum die Bilder aus der Entwicklungsinstanz kommen und nicht aus CI

Die naheliegende Quelle wäre der Referenzkorpus, den die
Integrationsjobs benutzen. Er ist die falsche Quelle, und zwar nicht aus
Bequemlichkeit: Seine Dateien heißen `09-bescheid.pdf` bis `33-...`, und zehn
von ihnen sind absichtlich beschädigte PDF-Dateien, weil der Fehlerweg das ist,
worauf dieses Projekt geprüft wird. Ein Bild davon wäre ehrlich und
unattraktiv zugleich, und es zeigt gerade nicht, wofür ein Mensch diese App
installiert.

Die drei Bilder entstehen deshalb aus einem Wegwerf-Stack der
Entwicklungsumgebung mit einem eigens erzeugten Bestand von acht deutschen
Bürodokumenten. Kein Dokument darin ist echt, kein Name darin ist echt, und die
einzige Kennung, die in einem Bild vorkommt, ist das Konto `Verwaltung`.

## Die drei Bilder

### `screenshot-search.png` (1440 x 700)

**Wofür:** das Produktversprechen in einem Bild, seit Plan 06-12 das der
semantischen Suche. Die gewöhnliche Unified Search von Nextcloud, darin die
Ergebnisgruppe `File contents`; der oberste Treffer ist ein Dokument, das über
eine Umschreibung gefunden wurde und nicht über eines seiner Wörter.

**Wie es entstand:** Anmeldung als `Verwaltung`, die Suche der Kopfzeile
geöffnet, die Frage `Wann muss ich spätestens absagen, damit es nicht
weiterläuft?` getippt, gewartet, bis die Gruppe erscheint, dann aufgenommen.
Das Werkzeug ist Playwright (Chromium, ohne Fenster), das Skript liegt nicht im
Repository, weil es einen Stack braucht, den es hier nicht gibt; die Schritte
stehen unten vollständig.

**Warum genau diese Frage:** Kein inhaltstragendes Wort der Frage steht im
gefundenen Dokument `Kuendigung-Lagerflaeche-Sued.docx`, das von der
Kündigungsfrist zum Quartalsende spricht; das ist dieselbe Regel, nach der
`testdata/semantik` gebaut ist. Belegt vor der Aufnahme mit zwei Gegenproben
auf demselben Stack: dieselben Wörter als Phrase und dieselben inhaltstragenden
Wörter mit einem Minus-Operator (beides schaltet nach der Operatorregel aus
Plan 06.1-20 die Vektorseite ab) finden **nichts**. Der Treffer kann also nur
aus der semantischen Suche stammen. Die weiteren Einträge der Gruppe sind die
näheren Nachbarn des kleinen Bestands in Rangfolge, so antwortet das Produkt
wirklich.

### `screenshot-admin.png` (1440 x 1100)

**Wofür:** was ein Selfhoster sehen will, bevor er etwas installiert. **Beide**
Deckungszahlen seit Plan 06-09: der Deckungsgrad der Volltextsuche mit seinem
Nenner und darunter die zweite Zahl `Findable by meaning`, dazu die vier
Zähler, die Liste der nicht indexierten Dateien mit ihrem Grund, und die
Einzelabfrage einer Datei.

**Wie es entstand:** Anmeldung als Verwalter, Aufruf von
`/settings/admin/findling`, aufgenommen nach dem ersten Statusabruf. Ebenfalls
Playwright.

**Warum der Bestand eine beschädigte Datei enthält:** Ein Deckungsgrad von
hundert Prozent über einen Bestand ohne einen einzigen Fehler sagt über die
Diagnose nichts, und die Diagnose ist der Teil, den diese Seite leistet. Der
Bestand enthält deshalb eine kennwortgeschützte PDF-Datei, die als
`Übersprungen` mit dem Grund `Password protected` erscheint. Beide
Deckungszahlen im Bild sind damit 87 Prozent und nicht 100, und das ist die
Absicht; dass die zweite Zahl der ersten gleicht, sagt dem Betrachter genau
das Richtige, nämlich dass jedes indexierte Dokument auch einen Vektor trägt.

### `header.png` (1440 x 810)

**Wofür:** das erste Bild der Store-Seite.

**Wie es entstand:** eine HTML-Seite, die in Chromium aufgenommen wurde,
ebenfalls über Playwright. Kein erzeugtes Bild und keine Bildbearbeitung: jedes
Element ist Text oder ein Vektor.

**Die Regeln, nach denen es gebaut ist** (Bildpost-Linie des Owners):
visuell zuerst, eine Überschrift und eine Zeile darunter, Space Grotesk als
Schrift, echte SVG-Logos, keine Emojis, ruhiger Hintergrund. Die Überschrift
sagt, was die App tut, und nicht, wie sie heißt; der Name steht klein als
Wortmarke daneben.

**Das Zeichen darin** ist das Symbol dieser App aus `php/img/app-dark.svg`, also
Material Design Icons "magnify" von Pictogrammers unter Apache-2.0, mit dem
Pfad wortgleich und in `THIRD-PARTY.md` verzeichnet. Es ist ausdrücklich kein
fremdes Markenzeichen. Die Schrift ist Space Grotesk unter der SIL Open Font
License 1.1; die Datei liegt nicht im Repository, sondern wird beim Bauen
geholt.

## Die Regeln, die für alle drei gelten

| Regel | Warum |
|---|---|
| PNG, verlustfrei | Text in einem JPEG wird unscharf, und diese Bilder sind fast nur Text |
| je unter 2 MiB | Grenze des Stores je Bild, geprüft von `backend/tests/test_store_metadata.py`; die Zahlen stehen oben |
| Breite 1440 | auf einer Store-Seite noch lesbar, ohne dass die Datei groß wird |
| Adresse über `https`, höchstens 256 Zeichen | `secure-url` der Store-XSD, geprüft von `backend/tests/test_store_metadata.py` |
| kein Personenname, keine Adresse, kein fremder Dateiname | ein Store-Bild ist ein öffentliches Artefakt, und ein Bestand aus einer echten Instanz gehört nicht hinein |
| kein Emoji, kein Gedankenstrich | gilt für jedes öffentliche Artefakt dieses Projekts |
| kein Browser-Beiwerk | keine Lesezeichenleiste, keine Adresszeile, kein fremdes Konto im Nutzermenü |

## Wie die Bilder neu entstehen

Zu beachten, wenn eines der Bilder nachgebaut wird:

1. **Nicht der laufende Alltagsstack.** Er bindet die PHP-Hälfte aus dem
   Haupt-Checkout ein und trägt den Bestand des Owners. Ein Wegwerf-Stack mit
   eigenem Projektnamen, eigenem Port und eigenem Bind ist der Weg, und der
   Grund steht als DI-05-07-A in `deferred-items.md` der Phase 5.
2. **Der Bestand wird erzeugt und nicht gesammelt**, mit denselben Bausteinen
   wie `scripts/dev/build_corpus.py`. Acht Dokumente mit sprechenden deutschen
   Namen reichen, davon eines kennwortgeschützt.
3. **Die Skelettdateien müssen weg.** `skeletondirectory` auf einen leeren Wert
   setzen, BEVOR ein Konto angelegt wird. Sonst zählen die Beispielbilder von
   Nextcloud in den Nenner des Deckungsgrads, und ohne Texterkennung auf dem
   Wirtssystem landen sie als Fehlergruppe im Bild, die auf einer echten
   Installation nicht entsteht.
4. **Der Erstlauf-Assistent muss aus** (`occ app:disable firstrunwizard`), sonst
   liegt sein Fenster über der Oberfläche.
5. **Die Wortliste des deutschen Analysators** wird für einen Host-Prozess
   einmal in einem Wegwerf-Container gebaut; der Befehl und die erwartete
   Prüfsumme stehen in `docs/dev-setup.md`.
6. **SQLite und ein laufender Poller streiten sich.** Eine Anmeldung kann mit
   "database is locked" zurückkommen. Das ist keine Störung der App, sondern
   der Datenbankdialekt des Wegwerf-Stacks, und die Antwort darauf ist ein
   erneuter Versuch.
7. **Vor dem Ablegen ansehen.** Die Sichtprobe ist ein Schritt des Plans und
   keine Formalie: ob ein Bild einen Namen zeigt, der dort nicht stehen soll,
   kann keine Prüfung entscheiden.
