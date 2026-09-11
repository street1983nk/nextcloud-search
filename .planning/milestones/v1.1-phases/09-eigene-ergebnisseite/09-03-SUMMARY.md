---
phase: 09-eigene-ergebnisseite
plan: 03
subsystem: api
tags: [php, refactoring, sicherheitsgrenze, gates, lockstep, paginierung]

requires:
  - phase: 05-haertung
    provides: Provider::search mit Recheck-Schleife, ProviderTest, ExAppService mit MAX_LIMIT
  - phase: 09-eigene-ergebnisseite
    provides: "09-01: ceilingSeconds als Parameter von searchCandidates, snippets und call"
provides:
  - SearchService::run als einzige Stelle des PHP-Baums, die die Lesbarkeitsfrage stellt
  - SearchCaps mit sieben Deckeln als Argumente beider Aufrufer
  - SearchOutcome mit vier benannten Fehlergruenden, darunter offset_ceiling
  - ApprovedHit mit Titel, Pfad und neu dem Mimetype aus dem bestaetigten Node
  - SearchService::MAX_CONTAINER_OFFSET = 1200 als gespiegelte Container-Decke
  - backend/tests/test_php_acl_boundary.py als Zaehl-Gate ueber die Berechtigungsentscheidung
  - backend/tests/test_search_limits_lockstep.py als Drift-Gate ueber beide Decken
  - php/tests/Unit/SearchServiceTest.php mit 21 Faellen
affects: [09-04, 09-05, 09-06, 09-07, 09-08, PageController]

tech-stack:
  added: []
  patterns:
    - "Vier Konstantenfamilien werden ein benanntes Wertobjekt (SearchCaps) statt sieben optionaler Argumente"
    - "Eine gespiegelte Fremdkonstante bekommt einen eigenen Fehlergrund und ein Lockstep-Gate"
    - "Ein Zaehl-Gate mit benanntem Register statt einer Behauptung ueber genau eine Aufrufstelle"
    - "@final statt final, wo PHPUnit ein Test-Double braucht (Muster von ExAppService)"

key-files:
  created:
    - php/lib/Service/SearchService.php
    - php/lib/Service/SearchCaps.php
    - php/lib/Service/SearchOutcome.php
    - php/lib/Service/ApprovedHit.php
    - php/tests/Unit/SearchServiceTest.php
    - backend/tests/test_php_acl_boundary.py
    - backend/tests/test_search_limits_lockstep.py
  modified:
    - php/lib/Search/Provider.php
    - php/lib/Service/ExAppService.php
    - php/tests/Unit/ProviderTest.php
    - php/lib/Service/QueueService.php
    - php/lib/Listener/GroupEventListener.php
    - php/lib/Listener/ShareEventListener.php
    - docs/testing.md

key-decisions:
  - "SearchService traegt @final statt final, weil PHPUnit kein Double einer finalen Klasse bauen kann und ProviderTest den Dienst mockt"
  - "ExAppService::REQUEST_TIMEOUT_SECONDS wird oeffentlich, damit der Dialog seinen Deckel benennen kann statt ihn zu kopieren"
  - "Der ACL-Gate haelt die Lesbarkeitsfrage auf genau eine Stelle und die Aufloesung auf ein Register von drei benannten Stellen, weil der Baum drei legitime Aufloesungen hat"
  - "Der Mimetype laeuft ebenfalls durch PlainText::bounded (T-09-03), verwirft aber nie einen Treffer"

patterns-established:
  - "Ein Gate, dessen Erwartung der Bestand widerlegt, wird zum benannten Register statt zur gesenkten Erwartung"
  - "Lokale Verhaltensprobe fuer PHP ohne PHPUnit: Stand-in-Welt in .dev/, Quelldateien per docker cp, php im Container"

requirements-completed: [UI-03]

duration: 145min
completed: 2026-09-09
---

# Phase 9 Plan 03: Geteilter Recheck-Dienst Summary

**Die Recheck-Schleife lebt ab jetzt einmal, in `SearchService::run`, mit allen sieben Deckeln als Argument; der Provider uebersetzt und rendert nur noch, ein Cursor jenseits von 1200 heisst `offset_ceiling` statt "Backend stumm", und zwei neue Python-Gates halten beides fest.**

## Performance

- **Duration:** rund 145 min
- **Tasks:** 3
- **Files:** 14 (7 neu, 7 geaendert), 2.274 Zeilen dazu, 831 weg

## Accomplishments

- `SearchService` traegt die Schritte 3 bis 10 des alten `Provider::search()` woertlich, samt Kommentaren, und ist die einzige Stelle im PHP-Baum, die die Lesbarkeitsfrage stellt.
- Die vier Konstantenfamilien sind sieben Felder von `SearchCaps`. Der Dialog schreibt seine Zahlen aus (20 bis 25 Treffer, 3 Runden, Overfetch 4, 2 und 64 Rechecks, 2,5 s, Per-Call-Deckel `ExAppService::REQUEST_TIMEOUT_SECONDS`), die Seite wird ihre eigenen ausschreiben.
- `SearchOutcome` kennt vier Fehlergruende. `offset_ceiling` ist neu und loest Pitfall 1 der Phase: der Startcursor wird vor jedem Kandidatenaufruf gegen `MAX_CONTAINER_OFFSET = 1200` geprueft, es wird nicht gerufen, und die falsche Aussage "Die Suche antwortet gerade nicht" kann nicht mehr entstehen.
- `ApprovedHit` traegt zusaetzlich den Mimetype, aus demselben bestaetigten Node wie Titel und Pfad und ebenfalls durch `PlainText::bounded` (T-09-03). Der Canary bleibt die eine benannte Ausnahme und traegt einen leeren Mimetype.
- Der Provider ist von 590 auf 271 Zeilen geschrumpft und hat `IRootFolder`, `IUserMountCache` und `IFileAccess` verloren. Seine Rueckgabeform ist unveraendert: dieselben Eintraege, dieselbe Reihenfolge, `paginated` genau dann, wenn es weitergeht.
- `SearchServiceTest` (21 Faelle) und `ProviderTest` (12 Faelle) teilen sich die 14 Faelle von vorher plus 19 neue. Kein Fall ist ersatzlos entfallen; die Zuordnung steht unten Zeile fuer Zeile.
- Zwei neue Gates mit Selbsttests: `test_php_acl_boundary.py` (8 Faelle) und `test_search_limits_lockstep.py` (9 Faelle).

## Task Commits

1. **Task 1: Die drei Wertobjekte und der geteilte Dienst** - `f185d39` (feat)
2. **Task 2: Der Provider reicht durch, und die Tests ziehen um** - `d814157` (refactor)
3. **Task 3: Zaehl-Gate und Drift-Gate** - `e230515` (test)

## Die Zuordnung der Testfaelle, Zeile fuer Zeile

`ProviderTest.php` hatte 14 Testmethoden. Wohin jede gegangen ist:

| Alter Fall (ProviderTest) | Wohin | Neuer Name |
|---|---|---|
| `testACandidateWhoseNodeTheUsersOwnFolderCannotResolveNeverBecomesAHit` | SearchServiceTest | gleicher Name |
| `testTheTitleAndTheLinkComeOutOfTheResolvedNodeAndNotOutOfTheContainerAnswer` | geteilt | SearchServiceTest: `testTheTitleAndThePathComeOutOfTheResolvedNodeAndNotOutOfTheContainerAnswer` (Titel und Pfad), ProviderTest: `testAnEntryIsBuiltOutOfTheApprovedHitAndItsExcerpt` (der Link ueber den URL-Generator) |
| `testANodeThatResolvesButIsNotReadableIsStillNotAHit` | SearchServiceTest | gleicher Name |
| `testAUserWithoutAHomeFolderGetsAnEmptyResultAndNotUncheckedHits` | SearchServiceTest | `testAUserWithoutAHomeFolderGetsNoHitsAndNotUncheckedOnes` |
| `testTheMissingHomeFolderIsLoggedWithoutNamingAnythingTheUserSearchedFor` | SearchServiceTest | gleicher Name |
| `testAnEmptyTermIsNotEvenAskedAbout` | ProviderTest | gleicher Name, jetzt gegen den gemockten Dienst |
| `testTheProviderAsksAtMostThreeTimes` | SearchServiceTest | `testTheServiceAsksAtMostAsOftenAsTheCapsAllow` |
| `testTheProviderResolvesAtMostTwoNodesPerDisplayedHitWhenTheLimitIsSmall` | SearchServiceTest | `testTheServiceResolvesAtMostTwoNodesPerDisplayedHitWhenThePageIsSmall` |
| `testTheProviderResolvesAtMostTheAbsoluteCeilingWhenTheLimitIsLarge` | SearchServiceTest | `testTheServiceResolvesAtMostTheAbsoluteCeilingWhenThePageIsLarge` |
| `testTheProviderStopsAskingWhenTheWallClockIsUsedUp` | SearchServiceTest | `testTheServiceStopsAskingWhenTheWallClockIsUsedUp` |
| `testExcerptsAreOnlyRequestedAfterTheRecheck` | SearchServiceTest | gleicher Name |
| `testExcerptsAreRequestedOnlyForTheFileIdsThatSurvivedTheRecheck` | SearchServiceTest | gleicher Name |
| `testWhenTheBudgetIsGoneNoExcerptCanBeFetchedAndTheSublineIsThePath` | geteilt | SearchServiceTest: `testWhenTheBudgetIsGoneNothingIsLeftToHandDownToTheExcerptCall` (Restbudget und Treffer), ProviderTest: `testTheSublineIsThePathOfTheHitWhenNoExcerptArrived` (die Subline) |
| `testTheProviderDeclaresBothBuiltinFiltersSoTheDialogNeverSkipsIt` | ProviderTest | gleicher Name |

Neu in `SearchServiceTest` (9): die vier vom Plan geforderten (`ACursorBeyondTheOffsetCeiling...`, `ABackendSilentOnTheFirstCall...`, `ABackendThatGoesSilentAfterHits...`, `TheMimeTypeOfAHitComesOutOfTheNode...`), dazu `ACursorAtTheOffsetCeilingIsStillAsked` (die andere Seite des Vergleichs), `AVersionDriftOnRecordCostsTheRunAndIsNamedAsThat`, `ALowerRoundCapReallyLowersTheNumberOfQuestions` (Gegenprobe zur Rundenzahl), `ThePerCallCeilingOfTheCapsTravelsWithBothCalls`, `TheCanaryTravelsAsAHitOfItsOwnWithoutATypeAndWithoutAResolution`.

Neu in `ProviderTest` (10): `TheCapsCarryTheConstantsOfTheDialogAndTheLimitOfTheQuery`, `ALimitOfZeroStillAsksForOneHit`, `TheCursorAndTheTitleOnlyFilterOfTheQueryTravelIntoTheRun`, `ACursorThatIsNotANumberStartsOverAtTheTop`, `EveryFailureOfTheServiceBecomesTheSameEmptyGroup`, `AnOutcomeWithMoreBehindItBecomesAPaginatedGroupCarryingItsCursor`, `AnOutcomeThatHitThePagingCeilingIsShownWithItsHitsAndWithoutANextPage`, `AnEntryIsBuiltOutOfTheApprovedHitAndItsExcerpt`, `TheSublineIsThePathOfTheHitWhenNoExcerptArrived`, `TheCanaryIsLinkedToTheFileListAndNotToAFileId`.

Summe: 14 vorher, 33 nachher (21 plus 12), also 19 mehr statt der geforderten vier.

## Decisions Made

- **`SearchService` ist `@final`, nicht `final`.** Der Plan verlangt vier finale Klassen und zugleich, dass `ProviderTest` den Dienst mockt. Beides zusammen geht nicht: PHPUnit kann kein Double einer finalen Klasse bauen. `ExAppService` steht seit Phase 5 vor genau derselben Wahl und loest sie mit der `@final`-Annotation plus einem Docblock, der den Grund nennt. Der Dienst folgt diesem Muster; die drei Wertobjekte bleiben `final`, weil niemand sie mockt.
- **`ExAppService::REQUEST_TIMEOUT_SECONDS` wird oeffentlich.** Der Provider soll laut Plan genau diese Zahl als Per-Call-Deckel setzen, und eine private Konstante kann er nicht lesen. Die Alternative waere ein zweiter Literalwert 1.5 im Provider gewesen, also genau die Kopie, die die Phase an anderer Stelle mit einem Lockstep-Gate bekaempft.
- **Der ACL-Gate zaehlt zwei Namen nach zwei verschiedenen Regeln.** Der Bestand hat drei Aufrufer von `getFirstNodeById` (Suchgrenze, Inhalts-Gateway, Crawl), also kann kein ehrlicher Gate "genau eine Stelle" behaupten. Die Lesbarkeitsfrage dagegen steht wirklich genau einmal, und sie ist die Suchgrenze: eine zweite Recheck-Schleife braucht sie zwingend. Also: Lesbarkeit auf genau eine Stelle festgenagelt, Aufloesung als benanntes Register mit Zahl je Datei (Ratsche).
- **Der Mimetype wird ebenfalls geklemmt.** Das Threat-Register (T-09-03) sagt "alle drei Felder durch `PlainText::bounded`". Anders als Titel und Pfad verwirft ein nicht saeuberbarer Mimetype aber keinen Treffer, sondern wird leer: ein Treffer ohne Symbol ist besser als kein Treffer.
- **`FAILURE_OFFSET_CEILING` mit Treffern bleibt `complete()`.** Der Dialog hat keinen Platz fuer einen Satz, und `complete()` heisst genau "von hier gibt es keine naechste Seite". Die Seite bildet denselben Zustand spaeter auf ihre Hinweiszeile ab.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] `final class SearchService` und ein Mock in ProviderTest schliessen sich aus**

- **Found during:** Task 2
- **Issue:** Das Abnahmekriterium von Task 1 verlangt vier finale Klassen, die Aufgabenbeschreibung von Task 2 verlangt "SearchService wird dort gemockt". PHPUnit 11 kann kein Test-Double einer finalen Klasse erzeugen, und `dg/bypass-finals` ist keine Abhaengigkeit dieses Projekts.
- **Fix:** Das im Repo bereits vorhandene Muster uebernommen: das Schluesselwort faellt weg, eine `@final`-Annotation mit Begruendung tritt an seine Stelle, wortgleich zur Loesung an `ExAppService`.
- **Files modified:** `php/lib/Service/SearchService.php`
- **Verification:** `php -l` gruen; `ProviderTest` mockt den Dienst; die drei Wertobjekte sind unveraendert `final`.
- **Committed in:** `d814157`

**2. [Rule 3 - Blockierend] `ExAppService::REQUEST_TIMEOUT_SECONDS` war privat**

- **Found during:** Task 2
- **Issue:** Der Provider soll diese Konstante als Per-Call-Deckel in `SearchCaps` setzen, konnte sie aber nicht lesen.
- **Fix:** Sichtbarkeit auf `public`, mit einem Absatz im Docblock, der sagt warum und dass sie Standardwert jeder Methode bleibt. Kein Wert und kein Verhalten geaendert.
- **Files modified:** `php/lib/Service/ExAppService.php`
- **Verification:** `php -l` gruen; der Provider setzt 1.5 aus der Konstante, die lokale Verhaltensprobe bestaetigt, dass 1.5 an beiden Aufrufen ankommt.
- **Committed in:** `d814157`

**3. [Rule 1 - Falsche Annahme im Plan] Der Baum hat drei Aufloesungen, nicht eine**

- **Found during:** Task 3
- **Issue:** Der Plan erwartet vom ACL-Gate "genau eine Datei nennt sie, naemlich SearchService.php, und dort je genau einmal" fuer beide Namen. Der Bestand widerlegt das fuer `getFirstNodeById`: `GatewayController::getFileContents` (Bytes fuer den Container, geschuetzt durch `rejectForeignCaller`) und `QueueService` (Groesse eines Node fuer den Crawl, laut eigenem Kommentar ausdruecklich keine Sicherheitskontrolle) rufen es ebenfalls. Ein Gate mit der geforderten Erwartung waere am Tag seiner Entstehung rot gewesen.
- **Fix:** Der Gate haelt die Lesbarkeitsfrage (`isReadable`) auf genau eine Stelle, weil das die Suchgrenze ist und eine zweite Recheck-Schleife sie zwingend braucht, und fuehrt fuer die Aufloesung ein benanntes Register mit drei Eintraegen und Zahl je Datei. Eine unregistrierte Datei und eine abweichende Zahl sind beide Befunde. Der Modul-Docstring begruendet die Unterscheidung.
- **Files modified:** `backend/tests/test_php_acl_boundary.py`
- **Verification:** `uv run pytest -q tests/test_php_acl_boundary.py` gruen, 8 Faelle; der Selbsttest mit einem zweiten Aufrufer in einer zweiten Datei meldet beide Namen.
- **Committed in:** `e230515`

**4. [Rule 2 - Threat-Register] Der Mimetype wurde nicht geklemmt**

- **Found during:** Task 1
- **Issue:** T-09-03 sagt, alle drei Felder eines Treffers laufen durch `PlainText::bounded`. Der Plan nennt fuer den Mimetype nur "wird zusaetzlich gelesen".
- **Fix:** Eigene Konstante `MAX_MIME_LENGTH = 255` und `bounded(...) ?? ''`, mit Kommentar, warum ein nicht saeuberbarer Mimetype anders als Titel und Pfad keinen Treffer verwirft.
- **Files modified:** `php/lib/Service/SearchService.php`
- **Verification:** Verhaltensprobe "hit carries the node mime" gruen.
- **Committed in:** `f185d39`

**5. [Rule 1 - Dokumentationsdrift] Vier Prosastellen nannten noch den Provider als Ort des Rechecks**

- **Found during:** Task 2
- **Issue:** `GroupEventListener`, `ShareEventListener`, `QueueService` (zweimal) und der `@final`-Docblock von `ExAppService` beschreiben den Recheck als "in Provider". Nach dem Umzug ist das falsch, und diese Saetze sind genau die, die eine spaetere Lesende sucht.
- **Fix:** Vier Ersetzungen "Provider" durch "SearchService" beziehungsweise `Provider::search` durch `SearchService::run`. Kein Code beruehrt. Dazu die Zeilen 4, 5, 10 und 11 der Verhaltenstabelle in `docs/testing.md`.
- **Files modified:** `php/lib/Listener/GroupEventListener.php`, `php/lib/Listener/ShareEventListener.php`, `php/lib/Service/QueueService.php`, `php/lib/Service/ExAppService.php`, `docs/testing.md`
- **Verification:** `php -l` gruen fuer die geaenderten Dateien; `grep "recheck in Provider"` findet nichts mehr.
- **Committed in:** `d814157`

**6. [Rule 2 - Registerpflege] Die beiden neuen Gates fehlten in der Gate-Tabelle**

- **Found during:** Task 3
- **Issue:** `docs/testing.md` fuehrt jeden textuellen Gate mit dem Satz, was er verhindert. Zwei neue Gates ohne Eintrag waeren ein Register, das nicht mehr vollstaendig ist.
- **Fix:** Zwei Zeilen ergaenzt, je mit dem Satz, was der Gate nicht traegt.
- **Files modified:** `docs/testing.md`
- **Verification:** Tabelle gelesen, Reihenfolge und Spaltenzahl stimmen.
- **Committed in:** `e230515`

---

**Total deviations:** 6 auto-fixed (2 nach Rule 3, 2 nach Rule 1, 2 nach Rule 2)
**Impact on plan:** Kein Umfangszuwachs. Zwei Abweichungen sind Werkzeugzwaenge (Mockbarkeit, Sichtbarkeit), eine korrigiert eine Annahme des Plans ueber den Bestand, drei sind Konsistenzpflege.

## Verification

| Pruefung | Ergebnis |
|---|---|
| `php -l` fuer alle sieben beruehrten PHP-Dateien (im Container, ueber `docker cp`) | `No syntax errors` |
| Lokale Verhaltensprobe des Dienstes (Stand-in-Welt, 14 Zusicherungen) | 14 von 14 gruen |
| `uv run pytest -q` (ganzes Backend) | 1778 passed, 15 skipped |
| `uv run pytest -q tests/test_php_acl_boundary.py tests/test_search_limits_lockstep.py` | 17 passed |
| Herbeigefuehrter Verstoss `MAX_CONTAINER_OFFSET = 1300` | `test_the_two_ceilings_stand_in_both_halves_with_the_same_number` rot, danach verworfen |
| `uv run ruff check .` / `ruff format --check .` / `pyright` / `vulture` | alle gruen (0 Fehler, 119 Dateien formatiert) |
| Gedankenstriche in neuen und geaenderten Dateien | keine |

**Nicht lokal pruefbar:** der PHPUnit-Job und der Job `search-parity`. Auf dieser Maschine gibt es kein PHP ausserhalb des Containers und keinen `nextcloud/server`-Checkout, den `php/tests/bootstrap.php` verlangt; die Suite ist laut `docs/testing.md` bewusst CI-only. Ersatzweise steht die Verhaltensprobe oben, die dieselben Aussagen gegen eine Stand-in-Welt fuehrt: Titel, Pfad und Mimetype aus dem Node, der unlesbare Node ohne Treffer, die Decke ohne Rundtrip, die Decke selbst noch gefragt, die stumme Antwort mit und ohne vorherige Treffer, die Rundenzahl und der Canary. Der Paritaetsjob ist der eigentliche Beweis fuer "der Dialog verhaelt sich unveraendert" und laeuft in CI.

## Issues Encountered

- **PHPUnit-Mockbarkeit und `final` sind ein Zielkonflikt**, den dieses Repo schon einmal hatte. Wer spaeter `SearchService` doch finalisieren will, braucht `dg/bypass-finals` oder ein Interface; beides waere eine eigene Entscheidung.
- **Die Erwartung "genau eine Aufloesung im Baum" stimmte nie.** Sie stammt aus der Research und meint die Suchgrenze; der Baum hat drei Aufloesungen mit drei verschiedenen Aufgaben. Der Gate benennt sie jetzt alle drei, was mehr wert ist als die urspruengliche Formulierung: eine neue Datei mit einer Aufloesung ist ab sofort ein roter Test, egal welchen Namen sie traegt.
- **Die lokale Verhaltensprobe liegt in `.dev/probe-0903/`** und ist gitignoriert. Sie ist kein Ersatz fuer PHPUnit und will keiner sein: sie stellt eine Stand-in-Welt und laesst den echten Dienst darin laufen.

## Next Phase Readiness

- Plan 09-04 baut `PageController` gegen genau diese Signaturen: `SearchService::run(IUser, string, bool, int, SearchCaps): SearchOutcome`, mit `PAGE_BUDGET_SECONDS = 3.0` und `ExAppService::PAGE_REQUEST_TIMEOUT_SECONDS` in den Caps und Seitengroesse 25.
- Der Controller darf `getFirstNodeById` und `isReadable` nicht aufrufen. Beides ist ab sofort ein roter Test statt einer Bitte.
- `SearchOutcome::FAILURE_OFFSET_CEILING` bildet die Seite auf ihre vorhandene Hinweiszeile ab, nicht auf den Fehlerblock. `FAILURE_BACKEND_SILENT` und `FAILURE_VERSION_DRIFT` sind die beiden Fehlerbloecke, `FAILURE_NO_HOME_FOLDER` ist der leere Zustand.
- `ApprovedHit::mimeType` steht fuer das Dateityp-Symbol bereit und ist beim Canary leer; wer ihn rendert, verlinkt auf die Dateiliste.
- Die Anti-Vakuitaets-Schranke von Gate B (`test_php_trust_boundary.py`) ist unveraendert und wartet weiter auf `php/lib/Controller/PageController.php`.

## Self-Check: PASSED

- Alle sieben neuen Dateien liegen auf der Platte, alle sieben geaenderten ebenfalls (`test -f`).
- Die drei Task-Commits stehen im Log: `f185d39`, `d814157`, `e230515`.
- `git diff --diff-filter=D f8a9e85 HEAD` ist leer: keine Datei wurde geloescht.
- Keine Aenderung an `.planning/STATE.md` oder `.planning/ROADMAP.md`.
- Kein Gedankenstrich der langen oder mittleren Form in Quellcode, Gates und dieser Zusammenfassung.

---
*Phase: 09-eigene-ergebnisseite*
*Completed: 2026-09-09*
