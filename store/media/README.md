# Die Bilder des Store-Eintrags

Vier Bilder, die im Store-Eintrag beider Hälften stehen. Der Store speichert
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
| `header.png` | 447925 Bytes (438 KiB) | 2 MiB je Bild |
| `header-backend.png` | 451825 Bytes (442 KiB) | 2 MiB je Bild |
| `screenshot-admin.png` | 159786 Bytes (156 KiB) | 2 MiB je Bild |
| `screenshot-search.png` | 277061 Bytes (271 KiB) | 2 MiB je Bild |

Die Zahlen sind nicht gepflegt, sondern geprüft: `backend/tests/test_store_metadata.py`
hält jede von ihnen gegen die Datei, die wirklich in diesem Verzeichnis liegt.
Wer ein Bild austauscht und die Zahl stehen lässt, bekommt ein rotes Gate mit
der heutigen Größe in der Meldung. Eine Zahl, die beim Tippen stimmte, ist
schlechter als gar keine.

## Die Live-Bestätigung der Adressen, 21.09.2026

Der Store speichert keine Bilder, sondern Adressen. Eine Adresse, hinter der
nichts liegt, besteht jede Schemaprüfung und ergibt auf der Store-Seite einen
leeren Rahmen, und das ist schlechter als kein Bild. `test_store_metadata.py`
prüft deshalb, dass jede `screenshot`-Adresse beider `info.xml` auf eine Datei
zeigt, die in diesem Verzeichnis liegt, und es prüft das bewusst **ohne Netz**:
ein Gate, das eine fremde Seite braucht, färbt den Bau rot, wenn jemand anderes
sie umbaut. Die Bestätigung, dass die Adresse auch von aussen antwortet, ist
deshalb einmalig und von Hand, und hier steht ihr Ergebnis.

Fünf Adressen, seit 22.09.2026 vier Dateien: die Companion-Hälfte nennt
Kopfbild, Suchbild und Verwaltungsbild, die Backend-Hälfte nennt ihr eigenes
Kopfbild `header-backend.png` und das Verwaltungsbild. Achtung Release-Stand:
die im Store liegende 1.2.0 traegt noch die info.xml, in der BEIDE Haelften auf
`header.png` zeigen; die Backend-Adresse `header-backend.png` reist erst mit dem
naechsten Release. Bis dahin zeigt die Backend-Store-Seite das Companion-Kopfbild.
Geprüft wurde je Datei, denn zwei gleiche Adressen sind eine Abfrage.

| Bild | Status | Inhaltstyp | Größe laut Antwort | Größe laut Tabelle oben | Maße |
|---|---|---|---|---|---|
| `header.png` | 200 | `image/png` | 327635 Bytes | 327635 Bytes | 1440 x 810 |
| `screenshot-admin.png` | 200 | `image/png` | 159786 Bytes | 159786 Bytes | 1440 x 1100 |
| `screenshot-search.png` | 200 | `image/png` | 277061 Bytes | 277061 Bytes | 1440 x 700 |

Abgerufen am 21.09.2026 um 12:56 UTC über `curl` gegen den Zweig `main` bei
Stand `1f6f85c`, also gegen genau die Adressen, die in beiden `info.xml`
stehen.

Damit ist die Wiedervorlage geschlossen, die seit dem 07.09.2026 offen stand,
also vierzehn Tage lang: die Größe laut Antwort und die Größe laut Tabelle oben
sind für alle drei Dateien dieselbe Zahl, und die Spalte "siehe Vermerk unten"
ist damit erledigt. Der Vermerk selbst steht weiter unten und ist nicht
gelöscht, weil an ihm ablesbar bleibt, wie lange die Frage offen war.

Über den Statuscode hinaus ist wieder zweierlei geprüft, weil ein Statuscode
allein nur sagt, dass etwas geantwortet hat:

1. **Es ist wirklich ein Bild.** Jede der drei Antworten beginnt mit der
   PNG-Signatur, und die Maße aus dem `IHDR`-Block stimmen mit den Maßen
   überein, die weiter unten je Bild stehen.
2. **Es ist wirklich dieses Bild.** Die heruntergeladenen Bytes sind byteweise
   dieselben wie die Dateien, die heute in diesem Verzeichnis liegen, und ihre
   SHA-256-Summen sind die der heutigen Dateien und nicht mehr die der
   abgelösten: `22cc597d...` (`header.png`), `1258e50a...`
   (`screenshot-admin.png`) und `568b0748...` (`screenshot-search.png`). Das
   sind genau die drei Summen, gegen die der Vermerk vom 07.09.2026 die
   Wiederholung angekündigt hat.

**Vermerk vom 07.09.2026, Plan 06-12, überholt am 21.09.2026 durch Plan
16-12:** Die beiden Screenshots wurden am selben Tag nach der damaligen
Bestätigung neu erzeugt (Semantik im Bild, zweite Deckungszahl, siehe die
Abschnitte unten). Die Maße sind unverändert, die Größen laut Antwort waren
damals die der abgelösten Dateien: 168515 Bytes für `header.png`, 157081 Bytes
für `screenshot-admin.png` und 113724 Bytes für `screenshot-search.png`, und
die Prüfsummen `511f7bb3...`, `c1c3f9aa...` und `c644294c...` gehörten
ebenfalls den abgelösten Dateien. Die Adressen zeigen auf `main`; sobald der
Stand mit den neuen Bildern dort liege, sei die Abfrage je Datei zu wiederholen
und die Tabelle nachzuziehen. `header.png` wurde am 07.09.2026 abends auf
Owner-Anweisung ebenfalls ersetzt (visuell statt textlastig, Abnahme im Chat);
die Wiederholung der Abfrage galt damit für alle drei Dateien. Sie ist am
21.09.2026 gefahren worden, und ihr Ergebnis steht oben.

**Vermerk vom 22.09.2026: Kopfbilder ersetzt auf Owner-Anweisung.**
`header.png` ist seit dem 22.09.2026 das neue Findling-Kopfbild (Motiv unten),
`header-backend.png` kommt als viertes Bild dazu. Die Tabelle der
Live-Bestätigung oben beschreibt damit fuer `header.png` einen abgeloesten
Stand (327635 Bytes, 1440 x 810, Pruefsumme `22cc597d...`); Die Wiederholung
der Abfrage ist am 22.09.2026 nach dem Push gefahren (curl gegen main bei
Stand `8335ca1`): `header.png` HTTP 200, `image/png`, 447925 Bytes, 1376 x 768,
PNG-Signatur, byteweise identisch mit der Datei hier, SHA-256 `5c29107f...`;
`header-backend.png` HTTP 200, `image/png`, 451825 Bytes, 1376 x 768,
PNG-Signatur, byteidentisch, SHA-256 `5719bf6c...`. Such- und Verwaltungsbild
sind unveraendert und behalten die Bestaetigung vom 21.09.2026 oben. Der Owner-Entscheid Q-6 vom 21.09.2026 ("Bilder
bleiben") ist damit fuer das Kopfbild ueberholt; Such- und Verwaltungsbild
bleiben unveraendert.

**Owner-Entscheid vom 21.09.2026 zu Q-6, im Wortlaut: "Bilder bleiben."** Die
drei Bilder vom 07.09.2026 reisen mit 1.2.0 mit, und es gibt keinen Plan für
neue Store-Bilder in dieser Phase. Was damit bewusst in Kauf genommen ist:
`screenshot-admin.png` zeigt die Verwaltungsseite im Stand vom 07.09.2026 und
damit ohne den sechsten Engine-Zustand aus Phase 14. Wer die Bilder später
erneuert, zieht diese Tabelle danach ein zweites Mal nach.

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

### `header.png` (1376 x 768)

**Wofür:** das erste Bild der Store-Seite der Companion-Hälfte.

**Wie es entstand (Fassung vom 22.09.2026, Owner-Anweisung im Chat):** mit
einem Bildmodell erzeugt (Nano Banana in gemini.google.com, Prompt-Datei
`Desktop/app-bilder/prompt-findling.txt`, eingefügt vom Owner), danach der
Schriftzug `Findling` unten zentriert per Pillow gesetzt (Segoe UI Bold,
Farbe `#0A1728`, dieselbe wie die Modell-Headline). Kein weiterer Eingriff,
nichts aus dem Modellbild entfernt.

**Was es zeigt:** links ein Dokumentstapel mit einem verschwommenen Scan und
der Plakette `OCR`; in der Mitte ein blauer Scan-Balken, über dem die Zeilen
unscharf und unter dem dieselben Zeilen scharf sind (Texterkennung als Bild);
rechts eine Lupe über einer gelb markierten Fundzeile mit grünem Haken, darüber
die Headline `Semantic Search`. Unten der Schriftzug `Findling`. Aller Text im
Bild ist Zeichen für Zeichen geprüft (Regel vom 08.09.2026). Kein fremdes
Markenzeichen im Bild.

### `header-backend.png` (1376 x 768)

**Wofür:** das erste Bild der Store-Seite der Backend-Hälfte, sobald die
Adresse mit dem nächsten Release reist (siehe Vermerk oben).

**Wie es entstand:** identisches Modellbild wie `header.png`, unten zentriert
der Schriftzug `Findling Backend` statt `Findling`, gesetzt mit demselben
Pillow-Schritt (Segoe UI Bold, `#0A1728`). Beide Hälften bleiben damit visuell
ein Paar und sind trotzdem unterscheidbar.

## Die Regeln, die für alle vier gelten

| Regel | Warum |
|---|---|
| PNG, verlustfrei | Text in einem JPEG wird unscharf, und diese Bilder sind fast nur Text |
| je unter 2 MiB | Grenze des Stores je Bild, geprüft von `backend/tests/test_store_metadata.py`; die Zahlen stehen oben |
| Breite um 1400 (Bestand: 1440 und 1376) | auf einer Store-Seite noch lesbar, ohne dass die Datei groß wird |
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
