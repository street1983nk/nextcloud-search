---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 10
subsystem: infra
tags: [hetzner-api, nextcloud-aio, harp, appapi, docker, containerd, cgroup-v2, acme, load-testing]

# Dependency graph
requires:
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: scripts/ops/hetzner_box.sh und scripts/ops/rss_sampler.sh aus Plan 05-05
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: HaRP-Installationsweg und mTLS-Korrektur aus Plan 05-01, DI-05-03
provides:
  - Eine laufende Mietbox mit Nextcloud AIO über HaRP, Datenverzeichnisse auf dem Volume, echtes Zertifikat, Oberfläche nur über SSH-Tunnel erreichbar
  - Die gemessene AIO-Grundlast ohne Findling, 290 MB im gleichzeitigen Höchststand, plus 55 MB für HaRP
  - docs/performance.md mit Umgebung, Methode, Grenzen und dem festgelegten Grenzwert von 2,0 GB
  - Rohdaten beider Messreihen unter docs/measurements/, unabhängig vom Fortbestand der Box
  - Ein Box-Werkzeug, das Bestand prüft, Schlüssel injiziert, die Firewall mitführt und beim Abbau nichts stehen lässt
affects: [05-12-findling-auf-der-box, 05-14-volllauf-und-abbau, store-aussage-peak-rss, arm-wiederholungslauf]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Verfügbarkeit vor Erzeugung prüfen, weil die Fehlermeldung der Fremd-API die falsche Ursache nennt"
    - "Architektur am Server-Typ ablesen statt sie danebenzuschreiben"
    - "Die Filterung sitzt außerhalb der Maschine, weil Docker an ufw vorbei in iptables schreibt"
    - "Jede erzeugte Ressource trägt dasselbe Label, und der Abbau räumt per Id und per Label"
    - "Rohdaten einer Messung ins Repository, weil die Maschine gelöscht wird und eine Zahl ohne Messreihe eine Behauptung ist"
    - "Die Weboberfläche eines Fremdprodukts über ihre eigene Schnittstelle bedienen statt über Klicks, damit Werksvorgaben nicht unbemerkt mitlaufen"

key-files:
  created:
    - docs/performance.md
    - docs/measurements/2026-09-03-grundlast-cpx22/README.md
    - docs/measurements/2026-09-03-grundlast-cpx22/*.csv
    - docs/measurements/2026-09-03-grundlast-cpx22/mit-harp/*.csv
  modified:
    - scripts/ops/hetzner_box.sh
    - backend/tests/test_ops_scripts.py
    - .planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md

key-decisions:
  - "Grenzwert für den Spitzenwert von anon liegt bei 2,0 GB und nicht bei der als Rahmen genannten Größenordnung von 2,5 GB, weil 2,5 GB neben einer Grundlast von 1,1 GB auf einer 4-GB-Box keine Zusage sondern eine Wette wären"
  - "Die Generalprobe läuft auf cpx22, weil alle vier ARM-Typen ohne Bestand waren; der ARM-Lauf wiederholt später alles und erbt keine einzige Zahl"
  - "Der Boxname trägt die Architektur nicht mehr, weil dasselbe Werkzeug beide Läufe mietet"
  - "Die Auswahl der optionalen AIO-Container läuft über die Schnittstelle der Oberfläche und nicht über Klicks, weil drei Container ab Werk angehakt sind und beim Klicken unbemerkt mitlaufen würden"
  - "Die Registrierung des Daemons durch AIO bleibt unangetastet: unter AIO ist Apache der Eingang und reicht /exapps an HaRP durch, die Korrektur aus DI-05-03 gilt nur für den compose-Aufbau"

patterns-established:
  - "Trockenlauf gegen einen lokalen Ersatz der Fremd-API vor jedem echten Aufruf, und danach ein Gegentest gegen die echte API, weil ein Ersatz das Antwortformat glättet"
  - "Sondierende Anfragen mit absichtlich ungültigen Feldern, um eine Ursache einzugrenzen, ohne etwas anzulegen"
  - "Messmethode und Grenzen werden vor den Zahlen geschrieben"

requirements-completed: [PKG-03]

# Metrics
duration: 8h 05m
completed: 2026-09-03
---

# Phase 5 Plan 10: Die Zielhardware steht und ihre Grundlast ist gemessen Summary

**Auf einer gemieteten 4-GB-Box läuft Nextcloud AIO 33.0.8 mit HaRP als einzigem optionalen Container, beide Datenverzeichnisse auf dem Volume, echtes Let's-Encrypt-Zertifikat, Oberfläche von außen unerreichbar, und ihre Grundlast ohne Findling steht mit 290 MB plus 55 MB für HaRP gemessen im Bericht, wo die Annahme vorher 700 bis 1100 MB geraten hatte.**

## Performance

- **Duration:** 8h 05m (mit zwei Unterbrechungen: Warten auf Freigaben und ein Sitzungslimit)
- **Started:** 2026-09-03T10:20:00Z
- **Completed:** 2026-09-03T18:25:00Z
- **Tasks:** 3 (zwei blockierende Checkpoints, ein Ausführungstask)
- **Files modified:** 18 Dateien, 4032 Zeilen hinzugefügt

## Accomplishments

- **Die Box läuft und ist belegbar richtig aufgesetzt.** Hetzner cpx22 in hel1, 50-GB-Volume, Ubuntu 24.04, cgroup v2, Nextcloud 33.0.8 aus All-in-One mit PostgreSQL 18.6. Docker-Datenverzeichnis und `NEXTCLOUD_DATADIR` liegen auf dem Volume, beide gesetzt bevor sie unveränderlich wurden. Die Systemplatte steht nach der ganzen Installation unverändert bei 1,9 GB, das Volume bei 4,1 GB.
- **Die Grundlast ist gemessen und die Annahme A2 damit erledigt.** Dreißig Minuten, sechs Sampler, 361 Messpunkte je Container, drei Phasen. Summe der `anon`-Werte im Mittel 224 MB, im gleichzeitigen Höchststand 290 MB, kein Speichertod, `memory.events` in allen Zählern auf null. HaRP wurde danach getrennt nachgemessen und trägt 55 MB bei.
- **Die Abschottung ist nicht behauptet, sondern von außen geprüft**, zweimal: vor dem Start und mit laufendem AIO. 443 wechselt von abgelehnt auf offen, 8080, 8443, 3478 und 9000 bleiben verworfen. Der Mastercontainer ist zusätzlich nur an `127.0.0.1` gebunden.
- **Vier Mängel am Box-Werkzeug behoben, die den ARM-Lauf teuer geworden wären**, dazu ein fünfter im Löschpfad. Alle mit einem neuen Fall im Textgate abgesichert, 19 Fälle grün.
- **Der Messbericht steht mit Methode und Grenzen vor den Zahlen**, in zwei sauber getrennten Spalten für die x86-Generalprobe und den ausstehenden ARM-Lauf.

## Task Commits

1. **Task 1: Die vier Voraussetzungen** - Checkpoint, kein Commit; `hetzner_box.sh prices` als Selbsttest bestanden
2. **Task 2a: Region und SSH-Schlüssel** - `94e7368` (fix)
3. **Task 2b: Bestandsprüfung und Bildauflösung** - `a238ad6` (fix)
4. **Task 2c: Adresskosten und leeres Löschergebnis** - `8257170` (fix)
5. **Task 2d: Methodenteil des Berichts** - `c9b95c2` (docs)
6. **Task 2e: DI-05-07 notiert** - `8f15df2` (docs)
7. **Task 2f: Umstellung auf cpx22** - `77cba86` (feat)
8. **Task 2g: Firewall anlegen und mitlöschen** - `59bd365` (feat)
9. **Task 2h: status gegen das echte Antwortformat** - `9b14cf9` (fix)
10. **Task 2i: Bericht auf zwei Läufe, containerd-Fund** - `ddd1f75` (docs)
11. **Task 2j: ARM als vollständiger Lauf, Zertifikat, Werksvorgaben** - `34abeca` (docs)
12. **Task 2k: Grundlast gemessen, Rohdaten im Repository** - `468f448` (feat)
13. **Task 3: HaRP zugeschaltet und gemessen** - `49d4d56` (feat)

## Files Created/Modified

- `docs/performance.md`: der Messbericht. Zwei Läufe mit getrennten Spalten, Umgebung beider Maschinen, Kosten aus der Konto-API mit Abfragezeitpunkt, die Reihenfolge der Einrichtung samt containerd-Falle, die Methode in den vier Sätzen aus dem Kopf des Samplers, sieben benannte Grenzen, der Grenzwert von 2,0 GB mit seiner Rechnung, die Grundlast und der Beitrag von HaRP. Fehlende Abschnitte sind als fehlend markiert.
- `docs/measurements/2026-09-03-grundlast-cpx22/`: 13 CSV-Dateien beider Messreihen und ein README, das Zeitraum, Maschine, Phasen und Spalten nennt.
- `scripts/ops/hetzner_box.sh`: Bestandsprüfung vor dem Erzeugen, Schlüsselinjektion mit Vorabprüfung im Konto, Bildauflösung über die am Typ abgelesene Architektur, Firewall als dritte Ressource mit Abbau per Id und per Label, Primär-IPv4 in der Kostenrechnung, `status` gegen das echte Antwortformat, Löschpfad ohne Falschmeldung.
- `backend/tests/test_ops_scripts.py`: sechs neue Fälle, die jede dieser Zusagen halten.
- `deferred-items.md`: DI-05-07.

## Decisions Made

- **Grenzwert 2,0 GB statt 2,5 GB.** D-03 stellte die Zahl ins Ermessen und nannte 2,5 GB als Größenordnung. Die Rechnung im Bericht: 4 GB Box, ungünstigste Findling-Lage 1,6 bis 1,7 GB, Grundlast damals veranschlagt bis 1,1 GB, dazu Luft für Seitencache und Kernel. Nach der Messung ist die Entscheidung noch bequemer als gedacht, weil die Grundlast bei 345 MB liegt.
- **Die Oberfläche von AIO über ihre eigene Schnittstelle bedient.** Domäne, Container-Auswahl, Start und das Zuschalten von HaRP liefen über dieselben Endpunkte, die auch die Oberfläche aufruft. Das war keine Bequemlichkeit: AIO hat Imaginary, Talk und Whiteboard ab Werk angehakt und eine Bürosuite vorausgewählt. Wer klickt und nur den gesuchten Haken setzt, misst gegen vier zusätzliche Container und merkt es nicht.
- **Der Boxname trägt die Architektur nicht mehr.** `findling-arm-loadtest` auf einer x86-Maschine ist eine Falle für jeden, der später die Konsole öffnet.
- **Die Registrierung des Daemons durch AIO bleibt, wie sie ist.** Siehe unter Issues.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] create sendete kein ssh_keys-Feld**
- **Found during:** Task 1, beim Lesen des Skripts vor dem ersten Aufruf
- **Issue:** Hetzner injiziert ausschließlich die Schlüssel, die im Erzeugungsaufruf benannt sind. Ein im Konto hinterlegter Schlüssel allein genügt nicht. Die Box wäre mit Zufalls-Root-Passwort hochgekommen, und der SSH-Tunnel aus Task 3 hätte kein Mittel zur Anmeldung gehabt. Nachträglich lässt sich das nicht beheben, ohne die Maschine neu aufzusetzen.
- **Fix:** `ssh_keys` im Erzeugungskörper, dazu eine Vorabprüfung im Konto, die vor dem ersten kostenpflichtigen Aufruf abbricht, wenn der Name dort nicht existiert.
- **Files modified:** scripts/ops/hetzner_box.sh, backend/tests/test_ops_scripts.py
- **Verification:** Erste Anmeldung an der echten Box gelang beim zweiten Versuch nach dem Start, ohne Passwort.
- **Committed in:** 94e7368

**2. [Rule 1 - Bug] Region nbg1 statt hel1**
- **Found during:** Task 1
- **Issue:** Das Skript stand auf `nbg1`, D-01 nennt `hel1`. Die Region einer Box ist nach dem Erzeugen unveränderlich.
- **Fix:** Konstante korrigiert, mit der Begründung im Kommentar.
- **Files modified:** scripts/ops/hetzner_box.sh, backend/tests/test_ops_scripts.py
- **Committed in:** 94e7368

**3. [Rule 2 - Missing Critical] Bestandsprüfung vor dem Erzeugen**
- **Found during:** Task 2, nach dem ersten fehlgeschlagenen `create`
- **Issue:** Die API antwortet auf einen ausverkauften Typ mit `invalid_input: unsupported location for server type`. Die Meldung nennt die Region und meint den Bestand. Sie erscheint für jede Region und sogar ohne Regionsangabe, also führt sie den Leser zuverlässig an die falsche Stelle. Sieben Sondierungen mit absichtlich ungültigen Feldern waren nötig, um Region, Bild, Architektur und Schreibrechte auszuschließen.
- **Fix:** `create` liest `locations[].available` am Server-Typ und bricht mit einer Aussage ab, die den Bestand nennt und den Beobachtungsbefehl dazu. `prices` bekam eine Spalte `in stock`.
- **Files modified:** scripts/ops/hetzner_box.sh, backend/tests/test_ops_scripts.py
- **Verification:** Gegen die echte API belegt, als alle vier ARM-Typen ausverkauft waren, und gegen den lokalen Ersatz im vorrätigen Fall.
- **Committed in:** a238ad6

**4. [Rule 1 - Bug] Bildname ist zweideutig**
- **Found during:** Task 2
- **Issue:** `ubuntu-24.04` existiert je einmal für x86 und arm. Der blanke Name überlässt die Wahl der API, und die falsche Hälfte bootet auf der Zielmaschine nicht.
- **Fix:** Auflösung über Name und Architektur, wobei die Architektur am Server-Typ abgelesen wird. Ein Wechsel des Typs ist damit ein Wort und kann kein unpassendes Bild hinterlassen.
- **Files modified:** scripts/ops/hetzner_box.sh
- **Committed in:** a238ad6, 77cba86

**5. [Rule 1 - Bug] status rechnete die Primär-IPv4 nicht mit**
- **Found during:** Task 2, beim Zusammenstellen der Kostenzeile
- **Issue:** Die öffentliche Adresse steht seit 2024 als eigener Posten auf der Rechnung. Gegen eine Box für gut einen Cent je Stunde macht sie rund acht Prozent aus, der Bericht hätte also zu niedrige Kosten genannt.
- **Fix:** Der Preis wird aus `/pricing` gelesen und mitgerechnet, wenn die Box tatsächlich eine Adresse hat.
- **Files modified:** scripts/ops/hetzner_box.sh
- **Committed in:** 8257170

**6. [Rule 1 - Bug] Ein leeres Löschergebnis galt als Fehlschlag**
- **Found during:** Task 2, im Trockenlauf gegen den lokalen Ersatz
- **Issue:** `DELETE` auf ein Volume antwortet mit 204 ohne Körper. Der allgemeine Leser des Skripts wertet eine leere Antwort als nicht angekommene Anfrage, also hätte jeder saubere Abbau eine Zeile gemeldet, die nach verlorenem Volume klingt. Genau dort muss man der Ausgabe glauben können, sonst gewöhnt sich ein Betreiber ab, sie zu lesen.
- **Fix:** Eigener Leser für die Löschpfade, der eine leere Antwort als Erfolg wertet.
- **Files modified:** scripts/ops/hetzner_box.sh, backend/tests/test_ops_scripts.py
- **Committed in:** 8257170

**7. [Rule 2 - Missing Critical] Firewall außerhalb der Box, und ihr Abbau**
- **Found during:** Task 2
- **Issue:** Der Plan verlangt, dass die AIO-Oberfläche von außen nicht erreichbar ist. Eine `ufw`-Regel hätte das nicht geleistet, weil Docker seine veröffentlichten Ports unmittelbar in iptables schreibt und an `ufw` vorbeigeht: der Port wäre offen gewesen, während `ufw` ihn als geschlossen meldet. Die dann angelegte Firewall des Anbieters war ihrerseits eine dritte Ressource, die `destroy` nicht kannte, und weil sie nichts kostet, ist sie genau die, die stehen bleibt (T-05-39).
- **Fix:** `create` legt die Firewall mit demselben Label an und schreibt ihre Id in die Zustandsdatei, `destroy` löscht sie nach dem Server und räumt ohne Zustandsdatei alle Firewalls mit dem Label ab. Beide Wege gegen den lokalen Ersatz durchgespielt.
- **Files modified:** scripts/ops/hetzner_box.sh, backend/tests/test_ops_scripts.py
- **Verification:** Portprobe von einer fremden Adresse, zweimal, siehe Bericht.
- **Committed in:** 59bd365

**8. [Rule 1 - Bug] status las die API zeilenweise**
- **Found during:** Task 2, beim ersten Aufruf gegen die echte API
- **Issue:** Die drei Antworten wurden als drei Zeilen an einen Leser übergeben. Hetzner verteilt sein JSON über mehrere Zeilen, der Leser bekam also eine öffnende Klammer und brach ab. Gegen den einzeiligen Ersatz aus 05-05 sah das wie funktionierend aus, und betroffen war ausgerechnet der Befehl, der die Kostenzeile des Berichts liefert.
- **Fix:** Übergabe als ein Array, das sich um Leerraum nicht kümmert.
- **Files modified:** scripts/ops/hetzner_box.sh, backend/tests/test_ops_scripts.py
- **Verification:** Gegen die echte API, Kostenzeile stimmt mit `/pricing` überein.
- **Committed in:** 9b14cf9

**9. [Rule 2 - Missing Critical] Docker 29 legt Abbilder nicht im data-root ab**
- **Found during:** Task 2, unmittelbar nach dem ersten `docker pull`
- **Issue:** `/etc/docker/daemon.json` mit `data-root` stand vor der Installation, wie der Plan es verlangt. Trotzdem landete das erste Abbild auf der Systemplatte: seit Docker 29 legt der containerd-Snapshotter die Abbilder ab, und der hat sein eigenes Wurzelverzeichnis unter `/var/lib/containerd`. `docker info` meldete dabei unbeirrt das Volume. Auf der CAX11 mit 40 GB Systemplatte hätten die Abbilder von AIO, Postgres, Apache, HaRP und Findling die Platte im Volllauf ernsthaft gefüllt, und das wäre als Fehler von Findling erschienen (T-05-43).
- **Fix:** `root` in `/etc/containerd/config.toml` auf das Volume, Bestand umgezogen, Dienste neu gestartet.
- **Files modified:** keine Repo-Datei, Zustand der Box; dokumentiert in docs/performance.md
- **Verification:** Gegenprobe mit einem frischen Abbild: Systemplatte wächst um 0 KB, Volume um 104 KB. Nach der ganzen AIO-Installation steht die Systemplatte unverändert bei 1,9 GB.
- **Committed in:** ddd1f75 (als Abschnitt im Bericht)

**10. [Rule 2 - Missing Critical] Drei optionale Container sind ab Werk angehakt**
- **Found during:** Task 2, vor dem ersten Start der Container
- **Issue:** AIO liefert Imaginary, Talk und Whiteboard angehakt aus und hat eine Bürosuite vorausgewählt. Die Grundlast, gegen die der ganze Bericht misst, wäre um vier Container zu hoch gewesen, und niemand hätte es der Zahl angesehen.
- **Fix:** Alle vier abgewählt, bevor die Container zum ersten Mal starteten. Die Konfiguration trägt danach keinen Schalter auf `true`, später genau einen für HaRP.
- **Files modified:** keine Repo-Datei, Zustand der Box; dokumentiert in docs/performance.md
- **Verification:** `docker ps` zeigt vor der HaRP-Aktivierung genau sechs Container, danach genau sieben.
- **Committed in:** 34abeca

---

**Total deviations:** 10 auto-fixed (5 Bug, 5 fehlende kritische Funktion)
**Impact on plan:** Keine Ausweitung des Umfangs. Neun der zehn betreffen unmittelbar die Abnahmekriterien dieses Plans, die zehnte den Grenzwert der Messung. Kein neues Paket: die Box bezieht Docker aus dem offiziellen Paketspeicher mit geprüftem Schlüssel und die Abbilder aus den Nextcloud-Kanälen (T-05-SC gehalten).

## Issues Encountered

- **Alle vier ARM-Typen waren ohne Bestand.** Der Plan steht auf einer CAX11, und am Tag der Ausführung war keine ARM-Maschine des Anbieters in einer der drei europäischen Regionen zu mieten; auch die günstigen x86-Typen `cx23` bis `cx53` waren ausverkauft. Nach Vorlage der drei Optionen hat der Owner beides entschieden: die Generalprobe läuft sofort auf cpx22, der vollständige Lauf wird auf ARM wiederholt. Der Bericht führt beide Reihen getrennt und benennt, dass die x86-Zahlen keine einzige Zeile der Store-Aussage tragen.
- **Die Anmeldung an der AIO-Oberfläche mit der Passphrase ist gesperrt, solange Nextcloud läuft.** `LoginController::TryLogin` verweist auf `GET /api/auth/getlogin?token=...`, geprüft wird gegen `AIO_TOKEN` aus der AIO-Konfiguration, den AIO bei jedem Containerstart neu würfelt. Der Knopf in der Nextcloud-Verwaltung baut seine Adresse aus `AIO_URL`, und die steht hier auf `localhost:8080`, zeigt über den Tunnel also zufällig richtig. Für die Sichtprüfung wurde der Token gelesen und eine fertige Adresse übergeben.
- **DI-05-03 ist für den AIO-Lauf beantwortet, und zwar anders als erwartet.** AppAPI hat den Daemon `harp_aio` selbst registriert, mit `NC Url = https://loadtest.infranode.dev`, also mit der Adresse von Nextcloud. Nach dem compose-Muster wäre das genau der Fehler, der zu `heartbeat check failed` führt. Unter AIO ist der Eingang aber Apache und nicht HaRP, und Apache reicht `/exapps` durch. Nachgewiesen vor der ersten ExApp: `/exapps/` antwortet mit einem schlichten `404 Not Found` in `text/plain`, ein gewöhnlicher Fehlpfad mit der HTML-Seite von Nextcloud. Plan 05-12 darf diese Registrierung deshalb **nicht** nach dem compose-Muster ändern.
- **Die Vorabrechnung der Grundlast war um Faktor drei bis vier zu hoch**, gemessen am selben Maßstab wie das Findling-Budget. Mit `memory.current` gerechnet wären es 1353 MB statt 290 MB. Der Unterschied ist Dateicache und zurückforderbar; beide Zahlen stehen mit dieser Begründung im Bericht, damit niemand später zwei Maßstäbe vergleicht.
- **Zwei Unterbrechungen der Ausführung**, eine durch das Warten auf Token, Schlüssel und A-Record, eine durch ein Sitzungslimit während des Container-Starts. Die Box lief in beiden Fällen weiter, der Ist-Zustand wurde danach per SSH gegen den Plan abgeglichen.

## User Setup Required

Keine für diesen Plan. Für die folgenden Pläne bleibt bestehen: `HCLOUD_TOKEN` liegt in `C:\Users\Student\.findling-hcloud.env` und wird bis zum Abbau in 05-14 gebraucht, der A-Record `loadtest.infranode.dev` verwaltet der Orchestrator, und die Box kostet weiter Geld.

## Next Phase Readiness

- **Bereit für 05-12.** Die Box steht mit AIO über HaRP, der Daemon `harp_aio` ist registriert, `/exapps` wird durchgereicht, das Volume hat 43 GB frei, und `NEXTCLOUD_MOUNT` zeigt auf `/mnt/HC_Volume_106785477/corpus`, wo der Lastkorpus hingehört. Der Volllauf-Seed ist `phase5-full`.
- **Zugang:** Box `164459278` unter `62.238.114.125`, SSH als root mit dem Schlüssel `khaled-windows-ed25519`. Die AIO-Oberfläche nur über einen Tunnel; der `AIO_TOKEN` für die Anmeldung ändert sich bei jedem Containerstart und ist mit `docker inspect nextcloud-aio-nextcloud` auslesbar. Nextcloud-Admin ist `admin`, das Passwort steht in den AIO-Secrets und nicht in dieser Datei.
- **Offen und ausdrücklich nicht hier entschieden:** wann der ARM-Lauf startet. Der Bestand wird beobachtet, und `hetzner_box.sh` braucht dafür ein Wort Änderung an `SERVER_TYPE`, weil die Architektur an der API hängt.
- **Pflicht am Ende, aus D-01 und T-05-39:** `hetzner_box.sh destroy` räumt Box, Volume und Firewall ab und prüft alle drei gegen die API. Bis dahin läuft die Uhr; nach acht Stunden stehen 0,10 EUR auf der Rechnung.

## Self-Check: PASSED

| Prüfung | Ergebnis |
|---|---|
| docs/performance.md | vorhanden, 554 Zeilen |
| docs/measurements/2026-09-03-grundlast-cpx22/ | 13 CSV plus README |
| Commits 94e7368, a238ad6, 8257170, c9b95c2, 8f15df2, 77cba86, 59bd365, 9b14cf9, ddd1f75, 34abeca, 468f448, 49d4d56 | alle im Log |
| `uv run python -m pytest tests/test_ops_scripts.py` | 19 bestanden |
| `sh -n scripts/ops/hetzner_box.sh` | fehlerfrei |
| Gedankenstriche in docs/performance.md und README | keine |
| HCLOUD_TOKEN im Arbeitsbaum | nirgends, per Volltextsuche geprüft |
| `git status --porcelain` | leer |
| Box, Volume und Firewall tragen purpose=findling-phase5 | ja, per `status` geprüft |

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-03*
