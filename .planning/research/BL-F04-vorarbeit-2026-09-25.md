# BL-F04 Vorarbeit (v1.4): Phase-22-Mitmessliste, Mehrkern-Rechnung, Profilschnitt

**Erstellt:** 2026-09-25
**Status:** Vorab-Research fuer den Milestone v1.4, VOR `/gsd:new-milestone`. Kein Plan, keine
Entscheidung, kein Code geaendert. Stand des Quelltexts: Arbeitsbaum vom 25.09.2026 (nach Phase 20).
**Verhaeltnis zur Vorgaengerin:** Baut auf `.planning/research/BL-F04-worker-skalierung.md` (24.09.)
auf und ersetzt sie NICHT. Was dort steht und hier nicht wiederholt wird, gilt weiter, mit den
fuenf Korrekturen aus Abschnitt 0.3.
**Zeitkritischer Teil:** Abschnitt 1 (Phase-22-Mitmessliste). Er muss in die Planung von Phase 22,
bevor deren Rechenblatt zum Owner geht.
**Konfidenz gesamt:** MEDIUM. Die Codebefunde sind HIGH (Zeilen gelesen), die Mehrkern-Rechnung ist
LOW-MEDIUM (gerechnet, zwei Eingangsgroessen ungemessen, genau die, die Abschnitt 1 beschafft).

---

## 0. Auf einen Blick

- **Der wichtigste Befund dieser Runde:** Waehrend der OCR-Spur laeuft tesseract seit dem 01.09.2026
  (Commit 5f4e314) mit `OMP_THREAD_LIMIT=1` (`backend/src/findling/extract/ocr.py:73`, gesetzt in
  Zeile 194), und die Poller-Schleife ist seriell (`backend/src/findling/worker/poller.py:803`). Auf
  der 2-Kern-Referenzbox liegt waehrend der OCR also **sehr wahrscheinlich ein Kern weitgehend
  brach**. Die Gegenbehauptung in `docs/performance.md:2886` ("tesseract nutzt auf dieser Maschine
  bereits beide Kerne fuer eine Seite") ist durch **keine einzige CPU-Messung** gedeckt: im ganzen
  Repo gibt es keine (grep ueber `docs/`, `docs/measurements/`, `scripts/ops/` nach vmstat, mpstat,
  cpu.stat, /proc/stat: null Treffer). Die Vorgaenger-Research hat den Satz uebernommen und daraus
  "auf zwei Kernen bringt ein zweiter Arbeiter fast nichts" abgeleitet. Das ist ungeprueft und
  wahrscheinlich falsch.
- **Die INDEX_WORKERS-A/B-Messung (802 s gegen 799 s) sagt nichts ueber Kerne**, sondern nur, dass
  die Konstante nirgends gelesen wird. Ernst genommen liefert sie zwei Dinge: den Beweis, dass es
  den Schalter nicht gibt, und eine **Rauschgrenze von 0,4 Prozent** fuer jede OCR-Wiederholmessung
  auf dieser Box. Beides wird in Abschnitt 1 benutzt.
- **Die Phase-22-Box kann die Mehrkern-Basiszahlen ohne Produktaenderung liefern**, wenn drei
  kleine Messwerkzeuge vorher boxlos gebaut werden und die Anfahrt am Ende einen Instanztyp-Wechsel
  auf eine 16-vCPU-Graviton3-Maschine macht (rund 1,25 h, rund 1,00 USD). Damit entfaellt die
  "Messphase auf einer groesseren Box" als eigene Entdeckungs-Anfahrt in v1.4. Eine
  Abnahme-Anfahrt fuer das GEBAUTE Mehr-Worker-Produkt bleibt in v1.4 unvermeidbar (Owner-Auflage
  "RAM-Messung je Stufe, BEVOR die Settings-UI ihn anbietet").
- **Gerechneter Lohn der Parallelitaet** (Abschnitt 2.4, LOW-MEDIUM): Erstindex 52k-Korpus heute
  19 h 20 min; mit echter Spur- und Slot-Parallelitaet rund 15 h auf 2 Kernen, rund 7 h auf 4,
  rund 3,5 bis 4 h auf 8 und rund 2 bis 3 h auf 16 Kernen, jeweils nur bei ausreichendem RAM.
- **Der erste Hebel ist nicht "N gleiche Worker", sondern "Einbettungsspur als eigener
  Nebenlaeufer"**: sie beruehrt den Tantivy-Writer nicht, teilt die threadsichere Engine und
  holt auf jeder Box ab 2 Kernen und 8 GB den gemessenen Aufschlag von +41 Prozent (5 h 15 min)
  weitgehend zurueck. Danach kommen N OCR-Slots.
- **Profile sollten Formeln mit Anteil an der Box sein, keine festen Zahlen**, sonst verschenkt
  "Leistung" auf 16 Kernen drei Viertel der Maschine. Dazu Hardware-Erkennung beim ersten Start mit
  Vorschlag, der erst nach Admin-Bestaetigung wirkt (Owner-Steuerung 25.09.).
- **Modellwechsel ist billiger als angenommen, hat aber eine Luecke:** die automatische
  Neu-Einbettung ueber die Marke `embedding_version` existiert seit E-H4 (06.09.,
  `docs/embeddings.md` Abschnitt 8). Die Marke enthaelt aber den Modell**namen**, nicht die
  Gewichtspraezision (`backend/src/findling/store/vectors.py:273`): int8 gegen fp32 desselben
  Modells wuerde heute **still gemischte Vektoren** erzeugen.

### 0.1 Owner-Steuerung 25.09.2026

Waehrend dieser Research eingegangen, verbindlich fuer die Gewichtung:

> Die MEHRHEIT der Findling-Nutzer hat nach Owner-Einschaetzung deutlich mehr Kerne und mehr RAM
> als die 4-GB-Referenzbox, und die Tendenz geht weiter in diese Richtung.

Konsequenzen, so umgesetzt:

1. **Nebenlaeufigkeit ist der Kernfall, nicht nachrangig.** Abschnitt 2 rechnet den Lohn fuer 4, 8
   und 16 Kerne durch, nicht nur die Schwelle.
2. **Profilschnitt mit Hardware-Erkennung und Profil-VORSCHLAG beim ersten Start** (erkannte Kerne
   und RAM, vorgeschlagenes Profil, Admin bestaetigt) statt reinem verstecktem Opt-in. Der
   Default-Fallback bleibt das 4-GB-Versprechen; Owner-Entscheid 24.09. bleibt gueltig: Sparsam ist
   der sichere Boden, kein Zwang. Siehe Abschnitt 3.
3. **Mitmessliste priorisiert Mehrkern-Zahlen** (tesseract-Skalierung je Kernzahl, RAM je
   zusaetzlichem Worker) vor Randposten. Siehe Abschnitt 1, Prioritaet 1.

### 0.2 Verbindliche Owner-Entscheide, die diese Research traegt

| Datum | Entscheid | Wirkung hier |
|---|---|---|
| 24.09.2026 | Default bleibt das 4-GB-Versprechen; Skalierung ist Opt-in ueber Worker-Zahl plus daranhaengende Deckel | Profil Sparsam wird Wert fuer Wert gepinnt (Abschnitt 3.2) |
| 24.09.2026 | BL-F04 ist Kern von v1.4 | diese Vorarbeit |
| 25.09.2026 | KEINE App-Spaltung, Leistung als Profil in derselben App | kein zweites Abbild; Neupruefung nur bei schweren Zusatzabhaengigkeiten (Abschnitt 5, K7) |
| 25.09.2026 | Mehrheit der Nutzer hat mehr Kerne/RAM (Abschnitt 0.1) | Gewichtung Abschnitte 1 bis 3 |

Nachfrage-Belege: drei Reddit-Signale (Neat_Supermarket_396, ayhamoo, budachst) zu Erstindex-Dauer
und Power-Settings; ayhamoo zusaetzlich Test-vor-Speichern-UI und groesseres Embedding-Modell
(`.planning/BACKLOG.md`, BL-F04).

### 0.3 Korrekturen an der Vorgaenger-Research vom 24.09.

| # | Dort | Richtig | Beleg |
|---|---|---|---|
| K1 | "auf zwei Kernen bringt ein zweiter Arbeiter fast nichts, weil zwei tesseract-Prozesse sich dieselben zwei Kerne teilen wuerden" | Ein tesseract mit `OMP_THREAD_LIMIT=1` belegt EINEN Kern. Der zweite ist waehrend der OCR nur durch Nextcloud/AIO, Hauptprozess und Download belegt. Der Gewinn auf 2 Kernen ist ungemessen, nicht null | `extract/ocr.py:73,194`; `worker/poller.py:803`; keine CPU-Messung im Repo |
| K2 | Kernregel `OCR-Slots = min(Kerne - 1, ...)` | `Kerne - r`, mit r = gemessene Kernbelegung durch Nextcloud und Hauptprozess waehrend der OCR. r ist die Zahl, die Mitmessung P22-B1/B2 liefert | Abschnitt 1 |
| K3 | Modellwahl "eigenes Vorhaben", weil Vektor-Reindex | Der Vektor-Reindex laeuft bereits automatisch (Marke leeren, Baender zu 500, Suche bleibt lexikalisch). Fehlend sind nur: Praezision in der Marke, Dimension als Konstante, Abbildgroesse | `docs/embeddings.md` Abschnitt 8; `store/vectors.py:81,87,273` |
| K4 | Zeilennummern | seit Phase 18 bis 20 verschoben: `settings()`-Cache jetzt `config.py:1240`, `WRITER_HEAP_BYTES` 256, `OCR_MAX_PAGES` 436, `OCR_JOB_SECONDS_MAX` 480, `EMBED_BATCH_SIZE` 634; Poller `run` 693, `run_once` 722, Schleife 803, Commit 821, Quittierung 854 | gelesen 25.09. |
| K5 | "Phase 3: Messphase auf einer groesseren Box" als eigene v1.4-Anfahrt | Die Basiszahlen dafuer passen in die Phase-22-Anfahrt (P22-B4) und teils kostenlos in CI (4-vCPU-arm64-Runner). v1.4 braucht nur noch die Abnahme-Anfahrt am gebauten Produkt | Abschnitt 1.4 |

---

## 1. Phase-22-Mitmessliste (WICHTIGSTES ERGEBNIS)

### 1.1 Randbedingungen

- **Was "ohne Produktaenderung" heisst:** Das Produktabbild wird per Digest gezogen und nicht
  veraendert. Erlaubt sind (a) Umgebungsvariablen, die `config.settings()` heute schon liest
  (`config.py:1279-1364`), (b) Messwerkzeuge unter `scripts/ops/` und (c) Wegwerf-Container
  desselben Digests mit `--entrypoint python`, genau wie `.github/workflows/measure.yml` es seit
  Welle 0 tut.
- **Heute per Umgebungsvariable stellbar:** `FINDLING_WRITER_HEAP_BYTES`, `FINDLING_OCR_DPI`,
  `FINDLING_OCR_MAX_PAGES`, `FINDLING_OCR_PAGE_SECONDS`, `FINDLING_OCR_JOB_SECONDS`,
  `FINDLING_EMBED_BATCH_SIZE`, `FINDLING_EMBED_SEQUENCE_LEN`, `FINDLING_BATCH_FILES`,
  `FINDLING_BATCH_MAX_BYTES`, `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES`,
  `FINDLING_EXTRACT_WORKER_MAX_FILES`, `FINDLING_EMBED_IDLE_RELEASE_SECONDS`.
- **Hart verdrahtet, also im Produkt NICHT messbar:** onnxruntime-Threads `THREADS = 2`
  (`embed/model.py:113`, benutzt 614), Tantivy `num_threads=1` (`index/writer.py:176` und
  `index/rebuild.py:561`), `OMP_THREAD_LIMIT=1` (`extract/ocr.py:73`), `INDEX_WORKERS = 1`
  (`config.py:81`, von niemandem gelesen). Diese Achsen sind nur ueber Wegwerf-Container
  messbar: `python -m findling.embed.bench --threads N` existiert (`embed/bench.py:767`), fuer
  tesseract und Slots fehlt ein Werkzeug (siehe 1.3).
- **Vergleichbarkeit der BL-F03-Zahlen geht vor.** Kein BL-F04-Block darf eine BL-F03- oder
  MESS-08/09-Messung veraendern: keine Umgebungsvariable des Produktcontainers wird vor Abschluss
  aller BL-F03-Schritte umgestellt, und jeder BL-F04-Block laeuft danach oder in einem getrennten
  Container. `scripts/ops/rss_sampler.sh` wird NICHT umgebaut (CSV-Format ist Vergleichsgrundlage),
  CPU kommt in ein eigenes Werkzeug.
- **Die Box:** m7g.large, 2 vCPU Graviton3, `mem=4G`, Containergrenze 2 GiB, eu-central-1c,
  Korpus aus `snap-03f1d1d9ad9262704` (`docs/runbook-messbox.md` Abschnitte 2 und 4). Auf
  Graviton ist jede vCPU ein physischer Kern (kein SMT) [ASSUMED, AWS-Standardaussage, nicht in
  dieser Sitzung nachgelesen]; die Kernzahl ist dort also sauberer als auf x86-Boxen.
- **BL-F03-Fenster** laut `.planning/BACKLOG.md`: 6 bis 10 Boxstunden, rund 1,0 bis 1,5 USD, ohne
  Volllauf; dazu kommt MESS-08 (Umbau-Wandzeit, geschaetzt 1 bis 3 h). Satz laufend 0,115841 USD/h
  (`docs/runbook-messbox.md` 2.3).

### 1.2 Die Liste, nach Prioritaet

Prioritaet 1 = stuetzt direkt die Mehrkern-Rechnung (Owner-Steuerung 25.09., Punkt 3).

| ID | Prio | Zahl, die entsteht | Messrezept (2 bis 3 Saetze) | Boxzeit | Werkzeug vorher | Sprengt das Fenster? |
|---|---|---|---|---|---|---|
| **P22-B1** | 1 | **Kernbelegung r** je Phase: Container und Box, waehrend Umbau (MESS-08), Bodensatz-Indexlauf, Laststufen, und in B2 waehrend OCR | `cpu_sampler.sh` laeuft ab Aufbau neben `rss_sampler.sh` und schreibt alle 5 s `usage_usec` aus der `cpu.stat` des Containers plus die Zeile `cpu` aus `/proc/stat` der Box. Kernbelegung = Delta usage_usec / Delta Wandzeit; Box-Leerlauf aus dem idle-Feld. Auswertung je Phase an den UTC-Stempeln der Bloecke | **0 min** zusaetzlich | W1 | nein |
| **P22-B2** | 1 | **OCR-Durchsatz und Kernbelegung unter Produktlast**, und die **Zerlegung des OCR-Aufschlags nach Prozess** (die ungeklaerten rund 400 MB zwischen 225 bis 325 MB Einzelposten und 676,6 MB Phasenaufschlag) | Nach allen BL-F03-Produktmessungen einen frischen Ordner per WebDAV fuellen: 120 einseitige plus 20 achtseitige Scans aus dem synthetischen Generator, danach `files:scan`, Muster der Nachmessung vom 07.09. (dort 120 Scans in 8 min 36 s). Neben B1 laeuft `proc_anon_sampler.sh` (W2) und liest alle 5 s `RssAnon` und `VmHWM` je Prozess im Container (Hauptprozess, Sandbox-Kind, tesseract-Enkel). Ergebnis: s je Datei, s je Seite, r, anon je Prozess, Spitze | **rund 40 min** (Upload 5, Lauf rund 25, Auswertung 5, Reserve 5) | W1, W2, Scan-Material | nein, im Fenster |
| **P22-B3** | 1 | **RAM je zusaetzlichem OCR-Slot** und **Durchsatzfaktor 2 Slots auf 2 Kernen**, am echten Extraktionspfad | Wegwerf-Container desselben Digests (`--network none`, `--cpuset-cpus 0,1`, `--memory 2g`), darin `ocr_slot_probe.py` (W3): N Threads mit je eigener `ExtractionWorker`-Instanz (`extract/sandbox.py:287`), jede liest denselben achtseitigen Scan ueber den OCR-Pfad, N = 1 und 2, je 3 Runden. Gemessen: Wandzeit, Seiten je Sekunde, anon der eigenen cgroup je N (Delta = Kosten je Slot), CPU-Zeit der Kinder. Zusatzmodus: ein tesseract-Aufruf mit `OMP_THREAD_LIMIT=1` gegen unset, prueft `docs/performance.md:2886` direkt | **rund 15 min** | W3 | nein |
| **P22-B4** | 1 | **Kernskalierung auf Zielarchitektur fuer 1, 2, 4, 8, 12, 16 Kerne**: tesseract-Slots und onnx-Threads, plus RAM je Slot bis N = 16 | Letzter Block vor dem Abbau: Box anhalten, `modify-instance-attribute` auf **m7g.4xlarge** (16 vCPU), starten, AIO NICHT hochfahren (nicht noetig). B3-Werkzeug mit `--cpuset-cpus 0-(N-1)` fuer N = 1, 2, 4, 8, 12, 16, danach `python -m findling.embed.bench --mode tokens-per-second --batch 2 --sequence 512 --threads T` fuer T = 1, 2, 4, 8 auf passendem cpuset. `mem=4G` darf bleiben (16 Slots gerechnet rund 1,8 bis 3,2 GB), die Grenze wird im Protokoll gefuehrt | **rund 75 min** inkl. Stop/Typwechsel/Start (rund 10 min) und Adress-Handgriff | W3 | **verlaengert es um rund 1,25 h und rund 1,00 USD** (eigener Deckelposten, eigene Owner-Freigabe) |
| **P22-B5** | 2 | **onnx-Durchsatz und Aktivierungsspeicher auf Graviton3**, threads 1 gegen 2, batch 2 gegen 8 | Wegwerf-Container, `--cpuset-cpus 0,1`, `embed.bench --mode tokens-per-second --sequence 512` in vier Kombinationen; `rss_sampler.sh` gegen den Bench-Container liefert max anon je Kombination. Heute gibt es Bench-Zahlen nur von zwei Neoverse-N2-Kernen im CI-Runner und nur mit `--threads 2` (`docs/measurements/2026-09-05-welle0-arm64/`) | **rund 12 min** | keines (Bench existiert) | nein |
| **P22-B6** | 2 | **Ist der Umbau einkernig?** Kernbelegung waehrend MESS-08 | faellt aus B1 ab. Liegt r waehrend des Umbaus bei rund 1,0 von 2 und dauert er ueber 1 h, ist Tantivy `num_threads` ein v1.4-Hebel fuer den Umbauweg (heute hart 1 in `rebuild.py:561`); die Vergleichsmessung dazu gehoert in CI, nicht auf die Box | **0 min** | W1 | nein |
| P22-B7 | 3 | NL-Automat nativ ARM (17,6 MB bestaetigen) | Nur mitnehmen, wenn die Grundlast-Reihe ohnehin laeuft (Schritt "niederlaendischer Automat gebaut"). Sonst im CI-arm64-Runner: dort ist die Hardware nativ, und die Praezedenz sagt amd64 gegen natives arm64 unter 0,5 MB auseinander und Runner gegen Box 543,7 gegen 542,8 MB (`docs/measurements/2026-09-grundlast-fein/README.md`). qemu-Werte bleiben unbrauchbar (`21-RESEARCH.md:202`) | 0 bis 5 min | keines | nein |
| P22-B8 | gestrichen | Bodensatz unter `FINDLING_EMBED_BATCH_SIZE=8` im Produkt | NICHT fahren: braucht eine Neuregistrierung des Containers mit geaenderter Umgebung (Rueckgriff auf den Wechselpfad, 30 min und mehr, Fehlerpfade dokumentiert in `docs/runbook-messbox.md` 2.1) und stoert den Bodensatz-Zyklus 2 als Vergleich. Der Aktivierungsspeicher je Batch kommt billiger aus B5 | - | - | - |
| P22-B9 | gestrichen | Kaltstart unter groesseren Deckeln | NICHT fahren: kein Wirkzusammenhang. Kaltstart ist mmap-Seitencache plus Gewichte-Laden (`docs/performance.md`, Wiederaufwaerm-Nachtrag 21.09.); die BL-F04-Deckel wirken auf Writer-Heap, OCR und Batch, nicht auf den Suchpfad | - | - | - |
| P22-B10 | gestrichen | zweiter Umbau mit `FINDLING_WRITER_HEAP_BYTES=128000000` | NICHT fahren: verdoppelt den teuersten MESS-08-Posten (1 bis 3 h). Heap und Threads des Writers sind laut Vorgaenger-Research nicht der Erstindex-Flaschenhals; fuer den Umbau reicht B6 als Entscheidungsgrundlage | - | - | - |

### 1.3 Werkzeuge, die VOR der Anfahrt boxlos stehen muessen

Alle drei sind Werkzeuge und keine Produktaenderung. Sie gehoeren als eigener Wave-0-Plan in
Phase 22 und werden im CI-arm64-Runner erstmals gefahren, damit der Erstvollzug nicht in die
bezahlte Zeit faellt (Lehre aus Phase 15: drei Laeufe fuer den Abbildwechsel,
`docs/runbook-messbox.md` 2.1).

| ID | Werkzeug | Inhalt | Regel |
|---|---|---|---|
| W1 | `scripts/ops/cpu_sampler.sh` | liest `cpu.stat` der Container-cgroup (Pfadbildung wie `rss_sampler.sh`) und `/proc/stat` der Box; Praefixzeilen, Abschlusszeile mit Mittel und Maximum der Kernbelegung | eigenes Skript, `rss_sampler.sh` bleibt unveraendert; verweigert statt Nullen zu schreiben, wie das Vorbild |
| W2 | `scripts/ops/proc_anon_sampler.sh` | `docker exec` in den Container, je Prozess `Name`, `RssAnon`, `VmHWM` aus `/proc/<pid>/status` | nur Zahlen und Prozessnamen, keine Kommandozeilen (Pfade von Nutzerdateien koennten darin stehen, T-02-14) |
| W3 | `scripts/ops/ocr_slot_probe.py` | N Threads, je eine `ExtractionWorker`, OCR-Route, eine synthetische Scan-PDF; misst Wandzeit, Seiten/s, anon der eigenen cgroup, CPU-Zeit der Kinder (`resource.getrusage(RUSAGE_CHILDREN)`); Modus `single` fuer den tesseract-Einzelvergleich `OMP_THREAD_LIMIT` 1 gegen unset | druckt `arch`, sichtbare CPUs (`sched_getaffinity`, wie `embed/bench.py:169`) und nie ein Wort des gelesenen Textes (T-02-14); laeuft im Wegwerf-Container desselben Digests |
| W4 | Erweiterung `.github/workflows/measure.yml` | Lauf auf `ubuntu-24.04-arm` (4 vCPU, 16 GB, Neoverse N2) mit W3 fuer N = 1, 2, 4 und `embed.bench --threads` 1, 2, 4 | kostenlos; liefert die 4-Kern-Vorabkurve und entscheidet, ob B4 noch noetig ist (siehe 1.4) |

**Scan-Material:** synthetische Seiten aus dem Korpus-Generator des Projekts (Reproduzieren-Abschnitt
in `docs/performance.md`), niemals Nutzerdateien. Die Probe braucht mindestens eine achtseitige
Scan-PDF ohne Textschicht; sie wird in den Wegwerf-Container gemountet, nicht ins Abbild gebaut.

### 1.4 CI zuerst, Box fuer die Zielarchitektur

Der oeffentliche arm64-Runner hat 4 vCPU und 16 GB [CITED: docs.github.com/en/actions/reference/runners/github-hosted-runners].
Das Projekt nutzt ihn schon (`measure.yml:104`, `python.yml:185`). Daraus folgt eine Aufteilung,
die Boxgeld spart, ohne Zahlen zu verlieren:

| Frage | CI-arm64 (kostenlos, N2, 4 Kerne, verrauscht) | Box m7g.large (Graviton3, 2 Kerne, AIO-Last) | Box m7g.4xlarge (Graviton3, 16 Kerne) |
|---|---|---|---|
| tesseract-Skalierung 1, 2, 4 | ja, Vorabkurve | 1, 2 | 1 bis 16 |
| tesseract-Skalierung 8, 12, 16 | nein | nein | **nur hier** |
| RAM je Slot | ja (native Hardware, RSS gueltig) | ja, unter echter 2-GiB-Grenze | ja, bis N = 16 |
| Kernbelegung r unter Nextcloud-Last | nein | **nur hier** | nein |
| onnx-Threads 1, 2, 4 | ja | 1, 2 | 1 bis 8 |
| NL-Automat nativ | ja | optional | nein |

**Empfehlung:** W4 in CI fahren, bevor das Phase-22-Rechenblatt zum Owner geht. Zeigt die
CI-Kurve auf 4 Kernen einen Slot-Faktor von 3 oder mehr, ist B4 der Beleg fuer 8 und 16 Kerne und
unbedingt zu fahren (Owner-Steuerung: Mehrheit der Nutzer hat mehr Kerne). Zeigt sie unter 1,5,
kippt Stufe 2 von BL-F04 (siehe Abschnitt 5, K1), und B4 kann entfallen.

### 1.5 Reihenfolge innerhalb der Anfahrt

1. Aufbau, Abbildwechsel, B1 startet mit dem ersten Container (neben `rss_sampler.sh`).
2. Alle BL-F03-Punkte und MESS-08/09 unveraendert nach ihrem eigenen Plan (B6 faellt dabei ab).
3. **B2** (Produkt-Indexlauf, deshalb nach allen BL-F03-Produktmessungen, insbesondere nach
   Kaltstart und Bodensatz-Zyklus 2).
4. **B3** und **B5** in Wegwerf-Containern, Produktcontainer im Leerlauf, Arbeitsvorrat null
   (sonst misst die Probe die Poller-Last mit).
5. Endmessungen und Gegenproben nach Runbook 8, Schritt 1, solange AIO laeuft.
6. **B4**: Stop, Typwechsel, Start, Proben, Stop.
7. Abbau nach Runbook 8 ab Schritt 2. Kein Ende-Snapshot noetig: die B2-Dateien sollen gerade NICHT
   in den Korpus-Snapshot gelangen (in v1.2 wurde ebenfalls keiner gezogen).

**Warum B4 zuletzt:** Nach dem Typwechsel aendert sich die oeffentliche Adresse (Runbook Block 10,
Rueckfall 1), und die Box ist keine Referenzbox mehr. Jede Messung danach waere mit der 4-GB-
Referenz unvergleichbar. Kapazitaet fuer m7g.4xlarge in eu-central-1c ist [ASSUMED]; Rueckfall ist
m7g.2xlarge (8 vCPU), dann fehlen die Stufen 12 und 16.

### 1.6 Rechenblatt-Zusatz fuer Phase 22

| Posten | Stunden | Satz | USD |
|---|---:|---|---:|
| B1, B6 | 0,00 | - | 0,00 |
| B2 | 0,67 | 0,115841 | 0,08 |
| B3 | 0,25 | 0,115841 | 0,03 |
| B5 | 0,20 | 0,115841 | 0,02 |
| B4 | 1,25 | rund 0,80 (m7g.4xlarge rund 0,7824 plus Speicher und IPv4 rund 0,018) | 1,00 |
| Summe | 2,37 | | 1,13 |
| mit 15 Prozent Zuschlag (Runbook 2.5) | **2,7 h** | | **1,30 USD** |

Der m7g.4xlarge-Satz ist gerechnet als achtfacher m7g.large-Satz (0,0978 USD/h, Runbook 2.3); die
Linearitaet innerhalb der Familie stuetzt eine Drittquelle fuer m7g.xlarge mit 0,1955 USD/h in
eu-central-1, also genau dem Doppelten [MEDIUM: doit.com, nicht die AWS-Preisliste]. **Am
Anfahrtstag mit `aws_box.sh prices` bzw. der Preis-API gegenlesen**, wie das Runbook es fuer den
Grundsatz verlangt; `aws_box.sh` pinnt heute nur m7g.large.

**Verdikt:** Ohne B4 bleibt die Anfahrt klar im BL-F03-Fenster (plus rund 1,1 h, plus rund 0,15 USD).
Mit B4 verlaengert sie sich um rund 2,7 h und rund 1,30 USD gegenueber dem BL-F03-Plan. Das sprengt
das Fenster nicht, aber es ist ein eigener Deckelposten mit eigener Owner-Freigabe.

---

## 2. Nebenlaeufigkeit: der Kernfall

### 2.1 Was heute seriell ist, mit Codestellen (Stand 25.09.)

| Baustein | Stelle | Form heute | Was fuer N Slots fehlt |
|---|---|---|---|
| Runde | `worker/poller.py:722` `run_once` | Anspruch, dann `for job in claim.jobs` (803), jedes `await` abgewartet | Aufteilung nach Spur, Semaphore je Spur, Zusammenfuehren der Ergebnislisten vor Schritt 2 |
| Commit | `poller.py:821` | ein `flush` je Runde, danach Verdikte (831), Uebergabe (846/847), Quittierung (854) | bleibt seriell am Rundenende (Zusage "mindestens einmal ausliefern, hoechstens einmal indexieren") |
| Extraktion | `extract/sandbox.py:287` `ExtractionWorker` | "Holds exactly one extraction child", Recycling nach 200 Dateien (`config.py:237`) | N Instanzen, je eigene Pipe und eigener Zaehler; die Klasse ist dafuer schon geschnitten (Zustand je Instanz) |
| OCR je Datei | `extract/ocr.py:154` | Seitenschleife seriell, `render_page_png` (161) dann `read_page` (178) | optional Seiten-Parallelitaet; fuer grosse Korpora reicht Datei-Parallelitaet |
| tesseract | `extract/ocr.py:73,194` | `OMP_THREAD_LIMIT=1`, Teil der Speicherzusage (`docs/ocr.md` Messung 2 und 3) | unveraendert lassen; Skalierung ueber Prozesse, nie ueber Threads |
| Einbettung | `poller.py:953` | `embed`-Zeilen laufen in derselben Schleife, nach Prioritaet hinter `ocr` | eigener Nebenlaeufer; Engine ist threadsicher (`embed/model.py`, Modulkommentar, Vorgaenger 1.3) |
| onnx-Threads | `embed/model.py:113,337,614` | hart 2, `inter_op` 1 | Profilwert |
| Tantivy-Writer | `index/writer.py:176` | ein Writer, `num_threads=1`, Heap aus Settings | eine Sperre um `add()` (unbewachte Zaehler, Vorgaenger R4), `num_threads` als Profilwert |
| Anspruch PHP | `php/lib/Service/QueueService.php:146-153,188-222` | `KIND_BATCH[ocr] = 2`, `[embed] = 8`, `[content] = 32`; Arten nacheinander in der Reihenfolge von `QueueMapper::KINDS` (75-82), kein Filter nach Art | Parameter "nur diese Arten" am Anspruch (fuer einen eigenen Einbettungs-Nebenlaeufer) und `KIND_BATCH[ocr]` mindestens N; beides `private const`, also Companion-Release |
| Sperrfrist | `php/lib/Db/QueueMapper.php:136` `LOCK_TIMEOUTS` | OCR 1800 s; Python leitet daraus `OCR_JOB_SECONDS_MAX` ab (`config.py:480`) | parallele Bearbeitung der Zeilen eines Anspruchs entspannt die Rechnung (Vorgaenger 2.3 Punkt 3); bei `KIND_BATCH[ocr] = 2N` die Ableitung neu fassen |
| Einstellungen | `config.py:1240` `@lru_cache` | eingefroren fuer die Prozesslebensdauer | Weg fuer Profil in den Container (Vorgaenger 6.4, Wege A, B, C) |

### 2.2 Architekturskizze: drei Spuren, ein Schreiber

```
 Nextcloud-Warteschlange (PHP, Anspruch je Art)
        |
        |  claim(kinds=[acl,delete,metadata,content,ocr])      claim(kinds=[embed])
        v                                                        v
 +---------------- Indexrunde (Nebenlaeufer 1) ---------+   +-- Einbettungsspur (Nebenlaeufer 2) --+
 |  Text-Slots (Semaphore n_text, I/O-lastig)           |   |  Embed-Slots (Semaphore n_embed)     |
 |     Abholen -> ExtractionWorker[i] -> Ergebnis       |   |     gespeicherter Text aus Tantivy   |
 |  OCR-Slots (Semaphore n_ocr, CPU-lastig)             |   |     -> geteilte Engine (1x Gewichte) |
 |     Abholen -> ExtractionWorker[j] -> tesseract      |   |     -> vectors.db (eigene Datei)     |
 |  Speicherwaechter drosselt n_ocr bei knapper cgroup  |   |  Quittierung eigener Zeilen          |
 +--------------------------+---------------------------+   +--------------------------------------+
                            | Ergebnisse zusammenfuehren
                            v
          ein Schreib-Thread: IndexBatchWriter.add() (Sperre)
                            v
          Commit -> Verdikte (state.db) -> Uebergabe ocr/embed -> Quittierung   (seriell, wie heute)
```

Zwei Eigenschaften machen diesen Schnitt billiger als "N gleiche Worker":

1. **Die Einbettungsspur beruehrt den Tantivy-Writer nicht.** Sie liest den gespeicherten Text und
   schreibt in `vectors.db` (`docs/embeddings.md` Abschnitt 7). Ein eigener Nebenlaeufer braucht
   also keine Writer-Sperre und kollidiert nicht mit der Commit-Reihenfolge. Die Kollisionsstellen
   sind nur `state.db` (WAL, `busy_timeout` 10 s, Vorgaenger R3) und der Anspruch.
2. **OCR-Slots teilen nichts ausser dem Writer am Rundenende.** Jeder Slot hat sein
   Sandbox-Kind, seine Scratch-Datei (`job-{queue_id}.part`, schon kollisionsfrei) und seinen
   tesseract-Enkel.

IDX-08 ("OCR und Einbettung nie gleichzeitig") ist im Kern die Regel "zwei Spitzen treffen sich auf
4 GB nicht". Im Profil Sparsam bleibt sie woertlich; in Standard und Leistung wird sie zur
RAM-Bedingung des Speicherwaechters.

### 2.3 Hebel, nach Lohn je Aufwand geordnet

| Stufe | Hebel | Lohn (gerechnet) | Aufwand | Risiko |
|---|---|---|---|---|
| H0 | Profilwerte ohne Nebenlaeufigkeit: onnx-Threads, Tantivy-Heap und `num_threads`, `OCR_MAX_PAGES` nachgerechnet | klein: nur die Einbettung (5 h von 19 h) profitiert von mehr onnx-Threads, und intra-op skaliert unterlinear [ASSUMED]; Seitendeckel bringt Vollstaendigkeit statt Tempo | klein | gering |
| **H1** | **Einbettungsspur als eigener Nebenlaeufer** | holt den gemessenen Aufschlag der ersten Spur (12 h 49 min auf 18 h 04 min, +41 Prozent) weitgehend zurueck, sobald ein Kern frei ist; auf 2 Kernen gerechnet von rund 19 h auf rund 13 bis 15 h | mittel: zweiter Nebenlaeufer, Art-Filter am Anspruch (PHP), Abbruchsemantik | mittel: `state.db`-Kollisionen, RAM (Aktivierungen gleichzeitig mit OCR-Spitze) |
| **H2** | **N OCR-Slots** | der grosse Hebel auf Mehrkern-Boxen: die OCR-Spur (85 Prozent der Uhr der ersten Spur, Vorgaenger 1.1) teilt sich fast linear auf die freien Kerne | gross: Semaphore, N Sandbox-Kinder, Writer-Sperre, Speicherwaechter, `KIND_BATCH[ocr]` | mittel bis hoch: OOM-Kette (Vorgaenger R1), Abbruch halber Staffeln |
| H3 | Text-Slots | Textspur ist 1 h 54 min von 19 h; Ueberlappung des Gateway-Wartens spart hoechstens einen Teil davon | mittel (faellt mit H2 fast umsonst ab) | gering |
| H4 | Seiten-Parallelitaet in einer Datei | nur wichtig fuer Instanzen mit wenigen, langen Scans; bei vielen Dateien deckt H2 dasselbe ab | mittel | mittel (Timeout je Seite, `killpg`-Baum) |

**Antwort auf "ist Worker-Parallelitaet der richtige erste Hebel?":** Nein, wenn damit N gleiche
Worker gemeint sind. Der richtige erste Hebel ist H1, weil er die teuerste Invariante (ein
Tantivy-Writer) gar nicht beruehrt und auf jeder Box ab 2 Kernen wirkt. Die billigen Konfig-Hebel
H0 gehoeren ins Profil-Geruest, bringen aber allein keine spuerbare Erstindex-Verkuerzung. Der
eigentliche Mehrkern-Gewinn kommt erst mit H2.

### 2.4 Lohnrechnung fuer 2, 4, 8 und 16 Kerne

**Status: gerechnet, LOW-MEDIUM.** Zwei Eingangsgroessen sind ungemessen und genau die, die
P22-B1 bis B4 liefern.

**Arbeit in Kern-Stunden, aus gemessenen Wandzeiten** (Korpus rund 52k, m7g.large):

| Posten | Wandzeit gemessen | Kernbelegung | Kern-Stunden | Quelle |
|---|---|---|---|---|
| OCR-Spur | 39.285 s = 10,9 h | rund 1,0 [ASSUMED, B1/B2 misst] | rund 10,9 | performance.md "Die beiden Spuren" |
| Text und Crawl | 6.842 s = 1,9 h | 0,5 bis 1,0 [ASSUMED] | 1,0 bis 1,9 | ebenda |
| Einbettung allein | 51.961 Dok. / rund 170 je min = rund 5,1 h | rund 1,6 bis 2,0 bei 2 onnx-Threads [ASSUMED] | 8 bis 10 | embeddings.md Abschnitt 7 |
| **Summe** | | | **rund 20 bis 23** | |

Gegenprobe: heute 19 h 20 min Wandzeit (v1.2-Anfahrt) fuer rund 21,5 Kern-Stunden, also rund 1,1
belegte Kerne im Mittel auf einer 2-Kern-Box. Das passt zur Hypothese K1.

**Modell:** Wandzeit(C) = Arbeit / (C - r) + Boden. r = Kernbelegung durch Nextcloud/AIO und den
Hauptprozess, angesetzt 0,5 [ASSUMED, B1/B2 misst]. Boden = serielle Anteile: Rundenende (Commit,
Verdikte, Quittierung), Anspruchs-HTTP, der letzte grosse Scan, der Nachlauf der Einbettung;
angesetzt 0,5 bis 1,0 h [ASSUMED].

| Kerne C | effektiv C - r | Wandzeit ideal | Faktor gegen heute | RAM-Bedarf der Slots (Band 200 bis 680 MB je OCR-Slot) | realistische Erwartung |
|---:|---:|---:|---:|---|---|
| 2 | 1,5 | 14,3 h + 0,5 = **rund 15 h** | 1,3 | 1 bis 2 Slots; auf 4 GB NICHT (235 MB Luft), ab 8 GB ja | 13 bis 16 h; der Gewinn kommt fast nur aus H1 |
| 4 | 3,5 | 6,1 h + 0,7 = **rund 7 h** | 2,8 | 3 Slots: 0,6 bis 2,0 GB ueber Grundlinie | 7 bis 9 h |
| 8 | 7,5 | 2,9 h + 0,8 = **rund 3,7 h** | 5,2 | 7 Slots: 1,4 bis 4,8 GB | 3,5 bis 5 h |
| 16 | 15,5 | 1,4 h + 1,0 = **rund 2,4 h** | 8 | 15 Slots: 3,0 bis 10,2 GB | 2 bis 4 h; Boden und Nextcloud-Seite dominieren |

Lesart:

- **Ab 4 Kernen lohnt Parallelitaet deutlich** (Faktor rund 3), auf 2 Kernen maessig (rund 1,3, fast
  nur ueber H1). Die frueher angesetzte Schwelle "ab 4 Kernen" stimmt also im Ergebnis, aber aus
  einem anderen Grund: nicht weil 2 Kerne nichts bringen, sondern weil auf 2 Kernen Nextcloud den
  zweiten Kern teilweise braucht.
- **Auf 16 Kernen ist der Boden die Grenze, nicht die Kerne.** Ab rund 8 Kernen muss der v1.4-Plan
  die seriellen Anteile angehen: groessere Ansprueche (`KIND_BATCH`), Rundenende seltener, und die
  Nextcloud-Seite (PHP-Prozesspool der Instanz liefert die Dateien; seine Groesse ist je
  Installation anders, Vorbehalt aus der Nebenlaeufigkeitszusage in `docs/performance.md`).
- **RAM bestimmt die Slotzahl frueher als die Kerne**, sobald das Band am oberen Rand liegt. Eine
  16-Kern-Box mit 16 GB traegt beim pessimistischen Band nur rund 10 Slots. Deshalb ist P22-B3/B4
  ("RAM je Slot") gleichrangig mit der Skalierung.
- **x86-Boxen:** tesseract ist dort je Kern schneller (x86-Mietbox 2.517 ms gegen ARM 3.557 ms je
  Seite, performance.md), die absoluten Zeiten fallen also kuerzer aus. vCPU sind dort oft
  Hyperthreads; zwei Slots auf einem Kernpaar bringen erfahrungsgemaess deutlich weniger als zwei
  Kerne [ASSUMED]. Die Erkennung muss physische Kerne zaehlen oder die Probe aus Abschnitt 4 die
  echte Skalierung messen lassen.

### 2.5 Was die A/B-Messung fuer die Rechnung heisst

- Sie beweist, dass es keinen Schalter gibt (Definition plus zwei Kommentare, niemand liest den
  Wert; heute weiterhin nur `config.py:81`).
- Sie liefert die Wiederholbarkeit: 802 s gegen 799 s, 0,4 Prozent. **Jeder in B3/B4 gemessene
  Faktor unter rund 1,05 ist Rauschen**, darueber ein Befund.
- Sie liefert eine Kernzahl NICHT. Die Aussage in ihrer Antworttabelle, tesseract nutze bereits
  beide Kerne, steht dort ohne Messung und widerspricht `OMP_THREAD_LIMIT=1`. B3 prueft sie in
  15 Minuten. Faellt sie, gehoert `docs/performance.md:2886` mit Datum berichtigt (Nachtrag, nicht
  Ersetzung, nach der Hauskonvention).

---

## 3. Profilschnitt

### 3.1 Grundsatz: Profil = Anteil an der Box plus Obergrenzen, nicht feste Slotzahl

Findling teilt die Box mit Nextcloud (AIO: PHP, Datenbank, Cron, HaRP). Ein Profil mit fester Zahl
"4 OCR-Slots" waere auf 16 Kernen Verschwendung und auf einem 2-Kern-VPS mit 16 GB schaedlich.
Deshalb bestimmt das Profil, **welchen Anteil der erkannten Kerne und des erkannten Speichers
Findling nehmen darf**, und die Slotzahl folgt aus der Regel:

```
OCR-Slots = max(1, min( floor(Anteil_Kerne x C - r),  floor((M_frei - Grundlinie - Reserve) / Kosten_je_Slot) ))
```

C = erkannte nutzbare Kerne, r = Kernbelegung Nextcloud (Startwert 0,5, gemessen in P22-B1),
M_frei = Speichergrenze des Containers oder, ohne Grenze, verfuegbarer Speicher der Box,
Kosten_je_Slot = gemessen in P22-B3/B4.

### 3.2 Die drei Profile, Startwerte

Werte fuer Standard und Leistung sind Vorschlaege zur Messung, nicht zur Auslieferung.

| Knopf | Sparsam (Default, 4-GB-Versprechen) | Standard | Leistung |
|---|---|---|---|
| Wann vorgeschlagen | immer als Fallback; Erkennung unter 6 GB oder unter 3 Kernen | ab 6 GB und 3 Kernen | ab 12 GB und 6 Kernen |
| Anteil Kerne / Speicher | fest 1 Slot, keine Anteile | 50 Prozent / 40 Prozent | Kerne minus 1 / 60 Prozent |
| OCR-Slots | 1 | nach Regel, Obergrenze 4 | nach Regel, Obergrenze 16 |
| Text-Slots | 1 | 2 x OCR-Slots, max 8 | 2 x OCR-Slots, max 16 |
| Einbettungsspur | in derselben Schleife (IDX-08 woertlich) | eigener Nebenlaeufer (H1), 1 Slot | eigener Nebenlaeufer, 2 Slots |
| onnx `intra_op` je Embed-Slot | 2 (heute hart) | 2 | min(4, Kerne/4) [zu messen in B4] |
| Tantivy heap / `num_threads` | 50 MB / 1 | 128 MB / 2 (8-GB-Schablone CLAUDE.md) | 256 MB / 2 |
| `EMBED_BATCH_SIZE` | 2 | 2 (Batch 8 brachte auf aarch64 nichts, `config.py:626-634`) | 2, Batch 8 nur wenn B4 bei mehr Threads einen Gewinn zeigt |
| `OCR_MAX_PAGES` | 30 | 100 (zulaessig, Rechnung Vorgaenger 3.2) | 150 |
| `OCR_DPI` | 300 | 300 | 300 (hoeher kostet Adressraum, `config.py:484`, und bringt fuer Suche wenig [ASSUMED]) |
| Modell | e5-small int8 | e5-small int8 | e5-small int8; fp32 als eigener Schalter (3.5) |
| Speicherwaechter | aus (Verhalten wie heute) | an, Reserve 20 Prozent | an, Reserve 15 Prozent |

**Sparsam wird Wert fuer Wert gegen die heutigen Konstanten gepinnt** (Test wie heute
`backend/tests/test_config.py` fuer `INDEX_WORKERS`), damit die Store-Zahl 1.812,7 MB nicht wandert
(Vorgaenger R6). Die 8-GB-Schablone aus CLAUDE.md ("Stack Patterns by Variant") ist der Startpunkt
von Standard; ihre Zeile "Batchgroesse 8" ist durch Welle 0 ueberholt.

### 3.3 Hardware-Erkennung mit Profil-Vorschlag (Owner-Steuerung 25.09.)

**Ablauf beim ersten Start und nach jedem Hardwarewechsel:**

1. Container liest beim Start: Kerne als Minimum aus `os.process_cpu_count()` (Python 3.13) und der
   Quote in `/sys/fs/cgroup/cpu.max`; Speicher aus `/sys/fs/cgroup/memory.max`, bei `max` aus
   `/proc/meminfo` (`MemTotal` und `MemAvailable`); Architektur (Vorgaenger 6.1, belegt).
2. Er rechnet das vorgeschlagene Profil nach 3.2 und meldet **erkannt** und **vorgeschlagen** ueber
   die bestehende Statusroute an die Admin-Seite. Er schaltet NICHTS um.
3. Die Admin-Seite zeigt einen Hinweis: erkannte Kerne und Speicher, vorgeschlagenes Profil, zwei
   Knoepfe ("Uebernehmen und pruefen", "Beim sicheren Standard bleiben"). Ohne Klick bleibt
   Sparsam. Kein Zwang, Owner-Entscheid 24.09.
4. "Uebernehmen und pruefen" startet die Vorab-Pruefung aus Abschnitt 4; erst bei Verdikt "passt"
   wird das Profil gespeichert.
5. Aendert sich die erkannte Hardware spaeter nach unten (Umzug auf kleinere Box), faellt der
   Container selbsttaetig auf die groesste noch passende Stufe zurueck und sagt das auf der Seite.
   Nach oben schlaegt er nur vor.

**Fallen der Erkennung, die der Plan kennen muss:**

| Falle | Folge | Gegenmittel |
|---|---|---|
| Kein Speicherlimit am Container (`memory.max` = `max`) | `MemTotal` ist der Speicher der ganzen Box, den Nextcloud und Datenbank mitbenutzen | `MemAvailable` im Leerlauf mal Profil-Anteil, nicht `MemTotal`; ob AppAPI/HaRP den ExApp-Container heute ueberhaupt begrenzt, ist ungeprueft [ASSUMED: meist nicht] |
| `os.cpu_count()` meldet Host-Kerne | Profil zu gross | `process_cpu_count()` und `cpu.max`, Minimum (Vorgaenger 6.1) |
| x86 mit SMT | vCPU doppelt gezaehlt | Probe misst echte Skalierung (Abschnitt 4), die Erkennung schlaegt nur vor |
| Box mit vielen Kernen, aber langsamer Platte oder kleinem PHP-Pool | Slots warten auf Nextcloud | Speicherwaechter plus gemessene Raten der Statusseite (`GET /rates`) zeigen es; kein Automatismus |
| Raspberry Pi 5, 8 GB, 4 Kerne, Drosselung bei Waerme | Probe gruen, Dauerlauf langsamer | Hinweis im Verdikt "Kurzprobe, kein Dauerlauf"; nicht loesbar in einer Probe |

**ADM-04 bleibt gewahrt:** ein Auswahlfeld plus ein Hinweis, kein Erweitert-Bereich
(`docs/admin-page.md`, "Was die Seite bewusst nicht kann"; Vorgaenger 6.5). Die Einzelwerte bleiben
Umgebungsvariablen; eine gesetzte Umgebungsvariable ueberstimmt das Profil (Vorgaenger 6.4, eine
Wahrheit).

### 3.4 Wechselmechanik: was einen Reindex braucht und was nicht

| Knopf | wirkt ab | Reindex? | Mechanik heute |
|---|---|---|---|
| Slots, Threads, Heap, Batch, Speicherwaechter | naechster Start (Weg A) oder naechste Runde (Weg B/C) | **keiner** | Profil-Geruest |
| `OCR_MAX_PAGES` hoch | nur fuer neu oder geaendert gelesene Scans | optional: gezielt die Dateien mit Verdikt `indexed(truncated)` neu vorlegen | Zustand `truncated` ist gespeichert (`store/repo.py:248`, `extract/errors.py:56`), deckt aber auch den Textdeckel ab; ein Nachholweg fehlt |
| `OCR_DPI`, OCR-Sprachen | nur fuer neu gelesene Scans | optional; keine Marke fuer OCR-Einstellungen | nicht vorhanden |
| Sprachen der Suche | Umbau | **Tantivy-Umbau** (Phase 18, `index/rebuild.py`) | vorhanden |
| Modell gleiches, Gewichte int8 zu fp32 | Neustart | **Vektor-Reindex** (vectors.db), Tantivy unberuehrt | automatisch ueber `embedding_version`, ABER die Marke ist `model/int8/384/tokens` (`store/vectors.py:273`) und enthaelt die Gewichtspraezision NICHT: der Wechsel wuerde **nicht erkannt**, alte und neue Vektoren mischen sich still. Marke muss um die Praezision erweitert werden |
| anderes Modell mit gleicher Dimension | Neustart | Vektor-Reindex | automatisch, Marke erkennt den Namen |
| anderes Modell mit anderer Dimension (z. B. 768) | Neustart | Vektor-Reindex **plus Schemawechsel** der vec0-Tabelle | `EMBEDDING_DIMENSIONS = 384` ist Modulkonstante (`store/vectors.py:81`), Laengenpruefung (636) weist alles andere ab |

Die Vektor-Neueinbettung kostet auf m7g.large rund 5 h (170 Dokumente je Minute), waehrend die
Suche lexikalisch weiter antwortet und die Seite "degraded" zeigt (`docs/embeddings.md` 8). Mit H1
und Embed-Slots auf Mehrkern-Boxen verkuerzt sich genau dieser Posten.

### 3.5 Modellwahl, knapp

- **e5-small fp32** ist der naheliegende Qualitaetsschritt: gemessen faellt MRR auf Franzoesisch mit
  der int8-Fassung um 9,24 Prozent, auf Deutsch und Englisch steigt es (+2,30 / +5,70 Prozent)
  (`docs/measurements/2026-09-05-modellqualitaet/README.md`). Kosten: Gewichte 470.268.510 statt
  118.101.091 Byte, also rund +352 MB Datei und gerechnet aehnlich viel Laufzeitspeicher [ASSUMED:
  RSS folgt der Dateigroesse]; dazu die Marken-Erweiterung aus 3.4.
- **Wo das fp32-Modell herkommt, ist die eigentliche Entscheidung:** ins Abbild (jede Installation
  laedt rund 350 MB mehr, auch die 4-GB-Boxen) oder Nachladen bei Bedarf (bricht die Regel "Modell
  ins Image backen, kein Download beim Start", CLAUDE.md "What NOT to Use"). Das ist der einzige
  BL-F04-Teil, der den Neupruefungs-Vorbehalt der Nicht-Spaltung beruehren koennte (Abschnitt 5, K7).
- **jina-v2-base-de** (768 Dimensionen, laut fastembed real im fp32-Original) braucht den
  Schemawechsel aus 3.4, verdoppelt Vektorspeicher und Scan-Kosten und gehoert nicht in v1.4.

---

## 4. Test vor dem Speichern (ayhamoo)

### 4.1 Was eine Vorab-Pruefung serioes pruefen kann

| Probe | Dauer (gerechnet) | Was sie belegt | Kosten, Risiko |
|---|---|---|---|
| Hardware lesen (3.3 Schritt 1) | unter 1 s | Profil passt ueberhaupt zur Box | keine |
| RAM-Rechnung mit gemessenen Kosten je Slot | unter 1 s | Slotzahl passt unter Grenze und Reserve | haengt an der Guete der Zahl aus P22-B3/B4 |
| **N-Slot-Probe**: das W3-Werkzeug als Produktfunktion, N Slots lesen gleichzeitig eine mitgelieferte synthetische Scanseite | rund 5 bis 20 s (eine Seite je Slot, 3,6 s je Seite auf ARM) | **echte** Kosten je Slot und **echter** Skalierungsfaktor auf DIESER Box, einschliesslich SMT und Nextcloud-Last im Moment der Probe | kurzzeitig N tesseract; muss vorher gegen die Grenze gerechnet werden, sonst wird die Probe selbst das OOM |
| Modell-Probe (nur bei fp32-Wunsch) | rund 1 bis 3 s Laden | Modell laedt, Ladesprung | teuerste Probe: +422 MB bleiben stehen (Vorgaenger 6.2); nur rechnen statt laden, wenn die Luft fehlt, oder danach entladen |
| Verdikt | - | "passt", "passt knapp", "passt nicht", mit benannter Ursache | kein stilles Abschneiden |

### 4.2 Was sie nicht pruefen kann

- Dauerverhalten: Fragmentierung ueber Stunden, Waermedrosselung, der naechtliche Cron der
  Instanz, gleichzeitige Nutzersuche plus OCR-Spitze.
- Das echte Material der Instanz: 300-Seiten-Scans, riesige Bilder, der eine Ausreisser, der im
  Volllauf die Spitze macht (die gemessene Spitze 1.812,7 MB entstand im Zusammenspiel, nicht in
  einer Einzelprobe).
- Wirkung auf die Nutzer der Nextcloud (Latenz der Weboberflaeche waehrend N Slots rechnen).

Darum gehoert neben die Probe ein **Laufzeit-Rueckfall**: wiederholtes `memory.events max` oder ein
OOM-Kill senkt das Profil selbsttaetig um eine Stufe (Vorgaenger R1/R2).

### 4.3 Aufwand

Gerechnet, [ASSUMED]: eine eigene Phase mit rund 5 bis 8 Plaenen (Container-Proberoute mit
Admin-Zugriff, Testseite im Abbild, Hardwareerkennung, PHP-Proxy und Hinweisflaeche, Verdikttexte in
16 Katalogen, UI-Phase mit ui-phase-Gate). Die N-Slot-Probe setzt voraus, dass es N Slots gibt
(H2); vorher kann die Pruefung nur Hardware, Rechnung und eine Einzelseite zeigen. Die Reihenfolge
"Geruest, dann Probe-UI, dann H2" aus der Vorgaenger-Research bleibt tragfaehig, wenn die Probe-UI
ihren N-Slot-Teil erst mit H2 bekommt.

---

## 5. Risiken und moegliche Killer

| # | Risiko | Wirkung auf BL-F04 | Frueherkennung |
|---|---|---|---|
| K1 | **Skalierung bleibt aus**: 2 Slots auf 2 Kernen unter Faktor 1,05, oder CI-4-Kern-Kurve unter 1,5 | Stufe H2 kippt; v1.4 liefert H0 plus H1 plus Profil-UI. Bleibt ein Produkt, das auf grossen Boxen schneller wird, nur weniger | P22-B3, W4 in CI, P22-B4 |
| K2 | **RAM je Slot am oberen Rand** (ueber 500 MB) | auf 8 GB nur 2 bis 3 Slots, Standard bringt wenig; die Mehrheit mit viel RAM profitiert trotzdem | P22-B2/B3/B4 |
| K3 | **Nextcloud ist der Engpass**, nicht Findling (PHP-Pool, Datenbank, Gateway) | Faktor auf 8 und 16 Kernen deutlich unter der Rechnung | nur mit Produkt messbar: Abnahme-Anfahrt v1.4 |
| K4 | **Findling verdraengt Nextcloud** auf der eigenen Box (Weboberflaeche traege waehrend des Erstindex) | Akzeptanzproblem gerade bei der Mehrheit, die mehr Kerne hat und sie mit anderem teilt | Anteilsprinzip 3.1; zusaetzlich tesseract-Kinder mit niedriger Prioritaet starten (`os.nice` im Sandbox-Kind) [ASSUMED wirksam, billig] |
| K5 | **Einstellungen kommen nicht live in den Container** (`config.py:1240` lru_cache, nur Umgebungsvariablen) | Profilwechsel braucht Neustart oder einen neuen Konfigurationsweg | Owner-Tor am Anfang von v1.4 (Wege A, B, C der Vorgaenger 6.4) |
| K6 | **PHP-Kopplung**: `KIND_BATCH`, `LOCK_TIMEOUTS` und der fehlende Art-Filter sind `private const` bzw. Routenform | jede Slot-Erweiterung ist ein Release beider Apps mit gleicher Version | im Milestone-Schnitt einplanen, keine Ueberraschung |
| K7 | **fp32-Modell blaeht das Abbild** | beruehrt den Neupruefungs-Vorbehalt der Nicht-Spaltung (Owner 25.09.); Empfehlung: fp32 nicht ins Basis-Abbild und aus v1.4 herausnehmen, Profile ohne Modellwahl ausliefern | Owner-Frage 7.3 |
| K8 | **Stille Vektormischung** bei Praezisionswechsel (3.4) | falsche Treffer ohne Fehlermeldung | Marke erweitern, bevor irgendein Modellschalter entsteht |
| K9 | **Testbarkeit**: CI hat 4 Kerne, 8 und 16 nur auf bezahlter Box; Windows/WSL2 kennt `RLIMIT_AS`, `setsid`, cgroup nicht (Vorgaenger R5) | Mehrkern-Pfade nur in Linux-CI und auf Box pruefbar | arm64-CI-Ast, Abnahme-Anfahrt |
| K10 | **Der Default rutscht** um einige MB durch das Profil-Geruest | Store-Zahl falsch | Pin-Test Sparsam (3.2) |

**Kein Killer im engeren Sinn gefunden.** Das schlechteste plausible Ergebnis (K1 plus K2) laesst
BL-F04 auf Profil-Geruest, Hardware-Vorschlag, Vorab-Pruefung und die Einbettungsspur als
Nebenlaeufer schrumpfen. Auch das beantwortet die drei Reddit-Signale teilweise.

---

## 6. Environment Availability

| Abhaengigkeit | Wofuer | Verfuegbar | Anmerkung |
|---|---|---|---|
| Korpus-Snapshot `snap-03f1d1d9ad9262704` | Phase-22-Box | ja, laut Runbook 1.2 und 3 (lesende Probe vorgesehen) | in dieser Research nicht abgefragt |
| AWS eu-central-1, m7g.large | Phase-22-Box | ja (Runbook) | |
| m7g.4xlarge in eu-central-1c | P22-B4 | [ASSUMED] | Rueckfall m7g.2xlarge |
| GitHub `ubuntu-24.04-arm`, 4 vCPU / 16 GB | W4 | ja, oeffentliches Repo, schon genutzt | [CITED: docs.github.com] |
| `embed.bench` im Abbild | P22-B4/B5 | ja (`findling/embed/bench.py`, Paket im Abbild) | |
| `scripts/ops/cpu_sampler.sh`, `proc_anon_sampler.sh`, `ocr_slot_probe.py` | P22-B1 bis B4 | **nein**, Wave-0-Werkzeug in Phase 22 | boxlos baubar und in CI pruefbar |

Keine neuen Pakete. Package-Legitimacy-Audit entfaellt.

## 7. Offene Fragen an den Owner

1. **B4 fahren?** Typwechsel am Ende der Phase-22-Anfahrt auf m7g.4xlarge, rund 1,25 h, rund
   1,00 USD, liefert 8- und 16-Kern-Zahlen auf Zielarchitektur. Empfehlung: ja, wenn die
   CI-Vorabkurve (W4) auf 4 Kernen einen Faktor ueber 1,5 zeigt.
2. **Werkzeug-Plan in Phase 22 aufnehmen?** W1 bis W4 sind Werkzeuge, keine Produktaenderung, aber
   sie erweitern den Umfang von Phase 22 (MESS-07..09). Formal braucht es eine Owner-Freigabe als
   Zusatzauftrag im Rechenblatt, keinen neuen Requirement-Eintrag in v1.3.
3. **Modellwahl aus v1.4 herausnehmen?** Empfehlung ja (K7, K8). Die Marken-Erweiterung aus 3.4 kann
   trotzdem in v1.4, weil sie billig ist und eine Falle schliesst.
4. **Wie kommt das Profil in den Container?** (Vorgaenger 11.1, Wege A, B, C) bleibt das erste
   Owner-Tor von v1.4. Die Hardware-Erkennung mit Vorschlag verlangt mindestens eine Statusmeldung
   Container an Admin-Seite; die gibt es schon.
5. **Anteile der Profile** (3.2: 50/40 und Kerne-1/60 Prozent) sind Vorschlaege. Sie sind eine
   Produktaussage ("Findling nimmt hoechstens die Haelfte der Box") und gehoeren in den Store-Text,
   also Owner-Wortlaut.

## 8. Security Domain (kurz)

| ASVS | gilt | Kontrolle |
|---|---|---|
| V4 Zugriff | ja | Proberoute und Profilroute nur `access_level` ADMIN in `info.xml`; die N-Slot-Probe startet N tesseract-Prozesse und ist fuer Nicht-Admins ein DoS-Hebel |
| V5 Eingabe | ja | Profilname als geschlossene Menge; Einzelwerte weiter ueber die vorhandenen Bereichspruefer in `config.py` (`_bounded_int_from_environment`) |
| V11 Geschaeftslogik / Ressourcen | ja | Probe vor dem Start gegen die Grenze rechnen, eine Probe gleichzeitig, Zeitdeckel |
| Datenschutz | ja | Hardwaredaten bleiben lokal, keine Telemetrie (Projektregel); Messwerkzeuge drucken keine Nutzertexte und keine Pfade (T-02-14) |

## 9. Assumptions Log

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---|---|---|
| A1 | Waehrend der OCR-Spur belegt Findling rund 1 Kern von 2 | 0, 2.4 | Gewinn auf 2 Kernen faellt weg (K1); B1/B2/B3 klaeren es in der Anfahrt |
| A2 | r (Kernbelegung durch Nextcloud/AIO waehrend Indexlauf) rund 0,5 | 2.4, 3.1 | alle Wandzeiten der Tabelle 2.4 |
| A3 | Serieller Boden 0,5 bis 1,0 h | 2.4 | Faktor auf 8 und 16 Kernen |
| A4 | Einbettung belegt bei 2 onnx-Threads 1,6 bis 2,0 Kerne; intra-op skaliert ueber 4 Threads unterlinear | 2.3, 2.4 | Kern-Stunden der Einbettung, Profilwert onnx-Threads; B4/B5 messen es |
| A5 | RAM je OCR-Slot im Band 200 bis 680 MB (Untergrenze gerechnet aus Sandbox-Kind 69 MB, tesseract 106,1 MB, Rasterung) | 2.4, 3.2 | Slotzahlen je Box; B2/B3/B4 |
| A6 | Graviton-vCPU ist ein physischer Kern | 1.1 | Skalierungskurve auf der Box waere mit x86-SMT vergleichbar statt sauber |
| A7 | m7g-Preise sind innerhalb der Familie linear, m7g.4xlarge rund 0,78 USD/h in eu-central-1 | 1.6 | B4-Kosten; am Anfahrtstag gegenlesen |
| A8 | m7g.4xlarge ist in eu-central-1c verfuegbar | 1.5 | Rueckfall 2xlarge, Stufen 12/16 fehlen |
| A9 | AppAPI/HaRP setzt dem ExApp-Container im Feld meist kein Speicherlimit | 3.3 | Erkennung muss dann `MemAvailable` nutzen; ist das Limit gesetzt, wird es einfacher |
| A10 | fp32-Laufzeitspeicher folgt ungefaehr der Dateigroesse (+352 MB) | 3.5 | Modellprobe, Profil Leistung |
| A11 | SMT-Paare bringen deutlich weniger als zwei Kerne | 2.4, 3.3 | x86-Profilvorschlag zu gross; die N-Slot-Probe korrigiert es |
| A12 | `os.nice` im Sandbox-Kind entlastet die Nextcloud-Oberflaeche spuerbar | 5 (K4) | Gegenmittel K4 schwaecher |
| A13 | Aufwand Vorab-Pruefung rund 5 bis 8 Plaene | 4.3 | Milestone-Schnitt |

## 10. Quellen

**Primaer, Quelltext (HIGH), gelesen 25.09.2026**

- `backend/src/findling/config.py`: 81, 222-237, 256, 436-491, 583-645, 673-686, 1240-1364
- `backend/src/findling/worker/poller.py`: 693, 722, 734, 783, 803, 821, 831, 846-854, 886-1060
- `backend/src/findling/extract/ocr.py`: 73, 107-216; `extract/sandbox.py`: 200-350;
  `extract/errors.py`: 56, 169-178
- `backend/src/findling/embed/model.py`: 86, 113, 337-338, 614; `embed/bench.py`: 160-190, 435-451,
  746-780
- `backend/src/findling/index/writer.py`: 176; `index/rebuild.py`: Modulkopf, 561-588;
  `index/bench.py`: Modulkopf, 342-348
- `backend/src/findling/store/vectors.py`: 78-87, 255-273, 457, 636; `store/repo.py`: 157, 248
- `php/lib/Service/QueueService.php`: 64, 136-153, 177-235; `php/lib/Db/QueueMapper.php`: 69-82, 136
- `scripts/ops/rss_sampler.sh`: Kopf und Abtastschleife (kein CPU-Feld)
- `.github/workflows/measure.yml`: Kopf, 84-104, 250-265
- git: `5f4e314` (01.09.2026, `OMP_THREAD_LIMIT` eingefuehrt)

**Primaer, Projektberichte (HIGH)**

- `docs/performance.md`: "Die Zusatzmessung: was ein zweiter Indexarbeiter bringt" (2785-2897),
  "Der Semantik-Volllauf" (2899-3005), "Die Nachmessung" (3007-3141), "Die Entladung im Leerlauf"
  (3604-3692), "Die v1.2-Anfahrt" (4157-4406)
- `docs/ocr.md`: Messung 3 (`OMP_THREAD_LIMIT`)
- `docs/embeddings.md`: Abschnitte 7 und 8
- `docs/runbook-messbox.md`: 2.1 bis 2.5, Block 3, Block 10
- `docs/measurements/2026-09-05-modellqualitaet/README.md`,
  `docs/measurements/2026-09-grundlast-fein/README.md`, `docs/measurements/2026-09-05-welle0-arm64/`
- `.planning/BACKLOG.md` (BL-F03, BL-F04), `.planning/ROADMAP.md` (Phasen 22, 23),
  `.planning/REQUIREMENTS.md` (MESS-07..09), `.planning/STATE.md`
- `.planning/phases/21-niederlaendische-komposita/21-RESEARCH.md` (17,6 MB, qemu-Artefakt),
  `21-CONTEXT.md`, `21-GO-ENTSCHEID.md`
- `.planning/research/BL-F04-worker-skalierung.md` (Vorgaengerin)

**Sekundaer**

- [CITED] docs.github.com/en/actions/reference/runners/github-hosted-runners: `ubuntu-24.04-arm`
  fuer oeffentliche Repos 4 CPU, 16 GB, 14 GB SSD (abgerufen 25.09.2026)
- [MEDIUM] github.blog Changelog 2025-08-07, arm64-Runner fuer oeffentliche Repos allgemein
  verfuegbar, Cobalt 100 / Neoverse N2
- [MEDIUM] doit.com/compute/spot/eu-central-1/m7g.xlarge: m7g.xlarge 0,1955 USD/h On-Demand in
  eu-central-1 (Drittquelle, nicht AWS-Preisliste)

## 11. Metadaten

| Bereich | Konfidenz | Grund |
|---|---|---|
| Phase-22-Mitmessliste | HIGH fuer Machbarkeit (Werkzeuge und Stellschrauben am Code geprueft), MEDIUM fuer Boxzeiten (aus Ist-Werten der v1.2-Anfahrt abgeleitet) | |
| Korrektur K1 (zweiter Kern liegt brach) | MEDIUM | Code eindeutig, CPU nie gemessen; B3 entscheidet in 15 min |
| Architektur und Codestellen | HIGH | gelesen |
| Lohnrechnung 2.4 | LOW-MEDIUM | zwei Eingangsgroessen ungemessen, alle markiert |
| Profilschnitt | MEDIUM | Mechanik belegt, Werte sind Vorschlaege |
| Wechselmechanik, Marken-Luecke | HIGH | `store/vectors.py:273` gelesen |
| Vorab-Pruefung | MEDIUM | Mechanik belegt, Aufwand geschaetzt |

**Gueltig bis:** Beginn der Phase-22-Planung fuer Abschnitt 1; Rest rund 30 Tage oder bis Phase 21/22
den Indexpfad, die Poller-Schleife oder die OCR-Kette aendern.
