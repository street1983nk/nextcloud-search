# Rohdaten des Volllaufs, Generalprobe cpx22

Die Messung, aus der `docs/performance.md` seinen Abschnitt "Findling im Volllauf"
und seine drei Störfall-Drills zieht. Sie liegt hier, weil die Maschine gelöscht
wird: eine Zahl im Bericht ohne die Reihe, aus der sie stammt, ist eine
Behauptung, und niemand kann sie nachrechnen, sobald die Box weg ist.

## Die Umgebung dieser Messung

| Angabe | Wert |
|---|---|
| Maschine | Hetzner CPX22, 3 vCPU x86, 3814 MB nutzbarer Arbeitsspeicher, kein Auslagerungsbereich |
| Ort | Helsinki, `hel1` |
| Datenträger | 50-GB-Volume, trägt Docker, containerd, das Nextcloud-Datenverzeichnis und den Korpus |
| Nextcloud | All-in-One v13.6.0, Server 33.0.8, PostgreSQL |
| Findling | `localhost:5000/findling_backend:05-12-fix`, Kennung `sha256:00c457bf48a2c531a5bbd8ff0fa589dc861216e57c84746189aaefd9b2d4c19b` |
| Codestand | Baumhash über die 44 Python-Dateien des Pakets, auf LF vereinheitlicht: `f305ac09adeae37ede6e210311c32ef2cf2b5d9b7d870409d7b550785046954e` |
| harte Speichergrenze | `docker update --memory=2g --memory-swap=2g`, `memory.max 2147483648` |
| Korpus | Seed `phase5-full`, 50.000 Dateien, 20.208.046.426 Byte, Listen-Prüfsumme `c03a880323171d29c5278ed350db277291e39d256e95d5a8654dd4a6c244a274` |
| Lauf | 2026-09-03T23:13:11Z bis 2026-09-04T09:27:25Z |

Der Baumhash ist die Angabe, die diesen Stand überlebt. Das Abbild wurde auf der
Messmaschine gebaut und existiert nur dort; der Hash dagegen lässt sich aus dem
Arbeitsbaum jederzeit nachrechnen, mit dem Verfahren, das im Bericht steht.

## Die Dateien

| Datei | Was drinsteht |
|---|---|
| `volllauf.csv` | die Speicherreihe des Samplers, 7.782 Messpunkte im Abstand von 5 s, plus die Abschlusszeile mit dem OOM-Beweis |
| `statusseite.csv` | 130 Aufnahmen der Verwaltungsseite im Abstand von 5 min, verdichtet auf 21 Felder |
| `01-korpus.log` | die Erzeugung des Korpus, mit Kategorien, Bytezahl, Prüfsumme und Dauer |
| `06-start.log` | Neuregistrierung, das Setzen der harten Grenze, das Räumen der Zustandstabellen, der Anstoß |
| `07-oom-beweis.txt` | `memory.events`, `memory.peak`, `memory.stat` und `docker inspect`, erhoben nach dem Lauf und vor jedem Eingriff |
| `08-drill1.txt` | Drill 1, `docker kill` mitten im OCR-Lauf, samt Endabrechnung |
| `11-drill2.txt` | Drill 2, das Backend ist weg |
| `10-drill3.txt` | Drill 3, die Platte wird knapp |

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
findling-rss summary samples=7782 max_anon=449441792 peak=1004195840
  events=[low=0 high=0 max=0 oom=0 oom_kill=0 oom_group_kill=0] oom_killed=false
```

## Die Spalten von `statusseite.csv`

Aufgenommen wurde `GET /apps/findling/admin/overview` über eine angemeldete
Sitzung, also derselbe Weg, den die Verwaltungsseite selbst nimmt. Die Spalten
sind die Felder dieser Antwort, ohne Umbenennung: `at`, `runState`, `scheduled`,
`running`, `docs`, `aclRows`, `failed`, `skipped`, `gruende`, `indexBytes`,
`lowDisk`, `diskFreeBytes`, `coveragePercent`, `coverageIndexable`,
`mountsFinished`, `provisional`, `secondsLeft`, `ocrMeasured`, `lockstep`,
`backendReachable`.

Kein Feld dieser Reihe trägt einen Pfad oder einen Dateinamen. Das ist der
Privatheitsvertrag der Anwendung, und er gilt für ihre Messdaten genauso: Zahlen
ja, Namen nein.

## Was hier nicht liegt

Das Manifest der 50.000 erzeugten Dateien. Der Trockenlauf hat seines mitgeliefert,
weil es 500 Zeilen waren; für den Volllauf wären es 50.000, und die Aussage, die es
trägt, steht bereits in zwei kürzeren Formen im Bericht: die Listen-Prüfsumme oben,
und die Verteilung nach Kategorien, die dort gegen die Dateiendungen auf der Platte
gegengeprüft ist. Wer den Korpus nachbauen will, braucht den Seed und das Abbild,
nicht die Liste.

## Nachbauen

```sh
# Korpus, im Abbild der ExApp, weil die Prüfsumme an der Rasterung der Schrift hängt
docker run --rm --user 0:0 --entrypoint python3 \
  -v <repo>/scripts:/w/scripts:ro -v <repo>/testdata:/w/testdata:ro \
  -v <zielverzeichnis>:/out \
  <abbild> /w/scripts/dev/build_load_corpus.py --seed phase5-full --files 50000 --out /out

# harte Grenze, nach der letzten Registrierung und vor dem Start
docker update --memory=2g --memory-swap=2g nc_app_findling_backend

# Speicher messen, fuenf Sekunden Abstand
scripts/ops/rss_sampler.sh nc_app_findling_backend 5 volllauf.csv
```
