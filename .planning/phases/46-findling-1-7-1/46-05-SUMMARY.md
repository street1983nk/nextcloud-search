---
phase: 46-findling-1-7-1
plan: 05
subsystem: release
tags: [rel-08, version, changelog]
requires: [46-04, 46-03]
provides: [Version 1.7.1, CHANGELOG 1.7.1 EN/DE/FR, Update-Probe ab v1.7.0, README-Faktencheck]
affects: [info.xml beider Apps, CHANGELOG*, deploy-harp.yml, update_in_process_proof.sh, docs]
duration: ca. 50 min
completed: 2026-11-27
---

# 46-05: Version 1.7.1, CHANGELOG, Store-Links, README-Faktencheck

## Ergebnis

- 292197c9 (vorgezogen, `Freigabe Text store-listing 46-05`): drei Zeilen in docs/store-listing.md ohne das gesperrte Wort (I-46-01-01).
- 5b9a8d94, c7cd217b: README-Faktencheck DE/EN/FR (46-README-PRUEFUNG.md), keine falsche Aussage.
- Freigaben (b22b123d, Owner "Ja" 2026-11-27 07:48): Version, Changelog (FR zweiter Punkt im Wortlaut des Owners), Tag-Datum 2026-11-28 vorläufig, Storetext nur Links, README unverändert mit je einem Satz in docs/admin-page.md, Docker-Fenster 46-06.
- 03c53f11 `chore(46-05): version 1.7.1 in both apps`: beide info.xml 1.7.1 (php version, backend version und image-tag), je sechs Links blob/v1.7.0 auf blob/v1.7.1, Store-Text sonst unverändert; FROM_TAGS endet auf v1.7.0 (Kommentar und Begründung mitgezogen); deploy-harp.yml "the tree carries 1.7.1 (1.7.0 until 2026-11-27, ...)", "jump is 1.5.0 to 1.7.1", ein Satz "Release 1.7.1 keeps the start on v1.5.0 (plan 46-05): no migration and no schema change", 508 633 Byte; CHANGELOG [1.7.1] - 2026-11-28 in EN/DE/FR, nur Fixed/Behoben/Corrigé, ohne Issue-Nummern, Link compare/v1.7.0...v1.7.1; test_store_metadata vergleicht die abgenommenen Store-Texte mit beiseitegelassener Release-Nummer im blob-Link (welche Version verlinkt ist, prüft weiter scan_doc_links gegen `<version>`).
- 2. Commit: docs/admin-page.md zwei Sätze (Enter wie der Knopf, IME fügt nichts hinzu; unter 360 px Chip unter dem Grund). Eine EN- oder FR-Fassung von admin-page.md gibt es nicht.
- STOPP-Prüfung: `git diff --stat v1.7.0..HEAD -- php/lib/Migration` leer, Schemadateien (store/schema.sql, store/vectors.sql, index/schema.py) leer.
- Gates: lockstep, store_metadata, upgrade_seed_steps, update_in_process_proof, workflow_size, changelog_translations, public_artifacts, phase33/34 audit 419 passed, 107 skipped; ruff, ruff format, pyright (0 Fehler), vulture grün; keine Gedankenstriche, keine closes/fixes-Wörter in den CHANGELOGs.

## Abweichungen

- Version und CHANGELOG in einem Commit statt zwei: `test_update_in_process_proof` verlangt, dass info.xml die neueste CHANGELOG-Überschrift trägt; getrennt wäre einer der Commits rot gewesen. Beide Gegenstände waren vor dem Commit freigegeben.
- Arbeitsdateien von CRLF auf LF gebracht (core.autocrlf true), die Commits enthalten nur die gewollten Zeilen.
