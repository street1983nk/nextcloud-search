# Rohdaten des ARM-Volllaufs, m7g.large

Die Messung, aus der `docs/performance.md` seine ARM-Zeilen zieht: der Volllauf
über 50.000 Dateien, der vierteilige OOM-Beweis, die drei Störfall-Drills und
die Zusatzmessung mit zwei Indexarbeitern. Sie liegt hier, weil die Maschine
gelöscht wird: eine Zahl im Bericht ohne die Reihe, aus der sie stammt, ist eine
Behauptung, und niemand kann sie nachrechnen, sobald die Box weg ist.

## Die Umgebung dieser Messung

| Angabe | Wert |
|---|---|
| Maschine | AWS m7g.large, 2 vCPU arm64 (Graviton), Arbeitsspeicher per `mem=4G` gedeckelt, 3958 MB nutzbar, kein Auslagerungsbereich |
| Ort | eu-central-1c, Frankfurt |
| Datenträger | 60-GB-Volume gp3, ext4, trägt Docker, containerd, das Nextcloud-Datenverzeichnis und den Korpus |
| Systemplatte | 40 GB gp3, so groß wie die der CAX11 |
| Kernel | 7.0.0-1012-aws, cgroup v2 |
| Nextcloud | All-in-One, Server 33.0.8, PostgreSQL, AppAPI 33.0.0, HaRP zugeschaltet |
| Findling | `localhost:5000/findling_backend:05-21-arm`, auf der Box gebaut |
| Codestand Container | Baumhash über `backend/src/findling`, auf LF vereinheitlicht: `ad79c9c6bfe6755aa3072ebe6e7c77f39c32caf1d57c1f97843e7405c290caa6` |
| Codestand PHP | Baumhash über `php`: `00ecbb3bb4d51ecd0a4f7777d930dd55f36c6d7881286598b1fa1006f5a5bb8b` |
| harte Speichergrenze | `docker update --memory=2g --memory-swap=2g`, `memory.max 2147483648` |
| Korpus | Seed `phase5-full`, 50.000 Dateien, 20.208.046.426 Byte, Listen-Prüfsumme `bcbef9b2cb067c2200df2a4a2e89408f690710983117d4e78328024046098a72` |
| Lauf | 2026-09-04T17:46:36Z bis 2026-09-05T06:35:23Z |

Der Baumhash ist die Angabe, die diesen Stand überlebt. Das Abbild wurde auf der
Messmaschine gebaut und existiert nur dort; der Hash dagegen lässt sich aus dem
Arbeitsbaum jederzeit nachrechnen, mit dem Verfahren, das im Bericht steht.

## Die Dateien

| Datei | Was drinsteht |
|---|---|
| `volllauf.csv` | die Speicherreihe des Samplers, 9.622 Messpunkte im Abstand von 5 s, plus die Abschlusszeile mit dem OOM-Beweis |
| `statusseite.jsonl` | 161 Aufnahmen der Verwaltungsseite im Abstand von 5 min, je eine vollständige Antwort ohne Namensträger |
| `11-korpus.log` | die Erzeugung des Korpus, mit Kategorien, Bytezahl, Prüfsumme und Dauer, dazu die Gegenprobe der Dateiendungen von der Platte |
| `13-volllauf.log` | der Anstoß des Laufs |
| `00-start.txt` | der Beginn, samt dem Nachtrag über den Fehlstart und seine Ursache (DI-05-36) |
| `00-ende.txt` | das Ende, wie der Wächter es erkannt hat |
| `07-oom-beweis.txt` | `memory.events`, `memory.peak`, `memory.stat` und `docker inspect`, erhoben nach dem Lauf und vor jedem Eingriff |
| `13b-wachter.log` | der Wächter, der den Lauf über Nacht beaufsichtigt hat |
| `99-ntfy-watch.log` | die Meldung an den Betreiber, als der Lauf fertig war |
| `22-drill1.txt` | Drill 1, `docker kill` mitten in der OCR-Arbeit |
| `25-neustart.txt` | Drill 1b, der Neustart der ganzen Maschine, mit dem Nachtrag, der das erste Urteil korrigiert |
| `23-drill2.txt` | Drill 2, das Backend ist weg |
| `24-drill3.txt` | Drill 3, die Platte wird knapp |
| `30-workers-abbild.log` | der Bau des Wegwerf-Abbilds mit `INDEX_WORKERS = 2`, samt Gegenprobe, dass sonst nichts anders ist |
| `31-workers-a.txt`, `31-workers-a.csv` | die Zusatzmessung mit einem Arbeiter, Protokoll und Speicherreihe |
| `31-workers-b.txt`, `31-workers-b.csv` | dieselbe Messung mit zwei Arbeitern |

## Die Spalten von `volllauf.csv`

Jede Zeile beginnt mit dem festen Präfix `findling-rss`, damit sich die Reihe aus
einem Protokoll herausfiltern lässt, das auch alles andere trägt. Danach folgen:

```
timestamp,anon,file,slab,current,peak
```

`anon` ist die Zahl, aus der die Store-Aussage kommt: der Speicher in anonymen
Abbildungen, also genau der Haufen, den ein Arbeiter, der Schreibpuffer und
tesseract erzeugen. `current` und `peak` zählen den Seitencache mit, und der Index
ist eine in den Speicher abgebildete Datei, also landet jeder gelesene Indexblock
in derselben cgroup. Beide werden trotzdem aufgezeichnet, weil der Docker-Client
eine Zahl auf Basis von `current` zeigt und der erste Leser, der sie danebenlegt,
den Unterschied erklärt finden soll statt versteckt.

Die letzte Zeile ist keine Messung, sondern die Abschlusszeile:

```
findling-rss summary samples=9421 max_anon=442695680 peak=1018101760
  events=[low=0 high=0 max=0 oom=0 oom_kill=0 oom_group_kill=0 sock_throttled=14865]
  oom_killed=false
```

Zwei Dinge daran gehören erklärt, damit niemand sie für Ungenauigkeit hält.

**`samples=9421`, aber 9.622 Messzeilen in der Datei.** Der Sampler ist um
17:29:42Z angelaufen, der Lauf hat erst um 17:46:36Z wirklich begonnen, und
dazwischen liegt der Fehlstart aus `00-start.txt`. Der Zähler der Abschlusszeile
gehört zum letzten Abschnitt des Samplers, die Datei trägt alle Zeilen. Für jede
Zahl dieses Berichts ist die Datei die Quelle und nicht der Zähler.

**`sock_throttled=14865`.** Dieser Zähler steht auf dem Kernel dieser Box neu in
`memory.events` und gehört nicht zu den sechs, die einen Speichertod anzeigen.
Er zählt, wie oft die Zuteilung von Puffern für Netzverbindungen innerhalb dieser
cgroup gebremst wurde. Die sechs Zähler, auf die es ankommt, stehen alle auf
null, `memory.max` wurde nie berührt, und der Lauf hat keine einzige Datei
verloren. Der Bericht nennt die Zahl trotzdem, weil ein weggelassener Zähler
schlimmer ist als ein erklärter.

## Die Felder von `statusseite.jsonl`

Aufgenommen wurde `GET /apps/findling/admin/overview` über eine angemeldete
Sitzung, also derselbe Weg, den die Verwaltungsseite selbst nimmt. Je Zeile eine
vollständige Antwort als JSON, mit dem Aufnahmezeitpunkt unter `at` davor.

Kein Feld dieser Reihe trägt einen Pfad oder einen Dateinamen. Der Beobachter
entfernt `examples`, `path`, `uid`, `exclusions` und `restartCommand` schon beim
Aufnehmen. Das ist der Privatheitsvertrag der Anwendung, und er gilt für ihre
Messdaten genauso: Zahlen ja, Namen nein.

## Was hier nicht liegt

Das Manifest der 50.000 erzeugten Dateien. Die Aussage, die es trägt, steht in
zwei kürzeren Formen im Bericht: die Listen-Prüfsumme oben, und die Verteilung
nach Kategorien, die dort gegen die Dateiendungen auf der Platte gegengeprüft
ist. Wer den Korpus nachbauen will, braucht den Seed und das Abbild, nicht die
Liste.

## Nachbauen

```sh
# Korpus, im Abbild der ExApp, weil die Pruefsumme an der Rasterung der Schrift haengt
docker run --rm --user 0:0 --entrypoint /app/.venv/bin/python \
  -v <repo>/scripts:/w/scripts:ro -v <repo>/testdata:/w/testdata:ro \
  -v <zielverzeichnis>:/out \
  <abbild> /w/scripts/dev/build_load_corpus.py --seed phase5-full --files 50000 --out /out

# harte Grenze, nach der letzten Registrierung und vor dem Start
docker update --memory=2g --memory-swap=2g nc_app_findling_backend

# Speicher messen, fuenf Sekunden Abstand
scripts/ops/rss_sampler.sh nc_app_findling_backend 5 volllauf.csv

# die Reihe verdichten
scripts/ops/rss_digest.py <verzeichnis mit den csv>
```
