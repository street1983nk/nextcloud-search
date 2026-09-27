---
phase: 22-messanfahrt-bl-f03
plan: 13
subsystem: messung, doku
tags: [performance, v13, MESS-07, BL-F04, nachanfahrt, kaltstart, gap-closure]
requires:
  - "22-12: Owner-Abnahme mit Nachfreigabe (Weg b, Nebenlücken mit), Fix e23780c (Ausführungsbit rss_sampler.sh)"
provides:
  - "Kaltstartlatenz mit Trefferpflicht: 2.617 ms, 26 Treffer (Einwort-Begriff Bescheid, lasttest, Schalter 0)"
  - "abtastreihe-spitze-mb 1688 (94c), RAM je onnx-Kombination 542 bis 877 MB (B5)"
  - "docs/measurements/2026-09-v13-messung/rohdaten-nachanfahrt/ (27 Dateien), README 6.15 und E5-Nachtrag in 6.12"
affects:
  - "22-12 Task 3: MESS-07 Complete, Phase 22 Complete"
  - "Backlog: V-22-01 zeigt sich auch an der Auszugsroute api/snippets.py"
tech-stack:
  added: []
  patterns:
    - "Nachanfahrt mit eigenem OUT, Hauptrohdaten per git status --porcelain vor jedem Commit leer"
    - "Timer absolut, nach jedem Neustart erneut gesetzt und zurückgelesen"
key-files:
  created:
    - docs/measurements/2026-09-v13-messung/rohdaten-nachanfahrt/ (27 Dateien)
    - .planning/phases/22-messanfahrt-bl-f03/22-13-SUMMARY.md
  modified:
    - docs/measurements/2026-09-v13-messung/README.md
    - docs/performance.md
    - .planning/phases/22-messanfahrt-bl-f03/deferred-items.md
decisions:
  - "Owner-Freigabe zweistufig über den Koordinator ('machen wir wie die empfehlung', dann 'weiter'), im Freigabevermerk wörtlich festgehalten"
  - "92d gehört zum Aufbau der Nachanfahrt, weil der Snapshot das Abbild vom 10.09. trägt; gleiches Abbild wie die Hauptanfahrt, Baumhash-Beweis ja"
  - "E5-Urteil der Hauptanfahrt bleibt verfehlt; die Nachanfahrt hält E5 für den Einwortfall (datierter Nachtrag, kein Umschreiben)"
  - "Befund an der Auszugsroute (snippets.py ohne Einwortregel) nicht in Phase 22 gefixt, Backlog mit V-22-01"
metrics:
  duration: "ca. 45 min (Boxzeit 22 min)"
  completed: 2026-09-26
  tasks: 5
  files: 30
---

# Phase 22 Plan 13: Nachanfahrt Summary

Eine Nachanfahrt aus dem Korpus-Snapshot hat alle drei Lücken der Hauptanfahrt geschlossen: Kaltstart 2.617 ms mit 26 Treffern (Einwort-Begriff), Bodensatz-Spitze 1.688 MB, RAM je onnx-Kombination 542 bis 877 MB. Kosten 0,37 h / 0,0427 USD gegen den Deckel 4 h / 0,50 USD.

## Tasks

| Task | Inhalt | Ergebnis | Commit |
|---|---|---|---|
| 1 | Owner-Bestätigung | zweistufig über den Koordinator, wörtlich im Freigabevermerk; Zeile "Nachanfahrt freigegeben: 26.09.2026, Deckel 4 h / 0,50 USD" vor der ersten Boxminute gepusht | 0de526b |
| 2 | Aufbau, Timer, Bewaffnung | Blöcke 1 bis 13 ohne Abweichung am Produkt, LaunchTime 16:35:31Z, Timer absolut 20:20Z dreimal zurückgelesen, Markentor 0, 92d 0, Bestand 52.137 / 44 / 6, backendReachable true 16:44:51Z | ea32513 |
| 3 | Einwort-Begriff warm | `Bescheid` unter lasttest: 26 Treffer (2.537 / 1.676 ms) | ea32513 |
| 4 | Drei Blöcke | 95c 0 (2.617 ms, 26 Treffer, Gegenprobe 2 Zeilen), 94c 0 (Spitze 1688), b5 0 (8 bis 49 Abtastungen je Kombination) | ea32513 |
| 5 | Abbau, Kosten, Auswertung | destroy 0 ohne Ende-Snapshot, 0 Ressourcen über 17 Regionen außer dem Korpus-Snapshot, A-Record weg; 0,0427 USD; README 6.15, E5-Nachtrag, performance.md | ea32513, ec15950 |

## Zahlen

- **MESS-07 Kaltstart:** 2.617 ms, 26 Treffer, gültig im ersten Kaltzyklus. Bezug v1.2: 2.051 ms (zweiwortig, 0 Treffer).
- **94c:** `abtastreihe-spitze-mb 1688`; Kennzahlen reproduziert (A 108,2, C1 729,3, C2 756,7, Zyklus 2 minus C1 27,4 MB).
- **B5:** anon 542,3 / 877,3 / 542,2 / 877,4 MB (threads 1/1/2/2, batch 2/8/2/8); Speicher hängt an der Batchgröße, nicht an den Threads.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 92d im Aufbau ergänzt**
- **Found during:** Task 2
- **Issue:** Der Plan nennt Blöcke 1 bis 13, Markentor und Bestand. Der Snapshot trägt aber das Abbild vom 10.09., ohne Entladeschalter und ohne v1.3-Routen; 95c hätte ein anderes Produkt gemessen.
- **Fix:** 92d mit dem Abbild der Hauptanfahrt und `OUT=rohdaten-nachanfahrt`, unverändert gefahren (Rückgabe 0, Baumhash-Beweis ja, Bestandstor bestanden), danach Bewaffnung.
- **Commit:** ea32513

**2. [Rule 1 - Bug] `00-typwechsel.sh vorpruefung` schrieb in die Rohdaten der Hauptanfahrt**
- **Found during:** Task 2
- **Issue:** Ohne gesetztes `OUT` hängte das Werkzeug vier Zeilen an `rohdaten/00-typwechsel.txt`.
- **Fix:** Zeilen nach `rohdaten-nachanfahrt/00-typwechsel.txt` übernommen, die Hauptdatei mit `git checkout --` auf den committeten Stand zurückgesetzt, bevor irgendetwas committet war; `git status --porcelain` über `rohdaten/` vor jedem Commit leer. Werkzeug unverändert (gefahren, prüfsummengeschützt), Merkpunkt in deferred-items.
- **Commit:** ea32513

**3. [Rule 1 - Bug] Versionsangabe in IPv4-Form**
- **Found during:** Task 5, `test_public_artifacts.py`
- **Issue:** `version 33.0.8.2` in `03-aufbau.txt` traf die Familie `muster-der-umsetzung`.
- **Fix:** als `version 33.0.8` geschrieben wie in der Hauptanfahrt; Gate grün (55 passed).
- **Commit:** ea32513

### Kleinere Abweichungen ohne Folge

- Security Group und Schlüsselpaar tragen zusätzlich `purpose=findling-phase5`; destroy hat beide gelöscht und gegen die API zurückgelesen.
- Der Tag-Sweep lief über `describe-tags`, weil die Tagging-API für das Konto nicht freigegeben ist (AccessDenied).

## Befund ohne Abbruch

Im Kaltstart-Fenster stehen `/snippets innerMs 1510.5` und `/search innerMs 1505.4` gegen `ceilingMs 1500.0`. Die Auszugsroute (`api/snippets.py`) kennt die Einwortregel nicht und lädt bei Schalter 0 die Gewichte; die Warmsuche von 95c eine Sekunde danach endete mit 0 Treffern. Das ist die Ursache von V-22-01 an einer zweiten Route. Nicht gefixt, Backlog (deferred-items 22-13).

## Prüfsummen

Kein Werkzeug wurde geändert. Die gefahrenen Fassungen (92d, 92e, 90e, 91m, 94c, 95c, 00-wegwerf.sh, 00-typwechsel.sh) sind byteweise die bereits in `test_v13_gefahren.py` geschützten; die Wächter liefen grün (775 passed über die Mess-Suiten).

## Known Stubs

Keine.

## Self-Check: PASSED

- rohdaten-nachanfahrt/ mit 27 Dateien vorhanden, 95c-kaltstart-einwort.txt, 94c-bodensatz-zyklen.txt, b5-max-anon-*.txt, 93-kosten.txt, 07-abbau.txt
- Commits 0de526b, ea32513, ec15950 in `git log`
- `git status --porcelain -- docs/measurements/2026-09-v13-messung/rohdaten` leer
