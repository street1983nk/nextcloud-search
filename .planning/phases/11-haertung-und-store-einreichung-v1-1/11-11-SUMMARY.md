---
phase: 11-haertung-und-store-einreichung-v1-1
plan: 11
subsystem: release
tags: [release, store, rel-01, d-10, d-11, v2-a, di-11-06, ghcr, upgrade]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: 11-VORENTSCHEIDE.md, Entscheid v2-a vom 10.09.2026, das Versionsfenster bleibt 33 bis 35
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: die Textabnahme (Fassung B) und das FR-Gate in beiden Teilen, aus 11-05 und 11-09
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: den Auditbericht mit critical 0 und high 0, aus 11-10
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: den Release-Asset-Modus und den Upgrade-Block von deploy-harp.yml, aus 11-04 und 11-07
provides:
  - "v1.1.0 im Nextcloud App Store, beide Haelften, je mit HTTP 201 belegt"
  - "das GitHub-Release v1.1.0 mit genau vier signierten Assets"
  - "ghcr.io/street1983nk/findling_backend:1.1.0 als Manifestindex mit linux/amd64 und linux/arm64"
  - "die Migration Version001100Date20260911000000, die eine veraltete Versionsmarke beim App-Update verwirft"
  - "der Angebot-anfordern-Kontakt in allen sechs Store-Texten und drei READMEs"
  - "DI-11-06 mit Zieladresse v1.2"
affects: [11-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Beweis, der zum ersten Mal wirklich greift, findet Fehler: der Upgrade-Block lief fuenf Releases lang in ERROR_UP_TO_DATE und deckte mit dem ersten echten Minor-Sprung drei Befunde auf"
    - "Ein Gate, das ein Ereignis einmal als Beleg und einmal als Fehler zaehlt, misst die falsche Groesse; die Zaehlung gehoert hinter die Ankuendigung, nicht davor"
    - "Eine Reparatur, die auf einem Pfadtest beruht, braucht eine Obergrenze und eine Anti-Vacuity-Klausel, sonst raeumt ein falsches Arbeitsverzeichnis die halbe Instanz leer"
    - "Eine Migration, die eine veraltete Marke findet, verwirft sie und raet keine neue: eine geratene Version haette die Drift-Erkennung ausgehebelt statt sie zu bedienen"
    - "Eine berichtete Messzahl wird nicht umgeschrieben; der heutige Baum bekommt eine zweite Konstante (PHP_FILES_TODAY neben PHP_FILES)"
    - "Vor der Store-Einreichung wird der Manifestindex geprueft und nicht angenommen (Pitfall 10, T-11-48)"

key-files:
  created:
    - php/lib/Migration/Version001100Date20260911000000.php
    - php/tests/Unit/Version001100Date20260911000000Test.php
  modified:
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - .github/workflows/deploy-harp.yml
    - php/tests/Unit/ExAppServiceTest.php
    - backend/tests/test_measurement_scripts.py
    - README.md
    - README.en.md
    - README.fr.md
    - docs/store-listing.md
    - .planning/phases/11-haertung-und-store-einreichung-v1-1/deferred-items.md

key-decisions:
  - "Das Versionsfenster bleibt bei min 33 max 35 (Entscheid v2-a vom 10.09.2026). Der Bump beruehrt nur die drei Versionsstellen, kein Fenster, keine Matrix"
  - "Der Tag sitzt auf 891bc6d und nicht auf dem Bump-Commit: die drei Befunde des Upgrade-Beweises wurden vor dem Tag behoben, wie vom Owner am 11.09. entschieden (Weg a)"
  - "Befund A wird nicht mit einer hoeheren Schwelle erledigt, sondern mit der richtigen Messgroesse. Die Zeilen vor der Rueckzugsankuendigung haengen am Zustand des Containers (drei mit nichts in Arbeit, sechs mit einer Datei in Arbeit), die Behauptung des Schrittes ist aber die Stille danach"
  - "Befund B wird an der Ursache behoben: alwaysEnabled von core/shipped.json nennt viewer, apps/ des Zweiges traegt es nicht. Nur alwaysEnabled wird bereinigt, defaultEnabled ausdruecklich nicht, weil es den Fehler nicht ausloest und zwei Dutzend Namen betraefe"
  - "Befund C ist ein Produktfehler und wurde als solcher gemeldet statt repariert: der Owner entschied. backend_app_version ueberlebte das App-Update und liess die Suche ueber eine Drift urteilen, die es nicht gab"
  - "Die Migration verwirft die Marke und schreibt nie eine Version. Eine geratene Version haette einer Instanz mit wirklich alterem Container Einigkeit bescheinigt, und das ist der eine Fehler, den die Drift-Erkennung verhindern soll"
  - "DI-11-06 wird nicht in dieser Phase gebaut: die Version in der Suchantwort mitzufuehren ist eine Protokollaenderung an beiden Haelften, drei Tage vor der Abgabe, auf genau dem Pfad, auf dem der Fehler sass. Zieladresse v1.2"
  - "Der Angebot-anfordern-Kontakt steht als Text und nicht als mailto-Verweis: dass der Store Markdown-Links rendert, ist belegt, dass er mailto sauber ausgibt, nicht"
  - "Die READMEs nennen die bezahlten Zusatzmodule als geplant und nicht als verfuegbar; ein Fake-Door-Text, der etwas als gebaut ausgibt, waere in dem Moment gelogen, in dem jemand antwortet"

patterns-established:
  - "Die erste Handlung bei einem roten Ast ist die Wiederholung, nicht die Fehlersuche; erst wenn sie Zeile fuer Zeile dasselbe liefert, ist es ein Befund"
  - "Eine Workflow-Aenderung wird vor dem Push gegen einen lokal nachgebauten Zustand gefahren (alle drei Server-Zweige plus zwei gebaute Fehlerfaelle)"
  - "Eine Diagnose-Ergaenzung aendert kein Verhalten: dieselbe Pruefung, dasselbe Budget, derselbe Ausgang, nur Ausgaben dazu"

requirements-completed: [REL-01]

# Metrics
duration: 3h50min
completed: 2026-09-11
---

# Phase 11 Plan 11: Die Abgabe Summary

v1.1.0 steht als signiertes App-Paar im Nextcloud App Store, beide Hälften mit HTTP 201 belegt, und der Weg dahin hat drei Fehler im Upgrade-Pfad gefunden, von denen einer das Produkt betraf.

## Was gebaut wurde

**Der Versionsbump**, drei Stellen in einem Commit: `php/appinfo/info.xml:113`, `backend/appinfo/info.xml:136` und der `<image-tag>` daneben, alle auf `1.1.0`. Das Versionsfenster blieb unangetastet bei `min-version="33" max-version="35"`, Entscheid v2-a.

**Drei Befunde, die erst dieser Bump sichtbar gemacht hat.** Der Upgrade-Block von `deploy-harp.yml` lief fünf Releases lang in `ERROR_UP_TO_DATE` hinaus, weil alle bisherigen Sprünge Patches waren. Mit dem ersten echten Minor-Sprung greift er wirklich, und dabei fiel auf:

- **Befund A:** Der Schritt `Store uninstall 6` zählte die Warnzeilen vor der Rückzugsankündigung und hielt damit den Container an einer Zahl fest, die sein Zustand entscheidet, nicht sein Verhalten. Gemessen: drei Zeilen mit nichts in Arbeit, sechs mit einer Datei in Arbeit, Schwelle fünf. Gezählt wird jetzt die Stille nach der Ankündigung.
- **Befund B:** `checkAppsRequirements()` von Nextcloud wirft für eine aktivierte Shipped-App, deren appinfo fehlt. `core/shipped.json` führt `viewer` unter `alwaysEnabled`, und `apps/` der Zweige stable33 bis 35 trägt es nicht, weil die Bundle-Apps eigene Repositories haben. Der neue Schritt `Store upgrade 3b` bereinigt genau diese Behauptung.
- **Befund C, ein Produktfehler:** `oc_appconfig.backend_app_version` überlebte das App-Update. Der Companion stand auf 1.1.0, AppAPI meldete den Container als 1.1.0, die Marke sagte 1.0.3, und jede Suche antwortete mit null Treffern und `FAILURE_VERSION_DRIFT`. Behoben durch die Migration `Version001100Date20260911000000`, die die veraltete Marke verwirft und ausdrücklich keine neue rät.

**Der Angebot-anfordern-Kontakt**, auf Owner-Auftrag vom selben Tag: je eine Zeile in allen sechs Store-Texten und ein Enterprise-Abschnitt in allen drei READMEs, dreisprachig, mit `admin@infranode.dev` als Text.

## Die Belege

| Was | Beleg |
| --- | --- |
| Tag | `v1.1.0` auf `891bc6d` |
| Release | Lauf **34573687101**, genau vier Assets |
| Assets | `findling.tar.gz` (282.432 B), `findling.tar.gz.sig` (684 B), `findling_backend.tar.gz` (28.524 B), `findling_backend.tar.gz.sig` (684 B) |
| ghcr, vor der Einreichung geprüft | `application/vnd.oci.image.index.v1+json` mit `linux/amd64` (`sha256:a2b9aef78e321d582983…`) und `linux/arm64` (`sha256:ae58d93005dc18849c3b…`), anonym abgefragt |
| Submission | Lauf **34573857157**, success |
| HTTP-Codes | `release findling v1.1.0: HTTP 201`, `release findling_backend v1.1.0: HTTP 201` |
| Gegenprobe | `apps.nextcloud.com/apps/findling` und `/apps/findling_backend` nennen beide 1.1.0 |
| Upgrade-Beweis | Lauf **34571130221**, alle sieben Upgrade-Schritte success: `installed_version went from 1.0.3 to 1.1.0`, `occ upgrade answered 0`, `the container after the upgrade answers the canary search`, sechs Nachher-Zusicherungen bestanden |

**Die sieben Tag-Läufe, alle success:** Release 34573687101, Multi-arch 34573687150, PHP 34573687100, Python 34573687142, Integration 34573687122, Resilience 34573687076, HaRP 34573687074.

**Erfolgskriterium 5** ist damit erfüllt, und zwar ohne Zutun: `store-submit.yml` übergibt die URL genau des Assets, das `release.yml` signiert und hochgeladen hat. Es gibt keinen zweiten Bau.

## Abweichungen vom Plan

### Automatisch behoben

**1. [Rule 1 - Bug] Die Rückzugszählung maß den Zustand statt des Verhaltens**
- **Gefunden bei:** Task 1, im CI-Lauf des Release-Commits
- **Problem:** `Store uninstall 6` und `Uninstall 6` zählten ab vor der Rückzugssequenz; die Zeilen über verlorene Arbeit hängen daran, ob beim Entfernen gerade eine Datei in Arbeit war
- **Lösung:** Zählung hinter die Ankündigung verlegt, 60 s Fenster, Toleranz eine Zeile; die alte Zahl bleibt im Protokoll sichtbar
- **Dateien:** `.github/workflows/deploy-harp.yml`
- **Commit:** `8283d6e`

**2. [Rule 3 - Blocker] Der Upgrade starb an einer Shipped-App, die der Checkout nicht mitbringt**
- **Gefunden bei:** Task 1, im selben Lauf
- **Problem:** `alwaysEnabled` von `core/shipped.json` nennt `viewer`, das Verzeichnis fehlt, `checkAppsRequirements()` wirft. Der erste Anlauf suchte in `oc_appconfig` und fand nichts, weil alwaysEnabled-Apps dort nicht stehen
- **Lösung:** `Store upgrade 3b` bereinigt `alwaysEnabled` auf die Apps, die wirklich da sind, mit Anti-Vacuity-Klausel (`apps/files`) und Obergrenze (höchstens drei), beide gegen gebaute Fehlerfälle geprüft
- **Dateien:** `.github/workflows/deploy-harp.yml`
- **Commits:** `8283d6e` (Fehlversuch), `4df64f5` (Ursache getroffen)

**3. [Rule 1 - Bug] Das Messgate zählte 58 PHP-Dateien, der Baum hatte 60**
- **Gefunden bei:** Task 3, nach dem Anlegen von Migration und Test
- **Lösung:** `PHP_FILES_TODAY` neben `PHP_FILES`, dieselbe Trennung, die der Baumhash seit dem 10.09. hat; beide Rohwerte werden jetzt gegen `40b-baumhash.txt` geprüft
- **Dateien:** `backend/tests/test_measurement_scripts.py`
- **Commit:** `891bc6d`

### Dem Owner vorgelegt statt selbst entschieden

**4. [Rule 4 - Produktfehler] Die Suche urteilte über eine Drift, die es nicht gab**
- **Gefunden bei:** Task 3, nach einer Diagnose-Ergänzung ohne Verhaltensänderung (`d054cc2`)
- **Warum vorgelegt:** Der Fehler saß im Produktcode auf dem Suchpfad, unmittelbar vor einer nicht mehr editierbaren Store-Abgabe
- **Entscheid:** Weg a, beheben vor der Abgabe, mit vorgelegtem Diff-Plan
- **Lösung:** Migration `Version001100Date20260911000000`, sechs PHPUnit-Fälle, bestehender Negativtest unverändert
- **Commit:** `891bc6d`

### Zusatzauftrag

**5. Der Angebot-anfordern-Kontakt**, Owner-Auftrag vom 11.09., Ort und Adresse vom Owner entschieden, Wortlaute am Freigabe-Checkpoint vorgelegt und abgenommen.
- **Commits:** `fb371a0` (Texte), `eba04b1` (Abnahme)

## Was offen bleibt

**DI-11-06**, Zieladresse v1.2: Zwischen einem Update und dem ersten Blick auf die Einstellungsseite hat die Suche kein Drift-Urteil, weil die Marke verworfen wurde und nur `GET /status` sie füllt. Das ist derselbe Zustand, in dem jede Instanz steht, deren Einstellungsseite nie geöffnet wurde. Der Weg dahin ist, die Version in der Antwort mitzuführen, die die Suche ohnehin holt.

**Der Merker für jeden weiteren Minor-Sprung:** Solange die Marke so gepflegt wird, braucht jeder Minor eine Migration nach dem Muster von `Version001100Date20260911000000`. Der Satz steht im Klassenkommentar der Migration, weil das die Datei ist, die jemand liest, wenn er die nächste schreibt.

**Nicht im Repository:** das Flag "Enterprise support" im Store-Konto, für beide Findling-Apps, nach dem Muster des Connectors vom 24.08.2026. Erledigt der Owner im Store-Konto.

**Nachtrag zur Gegenprobe:** Die große `apps.json` unter `?version=34.0.0` führte kurz nach der Einreichung noch bis 1.0.3. Das ist ihr Cache; die App-Seiten beider Hälften nennen 1.1.0. Die Datei ist 33 MB und wurde nicht im Minutentakt abgefragt.

## Authentifizierungs-Gates

Keine. Alle Geheimnisse blieben im GitHub-Secret-Store, `release.yml` und `store-submit.yml` haben sie nie verlassen.

## Self-Check: PASSED

Alle genannten Dateien liegen im Baum, alle acht Commits stehen in der Historie,
und `git rev-list -n 1 v1.1.0` nennt `891bc6d`, also genau den Commit, auf den
der Tag laut Freigabe gehoert.
