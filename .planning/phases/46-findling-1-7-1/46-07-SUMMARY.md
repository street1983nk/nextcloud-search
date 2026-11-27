---
phase: 46-findling-1-7-1
plan: 07
subsystem: release
tags: [rel-08, volltest, abnahme, issue-63]
requires: [46-06]
provides: [46-VOLLTEST.md, audited_head a3c94c16, ci_head a3c94c16, status_46_07 passed]
duration: ca. 1 Tag
completed: 2026-11-28
---

# 46-07: Volltest, gemeinsame Abnahme, Nacharbeit

## Ergebnis

- Volltest und gemeinsame Playwright-Abnahme (Hilfesatz, Enter, Fehlerliste 320/375/1280 hell und dunkel, FR, zh_TW) ohne Einwand.
- Nacharbeit nach Owner-Entscheid, je Test zuerst: übersetzte Beispiele in der Ablehnungsmeldung (Sicherung*, Sauvegarde* usw.) und im Musterfeld (Nom*, Nombre* usw.), dazu #63 (leere Unterzeile bei leerem Ausschnitt) auf beiden Seiten: Backend `wire_snippets`, Begleit-App `filterSnippets` mit `\z`-Anker.
- Changelog-Punkte vier und fünf in drei Sprachen, ohne Issue-Nummer.
- Volltest lokal 7429 passed, 333 skipped (Docker aus), ruff, format, vulture, pyright grün.
- Push nach Freigabe auf a3c94c16, alle 8 Workflows grün. Delta-Audit in 46-AUDIT.md "## Nachtrag 46-07": keine neue Angriffsfläche. audited_head = ci_head = a3c94c16, status_46_07 passed, Abnahme Härtung ja.

## Lehren

- Nach jeder PHP-Änderung den Baumhash und das Audit-Gate der Regex-Anker (`\z` statt `$`) lokal mitlaufen lassen, bevor gepusht wird.
- `head_green.sh` braucht den vollen Commit-Hash; ein gekürzter liefert "no workflow run".
- Docker Desktop frisst rund 2,5 GiB; der CI-Warter wurde bei 2,6 GiB frei vom Speicherwächter beendet.
