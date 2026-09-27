---
phase: 20-ui-kataloge-es-it-nl-pt
plan: 08
subsystem: l10n
tags: [portugiesisch, pt_BR, varietaet, unterschieds-gate, drei-pluralformen, vorbehalt]

# Dependency graph
requires:
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 02
    provides: "PLURAL_FORM_OF['pt_BR'], FORM_COUNT_OF['pt_BR'] und die Messung, dass die Kerndatei pt_BR die Millionenform auf Index 1 schreibt"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 07
    provides: "pt_PT.json als Gegenstueck, die Giessform, die dreispaltige Sprachdoku und die vier Varietaetsproben"
provides:
  - "php/l10n/pt_BR.json und pt_BR.js: 202 Schluessel, eigene brasilianische Wortlaute, fuenf Pluralwerte mit drei Formen (Form 1 gleich Form 2), pt_BR-Regel mit nplurals=3"
  - "L10N_CATALOGUES mit sechzehn Eintraegen, acht Sprachcodes, eine Schluesselmenge"
  - "PORTUGUESE_WORDINGS_THAT_MUST_DIFFER (elf Schluessel mit Wortpaar), scan_named_difference und test_the_two_portuguese_catalogues_are_two"
  - "VALUES_THAT_MAY_EQUAL_THEIR_KEY['pt_BR'], gemessen: Findling und PDF"
  - "Docstring-Absatz zum Sprung von sechs auf sechzehn Katalogdateien bei unveraenderter Zahl 202"
  - "docs/l10n-portuguese.md vierspaltig, zwei G2-Listen, zweiter datierter Vorbehalt Plan 20-08"
affects: [20-09 (CI-Sprachbeweis laeuft auch fuer pt_BR), KAT-01, KAT-02]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Positives Unterschieds-Gate als benannte Liste mit Wortpaar je Schluessel statt Mindestzahl unterschiedlicher Werte; kein Textgleichheits-Gate in irgendeiner Richtung"
    - "Ein Listenschluessel, der in einem Katalog fehlt, ist ein Fund und kein stiller Ausfall"
    - "Tabellen-Neuerzeugung erst, nachdem dieselbe Erzeugung die alte Fassung zeichengleich reproduziert (204 von 204)"

key-files:
  created:
    - php/l10n/pt_BR.json
    - php/l10n/pt_BR.js
    - .planning/phases/20-ui-kataloge-es-it-nl-pt/20-08-SUMMARY.md
  modified:
    - backend/tests/test_admin_ui_contract.py
    - docs/l10n-portuguese.md

key-decisions:
  - "Katalogpaar pt_BR.json und pt_BR.js in EINEM Commit (592980d), erneut gemessen: ohne pt_BR.js stuerzt das Pluralregel-Gate mit FileNotFoundError ab (1 failed, 51 passed)"
  - "run und worker brasilianisch ANDERS entschieden als in pt_PT: a execucao statt a passagem, o processo de indexacao statt o processo de tratamento"
  - "Die Probe ecra gegen tela hat einen echten Gegenstand: zwei Schluessel sprechen von 'dieser Seite' der Verwaltung, pt_BR sagt tela, pt_PT sagt dort pagina (nicht ecra); a transferir gegen baixando hat weiterhin keinen Schluessel und ist so benannt"
  - "Suchbegriff in pt_BR in doppelten Anfuehrungszeichen U+201C/U+201D statt Guillemets"
  - "PORTUGUESE_WORDINGS_THAT_MUST_DIFFER fuehrt elf Schluessel; Gegenprobe mit pt_PT-Kopie ergibt elf Funde"
  - "72 von 202 Werten sind in beiden Varietaeten gleich, keiner kuenstlich verschieden gemacht"
  - "KAT-01 und KAT-02 sind mit diesem Plan erfuellt: alle zehn neuen Katalogdateien stehen"

requirements-completed: [KAT-01, KAT-02]

# Metrics
duration: 50min
completed: 2026-09-25
---

# Phase 20 Plan 08: Der brasilianisch-portugiesische Katalog Summary

**Findling spricht brasilianisches Portugiesisch: `pt_BR.json` und `pt_BR.js` führen die 202
Schlüssel mit eigenen Alltagswörtern (`arquivo`, `usuário`, `tela`, `senha`, `lixeira`,
`planilhas`, Gerundium), und ein neues Gate hält fest, dass die zwei portugiesischen Kataloge
zwei sind: eine Kopie von `pt_PT` fällt mit elf Funden rot.**

## Was gebaut wurde

- **Zwei Katalogdateien**, aus einer eigenen Wortlauttabelle gegossen und nicht aus `pt_PT.json`
  kopiert. Pluralwerte mit drei Formen, Form 1 gleich Form 2; die Millionenform der Kerndatei
  `core/l10n/pt_BR.json` wird ausdrücklich nicht übernommen. `pluralForm` zeichengleich mit
  `docs/l10n-catalogues.md` und `PLURAL_FORM_OF["pt_BR"]`.
- **Gate:** Konstantenpaar mit Begründungsabsatz, `L10N_CATALOGUES` mit 16 Einträgen,
  gemessene Ausnahmeliste `pt_BR`, die Unterschiedsliste mit elf Schlüsseln, der Scanner
  `scan_named_difference` und `test_the_two_portuguese_catalogues_are_two` mit Dreiklang
  (fehlende Dateien, Scan, zwei gestellte Zeilen). Dazu der Docstring-Absatz über der harten
  Zahl 202. Nur Zufügungen (169 Zeilen, 0 Löschungen).
- **Doku:** Tabelle vierspaltig, Wortwahl je Varietät, vollständige Varietätenprobe mit der
  Schlüsselliste des Gates, pt_BR-Absatz in "Pluralformen", zwei G2-Listen, Prüfungstabelle mit
  Spalte PT_BR, zweiter datierter Vorbehalt. Der Vorbehalt aus 20-07 ist unverändert.

## Aufgaben und Commits

| Task | Name | Commit | Dateien |
| --- | --- | --- | --- |
| 1 | pt_BR.json, samt gegossener pt_BR.js | `592980d` | `php/l10n/pt_BR.json`, `php/l10n/pt_BR.js` |
| 2 | Sechzehn Kataloge im Tupel, Unterschieds-Gate | `f79254c` | `backend/tests/test_admin_ui_contract.py` |
| 3 | docs/l10n-portuguese.md vierspaltig | `cd38e2d` | `docs/l10n-portuguese.md` |

## Die Begriffsentscheide

| Englisch | PT_PT | PT_BR |
| --- | --- | --- |
| the backend | o serviço | o serviço |
| run | a passagem | **a execução** |
| worker | o processo de tratamento | **o processo de indexação** |
| index | o índice, indexar, a indexação | gleich |
| coverage | a cobertura | gleich |

Begründungen stehen in der Wortwahltabelle von `docs/l10n-portuguese.md`.

## Messungen

| Kriterium | Ergebnis |
| --- | --- |
| Giessform gegen Bestand (7 Sprachen, je .json und .js) | 14 von 14 byteweise gleich |
| Schlüssel und Reihenfolge gegen `de.json` | 202 von 202 |
| Pluralwerte mit 3 Formen, Form 1 gleich Form 2 | 5 von 5 |
| `arquivo` / `usuário` / `tela` in `pt_BR.json` | 55 / 1 / 2 |
| `ficheiro` / `utilizador` / `ecrã` in `pt_BR.json` | 0 / 0 / 0 |
| U+2014, U+2013, U+2019, U+00A0, U+202F | 0 |
| Pipe, nacktes Prozentzeichen | 0 |
| `cmp pt_BR.json pt_PT.json` | verschieden |
| Werte gleich pt_PT | 72 von 202 |
| Ausnahmeliste: ohne Eintrag / leeres Mapping / zwei Einträge | AssertionError mit `['pt_BR']` / 4 Funde / grün |
| `scan_plural_rule` pt_BR: eigene / deutsche / spanische Regel | 0 / 2 / 1 Funde |
| Gegenprobe Kopie von pt_PT als pt_BR | 11 Funde, danach zurückgesetzt |
| `L10N_CATALOGUES` | 16 Einträge |
| `php/l10n/*.json` / `*.js` | 8 / 8 |
| Doku: vierspaltige Tabelle, 202 Zeilen, jeder Schlüssel vorhanden | ja |
| Doku-Schlüsselliste gleich `PORTUGUESE_WORDINGS_THAT_MUST_DIFFER` | ja, maschinell verglichen |
| `test_admin_ui_contract.py` / `test_public_artifacts.py` | 53 passed / 55 passed |
| Gesamtsuite | 2880 passed, 15 skipped (vor jedem Commit) |
| ruff check, ruff format --check, pyright (latest), vulture | grün |
| Git-Blobs der vier Dateien | 0 CR |
| `git diff --name-only 05f9ca7..HEAD -- php/templates php/js php/lib backend/src` | leer |

## Abweichungen vom Plan

### 1. [Rule 3 - Blocker, erneut gemessen] Katalogpaar in EINEM Commit

- **Gefunden in:** Task 1
- **Problem:** Der Plan schneidet `pt_BR.js` in Task 2. Mit beiseitegelegter `pt_BR.js` stürzt
  `test_every_catalogue_carries_the_plural_rule_of_its_language` mit `FileNotFoundError` ab.
- **Fix:** `.json` und `.js` zusammen in `592980d`, Gate-Änderung als eigener Commit. Wie in
  20-05 bis 20-07.

### 2. [Rule 1 - Messung berichtigt die Erwartung] Die Probe `tela` hat einen anderen Gegenstand

- **Gefunden in:** Task 1
- **Problem:** Kein Schlüssel spricht von einem Bildschirm, das Abnahmekriterium verlangt aber
  `tela` im Katalog.
- **Fix:** `tela` steht dort, wo es im Brasilianischen wirklich steht: für "diese Seite" der
  Verwaltung (zwei Schlüssel). `pt_PT` sagt dort `página`, nicht `ecrã`. Doku und
  Unterschiedsliste nennen das Wortpaar ehrlich als `página` gegen `tela`. `a transferir` gegen
  `baixando` bleibt ohne Schlüssel und ist in Gate-Kommentar und Doku so benannt.

### 3. [Rule 2 - Ergänzung] Der Scanner meldet auch fehlende Listenschlüssel

- `scan_named_difference` meldet einen Schlüssel der Liste, der in einem Katalog fehlt, als Fund,
  mit eigener gestellter Zeile. Sonst würde eine Umbenennung die Liste still entwerten.

## Was ausdrücklich NICHT geändert wurde

Kein Textgleichheits-Gate für pt_PT/pt_BR. Keine Datei unter `php/templates/`, `php/js/`,
`php/lib/`, `backend/src/findling`. `docs/l10n-catalogues.md`, die übrigen Kataloge und der
20-07-Vorbehalt liegen unverändert. Kein Eintrag im Vokabular-Gate nötig (55 passed). Nicht
gepusht.

## Bedrohungen dieses Plans

| ID | Erledigt durch |
| --- | --- |
| T-20-34 (pt_BR als Kopie) | Unterschiedsliste + Scanner + Gegenprobe mit 11 Funden |
| T-20-35 (nacktes Prozentzeichen) | `scan_percent_discipline` über beide Dateien, 0 Funde |
| T-20-36 (Millionenform auf Index 1) | Form 1 gleich Form 2 in 5 von 5, Begründung in Doku und Gate-Kommentar |
| T-20-37 (Platzhalter) | `scan_placeholder_parity` über 16 Dateien, 0 Abweichungen |
| T-20-38 (Sprung ohne Spur) | Docstring-Absatz zu sechzehn Katalogen |
| T-20-39 (geerbter Vorbehalt) | eigener Vorbehalt Plan 20-08, 20-07 unverändert |

## Bekannte Stubs

Keine.

## Authentifizierungs-Tore

Keine.

## Self-Check: PASSED

`php/l10n/pt_BR.json`, `php/l10n/pt_BR.js`, `docs/l10n-portuguese.md` und
`backend/tests/test_admin_ui_contract.py` liegen im Baum; die Commits `592980d`, `f79254c` und
`cd38e2d` stehen in der Historie.
