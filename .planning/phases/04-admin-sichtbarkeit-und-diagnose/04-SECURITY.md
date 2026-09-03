---
phase: 04-admin-sichtbarkeit-und-diagnose
audited: 2026-09-03
asvs_level: 2
block_on: critical
register_authored_at_plan_time: true
threats_total: 65
threats_closed: 65
threats_open: 0
supply_chain_entries: 10 (T-04-SC, one per plan) - all closed
unregistered_flags: 0
status: SECURED
---

# Security-Audit Phase 4: Admin-Sichtbarkeit und Diagnose

Verifikation der Dispositionen aus den zehn `<threat_model>`-Bloecken der Plaene
04-01 bis 04-10. Der Auditor hat kein Implementierungsfile geaendert. Jede
Zeile unten ist gegen die Quelle belegt, nicht gegen die Absicht des Plans.

**Ergebnis: 65 von 65 Bedrohungen geschlossen.** Der Audit vom 03.09. fand
T-04-64 zunaechst offen (fehlender Nachweis, kein Codemangel); die fehlende
Messung wurde am selben Tag nachgeholt und ist unten unter T-04-64 belegt.

## Ausgefuehrte Nachweise

| Nachweis | Ergebnis |
|----------|----------|
| Gate A `test_readonly_gate.py`, Gate B `test_php_trust_boundary.py`, Gate C `test_admin_ui_contract.py`, Gate D `test_exclusion_path_space.py`, Reason-Paritaet `test_extract_errors.py` | 118 passed |
| `test_status_endpoint.py`, `test_rates_endpoint.py`, `test_diagnose_endpoint.py` | 45 passed |
| `php/appinfo/routes.php` leer, alle Routen attributbasiert, Gate B sieht also jede Route | bestaetigt |
| Manifest-Diff ueber das gesamte Phasen-4-Fenster (538f8dd^..HEAD) auf `backend/pyproject.toml`, `php/composer.json`, `uv.lock`, `composer.lock` | leer |
| `package.json` an keiner Stelle des Repos | bestaetigt |

## Trust Boundaries dieser Phase

| Grenze | Durchsetzung | Beleg |
|--------|--------------|-------|
| Browser-Sitzung zu PHP-Admin-Route | `FrontpageRoute` ohne `NoAdminRequired`, `PublicPage`, `NoCSRFRequired`, `ExAppRequired`; `SecurityMiddleware` verlangt Admin plus CSRF | `php/lib/Controller/SettingsController.php:138,176,233,311`; `backend/tests/test_php_trust_boundary.py:82,177-186` |
| Registrierter Fremd-Container zu PHP-Route | ExApp-Klasse unveraendert: `ExAppRequired` plus `rejectForeignCaller()` als erste Anweisung | `backend/tests/test_php_trust_boundary.py:188-199` (gruen ueber alle vier Controller) |
| Nicht-Admin zu Container-Route | `access_level ADMIN` fuer `/status`, `/rates`, `/diagnose` | `backend/appinfo/info.xml:119,136,154` |
| Container-Antwort zu DOM | ausschliesslich `p()` im Template, ausschliesslich `textContent` im Skript | `backend/tests/test_admin_ui_contract.py:87-107`; `php/js/admin.js:238` |
| Admin-Eingabe zu Dateisystem | `..`-Segment abgelehnt statt gefiltert, Auflösung ueber `Folder::get()` | `php/lib/Service/PathResolverService.php:213-217,233` |

## Threat-Register: Verifikation je Disposition

### Plan 04-01: Gate B und Store-Pfad

| Threat ID | Kategorie | Disposition | Status | Beleg |
|-----------|-----------|-------------|--------|-------|
| T-04-01 | Elevation of Privilege | mitigate | CLOSED | `backend/tests/test_php_trust_boundary.py:82` (`FORBIDDEN_ON_ADMIN_ROUTE` = alle vier Attribute), `:177-186` Urteil je Admin-Route |
| T-04-02 | Elevation of Privilege | mitigate | CLOSED | `backend/tests/test_php_trust_boundary.py:188-199`; Gate gruen ueber acht ExApp-Routen |
| T-04-03 | Tampering | mitigate | CLOSED | Anti-Vakuum-Klausel `backend/tests/test_php_trust_boundary.py:226-243` (Gleichung ueber beide Attributnamen plus Untergrenze `>= 12`); zehn Selbsttests, davon sechs negativ, `:284-421` |
| T-04-04 | Repudiation | accept | CLOSED (akzeptiert) | Siehe Akzeptierte Risiken unten. CI-Assertion `.github/workflows/php.yml:136-151`, `<settings>`-Block `php/appinfo/info.xml:86` |
| T-04-05 | Tampering | mitigate | CLOSED | `.github/workflows/php.yml:33` `APPSTORE_SHA: 5c4373d7d026a8f7c7838cc9990fecaf19e8e682`, verwendet `:88`; kein `master` |
| T-04-SC | Tampering | mitigate | CLOSED | Kein Installationsschritt, kein Manifest-Diff im Phasenfenster |

### Plan 04-02: Statusroute

| Threat ID | Kategorie | Disposition | Status | Beleg |
|-----------|-----------|-------------|--------|-------|
| T-04-06 | Information Disclosure | mitigate | CLOSED | Feld fuer Feld, kein Row-Spread `backend/src/findling/api/status.py:157-189`; `FIELDS` um die sechs neuen Namen erweitert `backend/tests/test_status_endpoint.py:35-53`; Privacy-Test laeuft auch ueber die Schluessel von `reasons` `:66-81,179-194` |
| T-04-07 | Information Disclosure | mitigate | CLOSED | Nur der Typname: `backend/src/findling/store/repo.py:925` (`type(error).__name__`); `backend/src/findling/api/resources.py:150-152` statischer Satz ohne Pfad |
| T-04-08 | Denial of Service | mitigate | CLOSED | `backend/src/findling/store/schema.sql:72` `CREATE INDEX IF NOT EXISTS files_indexed_at` |
| T-04-09 | Denial of Service | mitigate | CLOSED | `backend/src/findling/api/status.py:233` `asyncio.to_thread(report)`; Ruhe-Intervall `php/js/admin.js:31` |
| T-04-10 | Spoofing | **transfer** | CLOSED | Transferziel belegt: `backend/appinfo/info.xml:119` `access_level ADMIN`; Docstring praezisiert die `exAppRequest`-Luecke und benennt die PHP-Route als wirksamen Schutz `backend/src/findling/api/status.py:40-48`; Route existiert und ist admin-only `php/lib/Controller/SettingsController.php:138` |
| T-04-SC | Tampering | mitigate | CLOSED | `backend/pyproject.toml` im Phasenfenster unveraendert |

### Plan 04-03: Admin-Seite

| Threat ID | Kategorie | Disposition | Status | Beleg |
|-----------|-----------|-------------|--------|-------|
| T-04-11 | Elevation of Privilege | mitigate | CLOSED | `php/lib/Controller/SettingsController.php:138` kein `NoAdminRequired`; Gate B prueft textuell |
| T-04-12 | Elevation of Privilege | mitigate | CLOSED | Kein `ExAppRequired` auf einer der vier Routen; `FrontpageRoute` statt `ApiRoute` `:138,176,233,311` |
| T-04-13 | Tampering | mitigate | CLOSED | Token je Aufruf frisch gelesen `php/js/admin.js:190,222`; Gate-Test auf Einruecken (also innerhalb einer Funktion) `backend/tests/test_admin_ui_contract.py:186-195` |
| T-04-14 | Tampering | mitigate | CLOSED | `backend/tests/test_admin_ui_contract.py:101-102` (`print_unescaped`), `:87-90` (`innerHTML`/`outerHTML`); `php/templates/admin.php` durchgaengig `p()`; `php/js/admin.js:238` `textContent` |
| T-04-15 | Denial of Service | mitigate | CLOSED | `php/lib/Service/ExAppService.php:82` `ADMIN_REQUEST_TIMEOUT_SECONDS = 2.0`, angewandt `:294`; `is_array($response)` vor allem anderen `:302,415` |
| T-04-16 | Denial of Service | mitigate | CLOSED | `php/js/admin.js:30-36` (`POLL_ACTIVE_MS 5000`, `POLL_IDLE_MS 30000`, `UNCHANGED_LIMIT 20`), `:1185-1188`, `:1197` visibilityState, `:1211` AbortController |
| T-04-17 | Information Disclosure | mitigate | CLOSED | Jede Logzeile ein statischer Satz plus Zaehler oder `['exception' => $e]`: `php/lib/Controller/SettingsController.php:143,180,196,239,263,329,371,392` |
| T-04-18 | Spoofing | mitigate | CLOSED | `php/templates/admin.php:27` `\OCP\Util::addScript`; Inline-Skript-Verbot `backend/tests/test_admin_ui_contract.py:106`; Initial State ueber `JSON.parse(atob(...))` statt Skript `php/js/admin.js:93-98` |
| T-04-SC | Tampering | mitigate | CLOSED | Kein `package.json`; MDI-Pfaddaten mit Commit belegt `THIRD-PARTY.md:154-163` |

### Plan 04-04: Deckungsgrad-Nenner

| Threat ID | Kategorie | Disposition | Status | Beleg |
|-----------|-----------|-------------|--------|-------|
| T-04-19 | Information Disclosure | mitigate | CLOSED | `php/lib/Migration/Version001000Date20260903000000.php:68-100`: nur `storage_id`, sieben Zaehler, zwei Zeitstempel. Kein Pfad, kein Name, kein Mimetype |
| T-04-20 | Repudiation | mitigate | CLOSED | Nenner ausgeschrieben `php/templates/admin.php:194`; `deliberatelyLeftOut` daneben `:199`; vorlaeufig mit Mount-Zahl `:203`; Felder `php/lib/Service/AdminViewService.php:1251-1260` |
| T-04-21 | Tampering | mitigate | CLOSED | `php/lib/BackgroundJobs/StorageCrawlJob.php:139-147` ruft `beginStorage` bei `last_file_id === 0`; `php/lib/Service/ScanStatsService.php:86,125` |
| T-04-22 | Denial of Service | mitigate | CLOSED | `add` je `TX_BAND` `php/lib/BackgroundJobs/StorageCrawlJob.php:260-265` und einmal am Ende `:287`; `insertIgnoreConflict` `php/lib/Service/ScanStatsService.php:199,241` |
| T-04-23 | Denial of Service | mitigate | CLOSED | `php/lib/Service/AdminViewService.php:1238-1245` `percent` bleibt null ohne Nenner; Empty-State statt `0 %` `php/js/admin.js:314-340` |
| T-04-SC | Tampering | mitigate | CLOSED | `php/composer.json` und `backend/pyproject.toml` unveraendert |

### Plan 04-05: Durchsatz und Schaetzung

| Threat ID | Kategorie | Disposition | Status | Beleg |
|-----------|-----------|-------------|--------|-------|
| T-04-24 | Information Disclosure | mitigate | CLOSED | Feld fuer Feld `backend/src/findling/api/rates.py:130-150`; `FIELDS` `backend/tests/test_rates_endpoint.py:35`; Schraegstrich- und Korpusnamen-Pruefung `:237-248` |
| T-04-25 | Denial of Service | mitigate | CLOSED | Index aus 04-02 `backend/src/findling/store/schema.sql:72`; Klemmung `backend/src/findling/api/rates.py:65-67,164` |
| T-04-26 | Tampering | mitigate | CLOSED | `int`-Signatur `backend/src/findling/api/rates.py:192` (Nicht-Zahl = 422, Test `:160-170`), Klemmung `:164`, `open_read_only` `:174`; Klemmtest `backend/tests/test_rates_endpoint.py:145-158` |
| T-04-27 | Repudiation | mitigate | CLOSED | Eigenes Feld `startupValues` `php/lib/Service/AdminViewService.php:1343,1358`; Beschriftung `php/templates/admin.php:348` |
| T-04-28 | Denial of Service | mitigate | CLOSED | `php/lib/Service/AdminViewService.php:1367-1369` `bytesExpected > diskFreeBytes - MIN_FREE_BYTES`; Konstante `:177` |
| T-04-29 | Elevation of Privilege | mitigate | CLOSED | `backend/appinfo/info.xml:136`; admin-only PHP-Route plus Gate B |
| T-04-SC | Tampering | mitigate | CLOSED | `rates.py` nutzt nur stdlib, FastAPI, pydantic |

### Plan 04-06: Fehlerliste

| Threat ID | Kategorie | Disposition | Status | Beleg |
|-----------|-----------|-------------|--------|-------|
| T-04-30 | Tampering | mitigate | CLOSED | `php/templates/admin.php:465-480` ausschliesslich `p()`; UI-Gate `backend/tests/test_admin_ui_contract.py:87-102` |
| T-04-31 | Information Disclosure | accept | CLOSED (akzeptiert) | Siehe Akzeptierte Risiken. Admin-only bestaetigt; Beispielzeile traegt Pfad, uid, shares, trashed und sonst nichts `php/lib/Service/AdminViewService.php:1150-1158`, kein Inhalt, kein Snippet |
| T-04-32 | Information Disclosure | mitigate | CLOSED | `php/lib/Service/PathResolverService.php:167,235,275,330,378` nur Zaehler und `['exception' => $e]`; `AdminViewService` hat keinen einzigen Logaufruf |
| T-04-33 | Information Disclosure | mitigate | CLOSED | `php/lib/Service/FileStateService.php:358-363` (`page()` lehnt Zustand und Grund ausserhalb der Listen ab und zaehlt), `:487` `reject()`; Label-Fallback in Klammern `php/lib/Service/AdminViewService.php:1178-1185` |
| T-04-34 | Denial of Service | mitigate | CLOSED | `MAX_PAGE = 50` `php/lib/Service/FileStateService.php:185,373`; `EXAMPLES_PER_GROUP = 20` `php/lib/Service/AdminViewService.php:276,1137`; Stapelabfrage `php/lib/Service/PathResolverService.php:372`; Index `php/lib/Migration/Version001000Date20260904000000.php:59` |
| T-04-35 | Repudiation | mitigate | CLOSED | `remaining` als eigenes Feld `php/lib/Service/AdminViewService.php:1082`; Ersatztext statt Verschwinden `php/templates/admin.php:470-478` |
| T-04-36 | Elevation of Privilege | accept | CLOSED (akzeptiert) | Siehe Akzeptierte Risiken. `php/lib/Service/PathResolverService.php:298` `getMountsForFileId`; kein `fopen`, kein `getContent`, kein `readStream` in der Datei |
| T-04-SC | Tampering | mitigate | CLOSED | Nur `OCP`-Klassen des Servers |

### Plan 04-07: Einzeldatei-Diagnose

| Threat ID | Kategorie | Disposition | Status | Beleg |
|-----------|-----------|-------------|--------|-------|
| T-04-37 | Tampering | mitigate | CLOSED | `php/lib/Service/PathResolverService.php:213-217` `..` abgelehnt, nicht gefiltert; Auflösung ueber `Folder::get()` `:233`; Container-Route nimmt nur `int` |
| T-04-38 | Information Disclosure | mitigate | CLOSED | `php/lib/Service/PathResolverService.php:226-239` faengt jede Ursache und antwortet identisch; `php/lib/Controller/SettingsController.php:179-186` statischer Satz, Wert nicht geloggt |
| T-04-39 | Information Disclosure | mitigate | CLOSED | `backend/src/findling/api/diagnose.py:65,122` `textChars` als Zahl; kein `fopen`, kein Stream; Grenze zu SRCH-02 im Docblock `:11-12` |
| T-04-40 | Information Disclosure | mitigate | CLOSED | `backend/tests/test_diagnose_endpoint.py:81-87` setzt Pfad und Titel, `:200-222` fordert deren Abwesenheit; `:279` prueft Feld-fuer-Feld-Aufbau |
| T-04-41 | Elevation of Privilege | mitigate | CLOSED | `php/lib/Controller/SettingsController.php:176` ohne Zugriffs-Attribut; Gate-B-Untergrenze steht bei 12, der Plan verlangte 10 `backend/tests/test_php_trust_boundary.py:243` |
| T-04-42 | Repudiation | mitigate | CLOSED | `php/lib/Service/AdminViewService.php:919-925` `backendReachable = false` plus Notiz statt "nicht indexiert" |
| T-04-43 | Repudiation | mitigate | CLOSED (mit Abweichung) | Grabstein wird erst nach bestaetigter Abwesenheit des Cache-Eintrags als Loeschung gelesen `php/lib/Service/AdminViewService.php:710-724`; Reihe faellt sonst durch `:929`. Abweichung: Die Vorrangregel wurde auf sechs Stufen umgezaehlt, die im Plan als "Stufe 2" beschriebene Pruefung ist implementiert als Stufe 1 und liegt damit weiterhin vor der Container-Stufe. Substanz vorhanden, Nummerierung im Register veraltet |
| T-04-44 | Denial of Service | mitigate | CLOSED | Eingabelaenge `php/lib/Controller/SettingsController.php:106,179`; Timeout `php/lib/Service/ExAppService.php:82`; eigener `AbortController` `php/js/admin.js:632`; `bruteforce_protection [401]` `backend/appinfo/info.xml:156` |
| T-04-SC | Tampering | mitigate | CLOSED | `diagnose.py` nutzt nur stdlib, FastAPI, pydantic |

### Plan 04-08: Regeln und Schalter

| Threat ID | Kategorie | Disposition | Status | Beleg |
|-----------|-----------|-------------|--------|-------|
| T-04-45 | Tampering | mitigate | CLOSED | Kein `NoCSRFRequired` auf `POST /admin/rules` `php/lib/Controller/SettingsController.php:311`; Token je Aufruf `php/js/admin.js:222`; Gate B `backend/tests/test_php_trust_boundary.py:82` |
| T-04-46 | Elevation of Privilege | mitigate | CLOSED | Kein `NoAdminRequired`, `FrontpageRoute` `php/lib/Controller/SettingsController.php:311` |
| T-04-47 | Tampering | mitigate | CLOSED | `php/lib/Service/ExclusionService.php:236` `..` abgelehnt; `files/`-Vorspann geschnitten `:756`; Laengen `:226,270`; Vergleich nur `str_starts_with` `:615` |
| T-04-48 | Denial of Service | mitigate | CLOSED | `MAX_PREFIXES = 64`, `MAX_PREFIX_LENGTH = 256` `php/lib/Service/ExclusionService.php:75-76`, durchgesetzt `:185,260,270` |
| T-04-49 | Tampering | mitigate | CLOSED | Ein Helfer `isExcluded` `php/lib/Service/ExclusionService.php:608`; Gate D `backend/tests/test_exclusion_path_space.py:208,214,220,230` gruen inklusive Selbsttests fuer selbstgebaute Vergleiche `:333-345` |
| T-04-50 | Repudiation | mitigate | CLOSED | Serverseitige Klemmung an den gemeldeten Container-Cap `php/lib/Service/SettingsService.php:302`, gespeichert `:169-180`; Hilfe nennt `FINDLING_MAX_FILE_BYTES` und den Neustart `php/templates/admin.php:681` |
| T-04-51 | Information Disclosure | mitigate | CLOSED | Abgelehnte Werte werden gezaehlt: `php/lib/Service/ExclusionService.php:768-771`, `php/lib/Service/SettingsService.php:315-318`, `php/lib/Service/ScanStatsService.php:358-361`, `php/lib/Service/FileStateService.php:489-492`. Keine Logzeile der neuen Dienste nennt einen Pfad |
| T-04-52 | Denial of Service | accept | CLOSED (akzeptiert) | Siehe Akzeptierte Risiken. Default aus `php/lib/Service/SettingsService.php:231`; Folge neben dem Schalter `php/templates/admin.php:693` |
| T-04-SC | Tampering | mitigate | CLOSED | `php/composer.json` unveraendert, kein `package.json` |

### Plan 04-09: Raeumung nach Ausschluss

| Threat ID | Kategorie | Disposition | Status | Beleg |
|-----------|-----------|-------------|--------|-------|
| T-04-53 | Tampering | mitigate | CLOSED | Gate A `backend/tests/test_readonly_gate.py` unveraendert und gruen; Bestaetigung sagt woertlich "The files themselves stay untouched on disk" `php/js/admin.js:907,910` |
| T-04-54 | Elevation of Privilege | mitigate | CLOSED | Einreihung PHP-seitig ueber `SubtreeExpandJob` `php/lib/Service/ExclusionService.php:496`; `test_write_allowlist_has_exactly_three_entries` `backend/tests/test_readonly_gate.py:545` gruen |
| T-04-55 | Repudiation | mitigate | CLOSED | `excluded` in allen drei Listen: `backend/src/findling/extract/errors.py:67`, `backend/src/findling/store/repo.py:127`, `php/lib/Service/FileStateService.php:107,154`; Vergleich in beiden Richtungen `backend/tests/test_extract_errors.py:121,164,183` |
| T-04-56 | Repudiation | mitigate | CLOSED (mit Abweichung) | Wie T-04-43: `php/lib/Service/AdminViewService.php:710-724,929`. Stufennummer im Register veraltet, Reihenfolge-Invariante erfuellt |
| T-04-57 | Denial of Service | mitigate | CLOSED | `PREVIEW_CAP` `php/lib/Service/ExclusionService.php:79-90`, durchgesetzt `:408-440`; `capped`-Signal `php/lib/Controller/SettingsController.php:256`; "at least" in der UI `php/js/admin.js:891-893` |
| T-04-58 | Denial of Service | mitigate | CLOSED | Ein Job je Praefix und Mount mit `IJobList::add`-Deduplikation `php/lib/Service/ExclusionService.php:493-496`; Baender 250, Deckel 30 s, Abstand 5 s, eigener Nachfolger `php/lib/BackgroundJobs/SubtreeExpandJob.php:49,57,64,72,204` |
| T-04-59 | Tampering | mitigate | CLOSED | Inline-Bestaetigung mit Pfad und Dokumentzahl `php/js/admin.js:864-912`; Fokus auf der harmlosen Wahl `:922-924`; `Escape` verwirft `:1138-1140`; reine Toggle- oder Cap-Aenderungen loesen nichts aus `:997` |
| T-04-60 | Information Disclosure | mitigate | CLOSED | `scheduleCleanup` zaehlt `planned`/`unresolved` `php/lib/Service/ExclusionService.php:508-511`; `SubtreeExpandJob` nennt nur Storage-Id, Ancestor und Zaehler `php/lib/BackgroundJobs/SubtreeExpandJob.php:116-119` |
| T-04-SC | Tampering | mitigate | CLOSED | Alle drei Reason-Listen sind Quelldateien des Repos |

### Plan 04-10: occ-Kommando und Abnahme

| Threat ID | Kategorie | Disposition | Status | Beleg |
|-----------|-----------|-------------|--------|-------|
| T-04-61 | Elevation of Privilege | accept | CLOSED (akzeptiert) | Siehe Akzeptierte Risiken. Rationale gegen die Realitaet geprueft: `php/lib/Command/DiagnoseCommand.php:138-165` gibt Verdikt, Grundcode, Label, Abhilfe, fileId, Pfad, Besitzer, Papierkorb, Freigabezahl, Zeitstempel und Notiz aus. Kein Dateiinhalt, kein Snippet, kein `fopen` |
| T-04-62 | Tampering | mitigate | CLOSED | Dieselbe Auflösung wie die Route: `php/lib/Command/DiagnoseCommand.php:107` ruft `AdminViewService::diagnose()`, das ueber `PathResolverService::resolveReference` `:101` und die `..`-Ablehnung `:213` geht; abgelehnter Wert erscheint in keiner Zeile `php/lib/Command/DiagnoseCommand.php:97-104`, die Datei hat keinen Logaufruf |
| T-04-63 | Repudiation | mitigate | CLOSED | `php/lib/Command/DiagnoseCommand.php:107` delegiert; im ganzen Kommando steht kein Zustandsname als Code, nur zwei Erwaehnungen in Kommentaren `:34,170` |
| T-04-64 | Tampering | mitigate | CLOSED | Messung am 03.09. nachgeholt, siehe "Nachgeholter Nachweis T-04-64" unten |
| T-04-65 | Information Disclosure | accept | CLOSED (akzeptiert) | Siehe Akzeptierte Risiken. Rationale geprueft: Pfad und Besitzer werden bewusst gedruckt `php/lib/Command/DiagnoseCommand.php:148-149`; die Datei enthaelt keinen Logger und keine Container-Antwort |
| T-04-SC | Tampering | mitigate | CLOSED | Manifeste unveraendert, kein `package.json` |

## Nachgeholter Nachweis T-04-64

**Messung vom 03.09.2026 (nach dem Audit, vor diesem Verschluss):** Der
Pruefsummenvergleich ueber das Referenzkorpus der Dev-Instanz
(`findling-nextcloud`, dieselbe Instanz, auf der die Raeumung der Sichtprobe 7
live lief) wurde nachgeholt. Der Vergleichsmassstab ist der deterministische
Korpus-Build (`scripts/dev/build_corpus.py`, "the build is deterministic ...
same checksums"), also der unveraenderte Urzustand jeder Korpusdatei, ein
strengerer Massstab als ein Schnappschuss vor dem Durchlauf.

| Messung | Ergebnis |
|---------|----------|
| sha256 aller 16 korpus-staemmigen Dateien der Instanz (12 unter `testuser/files/corpus/`, 4 lose: 13, 15, 17, 22) gegen `testdata/corpus/` | 16 geprueft, **0 Abweichungen** |
| `find data/{admin,kollegin,testuser}/files -type f -newermt "2026-09-03 02:30"` (Sichtprobe lief 02:30-03:12, Raeumung 02:51) | **kein Treffer**: keine Nutzerdatei irgendeines Accounts wurde waehrend oder nach dem Durchlauf veraendert |

Damit ist die vom Register verlangte Messung am Referenzkorpus nach dem realen
Raeumungslauf erbracht: nicht ein Byte einer Nutzerdatei hat sich bewegt, und
der Abgleich lief gegen Pruefsummen, nicht gegen Augenmass. Ergaenzend haelt
04-VERIFICATION.md den Nachtrag fest.

## Audit-Historie

| Datum | Ereignis | Threats gefunden | Closed | Open |
|-------|----------|------------------|--------|------|
| 2026-09-03 | Erstaudit (gsd-security-auditor) | 65 | 64 | 1 (T-04-64) |
| 2026-09-03 | Nachweis T-04-64 nachgeholt (Pruefsummenvergleich Dev-Instanz) | 65 | 65 | 0 |

## Urspruenglicher Befund T-04-64 (historisch, geschlossen)

### T-04-64, Tampering, mitigate, war BLOCKER

**Deklarierte Minderung (04-10-PLAN.md:369):** "Die Sichtprobe schliesst mit
dem bestehenden Pruefsummen-Gate ueber das Referenzkorpus (IDX-07, Gate A),
nicht mit Augenmass." Als Akzeptanzkriterium ausformuliert in 04-10-PLAN.md:335
und :344: das Gate ist nach dem ganzen Durchlauf gruen, **insbesondere nach der
Raeumung durch einen Ausschluss**.

**Befund:** Der Nachweis fehlt. Die Ausfuehrung protokolliert das selbst:

> 04-10-SUMMARY.md:275: "**The checksum gate over the reference corpus was not
> run as the closing step of the walkthrough.** ... The corpus level checksum
> comparison after the live clearing is outstanding and belongs to the phase
> verification that runs next."

Die anschliessende Phasenverifikation hat es nicht nachgeholt: 04-VERIFICATION.md
enthaelt keinen Treffer auf Pruefsumme, Checksum, IDX-07 oder Nur-Lesen. Die
Sichtprobe 7 des Walkthroughs hat die Raeumung dabei tatsaechlich live ausgeloest
(`SubtreeExpandJob` raeumte zwei Dokumente, Nenner sank von 168 auf 166), also
genau der Zustand, nach dem das Gate laut Plan laufen sollte.

**Was stattdessen vorliegt (Kompensation, kein Ersatz):**
- Gate A `backend/tests/test_readonly_gate.py` als Quellcode-Gate gruen
- `test_write_allowlist_has_exactly_three_entries` `:545` gruen, die Schreib-Allowlist steht unveraendert bei drei Eintraegen
- Byte-Vergleiche vor und nach einem Lesezugriff in `test_diagnose_endpoint.py:289-299`, `test_index_status.py:137-141`, `test_ocr.py:215-223`
- Kein Codepfad dieser Phase schreibt in eine Nutzerdatei

Diese Belege stuetzen die Behauptung auf Quell- und Testebene. Sie ersetzen den
deklarierten Nachweis nicht: das Register verlangt eine Messung am Referenzkorpus
nach dem realen Raeumungslauf, und genau diese Messung existiert nicht.

**Aufloesung:** Option 1 wurde am 03.09.2026 ausgefuehrt (siehe "Nachgeholter
Nachweis T-04-64" oben): Pruefsummenvergleich gegen den deterministischen
Korpus-Build, 16/16 identisch, plus mtime-Beweis ueber alle drei Accounts.
Ergebnis in 04-VERIFICATION.md notiert. T-04-64 ist CLOSED.

## Akzeptierte Risiken

| Threat ID | Kategorie | Risiko | Begruendung, gegen die Realitaet geprueft | Beleg |
|-----------|-----------|--------|--------------------------------------------|-------|
| T-04-04 | Repudiation | `pre-info.xslt` leert den `<settings>`-Block im Store-Tarball | Folgenlos, weil Nextcloud den Block zur Laufzeit aus dem installierten `info.xml` liest. Die Annahme ist brechbar gemacht: der CI-Schritt "State the settings finding explicitly" unterscheidet die drei moeglichen Ausgaenge und meldet jede Aenderung | `.github/workflows/php.yml:136-151`; `php/appinfo/info.xml:86` |
| T-04-31 | Information Disclosure | Dateinamen ueber die Fehlerliste | Geprueft und zutreffend: die Seite ist admin-only (alle vier Routen `FrontpageRoute` ohne Zugriffs-Attribut, Gate B), und die Beispielzeile traegt Pfad, uid, Freigabezahl und Papierkorb-Flag, aber keinen Inhalt und kein Snippet. Ein Admin kann jede Datei ueber die Files-App ohnehin benennen; die Grenze zu SRCH-02 bleibt | `php/lib/Service/AdminViewService.php:1150-1158`; `php/lib/Controller/SettingsController.php:138` |
| T-04-36 | Elevation of Privilege | Pfad-Auflösung umgeht das Berechtigungsmodell | Geprueft und zutreffend: `getMountsForFileId` prueft bewusst keine Rechte, weil der Admin einen Pfad benennen darf. Die Datei enthaelt kein `fopen`, kein `getContent` und kein `readStream`, es wird kein Node geoeffnet und kein Inhalt geliefert | `php/lib/Service/PathResolverService.php:298`; Negativbefund ueber die ganze Datei |
| T-04-52 | Denial of Service | External Storage zieht ein Terabyte durch HTTP | Geprueft und zutreffend: ausdrueckliche Admin-Entscheidung, Default aus, Folge steht neben dem Schalter ("External storage can be slow or charged per request. Indexing reads every file once."), und die Schaetzung aus 04-05 zeigt den Aufwand vorher | `php/lib/Service/SettingsService.php:231`; `php/templates/admin.php:693` |
| T-04-61 | Elevation of Privilege | `occ findling:diagnose` kennt keine Sitzung und kein CSRF | Geprueft und zutreffend: occ setzt eine Shell auf der Maschine voraus, wer die hat, liest ohnehin jede Datei. Die Kommandoausgabe wurde Feld fuer Feld geprueft und liefert nur Metadaten und Verdikte, keinen Dateiinhalt und kein Snippet | `php/lib/Command/DiagnoseCommand.php:138-165` |
| T-04-65 | Information Disclosure | Ein Dateiname in der Kommandoausgabe | Geprueft und zutreffend: Pfad und Besitzer werden bewusst gedruckt, die Ausgabe ist fuer einen Admin auf der Maschine gedacht. Sie geht in kein Log der App (die Datei enthaelt keinen Logger) und in keine Container-Antwort | `php/lib/Command/DiagnoseCommand.php:148-149` |

## Threat Flags aus den Summaries

| Flag | Datei | Urteil |
|------|-------|--------|
| `information_disclosure`, aus 04-09-SUMMARY.md: die Vorschau-Antwort traegt die normalisierten neuen Praefixe zurueck | `php/lib/Controller/SettingsController.php:253-257` | **Informational, auf bestehende Threat-IDs abgebildet, kein unregistrierter Flag.** Der Wert stammt aus derselben Anfrage derselben Admin-Sitzung, enthaelt keine Daten, die der Anfragende nicht selbst geschickt hat, und ist zuvor durch `ExclusionService::validate` gegangen (`..` abgelehnt, T-04-47). Die Route ist admin-only plus CSRF (T-04-45, T-04-46). Der Rueckweg endet in einem Textknoten (T-04-14, Gate C verbietet `innerHTML`), und die Einsetzung nutzt Funktionsersetzungen, damit ein Ordner namens `Archiv$&2024` nicht verstuemmelt in der destruktiven Bestaetigung landet (`php/js/admin.js:899-911`, Review-Befund WR-04). Er erreicht kein Log (T-04-51, `php/lib/Controller/SettingsController.php:239-241` zaehlt nur). Keine neue Vertrauensgrenze |
| 04-05, 04-07, 04-10: ausdruecklich "keine neue Oberflaeche" | - | Stichprobe bestaetigt: `php/appinfo/routes.php` ist leer, jede Route traegt ein Attribut, Gate B zaehlt zwoelf und urteilt ueber alle zwoelf |

**Unregistrierte Flags: keine.**

## Was dieser Audit nicht behauptet

- Er sucht nicht nach neuen Schwachstellen. Das Register ist zum Planzeitpunkt
  autorisiert worden, dieser Lauf prueft nur seine Dispositionen. Der
  Pentest-Charakter des Phase-2-Audits (`02-AUDIT-SECURITY.md`) ist hier
  ausdruecklich nicht wiederholt worden.
- Er sagt nichts ueber die PHP-Laufzeit. Es gibt keine PHP-Testumgebung im Repo;
  die PHP-Seite ist textuell (Gates B, C, D) und mit `php -l` im Container
  geprueft, und die Belege oben sind Quellzeilen, keine Laufzeitmessungen.
- Er ersetzt die zwei zurueckgestellten Punkte aus 04-VERIFICATION.md nicht
  (DI-04-03, DI-04-04). Beide sind keine Sicherheitsbefunde.
