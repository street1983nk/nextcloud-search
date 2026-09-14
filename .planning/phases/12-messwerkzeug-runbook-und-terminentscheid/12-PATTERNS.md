# Phase 12: Messwerkzeug, Runbook und Terminentscheid - Pattern Map

**Mapped:** 2026-09-14
**Files analyzed:** 12 (6 neu, 6 geaendert)
**Analogs found:** 11 / 12

Diese Phase baut kein Produkt, sondern Werkzeug, Text und einen Entscheid. Fuer
fast jede Datei existiert in diesem Repositorium bereits ein Muster mit
ausgeschriebener Begruendung. Der Planer soll die Analogie zitieren, nicht ein
zweites Verfahren erfinden (siehe RESEARCH "Don't Hand-Roll").

---

## File Classification

| Neue/geaenderte Datei | Rolle | Datenfluss | Naechstes Analog | Match |
|---|---|---|---|---|
| `docs/measurements/2026-09-v12-messung/skripte/73-bestand-sonde.py` | probe/utility (In-Container) | batch, read-only in-process | `docs/measurements/2026-09-werkzeugfixe/skripte/72-fremdbestand.py` | role-match |
| `docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh` | test-harness/driver | request-response + batch, dreiwertiges Urteil | `docs/measurements/2026-09-werkzeugfixe/skripte/98b-sprachfaelle.sh` | exakt |
| `docs/measurements/2026-09-v12-messung/skripte/9x-cron-vorpruefung.sh` (Name frei) | guard/precondition, fail-closed | polling/event-driven | `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/93-nullstand.sh` | exakt (Konfigzweig) |
| ... Wirkungszweig desselben Skripts | observer | polling ueber Zeit | `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/96b-waechter.sh` | role-match |
| `docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md` | doc (Ablaufplan) | n/a | `docs/measurements/2026-09-werkzeugfixe/skripte/00-ablauf.md` | exakt |
| `docs/measurements/2026-09-v12-messung/README.md` (optional, traegt die Freigabezeile) | doc (Bericht) | n/a | `docs/measurements/2026-09-werkzeugfixe/README.md` | exakt |
| `docs/runbook-messbox.md` | doc (dauerhaftes Runbook) | n/a | `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/00-ablauf.md` (Tiefe) + `2026-09-werkzeugfixe/skripte/00-ablauf.md` (Groessenordnung/Form) | partial, siehe "No Analog Found" |
| `.planning/phases/12-.../12-STABLE35-ENTSCHEID.md` (Name frei) | doc (Entscheidungsnotiz) | n/a | `.planning/milestones/v1.1-phases/11-.../11-VORENTSCHEIDE.md` | role-match |
| `scripts/ops/aws_box.sh` (neuer Unterbefehl `restore`) | ops-tool/config | request-response gegen AWS-API | `cmd_volume` + `cmd_snapshot` in derselben Datei | exakt |
| `backend/tests/test_ops_scripts.py` (Usage-Gate 8 auf 9) | test | n/a | `test_the_aws_tool_names_its_eight_subcommands_in_the_usage:264-280` | exakt |
| `backend/tests/test_measurement_scripts.py` (`NARROW_SCOPE_DIRS`) | test | n/a | Zeilen 63-79, 785-795, 992-1004 derselben Datei | exakt |
| `.github/workflows/python.yml` (Pfadfilter `docs/measurements/**`) | config (CI) | n/a | Zeilen 5-25 derselben Datei (Begruendungsmuster `scripts/dev/build_corpus.py`) | exakt |
| `.github/workflows/deploy-harp.yml` (stable35-Flag und Kommentarkette) | config (CI) | n/a | Zeilen 211-273 derselben Datei | exakt |

---

## Pattern Assignments

### `docs/measurements/2026-09-v12-messung/skripte/73-bestand-sonde.py` (probe, in-process)

**Analog Struktur/Prosa:** `docs/measurements/2026-09-werkzeugfixe/skripte/72-fremdbestand.py`
**Analog Transport:** `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/94-grundlast.sh:102-113`

**Shebang und Docstring-Muster** (`72-fremdbestand.py:1-18`) - der Kopf erklaert
zuerst den Befund, dann was diese Datei misst, dann die Geheimnisregel:

```python
#!/usr/bin/env python3
"""Was die Vorpruefung des Fremdbestands auf dieser Instanz wirklich misst.

Der Lauf vom 10.09.2026 hat vier Faelle als ROT gemeldet, und DI-10-02 nennt
dafuer den Fremdbestand als Grund: ...

Das Passwort kommt aus der Umgebung und nie aus einem Argument (T-10-27).
"""
```

**Konstanten oben, keine Maschinenpfade** (`72-fremdbestand.py:26-32`):

```python
BASIS = "https://loadtest.infranode.dev"
ROUTE = "/ocs/v2.php/search/providers/findling/search"
KONTO = "lasttest"
BEGRIFFE_DER_FAELLE = ("Genehmigung", "Frist", "Vertrag", "bescheid")
TIEFEN = (5, 64, 200, 2000)
SCHWELLE = 64
```

**Ausgabeformat: eine Zeile je Begriff, ausgerichtet, maschinenlesbar**
(`72-fremdbestand.py:57-58`):

```python
zahlen = " ".join("tiefe%-5d treffer=%-4d" % (t, frage(auth, begriff, t)) for t in TIEFEN)
print("   %-14s %s" % (begriff, zahlen))
```

**Schlussabschnitt "was daraus folgt"** (`72-fremdbestand.py:65-72`): die Sonde
schreibt die Lesart der Zahlen selbst hin, damit der Bericht sie nicht erfinden
muss. Uebernehmen.

**Neu gegenueber dem Analog** (aus RESEARCH Befund 1.4/1.5, Code Example A): die
Sonde laeuft IM Container, nicht ueber den Draht. Kein `urllib`, kein Passwort,
keine Route. Drei Zahlen je Begriff: `bestand` aus
`searcher.search(query, 1, count=True).count`, `fenster_lexikalisch` /
`fenster_semantisch` aus `len(ranked_sides(...).lexical|.semantic)`, spaeter
`rang_eigene_datei`. `.count` ist im Typstub nicht deklariert; solange die Datei
unter `docs/measurements/**/skripte/` liegt, greift weder ruff noch pyright
(RESEARCH 6.3).

**Transportmuster des Fahrers** (`94-grundlast.sh:102-113`, woertlich uebernehmbar):

```sh
sudo docker cp "$GEWICHTE" "$CONTAINER:/tmp/49b-gewichte.py"
sudo docker exec "$CONTAINER" /app/.venv/bin/python /tmp/49b-gewichte.py
```

Containername als Variable mit Vorgabe (`94-grundlast.sh:49`):

```sh
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
```

---

### `docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh` (driver, request-response)

**Analog:** `docs/measurements/2026-09-werkzeugfixe/skripte/98b-sprachfaelle.sh` (664 Zeilen, exakt dieselbe Aufgabe)

**Kopf-Muster: die Nachfolge wird im Kopf begruendet** (`98b:1-13`). `98c` muss
genau dieselbe Konstruktion auf `98b` anwenden, weil `98b` am 10.09. gefahren
wurde und Rohdaten traegt:

```sh
#!/bin/sh
# The ten German language cases on the box, the successor fassung for DI-10-02.
#
# **Where the driven fassung lies, and that it stays where it lies.** The run of
# 10.09.2026 (plan 10-06) drove
# docs/measurements/2026-09-vergleichsmessung-m7g/skripte/98-sprachfaelle.sh.
# That file is part of the evidence of that run and stays byte identical: a
# measurement script that is edited afterwards makes every figure next to it
# unsupported.
```

**Exit-Code-Katalog im Kopf** (`98b:84-88`) - fortsetzen, nicht verschieben:

```sh
# The exit codes: 15 the upload did not deliver 39 files, 16 the work stock was
# still not empty at the round cap, 17 at least one MEASURABLE case was red, 18
# jq is not on this box, 19 the pre check of the foreign stock could not be
# driven, 22 CI_LAUF carries no run number, 23 not a single case was measurable.
set -eu
```

**Variablenkopf ohne Maschinenpfad** (`98b:93-130`):

```sh
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
KONTO="${KONTO:-sprachfall}"
LASTKONTO="${LASTKONTO:-lasttest}"
PWFILE="${PWFILE:-$HOME/work/.pw/lasttest}"
FREMD_SCHWELLE="${FREMD_SCHWELLE:-64}"
CI_LAUF="${CI_LAUF:-}"
```

**Pflichteingabe vor allem anderen, Exit 22** (`98b:145-155`) - unveraendert
uebernehmen:

```sh
case "$CI_LAUF" in
    '' | *[!0-9]*)
        echo "98b-sprachfaelle: CI_LAUF carries no run number of a green integration.yml run" >&2
        ...
        exit 22
        ;;
esac
```

**Arbeitsverzeichnis und leere Urteilsdateien** (`98b:167-177`):

```sh
WORK=$(mktemp -d)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT
: >"$WORK/fehler"
: >"$WORK/fehlertexte"
: >"$WORK/nichtmessbar"
mkdir -p "$WORK/fremd"
```

**Dreiwertiges Urteil, die drei Funktionen** (`98b:243-279`) - das Grundmuster
bleibt, nur die Messgroesse hinter `$WORK/fremd/$FALL` wechselt:

```sh
messbar() {
    fremd=$(cat "$WORK/fremd/$1" 2>/dev/null || echo '')
    if [ -z "$fremd" ]; then
        printf 'sprachfall %s NICHT MESSBAR (Fremdbestand nicht erhoben)\n' "$1"
        printf 'fall %s\n' "$1" >>"$WORK/nichtmessbar"
        return 1
    fi
    if [ "$fremd" -ge "$FREMD_SCHWELLE" ]; then
        printf 'sprachfall %s NICHT MESSBAR (Fremdbestand %s Treffer)\n' "$1" "$fremd"
        printf 'fall %s\n' "$1" >>"$WORK/nichtmessbar"
        return 1
    fi
    return 0
}
```

**Fallmuster, zehnmal identisch** (`98b:428-446`, Fall 1 als Vorlage):

```sh
FALL=1
if messbar 1; then
    search 'Genehmigung' "$WORK/compound.json" || true
    jq -e '.ocs.data.entries | length == 1' "$WORK/compound.json" >/dev/null 2>&1 ||
        fail "a compound searched through one constituent did not bring back exactly one file" "$WORK/compound.json"
    urteil 1
fi
```

**Bilanz mit ZWEI Zahlen in einer Zeile** (`98b:573-580`):

```sh
ROT=$(sort -u "$WORK/fehler" | grep -c . || true)
NICHTMESSBAR=$(sort -u "$WORK/nichtmessbar" | grep -c . || true)
BESTANDEN=$((10 - ROT - NICHTMESSBAR))
printf 'sprachfaelle bestanden %s von 10, davon %s nicht messbar\n' "$BESTANDEN" "$NICHTMESSBAR"
```

**Error handling: alle Abbrueche NACH der Pipeline** (`98b:618-664`) - das ist
der wichtigste strukturelle Griff und gilt fuer jedes neue Messskript:

```sh
} 2>&1 | tee "$ZIEL"

# Everything below the pipeline, because the return code of a pipeline belongs to
# tee: an exit inside the block above would only leave the subshell, and the
# refusal would be a line in the raw file that nobody reads.
vorpruefung=$(cat "$WORK/vorpruefung-urteil" 2>/dev/null || echo 'vorpruefung-gefahren nein')
...
if [ "$vorpruefung" != 'vorpruefung-gefahren ja' ]; then
    echo "98b-sprachfaelle: the pre check of the foreign stock could not be driven" >&2
    exit 19
fi
...
echo "98B-SPRACHFAELLE-FERTIG"
```

**Strukturelle Aenderung gegenueber `98b`** (RESEARCH 1.6): die Rang-Pruefung
kann erst nach Upload und Indexierung laufen und wandert als Abschnitt 3b
zwischen Indexierung (`98b:391-416`) und Faelle (`98b:418`).

---

### `docs/measurements/2026-09-v12-messung/skripte/9x-cron-vorpruefung.sh` (guard, fail-closed)

**Analog Konfigzweig und Abbruch:** `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/93-nullstand.sh`
**Analog Wirkungszweig:** `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/96b-waechter.sh`

**Kopf-Muster "warum dieser Schritt existiert" plus nummerierte Quellenliste**
(`93-nullstand.sh:1-16`) - genau die Form, die der zweiteilige Cron-Check
braucht:

```sh
#!/bin/sh
# Both halves stand at nought, proven with figures, before the base load is
# measured and before the rebuild is started.
#
# Why this step exists at all. ... so this step reads four sources and prints a
# number from each of them:
#
#   1. the contents of the volume: ...
#   2. the end states of oc_findling_file_state, over occ
```

**Frist gegen die langsamste Uhr, als Variable mit Begruendung**
(`93-nullstand.sh:47-50`):

```sh
# The frist, in seconds, against the slowest clock involved. 300 s poller backoff
# plus two rounds of the five minute system cron, so 360 is the floor and not the
# target.
FRIST="${FRIST:-360}"
```

**Urteil in eine Datei schreiben, dann nach der Pipeline lesen und abbrechen**
(`93-nullstand.sh:149-176`) - das ist der fail-closed-Griff aus D-08:

```sh
    vorrat=$(vorrat_von "$WORK/status-nachher.txt")
    printf 'arbeitsvorrat-nachher %s\n' "$vorrat"
    printf '%s\n' "$vorrat" >"$WORK/vorrat"
    if [ "$vorrat" -gt 0 ]; then
        echo "arbeitsvorrat-da ja"
    else
        echo "arbeitsvorrat-da nein"
        echo "ROTES URTEIL: the rebuild did not start. ..."
    fi
} 2>&1 | tee "$ZIEL"

# Read back out of the file rather than out of the pipeline, because the exit
# status of a pipeline that ends in tee is the status of tee.
vorrat=$(cat "$WORK/vorrat" 2>/dev/null || echo 0)
if [ "$vorrat" -le 0 ]; then
    echo "93-nullstand: the work stock is still nought after $FRIST seconds" >&2
    exit 10
fi
```

**Wirkungszweig: Beobachtungsschleife mit Deckel und gezaehlten Lesungen**
(`96b-waechter.sh`, Schleifenkopf) - die Zahl "vorrat=0 in N von M Lesungen"
entsteht genau hier:

```sh
RUNDE=0
LESUNGEN=0
...
    printf 'deckel: %s runden a %s s\n' "$DECKEL" "$INTERVALL"
    while [ "$RUNDE" -lt "$DECKEL" ]; do
        RUNDE=$((RUNDE + 1))
        lesung=$(tail -1 "$AUFNAHMEN" 2>/dev/null | python3 "$LESER" 2>/dev/null || true)
        [ -n "$lesung" ] || lesung='unklar unklar unklar'
        # shellcheck disable=SC2086
        set -- $lesung
        vorrat="${1:-unklar}"
        if [ "$vorrat" != unklar ] || [ "$embedded" != unklar ]; then
            LESUNGEN=$((LESUNGEN + 1))
        fi
```

**Warnung an den Planer** (RESEARCH Befund 4.1, Pitfall 3): ein Check, der nur
die Konfiguration liest, haette am 10.09. GRUEN gemeldet. Beide Zweige gehoeren
in die Aufgabenliste, sonst erfuellt der Plan MESS-06 dem Buchstaben nach und
verfehlt den Befund.

---

### `docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md` (doc)

**Analog:** `docs/measurements/2026-09-werkzeugfixe/skripte/00-ablauf.md` (133 Zeilen, exakt dieselbe Gattung)

**Gliederung woertlich uebernehmbar:**

1. Kopf mit zwei Saetzen vorweg: was der Lauf beweist und was nicht, plus Deckel
   und Owner-Freigabe (`00-ablauf.md:9-20`)
2. `## 1. Was dieser Lauf misst` mit Befundtabelle (Befund, was schiefging, was
   der Fix tut, wo der Fix liegt) (`:30-33`)
3. `## 2. Die Schrittfolge` als Tabelle `Nr | Schritt | Rohdatei | Die Aussage,
   an der der Schritt haengt` (`:54-63`)
4. `## 3. Die Erwartung, vorher aufgeschrieben` als Tabelle `Nr | Erwartung |
   Woher sie kommt`, E1..E8 (`:84-93`)
5. `## 4. Woran der Lauf abgebrochen wird` als Tabelle `Bedingung | Wo sie
   greift | Folge` mit den Rueckgabewerten (`:107-117`)
6. `## 5. Nach dem Lauf` (`:125-133`)

**Der Satz, der die Datei traegt** (`00-ablauf.md:79-82`):

```markdown
Dieser Abschnitt ist der Grund, warum diese Datei vor der Anfahrt entsteht. Was
hier steht, wird nach der Messung **nicht** angepasst.
```

**Die Zeile, die die Anfahrt beendet, bevor sie Geld kostet** (`:57`, woertlich
auch ins Runbook):

```markdown
Der Index ist intakt und die Box ist die, gegen die Phase 10 gemessen hat:
**52.111 indexiert, 37 uebersprungen, 0 fehlgeschlagen**, 3.9Gi, 2 Kerne,
aarch64. Stimmt das nicht, endet die Anfahrt hier
```

**Schlusszeile zum Vokabular-Gate** (`:132-133`) - dieselbe Zeile ans Ende des
neuen Ablaufplans:

```markdown
Vor dem Fertigmelden laeuft das Vokabular-Gate lokal ueber die Dateien dieses
Verzeichnisses, wie ueber jede nach aussen sichtbare Datei dieses Projekts.
```

---

### `docs/runbook-messbox.md` (doc, dauerhaft)

**Analog Form und Groessenordnung:** `docs/measurements/2026-09-werkzeugfixe/skripte/00-ablauf.md` (133 Zeilen)
**Analog Tiefe und wiederkehrende Handgriffe:** `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/00-ablauf.md` (313 Zeilen, Abschnitt 1)

Es gibt in `docs/` heute KEIN dauerhaftes Runbook (`docs/` traegt nur
Themendokumente: `performance.md`, `uninstall.md`, `install-check.md` und so
fort). Die beiden `00-ablauf.md` sind die naechsten Verwandten, aber sie sind
laufgebunden. Der Planer muss die Form uebernehmen und die Laufbindung
weglassen.

**Zu uebernehmende Muster aus den beiden Analogen:**

| Muster | Quelle | Uebernahme |
|---|---|---|
| Zwei Saetze vorweg, die den Rest tragen (Geltungsbereich, Deckel) | `2026-09-werkzeugfixe/skripte/00-ablauf.md:9-20` | Abschnitt 1 und 2 des Runbooks (D-09, D-05) |
| Tabelle `Nr | Schritt | Rohdatei | Aussage` | ebenda `:54-63` | Abschnitt 4, nummerierte Copy-paste-Bloecke (D-10) |
| Tabelle `Bedingung | Wo sie greift | Folge` mit Exit-Codes | ebenda `:107-117` | Abschnitt 7, Messreihenfolge mit Abbruchpfaden |
| Tabelle der wiederkehrenden Handgriffe, die `aws_box.sh start` NICHT erledigt (A-Record, `/etc/hosts`-Pin, DI-05-36-Bewaffnung, Speichergrenze, nur EINE Nextcloud, Git-Pfad-Umschreibung) | `2026-09-vergleichsmessung-m7g/skripte/00-ablauf.md`, Abschnitt 1; zusammengefasst in RESEARCH 3.3 | Abschnitt 4 des Runbooks |
| Kostensaetze und Deckelgeschichte | `scripts/ops/aws_box.sh:121-151`, RESEARCH 7.1 | Deckel-Rechenblatt, Abschnitt 2 |

**Sicherheitsregel, die in den Kopf des Runbooks gehoert** (RESEARCH, Security
Domain): das Runbook liegt im oeffentlichen Repositorium. Dateipfade und
Variablennamen ja, Werte nein: keine IP-Adressen, keine lebenden Instanz- oder
Volume-Kennungen, keine Passwortdateiinhalte. Die Snapshot-Kennung ist
unbedenklich, sie steht bereits in committeten Dateien.

**Prosa-Konventionen:** echte Umlaute (das Runbook ist deutsche Prosa), keine
Em-Dashes, keine Emojis. Fuer `docs/**` gibt es dafuer kein Gate, die Regel gilt
trotzdem.

---

### `.planning/phases/12-.../12-STABLE35-ENTSCHEID.md` (doc, Entscheidungsnotiz)

**Analog:** `.planning/milestones/v1.1-phases/11-haertung-und-store-einreichung-v1-1/11-VORENTSCHEIDE.md`

**Kopf-Muster** (`11-VORENTSCHEIDE.md:1-8`):

```markdown
# Phase 11: Vorentscheide V-1 und V-2

**Angelegt:** 2026-09-10 (Plan 11-01, Task 1)
**Zweck:** Zwei Fragen stehen vor der Arbeit dieser Phase und nicht in ihrer
Mitte. ... Diese Datei stellt die Beleglage bereit und traegt nach dem
Checkpoint die beiden Entscheide woertlich mit Datum. Die Folgeplaene zitieren
die Optionskennung (v1-a, v1-b, v2-a, v2-b) und keine Zusammenfassung.
```

**Abschnittsfolge je Frage** (`11-VORENTSCHEIDE.md:12-66`), woertlich uebernehmbar:

```markdown
## V-1, DI-07-03: <die Frage in einem Halbsatz>
### Was festgestellt ist      <- Belege mit Datei:Zeile, Tabellen mit Zahlen
### Was unklar ist
### Die Leitplanke, die fuer beide Optionen gilt
### Option a: ...
### Option b: ...
```

**Anwendung auf Phase 12:** Beide Zweige (D-01/D-02 und D-03) werden VOR dem
16.09. als Option a und Option b ausformuliert, inklusive des fertigen
YAML-Kommentartextes. Am 16.09. wird nur gelesen, welcher greift (Pitfall 6).

---

### `scripts/ops/aws_box.sh` - neuer Unterbefehl `restore` (ops-tool, AWS-API)

**Analog im selben File:** `cmd_volume:320-384` (Aufnahme statt zweiter
Erzeugung, Waiter, Zustandsdatei) und `cmd_snapshot:652-760` (lesende
Bestaetigung, unabhaengige Nachlese, Geduld mit dem Waiter).

**Vorspann jedes Unterbefehls** (`cmd_volume:320-329`):

```sh
cmd_volume() {
    require_credentials
    require_tools
    require_state

    if [ -n "${VOLUME_ID:-}" ]; then
        echo "aws_box: $STATE_FILE already names volume $VOLUME_ID" >&2
        echo "run status, or destroy first: two volumes are two invoices" >&2
        exit 1
    fi
```

**Aufnahme statt zweiter Erzeugung** (`cmd_volume:331-358`) - genau dieser Block
muss in `restore` wiederkehren, mit `--snapshot-id` in der Erzeugung:

```sh
    # An unattached volume that already carries the tag is picked up instead of
    # creating a second one. This is not convenience: the first run of this
    # subcommand created the volume and then failed on the attach, and a retry
    # that starts with create-volume leaves the first one behind as an invoice
    # nobody is watching. The search is limited to the zone of the box, because
    # a volume in another zone could never be attached to it anyway.
    volume_id=$(ec2 describe-volumes \
        --filters "Name=tag:$TAG_KEY,Values=$TAG_VALUE" \
        "Name=availability-zone,Values=$ZONE" \
        "Name=status,Values=available" | json '
import json
import sys

volumes = json.load(sys.stdin)["Volumes"]
print(volumes[0]["VolumeId"] if len(volumes) == 1 else "")
')
    if [ -n "$volume_id" ]; then
        echo "aws_box: an unattached volume with the tag exists, using $volume_id"
    else
        response=$(ec2 create-volume \
            --availability-zone "$ZONE" \
            --size "$VOLUME_SIZE_GB" \
            --volume-type "$VOLUME_TYPE" \
            --tag-specifications \
            "ResourceType=volume,Tags=[{Key=Name,Value=$VOLUME_NAME},{Key=$TAG_KEY,Value=$TAG_VALUE}]")
        volume_id=$(printf '%s' "$response" | json 'import json,sys; print(json.load(sys.stdin)["VolumeId"])')
    fi
```

**Waiter statt Schleife, Hausregel seit 2026-09-04** (`cmd_volume:360-366`):

```sh
    echo "aws_box: waiting for volume $volume_id to become available"
    "$AWS_BIN" --region "$REGION" ec2 wait volume-available --volume-ids "$volume_id"

    echo "aws_box: attaching $volume_id to $BOX_INSTANCE_ID as $VOLUME_DEVICE"
    ec2 attach-volume --volume-id "$volume_id" --instance-id "$BOX_INSTANCE_ID" \
        --device "$VOLUME_DEVICE" >/dev/null
    "$AWS_BIN" --region "$REGION" ec2 wait volume-in-use --volume-ids "$volume_id"
```

**Zustandsdatei anhaengen, nie neu schreiben, umask 077** (`cmd_volume:368-383`):

```sh
    # The state file was written by hand for the instance, so this appends
    # rather than rewriting: losing the instance id here would lose the only
    # record of a machine that costs money.
    (
        umask 077
        {
            echo "VOLUME_ID=$volume_id"
            echo "VOLUME_NAME=$VOLUME_NAME"
            echo "VOLUME_SIZE_GB=$VOLUME_SIZE_GB"
            echo "VOLUME_TYPE=$VOLUME_TYPE"
            echo "VOLUME_CREATED_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        } >>"$STATE_FILE"
    )
    echo "aws_box: volume=$volume_id noted in $STATE_FILE, tag $LABEL"
    echo "aws_box: nitro exposes it as a nvme device and ignores $VOLUME_DEVICE,"
    echo "so find it by size on the box and mount it by uuid, never by name"
```

**Id als optionales Argument, damit ein zweiter Aufruf nichts zweites erzeugt**
(`cmd_snapshot:666-669`):

```sh
    snapshot_id="${1:-}"
    if [ -n "$snapshot_id" ]; then
        echo "aws_box: $snapshot_id was handed in, so nothing is created here"
    else
```

**Unabhaengige Nachlese statt Vertrauen in den Waiter** (`cmd_snapshot:701-739`):

```sh
    # The waiter of the cli and no loop of our own, house rule since 2026-09-04.
    waiter=0
    "$AWS_BIN" --region "$REGION" ec2 wait snapshot-completed --snapshot-ids "$snapshot_id" || waiter=1

    # The verification, and it is this and not the waiter: a waiter that returns
    # says the api stopped answering pending, it does not say what the snapshot
    # now is.
    details=$(ec2 describe-snapshots --snapshot-ids "$snapshot_id" | json "
...
print('State       %s' % snapshot['State'])
print('VolumeId    %s' % snapshot['VolumeId'])
")
    snapshot_state=$(printf '%s' "$details" | sed -n 's/^State  *//p')
    snapshot_volume=$(printf '%s' "$details" | sed -n 's/^VolumeId  *//p')
    if [ "$snapshot_volume" != "$VOLUME_ID" ]; then
        echo "aws_box: $snapshot_id belongs to $snapshot_volume and not to the data" >&2
        exit 1
    fi
```

**Umtaggen mit Rueckleseprobe (NEU, kein Analog im Skript, Quelle
`docs/measurements/2026-09-werkzeugfixe/rohdaten/07-snapshot-und-abbau.txt`
Abschnitt 10 und RESEARCH Code Example D).** Das aus dem Snapshot erzeugte
Volume erbt `purpose=findling-corpus-keep` und entgeht damit dem Tag-Sweep von
`cmd_destroy`:

```sh
ec2 create-tags --resources "$volume_id" \
    --tags "Key=$TAG_KEY,Value=$TAG_VALUE" "Key=Name,Value=$VOLUME_NAME"
ec2 describe-tags --filters "Name=resource-id,Values=$volume_id"   # Nachlese
```

**Die drei Stellen, die bei einem neunten Unterbefehl mitwandern muessen:**

| Stelle | Zeile | Ist |
|---|---|---|
| Kopfkommentar "Eight subcommands" mit Liste | `aws_box.sh:24-36` | acht Eintraege |
| `# Usage:`-Zeile im Kopf | `aws_box.sh:65` | `<prices\|create\|volume\|status\|stop\|start\|snapshot\|destroy>` |
| `usage()` | `aws_box.sh:153-166` | dieselbe Zeile plus eine Beschreibungszeile je Unterbefehl |
| `case "$COMMAND"` | `aws_box.sh:1012-1025` | acht Zweige plus die Meldung `one of the eight subcommands is required` |

```sh
case "$COMMAND" in
    prices) cmd_prices ;;
    create) cmd_create ;;
    volume) cmd_volume ;;
    status) cmd_status ;;
    stop) cmd_stop ;;
    start) cmd_start ;;
    snapshot) cmd_snapshot "$@" ;;
    destroy) cmd_destroy "$@" ;;
    '')
        echo "aws_box: one of the eight subcommands is required" >&2
```

**Konstanten, die `restore` braucht** (`aws_box.sh:79-114`): `REGION`, `ZONE`,
`VOLUME_SIZE_GB=60`, `VOLUME_TYPE='gp3'`, `TAG_KEY='purpose'`,
`TAG_VALUE='findling-phase5'`, `KEEP_TAG_VALUE='findling-corpus-keep'`. Eine
neue Konstante fuer die Snapshot-Vorgabe `snap-03f1d1d9ad9262704` folgt dem
Muster von `SNAPSHOT_NAME:110` und `SNAPSHOT_DESCRIPTION:114`.

**Grenze des Unterbefehls** (RESEARCH Open Question 5): `restore` endet wie
`cmd_volume` beim Anhaengen. Das Mounten ist ein Handgriff auf der Box und ein
nummerierter Runbook-Block, kein AWS-Aufruf.

---

### `backend/tests/test_ops_scripts.py` (test)

**Analog:** derselbe File, `test_the_aws_tool_names_its_eight_subcommands_in_the_usage:264-280`.

Der Test prueft die Usage-Zeile woertlich und wird mit einem neunten
Unterbefehl rot. Umbenennen und anpassen gehoert in DIESELBE Aenderung
(Pitfall 8).

```python
def test_the_aws_tool_names_its_eight_subcommands_in_the_usage() -> None:
    """Eight and not five: the box lives between stop and start, and it outlives itself.

    ... snapshot came last, in 11-12, because the corpus of the run has to
    survive the machine that carried it, and a snapshot taken by hand is a
    snapshot whose verification nobody keeps.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    for subcommand in ("prices", "create", "volume", "status", "stop", "start", "snapshot", "destroy"):
        assert f"    {subcommand})" in text, subcommand
    assert "usage: aws_box.sh <prices|create|volume|status|stop|start|snapshot|destroy>" in text
```

**Muster fuer die neuen Zusicherungen des `restore`-Unterbefehls**
(`test_ops_scripts.py:282-315`): Koerper herausschneiden und die Reihenfolge der
Aufrufe pruefen, nicht nur ihre Anwesenheit:

```python
def test_the_aws_snapshot_refuses_a_box_that_is_not_stopped() -> None:
    text = AWS_BOX.read_text(encoding="utf-8")
    body = text.split("cmd_snapshot() {", 1)[1].split("\n# Gone has three shapes", 1)[0]
    assert "!= 'stopped'" in body
    # The refusal happens before anything is created, so the check stands in
    # front of the call that makes the snapshot.
    assert body.index("'stopped'") < body.index("create-snapshot")
```

Analog fuer `restore`: `body.index("create-volume") < body.index("create-tags")`
und `describe-snapshots` vor `create-volume`.

**Weitere Gates, die eine Aenderung an `aws_box.sh` mittragen muss** (RESEARCH
2.3): `test_the_script_carries_neither_a_dash_nor_a_carriage_return`,
`test_the_aws_tool_waits_with_the_waiters_and_not_with_a_loop`,
`test_the_box_tool_labels_every_resource_it_creates`.

---

### `backend/tests/test_measurement_scripts.py` (test)

**Analog:** derselbe File.

**Die Konstanten, die um das neue Laufverzeichnis wachsen** (`:62-79`):

```python
REPO_ROOT = Path(__file__).resolve().parents[2]
MEASUREMENTS_DIR = REPO_ROOT / "docs" / "measurements"
RUN_DIR = MEASUREMENTS_DIR / "2026-09-vergleichsmessung-m7g" / "skripte"
FIX_RUN_DIR = MEASUREMENTS_DIR / "2026-09-werkzeugfixe" / "skripte"

# The two directories the narrow scope covers. Written down as a pair rather
# than globbed, because widening it is a decision and not a side effect of the
# next directory somebody creates: the semantic run of 05.09. must stay outside
# it, and the reason is in the docstring above.
NARROW_SCOPE_DIRS = (RUN_DIR, FIX_RUN_DIR)
```

**Der weite Bereich nimmt das neue Verzeichnis von selbst auf** (`:780-795`) -
hier ist nichts zu tun:

```python
def measurement_scripts() -> list[Path]:
    """Every script of every measurement this repository holds."""
    return sorted(path for path in MEASUREMENTS_DIR.glob("**/skripte/*") if path.suffix in SCRIPT_SUFFIXES)


def scripts_of_this_run() -> list[Path]:
    """Every script of the run directories written under these rules.

    Two directories since plan 11-03. ...
    """
    return sorted(
        path for directory in NARROW_SCOPE_DIRS for path in directory.glob("*") if path.suffix in SCRIPT_SUFFIXES
    )
```

**Der Pin-Test, der mitwandert** (`:992-1004`):

```python
def test_the_narrow_scope_covers_the_two_run_directories_written_under_these_rules() -> None:
    """Widening the narrow scope is a decision, so it is pinned here.
    ...
    """
    assert NARROW_SCOPE_DIRS == (RUN_DIR, FIX_RUN_DIR)
    found = scripts_of_this_run()
    assert SUCCESSOR_LANGUAGE_CASES in found
    assert DRIVEN_LANGUAGE_CASES in found
    assert not [path for path in found if path.parent.parent.name == "2026-09-05-semantiklauf-m7g"]
```

**Waechter, der NICHT angefasst wird** (`:1007-1019`): der sha256 von
`98-sprachfaelle.sh` bleibt. Die Regelkonstante ist der Text, der beim Rotwerden
erscheint:

```python
DRIVEN_FASSUNG_RULE = (
    "eine gefahrene Messfassung ist Teil des Belegs, und ein Fix entsteht als neue Datei in einem neuen Laufverzeichnis"
)
```

Ein zweiter Waechter ueber `98b-sprachfaelle.sh` ist eine Option des Planers:
`98b` ist gefahren worden, traegt aber heute keinen sha256-Pin (RESEARCH Open
Question 1).

---

### `.github/workflows/python.yml` (config)

**Analog:** derselbe File, `:3-25`. Das Begruendungsmuster existiert bereits
woertlich fuer `scripts/dev/build_corpus.py` und ist auf
`docs/measurements/**` uebertragbar:

```yaml
# Path filtered on purpose: a documentation commit must not spend runner minutes
# on the backend gates.
on:
  push:
    paths:
      - 'backend/**'
      - 'scripts/**'
      # Two reasons for the second line, and both are load bearing.
      # backend/tests/test_corpus_terms.py and backend/tests/test_ocr_quality.py
      # load scripts/dev/build_corpus.py at run time ... Without this
      # line the breakage surfaces on the next commit that happens to touch
      # backend/** and is blamed on the wrong one.
      - '.github/workflows/python.yml'
  pull_request:
    paths:
      - 'backend/**'
      - 'scripts/**'
      - '.github/workflows/python.yml'
```

Die neue Zeile gehoert in BEIDE Listen (`push` und `pull_request`), mit einem
Kommentar nach demselben Muster: `test_measurement_scripts.py` liest Dateien
unter `docs/measurements/**/skripte/`, also ist ein Filter, der enger ist als
sein Pruefgegenstand, ein Gate, das seinen eigenen Gegenstand nicht sehen kann.

---

### `.github/workflows/deploy-harp.yml` (config, stable35)

**Analog:** derselbe File, `:211-273`. Der Kommentar ist eine fortgeschriebene
Entscheidungskette, und genau so wird er weitergeschrieben: jeder Eintrag traegt
Datum, Plan, Beleg und Nachfolge-Adresse.

**Ist-Zustand des Matrixeintrags** (`:217-273`):

```yaml
          - server-version: stable35
            php-version: '8.3'
            # The only entry that may fail, and here is the condition for removing
            # this flag: as soon as Nextcloud 35 is generally available. ...
            #
            # RE-CHECK DATE: 2026-09-16. On that day this flag and this whole
            # paragraph come out, the leg becomes must-be-green, and a red run is a
            # finding rather than a reason to put the flag back. The plan that holds
            # the follow-through is 06-12, the store submission, ...
            #
            # Decided on 2026-09-10 by phase 11, decision v2-a
            # (.planning/phases/11-haertung-und-store-einreichung-v1-1/
            # 11-VORENTSCHEIDE.md, section V-2): the declared window of v1.1.0
            # stays at min-version 33 and max-version 35, both info.xml stay as
            # they are, this entry stays with tolerate-failure: true, ...
            tolerate-failure: true
            runner: ubuntu-24.04
```

**Muster fuer den Fortschreibe-Eintrag** (aus `:254-271` abgelesen): Datum,
entscheidendes Gremium/Plan, Aktenzeichen der Notiz, der gelesene Beleg
(`gh api repos/nextcloud/server/releases` mit Tag und Datum), und die neue
Nachfolge-Adresse fuer das RE-CHECK.

**Was NICHT passieren darf** (RESEARCH 5.1/5.2): die `info.xml` stehen bereits
auf `min-version="33" max-version="35"` (`php/appinfo/info.xml:219`,
`backend/appinfo/info.xml:225`). Es ist nichts zu heben. Und der
`stable35`-Eintrag darf nicht entfernt werden, nur sein Flag darf fallen:
`backend/tests/test_lockstep_versions.py:387` prueft, dass die Matrix jede
Version des Fensters abdeckt.

---

## Shared Patterns

### 1. Der Messskript-Kopf: keine Maschinenpfade, alles als Variable mit Vorgabe

**Quelle:** `98b-sprachfaelle.sh:91-98`, identisch in `94-grundlast.sh:42-49`,
`93-nullstand.sh:38-45`
**Gilt fuer:** jedes neue Skript unter `docs/measurements/**/skripte/`

```sh
# Everything a machine could differ in is a variable with a default, so this file
# carries no path of one machine. The first default is derived from the location
# of the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
```

Durchgesetzt von `machine_shapes_in_code` (`test_measurement_scripts.py:812-827`):
`/home/`, `sys.path.insert`, `sys.path.append`, `drillhelfer` sind im Code
verboten, in Kommentaren und in kommentierten Vorgabewerten erlaubt.

### 2. Block in `tee`, Urteil in eine Datei, Abbruch NACH der Pipeline

**Quelle:** `93-nullstand.sh:165-176` und `98b-sprachfaelle.sh:618-664`
**Gilt fuer:** `98c-sprachfaelle.sh`, die Cron-Vorpruefung, jedes neue Messskript

```sh
} 2>&1 | tee "$ZIEL"

# Read back out of the file rather than out of the pipeline, because the exit
# status of a pipeline that ends in tee is the status of tee.
vorrat=$(cat "$WORK/vorrat" 2>/dev/null || echo 0)
if [ "$vorrat" -le 0 ]; then
    echo "93-nullstand: the work stock is still nought after $FRIST seconds" >&2
    exit 10
fi

echo "93-NULLSTAND-FERTIG"
```

### 3. `occ` ueber zwei Schichten, Passwort nur aus der Umgebung

**Quelle:** `98b-sprachfaelle.sh:179-190`
**Gilt fuer:** jedes Skript, das `occ` auf der Box ruft

```sh
# The wrapper carries OC_PASS across the two layers that would otherwise eat it,
# and only when it is set: sudo clears the environment under env_reset, and
# docker exec passes none on of its own accord.
occ() {
    if [ -n "${OC_PASS:-}" ]; then
        sudo --preserve-env=OC_PASS docker exec -e OC_PASS \
            --user www-data "$NEXTCLOUD" php occ "$@"
    else
        sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
    fi
}
```

Die einfache Fassung ohne Passwort steht in `93-nullstand.sh:57-59`.
Durchgesetzt von `passwords_on_a_command_line`
(`test_measurement_scripts.py`, Zusicherung um Zeile 975).

### 4. Zwei Quellen fuer eine Zahl, aus EINEM Aufruf gelesen

**Quelle:** `93-nullstand.sh:61-67`, identisch in `98b-sprachfaelle.sh:192-198`
**Gilt fuer:** jede Zahl, die aus `occ findling:index` kommt

```sh
# The two blocks of the status output, read out of one call rather than out of
# two: they are two sources, but asking twice would let them disagree.
vorrat_von() {
    awk '/^Work stock/ {found = 1; next}
         found && /^  (scheduled|handed to the worker)/ {sum += $NF}
         END {print sum + 0}' "$1"
}
```

### 5. AWS: Waiter warten, Nachlese urteilen, jede Ressource taggen

**Quelle:** `aws_box.sh:59-63` (Hausregel), `:360-366` (Waiter), `:701-739` (Nachlese)
**Gilt fuer:** den neuen `restore`-Unterbefehl

```sh
# Rate limits, as a house rule since 2026-09-04: every loop in here that waits
# for AWS uses the waiters of the CLI, which poll on a fixed interval of 15
# seconds and give up after a bounded number of tries. No hand rolled busy loop,
# because a diagnostic run that asked a foreign API sixty times a minute is what
# earned this repository the rule.
```

Und `aws_box.sh:50-57`:

```sh
# Every resource this script creates carries the tag purpose=findling-phase5.
# In an account that holds other things a tag is the only way to find something
# that was forgotten, and destroy searches by exactly that tag (T-05-19).
#
# With one deliberate exception since 11-12: the snapshot of the corpus carries
# purpose=findling-corpus-keep, because it is the one resource of this run that
# is meant to outlive the box.
```

### 6. Geheimnisse: Namen einmal, Werte nie

**Quelle:** `aws_box.sh:45-48` und `:168-174`
**Gilt fuer:** `aws_box.sh`, alle Messskripte, das Runbook

```sh
require_credentials() {
    # The only two places these names appear. The CLI picks the values up from
    # the environment on its own, so no value ever reaches an argument, a log or
    # this state file.
    : "${AWS_ACCESS_KEY_ID:?access key fehlt}"
    : "${AWS_SECRET_ACCESS_KEY:?secret key fehlt}"
}
```

### 7. Der Zustandsdatei-Ort, ausserhalb des Arbeitsbaums

**Quelle:** `aws_box.sh:116-119`
**Gilt fuer:** jede Zeile des Runbooks, die `box.env` anfasst

```sh
# Outside the working tree, same reason as in the Hetzner tool: a state file in
# the repository is one careless git add away from a public commit.
STATE_DIR="${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}"
STATE_FILE="$STATE_DIR/box.env"
```

### 8. Textregeln, teils als Gate durchgesetzt

| Regel | Durchsetzung | Geltung |
|---|---|---|
| Kein Wagenruecklauf (als Bytes geprueft) | `carriage_returns_in` (`test_measurement_scripts.py:798-804`), gleiches Gate in `test_ops_scripts.py` | alle Skripte unter `docs/measurements/**/skripte/` und `scripts/ops/` |
| Kein Halbgeviert- und kein Geviertstrich | `DASHES = (chr(0x2014), chr(0x2013))` (`test_measurement_scripts.py:216`, `dashes_in:807-809`) | wie oben; fuer `docs/**` kein Gate, Regel gilt trotzdem |
| Shebang exakt `#!/bin/sh\n` oder `#!/usr/bin/env python3\n` | enger Bereich, `NARROW_SCOPE_DIRS` | nur die gepinnten Laufverzeichnisse, daher der Pflichteintrag des neuen |
| Kein Passwort auf der Kommandozeile | `passwords_on_a_command_line` | enger Bereich |
| ASCII-Bezeichner im Code (`ue`, `ae`), echte Umlaute nur in Prosa | Konvention, kein Gate; `98b` haelt sie durchgaengig | Skripte gegen Doku |
| Vokabular-Gate lokal vor dem Fertigmelden | Zeile am Ende von `2026-09-werkzeugfixe/skripte/00-ablauf.md:132-133` | jede nach aussen sichtbare Datei |

**Hinweis zum verbotenen Vokabular der Owner-Regel** (das Wort fuer eine
Ablage alter Bestaende, mit A beginnend): RESEARCH (Project Constraints,
Annahme A2) hat festgestellt, dass es in diesem Repositorium KEIN solches Gate
gibt und `.planning/ROADMAP.md` das Wort mehrfach benutzt. Der Planer soll es in
neuen, oeffentlich sichtbaren Artefakten vermeiden, aber kein Gate dafuer bauen.

### 9. Die Hausregel ueber gefahrene Messfassungen

**Quelle:** `test_measurement_scripts.py:89-93` und `:981-1019`
**Gilt fuer:** jede Entscheidung "98b anpassen oder 98c bauen"

```python
# The sentence the watchman says when it goes red. It is a constant so that the
# diagnosis cannot drift away from the rule it defends.
DRIVEN_FASSUNG_RULE = (
    "eine gefahrene Messfassung ist Teil des Belegs, und ein Fix entsteht als neue Datei in einem neuen Laufverzeichnis"
)
```

Konsequenz fuer den Plan: neues Laufverzeichnis, neue Dateien. `98b` und `98`
bleiben unberuehrt.

---

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|---|---|---|---|
| `docs/runbook-messbox.md` | doc (dauerhaftes Betriebsrunbook) | n/a | In `docs/` liegt heute kein Runbook, nur Themendokumente (`performance.md`, `uninstall.md`, `install-check.md`, `dev-setup.md`, `reconcile.md`). Die naechsten Verwandten sind die beiden laufgebundenen `00-ablauf.md`; Form und Tabellen sind uebernehmbar, die Laufbindung nicht. Ergaenzend: RESEARCH 3.5 liefert die neunteilige Gliederung, RESEARCH 3.3 die Tabelle der wiederkehrenden Handgriffe, RESEARCH 7 die Posten des Deckel-Rechenblatts |

Teil-Analog fuer den `restore`-Unterbefehl: `cmd_volume` deckt alles ausser dem
Umtaggen ab. Fuer das Umtaggen mit Rueckleseprobe gibt es im Skript kein Vorbild,
nur das Kommando in
`docs/measurements/2026-09-werkzeugfixe/rohdaten/07-snapshot-und-abbau.txt`
Abschnitt 10 und RESEARCH Code Example D.

---

## Reihenfolge-Hinweise fuer den Planer

Diese ergeben sich aus den Analogen und aus den Gates, nicht aus dem Zuschnitt:

1. **Der stable35-Strang ist terminlich isoliert** (Frist 16.09.). Beide Zweige
   vorher ausformulieren, am 16.09. nur noch einsetzen (Pitfall 6).
2. **`aws_box.sh` und `backend/tests/test_ops_scripts.py` gehoeren in EINE
   Aenderung**, sonst ist das Usage-Gate rot (Pitfall 8).
3. **Neues Laufverzeichnis, `NARROW_SCOPE_DIRS` und der Pfadfilter in
   `python.yml` gehoeren in EINE Welle.** Ein Commit, der nur unter
   `docs/measurements/**` anlegt, startet `python.yml` heute nicht; die Gates
   faerben dann den naechsten, falschen Commit rot (RESEARCH 6.2).
4. **Die lesenden AWS-Proben** (`describe-snapshots` auf
   `snap-03f1d1d9ad9262704`, `aws_box.sh prices`, `describe-tags`) kosten nichts
   und liefern die erwarteten Ausgaben fuer das Runbook. Ohne die Snapshot-Probe
   steht der gesamte D-09-Hauptpfad auf Annahme A3.

---

## Metadata

**Analog search scope:** `docs/measurements/2026-09-werkzeugfixe/skripte/`,
`docs/measurements/2026-09-vergleichsmessung-m7g/skripte/`, `scripts/ops/`,
`backend/tests/`, `.github/workflows/`, `docs/`,
`.planning/milestones/v1.1-phases/11-.../`

**Files read in full:** `98b-sprachfaelle.sh` (664), `72-fremdbestand.py` (75),
`93-nullstand.sh` (176), `2026-09-werkzeugfixe/skripte/00-ablauf.md` (133)

**Files read in targeted ranges:** `aws_box.sh` (1-234, 316-385, 648-747,
990-1031), `test_ops_scripts.py` (240-319), `test_measurement_scripts.py`
(60-109, 780-838, 975-1024), `python.yml` (1-40), `deploy-harp.yml` (205-279),
`94-grundlast.sh` (38-122), `96b-waechter.sh` (1-40, 100-175),
`11-VORENTSCHEIDE.md` (1-70)

**Pattern extraction date:** 2026-09-14
