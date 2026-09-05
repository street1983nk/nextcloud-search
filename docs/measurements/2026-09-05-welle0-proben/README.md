# Welle 0 der Phase 6: die zwei Fünf-Minuten-Proben A12 und A13

Zwei Annahmen aus dem Assumptions Log von `06-RESEARCH.md`, beantwortet **bevor**
ein Vektorschema entsteht. Beide sind hier billig und wären teuer, sobald eine
Tabelle steht: A13 entscheidet, ob das Abbild eine eigene Python-Übersetzung
braucht, und A12 entscheidet, ob die Leseseite ihr `PRAGMA query_only = 1`
behalten kann. Das eine ist eine Entscheidung über das Abbild, das andere eine
über die Leseseitenarchitektur, und keine von beiden ist eine Zeile Code.

Die Probe selbst liegt als `backend/tests/test_vec_extension_probe.py` im
Repository und läuft in zwei Formen: als Testdatei neben den übrigen Unittests
und als einfaches Skript im gebauten Abbild, weil pytest im Laufzeitabbild
bewusst nicht installiert ist.

## Die Fragen

| Kennung | Frage | Art |
|---|---|---|
| A13 | Erlaubt die CPython-Übersetzung im Abbild ladbare SQLite-Erweiterungen, und lädt die Datei unter `$FINDLING_VEC0_PATH` tatsächlich? | **Gatter.** Ohne sie ist die Phase nicht baubar |
| A12 | Läuft eine `vec0`-KNN-Abfrage unter `PRAGMA query_only = 1`? | **Messung.** Beide Ausgänge sind zulässig, der Ausgang steuert Plan 06-04 |

## Die Umgebung dieser Messung

| Angabe | Wert |
|---|---|
| Datum | 2026-09-05 |
| Maschine | x86_64, 13th Gen Intel Core i5-1335U, Docker Desktop 29.5.2 unter Windows |
| Abbild | aus `backend/Dockerfile` dieses Standes, gebaut mit `--build-context scripts=./scripts` |
| Kennung amd64 | `sha256:c9bb41d65746c584480ad05569445a2c36c6f347543f983d42416cedb02bfef9` |
| Kennung arm64 | `sha256:2be00e795164797a9f4ad655904b4c6182bf7286d9f49ad10d019298b842eeb5` |
| Netzwerk | in jedem Lauf abgeklemmt (`--network none`) |

Die Kennungen sind Abbild-Kennungen eines lokalen Baus, keine Registry-Digests:
diese Abbilder wurden nie veröffentlicht. Der Registry-Digest desselben Standes
entsteht im Lauf von `.github/workflows/docker.yml`, der denselben Probenschritt
auf beiden Architekturen gegen das veröffentlichte Manifest fährt.

**Ein Vorbehalt, der dazugehört:** die arm64-Zahlen unten stammen aus einem
emulierten Bau (`docker build --platform linux/arm64` unter QEMU auf derselben
x86-Maschine). Emuliert wird die Befehlssatzarchitektur, nicht die Software: es
sind die echten aarch64-Binärdateien von CPython, SQLite und `vec0.so`, die dort
laufen, und genau darauf zielen A12 und A13. Was ein emulierter Lauf **nicht**
belegt, ist Geschwindigkeit; darüber sagt dieses Dokument auch nichts.

## Die Kommandozeilen

```bash
# das Abbild, mit dem zusätzlichen Kontext, den die Modellstufe braucht
docker build --build-context scripts=./scripts -f backend/Dockerfile \
    -t findling-sem-probe:local backend
docker build --platform linux/arm64 --build-context scripts=./scripts \
    -f backend/Dockerfile -t findling-sem-probe:arm64 backend

# die Probe im Abbild, ohne Netzwerk, tests/ als Bind-Mount, weil
# backend/.dockerignore die Testdateien absichtlich aus dem Kontext hält
docker run --rm --network none \
    -v "$PWD/backend/tests:/probe:ro" \
    --entrypoint python findling-sem-probe:local /probe/test_vec_extension_probe.py

# die Gegenprobe: ein Pfad, der keine Erweiterung ist
docker run --rm --network none -e FINDLING_VEC0_PATH=/etc/hostname \
    -v "$PWD/backend/tests:/probe:ro" \
    --entrypoint python findling-sem-probe:local /probe/test_vec_extension_probe.py
```

## A13: ladbare SQLite-Erweiterungen im Abbild

**Antwort: ja, auf beiden Architekturen.**

Die Ausgabe des Laufs auf amd64, wörtlich:

```
python           3.13.15
platform         linux-x86_64
sqlite           3.46.1
vec0 path        /usr/local/lib/findling/vec0.so
A13 has api      True
A13 loaded       True
A13 vec_version  v0.1.9
A13 error        None
```

Auf arm64:

```
python           3.13.15
platform         linux-aarch64
sqlite           3.46.1
vec0 path        /usr/local/lib/findling/vec0.so
A13 has api      True
A13 loaded       True
A13 vec_version  v0.1.9
A13 error        None
```

Zwei Befunde stecken in dieser einen Frage, und sie werden getrennt gemeldet,
weil sie verschiedene Ursachen haben: `has api` sagt, ob die
CPython-Übersetzung mit `--enable-loadable-sqlite-extensions` gebaut wurde, und
`loaded` sagt, ob die Datei an `$FINDLING_VEC0_PATH` wirklich geladen werden
konnte. Beide sind wahr, und `vec_version` beweist, dass die geladene Datei die
sqlite-vec-Fassung ist, die `uv.lock` pinnt.

**Dass das Gatter rot werden kann, ist belegt und nicht behauptet.** Mit
`FINDLING_VEC0_PATH=/etc/hostname` antwortet dieselbe Probe im selben Abbild:

```
A13 has api      True
A13 loaded       False
A13 vec_version  None
A13 error        OperationalError: /etc/hostname.so: cannot open shared object file: No such file or directory
A12 not measured in this run
A13 is negative: the image cannot load sqlite-vec
```

und endet mit Exitcode 1.

**Konsequenz:** keine. Das Abbild bleibt, wie es ist; die eigene
Python-Übersetzung, die ein Nein erzwungen hätte, wird nicht gebraucht. Der
Befund gehört trotzdem als Gatter in `docker.yml`, weil die Eigenschaft an der
Basis-Abbild-Kennung hängt und mit ihr wandern kann.

## A12: `vec0`-KNN unter `PRAGMA query_only = 1`

**Antwort: ja, auf beiden Architekturen. Die Abfrage läuft.**

Der Ablauf der Probe ist derselbe, den die Leseseite später fährt: eine
`vec0`-Virtualtabelle mit `int8[384]` anlegen, 512 Vektoren schreiben, die
Verbindung schließen, die Datei erneut öffnen, die Erweiterung laden,
anschließend `PRAGMA query_only = 1` setzen wie in `store/repo.py::_connect`
und dann fünf Nachbarn erfragen.

Auf amd64:

```
A12 knn ran      True
A12 neighbours   5
A12 error class  None
A12 error        None
```

Auf arm64:

```
A12 knn ran      True
A12 neighbours   5
A12 error class  None
A12 error        None
```

Eine Zahl am Rande, die zu A12 nicht gehört und trotzdem hierher: die
quantisierte Datei wiegt auf beiden Architekturen **exakt** 118.101.091 Byte.
Die Quantisierung ist also reproduzierbar über die Architektur hinweg, und das
ist die Voraussetzung dafür, dass ein Suchergebnis auf der ARM-Box dasselbe ist
wie auf der x86-Maschine.

Die Reihenfolge im Ablauf ist keine Nebensache und ist die Vorlage für Plan
06-04: `load_extension` ist selbst eine Änderung am Verbindungszustand und muss
**vor** `query_only` passieren. Wer die Pragmas in der Reihenfolge von
`_connect` setzt und die Erweiterung danach laden will, bekommt ein Nein, das
wie ein Nein auf A12 aussieht und keines ist.

**Konsequenz für Plan 06-04:** die Leseseite behält `PRAGMA query_only = 1`. Der
Vektorspeicher wird auf derselben schreibgeschützten Verbindungsart gelesen wie
der Rest der Leseseite, und die strukturelle Hälfte des Lese-Schreib-Schnitts
bleibt unangetastet. Was `_connect` dagegen bekommen muss, ist der Ladevorgang
der Erweiterung für **beide** Verbindungsarten; heute ruft die Funktion
`enable_load_extension` an keiner Stelle (06-RESEARCH.md, Abschnitt 1.2).

## Ein dritter Befund, der nebenbei abfiel

`sqlite-vec` liest einen Blob nicht nach der Spaltendeklaration, sondern
verlangt die Typangabe an der Aufrufstelle. Ein 384-Byte-Blob, der ohne
Markierung in eine `int8[384]`-Spalte geschrieben wird, endet mit:

```
sqlite3.OperationalError: Inserted vector for the "embedding" column is
expected to be of type int8, but a float32 vector was provided.
```

Richtig ist `INSERT INTO chunk_vectors(rowid, embedding) VALUES (?, vec_int8(?))`
und ebenso `WHERE embedding MATCH vec_int8(?)`. Das steht hier, damit Plan 06-04
es nicht ein zweites Mal herausfindet.

## Was hier bewusst nicht gemessen wurde

Geschwindigkeit. Weder die Dauer einer KNN-Abfrage noch die eines
Einbettungsvorgangs, weder auf amd64 noch auf arm64. Beides gehört in die
Lasttests dieser Phase, auf echte Zielhardware und nicht auf eine Emulation, und
Erfolgskriterium 4 verlangt ausdrücklich, dass das Vektorschema erst danach
festgezurrt wird.

Ebenso wenig wurde hier belegt, dass der Container ohne Netzwerk eine
**semantische Suche** fahren kann. Dass die Erweiterung und das Modell mit
abgeklemmtem Netzwerk erreichbar sind, zeigen diese Läufe; der Beweis für die
Suche selbst ist der Offline-Test aus Plan 06-10.

## Die Rohdaten

Es gibt keine Datei neben dieser: die vollständige Ausgabe beider Läufe steht
oben, und der Lauf ist mit den Kommandozeilen dieses Dokuments in wenigen
Minuten wiederholbar. Der laufende Nachweis ist der Schritt
"Answer A12 and A13 inside this image" in `.github/workflows/docker.yml`, der
dieselbe Probe bei jedem Bau auf beiden Architekturen gegen das veröffentlichte
Abbild fährt.
