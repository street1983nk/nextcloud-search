---
phase: 01-integrationsbeweis
plan: 04
subsystem: api
tags: [fastapi, nc-py-api, appapi, pydantic, exapp, walking-skeleton, authentication]

# Dependency graph
requires:
  - phase: 01-02
    provides: "uv-Projekt backend/ mit exakten Pins, fuenf Qualitaetsgates und Gate A als AST-Test der Nur-Lesen-Invariante"
provides:
  - "Lauffaehige ExApp: AppAPI-Handshake ueber PUT /enabled, GET /heartbeat, POST /init"
  - "POST /search mit dem eingefrorenen Klartext-Protokoll (fileId, path, title, snippet, highlights, score, mtime)"
  - "Unfaelschbarer Container-Beweis: Hostname, UTC-Zeitstempel und Header-Nutzer-ID im snippet"
  - "nc/client.py als einzige nc_py_api-Grenze mit current_user_id als Identitaets-Zugang"
  - "Ablehnung jeder Nutzer-ID aus dem Request-Body mit HTTP 400 statt stiller Ignoranz"
affects: [01-05, 01-06, 01-07, 01-08, phase-02-indexierung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Grenzschicht-Re-Export: Fachmodule importieren AppAPI-Bausteine ausschliesslich aus findling.nc.client"
    - "Identitaet nur aus dem signierten Header, Body-Identitaet wird abgelehnt statt ignoriert"
    - "Klartext-Protokoll: snippet ohne Markup, Hervorhebungen als Zeichenoffsets"
    - "TDD je Task in zwei Commits (test -> feat) mit importfaehigem Skelett im RED-Schritt, damit die fuenf Gates auch dort gruen bleiben"

key-files:
  created:
    - backend/src/findling/nc/__init__.py
    - backend/src/findling/nc/client.py
    - backend/src/findling/main.py
    - backend/src/findling/api/__init__.py
    - backend/src/findling/api/search.py
    - backend/tests/test_lifecycle.py
    - backend/tests/test_search_canary.py
  modified: []

key-decisions:
  - "Die noqa-Zeile fuer fileId aus dem Plan wurde durch einen Begruendungskommentar ersetzt: die Namensregeln (N) sind im konfigurierten ruff-Regelsatz nicht aktiv, ein noqa darauf ist selbst ein Fehler (RUF100)"
  - "await nc.user liegt in nc/client.py (current_user_id), nicht in api/search.py, damit die AppAPI-Oberflaeche vollstaendig hinter der Grenzschicht bleibt"
  - "set_handlers wird mit einem gezielten pyright-ignore aufgerufen, weil die Signatur der Bibliothek noch die synchrone Client-Klasse zulaesst, die in 0.31.0 verschwindet"
  - "Docstrings ausserhalb von nc/client.py nennen den Bibliotheksnamen nicht, damit auch ein einfaches grep die Grenze bestaetigt und nicht nur der AST-Test"
  - "limit-Verstoss bleibt bei 422, nur extra_forbidden wird auf 400 gehoben: 400 markiert genau den Rechteumgehungsversuch und nichts sonst"

patterns-established:
  - "Neue Routen werden hinter APP.add_middleware(AppAPIAuthMiddleware) eingehaengt, nie davor"
  - "Beweisfunktionen sind reine Funktionen (build_canary_hits), damit die Aussage ohne HTTP-Runde pruefbar ist"
  - "Verifikation nutzt ein anderes Muster als die Umsetzung: der Zeitstempel wird im Test per fromisoformat zurueckgelesen, nicht per nachgebautem Formatstring"

requirements-completed: [COMP-01]

# Metrics
duration: 14 min
completed: 2026-08-15
---

# Phase 1 Plan 04: ExApp-Skelett mit AppAPI-Handshake und Container-Beweis Summary

**Lauffaehige ExApp, die den AppAPI-Handshake beantwortet und auf POST /search einen Treffer liefert, der Containernamen, UTC-Zeitstempel und die aus dem signierten Header gelesene Nutzer-ID als Klartext traegt.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-08-15T12:55:00Z
- **Completed:** 2026-08-15T13:09:00Z
- **Tasks:** 2 (beide als TDD-Zyklus mit je zwei Commits)
- **Files created:** 7

## Accomplishments

- `backend/src/findling/nc/client.py` ist die einzige nc_py_api-Grenze des Pakets und reicht `AppAPIAuthMiddleware`, `AsyncNextcloudApp`, `anc_app`, `run_app`, `set_handlers` sowie die eigene Funktion `current_user_id` weiter. Die schreibenden Bezeichner und der Impersonation-Einstieg sind bewusst nicht dabei: was die Grenze nicht herausgibt, kann ein Aufrufer nicht erreichen.
- `backend/src/findling/main.py` registriert im Lifespan die drei Pflichtrouten (`PUT /enabled`, `GET /heartbeat`, `POST /init`), haengt `AppAPIAuthMiddleware` ein und loggt beim Start den gewaehlten Bindungsmodus. Genau diese Zeile spart laut Pitfall 5 Stunden Diagnose, wenn ein Container unter HaRP zwar laeuft, aber am falschen Endpunkt lauscht.
- `POST /search` liefert das eingefrorene Protokoll und darin einen Treffer, der nur im Container entstanden sein kann. Beweis aus dem realen Durchstich: `produced inside container MD-43700650276 at 2026-08-15T11:09:17+00:00 for user alice`.
- Die Rechteumgehung aus dem Threat-Register ist geschlossen: ein Body mit `userId` erreicht den Handler nicht (`extra="forbid"`) und wird vom Validierungs-Handler mit **400** und der Meldung `user identity is taken from the AppAPI header only` beantwortet. Ohne Identitaet im Header antwortet der Endpunkt mit **401**.
- 18 Tests gruen, alle fuenf Gates gruen, Gate A weiterhin ohne Verstoss: genau eine Datei importiert nc_py_api.

## Task Commits

1. **Task 1 RED: fehlschlagende Tests des AppAPI-Handshakes** - `d3bac09` (test)
2. **Task 1 GREEN: Handshake, Middleware, Bindungsmodus-Log** - `1ed7d94` (feat)
3. **Task 2 RED: fehlschlagende Tests fuer Kanarienvogel und Identitaetsregeln** - `a53ed9b` (test)
4. **Task 2 GREEN: POST /search mit Container-Beweis** - `2600f04` (feat)

REFACTOR entfiel in beiden Zyklen: die GREEN-Implementierungen bestanden alle fuenf Gates ohne Nacharbeit.

## Files Created/Modified

- `backend/src/findling/nc/__init__.py` - Paketdocstring der Grenzschicht
- `backend/src/findling/nc/client.py` - einzige nc_py_api-Grenze, Re-Exporte plus `current_user_id`
- `backend/src/findling/main.py` - FastAPI-App, Lifespan mit `set_handlers`, Middleware, Router-Einbindung, Validierungs-Handler, `run_app`-Einstiegspunkt
- `backend/src/findling/api/__init__.py` - Paketdocstring der HTTP-Oberflaeche
- `backend/src/findling/api/search.py` - `SearchRequest`, `Hit`, `SearchResponse`, `build_canary_hits`, `POST /search`
- `backend/tests/test_lifecycle.py` - fuenf Behauptungen zum Handshake plus Dateicheck der nc_py_api-Grenze
- `backend/tests/test_search_canary.py` - sieben Testfaelle zu den sechs Behauptungen (limit-Grenze parametrisiert auf 0 und 101)

## Decisions Made

- **`await nc.user` bleibt in der Grenzschicht.** Der Plan nennt in `must_haves.key_links` das Muster `await .*\.user` fuer `api/search.py`, im Task-Text steht dagegen "Nutzer-ID ueber `current_user_id` aus der Grenzschicht holen". Beides zugleich geht nicht. Umgesetzt ist die Task-Anweisung: `search.py` ruft `await current_user_id(nc)`, der Await auf die async property liegt in `nc/client.py`. Das haelt die AppAPI-Oberflaeche vollstaendig hinter der Grenze, was der eigentliche Zweck des Artefaktvertrags ist (`provides: Middleware, Handler-Registrierung, Nutzer-ID`).
- **400 nur fuer `extra_forbidden`.** Ein zu grosses `limit` bleibt 422. Wuerde jeder Validierungsfehler zu 400, verloere der Statuscode genau die Aussage, wegen der er hier steht: hier hat jemand versucht, sich eine Identitaet zu geben.
- **Leerer String heisst "keine Identitaet".** `current_user_id` liefert `None` statt `""`, weil ein leerer Nutzername sonst wie ein gueltiger aussieht. Der signierte Header mit leerem Namen ist genau der Fall, den `test_missing_user_id_is_unauthorized` durchspielt.
- **Docstring-Disziplin an der Grenze.** Der Bibliotheksname steht nur in `nc/client.py`. Damit stimmt auch das Abnahmekriterium per `grep -l`, nicht nur der AST-Test. Das ist bewusst festgehalten, weil ein spaeterer erklaerender Kommentar in einem anderen Modul das Kriterium sonst kippt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `# noqa: N815` durch Begruendungskommentar ersetzt**
- **Found during:** Task 2 (RED)
- **Issue:** Der Plan verlangt fuer `fileId` eine noqa-Zeile. Die Namensregeln (`N`) stehen nicht im konfigurierten ruff-Regelsatz (CLAUDE.md: E,F,I,UP,B,ASYNC,S,SIM,C4,RUF,PT,RET,A,ISC). Ruff meldet die Direktive deshalb als `RUF100 Unused noqa directive (non-enabled: N815)`, das Lint-Gate war rot.
- **Fix:** Die Direktive entfaellt; ein dreizeiliger Kommentar traegt dieselbe Begruendung (Drahtformat gehoert der PHP-Seite) plus den Hinweis, warum hier kein noqa steht. Der Regelsatz wurde nicht angefasst, er ist eine globale Vorgabe.
- **Files modified:** backend/src/findling/api/search.py
- **Verification:** `uv run ruff check .` meldet "All checks passed!"
- **Committed in:** `a53ed9b`

**2. [Rule 1 - Bug] pyright-Fehler bei `set_handlers(app, enabled_handler)`**
- **Found during:** Task 1 (GREEN)
- **Issue:** Die Bibliothek typisiert den Parameter als `Callable[[bool, AsyncNextcloudApp | NextcloudApp], ...]`. Unser Handler nimmt nur die async Klasse, was pyright korrekt als Kontravarianz-Verstoss meldet (`reportArgumentType`). Das Typ-Gate war rot.
- **Fix:** Gezieltes `# pyright: ignore[reportArgumentType]` genau an der Aufrufstelle, mit Begruendung im Kommentar. Die Alternative waere gewesen, die synchrone Klasse in die eigene Signatur zu holen; die faellt in 0.31.0 weg und haette den Grund der Grenzschicht untergraben.
- **Files modified:** backend/src/findling/main.py
- **Verification:** `uv run pyright` meldet "0 errors"; die Handler-Registrierung ist im Test `test_heartbeat_answers_without_an_auth_header` real durchlaufen.
- **Committed in:** `1ed7d94`

**3. [Rule 3 - Blocking] Docstring von `nc/__init__.py` nannte den Bibliotheksnamen**
- **Found during:** Task 1 (RED)
- **Issue:** Der erklaerende Docstring enthielt die Zeichenkette `nc_py_api`. Damit listete `grep -rl 'nc_py_api' src/findling` zwei Dateien statt einer, und ein Abnahmekriterium war verletzt, obwohl kein Import existierte.
- **Fix:** Der Docstring beschreibt die Grenze jetzt ohne den Namen und haelt fest, dass das Absicht ist.
- **Files modified:** backend/src/findling/nc/__init__.py
- **Verification:** `grep -rn 'nc_py_api' src/findling --include='*.py' -l` liefert genau `src/findling/nc/client.py`
- **Committed in:** `d3bac09`

**4. [Rule 3 - Blocking] RED-Schritt von Task 1 mit async Platzhalter statt sync Platzhalter**
- **Found during:** Task 1 (RED)
- **Issue:** Ein synchroner Platzhalter-Handler haette die erste Behauptung sauber rot gemacht, aber `await enabled_handler(...)` im Test ist dann fuer pyright ein Typfehler ("str is not awaitable"). Das Typ-Gate waere im RED-Commit rot gewesen, was der Auftragsvorgabe "alle Gates lokal gruen vor jedem Commit" widerspricht.
- **Fix:** Der Platzhalter ist async, liefert aber `"not implemented"`. Damit waren im RED-Commit drei der fuenf Behauptungen rot (Rueckgabewert, Middleware, /heartbeat), die uebrigen zwei sind strukturell und bereits durch das Skelett erfuellt.
- **Files modified:** backend/src/findling/main.py
- **Verification:** RED-Lauf: 3 failed, 8 passed bei gruenen Gates; GREEN-Lauf: 11 passed
- **Committed in:** `d3bac09`

---

**Total deviations:** 4 auto-fixed (3 blockierend, 1 Bug)
**Impact on plan:** Kein Scope-Zuwachs, keine inhaltliche Aenderung am Protokoll oder an den Sicherheitszusagen. Abweichungen 1 und 2 sind Kollisionen zwischen Plantext und Werkzeugkonfiguration, 3 und 4 sind Nebenwirkungen der eigenen Abnahmekriterien beziehungsweise der TDD-Reihenfolge.

## Issues Encountered

- **StarletteDeprecationWarning bleibt sichtbar.** `fastapi.testclient` warnt, dass `httpx` zugunsten von `httpx2` abgeloest wird. Geprueft: die Klasse leitet von `UserWarning` ab, nicht von `DeprecationWarning` (`starlette/exceptions.py:36`). Der Gate `filterwarnings = ["error::DeprecationWarning"]` greift also korrekt nicht, und das Abnahmekriterium "kein DeprecationWarning" ist erfuellt. Die Warnung stammt aus der gepinnten Abhaengigkeitskette und ist nichts, was dieser Plan aendern darf.
- **Kein `/search` in der naiven Routenliste.** FastAPI 0.141 legt eingehaengte Router als `_IncludedRouter` ab, ein Filter auf `hasattr(r, "path")` uebersieht sie. Der Endpunkt existiert nachweislich: der Durchstich liefert 200 mit dem Beweis-Treffer. Wer spaeter Routen inventarisiert, darf sich nicht auf `APP.routes` mit diesem Filter verlassen.
- **Kein Containerlauf in diesem Plan.** Das Image ist Plan 01-07. Der Beweis-String traegt hier den Hostnamen des Entwicklungsrechners; im Container traegt er den Containernamen, was der eigentliche Beweiswert ist.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers. Alle fuenf mitigierten Eintraege sind umgesetzt und je durch einen Test belegt:

| Threat ID | Umsetzung | Beleg |
|-----------|-----------|-------|
| T-01-11 (Elevation of Privilege, Identitaet) | Identitaet nur aus `Depends(anc_app)`; `extra="forbid"` plus 400-Handler | `test_user_id_in_the_body_is_rejected` |
| T-01-12 (Spoofing, Header) | Keine eigene Header-Auswertung, ausschliesslich `AppAPIAuthMiddleware` | `test_app_carries_the_appapi_auth_middleware`, `test_missing_user_id_is_unauthorized` |
| T-01-13 (Impersonation ueber set_user) | Nicht re-exportiert, nicht verwendet; Gate A verbietet den Bezeichner | `grep -c 'set_user' src/findling/api/search.py` = 0, Gate A gruen |
| T-01-14 (Input Validation) | `min_length` fuer query, `ge`/`le` fuer limit, `extra="forbid"` fuer den Body | `test_limit_out_of_range_is_rejected[0]` und `[101]` |
| T-01-15 (Information Disclosure, Logging) | Geloggt werden nur Aktivierungszustand und Bindungsmodus, kein Suchbegriff, kein Snippet | Log des Durchstichs: eine Zeile, `binding mode: tcp 127.0.0.1:unset` |

## Known Stubs

Bewusste Platzhalter dieser Phase, laut CONTEXT.md ("KEINE Indexierung, KEINE echte Suche") und nicht zu beheben:

| Ort | Stub | Aufgeloest in |
|-----|------|---------------|
| `api/search.py`, `search()` | `del body`: der Suchbegriff wird nicht ausgewertet | Phase 2 (Indexierung) |
| `api/search.py`, `build_canary_hits` | Fester Treffer mit `fileId=0`, leerem `path` und `score=0.0` | Phase 2 |
| `api/search.py`, `Hit.highlights` | Immer leer, das Feld existiert nur, damit Phase 2 nichts umbauen muss | Phase 2 |

Open Question 2 der RESEARCH.md empfiehlt zusaetzlich einen zweiten Treffer auf eine echte Datei, damit auch der `resourceUrl`-Pfad bewiesen ist. Der Plan schreibt fuer diesen Task ausdruecklich "genau einen Hit" vor, deshalb ist er hier nicht gebaut. Der Punkt gehoert in die PHP-Haelfte beziehungsweise in den Integrationsplan der Phase.

## User Setup Required

None - keine externe Dienstkonfiguration noetig. Fuer den Containerbetrieb gelten die Pflicht-Umgebungsvariablen aus dem Plan (`APP_ID`, `APP_VERSION`, `APP_SECRET`, `APP_PORT`, `APP_HOST`, `NEXTCLOUD_URL`, `APP_PERSISTENT_STORAGE`, unter HaRP zusaetzlich `HP_SHARED_KEY`, `HP_FRP_ADDRESS`, `HP_FRP_PORT`, optional `HP_EXAPP_SOCK`); sie werden von AppAPI gesetzt, nicht vom Nutzer.

## Next Phase Readiness

- Die Container-Haelfte des Integrationsbeweises steht. Was jetzt fehlt, ist die PHP-Haelfte (`IProvider` plus `exAppRequest`) und das Image, damit `occ app_api:app:register` einen echten Container erreicht.
- Fuer Plan 01-07 (Dockerfile) ist der Bindungsmodus bereits sichtbar geloggt; `frpc`, `harp_connect.sh` und `supervisord` gehoeren von der ersten Dockerfile-Version an ins Image, sonst laeuft der Prozess unerreichbar (Pitfall 5).
- Das Antwortprotokoll ist eingefroren. Die PHP-Seite darf sich auf `fileId`, `path`, `title`, `snippet`, `highlights`, `score`, `mtime` verlassen; `snippet` ist garantiert Klartext.
- Offen und bewusst offen: kein echter Suchindex, kein zweiter Treffer auf eine reale Datei, keine Ausfuehrung im Container.

## Self-Check: PASSED

- Alle sieben angelegten Dateien auf der Platte vorhanden (`ls -l` bestaetigt, 179 bis 4479 Byte).
- Alle vier Commits im Log gefunden: `d3bac09`, `1ed7d94`, `a53ed9b`, `2600f04`.
- Abnahmekriterien Task 1: `pytest tests/test_lifecycle.py` 5 passed; `pytest tests/test_readonly_gate.py` 6 passed; `grep -rl 'nc_py_api' src/findling` liefert genau `src/findling/nc/client.py`; keine DeprecationWarning; alle fuenf Gates Exit 0.
- Abnahmekriterien Task 2: `pytest tests/test_search_canary.py` 7 passed; `grep -c 'extra="forbid"'` = 2; `grep -c 'def test_snippet_has_no_markup'` = 1; `grep -c 'set_user'` = 0; Gate A gruen; alle fuenf Gates Exit 0.
- Plan-Verifikation im echten Durchstich ausgefuehrt: `POST /search` liefert Hostname, ISO-Zeitstempel und Nutzer-ID als Klartext, Body-`userId` ergibt 400, fehlender Header ergibt 401, `/heartbeat` ergibt `{"status": "ok"}`. Die Sonde wurde danach geloescht, der Arbeitsbaum ist sauber.
- Keine Aenderung an STATE.md, ROADMAP.md oder REQUIREMENTS.md, kein Push.

---
*Phase: 01-integrationsbeweis*
*Completed: 2026-08-15*
