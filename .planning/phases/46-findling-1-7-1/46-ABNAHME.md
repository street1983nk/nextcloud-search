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

## Signatur-Probe

Nach `Freigabe Signatur 46-09`: `gh workflow run release.yml --ref main -f create_release=false`, Lauf 46083361339, success. Code von origin/main gleich Tag-Kopf (`git diff --quiet a3c94c16 origin/main -- . ':!.planning'`), release.yml seit v1.7.0 unverändert (T-46-21).

Probe-headSha: 7806e83a7f92369fccac3bbf8affba396b032a28

- `appinfo/signature.json was written and is not empty` (Code-Signatur der Companion-App)
- `dist/findling.tar.gz is 811859 bytes, the store limit is 20971520`, Release-Signatur: `Verified OK`
- `dist/findling_backend.tar.gz is 53293 bytes, the store limit is 20971520`, Release-Signatur: `Verified OK`
- `dist/findling.tar.gz: carries appinfo/signature.json, as the integrity check of the instance requires`
- `dist/findling_backend.tar.gz: carries no code signature, which is correct for a container half`
- Kein Release v1.7.1 (`gh release view v1.7.1` ohne Treffer), kein Tag v1.7.1 auf origin (`git ls-remote --tags origin v1.7.1` leer)

## Vorprüfung Tag

Stand 2026-11-28 00:11 UTC, Tag-Kopf K = a3c94c1635b2fe13436394524ed3bb3aa05792b5, origin/main = a64fdbaa.

- Code von origin/main gleich K: `git diff --quiet K origin/main -- . ':!.planning'` rc 0.
- Workflows am K alle grün (push): HaRP deploy, Integration, Multi-arch image, OpenSSF Scorecard, PHP and store metadata gates, Python gates, Resilience, Security scans; `scripts/ci/head_green.sh` mit vollem Hash grün.
- Signatur-Probe grün: Lauf 46083361339 success auf 7806e83a (Code gleich K, T-46-22).
- threats_open 0 (46-SECURITY.md status verified, d22d47bb; Abschluss Security 46-10).
- Kein Tag v1.7.1 lokal und auf origin (`git ls-remote --tags origin v1.7.1` leer).
- Versionen am K: php/appinfo/info.xml 1.7.1, backend/appinfo/info.xml 1.7.1, image-tag 1.7.1.
- blob/v1.7.1-Pfade: 6 verschiedene, alle mit `git cat-file -e K:<pfad>` vorhanden.
- CHANGELOG `## [1.7.1] - 2026-11-28` gleich heute.
- Befehle: `git tag -a v1.7.1 -m "Findling 1.7.1" a3c94c1635b2fe13436394524ed3bb3aa05792b5` und `git push origin v1.7.1`.

## Release-Lauf

- Tag v1.7.1 annotiert auf a3c94c1635b2fe13436394524ed3bb3aa05792b5, gepusht 2026-11-28 00:10:58 UTC (Freigabe Tag 46-11).
- Release archives for the app store 46086508768 success; "Verified OK" für das Begleit- und das Backend-Archiv (00:11:59Z).
- Größen: findling.tar.gz 811 833 Byte, findling_backend.tar.gz 53 307 Byte (beide unter 20 971 520).
- SHA-256: findling.tar.gz 77bbf272716bfe818011385c76dad59c63cc3d5b3337618ce13e7ec630bf2ba4, findling_backend.tar.gz 84c5bc33f8e1ad8d011abc90d7b6016abe634ab510a4713319da4c1a910bf487.
- Release immutable true, kein Entwurf; Notiz per `gh release edit` gesetzt (Freigabe ReleaseEdit 46-11), Assets unverändert.
- Image ghcr.io/street1983nk/findling_backend:1.7.1 Digest sha256:d8be49cee64630f9dff4af07b06215b09eda7f50ad009323277fc53d195721f6 (Tags 1.7.1, a3c94c16..., dev; per `gh api`, ohne Docker-Pull), Lauf Multi-arch image 46086508788 success für linux/amd64 und linux/arm64.
- Tag-Läufe alle success: Workflow security lint 46086508778, PHP and store metadata gates 46086508834, Python gates 46086508804, Integration 46086508749, Resilience 46086508785, HaRP deploy 46086508783, Multi-arch image 46086508788.
- blob/v1.7.1-Links: 6 von 6 liefern 200 (README.md, README.en.md, README.fr.md, docs/migrate-from-fulltextsearch.md/.en.md/.fr.md).

## Store-Einreichung

- store-submit.yml 46089033695 (Dispatch 00:39 UTC, Freigabe Store 46-11) success.
- release findling v1.7.1: HTTP 201
- release findling_backend v1.7.1: HTTP 201

## Fremdinstallation

- deploy-harp 46089036633 mit release_tag=v1.7.1 (Freigabe Dispatch 46-11) success; Schritt "Store install 1 from the release, load both archives instead of building them" und "Store install 1 content proof" grün auf stable33/8.2, stable34/8.2, stable34/8.2 arm, stable35/8.3; das Bauen der Archive übersprungen.
