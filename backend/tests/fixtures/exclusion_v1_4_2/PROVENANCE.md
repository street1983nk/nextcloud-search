<!--
SPDX-FileCopyrightText: 2026 street1983nk
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Herkunft der Fixture `ExclusionService.php`

Die Datei `ExclusionService.php` in diesem Ordner ist die `ExclusionService` von Findling 1.4.2,
byte-gleich und ohne Umkodierung übernommen.

| Feld | Wert |
|---|---|
| Tag | `v1.4.2` |
| Commit | `17363bb23bdb1d5d4391a85acf37469c9f832793` |
| Pfad im Tag | `php/lib/Service/ExclusionService.php` |
| Git-Blob | `805c63392a4337a1845794106d5e831a92868f12` |
| Erzeugt mit | `git show v1.4.2:php/lib/Service/ExclusionService.php` |

## Zweck

Der Differenztest `backend/tests/test_exclusion_driver.py` (Plan 33-02) baut diese Klasse und die
`ExclusionService` von heute mit demselben Treiber `backend/tests/drivers/exclusion_driver.php` auf
`php:8.3-cli` und vergleicht `prefixes()` und `isExcluded()` über einen Korpus schwieriger Präfixe und
Pfade. So ist belegt, dass gespeicherte Präfixe aus 1.4.2 nach dem Upgrade genauso wirken wie vorher
(Erfolgskriterium 1 der Phase 33). Der Test braucht kein Tag und kein `fetch-depth`; der CI-Checkout
hat keine Tags.

Der Herkunftstest im selben Modul prüft die Bytes gegen den Blob oben und, wo das Tag vorhanden ist,
gegen `git show v1.4.2:php/lib/Service/ExclusionService.php`.

## Regeln

- Nicht ändern. Auch keine Formatierung, kein Kopf, kein Zeilenende: `.gitattributes` setzt für diesen
  Ordner `-text`, damit `core.autocrlf` keine Wagenrückläufe einfügt.
- Nie unter `php/` legen. Der Baumhash der PHP-Hälfte liest `php/**/*.php`, und die Datei würde als
  zweite Klasse gleichen Namens im Autoload-Raum stehen.
- Die Lizenz deckt `REUSE.toml` über `path = "**"` ab.
