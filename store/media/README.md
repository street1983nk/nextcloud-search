# Die Bilder des Store-Eintrags

Drei Bilder, die im Store-Eintrag beider Hälften stehen. Der Store speichert
keine Bilder, sondern nur Adressen, deshalb liegen sie hier im öffentlichen
Repository und werden über `raw.githubusercontent.com` verlinkt. Welches Element
auf welches Bild zeigt, steht in beiden `appinfo/info.xml` mit der Begründung
daneben; die sechs Texte des Eintrags stehen in `docs/store-listing.md`.

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

**Wofür:** das Produktversprechen in einem Bild. Die gewöhnliche Unified Search
von Nextcloud, darin eine Ergebnisgruppe `File contents` mit zwei Treffern und
je einem Auszug aus dem Text des Dokuments.

**Wie es entstand:** Anmeldung als `Verwaltung`, die Suche der Kopfzeile
geöffnet, das Wort `Kündigungsfrist` getippt, gewartet, bis die Gruppe
erscheint, dann aufgenommen. Das Werkzeug ist Playwright (Chromium, ohne
Fenster), das Skript liegt nicht im Repository, weil es einen Stack braucht, den
es hier nicht gibt; die Schritte stehen unten vollständig.

**Warum genau dieses Wort:** `Kündigungsfrist` steht im Inhalt von zwei
Dokumenten und in keinem Dateinamen. Ein Wort, das auch im Namen stünde, würde
ein Bild der Dateiliste ergeben und nicht eines dieser App.

### `screenshot-admin.png` (1440 x 1100)

**Wofür:** was ein Selfhoster sehen will, bevor er etwas installiert. Der
Deckungsgrad mit seinem Nenner, die vier Zähler, die Liste der nicht
indexierten Dateien mit ihrem Grund, und die Einzelabfrage einer Datei.

**Wie es entstand:** Anmeldung als Verwalter, Aufruf von
`/settings/admin/findling`, aufgenommen nach dem ersten Statusabruf. Ebenfalls
Playwright.

**Warum der Bestand eine beschädigte Datei enthält:** Ein Deckungsgrad von
hundert Prozent über einen Bestand ohne einen einzigen Fehler sagt über die
Diagnose nichts, und die Diagnose ist der Teil, den diese Seite leistet. Der
Bestand enthält deshalb eine kennwortgeschützte PDF-Datei, die als
`Übersprungen` mit dem Grund `Password protected` erscheint. Der Deckungsgrad
im Bild ist damit 87 Prozent und nicht 100, und das ist die Absicht.

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
| je unter 2 MiB | Grenze des Stores je Bild; alle drei liegen unter 200 KiB |
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
