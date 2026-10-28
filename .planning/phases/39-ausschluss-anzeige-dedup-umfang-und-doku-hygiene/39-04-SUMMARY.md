---
phase: 39-ausschluss-anzeige-dedup-umfang-und-doku-hygiene
plan: 04
subsystem: ci, dedup
tags: [dedup, smb, acl, ci, measurement, owner-decision]
requires: ["39-01", "39-03"]
provides:
  - "dispatch-only CI measurement of SMB ACL behaviour (smb-acl-measure.yml)"
  - "A7 test: indexed counter counts per fileid"
  - "DEDUP-02 closed: Weg C geliefert, Weg A nicht gebaut, Weg B vertagt auf v1.7"
affects: [phase-40-audit, v1.7-planning]
tech-stack:
  added: []
  patterns: ["Samba aus dem Ubuntu-Archiv auf dem Runner statt Container", "Positivkontrolle am Samba-Server vor jeder Nextcloud-Messung"]
key-files:
  created:
    - .github/workflows/smb-acl-measure.yml
    - scripts/ci/smb_acl_measure.sh
    - scripts/ci/smb_acl_probe.php
    - backend/tests/test_phase39_a7_counter.py
    - .planning/phases/39-ausschluss-anzeige-dedup-umfang-und-doku-hygiene/39-OWNER-VORLAGE.md
    - .planning/phases/39-ausschluss-anzeige-dedup-umfang-und-doku-hygiene/39-DEDUP-ERGEBNIS.md
  modified:
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md
decisions:
  - "D-39-01 = (b): Weg A wird nicht gebaut; Messung A6 zeigt das Leck ohne und mit check_acl"
  - "D-39-02: Weg B vertagt auf v1.7 (Release-Rahmen 29.10., Audit-Pflicht Phase 40)"
metrics:
  duration: "ca. 2 h inkl. Owner-Runde"
  completed: 2026-10-28
  tasks: 3
requirements: [DEDUP-02]
---

# Phase 39 Plan 04: Messung A6/A7 und Abschluss DEDUP-02 Summary

Dispatch-only CI-Messung mit Samba auf dem Runner bestaetigt A6 (Nutzer B sieht die am Server gesperrte Datei gelistet, isReadable() true, auch mit check_acl; nur der Download liefert nichts), A7 per Test (Zaehlung je fileid); Owner entschied "wie empfohlen": Weg A nicht gebaut, Weg B auf v1.7 vertagt.

## Tasks

| Task | Commit | Inhalt |
|------|--------|--------|
| 1 | d8d287a2 | Workflow smb-acl-measure.yml (nur workflow_dispatch, contents: read, SHA-Pins, kein Image), smb_acl_measure.sh, smb_acl_probe.php, A7-Test |
| 1 Fix | 59f93e49 | Timeouts und Schrittmarken fuer jeden Nextcloud-Aufruf (Lauf 1 hing am GET von userb) |
| 2 | 08cfa379 | 39-OWNER-VORLAGE.md mit Messergebnis, D-39-01, D-39-02 |
| 3 | 1003cbce | 39-DEDUP-ERGEBNIS.md (Weg C, Messung A6, A7, Weg A, Weg B, Owner-Antwort woertlich) |

Messlaeufe: 40714077919 (abgebrochen, Hang nach bestandener Positivkontrolle), 40716240639 (success, Ergebnis im Artefakt smb-acl-result und in 39-DEDUP-ERGEBNIS.md).

Owner-Antwort: "Wie empfohlen (Recommended)", 28.10.2026 ca. 16:5x Uhr, Remote Control (AskUserQuestion).

## Deviations from Plan

1. **[Rule 1] check_acl per files_external:config statt files_external:option.** check_acl ist eine Backend-Option des SMB-Backends (Backend/SMB.php, stable34), keine Mount-Option. Commit d8d287a2.
2. **[Rule 3] Timeouts nach Lauf 1.** Der WebDAV-GET von userb auf die gesperrte Datei antwortet nicht; ohne curl-Timeout hing der Lauf. Fix 59f93e49, zweiter Lauf gruen (innerhalb des Limits von zwei Versuchen).
3. **Anmeldung:** nur logincredentials gebraucht; statt userprovided gibt es einen Rueckfall, der die Zugangsdaten ueber ICredentialsManager einspielt; er wurde nicht gebraucht (Tabelle sagt "stored at login").
4. **Push nach main** vor `gh workflow run` durch den Orchestrator freigegeben (Projektregel sonst: kein Push ohne Owner-Wort).
5. **isReadable() doppelt gemessen:** Node::isReadable() und SMB::isReadable() derselben Datei, damit F3 direkt belegt ist.

## Offene Punkte (v1.7)

- check_acl-Nebenbefund: Ursache, warum die Datei auch mit check_acl fuer B gelistet blieb, nicht eingegrenzt (ACL fuer B unlesbar wegen READ_CONTROL im DENY, oder Filecache). Nur relevant, falls Weg A je wieder aufgegriffen wird.
- Weg B: Startpunkt poller is_unchanged und files.content_hash (siehe 39-DEDUP-ERGEBNIS.md).

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsflaeche ausser der im Plan modellierten (T-39-12, T-39-13): der Workflow laeuft nur per Dispatch, mit contents: read, feste Testpasswoerter werden nie ausgegeben (Auth-Dateien 0600, smbpasswd ueber stdin).

## Self-Check: PASSED

- Dateien vorhanden: smb-acl-measure.yml, smb_acl_measure.sh, smb_acl_probe.php, test_phase39_a7_counter.py, 39-OWNER-VORLAGE.md, 39-DEDUP-ERGEBNIS.md
- Commits d8d287a2, 59f93e49, 08cfa379, 1003cbce in der Historie von main bzw. gsd/39-04
- grep der fuenf Abschnitte in 39-DEDUP-ERGEBNIS.md ergibt 5; Zweig Vertagung ohne Produktcode-Diff
