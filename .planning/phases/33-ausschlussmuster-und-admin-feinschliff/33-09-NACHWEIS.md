# Phase 33 Plan 09: Nachweis EXCL-02 auf der Dev-Instanz 8090

**Stand: angehalten nach Task 1 (Weg A) wegen Befund L-33-09-01 (siehe unten).**
Task 1 ist bis auf den Rückweg gefahren, Task 2 (Weg C) ist noch nicht begonnen.
Die Instanz steht bewusst im Zustand nach Weg A (Abschnitt "Zustand beim Anhalten"),
damit die Fortsetzung dort ansetzen kann.

## Stand

| Punkt | Wert |
|---|---|
| Datum | 14.10.2026, Beginn 10:21 Ortszeit (08:21Z) |
| Commit | `a3df7c4d` (origin/main, Stand nach 33-08) |
| Instanz | `findling-nextcloud`, http://localhost:8090, Nextcloud 34.0.3, `php/` als Bind-Mount |
| Apps | findling 1.4.2 (`php/` von main), findling_backend 1.4.2 als Host-Prozess (pid 987667, gestartet 04:46), app_api 34.0.0 |
| `occ status` | `needsDbUpgrade: false`, `maintenance: false`, kein `occ upgrade` nötig |
| Kanarie | `term=findling-canary`: 1 Treffer; Statusroute über den AppAPI-Proxy HTTP 200 (`appVersion` 1.4.2) |
| Regeln vorher | `exclusions` = `["Archiv"]` (hex `5B22417263686976225D`), `exclusion_patterns` fehlt (`config:app:get` Exit 1) |
| Abgleich vorher | letztes Ende 13.10.2026 12:56:05 Ortszeit (state.db, Tabelle `reconcile`, alle fünf Mounts), kein offener Lauf |
| Suche | OCS `/ocs/v2.php/search/providers/findling/search?term=<wort>` als testuser mit App-Passwort `nachweis3309` (`occ user:auth-tokens:add`), Header `OCS-APIRequest: true` |
| SQL | Lesend per PDO auf `/var/www/html/data/nextcloud.db` (SQLite) im Container |
| Browser | Playwright 1.63 (Node, Chromium headless), Viewport 1600 x 1000, Seitensprache de; vor jeder Sichtprobe alle Findling-Skripte per `fetch(url,{cache:'reload'})` neu geladen, dann Seite neu geladen |
| Bildschirmfotos und Rohprotokoll | Scratch `C:\Users\Student\AppData\Local\Temp\claude\C--Users-Student\f6488641-8ddf-4bad-8748-b99f3aecda70\scratchpad\nachweis3309\` (`protokoll.log` mit Zeitstempel je Erwartung und Ergebnis) |

Die Erwartung jedes Schritts steht im Rohprotokoll mit Zeitstempel VOR dem Ergebnis
(`ERWARTUNG:`-Zeilen); die Tabellen unten übernehmen sie.

## Saat Weg A (testuser, WebDAV)

Wörter ohne deutsche Wortbestandteile, damit die Kompositazerlegung keine Fremdtreffer erzeugt.
Vorher je Wort 0 Treffer (Gegenprobe der Saat), Kanarie 1.

| Kürzel | Pfad | Wort | Datei-ID |
|---|---|---|---|
| A | `/Abnahme33/Vortrag.key/Data/notiz.txt` | zyqanta | 2991 |
| B (Kontrolle) | `/Abnahme33/Kontrolle/notiz.txt` | zyqbelo | 2992 |
| C (Gegenfall) | `/Abnahme33/Vortrag.keynote/notiz.txt` | zyqcomu | 2993 |
| D | `/node_modules/x.txt` | zyqdura | 2994 |
| Bild unter Bundle | `/Abnahme33/Vortrag.key/Data/bild.png` (24 x 24) | , | 2995 |
| Bild Kontrolle | `/Abnahme33/Kontrolle/bild.png` (24 x 24) | , | 2996 |
| E | `/Archiv/alt.txt` (Ordner `Archiv` bestand schon, MKCOL 405) | zyqepsi | 2997 |
| F (später) | `/Abnahme33/Vortrag.key/Data/neu.txt` | zyqfumo | 2998 |

Alle PUT 201. Queue direkt nach dem Hochladen: Zeilen für 2991 bis 2996, **keine für 2997**
(Präfix `Archiv` wirkt schon im Listener). Abholung 08:23:38Z: `claimed=6 indexed=4 skipped=2 requeued=2`.

## Task 1: Weg A über die Seite

| Nr. | Schritt | Erwartung (vorher notiert) | Ergebnis | Beleg |
|---|---|---|---|---|
| A1 | Positivkontrolle Suche | A, B, C, D je 1; E 0 | A 1, B 1, C 1, D 1, E 0 | `protokoll.log` 10:25:56 |
| A2 | Positivkontrolle Urteile | 2995 und 2996 `skipped(image_not_ocrable)` | beide Zeilen da (`updated_at` 08:23:42) | SQL `findling_file_state` |
| A3 | Diagnose vorher | A `indexed`, E `excluded` | 2991: `indexed`, "The content of this file is searchable."; 2997: `skipped` / `excluded` / "Excluded by a rule" | `occ findling:diagnose` |
| A4 | Seite vorher | Kachel und Fehlerliste notieren | Kachel "Excluded by a rule" 2, Fehlerliste `image_not_ocrable` 10 | `seite`-Lauf 10:26:12 |
| A5 | Muster `*.key` und `*/node_modules/*` auf der Seite eintragen, speichern | Bestätigung ohne Zahl, Muster im code-Element, gespeichert | Bestätigung: "Indexierte Inhalte entfernen? Der Ausschluss von *.key, */node_modules/* entfernt außerdem die bereits indexierten Dokumente, auf die diese Muster passen, aus dem Index. ..." (Ordnerzeile verborgen, keine Zahl), code-Element `*.key, */node_modules/*`; Rückmeldung "Regeln gespeichert. Der nächste Lauf übernimmt sie."; Anfragen genau eine Vorschau (GET) und ein POST; keine Konsolenfehler | `a1-bestaetigung-ohne-zahl.png`, `a2-gespeichert.png` |
| A6 | appconfig und Jobliste | Muster gespeichert, Präfix unverändert, genau ein ExclusionSweepJob, kein SubtreeExpandJob | `exclusion_patterns` = `["*.key","*\/node_modules\/*"]`, `exclusions` = `["Archiv"]`; genau ein ExclusionSweepJob (`storage 0, root 0, cursor 0`, Fingerabdruck `35b16b2a...`), kein SubtreeExpandJob | `occ background-job:list` |
| A7 | cron.php bis der Kehrjob weg ist | Löschzeilen für A, D und das Bild unter dem Bundle; Urteil 2995 weg, 2996 bleibt | nach dem ersten Lauf (10:26:28) kein ExclusionSweepJob mehr; Queue: `delete` für 2991, 2994, 2995 **und 2997** (siehe Hinweis H1); `findling_file_state`: nur noch 2996 | SQL |
| A8 | Poller abwarten | Löschaufträge abgeholt | `DELETE /queues/documents` 08:27:28Z, Queue für 2991 bis 2999 leer; Container `docs` 469 + 4 - 2 = 471 | Access-Log, Statusroute |
| A9 | Nachher Suche | A 0, D 0, B 1, C 1, E 0 | A 0, D 0, B 1, C 1, E 0 | `protokoll.log` 10:27:53 |
| A10 | Diagnose nachher | A und D "Excluded by a rule", C weiter `indexed` | 2991 und 2994: `skipped` / `excluded` / "Excluded by a rule", Abhilfe nennt beide Listen; 2993: `indexed` | `occ findling:diagnose` |
| A11 | Fehlerliste (B2) | Bild-Urteil unter `Vortrag.key` weg, Kontrollbild bleibt | `image_not_ocrable` 10 auf 9; Beispielpfade der Liste: nur `Abnahme33/Kontrolle/bild.png (ID 2996)`, kein Eintrag für 2995 | `a3-fehlerliste.png`, SQL |
| A12 | Recount (Scan durch das Speichern als veraltet markiert, cron.php) | `excluded` von 2 auf 6 (3 Saatdateien unter Mustern plus E unter `Archiv`); Kachel 6 | ScanRecountJob lief im Lauf von A7 (08:26:29Z), StorageCrawlJob nach einem weiteren Lauf weg; Storage 3: `files_seen` 373 auf 380 (+7 Saat), `excluded` 2 auf 6; Kachel "Excluded by a rule" 6 | `a3-kacheln.png`, SQL `findling_scan_stats` |
| A13 | Neue Datei F unter dem Bundle | keine Queue-Zeile, F 0 Treffer; Kontrolle B weiter 1 | PUT 201, ID 2998, **keine** Queue-Zeile (Queue gesamt 0; Positivkontrolle derselben Abfrage: bei der Saat bekam 2992 sofort Zeile 9473), F 0, B 1 | SQL, Suche |
| A14 | Bestand Präfix | `exclusions` byte-gleich `["Archiv"]`, E 0, Diagnose E "Excluded by a rule" | hex `5B22417263686976225D` vor und nach den Ablehnungen gleich (`cmp`); E 0; 2997 `excluded` | `appconfig_vor_ablehnung.txt`, `appconfig_nach_ablehnung.txt` |

Dauer Weg A bis zum Verschwinden: Speichern 10:26:2x, Kehrjob 10:26:28 (erster cron.php),
Abholung der Löschaufträge 10:27:28 (nächster Poll des Backends, Takt bis 120 s), Suche A 0 um
10:27:53. Also rund eine Minute, bestimmt durch cron und den Poll-Takt.

**Hinweis H1 (kein Befund):** Der Kehrjob reiht auch für `Archiv/alt.txt` (2997) eine Löschzeile
ein, obwohl die Datei nie indexiert war: Er fragt `isExcluded()` über beide Listen. Die Löschung
ist idempotent, die Datei bleibt 0 Treffer. Entspricht dem Plan "für jede Datei, auf die
`isExcluded` antwortet".

### Ablehnungen über die Seite

Erwartung (10:29:06): je Code der Satz am Musterfeld, keine Bestätigung, nichts gespeichert;
61 Zeichen und 33 Muster lokal abgelehnt, der Server antwortet 400 mit `too_long` bzw. `too_many`;
appconfig danach byte-gleich.

| Nr. | Eingabe | Satz am Musterfeld (de, zeichengleich 33-WORTLAUT.md) | Bestätigung | Bild |
|---|---|---|---|---|
| R1 | `[0-9]*` | "Eckige und geschweifte Klammern sowie der Backslash sind nicht erlaubt. Nur * und ? sind Platzhalter." | nein | `r01-ablehnung.png` |
| R2 | `**/x` | "Einen einfachen * verwenden: Er gilt bereits über Ordner hinweg." | nein | `r02-ablehnung.png` |
| R3 | `!foo` | "Ein führendes ! wird nicht unterstützt. Muster schließen nur aus." | nein | `r03-ablehnung.png` |
| R4 | `*` | "Ein Muster braucht mindestens ein Zeichen außer * und ?, sonst schlösse es alles aus." | nein | `r04-ablehnung.png` |
| R5 | 61 Zeichen (`Ordner/` + 52 x `a` + `/*`) | Feld hat `maxlength` 60, `fill` kommt mit 60 Zeichen an; mit 61 Zeichen per Skript ins Feld gesetzt: "Ein Muster darf höchstens 60 Zeichen lang sein.", keine Zeile angelegt | , | `r05-ablehnung-61-zeichen.png` |
| R6 | 33 Muster | 30 Zeilen ergänzt bis 32, das 33. Hinzufügen: "Höchstens 32 Muster sind erlaubt." | , | `r06-ablehnung-33-muster.png` |
| R7 | `node_modules` | "Dieser Eintrag enthält weder * noch ?. Ihn stattdessen unter "Ausgeschlossene Ordner" eintragen." | nein | `r07-ablehnung.png` |

Über jedem Satz die Kopfzeile "Die Regeln wurden nicht gespeichert. Es hat sich nichts geändert."
R1 bis R4 und R7 lehnte schon die Vorschau ab (HTTP 400), die Seite schickte keinen POST.
Am Formular vorbei (gleiche Sitzung, gleiches Token, POST `/apps/findling/admin/rules`):
61 Zeichen ergibt `400 {"exclusionPatterns":["too_long"],"saved":false}`, 33 Muster
`400 {"exclusionPatterns":["too_many"],"saved":false}`. appconfig danach byte-gleich (`cmp`),
keine neue Zeile ExclusionSweepJob oder SubtreeExpandJob.

### Logprobe

Positivkontrolle: Marker `markerzyq3309` als Login-Name (PROPFIND, 401) und als Pfad am
Backend-Port (401). Gefunden: `nextcloud.log` 1, `.dev/exapp.log` 1.

| Log | Saatwörter | Ordnernamen (`Abnahme33`, `Vortrag.key`, `keynote`, `Kontrolle`, Dateinamen) | Muster |
|---|---|---|---|
| `.dev/exapp.log` (Host-Backend, 110 Zeilen) | 0 | 0 | 0 |
| `nextcloud.log` ab 08:20Z (16 Zeilen) | 0 | 0 | **10 Zeilen mit `*.key` und `node_modules`, siehe Befund** |

## Befund L-33-09-01: Präfixe und Muster stehen bei abgelehnter Vorschau im nextcloud.log

**Beobachtung.** Jede vom Server abgelehnte Vorschau schreibt zwei Warnungen
(`ExclusionService.php:1305-1310` "refused an exclusion entry that is not a usable folder path"
und `SettingsController.php:251` "refused to preview a list of exclusions that did not validate").
Nachricht und `data` tragen nur Zähler. Nextcloud setzt aber in jede Logzeile das Kernfeld `url`
der Anfrage, und die Vorschau ist eine GET-Route (`SettingsController.php:243`) mit allen Listen
in der Query. Damit stehen in `nextcloud.log` sämtliche Einträge beider Listen im Klartext, auch
die gültigen:

```
{"level":2,"time":"2026-10-14T08:29:13+00:00","user":"admin","app":"findling","method":"GET",
 "url":"/apps/findling/admin/rules/preview?exclusions%5B%5D=Archiv&exclusionPatterns%5B%5D=*.key&exclusionPatterns%5B%5D=*%2Fnode_modules%2F*&exclusionPatterns%5B%5D=%5B0-9%5D*",
 "message":"Findling: refused to preview a list of exclusions that did not validate",
 "data":{"app":"findling","exclusions":"0","exclusionPatterns":"1"}}
```

Zehn solche Zeilen für R1 bis R4 und R7 (je zwei). Die zwei POST-Ablehnungen (61 Zeichen,
33 Muster) tragen keine Werte (`url` ohne Query). Das Access-Log des Containers enthält dieselben
Query-Strings (6 Zeilen mit `exclusionPatterns%5B%5D` in den letzten 10 Minuten).

**Seit wann.** In v1.4.2 ist die Vorschau dieselbe GET-Route mit derselben Warnung
(`git show v1.4.2:php/lib/Controller/SettingsController.php`, Zeilen 233 bis 239), also stehen
abgelehnte Ordnerlisten schon seit 1.4.2 so im Log. Phase 33 (Plan 33-05) hat die Musterliste in
dieselbe Query gelegt.

**Warum Befund.** must_have des Plans "the log carries counters only" und T-33-28 (keine Ordner
oder Muster im Log); die Docblocks von `reject()` sagen ausdrücklich, das Log trage "counters and
codes and nothing somebody else wrote". Die Wert-Abwesenheitsprobe in 33-05 prüfte Nachricht und
Kontext, nicht das Kernfeld `url`.

**Nebenbefund.** Eine abgelehnte Musterliste loggt "refused an exclusion entry that is not a usable
folder path", obwohl es kein Ordnerpfad war.

**Nicht gefixt** (Auftrag: Produktfehler nicht still fixen, wenn der Fix Verhalten ändert). Ein Fix
ändert entweder die Route (Vorschau als POST mit Body, wie das Speichern) oder das Logverhalten.
Optionen für den Owner:

1. Vorschau auf POST umstellen (Werte nur im Body; beseitigt auch das Access-Log), Seite und PHPUnit nachziehen.
2. Ablehnung in der Vorschau nicht mehr als Warnung loggen (die Antwort trägt die Codes schon), Speichern loggt weiter; Access-Log bleibt.
3. Als bekannt hinnehmen und in docs/admin-page.md vermerken (Wert ist Admin-Konfiguration, Log ist Admin-Log).

## Zustand beim Anhalten (für die Fortsetzung)

- `exclusions` = `["Archiv"]`, `exclusion_patterns` = `["*.key","*\/node_modules\/*"]` (Weg A aktiv).
- Saat Weg A liegt: 2991 bis 2998 wie oben; A, D, Bild 2995 aus dem Index, F nie eingereiht.
- Keine Findling-Jobs offen außer dem regulären ScanRecountJob.
- Host-Backend unverändert (pid 987667, Standardtakt des Abgleichs 24 h / Stunde 2; nächster Abgleich frühestens 15.10. 02:00).
- App-Passwort `nachweis3309` für testuser besteht noch (Token im Scratch `testuser.tok`), wird beim Aufräumen gelöscht.
- Offen aus Task 1: Rückweg (Muster auf der Seite entfernen, `occ findling:index --restart`, A wieder 1).
- Offen: Task 2 (Weg C mit Gegenprobe), Aufräumen, Endzustand.
