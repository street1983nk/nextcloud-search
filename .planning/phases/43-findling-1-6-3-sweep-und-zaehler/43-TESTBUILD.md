# 43-TESTBUILD: Testbuild 1.6.3-rc.1 für mbozem (D-43-10, D-43-13)

**Stand:** 2026-11-09, Task 3 abgeschlossen. Alle CI-abhängigen Felder sind mit den Belegen aus dem grünen Proof-Lauf 42565361965 und dem Artefakt-Lauf 42537119924 gefüllt.

## Zweck

mbozem (Issue #25) prüft seine Abdeckungszahl vor der Store-Einreichung 1.6.3 (erwartet etwa 18 % bei laufendem Crawl). Nach D-43-13 gibt es KEIN öffentliches GitHub-Pre-Release: der Testbuild besteht aus einem signierten Companion-Archiv als Workflow-Artefakt (nur für angemeldete GitHub-Nutzer, läuft ab), einem unveränderlichen Backend-Image `:<sha>` und einer Test-info.xml im Branch. Vorher weist der Proof-Workflow nach, dass die Versionsordnung hält (A5/A6, Pitfall 6): die spätere Store-1.6.3 muss bei ihm als Update erscheinen.

## Branch rc/1.6.3-rc.1 (lokal, NIE nach main mergen)

- Branch-Commit: `47c4ce4e7047d98a2bc4a494146953821f4dbc29` (`chore(43-10): test build 1.6.3-rc.1 for the reporter`; der alte Stand f6c5a6ce wurde nach dem Fix-Delta verworfen, siehe 43-10-SUMMARY.md)
- Basis: main-Kopf `7725bba8` (Fix-Delta nach dem Audit, nur Harness); `audited_head` = `37b518d6754a4a8a8593dc537a13b27644caf986` (43-AUDIT.md) gilt unverändert, kein Produktcode berührt
- Diff-Beleg: `git diff 7725bba8..47c4ce4e --name-only` zeigt genau `backend/appinfo/info.xml`, `php/appinfo/info.xml`, `testbuild/findling_backend-1.6.3-rc.1-info.xml`; der Inhalts-Diff der beiden info.xml besteht nur aus den drei Versionszeilen (`<version>` zweimal, `<image-tag>` einmal, je 1.6.3 zu 1.6.3-rc.1). Lockstep bleibt grün (version == image-tag == 1.6.3-rc.1).
- Test-info.xml: `testbuild/findling_backend-1.6.3-rc.1-info.xml` = backend/appinfo/info.xml des Branches mit `<image-tag>655fe197cc4363e7da2f7c6a7e8000c561f3b31e</image-tag>`.

## Image-Digest

- Image: `ghcr.io/street1983nk/findling_backend:655fe197cc4363e7da2f7c6a7e8000c561f3b31e`
- Digest (Index): `sha256:30d56229b7abebee1e93e1c25a33b1811a3b7a44a0ba35b88defc19a9032a58f`
- Plattformen: linux/amd64 und linux/arm64 (am 2026-11-08 anonym über die ghcr-Registry-API gelesen: Token ohne Anmeldung, `GET /v2/street1983nk/findling_backend/manifests/<tag>`, Media-Type `application/vnd.oci.image.index.v1+json`)
- Herkunft: docker.yml-Lauf 42523105680 (push auf main, grün, 2026-11-08). docker.yml taggt `:<GITHUB_SHA>` mit dem KOPF des Pushes; der Push von 43-09 trug den Fix `37b518d6` und drei Doku-Commits, Kopf `655fe197`.
- Abweichung vom Plan-Wortlaut ("jüngster Commit <= audited_head"): `655fe197` ist ein NACHFAHRE des audited_head (nur .planning-Doku dazwischen). Es gibt keinen Vorfahren-Tag mit leerem backend-Diff: der letzte Lauf davor (`d9f8a65d`) liegt VOR dem Fix `37b518d6`. Beleg der Gleichheit: `git diff --stat 37b518d6 655fe197 -- backend` ist leer, der backend/-Stand des Images ist also exakt der audited_head. Damit ist das must_have "backend/-Stand gleich audited_head" erfüllt.

## Proof-Workflow (rc-version-proof.yml, nur workflow_dispatch)

Eingänge: `rc_ref` (Standard rc/1.6.3-rc.1), `archive_run_id` (Lauf-ID des release.yml-Dispatch), `image_sha` (655fe197cc4363e7da2f7c6a7e8000c561f3b31e). Run-Blöcke in `scripts/ci/rc_version_proof.sh`.

Was er nachweist:
- **A6** (frische NC stable33 UND stable34): Companion aus Release v1.6.2 installiert, eine Zeile in findling_scan_stats per SQL gesetzt (Begründung im Log: kein Backend-Container im Job, die Migration liest nur "mindestens eine Zeile"), rc-Archiv aus `archive_run_id` geholt, Signatur gegen das öffentliche Zertifikat geprüft (Fingerprint-Abgleich wie release.yml), über apps/findling entpackt, `occ upgrade`, app:list zeigt 1.6.3-rc.1, Migration 001603Date20261108000000 in oc_migrations, `coverage_per_document_hint` = 1; Servers Vergleichsfunktion per grep in lib/private/Installer.php und lib/private/App/AppStore/ gefunden (Datei:Zeile ins Log), `php -r` mit version_compare(a, b, '>') beweist 1.6.3 > 1.6.3-rc.1 > 1.6.2.
- **A5** (stable34, HaRP nach Muster deploy-harp.yml): Daemon + Front-Proxy wie dort, Backend 1.6.2 aus der info.xml des Tags v1.6.2 registriert (zieht :1.6.2), AppAPI-Vergleichsfunktion per grep in lib/Command/ExApp und lib/Service gefunden, Store-Erkennung separat gegriffen (ExAppArchiveFetcher/Fetcher/AppAPIService, Fallback ganzes lib/), `php -r` für beide Paare; dann `occ app_api:app:update findling_backend --info-xml https://raw.githubusercontent.com/street1983nk/nextcloud-search/<rc_ref>/testbuild/findling_backend-1.6.3-rc.1-info.xml` (die URL-Form des Melders), Image-Pull :<sha> am laufenden Container belegt, app:list zeigt 1.6.3-rc.1, /heartbeat antwortet; danach eine im Lauf erzeugte Store-förmige info.xml mit Version 1.6.3 und image-tag <sha>: Update wird angewendet. Jede occ-Ausgabe wörtlich; scheitert ein Schritt ohne `--force-update`, wird er damit wiederholt und beide Ausgaben stehen im Log.
- Scheitert A5 oder A6: Job-Summary `A5: failed <grund>` bzw. `A6: failed <grund>`, Exit 1, KEINE Weitergabe an den Melder; Befund mit Alternativen an den Owner, Entscheid in 43-11.

## Proof-Lauf

- Lauf-ID: 42565361965 (grün, 2026-11-09 05:06 UTC, Dispatch auf main mit rc_ref=rc/1.6.3-rc.1, archive_run_id=42537119924, image_sha=655fe197cc4363e7da2f7c6a7e8000c561f3b31e; ARCHIVE_RUN_ID 42537119924 steht wörtlich im Job-Env des Logs)

Ergebnis wörtlich aus der Job-Summary:

A5: ok
A6: ok

Store-Erkennung AppAPI: apps/app_api/lib/Fetcher/ExAppFetcher.php:124 nutzt version_compare

### A6-Kernausgaben (wörtlich aus dem Log, Job a6-companion, Matrix stable33 UND stable34 grün)

- `installed companion before the upgrade: 1.6.2`
- `seeding one scan row by SQL, because no backend container exists in this job to crawl one`
- `archive 692014 bytes, signature 684 bytes` und `Verified OK` (Signaturprüfung gegen das öffentliche Zertifikat)
- `occ upgrade`: `Updating <findling> ...`, `Updated <findling> to 1.6.3-rc.1`, `Update successful`
- `app:list shows findling at 1.6.3-rc.1`
- `oc_migrations carries 001603Date20261108000000`
- `coverage_per_document_hint = 1`
- Servers Vergleichsstelle (grep im Checkout, Datei:Zeile, stable34/stable33):
  - `lib/private/Installer.php:310` bzw. `:309` (`if (version_compare($currentVersion, $newVersion) === 1) {`)
  - `lib/private/Installer.php:391` bzw. `:390` (`if ($currentVersion !== '0' && version_compare($newestVersion, $currentVersion, '>')) {`)
  - `lib/private/App/AppStore/Fetcher/AppFetcher.php:129` bzw. `:125` (`return version_compare($version1, $version2);`)
- `php -r version_compare('1.6.3', '1.6.3-rc.1', '>') = true (raw comparison 1)`
- `php -r version_compare('1.6.3-rc.1', '1.6.2', '>') = true (raw comparison 1)`
- `A6 detail: 1.6.2 to 1.6.3-rc.1 upgraded, migration ran, hint flag 1, server comparison reads 1.6.3 as newer than 1.6.3-rc.1`

### A5-Kernausgaben (wörtlich aus dem Log, Job a5-backend, stable34 mit HaRP)

- Registrierung 1.6.2: `ExApp findling_backend deployed successfully.`, `ExApp findling_backend successfully registered.`
- AppAPI-Vergleichsstellen (grep im app_api-Checkout, Datei:Zeile):
  - `apps/app_api/lib/Command/ExApp/Update.php:75` (`return $exApp !== null && isset($app['releases'][0]['version']) && version_compare($newestVersion, $exApp->getVersion(), '>');`)
  - `apps/app_api/lib/Service/AppAPIService.php:412` (`if (version_compare($requestExAppVersion, $exApp->getVersion(), '>')) {`)
  - `apps/app_api/lib/Fetcher/ExAppFetcher.php:124` (`return version_compare($version1, $version2);`) und `:173` (gleiche Form wie Update.php:75): die Store-Update-Erkennung nutzt dieselbe Funktion (W7 erledigt)
- `php -r version_compare('1.6.3-rc.1', '1.6.2', '>') = true (raw comparison 1)`
- `php -r version_compare('1.6.3', '1.6.3-rc.1', '>') = true (raw comparison 1)`
- `testbuild info.xml of the reporter path: https://raw.githubusercontent.com/street1983nk/nextcloud-search/rc/1.6.3-rc.1/testbuild/findling_backend-1.6.3-rc.1-info.xml`
- `testbuild info.xml carries version 1.6.3-rc.1, image-tag 655fe197cc4363e7da2f7c6a7e8000c561f3b31e`
- `occ app_api:app:update findling_backend --info-xml https://raw.githubusercontent.com/street1983nk/nextcloud-search/rc/1.6.3-rc.1/testbuild/findling_backend-1.6.3-rc.1-info.xml`:
  `ExApp findling_backend successfully disabled.` / `ExApp findling_backend update successfully deployed.` / `ExApp findling_backend successfully updated.` / exit 0
- `findling_backend (Array): 1.6.3-rc.1 [enabled]` (app_api:app:list)
- `update 1.6.2 to 1.6.3-rc.1 over the raw URL landed, --force-update not needed`
- `container nc_app_findling_backend runs image ghcr.io/street1983nk/findling_backend:655fe197cc4363e7da2f7c6a7e8000c561f3b31e`
- `the image reference carries the immutable tag :655fe197cc4363e7da2f7c6a7e8000c561f3b31e`
- `the container answered heartbeat with 200 through the HaRP tunnel (its own log)`
- `store shaped info.xml built in this run: version 1.6.3, image-tag 655fe197cc4363e7da2f7c6a7e8000c561f3b31e`
- `occ app_api:app:update findling_backend --info-xml /home/runner/work/_temp/info-163-test.xml`:
  `ExApp findling_backend successfully disabled.` / `ExApp findling_backend update successfully deployed.` / `ExApp findling_backend successfully updated.` / exit 0
- `findling_backend (Array): 1.6.3 [enabled]`, heartbeat wieder 200
- `update 1.6.3-rc.1 to 1.6.3 applied, --force-update not needed`
- `A5 detail: 1.6.2 registered over HaRP, raw URL update to 1.6.3-rc.1 (--force-update not needed), store shaped 1.6.3 applied over it (--force-update not needed)`

Damit ist Pitfall 6 ausgeräumt: die Ordnung 1.6.2 < 1.6.3-rc.1 < 1.6.3 gilt in Servers UND AppAPIs Vergleichsfunktion, und der spätere Store-Release 1.6.3 wird beim Melder als Update angewendet, ohne --force-update.

## Proof-Historie (drei rote Vorläufer, alle Ursachen im Harness, kein Produktcode)

- 42537244567 (2026-11-08 23:52 UTC, rot): die Heartbeat-Sonde fragte nginx `/exapps/...` von außen und bekam 401; Fix eb290016 liest stattdessen das Container-Log.
- 42538879801 (2026-11-09 00:12 UTC, rot): `gh run download -d` gibt es nicht, das Flag heißt `--dir`; Fix ebenfalls eb290016.
- 42551978920 (2026-11-09 02:37 UTC, rot, A5 bereits ok): a6 scheiterte an `core/shipped.json` (verspricht viewer, der nicht im Checkout liegt); Fix ce6bacf8 reduziert alwaysEnabled vor `occ upgrade` auf die Apps des Checkouts.

## Artefakt-Lauf (signiertes Companion-Archiv)

- Lauf-ID: 42537119924 (release.yml, Dispatch auf rc/1.6.3-rc.1 mit create_release=false, grün; Kopf des Laufs = Branch-Commit `47c4ce4e7047d98a2bc4a494146953821f4dbc29`; KEIN Release, KEIN Tag entstanden)
- Artefakt: `store-release` (enthält findling.tar.gz, findling.tar.gz.sig, findling_backend.tar.gz, findling_backend.tar.gz.sig, Quellarchive); nur für angemeldete GitHub-Nutzer; Gesamtgröße laut API 49 312 522 Bytes
- Bytezahl findling.tar.gz: 692 014 (lokal per `wc -c` nach `gh run download`, deckungsgleich mit der Proof-Log-Zeile `archive 692014 bytes, signature 684 bytes`; weit unter dem Deckel 20 971 520)
- "Verified OK": im Proof-Lauf 42565361965 (a6, beide Matrix-Zweige) nach der Signaturprüfung gegen das öffentliche Zertifikat ausgegeben
- SHA-256 des Companion-Archivs findling.tar.gz: `fa9c38745ec79dd21411d17aaa4bb46455987893f4ab13d2f8f3204861c333be` (lokal per sha256sum über das heruntergeladene Artefakt)
- Der Upload-Schritt von release.yml trägt `retention-days: 30`; `expires_at` des Artefakts laut `gh api .../actions/runs/42537119924/artifacts`: `2026-12-08T23:51:31Z`

Aufbewahrung: 30 Tage, Ablauf 2026-12-08

## Installationsweg für mbozem (durch den Proof-Lauf 42565361965 belegt)

1. Companion: Artefakt `store-release` des Laufs 42537119924 angemeldet herunterladen (https://github.com/street1983nk/nextcloud-search/actions/runs/42537119924, Ablauf 2026-12-08), SHA-256 von `findling.tar.gz` gegen `fa9c38745ec79dd21411d17aaa4bb46455987893f4ab13d2f8f3204861c333be` prüfen, nach `custom_apps/findling` (bzw. apps/findling) entpacken (ersetzt die 1.6.2 dort), `occ upgrade`. Belegt in A6: `Updated <findling> to 1.6.3-rc.1`, Migration 001603Date20261108000000 lief, Hinweis-Flag 1.
2. Backend: `occ app_api:app:update findling_backend --info-xml https://raw.githubusercontent.com/street1983nk/nextcloud-search/rc/1.6.3-rc.1/testbuild/findling_backend-1.6.3-rc.1-info.xml` OHNE `--force-update` (A5 belegt: `update 1.6.2 to 1.6.3-rc.1 over the raw URL landed, --force-update not needed`; zieht das unveränderliche Image `:655fe197cc4363e7da2f7c6a7e8000c561f3b31e`, Heartbeat 200).
3. Später zurück auf den Store-Weg: der Store-Release 1.6.3 erscheint als normales Update (A5 belegt: `update 1.6.3-rc.1 to 1.6.3 applied, --force-update not needed`; A6 belegt dieselbe Ordnung für die Companion).
4. Rückweg auf 1.6.2 (falls gewünscht): Companion aus Release v1.6.2 (`gh release download v1.6.2 --pattern findling.tar.gz`) zurück entpacken; Backend mit der info.xml des Tags v1.6.2 per `occ app_api:app:update findling_backend --info-xml <datei> --force-update` (Downgrade braucht force).

Hinweis: Der Kommentar an mbozem mit diesem Weg entsteht in 43-11 und geht nur mit Owner-Freigabe raus.

## Reihenfolge der Schritte (alle erledigt, Freigaben in 43-FREIGABEN.md)

1. Push main (Proof-Workflow + Skript + dieses Dokument), Security-Workflow grün. ERLEDIGT.
2. Push Branch rc/1.6.3-rc.1 (öffentlich sichtbar; docker.yml läuft NICHT, sein push-Trigger gilt nur für main). ERLEDIGT, Kopf 47c4ce4e.
3. Dispatch release.yml auf rc/1.6.3-rc.1 mit create_release=false. ERLEDIGT: Lauf 42537119924 (archive_run_id), kein docker.yml-Dispatch nötig, das Image existiert bereits (siehe Image-Digest).
4. Dispatch rc-version-proof.yml auf main mit rc_ref, archive_run_id, image_sha. ERLEDIGT: grüner Lauf 42565361965 nach drei roten Harness-Vorläufern (siehe Proof-Historie).

## Kommentar an mbozem (gepostet 09.11.2026)

Link: https://github.com/street1983nk/nextcloud-search/issues/25#issuecomment-6732932582
Freigabe: "Ja, so posten" (43-FREIGABEN.md). Gekuerzte Fassung, vom Owner zeichengenau gesehen.

Wortlaut:

Thanks, I'll take you up on that. 1.6.3-rc.1 is ready: the sweep no longer waits for the queue, and the figure is counted per document.

No pre-release this time, the build sits as workflow artifact `store-release` on https://github.com/street1983nk/nextcloud-search/actions/runs/42537119924 (GitHub login needed, expires 2026-12-08). sha256 of findling.tar.gz: `fa9c38745ec79dd21411d17aaa4bb46455987893f4ab13d2f8f3204861c333be`

Install: extract it over `custom_apps/findling`, run `occ upgrade`, then right after:

```
occ app_api:app:update findling_backend --info-xml https://raw.githubusercontent.com/street1983nk/nextcloud-search/rc/1.6.3-rc.1/testbuild/findling_backend-1.6.3-rc.1-info.xml
```

Both apps in one go please, otherwise the counting waits for the companion. First thing after the update is a key backfill (log line `doc key backfill, done=`), the page says "being counted" meanwhile, on your ~190k rows up to maybe 3.5 h. Then you should land around 18 % while the crawl runs, 43,602 of 247,123 from your table, and the first round should log `storage sweep, absent=... gone=5` for the deleted homes. Going back to 1.6.2 works if anything acts up (companion from the v1.6.2 release, backend with the v1.6.2 info.xml plus `--force-update`).

Two quick questions about your setup: does anyone reshare a folder of an SMB mount as a Nextcloud share, or is the same share mounted twice at different mount points? Those count once now. And is the same share configured with two different roots somewhere, like /Daten and /Daten/Projekte? That case still counts twice, I'd fix it before the store release if you have it, otherwise in 1.6.4.

If the number checks out, 1.6.3 goes to the store the normal way. Curious what you end up with.

Rueckmeldung: teilweise (Installation und erste Runde bestätigt, Zahl steht noch aus)

Link: https://github.com/street1983nk/nextcloud-search/issues/25#issuecomment-6735344512 (mbozem, 2026-11-09 08:13 UTC)

- Installation: beide Apps in einem Zug, sha256 von findling.tar.gz stimmt, Backend über die info.xml von rc/1.6.3-rc.1 (Image 655fe197), /status meldet appVersion 1.6.3-rc.1, alle 20 FINDLING_*-Variablen erhalten, Index intakt.
- Sweep wie vorhergesagt: "storage sweep, absent=10 gone=5 deselected=0 stamped=5 removed=5, removed storages [215, 216, 221, 226, 231], waiting [54, 135, 136, 152, 173]".
- Backfill: "doc key backfill, done=5000 missing=474149 unresolved=0", etwa 5000 Schlüssel je Minute, Rest etwa 1,5 h; Seite zeigt perDocumentHint=true. Die gelandete Zahl meldet er nach.
- Frage A1 (Weiterteilung): keine Nutzer- oder Gruppenfreigaben, aber zwei Linkfreigaben von Ordnern auf einem SMB-Mount von //Daten.
- Neuer Befund (nicht gefragt): dieselbe Samba-Freigabe unter zwei Schreibweisen, 192.168.98.246//Daten (42 Speicher) und //daten (5), dazu je ein Daten/daten-Paar auf den Hosts .2 und .231. StorageService::countingKey vergleicht Host und Freigabe zeichengenau (kein strtolower), also zwei Gruppen für einen Baum; im Code bestätigt 09.11.

Wurzel-Frage: ja

Zitat: "Same share with two roots: yes, we have exactly that case" und "please fix it before the store release. `192.168.98.246 //Daten` is configured 25 times with root `/` **and** 17 more times with sub-roots: `/Arbeitssicherheit` (11 user mounts), `/Projekte` (2), and `/Fue`, `/Allgemein`, `/Arbeitsvorbereitung`, `/QM` once each."

Folge nach D-43-15: Stopp vor GO, Tag und Store. Zusatzplan für die Wurzel-Behebung (Dokumentschlüssel über host//share plus Wurzel plus filecache-Pfad, PHP-Gruppierung nach Freigabe, N1/phpOnly je Mitglied umgerechnet) plus die Schreibweisen-Faltung von Host und Freigabe, danach Audit-Nachtrag.
