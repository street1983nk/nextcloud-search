---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 16
subsystem: php
tags: [phpunit, unit-tests, security-boundary, ci-gate, ex-app-id, body-cap, wall-clock]

# Dependency graph
requires:
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: 05-15, das PHPUnit-Geruest (bootstrap.php, phpunit.xml, composer.lock, Job phpunit) und die Verhaltensweisen 1 bis 6
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: 05-07, ExAppService ohne final-Schluesselwort und der Provider-Stand, gegen den die Faelle geschrieben sind
provides:
  - Tests fuer die Verhaltensweisen 7 bis 12 aus docs/testing.md, damit alle zwoelf abgedeckt sind
  - php/tests/Unit/GatewayControllerTest.php, der einzige Test der Abweisung einer fremden App-Id, die kein Integrationsjob erreicht
  - ExAppService::proxyRequest, die eine ausgehende Anfrage dieser App als benannte Naht
  - Provider mit stellbarer Uhr, sodass das Zeitbudget ohne Warten pruefbar ist
  - die Untergrenze MINIMUM_TESTS im Job phpunit steht auf 28 statt 14
  - die vollstaendige Abbildung aller zwoelf Nummern auf Testnamen (Tabelle unten), das Material fuer Plan 05-19
affects: [Plan 05-19 (ersetzt den Abschnitt "The gap" in docs/testing.md), Phase-Review (DI-05-18)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Eine Naht mit eigener Signatur statt eines Doubles der fremden Klasse dahinter, wenn die fremde Klasse im Autoload-Raum der Suite gar nicht existiert
    - Eine Reihenfolge wird ueber die Reihenfolge der Mock-Aufrufe behauptet und nie ueber das Ergebnis, weil ein Vertauschen das Ergebnis unveraendert laesst
    - Ein Deckel vor einem Parser wird bewiesen, indem zwei gleich lange Koerper mit und ohne gueltiges JSON denselben Ausgang nehmen, plus ein Gegenbeweis unterhalb des Deckels
    - Eine gestellte Uhr als optionales Konstruktorargument; Nextcloud faellt auf den Vorgabewert zurueck, weil der Container keine Closure bauen kann

key-files:
  created:
    - php/tests/Unit/GatewayControllerTest.php
  modified:
    - php/tests/Unit/ExAppServiceTest.php
    - php/tests/Unit/ProviderTest.php
    - php/lib/Service/ExAppService.php
    - php/lib/Search/Provider.php
    - .github/workflows/php.yml
    - docs/testing.md
    - .planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md

key-decisions:
  - "Die Transport-Naht ist ExAppService::proxyRequest mit eigener Signatur, nicht ein weicher Rueckgabetyp von publicFunctions: OCA\\AppAPI\\PublicFunctions gehoert einer anderen App und fehlt im Autoload-Raum der Suite, es gibt dort also nichts zu doppeln"
  - "Die Uhr des Providers ist ein optionales Closure-Argument statt einer ueberschreibbaren Methode, weil damit final an der Klasse bleibt"
  - "Verhalten 11 wird an zwei Stellen behauptet: der Provider reicht das Restbudget herunter, ExAppService verweigert unterhalb von MIN_CALL_SECONDS den Aufruf. Ein Fall, der beides im Provider behauptet, muesste so tun, als entscheide der Provider etwas, was er nicht entscheidet"
  - "MINIMUM_TESTS steigt von 14 auf 28, dieselbe Arithmetik wie in 05-15 (zwei je Verhalten und etwas Luft), nun fuer zwoelf statt sechs"
  - "docs/testing.md wird nur an den zwei Stellen nachgezogen, die dieser Plan falsch macht; den Abschnitt umschreibt Plan 05-19"

requirements-completed: [PKG-05]

duration: 28 min
completed: 2026-09-03
---

# Phase 5 Plan 16: Die restlichen sechs Verhaltensweisen der PHP-Haelfte Summary

Die Liste aus `docs/testing.md` ist abgearbeitet: alle zwoelf dokumentierten Eigenschaften der PHP-Haelfte haben einen Test, darunter die drei Verteidigungslinien, die der Sicherheits-Audit gezogen hat und die bis heute nur als Absicht im Quelltext standen. Die Suite waechst von 43 auf 66 Faelle, und eine Rotprobe hat vier dieser Linien einzeln gebrochen und dabei genau die acht Faelle rot gesehen, die sie tragen.

## Die Abbildung aller zwoelf Nummern

Das ist das Material, mit dem Plan 05-19 den Abschnitt "The gap" ersetzt. Keine Nummer fehlt.

| Nr | Eigenschaft, verkuerzt | Datei | Testnamen |
|----|------------------------|-------|-----------|
| 1 | `filterCandidates` verwirft einen Kandidaten ohne oder mit nicht ganzzahliger `fileId` | `ExAppServiceTest` | `testACandidateWithNoFileIdAtAllIsDropped`, `testACandidateWhoseFileIdIsNotAnIntegerIsDropped`, `testSomethingThatIsNotACandidateShapeAtAllIsDropped` |
| 2 | Nicht positive `fileId` ueberlebt nur als Kanarienvogel | `ExAppServiceTest` | `testACandidateWithoutAFileBehindItIsDroppedUnlessItIsTheCanary`, `testTheCanaryIsTheOneCandidateWithoutAFileBehindItThatSurvives`, `testTheCanaryWithoutASnippetIsDroppedLikeAnyOtherMalformedCandidate` |
| 3 | Jeder Kandidat mit positiver `fileId` verliert `title` und `snippet` | `ExAppServiceTest` | `testEveryCandidateWithAPositiveFileIdLosesItsTitleAndItsSnippet`, `testTheStrippingHoldsForEveryCandidateOfAPageAndNotOnlyTheFirst`, `testAPageMixingTheCanaryWithOrdinaryHitsKeepsBothRulesApart`, `testTheDroppedCandidatesAreCountedInOneLogLineAndNotNamed` |
| 4 | `Provider::search` verwirft einen nicht aufloesbaren Knoten, Titel und Link kommen aus dem Knoten | `ProviderTest` | `testACandidateWhoseNodeTheUsersOwnFolderCannotResolveNeverBecomesAHit`, `testTheTitleAndTheLinkComeOutOfTheResolvedNodeAndNotOutOfTheContainerAnswer`, `testANodeThatResolvesButIsNotReadableIsStillNotAHit` |
| 5 | Ohne Home-Verzeichnis ein leeres Ergebnis, keine ungeprueften Treffer | `ProviderTest` | `testAUserWithoutAHomeFolderGetsAnEmptyResultAndNotUncheckedHits`, `testTheMissingHomeFolderIsLoggedWithoutNamingAnythingTheUserSearchedFor` |
| 6 | `PlainText::bounded`: ein Leerzeichen je Steuerzeichen, Tabulator bleibt, Klemmung, Zeichengrenze, ungueltiges UTF-8 | `PlainTextTest` | `testEveryControlCharacterBecomesExactlyOneSpaceSoTheLengthIsPreserved`, `testAControlCharacterIsReplacedRatherThanRemoved`, `testTheTabIsTheOneCharacterOfThatRangeThatIsKept`, `testItCapsAtTheGivenLengthAndLeavesAShorterValueAlone`, `testItCutsOnACharacterBoundaryAndNeverInsideAMultibyteCharacter`, `testTheBoundaryHoldsForCharactersOutsideTheBasicPlaneToo`, `testInvalidUtf8IsRefusedAndNotRepaired`, `testValidUtf8ThatMerelyLooksExoticIsNotRefused` |
| 7 | Leerer Begriff ohne Roundtrip, Limit geklemmt in 1 bis 100 | `ExAppServiceTest` | `testAnEmptyTermIsRefusedWithoutASingleRoundTrip`, `testALimitBelowTheAcceptedRangeIsClampedToTheLowerBound`, `testALimitAboveTheAcceptedRangeIsClampedToTheUpperBound`, `testALimitInsideTheAcceptedRangeIsPassedOnUnchanged` |
| 8 | Antwortkoerper ueber einem Megabyte wird vor `json_decode` abgelehnt | `ExAppServiceTest` | `testAnAnswerAtTheBodyCapIsStillParsed`, `testAnAnswerAboveTheBodyCapIsRefusedBeforeItIsParsed`, `testAnAnswerBelowTheCapThatIsNotJsonTakesTheOtherExit` |
| 9 | `getFileContents` antwortet 403 bei fremder `EX-APP-ID` | `GatewayControllerTest` | `testACallFromTheBackendUnderItsOwnAppIdDeliversTheFileContents`, `testACallFromAForeignExAppIsRefused`, `testACallWithoutTheHeaderIsRefusedAndDoesNotFail`, `testTheRefusalForAForeignExAppSaysNothingAboutWhetherTheFileExists`, `testTheRefusalIsLoggedWithTheCallerAppIdAndWithNothingElse` |
| 10 | Hoechstens dreimal fragen, hoechstens `min(64, limit * 2)` Knoten aufloesen, Wanduhr von 2,5 s | `ProviderTest` | `testTheProviderAsksAtMostThreeTimes`, `testTheProviderResolvesAtMostTwoNodesPerDisplayedHitWhenTheLimitIsSmall`, `testTheProviderResolvesAtMostTheAbsoluteCeilingWhenTheLimitIsLarge`, `testTheProviderStopsAskingWhenTheWallClockIsUsedUp` |
| 11 | Auszuege erst nach dem Recheck, nur fuer Ueberlebende, bei verbrauchtem Budget gar nicht | `ProviderTest` und `ExAppServiceTest` | `testExcerptsAreOnlyRequestedAfterTheRecheck`, `testExcerptsAreRequestedOnlyForTheFileIdsThatSurvivedTheRecheck`, `testWhenTheBudgetIsGoneNoExcerptCanBeFetchedAndTheSublineIsThePath`, `testASpentBudgetCostsNoRoundTripForCandidatesAndNoneForExcerpts` |
| 12 | `filterSnippets` verwirft fremde fileids und die Bereiche eines gekuerzten Textes | `ExAppServiceTest` | `testAnExcerptForAFileIdThatWasNotAskedForIsDropped`, `testTheHighlightRangesOfATextTheCleaningShortenedAreDropped`, `testTheHighlightRangesOfATextThatOnlyChangedCharactersSurvive` |

Nummer 11 ist die einzige, die auf zwei Dateien verteilt ist, und das ist eine Feststellung ueber den Code und keine Bequemlichkeit; der Abschnitt "Ein Befund" unten sagt, warum.

## Was gebaut wurde

**Task 1, Verhalten 7, 8 und 12.** Elf Faelle in `ExAppServiceTest`, alle durch die oeffentlichen Methoden statt durch Reflection. Der leere Begriff traegt eine `never`-Erwartung an der Transport-Naht, also sagt der Fall "kein Roundtrip" und nicht bloss "kein Ergebnis". Die Klemmung wird an dem Limit gemessen, das tatsaechlich in der Anfrage ankam, und die Grenzen kommen per Reflection aus `MIN_LIMIT` und `MAX_LIMIT`. Der Koerperdeckel hat drei Faelle: genau auf dem Deckel wird verarbeitet, ein Byte darueber abgelehnt, und ein Byte darueber mit einem Koerper, der ueberhaupt kein JSON ist, nimmt denselben Ausgang und hinterlaesst dieselbe Logzeile. Dazu kommt der Gegenbeweis unterhalb des Deckels, ohne den "beide hinterlassen dieselbe Zeile" auch heissen koennte, dass beide den Parser erreicht haben.

**Task 2, Verhalten 10 und 11.** Sieben Faelle in `ProviderTest`. Die Fragegrenze und die Aufloesungsgrenze werden mit Seiten gefahren, deren Kandidaten samt und sonders am Recheck scheitern, sodass nur eine Grenze die Schleife beenden kann; die Aufloesungsgrenze wird zweimal gemessen, bei `limit` 10 gegen `limit * 2` und bei `limit` 100 gegen die absolute Obergrenze, und beide Zahlen kommen aus den Konstanten. Die Wanduhr steht still und wird von Hand bewegt: der einzige Vorgang, der hier Zeit kostet, ist der Roundtrip, und die erste Antwort verbraucht das ganze Budget. Die Reihenfolge Recheck vor Auszug wird ueber eine Liste der Mock-Aufrufe behauptet und nicht ueber das Ergebnis.

**Task 3, Verhalten 9.** Fuenf Faelle in der neuen `GatewayControllerTest`. Der erlaubte Fall liefert einen Strom und belegt dabei das `r` im `fopen`, die fremde App-Id und der fehlende Kopf enden beide bei `Http::STATUS_FORBIDDEN`, und der vierte Fall belegt, dass die Abweisung nichts ueber den Bestand verraet. Die tragende Haelfte dieses vierten Falls ist nicht der Vergleich der beiden Antworten, sondern die Erwartung, dass `IRootFolder::getUserFolder` gar nicht erst gerufen wird: die Gleichheit folgt daraus, dass zum Zeitpunkt der Antwort noch niemand ins Dateisystem gesehen hat.

Der Job `phpunit` faehrt seither mit `MINIMUM_TESTS: 28` statt 14, und `docs/testing.md` sagt nicht mehr, die Nummern 7 bis 12 seien offen.

## Belege

Alle Laeufe auf dem Zweig `worktree-agent-05-16`, Workflow `php.yml`.

| Lauf | Ergebnis | Was er zeigt |
|------|----------|--------------|
| 33775046356 | gruen | Task 1: `OK (54 tests, 128 assertions)`, `the suite executed 54 tests` |
| 33775394579 | gruen | Task 2: `OK (61 tests, 150 assertions)` |
| 33775620870 | gruen | Task 3 und die angehobene Untergrenze: `OK (66 tests, 171 assertions)`, `the suite executed 66 tests, the floor is 28` |
| 33775825306 | rot | Die Rotprobe, siehe unten |

Kein einziger der zwoelf Faelle ist bei seinem ersten Lauf rot gewesen: die Eigenschaften galten alle, was sie auch sollten, denn es sind dokumentierte Eigenschaften. Der Befund dieses Plans ist ein anderer und steht unten.

**Die Rotprobe.** Auf dem Wegwerf-Zweig `worktree-agent-05-16-redprobe` wurden vier der neu verteidigten Linien mit je einer Zeile gebrochen: der Wanduhr-Wachter in der Frageschleife, die absolute Aufloesungsobergrenze, der Koerperdeckel vor dem Parser und der Vergleich der `EX-APP-ID`. Ergebnis: `Tests: 66, Assertions: 164, Failures: 8`, und die acht sind genau die tragenden Faelle:

```
1) ExAppServiceTest::testAnAnswerAboveTheBodyCapIsRefusedBeforeItIsParsed
2) ExAppServiceTest::testAnAnswerBelowTheCapThatIsNotJsonTakesTheOtherExit
3) GatewayControllerTest::testACallFromAForeignExAppIsRefused
4) GatewayControllerTest::testACallWithoutTheHeaderIsRefusedAndDoesNotFail
5) GatewayControllerTest::testTheRefusalForAForeignExAppSaysNothingAboutWhetherTheFileExists
6) GatewayControllerTest::testTheRefusalIsLoggedWithTheCallerAppIdAndWithNothingElse
7) ProviderTest::testTheProviderResolvesAtMostTheAbsoluteCeilingWhenTheLimitIsLarge
8) ProviderTest::testTheProviderStopsAskingWhenTheWallClockIsUsedUp
```

Bemerkenswert ist, was NICHT rot wurde: `testTheProviderResolvesAtMostTwoNodesPerDisplayedHitWhenTheLimitIsSmall` blieb gruen, weil der entfernte Deckel nur die absolute Obergrenze war und ein kleines Limit sie nie erreicht. Genau dafuer gibt es zwei Faelle statt einem.

Der Zweig ist lokal und auf `origin` geloescht, der Arbeitszweig hat nie einen absichtlich kaputten Commit getragen, und `grep -rn "DELIBERATE DEFECT" php/` findet nichts.

## Ein Befund: Verhalten 11 wohnt in zwei Klassen

Die Spezifikation sagt, der Provider fordere bei verbrauchtem Budget "gar keine" Auszuege an. Der Code tut etwas leicht anderes, und es ist nicht falsch, nur anders verteilt: `Provider::search` ruft `ExAppService::snippets` immer, sobald ein Treffer ueberlebt hat, und reicht dabei das Restbudget herunter; die Weigerung selbst sitzt in `ExAppService::call`, das unterhalb von `MIN_CALL_SECONDS` gar nicht erst waehlt. Von aussen ist das Ergebnis dasselbe, es entsteht kein Roundtrip und kein Auszug, und die Unterzeile ist der Pfad.

Der Test bildet das ab, statt es zu glaetten. `testWhenTheBudgetIsGoneNoExcerptCanBeFetchedAndTheSublineIsThePath` behauptet, dass die heruntergereichte Zahl unter der Schwelle liegt und die Unterzeile der Pfad ist; `testASpentBudgetCostsNoRoundTripForCandidatesAndNoneForExcerpts` behauptet an der Klasse, die entscheidet, dass unterhalb der Schwelle nichts hinausgeht. Ein Fall, der im Provider ein `never` auf `snippets` gesetzt haette, waere rot gewesen, und er waere aus dem falschen Grund rot gewesen: er haette behauptet, der Provider entscheide etwas, was er nicht entscheidet. Das Abnahmekriterium des Plans ist damit erfuellt, seine Formulierung aber nicht woertlich, und das steht hier statt in einem stillen Kompromiss.

## Abweichungen vom Plan

### 1. [Rule 3 - Blocker] Die PHP-Haelfte hatte keine Naht zum Transport

- **Gefunden bei:** Task 1, beim Entwurf der Faelle zu Verhalten 7 und 8
- **Problem:** Beide Aussagen sind Aussagen ueber einen Roundtrip. Der Weg dorthin fuehrt durch `ExAppService::publicFunctions`, das `OCA\AppAPI\PublicFunctions` aus dem Nextcloud-Container holt. Diese Klasse gehoert einer anderen App, sie ist im Autoload-Raum der Suite nicht vorhanden, und PHPUnit kann nichts doppeln, was nicht existiert. Ohne Naht waren weder das geklemmte Limit noch der Koerperdeckel beobachtbar: das eine verschwindet in einer Anfrage, die nie gestellt wird, das andere sitzt hinter einer Antwort, die nie kommt.
- **Behebung:** `ExAppService::proxyRequest` als `protected` Methode mit eigener Signatur und eigenem Rueckgabetyp (`array|IResponse|null`). Sie haelt die Vorpruefung, die Backend-App-Id und den Timeout, und beide Aufrufwege benutzen sie, statt diese drei Dinge zweimal zu schreiben. Kein Verhalten aendert sich, die vier Fehlerfaelle und ihre Logzeilen sind unberuehrt.
- **Warum diese Form:** ein weicherer Rueckgabetyp an `publicFunctions` haette die Typinformation an der Aufrufstelle verloren. Eine Methode mit eigener Signatur ist eine Naht am Transport und an sonst nichts.
- **Datei:** `php/lib/Service/ExAppService.php` (steht nicht in `files_modified` des Plans)
- **Commit:** dde2692

### 2. [Rule 3 - Blocker] Die Wanduhr des Providers war nicht stellbar

- **Gefunden bei:** Task 2, ausdruecklich vom Plan vorgesehen ("die kleinste moegliche Naht")
- **Problem:** `Provider::search` liest `hrtime(true)` an drei Stellen direkt. Ein Fall zum Zeitbudget haette zweieinhalb echte Sekunden gewartet, was die Suite langsam macht und auf einem ausgelasteten Runner flackert.
- **Behebung:** ein optionales achtes Konstruktorargument, eine Closure, die Nanosekunden liefert, mit `hrtime(true)` als Vorgabe. Nextcloud loest es auf den Vorgabewert auf, weil der Container keine `Closure` bauen kann und bei einer nicht aufloesbaren Abhaengigkeit mit Vorgabewert genau diesen nimmt. Nichts in der App uebergibt das Argument.
- **Warum nicht die geschuetzte Methode:** ein Zeitgeber als Argument laesst `final` an der Klasse stehen, eine ueberschreibbare Methode nicht. Provider ist die Sicherheitsgrenze des Produkts, und `final` ist dort mehr wert als eine gesparte Zeile.
- **Datei:** `php/lib/Search/Provider.php` (steht nicht in `files_modified` des Plans)
- **Commit:** 85136e8

### 3. [Rule 1 - Bug] Zwei Aussagen wurden durch diese Arbeit falsch

- **Gefunden bei:** Abschluss von Task 3
- **Problem:** `.github/workflows/php.yml` fuehrte die Untergrenze 14 mit einem Kommentar, der ausdruecklich sagt, Plan 05-16 hebe sie an. `docs/testing.md` fuehrte die Nummern 7 bis 12 weiter als offen und sagte von Nummer 9, sie sei kein Unit-Test-Material.
- **Behebung:** `MINIMUM_TESTS: 28`, nach derselben Arithmetik wie 05-15, und zwei nachgezogene Absaetze in `docs/testing.md`.
- **Nicht angefasst:** die Einleitung derselben Datei, die weiterhin sagt, die PHP-Haelfte habe keinen Unit-Test. Diese Aussage ist seit Plan 05-15 falsch, wurde von diesem Plan nicht verursacht, und `docs/testing.md` benennt Plan 05-19 als den, der den Abschnitt umschreibt. Sie hier halb zu korrigieren, waere eine Kollision mit genau diesem Plan.
- **Dateien:** `.github/workflows/php.yml`, `docs/testing.md`
- **Commit:** d7c8970

**Gesamt:** 3 Abweichungen, alle automatisch behoben (2 Blocker, 1 Bug). **Auswirkung auf das Verhalten der App:** keine. Beide Produktivaenderungen sind Nahtstellen ohne Verhaltensaenderung, und die Rotprobe hat gezeigt, dass die Suite echte Aenderungen an den betroffenen Klassen bemerkt.

## Deferred Items

**DI-05-18:** DI-05-17 (Unit-Suite nur gegen `stable34`) bleibt offen, aber die Vorfrage, die es selbst stellt, ist beantwortet: die Signaturen der vier OCP-Schnittstellen, die diese Suite doppelt, sind am 03.09.2026 auf `stable32`, `stable33`, `stable34` und `stable35` identisch. Der heutige Nutzen einer vierfachen Suite waere also null, der Preis vier PHPUnit-Hauptversionen und vier Lockdateien, und der Paketbezug steht unter einem Owner-Gate. Adressiert an den Phase-Review, mit der Messtabelle als Material.

## Was diese sechs Faelle nicht koennen, ausdruecklich

Sie sagen nichts ueber HTTP. `GatewayControllerTest` prueft, was die Methode tut, wenn sie laeuft; ob die Route ueberhaupt noch ihre Attribute traegt, prueft Gate B in `backend/tests/test_php_trust_boundary.py`, und keiner der beiden sieht, was der andere sieht. Ebenso sagt der Koerperdeckel-Fall nichts darueber, ob AppAPI je einen Koerper dieser Groesse durchreicht, und der Wanduhr-Fall nichts darueber, wie lange eine echte Suche wirklich braucht. Was hier gemessen wird, ist die Logik zwischen den Schnittstellen, und das ist die Staerke und die Grenze einer Suite ohne Datenbank, Dateisystem und Netz.

## Threat Flags

Keine. Der Plan fuegt keine Netzroute, keinen Auth-Pfad und keine Schemaaenderung hinzu. Die vier Bedrohungen des Registers sind adressiert: T-05-65 durch die fuenf Faelle am `EX-APP-ID`-Kopf, darunter den ohne Kopf und den, der nichts ueber den Bestand verraet; T-05-66 durch die Reihenfolgepruefung ueber die Mock-Aufrufe, die in der Rotprobe als Klasse mitgetragen wurde; T-05-67 durch drei Faelle am Koerperdeckel und vier an Fragegrenze, Aufloesungsgrenze und Zeitbudget, alle Grenzen aus den Konstanten gelesen; T-05-SC dadurch, dass kein Paket bezogen wurde.

## Known Stubs

Keine.

## Naechster Schritt

Plan 05-19 kann den Abschnitt "The gap" in `docs/testing.md` durch die Tabelle oben ersetzen. Die zwei Aussagen in der Einleitung derselben Datei, die seit Plan 05-15 falsch sind, gehoeren in denselben Handgriff.

## Self-Check: PASSED

`php/tests/Unit/GatewayControllerTest.php` liegt auf der Platte, die fuenf Arbeits-Commits sind
in der Historie (dde2692, 7116959, 85136e8, a4a7ac5, d7c8970), der Wegwerf-Zweig der
Rotprobe ist lokal und auf `origin` verschwunden, `git status` ist ausser dieser
Zusammenfassung sauber, und weder `STATE.md` noch `ROADMAP.md` wurden angefasst.
Letzter Workflow-Lauf 33775620870: gruen, 66 Tests, Untergrenze 28.
