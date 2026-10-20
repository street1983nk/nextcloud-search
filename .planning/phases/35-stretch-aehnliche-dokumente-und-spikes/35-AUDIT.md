---
phase: 35-stretch-aehnliche-dokumente-und-spikes
audited: 2026-10-20
diff: 5a66ba1e..c1db884b
files_reviewed: 24
findings:
  critical: 0
  high: 0
  medium: 0
  low: 6
  total: 6
status: fixed
fix_run: 2026-10-20
fix_commits: [5a98eee0, 0e1e42f9, c2b402cb]
fixed: [L-35-01, L-35-03, L-35-04, L-35-05]
still_open: [L-35-02, L-35-06]
---

# Phase 35: Security-, Bug- und Performance-Audit

**Stand:** geschlossen am 20.10.2026. Task 1 (Sicherheit und Fehler), Task 2
(Performance) und Task 3 (Behandlung, Abschluss) am selben Tag. Kein Befund
CRITICAL, HIGH oder MEDIUM; sechs LOW-Befunde, alle behandelt (Owner-Wort
20.10.: auch LOW-Befunde werden behandelt): vier gefixt (L-35-01 mit
Regressionstest, L-35-04 und L-35-05 im Dev-Skript mit Live-Gegenprobe,
L-35-03 als Doku-Nachtrag), zwei begründet akzeptiert (L-35-02, L-35-06,
Abschnitt "LOW-Entscheidungen").

**Umfang:** `git diff 5a66ba1e..c1db884b` (Basis = Elternteil von 1d02bf51,
dem ersten Commit mit "(35-01)"). Mit Planung 131 Dateien (11 422 Zeilen dazu,
118 weg), ohne `.planning/` 113 Dateien (9 779 dazu, 97 weg). Gelesen bzw. per
Probe gefahren: `backend/src/findling/api/similar.py`,
`index/search.py` (similar_candidates), `store/vectors.py` (vectors_of),
`index/fusion.py` (centroid), `config.py`, `main.py`, `appinfo/info.xml`;
`php/lib/Service/{SearchService,ExAppService,SimilarOutcome,SearchCaps}.php`,
`php/lib/Controller/PageController.php` (similarId, similarView),
`php/templates/search.php`, `php/css/search.css`, 16 Kataloge (über die Gates
aus 35-13); die Messordner `docs/measurements/2026-10-aehnlich-distanzen/` und
`2026-10-granite-vergleich/` samt Rohdaten; `35-DEDUP-NOTIZ.md`; alle SUMMARYs
35-01 bis 35-11, 35-04B und 35-13 (Abweichungen und offene Fragen vor Task 1).

**Wo gelaufen:** Windows 11 Pro 10.0.26200; Instanz `findling-nextcloud`
(http://localhost:8090, SQLite, `php/` des Haupt-Checkouts als Bind-Mount,
Stand c1db884b), Backend als Host-Prozess auf Port 10035 (register-exapp.sh,
mit Modellverzeichnis, 1 031 Chunks über 440 Dokumente). Konten admin,
kollegin, testuser (alle bestanden vorher); Cookie-Logins nach dem Muster von
`scripts/dev/probe_page_login.sh`. Proben per curl, kein Browser; alles
seriell. Quelltextproben stehen als Regressionstests in
`backend/tests/test_phase35_audit.py` (5 Tests, mit Positivkontrolle der
Logmuster-Probe).

## Security

Jede Probe mit Verfahren und Ergebnis; die Logmarken vor den Proben:
`.dev/exapp.log` 75 Zeilen, `nextcloud.log` 5 369 Zeilen.

### S1 Quelle vor Container

- **Quelltext:** in `SearchService::similar` steht `self::readableFile(`
  (Zeile 581) vor `$this->exApp->similarCandidates(` (Zeile 589); Nachbar-
  Recheck Zeile 641. Als Test: `test_the_source_is_rechecked_before_the_container_is_asked`.
- **Live:** kollegin ruft `?similar=14` (Datei von admin). Zählung
  `grep -c "POST /similar" .dev/exapp.log` vor und nach der Probe: 16 und 16,
  **kein Containeraufruf**. Die Seite zeigt "Diese Datei ist nicht verfügbar",
  0 Treffer.

### S2 Kein fremder Nachbar (unabhängiges Orakel)

Aufbau: `Triangle.odp` (Datei 14, admin) als byte-gleiche Kopie zweimal
hochgeladen, `Triangle-Kopie-3512.odp` als admin (fileid 21644) und
`Triangle-bob-3512.odp` als kollegin (21645); beide indexiert und eingebettet
(exapp.log: `indexed=3`, dann `embedded=3`).

- admin, `?similar=14`: Nachbarn `/f/15 /f/27 /f/28 /f/21644`. Die eigene
  Kopie erscheint (B5), **die inhaltsgleiche kollegin-Kopie 21645 erscheint
  nicht** (0 Vorkommen im HTML).
- Gegenrichtung kollegin, `?similar=21645`: Nachbarn `/f/203 /f/204 /f/216
  /f/217`, weder 14 noch 21644.
- **Orakel** (SQL per PDO auf `oc_filecache` JOIN `oc_storages` und
  `oc_share` im Container, nicht der geprüfte Code): 21645 liegt auf
  `home::kollegin`, keine Zeile in `oc_share`; 14 und 21644 auf
  `home::admin`, keine Freigabe; die vier gezeigten Nachbarn der Gegenrichtung
  liegen alle auf `home::kollegin` (203 ist kollegins eigene
  `Templates/Triangle.odp`). Jede gezeigte Zeile ist lesbar, jede fremde fehlt.

### S3 Orakel fremd, gelöscht, unbekannt

Als admin: `similar=21644` (nach DELETE, Tombstone), `similar=21645` (fremd),
`similar=999999999` (nicht existent). Der Block `app-content` bis `</main>`
ist in allen drei Antworten **byte-identisch (2 204 Bytes)**; kein Titel der
fremden Datei im HTML; Satz "Diese Datei ist nicht verfügbar".

### S4 Eingaben

`similar` mit `12345678901234567890` (20 Ziffern), `+14` (roh und
URL-codiert), `%2014` (Leerzeichen), `1e3`, `0`, `014`, `١٤`
(Unicode-Ziffern) und der Array-Form `similar[]=1`: überall HTTP 200, der
`app-content` byte-gleich zur normalen Ergebnisseite (Array-Form: normale
Seite mit Treffern). **Kein 500.**

### S5 Containerroute direkt

`POST http://127.0.0.1:10035/similar`: ohne AppAPI-Header **401**; mit
falschem Secret **401**; mit gültiger Signatur und `userId` im Body **400**
("user identity is taken from the AppAPI header only"); Positivkontrolle
gültig: 200 mit `{27, 28, 15}`. Routenliste: `grep -cE "<url>[^<]*similar"
backend/appinfo/info.xml` = 0 (Test:
`test_the_similar_route_stays_out_of_the_route_table`). Zählgate
`prefilter_visible` in `index/search.py` = 2 (Test:
`test_the_prefilter_is_called_exactly_twice_in_the_search_module`).

### S6 Logs

- **Quelltext:** die Logzeilen der neuen Teile tragen Typnamen, statische
  Sätze, eine Zahl (`count`) oder die zwei Versionswerte; keine fileid, kein
  Pfad, kein Titel, kein Nutzer (Test mit Positivkontrolle:
  `test_no_log_line_of_the_similar_code_names_a_file_or_user`).
- **Live:** nach allen Proben 0 neue Zeilen in `nextcloud.log` seit Marke
  5 369; die neuen exapp.log-Zeilen enthalten keinen der Testdateinamen
  (`triangle-kopie`, `triangle-bob`, `onerror`, `Nextcloud.png`: 0 Treffer).
  Bestandsbeobachtung ohne Phasenbezug: die httpx-INFO-Zeilen des
  Indexierpfads nennen fileid und userId der OCS-Metadatenabfrage; Bestand
  vor Phase 35, siehe L-35-06.

### S7 XSS über den Dateititel

Datei `<img src=x onerror=alert(1)>.txt` als admin hochgeladen (21646),
`?similar=21646` als Rohtext geprüft: h1 trägt
`&lt;img src=x onerror=alert(1)&gt;.txt`, **0 Vorkommen** von rohem
`<img src=x` im `app-content`.

### S8 Dedup-Notiz gegen die Sperrliste

Issue #25 samt Kommentaren frisch per `gh` gezogen, identifizierende Namen
extrahiert (vier `smb::<name>@...//Daten//`-Storage-Ids, Share-Name):
`grep -F -i -f` gegen `35-DEDUP-NOTIZ.md`: **0 Treffer**; Positivkontrolle
mit eingepflanztem Namen: 1.

### S9 Kontodaten im Messordner

`docs/measurements/2026-10-granite-vergleich/`: freistehende 12-Ziffern-Zahlen
(Kontonummern-Form) 0, `.pem` 0; die Treffer des rohen Rasters sind
sha256-Werte und deutsch gesetzte Byte-Zahlen (2.147.483.648), keine IPs.

## Bugs

| Nr. | Fall | Verfahren | Ergebnis | Urteil |
|---|---|---|---|---|
| B1 | Quelle ohne Vektoren | `similar=58` (Nextcloud.png, admin, per SQL auf state.db und vectors.db als lebend und vektorlos bestätigt) | h1 "Ähnlich zu: Nextcloud.png", Leersatz, 0 Treffer, kein "nicht verfügbar" | in Ordnung |
| B2 | Quelle zwischen Klick und Anzeige gelöscht | DELETE 21644 per WebDAV, dann `similar=21644` | Zustand "nicht verfügbar", byte-gleich zu fremd und unbekannt (S3) | in Ordnung |
| B3 | Backend gestoppt | Host-Prozess (PID 29516) beendet, `?similar=14` als admin, danach Neustart über register-exapp.sh | HTTP 200, sichtbarer Bestandsbanner "Die Suche antwortet gerade nicht ...", Rückweg vorhanden, kein Leerzustand, kein 500 | in Ordnung |
| B4 | Rückweg-Parameter | testuser, Seite 2 einer echten Trefferliste (`cursors=0.25&page=2&fp=c17df32e`), Ähnlich-Link von dort, backUrl gegen die Ausgangsadresse (Query-Paare sortiert verglichen) | identisch bis auf das fehlende `similar`; mit unpassendem fp fällt die Seite wie im Bestand auf Seite 1 zurück (Fingerprint-Mechanik, kein Phasenbefund) | in Ordnung |
| B5 | Echte Kopie als Nachbar | Kopie 21644 (admin) nach Einbettung | erscheint in `similar=14`, die Quelle selbst nie | in Ordnung |
| B6 | Regel vor Rohdaten | `git log --reverse` je Ordner | aehnlich-distanzen: Regel 7068abe7 (19.10. 20:45) vor Rohdaten 839a5fdf (21:07); 04B-Kette 1a32b6c9 vor 12f55aad; granite: Regel 3d1a41b7 (19.10. 18:25) vor Rohdaten 5c7f7de0 (20.10. 02:11) | in Ordnung |
| B7 | Regel wie geschrieben angewandt | Abschnitt 18 des granite-Berichts zeilenweise gegen Abschnitt 1; Abschnitt 1 per `git show 3d1a41b7` gegen HEAD gedifft | Regelabschnitt unverändert seit dem Regel-Commit; (a) bis (d) je mit Messwert, Grenze, Ergebnis und Rohdatei; Eindeutigkeitsfrage beantwortet | in Ordnung |
| B8 | Kein Modellwechsel in v1.5 | `git diff 5a66ba1e..HEAD -- backend/Dockerfile` | leer; der Produktdiff ist genau der Code der Ähnlich-Ansicht plus info.xml-Kommentar | in Ordnung |

Aufräumen der Proben: 21644 im Lauf gelöscht (B2), 21645 und 21646 nach den
Proben per WebDAV gelöscht (je 204); kein Konto angelegt, keine Sprache
umgestellt; das Basis-Template aus der P1-Messung per `git checkout --`
zurückgesetzt (git status leer).

## Performance

Gemessen am 20.10.2026 auf dem Entwicklungsrechner (Instanz wie oben), curl
mit Cookie-Jar, je Reihe 3 verworfene Aufwärmaufrufe und 20 Messungen, seriell,
kein Browser. Rohzeiten im Scratch der Session (p1-, p2-, p3-zeiten.txt).

| Nr. | Messgröße | Wert | Budget | Urteil |
|---|---|---|---|---|
| P1 | Ergebnisseite 25 Treffer, ohne gegen mit Ähnlich-Links (Basis-Template 5a66ba1e eingespielt, Wirksamkeit je Richtung per Linkzählung 0 bzw. 25 abgewartet, danach Rückbau) | ohne p50 115,5 ms / p95 173,7 ms; mit p50 124,5 ms / p95 148,2 ms; Zuwachs p50 +9,0 ms für 25 zusätzliche Anker | 3,0 s Seitenbudget | in Ordnung |
| P2 | Ähnlich-Ansicht derselben Quelle (similar=14, 3 Nachbarn), 20 Aufrufe | p50 82,9 ms / p95 101,2 ms / max 211,2 ms | 3,0 s | in Ordnung |
| P3 | Containeraufruf `POST /similar` direkt (limit 30 wie die Companion-Anfrage), 20 Aufrufe | p50 6,8 ms / p95 10,7 ms / max 11,4 ms | 1,5 s Decke | in Ordnung |
| P4 | `readableFile`-Auflösungen je Ansicht | aus dem Quelltext: 1 (Quelle, Zeile 581) plus höchstens `SIMILAR_CANDIDATES` = 30 im Recheck, der bei 10 Treffern, `MAX_RECHECKS_ABSOLUTE` = 64 oder der Deadline abbricht, also höchstens 31; der PHPUnit-Fall "Recheck-Deckel und Zeitbudget" aus 35-06 zählt die Aufrufe per Mock (CI) | höchstens Kandidaten plus Quelle | in Ordnung |
| P5 | Plausibilität | Bestand auf 8090: 1 031 Chunks über 440 Dokumente; bekannte Scanzeiten 37,8 ms p95 warm bei 100 136 Chunks (arm64): der 6,8-ms-Aufruf bei einem Hundertstel des Bestands passt, der Löwenanteil ist Request-Overhead | n/a | in Ordnung |

## Befunde

Alle sechs LOW; MEDIUM oder höher: keiner. Die Behandlung folgt dem Owner-Wort
vom 20.10.2026 ("auch LOW-Befunde müssen behandelt werden").

### L-35-01 (LOW, gefixt): Leerer Vektorbestand unter der unknown-Marke füllt sich nie

- **Ort:** `backend/src/findling/worker/embedding.py`, Markenschritt (Bestand
  vor Phase 35; beobachtet in 35-08 auf der Dev-Instanz).
- **Beleg:** Instanz indexierte lange ohne Modell (vectors.db leer, Marke
  `unknown`, 8 429 indexierte Zeilen); nach dem Start mit Modell startete
  keine Nachlieferung, weil der unknown-Fall auf `embedded == indexed` wartet,
  das ohne Nachlieferung nie eintritt. 35-08 musste die Marke per SQL auf
  einen Altwert setzen, um die Kette über einen echten Drift auszulösen.
- **Fix (5a98eee0):** Findet der Leerlauf-Schritt indexierte Dokumente über
  einem **leeren** Bestand unter der unknown-Marke, schreibt er Cursor und
  Marke in der Drift-Reihenfolge und fordert die Dokumente zurück. Ein leerer
  Bestand kann nicht falsch beansprucht werden (T-06.1-41 braucht mindestens
  einen Vektor); ein teilgefüllter Bestand wartet weiter wie bisher, weil
  seine Vektoren kein benanntes Modell haben und die ehrliche Antwort darauf
  die Drift-Kette bleibt, die nichts auf Verdacht auslösen darf.
- **Regressionstest:**
  `test_an_empty_stock_under_the_unknown_mark_starts_the_redelivery` (rot vor
  dem Fix belegt: Marke blieb `unknown`; grün danach, inklusive
  Nicht-Schleifen bei dauerhaft scheiternder Einbettung); das ganze Modul
  `test_embedding_track.py` 72 passed. Baumhash des Pakets neu (80 Dateien,
  5a348317..., unabhängig mit find/sort/tr/sha256sum nachgerechnet, Journal
  "Plan 35-12" in `test_measurement_scripts.py`).

### L-35-02 (LOW, akzeptiert): Requeue-te embed-Zeilen wecken den armed Poller nicht sofort

- **Beleg aus 35-08:** 5 requeue-te Zeilen blieben im Leerlauf Minuten liegen,
  nach Neustart sofort verarbeitet.
- **Einordnung (Code gelesen, nicht nur vermutet):** der Poller fragt im
  Leerlauf spätestens alle `POLL_COOLDOWN_MAX_SECONDS` = 120 s wieder an;
  nach Queue-Ausfällen klettert die Retreat-Leiter auf höchstens 300 s. Die
  Beobachtung von 35-08 fiel in genau so ein Fenster (exapp.log: "the queue
  did not answer" nach den Backend-Neustarts). Die Requeue-Route ist zudem
  rein intern ("ExApp required", Gegenprobe als admin: 401-Äquivalent); im
  Produkt requeued nur die Drift-Kette, die im Poller selbst läuft und direkt
  weiterzieht. Verzögerung beschränkt, selbstheilend, kein Nutzerpfad.
- **Entscheidung:** accept; ein Push-Weckruf wäre neue Infrastruktur für
  einen Fall, der im Produkt nicht auftritt.

### L-35-03 (LOW, gefixt): Maß der Route gegen Maß der Deckenmessung nicht am Wert dokumentiert

- **Beleg:** 35-04B maß Centroid gegen Centroid; die Route vergleicht den
  Quell-Centroid gegen einzelne Nachbar-Abschnitte (Minimum je Dokument). Die
  Regel klammerte das als A1 aus, aber am abgeleiteten Wert 54,5 stand der
  Unterschied nicht.
- **Fix (c2b402cb):** Absatz in Abschnitt 10 (Grenzen) des Distanz-READMEs:
  beide Maße können in beide Richtungen abweichen (Renormierung), der
  Spielraum ist die Lücke von knapp 10 Punkten zwischen Fassungen (max 45,63)
  und Unbeteiligten (min 55,41); Live-Gegenprobe dieses Audits verlinkt
  (Kopie erscheint, Fremdes nie).

### L-35-04 (LOW, gefixt): register-exapp.sh erkennt einen Prozess ohne /similar nicht als veraltet

- **Beleg aus 35-13:** der alte Host-Prozess beantwortete `POST /similar` mit
  404 und wurde nicht ersetzt, weil die Stale-Probe nur die in info.xml
  deklarierten Routen prüft und die Inhaltsrouten bewusst nicht deklariert
  sind.
- **Fix (0e1e42f9):** zweite Probeschleife über die aus den API-Quellen
  gelesenen gemounteten Routen (keine Literal-Liste, DI-04-01-Muster);
  405 gilt als gemountet, nur 404 als veraltet. Gegenprobe live: GET auf
  `/similar` am laufenden Prozess 405, auf einen nicht existenten Pfad 404.
  Dev-Skript, kein Produktcode, kein Baumhash.

### L-35-05 (LOW, gefixt, Neufund dieses Audits): Die Stale-Probe prüfte die Regex-Form und machte den Reuse-Zweig zu totem Code

- **Beleg:** die deklarierten Routen stehen als Regex in info.xml
  (`^/status$`); die Probe hängte sie wörtlich an die URL, bekam immer 404
  und startete den Prozess bei **jedem** Lauf neu ("restarting ... because
  the declared route ^/status$ is not mounted in it", live reproduziert).
- **Fix (0e1e42f9, gleicher Commit):** Anker werden vor der Probe
  abgestreift. Gegenprobe: der Folgelauf meldet "backend already answers ...
  reusing the secret".

### L-35-06 (LOW, akzeptiert, Bestand): httpx-INFO-Zeilen des Indexierpfads nennen fileid und userId

- **Beleg:** S6-Live-Scan; die Zeilen stammen aus der OCS-Metadatenabfrage
  des Workers (`GET .../files/<id>?userId=<uid>`), nicht aus Phase-35-Code.
- **Entscheidung:** accept für dieses Audit (außerhalb des Phasen-Diffs);
  als Prüfpunkt für die Launch-Härtung Phase 36 notiert (gehört das
  httpx-INFO-Level in das ausgelieferte Image?).

### T-35-15 (benannter LOW, akzeptiert): Verdrängungsklasse des Scan-Fensters

Ein fremdes Dokument, das näher an der Quelle liegt als ein eigenes, belegt
einen Platz im Scan-Fenster (`SIMILAR_SCAN_CHUNKS` = 300 plus Quellchunks),
bevor der Rechte-Filter greift. Bei 10 gezeigten Treffern aus bis zu 30
Kandidaten über ein 300er-Fenster beißt das nur auf einem Bestand voller
fremder Fast-Duplikate, und es ist dieselbe Verdrängungsklasse, die die
gewöhnliche semantische Runde hat (Docstring von `similar_candidates`,
Pitfall 2 des Plans). Live sichtbar in S2: kollegins Kopie verdrängte keinen
der drei admin-Nachbarn. Entscheidung: accept, wie im Threat-Model der Phase
vorgesehen; eine per-Nutzer-Rangliste wäre ein zweites Rechtemodell im
Container und genau das, was D-14 und die Vorfilter-Doktrin ausschließen.

## LOW-Entscheidungen

| Befund | Entscheidung | Grund | Zielphase | Quelle |
|---|---|---|---|---|
| L-35-01 | fix | Produktpfad; genau die Instanzklasse, für die die Ähnlich-Ansicht gedacht ist, bliebe sonst für immer leer | 35 | 35-08-Befund |
| L-35-02 | accept | Verzögerung beschränkt (120 s, nach Ausfällen 300 s), Route intern, kein Nutzerpfad | keine | 35-08-Befund |
| L-35-03 | fix | Doku am Wert; billig, hält die Regel ehrlich | 35 | 35-05/35-08 |
| L-35-04 | fix | Dev-Werkzeug log den falschen Zustand; kostet jeden Entwickler Zeit | 35 | 35-13 Frage 3 |
| L-35-05 | fix | Reuse-Zweig war tot; gleicher Fix-Ort wie L-35-04 | 35 | Audit 35-12 |
| L-35-06 | accept | Bestand außerhalb des Phasen-Diffs; Prüfpunkt Phase 36 | 36 | Audit 35-12 |
| T-35-15 | accept | Verdrängungsklasse der gewöhnlichen semantischen Runde; Gegenmittel wäre ein zweites Rechtemodell | keine | Threat-Model 35 |

## Fixes (Task 3)

**RED vor dem Fix** (L-35-01):
`test_an_empty_stock_under_the_unknown_mark_starts_the_redelivery` rot gegen
den unveränderten Code (`AssertionError: ... unknown`), danach grün; Modul
72 passed.

| Befund | Commit | Fix | GREEN |
|---|---|---|---|
| L-35-01 | 5a98eee0 | `worker/embedding.py`: unknown-Fall liefert bei leerem Bestand nach (Cursor vor Marke, Drift-Reihenfolge); Baumhash-Journal "Plan 35-12" | 72 passed (Modul), 649 passed (measurement + audit + track) |
| L-35-04, L-35-05 | 0e1e42f9 | `scripts/dev/register-exapp.sh`: gemountete Routen aus den API-Quellen zusätzlich proben; Regex-Anker vor der Probe abstreifen | Live: Lauf 1 restart (Anker-Befund), Lauf 2 "reusing"; 405/404-Unterscheidung belegt |
| L-35-03 | c2b402cb | Distanz-README Abschnitt 10, Grenzen-Absatz zum Maß der Route | Doku-Gates grün |

Gates nach den Fixes: ruff check und ruff format (src, tests, scripts, 248
Dateien), pyright (latest) 0 Fehler, vulture sauber, reuse lint 2831 konform;
php -l entfällt (keine PHP-Datei geändert, Companion-Baumhash unverändert).
Volle Suite und CI: siehe Abschlussvermerk in 35-12-SUMMARY.md (CI-Block nach
dem Push).

## Was gegengeprüft wurde, nicht nur gelesen

| Prüfung | Verfahren (anders als die Umsetzung) | Ergebnis |
|---|---|---|
| Rechtegrenze S2 | byte-gleiche Fremdkopie, Besitz und Freigaben per SQL auf oc_filecache/oc_share | fremde Kopie nie gezeigt |
| Zustandsgleichheit S3 | app-content-Blöcke byte-verglichen (Python, nicht grep) | 3 x 2 204 Bytes identisch |
| Containeraufruf S1 | Zeilenzählung im Backend-Zugriffslog, nicht der PHP-Code | 16 vor, 16 nach |
| Direktzugriff S5 | curl gegen 10035 mit und ohne Signatur, mit userId im Body | 401/401/400, Kontrolle 200 |
| Logs S6 | zwei Logquellen nach den Probennamen durchsucht, Positivkontrolle im Test | 0 Treffer |
| XSS S7 | Rohtext der Antwort, nicht der Browser | escaped, 0 rohe Tags |
| Sperrliste S8 | Namen frisch aus dem Issue gezogen, nicht die Liste aus 35-02 | 0 Treffer, Kontrolle 1 |
| Regel B7 | Abschnitt 1 per git show gegen HEAD, Abschnitt 18 zeilenweise | unverändert, mechanisch angewandt |
| P1 | Basis-Template live eingespielt (Opcache-Wirksamkeit je Richtung abgewartet), nicht geschätzt | +9,0 ms p50 für 25 Links |
| L-35-01-Fix | RED vor dem Fix, GREEN danach, Nicht-Schleifen-Fall im selben Test | siehe Fixes |
| L-35-05-Fix | Reproduktion vor dem Fix (restart-Zeile), Reuse-Zeile danach | siehe Fixes |

## Offene Punkte für Phase 36

- L-35-06: httpx-INFO-Level im ausgelieferten Image prüfen (nennt fileid und
  userId der OCS-Abfrage im Container-Log).
- Teilgefüllter Bestand unter der unknown-Marke wartet weiterhin (bewusste
  Grenze des L-35-01-Fixes); falls eine Fremdinstallation diesen Zustand
  zeigt, ist die Antwort die Drift-Kette, nie ein stilles Beanspruchen.
- 186 Datenbankabfragen je Pollaufruf (aus 34-AUDIT, deferred-items.md),
  unverändert offen.
