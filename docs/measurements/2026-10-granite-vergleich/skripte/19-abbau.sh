#!/bin/sh
# Step 19 of the granite comparison: the teardown of the arm box, on the
# development machine, and its proof.
#
# Runs only after the raw data of steps 11 to 14 are fetched and committed.
# scripts/ops/aws_box.sh destroy terminates the instance and deletes the
# security group and the key pair of the run, with its own read back; this box
# has no data volume, and its root disk goes with the instance
# (DeleteOnTermination=true). Afterwards four counts, asked of the api and not
# of a state file: instances of the run that are not terminated, volumes and
# elastic addresses that carry the tag of the run, and security groups with its
# name. All four have to be zero.
#
# The output goes into a public repository, so every identifier of the account
# is masked before it is written: instance, volume, group, key, snapshot and
# image identifiers, addresses and twelve digit numbers.
#
#   FINDLING_LOADTEST_DIR   state directory of the box (read by aws_box.sh)
#   FINDLING_STATE_BACKUP   copy of box.env, required by aws_box.sh destroy
#   OUT                     raw file (default rohdaten/08-abbau-boxen.txt)
#
# The two credentials come from the environment, as for aws_box.sh.
set -eu

: "${FINDLING_STATE_BACKUP:?FINDLING_STATE_BACKUP must name the copy of box.env}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$HERE/../../.." && pwd)"
OUT="${OUT:-$HERE/rohdaten/08-abbau-boxen.txt}"
MSYS2_ARG_CONV_EXCL='*'
export MSYS2_ARG_CONV_EXCL

mask() {
    sed -E \
        -e 's/\bi-[0-9a-f]{8,17}\b/<instanz>/g' \
        -e 's/\bvol-[0-9a-f]{8,17}\b/<volume>/g' \
        -e 's/\bsg-[0-9a-f]{8,17}\b/<sg>/g' \
        -e 's/\bsgr-[0-9a-f]{8,17}\b/<regel>/g' \
        -e 's/\bkey-[0-9a-f]{8,17}\b/<schluessel>/g' \
        -e 's/\bsnap-[0-9a-f]{8,17}\b/<snapshot>/g' \
        -e 's/\bami-[0-9a-f]{8,17}\b/<abbild>/g' \
        -e 's/\beipalloc-[0-9a-f]{8,17}\b/<adresszuteilung>/g' \
        -e 's/([0-9]{1,3}\.){3}[0-9]{1,3}/<adresse>/g' \
        -e 's/\b[0-9]{12}\b/<konto>/g' \
        -e 's#[A-Za-z]:?/[^ ]*/box\.env#<zustandsdatei>#g' \
        -e 's#[^ ]*box\.env\.bak[^ ]*#<sicherung>#g'
}
say() { printf '%s\n' "$*" | mask | tee -a "$OUT"; }
aws_bin() {
    if command -v aws >/dev/null 2>&1; then aws "$@"; else "$AWS_CLI" "$@"; fi
}
# A call that fails is no count. Found on the first teardown of this run: the
# exported session had expired, every call answered an error on stderr and
# nothing on stdout, and a word count over nothing reported zero leftovers for
# a box that was still running. So the answer of the api is taken first and a
# failure ends this script red, before anything is counted.
count() {
    answer=$(aws_bin --region eu-central-1 --output text ec2 "$@") || {
        echo "gegenprobe gescheitert: ec2 $1 antwortet mit einem fehler, nichts gezählt" >&2
        exit 1
    }
    printf '%s\n' "$answer" | wc -w | tr -d ' '
}

: >"$OUT"
say "schritt 19 abbau der arm-box, start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
# The session has to answer before anything is asked of it: a destroy against
# an expired session terminates nothing and its output is easy to misread.
if ! aws_bin --region eu-central-1 sts get-caller-identity >/dev/null 2>&1; then
    say "sitzung antwortet nicht (abgelaufen?), es wird nichts abgebaut und nichts gezählt"
    exit 1
fi
say "sitzung gültig, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "befehl: FINDLING_STATE_BACKUP=<sicherung> sh scripts/ops/aws_box.sh destroy"
sh "$REPO_ROOT/scripts/ops/aws_box.sh" destroy 2>&1 | mask | tee -a "$OUT" || true
say "destroy ende $(date -u +%Y-%m-%dT%H:%M:%SZ)"

say ""
say "befehl: sh scripts/ops/aws_box.sh status (ohne zustandsdatei: suche nach dem tag)"
sh "$REPO_ROOT/scripts/ops/aws_box.sh" status 2>&1 | mask | tee -a "$OUT" || true

say ""
say "gegenproben gegen die api, $(date -u +%Y-%m-%dT%H:%M:%SZ):"
instances=$(count describe-instances --filters "Name=tag:purpose,Values=findling-phase5" \
    "Name=instance-state-name,Values=pending,running,stopping,stopped,shutting-down" \
    --query 'Reservations[].Instances[].InstanceId')
volumes=$(count describe-volumes --filters "Name=tag:purpose,Values=findling-phase5" --query 'Volumes[].VolumeId')
addresses=$(count describe-addresses --filters "Name=tag:purpose,Values=findling-phase5" --query 'Addresses[].AllocationId')
all_addresses=$(count describe-addresses --query 'Addresses[].AllocationId')
groups=$(count describe-security-groups --filters "Name=group-name,Values=findling-loadtest" --query 'SecurityGroups[].GroupId')
say "instanzen-nicht-beendet $instances"
say "volumes-mit-tag $volumes"
say "elastische-adressen-mit-tag $addresses, elastische-adressen-im-konto-gesamt $all_addresses"
say "security-groups-findling-loadtest $groups"
if [ "$instances" = 0 ] && [ "$volumes" = 0 ] && [ "$addresses" = 0 ] && [ "$groups" = 0 ]; then
    say "abbau belegt: keine instanz, kein volume, keine adresse, keine gruppe der messung"
else
    say "abbau NICHT vollstaendig, siehe zahlen oben"
    exit 1
fi
say "schritt 19 fertig $(date -u +%Y-%m-%dT%H:%M:%SZ)"
