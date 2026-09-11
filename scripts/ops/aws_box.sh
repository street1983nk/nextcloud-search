#!/bin/sh
# The arm box of the load test, on AWS, plus its data volume and its teardown.
#
# The counterpart of scripts/ops/hetzner_box.sh, and it exists because the box
# it rents could not be rented. Decision D-01 of phase 5 names a Hetzner CAX11,
# 2 vCPU arm and 4 GB, because that is the machine the store claim talks about.
# On 2026-09-03 and again on 2026-09-04 no arm type of that provider was
# available in any european location, and the owner established by telephone on
# 2026-09-04 that the shortage runs for months. So the run moved to a machine of
# the same shape somewhere else:
#
#     m7g.large, 2 vCPU Graviton3, eu-central-1c, Ubuntu 24.04 arm64
#     memory capped to 4 GB by the kernel, because the type carries 8 GB
#
# The cap is the whole point and it is not cosmetic. A measurement on 8 GB says
# nothing about a 4 GB box, because what is being measured is the distance to
# the ceiling: the page cache of the index, the heap of tesseract and the base
# load of AIO all compete for exactly the memory that is not there. The cap sits
# in a drop-in at /etc/default/grub.d/99-mem4g.cfg, it extends
# GRUB_CMDLINE_LINUX_DEFAULT rather than replacing it (the console parameters of
# the cloud image have to survive), and it is read back before every run:
# free -h says 3.9Gi, nproc says 2, uname -m says aarch64.
#
# Eight subcommands, and none of them creates a machine by itself:
#
#     prices    what this account is charged for the box and the volume
#     create    what created the box, said in words, and a refusal to do it again
#     volume    the 60 GB data volume: create, tag, attach
#     status    what is running, for how long, and what it has cost so far
#     stop      park the box and write the closing figures of the uptime down
#     start     wake it, read the new address, move the ssh rule onto the
#               current address of the owner, and name what is left to pull along
#     snapshot  the corpus of the run, out of the volume and into a snapshot that
#               outlives the box, verified by a read back and not by a waiter
#     destroy   volume, instance and security group, with a check that all
#               three are gone and a sweep by tag
#
# stop and start were missing until 2026-09-07, and the box lived exactly between
# them: parked after the run of 06-11, woken by hand for the one of 06.1-18. A
# box that is driven past this script is also driven past its cost arithmetic,
# which is why the two are here now and why stop writes the uptime it closes into
# the state file. A stopped instance keeps a LaunchTime, so the figure has to be
# taken before the call that stops it or it is simply wrong.
#
# The two credentials come out of the environment and are never printed, never
# written into the state file and never handed to a command line: the CLI reads
# them from the environment itself, so this script mentions each of them exactly
# once, in the check that they are set at all (T-05-17).
#
# Every resource this script creates carries the tag purpose=findling-phase5.
# In an account that holds other things a tag is the only way to find something
# that was forgotten, and destroy searches by exactly that tag (T-05-19).
#
# With one deliberate exception since 11-12: the snapshot of the corpus carries
# purpose=findling-corpus-keep, because it is the one resource of this run that
# is meant to outlive the box. Under the other tag the sweep of destroy would
# report it as a leftover and end a correct teardown red (T-11-52).
#
# Rate limits, as a house rule since 2026-09-04: every loop in here that waits
# for AWS uses the waiters of the CLI, which poll on a fixed interval of 15
# seconds and give up after a bounded number of tries. No hand rolled busy loop,
# because a diagnostic run that asked a foreign API sixty times a minute is what
# earned this repository the rule.
#
# Usage: AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... aws_box.sh <prices|create|volume|status|stop|start|snapshot|destroy>

set -eu

# The development machine of this project is Windows, and Git for Windows
# rewrites every argument that looks like a unix path into a windows path before
# the program sees it. That turned the device name /dev/sdf into
# C:/Program Files/Git/dev/sdf, and the api refused the attach with a message
# that names the value and not the cause. Switching the rewriting off for this
# process costs nothing anywhere else, because no argument in this script is a
# path on the machine that runs it.
MSYS2_ARG_CONV_EXCL='*'
export MSYS2_ARG_CONV_EXCL

REGION='eu-central-1'
# The zone and not just the region: a volume can only be attached to an instance
# in its own availability zone, and it cannot be moved afterwards. The box lives
# in eu-central-1c, so the volume has to be created there.
ZONE='eu-central-1c'
INSTANCE_TYPE='m7g.large'
INSTANCE_NAME='findling-loadtest'
# The image the box actually booted from, kept here because create documents
# what happened rather than guessing what would happen: Ubuntu 24.04 arm64.
INSTANCE_IMAGE='ami-0e79e661e73ddfac9'
SSH_KEY_NAME='findling-loadtest'
SECURITY_GROUP_NAME='findling-loadtest'
# 60 GB and not the 50 of the Hetzner run. The corpus of the full run weighs
# 20 GB, next to it live the index, the images of eight containers and the data
# directory of Nextcloud, and the root disk of this box is 40 GB on purpose,
# because the CAX11 it stands in for has 40 GB as well.
VOLUME_NAME='findling-corpus'
VOLUME_SIZE_GB=60
VOLUME_TYPE='gp3'
# The device name the api is asked for. Nitro instances ignore it and expose the
# volume as a /dev/nvme?n1 in attachment order, so nothing in this run may rely
# on this string; the volume is found by its size and by its uuid in the fstab.
VOLUME_DEVICE='/dev/sdf'
ROOT_DISK_GB=40
TAG_KEY='purpose'
TAG_VALUE='findling-phase5'
LABEL="$TAG_KEY=$TAG_VALUE"
# The second tag value, and the only one this script gives to something that is
# supposed to stay: findling-corpus-keep. See the paragraph about the sweep
# above, and cmd_destroy, which asks for it by name.
KEEP_TAG_VALUE='findling-corpus-keep'
SNAPSHOT_NAME='findling-corpus-2026-09'
# What the snapshot is of, in the words the report uses: the corpus of the load
# test and the index built over it, in the shape the comparison measurement of
# 2026-09-10 left behind.
SNAPSHOT_DESCRIPTION='findling corpus and index, v1.1 comparison run 2026-09-10, 52111 documents'

# Outside the working tree, same reason as in the Hetzner tool: a state file in
# the repository is one careless git add away from a public commit.
STATE_DIR="${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}"
STATE_FILE="$STATE_DIR/box.env"

# Read from the public price list of this provider, the bulk api that needs no
# credentials, version 20260903195206 of the eu-central-1 file for AmazonEC2,
# effective 2026-09-01, filtered on the box on 2026-09-04:
#
#     $0.0978 per On Demand Linux m7g.large Instance Hour
#     $0.0952 per GB-month of General Purpose (gp3) provisioned storage
#
# The third one comes from the price list of AmazonVPC, version 20260831092232,
# and it is the item that is easy to miss:
#
#     $0.005 per In-use public IPv4 address per hour
#
# The public address has been its own line on an AWS invoice since 2024-02-01,
# exactly as it has been at Hetzner since 2024, and the Hetzner half of this
# report once understated a run by eight percent for leaving it out. Against
# this box it is five percent, and it is counted.
#
# All three are net USD. That is not the same measure as the gross EUR of the
# Hetzner table in docs/performance.md, and the report says so rather than
# converting the two into a comparison that neither of them supports.
#
# They are pinned here instead of fetched, because the regional price list is
# well over a gigabyte: a tool that downloads that when somebody types "prices"
# is a trap. The command that reproduces them stands in cmd_prices, and the
# filtered rows are in docs/measurements/ next to the run.
PRICE_INSTANCE_HOURLY='0.0978'
PRICE_GP3_GB_MONTH='0.0952'
PRICE_IPV4_HOURLY='0.0050'
PRICE_CURRENCY='USD'
# AWS states monthly storage prices against a 730 hour month.
HOURS_PER_MONTH=730

usage() {
    echo "usage: aws_box.sh <prices|create|volume|status|stop|start|snapshot|destroy>" >&2
    echo "  prices   the facts of the instance type and the pinned rates" >&2
    echo "  create   how the box was created, and why this refuses to repeat it" >&2
    echo "  volume   create the ${VOLUME_SIZE_GB} GB data volume and attach it" >&2
    echo "  status   state, run time and the cost so far" >&2
    echo "  stop     park the box, then write the uptime and its cost down" >&2
    echo "  start    wake it, print the new address, move the ssh rule along" >&2
    echo "  snapshot snapshot the data volume of a stopped box, then read it back" >&2
    echo "  destroy  delete volume, instance and security group, then verify" >&2
    printf 'the credentials are read from the environment: %s and %s\n' \
        'AWS_ACCESS_KEY_ID' 'AWS_SECRET_ACCESS_KEY' >&2
}

require_credentials() {
    # The only two places these names appear. The CLI picks the values up from
    # the environment on its own, so no value ever reaches an argument, a log or
    # this state file.
    : "${AWS_ACCESS_KEY_ID:?access key fehlt}"
    : "${AWS_SECRET_ACCESS_KEY:?secret key fehlt}"
}

AWS_BIN=''

require_tools() {
    if [ -n "${AWS_CLI:-}" ]; then
        AWS_BIN="$AWS_CLI"
    elif command -v aws >/dev/null 2>&1; then
        AWS_BIN='aws'
    elif [ -x '/c/Program Files/Amazon/AWSCLIV2/aws.exe' ]; then
        # The development machine of this project is Windows, where the CLI is
        # installed but not on the path of the shell that runs this script.
        AWS_BIN='/c/Program Files/Amazon/AWSCLIV2/aws.exe'
    else
        echo "aws_box: the aws cli is required and not on the path" >&2
        echo "point AWS_CLI at it if it lives somewhere unusual" >&2
        exit 1
    fi
    for tool in python3 date sed; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            echo "aws_box: $tool is required and not on the path" >&2
            exit 1
        fi
    done
}

# One call. Region and output format are fixed here so that no caller can
# accidentally read a different region than the one the box lives in.
ec2() {
    "$AWS_BIN" --region "$REGION" --output json ec2 "$@"
}

# The same call, but a failure is an answer rather than an abort: the deletion
# path needs to read the error code of a resource that is already gone.
ec2_soft() {
    "$AWS_BIN" --region "$REGION" --output json ec2 "$@" 2>&1 || true
}

json() {
    python3 -c "$1"
}

read_state() {
    if [ ! -r "$STATE_FILE" ]; then
        return 1
    fi
    # shellcheck source=/dev/null
    . "$STATE_FILE"
    return 0
}

require_state() {
    if ! read_state; then
        echo "aws_box: no state file at $STATE_FILE" >&2
        echo "this box was created by hand, so the file is the only record of it" >&2
        exit 1
    fi
    : "${BOX_INSTANCE_ID:?instance id fehlt in $STATE_FILE}"
}

cmd_prices() {
    require_credentials
    require_tools
    response=$(ec2 describe-instance-types --instance-types "$INSTANCE_TYPE")
    printf '%s' "$response" | json "
import json
import sys

instance_type = json.load(sys.stdin)['InstanceTypes'][0]
memory_mib = instance_type['MemoryInfo']['SizeInMiB']
print('type      %s' % instance_type['InstanceType'])
print('cores     %s vCPU, %s, %s GHz sustained' % (
    instance_type['VCpuInfo']['DefaultVCpus'],
    instance_type['ProcessorInfo'].get('SupportedArchitectures', ['?'])[0],
    instance_type['ProcessorInfo'].get('SustainedClockSpeedInGhz', '?'),
))
print('memory    %s MiB on the type, capped to 4096 MiB by the kernel' % memory_mib)
print('network   %s' % instance_type['NetworkInfo']['NetworkPerformance'])
"
    echo "disk      ${ROOT_DISK_GB} GB gp3 root, ${VOLUME_SIZE_GB} GB gp3 data volume"
    echo "rate      $PRICE_INSTANCE_HOURLY $PRICE_CURRENCY per hour for the box, net"
    echo "rate      $PRICE_GP3_GB_MONTH $PRICE_CURRENCY per GB and month for gp3, net"
    echo "rate      $PRICE_IPV4_HOURLY $PRICE_CURRENCY per hour for the public address, net"
    echo "aws_box: the two rates are pinned in this script, with their source"
    echo "aws_box: this account cannot read the price api (pricing:GetProducts is"
    echo "not in its policy), so they come from the public bulk price list:"
    echo "  curl -sS https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/eu-central-1/index.csv"
    echo "  | grep -E 'm7g[.]large|VolumeUsage[.]gp3' | grep OnDemand"
    echo "aws_box: a gp3 volume carries 3000 IOPS and 125 MB/s at no extra charge,"
    echo "and this run stays inside both, so nothing is added for them"
}

cmd_create() {
    # This subcommand deliberately creates nothing. The box of this run was
    # created by hand on 2026-09-04, while the question was still open whether
    # arm capacity would return at the other provider, and a second box would be
    # a second invoice and a second machine nobody watches.
    #
    # What it does instead is name the calls that produced the machine, so that
    # the run is reproducible from this repository and not from a shell history
    # on a laptop. Everything below was really executed, in this order.
    cat <<'RECIPE'
aws_box: the box of this run exists already and this command will not make one.
It records how it came about. To repeat the run on a fresh machine, read this,
check it against the current api, and run it by hand:

  # 1. a security group with ssh from one address and nothing else open to it
  aws ec2 create-security-group --group-name findling-loadtest \
      --description "findling load test" --vpc-id <default vpc>
  aws ec2 authorize-security-group-ingress --group-id <sg> \
      --ip-permissions \
      'IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=<your address>/32}]' \
      'IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=0.0.0.0/0}]' \
      'IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges=[{CidrIp=0.0.0.0/0}]'

  # 2. a key pair whose private half never leaves the machine that made it
  aws ec2 create-key-pair --key-name findling-loadtest \
      --query KeyMaterial --output text > ~/.ssh/findling-loadtest

  # 3. the instance: arm64 image, 40 GB gp3 root, one subnet in eu-central-1c
  aws ec2 run-instances --image-id ami-0e79e661e73ddfac9 \
      --instance-type m7g.large --key-name findling-loadtest \
      --security-group-ids <sg> --subnet-id <subnet in eu-central-1c> \
      --block-device-mappings \
      'DeviceName=/dev/sda1,Ebs={VolumeSize=40,VolumeType=gp3,DeleteOnTermination=true}' \
      --tag-specifications \
      'ResourceType=instance,Tags=[{Key=Name,Value=findling-loadtest},{Key=purpose,Value=findling-phase5}]'

  # 4. the memory cap, on the box, as a drop-in that extends the cmdline
  #    instead of replacing it, then reboot and read the three numbers back
  echo 'GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT mem=4G"' \
      | sudo tee /etc/default/grub.d/99-mem4g.cfg
  sudo update-grub && sudo reboot
  free -h   # 3.9Gi
  nproc     # 2
  uname -m  # aarch64

  # 5. the data volume, which this script does do:
  aws_box.sh volume

The state of the box lives in $HOME/.findling-loadtest/box.env, written by hand
for the parts above and by this script for the volume.
RECIPE
    exit 1
}

cmd_volume() {
    require_credentials
    require_tools
    require_state

    if [ -n "${VOLUME_ID:-}" ]; then
        echo "aws_box: $STATE_FILE already names volume $VOLUME_ID" >&2
        echo "run status, or destroy first: two volumes are two invoices" >&2
        exit 1
    fi

    # An unattached volume that already carries the tag is picked up instead of
    # creating a second one. This is not convenience: the first run of this
    # subcommand created the volume and then failed on the attach, and a retry
    # that starts with create-volume leaves the first one behind as an invoice
    # nobody is watching. The search is limited to the zone of the box, because
    # a volume in another zone could never be attached to it anyway.
    volume_id=$(ec2 describe-volumes \
        --filters "Name=tag:$TAG_KEY,Values=$TAG_VALUE" \
        "Name=availability-zone,Values=$ZONE" \
        "Name=status,Values=available" | json '
import json
import sys

volumes = json.load(sys.stdin)["Volumes"]
print(volumes[0]["VolumeId"] if len(volumes) == 1 else "")
')
    if [ -n "$volume_id" ]; then
        echo "aws_box: an unattached volume with the tag exists, using $volume_id"
    else
        echo "aws_box: creating a ${VOLUME_SIZE_GB} GB $VOLUME_TYPE volume in $ZONE"
        response=$(ec2 create-volume \
            --availability-zone "$ZONE" \
            --size "$VOLUME_SIZE_GB" \
            --volume-type "$VOLUME_TYPE" \
            --tag-specifications \
            "ResourceType=volume,Tags=[{Key=Name,Value=$VOLUME_NAME},{Key=$TAG_KEY,Value=$TAG_VALUE}]")
        volume_id=$(printf '%s' "$response" | json 'import json,sys; print(json.load(sys.stdin)["VolumeId"])')
    fi

    echo "aws_box: waiting for volume $volume_id to become available"
    "$AWS_BIN" --region "$REGION" ec2 wait volume-available --volume-ids "$volume_id"

    echo "aws_box: attaching $volume_id to $BOX_INSTANCE_ID as $VOLUME_DEVICE"
    ec2 attach-volume --volume-id "$volume_id" --instance-id "$BOX_INSTANCE_ID" \
        --device "$VOLUME_DEVICE" >/dev/null
    "$AWS_BIN" --region "$REGION" ec2 wait volume-in-use --volume-ids "$volume_id"

    # The state file was written by hand for the instance, so this appends
    # rather than rewriting: losing the instance id here would lose the only
    # record of a machine that costs money.
    (
        umask 077
        {
            echo "VOLUME_ID=$volume_id"
            echo "VOLUME_NAME=$VOLUME_NAME"
            echo "VOLUME_SIZE_GB=$VOLUME_SIZE_GB"
            echo "VOLUME_TYPE=$VOLUME_TYPE"
            echo "VOLUME_CREATED_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        } >>"$STATE_FILE"
    )
    echo "aws_box: volume=$volume_id noted in $STATE_FILE, tag $LABEL"
    echo "aws_box: nitro exposes it as a nvme device and ignores $VOLUME_DEVICE,"
    echo "so find it by size on the box and mount it by uuid, never by name"
}

cmd_status() {
    require_credentials
    require_tools

    if ! read_state; then
        echo "aws_box: no state file at $STATE_FILE, searching by tag $LABEL" >&2
        response=$(ec2 describe-tags --filters "Name=tag:$TAG_KEY,Values=$TAG_VALUE")
        printf '%s' "$response" | json "
import json
import sys

tags = json.load(sys.stdin)['Tags']
if not tags:
    print('nothing in this region carries the tag, so nothing of this test is up')
for tag in tags:
    print('%s %s' % (tag['ResourceType'], tag['ResourceId']))
"
        return 0
    fi

    instance=$(ec2 describe-instances --instance-ids "$BOX_INSTANCE_ID")
    volumes=$(ec2 describe-volumes --filters "Name=attachment.instance-id,Values=$BOX_INSTANCE_ID")
    now=$(date -u +%s)
    printf '[%s,%s]' "$instance" "$volumes" | json "
import datetime
import json
import sys

answers = json.load(sys.stdin)
instance = answers[0]['Reservations'][0]['Instances'][0]
volumes = answers[1]['Volumes']

launched = instance['LaunchTime']
if isinstance(launched, str):
    launched = datetime.datetime.fromisoformat(launched)
hours = ($now - launched.timestamp()) / 3600.0
state = instance['State']['Name']
# The same trap cmd_stop is built around, one subcommand further along: a stopped
# instance keeps answering with the LaunchTime of its last start, so the distance
# from it to now counts every parked hour as an hour of uptime. On 2026-09-09 this
# reported 52.3 hours and 5.80 USD for a box that had run 1.95 hours and been
# parked since 2026-09-07T06:56:42Z. The figure looked right and was not, and it
# is the figure a cost ceiling gets checked against, so it is only an uptime while
# the instance is actually running.
running = state == 'running'

print('instance  %s %s %s in %s' % (
    instance['InstanceId'],
    instance['InstanceType'],
    state,
    instance['Placement']['AvailabilityZone'],
))
print('address   %s' % instance.get('PublicIpAddress', 'none'))
gigabytes = 0
for volume in sorted(volumes, key=lambda entry: entry['Size']):
    gigabytes += volume['Size']
    print('volume    %s %s G %s %s IOPS %s MB/s' % (
        volume['VolumeId'], volume['Size'], volume['VolumeType'],
        volume.get('Iops', '?'), volume.get('Throughput', '?'),
    ))
if running:
    print('running   %.1f hours since %s' % (hours, launched.isoformat()))
else:
    print('running   no, this instance is %s' % state)
    print('running   last launch %s, and the %.1f hours since it are NOT an uptime:' % (
        launched.isoformat(), hours))
    print('running   a stopped instance keeps its LaunchTime. The closing figures of')
    print('running   the last uptime were written into box.env by aws_box.sh stop')

instance_hourly = float('$PRICE_INSTANCE_HOURLY')
storage_hourly = float('$PRICE_GP3_GB_MONTH') * gigabytes / $HOURS_PER_MONTH
# Counted when the box really has an address, and not otherwise. Leaving it out
# understated the Hetzner half of this report by eight percent once.
ipv4_hourly = float('$PRICE_IPV4_HOURLY') if instance.get('PublicIpAddress') else 0.0
print('rate      %.6f %s per hour for the box, %.6f for %s GB of storage, %.6f for the address' % (
    instance_hourly, '$PRICE_CURRENCY', storage_hourly, gigabytes, ipv4_hourly))
if running:
    print('spent     %.2f %s so far, net, from the pinned public rates' % (
        hours * (instance_hourly + storage_hourly + ipv4_hourly), '$PRICE_CURRENCY'))
else:
    print('spent     %.4f %s per day while parked, net, the disks and nothing else' % (
        storage_hourly * 24.0, '$PRICE_CURRENCY'))
    print('spent     this subcommand does not add the parked days up: the day the box')
    print('spent     was parked stands in box.env as BOX_STOPPED_ISO')
"
    echo "aws_box: the public address is its own item on an AWS invoice since"
    echo "2024-02-01 and it is counted above, because it is five percent of this"
    echo "run and the Hetzner half of this report once left it out"
    echo "aws_box: the closing figure of the report comes from this rate times"
    echo "the run time, and the source of the rate is aws_box.sh prices"
}

cmd_stop() {
    require_credentials
    require_tools
    require_state

    # Read before the call that parks it. A stopped instance still answers with a
    # LaunchTime, but the uptime that time belongs to is over by then, so an
    # arithmetic that reads afterwards reports the wrong number and keeps
    # reporting it, because the state file is what the next report quotes.
    instance=$(ec2 describe-instances --instance-ids "$BOX_INSTANCE_ID")
    volumes=$(ec2 describe-volumes --filters "Name=attachment.instance-id,Values=$BOX_INSTANCE_ID")
    now=$(date -u +%s)
    parked_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    figures=$(printf '[%s,%s]' "$instance" "$volumes" | json "
import datetime
import json
import sys

answers = json.load(sys.stdin)
instance = answers[0]['Reservations'][0]['Instances'][0]
volumes = answers[1]['Volumes']

launched = instance['LaunchTime']
if isinstance(launched, str):
    launched = datetime.datetime.fromisoformat(launched)
hours = ($now - launched.timestamp()) / 3600.0
gigabytes = sum(volume['Size'] for volume in volumes)

instance_hourly = float('$PRICE_INSTANCE_HOURLY')
storage_hourly = float('$PRICE_GP3_GB_MONTH') * gigabytes / $HOURS_PER_MONTH
# Same rule as in status: the address is only charged while the box has one.
ipv4_hourly = float('$PRICE_IPV4_HOURLY') if instance.get('PublicIpAddress') else 0.0
print('%s %.2f %.4f %.4f %s' % (
    instance['State']['Name'],
    hours,
    hours * (instance_hourly + storage_hourly + ipv4_hourly),
    storage_hourly * 24.0,
    gigabytes,
))
")
    state_before=$(printf '%s' "$figures" | cut -d' ' -f1)
    uptime_hours=$(printf '%s' "$figures" | cut -d' ' -f2)
    uptime_cost=$(printf '%s' "$figures" | cut -d' ' -f3)
    parked_per_day=$(printf '%s' "$figures" | cut -d' ' -f4)
    gigabytes=$(printf '%s' "$figures" | cut -d' ' -f5)

    echo "aws_box: instance $BOX_INSTANCE_ID is $state_before, stopping it"
    ec2 stop-instances --instance-ids "$BOX_INSTANCE_ID" >/dev/null
    "$AWS_BIN" --region "$REGION" ec2 wait instance-stopped --instance-ids "$BOX_INSTANCE_ID"
    echo "aws_box: instance $BOX_INSTANCE_ID is stopped, verified by the waiter"
    echo "aws_box: this uptime ran $uptime_hours hours and cost $uptime_cost $PRICE_CURRENCY net"
    echo "aws_box: parked it keeps only its $gigabytes GB of disks, about"
    echo "$parked_per_day $PRICE_CURRENCY per day, and it keeps corpus, index and images"

    (
        umask 077
        {
            echo "# stopped by aws_box.sh stop at $parked_iso, uptime and cost from the pinned rates"
            echo "BOX_STOPPED_ISO=$parked_iso"
            echo "BOX_LAST_UPTIME_HOURS=$uptime_hours"
            echo "BOX_LAST_UPTIME_COST_USD=$uptime_cost"
            echo "BOX_PARKED_COST_USD_PER_DAY=$parked_per_day"
        } >>"$STATE_FILE"
    )
    echo "aws_box: the closing figures are appended to $STATE_FILE"
    echo "aws_box: a stop releases the public address, so BOX_IP in that file and"
    echo "the A record of the load test are stale until the next start"
}

cmd_start() {
    require_credentials
    require_tools
    require_state
    # The security group is the one piece start cannot do without: without it the
    # box comes up and nobody can reach it, which looks like a broken box.
    : "${BOX_SECURITY_GROUP:?security group fehlt in $STATE_FILE}"
    if ! command -v curl >/dev/null 2>&1; then
        echo "aws_box: start needs curl, to read the current address of the owner" >&2
        exit 1
    fi

    echo "aws_box: starting instance $BOX_INSTANCE_ID"
    ec2 start-instances --instance-ids "$BOX_INSTANCE_ID" >/dev/null
    "$AWS_BIN" --region "$REGION" ec2 wait instance-running --instance-ids "$BOX_INSTANCE_ID"
    started_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    address=$(ec2 describe-instances --instance-ids "$BOX_INSTANCE_ID" | json '
import json
import sys

instance = json.load(sys.stdin)["Reservations"][0]["Instances"][0]
print(instance.get("PublicIpAddress") or "")
')
    if [ -z "$address" ]; then
        echo "aws_box: the box is running but the api reports no public address" >&2
        exit 1
    fi
    echo "aws_box: instance $BOX_INSTANCE_ID is running at $address since $started_iso"

    # The address of the owner changes with the carrier lease, and the ssh rule
    # that points at the old one is an open port for whoever holds it now
    # (T-06.1-78). Revoke first and authorize afterwards: the other order leaves
    # both open for the duration of one api call, and that is the state a mistake
    # would leave behind for good.
    owner=$(curl -sS --max-time 20 https://api.ipify.org)
    owner=$(printf '%s' "$owner" | json '
import ipaddress
import sys

candidate = sys.stdin.read().strip()
print(ipaddress.IPv4Address(candidate))
')
    stale=$(ec2 describe-security-group-rules \
        --filters "Name=group-id,Values=$BOX_SECURITY_GROUP" | json "
import json
import sys

wanted = '$owner/32'
rules = json.load(sys.stdin)['SecurityGroupRules']
print(' '.join(
    rule['SecurityGroupRuleId']
    for rule in rules
    if not rule.get('IsEgress')
    and rule.get('IpProtocol') == 'tcp'
    and rule.get('FromPort') == 22
    and rule.get('ToPort') == 22
    and rule.get('CidrIpv4') != wanted
))
")
    for rule in $stale; do
        echo "aws_box: revoking the ssh rule $rule, it points at a foreign address"
        ec2 revoke-security-group-ingress --group-id "$BOX_SECURITY_GROUP" \
            --security-group-rule-ids "$rule" >/dev/null
    done
    response=$(ec2_soft authorize-security-group-ingress \
        --group-id "$BOX_SECURITY_GROUP" \
        --ip-permissions "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=$owner/32,Description=owner}]")
    case "$response" in
    *InvalidPermission.Duplicate*)
        echo "aws_box: ssh was already open to $owner/32 and to nothing else"
        ;;
    *error*)
        echo "aws_box: the ssh rule was not set: $response" >&2
        exit 1
        ;;
    *)
        echo "aws_box: ssh is open to $owner/32 and to nothing else"
        ;;
    esac

    (
        umask 077
        {
            echo "# started by aws_box.sh start at $started_iso, new address and ssh rule set by it"
            echo "BOX_IP=$address"
            echo "BOX_STARTED_ISO=$started_iso"
            echo "BOX_SSH_FROM=$owner/32"
        } >>"$STATE_FILE"
    )

    # The three things a start by hand forgot every single time. Two of them are
    # done above, and this says which, because a tool that claims to have done
    # something is worse than one that says what is left.
    echo "aws_box: three things do not follow from a start, and here is their state:"
    echo "  1. BOX_IP: done, $address is appended to $STATE_FILE"
    echo "  2. the ssh rule of the security group for port 22: done, $owner/32"
    echo "  3. the A record loadtest.infranode.dev: OPEN, point it at $address"
    echo "aws_box: and two that belong to the container rather than to the box:"
    echo "  4. after a machine start the container is not started by AppAPI and"
    echo "     does not index (DI-05-36): occ app_api:app:disable findling_backend"
    echo "     followed by occ app_api:app:enable findling_backend"
    echo "  5. after every app_api:app:register the hard memory limit is gone:"
    echo "     docker update --memory=2g --memory-swap=2g on the container"
}

cmd_snapshot() {
    require_credentials
    require_tools
    require_state
    : "${VOLUME_ID:?volume id fehlt in $STATE_FILE}"

    # The state is the precondition and not a note in a plan. A snapshot of an
    # attached volume that is being written to is crash consistent and nothing
    # more; at a stopped instance the filesystem is quiet and the copy is clean.
    # This is also the one thing that cannot be made up for afterwards, because
    # a broken snapshot looks exactly like a good one until it is restored.
    state=$(ec2 describe-instances --instance-ids "$BOX_INSTANCE_ID" | json '
import json
import sys

instance = json.load(sys.stdin)["Reservations"][0]["Instances"][0]
print(instance["State"]["Name"])
')
    if [ "$state" != 'stopped' ]; then
        echo "aws_box: instance $BOX_INSTANCE_ID is $state, and this refuses to" >&2
        echo "snapshot a volume under a box that is not stopped: the copy would be" >&2
        echo "crash consistent, and nothing would say so afterwards" >&2
        exit 1
    fi

    echo "aws_box: snapshotting $VOLUME_ID, the data volume of $BOX_INSTANCE_ID"
    taken_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    snapshot_id=$(ec2 create-snapshot \
        --volume-id "$VOLUME_ID" \
        --description "$SNAPSHOT_DESCRIPTION" \
        --tag-specifications \
        "ResourceType=snapshot,Tags=[{Key=Name,Value=$SNAPSHOT_NAME},{Key=$TAG_KEY,Value=$KEEP_TAG_VALUE}]" \
        | json 'import json,sys; print(json.load(sys.stdin)["SnapshotId"])')
    echo "aws_box: snapshot $snapshot_id is being taken, tag $TAG_KEY=$KEEP_TAG_VALUE"

    # The waiter of the cli and no loop of our own, house rule since 2026-09-04.
    # It polls every 15 seconds and gives up after a bounded number of tries, so
    # a large first snapshot can outlast it. That is not a failure of the
    # snapshot, and the read back below is what decides, which is why the giving
    # up is caught here instead of ending the subcommand.
    waiter=0
    "$AWS_BIN" --region "$REGION" ec2 wait snapshot-completed --snapshot-ids "$snapshot_id" || waiter=1

    # The verification, and it is this and not the waiter: a waiter that returns
    # says the api stopped answering pending, it does not say what the snapshot
    # now is. These are the fields the report quotes.
    details=$(ec2 describe-snapshots --snapshot-ids "$snapshot_id" | json "
import json
import sys

snapshot = json.load(sys.stdin)['Snapshots'][0]
full = snapshot.get('FullSnapshotSizeInBytes')
print('SnapshotId  %s' % snapshot['SnapshotId'])
print('State       %s' % snapshot['State'])
print('Progress    %s' % snapshot.get('Progress', '?'))
print('VolumeId    %s' % snapshot['VolumeId'])
print('VolumeSize  %s GB, the size of the volume and not the billed size' % snapshot['VolumeSize'])
print('FullSize    %s' % ('%d bytes, %.1f GB of written blocks' % (full, full / 1000000000.0) if full else 'not reported by this api version'))
print('StartTime   %s' % snapshot['StartTime'])
print('OwnerId     %s' % snapshot['OwnerId'])
print('Encrypted   %s' % snapshot['Encrypted'])
print('Description %s' % snapshot.get('Description', ''))
")
    echo "$details"
    snapshot_state=$(printf '%s' "$details" | sed -n 's/^State  *//p')
    if [ "$waiter" -ne 0 ]; then
        echo "aws_box: the waiter gave up before the snapshot did, which is a limit"
        echo "of the cli and not a verdict: the read back above is the verdict"
    fi
    if [ "$snapshot_state" != 'completed' ]; then
        echo "aws_box: $snapshot_id is $snapshot_state and not completed yet." >&2
        echo "aws_box: nothing may be destroyed on this. Read it back again with" >&2
        echo "aws ec2 describe-snapshots --region $REGION --snapshot-ids $snapshot_id" >&2
        echo "aws_box: and do NOT run this subcommand again, that would be a second" >&2
        echo "snapshot and a second invoice" >&2
        exit 1
    fi

    (
        umask 077
        {
            echo "# snapshot of the data volume by aws_box.sh snapshot at $taken_iso"
            echo "CORPUS_SNAPSHOT_ID=$snapshot_id"
            echo "CORPUS_SNAPSHOT_ISO=$taken_iso"
            printf '%s\n' "$details" | sed 's/^/# /'
        } >>"$STATE_FILE"
    )
    echo "aws_box: $snapshot_id is completed, verified by a read back of its own"
    echo "aws_box: id and read back are appended to $STATE_FILE. That file is"
    echo "removed by destroy, so its content belongs in the report before then"
}

# Gone has three shapes here and none of them is Hetzner's not_found:
#
#   instance: a terminated instance keeps answering for up to an hour before it
#             disappears from the api, so state=terminated is the proof, and it
#             is also the moment the billing stops.
#   volume:   InvalidVolume.NotFound, once it is really deleted.
#   group:    InvalidGroup.NotFound, and it can only be deleted after the last
#             interface that used it is gone, which means after the instance.
#
# Anything this script cannot read counts as still there. A resource that is
# presumed deleted is the actual risk of the whole exercise.
instance_gone() {
    response=$(ec2_soft describe-instances --instance-ids "$1")
    case "$response" in
    *InvalidInstanceID.NotFound*)
        echo 'gone'
        return 0
        ;;
    esac
    state=$(printf '%s' "$response" | json '
import json
import sys

try:
    payload = json.load(sys.stdin)
except ValueError:
    print("unreadable")
    raise SystemExit(0)
try:
    print(payload["Reservations"][0]["Instances"][0]["State"]["Name"])
except (KeyError, IndexError):
    print("unreadable")
')
    if [ "$state" = 'terminated' ]; then
        echo 'gone'
    else
        echo "$state"
    fi
}

resource_gone() {
    case "$1" in
    *NotFound*)
        echo 'gone'
        ;;
    *)
        echo 'there'
        ;;
    esac
}

cmd_destroy() {
    require_credentials
    require_tools

    # The last step of this subcommand removes the state file, and that file is
    # the entire cost and damage history of this box: instance and volume, every
    # stop and every start with its run time and its cost, the damage report of
    # 2026-09-07 in which a second Nextcloud on the same docker daemon deleted
    # the measurement volume of the first, and the DI-05-36 finding. None of it
    # exists anywhere else. So the backup is a precondition and not a habit: the
    # path is named, the file has to be there and it has to have content, and
    # the refusal happens here, before the first destructive call, rather than
    # after the file is gone (T-11-53).
    backup="${FINDLING_STATE_BACKUP:-}"
    if [ -z "$backup" ]; then
        echo "aws_box: destroy needs FINDLING_STATE_BACKUP, the path of a copy of" >&2
        echo "$STATE_FILE, because the last step of this subcommand removes it" >&2
        exit 1
    fi
    if [ ! -f "$backup" ]; then
        echo "aws_box: the named backup $backup does not exist" >&2
        exit 1
    fi
    if [ ! -s "$backup" ]; then
        echo "aws_box: the named backup $backup is empty" >&2
        exit 1
    fi
    echo "aws_box: the history of this box is backed up in $backup"

    instance_id="${1:-}"
    volume_id="${2:-}"
    group_id="${3:-}"
    if [ -z "$instance_id" ]; then
        require_state
        instance_id="$BOX_INSTANCE_ID"
        volume_id="${VOLUME_ID:-}"
        group_id="${BOX_SECURITY_GROUP:-}"
    fi

    if [ -n "$volume_id" ]; then
        # A volume in use cannot be deleted, and detaching it while the box
        # still writes to it is how a filesystem gets corrupted. The instance
        # therefore goes first here, unlike in the Hetzner tool, where the
        # volume had to be detached before the server could release it.
        echo "aws_box: the data volume goes after the instance, not before"
    fi

    echo "aws_box: terminating instance $instance_id"
    ec2_soft terminate-instances --instance-ids "$instance_id" >/dev/null
    "$AWS_BIN" --region "$REGION" ec2 wait instance-terminated --instance-ids "$instance_id" || true

    if [ -n "$volume_id" ]; then
        echo "aws_box: deleting volume $volume_id"
        response=$(ec2_soft delete-volume --volume-id "$volume_id")
        case "$response" in
        *error*)
            echo "aws_box: the volume was not deleted yet: $response" >&2
            ;;
        esac
    fi

    if [ -n "$group_id" ]; then
        echo "aws_box: deleting security group $group_id"
        response=$(ec2_soft delete-security-group --group-id "$group_id")
        case "$response" in
        *error*)
            echo "aws_box: the security group was not deleted yet: $response" >&2
            ;;
        esac
    fi

    failed=0
    instance_state=$(instance_gone "$instance_id")
    if [ "$instance_state" = 'gone' ]; then
        echo "aws_box: instance $instance_id is gone, verified against the api"
    else
        echo "aws_box: instance $instance_id is still there ($instance_state)" >&2
        failed=1
    fi

    volume_state='gone'
    if [ -n "$volume_id" ]; then
        volume_state=$(resource_gone "$(ec2_soft describe-volumes --volume-ids "$volume_id")")
    fi
    if [ "$volume_state" = 'gone' ]; then
        echo "aws_box: volume ${volume_id:-none} is gone, verified against the api"
    else
        echo "aws_box: volume $volume_id is still there" >&2
        failed=1
    fi

    group_state='gone'
    if [ -n "$group_id" ]; then
        group_state=$(resource_gone "$(ec2_soft describe-security-groups --group-ids "$group_id")")
    fi
    if [ "$group_state" = 'gone' ]; then
        echo "aws_box: security group ${group_id:-none} is gone, verified against the api"
    else
        echo "aws_box: security group $group_id is still there" >&2
        failed=1
    fi

    # The sweep by tag, which is the check that catches what the state file did
    # not know about. Two exceptions are expected and named rather than hidden.
    #
    # The first: a terminated instance keeps its tags for up to an hour, so a
    # hit that is the instance we just terminated is not a leftover.
    #
    # The second, since 11-12: the snapshot of the corpus. It is the one
    # resource of this run that is meant to stay, it carries
    # purpose=findling-corpus-keep, and the filter below therefore does not see
    # it at all. It is asked for anyway, on purpose. A reader of this sweep has
    # to be told which resource outlives the box rather than infer it from a
    # filter, a resource that carried both tags would otherwise be reported as a
    # leftover, and the answer is at the same time the proof that the snapshot
    # survived the teardown (T-11-52, T-11-55).
    keepers=$(ec2 describe-tags --filters "Name=tag:$TAG_KEY,Values=$KEEP_TAG_VALUE" | json "
import json
import sys

tags = json.load(sys.stdin)['Tags']
print(' '.join(tag['ResourceId'] for tag in tags))
")
    if [ -n "$keepers" ]; then
        echo "aws_box: expected to outlive this box, tagged $TAG_KEY=$KEEP_TAG_VALUE:"
        echo "  $keepers"
    else
        echo "aws_box: nothing carries $TAG_KEY=$KEEP_TAG_VALUE, so nothing of this" >&2
        echo "run is kept. That is correct only if no snapshot was meant to be" >&2
        echo "taken; aws_box.sh snapshot is the subcommand that takes one" >&2
    fi
    remaining=$(ec2 describe-tags --filters "Name=tag:$TAG_KEY,Values=$TAG_VALUE" | json "
import json
import sys

tags = json.load(sys.stdin)['Tags']
keepers = '$keepers'.split()
left = [
    tag for tag in tags
    if tag['ResourceId'] != '$instance_id' and tag['ResourceId'] not in keepers
]
for tag in left:
    print('%s %s' % (tag['ResourceType'], tag['ResourceId']))
")
    if [ -n "$remaining" ]; then
        echo "aws_box: something still carries the tag $LABEL:" >&2
        echo "$remaining" >&2
        failed=1
    else
        echo "aws_box: no resource but the terminated instance carries $LABEL"
        echo "aws_box: its tags fall off the api within the hour, on their own"
    fi

    if [ "$failed" -ne 0 ]; then
        echo "aws_box: something is left over. Find it by tag: $LABEL" >&2
        echo "aws_box: the state file stays, so a second destroy can use it" >&2
        exit 1
    fi

    rm -f "$STATE_FILE"
    echo "aws_box: every resource of this run is gone and $STATE_FILE is removed"
}

COMMAND="${1:-}"
if [ -n "$COMMAND" ]; then
    shift
fi

case "$COMMAND" in
    prices) cmd_prices ;;
    create) cmd_create ;;
    volume) cmd_volume ;;
    status) cmd_status ;;
    stop) cmd_stop ;;
    start) cmd_start ;;
    snapshot) cmd_snapshot ;;
    destroy) cmd_destroy "$@" ;;
    '')
        echo "aws_box: one of the eight subcommands is required" >&2
        usage
        exit 2
        ;;
    *)
        echo "aws_box: '$COMMAND' is not a subcommand of this script" >&2
        usage
        exit 2
        ;;
esac
