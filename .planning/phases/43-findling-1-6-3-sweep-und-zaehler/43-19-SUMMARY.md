---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 19
subsystem: ui
tags: [l10n, admin-page, php, smb, d-43-16]

requires:
  - phase: 43-findling-1-6-3-sweep-und-zaehler (43-07)
    provides: End-to-End-Beleg der 1.6.3-Zählung; 43-17/43-18 lieferten Gateway-Frist und skipped(unreadable) für 422
provides:
  - Abhilfetext zu skipped(unreadable) nennt externe Speicher, Sperren und Offline-Dateien (neuer Schlüssel in allen 16 Katalogen, alter entfernt)
  - SMB-Zusatzsatz als eigener Schlüssel, angehängt nur wenn php-smbclient fehlt (43-18 Fix 2), Probe hinter Closure-Naht, ein PHPUnit-Fall je Zweig
  - Block V in 43-TEXTE.md für die Owner-Runde 43-12 (EN/DE/FR plus Zusatzsatz)
  - korrigierter Docblock über PHP_ONLY_NOT_READABLE (422-Quittung seit 1.6.3, D-43-16)
  - de-Schlüsselzahl 366, PHP-Baumhash 20dac366 (beide Rechenwege)
affects: [43-12 owner-runde, 43-13 store-einreichung, admin-seite]

tech-stack:
  added: []
  patterns: [Closure-Naht im Konstruktor für Umgebungsproben in einer final class (Muster BoundedStreamReader)]

key-files:
  created: []
  modified:
    - php/lib/Service/AdminViewService.php
    - php/lib/Service/FileStateService.php
    - php/tests/Unit/AdminViewServiceTest.php
    - php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{json,js}
    - docs/l10n-{french,spanish,italian,dutch,portuguese}.md
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-TEXTE.md

key-decisions:
  - "Die php-smbclient-Probe liegt hinter einer Closure-Naht im Konstruktor statt hinter einer per Unterklasse überschreibbaren Methode, weil AdminViewService final ist; dasselbe Nahtmuster wie die Uhr- und Pause-Closures von BoundedStreamReader, der Test fährt beide Zweige ohne die Erweiterung"
  - "FR-Begriff an den Bestand angeglichen: 'du Team Folder' statt 'du dossier d'équipe' aus dem Planentwurf; der FR-Satz trägt wie der abgelöste ein ' : ' mit gewöhnlichem Leerzeichen"
  - "Kein lokaler PHPUnit-Beleg: Docker-Engine kam trotz Start und Restart nicht hoch (WSL-Distro docker-desktop blieb Stopped), CI übernimmt mit dem nächsten freigegebenen Push (F2)"

patterns-established:
  - "Umgebungsprobe in final class: optionaler ?\\Closure-Konstruktorparameter mit Default null, Produktion bekommt function_exists"

requirements-completed: [D-43-16, D-43-11]

duration: 29min
completed: 2026-11-08
---

# Phase 43 Plan 19: Abhilfetext zu unreadable und SMB-Zusatzsatz Summary

**Die Abhilfe zu skipped(unreadable) deckt jetzt vom externen Speicher verweigerte, gesperrte und ausgelagerte Dateien ab (16 Kataloge, Block V für 43-12), plus SMB-Zusatzsatz hinter einer testbaren Probe und korrigierter Docblock.**

## Performance

- **Duration:** 29 min (dazu rund 25 min erfolgloser Docker-Start für PHPUnit)
- **Started:** 2026-11-08T18:09:00Z
- **Completed:** 2026-11-08T18:38:21Z
- **Tasks:** 1/1
- **Files modified:** 27

## Accomplishments

- Neuer englischer Schlüssel "The file is still there. Check the advanced permissions of the Team Folder or the access rights on the external storage: ... A file that is locked or offline is tried again a few times." ersetzt den alten in AdminViewService::REASON_TEXT und in allen 16 Katalogen (de, de_DE, es, fr, it, nl, pt_BR, pt_PT, je .json und .js); DE und FR wörtlich aus dem Plan (FR-Begriff Team Folder an fr.json angeglichen), es/it/nl/pt_BR/pt_PT maschineller Entwurf unter Vorbehalt (Muster 39-01); je eine ersetzte und eine neue Zeile in den fünf docs/l10n-*.md samt datiertem Nachtrag.
- SMB-Zusatzsatz (43-18 Fix 2) als eigener Schlüssel in allen 16 Katalogen; AdminViewService hängt ihn in reasonText() nur an die unreadable-Abhilfe an, wenn `function_exists('smbclient_state_new')` falsch ist (dieselbe Prüfung wie icewind/smb System::libSmbclientAvailable); die Prüfung sitzt in smbclientLoaded() hinter einer Closure-Naht im Konstruktor; zwei PHPUnit-Fälle (Erweiterung da: kein Zusatz; fehlt: Zusatz, und gateway_error bleibt ohne Zusatz).
- Block V in 43-TEXTE.md angelegt (Zweck, Ort, EN/DE/FR, Begriffsvermerk, Zusatzsatz-Abschnitt aus dem Vorab-Entwurf übernommen samt neuer FR-Zeile); Vermerk, dass der Owner in 43-12 freigibt, keine Maschinenzeile.
- FileStateService: Docblock über PHP_ONLY_NOT_READABLE korrigiert; er sagt jetzt, dass skipped(unreadable) seit 1.6.3 auch die Quittung für eine Gateway-Antwort 422 ist (D-43-16), die Zählung beide Herkünfte gleich behandelt und der Container solche Zeilen aus seinem judged-Ausdruck nimmt. Kein Code geändert.
- de-Schlüsselzahl in test_admin_ui_contract.py von 365 auf 366 (Ersatz bewegt nichts, Zusatz +1) mit Absatz "It stands at 366 since 2026-11-08, plan 43-19 ..."; PHP-Baumhash in test_measurement_scripts.py auf 20dac366f67114217d13d20eac6d82739ac22e2ee298882b2f21cfdc940713a2 nachgezogen (129 Dateien unverändert), Journal "Moved on 2026-11-08 by Plan 43-19 (unreadable remedy text)", beide Rechenwege (Rezept 40b-baumhash.py und unabhängig find/sort/tr/sha256sum, auch über git archive HEAD vor dem Plan: 6d1847e6 bestätigt).

## Task Commits

1. **Task 1: Block V, Abhilfetext in 16 Katalogen, Docblock, Kontrakt und Baumhash** - `72f4d252` (fix)

**Plan metadata:** siehe Folge-Commit mit dieser SUMMARY

## Files Created/Modified

- `php/lib/Service/AdminViewService.php` - neuer Abhilfetext, Konstante UNREADABLE_SMB_HINT, Closure-Naht `?\Closure $smbclientProbe = null`, smbclientLoaded(), Anhängen in reasonText()
- `php/lib/Service/FileStateService.php` - nur Docblock über PHP_ONLY_NOT_READABLE (D-43-16)
- `php/tests/Unit/AdminViewServiceTest.php` - reasonTextWithProbe()-Helfer, zwei Fälle (je Zweig), Eingrenzung auf unreadable
- `php/l10n/*.{json,js}` (16 Dateien) - alter Schlüssel raus, neuer Schlüssel und SMB-Schlüssel rein; de und de_DE bytegleich
- `docs/l10n-{french,spanish,italian,dutch,portuguese}.md` - ersetzte Zeile, neue SMB-Zeile, Nachtrag 08.11.2026
- `backend/tests/test_admin_ui_contract.py` - 366 mit Absatz und Kommentarrechnung
- `backend/tests/test_measurement_scripts.py` - PHP_TREE_HASH_TODAY 20dac366, Journal
- `.planning/phases/43-.../43-TEXTE.md` - Block V samt Zusatzsatz, Kopf-Nachtrag

## Decisions Made

- Closure-Naht statt überschreibbarer Methode: AdminViewService ist `final` (und bleibt es); der Plan verlangte eine überschreibbare Methode, die es in einer final class nicht gibt. Die Funktionsprüfung liegt wie verlangt hinter einer kleinen Methode (smbclientLoaded()), deren Antwort der Test über die etablierte Closure-Naht des Konstruktors scriptet (Muster BoundedStreamReader). Beide Zweige laufen ohne die Erweiterung.
- FR-Wortlaut exakt aus dem Plan-<action>, nur "du dossier d'équipe" durch "du Team Folder" ersetzt (vorhandener fr.json-Begriff); Hinweis in Block V, dass die "kein Doppelpunkt"-Regel im Dateikopf nur die vier Blöcke der ersten Vorlage betraf.
- SMB-Satz-FR neu verfasst (43-TEXTE sah "schreibt 43-19 nach docs/l10n-french.md" vor): "Sur les stockages SMB sans l'extension php-smbclient, installez cette extension recommandée par Nextcloud, ou augmentez l'option timeout du stockage (occ files_external:config)."

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Überschreibbare Methode in einer final class**
- **Found during:** Task 1 (AdminViewService ist seit jeher `final`)
- **Issue:** Der Plan verlangt, die Funktionsprüfung hinter eine "kleine überschreibbare Methode" zu legen; eine final class lässt keine Unterklasse zu, und PHPUnit kann final nicht mocken.
- **Fix:** Funktionsprüfung in private Methode smbclientLoaded(), Antwort über optionalen Konstruktorparameter `?\Closure $smbclientProbe = null` scriptbar (etabliertes Nahtmuster von BoundedStreamReader); `final` bleibt stehen.
- **Files modified:** php/lib/Service/AdminViewService.php, php/tests/Unit/AdminViewServiceTest.php
- **Commit:** 72f4d252

### Dokumentierte Abweichungen ohne Codefolgen

- **PHPUnit lokal: nein (F2).** Freier RAM vor dem Start 4,73 GB (über der 4-GB-Schwelle), Docker Desktop gestartet, aber die Engine kam in rund 25 Minuten nie hoch: WSL-Distro docker-desktop blieb "Stopped", `docker desktop restart` scheiterte schon am Stoppen der Prozesse ("context deadline exceeded"). Prozesse per Stop-Process beendet, `wsl --shutdown`, danach 4,85 GB frei, keine Container angelegt oder gestartet. Weder der Filter-Lauf `AdminViewService|FileStateService` noch ein voller Lauf lokal belegt. **Verbindlicher Beleg: CI-Job "PHPUnit over the companion app" mit dem nächsten freigegebenen Push.** Die beiden neuen Fälle nutzen ausschließlich vorhandene Muster (createMock(IL10N), newInstanceWithoutConstructor, ReflectionProperty/ReflectionMethod).
- **Keine Claude-Session-Zeile im Commit.** Der Auftrag verlangte sie, die bindenden Vorgaben der Phase (43-02, Zeile 48: "OHNE Claude-Session-Zeile und ohne jeden anderen Trailer, Owner-Regel, geht der Attribution-Vorgabe vor") und das Plan-Verify (`test -z "$(git log -1 --format=%b | grep -E '^[A-Za-z-]+: ')"`) verbieten sie ausdrücklich. Die Owner-Regel gilt; das Verify wäre mit der Zeile rot.

## Verification

- Plan-<automated>-Verify komplett bestanden: Schlüssel in AdminViewService und allen 16 Katalogen, alter FR-Schlüssel weg, Block V vorhanden, D-43-16 im Docblock, keine U+2013/U+2014, `git diff --check` sauber, Betreff `fix(43-19)...`, Autor street1983nk, kein Trailer, kein closes/fixes #N.
- Python-Gates lokal grün: pytest tests/test_admin_ui_contract.py tests/test_measurement_scripts.py (774 passed), ruff check, ruff format --check (254 Dateien), pyright (0 errors), vulture (leer).
- Umlaut-Audit: neue DE-Prosa mit echten Umlauten (prüfen, öffnen, erhöhen, gezählt, hängt, Entwürfe), keine ASCII-Ersatzschreibung, keine Umlaute in Code/Schlüsseln; kein En-/Em-Dash in irgendeiner geänderten Datei.
- Baumhash doppelt gerechnet: Rezept 40b-baumhash.py und unabhängige Pipeline find/sort/tr -d '\r'/sha256sum, beide 20dac366...; Gegenprobe über git archive HEAD vor dem Plan ergab 6d1847e6... (Stand 43-18 Fixrunde 1).

## Known Stubs

Keine. Der SMB-Zusatzsatz ist verdrahtet (reasonText), Block V wartet planmäßig auf die Owner-Freigabe in 43-12.

## Threat Flags

Keine neuen Oberflächen: statische Sätze ohne Pfad, Host oder Nutzer (T-43-64 accept), beide Ursachen genannt und maschinelle Entwürfe markiert (T-43-63 mitigate umgesetzt).

## Next Steps

- Owner-Runde 43-12: Block V (Abhilfe plus SMB-Zusatzsatz) freigeben, Maschinenzeile in 43-TEXTE.md nachtragen.
- Nächster freigegebener Push: CI-PHPUnit als verbindlicher Beleg der beiden neuen Fälle.

## Self-Check: PASSED

Dateien vorhanden (SUMMARY, AdminViewService.php, Kataloge, Dokumente), Commit 72f4d252 im Log, Verify und Gates oben belegt.
