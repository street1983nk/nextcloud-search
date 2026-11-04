# Phase 41: Issue-Antworten nach dem Store-Release 1.6.2 (Plan 41-12)

Stand: 04.11.2026. Freigabe: Owner "Go für alles" (41-ABNAHME.md) für I2 (#37), I3 (#25), I4 (#44): Claude postet und schließt genau diese drei Issues. Forum-Post I1 bleibt beim Owner. Die Außenhandlungen (Posten, Schließen) hat der Koordinator ausgeführt; dieses Protokoll hält Belege, Wortlaute und Zustände fest.

## Store-Beleg (vor jeder Außenhandlung)

- `https://apps.nextcloud.com/api/v1/apps.json`, abgerufen am 04.11.2026 gegen 19:20 Ortszeit (vor den Posts): id `findling`, Releases `['1.6.2', '1.6.1', ...]`.
- Nachkontrolle 04.11.2026 18:28:43Z (19:28 Ortszeit): `apps.json` id `findling` `['1.6.2', '1.6.1', '1.6.0', '1.5.1']`; `https://apps.nextcloud.com/api/v1/appapi_apps.json` id `findling_backend` `['1.6.2', '1.6.1', '1.6.0', '1.5.1']` (18:28:59Z). Die ExApp steht nicht in `apps.json`, sondern im AppAPI-Katalog `appapi_apps.json`; beide Apps nennen 1.6.2, kein Mischbetrieb.
- Store-Einreichung: Lauf 41875127182 scheiterte mit HTTP 401 "Invalid token" (keine Store-Änderung). Der Owner hat das Secret `APPSTORE_TOKEN` erneuert; Wiederholung 41885026379: release findling v1.6.2 HTTP 201, release findling_backend v1.6.2 HTTP 201.
- Tag `v1.6.2` zeigt auf `ba098b00`; alle sieben Tag-Läufe grün: Release-Archive 41869261561, PHP 41869261491, Python 41869261151, Integration 41869261583, Resilience 41869261405, Multi-arch 41869261338, HaRP 41869261143.
- Image `ghcr.io/street1983nk/findling_backend:1.6.2`: Manifest HTTP 200.

## Verlauf je Issue (seit 04.11.2026)

- **#37 (Backup-Pause):** Abweichung. Das Issue wurde am 04.11.2026 um 15:21:49Z automatisch geschlossen, durch den Push von Commit f88b46e7, dessen Betreffzeile das Schlüsselwort "closes" direkt vor der Nummer 37 enthielt. Keine neue Frage des Melders. Der Wortlaut I2 wurde deshalb im letzten Absatz angepasst und vom Owner freigegeben ("Ja zu 37"); Rest zeichengleich.
- **#25 (Dedup über 100 000, Share-Repräsentant):** keine neue Frage oder neuer Befund seit der Vorlage; I3 gilt zeichengleich.
- **#44 (RTF mit Emoji):** keine neue Frage oder neuer Befund seit der Vorlage; I4 gilt zeichengleich.
- **#33, #43, #45:** bleiben offen. Auf #33 keine Antwort (letzter Kommentar 29.10.2026 13:11:18Z vom Owner, unverändert).

## Endgültige Wortlaute

**I2, Issue #37** (geändert gegenüber I2 nur im letzten Absatz, Owner-Freigabe "Ja zu 37"):

```
1.6.2 is in the app store now (update both apps), with the pause I mentioned. A backup now works like this:

1. `occ findling:pause --wait` (returns once the status says paused), or the switch "Pause indexing" on the admin page, then wait until it says paused
2. Back up the volume `nc_app_findling_backend_data`
3. `occ findling:resume`, or "Resume indexing"

Search keeps working the whole time. The full guide, including restore: https://github.com/street1983nk/nextcloud-search/blob/v1.6.2/docs/backup.en.md

This one got closed a bit early by one of my commits, sorry about that. If the pause doesn't fit your backup setup, just reopen it.
```

Alter letzter Absatz (Vorlage): "I'll close this one. If it doesn't fit your backup setup, just reopen it."

**I3, Issue #25** (zeichengleich zu I3):

```
1.6.2 is in the app store now (update both apps). Both points from your last comment are in: the vector figure is now worked out in the background above 100,000 documents too, so the dedup no longer switches itself off, and the member with the most files seen represents a share group. The first figure can take a reload or two after the update, since the count runs in the background.

I'll close this one. If the page still doesn't show something close to 100% for your four shares, please reopen it.
```

**I4, Issue #44** (zeichengleich zu I4):

```
1.6.2 is in the app store now (update both apps) with the fix. An emoji in an RTF file is now kept as it is, and if the index still can't take a single file, only that file fails (as corrupt) and the rest of the batch goes on.

The 7 files that were written off as repeatedly_stuck come back with `occ findling:index --restart`, as mentioned. I'll close this one, just reopen it if anything stalls again.
```

## Zeichengleichheit (Python-Vergleich)

Scratch-Dateien `i2.md`, `i3.md`, `i4.md` (je mit einem abschließenden Zeilenumbruch, verglichen nach `rstrip('\n')`) gegen den Codeblock in 41-OWNER-VORLAGE.md Block I:

```
I3 i3.md len_vorlage 502 len_datei 502 gleich True
I4 i4.md len_vorlage 404 len_datei 404 gleich True
I2 i2.md len_vorlage 586 len_datei 644 gleich False
- I'll close this one. If it doesn't fit your backup setup, just reopen it.
+ This one got closed a bit early by one of my commits, sorry about that. If the pause doesn't fit your backup setup, just reopen it.
nur letzter Absatz verschieden: True
```

Gegenprobe gepostet gegen Datei (`gh api repos/street1983nk/nextcloud-search/issues/comments/<id> --jq .body`): #37 True, #25 True, #44 True.

## Kommentare und Zustände

| Issue | Kommentar | gepostet (UTC) | Zustand |
|-------|-----------|----------------|---------|
| #37 | https://github.com/street1983nk/nextcloud-search/issues/37#issuecomment-6638602142 | 2026-11-04T18:24:04Z | closed (completed), geschlossen 15:21:48Z durch Commit f88b46e7, nicht wieder geöffnet |
| #25 | https://github.com/street1983nk/nextcloud-search/issues/25#issuecomment-6638501178 | 2026-11-04T18:19:27Z | closed (completed) 18:19:28Z |
| #44 | https://github.com/street1983nk/nextcloud-search/issues/44#issuecomment-6638502123 | 2026-11-04T18:19:29Z | closed (completed) 18:19:30Z |
| #33 | keine Antwort | n/a | open |
| #43 | n/a | n/a | open |
| #45 | n/a | n/a | open (Kandidat v1.7) |

## Lehre

Commit-Nachrichten enthalten nie die GitHub-Schlüsselwörter close/closes/closed, fix/fixes/fixed, resolve/resolves/resolved direkt vor einer Issue-Nummer mit Raute. Stattdessen "issue 37" schreiben. Ein solcher Commit auf main schließt das Issue beim Push, auch wenn die Nachricht nur einen Plan beschreibt.
