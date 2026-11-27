# Abnahme 1.7.1

Stand: 2026-11-28, Plan 46-08. Muster 45-12 mit der Lehre aus 45-ABNAHME.md Z. 5.

Fall: 1
Tag-Kopf: a3c94c1635b2fe13436394524ed3bb3aa05792b5

Begründung Fall 1: Datum von [1.7.1] in CHANGELOG.md, CHANGELOG.de.md, CHANGELOG.fr.md ist 2026-11-28 und gleich dem geplanten Tag des Tags (Entscheid Tag-Datum 46-05). Keine neue Datumszeile, Tag-Kopf ist der ci_head aus 46-AUDIT.md.

Läufe (alle headSha a3c94c1635b2fe13436394524ed3bb3aa05792b5, success):

- 46076437121 Python gates
- 46076437005 PHP and store metadata gates
- 46076437035 HaRP deploy
- 46076437149 Integration
- 46076437150 Resilience
- 46076437214 Multi-arch image
- 46076437153 Security scans
- 46076437084 OpenSSF Scorecard
- Workflow security lint: lief nicht (paths-Filter, `.github` seit a66b016c unverändert), grün auf a66b016c (45973260375)

audited_head: a3c94c1635b2fe13436394524ed3bb3aa05792b5
ci_head: a3c94c1635b2fe13436394524ed3bb3aa05792b5

Diff audited_head..Tag-Kopf: leer (gleicher Commit)

Bedingungen:

- status_46_06: passed (46-AUDIT.md)
- status_46_07: passed (46-AUDIT.md, Nachtrag 46-07)
- Abnahme Härtung 46-07: ja
- Freigabe Version 46-05: ja (1.7.1 für findling und findling_backend)
- Freigabe Changelog 46-05: ja, dazu Changelog 46-07 (vierter Punkt) und Changelog #63 46-07 (fünfter Punkt)
- Freigabe Storetext 46-05: ja
- Freigabe Push 46-08: ja (nur Belegdokumente unter .planning, Code von origin/main bleibt gleich Tag-Kopf)
