---
phase: 37-owner-tor-und-store-sichtbarkeit
plan: 02
subsystem: store-metadata
tags: [store, info.xml, gates, discussion-link, STORE-01, STORE-02]
requires: [37-OWNER-ENTSCHEIDE.md, D-37-05, D-37-06, D-37-07, D-37-08]
provides: [APP_IDS, STORE_NAMES, DISCUSSION_URL, DRAFT_OF_PHASE_37, APPROVAL_DATE, scan_identity, scan_discussion, scan_phase_37_draft]
affects: [phase-40-store-submission]
tech-stack:
  added: []
  patterns: [scan_xxx-Befundsaetze mit Bestandstest plus Mutationstests, Entwurfsabschnitt per startswith bis zur naechsten '# '-Ueberschrift]
key-files:
  created: []
  modified:
    - backend/tests/test_store_metadata.py
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - docs/store-listing.md
decisions:
  - "discussion-Element (Forum-Thread 249775) in beiden info.xml zwischen website und bugs, mit Kommentar D-37-07"
  - "Namen und alle sechs Beschreibungen Byte fuer Byte unveraendert (D-37-05, D-37-06, D-37-08 = a)"
  - "Gate fuer die Namen im Entwurf prueft Tabellenzeilen (App | Sprache | ... | Wert) statt blossem Teilstring, damit 'Findling Backend' nicht zufaellig trifft"
metrics:
  duration: "ca. 20 min"
  completed: 2026-10-28
  tasks: 2
  files: 4
---

# Phase 37 Plan 02: Store-Sichtbarkeit Summary

Beide info.xml tragen jetzt genau ein discussion-Element auf den Forum-Thread 249775 (D-37-07), zwischen website und bugs. App-IDs, Namen ("Findling Search" / "Findling Suche" / "Findling Recherche", "Findling Backend") und der Cross-Promo-Satz sind durch neue Gates in test_store_metadata.py festgehalten. docs/store-listing.md fuehrt den Abschnitt "# Entwurf v1.6.0 (Teil Phase 37), abgenommen am 28.10.2026". Version bleibt 1.5.1, nichts eingereicht.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Gates fuer IDs, Namen, discussion-Link, Cross-Promo und Entwurfsabschnitt (RED) | c20d7c3d |
| 2 | info.xml beider Apps und docs/store-listing.md eingespielt (GREEN), Schema und Qualitaetsgates | e17ed7c5 |

## TDD Gate Compliance

- RED: c20d7c3d `test(37-02)`, gegen den Ist-Stand 2 failed (discussion-Bestandstest, Entwurfs-Bestandstest), 20 passed (Identitaet, Connector, alle Mutationstests). Anzahl `def test_` 91 -> 110.
- GREEN: e17ed7c5 `feat(37-02)`, alle Gates gruen.
- REFACTOR: nicht noetig.

## Verifikation (Task-2-Verify, 28.10.2026)

- curl -L Forum-URL: HTTP 200, 0 Weiterleitungen (13:30 Uhr / 12:30Z)
- grep -c '<discussion>': 1 in php/appinfo/info.xml, 1 in backend/appinfo/info.xml
- Ueberschrift '^# Entwurf v1\.6\.0 \(Teil Phase 37\), abgenommen am 28.10.2026' vorhanden, direkt vor '# Release 1.5.1 (22.10.2026): Umbenennung'
- lxml pre-info.xslt + info.xsd: [True, True], error_log leer
- pytest test_store_metadata.py + test_migration_path.py + test_measurement_scripts.py: 706 passed
- ruff check, ruff format --check (234 Dateien), pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest, 0 errors), vulture src tests --min-confidence 80: ohne Befund
- Zusaetzlich gruen: test_info_xml_defaults, test_lockstep_versions, test_uninstall_contract, test_workflow_tag_triggers, test_phase35_audit, test_phase36_audit
- Baumhash-Gegenprobe: git diff --name-only 1f276c0e HEAD -- '*.php' backend/src = 0 Dateien; PACKAGE_TREE_HASH, PHP_TREE_HASH_TODAY, PHP_FILES_TODAY bleiben richtig (test_measurement_scripts gruen)
- Dash-Pruefung: kein U+2013/U+2014 im Diff; Umlaut-Audit: keine deutsche/franzoesische Store-Zeile in info.xml geaendert; der neue Abschnitt in store-listing.md nutzt echte Umlaute und Akzente (ä, ö, ü, é)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ruff ISC004/E501 in den neuen Tests**
- **Found during:** Task 1 (vor dem Commit)
- **Issue:** implizit verkettete Strings in Listen ohne Klammern, eine Zeile ueber 120 Zeichen
- **Fix:** Klammern um die 8 Verkettungen, ruff format
- **Files modified:** backend/tests/test_store_metadata.py
- **Commit:** c20d7c3d

### Hinweise

- Plan-Verify nutzt `git diff HEAD~2`; zwischen den beiden Task-Commits liegt ein paralleler Commit eefdd1a2 `docs(38): create phase plan` (andere Session). Die Gegenprobe wurde deshalb gegen den Planstart 1f276c0e gefahren: 0 Dateien.
- Commits ohne Claude-Session-Trailer, weil der Plan fuer beide Commits ausdruecklich "keine Claude-Trailer, Owner-Regel" vorschreibt (Orchestrator: "Follow the plan if it says otherwise").
- test_phase34_audit nicht gelaufen: braucht docker, haengt auf dieser Box (Auftrag: kein docker).

## Bekannte Spannung (D-37-08 = a)

Die Regel "Nur EIN Satz zum MCP Connector, und keine RAG-Wortwahl" in docs/store-listing.md bleibt unveraendert, obwohl der ausgelieferte Satz "RAG" sagt. Der Owner hat das mit D-37-08 bewusst so belassen; der neue Abschnitt der Phase 37 vermerkt es. Der Verweis "Begruendung im Connector-BACKLOG BL-01" ist nicht angepasst (Connector-Repo).

## Offen

- CI-Job app-metadata (php.yml, xmllint gegen die gepinnte XSD) laeuft erst mit dem naechsten freigegebenen Push; nicht gepusht.
- Einreichung und Versionssprung auf 1.6.0: Phase 40.

## Threat Model

- T-37-04 (IDs): scan_identity + Mutationstest findling -> findling_search
- T-37-05 (URL): DISCUSSION_URL zeichengleich zu D-37-07, https auf help.nextcloud.com, curl 200 vor dem Commit
- T-37-06 (Schema): scan_discussion prueft Reihenfolge website, discussion, bugs; lxml XSLT+XSD True fuer beide Dateien

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: backend/tests/test_store_metadata.py, php/appinfo/info.xml, backend/appinfo/info.xml, docs/store-listing.md
- FOUND: c20d7c3d, e17ed7c5
