---
phase: 34-umstiegsweg
plan: 05
status: complete
requirements: [UMST-01, UMST-02, UMST-03]
---

# 34-05 SUMMARY: Gemeinsame Owner-Abnahme der Phase 34

## Ergebnis

Owner-Abnahme am 19.10.2026: "abgenommen" (Phase 34 gesamt), Store-Entwurf auf
Nachfrage ebenfalls abgenommen ("Auch abgenommen"); der foermliche
Release-Schritt (info.xml) bleibt bei REL-05. Protokoll mit allen neun Proben,
Wortlaut-Tabelle und der Abnahme-Zeile: `34-05-ABNAHME.md`.

## Was getan wurde

- **Task 1, Proben:** alle neun Proben auf http://localhost:8090 und GitHub
  `main` gefahren und protokolliert, jede gruen: Negativkontrolle, Banner mit
  Flag in de/en/fr (Saetze zeichengleich, Links sprachrichtig auf die
  Tag-URLs), nur files_fulltextsearch, Gruppenform ohne Admin-Mitgliedschaft
  (isEnabledForAnyone belegt), Flags entfernt (Banner hidden, Poll 8 s ohne
  Skriptfehler), es-Fallback auf `.en.md`, Konsole 0 Fehler und nextcloud.log
  unveraendert (5336 Zeilen ueber alle Proben), drei Seiten und drei READMEs
  rendern auf GitHub mit Umschaltern und richtigen Links, Store-Entwurf als
  Text aufbereitet. Simuliertes Flag per `occ config:app:set ... enabled`,
  kein Rueckfall auf echte Installation noetig.
- **Task 2, gemeinsame Runde:** mit dem Owner am geteilten Playwright-Browser.
  Eine Aenderung aus der Runde: "bei dem banner fehlt was der doku buttom
  braucht ein rahmen" -> Doku-Link als Button (Klasse `findling-banner__link`,
  2px-Rahmen in currentColor, Theme-Radius, fett, Hover/Fokus unterstrichen),
  live gezeigt, Owner: "jetzt sieht es gut aus", dann "abgenommen".
- **Task 3, Nachziehen und Aufraeumen:** Kopfsatz des Store-Entwurfs auf
  "Owner-Abnahme 19.10.2026" (info.xml unveraendert), Gates mitgezogen
  (PARALLEL_LINK im Linkgate, DRAFT_HEAD im Migrationsgate, PHP-Baumhash
  04a2c174... mit Journalabsatz "Plan 34-05", PHP_FILES_TODAY bleibt 105).
  Instanz aufgeraeumt: beide Flags weg, Probegruppe geloescht, Admin-Sprache
  de, Banner hidden (Beleg). UMST-01..03 stehen weiter auf Pending (34-06).

## Commits

- `fdfef7ba` fix(34-05): the wording of the migration path as accepted by the
  owner (Template, CSS, drei Gate-Dateien, docs/store-listing.md)
- Protokoll und diese SUMMARY im Metadaten-Commit dieses Plans.

## Verifikation

- `php -l` php/templates/admin.php sauber (php:8.3-cli per Docker).
- Fuenf Gate-Module: 841 passed. Volle Suite: 5734 passed, 252 skipped.
- ruff check + format, pyright (0 errors), vulture, REUSE compliant (2758/2758).
- `^Owner-Abnahme: 19.10.2026` im Protokoll; UMST-01..03 in REQUIREMENTS.md
  unveraendert `- [ ]`.

## Abweichungen vom Plan

- Owner-Aenderung in der Runde (Button-Rahmen) zog `php/css/admin.css` hinzu,
  das nicht in der files_modified-Liste stand; der Rahmen ist eine CSS-Regel,
  das Template traegt nur die Klasse. Gates und Baumhash-Journal decken es.
- Die Owner-Antwort kam zweistufig ("abgenommen", dann auf Nachfrage "Auch
  abgenommen" fuer den Store-Entwurf); beide woertlich im Protokoll.
