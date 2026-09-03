---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 02
subsystem: infra
tags: [nextcloud, repair-steps, occ, appconfig, migrations, pytest-gate, uninstall]

# Dependency graph
requires:
  - phase: 02-suche-und-index
    provides: Queue-Tabelle und QueueMapper::TABLE_NAME
  - phase: 03-aktualit-t-und-ocr
    provides: SubtreeExpandJob, FileStateService, Reconcile-Kette
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: ScanStatsService, SettingsService, ExclusionService, IndexCommand und DiagnoseCommand als Befehlsmuster
provides:
  - "Gemessener Befund: Nextcloud fuehrt repair-steps/uninstall beim Disable aus, nicht beim Remove"
  - "AppUninstallStep mit Absichtsmarke purge_intent und Aufrufzaehler purge_step_calls"
  - "PurgeService als einzige Raeumroutine: drei Tabellen, appconfig, drei Hintergrundjobs, Migrations-Buchfuehrung"
  - "occ findling:purge mit --arm, --disarm und --now, Lesen als Vorgabe"
  - "backend/tests/test_uninstall_contract.py als Textgate ueber die Reihenfolge"
  - "docs/uninstall.md: Disable gegen Remove, Index-Volume, Rueckstaende, Reihenfolge"
affects: [05-08 Deploy-Job und NC-Versionsmatrix, 05-17 Versions-Bump auf 1.0.0, Store-Einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Absichtsmarke im appconfig als Bedingung eines Lifecycle-Schritts (Gegenstueck zu AppInstallStep::FIRST_INDEX_SCHEDULED)"
    - "Eine Raeumroutine, zwei Aufrufer: Repair-Step und occ-Befehl delegieren beide an denselben Service"
    - "Messen statt behaupten: der Lifecycle-Befund steht als Zaehlerprotokoll in der Betriebsdoku"

key-files:
  created:
    - php/lib/Repair/AppUninstallStep.php
    - php/lib/Service/PurgeService.php
    - php/lib/Command/PurgeCommand.php
    - backend/tests/test_uninstall_contract.py
    - docs/uninstall.md
  modified:
    - php/appinfo/info.xml
    - docs/testing.md

key-decisions:
  - "Die Raeumung nimmt auch die Zeilen der App in der Kerntabelle migrations mit, weil sie sonst ein Rueckstand sind UND ein Re-Enable ein Schema ohne Tabellen vorfindet, das Nextcloud fuer aktuell haelt"
  - "--now nimmt enabled mit und schaltet die App damit ab; das steht im Hilfetext und in der Ausgabe statt als Ueberraschung"
  - "Die Absichtsmarke wird von dem Lauf verbraucht, den sie ausloest, weil sie im appconfig der App liegt: einmal scharf, nie zweimal"
  - "Die Store-Validierung wurde lokal ueber lxml gegen die in php.yml gepinnte XSD nachvollzogen, weil xsltproc und xmllint auf dieser Maschine fehlen"

patterns-established:
  - "Kanarienvogel-Schritt: ein Lifecycle-Schritt wird zuerst als Zaehler eingebaut und gemessen, bevor er etwas tut"
  - "Textgate ueber Reihenfolge: Befundsammler plus Antivakuitaetsklausel plus saubere und schmutzige Probe"

requirements-completed: [PKG-04]

# Metrics
duration: 95min
completed: 2026-09-03
---

# Phase 5 Plan 02: Uninstall-Cleanup mit Absichtsmarke Summary

**Gemessen statt behauptet: Nextcloud fuehrt den Uninstall-Repair-Step bei jedem Disable aus, deshalb raeumt Findling nur nach ausdruecklicher Absicht, ueber genau eine Routine, rueckstandsfrei und beliebig oft wiederholbar.**

## Performance

- **Duration:** ca. 95 min
- **Tasks:** 3 von 3
- **Files modified:** 7 (5 neu, 2 geaendert)

## Accomplishments

- **Der wichtigste Einzelbefund der Recherche ist jetzt Messwert und nicht Quellcodelektuere.** Auf Nextcloud 34.0.3 laeuft der Uninstall-Schritt beim Disable (Zaehler von nicht gesetzt auf 1), beim Enable nicht, bei `app:remove --keep-data` nicht und bei `app:remove` ohne Flag erneut. Die Kette samt Zaehlerstaenden und Serverversion steht in `docs/uninstall.md`.
- **Ein Disable verliert nichts.** Gemessen vor und nach dem Befehl: drei Tabellen, fuenf appconfig-Werte, ein Job, jeweils unveraendert.
- **Eine ausdrueckliche Absicht raeumt vollstaendig und wiederholbar.** Nach `occ findling:purge --arm --no-interaction` plus `occ app:disable findling`: null Tabellen, null appconfig-Werte, null Jobs. Ein zweiter Lauf mit gesetzter Marke und drei abwesenden Tabellen lief bei geleertem Protokoll durch und hinterliess null Bytes Log.
- **Die Raeumung ist umkehrbar.** `occ app:enable findling` legt die drei Tabellen wieder an, der Install-Schritt plant die Erstindexierung erneut, `occ findling:index` antwortet ohne Fehler.
- **Ein Textgate haelt die Trennung fest**, mit sechs Selbsttests gegen schmutzige Proben und einer Antivakuitaetsklausel, die durch Umbenennen einer Quelldatei ausprobiert wurde (2 statt 0 Fehlschlaege, also rot und nicht gruen).

## Task Commits

1. **Task 1: Kanarienvogel-Step, der zaehlt, wann Nextcloud ihn ruft** , `79b1878` (feat)
2. **Task 2: Eine Raeumroutine, zwei Aufrufer, Absicht als Bedingung** , `e5acba6` (feat)
3. **Task 3: Textgate plus die vier Faelle in der Doku** , `275e3ba` (test)
4. **Nachtrag: das neue Gate in der Gate-Landschaft** , `c15666c` (docs)

## Files Created/Modified

- `php/lib/Repair/AppUninstallStep.php` , Uninstall-Schritt: ohne Marke ein Nichtstun mit Logzeile, mit Marke Delegation an die eine Routine; alles in `try`/`catch (\Throwable)`, nie ein Abbruch; Aufrufzaehler `purge_step_calls` als Messinstrument
- `php/lib/Service/PurgeService.php` , die einzige Raeumroutine. `plan()` sagt, was verschwinden wuerde, `run()` raeumt in der zwingenden Reihenfolge: drei Jobs, dann je Tabelle `tableExists` vor `dropTable`, dann die Migrations-Zeilen, zuletzt `IAppConfig::deleteApp`
- `php/lib/Command/PurgeCommand.php` , `occ findling:purge`. Ohne Option nur lesen, `--arm` setzt die Absicht, `--disarm` nimmt sie zurueck, `--now` raeumt sofort; Bestaetigung nach dem Muster `IndexCommand::confirm()`, nicht interaktiv gilt als bestaetigt; Ausgabe nennt Tabellennamen und Zahlen, nie einen Pfad
- `php/appinfo/info.xml` , `uninstall`-Eintrag im einzeiligen `repair-steps`-Block, dritter `command`-Eintrag im einzeiligen `commands`-Block, Begruendung im umgebenden Kommentar; Versionszeile unangetastet bei 0.3.0
- `backend/tests/test_uninstall_contract.py` , Textgate: Markenabfrage vor jeder Delegation, kein `dropTable`/`deleteApp` im Schritt, `catch (\Throwable)` vorhanden und kein Abbruch, `tableExists` vor jedem `dropTable`, `deleteApp` genau einmal und nach der letzten Tabelle, alle drei Jobklassen, keine Tabellennamen als Literal, beide info.xml-Bloecke je einzeilig
- `docs/uninstall.md` , die Messung als Beweis, dann vier Abschnitte mit je einer Frage und je ihrer Grenze
- `docs/testing.md` , das neue Gate in der Gate-Landschaft, mit dem was es nicht beweist

## Decisions Made

- **Migrations-Buchfuehrung gehoert zur Raeumung.** Siehe Deviation 1. Ohne sie ist die Entfernung nicht rueckstandsfrei und ein Re-Enable ergibt eine kaputte App.
- **`--now` schaltet die App ab, und das wird ausgesprochen.** `deleteApp` nimmt `enabled` mit. Statt das zu verstecken oder `enabled` kuenstlich zu erhalten (was eine zweite Wahrheit ueber den Zustand der App waere), sagen Hilfetext und Ausgabe den Weg zurueck: `occ app:enable findling`.
- **Die Absichtsmarke ist Einmalgebrauch.** Sie liegt im appconfig der App und verschwindet mit ihm. Ein zweites Disable ohne neues `--arm` raeumt nichts. Das ist die sichere Richtung des Fehlers.
- **Store-Validierung lokal ueber lxml.** `xsltproc` und `xmllint` gibt es auf dieser Maschine nicht, `lxml` ist im Backend gepinnt und traegt dieselben libxslt und libxml2. Beide `info.xml` wurden durch die gepinnte `pre-info.xslt` geschickt und gegen die gepinnte `info.xsd` (APPSTORE_SHA `5c4373d7`) validiert: beide gueltig. Die XSD bestaetigt ausserdem die Reihenfolge `install` vor `uninstall` als `xs:sequence`.
- **Der Messcontainer war ein eigener, ohne Bind-Mount.** Siehe Issues: `occ app:remove` loescht das App-Verzeichnis, ein Bind-Mount haette den Worktree geleert.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Die Raeumung nimmt die Migrations-Buchfuehrung der App mit**

- **Found during:** Task 2 (Messung der Wiederherstellung nach der Raeumung)
- **Issue:** Nach `--arm` plus `app:disable` waren Tabellen, appconfig und Jobs weg, aber `occ app:enable findling` legte die Tabellen **nicht** wieder an. Gemessen: die fuenf Zeilen der App in der Kerntabelle `oc_migrations` ueberleben die Raeumung, Nextcloud haelt das Schema damit fuer aktuell und fuehrt die Migrationen nie erneut aus. Die App kommt kaputt zurueck, und kein occ-Kommando setzt das gerade. Zusaetzlich sind diese Zeilen selbst ein Rueckstand, den D-18 verbietet. Der Plan hatte die Wiederherstellung als Akzeptanzkriterium angenommen; die Messung hat die Annahme widerlegt.
- **Fix:** `PurgeService` entfernt zwischen den Tabellen und dem appconfig auch die Zeilen der App in `migrations`, ueber den Query Builder (dialektneutral, kein rohes SQL) und ausschliesslich mit `app = 'findling'` als Bedingung. `plan()` und die Befehlsausgabe fuehren die Zahl als eigene Zeile `migration records`, damit die Raeumung nichts Unangekuendigtes tut. Begruendung als Kommentar im Klassen-Docblock.
- **Files modified:** php/lib/Service/PurgeService.php, php/lib/Command/PurgeCommand.php
- **Verification:** Nach dem Fix erneut gemessen: Raeumung auf null, danach `occ app:enable findling` liefert wieder drei Tabellen, einen Job und vier appconfig-Werte, `occ findling:index` antwortet ohne Fehler. Gegenprobe vor dem Fix von Hand nachgestellt: erst nach dem Loeschen der fuenf Zeilen legte ein Disable/Enable die Tabellen wieder an.
- **Committed in:** `e5acba6` (Task-2-Commit)

**2. [Rule 2 - Missing Critical] Die Nebenwirkung von `--now` steht im Hilfetext**

- **Found during:** Task 2 (Messung von `--now`)
- **Issue:** `--now` war als "raeumen, ohne die App zu entfernen" beschrieben. Gemessen schaltet es die App zusaetzlich ab, weil `enabled` zu den Werten gehoert, die `deleteApp` mitnimmt. Ein Admin haette den Befehl nach der Beschreibung gerufen und die Suche verloren, ohne zu wissen warum.
- **Fix:** Hilfetext der Option und Ausgabe nach dem Lauf sagen es ausdruecklich und nennen den Weg zurueck. `docs/uninstall.md` fuehrt es als eigenen Absatz.
- **Files modified:** php/lib/Command/PurgeCommand.php, docs/uninstall.md
- **Verification:** `occ findling:purge --now --no-interaction` gefahren, App danach unter "Disabled" gelistet, `occ app:enable findling` stellt drei Tabellen und den Job wieder her.
- **Committed in:** `e5acba6` und `275e3ba`

### Additions outside the plan's file list

**3. [Rule 2 - Consistency] `docs/testing.md` nennt das neue Gate**

- **Issue:** `docs/testing.md` ist die dokumentierte Gate-Landschaft dieses Repos und listet jedes Textgate mit dem, was es beweist und was nicht. Ein Gate, das dort fehlt, macht die Seite unvollstaendig.
- **Fix:** Eine Zeile in der Gate-Tabelle, mit dem ausdruecklichen Zusatz, dass das Gate nichts darueber sagt, ob die Raeumung funktioniert (das ist die Messung in `docs/uninstall.md`).
- **Committed in:** `c15666c`

---

**Total deviations:** 3 auto-fixed (2 missing critical, 1 consistency)
**Impact on plan:** Deviation 1 ist die Voraussetzung dafuer, dass das Erfolgskriterium ueberhaupt erreichbar ist; ohne sie waere die Raeumung eine Einbahnstrasse in eine kaputte Installation. Deviation 2 und 3 sind Ehrlichkeit gegenueber dem Admin und der eigenen Doku. Kein Scope Creep: keine neue Abhaengigkeit, keine neue Route, keine neue Schreibroute in den Container.

## Issues Encountered

- **`occ app:remove` loescht das App-Verzeichnis, und das Verzeichnis war der Worktree.** Der laufende Dev-Stack (`scripts/dev/compose.yaml`) mountet `../../php` aus dem Hauptcheckout; ein Messlauf dagegen haette in den Hauptcheckout geschrieben, und ein Bind-Mount des Worktrees waere von `Installer::removeApp()` mitsamt Inhalt geloescht worden. Geloest mit einem eigenen Messcontainer `findling-wt0502` auf Port 8095, in dem die App per `docker cp` als container-eigene Kopie liegt, nie als Mount. Container und Volume nach der Messung entfernt; die Container des Hauptstacks und des Nachbaragenten blieben unberuehrt.
- **`app:remove` scheiterte zuerst mit "Cannot write into apps directory".** Ursache war nicht die App, sondern `/var/www/html/custom_apps` als root-eigenes Verzeichnis im Image: der Webserver-Nutzer darf den Eintrag darin nicht entfernen. Nach `chown www-data` lief die Kette durch. Ein reiner Eigenschaft des Messaufbaus, kein Befund ueber Findling.
- **Git Bash schreibt Pfade um.** Jeder `docker exec`-Aufruf mit `/var/www/html/...` landete als `C:/Program Files/Git/var/www/html/...` im Container. `MSYS_NO_PATHCONV=1` im Messskript loest es.
- **`POLL_COOLDOWN_START_SECONDS` liess sich nicht per Namenssuche finden**, weil der Poller den Wert ueber ein aufgeloestes Konfigurationsobjekt liest. Relevanz: die Aussage in `docs/uninstall.md` zum Verhalten des Containers ohne Companion wurde erst nach dem Lesen von `worker/poller.py` geschrieben und nennt die gemessenen Grenzen 15 bis 120 Sekunden plus eine Protokollzeile je Durchgang, statt einen "Rueckzugspfad" zu behaupten, den die Recherche nur gefordert hatte.

## Verification

- `cd backend && uv run python -m pytest -q` , 790 passed, 11 skipped
- `cd backend && uv run ruff check .` , All checks passed
- `cd backend && uv run ruff format --check .` , 79 files already formatted
- `cd backend && uv run pyright` , 0 errors, 0 warnings, 0 informations
- `cd backend && uv run vulture src tests --min-confidence 80` , keine Funde
- Alle PHP-Dateien unter `php/lib` , `php -l` im Container, 0 Dateien mit Fehlern
- Beide `info.xml` , gepinnte `pre-info.xslt` plus gepinnte `info.xsd`, beide gueltig
- Kein Em-Dash (U+2014) und kein En-Dash (U+2013) in allen sieben Dateien
- Antivakuitaetsklausel , mit umbenannter `PurgeService.php` schlaegt das Gate fehl (2 failed, 13 passed), danach wieder 15 passed

## Known Stubs

Keine. Alle drei Klassen sind vollstaendig verdrahtet und auf einer laufenden Instanz gefahren.

## Threat Flags

Keine neue Angriffsflaeche gegenueber dem `<threat_model>` des Plans. Ein Hinweis zur Einordnung von T-05-08 (Tampering, `dropTable` auf einer fremden Tabelle): die Raeumung fasst mit `migrations` jetzt eine Kerntabelle an, die nicht dieser App gehoert. Sie entfernt daraus ausschliesslich **Zeilen** mit `app = 'findling'` und nie die Tabelle selbst, ueber den Query Builder statt ueber SQL-Text. Die drei eigenen Tabellen kommen weiterhin ausschliesslich aus Konstanten, und das Gate haelt fest, dass ihre Namen nicht als Zeichenkette in der Routine stehen.

## User Setup Required

Keine.

## Next Phase Readiness

- **Fuer Plan 05-08 (Deploy-Job und NC-Versionsmatrix)** liegen drei benannte offene Punkte bereit, alle in `docs/uninstall.md` als Grenze markiert: die Messkette auf Nextcloud 32, 33, 34 und 35 wiederholen; belegen, dass `occ app_api:app:unregister findling_backend --rm-data` das Volume auf jeder Version mitnimmt; die beiden Teilentfernungen als Kette fahren.
- **Fuer Plan 05-17 (Versions-Bump)** ist die Versionszeile in `php/appinfo/info.xml` ausdruecklich unangetastet bei 0.3.0 geblieben, damit zwei Plaene nicht dieselbe Zeile anheben.
- **Keine Blocker.**

## Self-Check: PASSED

Alle sechs genannten Dateien liegen im Worktree, alle fuenf Commits sind in der Historie von `worktree-agent-05-02`, der Arbeitsbaum ist sauber.

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-03*
