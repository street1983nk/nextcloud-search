---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 15
subsystem: php/companion (Auftrag, Reconcile-Route)
tags: [doc-key, issue-25, d-43-14, reconcile, queue]
requires:
  - 43-02 (Bindende Vorgaben, Baumhash-Stand)
provides:
  - "DocKeyService::docKeyOf(string): string (statisch) und docKeysFor(list<int>): {keys, absent}"
  - "Feld docKey in jedem Auftrag außer delete (content, ocr, metadata, acl, embed)"
  - "GET /ocs/v2.php/apps/findling/reconcile/doc-keys?ids=1,2,3 (oder ids[]=), höchstens ReconcileController::DOC_KEY_BAND = 200"
  - "backend/tests/fixtures/doc_key_cases.json (13 Fälle, Hash von Hand)"
affects:
  - 43-16 (Container: Spalte doc_key, Backfill über die Route, DOC_KEY_BAND-Parität)
tech-stack:
  added: []
  patterns:
    - "Dokumentschlüssel aus oc_filecache.path per Datei-ID über IFileAccess::getByFileIds, nie aus dem Leser-Knoten"
    - "eine Abfrage je Auftragsstapel, fehlgeschlagene Abfrage lässt das Feld weg statt den Claim zu stoppen"
key-files:
  created:
    - php/lib/Service/DocKeyService.php
    - php/tests/Unit/DocKeyServiceTest.php
    - backend/tests/fixtures/doc_key_cases.json
  modified:
    - php/lib/Service/QueueService.php
    - php/lib/Controller/ReconcileController.php
    - php/appinfo/routes.php
    - php/tests/Unit/QueueServiceTest.php
    - php/tests/Unit/QueueServiceReaderTest.php
    - php/tests/Unit/ReconcileControllerTest.php
    - php/tests/route-security.json
    - backend/tests/test_measurement_scripts.py
    - backend/tests/test_php_trust_boundary.py
decisions:
  - "Dateicache-Lesung über OCP IFileAccess::getByFileIds statt eigener Querybuilder-Abfrage (gleiche Quelle oc_filecache, Muster SearchService/PathResolverService, StorageService-Regel 'kein handgeschriebenes SQL gegen den Dateicache'); Papierkorb-Ausschluss wie countByReason (files_trashbin/, __groupfolders/trash/)"
  - "docKeyOf ist statisch und nimmt nur den Pfad; der Speicher-/Gruppenbezug entsteht im Container über storage_id und countingKey"
  - "docKey auch in embed-Aufträgen (alle Arten außer delete, auch per Ausschlussregel zu delete gewordene Zeilen tragen keinen)"
  - "Route nimmt ids als Komma-Wert oder als ids[]-Liste, beide gleich streng (kanonische positive Ganzzahlen, 1 bis 200, Rohlänge begrenzt)"
  - "Leere keys werden als JSON-Objekt {} geliefert, nie als Liste"
metrics:
  duration: "ca. 70 min"
  completed: 2026-11-07
  tasks: 2
  files: 12
---

# Phase 43 Plan 15: Dokumentschlüssel aus dem internen Pfad Summary

PHP liefert jetzt zu jedem Auftrag `docKey` = sha256-hex über `oc_filecache.path` der Datei-ID (NFC, ohne führenden Schrägstrich, `files/` bleibt), gelesen einmal je Claim über `DocKeyService::docKeysFor`, und dieselben Schlüssel bandweise über die neue ExApp-Route `GET /reconcile/doc-keys` für den Backfill aus 43-16.

## Umsetzung

- **DocKeyService** (neu, nicht final, damit mockbar): `docKeyOf` normalisiert nur (ltrim '/', `\Normalizer` FORM_C mit Rückfall auf den Rohwert wie `Provider::composed`), `hash('sha256', ...)`. `docKeysFor` filtert IDs > 0, entdoppelt, fragt `IFileAccess::getByFileIds` in Bändern zu 200; jede gefragte ID landet in genau einer Liste (keys oder absent; absent = kein Eintrag oder Papierkorbpfad). Kein Log, kein Pfad in der Antwort.
- **QueueService**: neuer Konstruktorparameter `DocKeyService`; `claim()` ruft nach der Stapelschleife einmal `withDocKeys($sources)`. Alle Aufträge außer delete bekommen `'docKey' => ...`, wenn der Dateicache einen Schlüssel liefert; sonst fehlt das Feld. Wirft die Abfrage, bleibt der Claim unverändert (Warnung mit `exception` und `count`, kein Pfad). Docblock verweist auf readerOf/SharedMount und SearchService::reduceIds.
- **ReconcileController::docKeys**: `#[ExAppRequired]`, `#[NoCSRFRequired]`, `ApiRoute GET /reconcile/doc-keys`, `rejectForeignCaller()` als erste Anweisung, `DOC_KEY_BAND = 200` (public const, Parität für 43-16), 400 "File id list is not valid." vor jedem Zugriff, 500 mit statischem Satz bei Fehler, Debug-Zeile nur mit Zählern `asked/keys/absent`.
- **Allowlist**: `ReconcileController::docKeys` in `php/tests/route-security.json`; `routes.php` bleibt leer (RouteSecurityTest verlangt `['routes' => [], 'ocs' => []]`), nur der Docblock nennt die Route.
- **Fall-Katalog** `backend/tests/fixtures/doc_key_cases.json`: 13 Fälle (Home mit `files/`, führender Schrägstrich, extern, `files/Rechnung.pdf` vs. `Rechnung.pdf`, NFC und NFD gleich, Leerzeichen, tief verschachtelt, zwei Einhängepunkte gleicher interner Pfad, Groß-/Kleinschreibung bleibt, Team-Folder-Pfad). Jeder Hash mit `printf '%s' '<pfad>' | sha256sum` gerechnet, Befehl im Feld `derivation`. Datei reines ASCII (Umlaut und kombinierendes Zeichen als JSON-Escape mit Backslash-u, damit NFC und NFD sichtbar getrennt bleiben).

## Tests (PHPUnit, laufen erst im CI)

- DocKeyServiceTest (12): Katalog gegen docKeyOf, Relationen sameAs/differsFrom, files/-Präfix, Schrägstriche, Vollständigkeit keys+absent, Papierkorb beider Arten, Gruppenmitglieder gleicher Schlüssel, nur Hex, Bänder 200/200/50, ungültige und doppelte IDs, leere Anfrage ohne Zugriff. Katalogsuche: `FINDLING_REPO_ROOT`, `dirname(__DIR__, 3)/backend/...` (lokal) und `dirname(__DIR__, 3)/findling-src/backend/...` (CI-Layout aus php.yml); fehlt er, scheitert der Test (kein Skip).
- QueueServiceTest (+8): Feld im Auftrag neben `path`; **testReaderViaSharedMountYieldsTheSameDocKeyAsTheOwner** (Leser aaron über SharedMount, `getInternalPath()` = 'Plan.xlsx', anderer Leserpfad; Schlüssel gleich dem Eigentümer-Fall und gleich docKeyOf('Gemeinsam/Plan.xlsx')); zwei Einhängepunkte ein Schlüssel; docKeysFor genau einmal je Claim (acl, metadata, content); delete ohne Feld und ohne Abfrage; fehlende Cache-Zeile ohne Feld; fehlschlagende Abfrage stoppt den Claim nicht und loggt keinen Pfad; keine Logzeile mit Pfad oder Schlüssel.
- ReconcileControllerTest (+8): Band 200, fremder Aufrufer 403 ohne Abfrage, 16 ungültige Formen 400 ohne Werte im Log, genau 200 IDs angenommen, Komma- und Listenform gleich, Vollständigkeit und nur Hex mit echtem DocKeyService, leere keys als `{}`, Fehler 500 ohne Meldung im Log.

## Lokale Checks

- Task-1-verify: grün (inkl. Python-Neuberechnung aller 13 Hashes, `TASK1-VERIFY-OK`).
- Task-2-verify: grün; `tests/test_measurement_scripts.py` 572 passed.
- Gates unter backend/: ruff check "All checks passed!", ruff format --check "248 files already formatted", pyright (latest) 0 errors, vulture leer.
- Betroffene Python-Module seriell (alle Tests, die PHP-Quellen lesen, 59 Module in drei Läufen): 417 passed/131 skipped, 1396 passed/139 skipped, 992 passed/7 skipped.
- Kein `php -l` und kein PHPUnit lokal (kein PHP).
- Baumhash PHP: PHP_FILES_TODAY 118 -> 120, PHP_TREE_HASH_TODAY eb5b2dc1... -> 422c02f73b37c27e590ff24a8cf4b0b52ffec5e80380d35e9d8fd75991afc651. Zweimal gerechnet: Rezept 40b-baumhash.py und unabhängig `find | LC_ALL=C sort | tr -d '\r' | sha256sum`, beide 422c02f7; Positivkontrolle derselben Pipeline über `git archive HEAD` vor dem Schritt: eb5b2dc1. PACKAGE-Paar und eingefrorenes PHP_FILES/PHP_TREE_HASH unberührt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] routes.php bleibt leer, Route per Attribut**
- **Issue:** Plan verlangt "Route in routes.php"; RouteSecurityTest::testAppinfoRoutesDeclaresNoRoute fordert leere Arrays, alle Routen stehen als ApiRoute-Attribut.
- **Fix:** Route als Attribut am Controller, `doc-keys` nur im Docblock von routes.php (erfüllt das grep-verify ehrlich, ändert keine Registrierung).

**2. [Rule 3 - Blocking] QueueServiceReaderTest.php angepasst**
- Nicht in files_modified; neuer Konstruktorparameter verlangt `$this->createMock(DocKeyService::class)`.

**3. [Rule 2 - Korrektheit] Ratsche in backend/tests/test_php_trust_boundary.py**
- Routenzahl-Untergrenze 20/19 -> 21/20 mit Absatz (Kommentar dort: "Every plan that adds a route raises this bound").

**4. Abweichung in der Form**
- Plan nennt `docKeys(string $ids)`; umgesetzt als `docKeys()` mit `getParam('ids')` wie `goneStorages`, damit Komma-Wert und `ids[]`-Liste beide funktionieren und das Framework keinen Typfehler bei einer Liste wirft.
- Artefakt-Zeile nennt `docKeyOf(int storageId, string internalPath)`; umgesetzt nach dem Action-Text als `docKeyOf(string $filecachePath)` (Speicherbezug im Container).
- Dateicache über `IFileAccess::getByFileIds` statt Querybuilder (siehe decisions).

## Risiken für den CI-Lauf (PHPUnit erst nach freigegebenem Push)

- Kein lokales `php -l`: Syntax nur per Durchsicht geprüft.
- Pfad zum Katalog im CI: angenommen `$GITHUB_WORKSPACE/findling-src/backend/tests/fixtures/doc_key_cases.json` (php.yml checkt nach `findling-src` aus und verschiebt nur `php`). Falls falsch, scheitern die drei Katalog-Tests mit Liste der gesuchten Pfade; Abhilfe `FINDLING_REPO_ROOT` im Job.
- Mock von `IMountPoint::getMountType` (seit NC 12) und `IFileAccess::getByFileIds` (im Projekt schon gemockt) angenommen vorhanden.
- NFD-Fall braucht `\Normalizer` (intl ist im CI-Setup aktiviert; Nextcloud bringt zusätzlich den Polyfill).
- MINIMUM_TESTS und ROUTE_GATE_MIN_TESTS bleiben Untergrenzen, kein Anpassungsbedarf.

## Hinweise

- STATE.md/ROADMAP.md nicht angefasst (wie 43-02, Koordinator).
- 43-TEXTE.md und 43-FREIGABEN.md nicht angefasst. Nichts gepusht.
- Für 43-16: `DOC_KEY_BAND = 200` ist `public const` in ReconcileController für den Paritätstest; Antwortform `{"keys": {"<id>": "<hex>"}, "absent": [ids]}` innerhalb der OCS-Hülle.

## Self-Check: PASSED

- Dateien vorhanden: php/lib/Service/DocKeyService.php, php/tests/Unit/DocKeyServiceTest.php, backend/tests/fixtures/doc_key_cases.json.
- Commit 49af9a8e im Log, Autor street1983nk <k.cherif@outlook.de>, kein Trailer, 0 Treffer für closes/fixes/resolves #N, keine Löschungen.
