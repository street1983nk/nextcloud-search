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

Offen. Wird nach dem CI-Lauf des Jobs `slots` gefüllt: F4 nach der Definition
in `skripte/00-ablauf.md`, Abschnitt 8, und die Folge für B4 nach D-03.

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
| `92d` | lokaler Digest, Daemon der Probe | 41 nach `occ upgrade` und Registrierung | **37** in Phase A: die Zählung meldet 3 Nextcloud-Instanzen am Docker-Dienst; Phase A lief ganz (Digest gleich, Baumhash dreifach, `baumhash-beweis ja`) | **offen**: Phase B (`occ upgrade`, unregister ohne `--rm-data`, Registrierung, Bestandstor) ist nicht geprobt. Das Tor 37 hat richtig gehalten; es mit einer anderen Zählung zu umgehen hätte die Nachbarinstanzen getroffen |
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

- **92d Phase B.** `occ upgrade`, das unregister ohne `--rm-data`, die
  Registrierung über HaRP und das Bestandstor sind vor der Anfahrt nicht
  gelaufen. Ein Ort, an dem das ohne Nachbarinstanzen ginge, wäre ein eigener
  CI-Lauf nach dem Muster von `deploy-harp.yml`.
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
