# Phase 33 Plan 09: Nachweis EXCL-02 auf der Dev-Instanz 8090

**Stand:** Task 1 (Weg A) ergab um 10:31 den Befund L-33-09-01, der Lauf hielt an.
Owner-Entscheid vom 14.10.2026: Option 1, die Vorschau geht per POST. Fix `fe813988`
(Abschnitt "Fix L-33-09-01"), danach Rückweg von Task 1, Task 2 (Weg C) und Aufräumen.

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

**Zunächst nicht gefixt** (Auftrag: Produktfehler nicht still fixen, wenn der Fix Verhalten ändert),
Lauf um 10:31 angehalten und mit drei Optionen gemeldet (POST, keine Warnung in der Vorschau,
hinnehmen). **Owner-Entscheid 14.10.2026: Option 1**, die Vorschau geht per POST.

## Fix L-33-09-01 (Commit `fe813988`)

- `SettingsController::previewRules()`: Route `POST /admin/rules/preview` statt GET, Docblocks
  von Klasse und Methode nennen den Grund; Request-Token wird wie bei jeder Admin-Route geprüft
  (kein Attribut, das die Prüfung aufhebt; Gate `test_php_trust_boundary.py` unverändert grün).
- `php/js/admin.js`: `preview(exclusions, patterns)` schickt beide Listen als JSON im Body,
  mit `requesttoken` und `Content-Type: application/json`, ohne Query.
- `ExclusionService::reject()`: Satz je Liste, Ordner unverändert wie 1.4.2 ("refused an
  exclusion entry that is not a usable folder path"), Muster neu "refused an exclusion pattern
  that is not a usable pattern"; Kontext weiter nur der Zähler.
- PHPUnit (`SettingsControllerTest.php`): Verb und URL aus dem Routenattribut, gleiches Verb wie
  das Speichern, kein Attribut, das CSRF oder Admin aufhebt; Logsatz je Liste ohne Werte.
  CI: 791 Tests, 2976 Assertions (vorher 789).
- Gate `scan_rules_routes` in `test_admin_ui_contract.py` mit Selbsttest: jede Regelroute ist
  POST, die Vorschau hat `method: 'POST'` und einen Body und baut keine Adresse mit
  `URLSearchParams` oder `'?'`; Anti-Leere: beide Regelrouten werden gesehen. Gegenprobe mit
  Controller und Skript aus `git show HEAD:` (Stand vor dem Fix): 2 rot (Gate mit 6 Befunden,
  Body-Prüfung im Mustertest), Selbsttest grün; eigene Kopien zurück, `cmp` gleich.
- PHP-Baumhash `1761f54c...` auf `6b4a5994dd005fe3bc4c19cc6f959517a681e296db4d785f7d18c8099a59d52c`,
  103 Dateien; Gegenprobe per Shell (`find`, `LC_ALL=C sort`, Wagenrücklauf entfernt, `sha256sum`) gleich.
- Gates lokal: pytest 5682 passed, 159 skipped (16:48 min), ruff, ruff format (222), pyright
  0 Fehler, vulture leer, reuse 2730/2730, `node --check`, `php -l` (php:8.3-cli) je Datei.
- CI `fe813988`, alle mit `gh run watch --exit-status` grün: PHP and store metadata gates
  38542497810, Python gates 38542497613, Security scans 38542497846, OpenSSF Scorecard
  38542497926, Resilience 38542497538, Multi-arch image 38542497556, Integration 38542497748,
  HaRP deploy 38542497788.

### Nachweis des Fixes auf 8090

Positivkontrolle: `befund-log-url.txt` (alter Stand, 10 Zeilen mit allen Regelwerten im Feld `url`).

| Schritt | Erwartung (vorher notiert, 11:04:25) | Ergebnis |
|---|---|---|
| Ausgeliefertes Skript | nach `fetch(url,{cache:'reload'})` mit POST-Vorschau | ja (Body-Zeile im ausgelieferten `admin.js`) |
| Erster Versuch 11:04 | Vorschau POST 400 mit Satz | **POST 405**: Nextcloud hält die Routen der App im APCu-Cache, der Bind-Mount ändert keine App-Version. Container `findling-nextcloud` neu gestartet (11:05), danach 400 mit Codes. Umgebung, kein Befund |
| Abgelehnte Vorschau `[0-9]*` | Satz am Musterfeld, Anfrage POST mit Body | Satz "Eckige und geschweifte Klammern ...", `POST /apps/findling/admin/rules/preview` mit Body `{"exclusions":["Archiv"],"exclusionPatterns":["*.key","*/node_modules/*","[0-9]*"]}`; Bild `f1-ablehnung-nach-fix.png` |
| Gültige Vorschau `*.fixprobe-nichts` | Bestätigung wie bisher | Bestätigung mit dem Muster im code-Element, abgebrochen; `f2-bestaetigung-nach-fix.png` |
| Alte GET-Adresse | abgelehnt | `GET .../preview?exclusions[]=Archiv` 405 |
| nextcloud.log | vorher 2523 Zeilen; neue Zeilen ohne Regelwerte | 4 neue Zeilen (zwei Ablehnungen), `url` = `/apps/findling/admin/rules/preview` ohne Query; grep `Archiv`, `*.key`, `node_modules`, `[0-9]`, `fixprobe`, `exclusionPatterns%5B` je 0; Satz der Musterablehnung jetzt "refused an exclusion pattern that is not a usable pattern" |
| Access-Log ab 09:05Z | keine Regelwerte | 473 Zeilen, `exclusionPatterns`, `*.key`, `node_modules`, `fixprobe` je 0; `Archiv` 1, das ist die eigene GET-Gegenprobe mit curl (405) |

## Rückweg Task 1

| Schritt | Erwartung | Ergebnis |
|---|---|---|
| Muster auf der Seite entfernen, speichern (11:27:56) | keine Bestätigung, `exclusion_patterns` `[]`, `exclusions` `["Archiv"]`, kein Kehrjob | so; nur ein POST `/admin/rules`; `a4-rueckweg-gespeichert.png` |
| `occ findling:index --restart -n`, cron.php bis kein Crawl-Job | 480 Queue-Zeilen, Abarbeitung | Crawl nach 6 cron-Läufen fertig (11:28:31), Queue leer 11:35:29 |
| Suche | A 1, D 1, F 1 (F war nie eingereiht), E 0 | A 1, B 1, C 1, D 1, E 0, F 1; Urteile 2995 und 2996 wieder `image_not_ocrable` |

Dauer des Rückwegs über `--restart`: rund 7,5 Minuten (ganzer Bestand neu eingereiht).

## Task 2: Weg C über den Abgleich

### Saat Weg C (Neustart R0 vorher)

Neustart R0 um 11:39:31: Hauptbaum, `FINDLING_OCR_ENABLED=false`, Abgleich auf Standard (24 h,
Stunde 2, nicht fällig). OCR aus, damit das PDF ohne Textschicht mit `skipped(no_text_layer)`
stehen bleibt (der Host-Prozess hat kein Tesseract, mit OCR an würde daraus `failed(ocr_unavailable)`).

| Kürzel | Pfad | Wort | Datei-ID | Urteil nach der Indexierung |
|---|---|---|---|---|
| G | `/Abnahme33c/Praesentation.key/Data/notiz.txt` | zyqgira | 3004 | indexed |
| H | `/Abnahme33c/Altordner/notiz.txt` | zyqhoxu | 3005 | indexed |
| K (Kontrolle) | `/Abnahme33c/Kontrolle/notiz.txt` | zyqkapo | 3006 | indexed |
| Bild unter Bundle | `/Abnahme33c/Praesentation.key/Data/bild.png` | , | 3007 | `skipped(no_text_layer)` |
| Bild Kontrolle | `/Abnahme33c/Kontrolle/bild.png` | , | 3008 | `skipped(no_text_layer)` |
| PDF ohne Textschicht | `/Abnahme33c/Praesentation.key/scan.pdf` | , | 3009 | `skipped(no_text_layer)` |

Mit OCR aus bekommen auch die Bilder `no_text_layer` (sie gehen den Weg eines Scans), nicht
`image_not_ocrable`; damit liegen drei `no_text_layer`-Zeilen vor (PE-9). Indexiert 11:40:13,
G, H, K je 1 Treffer. `findling_file_state` vorher: 3007, 3008, 3009 (`fs_c_vorher.txt`).

### Regeln am Formular vorbei (11:45:27)

```
occ config:app:set findling exclusion_patterns --value='["*.key"]' --type=array
occ config:app:set findling exclusions --value='["Archiv","Abnahme33c/Altordner"]' --type=array
```

Erwartung: kein ExclusionSweepJob, kein SubtreeExpandJob, Queue leer, G und H weiter 1.
Ergebnis: Jobs vorher 0, nachher 0, auch nach einem cron.php 0; Queue 0; G 1, H 1, K 1.
Die Diagnose von G sagt sofort `excluded` (live), der Index hält G aber weiter (B1).

### Fälligkeit und Läufe des Abgleichs

Regel aus `reconcile.py` (`_is_due`, Zeilen 793 bis 822): kein offener Lauf, seit dem letzten
Ende mindestens `FINDLING_RECONCILE_MIN_INTERVAL_HOURS`, und die Stunde der Hostuhr gleich
`FINDLING_RECONCILE_HOUR`; sonst erst nach dem doppelten Intervall. Geprüft wird je Takt
(`RECONCILE_TICK_SECONDS` 300, erster Takt beim Start). Letztes Ende aus `state.db`, Tabelle
`reconcile`, `MAX(finished_at)` (Skript `rstate.py`, nur lesend), Ortszeit des Hosts (UTC+2).

| Lauf | Codestand | letztes Ende vorher | Neustart | gesetzte Stunde | erwarteter Start | tatsächlicher Start | Ende | Logzeile (nur Zähler) |
|---|---|---|---|---|---|---|---|---|
| 1 Gegenprobe | `bd4e13af` (Elternteil von `eff4a9bf`, vor 33-03), Worktree `abnahme33-gegenprobe` | 13.10. 12:56:05 | 11:46:08 | 13 (t1 = 13.10. 13:56:05) | erster Takt, weil seit dem Ende mehr als 2 h vergangen sind | erster Takt beim Start (11:46:08 bis 11:46:10) | 11:46:10 | `walked, mounts=3 slices=3 seen=491 stale=0 missing=0 given_up=0` |
| 2 neuer Stand | `fe813988` (main) | 11:46:10 | 11:47:18 | 12 (t1 = 12:46:10) | erster Takt nach 12:46:10, also 12:47:2x | 12:47:2x (Takt 12 nach dem Start) | 12:47:27 | `walked, mounts=3 slices=3 seen=491 stale=7 missing=0 given_up=0` |
| 3 neuer Stand, zweiter Abgleich | `fe813988` | 12:47:27 | 12:48:08 | 13 (t1 = 13:47:27) | erster Takt nach 13:47:27, also 13:48:1x | 13:48:1x | 13:48:16 | `walked, mounts=3 slices=3 seen=491 stale=0 missing=0 given_up=0` |

Alle drei Starts mit `FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1` und `FINDLING_OCR_ENABLED=false`.
Zwischen Lauf 1 und Lauf 2 lief von 11:46:23 bis 11:47:14 der Hauptbaum ohne die Variablen
(Abweichung A2 unten); Standardtakt 24 h, also kein Abgleich, `state.db` bestätigt das.

Gegenprobe-Prozess: Python des Hauptbaums mit `PYTHONPATH=<worktree>/backend/src`, gleicher
Speicher `.dev/storage`, gleiches Geheimnis. Positivkontrolle des Codestands vor dem Start:
`findling.worker.reconcile.__file__` zeigt in den Worktree und der Quelltext enthält den
Weg-C-Zweig `row.file_id in known` nicht; im Hauptbaum enthält er ihn.

### Ergebnis je Datei

| Datei | vorher (nach Saat) | nach Lauf 1, alter Stand (Gegenprobe) | nach Lauf 2, neuer Stand | nach Lauf 3 | nach dem Rückweg |
|---|---|---|---|---|---|
| G `Praesentation.key/Data/notiz.txt` (Muster) | 1 | **1** | **0** | 0 | 1 |
| H `Altordner/notiz.txt` (Präfix) | 1 | **1** | **0** | 0 | 1 |
| K Kontrolle | 1 | 1 | 1 | 1 | 1 |
| A `Vortrag.key/Data/notiz.txt` (aus Task 1, auch unter `*.key`) | 1 | 1 | 0 | , | 1 |
| F `Vortrag.key/Data/neu.txt` (aus Task 1) | 1 | , | 0 | , | 1 |
| Diagnose G und H | `excluded` sofort nach dem occ-Befehl | `excluded` | `excluded` | , | , |

Lauf 2 räumte genau sieben Dateien (`stale=7`): G, H, Bild 3007, PDF 3009 und aus Task 1 A, F
und Bild 2995. Abholung ohne cron.php: Der Abgleich reiht über `requeue` ein, der Poller holte
sie ab, `describe()` machte Löschaufträge daraus (`claimed=7 committed=7`, `DELETE` quittiert),
12:47:51 G 0 und H 0. Lauf 3 reihte nichts ein (`stale=0`, Queue 0), keine Schleife.

Dauer bis zum Verschwinden, Weg C: vom Setzen der Regeln (11:45:27) bis 12:47:51, bestimmt nur
durch die Fälligkeit; vom Start des fälligen Laufs bis zum Verschwinden unter 30 Sekunden.
Weg A zum Vergleich: rund eine Minute nach dem Speichern.

### Urteilszeilen (PE-9, B2), `findling_file_state`

| Datei-ID | vorher (11:40:13) | nach Lauf 1 | nach Lauf 3 |
|---|---|---|---|
| 3007 Bild unter `Praesentation.key` | `skipped(no_text_layer)` | weg | weg |
| 3009 PDF unter `Praesentation.key` | `skipped(no_text_layer)` | weg | weg |
| 3008 Kontrollbild | `skipped(no_text_layer)` | bleibt | bleibt |
| 2995 Bild unter `Vortrag.key` (Task 1) | `skipped(image_not_ocrable)` | nicht abgefragt | weg |
| 2996 Kontrollbild (Task 1) | `skipped(image_not_ocrable)` | , | bleibt |

Die Urteilszeilen unter der per occ gesetzten Regel verschwanden schon im Gegenprobe-Lauf. Das
ist kein Widerspruch zur Gegenprobe: Die Bereinigung sitzt laut 33-04 im Abgleichs-Slice der
PHP-Seite (`ReconcileController::forgetExcludedVerdicts()`), und `php/` ist in beiden Läufen der
neue Stand. Der Codestand des Containers entscheidet nur, ob das Dokument den Index verlässt;
das zeigen G und H (1 auf dem alten, 0 auf dem neuen Stand). SQL-Ausgaben: `fs_c_vorher.txt`,
`fs_c_nachher.txt`, `protokoll.log`.

### Rückweg Weg C

Regeln per occ zurück (`exclusions` `["Archiv"]`, `exclusion_patterns` `[]`, 13:58),
`occ findling:index --restart -n`, cron.php bis der Crawl fertig war (8 Läufe, 13:58:21),
Queue leer 13:59:19: G 1, H 1, K 1, A 1, F 1.

## Aufräumen und Endzustand

Erwartung (13:59:31 und 14:58:01) vor jedem Schritt im Rohprotokoll.

| Schritt | Ergebnis |
|---|---|
| WebDAV `DELETE` `/Abnahme33`, `/Abnahme33c`, `/node_modules`, `/Archiv/alt.txt` | je 204; `/Archiv` selbst (1.4.2-Bestand mit zwei Dateien) bleibt |
| cron.php bis kein SubtreeExpandJob | 6 Läufe (13:59:49), 13 Löschzeilen abgeholt (`claimed=13 committed=13`) |
| danach Papierkorb (`occ trashbin:cleanup testuser`) | geleert, Reihenfolge wie in 32-07 |
| Suche nach allen neun Saatwörtern | je 0 |
| PROPFIND `/Abnahme33`, `/Abnahme33c`, `/node_modules`, `/Archiv/alt.txt` | je 404 |
| Host-Backend ohne die Testvariablen neu registriert (14:57:34) | Status 1.4.2, `docs` 469 wie vor dem Plan |
| Worktree `abnahme33-gegenprobe` | entfernt; issue-14, release-1.3, release-1.4.x unberührt |
| App-Passwort `nachweis3309` (ID 101) | gelöscht, altes Token danach 401, Tokendatei im Scratch gelöscht |
| `exclusions` | `["Archiv"]`, hex `5B22417263686976225D`, byte-gleich zum Anfang |
| `exclusion_patterns` | Schlüssel gelöscht wie vor dem Plan (`config:app:get` Exit 1, liest sich als leere Liste) |
| Jobs, Queue | nur der reguläre ScanRecountJob, Queue 0 |
| Datei 2970 (carol, M-32-02) | nicht angefasst: im Container weiter `indexed`, ohne Grabstein, ACL `carol` |

## Abweichungen

- **A1 Befund L-33-09-01 und Fix im Plan** (Owner-Entscheid Option 1), eigener Commit `fe813988`.
- **A2 Registrierskript ersetzt den Gegenprobe-Prozess.** `register-exapp.sh` hält einen laufenden
  Prozess für veraltet, wenn eine Routenprobe 404 ergibt; mit dem Gegenprobe-Prozess ergab die
  Probe für `^/status$` 404, das Skript startete 11:46:23 den Hauptbaum ohne die Variablen. Der
  Abgleich der Gegenprobe war da schon gelaufen (11:46:10). Für Lauf 2 und 3 wurde der Prozess
  vorher beendet und das Skript mit den Variablen gestartet.
- **A3 Routen-Cache.** Nach dem Wechsel GET auf POST antwortete die Instanz 405, weil Nextcloud die
  Routen im APCu hält und der Bind-Mount keine App-Version ändert; Container neu gestartet.
- **A4 OCR für die Weg-C-Läufe aus** (`FINDLING_OCR_ENABLED=false`), damit `no_text_layer` stehen
  bleibt; dadurch tragen auch die Bilder `no_text_layer`.
- **A5 Kehrjob und Präfix** (Hinweis H1 oben): Weg A reiht auch Dateien unter einem Präfix als
  Löschzeile ein; idempotent, kein Befund.
- **A6 Wartezeiten** über ereignisgetriebene Wartebefehle (`tail -f` auf Backend- und Access-Log mit
  `grep -m1`, Hintergrundbefehle), kein `sleep`. Zweimal überbrückte ein `timeout 2 tail -f`
  das Ende eines gestoppten Prozesses beziehungsweise den Neustart des Containers.
