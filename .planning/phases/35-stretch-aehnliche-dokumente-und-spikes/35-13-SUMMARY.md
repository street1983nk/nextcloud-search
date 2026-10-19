---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 13
subsystem: php-companion-l10n
status: abgeschlossen
tags: [STR-01, similar-documents, l10n, rendering-probe]
requires:
  - 35-01 (Wortlaut abgenommen 19.10.2026, O1-O6 je a)
  - 35-07 (Ähnlich-Ansicht, sieben englische Schlüssel im Template)
provides:
  - "Sieben Schlüssel der Ähnlich-Ansicht in allen 16 Katalogen und fünf Sprachtabellen"
  - "Schlüsselzahl 348 mit Absatz plan 35-13"
  - "Serverseitige Rendering-Probe auf 8090 (Link, Kopf, Rückweg, beide Zustände, Orakelschutz)"
affects:
  - 35-08 (gemeinsame Abnahme)
key-files:
  modified:
    - php/l10n/de.json, de.js, de_DE.json, de_DE.js
    - php/l10n/fr.json, fr.js, es.*, it.*, nl.*, pt_PT.*, pt_BR.*
    - docs/l10n-french.md, l10n-spanish.md, l10n-italian.md, l10n-dutch.md, l10n-portuguese.md
    - backend/tests/test_admin_ui_contract.py
decisions:
  - "Neue Schlüssel direkt hinter 'last opened' in allen Katalogen und Tabellen (Ort der Trefferliste)"
  - "Italienischer Entwurf in der Lei-Form wie der Bestand, nl mit u, pt_PT ficheiro, pt_BR arquivo"
  - "Probe mit testuser statt admin (Korpus liegt bei testuser, Sprache bereits de, keine Umstellung nötig)"
  - "Deutscher Katalog für die Probe per Theme-Override im Volume eingespielt, weil 8090 den Hauptcheckout mountet und die Kataloge dort erst nach dem Merge liegen"
metrics:
  completed: 2026-10-19
  tasks: 2
  files: 22
---

# Phase 35 Plan 13: Wortlaut der Ähnlich-Ansicht in allen Katalogen Summary

Die sieben abgenommenen Sätze der Ähnlich-Ansicht stehen in allen 16 Katalogen (de/fr zeichengleich aus 35-WORTLAUT.md, fünf Sprachen als Maschinenentwurf) und fünf Sprachtabellen, Schlüsselzahl 341 auf 348 im selben Commit; die Probe auf 8090 belegt Link, Kopf, Rückweg und den byte-gleichen Zustand für fremd und nicht existent.

## Commits

| Task | Commit | Inhalt |
|---|---|---|
| 1 | 2f7b7297 | 16 Kataloge, 5 Sprachtabellen mit Nachtrag, Schlüsselzahl 348 + Absatz plan 35-13 |
| 2 | (dieser Docs-Commit) | Probenbefund in dieser SUMMARY |

## Task 1: Kataloge

**Pre-flight:**
`187:Owner-Abnahme: 19.10.2026, "Abgenommen (alle Empfehlungen)", alle Sätze wie vorgelegt, O1-O6 je Option a`

**Gegenprobe 1 (de/fr gegen Tabelle A, Werte per json.load aus de.json/fr.json, Tabelle aus 35-WORTLAUT.md geparst):**
```
OK  'Similar documents'
OK  'Similar documents to %s'
OK  'Similar to: %s'
OK  'Back to the results'
OK  'No similar documents found'
OK  'None of your other files is close enough'
OK  'This file is not available'
rows 7 bad 0
```

**Gegenprobe 2 (neue `$l->t()`-Schlüssel aus `git diff e6c6b975~1 e6c6b975 -- php/templates/search.php` minus Bestand von HEAD gegen neue Katalogschlüssel):**
`Template neu: 7 Katalog neu: 7 gleich: True Gesamt: 348`
("Search results" taucht im Diff auf, weil die aria-Zeile der Liste geändert wurde; Bestandsschlüssel, korrekt herausgerechnet.)

**Gates:** de/de_DE byte-gleich (cmp); pytest test_admin_ui_contract, test_measurement_scripts, test_php_acl_boundary, test_php_trust_boundary: 703 passed; ruff check, ruff format --check (227 Dateien), pyright latest 0 Fehler, vulture `src tests --min-confidence 80` sauber, reuse lint 2802/2802 konform. PHPL-Block: keine PHP-Datei geändert. Volle Suite als letzter Schritt (nach der Probe, allein): **5814 passed, 264 skipped, 2 warnings in 745.89s**.

## Task 2: Rendering-Probe auf 8090 (curl, kein Browser)

Vorbereitung:
- Ausgangswerte: `occ user:setting testuser core lang` = de, `admin` = de, `occ config:system:get theme` = nicht gesetzt (rc 1), `occ app:list` findling 1.4.2 (Bind-Mount `C:/Users/Student/nextcloud-search/php`, Template aus 35-07 vorhanden).
- **Backend veraltet:** der Host-Prozess auf 10035 beantwortete `POST /similar` mit 404 (`.dev/exapp.log`), die erste Probe zeigte daher den Ausfall-Banner. `/similar` steht bewusst nicht in info.xml, also erkennt `register-exapp.sh` den Prozess nicht als veraltet. Neu gestartet: `taskkill //PID 13996 //F`, dann `FINDLING_PORT=8090 sh scripts/dev/register-exapp.sh` aus dem Hauptcheckout (`registered`). Danach `POST /similar` 200.
- **Kataloge auf 8090:** der Container mountet `php/` des Hauptcheckouts, der die neuen Kataloge erst nach dem Merge trägt. Für die Probe den committeten `php/l10n/de.json` per Theme-Override ins Volume gelegt (nicht in den Bind-Mount): `mkdir -p /var/www/html/themes/findlingprobe35/custom_apps/findling/l10n`, `docker cp php/l10n/de.json ...`, `occ config:system:set theme --value=findlingprobe35` (Factory.php:586-589 mischt Theme-Übersetzungen).
- Anmeldung als testuser per Cookie-Jar nach `scripts/dev/probe_page_login.sh` (Login-Redirect `/apps/dashboard/`). Seiten in `.dev/scratch/probe/` (gitignored). Erwartete Sätze im Auswerteskript von Hand aus 35-WORTLAUT.md abgetippt, nicht aus dem Katalog gelesen.

Ergebnisse:

| Probe | Adresse | Befund |
|---|---|---|
| (1) Ergebnisseite | `?query=Genehmigung` | 25 Treffer, 25 `findling-hit__similar` (gleich Trefferzahl); jeder Linktext "Ähnliche Dokumente", jedes aria-Label beginnt "Ähnliche Dokumente zu ", Beispiel `aria-label="Ähnliche Dokumente zu 00053-antrag.pdf"`, href `...similar=389&query=Genehmigung&fp=...` |
| (2) Ähnlich-Ansicht | `?query=Genehmigung&similar=389` | ein App-h1 "Ähnlich zu: 00053-antrag.pdf"; Rückweg "Zurück zu den Treffern", href `/apps/findling/?cursors=0&page=1&query=Genehmigung&fp=c17df32e` ohne `similar`; kein Filterblock, kein Pager, 0 Treffer, 0 `findling-hit__similar`; Leerzustand (a) mit h2 "Keine ähnlichen Dokumente gefunden" und Erklärsatz zeichengleich |
| (3a) nicht existent | `?...&similar=999999999` | h1 "Ähnliche Dokumente", Rückweg ohne similar, h2 "Diese Datei ist nicht verfügbar", kein Filter, kein Pager |
| (3b) fremd | `?...&similar=243` (kollegin/files/Readme.md, `occ info:file`; `occ share:list --owner=kollegin` leer, also nicht geteilt) | wie (3a) |
| (3) Vergleich | `compare_states.py none.html foreign.html` | Block ab `<div id="app-content"`: **0 Diff-Zeilen, equal=True, 2214/2214 Bytes**. Restunterschiede der Gesamtseite nur Nextcloud-Sitzungswerte (requesttoken im Abmeldelink, `nc_lastLogin`, `nc_pageLoad`) |
| (4) formfalsch | `?...&similar=abc` | normale Ergebnisseite: App-Block byte-gleich mit (1) (`abc app-content == p1 app-content: True`), 25 Treffer, Filter, Pager |

Gegenkontrolle nach Rückbau: dieselbe Adresse (2) zeigt wieder "Similar to: 00053-antrag.pdf" (englischer Fallback, 0 Treffer für "Ähnlich zu"), also stammte der deutsche Text aus dem eingespielten Katalog dieses Plans.

Rückbau (alle ausgeführt und geprüft):
- `occ config:system:delete theme` (danach `config:system:get theme` rc 1), `rm -r /var/www/html/themes/findlingprobe35` (themes enthält wieder nur README, example).
- Fehlpfad: mein erstes `docker exec mkdir` lief ohne `MSYS_NO_PATHCONV` und legte `/var/www/html/C:/Program Files/Git/...` als leere Ordnerkette an (0 Dateien); entfernt mit `rm -r "/var/www/html/C:"`, geprüft.
- Kein Testnutzer angelegt (kollegin besteht), keine Sprache umgestellt (testuser war bereits de).
- Backend läuft weiter mit dem aktuellen Stand des Hauptcheckouts, ohne Einbettungsmodell wie vorher, neu registriert (neues Secret in `.dev/exapp.secret`). Ein zwischenzeitlicher Start mit `FINDLING_EMBED_MODEL_DIR` wurde wieder beendet (siehe Fragen).

## Fragen für 35-08

1. **Nachbarliste live nicht belegbar:** Das Dev-Backend hat kein Einbettungsmodell und praktisch keinen Vektorbestand (`vectors.db` 4 KB, Stand 19.09.; `state.db` 8499 Dateien). Darum zeigt (2) den Leerzustand (a) statt einer Nachbarliste. "Höchstens 10 Treffer, ohne Auszug, ohne Ähnlich-Link" ist live nur als 0 belegt, die Liste selbst nur im Stub-Render von 35-07. Für die gemeinsame Abnahme braucht es einen Stand mit Vektoren (Modell unter `.dev/model` vorhanden, aber 8499 Dateien nachzuziehen ist bei ca. 3,2 GB freiem RAM nicht ohne Owner-Wort zu starten).
2. **Zwei h1 im Dokument:** Nextcloud setzt im Layout `<h1 class="hidden-visually" id="page-heading-level-1">`; das Template trägt genau ein eigenes h1. Gilt schon für die normale Ergebnisseite (Bestand, kein Rückschritt dieses Plans).
3. **Stale-Backend-Erkennung:** `register-exapp.sh` erkennt einen Prozess ohne `/similar` nicht als veraltet, weil die Route bewusst nicht in info.xml steht. Kandidat für einen kleinen Fix (z. B. Probe auf die undeclared Routen).

## Deviations from Plan

- **[Rule 3] Backend-Neustart nötig:** veralteter Host-Prozess (404 auf /similar), wie vom Plan vorgesehen neu gestartet; der dokumentierte Weg erkennt ihn nicht selbst, daher vorher `taskkill`.
- **[Rule 3] Theme-Override statt Katalog im Hauptcheckout:** der Worktree darf den Hauptcheckout nicht ändern, 8090 mountet ihn aber; der Override liegt im Docker-Volume und ist zurückgebaut.
- **Probe-Nutzer testuser statt admin:** der Korpus liegt bei testuser; Sprache bereits de, kein Umstellen und Zurücksetzen nötig.
- **Kein Push, kein CI** (Worktree, Orchestrator merged und pusht); Laufnummern offen.

## Known Stubs

Keine.

## Threat Flags

Keine neuen Flächen. T-35-25 durch (3) belegt (App-Block byte-gleich), T-35-47 durch die Platzhalter- und Seitenbruch-Gates grün, T-35-48 durch Gegenprobe 1.

## Self-Check: PASSED

- SUMMARY vorhanden; Commit 2f7b7297 vorhanden (`git cat-file -t` = commit).
- Keine Halbgeviert- oder Geviertstriche in dieser Datei.
