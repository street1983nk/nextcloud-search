---
phase: 22-messanfahrt-bl-f03
plan: 05
subsystem: messwerkzeuge
tags: [ops, box, messung, v13, ablauf, timer, deckel, streichlogik, abholen]
requires:
  - "22-01 (W1 cpu_sampler.sh, W2 proc_anon_sampler.sh, F4-Definition im W4-Job)"
  - "22-02 (92d, 92e, 90e, 91m)"
  - "22-03 (94c, 95c, 98d)"
  - "22-04 (00-wegwerf.sh b3/b5/b4, 00-typwechsel.sh)"
provides:
  - "00-lauf.sh: unbeaufsichtigter Ablauf (start, ablauf, status, b4) mit Timer shutdown -h +<Rest> und Ruecklesung (55), Blockfolge Weg a und Weg b, Streichlogik D-05 (zeit_fuer, reserve_fuer), Abtaster je Containerleben, Abbrueche 54 bis 58"
  - "00-abholen.sh: Abholen der Rohdaten alle 10 min per scp, Abholmarke ~/work/abgeholt per ssh, Ende nach 00-FERTIG/B4-FERTIG oder drei Fehlversuchen, kein git"
  - "00-ablauf.md: E1 bis E14 mit Zahlen, Abbruchkatalog 40 bis 58, Streichreihenfolge mit den Planminuten des Skripts, F4 woertlich aus measure.yml, Abschnitt 6 leer bis Checkpoint 22-07"
  - "README.md des Laufverzeichnisses: Freigabezeile offen, Ruempfe Rechenblatt, W4-Vorabkurve, Generalprobe, Laufwerte, Offene Owner-Fragen, Bericht"
affects:
  - "22-06 (Generalprobe: 00-lauf.sh gegen die lokale Test-Nextcloud; Risiko Weg b mit 92c ohne occ upgrade pruefen)"
  - "22-07 (Owner fuellt Abschnitt 6, E10-Regel, Laufwerte und Freigabezeile)"
  - "22-08 (Anfahrt: LAUFWERTE-Datei auf der Box, ./00-lauf.sh start, 00-abholen.sh auf der Entwicklungsmaschine)"
  - "22-09 (B4: 00-typwechsel.sh hin, 00-abholen.sh mit neuer Adresse, ./00-lauf.sh start b4)"
tech-stack:
  added: []
  patterns:
    - "Orchestrierung ohne tee-Pipeline um die Bloecke: jeder Tor-Abbruch ist ein exit der Hauptshell, die EXIT-Falle schreibt 00-abbruch und zieht den Timer vor"
    - "Laufwerte aus einer Datei gelesen (awk je Name), nie ausgefuehrt"
    - "Tor gegen Befund: Abbruch nur, wenn der Zustand der Box nicht mehr stimmt; eine fehlende Zahl ist ein Befund und der Lauf misst weiter"
    - "Ablaufskript gegen nachgestelltes sudo, shutdown und git in einer Kopie seines Verzeichnisses getestet"
key-files:
  created:
    - docs/measurements/2026-09-v13-messung/skripte/00-lauf.sh
    - docs/measurements/2026-09-v13-messung/skripte/00-abholen.sh
    - docs/measurements/2026-09-v13-messung/skripte/00-ablauf.md
    - docs/measurements/2026-09-v13-messung/README.md
    - backend/tests/test_v13_ablauf.py
  modified: []
decisions:
  - "Ein Werkzeug, das keine oder eine rote Zahl liefert, waehrend der Zustand der Box stimmt (94c, 95c, 98d, 99d, 00-wegwerf, 90-bestand, 92c-Paar, 97 waehrend), beendet den Lauf nicht; Abbruch nur an Zustandstoren (90e, 92d, 92e, 97 vorher, 54 bis 58)"
  - "Nach einem Abbruch zieht 00-lauf.sh den Timer auf ABBRUCH_FRIST (60 min) vor, damit eine haltende Box nicht bis zum Deckel kostet"
  - "93-nullstand.sh laeuft nach dem regulaeren 92c (Gegenprobe des geleerten Volumens, in Weg b Anstoss des Vorrats), nicht davor"
  - "Die Rueckkehr nach B2 gilt in Weg a gegen 52111/37/0, in Weg b gegen den unmittelbar vor B2 gelesenen Bestand"
  - "Reserve vor B5 enthaelt B4 (wenn geplant) und B3 nur, solange B3 nicht gefahren ist; vor B2 und B3 ist B4 nie reserviert"
  - "Der Timer steht vor dem Waechter der Altverzeichnisse (54): kein Abbruch vor dem ersten Deckel"
metrics:
  duration: "ca. 75 min"
  completed: 2026-09-26
  tasks: 2
  files: 5
---

# Phase 22 Plan 05: Ablaufskript, Abholen, Erwartungen Summary

Die v1.3-Anfahrt ist als ein abgesetztes Skript fahrbar: 00-lauf.sh setzt beim Start den Deckel als `sudo shutdown -h +<Rest>` und liest ihn aus der systemd-Datei zurück (sonst 55), fährt Weg a oder b in der Blockfolge des Plans, streicht B2, B3, B5 und die B4-Vorbereitung nach D-05 und schaltet sich nach der letzten Abholung selbst ab. 00-abholen.sh holt die Rohdaten alle zehn Minuten auf die Entwicklungsmaschine, und 00-ablauf.md hält E1 bis E14, den Abbruchkatalog 40 bis 58 und die F4-Regel fest, bevor die erste Boxminute läuft.

## Aufgaben

| Task | Name | Commit | Dateien |
| ---- | ---- | ------ | ------- |
| 1 | 00-lauf.sh mit Timer, Blockfolge, Streichlogik und Wächtern | 433c531 | 00-lauf.sh, test_v13_ablauf.py |
| 2 | 00-abholen.sh, 00-ablauf.md mit Erwartungen, README-Gerüst | 3f0807d | 00-abholen.sh, 00-ablauf.md, README.md, test_v13_ablauf.py |
| 2 (Nachtrag) | Markdown-Wächter ohne CR-Prüfung | 5fdb8e5 | test_v13_ablauf.py |

## Was entstanden ist

- **00-lauf.sh:** Unterbefehle `start [ablauf|b4]` (setsid nohup, voll umgeleitet nach `00-lauf-protokoll.txt`), `ablauf`, `status`, `b4`. Laufwerte aus `LAUFWERTE` (Vorgabe `$HOME/work/v13-lauf.env`), je Name per awk gelesen, nie ausgeführt; ohne gültiges `DECKEL_MINUTEN`, `BOX_START_EPOCH` (auch nicht in der Zukunft), `B4_GEPLANT`, `EINZELWEG`, `ABBILD_DIGEST` endet `ablauf` mit 2, `b4` ohne `DECKEL_REST_MINUTEN` ebenso. `OUT="$LAUF/rohdaten"` einmal gesetzt und exportiert; `git status --porcelain` über das v1.2- und das Nachfolgeverzeichnis beim Start und im Abschluss (54). Timer mit Rücklesung von `USEC` und `MODE`, Abweichung höchstens 120 s (55). Abtaster W1 und `rss_sampler.sh` bei 5 s je Containerleben neu (nach 92d, jedem 92e, 94c, 95c, 92c). Weg a: Markentor mit den E1-Paaren, Einzelliste, 92d, 97 vorher, Indexgröße de,en, M-01 (loglevel lesen, auf 1, fünf Stufen mit 91m je Stufe, 95c, 91m über das Kaltstart-Fenster, loglevel zurück, 57), Bodensatz (92e 120, 94c, 92e 0), 99d ohne `FINDLING_LOAD_PASSWORD`, B2 (120 + 20 synthetische Scans im Wegwerf-Container, WebDAV, W2 bei 1 s, 97 waehrend, Löschen, Rückkehr, 56), Umbau (92e sechs Sprachen, Statusreihe 30 s, Platz 60 s, Wandzeit bis zur Logzeile, 58), Indexgröße sechs Felder, 98d, B3, B5, 90-bestand, 92c-Paar (36 und 0), 93-nullstand, Abschluss. Weg b: 92c-Paar, Vollreindex, Einzelliste, dann ab 97 vorher ohne 92d und ohne 92c am Ende.
- **00-abholen.sh:** `BOX_ADRESSE` Pflicht, Schlüssel und known_hosts aus `FINDLING_LOADTEST_DIR`, `scp -r` in ein Stufenverzeichnis und von dort in `rohdaten/`, danach `ssh ... 'date +%s > ~/work/abgeholt'`, Protokoll `v13-abholen.log` im Zustandsverzeichnis. Ende mit 0 nach `00-FERTIG` (B4 nicht geplant, gestrichen) oder `B4-FERTIG`, mit 1 nach drei Fehlversuchen in Folge. Kein git-Aufruf.
- **00-ablauf.md:** acht Abschnitte, Überschriften ohne Umlaute. E1 mit den Markenwerten aus dem Code (Wächter liest `ANALYZER_VERSION`, `INDEX_VERSION`, `SCHEMA_VERSION`, `TANTIVY_VERSION`, `embedding_mark` und hält sie gegen die `ERWARTUNG_*` von 00-lauf.sh). Katalog 40 bis 58 je genau eine Zeile mit Skript, Bedingung und Folge im Ablauf. Abschnitt 6 enthält die drei Fragen mit „Antwort: offen (Checkpoint 22-07).“ und den Research-Vorschlag zur dismax-Regel ausdrücklich als „Vorschlag der Research, nicht beschlossen“. Abschnitt 7 nennt die neun `PLAN_*`-Konstanten des Skripts. Abschnitt 8 zitiert F4 wörtlich aus measure.yml.
- **README.md:** Freigabezeile `Anfahrt freigegeben: offen (Owner-Checkpoint 22-07)`, leere Rümpfe.
- **test_v13_ablauf.py:** 51 Fälle, darunter zwei Läufe von 00-lauf.sh in einer Kopie seines Verzeichnisses gegen nachgestelltes sudo, shutdown und git: ohne Rücklesung 55 (kein Wächter 54 davor, Meldung gesendet), mit Rücklesung und schmutzigem v1.2-Verzeichnis 54 und vorgezogener Timer `-h +60`; fünf Läufe von 00-abholen.sh gegen nachgestelltes scp und ssh.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Korrektheit] Timer vor dem Wächter 54**
- **Found during:** Task 1
- **Issue:** Stünde der Wächter der Altverzeichnisse vor dem Timer, liefe eine Box nach Abbruch 54 ohne Deckel weiter.
- **Fix:** Timer zuerst, dann 54; nach jedem Abbruch zieht die EXIT-Falle den Timer auf 60 min vor (außer beim Ende durch Signal).
- **Commit:** 433c531

**2. [Rule 2 - Korrektheit] Befund statt Abbruch bei Messwerkzeugen ohne Zahl**
- **Found during:** Task 1
- **Issue:** Ein Abbruch bei 48, 49, 50 oder einem Fehler in 94c hätte die folgenden Pflichtzahlen (Umbau, 92c) der einen Anfahrt gekostet, obwohl der Zustand der Box stimmt.
- **Fix:** Zeile `befund` plus Meldung, der Lauf misst weiter; abgebrochen wird an Zustandstoren. In 00-ablauf.md Abschnitt 4 als Spalte „Folge im Ablauf“ festgehalten. Nach einem Befund in 94c geht die Entladefrist trotzdem auf 0 zurück.
- **Commit:** 433c531, 3f0807d

**3. [Rule 1 - Bug] Rückgabewert von 94c durch den folgenden 92e-Neubau überschrieben**
- **Found during:** Task 1 (Durchsicht vor dem Commit)
- **Fix:** eigene Variable `rc_94c`.
- **Commit:** 433c531

**4. [Rule 1 - Bug] Markdown-Wächter hätte auf einem Windows-Checkout versagt**
- **Found during:** Task 2, nach dem Commit (Git-Warnung LF zu CRLF)
- **Issue:** `.md` steht außerhalb der eol-Regeln von `.gitattributes`.
- **Fix:** CR-Prüfung aus dem Markdown-Wächter entfernt, Dash-Prüfung bleibt.
- **Commit:** 5fdb8e5

### Weitere Anpassungen

- `93-nullstand.sh` läuft unmittelbar nach dem regulären 92c statt vor 92c (Begründung in 00-ablauf.md Abschnitt 2); der Plan nennt es in PIII neben 90-bestand.
- Die Rückkehr nach B2 prüft `indexiert` aus der state.db (wie 92d, Schritt 17), weil die PHP-Hälfte diese Zahl nie schreibt; in Weg b gegen den Bestand vor B2.
- Die Frist des Umbaus (und des Vollreindex in Weg b) ist die Abschaltung minus `PLAN_ABHOLEN`, damit die Daten vor dem Stopp abgeholt werden; der Vollreindex in Weg b verwendet dafür ebenfalls 58.
- Der Abbruch durch Signal endet mit 143 (Zeile `00-abbruch-durch-signal`), in Abschnitt 4 benannt.
- 00-abholen.sh endet nach `00-FERTIG` auch bei `B4_GEPLANT=ja`, wenn die Box `b4 gestrichen` meldet, und wartet bei `b4 vorbereitet` auf `B4-FERTIG`.
- 00-abholen.sh erwartet den Schlüssel als `$FINDLING_LOADTEST_DIR/findling-loadtest` (Plan); das Runbook legt ihn unter `~/.ssh/findling-loadtest` ab, also vor der Anfahrt kopieren oder `SCHLUESSEL` setzen.

### TDD Gate Compliance

Beide Tasks tragen tdd="true"; Werkzeug und Wächter sind je Task in einem Commit gelandet (Muster aus 22-02 bis 22-04), es gibt keine getrennten test(...)-Commits. Die Wächter liefen vor jedem Commit grün, 00-lauf.sh und 00-abholen.sh dabei auch als Programme gegen nachgestellte Befehle.

## Verification

- `ruff check .`, `ruff format --check .` (146 Dateien), pyright latest 0 Fehler, vulture sauber
- pytest test_v13_ablauf.py, test_v13_wechsel.py, test_v13_zyklen.py, test_v13_wegwerf.py, test_dismax_probe.py, test_measurement_scripts.py, test_public_artifacts.py: 678 passed
- `grep -c "shutdown -h +"` 00-lauf.sh 3, `FINDLING_OCR_LANGUAGES` 0, `exit 5[4-8]` 10, `zeit_fuer` 11; 00-ablauf.md 8 Abschnitte, 14 E-Zeilen, keine Dashes; 00-abholen.sh ohne `git `; README einmal „Anfahrt freigegeben:“
- `sh -n` beider Skripte grün, beide mit Modus 100755 im Index
- Keine Änderung unter backend/src/findling oder php/, daher kein Baumhash-Bump. MESS-07, MESS-08 und MESS-09 bleiben offen. Kein Push, keine Box, kein AWS-Aufruf.

## Offene Risiken für die Generalprobe (22-06)

- **Weg b und 92c ohne `occ upgrade`:** 92c installiert die PHP-Hälfte, fährt aber anders als 92d kein `occ upgrade`. Auf einer Box mit PHP-Hälfte 1.2 könnte Nextcloud danach im Modus „requires upgrade“ stehen (dann fehlt `app_api:app`, 22-02). Weg a ist davon nicht betroffen, weil 92c dort nach 92d läuft.
- **Admin-Übersicht:** Die Felder `rebuildRunning`, `rebuildDone`, `rebuildTotal`, `languagesActive`, `embedded` werden rekursiv aus der JSON-Antwort gesucht; die Generalprobe sollte eine echte Antwort der Route gegen `umbau-status.jsonl` halten.
- **Logzeile des Umbaus:** Die Wandzeit hängt daran, dass „the rebuilt index directory is in place“ in `docker logs` erscheint (Level info des Containers).

## Known Stubs

Der README-Rahmen und Abschnitt 6 von 00-ablauf.md sind absichtlich leer: sie werden am Checkpoint 22-07 (Rechenblatt, Laufwerte, Owner-Antworten) und nach der Anfahrt (Bericht) gefüllt. Sie verhindern das Ziel dieses Plans nicht.

## Threat Flags

Keine neuen Flächen außerhalb des Threat-Modells: T-22-17 (Timer mit Rücklesung, 55, Neusetzen in b4, Selbstabschaltung, Vorziehen nach Abbruch), T-22-18 (Laufwerte und Passwortdateien außerhalb des Repos, nie Kommandozeile, Lastpasswort nur in einer Subshell), T-22-19 (OUT exportiert, 54), T-22-21 (UTC-Stempel je Block, 00-gestrichen.txt). T-22-20 bleibt bei 22-08 und 22-09 (Gate vor dem Rohdaten-Commit); das Protokoll von 00-abholen.sh mit der Boxadresse liegt außerhalb des Repos.

## Self-Check: PASSED

- FOUND: 00-lauf.sh, 00-abholen.sh, 00-ablauf.md, README.md, test_v13_ablauf.py
- FOUND: 433c531, 3f0807d, 5fdb8e5
