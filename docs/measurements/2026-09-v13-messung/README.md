# Die v1.3-Messanfahrt (Phase 22)

Diese Anfahrt liefert den Messbeleg von BL-F03 und der v1.3: das Bündel aus
MESS-07 (M-01 auf Zielhardware, Wirkungsnachmessung 92c und 99d, Bodensatz im
zweiten Zyklus, die übersprungenen und fehlgeschlagenen Dateien einzeln,
Kaltstartlatenz mit Treffern), MESS-08 (Indexgröße bei sechs Sprachfeldern und
Wandzeit des Umbaus) und MESS-09 (der disjunction_max-Entscheid), dazu die
BL-F04-Mitmessliste B1 bis B6. Der Ablauf und die vorher aufgeschriebene
Erwartung stehen in `skripte/00-ablauf.md`, die Rohdaten in `rohdaten/`.

Anfahrt freigegeben: offen (Owner-Checkpoint 22-07)

Die Freigabe erteilt der Owner am Checkpoint 22-07, zusammen mit den Antworten
auf die drei Fragen in `skripte/00-ablauf.md`, Abschnitt 6. Vor dieser Zeile
läuft keine Boxminute.

**Zur Schreibweise.** Die Abschnittsüberschriften stehen ohne Umlaute, weil
Prüfungen und Verweise auf sie zeigen. Der Fließtext benutzt echte Umlaute.
Adressen, Kennungen und Passwörter der Box stehen in keiner Zeile dieser Datei.

---

## 1. Rechenblatt

Offen. Wird vor dem Checkpoint 22-07 gefüllt: Planwerte je Block aus
`skripte/00-ablauf.md`, Abschnitt 2, der Deckel D-01 als eigene Zeile und B4
als eigener Deckelposten.

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

Offen. Wird am Checkpoint 22-07 gefüllt: `DECKEL_MINUTEN`,
`DECKEL_REST_MINUTEN`, `B4_GEPLANT`, `EINZELWEG`, mit Herleitung aus dem
gewählten Deckel.

## 5. Offene Owner-Fragen

Offen. Die drei Fragen stehen in `skripte/00-ablauf.md`, Abschnitt 6.

## 6. Bericht

Offen. Wird nach der Anfahrt geschrieben: Urteil je Erwartung E1 bis E14,
gestrichene Blöcke und Lücken, Kosten gegen den Deckel.
