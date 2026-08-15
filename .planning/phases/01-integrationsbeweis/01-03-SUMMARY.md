---
phase: 01-integrationsbeweis
plan: 03
subsystem: infra
tags: [openssl, csr, code-signing, github, app-store, nextcloud]

requires:
  - phase: 01-01
    provides: eingefrorene App-IDs findling und findling_backend
provides:
  - Zwei RSA-4096-Schluesselpaare ausserhalb des Repos unter ~/.findling-secrets
  - Zwei CSRs mit verifiziertem CN, Fingerprints dokumentiert
  - Zwei vorbereitete Fork-Branches in street1983nk/app-certificate-requests
  - Zwei fertige PR-Texte und PR-Kommandos fuer den Owner
  - Dokumentierter Signaturweg bis zur signierten Release
affects: [05-release, store-einreichung, ci-release-automation]

tech-stack:
  added: []
  patterns:
    - "Signier-Schluessel liegen ausserhalb des Arbeitsbaums, nur der CSR-Text verlaesst das Verzeichnis"
    - "Fingerprint-Tabelle als Bindeglied zwischen lokalem Schluessel und spaeter ausgestelltem Zertifikat"

key-files:
  created: [docs/certificates.md]
  modified: [docs/store-identity.md]

key-decisions:
  - "Fork-Branches per GitHub-API statt lokalem Klon: der Executor ist worktree-isoliert, ein Klon ausserhalb des Worktrees ist nicht moeglich"
  - "Zwei getrennte Branches und zwei getrennte PRs, damit eine Rueckfrage zu einer App die andere nicht aufhaelt"
  - "Zugriffsschutz der Schluessel per Windows-ACL, weil chmod auf NTFS wirkungslos ist"

patterns-established:
  - "Pattern 1: Geheimnisse nie im Repo, Ablageort dokumentiert, Inhalt nie"
  - "Pattern 2: Owner-Schritte werden bis zur letzten automatisierbaren Zeile vorbereitet, dann uebergeben"

requirements-completed: []

duration: 9min
completed: 2026-08-15
---

# Phase 01 Plan 03: Store-Zertifikate Summary

**Zwei RSA-4096-CSRs mit verifiziertem CN fuer `findling` und `findling_backend`, Schluessel ausserhalb des Repos, beide Fork-Branches gepusht und beide Pull-Requests bis auf den Klick des Owners fertig.**

> **Status: am Owner-Checkpoint angehalten.** Task 1 und Task 2 sind abgeschlossen und committet. Task 3 ist ein `checkpoint:human-action` und laut CONTEXT.md ausdruecklich kein autonomer Schritt. Die zwei Pull-Requests sind nicht geoeffnet, kein Store-Konto angelegt, kein Secret gesetzt.

## Performance

- **Duration:** 9 min
- **Started:** 2026-08-15T10:45:11Z
- **Completed (bis Checkpoint):** 2026-08-15T10:54:01Z
- **Tasks:** 2 von 3 (Task 3 wartet auf den Owner)
- **Files modified:** 2

## Accomplishments

- Zwei RSA-4096-Schluesselpaare erzeugt und ausserhalb des Repos unter `~/.findling-secrets/` abgelegt; das Verzeichnis ist per ACL auf den Besitzer beschraenkt
- CN beider CSRs vor jeder Einreichung geprueft: `subject=CN=findling` und `subject=CN=findling_backend`; beide bestehen `openssl req -noout -verify`
- SHA256-Fingerprints beider oeffentlicher Schluessel dokumentiert, damit das spaeter ausgestellte Zertifikat gegen den lokalen Schluessel geprueft werden kann
- Fork `street1983nk/app-certificate-requests` gegen upstream `master` abgeglichen (identischer SHA) und zwei Branches darauf angelegt
- Beide CSRs in den Fork geladen; jeder Branch fuegt genau eine `.csr` hinzu und aendert sonst nichts
- Hochgeladene CSR-Texte gegengeprueft: beide Fingerprints stimmen mit den lokalen Schluesseln ueberein
- Signaturweg bis zur Release dokumentiert, inklusive Bezug der `.crt` nach dem Merge und Regeln fuer die drei CI-Secrets

## Task Commits

1. **Task 1: Schluesselpaare und CSRs erzeugen, Prozess dokumentieren** - `cc670d0` (docs)
2. **Task 1 Nachtrag: Rechteschutz korrigiert** - `56325bc` (fix)
3. **Task 2: Beide Pull-Requests im Fork vorbereiten** - `f2d6651` (docs)
4. **Task 3: Owner-Checkpoint** - offen, kein Commit

## Files Created/Modified

- `docs/certificates.md` - Ablageort der Schluessel, Warnung vor der Widerrufsrunde, Erzeugungs- und Pruefkommandos, Fingerprint-Tabelle, Bezug der `.crt`, `occ integrity:sign-app` fuer beide Apps, Regeln fuer `APP_PRIVATE_KEY`, `BACKEND_PRIVATE_KEY` und `APPSTORE_TOKEN`
- `docs/store-identity.md` - neuer Abschnitt "Certificate status": Tabelle je App mit Branch, PR-Titel, Status und Platzhaltern fuer PR-Link, Einreichungs- und Merge-Datum, dazu beide PR-Texte und die zwei fertigen `gh pr create`-Kommandos

## Artefakte ausserhalb des Repos

| Ablage | Inhalt | Anmerkung |
|--------|--------|-----------|
| `~/.findling-secrets/` (auf dieser Maschine `C:\Users\Student\.findling-secrets`) | `findling.key`, `findling.csr`, `findling_backend.key`, `findling_backend.csr` | ACL auf den Besitzer beschraenkt, Inhalte nirgends zitiert, nicht im Repo |
| Fork-Branch `findling-csr` | `findling/findling.csr`, Commit `2aacf62` | ein Diff-Eintrag, `added` |
| Fork-Branch `findling-backend-csr` | `findling_backend/findling_backend.csr`, Commit `71c913d` | ein Diff-Eintrag, `added` |

Fingerprints der oeffentlichen Schluessel, identisch lokal und im Fork:

| App id | SHA256 |
|--------|--------|
| `findling` | `781011795ce8b96c78a9fb485d98dd3cd95e0d2cc93c684beebd3263b81e5e3b` |
| `findling_backend` | `70b9340b24457bd29fb107519495e51b3fb7e4edbcf725334c33a229be6f8b8e` |

## Decisions Made

- **Fork-Branches per GitHub-API statt lokalem Klon.** Der Executor laeuft worktree-isoliert; Shell-Umleitungen und Git-Operationen ausserhalb des Worktrees werden abgelehnt. Ein Klon in ein temporaeres Verzeichnis war damit nicht moeglich. Das Ergebnis ist identisch: zwei Branches, je ein Commit, je eine Datei.
- **Der Fork existierte bereits** (angelegt am 2026-08-15 um 04:21 UTC fuer das Schwesterprojekt `mcp_connector`). Statt ihn neu anzulegen, wurde `master` gegen upstream abgeglichen; beide zeigen auf `ab45cad`, also wurde von einem sauberen Stand abgezweigt.
- **Zwei Branches, zwei PRs** statt eines gebuendelten PRs, wie in der Research begruendet.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Commit-Identitaet im Fork zeigte den Profilnamen statt des Handles**
- **Found during:** Task 2
- **Issue:** Die Contents-API setzt Author und Committer aus dem GitHub-Profil. Die Commits lauteten `Khaled Cherif <k.cherif@outlook.de>`, der Plan verlangt `street1983nk <k.cherif@outlook.de>`.
- **Fix:** Beide Commit-Objekte ueber die Git-Data-API mit explizitem Author und Committer neu erzeugt und die Branch-Refs darauf gesetzt. Baum und Inhalt unveraendert, Parent ist weiterhin upstream `master`.
- **Files modified:** keine im Repo, nur die zwei Fork-Branches
- **Verification:** `git/commits/<sha>` liefert fuer beide `name: street1983nk`, `email: k.cherif@outlook.de`; kein Co-Authored-By-Trailer
- **Committed in:** nicht in diesem Repo

**2. [Rule 1 - Bug] chmod schuetzt die privaten Schluessel auf NTFS nicht**
- **Found during:** Task 1, bei der Endkontrolle des Ablageverzeichnisses
- **Issue:** `chmod 700` und `chmod 600` melden Erfolg, `ls -l` zeigt danach weiterhin `0644`. Der Plan verlangt restriktive Rechte, und die Doku behauptete sie bereits.
- **Fix:** Zugriff per `icacls /inheritance:r /grant:r` auf den Besitzer beschraenkt; `docs/certificates.md` korrigiert, so dass der POSIX-Weg und der Windows-Weg samt Pruefkommando dastehen, mit dem Hinweis, dass `ls -l` hier nichts beweist.
- **Files modified:** `docs/certificates.md`
- **Verification:** `icacls` auf die Schluesseldatei listet nur das Besitzerkonto
- **Committed in:** `56325bc`

**3. [Rule 3 - Blocking] Fork-Arbeitskopie nicht moeglich, API-Weg gewaehlt**
- **Found during:** Task 2
- **Issue:** `gh repo fork --clone` in ein temporaeres Verzeichnis scheitert an der Worktree-Isolation des Executors; auch das Schreiben von Hilfsdateien ausserhalb des Worktrees wird abgelehnt.
- **Fix:** Branch-Anlage, Datei-Upload und Commit-Korrektur vollstaendig ueber die GitHub-API. Die CSR wurde per `openssl base64 -A -out` in eine temporaere Datei kodiert, hochgeladen und die temporaere Datei danach geloescht.
- **Files modified:** keine im Repo
- **Verification:** `compare/master...<branch>` zeigt je genau eine hinzugefuegte `.csr` und sonst nichts
- **Committed in:** nicht in diesem Repo

---

**Total deviations:** 3 auto-fixed (2 Bugs, 1 Blocker)
**Impact on plan:** Kein Scope-Zuwachs. Zwei der drei Abweichungen schliessen Luecken, die genau die Bedrohungen betreffen, die der Plan selbst listet (T-01-07 Schluesselschutz, Nachvollziehbarkeit der Identitaet). Die dritte ist ein Wegewechsel mit identischem Ergebnis.

## Issues Encountered

**Ein Acceptance-Kriterium ist so nicht erfuellbar und wurde sinngemaess geprueft.**
Task 2 verlangt, dass `gh pr list --repo nextcloud/app-certificate-requests --author street1983nk` leer ist. Die Liste enthaelt bereits PR **#1160 "Add certificate request for mcp_connector"** aus dem Schwesterprojekt, angelegt vor diesem Plan und ausserhalb seines Scopes. Geprueft wurde deshalb die Absicht des Kriteriums: es existiert kein Pull-Request zu `findling` oder `findling_backend`. Das ist erfuellt.

**Folge fuer Task 3:** Das dortige Kriterium "listet genau zwei offene PRs" wird nach der Einreichung **drei** ergeben, solange #1160 offen ist. Zu pruefen ist stattdessen, dass genau zwei PRs mit `findling` im Titel offen sind.

## User Setup Required

Keine USER-SETUP.md. Die offenen Handgriffe stehen im Checkpoint unten und in `docs/store-identity.md`.

## Next Phase Readiness

- Der Signaturweg fuer Phase 5 ist dokumentiert, die Vorlaufzeit kann mit dem Klick des Owners beginnen
- Blockiert nichts in Phase 1: bis zum Merge der Zertifikate laeuft der Bau ungehindert weiter
- `PKG-02` bleibt offen, bis beide Pull-Requests eingereicht sind; deshalb steht `requirements-completed` bewusst leer

## Offener Owner-Checkpoint (Task 3)

**Typ:** human-action, blockierend. Laut CONTEXT.md ausdruecklich kein autonomer Schritt.

Vorbereitet ist alles: beide Branches liegen im Fork und sind erreichbar, beide PR-Texte und beide Kommandos stehen in `docs/store-identity.md`.

1. Die zwei `gh pr create`-Kommandos aus `docs/store-identity.md` ausfuehren, oder die PRs im Webinterface oeffnen. Zwei getrennte PRs, je eine App, niemanden erwaehnen.
2. Beide PR-Links plus Einreichungsdatum in die Tabelle "Certificate status" eintragen lassen.
3. Auf https://apps.nextcloud.com ein Entwicklerkonto anlegen und unter https://apps.nextcloud.com/account/token den `APPSTORE_TOKEN` abholen.
4. Token als Secret hinterlegen: `gh secret set APPSTORE_TOKEN --repo street1983nk/nextcloud-search`. Gebraucht wird er erst in Phase 5, das Konto ist aber die Vorlaufzeit, die jetzt anfangen soll.
5. Erwartung: Median drei bis vier Tage bis zum Merge, Ausreisser bis elf Tage.

Ruecksignal: "submitted" mit beiden PR-Nummern.

## Self-Check: PASSED

- `docs/certificates.md` existiert im Arbeitsbaum: FOUND
- `docs/store-identity.md` existiert im Arbeitsbaum: FOUND
- Commit `cc670d0`: FOUND
- Commit `f2d6651`: FOUND
- Commit `56325bc`: FOUND
- `git ls-files | grep -Ec '\.(key|csr|pem|crt)$'` liefert 0: PASSED
- `grep -c 'BEGIN.*PRIVATE KEY' docs/certificates.md` liefert 0: PASSED
- Repo-weite Suche nach `BEGIN (RSA )?PRIVATE KEY`: keine Treffer
- `grep -v '^#' docs/certificates.md | grep -c 'integrity:sign-app'` liefert 2: PASSED
- `grep -v '^#' docs/store-identity.md | grep -c 'gh pr create'` liefert 2: PASSED
- CN-Pruefung beider CSRs: PASSED
- 4096-Bit-Pruefung beider CSRs: PASSED
- Fingerprint-Abgleich lokal gegen Fork: identisch fuer beide Apps
- Diff je Branch: genau eine hinzugefuegte `.csr`, keine weitere Datei

---
*Phase: 01-integrationsbeweis*
*Angehalten am Owner-Checkpoint: 2026-08-15*
