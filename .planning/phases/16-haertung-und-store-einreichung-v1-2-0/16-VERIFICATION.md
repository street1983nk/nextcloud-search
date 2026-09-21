---
phase: 16-haertung-und-store-einreichung-v1-2-0
verified: 2026-09-21T23:59:00Z
status: passed
score: 9/9 must-haves verified (7 vollstaendig, 2 ueber ein dokumentiertes, vom Owner angenommenes Override)
overrides_applied: 2
overrides:
  - must_have: "Auflage A1 (Nachfolgefassungen 92c-wechsel.sh und 99d-filter-sortierung.sh) ist vollstaendig erfuellt, inklusive Wirkungsbeleg auf einer Box"
    reason: "Die Phase hat bewusst keine bezahlte Box gefahren (A4 wurde stattdessen ueber den kostenlosen CI-Weg geschlossen). Die beiden Nachfolgefassungen stehen mit eigenen Waechtern (Rueckgabewertpruefung, Abbruchcodes) im Baum, sind byteweise gegen ihre Herkunft geprueft, aber ungefahren. Der Phasenaudit nennt das selbst unter Abschnitt 6 als 'NICHT belegt: die Wirkung'. Owner-Abnahme der gesamten Haertung am Checkpoint 16-13 im Wortlaut 'Abgenommen', nach Vorlage dieses genauen Standes."
    accepted_by: "Owner, im Wortlaut dokumentiert in 16-13-SUMMARY.md und docs/audits/2026-09-phase-16/README.md Abschnitt 6"
    accepted_at: "2026-09-21"
  - must_have: "Auflage A3 (Instrumentierung des inneren Aufrufs) liefert eine Zahl auf Zielhardware fuer die 1,5-Sekunden-Frage (M-01)"
    reason: "Die Instrumentierung selbst ist vollstaendig gebaut (hrtime um den inneren Aufruf, Schwelle, drei Felder, alle vier Fehlerpfade, fuenf Textgate-Faelle, zwei PHPUnit-Faelle). Die Zahl auf Zielhardware fehlt, weil A4 ueber den CI-Weg statt einer neuen Box erfuellt wurde und diese Phase deshalb keine Box gefahren hat, die die Messung haette mitnehmen koennen. Traceability-Tabelle fuehrt M-01 explizit als 'teilerfuellt'. Owner-Abnahme am Checkpoint 16-13 im Wortlaut 'Abgenommen', nach Vorlage dieses genauen Standes."
    accepted_by: "Owner, im Wortlaut dokumentiert in 16-13-SUMMARY.md und docs/audits/2026-09-phase-16/README.md Abschnitt 6"
    accepted_at: "2026-09-21"
---

# Phase 16: Haertung und Store-Einreichung v1.2.0 Verification Report

**Phase Goal:** Die Ergebnisse des Milestones stehen gehaertet, belegt und im Gleichschritt im Store
**Verified:** 2026-09-21T23:59:00Z
**Status:** passed
**Re-verification:** No, initial verification

## Vorbemerkung zur Methode

Diese Verifikation misstraut den SUMMARY-Dateien standardmaessig und prueft
gegen tatsaechlich vorhandene Artefakte, echte CI-Laufergebnisse (per `gh run
view`, unabhaengig gegen die GitHub-API gefahren, nicht aus einer SUMMARY
abgeschrieben) und die beiden lebenden Store-Seiten (per `curl` gegen
apps.nextcloud.com abgerufen). Folgende Laufnummern wurden einzeln gegen die
GitHub-API geprueft: 35594647362, 35603906800, 35612546138, 35612545646,
35618848300, 35617988639, 35586213137. Alle Ausgaenge, Commits und Zweige
stimmen mit den Angaben in REQUIREMENTS.md, ROADMAP.md und den SUMMARY-Dateien
ueberein. Zusaetzlich wurde der annotierte Tag `v1.2.0` lokal aufgeloest
(zeigt auf Commit `f827145`) und alle sieben Laeufe des Tag-Pushes einzeln
aufgelistet.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | DI-11-02/03/05/06 sind abgearbeitet oder dokumentiert entschieden, inklusive des flatternden pgsql-Asts (HTTP 423) | VERIFIED | `flake-register.md` fuehrt den Stamm `mutation-423` mit Fix-Verdikt und Gegenprobe; die enge Wiederholung steht im Workflow-Diff der Phase. DI-11-06 ist mit Zieladresse dokumentiert entschieden (`deferred-items.md`), DI-11-02 mit Zahlen aus dem Phase-15-Bericht dokumentiert entschieden, DI-11-03 als Vorlaufsonde gebaut (`ranked_sides`-Sonde, Begrenzung im Kommentar benannt) |
| 2 | Der BL-F01-Schlusssatz zur Connector-Synergie steht in EN/DE/FR in beiden Haelften, keine Em-Dashes/Backticks/Tabellen | VERIFIED | Satz wortgleich in `php/appinfo/info.xml` und `backend/appinfo/info.xml`, je EN/DE/FR gefunden. Gate-Datei `backend/tests/test_store_metadata.py` existiert. CI-Lauf 35603906800 (main) und Tag-Lauf 35612546138 (v1.2.0, Commit f827145) beide `success` fuer "PHP and store metadata gates", unabhaengig per `gh run view` bestaetigt |
| 3 | Upgrade 1.1.0 auf 1.2.0 ist Ende-zu-Ende in CI bewiesen, Migration `Version001200Date...` vorhanden, Suche nach Sprung nicht stumm | VERIFIED | `php/lib/Migration/Version001200Date20260921000000.php` und `Version001200Date20260921000000Test.php` existieren im Baum. Lauf 35594647362 (main, Commit 73cbca1) `success`; Log enthaelt woertlich "the instance performed the app update: 1.1.0 to 1.2.0" und "all six assurances hold" (Zeilen im Log direkt gelesen, nicht aus einer SUMMARY zitiert). Tag-Lauf 35612546034 (HaRP deploy, v1.2.0) ebenfalls `success` |
| 4 | Die Messzahl steht im Gleichschritt an drei Stellen (README.en.md, beide info.xml) | VERIFIED | `README.en.md` nennt "731.9 MB" nach einem Indexlauf; beide `info.xml` tragen `<version>1.2.0</version>` und denselben Messwert im Beschreibungstext. Ein Gate mit Mutationsfall je Stelle liegt laut `test_store_metadata.py`-Fund vor, gruen im selben CI-Lauf wie Truth 2 |
| 5 | v1.2.0 ist als signiertes App-Paar eingereicht, zweimal HTTP 201 | VERIFIED | Lauf 35618848300 (Store submission, main, Commit f827145) `success`; Log zeigt woertlich "release findling v1.2.0: HTTP 201" und "release findling_backend v1.2.0: HTTP 201". Externe Gegenprobe: `curl https://apps.nextcloud.com/apps/findling` und `.../apps/findling_backend` liefern beide live die Version 1.2.0 mit Downloadlink auf `releases/download/v1.2.0/`. Der erste Dispatch 35617988639 endete tatsaechlich mit HTTP 401 (Log bestaetigt), ist aber als L-16-05 dokumentiert und blockiert den Haken nicht, weil der zweite Lauf ihn traegt |
| 6 | Auflage A1: Nachfolgefassungen 92c und 99d ersetzen die Phase-15-Werkzeuge mit Rueckgabewertpruefung | VERIFIED (Artefakt) / Wirkung ungeprueft, siehe Override | `92c-wechsel.sh` und `99d-filter-sortierung.sh` sind im Baum, mit den im Audit beschriebenen Abbruchcodes 36 und 2. Keine Rohdatei einer Ausfuehrung vorhanden; das ist im Audit selbst als offener Punkt benannt und vom Owner mit vollem Kenntnisstand abgenommen |
| 7 | Auflage A2: Geheimnisregel als Gate ueber `docs/` plus Bereinigung der Altfunde | VERIFIED | Gate-Lauf ueber 405 Dateien unter `docs/`, 55 Faelle, Restliste mit 49 begruendeten Eintraegen. Reichweitenluecke (kein Gate ausserhalb `docs/`) ist als benannte Grenze im Audit dokumentiert, kein stiller Fehlschlag |
| 8 | Auflage A3: Instrumentierung des inneren Aufrufs (M-01) | VERIFIED (Artefakt) / Zielhardware-Zahl fehlt, siehe Override | `hrtime`-Instrumentierung um den inneren Aufruf, Schwelle, drei Felder, vier Fehlerpfade, Text- und PHPUnit-Faelle laut Audit vorhanden. Traceability fuehrt M-01 ausdruecklich als teilerfuellt, nicht als erledigt |
| 9 | Auflage A4: Sprachfaelle ohne Fremdbestand ueber den CI-Weg belegt | VERIFIED | Lauf 35586213137 (Integration, `index-search-e2e (sqlite, ubuntu-24.04-arm)`) `success`, Commit 845c019. Log-Kernaussage laut Audit: "files on the instance before the corpus: 0", "corpus entries: 39", zehn von zehn Sprachfaellen gruen. Owner-Wort am Checkpoint 16-08 im Wortlaut "Zweig a, zustimmen" liegt in `16-08-SUMMARY.md` vor |

**Score:** 9/9 truths verified (7 vollstaendig ohne Einschraenkung, 2 ueber ein explizit vom Owner angenommenes Override)

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `php/lib/Migration/Version001200Date20260921000000.php` | Migration fuer den Minor-Sprung 1.1.0 -> 1.2.0 | VERIFIED | Vorhanden, mit Klassenkommentar zur DI-11-06-Begruendung des Migrationszwangs |
| `php/tests/Unit/Version001200Date20260921000000Test.php` | Testfaelle der Migration | VERIFIED | Vorhanden |
| `backend/tests/test_store_metadata.py` | Gate mit Anzahlpruefung fuer BL-F01-Satz und Messzahl | VERIFIED | Datei existiert im Baum |
| `php/appinfo/info.xml`, `backend/appinfo/info.xml` | Version 1.2.0, BL-F01-Satz EN/DE/FR | VERIFIED | Beide tragen `<version>1.2.0</version>` und den wortgleichen Connector-Satz in allen drei Sprachen |
| `docs/audits/2026-09-phase-16/flake-register.md` | Drei Flake-Staemme mit Kennung, letztem roten Lauf, Gegenprobe, Verdikt | VERIFIED | Vorhanden, inklusive Nachtrag zum nicht tragenden ersten Fix |
| `docs/audits/2026-09-phase-16/README.md` | Phasenaudit mit Haertungsmatrix, Befundliste, A1-A4-Stand, Belegkette Abschnitt 9 | VERIFIED | Vorhanden, alle referenzierten Laufnummern stimmen mit der GitHub-API ueberein |
| `.planning/phases/16-haertung-und-store-einreichung-v1-2-0/deferred-items.md` | Verdikte fuer DI-11-02/03/05/06 und die Phase-15-Restliste | VERIFIED | Vorhanden, jeder Punkt mit Verdikt, keiner mit "spaeter" |
| Git-Tag `v1.2.0` | Annotierter Tag auf dem geprueften Baum | VERIFIED | Zeigt auf Commit `f827145`, sieben gleichzeitig gruene CI-Laeufe am Tag-Push (PHP and store metadata gates, Release archives, Multi-arch image, HaRP deploy, Python gates, Integration, Resilience) |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| Commit 73cbca1 (main) | CI-Lauf 35594647362 | Push-Trigger `deploy-harp.yml` | WIRED | Lauf existiert, `success`, Log enthaelt die sechs Zusicherungen |
| Tag `v1.2.0` | CI-Laeufe 35612545646/35612546138/35612546034/u.a. | Tag-Push-Trigger | WIRED | Sieben Laeufe auf headBranch `v1.2.0`, alle `success` |
| Release-Lauf 35612545646 | Store-Submission-Lauf 35618848300 | signierte Anhaenge -> Release-Route der App-Store-API | WIRED | Zweiter Dispatch traegt den Haken (HTTP 201 zweimal), erster (35617988639) ist dokumentiert und nicht der tragende Lauf |
| Store-Submission | apps.nextcloud.com | Store-API -> oeffentliche App-Seite | WIRED | Externe Live-Abfrage zeigt 1.2.0 auf beiden App-Seiten mit Downloadlink auf `v1.2.0` |
| Migration `Version001200Date...` | `oc_appconfig.backend_app_version` | `IOutput`/`ExAppService::lockstep` | WIRED (laut Klassenkommentar und Testlauf, siehe Truth 3) | Log des Upgrade-Beweises zeigt den Zustandswechsel 1.1.0 -> 1.2.0 explizit |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| HART-01 | 16-01, 16-04, 16-13 | DI-11-02/03/05/06 abgearbeitet oder dokumentiert entschieden | SATISFIED | Flake-Register, deferred-items.md, Vorlaufsonde im Baum, Owner-Abnahme "Abgenommen" |
| HART-02 | 16-11, 16-12 | BL-F01-Schlusssatz in EN/DE/FR in beiden Haelften, Gate-konform | SATISFIED | Satz in beiden info.xml verifiziert, Gate-Laeufe 35603906800 und 35612546138 gruen |
| REL-02 | 16-07, 16-09, 16-12, 16-14 | Migration, Upgrade-Beweis in CI, Messzahl im Gleichschritt, Submission 2x HTTP 201 | SATISFIED | Migrationsdatei vorhanden, Upgrade-Lauf 35594647362 gruen mit Wortlautbeleg, Messzahl an drei Stellen gefunden, Submission-Lauf 35618848300 mit zweimal HTTP 201 im Log bestaetigt |
| A1 (Owner-Auflage, Phase 15) | 16-03, 16-13 | Nachfolgefassungen 92c/99d | SATISFIED mit Override | Artefakt vorhanden, Wirkung ungeprueft, vom Owner explizit so angenommen |
| A2 (Owner-Auflage, Phase 15) | 16-02, 16-05, 16-13 | Geheimnis-Gate ueber docs/ | SATISFIED | Gate aktiv, Reichweitenluecke benannt, M-16-02 in derselben Phase gefunden und behoben |
| A3 (Owner-Auflage, Phase 15) | 16-06, 16-13 | Instrumentierung des inneren Aufrufs (M-01) | SATISFIED mit Override | Instrumentierung gebaut, Zielhardware-Zahl fehlt, vom Owner explizit so angenommen |
| A4 (Owner-Auflage, Phase 15) | 16-08, 16-13 | Sprachfaelle ohne Fremdbestand | SATISFIED | CI-Lauf 35586213137 gruen, Owner-Wort "Zweig a, zustimmen" |

Keine Waise: HART-03 ist laut REQUIREMENTS.md bewusst Phase 12 zugeordnet und
fliesst nur in die Release-Entscheidung dieser Phase ein, ohne hier erneut als
eigene Anforderung zu zaehlen. Alle 17 Requirements des Milestones sind laut
REQUIREMENTS.md-Traceability-Tabelle abgehakt, keine Doppelzuordnung.

### Anti-Patterns Found

Keine TBD/FIXME/XXX-Marker in den in dieser Phase geaenderten Kernartefakten
(Migration, Store-Gate-Test, beide info.xml, README.en.md, Audit-Verzeichnis).
Die einzigen im Audit selbst dokumentierten "Nicht behoben"-Punkte (A1-Wirkung,
A3-Zielhardware-Zahl, drei LOW-Befunde L-16-01/03/04, ein weiterhin offener
Flake-Stamm `parity-login`) tragen alle ein Verdikt und eine Zieladresse in
`deferred-items.md` und sind damit keine stillen Luecken.

### Human Verification Required

Keine Punkte identifiziert. Alle fuenf Erfolgskriterien der Phase sowie die
vier Owner-Auflagen sind entweder vollstaendig durch unabhaengig nachgefahrene
CI-Laeufe und externe Store-Abfragen belegt, oder als benannte, vom Owner mit
vollem Kenntnisstand angenommene Grenzen dokumentiert (siehe Overrides oben).

### Gaps Summary

Keine Luecken gefunden, die nicht bereits im Phasenaudit selbst benannt und
vom Owner am Checkpoint 16-13 ("Abgenommen") sowie am Checkpoint 16-08
("Zweig a, zustimmen") angenommen wurden. Die beiden Punkte mit Override
(A1-Wirkungsbeleg, A3-Zielhardware-Zahl) sind bewusste, dokumentierte
Terminentscheidungen und keine uebersehenen Defekte: die Instrumentierung und
die Nachfolgefassungen stehen im Baum, nur die Messung auf echter Hardware
steht aus, weil diese Phase bewusst den kostenlosen CI-Weg statt einer
zweiten bezahlten Box gewaehlt hat.

---

*Verified: 2026-09-21T23:59:00Z*
*Verifier: Claude (gsd-verifier)*
