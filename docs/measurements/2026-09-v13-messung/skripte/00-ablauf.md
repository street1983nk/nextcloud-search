# Der Ablauf der v1.3-Anfahrt, in seiner Reihenfolge

Diese Datei ist der Ablaufplan des Laufs im Verzeichnis
`docs/measurements/2026-09-v13-messung/`. Sie beschreibt den Lauf, **bevor** er
stattfindet: die Erwartungen stehen unten mit Zahlen da, und der Commit dieser
Datei ist ihr Zeitstempel. Nach der Messung werden sie nicht umformuliert; die
Urteile lauten nur `gehalten`, `verfehlt` oder `nicht entschieden`.

**Zur Schreibweise.** Die Abschnittsüberschriften stehen ohne Umlaute, weil
Prüfungen und Verweise auf sie zeigen. Der Fließtext benutzt echte Umlaute. Die
Skripte dieses Verzeichnisses schreiben ihre Kommentare und Protokollzeilen in
ASCII, weil sie auf einer Box laufen, deren Gebietsschema niemand garantiert.

**Zur Geltung.** Der Lauf ist unbeaufsichtigt: `skripte/00-lauf.sh` fährt ihn
allein, während die Härtung der Phase 23 lokal läuft, und
`skripte/00-abholen.sh` holt die Rohdaten alle zehn Minuten auf die
Entwicklungsmaschine. Deckel, Weg und B4-Plan kommen als Laufwerte aus einer
Datei außerhalb des Repos; ihre Werte legt der Owner am Checkpoint 22-07 fest
(Abschnitt 6), nicht diese Datei.

---

## 1. Was dieser Lauf misst

**Die fünf Boxzahlen von MESS-07 (BL-F03).**

| Zahl | Werkzeug | Rohdatei |
|---|---|---|
| M-01: Dauer des inneren Aufrufs auf Zielhardware, je Laststufe 1, 4, 8, 12, 16 | `scripts/ops/search_load.py` unter `loglevel` 1, gelesen mit `91m-langsame-aufrufe.py` | `m01-stufe-*.json`, `m01-langsame-aufrufe.txt` |
| Wirkungsnachmessung der Nachfolgefassungen 92c und 99d | `92c-wechsel.sh` zweimal (Fehlschlag, regulär), `99d-filter-sortierung.sh` | `92c-wechsel-fehlschlag.txt`, `92c-wechsel.txt`, `99d-filter-sortierung.txt` |
| Bodensatz über zwei Indexzyklen in einem Containerleben | `94c-bodensatz-zyklen.sh` unter Entladefrist 120 s | `94c-bodensatz-zyklen.txt` |
| Die übersprungenen und fehlgeschlagenen Dateien einzeln benannt | `90e-einzelliste.py liste` | `90e-einzelliste.json` (Weg a) oder `90e-einzelliste-nach-vollreindex.json` (Weg b) |
| Kaltstartlatenz mit Trefferpflicht der ersten Suche | `95c-kaltstart.sh` | `95c-kaltstart.txt` |

**Die zwei v1.3-Zahlen von MESS-08.** Die Indexgröße bei sechs befüllten
Sprachfeldern am Korpus-Snapshot (`indexgroesse-de-en.txt` gegen
`indexgroesse-sechs-felder.txt`, dazu die Spitze beider Verzeichnisse in
`umbau-platz.txt`) und die Wandzeit des Re-Analyse-Umbaus, gemessen vom
Containerstart bis zur Logzeile „the rebuilt index directory is in place“
(`00-lauf.txt`, Zeile `umbau-wandzeit-s`, daneben `umbau-status.jsonl`).

**MESS-09.** Der disjunction_max-Entscheid auf Messbasis: `98d-dismax-probe.py`
im Produktcontainer nach dem Umbau, Rohdatei `98d-dismax-probe.txt`. Die Regel,
die aus diesen Zahlen einen Entscheid macht, steht nicht im Werkzeug und nicht
in diesem Abschnitt, sondern in Abschnitt 6, und sie wird vor dem Boxstart
festgelegt (D-04).

**Die BL-F04-Mitmessliste B1 bis B6.** B1, die Kernbelegung je Phase aus
`cpu_sampler.sh` neben `rss_sampler.sh`, je Containerleben eine eigene Datei
(`b1-cpu-*.csv`, `b1-rss-*.csv`); B2, die OCR-Charge im Produkt mit W2 im
Sekundentakt (`b2-ocr-charge.txt`, `b2-anon.csv`); B3, RAM je OCR-Slot und der
Faktor zweier Slots im Wegwerf-Container (`b3-*.txt`); B4, die Kurve 1 bis 16
Kerne auf m7g.4xlarge (`b4-*.txt`); B5, die onnx-Kombinationen Threads und
Batch (`b5-*.txt`); B6, ob der Umbau einkernig läuft, abgelesen aus B1 während
Phase II. **B7**, der niederländische Automat nativ auf arm64, läuft nie auf
der Box, sondern im CI-Job `slots` von `measure.yml`.

---

## 2. Die Schrittfolge

Jede Zeile nennt den Block von `00-lauf.sh`, seine Planminuten aus dem
Rechenblatt-Entwurf und ob vor ihm die Zeit geprüft wird (`zeit_fuer`) oder ob
er Pflicht ist. Jeder Block schreibt beim Betreten und Verlassen eine Zeile mit
UTC-Stempel nach `rohdaten/00-lauf.txt`. Der Timer steht vor jedem Messblock.

**Weg a** (die 37 des Snapshots einzeln, 92c zuletzt):

| Nr | Block | Werkzeug | Planminuten | Zeitprüfung |
|---|---|---|---:|---|
| P0 | Timer | `sudo shutdown -h +<Rest>`, Rücklesung aus `/run/systemd/shutdown/scheduled` | 1 | Pflicht |
| P0 | Altverzeichnisse, Abtaster | `git status --porcelain` über das v1.2- und das Nachfolgeverzeichnis; W1 und `rss_sampler.sh` | 1 | Pflicht |
| P0 | Markentor und Einzelliste | `90e-einzelliste.py marken`, dann `liste` | 10 | Pflicht |
| PI | Wechsel ohne Volumenverlust | `92d-wechsel.sh`, danach neue Abtaster | 45 | Pflicht |
| PI | Cron vorher | `97-cron-vorpruefung.sh vorher` | 5 | Pflicht |
| PI | Indexgröße de,en | `du -sb` von `index` und `index.rebuild` | 5 | Pflicht |
| PI | M-01 und Kaltstart | `loglevel` lesen, auf 1, fünf Stufen, `91m` je Stufe, `95c-kaltstart.sh`, `91m` über das Kaltstart-Fenster, `loglevel` zurück | 50 | Pflicht |
| PI | Bodensatz | `92e-umgebung.sh` Frist 120, `94c-bodensatz-zyklen.sh`, `92e-umgebung.sh` Frist 0 | 30 | Pflicht |
| PI | Filter und Sortierung | `99d-filter-sortierung.sh` ohne `FINDLING_LOAD_PASSWORD` in der Umgebung | 10 | Pflicht |
| PI | B2 | 120 einseitige und 20 achtseitige synthetische Scans per WebDAV, `files:scan`, W2 bei 1 s, `97 waehrend`, Ordner löschen, Rückkehr auf 52.111 / 37 / 0 | 45 | `zeit_fuer b2` |
| PII | Umbau auf sechs Sprachen | `92e-umgebung.sh FINDLING_LANGUAGES=de,en,es,it,nl,pt`, Statusreihe alle 30 s, Platz alle 60 s, `97 waehrend` | 180 | Pflicht |
| PII | Indexgröße sechs Felder | `du -sb` nach dem Tausch | 5 | Pflicht |
| PII | dismax-Probe | `98d-dismax-probe.py` per `docker cp` und `docker exec` | 20 | Pflicht |
| PIII | B3 | `00-wegwerf.sh b3` | 15 | `zeit_fuer b3` |
| PIII | B5 | `00-wegwerf.sh b5` | 12 | `zeit_fuer b5` |
| PIII | Endmessungen | `90-bestand.sh` | 15 | Pflicht |
| PIII | 92c Fehlschlag, 92c regulär, Nullstand | `92c-wechsel.sh` mit `DAEMON=nicht-vorhanden`, dann regulär, dann `93-nullstand.sh` | 30 | Pflicht |
| PIV | Abschluss | B4-Vorbereitung (Grub-Drop-in `mem=4G` entfernen, `update-grub`), `00-FERTIG`, Warten auf die Abholung, `sudo shutdown -h now` | 20 | `zeit_fuer b4` nur für die B4-Vorbereitung |
| PIV | B4, nach dem Typwechsel | `00-lauf.sh b4`: Timer aus `DECKEL_REST_MINUTEN`, alle Container anhalten, `00-wegwerf.sh b4`, `B4-FERTIG`, Abschaltung | 75 | eigener Deckelposten |

**Weg b** (Vollreindex, 92c zuerst): P0 ohne Markentor, dann 92c Fehlschlag,
92c regulär und `93-nullstand.sh` (30 min), dann das Warten auf den Vollreindex
beider Spuren (Statusreihe alle 120 s, Ende nach acht Lesungen mit Vorrat 0 und
stehendem `embedded`, Frist bis zum Timer), dann `90e-einzelliste.py liste`
nach `90e-einzelliste-nach-vollreindex.json`, dann PI ab „Cron vorher“ ohne
92d, PII wie oben, PIII ohne 92c. Die Rückkehr nach B2 gilt in Weg b gegen den
Bestand, der unmittelbar vor B2 gelesen wurde.

**Zwei Festlegungen, die der Lauf trifft und die hier stehen, damit sie nicht
nach der Messung begründet werden:**

- `93-nullstand.sh` läuft unmittelbar **nach** dem regulären 92c und nicht
  davor. Dort ist es die Gegenprobe, dass 92c das Volumen geleert hat (Pitfall 1
  der Research: „`occ findling:index` zeigt danach 0 indexiert“), und in Weg b
  zugleich der Anstoß des Arbeitsvorrats mit `--restart -n`. Vor 92c liefe es
  gegen ein volles Volumen und setzte einen Vollreindex in Gang, den 92c eine
  Minute später wegwirft.
- Ein Werkzeug, dessen Messung keine Zahl oder eine rote Zahl liefert, während
  der Zustand der Box der erwartete bleibt, beendet den Lauf **nicht**: die
  Zeile `befund <block> ...` steht in `00-lauf.txt`, die Meldekette sendet, und
  die folgenden Pflichtblöcke messen weiter. Abgebrochen wird nur an Toren, an
  denen der Zustand der Box nicht mehr der ist, den die folgenden Zahlen
  voraussetzen (Abschnitt 4, Spalte „Folge im Ablauf“).

---

## 3. Die Erwartung, vorher aufgeschrieben

Dieser Abschnitt ist der Grund, warum diese Datei vor der Anfahrt entsteht. Was
hier steht, wird nach der Messung **nicht** angepasst. Eine verfehlte Erwartung
ist ein Ergebnis und kein Grund für eine zweite Anfahrt.

- **E1, Marken.** Das Markentor meldet 0: jede Marke außer den drei, die der
  Umbau beantwortet (`schema_version`, `languages`, `wordlist_hash_nl`), ist
  gleich den Konstanten des Codes, gelesen beim Schreiben dieser Datei:
  `analyzer_version=1` (`ANALYZER_VERSION`, `index/analyzer.py`),
  `index_version=1` (`INDEX_VERSION`, `config.py`, als Untergrenze),
  `store_schema_version=2` (`SCHEMA_VERSION`, `config.py`),
  `wordlist_hash=b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0`
  (der deutsche Digest, seit Phase 2 unverändert),
  `tantivy_version=tantivy v0.26.2, index_format v7` (verglichen am
  `index_format`), `embedding_version=multilingual-e5-small/int8/384/1024`
  (`embedding_mark` aus `store/vectors.py` mit `EMBED_TOKEN_CAP` 1.024).
  `schema_version=2` und `languages=de,en` stehen als Umbau-Marken mit in der
  Erwartung; ihre Abweichung ist erwartet. Gilt für Weg a.
- **E2, Bestandstor.** Nach 92d steht der Snapshot auf **52.111 indexiert, 37
  übersprungen, 0 fehlgeschlagen**. Quelle: `90-bestand.txt` der v1.2 und der
  Wechsel ohne `--rm-data`.
- **E3, Einzelliste.** Die Liste nennt **37 übersprungene und 0
  fehlgeschlagene** Dateien einzeln, jede mit Kennung, Endung, Größe und
  Grundcode. Gilt für Weg a; die 44 / 6 der v1.2-Box sind ohne Ende-Snapshot
  nicht mehr lesbar.
- **E4, M-01.** Das Maximum von `innerMs` liegt in **allen fünf Stufen unter
  `ceilingMs` 1.500**. Quelle: die Decke des inneren Aufrufs in
  `php/lib/Service/ExAppService.php`; gezählt werden nur Aufrufe ab 1.000 ms,
  darunter schreibt das Produkt keine Zeile.
- **E5, Kaltstart.** Die erste kalte Suche liefert **Treffer > 0**; ihre Latenz
  wird gegen **2.051 ms** gestellt, den kalten Wert ohne Entladung der v1.2
  (`95b-gegenueberstellung.txt`, Ausprägung 3, dort mit 0 Treffern). Die
  Gegenprobe von M-01 im Kaltstart-Fenster findet **mindestens eine Zeile**.
- **E6, Bodensatz.** `zyklus2-minus-c1` liegt bei **höchstens 50 MB**; Bezug ist
  der Bodensatz der v1.2 von **628,0 MB** (A 103,9 MB, C 731,9 MB,
  `94b-grundlast-rueckkehr.txt`). Ein zweiter Zyklus, der erneut Hunderte MB
  anlegt, wäre kein Bodensatz, sondern ein Leck.
- **E7, 99d.** `99d-filter-sortierung.sh` endet **mit 0**, und in seiner
  Umgebung steht **kein** `FINDLING_LOAD_PASSWORD` (Zeile `99d-umgebung` in
  `00-lauf.txt`): das Passwort kommt aus der Passwortdatei.
- **E8, Indexfaktor.** Die Indexgröße bei sechs Feldern liegt beim **Faktor
  rund 2,5** gegen de,en, im **Band 2,0 bis 3,0**. Quelle: je Kette 0,372 des
  Verzeichnisses, gemessen am 24.09. über 2.000 Dokumente
  (`index/rebuild.py`, Platzprüfung).
- **E9, Umbau-Wandzeit.** Der Umbau dauert **höchstens 3 h** (Planwert; die
  Schätzung liegt bei 1 bis 3 h) gegen die **19 h 20 min** des Vollreindex. Der
  Planwert nimmt keine Verbesserung vorweg (Runbook 2.1).
- **E10, dismax.** Die Probe liefert je Form die Kennzahlen, auf die die Regel
  aus Abschnitt 6 zeigt, und die Treffermenge von Summe und per-Wort-dismax ist
  gleich (sonst 49). Der Entscheid folgt allein der am 26.09.2026 beschlossenen
  Regel in Abschnitt 6: **dismax**, wenn für `dismax_t00` oder `dismax_t01` der
  Median von `rbo10_gegen_altplan` mindestens **0,05** über dem von `summe`
  liegt, kein Sprachfall-Eigenrang schlechter wird und der Median von
  `latenz_ms` höchstens das **1,20-fache** von `summe` ist; erfüllen beide
  tie-Werte, gilt der mit dem höheren RBO-Median, bei Gleichstand **0.0**.
  Sonst **Summe**. Die Erwartung selbst nimmt keinen der beiden Ausgänge
  vorweg.
- **E11, 92c.** Der Lauf mit einem Daemon, den es nicht gibt, endet mit **36**
  (`92c-fehlschlag-rueckgabewert 36`, „registrierung-gelungen nein“), der
  reguläre Lauf mit **0** (`92c-regulaer-rueckgabewert 0`).
- **E12, B6.** Die Kernbelegung des Produktcontainers während des Umbaus liegt
  bei **rund 1,0 von 2** Kernen (`mean_cores` in `b1-cpu-*-umbau.csv`). Das
  wäre der Befund „der Umbau läuft einkernig“; der Hebel dagegen ist deferred.
- **E13, B3.** Der Faktor zweier OCR-Slots gegen einen liegt bei **mindestens
  1,05**; darunter ist er Rauschen (A/B 802 gegen 799 s).
- **E14, B2.** Die Sekunden je Seite der Charge werden gegen die **120 Scans in
  8 min 36 s vom 07.09.2026** gestellt, also rund 4,3 s je Seite
  (`2026-09-nachmessung-m7g`, `71-ocrphase.sh`). Die Charge dieses Laufs hat
  280 Seiten, 120 einseitige und 20 achtseitige.

---

## 4. Woran der Lauf abgebrochen wird

Der Katalog der Werte 15 bis 39 aus `docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md`
gilt unverändert weiter; keine Zahl wird umgehängt. Die Werte dieses Laufs
setzen ihn fort. Jeder steht in seinem Werkzeug **unterhalb** der `tee`-Pipeline
oder, in `00-lauf.sh`, in der Hauptshell, die gar keine Pipeline um ihre Blöcke
hat. Die Verweigerung vor der ersten Zeile endet weiterhin mit 2.

„Folge im Ablauf“ sagt, was `00-lauf.sh` mit dem Wert tut: **Abbruch** heißt,
der Lauf endet mit diesem Wert, die Meldekette sendet mit hoher Priorität, und
der Timer wird auf 60 Minuten vorgezogen, damit eine haltende Box nicht bis zum
Deckel kostet; **Befund** heißt, die Zeile `befund` steht in `00-lauf.txt` und
der Lauf misst weiter.

| Wert | Skript | Bedingung | Folge im Ablauf |
|---|---|---|---|
| **40** | `92d-wechsel.sh` | `occ upgrade` ist gescheitert; unregister und register sind dann nicht gefahren | Abbruch |
| **41** | `92d-wechsel.sh` | das Bestandstor nach der Registrierung meldet nicht 52.111 / 37 / 0, oder eine der drei Zahlen war nicht lesbar | Abbruch |
| **42** | `92e-umgebung.sh` | die harte Grenze steht nach dem Neubau nicht in der cgroup | Abbruch |
| **43** | `92e-umgebung.sh` | der Container ist nicht in der nachbaubaren Gestalt, der Neubau ist gescheitert, oder der neue Container trägt den Schalter nicht | Abbruch |
| **44** | `90e-einzelliste.py marken` | eine Marke außerhalb der drei Umbau-Marken und außerhalb von `embedding_version` weicht ab oder fehlt | Abbruch, kein Wechsel |
| **45** | `90e-einzelliste.py marken` | `embedding_version` weicht ab oder fehlt: eine Neueinbettung liefe neben dem Umbau | Abbruch, kein Wechsel |
| **46** | `94c-bodensatz-zyklen.sh` | ein Zyklus ist nicht abgeschlossen (Upload, Frist, kein Passwort) oder der Block lief nicht bis zu seinem Ende | Befund, die Frist geht trotzdem auf 0 zurück |
| **47** | `94c-bodensatz-zyklen.sh` | die Stellung des Entladeschalters ist beim Start nicht 120 | Befund, die Frist geht trotzdem auf 0 zurück |
| **48** | `95c-kaltstart.sh` | nach höchstens drei Kaltzyklen hat keine erste Suche Treffer geliefert, oder der Block lief nicht bis zu seinem Ende | Befund, die M-01-Gegenprobe heißt dann nicht entschieden |
| **49** | `98d-dismax-probe.py` | die Treffermenge von Summe und per-Wort-dismax ist ungleich | Befund |
| **50** | `00-wegwerf.sh b3` oder `b5` | das Produkt war nicht im Leerlauf, sein Start hat sich bewegt, eine Probe hat keine Zahl, oder der Block lief nicht bis zu seinem Ende | Befund |
| **51** | `00-wegwerf.sh b4` | ein Container lief neben dem Wegwerf-Container, eine Probe hat keine Zahl, oder der Block lief nicht bis zu seinem Ende | Befund in `B4-FERTIG` |
| **52** | `00-typwechsel.sh vorpruefung` | `instanceInitiatedShutdownBehavior` ist nicht `stop` (terminate, leer oder unlesbar) | die Anfahrt beginnt nicht (Entwicklungsmaschine) |
| **53** | `00-typwechsel.sh hin` oder `zurueck` | der zurückgelesene Typ oder Zustand weicht vom geforderten ab | B4 entfällt oder der Abbau läuft von Hand (Entwicklungsmaschine) |
| **54** | `00-lauf.sh` | das v1.2- oder das Nachfolgeverzeichnis im Box-Klon ist nicht sauber (`git status --porcelain` nicht leer), beim Start oder im Abschluss | Abbruch |
| **55** | `00-lauf.sh` | die geplante Abschaltung ist nicht zurückzulesen, ist kein Herunterfahren, liegt mehr als 120 s neben dem Deckel, oder der Deckel ist beim Start schon erreicht | Abbruch vor jeder Messung |
| **56** | `00-lauf.sh` | nach B2 kehrt der Bestand in der Frist nicht auf den Stand vor B2 zurück (Weg a: 52.111 / 37 / 0) | Abbruch |
| **57** | `00-lauf.sh` | die Gegenprobe von M-01 findet im Kaltstart-Fenster keine Zeile: das Level oder der Leser ist falsch, nicht das Backend | Abbruch, nach dem Zurücksetzen von `loglevel` |
| **58** | `00-lauf.sh` | `embedded` bewegt sich während des Umbaus, oder der Umbau (in Weg b der Vollreindex) erreicht die Frist 20 Minuten vor dem Timer | Abbruch |

Die Werte 36 bis 39 von `92d-wechsel.sh` bedeuten dasselbe wie in 92c und
führen in `00-lauf.sh` ebenfalls zum Abbruch, ebenso 25 und 26 des
Cron-Konfigurationszweiges. Der Wirkungszweig `97-cron-vorpruefung.sh waehrend`
läuft neben B2 und dem Umbau; seine Werte 27 und 28 sind Befunde. Endet ein
Befehl außerhalb dieser Tore unerwartet, schreibt die EXIT-Falle von
`00-lauf.sh` die Zeile `00-abbruch` mit dessen Rückgabewert und die Datei
`00-ABBRUCH`; der Lauf endet dann fail-closed, nie mit 0. Endet er durch ein
Signal, also durch den harten Stopp des Timers selbst, steht davor die Zeile
`00-abbruch-durch-signal` und der Rückgabewert ist 143; der Timer wird dann
nicht mehr vorgezogen.

---

## 5. Nach dem Lauf

Rohdaten und Skripte committen, den Bericht in `../README.md` schreiben, die
Kosten dem freigegebenen Deckel gegenüberstellen. Vor jedem Commit der Rohdaten
läuft `backend/tests/test_public_artifacts.py` über dieses Verzeichnis; die
Container-Logs tragen Brückenadressen.

**Die Prüfsummenregel, wie in der v1.2.** Jede Fassung, die auf dieser Anfahrt
gefahren wird, bekommt nach dem Lauf eine Prüfsumme in
`backend/tests/test_measurement_scripts.py`, wie sie die älteren gefahrenen
Fassungen tragen: eine gefahrene Messfassung ist Teil des Belegs und wird danach
nicht mehr angefasst. Das gilt für jedes Werkzeug dieses Verzeichnisses, das
gelaufen ist, und ausdrücklich auch für `92c-wechsel.sh` und
`99d-filter-sortierung.sh` aus `docs/measurements/2026-09-nachfolgefassungen/`:
beide gelten nach dem Lauf als gefahren. Ihr Kopfsatz „DIESE FASSUNG IST NICHT
GEFAHREN“ bleibt byteweise stehen; der Wächter, der ihn verlangt, wird durch
einen Prüfsummen-Wächter ersetzt, und der Bericht nennt das Fahrdatum.

---

## 6. Owner-Entscheide

Beantwortet am Checkpoint 22-07 am **26.09.2026**, vor jeder Boxminute, und
mit diesem Commit eingefroren. Die Antwort des Owners, wörtlich:

> machen wir nach deiner empfehlung

Die Empfehlung, auf die sie antwortet, stand wörtlich in der Form des
Checkpoints:

> Weg a, Deckel stunden, dismax vorschlag, F4 bestaetigt, freigegeben

Daraus folgen die drei Antworten unten und die Laufwerte in `../README.md`,
Abschnitt 4. Nach dem Boxstart wird hier nichts mehr geändert.

**Frage 1: Wie werden die 6 Fehlschläge und 44 Übersprungenen benannt?**
(a) die 37 des Snapshots einzeln, die 44 / 6 dokumentiert nicht
reproduzierbar; (b) ein v1.3-Vollreindex (rund +20 h, 92c zuerst, Deckel neu zu
rechnen), der eine neue Endzahl einzeln benennt; (c) ein Teilweg über die in
v1.2 hinzugekommenen Dateien.

Antwort (26.09.2026): **Weg a.** Die 37 übersprungenen Dateien des Snapshots
werden in P0 einzeln benannt (`90e-einzelliste.json`), die 44 / 6 der v1.2-Box
sind als nicht reproduzierbar dokumentiert. `EINZELWEG=a`; `00-lauf.sh` bleibt
unverändert, der Block `teilweg` wird nicht gebaut.

**Frage 2: Welcher Deckel gilt, 24 h oder 3,00 USD?** Mit B4 greift der
USD-Deckel schon bei rund 17,4 h Gesamtzeit.

Antwort (26.09.2026): **Variante Stunden.** 24 Boxstunden gesamt, B4 darin,
höchstens 3,76 USD (README 1.3). `DECKEL_MINUTEN=1354` für den m7g.large-Teil,
`DECKEL_REST_MINUTEN=86` für B4 auf m7g.4xlarge.

**Frage 3: Nach welcher Regel fällt die Messung für disjunction_max aus?**

Antwort (26.09.2026): **Der Vorschlag der Research gilt**, und die
F4-Definition aus Abschnitt 8 ist bestätigt (F4 = 3,955, `B4_GEPLANT=ja`). Der
Vorschlag lautete:

> Vorteil für dismax, wenn der Median von RBO@10 gegen den Altplan unter dismax
> um mindestens 0,05 höher liegt als unter der Summe, kein Sprachfall-Eigenrang
> schlechter wird und die lexikalische Latenz um höchstens 20 Prozent steigt;
> tie 0.0 gegen 0.1 wird mitgemessen.

Beschlossen in dieser Form, ohne Ermessen. Die Kennzahlen sind Zeilen von
`98d-dismax-probe.txt`; `<t>` steht für `dismax_t00` und `dismax_t01`, die beide
einzeln geprüft werden:

1. **RBO.** `kennzahl rbo10_gegen_altplan <t>` ist mindestens um **0,05**
   größer als `kennzahl rbo10_gegen_altplan summe`.
2. **Sprachfall-Eigenrang.** In keiner der zehn Sprachfall-Anfragen (die
   Anfragen 11 bis 20, Reihenfolge von `SPRACHFAELLE`) steht die eigene Datei
   des Falls in der Zeile `spitze <t>` auf einem schlechteren Rang als in der
   Zeile `spitze summe`; aus der Spitze gefallen, während sie unter `summe`
   darin stand, zählt als schlechter. Eine Anfrage der Klasse `rueckfall`
   (die Probe misst sie nur mit `summe`, das Produkt antwortet unverändert)
   zählt nicht als schlechter. Die Kennung der eigenen Datei ordnet der Bericht
   aus dem Bestand der Box zu; veröffentlicht wird nur die Kennung. Eine
   Anfrage, deren eigene Datei nicht zuzuordnen ist, zählt nicht als
   schlechter.
3. **Latenz.** `kennzahl latenz_ms <t>` ist höchstens das **1,20-fache** von
   `kennzahl latenz_ms summe`.

**Entscheid.** Erfüllt mindestens ein `<t>` alle drei Bedingungen, lautet der
Entscheid **dismax**, mit dem tie-Wert, der sie erfüllt; erfüllen beide, gilt
der mit dem höheren Median aus Bedingung 1, bei gleichem Median **0.0**.
Erfüllt keiner alle drei, lautet der Entscheid **Summe** (das ausgelieferte
Verhalten bleibt). Fehlt eine der Kennzahlen, endet die Probe mit 49, oder ist
für keine der zehn Sprachfall-Anfragen die eigene Datei zuzuordnen, heißt der
Entscheid **nicht entschieden**.

---

## 7. Streichreihenfolge

D-05 gilt wörtlich: bei knapper Boxzeit fällt zuerst **B7** (läuft nie auf der
Box), dann **B5**, dann **B4**, dann **B2 und B3**. Die Pflichtzahlen der
Erfolgskriterien 2 und 3 und **B1** fallen nie; vor ihnen steht keine
Zeitprüfung. Reicht die Zeit für einen Pflichtblock nicht, stoppt der Timer die
Box, und die fehlenden Zahlen stehen als Lücken im Bericht (D-02).

`zeit_fuer` in `00-lauf.sh` rechnet vor B2, B3, B5 und der B4-Vorbereitung die
Minuten bis zur zurückgelesenen Abschaltung gegen Planminuten plus Reserve. Bei
Mangel steht die Zeile `gestrichen <block> rest <m> bedarf <m>` in
`rohdaten/00-gestrichen.txt`, und die Meldekette sendet. Die Planminuten sind
Konstanten des Skripts:

- `PLAN_B2=45`, `PLAN_B3=15`, `PLAN_B5=12`, `PLAN_B4=75`
- `PLAN_UMBAU=180`, `PLAN_98D=20`, `PLAN_ENDE=15`, `PLAN_92C=30`, `PLAN_ABHOLEN=20`

Die Reserve ist die Zeit der Blöcke, die im Rang über dem geprüften stehen und
noch kommen (`PLAN_92C` nur in Weg a, weil 92c in Weg b schon gelaufen ist):

- **vor B2:** `PLAN_UMBAU + PLAN_98D + PLAN_ENDE + PLAN_92C + PLAN_ABHOLEN`, also
  265 min in Weg a und 235 min in Weg b. B4 ist **nicht** reserviert, weil B4
  vor B2 fällt.
- **vor B3:** `PLAN_ENDE + PLAN_92C + PLAN_ABHOLEN`, also 65 min in Weg a und
  35 min in Weg b. B4 ist **nicht** reserviert.
- **vor B5:** die Reserve von B3 plus `PLAN_B4`, wenn B4 geplant ist, plus
  `PLAN_B3`, solange B3 nicht gefahren ist. B5 fällt vor B4 und vor B3.
- **vor der B4-Vorbereitung:** `PLAN_ABHOLEN`. Reicht sie nicht, steht in
  `00-FERTIG` der Zustand `b4 gestrichen`, der Grub-Drop-in bleibt, und die
  Box ist weiter eine Referenzbox.

---

## 8. F4 und die B4-Regel

F4 ist im W4-Job `slots` von `.github/workflows/measure.yml` vor dem ersten
Lauf festgelegt, und zwar wörtlich so:

```
F4 = pages per second at N = 4 on --cpuset-cpus 0-3, divided by pages
     per second at N = 1 on --cpuset-cpus 0, each the median of three
     timed rounds (pages_per_second_median of w3-slots-4.txt over the
     one of w3-slots-1.txt).
```

Ein fehlender oder nicht numerischer Median, ein Median von null bei N = 1 oder
eine Runde mit verlorenem Slot lassen F4 unbestimmt; der Job schreibt dann
„F4 unbestimmt“ und schlägt fehl.

**D-03, die B4-Regel.** F4 mindestens 1,5 auf der CI-Kurve heißt: **B4 wird
gefahren**, auch im Zwischenbereich 1,5 bis 3,0 (`B4_GEPLANT=ja`). Unter 1,5
entfällt B4 (`B4_GEPLANT=nein`), und die BL-F04-Stufe 2 kippt nach K1 der
Vorarbeit. Ein unbestimmtes F4 ist kein Wert über 1,5; über B4 entscheidet dann
der Owner am Checkpoint 22-07.
