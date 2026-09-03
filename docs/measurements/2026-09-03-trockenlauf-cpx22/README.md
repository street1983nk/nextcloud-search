# Rohdaten des Trockenlaufs, 500 Dateien, Generalprobe cpx22

Diese Dateien sind die Messreihen hinter dem Abschnitt "Der Trockenlauf" in
`docs/performance.md`. Sie liegen hier, weil die Maschine, auf der sie
entstanden sind, in Plan 05-14 gelöscht wird, und eine Zahl ohne ihre Messreihe
eine Behauptung ist.

## Umgebung

| Angabe | Wert |
|---|---|
| Maschine | Hetzner cpx22, x86_64, 2 vCPU, 4 GB, hel1 |
| Nextcloud | 33.0.8.2, All-in-One, PostgreSQL 18.6 |
| Container der ExApp | `nc_app_findling_backend` |
| Abbild in Lauf 1 | `ghcr.io/street1983nk/findling_backend:5c82598a4b793e77834b494861ddbf13d4671f22`, Index-Digest `sha256:bb8f17e7d18df86b410308ee06bb2a6935dbbd183f0c6fcd032ab1ef17234544` |
| Abbild in Lauf 2 | auf der Box gebaut aus dem Stand von Commit `f44ff25`, Kennzeichen `05-12-fix` in einer lokalen Registry |
| Datum | 2026-09-03 |

**Diese Zahlen gelten nicht für ARM.** Sie stammen von einer x86-Maschine. Der
ARM-Lauf wiederholt alles und erbt keine einzige Zeile.

## Die Dateien

| Datei | Was darin steht |
|---|---|
| `dry-report.csv` | der Korpus selbst: 500 Zeilen mit Name, Bytezahl und SHA-256 je erzeugter Datei, geschrieben von `scripts/dev/build_load_corpus.py --seed phase5-dry --dry-run-files` |
| `dry-run.csv` | Lauf 1, Speicher des ExApp-Containers im Abstand von fünf Sekunden, 146 Messpunkte, mit der Abschlusszeile des Samplers |
| `dry-run-2.csv` | Lauf 2, derselbe Sampler über den Nachlauf mit dem korrigierten Abbild, 40 Messpunkte, ohne Abschlusszeile (der Sampler wurde beendet, bevor er sie schreiben konnte) |
| `sampler.log`, `sampler2.log` | die Kopfzeile je Sampler mit dem aufgelösten cgroup-Pfad, damit nachvollziehbar ist, welche cgroup gemessen wurde |

## Die Spalten der Messreihen

`timestamp,anon,file,slab,current,peak`, alle Speicherangaben in Byte, gelesen
aus `memory.stat` und `memory.peak` der cgroup des Containers. Warum `anon` und
nicht `memory.current` die Zahl des Berichts ist, steht im Methodenteil von
`docs/performance.md` und im Kopf von `scripts/ops/rss_sampler.sh`.

Jede Zeile trägt das Präfix `findling-rss`, damit sich die Messung aus einem
Protokoll herausfiltern lässt, das auch anderes enthält.

## Die Abschlusszeile von Lauf 1

```
findling-rss summary samples=146 max_anon=400003072 peak=476631040
  events=[low=0 high=0 max=0 oom=0 oom_kill=0 oom_group_kill=0] oom_killed=false
```

400.003.072 Byte sind 381 MB. Der Grenzwert des Berichts liegt bei 2,0 GB.

## Nachbauen

```sh
# Korpus, im Abbild der ExApp, weil dort Pillow in der gepinnten Fassung liegt
docker run --rm --user 0:0 --entrypoint python3 \
  -v <repo>/scripts:/w/scripts:ro -v <repo>/testdata:/w/testdata:ro \
  -v <ziel>:/out -v <log>:/log \
  ghcr.io/street1983nk/findling_backend:<tag> \
  /w/scripts/dev/build_load_corpus.py --seed phase5-dry --dry-run-files \
  --out /out --report /log/dry-report.csv

# Messung
scripts/ops/rss_sampler.sh nc_app_findling_backend 5 dry-run.csv
```
