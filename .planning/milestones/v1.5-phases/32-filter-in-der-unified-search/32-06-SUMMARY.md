---
phase: 32-filter-in-der-unified-search
plan: 06
subsystem: CI (deploy-harp, team-folder-acl), Backend-Tests (Workflow-Vertrag), Doku, Store-Entwurf
tags: [usrch-01, usrch-02, usrch-03, d-32-01, d-32-02, d-32-03, a1, deploy-harp, groupfolders, share]
requires:
  - phase: 32
    provides: "32-01 bis 32-05: types und folder im Provider, Ordnerfilter in PHP mit FOLDER_MAX_ROUNDS 12, Plugin und Kataloge"
provides:
  - "deploy-harp-Schritt 'Unified search filters, type and folder on the ordinary search route' ohne if: auf NC 33, 34, 35 und arm64"
  - "backend/tests/test_unified_search_filter_steps.py: Vertrag über den Schritt (Lage, kein if:, alle Proben, 400-Probe, Saat), fünf Gegenproben"
  - "team_folder_acl.sh Abschnitt 8: vier Ordnerproben (a) bis (d) über Gruppenordner, ACL-Sperre und empfangenen Share; Annahme A1 belegt"
  - "docs/search-filters.md Abschnitt 'In the unified search' mit den Grenzen D-32-01 bis D-32-03"
  - "docs/store-listing.md 'Entwurf v1.5.0 (Teil Phase 32)', Owner-Abnahme offen (REL-05)"
  - "CHANGELOG [Unreleased] Added: Typ- und Ordnerfilter in der Unified Search"
affects: [32-07 Owner-Abnahme per Playwright, 32-08 Audit, REL-05 Store-Text]
tech-stack:
  added: []
  patterns: ["Saat-Proben gegen IDs aus WebDAV statt aus der geprüften Suche; Vergleichsbasis zweimal gelesen als Positivkontrolle"]
key-files:
  created:
    - backend/tests/test_unified_search_filter_steps.py
  modified:
    - .github/workflows/deploy-harp.yml
    - scripts/ci/team_folder_acl.sh
    - docs/search-filters.md
    - docs/store-listing.md
    - CHANGELOG.md
decisions:
  - "Vertragstest liest den Workflow als Text über collect_steps aus test_language_proof_steps (kein YAML-Parser im Backend, wie dort begründet), statt 'per YAML' wie im Plan"
  - "Zusätzliche Gegenprobe types=pdf&until=<vor dem Upload>: die Saat-PDF muss fehlen, sonst wirkt das Datum neben dem Typ nicht"
  - "Fremde Treffer unter types=text dürfen keine PDF-Titel tragen; keine zweite Endungsliste im Workflow (eine Vokabel bleibt TYPE_GROUPS)"
  - "Frist der Saat ist LANGUAGE_PROOF_BUDGET_SECONDS (gleiche Uhr, vier kleine Dokumente), keine neue Variable"
  - "Probe (c) sperrt per Nutzerregel auf einem Unterordner von SUB; eine Gruppenregel auf demselben Pfad würde nach Rule::mergeRules mit allow gewinnen"
metrics:
  duration: "ca. 150 min inkl. ca. 25 min Volltestläufe und ca. 45 min CI"
  completed: 2026-10-13
  tasks: 3
  files: 6
---

# Phase 32 Plan 06: CI-Belege, Gruppenordner und Share, Doku Summary

Die drei Erfolgskriterien der Phase 32 und das Kernverhalten D-32-01 sind auf NC 33, 34, 35 und arm64 belegt (deploy-harp 38339350221, alle vier Beine grün); der Job team-folder-acl belegt Annahme A1 mit Gruppenordner, ACL-Sperre und empfangenem Share; Doku, Store-Entwurf und CHANGELOG stehen.

## Commits

- `b44006dd` test(32-06): the unified search filters on every leg of the HaRP deploy (Task 1)
- `64350f8c` test(32-06): the folder filter over team folders and a received share (Task 2)
- `2d6b0214` docs(32-06): the unified search filters and their limits (Task 3)
- Alle gepusht auf origin/main.

## Task 1: deploy-harp-Schritt und Vertragstest

- Schritt nach "Language proof", vor "The drift probe both directions share", ohne `if:`, Kommentarblock mit Begründung und D-32-01/D-32-02.
- Ablauf: Filterkarte (HTTP 200, genau ein findling-Eintrag, `types` und `folder` als string, fail closed); Saat per WebDAV (`/Filterprobe32/Oben.txt`, `/Filterprobe32/Innen/Tief.md`, `/Filterprobe32/Bericht.pdf` aus `findling-src/testdata/corpus/01-text-layer.pdf`, `/Andere32/Fremd.txt`), IDs per PROPFIND, `findling:index --restart`, Polling mit cron.php bis alle vier IDs bei `term=reference` da sind; zwei ungefilterte Läufe müssen gleich sein (Positivkontrolle der Vergleiche).
- Proben (limit 25): `types=pdf`, `types=text`, `folder=/Filterprobe32`, `folder=/Filterprobe32/Innen`, `types=pdf&since=<vor>`, `types=pdf&until=<vor>` (Gegenprobe, PDF fehlt), `folder=/Filterprobe32&since=<morgen>` (0, HTTP 200); fail-open `types=videos`, `types=` 5000 mal `a`, `folder=/gibtsnicht`, `folder=/../../`, `folder=/Filterprobe32/Oben.txt`, `folder=/`, `folder=//` je gleich ungefiltert; `types=pdf,videos` gleich `types=pdf`; `types=` und `folder=` leer je HTTP 400. Saat am Ende per DELETE weg, danach keine Saat-ID mehr in der Antwort.
- Vertragstest (8 Fälle): echter Workflow ohne Befund, Schritt ohne `if:`; Selbsttests mit sauberem Beispiel (Positivkontrolle), `if:` am Schritt, fehlende 400-Probe, fehlender manipulierter Wert, falsche Lage, umbenannter Schritt (ein Befund je Anspruch).
- RED: 2 rot (Schritt fehlt), 6 grün. Gegenproben am echten Workflow: `if:` eingefügt meldet "carries an if:", gelöschte `refused empty-folder`-Zeile meldet die 400-Probe.
- Helfer lokal geprüft: extrahierter Schritt `bash -n` und shellcheck ohne Befund; jq-Helfer und `probe`/`same` mit Beispielantwort (Tür mit `attributes: []`) gegen Positiv- und Negativkontrollen gefahren.
- Belege je Bein (Log): Filterkarte `{"term":"string","title-only":"bool","since":"datetime","until":"datetime","types":"string","folder":"string"}`, alle Proben wie erwartet, `empty-types` und `empty-folder` HTTP 400.

| Bein | Job | Saat nach | Ergebnis |
|---|---|---|---|
| stable33, ubuntu-24.04 | 115106615731 | 4 cron-Runden | grün |
| stable34, ubuntu-24.04 | 115106615493 | 2 cron-Runden | grün |
| stable35, ubuntu-24.04 | 115106615748 | 3 cron-Runden | grün |
| stable34, ubuntu-24.04-arm | 115106615760 | 2 cron-Runden | grün |

- Spätere Schritte: Drift und Uninstall fragen nur die Kanarie, "Uninstall 3" entfernt das Volume und damit den Index vor den Store-Strecken; die Saat beeinflusst keine spätere Zählung (gegen die Schritte geprüft, Lauf grün bis Store upgrade 7).

## Task 2: team-folder-acl (Annahme A1)

- Abschnitt 8 nach dem Urteilsdurchlauf: `hits_in(user, term, folder)` mit `--data-urlencode "folder=$3"`, Datei-IDs statt Anzahl, Tür übersprungen.
- Vorbereitung: Datei unter `${SUB}/locked`, Nutzerregel `-read` für Mitglied 2 (PROPFIND 404 für Mitglied 2, 207 für Mitglied 1 als Beleg der Sperre); Ordner `ShareF-ci` von Mitglied 1, Share per OCS (shareType 0, permissions 1) an Mitglied 2, Mountpunkt aus `shared_with_me` gelesen (`/ShareF-ci`), Dateisystem von Mitglied 2 vor dem Upload eingerichtet; Warten bis beide neuen Dateien ohne Ordner gefunden werden.
- Ergebnis (Integration 38339350216, Job 115106615329, grün):
  - (a) `/NoAclF-ci` liefert die plain-Datei [51]; Gegenprobe `/AclF-ci` leer.
  - (b) `/AclF-ci/b_plus_m` liefert die ACL-Datei [50], ebenso der Mountpunkt `/AclF-ci`; plain-Datei dort leer.
  - (c) gesperrte Datei für Mitglied 2 unter `/AclF-ci/b_plus_m` und `/AclF-ci/b_plus_m/locked` leer; Kontrolle Mitglied 1 unter `/AclF-ci/b_plus_m` findet sie [56].
  - (d) Share über `/ShareF-ci` liefert [59]; eigener Ordner `/OwnF-ci` leer; Außenstehender leer.
- **Annahme A1 belegt:** Die Vorauswahl verwirft weder unter dem Mountpunkt eines Gruppenordners noch unter einem Unterordner darin noch unter dem Mountpunkt eines empfangenen Shares. Grenze des Belegs: von außen ist nicht sichtbar, ob die Koordinaten im Lauf vorhanden waren oder der Recheck allein entschied (ohne Mountliste gibt es keine Koordinaten, 32-02); ein falscher Rohpfadraum hätte (a), (b) oder (d) geleert. Kein Fix in SearchService nötig.

## Task 3: Doku, Store-Entwurf, CHANGELOG

- `docs/search-filters.md`: Einleitungssatz, Abschnitt `## In the unified search` (sieben Einträge, Unterordner, Prüfung im Baum des Nutzers, Ordner verlässt PHP nie; Grenzen: zwei Chips zwei Gruppen D-32-02, Datum wirkt mit, leerer Wert HTTP 400 vom Kern D-32-01, manipulierte Werte ignoriert D-32-03, `pdf,videos` filtert nur `pdf`, Ergebnisseite ohne Ordnerfilter, Tür trägt Typen, ZIP-Grenze).
- `docs/store-listing.md`: `# Entwurf v1.5.0 (Teil Phase 32)` mit Zeile en/de/fr und Vermerk "Owner-Abnahme offen, Teil von REL-05; info.xml und READMEs werden erst nach der Abnahme geändert". info.xml und READMEs unverändert. Nichts eingereicht.
- `CHANGELOG.md` [Unreleased] Added: ein Eintrag.
- Gedankenstrich-Prüfung über die drei Dateien leer; Workflow und Skript bleiben reines ASCII.

## Gates und CI

- Lokal aus backend/ mit PYTHONUTF8=1, vor jedem Commit: `pytest` 5621 passed, 30 skipped (zweimal, der zweite Lauf nach den Doku-Änderungen); `ruff check`, `ruff format --check` grün; `PYRIGHT_PYTHON_FORCE_VERSION=latest pyright` 0 Fehler; `vulture src tests --min-confidence 80` ohne Befund. `test_php_acl_boundary.py` unverändert (`git diff --quiet HEAD`) und grün. Keine PHP-Änderung, Baumhash unberührt.
- CI auf 64350f8c, `gh run watch <id> --exit-status` Exitcode 0: HaRP deploy 38339350221, Integration 38339350216, Python gates 38339350197, Resilience 38339350228, Security scans 38339350233, OpenSSF Scorecard 38339350127, Multi-arch image 38339350235. (Der erste Hintergrund-watch auf 38339350221 brach mit "error connecting to api.github.com" ab; der Lauf selbst war grün, erneuter watch Exitcode 0.)
- CI auf 2d6b0214: Security scans 38341732175, OpenSSF Scorecard 38341732085 grün. python.yml startet bei docs/ nicht über den Pfadfilter, die Gates lesen aber store-listing.md; deshalb per workflow_dispatch auf main: Python gates 38341903380 grün (beide Jobs).

## Deviations from Plan

### Präzisierungen

- Vertragstest liest Text statt YAML (Begründung in test_language_proof_steps.py: kein YAML im Backend); er nutzt dessen `collect_steps`.
- Zusätzliche Proben über den Plan hinaus: `types=pdf&until=<vor dem Upload>` (Gegenprobe zum Datum), `types=pdf,videos` gleich `types=pdf`, zweite ungefilterte Lesung als Positivkontrolle, Saat-IDs nach dem Löschen.
- team-folder-acl: Proben vergleichen Datei-IDs statt Anzahlen; je Probe eine Gegenprobe; Außenstehender beim Share.
- python.yml per Dispatch statt per Push (Pfadfilter).

Sonst keine Abweichungen; kein Produktfehler gefunden.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-32-20 (Probe (c) gesperrte Datei bleibt mit folder unsichtbar, Sperre per PROPFIND belegt), T-32-21 (Probe (d) Share nur beim Empfänger und nur unter seinem Mountpunkt, Außenstehender leer), T-32-22 (keine neuen Actions, keine Nutzerdaten in `${{ }}`, keine GITHUB_ENV-Schreibstelle, `[[ =~ ]]` statt `grep -E`, test_workflow_pins grün), T-32-23 (Schritt ohne `if:`, Vertragstest verbietet es) sind umgesetzt.

## Offene Punkte

- Owner-Abnahme des Store-Satzes Teil Phase 32 (REL-05); erst danach info.xml und READMEs.
- 32-07: Playwright-Abnahme der sieben Menüeinträge mit dem Owner (Checkpoint).
- USRCH-03 abgehakt; USRCH-01 und USRCH-02 bleiben bis zur Owner-Abnahme 32-07 offen.

## Self-Check: PASSED

- Dateien vorhanden: backend/tests/test_unified_search_filter_steps.py, Abschnitt `## In the unified search` in docs/search-filters.md, `# Entwurf v1.5.0 (Teil Phase 32)` in docs/store-listing.md.
- Commits b44006dd, 64350f8c, 2d6b0214 in `git log` und auf origin/main.
- deploy-harp 38339350221 vier Beine grün mit 400-Probe im Log je Bein; team-folder-acl grün mit (a) bis (d).
