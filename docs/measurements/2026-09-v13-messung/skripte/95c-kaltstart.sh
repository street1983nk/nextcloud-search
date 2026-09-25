#!/bin/sh
# Die Kaltstartlatenz des v1.3-Laufs, MESS-07 Punkt 5.
#
# NACHFOLGEFASSUNG von
# docs/measurements/2026-09-v12-messung/skripte/95b-wiederaufwaermen.sh.
# 95b ist gefahren, pruefsummengeschuetzt und bleibt unberuehrt.
#
# DIESE FASSUNG IST NICHT GEFAHREN. Neben ihr liegt keine Rohdatei; was sie auf
# der Box misst, misst die v1.3-Anfahrt.
#
# **Der Befund, der diese Datei noetig macht.** Keiner der beiden v1.2-Versuche
# hat eine gueltige Kaltstartzahl geliefert. 95-spitze.sh hat mit einem Begriff
# gemessen, der nichts findet (EmptyResultGroup), und eine leere Antwort ist
# schneller als jede Suche, die wirklich rechnet. 95b Auspraegung 3 hat mit
# "Bescheid Antrag" gemessen und in der ersten kalten Suche 0 Treffer bekommen,
# wo derselbe Begriff sonst 26 liefert ("transient 0"). Beide Zahlen sind die
# Latenz einer Antwort, die keine war.
#
# **Die eine Aenderung gegen 95b.** Treffer groesser 0 in der ersten kalten
# Suche ist Pflicht. Faellt sie leer aus, gilt der ganze Kaltzyklus als
# ungueltig, und er wird GANZ wiederholt: Neustart, sync, drop_caches, erste
# Suche. Nie wird eine leere Antwort herausgerechnet oder durch eine zweite,
# schon warme Suche ersetzt. Hoechstens KALTZYKLEN_MAX Zyklen, Vorgabe 3; ist
# danach keiner gueltig, endet das Werkzeug mit 48.
#
# **Was ausdruecklich gleich bleibt.** Die Nutzerroute
# /ocs/v2.php/search/providers/findling/search und nur sie, derselbe
# zweiwortige Begriff als Vorgabe, das Leeren des Seitencaches auf dem WIRT
# (sync und drop_caches verwerfen auch den mmap-Cache des Tantivy-Index, die
# Messung ist in beiden Haelften kalt), die Admin-Seite als Bereitschaftsprobe,
# weil eine Suche als Probe die erste Suche waere und damit die gemessene Zahl.
# Vor der Messung wird keine andere Route gefragt, die ein Modell laedt; der
# Abbruch 30 aus Abschnitt 7.2 des Runbooks entfaellt damit, weil der Fall
# nicht mehr entstehen kann. Steht vor der Suche trotzdem loaded, ist der
# Zyklus ungueltig und wird wiederholt.
#
# **Das Zeitfenster.** Beim Betreten und Verlassen des Blocks steht ein
# UTC-Zeitstempel, und am Ende die Zeile kaltstart-fenster <von> <bis>. Daraus
# liest 91m-langsame-aufrufe.py die M-01-Zeilen dieses Fensters.
#
# **Woher das Passwort kommt.** Zuerst aus der Umgebungsvariablen, deren NAMEN
# PASSWORT_ENV traegt, sonst aus der Datei, auf die PWFILE zeigt; nie von einer
# Kommandozeile (T-22-11).
#
# Die Exit-Codes:
#
#   2  das Werkzeug wurde mit einem Argument gerufen, oder KALTZYKLEN_MAX liegt
#      nicht zwischen 1 und 3
#   48 kein gueltiger Kaltzyklus: nach KALTZYKLEN_MAX Zyklen hat keine erste
#      kalte Suche Treffer geliefert, es gab kein Passwort, oder der Block ist
#      nicht bis zu seinem Ende gelaufen
set -eu

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: 95c-kaltstart.sh

Ohne Argument. Neustart, sync, drop_caches auf dem Wirt, dann die erste Suche
gegen die Nutzerroute. Treffer groesser 0 ist Pflicht; sonst wird der ganze
Kaltzyklus wiederholt, hoechstens KALTZYKLEN_MAX mal (1 bis 3, Vorgabe 3).
HINWEIS
}

if [ "$#" -ne 0 ]; then
    benutzung
    exit 2
fi

# Hoechstens drei Kaltzyklen. Eine hoehere Zahl waere keine Stellschraube mehr,
# sondern die Suche nach einem Zyklus, der zufaellig passt.
KALTZYKLEN_MAX="${KALTZYKLEN_MAX:-3}"
case "$KALTZYKLEN_MAX" in
1 | 2 | 3) ;;
*)
    benutzung
    exit 2
    ;;
esac

SKRIPTE=$(cd "$(dirname "$0")" && pwd)
OUT="${OUT:-$SKRIPTE/../rohdaten}"
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
ADRESSE="${ADRESSE:-https://loadtest.infranode.dev}"
BENUTZER="${BENUTZER:-admin}"
PASSWORT_ENV="${PASSWORT_ENV:-FINDLING_ADMIN_PASSWORD}"
PWFILE="${PWFILE:-$HOME/work/.pw/admin}"
UEBERSICHT="${UEBERSICHT:-/apps/findling/admin/overview}"
# Zwei Woerter, weil eine einwortige Zeile allein aus dem Wortindex beantwortet
# wird (Plan 06.1-20). In 95b lieferte dieser Begriff warm 26 Treffer.
BEGRIFF="${BEGRIFF:-Bescheid Antrag}"
LIMIT="${LIMIT:-100}"
BEREIT_DECKEL="${BEREIT_DECKEL:-180}"

mkdir -p "$OUT"
ZIEL="${ZIEL:-$OUT/95c-kaltstart.txt}"
WORK=$(mktemp -d)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT

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
CURLRC="$WORK/curlrc"
: >"$CURLRC"
chmod 600 "$CURLRC"
{
    printf 'user = "%s:' "$BENUTZER"
    cat "$PWFELD"
    printf '"\n'
} >"$CURLRC"
JAR="$WORK/cookies.txt"

if command -v jq >/dev/null 2>&1; then
    JQ=ja
    ZAEHLQUELLE=jq
else
    JQ=nein
    ZAEHLQUELLE=muster
fi

scope_von() {
    cid=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER" 2>/dev/null || true)
    [ -n "${cid:-}" ] || return 1
    printf '/sys/fs/cgroup/system.slice/docker-%s.scope\n' "$cid"
}

cgroup_wert() {
    pfad=$(scope_von) || {
        printf 'unlesbar\n'
        return 0
    }
    sudo cat "$pfad/$1" 2>/dev/null || printf 'unlesbar\n'
}

protokoll() {
    printf '%s\n' "$*" >>"$WORK/protokollblock"
    printf '%s\n' "$*"
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
    printf '%s\n' "$zeichen" >"$WORK/token"
    return 0
}

# Genau ein Feld der Admin-Seite; ihr Lesen laedt kein Modell.
engine_zustand() {
    zeichen=$(cat "$WORK/token" 2>/dev/null || true)
    if [ -z "${zeichen:-}" ]; then
        printf 'unbekannt\n'
        return 0
    fi
    antwort=$(curl -sS -b "$JAR" -c "$JAR" -H 'Accept: application/json' \
        -H "requesttoken: $zeichen" "$ADRESSE$UEBERSICHT" 2>/dev/null || true)
    zustand=$(printf '%s' "${antwort:-}" |
        sed -n 's/.*"engineState"[[:space:]]*:[[:space:]]*"\([A-Za-z_]*\)".*/\1/p' | head -1)
    [ -n "${zustand:-}" ] || zustand=unbekannt
    printf '%s\n' "$zustand"
}

bereit_warten() {
    versuch=0
    while [ "$versuch" -lt "$BEREIT_DECKEL" ]; do
        versuch=$((versuch + 1))
        zustand=$(engine_zustand)
        if [ "$zustand" != unbekannt ]; then
            printf 'bereit-nach-s %s zustand %s\n' "$versuch" "$zustand"
            return 0
        fi
        sleep 1
    done
    printf 'bereit-nach-s ueber-deckel-%s\n' "$BEREIT_DECKEL"
    return 1
}

treffer_in() {
    if [ "$JQ" = ja ]; then
        jq -r '.ocs.data.entries | length' "$1" 2>/dev/null || printf 'unklar\n'
    else
        grep -o '"resourceUrl"' "$1" 2>/dev/null | wc -l | tr -d ' '
    fi
}

# Eine Suche gegen die NUTZERROUTE, und nur gegen sie. Die drei Zahlen landen in
# Arbeitsdateien.
suche() {
    antwort=$(curl -sS -G -K "$CURLRC" \
        -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
        --data-urlencode "term=$1" --data-urlencode "limit=$LIMIT" \
        -o "$WORK/$2.json" -w '%{time_total} %{http_code}' \
        "$ADRESSE/ocs/v2.php/search/providers/findling/search" 2>/dev/null || printf '0 000')
    printf '%s\n' "$antwort" | awk '{printf "%d\n", ($1 * 1000) + 0.5}' >"$WORK/$2.ms"
    printf '%s\n' "$antwort" | awk '{print $2}' >"$WORK/$2.code"
    treffer_in "$WORK/$2.json" >"$WORK/$2.treffer"
}

lies() {
    cat "$WORK/$1" 2>/dev/null || printf 'unklar\n'
}

{
    VON=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    printf 'kaltstart-start %s\n' "$VON"
    printf 'begriff %s, deckel der antwortliste %s, trefferzaehlung-quelle %s, kaltzyklen hoechstens %s\n' \
        "$BEGRIFF" "$LIMIT" "$ZAEHLQUELLE" "$KALTZYKLEN_MAX"

    echo "=== 1. Die Pflichtzeilen, VOR der Messung ==="
    protokoll "passwort-quelle $PASSWORT_QUELLE"
    if sudo docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$CONTAINER" \
        >"$WORK/umgebung" 2>/dev/null; then
        SCHALTER=$(awk -F= '/^FINDLING_EMBED_IDLE_RELEASE_SECONDS=/ {print $2; exit}' "$WORK/umgebung")
        protokoll "entladeschalter-ist ${SCHALTER:-0}"
    else
        protokoll "entladeschalter-ist unlesbar"
    fi
    protokoll "speichergrenze-ist $(cgroup_wert memory.max)/$(cgroup_wert memory.swap.max)"

    GUELTIG=nein
    if [ "$PASSWORT_QUELLE" = keine ]; then
        echo "-- Ohne Passwort antwortete jede Suche mit 401 und 0 Treffern. Gemessen wird"
        echo "   nichts, und der Lauf endet unterhalb der Pipeline. --"
        : >"$WORK/kein-passwort"
    else
        zyklus=0
        while [ "$zyklus" -lt "$KALTZYKLEN_MAX" ]; do
            zyklus=$((zyklus + 1))
            echo "=== Kaltzyklus $zyklus von hoechstens $KALTZYKLEN_MAX ==="
            sudo docker restart "$CONTAINER" >/dev/null
            protokoll "kaltzyklus $zyklus containerstart $(sudo docker inspect --format '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || echo unlesbar)"
            if anmelden; then
                echo "anmeldung ok"
            else
                echo "anmeldung fehlgeschlagen, engineState bleibt unbekannt"
            fi
            bereit_warten || echo "-- Bereitschaftsdeckel gerissen, gemessen wird trotzdem --"
            echo "-- Der Seitencache des Wirts, geleert. Die Messung ist in beiden Haelften kalt --"
            sync
            echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null
            free -h
            zustand=$(engine_zustand)
            protokoll "kaltzyklus $zyklus engine-zustand-vor-suche $zustand"
            if [ "$zustand" = loaded ]; then
                protokoll "kaltzyklus $zyklus ungueltig aufgewaermt"
                continue
            fi
            suche "$BEGRIFF" "kalt-$zyklus"
            ms=$(lies "kalt-$zyklus.ms")
            code=$(lies "kalt-$zyklus.code")
            treffer=$(lies "kalt-$zyklus.treffer")
            protokoll "kaltzyklus $zyklus ms $ms code $code treffer $treffer"
            case "$treffer" in
            '' | *[!0-9]*) ;;
            *)
                if [ "$treffer" -gt 0 ]; then
                    GUELTIG=ja
                    protokoll "kaltstart-ms $ms"
                    suche "$BEGRIFF" warm
                    protokoll "warmsuche ms $(lies warm.ms) code $(lies warm.code) treffer $(lies warm.treffer)"
                    break
                fi
                ;;
            esac
            protokoll "kaltzyklus $zyklus ungueltig keine-treffer"
        done
        protokoll "kaltzyklen-gefahren $zyklus"
    fi
    protokoll "kaltstart-gueltig $GUELTIG"
    if [ "$GUELTIG" != ja ]; then
        : >"$WORK/kaltstart-ungueltig"
    fi

    BIS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    protokoll "kaltstart-fenster $VON $BIS"
    echo "=== Der Protokollblock, als Block zitierbar ==="
    cat "$WORK/protokollblock"
    printf 'kaltstart-ende %s\n' "$BIS"
    : >"$WORK/block-durchgelaufen"
} 2>&1 | tee "$ZIEL"

# Unterhalb der Pipeline, und nur hier: der Rueckgabewert einer Pipeline, die in
# tee endet, gehoert zu tee.
if [ -f "$WORK/kein-passwort" ]; then
    echo "95c-kaltstart: kein Passwort in $PASSWORT_ENV und keines in PWFILE" >&2
    exit 48
fi
if [ -f "$WORK/kaltstart-ungueltig" ]; then
    echo "95c-kaltstart: nach $KALTZYKLEN_MAX Kaltzyklen hat keine erste kalte Suche Treffer geliefert" >&2
    echo "95c-kaltstart: eine leere Antwort ist keine Kaltstartzahl und wird nicht herausgerechnet" >&2
    exit 48
fi
# Fail closed: ohne die Endmarke ist der Block irgendwo abgebrochen.
if [ ! -f "$WORK/block-durchgelaufen" ]; then
    echo "95c-kaltstart: der Block ist nicht bis zu seinem Ende gelaufen" >&2
    exit 48
fi

echo "95C-KALTSTART-FERTIG"
