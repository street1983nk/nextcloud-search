# Phase 46: Findling 1.7.1 - Context

**Gathered:** 2026-11-27
**Status:** Ready for planning (Entscheide E-46-01 bis E-46-08 vom Planer vorbelegt, Owner bestätigt sie vor der Ausführung, siehe unten)
**Source:** Auftrag des Owners über den Koordinator (27.11.2026), kein discuss-phase; Befunde aus Phase 45 vom Planer am Code nachgeprüft (Stand origin/main 09ca4d2377d21e4e74565d0c613162e9f7ad5095, lokal gleich, `git fetch` am 27.11.2026)

<domain>
## Phase Boundary

Findling 1.7.1 (findling und findling_backend in gleicher Version) im Store, als Patch-Release ohne Migration und ohne Schemawechsel, Upgrade ab 1.7.0. Inhalt sind genau die fünf Befunde aus Phase 45 (Tabelle unten) plus der Release-Ablauf wie 45-08 bis 45-16, 45-14 und 45-15. Neue Funktionen gehören nicht in diese Phase.

</domain>

## Befunde und Nachprüfung am Code

| Befund | Quelle | Anforderung | Nachprüfung am Code (27.11.2026, Kopf 09ca4d23) |
|---|---|---|---|
| I-45-10-04 | 45-VOLLTEST.md Befundtabelle | EXCL-07 | bestätigt: `php/templates/admin.php` Z. 1586 Hilfesatz mit msgid `... Example: Backups`, Z. 1612 Platzhalter `$l->t('Backups')`. In allen neun Sprachen endet der Katalogwert des Hilfesatzes auf das englische "Backups", der Platzhalter ist übersetzt: de/de_DE "Sicherungen", fr "Sauvegardes", es "Copias de seguridad", it "Backup", nl "Back-ups", pt_BR "Backup", pt_PT "Cópias de segurança", zh_TW "備份". Der Befund betrifft also nicht nur DE und FR, sondern alle neun Sprachen (18 Dateien .json und .js). Der Test `backend/tests/test_admin_ui_contract.py` Z. 5172 pinnt nur die msgid (FOLDER_HELP), nicht den Wert. Sprachtabellen in docs/l10n-chinese.md, -dutch.md, -french.md, -italian.md, -portuguese.md, -spanish.md führen den Satz (je Z. ~315 bis ~476) |
| I-45-10-06 | 45-VOLLTEST.md, gemeinsame Abnahme Schritt 2 | EXCL-08 | bestätigt: `php/js/admin.js` `setupExclusionList()` (Z. ~1445) und `setupPatternList()` (Z. ~1516) hängen nur `click` an `#findling-rules-add` bzw. `#findling-rules-patterns-add`; kein `keydown` an `#findling-rules-new` oder `#findling-rules-patterns-new`; die Felder stehen in keinem `<form>` (einziges Formular der Seite: `#findling-diagnosis-form`, admin.php Z. 999), also löst Enter auch keinen Submit aus. Einziger keydown in admin.js: Escape der Bestätigung (Z. ~2010) |
| I-45-10-08 | 45-VOLLTEST.md | ADM-05 | bestätigt: `php/css/admin.css` Z. 290 bis 312: `hyphens: auto` und `overflow-wrap: anywhere` an allen Zellen, halbe Zellpolster erst unter 512 px; keine Regel unter 360 px. Zustandsspalte `.findling-errors__state` mit `width: 1%` und `white-space: nowrap` (Z. 337 bis 341), der Chip bleibt ganz, also nimmt er dem Zeilenkopf bei 320 px die Breite. Template admin.php Z. 864 bis 899: Tabelle mit drei Spalten Grund, Dateien, Zustand |
| I-45-10-07 (45-AUDIT.md) | 45-AUDIT.md Nachtrag nach "Freigabe Push 45-10 Fix" (Z. ~2611) und Ergebnis der Nachprüfung (Z. ~2729), 45-SECURITY.md Z. 164 | PRUEF-05 | bestätigt: `.github/actions/setup-test-nc/action.yml` Z. 392 bis 399, Schritt "Install the German dictionary the analyzer reads": `sudo apt-get update -qq` und `sudo apt-get install -y -qq wngerman` ohne `timeout`, ohne `Acquire::Retries`, ohne Schleife. Composite-Action-Schritte kennen kein `timeout-minutes` (vor dem Bau gegen die aktuelle GitHub-Doku prüfen); das Zeitlimit gehört deshalb in die Shell. Dieselbe Art Aufruf ohne Zeitlimit steht auch in integration.yml Z. 644, 1357, 2454 (tesseract), coverage-e2e.yml Z. 182, deploy-harp.yml Z. 2429 (sqlite3), php.yml Z. 166 und release.yml Z. 145 (xsltproc), python.yml Z. 227 (shellcheck), siehe E-46-04 |
| I-45-12-01 | 45-ABNAHME.md Z. 20, 45-12-SUMMARY.md, 45-AUDIT.md Z. ~2729 | PRUEF-06 | bestätigt und Ursache belegt: deploy-harp.yml "Store upgrade 2b" (Schritt ab Z. 3935), Teil 5 (Z. ~4530 bis 4566) wartet nur, bis state.db `indexed/` meldet, und prüft dann sofort `left=$(q "SELECT COUNT(*) FROM oc_findling_queue WHERE file_id = ...")` gleich 0. Log des roten Versuchs 1 von Lauf 45885132945 (Job `deploy-harp (stable34, 8.2, false, ubuntu-24.04)`, einmal gelesen): `pass finished, claimed=1 indexed=1 ... requeued=1 embedded=0 committed=1`, danach die Fehlzeile `short=1 accepted=1 stayed-short-twice=0 and 1 queue row(s)`. Laut `git show v1.5.0:backend/src/findling/worker/poller.py` Z. ~1185 bis 1206 übergibt der Pass ein indexiertes Dokument per `hand_over(..., kind=KIND_EMBED)` an die Embed-Spur; die Zeile bleibt bis zum Embed-Lauf stehen. Die drei Logzeilen stimmten (1:1:0), nur die Queue war noch nicht leer. Randbedingung: deploy-harp.yml hat 507 734 Byte, der Gate `backend/tests/test_workflow_size.py` erlaubt unter 512 000; der Fix darf also höchstens rund 4 KB dazulegen oder muss Teile nach scripts/ci/ verschieben (Muster MOVED_STEPS) |

### Klarstellung der doppelt vergebenen ID I-45-10-07

In 45-AUDIT.md ist I-45-10-07 der CI-Punkt (Wörterbuch-Download ohne Zeitlimit, LOW). In 45-VOLLTEST.md (Befundtabelle) ist I-45-10-07 das grau gefüllte gesperrte Kästchen bei ausgeschaltetem Hauptschalter, eine Darstellung von Nextcloud und kein Befund von Findling. Nur der CI-Punkt gehört in 1.7.1. In allen Dokumenten der Phase 46 heißt er "I-45-10-07 (45-AUDIT.md)"; die Dokumente der Phase 45 bleiben unverändert (archivierter Stand).

<decisions>
## Implementation Decisions

### Hilfesatz (EXCL-07)
- D-46-01: Die msgid bleibt unverändert (`... Example: Backups`, also kein neuer Schlüssel, FOLDER_HELP im Test bleibt); nur die Katalogwerte ändern sich: in jedem Katalog endet der Hilfesatz auf genau den Wert, den derselbe Katalog für `Backups` führt, mit der Typografie der Sprache (FR "Exemple : Sauvegardes", zh_TW "範例：備份"). Englisch ist schon stimmig. 18 Dateien (je Sprache .json und .js, de_DE gleich de).
- D-46-02: Ein neuer Gate in backend/tests/test_admin_ui_contract.py prüft je Katalogdatei, dass der Wert des Hilfesatzes mit dem Wert von `Backups` endet; Positivkontrolle: ein Katalog mit dem alten Wert ("Beispiel: Backups" neben "Sicherungen") macht den Gate rot.
- D-46-03: Die Sprachtabellen in docs/l10n-*.md und der Absatz "Platzhalter der Regelfelder" in docs/admin-page.md (Z. ~800) ziehen mit; wo ein Gate die Tabellen mit den Katalogen vergleicht, bleibt er grün.

### Enter in den Listen (EXCL-08)
- D-46-04: Je Feld ein `keydown`-Handler: bei `event.key === 'Enter'` und weder `event.isComposing` noch `event.keyCode === 229` (Eingabemethode, etwa Zhuyin für zh_TW) wird `preventDefault()` gerufen und derselbe Weg wie beim Knopf genommen (eine gemeinsame Funktion je Liste, kein doppelter Prüfcode, kein synthetischer Klick, wenn eine Funktion sauberer ist). Shift, Strg, Alt oder Meta mit Enter tun nichts.
- D-46-05: Nach dem Hinzufügen bleibt der Fokus im Feld (wie heute beim Knopf), bei einer Ablehnung steht die Meldung wie beim Knopf und der Text bleibt im Feld.
- D-46-06: Gate: statischer Vertragstest in test_admin_ui_contract.py (beide Felder haben einen keydown-Handler mit Enter-Prüfung und IME-Schutz, beide Wege rufen dieselbe Funktion wie der Knopf) mit Positivkontrolle (Fassung ohne isComposing rot); dazu Verhalten im Browser im Volltest (Enter fügt hinzu, Enter bei leerem Feld zeigt "empty", Enter bei laufender Komposition fügt nichts hinzu).

### Fehlerliste bei 320 px (ADM-05)
- D-46-07: Ziel: bei 320 px kein Wort im Zeilenkopf und in den Köpfen mitten im Wort getrennt (Trennung an einer Silbe mit Bindestrich durch `hyphens: auto` gilt als zulässig, ein Bruch durch `overflow-wrap: anywhere` nicht), keine waagerechte Scrollleiste; 375 und 1280 wie in 1.7.0 abgenommen (Bilder `abn/22-v07-*` aus 45 als Vergleich).
- D-46-08: Layout nach dem Vorschlag aus 45-VOLLTEST.md: unter 360 px steht der Chip unter dem Grund. Zwei Varianten werden als Playwright-Bilder gebaut, der Owner wählt (E-46-03): Variante A: unter 360 px sind Kopf und Zellen der Zustandsspalte `display: none`, eine zweite Fassung des Chips im Zeilenkopf ist nur unter 360 px sichtbar (zu jeder Breite steht genau eine Fassung im Accessibility-Baum). Variante B: Zustand und Anzahl rücken unter 360 px per Template in eine zweite Zeile unter dem Grund (ohne `display: block` an Tabellenzellen, damit die Tabellensemantik bleibt). Kein `display: block`/`grid` an `table`, `tr`, `th`, `td`.
- D-46-09: Gate in test_admin_ui_contract.py für die gewählte Variante mit Positivkontrolle (ohne die neue Medienregel rot), dazu die Browsermessung je Sprache bei 320 px: für jeden Textknoten in `.findling-errors th` und `.findling-errors td` liegt jeder Zeilenumbruch an einem Leerzeichen, Bindestrich oder weichen Trennstrich (Messung über `Range.getClientRects()` je Zeichen, Methode im Volltest-Bericht beschrieben), Gegenprobe mit dem Stand 1.7.0 rot.

### CI-Robustheit (PRUEF-05, PRUEF-06)
- D-46-10: Der Wörterbuch-Schritt bekommt ein Zeitlimit in der Shell (`timeout`), apt-Optionen `-o Acquire::Retries=3` und kurze `Acquire::http::Timeout`/`Acquire::https::Timeout`, und höchstens drei Versuche mit kurzer Pause; schlägt der letzte fehl, endet der Schritt rot mit einer klaren `::error::`-Zeile. Budget: ein Zeitlimit je Versuch für `apt-get update` und `install` zusammen (Standard 120 s), also höchstens rund 6,5 Minuten für drei Versuche samt Pausen; das muss deutlich unter dem kleinsten `timeout-minutes` aller Jobs liegen, die den Schritt ausführen (am 27.11.: 20 bis 25 Minuten, etwa integration.yml Z. 4783, resilience.yml Z. 1224), sonst wäre der Befund nicht behoben (Planprüfung B-3). `apt-get update` fällt genauso unter die Regel wie `install`. Umfang je E-46-04. Ein gemeinsames Skript scripts/ci/apt_install.sh (Bash, `set -euo pipefail`, shellcheck-sauber) trägt die Logik, die Schritte rufen es.
- D-46-11: Gate in backend/tests (neue Datei test_ci_apt_timeouts.py oder Erweiterung eines vorhandenen Workflow-Tests): jeder `apt-get install` im gewählten Umfang läuft über das Skript bzw. trägt Zeitlimit und Wiederholung; Positivkontrolle: die Fassung aus v1.7.0 von action.yml ist rot. Selbsttest des Skripts mit einem Kommando, das hängt (`sleep`), und einem, das zweimal fehlschlägt und dann gelingt, ohne Netz und ohne Docker.
- D-46-12: "Store upgrade 2b" Teil 5: nach `indexed/` wartet der Schritt innerhalb des restlichen Budgets `UPGRADE_DRAIN_BUDGET_SECONDS`, bis `oc_findling_queue` für die Datei leer ist (je Runde eine Logzeile mit Zeilenzahl und Art `kind`, ohne Pfad), erst dann zählt er die drei Logzeilen und prüft `1:1:0` und `left=0` wie bisher. Bleibt die Zeile bis zum Budgetende, ist der Schritt rot wie bisher. Andere Stellen in deploy-harp.yml, die direkt nach einem Urteil die Queue prüfen, werden im selben Plan gesucht und im Bericht aufgezählt; nur echte gleiche Rennen werden mitbehoben (sonst Befund mit Empfehlung).
- D-46-13: Gate in backend/tests/test_upgrade_seed_steps.py (oder test_workflow_*.py): im Schritt "Store upgrade 2b" steht vor der Prüfung `short:accepted:stuck` eine Warteschleife auf die leere Queue mit Budget; Positivkontrolle: der Text des Schritts aus v1.7.0 ist rot. test_workflow_size.py bleibt grün.

### Release 1.7.1 (REL-08)
- D-46-14: Version 1.7.1 an allen Lockstep-Stellen (php/appinfo/info.xml, backend/appinfo/info.xml version und image-tag, Links blob/v1.7.0 auf blob/v1.7.1, Kommentar "the tree carries" in deploy-harp.yml), FROM_TAGS um v1.7.0 ergänzt (Gate test_update_in_process_proof.py verlangt die Vorversion als letzten Eintrag), keine Migration (STOPP-Prüfung: `git diff --stat v1.7.0..HEAD -- php/lib/Migration` und die Schemadateien leer). Version und CHANGELOG je mit eigener Owner-Freigabe.
- D-46-15: CHANGELOG `## [1.7.1] - <Datum>` in EN, DE, FR inhaltsgleich (test_changelog_translations.py), nur `### Fixed` mit den drei sichtbaren Punkten (E-46-05), ohne closes/fixes/resolves, ohne Issue-Nummern (keiner der Befunde kam aus einem Issue), Link `[1.7.1]: .../compare/v1.7.0...v1.7.1`.
- D-46-16: README-Faktencheck DE/EN/FR vor dem Release (Owner-Regel 12.11.): jede Aussage zu Ausschlussfeldern, Fehlerliste, Sprachen, Versionen gegen den Kandidaten; Lücken nachziehen, Bericht in 46-README-PRUEFUNG.md.
- D-46-17: Volltest DE/EN/FR mit Playwright in drei Breiten (1280, 375, 320 px) hell und dunkel, Umlaut-Audit aller geänderten sichtbaren Texte, impeccable auf den geänderten Teilen, gemeinsame Owner-Abnahme per Playwright; Bericht 46-VOLLTEST.md.
- D-46-18: secure-phase 46 VOR dem Tag (Owner-Regel 15.11.), threats_open 0; die Release-Threats (Tag, Store, Kommentare) im Nachtrag nach dem Release wie 45-15.
- D-46-19: Release-Ablauf wie 45-12 bis 45-15, mit der Lehre aus 45-ABNAHME.md Z. 5: Die CI läuft nur auf gepushten Köpfen, und der gepushte Kopf ist meist ein Freigabe-Commit in .planning. Deshalb gibt es nach jedem Push eine Zeile `ci_head: <git rev-parse origin/main direkt nach dem Push>`; `head_green.sh` läuft nur auf ci_head; `audited_head` bleibt der letzte Commit außerhalb .planning und es gilt `git diff --quiet <audited_head> <ci_head> -- . ':!.planning'`. Der Tag-Kopf ist der ci_head des letzten Pushes vor dem Tag (der CI-geprüfte Kopf selbst). Ein Kopf, der nur CHANGELOG-Zeilen ändert, löst wegen der paths-Filter nur "Security scans" aus; dafür gilt die Sonderregel in 46-08. Signatur-Probe vor dem Tag; Tag und Store je eigene Freigabe; Store-API höchstens alle 10 Minuten.

### Claude's Discretion
- Namen der neuen Tests und der Hilfsfunktion in admin.js, solange Code und Kommentare Englisch sind.
- Ob der Gate für PRUEF-05 eine neue Datei oder eine Erweiterung ist.

</decisions>

## Entscheide, die der Owner vor der Ausführung bestätigt

Vom Planer vorbelegt (Empfehlung zuerst). Ohne Bestätigung startet 46-01 nicht; die Antwort steht als Zeile `Entscheid <Name> 46-00: <Zitat> (<JJJJ-MM-TT HH:MM>, <Kanal>) Entscheid: <Wert>` in 46-FREIGABEN.md.

- E-46-01 Richtung der Angleichung (EXCL-07): (a, Empfehlung) der Hilfesatz übernimmt das übersetzte Beispiel des Platzhalters ("Beispiel: Sicherungen"); (b) beides "Backups" (nimmt die Übersetzung des Platzhalters aus 45-25 zurück). Hinweis: 45-UI-SPEC ließ den Hilfesatz bewusst unverändert; der Auftrag zu 1.7.1 hebt das auf.
- E-46-02 Umfang EXCL-07 (Planer-Befund): (a, Empfehlung) alle neun Sprachen, weil der Widerspruch in allen besteht; (b) nur DE und FR wie im Befundtext.
- E-46-03 Layout bei 320 px (ADM-05), Wert ja|nein: bestätigt der Owner, dass unter 360 px der Chip unter den Grund rückt (Vorschlag aus 45)? Die Wahl zwischen Variante A und B fällt erst im Checkpoint von 46-03 anhand der Bilder.
- E-46-04 Umfang PRUEF-05: (a, Empfehlung) Wörterbuch-Schritt plus die tesseract-Installationen in integration.yml und coverage-e2e.yml über scripts/ci/apt_install.sh (dieselben Testjobs, dasselbe Risiko); release.yml, php.yml, python.yml und deploy-harp.yml bleiben unverändert (Backlog); (b) nur der Wörterbuch-Schritt; (c) alle apt-get-Aufrufe aller Workflows. Hinweis: coverage-e2e.yml startet nur per workflow_dispatch; seine Umstellung belegt in echter CI nur ein eigener Dispatch mit `Freigabe Dispatch coverage-e2e 46-06` (Empfehlung: ein Lauf), sonst nur der statische Gate.
- E-46-05 CHANGELOG (D-46-15): (a, Empfehlung) nur die drei sichtbaren Fixes; (b) zusätzlich ein Satz zu den CI-Punkten.
- E-46-06 Store-Texte: (a, Empfehlung) unverändert bis auf die Links blob/v1.7.0 auf blob/v1.7.1; (b) Owner will Textänderung (dann eigener Entwurf vor dem Einbau).
- E-46-07 Kommentare nach dem Release: (a, Empfehlung) keine, weil kein Befund aus einem Issue kommt; (b) Owner nennt Threads, dann je Thread Entwurf und eigene Freigabe wie 45-15.
- E-46-08 Docker-Fenster, Wert ja|nein: Volltest (46-07), Varianten-Bilder (46-03), PHPUnit und PHP-Gates (B3) brauchen Docker. Gilt die Regel "Docker nur, wenn keine andere Docker-Arbeit läuft (`docker ps -q` leer) und der Owner das einzelne Fenster mit einer Zeile `Freigabe Docker-Fenster 46-NN: ... Entscheid: ja` freigegeben hat", weil der Connector-Agent parallel arbeitet? Bis dahin laufen nur Schritte ohne Docker.

## Bindende Vorgaben 46 (gelten für JEDEN Plan der Phase 46; andere Pläne verweisen hierher)

- B1 Commits nur so: `git -c user.name=street1983nk -c user.email=k.cherif@outlook.de commit -m "<typ>(46-NN): <englischer Satz>" -- <explizite Pfade>`. Nie `gsd-sdk query commit`, nie phases.clear, keine Zeile "Claude-Session", kein Co-Authored-By, nie closes/fixes/resolves vor einer Issue-Nummer (auch nicht in CHANGELOG, Commit-Text oder PR-Text).
- B2 Jeder Push, Merge, Kommentar, Tag, Workflow-Dispatch, Release-Edit, jede Signatur-Probe und jede Store-Aktion nur mit einer Zeile in `.planning/phases/46-findling-1-7-1/46-FREIGABEN.md` im Format `Freigabe <Gegenstand> 46-NN: <Owner-Zitat> (<JJJJ-MM-TT HH:MM>, <Kanal>) Entscheid: ja|nein`. Eine Freigabe deckt genau ihren Gegenstand und verbraucht sich. Fehlt sie: Stopp. Owner-"Hi" auf eine offene Ja/Nein-Frage gilt als "Go" (Owner-Regel 22.11.), wird aber wörtlich zitiert.
- B3 Lokal grün vor jedem Commit: Python in `backend/` mit `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run --no-sync pyright`, `uv run --no-sync vulture`, dazu `PYTHONUTF8=1 uv run --no-sync python -m pytest -q <betroffene Tests>`; bei PHP-, Template-, JS- oder Workflow-Änderung zusätzlich `bash scripts/dev/phpunit_docker.sh` und `bash scripts/dev/php_gates_docker.sh all` (bzw. `workflows`), aber nur im Docker-Fenster nach E-46-08; außerhalb davon bleibt der Commit lokal und der Docker-Teil wird vor dem ersten Push nachgeholt (Vermerk in der SUMMARY). Ausnahme: ein TDD-RED-Commit `test(46-NN): ...` darf mit genau dem neuen, absichtlich roten Test committet werden (alle übrigen Gates grün, der rote Lauf steht wörtlich in der SUMMARY); der GREEN-Commit folgt im selben Plan, und kein Push enthält einen RED-Commit ohne seinen GREEN-Commit. Nie `python -c` und nie `python -`; Hilfsskripte als Datei im Scratchpad.
- B4 Docker nie parallel zu anderer Docker-Arbeit; höchstens ein Executor; höchstens ein CI-Warter, kein paralleles `gh run watch`; GitHub-API sparsam.
- B5 Texte: kein U+2013, kein U+2014, keine Emojis. Echte Umlaute nur in deutscher Prosa, nie in Code, Bezeichnern, URLs, YAML. Code und Code-Kommentare Englisch.
- B6 Logzeilen tragen nur Zähler und Codes, nie Pfade, Mountpunkte oder ID-Listen (T-04-51); die neue Wartezeile in "Store upgrade 2b" nennt Zeilenzahl, Art und Restbudget.
- B7 Kein Kommentar auf GitHub ohne E-46-07 (b) und eigene Freigabe je Thread; nie vor dem Store-Release.
- B8 Gegenprobe nie mit dem Muster der Umsetzung; jeder neue Gate bekommt eine Positivkontrolle (Fehl-Sample, das ihn rot macht), am besten der Stand aus v1.7.0.
- B9 App-Store-API höchstens alle 10 Minuten abfragen.
- B10 Sorgfalt vor Tempo; kein Schritt unter Zeitdruck; LOW-Befunde sauber beheben statt aus Bequemlichkeit akzeptieren (Owner-Regel 20.11./22.11.).
- B11 Vor jedem Push `git fetch origin` und `git rev-list HEAD..origin/main`; nicht leer: Stopp und Owner-Frage (Rebase nur mit Zeile `Entscheid Rebase 46-NN`).

<canonical_refs>
## Canonical References

- .planning/phases/45-findling-1-7-0/45-VOLLTEST.md (Befundtabelle, Methoden des Volltests, Bilder abn/22-v07-*)
- .planning/phases/45-findling-1-7-0/45-AUDIT.md (Nachtrag 45-10 Fix, Ergebnis der Nachprüfung)
- .planning/phases/45-findling-1-7-0/45-ABNAHME.md (Rerun HaRP deploy 45885132945)
- .planning/phases/45-findling-1-7-0/45-UI-SPEC.md (Regelblock, Fehlerliste)
- .planning/phases/45-findling-1-7-0/45-08-PLAN.md bis 45-16-PLAN.md (Muster Version, Audit, Volltest, Tag-Kopf, Signatur, secure-phase, Tag und Store, Abschluss)
- php/templates/admin.php, php/js/admin.js, php/css/admin.css, php/l10n/*.json und *.js
- .github/actions/setup-test-nc/action.yml, .github/workflows/deploy-harp.yml, integration.yml, coverage-e2e.yml
- backend/tests/test_admin_ui_contract.py, test_upgrade_seed_steps.py, test_workflow_size.py, test_update_in_process_proof.py, test_lockstep_versions.py, test_changelog_translations.py
</canonical_refs>

<deferred>
## Deferred Ideas

- apt-Aufrufe außerhalb des Umfangs von E-46-04 (Backlog)
- Umbenennung der doppelten ID in den Dokumenten der Phase 45: nicht, archivierter Stand
- body_zh (#53, PR #60), Dedup Weg B: nächste Milestones
</deferred>

---

*Phase: 46-findling-1-7-1*
*Context gathered: 2026-11-27*

## Planprüfung (27.11.2026)

gsd-plan-checker über 46-01 bis 46-12: 3 BLOCKER, 11 WARNING, 5 INFO, alle eingearbeitet. BLOCKER: B-1 Tag-Kopf und audited_head lagen nicht auf einem gepushten Kopf mit CI (jetzt Zeile ci_head, D-46-19); B-2 eine reine Datumszeile löst die sieben Workflows nicht aus (jetzt Fall 1 und Fall 2 in 46-08 mit Dispatch "Python gates" nach Freigabe); B-3 das Zeitlimit von apt_install.sh hätte das Job-Limit gesprengt (jetzt ein Budget je Versuch, Gate gegen das kleinste timeout-minutes). WARNING unter anderem: apt-get update im Gate, coverage-e2e nur per Dispatch, "Workflow security lint" in head_green, doppelte id der Live-Anzahl bei Variante B, Abbruchkriterium und Variante C in 46-03, RED-Commits als Ausnahme in B3, Werte der Entscheide, Docker-Fenster je Zeile, zh_TW-Proben mit CDP und Positivkontrolle, headSha der Signatur-Probe, schärfere verify-Befehle in 46-06, 46-10, 46-11, 46-12.
