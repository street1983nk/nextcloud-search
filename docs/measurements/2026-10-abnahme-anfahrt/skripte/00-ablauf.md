# Der Ablauf der Abnahme-Anfahrt der Phase 28, mit den Erwartungen je Zelle

Diese Datei ist der Ablaufplan des Laufs im Verzeichnis
`docs/measurements/2026-10-abnahme-anfahrt/`. Sie beschreibt den Lauf, **bevor**
er stattfindet: jede Zelle hat unten ihre Rechnung, ihre Slotzahl, ihre
Probe-Erwartung und ihren Lauf-Planwert, und der Commit dieser Datei ist ihr
Zeitstempel (T-28-04). Nach der Messung werden die Erwartungen nicht
umformuliert; die Urteile lauten nur `getragen`, `nicht getragen` oder
`nicht entschieden`.

**Zur Schreibweise.** Die Abschnittsüberschriften stehen ohne Umlaute, weil
Prüfungen und Verweise auf sie zeigen. Der Fließtext benutzt echte Umlaute. Die
Skripte dieses Verzeichnisses schreiben Kommentare und Protokollzeilen in ASCII,
weil sie auf einer Box laufen, deren Gebietsschema niemand garantiert.

**Zur Geltung.** Der Ordnername `2026-10-abnahme-anfahrt` ist fest, auch wenn
der erste Boxstart noch im September läge; die Tests der Pläne 28-01 bis 28-03
hängen an ihm. Ohne die datierte Freigabe des Deckels durch den Owner startet
keine Box (D-28-01, SC1).

---

## 1. Die Grundlagen dieser Datei

| Grundlage | Werkzeug | Stand |
|---|---|---|
| Teilkorpus, feste Regel nach D-28-09 | `skripte/01-teilkorpus.py auswahl` | 5.000 Dateien, 2.691 OCR-Seiten, offline nachgerechnet |
| Rechenblatt und Deckel nach D-28-01 und D-28-11 | `skripte/02-rechenblatt.py deckel` | Sätze vom 29.09.2026 |
| Rechnung je Zelle nach D-28-08 | `skripte/12-slotkosten.py rechnung` | Posten aus `findling.config` und `findling.probe` |
| Kosten je Slot aus der Messreihe | `skripte/12-slotkosten.py slots` | Maß von B2, 235 MiB |

**Das Teilkorpus.** Die ersten N Dateien je Kategorie des Snapshot-Korpus in der
Reihenfolge von `build_load_corpus.py` (Seed `phase5-full`, Bereiche aus
`allocate(50000)`):

| Kategorie | im Teilkorpus | Präfixe |
|---|---:|---|
| scan_single | 1.800 | 00001 bis 01800 |
| scan_multi | 100 (791 Seiten) | 09917 bis 10016, alle |
| text_pdf | 1.500 | 10017 bis 11516 |
| ooxml | 900 | 32553 bis 33452 |
| opendocument | 400 | 42569 bis 42968 |
| plain_text | 200 | 47577 bis 47776 |
| image | 100 | 49881 bis 49980, alle |
| oversize | 0 | ausgelassen |
| **Summe** | **5.000** | 2.000 OCR-Dateien, 2.691 OCR-Seiten |

Auf der Box legt `01-teilkorpus.py hardlinks` den Ordner `teilkorpus/` im Home
des Kontos `lasttest` an (Hardlinks, gleiche Bytes, gleicher Eigentümer),
`01-teilkorpus.py liste` schreibt `name,bytes,sha256` der 5.000 Dateien und die
Listen-Prüfsumme als Rohdatei, und nach dem Crawl muss `01-teilkorpus.py
zaehltor` genau 5.000 bestätigen, sonst endet die Zelle. Der Ordner entsteht auf
der ARM-Platte erst NACH der Vollzelle, sonst zählt der Vollkorpus 5.000
Duplikate mit; auf der x86-Platte gleich beim Aufbau.

---

## 2. Die Zellen in ihrer Reihenfolge

Reihenfolge nach 28-RESEARCH.md, Pattern 2: Referenzbox zuerst, danach die
ARM-Baseline, dann eine x86-Instanz, die per Typwechsel von 4 auf 32 Kerne
wächst. Innerhalb einer Box: Sparsam, Standard, Leistung, fp32 zuletzt; danach
geht `model_precision` über den Abwärtsweg zurück auf int8. Alles seriell
(vCPU-Quota 32, D-26-10).

Spalten: **Slots** ist die Slotzahl, die die Formel (`findling.profile.ocr_slots`,
MemAvailable als MemTotal minus 1 GiB) gewährt und die Probe vorschlagen wird.
**Probe** ist das erwartete Verdikt der Probe über die Produktroute; bei Sparsam
läuft keine Probe, weil Sparsam der Abwärtsweg ist. **Rechnung** ist
Rechnung_anon aus `12-slotkosten.py rechnung` in MiB, **Grenze** das 1,10-fache
davon. **Plan** ist der Lauf-Planwert des Rechenblatts ohne Zellen-Overhead.

| Nr | Box | Zelle | Profil | Präzision | Slots | Probe | Rechnung MiB | Grenze MiB | Plan |
|---:|---|---|---|---|---:|---|---:|---:|---:|
| 1 | m7g.large | S-voll (52.111 Dokumente) | Sparsam | int8 | 1 | keine Probe | 1.492,5 | 1.641,8 | 21:15 |
| | m7g.large | 94c, Rückkehr zur Grundlast | Sparsam | int8 | | keine Probe | Store-Zahl, Abschnitt 3 | | 0:15 |
| | m7g.large | Teilkorpus einrichten, Zähltor | | | | | | | 0:20 |
| 2 | m7g.large | Anker S-T (D-28-11) | Sparsam | int8 | 1 | keine Probe | 1.492,5 | 1.641,8 | 3:50 |
| 3 | m7g.large | St-T | Standard | int8 | 1 | nofit oder narrow, dann erzwungen | 1.593,9 | 1.753,3 | 3:20 |
| 4 | m7g.large | L-T | Leistung | int8 | 1 | nofit oder narrow, dann erzwungen | 1.743,0 | 1.917,3 | 3:20 |
| 5 | m7g.4xlarge | S-T | Sparsam | int8 | 1 | keine Probe | 1.492,5 | 1.641,8 | 3:50 |
| 6 | m7g.4xlarge | St-T | Standard | int8 | 4 | fits | 2.298,9 | 2.528,8 | 1:00 |
| 7 | m7g.4xlarge | L-T | Leistung | int8 | 15 | fits | 5.033,0 | 5.536,3 | 0:45 |
| | c7a.xlarge | Tor: amd64-Abbilder, PostgreSQL-Start, REINDEX | | | | | | | 2:00 |
| 8 | c7a.xlarge | S-T | Sparsam | int8 | 1 | keine Probe | 1.492,5 | 1.641,8 | 3:50 |
| 9 | c7a.xlarge | St-T | Standard | int8 | 1 | fits | 1.593,9 | 1.753,3 | 3:20 |
| 10 | c7a.xlarge | L-T | Leistung | int8 | 3 | fits | 2.213,0 | 2.434,3 | 1:15 |
| 11 | c7a.xlarge | St-fp32-T | Standard | fp32 | 1 | fits | 1.960,9 | 2.157,0 | 3:30 |
| 12 | c7a.2xlarge | S-T | Sparsam | int8 | 1 | keine Probe | 1.492,5 | 1.641,8 | 3:50 |
| 13 | c7a.2xlarge | St-T | Standard | int8 | 3 | fits | 2.063,9 | 2.270,3 | 1:15 |
| 14 | c7a.2xlarge | L-T | Leistung | int8 | 7 | fits | 3.153,0 | 3.468,3 | 0:45 |
| 15 | c7a.4xlarge | S-T | Sparsam | int8 | 1 | keine Probe | 1.492,5 | 1.641,8 | 3:50 |
| 16 | c7a.4xlarge | St-T | Standard | int8 | 4 | fits | 2.298,9 | 2.528,8 | 1:00 |
| 17 | c7a.4xlarge | L-T | Leistung | int8 | 15 | fits | 5.033,0 | 5.536,3 | 0:45 |
| 18 | c7a.4xlarge | St-fp32-T | Standard | fp32 | 4 | fits | 2.665,9 | 2.932,5 | 1:30 |
| 19 | c7a.8xlarge | S-T | Sparsam | int8 | 1 | keine Probe | 1.492,5 | 1.641,8 | 3:50 |
| 20 | c7a.8xlarge | St-T | Standard | int8 | 4 | fits | 2.298,9 | 2.528,8 | 1:00 |
| 21 | c7a.8xlarge | L-T | Leistung | int8 | 16 | fits | 5.268,0 | 5.794,8 | 0:45 |

Das sind 21 Messzellen: 4 auf m7g.large (S-voll, Anker, St-T, L-T), 3 auf
m7g.4xlarge, 4 auf c7a.xlarge, 3 auf c7a.2xlarge, 4 auf c7a.4xlarge und 3 auf
c7a.8xlarge, dazu das Machbarkeitstor auf c7a.xlarge und 94c nach der Vollzelle.

**Warum die Probe auf m7g.large nicht passen sollte.** Die Referenzbox läuft mit
harter Grenze 2g (Block 12). Nach dem Nullstand sind Schneider und Gewichte
nicht geladen, also zählt die Probe sie als Ladekosten
(`probe.pending_load_bytes`): 27 plus 235 MiB Reserve der Einbettungsspur, 545
MiB Schneider, 392 MiB Gewichte, dazu die Aktivierungen der parallelen Spuren
und das Wachstum des Schreiberheaps, und obendrauf ein Slot mit 235 MiB. Das
sind für Standard rund 1.535 MiB gegen einen Spielraum von rund 1.350 MiB
(2.048 MiB minus rund 700 MiB Leerlauf). Erwartet ist also `nofit`, bei
günstigerem Leerlauf `narrow`; gemessen wird trotzdem, per occ erzwungen und in
Rohdatei und Bericht als `erzwungen ja grund <verdikt>/<ursache>` markiert
(D-28-05).

**Die Rechnung je Zelle** (`12-slotkosten.py`, Kopf der Datei):

```
Rechnung_anon = MAIN_PROCESS_BASELINE_BYTES          1.257,5 MiB, enthält Gewichte int8,
                                                     Schneider, Sparsam-Heap, eine Aktivierung
              + slotsInForce x OCR_SLOT_COST_BYTES   235 MiB je Slot (Kind plus tesseract)
              + embed_slots x EMBED_ACTIVATION_BYTES 27 MiB je paralleler Spur
              + Schreiberheap des Profils minus Sparsam (78 MB Standard, 206 MB Leistung)
              + FP32_EXTRA_BYTES                     367 MiB, nur fp32
```

Verglichen wird das anon-Maximum der Container-cgroup der Zelle
(`rss_sampler.sh`) mit dieser Rechnung. Die Kosten je Slot aus
`12-slotkosten.py slots` stehen daneben gegen 235 MiB.

---

## 3. Die Toleranzen, vor der Messung festgelegt

**D-28-08, Rechnung gegen Messung.** Eine Zelle gilt als von der Rechnung
getragen, wenn ihr gemessenes anon-Maximum höchstens das 1,10-fache der
Rechnung ist (ganze Bytes, abgerundet; `12-slotkosten.py rechnung
--gemessen-bytes`). Liegt eine Zelle darüber, oder widerspricht ein
Probe-Verdikt der Messung (Abschnitt 5), entscheidet der Owner je Fall, ob die
Formel nachgezogen oder die Stufe im Release nicht angeboten wird (SC4,
Checkpoint C5).

**D-28-10, Sparsam gegen die Store-Zahl.** Nach der Vollzelle auf m7g.large misst
`94c-bodensatz-zyklen.sh` (zwei Zyklen, Ruhezeit 120 s) die Marke C1. Sie muss
im Band 730,2 MB plus/minus 2 Prozent liegen, also **715,6 bis 744,8 MB**.
Innerhalb bleibt der Store-Text; außerhalb entscheidet der Owner über die
Store-Zahl (Checkpoint C4). Frühere Messungen derselben Box: 731,9 (v1.2), 730,2
und 729,3 MB (v1.3).

---

## 4. Die fp32-Zellen

Nach D-28-07 misst Standard mit fp32 auf einer knappen und einer großzügigen Box:

- **knapp: c7a.xlarge** (4 Kerne, 8 GiB). Die typische Selfhost-Box aus D-28-04
  und die kleinste, auf der die Formel Standard vorschlägt. m7g.large mit 2g
  wäre zwar knapper, aber dort ist das Verdikt rechnerisch sicher `nofit`
  (1.257,5 plus 367 plus 235 plus 235 MiB Reserve = 2.094,5 MiB über 2.048 MiB),
  und die Zelle würde nur einen erzwungenen OOM messen.
- **großzügig: c7a.4xlarge** (16 Kerne, 32 GiB), mit 4 Slots, so dass fp32 und
  volle Standard-Slotzahl zusammen gemessen werden.

Die Probe lädt die fp32-Datei live aus dem eigenen Release (470.268.510 Bytes,
sha256-Prüfung im Produkt, Deckel 600 s). Der Nullstand läuft VOR der
fp32-Probe, weil `--rm-data` die geholte Datei mitnimmt. Gemessen wird neben der
Spitze der fp32-Mehrbedarf des Hauptprozesses gegen St-T derselben Box
(`12-slotkosten.py fp32`, Vergleichswert 367 MiB).

---

## 5. Die Gegenprobe der Probe je Zelle

Jede Standard-, Leistungs- und fp32-Zelle vergleicht das Verdikt der Probe mit
dem, was die Messung zeigt (28-RESEARCH.md, Pattern 5):

| Verdikt | stimmt, wenn die Messung zeigt |
|---|---|
| `fits` | kein Wächtereingriff, kein OOM, Reserve am Tiefpunkt mindestens 235 MiB |
| `narrow` | Reserve am Tiefpunkt unter 235 MiB oder eine Drossel |
| `nofit` | Drossel, Absenkung oder OOM |

Ein Widerspruch in beide Richtungen ist ein SC4-Fall für den Owner. Senkt der
Wächter mitten in der Zelle ab (`guard`-Block am Ende), wurde teils eine andere
Stufe gemessen; das wird als Befund der Gegenprobe geführt, nicht als Messfehler
verworfen.

---

## 6. Deckel und Sicherheitstimer

**Der Deckel.** `02-rechenblatt.py deckel` rechnet mit den Sätzen vom 29.09.2026:
Summe 45,18 USD, Deckel 58,74 USD; mit der Anker-Zelle nach D-28-11 Summe
45,71 USD, **Deckel 59,43 USD**. Die Stunden (113,86 h, mit Anker 119,82 h) sind
nur Anzeige, bindend ist USD. Die Sätze werden am Anfahrtstag noch einmal
gelesen; weicht einer ab, wird der Deckel vor der ersten Kommandozeile neu
gerechnet. Vor der ersten Minute steht in der Rohdatei die Zeile
`Anfahrt freigegeben: <Datum>, Deckel <h> h / <USD> USD`.

**D-28-02, beim Deckel.** Vor jeder neuen Zelle rechnet `02-rechenblatt.py stand`
aus den Kostenstempeln die bisherigen Kosten. Ist der Deckel erreicht
(Rückgabewert 5), wird die laufende Zelle zu Ende gemessen, keine neue Zelle
startet, und die Box bleibt stehen bis zum Owner-Wort (Checkpoint C3). Kein
automatischer Abbau.

**D-28-14, der Sicherheitstimer.** Bei Deckel mal 1,20 **stoppt** ein
Sicherheitstimer die Instanz, falls der Owner nicht antwortet; er beendet sie
nie (kein Terminate, nichts geht verloren). Seine Frist ist die Zeile
`minuten bis sicherheitsstopp` von `02-rechenblatt.py stand` beim Satz, der
gerade läuft.

---

## 7. Messgrößen und Quellen

| Größe | Quelle | Regel |
|---|---|---|
| RAM-Spitze der Zelle | `rss_sampler.sh`, 2 s, anon-Maximum der Container-cgroup | anon statt `memory.peak`, weil `memory.peak` den Seitencache des mmap-Index enthält |
| OOM-Beweis | Schlusszeile von `rss_sampler.sh` | `memory.events`, OOMKilled, RestartCount |
| Kosten je Slot | `proc_anon_sampler.sh`, 1 s, ausgewertet mit `12-slotkosten.py slots` | VmHWM-Paar Kind plus tesseract, anon-Summe je Zeitpunkt durch slotsInForce, Hauptprozess getrennt |
| fp32-Mehrbedarf | `12-slotkosten.py fp32` | Hauptprozess St-fp32 minus St-int8 derselben Box, gegen 367 MiB |
| Nextcloud-Kernlast r | `cpu_sampler.sh` | gegen 0,25 |
| Durchsatz | Statusreihe der Admin-Übersicht alle 120 s | Dateien je Stunde bis zum letzten Vektor, OCR-Seiten je Sekunde über die OCR-Phase |
| Leerlaufanteil | Anteil der Lesungen mit leerem Vorrat | über 10 Prozent heißt zulaufgebunden, nicht rechengebunden; im Bericht so benannt |

Vor dem Trigger jeder Zelle: Seitencache leeren (`drop_caches`, Zeile in der
Rohdatei), und gemessen wird erst, wenn die Admin-Übersicht `effective` gleich
dem Zielprofil meldet und `slotsInForce` gelesen ist.

---

## 8. Speichergrenzen

Nur die Referenzbox m7g.large läuft wie die Store-Messung mit `mem=4G` (Block 5)
und der harten Containergrenze 2g (Block 12, D-28-03). Auf den Matrix-Boxen
gibt es keine harte Speichergrenze, sie messen den vollen Box-RAM, im Protokoll
`memory.max max` (D-28-12). Vor dem Typwechsel auf m7g.4xlarge wird das
Drop-in für `mem=4G` entfernt.

---

## 9. Das gemessene Abbild

Gemessen wird das Abbild zum Commit
`c87a0239ca676a7dc6ac3f1b95f104800487a1a5`, per Digest und mit Baumhash-Beweis
im laufenden Container (Muster `92d-wechsel.sh`, `40b-baumhash.sh`). Die
SC4-Codeänderung an `OCR_SLOT_COST_BYTES` in `backend/src/findling/config.py`
fällt erst nach der letzten Zelle, sonst laufen Baumhash und Abbild
auseinander. Neue Skripte unter `docs/measurements/` berühren den Baumhash nicht.

---

## 10. Werkzeuge während der Anfahrt

Während der bezahlten Anfahrt wird kein Werkzeug geändert (Runbook 7.1). Eine
Ausnahme gibt es nur mit einem Owner-Wort, und sie bekommt eine eigene Zeile in
der Rohdatei: welches Werkzeug, warum, welcher Commit.
