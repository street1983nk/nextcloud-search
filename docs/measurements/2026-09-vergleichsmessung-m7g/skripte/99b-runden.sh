#!/bin/sh
# The round count of the permission recheck, for DI-07-03, and not one line of
# the permission chain is touched.
#
# **The deferred item in the wording of the matter.** searchCandidates is called
# in php/lib/Search/Provider.php INSIDE the loop over MAX_ROUNDS = 3, and
# snippets once afterwards. The loop turns more than one round when the recheck
# removes hits of a page and there is recheck budget left. A single search can
# therefore set four container calls against a group budget of 2.500 ms, and
# every call gets only what secondsLeft(deadline) leaves over, with a ceiling of
# 1,5 s per call. What is missing to judge any of this is the number: how often
# the loop turns more than one round in real stocks is measured nowhere. This
# step measures it.
#
# **Measured over the number of container calls per user search**, out of the
# access log of the container, split by the candidate route and the snippet
# route. More than one candidate call per search means more than one round. The
# permission chain itself is not asked and not changed: no line in Provider.php,
# no second recheck, no way around the prefilter.
#
# **Two separate cases, because only both together are a statement.**
#
#   Case 1, the everyday: the load test account, which owns every file. The
#     recheck removes nothing, so one round is what to expect.
#   Case 2, the provoked drift: a second account is given a set of files as
#     shares, the index takes the rights up, and then the share is revoked in
#     Nextcloud WITHOUT giving the poller time to follow. A search of that
#     account then gets candidates out of the prefilter that the final PHP
#     recheck removes, and that is exactly when the loop turns more than one
#     round.
#
# **The three sentences about case 2 that the report has to carry.** This state
# is produced on purpose, by revoking a share and asking before the index has
# heard about it. It is not the everyday: in the everyday the poller follows
# within one pass, and the window this case measures is minutes long at most. The
# report must therefore name BOTH cases together with the way each was produced,
# because a number out of a provoked state that is reported as an everyday number
# is worse than no number at all.
#
# Both cases also measure the duration per search, so that the question "what do
# the rounds cost" gets a figure and not only the question "how often". The two
# figures they are held against are the group budget of 2.500 ms
# (Provider::BUDGET_SECONDS) and the per call ceiling of 1,5 s
# (ExAppService::REQUEST_TIMEOUT_SECONDS).
#
# Passwords never become arguments: occ user:add reads OC_PASS out of the
# environment, search_load.py takes --password-env with the NAME of the variable,
# and the curl calls of the share api read their credential out of a config file
# with mode 600 (T-10-27).
#
# The exit codes: 20 the access log carried no request line at all, so the count
# is not a measurement; 21 the drift case could not be produced, which is a
# finding about the box and not about the loop.
set -eu

# Everything a machine could differ in is a variable with a default, so this file
# carries no path of one machine. The first default is derived from the location
# of the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
BASE="${BASE:-https://loadtest.infranode.dev}"
DATA_ROOT="${DATA_ROOT:-/mnt/findling}"
KONTO="${KONTO:-lasttest}"
KORPUSORDNER="${KORPUSORDNER:-loadtest}"
KORPUS="${KORPUS:-$DATA_ROOT/ncdata/$KONTO/files/$KORPUSORDNER}"
LAST="${LAST:-$REPO/scripts/ops/search_load.py}"
# The password file of the load test account on the box. The value goes into an
# environment variable and into a curl config file, never into a command line.
PWFILE="${PWFILE:-$HOME/work/.pw/lasttest}"
# The second account of case 2. It exists for this measurement and for nothing
# else, and its home stays empty so that its own files cannot survive the recheck
# and blunt the case.
DRIFTKONTO="${DRIFTKONTO:-driftfall}"
# How many files are shared, and how many searches each case drives. Both small
# on purpose: the ACL rows of a share have to be taken up by the index, and
# sharing the whole corpus would be a reconcile job of hours.
DATEIEN="${DATEIEN:-40}"
SUCHEN="${SUCHEN:-10}"
# Two rounds of 90 s, the frist of 00-ablauf.md for a counted poller pass: a
# state read at the wrong moment looks like a movement.
FRIST="${FRIST:-90}"
# The two figures of the PHP side, in milliseconds.
BUDGET_MS="${BUDGET_MS:-2500}"
DECKE_MS="${DECKE_MS:-1500}"

if ! command -v jq >/dev/null 2>&1; then
    echo "99b-runden: jq is not on this box, and the share api answers JSON" >&2
    exit 18
fi

mkdir -p "$OUT"
ZIEL="$OUT/99b-runden.txt"
WORK=$(mktemp -d)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT

occ() { sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"; }

FINDLING_LOAD_PASSWORD=$(sudo cat "$PWFILE")
export FINDLING_LOAD_PASSWORD
EIGNERRC="$WORK/eigner.curlrc"
printf 'user = "%s:%s"\n' "$KONTO" "$FINDLING_LOAD_PASSWORD" >"$EIGNERRC"
chmod 600 "$EIGNERRC"

# The drift account gets a fresh password that exists for the length of this
# script. It never needs a curl config file of its own: its searches run over
# search_load.py, which takes the NAME of the variable, and the share api is
# called by the owner and not by the recipient.
DRIFTPW=$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')

# The searches of one case, over the route a user takes. Concurrency 1, because
# the question is how many container calls ONE search sets, and concurrent
# searches would make the log lines of several of them one heap.
#
# The password of the account travels in the exported variable FINDLING_RUNDEN_PW
# and is set by a shell assignment before the call. NOT with `env VAR=wert`: that
# would put the value into the argument list of env, which is the process list of
# the box, and it is the very thing --password-env exists to avoid.
suchen() {
    konto=$1
    ziel=$2
    sudo -E python3 "$LAST" \
        --base-url "$BASE" --user "$konto" --password-env FINDLING_RUNDEN_PW \
        --concurrency 1 --rounds "$SUCHEN" --container "$CONTAINER" \
        >"$ziel" 2>"$ziel.err" || true
    tail -3 "$ziel.err" || true
}

# One reading of the access log of the container in a time window, split by the
# two routes. The container is a uvicorn behind AppAPI, and its access log is
# where a request per line comes from.
auswerten() {
    label=$1
    bericht=$2
    protokoll=$3
    kandidaten=$(grep -c 'POST /search' "$protokoll" || true)
    snippets=$(grep -c 'POST /snippets' "$protokoll" || true)
    python3 - "$label" "$bericht" "${kandidaten:-0}" "${snippets:-0}" "$SUCHEN" "$BUDGET_MS" "$DECKE_MS" <<'PY'
import json
import pathlib
import sys

label, pfad, kandidaten, snippets, suchen, budget, decke = (
    sys.argv[1],
    sys.argv[2],
    int(sys.argv[3]),
    int(sys.argv[4]),
    int(sys.argv[5]),
    float(sys.argv[6]),
    float(sys.argv[7]),
)


def de(zahl: float) -> str:
    """German thousands and decimal separator, as the reports write them."""
    return f"{zahl:,.1f}".replace(",", "#").replace(".", ",").replace("#", ".")


print(f"{label} suchen-gefahren        {suchen}")
print(f"{label} kandidatenaufrufe      {kandidaten}")
print(f"{label} snippetaufrufe         {snippets}")
if suchen > 0:
    print(f"{label} runden-je-suche        {de(kandidaten / suchen)}")
    print(f"{label} snippets-je-suche      {de(snippets / suchen)}")
    print(f"{label} containeraufrufe-je-suche {de((kandidaten + snippets) / suchen)}")
    # No line at all is not a round count of zero, it is a statement about the
    # log. Naming both in the same run would be two verdicts that contradict each
    # other, so exactly one of the two is printed.
    if kandidaten == 0 and snippets == 0:
        print(f"{label} befund                 das Zugriffsprotokoll traegt keine Anfragezeile;")
        print(f"{label}                        die Zaehlung ist damit keine Messung, sondern eine")
        print(f"{label}                        Aussage ueber das Protokoll (siehe die Stichprobe)")
    elif kandidaten / suchen > 1.05:
        print(f"{label} befund                 mehr als eine Runde je Suche")
    else:
        print(f"{label} befund                 eine Runde je Suche")

text = pathlib.Path(pfad).read_text(encoding="utf-8") if pathlib.Path(pfad).is_file() else ""
if not text.strip():
    print(f"{label} dauer                  keine Antwortdatei, siehe die Fehlerdatei daneben")
    raise SystemExit(0)
bericht = json.loads(text)
print(f"{label} anfragen               {bericht.get('requests', 0)} "
      f"(davon fehlgeschlagen {bericht.get('failures', 0)})")
print(f"{label} treffer-insgesamt      {bericht.get('hits_total', 0)}")
# search_load.py writes p50_ms, p95_ms and max_ms only if at least one request
# was answered. A case in which everything failed is the most interesting one of
# the two, and it must not end this block in a KeyError.
if "max_ms" not in bericht:
    print(f"{label} dauer                  keine Anfrage wurde beantwortet")
    print(f"{label} fehlerarten            {bericht.get('failure_kinds', {})}")
    raise SystemExit(0)
print(f"{label} p50                    {de(float(bericht['p50_ms']))} ms")
print(f"{label} p95                    {de(float(bericht['p95_ms']))} ms")
print(f"{label} max                    {de(float(bericht['max_ms']))} ms")
print(f"{label} gruppenbudget          {de(budget)} ms (Provider::BUDGET_SECONDS = 2.5)")
print(f"{label} marge-zum-budget       {de(budget - float(bericht['p95_ms']))} ms")
print(f"{label} aufrufdecke            {de(decke)} ms (ExAppService::REQUEST_TIMEOUT_SECONDS = 1.5)")
print(f"{label} hinweis                die Decke gilt JE AUFRUF, das Budget je Ergebnisgruppe;")
print(f"{label}                        bei mehr als einer Runde teilen sich mehrere Aufrufe")
print(f"{label}                        dasselbe Budget, und secondsLeft deckelt jeden weiteren")
PY
}

{
    date -u +'runden-start %Y-%m-%dT%H:%M:%SZ'
    printf 'container: %s\n' "$CONTAINER"
    printf 'suchen je fall: %s, geteilte dateien: %s\n' "$SUCHEN" "$DATEIEN"
    echo "gemessen wird die Zahl der Containeraufrufe je Nutzersuche, getrennt nach"
    echo "der Kandidatenroute und der Snippet-Route. Die Berechtigungskette wird nicht"
    echo "angefasst: keine Zeile in Provider.php, kein zweiter Recheck, kein Weg um den"
    echo "Vorfilter herum."

    echo "=== Fall 1, der Alltag: das Konto, das alle Dateien besitzt ==="
    STEMPEL=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    sleep 1
    FINDLING_RUNDEN_PW="$FINDLING_LOAD_PASSWORD"
    export FINDLING_RUNDEN_PW
    suchen "$KONTO" "$OUT/99b-fall1.json"
    sleep 3
    sudo docker logs --since "$STEMPEL" "$CONTAINER" >"$WORK/fall1.log" 2>&1 || true
    echo "-- eine Stichprobe des Protokollfensters, damit die Zaehlung nachlesbar ist --"
    grep -E 'POST /(search|snippets)' "$WORK/fall1.log" | tail -6 || true
    auswerten 'fall1' "$OUT/99b-fall1.json" "$WORK/fall1.log"

    echo "=== Fall 2, der provozierte Driftfall: Vorbereitung ==="
    # The skeleton is switched off before the account is created, so its home
    # stays empty: own files of that account would survive the recheck and blunt
    # the very case this section produces.
    SKELETON_VORHER=$(occ config:system:get skeletondirectory 2>/dev/null || true)
    occ config:system:set skeletondirectory --value='' 2>&1 || true
    if occ user:info "$DRIFTKONTO" >/dev/null 2>&1; then
        echo "das Driftkonto existiert schon, das Passwort wird neu gesetzt"
        OC_PASS="$DRIFTPW" occ user:resetpassword --password-from-env "$DRIFTKONTO" 2>&1 || true
    else
        OC_PASS="$DRIFTPW" occ user:add --password-from-env "$DRIFTKONTO" 2>&1
    fi

    echo "-- die $DATEIEN Dateien, die geteilt werden --"
    sudo ls "$KORPUS" | head -"$DATEIEN" >"$WORK/namen.txt"
    wc -l "$WORK/namen.txt"
    : >"$WORK/shares.txt"
    while IFS= read -r name; do
        antwort=$(curl -s -K "$EIGNERRC" \
            -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
            -d "path=/$KORPUSORDNER/$name" \
            -d 'shareType=0' \
            -d "shareWith=$DRIFTKONTO" \
            -d 'permissions=1' \
            "$BASE/ocs/v2.php/apps/files_sharing/api/v1/shares" || true)
        printf '%s\n' "$antwort" | jq -r '.ocs.data.id // empty' >>"$WORK/shares.txt" 2>/dev/null || true
    done <"$WORK/namen.txt"
    printf 'freigaben-angelegt %s\n' "$(grep -c . "$WORK/shares.txt" || true)"
    # The recipient's mount only exists in the mount cache after a scan, and the
    # index reads the access list out of that cache.
    occ files:scan --all 2>&1 | tail -3 || true

    echo "-- die Frist, gegen die langsamste Uhr, und der Durchgang wird GEZAEHLT --"
    CSTART=$(sudo docker inspect "$CONTAINER" --format '{{.State.StartedAt}}')
    vorher=$(sudo docker logs --since "$CSTART" "$CONTAINER" 2>&1 | grep -c 'pass finished' || true)
    sleep "$FRIST"
    sleep "$FRIST"
    nachher=$(sudo docker logs --since "$CSTART" "$CONTAINER" 2>&1 | grep -c 'pass finished' || true)
    printf 'poller-durchgaenge vorher=%s nachher=%s\n' "${vorher:-0}" "${nachher:-0}"

    echo "-- die Kontrolle: sieht das Driftkonto die Dateien, BEVOR zurueckgenommen wird --"
    FINDLING_RUNDEN_PW="$DRIFTPW"
    export FINDLING_RUNDEN_PW
    suchen "$DRIFTKONTO" "$OUT/99b-fall2-vor-ruecknahme.json"
    treffer=$(jq -r '.hits_total // 0' "$OUT/99b-fall2-vor-ruecknahme.json" 2>/dev/null || echo 0)
    printf 'treffer-vor-ruecknahme %s\n' "$treffer"
    if [ "${treffer:-0}" -gt 0 ]; then
        echo 'rechte-aufgenommen ja' >"$WORK/drift-urteil"
    else
        echo 'rechte-aufgenommen nein' >"$WORK/drift-urteil"
    fi
    cat "$WORK/drift-urteil"

    echo "=== Fall 2, der provozierte Driftfall: die Ruecknahme und die Messung ==="
    echo "-- die Freigaben zurueckgenommen, OHNE dem Poller Zeit zu geben --"
    while IFS= read -r kennung; do
        [ -n "$kennung" ] || continue
        curl -s -o /dev/null -K "$EIGNERRC" \
            -H 'OCS-APIRequest: true' -X DELETE \
            "$BASE/ocs/v2.php/apps/files_sharing/api/v1/shares/$kennung" || true
    done <"$WORK/shares.txt"
    date -u +'ruecknahme %Y-%m-%dT%H:%M:%SZ'

    STEMPEL=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    sleep 1
    suchen "$DRIFTKONTO" "$OUT/99b-fall2.json"
    sleep 3
    sudo docker logs --since "$STEMPEL" "$CONTAINER" >"$WORK/fall2.log" 2>&1 || true
    echo "-- eine Stichprobe des Protokollfensters, damit die Zaehlung nachlesbar ist --"
    grep -E 'POST /(search|snippets)' "$WORK/fall2.log" | tail -6 || true
    auswerten 'fall2' "$OUT/99b-fall2.json" "$WORK/fall2.log"
    treffer2=$(jq -r '.hits_total // 0' "$OUT/99b-fall2.json" 2>/dev/null || echo 0)
    printf 'treffer-nach-ruecknahme %s\n' "$treffer2"

    echo "-- die dreiwertige Lesung dieses Falls, damit er nicht behauptet wird --"
    echo "   treffer > 0 nach der Ruecknahme: der Recheck hat NICHT entfernt, die"
    echo "   Freigabe war noch wirksam, und dieser Fall ist nicht der Driftfall."
    echo "   treffer = 0 und mehr als eine Runde je Suche: der Driftfall ist erzeugt."
    echo "   treffer = 0 und eine Runde je Suche: der Vorfilter wusste schon Bescheid,"
    echo "   die Drift war zu kurz, und die Zahl ist keine Aussage ueber die Schleife."

    echo "=== Die Einordnung, die der Bericht uebernehmen muss ==="
    echo "Fall 1 ist der Alltag: ein Konto, das alle Dateien besitzt, und ein Recheck,"
    echo "der nichts entfernt. Fall 2 ist ABSICHTLICH erzeugt: eine Freigabe wurde"
    echo "zurueckgenommen und gefragt wurde, bevor der Index davon wusste. Der Bericht"
    echo "muss beide Faelle mit ihrer Herstellung nennen; eine Zahl aus dem"
    echo "provozierten Zustand als Alltagszahl zu berichten ist schlimmer als keine"
    echo "Zahl. Ueber MAX_ROUNDS entscheidet dieses Skript nicht, es liefert die Zahlen,"
    echo "nach denen DI-07-03 fragt."

    echo "=== Die Aufraeumung, so weit sie folgenlos ist ==="
    if [ -n "${SKELETON_VORHER:-}" ]; then
        occ config:system:set skeletondirectory --value="$SKELETON_VORHER" 2>&1 || true
    else
        occ config:system:delete skeletondirectory 2>&1 || true
    fi
    echo "das Konto $DRIFTKONTO bleibt stehen: ein user:delete loest eine Raeumung im"
    echo "Index aus, und die waere eine Bewegung mitten in einer Messreihe."

    kandidaten1=$(grep -c 'POST /search' "$WORK/fall1.log" || true)
    kandidaten2=$(grep -c 'POST /search' "$WORK/fall2.log" || true)
    if [ "${kandidaten1:-0}" -eq 0 ] && [ "${kandidaten2:-0}" -eq 0 ]; then
        echo 'protokoll-traegt-anfragen nein' >"$WORK/urteil"
    else
        echo 'protokoll-traegt-anfragen ja' >"$WORK/urteil"
    fi
    cat "$WORK/urteil"

    date -u +'runden-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Everything below the pipeline, because the return code of a pipeline belongs to
# tee: an exit inside the block above would only leave the subshell, and the
# refusal would be a line in the raw file that nobody reads.
protokoll=$(cat "$WORK/urteil" 2>/dev/null || echo 'protokoll-traegt-anfragen nein')
drift=$(cat "$WORK/drift-urteil" 2>/dev/null || echo 'rechte-aufgenommen nein')

if [ "$protokoll" != 'protokoll-traegt-anfragen ja' ]; then
    echo "99b-runden: the access log of the container carried no request line at all" >&2
    echo "99b-runden: the count is therefore a statement about the log and not about" >&2
    echo "99b-runden: the loop; $ZIEL holds the sample of the window" >&2
    exit 20
fi

if [ "$drift" != 'rechte-aufgenommen ja' ]; then
    echo "99b-runden: the drift case could not be produced: the index never took the" >&2
    echo "99b-runden: rights of the shares up, so the revocation removed nothing that" >&2
    echo "99b-runden: was there. Fall 1 stands, Fall 2 is a finding about the box" >&2
    exit 21
fi

echo "99B-RUNDEN-FERTIG"
