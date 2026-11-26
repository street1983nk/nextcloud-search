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

## Vorprüfung Tag

Stand 2026-11-26, Tag-Kopf 22f98ef260fb12f8b55844b76d8070e64f441a4d.

- Code am Tag-Kopf gleich origin/main (`git diff --quiet <tk> origin/main -- . ':!.planning'`: 0): ja
- Diff audited_head bb4c0bc8..Tag-Kopf außerhalb .planning genau die in 45-12 erlaubten Dateien: CHANGELOG.de.md, CHANGELOG.fr.md, CHANGELOG.md (nur Datumszeile), backend/appinfo/info.xml, backend/tests/test_store_metadata.py, docs/store-listing.md, php/appinfo/info.xml: ja
- CHANGELOG `## [1.7.0] - 2026-11-26` gleich dem heutigen Datum (UTC): ja. Wird der Tag erst nach 00:00 UTC gesetzt, liegt das Datum einen Tag zurück (Befund an den Owner).
- head_green.sh sieben Workflows am Tag-Kopf: grün (Läufe oben, ein Rerun HaRP deploy, I-45-12-01)
- Signatur-Probe 45892161829 auf dem Tag-Kopf: grün, zweimal Verified OK
- Kein Tag v1.7.0 auf origin (`git ls-remote --tags origin v1.7.0`: 0 Zeilen), kein Release (`gh release view v1.7.0`: Exit 1): ja
- Alle blob/v1.7.0-Pfade der beiden info.xml existieren am Tag-Kopf (`git cat-file -e`): README.md, README.en.md, README.fr.md, docs/migrate-from-fulltextsearch.md, .en.md, .fr.md: ja
- Security: 45-SECURITY.md threats_open 0, Abschluss Security 45-16 "Ja": ja

Befehlsfertig:

```
git tag -a v1.7.0 -m "Findling 1.7.0" 22f98ef260fb12f8b55844b76d8070e64f441a4d
git push origin v1.7.0
```

## Release-Lauf

Tag v1.7.0 annotiert ("Findling 1.7.0") auf 22f98ef260fb12f8b55844b76d8070e64f441a4d, gepusht 2026-11-26 21:05 UTC (Freigabe Tag 45-14, Option a). Release-Lauf 45895635994 (push auf v1.7.0), Ergebnis success, Commit des Laufs = Tag-Kopf. Belege aus dem Log wörtlich:

```
2026-11-26T21:07:16.6194974Z php/appinfo/info.xml is 18490 bytes, the store limit is 524288
2026-11-26T21:07:17.4955595Z appinfo/signature.json was written and is not empty
2026-11-26T21:07:17.7128412Z dist/findling.tar.gz is 808542 bytes, the store limit is 20971520
2026-11-26T21:07:17.7530379Z Verified OK
2026-11-26T21:07:17.7927575Z backend/appinfo/info.xml is 35054 bytes, the store limit is 524288
2026-11-26T21:07:17.8298444Z dist/findling_backend.tar.gz is 52368 bytes, the store limit is 20971520
2026-11-26T21:07:17.8698611Z Verified OK
2026-11-26T21:07:17.9053598Z dist/findling.tar.gz: carries appinfo/signature.json, as the integrity check of the instance requires
```

`gh release view v1.7.0`: isImmutable true; Assets findling.tar.gz, findling.tar.gz.sig, findling_backend.tar.gz, findling_backend.tar.gz.sig, findling-1.7.0-source.tar.gz und die Quellarchive libde265-1.1.3, libheif-1.23.6, pillow_heif-1.8.1, x265_4.3. Release-Notiz (Freigabe ReleaseEdit 45-14) als englische Faktenliste gesetzt, Titel "Findling 1.7.0". Dispatch deploy-harp mit release_tag=v1.7.0 (Freigabe Dispatch 45-14): Lauf 45896004205.

## Store-Einreichung

Freigabe Store 45-14 ("Ok", 2026-11-26 21:10). `store-submit.yml` mit tag=v1.7.0, ein Lauf, 45898491529, success. Belege aus dem Log wörtlich:

```
2026-11-26T21:29:53.0822261Z php.yml run 45895636004 on v1.7.0: success; job 'Store update in one process (issue 51)': success
2026-11-26T21:29:54.6411110Z release findling v1.7.0: HTTP 201
2026-11-26T21:29:56.1472371Z release findling_backend v1.7.0: HTTP 201
```
