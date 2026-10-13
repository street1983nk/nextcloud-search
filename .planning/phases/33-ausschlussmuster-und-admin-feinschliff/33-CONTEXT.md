# Phase 33: Ausschlussmuster und Admin-Feinschliff, Kontext

Owner-Entscheide (Stand 13.10.2026), gesperrt für die Planung.

## Entscheide

- **D-30-01 (aus Phase 30, gilt weiter):** Nur `*` und `?` als Platzhalter, fnmatch-artig, kein `**`, keine Negation, keine Regex. Beispiele `*.photoslibrary`, `*/node_modules/*`. Bestehende Präfix-Ausschlüsse bleiben gültig.
- **D-33-01 Abgleich als Netz (Weg C aus 33-RESEARCH):** Eine bekannte, unveränderte Datei, die unter eine Ausschlussregel fällt (Muster oder Präfix), wird beim nächsten Abgleich aus dem Index entfernt. Das erweitert den Owner-Entscheid vom 03.10.2026 um den Fall "bekannt und unverändert": die Regel von heute entscheidet. Owner-Wort 13.10.2026.
- **D-33-02 Keine UI-SPEC:** Wie Phase 32 direkt planen. Die Admin-Seite folgt dem bestehenden Stil; Wortlaute (Musterliste, Fehlermeldungen, Grenzblock, Hardware-Satz) gehen als Entwurf an den Owner; Abnahme gemeinsam per Playwright am Ende der Phase. Owner-Wort 13.10.2026.
- **D-33-03 Grenzen für Muster (Planer-Entscheidung, Owner kann widersprechen):** Höchstens 32 Muster zu je 60 Zeichen (Vorschlag aus 33-RESEARCH); Präfixe bleiben bei 64 und 256.

## Folgen

- Keine Schemaänderung (D-30-08 bleibt gehalten): Muster liegen im neuen appconfig-Schlüssel `exclusion_patterns`, Präfixe byte-gleich wie in 1.4.2.
- Alte Urteilszeilen ausgeschlossener Dateien (Issue #22, 266k Einträge) müssen aus `findling_file_state` verschwinden (Befund B2).
- Der falsche Änderungshinweis zur Größengrenze (`admin.php:1291`, Befund B3) wird mit dem Grenzblock (POL-01) korrigiert.
