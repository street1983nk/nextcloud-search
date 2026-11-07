---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 17
subsystem: php-content-gateway
tags: [smb, gateway, deadline, dos, tdd]
requires: [43-06]
provides: [D-43-16, BoundedStreamReader, BoundedStreamResponse]
affects: [43-18, 43-19, 43-08]
tech-stack:
  added: []
  patterns: [Vorlesen vor den Headern, nicht blockierendes Lesen nur auf Speicher-Entscheid, Fake-Uhr per Closure]
key-files:
  created:
    - php/lib/Http/BoundedStreamReader.php
    - php/lib/Http/BoundedStreamResponse.php
    - php/tests/Unit/ScriptedStream.php
    - php/tests/Unit/BlockCollectingStream.php
    - php/tests/Unit/BoundedStreamReaderTest.php
  modified:
    - php/lib/Controller/GatewayController.php
    - php/tests/Unit/GatewayControllerTest.php
    - backend/tests/test_measurement_scripts.py
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-CONTEXT.md
decisions:
  - "D-43-16: Content-Gateway liest SMB ohne Server-Verschlüsselung nicht blockierend mit Fristen (30 s / 30 s), Lesedeckel 60000, 422 vor den Headern; alle anderen Speicher blockierend"
  - "Lesedeckel MAX_READS gilt nur, wenn wirklich nicht blockierend gelesen wird (prime liefert nonBlocking, pump bekommt capReads)"
  - "Reader kommt per DI; SimpleContainer fällt bei ?Closure-Parametern auf den Vorgabewert zurück, keine Fabrik nötig"
metrics:
  completed: 2026-11-07
  tasks: 2
  files: 9
---

# Phase 43 Plan 17: Content-Gateway mit Frist statt blockierender Kopie Summary

Der Content-Gateway liest Dateien eines unverschlüsselten SMB-Speichers nicht blockierend vor, entscheidet die Antwort vor den Headern (422 bei Frist, 0 Bytes trotz Größe, fread false, FileInUseException) und reicht den Rest mit Leerlauffrist, wachsender Pause und Lesedeckel weiter; alle anderen Speicher lesen blockierend wie bisher.

## Commits

| Task | Commit | Betreff |
|------|--------|---------|
| 1 (RED) | 33e37362 | test(43-17): a gateway read with a deadline instead of a blocking copy |
| 2 (GREEN) | 8b5ceaac | fix(43-17): the content gateway never waits forever on a file it cannot open |

## Umsetzung

- **BoundedStreamReader** (`OCA\Findling\Http`): Konstanten wie geplant (FIRST_BYTE_SECONDS 30.0, IDLE_SECONDS 30.0, Pausen 1 bis 20 ms vor Daten, 20 bis 200 ms nach Daten, BLOCK_BYTES 8192, MAX_READS 60000). `prime()` schaltet nur auf Anforderung auf nicht blockierend und liefert zusätzlich `nonBlocking` (ob der Schalter wirklich griff); `pump()` schreibt Kopf und Rest, prüft nach jedem Block `connection_aborted`, schließt den Stream in `finally`.
- **BoundedStreamResponse**: `ICallbackResponse`, 200, kein Content-Length, Warnzeilen "stalled" und "ended before its size" je nur mit fileId, beim Client-Abbruch keine Zeile.
- **GatewayController**: Größe und Speicher vor dem Öffnen, Flag `instanceOfStorage(SMB) && !instanceOfStorage(Encryption)`, 422-Zweig als `cannotOpen()` (Logzeile genau einmal im Code), FileInUseException per `is_a` auf 422 ohne error-Zeile, StorageNotAvailableException und alle anderen Ausnahmen bleiben 500. Route, Attribute und `rejectForeignCaller()` als erste Anweisung unverändert.
- **SimpleContainer-Befund**: `?\Closure`-Parameter löst der Container über `query('Closure')` auf, das scheitert mit QueryException (Closure ist nicht instanziierbar), danach greift `isDefaultValueAvailable()` (SimpleContainer.php:97). Die float-Parameter fallen ebenso auf ihre Vorgabe. Keine Fabrik `withClock` nötig.
- **FileInUseException**: kommt vom Server unverändert an (SMB::fopen fängt sie nicht, `grep` in lib und apps/files_external ohne Treffer); ihre Meldung enthält den Pfad (`'Invalid request for ' . $path`), deshalb keine error-Zeile.
- **Baumhash PHP**: 124 auf 129 Dateien, abd32292 auf e67c5d95859f156c8178c5ca27876bd371dc06f7064f473f16afe8452d911591, zweimal gerechnet (Rezept 40b-baumhash.py und find, LC_ALL=C sort, tr -d '\r', sha256sum), Kontrolle über `git archive HEAD~1` vor dem Plan ergab abd32292, nach dem Commit über `git archive HEAD` erneut e67c5d95. PHP_FILES/PHP_TREE_HASH und das PACKAGE-Paar unberührt.

## Tests

- **PHPUnit lokal: nein.** Freier RAM vor dem Start des Docker-Daemons 4,89 GB (und beim zweiten Versuch 6,0 GB), nach dem Start jeweils 2,3 GB und darunter (Tiefstwert 1,11 GB, beim ersten Start liefen Container anderer Projekte mit Restart-Policy an). Der Lauf hätte unter 4 GB stattgefunden, deshalb nach F2 nicht gestartet; Docker beide Male mit `docker desktop stop` beendet, danach 3,91 bzw. 4,85 GB frei, keine eigenen Container angelegt. Weder RED (Filter `BoundedStreamReader|GatewayController`) noch GREEN (Filter plus RouteSecurity, voller Lauf mit Bodenprüfung) lokal belegt. **Verbindlicher Beleg: CI-Job "PHPUnit over the companion app" nach dem Push in 43-18.** Die RED-Aussage folgt aus dem Stand von 33e37362: `php/lib/Http/` existierte nicht, beide Testdateien referenzieren die fehlenden Klassen.
- Python lokal: test_measurement_scripts, test_php_trust_boundary, test_php_acl_boundary, test_php_surface_bans 680 passed; PHP-lesende Module (coverage_counts, exapp_surface, gateway_client, migration_path, phase34/35/36/39/40/41-Audit, php_route_gate_presence, php_supply_chain_gates, probe_php_parity, public_artifacts, store_metadata, unified_search_*, admin_ui_contract) 724 passed, 25 skipped.
- Gates: ruff check grün, ruff format --check (254 Dateien), pyright latest 0 errors, vulture leer.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Korrektheit] Lesedeckel nur im nicht blockierenden Modus**
- **Found during:** Task 2
- **Issue:** Ein Deckel von 60000 Reads über alle Speicher hätte jede lokale oder verschlüsselte Datei über rund 469 MiB kurz enden lassen, sobald ein Admin FINDLING_MAX_FILE_BYTES erhöht; das widerspricht dem Erfolgskriterium "keine lesbare Datei eines anderen oder verschlüsselten Speichers ändert ihr Verhalten" und der Grenze des Plans selbst ("eine größere Wrapped-SMB-Datei endet kurz").
- **Fix:** `prime()` liefert zusätzlich `nonBlocking` (Schalter wirklich gesetzt), `pump()` hat einen sechsten Parameter `bool $capReads = true`, der Controller reicht `$primed['nonBlocking']` über BoundedStreamResponse durch. Nativer SMB-Modus (NativeStream verweigert den Schalter) und alle blockierenden Speicher sind damit ungedeckelt.
- **Commit:** 8b5ceaac

**2. [Rule 1 - Bug] Testhilfe BlockCollectingStream ohne dir_opendir**
- **Found during:** Durchsicht vor Task 2 (kein lokales PHP)
- **Issue:** `Icewind\Streams\Wrapper` implementiert das Interface Directory, `dir_opendir` ist abstrakt; die Klasse aus dem RED-Commit wäre beim Laden fatal gescheitert.
- **Fix:** `dir_opendir` gibt false; dazu `stream_set_option` von ScriptedStream mit `mixed` für arg1/arg2.
- **Commit:** 8b5ceaac

**3. Rechnung im Kommentar**
- Der Plan nannte etwa vier leere Reads je 64-KiB-Happen (rund 9600 Reads). Mit den Pausen 20, 40, 80, 160, 200 ms sind es fünf bis sechs bis zum nächsten Happen nach 0,6 s, zusammen etwa 11000 Reads; so steht es im Kommentar, der Test prüft unter MAX_READS und unter 12000.

**4. Werkzeug-Befund zum verify von Task 2**
- Die zwei grep-Prüfungen mit `\\\\` (Encryption, FileInUseException) liefern im Git-Bash-grep 3.0 dieser Maschine immer 0, auch für `echo 'x\F' | grep 'x\\F'`. Inhalt per `grep -F 'OC\Files\Storage\Wrapper\Encryption'` und `grep -F 'Icewind\SMB\Exception\FileInUseException'` geprüft (je 1 Treffer); alle übrigen Teile des verify grün.

## Grenzen (je ein Satz für "Known limitations" in 43-08)

- MAX_READS = 60000 Reads zu höchstens 8 KiB sind etwa 469 MiB; eine größere Wrapped-SMB-Datei endet kurz, der Container sieht ShortRead und gibt sie nach den Zustellungen als repeatedly_stuck auf; das betrifft nur Instanzen mit FINDLING_MAX_FILE_BYTES über der Vorgabe 50 MB.
- Bei Server-Verschlüsselung plus DENY-ACE hängt der Abruf schon in fopen (Encryption.php:246, skipHeader), vor jedem Vorlesen.
- Eine SMB-Freigabe unter aktiver Server-Verschlüsselung wird weiter blockierend gelesen und bleibt damit ohne Schutz gegen den Hänger.
- Ein Netzfehler zwischen stat und cli_open im Wrapped-Modus wird 422 und damit (43-18) unreadable; die gedeckelte Wiederholung mildert das (W9).
- W10: erwartet der Container 0 Bytes (requeueAs), erkennt er eine kurze Antwort nicht als ShortRead.
- Der Client-Abbruch wird erst bemerkt, wenn PHP beim Ausgeben den Abbruch sieht (connection_aborted nach setOutput); View setzt ignore_user_abort(true), das Lesen endet dann am nächsten Block.

## Threat Flags

Keine neue Angriffsfläche: keine neue Route, kein neuer Schlüssel; die neuen Logzeilen tragen nur fileId (T-43-55).

## Known Stubs

Keine.

## Self-Check: PASSED

- Dateien vorhanden: php/lib/Http/BoundedStreamReader.php, php/lib/Http/BoundedStreamResponse.php, php/tests/Unit/ScriptedStream.php, php/tests/Unit/BlockCollectingStream.php, php/tests/Unit/BoundedStreamReaderTest.php.
- Commits vorhanden: 33e37362, 8b5ceaac.
