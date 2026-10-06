---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 11
subsystem: release/upgrade-proof
tags: [rel-04, k6, migration, upgrade, recheck, d-29-01, d-29-10, deploy-harp]
requires:
  - "29-03: Store-Texte (Stand der info.xml)"
  - "29-05: Sidecar-Regel skipped(system_file)"
  - "29-07: TIFF-Shim Grau+Extra (_SHIM_KEYS)"
  - "29-09: Nachprüfung recheck_1_4_0"
  - "29-10: Pins Stand 88 PHP-Dateien"
provides:
  - "php/lib/Migration/Version001400Date20261006000000.php (verwirft backend_app_version)"
  - "Beide Hälften auf 1.4.0 (php info.xml, backend info.xml version + image-tag)"
  - ".github/fixtures/upgrade-seed-grey-extra.tif + scripts/ci/make_upgrade_seed_tiff.py"
  - "deploy-harp.yml: UPGRADE_FROM_TAG v1.3.2, Saat 2b, neuer Schritt 3c, Zusicherungen 5 (acht)"
  - "backend/tests/test_upgrade_seed_steps.py (Workflow-Gate), test_upgrade_seed_fixture.py"
affects:
  - "29-13: erster CI-Lauf beweist Upgrade 1.3.2 -> 1.4.0 und die Nachprüfung an echten Dateien"
tech-stack:
  added: []
  patterns:
    - "Saat aus echten Dateien, vom ALTEN Container geurteilt, statt SQL-gesäter Verdikte"
    - "Vorher-Werte, die der Snapshot nicht trägt, in eigenem Schritt (3c) statt im wachstumsgesperrten 3er-Block"
    - "Container-Abfragen per docker exec -i python - < seed-probe.py, sqlite read-only (mode=ro)"
key-files:
  created:
    - php/lib/Migration/Version001400Date20261006000000.php
    - php/tests/Unit/Version001400Date20261006000000Test.php
    - scripts/ci/make_upgrade_seed_tiff.py
    - .github/fixtures/upgrade-seed-grey-extra.tif
    - backend/tests/test_upgrade_seed_fixture.py
    - backend/tests/test_upgrade_seed_steps.py
  modified:
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - backend/tests/test_measurement_scripts.py
    - .github/workflows/deploy-harp.yml
    - .gitattributes
decisions:
  - "SEED_WORD = quorvintax (Wort der alten gone-Saat behalten, Env SEED_TERM in SEED_WORD umbenannt); Bild trägt es zweimal plus eine Zeile, damit OCR >= 20 Zeichen liefert"
  - "Saat-Trigger in 2b: files:scan + findling:index --restart + cron-Schleife (wie Schritt 2); unveränderte Dateien laufen über den fast path"
  - "Gegenprobe von Zusicherung 6 ist jetzt die Marke recheck_1_4_0 (vorher absent, nachher done); Sprachmarke bleibt als unverändert-leer"
  - "Neue-Einbettung-Beweis: embedding_version unverändert + Digest der chunks-Zeilen ohne das Saatbild unverändert"
  - "Schritt 5 ohne ${{ }}-Ausdruck (Matrixwerte als env wie Schritt 6), damit die 21000-Zeichen-Grenze nicht greift"
metrics:
  duration: "ca. 2 h 15 min"
  completed: 2026-10-06
  tasks: 3
  files: 11
---

# Phase 29 Plan 11: Versionssprung 1.4.0, Pflicht-Migration und Upgrade-Strecke ab v1.3.2 Summary

Beide Hälften stehen auf 1.4.0 mit der Minor-Migration Version001400Date20261006000000; die Upgrade-Strecke von deploy-harp.yml startet ab v1.3.2 und beweist die Nachprüfung D-29-10 an zwei echten Dateien (AppleDouble-Sidecar und Grau+Extra-TIFF), die der 1.3.2-Container nachweislich als failed(corrupt) urteilt, mit exakt hergeleiteten Zählern.

## Was gebaut wurde

**Task 1 (`731a8df8`): Migration und Versionen**
- `Version001400Date20261006000000`: Mechanik von Version001300Date20260924000000 (IAppConfig, postSchemaChange löscht `ExAppService::KEY_BACKEND_VERSION`, Ausgabe nur mit Version). Klassenkommentar trägt die drei Pflichtsätze ("Every minor step needs a migration of this shape", "Nothing is asked of the container here", "The class name and the file name have to be identical to the character") und verweist die Nachprüfung in den Container (29-09).
- PHPUnit-Test mit den sechs Fällen des Vorbilds (Löschen, nichts aufgezeichnet, nie setValueString, Version in der Ausgabe, zweiter Lauf no-op, Konstruktor nur IAppConfig); schemaClosure schlägt laut fehl, falls gerufen.
- `php/appinfo/info.xml` und `backend/appinfo/info.xml` `<version>1.4.0</version>`, `<image-tag>1.4.0</image-tag>`; `backend/pyproject.toml` bleibt 0.1.0.
- PHP-Pin: 88 -> **90** Dateien, Hash `f22c3b8861d853c4eb23502259d84a4f03361fc6fdc49cd58a9332c841e4a5b5`. Gemessen über den realen Baum (`**/*.php`); die Erwartung 90 aus dem Plan trifft genau zu. info.xml zählt nicht mit (Rezept liest nur .php).

**Task 2 (`0d789660`): Fixture, Generator, v1.3.2, Saat 2b**
- `scripts/ci/make_upgrade_seed_tiff.py`: LA-Bild 960x400, Default-Font Größe 72, Zeilen `quorvintax` / `Kisten im Keller` / `quorvintax`, raw, Tag 338 auf 0 gepatcht, per Hand auf big-endian gedreht. 768146 Bytes, deterministisch.
- `.github/fixtures/upgrade-seed-grey-extra.tif` committet; `.gitattributes` bekommt `.github/fixtures/** -text`.
- `UPGRADE_FROM_TAG: v1.3.2` mit fortgeschriebenem Historienkommentar. Vorher geprüft: `gh release view v1.3.2 --json assets` liefert findling.tar.gz(.sig) und findling_backend.tar.gz(.sig); `ghcr.io/street1983nk/findling_backend:1.3.2` antwortet anonym als Index amd64+arm64.
- "Store upgrade 2b" neu: Fixture und `._seed-notes.docx` (26 Byte AppleDouble-Kopf `00 05 16 07`, per `od` geprüft) unter `data/testuser/files/fix-seed/`, files:scan, `findling:index --restart`, cron-Schleife bis beide Dateien im state.db ein Urteil haben; dann fail-closed: beide `failed/corrupt` in state.db UND in `oc_findling_file_state`, Saatwort 0 Treffer vorher und nachher; `UPGRADE_SEED_TIFF_ID`/`UPGRADE_SEED_SIDECAR_ID` nach GITHUB_ENV. Hilfsdateien `seed-probe.py`/`seed-probe.sh` (verdict, meta, chunks, stock) für 3c und 5.
- gone-Saat restlos entfernt (`upgrade-gone-seed` 0 Treffer), `SEED_TERM` -> `SEED_WORD`.

**Task 3 (`051601c8`): Zusicherungen**
- Neuer Schritt "Store upgrade 3c" (nach 3b, vor 4): Marke `recheck_1_4_0` muss `absent` sein, wartet bis `embedding_version` gesetzt ist, hält Vektorbestand fest, beide Saatdateien ohne Chunks; exportiert `UPGRADE_EMBEDDING_MARK`, `UPGRADE_VECTOR_STOCK`.
- "Store upgrade 5" (jetzt "the eight assurances"): wartet nur per Poller (kein cron.php) mit `UPGRADE_DRAIN_BUDGET_SECONDS` auf open=0, recheck done, Sidecar `skipped/system_file`, Bild `indexed/` mit Chunks. 3: Zähler exakt (Tabelle unten). 3b: Sidecar skipped(system_file) in state.db und Nextcloud, Bild indexed ohne Nextcloud-Verdikt, Saatwort findet genau `attributes.fileId == UPGRADE_SEED_TIFF_ID`. 6: recheck-Marke done, Sprachmarke vorher und nachher leer. 8: Embedding-Marke gleich, Chunk-Digest ohne das Bild gleich, Bild hat Chunks, `profileEffective == economy`. indexVersion bleibt in Zusicherung 2.
- "Store upgrade 4": Zweig "the instance performed the app update" unverändert fail-closed, Kommentar nennt ERROR_UP_TO_DATE als Fehler; Texte auf "1.4.0 against the 1.3.2" (`grep -c "1.3.0 against the 1.2.0"` = 0).
- "Store upgrade 3": nur die Sprachmarken-Bedingung (siehe Abweichung 1); run-Block 20726 -> 20069 Zeichen.

## Hergeleitete Sollwerte je Zähler von Block 3 (vorher = Snapshot nach 2b, nachher = nach Upgrade und Nachprüfung)

| Zähler | Soll | Herleitung |
|---|---|---|
| terms.Belehrung/Auszug/Erinnerung | unverändert | Saat enthält keines der Wörter |
| spanish | unverändert (0) | Zusicherung 7 |
| container.docs | +1 | Bild kommt in den Index, Sidecar nie |
| container.indexed | +1 | Bild |
| container.skipped | +1 | Sidecar skipped(system_file) |
| container.failed | -2 | beide Saatdateien nicht mehr failed |
| container.rebuildState | unverändert | nichts baut um |
| nextcloud.skipped | +1 | Sidecar mit neuem Reason erfasst |
| nextcloud.failed | -2 | Bild-Verdikt widerrufen, Sidecar-Verdikt ersetzt |
| nextcloud.scheduled | unverändert (0) | Nachprüfungszeilen vor dem Snapshot abgearbeitet |
| nextcloud.running | unverändert (0) | dto. |

Die failed(corrupt)-PDFs des Referenzkorpus (24, 26, 27, 28, 33) werden von der Nachprüfung ebenfalls neu eingereiht; Soll ist, dass 1.4.0 sie wieder failed(corrupt) urteilt und sie damit nichts bewegen. Urteilt 1.4.0 eines davon anders, wird der Zähler rot und benennt es: das ist ein Befund über das Release, kein Anlass zum Lockern.

## Verifikation (lokal)

- `uv run pytest -q tests/test_lockstep_versions.py tests/test_measurement_scripts.py tests/test_store_metadata.py tests/test_info_xml_defaults.py`: 584 passed.
- `tests/test_upgrade_seed_steps.py tests/test_upgrade_seed_fixture.py tests/test_language_proof_steps.py tests/test_v13_wechsel.py`: 117 passed (bash -n lief echt, kein Skip).
- Alle Tests, die deploy-harp.yml lesen: 1060 passed, 1 skipped.
- Volle Suite nach Task 1: 4670 passed, 25 skipped; nach Task 3: 4705 passed, 25 skipped (PYTHONUTF8=1).
- ruff check/format (backend und scripts), pyright latest 0 Fehler, vulture sauber; YAML lädt; `bash -n` aller Store-upgrade-Blöcke grün.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Sprachmarken-Bedingung von Store upgrade 3 und Zusicherung 6 wären ab v1.3.2 rot gewesen**
- **Found during:** Task 3
- **Issue:** Schritt 3 verlangte `.marks.languages == null` und Zusicherung 6 "vorher null, nachher leer", weil der Bericht von 1.2.0 den Schlüssel nicht hatte. `git show v1.3.2:backend/src/findling/tools/index_status.py` belegt: 1.3.2 hat den Schlüssel (leer, solange kein Umbau stempelt). Beide Prüfungen wären auf einer gesunden Installation rot gewesen; der Plan und die Research hatten das nicht erfasst.
- **Fix:** Schritt 3 verlangt `== ""` (Block dabei kürzer geworden); Zusicherung 6 nimmt als Gegenprobe die Marke `recheck_1_4_0` (3c: absent, 5: done) und hält die Sprachmarke als vorher und nachher leer.
- **Files modified:** .github/workflows/deploy-harp.yml
- **Commit:** 051601c8

**2. [Rule 2 - Correctness] Saatbild braucht mindestens 20 OCR-Zeichen**
- **Found during:** Task 2
- **Issue:** Ein Bild nur mit dem Saatwort (Plan-Beispiel "Kronleuchterfisch", 17 Zeichen; "quorvintax", 10) endet in `extract/image.py` als skipped(empty_text) (`_MIN_OCR_CHARS = 20`), der Beweis wäre rot.
- **Fix:** Drei Zeilen (Saatwort zweimal plus "Kisten im Keller"), Fixture-Test prüft Länge, Mindestkante 640 und Seitenverhältnis gegen die Konstanten von image.py.
- **Commit:** 0d789660

**3. [Rule 2 - Correctness] Vorher-Werte für "keine Neu-Einbettung" und Gegenprobe in eigenem Schritt 3c**
- **Issue:** Der Snapshot von Schritt 3 trägt weder Embedding-Marke noch Vektorbestand noch recheck-Marke, und sein run-Block darf nicht wachsen.
- **Fix:** Neuer Schritt "Store upgrade 3c" (im Gate per Name geprüft).
- **Commit:** 051601c8

**4. [Rule 3 - Blocking] Schritt 5 ohne `${{ }}`-Ausdruck**
- **Issue:** Schritt 5 enthielt `${{ matrix.* }}` in der Run-Summary, damit gilt die 21000-Zeichen-Grenze; der Block wuchs von 14419 auf 17492 Zeichen.
- **Fix:** Matrixwerte als `env` (Muster von Schritt 6); Gate prüft, dass Schritt 5 ausdrucksfrei bleibt.
- **Commit:** 051601c8

**5. [Rule 2] `.gitattributes`: `.github/fixtures/** -text`**, damit autocrlf das byte-genau geprüfte Fixture nie umschreibt (Commit 0d789660).

**6. Längengrenze von Schritt 3:** Die Grenze ist im Gate als Konstante `SNAPSHOT_RUN_MAX = 20726` gepinnt (gemessen vor Task 3 per yaml auf dem Baum von b013af40 plus Task 2, Schritt 3 war dort unverändert).

## Offene Punkte / ehrliche Grenzen

- **PHP-Syntax lokal nicht geprüft:** kein PHP, Docker-Daemon nicht erreichbar (`dockerDesktopLinuxEngine` fehlt). `php -l` und PHPUnit für Migration und Test belegt erst die CI in 29-13.
- **OCR des Saatworts nicht lokal belegt:** kein Tesseract auf der Maschine. Das Bild ist sauber gerendert (Vorschau geprüft), das Saatwort steht zweimal; den Treffer belegt erst der CI-Lauf in 29-13.
- **Annahmen, die der erste Lauf fail-closed prüft:** 1.3.2 meldet beide Saatdateien als failed(corrupt) an Nextcloud (2b bricht sonst mit Befund ab); `embedding_version` ist nach dem Drain gesetzt (3c wartet mit Frist, sonst rot); der Requeue der Korpus-PDFs ändert nichts (Zusicherung 3 sonst rot mit Zählername); `profileEffective` lautet nach dem Upgrade `economy` (D-29-01).
- **Blinder Fleck des Chunk-Digests** im Workflow-Kommentar benannt: Würden genau die Zeilen mit den höchsten chunk_ids in identischer Form neu geschrieben, wäre der Digest gleich.
- `yaml` im Test kommt transitiv über huggingface-hub (fastembed) in die Umgebung; kein neues Paket.
- Kein Push (29-13).

## Threat Flags

Keine neue Oberfläche. Die Saat-Hilfsdateien lesen state.db/vectors.db read-only im CI-Container und geben nur Zustände, Reasons, Marken und Zählwerte aus (T-29-40: Fixture selbst erzeugt, nur Saatwort).

## Known Stubs

Keine.

## Self-Check: PASSED

- Alle sechs neuen Dateien vorhanden (Migration, PHPUnit-Test, Generator, Fixture, zwei Tests)
- Commits 731a8df8, 0d789660, 051601c8 im Log
