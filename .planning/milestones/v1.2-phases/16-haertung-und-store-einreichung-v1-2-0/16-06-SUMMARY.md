---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 06
subsystem: php-companion
tags: [a3, m-01, mem-03, instrumentierung, hrtime, protokollschwelle, baumhash]

# Dependency graph
requires:
  - phase: 15-messphase-eine-box-anfahrt
    provides: Befund M-01 (drei von vier Auspraegungen ueber 1,5 s, code=200 in allen vieren, innere Dauer nirgends ausgewiesen)
  - phase: 11-budget-und-decke
    provides: die drei Zeitdecken in ExAppService und die eine Stelle, an der der Aufruf abgesetzt wird
provides:
  - eine getrennte Zahl fuer den inneren Aufruf (hrtime um proxyRequest in ExAppService::call), in Millisekunden auf eine Nachkommastelle
  - eine Protokollzeile oberhalb von SLOW_CALL_LOG_MILLISECONDS mit genau drei Feldern und ohne Nutzerinhalt
  - die gemessene Dauer in allen vier Fehlerpfaden von call()
  - ein Textgate (backend/tests/test_exapp_call_instrumentation.py), das Sitz, Schwelle, Schweigen und Nutzerinhalt in CI-loser Umgebung haelt
affects: [16-08-a4-anfahrt, naechste-box-anfahrt, 16-12-phasenaudit]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Der innere Aufruf wird auf der PHP-Seite gemessen und nicht im Container: eine Messung im Container liesse Proxy und HaRP weg, also genau den Teil, der die Decke reissen laesst, ohne dass der Container etwas davon merkt"
    - "Eine Protokollzeile in einer ausgelieferten App steht hinter einer Schwelle, nicht hinter jedem Aufruf; die Unified Search fragt bei jedem Tastenanschlag"
    - "Ein Textgate liest die PHP-Quelle ueber die Zeilenfolge und nicht ueber blosse Anwesenheit, weil ein hrtime am Methodenanfang und eines am Methodenende jede Anwesenheitspruefung besteht und die Gesamtdauer unter neuem Namen misst"
    - "Ein gemessener Wert in einem Protokollfeld macht jeden Vergleich zweier Protokollzeilen nichtdeterministisch; der Vergleich normalisiert die Zahl und haelt dafuer den Schluessel fest"

key-files:
  created:
    - backend/tests/test_exapp_call_instrumentation.py
  modified:
    - php/lib/Service/ExAppService.php
    - php/tests/Unit/ExAppServiceTest.php
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Die Messung sitzt um den einen proxyRequest-Aufruf in call() und um sonst nichts. Zwischen den beiden Uhrablesungen steht genau eine Anweisung, und das Textgate prueft das ueber die Zeilenfolge"
  - "SLOW_CALL_LOG_MILLISECONDS = 1000.0, also unter der kleinsten der drei Zeitdecken. M-01 beschreibt Aufrufe NAHE der Decke; eine Schwelle auf der Decke saehe genau die nicht"
  - "Das Feld ceilingMs traegt die Decke, die fuer DIESEN Aufruf galt, also min(Decke, Restbudget) mal 1000 und nicht die Konstante. Ein Aufruf, dessen Budget kleiner war als seine Decke, wuerde sonst gegen eine Zahl gemessen, die er nie hatte"
  - "Alle VIER Fehlerpfade von call() tragen die gemessene Dauer, nicht nur die drei, die der Plan nennt. Der vierte Pfad ohne Wartezeit waere eine Luecke genau dort, wohin M-01 sieht"
  - "Die Protokollzeile laeuft auf info und hat genau drei Felder (path, innerMs, ceilingMs). Kein Suchbegriff, kein Dateiname, keine Kennung, kein Rumpf; ein PHP-Fall und ein Python-Gate halten das von beiden Seiten"
  - "Der Nachzug von PHP_TREE_HASH_TODAY liegt im selben Commit wie die PHP-Aenderung, und deshalb liegen Task 1, die PHP-Faelle aus Task 2 und Task 3 in einem Commit: ein Zwischenstand mit rotem Messgate waere ein Commit, den niemand fahren kann"

patterns-established:
  - "Ein PHPUnit-Fall, der eine gemessene Dauer sehen will, wartet wirklich (usleep) statt eine Uhr vorzutaeuschen; der Preis ist eine Sekunde Laufzeit und der Gegenwert ist, dass die echte Messung geprueft wird"
  - "Ein Textgate bringt seinen Selbsttest gegen eine gestagte Zeichenkette mit, damit ein geleerter Scanner nicht null Funde ueber null Anweisungen meldet und gesund aussieht"

requirements-completed: []
requirements-partial:
  - "HART-01: Auflage A3 ist auf der Entwicklungsmaschine gebaut. Die Zahl auf Zielhardware fehlt weiterhin und liefert erst die naechste Box; das Requirement wird in 16-13/16-14 abgehakt"

# Metrics
duration: 50 min
completed: 2026-09-21
---

# Phase 16 Plan 06: Instrumentierung des inneren Aufrufs Summary

Der Aufruf, dem die 1,5-Sekunden-Decke gilt, misst sich ab jetzt selbst: `hrtime` umschließt in `ExAppService::call` genau den einen `proxyRequest`-Aufruf, oberhalb von 1.000 ms entsteht eine `info`-Zeile mit drei Feldern und ohne jeden Nutzerinhalt, alle vier Fehlerpfade tragen dieselbe Zahl, und ein Textgate hält Sitz, Schwelle und Schweigen fest, weil auf dieser Maschine kein PHP läuft.

## Was gebaut wurde

**Task 1 und die PHP-Fälle aus Task 2 und Task 3, Commit `f604805`.**

Vier Bauteile in `php/lib/Service/ExAppService.php`:

| Bauteil | Form |
|---|---|
| Messung | `$startedAt = hrtime(true);` unmittelbar vor dem Aufruf, `$innerMs = round((hrtime(true) - $startedAt) / 1000000, 1);` unmittelbar danach |
| Schwelle | `public const SLOW_CALL_LOG_MILLISECONDS = 1000.0;` neben den Zeitkonstanten, mit dreiteiligem Begründungskommentar |
| Protokollzeile | `info`, nur oberhalb der Schwelle, Kontext genau `path`, `innerMs`, `ceilingMs` |
| Fehlerpfade | die vier `warning`-Zeilen von `call()` tragen zusätzlich `innerMs`, Stufe und Text unverändert |

Die Begründung der Schwelle sagt drei Dinge, weil die Zahl sonst nur eine Zahl
wäre: warum überhaupt eine Schwelle und keine Zeile je Aufruf (die Unified
Search fragt bei jedem Tastenanschlag, eine Zeile je Anschlag ist Rauschen und
keine Messung), warum sie unter der Decke liegt und nicht auf ihr (M-01
beschreibt Aufrufe NAHE der Decke) und dass sie eine Protokollschwelle ist und
keine Abbruchgrenze. Was einen Aufruf beendet, bleibt das Transportzeitlimit
`min(Decke, Restbudget)`; diese Zahl entscheidet nur, ob die gemessene Dauer
aufgeschrieben wird.

Nicht angefasst: die drei Zeitkonstanten, die Reihenfolge der vier Fehlerpfade,
die Behandlung von `$timeout < MIN_CALL_SECONDS` und die Berechtigungskette.
Kein Rückgabepfad hat sich geändert; der Diff zeigt Messung und Protokollierung
und sonst nichts.

Zwei neue PHPUnit-Fälle in `php/tests/Unit/ExAppServiceTest.php`:

1. Ein Aufruf, dessen Proxy `usleep` macht, bis die Schwelle überschritten ist,
   hinterlässt genau eine `info`-Zeile, deren Schlüssel genau `path`, `innerMs`
   und `ceilingMs` sind; zusätzlich wird nachgelesen, dass weder der Suchbegriff
   noch die Nutzerkennung in der Zeile stehen.
2. Ein Aufruf unterhalb der Schwelle hinterlässt KEINE `info`-Zeile. Das ist der
   wichtigere der beiden: ein Gate nur auf den lauten Fall bliebe grün für eine
   Klasse, die jeden einzelnen Aufruf protokolliert.

Der Fall wartet wirklich, statt eine Uhr vorzutäuschen. Was die Klasse
aufschreibt, ist eine echte `hrtime`-Ablesung um den Transport, also muss ein
langsamer Fall langsam sein. Eine Sekunde Laufzeit ist der Preis dafür, dass
geprüft wird, was tatsächlich gemessen wird.

`PHP_TREE_HASH_TODAY` zieht im selben Commit nach: `29dc890b...` statt
`8fdcd9df...`, `PHP_FILES_TODAY` bleibt bei 64, weil dieser Plan Bytes ändert
und keine Datei anlegt. Die Kommentarkette hat ihren Eintrag zu Plan 16-06 mit
Datum, den zwei geänderten Dateien und dem Grund. Die historischen Zwillinge
`PHP_TREE_HASH` und `PHP_FILES` sind unberührt.

**Task 2, das Textgate, Commit `e3fb6c5`.**

`backend/tests/test_exapp_call_instrumentation.py`, vier Fälle plus Selbsttest,
alle als Textproben über die PHP-Quelle:

| Fall | Was er hält | Bedrohung |
|---|---|---|
| Sitz der Messung | zwischen den beiden `hrtime`-Ablesungen steht genau eine Anweisung, und die ist der Proxyaufruf | T-16-22 |
| Schwellenbedingung | die Konstante steht in genau einer Bedingung, diese vergleicht die gemessene Variable, und die nächste Anweisung ist die Protokollzeile | T-16-20 |
| kein Nutzerinhalt | keine Protokollanweisung der Klasse enthält `$body`, `$userId`, `term`, `query` oder `filename` | T-16-21 |
| Schwellenwert | die Konstante ist lesbar und liegt unter der kleinsten der drei Zeitdecken | M-01 |

Zwei Bauentscheidungen tragen das Gate. Erstens prüft der Sitz über die
**Zeilenfolge** und nicht über Anwesenheit: ein `hrtime` am Methodenanfang und
eines am Methodenende bestünde jede Anwesenheitsprüfung und würde Klammerung,
Fehlerpfade und Parser mitmessen, also die Gesamtdauer unter neuem Namen.
Zweitens liest der Nutzerinhalts-Scanner **vollständige Anweisungen** und nicht
einzelne Zeilen: die Felder einer Warnung stehen unter der Zeile, die den Logger
nennt, und eine Zeilenprüfung läse die Meldung und übersähe alles, was mit ihr
reist. Dazu eine Untergrenze von zehn gefundenen Anweisungen, damit ein
geleerter Scanner nicht null Funde über null Anweisungen meldet.

Der Selbsttest fährt den Scanner gegen eine gestagte Zeichenkette mit
`'term' => $body['query']` und verlangt drei Funde, und gegen die harmlose
Längenzeile mit `$responseBody` und verlangt keinen. Die Muster sind
wortgebunden, weil das `Body` in `$responseBody` eine Länge ist und kein Inhalt;
ein Gate, das darauf rot würde, wird abgeschaltet.

## Die Grenze der Auflage A3

Dieser Plan liefert die Instrumentierung, nicht die Zahl. Die Messung entsteht
auf der Entwicklungsmaschine; **eine Zahl auf Zielhardware gibt es nicht und
soll es hier auch nicht geben**. Sie liefert erst die nächste Box, und wenn A4
als Anfahrt gefahren wird, kann sie die Zahl ohne Umbau mitnehmen: die
Protokollzeile steht schon da, sie muss nur aus dem Nextcloud-Protokoll gelesen
werden. Das steht so in der Auflage und ist hier keine Einschränkung, sondern
der vereinbarte Umfang.

Was ab jetzt entscheidbar ist: ob der innere Aufruf seine Decke hält. Was die
vier Rohdateien der Phase-15-Anfahrt ausweisen, bleibt die Gesamtdauer der
Anfrage auf der Nutzerroute, und daran ändert dieser Plan nichts.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - fehlende kritische Vollstaendigkeit] Vier Fehlerpfade statt drei**

- **Found during:** Task 1
- **Issue:** Der Plan spricht von "den drei bestehenden `warning`-Zeilen der
  Fehlerpfade". `call()` hat vier: unerreichbarer Container, Statuscode ab 400,
  Rumpf über der Grenze, nicht parsbarer Rumpf. Der vierte steht einzeilig und
  ist deshalb beim Zählen vermutlich untergegangen.
- **Fix:** Alle vier tragen `innerMs`. Ein Fehlerpfad ohne Wartezeit wäre eine
  Lücke genau dort, wohin M-01 sieht, und zwei Formen derselben Zeile sind der
  Ort, an dem zwei Zweige auseinanderlaufen.
- **Files modified:** php/lib/Service/ExAppService.php
- **Commit:** f604805

**2. [Rule 1 - Bug] Ein bestehender PHP-Fall waere durch die Messung nichtdeterministisch geworden**

- **Found during:** Task 2
- **Issue:** `testAnAnswerAboveTheBodyCapIsRefusedBeforeItIsParsed` vergleicht
  die Warnungen zweier Läufe **feldweise** (`assertSame`). Mit `innerMs` im
  Kontext vergleicht dieser Fall eine echte Uhrablesung gegen eine zweite und
  wäre ab dem ersten Lauf ein Wackelkandidat.
- **Fix:** Ein Helfer `withoutTheMeasuredDuration` ersetzt die gemessene Zahl
  durch ihren eigenen Namen und verlangt dabei, dass der Schlüssel überhaupt da
  ist und eine Fließkommazahl trägt. Die Aussage des Falls (beide Rümpfe
  hinterlassen dieselbe Zeile, also wurde die Länge zuerst beurteilt) bleibt
  vollständig erhalten und wird um eine Zusicherung reicher.
- **Files modified:** php/tests/Unit/ExAppServiceTest.php
- **Commit:** f604805

**3. [Rule 3 - blockierende Randbedingung] Der Commitschnitt**

- **Found during:** Task 3
- **Issue:** Der Plan will einen Commit je Task, verlangt aber zugleich, dass
  der Baumhash-Nachzug im selben Commit wie die PHP-Änderung liegt. Beide
  PHP-Dateien dieses Plans (Quelle und Testdatei) bewegen den Hash, also gäbe
  ein Commit je Task entweder zwei Hash-Bewegungen mit zwei Einträgen in der
  Kommentarkette oder einen Zwischenstand mit rotem Messgate.
- **Fix:** Zwei Commits statt drei. `f604805` trägt die PHP-Quelle, die
  PHP-Fälle und den Hash-Nachzug (die Kommentarform des Plans nennt selbst
  beide PHP-Dateien in einem Eintrag), `e3fb6c5` trägt das Python-Textgate. Der
  Baum war vor und nach jedem der beiden Commits grün.
- **Files modified:** (Commitschnitt, keine zusaetzliche Datei)
- **Commit:** f604805, e3fb6c5

### Entscheidungen im Rahmen des Plans

- **`ceilingMs` trägt die Decke dieses Aufrufs, nicht die Konstante.** Der Plan
  nennt nur den Feldnamen. Geschrieben wird `min(Decke, Restbudget) * 1000`,
  also die Zahl, gegen die die gemessene Dauer tatsächlich lief. Ein Aufruf,
  dessen Restbudget kleiner war als seine Decke, würde sonst gegen eine Grenze
  ausgewiesen, die für ihn nie galt, und genau diese Verwechslung ist der Kern
  von M-01.
- **Das Textgate hat fünf Testfunktionen, nicht vier.** Die vier Fälle des Plans
  plus der Selbsttest, den die Abnahmekriterien desselben Plans verlangen.

## Was offen bleibt

**Der PHPUnit-Lauf steht aus.** Auf dieser Maschine gibt es kein PHP, und der
Auftrag verbietet das Pushen, also ist `php.yml` für diese beiden Commits noch
nicht gelaufen und es gibt keine Laufnummer zu nennen. Der Workflow ist
pfadgefiltert auf `php/**` und startet mit dem Push dieser Commits von selbst;
zu prüfen sind dann der Auftrag `php -l` und der Auftrag PHPUnit, dessen
Mindestzahl `MINIMUM_TESTS: 28` durch die zwei neuen Fälle weiter steigt.
Statisch geprüft wurde stattdessen, was ohne PHP prüfbar ist: die Klammerbilanz
beider Dateien (Geschweifte, Runde, Eckige je null) und die vier Aussagen des
Textgates über die geänderte Quelle.

## Gate-Protokoll

Gefahren am 21.09.2026 auf der Entwicklungsmaschine, in der Reihenfolge von
`.github/workflows/python.yml`, gegen den Baum von `e3fb6c5`.

| Stufe | Befehl | Ausgang |
|---|---|---|
| 1 | `uv run pytest tests/test_exapp_call_instrumentation.py -q` | grün, 5 Fälle |
| 2 | `uv run pytest tests/test_measurement_scripts.py -q -k "php"` | grün, 2 ausgewählt |
| 3 | `uv run ruff check .` | grün, All checks passed |
| 4 | `uv run ruff format --check .` | grün, 125 Dateien bereits formatiert |
| 5 | `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` | grün, 0 errors, 0 warnings, 0 informations |
| 6 | `uv run vulture src tests --min-confidence 80` | grün, keine Ausgabe |
| 7 | `uv run pytest -q` (VOLLE Suite) | grün, **2469 bestanden, 15 übersprungen**, 209,74 s |
| 8 | `php -l`, PHPUnit | **nicht gefahren**, kein PHP auf dieser Maschine, kein Push |

Die Skipzahl ist unverändert 15 gegen den Stand nach 16-05 (2464 bestanden und
15 übersprungen); die fünf zusätzlichen bestandenen Fälle sind genau die des
neuen Textgates.

## Verification

1. Die Messung sitzt um `proxyRequest` und nirgends sonst: **ja**, zwei
   `hrtime`-Ablesungen in `call()`, dazwischen genau eine Anweisung, gehalten
   von Fall 1 des Textgates.
2. Unterhalb der Schwelle schweigt die App, oberhalb schreibt sie drei Felder:
   **ja**, ein PHP-Fall je Richtung und Fall 2 des Textgates.
3. Keine Protokollzeile trägt Nutzerinhalt, und ein Gate hält das fest: **ja**,
   Fall 3 mit Selbsttest gegen eine gestagte Zeichenkette.
4. `PHP_TREE_HASH_TODAY` ist nachgezogen, `PHP_FILES_TODAY` steht bei 64:
   **ja**, `29dc890b...` und 64.
5. Volle Suite grün, PHP-Teil in CI: **halb**, die Suite ist grün, der PHP-Teil
   läuft erst mit dem Push (siehe "Was offen bleibt").

## Self-Check: PASSED

- `backend/tests/test_exapp_call_instrumentation.py`: vorhanden, neu.
- `php/lib/Service/ExAppService.php`, `php/tests/Unit/ExAppServiceTest.php`,
  `backend/tests/test_measurement_scripts.py`: vorhanden und geändert.
- Commits `f604805` und `e3fb6c5`: in `git log` vorhanden.
- `git show --stat f604805` zeigt die PHP-Änderung und den Hash-Nachzug im
  selben Commit; `git diff --diff-filter=D HEAD~2 HEAD` nennt keine gelöschte
  Datei.
- Keine Stubs: der Plan legt keine Platzhalterdaten an; die einzige neue
  Funktion in der ausgelieferten App ist die Protokollzeile, und sie ist von
  beiden Seiten geprüft.
