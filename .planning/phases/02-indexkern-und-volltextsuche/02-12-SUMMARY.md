---
phase: 02-indexkern-und-volltextsuche
plan: 12
subsystem: php-companion
tags: [zweistufig, recheck, comp-04, ifilteringprovider, zeitbudget, snippets, offsets]

# Dependency graph
requires:
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-09: Kandidaten ohne Namen und Text, Snippets mit Zeichenoffsets"
  - phase: 01-integrationsbeweis
    provides: "01-05: ExAppService mit den vier stillen Fehlerpfaden, Provider, Kanarien-Sonderweg"
provides:
  - "ExAppService::searchCandidates und ExAppService::snippets, je 1,5 s, ein einziger exAppRequest"
  - "Provider als IFilteringProvider mit begrenztem Nachfassen, gedeckelter Knotenaufloesung und 2,5-s-Wanduhr"
  - "OCA\\Findling\\Text\\PlainText: die gemeinsame Textbegrenzung beider Haelften"
  - "integration.yml: Gegenprobe gegen den Kanarienvogel und Probe auf die gemeldete Filterliste"
  - "Gemessener Befund: IFileAccess::getByFileIds existiert seit 29.0.0, die Sammelabfrage ist also verfuegbar"
affects: [02-11, 02-13, 02-14, phase-04-statusseite]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Was vor dem Recheck ankommt, wird auf die Kennung reduziert: der Container kann kein Feld anbieten, das angezeigt wird"
    - "Gedeckelt wird die Zahl der Pruefungen, nie die Pflicht zu pruefen"
    - "Guenstige Vorreduktion vor teurer Aufloesung: zwei Abfragen je Seite statt einer je Kandidat"
    - "Zeitbudget als Wanduhr mit hrtime, nicht mit microtime: eine Uhrkorrektur darf ein Budget nicht verdoppeln"
    - "Hervorhebungen werden verworfen statt verschoben, wenn die Textbereinigung den Text geaendert hat"

key-files:
  created:
    - php/lib/Text/PlainText.php
  modified:
    - php/lib/Service/ExAppService.php
    - php/lib/Search/Provider.php
    - .github/workflows/integration.yml
    - docs/testing.md

key-decisions:
  - "Der Recheck wandert aus dem ExAppService in den Provider: nur dort ist bekannt, wie viele Treffer angezeigt werden, und genau das ist die Groesse, ueber die gedeckelt wird"
  - "Ein Kandidat mit fileId > 0 wird auf die Kennung reduziert statt nur um title und snippet bereinigt: was der Provider nicht bekommt, kann er nicht versehentlich anzeigen"
  - "IFileAccess::getByFileIds im Quellcode der Zielversion nachgeschlagen und benutzt: die Vorreduktion kostet eine Abfrage je Seite statt einer je Kandidat"
  - "Die Textbegrenzung wird zu OCA\\Findling\\Text\\PlainText: zwei Aufrufer brauchen exakt dieselbe Reinigung und duerfen nicht auseinanderlaufen"
  - "Hervorhebungen ueberleben nur einen unveraenderten Text; jede Reinigung oder Kuerzung verwirft sie ganz, statt Offsets zu raten"
  - "Der Cursor der Anfrage wird als Startoffset gelesen: ohne ihn liefert Weiterblaettern immer wieder dieselbe Seite"
  - "SearchResult::complete statt paginated, wenn der Container hasMore false gemeldet hat: ein Weiterblaettern ins Leere ist eine Zusage, die nicht eingehalten wird"

patterns-established:
  - "Fremde Schnittstellen vor der Benutzung am Quellcode der Zielversion pruefen, nicht aus dem Gedaechtnis"
  - "Ein Kommentar, der eine Zahl nennt, wird mitgeaendert, wenn die Zahl sich aendert"

requirements-completed: [COMP-04, SRCH-02, SRCH-03]

# Metrics
duration: 22 min
completed: 2026-08-31
---

# Phase 02 Plan 12: Der zweistufige Suchpfad in PHP Summary

**Zwei gekapselte Proxy-Aufrufe zu je 1,5 Sekunden, ein Provider, der hoechstens dreimal nachfasst, hoechstens `min(64, limit * 2)` Knoten aufloest und innerhalb von 2,5 Sekunden entscheidet, und ein Textausschnitt, den es erst gibt, nachdem der Nutzerordner den Treffer bestaetigt hat.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-08-31T20:49Z
- **Completed:** 2026-08-31T21:11Z
- **Tasks:** 3 von 3
- **Files created:** 1, **modified:** 4

## Accomplishments

- `ExAppService` traegt das neue Protokoll: `searchCandidates()` liefert Kandidaten, `hasMore`, `nextOffset` und `degraded`, `snippets()` liefert die Textausschnitte. Beide teilen sich eine private Hilfsmethode, in der die vier stillen Fehlerpfade der Phase 1 genau einmal stehen, und damit bleibt die Zahl der `exAppRequest`-Vorkommen im ganzen Projekt bei **eins**.
- Die Zeitgrenze steht als benannte Konstante bei 1,5 Sekunden, mit der Rechnung im Kommentar: AppAPI-Vorgabe 3 s, kein Deckel in AppAPI, zwei Aufrufe zu 1,5 s bleiben unter der 2,5-s-Wanduhr des Providers.
- Ein Kandidat mit `fileId > 0` wird auf die Kennung reduziert. Ein Backend, das freiwillig `title` oder `snippet` mitschickt, bekommt diese Felder nicht weitergereicht; der Kanarienvogel mit `fileId <= 0` ist die einzige Ausnahme und nur unter seinem exakten Titel.
- Der Provider implementiert `IFilteringProvider` und meldet `term` und `title-only`. Die Filterliste ist die Falle aus Pitfall 15: ein nicht genannter Filter laesst den Anbieter kommentarlos verschwinden.
- Die Knotenaufloesung ist dreifach gebremst: guenstige Vorreduktion ueber die Mountliste des Nutzers und eine Sammelabfrage je Seite, Abbruch bei voller Anzeigemenge, und eine harte Obergrenze als benannte Konstante.
- Die Snippets werden erst nach dem Recheck, nur fuer die ueberlebenden Kennungen und nur mit Restbudget angefordert. Ohne Budget erscheinen die Treffer mit dem Pfad als Subline.
- Der Durchstich der Phase 1 bleibt woertlich stehen und bekommt zwei Gegenproben: ein gewoehnlicher Suchbegriff sieht den Kanarienvogel nicht, und die gemeldete Filterliste nennt `title-only`.

## Task Commits

1. **Task 1: Zwei gekapselte Aufrufe mit je 1,5 Sekunden Zeitgrenze** , `4e399d4` (feat)
2. **Task 2: Provider mit begrenztem Nachfassen, gedeckelter Knotenaufloesung und Filterliste** , `2d6f076` (feat)
3. **Task 3: Der Durchstich der Phase 1 bleibt gruen, und der Kanarienvogel bleibt allein** , `9437c36` (test)

Dazu `be695e2` (docs): `docs/testing.md` nennt die Methoden, die es nach dem Umbau noch gibt, siehe Deviation 2.

## Die Zahlen, die der Plan im SUMMARY verlangt

| Groesse | Wert | Herkunft |
|---|---|---|
| Knotenaufloesungen je Suche, schlechtester Fall | **40** bei `limit` 20, absolut hoechstens **64** | `min(MAX_RECHECKS_ABSOLUTE, limit * MAX_RECHECKS_PER_HIT)`, im Code als Konstante |
| Knotenaufloesungen ohne Deckelung | bis zu **240** | `limit` 20 mal Ueberfetch 4 mal 3 Runden, die Rechnung des Plans |
| Zusaetzliche Abfragen gegen den Dateicache | **1 + hoechstens 3** | einmal die Mountliste je Suche, einmal die Sammelabfrage je Runde |
| Proxy-Aufrufe je Suche | hoechstens **4** | bis zu 3 mal `/search`, danach hoechstens einmal `/snippets` |
| Zeitdeckel | 1,5 s je Aufruf, 2,5 s Wanduhr | benannte Konstanten in beiden Dateien |

**Nicht gemessen, und zwar ausdruecklich:** die Gesamtdauer einer Suche im CI-Lauf. Dieser Executor laeuft in einem Worktree ohne Push, es gibt also keinen Lauf zu diesem Code (Deviation 1). Damit die Zahl nach dem Push nicht wieder fehlt, gibt die neue Gegenprobe in `integration.yml` die gemessene Dauer der Suche in Millisekunden aus (`the search for an ordinary term answered after ...ms`). Der Wert steht dann im Joblog, ohne dass jemand den Job dafuer aendern muss.

## Files Created/Modified

- `php/lib/Text/PlainText.php` , `bounded()`: Steuerzeichen raus, Tabulator bleibt, Kuerzung auf Zeichengrenzen, ungueltiges UTF-8 wird zu null. Die Begruendung der Phase 1 steht unveraendert am Kopf der Klasse.
- `php/lib/Service/ExAppService.php` , `searchCandidates`, `snippets`, `call` (der einzige ausgehende Aufruf), `filterCandidates`, `filterSnippets`, `filterHighlights`. `IRootFolder` ist keine Abhaengigkeit mehr, weil hier keine Rechteentscheidung mehr faellt.
- `php/lib/Search/Provider.php` , `search` mit Wanduhr, Rundenbegrenzung, Vorreduktion, Recheck, Snippets und Seitenmarke; `getSupportedFilters`, `getAlternateIds`, `getCustomFilters`; `reduce`, `storageIdsOfUser`, `titleOnly`, `startOffset`, `toEntries`, `resourceUrl`.
- `.github/workflows/integration.yml` , zwei neue Schritte im Job `walking-skeleton`, dazu zwei richtiggestellte Kommentare zur Zeitgrenze. Der Job `readonly-gate` ist unberuehrt.
- `docs/testing.md` , die Liste der ungetesteten Verhaltensweisen nennt jetzt existierende Methoden und ist um drei Punkte gewachsen.

## Decisions Made

- **Der Recheck wandert in den Provider.** In der Phase-1-Fassung stand er im `ExAppService` und lief ueber jeden gelieferten Treffer. Die Deckelung braucht aber die Anzeigemenge als Bezugsgroesse, und die kennt nur der Provider. Der `ExAppService` faellt damit keine Rechteentscheidung mehr, und der Klassenkommentar sagt das ausdruecklich, damit die Grenze nicht spaeter wieder als "irgendwo im Proxy" gesucht wird.
- **Ein Kandidat behaelt nur seine Kennung.** Der Plan verlangt, `title` und `snippet` bei `fileId > 0` zu entfernen. Umgesetzt ist die strengere Form: es wird nur `fileId` uebernommen. Das ist eine Obermenge der Forderung und macht die Zusage strukturell statt aufzaehlend, denn ein spaeter hinzukommendes Feld waere sonst wieder ein Feld, an das jemand denken muss.
- **`IFileAccess::getByFileIds` wird benutzt.** Der Plan verlangt, im Quellcode der Zielversion nachzusehen, ob es eine Sammelabfrage gibt. Es gibt sie, seit 29.0.0, also weit unter unserem `min-version` 32 (siehe "Verifizierte Schnittstellen" unten). Die Vorreduktion verwirft damit Kandidaten, deren Speicher der Nutzer gar nicht eingehaengt hat, bevor auch nur ein Knoten aufgeloest wird.
- **Die Vorreduktion ist ausdruecklich keine Grenze.** Sie ist in beide Richtungen ungenau: ein Speicher kann Dateien eines Mounts tragen, den dieser Nutzer nicht hat, und die erweiterten Berechtigungen eines Team Folders loest sie gar nicht auf. Beides steht als Kommentar an der Methode, und beides ist unschaedlich, weil der Recheck jeden Kandidaten entscheidet, den sie durchlaesst. Faellt die Mountliste oder die Sammelabfrage aus, wird die Seite ungefiltert weitergereicht: die Deckelung und der Recheck bleiben in Kraft.
- **Hervorhebungen werden verworfen, nicht verschoben.** Die Bereiche zaehlen Zeichen des Textes, den der Container geschickt hat. Hat die Reinigung ein Zeichen entfernt oder die Obergrenze gekuerzt, zeigt jeder Offset dahinter woanders hin. Ein "Nachrechnen" waere geraten; die Bereiche fallen dann ganz weg, der Text bleibt.
- **Der Cursor wird gelesen.** Der Plan nennt nur die Rueckgabe ueber `SearchResult::paginated`. Ohne den Cursor der Anfrage als Startoffset liefert "mehr laden" dieselbe Seite noch einmal, und die Seitenmarke waere Dekoration. Nicht numerische Cursor beginnen wieder oben.
- **`complete` statt `paginated`, wenn nichts mehr kommt.** Hat der Container `hasMore` false gemeldet, gibt es keine naechste Seite, und ein angebotenes Weiterblaettern waere ein Versprechen ins Leere.

## Verifizierte Schnittstellen

Vor der Benutzung am Quellcode der Zielversion nachgeschlagen (`nextcloud/server`, Zweig `stable32`), statt aus dem Gedaechtnis geschrieben. `php -l` findet einen falschen Klassennamen oder eine erfundene Konstante nicht, ein Fehler hier waere erst zur Laufzeit sichtbar geworden.

| Symbol | Befund |
|---|---|
| `IFileAccess::getByFileIds(array): array<int,ICacheEntry>` | vorhanden, `@since 29.0.0` |
| `ICacheEntry::getStorageId()` | vorhanden, `@since 9.0.0` |
| `IUserMountCache::getMountsForUser(IUser): ICachedMountInfo[]` | vorhanden, `ICachedMountInfo::getStorageId(): int` |
| `IFilter::BUILTIN_TERM`, `IFilter::BUILTIN_TITLE_ONLY` | auf `IFilter`, nicht auf `FilterDefinition`; Werte `term` und `title-only` |
| `BooleanFilter::get(): bool` | echter bool, deshalb `=== true` statt einer Umwandlung |
| `ISearchQuery::getFilter(string): ?IFilter`, `getCursor()` | vorhanden, `@since 28.0.0` bzw. `20.0.0` |
| `SearchResultEntry::__construct` | **ohne** `attributes`-Parameter; Attribute nur ueber `addAttribute(string,string)`, deshalb die Hervorhebungen als JSON-Zeichenkette |
| `SearchComposer::getProviders` | meldet `filters` als Abbildung Name auf Typ, deshalb pruefen die CI-Zeilen `has("term")` und `has("title-only")` |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die CI-Kriterien sind im Worktree nicht auswertbar, Ersatzpruefung lokal**

- **Found during:** alle drei Tasks
- **Issue:** Jedes Task hat als letztes Abnahmekriterium einen `gh run list`-Aufruf mit dem Wert `success`. Dieser Executor arbeitet in einem Worktree und pusht nicht; ohne Push gibt es keinen Lauf zu diesem Code. `gh run list --workflow=php.yml --limit 1` liefert zwar `success`, aber fuer `530679876de23c5e925cd17f9be9ba0288fd2d81`, also fremden Code von vor diesem Plan. Laut Projektregel wird so etwas dokumentiert, nicht simuliert.
- **Fix:** Der Lint-Job wurde lokal identisch nachgestellt: `docker run --rm php:8.2-cli` mit exakt dem Kommando des Workflows (`find php/lib php/appinfo -name '*.php' -print0 | xargs -0 -n1 php -l`) und exakt der CI-Version PHP 8.2. Ergebnis nach jedem Task: 17 Dateien, kein Syntaxfehler. Zusaetzlich wurde `integration.yml` mit einem YAML-Parser gelesen (beide Jobs vorhanden, 16 bzw. 18 Schritte), damit ein Einrueckungsfehler nicht erst im teuersten Workflow des Projekts auffaellt. Der Job `app-metadata` ist nicht betroffen, weil keine `info.xml` angefasst wurde.
- **Files modified:** keine
- **Verification:** **Offen bis zum Orchestrator-Push.** Danach `gh run list --workflow=php.yml --limit 1 --json conclusion -q '.[0].conclusion'` und dasselbe fuer `integration.yml` auf `success` pruefen.
- **Committed in:** keiner (Pruefschritt)

**2. [Rule 1 - Bug] `docs/testing.md` nannte drei Methoden, die es nicht mehr gibt**

- **Found during:** Abschliessende Verifikation
- **Issue:** Das Dokument fuehrt die ungetesteten Verhaltensweisen der PHP-Haelfte namentlich auf und nannte `ExAppService::filterHits`, `ExAppService::plainText` und `ExAppService::search`. Alle drei sind mit diesem Plan verschwunden, und es beschrieb den Recheck als etwas, das im Proxy stattfindet. Ein falscher Name an genau der Stelle, an der jemand die Spezifikation fuer die fehlende Testsuite sucht, ist teurer als kein Name; dieselbe Klasse wie Deviation 2 aus 02-03.
- **Fix:** Die Liste nennt die Methoden, die es gibt, und ist um drei Punkte gewachsen, die es vorher nicht geben konnte: Runden- und Recheck-Deckel, Snippets erst nach dem Recheck, Snippets nur fuer angefragte Kennungen. Die Liste der abgedeckten Integrationsschritte nennt die beiden neuen Proben, und die Aufzaehlung der zu mockenden Dienste nennt die zwei neuen.
- **Files modified:** `docs/testing.md`
- **Verification:** Jede genannte Methode existiert im Quelltext.
- **Committed in:** `be695e2`

**3. [Rule 1 - Bug] Zwei Kommentare in `integration.yml` nannten die alte Zeitgrenze**

- **Found during:** Task 3
- **Issue:** Der Schritt zum haengenden Backend begruendete seine Sechs-Sekunden-Schranke mit "Two seconds is the configured timeout". Nach diesem Plan sind es 1,5 Sekunden je Aufruf. Die Zusicherung selbst bleibt richtig und unveraendert, die Begruendung daneben war ab dem ersten Task falsch.
- **Fix:** Beide Stellen nennen jetzt 1,5 Sekunden je Aufruf und sagen dazu, dass der zweite Aufruf gar nicht stattfindet, wenn der erste scheitert. Die drei Assertions der Phase 1 und die Schranke `-lt 6` sind woertlich unveraendert.
- **Files modified:** `.github/workflows/integration.yml`
- **Verification:** `grep -c 'produced inside container'` = 1, `grep -c 'findling-canary'` = 4, `git diff` beruehrt keine Zeile des Jobs `readonly-gate`.
- **Committed in:** `9437c36`

**4. [Rule 2 - Missing critical functionality] Eine gemeinsame Textbegrenzung statt zweier Kopien**

- **Found during:** Task 1
- **Issue:** Nach der Verlagerung des Rechecks braucht der Provider dieselbe Reinigung fuer den Namen und den Pfad des Knotens, die der Proxy fuer Snippets und den Kanarien-Text braucht. Ein Dateiname aus einem externen Speicher ist nicht vertrauenswuerdiger als eine Containerantwort, und zwei Kopien derselben sicherheitsrelevanten Regel laufen frueher oder spaeter auseinander.
- **Fix:** `php/lib/Text/PlainText.php` mit `bounded()`, benutzt von beiden Seiten. Der Plan nennt die Datei nicht, aber die Alternative waere gewesen, entweder die Reinigung im Provider wegzulassen (eine Luecke) oder sie zu kopieren (eine kuenftige Luecke).
- **Files modified:** `php/lib/Text/PlainText.php` (neu)
- **Verification:** `php -l` sauber, beide Aufrufer benutzen dieselbe Methode.
- **Committed in:** `4e399d4`

---

**Total deviations:** 4 auto-fixed (2 Bugs, 1 fehlende Notwendigkeit, 1 blockierendes CI-Kriterium)
**Impact on plan:** Kein Scope-Zuwachs. Deviation 1 ist die bekannte Grenze des Worktree-Executors, 2 und 3 sind Kommentare und Doku, die dieser Plan selbst falsch gemacht haette, 4 ist eine Datei, die eine Sicherheitszusage an einer Stelle haelt statt an zweien.

## Acceptance Criteria

### Task 1

| Kriterium | Soll | Ist |
|---|---|---|
| `grep -c 'exAppRequest' ExAppService.php` | 1 | 1 |
| `grep -rl 'exAppRequest' php/lib` | nur ExAppService.php | nur ExAppService.php |
| `grep -c "'/snippets'" ExAppService.php` | 1 | 1 |
| `grep -c 'exAppRequestWithUserInit'` | 0 | 0 |
| `grep -Ec '1\.5\|1500'` | >= 1 | 2 |
| `grep -Ec 'TIMEOUT_SECONDS = 2\b'` | 0 | 0 |
| Logaufruf mit `$term` | keiner | keiner |
| `php.yml` gruen | success | siehe Deviation 1, lokal `php -l` sauber |

### Task 2

| Kriterium | Soll | Ist |
|---|---|---|
| `grep -c 'getFirstNodeById' Provider.php` | 1 | 1 |
| Reihenfolge `getFirstNodeById` vor `snippets(` | ja | Zeile 243 vor Zeile 288 |
| `grep -Ec 'MAX_RECHECKS\|RECHECK_LIMIT'` | >= 2 | 3 |
| `grep -Ec 'round < 3\|MAX_ROUNDS'` | >= 1 | 2 |
| `grep -c 'hrtime'` | >= 1 | 4 |
| `grep -c 'IFilteringProvider'` | >= 2 | 3 |
| `grep -c 'getSupportedFilters'` | 1 | 1 |
| `grep -c 'paginated'` | >= 1 | 1 |
| `grep -Ec 'return null'` | 0 | 0 |
| `php.yml` gruen | success | siehe Deviation 1, lokal `php -l` sauber |

### Task 3

| Kriterium | Soll | Ist |
|---|---|---|
| `grep -c 'produced inside container'` | >= 1 | 1 |
| `grep -c 'findling-canary'` | >= 2 | 4 |
| `grep -c 'entries \| length == 0'` | >= 2 | 3 |
| `grep -c 'title-only'` | >= 1 | 3 |
| `readonly-gate` unveraendert | ja | beide Diff-Bloecke enden vor dem Job |
| `integration.yml` gruen | success | siehe Deviation 1, YAML geparst, beide Jobs vorhanden |

## Threat Flags

Keine neue Angriffsflaeche. Die sechs `mitigate`-Dispositionen des Plans sind umgesetzt, die eine `accept`-Disposition ist unveraendert:

| Threat ID | Umsetzung |
|---|---|
| T-02-121 (Treffer aus einer Datei ohne Zugriff) | `getUserFolder($uid)->getFirstNodeById()` je angezeigtem Treffer; alles, was kein `File` ist, faellt raus. Der Kommentar ueber der Schleife nennt beide Aussagen: einzige Rechteentscheidung, und gedeckelt wird die Zahl der Pruefungen |
| T-02-122 (Snippet aus einer entzogenen Freigabe) | `snippets()` wird nach der Schleife aufgerufen und bekommt ausschliesslich die Kennungen der bestaetigten Treffer; `filterSnippets` verwirft zusaetzlich jede Antwort zu einer nicht angefragten Kennung |
| T-02-123 (Titel oder Pfad aus der Containerantwort) | `filterCandidates` gibt bei `fileId > 0` nur die Kennung weiter; Titel und Verweis entstehen aus dem bestaetigten Knoten |
| T-02-124 (Haengender Anbieter) | 1,5 s je Aufruf, 2,5-s-Wanduhr, vier stille Fehlerpfade in einer Methode, jeder endet in einem leeren Ergebnis; der CI-Schritt mit dem langsamen Stub bleibt |
| T-02-125 (N+1 auf oc_filecache) | Vorreduktion ueber Mountliste und Sammelabfrage, Recheck nur bis die Anzeigemenge voll ist, harte Obergrenze `min(64, limit * 2)`; der schlechteste Fall steht oben in der Tabelle |
| T-02-126 (Kanarien-Sonderweg) | unveraendert `accept`: nur `fileId <= 0`, nur unter dem exakten Titel, Inhalt entsteht im Container. Neu ist die Gegenprobe in der CI, die belegt, dass er bei anderen Begriffen nicht erscheint |
| T-02-127 (Anbieter wegen unbekanntem Filter uebergangen) | `term` und `title-only` gemeldet, die CI prueft beide in der gemeldeten Filterliste |

## Known Stubs

Keine. Die drei Dateien sind vollstaendig. Was noch fehlt, fehlt planmaessig auf der anderen Seite: die beiden Endpunkte `/search` und `/snippets` im neuen Zuschnitt entstehen in Plan 02-11, der in derselben Welle laeuft. Bis dahin antwortet der Container in der alten Form, was hier zu einer leeren Trefferliste fuehrt und nicht zu einem Fehler , genau der Zweck der vier stillen Fehlerpfade.

## Issues Encountered

- **Zwei Haelften eines Protokolls in zwei Worktrees.** Diese Seite ist gegen den im Plan eingefrorenen Wortlaut gebaut, nicht gegen laufenden Code. Der erste gemeinsame Lauf ist der `integration.yml`-Lauf nach dem Zusammenfuehren beider Zweige; wenn dort etwas klemmt, ist die Feldbenennung der wahrscheinlichste Ort.
- **`SearchResultEntry` nimmt keine Attribute im Konstruktor.** Das war die einzige Annahme, die sich beim Nachschlagen als falsch herausstellte, und sie haette `php -l` unbemerkt passiert. Die Hervorhebungen reisen jetzt ueber `addAttribute('highlights', ...)` als JSON-Zeichenkette, weil Attribute Zeichenketten sind.
- **Der Provider hat jetzt sieben Konstruktorabhaengigkeiten.** Alle werden gebraucht und alle sind autowirebar, aber die Klasse ist damit an der Grenze dessen, was noch eine Aufgabe ist. Wenn Phase 4 eine achte braucht, ist das Zeichen, den Suchablauf aus dem Provider herauszuziehen.
- **`docs/testing.md` waechst weiter.** Die PHP-Haelfte hat weiterhin keine Unit-Tests, und dieser Plan hat drei weitere Verhaltensweisen hinzugefuegt, die nur eine PHPUnit-Suite pruefen kann. Die Liste steht dort bei zwoelf Punkten.

## User Setup Required

Keine.

## Next Phase Readiness

- **Fuer 02-11 (Endpunkte im Container):** Diese Seite schickt an `/search` genau `{"query","limit","offset","titleOnly"}` und erwartet `{"candidates":[{"fileId",...}],"hasMore","nextOffset","degraded"}`. An `/snippets` gehen `{"query","fileIds","titleOnly"}`, erwartet wird `{"snippets":{"4711":{"text","highlights"}}}` mit Zeichenoffsets. Der Kanarien-Kandidat traegt `fileId` 0 sowie `title` und `snippet` und nur er.
- **Fuer 02-13:** Der Ueberfetch ist hier vier, die Rundenzahl drei; beides sind benannte Konstanten in `Provider.php`. Die Werte `search_overfetch` und `search_rounds` aus der Konfiguration des Containers werden von dieser Seite nicht gelesen; wer sie zusammenfuehren will, entscheidet, welche Seite die Wahrheit ist.
- **Fuer Phase 4 (Statusseite):** `degraded` kommt an und wird bislang nur als Debug-Zeile protokolliert. Das ist das Signal, aus dem die Statusseite "der Index ist noch nicht vollstaendig" bauen kann, ohne einen neuen Endpunkt zu brauchen.
- **Offene Messung:** Die Gesamtdauer einer Suche im CI-Lauf. Die Ausgabezeile dafuer steht im Job, der Wert entsteht beim ersten Lauf nach dem Push.

## Self-Check: PASSED

- Alle vier angefassten Dateien und die eine neue liegen im Worktree: `php/lib/Text/PlainText.php`, `php/lib/Service/ExAppService.php`, `php/lib/Search/Provider.php`, `.github/workflows/integration.yml`, `docs/testing.md`.
- Alle vier Commits im Log von `gsd/agent-02-12`: `4e399d4`, `2d6f076`, `9437c36`, `be695e2`.
- Keine ungewollte Loeschung: `git diff --diff-filter=D HEAD~1 HEAD` nach jedem Commit leer.
- Arbeitsverzeichnis sauber, keine unbeobachteten Dateien.
- Keine Aenderung an STATE.md, ROADMAP.md oder REQUIREMENTS.md.

---
*Phase: 02-indexkern-und-volltextsuche*
*Completed: 2026-08-31*
