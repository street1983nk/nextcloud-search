---
phase: 11-haertung-und-store-einreichung-v1-1
plan: 04
subsystem: ci
tags: [deploy-harp, arm64, store-install, release-assets, v2-a, rel-01]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: 11-VORENTSCHEIDE.md, Entscheid v2-a vom 10.09.2026 (Plan 11-01)
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: der etablierte Runner ubuntu-24.04-arm in docker.yml, python.yml und measure.yml
  - phase: 06.1-launch-haertung-vor-der-store-abgabe
    provides: die Store-Install-Strecke "Store install 1 bis 7" und scripts/release/store-archive.sh
provides:
  - "deploy-harp.yml faehrt die Store-Install-Strecke nativ auf ubuntu-24.04-arm, ein Ast, ohne tolerate-failure"
  - "deploy-harp.yml kann beide Store-Archive vom GitHub-Release laden statt sie lokal zu bauen (workflow_dispatch-Eingabe release_tag)"
  - "gemessene Laufzeiten beider Architekturen gegen timeout-minutes 45, damit Annahme A4 der Recherche durch eine Messung ersetzt ist"
  - "der Entscheid v2-a steht als datierter Absatz in derselben Datei wie die Matrix"
affects: [11-07, 11-10, 11-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Runner als Matrixspalte statt als zweiter Job: eine Strecke, zwei Architekturen, kein zweiter Bestand"
    - "Zwei Bezugsquellen fuer dieselben Archive, per if komplementaer, nie beide und nie keine; der Inhaltsbeweis liegt hinter beiden"
    - "Plattform aus dpkg --print-architecture statt hart linux/amd64, damit derselbe Schritt auf beiden Runnern die richtige Haelfte des Index zieht"
    - "Kein stiller Rueckfall: ein fehlgeschlagener Download beendet den Job, statt lokal zu bauen und gruen zu melden"

key-files:
  created: []
  modified:
    - .github/workflows/deploy-harp.yml

key-decisions:
  - "Genau ein arm64-Ast (stable34) statt sechs: sechs Aeste waeren sechs Instanzen einer Aussage, die einer traegt, und stable34 ist am 10.09.2026 die neueste echte Freigabe (v34.0.4), also die Version, auf der die Aussage steht"
  - "test_lockstep_versions.py bleibt unveraendert. Der Entscheid v2-a verlangt das, und die Regex des Gates liest die Eintragszeile, nicht den Eintrag: die neue runner-Spalte ist ihr unsichtbar, und der zweite stable34-Eintrag faellt in ihr set() zusammen"
  - "Der occ-Recorder wird ein eigener Schritt (Store install 0). Er stand im Kopf des Bauschritts, und der laeuft im Release-Modus nicht; ein Recorder, der mit dem Bauschritt verschwindet, haette den Zero-Config-Beweis davon abhaengig gemacht, wie die Archive angekommen sind"
  - "assert-contents wird ein eigener Schritt hinter beiden Bezugswegen, statt im Bauschritt zu bleiben. Ein geladenes Archiv ist nicht deshalb richtig, weil es geladen wurde"
  - "Die throwaway-Signaturidentitaet bleibt im Bauschritt und wird im Release-Modus nicht gemintet: das Release-Archiv traegt die echte Signatur, und der Server-Checkout vertraut ihrer Wurzel ohnehin"
  - "docker pull nimmt die Plattform vom Runner. Der harte Wert linux/amd64 haette auf arm64 die falsche Haelfte gezogen, und eine emulierte Installation ist genau die Aussage, die Erfolgskriterium 1 nicht will"

patterns-established:
  - "Eine Architektur-Erweiterung eines Jobs wird als Matrixspalte gebaut und die zwei Stellen, die die Architektur wirklich kennen muessen, werden im Matrixkommentar namentlich genannt"
  - "Ein zweiter Bezugsweg fuer ein Artefakt bekommt denselben URL-Bau wie der bestehende (hier: store-submit.yml) und schreibt sha256 der geladenen Bytes ins Log"

requirements-completed: []

# Metrics
duration: 70min
completed: 2026-09-10
---

# Phase 11 Plan 04: deploy-harp, nativer arm64-Ast und der Release-Asset-Modus Summary

**Die Fremdinstallation aus Store-Archiven laeuft seit dem 10.09.2026 nativ auf arm64 (nicht emuliert, erster Anlauf gruen), und dieselbe Strecke kann die beiden Archive vom GitHub-Release laden statt sie lokal zu bauen; beides ist mit je einem gruenen Lauf belegt.**

## Performance

- **Duration:** rund 70 min, davon rund 25 min CI-Wartezeit, keine Box-Minute
- **Started:** 2026-09-10T20:00:00Z
- **Completed:** 2026-09-10T21:10:00Z
- **Tasks:** 3 von 3
- **Files modified:** 1 geaendert, 0 neu

## Accomplishments

- **Die Matrix hat eine `runner`-Spalte, und `runs-on` liest sie.** Die drei bestehenden Aeste behalten `ubuntu-24.04`, hinzu kommt **genau einer**: `stable34`, PHP 8.2, `tolerate-failure: false`, `runner: ubuntu-24.04-arm`. Kein `continue-on-error` fuer diesen Ast, denn er **ist** die zweite Haelfte von Erfolgskriterium 1, und ein toleranter Ast waere keine Aussage. Die Begruendung fuer "einer und nicht sechs" steht als Kommentar ueber der Include-Liste.
- **Der arm64-Ast war beim ersten Anlauf gruen**, ueber die vollstaendige Schrittfolge: Entwicklerpass, Driftprobe, sechs Deinstallationszusagen, Store install 1 bis 7 und sechs weitere Deinstallationszusagen. Nichts musste nachgezogen werden. Annahme A3 der Recherche (ein Paket oder eine `setup-php`-Version fehlt auf arm64) hat sich **nicht** bestaetigt.
- **Nativ und nicht emuliert, und das ist im Log nachlesbar.** Zwei Zeilen belegen es: `this runner is linux/arm64, and that is the half of the index that gets pulled`, gefolgt vom anonymen Pull, und aus dem HaRP-Bau `install_frpc: architecture aarch64, downloading .../frp_0.61.1_linux_arm64.tar.gz`.
- **Eine einzige Zeile musste die Architektur lernen.** "Store install 4" zog hart `--platform linux/amd64`; das ist jetzt `linux/$(dpkg --print-architecture)`. `dpkg` antwortet `amd64` beziehungsweise `arm64`, also genau die Namen, die der Index fuehrt, deshalb braucht es keine Uebersetzungstabelle. Geprueft am 10.09.: `ghcr.io/street1983nk/findling_backend` fuehrt `linux/amd64` und `linux/arm64` fuer `:dev` und fuer `:1.0.3`. `HARP_IMAGE` musste gar nichts lernen, weil dort seit dem 03.09. der Index-Digest gepinnt ist und nicht einer der beiden Plattform-Digests.
- **Der Release-Asset-Modus ist eine `workflow_dispatch`-Eingabe `release_tag` mit leerem Vorgabewert.** Leer heisst: alles bleibt, wie es war. Auf jedem Push und jedem Pull Request ist die Eingabe leer, weil der `inputs`-Kontext dort leer ist, und der Alltagslauf baut lokal wie bisher.
- **Der Ladeweg ist derselbe, den `store-submit.yml` dem Store nennt:** `https://github.com/${GITHUB_REPOSITORY}/releases/download/${TAG}/<app>.tar.gz`, aus `GITHUB_REPOSITORY` gebaut wie dort. Ein zweiter Weg waere ein zweiter Bestand.
- **Kein stiller Rueckfall.** `curl -sfL` (das `-f` verhindert, dass eine Fehlerseite als `findling.tar.gz` landet), drei Wiederholungen, danach `::error::` und Jobende. Zusaetzlich die Leerdatei-Pruefung. Ein Lauf, der still etwas anderes installiert als das Verlangte, waere schlimmer als ein roter Lauf.
- **Die geladenen Bytes stehen im Log und in der Zusammenfassung.** `ls -l` und `sha256sum` beider Dateien. Gemessen im Lauf 34526436580: `feee2e54fe7050ad8079c6781405326397fc94d79279da36f7ff6d2bd7e9ecfb` (findling.tar.gz, 235.706 Byte) und `678c5b8ac...ebc0` (findling_backend.tar.gz, 27.672 Byte). Beide stimmen mit den `digest`-Feldern ueberein, die die GitHub-API fuer die Assets von `v1.0.3` fuehrt.
- **Das Archiv wird in keinem Lauf zweimal gebaut.** Bauschritt und Ladeschritt tragen komplementaere `if`-Bedingungen, per API je Lauf geprueft (siehe Tabelle unten). `tar.gz` ist nicht byte-reproduzierbar; ein "bau es zusaetzlich und vergleiche" haette einen Unterschied erzeugt, der nichts aussagt.
- **`assert-contents` liegt jetzt hinter beiden Wegen**, als eigener Schritt "Store install 1 content proof, over whichever archives arrived". Im Release-Lauf hat er die geladenen Archive geprueft: 68 Eintraege mit `appinfo/signature.json` fuer die Begleit-App, 5 Eintraege ohne Codesignatur fuer die Container-Haelfte, kein `tests`, kein `vendor`, kein `composer.json`.
- **Ein Nebenbefund, der staerker ist als der Alltagslauf:** Weil "Store install 1" im Release-Modus uebersprungen wird, wird die throwaway-CI-Signaturidentitaet **nicht** gemintet und nichts an `resources/codesigning/root.crt` angehaengt (die Zeile `root.crt carried ... certificate(s)` fehlt im Log). `occ integrity:check-app findling` war trotzdem leer und sauber, die Manipulationsprobe wurde `INVALID_HASH`, die Wiederherstellung wieder sauber. Der Release-Modus prueft also gegen **die echte Nextcloud Code Signing Root Authority**, gegen dieselbe Wurzel wie die Instanz eines Nutzers. Das ist genau die Haelfte, die der Kommentarblock ueber "Store install 1" bis heute ausdruecklich als nicht beweisbar fuehrt.
- **Der Entscheid v2-a steht als Code und als datierter Absatz.** Die Matrix bleibt bei stable33/34/35, beide `info.xml` bleiben bei `min-version="33" max-version="35"`, der stable35-Eintrag behaelt `tolerate-failure: true` mit seinem vollstaendigen Kommentarblock, und `test_lockstep_versions.py` ist unangetastet. Darunter steht der neue Absatz: Entscheid vom 10.09.2026, Quelle `11-VORENTSCHEIDE.md` Abschnitt V-2, `RE-CHECK DATE: 2026-09-16` unveraendert, und die Nachverfolgung wandert von Plan 06-12 (abgeschlossen) auf **Plan 11-11**, wobei die Einreichung nach D-10 nicht auf den 16.09. wartet.

## Die vier Zahlen zu Annahme A4

Annahme A4 der Recherche (die Laufzeit passt in `timeout-minutes: 45`) ist damit durch eine Messung ersetzt, und zwar fuer beide Architekturen und beide Bezugswege. Plan 11-07 legt den Upgrade-Block in denselben Ast und kann mit diesen Zahlen rechnen.

| Lauf | Modus | arm64-Ast | laengster amd64-Ast | Abstand zu 45 min |
|---|---|---|---|---|
| **34525240422** | ohne `release_tag` (Push auf `9925f6d`) | **10 min 43 s** (stable34) | **11 min 14 s** (stable35) | **33 min 46 s** |
| **34526436580** | `release_tag=v1.0.3` (Dispatch) | **10 min 07 s** (stable34) | **12 min 15 s** (stable35) | **32 min 45 s** |

Alle acht Aeste `success`. Der arm64-Ast ist in beiden Laeufen **nicht** der langsamste; er liegt rund eine bis zwei Minuten unter dem langsamsten amd64-Ast. Der Abstand zum Deckel ist in beiden Laeufen groesser als die gesamte Laufzeit selbst, also bleibt Raum fuer den Upgrade-Block, ohne `timeout-minutes` anzufassen. `timeout-minutes: 45` ist unveraendert geblieben.

Zum Vergleich der Stand vor dieser Aenderung, Lauf 34522959025 vom selben Tag: 10 min 35 s bis 12 min 40 s ueber drei Aeste. Der vierte Ast kostet also keine Wanduhrzeit, weil die Aeste parallel fahren.

## Was der Release-Asset-Modus jetzt kann

Angestossen wird er ausschliesslich von Hand:

```
gh workflow run deploy-harp.yml --ref main -f release_tag=v1.0.3
```

Danach faehrt **jeder** Ast der Matrix die Store-Install-Strecke gegen die Bytes dieses Releases:

1. **Store install 0** legt den occ-Recorder an, in beiden Modi.
2. **Store install 1** wird uebersprungen, **Store install 1 from the release** laedt beide Archive nach `${RUNNER_TEMP}/store-dist`, also an genau die Stelle, an die der lokale Bau sie legt, und schreibt Groesse und sha256 ins Log und in die Job-Zusammenfassung.
3. **Store install 1 content proof** prueft die geladenen Archive mit demselben `assert-contents`, das `release.yml` faehrt.
4. Ab **Store install 2** ist die Strecke identisch: kein Schritt weiss, woher die Archive kamen.

Im Lauf 34526436580 hiess das konkret: die `info.xml` aus dem geladenen Archiv nennt `ghcr.io/street1983nk/findling_backend:1.0.3`, dieser Tag existiert, also wurde die `info.xml` **byte fuer byte** verwendet (kein `dev`-Rueckfall, keine ersetzte `image-tag`-Zeile), der Pull lief anonym mit leerem Credential-Store gegen den Index-Digest `sha256:34fbff64...`, und der Zero-Config-Beweis fand den Inhalt **nach einer einzigen cron-Runde**, ohne einen einzigen occ-Aufruf zwischen Installation und Treffer.

Damit hat Plan 11-07 sein Werkzeug: einmal gebaut, zweimal genutzt. Der Upgrade-Beweis 1.0.3 auf 1.1.0 braucht keinen zweiten Ladeweg mehr, sondern nur noch einen zweiten Aufruf desselben.

## Task Commits

1. **Task 1:** `274d8e3` , `ci(11-04): der native arm64-Ast der Store-Install-Strecke und der Entscheid v2-a` (runner-Spalte, vierter Eintrag, Plattform vom Runner, v2-a-Absatz)
2. **Task 2:** `9925f6d` , `ci(11-04): die Store-Install-Strecke kann die Archive vom Release laden` (release_tag, Ladeschritt, occ-Recorder als eigener Schritt, Inhaltsbeweis als eigener Schritt)
3. **Task 3:** kein eigener Commit , die Aufgabe war, beide Aenderungen gruen zu fahren und den Befund festzuhalten; der Befund steht in dieser Datei.

Gepusht: `8e1a347..9925f6d` auf `origin/main`.

## Gates

Der Plan aendert nur eine Workflow-Datei, keine Zeile Python. Die volle Backend-Suite ist trotzdem gefahren, weil zwei ihrer Gates die geaenderte Datei lesen.

| Gate | Ergebnis |
|---|---|
| `uv run python -m pytest -q` | **2002 passed, 15 skipped** (Grundlinie unveraendert) |
| `uv run python -m pytest tests/test_lockstep_versions.py tests/test_workflow_pins.py -q` | 37 passed, vor jedem der beiden Commits |
| `yaml.safe_load(deploy-harp.yml)` | gueltig, vor jedem der beiden Commits |
| `grep -c "ubuntu-24.04-arm"` | 2 (Matrixeintrag und Kommentar), gefordert mindestens 1 |
| `grep -c "runs-on: \${{ matrix.runner }}"` | 1 |
| `grep -c "release_tag\|RELEASE_TAG"` | 8, gefordert mindestens 3 |
| `grep -c "releases/download"` | 2, gefordert mindestens 1 |
| `grep -c "RE-CHECK DATE: 2026-09-16"` | 1, also noch da |
| `git diff` auf `- name:`-Zeilen | nur **drei Zusaetze**, keine geaenderte und keine entfernte Zeile |

`actionlint` steht auf diesem Rechner nicht zur Verfuegung (`which actionlint` leer); die YAML-Pruefung lief deshalb ueber `yaml.safe_load` plus eine Strukturpruefung, die `runs-on`, die vier Matrixeintraege, die Eingabeliste und alle `if`-Bedingungen ausliest. Die eigentliche Validierung war der gruene Lauf.

### CI nach dem Push

Der Push auf `9925f6d` beruehrt nur `.github/workflows/deploy-harp.yml`, und die Pfadfilter der uebrigen Workflows greifen darauf nicht. Angestossen wurde deshalb genau ein Lauf, und der zweite wurde von Hand gefahren.

| Lauf | Ausloeser | `release_tag` | Ergebnis |
|---|---|---|---|
| **34525240422** | Push `9925f6d` | leer | **success**, alle vier Aeste |
| **34526436580** | `workflow_dispatch` | `v1.0.3` | **success**, alle vier Aeste |

Die Aeste im Einzelnen, beide Laeufe:

| Ast | 34525240422 | 34526436580 |
|---|---|---|
| stable33, 8.2, ubuntu-24.04 | success, 10:35 | success, 09:59 |
| stable34, 8.2, ubuntu-24.04 | success, 10:54 | success, 12:02 |
| **stable34, 8.2, ubuntu-24.04-arm** | **success, 10:43** | **success, 10:07** |
| stable35, 8.3, ubuntu-24.04 (tolerant) | success, 11:14 | success, 12:15 |

Die Komplementaritaet der beiden Bezugswege ist nicht behauptet, sondern je Lauf aus der API gelesen:

| Schritt | 34525240422 | 34526436580 |
|---|---|---|
| Store install 0, the occ recorder | success | success |
| Store install 1, build both release archives | success | **skipped** |
| Store install 1 from the release | **skipped** | success |
| Store install 1 content proof | success | success |

Der stable35-Ast ist in beiden Laeufen gruen, also faellt der `tolerate-failure`-Flag am 16.09. voraussichtlich ohne Widerstand; die Nachverfolgung liegt bei 11-11.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Die Plattform des anonymen Pulls war hart `linux/amd64`**
- **Found during:** Task 1, beim Durchsehen der Strecke auf Architekturabhaengigkeiten, vor dem ersten Lauf
- **Issue:** "Store install 4" rief `docker pull --platform linux/amd64`. Auf `ubuntu-24.04-arm` haette das die amd64-Haelfte des Index gezogen; der Container waere emuliert gelaufen oder gar nicht gestartet. Eine emulierte Installation ist genau die Aussage, die Erfolgskriterium 1 nicht verlangt.
- **Fix:** `platform="linux/$(dpkg --print-architecture)"`, mit einer Log-Zeile, die die erkannte Plattform nennt, und einem Kommentar, der die frueher hartkodierte Zeile und den Grund fuer den Wechsel benennt.
- **Files modified:** `.github/workflows/deploy-harp.yml`
- **Commit:** `274d8e3`

**2. [Rule 3 - Blockierend] Der occ-Recorder haette den Release-Modus stumm gemacht**
- **Found during:** Task 2
- **Issue:** `OCC_LOG` und `${RUNNER_TEMP}/nc-occ.sh` wurden im Kopf von "Store install 1" angelegt. Dieser Schritt laeuft im Release-Modus nicht, und dann haette es weder den Wrapper (jeder spaetere Schritt ruft ihn) noch das Log gegeben, das "Store install 7" fuer den Zero-Config-Beweis auswertet.
- **Fix:** Die sieben Zeilen sind in den neuen, immer laufenden Schritt "Store install 0, the occ recorder every step of the store pass goes through" gewandert, mit einem Kommentar, der den Grund nennt. Im lokalen Modus ist das Verhalten identisch: derselbe Befehl, ein Schritt frueher.
- **Files modified:** `.github/workflows/deploy-harp.yml`
- **Commit:** `9925f6d`

**3. [Rule 2 - Fehlende kritische Funktionalitaet] `assert-contents` haette nur den lokalen Bau geprueft**
- **Found during:** Task 2
- **Issue:** Der Inhaltsbeweis stand am Ende des Bauschritts. Waere er dort geblieben, haette der Release-Modus als einziger Weg in eine Installation gefuehrt, den nichts geprueft hat , und der Plan nennt genau das als Falle ("ein geladenes Archiv ist nicht deshalb richtig, weil es geladen wurde", T-11-12).
- **Fix:** Eigener, immer laufender Schritt hinter beiden Bezugswegen.
- **Files modified:** `.github/workflows/deploy-harp.yml`
- **Commit:** `9925f6d`

### Abweichungen vom Wortlaut des Plans

**1. `backend/tests/test_lockstep_versions.py` ist nicht geaendert worden**, obwohl der Plan die Datei in `files_modified` fuehrt. Der Entscheid v2-a verlangt ausdruecklich, sie unveraendert zu lassen, und sie musste auch technisch nicht nachgezogen werden: `_MATRIX_ENTRY` liest die Zeile, die einen Eintrag eroeffnet (`- server-version: stableNN`), nicht den ganzen Eintrag, also ist die neue `runner`-Spalte fuer das Gate unsichtbar; und `running = sorted(set(matrix), ...)` laesst den zweiten `stable34`-Eintrag mit dem ersten zusammenfallen. Beide Richtungen des Gates sind mit vier Eintraegen gruen. Der Wortlaut des must_have ("auch mit der neuen Runner-Spalte") ist damit erfuellt, ohne die Datei anzufassen.

**2. Die Job-Namen haben sich geaendert**, was der Plan nicht erwaehnt: GitHub haengt die Matrixwerte an den Job-Namen an, auch wenn `name:` gesetzt ist. Aus `deploy-harp (stable33, 8.2, false)` wird `deploy-harp (stable33, 8.2, false, ubuntu-24.04)`. Geprueft, dass daran nichts haengt: `main` hat keinen Branch-Schutz (`gh api .../branches/main/protection` antwortet 404) und kein Test und kein Workflow nennt einen dieser Namen. Frueher zitierte Laufnummern bleiben lesbar, weil sie Laufnummern sind und keine Namen.

**3. Task 1 und Task 2 aendern dieselbe Datei** und sind trotzdem in zwei Commits gelandet: der fertige Stand wurde beiseitegelegt, die Datei auf `8e1a347` zurueckgesetzt, die Hunks von Task 1 einzeln angewandt, geprueft und committet, danach der fertige Stand wiederhergestellt und Task 2 committet. Beide Commits sind fuer sich gueltiges YAML und beide Gates sind vor beiden Commits gruen gefahren.

**4. Keine Anpassung war noetig, wo der Plan eine erwartet hat.** Annahme A3 (auf arm64 fehlt ein Paket oder eine `setup-php`-Version) ist nicht eingetreten: `shivammathur/setup-php` in der gepinnten Fassung, `sqlite3`, `wngerman`, `openssl`, die HaRP-Instanz und der lokale Registry-Bau liefen auf `ubuntu-24.04-arm` ohne eine einzige Aenderung. Es gibt also keine "genaue Fehlstelle" zu notieren.

## Threat-Bezug

| Threat | Wie er in dieser Aenderung behandelt ist |
|---|---|
| T-11-12 (Tampering, Release-Asset-Modus) | Derselbe URL-Bau wie `store-submit.yml`, `assert-contents` als eigener Schritt hinter beiden Wegen, sha256 beider Dateien im Log und in der Zusammenfassung, `::error::` statt Rueckfall. Zusaetzlich, ungeplant: die Integritaetspruefung laeuft im Release-Modus gegen die echte Signaturwurzel |
| T-11-13 (Spoofing, Aktionen im neuen Ast) | Kein neuer `uses`-Eintrag; `test_workflow_pins.py` gruen |
| T-11-14 (DoS, timeout-minutes 45) | Vier Zahlen gemessen, siehe oben; Abstand 32 bis 34 min, `timeout-minutes` unveraendert |
| T-11-15 (Repudiation, Fenster gegen Matrix) | `test_lockstep_versions.py` gruen in beide Richtungen, v2-a als datierter Absatz in derselben Datei |
| T-11-SC (Tampering, Paketinstallation) | Kein Paket installiert, kein Pin bewegt, `HARP_IMAGE` unveraendert |

## Was der naechste Plan wissen muss

- **11-07 (Upgrade-Beweis):** Der Ladeweg steht und ist gefahren. `release_tag` ist eine `workflow_dispatch`-Eingabe des Jobs, wirkt auf **alle** Aeste zugleich und legt die Archive nach `${RUNNER_TEMP}/store-dist`. Wer 1.0.3 und dann 1.1.0 hintereinander installieren will, braucht einen zweiten Ladevorgang **innerhalb** eines Laufs, nicht zwei Laeufe; die Eingabe allein leistet das nicht. Die Laufzeitreserve dafuer ist gemessen: rund 33 Minuten. Der Upgrade-Block soll nach D-02 auf `stable34` liegen, und genau dort liegt jetzt auch der arm64-Ast, also ist zu entscheiden, ob der Upgrade auf beiden stable34-Aesten faehrt oder nur auf einem.
- **11-11 (Versionsbump und Einreichung):** Die Nachverfolgung des `RE-CHECK DATE: 2026-09-16` liegt jetzt namentlich bei diesem Plan; der Absatz im Workflow sagt es. Der stable35-Ast war am 10.09. zweimal gruen, das Umlegen des Flags traegt also kein bekanntes Risiko. Das Versionsfenster bleibt nach v2-a unangetastet.
- **11-10 (Audits):** Der Release-Modus ist eine neue Bezugsquelle fuer Bytes, die in einem Job mit Docker-Socket installiert werden. Die Gegenmassnahmen stehen oben in der Threat-Tabelle; ein Auditblick auf "kein stiller Rueckfall" und "assert-contents hinter beiden Wegen" ist der kurze Weg.
- **REL-01 ist NICHT abgehakt.** Dieser Plan liefert die zwei fehlenden Haelften von Erfolgskriterium 1, aber die Anforderung haengt an der Einreichung selbst und wird in 11-11 abgeschlossen.

## Self-Check: PASSED

- `.github/workflows/deploy-harp.yml` vorhanden und geaendert
- `.planning/phases/11-haertung-und-store-einreichung-v1-1/11-04-SUMMARY.md` vorhanden
- Commit `274d8e3` in `git log` vorhanden
- Commit `9925f6d` in `git log` vorhanden, `origin/main` zeigt darauf
- Lauf 34525240422 `success`, Lauf 34526436580 `success`, beide ueber `gh run view` geprueft
