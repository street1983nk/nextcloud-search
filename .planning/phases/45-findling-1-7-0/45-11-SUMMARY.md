---
phase: 45-findling-1-7-0
plan: 11
subsystem: store texts (info.xml beider Apps), docs/store-listing.md, store gates
tags: [store-03, store-04, d-45-13, d-45-14]
requires: [45-10, 45-07]
provides:
  - "Sechs kurze Store-Beschreibungen (findling, findling_backend; en/de/fr), vom Owner am 26.11.2026 freigegeben, zeichengleich in beiden info.xml"
  - "Abschnitt '# Entwurf v1.7.0 (Store-Texte kurz), abgenommen am 26.11.2026' in docs/store-listing.md"
  - "45-STORE-VORLAGE.md mit Längenvergleich, Entwürfen, Liste der Verlagerungen und Diff-Auszug"
  - "Drei neue Gates mit Fehl-Samples: zeichengleich zum abgenommenen Abschnitt, Doku-Link je Sprache auf dem Release-Tag, keine Rückkehr der verlagerten Inhalte"
affects: [45-12]
key-files:
  created:
    - .planning/phases/45-findling-1-7-0/45-STORE-VORLAGE.md
  modified:
    - docs/store-listing.md
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - backend/tests/test_store_metadata.py
decisions:
  - "Doku-Link-Gate liest die Version aus <version> der info.xml (blob/v1.7.0 für 1.7.0), damit der nächste Release ihn mitzieht statt ihn zu brechen"
  - "Datenschutz-Satz als eigene Zeile statt Listenpunkt, Wortlaut unverändert; Enterprise-Zeile, RAM- und CPU-Zeile bleiben (vom Owner wie vorgelegt freigegeben)"
metrics:
  completed: 2026-11-26
---

# Phase 45 Plan 11: Kurze Store-Texte DE/EN/FR für beide Apps (STORE-03) Summary

Die sechs Store-Beschreibungen sind auf eine kurze Faktenliste mit Datenschutz-Satz, Connector-Satz, Umstiegs-Link und README-Link der eigenen Sprache auf `blob/v1.7.0` gekürzt (rund 1.200 bis 1.500 statt 2.300 bis 2.900 Zeichen), vom Owner freigegeben und zeichengleich eingebaut; drei neue Gates halten das.

## Store-API-Abfrage

Genau eine: `curl -s https://apps.nextcloud.com/api/v1/apps.json` am
**2026-11-26T18:42:31Z** (1017 Apps), Datei im Scratchpad, Auswertung per
eigenem Skript mit `uv run python`.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Längenmessung und Entwurf | e859018a | 45-STORE-VORLAGE.md, docs/store-listing.md |
| 2 | Owner-Freigabe (Koordinator) | 76c6f389 | 45-FREIGABEN.md, Zeile `Freigabe Storetext 45-11: "Ok" (2026-11-26 18:59, Claude-Code-Chat) Entscheid: ja` |
| 3 | Einbau, abgenommener Entwurf, Gates | d5e8e1d0 | php/appinfo/info.xml, backend/appinfo/info.xml, docs/store-listing.md, backend/tests/test_store_metadata.py |

## Längenvergleich (Zeichen)

| App | en | de | fr |
|---|---|---|---|
| context_chat 5.6.0 | 610 | n/a | n/a |
| files_fulltextsearch_tesseract 32.0.0 | 357 | n/a | n/a |
| fulltextsearch 35.0.1 | 62 | n/a | n/a |
| recognize 9.0.9 | 3148 | n/a | n/a |
| findling alt (1.6.5) | 2517 | 2662 | 2884 |
| findling_backend alt | 2284 | 2403 | 2631 |
| findling neu | 1279 | 1329 | 1473 |
| findling_backend neu | 1212 | 1215 | 1375 |

## Neue Gates (test_store_metadata.py)

- `test_every_description_stands_in_the_accepted_short_texts_of_1_7_0` (scan_short_store_texts): jede Beschreibung als eigener Codeblock zeichengleich im Abschnitt mit Abnahmedatum. Fehl-Samples: ein Zeichen geändert (EN findling), Kopf ohne Datum, Abschnitt fehlt.
- `test_every_description_links_the_readme_of_its_language_on_the_release_tag` (scan_doc_links): genau ein README-Link, eigene Sprache, Tag aus `<version>`. Fehl-Samples: falsche Sprache, falscher Tag (v1.6.5), kein Link; Positivfall.
- `test_no_description_takes_back_what_moved_to_the_readmes` (scan_moved_contents): keine Messzahl, keine Grenzen-/Format-Überschrift, keine Formatzeile, kein Share-Satz, keine Zeile Ähnliche Dokumente. Fehl-Samples für alle; Positivfall mit RAM/CPU-Zeile.

## Verifikation

- `sh scripts/dev/validate_info_xml.sh php/appinfo/info.xml backend/appinfo/info.xml`: beide bestehen Transform und Schema (appstore eda850ba). Hinweis: ohne lokales xsltproc/xmllint startet das Skript selbst einen einmaligen alpine-Container.
- 20 Testdateien, die info.xml, store-listing oder die READMEs lesen: 1767 passed, 19 skipped. Keine Alt-Tests angepasst, alle blieben grün.
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture (Konfiguration und `src tests --min-confidence 80`) grün.
- Task-1- und Task-3-`<verify>` grün (191 passed in test_store_metadata.py plus test_lockstep_versions.py).
- Der Lauf der ganzen Testsuite wurde vom System wegen Speichermangel abgebrochen und nicht wiederholt; geprüft sind die 20 Dateien oben.

## Deviations from Plan

Keine inhaltlichen. Der Gate für den Doku-Link liest die Version aus der info.xml statt `v1.7.0` fest zu verdrahten (Rule 2, sonst bricht er beim nächsten Release).

## Known Stubs

Keine. Die Links auf `blob/v1.7.0` lösen erst nach dem Tag auf (45-12).
