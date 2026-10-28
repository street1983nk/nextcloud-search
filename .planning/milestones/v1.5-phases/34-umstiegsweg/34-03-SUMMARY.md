---
phase: 34-umstiegsweg
plan: 03
subsystem: php-admin-page
tags: [umst-02, admin-banner, l10n, link-gate, phpunit]
requires:
  - 34-02 (migration pages docs/migrate-from-fulltextsearch{,.en,.fr}.md)
provides:
  - ParallelSearchService (IAppManager::isEnabledForAnyone for fulltextsearch, files_fulltextsearch)
  - overview() key parallelSearch (bool, fixed)
  - banner findling-banner-parallel with language dependent tag link
  - generalised link gate scan_docs_links() (four expected links)
affects:
  - 34-05 (banner visual check on 8090 with simulated app flag)
  - 34-06 (audit, T-34-13 measurement, T-34-14 probe)
  - REL-05 (tag v1.5.0 makes the four links resolve)
tech-stack:
  added: []
  patterns:
    - server rendered banner outside the $banners loop, script untouched
    - URL literals in a template map, never in a catalogue
key-files:
  created:
    - php/lib/Service/ParallelSearchService.php
    - php/tests/Unit/ParallelSearchServiceTest.php
  modified:
    - php/lib/Service/AdminViewService.php
    - php/tests/Unit/SettingsControllerTest.php
    - php/templates/admin.php
    - php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{js,json}
    - docs/l10n-{french,spanish,italian,dutch,portuguese}.md
    - docs/admin-page.md
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "CI für 34-03 lief auf dem gepushten Worktree-Zweig statt auf main; der Push auf main bleibt beim Orchestrator nach dem Merge"
  - "Katalog-Gate prüft URL-Schema und Repo-Pfad statt des bloßen Hostnamens github.com, weil ein bestehender Satz (Modell-Download) github.com als Host nennt"
  - "SettingsControllerTest liest parallelSearch über die echte Route overview() statt per Reflection; in CI grün"
metrics:
  duration: "ca. 2 h 10 min"
  completed: 2026-10-19
  tasks: 3
  files: 32
---

# Phase 34 Plan 03: Admin-Hinweis bei parallelem fulltextsearch Summary

`ParallelSearchService` fragt `IAppManager::isEnabledForAnyone` für genau `fulltextsearch` und `files_fulltextsearch`; `overview()` trägt den festen Schlüssel `parallelSearch`, das Template rendert daraus serverseitig den Warnbanner `findling-banner-parallel` mit dem abgenommenen Satz und einem sprachabhängigen Tag-Link auf die Umstiegs-Seite (de/fr/en).

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | ParallelSearchService mit PHPUnit und Schlüssel parallelSearch in overview() | 1c0130d5 |
| 2 | Banner im Template, l10n-Kette, Linkgate verallgemeinert, Doku-Abschnitt | ebff76c2 |
| 3 | Push, CI mit PHPUnit, Gegenprobe des Bedingungstests | (kein Commit auf dem Zweig; Wegwerf-Commit 413a1c37 remote und lokal gelöscht) |

## Was gebaut ist

- `php/lib/Service/ParallelSearchService.php`: `final`, Konstante `APP_IDS = ['fulltextsearch', 'files_fulltextsearch']`, `active(): bool` mit frühem true, kein Logging, keine Konfiguration. Docblock nennt UMST-02 und den Grund gegen `isEnabledForUser` (Gruppenfreigaben, T-34-11).
- `AdminViewService`: neue Abhängigkeit am Ende des Konstruktors, `'parallelSearch' => $this->parallelSearch->active()`, Docblock-Shape um `parallelSearch:bool` ergänzt.
- PHPUnit `ParallelSearchServiceTest`, sieben Methoden: keine App, nur fulltextsearch, nur files_fulltextsearch, beide, gefragte IDs gleich `APP_IDS`, Konstante selbst, Plattform-Apps allein lösen nichts aus. `isEnabledForUser` und `isInstalled` sind in jedem Fall `expects(self::never())`.
- `SettingsControllerTest`: Ansicht mit `new ParallelSearchService($this->createMock(IAppManager::class))`, neuer Fall ruft die Route `overview()` und prüft Status 200 und `parallelSearch === false`.
- Template: Banner nach der `$banners`-Schleife in `#findling-coverage-banners`, `hidden` solange `parallelSearch` nicht strikt true ist, Warn-Icon, Text-Span `findling-banner-parallel-text`, Link mit `target="_blank" rel="noreferrer noopener"` und dem vorhandenen Schlüssel "Steps in the documentation". URL aus `$migrationDocsUrls` (drei volle Literale), Wahl über `$l->getLanguageCode()` (Präfix de, Präfix fr, sonst en). `php/js/admin.js` unverändert.
- l10n: neuer Schlüssel in allen 16 Katalogen direkt hinter dem Platzbanner des Umbaus, de/fr wörtlich aus 34-WORTLAUT (B), es/it/nl/pt_PT/pt_BR als maschineller Entwurf nach den Wortwahl-Regeln der Sprachdokus (pasada, passata, doorloop, passagem/execução; Anrede bzw. Infinitiv wie im Bestand). Fünf Tabellen je eine Zeile plus Nachtrag-Absatz "19.10.2026 (Phase 34, Plan 34-03)" mit Vorbehalt.
- Schlüsselzahl 340 auf 341 mit Docstring-Absatz und Kommentarliste.
- `docs/admin-page.md`: Abschnitt "Hinweis bei parallelem fulltextsearch" (Bedingung, Folge, Link, verschwindet beim nächsten Laden, nicht im Poll).
- PHP-Baumhash: `PHP_FILES_TODAY` 103 auf 105, Hash `4b826c12...a36d876`, zwei Journalabsätze "Moved on 2026-10-19 by Plan 34-03".

## Gates

- Neu in `test_admin_ui_contract.py`: `scan_docs_links()` (ersetzt `scan_limits_link()`, einziger Aufrufer war dieselbe Datei; `test_phase33_audit.py` zählt nur `limits-per-file` und blieb grün), `scan_parallel_banner()`, `test_the_parallel_banner_stands_alone_and_links_the_migration_page`, `test_the_migration_link_follows_the_language_of_the_admin`, `test_no_catalogue_value_carries_a_link`, Selbsttests für fünften Link, fehlende Zieldatei, blob/main, anderen Anker, zu kurze Menge, Banner in der Schleife, ohne rel, immer sichtbar, im Skript erwähnt.
- Rot gesehen vor dem Template (Task 2): `6 failed, 7 passed` mit u. a. "the template carries 0 banners findling-banner-parallel", "the template lost its map of migration links" und beim Linkgate "the template carries the documentation links [...admin-page.md#limits-per-file] instead of [...vier Links]". Danach grün.
- Lokal vor Commit 2: `5722 passed, 252 skipped` (vor Commit 1: `5717 passed`), ruff check, ruff format, pyright (0 errors), vulture, `reuse lint`, `php -l` aller geänderten PHP-Dateien per Docker.

## CI

HEAD `ebff76c2` auf dem Zweig `worktree-agent-a1ed2279ee0464547`, alle Läufe grün:

| Workflow | Lauf |
|---|---|
| PHP and store metadata gates | 39223418814 |
| Python gates | 39223418817 |
| Integration | 39223418815 |
| Resilience | 39223418820 |
| HaRP deploy | 39223418908 |

PHPUnit: vorher 810 Tests (letzter grüner `php.yml` auf main, Lauf 39189895915, Commit 3657bb43), nachher 818 Tests, 3215 Assertions (810 + 7 aus ParallelSearchServiceTest + 1 aus SettingsControllerTest).

Gegenprobe: Wegwerf-Zweig `scratch-34-03-gegenprobe` (Commit 413a1c37, `APP_IDS = ['fulltextsearch']`, Baumhash mitgezogen). `php.yml` Lauf 39224774605 rot mit genau `testOnlyFilesFulltextsearchEnabledIsTheHint` ("Failed asserting that false is true") und `testTheAppIdsAreTheTwoAppsThatReachTheSearchBar` (Tests: 818, Failures: 2); Python gates Lauf 39224774529 grün, also kein Python-Gate rot. Die übrigen drei Läufe des Wegwerf-Commits abgebrochen (unnötig). Zweig remote und lokal gelöscht.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug im Plan-Prüfkommando] Katalog-Gate auf URL-Schema und Repo-Pfad**
- **Gefunden in:** Task 2
- **Problem:** Das Plan-Verify `! grep -l "github.com" php/l10n/*.json` kann nie grün werden: der Satz "The model could not be downloaded. Check that github.com and release-assets.githubusercontent.com are reachable." (Plan 27-13) nennt github.com als Host in allen Katalogen.
- **Lösung:** `test_no_catalogue_value_carries_a_link` verbietet in Schlüsseln und Werten `http`, `street1983nk` und `nextcloud-search/` und prüft für den neuen Satz zusätzlich, dass er github.com nicht nennt. T-34-09 bleibt abgedeckt (kein Link und kein Repo-Pfad im Katalog).
- **Commit:** ebff76c2

**2. [Worktree-Modus] Push auf den Agentenzweig statt auf origin main**
- **Gefunden in:** Task 3
- **Problem:** Der Plan sagt "Push auf origin main"; als paralleler Worktree-Agent darf ich main nicht schreiben, der Merge gehört dem Orchestrator.
- **Lösung:** `php.yml` und die übrigen Workflows laufen auf jedem Zweig; gepusht wurde `worktree-agent-a1ed2279ee0464547`, alle fünf Läufe grün. Der Remote-Zweig ist danach wieder gelöscht, die Commits liegen lokal auf dem Zweig. Das Plan-Verify `git diff --quiet origin/main -- php backend` gilt erst nach Merge und Push durch den Orchestrator; dabei laufen die Workflows auf main erneut.

**3. [Rule 2] SettingsControllerTest liest den Schlüssel über die Route**
- Statt einer reinen Konstruktionsprüfung ruft der neue Fall `SettingsController::overview()` und verlangt Status 200; ein Fehler im Aufbau von `overview()` mit den Doppeln würde als 500 sichtbar. In CI grün.

## Known Stubs

Keine.

## Threat Flags

Keine neue Oberfläche außerhalb des Bedrohungsmodells: keine neue Route, ein Bool in der bestehenden Admin-Antwort, ein externer Link mit `noreferrer noopener`.

## Offene Punkte für spätere Pläne

- 34-05: Banner-Sichtprobe auf 8090 mit simuliertem App-Flag, Sprache de/fr/en.
- 34-06: Messung T-34-13 (zwei Lookups je Poll), Probe T-34-14.
- Die vier Tag-Links lösen erst mit dem Tag v1.5.0 auf (REL-05).

## Self-Check: PASSED
