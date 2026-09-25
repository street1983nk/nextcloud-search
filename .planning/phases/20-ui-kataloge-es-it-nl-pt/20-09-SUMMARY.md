---
phase: 20-ui-kataloge-es-it-nl-pt
plan: 09
subsystem: l10n
tags: [ci-sprachbeweis, search-parity, sichtprobe, schlussabschnitt, owner-abnahme]

# Dependency graph
requires:
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 08
    provides: "alle zehn neuen Katalogdateien, L10N_CATALOGUES mit sechzehn Einträgen"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 02
    provides: "docs/l10n-catalogues.md mit sieben Abschnitten, Ladepfad-Beweis"
provides:
  - "Schritt 'The result page answers in every new language (core lang)' im Job search-parity: je Code es, it, nl, pt_PT, pt_BR Anwesenheit des übersetzten Titels und Abwesenheit von 'Search your file contents', Erwartungswert zur Laufzeit aus apps/findling/l10n/<code>.json"
  - "Rücksetzung der Nutzersprache per trap EXIT, auch nach einem Fehlschlag, --delete wenn vorher nichts gesetzt war"
  - "docs/l10n-catalogues.md Abschnitt 'Stand nach Phase 20': Dateiliste, Gate-Liste, CI-Beweis, Vorbehalt und vier Grenzen"
  - "Owner-abgenommene Sichtprobe in fünf Sprachen an der laufenden Instanz"
affects: [Phase 20 Abschluss, Verifikation Phase 20, KAT-01, KAT-02]

tech-stack:
  added: []
  patterns:
    - "Ein CI-Sprachbeweis liest seinen Erwartungswert aus dem Katalog und prüft die Abwesenheit des Quellsatzes als tragende Zusicherung"
    - "Geteilter Instanzzustand (Nutzersprache) wird per trap zurückgesetzt, nicht per Folgeschritt"
    - "Sichtprobe mit Gegenprobe: dieselbe Rest-Suche auf en muss Funde liefern, sonst beweist die Null nichts"

key-files:
  created:
    - .planning/phases/20-ui-kataloge-es-it-nl-pt/20-09-SUMMARY.md
  modified:
    - .github/workflows/integration.yml
    - docs/l10n-catalogues.md

key-decisions:
  - "Der Erwartungswert wird wie p() maskiert (htmlspecialchars, ENT_QUOTES), damit ein späteres Apostroph die Anwesenheitsprüfung nicht falsch rot macht"
  - "Fehler je Code werden gesammelt und am Ende gemeldet, statt beim ersten Code abzubrechen: ein roter Lauf nennt alle kaputten Sprachen auf einmal"
  - "Die Sichtprobe setzt die Sprache auf admin UND testuser, weil nur admin die Adminseite sieht; beide Ausgangswerte (de) sind wiederhergestellt"
  - "Schlüsselzahl nachgezählt: weiterhin 202, davon 5 Pluralschlüssel, datiert vermerkt"

requirements-completed: [KAT-01, KAT-02]

duration: 90min
completed: 2026-09-25
---

# Phase 20 Plan 09: CI-Sprachbeweis, Sichtprobe und Schlussabschnitt Summary

**Der Job `search-parity` beweist künftig je Sprachcode, dass die Ergebnisseite in dieser Sprache
antwortet und der englische Titel verschwunden ist, mit einem Erwartungswert aus dem Katalog statt
aus der YAML. Die Oberfläche ist in allen fünf neuen Sprachen an der laufenden Instanz gesehen und
vom Owner abgenommen ("approved", 25.09.2026).**

## Aufgaben und Commits

| Task | Name | Commit | Dateien |
| --- | --- | --- | --- |
| 1 | Sprachbeweis im Job search-parity | `1c80e26` | `.github/workflows/integration.yml` |
| 2 | Schlussabschnitt "Stand nach Phase 20" | `530bb7c` | `docs/l10n-catalogues.md` |
| 3 | Sichtprobe in fünf Sprachen (Checkpoint) | kein Code-Commit | nur diese SUMMARY |

## Task 1: der CI-Schritt

- Schritt "The result page answers in every new language (core lang)", nach "Log every account in
  and keep its session", vor "Queue and run the crawl". Kein neuer Job, kein zweiter Login, kein
  `${{ }}` im run-Block (2541 Zeichen).
- Je Code: Wert zu `Search your file contents` aus `apps/findling/l10n/<code>.json` per `php -r`
  lesen (leer oder gleich Schlüssel: `::error::`), `occ user:setting owner core lang <code>`,
  Ergebnisseite `index.php/apps/findling/` mit dem Cookie-Jar des Owners, HTTP 200, Anwesenheit des
  übersetzten Titels, Abwesenheit des englischen. Antwort bleibt als `language-probe-<code>.html`.
- Lokal geprüft: YAML-Parse mit den Planprüfungen, `bash -n` über den run-Block, Erwartungswerte
  der fünf Kataloge per Python gelesen (alle vorhanden, keiner gleich dem Schlüssel).
- **Erster echter Lauf folgt mit dem Push durch den Orchestrator; der Lauf-Beleg wird hier
  nachgetragen.** Lokal gibt es weder PHP noch den CI-Runner.

## Task 2: der Schlussabschnitt

Dateiliste (8 Codes, 16 Dateien, Verweis je Code), zehn Gates mit Zusicherung (Wortwahl
ausdrücklich ungeprüft), der CI-Beweis mit "was er beweist" und "was er nicht beweist", der
Vorbehalt E-17-5 Option a und die vier Grenzen (es_EC/es_MX, Rechtschreibreform, keine getrennten
Suchwortlaute, n gleich 0). Schlüsselzahl 202 nachgezählt und datiert.

## Task 3: die Sichtprobe (vom Owner abgenommen)

Chromium über Playwright an `findling-nextcloud` (NC 34.0.3, Port 8090), echte Anmeldung: `admin`
für die Adminseite, `testuser` für die Ergebnisseite ohne Begriff, mit Treffern (`Genehmigung`)
und ohne Treffer. Englische Reste gesucht als jedes englische Satzstück von mindestens 14 Zeichen
aus den Schlüsseln von `de.json` im sichtbaren Text, dazu die Screenshots angesehen.

| Code | Adminseite | Ergebnisseite leer / Treffer / kein Treffer | englische Reste | Pluralform bei n > 1 |
|---|---|---|---|---|
| es | 200, `lang=es` | 200 / 200 / 200 | 0 | "última comprobación hace 16 días", "24 horas" |
| it | 200, `lang=it` | 200 / 200 / 200 | 0 | "ultimo controllo 16 giorni fa", "Ultimi 7 giorni" |
| nl | 200, `lang=nl` | 200 / 200 / 200 | 0 | "16 dagen geleden", "Laatste 30 dagen", "24 uur" |
| pt_PT | 200, `lang=pt-PT` | 200 / 200 / 200 | 0 | "última verificação 16 dias atrás", "24 horas" |
| pt_BR | 200, `lang=pt-BR` | 200 / 200 / 200 | 0 | "16 dias atrás", "Últimos 30 dias" |

- **Gegenprobe `en`:** derselbe Lauf meldet 37 Funde auf der Adminseite und 1 bis 3 je
  Ergebnisseite. Die Suche nach Resten kann also finden; die Nullen oben sind eine Aussage.
- Keine weiße Seite, keine abgebrochene Seite; Trefferseiten zeigen echte Treffer mit Snippets.
- Englisch in der Einstellungs-Seitenleiste ("Personal" unter pt_PT, "Quick presets", "Support")
  kommt aus dem Kern und anderen Apps, nicht aus Findling, und ist kein Befund dieser Phase.
- **Ausgangswert:** vorher `admin=de`, `testuser=de`; nachher `admin=de`, `testuser=de`
  (Rücksetzung im `finally`, auch nach dem ersten abgebrochenen Lauf).
- **`git status --short`:** leer; `php/l10n/` führt weiter 16 Dateien.

## Abweichungen vom Plan

### 1. [Rule 3 - Blocker] `occ upgrade` an der Entwicklungsinstanz

- **Gefunden in:** Task 3
- **Problem:** `findling-nextcloud` stand auf Findling 1.1.0, das Repo seit 21.09. (734a1b2) auf
  1.2.0; die Instanz meldete "require upgrade" und hätte keine Seite gezeigt.
- **Fix:** `occ upgrade`, Findling danach 1.2.0 an der Instanz. Kein Repo-Eingriff.

### 2. [Rule 3 - Blocker] Backend auf dem Host neu gestartet

- **Gefunden in:** Task 3
- **Problem:** Ohne laufendes Backend keine Ergebnisseite mit Treffern.
- **Fix:** `FINDLING_PORT=8090 scripts/dev/register-exapp.sh`, Backend 1.2.0 neu registriert.
  Zustand liegt im gitignorten `.dev/`.

### 3. [Rule 2 - Ergänzung] Sprache auch für `admin` gesetzt

- Der Plan nennt `testuser`, die Adminseite sieht nur `admin`. Beide Ausgangswerte gelesen und
  wiederhergestellt.

## Gates

Suite 2880 passed / 15 skipped vor jedem Commit, ruff check, ruff format --check, pyright
(latest), vulture grün. Git-Blobs der zwei Dateien: 0 CR.
`git diff --name-only cfe96c7..HEAD -- php/templates php/js php/lib backend/src`: leer.

## Bedrohungen dieses Plans

| ID | Erledigt durch |
| --- | --- |
| T-20-40 (veralteter Erwartungswert) | Wert zur Laufzeit aus dem Katalog, leer oder gleich Schlüssel bricht ab |
| T-20-41 (Sprache bleibt stehen) | trap EXIT im CI-Schritt; `finally` in der Sichtprobe, Ausgangswert de belegt |
| T-20-42 (Seite zerbricht ungesehen) | Sichtprobe über Adminseite und drei Ergebnisseiten in fünf Sprachen |
| T-20-43 (Probedatei im Repo) | `git status --short` leer |
| T-20-44 (Artefakt mit Sitzung) | akzeptiert, Wegwerf-Instanz |

## Bekannte Stubs

Keine.

## Authentifizierungs-Tore

Keine.

## Self-Check: PASSED

`.github/workflows/integration.yml` und `docs/l10n-catalogues.md` liegen im Baum, die Commits
`1c80e26` und `530bb7c` stehen in der Historie.
