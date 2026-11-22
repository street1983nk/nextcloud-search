# Prüfbericht PR #56 und PR #57 (Plan 45-01)

Stand: 2026-11-22. Geprüft gegen origin/main `e3491b1d682fe7f46f0c846cd4da44e2e02045c2`.
Beide PRs basieren auf `cba2de8cf50765570b5d1691f195a26d2160b5b7` (16.11.2026). Seitdem kamen auf main
die Phase-44-Commits dazu, darunter zwei Änderungen an `.github/workflows/integration.yml`
(325fb97a, ec3b3743 vom 21.11.2026). Keine Datei unter `php/l10n/`, kein `php/js/admin.js` und keiner der
geänderten Tests wurde seit der Basis auf main angefasst.

Merge-Methode für beide PRs (D-45-11): `gh pr merge <n> --merge --match-head-commit <Kopf>`.
Merge-Commit, die PR-Commits behalten foolfitz als Autor; kein Squash, kein Rebase. Reihenfolge: erst
#57, dann #56 (beide konfliktfrei, auch nacheinander, siehe "Gemeinsamer Merge-Stand").

Keine GitHub-Aktion ausgelöst: kein Merge, kein Kommentar, keine Workflow-Freigabe. Die Fork-Workflows
sind bereits gelaufen (GitHub hat sie ohne weitere Freigabe gestartet), eine Frage `Freigabe CI-Lauf`
entfällt deshalb.

## PR #57

Titel: fix(admin): the admin page keeps working under a three part locale such as zh_Hant_TW
Kopf: 168b6b13ba7d03b407e94f9f57a17a2970657457
Autor: foolfitz
Commits: 1 (168b6b13, Autor foolfitz <foolfitz@gmail.com>, Trailer `Co-Authored-By: Claude Opus 5.5`)
Dateien: `php/js/admin.js` (+19/-2), `backend/tests/test_admin_locale.py` (neu, 183 Zeilen)
CI: grün (Läufe 44744831718, 44744831569, 44744831624, 44744831578, 44744831538; 23 Checks pass, 1 skipping "extraction start cost on arm64" wie üblich). Achtung: gelaufen am 2026-11-20 13:30 UTC gegen den damaligen main-Stand, also ohne die Phase-44-Workflow-Gates.
Lokale Gates: `cd backend && PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_admin_locale.py tests/test_admin_ui_contract.py` (Worktree auf dem Kopf) -> 209 passed; `ruff check` und `ruff format --check` auf test_admin_locale.py -> grün
Konfliktfrei: ja
Closing-Referenzen im PR-Text: keine (`closingIssuesReferences` leer), der Merge schließt kein Issue.

Inhalt: `locale()` ersetzt jetzt jeden Unterstrich von `data-locale` (`replace(/_/g, '-')`) und schickt
jeden Kandidaten (eigene Locale, dann `root.lang`) durch `Intl.getCanonicalLocales`; was Intl ablehnt,
fällt auf den nächsten Kandidaten und zuletzt auf `'en'`. Der Test schneidet die Funktion aus dem Skript,
lässt sie in node gegen alle 42 dreiteiligen Codes von NC 34, elf zweiteilige und kaputte Werte laufen,
mit zwei Positivkontrollen (alte Funktion wirft genau für die 42; Mutation auf `replace('_', '-')` fällt
still zurück und wird über die Gleichheit erkannt). Sauber, B8-konform.

Befunde:
- [niedrig] root.lang-Nit (D-45-11): Der Rückfall `root.lang` wird NICHT umgeschrieben. Ein
  `root.lang = 'zh_Hant_TW'` ohne `data-locale` wird von `getCanonicalLocales` abgelehnt und endet bei
  `'en'` statt `'zh-Hant-TW'`. Kein Absturz mehr, nur falsches Zahlenformat. In der Praxis setzt der
  Nextcloud-Layout `lang` mit Bindestrichen, deshalb nur Härtung. Nachtrag von uns (Task 3a).
- [Info] Der Commit trägt `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Mit einem
  Merge-Commit bleibt der Trailer in der Historie, GitHub zeigt den Co-Autor am Commit. Die Owner-Regel
  "keine Claude-Zeilen" gilt für eigene Commits; der Autor ist foolfitz, der PR-Text legt die Hilfe offen.
  Nur zur Kenntnis.
- [Info] CI lief vor den Phase-44-Gates. Der kombinierte Merge-Stand ist lokal geprüft (siehe unten);
  die Workflow-Gates (zizmor, actionlint) laufen laut T-45-02 in 45-06 vor dem Push.

Empfehlung: mergen mit Nachtrag
Nachtrag von uns:
- root.lang-Nit: auch `root.lang` jeden Unterstrich zu Bindestrich, Testfälle `root.lang = 'zh_Hant_TW'`
  ohne data-locale -> `zh-Hant-TW` und `data-locale = 'pt_BR'` -> `pt-BR`, mit Fehl-Sample (Task 3a)
- CHANGELOG (alle drei Sprachen), Punkt "Fixed" mit (#57) (Task 3c)

## PR #56

Titel: l10n: Traditional Chinese (Taiwan) catalogue zh_TW (#53)
Kopf: 51690b2ac926bbbb14df4e3f3b5c0fd40bc078d4
Autor: foolfitz
Commits: 3 (525f02de feat(l10n), 66717f00 docs(l10n), 51690b2a ci(integration)), alle Autor foolfitz <foolfitz@gmail.com>, jeweils Trailer `Co-Authored-By: Claude Opus 5.5`
Dateien: `.github/workflows/integration.yml` (+3/-2), `backend/tests/test_admin_ui_contract.py` (+73/-14), `backend/tests/test_phase34_audit.py` (+2/-1), `backend/tests/test_unified_search_plugin.py` (+2/-2), `docs/l10n-catalogues.md` (+62/-2), `docs/l10n-chinese.md` (neu, 636), `php/l10n/zh_TW.js` (neu, 371), `php/l10n/zh_TW.json` (neu, 371)
CI: grün (Läufe 44744825491, 44744825758, 44744825518, 44744825462, 44744825656; 23 Checks pass, 1 skipping "extraction start cost on arm64"). Gelaufen am 2026-11-20 13:30 UTC gegen den damaligen main-Stand, ohne die Phase-44-Workflow-Gates.
Lokale Gates: `cd backend && PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_admin_ui_contract.py tests/test_phase34_audit.py tests/test_unified_search_plugin.py` (Worktree auf dem Kopf) -> 273 passed, 12 skipped (nur Live-Audit-Instanz, Netzprobe, Mutationslauf, wie auf main); `ruff check .` und `ruff format --check .` -> grün
Konfliktfrei: ja
Closing-Referenzen im PR-Text: keine, #53 bleibt offen (gewollt: der PR ist "first step of #53").

Katalogprüfung (eigenes Skript `check_zh.py` im Scratchpad, mit Positivkontrolle: ein in de.json
gepflanzter Schlüssel wird als fehlend gemeldet):
- Schlüssel zh_TW.json 366, zh_TW.js 366, de.json auf origin/main 366; JSON-Hälfte und JS-Hälfte identisch, Reihenfolge wie de.json
- Fehlende zh_TW-Schlüssel gegen origin/main: keine (seit der PR-Basis kam auf main kein neuer Schlüssel dazu)
- Überzählige Schlüssel: keine
- Pluralkopf in beiden Hälften `nplurals=1; plural=0;`, die fünf Pluralschlüssel tragen je eine Form
- Platzhalter-Parität: keine Abweichung
- U+2013/U+2014 in zh_TW.json und zh_TW.js: keine
- Markup oder `javascript:` in Werten: keines (T-45-03)

Workflow-Änderung (T-45-02): nur ein Kommentarsatz und `zh_TW` in der Schleife
`for code in es it nl pt_PT pt_BR zh_TW` des Schritts "The result page answers in every new language
(core lang)". Keine neuen Actions, keine Rechte, keine Secrets, kein neuer Trigger. Unbedenklich.

Befunde:
- [Owner-Frage] Der PR-Text fragt, ob `docs/l10n-chinese.md` auf Englisch bleiben darf (die fünf anderen
  Sprachdokumente sind deutsch). foolfitz liest kein Deutsch gut genug, um deutsche Prosa zu verantworten.
  Vorschlag: Englisch lassen. Antwort erst nach dem Store-Release (D-45-16), Entwurf unten.
- [niedrig] `docs/l10n-chinese.md` nennt im Abschnitt zur Typografie das chinesische Doppel-Geviertstrich
  (zwei U+2014 in Eckklammern) als Beispiel dafür, was NICHT verwendet wird. Einziges U+2014 im PR, steht in einer
  Regelbeschreibung, nicht in einem Katalogwert. Lassen.
- [Info] Neue Schlüssel späterer Pläne der Phase 45 müssen nun in 17 Katalogen plus einer Tabellenzeile
  in `docs/l10n-chinese.md` landen (Gate `LANGUAGE_TABLES`), sonst wird test_admin_ui_contract.py rot.
- [Info] Co-Authored-By-Trailer wie bei #57, PR-Text legt die Hilfe offen ("Drafted with the assistance
  of Claude").
- [Info] Der PR-Text schlägt für PRODUCT.md vor: "Oberfläche in neun Sprachen: EN, DE, FR, ES, IT, NL,
  pt_PT, pt_BR, zh_TW". Übernehmen wir in Task 3c.

Empfehlung: mergen mit Nachtrag
Nachtrag von uns:
- Fehlende zh_TW-Schlüssel: keine (Task 3b entfällt, solange main keinen neuen Schlüssel bekommt)
- PRODUCT.md: Sprachliste um zh_TW (Task 3c)
- CHANGELOG (alle drei Sprachen), Punkt "Added" mit (#56) (Task 3c)

## Gemeinsamer Merge-Stand

`git merge-tree --write-tree origin/main pr-57` -> Baum e8f74320, rc 0; `... origin/main pr-56` -> Baum
00f2be0a, rc 0. Zusätzlich in einem Wegwerf-Worktree origin/main + #57 + #56 nacheinander mit `--no-ff`
gemergt, ohne Konflikt, und dort die volle Backend-Suite gelaufen:
`cd backend && PYTHONUTF8=1 uv run --no-sync python -m pytest -q -p no:cacheprovider` -> 7252 passed,
303 skipped, 0 failed (13:16 min). Dazu auf demselben Stand
`PYRIGHT_PYTHON_FORCE_VERSION=latest uv run --no-sync pyright` -> 0 errors, `uv run --no-sync vulture` -> rc 0,
`ruff check .` und `ruff format --check .` -> grün. Die PHP- und Workflow-Gates (Docker) laufen nicht hier,
sondern nach dem Merge in 45-06 vor dem Push (T-45-02, B4).

Alle Wegwerf-Worktrees sind danach entfernt.

## Antwortentwürfe (Englisch, erst nach dem Store-Release posten, D-45-16, Owner postet)

#57:

> Thanks a lot, merged. Great catch, and the test with the old function as control is exactly how we
> like it. I added one small follow-up on top: the fallback to the page language now gets the same
> underscore treatment. It ships in Findling 1.7.0.

#56:

> Thank you, merged and shipped in Findling 1.7.0. Keeping docs/l10n-chinese.md in English is fine,
> no translation needed. The new strings of 1.7.0 got a first Traditional Chinese version from us,
> I'll ask you in #53 to look them over.
