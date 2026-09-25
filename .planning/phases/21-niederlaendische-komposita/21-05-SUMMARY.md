---
phase: 21-niederlaendische-komposita
plan: 05
subsystem: store/repo, index/open, tests
tags: [komposita, nl, version-mark, d-06, komp-01]
requires: ["21-01", "21-03", "21-04"]
provides:
  - open.DUTCH_MARK ("wordlist_hash_nl"), expected_versions(..., *, dutch_mark="off") als letzter Schlüssel
  - DUTCH_MARK in _MARKS_OF_A_DIRECTORY, geschrieben von stamp_a_new_directory
  - repo._DUTCH_MARK, repo._DUTCH_LIST_OFF, repo._dutch_list_is_legacy, Saat-Ausnahme
  - conftest.write_wordlist_nl(root) -> str
affects: [21-06, 21-07]
tech-stack:
  added: []
  patterns: [Marke wie die Sprachmarke, benannte Legacy-Regel fällt geschlossen, Literal statt Import im Store]
key-files:
  created: []
  modified:
    - backend/src/findling/index/open.py
    - backend/src/findling/store/repo.py
    - backend/tests/conftest.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_index_open.py
    - backend/tests/test_upgrade_compatibility.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Legacy-Regel: nur fehlende Marke gegen erwartet off ist keine Abweichung; geschriebenes off, leerer Wert und fehlende Marke gegen echte Liste werden verglichen"
  - "Begründung im Code als 'kein Build vor Phase 21 hat body_nl mit Liste gesplittet' statt 'bis 1.3', weil 1.3 noch nicht veröffentlicht ist"
  - "Befund 21-01 (stamp_after_rebuild leert REBUILD_MARK trotz verbleibender Drift) nicht gefixt, im Docstring von stamp_after_rebuild benannt; die nl-Marke erbt ihn, Antwort ist der Band-Umbau in 21-06"
metrics:
  duration: ca. 35 min
  completed: 2026-09-25
  tasks: 2 von 2
---

# Phase 21 Plan 05: Siebte Marke wordlist_hash_nl Summary

Die siebte Versionsmarke `wordlist_hash_nl` existiert jetzt im Store und im Index-Tier, reist wie die Sprachmarke (nie gesät, nur hinter Verzeichnisneubau geschrieben, Fehlen bei `off` ist Altbestand) und ist per Zustandstabelle und Upgrade-Gold festgeschrieben; alle src-Aufrufer laufen noch über den Default `off`, `ANALYZER_VERSION` bleibt 1.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 RED | Zustandstabelle als fehlschlagende Tests | 3d0994c | test_store_repo.py, test_index_open.py, conftest.py |
| 1 GREEN | Marke im Store und Index-Tier, Baumhash | 0095647 | open.py, repo.py, test_measurement_scripts.py |
| 2 | Upgrade-Gold, Upgrade-Test | 9efbd0d | test_upgrade_compatibility.py, test_measurement_scripts.py (nur Kommentar-Schreibweise) |

## Umsetzung

- `open.py`: `DUTCH_MARK` mit Begründungsblock unter `LANGUAGES_MARK`; `expected_versions(digest, languages, *, dutch_mark=DUTCH_LIST_OFF)`, Marke als letzter Schlüssel, Docstring nennt `wordlist_nl.dutch_mark(settings().languages)` und das Gate aus 21-06; `_MARKS_OF_A_DIRECTORY` mit vier Einträgen; `stamp_a_new_directory` schreibt die Marke; Docstring von `stamp_after_rebuild` auf vier ausgelassene Marken plus Hinweis auf den 21-01-Befund.
- `repo.py`: Literale `_DUTCH_MARK`, `_DUTCH_LIST_OFF`; `_DEFAULT_META` ohne die Marke (Kommentar nennt die zweite Ausnahme); `_dutch_list_is_legacy`; Zeile in `version_mismatch` neben den bestehenden Ausnahmen; `seed.pop(_DUTCH_MARK, None)`.
- Baumhash neu `32e5cc31bbd8...0e7354746`, `PACKAGE_FILES_TODAY` bleibt 57, datierter Kommentar "Plan 21-05".
- Upgrade-Gold: `GOLD_V1_3[DUTCH_MARK] = "off"` (Literal), `ALL_MARKS` mit siebtem Eintrag und Ausnahme-Kommentar; Docstring von `test_no_mark_appeared_and_none_went_missing` behauptet die Regel weiter ("ein neuer Marker ohne benannte Legacy-Regel ist ein Umbau für alle, eine achte schlägt hier fehl") und nennt genau zwei Ausnahmen.
- `test_an_upgrade_without_dutch_moves_no_seventh_mark` prüft gegen den echten Store: 1.2.x-Datenbank (Schema 1, keine Sprach- und keine nl-Marke) gegen off ergibt `[]`, gegen `1:d` ergibt `[wordlist_hash_nl]`.

## Pitfall-1-Bestätigung

Kein Test setzt die Marke auf den erwarteten Wert und prüft danach "keine Abweichung", außer `test_an_unchanged_dutch_list_is_no_drift`. `test_a_new_directory_is_stamped_with_the_dutch_mark` prüft Stille erst, nachdem `stamp_a_new_directory` (der einzige legitime Schreiber) die Marke geschrieben hat; die Saat ist vorher als leer zugesichert.

## Verifikation

- test_store_repo + test_index_open: 141 passed
- test_upgrade_compatibility: 14 passed
- Volle Suite: 2957 passed, 15 skipped
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün
- grep-Kriterien: zehn Testnamen je 1, `seed.pop(_DUTCH_MARK, None)` 1, `_dutch_list_is_legacy(current, value)` 1, `_DEFAULT_META` ohne Marke 0, `ANALYZER_VERSION = 1` 1, "Plan 21-05" 1
- Kein Test scheiterte an einem fehlenden nl-Artefakt (alle src-Aufrufer nehmen den Default off)

## Deviations from Plan

**1. Zwischencommit 0095647 war in einem Test rot.** `test_no_mark_appeared_and_none_went_missing` bricht, sobald die Marke in `expected_versions` steht; das Gold gehört laut Plan zu Task 2, deshalb war die Suite zwischen 0095647 und 9efbd0d in genau diesem Test rot. Ab 9efbd0d ist alles grün.

**2. Veralteter Verweis korrigiert.** Der Docstring von `test_no_mark_appeared_and_none_went_missing` verwies für den Beweis der sechsten Marke auf `test_store_metadata.py`; die Fälle stehen in `test_store_repo.py`. Beim Umschreiben korrigiert.

**3. Kommentar-Schreibweise "Plan 21-05"** im Baumhash-Block großgeschrieben (Akzeptanz-grep ist case-sensitiv), abweichend von den kleingeschriebenen Vorgängereinträgen.

**4. `write_wordlist_nl` ist noch ohne Aufrufer** (für 21-06 vorbereitet, wie im Plan vorgesehen); vulture bei 80 meldet nichts.

## Offener Befund (geerbt, nicht gefixt)

`stamp_after_rebuild` leert `REBUILD_MARK`, obwohl eine übersprungene Verzeichnismarke weiter driftet (Befund aus 21-01). `test_the_stamp_after_rebuild_leaves_the_dutch_mark_alone` zeigt es auch für die nl-Marke: Rückgabe True, Marke fehlt, `version_mismatch` nennt sie weiterhin. Unter dem fullreindex-Ausweg hebt der nächste Start die Generation also erneut. Antwort ist der Band-Umbau mit Stempel hinter dem Tausch in 21-06.

## Threat Flags

Keine neue Oberfläche. T-21-05-01 (Saat-Test in beide Richtungen), T-21-05-02 (nur stamp_a_new_directory schreibt, stamp_after_rebuild überspringt, zwei Tests), T-21-05-03 (vier Fälle von `_dutch_list_is_legacy`), T-21-05-04 (Docstring behauptet die Regel weiter, neuer Upgrade-Test) mitigiert.

## Self-Check: PASSED

- FOUND: alle sieben geänderten Dateien
- FOUND: Commits 3d0994c, 0095647, 9efbd0d
