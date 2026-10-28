---
phase: 33-ausschlussmuster-und-admin-feinschliff
plan: 10
subsystem: admin-ui, l10n, proof
tags: [excl-01, excl-02, excl-03, pol-01, pol-03, d-33-02, owner-abnahme, playwright, einheiten, fr]
requires:
  - "33-05: Musterliste, Fehlersätze, zahlenlose Bestätigung"
  - "33-06: Grenzblock Limits per file mit Änderungshinweis"
  - "33-07: Kataloge mit 334 Schlüsseln, Hardware-Satz"
  - "33-09: Nachweis EXCL-02 (Weg A, Weg C, Gegenprobe)"
provides:
  - "33-10-ABNAHME.md: neun Vorab-Proben plus T-33-31 in de/en/fr, Wortlauttabellen A bis F, gemeinsame Runde, Owner-Abnahme 18.10.2026"
  - "Größeneinheiten als sechs Katalogschlüssel (B, KB, MB, GB, TB, PB); fr zeigt o, Ko, Mo, Go, To, Po"
affects: [33-11, 36]
tech-stack:
  added: []
  patterns:
    - "Einheitensymbole sind Katalogwerte: Template $size und admin.js sizeUnits() fragen dieselben sechs Schlüssel"
    - "Owner-Abnahme einer UI gemeinsam per Playwright am geteilten Browserfenster, Entscheid wörtlich mit Datum im Protokoll"
key-files:
  created:
    - .planning/phases/33-ausschlussmuster-und-admin-feinschliff/33-10-ABNAHME.md
  modified:
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/de.js
    - php/l10n/de.json
    - php/l10n/de_DE.js
    - php/l10n/de_DE.json
    - php/l10n/fr.js
    - php/l10n/fr.json
    - php/l10n/es.js
    - php/l10n/es.json
    - php/l10n/it.js
    - php/l10n/it.json
    - php/l10n/nl.js
    - php/l10n/nl.json
    - php/l10n/pt_PT.js
    - php/l10n/pt_PT.json
    - php/l10n/pt_BR.js
    - php/l10n/pt_BR.json
    - docs/l10n-french.md
    - docs/l10n-spanish.md
    - docs/l10n-italian.md
    - docs/l10n-dutch.md
    - docs/l10n-portuguese.md
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "33-10: Owner-Abnahme 18.10.2026: 'fr angleichen sonst abgenommen' -> Richtung 'Mo überall' -> nach Sichtprobe 'abgenommen' (D-33-02 erfüllt)"
  - "33-10: O2 (ungespeicherte Zeile ohne Markierung), O3 (< und > in Mustern erlaubt, nur Text) und O5 (33-09-Beleg genügt) mit 'sonst abgenommen' akzeptiert; O4 Variante a (Hardware-Satz über Wortlauttabelle F)"
  - "33-10: Einheitensymbole als sechs Katalogschlüssel, nur fr weicht ab (o, Ko, Mo, Go, To, Po); Schlüsselzahl 334 auf 340"
  - "33-10: 'Enter a size between %1$s and %2$s MB.' bewusst nicht auf Symbolschlüssel umgebaut: fr sagt dort schon Mo, acht Sprachen neu zu übersetzen ohne sichtbare Änderung verstieße gegen 'nur erbetene Änderungen'"
metrics:
  duration: "ca. 2 h 45 min (21:04 bis 23:50 Ortszeit) inkl. Vorab-Proben in drei Sprachen, gemeinsamer Runde, fr-Fix mit Gates und Aufräumen"
  completed: 2026-10-18
  tasks: 3
  files: 26
---

# Phase 33 Plan 10: Gemeinsame Owner-Abnahme der Admin-Seite Summary

Der Owner hat die Phase-33-Flächen am 18.10.2026 an der laufenden Instanz abgenommen: Regelblock mit beiden Listen, Ablehnungssätze, Wirkung des Musters in der Unified Search (P 0, Q 1 als testuser), Grenzblock mit Änderungshinweis und Doku-Anker, Hardware-Satz über die Wortlauttabelle, Wortlaute de/en/fr. Einzige verlangte Änderung: Französisch zeigt Größen jetzt mit französischen Einheiten (Mo statt MB), umgesetzt über sechs neue Katalogschlüssel mit grünen Gates. Die Anforderungen EXCL-01..03, POL-01, POL-03 bleiben Pending; sie hakt der letzte Task von 33-11 ab.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Proben vorab per Playwright (9 Proben plus T-33-31, de/en/fr, Saat P/Q/P2) | b664d854 | 33-10-ABNAHME.md |
| 2 | Gemeinsame Runde mit dem Owner (Checkpoint, Schritte 1-7) | docs-Commit | 33-10-ABNAHME.md |
| 3 | fr-Einheiten-Fix (Mo überall), Abnahme-Vermerk, Aufräumen | 9eff47b4 + docs-Commit | Template, admin.js, 16 Kataloge, 5 Dokus, 2 Tests, Protokoll |

## Ergebnisse

- **Vorab-Proben (Task 1):** alle neun grün in de/en/fr, keine rote Probe, kein Produktfehler. T-33-31 (`*<img src=x>*`): gültiges Muster, erscheint nur als Text, kein DOM-Element, kein Dialog. Logprobe: keine Regelwerte im nextcloud.log (L-33-09-01-Fix hält).
- **Gemeinsame Runde (Task 2):** live am geteilten Playwright-Fenster: Regelblock, Ablehnung `[0-9]*` mit Satz am Feld, Suche als admin (beide 0, Rechte-Filter) und als testuser (P 0, Q 1), Doku-Anker über `blob/main` im Abschnitt "Grenzen je Datei ändern"; Tag-Link geht erst mit v1.5.0 auf. Bilder `runde-01` bis `runde-08` im Scratch.
- **fr-Fix (Task 3):** Einheitensymbole als Katalogschlüssel in Template (`$size`, Feld-Label) und admin.js (`sizeUnits()`); fr: o, Ko, Mo, Go, To, Po; Schlüsselzahl 334 auf 340; fünf Doku-Tabellen; Baumhash-Journal "Plan 33-10" (`0e566c06...`). Nachprobe: fr "50,0 Mo", "512,0 Mo", Label "Mo"; de unverändert MB. Owner sah das Bild live, dann "abgenommen".
- **Aufräumen:** Muster-Schlüssel gelöscht (`config:app:get` Exit 1), Saat `/Abnahme33` per WebDAV gelöscht (204), SubtreeExpandJob per force-execute plus cron abgeräumt, Papierkorb testuser geleert, PROPFIND 404, Saatwörter 0 Treffer, Kanarie 1, `exclusions = ["Archiv"]` unverändert, Admin-Sprache de. Heartbeat-Reststück `php/l10n/.claude-active` (14.10., ignoriert, verwaist) entfernt.

## Gates

666 passed (test_admin_ui_contract.py, test_measurement_scripts.py); unified_search-Plugin 32 passed; public_artifacts/store_metadata/workflow_tag_triggers/filter_steps 183 passed; ruff check und format grün; pyright (latest) 0 Fehler; vulture grün; `node --check php/js/admin.js`; `php -l` (php:8.3-cli) für admin.php.

## CI

Push nach dem Abschluss-Commit, alle Läufe des HEAD-Commits beobachtet; Ergebnis je Workflow in der Abschlussmeldung der Session (alle grün, sonst stünde hier der Fix).

## Deviations from Plan

### Auto-fixed Issues

Keine stillen Fixes.

### Weitere Abweichungen

1. **Hardware-Satz nicht live auslösbar (O4 Variante a):** Das Host-Backend unter Windows meldet keinen Arbeitsspeicher (`judge_hardware()` antwortet `memory_unknown`, nicht `hardware_short`); an 8096 ist das Backend nicht angebunden. Abnahme über die Wortlauttabelle F mit Owner-Wort.
2. **"Enter a size between %1$s and %2$s MB." nicht umgebaut:** fr übersetzt dort schon mit Mo; ein Umbau hätte acht Sprachen ohne sichtbare Änderung neu übersetzt (Regel "nur erbetene Änderungen").
3. **Suche-Schritt der Runde als zwei Konten:** Als admin sind P und Q 0 (Saat gehört testuser, Rechte-Filter); der P-0/Q-1-Beweis lief als testuser. Im Plan stand das Konto nicht fest.
4. **Kachel-Anstieg (Probe 8) erst mit Gegenprobe P2 sichtbar**, weil der alte Zählstand vom 14.10. eine inzwischen gelöschte Datei enthielt; Fehlerlisten-Beleg über 33-09 A11 (O5 vom Owner akzeptiert).
5. **Muster-Schlüssel am Ende gelöscht** statt `[]` gespeichert, wie in 33-09, damit der Endzustand dem vor dem Plan gleicht.
6. **Stufen-Teilung von Task 3:** Fix und Nachprobe zuerst (9eff47b4), Abnahme-Vermerk erst nach der Sichtprobe des Owners, dann Aufräumen und dieser Abschluss; der Plan verlangt genau diese Reihenfolge ("Bild zeigen, bevor abgenommen vermerkt wird").

## Known Stubs

Keine.

## Threat Flags

T-33-30 (Selbstabnahme) mitigiert: blockierender Checkpoint, Owner-Antwort wörtlich mit Datum unter "Abnahme durch den Owner". T-33-31 (Markup in der Liste) geprüft: nur Text, kein Element, kein Dialog. T-33-32 (Skriptfehler) geprüft: 0 Konsolenfehler aus admin.js über alle Proben, nur erwartete 400-Netzmeldungen.

## Self-Check: PASSED

- FOUND: 33-10-ABNAHME.md mit "Owner-Abnahme: 18.10.2026", 33-10-SUMMARY.md
- FOUND: b664d854, 9eff47b4
- REQUIREMENTS.md: EXCL-01..03, POL-01, POL-03 stehen auf `- [ ]` (Abhaken in 33-11)
- Endzustand 8090: exclusions `["Archiv"]`, exclusion_patterns weg, PROPFIND /Abnahme33 404, Kanarie 1
