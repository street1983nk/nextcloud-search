---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 05
subsystem: php/companion (Admin-Übersicht)
tags: [coverage, issue-25, d-43-07, d-43-09, d-43-11, d-43-14, b1, php]
requires:
  - 43-04 (POST /coverage, Antwortform, Grenzen)
  - 43-03 (coverage_topology.json mit expected.php)
provides:
  - "FileStateService::countByReasonPerStorage(state, reason, storageIds): array<int,int>, STORAGE_BAND = 1000"
  - "FileStateService::distinctPathsByReasons(groups, singles): {byGroup, byStorage, notReadableByGroup, notReadableByStorage}"
  - "ScanStatsService::groupParts(mounted, groups, refusedPerStorage) und statisch partsOf(...): {groups, singles, refused, representatives}"
  - "AdminViewService: COVERAGE_MAX_MOUNTED, COVERAGE_MAX_MEMBERS, COVERAGE_MAX_SINGLES, coverageBody, perDocumentAnswer, perDocumentDenominator, perDocumentFigures; coverage-Schlüssel counting, perDocument, notReadable, legacyCount, legacyReason"
affects:
  - 43-06 (Anzeige von notReadable, legacyCount, counting, Hinweis)
  - 43-07 (PHPUnit im CI)
tech-stack:
  added: []
  patterns:
    - "Rechnung als statische Methoden (perDocumentAnswer/Denominator/Figures, partsOf), Orchestrierung in kleinen privaten Methoden, testbar per Reflection ohne Konstruktor"
    - "N1 über den Dateicache: path_hash, LEFT JOIN findling_file_state auf PHP-only-Paare, IS NULL"
key-files:
  created:
    - php/tests/Unit/FileStateServiceCoverageTest.php
    - php/tests/Unit/CoverageTopologyParityTest.php
  modified:
    - php/lib/Service/AdminViewService.php
    - php/lib/Service/FileStateService.php
    - php/lib/Service/ScanStatsService.php
    - php/tests/Unit/AdminViewServiceTest.php
    - php/tests/Unit/ScanStatsServiceTest.php
    - php/tests/Unit/SettingsControllerTest.php
    - backend/tests/test_measurement_scripts.py
decisions:
  - "N1 über den Dateicache statt über findling_file_state: diese Tabelle hält nie indexed, ein indexiertes Mitglied wäre unsichtbar (Befund aus 43-03). Ein Pfad zählt als PHP-only, solange kein Mitglied der Gruppe dieselbe filecache-Zeile (path_hash) ohne PHP-only-Urteil hat"
  - "distinctPathsByReasons liefert unreadable+stuck und gone in einem Lauf (byGroup = alle drei, notReadable* = die ersten zwei), damit ein Pfad mit zwei verschiedenen PHP-only-Urteilen nicht doppelt zählt"
  - "COVERAGE_MAX_SINGLES = 25.000 Einzelspeicher: darüber legacy/limits, weil ExAppService::MAX_BODY_BYTES = 1 MiB die Antwort ablehnen würde (43-04 gemessen: 1,40 MB bei 50.000); sichtbar statt still (W10)"
  - "AdminViewService bekommt LoggerInterface als letzten Konstruktorparameter (vorher kein Logger); DI ist automatisch, SettingsControllerTest übergibt ihn"
  - "Im neuen Weg: Scan-Zähler der Coverage aus totals()['grouped'] (Vertreter), refusedByType = Summe der abgezogenen refused der Vertreter und Einzelspeicher, deduplicated = true (kein duplicates-Satz)"
  - "Während counting: Nenner = Summe der PHP-Teile, percent und embeddedPercent null"
  - "Antwortprüfung streng: Summen gleich Summe der Teile, documents_g <= judged_g, embedded <= documents, ByStorage nur Einzelspeicher des Bodys, jede ID einmal; sonst Fallback mit einer Warnzeile"
metrics:
  duration: "ca. 110 min (mit Pause wegen Ratelimit)"
  completed: 2026-11-07
  tasks: 3
  files: 9
---

# Phase 43 Plan 05: Zählung pro Dokument auf der Admin-Seite Summary

Die Admin-Übersicht fragt den Container per `adminSend('/coverage', {mounted, groups})` mit derselben Mountmenge und denselben Gruppen, aus denen sie den Nenner baut, und rechnet den Nenner pro Gruppe und Einzelspeicher als max(PHP_g, judged_g + phpOnly_g); refused zählt nur noch über eingebundene Speicher (B1), nicht lesbare Dateien senken die Quote und stehen als `notReadable` daneben.

## Umsetzung

- **FileStateService**: `countByReasonPerStorage` (Filter wie countByReason: geschlossene Listen, filecache-Join, beide Papierkorbpfade; `GROUP BY fc.storage`; Bänder zu `STORAGE_BAND = 1000`; leere Liste fragt nichts). `distinctPathsByReasons(groups, singles)`: liest die PHP-only-Urteile (`PHP_ONLY_NOT_READABLE` = skipped/unreadable, failed/repeatedly_stuck; `PHP_ONLY_GONE` = skipped/gone) über `INNER JOIN filecache` (W-b: ohne filecache-Zeile nirgends), schlüsselt je Gruppe nach `fc.path_hash` (interner Pfad, Schlüsselraum des doc_key), prüft N1 je Gruppe mit einer Abfrage über die Mitglieder dieser Gruppe (`LEFT JOIN findling_file_state` auf die PHP-only-Paare, `s.file_id IS NULL`), Bänder zu 1000 auch für die Hashes. Rückgabe nur Zahlen.
- **ScanStatsService**: Zeilenlesen als `rowsOf`, Vertreterwahl als `representative` (totals und groupParts nutzen dieselbe Regel), `groupParts` und statisch `partsOf`: PHP_g = files_seen - overCap - excluded - refused des Vertreters, nie unter 0, je Einzelspeicher ebenso (ohne Zeile 0), ohne leaveOut-Abzug (W9). `totals()` unverändert im Verhalten.
- **AdminViewService::overview()**: `coverageBody` (eingebundene IDs sortiert, Gruppen nur eingebundene Mitglieder, je ID einmal, nur ab zwei Mitgliedern), `perDocumentCoverage` (Grenzen -> legacy/limits mit Warnzeile und den Zahlen mounted, members, singles; `missing` -> legacy/missing mit "Findling: the backend has no per document count, the page shows the 1.6.2 figure"; unreachable/busy/refused oder ungültige Antwort -> fallback, der 1.6.2-Weg wie bisher). Bei ok/counting: `/status` ohne leaveOut, `perDocumentFiguresFor` (countByReasonPerStorage über mounted, groupParts, distinctPathsByReasons), `perDocumentFigures` (indexed = documents, embedded = embeddedDocuments, indexable = perDocumentDenominator). `coverage()` mit den neuen Schlüsseln; im neuen Weg recounting immer false (Kommentar D-43-09/D-43-11), bei counting beide Quoten null. Nutzersichtbare Sätze kommen erst mit 43-06.

## Tests (PHPUnit, laufen erst im CI von 43-07)

- AdminViewServiceTest (+15 Testmethoden, eine davon mit 15 Datenprovider-Fällen für kaputte Antworten): (a) ok mit Nenner pro Gruppe, recounting false; (b) `testKindOkKeepsTheGroupedDenominator` (W9); (c) Maximum pro Teil statt über die Summen (72 statt 60); (d) 190/200 = 95 und notReadable 10; Nachhinken von files_seen (3 + 1 > 2, Quote 75); (e) B1: countByReason nie, countByReasonPerStorage nur mit den mounted des Bodys, distinctPathsByReasons mit Gruppen und Einzelspeichern; (f) counting: Quoten null; (g) missing: legacy, Warnzeile, legacyCount/legacyReason; (h) über COVERAGE_MAX_MOUNTED, COVERAGE_MAX_MEMBERS und COVERAGE_MAX_SINGLES kein adminSend, legacy/limits; unreachable/busy/refused als stiller Fallback; ok und counting; (i) 15 kaputte Antworten (String, negativ, Float, Listenlänge, Objekt statt Liste, Mitglied als Einzelspeicher, nicht eingebunden, doppelte ID, Dreierpaar, falsche Summen, documents > judged, embedded > documents, counting fehlt/String) je null und Fallback mit einer Warnzeile; (j) Body-Aufbau; Grenzen gleich dem Container.
- ScanStatsServiceTest (+7): Vertreter mit eigenem refused, refused eines nicht eingebundenen Speichers wirkungslos, kein leaveOut-Abzug, nie unter 0, ohne Mounts keine Abfrage, Position einer Gruppe ohne eingebundenes Mitglied, totals und groupParts nennen denselben Vertreter.
- FileStateServiceCoverageTest (neu, 12): 2500 IDs in drei Abfragen (1000/1000/500), jede Abfrage mit `fc.storage` eingeschränkt und filecache-Join, leere/ungültige Listen und fremdes Paar ohne Abfrage; Topologie ergibt byGroup [3, 1], notReadable [2, 1], Einzelspeicher {31: 1, 32: 1}; N1 (`testUnreadableForOneMemberIndexedForAnotherCountsOnceAndIsNotInNotReadable`); N1-Prüfung nur über die Mitglieder derselben Gruppe; inner join für gone (W-b), 41 nie gefragt; 2500 Einzelspeicher in drei Bändern; Einzelspeicher ohne N1-Abfrage; nur Zahlen.
- CoverageTopologyParityTest (neu, 7): liest die Fixture (FINDLING_REPO_ROOT, `dirname(__DIR__, 3)/backend/...`, `dirname(__DIR__, 3)/findling-src/backend/...`, fehlend = rot); Body gleich Topologie, Containerantwort hält die Prüfung, Teile gleich expected.php.groupParts, B1, Nenner 30, Zähler 13, Vektoren 5, notReadable 5, Quote 43, Vektorquote 16, Maximum je Teil gleich denominatorParts, kein Teil über 100 %.

## Lokale Checks

- Kein php: kein `php -l`, kein PHPUnit; Syntax per Durchsicht. `git diff --check` sauber, keine U+2013/U+2014 in den berührten PHP-Dateien.
- Plan-verify Task 1, 2, 3: grün.
- Python-Tests, die PHP-Quellen lesen (23 Module, darunter admin_ui_contract, php_surface_bans, php_trust_boundary, store_metadata, measurement_scripts, coverage_counts): 1415 passed, 7 skipped. Keine Python-Quelle geändert, daher keine weitere Volltestsuite (letzte am Stand 43-04: alles grün).
- Gates: ruff check und ruff format --check grün (253 Dateien), pyright (latest) 0 errors (ein Lauf brach einmal ohne Ausgabe ab, zweimal neu: 0 errors), vulture leer.
- Baumhash PHP: zwei Schritte, beide zweimal gerechnet (Rezept 40b-baumhash.py und `find | LC_ALL=C sort | tr -d '\r' | sha256sum`), Positivkontrolle über `git archive HEAD` vor dem Schritt:
  - feat 470de86a: 120 Dateien, 422c02f7... -> be729b12ab01142812dfe5d81c40832f0b52a6943be79e3b5bd9ce0b60f5d61d (Kontrolle 422c02f7).
  - test b0be0870: 120 -> 122 Dateien, be729b12... -> df3a2adcfa61b355e9021eff5b9b6be193a40913eb8004ff6f6c86d2644544ce (Kontrolle be729b12).
  - PACKAGE-Paar und eingefrorenes PHP_FILES/PHP_TREE_HASH unberührt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] N1 über den Dateicache statt über findling_file_state**
- **Found during:** 43-03 (Hinweis dort), umgesetzt in Task 1
- **Issue:** Die Plan-Bedingung `NOT EXISTS` über findling_file_state der Mitglieder sieht ein indexiertes Mitglied nie (die Tabelle hält kein indexed); eine Datei, die für ein Mitglied indexiert und für ein anderes unlesbar ist, wäre doppelt gezählt und als nicht lesbar gemeldet worden.
- **Fix:** Kandidaten je Gruppe nach path_hash; eine Abfrage je Gruppe über filecache der Mitglieder mit LEFT JOIN auf PHP-only-Urteile und `IS NULL`.
- **Commit:** 470de86a

**2. [Rule 2 - Korrektheit] Sichtbarer Fallback über 25.000 Einzelspeichern**
- **Issue:** ExAppService lehnt Antworten über 1 MiB ab; bei mehr als grob 37.000 Einzelspeichern mit Dokumenten wäre der neue Weg still als `refused` auf 1.6.2 gefallen.
- **Fix:** `COVERAGE_MAX_SINGLES = 25000`, darüber legacy/limits mit Warnzeile (Zahl singles im Kontext). ExAppService bleibt unverändert. Für die Owner-Runde (K4) zu nennen.

**3. [Rule 3 - Blocking] Logger in AdminViewService**
- AdminViewService hatte keinen Logger; neuer letzter Konstruktorparameter `LoggerInterface $logger`, `php/tests/Unit/SettingsControllerTest.php` (nicht in files_modified) übergibt ihn.

**4. Form**
- `distinctPathsByReasons(array $groups, array $singles)` statt `(array $pairs, array $storageGroups)`: die Paare sind Konstanten, alle drei in einem Lauf (siehe decisions).
- `groupParts` liefert zusätzlich `refused` und `representatives`.
- Task 1 und Task 2 in einem feat-Commit (470de86a), weil der PHP-Baumhash je Commit stimmen muss und beide Tasks dieselben Paare bewegen; Task 3 eigener test-Commit (b0be0870). Im test-Commit wurde der PHP-Teil des neuen Wegs aus overview() in `perDocumentFiguresFor` verschoben (gleiches Verhalten), damit Fall (e) ohne den ganzen overview()-Aufbau prüfbar ist.

## Offene Punkte und Risiken für den CI-Lauf (43-07)

- Der Teil "/status wird im neuen Weg ohne leaveOut gefragt" (Fall b) ist nur per Code geprüft (`$parameters = []` im neuen Zweig), nicht per PHPUnit: overview() braucht rund ein Dutzend Doubles. Abdeckung durch die E2E-Strecke empfohlen.
- Mock-Annahmen: `IExpressionBuilder::andX/orX` liefern einen Mock von `ICompositeExpression`, `IFunctionBuilder::count` einen von `IQueryFunction`; `leftJoin` nimmt eine ICompositeExpression als Bedingung.
- `ReflectionProperty::setValue` auf promovierte private Eigenschaften einer ohne Konstruktor gebauten Instanz (PHP >= 8.1 ohne setAccessible).
- Kein `php -l` lokal: der Lint-Job von php.yml (`find php/lib ... php -l`) ist der erste echte Syntaxbeleg.

## Threat Flags

Keine neue Oberfläche: ausgehend nur die neue ADMIN-Route aus 43-04 (Body nur IDs), eingehend nur geprüfte Zahlen (T-43-14); SQL nur mit gebundenen Parametern in Bändern (T-43-15); keine Pfade aus distinctPathsByReasons (T-43-44).

## Known Stubs

Keine im Rechenweg. Die Anzeige der neuen Schlüssel (notReadable, legacyCount, counting, Hinweis) folgt planmäßig in 43-06.

## Self-Check: PASSED

- php/tests/Unit/FileStateServiceCoverageTest.php und php/tests/Unit/CoverageTopologyParityTest.php vorhanden; die grep-Prüfungen der Pläne (adminSend('/coverage', perDocumentDenominator, judgedByGroup, countByReasonPerStorage, 'legacyReason', 'notReadable', COVERAGE_MAX_MOUNTED, STORAGE_BAND = 1000, groupParts, coverage_topology.json, KeepsTheGroupedDenominator) treffen.
- Commits 470de86a (feat) und b0be0870 (test) im Log, Autor street1983nk <k.cherif@outlook.de>, kein Trailer, 0 Treffer für closes/fixes/resolves #N, keine Löschungen.
