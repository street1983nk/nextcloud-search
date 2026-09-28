# Laufzeitspeicher e5-small fp32 gegen int8, 28.09.2026

## 1. Zweck

Die Recherche zu Phase 25 hat den Laufzeitspeicher der fp32-Gewichte als
Annahme A1 offen gelassen. D-25-01 verlangt, dass die RAM-Schranke der
Einbettungsspur den fp32-Mehrbedarf einrechnet. Ohne Messung wären Slotformel
und RAM-Bedingung geraten. Diese Messung liefert die Zahl `FP32_EXTRA_BYTES`,
die Plan 25-08 als Literal in `backend/src/findling/config.py` übernimmt.

## 2. Aufbau

| Was | Wert |
|---|---|
| Abbild | `ghcr.io/street1983nk/findling_backend:dev` |
| Digest | `sha256:8d49814ce631cd226da40785b8aaed0384b4ce933965a31b3bcdf236c9fa428b`, gebaut am 08.09.2026 |
| Docker | 29.5.2, Docker Desktop auf WSL2 (Kernel 6.6.87.2), x86_64, 12 Kerne, 7,6 GiB im VM |
| onnxruntime im Abbild | 1.29.0 |
| int8-Gewichte | `/usr/local/share/findling/model/model.onnx` aus dem Abbild |
| fp32-Gewichte | `intfloat/multilingual-e5-small`, Datei `onnx/model.onnx`, Revision `614241f622f53c4eeff9890bdc4f31cfecc418b3` |
| fp32 Größe | 470268510 Byte |
| fp32 sha256 | `ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665` |
| Rohdaten | `rohdaten/00-umgebung.txt`, `rohdaten/01-int8-lauf1.txt` bis `-lauf5.txt`, `rohdaten/01-fp32-lauf1.txt` bis `-lauf5.txt` |
| Skript | `skripte/01-fp32-speicher.py` |

Größe und Digest der fp32-Datei sind vor der Messung gegen die Pins in
`backend/Dockerfile` (Zeilen 144 und 145) geprüft worden und stimmen. Die Datei
lag außerhalb des Repos und wurde read-only in den Container gehängt; im Repo
liegt keine Modelldatei.

## 3. Methode

- Ein frischer Container je Lauf (`docker run --rm --network none`, ohne
  `--memory`-Grenze), die Läufe nacheinander und abwechselnd int8 und fp32.
- Gemessen wird `RssAnon` aus `/proc/self/status`: die Gewichte einer
  ONNX-Sitzung liegen im anonymen Speicher, dateigestützte Seiten der
  Bibliotheken würden den Vergleich nur verwischen.
- Vor der ersten Ablesung sind onnxruntime, numpy, tokenizers, die
  Konfiguration und der Tokenizer schon geladen. Die Deltas zeigen also nur
  Gewichte und Aktivierungen.
- Drei Ablesungen: vor dem Laden, nach dem Anlegen der InferenceSession, nach
  dem ersten Batch. Danach fünf weitere Batches für die Rate, und eine vierte
  Ablesung am Ende.
- Sitzungsoptionen wie `embed/model.py::_open_session`: zwei Intra-Op-Threads,
  ein Inter-Op-Thread, Speicherarena aus, nur CPUExecutionProvider.
- Batch aus 8 festen englischen Passagen, jede so lang, dass sie auf die
  Sequenzlänge 512 abgeschnitten wird (ungünstigster Fall für die
  Aktivierungen).

Geplant waren drei Läufe je Präzision. Die Rate streute danach um mehr als
5 Prozent, deshalb sind zwei weitere Läufe je Präzision nachgeholt; alle fünf
stehen in der Tabelle.

## 4. Die Läufe

Alle Werte in KiB, wie `/proc/self/status` sie liefert.

| Lauf | vor dem Laden | nach Session | nach erstem Batch | nach allen Batches | Zuwachs Session | Zuwachs bis erster Batch | Passagen je s |
|---|---:|---:|---:|---:|---:|---:|---:|
| int8 1 | 313140 | 445756 | 461360 | 464668 | 132616 | 148220 | 5,973 |
| int8 2 | 312968 | 445584 | **460704** | 463744 | 132616 | 147736 | 5,901 |
| int8 3 | 313096 | 445712 | 461288 | 464820 | 132616 | 148192 | 5,095 |
| int8 4 | 313176 | 445792 | 461536 | 464216 | 132616 | 148360 | 6,080 |
| int8 5 | 313220 | 445804 | 461620 | 464332 | 132584 | 148400 | 4,762 |
| fp32 1 | 312772 | 832988 | 833660 | 837152 | 520216 | 520888 | 3,614 |
| fp32 2 | 313120 | 833476 | 833108 | 836484 | 520356 | 519988 | 3,220 |
| fp32 3 | 313156 | 833460 | 833804 | 836816 | 520304 | 520648 | 3,783 |
| fp32 4 | 313108 | 833360 | **835980** | 838092 | 520252 | 522872 | 3,029 |
| fp32 5 | 313168 | 833356 | 833772 | 837228 | 520188 | 520604 | 3,011 |

**Streuung Speicher:** nach dem ersten Batch int8 460704 bis 461620 KiB
(0,2 Prozent), fp32 833108 bis 835980 KiB (0,3 Prozent). Der Speicher ist
stabil.

**Streuung Rate:** int8 4,762 bis 6,080, fp32 3,011 bis 3,783 Passagen je
Sekunde, rund 25 Prozent in beiden Reihen. Die Rate hängt am Wirt (Docker
Desktop unter Windows, andere Last im Hintergrund) und ist nur als Verhältnis
belastbar, nicht als absolute Zahl für die Zielhardware.

## 5. Ergebnis

**Ableitung:** größter fp32-Wert nach dem ersten Batch minus kleinster
int8-Wert nach dem ersten Batch.

- 835980 KiB minus 460704 KiB = 375276 KiB
- mal 1024 = 384282624 Byte = 366,5 MiB
- auf ganze MiB aufgerundet: 367 MiB

> **`FP32_EXTRA_BYTES = 367 * MIB`**, das sind **384827392 Byte**.

Diese Literalform übernimmt Plan 25-08 in `backend/src/findling/config.py`,
mit Verweis auf diesen Ordner.

**Warum der Wert nach dem ersten Batch und nicht nach der Session.** Nach der
Session allein ist der Abstand größer (höchster fp32-Wert 833476 minus
niedrigster int8-Wert 445584 = 387892 KiB, 378,8 MiB), weil int8 im ersten
Batch noch rund 15 MiB nachlegt und fp32 kaum etwas. Die RAM-Schranke reserviert
aber für die Spitze einer laufenden Einbettung, und die liegt bei beiden
Präzisionen nach dem ersten Batch. Nach allen sechs Batches ist der Abstand
mit höchstens 374348 KiB (365,6 MiB) kleiner als der gewählte Wert. 367 MiB
decken also den Dauerzustand ab.

**Was die Ablesung nicht sieht.** `RssAnon` wird zwischen den Batches gelesen,
nicht während `session.run`. Die kurzlebige Aktivierungsspitze innerhalb eines
Laufs fehlt in beiden Reihen gleichermaßen; sie ist in `docs/embeddings.md` mit
+26,4 MB getrennt gemessen und rechnet sich unabhängig von der Präzision ein.
Der Mehrbedarf von fp32 sind die Gewichte, nicht die Aktivierungen.

**Einbettungsrate (Median aus fünf Läufen, Batch 8, Sequenz 512, 2 Threads):**

| Präzision | Median Passagen je s | Verhältnis |
|---|---:|---:|
| int8 | 5,901 | 1,00 |
| fp32 | 3,220 | 0,55 |

fp32 bettet auf diesem Wirt mit gut der Hälfte der int8-Rate ein.

**Vergleich mit dem int8-Ladesprung aus `docs/embeddings.md`.** Dort kostet die
erste Einbettung mit int8 +391,9 MB. In dieser Zahl steckt auch die
Tokenizer-Instanz, die `_load` für die Engine öffnet; hier ist der Tokenizer vor
der ersten Ablesung gebaut, und int8 kostet nur Session plus ersten Batch, rund
145 MiB. Der Unterschied ist die Tokenizer-Instanz, die der Grundlast-Bericht
mit 216 bis 266 MB misst (`docs/measurements/2026-09-grundlast-fein/README.md`,
Schritte 11b und 16). Mit fp32 wächst der Ladesprung der ersten Einbettung um die
367 MiB dieses Berichts, auf grob 760 MB.
