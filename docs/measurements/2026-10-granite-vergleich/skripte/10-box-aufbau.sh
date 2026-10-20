#!/bin/sh
# Step 10 of the granite comparison: the bare m7g.large, on the box itself.
#
# Three subcommands, called over ssh in this order:
#
#   kappe    the memory cap mem=4G as a grub drop-in that extends the command
#            line of the cloud image rather than replacing it (aws_box.sh create,
#            step 4). The reboot is the caller's, because it ends this session.
#   docker   docker from the distribution, then the shipped image pulled by the
#            digest of its index, so the arm64 manifest under it is fixed.
#   pruefen  the readbacks every measurement rests on: MemTotal under 4 GiB, two
#            cores, aarch64, the image digest and its architecture, and the
#            sha256 of every uploaded file against the values of steps 1, 2, 7.
#            A mismatch ends red and nothing is measured.
#
# No Nextcloud on this box (assumption A4) and no data volume: the models and the
# text of the sample are uploaded into WORK.
#
#   WORK   upload directory on the box (required for docker and pruefen)
#   IMAGE  the shipped image by digest (default store release 1.4.3, index digest)
set -eu

IMAGE="${IMAGE:-ghcr.io/street1983nk/findling_backend@sha256:036eb67e3e1144bc371142e18fcbfe94327b2a6edbfc0d1aea2f32d93302fc6d}"
# The four GiB the cap leaves, in the unit of /proc/meminfo.
LIMIT_KB=4194304

stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }

cmd_kappe() {
    echo "kappe start $(stamp)"
    echo 'GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT mem=4G"' \
        | sudo tee /etc/default/grub.d/99-mem4g.cfg
    sudo update-grub 2>&1 | tail -n 3
    echo "kappe geschrieben $(stamp), neustart folgt durch den aufrufer"
}

cmd_docker() {
    : "${WORK:?WORK must name the upload directory}"
    echo "docker start $(stamp)"
    sudo DEBIAN_FRONTEND=noninteractive apt-get -qq update
    sudo DEBIAN_FRONTEND=noninteractive apt-get -qq install -y docker.io >/dev/null
    sudo docker version --format 'docker server {{.Server.Version}}, {{.Server.Arch}}'
    sudo docker pull -q "$IMAGE"
    echo "docker ende $(stamp)"
}

check() {
    # file, expected sha256
    actual=$(sha256sum "$WORK/$1" | cut -d ' ' -f 1)
    if [ "$actual" = "$2" ]; then
        echo "sha256 $1 $actual OK"
    else
        echo "sha256 $1 $actual ABWEICHUNG, erwartet $2" >&2
        failed=1
    fi
}

cmd_pruefen() {
    : "${WORK:?WORK must name the upload directory}"
    failed=0
    echo "pruefen $(stamp)"
    total=$(sed -n 's/^MemTotal: *\([0-9]*\) kB$/\1/p' /proc/meminfo)
    echo "meminfo $(grep -E '^(MemTotal|MemAvailable|SwapTotal):' /proc/meminfo | tr -s ' ' | tr '\n' ' ')"
    if [ "$total" -lt "$LIMIT_KB" ]; then
        echo "kappe MemTotal $total kB unter $LIMIT_KB kB OK"
    else
        echo "kappe MemTotal $total kB NICHT unter $LIMIT_KB kB" >&2
        failed=1
    fi
    echo "cmdline mem=4G $(grep -c 'mem=4G' /proc/cmdline)"
    echo "nproc $(nproc), uname -m $(uname -m), kernel $(uname -r)"
    echo "cgroup $(stat -fc %T /sys/fs/cgroup)"
    echo "image $(sudo docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}} {{.Os}}/{{.Architecture}}')"
    check e5/model.onnx 8da4c9ba0ad59f58e8566839425d7fd6339d31414d0ce5cba2d7d0afb75dd8b6
    check e5/tokenizer.json 0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39
    check e5/tokenizer_config.json a1d6bc8734a6f635dc158508bef000f8e2e5a759c7d92f984b2c86e5ff53425b
    check e5/special_tokens_map.json d05497f1da52c5e09554c0cd874037a083e1dc1b9cfd48034d1c717f1afc07a7
    check e5/config.json bbb7c1333fc4b3e27fbc9cd5d2070aabcc1d4dfb99917c3633e772f97545a6b6
    check granite-int8/model.onnx 704c1ebca5fbb7cd83ced41827658ac4c9990c64f7f2874d22b78044e5022e22
    check granite-int8/tokenizer.json 4f2842d568e2724370aec203652a42ac783c7937f8347a1a2cc7506d71f1582f
    check granite-int8/tokenizer_config.json 6ed69389e30a8ecabfce2f9ebcdf0c908b34056f24d994340f2f216521c057d5
    check granite-int8/special_tokens_map.json 013787ee251ff611722479197c00853b62113ad303cb0a36524231783c676c69
    check granite-int8/config.json de948b0bdc6f356afad7a84b276d8dd7e7fe10fb9add1bb5e610621c28e41ebc
    check text/texte.jsonl f0077c0e3beb0833624c684016d2622438e340dded3b1f7b9798df231315abef
    check semantik/de.jsonl 700c74d2c40d30ad26ad2cbd0ad8567a4b51346ea2b7f570abe884a0811e4f51
    if [ "$failed" -ne 0 ]; then
        echo "pruefen ROT, es wird nicht gemessen" >&2
        exit 1
    fi
    echo "pruefen gruen $(stamp)"
}

case "${1:-}" in
kappe) cmd_kappe ;;
docker) cmd_docker ;;
pruefen) cmd_pruefen ;;
*)
    echo "usage: 10-box-aufbau.sh <kappe|docker|pruefen>" >&2
    exit 2
    ;;
esac
