# Phase 41: Owner-Abnahme 1.6.2

Grundlage: 41-OWNER-VORLAGE.md (erneuert in 78d326e0, CI-Beleg 9306c068; Blöcke H1, H2, B, C, D, E, G, K, I1 bis I4, F). Eine Runde, gestellt vom Koordinator.

GO: ja
Zitat: Go für alles
Datum: 2026-11-04 16:17
Kanal: Claude-Code-Sitzung des Koordinators, Owner-Antwort auf die Vorlage, an den Ausführenden weitergegeben (Uhrzeit = Übermittlung an den Ausführenden, die Owner-Antwort lag davor am selben Tag)
Frage: Owner-Abnahme Findling 1.6.2: Wie entscheidest du H1, H2, B, C, D, G, K, I und das GO (F)? Vorlage: .planning/phases/41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes/41-OWNER-VORLAGE.md

Das GO deckt Tag v1.6.2 und die Einreichung beider Apps; beides führt der Owner aus.

Lesart laut Koordinator: "Go für alles" heißt jeder Punkt wie empfohlen (a), also auch die Owner-Freigabe aus der Vorlage, dass Claude die Antworten I2 bis I4 nach dem Store-Release postet und die drei Issues schließt.

## Urteil je Punkt

| Punkt | Urteil |
|---|---|
| H1 Hinweis gateway_error (Schlüsselwechsel) | (a) angenommen, Wortlaut en/de/fr wie in der Vorlage |
| H2 sechs Sätze zur Pause | (a) angenommen, H2.1 bis H2.6 wie in der Vorlage |
| B Store-Text 1.6.2 | (a) bestätigt: Namen und Beschreibungen wie 1.6.1, Version, image-tag und Doku-Links auf blob/v1.6.2 |
| C Release-Notiz v1.6.2 | (a) übernommen, sechs Punkte, Full-Changelog-Zeile v1.6.1...v1.6.2 |
| D Audit 1.6.2 | zur Kenntnis (0 offen, audited_head 5dc1aa12) |
| E Umlaut-Audit | zur Kenntnis (0 echte Funde, kein Entscheidungspunkt) |
| G Backup-Doku | (a) angenommen, drei Dateien wie vorgelegt |
| K1 bis K7 | zur Kenntnis |
| I1 Forum-Post | (a) angenommen; der Owner postet im Thread 249775 |
| I2 Antwort #37 | (a) angenommen; Claude postet nach dem Store-Release wörtlich und schließt #37 |
| I3 Antwort #25 | (a) angenommen; Claude postet nach dem Store-Release wörtlich und schließt #25 |
| I4 Antwort #44 | (a) angenommen; Claude postet nach dem Store-Release wörtlich und schließt #44 |
| #33 | keine Antwort, nicht schließen |
| F GO | (a) GO für Tag v1.6.2 und die Store-Einreichung beider Apps; beides führt der Owner aus |

Keine Abweichung, also keine Änderung an Katalogen, info.xml oder Notiz vor dem Tag und kein Nachtrag im Audit. Umgesetzt in Task 3: Abschnitt "# Entwurf v1.6.2 (Gesamttext), abgenommen am 04.11.2026" in docs/store-listing.md mit Gate `scan_full_text_1_6_2`.

## Nach dem Release (Owner-Freigabe vom 04.11.2026)

- Claude postet I2 (#37), I3 (#25), I4 (#44) wörtlich aus 41-OWNER-VORLAGE.md und schließt die drei Issues, erst wenn die App-Store-API (apps.nextcloud.com/api/v1/apps.json) findling 1.6.2 nennt (Plan 41-12).
- #33, #43 und #45 bleiben offen; auf #33 keine Antwort.
- Forum-Post I1 und UI-Sichtung der Pause durch den Owner.

## Tag-Kopf

Tag-Kopf: ba098b00f61cb57dfa8bc127c264e198e4afa313
Läufe: 41856594390 Python gates, 41856594365 HaRP deploy, 41856594734 Integration, 41856594679 Resilience, 41856594507 Multi-arch image, 41856594904 Security scans, 41856594558 OpenSSF Scorecard (alle success, `scripts/ci/head_green.sh` Exit 0 am 04.11.2026); PHP and store metadata gates per Zitat 41792859857 (success auf f12649a213502900f5d8f10e30aeceeea5cfb2e5, "OK (958 tests, 5851 assertions)"), `git diff --stat f12649a2 ba098b00 -- php backend/appinfo .github/workflows/php.yml .github/workflows/release.yml scripts/dev/validate_info_xml.sh` leer.

Der Tag-Kopf ist der letzte Commit außerhalb .planning (`git log -1 --format=%H -- . ':!.planning'`). Code-Diff audited_head 5dc1aa127a495c78ec4ef5272a275c6788c92af0..ba098b00 über backend/src, backend/docker, backend/appinfo, php/appinfo, php/lib, php/js, php/templates, php/l10n, .github/workflows, scripts: leer.

Zwei Läufe brauchten einen zweiten Versuch, beide ohne Bezug zum Code:
- Security scans 41856594904, Versuch 1 cancelled: der Push von f88b46e7 (nur .planning) hat ihn über `concurrency: security-${{ github.ref }}` abgebrochen; Versuch 2 success.
- HaRP deploy 41856594365, Versuch 1 nur im Bein stable34/ubuntu-24.04 rot: Wettlauf im Harness "Store upgrade 2b" Schritt 5 (Queue-Zeile gezählt, bevor das Image v1.5.0 sie nach dem Commit entfernt). Nur das rote Bein neu gestartet, Versuch 2 success. Eintrag für v1.7 in deferred-items.md.

## Vorprüfung Tag (für Plan 41-11, Stand 04.11.2026)

- (a) `git fetch origin`; Tag-Kopf oben nicht leer.
- (b) `git merge-base --is-ancestor ba098b00 origin/main` ja; `git diff --stat ba098b00 origin/main -- . ':!.planning'` leer.
- (c) head_green.sh mit sechs Workflows Exit 0 (oben). "PHP and store metadata gates" hat auf ba098b00 keinen Lauf (Pfadfilter), `head_green.sh` mit diesem Namen endet daher mit "no run"; Ersatzbeleg 41792859857 auf f12649a2 plus leerer Diff der Filterpfade f12649a2..ba098b00 (oben). Zusatz: php.yml startet bei einem Tag-Push `v*.*.*` ohne Pfadfilter, der Tag selbst bekommt also einen eigenen PHP-Lauf; Claude prüft ihn nach dem Tag.
- (d) `git ls-remote --tags origin v1.6.2` leer: noch kein Tag.
- (e) Tag-Links `blob/v1.6.2/...` aus beiden info.xml, docs/store-listing.md und den drei READMEs: 3 Pfade (docs/migrate-from-fulltextsearch.md, .en.md, .fr.md), alle per `git cat-file -e ba098b00:<pfad>` vorhanden; dazu docs/backup.en.md (Link in I2) vorhanden.

## Befehle für den Owner (PowerShell)

Schritt 1, Tag setzen und pushen:

```powershell
cd C:\Users\Student\nextcloud-search
git fetch origin
git tag -a v1.6.2 -m "Findling 1.6.2" ba098b00f61cb57dfa8bc127c264e198e4afa313
git push origin v1.6.2
```

Schritt 2, erst wenn Claude den Lauf "Release archives for the app store" auf v1.6.2 grün meldet:

```powershell
cd C:\Users\Student\nextcloud-search
gh workflow run store-submit.yml --ref main -f tag=v1.6.2
```
