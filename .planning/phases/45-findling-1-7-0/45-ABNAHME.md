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

## Signatur-Probe

Freigabe Signatur 45-13 "Ja". `gh workflow run release.yml --ref main -f create_release=false`, Lauf 45892161829 (workflow_dispatch), Commit des Laufs 22f98ef260fb12f8b55844b76d8070e64f441a4d = Tag-Kopf, Ergebnis success (`gh run watch --exit-status` 0). Belege aus dem Log wörtlich:

```
2026-11-26T20:36:36.4872667Z php/appinfo/info.xml is 18490 bytes, the store limit is 524288
2026-11-26T20:36:37.3469871Z appinfo/signature.json was written and is not empty
2026-11-26T20:36:37.5800136Z dist/findling.tar.gz is 808546 bytes, the store limit is 20971520
2026-11-26T20:36:37.6062634Z the release signature is 684 base64 characters
2026-11-26T20:36:37.6270227Z Verified OK
2026-11-26T20:36:37.6937186Z backend/appinfo/info.xml is 35054 bytes, the store limit is 524288
2026-11-26T20:36:37.7372970Z dist/findling_backend.tar.gz is 52371 bytes, the store limit is 20971520
2026-11-26T20:36:37.7570765Z the release signature is 684 base64 characters
2026-11-26T20:36:37.7759706Z Verified OK
2026-11-26T20:36:37.8137460Z dist/findling.tar.gz: carries appinfo/signature.json, as the integrity check of the instance requires
```

Beide Release-Signaturen "Verified OK", Code-Signatur der Companion-App geschrieben und im Archiv, beide Archive unter 20 971 520 B (808 546 und 52 371). Kein Release angelegt: `gh release view v1.7.0` endet mit Exit 1, vor und nach dem Lauf.
