# Phase 43 Plan 14: Antwort in #25 nach dem Store-Release

Stand 2026-11-12 00:49.

## Store-Beleg

- Store submission Lauf 43120250685 (12.11.2026, 23:30 UTC am 11.11.): `release findling v1.6.3: HTTP 201` und `release findling_backend v1.6.3: HTTP 201`.
- `https://apps.nextcloud.com/api/v1/appapi_apps.json`, 23:31 UTC und 23:46 UTC: id findling_backend führt 1.6.3 als neueste Fassung.
- `https://apps.nextcloud.com/api/v1/apps.json`, 23:31, 23:46 und 23:48 UTC: id findling führt noch 1.6.2 (lastModified 2026-11-04, Zwischenspeicher der Liste). Die Seite https://apps.nextcloud.com/apps/findling/releases nennt 1.6.3 bereits (23:31 UTC).
- Abweichung vom Plan, offen benannt: Der Plan verlangt, dass die API 1.6.3 für beide IDs nennt, sonst Stopp. Claude hat dem Owner den Stand vorgelegt und empfohlen zu warten; der Owner hat das Posten ausdrücklich angewiesen ("Poste die Antwort auf 25"), nachdem er selbst festgestellt hatte "1.6.3 ist im Store". Die Gegenprobe der API für findling wird nachgetragen.

## Verlauf seit dem Testbuild-Kommentar

- street1983nk, 2026-11-09 08:18 UTC: Dank für die Daten, Unterwurzeln und Schreibweise Daten/daten werden vor dem Store-Release behoben.
- mbozem, 2026-11-09 17:10 UTC: Landebericht zu rc.1, Backfill vollständig (done=3099, missing=0, unresolved=54), documents=42156, indexable=251758, 16 Prozent, 7,5 Stunden für rund 497.000 Zeilen.
- street1983nk, 2026-11-09 17:25 UTC: kein rc.2, 1.6.3 geht in den Store, sobald die Zusammenführung drin und geprüft ist, Erwartung rund 18 Prozent.
- Danach kein weiterer Kommentar bis zum Posten (18 Kommentare, letzter vom 09.11.).

I2 deckt den Verlauf: ja

## Wortlaut (abgenommen in Runde 2, I2 mit der gemessenen Dauer)

```
1.6.3 is in the app store now, update both apps together. Thanks again for the rc.1 test and the two topology posts, the fold for sub-roots and spelling is built on them.

Coming from rc.1 (or straight from 1.6.2) the document keys are rebuilt once, so the page says "being counted" again. On an instance your size that takes hours, about as long as the rc.1 backfill took (7.5 h on yours), and the search works normally meanwhile. After that you should land around 18 %.

Could you confirm the figure on the store build? I'll leave this one open until then.
```

## Gepostet

Kommentar: https://github.com/street1983nk/nextcloud-search/issues/25#issuecomment-6810021534
Zustand: OPEN

Das Issue wird von uns nicht geschlossen. Es bleibt offen, bis mbozem die Zahl auf dem Store-Stand bestätigt; danach den Owner fragen, ob es geschlossen wird.

## Offen

- Gegenprobe apps.json für findling: nachgetragen, 2026-11-11T23:52Z führt `api/v1/apps.json` für id findling 1.6.3 und `api/v1/appapi_apps.json` für id findling_backend 1.6.3. Der Kommentar in #25 trägt den Zeitstempel 2026-11-11T23:48:34Z, er ging also wenige Minuten vor dem Umspringen der Liste hinaus.
- Remote-Branch rc/1.6.3-rc.1: keine Entscheidung des Owners, bleibt bestehen.
- Push dieser Zustandspflege: eigene Freigabe.
