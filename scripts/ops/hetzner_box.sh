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

# cax11 is the target of decision D-01 and it is what the store claim talks
# about. On 2026-09-03 all four arm types of this provider were out of stock in
# every european location, so the owner decided to run the rehearsal on the x86
# machine of the same size and to repeat the core measurement on arm once the
# stock returns. Both runs are wanted, and the report keeps their numbers apart.
# Switching back is this one word, because everything that follows is read from
# the API rather than repeated here. On 2026-09-04 the stock returned and this
# word was switched back for the arm run; the rehearsal ran on cpx22 and its
# numbers stay in the report next to these.
SERVER_TYPE='cax11'
SERVER_IMAGE='ubuntu-24.04'
# Helsinki, because decision D-01 of the phase names that location. The earlier
# value here was nbg1, taken from the example request of the research document;
# the price is the same in all three cax locations (7.1281 EUR per month, gross,
# read from this account), so this is a choice and not a cost. It is corrected
# before the first create, because the location of a server cannot be changed
# afterwards: a box in the wrong region costs a destroy and a create.
SERVER_LOCATION='hel1'
# Without the architecture in it, on purpose: the same script rents the x86
# rehearsal and the arm repeat, and a box called arm that is not one is a trap
# for whoever opens the console next.
SERVER_NAME='findling-loadtest'
# The key is injected by name, and the name has to exist in the account. Hetzner
# puts only the keys of this one request into the machine, so a create without
# this field produces a box that is reachable by password over the web console
# and by nothing else. The AIO run needs an ssh tunnel, so that would not do.
SSH_KEY_NAME='khaled-windows-ed25519'
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
print("%-8s %5s %7s %6s %-8s %-26s %s" % (
    "name", "cores", "memory", "disk", "arch", "price per month, gross", "in stock"))
for server_type in payload["server_types"]:
    if not server_type["name"].startswith("cax"):
        continue
    monthly = {price["location"]: price["price_monthly"]["gross"] for price in server_type["prices"]}
    one_price = sorted(set(monthly.values()))
    price_column = one_price[0] if len(one_price) == 1 else ", ".join(
        "%s %s" % (location, value) for location, value in sorted(monthly.items())
    )
    # Availability is a property of the type in this API, it differs per
    # location, and it moves without notice. It is printed next to the price
    # because a price for a machine nobody can rent is half the answer. This
    # flag and not /datacenters: the two disagreed on 2026-09-04 and this one
    # was right, see the note in cmd_create.
    in_stock = [
        location["name"] for location in server_type.get("locations", []) if location.get("available")
    ]
    print(
        "%-8s %5s %6s G %5s G %-8s %-26s %s"
        % (
            server_type["name"],
            server_type["cores"],
            server_type["memory"],
            server_type["disk"],
            server_type["architecture"],
            price_column,
            ", ".join(in_stock) if in_stock else "nowhere",
        )
    )
'
    echo "hetzner_box: these are the prices of this account, not of a web search"
    echo "hetzner_box: in stock is read at this moment and it changes without notice"
}

cmd_create() {
    require_token
    require_tools

    if read_state; then
        echo "hetzner_box: $STATE_FILE already names server ${SERVER_ID:-?}" >&2
        echo "run status, or destroy first: two boxes are two invoices" >&2
        exit 1
    fi

    # Stock first, because it is the one precondition that no amount of correct
    # arguments can fix. When the arm types are gone the API answers a create
    # with "unsupported location for server type", which reads like a mistake in
    # this script and sends the next reader to the location field. It is not:
    # capacity is a state of the account's region, and the only cure is to wait.
    #
    # Two endpoints answer the stock question and they do not agree, so this
    # names which one is believed and why. The live answer is the per location
    # availability flag on the server type: on 2026-09-04 it stood false for
    # cax11 in all three european locations, and two create attempts, hel1 and
    # nbg1, were refused with "unsupported location for server type". The same
    # flag stood true for cpx22 in hel1, which is the machine that actually ran
    # the day before. The flag tells the truth.
    #
    # /datacenters at that same minute listed cax11 as available in hel1-dc2 and
    # nbg1-dc3. It was wrong, and it is wrong because that endpoint is on its way
    # out: the datacenter field of a create was removed on 2025-12-16 and now
    # answers "datacenter is deprecated and cannot be used anymore". An endpoint
    # nobody can act on is an endpoint nobody keeps current.
    #
    # It is still queried here, for one purpose: when the two disagree, the
    # disagreement is printed. Otherwise the next person reads the cheerful half
    # of the API, believes the machine is there, and spends an hour looking for
    # the mistake in this script.
    types=$(api GET "/server_types?name=$SERVER_TYPE")
    fail_on_error "$types"
    datacenters=$(api GET /datacenters)
    fail_on_error "$datacenters"
    stock=$(printf '[%s,%s]' "$types" "$datacenters" | json "
import json
import sys

answers = json.load(sys.stdin)
server_types = answers[0]['server_types']
if not server_types:
    print('missing')
    raise SystemExit(0)
server_type = server_types[0]
available = [
    location['name']
    for location in server_type.get('locations', [])
    if location.get('available')
]
if '$SERVER_LOCATION' in available:
    print('here')
elif available:
    print('elsewhere ' + ' '.join(available))
else:
    claimed = [
        datacenter['name']
        for datacenter in answers[1]['datacenters']
        if server_type['id'] in datacenter['server_types'].get('available', [])
    ]
    print(('nowhere ' + ' '.join(claimed)).strip())
")
    claimed_by_datacenters="${stock#nowhere}"
    case "$stock" in
    here)
        echo "hetzner_box: $SERVER_TYPE is in stock in $SERVER_LOCATION"
        ;;
    missing)
        echo "hetzner_box: this account does not know a server type called $SERVER_TYPE" >&2
        exit 1
        ;;
    nowhere*)
        echo "hetzner_box: $SERVER_TYPE is out of stock in every location right now" >&2
        echo "this is capacity, not a wrong argument: the type carries availability" >&2
        echo "false everywhere, and it returns without an announcement" >&2
        if [ -n "$claimed_by_datacenters" ]; then
            echo "note: /datacenters disagrees and claims$claimed_by_datacenters" >&2
            echo "do not believe it, it was measured wrong on 2026-09-04 and that" >&2
            echo "endpoint is being retired; a create there is refused with" >&2
            echo "'unsupported location for server type'" >&2
        fi
        echo "watch it with: hetzner_box.sh prices, then run create again" >&2
        exit 1
        ;;
    *)
        echo "hetzner_box: $SERVER_TYPE is out of stock in $SERVER_LOCATION" >&2
        echo "in stock right now: ${stock#elsewhere }" >&2
        echo "the location of a box cannot be changed afterwards, so moving the run" >&2
        echo "is a decision and not a retry: change SERVER_LOCATION on purpose" >&2
        exit 1
        ;;
    esac

    # The key is looked up before anything is created. A box that came up without
    # a key cannot be given one later without reinstalling it, so the cheap check
    # belongs in front of the expensive request.
    keys=$(api GET "/ssh_keys?name=$SSH_KEY_NAME")
    fail_on_error "$keys"
    key_line=$(printf '%s' "$keys" | json '
import json
import sys

keys = json.load(sys.stdin)["ssh_keys"]
if len(keys) == 1:
    print("%s %s" % (keys[0]["id"], keys[0]["fingerprint"]))
')
    if [ -z "$key_line" ]; then
        echo "hetzner_box: this account has no ssh key named $SSH_KEY_NAME" >&2
        echo "without it the box would only take a password over the web console," >&2
        echo "and the AIO interface of the load test is reached through an ssh tunnel" >&2
        exit 1
    fi
    echo "hetzner_box: injecting ssh key $SSH_KEY_NAME, $key_line"

    # Same reason as the key, one line further: the name ubuntu-24.04 exists
    # twice in every account, once for x86 and once for arm, and the wrong half
    # of it does not boot on this machine. The architecture is not repeated as a
    # constant but read off the server type, so that changing the type is one
    # word and cannot leave a mismatched image behind.
    architecture=$(printf '%s' "$types" | json "
import json
import sys

server_types = json.load(sys.stdin)['server_types']
print(server_types[0]['architecture'] if server_types else '')
")
    if [ -z "$architecture" ]; then
        echo "hetzner_box: the API did not state an architecture for $SERVER_TYPE" >&2
        exit 1
    fi
    images=$(api GET "/images?name=$SERVER_IMAGE&architecture=$architecture&status=available")
    fail_on_error "$images"
    image_id=$(printf '%s' "$images" | json '
import json
import sys

images = json.load(sys.stdin)["images"]
if len(images) == 1:
    print(images[0]["id"])
')
    if [ -z "$image_id" ]; then
        echo "hetzner_box: no single available $SERVER_IMAGE image for $architecture in this account" >&2
        exit 1
    fi
    echo "hetzner_box: image $SERVER_IMAGE for $architecture is id $image_id"

    # The location and not the datacenter, and that is no longer a choice: the
    # datacenter field was removed on 2025-12-16 and a create that carries it is
    # refused with "datacenter is deprecated and cannot be used anymore". Tried
    # on 2026-09-04, when /datacenters looked like the better informed endpoint.
    server_body=$(
        printf '{"name":"%s","server_type":"%s","image":%s,"location":"%s"' \
            "$SERVER_NAME" "$SERVER_TYPE" "$image_id" "$SERVER_LOCATION"
        printf ',"ssh_keys":["%s"]' "$SSH_KEY_NAME"
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

    # The firewall sits outside the machine on purpose. A rule set on the box
    # itself does not hold here: docker writes its published ports straight into
    # iptables and walks past ufw, so the interface of AIO on 8080 would be open
    # to the world while ufw reports it closed. This one filters before the
    # packet reaches the host, and it knows nothing about docker (T-05-40).
    firewall_body=$(
        printf '{"name":"%s-fw","labels":{"%s":"%s"},"rules":[' \
            "$SERVER_NAME" "${LABEL%%=*}" "${LABEL#*=}"
        printf '{"direction":"in","protocol":"tcp","port":"22","source_ips":["0.0.0.0/0","::/0"]},'
        printf '{"direction":"in","protocol":"tcp","port":"80","source_ips":["0.0.0.0/0","::/0"]},'
        printf '{"direction":"in","protocol":"tcp","port":"443","source_ips":["0.0.0.0/0","::/0"]},'
        printf '{"direction":"in","protocol":"icmp","source_ips":["0.0.0.0/0","::/0"]}],'
        printf '"apply_to":[{"type":"server","server":{"id":%s}}]}' "$server_id"
    )
    echo "hetzner_box: firewall with 22, 80, 443 and nothing else"
    response=$(api POST /firewalls "$firewall_body")
    fail_on_error "$response"
    firewall_id=$(printf '%s' "$response" | json 'import json,sys; print(json.load(sys.stdin)["firewall"]["id"])')

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
            echo "FIREWALL_ID=$firewall_id"
            echo "CREATED_AT=$created_at"
            echo "CREATED_ISO=$created_iso"
        } >"$STATE_FILE"
    )

    echo "hetzner_box: server=$server_id volume=$volume_id firewall=$firewall_id ipv4=$server_ip created=$created_iso"
    echo "hetzner_box: state in $STATE_FILE, label $LABEL on all three resources"
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
    # The three answers are handed over as one array and not as three lines. The
    # real API pretty prints its JSON, so a reader that takes one line per answer
    # gets an opening brace and nothing else. Against a stub that answers in a
    # single line this looked like it worked.
    printf '[%s,%s,%s]' "$server" "$volume" "$pricing" | json "
import json
import sys

answers = json.load(sys.stdin)
server = answers[0]['server']
volume = answers[1]['volume']
pricing = answers[2]['pricing']

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

# The public address is a separate item on the invoice, and it is not small
# against a box that costs one cent an hour: leaving it out understates the run
# by roughly eight percent. It is counted when the box actually has one.
ipv4_hourly = 0.0
ipv4_monthly = 0.0
if (server['public_net'] or {}).get('ipv4'):
    for entry in pricing.get('primary_ips', []):
        if entry['type'] != 'ipv4':
            continue
        for price in entry['prices']:
            if price['location'] != '$SERVER_LOCATION':
                continue
            ipv4_hourly = float(price['price_hourly']['gross'])
            ipv4_monthly = float(price['price_monthly']['gross'])

spent = hours * (server_hourly + volume_hourly + ipv4_hourly)

print('server  %s %s %s' % (server['id'], server['name'], server['status']))
print('volume  %s %s %s G attached to %s' % (
    volume['id'], volume['name'], volume['size'], volume['server']))
print('running %.1f hours since $CREATED_ISO' % hours)
print('price   %.4f %s per hour for the box, %.4f for the volume, %.4f for the address' % (
    server_hourly, currency, volume_hourly, ipv4_hourly))
print('month   %.2f %s box, %.2f %s volume, %.2f %s address' % (
    server_monthly, currency, volume_monthly, currency, ipv4_monthly, currency))
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

# Everywhere else in this script an empty answer means the request never arrived,
# and that is worth an error. Not here: a successful delete answers either with an
# action object or, as the volume endpoint does, with 204 and no body at all. If
# the empty case were reported as a failure, the one step that has to be trusted
# would print a sentence that sounds like a lost volume every single time, and an
# operator learns fast to stop reading the output of destroy.
delete_error() {
    if [ -z "$1" ]; then
        return 0
    fi
    api_error "$1"
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
        if [ -n "$(delete_error "$response")" ]; then
            echo "hetzner_box: the volume was not deleted yet: $(delete_error "$response")" >&2
        fi
    fi

    echo "hetzner_box: deleting server $server_id"
    response=$(api DELETE "/servers/$server_id")
    if [ -n "$(delete_error "$response")" ]; then
        echo "hetzner_box: the server was not deleted: $(delete_error "$response")" >&2
    fi

    # A second attempt at the volume, for the case above where the server had to
    # go first to get it detached.
    if [ -n "$volume_id" ] && [ "$(gone "$(api GET "/volumes/$volume_id")")" != "gone" ]; then
        api DELETE "/volumes/$volume_id" >/dev/null
    fi

    # The firewall costs nothing, which is exactly why it is the resource that
    # stays behind. It is deleted by id when the state file names one, and in
    # any case every firewall carrying the label is swept up: a run that was
    # torn down by hand once leaves no state file behind, and the label is then
    # the only thread left (T-05-39). A firewall cannot be deleted while it is
    # applied to a server, so this happens after the server is gone.
    firewall_id="${FIREWALL_ID:-}"
    if [ -z "$firewall_id" ]; then
        firewall_id=$(api GET "/firewalls?label_selector=$LABEL" | json '
import json
import sys

try:
    firewalls = json.load(sys.stdin)["firewalls"]
except (ValueError, KeyError):
    firewalls = []
print(" ".join(str(firewall["id"]) for firewall in firewalls))
')
    fi
    firewall_state='gone'
    for one_firewall in $firewall_id; do
        echo "hetzner_box: deleting firewall $one_firewall"
        response=$(api DELETE "/firewalls/$one_firewall")
        if [ -n "$(delete_error "$response")" ]; then
            echo "hetzner_box: the firewall was not deleted: $(delete_error "$response")" >&2
        fi
        if [ "$(gone "$(api GET "/firewalls/$one_firewall")")" != "gone" ]; then
            firewall_state='there'
        fi
    done

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
    if [ "$firewall_state" = "gone" ]; then
        echo "hetzner_box: firewall ${firewall_id:-none} is gone, verified against the API"
    else
        echo "hetzner_box: firewall $firewall_id is still there" >&2
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
    echo "hetzner_box: every resource of this run is gone and $STATE_FILE is removed"
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
