---
phase: 32-filter-in-der-unified-search
audited: 2026-10-13
diff: a632a35c..7006129d
files_reviewed: 52
findings:
  critical: 0
  high: 0
  medium: 2
  low: 7
  total: 9
status: issues_found
fix_run: 2026-10-13
fix_commits: d09e5a5a, 4c481f74
fixed: [M-32-01, L-32-02, L-32-06]
still_open: [M-32-02, L-32-01, L-32-03, L-32-04, L-32-05, L-32-07]
---

# Phase 32: Security-, Bug- und Performance-Audit

**Umfang:** `git diff a632a35c..7006129d` (Basis = Elternteil von ed2908fc, dem
ersten Commit mit "(32-01)"; 22 Commits). Mit Planung 135 Dateien, 8502 Zeilen
dazu, 247 weg; ohne `.planning/` 123 Dateien (7014 dazu, 106 weg); ohne die
Rohdaten der Messung 32-03 bleiben 52 Dateien (4830 dazu, 106 weg), und die
sind gelesen: `php/lib/Search/{Provider,FilterProvider}.php`,
`php/lib/Service/{SearchFilters,SearchService}.php`,
`php/lib/Controller/PageController.php`,
`php/lib/Listener/LoadUnifiedSearchFiltersListener.php`,
`php/lib/AppInfo/Application.php`, `php/js/unified-search.js`,
`php/img/{app-white,findling}.svg`, 16 Kataloge unter `php/l10n/`,
`scripts/ci/team_folder_acl.sh`, `scripts/dev/measure_folder_filter.sh`, der
neue Schritt in `.github/workflows/deploy-harp.yml`, `docs/search-filters.md`,
`docs/store-listing.md`, die PHPUnit- und pytest-Dateien der Phase.
`ExAppService.php` ist seit der Basis unverändert. `backend/src` ist in der
Phase nicht berührt (D-30-08, D-32-06), und kein Fix dieses Audits berührt es.

Die Proben stehen als Regressionstests in `backend/tests/test_phase32_audit.py`
(913 Zeilen), in zwei Gruppen:

- **Quelltextproben, laufen immer** (9 Fälle): ein von Hand geschriebener
  Scanner, Zeichen für Zeichen mit Zuständen (Code, Zeilen- und
  Blockkommentar, beide Stringarten, Heredoc; im Skript zusätzlich Template-
  und Regex-Literale), auf dessen Tokens geprüft wird. Das ist bewusst ein
  anderes Werkzeug als `test_php_acl_boundary.py`, das Kommentare und Strings
  mit regulären Ausdrücken entfernt und Namen zählt. Jeder Scanner hat eine
  Positivkontrolle.
- **Instanzproben, ohne Instanz übersprungen** (128 Fälle): der Korpus
  manipulierter Filterwerte gegen die Dev-Instanz über die OCS-Route, als
  alice und bob, mit Log-, Orakel-, Paging-, Datums-, Tür- und
  Umbenennungsproben. Variablen und Saat stehen im Modulkopf.

**Wo gelaufen:** Quelltextproben lokal (Windows 11) und in CI python.yml; der
Instanzkorpus lokal gegen `findling-nextcloud` (http://localhost:8090,
Nextcloud 34.0.3, `php/` als Bind-Mount, Backend 1.4.2 als Host-Prozess auf
Stand HEAD). PHPUnit nur in CI. groupfolders ist auf der Dev-Instanz nicht
aktiv; Gruppenordner und Rechteregeln deckt der CI-Beweis aus 32-06 ab
(`scripts/ci/team_folder_acl.sh`, Integration 38339350216).

**Saat der Instanz:** alice besitzt `/Projekte/Plan.txt`,
`/Projekte/Unter/Tief.pdf`, `/Projekte2/Neben.txt`, `/Café32/Cafe.txt` (NFC),
`/Alt32/Umbenannt.txt`, `/Wurzel.txt` und den leeren Ordner `/Leer32`. bob
besitzt `/Geheim/Geheim.txt`, `/NurBob/NurBob.txt`, teilt `/Geteilt` mit alice
und hat die Freigabe von `/Weg` vor dem Lauf zurückgenommen. Jede Datei trägt
das Wort `auditwort32`. Positivkontrolle der Saat: alice sieht ohne Filter
genau sieben Dateien (ihre sechs und `Geteilt.txt`), bob seine vier.

## Security

### S1 Korpus manipulierter Filterwerte gegen die echte Instanz

Gefahren: `uv run python -m pytest -q tests/test_phase32_audit.py -rfs -p no:randomly`
mit den Variablen aus dem Modulkopf, am 13.10.2026. Jeder Wert läuft gegen
`findling` und gegen `findling-filter`. Erwartung je Wert vor dem Lauf in der
Tabelle `FOLDER_CASES` / `TYPE_CASES` festgehalten: die korrekt eingeschränkte
Menge oder die Treffer ohne Filter (USRCH-03), nie eine Datei aus
`{Geheim.txt, NurBob.txt, Weg.txt}`, nie HTTP 5xx.

| Gruppe | Werte | Ergebnis vor dem Fix | nach dem Fix |
|---|---|---|---|
| Traversal | `/../bob/files/Geheim`, `..%2F..%2Fbob` (einmal kodiert), `..%252F..` (zweimal kodiert), `..\..\bob\files\Geheim`, `/bob/files/Geheim`, `~bob/Geheim`, `/proc/self/root`, `..`, URL als Ordner | ungefiltert, kein Fremdtreffer | gleich |
| Eigene Wege | `/./Projekte/../Projekte` (`..` refused), `\Projekte\Unter` (der Kern macht `\` zu `/`: eingeschränkt auf Tief.pdf), `//Projekte//Unter`, `Projekte` ohne Slash, `/Projekte/` | wie erwartet | gleich |
| Steuerzeichen | `%00` hinten und mittig, `%0A`, `%1F`, `%7F` | ungefiltert | gleich |
| Unicode | NFC `/Café32`, NFD `/Café32`, Bidi U+202E hinten und vorn | NFC eingeschränkt; **NFD leere Gruppe: M-32-01**; Bidi ungefiltert | NFD eingeschränkt wie NFC |
| Punktsegmente | `.`, `/.`, `/Projekte/.`, `/./Projekte`, `/Projekte/./Unter`, `\Projekte\.\Unter` | **leere Gruppe: M-32-01** | ungefiltert |
| Länge | 4000 und 4001 Zeichen | ungefiltert | gleich |
| Fremd und weg | Ordner nur bei bob, nicht existent, zurückgenommene Freigabe `/Weg`, Datei statt Ordner `/Wurzel.txt`, `/Projekt` (Präfix ohne Trenner) | ungefiltert, kein Fremdtreffer | gleich |
| Rechte | empfangene Freigabe `/Geteilt` | nur Geteilt.txt | gleich |
| Grenzen | `/Projekte2` (Geschwister mit gleichem Präfix), leerer eigener Ordner `/Leer32`, `/`, `////`, `~`, `.versteckt32`, `/projekte` (andere Schreibung, Speicher unterscheidet Groß und Klein) | Neben.txt; leer; ungefiltert | gleich |
| types | `PDF`, ` pdf `, `,,pdf,,`, `pdf, text`, `pdf;text`, `pdf` 1000-mal, kyrillisches `рdf`, Vollbreite, JSON-Text, `pdf%00`, `archives`, `text` | wie erwartet (D-32-03) | gleich |
| Leer | `folder=`, `types=` | HTTP 400 des Kerns (D-32-01) | gleich |
| Array | `folder[]=`, `types[]=` | **HTTP 500 im Kern: L-32-01** | gleich |

Zählung: vor dem Fix 15 rot (zwölf Fälle M-32-01, je sechs auf beiden
Providern, die Logprobe wegen der Positivkontrolle selbst, siehe S2), nach dem
Fix **137 passed** in 88 s. Kein Lauf hat je eine Datei gezeigt, die alice
ohne Filter nicht sieht, und keiner endete in 5xx außer der Array-Form.

**Orakel** (`test_a_foreign_folder_and_a_folder_nobody_has_answer_alike`):
`/Geheim` (gibt es nur bei bob) und `/GibtEsNicht32` geben denselben Status und
dieselben Datei-IDs. Laufzeit, Median aus 11 abwechselnden Anfragen: 0,457
gegen 0,471 s (erster Lauf) und 0,439 gegen 0,525 s (zweiter Lauf), also
einmal so und einmal so herum. Bewertung: beide Werte gehen durch denselben
Weg (`Folder::get()` wirft `NotFoundException` im Baum von alice, ein Ordner
von bob ist dort genauso wenig vorhanden wie ein erfundener), der Unterschied
ist Rauschen. Ein Orakel über fremde Ordner gibt es nicht, weil der Ordner nur
im Baum des Fragenden aufgelöst wird.

**Versteckter Provider `findling-filter`:** anonym HTTP 401 (wie `findling`);
die Providerliste von alice nennt `findling` und nicht `findling-filter`;
ohne `types` und `folder` leere Gruppe ohne Backend-Aufruf (P5); mit Chip
dieselben Antworten wie `findling` in allen 59 Korpusfällen (Status und
Datei-IDs je Fall verglichen, 0 Abweichungen). Quelltextprobe
`test_the_filter_provider_decides_nothing_about_rights`: kein
`getFirstNodeById`, `isReadable`, `getUserFolder`, `SearchService`,
`ExAppService`, `IRootFolder`, Logger oder Datenbank in der Klasse, genau ein
Aufruf `$this->provider->search($user, $query)` mit unveränderten Argumenten.
**Fehlerpfad:** Backend nicht erreichbar (Port in `oc_ex_apps` auf einen
geschlossenen gestellt, danach zurück): `types=pdf`, `folder=/Projekte`,
`folder=/GibtEsNicht32` je HTTP 200 mit leerer Gruppe; Logzeilen siehe
L-32-02.

### S2 Logs

Gefahren: `test_no_log_line_carries_a_corpus_folder_or_the_term` über den
ganzen Korpuslauf, gelesen aus `nextcloud.log` des Containers (neue Zeilen
seit dem Laufbeginn) und aus dem Log des Backend-Prozesses
(`.dev/exapp.log`), gesucht nach allen Korpusordnern (auch NFD) und dem
Suchwort. Positivkontrollen: ein Login mit einem Markernamen und falschem
Passwort (der Kern schreibt "Login failed" als Warnung) und ein Marker im
Pfad einer Anfrage an das Backend (Access-Log von uvicorn), beide gefunden.
Ergebnis auf der Voreinstellung (Loglevel 2): **keine Zeile** mit einem
Korpuswert. Der erste Lauf war rot, weil die Positivkontrolle selbst über die
Suchroute lief und deren Adresse das Suchwort trägt; seitdem läuft sie über
`/ocs/v2.php/cloud/user`.

Zusätzlich gefahren (nicht im Korpus, weil sie die Instanz umstellen):

- Loglevel 0 für zwei Anfragen, danach zurück auf 2: die Debugzeile
  "Findling: the narrowing of the dialog was ignored" steht mit dem Feld
  `url` samt `term=` und `folder=` im Log. Die Zeile selbst trägt nichts.
- Backend nicht erreichbar: je Anfrage eine Warnung von `app_api` und eine von
  Findling, beide mit `url` samt Begriff und Ordner. Siehe **L-32-02**.
- Array-Form: der Kern schreibt einen Fehler (Level 3) mit `url`. Siehe
  **L-32-01**.

Quelltextprobe `test_no_log_call_of_the_phase_files_carries_a_term_a_folder_or_a_path`:
in Provider, FilterProvider, SearchService, SearchFilters, dem Listener und
PageController übergibt kein `->logger->...()` eine der Variablen `$term`,
`$folder`, `$path`, `$value`, `$raw`, `$query`, `$node`, `$scope`, `$entry`,
`$candidate`, `$filters`, `$filter`.

### S3 Quelltextproben und gefahrene Musterprüfungen

- **Eine Auflösung, eine Lesefrage:**
  `test_the_php_tree_asks_resolution_and_readability_exactly_once_each` zählt
  `->getFirstNodeById(` und `->isReadable(` über alle 59 Dateien unter
  `php/lib`: je genau einmal, beide in `Service/SearchService.php`.
  `test_php_acl_boundary.py` unverändert und grün (in jeder vollen Suite).
- **Kein Ordnerwert zum Container:** `ExAppService.php` kennt weder einen
  Namen noch einen String mit "folder" noch `scope`/`coordinates`; in
  `SearchService.php` wird `$filters->folder` genau einmal gelesen, und zwar
  als Argument von `scopeOf()`. Live gegengeprüft mit einem mitschneidenden
  TCP-Proxy vor dem Backend (P4): drei Ordnerläufe, kein Byte "Projekte",
  "Geheim", "Unter" oder "folder" in den Anfragen an den Container.
- **Skript ohne DOM-Schreibzugriff und ohne Netz:**
  `test_the_script_writes_nothing_into_the_page_and_asks_the_server_nothing`:
  keiner von 18 schreibenden DOM-Membern, keiner von 11 verbotenen Namen
  (`eval`, `Function`, `fetch`, `XMLHttpRequest`, Storage ...), von `document`
  nur `readyState` und `addEventListener`, und geschrieben werden nur die
  Eigenschaften `filters` (Filterkarte des Menüeintrags) und `folder` (der
  Parameter des Chips). `grep -n "innerHTML\|eval(\|new Function" php/js/unified-search.js`:
  kein Treffer.
- **Listener ohne Dienst:** keine `__construct`, genau ein `isLoggedIn()`.
- **CSP:** `curl -u alice:… /apps/files/`: Header `script-src
  'nonce-…'` und `script-src-elem 'strict-dynamic' 'nonce-…'`; das Tag von
  `/custom_apps/findling/js/unified-search.js` trägt denselben Nonce und steht
  hinter `core-unified-search.js`.
- **Seiten ohne Unified Search:** Login-Seite und öffentlicher Link (anonym
  und angemeldet als bob) laden das Skript nicht (curl, Zählung 0; Files als
  Kontrolle 1).
- **Legacy-Suche:** `unified_search.enabled=true` gesetzt, Dashboard und Files
  als alice per Playwright, danach entfernt: Skript geladen,
  `OCA.UnifiedSearch` fehlt, `legacy-unified-search` geladen, keine Meldung und
  kein `pageerror` aus dem Skript (nur die Warnung von viewer und der
  tiptap-Fehler von text, wie im Normalbetrieb gemessen).
- **Gedankenstriche:** `git diff a632a35c..HEAD | grep "^+" | LC_ALL=C.UTF-8 grep -cP "\x{2013}|\x{2014}"`
  ergibt 0; Positivkontrolle mit einer Probedatei mit U+2013 ergibt 1.
- **Workflows:** der neue Schritt in `deploy-harp.yml` schreibt nichts nach
  `GITHUB_ENV` (L-30-03 greift nicht), nutzt kein `grep -Eq` (L-31-07 greift
  nicht) und keine neue Action (`uses:` 0 in den hinzugefügten Zeilen); der
  eine `${{ }}`-Ausdruck in einem `run`-Block ist `matrix.server-version` /
  `matrix.runner`, beides Konstanten der Matrix in derselben Datei.
  `test_workflow_pins.py` und `test_unified_search_filter_steps.py`: 24 passed.
- **REUSE:** `uvx --from "reuse[charset-normalizer]" reuse lint`: 2693 / 2693,
  konform.
- **Store-Archiv:** `scripts/release/store-archive.sh stage-companion` lokal:
  `js/unified-search.js` (byte-gleich mit dem Repo),
  `lib/Search/FilterProvider.php`,
  `lib/Listener/LoadUnifiedSearchFiltersListener.php`, `img/app-white.svg`,
  `img/findling.svg` im Archiv. Nebenbei gesehen: das lokale Staging nimmt die
  ignorierte Markerdatei `js/.claude-active` mit; die Releases baut CI aus
  einem frischen Checkout, siehe `deferred-items.md`.
- **Kern-Interna und Nebenwirkung des Symbols** sind dokumentiert: die
  Abhängigkeit von `this` im Callback im Kopf von `unified-search.js` und in
  `docs/search-filters.md` ("One dependency on core internals"); die
  Nebenwirkung von `findling.svg` auf Tab- und Homescreen-Symbol im Kommentar
  der SVG-Datei, in THIRD-PARTY.md und in 32-07-ABNAHME.md, nicht im
  CHANGELOG (**L-32-07**).

## Bugs

- **Paging im Ordner** (`test_the_next_page_of_a_folder_stays_in_the_folder`):
  `folder=/Projekte&limit=1` liefert einen Treffer und einen Cursor, die
  zweite Seite mit dem Cursor bleibt im Ordner, beide zusammen sind genau
  Plan.txt und Tief.pdf. Grün.
- **Ordner plus Datum, Typ plus Datum**
  (`test_a_folder_and_a_type_go_together_with_the_date_of_the_core`):
  letzte 30 Tage gibt die Menge, 2020 gibt nichts, für beide Chips. Grün.
- **Tür mit types** (`test_the_door_of_a_type_chip_carries_the_type_and_never_the_folder`):
  `types=text&limit=2` führt zur Ergebnisseite mit `types=text`, die Tür eines
  Ordnerchips nennt den Ordner nicht. Grün.
- **Legacy-Suche:** siehe S3, ohne Skriptfehler.
- **Umbenennen während offener Suche**
  (`test_a_folder_renamed_while_the_chip_stands_is_no_folder_any_more`):
  `/Alt32` per WebDAV nach `/Neu32`: der alte Wert gibt die Treffer ohne
  Filter, der neue nur Umbenannt.txt; danach zurückbenannt. Ein gelöschter
  Ordner im Chip ist derselbe Fall wie "nicht existent" im Korpus. Verhalten
  nach USRCH-03, siehe **L-32-03**.
- **Index-Waisen (Befund aus 32-07).** Der Abgleich der Dev-Instanz meldete am
  13.10. um 01:08 `seen=1488 stale=0 missing=0`, obwohl die 1011 Messdateien
  aus 32-03 heute in `oc_filecache` fehlen. Ursache: die Reihenfolge, kein
  Fehler des Abgleichs. Die Messdateien wurden 01:02:24 bis 01:08:16
  indexiert (`indexed_at` in state.db), der Abgleich lief 01:08:16 bis
  01:08:19 (Stempel der Tabelle `reconcile`), und im Backend-Log stehen direkt
  davor die Abrufe `files/1720` bis `files/1740` mit HTTP 200: Die Dateien
  lebten noch, `seen=1488` zählt sie mit. Gelöscht wurden sie erst danach in
  der Messung 32-03 (Commit 060d637b um 02:09), samt Papierkorb vor dem Cron.
  Der nächste Abgleich wäre frühestens 24 Stunden später fällig gewesen.
  **Positivkontrolle:** Stempel der Tabelle `reconcile` um 49 Stunden
  zurückgesetzt (zweimal das Intervall plus eins), der laufende Prozess nahm
  den Abgleich beim nächsten Takt auf: `reconcile round queue_busy, ...
  missing=1011`, danach alle 1011 Zeilen mit `deleted_at`, 0 Dokumente in
  Tantivy (vorher 1011). Der Abgleich erkennt solche Waisen also
  grundsätzlich; bis zum nächsten Lauf stehen sie im Index, siehe
  **L-32-05**. Dabei aufgefallen und mit Positivkontrolle im selben Lauf
  belegt: Dokumente eines gelöschten Nutzers bleiben für immer, **M-32-02**.

## Befunde

### M-32-01 (MEDIUM): Ein Punktsegment oder die NFD-Schreibung im Ordner ergibt eine leere Gruppe

- **Ort:** `php/lib/Search/Provider.php:413` bis `427` (`folderOf()` vor dem
  Fix) und `php/lib/Service/SearchService.php` (`scopeOf()`,
  `readableFile($scope ?? $userFolder, ...)`); Ursache im Kern:
  `Folder::get()` normalisiert über `PathHelper::normalizePath()`
  (`lib/private/Files/Utils/PathHelper.php:36` bis `56`, NC 34.0.3), das `\`
  zu `/` macht und doppelte Slashes faltet, aber `.`-Segmente und die
  Unicode-Form stehen lässt; `Filesystem::isValidPath()` verwirft nur `..`.
- **Beleg (gefahren, Instanz):** `folder=.`, `/.`, `/Projekte/.`,
  `/./Projekte`, `/Projekte/./Unter`, `\Projekte\.\Unter` und NFD
  `/Café32` je HTTP 200 mit **leerer Gruppe** auf beiden Providern. Der Wert
  löst zu einem Ordnerknoten auf, dessen Pfad so geschrieben ist wie der Wert
  (`/alice/files/Projekte/.`), und `getFirstNodeById()` unter diesem Knoten
  findet keine Datei, weil jede Datei den kanonischen Pfad trägt.
- **Warum MEDIUM:** USRCH-03 verspricht, dass ein unbekannter oder
  manipulierter Wert nie zu einer leeren Suche führt. Kein Fremdtreffer, kein
  Fehler, keine Auskunft über Fremdes; nur gebaute Werte erreichen den Weg
  (die Ordnerauswahl liefert kanonische Pfade). Einstufung nach Plan: falsches
  Ignorieren.
- **Fix (d09e5a5a):** `folderOf()` setzt den Wert in NFC (Form des Filecache;
  `\Normalizer`, das Nextcloud als Polyfill mitliefert, mit Rückfall auf den
  Rohwert) und liest einen Wert mit einem `.`-Segment (Trenner `/` und `\`)
  als keinen Ordner. Namen mit Punkt am Anfang (`.versteckt`) und `...`
  bleiben Namen. Regression: ProviderTest (NFD wird NFC, zwei Punktnamen
  bleiben, sieben Punktschreibungen ergeben `none()`), Korpusfälle jetzt
  streng (`(UNFILTERED,)` bzw. nur Cafe.txt).

### M-32-02 (MEDIUM, Owner-Frage): Dokumente eines gelöschten Nutzers bleiben für immer im Index

- **Ort:** `backend/src/findling/worker/reconcile.py:398` bis `410`
  (`run_once` läuft nur die Mounts, die `files.mounts()` listet), dazu
  `php/lib/BackgroundJobs/ScanRecountJob.php:54` bis `59` und
  `docs/admin-page.md:124` bis `128`, die das als bewusste Grenze "nach
  heutigem Stand" nennen. Kein Listener für das Löschen eines Nutzers.
- **Beleg (gefahren, Instanz, mit Positivkontrolle im selben Abgleich):**
  Nutzer carol (ohne Skelettdateien) mit `/Carol32.txt` angelegt und
  indexiert (Datei 2970, Storage 14); alice legt `/Kontrolle32/k.txt` an
  (Datei 2972, Storage 12), indexiert. Dann `/Kontrolle32` per WebDAV
  gelöscht und der Papierkorb von alice vor dem Cron geleert (der Ablauf aus
  32-03), und `occ user:delete carol`. Abgleich fällig gemacht: `reconcile
  round walked, mounts=5 ... missing=1`. Danach Datei 2972 mit `deleted_at`
  und 0 Dokumenten in Tantivy (die Positivkontrolle), Datei 2970 ohne
  `deleted_at` und mit 1 Dokument, Storage 14 nicht mehr in `oc_mounts`.
- **Wirkung:** Kein Fremdtreffer: ein solches Dokument scheitert an der
  Vorauswahl (kein Eintrag mehr im Filecache) bzw. am Recheck. Aber der Index
  wächst mit jedem gelöschten Nutzer und jedem abgeschalteten Mount, und jedes
  verwaiste Dokument, das vor den Treffern eines Nutzers rangiert, belegt
  einen Kandidatenplatz: im Ordnermodus einen der 1200 Ränge, die 32-03
  gemessen hat (`FOLDER_MAX_ROUNDS` 12 mal 100), sonst einen Platz der
  Überabfrage. Fallen die Treffer eines Ordners dadurch hinter Rang 1200,
  bleibt die Gruppe leer. Genau die Bedingung, die der Auftrag als
  mindestens MEDIUM nennt.
- **Warum nicht gefixt:** Der Fix (Dokumente von Storages löschen, die aus
  der Mountliste verschwunden sind, oder ein Listener auf das Löschen eines
  Nutzers, der die Löschaufträge einreiht) berührt den Abgleich in
  `backend/src` oder die Queue-Semantik; das verbietet D-30-08/D-32-06 dieser
  Phase. Dazu ist die Grenze eine bewusste, dokumentierte Entscheidung früherer
  Phasen (Zähler und Nenner der Statusseite). **Owner-Frage:** Soll ein
  eigener Plan (Phase 36 Launch-Härtung oder ein Einschub) verwaiste Storages
  aufräumen, und wenn ja, mit welcher Karenz (ein abgeschalteter Mount kann
  zurückkommen)?
- Auf der Dev-Instanz bleibt das eine Dokument von carol (Datei 2970) als
  Beleg stehen.

### L-32-01 (LOW): Die Array-Form eines Filters endet im Kern mit HTTP 500

- **Ort:** Kern, `lib/private/Search/SearchComposer.php:294` und `304`
  (`buildFilter(string $name, string $value, ...)`), NC 34.0.3.
- **Beleg:** `types[]=pdf` und `folder[]=/Projekte` auf beiden Providern:
  HTTP 500, im Log ein TypeError (Level 3) mit `url`. Gegenprobe ohne Findling:
  der Files-Provider des Kerns antwortet auf `path[]=/Projekte` und
  `term[]=x` genauso mit 500; `path=/Projekte` gibt 200.
- **Einordnung:** Findling wird nie erreicht; dasselbe gilt für jeden
  String-Filter jedes Providers, auch für den Suchbegriff. Die Filtereinträge
  senden nie ein Array.

### L-32-02 (LOW): Suchbegriff und Ordner stehen bei einer Störung im nextcloud.log

- **Ort:** Kern (jede Logzeile trägt das Feld `url` der laufenden Anfrage),
  dazu die Warnungen von AppAPI ("Error during request to ExApp") und
  `ExAppService.php:924` ("Findling: backend unreachable").
- **Beleg:** siehe S2. Auf Loglevel 2 im Normalbetrieb keine Zeile (Korpus
  mit Positivkontrolle); bei nicht erreichbarem Backend je Anfrage zwei
  Warnungen mit `term=` und `folder=` in `url`; auf Loglevel 0 die Debugzeilen
  ebenso.
- **Einordnung:** Für den Suchbegriff gilt das seit Phase 1; Phase 32 fügt den
  Ordner hinzu, weil der Kern Filter als Parameter der Adresse schickt.
  Findling schreibt beides nie selbst, und die Zeile von AppAPI entsteht auch
  ohne die von Findling.

### L-32-03 (LOW): Ein umbenannter oder gelöschter Ordner unter einem stehenden Chip zeigt ungefilterte Treffer

- **Ort:** `SearchService::scopeOf()` (jeder Fehlschlag ist die Suche ohne
  Ordner), Chiptext im Kern.
- **Beleg:** Bugs, Umbenennungsprobe.
- **Einordnung:** USRCH-03 und T-32-06 verlangen genau das (ein nicht
  auflösbarer Ordner antwortet wie keiner, ohne Orakel); der Chip trägt den
  alten Namen, weil der Kern ihn so stehen lässt.

### L-32-04 (LOW): Andere Groß- und Kleinschreibung auf einem Speicher, der sie nicht unterscheidet

- **Ort:** derselbe Mechanismus wie M-32-01: löst ein Speicher `/projekte`
  zu `Projekte` auf, trägt der Ordnerknoten den Pfad in der Schreibweise des
  Werts, und der Recheck darunter fände nichts.
- **Beleg:** auf der Dev-Instanz nicht nachstellbar (lokaler Speicher
  unterscheidet die Schreibweise: `/projekte` gibt die Treffer ohne Filter);
  hergeleitet aus `PathHelper::normalizePath()`.
- **Einordnung:** nur mit einem gebauten Wert und nur auf solchen externen
  Speichern (SMB, manche S3-Varianten); die Ordnerauswahl liefert den
  kanonischen Pfad.

### L-32-05 (LOW): Waisen nach Löschen mit sofort geleertem Papierkorb bis zum nächsten Abgleich

- **Ort:** Ordnerlöschung über `SubtreeExpandJob` (Cron), Abgleich
  (`RECONCILE_MIN_INTERVAL_HOURS` 24, Stunde 2, Notausgang nach 48 Stunden).
- **Beleg:** Positivkontrolle oben (missing=1011, alle entfernt) und im Lauf
  von M-32-02 (missing=1).
- **Einordnung:** Liegen bleiben die Dokumente höchstens bis zum nächsten
  Abgleich; in der Zeit belegen sie Kandidatenplätze wie in M-32-02, zeigen
  sich aber nie als Treffer. Der Weg ist älter als Phase 32 und im Docblock
  von `FileEventListener::queueDeletion` so beschrieben.

### L-32-06 (LOW): Die PHPUnit-Doppel zählten die Abfragen des Ordnermodus nicht

- **Ort:** `php/tests/Unit/SearchServiceTest.php`.
- **Beleg:** P2 verlangt den Beleg über die Doppel und über das Query-Log;
  die Fälle aus 32-02 konfigurieren `getMountsForUser`, `getByFileId` und
  `getByFileIds` nur mit `method()`, ohne `expects()`.
- **Fix (4c481f74):** ein Fall über den längsten Ordnerlauf (alle
  `FOLDER_MAX_ROUNDS` Runden, jeder Kandidat außerhalb): genau ein
  `get()`, ein `getMountsForUser`, ein `getByFileId`, `FOLDER_MAX_ROUNDS`-mal
  `getByFileIds` und `searchCandidates`, kein Snippet, kein Recheck. CI php.yml
  38385967900: 666 Tests grün (vorher 661).

### L-32-07 (LOW): Das neue Tab- und Homescreen-Symbol steht nicht im CHANGELOG

- **Ort:** `CHANGELOG.md` (Phase 32 nennt nur die Filter).
- **Einordnung:** Die Nebenwirkung von `findling.svg` ist dokumentiert
  (SVG-Kommentar, THIRD-PARTY.md, Abnahmeprotokoll) und vom Owner angenommen;
  ob sie eine Zeile im Releasetext bekommt, entscheidet der Owner beim Entwurf
  des Release- und Store-Texts (Owner-Regel "Entwurf vor Release zeigen",
  REL-05).

## Performance

Gemessen am 13.10.2026 zwischen 10:47 und 11:56 auf dem Entwicklungsrechner:
Windows 11 Pro 10.0.26200, Intel Core i5-1335U, 16 GB RAM; Dev-Instanz
`findling-nextcloud` (Nextcloud 34.0.3, SQLite, APCu), Backend 1.4.2 als
Host-Prozess. Korpus für P1, P2 und P5: derselbe wie 32-03
(`measure_folder_filter.sh setup`, Begriff `ordnermessung32`, 1000 Dateien
außen auf Rang 1 bis 1000, 10 Dateien in `/Messung32/Innen/Tief` auf Rang 1001
bis 1010, eine in `/Messung32/Einzeln` auf Rang 1011), diesmal unter alice;
alle 1011 indexiert (state.db), danach abgeräumt (Cron vor dem Papierkorb,
alle 1011 mit `deleted_at`, 0 Dokumente in Tantivy).

Jedes Verfahren weicht von 32-03 ab: 32-03 maß mit `curl -w time_total` und
einem App-Passwort; hier misst der Browser (Playwright 1.63, Chromium
headless), die Abfragen über eine angemeldete Sitzung, die Datenbank über das
Query-Log des Kerns, der Body über einen mitschneidenden Proxy.

| Nr. | Messgröße | Wert | Vergleich | Urteil |
|---|---|---|---|---|
| P1 | ohne Ordner, Limit 5 / 10 | Median 80,4 / 72,2 ms | 32-03 D: 60 / 67 ms (+34 / +8 %) | in Ordnung, Begründung unten |
| P1 | weiter Ordner `/Messung32`, Limit 5 / 10 | Median 79,7 / 77,5 ms | wie ohne Ordner (erste Runde trifft) | in Ordnung |
| P1 | enger Ordner `/Messung32/Innen`, Limit 5 / 10 | Median 144,8 / 157,7 ms | 32-03 D: 134 / 129 ms (+8 / +22 %) | in Ordnung |
| P1 | engster Ordner `/Messung32/Einzeln`, Limit 5 / 10 | Median 141,5 / 148,3 ms | 32-03 D: 127 / 122 ms (+11 / +22 %) | in Ordnung |
| P1 | Mehrkosten eng gegen ohne Ordner | +64 ms (Limit 5), +86 ms (Limit 10) | 32-03: +74 / +62 ms | in Ordnung |
| P2 | Abfragen je Ordnerlauf (eng, 11 Runden) | `getByFileIds` 11 (eine je Runde), `getByFileId` 1, `Folder::get` 1, `oc_mounts` 1 (Aufbau des Dateisystems durch den Kern, `getMountsForUser` von Findling trifft dessen Zwischenspeicher), `readableFile` 1 | ohne Ordner: `getByFileIds` 1, `readableFile` 5, `oc_mounts` 1 | in Ordnung; PHPUnit-Zählung fehlte: L-32-06, gefixt |
| P3 | Kosten des Skripts je Seite | 11 880 Byte, gzip 4 428, kalt 4 728 übertragen; warm 0 (`Cache-Control: max-age=15778463, immutable`, Cachebuster `?v=`); zwei Anfragen kalt (Skript und `l10n/de_DE.js`), warm keine; CPU-Selbstzeit Median 0, höchstens 0,70 ms; erste bis siebte Registrierung 0,5 bis 2,3 ms | Login und öffentlicher Link: Skript nicht geladen | in Ordnung |
| P4 | Body an `/search` und `/snippets` ohne Filter | 7 Anfragen (vier Suchen: schlicht, Limit 10, Datum, nur Dateiname), SHA-256 je Body gleich zwischen HEAD, Basis a632a35c und HEAD erneut | byte-gleich | in Ordnung |
| P5 | Aufrufe des Containers je Dialogsuche | ohne Ordner 1 `/search` + 1 `/snippets`; weiter Ordner 1 + 1; enger und engster Ordner 11 + 1; sieben Anfragen von Menüeinträgen ohne Chip 0 | Obergrenze 12 (`FOLDER_MAX_ROUNDS`) | in Ordnung |

Verfahren im Einzelnen:

- **P1:** angemeldet als alice auf `/settings/user`; die Adresse ist die, die
  der Dialog selbst sendet (vorher mit dem Dialog mitgeschnitten:
  `.../providers/findling/search?term=ordnermessung32&from=%2Fapps%2Fdashboard%2F`,
  für Chips `findling-filter` mit `folder=` wie in 32-07). Abgeschickt per
  `fetch` aus der Seite mit Request-Token, gemessen über den
  `PerformanceResourceTiming`-Eintrag des Browsers (`responseEnd - startTime`),
  je Variante ein verworfener Aufwärmaufruf, dann 20 Runden, jede Runde jede
  Variante einmal in abwechselnder Reihenfolge; drei solche Reihen, gepoolt
  n = 60, Median als Rangwert an `ceil(0,5 n)` wie in 32-03.
  **Abweichung über 25 Prozent:** ohne Ordner bei Limit 5 (80,4 gegen 60 ms).
  Die drei Einzelreihen gaben 72,8 / 80,4 / 97,9 ms, und 32-03 selbst maß
  dieselbe ungefilterte Abfrage je nach Variante mit 57 bis 79 ms (Basis
  0,079 s); der Browser misst zusätzlich seinen Netzweg und die
  Sitzungsprüfung statt eines App-Passworts. Die Ordnervarianten liegen
  innerhalb von 25 Prozent, und die Mehrkosten des Ordnermodus stimmen mit
  32-03 überein.
- **P2:** `query_log_file` und `query_log_file_backtrace` je Anfrage gesetzt
  und danach entfernt, Abfragen über die Rückverfolgung den Methoden von
  `SearchService` zugeordnet. Daneben je Containeraufruf eine Abfrage auf
  `oc_ex_apps` von AppAPI (ohne verteilten Cache auf der Dev-Instanz).
- **P3:** Chrome DevTools Protocol, Profiler mit 50 µs Abtastung über sechs
  Ladevorgänge des Dashboards, der erste nach `Network.clearBrowserCache`;
  die Registrierungszeiten über einen Haken an
  `OCA.UnifiedSearch.registerFilterAction`.
- **P4:** TCP-Proxy auf Port 10036 vor dem Backend (Port in `oc_ex_apps`
  umgestellt und zurück). Basis: die fünf in Phase 32 geänderten Dateien unter
  `php/lib` per `git show a632a35c:…` eingesetzt, 70 s auf OPcache gewartet,
  Stand per SHA-256 im Container geprüft (Positivkontrolle: `findling-filter`
  antwortet auf der Basis mit 500, auf HEAD mit 200), danach die Dateien
  byte-gleich zurück.
- **P5:** Zählung der `POST /search` und `/snippets` im Access-Log des
  Backends je Verbindung (eine Verbindung je PHP-Anfrage).

## LOW-Entscheidungen

| Befund | Entscheidung | Grund |
|---|---|---|
| L-32-01 Array-Form, 500 im Kern | **accept**, dokumentiert (4c481f74) | Findling wird nicht erreicht, der Kern antwortet bei seinen eigenen Filtern genauso; ein Fix gehört in nextcloud/server. Eine Meldung dort ist eine Owner-Entscheidung. |
| L-32-02 Begriff und Ordner im Log bei Störung | **fix** als Dokumentation (4c481f74) | `docs/privacy.md` nennt, wann der Kern die Adresse einer Suche neben eine Zeile schreibt; Findling selbst schreibt beides nie, und die Zeile von AppAPI bliebe auch ohne die eigene. |
| L-32-03 umbenannter Ordner unter dem Chip | **accept**, dokumentiert (4c481f74) | verlangt von USRCH-03 und T-32-06; `docs/search-filters.md` nennt den Fall. |
| L-32-04 Groß- und Kleinschreibung | **accept** | nur gebaute Werte auf Speichern ohne Unterscheidung; Zielphase 36 (Launch-Korpus mit externem Speicher). |
| L-32-05 Waisen bis zum nächsten Abgleich | **accept** | Abgleich belegt (missing=1011 und missing=1, alle entfernt); höchstens ein Tag, nie ein Treffer. |
| L-32-06 PHPUnit zählte nicht | **fix** (4c481f74) | ein Fall, CI 666 Tests grün. |
| L-32-07 Symbol nicht im CHANGELOG | **accept** | Releasetext entsteht mit dem Owner (REL-05). |

## Status nach dem Fix-Lauf (13.10.2026)

- 0 CRITICAL, 0 HIGH. M-32-01 gefixt (d09e5a5a). **M-32-02 offen als
  Owner-Frage** (verwaiste Storages, Fix nur in `backend/src`), deshalb
  `status: issues_found`. LOW: L-32-02 und L-32-06 gefixt, die übrigen fünf
  entschieden (Tabelle oben).
- Commits: 6ec32be7 (Audit-Proben), d09e5a5a (M-32-01), 4c481f74 (L-32-06 und
  Dokumentation L-32-01/02/03).
- Lokal vor jedem Commit aus `backend/` mit `PYTHONUTF8=1`: ruff check, ruff
  format --check, pyright (latest) 0 Fehler, vulture ohne Befund,
  `node --check php/js/unified-search.js`, `php -l` über die geänderten
  PHP-Dateien per `php:8.3-cli`, volle Suite je **5637 passed, 158 skipped**
  (vor dem Audit 5628 passed, 30 skipped; dazu 9 Quelltextproben und 128
  übersprungene Instanzproben). `test_php_acl_boundary.py` unverändert und
  in jeder Suite grün.
- Baumhash: `PHP_TREE_HASH_TODAY` a54f3104…aad2 (d09e5a5a, Journal "Plan
  32-08, Befund M-32-01"), dann 5cb3e48f…8fb2 (4c481f74, Journal "Plan 32-08,
  Befund L-32-06"); `PHP_FILES_TODAY` bleibt 97.
- CI auf 4c481f74 (Push `7006129d..4c481f74`), alle per `gh run watch
  --exit-status`: PHP and store metadata gates **38385967900** (PHPUnit 666
  Tests), Python gates 38385966880, HaRP deploy 38385966780, Integration
  38385966737, Resilience 38385967215, Security scans 38385967351, OpenSSF
  Scorecard 38385966865, Multi-arch image 38385966954.

## Was gegengeprüft wurde, nicht nur gelesen

| Prüfung | Verfahren (anders als die Umsetzung) | Ergebnis |
|---|---|---|
| Traversal, Fremdordner, Freigaben | Korpus gegen die echte Instanz mit zweitem Nutzer, Freigabe und zurückgenommener Freigabe (die Baupläne nutzten PHPUnit-Doppel und die CI-Proben) | nie ein Fremdtreffer; M-32-01 gefunden |
| Orakel | Status, IDs und Laufzeit, Median aus 11 abwechselnden Anfragen | gleich, Laufzeit Rauschen |
| Logs | Instanz- und Backend-Log mit zwei Positivkontrollen; Loglevel 0 und Backendausfall gefahren | Normalbetrieb sauber; L-32-02 |
| Rechtegrenze im Quelltext | eigener Zustandsautomat statt regulärer Ausdrücke | eine Auflösung, eine Lesefrage |
| Ordnerwert zum Container | Tokens von ExAppService und mitschneidender Proxy | kein Ordnerwert |
| Skript | Tokens des Skripts, CSP-Header, Legacy-Suche im Browser | kein DOM-Schreibzugriff, Nonce, keine Fehler |
| Waisen | Zeitstempel aus state.db, Tabelle `reconcile` und Backend-Log; Abgleich fällig gemacht | Ursache die Reihenfolge; Abgleich findet Waisen; M-32-02 gefunden |
| Performance | Browser-Timing, Query-Log, CDP-Profiler, Proxy-Mitschnitt gegen Basis | P1 bis P5 in Ordnung |
| Trennschärfe | Gegenproben unten | jede rot |

### Gegenproben

Quelltextproben (Skript im Scratch-Verzeichnis: je Probe genau eine
Ersetzung, die genannte Auswahl von `test_phase32_audit.py`, danach die Datei
aus der Sicherung zurück und `filecmp` gleich, bei allen `restored
equal=True`):

| Probe | Eingriff | rot |
|---|---|---|
| G1 | `FilterProvider.php`: zusätzliche `->getFirstNodeById(1)` | 2 (eine Auflösung; Provider ohne Rechte) |
| G2 | `ExAppService.php`: Konstante `'folder'` | 1 |
| G3 | `SearchService.php`: `scopeOf()` loggt `['f' => $folder]` | 1 |
| G4 | `SearchService.php`: `$filters->folder` ein zweites Mal gelesen | 1 |
| G5 | `FilterProvider.php`: `search($user, clone $query)` | 1 |
| G6 | `unified-search.js`: `document.body.innerHTML = ''` | 1 |
| G7 | `unified-search.js`: Funktion mit `window.fetch('/x')` | 1 |
| G8 | Listener: leere `__construct` | 1 |

Fix M-32-01, live auf der Instanz (je eine Hälfte zurückgenommen, 75 s auf
OPcache gewartet, Korpusfälle gefragt, Datei byte-gleich zurück):

| Probe | Eingriff | rot |
|---|---|---|
| F1 | ohne die Regel für Punktsegmente | alle fünf Punktfälle wieder leer, NFD grün |
| F2 | ohne die NFC-Komposition | NFD wieder leer, die Punktfälle grün |
| nach dem Zurücklegen | | alle grün |
