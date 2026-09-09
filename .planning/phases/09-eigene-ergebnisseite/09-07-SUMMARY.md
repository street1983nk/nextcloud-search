---
phase: 09-eigene-ergebnisseite
plan: 07
subsystem: ci
tags: [paritaet, ci, cookie-login, html-auszieher, standardbibliothek, T-09-22, T-09-26]

requires:
  - phase: 09-eigene-ergebnisseite
    provides: "09-05: die Zeilen-Id findling-hit-<fileid>, das ol der Trefferliste und der Leerzustand als Marken der Seite"
  - phase: 09-eigene-ergebnisseite
    provides: "09-06: der Einstiegs-Eintrag am Ende der Findling-Gruppe, ohne fileId-Attribut, erkennbar an seiner Zieladresse"
  - phase: 09-eigene-ergebnisseite
    provides: "09-04: die Route findling.page.index mit NoCSRFRequired und PAGE_SIZE 25"
provides:
  - scripts/dev/probe_page_login.sh, der belegte Anmeldeweg als eincheckbares Werkzeug
  - Der dritte Eingabemodus --findling-html von scripts/ci/parity_diff.py, mit drei harten Fehlerfaellen
  - Das Ueberspringen des Einstiegs-Eintrags an seiner Zieladresse im JSON-Auszieher
  - Der Anmeldeschritt und der dritte Vergleich je Szenario im Job search-parity
  - Die Falsifikation der dritten Vergleichshaelfte in der negativen Probe des Jobs
affects: [09-08]

tech-stack:
  added: []
  patterns:
    - "Ein Auszieher, der HTML liest, braucht keine Bibliothek, wenn die gelesene Marke ohnehin schon Vertrag ist: die Zeilen-Id ist der Anker der Rueckkehr-Markierung und kein Testartefakt"
    - "Eine leere Menge ist nur dann eine Antwort, wenn die Seite ihren Leerzustand mitliefert; ohne Marke und mit Fehlerblock ist sie ein unlesbares Verdikt"
    - "Ein CI-Schritt, dessen Weg vorher an einer laufenden Instanz geprobt wurde, faellt nicht nach zwanzig Minuten Laufzeit ueber ein Detail"
    - "Ein neuer Vergleich bekommt seine eigene Falsifikation im selben Job: ein Gate, das nie rot gesehen wurde, ist kein Gate"

key-files:
  created:
    - scripts/dev/probe_page_login.sh
  modified:
    - scripts/ci/parity_diff.py
    - backend/tests/test_parity_diff.py
    - .github/workflows/integration.yml

key-decisions:
  - "Der Origin-Kopf ist Pflicht am Anmelde-POST: LoginController von Nextcloud 34 weist eine Anmeldung ohne vertrauenswuerdigen Ursprung ab, bevor er das Passwort ansieht, mit derselben Umleitung wie bei einem falschen Passwort. Genau der Stolperstein, den Annahme A7 befuerchtet hat"
  - "Der Fehlerblock wird vor den Listenmarken geprueft: eine Seite mit Fehlerblock ist eine sprechendere Diagnose als eine Seite ohne Marken, und der Leerzustand steht unter dem Fehlerblock ohnehin immer mit da"
  - "Der Einstiegs-Eintrag wird an der resourceUrl erkannt, die auf den App-Pfad zeigt, und die Regel gilt fuer jede Seite gleich: das Kriterium ist die Adresse und nicht die Herkunft der Antwort"
  - "Der erste Vergleich gewinnt den Exitcode, aber beide Vergleiche laufen und drucken immer: ein Lauf, der nur den ersten Befund zeigt, schickt jemanden fuer den zweiten noch einmal los"
  - "Die negative Probe des Jobs bekommt drei Seiten-Faelle dazu, obwohl der Plan nur einen verworfenen Handversuch verlangt: die HTML-Haelfte kann still leer lesen, und genau das muss einmal rot gesehen werden"

patterns-established:
  - "Verifikation eines CI-Schritts ohne CI-Lauf: den Rumpf des run-Blocks aus der YAML herausschneiden, nur Host und Konto ersetzen und woertlich gegen die lokale Instanz fahren"

requirements-completed: [UI-03]

duration: 50min
completed: 2026-09-09
---

# Phase 9 Plan 07: Der Paritaetsjob deckt die Ergebnisseite mit Summary

**Jedes der 32 Szenarien des Paritaetsjobs vergleicht ab jetzt drei Mengen statt zwei, der Weg dorthin wurde vor dem Bau an einer laufenden Nextcloud 34 geprobt, und die Probe hat den Stolperstein von Annahme A7 tatsaechlich gefunden: ohne Origin-Kopf weist der Server die Anmeldung ab, bevor er das Passwort ansieht.**

## Performance

- **Duration:** rund 50 min
- **Tasks:** 3, alle autonom, kein Checkpoint
- **Files:** 4 (1 neu, 3 geaendert)

## Accomplishments

- **`scripts/dev/probe_page_login.sh`**, 128 Zeilen, POSIX-sh, ausfuehrbar (Modus 100755 im Index). Anmeldeformular holen, Token ziehen, Anmeldung absenden, Seite mit dem Behaelter abrufen, Zeilen-Ids zaehlen. Ohne Zugangsdaten im Text, Basisadresse aus `FINDLING_BASE_URL` mit `http://localhost:8090` als Vorgabe. Meldet drei Arten von Nichts getrennt: Fehlerblock, Leerzustand, und eine Antwort, die gar nicht die Ergebnisseite ist.
- **`--findling-html` in `scripts/ci/parity_diff.py`.** Ein Muster ueber `id="findling-hit-<n>"`, reine Standardbibliothek (`re` und `urllib.parse` dazu, sonst nichts), drei harte Fehlerfaelle und ein vierter, der eine gueltige leere Menge ist. Der dritte Vergleich laeuft symmetrisch mit denselben Exitcodes, und seine Meldungen heissen `page-missing` und `page-extra`, damit ein roter Lauf sagt, welcher der beiden Wege abweicht.
- **Der Einstiegs-Eintrag wird uebersprungen, an seiner Adresse.** `_is_entry_point()` liest die `resourceUrl`, nimmt ihren Pfad und prueft ihn gegen den App-Pfad der Seite. Ein gewoehnlicher Eintrag ohne `attributes.fileId` laesst den Auszieher weiterhin werfen; damit ist die zweite Haelfte von T-09-22 gebaut, die Plan 09-06 hier abgelegt hat.
- **Der Job `search-parity` meldet vier Konten an und vergleicht drei Mengen je Szenario.** Ein Anmeldeschritt legt je Konto einen Cookie-Behaelter an und prueft ihn gegen genau die Route, die spaeter verglichen wird. `ask_page()` stellt dieselbe Frage an die Seite, `compare()` reicht die drei Dateien an den Vergleicher weiter. Keine neuen Zugangsdaten: es sind die vier Konten, auf denen der Job ohnehin laeuft.
- **Die negative Probe faelscht auch die dritte Haelfte.** Drei Faelle ueber die echte Seite eines bestandenen Szenarios: eine Zeile mehr (`page-extra`), eine Zeile weniger (`page-missing`) und eine Antwort, die nicht die Seite ist (`unreadable`). Alle drei muessen rot werden und ihren Befund benennen, sonst faellt der Schritt.
- **Zehn neue Testfaelle** in `backend/tests/test_parity_diff.py` (9 auf 19), gefordert waren acht. Sie decken drei Zeilen, den Leerzustand, die markenlose Antwort, den Fehlerblock, die nicht lesbare Datei, den Einstiegs-Eintrag, den gewoehnlichen Eintrag ohne Attribut, beide Richtungen des dritten Vergleichs, den Mindestwert auf der dritten Menge und die Vertraulichkeit der Ausgabe.

## Task Commits

1. **Task 1: Die Anmeldeprobe, die Annahme A7 beantwortet** - `ff435dd` (feat)
2. **Task 2: Der dritte Eingabemodus des Vergleichers** - `bfefb49` (feat)
3. **Task 3: Der dritte Vergleich im Paritaetsjob** - `0fad7ec` (test)

## Annahme A7, an der laufenden Instanz beantwortet

**A7 traegt, aber nicht so, wie sie dastand.** Der Weg funktioniert, und er scheitert an genau einem Detail, wenn man ihn naiv baut.

| Schritt | Ergebnis gegen `findling-nextcloud`, Nextcloud 34.0.3, Port 8090 |
|---|---|
| Anmeldeformular mit Cookie-Behaelter | HTTP 200, `data-requesttoken` im Kopf, vier Cookies im Behaelter |
| Anmelde-POST **ohne** Origin-Kopf | 303 auf `/login?direct=1&user=testuser`, also abgewiesen. Ununterscheidbar von einem falschen Passwort |
| Anmelde-POST **mit** `Origin: http://localhost:8090` | 303 in die Instanz, Sitzung steht |
| `GET /apps/findling/?query=...` mit dem Behaelter | HTTP 200, echte Ergebnisseite, kein Token noetig |
| Falsches Passwort | Exit 1 mit `the password was refused` |
| Unbekanntes Konto | Exit 1, dieselbe Meldung, weil der Server beide Faelle gleich beantwortet |

Der Grund steht in `core/Controller/LoginController.php` der laufenden Instanz, Zeile 307 bis 314: ist der Origin leer oder keine vertrauenswuerdige Adresse, setzt der Controller `LOGIN_MSG_INVALID_ORIGIN`, **bevor** er die Zugangsdaten prueft. Ein Browser setzt den Kopf, curl nicht. Ohne diese Probe waere der Anmeldeschritt im Job gebaut worden, waere rot geworden und haette dabei "das Passwort ist falsch" behauptet, ueber Passwoerter, die stimmen.

**Was die Probe nicht belegen konnte: eine Zeilenzahl groesser als null.** Das lokale Backend indexiert auf dieser Maschine nicht. Der Poller beendet jeden Durchgang mit `FileNotFoundError` (`.dev/exapp.log`), der Bestand in `.dev/storage` stammt aus einem aelteren Bau (`a reindex is required: wordlist_hash`), und `tesseract` gibt es auf dem Host nicht. 465 Dateien stehen geplant, keine wird beurteilt, die Suche antwortet leer, und die Seite rendert folgerichtig ihren Leerzustand. Das ist eine Eigenschaft der Maschine und kein Befund ueber die Seite; aufgenommen als DI-09-05.

Ersatz, und er ist naeher am Vertrag als ein Lauf gegen einen Index waere: das **echte Template** wurde in drei Zustaenden gerendert (Stand-in-Muster aus 09-05, `php:8.5-cli` im laufenden Container, die OCP-Namen als Doubles, `search.php` per `require`) und der Vergleicher gegen diese Ausgaben gefahren. Die drei Marken stehen dort so, wie der Auszieher sie erwartet: Treffer-Ausgabe 3 Zeilen-Ids und ein `findling-hits`, Leerzustands-Ausgabe 0 Ids und vier `findling-empty`, Fehler-Ausgabe zusaetzlich ein `findling-banner--error`.

## Annahme A4, gegen die Marker-Zaehlungen des Jobs geprueft

**A4 traegt, mit Abstand.** Die Seitengroesse ist `PageController::PAGE_SIZE` = 25. Was die Szenarien wirklich vergleichen:

| Szenario | Dateien mit dem Marker | Hoechster Erwartungswert |
|---|---|---|
| `parityown`, `parityshared`, `parityrevoked`, `parityminimal`, `paritytrash` | je 3 (`write_three`) | 3 |
| `parityteam` (Team-Ordner) | 3 | 3 |
| `parityversion` | 1 | 1 |
| Alle Verweigerungs-Szenarien | 0 | 0 |

19 Fixturedateien insgesamt, was der Zaehlung `EXPECTED_JUDGED: '19'` des Jobs entspricht. Der groesste je verglichene Satz ist drei, die Grenze ist 25, und der Kommentar im Job sagt jetzt den Satz aus, unter dem ein spaeteres Szenario blaettern muesste, statt still falsch zu vergleichen.

**Laufzeit:** vier Anmeldungen zu je drei Anfragen und ein zusaetzlicher Seitenabruf je `compare`, davon gibt es 32. Also rund 44 Anfragen mehr. Der Seitenabruf ist keine statische Datei, sondern eine echte Suche mit dem Budget von 3 Sekunden aus `PageController::BUDGET_SECONDS`, im Regelfall deutlich schneller. Obergrenze also gut zwei Minuten gegen eine Grenze von 30, realistisch unter einer. Faellt die Laufzeit im ersten CI-Lauf dennoch auf, gehoert sie in die Abnahme der Phase.

## Verification

| Pruefung | Ergebnis |
|---|---|
| `bash -n scripts/dev/probe_page_login.sh` und `sh -n` | beide still |
| `test -x scripts/dev/probe_page_login.sh`, Modus im Index | ausfuehrbar, `100755` |
| Zugangsdaten im Skript | keine; drei Argumente, Basisadresse aus der Umgebung |
| `python -c "import ast; ast.parse(...)"` ueber `parity_diff.py` | parst |
| `grep -c 'findling-hit-' scripts/ci/parity_diff.py` | 2 (Muster und Kommentar) |
| Importe von `parity_diff.py` | `argparse`, `json`, `re`, `sys`, `pathlib`, `urllib.parse`; der Standardbibliotheks-Test bleibt gruen |
| `uv run pytest -q tests/test_parity_diff.py` | 19 passed (vorher 9, gefordert mindestens 8 mehr) |
| `uv run pytest -q` (ganze Backend-Suite) | 1790 passed, 15 skipped (vorher 1780) |
| `uv run ruff check --config pyproject.toml ../scripts` und `format --check` | gruen, 10 Dateien |
| `uv run ruff check .` und `format --check .` ueber das Repo | gruen, 119 Dateien |
| `uv run pyright` | 0 errors, 0 warnings |
| `python -c "import yaml; yaml.safe_load(open('.github/workflows/integration.yml'))"` | laedt |
| `grep -c 'findling-html' .github/workflows/integration.yml` | 1 (der Aufruf in `compare()`) |
| Live: der Rumpf des Anmeldeschritts, woertlich aus der YAML geschnitten, nur Host und Konto ersetzt | `testuser is logged in and the result page answers this session`, Exit 0 |
| Live: `compare` aus `parity.sh`, woertlich aus der YAML geschnitten, gegen Port 8090 | zwei Zeilen `parity ok`, Exit 0, drei Dateien geschrieben (`native-`, `findling-`, `page-`) |
| Live: dasselbe `compare` mit verfaelschtem Erwartungswert 3 | zweimal `parity inconclusive`, `::error::`, Exit 1 |
| Vergleicher gegen die echte Template-Ausgabe mit drei Treffern | `the result page compared 3 fileids, identical to the search dialog` |
| Vergleicher gegen die echte Leerzustands-Ausgabe und gegen die Live-Seite | je `compared 0 fileids`, Exit 0 |
| Vergleicher gegen die echte Fehlerblock-Ausgabe | Exit 3, `carries the error block` |
| Vergleicher gegen die echte Anmeldeseite der Instanz | Exit 3, `neither the hit list nor the empty state` |
| Vergleicher gegen eine Dialogantwort **mit** Einstiegs-Eintrag | `compared 3 fileids`, also drei und nicht vier |
| Die drei Seiten-Proben der negativen Probe, gegen echte Template-Ausgabe gefahren | `page-extra` Exit 1, `page-missing` Exit 1, `unreadable` Exit 3 |
| Em-Dash, En-Dash, Emoji in allen vier Dateien | 0 / 0 / 0 |

**Der CI-Lauf selbst steht noch aus, und das ist die Bauform dieser Arbeit und kein Versaeumnis.** Der Job braucht eine frische Nextcloud, den Groupfolders-Aufbau und den Crawl, alles Dinge, die es nur auf dem Runner gibt; der Push gehoert der Welle. Was ohne Runner pruefbar war, wurde geprueft, und zwar am Rumpf der Schritte selbst statt an einer Nacherzaehlung: beide Funktionen des Jobs wurden aus der YAML geschnitten und woertlich gefahren. Der erste rote oder gruene Lauf gehoert in die Abnahme von Plan 09-08.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Der Anmelde-POST braucht einen Origin-Kopf**

- **Found during:** Task 1
- **Issue:** Der geplante Weg (Formular holen, Token ziehen, POST absenden) wurde von der Instanz abgewiesen, obwohl das Passwort stimmte, was mit Basic-Auth gegen `ocs/v2.php/cloud/user` sofort belegt war. `LoginController::tryLogin` prueft in Nextcloud 34 zuerst den Origin gegen die vertrauenswuerdigen Adressen und setzt sonst `LOGIN_MSG_INVALID_ORIGIN`, ohne die Zugangsdaten anzusehen.
- **Fix:** `-H "Origin: <basisadresse>"` am POST, im Skript und im Job-Schritt, jeweils mit dem Absatz, warum er dasteht. Ohne ihn ist der Weg nicht baubar, mit ihm ist er es.
- **Files modified:** `scripts/dev/probe_page_login.sh`, `.github/workflows/integration.yml`
- **Commit:** `ff435dd`, `0fad7ec`

**2. [Rule 2 - Missing critical functionality] Die negative Probe des Jobs deckt die dritte Haelfte mit ab**

- **Found during:** Task 3
- **Issue:** Der Plan verlangt eine absichtliche Verfaelschung als Handversuch, der danach verworfen wird. Der Job selbst begruendet in seinem eigenen Kommentar, warum das zu wenig ist: "ein Gate, das nie rot gesehen wurde, ist nicht bekanntermassen in Ordnung". Die HTML-Haelfte kann auf eine Weise still werden, die der JSON-Haelfte fehlt: eine Antwort ohne Zeilen liest sich als leere Menge, und zwei leere Mengen sind einig.
- **Fix:** `page_probe()` im Schritt "The negative probe", drei Faelle ueber die echte Seite eines bestandenen Szenarios: eine Zeile dazu, die erste Zeilen-Id entwertet, und eine Antwort, die nicht die Seite ist. Jeder Fall muss rot werden **und** seinen Befund benennen. Die drei `sed`-Ausdruecke wurden gegen die echte Template-Ausgabe gefahren, bevor sie in den Job kamen.
- **Files modified:** `.github/workflows/integration.yml`
- **Commit:** `0fad7ec`

**3. [Rule 2 - Missing critical functionality] Der Fehlerbericht des Jobs zeigt auch die Seitenantworten**

- **Found during:** Task 3
- **Issue:** Der Schritt "Everything the failure had to say" gibt die Fileids beider JSON-Antworten aus, damit ein roter Lauf ohne zweiten Lauf diagnostizierbar ist. Mit einer dritten Antwort im Spiel waere genau die Datei nicht im Bericht gewesen, an der ein neuer Fehler haengt.
- **Fix:** Eine Schleife ueber `page-*.html`, die die Zeilen-Ids und die Zaehlung der drei Marken ausgibt. Ids und Marken, nie das Markup: eine Seite traegt den Dateinamen in jeder Zeile, und dieses Protokoll ist das eines oeffentlichen Repositoriums.
- **Files modified:** `.github/workflows/integration.yml`
- **Commit:** `0fad7ec`

### Bewusste Auslegungen des Plans

**4. Der Fehlerblock wird vor den Listenmarken geprueft.** Der Plan zaehlt die drei Fehlerfaelle in der Reihenfolge "nicht lesbar, keine Marke, Fehlerblock" auf. Das ist eine Aufzaehlung und keine Vorrangregel, und die Reihenfolge im Code ist die umgekehrte, weil die Seite ihren Leerzustand **unter** dem Fehlerblock ohnehin mitrendert: eine Seite mit Fehlerblock traegt also immer auch eine Marke, und die genauere Meldung ist die ueber den Fehlerblock. Beide Faelle enden mit demselben Exitcode, nur die Diagnose ist die schaerfere.

**5. Die Regel fuer den Einstiegs-Eintrag gilt fuer jede Antwort, nicht nur fuer die von findling.** Der Plan sagt, der Eintrag komme in der Dialogantwort vor. Das stimmt, und der Auszieher fragt trotzdem nicht danach, aus welcher Antwort ein Eintrag stammt: das Kriterium ist die Adresse. Eine Regel, die zusaetzlich die Seite prueft, sagt dasselbe zweimal und laedt dazu ein, spaeter die eine Haelfte zu aendern und die andere zu vergessen. Der native Anbieter erzeugt diese Adresse ohnehin nie.

**6. Beide Vergleiche laufen und drucken immer, der erste gewinnt den Exitcode.** Der Plan sagt nur "derselbe Exitcode". Ein Abbruch nach dem ersten Befund waere die einfachere Lesart und die teurere: wer einen roten Lauf ansieht, will beide Antworten auf einmal, nicht die zweite nach einem weiteren Lauf. Der Exitcode bleibt der des ersten Vergleichs, weil der die Aussage ueber die Rechtekette ist und der zweite die ueber die Seite.

**7. Zehn Testfaelle statt acht.** Die zwei zusaetzlichen sind der Mindestwert auf der dritten Menge und die Vertraulichkeit der Ausgabe des Seitenvergleichs. Beide fielen im Bau an, beide haetten sonst nur als Behauptung im Summary gestanden.

## Threat Model

| Threat ID | Umsetzung |
|---|---|
| T-09-22 (Tampering, Einstiegs-Eintrag als Treffer gezaehlt) | `_is_entry_point()` liest den Pfad der `resourceUrl` und vergleicht ihn mit dem App-Pfad der Seite; ein Eintrag ohne `attributes.fileId`, der diese Adresse nicht traegt, laesst den Auszieher weiterhin werfen. Zwei Testfaelle halten beide Haelften, und einer davon lief gegen eine Antwort in der echten Form, mit `"attributes": []`, wie PHP ein leeres Feld serialisiert. Die Haelfte aus 09-06 ist damit geschlossen |
| T-09-26 (Tampering, leere Menge als bestandene Paritaet) | Drei Faelle enden als unlesbare Antwort: keine Marke, Fehlerblock, nicht lesbare Datei. Der Mindestwert gilt fuer alle drei Mengen, mit eigenem Testfall. Gegen echtes Material belegt: die Anmeldeseite der Instanz und die Fehlerblock-Ausgabe des echten Templates enden beide mit Exitcode 3, und die negative Probe des Jobs faehrt den Fall bei jedem Lauf |
| T-09-04 (Elevation of Privilege, Abweichung zwischen Dialog und Seite) | Der dritte Vergleich laeuft symmetrisch, beide Richtungen haben eigene Meldungen: `page-missing` ist ein funktionaler Defekt der Seite, `page-extra` einer an der Rechtegrenze. Beide wurden an echtem Markup rot gesehen |
| T-09-10 (Information Disclosure, Cookie-Behaelter im CI-Lauf) | accept, wie geplant. Es kommen keine Zugangsdaten dazu: der Anmeldeschritt nimmt die vier Konten, auf denen der Job ohnehin laeuft, die Behaelter liegen im Arbeitsverzeichnis des Runners und sterben mit ihm. `probe_page_login.sh` nimmt seine als Argumente und hat keine eingebaut |
| T-09-27 (DoS, Zeitgrenze des Jobs) | accept, mit Zahl statt Zusicherung: rund 44 zusaetzliche Anfragen, davon 32 echte Suchen mit einem Budget von 3 Sekunden, gegen eine Grenze von 30 Minuten |
| T-09-SC (Supply Chain) | Kein Paket installiert. `parity_diff.py` bleibt bei der Standardbibliothek, `re` und `urllib.parse` kommen dazu, und der Test, der das prueft, ist unveraendert gruen. Die Vertraulichkeit der Ausgabe wurde fuer den neuen Vergleich eigens gemessen: die Seiten-Fixtures tragen Pfad und Titel in jeder Zeile, und keiner von beiden erscheint in einer Meldung |

Keine neue Angriffsflaeche ausserhalb des Registers: dieser Plan legt keine Route an, keinen Endpunkt und keinen Schreibvorgang. Neu ist eine angemeldete Sitzung im CI-Lauf, und sie steht als T-09-10 im Modell.

## Notes for Future Phases

- **Der erste CI-Lauf des erweiterten Jobs ist die offene Zusicherung dieses Plans.** Zwei Dinge sind dort zuerst anzusehen: der Anmeldeschritt (vier Zeilen `is logged in`) und die Zeilenpaare je Szenario, von denen die zweite `the result page compared N fileids` sagt. Beides steht im Protokoll, ohne dass man etwas aufklappen muss.
- **Ein Szenario mit mehr als 25 Treffern muss blaettern.** Der Satz steht als Kommentar in `compare()`. Wer ihn ueberliest, bekommt eine Meldung `page-missing` und wird die Ursache in der Rechtekette suchen, wo nur paginiert wurde.
- **Die Sitzung ist ein Zustand, der die ganze Joblaufzeit haelt.** Faellt sie aus, antwortet die Seite mit dem Anmeldeformular, und das ist ausdruecklich kein leeres Ergebnis, sondern Exitcode 3 mit `neither the hit list nor the empty state`. Genau dieser Fall ist als dritte Seiten-Probe eingebaut.
- **`docs/testing.md` beschreibt den Paritaetsjob noch als Vergleich zweier Antworten** (Abschnitt ueber die Gastprobe, Zeile 227 bis 235). Die Datei steht in keiner Aufgabe und in keiner Dateiliste dieses Plans, deshalb unangetastet; aufgenommen als DI-09-06.
- **`scripts/dev/guest_parity.sh` ruft denselben Vergleicher weiterhin mit vier Argumenten.** `--findling-html` ist optional, die Gastprobe bleibt unveraendert gueltig, und sie koennte den dritten Vergleich spaeter dazubekommen, wenn jemand den Gastnutzer auch auf der Seite sehen will.
- **Der Rumpf eines Job-Schritts ist lokal fahrbar.** Aus der YAML schneiden, die zehn Leerzeichen der Blockeinrueckung abziehen, Host und Konto ersetzen. Das hat hier zwei Fehler vor dem ersten Runner-Lauf gefunden und ist billiger als jeder Push.

## Deferred Issues

| Id | Punkt | Warum offen |
|---|---|---|
| DI-09-05 | Das lokale Backend indexiert nicht (`FileNotFoundError` je Durchgang, Bestand aus einem aelteren Bau, kein `tesseract` auf dem Host), deshalb konnte `probe_page_login.sh` keine Trefferzeile groesser null melden | Eigenschaft der Entwicklungsmaschine und nicht der Seite. Ersatzbeleg ist die Ausgabe des echten Templates in drei Zustaenden. Wer den Bestand einmal frisch aufbaut, faehrt die Probe nach |
| DI-09-06 | `docs/testing.md` beschreibt den Paritaetsjob als Vergleich zweier Antworten und kennt die dritte Menge nicht | Ausserhalb der Dateiliste dieses Plans. Gehoert in Plan 09-08 oder in die Phasen-Verifikation |
| DI-09-02 | Die Abnahme-Sichtproben der 09-UI-SPEC | unveraendert aus 09-05 und 09-06 |
| DI-09-03 | Sichtprobe 5 der 09-UI-SPEC ist in ihrer Fassung nicht haltbar | unveraendert aus 09-05 |
| DI-09-04 | `php/l10n/fr.json` und `fr.js` fehlen weiterhin | unveraendert aus 09-06, Owner-Entscheidung |

## Self-Check: PASSED

- `scripts/dev/probe_page_login.sh` liegt auf der Platte, 128 Zeilen, im Index mit Modus `100755`.
- `scripts/ci/parity_diff.py` (355 Zeilen) und `backend/tests/test_parity_diff.py` (567 Zeilen) tragen die beschriebenen Aenderungen; `.github/workflows/integration.yml` laedt als YAML und enthaelt `findling-html` genau einmal.
- Die drei Commits `ff435dd`, `bfefb49` und `0fad7ec` stehen in `git log`.
- Der Arbeitsbaum war vor dem Schreiben dieser Datei sauber bis auf `.planning/STATE.md`.
