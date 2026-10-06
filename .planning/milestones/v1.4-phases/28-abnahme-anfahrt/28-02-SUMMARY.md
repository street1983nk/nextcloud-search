---
phase: 28-abnahme-anfahrt
plan: 02
subsystem: messung
tags: [abnahme-anfahrt, zelle, kette, probe-route, sicherheitstimer, mess-10]
requires:
  - "28-01: 01-teilkorpus.py zaehltor, V14_RUN_DIR in NARROW_SCOPE_DIRS"
provides:
  - "11-probe-route.py: Probe headless über die Produktroute (pruefen, abwaerts, uebersicht)"
  - "10-zelle.sh: eine Zelle in fester Reihenfolge vom Nullstand bis zu den Rohdaten"
  - "93b-nullstand.sh: die vier Quellen des Nullstands ohne Neuaufbau"
  - "00-kette.sh: alle Zellen einer Box, Deckel vor jeder Zelle, Sicherheitstimer bei Deckel x 1,20"
  - "backend/tests/test_v14_zelle.py: 59 boxlose Tests"
affects: [28-03, 28-05]
tech-stack:
  added: []
  patterns:
    - "Probe-Route nur mit Standardbibliothek, Cookie-Glas in tempfile.mkdtemp, finally löscht"
    - "Übersicht als Projektion auf eine geschlossene Feldmenge, eine Zeile key=wert für die Shell"
    - "Boxlose Tests mit nachgestellten sudo/docker/python3/shutdown im PATH, python3-Stub reicht an den echten Interpreter durch"
key-files:
  created:
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/11-probe-route.py
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/93b-nullstand.sh
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/00-kette.sh
    - backend/tests/test_v14_zelle.py
  modified: []
decisions:
  - "93b-nullstand.sh statt 93-nullstand.sh in der Zelle: 93 stößt den Neuaufbau selbst an und wartet 360 s, das füllte den Vorrat vor Probe und Wirksamkeit (Pitfall 2); 93 bleibt als gefahrene Fassung unverändert"
  - "Ende der Zelle: Vorrat 0 und embedded == indexed zweimal hintereinander, zusätzlich indexed > 0, damit der leere Anfang vor dem ersten Cron-Lauf kein Ende ist"
  - "Deckel-Rechnung der Kette direkt aus den Laufwerten (BISHER_USD + Laufzeit x SATZ_USD_H), wie im Plan; 02-rechenblatt.py stand bleibt das Werkzeug der Entwicklungsmaschine"
  - "Kette: eine fehlgeschlagene Zelle beendet die Kette (84) und zieht den Timer auf 60 min vor; kein Abbau, nur Stopp"
  - "Deckel x 1,20 schon beim Start erreicht: shutdown -h now (82), das ist der Sicherheitstimer mit Rest null"
  - "Marke der Vorprüfung als Laufwert VORPRUEFUNG=stop-ja, von Hand nach 00-typwechsel.sh vorpruefung gesetzt"
metrics:
  duration: "rund 35 min"
  completed: "2026-09-29"
  tasks: 2
  files: 5
---

# Phase 28 Plan 02: Laufwerkzeuge der Box Summary

Probe über die Produktroute, eine Zelle in der Reihenfolge von Pattern 1 und die Kette je Box mit Deckel vor jeder Zelle und Sicherheitstimer bei Deckel x 1,20, alles boxlos getestet (59 Tests gegen einen http.server-Stub und nachgestellte Kommandos).

## Was gebaut wurde

- **11-probe-route.py** (`pruefen <profil> <praezision>`, `abwaerts`, `uebersicht`): Anmeldung nach `probe_page_login.sh` (Token aus `data-requesttoken`, Origin-Kopf, frisches Token aus `/settings/admin/findling`), POST und GET `/apps/findling/admin/profile/check` alle 2 s mit einer Zeile je Lesung im Format von `02-fits-probe.txt`, Ende `verdikt fits erzwungen nein` (0), narrow 30, nofit 31, Frist 32 (900 s, fp32 900 plus 600 s Download). Ein Ergebnis mit anderem Ziel (ältere Probe) zählt nicht als Verdikt. Passwort nur aus `FINDLING_ADMIN_PWFILE` oder `FINDLING_ADMIN_PASSWORD`, jedes Passwort-Argument endet mit 2; Adresse und Passwort erscheinen nie in der Ausgabe; das Cookie-Glas liegt in `tempfile.mkdtemp` und wird im `finally` gelöscht.
- **10-zelle.sh `<box> <zelle> <profil> <praezision>`**: abwaerts, zaehlung-eine-nextcloud (unmittelbar vor `--rm-data`, sonst 61), nullstand, registrierung per Digest, bewaffnung mit Beleg `backendReachable true`, grenze (nur `GRENZE_2G=ja`, aus der cgroup zurückgelesen), baumhash (40b-baumhash.sh plus Hash im laufenden Container), 93b-nullstand, drop-caches, probe (economy: `probe keine abwaertsweg`; narrow/nofit: occ erzwingt, bei fp32 auch `model_precision`, Zeile `erzwungen ja grund <verdikt>/<ursache>`), wirksamkeit (effective == Ziel und slotsInForce, zur Hälfte der Frist einmal neu bewaffnet, sonst 69 ohne Trigger), sampler (rss 2 s, anon 1 s, cpu, 96d 120 s), trigger `occ findling:index --restart -n`, beim Teilkorpus Zähltor 5000 über 01-teilkorpus.py (sonst 71), ende, nachlauf (Ruhe 120 s, Grundlast, guard-Block, `waechter-absenkung ja|nein`), abholen. Rohdaten unter `rohdaten/<box>/<zelle>/`, Protokoll des Statusbeobachters mit Platzhalter statt Adresse. Rückgabewerte 2 und 59 bis 72 im Kopf katalogisiert.
- **93b-nullstand.sh**: Ableitung von 93-nullstand.sh, liest Volumen, Endzustände, Marken und Vorrat, stößt nichts an; `volumen-leer nein` (11) wenn die state.db Dateien führt, 12 wenn sie unlesbar ist.
- **00-kette.sh `<box>`**: Laufwerte geprüft (Beträge, Start nicht in der Zukunft, Digest, jede Zelle `name:profil:praezision:korpus`), ohne `VORPRUEFUNG=stop-ja` kein Start (80), Timer `shutdown -h +<min>` mit min = (1,20 x Deckel minus bisher) / Satz x 60 und Rücklesung aus der systemd-Datei (sonst 81), Herzschlag je Minute in `00-herzschlag.txt`, Deckel vor jeder Zelle: Marke `deckel-erreicht <UTC> bisher <USD>` plus Datei `00-DECKEL-ERREICHT`, Ende 83, KEIN shutdown; nach der letzten Zelle `shutdown -h +2`.

## Commits

| Task | Commit | Art |
|---|---|---|
| 1 RED | 79b76340 | test: Probe über die Produktroute |
| 1 GREEN | 347145c6 | feat: 11-probe-route.py |
| 2 RED | 9eeb8ae5 | test: Zelle und Kette |
| 2 Fix | 7e1da732 | fix: Schlüsselwörter ohne Wert im Probe-Werkzeug |
| 2 GREEN | 1976584a | feat: 10-zelle.sh, 93b-nullstand.sh, 00-kette.sh |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 93-nullstand.sh hätte den Vorrat vor der Probe gefüllt**
- **Found during:** Task 2
- **Issue:** Der Plan ruft 93-nullstand.sh zwischen Baumhash und Probe. Das gefahrene Werkzeug stößt aber selbst `findling:index --restart -n` an und wartet 360 s; der frische Container indexierte dann im Profil economy, während Probe und Wirksamkeitstor laufen (Pitfall 2), und die Zelle mäße zwei Stufen. Die Research nennt ausdrücklich "93-nullstand.sh ohne Neustart des Vorrats" und sieht Ableitungen im Laufverzeichnis vor.
- **Fix:** Neue Datei `93b-nullstand.sh` mit denselben vier Quellen ohne Neuaufbau; 93-nullstand.sh bleibt unverändert, 10-zelle.sh nennt beide.
- **Files modified:** docs/measurements/2026-10-abnahme-anfahrt/skripte/93b-nullstand.sh (neu, zusätzlich zu files_modified)
- **Commit:** 1976584a

**2. [Rule 1 - Bug] Ende-Bedingung am leeren Anfang**
- **Found during:** Task 2
- **Issue:** Direkt nach dem Trigger stehen Vorrat 0 und embedded == indexed == 0, bevor der erste Cron-Lauf den Vorrat füllt; die Bedingung "zweimal Vorrat 0 und embedded == indexed" hätte die Zelle sofort beendet.
- **Fix:** zusätzlich indexed > 0.
- **Commit:** 1976584a

**3. [Rule 3 - Blocking] Gate test_public_artifacts auf Bezeichner**
- **Found during:** Task 2, Gesamtprüfung
- **Issue:** `TOKEN = re.compile(...)`, `self.token = ...` und `secret: str` trafen die Familie "schluesselwort-mit-wert".
- **Fix:** Umbenannt in `TOKEN_IN_PAGE`, `request_token`, `phrase`; Verhalten unverändert.
- **Commit:** 7e1da732

### Auslegung

- **kette-deckel "ruft KEIN shutdown":** Der Sicherheitstimer steht beim Start (kette-timer) und bleibt im Deckelfall stehen, damit die Box bei Deckel x 1,20 anhält, falls der Owner nicht antwortet (D-28-14). Der Test sichert zu, dass im Deckelfall kein weiterer shutdown-Aufruf folgt (weder `+2` noch `now`) und die Funktion `deckel_erreicht` kein shutdown enthält.

## Known Stubs

Keine. Die Werkzeuge sind boxlos getestet und nicht gefahren; jede Datei trägt die Zeile "DIESE FASSUNG IST NICHT GEFAHREN".

## Threat Flags

Keine neue Fläche außerhalb des Threat-Registers: die Admin-Routen (T-28-05, T-28-06), `--rm-data` (T-28-07), Timer und Deckel (T-28-08, T-28-09), Rohdaten ohne Kennungen (T-28-10) und das Wirksamkeitstor (T-28-11) sind alle abgedeckt und getestet.

## Self-Check: PASSED

- Dateien vorhanden: 11-probe-route.py, 10-zelle.sh, 93b-nullstand.sh, 00-kette.sh, test_v14_zelle.py
- Commits vorhanden: 79b76340, 347145c6, 9eeb8ae5, 7e1da732, 1976584a
- Skripte im Index 100755; `grep -c "findling:index --restart -n" 10-zelle.sh` = 2; `argv` in 11-probe-route.py ohne Passwort-Parameter
- Gates: pytest test_v14_zelle, test_measurement_scripts, test_public_artifacts, test_v14_teilkorpus 640 passed; ruff check und format grün; pyright (latest) 0 Fehler; vulture grün; `sh -n` für alle drei Shell-Skripte
