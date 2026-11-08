# 43-TESTBUILD: Testbuild 1.6.3-rc.1 für mbozem (D-43-10, D-43-13)

**Stand:** 2026-11-08, lokale Vorbereitung (Plan 43-10 Task 1). Alle CI-abhängigen Felder sind als AUSSTEHEND markiert und werden in Task 3 nach den Owner-Freigaben (Task 2) gefüllt.

## Zweck

mbozem (Issue #25) prüft seine Abdeckungszahl vor der Store-Einreichung 1.6.3 (erwartet etwa 18 % bei laufendem Crawl). Nach D-43-13 gibt es KEIN öffentliches GitHub-Pre-Release: der Testbuild besteht aus einem signierten Companion-Archiv als Workflow-Artefakt (nur für angemeldete GitHub-Nutzer, läuft ab), einem unveränderlichen Backend-Image `:<sha>` und einer Test-info.xml im Branch. Vorher weist der Proof-Workflow nach, dass die Versionsordnung hält (A5/A6, Pitfall 6): die spätere Store-1.6.3 muss bei ihm als Update erscheinen.

## Branch rc/1.6.3-rc.1 (lokal, NIE nach main mergen)

- Branch-Commit: `f6c5a6ce0e5378ce0facacac155c919d64f019a2` (`chore(43-10): test build 1.6.3-rc.1 for the reporter`)
- Basis: `audited_head` = `37b518d6754a4a8a8593dc537a13b27644caf986` (43-AUDIT.md)
- Diff-Beleg: `git diff 37b518d6..f6c5a6ce --name-only` zeigt genau `backend/appinfo/info.xml`, `php/appinfo/info.xml`, `testbuild/findling_backend-1.6.3-rc.1-info.xml`; der Inhalts-Diff der beiden info.xml besteht nur aus den drei Versionszeilen (`<version>` zweimal, `<image-tag>` einmal, je 1.6.3 zu 1.6.3-rc.1). Lockstep bleibt grün (version == image-tag == 1.6.3-rc.1).
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

- Lauf-ID: AUSSTEHEND (Dispatch `gh workflow run rc-version-proof.yml --ref main -f rc_ref=rc/1.6.3-rc.1 -f archive_run_id=<id> -f image_sha=655fe197cc4363e7da2f7c6a7e8000c561f3b31e`, erst nach Owner-Freigabe "Dispatch 43-10 proof")
- A5: AUSSTEHEND (wird wörtlich aus der Job-Summary übernommen)
- A6: AUSSTEHEND (wird wörtlich aus der Job-Summary übernommen)
- Store-Erkennung AppAPI: AUSSTEHEND (Zeile `Store-Erkennung AppAPI: <datei>:<zeile> nutzt version_compare` wörtlich aus dem Proof-Log, W7)
- Fundstellen der Vergleichsfunktionen (Server und AppAPI, Datei:Zeile): AUSSTEHEND

## Artefakt-Lauf (signiertes Companion-Archiv)

- Lauf-ID: AUSSTEHEND (Dispatch `gh workflow run release.yml --ref rc/1.6.3-rc.1 -f create_release=false`, erst nach Owner-Freigabe "Dispatch 43-10 release"; der Guard von release.yml erlaubt den Dispatch, es entsteht KEIN Release und KEIN Tag)
- Artefakt: `store-release` (enthält findling.tar.gz, findling.tar.gz.sig, findling_backend.tar.gz, findling_backend.tar.gz.sig, Quellarchive); nur für angemeldete GitHub-Nutzer
- Bytezahl findling.tar.gz: AUSSTEHEND (muss < 20 971 520 sein)
- "Verified OK": AUSSTEHEND (Signaturprüfung des Proof-Laufs, zusätzlich im Artefakt-Lauf selbst enthalten)
- SHA-256 des Companion-Archivs: AUSSTEHEND
- Aufbewahrung/Ablauf: AUSSTEHEND; der Upload-Schritt von release.yml trägt `retention-days: 30` (Zeile 540), erwartete Zeile nach dem Lauf: `Aufbewahrung: 30 Tage, Ablauf <JJJJ-MM-TT>` (Ablaufdatum aus `gh api repos/street1983nk/nextcloud-search/actions/runs/<id>/artifacts`, Feld `expires_at`)

## Installationsweg für mbozem (Entwurf, endgültig nach dem Proof-Lauf)

1. Companion: Artefakt `store-release` des Artefakt-Laufs angemeldet herunterladen, `findling.tar.gz` nach `custom_apps/findling` (bzw. apps/findling) entpacken (vorher die 1.6.2 dort ersetzen), `occ upgrade`.
2. Backend: `occ app_api:app:update findling_backend --info-xml https://raw.githubusercontent.com/street1983nk/nextcloud-search/rc/1.6.3-rc.1/testbuild/findling_backend-1.6.3-rc.1-info.xml` (mit oder ohne `--force-update`, je nach A5-Ergebnis; zieht das unveränderliche Image `:655fe197cc4363e7da2f7c6a7e8000c561f3b31e`).
3. Rückweg auf 1.6.2: Companion aus Release v1.6.2 (`gh release download v1.6.2 --pattern findling.tar.gz`) zurück entpacken; Backend mit der info.xml des Tags v1.6.2 per `occ app_api:app:update findling_backend --info-xml <datei> --force-update` (Downgrade braucht force, A5-Log zeigt das Verhalten).

Hinweis: Der Kommentar an mbozem mit diesem Weg entsteht in 43-11 und geht nur mit Owner-Freigabe raus.

## Reihenfolge der ausstehenden Schritte (jeweils eigene Freigabe, Task 2)

1. Push main (Proof-Workflow + Skript + dieses Dokument), Security-Workflow grün abwarten.
2. Push Branch rc/1.6.3-rc.1 (öffentlich sichtbar; docker.yml läuft NICHT, sein push-Trigger gilt nur für main; die Testsuiten-Workflows laufen auf dem Branch und sollen grün sein, keine Versions-Pins in den Tests).
3. Dispatch release.yml auf rc/1.6.3-rc.1 mit create_release=false (liefert `archive_run_id` und das signierte Archiv; kein docker.yml-Dispatch nötig, das Image existiert bereits, siehe Image-Digest).
4. Dispatch rc-version-proof.yml auf main mit rc_ref, archive_run_id, image_sha.
