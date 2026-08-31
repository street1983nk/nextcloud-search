---
phase: 02-indexkern-und-volltextsuche
plan: 07
subsystem: packaging
tags: [docker, wngerman, licences, third-party, info-xml, appstore, environment-variables, privacy]

requires:
  - phase: 02-indexkern-und-volltextsuche
    provides: findling/config.py with the exact environment variable names, wordlist.py recipe A over /usr/share/dict/ngerman
  - phase: 01-integrationsbeweis
    provides: multi-arch image, backend/appinfo/info.xml with docker-install, the store validation gate in php.yml
provides:
  - wngerman 20161207-15 pinned in the runtime image, plus its GPL-2+ text at /usr/local/share/findling/COPYING.wngerman
  - THIRD-PARTY.md, origin, version, licence and place in the image for every distributed third party artifact
  - backend/appinfo/info.xml at 0.2.0 with three routes (search, snippets USER; status ADMIN) and four environment variables
  - the store description states that the extracted document text lives in the app volume and that backups capture it
affects: [02-04 php version bump to 0.2.0, 02-08 snippets endpoint, 04 admin status page, phase 5 release packaging]

tech-stack:
  added: [wngerman==20161207-15 (Debian trixie), dictionaries-common==1.30.10 (pulled in as a dependency)]
  patterns:
    - "A licence obligation travels with the image, not only with the repository; the build fails if the text is missing"
    - "Data packages may live in the runtime stage; tools may not"
    - "Every environment variable in info.xml is spelled exactly as the Python side reads it, checked pairwise"
    - "Version, image-tag and both halves of the app move together, and the release gate compares all three"

key-files:
  created:
    - THIRD-PARTY.md
  modified:
    - backend/Dockerfile
    - backend/appinfo/info.xml

key-decisions:
  - "The word list stays in the runtime image instead of being distilled in a build stage, so the tokenisation hangs on a hash in the meta table and not on a build nobody can inspect"
  - "The apt version is pinned hard: a silent move of the list is a silent move of every German search result, and a loud build failure is the cheap moment to notice"
  - "image-tag was raised to 0.2.0 together with the version, because the release gate in docker.yml compares them and an installation pulls the tag"
  - "dictionaries-common is listed in THIRD-PARTY.md although the plan does not name it: it is distributed, so it belongs there"
  - "The privacy statement is two sentences and not one; the storage fact alone is alarming, the 'nothing leaves the server' alone is incomplete"

patterns-established:
  - "Pattern: fail closed on licence obligations (test -s on the copyright file inside the same RUN)"
  - "Pattern: measured numbers belong in the description of a setting, so choosing is a decision and not a guess"

requirements-completed: [SRCH-01, IDX-06]

duration: 15min
completed: 2026-08-31
---

# Phase 02 Plan 07: Image, Metadaten und Lizenzen Summary

**Die deutsche Wortliste liegt gepinnt und mit ihrem GPL-2+-Text im Laufzeitimage, die ExApp deklariert drei Routen und vier Schalter auf Version 0.2.0, und dass der extrahierte Dokumenttext im App-Volume liegt, steht jetzt in der Store-Beschreibung statt in einer stillen Annahme.**

## Performance

- **Duration:** ca. 15 min
- **Started:** 2026-08-31T19:50Z
- **Completed:** 2026-08-31T20:03Z
- **Tasks:** 2 von 2
- **Files modified:** 3 (1 neu, 2 geaendert)

## Accomplishments

- `wngerman=20161207-15` im Laufzeitimage, `--no-install-recommends`, Paketlisten im selben RUN geloescht, kein Netzzugriff beim Start.
- Der Lizenztext wird nach `/usr/local/share/findling/COPYING.wngerman` kopiert, und der Bau bricht ab, wenn entweder die Liste oder ihr Copyright fehlt.
- `THIRD-PARTY.md` (108 Zeilen) nennt Herkunft, Version, Lizenz und Ort im Image fuer die Wortliste, ihre eine Debian-Abhaengigkeit, alle neun Extraktions- und Indexpakete sowie Basisimage, nc-py-api, fastapi, httpx und frpc.
- `backend/appinfo/info.xml`: `snippets` (POST, USER) und `status` (GET, ADMIN) neben `search`, nichts ohne Anmeldung erreichbar, Version und `image-tag` auf 0.2.0.
- Drei neue Umgebungsvariablen mit gemessenen Zahlen und dem Reindex-Hinweis, Namen paarweise gegen die Python-Seite geprueft.
- Die Store-Beschreibung sagt jetzt beides: der extrahierte Text liegt im App-Volume und Sicherungen erfassen ihn, und nichts davon verlaesst den Server.

## Task Commits

1. **Task 1: Wortlistenpaket und Lizenztext ins Laufzeitimage** , `4a74d15`
2. **Task 2: Routen, Umgebungsvariablen, gekoppelte Version und die Datenschutzaussage** , `226833f`

## Eigene Messungen am gebauten Image

Lokaler `docker build` des Backends (amd64) und Kontrolle im fertigen Image:

| Zahl | Wert | Wie gemessen |
|---|---|---|
| `/usr/share/dict/ngerman` | 356.010 Zeilen, 4.725.887 Byte | `wc -lc` im Image |
| Paketversion und Architektur | `20161207-15`, `all` | `dpkg-query -W` im Image |
| Lizenztext | 4.826 Byte, `-r--r--r--`, 9 GPL-Nennungen | `ls -l` und `grep -c` im Image |
| Groesse der apt-Schicht | 8,2 MB (davon 4,6 MB `/usr/share/dict`) | `docker history` und `du -sh` |
| Zusatzpaket | `dictionaries-common` 1.30.10, 711 kB | `dpkg-query -W` im Image |
| Laufzeitnutzer | uid 1000 | `id -u` im Image |
| Netz beim Lesen der Liste | nicht noetig | Kontrolle lief mit `--network none` |

Die drei Zahlen der Wortliste decken sich exakt mit RESEARCH und Plan 02-01. Die apt-Schicht ist mit 8,2 MB groesser als die reine Datei, weil `dictionaries-common` und die dpkg-Metadaten mitkommen; das steht so in `THIRD-PARTY.md`, statt die 4,6 MB als Gesamtpreis auszugeben.

**Store-Validierungsweg lokal nachgestellt** (derselbe gepinnte appstore-Commit `5c4373d7` wie in `php.yml`, `xsltproc pre-info.xslt | xmllint --schema info.xsd` in einem Wegwerf-Container): beide `info.xml` melden `- validates`. Das normalisierte Dokument zeigt wie erwartet, dass der `routes`-Block still verschwindet und `environment-variables`, `version` und `image-tag` erhalten bleiben.

## Paarweiser Abgleich der Umgebungsvariablen

Abnahmekriterium von Task 2, jede in `info.xml` genannte Variable gegen die Python-Seite:

| Variable in info.xml | Vorgabe dort | Gelesen in | Vorgabe dort | Gleich |
|---|---|---|---|---|
| `FINDLING_LOG_LEVEL` | `info` | `backend/src/findling/main.py:47` | `"info"` | ja |
| `FINDLING_LANGUAGES` | `de,en` | `config.py::_languages` | `DEFAULT_LANGUAGES = ("de", "en")` | ja |
| `FINDLING_COMPOUND_DICT` | `full` | `config.py::_compound_dict` | `DEFAULT_COMPOUND_DICT = "full"` | ja |
| `FINDLING_MAX_FILE_BYTES` | `52428800` | `config.py::settings` | `MAX_FILE_BYTES = 52_428_800` | ja |

`FINDLING_LOG_LEVEL` ist die einzige, die nicht in `config.py` steht: sie stammt aus Phase 1 und wird beim Aufsetzen des Loggings in `main.py` gelesen, bevor `config.py` ueberhaupt gebraucht wird. Umgekehrt liest `config.py` sechzehn weitere `FINDLING_`-Variablen, die bewusst **nicht** in `info.xml` stehen: sie sind Feinjustierung fuer einen Fehlerfall, kein Admin-Schalter, und jeder Eintrag in der Einstellungsliste ist eine Einladung, daran zu drehen.

## Decisions Made

- **Die Wortliste bleibt im Laufzeitimage.** Ein in der Build-Stage destilliertes Artefakt haenge an einer Bauentscheidung; die Aufbereitung als Startschritt haengt an einem SHA-256, der neben `schema_version` in der Metatabelle steht und beim Oeffnen geprueft wird (T-02-71).
- **Harte Versionspinnung statt `wngerman` ohne Version.** Bewegt Debian das Paket, faellt der Bau laut um, statt jedes deutsche Suchergebnis leise zu verschieben. Der Preis ist ein bekannter Wartungspunkt, der Gegenwert ist Reproduzierbarkeit ueber amd64 und arm64 (`Architecture: all`).
- **`test -s` auf beide Dateien im selben RUN.** Ein Image ohne Lizenztext darf nicht entstehen; das ist billiger als eine Zusage in einer Dokumentationsdatei, die niemand prueft.
- **`status` bekommt ADMIN, nicht USER.** Zaehler und Versionen des Index sind Betreibersache. Die Route wird in Phase 2 nur befuellt, Phase 4 baut die Anzeige darauf.
- **Die Datenschutzaussage steht in der App-Beschreibung, nicht nur in der Doku.** Der Store-Text ist das Einzige, was ein Admin vor der Installation liest.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] `image-tag` musste mit der Version steigen**

- **Found during:** Task 2
- **Issue:** Der Plan nennt nur `<version>`. `docker.yml` vergleicht bei einem `v*`-Tag aber `image-tag`, beide `info.xml`-Versionen und den git-Tag und bricht bei Abweichung ab; AppAPI zieht ausserdem `registry/image:<image-tag>` bei der Installation. Version 0.2.0 mit `image-tag` 0.1.0 waere ein Release, das das Vorgaengerimage installiert, und ein garantiert roter Release-Lauf.
- **Fix:** `<image-tag>` ebenfalls auf 0.2.0, Kopplungskommentar im Dateikopf nennt jetzt alle drei Werte und den Vergleich in `docker.yml`.
- **Files modified:** `backend/appinfo/info.xml`
- **Verification:** `grep -c '<version>0.2.0</version>'` bleibt 1 (das Abnahmekriterium ist unberuehrt), das normalisierte Store-Dokument zeigt `<image-tag>0.2.0</image-tag>`.
- **Committed in:** `226833f`

**2. [Rule 1 - Bug] Der Dockerfile-Kopf behauptete das Gegenteil dessen, was die Datei jetzt tut**

- **Found during:** Task 1
- **Issue:** Der einleitende Kommentar sagte woertlich "The runtime stage installs no package at all, on purpose" und begruendete das mit 58 MB gesparter apt-Schicht. Nach Task 1 ist das falsch, und ein falscher Kommentar an genau der Stelle, die eine Regel erklaert, ist schlimmer als gar keiner: der naechste Leser haelt die neue Zeile fuer ein Versehen und entfernt sie.
- **Fix:** Der Kopf sagt jetzt, dass genau ein Paket installiert wird, dass es Daten und kein Werkzeug ist, und verweist auf die Begruendung an der installierenden Zeile.
- **Files modified:** `backend/Dockerfile`
- **Verification:** Gegenlesen; die 58-MB-Begruendung fuer supervisor, curl und ca-certificates bleibt unveraendert gueltig.
- **Committed in:** `4a74d15`

**3. [Rule 2 - Missing critical] `dictionaries-common` wird mitgeliefert und stand nirgends**

- **Found during:** Task 1
- **Issue:** `wngerman` zieht `dictionaries-common` 1.30.10 auch mit `--no-install-recommends` als harte Abhaengigkeit herein. Eine Lizenzdatei, die "jedes mitgelieferte Fremdartefakt" verspricht und ein tatsaechlich ausgeliefertes Paket auslaesst, ist genau die Art Luecke, die sie verhindern soll.
- **Fix:** Eigene Tabelle in `THIRD-PARTY.md` mit Version, Grund der Anwesenheit (ispell-Registrierung, von Findling nie aufgerufen) und Lizenz (GPL-2+ und GPL-3+ in Teilen, beide ueber GPLv3 mit AGPL-3.0 vertraeglich), dazu die gemessene Schichtgroesse.
- **Files modified:** `THIRD-PARTY.md`
- **Verification:** `dpkg-query -W dictionaries-common` und `/usr/share/doc/dictionaries-common/copyright` im gebauten Image gelesen.
- **Committed in:** `4a74d15`

### Nicht lokal pruefbare Abnahmekriterien

Beide Aufgaben verlangen einen gruenen CI-Lauf (`gh run list --workflow=docker.yml` beziehungsweise `--workflow=php.yml`). Dieser Executor arbeitet in einem nicht gepushten Worktree-Branch; ein CI-Lauf ist erst nach dem Zusammenfuehren der Welle moeglich, und `gh run list` wuerde den letzten Lauf auf `main` melden, also eine Aussage ueber fremden Code. Nach der Projektregel wird das dokumentiert statt simuliert. Ersatzweise lokal ausgefuehrt:

| CI-Kriterium | Lokaler Ersatz | Ergebnis |
|---|---|---|
| `docker.yml` gruen | `docker build` des kompletten Backends, danach Kontrolle von Wortliste, Lizenztext, Paketversion und uid im fertigen Image | gruen, amd64 |
| `docker.yml` gruen fuer arm64 | **nicht ausgefuehrt**, kein arm64-Runner vorhanden | offen, siehe unten |
| `php.yml` gruen (XSD-Gate) | `xsltproc pre-info.xslt \| xmllint --schema info.xsd` mit demselben gepinnten appstore-Commit, in einem Wegwerf-Container, ueber beide `info.xml` | beide "- validates" |

**Zum arm64-Risiko:** `wngerman` ist `Architecture: all`, das Paket ist auf beiden Architekturen dieselbe Datei, und die geaenderten Zeilen enthalten nichts Architekturabhaengiges. Das Restrisiko liegt beim Basisimage, das ohnehin per Digest als Multi-Plattform-Index gepinnt ist. Der erste Lauf von `docker.yml` nach dem Zusammenfuehren ist trotzdem der Beleg und sollte beobachtet werden.

---

**Total deviations:** 3 auto-fixed (2x Rule 2, 1x Rule 1)
**Impact on plan:** Kein Scope Creep. Zwei der drei folgen zwingend aus dem, was der Plan verlangt (Version heben, Lizenzpflicht erfuellen), die dritte haelt eine Kommentarzusage wahr, die sonst in ihr Gegenteil gekippt waere.

## Issues Encountered

- **`docker run` mit `sh -c` griff zunaechst nicht.** Das Image hat einen ENTRYPOINT (`init.sh`), der Argumente nicht als Kommando ausfuehrt; die Kontrolle brauchte `--entrypoint sh`. Kein Befund am Image, nur eine Falle beim Nachmessen, die hier steht, damit sie nicht zweimal Zeit kostet.
- **`docker run -v` unter Git Bash.** Die Pfadumschreibung von MSYS macht aus `/w` ein `W:/`; `MSYS_NO_PATHCONV=1` plus absoluter Windows-Pfad ist der Weg. Betrifft nur die lokale Kontrolle, nichts im Repository.

## User Setup Required

Keine. Der Bau braucht Netz fuer `apt-get` und die Basisimages, wie bisher; die App selbst laedt beim Start weiterhin nichts.

## Next Phase Readiness

- **02-04 (PHP-Haelfte)** muss `php/appinfo/info.xml` ebenfalls auf 0.2.0 heben. Solange das aussteht, wuerde ein Release-Tag am Versionsvergleich in `docker.yml` scheitern; im normalen Push-Lauf ist es folgenlos.
- **02-08 (Snippets)** und die Statusroute haben ihre Deklaration; die Endpunkte selbst entstehen in ihren eigenen Plaenen. Bis dahin nennt `info.xml` zwei Routen, die der Container noch nicht bedient. Das ist folgenlos, weil AppAPI die Liste erst bei der Installation liest, und es ist die richtige Reihenfolge: die Deklaration muss vor dem Release stehen, nicht vor dem Code.
- **Phase 4 (Adminseite)** kann `status` mit `ADMIN` voraussetzen.
- **Phase 5 (Verpackung)** hat mit `THIRD-PARTY.md` die Lizenzuebersicht, die eine Store-Einreichung braucht.

Kein Blocker.

## Threat Model Coverage

| Threat ID | Umsetzung |
|---|---|
| T-02-71 | Kein Download beim Start; Paket gepinnt im Image; das abgeleitete Artefakt traegt den SHA-256 aus Plan 02-01 |
| T-02-72 | Genau drei Routen, `grep -c 'PUBLIC'` liefert 0, `heartbeat`/`enabled`/`init` ohne Eintrag |
| T-02-73 | `status` mit `access_level` ADMIN, Kommentar haelt fest, dass die Antwort keine Pfade und keine Suchbegriffe traegt |
| T-02-74 | Vorgabewerte in `info.xml` und auf der Python-Seite paarweise geprueft, siehe Tabelle oben |
| T-02-75 | Akzeptiert und ausgesprochen: die Store-Beschreibung nennt Volume und Sicherungen |
| T-02-76 | Version, `image-tag` und der Vergleich in `docker.yml` im Dateikopf benannt; die PHP-Haelfte zieht in 02-04 nach |

Keine neuen sicherheitsrelevanten Flaechen: dieser Plan legt Daten und Metadaten ab, er fuegt keinen Endpunkt und keinen Codepfad hinzu.

## Known Stubs

Keine. Beide geaenderten Dateien sind Metadaten beziehungsweise Bauanweisung und in ihrem Endzustand; die zwei deklarierten Routen sind absichtlich vor ihren Implementierungen da (siehe Next Phase Readiness).

## Self-Check: PASSED

- `THIRD-PARTY.md`, `backend/Dockerfile`, `backend/appinfo/info.xml` liegen im Worktree.
- `4a74d15` und `226833f` stehen im Log von `gsd/agent-02-07`.
- `git diff --diff-filter=D` ueber beide Commits ist leer, es wurde nichts geloescht.
- `STATE.md`, `ROADMAP.md` und `REQUIREMENTS.md` wurden nicht angefasst; die erfuellten Anforderungen SRCH-01 und IDX-06 stehen im Frontmatter fuer den Orchestrator.

---
*Phase: 02-indexkern-und-volltextsuche*
*Completed: 2026-08-31*
