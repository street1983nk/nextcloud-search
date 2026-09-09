#!/bin/sh
# The concurrency series, with enough requests to carry a promise.
#
# This is 67-nebenlaeufigkeit.sh word for word in structure and in parameters,
# and that is deliberate: the series it produced is the baseline of MESS-02, and
# a series driven with other parameters would be adjacent to it rather than
# comparable with it. Five levels, ten rounds each, 410 requests in all, twenty
# seconds of pause between the levels, the sampler beside it, memory.events
# before the series and after every level.
#
# The baseline of the follow up measurement, on the same box and over the same
# OCS route, 410 requests, not one of them failed:
#
#     conc   requests   p50           p95
#        1         10     376,4 ms      481,6 ms   held
#        4         40     885,1 ms    1.009,4 ms   held
#        8         80   1.792,9 ms    1.915,0 ms   held
#       12        120   2.724,0 ms    3.045,4 ms   broken
#       16        160   3.476,0 ms    3.782,7 ms   broken
#
# So the promise stands on EIGHT concurrent searches, at 76,6 percent of the
# budget of 2500 ms, with oom, oom_kill and oom_group_kill at nought. This series
# is here to confirm or to refute that promise on the state of v1.1, and the
# level 12 sits between the last one that held the budget and the first that did
# not, for the same reason as in the predecessor.
#
# A level that is worse than the baseline gets a line of its own,
# "regression stufe <n>: <alt> auf <neu> ms", because a finding for section 19 of
# the report must not go down in a table column. The line is printed for every
# level that is slower at all, and it says next to it whether the difference is
# larger than the noise band of five percent, so that measurement noise and a
# real regression stay distinguishable.
#
# The model is loaded at this point, deliberately: a promise about concurrency is
# a promise about the steady state, and putting the one time cost of the first
# embedding into the first level would flatter every level after it. That cost is
# measured on its own, in 95-spitze.sh, in both of its roles.
#
# The password comes out of the environment variable FINDLING_LOAD_PASSWORD and
# is handed over with --password-env, which carries the NAME and not the value
# (T-10-15).
set -eu

# Everything a machine could differ in is a variable with a default, so this
# file carries no path of one machine. The first default is derived from the
# location of the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
BASE="${BASE:-https://loadtest.infranode.dev}"
KONTO="${KONTO:-lasttest}"
SAMPLER="${SAMPLER:-$REPO/scripts/ops/rss_sampler.sh}"
LAST="${LAST:-$REPO/scripts/ops/search_load.py}"
# The password file of the load test account on the box. The value is read into
# an environment variable and never handed to a command line.
PWFILE="${PWFILE:-$HOME/work/.pw/lasttest}"
# The parameters of the predecessor, unchanged. Five levels times ten rounds is
# 410 requests.
STUFEN="${STUFEN:-1 4 8 12 16}"
RUNDEN="${RUNDEN:-10}"
PAUSE="${PAUSE:-20}"

mkdir -p "$OUT"
ZIEL="$OUT/97-nebenlaeufigkeit.txt"
CSV="$OUT/97-nebenlaeufigkeit.csv"

CID=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER")
SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"

FINDLING_LOAD_PASSWORD=$(sudo cat "$PWFILE")
export FINDLING_LOAD_PASSWORD

{
    date -u +'nebenlaeufigkeit-start %Y-%m-%dT%H:%M:%SZ'
    printf 'stufen: %s, runden je stufe: %s, pause: %s s\n' "$STUFEN" "$RUNDEN" "$PAUSE"

    echo "=== memory.events, read BEFORE this series ==="
    sudo cat "$SCOPE/memory.events"
    echo "-- and the two figures next to it, as the zero point of the series --"
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s memory.peak=%s memory.max=%s\n' \
        "$(sudo cat "$SCOPE/memory.current")" \
        "$(sudo cat "$SCOPE/memory.peak")" \
        "$(sudo cat "$SCOPE/memory.max")"

    echo "=== The sampler beside it ==="
    sudo sh "$SAMPLER" "$CONTAINER" 2 "$CSV" &
    SAMPLER_PID=$!
    printf 'sampler-pid %s\n' "$SAMPLER_PID"
    sleep 4

    for stufe in $STUFEN; do
        echo "=== Concurrency $stufe over $RUNDEN rounds ==="
        date -u +"stufe-$stufe-vor %Y-%m-%dT%H:%M:%SZ"
        sudo -E python3 "$LAST" \
            --base-url "$BASE" --user "$KONTO" --password-env FINDLING_LOAD_PASSWORD \
            --concurrency "$stufe" --rounds "$RUNDEN" --container "$CONTAINER" \
            >"$OUT/97-stufe-$stufe.json" 2>"$OUT/97-stufe-$stufe.err" || true
        date -u +"stufe-$stufe-nach %Y-%m-%dT%H:%M:%SZ"
        tail -3 "$OUT/97-stufe-$stufe.err" || true
        sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
        printf 'memory.current=%s memory.peak=%s\n' \
            "$(sudo cat "$SCOPE/memory.current")" "$(sudo cat "$SCOPE/memory.peak")"
        sudo cat "$SCOPE/memory.events"
        # A pause between the levels, so the level that follows measures itself
        # and not the tail of the one before it.
        sleep "$PAUSE"
    done

    echo "=== The sampler down ==="
    sudo kill -TERM "$SAMPLER_PID" 2>/dev/null || true
    sleep 3
    tail -3 "$CSV"

    echo "=== The table this promise is read off, and the regressions by name ==="
    python3 - "$OUT" <<'PY'
import json
import pathlib
import sys

# The baseline of the follow up measurement, p95 in milliseconds. Written down
# and not read out of the other report, because a comparison that recomputes its
# own reference agrees with itself no matter what the reference says.
BASELINE = {1: 481.6, 4: 1009.4, 8: 1915.0, 12: 3045.4, 16: 3782.7}
# Anything below this is noise on a box that also answers cron jobs. The line is
# printed either way, the band only says how to read it.
RAUSCHEN = 0.05

out = pathlib.Path(sys.argv[1])


def de(zahl: float) -> str:
    """German thousands and decimal separator, as the reports write them."""
    return f"{zahl:,.1f}".replace(",", "#").replace(".", ",").replace("#", ".")


def mb(bytes_: object) -> str:
    """A cgroup figure in megabytes, or n/a when the reading is not in the report."""
    return de(float(bytes_) / 1048576) if isinstance(bytes_, (int, float)) else "n/a"


kopf = (
    f"{'conc':>5} {'req':>5} {'fail':>5} {'p50':>10} {'p95':>10} "
    f"{'max':>10} {'budget':>7} {'anon MB':>9} {'current MB':>11} {'p95 06.1':>10}"
)
print(kopf)
regressionen = []
for stufe in sorted(BASELINE):
    datei = out / f"97-stufe-{stufe}.json"
    if not datei.is_file():
        print(f"{stufe:>5} (keine Antwortdatei {datei.name})")
        continue
    text = datei.read_text(encoding="utf-8")
    if not text.strip():
        print(f"{stufe:>5} (die Antwortdatei {datei.name} ist leer)")
        continue
    bericht = json.loads(text)
    # search_load.py writes p50_ms, p95_ms and max_ms only if at least one
    # request was answered. A level in which everything failed is a finding and
    # has to be printed as one, not end this table in a KeyError.
    if "p95_ms" not in bericht:
        print(
            f"{stufe:>5} {bericht.get('requests', 0):>5} {bericht.get('failures', 0):>5} "
            f"  keine Anfrage wurde beantwortet, Fehlerarten {bericht.get('failure_kinds', {})}"
        )
        continue
    danach = bericht.get("memory", {}).get("after", {})
    print(
        f"{bericht['concurrency']:>5} {bericht['requests']:>5} {bericht['failures']:>5} "
        f"{de(bericht['p50_ms']):>10} {de(bericht['p95_ms']):>10} {de(bericht['max_ms']):>10} "
        f"{str(bericht.get('p95_within_budget', 'n/a')):>7} {mb(danach.get('anon')):>9} "
        f"{mb(danach.get('memory.current')):>11} {de(BASELINE[stufe]):>10}"
    )
    if bericht["p95_ms"] > BASELINE[stufe]:
        regressionen.append((stufe, BASELINE[stufe], float(bericht["p95_ms"])))

print("")
if not regressionen:
    print("keine stufe ist schlechter als die baseline")
for stufe, alt, neu in regressionen:
    anteil = (neu - alt) / alt
    band = "ueber dem rauschband" if anteil > RAUSCHEN else "innerhalb des rauschbands"
    print(f"regression stufe {stufe}: {de(alt)} auf {de(neu)} ms ({anteil * 100:.1f} Prozent, {band})")
PY

    echo "=== memory.events, all counters, at the end of the series ==="
    sudo cat "$SCOPE/memory.events"
    printf 'OOMKilled=%s RestartCount=%s\n' \
        "$(sudo docker inspect "$CONTAINER" --format '{{.State.OOMKilled}}')" \
        "$(sudo docker inspect "$CONTAINER" --format '{{.RestartCount}}')"

    date -u +'nebenlaeufigkeit-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

echo "97-NEBENLAEUFIGKEIT-FERTIG"
