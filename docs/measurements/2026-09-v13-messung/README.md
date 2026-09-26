# Die v1.3-Messanfahrt (Phase 22)

Diese Anfahrt liefert den Messbeleg von BL-F03 und der v1.3: das Bündel aus
MESS-07 (M-01 auf Zielhardware, Wirkungsnachmessung 92c und 99d, Bodensatz im
zweiten Zyklus, die übersprungenen und fehlgeschlagenen Dateien einzeln,
Kaltstartlatenz mit Treffern), MESS-08 (Indexgröße bei sechs Sprachfeldern und
Wandzeit des Umbaus) und MESS-09 (der disjunction_max-Entscheid), dazu die
BL-F04-Mitmessliste B1 bis B6. Der Ablauf und die vorher aufgeschriebene
Erwartung stehen in `skripte/00-ablauf.md`, die Rohdaten in `rohdaten/`.

Anfahrt freigegeben: 26.09.2026, Deckel 24 h / 3,76 USD (Variante stunden), Weg a, B4 gefahren (F4 = 3,955)

Die Freigabe hat der Owner am Checkpoint 22-07 erteilt, zusammen mit den
Antworten auf die drei Fragen in `skripte/00-ablauf.md`, Abschnitt 6, und mit
dem Freigabeumfang aus 1.5. Beides ist vor der ersten Boxminute committet.

**Zur Schreibweise.** Die Abschnittsüberschriften stehen ohne Umlaute, weil
Prüfungen und Verweise auf sie zeigen. Der Fließtext benutzt echte Umlaute.
Adressen, Kennungen und Passwörter der Box stehen in keiner Zeile dieser Datei.

---

## 1. Rechenblatt

Vorgelegt am 26.09.2026 für den Checkpoint 22-07, vor jeder Boxminute.
Rechenweg nach Runbook 2.5: Planwert je Posten, Summe, Zuschlag 15 Prozent,
mal Stundensatz. Die Planwerte stammen aus dem Rechenblatt-Entwurf der
Research (v1.2-Ist als Untergrenze); die Blockminuten in `skripte/00-ablauf.md`,
Abschnitt 2, summieren sich ohne Aufbau, Abbau und Wartezeit auf 499 min und
liegen damit 22 min über den 477 min derselben Posten hier, weil sie das
Abholen (20 min) und die Timerschritte mitzählen. Beides trägt der Zuschlag.

### 1.1 Die Sätze, am 26.09.2026 gelesen

`scripts/ops/aws_box.sh prices` (26.09.2026, lief mit 0) bestätigt Typ und
Platten: m7g.large, 2 vCPU arm64, 40 GB gp3 Systemplatte und 60 GB gp3
Datenvolumen, und nennt die gepinnten Sätze. Die Preis-API ist für dieses
Konto gesperrt: `00-typwechsel.sh preis m7g.4xlarge` und `preis m7g.large`
endeten am 26.09.2026 um 04:25Z beide mit 1 („preis ... unlesbar“, kein
`pricing:GetProducts` in der Richtlinie). Die Ausgabe ging in ein Verzeichnis
außerhalb des Repos, `rohdaten/` ist unberührt. Die Instanzsätze sind deshalb
von Hand aus der öffentlichen On-Demand-Preiskarte gelesen, die auch die
Preisseite von AWS speist: `https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/EU%20(Frankfurt)/Linux/index.json`,
gelesen am 26.09.2026, Veröffentlichungsstempel der Karte
`2026-09-25T17:45:21Z` (48 KB statt der über ein Gigabyte großen Liste der
Region).

| Satz | USD je Stunde, netto | Quelle |
|---|---:|---|
| m7g.large, Instanz | 0,0978 | Preiskarte 26.09.2026, gleich dem gepinnten Satz in `aws_box.sh` |
| m7g.4xlarge, Instanz | 0,7821 | Preiskarte 26.09.2026 (m7g.2xlarge 0,3910, m7g.xlarge 0,1955, also linear) |
| gp3, 100 GB zu 0,0952 je GB und Monat, 730 h | 0,013041 | gepinnt in `aws_box.sh`, am 26.09.2026 nicht neu gelesen |
| öffentliche IPv4-Adresse | 0,0050 | gepinnt in `aws_box.sh`, am 26.09.2026 nicht neu gelesen |
| **Box als m7g.large, gesamt** | **0,115841** | 0,0978 + 0,0050 + 0,013041 |
| **Box als m7g.4xlarge, gesamt** | **0,800141** | 0,7821 + 0,0050 + 0,013041 |

Die Research hatte den 4xlarge-Satz auf rund 0,80 USD je Stunde geschätzt
(Annahme A6); gelesen ist 0,800141. Die Verfügbarkeit von m7g.4xlarge in
eu-central-1c bleibt ungeprüft bis zum Typwechsel (Rückfall m7g.2xlarge, dann
fehlen die Stufen 12 und 16).

### 1.2 Die Posten, Weg a

| Posten | Planwert | Herleitung |
|---|---:|---|
| Handaufbau und Wiederaufbau (Runbook-Blöcke 1 bis 13) | 1 h 30 min | Ist v1.2 rund 0 h 40 min, als Untergrenze; Aufschlag für neue Fallen |
| Markenlesung und Einzelliste der 37 (P0) | 0 h 10 min | read-only, Sekunden |
| Wechsel 92d mit `occ upgrade` | 0 h 45 min | Ist 0 h 32 min in drei Läufen der v1.2 |
| Zustandsprüfung, Cron vorher, Indexgröße de,en | 0 h 15 min | |
| M-01 (Level, fünf Stufen, Leser) | 0 h 30 min | Ist Stufen 0 h 06 min |
| Kaltstart mit Trefferpflicht (bis drei Zyklen) | 0 h 20 min | Ist 95b 0 h 07 min für vier Ausprägungen |
| Bodensatz, Zyklen 1 und 2, zwei Neubauten | 0 h 30 min | Ist 94b 0 h 03 min je Zyklus bei 120 s |
| 99d | 0 h 10 min | Ist 99c 11 s |
| B2 samt Löschen und Rückkehr | 0 h 45 min | Vorarbeit 40 min |
| Umbau MESS-08 auf sechs Sprachen samt Indexgröße | 3 h 00 min | obere Schätzung, keine Verbesserung vorweggenommen |
| disjunction_max-Probe (98d) | 0 h 20 min | |
| B3 und B5 | 0 h 27 min | Vorarbeit 15 und 12 min |
| Endmessungen, Kostenrohdatei | 0 h 15 min | |
| 92c, Fehlschlag und regulär, Nullstand | 0 h 30 min | |
| Abbau bis Stop | 0 h 10 min | Ist 0 h 05 min |
| Warte- und Sitzungszeit (Tore, Handgriffe) | 3 h 00 min | v1.2: 25,75 h Box gegen rund 21 h gestempelt |
| **Summe m7g.large** | **12 h 37 min** | 757 min; mal 1,15 = **870,6 min = 14,51 h**; mal 0,115841 = **1,681 USD** |
| **B4 auf m7g.4xlarge, eigener Deckelposten (D-01)** | **1 h 15 min** | 75 min; mal 1,15 = **86,25 min = 1,44 h**; mal 0,800141 = **1,150 USD**; Status nach D-03: **gefahren, F4 = 3,955** (`rohdaten/w4-ci-arm64/f4.txt`: `F4 3.955`, Schwelle 1,5) |
| **Rechenwert gesamt** | | **15,95 h / 2,83 USD** |
| **Deckel D-01** | | **24 Boxstunden / rund 3,00 USD**; die beiden Zahlen widersprechen sich mit B4, siehe 1.3 |

B7 steht in keiner Zeile: im CI gemessen (Abschnitt 2), auf der Box entfällt
es (D-05). Stillstandszeiten, in denen die Box gestoppt ist (Typwechsel, nach
dem Abholen), kosten nur die Platten, 0,013 USD je Stunde, und sind nicht
eingerechnet. Der Korpus-Snapshot kostet unabhängig von der Anfahrt 2,79 bis
2,99 USD im Monat.

### 1.3 Die zwei Deckelvarianten, gerechnet (Pitfall 3)

Beide Varianten halten den B4-Posten mit seinem Planwert samt Zuschlag
(86 min) als eigenen Timer; der m7g.large-Teil ist der Rest. `DECKEL_MINUTEN`
zählt ab `BOX_START_EPOCH`, also mit dem Handaufbau, und endet mit dem
Herunterfahren vor dem Typwechsel; `DECKEL_REST_MINUTEN` setzt `00-lauf.sh b4`
nach dem Typwechsel neu.

| | Variante Stunden | Variante USD |
|---|---|---|
| Regel | 24 h gesamt, B4 darin | 3,00 USD gesamt, B4 darin |
| `DECKEL_REST_MINUTEN` (B4, m7g.4xlarge) | 86 | 86 |
| B4 höchstens | 1,43 h, 1,147 USD | 1,43 h, 1,147 USD |
| `DECKEL_MINUTEN` (m7g.large) | 1354 (= 1440 minus 86) | 959 (= 1,853 USD durch 0,115841, abgerundet) |
| m7g.large höchstens | 22,57 h, 2,614 USD | 15,98 h, 1,852 USD |
| **Gesamt höchstens** | **24,0 h / 3,76 USD** | **17,4 h / 3,00 USD** |
| Reserve des m7g.large-Teils gegen den Planwert 871 min | 483 min | 88 min |

Die Research nannte für die Variante Stunden rund 3,64 bis 3,80 USD; mit dem
gelesenen 4xlarge-Satz sind es 3,76 USD. In der Variante USD greift der Deckel
nach 17,4 Boxstunden, obwohl die 24 h nicht verbraucht sind; der Planwert
passt hinein, die Reserve ist aber mit 88 min kleiner als die Warte- und
Sitzungszeit der v1.2, und Streichungen nach D-05 werden wahrscheinlicher.

### 1.4 Harter Stopp und Streichreihenfolge

| Regel | Wortlaut |
|---|---|
| **D-02** | Bei Erreichen des Deckels harter Stopp der Box, fehlende Messungen als Lücken im Bericht, Nachfreigabe nur durch den Owner. Der Timer auf der Box (`shutdown -h`) ist der Stopp; er wird nicht verlängert. |
| **D-05** | Streichreihenfolge bei knapper Boxzeit: **B7** (im CI erledigt, läuft nie auf der Box), dann **B5**, dann **B4**, dann **B2 und B3**. Die Pflichtzahlen der Erfolgskriterien 2 und 3 und **B1** fallen nie. |

### 1.5 Freigabeumfang

Die Freigabe am Checkpoint umfasst: Aufbau nach Runbook aus dem
Korpus-Snapshot, den A-Record über den vorhandenen DNS-Zugang, den Typwechsel
auf m7g.4xlarge für B4 nach D-03 (Rückfall m7g.2xlarge) und zurück, und den
Abbau ohne Ende-Snapshot (der Korpus-Snapshot bleibt). Dazu zur Kenntnis
(`deferred-items.md`): 92d installiert die PHP-Hälfte als **1.2.0** auf eine
Box, deren Snapshot v1.1 trägt, weil der Versionssprung auf 1.3.0 zu Phase 23
gehört; die Migration `Version001300Date20260924000000` läuft auf der Box
deshalb nicht. Kein Messgegenstand hängt daran.

## 2. W4-Vorabkurve

Gefahren am 26.09.2026 im kostenlosen arm64-Runner, ohne Box: Workflow
`measure.yml`, Lauf 4 (Lauf-ID 36216002856), Job `slots` grün, Artefakt
`w4-arm64`, Rohdaten unverändert in `rohdaten/w4-ci-arm64/`. F4 folgt der
Definition in `skripte/00-ablauf.md`, Abschnitt 8.

**Abbild.** `ghcr.io/street1983nk/findling_backend@sha256:40ca8c2b9786151640665c378a522f200905ae428d8bbcadebdc2097c7925e3e`,
per `docker buildx imagetools inspect` von `:dev` abgelesen und vom Merge-Job
der Abbildstrecke `docker.yml` des gepushten Commits 59f05fe geschrieben
(Lauf 174, Lauf-ID 36215893830, auf `:dev` und auf den Commit-Tag gepusht).
`machine.txt` nennt denselben Digest und denselben Commit.

**Maschine.** `ubuntu-24.04-arm`, 4 CPUs (`nproc` 4), ARM Neoverse-N2,
Kernel 6.17 azure. Die Box ist eine m7g (Graviton3, Neoverse-V1) mit 2 vCPU;
die Kurve sagt, ob Slots je Kern Durchsatz kaufen, nicht was die Box absolut
schafft.

**W3, Slotkurve** (acht synthetische Scanseiten, Seed `phase-22-w4`, je Slot
eigener Kern, drei gemessene Runden, keine Runde mit verlorenem Slot):

| N | cpuset | Seiten je Sekunde, Median | Faktor zu N 1 | anon_bytes_delta je Runde |
|---|---|---|---|---|
| 1 | 0 | 0,288 | 1,000 | 9768960, -9789440, 12288 |
| 2 | 0,1 | 0,575 | 1,997 | 405504, 28672, 53248 |
| 4 | 0-3 | 1,139 | 3,955 | 819200, 65536, 135168 |

Die Wandzeit je Runde bleibt bei 27,8 bis 28,1 s, die CPU-Zeit wächst mit N:
die Slots teilen sich keinen Kern, und der Speicherzuwachs je zusätzlichem
Slot liegt unter einem MB.

**W3, Einzelmodus** (eine gerenderte Seite, 4 Kerne sichtbar):
`OMP_THREAD_LIMIT=1` 3,470 s Wand bei 3,47 s CPU, ungesetzt 2,485 s Wand bei
5,74 s CPU. Ohne Grenze nutzt tesseract also gut zwei Kerne und ist 1,40-mal
schneller; der Satz in `docs/performance.md`, dass tesseract beide Kerne
nutzt, hält.

**Einbettung, Tokens je Sekunde** (Batch 2, Sequenz 512, cpuset so breit wie
die Threadzahl, p50): T 1 1836,9; T 2 3638,5; T 4 7109,0. Faktoren 1,98 und
3,87.

**B7, niederländischer Automat nativ arm64** (`b7-nl-automat.txt`, drei
Läufe): `ram_nl_released_mb` 22,99 in allen drei, Bau 0,78 bis 0,80 s. Das
liegt unter den 24,2 bis 25,3 MB der produktnahen amd64-Messung und über den
17,6 MB der Research. Die Kennzahlen (`b7-kennzahlen.txt`) treffen die
Erwartung aus dem Kopf von `scripts/dev/measure_compounds_nl.sh` genau:
316740 Einträge, Digest `ee7f3b83...`, 21 von 28 Komposita über den
Bestandteil, 0 von 28 ohne Zerleger, 32 von 33 Wächter ganz. B7 ist damit im
CI gemessen und fällt auf der Box ganz weg (D-05).

**F4.** `f4.txt`: `F4 3.955`.

D-03 angewandt: F4 = 3,955, B4 gefahren (`B4_GEPLANT=ja`).

K1 ist nicht ausgelöst: F4 liegt über 1,5, die BL-F04-Stufe 2 kippt nicht.

Box-Digest-Kandidat: sha256:40ca8c2b9786151640665c378a522f200905ae428d8bbcadebdc2097c7925e3e, Abbildstrecke Lauf 174 (Lauf-ID 36215893830), Commit 59f05fe. Der Beweis auf der Box bleibt der Baumhash (92d, `baumhash-beweis ja`); spätere Pushes, die `backend/src` nicht ändern, schieben `:dev` weiter, ohne diesen Kandidaten zu entwerten.

## 3. Generalprobe

Gefahren am 26.09.2026 gegen die lokale Test-Nextcloud (Serverlinie 34), ohne
Box und ohne bezahlte Minute. Jede Probe schrieb in ein Verzeichnis außerhalb
des Repos; `rohdaten/` ist unberührt. Die Werte der Proben haben keine
Aussagekraft (amd64, geteilter Rechner), geprüft wurde allein, ob jedes Werkzeug
läuft und an seinen Toren das Erwartete meldet.

**Die Umgebung, und worin sie von der Box abweicht.** Die Werkzeuge liefen in
einem Hilfscontainer mit Docker-Klient, `sudo` als Durchreiche und der
cgroup-Schreibweise des systemd-Treibers (`system.slice/docker-<id>.scope`), die
auf dem Docker-Dienst dieses Rechners nachgebildet war. Das Produkt lief als
Container `nc_app_findling_backend` aus dem Abbild des aktuellen main-Stands,
gezogen per Digest `sha256:0adcfc3802730d44db436ac2b7b11d10e78425ed191753605b3742c00eb7e9d0`,
mit 2 GiB harter Grenze, auf einer Kopie des lokalen Datenbestands, angemeldet
über einen manual-install-Daemon statt HaRP. Der Baumhash dieses Abbilds ist
gleich dem des Arbeitsbaums (92d, `baumhash-beweis ja`). An diesem Docker-Dienst
laufen drei Nextcloud-Instanzen, eine davon die Test-Nextcloud.

| Werkzeug | Probe | erwartet | tatsächlich | Befund |
|---|---|---|---|---|
| alle `.sh` des Verzeichnisses, W1, W2 | `sh -n` unter dash | 0 | 0 | keiner |
| W1 `cpu_sampler.sh` | 30 s gegen den Produktcontainer | Datenzeilen und Schlusszeile | 6 Zeilen, `summary ... reason=signal` | keiner |
| W2 `proc_anon_sampler.sh` | 30 s gegen den Produktcontainer | Datenzeilen und Schlusszeile, keine cmdline | 18 Zeilen, Schlusszeile, kein cmdline | keiner |
| W3 `ocr_slot_probe.py` (über b3) | N 1, N 2, Einzelmodus | je eine Zahl | `pages_per_second_median` für N 1 und 2, `rounds 3` im Einzelmodus | keiner |
| `90e` marken | Kopie der lokalen state.db, Erwartungen aus `00-lauf.sh` | Rückgabe nach Stand der lokalen Marken | 45: lokal steht `embedding_version unknown`; die übrigen Marken gleich, `tantivy_version` am `index_format` verglichen | keiner (lokaler Stand) |
| `90e` liste | dieselbe Kopie | JSON mit Zählung und Einzelliste | 0, Zählung je state und Einzelliste ohne Pfade | keiner |
| `91m` | Kaltstart-Fenster aus 95c, loglevel 1 und zurück auf 2 | Zeilen gezählt, kein `unklar` | zuerst `langsame-aufrufe 0` bei einer vorhandenen Zeile, nach dem Fix `langsame-aufrufe 1` | **behoben** (463fcfe, a65c9c5): Nextcloud 34 schreibt `innerMs` und `ceilingMs` als Zeichenketten, der Leser nahm nur JSON-Zahlen und zählte die Zeile als kaputt. Auf der Box hätte jede Stufe 0 gemeldet und die Gegenprobe den Lauf mit 57 beendet |
| `92e` | Entladefrist 120, dann 0 | 0, Grenze und Schalter zurückgelesen | 0 und 0, `speichergrenze-ist 2147483648/0`, `entladeschalter-ist 120` und `0` | keiner |
| `92e` | Sprachen de,en,es,it,nl,pt, dann de,en | 0, Umbau mit Logzeile | 0 und 0; „the rebuilt index directory is in place“ nach 5 s, mit derselben Suche wie in `00-lauf.sh` gefunden | keiner |
| `92d` | lokaler Digest, Daemon der Probe | 41 nach `occ upgrade` und Registrierung | **37** in Phase A: die Zählung meldet 3 Nextcloud-Instanzen am Docker-Dienst; Phase A lief ganz (Digest gleich, Baumhash dreifach, `baumhash-beweis ja`) | Das Tor 37 hat richtig gehalten; es mit einer anderen Zählung zu umgehen hätte die Nachbarinstanzen getroffen. Phase B lief deshalb im CI (nächste Zeile) |
| `92d` Phase B, CI | `probe-92d.yml` im arm64-Runner: Container-Nextcloud 34 mit HaRP, v1.1.0 installiert (Companion und Abbild), Referenzkorpus indexiert, dann 92d per Box-Digest-Kandidat; Gegenprobe mit einem Bestand, der um eins daneben liegt | 0 mit `92D-WECHSEL-FERTIG`; Gegenprobe 41 | Lauf 2 (Lauf-ID 36217297257) grün: `occ upgrade` fuhr das App-Update 1.1.0 auf 1.2.0 mit 0, unregister 0, `volumen-nach-unregister nc_app_findling_backend_data` mit unveränderter Erstellungszeit, Registrierung ja, `speichergrenze-ist 2147483648/0`, Baumhash im laufenden Container gleich, Bestandstor 26 / 7 / 6 bestanden, danach dieselben Zahlen aus dem Container und ein Treffer der Suche; Gegenprobe 41 mit `bestandstor-bestanden nein` und unverändertem Bestand | **behoben** (bbf929e): 92d nahm von `occ upgrade` nur 0 an, `deploy-harp.yml` belegt 3 (ERROR_UP_TO_DATE) als Antwort ohne Arbeit; jetzt gelten 0 und 3. Lauf 1 (36216798070) startete ab v1.2.0 und hatte kein App-Update, weil der Baum bis Phase 23 noch 1.2.0 trägt |
| `94c` | Frist 120, drei Dateien je Zyklus | Marken A, C1, C2, Rückgabe 0 | 0, A, C1 und C2 geschrieben, beide Ordner entfernt | **behoben** (5d97688): `abtastreihe-spitze-mb` klebte Datum und Stunde an die Megabyte (16982026092523 statt 1698); Probe wiederholt mit 1698 |
| `95c` | Begriff mit lokalen Treffern | `kaltstart-gueltig ja` | 0, `kaltstart-gueltig ja` im ersten Kaltzyklus | keiner |
| `98d` | `docker cp` und `docker exec` im Produktcontainer, de,en und nach dem Umbau auf sechs Sprachen | 0 oder 49 mit Analyse | 0 und 0 (4 und 8 Felder), keine `treffermenge-ungleich`-Zeile | keiner |
| `00-wegwerf.sh b3` | Abbild per Digest, Leerlaufprüfung | `B3-FERTIG` | 0, Leerlauf ja, Scan gebaut, drei Proben mit Zahl | keiner |
| `00-wegwerf.sh b5` | Abbild per Digest, vier Kombinationen | `B5-FERTIG` | 0, je Kombination `tokens_per_second_p50` und `b5-max-anon` | keiner |
| `00-lauf.sh` | `ablauf`, `b4` und ohne Befehl, ohne Laufwerte | 2 | 2, 2, 2; kein Verzeichnis angelegt | keiner |
| `00-lauf.sh` Statusreihe | Leser der Umbaureihe gegen eine echte Antwort der Admin-Übersicht | fünf Felder | `embedded`, `languagesActive`, `rebuildDone`, `rebuildRunning`, `rebuildTotal` gelesen | keiner |
| `00-abholen.sh` | Vorgaben ohne Schlüssel; unerreichbare Adresse aus TEST-NET-2 | 2; 1 nach drei Fehlversuchen | 2; 1 nach drei Fehlversuchen | **behoben** (c24f142): im Zustandsverzeichnis lagen weder Schlüssel noch known_hosts. Der Schlüssel fiel schon mit 2 auf, die fehlende known_hosts erst nach drei Takten; jetzt 2 vor dem ersten Takt |

**Was die Generalprobe nicht beantworten konnte**, und es steht hier, damit es
nicht als geprobt gelesen wird:

- **92d Phase B auf der Box selbst.** Im CI gelaufen (Tabelle oben), mit einer
  Container-Nextcloud aus `nextcloud:34-apache` statt AIO, 39 Dateien statt
  52.111 und einem v1.1.0-Volumen, das dort frisch indexiert wurde. Ob das
  Volumen des Snapshots dieselben Marken trägt, liest erst die Box (Research,
  Annahme A1).
- **Weg b und 92c ohne `occ upgrade`.** In Weg b läuft 92c vor jedem
  `occ upgrade`. Bringt 92c eine PHP-Hälfte mit neuer Version auf eine Instanz
  mit älterer, steht die Nextcloud danach vermutlich auf „requires upgrade“, und
  die Registrierung findet `app_api:app` nicht (Befund Lauf 1 der v1.2). Weg a
  ist nicht betroffen, weil 92d vorher das upgrade fährt.
- **M-01 unter Last** (`search_load.py` gegen das Lastkonto) und der
  Wirkungszweig von `97-cron-vorpruefung.sh` sind gefahrene Fassungen der v1.2
  und wurden nicht erneut geprobt.

## 4. Laufwerte

Festgelegt am 26.09.2026 aus dem Owner-Entscheid (Variante Stunden, Weg a,
F4 bestätigt). Diese Werte kommen auf der Box in die Laufwertedatei
(`LAUFWERTE`, Vorgabe `$HOME/work/v13-lauf.env`, außerhalb des Repos);
`BOX_START_EPOCH` und `ABBILD_DIGEST` setzt der Aufbau am Anfahrtstag.

| Laufwert | Wert | Herleitung |
|---|---|---|
| `DECKEL_MINUTEN` | 1354 | Variante Stunden: 24 h = 1440 min gesamt, minus der B4-Posten mit Zuschlag (86 min); zählt ab `BOX_START_EPOCH` samt Handaufbau, höchstens 22,57 h zu 0,115841 USD = 2,614 USD |
| `DECKEL_REST_MINUTEN` | 86 | B4-Posten 75 min mal 1,15 = 86,25 min, abgerundet; `00-lauf.sh b4` setzt damit den Timer nach dem Typwechsel, höchstens 1,43 h zu 0,800141 USD = 1,147 USD |
| `B4_GEPLANT` | ja | D-03: F4 = 3,955 (`rohdaten/w4-ci-arm64/f4.txt`) ist mindestens 1,5; die Definition (N 4 gegen N 1) hat der Owner bestätigt |
| `EINZELWEG` | a | Frage 1, Weg a: die 37 des Snapshots einzeln in P0, die 44 / 6 der v1.2-Box nicht reproduzierbar; `00-lauf.sh` unverändert |

Gesamt höchstens 24,0 Boxstunden und 3,76 USD; der Rechenwert des Plans liegt
bei 15,95 h / 2,83 USD (1.2). Stillstand mit gestoppter Box kostet nur die
Platten und ist nicht eingerechnet.

## 5. Offene Owner-Fragen

Vorgelegt am 26.09.2026, beantwortet am 26.09.2026 (Checkpoint 22-07). Die
Antwort des Owners, „machen wir nach deiner empfehlung“, auf die Empfehlung
„Weg a, Deckel stunden, dismax vorschlag, F4 bestaetigt, freigegeben“: Weg a,
Variante Stunden, die dismax-Regel des Research-Vorschlags, F4 wie angewandt,
Anfahrt freigegeben. Wortlaut, Datum und die beschlossene Regel ohne Ermessen
stehen in `skripte/00-ablauf.md`, Abschnitt 6. Die Fragen bleiben unten in der
vorgelegten Form stehen.

### Frage 1: Wie werden die 6 Fehlschläge und 44 Übersprungenen benannt?

**Die Lage.** Die 52.137 / 44 / 6 sind der Endstand der v1.2-Box
(`docs/measurements/2026-09-v12-messung/rohdaten/93-kosten-und-verbleib.txt`).
Deren Volume ist am 21.09.2026 ohne Ende-Snapshot zerstört worden (Owner-Entscheid
Frage B aus 15-08, Beleg
`docs/measurements/2026-09-v12-messung/rohdaten/07-snapshot-und-abbau.txt`
und `93-kosten-und-verbleib.txt`), keine Rohdatei nennt die Dateien. Der
Korpus-Snapshot trägt 52.111 / 37 / 0 (v1.1-Box, 11.09.2026).

**Was in v1.2 hinzukam, aus Skripten und Rohdaten der v1.2 ermittelt.** Zwei
Uploads, sonst keiner:

- `98c-sprachfaelle.sh`: die **39 Dateien** von `testdata/corpus` über WebDAV
  in das Konto `sprachfall` (`05-sprachfaelle.txt`: `dateien-hochgeladen 39`,
  Upload 17 s, Arbeitsvorrat nach rund 6 min leer). Darunter stehen die
  absichtlich kaputten und bösartigen Dateien 24 bis 39 (abgeschnittener
  Trailer, kaputte xref, Zip-Bombe, AES-256, Seitenbaum-Zyklus und andere),
  dazu Null-Byte-, Passwort- und Scan-Dateien 01 bis 23.
- `94b-grundlast-rueckkehr.sh` (MEM-02): **12 kleine Textdateien**, alle
  eingebettet (52.137 auf 52.149) und danach wieder gelöscht
  (`indexlauf-korpus-entfernt=204`). Sie tragen zu 44 / 6 nichts bei.

Die Differenz zwischen Snapshot und v1.2-Endstand ist 26 / 7 / 6, zusammen 39,
genau die Größe des Korpus. Der CI-Lauf `probe-92d.yml` (Lauf-ID 36217297257)
hat denselben Korpus auf arm64 mit v1.1.0 indexiert und ebenfalls **26 / 7 / 6**
gezählt. Das ist ein Befund aus Zählungen, keine Benennung: ob die 7 und 6 der
v1.2-Box genau diese Dateien waren, ist auf keiner Box gelesen, und ob die 39
schon im Snapshot liegen (98b hatte sie am 10.09. hochgeladen, der Snapshot
entstand am 11.09.), zeigt erst die Einzelliste in P0.

| Weg | Was benannt wird | Zusatzzeit | Deckel und Kosten | Folge |
|---|---|---|---|---|
| **(a)** | die **37 übersprungenen** des Snapshots einzeln (P0, `90e-einzelliste.json`); die 44 / 6 der v1.2-Box als **nicht reproduzierbar** dokumentiert | 0 (P0 ist schon im Plan) | wie 1.3: 24 h / 3,76 USD oder 17,4 h / 3,00 USD | MESS-07 Punkt 4 wird mit dem vorhandenen Datenbestand erfüllt, nicht mit den ursprünglichen 44 / 6. `00-lauf.sh` bleibt unverändert |
| **(b)** | ein **v1.3-Vollreindex** von leer, dessen neue Endzahl einzeln benannt wird (`90e-einzelliste-nach-vollreindex.json`) | **rund +20 h** (Vollreindex v1.2: 19 h 20 min, dazu die acht Leerlauflesungen); dafür entfällt 92d (45 min) | Planwert m7g.large 31 h 52 min, mal 1,15 = 36,65 h = 4,245 USD; mit B4 **38,1 h / 5,40 USD**. Ein Deckel von **40 h** hieße `DECKEL_MINUTEN` 2314 und `DECKEL_REST_MINUTEN` 86, höchstens **5,61 USD**, Reserve 115 min. Die Research nannte 4,70 USD; das waren 40 h zum m7g.large-Satz ohne den 4xlarge-Satz für B4. Unter 3,00 USD ist Weg b nicht möglich | Reihenfolge 92c zuerst. **Neues Risiko:** in Weg b läuft 92c vor jedem `occ upgrade`. Bringt 92c die PHP-Hälfte 1.2.0 auf die v1.1-Instanz des Snapshots, steht die Nextcloud danach vermutlich auf „requires upgrade“, und die Registrierung findet `app_api:app` nicht (Befund Lauf 1 der v1.2). Das ist weder lokal noch im CI geprobt (Abschnitt 3); in Weg a fährt 92d das upgrade vorher |
| **(c)** | **Teilweg:** die 39 Korpusdateien aus 98c erneut, in einen eigenen Ordner, und deren Fehlschläge und Übersprungene einzeln (`90e-teilweg.json`); die MEM-02-Dateien entfallen, weil sie alle eingebettet wurden | Planwert rund **25 min** (Upload, `files:scan`, Warten auf Vorrat 0 wie in 98c rund 6 min, `90e liste`, Ordner löschen, Rückkehr auf 52.111 / 37 / 0); mal 1,15 rund 29 min | rund **0,06 USD**; passt in beide Varianten aus 1.3, in der Variante USD sinkt die Reserve von 88 auf rund 59 min | benennt die Dateien, die die Differenz 7 / 6 sehr wahrscheinlich ausmachen, aber nicht die 44 / 6 der v1.2-Box selbst. Der Block `teilweg` wird erst nach dem Entscheid in `00-lauf.sh` gebaut und getestet (nach 92d, vor „Cron vorher“), Rückkehrtor mit 56 |

### Frage 2: Welcher Deckel gilt?

D-01 nennt 24 Boxstunden und rund 3,00 USD. Mit B4 auf m7g.4xlarge passen
beide Zahlen nicht zusammen (Rechnung in 1.3):

- **Variante Stunden:** 24 h gelten, B4 darin; höchstens **3,76 USD**.
  Timerwerte `DECKEL_MINUTEN` 1354, `DECKEL_REST_MINUTEN` 86.
- **Variante USD:** 3,00 USD gelten, B4 darin; höchstens **17,4 h**
  Gesamtzeit. Timerwerte `DECKEL_MINUTEN` 959, `DECKEL_REST_MINUTEN` 86.

Bei Weg b gilt keine der beiden; dann ist der Deckel neu festzulegen (Zeile
Weg b oben).

### Frage 3: Nach welcher Regel fällt die Messung für disjunction_max aus, und gilt F4 so?

**Die Regel.** Sie muss vor der Messung feststehen (D-04, E10). Der
**Vorschlag der Research, nicht beschlossen**, wörtlich aus
`skripte/00-ablauf.md`, Abschnitt 6:

> Vorteil für dismax, wenn der Median von RBO@10 gegen den Altplan unter dismax
> um mindestens 0,05 höher liegt als unter der Summe, kein Sprachfall-Eigenrang
> schlechter wird und die lexikalische Latenz um höchstens 20 Prozent steigt;
> tie 0.0 gegen 0.1 wird mitgemessen.

Die Schwellen 0,05 und 20 Prozent sind ohne Relevanzurteile gesetzt
(Annahme A7). Der Owner nimmt den Vorschlag an, legt andere Schwellen fest oder
eine andere Regel; offen ist dabei auch, welche Rolle tie 0.0 und 0.1 im
Entscheid spielen.

**Die F4-Definition.** Angewandt wie in `skripte/00-ablauf.md`, Abschnitt 8:
Seiten je Sekunde bei N = 4 auf `--cpuset-cpus 0-3` geteilt durch Seiten je
Sekunde bei N = 1 auf `--cpuset-cpus 0`, je Median dreier Runden. Gemessen
1,139 durch 0,288, **F4 = 3,955** (Abschnitt 2); nach D-03 ist B4 damit
gefahren. Der Owner bestätigt die Definition oder nennt eine Alternative, die
aus den vorhandenen CI-Rohdaten in `rohdaten/w4-ci-arm64/` ohne neuen Lauf
rechenbar ist (etwa N = 2 gegen N = 1: 1,997, oder die Tokens je Sekunde der
Einbettung T 4 gegen T 1: 3,87).

## 6. Bericht

Offen. Wird nach der Anfahrt geschrieben: Urteil je Erwartung E1 bis E14,
gestrichene Blöcke und Lücken, Kosten gegen den Deckel.

**Nachtrag vom 26.09.2026 (Plan 22-11):** geschrieben. Die Urteile stehen in
6.12, die ausgewerteten Zahlen in 6.13, die Prüfsummen der gefahrenen
Fassungen in 6.14; Kosten in 6.8, Lücken in 6.9 und 6.11. Die Abschnitte 6.1
bis 6.11 bleiben als Protokoll der Anfahrt stehen.

### 6.1 Tor-Abbruch in P1, Rückgabewert 41 (26.09.2026)

**Was geschah.** Aufbau nach Runbook, Blöcke 1 bis 13, von 04:58:54Z bis
05:10Z (`rohdaten/02-vorbedingungen.txt`, `03-aufbau.txt`), Vorprüfung
`shutdown-verhalten stop` (`00-typwechsel.txt`). Die Rohdaten dieser ersten
Fahrt liegen unverändert in `rohdaten/lauf1-tor41/`. `00-lauf.sh start` um
05:10:34Z, Timer auf 2026-09-27T03:33:34Z gesetzt und zurückgelesen
(`00-timer.txt`, Modus poweroff). Das Markentor bestand (`90e-marken.txt`,
`marken-urteil umbau`), die Einzelliste lief mit 0. 92d fuhr Phase A und B bis
zum Ende: Baumhash-Beweis ja, `occ upgrade` 0, Volumen nach dem unregister
erhalten, Registrierung ja, Grenze 2147483648/0. Dann das Bestandstor:

```
bestandstor indexiert 52137 uebersprungen 44 fehlgeschlagen 6
bestandstor-erwartet indexiert 52111 uebersprungen 37 fehlgeschlagen 0
bestandstor-bestanden nein
```

92d endete mit **41**, `00-lauf.sh` mit `tor-abbruch p1-92d rueckgabe 41`
(05:13:43Z) und zog den Timer auf 60 Minuten vor. Um 05:14Z sind die Rohdaten
abgeholt und die Box per `aws_box.sh stop` angehalten worden: 0,25 Boxstunden,
0,0287 USD. Sie steht gestoppt, mit Volumen, Korpus und dem Stand nach 92d.

**Die Ursache, aus den Rohdaten.** Der Snapshot trägt nicht 52.111 / 37 / 0,
sondern bereits **52.137 / 44 / 6**: die Einzelliste (`lauf1-tor41/90e-einzelliste.json`)
zählt je Zustand 52137 indexiert, 44 übersprungen, 6 fehlgeschlagen und nennt
alle 50 einzeln (22 `too_large`, 16 `empty_text`, 4 `image_not_ocrable`, 2
`encrypted`, 5 `corrupt`, 1 `empty_file`). Die Differenz 26 / 7 / 6 ist genau
der 39-Dateien-Korpus des Kontos `sprachfall`, und der liegt im Snapshot: das
Konto besteht, unter `ncdata/sprachfall/files` stehen 39 Dateien
(`03-aufbau.txt`, Abschnitt Sprachfall-Bestand). 98b hatte sie am 10.09.
hochgeladen, der Snapshot vom 11.09. hat sie mitsamt ihrem Indexstand
aufgenommen. Die Beschreibung des Snapshots (52111 Dokumente) und das Tor aus
E2 nannten den Stand vor diesem Upload.

**Folgen, ohne Entscheid.**

- E2 ist nach dem Wortlaut verfehlt; die Zahl, die das Tor gelesen hat, ist die
  des Snapshots und kein Schaden der Box. Der Wechsel selbst ist gelungen.
- Frage 1 steht auf einer falschen Annahme: die 44 / 6 der v1.2-Box sind
  **reproduzierbar**, sie sind der Stand des Snapshots, und die Einzelliste
  benennt sie bereits einzeln (MESS-07 Punkt 4). E3 („37 und 0“) ist damit
  ebenfalls verfehlt, im Sinne von MESS-07 aber übererfüllt.
- MESS-09: die Sprachfall-Dateien stehen im Bestand, Bedingung 2 der
  dismax-Regel ist zuzuordnen (deferred-items 22-07).
- Ein Weiterlauf braucht zwei Sollwerte, die heute im Werkzeug stehen: das
  Bestandstor von 92d (per Umgebung `BESTAND_INDEXIERT`,
  `BESTAND_UEBERSPRUNGEN`, `BESTAND_FEHLGESCHLAGEN` einstellbar) und die
  Rückkehr nach B2 in `00-lauf.sh` (`BESTAND_SNAPSHOT="52111 37 0"`, als
  Konstante fest, sonst 56). Ein Werkzeug wird in bezahlter Zeit nicht
  geändert (Runbook 7.1); die Fortsetzung ist ein Owner-Entscheid (D-02).
- Der Deckel zählt ab `BOX_START_EPOCH` (LaunchTime 04:59:25Z); verbraucht
  sind 0,25 h von 24 h. Der gestoppte Zustand kostet nur die Platten, rund
  0,31 USD je Tag.

**Entscheid (26.09.2026, Checkpoint 22-08).** Owner, wörtlich: „wie deine
empfehlung“, also Option A: Sollwert des Snapshots 52.137 / 44 / 6 in 92d und
in `00-lauf.sh`, E2 und E3 neu gefasst (`skripte/00-ablauf.md`, Abschnitt 3 und
Nachtrag in Abschnitt 6), Neustart mit dem Restdeckel ab LaunchTime 04:59:25Z.
Die zweite Fahrt schreibt wieder nach `rohdaten/`.

### 6.2 Zweite Fahrt, Tor-Abbruch in PII, Rückgabewert 58 (26.09.2026)

**Was lief.** Start 05:38:31Z mit 1315 Restminuten (`rohdaten/04-wiederanlauf.txt`,
`00-timer.txt`). 92d mit 0, Bestandstor 52.137 / 44 / 6 bestanden. Cron vorher 300 s,
Indexgröße de,en 786.508.818 Byte, M-01 alle fünf Stufen, Bodensatz mit
`zyklus2-minus-c1 30.5`, B2 vollständig: 140 Scans, Vorrat 0 um 06:12:18Z,
Rückkehr auf 52.137 / 44 / 6 um 06:16:54Z.

**Drei Befunde ohne Abbruch** (`00-lauf.txt`, Zeilen `befund`):

- 95c endete mit **48**: die Suche „Bescheid Antrag“ als `admin` lieferte in
  allen drei Kaltzyklen 0 Treffer (Latenzen 2.028, 2.109, 2.084 ms). Damit ist
  auch die M-01-Gegenprobe nicht entschieden.
- 94c endete mit **32**: die Kennzahlen stehen (`zyklus2-minus-c1 30.5`), nur
  `abtastreihe-spitze-mb` ist unlesbar (`rss_digest: no series with a
  findling-rss prefix`).
- 99d endete mit **34**: der Arbeitsvorrat stand bei 2 (`bestand-steht=nein`),
  unmittelbar nach den Uploads und Löschungen von 94c.

**Der Abbruch.** 92e baute den Container mit sechs Sprachen neu (0), und
`00-lauf.sh` las die erste Statuszeile um 06:16:59Z, 4 s nach dem
Containerstart. Das Backend antwortete da noch nicht: `embedded 0`,
`rebuildTotal 0`, `languagesActive` leer. Die zweite Zeile um 06:17:29Z trug die
echten Werte (`embedded 52137`, Umbau 2.500 von 52.137). Das Werkzeug nahm die
0 als Ausgangswert, meldete `embedded-bewegt von 0 auf 52137` und endete mit
**58**. Die Vektorspur hat sich nicht bewegt: 52.137 ist der Bestand. Die Box
ist um 06:18Z abgeholt und angehalten worden. Diese Uptime: 0,73 h, 0,0843 USD.
Zusammen mit der ersten Fahrt sind das 0,98 h und 0,113 USD.

**Stand der Box.** Gestoppt, mitten im Umbau: der Container trägt
`FINDLING_LANGUAGES=de,en,es,it,nl,pt`, `index.rebuild` hatte 72.649.972 Byte.
Nach einem Start nimmt das Backend den Umbau vermutlich von selbst wieder auf.
Eine saubere Wandzeitmessung verlangt dann entweder den Rückweg über 92e auf
de,en vor dem nächsten Umbau oder das Hinnehmen eines angefangenen Umbaus.
Beides ist ein Owner-Entscheid.

### 6.3 Wiedereinstieg ab PII, Tor-Abbruch 59 (26.09.2026)

Owner-Entscheid A („ja bitte“), Fix in aecca7d. Start 11:52:32Z, `00-lauf.sh
start ab-pii` um 11:53:01Z. Den Timer hat `shutdown +941` auf 03:34:01Z gesetzt,
wegen der Minutenrundung 36 s hinter dem Deckelende. Er ist sofort absolut auf
**2026-09-27T03:33:00Z** gesetzt und zurückgelesen worden (`00-timer.txt`).
Markentor 0, Bestand 52.137 / 44 / 6. Der Rückweg über 92e auf de,en lief mit 0.
Danach meldete die Admin-Übersicht sieben Minuten lang nur Nullen, das Werkzeug
endete mit **59**.

**Ursache:** Die Übersicht antwortete 200 mit `backendReachable false`. Der
Container lief und war bewaffnet, der Name löste auf. Nextcloud erreichte das
Backend über AppAPI aber nicht, weil nach dem Maschinenstart der wiederkehrende
Handgriff aus Runbook Block 11 fehlte (`app_api:app:disable` und `enable`). Er
ist ein Bedienfehler dieses Wiederanlaufs, kein Werkzeug- und kein Boxbefund.
Das Tor hat fail-closed gehalten, der halbe `index.rebuild` (237 MB) ist nicht
verworfen worden. Uptime 0,16 h, 0,0189 USD. Gesamt bisher 1,14 h und
0,132 USD. Die Box ist gestoppt (`rohdaten/04-wiederanlauf.txt`).

### 6.4 Bewaffnung nachgeholt, Befund in 92e (26.09.2026)

Owner-Entscheid A zum Tor 59: Box starten, zuerst bewaffnen, dann `ab-pii`.
Start 12:04:44Z, A-Record nachgezogen, Hostschlüssel gleich. Ein
Sicherheitstimer stand sofort absolut auf 2026-09-27T03:33:00Z, zurückgelesen.
Eine Nextcloud am Docker-Dienst, `app_api:app:disable` erfolgreich, dann hing
`app_api:app:enable` fünf Minuten ohne Antwort. HaRP meldete dabei alle 6 s
`Cannot resolve 'findling_backend' to IP address`.

**Befund:** Der Container, den `92e-umgebung.sh` im Rückweg gebaut hat, steht im
Netz `nextcloud-aio` ohne Alias (`aliases []`, Hostname zufällig). 92e übernimmt
Abbild, Umgebung, Mounts, Labels, Restart-Policy und NetworkMode, aber keine
Netzaliase. Der Kopf des CI-Musters sagt dazu, dort gebe es keine
(`deploy-harp.yml`, Netz `host`). Auf der Box löst HaRP die App-Kennung über
den Namensdienst des Netzes auf. In der zweiten Fahrt fiel das nicht auf,
weil HaRP die Adresse aus der Registrierung durch 92d noch kannte. Nach dem
Maschinenstart musste er neu auflösen und fand keinen Namen mehr. Damit
erklärt sich auch das `backendReachable false` des Tors 59: die fehlende
Bewaffnung war nicht die einzige Ursache.

Die Box ist um 12:13Z angehalten worden, nichts wurde gemessen. Uptime 0,14 h,
0,0164 USD, gesamt bisher 1,28 h und 0,148 USD. Stand: `enable` war nicht
fertig, die App steht in AppAPI vermutlich auf deaktiviert. Der Container
trägt de,en, das halbe `index.rebuild` (237 MB) liegt noch auf dem Volumen.
Weiterarbeit braucht einen Werkzeugentscheid, weil jeder weitere 92e-Neubau
(Rückweg, Umbau) denselben Container ohne Alias baut.

### 6.5 Fix 92e gefahren, Tor 59 aus dem eigenen Kriterium des Rückwegs (26.09.2026)

Owner-Entscheid A zum Befund 92e, Fix in be35cfe. Start 12:21:40Z, Timer sofort
absolut auf 2026-09-27T03:33:00Z, zurückgelesen. 92d lief mit 0 (Ausgabe in
`rohdaten/ab-pii-92d/`): Baumhash-Beweis ja, `occ upgrade` 0, Registrierung ja,
Grenze 2147483648/0, Entladeschalter 0, Bestandstor 52.137 / 44 / 6 bestanden.
Der von AppAPI gebaute Container trägt den Alias `findling_backend`, das
bestätigt den Befund aus 6.4. Die Bewaffnung ging diesmal durch (`disable` und
`enable` erfolgreich), die Übersicht meldete um 12:25:04Z `backendReachable
True` (`ab-pii-92d/bewaffnung.txt`). `ab-pii` startete um 12:25:14Z, der Timer
wurde danach wieder absolut auf 03:33:00Z gezogen. Markentor 0, Bestand
52.137 / 44 / 6. Der Rückweg über 92e lief mit 0, und der neue Container trägt
den Alias (`netz-aliase findling_backend quelle alter-container`).

**Warum trotzdem 59:** Das Backend antwortete vom ersten Takt an mit
`embedded 52137` und `languagesActive de,en`. Nur `rebuildTotal` stand auf 0,
und zu Recht: unter de,en ist kein Umbau fällig. Das Kriterium
`backend_hat_geantwortet` (`rebuildTotal` über 0) ist für den Umbau richtig,
im Rückweg aber falsch, denn dort gilt gerade der Ruhezustand ohne Umbau. Das
ist ein Fehler in meinem Fix aecca7d, nicht an der Box. Das halbe
`index.rebuild` ist nicht verworfen worden. Uptime 0,16 h, 0,0190 USD, gesamt
bisher 1,44 h und 0,167 USD. Die Box ist gestoppt.

### 6.6 Laufende

**Ende: regulär.** `rohdaten/00-FERTIG`: `fertig 2026-09-26T13:06:26Z ... weg a
b4 vorbereitet`. Die Box hat nach der letzten Abholung (13:12:52Z) selbst
abgeschaltet, stopped seit spätestens 13:13:39Z. Kein harter Stopp: der Timer
stand absolut auf 2026-09-27T03:33:00Z und wurde nicht erreicht. Die Box bleibt
gestoppt für 22-09 (B4, Abbau). Der Grub-Drop-in `mem=4G` ist entfernt
(`b4-vorbereitet grub-dropin-entfernt ja`).

**Kosten m7g.large, sechs Uptimes** (`aws_box.sh stop`, gepinnter Satz): 0,25 h
+ 0,73 h + 0,16 h + 0,14 h + 0,16 h + 0,58 h = **2,02 h, 0,232 USD**. Deckel des
m7g.large-Teils: 22,57 h / 2,614 USD. Gestoppte Zeit kostet nur die Platten.

**Die Blöcke mit Start- und Endstempel** (`rohdaten/00-lauf.txt`; Fahrt 1 in
`rohdaten/lauf1-tor41/00-lauf.txt`):

| Fahrt | Block | Start | Ende |
|---|---|---|---|
| 1 | p0-timer, p0-marken, einzelliste | 05:10:34Z | 05:10:35Z |
| 1 | p1-92d | 05:10:35Z | Tor 41, 05:13:43Z |
| 2 | p0-timer, p0-marken, einzelliste | 05:38:31Z | 05:38:31Z |
| 2 | p1-92d | 05:38:31Z | 05:39:01Z |
| 2 | cron-vorher | 05:39:01Z | 05:39:02Z |
| 2 | indexgroesse-de-en | 05:39:02Z | 05:39:02Z |
| 2 | m01 (fünf Stufen, 95c) | 05:39:02Z | 05:43:09Z |
| 2 | bodensatz | 05:43:09Z | 05:50:26Z |
| 2 | 99d | 05:50:26Z | 05:50:26Z |
| 2 | b2 | 05:50:26Z | 06:16:54Z |
| 2 | p2-umbau | 06:16:54Z | Tor 58, 06:17:30Z |
| ab-pii 1 | p0-timer, p0-marken, p0-bestand | 11:53:01Z | 11:53:02Z |
| ab-pii 1 | rueckweg | 11:53:02Z | Tor 59, 12:00:24Z |
| ab-pii 2 | p0-timer, p0-marken, p0-bestand | 12:25:14Z | 12:25:15Z |
| ab-pii 2 | rueckweg | 12:25:15Z | Tor 59, 12:30:25Z |
| ab-pii 3 | p0-timer, p0-marken, p0-bestand | 12:41:48Z | 12:41:49Z |
| ab-pii 3 | rueckweg (`index.rebuild` verworfen, Bestand 52.137 / 44 / 6) | 12:41:49Z | 12:41:52Z |
| ab-pii 3 | kaltstart-lasttest | 12:41:52Z | 12:42:21Z |
| ab-pii 3 | 99d-wiederholung | 12:42:21Z | 12:43:04Z |
| ab-pii 3 | p2-umbau (`umbau-wandzeit-s 581`) | 12:43:04Z | 12:53:17Z |
| ab-pii 3 | indexgroesse-sechs-felder (1.431.953.684 Byte) | 12:53:17Z | 12:53:17Z |
| ab-pii 3 | 98d (Rückgabe 0) | 12:53:17Z | 12:53:33Z |
| ab-pii 3 | b3 (Rückgabe 0) | 12:53:33Z | 12:58:16Z |
| ab-pii 3 | b5 (Rückgabe 50) | 12:58:16Z | 12:59:57Z |
| ab-pii 3 | endmessungen (90-bestand 0) | 12:59:57Z | 13:00:06Z |
| ab-pii 3 | 92c (Fehlschlag 36, regulär 0, 93-nullstand 0) | 13:00:06Z | 13:06:25Z |
| ab-pii 3 | b4-vorbereitung, abschluss | 13:06:25Z | 13:06:26Z |

Zwischen den Fahrten liegen die Bewaffnung und 92d von Hand
(`rohdaten/ab-pii-92d/`, 12:24Z: 92d 0, Bestandstor bestanden;
`backendReachable True` um 12:25:04Z und 12:41:38Z).

**Gestrichene Blöcke:** keine. `00-gestrichen.txt` gibt es nicht; jede
`zeit_fuer`-Prüfung (B2, B3, B5, B4) hatte Rest. B7 lief nach D-05 im CI.

**Lücken und Befunde, gegen die Pflichtliste gestellt** (Erfolgskriterien 2
und 3, B1):

- **Kaltstartlatenz mit Trefferpflicht (MESS-07): Lücke.** 95c endete zweimal
  mit 48. Als `admin` (Fahrt 2) lieferten die kalten Suchen 0 Treffer, 2.028
  bis 2.109 ms. Als `lasttest` (ab-pii 3, Sitzung `admin`) ebenfalls 0 Treffer
  bei 1.828 und 1.832 ms, obwohl dieselbe Suche warm 26 Treffer liefert. Der
  Korpus gehört `lasttest`: 52.114 Dateien gegen 64 unter `admin`
  (`zusatz-korpus-und-kaltstart.txt`). Damit ist auch die M-01-Gegenprobe im
  Kaltstart-Fenster nicht entschieden. Warum eine kalte Suche leer zurückkommt,
  die warm trifft, beantwortet dieser Lauf nicht. Das gehört in die Auswertung
  (22-10/22-11).
- **M-01 Laststufen:** alle fünf Stufen gefahren (`m01-stufe-*.json`,
  `m01-langsame-aufrufe.txt`).
- **Bodensatz:** `zyklus2-minus-c1 30.5`; Befund 32, weil nur
  `abtastreihe-spitze-mb` unlesbar ist.
- **99d:** Fahrt 2 mit 34 (Vorrat 2); Wiederholung nach Vorrat 0 mit **0**
  (`99d-filter-sortierung-wiederholung.txt`).
- **92c-Paar:** 36 und 0 wie erwartet (E11).
- **Einzelliste:** 50 Dateien einzeln benannt (44 übersprungen, 6
  fehlgeschlagen).
- **MESS-08:** Indexgröße de,en 786.508.818 Byte, sechs Felder 1.431.953.684
  Byte; Umbau-Wandzeit 581 s. Die Wandzeit ist die des dritten Anlaufs mit
  frisch verworfenem `index.rebuild`, gemessen ab Containerstart.
- **MESS-09:** 98d mit 0.
- **B1:** Abtaster je Containerleben, 16 Leben (`b1-cpu-*`, `b1-rss-*`).
- **B2:** gefahren. **B3:** gefahren (0). **B5:** Befund 50: Durchsatz in
  allen vier Kombinationen gelesen, der RAM-Abtaster lieferte 0 Abtastungen
  (`b5-max-anon ... unlesbar`). **B4:** vorbereitet, folgt in 22-09.

### 6.7 B4 auf m7g.4xlarge (26.09.2026, Plan 22-09)

**Gefahren**, nach D-03 (`B4_GEPLANT=ja`, F4 = 3,955) und im Restdeckel:
Variante Stunden, 24 h minus 2,02 h m7g.large, der B4-Posten mit 1,44 h passt.
`00-typwechsel.sh hin` stellte den Typ ohne Rückfall auf m7g.4xlarge
(`typ-ist m7g.4xlarge`, 13:20:59Z). `DECKEL_REST_MINUTEN` stand auf 84, das
sind 86 Minuten ab dem Start abzüglich der schon verstrichenen, und
`00-lauf.sh b4` setzte den Timer auf 14:45:42Z und las ihn zurück. Das liegt
vor dem Deckelende 14:46:56Z. Neun Container wurden angehalten, der
Wegwerf-Block lief ohne laufenden Container mit 16 Kernen und ohne
`mem`-Grenze (`b4-grenze keine`, nicht gekürzt). `00-wegwerf.sh b4` endete mit
**0** (`B4-FERTIG` 13:34:39Z). Nach der Abholung hat sich die Box selbst
abgeschaltet. `00-typwechsel.sh zurueck` stellte den Typ auf m7g.large zurück
(`b4-laufzeit-s 1069`).

| N (W3, cpuset 0 bis N-1) | `pages_per_second_median` | T (embed.bench, batch 2, seq 512) | `tokens_per_second_p50` |
|---:|---:|---:|---:|
| 1 | 0,263 | 1 | 2.242,2 |
| 2 | 0,526 | 2 | 4.283,7 |
| 4 | 1,052 | 4 | 7.609,6 |
| 8 | 2,102 | 8 | 13.484,8 |
| 12 | 3,150 | | |
| 16 | 4,172 | | |

Rohdaten: `b4-slots-{1,2,4,8,12,16}.txt`, `b4-bench-{1,2,4,8}.txt` und
`00-wegwerf-b4.txt`. Ausgewertet wird in 22-10/22-11.

### 6.8 Kosten und Deckel

Die Rechnung steht in `rohdaten/93-kosten-und-verbleib.txt`. Der B4-Anteil ist
von Hand aus den Stempeln gerechnet und nicht aus
`BOX_LAST_UPTIME_COST_USD` (Pitfall 9).

| Posten | Stunden | USD netto |
|---|---:|---:|
| m7g.large, sechs Uptimes | 2,02 | 0,2340 |
| B4 auf m7g.4xlarge, 1.069 s | 0,30 | 0,2376 |
| **laufend gesamt** | **2,32** | **0,4716** |
| Platten bei gestoppter Box, 6,37 h (obere Schranke, außerhalb des Deckels) | | 0,0831 |
| **mit Stillstand** | | **0,5547** |

**Deckel D-01, Variante Stunden, 24 h / 3,76 USD: gehalten**, 21,68 h und
3,29 USD darunter. Der B4-Posten (86 min / 1,147 USD) ist mit 17,8 min
gehalten. Der Rechenwert des Plans, 15,95 h / 2,83 USD, ist deutlich
unterschritten. Der Umbau dauerte 581 s statt der geplanten 3 h, und die
Wartezeit an den Tor-Abbrüchen lag bei gestoppter Box.

**Abbau** (`rohdaten/07-abbau.txt`): 13:41:10Z, `aws_box.sh destroy` mit 0,
ohne Ende-Snapshot. Instanz, Datenvolume, Security Group und Schlüsselpaar
sind gegen die API als gelöscht zurückgelesen (`InvalidKeyPair.NotFound`). Der
Tag-Sweep ist sauber, und der A-Record ist entfernt. Über 17 Regionen stehen 0
Instanzen, 0 Volumes, 0 Adressen und 0 Schlüsselpaare. Es bleibt allein der
Korpus-Snapshot (`purpose=findling-corpus-keep`, 2,79 bis 2,99 USD im Monat),
Wiedervorlage beim Milestone-Close.

### 6.9 Luecken

Kein Deckel ist gerissen, kein Block fiel durch einen harten Stopp aus, und
kein Block wurde gestrichen. Drei Zahlen fehlen trotzdem, weil ihr Werkzeug
einen Befund statt einer Zahl geliefert hat (6.6):

| Fehlende Messung | Anforderung | Stand | Nachmessung, Planwert |
|---|---|---|---|
| Kaltstartlatenz mit Trefferpflicht der ersten Suche, damit auch die M-01-Gegenprobe im Kaltstart-Fenster | **MESS-07, Pflichtzahl** (Erfolgskriterium 2) | 95c zweimal 48, kalt 0 Treffer, warm 26; die Ursache ist offen | Aufbau 1 h 30 min und Kaltstart 20 min, mal 1,15 gleich 2,11 h, rund **0,24 USD** |
| `abtastreihe-spitze-mb` des Bodensatzes | MESS-07, Nebenzahl (`zyklus2-minus-c1 30.5` liegt vor) | 94c Befund 32, Leser unlesbar | Aufbau und Bodensatz, 2,30 h, rund 0,27 USD |
| RAM je onnx-Kombination | B5 (BL-F04-Mitmessliste) | Befund 50, Durchsatz aller vier Kombinationen liegt vor, der Abtaster lieferte 0 Abtastungen | Aufbau und B5, 1,96 h, rund 0,23 USD |

Zusammen in einer Anfahrt: 2,91 h, rund 0,34 USD. Die Box ist abgebaut, jede
Nachmessung beginnt also mit dem Aufbau aus dem Korpus-Snapshot. Ohne geklärte
Ursache des leeren Kaltstarts würde eine Nachmessung von 95c voraussichtlich
wieder 0 Treffer liefern. Die Ursache gehört deshalb zuerst in die Auswertung
(22-10/22-11).

**Nachfreigabe durch den Owner noetig (D-02)** für die Pflichtzahl
Kaltstartlatenz mit Trefferpflicht. Die zwei übrigen Lücken sind keine
Pflichtzahlen. Über ihre Nachmessung entscheidet der Owner mit.

### 6.10 MESS-09, disjunction_max nach der Regel E10 (26.09.2026, Plan 22-10)

Quelle ist `rohdaten/98d-dismax-probe.txt`, gefahren 12:53:17Z bis 12:53:33Z
im Produktcontainer nach dem Umbau auf sechs Felder (`00-lauf.txt`:
`98d-rueckgabewert 0 fehlerzeilen 0`). 60 Anfragen: 10 feste Begriffe, 10
Sprachfälle, 40 Stichprobe; 33 einwortig, 22 mehrwortig, 5 Rückfall
(Operator, Phrase oder Feld, nur unter `summe` gemessen). Plan mit 8 Feldern,
Tiefe 100, je Anfrage und Form 5 Wiederholungen. Bezug jeder Rangzahl ist der
Altplan (`body_de`, `body_en`, Name, Titel).

| Kennzahl (Median über alle Anfragen) | `summe` | `dismax_t00` | `dismax_t01` | `altplan` |
|---|---:|---:|---:|---:|
| `rbo10_gegen_altplan` | **0,9531** | **0,8399** | **0,9633** | |
| davon einwortig | 0,9720 | 0,8745 | 0,9849 | |
| davon mehrwortig | 0,8805 | 0,8297 | 0,9040 | |
| `overlap10_gegen_altplan` | 1,0000 | 0,9000 | 1,0000 | |
| `rangverschiebung_gegen_altplan` | 4,0208 | 8,9213 | 3,4545 | |
| `latenz_ms` | **4,7667** | **4,2832** | **4,7697** | 3,8983 |

Die Treffermenge ist in allen 55 Nicht-Rückfall-Anfragen unter allen Formen
gleich (sonst hätte 98d mit 49 geendet; eigens nachgezählt, keine Abweichung).

**Die Regel, angewandt** (`skripte/00-ablauf.md`, Abschnitt 6, Frage 3):

| Bedingung | Schwelle | `dismax_t00` | `dismax_t01` |
|---|---|---|---|
| 1. RBO-Median mindestens 0,05 über `summe` | ≥ 1,0031 | 0,8399, **nein** (−0,1132) | 0,9633, **nein** (+0,0102) |
| 2. kein Sprachfall-Eigenrang schlechter | | ja | ja |
| 3. Latenz-Median höchstens 1,20 × `summe` | ≤ 5,7200 ms | 4,2832, ja (0,90) | 4,7697, ja (1,00) |

Zu Bedingung 2: Die Kennung der eigenen Datei stammt aus dem Bestand, wie ihn
die v1.2-Box vergeben hat (`../2026-09-v12-messung/rohdaten/05-sprachfaelle.txt`,
Zeilen `fall <n> ... traegt die Kennung`). Der Snapshot trägt dieselben 39
Dateien des Kontos `sprachfall` (`rohdaten/03-aufbau.txt`, Abschnitt
Sprachfall-Bestand). Zugeordnet sind damit alle acht Nicht-Rückfall-Fälle:
Mueller 52290, Belehrung 52293, Auszug 52294 und Erinnerung 52308 stehen unter
allen drei Formen auf Rang 1 (je ein Treffer); Genehmigung und bescheid
(52287), Frist (52288) und Vertrag (52289) stehen unter keiner Form in der
Spitze 10, also auch unter `summe` nicht. Die Fälle 5 und 7 (`"drei Monate"`,
`type:pdf bescheid`) sind Rückfall und zählen nach der Regel nicht. Unter
`dismax_t01` ist die Spitze 10 jedes Sprachfalls außerdem Kennung für Kennung
gleich der unter `summe`.

**Urteil E10: gehalten.** Die Probe hat jede Kennzahl geliefert, die
Treffermengen sind gleich, und der Entscheid folgt allein der Regel.
**Entscheid: Summe**, weil keiner der beiden tie-Werte Bedingung 1 erfüllt.
tie 0.1 liegt näher am Altplan als tie 0.0 (0,9633 gegen 0,8399); tie 0.0
verdrängt bei zehn Einwortanfragen die ganze Spitze 10 des Altplans
(Overlap 0,0). **Folge: verworfen.** Das ausgelieferte Verhalten bleibt,
`backend/src/findling/query/rewrite.py` ist unverändert.

Vermerkt, ohne am Urteil etwas zu ändern: Die Schwelle aus Bedingung 1 lag auf
diesen Daten bei 1,0031 und damit über dem Höchstwert 1 jedes RBO. Die Summe
steht dem Altplan schon so nah (0,9531), dass keine Form sie um 0,05 hätte
übertreffen können. Das ist eine Eigenschaft der vorab beschlossenen Regel und
kein Ermessen im Nachhinein; eine andere Regel wäre ein neuer Owner-Entscheid
vor einer neuen Messung. Vier der zehn festen Mehrwortbegriffe (`Vertrag
beenden`, `Widerspruch einlegen`, `Rechnung bezahlen`, `Termin absagen`)
haben in diesem Korpus unter jeder Form 0 Treffer und gehen mit RBO 1,0 in
alle drei Mediane gleich ein.

### 6.11 Nachtrag zu 6.9: die Ursache des leeren Kaltstarts (26.09.2026, Plan 22-10)

Die Ursache ist aus den Rohdaten geklärt, eine Nachmessung ist dafür nicht
nötig. Die erste kalte Suche endete in beiden 95c-Läufen am Deckel des
PHP-Aufrufs und nicht an einer leeren Treffermenge:

- `rohdaten/m01-langsame-aufrufe-kaltstart-lasttest.txt`: drei Aufrufe
  `/search innerMs 1505.7`, `1505.6` und `1505.1` gegen `ceilingMs 1500.0`,
  um 12:42:03Z, 12:42:10Z und 12:42:17Z, also je einer pro Kaltzyklus aus
  `rohdaten/95c-kaltstart-lasttest.txt`. Der erste Lauf unter `admin` zeigt
  dasselbe Bild (`rohdaten/m01-langsame-aufrufe.txt`, Stufe `kaltstart`:
  `innerMs 1513.3`, `1596.3` und `1563.3`).
- Die gemessenen 1.828 bis 2.109 ms der Nutzerroute sind dieser Deckel
  (`ExAppService::REQUEST_TIMEOUT_SECONDS`, 1,5 s) plus der Aufwand der Route
  (0,33 bis 0,55 s, darin der Basic-Auth-Anteil von rund 0,32 s, Befund M-03). Nextcloud antwortet danach mit HTTP 200
  und einer Gruppe ohne Containerhälfte.
- Der Begriff `Bescheid Antrag` hat zwei Wörter, die Runde ist also hybrid, und
  der Entladeschalter stand in beiden Läufen auf 0 (`entladeschalter-ist 0`).
  Bei 0 erlaubt `findling.embed.engine.query_may_load` der ersten Suche, die
  Modellgewichte selbst zu laden. Das Laden dauert länger als 1,5 s. Es ist
  genau der Vorfall vom 10.09.2026 (1.838,4 ms gegen denselben Deckel, Docstring
  von `query_may_load`, `../2026-09-vergleichsmessung-m7g/` Abschnitte 9.2 und
  19.4). Dort ist der allgemeine Fall ohne Schalter bewusst als Backlog-Punkt
  zurückgestellt.
- Warm lieferte derselbe Begriff unter `lasttest` 26 Treffer
  (`rohdaten/zusatz-korpus-und-kaltstart.txt`). Unter `admin` waren es 0, weil
  das Konto nur 64 eigene Dateien hat. Der Wechsel auf das Suchkonto
  `lasttest` räumte also einen echten Grund aus, aber nicht den
  entscheidenden.

**Folge für die Nachfreigabe (D-02).** Eine Nachmessung von 95c mit
unverändertem Aufbau (Schalter 0, zweiwortiger Begriff) liefert wieder 0
Treffer, und zwar deterministisch. Einen gültigen Kaltstart mit Trefferpflicht
gibt es nur auf einem von drei Wegen, und jeder ist ein Owner-Entscheid:
(a) Messung mit eingeschaltetem Entladeschalter, dann antwortet die erste Suche
lexikalisch und lädt im Hintergrund nach; (b) ein einwortiger Begriff, der
lexikalisch bleibt; (c) vorher der zurückgestellte Produktfix für den
allgemeinen Fall. Ohne diese Wahl ist die rund 0,24 USD teure Nachmessung
nicht sinnvoll. Der Befund ist ein bekanntes Produktverhalten und keine neue
Fehlerklasse: Nach jedem Neustart mit Schalter 0 zeigt die erste
Mehrwortsuche in der Unified Search keine Findling-Treffer.

### 6.12 Urteile E1 bis E14 (26.09.2026, Plan 22-11)

Die Erwartungen stehen unverändert in `skripte/00-ablauf.md`, Abschnitt 3;
E2 und E3 dort mit der Neufassung vom Checkpoint 22-08, über deren erste
Fassung das Urteil in derselben Datei bereits festgeschrieben ist. Hier steht
je Erwartung genau ein Urteil und sein Beleg. Die Zahlen stammen aus den
Rohdateien in `rohdaten/`; ihre Auswertung steht in 6.13.

| Erwartung | Urteil | Beleg |
|---|---|---|
| E1, Marken | gehalten | `90e-marken.txt` und `90e-marken-ab-pii.txt`: Rückgabe 0, `marken-urteil umbau`; nur die drei Umbau-Marken weichen ab |
| E2, Bestandstor (Neufassung 52.137 / 44 / 6) | gehalten | 92d mit 0 in Fahrt 2 und von Hand vor ab-pii 2 (`ab-pii-92d/`), Bestandstor jeweils bestanden; die erste Fassung ist am Tor 41 der Fahrt 1 gescheitert (6.1) |
| E3, Einzelliste (Neufassung 44 / 6) | gehalten | `90e-einzelliste.json`: Zählung 52.137 / 44 / 6, 50 Einträge mit Kennung, Endung, Größe und Grundcode, keine Pfade |
| E4, M-01 | verfehlt | `m01-langsame-aufrufe.txt`: Stufe 1 hat 10 Zeilen, 9 davon über `ceilingMs` 1.500 (Maximum 1.512,5); die Stufe lief 5 s nach einem Containerstart und hat das Modell geladen (6.13). Stufen 4 und 8 ohne Zeile, 12 mit Maximum 1.021,7, 16 mit Maximum 1.080,6 |
| E5, Kaltstart | verfehlt | `95c-kaltstart.txt`, `95c-kaltstart-lasttest.txt`: in beiden Läufen je drei Kaltzyklen mit 0 Treffern (2.028, 2.109, 2.084 ms und 1.832, 1.828, 1.892 ms), Ursache in 6.11; die Gegenprobe fand je drei Zeilen im Kaltstart-Fenster |
| E6, Bodensatz | gehalten | `94c-bodensatz-zyklen.txt`: `zyklus2-minus-c1 30.5` MB gegen höchstens 50 MB |
| E7, 99d | gehalten | `00-lauf.txt`: `99d-umgebung FINDLING_LOAD_PASSWORD ungesetzt`, `99d-wiederholung-rueckgabewert 0`; der Lauf der Fahrt 2 endete mit 34 bei Arbeitsvorrat 2 und hat nichts gemessen |
| E8, Indexfaktor | verfehlt | `indexgroesse-de-en.txt` 786.508.818 Byte, `indexgroesse-sechs-felder.txt` 1.431.953.684 Byte, Faktor 1,82 unter dem Band 2,0 bis 3,0 |
| E9, Umbau-Wandzeit | gehalten | `00-lauf.txt`: `umbau-wandzeit-s 581`, also 9 min 41 s gegen höchstens 3 h |
| E10, dismax | gehalten | 6.10: alle Kennzahlen geliefert, Treffermengen gleich, Entscheid Summe nach der Regel |
| E11, 92c | gehalten | `00-lauf.txt`: `92c-fehlschlag-rueckgabewert 36 erwartet 36`, `92c-regulaer-rueckgabewert 0 erwartet 0`; `92c-wechsel-fehlschlag.txt`: `registrierung-gelungen nein` |
| E12, B6 | gehalten | `b1-cpu-15-umbau.csv` im Umbaufenster 12:43:05Z bis 12:52:46Z: 1,025 Kerne im Mittel, höchstens 1,251 |
| E13, B3 | gehalten | `b3-slots-1.txt` 0,264, `b3-slots-2.txt` 0,519 Seiten je Sekunde, Faktor 1,97 gegen mindestens 1,05 |
| E14, B2 | gehalten | `b2-ocr-charge.txt`: 280 Seiten in 1.146 s ab Upload-Ende, 4,09 s je Seite gegen rund 4,3 s vom 07.09.2026; E14 nennt kein Band, der Wert liegt 5 Prozent darunter |

**Zählung:** elf gehalten, drei verfehlt (E4, E5, E8), keine ohne Urteil. Eine
verfehlte Erwartung ist ein Ergebnis und kein Grund für eine zweite Anfahrt
(`skripte/00-ablauf.md`, Abschnitt 3).

**Nachtrag zu Abschnitt 2 (W4, Einzelmodus).** Der Satz dort, der
tesseract-Satz in `docs/performance.md` halte, gilt für den CI-Runner mit
4 Kernen und ohne Grenze. Auf der Box (B3 single, 6.13) ist ungesetzt
langsamer als `OMP_THREAD_LIMIT=1`, und das Produkt setzt die Grenze immer.
Die Berichtigung steht als datierter Nachtrag in `docs/performance.md`.

### 6.13 Auswertung der Rohdaten (26.09.2026, Plan 22-11)

Megabyte sind dezimal (10^6 Byte), wo nicht MiB steht. Ausnahme ist der
Bodensatz: 94c schreibt wie 94b der v1.2 „MB“ für 2^20 Byte, und die Werte
stehen hier so, wie das Werkzeug sie schreibt, damit sie mit v1.2
vergleichbar bleiben. Uhrzeiten UTC.

**M-01, innerer Aufruf je Stufe** (`m01-langsame-aufrufe.txt`, Stufen aus
`m01-stufe-*.json`, Loglevel 1 während der Reihe, danach zurück auf 2):

| Stufe | Aufrufe ab 1.000 ms | davon über 1.500 ms | Maximum `innerMs` | p95 Nutzerroute | Ergebnisgruppen ohne Containerteil (davon Fehlschlag) |
|---:|---:|---:|---:|---:|---|
| 1 | 10 | 9 | 1.512,5 | 2.145,7 ms | 8 (3) |
| 4 | 0 | 0 | keins | 1.366,3 ms | 4 (0) |
| 8 | 0 | 0 | keins | 1.953,5 ms | 9 (0) |
| 12 | 1 | 0 | 1.021,7 | 2.845,4 ms | 15 (1) |
| 16 | 3 | 0 | 1.080,6 | 3.813,1 ms | 20 (0) |
| Kaltstart `admin` | 3 | 3 | 1.596,3 | | |
| Kaltstart `lasttest` | 3 | 3 | 1.505,7 | | |

Stufe 1 begann 5 s nach dem Containerstart aus 92d (`abtaster leben 2`,
05:38:58Z). Die cgroup-Größe `anon` stieg während der Stufe von 116,9 MB auf
552,7 MB (`m01-stufe-1.json`, `memory.before` und `after`): die Stufe hat das
Modell geladen und ist damit eine Kaltmessung mit demselben Befund wie 6.11.
Dass die Nullen der Stufen 4 und 8 echte Nullen sind, belegt der Leser selbst:
in derselben Reihe hat er in Stufe 1, 12, 16 und in beiden Kaltstart-Fenstern
Zeilen gefunden, `kaputte-zeilen 0` in jeder Stufe. Die Spalte
„ohne Containerteil“ zählt die fünf Begriffe ohne Treffer im Korpus mit.

**92c und 99d** (`00-lauf.txt`, `92c-wechsel-fehlschlag.txt`,
`92c-wechsel.txt`, `99d-filter-sortierung-wiederholung.txt`): 92c mit einem
Daemon, den es nicht gibt, 36 und `registrierung-gelungen nein`; regulär 0,
`registrierung-gelungen ja`, Grenze `2147483648/0`, danach `93-nullstand.sh`
mit 0. 99d ohne `FINDLING_LOAD_PASSWORD` in der Umgebung mit 0, Passwort aus
der Datei, Sitzung `lasttest`: relevance Median 327,6 ms, newest 167,6 ms,
oldest 166,6 ms, Blättern 358,0 / 331,5 / 323,8 ms bei je 25 Treffern und
ohne doppelte Kennung.

**Bodensatz** (`94c-bodensatz-zyklen.txt`, Entladefrist 120 s, 12 Dateien je
Zyklus): Marke A 107,9 MB (`cold`), C1 730,2 MB, C2 760,8 MB (je `unloaded`);
`zyklus1-minus-a` 622,3, `zyklus2-minus-a` 652,8, `zyklus2-minus-c1` 30,5 MB.
Die v1.2 hatte A 103,9, C 731,9 und 628,0 MB Bodensatz. Die zweite Entladung
senkt den Bodensatz nicht, und ein zweiter Zyklus legt nur 30,5 MB dazu.

**Einzelliste** (`90e-einzelliste.json`, P0 der Fahrt 2, gelesen aus
`state.db` ohne Reindex): 44 übersprungen, 6 fehlgeschlagen, je einzeln in
`docs/performance.md`. Nach Grund: 22 `too_large` (21 CSV zu rund 56 MB, eine
DOCX mit 66.154 Byte), 16 `empty_text` (14 JPG, 2 PDF), 4
`image_not_ocrable` (PNG), 2 `encrypted` (PDF); fehlgeschlagen 5 `corrupt`
und 1 `empty_file` (je PDF). Die 14 JPG sind zwei Siebenergruppen mit
paarweise gleicher Größe (Kennungen 52 bis 60 und 50186 bis 50194).

**MESS-08** (`indexgroesse-*.txt`, `umbau-platz.txt`, `umbau-status.jsonl`,
`00-lauf.txt`): de,en 786.508.818 Byte, sechs Felder 1.431.953.684 Byte,
Faktor 1,821. Auf der Platte lagen während des Umbaus beide Verzeichnisse
nebeneinander; die letzte Platzlesung davor (12:52:15Z) zeigt
787.051.223 + 1.348.713.655 = 2.135.764.878 Byte, die obere Schranke kurz vor
dem Tausch ist 787.051.223 + 1.431.953.684 = 2.219.004.907 Byte. Wandzeit 581 s
ab Containerstart für 52.137 Dokumente, rund 90 Dokumente je Sekunde;
gegen 19 h 20 min (69.600 s) des v1.2-Vollreindex rund 120-mal kürzer.
`embedded` stand durchgehend auf 52.137.

**B1, Kernbelegung je Phase** (`b1-cpu-*.csv`, Delta `usage_usec` durch
Wandzeit; Box aus `/proc/stat`, 2 Kerne, an den Blockstempeln aus
`00-lauf.txt` und den Rohdateien):

| Phase | Fenster | Container, Mittel | Container, höchstens | Box belegt |
|---|---|---:|---:|---:|
| M-01, alle Stufen | 05:39:02Z bis 05:42:24Z | 0,196 | 0,530 | 1,040 |
| M-01, Stufe 16 | 05:41:47Z bis 05:42:24Z | 0,372 | 0,530 | 1,869 |
| Bodensatz, Zyklus 1 | 05:43:24Z bis 05:43:39Z | 0,389 | 0,504 | 1,043 |
| Bodensatz, Zyklus 2 | 05:46:34Z bis 05:47:37Z | 0,051 | 0,431 | 0,130 |
| B2, OCR bis Vorrat 0 | 05:50:26Z bis 06:12:18Z | 0,901 | 1,175 | 1,151 |
| Umbau MESS-08 | 12:43:05Z bis 12:52:46Z | 1,025 | 1,251 | 1,125 |
| 98d | 12:53:17Z bis 12:53:33Z | 0,802 | 0,936 | 1,043 |
| B3 (Wegwerf-Container) | 12:53:33Z bis 12:58:16Z | 0,001 | 0,004 | 1,501 |
| B5 (Wegwerf-Container) | 12:58:16Z bis 12:59:57Z | 0,001 | 0,001 | 1,348 |

Die Zusammenfassung von `b1-cpu-2-92d.csv` (`mean_cores=0.000`) ist nicht
verwendbar, weil 95c den Container im selben Leben neu gestartet hat und der
Zähler dabei zurückfiel; das M-01-Fenster liegt davor und ist sauber.

**B2** (`b2-ocr-charge.txt`, `b2-anon.csv`): 140 Scans, 280 Seiten, Upload
05:51:32Z bis 05:52:57Z, erste Abnahme des Vorrats zwischen den Lesungen
05:54:46Z und 05:55:01Z, erste Lesung mit Vorrat 0 um 06:12:03Z. Ab
Upload-Ende 1.146 s, 4,09 s je Seite und 8,19 s je Datei; ab 05:54:46Z
1.037 s, 3,70 s je Seite. r, die Kernbelegung außerhalb des
Containers während der OCR, ist 1,151 minus 0,901 = 0,25 Kerne. Speicher je
Prozess (`RssAnon`, Abtastung 1 s): Hauptprozess höchstens 1.257,5 MiB
(`VmHWM` 1.336,0 MiB) bei Entladeschalter 0, drei Sandbox-Kinder höchstens
136,4 MiB (`VmHWM` 161,2), 280 tesseract-Aufrufe höchstens 98,8 MiB (`VmHWM`
114,2), die Summe je Abtastung höchstens 1.435,8 MiB um 06:03:38Z.

**B3** (`b3-slots-*.txt`, `b3-single.txt`, Wegwerf-Container,
`--cpuset-cpus 0,1`, 2 GiB): N 1 0,264 und N 2 0,519 Seiten je Sekunde,
Faktor 1,97; CPU-Zeit je Runde 30,3 s bei N 1 und 60,6 s bei N 2, also ein
Kern je Slot. `anon_bytes_delta` je Runde bei N 2 höchstens 0,41 MB: das ist
der bleibende Zuwachs, keine Spitze je Slot. Einzelmodus:
`OMP_THREAD_LIMIT=1` 3,753 s Wand bei 3,75 s CPU, ungesetzt 6,382 s Wand bei
8,96 s CPU. Ohne Grenze belegt tesseract im Mittel 1,40 Kerne und braucht
1,70-mal so lange.

**B4** (6.7, m7g.4xlarge, 16 Kerne, ohne Speichergrenze): Faktoren gegen N 1
bei N 2, 4, 8, 12, 16: 2,00, 4,00, 7,99, 11,98, 15,86. Einbettung gegen T 1
bei T 2, 4, 8: 1,91, 3,39, 6,01. `anon_bytes_delta` bei N 16 höchstens
3,26 MB je Runde.

**B5** (`b5-threads-*-batch-*.txt`, m7g.large, `--cpuset-cpus 0,1`, Sequenz
512, p50): threads 1 batch 2 1.844,8, threads 1 batch 8 1.821,4, threads 2
batch 2 3.450,4, threads 2 batch 8 3.416,2 Tokens je Sekunde. Der zweite
Thread bringt Faktor 1,87, Batch 8 bringt nichts (minus 1,0 bis 1,3 Prozent).
Der Speicher je Kombination fehlt (6.9).

**B6:** einkernig ja, 1,025 Kerne im Umbau (Tabelle B1). Der Umbau dauert aber
9 min 41 s und nicht über eine Stunde; Tantivy `num_threads` bleibt als
v1.4-Hebel benannt, sein Gewinn ist auf diesem Bestand höchstens einige
Minuten.

**B7:** im CI, Abschnitt 2: 22,99 MB.

### 6.14 Gefahrene Fassungen und ihre Pruefsummen (26.09.2026, Plan 22-11)

Gefahren am **26.09.2026** auf der Box dieser Anfahrt: `92c-wechsel.sh` und
`99d-filter-sortierung.sh` aus `docs/measurements/2026-09-nachfolgefassungen/`
(92c Fehlschlag und regulär 13:00:06Z bis 13:06:25Z; 99d um 05:50:26Z und in
der Wiederholung 12:42:21Z bis 12:43:04Z) und alle Werkzeuge dieses
Verzeichnisses: `00-lauf.sh`, `00-abholen.sh`, `00-typwechsel.sh`,
`00-wegwerf.sh` (b3, b5, b4), `90e-einzelliste.py`, `91m-langsame-aufrufe.py`,
`92d-wechsel.sh`, `92e-umgebung.sh`, `94c-bodensatz-zyklen.sh`,
`95c-kaltstart.sh` und `98d-dismax-probe.py`. Gestrichen ist keines
(`00-gestrichen.txt` gibt es nicht).

Die Prüfsumme gilt der zuletzt gefahrenen Fassung, also dem Stand, mit dem
ab-pii 3 und B4 liefen (`00-lauf.sh` aus 65f8399, `92e-umgebung.sh` aus
be35cfe, `95c-kaltstart.sh` aus aecca7d, `92d-wechsel.sh` und
`90e-einzelliste.py` aus 26e5e8f). Die früheren Fahrten liefen mit älteren
Fassungen derselben Werkzeuge; welche Änderung wann kam, steht in 6.1 bis 6.5.
Der Kopfsatz „DIESE FASSUNG IST NICHT GEFAHREN“ bleibt in jeder dieser Dateien
byteweise stehen, wie bei 92c vorgesehen (`skripte/00-ablauf.md`, Abschnitt 5);
er beschreibt den Stand beim Schreiben. Die Prüfsummen stehen in
`backend/tests/test_v13_gefahren.py` (`DRIVEN_V13_FASSUNGEN`) und für 92c und
99d in `backend/tests/test_measurement_scripts.py`
(`DRIVEN_SUCCESSOR_FASSUNGEN`).
