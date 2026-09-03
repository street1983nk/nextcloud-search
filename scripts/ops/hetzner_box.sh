#!/bin/sh
# Rent the ARM box of the load test, prove what it costs, and give it back.
#
# The load run of phase 5 needs a machine this project does not own: an Ampere
# CAX11 with 4 GB of memory and a 50 GB volume, because the 40 GB root disk of
# that machine does not hold a 20 GB corpus plus the index plus the images. The
# box is rented for the run and deleted afterwards, and that second half is not
# an afterthought but decision D-01: a forgotten box with a Nextcloud, an admin
# password and an open port 443 is a security problem and a monthly invoice.
# Therefore destroy belongs to every end of the run, including the ends nobody
# planned, and it verifies afterwards that both resources are really gone.
#
# Four subcommands and no automatic behaviour that creates anything by itself:
#
#     prices    what the account is actually charged for cax servers
#     create    the box and the volume, plus a state file outside the repository
#     status    what is running, for how long, and what it has cost so far
#     destroy   the volume and the box, with a check that both are gone
#
# The token comes out of the environment and nowhere else. It is never printed,
# never written into the state file, and it is handed to curl through a config
# file on standard input rather than as an argument, so it does not stand in the
# process list of the box either (T-05-17).
#
# Both resources carry the label purpose=findling-phase5. That is not decoration:
# in an account that holds other things, a label is the only way to find a
# resource that was forgotten, and "status" without a state file searches by
# exactly that label (T-05-19).
#
# Usage: HCLOUD_TOKEN=... scripts/ops/hetzner_box.sh <prices|create|status|destroy>

set -eu

API_BASE='https://api.hetzner.cloud/v1'

SERVER_TYPE='cax11'
SERVER_IMAGE='ubuntu-24.04'
SERVER_LOCATION='nbg1'
SERVER_NAME='findling-arm-loadtest'
VOLUME_NAME='findling-corpus'
VOLUME_SIZE_GB=50
LABEL='purpose=findling-phase5'

# Outside the working tree on purpose. A state file inside the repository is one
# careless git add away from a public commit, and it is the kind of file that
# nobody notices in a diff of a load test branch.
STATE_DIR="${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}"
STATE_FILE="$STATE_DIR/box.env"

# One month of billing at Hetzner, in hours. Used only to turn the monthly price
# the API states into the hourly one when the API does not state an hourly price.
HOURS_PER_MONTH=730

usage() {
    echo "usage: hetzner_box.sh <prices|create|status|destroy>" >&2
    echo "  prices   list the cax server types with the prices of this account" >&2
    echo "  create   create the box and the volume and write $STATE_FILE" >&2
    echo "  status   state, run time and the cost so far" >&2
    echo "  destroy  delete the volume and the box, then verify both are gone" >&2
    # printf and not echo, so that no line of this script has the words echo and
    # the name of the token variable next to each other. That is a rule with a
    # test behind it, and the test cannot tell a name from a value.
    printf 'the token is read from the environment: %s=... hetzner_box.sh prices\n' 'HCLOUD_TOKEN' >&2
}

require_token() {
    # The first thing every subcommand that talks to the API does. Without it the
    # script must not reach curl at all.
    : "${HCLOUD_TOKEN:?token fehlt}"
}

require_tools() {
    for tool in curl python3 date; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            echo "hetzner_box: $tool is required and not on the path" >&2
            exit 1
        fi
    done
}

# The token is written into a curl config on standard input. Not into an
# argument, because arguments are world readable in the process list, and not
# into a file, because a file outlives the call.
curl_config() {
    printf 'silent\nshow-error\n'
    printf 'header = "Authorization: Bearer %s"\n' "$HCLOUD_TOKEN"
    printf 'header = "Content-Type: application/json"\n'
}

# One request. The body is optional; the exit code of curl is swallowed on
# purpose, because an empty or an error answer is reported by the caller with a
# sentence instead of by the shell with a number.
api() {
    api_method="$1"
    api_path="$2"
    api_body="${3:-}"
    if [ -n "$api_body" ]; then
        curl_config | curl --config - --request "$api_method" --data "$api_body" "$API_BASE$api_path" || true
    else
        curl_config | curl --config - --request "$api_method" "$API_BASE$api_path" || true
    fi
}

# The answers are nested JSON, and a price list per location is exactly the place
# where an extraction with sed produces a plausible wrong number in a cost
# report. python3 is on Ubuntu 24.04 out of the box, so this costs no dependency.
json() {
    python3 -c "$1"
}

# The API states a failure as an object with a code and a message. Both are
# printed, the request never is: the request carries the token.
api_error() {
    printf '%s' "$1" | json '
import json
import sys

try:
    payload = json.load(sys.stdin)
except ValueError:
    print("the answer is not JSON, so the request did not reach the API")
    raise SystemExit(0)
error = payload.get("error")
if error:
    print("%s: %s" % (error.get("code", "unknown"), error.get("message", "")))
'
}

fail_on_error() {
    if [ -z "$1" ]; then
        echo "hetzner_box: no answer from the API" >&2
        exit 1
    fi
    message=$(api_error "$1")
    if [ -n "$message" ]; then
        echo "hetzner_box: the API refused the request: $message" >&2
        exit 1
    fi
}

read_state() {
    if [ ! -r "$STATE_FILE" ]; then
        return 1
    fi
    # shellcheck source=/dev/null
    . "$STATE_FILE"
    return 0
}

cmd_prices() {
    require_token
    require_tools
    response=$(api GET /server_types)
    fail_on_error "$response"
    printf '%s' "$response" | json '
import json
import sys

payload = json.load(sys.stdin)
print("%-8s %5s %7s %6s %-8s %s" % ("name", "cores", "memory", "disk", "arch", "price per month, gross"))
for server_type in payload["server_types"]:
    if not server_type["name"].startswith("cax"):
        continue
    prices = ", ".join(
        "%s %s" % (price["location"], price["price_monthly"]["gross"]) for price in server_type["prices"]
    )
    print(
        "%-8s %5s %6s G %5s G %-8s %s"
        % (
            server_type["name"],
            server_type["cores"],
            server_type["memory"],
            server_type["disk"],
            server_type["architecture"],
            prices,
        )
    )
'
    echo "hetzner_box: these are the prices of this account, not of a web search"
}

cmd_create() {
    require_token
    require_tools

    if read_state; then
        echo "hetzner_box: $STATE_FILE already names server ${SERVER_ID:-?}" >&2
        echo "run status, or destroy first: two boxes are two invoices" >&2
        exit 1
    fi

    server_body=$(
        printf '{"name":"%s","server_type":"%s","image":"%s","location":"%s"' \
            "$SERVER_NAME" "$SERVER_TYPE" "$SERVER_IMAGE" "$SERVER_LOCATION"
        printf ',"start_after_create":true,"labels":{"%s":"%s"}}' \
            "${LABEL%%=*}" "${LABEL#*=}"
    )
    echo "hetzner_box: creating $SERVER_TYPE $SERVER_NAME in $SERVER_LOCATION"
    response=$(api POST /servers "$server_body")
    fail_on_error "$response"

    server_id=$(printf '%s' "$response" | json 'import json,sys; print(json.load(sys.stdin)["server"]["id"])')
    server_ip=$(
        printf '%s' "$response" | json 'import json,sys; print(json.load(sys.stdin)["server"]["public_net"]["ipv4"]["ip"])'
    )

    volume_body=$(
        printf '{"name":"%s","size":%s,"server":%s' "$VOLUME_NAME" "$VOLUME_SIZE_GB" "$server_id"
        printf ',"automount":true,"format":"ext4","labels":{"%s":"%s"}}' \
            "${LABEL%%=*}" "${LABEL#*=}"
    )
    echo "hetzner_box: attaching a ${VOLUME_SIZE_GB} GB volume, ext4, automounted"
    response=$(api POST /volumes "$volume_body")
    fail_on_error "$response"

    volume_id=$(printf '%s' "$response" | json 'import json,sys; print(json.load(sys.stdin)["volume"]["id"])')
    volume_device=$(printf '%s' "$response" | json 'import json,sys; print(json.load(sys.stdin)["volume"]["linux_device"])')

    created_at=$(date -u +%s)
    created_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    # umask before the first write, so the file is never readable by others, not
    # even for the moment between creation and a chmod. It holds no secret today
    # and it will not start holding one by accident.
    mkdir -p "$STATE_DIR"
    (
        umask 077
        {
            echo "# Written by scripts/ops/hetzner_box.sh. No token in here, by design."
            echo "SERVER_ID=$server_id"
            echo "SERVER_NAME=$SERVER_NAME"
            echo "SERVER_TYPE=$SERVER_TYPE"
            echo "SERVER_IP=$server_ip"
            echo "SERVER_LOCATION=$SERVER_LOCATION"
            echo "VOLUME_ID=$volume_id"
            echo "VOLUME_NAME=$VOLUME_NAME"
            echo "VOLUME_SIZE_GB=$VOLUME_SIZE_GB"
            echo "VOLUME_DEVICE=$volume_device"
            echo "CREATED_AT=$created_at"
            echo "CREATED_ISO=$created_iso"
        } >"$STATE_FILE"
    )

    echo "hetzner_box: server=$server_id volume=$volume_id ipv4=$server_ip created=$created_iso"
    echo "hetzner_box: state in $STATE_FILE, label $LABEL on both resources"
    echo "hetzner_box: when the run ends, for any reason: hetzner_box.sh destroy"
}

cmd_status() {
    require_token
    require_tools

    if ! read_state; then
        echo "hetzner_box: no state file at $STATE_FILE, searching by label $LABEL" >&2
        response=$(api GET "/servers?label_selector=$LABEL")
        fail_on_error "$response"
        printf '%s' "$response" | json '
import json
import sys

payload = json.load(sys.stdin)
servers = payload["servers"]
if not servers:
    print("no server carries the label, so nothing of this test is running")
for server in servers:
    print("server %s %s %s" % (server["id"], server["name"], server["status"]))
'
        response=$(api GET "/volumes?label_selector=$LABEL")
        fail_on_error "$response"
        printf '%s' "$response" | json '
import json
import sys

for volume in json.load(sys.stdin)["volumes"]:
    print("volume %s %s %s G" % (volume["id"], volume["name"], volume["size"]))
'
        return 0
    fi

    server=$(api GET "/servers/$SERVER_ID")
    fail_on_error "$server"
    volume=$(api GET "/volumes/$VOLUME_ID")
    fail_on_error "$volume"
    pricing=$(api GET /pricing)
    fail_on_error "$pricing"

    now=$(date -u +%s)
    printf '%s\n%s\n%s\n' "$server" "$volume" "$pricing" | json "
import json
import sys

server = json.loads(sys.stdin.readline())['server']
volume = json.loads(sys.stdin.readline())['volume']
pricing = json.loads(sys.stdin.readline())['pricing']

hours = ($now - $CREATED_AT) / 3600.0
currency = pricing['currency']

server_hourly = 0.0
server_monthly = 0.0
for server_type in pricing['server_types']:
    if server_type['name'] != '$SERVER_TYPE':
        continue
    for price in server_type['prices']:
        if price['location'] != '$SERVER_LOCATION':
            continue
        server_hourly = float(price['price_hourly']['gross'])
        server_monthly = float(price['price_monthly']['gross'])

volume_monthly = float(pricing['volume']['price_per_gb_month']['gross']) * $VOLUME_SIZE_GB
volume_hourly = volume_monthly / $HOURS_PER_MONTH
spent = hours * (server_hourly + volume_hourly)

print('server  %s %s %s' % (server['id'], server['name'], server['status']))
print('volume  %s %s %s G attached to %s' % (
    volume['id'], volume['name'], volume['size'], volume['server']))
print('running %.1f hours since $CREATED_ISO' % hours)
print('price   %.4f %s per hour for the box, %.4f for the volume' % (
    server_hourly, currency, volume_hourly))
print('month   %.2f %s box, %.2f %s volume' % (
    server_monthly, currency, volume_monthly, currency))
print('spent   %.2f %s so far, gross, out of this account' % (spent, currency))
"
}

gone() {
    # Gone means the API says not_found. Anything else, including an answer this
    # script cannot read, counts as still there: a resource that is presumed
    # deleted is the actual risk of this whole exercise.
    printf '%s' "$1" | json '
import json
import sys

try:
    payload = json.load(sys.stdin)
except ValueError:
    print("unreadable")
    raise SystemExit(0)
error = payload.get("error") or {}
print("gone" if error.get("code") == "not_found" else "there")
'
}

cmd_destroy() {
    require_token
    require_tools

    server_id="${1:-}"
    volume_id="${2:-}"
    if [ -z "$server_id" ]; then
        if ! read_state; then
            echo "hetzner_box: no state file at $STATE_FILE and no ids given" >&2
            echo "usage: hetzner_box.sh destroy [server-id] [volume-id]" >&2
            echo "run status first: it searches the account by label $LABEL" >&2
            exit 1
        fi
        server_id="$SERVER_ID"
        volume_id="$VOLUME_ID"
    fi

    if [ -n "$volume_id" ]; then
        # A volume that is attached cannot be deleted, so it is detached first and
        # the detach is waited out. The wait has a counter and a spoken end, as
        # the registration script of the development stack has: a loop without one
        # turns a failed detach into a script that hangs.
        echo "hetzner_box: detaching volume $volume_id"
        response=$(api POST "/volumes/$volume_id/actions/detach" '{}')
        if [ -n "$(api_error "$response")" ]; then
            echo "hetzner_box: the detach did not take: $(api_error "$response")" >&2
            echo "hetzner_box: continuing, the volume may already be detached" >&2
        fi
        round=0
        while [ "$round" -lt 30 ]; do
            response=$(api GET "/volumes/$volume_id")
            attached=$(printf '%s' "$response" | json '
import json
import sys

try:
    print(json.load(sys.stdin)["volume"]["server"])
except (ValueError, KeyError, TypeError):
    print("None")
')
            if [ "$attached" = "None" ]; then
                break
            fi
            round=$((round + 1))
            sleep 2
        done
        if [ "$round" -ge 30 ]; then
            echo "hetzner_box: volume $volume_id is still attached after a minute" >&2
            echo "hetzner_box: deleting the server first, which detaches it" >&2
        fi

        echo "hetzner_box: deleting volume $volume_id"
        response=$(api DELETE "/volumes/$volume_id")
        if [ -n "$(api_error "$response")" ]; then
            echo "hetzner_box: the volume was not deleted yet: $(api_error "$response")" >&2
        fi
    fi

    echo "hetzner_box: deleting server $server_id"
    response=$(api DELETE "/servers/$server_id")
    if [ -n "$(api_error "$response")" ]; then
        echo "hetzner_box: the server was not deleted: $(api_error "$response")" >&2
    fi

    # A second attempt at the volume, for the case above where the server had to
    # go first to get it detached.
    if [ -n "$volume_id" ] && [ "$(gone "$(api GET "/volumes/$volume_id")")" != "gone" ]; then
        api DELETE "/volumes/$volume_id" >/dev/null
    fi

    failed=0
    server_state=$(gone "$(api GET "/servers/$server_id")")
    volume_state='gone'
    if [ -n "$volume_id" ]; then
        volume_state=$(gone "$(api GET "/volumes/$volume_id")")
    fi

    if [ "$server_state" = "gone" ]; then
        echo "hetzner_box: server $server_id is gone, verified against the API"
    else
        echo "hetzner_box: server $server_id is still there ($server_state)" >&2
        failed=1
    fi
    if [ "$volume_state" = "gone" ]; then
        echo "hetzner_box: volume ${volume_id:-none} is gone, verified against the API"
    else
        echo "hetzner_box: volume $volume_id is still there ($volume_state)" >&2
        failed=1
    fi

    if [ "$failed" -ne 0 ]; then
        echo "hetzner_box: something is left over. Find it by label: $LABEL" >&2
        echo "hetzner_box: the state file stays, so a second destroy can use it" >&2
        exit 1
    fi

    # Only now, because a state file that names deleted resources is a lie and a
    # state file that is missing while they still exist is worse.
    rm -f "$STATE_FILE"
    echo "hetzner_box: both resources are gone and $STATE_FILE is removed"
}

COMMAND="${1:-}"
if [ -n "$COMMAND" ]; then
    shift
fi

case "$COMMAND" in
    prices) cmd_prices ;;
    create) cmd_create ;;
    status) cmd_status ;;
    destroy) cmd_destroy "$@" ;;
    '')
        echo "hetzner_box: one of the four subcommands is required" >&2
        usage
        exit 2
        ;;
    *)
        echo "hetzner_box: '$COMMAND' is not a subcommand of this script" >&2
        usage
        exit 2
        ;;
esac
