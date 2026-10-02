#!/bin/sh
# Der Nullstand einer Zelle der Abnahme-Anfahrt, gelesen und NICHT angestossen.
#
# **DIESE FASSUNG IST NICHT GEFAHREN.** Keine Rohdatei liegt neben ihr; was sie
# auf der Box liest, liest sie auf der Anfahrt.
#
# Die Ableitung von docs/measurements/2026-09-v12-messung/skripte/93-nullstand.sh,
# und der eine Unterschied ist der Grund fuer ihre Existenz: 93-nullstand.sh
# stoesst nach den vier Quellen den Neuaufbau an (findling:index --restart -n)
# und wartet 360 s auf einen Vorrat. In einer Zelle der Phase 28 darf der Vorrat
# erst NACH der Probe und dem Wirksamkeitstor gefuellt werden (Pitfall 2 der
# Research): sonst indexiert der frische Container minutenlang im Profil der
# Vorzelle, bevor die Probe ueberhaupt laeuft, und die Zelle misst zwei Stufen.
# Den Trigger setzt 10-zelle.sh selbst, unmittelbar nach dem Start der Sampler.
# 93-nullstand.sh bleibt als gefahrene Fassung unveraendert.
#
# Was gleich bleibt: die vier Quellen und ihre Zeilen. 1. der Inhalt des
# Volumens (state.db, vectors.db, das tantivy-Verzeichnis), 2. die Endzustaende
# der Nextcloud ueber occ, 3. die Marken in meta und die Dateien je Zustand,
# nur wenn es eine state.db gibt, 4. der Arbeitsvorrat der PHP-Haelfte.
#
# Das Urteil. Leer ist das Volumen, wenn es keine state.db gibt oder die
# state.db keine einzige Datei fuehrt; der Container legt eine leere state.db
# bei seinem ersten Durchgang an, und die ist ein Nullstand. Fuehrt sie Dateien,
# hat --rm-data nicht gegriffen, und die Zelle endet. Quelle 4 (der
# Arbeitsvorrat der PHP-Haelfte) wird weiter gelesen und als "arbeitsvorrat N"
# protokolliert, aber hier nicht mehr beurteilt: Lauf 4 zeigte, dass der frisch
# bewaffnete Container den Vorrat binnen 6-16 s selbst ueber die Top-up-Route
# fuellt (POST /queues/documents/topup -> CrawlAdvanceService), ein Urteil an
# dieser Position straefte also unschaedliche Frischbefuellung. Das
# Altbestand-Urteil faellt 10-zelle.sh am Schritt vorrat-tor VOR der
# Bewaffnung.
#
# Rueckgabewerte:
#
#   0   volumen-leer ja
#   11  volumen-leer nein: die state.db fuehrt Dateien
#   12  die state.db ist da und nicht lesbar
#
# ASCII, weil die Box ihr Gebietsschema nicht garantiert.
set -eu

SKRIPTE=$(cd "$(dirname "$0")" && pwd)
OUT="${OUT:-$SKRIPTE/../rohdaten}"
DATA_ROOT="${DATA_ROOT:-/mnt/findling}"
VOLUME="${VOLUME:-$DATA_ROOT/docker/volumes/nc_app_findling_backend_data/_data}"
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"

mkdir -p "$OUT"
ZIEL="$OUT/93b-nullstand.txt"
WORK=$(mktemp -d)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT

occ() {
    sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
}

vorrat_von() {
    awk '/^Work stock/ {found = 1; next}
         found && /^  (scheduled|handed to the worker)/ {sum += $NF}
         END {print sum + 0}' "$1"
}

{
    date -u +'nullstand-start %Y-%m-%dT%H:%M:%SZ'
    echo "volumen: <volumen des backends>"
    printf 'container %s\n' "$CONTAINER"

    echo "=== Quelle 1: der Inhalt des Volumens ==="
    for datei in state.db vectors.db; do
        if sudo test -f "$VOLUME/$datei"; then
            printf '%s vorhanden, groesse in byte: %s\n' "$datei" "$(sudo wc -c <"$VOLUME/$datei" | tr -d ' ')"
        else
            printf '%s fehlt\n' "$datei"
        fi
    done
    if sudo test -d "$VOLUME/index"; then
        printf 'tantivy-verzeichnis vorhanden, dateien: %s\n' "$(sudo find "$VOLUME/index" -type f | wc -l | tr -d ' ')"
    else
        echo "tantivy-verzeichnis fehlt"
    fi

    echo "=== Quelle 2 und 4: Endzustaende und Arbeitsvorrat, ueber occ ==="
    occ findling:index >"$WORK/status.txt" 2>&1 || true
    cat "$WORK/status.txt"
    vorrat=$(vorrat_von "$WORK/status.txt")
    printf 'arbeitsvorrat %s\n' "$vorrat"

    echo "=== Quelle 3: Marken und Dateien je Zustand, nur mit state.db ==="
    if sudo test -f "$VOLUME/state.db"; then
        if sudo python3 - "$VOLUME/state.db" >"$WORK/speicher.txt" 2>&1 <<'PY'; then
import sqlite3
import sys

connection = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
try:
    for key, value in connection.execute("select key, value from meta order by key"):
        print(f"  {key} = {value}")
except sqlite3.OperationalError:
    print("  meta fehlt")
try:
    rows = connection.execute(
        "select state, count(*) from files where deleted_at is null group by state order by state"
    ).fetchall()
except sqlite3.OperationalError:
    rows = []
print("  dateien je zustand:", rows)
print("dateien-im-speicher", sum(count for _, count in rows))
PY
            cat "$WORK/speicher.txt"
            awk '$1 == "dateien-im-speicher" {print $2; exit}' "$WORK/speicher.txt" >"$WORK/dateien"
        else
            cat "$WORK/speicher.txt"
            echo "state.db-lesbar nein"
            : >"$WORK/unlesbar"
        fi
    else
        echo "keine state.db im Volumen, also keine Marken zu lesen"
        echo 0 >"$WORK/dateien"
    fi

    if [ -f "$WORK/unlesbar" ]; then
        echo "volumen-leer unlesbar"
    elif [ "$(cat "$WORK/dateien" 2>/dev/null || echo x)" = 0 ]; then
        echo "volumen-leer ja"
    else
        echo "volumen-leer nein"
        : >"$WORK/nicht-leer"
    fi
    date -u +'nullstand-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Unterhalb der Pipeline, weil der Rueckgabewert einer Pipeline, die in tee
# endet, zu tee gehoert.
if [ -f "$WORK/unlesbar" ]; then
    echo "93b-nullstand: die state.db ist da und nicht lesbar" >&2
    exit 12
fi
if [ -f "$WORK/nicht-leer" ]; then
    echo "93b-nullstand: die state.db fuehrt Dateien, --rm-data hat nicht gegriffen" >&2
    exit 11
fi
echo "93B-NULLSTAND-FERTIG"
