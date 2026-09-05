#!/bin/sh
# Meldet per ntfy, wenn der Semantiklauf fertig ist, und warnt am Deckel.
#
# Reines Mitlesen: dieser Waechter fasst keinen Prozess an und entscheidet
# nichts. Den Abschluss erkennt er an der Datei, die der Waechter des Laufs erst
# NACH dem OOM-Beweis schreibt.
#
# Der Unterschied zu volllauf_watch.sh aus Plan 05-21: dort wurde gesendet und
# nicht hingesehen. Hier wird der HTTP-Code jedes Sendeversuchs protokolliert,
# denn beim Scharfstellen dieses Laufs hat das Ziel mit 403 geantwortet, obwohl
# es am 04.09. noch angenommen hat. Eine Meldekette, die still nicht meldet, ist
# schlimmer als keine, weil man sich auf sie verlaesst. Zusaetzlich schreibt
# dieser Waechter eine Weckdatei, und die ist der eigentliche Vertrag: sie liegt
# im Dateisystem und haengt an keinem fremden Dienst.
LAUF=/home/ubuntu/work/semantiklauf
BEWEIS=$LAUF/07-oom-beweis.txt
FERTIG=$LAUF/00-FERTIG
LOG=$LAUF/99-ntfy-watch.log
TOPIC=https://ntfy.infranode.dev/infranode-alerts-f43ceefc1193
DECKEL=$((20 * 3600))
MAX=$((34 * 3600))
START=$(date +%s)
gewarnt=0

say() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" >>"$LOG"; }

stand() {
    tail -1 "$LAUF/semantiklauf.csv" 2>/dev/null | cut -d, -f2 |
        awk '{printf "%.0f MB anon", $1/1048576}'
}

sende() {
    code=$(curl -s -o /dev/null -w '%{http_code}' -H "Title: $1" -H "Priority: $3" \
        -d "$2" "$TOPIC" 2>/dev/null || echo 000)
    say "ntfy gesendet, http=$code, titel=$1"
}

say "ntfy-watch scharf, prueft alle 300 s, Deckel 20 h"
sende "Findling 06-11 Semantiklauf gestartet" \
    "Der Volllauf mit Semantik laeuft. Meldung folgt beim Abschluss." "default"

while :; do
    verstrichen=$(($(date +%s) - START))
    if [ -f "$BEWEIS" ]; then
        std=$(awk -v s="$verstrichen" 'BEGIN{printf "%.1f", s/3600}')
        {
            date -u +'semantiklauf-fertig %Y-%m-%dT%H:%M:%SZ'
            echo "stunden=$std"
            echo "weckwort: semantiklauf pruefen"
        } >"$FERTIG"
        sende "Findling 06-11 Semantiklauf fertig" \
            "Beide Spuren sind durch, nach ${std} h. Der OOM-Beweis ist erhoben. Naechster Schritt: Agent mit 'semantiklauf pruefen' wecken." \
            "default"
        say "FERTIG nach ${std}h, Weckdatei geschrieben"
        exit 0
    fi
    if [ "$verstrichen" -gt "$DECKEL" ] && [ "$gewarnt" -eq 0 ]; then
        sende "Findling 06-11 ueber 20 h" \
            "Der Deckel von 20 h ist ueberschritten und der Lauf laeuft noch ($(stand)). Owner-Entscheidung: weiterlaufen lassen oder abbrechen und mit der Teilmessung berichten." \
            "high"
        say "DECKEL 20h ueberschritten"
        gewarnt=1
    fi
    if [ "$verstrichen" -gt "$MAX" ]; then
        say "GIVING UP: 34h ohne Abschluss"
        exit 0
    fi
    sleep 300
done
