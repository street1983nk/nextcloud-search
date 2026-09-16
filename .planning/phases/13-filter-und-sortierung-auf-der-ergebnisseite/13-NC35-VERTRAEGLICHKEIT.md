# Phase 13: Verträglichkeit mit Nextcloud 35

**Angelegt:** 2026-09-16, nach Welle 2, vor Welle 6
**Anlass:** Nextcloud Hub 26 Summer (Serverversion 35) ist am 15.09.2026 erschienen,
der Ankündigungstext vom 16.09.2026 führt "Unified Search redesign" ausdrücklich als
Funktion auf. Die Pläne 13-06 (Datumsfilter des Unified-Search-Dialogs) und 13-10
(Stil der Filterleiste) beruhen auf Recherche, die vor diesem Release entstanden ist.
Diese Notiz prüft beide Grundlagen nach, damit die Wellen 6 und 9 nicht auf einer
veralteten Annahme bauen.

**Ergebnis: beide Pläne sind unverändert gültig. Kein Plan muss angefasst werden.**

---

## 1. Der Provider-Vertrag: inhaltlich unverändert

Verglichen wurden die Zweige `stable34` und `stable35` von `nextcloud/server`, Datei für
Datei über die Inhalts-Schnittstelle von GitHub.

| Datei | Befund |
|---|---|
| `lib/public/Search/IFilter.php` | eine geänderte Zeile, leer |
| `lib/public/Search/IFilteringProvider.php` | eine geänderte Zeile, leer |
| `lib/public/Search/IProvider.php` | eine geänderte Zeile, leer |
| `lib/public/Search/ISearchQuery.php` | eine geänderte Zeile, leer |
| `lib/public/Search/SearchResult.php` | eine geänderte Zeile, leer |
| `lib/public/Search/SearchResultEntry.php` | eine geänderte Zeile, leer |
| `lib/public/Search/FilterDefinition.php` | eine geänderte Zeile, leer |
| `lib/private/Search/SearchComposer.php` | eine geänderte Zeile, leer |
| `core/Controller/UnifiedSearchController.php` | eine geänderte Zeile, leer |

Die eine Zeile ist in allen neun Fällen dieselbe: eine Leerzeile, die zwischen den
SPDX-Lizenzkopf und die `namespace`-Anweisung eingezogen wurde. Es gibt keine
inhaltliche Änderung.

**Folge für 13-06.** Die Annahmen des Plans gelten weiter: `SearchComposer::buildFilter()`
wirft weiterhin bei einem nicht deklarierten exklusiven Filter, der
`UnifiedSearchController` antwortet weiterhin mit 400 für diesen Provider, und
`IFilter::BUILTIN_SINCE` sowie `IFilter::BUILTIN_UNTIL` heißen weiterhin so. Das
angekündigte Redesign der Unified Search hat ausschließlich die Oberfläche betroffen,
nicht den Vertrag, an dem `php/lib/Search/Provider.php` hängt.

## 2. Die Stilmittel: alle vorhanden

Geprüft wurde gegen das ausgelieferte Release `nextcloud-35.0.0.zip`
(SHA-256 `552b13b3ee32ba8892aa02578c2ff10ea46cbd83d3bfcfbc4317a26d359aa39a`, gegen die
mitgelieferte Prüfsummendatei verifiziert), genauer gegen
`apps/theming/lib/Themes/` und `core/css/`.

Alle 21 CSS-Variablen, die `php/css/search.css` heute benutzt, sind in Nextcloud 35
weiterhin definiert. Keine davon ist entfallen oder umbenannt:

```
--background-invert-if-dark   --color-element-info      --color-primary-element-light
--border-radius-container     --color-error             --color-primary-element-light-text
--border-radius-small         --color-error-text        --color-text-maxcontrast
--color-background-hover      --color-info              --default-clickable-area
--color-border                --color-info-text         --default-font-size
--color-element-error         --color-main-background   --default-grid-baseline
                              --color-main-text         --default-line-height
                                                        --font-size-small
```

**Folge für 13-10.** Die Filterleiste kann die Variablen benutzen, die die Seite schon
benutzt. Es entsteht kein Bruch beim Sprung auf 35.

## 3. Bewegung: heute kein Thema, künftig ein benannter Weg

Das Release wirbt mit Animationen in der Oberfläche und mit Rücksicht auf
`prefers-reduced-motion`. Das betrifft uns derzeit nicht: weder `php/css/search.css` noch
die UI-Spezifikation dieser Phase kennen `transition` oder `animation`, die Filterleiste
wird ohne Bewegung gebaut.

Falls später doch Bewegung dazukommt, ist der richtige Weg benannt statt erfunden:
Nextcloud 35 liefert das ergänzende Thema
`apps/theming/lib/Themes/ReducedMotion.php`, das unter der Medienabfrage
`(prefers-reduced-motion: reduce)` die Variablen `--animation-quick` und
`--animation-slow` auf `0` setzt. Eine Übergangsdauer gehört dann an diese Variablen und
nicht an eine feste Millisekundenzahl, sonst greift die Rücksichtnahme des Servers nicht.

## 4. Was diese Notiz nicht behauptet

Sie prüft den Vertrag und die Stilmittel, nicht das Aussehen. Ob die Ergebnisseite auf
einer laufenden 35er-Instanz genauso wirkt wie auf 34, ist eine Frage für den
Abnahmeplan 13-13 und für den Paritätsjob aus 13-12, nicht für diese Notiz. Das
deklarierte Versionsfenster der beiden `info.xml` steht bereits auf `33` bis `35` und
wurde in Phase 12 vollzogen; hier ist nichts offen.
