---
phase: 09-eigene-ergebnisseite
plan: 06
subsystem: ui
tags: [navigation, info-xml, appstore-schema, unified-search, attribution, gate-c, mdi]

requires:
  - phase: 09-eigene-ergebnisseite
    provides: "09-04: die Route findling.page.index und der Parametervertrag der Seite"
  - phase: 09-eigene-ergebnisseite
    provides: "09-05: php/templates/search.php, php/css/search.css, php/js/search.js und die zwei Dialog-Strings in beiden Katalogen"
  - phase: 09-eigene-ergebnisseite
    provides: "09-UI-SPEC.md, approved: Einstiegspunkt aus der Unified Search, Verbote mit [G], die drei neuen MDI-Namen"
provides:
  - php/img/app.svg, das Symbol des Navigationseintrags
  - Der Navigationsblock in php/appinfo/info.xml, live geprueft gegen die laufende Instanz
  - Der Einstiegs-Eintrag am Ende der Findling-Gruppe, ohne fileId-Attribut, erkennbar an seiner Zieladresse
  - THIRD-PARTY.md mit zwoelf Symbolnamen, beiden Orten von magnify und einem Pruefbefehl, der beide Schreibweisen findet
  - Gate C ueber sechs Dateien, plus zwei Aussagen ueber das Seitenskript
affects: [09-07, 09-08]

tech-stack:
  added: []
  patterns:
    - "Ein zweiter Ort fuer dasselbe Symbol ist eine byte-identische Kopie und keine zweite Datei mit eigenem Inhalt: cmp ist die Zusicherung, und die Lizenzfrage bleibt eine"
    - "Der Einstiegs-Eintrag wird nach dem Bau der Eintraege angehaengt, also zaehlt er nie gegen das Limit, und die Antwortform bleibt die paginierte"
    - "Ein Gate, das Dateien dazubekommt, bekommt sie in die Quellenliste und nicht in die Sondertests: der Kommentar nennt die Tests, die bewusst stehen bleiben"
    - "Ein Pruefbefehl in einer Attributionsdatei muss das finden, was wirklich dasteht: die Pfaddaten der Seite stehen in PHP-Variablen und nicht in einem d-Attribut"

key-files:
  created:
    - php/img/app.svg
  modified:
    - php/appinfo/info.xml
    - THIRD-PARTY.md
    - php/lib/Search/Provider.php
    - php/tests/Unit/ProviderTest.php
    - backend/tests/test_admin_ui_contract.py
    - docs/testing.md

key-decisions:
  - "Der Navigationsblock steht am Dateiende hinter dem Einstellungsblock, die eine vom Store-Schema erlaubte Stelle; gegen den gepinnten appstore-Commit belegt statt angenommen"
  - "php/img/app.svg ist eine byte-identische Kopie von app-dark.svg, kein zweites Symbol und keine zweite Lizenzfrage"
  - "Der Einstiegs-Eintrag traegt kein fileId-Attribut und ist an seiner Zieladresse erkennbar, nicht am fehlenden Attribut"
  - "Gate C liest sechs Dateien, die drei Sondertests der Verwaltungsseite bleiben woertlich auf admin.js, und das Seitenskript bekommt zwei eigene Aussagen ueber die Abwesenheit derselben Marker"
  - "Der Pruefbefehl von THIRD-PARTY.md matcht auf das fuehrende M eines Pfades statt auf d=\", weil search.php keine d-Attribute hat und id=\" auf d=\" endet"
  - "Die zwoelf Verhalten von docs/testing.md bleiben zwoelf; die drei Verhalten aus Phase 9 stehen in einer eigenen Tabelle darunter"

patterns-established:
  - "Stand-in-Welt fuer eine Provider-Klasse: die OCP-Namen als Doubles im echten Namensraum, die echten Wertklassen per require, php:8.2-cli im Container"

requirements-completed: [UI-01, UI-03]

duration: 40min
completed: 2026-09-09
---

# Phase 9 Plan 06: Die Seite wird auffindbar Summary

**Die Ergebnisseite hat ab jetzt zwei Wege hinein, das App-Menue mit eigenem Symbol und den letzten Eintrag der Findling-Gruppe im Suchdialog, und der zweite ist ausdruecklich kein Treffer: er traegt keine fileid und ist an seiner Adresse erkennbar, nicht an dem, was ihm fehlt.**

## Performance

- **Duration:** rund 40 min
- **Tasks:** 3, alle autonom, kein Checkpoint
- **Files:** 7 (1 neu, 6 geaendert)

## Accomplishments

- **`php/img/app.svg`, byte-identisch mit `app-dark.svg`** (`cmp` still, beide Blobs mit derselben md5 im Objektspeicher). Damit findet der Symbolsucher des Servers eine Datei: die Navigation der laufenden Instanz meldet jetzt `"icon":"/custom_apps/findling/img/app.svg"` statt des Standardsymbols des Cores.
- **Der Navigationsblock in `php/appinfo/info.xml`**, am Dateiende hinter dem Einstellungsblock, in einer Zeile wie die drei Bloecke ueber ihm. Live gegen die Instanz geprueft: `NavigationManager` liefert fuer `testuser` den Eintrag `{"id":"findling","order":10,"href":"/index.php/apps/findling/","icon":"/custom_apps/findling/img/app.svg","type":"link","name":"Findling"}`.
- **Die Store-Validierung ist gefahren und nicht nur die Pin-Pruefung.** `scripts/dev/validate_info_xml.sh php/appinfo/info.xml` laeuft die beiden Stufen im Container und meldet `passes the store path, transform then schema`. Zusaetzlich wurde die Ausgabe von `pre-info.xslt` angesehen: `<settings/>` kommt geleert heraus, `<navigations>` mit allen sechs Kindern woertlich. Der Satz im Kommentar ist damit belegt und nicht behauptet.
- **`THIRD-PARTY.md` fuehrt zwoelf Symbolnamen**, `magnify` mit beiden Orten und die drei neuen mit ihrer Stelle in `search.php`. Der Pruefbefehl wurde gefahren: die zwoelf Pfaddaten dieses Repositoriums sind zeichengleich mit den zwoelf `svg/<name>.svg` des gepinnten Commits `9e04201d…` (`diff` ueber beide sortierten Listen, kein Unterschied). Damit ist **DI-09-01 geschlossen**.
- **Der Einstiegs-Eintrag im Provider**, angehaengt nach dem Bau der Eintraege, nur bei paginierter Antwort und mindestens einem genehmigten Treffer, mit dem uebersetzten Titel, der Unterzeile, `icon-search`, leerem Vorschaubild und einer Adresse aus Suchbegriff und, falls gesetzt, `names=1`. Kein `page`, kein `cursors`, kein `fileId`.
- **Gate C liest sechs Dateien statt drei**, mit derselben Zuordnung Datei zu Scanner, einer Existenzpruefung ueber sechs Pfade und zwei neuen Aussagen ueber das Seitenskript: keiner der vier Poll-Marker, kein `preventDefault`. Beide mit schmutzigem Selbstmuster im selben Test.
- **`docs/testing.md`** beschreibt Gate C jetzt ueber sechs Dateien und nennt die zwei neuen Aussagen; die drei Verhalten aus Phase 9 (geteilter Recheck-Dienst, Highlight-Zerleger, URL-Pruefung des Controllers) stehen als Nummern 13 bis 15 in einer eigenen Tabelle unter den zwoelf.

## Task Commits

1. **Task 1: Symbol, Navigationseintrag und Attribution** - `d625d86` (feat)
2. **Task 2: Der Einstiegs-Eintrag im Suchdialog** - `57982ce` (feat)
3. **Task 3: Gate C nimmt die drei Seitendateien auf** - `474bf5d` (test)

## Verification

| Pruefung | Ergebnis |
|---|---|
| `cmp php/img/app.svg php/img/app-dark.svg` | gleich; auch die beiden Git-Blobs (md5 `acfca30b…` je) |
| `git ls-files --eol php/img/` | beide `i/lf w/lf`, also kein Zeilenende-Drift zwischen Original und Kopie |
| Reihenfolge in `info.xml`: Zeile von `settings` gegen `navigations` | 263 gegen 288, also hinter dem Einstellungsblock |
| `grep -c 'findling.page.index' php/appinfo/info.xml` | 1 |
| `scripts/dev/validate_info_xml.sh --check-pins` | gruen, ein Pin an zwei Stellen |
| `scripts/dev/validate_info_xml.sh php/appinfo/info.xml` | gruen, Transform und Schema |
| `pre-info.xslt` ueber die Datei | `<settings/>` geleert, `<navigations>` mit sechs Kindern unveraendert |
| Live: `NavigationManager::getAll()` als `testuser` | ein Eintrag, `href` `/index.php/apps/findling/`, `icon` `/custom_apps/findling/img/app.svg` |
| Zwoelf MDI-Pfaddaten gegen den gepinnten Commit | `diff` ueber beide sortierten Listen: kein Unterschied, 12 gegen 12 |
| `grep -c 'findling.page.index' / 'Show all results' / 'Opens the Findling results page'` in `Provider.php` | 1 / 1 / 1 |
| `php -l` ueber `Provider.php` und `ProviderTest.php` im Container | `No syntax errors` |
| `grep -c 'function test.*EntryPoint' php/tests/Unit/ProviderTest.php` | 4 |
| Stand-in-Probe ueber den echten Provider, fuenf Faelle | 18 von 18 gruen |
| `grep -c 'AbortController' backend/tests/test_admin_ui_contract.py` | 3 |
| `uv run pytest -q tests/test_admin_ui_contract.py` | 33 passed (vorher 31) |
| `uv run pytest -q` (ganze Backend-Suite) | 1780 passed, 15 skipped (vorher 1778) |
| `uv run ruff check .` und `ruff format --check .` ueber das ganze Repo | gruen, 119 Dateien formatiert |
| `uv run pyright` | 0 errors, 0 warnings |
| Em-Dash, En-Dash und Emoji in allen sieben Dateien | 0 / 0 / 0 |
| Jeder in `docs/testing.md` neu genannte Name | mit `grep` bestaetigt: `SearchServiceTest.php`, `HighlighterTest.php`, `PageControllerTest.php`, `test_php_acl_boundary.py`, `Highlighter::segments`, `SearchService::run`, `MAX_PAGE`, `MAX_QUERY_LENGTH` |

**Der PHPUnit-Job konnte lokal nicht gefahren werden, und das ist eine Eigenschaft der Maschine.** Auf ihr gibt es kein PHP ausser dem im Container und keine Testabhaengigkeiten (`phpunit/phpunit` ist `require-dev` und wird nur in CI installiert, `docs/testing.md` sagt genau das). Ersatz ist eine Stand-in-Probe nach dem Muster aus Plan 09-05: die neun OCP- und Findling-Namen, die `Provider` beruehrt, als Doubles in ihren echten Namensraeumen, die echten Wertklassen `ApprovedHit`, `SearchCaps` und `SearchOutcome` per `require`, das echte `Provider.php` daneben, gefahren in `php:8.2-cli`. Fuenf Faelle, 18 Zusicherungen, darunter die vier, die als PHPUnit-Faelle eingecheckt sind, mit denselben erwarteten Werten bis auf die Adresszeichenkette. Die Probe liegt in der Scratchpad-Ablage und ist bewusst nicht eingecheckt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Der Pruefbefehl von THIRD-PARTY.md haette ueber `search.php` nichts gefunden**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt die beiden neuen Pfade in der letzten Zeile der Pruefschleife. Diese Zeile ist `grep -o 'd="[^"]*"'`, und sie passt auf `search.php` nicht: die sechs Pfaddaten stehen dort in einfach zitierten PHP-Variablen am Kopf der Datei und nicht in einem `d`-Attribut. Dazu passt `d="` auch auf `id="`, weil `i` davorsteht, der Befehl gibt ueber `admin.php` also seit Phase 4 vier Dutzend Element-Ids mit aus. Woertlich uebernommen haette die Datei einen Befehl gefuehrt, der fuer die drei neuen Symbole sauber aussieht, weil er sie nicht liest.
- **Fix:** Beide Haelften geben jetzt einen Pfad je Zeile und nichts sonst, gematcht auf das fuehrende `M` eines Pfades in beiden Zitierweisen, sortiert und mit `diff` vergleichbar. Ein Absatz darueber sagt, warum es zwei Schreibweisen gibt. Gefahren: zwoelf Zeilen auf jeder Seite, kein Unterschied.
- **Files modified:** `THIRD-PARTY.md`
- **Commit:** `d625d86`

**2. [Rule 2 - Missing critical functionality] Die Ueberschrift des Abschnitts sprach nur von der Verwaltungsseite**

- **Found during:** Task 1
- **Issue:** Der Abschnitt heisst "The icon path data of the admin page". Drei Symbole der Ergebnisseite darunter einzutragen haette eine Attributionsdatei ergeben, die an ihrer eigenen Ueberschrift vorbei behauptet, wo das Material landet. Eine Attributionsdatei ist genau die Datei, in der das nicht passieren darf.
- **Fix:** Ueberschrift auf die zwei Seiten der Companion-App gezogen, der einleitende Satz nennt Phase 4 und Phase 9. Die Zeile "A tenth icon" wurde zu "A thirteenth icon", und die Zeichenzahl der Kurvendaten von "nine hundred" auf die gemessenen rund zweieinhalbtausend.
- **Files modified:** `THIRD-PARTY.md`
- **Commit:** `d625d86`

### Bewusste Auslegungen des Plans

**3. Der Kommentar nennt drei Testnamen, und die dritte Nennung ist eine Klasse statt eines einzelnen Tests.** Der Plan spricht von "den drei Admin-Sondertests" und beschreibt danach drei Eigenschaften: Token, Abbruchgeber und Sichtbarkeitsabfrage. Diese drei Eigenschaften liegen in **zwei** Tests, `test_the_script_reads_the_token_inside_the_call` und `test_the_script_polls_politely`. Der Kommentar nennt beide beim Namen, dazu als dritten `test_both_halves_of_the_page_write_the_same_percent_separator` und ausdruecklich "jeden Paartest danach": auch die Tests ueber die zweite Deckungszahl, den Zustand der Engine und den Stockt-Satz sind Aussagen ueber eine Seite, die einen laufenden Vorgang beobachtet, und keiner von ihnen darf auf die neue Seite gezogen werden. Nur drei Namen zu nennen und die uebrigen zu verschweigen waere die genauere Befolgung des Wortlauts und die ungenauere Auskunft gewesen.

**4. Die zwoelf Verhalten in `docs/testing.md` bleiben zwoelf.** Der Plan verlangt "drei neue Zeilen" im Abschnitt ueber die Verhalten der PHP-Haelfte. Der Abschnitt heisst "The twelve behaviours", sagt in seinem eigenen Text, dass er die Spezifikation **eines** Audit-Nachlaufs ist, und die Zahl steht ausserhalb: `php.yml` nennt sie an zwei Stellen, `ProviderTest.php` sagt "Not one of the twelve". Die drei neuen Zeilen stehen deshalb als Nummern 13 bis 15 in einer eigenen kleinen Tabelle unter der ersten, mit einem Satz, warum die erste nicht mitwaechst. Drei Zeilen, dieselben Spalten, keine gebrochene Referenz.

**5. Der Provider hat einen zusaetzlichen Testfall bekommen, den der Plan nicht verlangt.** `testACompleteGroupHasNoEntryPointBecauseThePageWouldShowTheSameHits` und die drei anderen sind die vier geforderten; die fuenfte Zusicherung ueber die Adresse ohne `names` liegt nicht als PHPUnit-Fall, sondern nur in der Stand-in-Probe, damit die Zahl vier bleibt, die das Abnahmekriterium zaehlt.

## Threat Model

| Threat ID | Umsetzung |
|---|---|
| T-09-22 (Tampering, Einstiegs-Eintrag im Paritaetsvergleich) | Der Eintrag traegt kein `fileId`-Attribut, ein Testfall haelt das gegen zwei echte Treffer, die je eines tragen, und der Kommentar an der Stelle sagt ausdruecklich, dass ein Leser dieser Gruppe ihn an seiner Adresse erkennen muss und nie am fehlenden Attribut. Plan 09-07 baut die andere Haelfte. Bis dahin bleibt der Job `search-parity` gruen, weil er mit `limit=100` gegen Szenarien mit deutlich unter 25 Dateien laeuft: `hasMore` ist dort falsch, der Eintrag erscheint also gar nicht |
| T-09-23 (Spoofing, fremdes Symbol oder fremde Kurvendaten) | `app.svg` ist eine byte-identische Kopie einer bereits attribuierten Datei (`cmp` still, gleiche Blob-Pruefsumme), die drei neuen Namen stehen in `THIRD-PARTY.md`, und der Pruefbefehl wurde gefahren: zwoelf Pfaddaten, zeichengleich mit dem gepinnten Commit. Kein Paket, keine Laufzeit, nur Kurvendaten |
| T-09-04 (Elevation of Privilege, zweite Sicherheitsflaeche) | Der Einstieg ist ein Link auf dieselbe Route, die dieselbe Berechtigungsentscheidung durch denselben Dienst faellt. `test_php_acl_boundary.py` ist unveraendert gruen, es steht weiterhin genau eine Aufrufstelle je Frage in `SearchService.php` |
| T-09-24 (Tampering, Gate C mit verlorenen Dateien) | Die Existenzpruefung deckt sechs Pfade ab, der Test heisst danach, und sein Kommentar sagt den Satz aus: die sauberste Ausgabe dieses Gates ist die, in der es nichts mehr liest |
| T-09-25 (DoS, falsch platzierter Navigationsblock) | Der Block steht hinter dem Einstellungsblock, und der Beleg ist nicht die Position im Diff, sondern der gefahrene Store-Pfad: Transform und Schema gruen gegen den gepinnten appstore-Commit, plus die Sichtprobe auf der normalisierten Ausgabe |
| T-09-SC (Supply Chain) | Kein Paket installiert. Die drei Container, die in diesem Plan liefen (`alpine` per Digest, `php:8.2-cli` fuer die Probe, die laufende `findling-nextcloud`), sind Werkzeuge dieser Maschine und kein ausgeliefertes Material |

Keine neue Angriffsflaeche ausserhalb des Registers: dieser Plan legt keine Route an, keinen Endpunkt und keinen Schreibvorgang. Der Navigationseintrag ist ein Link auf eine Route, die es seit Plan 09-04 gibt und die ihre Berechtigungsentscheidung nicht von ihm bekommt.

## Notes for Future Phases

- **Plan 09-07 erbt die zweite Haelfte von T-09-22.** `scripts/ci/parity_diff.py` muss den Eintrag an der `resourceUrl` erkennen und ueberspringen, nicht am fehlenden `fileId`. Der Kommentar an der Baustelle in `Provider.php` sagt denselben Satz, damit die Regel an beiden Enden steht.
- **Der Navigationseintrag ist erst nach einem App-Update sichtbar.** Nextcloud liest ihn aus der installierten `appinfo/info.xml`; auf der Entwicklungsinstanz ist das Verzeichnis eingehaengt, auf einer echten Installation ist es das nicht. Das gehoert in die Sichtproben von Plan 09-08 und in die Release-Notiz, nicht in einen Fehlerbericht.
- **Die zwei neuen Aussagen ueber `search.js` sind Abwesenheitsaussagen.** Wer der Seite spaeter doch einen Zeitgeber gibt, weil irgendetwas nachzuladen waere, faellt zuerst ueber `test_the_page_script_does_no_polling` und nicht ueber ein Verhalten. Das ist Absicht: der Vertrag sagt, dass es auf dieser Seite kein Polling gibt, und ein Nachladen waere die Aenderung des Vertrags und nicht seine Umsetzung.
- **`docs/testing.md` fuehrt jetzt zwei Tabellen von Verhalten.** Wer die Zwoelf jemals zusammenfuehren will, bewegt dabei `php.yml` an zwei Stellen und den Klassenkommentar von `ProviderTest.php`.

## Deferred Issues

| Id | Punkt | Warum offen |
|---|---|---|
| DI-09-02 | Die zwanzig Abnahme-Sichtproben der 09-UI-SPEC, jetzt zusaetzlich Sichtprobe 1, 2 und 13: der Einstiegs-Eintrag im Dialog und der Weg ueber das App-Menue | Augenarbeit, und fuer den Einstiegs-Eintrag braucht es einen laufenden Backend-Container mit mehr Treffern als der Dialog zeigt. Auf dieser Maschine laeuft nur `findling-nextcloud` |
| DI-09-03 | Sichtprobe 5 der 09-UI-SPEC ist in ihrer Fassung nicht haltbar und gehoert umformuliert | Unveraendert aus Plan 09-05, Befund 2 der 09-RESEARCH |
| DI-09-04 | `php/l10n/fr.json` und `fr.js` gibt es weiterhin nicht, der Navigationsname laeuft also auf Franzoesisch durch den englischen Quellstring | Offener Punkt 3 der 09-UI-SPEC, Owner-Entscheidung, vorgesehen fuer Plan 09-08 |

**DI-09-01 ist geschlossen:** `THIRD-PARTY.md` fuehrt die drei neuen Symbolnamen in der Namensliste, ihren Fundort in `search.php` und beide neuen Pfade in der Pruefschleife, und die Schleife wurde gefahren.

## Self-Check: PASSED

- `php/img/app.svg` liegt auf der Platte, 740 Byte, byte-identisch mit `app-dark.svg`.
- `php/appinfo/info.xml` traegt den Navigationsblock an Zeile 288, hinter dem Einstellungsblock an Zeile 263.
- `THIRD-PARTY.md`, `php/lib/Search/Provider.php`, `php/tests/Unit/ProviderTest.php`, `backend/tests/test_admin_ui_contract.py` und `docs/testing.md` tragen alle beschriebenen Aenderungen.
- Die drei Commits `d625d86`, `57982ce` und `474bf5d` stehen in `git log`.
- Der Arbeitsbaum war vor dem Schreiben dieser Datei sauber bis auf die Planungsdateien.
