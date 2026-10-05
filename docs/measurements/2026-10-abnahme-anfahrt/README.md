# Die Abnahme-Anfahrt der v1.4 (Phase 28)

Diese Anfahrt liefert den Messbeleg von MESS-10: RAM-Spitze und
Erstindex-Durchsatz je Profil auf der Referenzbox m7g.large und auf Mehrkern-Boxen
beider Architekturen (m7g.4xlarge, c7a.xlarge bis c7a.8xlarge), dazu die
gemessenen Kosten je OCR-Slot, die Gegenprobe der Probe und die Store-Marke C1.
Der Ablauf und die vor der Messung festgeschriebenen Erwartungen stehen in
`skripte/00-ablauf.md`, die Rohdaten in `rohdaten/`, die maschinelle Auswertung
aller Zellen in `auswertung.txt`.

Anfahrt freigegeben: 30.09.2026, Deckel 119,82 h / 59,43 USD (mit Anker-Zelle, `rohdaten/02-rechenblatt-freigabe.txt`)

**Zur Schreibweise.** Die Abschnittsüberschriften stehen ohne Umlaute, weil
Prüfungen und Verweise auf sie zeigen. Der Fließtext benutzt echte Umlaute.
Adressen, Kennungen und Passwörter der Boxen stehen in keiner Zeile dieser Datei.
Zahlen in MiB sind Vielfache von 1.048.576 Byte, die Store-Marke C1 steht wie im
Store-Text in MB.

---

## 1. Umfang und Abweichungen vom Plan

Gemessen sind **18 Zellen**, nicht 21. Die Zellen 3 und 4 (Standard und Leistung
auf m7g.large) und 10 (Leistung auf c7a.xlarge) hat der Owner am 03.10.2026
gestrichen (Quick 261003-d3y): Diese Boxen liegen unter den Vorschlags-Schwellen
(D-24-06, D-24-07), das Produkt lässt das Ziel dort nie wirksam werden, und die
Probe sagt seit dem Fix `nofit hardware_short`. Der erste Versuch der Zelle 3
brach deshalb mit 69 ab (`rohdaten/m7g.large/St-T-abbruch69-lauf6/`). Leistung
auf x86 messen die Zellen 14, 17 und 21. Die 18 Zellen zählen die Vollzelle
S-voll aus 28-06 mit.

| Box | Zellen | Plan |
|---|---|---|
| m7g.large (Referenz, `mem=4G`, Grenze 2g) | 1 S-voll, 2 Anker S-T | 28-06, 28-07 |
| m7g.4xlarge | 5 S-T, 6 St-T, 7 L-T | 28-07 |
| c7a.xlarge | 8 S-T, 9 St-T, 11 St-fp32-T | 28-08 |
| c7a.2xlarge | 12 S-T, 13 St-T, 14 L-T | 28-09 |
| c7a.4xlarge | 15 S-T, 16 St-T, 17 L-T, 18 St-fp32-T | 28-09 |
| c7a.8xlarge | 19 S-T, 20 St-T, 21 L-T | 28-09 |

Weitere Abweichungen, jeweils mit Beleg in den Rohdaten:

- **Abbild-Stand gewandert** (Abschnitt 2): gemessen nicht durchgehend auf
  c87a0239, sondern auf drei Ständen, zuletzt 18602c48.
- **Kettenabbrüche vor der ersten gültigen Teilkorpus-Zelle:** neun Kettenläufe
  auf ARM, sechs Quick-Tasks und ein Debug haben Zähltor, Vorrats-Tor,
  Reconcile und Crawl gehärtet. Die Rohdaten der Abbruchläufe liegen mit dem
  Suffix `-abbruch<code>` daneben und gehen in keine Zahl dieses Berichts ein.
- **c7a.8xlarge, Kettenstart-Abbruch 60:** veralteter DNS-Eintrag rund 1 min nach
  dem A-Record-Wechsel, vor Nullstand und Registrierung; genau eine Wiederholung,
  Rückgabewert 0 (`rohdaten/c7a.8xlarge-abbruch60-dns/`).
- **S-voll, Lücke der Prozessreihe:** `anon.csv` endet um 06:07:48Z, weil
  unattended-upgrades containerd neu startete; die cgroup-Reihe `rss.csv` läuft
  bis zum Ende. Kosten je Slot und Hauptprozess der S-voll decken 11,9 von 19,6 h
  (`rohdaten/m7g.large/S-voll/10-auswertung.txt`).
- **Containerlog fehlt** für S-T auf c7a.xlarge und c7a.2xlarge (Mitschnitt ging
  bei der Bewaffnung verloren). Keine Zahl dieses Berichts hängt am Containerlog.
- **Satz c7a.xlarge:** Die Statusabfrage von `aws_box.sh` nannte 0,234260 USD je
  Stunde, Kette und Kostenstempel rechnen mit dem Plansatz 0,252301 USD, also zum
  Deckel hin vorsichtig.

## 2. Abbild

Der Plan pinnt das Abbild zum Commit **c87a0239** (`skripte/00-ablauf.md`,
Abschnitt 9). Gemessen wurde auf drei Ständen, je Zelle per Digest gezogen und
mit Baumhash-Beweis im laufenden Container (`40b-baumhash.txt` je Zelle):

| Zellen | Commit | Index-Digest | Baumhash im Container |
|---|---|---|---|
| 1, 2 (m7g.large) | c87a0239 | `sha256:6a0c13be68de5ddd7c7ff404ab3a3caf15b646a5386c9e902ae3843ac572d80f` | `556148291147...` |
| 5, 6 (m7g.4xlarge) | f73566c1 | `sha256:d33bfcaea1ff933bb6fdcd387c70a665f5e04ce3ca5288c3932831882a9bdb0a` | `1a0598a6e159...` |
| 7 und alle x86-Zellen 8 bis 21 | 18602c48 | `sha256:5ed5742cbaddf14a378664e19cf2be6f500c3ac9b60d1a0bfc86e388f43ebc27` | `ee918ce4bc7c...` |

Warum der Wechsel: Jede Werkzeug- und Produktänderung während der Anfahrt lief
mit Owner-Wort (Runbook 7.1). Von c87a0239 auf f73566c1 kam der Fix der
Vorschlags-Schwellen in der Probe (`probe.py`, `worker/probe_run.py`, Quick
261003-d3y). Von f73566c1 auf 18602c48 kamen Reconcile und Crawl
(`worker/reconcile.py`, `nc/queue.py`, `nc/client.py`, Quick 261003-wxg und
Debug crawl-unfinished-zweitlauf), ohne die L-T auf m7g.4xlarge dreimal mit 71
abbrach. Keine der Änderungen berührt Extraktion, OCR, Einbettung oder
Speicherposten; die Rechnung (`12-slotkosten.py rechnung`) ist über alle Stände
dieselbe. Die SC4-Codeänderung an `OCR_SLOT_COST_BYTES` liegt nach der letzten
Zelle (28-12), damit Baumhash und Abbild nicht auseinanderlaufen.

## 3. Teilkorpus

5.000 Dateien nach der festen Regel aus D-28-09 (2.000 OCR-Dateien, 2.691
OCR-Seiten), als Hardlinks unter `lasttest/files/teilkorpus` auf beiden Platten.
`teilkorpus-liste.txt` trägt `name,bytes,sha256` und die Listen-Prüfsumme
`f6b3dd70971035374d502dfd27ac0dc8dd372f033c9fc4e12aa462e887c09979`; die x86-Platte
ergab dieselbe Prüfsumme (`rohdaten/06-aufbau-x86.txt`, `listen-pruefsumme-gleich
ja`). Das Zähltor bestätigte in jeder Teilkorpus-Zelle genau 5.000.

## 4. Speicher je Zelle

Die Zahl der Zelle ist das anon-Maximum der Container-cgroup (`rss.csv`, 2 s).
`memory.peak` steht in `auswertung.txt` daneben, weil er den Seitencache des
mmap-Index enthält. Rechnung und Grenze stammen aus `00-ablauf.md`, gerechnet mit
`slotsInForce` am Ende der Zelle; getragen heißt: höchstens das 1,10-fache der
Rechnung (D-28-08).

| Nr | Box | Zelle | Slots | anon MiB | Rechnung MiB | Grenze MiB | Abw. | getragen | Hauptprozess MiB | Probe | erzwungen | Gegenprobe |
|---:|---|---|---:|---:|---:|---:|---:|---|---:|---|---|---|
| 1 | m7g.large | S-voll | 1 | 1.788,9 | 1.492,5 | 1.641,8 | +19,9 % | **nein** | 1.571,1 (Teilreihe) | keine | | entfällt |
| 2 | m7g.large | Anker S-T | 1 | 1.512,0 | 1.492,5 | 1.641,8 | +1,3 % | ja | 1.291,6 | keine | | entfällt |
| 5 | m7g.4xlarge | S-T | 1 | 1.499,6 | 1.492,5 | 1.641,8 | +0,5 % | ja | 1.281,0 | keine | | entfällt |
| 6 | m7g.4xlarge | St-T | 4 | 2.358,2 | 2.298,9 | 2.528,8 | +2,6 % | ja | 1.497,0 | fits | nein | stimmt |
| 7 | m7g.4xlarge | L-T | 15 | 5.481,8 | 5.033,0 | 5.536,3 | +8,9 % | ja | 2.319,0 | fits | nein | stimmt |
| 8 | c7a.xlarge | S-T | 1 | 1.520,2 | 1.492,5 | 1.641,8 | +1,9 % | ja | 1.288,5 | keine | | entfällt |
| 9 | c7a.xlarge | St-T | 1 | 1.679,5 | 1.593,9 | 1.753,3 | +5,4 % | ja | 1.396,9 | fits | nein | stimmt |
| 11 | c7a.xlarge | St-fp32-T | 1 | 2.172,5 | 1.960,9 | 2.157,0 | +10,8 % | **nein** | 1.906,6 | fits | nein | stimmt |
| 12 | c7a.2xlarge | S-T | 1 | 1.535,3 | 1.492,5 | 1.641,8 | +2,9 % | ja | 1.303,4 | keine | | entfällt |
| 13 | c7a.2xlarge | St-T | 3 | 2.181,9 | 2.063,9 | 2.270,3 | +5,7 % | ja | 1.506,0 | fits | nein | stimmt |
| 14 | c7a.2xlarge | L-T | 7 | 3.374,0 | 3.153,0 | 3.468,3 | +7,0 % | ja | 1.960,6 | fits | nein | stimmt |
| 15 | c7a.4xlarge | S-T | 1 | 1.534,8 | 1.492,5 | 1.641,8 | +2,8 % | ja | 1.302,3 | keine | | entfällt |
| 16 | c7a.4xlarge | St-T | 4 | 2.591,6 | 2.298,9 | 2.528,8 | +12,7 % | **nein** | 1.755,6 | fits | nein | stimmt |
| 17 | c7a.4xlarge | L-T | 15 | 5.623,7 | 5.033,0 | 5.536,3 | +11,7 % | **nein** | 2.410,8 | fits | nein | stimmt |
| 18 | c7a.4xlarge | St-fp32-T | 4 | 2.844,6 | 2.665,9 | 2.932,5 | +6,7 % | ja | 1.978,9 | fits | nein | stimmt |
| 19 | c7a.8xlarge | S-T | 1 | 1.534,3 | 1.492,5 | 1.641,8 | +2,8 % | ja | 1.300,6 | keine | | entfällt |
| 20 | c7a.8xlarge | St-T | 4 | 2.560,2 | 2.298,9 | 2.528,8 | +11,4 % | **nein** | 1.640,1 | fits | nein | stimmt |
| 21 | c7a.8xlarge | L-T | 16 | 5.802,8 | 5.268,0 | 5.794,8 | +10,2 % | **nein** | 2.530,2 | fits | nein | stimmt |

In keiner Zelle senkte der Wächter ab, keine Zelle wurde gedrosselt, und jede
Zelle endet mit `oom 0 oom_kill 0`, OOMKilled false und RestartCount 0. Die
S-voll hat keine OOM-Schlusszeile (das Werkzeug schrieb sie damals noch nicht);
das Kernel-Journal ihres Boots enthält keinen OOM-Treffer
(`S-voll/10-auswertung.txt`, Nachtrag 01.10.).

## 5. Durchsatz je Zelle

Dateien je Stunde über den ganzen Lauf, vom Trigger bis zur ersten Statuslesung
mit dem letzten Vektor (Lesungen alle 120 s). OCR-Seiten je Sekunde über das
OCR-Fenster, die Spanne von der ersten bis zur letzten tesseract-Zeile der
Prozessreihe (1 s). r ist die mittlere Kernlast der Box ohne den Container
über das OCR-Fenster (`cpu.csv`), gegen `NEXTCLOUD_CORE_LOAD` 0,25.

| Nr | Box | Zelle | Dateien/h | OCR-Seiten/s | Volltext h | beide Spuren h | Leerlauf | Anlauf min | r |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | m7g.large | S-voll (52.137) | 2.670 | nicht berechnet | 18,72 | 19,53 | 0 % | 2 | 0,210 |
| 2 | m7g.large | Anker S-T | 1.325 | 0,214 | 3,77 | 3,77 | 4 % | 10 | 0,133 |
| 5 | m7g.4xlarge | S-T | 1.399 | 0,226 | 3,57 | 3,57 | 4 % | 10 | 0,129 |
| 6 | m7g.4xlarge | St-T | 3.185 | 0,599 | 1,57 | 1,57 | 13 % | 12 | 0,146 |
| 7 | m7g.4xlarge | L-T | 3.403 | 0,617 | 1,00 | 1,47 | 9 % | 10 | 0,160 |
| 8 | c7a.xlarge | S-T | 1.920 | 0,309 | 2,60 | 2,60 | 5 % | 10 | 0,147 |
| 9 | c7a.xlarge | St-T | 2.024 | 0,344 | 2,47 | 2,47 | 7 % | 12 | 0,160 |
| 11 | c7a.xlarge | St-fp32-T | 2.024 | 0,339 | 2,47 | 2,47 | 7 % | 10 | 0,161 |
| 12 | c7a.2xlarge | S-T | 1.872 | 0,315 | 2,67 | 2,67 | 6 % | 12 | 0,143 |
| 13 | c7a.2xlarge | St-T | 3.840 | 0,723 | 1,30 | 1,30 | 15 % | 12 | 0,188 |
| 14 | c7a.2xlarge | L-T | 4.831 | 1,052 | 1,03 | 1,03 | 23 % | 14 | 0,205 |
| 15 | c7a.4xlarge | S-T | 1.849 | 0,304 | 2,70 | 2,70 | 6 % | 10 | 0,148 |
| 16 | c7a.4xlarge | St-T | 4.159 | 0,836 | 1,20 | 1,20 | 19 % | 14 | 0,195 |
| 17 | c7a.4xlarge | L-T | 6.241 | 1,508 | 0,77 | 0,80 | 22 % | 12 | 0,238 |
| 18 | c7a.4xlarge | St-fp32-T | 4.279 | 0,835 | 1,17 | 1,17 | 17 % | 12 | 0,196 |
| 19 | c7a.8xlarge | S-T | 1.849 | 0,303 | 2,70 | 2,70 | 6 % | 10 | 0,159 |
| 20 | c7a.8xlarge | St-T | 4.280 | 0,838 | 1,17 | 1,17 | 15 % | 12 | 0,204 |
| 21 | c7a.8xlarge | L-T | 6.512 | 1,565 | 0,77 | 0,77 | 26 % | 12 | 0,248 |

**Leerlauf.** In acht Zellen (6, 13, 14, 16, 17, 18, 20, 21) liegt der
Leerlaufanteil über 10 Prozent. Diese Zellen sind im Anlauf **zulaufgebunden**:
Jede leere Lesung fällt in die 10 bis 14 Minuten zwischen Trigger und erster
indexierter Datei, in denen der Crawl auf den nächsten Hintergrundjob wartet
(Cron-Intervall 300 s) und die ersten Scheiben einplant. Nach dem Anlauf gab es
in keiner Zelle eine leere Lesung. Bei kurzen Läufen von rund einer Stunde macht
dieser feste Anlauf den Anteil groß; der Durchsatz der schnellen Zellen ist
deshalb eine Untergrenze ihrer Rechenleistung.

**r.** In allen Zellen liegt r zwischen 0,129 und 0,248 und damit unter oder
an `NEXTCLOUD_CORE_LOAD` 0,25; die Leistungszellen mit 15 und 16 Slots kommen
am nächsten heran.

**S-voll.** Die Seitenzahl des Vollkorpus steht nicht in den Rohdaten, und die
Prozessreihe endet vor dem OCR-Ende; OCR-Seiten je Sekunde sind deshalb für die
S-voll nicht berechnet.

## 6. Gegenprobe der Probe

Elf Zellen hatten eine Probe (alle Standard-, Leistungs- und fp32-Zellen), alle
elf mit dem Verdikt `fits` und `erzwungen nein`. Die Regel aus `00-ablauf.md`,
Abschnitt 5: `fits` stimmt bei keinem Wächtereingriff, keinem OOM und einer
Reserve am Tiefpunkt von mindestens 235 MiB.

Wächter und OOM sind in allen elf Zellen sauber (Abschnitt 4). Den freien
Box-Speicher am Tiefpunkt hat keine Zelle gesampelt; als Ersatzmaß steht in
`auswertung.txt` der Box-RAM nach dem Typwechsel (`free -h`) minus 1 GiB (die
MemAvailable-Annahme der Formel) minus anon-Spitze der Zelle. Der kleinste Wert
liegt bei Zelle 11 auf c7a.xlarge mit rund 4.586 MiB, also weit über 235 MiB.
**Alle elf Verdikte stimmen; es gibt keinen Probe-Widerspruch.**

## 7. Sparsam-voll und die Store-Marke C1

Die Vollzelle S-voll (m7g.large, `mem=4G`, Grenze 2g, 52.137 Dateien) lief
19,53 h unbeaufsichtigt durch: Volltextspur 18,72 h, rund 2.670 Dateien je
Stunde über beide Spuren, anon-Spitze 1.788,9 MiB (1.875,8 MB) unter der Grenze
von 2.048 MiB, kein OOM.

Nach der Vollzelle maß `94c-bodensatz-zyklen.sh` (zwei Zyklen, Ruhezeit 120 s)
**C1 = 743,9 MB** gegen die Store-Zahl 730,2 MB: +13,7 MB oder +1,88 Prozent,
**innerhalb** des Bands 715,6 bis 744,8 MB (D-28-10). Die Marke liegt 0,9 MB
unter der oberen Bandgrenze; frühere Messungen derselben Box: 731,9 (v1.2),
730,2 und 729,3 MB (v1.3). Ein Store-Zahl-Fall (C4) entsteht damit nicht
(`rohdaten/m7g.large/94c/94c-bewertung.txt`).

Die anon-Spitze der S-voll liegt dagegen 19,9 Prozent über ihrer Rechnung und ist
damit ein SC4-Fall (Abschnitt 11). Diese Bewertung steht hier zum ersten Mal;
28-06 hatte die Zahl gemessen, aber nicht gegen die Grenze 1.641,8 MiB gestellt.

## 8. Kosten je Slot und Kandidat fuer OCR_SLOT_COST_BYTES

`12-slotkosten.py slots` liefert je Zelle drei Maße (Rohausgabe am Ende von
`auswertung.txt`):

| Maß | Bereich über alle Zellen | Maximum |
|---|---|---|
| VmHWM-Paar Kind plus tesseract | 404,6 bis 447,2 MiB | 447,2 MiB, Zelle 6 |
| RssAnon-Paar Kind plus tesseract | 356,2 bis 390,7 MiB | 390,7 MiB, Zelle 17 |
| anon-Summe je Zeitpunkt durch Slots, bei 1 Slot | 290,5 bis 300,1 MiB | 300,1 MiB, Zelle 5 |
| dasselbe bei mehreren Slots | 212,5 bis 235,4 MiB | 235,4 MiB, Zelle 13 |

**Der Kandidat nach der Regel des Plans** (Maximum des VmHWM-Paars, auf volle MiB
aufgerundet) ist **448 MiB = 469.762.048 Byte** (alt: 235 MiB = 246.415.360
Byte). Dabei ist zu beachten: Die 235 MiB aus B2 sind ein **RssAnon**-Paar
(Kind 136,4 plus tesseract 98,8, `docs/performance.md`), kein VmHWM-Paar. VmHWM
zählt den residenten Höchststand samt dateigestützter Seiten, und das Paar
setzt zwei Maxima aus verschiedenen Zeitpunkten zusammen. Das Maß von B2 ergibt
**391 MiB = 409.993.216 Byte**. Beide Paarmaße liegen weit über dem, was mehrere
Slots gleichzeitig tatsächlich belegen (212,5 bis 235,4 MiB je Slot).

Was die Kandidaten an der Rechnung ändern (anon geteilt durch Rechnung, über
1,10 nicht getragen; Zahlen aus `auswertung.txt`):

| Slotwert | nicht getragen | knappste getragene Zelle | größte Überschätzung |
|---|---|---|---|
| 235 MiB (heute) | 1, 11, 16, 17, 20, 21 | 7 (1,089) | keine unter 1,0 |
| 250 MiB = 262.144.000 Byte | 1 | 11 (1,100) | 5 (0,995) |
| 301 MiB = 315.621.376 Byte | 1 | 11 (1,072) | 7 (0,910) |
| 391 MiB = 409.993.216 Byte | keine | 1 (1,085) | 7 (0,744) |
| 448 MiB = 469.762.048 Byte | keine | 1 (1,049) | 7 (0,666) |

250 MiB ist der kleinste Slotwert, der alle 17 Teilkorpus-Zellen trägt; alle 18
Zellen trägt erst ein Slotwert von 369 MiB, weil die S-voll einen anderen Grund
hat (Abschnitt 10).

**Wirkung im Produkt.** `EMBED_LANE_RESERVE_BYTES` und `GUARD_RESERVE_BYTES`
sind in `config.py` gleich `OCR_SLOT_COST_BYTES` und wachsen mit; damit wächst die
Reserve, ab der die Probe "passt knapp" sagt, und der Abstand, ab dem der
Wächter eingreift. Die Slotzahl der Formel ändert sich auf allen Messboxen mit
keinem der Kandidaten, weil dort der Kernterm bindet. Auf einer Box mit 8 Kernen
und 8 GiB sinkt Standard bei 391 und 448 MiB von 3 auf 2 Slots, Standard mit fp32
von 2 auf 1 und Leistung von 7 auf 6 (391 MiB) bzw. 5 (448 MiB); bei 250 und
301 MiB bleibt sie gleich.

## 9. fp32

| Box | Slots | Hauptprozess int8 | Hauptprozess fp32 | Mehrbedarf | gegen 367 MiB |
|---|---:|---:|---:|---:|---|
| c7a.xlarge (Zelle 11) | 1 | 1.396,9 MiB | 1.906,6 MiB | 509,7 MiB | nicht getragen |
| c7a.4xlarge (Zelle 18) | 4 | 1.755,6 MiB | 1.978,9 MiB | 223,2 MiB | getragen |

Beide fp32-Dateien kamen live aus dem eigenen Release (470.268.510 Byte, ohne
Digest-Warnung), beide Zellen kehrten danach über den Abwärtsweg auf int8 zurück
(`99-rueckkehr-int8.txt`). Der Mehrbedarf ist die Differenz zweier
Hauptprozess-Maxima, die beide mit der Slotzahl driften: Auf c7a.4xlarge liegt
schon das int8-Gegenstück 396,7 MiB über dem Hauptprozess-Anteil der Rechnung
(Zelle 16), und der Mehrbedarf fällt entsprechend klein aus. Die beiden
Datenpunkte schließen sich nicht aus, sie messen den fp32-Posten nur nicht
getrennt vom Slotposten im Hauptprozess.

## 10. Befund Hauptprozess

Zieht man von der Rechnung die Slots ab (Slots mal 235 MiB), bleibt der
Hauptprozess-Anteil der Rechnung: 1.257,5 MiB bei Sparsam, 1.358,9 MiB bei
Standard, 1.508,0 MiB bei Leistung, je plus 367 MiB bei fp32. Gegen diesen Anteil:

| Zelle | Slots | Hauptprozess über dem Anteil | je Slot | anon minus Hauptprozess, je Slot |
|---|---:|---:|---:|---:|
| ARM 5 S-T | 1 | +23,5 MiB | +23,5 | 218,6 |
| ARM 6 St-T | 4 | +138,1 MiB | +34,5 | 215,3 |
| ARM 7 L-T | 15 | +811,0 MiB | +54,1 | 210,9 |
| x86 8, 12, 15, 19 S-T | 1 | +31,0 bis +45,9 MiB | +31,0 bis +45,9 | 231,7 bis 233,7 |
| x86 13 St-T | 3 | +147,1 MiB | +49,0 | 225,3 |
| x86 14 L-T | 7 | +452,6 MiB | +64,7 | 201,9 |
| x86 16 St-T | 4 | +396,7 MiB | +99,2 | 209,0 |
| x86 20 St-T | 4 | +281,2 MiB | +70,3 | 230,0 |
| x86 17 L-T | 15 | +902,8 MiB | +60,2 | 214,2 |
| x86 21 L-T | 16 | +1.022,2 MiB | +63,9 | 204,5 |
| S-voll 1 | 1 | +313,6 MiB | | 217,8 |

Was die Zahlen zeigen:

- Was neben dem Hauptprozess im Container liegt (anon-Spitze minus
  Hauptprozess-Maximum, zwei Maxima aus verschiedenen Zeitpunkten), bleibt in 16
  von 18 Zellen bei 202 bis 234 MiB je Slot und damit **unter 235 MiB**; darüber
  liegen nur die Standardzellen mit einem Slot auf c7a.xlarge (Zelle 9 mit
  282,6 MiB, getragen; Zelle 11 mit 265,9 MiB, der fp32-Fall). In den vier
  x86-Fällen mit mehreren Slots sind die Slots selbst nicht zu
  teuer gerechnet.
- Der **Hauptprozess wächst mit der Slotzahl**, auf beiden Architekturen. Die
  Rechnung kennt im Hauptprozess keinen Posten je Slot (nur je Einbettungsspur
  27 MiB und den Schreiberheap).
- Auf x86 wächst er stärker: bei 4 Slots +70 bis +99 MiB je Slot gegen +34,5 auf
  ARM, bei 15 Slots +60,2 gegen +54,1. ARM trägt dieselben Stufen deshalb
  (St-T +2,6 %, L-T +8,9 %), x86 nicht (+11,4 bis +12,7 %, +10,2 bis +11,7 %).
- Die Hypothese, dass die Rechnung auf x86 einen architekturabhängigen
  Hauptprozess-Term braucht statt höherer Slotkosten, passt zu den Zahlen; die
  ARM-L-T mit +8,9 % liegt aber selbst nur knapp in der Toleranz, ein Term je
  Slot würde beide Architekturen betreffen. Die Daten unterscheiden die zwei
  Lesarten nicht sicher: zwei Hauptprozess-Maxima je Box, keine Wiederholung.
- Die S-voll ist ein eigener Fall: ein Slot, aber ein Index über 52.137 Dateien.
  Ihr Hauptprozess liegt 313,6 MiB über der Grundlinie, gemessen nur über die
  ersten 11,9 h; ein Posten für die Indexgröße steht nicht in der Rechnung.

Was ein korrigierter Hauptprozess-Term je Zelle ergäbe (kleinster Zuschlag, der
die Zelle unter die Grenze bringt, anon/1,10 minus Rechnung):

| Zelle | Zuschlag gesamt | je Slot |
|---|---:|---:|
| 11 c7a.xlarge St-fp32-T | 14,1 MiB | 14,1 |
| 16 c7a.4xlarge St-T | 57,1 MiB | 14,3 |
| 17 c7a.4xlarge L-T | 79,5 MiB | 5,3 |
| 20 c7a.8xlarge St-T | 28,6 MiB | 7,2 |
| 21 c7a.8xlarge L-T | 7,3 MiB | 0,5 |
| 1 m7g.large S-voll | 133,8 MiB | 133,8 |

Ein Zuschlag von 15 MiB je Slot im Hauptprozess trägt alle fünf x86-Fälle; er ist
rechnerisch gleichwertig mit einem Slotwert von 250 MiB. Ein fester Zuschlag
ohne Slotbezug müsste 80 MiB betragen (Zelle 17). Beides trägt die S-voll nicht.

## 11. Offene SC4-Faelle

Nach D-28-08 entscheidet der Owner je Fall: **Formel nachziehen** oder **Stufe im
Release nicht anbieten**. Probe-Widersprüche gibt es keine.

| Fall | Zelle | Rechnung | Messung | Abweichung | Kernbefund |
|---|---|---:|---:|---:|---|
| 1 | 1 m7g.large S-voll, Sparsam | 1.492,5 MiB | 1.788,9 MiB | +19,9 % | Hauptprozess +313,6 MiB bei großem Index; unter 2g, kein OOM; C1 im Band |
| 2 | 11 c7a.xlarge St-fp32-T | 1.960,9 MiB | 2.172,5 MiB | +10,8 % | fp32-Mehrbedarf 509,7 statt 367 MiB |
| 3 | 16 c7a.4xlarge St-T | 2.298,9 MiB | 2.591,6 MiB | +12,7 % | Hauptprozess +396,7 MiB bei 4 Slots |
| 4 | 17 c7a.4xlarge L-T | 5.033,0 MiB | 5.623,7 MiB | +11,7 % | Hauptprozess +902,8 MiB bei 15 Slots |
| 5 | 20 c7a.8xlarge St-T | 2.298,9 MiB | 2.560,2 MiB | +11,4 % | Hauptprozess +281,2 MiB bei 4 Slots |
| 6 | 21 c7a.8xlarge L-T | 5.268,0 MiB | 5.802,8 MiB | +10,2 % | Hauptprozess +1.022,2 MiB bei 16 Slots |

Zu Fall 1: Sparsam ist der Abwärtsweg und der Grundzustand des Produkts; "nicht
anbieten" ist für diese Stufe kein gangbarer Weg im Sinne von D-28-08.

Daneben steht der Wert von `OCR_SLOT_COST_BYTES` zur Bestätigung (Abschnitt 8).

## 12. Kosten gegen den Deckel

Stand nach dem letzten Stopp (`02-rechenblatt.py stand --jetzt
2026-10-05T16:04:27Z`, `rohdaten/90-kosten.txt`): **34,09 USD gegen den Deckel
59,43 USD**, Rest 25,34 USD; der Sicherheitsstopp bei 71,32 USD (Deckel mal 1,20)
wurde nie erreicht. Beide Boxen sind geparkt, die Platten laufen als Parkposten
weiter. Aufgeschlüsselt aus den Stempelzeilen:

| Posten | Stunden | Satz USD/h | USD |
|---|---:|---:|---:|
| m7g.large | 31,95 | 0,115841 | 3,70 |
| m7g.4xlarge | 10,53 | 0,800141 | 8,43 |
| c7a.xlarge | 8,66 | 0,252301 | 2,18 |
| c7a.2xlarge | 5,31 | 0,486561 | 2,59 |
| c7a.4xlarge | 6,51 | 0,955081 | 6,21 |
| c7a.8xlarge | 5,22 | 1,892121 | 9,87 |
| geparkt (Platten) | 84,66 | 0,013041 | 1,10 |
| **Summe** | | | **34,09** |

Die Schlusstabelle nach Runbook 2.6 (Summe je Typ, Differenz, Sicherheitstimer
ausgelöst ja/nein) gehört zum Abbau in 28-10 und steht noch aus; der Rechenwert
der Freigabe lag bei 45,71 USD.

## 13. Runbook-Belege

- **Cron-Gate je Instanz:** ARM `rohdaten/97-cron-vorpruefung-vorher.txt` und
  `03-aufbau-arm.txt` (Modus cron, Intervall 300 s, Toleranz 270 bis 330 s
  erfüllt); x86 `06-aufbau-x86.txt` (Cron-Intervall 300 s, AIO-Cron-Container).
  Die Typwechsel behalten Instanz und Cron-Container; eine eigene Cron-Messung je
  Typ steht nicht in den Rohdaten.
- **Digest-Wechsel:** `92d-wechsel.txt` (c87a0239), `05-typwechsel-arm.txt`
  (d33bfcae, 5242e47f für Lauf 8, 5ed5742c für Lauf 9), `06-aufbau-x86.txt`
  (5ed5742c); je Zelle `abbild-digest` in `10-zelle.txt`.
- **Baumhash:** je Zelle `40b-baumhash.txt` mit `baumhash-gleich ja`, Werte in
  Abschnitt 2.
- **Typwechsel:** `05-typwechsel-arm.txt`, `07-typwechsel-x86.txt` mit Stempeln und
  Rücklesung (`nproc`, `free -h`, Architektur); `memory.max max` je Matrix-Zelle.
- **Machbarkeitstor x86:** `06-aufbau-x86.txt`, bestanden in 45 min.

## 14. Owner-Entscheide

Entschieden am **05.10.2026** per Auswahlfrage in der Session, auf Grundlage der
Abschnitte 8 bis 11. Das Signal, wörtlich:

> je-fall: 11=nachziehen, 16=nachziehen, 17=nachziehen, 20=nachziehen, 21=nachziehen, S-voll=nachziehen (Vollindex-Term, Umfang legt 28-12 vor), wert=250 MiB, store=kein Fall

Was das im Einzelnen heißt:

1. **`OCR_SLOT_COST_BYTES` wird 250 MiB = 262.144.000 Byte** (alt 235 MiB =
   246.415.360 Byte). Der Owner wählte weder den Kandidaten nach der Planregel
   (448 MiB, VmHWM-Paar) noch das B2-Maß (391 MiB), sondern den kleinsten
   Slotwert, der alle 17 Teilkorpus-Zellen trägt (Abschnitt 8). Er entspricht
   rechnerisch dem Hauptprozess-Zuschlag von 15 MiB je Slot aus Abschnitt 10 und
   trägt auch die fp32-Zelle 11 (anon durch Rechnung 1,100). Die Slotzahl der
   Formel bleibt auf allen Messboxen und auf einer Box mit 8 Kernen und 8 GiB
   gleich. `EMBED_LANE_RESERVE_BYTES` und `GUARD_RESERVE_BYTES` folgen dem Wert.
   `FP32_EXTRA_BYTES` bleibt bei 367 MiB.
2. **Die fünf x86-Fälle (Zellen 11, 16, 17, 20, 21): Formel nachziehen.** Keine
   Stufe wird im Release gestrichen. Die Umsetzung ist der neue Slotwert aus
   Punkt 1, Codeänderung in 28-12.
3. **S-voll (Fall 1, +19,9 %): Formel nachziehen.** 28-12 legt einen
   Vollindex-Term vor: Der Hauptprozess wächst mit der Indexgröße, die S-voll
   braucht 133,8 MiB Zuschlag (Abschnitt 10). Der Umfang dieser Produktänderung
   wird dem Owner vor dem Bau vorgelegt.
4. **Store-Zahl (C4): kein Fall.** C1 = 743,9 MB liegt im Band 715,6 bis
   744,8 MB (Abschnitt 7); die Store-Zahl 730,2 MB und `RESIDENT_FIGURE` "730.2"
   in `backend/tests/test_store_metadata.py` bleiben unverändert.

Damit hat jeder SC4-Fall aus Abschnitt 11 einen Entscheid. Probe-Widersprüche
gab es keine (Abschnitt 6).

