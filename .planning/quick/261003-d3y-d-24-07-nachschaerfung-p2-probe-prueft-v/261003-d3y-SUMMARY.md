---
phase: quick-261003-d3y
plan: 01
subsystem: probe, admin-ui, measurements
tags: [D-24-06, D-24-07, PRUEF-01, probe, hardware_short, 28-07]
requires: [profile.suggest, probe.CAUSES, 10-zelle.sh]
provides: [probe.judge_hardware, cause hardware_short, Abbruch 74]
affects: [Admin-Seite Probe-Karte, Messkette 28-07]
tech-stack:
  added: []
  patterns: [Schwellenpruefung ueber profile.suggest statt eigener Konstanten]
key-files:
  created: []
  modified:
    - backend/src/findling/probe.py
    - backend/src/findling/worker/probe_run.py
    - backend/tests/test_probe.py
    - backend/tests/test_probe_run.py
    - php/lib/Service/AdminViewService.php
    - php/lib/Service/ProbeService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/*.json, php/l10n/*.js (16 Dateien)
    - docs/l10n-{french,spanish,italian,dutch,portuguese}.md
    - docs/admin-page.md
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/00-ablauf.md
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/12-slotkosten.py
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh
    - backend/tests/test_v14_teilkorpus.py
    - backend/tests/test_v14_zelle.py
decisions:
  - "D-24-07 P2 (Owner 03.10.2026): die Probe prüft vor jeder Messung die Vorschlags-Schwellen über profile.suggest(); darunter nofit hardware_short ohne Messung; profile.effective() unverändert"
  - "Zellen 3, 4 (m7g.large St-T/L-T) und 10 (c7a.xlarge L-T) gestrichen (Owner 03.10.2026), Matrix 18 Zellen, Nummern stabil"
  - "10-zelle.sh bricht bei Probe-Ursache hardware_short mit 74 ab statt per occ zu erzwingen"
metrics:
  duration: "ca. 30 min"
  completed: 2026-10-03
  tasks: 3
  commits: 4
---

# Quick 261003-d3y: Probe prüft die Vorschlags-Schwellen (D-24-07) Summary

Die Probe hält das Ziel vor der Pause gegen `profile.suggest()` und endet auf einer Box unter den Schwellen sofort mit `nofit hardware_short` (kein Download, kein Modell- oder OCR-Kind); die Ursache steht mit den Schwellen beider Profile in allen 8 Sprachen auf der Admin-Seite, und die Messkette streicht die Zellen 3, 4 und 10 und bricht bei `hardware_short` mit 74 ab.

## Commits (alle NUR LOKAL, kein Push)

| Task | Commit | Inhalt |
|------|--------|--------|
| 1 | 52390ff7 | feat(probe): check the suggestion thresholds before measuring (D-24-07) |
| 2 | 53170027 | feat(admin): name the threshold cause hardware_short in every catalogue (D-24-07) |
| 1+2 | d799ef53 | test(measurements): re-pin the tree hashes after hardware_short (D-24-07) |
| 3 | 3d1c6d72 | docs(measurements): strike cells 3, 4 and 10, abort 74 on hardware_short (D-24-07) |

## RED-Beleg (Task 1, vor der Änderung)

`uv run pytest tests/test_probe.py tests/test_probe_run.py -q`:

```
38 failed, 109 passed, 1 skipped, 1 warning in 10.27s
E       AttributeError: module 'findling.probe' has no attribute 'judge_hardware'
E       AssertionError: assert ('fits', '') == ('nofit', 'hardware_short')
```

Die zweite Zeile ist genau der Produktwiderspruch aus Lauf 6: Referenzbox (2 Kerne, 2 GiB), Ziel standard, die Probe sagte `fits`.

Gegenprobe Task 3: mit auskommentiertem `hardware_short`-Zweig in 10-zelle.sh fällt der neue Zellentest mit `assert 0 == 74` (danach Datei bytegleich zurück).

## Testbilanz

- Betroffene Suiten Task 1: vorher 109 passed (RED-Lauf), nachher alle grün (180 passed inkl. probe_endpoint; parity siehe Abweichung 2).
- Task 2: admin_ui_contract + parity + probe + probe_run + php-boundary: 271 passed, 1 skipped.
- Task 3: v14_teilkorpus + v14_zelle + v14_typwechsel + measurement_scripts: grün bis auf die zwei vorbestehenden CRLF-Fälle (unten).
- Volle Suite am Ende: **4408 passed, 25 skipped, 2 failed** (472 s). Die 2 Fehler sind `test_the_measurement_script_carries_no_carriage_return` und `test_the_script_of_this_run_starts_with_a_shebang` für `11-probe-route.py`: lokale Arbeitskopie hat CRLF (seit 30.09., Datei in diesem Task nicht berührt, `git diff` leer); der committete Blob ist LF (`git show HEAD:... | grep -c $'\r'` = 0). In CI grün; lokal reicht ein Re-Checkout der Datei. Nicht angefasst (Scope).
- Gates vor jedem Commit: ruff check (inkl. skripte-Verzeichnis), ruff format --check, pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest) 0 Fehler, vulture 80 sauber, `bash -n 10-zelle.sh` ok.
- `git diff 841fd1b8 --stat -- backend/src/findling/profile.py`: leer, `effective()` unverändert.

## Owner-Nachtrag 03.10. (Zelle 10)

Die im Plan als offene Owner-Frage geführte Zelle 10 (c7a.xlarge, L-T/Leistung, 4 Kerne / 8 GiB unter der Leistungsschwelle 6 Kerne + 12 GB): **ERLEDIGT, Owner-Entscheid: streichen.** Umgesetzt in 3d1c6d72: Matrixzeile 10 entfällt, Zellenzahl 18 (nicht 19), `12-slotkosten.py` CELLS 18, Test pinnt 18, Begründungszeile im Ablauf nennt alle drei Zellen; Leistung auf c7a messen die Zellen 14, 17 und 21. Kein weiterer Test referenzierte Zelle 10.

## Deviations from Plan

**1. [Owner-Nachtrag] Zelle 10 zusätzlich gestrichen** (siehe oben), Matrix 18 statt 19 Zellen.

**2. [Rule 3 - Plan-Kopplung] Paritätstest zwischen Commit 1 und 2 rot**
- `test_probe_php_parity[CAUSES]` vergleicht probe.CAUSES mit den PHP-Spiegeln; der Plan legt Python in Task 1, PHP in Task 2. Ein PHP-Nachzug in Task 1 hätte dafür `test_the_script_and_the_template_name_every_probe_code_alike` rot gemacht (Satz und Kataloge gehören zu Task 2). Entschieden: Dateiteilung des Plans behalten; der Stand von 52390ff7 allein hat genau diesen einen roten Test, ab 53170027 grün.

**3. [Rule 3 - Blocker] Baumhash-Pins nachgeführt (d799ef53)**
- `test_the_recipe_reproduces_the_tree_hash_of_the_python_package` und `..._php_half` pinnen den heutigen Baum; Task 1 (probe.py, probe_run.py) und Task 2 (3 PHP-Dateien) bewegen beide Hashes. Vor der Änderung reproduziert (Archiv von 841fd1b8: 556148.../3a6ae1..., gleich den Pins), danach per Rezept auf dem Archiv von HEAD neu gemessen: Paket 71 Dateien `1a0598a6...`, PHP 87 Dateien `8ee9286c...`; Chronik-Absätze ergänzt. Eigener Commit, weil die Pins zu Task 1 und 2 zusammen gehören.

**4. Französisches Leerzeichen vor dem Doppelpunkt:** der Plan sprach von geschütztem Leerzeichen; der bestehende Katalog ("Détecté : ...") nutzt ein normales Leerzeichen (Byteprüfung 0x20). Übernommen wie im Katalog.

**5. Profil-Test economy auf Referenzbox** zusätzlich (Abwärtsweg misst weiter, beginnt mit pause), als Positivkontrolle, dass die Prüfung nur Messziele trifft.

Bewusst unverändert (Plan-Entscheide): `02-rechenblatt.py` (Deckel 59,43 USD ist der freigegebene Budgetdeckel D-28-14, per Test gepinnt; das Streichen senkt nur den Verbrauch; die Tabelle dort führt Zelle 3/4/10 weiter als Kostenposten) und `00-kette.sh` (Zellen kommen aus LAUFWERTE `ZELLEN`). Für Lauf 7: `ZELLEN` in den Laufwerten ohne St-T/L-T auf m7g.large und ohne L-T auf c7a.xlarge setzen.

## CI-Vorbehalte

- **php -l / PHPUnit:** lokal kein PHP. Geändert sind nur zwei Array-Konstanten (ein String mehr), ein Map-Eintrag in templates/admin.php und ein Eintrag in admin.js, per Review auf Syntax geprüft; Beleg mit dem nächsten Owner-Push (php.yml).
- 16 Katalogdateien: JSON-Gültigkeit lokal durch die Katalogtests belegt (G1/G2, Zählgate 292).

## Known Stubs

Keine. (`STUB_URSACHE` ist ein Test-Stub des boxlosen Harness, kein Produkt-Stub.)

## Threat Flags

Keine neue Oberfläche. T-d3y-01 (hardware_short nur nofit, finish narrow/fits wirft) und T-d3y-03 (Holds werden im finally freigegeben, Test prüft `released()` und Meta `done`) per Test belegt; T-d3y-04 durch Parität.

## Self-Check: PASSED

- Dateien: probe.py enthält `CAUSE_HARDWARE_SHORT` und `judge_hardware`; probe_run.py `judge_hardware(target, self._hardware())`; admin.php und 10-zelle.sh enthalten `hardware_short`.
- Commits 52390ff7, 53170027, d799ef53, 3d1c6d72 vorhanden.
- `grep -c "| m7g.large | St-T\|| m7g.large | L-T\|| c7a.xlarge | L-T" 00-ablauf.md` = 0.
