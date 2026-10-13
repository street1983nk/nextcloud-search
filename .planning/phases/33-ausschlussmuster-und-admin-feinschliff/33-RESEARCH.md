# Phase 33: Ausschlussmuster und Admin-Feinschliff - Research

**Researched:** 2026-10-13
**Domain:** PHP-Companion (ExclusionService, Admin-Seite, Kataloge), Abgleich im Container (Python), Statusantwort
**Confidence:** HIGH für Bestand und Codepfade (alles per Datei:Zeile belegt), MEDIUM für die vorgeschlagenen Grenzwerte (gemessen an einem Prototyp, nicht am echten Code)

<user_constraints>
## User Constraints (aus 30-CONTEXT.md)

Für Phase 33 gibt es keine eigene CONTEXT.md. Bindend ist der Owner-Entscheid aus Phase 30, wörtlich:

### Locked Decisions

- **D-30-01 Ausschlussmuster-Syntax (EXCL, Phase 33):** Einfache Platzhalter, nur `*` und `?` (fnmatch-artig, kein `**`, keine Negation, keine Regex). Beispiele `*.photoslibrary`, `*/node_modules/*`. Bestehende Praefix-Ausschluesse bleiben gueltig.
- **D-30-08 Schema-Einmaligkeit:** Phase 30 ist der einzige Schemaschritt (SCHEMA_VERSION 2 -> 3, LEGACY_SCHEMA_STEPS ("2","3"),("1","3")). [...] spätere v1.5-Phasen ändern weder Schema noch Indexmarken (ROADMAP Phase 30, Kriterium 4).

### Claude's Discretion (vom Auftraggeber benannt)

- Grenzen für Musterzahl und Musterlänge: offen gelassen, begründete Werte vorschlagen; der Planer markiert sie als Planer-Entscheidung.

### Deferred Ideas (OUT OF SCOPE)

- Grenzwerte in der UI editierbar (REQUIREMENTS.md:79, "Werte sind Deploy-Optionen; erst Anzeige (POL-01)").
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXCL-01 | Admin pflegt Ausschlussmuster mit Platzhaltern auf der Admin-Seite; bestehende Präfix-Ausschlüsse bleiben gültig | Abschnitte "Bestand der Präfix-Ausschlüsse", "Muster-Semantik", "Speicherort", Muster 1 und 2 |
| EXCL-02 | Mac-Bundles mit einer Regel komplett ausschließen; bereits indexierte Treffer verschwinden | Befund B1 (Abgleich lässt bekannte Dateien liegen), Muster 3 (Räumweg A und C) |
| EXCL-03 | Ausgeschlossene Dateien zählen als "excluded", nicht als Fehler; Musterzahl und -länge begrenzt, kein ReDoS, keine Regex | Befund B2 (Fehlerliste behält alte Urteile), Matcher-Messung, Grenzwert-Vorschlag |
| POL-01 | Zellgrenze, Adressraum, Größengrenze, OCR-Seitendeckel nur lesend mit Änderungshinweis (#21) | Abschnitt "Grenzwerte für #21", Befund B3 (falscher AppAPI-Satz) |
| POL-03 | Hardware-Hinweis "This box has fewer cores..." in allen Katalogen verständlich umformuliert | Abschnitt "Hardware-Hinweis" mit Fundstellen, Gates und Formulierungsvorschlag |
</phase_requirements>

## Project Constraints (aus CLAUDE.md)

- Code Englisch; Prosa der Doku dreisprachig (README de/en/fr), Projektkommunikation Deutsch; keine Em-Dashes; echte Umlaute nur in deutscher Prosa, nie in Code, URLs, YAML.
- Qualitätsgates lokal grün vor Commit: ruff-Vollregelsatz, pyright basic, vulture, CI-Gates.
- Security/Privacy: Berechtigungs-Durchgriff strikt, keine Inhalte verlassen den Server, kein Telemetrie-Phoning. Für diese Phase heißt das: keine Pfade, Muster oder Ordnernamen in Logs oder Antworten (bestehende Regel T-04-51/T-04-60, `ExclusionService.php:59-62`).
- Kurze Produkttexte; Store-Text-Entwurf vor Release dem Owner zeigen (REL-05).
- Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Phasenabschluss fixen.
- Owner-Regeln aus dem Gedächtnis des Auftraggebers: Commits nur als street1983nk ohne Claude-Trailer; UI-Abnahmen gemeinsam per Playwright; nicht vermuten, sondern mit Positivkontrolle belegen; Produkt-Fix vor Harness-Patch.

## Summary

Die Ausschlussregeln leben komplett auf der PHP-Seite in `ExclusionService` und werden an fünf Stellen über einen einzigen Helfer `isExcluded()` auf einem einzigen Pfadraum (`mountRelativePath()`) gefragt: Crawl, Ereignis-Listener, `describe()` beim Abholen, Abgleichs-Slice und Diagnose. Ein Textgate (`backend/tests/test_exclusion_path_space.py`) hält das fest. Muster passen sauber in diese Architektur: Wenn `isExcluded()` Präfixe UND Muster prüft, wirken Muster automatisch an allen fünf Stellen, im Zähler "Excluded by a rule" und in der Diagnose. Der Container kennt keine Regeln und soll auch keine kennen (D-06, `reconcile.py:110-111`).

Drei Befunde ändern den Zuschnitt gegenüber der naiven Lesart. **B1:** Das Räumen bereits indexierter Dateien hängt heute allein am Speichern eines Präfixes (SubtreeExpandJob je aufgelöstem Ordner). Der Abgleich, den der Docblock von `scheduleCleanup()` als "Netz" beschreibt, lässt seit dem Owner-Entscheid vom 03.10.2026 eine bekannte, unveränderte Datei unter einer Regel liegen (`reconcile.py:614-620`). Ein Muster wie `*.key` lässt sich nicht in Ordner-IDs auflösen, also braucht EXCL-02 einen eigenen Räumweg. **B2:** Die Kacheln "Skipped" und "Failed" und die Fehlerliste lesen `findling_file_state`; Urteilszeilen von Dateien, die erst später ausgeschlossen werden, bleiben dort stehen (Löschweg über `KIND_DELETE` widerruft nichts, `QueueService.php:103-106`, `581-608`). Genau das ist der Schmerz aus Issue #22 (266k Skip-Einträge aus Keynote-Bundles). **B3:** Der vorhandene Hinweis unter "Largest file to read" sagt, man ändere `FINDLING_MAX_FILE_BYTES` "in the app settings of AppAPI, which restarts the container" (`admin.php:1291`); AppAPI 34.0.0 hat dafür keinen Weg, Deploy-Optionen werden nur beim Deploy gesetzt und danach nur gelesen.

Für die Mustersprache empfehle ich einen eigenen, bitparallelen Matcher (Shift-And mit Stern-Selbstschleifen) statt `fnmatch()`, `preg_match()` oder `fnmatch.translate`-artiger Übersetzung: garantiert linear in der Pfadlänge, ohne Regex, gemessen im Prototyp mit 8,4 ms im schlechtesten Fall (32 Muster, 4000-Zeichen-Pfad) und 22 bis 180 µs typisch. Muster speichern in einem neuen appconfig-Schlüssel neben `exclusions`; damit bleibt jeder gespeicherte Präfix aus 1.4.2 byte-gleich und wird nie als Muster gelesen. Keine Schema- oder Markenänderung nötig.

**Primary recommendation:** Muster als zweite Liste in `ExclusionService` (neuer Schlüssel `exclusion_patterns`, eigener Matcher, `isExcluded()` prüft beides), Räumen über einen neuen PHP-Kehrjob beim Speichern plus eine kleine Abgleichs-Änderung im Container als Netz, Urteilszeilen ausgeschlossener Dateien beim Räumen mitlöschen; Grenzwerte über zwei neue Felder der Statusantwort lesend anzeigen, den falschen AppAPI-Satz dabei ersetzen.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Muster speichern, prüfen, normalisieren | API/Backend (PHP-Companion, appconfig) | Browser (Formular) | Regeln gehören nur der PHP-Seite (D-06, `reconcile.py:110-111`) |
| Muster gegen Pfad prüfen | API/Backend (PHP, `ExclusionService::isExcluded`) | , | Ein Helfer, ein Pfadraum (Gate D) |
| Neue Dateien unter Regel nicht einreihen | API/Backend (Crawl, Listener) | , | bestehende Aufrufstellen |
| Bereits indexierte Dokumente räumen | API/Backend (PHP-Hintergrundjob) | Container (Abgleich, `_forget`) | PHP kennt die Regel, der Container löscht |
| Zähler "excluded" | Database/Storage (`findling_scan_stats`) | PHP (Crawl/Recount) | `StorageCrawlJob.php:160`, `531` |
| Diagnose "excluded" | API/Backend (AdminViewService Stufe 2) | , | live berechnet, nie gespeichert |
| Grenzwerte lesen | Container (`config.py`, Statusantwort) | PHP (AdminViewService) | Werte sind Container-Umgebung |
| Grenzwerte anzeigen | Browser/Template (admin.php, admin.js) | , | nur lesend |

## Bestand der Präfix-Ausschlüsse (Frage 1)

| Aspekt | Befund | Beleg |
|---|---|---|
| Speicherort | appconfig, App `findling`, Schlüssel `exclusions`, Typ Array (`getValueArray`/`setValueArray`) | `SettingsService.php:57`; `ExclusionService.php:173`, `377` |
| Werte auf der Dev-Instanz | `["Archiv"]` | `occ config:app:get findling exclusions` auf `findling-nextcloud` am 13.10.2026 |
| Grenzen | 64 Einträge, 256 Bytes je Eintrag | `ExclusionService.php:75-76` |
| Normalisierung | trim, doppelte `/` falten, äußere `/` weg, `files/`-Vorspann weg, `.`/`..`-Segmente abgelehnt, kein NFC | `ExclusionService.php:261-279`, `770-794` |
| Fehlercodes | `empty`, `too_long`, `traversal`, `duplicate`, `too_many` | `ExclusionService.php:110-115` |
| Zweiter Schreiber | `occ config:app:set` umgeht `save()`, deshalb defensives Lesen mit Deckel und Warnung | `ExclusionService.php:150-228` |
| Vergleich | `$path === $prefix` oder `str_starts_with($path, $prefix . '/')`, Groß/Klein unterschieden | `ExclusionService.php:645-658` |
| Pfadraum | relativ zur Mount-Wurzel; im Home relativ zu `files/`, in Team Folder/External relativ zur Mount-Wurzel | `ExclusionService.php:24-34`, `684-698` |
| Pflege auf der Seite | Block "Rules and limits", Liste "Excluded folders", Hilfe "Prefix match ..., no wildcards and no patterns" | `admin.php:1245-1282` |
| Speichern | `POST /admin/rules` (`saveRules`), Vorschau `previewRules` mit Zahl betroffener Dokumente (Deckel 5000) | `SettingsController.php:234-265`, `312-405`; `ExclusionService.php:93`, `445-479` |
| Bestätigung | Inline-Satz "Remove indexed content? Excluding %1$s also removes %2$s ..." vor dem Speichern | `admin.js:1061-1124`; `admin.php:1340-1348` |
| Fehlermeldungen | Server antwortet mit Codes, die Seite zeigt nur "The rules were not saved. Nothing changed."; Client prüft lokal nur leer/doppelt | `SettingsController.php:336-344`; `admin.js:980-988`, `1225-1229` |

**Prüfstellen (alle über `isExcluded(mountRelativePath(...))`):**

| Stelle | Wirkung | Beleg |
|---|---|---|
| Crawl `StorageCrawlJob::verdict()` | ausgeschlossen vor Größengrenze; gezählt in `excluded`, keine Queue-Zeile, keine Urteilszeile | `StorageCrawlJob.php:482-490`, `309-319`, `511-512` |
| Recount (Zählmodus des Crawls) | dieselbe `verdict()` | `StorageCrawlJob.php:300-305`; `ScanRecountJob.php:117` |
| Ereignis-Listener | nicht einreihen; Löschungen laufen absichtlich durch; Guard `prefixes() !== []` | `FileEventListener.php:441-454` |
| `QueueService::describe()` | Abholung einer Zeile unter Regel wird Löschauftrag | `QueueService.php:886-898` |
| Abgleichs-Slice | Zeile wird live als `skipped(excluded)` markiert, nie gefiltert (sonst falsches `final`); Guard `prefixes() === []` | `ReconcileController.php:189`, `251-258`, `275-284`; `StorageService.php:413-455` |
| Diagnose (Seite und `occ findling:diagnose`) | Stufe 2 meldet `skipped(excluded)` vor jedem gespeicherten Urteil | `AdminViewService.php:1236-1285`, `1316-1318` |

**Räumen beim Hinzufügen (Weg A):** `save()` ermittelt neue Präfixe (`newPrefixes`, verschachtelte zusammengefasst) und plant je Mount, in dem der Präfix zu einem Ordner auflöst, einen `SubtreeExpandJob` mit `kind delete` (`ExclusionService.php:360-382`, `518-552`, `565-592`). Der Poller macht daraus `_forget`: Dokument raus, ACL raus, Grabstein (`poller.py:1845-1872`).

**Befund B1 (Weg B ist kein Netz mehr):** Der Docblock nennt den Abgleich als Netz ("Those files drop out of the enumeration", `ExclusionService.php:493-500`). Das stimmt seit dem Owner-Entscheid vom 03.10.2026 nicht mehr: Ausgeschlossene Zeilen bleiben im Slice und tragen `skipped(excluded)`. Im Container gilt `if stored == row.etag: continue` VOR der Ausschlussprüfung (`reconcile.py:614-620`), also bleibt eine bekannte, unveränderte Datei unter einer Regel im Index. Nur eine geänderte Datei (andere etag) wird Arbeit und über `describe()` gelöscht (`test_reconcile.py:376-387`). Folge: Was Weg A verfehlt (Ordner, der beim Speichern nicht auflöste; Ordner, der später per Umbenennen INNERHALB eines Mounts unter eine Regel rutscht, `FileEventListener.php:217-230` setzt dann nur `markScanStale`), bleibt dauerhaft im Index. Das betrifft auch die Präfixe von heute.

**Befund B2 (alte Urteile bleiben in der Fehlerliste):** Die Kacheln "Skipped"/"Failed" kommen aus `FileStateService::counts()` (`AdminViewService.php:696-698`), die Fehlerliste aus derselben Tabelle. Ein Löschauftrag aus `SubtreeExpandJob` ist `KIND_DELETE`; `revocableFileIds()` widerruft nur bei `content`/`ocr` (`QueueService.php:103-106`, `581-608`). Eine Datei, die vor dem Ausschluss als `skipped(image_not_ocrable)` gezählt wurde, bleibt danach dort gezählt. Die Diagnose zeigt sie zwar als "excluded" (Stufe 2 vor Stufe 4), die Kacheln und die Liste aber nicht. Für #22 (266k Thumbnails, `gh issue view 22`) wäre der Ausschluss ohne diese Bereinigung wirkungslos für den eigentlichen Schmerz.

## Der Zähler "excluded" (Frage 2)

- Gibt es schon: Spalte `excluded` in `findling_scan_stats` (`Version001000Date20260903000000.php:89`), gezählt vom Crawl und vom Recount (`StorageCrawlJob.php:160`, `511-512`, `531`), Kachel "Excluded by a rule" (`admin.php:303`, `AdminViewService.php:713`), abgezogen vom Nenner der Abdeckung (`AdminViewService.php:640-645`).
- Präfix-Ausschlüsse zählen heute genau dort: jede vom Crawl gesehene Datei unter einer Regel +1, keine Zeile in `findling_file_state` (`StorageCrawlJob.php:309-319`).
- Nach dem Speichern der Regeln wird der Scan als veraltet markiert, damit der Recount neu misst (`SettingsService.php:707-711`).
- Reason-Code `excluded` existiert auf beiden Seiten (`FileStateService.php:114`, `166`; `backend/src/findling/extract/errors.py:110`, `145`), wird nie geschrieben, nur live vergeben. Keine neue Generation der Urteile nötig.
- Konsequenz: Muster, die über `isExcluded()` laufen, zählen automatisch richtig. Offen ist nur B2.

## Muster-Semantik (Frage 3)

Alle Punkte unten sind Empfehlungen für den Planer, begründet am Bestand.

| Frage | Empfehlung | Begründung |
|---|---|---|
| Pfadraum | derselbe wie Präfixe: `mountRelativePath()` | Gate D verlangt einen Pfadraum; Team Folder (#22-Pfad `AG_Beteiligungen/...`) wird relativ zur Mount-Wurzel geprüft |
| `*` über `/` | ja, `*` passt auf beliebig viele Zeichen inklusive `/` | Sonst bräuchte `*.photoslibrary` in Unterordnern `**`, das D-30-01 verbietet; entspricht Pythons `fnmatch` [CITED: docs.python.org/3/library/fnmatch.html] |
| `?` | genau ein Zeichen, aber nicht `/` (Planer-Entscheidung) | Hält die Wirkung eines `?` im Namen; verhindert, dass `?Backups` über den gedachten führenden `/` greift (siehe unten). fnmatch lässt `?` auch `/` treffen, "fnmatch-artig" deckt beide Lesarten |
| Zeichen statt Bytes | `?` = ein Unicode-Zeichen (`mb_str_split`) | `Caf?` muss `Café` treffen; im Prototyp belegt |
| Ordner gegen Datei | Muster trifft, wenn es auf den Pfad SELBST oder auf einen seiner Vorfahren (an einer `/`-Grenze) passt | Bundle ist ein Ordner; dieselbe Semantik wie Präfix (`Archiv` trifft `Archiv` und `Archiv/...`) |
| Oberste Ebene bei `*/name/*` | Prüfung gegen `/` + Pfad UND gegen den Pfad | Sonst verfehlt `*/node_modules/*` ein `node_modules` direkt im Home; mit führendem `/` passt `*` auf leer. Ein Muster ohne führenden Stern bleibt am Mount-Anfang verankert (`Backups/*` trifft nicht `Archiv/Backups/x`) |
| Groß/Klein | unterschieden, wie Präfixe | ein Vergleichsverhalten für beide Listen; Apple-Bundle-Endungen sind klein geschrieben [ASSUMED]; Grenze auf Speichern ohne Unterscheidung bleibt L-32-04 (Phase 36) |
| NFC | Muster beim Speichern nach NFC komponieren (`\Normalizer::FORM_C`, Rückfall wie `Provider::composed`) | Dateicache speichert NFC (`Provider.php:415-424`, Befund M-32-01); macOS-Clients tippen NFD |
| Präfix-Normalisierung | NICHT ändern | Erfolgskriterium 1: Präfixe wirken unverändert; NFC für Präfixe wäre eine Verhaltensänderung |

**Matcher ohne Regex (ReDoS):** Nicht `fnmatch()` (glibc-Implementierung rekursiv je `*`, kennt `[...]` und `\`), nicht `preg_match()` mit übersetztem Muster (Gate D führt beide als verbotene Vergleiche an Aufrufstellen, `test_exclusion_path_space.py:119-126`; und eine Übersetzung à la `fnmatch.translate` erzeugt Regex). Empfehlung: Shift-And mit Stern-Selbstschleifen:

- Kompilieren einmal je Muster und Request (im `cached`-Feld neben den Präfixen): je Nicht-Stern-Symbol ein Bit (Bit 0 = leerer Präfix), Maske je Zeichen, Maske für `?`, Stern-Maske (Bit j, wenn nach j Symbolen ein Stern steht), Annahme-Bit k.
- Schritt je Zeichen c: `D = ((D << 1) & (B[c] | Q)) | (D & STAR)`; nach dem ersten Zeichen (`/`) zusätzlich `D |= 1` (zweiter Start ohne führenden `/`); an jeder `/`-Grenze und am Ende Annahme prüfen (Vorfahren-Semantik); `D === 0` bricht ab.
- Grenze aus der Technik: höchstens 62 Nicht-Stern-Symbole je Muster (PHP-int 64 Bit, Vorzeichenbit frei).
- Laufzeit O(Pfadlänge) je Muster, unabhängig von der Musterform.

**Messung am Prototyp** (`php:8.3-cli` in Docker, 13.10.2026, Skript im Scratchpad, nicht im Repo): 13 Korrektheitsfälle grün (`*.photoslibrary` in Unterordnern, nicht `.photoslibrary.txt`; `*/node_modules/*` oben und tief, nicht `my_node_modules`; `*.key` für den #22-Pfad; `Backups/*` verankert; `Caf?` trifft `Café`). Laufzeiten:

| Fall | bitparallel | gieriger Segment-Matcher (Vergleich) |
|---|---|---|
| 32 Muster, Pfad 3996 Zeichen, `*?`-lastig | 8,4 ms | 17,5 ms bis 708 ms (`?`-Segmente sind O(n·m)) |
| 64 Muster, sonst gleich | 17,2 ms | 32,4 ms |
| 32 Muster, Pfad 75 Zeichen, realistisch | 180 µs je Datei | 35 µs |
| 4 Muster, Pfad 75 Zeichen | 22 µs je Datei | , |

Der gierige Matcher ist typisch schneller, aber nicht beschränkt; der bitparallele ist beschränkt. Der Pfad wird vom Nutzer bestimmt (Dateicache-Pfad bis 4000 Zeichen), die Muster vom Admin. Optimierung für den Planer: `mb_str_split` des Pfades einmal je Datei, nicht je Muster (im Prototyp je Muster).

**Vorgeschlagene Grenzwerte (Planer-Entscheidung):**

| Grenze | Wert | Begründung |
|---|---|---|
| Musterzahl | 32 | schlimmster Fall 8,4 ms je Schreibvorgang (Listener läuft in jedem Write der Instanz, `FileEventListener.php:430-434`); 64 verdoppelt das. Bundle-Typen und Build-Ordner sind eine Handvoll |
| Musterlänge | 60 Zeichen (`mb_strlen`), zusätzlich höchstens 62 Nicht-Stern-Symbole technisch | darunter bleibt jedes realistische Muster (`*.photoslibrary` 15, `*/node_modules/*` 16, `Abteilung/*/Exporte/*` 21); 60 hält die Bit-Grenze mit Abstand |
| Präfixe | unverändert 64 Einträge, 256 Bytes | Erfolgskriterium 1 |

**Ablehnen mit eigener Meldung (Codes, nie den Wert zurückgeben):** leer; zu lang; zu viele; `**` ("`*` matches across folders already"); `[`, `]`, `{`, `}`, `\` (Klassen, Klammern, Escape: Regex/fnmatch-artig, nicht in D-30-01); führendes `!` (Negation); Steuerzeichen; `.`/`..`-Segment (wie Präfixe); Muster ohne ein einziges Literalzeichen (`*`, `*/*`, `?*`: schlösse alles aus, Gegenstück zur Ablehnung von `files`, `ExclusionService.php:776-785`); Duplikat. Muster ohne `*` und `?`: Empfehlung ablehnen mit Hinweis auf "Excluded folders" (sonst zwei Schreibweisen derselben Regel). Literale Ordnernamen mit `[`/`]` bleiben über die Präfixliste ausschließbar. `(`, `)`, `+`, `$`, `^` und `.` NICHT ablehnen: alltäglich in Ordnernamen ("Fotos (2024)").

## Speicherort und Upgrade (Frage 7)

- **Neuer Schlüssel** `exclusion_patterns` (appconfig, Array) neben `exclusions`. Begründung: Ein 1.4.2-Präfix mit literalem `*` oder `?` (in Nextcloud-Namen zulässig) würde bei gemeinsamer Liste nach dem Upgrade als Muster gelesen und änderte seine Wirkung. Getrennt bleibt jeder gespeicherte Präfix byte-gleich und wird mit demselben Code verglichen.
- **Keine Migration:** fehlender Schlüssel liest sich als leere Liste (`getValueArray(..., [])`). Keine Repair-Step-Arbeit.
- **D-30-08 geprüft:** keine Änderung an tantivy-Schema, `SCHEMA_VERSION`, Indexmarken, `ANALYZER_VERSION`, `VERDICTS_GENERATION` (Code `excluded` existiert beidseitig) und keine Nextcloud-DB-Migration. Was sich ändert, ist die Statusantwort (zwei neue Felder für POL-01, siehe unten) und der Inhalt des Abgleichs-Vergleichs im Container. Beides ist weder Schema noch Marke. Befund: keine Schemaänderung nötig.
- **Purge:** `occ findling:purge` räumt den appconfig der App (`AppUninstallStep.php:15-80`); ob ein neuer Schlüssel dort einzeln genannt werden muss, prüft der Planer an `PurgeService` (nicht gelesen).
- **Upgrade-Beweis:** Dev-Instanz trägt `["Archiv"]` als 1.4.2-Bestand. Die Upgrade-Strecke in deploy-harp (Phase 36) kann einen Präfix vor dem Upgrade setzen und danach Wert und Wirkung prüfen; das passt in den dortigen Saatblock (Store upgrade 2b/5).

## Räumweg für Muster (EXCL-02)

**Muster 3, Empfehlung: zwei Wege wie bei den Präfixen.**

**Weg A (sofort, PHP):** Ein neuer `QueuedJob` (Arbeitsname `ExclusionSweepJob`), geplant von `save()` nur bei neu hinzugekommenen Mustern, läuft wie Crawl und SubtreeExpandJob in Bändern über jeden Mount aus `StorageService::getMounts()` mit `getFilesInMount()` (gleicher Mimetyp-Filter, Cursor als Job-Argument, Wanduhr-Budget, Nachfolger plant sich selbst). Für jede Datei, auf die `isExcluded(mountRelativePath(...))` antwortet: Löschzeile (`KIND_DELETE`) einreihen und die Urteilszeile in `findling_file_state` entfernen (neue Methode neben `revokeFailures`, die auch `no_text_layer` nimmt, weil die Datei unter einer Regel kein OCR-Memo mehr braucht). Muss als fünfte Aufrufstelle in Gate D aufgenommen werden.
- Vorteil: wirkt innerhalb einer Cron-Runde, wie die Seite es für Präfixe verspricht (`AdminViewService.php:981-990`).
- Kosten: ein Lauf über alle indexierbaren Dateien der Instanz je neuer Mustergruppe. Für #22 heißt das 266k Löschzeilen; `_forget` ist idempotent und billig (`poller.py:1868-1872`).
- Alternative, die ich nicht empfehle: SQL-`LIKE` auf `filecache.path` als Vorfilter (führendes `%` erzwingt Tabellenscan je Storage; Kollation unterscheidet je DB Groß/Klein), nur als Obermenge brauchbar.

**Weg C (Netz, Container):** In `Reconcile._compare` eine Zeile mit `skipped(excluded)` für eine Datei, die der Container KENNT (`stored is not None`, also ohne Grabstein), als `stale` einreihen, und zwar VOR dem Zweig `stored == row.etag` (`reconcile.py:614-620`). Danach greift der erprobte CR-01-Weg: `describe()` macht aus der Abholung einen Löschauftrag (`QueueService.php:886-898`), der Poller setzt den Grabstein, und weil die PHP-Zeile `content` ist, widerruft die Quittung die Urteilszeile (außer `no_text_layer`). Die nächste Runde sieht die Datei als unbekannt plus `excluded` und lässt sie liegen (`reconcile.py:621-623`), also keine Schleife.
- Deckt, was Weg A nicht sieht: per `occ config:app:set` gesetzte Regeln, später auftauchende Mounts, Ordner, die innerhalb eines Mounts unter eine Regel umbenannt werden, und dieselben Lücken bei Präfixen (B1).
- Latenz: bis `FINDLING_RECONCILE_MIN_INTERVAL_HOURS` (24) zur `FINDLING_RECONCILE_HOUR` (2), Ruhe-Tor `RECONCILE_QUIET_MAX` 100 (`config.py:631-647`).
- Erweitert den Owner-Entscheid 03.10.2026 Teil a um den Fall "bekannt und unverändert", der dort nicht geregelt war; im Sinn des Entscheids ("die Regel von heute entscheidet"). Planer-Entscheidung mit Owner-Veto.
- Zusätzlich die Guards `prefixes() !== []` / `=== []` an `FileEventListener.php:441`, `QueueService.php:886`, `ReconcileController.php:276` auf eine neue Methode (`hasRules()`) umstellen, sonst prüft eine Instanz mit nur Mustern nichts. Crawl und Diagnose rufen `isExcluded()` ohne Guard.

**Vorschau:** `affectedDocuments()` löst Präfixe in Ordner auf (`ExclusionService.php:445-479`); für Muster gibt es keinen billigen Weg. Empfehlung: für Muster keine Zahl, die Seite nutzt die zahlenlose Satzform (Muster der Bestandsseite `admin.js:1102-1108`) mit eigenem Satz "matching that pattern". `newPrefixes()`-Gegenstück `newPatterns()` für die Bestätigung.

## Admin-Seite (Frage 4)

- **Eine Seite, PHP-gerendert:** `php/templates/admin.php` (1363 Zeilen) plus `php/js/admin.js` (2317 Zeilen), kein Build-Schritt, keine ExApp-UI. Block "Rules and limits" (`admin.php:1243-1363`).
- **Empfehlung UI:** zweite Liste "Excluded patterns" direkt unter "Excluded folders", gleiche Zeilenvorlage (`admin.php:1354-1361`), eigenes Eingabefeld, Hilfesatz mit `*`/`?`-Erklärung und zwei Beispielen, eigener Leer-Satz. Die Hilfe von "Excluded folders" ("no wildcards and no patterns", `admin.php:1261`) bleibt inhaltlich richtig, sollte aber auf die zweite Liste verweisen (Schlüsselwechsel).
- **Formular:** `saveRules` und `previewRules` bekommen einen zweiten Array-Parameter (`exclusionPatterns`), Antwort `exclusionPatterns` mit Fehlercodes; Codes werden in der Seite auf Sätze abgebildet (Erfolgskriterium 3: "verständliche Meldung"), nie mit dem eingegebenen Wert. Die Bestandsseite bildet Codes heute gar nicht ab (`admin.js:1215-1229`), das ist neu.
- **Diagnose-Abhilfe:** `'Remove the matching entry under "Excluded folders".'` (`AdminViewService.php:490-493`) muss beide Listen nennen (Schlüsselwechsel, Anzahl gleich).
- **UI-Phase:** ROADMAP markiert "UI hint: yes", `.planning/config.json` hat `workflow.ui_phase: true`. Vor der Planung gehört ein 33-UI-SPEC.md her (wie Phase 27/32), sonst greift das UI-Sicherheitstor.

**Katalogkette (Gate-Pflichten bei jedem neuen oder geänderten Satz):**

| Was | Wo | Beleg |
|---|---|---|
| 16 Katalogdateien | `php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{js,json}` | `ls php/l10n` |
| de == de_DE byte-gleich | Test | `test_admin_ui_contract.py:3404-3408` |
| Schlüsselzahl 306 mit Begründungsabsatz | Test plus Docstring-Absatz "Whoever moves it next writes the next paragraph" | `test_admin_ui_contract.py:3394-3442` |
| gleiche Schlüssel in allen Katalogen | Test | `test_admin_ui_contract.py:3445` |
| Platzhalter je Sprache unverändert | Test | `test_admin_ui_contract.py:3653` |
| Sprachtabellen in 5 Dokumenten zeichengleich zum Katalog | `docs/l10n-{dutch,french,italian,portuguese,spanish}.md` | `test_admin_ui_contract.py:3955-3975` |
| Template-Map und Script-Map gleich | Test | `test_admin_ui_contract.py:2989-3010` |
| keine Markup-Bauten im Script, kein ungeescapetes Drucken, keine Halbgeviert-/Geviertstriche, keine Emojis | Gate C | `test_admin_ui_contract.py:1-50` |

**PHP-Baumhash-Gate:** `backend/tests/test_measurement_scripts.py:886-887` (`PHP_FILES_TODAY = 97`, `PHP_TREE_HASH_TODAY = "5cb3e48f..."`), geprüft in `test_the_recipe_reproduces_the_tree_hash_of_the_php_half` (`:2097-2118`), Rezept über `php/**/*.php` (JS und l10n nicht im Hash, `:870-874`). Jede Änderung an einer PHP-Datei verlangt neuen Hash plus Absatz "Moved on ... by Plan 33-xx", jede neue PHP-Datei (Job, Tests) erhöht `PHP_FILES_TODAY`. Das Python-Gegenstück `PACKAGE_TREE_HASH_TODAY` bewegt sich bei Änderungen unter `backend/src/findling` (Weg C, Statusfelder). **Folge für die Wellen:** Pläne, die PHP-Dateien ändern, können nicht parallel laufen, weil alle dieselben zwei Konstanten anfassen.

**PHPUnit:** 666 Tests laufen nur in CI (`php.yml`, im Autoload-Raum von nextcloud/server, PHP 8.2); lokal nur `php -l` per `php:8.3-cli`. Es gibt keinen `ExclusionServiceTest.php`; `ExclusionService` ist `final` und wird in Tests echt über gemocktes `IAppConfig` gebaut (`ReconcileControllerTest.php:33`, `82-90`; `StorageCrawlJobTest.php:237-260`). Der Matcher braucht einen eigenen Test mit Positivkontrolle und Gegenproben.

## Grenzwerte für #21 (Frage 5)

Issue #21 (`gh issue view 21`): Owner sagte zu, die Grenzen auf der Admin-Seite zu zeigen; `FINDLING_MAX_CELLS` ist seit 1.4.0 Deploy-Option. Issue #22 (`gh issue view 22`): Keynote-Bundles (`.key`), 266k Thumbnails mit `skipped(image_not_ocrable)`, Owner versprach "allowing patterns in the excluded folders" als Kandidat.

| Grenze | Default | Env-Variable | Deploy-Option in info.xml | Heute in der Statusantwort | Heute auf der Seite |
|---|---|---|---|---|---|
| Zellgrenze | 200 000 | `FINDLING_MAX_CELLS` | ja, `backend/appinfo/info.xml:569-573` | nein | nein |
| Adressraum je Dokument | 536 870 912 (512 MiB) | `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES` | ja, `info.xml:552-556` | nein | nein |
| Größengrenze (Decke) | 52 428 800 (50 MiB) | `FINDLING_MAX_FILE_BYTES` | ja, `info.xml:423-427` | ja, `maxFileBytes` (`status.py:305-309`, `572`) | ja, Feld "Largest file to read" mit `max` = Decke und Hinweissatz (`admin.php:1285-1292`) |
| OCR-Seitendeckel | 30 Sparsam, 100 Standard, 150 Leistung | `FINDLING_OCR_MAX_PAGES` (überstimmt Profil) | ja, `info.xml:452-456` | ja, `profile.values.ocrMaxPages` plus `sources` (`status.py:121-131`) | nur wenn per env gesetzt (`admin.php:1124-1131`, `AdminViewService.php:259-276`, `899-915`) |

Belege der Defaults: `config.py:236`, `266`, `279`, `533`, `1112`, `1125`; Lesen aus der Umgebung `config.py:1650-1694`.

**Weg zur Seite:** Die Seite holt `/status` vom Container (`AdminViewService.php:647`) und filtert jedes Feld (`backend()`, `AdminViewService.php:2330-2340`, `counter()`). Empfehlung: zwei neue Felder `maxCells` und `extractAddressSpaceBytes` in `HardwareReport`/Statusmodell (`status.py`), aus `settings()` wie `maxFileBytes`; PHP liest sie als optionale Zähler (null bei Container 1.4.x, Zeile dann verborgen, Muster wie `optionalCounter`). Der OCR-Seitendeckel kommt bereits aus `profile.values.ocrMaxPages`, mit Quelle `env` oder Profil. Kein neuer Endpunkt nötig.

**Befund B3 (falscher Änderungshinweis):** `admin.php:1291` sagt "raise FINDLING_MAX_FILE_BYTES in the app settings of AppAPI, which restarts the container". In AppAPI 34.0.0 auf der Dev-Instanz gibt es nur `GET /apps/deploy-options/{appId}` (`apps/app_api/appinfo/routes.php:41`); gesetzt werden Deploy-Optionen beim Deploy (`ExAppsPageController::enableApp`, `:317-329`) oder per `occ app_api:app:register --env`; `app_api:app:update` übernimmt die gespeicherten Optionen (`Command/ExApp/Update.php:97-102`). Die offizielle Doku nennt nur Setzen beim Deploy und Anzeigen danach [CITED: docs.nextcloud.com/server/stable/admin_manual/exapps_management/AdvancedDeployOptions.html]. Der projekteigene Weg: `occ app_api:app:unregister findling_backend` OHNE `--rm-data`, dann neu registrieren, Daten bleiben (`docs/performance.md:1446-1450`). Der neue Hinweis für alle vier Grenzen sollte genau das sagen und auf eine Doku-Stelle verweisen; der alte Satz wird ersetzt (Schlüsselwechsel).

**Formulierungsvorschlag (Entwurf, Owner-Abnahme):**
- Überschrift im Block "Rules and limits": "Limits per file" / "Grenzen je Datei".
- Zeilen: "Largest file the backend reads: %s" / "Memory one document may use while it is read: %s" / "Cells per spreadsheet: %s" / "Pages read per scanned document: %s"; Variablenname je Zeile als `<code>` über die Marker-Technik der env-Zeilen (`admin.php:1118-1131`, `1188-1194`), nie im übersetzten Satz.
- Hinweis: "These are deploy options of Findling Backend. To change one, remove Findling Backend without deleting its data and deploy it again with the new value." plus Verweis auf `docs/` (Pfad vom Planer).

## Hardware-Hinweis (Frage 6)

**Fundstellen (alle mit identischem englischem Schlüssel):**
- `php/templates/admin.php:1072` (`$probeCauseNames['hardware_short']`)
- `php/js/admin.js:1449` (`probeCauseNames()`)
- `php/l10n/*.json:292` und `php/l10n/*.js:293` in allen 16 Dateien
- `docs/l10n-{dutch:497,french:415,italian:456,portuguese:580,spanish:418}.md`
- Test `backend/tests/test_admin_ui_contract.py:2974-2986` baut den Satz aus `SUGGEST_*` in `config.py:1142-1145` und vergleicht Template und Script
- nicht betroffen: `docs/admin-page.md:552` (nennt nur den Code), Messdokumente unter `docs/measurements/2026-10-abnahme-anfahrt/` (historisch, nicht ändern)

**Was unverständlich ist (Begründung, keine Owner-Aussage gefunden):** "box" ist Jargon und meint hier das, was der Container sieht (`min(memory.max, MemTotal)`, cgroup-Kernquote, `hardware.py:148-157`), nicht unbedingt den Server; "the profile" sagt nicht welches; der Satz sagt nicht, was zu tun ist. Dieselbe Wortwahl steht in drei weiteren Sätzen des Profilblocks ("Suggested for this box", "How much of this box Findling may use", "this box has less hardware ...", `admin.php:1138-1146`); POL-03 nennt nur den einen, die anderen bleiben außerhalb, außer der Owner will es anders.

**Vorschlag (Platzhalterfrei wie heute, Zahlen aus `config.py`):**
- en: "Findling sees fewer CPU cores or less memory than this profile requires. Standard requires at least 3 cores and 6 GB of memory, Performance at least 6 cores and 12 GB. If the backend container has a memory or CPU limit, that limit counts."
- de: "Findling sieht weniger CPU-Kerne oder weniger Arbeitsspeicher, als dieses Profil verlangt. Standard verlangt mindestens 3 Kerne und 6 GB Arbeitsspeicher, Leistung mindestens 6 Kerne und 12 GB. Ist der Backend-Container begrenzt, zählt diese Grenze."
- fr: "Findling voit moins de cœurs de processeur ou moins de mémoire que ce profil n'en demande. Standard demande au moins 3 cœurs et 6 Go de mémoire, Performance au moins 6 cœurs et 12 Go. Si le conteneur du backend est limité, c'est cette limite qui compte."
- es/it/nl/pt_BR/pt_PT nach Muster der bestehenden Übersetzungen, als maschinelle Entwürfe unter demselben datierten Vorbehalt wie bisher.

Gates: Schlüssel wird ersetzt (alt raus, neu rein), Anzahl bleibt; Test `:2974-2986` bekommt den neuen Satz; Sprachtabellen der fünf Dokumente; Template- und Script-Map gleich (`:2989-3010`). "GB" mit `// 10**9` stimmt mit den Bytewerten 6 000 000 000 / 12 000 000 000 überein.

## Standard Stack

Keine neuen Pakete. Alles mit dem vorhandenen Stack:

| Baustein | Version | Zweck |
|---|---|---|
| PHP (Companion) | Nextcloud 33 bis 35, CI PHP 8.2, lokal `php:8.3-cli` | ExclusionService, Job, Controller, Template |
| `mbstring`, `intl`/Polyfill | im Nextcloud-Kern | `mb_str_split`, `\Normalizer` (Polyfill vom Kern, `Provider.php:452-457`) |
| Python 3.13 + FastAPI/pydantic | vorhanden | zwei Statusfelder, Abgleichszweig |
| PHPUnit (CI) | ^11.5 laut `php.yml:231-234` | Matcher- und Jobtests |

## Package Legitimacy Audit

Keine externen Pakete werden installiert. slopcheck nicht nötig.

## Architecture Patterns

### Datenfluss

```
Admin-Formular (Muster) --POST /admin/rules--> SettingsController::saveRules
   --> ExclusionService::validate/save --> appconfig "exclusion_patterns"
   --> neue Muster? --> IJobList::add(ExclusionSweepJob)          [Weg A]

Cron --> ExclusionSweepJob (Bänder über getMounts/getFilesInMount)
   --> isExcluded(mountRelativePath) ja --> Queue KIND_DELETE + Urteilszeile weg
   --> Container-Poller --> _forget (Index, ACL, Grabstein)

Datei-Ereignis --> FileEventListener --> hasRules && isExcluded --> nicht einreihen
Crawl/Recount --> verdict() --> excluded gezählt (scan_stats) --> Kachel "Excluded by a rule"

Container-Abgleich (nachts) --> /files/slice (PHP markiert skipped(excluded) live)
   --> _compare: excluded UND bekannt --> stale --> requeue content    [Weg C]
   --> Abholung --> describe(): isExcluded --> Löschauftrag --> _forget
   --> Quittung (content) --> revokeFailures

Admin-Seite --> AdminViewService --> /status (maxFileBytes, maxCells, extractAddressSpaceBytes, profile.values.ocrMaxPages)
   --> Block "Limits per file" nur lesend
Diagnose --> Stufe 2 --> isExcluded --> "Excluded by a rule"
```

### Muster 1: Eine Prüfmethode, zwei Listen

`isExcluded()` bleibt der einzige Helfer; Gate D verbietet `explode(` und Segment-Deutung im Körper von `isExcluded` (`test_exclusion_path_space.py:253-288`). Deshalb den Musterteil in eine private Methode legen und aus `isExcluded` aufrufen; die Gate-Prüfung `scan_segment_refusal` gilt dann weiter für `normalise`/`isExcluded`, und der Planer ergänzt Selbsttests für die Musterseite (`.`/`..`-Ablehnung auch in der Muster-Normalisierung).

### Muster 2: Kompilieren beim Lesen, defensiv

Wie `prefixes()` (`ExclusionService.php:168-228`): appconfig lesen, jeden Eintrag normalisieren und kompilieren, Unbrauchbares zählen und einmal loggen (nur Zahlen), über dem Deckel abschneiden und warnen. Kompilat im Request-Cache.

### Muster 3: Räumen in Bändern

Vorlage `SubtreeExpandJob` (`BATCH_SIZE 250`, `MAX_SECONDS 30`, `INTERVAL 5`, Cursor im Argument, `SubtreeExpandJob.php:38-72`) und `StorageCrawlJob` (Transaktionsbänder, Cursor bewegt sich für jede gesehene Datei).

### Anti-Patterns

- **Muster in die Liste `exclusions` mischen:** ändert die Bedeutung gespeicherter 1.4.2-Präfixe mit `*`/`?`.
- **`fnmatch()`/`preg_match()` oder Regex-Übersetzung:** ReDoS-Fläche, Gate D, und `[...]` käme durch die Hintertür.
- **Muster in den Container schicken:** bricht D-06 und das Gate "container carries no prefix list".
- **Ausgeschlossene Zeilen im Slice filtern:** kürzere Seite liest sich als `final` und löscht den Rest des Mounts (`StorageService.php:413-421`).
- **Eine Urteilszeile je ausgeschlossener Datei schreiben:** ausdrücklich verworfen (`ExclusionService.php:50-57`).
- **Werte oder Pfade loggen:** nur Zähler (T-04-51).

## Don't Hand-Roll

| Problem | Nicht bauen | Stattdessen | Warum |
|---|---|---|---|
| Löschen eines Dokuments | eigene Container-Route | Queue `KIND_DELETE` bzw. `describe()`-Löschauftrag | Schreib-Allowlist des Read-only-Gates steht bei drei Einträgen (`ExclusionService.php:502-509`) |
| Pfadraum | Pfad an der Aufrufstelle bauen | `mountRelativePath()` / `mountRelativePathInStorage()` | Pitfall 4, Gate D |
| Mount-Liste | eigene Abfrage | `StorageService::getMounts()` | eine Mount-Liste (Gate D Punkt 3) |
| NFC | eigene Normalisierung | `\Normalizer` mit Rückfall wie `Provider::composed` | Kern liefert Polyfill |
| Band-Job | neue Ablaufmechanik | Form von `SubtreeExpandJob` | erprobt mit Cursor und Wanduhr |

## Runtime State Inventory

| Category | Items Found | Action Required |
|---|---|---|
| Stored data | appconfig `findling/exclusions` (Dev: `["Archiv"]`); Container `files`-Tabelle mit Zeilen für Dateien unter künftigen Mustern; `findling_file_state` mit alten Urteilen solcher Dateien | Präfixe: nichts. Container-Zeilen: Räumweg A/C (Daten, kein Code-Rename). Urteilszeilen: Bereinigung beim Räumen (B2) |
| Live service config | AppAPI Deploy-Optionen der ExApp (`oc_ex_apps_deploy_options`), nur beim Deploy änderbar | keine Änderung; Hinweistext korrigieren (B3) |
| OS-registered state | keine; Dev-Host-Backend läuft als Prozess über `scripts/dev/register-exapp.sh` (Neustart bei geänderten `backend/src`) | nach Python-Änderung `FINDLING_PORT=8090 scripts/dev/register-exapp.sh` |
| Secrets/env vars | keine neuen; `FINDLING_MAX_CELLS`, `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES` nur gelesen | keine |
| Build artifacts | Store-Archiv `scripts/release/store-archive.sh` packt `php/`; neue PHP-Dateien müssen drin sein | im Archiv-Inhalt prüfen (wie 32-07 für `unified-search.js`) |

## Common Pitfalls

### Pitfall 1: Guard nur auf Präfixe
**What goes wrong:** Instanz mit nur Mustern prüft im Listener, in `describe()` und im Slice nichts.
**Why:** `prefixes() !== []` als Kurzschluss an drei Stellen.
**How to avoid:** `hasRules()` einführen; Test "nur Muster, keine Präfixe".
**Warning signs:** Datei in `X.key/` wird nach dem Speichern bei der nächsten Änderung wieder eingereiht.

### Pitfall 2: Abgleich holt geräumte Dateien zurück oder lässt sie liegen
**What goes wrong:** Ohne Weg C bleibt eine bekannte unveränderte Datei für immer; ohne Ausschluss-Markierung im Slice würde ein Grabstein als Wiederherstellung gelesen.
**How to avoid:** Slice markiert über `isExcluded` (inkl. Muster), `_compare` behandelt "bekannt + excluded" als stale; Tests in `test_reconcile.py` für beide Etag-Fälle und für "nach Grabstein liegen lassen".

### Pitfall 3: Fehlerliste zählt Ausgeschlossene weiter
**What goes wrong:** #22-Rauschen bleibt (B2).
**How to avoid:** Urteilszeilen beim Räumen löschen; Positivkontrolle: Zeile vor dem Ausschluss vorhanden, danach weg, Kontrolldatei außerhalb behält ihre Zeile.

### Pitfall 4: `*/node_modules/*` verfehlt die oberste Ebene
**How to avoid:** Prüfung auch gegen `/` + Pfad; Testfall `node_modules/x.js` im Home.

### Pitfall 5: Bitbreite überschritten
**What goes wrong:** mehr als 62 Nicht-Stern-Symbole laufen über das Vorzeichenbit.
**How to avoid:** Längengrenze 60 Zeichen in `validate` und beim defensiven Lesen.

### Pitfall 6: Parallele Pläne kollidieren an den Baumhashes und an den Katalogen
**How to avoid:** Pläne mit PHP- oder Kataloganteil in Wellen nacheinander.

### Pitfall 7: Schreibpfad-Kosten
**What goes wrong:** jeder Write der Instanz zahlt alle Muster.
**How to avoid:** Musterdeckel 32, Pfad einmal zerlegen, Messung im Audit wiederholen (P-Befund wie in 32-08).

## Code Examples

Bitparalleler Kern (Prototyp, im Scratchpad gemessen; Planer übernimmt die Idee, nicht den Text):

```php
// One pass over '/' . $relative; '*' self-loop, '?' one character, ancestor-or-self at '/'.
$d = 1;
foreach ($chars as $i => $ch) {
	$d = (($d << 1) & (($masks[$ch] ?? 0) | ($ch === '/' ? 0 : $q))) | ($d & $star);
	if ($i === 0) {
		$d |= 1; // second start: the path without the leading slash
	}
	$boundary = !isset($chars[$i + 1]) || $chars[$i + 1] === '/';
	if ($boundary && $i > 0 && ($d & $accept) !== 0) {
		return true;
	}
	if ($d === 0) {
		return false;
	}
}
return false;
```

Abgleichszweig (Skizze für `reconcile.py:614`):

```python
excluded = row.state == EXCLUDED_STATE and row.reason == EXCLUDED_REASON
if excluded:
    if stored is not None:  # known here, so describe() will turn the claim into a delete order
        stale.append(row.file_id)
    continue
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| Präfix "ohne Wildcards und ohne Muster" (D-06) | Präfix plus Platzhaltermuster (D-30-01) | Owner-Tor 10.10.2026 | Docblock `ExclusionService.php:17-22` und Hilfesatz sind zu überarbeiten |
| Abgleich als Netz für Ausschlüsse | Abgleich lässt bekannte Dateien liegen | Owner-Entscheid 03.10.2026 | Netz neu herstellen (Weg C) |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | Apple-Bundle-Endungen (`.photoslibrary`, `.key`, `.pages`, `.numbers`, `.app`, `.bundle`, `.fcpbundle`) sind klein geschrieben | Muster-Semantik | groß geschriebene Bundles würden von `*.key` nicht getroffen; Doku-Hinweis nötig |
| A2 | Dateicache-Pfade sind NFC | Muster-Semantik | NFD-Pfade (extern angelegt, `files:scan`) verfehlt ein NFC-Muster; bekannt aus M-32-01 |
| A3 | `POST /admin/rules` lässt sich für den Dev-Nachweis per `curl` mit Basic-Auth und Header `OCS-APIRequest: true` ohne CSRF-Token aufrufen | Nachweisweg | sonst Playwright (Owner-Regel ohnehin) |
| A4 | `occ findling:purge` entfernt den ganzen appconfig der App, also auch `exclusion_patterns` | Speicherort | sonst bleibt ein Schlüssel nach Purge liegen |
| A5 | Die gemessenen Matcher-Zeiten übertragen sich auf den echten Code in PHP 8.2 (CI) | Grenzwerte | Grenzen nach unten anpassen; Audit misst nach |

## Open Questions

1. **Weg C ändert das Verhalten des Abgleichs für bekannte Dateien unter Regel.**
   - Wissen: im Geist des Owner-Entscheids vom 03.10.2026, schließt B1 auch für Präfixe.
   - Unklar: ob der Owner das als neue Entscheidung sehen will.
   - Empfehlung: als Planer-Entscheidung mit ausdrücklichem Veto-Hinweis im Plan führen; keine Rückfrage vorab.
2. **Bereinigung der Urteilszeilen auch für Präfix-Räumungen (SubtreeExpandJob)?**
   - Wissen: B2 betrifft Präfixe heute genauso; Erfolgskriterium 3 spricht allgemein von "ausgeschlossene Dateien".
   - Empfehlung: ja, gleiche Methode in beiden Räumwegen; die Präfix-Treffer bleiben unverändert, nur die Fehlerliste wird ehrlicher.
3. **`?` über `/` hinweg?** Empfehlung nein (Planer-Entscheidung, Begründung oben).
4. **Muster ohne Platzhalter erlauben?** Empfehlung ablehnen mit Verweis auf die Ordnerliste.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| Docker | `php -l`, Dev-Instanz | ja | läuft | , |
| `php:8.3-cli` Image | `php -l`, Matcher-Messung | ja | lokal vorhanden | `php:8.2-cli` |
| Dev-Nextcloud `findling-nextcloud` | Nachweis | ja, HTTP 200 auf 8090 | 34.0.3, AppAPI 34.0.0, findling 1.4.2, findling_backend 1.4.2 | , |
| HaRP-Instanz 8096 | nicht nötig | läuft | backend 1.4.3 | , |
| Node | `node --check` | ja | v22.21.0 | , |
| uv | Python-Gates | ja | 0.11.7 | , |
| reuse | `reuse lint` | nicht im PATH | , | per uv/pipx wie in Phase 32 (Aufruf nicht geprüft) |
| PHPUnit | PHP-Tests | nur CI | ^11.5 | CI-Lauf `php.yml` |

## Nachweisweg auf der Dev-Instanz (Frage 8)

Voraussetzungen: `php/` ist gebunden (sofort live); Host-Backend nach Python-Änderung neu starten (`FINDLING_PORT=8090 scripts/dev/register-exapp.sh`); Cron läuft nicht von selbst, `docker exec -u www-data findling-nextcloud php cron.php` von Hand.

1. **Saat (testuser, WebDAV):** `/Abnahme33/Vortrag.key/Data/notiz.txt` mit eindeutigem Wort A; Kontrolle `/Abnahme33/Kontrolle/notiz.txt` mit Wort B; Gegenprobe `/Abnahme33/Vortrag.keynote/notiz.txt` mit Wort C (darf nicht getroffen werden); `/node_modules/x.txt` oben im Home mit Wort D; zusätzlich ein Bild, das ein Urteil `skipped(...)` in der Fehlerliste erzeugt, unter `Vortrag.key/`.
2. **Positivkontrolle vorher:** Suche nach A, B, C, D je 1 Treffer (OCS-Suche des Providers `findling`); Fehlerliste zeigt das Bild-Urteil; `occ findling:diagnose <id>` zeigt `indexed`.
3. **Muster speichern über die Seite** (Playwright, gemeinsam mit dem Owner nach Regel): `*.key` und `*/node_modules/*`. Bestätigungssatz erscheint ohne Zahl.
4. **cron.php** bis der Kehrjob fertig ist (Jobliste leer für die Klasse).
5. **Nachher:** A und D 0 Treffer; B und C weiter 1 Treffer (Kontrolle und Gegenprobe); Fehlerliste ohne das Bild-Urteil; Diagnose der A-Datei "Excluded by a rule"; nach Recount Kachel "Excluded by a rule" um die Saat gestiegen; neue Datei unter `Vortrag.key/` wird nicht eingereiht.
6. **Bestand:** Präfix `Archiv` unverändert in appconfig und wirksam (Datei unter `Archiv/` als excluded diagnostiziert).
7. **Weg C separat:** Muster per `occ config:app:set findling exclusion_patterns` setzen (umgeht Weg A), Host-Backend mit `FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1` und `FINDLING_RECONCILE_HOUR=<aktuelle Stunde>` neu starten, Abgleich abwarten, Treffer weg; Gegenprobe: auf dem Stand vor der Änderung (Commit davor) bleibt der Treffer.
8. **Rückweg:** Muster entfernen, `occ findling:index --restart` oder Abgleich, A wieder 1 Treffer.
9. **Aufräumen:** Saat löschen, cron, Papierkorb leeren (Muster aus 32-07); appconfig der Muster zurück auf leer.

Ablehnung prüfen: `[0-9]*`, `**/x`, `!foo`, `*`, ein 61-Zeichen-Muster, 33 Muster: jeweils verständliche Meldung, nichts gespeichert, Log nur mit Zähler.

## Gates dieser Phase (Frage 9)

| Gate | Relevant | Warum |
|---|---|---|
| `pytest` (aus `backend/`, `PYTHONUTF8=1`) | ja | Gate D, Gate C, Kataloge, Baumhashes, Abgleich, Status |
| `ruff check`, `ruff format --check` | ja | Python-Änderungen (Abgleich, Status, Tests) |
| `PYRIGHT_PYTHON_FORCE_VERSION=latest pyright` | ja | dto. |
| `vulture src tests --min-confidence 80` | ja | dto. |
| `node --check php/js/admin.js` | ja | Listen, Fehlermeldungen, Grenzblock |
| `reuse lint` | ja | neue Dateien (Job, Tests) |
| PHP `php -l` per `php:8.3-cli` | ja | alle geänderten PHP-Dateien inkl. Templates |
| PHPUnit | nur CI | Matcher-, Service-, Job-, Controller-Tests |

Gezielte Läufe statt Vollsuite bei knappem RAM: `test_exclusion_path_space.py`, `test_admin_ui_contract.py`, `test_measurement_scripts.py -k tree_hash`, `test_reconcile.py`, `test_status_endpoint.py`, `test_php_trust_boundary.py`, `test_unified_search_plugin.py` (Katalogschlüssel). Vollsuite einmal vor dem Push je Plan (bisher 5600+ Tests, ca. 13 min laut STATE.md).

## Security Domain

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2 Authentication | nein | , |
| V3 Session Management | nein | , |
| V4 Access Control | ja | Admin-Route ohne `NoAdminRequired`; Container-Routen mit `ExAppRequired` und Fremdaufrufer-Abwehr (bestehend) |
| V5 Input Validation | ja | geschlossene Fehlercodes, Längen- und Zahlgrenzen, Ablehnung statt Filterung, defensives Lesen von appconfig |
| V6 Cryptography | nein | , |

| Pattern | STRIDE | Mitigation |
|---|---|---|
| ReDoS über Muster und lange Nutzerpfade | Denial of Service | bitparalleler Matcher O(n), Deckel 32 Muster und 60 Zeichen |
| Muster schließt alles aus (`*`) | Tampering/DoS am Index | Ablehnung ohne Literalzeichen |
| Pfad- oder Musterleck in Logs/Antworten | Information Disclosure | nur Zähler und Codes (T-04-51, T-04-60) |
| Zweiter Schreiber `occ config:app:set` | Tampering | defensives Lesen mit Normalisierung, Deckel, Warnzeile |
| Kehrjob als Massenlöschung | DoS | Bänder, Wanduhr, Idempotenz, keine neue Container-Route |
| Statusfelder aus dem Container | Tampering über Vertrauensgrenze | `counter()`-Filter in `AdminViewService::backend()` |

## Empfohlene Planaufteilung

Wegen Baumhash- und Katalogkonflikten seriell in Wellen; Python-Anteile können neben reinen PHP-Plänen laufen, wenn sie nur `backend/src` und eigene Tests anfassen (dann bewegt sich nur `PACKAGE_TREE_HASH_TODAY`).

| Plan | Inhalt | Welle |
|---|---|---|
| 33-01 | ExclusionService: Schlüssel `exclusion_patterns`, Normalisierung (NFC, Ablehnungen, Codes), Matcher, `isExcluded` beide Listen, `hasRules()` an drei Guards, Gate D erweitert, PHPUnit `ExclusionServiceTest` | 1 |
| 33-02 | Container-Teil: Abgleichszweig (Weg C) mit Tests; Statusfelder `maxCells`, `extractAddressSpaceBytes` mit Tests | 1 (parallel zu 33-01, nur Python) |
| 33-03 | Räumweg A: `ExclusionSweepJob`, Urteilszeilen-Bereinigung für Muster und Präfixe, `save()` plant den Job, Vorschau ohne Zahl, PHPUnit | 2 |
| 33-04 | Admin-Seite Muster: zweite Liste, Fehlermeldungen je Code, Bestätigungssatz, Diagnose-Abhilfe, Kataloge (16 + 5), Schlüsselzahl, Wortlaut-Entwurf | 3 |
| 33-05 | POL-01 und POL-03: Block "Limits per file" (Template, Script, AdminViewService), Ersatz des AppAPI-Satzes, Hardware-Satz, Kataloge | 4 |
| 33-06 | Doku (admin-page.md, Muster-Doku dreisprachig wo nötig, CHANGELOG, Store-Entwurf Teil Phase 33), Dev-Nachweis 8090 mit Owner per Playwright | 5 |
| 33-07 | Security-, Bug- und Performance-Audit (Matcher-Korpus, Schreibpfad-Messung, Kehrjob auf großem Korpus) | 6 |

Vorher: 33-UI-SPEC.md (UI-Phase-Gate).

## Sources

### Primary (HIGH confidence)
- Codebasis `C:\Users\Student\nextcloud-search`, Stand `c800826c`, alle Datei:Zeile-Angaben oben
- `gh issue view 21`, `gh issue view 22` (13.10.2026)
- Dev-Instanz `findling-nextcloud`: `occ config:app:get findling exclusions`, `occ app_api:app:list`, AppAPI 34.0.0 Quellen (`routes.php`, `ExAppsPageController.php`, `Command/ExApp/Update.php`)
- Prototyp-Messung in `php:8.3-cli` (Matcher, 13.10.2026)

### Secondary (MEDIUM confidence)
- [Nextcloud Admin Manual: Advanced Deploy Options](https://docs.nextcloud.com/server/stable/admin_manual/exapps_management/AdvancedDeployOptions.html)
- [Nextcloud Admin Manual: Managing ExApps](https://docs.nextcloud.com/server/stable/admin_manual/exapps_management/ManagingExApps.html)

### Tertiary (LOW confidence)
- Bundle-Endungen von Apple (A1), aus Trainingswissen

## Metadata

**Confidence breakdown:**
- Bestand und Codepfade: HIGH, jede Aussage an Datei:Zeile belegt, Ausschluss-Tests lokal grün (28 passed)
- Muster-Semantik und Matcher: MEDIUM, Prototyp korrekt in 13 Fällen und gemessen, echter Code steht aus
- Räumwege: MEDIUM-HIGH, beide nutzen erprobte Pfade; Weg C ist eine Verhaltensänderung
- Grenzwerte: MEDIUM, aus Prototyp-Messung abgeleitet

**Research date:** 2026-10-13
**Valid until:** 2026-11-12 (stabiler Bestand; neu prüfen, falls Phase 36 vorher Abgleich oder ExclusionService anfasst)
