# Abnahme 1.7.0

Tag-Kopf: 22f98ef260fb12f8b55844b76d8070e64f441a4d

Abweichung vom Plan: Der Plan nennt als Tag-Kopf den letzten Commit außerhalb .planning (c1cb767c95e8186a96be6598a38cfaa5dc3752e0). Die CI läuft aber nur auf gepushten Köpfen, und der gepushte Kopf ist 22f98ef2 (darüber nur die Freigabezeile in .planning). Tag-Kopf ist deshalb der CI-geprüfte Kopf selbst. Der Code ist gleich: `git diff --quiet c1cb767c 22f98ef2 -- . ':!.planning'` endet mit 0.

Läufe:

```
45885132814 Integration success
45885134352 OpenSSF Scorecard success
45885132839 Security scans success
45885132920 PHP and store metadata gates success
45885133027 Multi-arch image success
45885132819 Python gates success
45885132910 Resilience success
45885132945 HaRP deploy success
```

Rerun: HaRP deploy 45885132945, Job `deploy-harp (stable34, 8.2, false, ubuntu-24.04)`, im ersten Versuch rot im Schritt "Store upgrade 2b". Die Annahme prüfte 5 s nach dem Neustart des Backends, als die eigene zweite Abholung der Datei mit veraltetem Dateicache noch in der Queue stand (`requeued=1`, "the acceptance left the lines short=1 accepted=1 ... and 1 queue row(s)"). Seit dem grünen Kopf 1db01d02 kein Backend-Code geändert (nur info.xml, Doku, Tests, Changelog-Datum). Die anderen drei Varianten waren grün. Nach genau einem `gh run rerun --failed` war der Job grün. Befund I-45-12-01 (LOW, CI-Robustheit, 1.7.1): Die Annahme von Schritt 2b wartet nicht auf die leere Queue.

audited_head: bb4c0bc8ca9c2b96edacc4de8a846d9d5ccdfe4d

Diff audited_head..Tag-Kopf:

```
 CHANGELOG.de.md                      |   2 +-
 CHANGELOG.fr.md                      |   2 +-
 CHANGELOG.md                         |   2 +-
 backend/appinfo/info.xml             |  99 +++++-----------
 backend/tests/test_store_metadata.py | 220 +++++++++++++++++++++++++++++++++++
 docs/store-listing.md                | 210 +++++++++++++++++++++++++++++++++
 php/appinfo/info.xml                 | 108 +++++------------
 7 files changed, 490 insertions(+), 153 deletions(-)
```

Bedingungen:
- status_45_09: passed
- status_45_10: passed
- Abnahme Härtung 45-10: ja
- Freigabe Version 45-08: ja
- Freigabe Changelog 45-08: ja
- Freigabe Storetext 45-11: ja
- Freigabe Push 45-12: ja
