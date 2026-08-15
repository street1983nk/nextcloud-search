---
phase: 01-integrationsbeweis
plan: 06
subsystem: testing
tags: [github-actions, appapi, docker-compose, unified-search, ocs, walking-skeleton, uv]

requires:
  - phase: 01-integrationsbeweis
    provides: "ExApp mit AppAPI-Handshake und POST /search samt Container-Beweis (Plan 01-04)"
  - phase: 01-integrationsbeweis
    provides: "PHP-Companion mit IProvider, exAppRequest-Proxy und Content-Gateway (Plan 01-05)"
provides:
  - "integration.yml als vollstaendiger Durchstichbeweis: ExApp nativ gestartet, ueber AppAPI registriert, Suche als Testnutzer geprueft"
  - "Scharfe Assertion auf den Container-Beweis: subline enthaelt 'produced inside container' und die Nutzer-ID"
  - "Negativprobe im selben Lauf: nach app_api:app:unregister bleibt die Suche 200 mit leerem Ergebnis"
  - "scripts/dev/compose.yaml: lokale Test-Nextcloud 34.0.3-apache auf SQLite mit php/ als custom_apps/findling"
  - "scripts/dev/register-exapp.sh: ein Kommando fuer Backendstart, Heartbeat, Daemon- und ExApp-Registrierung, idempotent"
  - "docs/dev-setup.md: reproduzierbares Setup ohne lokales PHP, mit Diagnosereihenfolge aus Pitfall 3"
affects: [01-07, 01-08, 02-indexierung]

tech-stack:
  added: [astral-sh/setup-uv, nextcloud:34.0.3-apache]
  patterns:
    - "Der Beweis prueft die Nutzer-ID im Ergebnis, nicht nur die Existenz eines Ergebnisses"
    - "Jede Positivprobe hat eine Negativprobe im selben Lauf"
    - "Alle occ-Aufrufe laufen ueber den Container, es gibt keinen lokalen PHP-Pfad"
    - "Host und Container haben getrennte Adressbilder: 127.0.0.1 in CI, host.docker.internal lokal"

key-files:
  created:
    - scripts/dev/compose.yaml
    - scripts/dev/register-exapp.sh
    - docs/dev-setup.md
    - .gitattributes
  modified:
    - .github/workflows/integration.yml
    - .gitignore

key-decisions:
  - "Die zweite jq-Assertion prueft die Nutzer-ID, eine dritte den Container-Marker: ein hartkodierter PHP-Treffer kann den Lauf nicht bestehen"
  - "Lokal bindet die ExApp auf 0.0.0.0 statt 127.0.0.1, weil Nextcloud im Container laeuft und einen Loopback-Bind nicht erreichen kann"
  - "Die Companion wird nach custom_apps/findling gemountet, das ist der schreibbare App-Pfad des offiziellen Images"
  - "docs/dev-setup.md setzt COMPOSE_FILE einmal, damit jedes weitere Kommando exakt so aussieht wie in der Checkpoint-Anleitung"

patterns-established:
  - "Registrierungsskripte raeumen vor sich selbst auf (unregister vor register), sonst scheitert der Handshake an einem alten Secret"
  - "Diagnose beginnt immer bei /ocs/v2.php/search/providers, erst danach beim Container"

requirements-completed: [COMP-01]

duration: 17 min
completed: 2026-08-15
---

# Phase 1 Plan 06: Durchstich als CI-Gate und lokale Sichtprobe Summary

**integration.yml startet die ExApp nativ, registriert sie ueber AppAPI und weist im Suchergebnis den Container-Beweis samt Nutzer-ID nach, dazu ein lokales compose-Setup, das dieselbe Kette ohne lokales PHP reproduziert.**

## Performance

- **Duration:** 17 min (bis zum Checkpoint)
- **Started:** 2026-08-15T11:06:00Z
- **Completed (autonomer Teil):** 2026-08-15T11:23:00Z
- **Tasks:** 2 von 3 (Task 3 ist der Owner-Checkpoint)
- **Files created:** 4, **modified:** 2

## Accomplishments

- Der Workflow beweist jetzt den ganzen Weg statt nur der Providerliste. Neu sind: uv-Setup mit `uv sync --frozen`, der native Start der ExApp mit den Pflichtvariablen, eine Warteschleife auf `/heartbeat` (30 Sekunden, danach Abbruch mit Log), die Daemon-Registrierung als `manual_install`, die ExApp-Registrierung mit `--wait-finish`, ein Testnutzer und die Suche ueber `/ocs/v2.php/search/providers/findling/search`.
- Die Assertion ist scharf gestellt: neben `entries | length > 0` wird geprueft, dass die subline `produced inside container` **und** `testuser` enthaelt und kein `<`. Damit ist der Beweis nicht faelschbar, ohne die Kette wirklich zu durchlaufen: Hostname und Zeitstempel entstehen im laufenden Backendprozess, die Nutzer-ID kommt aus dem signierten AppAPI-Header.
- Die Negativprobe (Pitfall 1, T-01-23) laeuft im selben Job: `app_api:app:unregister`, danach dieselbe Suche, Statuscode muss 200 bleiben und `entries` leer sein. Ein gestopptes Backend darf die Suche des Nutzers nicht mitreissen.
- Der Job raeumt deterministisch auf: ein `always()`-Schritt beendet den Backendprozess ueber die abgelegte PID, und der `failure()`-Schritt gibt zusaetzlich `app_api:app:list` und die letzten 200 Zeilen des Backendlogs aus.
- Das lokale Setup steht ohne eine einzige lokale PHP-Voraussetzung: compose-Datei mit gepinntem `nextcloud:34.0.3-apache` auf SQLite, `php/` als `custom_apps/findling` gemountet, `host.docker.internal:host-gateway` fuer Parität zwischen Docker Desktop und einem nackten Linux-Daemon.
- `scripts/dev/register-exapp.sh` ist idempotent: es laesst ein bereits antwortendes Backend in Ruhe, entfernt eine alte Registrierung vor der neuen und meldet am Ende `registered`.

## Task Commits

1. **Task 1: Kanarienprobe gruen ziehen, inklusive Negativfall** - `e6bb6d8` (feat)
2. **Task 2: Lokales Setup fuer die Sichtprobe** - `aff9e30` (feat)
3. **Deviation, Zeilenenden** - `5ad7dd2` (fix)
4. **Task 3: Owner-Sichtprobe** - offen, Checkpoint

## Files Created/Modified

- `.github/workflows/integration.yml` - 23 Schritte statt 12: Backendstart, Heartbeat, zwei Registrierungen, Testnutzer, Positivprobe mit vier jq-Assertions, Negativprobe, Diagnoseausgabe, Aufraeumschritt.
- `scripts/dev/compose.yaml` - Test-Nextcloud, gepinnte Version, SQLite, Port 8080, benanntes Volume, Bind-Mount `../../php` nach `custom_apps/findling`, `extra_hosts` fuer `host.docker.internal`.
- `scripts/dev/register-exapp.sh` - POSIX sh, wartet auf `status.php`, aktiviert `app_api` und `findling`, startet das Backend im Hintergrund nach `.dev/exapp.log` mit PID in `.dev/exapp.pid`, wartet auf den Heartbeat, deregistriert vorsorglich, registriert Daemon und ExApp.
- `docs/dev-setup.md` - 165 Zeilen: Voraussetzungen, Adressbild Host gegen Container als ASCII-Diagramm, sieben Schritte bis zum sichtbaren Treffer, Gegenprobe, Diagnosereihenfolge (erst Providerliste, dann Container), WSL2-Hinweis, Abbau, CI-Pruefbefehl.
- `.gitattributes` - neu, erzwingt LF fuer `*.sh`, `*.yml`, `*.yaml`.
- `.gitignore` - `.dev/` ergaenzt, das Laufzeitverzeichnis des lokalen Backends.

## Decisions Made

- **Vier Assertions statt drei.** Der Plan nennt drei. Die zusaetzliche Pruefung auf `produced inside container` trennt zwei Fehlerbilder, die sonst gleich aussehen: ein Treffer aus einer anderen Quelle mit passender Nutzer-ID gegen den echten Containerbeweis. Sie kostet nichts und ist genau die Zeile, die der Orchestrator-Auftrag scharf gestellt sehen wollte.
- **`0.0.0.0` lokal, `127.0.0.1` in der CI.** In der CI liegen Server und Backend auf demselben Host, lokal liegt Nextcloud im Container. Ein Loopback-Bind waere von dort unsichtbar, das Log des Backends saehe dabei vollkommen gesund aus. Der Unterschied steht als Kommentar im Skript und als Absatz in der Doku, weil er sonst genau der Fehler ist, den Pitfall 5 beschreibt.
- **Der Daemon zeigt lokal auf `host.docker.internal`.** Der interfaces-Block nennt `localhost`, das gilt fuer den CI-Fall. Innerhalb des Containers ist `localhost` der Container selbst.
- **Kein `-f` in den Doku-Kommandos.** `COMPOSE_FILE` wird einmal exportiert. Dadurch sehen die Kommandos exakt so aus wie in der Checkpoint-Anleitung des Plans, und das Abnahmekriterium "kein `occ` ohne `docker compose exec`" ist auch woertlich erfuellt, nicht nur sinngemaess.
- **Testzugangsdaten stehen im Klartext im Workflow und in der compose-Datei.** Sie gehoeren zu Instanzen, die mit dem Runner beziehungsweise dem Volume sterben (T-01-24). Ein GitHub-Secret waere hier kein Gewinn, sondern nur eine Stelle mehr, an der ein echtes Geheimnis versehentlich landen kann.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] CI-Abnahmekriterien sind vor dem Push nicht pruefbar**
- **Found during:** Task 1
- **Issue:** Zwei Kriterien verlangen `gh run list --workflow=integration.yml --limit 1 --json conclusion -q '.[0].conclusion'` gleich `success`. Im Worktree ohne Push liefert der Befehl den Stand des Wave-3-Commits `a9617eb` (`success`), also das Urteil ueber die **alte** Workflowfassung, die nur die Providerliste geprueft hat. Das waere ein falsch positives Kriterium.
- **Fix:** Nicht vorgetaeuscht. Lokal geprueft wurde alles, was ohne Runner pruefbar ist: YAML parst (23 Schritte), alle Grep-Gates des Plans, Reihenfolge der Schritte. Der offene Nachweis steht unten unter "Offen bis zum Push".
- **Files modified:** keine
- **Verification:** `gh run list ... -q '.[0].conclusion'` liefert aktuell `success` fuer `a9617eb`, nicht fuer diesen Plan. Nach dem Push des Orchestrators ist derselbe Befehl das gueltige Urteil.
- **Committed in:** n/a

**2. [Rule 1 - Bug] Zeilenenden von `register-exapp.sh`**
- **Found during:** Task 2
- **Issue:** Das Repo hatte keine `.gitattributes`. Ein Checkout mit `core.autocrlf=true`, dem Windows-Standard, schreibt CRLF in die Datei. Die Shebang-Zeile traegt dann ein Wagenruecklaufzeichen, und jeder Aufruf endet in einem "command not found", das ein unsichtbares Zeichen benennt.
- **Fix:** `.gitattributes` mit `text eol=lf` fuer `*.sh`, `*.yml`, `*.yaml`.
- **Files modified:** .gitattributes (neu)
- **Verification:** `sh -n scripts/dev/register-exapp.sh` Exit 0; die Datei liegt im Index mit LF.
- **Committed in:** `5ad7dd2`

**3. [Rule 3 - Blocking] Mountpfad `custom_apps` statt `apps-extra`**
- **Found during:** Task 2
- **Issue:** Der Plan nennt ein "Volume fuer apps-extra". `apps-extra` ist der Pfad des Entwicklerimages `juliusknorr/nextcloud-docker-dev`. Das offizielle `nextcloud:apache` kennt es nicht; sein schreibbarer App-Pfad ist `/var/www/html/custom_apps`. Ein Mount nach `apps-extra` waere von `app:enable` nie gefunden worden.
- **Fix:** Bind-Mount `../../php` nach `/var/www/html/custom_apps/findling`, Verzeichnisname exakt die App-ID.
- **Files modified:** scripts/dev/compose.yaml
- **Verification:** `docker compose -f scripts/dev/compose.yaml config` Exit 0; der Nachweis, dass `app:enable` die App findet, ist Teil der Owner-Sichtprobe.
- **Committed in:** `aff9e30`

**4. [Rule 2 - Missing Critical] `.dev/` in `.gitignore`**
- **Found during:** Task 2
- **Issue:** Das Skript schreibt Log, PID und den persistenten Speicher des Backends nach `.dev/`. Ohne Eintrag lagen diese Dateien nach dem ersten lokalen Lauf als unversionierte Dateien im Baum und waeren irgendwann mitcommittet worden.
- **Fix:** Eintrag `.dev/` unter "Runtime and build output".
- **Files modified:** .gitignore
- **Verification:** `git status --short` zeigt nach dem Task keinen unversionierten Rest.
- **Committed in:** `aff9e30`

**5. [Rule 2 - Missing Critical] Bindungsadresse und Daemon-Host weichen lokal von der CI ab**
- **Found during:** Task 2
- **Issue:** Der Plan verlangt fuer das Skript "dieselben Umgebungsvariablen wie die CI". Woertlich umgesetzt haette das Backend auf `127.0.0.1` gebunden und der Daemon auf `localhost` gezeigt. Beides ist aus dem Container heraus unerreichbar, die Registrierung waere in einen Timeout gelaufen, waehrend das Backendlog gesund aussieht: genau das Fehlerbild aus Pitfall 5.
- **Fix:** Lokal `APP_HOST=0.0.0.0` und Daemon-Host `host.docker.internal`, dazu `extra_hosts: host.docker.internal:host-gateway` in der compose-Datei. Secret, Port, Version und `NEXTCLOUD_URL` bleiben identisch zur CI.
- **Files modified:** scripts/dev/register-exapp.sh, scripts/dev/compose.yaml, docs/dev-setup.md
- **Verification:** `sh -n` Exit 0, `docker compose config` Exit 0; der Laufzeitnachweis ist die Owner-Sichtprobe.
- **Committed in:** `aff9e30`

---

**Total deviations:** 5 auto-fixed (1 Bug, 2 fehlende kritische Funktionalitaet, 2 blockierend)
**Impact on plan:** Keine inhaltliche Aenderung am Beweis und kein Scope-Zuwachs. Drei Abweichungen sind Anpassungen an die reale Zielumgebung (Imagepfad, Adressbild, Zeilenenden), zwei sind Hygiene. Zwei neue Dateien ausserhalb der `files_modified`-Liste: `.gitattributes` und der `.gitignore`-Eintrag, beide klein und beide Korrektheitsanforderungen.

## Issues Encountered

- **`grep -c 'wait-finish'` lieferte zunaechst 2.** Ursache war ein erklaerender Kommentar, der die Option beim Namen nannte. Der Kommentar beschreibt sie jetzt, ohne sie zu zitieren. Gleiches Muster wie beim `ExAppRequired`-Zaehler in Plan 01-05: Grep-Gates messen Zeichenketten, nicht Absichten, also duerfen Kommentare die geprüften Zeichenketten nicht tragen.
- **`${{ env.X }}` in einem Schritt-`env` vermieden.** Die Kontextverfuegbarkeit an dieser Stelle ist unter Actions eine bekannte Stolperstelle. Die Variablen werden stattdessen im `run`-Block exportiert, was in jedem Fall funktioniert und ausserdem sichtbar macht, welche Variable das Backend wirklich sieht.
- **`grep -c 'HP_SHARED_KEY'` muss 0 bleiben.** Der Kommentar zum bewusst nicht gesetzten Schluessel umschreibt ihn deshalb ("the HaRP shared key"). Die Aussage steht, der Zaehler bleibt bei 0.

## Verification

| Kriterium | Ergebnis |
|---|---|
| `grep -c 'app_api:app:unregister' .github/workflows/integration.yml` | 1 PASS |
| `grep -c 'HP_SHARED_KEY' .github/workflows/integration.yml` | 0 PASS |
| `grep -c 'wait-finish' .github/workflows/integration.yml` | 1 PASS |
| `grep -c 'app_api:app:register' .github/workflows/integration.yml` | 1 PASS |
| `grep -c 'providers/findling/search' .github/workflows/integration.yml` | 2 PASS |
| integration.yml parst als YAML | 23 Schritte PASS |
| `sh -n scripts/dev/register-exapp.sh` | Exit 0 PASS |
| `docker compose -f scripts/dev/compose.yaml config` | Exit 0 PASS |
| `grep -vc '^#' scripts/dev/register-exapp.sh` | 96 (Vorgabe > 10) PASS |
| `grep -c 'manual_install' scripts/dev/register-exapp.sh` | 1 PASS |
| `grep -v '^#' docs/dev-setup.md \| grep -c 'search/providers'` | 2 (Vorgabe > 0) PASS |
| `grep -c 'php occ' docs/dev-setup.md` | 3 (Vorgabe > 0) PASS |
| Zeilen mit `occ` ohne `docker compose exec` in docs/dev-setup.md | 0 PASS |
| `wc -l docs/dev-setup.md` | 165 (Vorgabe >= 40) PASS |

### Offen bis zum Push durch den Orchestrator

```bash
gh run list --workflow=integration.yml --limit 1 --json conclusion,headSha -q '.[0]'
```

Erwartet: `conclusion` gleich `success` **und** `headSha` gleich dem Merge-Commit dieser Wave. Der aktuelle Erfolgslauf gehoert zu `a9617eb` und damit zur alten Workflowfassung; er ist kein Nachweis fuer diesen Plan. Faellt der neue Lauf durch, sagt der Schritt, wo:

| Fehlgeschlagener Schritt | Aussage |
|---|---|
| Wait for the ExApp heartbeat | Das Backend startet nicht, Ursache steht im ausgegebenen Log |
| Register the ExApp | Handshake scheitert, meist Secret, Port oder Bindungsmodus |
| Search as the test user | Die Kette laeuft, aber der Treffer stimmt nicht: die fehlgeschlagene jq-Zeile benennt, welche der vier Zusagen gebrochen ist |
| Search again with the backend gone | Pitfall 1: der Proxy behandelt das Fehler-Array wie ein Antwortobjekt |

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers. Die drei `mitigate`-Eintraege dieses Plans sind umgesetzt:

| Threat ID | Umsetzung | Beleg |
|---|---|---|
| T-01-22 (Spoofing, Beweiskraft) | Der Lauf prueft die Nutzer-ID **und** den Container-Marker in der subline | `jq -e '... contains("testuser")'` und `contains("produced inside container")` |
| T-01-23 (Denial of Service) | Negativprobe im selben Job, 200 mit leerem `entries` | Schritt "Search again with the backend gone" |
| T-01-24 (Information Disclosure) | Testwerte statt Geheimnisse, Instanz und Runner sind Wegwerfware | `EXAPP_SECRET: '12345'`, `TESTUSER_PASS` im Klartext, kein GitHub-Secret im Workflow |
| T-01-25 (Tampering, XSS) | accept laut Register, zusaetzlich prueft der Lauf, dass kein `<` im Snippet steht | `jq -e '... contains("<") \| not'` |

## Known Stubs

Keine neuen. Die bestehenden Platzhalter der Phase (fester Treffer ohne Datei, `fileId=0`, leere `highlights`) stammen aus Plan 01-04 und sind dort dokumentiert; dieser Plan beweist den Weg, nicht die Suche.

## User Setup Required

None - keine externe Dienstkonfiguration. Fuer die Sichtprobe muss Docker Desktop laufen; zum Zeitpunkt dieses Summaries antwortet die Engine (Version 29.5.2).

## Next Phase Readiness

- Der CI-Beweis steht und wird mit dem naechsten Push zum Urteil. Danach ist der Weg Suchleiste bis Container dauerhaft abgesichert, und Plan 01-07 (Image) kann den nativen Start durch den Containerstart ersetzen, ohne die Assertionen anzufassen.
- Fuer 01-07 vorgemerkt: sobald das Image existiert, sollte die Daemon-Registrierung im lokalen Skript optional auf `docker-install` umschaltbar sein; die Assertionen und die Doku bleiben unveraendert gueltig.
- Offen: die Owner-Sichtprobe (Task 3). Alles dafuer noetige ist gebaut und geprueft, die Schrittfolge steht in `docs/dev-setup.md` und im Checkpoint-Bericht.

## Self-Check: PASSED

- Dateien auf der Platte: `scripts/dev/compose.yaml`, `scripts/dev/register-exapp.sh`, `docs/dev-setup.md`, `.gitattributes` vorhanden; `.github/workflows/integration.yml` und `.gitignore` geaendert.
- Commits im Log: `e6bb6d8`, `aff9e30`, `5ad7dd2`.
- Alle lokal pruefbaren Abnahmekriterien beider autonomer Tasks gruen (Tabelle oben), keine Loeschung in einem der drei Commits.
- Keine Aenderung an STATE.md, ROADMAP.md oder REQUIREMENTS.md, kein Push.

---
*Phase: 01-integrationsbeweis*
*Status: Task 1 und 2 abgeschlossen, Task 3 wartet auf die Sichtprobe des Owners*
*Completed: 2026-08-15*
