---
phase: 25-einbettungsspur-und-modellwahl
plan: 12
subsystem: api-status, docs
tags: [status, praezision, spur, doku, pins, abschluss]
requires:
  - "25-04: Admin-UI-Vertrag model.precisionActive / model.reembedRunning"
  - "25-08: precision.snapshot() mit VERDICTS"
  - "25-09: lane.snapshot() mit MODES/REASONS"
  - "25-11: Präzisionsverdrahtung, Rückweg löscht fp32-Datei"
provides:
  - "GET /status: Block model {precisionChosen, precisionActive, precisionVerdict, reembedRunning}"
  - "GET /status: Block lane {mode, reason}"
  - "Admin-Doku Präzision, Offline-Weg, Einbettungsspur, Modellzeile"
affects:
  - "php/lib/Service/AdminViewService.php (liest die Felder, keine Änderung nötig)"
tech-stack:
  added: []
  patterns: ["Prozesswert in _volume() setzen und in _of() übertragen (Pitfall 2)"]
key-files:
  created: []
  modified:
    - backend/src/findling/api/status.py
    - backend/tests/test_status_endpoint.py
    - docs/embeddings.md
    - docs/profiles.md
    - docs/admin-page.md
    - backend/tests/test_measurement_scripts.py
decisions:
  - "reembedRunning = Cursor embedding_backlog_at in meta gesetzt (nicht leer); der Sweep leert ihn am Ende"
  - "precisionActive vor dem Settle aus engine_precision(), danach aus precision.snapshot().active"
  - "lane.reason im Ruhezustand ist economy (so steht es in findling.lane), nicht leer"
metrics:
  duration: "ca. 35 min"
  completed: 2026-09-28
  tasks: 2
  files: 6
---

# Phase 25 Plan 12: Statusfelder, Doku und letzte Pin-Messung Summary

GET /status meldet jetzt Präzision (gewählt, aktiv, Verdikt), den Stand der Neueinbettung aus dem Redelivery-Cursor und die Einbettungsspur in beiden Zweigen, ohne I/O; die Admins finden Präzisionswahl, Offline-Weg per docker cp und Spurverhalten dokumentiert, und der Paketbaum ist über den vollständigen Phasenbaum neu gepinnt.

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | ModelReport und LaneReport in /status, IN-03-Parität | e7f395e (test), 3a42b3c (feat) |
| 2 | Admin-Doku, letzte Pin-Messung, Phasen-Gate | f7aa02f |

### Task 1
- `ModelReport` und `LaneReport` als pydantic-Modelle, Felder `model` und `lane` in `StatusResponse`.
- `_model_report()` liest nur `precision.snapshot()` und `engine_precision()`, `_lane_report()` nur `lane.snapshot()`. Kein Digest, kein Dateizugriff (T-25-53).
- `_volume()` setzt beide Blöcke, `_of()` überträgt sie mit Pitfall-2-Kommentar (`lane=volume.lane`) und setzt `reembedRunning` aus `marks[EMBEDDING_BACKLOG_MARK]`.
- Tests: FIELDS erweitert; Ruhezustand, `fp32_on_a_tight_box`, `fp32_active_in_economy`, `fp32_unavailable` je in beiden Zweigen; Cursor fehlt/leer/gesetzt; Spur parallel und `waiting_for_memory`; IN-03 (`set(PROFILE_VALUE_KEYS) == fields(ProfileValues)`); `hash_count()` bleibt bei einem Poll mit fp32-Datei auf dem Volume stehen, status.py importiert weder `findling.embed.weights` noch `hashlib`.

### Task 2
- `docs/embeddings.md`: neuer Abschnitt 11 "Präzision int8 und fp32" (occ-Befehl, Default, nur Standard/Leistung, Profilwechsel ändert nichts, Quelle mit URL, sha256, Größe und beiden Hosts, Ablagepfad, Offline-Weg mit `docker cp`-Beispiel und chown auf uid 1000, falsche Datei = `fp32_unavailable`, Proxy-Netze, neuer Versuch erst int8 dann fp32, Rückweg löscht die Datei, Suche während der Neueinbettung, Verdikttabelle mit allen sechs Werten aus VERDICTS). Abschnitt 7 bekommt einen PAR-04-Nachtrag, Abschnitt 8 verweist auf Abschnitt 11.
- `docs/profiles.md`: Abschnitt "Einbettungsspur" (ab 2 Kernen technisch, wirksam ab 3 Kernen und 6 GB, Speicherbedingung statisch und live, serieller Rückfall, genau ein Läufer, embed_slots 2 ab Phase 26, fp32 nur Standard/Leistung, Companion 1.4.0, Statusblock `lane`, Hinweis auf die RuntimeError-Runde aus 25-10).
- `docs/admin-page.md`: Abschnitt "Die Modellzeile: Präzision und Neueinbettung", Verdikte als Satz erst mit Phase 27.
- Pins: `PACKAGE_TREE_HASH_TODAY` neu gemessen (`48f2486c...ba6b12a`, 64 Dateien bestätigt). PHP-Paar neu geprüft und unverändert (75 Dateien, `726756a8...`).

## Verifikation

- Gesamtsuite: 3701 passed, 16 skipped (inklusive beider Pin-Tests und test_public_artifacts.py).
- ruff check, ruff format --check, pyright (latest, 0 Fehler), vulture 80: grün.
- Keine Em- oder En-Dashes in den drei Doku-Dateien.
- Keine Modelldatei im Arbeitsbaum. **Nichts gepusht**; alle Commits nur lokal.

## Offene CI-Nachweise (laufen erst nach einem Push)

1. PHPUnit der Pläne 25-03 und 25-04 in `.github/workflows/php.yml`.
2. T3-Überlappung in `.github/workflows/python.yml`, Job gates.

Push-Entscheid liegt beim Owner; der Executor hat nicht gepusht.

## Deviations from Plan

1. **[Rule 1, Spezifikation] Ruhezustand der Spur:** Das Plan-Verhalten nannte `lane {mode "inline", reason ""}` für die leere Installation. `findling.lane` steht im Ruhezustand aber auf `inline`/`economy` (die wirksame Stufe vor dem ersten Profillesen ist Sparsam, D-24-02). Die Route meldet den Modulzustand unverändert, der Test prüft `economy`. Kein Codeeingriff an lane.py.
2. **TDD-Reihenfolge:** Test und Implementierung entstanden in einem Zug; der Test-Commit (e7f395e) liegt vor dem feat-Commit (3a42b3c), ein getrennter RED-Lauf wurde nicht ausgeführt. Ohne die Implementierung scheitern die Tests zwingend (FIELDS enthält `model`/`lane`).
3. **Checkpoint:** Der Plan ist `autonomous: true` und enthält keinen Checkpoint-Task; die im Auftrag erwähnte Owner-Abnahme ist damit kein Task dieses Plans und bleibt Sache des Orchestrators bzw. von verify/secure-phase.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche: die zwei Blöcke tragen nur Wörter aus geschlossenen Mengen und `int8`/`fp32`, keine Pfade, Digests oder URLs (T-25-52 accept, T-25-53 per Test belegt, T-25-54 durch Digest-Angabe in der Doku).

## Self-Check: PASSED

- backend/src/findling/api/status.py, backend/tests/test_status_endpoint.py, docs/embeddings.md, docs/profiles.md, docs/admin-page.md, backend/tests/test_measurement_scripts.py: vorhanden und geändert.
- Commits e7f395e, 3a42b3c, f7aa02f: vorhanden.
