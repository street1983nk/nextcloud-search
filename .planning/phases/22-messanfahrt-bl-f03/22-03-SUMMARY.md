---
phase: 22-messanfahrt-bl-f03
plan: 03
subsystem: messwerkzeuge
tags: [ops, box, messung, v13, dismax, tantivy, bodensatz, kaltstart]
requires: []
provides:
  - "94c-bodensatz-zyklen.sh: Marke A, Zyklus 1, C1, Zyklus 2, C2 in einem Containerleben; zyklus2-minus-a und zyklus2-minus-c1 (46 Zyklus offen, 47 Schalter nicht 120, 29/31/32/33 wie 94b)"
  - "95c-kaltstart.sh: Kaltzyklus mit Trefferpflicht der ersten Suche, hoechstens 3 Zyklen, sonst 48; kaltstart-fenster fuer 91m"
  - "98d-dismax-probe.py: summe, dismax_t00, dismax_t01, altplan bis SEARCH_RRF_WINDOW im Produktcontainer; nur Zahlen und file_ids; 49 bei ungleicher Treffermenge, 2 ohne Index oder Wortliste"
affects:
  - "22-05 (00-lauf.sh ruft 92e mit Schalter 120 vor 94c, 95c nach den Laststufen, 98d nach dem Umbau; 00-ablauf.md katalogisiert 46 bis 49 und traegt die dismax-Regel)"
  - "22-06 (Generalprobe der drei Werkzeuge)"
  - "22-07 (dismax-Regel am Owner-Checkpoint, gegen die Kennzahlnamen von 98d)"
tech-stack:
  added: []
  patterns:
    - "Treffermengengleichheit zweier Anfragen als zwei Differenzzaehlungen (Must a, MustNot b) statt Listenvergleich"
    - "Kaltzyklus wird ganz wiederholt statt eine leere Antwort herauszurechnen"
    - "Endmarke am Blockende (fail-closed) auch in 94c und 95c"
key-files:
  created:
    - docs/measurements/2026-09-v13-messung/skripte/94c-bodensatz-zyklen.sh
    - docs/measurements/2026-09-v13-messung/skripte/95c-kaltstart.sh
    - docs/measurements/2026-09-v13-messung/skripte/98d-dismax-probe.py
    - backend/tests/test_v13_zyklen.py
    - backend/tests/test_dismax_probe.py
  modified: []
decisions:
  - "94c und 95c lesen das Passwort zuerst aus der Umgebung (PASSWORT_ENV), dann aus PWFILE (Vorgabe $HOME/work/.pw/admin), in der Reihenfolge von 99d"
  - "95c: steht vor der kalten Suche engineState loaded, ist der Zyklus ungueltig und wird wiederholt (Ersatz fuer den Wachposten von 95b, der die Modell-Route per Logmuster suchte)"
  - "98d: Einwortzeilen bauen den per-Wort-dismax aus ihrer umgeschriebenen Form (Umlautvariante eingeschlossen); Mehrwortzeilen mit Umlautvariante, Operator, Phrase, Klammer oder Dateityp sind rueckfall und nur mit der Summe gemessen"
  - "98d liest die Stichprobe aus WORDS von build_load_corpus.py per ast (Datei per docker cp nach WORTLISTE), weil scripts/ nicht im Abbild liegt"
metrics:
  duration: "ca. 35 min"
  completed: 2026-09-25
  tasks: 2
  files: 5
---

# Phase 22 Plan 03: Bodensatz-Zyklen, Kaltstart, dismax-Probe Summary

Drei Box-Werkzeuge im Laufverzeichnis 2026-09-v13-messung: 94c misst den Bodensatz über zwei Indexzyklen in EINEM Containerleben (C2 minus A, C2 minus C1), 95c misst die Kaltstartlatenz nur mit einer ersten Suche, die Treffer liefert, und 98d vergleicht im Produktcontainer die Summenrangliste mit per-Wort-dismax (tie 0.0 und 0.1) und dem Altplan. Alle drei stehen unter Wächtern; die dismax-Rechnung ist gegen einen Sechs-Feld-Index unit-getestet.

## Aufgaben

| Task | Name | Commit | Dateien |
| ---- | ---- | ------ | ------- |
| 1 | 94c-bodensatz-zyklen.sh und 95c-kaltstart.sh mit Wächtern | 2afafb4 | 94c-bodensatz-zyklen.sh, 95c-kaltstart.sh, test_v13_zyklen.py |
| 2 | 98d-dismax-probe.py und test_dismax_probe.py | e32fcb3 | 98d-dismax-probe.py, test_dismax_probe.py |

## Was entstanden ist

- **94c-bodensatz-zyklen.sh:** Nachfolgefassung von 94b (voller Pfad im Kopf, NOT_DRIVEN, Bezug v1.2 A 103,9 / C 731,9 / Bodensatz 628,0 MB als Kommentar). Vorbedingung `entladeschalter-ist` gleich 120 (sonst 47, unlesbar 29). Genau ein `docker restart` vor Marke A, danach `zyklus 1`, `marke-c1`, `zyklus 2`, `marke-c2`; jeder Zyklus mit eigenem Ordner und Inhalt, WebDAV per `-K $CURLRC`, files:scan, Warten auf bewegtes embedded und Vorrat 0 innerhalb ZYKLUS_DECKEL (sonst 46, ohne Bewegung 33), Ruhezeit plus Karenz bis unloaded (sonst 31). Abtaster rss_sampler.sh über die ganze Reihe, Digest am Ende (keine Zahl 32). Ergebniszeilen `zyklus1-minus-a`, `zyklus2-minus-a`, `zyklus2-minus-c1`; beide Ordner werden danach gelöscht. Endmarke `block-durchgelaufen`, sonst 46.
- **95c-kaltstart.sh:** Nachfolgefassung von 95b. Schleife über höchstens KALTZYKLEN_MAX (1 bis 3, sonst 2): Neustart, Anmeldung, Bereitschaft an der Admin-Seite, sync, drop_caches auf dem Wirt, erste Suche der Nutzerroute mit `Bescheid Antrag`. Treffer > 0 ist Pflicht, sonst ganzer Zyklus neu; nach dem letzten Fehlschlag Arbeitsdatei und 48 unter der Pipeline. Zeilen `kaltzyklus <n> ms <x> code <c> treffer <t>`, `kaltstart-gueltig ja|nein`, `kaltstart-fenster <von> <bis>` (UTC) und eine warme Folgesuche. Das Wort der Modell-Route kommt in der Datei nicht vor.
- **98d-dismax-probe.py:** Index über read_side (öffnet per open_index), Plan über field_plan_for, Summe und Altplan über build_query. Formen summe, dismax_t00, dismax_t01, altplan; Klassen einwort, mehrwort, rueckfall, leer. Je Anfrage Treffer, Spitze (file_ids), Median-Latenz aus 5 Wiederholungen, overlap10/rbo10/rangverschiebung gegen altplan; am Ende Mediane je Kennzahl und Form, auch je Klasse. Treffermengengleichheit summe gegen beide dismax-Formen über zwei Differenzzählungen, ungleich ergibt `treffermenge-ungleich anfrage <nr> <form>` und 49. Keine Entscheidungsregel im Skript.
- **Tests:** test_v13_zyklen.py (18 Fälle, darunter boxlose Verweigerungsläufe für beide Skripte und KALTZYKLEN_MAX 0/4/10/drei), test_dismax_probe.py (21 Fälle: Treffermenge gleich, ganze-Zeile-dismax verliert Dokument 1, Rangumkehr Summe gegen dismax, Overlap/RBO per Handrechnung 1.45/1.9 und 0,874924, Rückfallklassen, Zeilenformen ohne Anfragetext, 49, 2 ohne Index, Stichprobe fest über Seed).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Shell-Variable `token` umbenannt**
- **Found during:** Task 1
- **Issue:** test_public_artifacts.py (Familie schluesselwort-mit-wert) meldete `${token:-}` und `Kein Passwort:` in beiden neuen Skripten; 94b und 95b stehen dafür auf der Ausnahmeliste, neue Dateien sollen dort nicht hin.
- **Fix:** Variable heißt `zeichen`, die Meldung ist umformuliert; keine Ausnahme ergänzt.
- **Commit:** 2afafb4

**2. [Rule 2 - Korrektheit] Endmarke in 94c und 95c**
- **Found during:** Task 1
- **Issue:** Ein unerwarteter Abbruch im tee-Block endet sonst mit 0 (Klasse L-03, deferred-items 22-02).
- **Fix:** `block-durchgelaufen` am Blockende, fehlt sie, endet 94c mit 46 und 95c mit 48. Boxlos bewiesen: ein Lauf, dessen `sudo` scheitert, endete mit 48.
- **Commit:** 2afafb4

**3. [Rule 2 - Korrektheit] 98d prüft die Treffermenge ohne Tiefendeckel**
- **Found during:** Task 2
- **Issue:** Ein Vergleich der Ranglisten bis Tiefe 100 hätte bei einem Wort mit Tausenden Treffern ungleiche Mengen gemeldet, die nur verschiedene Ränge sind.
- **Fix:** `same_hits` zählt `Must a, MustNot b` und umgekehrt; beide 0 heißt gleiche Menge.
- **Commit:** e32fcb3

### Weitere Anpassungen

- Passwortquelle: Umgebung zuerst, dann PWFILE (Plan nennt nur PWFILE); gleiche Reihenfolge wie 99d, damit das Ablaufskript es wie 96-volllauf.sh in die Umgebung legen kann.
- OUT-Vorgabe von 95c ist `$SKRIPTE/../rohdaten` wie bei 92d und 94c (der Plan schreibt "v13-rohdaten" für die Rohdaten des v13-Laufs).
- 95c: `loaded` vor der kalten Suche macht den Zyklus ungültig (Ersatz für den Log-Wachposten von 95b, dessen Muster die Datei nicht mehr tragen darf).
- 98d: `type:`-Zeilen zählen als rueckfall; fehlende Wortliste ergibt ebenfalls 2 (nichts gemessen). `carries_one_term` wird nicht importiert, die Einwortprüfung läuft über die bereinigte Zeile.

### TDD Gate Compliance

Beide Tasks tragen tdd="true"; Werkzeug und Wächter sind je Task in einem Commit gelandet (Muster aus 22-02), es gibt keine getrennten test(...)-Commits. Die Wächter liefen vor dem Commit grün; 94c und 95c zusätzlich je einmal voll gegen ein nachgestelltes sudo/curl im Scratchpad (94c bis 94C-BODENSATZ-ZYKLEN-FERTIG, 95c gültig nach Zyklus 2 und 48 nach drei leeren Zyklen).

## Verification

- `ruff check .`, `ruff format --check .` (144 Dateien), pyright latest 0 Fehler, vulture sauber; ruff check/format auch für das v13-Skriptverzeichnis grün
- pytest test_v13_zyklen.py, test_dismax_probe.py, test_measurement_scripts.py, test_public_artifacts.py: 505 passed
- `grep -c zyklus2-minus-c1` 94c >= 1, `exit 48` in 95c, `grep -ci diagnose` 95c = 0, `disjunction_max_query` 4, `open_index` 1, `= 49` 1
- `git diff --quiet HEAD -- docs/measurements/2026-09-v12-messung`: unverändert
- Alle drei Skripte mit Modus 100755 im Index; `sh -n` für beide Shell-Skripte grün
- Keine Änderung unter backend/src/findling oder php/, daher kein Baumhash-Bump. MESS-07 und MESS-09 bleiben offen. Kein Push, keine Box.

## Known Stubs

Keine.

## Threat Flags

Keine neuen Flächen außerhalb des Threat-Modells: T-22-10 (98d druckt nur Nummern, Klassen, Formnamen, file_ids, Kennzahlen; Test prüft Zeilenformen und Abwesenheit jedes Anfrageworts), T-22-11 (Passwort in Datei 600 und curl -K, nie Kommandozeile), T-22-12 (Test verbietet docker create/rm und 92e im laufenden Code, genau ein Neustart vor Marke A).

## Self-Check: PASSED

- FOUND: 94c-bodensatz-zyklen.sh, 95c-kaltstart.sh, 98d-dismax-probe.py, test_v13_zyklen.py, test_dismax_probe.py
- FOUND: 2afafb4, e32fcb3
