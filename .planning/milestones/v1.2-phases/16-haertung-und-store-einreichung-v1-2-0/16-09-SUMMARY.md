---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 09
subsystem: release-mechanik
tags: [rel-02, upgrade-beweis, deploy-harp, q-5, ratsche, d-04]

# Dependency graph
requires:
  - phase: 16-haertung-und-store-einreichung-v1-2-0
    provides: der Baum steht auf 1.2.0 und traegt die Migration Version001200Date20260921000000 (Plan 16-07), sonst liefe der Beweis in ERROR_UP_TO_DATE
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: der Upgrade-Beweis selbst (Plan 11-07) und die Lehre des ersten echten Sprungs (Plan 11-11)
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    provides: getSupportedFilters mit BUILTIN_SINCE und BUILTIN_UNTIL (Plan 13-06), der Gegenstand der neuen Zusicherung 6
provides:
  - deploy-harp springt von v1.1.0 auf den Baum, nicht mehr von v1.0.3
  - snapshot() schreibt searchFilters.declared und searchFilters.dates
  - Zusicherung 6 misst die zwei Datumsgrenzen des Anbieters statt des Navigationseintrags
  - die Ratsche heisst GOLD_V1_0_AND_V1_1 und nennt beide Minor-Reihen
affects: [16-14-abgabe]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Zusicherung des Upgrade-Beweises braucht eine Vorbedingung im Vorher-Zustand, die dieselbe Eigenschaft auf Abwesenheit prueft; ohne sie kann die Zusicherung gruen sein, weil der Wert schon vorher da war"
    - "Die Route /ocs/v2.php/search/providers traegt die Filterliste je Anbieter; ein Unterschied in den deklarierten Filtern ist ohne gerenderte Seite ablesbar"
    - "Ein ueberholter Begruendungsabsatz wird datiert unter den neuen gestellt statt geloescht; ein Leser sieht dann, warum die alte Fassung in ihrer Zeit richtig war"
    - "Versionsliterale in Meldungen des Beweises werden durch ${UPGRADE_FROM_TAG} ersetzt, damit der naechste Sprung eine Zeile kostet und keine Suche durch Schritte"

key-files:
  created: []
  modified:
    - .github/workflows/deploy-harp.yml
    - backend/tests/test_upgrade_compatibility.py
    - .planning/phases/16-haertung-und-store-einreichung-v1-2-0/deferred-items.md

key-decisions:
  - "Q-5 ist zugunsten der deklarierten Filter entschieden und gegen den sechsten Engine-Zustand. Der Zustand faellt aus zwei nachgesehenen Gruenden: das Feld engineState steht schon in v1.1.0 in der Admin-Antwort (git show v1.1.0:php/lib/Service/AdminViewService.php Zeile 1813), und der Wert unloaded haengt an unload_count() > 0, also an einer Leerlaufspanne, die dieser Auftrag nicht faehrt"
  - "Der zweite Kandidat wird auf einem billigeren Weg gelesen als die Recherche annahm. Die Filter- und Sortierarbeit der Phase 13 muss nicht als gerenderte Seite abgebildet werden: /ocs/v2.php/search/providers traegt die Filterliste je Anbieter, und integration.yml liest dieselbe Route seit Phase 1 fuer dieselbe Frage"
  - "Die Vorbedingung in Store upgrade 1 wird umgedreht und nicht geloescht. Sie verlangt jetzt die ANWESENHEIT des navigations-Blocks und ist damit die billigste Zusicherung der Datei, dass UPGRADE_FROM_TAG wirklich auf die 1.1.x-Reihe zeigt; eine Marke der 1.0.x-Reihe antwortete ohne den Block"
  - "Die zwei Zweige des Versionsschritts in Store upgrade 4 bleiben beide stehen, obwohl heute nur der erste laeuft. Jeder Release-Zyklus geht einmal durch den zweiten: zwischen dem Bump eines Baumes und der Veroeffentlichung der passenden Marke sind beide Seiten wieder gleich"
  - "navigation bleibt im Zustandsabbild, ohne noch gepruft zu werden. Es ist das App-Menue der Instanz zu Protokoll, und der Leser eines roten Laufs soll es nicht raten muessen"
  - "Die Ratsche aendert nur Namen und Meldungen. Die fuenf Werte bleiben zeichengleich, weil sie sich weder durch Phase 13 noch durch Phase 14 bewegt haben; der Kommentar sagt jetzt, dass ein Wert ueber zwei Minor-Spruenge staerker ist als einer ueber einen"

patterns-established:
  - "Der Upgrade-Beweis wird je Release auf die neueste Veroeffentlichung nachgezogen, und mit ihm wandert die sechste Zusicherung auf einen sichtbaren Unterschied, den der neue Sprung wirklich macht"

requirements-completed: []
requirements-partial:
  - "REL-02: der Upgrade-Beweis ist auf den Sprung 1.1.0 auf 1.2.0 umgestellt und lokal geprueft. Erfolgskriterium 3 ist erst mit einer Laufnummer belegt; der Pruefweg steht unten"

# Metrics
duration: 80 min
completed: 2026-09-21
---

# Phase 16 Plan 09: Der Upgrade-Beweis springt von v1.1.0 Summary

Der Beweis startet ab jetzt bei der Version, die die Leute wirklich installiert haben, und seine sechste Zusicherung misst die zwei Datumsgrenzen, die der Suchanbieter seit Plan 13-06 deklariert: vorher nicht da, nachher da, und die Vorbedingung des Vorher-Zustands hält genau dieselbe Eigenschaft frei, damit die Zusicherung nicht aus dem falschen Grund grün wird.

## Was gebaut wurde

### Task 1: Q-5 ist nachgesehen, nicht geraten (`12fec7d`)

Die offene Frage Q-5 der Recherche lautete: welcher sichtbare Unterschied zwischen 1.1.0 und 1.2.0 ist im Zustandsabbild ablesbar, das `snapshot()` schreibt? Beide Kandidaten sind an der Quelle geprüft worden.

**Kandidat 1, der sechste Engine-Zustand `unloaded` (Phase 14), trägt nicht.** Zwei Gründe, beide nachgesehen:

1. Das Feld ist nicht neu. `git show v1.1.0:php/lib/Service/AdminViewService.php` baut `engineState` bereits in die Übersichtsantwort ein (dort Zeile 1813, im heutigen Baum Zeile 1816). Seine Anwesenheit sagt also nichts, nur sein Wert könnte etwas sagen.
2. Der Wert ist hier nicht erreichbar. `engine_state()` in `backend/src/findling/embed/engine.py` antwortet `unloaded` nur, solange `unload_count()` über null steht (der Zweig in Zeile 358). Das verlangt eine Leerlaufspanne, in der der Container die Gewichte wirklich zurückgegeben hat. Der Auftrag registriert einen Container und liest ihn Minuten später; beide Hälften meldeten dasselbe Wort. Eine Zusicherung auf einem Wort, das an einer Zeitschaltung hängt, wäre ein Flattern und kein Beweis.

Der Vollständigkeit halber: die geschlossene Liste in `AdminViewService` ist in v1.1.0 fünfstellig (Zeile 177) und heute sechsstellig (Zeile 180), und `ENGINE_STATES` in `engine.py` desgleichen. Der Unterschied existiert also, er ist nur nicht in einem Abbild ablesbar, das niemand warten lässt.

**Kandidat 2, die Filter- und Sortierarbeit der Phase 13, trägt, und billiger als erwartet.** Die Recherche nahm an, ein Abbild müsse dafür die Ergebnisseite rendern. Muss es nicht: `GET /ocs/v2.php/search/providers` liefert je Anbieter eine Filterkarte, und `integration.yml` liest dieselbe Route seit Phase 1 im Schritt "The reported filters name term and title-only". `php/lib/Search/Provider.php` antwortete in `getSupportedFilters()` in v1.1.0 mit `term` und `title-only` (dort Zeile 133) und antwortet seit Plan 13-06 mit `term`, `title-only`, `since` und `until`.

Dazu kommt das Sachargument: eine nicht deklarierte Filterart ist genau das, was diesen Anbieter wortlos aus einer datierten Suche fallen ließ. Das ist eine Änderung, die auf einer bestehenden Installation ankommen muss und nicht nur auf einer frischen.

Gebaut wurde:

- `declared_filters()` in der geteilten Sonde, in derselben Bauform wie `navigation_ids()`: ein Status ungleich 200 und eine Antwort ohne `findling`-Anbieter kehren mit einer Meldung zurück, nie mit einer leeren Liste. Eine leere Liste wäre die eine Form, die die Zusicherung danach bedeutungslos macht, weil sie sich liest wie "diese Fassung deklariert nichts" statt wie "dieser Aufruf hat nicht funktioniert".
- `snapshot()` schreibt `searchFilters.declared` (die sortierte Namensliste) und `searchFilters.dates` (beide Grenzen vorhanden, ja oder nein).
- Der Q-5-Kommentar steht genau dort, wo `snapshot()` erweitert wird, und nennt den gewählten Kandidaten, die Begründung, den Grund gegen den anderen und die Belege als Dateiname mit Zeile beziehungsweise als `git show`-Befehl.
- `upgrade-providers.json` wandert in die Liste der gesicherten Belege, wie `upgrade-overview.json` daneben.

### Task 2: die vier Stellen, die von 1.0.3 erzaehlten (`0f112c3`)

1. **`UPGRADE_FROM_TAG: v1.1.0`.** Der Begründungsabsatz ist fortgeschrieben: v1.1.0 ist am 21.09.2026 die neueste Veröffentlichung, 1.2.0 lebt allein in diesem Baum (seit Plan 16-07), und `store-submit.yml` hat genau diese Bytes am 11.09.2026 eingereicht. Der alte Absatz zu v1.0.3 steht datiert als Vorgänger darunter, samt der Laufnummer 34526436580, die ihn belegte.
2. **Die Vorbedingung in "Store upgrade 1" ist umgedreht.** Sie verlangte die Abwesenheit des `<navigations>`-Blocks, weil `php/appinfo/info.xml` ihn erst in Plan 09-06 bekam. v1.1.0 trägt ihn, also verlangt sie jetzt seine Anwesenheit. Das ist keine Formalie: es ist die billigste Zusicherung der Datei, dass `UPGRADE_FROM_TAG` wirklich auf die 1.1.x-Reihe zeigt, denn eine Marke der 1.0.x-Reihe antwortete ohne den Block. Der alte Wortlaut steht datiert im Kommentar.
3. **Die zweite Vorbedingung des Vorher-Zustands** verlangte die Abwesenheit von `navigation.findling`; an ihre Stelle tritt die Abwesenheit von `searchFilters.dates`. Ohne diesen Tausch wäre Zusicherung 6 grün aus dem falschen Grund. `navigation` bleibt im Abbild stehen, ohne noch geprüft zu werden, weil es das App-Menü der Instanz zu Protokoll ist.
4. **Zusicherung 6** vergleicht `searchFilters.dates` vorher und nachher und nennt in ihrer Fehlermeldung Plan 13-06. Sie gibt bei rot beide Filterlisten und beide Menülisten aus.

Ohne Verhaltensänderung nachgezogen: die Kommentare, die 11-11 und 1.1.0 als Zukunft nannten. Der Versionsschritt in "Store upgrade 4" behält **beide** Zweige; heute läuft der erste, und der zweite bleibt, weil jeder Release-Zyklus einmal durch ihn geht, sobald ein Baum gebumpt und die passende Marke noch nicht veröffentlicht ist. Der Kommentar zum registrierten Abbild sagt jetzt den heutigen Grund: `backend/appinfo/info.xml` nennt seit 16-07 `image-tag 1.2.0`, und diese Marke liegt noch nicht in der Registratur, weil die Veröffentlichung Plan 16-14 ist. Deshalb wird weiterhin `info-citest.xml` registriert, das auf die lokale Registratur zeigt.

Alle Versionsliterale in aktiven Meldungen sind durch `${UPGRADE_FROM_TAG}` ersetzt. Wo "1.0.3" noch steht, steht es in einem Kommentar mit Datum als Vorgänger (Zeilen 94/95, 1723, 2470, 2494, 2917/2919, 3125, 3237).

### Task 3, Teil 1: die Ratsche nennt beide Minor-Reihen (`607f8d0`)

`GOLD_V1_0_3` heißt `GOLD_V1_0_AND_V1_1`. Die Meldung sagt "ein Upgrade von 1.0.x oder 1.1.x wuerde jetzt einen Reindex ausloesen (D-04)", der Testname nennt beide Reihen, und der Kommentar trägt den Satz, dass ein Wert, der über zwei Minor-Sprünge steht, stärker ist als einer, der über einen steht. **Die fünf Werte sind zeichengleich unverändert**, ebenso das Indexformat, der Debian-Pin und der tantivy-Pin.

## Verifikation

### Die Gates

Vor dem ersten Commit lief `uv sync`, weil die beiden Dependabot-Merges anlagen. Tatsächlicher Vorher-Stand danach:

| Paket | vorher | nachher |
|---|---|---|
| `pypdf` | 6.18.1 | **6.19.0** |
| `ruff` | 0.16.7 | **0.16.8** |

Der neue ruff brachte **keine neue Regel zum Tragen**: `ruff check .` meldete schon vor jeder Änderung "All checks passed", `ruff format --check .` "125 files already formatted". Es war also nichts zu fixen und nichts zu unterdrücken.

| Gate | Vorher-Stand | nach den Aenderungen |
|---|---|---|
| `ruff check .` | All checks passed | All checks passed |
| `ruff format --check .` | 125 files already formatted | 125 files already formatted |
| `PYRIGHT_PYTHON_FORCE_VERSION=latest pyright` | 0 errors, 0 warnings | 0 errors, 0 warnings |
| `vulture src tests --min-confidence 80` | leer | leer |
| volle `pytest -q` | **2469 passed / 15 skipped** | **2469 passed / 15 skipped** |
| `pytest tests/test_upgrade_compatibility.py -q` | 6 Faelle | **6 Faelle**, gruen |

Die Skipzahl ist unverändert, und die Fallzahl der Ratsche ist dieselbe wie vorher.

### Die YAML-Pruefung vor dem Commit

`yaml.safe_load` auf `.github/workflows/deploy-harp.yml`, mit `uv run python` aus dem Backend-Baum: ein Auftrag `deploy-harp`, **48 Schritte**, `env.UPGRADE_FROM_TAG` liest sich als `v1.1.0`, die sieben Schritte "Store upgrade 0" bis "Store upgrade 5" sind vollständig da. Vor und nach jedem der beiden Workflow-Commits gefahren.

Zusätzlich: das eingebettete Sondenskript `upgrade-probe.sh` ist aus dem Here-Dokument herausgelöst und mit `sh -n` geprüft worden. **250 Zeilen, keine Syntaxmeldung.**

### Die Zusicherungen 1 bis 5 sind zeichengleich

Der Block von `--- 1, the same hits` bis vor `--- 6,` ist aus `git show HEAD:...` und aus dem Arbeitsbaum gelesen und zeichenweise verglichen worden: **48 Zeilen, `zeichengleich: True`**. Auch `git diff -U0` zeigt in diesem Block keine Zeile.

### Die zwei lokal gefahrenen Probefaelle

Selbst gebaute Vorher- und Nachher-Abbilder, gegen die echten jq-Ausdrücke des Workflows gefahren.

**Erwarteter Fall.** Vorher `"declared": "term title-only"`, `"dates": false`; nachher `"declared": "since term title-only until"`, `"dates": true`.

```
=== Vorbedingung des Vorher-Zustands, erwarteter Fall ===
GRUEN: keine Datumsgrenzen vorher
=== Zusicherung 6, erwarteter Fall ===
GRUEN: vorher false, nachher true
```

**Fehlerfall A**, die Datumsgrenzen stehen schon im Vorher-Zustand:

```
::error::the provider of the v1.1.0 installation already declares the two date bounds
Their presence after the upgrade would then be no change at all.
{ "declared": "since term title-only until", "dates": true }
-> Schritt bricht ab (exit 1), wie gewollt
```

**Fehlerfall B**, Zusicherung 6, das Upgrade kam nicht an:

```
::error::the provider declared the two date bounds as false before the upgrade and as false
after it, and the change plan 13-06 made has to arrive on an existing installation
term title-only
term title-only
dashboard files findling settings
dashboard files findling settings
fail=1
```

Dazu die Extraktion aus der echten Antwortform: `jq -r '[.ocs.data[] | select(.id == "findling") | .filters | keys[]] | sort | join(" ")'` liefert auf einer nachgebauten v1.1.0-Antwort `term title-only`, auf einer v1.2.0-Antwort `since term title-only until`, und auf einer Antwort ohne `findling`-Anbieter die leere Zeichenkette, die den Fehlerpfad der Hilfsfunktion auslöst.

### Die umgedrehte Vorbedingung gegen die echten Marken

```
v1.0.3 -> the companion declares no navigation entry, so this is not the 1.1.x release
          this proof starts from (exit 1)
v1.1.0 -> the companion declares the navigation entry, as every release since v1.1.0 does
          (GRUEN)
```

### Die Bytes, auf die der Beweis zeigt

- **Release-Anhänge `v1.1.0`:** `findling.tar.gz` (282.432 B), `findling.tar.gz.sig`, `findling_backend.tar.gz` (28.524 B), `findling_backend.tar.gz.sig`. Über `gh release view v1.1.0` am 21.09.2026 nachgesehen.
- **Abbildmarke `ghcr.io/street1983nk/findling_backend:1.1.0`:** existiert als Index mit `linux/amd64` und `linux/arm64`. Anonym über das Manifest der Registratur am 21.09.2026 geprüft, auf demselben Weg, auf dem `:1.0.3` am 10.09.2026 geprüft worden war. `:1.2.0` existiert erwartungsgemäß **noch nicht**; das ist Plan 16-14, und deshalb registriert der Beweis weiterhin `info-citest.xml`.

## Was der Orchestrator in CI nachsehen muss

**Task 3, Teil 2 des Plans, konnte in dieser Ausführung nicht stattfinden.** Der Ausführungsauftrag verbietet das Pushen ausdrücklich, und `deploy-harp` läuft ausschließlich auf einem Runner. Lokal grün ist hier kein Beweis. Erfolgskriterium 3 von REL-02 ist deshalb **noch nicht belegt**; der Punkt steht mit Zieladresse in `deferred-items.md`.

**Der Pruefweg, Schritt fuer Schritt:**

1. **Auslöser.** Der Push der vier Commits startet die Werkbank von selbst: `deploy-harp.yml` horcht auf `push` mit `paths` unter anderem auf `.github/workflows/deploy-harp.yml` und `backend/**`. Kein `workflow_dispatch` nötig, und vor allem **kein `release_tag`-Eingang**: mit gesetztem Eingang läuft der Upgrade-Block per `if` gar nicht.
2. **Werkbank und Auftrag.** Werkbank "HaRP deploy", Auftrag `deploy-harp`, und von den Beinen **nur** `stable34` auf `ubuntu-24.04`. Die übrigen Beine überspringen die sieben Schritte per `if`; das ist so gewollt und kein Ausfall.
3. **Laufliste.** `gh run list --workflow=deploy-harp.yml --limit 5`, dann `gh run view <id> --log`.
4. **Die sieben Schritte.** "Store upgrade 0" bis "Store upgrade 5" plus "Store upgrade 3b".

**Die Pruefzeilen, an denen der Beweis haengt:**

| Schritt | Zeile, die dastehen muss |
|---|---|
| Store upgrade 1 | `the companion of v1.1.0 declares the navigation entry, as every release since v1.1.0 does` |
| Store upgrade 1 | `the v1.1.0 installation runs as <container> on the volume <volume>` |
| Store upgrade 3 | `three terms, one file each; no date bounds on the provider; the state is on record in upgrade-before.json` |
| Store upgrade 4 | `the instance performed the app update: 1.1.0 to 1.2.0` (der ERSTE Zweig; ein `::notice::` aus dem zweiten Zweig waere hier ein Befund) |
| Store upgrade 5 | `the two date bounds were not declared before the upgrade and are declared after it` |
| Store upgrade 5 | `all six assurances hold` |

Dazu der Beleganhang `harp-logs` mit `upgrade-before.json`, `upgrade-after.json` und **neu** `upgrade-providers.json`. Im Vorher-Abbild muss `searchFilters.declared` gleich `term title-only` stehen, im Nachher-Abbild `since term title-only until`.

**Bei rot gilt die Lehre aus 11-11 und die Regel des Plans:** die erste Handlung ist die Wiederholung (`gh run rerun <id> --failed`). Erst wenn sie Zeile für Zeile dasselbe liefert, ist es ein Befund, und dann gehören **beide** Laufnummern und die Ursache in die Notiz. Kein roter Lauf wird als Flattern abgelegt, ohne dass die Wiederholung ihn so ausgewiesen hätte. Ein Befund im Erzeugnis bekommt einen eigenen Eintrag in `deferred-items.md` oder, wenn er nutzerwirksam ist, einen eigenen Fix in dieser Phase.

**Wo die Wahrscheinlichkeit eines Befundes am höchsten ist**, damit die Suche nicht bei null anfängt:

- **"Store upgrade 4", erster Zweig.** Dieser Zweig ist noch nie gelaufen, seit die Migration `Version001200Date20260921000000` existiert. `occ upgrade` führt sie jetzt wirklich aus. Ein Fehler dort ist ein Befund im Erzeugnis und keine Formalie.
- **"Store upgrade 3b".** Der Schritt existiert genau deshalb, weil `doUpgrade()` mit einem echten Versionsschritt bis `checkAppsRequirements()` durchläuft. Er lief beim ersten echten Sprung als Reparatur; beim zweiten muss er wieder tragen.
- **Zusicherung 2, die fünf Marken.** Wenn eine sich bewegt hat, ist das eine Frage an den Owner und keine Teständerung; die Ratsche in `test_upgrade_compatibility.py` ist lokal grün und sagt, dass keine sich bewegt hat.

Zusätzlich lief `php.yml` für die Commits dieses Plans nicht lokal, aus demselben Grund wie in 16-06 und 16-07: kein PHP auf dieser Maschine. Dieser Plan ändert allerdings **keine** `.php`-Datei, also steht hier nichts Neues offen.

## Abweichungen vom Plan

### Auto-behobene Punkte

**1. [Rule 2 - fehlende Zusage] Der zweite Kandidat aus Q-5 wird anders gelesen als die Recherche vorschlug**

- **Gefunden bei:** Task 1
- **Sachverhalt:** Die Recherche hielt für die Filter- und Sortierarbeit der Phase 13 ein gerendertes Formular für nötig und nannte das "den teureren Weg". Beim Nachsehen zeigte sich, dass `/ocs/v2.php/search/providers` die Filterliste je Anbieter trägt und `integration.yml` diese Route bereits für dieselbe Frage liest.
- **Wirkung:** Kein Renderschritt, keine neue Abhängigkeit, dieselbe Aussage. Der Plan verlangte "durch Nachsehen und nicht durch Raten"; das Nachsehen hat einen dritten, billigeren Weg ergeben und nicht einen der zwei genannten.
- **Datei:** `.github/workflows/deploy-harp.yml`
- **Commit:** `12fec7d`

**2. [Rule 2 - Beleg sichern] `upgrade-providers.json` wandert in die gesicherten Belege**

- **Gefunden bei:** Task 1
- **Sachverhalt:** Die neue Hilfsfunktion schreibt eine Antwortdatei, die bei einem roten Lauf die entscheidende Auskunft trägt. Die Liste der kopierten Belege kannte sie nicht, also wäre sie mit dem Runner verschwunden.
- **Wirkung:** Ein roter Lauf lässt sich ohne Wiederholung lesen.
- **Datei:** `.github/workflows/deploy-harp.yml`
- **Commit:** `12fec7d`

**3. [Rule 3 - ueberholter Kommentar] Der Grund gegen die Marke des Baumes hat sich geaendert**

- **Gefunden bei:** Task 2
- **Sachverhalt:** Der Kommentar in "Store upgrade 4" begründete die Registrierung über `info-citest.xml` damit, dass `backend/appinfo/info.xml` noch `image-tag 1.0.3` sage und eine erneute Registrierung derselben Marke ein no-op wäre. Seit Plan 16-07 sagt die Datei `1.2.0`, und diese Marke liegt noch gar nicht in der Registratur (anonym geprüft: `MANIFEST_UNKNOWN`).
- **Wirkung:** Der Kommentar nennt jetzt den heutigen Grund und behält den alten als Vorgänger. Ohne die Korrektur läse der nächste Mensch eine Begründung, die auf das Gegenteil des heutigen Zustands zeigt.
- **Datei:** `.github/workflows/deploy-harp.yml`
- **Commit:** `0f112c3`

**4. [Rule 2 - Punkt ohne Adresse] Der ungefahrene Lauf bekommt einen Eintrag**

- **Gefunden bei:** Task 3
- **Sachverhalt:** Task 3, Teil 2 verlangt einen gefahrenen Auftrag; der Ausführungsauftrag verbietet das Pushen. Ein Erfolgskriterium, das offen bleibt, ohne dass es irgendwo steht, ist genau die Sorte Zusage, die dieses Projekt sonst mit Gates festhält.
- **Wirkung:** `deferred-items.md` trägt den Punkt mit Befund, Verdikt, Begründung und Zieladresse.
- **Datei:** `.planning/phases/16-haertung-und-store-einreichung-v1-2-0/deferred-items.md`
- **Commit:** `1c61216`

### Nicht ausgefuehrt

**Task 3, Teil 2 (den Lauf auslesen).** Nicht ausgeführt, weil der Ausführungsauftrag das Pushen verbietet und `deploy-harp` nur auf einem Runner läuft. Ein `workflow_dispatch` auf `main` liefe gegen die alte Fassung der Datei und bewiese nichts. Siehe "Was der Orchestrator in CI nachsehen muss" und den Eintrag in `deferred-items.md`. In der Folge nennt diese Zusammenfassung **keine Laufnummer und keine sechs Ein-Wort-Urteile**; beides gehört an den Orchestrator.

## Threat Flags

Keine neue Angriffsfläche. Die neue Hilfsfunktion liest eine bestehende, lesende OCS-Route als der gewöhnliche Testbenutzer, mit denselben Kopfzeilen, die die drei vorhandenen Hilfsfunktionen benutzen. `T-16-32` (ERROR_UP_TO_DATE) ist durch den Bump aus 16-07 gedeckt und wird durch die Prüfzeile in "Store upgrade 4" sichtbar; `T-16-33` (Zusicherung 6 grün aus dem falschen Grund) ist durch die getauschte Vorbedingung gedeckt; `T-16-34` (stumme Suche) durch die unveränderten Zusicherungen 1 bis 5; `T-16-35` (roter Lauf als Flattern abgelegt) durch die Wiederholungsregel oben. `T-16-SC`: keine neue Abhängigkeit, kein Installationsbefehl.

## Bekannte Stubs

Keine.

## Commits

1. `12fec7d` , `ci(16-09)`: Q-5 nachgesehen, `snapshot()` trägt die deklarierten Filter
2. `0f112c3` , `ci(16-09)`: der Upgrade-Beweis springt von v1.1.0 auf den Baum
3. `607f8d0` , `test(16-09)`: die Ratsche nennt beide Minor-Reihen
4. `1c61216` , `docs(16-09)`: der ungefahrene Upgrade-Beweis bekommt eine Adresse

## Self-Check: PASSED

Alle vier geaenderten beziehungsweise angelegten Dateien sind auf der Platte,
alle vier Commit-Kennungen sind in `git log`. Die Zusicherungen 1 bis 5 sind
zeichenweise gegen `HEAD` vor diesem Plan geprueft und unveraendert (48 Zeilen,
`zeichengleich: True`).
