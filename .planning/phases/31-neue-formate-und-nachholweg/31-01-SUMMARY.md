---
phase: 31-neue-formate-und-nachholweg
plan: 01
subsystem: build/licences (Pins, THIRD-PARTY, Quellpflicht, Workflow-Trigger)
tags: [fmt-03, fmt-04, fmt-05, olefile, xlrd, pillow-heif, gpl, lgpl, reuse, ci-triggers, image-size]
requires: []
provides:
  - "olefile==0.47, xlrd==2.0.2, pillow-heif==1.8.0 exakt gepinnt (pyproject.toml, uv.lock), keine weiteren transitiven Pakete"
  - "THIRD-PARTY.md: drei Paketzeilen, Unterabschnitt pillow-heif mit libheif 1.23.4, libde265 1.1.3 (LGPL-3.0), x265 4.2 (GPL-2.0-or-later), sieben veraltete Versionen korrigiert"
  - "backend/tests/test_third_party_versions.py: jede /app/.venv-Zeile gleich Pin, jeder Pin hat eine Zeile"
  - "scripts/release/corresponding_source.py: vier Quellpakete mit SHA-256, fetch, --verify-only, publish (Pre-Release, Assets im create-Aufruf)"
  - "backend/tests/test_corresponding_source.py: Tabelle, Skript und Pin deckungsgleich"
  - "Workflow-Trigger: kein Nicht-v-Tag startet einen Workflow; backend/tests/test_workflow_tag_triggers.py"
  - "Pre-Release source-1.5-dev.2 mit den vier geprüften Quellpaketen (Spiegel für :dev)"
  - "docs/measurements/2026-10-formate-v15/README.md, Abschnitt Imagegröße"
affects: [31-04 .doc, 31-05 .xls, 31-07 HEIC (Pakete vorhanden), 36 REL-05 (release.yml muss die Quellpakete im create-Aufruf mitgeben)]
tech-stack:
  added: ["olefile 0.47 (BSD-2-Clause)", "xlrd 2.0.2 (BSD-3-Clause)", "pillow-heif 1.8.0 (Quelle BSD-3-Clause, Wheel GPL-2.0-or-later)"]
  patterns: ["Versionsgate Lizenzdatei gegen Pins", "Quellpflicht per gehashten Quellpaketen plus Spiegel-Release", "push-Trigger nur branches plus v-Tag"]
key-files:
  created:
    - backend/tests/test_workflow_tag_triggers.py
    - backend/tests/test_third_party_versions.py
    - backend/tests/test_corresponding_source.py
    - scripts/release/corresponding_source.py
    - docs/measurements/2026-10-formate-v15/README.md
  modified:
    - .github/workflows/python.yml
    - .github/workflows/php.yml
    - .github/workflows/integration.yml
    - .github/workflows/resilience.yml
    - .github/workflows/deploy-harp.yml
    - backend/pyproject.toml
    - backend/uv.lock
    - THIRD-PARTY.md
    - REUSE.toml
    - docs/store-listing.md
decisions:
  - "pillow-heif 1.8.0 bleibt: am 10.10.2026 weiter die neueste Version auf PyPI (1.9.0 nicht erschienen); olefile 0.47 und xlrd 2.0.2 ebenfalls neueste"
  - "Das Repository veröffentlicht unveränderliche Releases: Quellpakete müssen im gh release create mitreisen; REL-05 muss release.yml entsprechend erweitern"
  - "Spiegel für :dev ist source-1.5-dev.2; source-1.5-dev blieb leer (unveränderlich), Text verweist auf .2, nicht gelöscht"
  - "Versionsgate deckt alle drei Python-Tabellen (Zeilen mit Ort /app/.venv), nicht nur die Extraktionstabelle"
metrics:
  duration: "ca. 105 min (davon 11 min volle Suite lokal, 7 min Text-Gates, ca. 45 min CI)"
  completed: 2026-10-11
  tasks: 4
  files: 15
---

# Phase 31 Plan 01: Pakete, Lizenzbelege, Quellpflicht und Imagegröße Summary

olefile 0.47, xlrd 2.0.2 und pillow-heif 1.8.0 sind exakt gepinnt und in THIRD-PARTY.md samt der drei nativen Bibliotheken des HEIF-Wheels (libheif und libde265 LGPL-3.0, x265 GPL-2.0-or-later) belegt; die Quellpflicht ist über vier gehashte Quellpakete, ein Prüfskript und das Pre-Release `source-1.5-dev.2` erfüllt, kein Nicht-v-Tag startet mehr einen Workflow, und das Image wächst komprimiert um 6,18 MB (amd64) bzw. 7,29 MB (arm64).

## Task 1: Tag-Trigger der Workflows

Einordnung vor der Änderung (GitHub wertet `paths` bei einem Tag-Push nicht aus; ein push-Block ohne `branches`/`tags` startet bei jedem Tag):

| Workflow | Trigger-Block (push) vorher | Nicht-v-Tag vorher | nachher |
|---|---|---|---|
| python.yml | `push: paths: [backend/**, scripts/**, ...]` | ja | nein (`branches: ['**']`, `tags: ['v[0-9]+.[0-9]+.[0-9]+']`) |
| php.yml | `push: paths: [php/**, backend/appinfo/**, ...]` | ja | nein (wie oben) |
| integration.yml | `push: paths: [php/**, backend/**, testdata/corpus/**, ...]` | ja | nein (wie oben) |
| resilience.yml | `push: paths: [backend/**, php/**, ...]` | ja | nein (wie oben) |
| deploy-harp.yml | `push: paths: [backend/**, php/**, ..., scripts/release/**]` | ja | nein (wie oben) |
| docker.yml | `push: branches: [main]`, `tags: ['v[0-9]+.[0-9]+.[0-9]+']`, `paths: [...]` | nein | nein (unverändert) |
| release.yml | `push: tags: ['v[0-9]+.[0-9]+.[0-9]+']` | nein | nein (unverändert) |
| scorecard.yml | `push: branches: [main]` | nein | nein (unverändert) |
| security.yml | `push: branches: [main]` | nein | nein (unverändert) |
| issue-notify, measure, probe-92d, store-submit | kein push-Trigger | nein | nein |

v-Tags lösen die fünf geänderten Workflows wie bisher aus (Release-Tags laufen weiter durch die Prüfungen); die `paths`-Listen sind unverändert (im Test gegen die Liste vor der Änderung verglichen).

- RED (einzeln): `11 failed, 16 passed` (`test_every_push_block_names_branches_or_tags` für alle fünf, `test_the_former_paths_only_workflows_carry_both_filters` für alle fünf, `test_no_workflow_starts_on_the_source_mirror_tag`: `AssertionError: deploy-harp.yml`). Die 16 grünen Fälle sind die Selbsttests der Filter-Nachbildung und die vier schon richtigen Workflows.
- GREEN: `27 passed`; alle 447 Tests, die Workflow-Dateien lesen, grün.
- Commit `0fc8da9e`, allein gepusht 22:16:09Z. Läufe, alle success: Python gates **38090784834**, PHP and store metadata gates **38090784785**, Integration **38090784839**, Resilience **38090784771**, HaRP deploy **38090784754**, Multi-arch image **38090784794**, Security scans 38090784710, OpenSSF Scorecard 38090784793.

## Task 2: Pins, Lizenzbelege, Versionsgate

- PyPI am 10.10.2026: pillow-heif 1.8.0 (Upload 2026-09-22) ist weiter die neueste Version, 1.9.0 nicht erschienen; cp313-Wheels `manylinux_2_26/2_28_aarch64` und `manylinux_2_27/2_28_x86_64`. olefile 0.47 und xlrd 2.0.2 ebenfalls neueste. Gewählt wie geplant.
- `uv add olefile==0.47 xlrd==2.0.2 pillow-heif==1.8.0`: Paketnamen in uv.lock 70 auf 73, Diff genau `olefile`, `pillow-heif`, `xlrd`; kein unerwartetes transitives Paket (pillow war schon da).
- Gebündelte Bibliotheken aus `LICENSES_bundled.txt` des Wheels und aus den Dateien in `pillow_heif.libs` (beide manylinux-Wheels): libheif 1.23.4, libde265 1.1.3, libx265 mit eingebauter Version `4.2+1-e444744`.
- RED (einzeln): `3 failed, 3 passed`, rote Zeile: `THIRD-PARTY.md version against pin: {'pypdf': ('6.16.1', '6.19.0'), 'striprtf': ('0.0.32', '0.0.33'), 'charset-normalizer': ('3.5.1', '3.5.2'), 'lxml': ('6.1.1', '6.1.3'), 'numpy': ('2.5.2', '2.5.3'), 'semantic-text-splitter': ('0.32.0', '0.33.0'), 'fastapi': ('0.141.1', '0.142.2')}`, dazu `assert None == '0.47'` und `'libheif' in ...`.
- GREEN: `6 passed`; `grep -n "6.16.1\|3.5.1\|6.1.1\|0.0.32" THIRD-PARTY.md` leer.
- `uvx --from "reuse[charset-normalizer]" reuse lint` (reuse 6.2.0): "Congratulations! Your project is compliant with version 3.3 of the REUSE Specification", 2536/2536 Dateien mit Copyright und Lizenz, 0 fehlende, 0 ungültige.
- Volle Suite lokal: **4885 passed, 25 skipped** (658,7 s); ruff, format (200 Dateien), pyright latest 0 Fehler, vulture grün.
- Commit `5cd885cd`.

## Task 3: Korrespondierender Quelltext und Pre-Release

Quellpakete aus `libheif/build_libs.py` des sdist pillow_heif-1.8.0 (enthält `LIBX265_URL`, `LIBDE265_URL`, `LIBHEIF_URL`); der Upstream-Workflow `.github/workflows/wheels.yml` am Tag `v1.8.0` (Commit `1486e9fb...`) ruft genau dieses Skript als `CIBW_BEFORE_ALL_LINUX`. Das sdist ist damit Träger der Build-Skripte.

| Quellpaket | SHA-256 | Lizenz |
|---|---|---|
| pillow_heif-1.8.0.tar.gz | e47c27432c6fd3d66c22f0de9f27fd379383b646c947520bc485854ce72060d0 | BSD-3-Clause |
| x265_4.2.tar.gz | 40b1ea0453e0309f0eba934e0ddf533f8f6295966679e8894e8f1c1c8d5e1210 | GPL-2.0-or-later |
| libde265-1.1.3.tar.gz | 554228bd17788c99a7e63b37ab5634722190e6e2bf60c1dcb01cef328e133905 | LGPL-3.0 |
| libheif-1.23.4.tar.gz | d0c02b4b0e978f34a1974b6f3eea7975a537bf7a9195ffeea38e7242ff316fdd | LGPL-3.0 |

`x265Version.txt` im Quellpaket (`releasetag: 4.2`, `repositorychangeset: e444744`, `releasetagdistance: 1`) stimmt mit der Version im Wheel und im Image (`4.2+1-e444744`) überein. Die Quelldateien von x265 tragen "either version 2 of the License, or (at your option) any later version".

- RED (einzeln): `10 errors`, `FileNotFoundError: ... scripts\release\corresponding_source.py`; danach mit Skript, ohne Tabelle: `1 failed, 9 passed` (`assert '### Corresponding source ...' in ...`).
- GREEN: `10 passed`. Gegenproben: Hashvergleich in `verify` ausgeschaltet → `test_verify_only_fails_on_a_manipulated_file` rot; Tag-Abweisung ausgeschaltet → drei Fälle `test_publish_refuses_a_store_release_tag` rot; Original zurück, grün.
- fetch-Lauf (frisches Verzeichnis): vier Zeilen `ok (fetched) <name> <sha256>`, Exit 0; `--verify-only` danach vier Zeilen `ok`, Exit 0.
- Commit `ee3fdebf`.

**Befund beim Anlegen (Rule 1):** Das Repository hat unveränderliche Releases aktiv (`gh api .../immutable-releases` → `enabled: true`; auch v1.4.2 hat `isImmutable: true`). Der erste `publish`-Lauf (`gh release create` ohne Assets, dann `gh release upload`) legte `source-1.5-dev` um 22:51:19Z an und bekam beim Upload `HTTP 422: Cannot upload assets to an immutable release`. Das Pre-Release blieb leer und lässt sich nicht mehr füllen.

- Fix: `publish` gibt die vier Quellpakete jetzt im `gh release create` mit (gh legt Entwurf an, lädt hoch, veröffentlicht zuletzt) und weist ein schon veröffentlichtes unveränderliches Release ab (belegt: `refusing source-1.5-dev: the release is published and immutable ...`, Exit 1). RED: `1 failed, 10 passed` (`test_publish_attaches_exactly_the_four_archives_when_it_creates`), GREEN `11 passed`. REL-05-Checkliste in docs/store-listing.md umgeschrieben: `gh release upload vX.Y.Z` nach release.yml würde genauso scheitern, release.yml muss die vier Dateien im eigenen `gh release create` mitgeben (bei REL-05). Commit `f124673c`.
- Neues Pre-Release **https://github.com/street1983nk/nextcloud-search/releases/tag/source-1.5-dev.2**, angelegt 22:55:40Z (Start 22:55:28Z) auf `0fc8da9e` (= origin/main zu dem Zeitpunkt, Task-1-Commit seit 22:16:09Z dort und grün), `isPrerelease: true`, `isImmutable: true`, Titel "Source mirror: corresponding source for the dev image", Text = englische Faktenliste aus `ARCHIVES` (eine Zeile je Quellpaket mit SHA-256, "Licences and details: THIRD-PARTY.md").
- Assets: libde265-1.1.3.tar.gz (324452 B), libheif-1.23.4.tar.gz (2217221 B), pillow_heif-1.8.0.tar.gz (17395353 B), x265_4.2.tar.gz (1833442 B); GitHub-Digests gleich der Tabelle. `gh release download source-1.5-dev.2 -D <scratch>` plus `--verify-only`: vier Zeilen `ok`, Exit 0.
- `source-1.5-dev`: nicht gelöscht; Text per `gh release edit` auf "No assets ... The corresponding source mirror is .../source-1.5-dev.2" gesetzt (0 Assets, Pre-Release).
- Latest: `gh api repos/.../releases/latest` → `v1.4.2`, `prerelease=false` (`gh release view --json isLatest` kennt gh 2.92.0 nicht, daher die API).
- Läufe: `gh run list --limit 30 --json databaseId,event,headBranch,createdAt,workflowName` um 22:55:16Z (4 min nach dem ersten Tag) und um 22:57:52Z (2:12 min nach dem zweiten): **kein Lauf seit 22:51:12Z überhaupt**, kein Lauf mit `headBranch` `source-1.5-dev` oder `source-1.5-dev.2`, kein Push-Ereignis eines dieser Tags. Neuester Lauf war 38090784839 (22:16:12Z, push main, Task 1). Fremde Läufe im Fenster: keine.

## Task 4: Imagegröße

Messbericht `docs/measurements/2026-10-formate-v15/README.md`, Abschnitt "Imagegröße" (Commit `bc287c11`).

| Plattform | vorher (`0fc8da9e`) | nachher (`f124673c`) | Differenz komprimiert | entpackt, drei Pakete |
|---|---|---|---|---|
| amd64 | `sha256:457369ef...` 303,04 MB | `sha256:38b8b8d2...` 309,22 MB | **+6,18 MB** | 28,44 MB im Image (libx265 22,79 MB) |
| arm64 | `sha256:9db88fdc...` 298,63 MB | `sha256:920b7bcd...` 305,92 MB | **+7,29 MB** | 16,67 MB aus den Wheels (libx265 11,43 MB) plus Bytecode |

Index vorher `sha256:ff7fe896...`, nachher `sha256:766907ff...` (= Tag `f124673c...`). Research erwartete rund 16 MB entpackt (libx265 11,4 MB): trifft arm64 genau; auf amd64 ist libx265 doppelt so groß.

Läufe des Pushes `5cd885cd..f124673c` (22:57:58Z): Multi-arch image **38093349796** (amd64, arm64, Merge grün), Python gates **38093349938** (4907 passed, 14 skipped), Integration 38093349839, Resilience 38093349789, Security scans 38093349790, OpenSSF Scorecard 38093349862, HaRP deploy **38093349846** (stable33/34/35, x86 und arm, alle success). Push des Berichts `bc287c11`: Python gates **38094436329**, Security scans 38094436373, OpenSSF Scorecard 38094436337, alle success.

## Commits

| Commit | Inhalt |
|---|---|
| 0fc8da9e | ci(31-01): workflows start on branches and release tags only |
| 5cd885cd | build(31-01): olefile, xlrd and pillow-heif pinned with their licences |
| ee3fdebf | build(31-01): corresponding source of the GPL and LGPL libraries in the image |
| f124673c | fix(31-01): source mirror attaches the archives in the create call |
| bc287c11 | docs(31-01): image growth of the three format packages, amd64 and arm64 |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Spiegel-Upload scheiterte an unveränderlichen Releases**
- **Found during:** Task 3 (Anlegen des Pre-Release)
- **Issue:** create ohne Assets plus späteres upload; das Repository veröffentlicht unveränderliche Releases, Upload mit HTTP 422 abgewiesen, `source-1.5-dev` blieb leer. Dieselbe Mechanik stand im Plan für REL-05 (`gh release upload <tag>` nach release.yml) und wäre dort genauso gescheitert.
- **Fix:** Assets im create-Aufruf, Abweisung veröffentlichter unveränderlicher Releases, REL-05-Checkliste korrigiert, Spiegel unter neuem Tag `source-1.5-dev.2` (das alte Tag ist durch die Unveränderlichkeit belegt).
- **Files modified:** scripts/release/corresponding_source.py, backend/tests/test_corresponding_source.py, backend/tests/test_workflow_tag_triggers.py, THIRD-PARTY.md, docs/store-listing.md
- **Commit:** f124673c

**2. [Rule 1 - Bug] docker.yml startete doch beim Trigger-Commit**
- **Found during:** Task 1
- **Issue:** Der Plan nahm an, der Trigger-Commit berühre backend/ nicht; die Testdatei liegt aber unter `backend/tests/`, also startete docker.yml (38090784794).
- **Fix:** keine Codeänderung nötig. Der Bau lieferte bytegleiche Plattform-Manifeste (amd64 `457369ef...`, arm64 `9db88fdc...` vor und nach dem Lauf gleich), nur der Index-Digest wechselte; die Vorher-Messung nutzt das Image von `0fc8da9e` und bleibt gültig.

**3. [Rule 2] Versionsgate über alle Python-Tabellen**
- **Found during:** Task 2
- **Issue:** Neben den vier aus der Research veralteten Zeilen lagen auch numpy (2.5.2 statt 2.5.3), semantic-text-splitter (0.32.0 statt 0.33.0) und fastapi (0.141.1 statt 0.142.2) hinter den Pins.
- **Fix:** Gate liest jede Tabellenzeile mit Ort `/app/.venv`, alle sieben korrigiert.
- **Commit:** 5cd885cd

**4. [Rule 1] Gesperrter Wortstamm in docs/store-listing.md**
- **Found during:** Task 3 (test_store_metadata, Vokabelregel E-H2)
- **Fix:** deutscher Abschnitt formuliert mit "Quellpakete" und "Store-Pakete"; THIRD-PARTY.md (englisch) ist nicht betroffen.

## Gates

- Vor `0fc8da9e`: ruff, format (199), pyright latest 0, vulture grün; 447 Workflow-Tests und 55 test_public_artifacts grün.
- Vor `5cd885cd`: volle Suite 4885 passed, 25 skipped; alle statischen Gates grün; reuse lint grün.
- Vor `ee3fdebf` und `f124673c`: statische Gates plus `ruff check/format --config pyproject.toml ../scripts` grün; 37 Testdateien, die scripts/, Store-Texte oder THIRD-PARTY lesen, 1819 passed; nach dem Fix 180 passed (Quellpaket-, Versions-, Trigger-, Store- und Artefakt-Tests).
- Vor `bc287c11`: test_measurement_scripts und test_public_artifacts 532 passed.
- `backend/src/findling` und `php/` unberührt, Baumhash-Pins bewegen sich nicht.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche über das Threat Model hinaus; T-31-SC (uv.lock-Diff), T-31-01c (Trigger-Gate plus Laufbeleg), T-31-01b (gehashte Quellpakete, Spiegel) und T-31-01 (Versionsgate, Bibliotheken aus dem tatsächlichen Wheel) sind umgesetzt.

## Requirements

FMT-03, FMT-04 und FMT-05 stehen im Frontmatter des Plans, sind aber erst mit den Extraktoren (31-04 bis 31-07) erfüllt. `gsd-sdk query requirements.mark-complete` hatte sie abgehakt; das wurde in REQUIREMENTS.md zurückgenommen. STATE.md und ROADMAP.md von Hand geprüft und korrigiert (Phase 31, 1/15, nächster Plan 31-02).

## Offene Punkte

- REL-05 (Phase 36): release.yml muss die vier Quellpakete im eigenen `gh release create` mitgeben (Fetch-Schritt davor); Checkliste in docs/store-listing.md.
- Leeres unveränderliches Pre-Release `source-1.5-dev` bleibt mit Verweistext stehen; Löschen nur mit Owner-Wort.
- Kommentar zu semantic-text-splitter in backend/pyproject.toml nennt noch 0.32.0 (Pin 0.33.0), außerhalb des Plans, nicht angefasst.

## Self-Check: PASSED

Alle fünf neuen Dateien vorhanden, alle fünf Commits in der Historie, origin/main auf bc287c11.
