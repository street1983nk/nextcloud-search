# 46-03: Fehlerliste unter 360 px, Varianten und Messung

Stand: 2026-11-27, Kopf a41bc81e (Code wie 1.7.0 in php/css und php/templates). Dev-Instanz `findling-vt` (Nextcloud 34.0.3, nur der Dienst app, Begleit-App aus dem Arbeitsbaum), gestartet im Fenster `Freigabe Docker-Fenster 46-03` nach `docker ps -q` leer und 4,5 GiB freiem RAM, danach gestoppt. Saat: die Fehlerliste der Volltest-Instanz aus 45 (drei Gruppen, darunter "Bild ohne erkennbare Schrift" und "Für die gefragten Nutzer nicht lesbar"). Browser: Chromium headless 147.0.7727.15 (Playwright 1.59.1) per Skript, das Playwright-MCP war in dieser Sitzung getrennt. Die Varianten lagen nur ungestaged im Arbeitsbaum und sind verworfen; der Arbeitsbaum ist sauber.

## Messmethode

Je Sprache, Breite und Thema: Anmeldung als admin, Sprache und Locale per occ, Aufruf der Admin-Seite, Bild nur von `#findling-errors` (Kopfleiste von Nextcloud für das Bild ausgeblendet). Gemessen in derselben Seite:

- **Brüche gesamt:** Zeilenumbrüche zwischen zwei Buchstaben in allen sichtbaren `th` und `td` der Tabelle, bestimmt über `Range.getClientRects()` je Zeichen. Silbentrennungen von `hyphens: auto` zählen hier mit, weil ihr Bindestrich nicht im DOM steht.
- **Brüche ohne Silbentrennung ("bare"):** dieselbe Zählung, nachdem für die Tabelle `hyphens: manual` gesetzt ist. Das entspricht einem Browser ohne Trennwörterbuch für die Sprache; jeder Bruch hier ist ein Wort, das `overflow-wrap: anywhere` mitten im Wort ohne Bindestrich teilt. Das ist der Befund I-45-10-08 (der Chrome der Abnahme 45 brach "Nutz|er" und "lesb|ar", Bild `abn/22-v07-de-320-light.png`). Ziel von ADM-05: bare = 0 bei 320 px.
- **Waagerechtes Scrollen:** `scrollWidth - clientWidth` der Seite, mit und ohne Silbentrennung.
- **Accessibility-Baum:** `ariaSnapshot()` der Tabelle bei 320 und 1280 px (DE), dazu die Zahl der Elemente mit der id `findling-errors-count-...` (Live-Anzahl, admin.js Z. ~746).

Erkenntnis nebenbei: Der hier benutzte Chromium trennt DE und FR mit `hyphens: auto` ("er-kennbare", "reconnais-sable"); der Befund aus 45 trat in einem Browser ohne Trennung auf. Deshalb ist "bare" das Maß, und nicht die Zählung im Messbrowser allein.

## Positivkontrolle

Stand 1.7.0 (`base-*`), hell:

| Sprache | 320 px bare | 375 px bare | 1280 px bare | Brüche gesamt 320 / 375 / 1280 |
|---|---|---|---|---|
| DE | 3 ("Textin\|halt", "erkenn\|bare", "gefrag\|ten") | 0 | 0 | 11 / 10 / 3 |
| EN | 0 | 0 | 0 | 2 / 3 / 0 |
| FR | 1 ("reconnaissabl\|e") | 0 | 0 | 8 / 6 / 1 |

Der Befund ist damit reproduziert (DE und FR bei 320 px), 375 und 1280 px sind frei wie in 45 abgenommen. Kontrolle der Methode: bei 240 px meldet sie auch das Überlaufen der Tabelle.

## Variante A

Der Chip steht unter 360 px als zweite Fassung im Zeilenkopf (`th`) unter dem Grund; Kopf und Zellen der Spalte "Zustand" sind unter 360 px `display: none`, die zweite Fassung ab 360 px `display: none`. Template: eine `span.findling-errors__state-narrow` mit demselben `$chip()` im `th`.

Ergebnis DE, EN, FR je 320, 375, 1280 px, hell und dunkel (18 Bilder `A-*`): bare 0 überall, kein waagerechtes Scrollen. Brüche gesamt bei 320 px: DE 6, EN 2, FR 7 (statt 11, 2, 8). 375 und 1280 px wie 1.7.0.

Accessibility: Zustand zu jeder Breite genau einmal im Baum. Bei 320 px wird er aber Teil des Zeilenkopfs: `rowheader "Kein Textinhalt Übersprungen"`, Zeile `"Kein Textinhalt Übersprungen 7"`. Ein Screenreader liest den Zustand dann als Teil des Namens der Zeile. Live-Anzahl unberührt (3 ids, eindeutig).

## Variante B

Unter 360 px eine eigene Tabellenzeile je Gruppe (`tr.findling-errors__state-row`, eine Zelle über drei Spalten) mit dem Chip, direkt unter der Gruppenzeile; Spalte "Zustand" wie bei A ausgeblendet, die Zeile ab 360 px `display: none`. Kein `display: block` an Tabellenzellen.

Ergebnis DE, EN, FR je 320, 375, 1280 px, hell und dunkel (18 Bilder `B-*`): bare 0 überall, kein waagerechtes Scrollen; Brüche gesamt bei 320 px gleich A (DE 6, EN 2, FR 7). 375 und 1280 px wie 1.7.0.

Accessibility: Zustand zu jeder Breite genau einmal im Baum. Der Zeilenkopf bleibt `"Kein Textinhalt"`, die Gruppenzeile heißt `"Kein Textinhalt 7"`, der Zustand steht als eigene Zeile `"Übersprungen"` darunter, ohne eigenen Zeilenkopf. Live-Anzahl unberührt (3 ids, eindeutig).

## Vergleich

| | A (Chip im Zeilenkopf) | B (eigene Zeile) |
|---|---|---|
| bare bei 320 px, DE/EN/FR hell und dunkel | 0 | 0 |
| Optik bei 320 px | Chip direkt unter dem Grund, Abstand zur Beschreibung wie vorher | Chip unter dem Grund, etwas enger an der Beschreibung |
| Zeilenkopf für Screenreader bei 320 px | "Kein Textinhalt Übersprungen" (Zustand im Namen) | "Kein Textinhalt" (unverändert) |
| Zustand für Screenreader bei 320 px | im Zeilenkopf | eigene Zeile ohne Kopf |
| Template | eine span im th | eine Tabellenzeile je Gruppe |
| Live-Anzahl (admin.js) | unberührt | unberührt |

Bilder für den Vergleich: `bilder/layout/base-de-320-light.png`, `A-de-320-light.png`, `B-de-320-light.png`, dazu `A-de-320-dark.png`, `B-de-320-dark.png`, `A-fr-320-light.png`, `B-fr-320-light.png`; 375 und 1280 px je Variante zum Abgleich mit 1.7.0.

## Empfehlung

Beide Varianten erfüllen ADM-05 gleich gut (bare 0, kein Scrollen, 375 und 1280 px unverändert). Empfehlung: **A**. Der Chip sitzt sichtbar eindeutig bei seinem Grund, das Template wächst nur um eine span, und dass der Zustand bei 320 px Teil des Zeilenkopfs wird, ist für einen Screenreader eher hilfreich ("Kein Textinhalt Übersprungen, 7"). Bei B steht der Zustand als lose Zeile ohne Bezug zu ihrem Grund, das ist der schwächere Zustand für Screenreader. Ein Abbruch nach dem Kriterium aus 46-03 (Variante C) ist nicht nötig.

## Entscheid

`Entscheid Layout 46-03` = A (Owner "Ok", 46-FREIGABEN.md).

## Ergebnis

Gebaut wie Variante A, RED e6932901, GREEN siehe 46-03-SUMMARY.md. Messung am GREEN-Stand im Fenster `Freigabe Docker-Fenster 46-03 Messung` (4,3 GiB frei, `docker ps -q` leer, nur der Dienst app, danach gestoppt), ausgeliefertes admin.css mit der neuen Regel per HTTP geprüft, Template-Stand im Accessibility-Baum bestätigt (drei Kopien im Zeilenkopf, bei 320 px sichtbar, bei 1280 px keine).

| Sprache | Thema | bare 320 / 375 / 1280 | Brüche gesamt 320 / 375 / 1280 | waagerechtes Scrollen |
|---|---|---|---|---|
| DE | hell | 0 / 0 / 0 | 6 / 10 / 3 | 0 |
| DE | dunkel | 0 / 0 / 0 | 6 / 10 / 3 | 0 |
| EN | hell | 0 / 0 / 0 | 2 / 3 / 0 | 0 |
| EN | dunkel | 0 / 0 / 0 | 2 / 3 / 0 | 0 |
| FR | hell | 0 / 0 / 0 | 7 / 6 / 1 | 0 |
| FR | dunkel | 0 / 0 / 0 | 7 / 6 / 1 | 0 |

Accessibility (DE): bei 320 px Zeile "Kein Textinhalt Übersprungen 7", Zeilenkopf "Kein Textinhalt Übersprungen"; bei 1280 px Zeile "Kein Textinhalt 7 Übersprungen", Zeilenkopf "Kein Textinhalt" wie in 1.7.0. "Übersprungen" je Breite gleich oft im Baum wie in 1.7.0, drei Zähler-ids, eindeutig. Bilder `bilder/layout/green-*.png` (18).
