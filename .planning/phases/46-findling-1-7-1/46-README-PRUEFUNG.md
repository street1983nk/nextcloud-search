# README-Faktencheck vor 1.7.1 (46-05, Owner-Regel 12.11.)

Stand: 2026-11-27, lokaler Kopf mit Bump 1.7.1 im Arbeitsbaum (php und backend `<version>1.7.1</version>`, `<image-tag>1.7.1</image-tag>`, `nextcloud min-version="33" max-version="35"`). Geprüft: README.md (DE), README.en.md (EN), README.fr.md (FR), jede Aussage zu Ausschlussfeldern, Fehlerliste, Sprachen, Versionen und Anforderungen gegen den Kandidaten. Messzahlen und Architektur sind seit 1.7.0 unverändert (kein Code im Container geändert) und wurden nicht neu gemessen.

| Datei | Zeile | Aussage | Beleg | Ergebnis |
|---|---|---|---|---|
| README.md | 37 | Ordner oder Muster wie *.photoslibrary vom Index ausschließen | Platzhalter des Musterfelds `*.photoslibrary` (admin.php), Ordnerliste unverändert bis auf Hilfesatz und Enter | stimmt |
| README.md | 43 bis 46 | Einzelne externe Speicher ausschließen, freie Plätze (ab 1.7.0) | unverändert seit 1.7.0 | stimmt |
| README.md | 47 bis 49 | Oberfläche in neun Sprachen, darunter Traditionelles Chinesisch (ab 1.7.0) | `ls php/l10n/*.json` ohne de_DE: en (Quelle), de, fr, es, it, nl, pt_PT, pt_BR, zh_TW = neun | stimmt |
| README.md | 50 bis 51 | Suchsprachen DE und EN voreingestellt, ES, IT, NL, PT, CS verfügbar | kein Container-Code seit 1.7.0 geändert | stimmt |
| README.md | 73 | Nextcloud 33 bis 35 mit AppAPI | info.xml beider Apps min 33, max 35 | stimmt |
| README.md | 106 bis 108 | Unterschiedliche Major- oder Minor-Version: Suche antwortet mit nichts | 1.7.0 und 1.7.1 teilen Major und Minor, der Fall greift beim Patch nicht | stimmt |
| README.en.md | 42 bis 47 | dieselben drei Punkte "from 1.7.0" | wie DE | stimmt |
| README.fr.md | 45 bis 51 | dieselben drei Punkte "à partir de 1.7.0" | wie DE | stimmt |

Ergebnis: keine falsche oder veraltete Aussage in den drei READMEs. Die drei Fixes von 1.7.1 (Hilfesatz, Enter, Fehlerliste unter 360 px) sind Bedienkorrekturen ohne neue Fähigkeit; nach der Owner-Regel "kurze Faktenliste" gehören sie nicht in die READMEs, sondern nur ins CHANGELOG.

## Vorschläge (nur mit Freigabe README 46-05)

1. READMEs: keine Änderung.
2. docs/admin-page.md (deutsche Admin-Doku, keine README): ein Satz im Abschnitt der Regelfelder, dass Enter im Feld wie der Knopf hinzufügt, und ein Satz im Abschnitt der Fehlerliste, dass unter 360 px der Zustand unter dem Grund steht. Optional; ohne Freigabe bleibt die Doku wie sie ist (der Hilfesatz ist dort schon in 46-01 nachgezogen).
