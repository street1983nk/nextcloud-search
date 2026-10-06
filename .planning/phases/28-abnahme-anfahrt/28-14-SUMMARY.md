---
phase: 28-abnahme-anfahrt
plan: 14
subsystem: phasenabschluss
tags: [abnahme-anfahrt, push, ci, owner-abnahme, mess-10]
status: "complete"
requires:
  - phase: 28-12
    provides: OCR_SLOT_COST_BYTES 250 MiB (SC4)
  - phase: 28-13
    provides: Abbau des Korpus-Snapshots, null laufende Kosten
provides:
  - "Push-Signal C7 wörtlich, CI-Tabelle mit Lauf-IDs und Rerun-Geschichte"
  - "Zuordnung SC1 bis SC4 und D-28-01 bis D-28-14 mit Belegen"
affects: [29]
tech-stack:
  added: []
  patterns: ["CI-Belege je Attempt über die Actions-API (runs/<id>/attempts/<n>, check-runs/<job>/annotations)"]
key-files:
  created:
    - .planning/phases/28-abnahme-anfahrt/28-14-SUMMARY.md
  modified: []
decisions:
  - "C7 (05.10.2026): Owner 'Pushen wie es ist' = push-now"
  - "Runner-Ausfälle auf aae091bd per rerun --failed nachgefahren, kein Fix-Commit, kein weiterer Push nötig"
metrics:
  duration: "Tasks 1 und 2 in der Orchestrator-Session, Dokumentation ca. 30 min"
  completed: "offen (Task 3)"
requirements: [MESS-10]
---

# Phase 28 Plan 14: Push, CI-Belege und Owner-Abnahme Summary

**Status: complete.** Push nach Owner-Wort in zwei Schüben, alle ausgelösten Workflows auf dem Endstand aae091bd grün (drei davon erst nach Rerun wegen eines GitHub-Runner-Ausfalls), lokale Gates grün, SC1 bis SC4 und D-28-01 bis D-28-14 mit Belegen zugeordnet; die Abnahme (Task 3) liegt beim Owner.

## Task 1: Push-Entscheid (C7)

Owner-Signal am 05.10.2026 per Auswahlfrage, wörtlich:

> Pushen wie es ist

Das entspricht der Option `push-now`. Die Begründung des Owners folgte der Vorlage: Die Box-Adressen in der Historie zeigen auf abgebaute, an AWS zurückgegebene Adressen (Abbau 28-10, `rohdaten/08-abbau-boxen.txt`; null Adressen über 17 Regionen, `rohdaten/09-abbau-snapshot.txt`).

Vollzug:

| Schub | Bereich | Zeit (UTC) |
|---|---|---|
| 1 | `18602c48..ab634401` | 19:08 |
| 2 | `ab634401..42e07168` | 19:27 |
| danach | Dependabot PR #24 auf GitHub per Squash gemergt (`aae091bd`), lokal per fast-forward nachgezogen | 19:27 |

Stand beim Schreiben: `origin/main` = `aae091bd`. Lokal liegt genau ein Commit darüber (`4d468329`, Tag-Nachlesung aus 28-13) plus dieses SUMMARY; beide werden nach Owner-Wort gemeinsam gepusht. Kein Release, kein Tag.

## Task 2: CI-Belege

### Welle 1 auf ab634401 (createdAt 2026-10-05T19:08:56Z)

| Workflow | Lauf-ID | Attempt | Ergebnis |
|---|---|---:|---|
| Python gates | 37361295250 | 1 | success |
| Integration | 37361295550 | 1 | success |
| Resilience | 37361295651 | 1 | success |
| Multi-arch image | 37361295788 | 1 | success |
| HaRP deploy | 37361295730 | 1 | success |

### Welle auf 42e07168 (createdAt 19:27:05Z)

Von der Folgewelle auf aae091bd per Concurrency abgebrochen: Python gates 37363465249, Integration 37363465235, Resilience 37363465266, HaRP deploy 37363465269 je `cancelled`; Multi-arch image 37363465430 `success`. Der Baum von 42e07168 ist in aae091bd enthalten (aae091bd ändert nur die Dependabot-Pins), die Belege der Endwelle gelten damit auch für ihn.

### Endwelle auf aae091bd (Dependabot-Merge, createdAt 19:27:24Z)

| Workflow | Lauf-ID | Attempt 1 | Attempt 2 | Attempt 3 | Endstand |
|---|---|---|---|---|---|
| Python gates | 37363501540 | success | | | **success** |
| Resilience | 37363501552 | success | | | **success** |
| Integration | 37363501570 | failure (19:43:48Z) | success (20:00:12Z) | | **success** |
| Multi-arch image | 37363501553 | failure (19:47:04Z) | failure (20:06:06Z) | success (21:05:44Z) | **success** |
| HaRP deploy | 37363501458 | failure (19:49:13Z) | failure (20:06:08Z) | success (21:16:23Z) | **success** |

Ursache der Fehlversuche: kein Testfehler, sondern ein GitHub-Vorfall (Actions zuerst `degraded_performance`, später `major_outage`, githubstatus.com). Die Jobs wurden nie von einem Runner angenommen; Annotation wörtlich in Integration Attempt 1 (Job readonly-gate, 111943756960), Multi-arch Attempt 1 (Manifest-Merge, 111944868554) und HaRP Attempt 2 (stable34 amd64, 111951352645): "The job was not acquired by Runner of type hosted even after multiple attempts". Nachgefahren per `gh run rerun --failed`, ohne Code-Änderung und ohne weiteren Push. Abweichend vom Orchestrator-Stand ("alle drei zweimal gescheitert") zeigt die Attempt-API: Integration scheiterte einmal und wurde beim ersten Rerun grün, Multi-arch und HaRP scheiterten zweimal und wurden beim zweiten Rerun grün.

### PHP and store metadata gates

Lief auf **keinem** der drei Commits: Der Workflow ist pfadgetriggert, und `php/` ist seit dem letzten Lauf unverändert (`git diff --stat 18602c48 aae091bd -- php` leer). Letzter Lauf: **37176289202** auf 18602c48 (2026-10-04T04:11:41Z, push), `success`. Ein Lauf auf dem Phasenstand selbst fehlt also; der Beleg ist "PHP-Baum identisch mit dem zuletzt grün geprüften". Der PHP-Baumhash-Pin in `backend/tests/test_measurement_scripts.py` ist unverändert (28-12).

### Lokale Gates (Plan-Verify Task 2, im Worktree auf 4d468329, Baum mit Dependabot-Pins)

| Gate | Ergebnis |
|---|---|
| `uv run pytest -q` | **4436 passed, 25 skipped**, 1 warning, 524,79 s, Rückgabe 0 |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 186 files already formatted |
| `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | keine Ausgabe (grün) |

Die eine Warnung ist eine `StarletteDeprecationWarning` aus `fastapi/testclient.py` ("Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead"), vermutlich mit den neuen Dependabot-Pins gekommen; kein Testfehler, Kandidat für Phase 29.

## Task 3: Zuordnung SC und D-28 (Stand vor der Abnahme)

Abkürzung: `M/` = `docs/measurements/2026-10-abnahme-anfahrt/`.

### Success Criteria

| SC | Inhalt | Status | Beleg |
|---|---|---|---|
| SC1 | Rechenblatt und Deckel vor Boxstart datiert freigegeben, Anfahrt unter dem Deckel | grün | Freigabezeile `M/rohdaten/02-rechenblatt-freigabe.txt` Z. 122 ("Anfahrt freigegeben: 2026-09-30, Deckel 119,82 h / 59,43 USD"), Commit cb49fa70 um 16:49:42Z; erster Startstempel `M/rohdaten/90-kosten.txt` Z. 5 (m7g.large, LaunchTime 16:53:40Z), also 4 min nach der Freigabe. Schlusskosten 34,64 USD gegen 59,43 USD, Sicherheitsstopp 71,32 USD nie erreicht (`M/README.md` Abschnitt 15, 28-13) |
| SC2 | RAM-Spitze und Durchsatz je Profil auf Referenz- und Mehrkern-Box in docs/performance.md, Rohdaten committet, Sparsam gleich Store-Zahl | grün, mit drei Hinweisen | `docs/performance.md` Z. 4864 "Abnahme-Anfahrt v1.4 (Phase 28)"; Tabellen `M/README.md` Abschnitte 4 und 5; Store-Marke C1 = 743,9 MB gegen 730,2 MB, +1,88 % im Band ±2 % (`M/rohdaten/m7g.large/94c/94c-bewertung.txt`, D-28-10). Hinweise: (a) 18 statt 21 Zellen, Zellen 3, 4, 10 vom Owner am 03.10. gestrichen (Quick 261003-d3y), Standard und Leistung damit nur auf Mehrkern-Boxen, auf der Referenzbox nur Sparsam; (b) gemessen auf drei Abbild-Ständen c87a0239, f73566c1, 18602c48 statt durchgehend c87a0239 (`M/README.md` Abschnitt 2, Baumhash je Zelle); (c) Vollzelle 52.137 statt 52.111 Dateien (Korpus-Stand) |
| SC3 | Runbook-Disziplin: Cron-Gate, Digest-Wechsel, Abbau | grün, mit zwei Restpunkten | Cron-Gate `M/rohdaten/03-aufbau-arm.txt` Z. 266 bis 269 und `M/rohdaten/06-aufbau-x86.txt` Z. 248 bis 251; Digest-Wechsel `92d-wechsel.txt`, `05-typwechsel-arm.txt`, `06-aufbau-x86.txt`, je Zelle `abbild-digest` in `10-zelle.txt`; Baumhash je Zelle `40b-baumhash.txt`; Abbau `M/rohdaten/08-abbau-boxen.txt` (28-10, Schlusszahlen nach Runbook 2.6 in `90-kosten.txt`, Timer nicht ausgelöst) und `M/rohdaten/09-abbau-snapshot.txt` (28-13, InvalidSnapshot.NotFound, 17 Regionen 0/0/0/0/0/0). Restpunkte: (a) Cron-Gate je Instanz, nicht je Typwechsel (`M/README.md` Abschnitt 13); (b) `scripts/ops/aws_box.sh cmd_destroy` nimmt das gemeinsame Schlüsselpaar noch nicht in die `shared`-Liste des Tag-Sweeps auf (28-10 Deferred Issues), Werkzeugfix offen |
| SC4 | Slot-Kosten fließen zurück, nicht getragene Stufe korrigiert oder nicht angeboten, Owner-Entscheid dokumentiert | grün für Formel und Entscheide, human_needed für Feldbeleg und Laufzeit | Owner-Entscheid wörtlich `M/README.md` Abschnitt 14 (alle sechs Fälle "nachziehen", Wert 250 MiB, Store kein Fall); `backend/src/findling/config.py` Z. 896 `OCR_SLOT_COST_BYTES = 250 * MIB`, Z. 933 und 945 Reserven folgen (28-12, 2f26d9fb, RED 66bf7a44); Vollindex-Term Z. 910 `MAIN_PROCESS_PER_FILE_BYTES = 6 * 1024` (Quick 261005-vit, e3d28dfd, RED 655cd037), S-voll damit rechnerisch getragen (0,987); CI auf Linux grün (Python gates 37361295250 und 37363501540). Offen: (a) alle Korrekturen sind nur rechnerisch und per Test belegt, kein Feldlauf mit 250 MiB; Zelle 11 liegt genau an der Grenze 1,100; (b) Vollindex-Term ohne Laufzeit-Verdrahtung (`index_files` Standard 0, `note_index_files` braucht Owner-Entscheid), `12-slotkosten.py rechnung` kennt den Term nicht; (c) Fall-2-Fix des Embed-Debugs (a0ac5aee, Band 500 auf 200 unter MAX_LIST_LENGTH 256) nur per Test belegt, Feldlauf steht aus (`.planning/debug/embed-handover-lock-timeout.md` Z. 38); Fall 1 per Owner-Entscheid A vertagt |

### Entscheide D-28-01 bis D-28-14

| D | Kern | Status | Beleg |
|---|---|---|---|
| D-28-01 | Deckel aus Rechenblatt plus 30 %, vor Boxstart datiert freigegeben | grün | `M/rohdaten/02-rechenblatt-freigabe.txt` Abschnitt 5, Z. 122; 28-05 (Owner-Signal wörtlich), cb49fa70 vor LaunchTime |
| D-28-02 | Beim Deckel: Zelle zu Ende, keine neue, Box bleibt stehen | grün (gebaut, nicht ausgelöst) | Deckel-Prüfung vor jeder Zelle `M/skripte/00-kette.sh` Z. 2 und 22 (28-02); Deckel nie erreicht, 34,64 von 59,43 USD (`M/README.md` Abschnitte 12, 15) |
| D-28-03 | Referenzbox m7g.large, `mem=4G`, Sparsam gleich Store-Zahl | grün | `M/README.md` Abschnitt 1 (Grenze 2g) und Abschnitt 7 (C1 743,9 MB im Band); 28-06 |
| D-28-04 | x86 c7a.xlarge bis c7a.8xlarge plus ARM m7g.4xlarge | grün | `M/README.md` Abschnitt 1, `M/rohdaten/05-typwechsel-arm.txt`, `07-typwechsel-x86.txt` (nproc, free -h, Architektur zurückgelesen); 28-07, 28-08, 28-09 |
| D-28-05 | Auf jeder Box alle drei Profile, Probe über die Produktroute, Gegenprobe | grün mit Owner-Abweichung | Probe über die Route in elf Zellen, alle `fits`, `erzwungen nein`, alle Verdikte stimmen (`M/README.md` Abschnitt 6); Abweichung: Zellen 3, 4, 10 vom Owner gestrichen (03.10., Quick 261003-d3y, Abbruch-Rohdaten `M/rohdaten/m7g.large/St-T-abbruch69-lauf6/`) |
| D-28-06 | Festes OCR-lastiges Teilkorpus je Zelle, Vollkorpus nur S-voll auf m7g.large | grün | `M/README.md` Abschnitt 3 (Listen-Prüfsumme f6b3dd70..., auf x86 gleich, Zähltor je Zelle 5.000), Abschnitt 7 (S-voll 52.137 Dateien) |
| D-28-07 | fp32 auf einer knappen und einer großzügigen Box, live geladen | grün | Zellen 11 (c7a.xlarge) und 18 (c7a.4xlarge), 470.268.510 Byte aus dem eigenen Release ohne Digest-Warnung, Rückkehr auf int8 (`M/README.md` Abschnitt 9, `99-rueckkehr-int8.txt`) |
| D-28-08 | Gemessene Slot-Kosten ersetzen Schätzwerte, Toleranz +10 %, Owner je Fall | grün | `M/README.md` Abschnitte 8, 11, 14; `backend/src/findling/config.py` Z. 896 (28-12); Feldbeleg offen wie SC4 (a) |
| D-28-09 | Teilkorpus Variante A, Deckel rund 59 USD | grün | `M/README.md` Abschnitt 3 (2.000 OCR-Dateien, 2.691 Seiten), Freigabe 59,43 USD (28-05) |
| D-28-10 | Toleranz ±2 % um 730,2 MB | grün | C1 = 743,9 MB, +1,88 %, Band 715,6 bis 744,8 MB (`M/rohdaten/m7g.large/94c/94c-bewertung.txt`, `M/README.md` Abschnitt 7); `RESIDENT_FIGURE` 730.2 unverändert |
| D-28-11 | Anker-Zelle Sparsam Teilkorpus auf m7g.large | grün | Zelle 2, 1.512,0 MiB, getragen (`M/README.md` Abschnitte 1, 4); 28-07 |
| D-28-12 | Keine harte Grenze auf Matrix-Boxen, Referenz `mem=4G` | grün | `memory.max max` je Matrix-Zelle (`M/README.md` Abschnitt 13), Referenz `mem=4G` Grenze 2g (Abschnitt 1) |
| D-28-13 | Boxen sofort nach der letzten Zelle ab, Snapshot erst nach SC4-Entscheiden | grün | `M/rohdaten/08-abbau-boxen.txt` (28-10, 05.10.), Snapshot nach Owner-Signal "Loeschen" am 05.10. 19:10:41Z (`M/rohdaten/09-abbau-snapshot.txt`, 28-13), SC4-Entscheide vorher (`M/README.md` Abschnitt 14) |
| D-28-14 | Sicherheitstimer stoppt bei Deckel plus 20 % | grün (gebaut, nicht ausgelöst) | `M/skripte/00-kette.sh` Z. 15 bis 16 (`shutdown -h +<min>`, 1,20 x DECKEL_USD); 71,32 USD in der Freigabe Z. 123; nie ausgelöst (`M/rohdaten/08-abbau-boxen.txt` Z. 60) |

## Deviations from Plan

- **Tasks 1 und 2 in der Orchestrator-Session vollzogen,** dieses SUMMARY dokumentiert sie nachträglich; Lauf-IDs und Attempt-Verlauf wurden per `gh run list` und Actions-API neu gelesen, nicht übernommen.
- **Push in zwei Schüben plus Dependabot-Merge** statt eines einzelnen `git push`; die Workflows sind deshalb auf drei Commits belegt, der Endstand ist aae091bd.
- **Reruns ohne erneutes Owner-Wort:** Der Plan verlangt erneutes Owner-Wort nur für Fix-Commits und weitere Pushes; ein `rerun --failed` ohne Code-Änderung ist keins von beidem.
- **PHP and store metadata gates** lief auf dem Phasenstand nicht (Pfadfilter), Beleg über den unveränderten PHP-Baum, siehe oben.

## Known Stubs

Keine.

## Offen für den Owner (Task 3)

Abnahme-Signal "approved" oder Befunde. Bis dahin ist die Phase nicht abgeschlossen; STATE.md und ROADMAP.md sind bewusst nicht fortgeschrieben.

## Self-Check: PASSED

- Lauf-IDs und Attempts per `gh run list` und `actions/runs/<id>/attempts/<n>` gelesen, alle fünf Endstände auf aae091bd `success`
- Belegdateien vorhanden: `M/rohdaten/02-rechenblatt-freigabe.txt`, `90-kosten.txt`, `03-aufbau-arm.txt`, `06-aufbau-x86.txt`, `08-abbau-boxen.txt`, `09-abbau-snapshot.txt`, `docs/performance.md` Z. 4864, `config.py` Z. 896/910/933/945
- Commits vorhanden: cb49fa70, 66bf7a44, 2f26d9fb, 655cd037, e3d28dfd, a0ac5aee, ab634401, 42e07168, aae091bd, 4d468329


## Owner-Abnahme (Task 3)

Signal vom 06.10.2026 kurz nach Mitternacht per Auswahlfrage, woertlich: "approved".
Die Vorlage nannte die fuenf Pruefpunkte, die Abweichungen (18 statt 21 Zellen, drei
Abbild-Staende, Cron-Gate je Instanz) und die ehrlich offenen Punkte (250 MiB ohne
Feldlauf, Vollindex-Term ohne Laufzeit-Verdrahtung, Fall-2-Fix nur per Test belegt,
aws_box.sh-Schluesselpaar-Liste, StarletteDeprecationWarning); alle offenen Punkte
sind als Phase-29-Kandidaten notiert. Phase 28 ist damit abgenommen.
