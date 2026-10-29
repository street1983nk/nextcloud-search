# 40-03-SUMMARY: Upgrade-Strecke startet ab v1.5.0, die 1.6-Änderungen überleben das Upgrade

Plan 40-03, REL-06, ROADMAP Phase 40 Erfolgskriterium 2. Beide Tasks ausgeführt;
jede Ableitung je Zusicherung steht in 40-03-ABLEITUNG.md.

## Was gebaut wurde

- `UPGRADE_FROM_TAG: v1.5.0` mit neuem Begründungsabsatz oben im Block; die Absätze
  v1.4.3, v1.4.2, v1.3.2 und älter stehen unverändert darunter (Commit c08d4daa).
- Jede startversionsabhängige Zusicherung der Schritte Store upgrade 0 bis 7 aus dem
  Code von v1.5.0 (6c953a76) neu abgeleitet, keine abgeschwächt, zwei verschärft
  (Vektorbestand: der GANZE Bestand wird eingefroren und verglichen; neue Guard
  schemaVersion==3 vor dem Upgrade). Inventar der 147 Fundstellen, Guard-Tabelle
  (kein Schritt kleiner, Ersatzzeilen benannt) und Leitfragen (a) bis (f) in der
  ABLEITUNG.
- Neue Zusicherung 12 "die 1.6-Änderungen überleben das Upgrade" (Commit 0bdd6b71):
  die vier lesenden Teile am Ende von Store upgrade 5 (jetzt "the eleven assurances
  after the upgrade"), der schreibende Teil 2 in Store upgrade 5b hinter dessen
  Regelschreibung.
- Vertragstests: test_upgrade_seed_steps.py auf v1.5.0 umgestellt (RED-Commit
  b84a489f, 12 Tests gezielt rot vor dem Umbau), test_phase40_audit.py um die
  Zusicherung-12-Sektion erweitert (RED-Commit 9e199d3d, 7 Tests gezielt rot).

## Entscheidungen und Abweichungen

- **Teil 2 über POST /admin/rules statt occ** (vom Koordinator genehmigt):
  rules_changed_at wird allein von der Route gestempelt (SettingsController.php:466
  ruft rememberRulesChange nach wirklich geändertem Satz); occ config:app:set ist der
  dokumentierte zweite Weg, der die Route nie passiert (SettingsService.php:316). Ein
  occ-Weg könnte den Hinweis nur per Hand-Stempel fälschen. Der POST läuft mit
  App-Passwort und OCS-APIRequest-Header (derselbe Weg wie overview.sh), setzt den
  Satz in Kraft plus einen Präfix eines nicht existierenden Ordners und nimmt ihn mit
  einem zweiten POST zurück; Schritte 5b/6/7 gelten unverändert (kein späterer
  Schritt liest coverage.rulesPending, der Sweep eines Präfixes ohne Dateien räumt
  nichts, die Liste liest danach wieder UPGRADE_EXCLUSIONS_BEFORE).
- **Teil 2 liegt in 5b, nicht in 5** (die im Plan vorgesehene Ausweiche): Store
  upgrade 5 tut nichts, was ein Admin tun würde (SC4,
  test_the_assurance_step_does_nothing_an_admin_would_do), und eine Regel zu setzen
  ist genau das.
- **Schrittname**: Store upgrade 5 heißt "the eleven assurances after the upgrade"
  (1 bis 10 plus 12; 11 ist 5b). Dadurch wurde test_cert_rotation_steps.py
  (COUNTER_SAMPLE und Stub) mit angepasst, obwohl die Datei nicht in files_modified
  stand; die Alternative wäre ein Schrittname gewesen, der zählt, was nicht da ist.
- **Keine Abschwächung beim Startwechsel**: wo die Saat unter 1.5.0 nichts mehr
  beweist (Nachholung der neuen Formate, Give-up der Stale-Datei), trat die gleich
  scharfe Zusicherung an ihre Stelle, dass 1.6.0 die Urteile von 1.5.0 unverändert
  übernimmt; die Stale-Datei wird exakt über die POL-02-Logzeilen gehalten
  (`short:accepted:stuck != 1:1:0`).
- **Task-2-Push vor der lokalen Vollsuite**: der RAM der Box war durch eine parallele
  Session unter 1,2 GB frei und der Speicher-Reaper stoppte drei Hintergrundläufe;
  die CI-Python-gates fahren dieselbe Suite. Die lokale Vollsuite wurde danach in
  zwei Vordergrund-Hälften grün nachgeholt (3435 passed/48 skipped + 2667 passed/21
  skipped = 6102 passed, 69 skipped); auf dem Task-1-Stand war sie zuvor in einem
  Stück grün (6096 passed, 69 skipped, 13:07 min).

## Probe-Läufe (gsd/40-03-probe) und Iterationen

- Task 1 (Kopf c08d4daa): HaRP deploy **40776866858 success**, alle vier
  Matrixzeilen grün; Integration, Python gates, Resilience success.
- Task 2 Iteration 0 (Kopf 0bdd6b71): HaRP **40780234240 failure**, genau eine rote
  Zeile: Teil 4 zählte die zwei Driftzeilen, die die Lockstep-Proben des
  Entwickler-Passes VOR dem Upgrade absichtlich schreiben. Korrektur 87085fd6:
  Fensterung gegen UPGRADE_DRIFT_LINES_AT_UPGRADE (Stand am Ende von Store upgrade
  4) statt gegen null; nicht abgeschwächt (die Aussage ist "keine NEUE Zeile nach dem
  Upgrade").
- Task 2 Iteration 1 (Kopf 87085fd6): HaRP **40783812259 failure**, reiner
  Shell-Defekt des Einfügeskripts (wörtliches `\n` in der stamp-Zeile von Teil 2,
  sqlite3 las `n` als SQL); inhaltlich war alles grün, inklusive der korrigierten
  Driftzeilen-Fensterung. Korrektur 21c8a83a: echte Zeilenfortsetzung.
- Task 2 Iteration 2 (Kopf 21c8a83a): HaRP **40817178890 success**, alle vier
  Matrixzeilen grün.

## Kopf auf main: 5c659b4f, head_green.sh Exit 0

```
40819967257 Integration success
40819967372 HaRP deploy success
40819967269 Resilience success
40819967228 Python gates success
40819967288 OpenSSF Scorecard success
40819967379 Multi-arch image success
40819967308 Security scans success
```

PHP-Gates per Zitat: kein Commit dieses Plans fasst php/ oder backend/appinfo/ an
(`git diff 46df0ee1..5c659b4f --stat -- php backend/appinfo` ist leer), der
PHP-Gate-Stand ist der von 40-02.

Zitate aus dem HaRP-Lauf des Kopfs (40819967372, stable34 amd64), wörtlich:

- Store upgrade 4: `installed_version went from 1.5.0 to 1.6.0`
- Zusicherung 12 (Store upgrade 5):
  - `the overview carries coverage.deduplicated=false and coverage.rulesPending=false, both booleans`
  - `coverage.rulesPending is false before any rule change over the route`
  - `the installed de catalog carries all 353 entries of this commit char-identical, the coverage sentences of plan 39-01 among them`
  - `indexedLeftOut equals the 296 living indexed documents of storage 3, embeddedLeftOut is 296, and without leaveOut neither field is in the answer`
  - `oc_migrations carries the row of Version001600Date20261028000000`
  - `backend_app_version read 1.5.0 before occ upgrade and was dropped by the migration`
  - `backend_app_version reads 1.6.0 again after the first overview call`
  - `the search answers with hits and nextcloud.log carries no drift line beyond the 2 the lockstep probes wrote before the upgrade`
  - `all eleven assurances of this step hold`
- Teil 2 in Store upgrade 5b:
  - `the route saved the changed set and stamped rules_changed_at=1793250786`
  - `coverage.rulesPending reads true after the rule change, the hint of plan 39-01 stands`
  - `the prefix list reads ["Ausschluss36"] again, the hint was driven and the rules stand as before`
  - `all parts of assurance 11 and part 2 of assurance 12 hold`

Probe-Zweig gelöscht: `git push origin --delete gsd/40-03-probe` ausgeführt,
`git ls-remote --heads origin gsd/40-03-probe` antwortet leer (0 Zeilen).

## Testfunktionszahlen (vorher -> nachher, kein Test ersatzlos entfernt)

| Datei | vorher | nachher |
|---|---|---|
| test_upgrade_seed_steps.py | 90 | 90 |
| test_upgrade_seed_fixture.py | 24 | 24 |
| test_language_proof_steps.py | 29 | 29 |
| test_phase36_audit.py | 12 | 12 |
| test_phase40_audit.py | 37 | 43 |
| test_cert_rotation_steps.py (nur Konstante/Stub umbenannt) | unverändert | unverändert |

## Commits

- b84a489f test(40-03): upgrade proof contracts for a start on v1.5.0 (RED)
- c08d4daa ci(40-03): upgrade proof starts on v1.5.0
- 9e199d3d test(40-03): the 1.6 changes survive the upgrade (RED)
- 0bdd6b71 ci(40-03): assurance that the 1.6 coverage fields, hint and sentences survive the upgrade
- 87085fd6 ci(40-03): hold the drift line count against the end of the upgrade, not against nought
- 21c8a83a ci(40-03): the stamp read of part 2 is one sqlite3 call again
- 5c659b4f docs(40-03): record the green iteration 2 probe run (der Kopf, an dem
  alle sieben Läufe hängen)
- dazu dieser abschließende docs-Commit mit den Zitaten (nur .planning/, startet
  per Pfadfilter keinen Workflow; der Beweis-Kopf ist 5c659b4f)
