---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 12
subsystem: Owner-Abnahme 1.6.3 (Runde 2), docs/store-listing.md, CHANGELOG in drei Sprachen, Text-Gate in backend/tests/test_store_metadata.py
tags: [D-43-10, D-43-15, D-43-17, T-43-36, T-43-37, abnahme, go, tag-kopf, changelog, gate]
requires: [43-27]
provides: [GO des Owners für Tag v1.6.3 und Store-Einreichung, Tag-Kopf 8b00d610 mit Belegen, Gesamttext Runde 2, Gate scan_full_text_1_6_3 auf Runde 2]
affects: [43-13, 43-14]
tech-stack:
  added: []
  patterns: [Gate hält die CHANGELOG-Sätze gegen alle drei Sprachdateien, Tag-Kopf als letzter Commit außerhalb von .planning mit leerem Code-Diff zum audited_head]
key-files:
  created:
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-12-SUMMARY.md
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-TESTBUILD-RC2.md
  modified:
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-OWNER-VORLAGE.md
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-ABNAHME.md
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-FREIGABEN.md
    - docs/store-listing.md
    - CHANGELOG.md
    - CHANGELOG.de.md
    - CHANGELOG.fr.md
    - backend/tests/test_store_metadata.py
decisions:
  - "Runde 2 am 11.11.2026: Owner-Zitat 'Wie empfohlen' auf die Empfehlung alles wie Vorlage, I2 mit der gemessenen Dauer von 7,5 Stunden, GO, Push ja"
  - "43-29 gestrichen und 43-11 als abweichend, abgelöst geschlossen (Owner 'Ok'): es gibt kein rc.2"
  - "Tag-Kopf 8b00d6100be0133fd436fd2f277736f5d9e86a9b; Code-Diff zum audited_head 2dacf753 leer"
  - "Ausnahme des Owners ('Ok'): 'PHP and store metadata gates' gilt über Lauf 43090328230 auf 2dacf753 bei unverändertem PHP-Stand; der Lauf auf dem Tag wird vor der Store-Einreichung geprüft"
  - "CHANGELOG-Datum 2026-11-12 als angenommener Tag-Tag"
metrics:
  completed: 2026-11-12T00:20:00+01:00
  tasks: 3
---

# Phase 43 Plan 12: Owner-Abnahme 1.6.3, Runde 2

Der Owner hat 1.6.3 in Runde 2 abgenommen und das GO für Tag und Store-Einreichung gegeben. Der Tag-Kopf 8b00d610 ist festgehalten, grün in sieben Workflows und end to end belegt.

## Tasks

1. **Vorlage Runde 2** (3711d4a0): Abschnitt "# Runde 2" in 43-OWNER-VORLAGE.md mit Umlaut-Audit (0 Funde), Forum-Entwurf auf dem Desktop.
2. **Owner-Runde 2** (8af9f8e5): Zitat, Datum, Kanal, Entscheide je Punkt in 43-ABNAHME.md; Freigaben für Push und Text in 43-FREIGABEN.md.
3. **Texte, Gate, Tag-Kopf** (b413cf68, 914040b4, 8b00d610, cc0d2f62): Gesamttext Runde 2, Datum in drei CHANGELOG-Dateien, Gate auf Runde 2 (23 Selbsttests), Umbruch im deutschen CHANGELOG, Tag-Kopf mit Läufen und Vorprüfung Tag.

## Belege

- pytest tests/test_store_metadata.py, test_changelog_translations.py, test_measurement_scripts.py: 728 passed; ruff, ruff format, pyright, vulture grün.
- Sieben Workflows auf 8b00d610 grün (IDs in 43-ABNAHME.md). `scripts/ci/e2e_head_proof.sh 8b00d610...`: Exit 0 über Lauf 43094681914.
- Vorprüfungen (a) bis (f) für den Tag in 43-ABNAHME.md, Abschnitt "Vorprüfung Tag".

## Abweichungen vom Plan

- Der verify-Befehl von Task 3 verlangt "PHP and store metadata gates" namentlich auf dem Tag-Kopf. Der Workflow startete per Pfadfilter nicht; es gilt die Ausnahme des Owners. Der Befehl endet deshalb an dieser Stelle nicht mit Exit 0, alle anderen Bedingungen sind erfüllt.
- R und I2 ohne rc.2: statt eines rc.2-Ergebnisses der Landebericht zu rc.1; I2 nennt die gemessene Dauer.
- Der Gesamttext Runde 2 enthält zusätzlich Teil 3 (CHANGELOG-Sätze) und Teil 4 (Außentexte); Teil 4 ist vom Gate nicht gehalten.

## Offen, an 43-13 und 43-14 übergeben

- Tag v1.6.3 und Store-Einreichung führt der Owner aus; drei eigene Freigaben für Release-Notiz, Fremdinstallation und Beleg-Push.
- Taggt der Owner nicht am 12.11.2026, ändern sich das CHANGELOG-Datum und der Tag-Kopf.
- Antwort in #25 nach dem Store-Release mit eigener Freigabe.
