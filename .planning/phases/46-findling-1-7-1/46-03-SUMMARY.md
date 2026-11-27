---
phase: 46-findling-1-7-1
plan: 03
subsystem: admin-ui
tags: [adm-05, fehlerliste, 320px]
requires: [46-02]
provides: [Fehlerliste unter 360 px mit Zustand unter dem Grund, Gate]
affects: [php/css/admin.css, php/templates/admin.php]
key-files:
  modified:
    - php/css/admin.css
    - php/templates/admin.php
    - backend/tests/test_admin_ui_contract.py
  created:
    - .planning/phases/46-findling-1-7-1/46-LAYOUT-320.md
    - .planning/phases/46-findling-1-7-1/bilder/layout/ (63 Bilder)
duration: ca. 2 h inkl. zwei Docker-Fenster
completed: 2026-11-27
---

# 46-03: Fehlerliste bei 320 px (ADM-05)

## Ergebnis

- Task 1: e1bd1b30, Varianten A und B mit Bildern und Messung, Positivkontrolle am Stand 1.7.0 (DE 3, FR 1 Wortbrüche ohne Bindestrich bei 320 px), Docker-Fenster `Freigabe Docker-Fenster 46-03`.
- Task 2: `Entscheid Layout 46-03` = A (Owner "Ok", vom Koordinator eingetragen).
- Task 3: RED e6932901 `test(46-03): the error list keeps every word whole at 320 px` (`test_the_error_list_puts_the_state_under_the_reason_below_360_px` mit 5 Funden: vier CSS-Regeln, zweite Chip-Fassung fehlt); GREEN 409fb5a5 `fix(46-03): the error list puts the state under the reason below 360 px` (admin.css +23, admin.php +12/-1); Messung b7d7fa1c.
- Gate: liest admin.css (Regeln mit einer Ebene @media) und das Template: unter `@media (max-width: 359px)` sind `thead th:last-child` und `.findling-errors__state` `display: none` und `.findling-errors__state-narrow` `display: block`, außerhalb ist die Kopie `display: none`; kein Tabellenteil der Fehlerliste bekommt `display: block|grid|flex`; die Kopie im `th` nutzt dieselben `$chipKind`, `$chipIcon`, `$chipLabel`; genau eine Zähler-id je Gruppe. Positivkontrollen: Stylesheet ohne die neue Medienregel (mindestens 3 Funde), `td` als block (1 Fund), zweite Zähler-id (1 Fund).
- Mutationen in der Datei je rot, Datei danach byte-gleich: Medienregel auf 1px, Ausblenden der Spalte entfernt, Kopie ohne Grundregel `display: none`.
- Messung am GREEN-Stand (Fenster `Freigabe Docker-Fenster 46-03 Messung`, 4,3 GiB frei, danach gestoppt): DE, EN, FR je 320, 375, 1280 px hell und dunkel, Wortbrüche ohne Bindestrich überall 0, kein waagerechtes Scrollen, 375 und 1280 px gleich 1.7.0; Accessibility: Zustand je Breite einmal, bei 320 px Teil des Zeilenkopfs. Tabelle in 46-LAYOUT-320.md "## Ergebnis", Bilder `bilder/layout/green-*.png`.
- Gates: test_admin_ui_contract, test_admin_locale, test_phase33_audit, test_phase34_audit 303 passed, 107 skipped; ruff, ruff format, pyright (0 Fehler), vulture grün. Ausgabe im Template nur über `p()`.

## Abweichungen

- Messmethode verfeinert gegenüber dem Plan: Der benutzte Chromium (147, Playwright 1.59.1 per Skript, Playwright-MCP war getrennt) trennt DE und FR mit `hyphens: auto` selbst; maßgeblich ist deshalb die Zählung mit abgeschalteter Silbentrennung ("bare"), die dem Browser der Abnahme 45 entspricht. Begründung und Kontrollen in 46-LAYOUT-320.md.
- PHP-Opcache der Dev-Instanz lieferte nach einer Template-Änderung kurz den alten Stand (erster B-Lauf hell): Lauf verworfen und wiederholt, für A und den GREEN-Stand per Accessibility-Baum und HTTP geprüft, dass der neue Stand ausgeliefert wird.
- Die Mess-Skripte bleiben im Scratchpad (sie tragen lokale Pfade); die Methode steht vollständig in 46-LAYOUT-320.md.
- Arbeitsdateien in CRLF (core.autocrlf true) vor dem Edit auf LF gebracht; die Commits ändern nur die gewollten Zeilen.
- PHP-Gates (PHPUnit, Psalm-Taint, php-cs-fixer) in Docker: offen bis vor dem Push (46-06); die Messung lief in einem nur dafür freigegebenen Fenster.
