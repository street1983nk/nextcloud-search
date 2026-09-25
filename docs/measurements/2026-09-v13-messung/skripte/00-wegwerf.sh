#!/bin/sh
# Die Wegwerf-Bloecke B3, B5 und B4 der v1.3-Anfahrt, MESS-07, auf der Box.
#
# DIESE FASSUNG IST NICHT GEFAHREN. Neben ihr liegt keine Rohdatei; was sie auf
# der Box misst, misst die v1.3-Anfahrt. Ihr Abnahmekriterium ist Form,
# statische Analyse und die Waechter in backend/tests/test_v13_wegwerf.py.
#
# **Wozu.** Drei Fragen der Mehrkern-Rechnung (BL-F04-Vorarbeit vom 25.09.2026,
# Abschnitt 1.2) lassen sich im Produkt nicht stellen, weil ihre Achsen hart
# verdrahtet sind: ein OCR-Slot, zwei onnx-Threads. Sie werden deshalb in
# Wegwerf-Containern DESSELBEN Digests gefahren, mit dem Einstiegspunkt Python,
# nach dem Muster der Schritte A bis D des W4-Jobs in
# .github/workflows/measure.yml:
#
#   b3  RAM je zusaetzlichem OCR-Slot und Durchsatzfaktor zwei Slots auf zwei
#       Kernen: ocr_slot_probe.py (W3) mit N 1 und 2 auf cpuset 0,1 unter
#       --memory 2g, je 3 Runden, danach der Einzelmodus (OMP_THREAD_LIMIT 1
#       gegen ungesetzt)
#   b5  onnx-Durchsatz und Aktivierungsspeicher auf Graviton3: embed.bench in
#       den vier Kombinationen threads 1 und 2, batch 2 und 8, sequence 512, auf
#       cpuset 0,1; neben jeder Kombination rss_sampler.sh gegen genau diesen
#       Bench-Container, max anon je Kombination
#   b4  Kernskalierung auf m7g.4xlarge: W3 fuer N 1, 2, 4, 8, 12, 16 auf cpuset
#       0 bis N-1 ohne Speichergrenze, danach embed.bench threads 1, 2, 4, 8 auf
#       cpuset 0 bis T-1. Die N-Liste wird auf die sichtbare Kernzahl gekuerzt
#       (Rueckfall m7g.2xlarge hat 8), und die Kuerzung steht als Zeile da.
#
# **Was dieses Werkzeug NICHT tut.** Es startet den Produktcontainer nicht neu,
# baut ihn nicht nach und aendert seine Umgebung nicht; es ruft weder das
# Umgebungswerkzeug noch den Abbildwechsel. Vom Produkt liest es nur: den
# Arbeitsvorrat ueber occ findling:index, runState ueber die Admin-Seite und den
# Startzeitpunkt aus docker inspect, vor und nach dem Block. Steht der
# Startzeitpunkt danach anders, ist das eine Zeile und ein Abbruch.
#
# **Leerlauf vor b3 und b5 (Pitfall 12).** Arbeitet das Produkt, misst die Probe
# die Poller-Last mit. Vor b3 und b5 muss deshalb der Arbeitsvorrat 0 und
# runState idle stehen, sonst wird nichts gemessen und das Werkzeug endet mit 50.
# b4 laeuft ohne Produkt (AIO gestoppt, Pitfall 8): steht dort irgendein
# Container, endet es mit 51.
#
# **Das Scan-Material** entsteht in einem eigenen Wegwerf-Container aus
# scripts/dev/build_load_corpus.py mit festem Seed, in derselben Aufrufform wie
# Schritt A des W4-Jobs: acht synthetische Seiten, nie eine Nutzerdatei. Jeder
# docker run dieses Werkzeugs traegt --network none und ein ausdrueckliches
# --cpuset-cpus (T-22-16).
#
# **Woher das Passwort kommt** (nur b3 und b5, fuer runState): zuerst aus der
# Umgebungsvariablen, deren NAMEN PASSWORT_ENV traegt, sonst aus der Datei, auf
# die PWFILE zeigt; von dort in eine Datei unter WORK mit Modus 600 und in eine
# curl-Konfiguration (-K). Auf einer Kommandozeile steht es nie.
#
# Die Rueckgabewerte, im Katalog dieses Laufverzeichnisses:
#
#   2  kein Block, ein unbekannter Block, mehr als ein Argument, oder
#      ABBILD_DIGEST fehlt oder hat nicht die Gestalt sha256:<64 hex>
#   50 b3 oder b5: das Produkt war nicht im Leerlauf (Vorrat nicht 0, runState
#      nicht idle oder unlesbar), sein Startzeitpunkt hat sich bewegt, eine
#      Probe hat keine Zahl hergegeben, oder der Block ist nicht bis zu seinem
#      Ende gelaufen
#   51 b4: ein Container lief neben dem Wegwerf-Container, eine Probe hat keine
#      Zahl hergegeben, oder der Block ist nicht bis zu seinem Ende gelaufen
#
# 52 und 53 gehoeren zu 00-typwechsel.sh, das den Typwechsel fuer b4 auf der
# Entwicklungsmaschine faehrt.
set -eu

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: ABBILD_DIGEST="sha256:<64 Hexziffern>" ./00-wegwerf.sh b3|b5|b4

Genau ein Block:
  b3  OCR-Slots 1 und 2 auf cpuset 0,1 unter 2g, dann der Einzelmodus
  b5  embed.bench threads 1/2 und batch 2/8 bei sequence 512 auf cpuset 0,1
  b4  OCR-Slots 1 2 4 8 12 16 und embed.bench threads 1 2 4 8, nur auf dem
      grossen Typ nach 00-typwechsel.sh hin, ohne laufendes Produkt

Vor b3 und b5 muessen Arbeitsvorrat 0 und runState idle stehen. Stellschrauben
stehen als Umgebungsvariablen im Kopf der Datei, darunter OUT und ABTASTINTERVALL.
HINWEIS
}

if [ "$#" -ne 1 ]; then
    benutzung
    exit 2
fi
BLOCK=$1
case "$BLOCK" in
b3 | b5 | b4) ;;
*)
    echo "00-wegwerf: '$BLOCK' ist kein Block dieses Werkzeugs" >&2
    benutzung
    exit 2
    ;;
esac

# Die Pflichtangabe, geprueft BEVOR ein Verzeichnis angelegt wird. Ein
# Wegwerf-Container eines anderen Digests misst ein anderes Abbild.
case "${ABBILD_DIGEST:-}" in
'')
    echo "00-wegwerf: ABBILD_DIGEST ist nicht gesetzt oder leer" >&2
    benutzung
    exit 2
    ;;
sha256:*[!0-9a-f]*)
    echo "00-wegwerf: ABBILD_DIGEST traegt nicht die Gestalt sha256:<hex>" >&2
    benutzung
    exit 2
    ;;
sha256:*) ;;
*)
    echo "00-wegwerf: ABBILD_DIGEST traegt nicht die Gestalt sha256:<hex>" >&2
    benutzung
    exit 2
    ;;
esac
if [ "${#ABBILD_DIGEST}" -ne 71 ]; then
    echo "00-wegwerf: ABBILD_DIGEST traegt nicht 64 Hexziffern" >&2
    benutzung
    exit 2
fi

SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
ABBILD_REPO="${ABBILD_REPO:-ghcr.io/street1983nk/findling_backend}"
IMAGE="$ABBILD_REPO@$ABBILD_DIGEST"
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
ADRESSE="${ADRESSE:-https://loadtest.infranode.dev}"
BENUTZER="${BENUTZER:-admin}"
# Der NAME der Umgebungsvariablen, nicht ihr Wert (T-10-27, T-15-06).
PASSWORT_ENV="${PASSWORT_ENV:-FINDLING_ADMIN_PASSWORD}"
PWFILE="${PWFILE:-$HOME/work/.pw/admin}"
UEBERSICHT="${UEBERSICHT:-/apps/findling/admin/overview}"
SAMPLER="${SAMPLER:-$REPO/scripts/ops/rss_sampler.sh}"
# Eine Sekunde: ein Bench-Lauf dauert Sekunden bis wenige Minuten, und der
# Abtaster soll mehr als eine Zeile je Kombination schreiben.
ABTASTINTERVALL="${ABTASTINTERVALL:-1}"
# Der feste Seed des Scans, derselbe wie im W4-Job, damit Box und CI dieselben
# Pixel lesen.
SCAN_SEED="${SCAN_SEED:-phase-22-w4}"
B4_SLOTS="1 2 4 8 12 16"
B4_THREADS="1 2 4 8"

mkdir -p "$OUT"
ZIEL="${ZIEL:-$OUT/00-wegwerf-$BLOCK.txt}"
WORK=$(mktemp -d)
chmod 700 "$WORK"
SCAN_DIR=$(mktemp -d "$WORK/scan.XXXXXX")
# Der Container liest den Scan unter seinem eigenen Nutzer, und mktemp legt 700 an.
chmod 755 "$SCAN_DIR"

aufraeumen() {
    rm -rf "$WORK"
}
trap aufraeumen EXIT

protokoll() {
    printf '%s\n' "$*" >>"$WORK/protokollblock"
    printf '%s\n' "$*"
}

occ() {
    sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
}

vorrat_von() {
    awk '/^Work stock/ {found = 1; next}
         found && /^  (scheduled|handed to the worker)/ {sum += $NF; seen = 1}
         END {if (seen) print sum + 0; else print "unlesbar"}' "$1"
}

produktstart() {
    start=$(sudo docker inspect --format '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || true)
    [ -n "${start:-}" ] || start=unlesbar
    printf '%s\n' "$start"
}

# Das Passwort und die Anmeldung, nur fuer b3 und b5. In der Reihenfolge von 94c.
passwort_bereitlegen() {
    PWFELD="$WORK/pwfeld"
    : >"$PWFELD"
    chmod 600 "$PWFELD"
    eval "printf '%s' \"\${$PASSWORT_ENV:-}\"" >"$PWFELD"
    PASSWORT_QUELLE=umgebung
    if [ ! -s "$PWFELD" ]; then
        sudo cat "$PWFILE" 2>/dev/null | tr -d '\n' >"$PWFELD" || true
        PASSWORT_QUELLE=datei
    fi
    if [ ! -s "$PWFELD" ]; then
        PASSWORT_QUELLE=keine
    fi
    JAR="$WORK/cookies.txt"
}

anmelden() {
    rm -f "$JAR"
    curl -sfS -c "$JAR" -o "$WORK/login.html" "$ADRESSE/login" || return 1
    zeichen=$(sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' "$WORK/login.html" | head -1)
    [ -n "${zeichen:-}" ] || return 1
    weiter=$(curl -sS -b "$JAR" -c "$JAR" -o /dev/null -w '%{redirect_url}' \
        -H "Origin: $ADRESSE" \
        --data-urlencode "user=$BENUTZER" \
        --data-urlencode "password@$PWFELD" \
        --data-urlencode "requesttoken=$zeichen" \
        "$ADRESSE/login" || true)
    case "$weiter" in
    '' | */login | */login\?*) return 1 ;;
    esac
    curl -sfS -b "$JAR" -c "$JAR" -o "$WORK/nach-anmeldung.html" "$ADRESSE/settings/admin" || return 1
    zeichen=$(sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' "$WORK/nach-anmeldung.html" | head -1)
    [ -n "${zeichen:-}" ] || return 1
    printf '%s\n' "$zeichen" >"$WORK/anmeldezeichen"
    return 0
}

# runState aus der Admin-Seite; ihr Lesen laedt kein Modell.
laufzustand() {
    zeichen=$(cat "$WORK/anmeldezeichen" 2>/dev/null || true)
    : >"$WORK/uebersicht.json"
    if [ -n "${zeichen:-}" ]; then
        curl -sS -b "$JAR" -c "$JAR" -H 'Accept: application/json' \
            -H "requesttoken: $zeichen" -o "$WORK/uebersicht.json" \
            "$ADRESSE$UEBERSICHT" 2>/dev/null || : >"$WORK/uebersicht.json"
    fi
    zustand=$(sed -n 's/.*"runState"[[:space:]]*:[[:space:]]*"\([A-Za-z_]*\)".*/\1/p' \
        "$WORK/uebersicht.json" 2>/dev/null | head -1)
    [ -n "${zustand:-}" ] || zustand=unlesbar
    printf '%s\n' "$zustand"
}

# Die Leerlaufpruefung vor b3 und b5 (Pitfall 12). Sie setzt eine Arbeitsdatei
# statt exit: ein exit stuende in der Subshell des tee-Blocks und verliesse nur
# sie. Der Abbruch 50 steht unterhalb der Pipeline.
leerlauf_pruefen() {
    passwort_bereitlegen
    protokoll "passwort-quelle $PASSWORT_QUELLE"
    occ findling:index >"$WORK/status.txt" 2>&1 || true
    vorrat=$(vorrat_von "$WORK/status.txt")
    protokoll "leerlauf-arbeitsvorrat $vorrat"
    if [ "$PASSWORT_QUELLE" != keine ] && anmelden; then
        zustand=$(laufzustand)
    else
        zustand=unlesbar
    fi
    protokoll "leerlauf-runstate $zustand"
    if [ "$vorrat" = 0 ] && [ "$zustand" = idle ]; then
        protokoll "leerlauf ja"
        return 0
    fi
    protokoll "leerlauf nein"
    printf 'arbeitsvorrat %s runstate %s\n' "$vorrat" "$zustand" >>"$WORK/nicht-im-leerlauf"
    return 1
}

cpuset_bis() {
    if [ "$1" -eq 1 ]; then
        printf '0\n'
    else
        printf '0-%s\n' "$(($1 - 1))"
    fi
}

# Der Scan, im Wegwerf-Container desselben Digests. Die Schriftart findet der
# Generator zwei Verzeichnisse ueber sich, daher die zwei Einhaengungen unter
# einer Wurzel. Geschrieben wird als Nutzer der Box.
scan_bauen() {
    date -u +'scan-start %Y-%m-%dT%H:%M:%SZ'
    if sudo docker run --rm --network none --cpuset-cpus 0 --user "$(id -u):$(id -g)" \
        -e PYTHONDONTWRITEBYTECODE=1 \
        -e PYTHONPATH=/repo/scripts/dev \
        -v "$REPO/scripts/dev:/repo/scripts/dev:ro" \
        -v "$REPO/testdata/fonts:/repo/testdata/fonts:ro" \
        -v "$SCAN_DIR:/scan" \
        --entrypoint /app/.venv/bin/python "$IMAGE" \
        -c "import build_load_corpus as corpus; open('/scan/scan-8.pdf', 'wb').write(corpus._scan_pdf(corpus.Rng('$SCAN_SEED', 'scan-8'), 8))" \
        && [ -s "$SCAN_DIR/scan-8.pdf" ]; then
        chmod 644 "$SCAN_DIR/scan-8.pdf"
        protokoll "scan-seiten 8"
        protokoll "scan-bytes $(wc -c <"$SCAN_DIR/scan-8.pdf" | tr -d ' ')"
        protokoll "scan-sha256 $(sha256sum "$SCAN_DIR/scan-8.pdf" | cut -d' ' -f1)"
        return 0
    fi
    protokoll "scan-gebaut nein"
    printf 'scan\n' >>"$WORK/probe-ohne-zahl"
    return 1
}

# Eine Probe hat eine Zahl hergegeben, wenn ihre Endzeile da ist und keine
# Luecke traegt. Ohne diese Pruefung endete ein abgebrochener Lauf mit 0.
probe_pruefen() {
    datei=$1
    marke=$2
    wert=$(awk -v marke="$marke" '$1 == marke {print $2; exit}' "$datei" 2>/dev/null || true)
    case "${wert:-}" in
    '' | na | *[!0-9.]*)
        protokoll "probe-ohne-zahl $(basename "$datei") $marke"
        printf '%s\n' "$datei" >>"$WORK/probe-ohne-zahl"
        ;;
    *) protokoll "probe-zahl $(basename "$datei") $marke $wert" ;;
    esac
}

bench_pruefen() {
    datei=$1
    wert=$(sed -n 's/^tokens_per_second_p50=\([0-9.]*\)$/\1/p' "$datei" 2>/dev/null | head -1)
    if [ -n "${wert:-}" ]; then
        protokoll "probe-zahl $(basename "$datei") tokens_per_second_p50 $wert"
    else
        protokoll "probe-ohne-zahl $(basename "$datei") tokens_per_second_p50"
        printf '%s\n' "$datei" >>"$WORK/probe-ohne-zahl"
    fi
}

# W3, einmal. $1 Slots, $2 cpuset, $3 Zieldatei, dahinter die Speichergrenze
# als Optionen, oder nichts.
slots_fahren() {
    slots=$1
    kerne=$2
    datei=$3
    shift 3
    echo "-- W3 slots $slots auf cpuset $kerne --"
    sudo docker run --rm --network none --cpuset-cpus "$kerne" "$@" \
        -v "$REPO/scripts/ops:/ops:ro" \
        -v "$SCAN_DIR:/scan:ro" \
        --entrypoint /app/.venv/bin/python "$IMAGE" \
        /ops/ocr_slot_probe.py --slots "$slots" --rounds 3 --scan /scan/scan-8.pdf \
        >"$datei" 2>&1 || protokoll "probe-rueckgabe-ungleich-0 $(basename "$datei")"
    cat "$datei"
    probe_pruefen "$datei" pages_per_second_median
}

b3_fahren() {
    date -u +'b3-start %Y-%m-%dT%H:%M:%SZ'
    protokoll "b3-produktstart-vorher $(produktstart)"
    produktstart >"$WORK/produktstart-vorher"
    if ! leerlauf_pruefen; then
        echo "-- Das Produkt arbeitet. Gemessen wird nichts, der Lauf endet mit 50. --"
        date -u +'b3-ende %Y-%m-%dT%H:%M:%SZ'
        return 0
    fi
    if scan_bauen; then
        for slots in 1 2; do
            slots_fahren "$slots" 0,1 "$OUT/b3-slots-$slots.txt" --memory 2g --memory-swap 2g
        done
        echo "-- W3 Einzelmodus auf cpuset 0,1 --"
        sudo docker run --rm --network none --cpuset-cpus 0,1 --memory 2g --memory-swap 2g \
            -v "$REPO/scripts/ops:/ops:ro" \
            -v "$SCAN_DIR:/scan:ro" \
            --entrypoint /app/.venv/bin/python "$IMAGE" \
            /ops/ocr_slot_probe.py --mode single --rounds 3 --scan /scan/scan-8.pdf \
            >"$OUT/b3-single.txt" 2>&1 || protokoll "probe-rueckgabe-ungleich-0 b3-single.txt"
        cat "$OUT/b3-single.txt"
        probe_pruefen "$OUT/b3-single.txt" rounds
    fi
    nachher=$(produktstart)
    protokoll "b3-produktstart-nachher $nachher"
    if [ "$nachher" != "$(cat "$WORK/produktstart-vorher")" ]; then
        printf 'produktstart bewegt\n' >>"$WORK/nicht-im-leerlauf"
    fi
    date -u +'b3-ende %Y-%m-%dT%H:%M:%SZ'
}

# Eine Kombination von b5. Der Bench-Container laeuft abgesetzt unter festem
# Namen, damit rss_sampler.sh ihn beim Namen fassen kann; seine Ausgabe kommt
# danach aus docker logs, und entfernt wird er ueber genau diesen Namen.
kombination_fahren() {
    threads=$1
    batch=$2
    bank="findling-wegwerf-b5-t$threads-b$batch"
    datei="$OUT/b5-threads-$threads-batch-$batch.txt"
    reihe="$WORK/b5-t$threads-b$batch.csv"
    echo "-- embed.bench threads $threads batch $batch sequence 512 auf cpuset 0,1 --"
    sudo docker rm -f "$bank" >/dev/null 2>&1 || true
    if ! sudo docker run -d --name "$bank" --network none --cpuset-cpus 0,1 \
        --memory 2g --memory-swap 2g \
        --entrypoint python "$IMAGE" \
        -m findling.embed.bench --mode tokens-per-second \
        --batch "$batch" --sequence 512 --threads "$threads" >/dev/null; then
        protokoll "probe-ohne-zahl $(basename "$datei") start"
        printf '%s\n' "$datei" >>"$WORK/probe-ohne-zahl"
        return 0
    fi
    sudo "$SAMPLER" "$bank" "$ABTASTINTERVALL" "$reihe" >"$WORK/sampler-t$threads-b$batch.log" 2>&1 &
    abtaster=$!
    rueckgabe=$(sudo docker wait "$bank" 2>/dev/null || echo unlesbar)
    sudo kill -TERM "$abtaster" 2>/dev/null || true
    wait "$abtaster" 2>/dev/null || true
    sudo docker logs "$bank" >"$datei" 2>&1 || true
    sudo docker rm -f "$bank" >/dev/null 2>&1 || true
    cat "$datei"
    protokoll "b5-rueckgabe threads $threads batch $batch $rueckgabe"
    # Das Maximum aus den Zeilen der Reihe selbst und nicht aus der Schlusszeile
    # des Abtasters: verschwindet die cgroup mit dem Ende des Containers, bricht
    # der Abtaster ab, bevor er sie schreibt, und die Zeilen davor gelten weiter.
    maximum=$(awk -F, '$1 ~ /^findling-rss [0-9]+$/ && $2 ~ /^[0-9]+$/ {
            if ($2 > m) m = $2; n++
        } END {if (n) printf "%d %d\n", m, n; else print "unlesbar 0"}' "$reihe" 2>/dev/null ||
        echo 'unlesbar 0')
    set -- $maximum
    if [ "$1" = unlesbar ]; then
        protokoll "b5-max-anon threads $threads batch $batch unlesbar abtastungen 0"
        printf '%s\n' "$reihe" >>"$WORK/probe-ohne-zahl"
    else
        protokoll "b5-max-anon threads $threads batch $batch $1 byte $(awk -v b="$1" 'BEGIN {printf "%.1f", b / 1048576}') MB abtastungen $2"
    fi
    printf 'b5-max-anon threads %s batch %s %s\n' "$threads" "$batch" "$1" >"$OUT/b5-max-anon-threads-$threads-batch-$batch.txt"
    bench_pruefen "$datei"
}

b5_fahren() {
    date -u +'b5-start %Y-%m-%dT%H:%M:%SZ'
    protokoll "b5-produktstart-vorher $(produktstart)"
    produktstart >"$WORK/produktstart-vorher"
    if ! leerlauf_pruefen; then
        echo "-- Das Produkt arbeitet. Gemessen wird nichts, der Lauf endet mit 50. --"
        date -u +'b5-ende %Y-%m-%dT%H:%M:%SZ'
        return 0
    fi
    protokoll "b5-abtaster $SAMPLER, unveraendert gerufen, intervall $ABTASTINTERVALL s"
    for threads in 1 2; do
        for batch in 2 8; do
            kombination_fahren "$threads" "$batch"
        done
    done
    nachher=$(produktstart)
    protokoll "b5-produktstart-nachher $nachher"
    if [ "$nachher" != "$(cat "$WORK/produktstart-vorher")" ]; then
        printf 'produktstart bewegt\n' >>"$WORK/nicht-im-leerlauf"
    fi
    date -u +'b5-ende %Y-%m-%dT%H:%M:%SZ'
}

b4_fahren() {
    date -u +'b4-start %Y-%m-%dT%H:%M:%SZ'
    # Ohne Produkt: steht irgendein Container, misst die Kurve ihn mit.
    laufend=$(sudo docker ps -q 2>/dev/null | wc -l | tr -d ' ')
    protokoll "b4-laufende-container $laufend"
    if [ "$laufend" != 0 ]; then
        echo "-- Neben dem Wegwerf-Container laeuft etwas. Gemessen wird nichts, der Lauf endet mit 51. --"
        printf 'laufende container %s\n' "$laufend" >>"$WORK/b4-nicht-frei"
        date -u +'b4-ende %Y-%m-%dT%H:%M:%SZ'
        return 0
    fi
    kerne=$(nproc)
    protokoll "b4-kerne $kerne"
    protokoll "b4-arch $(uname -m)"
    protokoll "b4-kernel-mem $(tr ' ' '\n' </proc/cmdline | awk -F= '$1 == "mem" {print $2; f = 1} END {if (!f) print "ungesetzt"}')"
    protokoll "b4-grenze keine"
    slots_liste=''
    for slots in $B4_SLOTS; do
        if [ "$slots" -le "$kerne" ]; then
            slots_liste="$slots_liste $slots"
        fi
    done
    threads_liste=''
    for threads in $B4_THREADS; do
        if [ "$threads" -le "$kerne" ]; then
            threads_liste="$threads_liste $threads"
        fi
    done
    if [ "$slots_liste" != " $B4_SLOTS" ]; then
        protokoll "b4-gekuerzt-auf $kerne"
    fi
    protokoll "b4-slots$slots_liste"
    protokoll "b4-threads$threads_liste"
    if scan_bauen; then
        for slots in $slots_liste; do
            slots_fahren "$slots" "$(cpuset_bis "$slots")" "$OUT/b4-slots-$slots.txt"
        done
    fi
    for threads in $threads_liste; do
        kerne_t=$(cpuset_bis "$threads")
        echo "-- embed.bench threads $threads batch 2 sequence 512 auf cpuset $kerne_t --"
        sudo docker run --rm --network none --cpuset-cpus "$kerne_t" \
            --entrypoint python "$IMAGE" \
            -m findling.embed.bench --mode tokens-per-second \
            --batch 2 --sequence 512 --threads "$threads" \
            >"$OUT/b4-bench-$threads.txt" 2>&1 || protokoll "probe-rueckgabe-ungleich-0 b4-bench-$threads.txt"
        cat "$OUT/b4-bench-$threads.txt"
        bench_pruefen "$OUT/b4-bench-$threads.txt"
    done
    date -u +'b4-ende %Y-%m-%dT%H:%M:%SZ'
}

{
    date -u +"wegwerf-$BLOCK-start %Y-%m-%dT%H:%M:%SZ"
    protokoll "wegwerf-block $BLOCK"
    protokoll "abbild-digest $ABBILD_DIGEST"
    protokoll "box-arch $(uname -m) kerne $(nproc)"
    case "$BLOCK" in
    b3) b3_fahren ;;
    b5) b5_fahren ;;
    b4) b4_fahren ;;
    esac
    echo "=== Der Protokollblock, als Block zitierbar ==="
    cat "$WORK/protokollblock"
    date -u +"wegwerf-$BLOCK-ende %Y-%m-%dT%H:%M:%SZ"
    : >"$WORK/block-durchgelaufen"
} 2>&1 | tee "$ZIEL"

# Unterhalb der Pipeline, und nur hier: der Rueckgabewert einer Pipeline, die in
# tee endet, gehoert zu tee. Gelesen wird aus den Arbeitsdateien unter WORK.
if [ -f "$WORK/nicht-im-leerlauf" ]; then
    echo "00-wegwerf: das Produkt war vor oder waehrend $BLOCK nicht im Leerlauf" >&2
    cat "$WORK/nicht-im-leerlauf" >&2
    exit 50
fi
if [ -f "$WORK/b4-nicht-frei" ]; then
    echo "00-wegwerf: neben b4 lief ein Container; AIO vorher stoppen (Pitfall 8)" >&2
    cat "$WORK/b4-nicht-frei" >&2
    exit 51
fi
if [ -f "$WORK/probe-ohne-zahl" ]; then
    echo "00-wegwerf: eine Probe von $BLOCK hat keine Zahl hergegeben" >&2
    cat "$WORK/probe-ohne-zahl" >&2
    if [ "$BLOCK" = b4 ]; then
        exit 51
    fi
    exit 50
fi
# Fail closed: ohne die Endmarke ist der Block irgendwo abgebrochen, und ohne
# diese Zeile endete das Werkzeug dann mit 0 (Klasse L-03, deferred-items 22-02).
if [ ! -f "$WORK/block-durchgelaufen" ]; then
    echo "00-wegwerf: der Block $BLOCK ist nicht bis zu seinem Ende gelaufen" >&2
    if [ "$BLOCK" = b4 ]; then
        exit 51
    fi
    exit 50
fi

case "$BLOCK" in
b3) echo "B3-FERTIG" | tee -a "$ZIEL" ;;
b5) echo "B5-FERTIG" | tee -a "$ZIEL" ;;
b4) echo "B4-FERTIG" | tee -a "$ZIEL" ;;
esac
