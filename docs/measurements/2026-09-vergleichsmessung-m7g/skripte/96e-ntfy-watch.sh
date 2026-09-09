#!/bin/sh
# The notification chain of the full run, and it decides nothing.
#
# Why this script logs instead of just sending. Its predecessor
# volllauf_watch.sh of plan 05-21 sent and did not look, and the target of the
# semantic run answered {"code":40301,"http":403,"error":"forbidden"} on 05.09.
# from the same box that it had accepted a message from on 04.09., because the
# box had a new public address. The server was reachable and the topic refused
# the message. A chain that silently does not report is worse than none, because
# somebody relies on it. So the HTTP code of EVERY attempt goes into
# 99-ntfy-watch.log, and a code that is not a 2xx falls through to the mail
# fallback, which the global rule says stays switched on.
#
# **The contract is the file, the message is the extra** (pitfall 6). The end of
# the run is 00-FERTIG in the run directory, written by 96b-waechter.sh after the
# OOM proof. No step of this run may depend on a message arriving, and this
# script therefore ends with return code 0 even when nothing was accepted
# anywhere: the failure stands in the log, where it can be read afterwards, and
# it never ends a nineteen hour run.
#
# Three modes, because the same chain is used from two directions:
#
#   96e-ntfy-watch.sh start                    announce that the run was triggered
#   96e-ntfy-watch.sh senden <titel> <text> [prio]   one attempt, logged
#   96e-ntfy-watch.sh warten                   watch for 00-FERTIG, warn at the cap
#
# The watchman calls "senden" itself, right after it has written 00-FERTIG, and
# the "warten" mode watches the same file independently. That the finish may
# therefore be announced twice is deliberate: two senders that do not know about
# each other are the cheapest insurance against the one that does not run.
set -eu

# Everything a machine could differ in is a variable with a default, so this file
# carries no path of one machine. The first default is derived from the location
# of the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
OUT="${OUT:-$SKRIPTE/../rohdaten}"
LOG="${LOG:-$OUT/99-ntfy-watch.log}"
FERTIG="${FERTIG:-$OUT/00-FERTIG}"
CSV="${CSV:-$OUT/96-volllauf.csv}"
TOPIC="${TOPIC:-https://ntfy.infranode.dev/infranode-alerts-f43ceefc1193}"
# The mail fallback of the global rule. It is not switched off for a run over
# night, and its address is a variable so that it can be pointed somewhere else
# without touching the body.
MAILTO="${MAILTO:-admin@infranode.dev}"
# The two clocks of the watching mode. 20 h is the point at which the owner has
# to decide whether the run carries on, 34 h is the point at which this script
# stops watching. Neither of them stops the run.
DECKEL="${DECKEL:-$((20 * 3600))}"
MAX="${MAX:-$((34 * 3600))}"
INTERVALL="${INTERVALL:-300}"
KENNUNG="${KENNUNG:-Findling 10-04 Volllauf}"

mkdir -p "$OUT"

say() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" >>"$LOG"; }

# The last anon figure of the sampler, so a warning carries a number instead of
# only a worry. A missing csv is an empty string and never an error.
stand() {
    tail -1 "$CSV" 2>/dev/null | awk '{print $NF}' | cut -d, -f2 |
        awk '{if ($1 > 0) printf "%.0f MB anon", $1/1048576; else print "kein Messwert"}'
}

mail_fallback() {
    # The fallback of the global rule: ntfy first, mail behind it, and the
    # fallback is not switched off. Whether it worked is a logged return code and
    # never a condition of anything.
    if command -v mail >/dev/null 2>&1; then
        printf '%s\n' "$2" | mail -s "$1" "$MAILTO" >/dev/null 2>&1
        say "mail-fallback ueber mail, rc=$?, an=$MAILTO"
    elif command -v sendmail >/dev/null 2>&1; then
        printf 'Subject: %s\n\n%s\n' "$1" "$2" | sendmail "$MAILTO" >/dev/null 2>&1
        say "mail-fallback ueber sendmail, rc=$?, an=$MAILTO"
    else
        say "mail-fallback nicht moeglich: weder mail noch sendmail auf dieser Box"
    fi
}

sende() {
    titel=$1
    text=$2
    prio=${3:-default}
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 \
        -H "Title: $titel" -H "Priority: $prio" \
        -d "$text" "$TOPIC" 2>/dev/null || echo 000)
    say "ntfy versucht, http=$code, prio=$prio, titel=$titel"
    case "$code" in
    2*) ;;
    *)
        say "ntfy hat NICHT angenommen (http=$code), der Fallback laeuft"
        mail_fallback "$titel" "$text"
        ;;
    esac
}

modus="${1:-}"
case "$modus" in
start)
    say "meldekette scharf, modus=start"
    sende "$KENNUNG gestartet" \
        "Der Volllauf ist angestossen. Der Vertrag des Abschlusses ist die Datei 00-FERTIG im Laufverzeichnis; diese Nachricht ist die Zugabe." \
        default
    ;;
senden)
    if [ "$#" -lt 3 ]; then
        say "senden ohne Titel oder Text aufgerufen, nichts gesendet"
        echo "96e-ntfy-watch: usage: 96e-ntfy-watch.sh senden <titel> <text> [prio]" >&2
        exit 0
    fi
    sende "$2" "$3" "${4:-default}"
    ;;
warten)
    START=$(date +%s)
    gewarnt=0
    say "meldekette scharf, modus=warten, prueft alle $INTERVALL s, deckel $((DECKEL / 3600)) h"
    while :; do
        verstrichen=$(($(date +%s) - START))
        if [ -f "$FERTIG" ]; then
            std=$(awk -v s="$verstrichen" 'BEGIN{printf "%.1f", s/3600}')
            say "00-FERTIG gesehen nach ${std}h"
            sende "$KENNUNG fertig" \
                "Der Volllauf ist durch, nach ${std} h beobachteter Zeit. Der OOM-Beweis ist erhoben und 00-FERTIG traegt Zeitpunkt, Dauer und Weckwort." \
                default
            exit 0
        fi
        if [ "$verstrichen" -gt "$DECKEL" ] && [ "$gewarnt" -eq 0 ]; then
            sende "$KENNUNG ueber $((DECKEL / 3600)) h" \
                "Der Deckel von $((DECKEL / 3600)) h ist ueberschritten und der Lauf laeuft noch ($(stand)). Owner-Entscheidung: weiterlaufen lassen oder abbrechen und mit der Teilmessung berichten." \
                high
            say "DECKEL $((DECKEL / 3600))h ueberschritten"
            gewarnt=1
        fi
        if [ "$verstrichen" -gt "$MAX" ]; then
            say "GIVING UP: $((MAX / 3600))h ohne 00-FERTIG, das Beobachten endet, der Lauf nicht"
            exit 0
        fi
        sleep "$INTERVALL"
    done
    ;;
*)
    echo "96e-ntfy-watch: the mode is a mandatory argument" >&2
    echo "96e-ntfy-watch: usage: 96e-ntfy-watch.sh <start|senden|warten>" >&2
    echo "96e-ntfy-watch: start announces the trigger, senden makes one logged attempt," >&2
    echo "96e-ntfy-watch: warten watches for 00-FERTIG and warns at the cap" >&2
    # Not an error either: a chain that is called wrongly must not end a run.
    exit 0
    ;;
esac

echo "96E-NTFY-WATCH-FERTIG modus=$modus"
