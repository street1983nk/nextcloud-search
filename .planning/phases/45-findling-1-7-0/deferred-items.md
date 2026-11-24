# Deferred items Phase 45

## 45-21: Reihenfolge-Abhängigkeit im Test (erledigt in 45-21)

- Gefunden: 2026-11-24, beim Lauf der vollen pytest-Suite in zehn Teilen (Speichermangel, Vorgabe des Koordinators).
- `tests/test_phase31_audit.py::test_a_mail_with_999_ordinary_attachments_stays_whole` wurde rot (`Reason.TRUNCATED`), wenn `tests/test_legacy_doc.py` im selben Prozess vorher lief: `test_reading_stops_at_the_character_cap` setzt `FINDLING_MAX_TEXT_CHARS=1024` per monkeypatch, `findling.config.settings()` ist mit `@lru_cache(maxsize=1)` (config.py Z. 1632) gepuffert und behielt den Wert nach dem Rückbau der Umgebung.
- Beleg vorher: `pytest tests/test_legacy_doc.py <mail-test>` -> `1 failed, 78 passed`; der Mail-Test allein grün.
- Status: erledigt in 45-21 (Koordinator: nicht verschieben). autouse-Fixture `forget_the_settings` in `backend/tests/conftest.py` leert den Cache nach jedem Test; nachher `79 passed`. Commit siehe 45-21-SUMMARY.
