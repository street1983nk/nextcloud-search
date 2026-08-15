---
phase: 01-integrationsbeweis
plan: 01
subsystem: infra
tags: [github, agpl-3.0, app-store, store-identity, repo-setup, gitignore]

# Dependency graph
requires: []
provides:
  - "Eingefrorene Store-Identitaet: findling (Apps) und findling_backend (External Apps), belegt frei in beiden Store-Feeds"
  - "Oeffentliches GitHub-Repo street1983nk/nextcloud-search mit AGPL-3.0"
  - "Mono-Repo-Verzeichnisgeruest php/, backend/, testdata/corpus/, .github/workflows/"
  - "Repo-lokale Commit-Identitaet street1983nk <k.cherif@outlook.de>, die die globale Akara-Adresse ueberschreibt"
  - "Strukturelle Sperre gegen committetes Schluesselmaterial (.gitignore)"
affects: [01-02, 01-03, 01-04, 01-05, csr, docker, ci]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Mono-Repo mit pfadgetrennten Bereichen php/ und backend/"
    - "Identitaets-Freeze als blockierender Vorgang vor jedem ID-schreibenden Commit"
    - "Kontotrennung ueber repo-lokale git config statt globaler Konfiguration"

key-files:
  created:
    - docs/store-identity.md
    - LICENSE
    - README.md
    - .gitignore
    - php/.gitkeep
    - backend/.gitkeep
    - testdata/corpus/.gitkeep
    - .github/workflows/.gitkeep
  modified: []

key-decisions:
  - "App-IDs endgueltig eingefroren: Companion findling im Store-Bereich Apps, ExApp findling_backend im Store-Bereich External Apps (context_chat-Muster)"
  - "Repo-Erzeugung und Push in zwei Schritten statt gh repo create --source --push, weil der Executor auf einem Worktree-Branch laeuft: Push explizit als HEAD:refs/heads/main"
  - "gitignore ueber die Planvorgabe hinaus um .crt, vendor/, dist/, build/, .claude-active und .claude/worktrees/ erweitert"
  - "PKG-02 bleibt offen, weil die zweite Haelfte der Anforderung (beide CSRs eingereicht) in Plan 01-03 liegt"

patterns-established:
  - "Store-Identitaet: jede ID-Aenderung ist eine Terminaenderung, nicht eine Kosmetik, dokumentiert in docs/store-identity.md"
  - "Sicherheitsrelevante .gitignore-Eintraege werden im Dateikopf begruendet, nicht kommentarlos gesetzt"

requirements-completed: []

# Metrics
duration: 4 min
completed: 2026-08-15
---

# Phase 1 Plan 01: Store-Identitaet und oeffentliches Repo Summary

**App-IDs findling und findling_backend live gegen beide Store-Feeds als frei belegt, unwiderruflich eingefroren und in einem oeffentlichen AGPL-3.0-Repo mit Mono-Repo-Geruest und erzwungener Kontotrennung verankert.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-08-15T10:37:38Z
- **Completed:** 2026-08-15T10:40:53Z
- **Tasks:** 2
- **Files created:** 8

## Accomplishments

- Beide App-IDs unmittelbar vor dem Freeze live geprueft: `findling` und `findling_backend` haben in `apps.json` (Plattform 34.0.0) und in `appapi_apps.json` je 0 Treffer, ein zusaetzlicher Substring-Sweep ueber beide Feeds findet den Namensstamm `findling` ueberhaupt nicht.
- `docs/store-identity.md` fixiert IDs, Store-Bereiche, Namespace `OCA\Findling`, Python-Paket, Image-Name, Repo, Lizenz, Freeze-Datum, den Verfuegbarkeitsbeleg und die Begruendung samt gemessener CSR-Laufzeiten (Median 3 bis 4 Tage, Ausreisser 11 Tage).
- Oeffentliches Repo `github.com/street1983nk/nextcloud-search` angelegt, GitHub erkennt die Lizenz als `agpl-3.0`, einziger Collaborator ist der Owner.
- Commit-Identitaet greift: die repo-lokale Konfiguration `street1983nk <k.cherif@outlook.de>` ueberschreibt die global gesetzte Akara-Adresse `khaled.cherif@akara-solutions.de`. Der gesamte Verlauf enthaelt genau eine Identitaet und null Co-Authored-By-Trailer.
- Schluesselmaterial kann strukturell nicht mehr committet werden (`*.key`, `*.pem`, `*.crt`, `.env`, `.env.*`), geprueft ueber `git ls-files`.

## Task Commits

1. **Task 1: App-IDs einfrieren und Verfuegbarkeit belegen** - `19c75b4` (docs)
2. **Task 2: Repo, Lizenz, Verzeichnisgeruest, Commit-Identitaet** - `93f9e02` (chore)

Remote-Stand nach dem Push: `origin/main` = `93f9e02e0b9a8f73b91a03088de40e0051ae042a`.

## Files Created/Modified

- `docs/store-identity.md` - Verbindliche Fixierung beider App-IDs mit Datum, Verfuegbarkeitsbeleg, Begruendung und Aenderungsverfahren
- `LICENSE` - AGPL-3.0-Volltext, unveraendert von gnu.org
- `README.md` - Englische Projektbeschreibung: Zwei-App-Modell, Zielhardware, NC-Fenster 32 bis 35, Privacy-Aussage, Repo-Layout, Statuszeile "walking skeleton, not usable yet"
- `.gitignore` - Schluessel- und Secret-Ausschluss mit begruendetem Dateikopf, dazu Python-, PHP-, Node- und Laufzeitartefakte
- `php/.gitkeep`, `backend/.gitkeep`, `testdata/corpus/.gitkeep`, `.github/workflows/.gitkeep` - Mono-Repo-Geruest

## Decisions Made

- **Checkpoint Task 1 ohne erneute Rueckfrage aufgeloest.** Der Owner hat beide IDs am 15.08.2026 entschieden und schriftlich fixiert (Commit `5fecd10` "docs(01): freeze app ids", nachlesbar in `01-CONTEXT.md` und `PROJECT.md`). Der Checkpoint verlangte genau diese Bestaetigung; der vorliegende Entscheid wurde als Bestaetigung dokumentiert und die Ausfuehrung fortgesetzt. Der irreversible Teil ist damit belegt und nicht stillschweigend vorweggenommen.
- **Push-Weg abgewandelt.** Der Plan sah `gh repo create --source . --remote origin --push` vor. Der Executor laeuft auf dem Branch `worktree-agent-afdacbf5040ef1782`; ein `--push` haette diesen Branchnamen oeffentlich gemacht. Stattdessen: Repo ohne Push angelegt, `origin` gesetzt, dann `git push origin HEAD:refs/heads/main`. Ergebnis identisch, Remote-Default-Branch ist `main`.
- **PKG-02 nicht abgehakt.** Die Anforderung besteht aus zwei Haelften ("beide IDs eingefroren" und "beide CSRs eingereicht"). Die zweite Haelfte liegt in Plan 01-03. `REQUIREMENTS.md` wurde deshalb bewusst nicht angefasst, auch um einen Schreibkonflikt mit parallel laufenden Worktree-Agenten zu vermeiden.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] .gitignore um Agenten-Scratchstate und weitere Artefakte erweitert**
- **Found during:** Task 2 (Repo-Grundeinrichtung)
- **Issue:** Die Planvorgabe war als Minimum formuliert. Im Arbeitsbaum lag eine untrackierte Datei `.claude-active`, und die Agenten-Worktrees liegen unter `.claude/worktrees/`. In einem oeffentlichen Repo ist beides Muell mit Informationsgehalt ueber interne Ablaeufe. Ausserdem fehlten `vendor/`, `dist/`, `build/` und `.crt`.
- **Fix:** Eintraege ergaenzt, Schluesselblock im Dateikopf begruendet (Bezug auf die realen "private key exposed"-Vorgaenge im Zertifikats-Repo).
- **Files modified:** `.gitignore`
- **Verification:** `git status --short` zeigt `.claude-active` nicht mehr; `git ls-files | grep -Ec '\.key$|\.pem$'` liefert 0.
- **Committed in:** `93f9e02`

**2. [Rule 3 - Blocking] Commit-Scope am GSD-Format statt an der woertlichen Planvorgabe**
- **Found during:** Task 2
- **Issue:** Der Plan gab die Commit-Nachricht woertlich als `chore: initialise ...` vor, das Commit-Protokoll verlangt den Scope `{phase}-{plan}`.
- **Fix:** `chore(01-01): initialise public repository with AGPL-3.0 and directory layout`. Beide Vorgaben erfuellt.
- **Files modified:** keine
- **Verification:** `git log --oneline -2`
- **Committed in:** `93f9e02`

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 blocking)
**Impact on plan:** Kein Scope-Zuwachs. Beide Anpassungen dienen der Sicherheit beziehungsweise der Formatkonsistenz.

## Verification Results

Alle Abnahmekriterien beider Tasks wurden ausgefuehrt und bestanden:

| Kriterium | Ergebnis |
|-----------|----------|
| `apps.json` Treffer fuer `"id": "findling"` | 0 PASS |
| `appapi_apps.json` Treffer fuer `"findling_backend"` | 0 PASS |
| `docs/store-identity.md` mit beiden IDs, beiden Store-Bereichen, Freeze-Datum | PASS |
| Owner-Freeze schriftlich belegt | PASS (Commit `5fecd10`, 15.08.2026) |
| `gh repo view --json visibility,licenseInfo` | `PUBLIC` + `agpl-3.0` PASS |
| `git log -1 --format='%an <%ae>'` | `street1983nk <k.cherif@outlook.de>` PASS |
| `git log --format=%B \| grep -ci 'co-authored-by'` | 0 PASS |
| `grep -c '^\*\.key$' .gitignore` | 1 PASS |
| `git ls-files \| grep -Ec '\.key$\|\.pem$'` | 0 PASS |
| `git ls-remote origin HEAD` | `93f9e02e...` PASS |
| README enthaelt `findling_backend` ausserhalb von Kommentaren | 1 PASS |
| `git log --format='%an <%ae>' \| sort -u` | genau eine Identitaet PASS |
| Collaborators | nur `street1983nk` PASS |

## Threat Model Coverage

| Threat ID | Status | Beleg |
|-----------|--------|-------|
| T-01-01 Spoofing der Commit-Identitaet | mitigiert | repo-lokale `git config` schlaegt die globale Akara-Adresse, verifiziert am Verlauf |
| T-01-02 Information Disclosure im oeffentlichen Repo | mitigiert | `.gitignore` vor dem ersten Push aktiv, `git ls-files`-Gate ohne Treffer |
| T-01-03 Tampering an der App-ID-Identitaet | mitigiert | Freeze mit Live-Beleg vor dem ersten ID-schreibenden Commit, dokumentiertes Aenderungsverfahren |

## Issues Encountered

None.

## User Setup Required

Keine externe Dienstkonfiguration in diesem Plan. Anschlusspflicht des Owners in Plan 01-03: die beiden CSR-Pull-Requests gegen `nextcloud/app-certificate-requests` einreichen. Zusaetzlich parallel vorzubereiten: Entwicklerkonto auf apps.nextcloud.com und `APPSTORE_TOKEN`.

## Next Phase Readiness

- Die Identitaet steht, also duerfen ab jetzt Dateien, Namespaces und Verzeichnisse die IDs tragen. Damit sind die Wave-2-Plaene (PHP-Companion, ExApp-Geruest) freigegeben.
- Das Verzeichnisgeruest liegt an den Stellen, die die CI-Workflows spaeter pfadgefiltert ansteuern.
- Offen und bewusst nicht in diesem Plan: Branch-Protection auf `main` sowie REUSE/SPDX-Header, beide aus der Repo-Grundeinrichtung der RESEARCH-Frage 7. Branch-Protection sollte erst nach dem Merge der Wave-1-Worktrees gesetzt werden, sonst blockiert sie die laufende Phase.

## Self-Check: PASSED

Alle acht erzeugten Dateien existieren auf der Platte. Beide Task-Commits (`19c75b4`, `93f9e02`) sind im Verlauf vorhanden, der Push nach `origin/main` ist ueber `git ls-remote` bestaetigt.

---
*Phase: 01-integrationsbeweis*
*Completed: 2026-08-15*
