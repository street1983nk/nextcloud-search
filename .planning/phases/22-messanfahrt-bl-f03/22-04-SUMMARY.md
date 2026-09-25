---
phase: 22-messanfahrt-bl-f03
plan: 04
subsystem: messwerkzeuge
tags: [ops, box, messung, v13, bl-f04, wegwerf, typwechsel, aws, graviton3]
requires:
  - "22-01 (W3 ocr_slot_probe.py, W4-Aufrufform des Scans in measure.yml)"
provides:
  - "00-wegwerf.sh: B3 (W3 N 1/2 auf cpuset 0,1 unter 2g plus Einzelmodus), B5 (embed.bench threads 1/2 x batch 2/8, sequence 512, rss_sampler.sh am Bench-Namen), B4 (W3 N 1 bis 16, bench T 1 bis 8, auf nproc gekuerzt); 50 kein Leerlauf oder keine Zahl in B3/B5, 51 fremder Container oder keine Zahl in B4; Endmarken B3-FERTIG, B5-FERTIG, B4-FERTIG"
  - "00-typwechsel.sh: vorpruefung (instanceInitiatedShutdownBehavior stop, sonst 52), hin (stop, m7g.4xlarge, start, Rueckfall m7g.2xlarge, dann m7g.large mit b4-entfallen), zurueck (stop, m7g.large, kein start, b4-laufzeit-s), preis (get-products mit sechs Filtern); 53 bei Typ- oder Zustandsabweichung"
affects:
  - "22-05 (00-lauf.sh ruft 00-wegwerf.sh b3/b5 nach den BL-F03-Produktmessungen und b4 zuletzt; 00-ablauf.md katalogisiert 50 bis 53)"
  - "22-06 (Generalprobe; vorpruefung ist eine lesende AWS-Abfrage und kann dort frei laufen)"
  - "22-07 (Rechenblatt: B4-Satz aus preis, B4-Stunden aus den Stempeln)"
  - "22-09 (Anfahrt: vorpruefung VOR dem Timer, hin/zurueck um B4)"
tech-stack:
  added: []
  patterns:
    - "Bench-Container abgesetzt unter festem Namen, damit rss_sampler.sh ihn fassen kann; max anon aus den CSV-Zeilen statt aus der Schlusszeile"
    - "Produkt nur gelesen: Startzeitpunkt vor und nach dem Block verglichen"
    - "AWS-Werkzeug gegen nachgestellte Kommandozeile und nachgestelltes aws_box.sh getestet"
key-files:
  created:
    - docs/measurements/2026-09-v13-messung/skripte/00-wegwerf.sh
    - docs/measurements/2026-09-v13-messung/skripte/00-typwechsel.sh
    - backend/tests/test_v13_wegwerf.py
  modified: []
decisions:
  - "B5 laeuft ebenfalls unter --memory 2g --memory-swap 2g wie das Produkt (Plan nennt die Grenze nur fuer B3); B3 zusaetzlich mit --memory-swap 2g"
  - "runState kommt aus der Admin-Seite (Anmeldung wie 94c, Passwort aus Umgebung oder PWFILE), weil occ findling:index nur den Arbeitsvorrat nennt; unlesbar zaehlt als nicht im Leerlauf"
  - "Aufgeteilte Abbruchwerte: 50 fuer B3/B5 (Leerlauf, Produktstart bewegt, Probe ohne Zahl, Block unvollstaendig), 51 fuer B4 (fremder Container, Probe ohne Zahl, Block unvollstaendig), 52/53 im Typwechsel"
  - "Rohdatei des Typwechsels mit Platzhaltern <instanzkennung> und <adresse-der-box>; die Ausgabe von aws_box.sh geht nach stderr, die neue Adresse steht nur auf dem Terminal"
  - "hin faehrt die vorpruefung selbst mit; ein gescheiterter Start mit nicht gestoppter Box ist kein Kapazitaetsfall und endet mit 53 ohne weiteres modify"
  - "preis endet mit 1 und 'preis <typ> unlesbar', wenn die API keinen eindeutigen Satz liefert (aws_box.sh notiert, dass dem Konto pricing:GetProducts fehlt); keine Preisliste wird geladen"
metrics:
  duration: "ca. 25 min"
  completed: 2026-09-26
  tasks: 2
  files: 3
---

# Phase 22 Plan 04: Wegwerf-Blöcke und Typwechsel Summary

Zwei Werkzeuge im Laufverzeichnis 2026-09-v13-messung: 00-wegwerf.sh fährt B3, B5 und B4 der BL-F04-Mitmessliste ausschließlich in Wegwerf-Containern desselben Digests (jedes `docker run` mit `--network none` und ausdrücklichem `--cpuset-cpus`), prüft vor B3/B5 den Leerlauf des Produkts und fasst den Produktcontainer nicht an; 00-typwechsel.sh läuft auf der Entwicklungsmaschine, beweist vor der Anfahrt, dass `shutdown -h` ein Stopp ist, und fährt den Typwechsel auf m7g.4xlarge mit Rückfallkette und Stempeln für die Handrechnung der B4-Kosten.

## Aufgaben

| Task | Name | Commit | Dateien |
| ---- | ---- | ------ | ------- |
| 1 | 00-wegwerf.sh (B3, B5, B4) mit Wächtern | b5f27b1 | 00-wegwerf.sh, test_v13_wegwerf.py |
| 2 | 00-typwechsel.sh (vorpruefung, hin, zurueck, preis) mit Wächtern | e072b15 | 00-typwechsel.sh, test_v13_wegwerf.py |

## Was entstanden ist

- **00-wegwerf.sh b3:** Leerlaufprüfung (Arbeitsvorrat aus `occ findling:index`, runState aus der Admin-Seite; beides muss 0 und idle sein), Scan aus `build_load_corpus._scan_pdf` mit Seed `phase-22-w4` im Wegwerf-Container (PYTHONPATH statt `sys.path.insert`, das das Maschinenpfad-Gate verbietet), W3 N 1 und 2 auf cpuset 0,1 unter 2g, je 3 Runden, dann `--mode single`. Ausgabe `b3-slots-N.txt`, `b3-single.txt`.
- **00-wegwerf.sh b5:** dieselbe Leerlaufprüfung, dann vier Kombinationen threads 1/2 und batch 2/8 bei sequence 512 auf cpuset 0,1. Jeder Bench-Container läuft abgesetzt unter `findling-wegwerf-b5-t<T>-b<B>`, daneben `rss_sampler.sh` unverändert gegen genau diesen Namen; max anon aus den CSV-Zeilen (`b5-max-anon-*.txt`), Bench-Ausgabe über `docker logs` (`b5-threads-*-batch-*.txt`), danach `docker rm -f` nur dieses Namens.
- **00-wegwerf.sh b4:** verlangt null laufende Container (sonst 51), liest `nproc`, kürzt N 1 2 4 8 12 16 und T 1 2 4 8 auf die Kernzahl (`b4-gekuerzt-auf <kerne>`), protokolliert `b4-grenze keine` und `b4-kernel-mem`, W3 auf cpuset 0 bis N-1 ohne Speichergrenze, bench `--batch 2 --sequence 512` auf cpuset 0 bis T-1. Ausgabe `b4-slots-N.txt`, `b4-bench-T.txt`.
- **Gemeinsam:** UTC-Stempel beim Betreten und Verlassen jedes Blocks, Produktstart vor und nach B3/B5 (bewegt heißt 50), jede Probe braucht ihre Endzahl (`pages_per_second_median`, `rounds`, `tokens_per_second_p50`), Endmarke `block-durchgelaufen` fail-closed, danach `B3-FERTIG`/`B5-FERTIG`/`B4-FERTIG` in die Rohdatei.
- **00-typwechsel.sh:** Zugangsdaten nur als `: "${...:?}"`, `MSYS_NO_PATHCONV=1` plus `MSYS2_ARG_CONV_EXCL`, Instanzkennung aus der aws_box.sh-Zustandsdatei. Stempel `typwechsel-<schritt> <UTC> epoch <s>` für vorpruefung, hin-start, hin-gestoppt, hin-laeuft, hin-ende, zurueck-start, zurueck-gestoppt, zurueck-ende, preis; `zurueck` rechnet daraus `b4-laufzeit-s`. Endmarken `TYPWECHSEL-<SCHRITT>-FERTIG`.
- **Tests:** test_v13_wegwerf.py, 54 Fälle: boxlose Verweigerung beider Skripte (Blöcke, Digestformen, Unterbefehle, Preistypen), Isolation jedes docker run, Blockinhalte, cpuset_bis aus der Datei ausgeführt, Leerlauf vor erster Probe, Produkt unberührt, Scan nur aus dem Generator; für den Typwechsel Läufe gegen nachgestellte AWS-Kommandozeile und aws_box.sh (52 bei terminate/leer/unlesbar, Reihenfolge stop < modify < start, Rückfall 2xlarge, Ende auf m7g.large, 53 bei klebendem Typ und bei laufender Box nach gescheitertem Start, zurueck ohne start, Laufzeit aus Stempeln, Preis aus PriceList, 1 ohne Satz, keine der beiden Attrappen-Zugangsdaten in stdout, stderr, Rohdatei oder Aufrufen).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] b4-laufzeit-s aus einem leeren Stempel**
- **Found during:** Task 2 (Wächter test_the_type_switch_comes_back_by_stop_and_modify_without_a_start)
- **Issue:** Die erste Fassung prüfte `"$von$bis"` zusammen; ohne hin-Stempel sah das wie eine Zahl aus, und die Laufzeit war die ganze Epoche (1790374178 s).
- **Fix:** Jeder Stempel einzeln geprüft, dazu `bis >= von`; sonst `b4-laufzeit-s unbestimmt`.
- **Commit:** e072b15

**2. [Rule 3 - Blocking] Scan-Aufruf ohne sys.path.insert**
- **Found during:** Task 1
- **Issue:** Die W4-Aufrufform in measure.yml trägt `sys.path.insert`, das MACHINE_SHAPES im Laufverzeichnis verbietet.
- **Fix:** `-e PYTHONPATH=/repo/scripts/dev` und `import build_load_corpus` direkt; gleicher Generator, gleicher Seed.
- **Commit:** b5f27b1

**3. [Rule 2 - Korrektheit] Endzahl je Probe und Endmarke je Block**
- **Found during:** Task 1
- **Issue:** Lehre aus 22-02/22-03: ein Werkzeug, das nach einem Abbruch im tee-Block mit 0 endet, meldet eine Messung, die nicht stattfand.
- **Fix:** probe_pruefen/bench_pruefen verlangen die Endzahl, sonst 50/51; ohne `block-durchgelaufen` ebenfalls 50/51. Scratchpad-Lauf mit kaputtem PATH endete tatsächlich mit 51 statt 0.
- **Commit:** b5f27b1

**4. [Rule 2 - Korrektheit] Gescheiterter Start bei laufender Box**
- **Found during:** Task 2
- **Issue:** Scheitert `aws_box.sh start` nach dem Start der Instanz (etwa an der SSH-Regel), wäre ein folgendes modify auf eine laufende Instanz gegangen.
- **Fix:** Nach jedem gescheiterten Start wird der Zustand gelesen; nicht `stopped` heißt 53 ohne weiteres modify.
- **Commit:** e072b15

### Weitere Anpassungen

- OUT-Vorgabe beider Skripte ist `$SKRIPTE/../rohdaten` wie bei 92d, 94c, 95c (der Plan schreibt "v13-rohdaten").
- B5 läuft unter `--memory 2g --memory-swap 2g` wie das Produkt; B3 zusätzlich mit `--memory-swap 2g`.
- `hin` fährt die vorpruefung selbst mit, damit der Typwechsel nie auf einer Box mit terminate-Verhalten läuft.
- `preis` endet ohne eindeutigen Satz mit 1 (Plan nennt keinen Wert); aws_box.sh vermerkt, dass dem Konto `pricing:GetProducts` fehlen kann.
- Vier Unterbefehle schreiben Endmarken `TYPWECHSEL-*-FERTIG`, damit ein Aufrufer nicht auf die bloße 0 angewiesen ist.

### TDD Gate Compliance

Beide Tasks tragen tdd="true"; Werkzeug und Wächter sind je Task in einem Commit gelandet (Muster aus 22-02 und 22-03), es gibt keine getrennten test(...)-Commits. Die Wächter liefen vor jedem Commit grün; 00-wegwerf.sh zusätzlich im Scratchpad gegen nachgestelltes sudo, docker, curl und nproc gefahren: b4 bis B4-FERTIG (gekürzt auf 8), b5 bis B5-FERTIG mit vier max-anon-Zeilen, b3 bis B3-FERTIG, und 50 bei runState running sowie ohne Passwort.

## Verification

- `ruff check .`, `ruff format --check .` (145 Dateien), pyright latest 0 Fehler, vulture sauber
- pytest test_v13_wegwerf.py, test_measurement_scripts.py, test_public_artifacts.py, test_v13_zyklen.py: 548 passed
- `grep -c "\-\-network none"` 00-wegwerf.sh 6, `grep -c "docker run"` 6; `b4-gekuerzt-auf` 1; `exit 50` 3
- `instanceInitiatedShutdownBehavior` 4, `exit 52` 1, `m7g.4xlarge` 3, echo/printf mit AWS_SECRET_ACCESS_KEY 0
- `sh -n` beider Skripte grün, beide mit Modus 100755 im Index, ASCII, keine CR, keine Dashes
- Keine Änderung unter backend/src/findling oder php/, daher kein Baumhash-Bump. MESS-07 bleibt offen. Kein Push, keine Box, kein AWS-Aufruf.

## Known Stubs

Keine.

## Threat Flags

Keine neuen Flächen außerhalb des Threat-Modells: T-22-13 (Zugangsdaten nur auf Gesetztheit geprüft, Attrappenwerte erscheinen in keiner Ausgabe, Test), T-22-14 (Stempel und b4-laufzeit-s für die Handrechnung, Rückfallkette endet auf m7g.large), T-22-15 (vorpruefung verlangt stop, sonst 52; hin fährt sie selbst), T-22-16 (--network none an jedem docker run, synthetischer Scan, kein Nutzerpfad im Mount).

## Self-Check: PASSED

- FOUND: 00-wegwerf.sh, 00-typwechsel.sh, test_v13_wegwerf.py
- FOUND: b5f27b1, e072b15
