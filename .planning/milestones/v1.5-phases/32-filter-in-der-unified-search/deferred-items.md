# Phase 32: zurückgestellte Befunde außerhalb des Plan-Umfangs

## Plan 32-01

- **Flake in `backend/tests/test_main_lifespan.py::test_the_status_answer_is_the_same_with_and_without_the_one_time_task`** (CI python.yml, Lauf 38309357739, Versuch 1 rot, Versuch 2 grün). Der Test vergleicht zwei Antworten von `status.report()` und entfernt dabei nur `diskFreeBytes`; der verschachtelte Live-Messwert `profile.memoryAvailableBytes` bleibt im Vergleich und unterschied sich zwischen den beiden Lesungen um rund 229 KB (14955311104 gegen 14955540480). Ursache im Test, nicht im Produkt und nicht in Plan 32-01 (keine Berührung von `status.py` oder `main.py`). Vorschlag: im Test auch den Speicherwert entfernen bzw. die Hardware-Lesung per monkeypatch festhalten; die Zusicherung "dieselbe Antwort mit und ohne Einmalaufgabe" bleibt dabei unverändert. Nicht in 32-01 behoben (Scope-Grenze).
  - **Erledigt 12.10.2026 (vor Plan 32-02, eigener Commit):** Der Test hält die Hardware-Lesung fest (`monkeypatch.setattr("findling.main.detect", lambda: _A_READING)`), der Vergleich bleibt vollständig (alle Felder, Hardware eingeschlossen). Gegenprobe mit einer Zwei-Lesungen-Folge: gleiche Lesung grün, nur `memory_available_bytes` verschieden rot (der Flake-Mechanismus), andere Kernzahl rot.

## Plan 32-08

- **Lokales Staging des Store-Archivs nimmt ignorierte Dateien mit.** `scripts/release/store-archive.sh stage-companion` kopiert `php/js` und die anderen Verzeichnisse ganz; auf dem Entwicklungsrechner landet so die gitignorierte Markerdatei `js/.claude-active` im Archivbaum. Die Releases baut deploy-harp aus einem frischen Checkout (`findling-src`), dort gibt es die Datei nicht; kein Befund der Phase 32 und nicht im Plan-Umfang. Vorschlag für Phase 36 (Store-Vorgaben): im Staging `find "${app}" -name '.claude-active' -delete` neben `.gitkeep`, oder nur getrackte Dateien kopieren (`git ls-files`).
