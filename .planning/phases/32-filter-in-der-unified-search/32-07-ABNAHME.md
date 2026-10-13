# Phase 32 Plan 07: Abnahmeprotokoll der Filter in der Unified Search

Task 1 (Proben vorab per Playwright) ist gefahren. Task 2 (gemeinsame Abnahme
mit dem Owner) ist offen; dieses Protokoll nimmt nichts ab.

## Stand

| Punkt | Wert |
|---|---|
| Datum | 13.10.2026 |
| Commit | `f1d935ac` (origin/main, Stand nach 32-06) |
| Instanz | `findling-nextcloud`, http://localhost:8090, Nextcloud 34.0.3, `php/` als Bind-Mount |
| Apps | findling 1.4.2, findling_backend 1.4.2 (Host-Prozess, Heartbeat 200), app_api 34.0.0 |
| `occ status` | `needsDbUpgrade: false`, `maintenance: false`, kein `occ upgrade` nötig |
| Kanarie | `term=findling-canary` über `/ocs/v2.php/search/providers/findling/search`: HTTP 200, Eintrag `findling-canary` |
| Ausgeliefertes Skript | `/custom_apps/findling/js/unified-search.js` per HTTP gleich dem Repo-Stand (SHA-256 `ca02a4db...959b`) |
| Nutzer | testuser, Sprache `de` (Ausgangswert), für die Wortlautbilder kurz `en` und `fr`, danach wieder `de` |
| Browser | Playwright (MCP), Chromium, Viewport 1920 x 1009 |
| Bildschirmfotos | Scratch der Sitzung, Ordner `abnahme32\` (Pfade unten relativ dazu) |

Scratch-Ordner:
`C:\Users\Student\AppData\Local\Temp\claude\C--Users-Student\f6488641-8ddf-4bad-8748-b99f3aecda70\scratchpad\abnahme32\`

## Saat (per WebDAV, bleibt bis Task 3 stehen)

| Pfad | Inhalt | Datei-ID |
|---|---|---|
| `/Abnahme32/Bericht.pdf` | Textlage "abnahme32 Bericht zur Abnahme" | 1746 |
| `/Abnahme32/Projekt/Notiz.txt` | "abnahme32 Notiz im Projekt" | 1747 |
| `/Abnahme32/Projekt/Tabelle.xlsx` | Zelle "abnahme32 Tabelle" | 1748 |
| `/Abnahme32/<img src=x onerror=alert(1)>/Probe.txt` | "abnahme32 Probe im Ordner mit Markup-Namen" | 1749 |
| `/Woanders32/Notiz.txt` | "abnahme32 Notiz woanders" | 1750 |
| `/Woanders32/Tuer/Tuer-1.pdf` bis `Tuer-6.pdf` | "tuerprobe32 Dokument n ..." (nur für die Tür, Probe 10) | 1751 bis 1756 |

Vorher: PROPFIND auf beide Ordner 404, Suche nach `abnahme32` und `tuerprobe32` je 0 Einträge.
Nachher per OCS (Positivkontrolle vor dem Browser): ungefiltert 5 Treffer,
`types=pdf` nur Bericht.pdf, `folder=/Abnahme32` genau die vier Dateien darunter,
`term=tuerprobe32&types=pdf&limit=5` fünf PDFs plus Tür.

Hinweise für Task 3 (Aufräumen): zusätzlich zu `/Abnahme32` und `/Woanders32`
liegt ein öffentlicher Link (Share-ID 3) auf
`/Woanders32/Notiz.txt` für Probe 11; er fällt mit der Datei weg. Lehre aus
32-03 beachten: erst Cron laufen lassen, dann den Papierkorb leeren.

Umgebungsnotiz: Die erste Fassung der Tür-PDFs (22 Zeichen Text) landete mit
`ocr_unavailable` im Fehlerbestand, weil der Host-Prozess des Backends kein
Tesseract hat und die kurze Textlage die OCR-Schwelle auslöste. Mit längerem
Text neu hochgeladen, danach `indexed`. Umgebung der Dev-Instanz, kein Befund
der Phase.

## Probentabelle

Grün heißt: im Browser gemessen (Accessibility-Baum, DOM oder Netzwerkmitschnitt), nicht nur angesehen.

| Nr. | Probe | Erwartung | Ergebnis | Beleg | Bild |
|---|---|---|---|---|---|
| 1 | Menü "Orte" | sieben Findling-Einträge, sechs Typen in der Reihenfolge von `SearchFilters::TYPES` | grün | Dashboard: Dateiinhalte, Dateiinhalte: PDF, Dokumente, Tabellen, Präsentationen, Bilder, Text, Dateiinhalte in einem Ordner; in Files ebenso, dort direkt vor "Dateien" und "Im Ordner" | `p01-menue-de.png`, `p01b-menue-in-files-de.png` |
| 2 | "Dateiinhalte: PDF" | Gruppe zeigt nur Bericht.pdf, Anfrage trägt `types=pdf` | grün | Gruppe "Dateiinhalte: PDF" mit genau Bericht.pdf (`/f/1746`); Netzwerk `.../providers/findling/search?term=abnahme32&...&types=pdf` 200 | `p02-typ-pdf.png` |
| 3 | Derselbe Eintrag ein zweites Mal | Chip bleibt und filtert weiter | grün | Chip "Dateiinhalte: PDF" steht, nächste Anfrage wieder mit `types=pdf`, keine ungefilterte dazwischen, Treffer unverändert Bericht.pdf | `p03-zweiter-klick.png` |
| 4 | "Dateiinhalte in einem Ordner", `/Abnahme32` | Auswahl zeigt nur Ordner; Treffer nur unter /Abnahme32 samt Unterordnern; Chip "Dateiinhalte in Abnahme32" | grün | Auswahl in der Wurzel und in /Abnahme32 nur Ordner (Wurzel hat laut PROPFIND 14 Dateien, /Abnahme32 hat Bericht.pdf, beide nicht gelistet); Titel "Ordner für die Suche wählen"; Treffer Bericht.pdf, Projekt/Notiz.txt, Projekt/Tabelle.xlsx, Markup-Ordner/Probe.txt; Woanders32/Notiz.txt fehlt; Anfrage `folder=%2FAbnahme32`. Zweiter Klick auf den Ordnereintrag: kein neuer Picker, Anfrage wieder mit `folder=%2FAbnahme32` | `p04a-ordnerauswahl-de.png`, `p04b-ordner-abnahme32.png` |
| 5 | Ordnerauswahl abbrechen | wie in 32-04: nichts gesendet, keine Fehlermeldung | grün nach 32-04, mit Befund B (Owner-Frage) | kein Toast, keine `folder`-Anfrage; Chip "Dateiinhalte in einem Ordner" bleibt stehen, die Gruppe trägt dieselbe Überschrift und zeigt ungefilterte Treffer inklusive Woanders32/Notiz.txt. Konsole: `FilePicker: No nodes selected` aus `core-common.js`; Gegenprobe: der Kerneintrag "Im Ordner" der Files-App erzeugt beim Abbruch denselben Eintrag | `p05-abbruch.png` |
| 6 | Wurzel wählen | keine leere Anfrage, kein `folder=`, keine Fehlermeldung | grün | Chip "Dateiinhalte in /", Anfragen ohne `folder`, alle HTTP 200, kein Toast, kein neuer Konsoleneintrag; Treffer ungefiltert (5 plus "Weitere Ergebnisse laden") | `p06-wurzel.png` |
| 7 | Ordner mit Markup-Namen | Chip zeigt die Zeichen als Text, kein `alert`, kein neues `img` | grün, Nebenbefund C (Kern) | Chip und Gruppenüberschrift "Dateiinhalte in <img src=x onerror=alert(1)>" als Text; Treffer nur Probe.txt; kein Dialog (Positivkontrolle: ein absichtlicher `alert` danach wurde erfasst); MutationObserver: 0 `img` mit `src=x` oder `onerror` (Positivkontrolle: ein eingefügtes `img src=x` wurde erfasst, einzige 404 auf `/x` stammt von dieser Kontrolle); einziges `img` im Dialog ist das App-Icon | `p07a-auswahl-markup-ordner.png`, `p07b-chip-markup-als-text.png` |
| 8 | Typ plus Datum des Kerns | beide wirken | grün | "Heute": Bericht.pdf, Anfrage mit `since`/`until` und `types=pdf`; "Letztes Jahr" (Gegenprobe): "Keine passenden Suchergebnisse", Anfrage mit Vorjahresgrenzen und `types=pdf` | `p08a-typ-plus-heute.png`, `p08b-typ-plus-letztes-jahr.png` |
| 9 | Typ-Chip plus Ordner-Chip | zwei getrennte Findling-Gruppen (D-32-02) | grün | Gruppe "Dateiinhalte in Abnahme32" (4 Treffer) und Gruppe "Dateiinhalte: PDF" (Bericht.pdf), keine Schnittmenge | `p09-zwei-gruppen.png` |
| 10 | Tür "Alle Treffer anzeigen" | Adresse trägt `types=pdf`, Seite zeigt Chip PDF | grün | `tuerprobe32` mit Chip PDF: fünf Treffer plus "Alle Treffer anzeigen / Öffnet die Findling-Ergebnisseite", `href=/apps/findling/?types=pdf&query=tuerprobe32`; Ergebnisseite: Chip PDF mit `aria-current=true` und "Filter PDF entfernen", sechs Treffer | `p10a-tuer-im-dialog.png`, `p10b-ergebnisseite-chip-pdf.png` |
| 11 | Seite ohne Unified-Search-API | keine Konsolenfehler aus unified-search.js | grün | Login: Skript nicht geladen, 0 Konsolenmeldungen. Öffentliche Share-Seite abgemeldet und angemeldet: Skript nicht geladen, Meldungen nur aus files (Service Worker, CSP), viewer und text. Zusätzlich die 403-Seite `/settings/admin/findling` als testuser: Skript geladen, `OCA.UnifiedSearch` fehlt, keine Meldung und kein `pageerror` aus dem Skript | `p11a-login-konsole.png`, `p11b-share-abgemeldet.png`, `p11c-share-angemeldet.png` |
| 12 | Konsole auf Files, Ergebnisseite, Einstellungen | keine Fehler aus unified-search.js | grün | Files: nur viewer-Warnung und tiptap-Fehler der text-App; Ergebnisseite: keine Meldung; `/settings/user`: nur viewer-Warnung; `/settings/admin/findling` als admin: keine Meldung. Auf allen vier Seiten Skript geladen, kein `pageerror` | `p12a-files.png`, `p10b-ergebnisseite-chip-pdf.png`, `p12b-einstellungen-nutzer.png`, `p12c-admin-einstellungen.png` |
| Z1 | Ungefilterte Suche (Zusatzbefund aus Probe 5 und 6) | eine Findling-Gruppe "Dateiinhalte" | **rot, Befund A** | ohne Chip acht Findling-Gruppen: "Dateiinhalte" plus sieben Gruppen mit den Namen der Menüeinträge, jede mit denselben ungefilterten Treffern; acht gleiche Anfragen je Suche | `befund-a-acht-gruppen-ungefiltert.png` |

## Befunde

### Befund A (rot, Produktfehler, gefixt mit Option A1, siehe "Befund A Fix"): sieben Scheingruppen und achtfache Anfrage in der ungefilterten Suche

Beobachtung (Dashboard und Files, testuser, `abnahme32`, kein Chip gesetzt):

- Der Dialog zeigt die Gruppe "Dateiinhalte" und darunter sieben weitere
  Gruppen "Dateiinhalte: PDF", "Dateiinhalte: Dokumente", "Dateiinhalte:
  Tabellen", "Dateiinhalte: Präsentationen", "Dateiinhalte: Bilder",
  "Dateiinhalte: Text" und "Dateiinhalte in einem Ordner". Jede listet
  dieselben fünf ungefilterten Treffer, also etwa Notiz.txt und Tabelle.xlsx
  unter der Überschrift "Dateiinhalte: PDF".
- Je Suchbegriff gehen acht gleiche Anfragen
  `GET /ocs/v2.php/search/providers/findling/search?term=abnahme32&from=...`
  ohne Filterparameter hinaus (dreimal reproduziert, Dashboard und Files).
  Jede läuft durch PHP, den Recheck und das Backend. Gegenprobe: der
  Files-Provider wird auf dem Dashboard einmal, in Files zweimal gefragt (dort
  registriert die Files-App ihren Eintrag "Im Ordner").
- Sobald ein Findling-Chip gesetzt ist, verschwinden die Scheingruppen
  (`updateResults` behält dann nur Gruppen mit Chip-ID); Proben 2 bis 10 sind
  davon nicht betroffen.

Ursache, im ausgelieferten Kern-Bundle `dist/core-unified-search.js` (NC
34.0.3) und in `core/src/components/UnifiedSearch/UnifiedSearchModal.vue`
gelesen:

1. Die Providerliste des Dialogs ist `groupProvidersByApp([...providers,
   ...this.externalFilters])` (stable34:436, stable35:739). Jeder über
   `registerFilterAction` registrierte Eintrag ist damit ein Provider.
2. `find()` fragt ohne Chip jeden Eintrag dieser Liste mit
   `type: e.searchFrom ?? e.id` ab und legt das Ergebnis unter der ID des
   Eintrags ab. Die sieben Findling-Einträge tragen `searchFrom: 'findling'`,
   daraus folgen sieben zusätzliche Anfragen und sieben Gruppen, benannt nach
   dem Label des Eintrags.
3. `filteredResults` blendet nur eine Gruppe aus: die mit der fest
   verdrahteten ID `in-folder` (der Eintrag der Files-App) ohne Pfad
   (stable33:389, stable34:389, stable35:574, master:565:
   `if (result.id !== 'in-folder') return false`). Findlings IDs
   `findling-type-*` und `findling-folder` fallen nicht darunter.

Der Mechanismus ist in stable33, stable34, stable35 und master gleich, betrifft
also das ganze Versionsfenster 33 bis 35. Die CI-Proben aus 32-06 fragen die
OCS-Route direkt und sehen den Dialog nicht; der Node-Vertragstest aus 32-04
spielt den Kern ohne `find()`. Darum ist der Fehler erst hier sichtbar.

Wirkung für Nutzer: In jeder Suche ohne Findling-Chip, also im Normalfall,
erscheinen sieben irreführend benannte Doppelgruppen, und Findling trägt die
achtfache Last je Suchbegriff. Nach Owner-Regel ein Produktfehler; gemäß
Auftrag nicht selbst gefixt, Entscheidung über einen Fix-Agenten beim Owner.
Bis dahin ist die Owner-Abnahme von USRCH-01 und USRCH-02 nicht sinnvoll.

### Befund A Fix (Plan-Abweichung in 32-07, vor dem Checkpoint)

Owner-Entscheid 13.10.2026: Option A1. Umgesetzt im Commit `4d616071`
("fix(32-07): the filter chips ask a hidden provider, no ghost groups without
a chip"), gepusht auf origin/main. Plan-Abweichung innerhalb von 32-07 (Befund
vor dem Checkpoint gefixt); in der 32-07-SUMMARY von Task 3 nachzutragen.

Mechanismus (Kern stable33, stable34, stable35, master, Zeilen im Kommentar von
`php/js/unified-search.js`): Jeder Eintrag aus `registerFilterAction` steht in
der Providerliste des Dialogs; ohne Chip fragt `find()` jeden Eintrag unter
`type: searchFrom ?? id` ohne Parameter ab. Gruppen erscheinen nur mit Treffern.
`SearchComposer::getProviders()` lässt einen Provider mit `getOrder() === null`
weg, `search()` prüft die Reihenfolge nicht.

Umsetzung:

- Neue Klasse `php/lib/Search/FilterProvider.php`, ID `findling-filter`,
  `getOrder()` immer `null`, Filter, Definitionen und Gruppenname
  ("Dateiinhalte") vom echten Provider übernommen. Ohne `types` und ohne
  `folder`: sofort leere Gruppe, kein Aufruf von `SearchService::run`. Sonst
  `Provider::search()` unverändert (gleiche Rechteprüfung, gleicher Recheck).
  Registriert in `AppInfo/Application.php` neben dem echten Provider.
- `php/js/unified-search.js`: `searchFrom: 'findling-filter'` an allen sieben
  Einträgen und Ereignissen; jeder Callback setzt `this.filters = {since,
  until, types, folder}` (nur wenn `this` ein Objekt ist, Schutzrahmen
  `guarded()` bleibt), damit das Datum des Kerns mit dem Chip reist; Wurzelwahl
  sendet `folder=/` (PHP liest `/` als keine Einschränkung, die Gruppe
  erscheint); Abbruch sendet weiter nichts, der Chip zeigt dann keine Treffer.
- Der echte Provider `findling` ist unverändert, sichtbar und antwortet gleich.
- Kern-Interna als bewusste Abhängigkeit dokumentiert in
  `docs/search-filters.md` (Abschnitt "How the chips reach Findling") und im
  Kopfkommentar des Skripts: ruft ein künftiger Kern den Callback nicht mehr als
  Methode des Menüeintrags auf, fällt nur das Datum neben einem Chip weg.
  Dazu der Hinweis auf `unified_search.providers_allowed` (dort muss
  `findling-filter` mit erlaubt sein).

Tests und Gegenproben:

| Ebene | Was | Ergebnis | Gegenprobe |
|---|---|---|---|
| PHPUnit | `FilterProviderTest` (13 Fälle: ID, Reihenfolge null auf vier Routen, Name, Filter, leer ohne `types`/`folder` in drei Varianten ohne Backend-Aufruf, Typ-Chip mit demselben Nutzer an `SearchService::run`, Ordner kanonisch, Wurzel `/` ohne Einschränkung mit Treffern, Chip plus Datum, Abgelehntes bleibt abgelehnt, Konstruktor hält nur `Provider`) | CI php.yml 38347181812 grün, 661 Tests (vorher 648) | Wegwerf-Zweig ohne Leer-Zweig: php.yml 38349488409 rot, genau die drei Leer-Fälle; Zweig danach gelöscht |
| Node-Vertragstest | `searchFrom` `findling-filter`, Filterkarte am Chip (Klick als Methode, Chip als Kopie wie im Kern), Wurzel und leere Wahl ergeben `{folder: '/'}`, losgelöster Callback sendet weiter und wirft nicht; Lese-Regeln und Selbsttests dazu | lokal 30 passed, CI python.yml 38347181819 grün | am echten Skript (Kopie, danach byte-gleich zurück): ohne `markChip(this)` 2 rot, `searchFrom` `findling` 4 rot, Wurzel wieder ohne `folder` 1 rot, ohne Objektprüfung 2 rot |
| deploy-harp | neue Proben im Schritt der Unified-Search-Filter: Providerliste ohne `findling-filter`, `findling-filter` ohne `types`/`folder` HTTP 200 und leere Liste, `types=pdf` liefert das Saat-PDF, `folder=/Filterprobe32` die drei Saatdateien, `folder=/` die ungefilterte Antwort; Gate `test_unified_search_filter_steps.py` um Anspruch 8 erweitert | HaRP deploy 38347181759 grün auf allen vier Beinen (stable33, stable34, stable35, stable34 arm64) | Gate auf dem echten Workflow ohne `same chip-root` meldet genau einen Befund; zwei neue Selbsttests |
| Sonst | `test_php_acl_boundary.py` unverändert und grün; team-folder-acl (Integration 38347181828) grün; Baumhash 97 Dateien `e8bb5819...ff8e` | grün | |

Lokale Gates vor dem Commit (aus `backend/`, `PYTHONUTF8=1`): pytest 5626
passed, 30 skipped; ruff check, ruff format --check, pyright (latest) 0 Fehler,
vulture ohne Befund; `node --check php/js/unified-search.js`; `php -l` über die
vier PHP-Dateien per `php:8.3-cli`. Weitere CI auf `4d616071` grün: Resilience
38347181820, Security scans 38347181769, OpenSSF Scorecard 38347181804,
Multi-arch image 38347181821.

Browser-Nachprobe auf der Dev-Instanz 8090 (`php/` als Bind-Mount, Stand
`4d616071`), testuser, Sprache de. Abweichung: Playwright-MCP stand in dieser
Sitzung nicht zur Verfügung; gefahren mit lokalem Playwright 1.63 (Chromium,
headless, Viewport 1920 x 1009) per Skript, gemessen über DOM und
Netzwerkmitschnitt. Bilder im Scratch-Ordner `abnahme32\`.

| Nr. | Probe | Ergebnis | Beleg | Bild |
|---|---|---|---|---|
| A1 | Ungefilterte Suche `abnahme32`, Dashboard | grün | genau eine Findling-Gruppe "Dateiinhalte" (5 Treffer plus "Weitere Ergebnisse laden"), daneben "Dateien"; eine Anfrage an `providers/findling`, sieben an `providers/findling-filter` ohne Parameter (leer, ohne Backend-Aufruf) | `fix-a-p1-ungefiltert.png` |
| A1b | dasselbe in Files | grün | eine Findling-Gruppe; Konsole nur viewer-Warnung und tiptap-Fehler der text-App (wie Probe 12) | `fix-a-p1-ungefiltert-files.png` |
| A2 | Chip "Dateiinhalte: PDF" | grün | Gruppe "Dateiinhalte: PDF" nur Bericht.pdf; Anfrage `findling-filter/search?...&types=pdf` | `fix-a-p2-chip-pdf.png` |
| A3 | Ordner `/Abnahme32` | grün | Gruppe "Dateiinhalte in Abnahme32": Bericht.pdf, Notiz.txt, Tabelle.xlsx, Probe.txt (Projekt und Markup-Ordner eingeschlossen, Woanders32 fehlt); Anfrage `folder=/Abnahme32` | `fix-a-p3-ordner-abnahme32.png` |
| A4 | Chip PDF plus "Heute" | grün | Anfrage `findling-filter/search?...&since=2026-10-12T22:00:00.000Z&until=2026-10-13T21:59:59.999Z&...&types=pdf`, Treffer Bericht.pdf | `fix-a-p4-chip-heute.png` |
| A5 | Ordnerauswahl abbrechen (Schließen) | grün | Chip "Dateiinhalte in einem Ordner" bleibt, "Keine passenden Suchergebnisse", keine Anfrage mit `folder`, kein Toast; Konsole `FilePicker: No nodes selected` (Kern, wie in Probe 5) | `fix-a-p5-abbruch.png` |
| A6 | Wurzel wählen ("testuser auswählen") | grün | Chip und Gruppe "Dateiinhalte in /" mit den 5 ungefilterten Treffern; Anfrage `folder=/`, HTTP 200, kein Toast | `fix-a-p6-wurzel.png` |
| A7 | Markup-Ordner | grün | Chip und Gruppe "Dateiinhalte in <img src=x onerror=alert(1)>" als Text, Treffer nur Probe.txt; kein Dialog, 0 `img` mit `src=x` oder `onerror` | `fix-a-p7-markup.png` |

Vorab per OCS auf 8090: Providerliste nennt nur `findling`; `findling-filter`
ohne Parameter leer, mit `types=pdf` Bericht.pdf, mit `folder=/Abnahme32` die
vier Dateien darunter, mit `folder=/` dieselben fünf Treffer wie `findling`.

Saat `/Abnahme32` und `/Woanders32` stehen weiter (Task 3). Folge für die
Owner-Fragen unten: Frage 1 ist entschieden (A1), das Verhalten zu Frage 4
(Wurzel) und 5 (Abbruch, jetzt ohne Treffer) hat sich mit dem Fix geändert.

### Befund B (Owner-Frage): Chip nach abgebrochener Ordnerauswahl

Nach Abbruch steht der Chip "Dateiinhalte in einem Ordner" und die Gruppe
heißt ebenso, gesucht wird aber ohne Ordner (Woanders32/Notiz.txt erscheint).
So in 32-04 bewusst gebaut, nach dem Vorbild `folderSearch.ts` der Files-App,
deren Eintrag "Im Ordner" sich gleich verhält. Der Plan nennt "kein
ungefilterter Chip, der als Filter ausgegeben wird" als Befundgrenze; der
Chiptext nennt allerdings keinen Ordner. Kein Fix ohne Owner-Entscheid.

Dazu: Der Abbruch hinterlässt in der Konsole `FilePicker: No nodes selected`
aus `core-common.js` (abgelehntes Promise der Kern-Dateiauswahl). Gegenprobe
mit dem Kerneintrag "Im Ordner": identischer Eintrag. Kein Findling-Code.

### Nebenbefund C (Kern, nur zur Kenntnis): Wählen-Knopf der Dateiauswahl

Im Markup-Ordner beschriftet die Kern-Dateiauswahl ihren Knopf mit
`&lt;img src=x onerror=alert(1)&gt; auswählen`, maskiert also doppelt. Kein
Skript läuft, kein Findling-Code; der Findling-Chip danach zeigt die Zeichen
korrekt als Text (Probe 7).

### Beobachtungen ohne Befund

- Die Gruppenüberschrift folgt dem Chip: mit Chip PDF heißt die Gruppe
  "Dateiinhalte: PDF", mit Ordner-Chip "Dateiinhalte in Abnahme32" (Kern setzt
  den Chiptext als Gruppennamen).
- Menüposition: auf dem Dashboard stehen die Findling-Einträge nach
  "Kommentare", in Files vor "Dateien" und "Im Ordner" (Kern gruppiert nach
  App).

## Wortlaut-Tabelle de / en / fr

Alle Werte am Bildschirm gemessen und gegen `php/l10n/de.json` und
`php/l10n/fr.json` geprüft: zeichengleich (auch das gewöhnliche Leerzeichen vor
dem Doppelpunkt im Französischen). Englisch ist der Quelltext.

| Nr. | Schlüssel | de | en | fr | Bild |
|---|---|---|---|---|---|
| 1 | `File contents: %s` | Dateiinhalte: %s | File contents: %s | Contenu des fichiers : %s | `wortlaut-<lang>-menue.png` |
| 2 | `PDF` (Eintrag) | Dateiinhalte: PDF | File contents: PDF | Contenu des fichiers : PDF | `wortlaut-<lang>-menue.png` |
| 3 | `Documents` (Eintrag) | Dateiinhalte: Dokumente | File contents: Documents | Contenu des fichiers : Documents | `wortlaut-<lang>-menue.png` |
| 4 | `Spreadsheets` (Eintrag) | Dateiinhalte: Tabellen | File contents: Spreadsheets | Contenu des fichiers : Feuilles de calcul | `wortlaut-<lang>-menue.png` |
| 5 | `Presentations` (Eintrag) | Dateiinhalte: Präsentationen | File contents: Presentations | Contenu des fichiers : Présentations | `wortlaut-<lang>-menue.png` |
| 6 | `Images` (Eintrag) | Dateiinhalte: Bilder | File contents: Images | Contenu des fichiers : Images | `wortlaut-<lang>-menue.png` |
| 7 | `Text` (Eintrag) | Dateiinhalte: Text | File contents: Text | Contenu des fichiers : Texte | `wortlaut-<lang>-menue.png` |
| 8 | `File contents in a folder` | Dateiinhalte in einem Ordner | File contents in a folder | Contenu des fichiers dans un dossier | `wortlaut-<lang>-menue.png` |
| 9 | `Choose the folder to search in` (Titel der Auswahl) | Ordner für die Suche wählen | Choose the folder to search in | Choisir le dossier où chercher | `wortlaut-<lang>-ordnerauswahl.png` |
| 10 | `File contents in %s` (Chip) | Dateiinhalte in Abnahme32 | File contents in Abnahme32 | Contenu des fichiers dans Abnahme32 | `wortlaut-<lang>-ordnerchip.png` |

`<lang>` steht für `de`, `en`, `fr`. Umgebende Kerntexte zum Vergleich: Menü
"Orte" / "Places" / "Emplacements", Wählen-Knopf "Abnahme32 auswählen" /
"Choose Abnahme32" / "Choisir Abnahme32", Kerneintrag der Files-App "Im Ordner".
Tür (Bestand vor Phase 32, de): "Alle Treffer anzeigen", Unterzeile "Öffnet die
Findling-Ergebnisseite".

## Offene Fragen an den Owner

1. Befund A: Fix-Agent beauftragen? Ohne Fix zeigt jede ungefilterte Suche
   sieben Scheingruppen und fragt Findling achtmal. Die Abnahme des Wortlauts
   ist davon getrennt möglich, die von USRCH-01 und USRCH-02 eher nicht.
2. Präfix "Dateiinhalte:" vor den sechs Typen behalten (Gruppe bleibt im Menü
   erkennbar, Einträge werden lang) oder kürzer (etwa nur "PDF")?
3. Ordnereintrag: "Dateiinhalte in einem Ordner" steht in Files direkt neben dem
   Kerneintrag "Im Ordner". Wortlaut so lassen oder deutlicher abgrenzen?
4. Wurzelwahl ergibt den Chip "Dateiinhalte in /" ohne Einschränkung. So lassen?
5. Befund B: Chip "Dateiinhalte in einem Ordner" nach abgebrochener Auswahl
   ohne Wirkung, wie beim Kerneintrag "Im Ordner". Akzeptabel?
6. Französisch: gewöhnliches Leerzeichen vor dem Doppelpunkt
   ("Contenu des fichiers : PDF") statt eines geschützten. So lassen?
7. Gruppenüberschrift gleich Chiptext ("Dateiinhalte: PDF" statt
   "Dateiinhalte"), Kernverhalten. Zur Kenntnis.

## Owner-Abnahme

Offen. Wird erst in Task 2 gemeinsam mit dem Owner ausgefüllt.
