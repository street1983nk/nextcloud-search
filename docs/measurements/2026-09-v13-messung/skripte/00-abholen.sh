#!/bin/sh
# Das periodische Abholen der Rohdaten der v1.3-Anfahrt, auf der
# ENTWICKLUNGSMASCHINE, nie auf der Box.
#
# **DIESE FASSUNG IST NICHT GEFAHREN.** Keine Rohdatei liegt neben ihr.
#
# Warum es dieses Skript gibt. 00-lauf.sh haelt den Deckel mit einem harten
# Stopp (D-02): die Box faehrt herunter, sobald die Zeit um ist, und was bis
# dahin nur auf der Box lag, ist mit ihr fuer diese Anfahrt verloren. Dieses
# Skript holt deshalb alle ABHOLTAKT Sekunden (Vorgabe 600) das
# Rohdatenverzeichnis des Box-Klons per scp in das gleichnamige Verzeichnis
# dieses Checkouts und setzt danach per ssh die Abholmarke ~/work/abgeholt auf
# der Box. 00-lauf.sh wartet vor seiner Selbstabschaltung auf eine Marke, die
# juenger ist als 00-FERTIG (bzw. B4-FERTIG); bei einem harten Stopp fehlt
# hoechstens ein Takt.
#
# Was dieses Skript nicht tut: es committet nichts und pusht nichts. Die
# Rohdaten laufen vor ihrem Commit durch das Gate der oeffentlichen Artefakte
# (T-22-20, Plan 22-08 und 22-09); ein Werkzeug, das von selbst committet,
# naehme diesen Schritt weg. Es startet und stoppt auch keine Box.
#
# Wann es endet:
#
#   0  00-FERTIG liegt lokal und B4 ist nicht geplant, nicht vorbereitet oder
#      gestrichen; oder B4-FERTIG liegt lokal
#   1  drei Fehlversuche in Folge (FEHLVERSUCHE_MAX): die Box ist gestoppt
#      oder nicht erreichbar. Nach dem harten Stopp ist das das erwartete Ende.
#   2  Aufruf ohne BOX_ADRESSE, ohne lesbaren Schluessel oder mit einem
#      B4_GEPLANT, das nicht ja oder nein ist
#
# Nach dem Typwechsel fuer B4 hat die Box eine neue Adresse (00-typwechsel.sh
# hin nennt sie auf dem Terminal). Dieses Skript wird dann mit der neuen
# BOX_ADRESSE neu gestartet; bis dahin enden seine Versuche mit 1.
#
# Schluessel und known_hosts liegen im Zustandsverzeichnis von aws_box.sh
# (FINDLING_LOADTEST_DIR), ausserhalb des Repos; das Protokoll dieses Skripts
# ebenfalls (v13-abholen.log), weil es die Adresse der Box traegt.
set -eu

# Git for Windows schreibt unixartige Argumente um; das Muster von aws_box.sh.
MSYS_NO_PATHCONV=1
MSYS2_ARG_CONV_EXCL='*'
export MSYS_NO_PATHCONV MSYS2_ARG_CONV_EXCL

SKRIPTE=$(cd "$(dirname "$0")" && pwd)
LAUF=$(cd "$SKRIPTE/.." && pwd)
RELATIV="docs/measurements/2026-09-v13-messung/rohdaten"
STATE_DIR="${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}"
SCHLUESSEL="${SCHLUESSEL:-$STATE_DIR/findling-loadtest}"
BEKANNT="${BEKANNT:-$STATE_DIR/known_hosts}"
BOX_NUTZER="${BOX_NUTZER:-ubuntu}"
# Der Klon auf der Box, Runbook Abschnitt 4 (Wiederaufbau der Messbox).
BOXREPO="${BOXREPO:-/home/ubuntu/work/nextcloud-search}"
LOKAL="${LOKAL:-$LAUF/rohdaten}"
ABHOLTAKT="${ABHOLTAKT:-600}"
FEHLVERSUCHE_MAX="${FEHLVERSUCHE_MAX:-3}"
B4_GEPLANT="${B4_GEPLANT:-nein}"
LOG="${LOG:-$STATE_DIR/v13-abholen.log}"
SCP="${SCP:-scp}"
SSH="${SSH:-ssh}"

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: BOX_ADRESSE=<adresse> [B4_GEPLANT=ja|nein] ./00-abholen.sh

Laeuft auf der Entwicklungsmaschine. Holt alle ABHOLTAKT Sekunden (Vorgabe 600)
das Rohdatenverzeichnis der v1.3-Anfahrt von der Box und setzt danach die
Abholmarke ~/work/abgeholt. Schluessel und known_hosts aus FINDLING_LOADTEST_DIR
(Vorgabe $HOME/.findling-loadtest). Kein Commit, kein Push.
HINWEIS
}

if [ -z "${BOX_ADRESSE:-}" ]; then
    echo "00-abholen: BOX_ADRESSE fehlt" >&2
    benutzung
    exit 2
fi
if [ ! -r "$SCHLUESSEL" ]; then
    echo "00-abholen: der Schluessel in FINDLING_LOADTEST_DIR ist nicht lesbar" >&2
    benutzung
    exit 2
fi
case "$B4_GEPLANT" in
ja | nein) ;;
*)
    echo "00-abholen: B4_GEPLANT muss ja oder nein sein" >&2
    benutzung
    exit 2
    ;;
esac
case "$ABHOLTAKT$FEHLVERSUCHE_MAX" in
*[!0-9]*)
    echo "00-abholen: ABHOLTAKT und FEHLVERSUCHE_MAX sind ganze Zahlen" >&2
    benutzung
    exit 2
    ;;
esac

mkdir -p "$STATE_DIR" "$LOKAL"

utc() {
    date -u +%Y-%m-%dT%H:%M:%SZ
}

protokoll() {
    printf '%s\n' "$*" >>"$LOG"
    printf '%s\n' "$*"
}

# Das Ende: 00-FERTIG ohne B4, oder B4-FERTIG. Traegt 00-FERTIG den Zustand
# "b4 vorbereitet", wartet dieses Skript auf B4-FERTIG, auch wenn B4_GEPLANT
# hier ja ist; "gestrichen" und "nicht-geplant" beenden es.
ende_erreicht() {
    if [ -f "$LOKAL/B4-FERTIG" ]; then
        return 0
    fi
    [ -f "$LOKAL/00-FERTIG" ] || return 1
    if grep -q ' b4 vorbereitet' "$LOKAL/00-FERTIG" 2>/dev/null; then
        return 1
    fi
    if [ "$B4_GEPLANT" = ja ] && ! grep -Eq ' b4 (gestrichen|nicht-geplant)' "$LOKAL/00-FERTIG" 2>/dev/null; then
        return 1
    fi
    return 0
}

fehl=0
protokoll "abholen-start $(utc) takt $ABHOLTAKT b4-geplant $B4_GEPLANT"
while :; do
    stufe=$(mktemp -d)
    if "$SCP" -q -r -i "$SCHLUESSEL" \
        -o UserKnownHostsFile="$BEKANNT" -o StrictHostKeyChecking=yes \
        -o BatchMode=yes -o ConnectTimeout=20 \
        "$BOX_NUTZER@$BOX_ADRESSE:$BOXREPO/$RELATIV" "$stufe/" && [ -d "$stufe/rohdaten" ]; then
        cp -R "$stufe/rohdaten/." "$LOKAL/"
        dateien=$(find "$LOKAL" -type f | wc -l | tr -d ' ')
        marke=gesetzt
        "$SSH" -i "$SCHLUESSEL" \
            -o UserKnownHostsFile="$BEKANNT" -o StrictHostKeyChecking=yes \
            -o BatchMode=yes -o ConnectTimeout=20 \
            "$BOX_NUTZER@$BOX_ADRESSE" 'date +%s > ~/work/abgeholt' || marke=fehlgeschlagen
        protokoll "abgeholt $(utc) dateien $dateien marke $marke"
        fehl=0
    else
        fehl=$((fehl + 1))
        protokoll "fehlversuch $(utc) nummer $fehl von $FEHLVERSUCHE_MAX"
    fi
    rm -rf "$stufe"
    if [ "$fehl" -ge "$FEHLVERSUCHE_MAX" ]; then
        protokoll "abholen-ende $(utc) box-nicht-erreichbar"
        exit 1
    fi
    if ende_erreicht; then
        protokoll "abholen-ende $(utc) fertig"
        exit 0
    fi
    sleep "$ABHOLTAKT"
done
