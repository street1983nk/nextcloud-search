---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 16
subsystem: ci, planung
tags: [push, ci-belege, sc3, owner-abnahme]
requires: ["27-15"]
provides:
  - "Push-Signal wörtlich, CI-Lauf-IDs auf a8e3d7ea und 2b9de323"
  - "Zuordnung D-27-01 bis D-27-20 zu den Plänen"
  - "SC1 bis SC4 mit Beleg"
affects: [.github/workflows/deploy-harp.yml]
tech-stack:
  added: []
  patterns: ["Routen-Ratsche in deploy-harp.yml zieht mit jeder neuen info.xml-Route mit"]
key-files:
  created: [.planning/phases/27-vorab-pr-fung-und-settings-oberfl-che/27-16-SUMMARY.md]
  modified: [.github/workflows/deploy-harp.yml]
decisions:
  - "HaRP-Rot auf a8e3d7ea war die geprüfte Routenliste in Store install 6, kein Produktfehler; Fix 2b9de323 mit Owner-Wort als zweiter Push"
metrics:
  duration: "ca. 1 h (Push, CI, Ratschen-Fix, Belege)"
  completed: 2026-09-29
requirements: [PRUEF-01, UI-01]
---

# Phase 27 Plan 16: Push-Entscheid, CI-Belege und Phasenabnahme Summary

Owner-Signal "push-now", 106 Commits nach main, alle Workflows auf dem Phasenstand grün, nachdem die Routen-Ratsche der HaRP-Strecke um die zwei ADMIN-Proberouten erweitert wurde; SC1 bis SC4 belegt, Owner hat die Phase am 2026-09-29 abgenommen.

## Tasks

| Task | Name | Commit | Stand |
|------|------|--------|-------|
| 1 | Push-Entscheid | Push d91305df..a8e3d7ea, zweiter Push 2b9de323 | erledigt, Signal unten |
| 2 | CI-Belege einsammeln | 2b9de323 (Ratschen-Fix), dieser Commit (SUMMARY) | erledigt |
| 3 | Owner-Abnahme der Phase 27 | erledigt | Owner-Signal "ok abgenommen" |

## Push-Signal (Task 1)

Wörtlich, 29.09.2026, per Frage-Dialog: "push-now"

- Push 1: `d91305df..a8e3d7ea`, 106 Commits (Phase 27 plus Quick-Task 260929-kii)
- Push 2 (erneutes Owner-Wort, Befund HaRP): `a8e3d7ea..2b9de323`, 1 Commit
- Danach `git log origin/main..HEAD` = 0; kein Release, kein Tag, keine Issue- oder Store-Texte

Kontext: Zwischen 27-15 und 27-16 lief der Quick-Task 260929-kii (Deckungsgrad-Nenner, Altfehler v1.0 aus der 27-15-Abnahme "607 von 587"), gemergt in bbb4f406, Doku a8e3d7ea, Verifikation 6/6. Er reiste mit Push 1 und ist in den CI-Läufen auf a8e3d7ea enthalten.

## CI-Belege (Task 2)

Der Plan nennt python.yml, php.yml, integration.yml und docker.yml; im Repo heißen die Workflows so:

| Plan-Name | Workflow | Lauf-ID | Commit | Ergebnis | Jobs |
|-----------|----------|---------|--------|----------|------|
| python.yml | Python gates | 36578517859 | a8e3d7ea | success | ruff, format, pyright, vulture, pytest (Linux, inkl. Probe-Kind- und cgroup-Tests) success; arm64-Startkosten skipped |
| php.yml | PHP and store metadata gates | 36578517939 | a8e3d7ea | success | php -l, info.xml Store-Validierung, PHPUnit über die Companion-App je success |
| integration.yml | Integration | 36578517923 | a8e3d7ea | success | 8 Jobs success, darunter walking-skeleton (stable34, 8.2) mit dem Nicht-Admin-Schritt (Job 109440272745) |
| docker.yml | Multi-arch image | 36578517843 | a8e3d7ea | success | Build und Smoke linux/amd64 und linux/arm64, Manifest-Merge |
| (zusätzlich) | Resilience | 36578517899 | a8e3d7ea | success | disk-full, kill-resume success; measurements skipped |
| (zusätzlich) | HaRP deploy | 36578517817 | a8e3d7ea | **failure** | alle 4 Beine rot in "Store install 6", siehe Gap |
| (zusätzlich) | HaRP deploy | 36581106370 | 2b9de323 | success | stable33/34/35 amd64 und stable34 arm64 success |

Auf 2b9de323 lief nur HaRP deploy an (Pfadfilter, der Commit ändert nur `.github/workflows/deploy-harp.yml`); die übrigen Belege gelten für a8e3d7ea, dessen Baum sich außerhalb dieser Workflow-Datei nicht unterscheidet.

### SC3-Schritt im Log (Integration 36578517923, Job walking-skeleton)

Schritt "A user who is not an admin reaches neither the probe nor the profile route": POST `admin/profile/check`, POST `admin/profile` und GET `admin/profile/check` als testuser liefen durch `expect_refused` (nur 401/403/302/303 erlaubt, jedes 200 bricht ab), das gespeicherte Profil war vorher und nachher gleich, und die Gegenprobe als Admin schrieb:

```
the GET admin/profile/check as the admin answered 200
```

Der Schritt endete grün, also kein 200 für den Nicht-Admin.

### Gap-Befund HaRP deploy (behoben)

- Befund: "Store install 6" in `.github/workflows/deploy-harp.yml` prüft die Routen aus `oc_ex_apps_routes` gegen eine geprüfte Liste von fünf Routen. Das Archiv deklariert seit 27-11 sieben: zusätzlich `^/probe$:POST:2` und `^/probe/state$:GET:2` (ADMIN, aus 27-07/27-11). Log: "the archive declares '... ^/probe$:POST:2 ^/probe/state$:GET:2 ...' instead of the five reviewed routes".
- Einordnung: kein Produktfehler, die Ratsche tat ihren Zweck (neue Routen fallen auf). 27-11 hatte die Routenzähl-Ratsche in den Python-Tests mitgezogen, die zweite Ratsche in der HaRP-Strecke nicht.
- Fix mit Owner-Freigabe: 2b9de323 "ci(27-16): widen the reviewed route ratchet to the two ADMIN probe routes", zweiter Push mit erneutem Owner-Wort; Nachlauf 36581106370 auf allen vier Beinen grün.

## Lokale Suite und Gates (Task 2 verify)

Befehl: `cd backend && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright && uv run vulture src tests --min-confidence 80`

Gefahren am 29.09.2026 auf HEAD 2b9de323 (Windows, lokal):

| Gate | Ergebnis |
|------|----------|
| pytest | 4107 passed, 25 skipped, 1 warning (StarletteDeprecationWarning aus fastapi.testclient), 303,74 s |
| ruff check | All checks passed! |
| ruff format --check | 183 files already formatted |
| pyright (latest) | 0 errors, 0 warnings, 0 informations |
| vulture --min-confidence 80 | keine Befunde |

Die 25 Skips sind plattform- oder werkzeugabhängig (POSIX-Grenzen wie RLIMIT_AS, SIGKILL/Prozessgruppen, fehlende Shell-Werkzeuge oder mitgeliefertes Modell unter Windows); der Linux-Lauf in Python gates 36578517859 trägt sie.

## Entscheidungen D-27-01 bis D-27-20

| Entscheidung | Inhalt kurz | umgesetzt in |
|--------------|-------------|--------------|
| D-27-01 | fp32-Häkchen unter dem Auswahlfeld, nur Standard/Leistung, beide Schlüssel zusammen | 27-04 (saveProfile beide Schlüssel), 27-10 (Template), 27-12 (Skript), 27-13 (Texte) |
| D-27-02 | fp32-Beschaffung in der Probe, Modell gemessen | 27-06 (Modellprobe als Spawn-Kind), 27-09 (Download, Digest, Aufräumen) |
| D-27-03 | Reindex-Hinweiszeile beim Umschalten der Genauigkeit | 27-08 (Reindex-Felder), 27-10, 27-12 |
| D-27-04 | Probe im Hintergrund, Poll, Ergebnis nach Neuladen sichtbar | 27-07 (Routen), 27-09 (Orchestrator), 27-11 (/probe, /probe/state), 27-12 (Poll 2000 ms) |
| D-27-05 | Indexierung pausiert während der Probe | 27-05 (Pause in Poller und EmbedRunner), 27-09; live belegt in 27-15 |
| D-27-06 | Zeitdeckel Messteil 120 s, Download 600 s, eine Probe gleichzeitig | 27-02 (Deckel), 27-09 (Einzelflug); busy live in 27-15 |
| D-27-07 | Zweistufig: ein Slot messen, vorab rechnen, dann N | 27-02 (Rechnung mit Vorab-Toren), 27-09 |
| D-27-08 | "passt knapp" unter Sicherheitsabstand, nur "passt" speichert | 27-02 (reserve_thin), 27-07 (Commit-Bindung), 27-12; narrow live in 27-15 |
| D-27-09 | Sparsam und fp32 zu int8 ohne Probe, Leistung zu Standard mit Probe | 27-04 (needsProbe), 27-07, 27-12; Abwärtsweg live in 27-15 |
| D-27-10 | Verdikt verfällt nicht, Datum und Ergebnis sichtbar | 27-04 (Probe-Ablage), 27-07, 27-10 |
| D-27-11 | Knopf "Bei Sparsam bleiben", SC1-Wortlaut angepasst | 27-01 (ROADMAP-Wortlaut), 27-10, 27-13 |
| D-27-12 | Nach Wächter-Absenkung "Erneut prüfen", occ-Zeile weg, Token bleibt auf dem Server | 27-07, 27-08 (guardConfirmable), 27-10 (occ-Zeile raus), 27-12 |
| D-27-13 | occ als zweiter Schreibweg ohne Probe dokumentiert | 27-14 (Doku), 27-04 |
| D-27-14 | Env überstimmt nur Einzelwerte, Fläche nennt sie, Probe rechnet mit ihnen | 27-08 (Env-Felder), 27-09, 27-10 |
| D-27-15 | Wächter-Absenkung während der Probe ausgesetzt, Slot-Drossel bleibt | 27-05 (Aussetzung), 27-03 (shed_idle, rebase), 27-09 |
| D-27-16 | Pause-Deckel 1800 s, Verdikt pause_timeout | 27-02 (Code und Deckel), 27-09 |
| D-27-17 | Probe löscht nur selbst geladene fp32-Datei | 27-09, 27-10, 27-14 (Doku) |
| D-27-18 | Reindex-Zeile ohne Dauer, solange keine Rate dieser Box vorliegt | 27-08, 27-12, 27-14 |
| D-27-19 | IN-01 und IN-02 aus 26-REVIEW mit Regressionstest | 27-03 |
| D-27-20 | fünf Ursachencodes plus Startcode rebuilding, je ein Satz in acht Katalogen | 27-01 (UI-SPEC-Delta), 27-02 (Codes), 27-13 (Kataloge) |

Jede Entscheidung ist mindestens einem Plan zugeordnet; keine Lücke.

## Success Criteria

| SC | Stand | Beleg |
|----|-------|-------|
| SC1: Auswahlfeld mit drei Profilen, Hinweisfläche (Kerne/Speicher, Vorschlag), Knöpfe "Übernehmen und prüfen" und "Bei Sparsam bleiben", ohne Klick Sparsam, kein Erweitert-Bereich | grün | 27-10 SC1/ADM-04-Gates; 27-15 live: Erstaufruf profileStored false, wirksam economy, Vorschlag standard (`raw/01-erstaufruf.txt`); Owner-Abnahme der Fläche per Playwright "approved" |
| SC2: echte Probe mit Verdikt und Ursache, gespeichert nur bei "passt" | grün für int8, fp32-Zweig nur automatisiert | 27-15 live: fits gespeichert (`raw/02`), nofit memory_short und narrow reserve_thin nicht gespeichert (`raw/03`, `raw/04`), Aufwärts ohne Probe 400 probe_required (`raw/06`); fp32-Modellprobe (27-06/27-09) nur in Tests und Python gates 36578517859, live nicht gefahren (470268510 Bytes Download plus Neueinbettung), Owner-Entscheid in 27-15 |
| SC3: Vorab-Rechnung gegen die Speichergrenze, eine Probe gleichzeitig, Zeitdeckel, Nicht-Admin erreicht Probe- und Profilroute nicht | grün | dreiteilig: PHP-Gate und PHPUnit (PHP and store metadata gates 36578517939), info.xml ADMIN für `^/probe$` und `^/probe/state$` (HaRP deploy 36581106370 prüft die Routen samt Level), Live-Schritt in Integration 36578517923 ohne 200; zusätzlich lokal 403 in 27-15 (`raw/07`), busy (`raw/05`), Linux-Kindtests in Python gates 36578517859 |
| SC4: alle neuen Texte in acht Katalogen (16 Dateien) im Gleichstand, Katalog-Gates grün | grün | 27-13: 72 neue Sätze in 16 Dateien, Schlüsselzahl 287, Gate `test_every_sentence_of_the_profile_block_is_in_every_catalogue`; grün in Python gates 36578517859 und lokal (siehe oben) |

## Owner-Abnahme (Task 3)

Status: **abgenommen** (2026-09-29). Keine Issue- oder Store-Entwürfe gewünscht.

Vorzulegen: SC1 bis SC4 (Tabelle oben), Entscheidungs-Tabelle D-27-01 bis D-27-20, Live-Beleg `docs/measurements/2026-09-probe-live/README.md`, CI-Stand (alle grün, HaRP nach Fix 2b9de323).

Resume-Signal: "approved", "approved, Entwürfe bitte" oder beschreibe Befunde. Bei "Entwürfe bitte" legt der Executor Issue- oder Store-Entwürfe nur als Datei unter `C:/Users/Student/Desktop/` ab, postet und ändert nichts.

Owner-Signal: "ok abgenommen"

## Deviations from Plan

**1. [Rule 3 - Blocking] Routen-Ratsche der HaRP-Strecke**
- **Found during:** Task 2 (HaRP deploy 36578517817 rot)
- **Issue:** Store install 6 erwartete fünf geprüfte Routen, das Archiv deklariert sieben
- **Fix:** Liste um `^/probe$:POST:2` und `^/probe/state$:GET:2` erweitert; nach Plan kein eigenmächtiger Umbau, daher erst nach Owner-Freigabe committet und mit erneutem Owner-Wort gepusht
- **Files modified:** .github/workflows/deploy-harp.yml
- **Commit:** 2b9de323

**2. Workflow-Namen:** Der Plan nennt Dateinamen (python.yml, php.yml, integration.yml, docker.yml); die Tabelle führt die tatsächlichen Workflow-Namen, das Abbild heißt "Multi-arch image".

## Lücken

- fp32 nicht live gefahren (aus 27-15 übernommen), nur automatisiert belegt

## Self-Check: PASSED

- Commits 2b9de323, a8e3d7ea, bbb4f406 in der Historie von main, origin/main = 2b9de323
- Lauf-IDs 36578517859, 36578517939, 36578517923, 36578517843, 36578517899, 36578517817, 36581106370 per `gh run view` geprüft
- docs/measurements/2026-09-probe-live/README.md vorhanden
