---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 08
subsystem: release, ci (deploy-harp)
tags: [release, 1.6.3, upgrade-proof, coverage, doc-key, hint]
requires:
  - 43-19 (letzter Code-Plan vor dem Bump, de-Katalog 366, PHP-Baumhash 20dac366)
  - 43-20 (REFUSAL_RENEW_MARK, CHANGELOG-Punkt 7)
provides:
  - Version 1.6.3 an allen Lockstep-Stellen (zwei version, ein image-tag, sechs Links)
  - CHANGELOG [1.6.3] mit Added, Fixed, Known limitations und Linkdefinition v1.6.2...v1.6.3
  - Store-Listing-Abschnitt "# Entwurf v1.6.3, Stand Plan 43-08 (08.11.2026)"
  - Zusicherungen 14 bis 18 in "Store upgrade 5" (Migration, Hinweis, Coverage-Route, Stempel, doc_key-Backfill)
affects:
  - 43-09 (Audit des Deltas v1.6.2..Kopf)
  - 43-10 (Testbuild)
  - 43-12/43-13 (Owner-Runde: Store-Entwurf, Wortlaute Block V)
key-files:
  created: []
  modified:
    - backend/appinfo/info.xml
    - php/appinfo/info.xml
    - CHANGELOG.md
    - docs/store-listing.md
    - .github/workflows/deploy-harp.yml
    - backend/tests/test_upgrade_seed_steps.py
    - backend/tests/test_cert_rotation_steps.py
decisions:
  - "Zusicherung 15 liest beide Werte in Store upgrade 4 (Zählerzeilen VOR occ upgrade, Hinweis-Flag direkt DANACH), weil der erste Overview-Abruf das pending 1 zum Zeitstempel stempelt; danach wäre 1 nie mehr beobachtbar"
  - "Die Warteschleife von 16/17 nutzt UPGRADE_DRAIN_BUDGET_SECONDS (kein zweites erfundenes Budget); ein transienter legacyReason=missing bricht die Schleife nicht ab, geurteilt wird nach der Schleife"
  - "Fünfter Known-limitations-Satz (SMB ohne Erweiterung unter etwa 420 KB/s) aus 43-18-SUMMARY übernommen, die den Satz ausdrücklich 'für 43-08' formuliert hat"
metrics:
  duration: "ca. 2 h (lokale Arbeit; CI-Teil offen)"
  completed: 2026-11-08
  tasks: 1 von 3 (Task 2 Checkpoint und Task 3 Push stehen aus)
  commits: 2
---

# Phase 43 Plan 08: Release-Vorbereitung 1.6.3 Summary

1.6.3 an allen Lockstep-Stellen, CHANGELOG mit Known limitations aus 43-17 bis 43-20, Store-Entwurf für die Owner-Runde, Upgrade-Strecke ab v1.5.0 mit fünf neuen Zusicherungen (Migration, Hinweis-Flag, Coverage-Route, Stempel D-43-12, doc_key-Backfill D-43-14); STOPP-Prüfung 1.6.3 bestanden. NUR lokale Arbeit: Push, Dispatch und CI-Beleg warten auf die Owner-Freigabe (Task 2, Checkpoint beim Koordinator).

## Commits

| Hash | Nachricht |
|------|-----------|
| 844d5e8c | chore(43-08): version 1.6.3 in both apps |
| dd79d073 | ci(43-08): the upgrade proof checks the migration, the coverage route and the hint of 1.6.3 |

Autor street1983nk <k.cherif@outlook.de>, ohne Trailer, keine closes-Wörter (je geprüft).

## Task 1: Bump, CHANGELOG, Store-Entwurf, Strecke, STOPP-Prüfung

- `git diff v1.6.2 -- backend/appinfo/info.xml php/appinfo/info.xml` (an 844d5e8c): nur zweimal `<version>1.6.3</version>`, `<image-tag>1.6.3</image-tag>` und die sechs Links `blob/v1.6.2` -> `blob/v1.6.3`; kein Byte an Namen und Beschreibungen.
- CHANGELOG `## [1.6.3] - 2026-11-08`: Added 1 (Hinweis, Zähl-Satz, Zahl nicht lesbarer Dateien), Fixed 6 (Sweep, Zählung pro Dokument, Nenner je Share-Gruppe, gelöschte Dateien, SMB ohne php-smbclient, gateway_error-Nachprüfung), Known limitations 5; `[Unreleased]` leer, Linkdefinition `compare/v1.6.2...v1.6.3`. Wortlaut der Grenzen gegen die SUMMARYs 43-17/43-18 geprüft (469 MiB, FINDLING_MAX_FILE_BYTES 50 MB, 420 KB/s, 20-s-timeout bestätigt).
- docs/store-listing.md: "# Entwurf v1.6.3, Stand Plan 43-08 (08.11.2026)" vor "# Release 1.6.2"; Namen/Beschreibungen zeichengleich zu 1.6.2, sechs neue Satzgruppen en/de/fr aus 43-TEXTE.md (H b, Z a, U a, L a freigegeben 07.11.; Block V + SMB-Zusatzsatz zur Freigabe in 43-12), Entwurf der englischen Release-Notiz.
- Konsistenz-grep `blob/v1.6.3` außerhalb der erlaubten Dateien: leer.
- deploy-harp.yml: `UPGRADE_FROM_TAG: v1.5.0` bleibt; Begründungssatz zu 1.6.3 unter dem v1.5.0-Absatz (eine Migration, nur ein AppConfig-Flag; Meta-Schlüssel storage_sweep_at, doc_key_backfill_after, refusal_streaks_1_6_3, Plan 43-20); Kommentare "the tree carries 1.6.3 (1.6.2 until 2026-11-08, ...)", "installed_version 1.6.3", Sprung-Kommentar REL-06, Image-Tag-Kommentar.
- "Store upgrade 4" liest neu: `oc_findling_scan_stats`-Zeilen VOR occ upgrade (`UPGRADE_SCAN_ROWS_BEFORE`) und das Flag `coverage_per_document_hint` direkt DANACH (`UPGRADE_HINT_AFTER_OCC`), beide mit L-30-03-Guard vor GITHUB_ENV. Die Seed-Prüfung "scan_stats gefüllt" ist damit Teil der Strecke: ist die Tabelle leer, wird Zusicherung 15 rot mit dem Satz, dass der Seed eine Zählerzeile säen muss (die Tabelle existiert seit 1.0.0, der Crawl des Seeds füllt sie unter v1.5.0; kein Seed-Umbau nötig).
- "Store upgrade 5, the seventeen assurances after the upgrade", neue Abschnitte je mit eigenem `::error::`:
  - 14: `oc_migrations` trägt `Version001603Date20261108000000` genau einmal.
  - 15: Flag == 1 (pending) direkt nach occ upgrade, bei > 0 Zählerzeilen.
  - 16: Overview-Schleife mit `UPGRADE_DRAIN_BUDGET_SECONDS` (900 s); `legacyReason` darf am Ende nicht "missing" sein (POST /coverage hat geantwortet).
  - 17: `coverage.perDocument == true`, `counting == false`, `perDocumentHint == true`; danach ist das Flag ein Unix-Stempel > 1, >= UPGRADE_FINISHED_AT und <= jetzt; ein frischer Overview-Abruf nach dem Stempel zeigt den Hinweis weiterhin (D-43-12, 7 Tage).
  - 18: Container-Log trägt `doc key backfill, done=`; Python-Probe im Container (Spiegel von `_DOC_KEYS_MISSING_SQL`, read only): Spalte `doc_key` existiert in state.db und `missing == 0` (D-43-14).
- `grep -c '::error::'` in deploy-harp.yml: vorher 233, nachher 244 (+11: zehn in den Zusicherungen 14-18, einer im L-30-03-Guard von "Store upgrade 4").
- Tests: test_upgrade_seed_steps.py auf "seventeen" und Abschnitte 12-18; zwei neue Tests (Textverträge 14-18; Lesereihenfolge scan_rows < occ upgrade < hint in "Store upgrade 4" plus die zwei Env-Namen); test_cert_rotation_steps.py Zählermuster auf "seventeen".

## STOPP-Prüfung 1.6.3 (Delta v1.6.2..7964ee9e, Stand vor dem Bump)

- `git diff --name-only v1.6.2..HEAD -- php/lib/Migration` = genau `php/lib/Migration/Version001603Date20261108000000.php`. BESTANDEN.
- vectors.sql und index/schema.py: Diff leer. BESTANDEN.
- schema.sql: nur die Spalte `doc_key` und der Index `files_storage_doc_key`; einziger weiterer Diff-Rest ist das Komma-Paar `-    deleted_at    INTEGER` / `+    deleted_at    INTEGER,` (identische Zeile, nur das Satzzeichen, das die erlaubte Spalte syntaktisch anhängt; 43-16, D-43-14). SUBSTANZIELL BESTANDEN, Verify-grep im Plan präzisiert (s. Abweichungen).
- STORE_SCHEMA_MARK/SCHEMA_VERSION: kein `+`-Treffer. BESTANDEN.
- Neue `write_meta`-Schlüssel: genau `storage_sweep_at` (SWEEP_MARK), `doc_key_backfill_after` (DOC_KEY_MARK) und `refusal_streaks_1_6_3` (REFUSAL_RENEW_MARK); kein `set_meta`. Entspricht der STOPP-Regel 1.6.3 aus 43-02 in der von 43-20 fortgeschriebenen Fassung. BESTANDEN.

## Verifikation (lokal)

- Plan-verify Task 1: alle Teilprüfungen grün (Versionsstellen, Links, CHANGELOG-Kopf und Linkdefinition, UPGRADE_FROM_TAG, Migrationsmuster, STOPP-greps mit der Präzisierung, keine Em-Dashes, "no longer blocks a PHP worker", "### Known limitations").
- pytest gezielt: test_lockstep_versions + test_store_metadata + test_upgrade_seed_steps 256 passed; alle 18 Module, die deploy-harp.yml lesen: 1241 passed/8 skipped plus test_poller/test_store_repo 380 passed/1 skipped.
- Gates: ruff check, ruff format --check (254 Dateien), pyright latest 0 errors, vulture --min-confidence 80 grün (vor beiden Commits).
- deploy-harp.yml: YAML-Parse grün, `bash -n` der Run-Blöcke "Store upgrade 4" und "Store upgrade 5" grün, eingebettete Python-Probe kompiliert; Dateigröße 511964 Bytes unter dem 500-KB-Gate (test_workflow_size grün). actionlint lokal nicht installiert.
- Em-Dash-Audit mit Positivkontrolle und Umlaut-Audit der neuen deutschen Prosa (Entwurfsabschnitt): sauber; CHANGELOG-Abschnitt rein ASCII.

## Offen (Checkpoint beim Koordinator, Task 2 und 3)

- Owner-Freigabe für Push auf main und Dispatch "Coverage end to end" (Frage mit Commit-Liste und CHANGELOG [1.6.3] wörtlich); Zeilen in 43-FREIGABEN.md schreibt der Owner-Dialog.
- Nach Freigabe: `git pull --rebase`, Push, head_green.sh über die sieben Workflows, Zitate "installed_version went from 1.5.0 to 1.6.3" und die Zusicherungszeilen 14-18 aus HaRP deploy, `gh workflow run coverage-e2e.yml --ref main`, Lauf-ID als Nachtrag in 43-E2E.md.
- CI-abhängige Plan-verify-Teile (head_green, gh run view auf HaRP deploy) sind damit offen.

## Nachtrag des Koordinators (08.11.2026, nach Owner-Freigabe)

Owner-Freigabe "Ja, Push + 1 Dispatch" (20:13, in 43-FREIGABEN.md), CHANGELOG lag wörtlich vor. Push d9f8a65d auf main, alle acht gestarteten Push-Workflows grün, darunter:

- HaRP deploy, Lauf 42513966073 (27 min 54 s): Upgrade-Strecke grün, wörtlich im Log "installed_version went from 1.5.0 to 1.6.3"; Version001603Date20261108000000.php im ausgerollten Baum. Die Zusicherungen 14-18 melden sich nur im Fehlerfall (je eigenes ::error:: mit Abbruch); der grüne Job ist ihr Beleg, eine Erfolgszeile je Zusicherung gibt es konstruktionsbedingt nicht.
- PHP and store metadata gates, Lauf 42513966089: PHPUnit-Beleg für 43-19 (lokal war PHPUnit nicht lauffähig, Docker Desktop kam nicht hoch).

E2E-Dispatch 42516315101 auf d9f8a65d gestartet (genau einer, von der Freigabe gedeckt); Lauf-ID-Nachtrag in 43-E2E.md folgt mit der Auswertung.

## Deviations from Plan

1. **[Rule 3] STOPP-grep des Plans an die erlaubte Spalte angeglichen.** Die Teilprüfung `grep '^[+-][^+-]' | grep -v 'doc_key'` auf schema.sql ließ das Komma-Paar der Vorzeile `deleted_at` übrig, den syntaktischen Träger der von der STOPP-Regel (43-02, Fassung 43-20) ausdrücklich erlaubten Spalte `doc_key` (43-16). Verify-grep in 43-08-PLAN.md um `|deleted_at    INTEGER,? ` erweitert und den Prosa-Satz präzisiert (Präzedenz: 43-20 hat 43-08-PLAN.md ebenso an den Code-Bestand angeglichen). Kein inhaltlicher STOPP-Fall; beide Zeilen sind bis auf das Komma identisch.
2. **[Rule 3] deploy-harp.yml über der 500-KB-Grenze (lokal abgefangen, kein CI-Lauf verbraucht).** Die erste Fassung der Zusicherungen 14-18 hob die Datei auf 514224 Bytes (Gate 512000, Lehre aus 41-08). Kommentare und Fehlertexte gekürzt, die vier jq-Einzelabfragen zu einem jq-String zusammengefasst, Python-Probe kompakt: 511964 Bytes. WARNUNG für Folgepläne: nur noch 36 Bytes Luft; die nächste Änderung an deploy-harp.yml muss einen Block nach scripts/ci/ auslagern (Muster 41-08, test_workflow_size.MOVED_STEPS).
3. **[Rule 2] Fünfter Known-limitations-Satz ergänzt** (SMB ohne php-smbclient unter etwa 420 KB/s, Block von 8 MiB im 20-s-timeout, Abhilfe Erweiterung oder timeout-Option): 43-18-SUMMARY formuliert diese Grenze ausdrücklich als "Known limitations für 43-08"; der Plan nennt vier Sätze, die SUMMARY geht laut Plan vor ("weicht eine Grenze dort ab, gilt die SUMMARY"). Owner sieht den Wortlaut ohnehin im CHANGELOG-Checkpoint.
4. **Klein:** Der Umbruch-Fix des CHANGELOG-Satzes "no longer blocks a PHP worker" (verify greppt die Phrase einzeilig) landete im ci-Commit dd79d073 statt im chore-Commit (aufgefallen erst beim Plan-verify nach Commit 1).
5. **Bewusst nicht ausgeführt (Auftrag des Koordinators):** Push, Dispatch, head_green, 43-E2E-Nachtrag, FREIGABEN-Zeilen; Task 2 ist ein blocking Checkpoint.

## Known Stubs

Keine. Der Store-Listing-Abschnitt ist ausdrücklich als Entwurf gekennzeichnet (Owner-Runde 43-12/43-13), das ist der geplante Weg, kein Stub.

## Threat Flags

Keine neue Angriffsfläche: keine neue Route, kein neuer Schlüssel; die neuen CI-Proben lesen nur (SC4 bestätigt durch test_the_assurance_step_does_nothing_an_admin_would_do). T-43-24 (STOPP-Prüfung bestanden), T-43-25 (Zusicherung 14 prüft die Migration ab v1.5.0), T-43-26 (test_lockstep_versions grün, beide Apps 1.6.3) umgesetzt; T-43-25/14-18 sind erst mit dem grünen CI-Lauf nach dem Push voll belegt.

## Self-Check: PASSED

- Commits 844d5e8c und dd79d073 vorhanden, Autor street1983nk <k.cherif@outlook.de>, ohne Trailer.
- Geänderte Dateien vorhanden; `<version>1.6.3</version>` zweimal, `<image-tag>1.6.3</image-tag>` einmal, `## [1.6.3] - 2026-11-08` und Linkdefinition im CHANGELOG, "# Entwurf v1.6.3, Stand Plan 43-08" im Listing, "seventeen assurances" und Abschnitte 14-18 im Workflow.
