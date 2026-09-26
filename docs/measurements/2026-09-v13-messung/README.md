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
