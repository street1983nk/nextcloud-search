#!/usr/bin/env bash
# Measurement A6 of the dedup note (35-DEDUP-NOTIZ, D-37-04, plan 39-04).
#
# Builds a Samba share on the runner with two users and one file that the
# second user is explicitly denied reading, proves that denial at the Samba
# server itself (positive control), mounts the share in Nextcloud with user
# specific credentials and measures, once without and once with the check_acl
# option of the SMB backend, for both users:
#   (1) listing:      WebDAV PROPFIND Depth 1 on the mount, is verboten.txt there
#   (2) isReadable(): the node and the SMB storage, through smb_acl_probe.php
#   (3) download:     WebDAV GET, HTTP status and whether the content arrived
#
# Runs from the root of the Nextcloud server checkout. Expects NC_URL, OCC,
# PROBE and RESULT_FILE. The passwords are fixed test values of a throwaway
# runner and are still never printed (T-39-12): Samba gets them on stdin, the
# SMB clients through an authentication file with mode 0600.

set -euo pipefail

: "${NC_URL:?NC_URL is required}"
: "${OCC:?OCC is required}"
: "${PROBE:?PROBE is required}"
: "${RESULT_FILE:?RESULT_FILE is required}"

SERVER_ROOT="${PWD}"
WORK="${RUNNER_TEMP:-/tmp}/smb-acl"
SHARE_DIR=/srv/messung
NETBIOS=MESSUNG
SMB_URL=//127.0.0.1/messung
MARKER='verboten-39-04-inhalt'
FREE_MARKER='frei-39-04-inhalt'
# Fixed test credentials, valid on this runner only.
PASS_USERA='Messung-A-39-x7Q'
PASS_USERB='Messung-B-39-k2W'

fail() {
  echo "::error::$*"
  exit 1
}

password_of() {
  case "$1" in
    usera) printf '%s' "${PASS_USERA}" ;;
    userb) printf '%s' "${PASS_USERB}" ;;
    *) fail "no test password for $1" ;;
  esac
}

umask 077
mkdir -p "${WORK}"

# --- Samba ------------------------------------------------------------------

echo "installing samba and smbclient from the Ubuntu archive"
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq samba smbclient > /dev/null
samba_version=$(smbd --version)
echo "samba: ${samba_version}"

sudo mkdir -p "${SHARE_DIR}"
sudo chmod 0777 "${SHARE_DIR}"

# acl_xattr keeps the NT ACL in an extended attribute, and with
# "ignore system acls" that stored ACL alone decides access, so a DENY ACE set
# through smbcacls is what the server enforces.
sudo tee /etc/samba/smb.conf > /dev/null << EOF
[global]
   netbios name = ${NETBIOS}
   workgroup = WORKGROUP
   server role = standalone server
   security = user
   map to guest = never
   smb ports = 445
   interfaces = lo
   bind interfaces only = yes
   disable netbios = yes
   log level = 1

[messung]
   path = ${SHARE_DIR}
   read only = no
   browseable = yes
   create mask = 0666
   directory mask = 0777
   vfs objects = acl_xattr
   acl_xattr:ignore system acls = yes
   store dos attributes = yes
EOF
testparm -s > /dev/null 2>&1 || fail "testparm rejected the generated smb.conf"

for uid in usera userb; do
  id "${uid}" > /dev/null 2>&1 || sudo useradd -M -s /usr/sbin/nologin "${uid}"
  pass=$(password_of "${uid}")
  printf '%s\n%s\n' "${pass}" "${pass}" | sudo smbpasswd -a -s "${uid}" > /dev/null
  printf 'username = %s\npassword = %s\ndomain = %s\n' "${uid}" "${pass}" "${NETBIOS}" > "${WORK}/auth-${uid}"
done

sudo systemctl restart smbd

up=0
for _ in $(seq 1 30); do
  if smbclient -L //127.0.0.1 -A "${WORK}/auth-usera" > /dev/null 2>&1; then
    up=1
    break
  fi
  sleep 1
done
[ "${up}" = 1 ] || fail "smbd did not answer on 127.0.0.1:445"

printf '%s\n' "${FREE_MARKER}" > "${WORK}/frei.txt"
printf '%s\n' "${MARKER}" > "${WORK}/verboten.txt"
smbclient "${SMB_URL}" -A "${WORK}/auth-usera" -c "lcd ${WORK}; put frei.txt; put verboten.txt" > /dev/null \
  || fail "usera could not put the two files onto the share"

# The explicit DENY read ACE for userb, set by usera as owner of the file.
smbcacls "${SMB_URL}" verboten.txt -A "${WORK}/auth-usera" --add "ACL:${NETBIOS}\\userb:DENIED/0x0/READ" \
  || fail "smbcacls could not add the DENY ACE for userb"
echo "--- NT ACL of verboten.txt ---"
smbcacls "${SMB_URL}" verboten.txt -A "${WORK}/auth-usera" || fail "smbcacls could not read the ACL back"

# --- positive control at the Samba server -------------------------------------

# smb_read <uid> <file> <marker>: exit 0 only if the file arrived with its marker.
smb_read() {
  local out="${WORK}/smb-$1-$2"
  rm -f "${out}"
  if smbclient "${SMB_URL}" -A "${WORK}/auth-$1" -c "get $2 ${out}" > "${WORK}/smb-$1.log" 2>&1 \
    && [ -f "${out}" ] && grep -qx "$3" "${out}"; then
    return 0
  fi
  return 1
}

smb_read usera verboten.txt "${MARKER}" || {
  cat "${WORK}/smb-usera.log"
  fail "positive control: usera cannot read verboten.txt at the Samba server, run invalid"
}
if smb_read userb verboten.txt "${MARKER}"; then
  fail "positive control: userb read verboten.txt at the Samba server despite the DENY ACE, run invalid"
fi
denial=$(grep -oE 'NT_STATUS_[A-Z_]+' "${WORK}/smb-userb.log" | head -n 1 || true)
smb_read userb frei.txt "${FREE_MARKER}" || {
  cat "${WORK}/smb-userb.log"
  fail "positive control: userb cannot read frei.txt at the Samba server, run invalid"
}
echo "positive control: usera reads verboten.txt, userb is refused (${denial:-no status}), userb reads frei.txt"

# --- Nextcloud ------------------------------------------------------------------

"${OCC}" app:enable files_external > /dev/null
"${OCC}" files_external:backends storage --output=json | grep -q '"smb"' \
  || fail "files_external does not list the smb backend (smbclient binary missing?)"
if php -m | grep -qi '^smbclient$'; then
  smb_client="libsmbclient-php"
else
  smb_client="smbclient binary (icewind/smb fallback)"
fi

for uid in usera userb; do
  OC_PASS=$(password_of "${uid}") "${OCC}" user:add --password-from-env --display-name "${uid}" "${uid}" > /dev/null
done

created=$("${OCC}" files_external:create /messung smb password::logincredentials \
  -c host=127.0.0.1 -c share=messung -c root= -c domain="${NETBIOS}")
mount_id=$(printf '%s\n' "${created}" | grep -oE '[0-9]+' | tail -n 1 || true)
[ -n "${mount_id}" ] || fail "files_external:create returned no mount id"
"${OCC}" files_external:applicable "${mount_id}" --add-user usera --add-user userb > /dev/null

dav() {
  # dav <uid> <method> <path> <outfile> [extra curl args]: prints the HTTP status
  local uid="$1" method="$2" path="$3" outfile="$4"
  shift 4
  curl -s -o "${outfile}" -w '%{http_code}' -u "${uid}:$(password_of "${uid}")" -X "${method}" "$@" \
    "${NC_URL}/remote.php/dav/files/${uid}/${path}"
}

# The first request of each user is the login that "save in database" stores
# the credentials from. If the store stays empty, they are seeded through the
# credentials manager under the same identifier, and the table says so.
auth_variant="password::logincredentials (Log-in credentials, save in database), stored at login"
for uid in usera userb; do
  dav "${uid}" PROPFIND "" "${WORK}/login-${uid}.xml" -H 'Depth: 1' > /dev/null || true
  state=$(php "${PROBE}" "${SERVER_ROOT}" creds "${uid}")
  if [ "${state}" != "stored" ]; then
    PROBE_PASS=$(password_of "${uid}") php "${PROBE}" "${SERVER_ROOT}" seed "${uid}" > /dev/null
    auth_variant="password::logincredentials (Log-in credentials, save in database), seeded through ICredentialsManager"
  fi
done

rows=()
invalid=""

measure() {
  local pass="$1" uid="$2"
  local code listing readable download
  code=$(dav "${uid}" PROPFIND "messung/" "${WORK}/list-${pass}-${uid}.xml" -H 'Depth: 1' || true)
  if [ "${code}" = "207" ]; then
    if grep -q 'verboten.txt' "${WORK}/list-${pass}-${uid}.xml"; then
      listing="gelistet"
    else
      listing="nicht gelistet"
    fi
    grep -q 'frei.txt' "${WORK}/list-${pass}-${uid}.xml" || listing="${listing} (frei.txt fehlt)"
  else
    listing="HTTP ${code}"
  fi

  readable=$(php "${PROBE}" "${SERVER_ROOT}" readable "${uid}" messung/verboten.txt 2> /dev/null || echo "probe-error")

  code=$(dav "${uid}" GET "messung/verboten.txt" "${WORK}/get-${pass}-${uid}.txt" || true)
  if grep -qx "${MARKER}" "${WORK}/get-${pass}-${uid}.txt" 2> /dev/null; then
    download="HTTP ${code}, Inhalt angekommen"
  else
    download="HTTP ${code}, kein Inhalt"
  fi

  rows+=("| ${pass} | ${uid} | ${listing} | ${readable} | ${download} |")

  # usera has no deny anywhere: if Nextcloud cannot list and read the file for
  # her, the setup is broken and the figures of userb mean nothing.
  if [ "${uid}" = "usera" ] && { [ "${listing}" != "gelistet" ] || [ "${download}" != "HTTP 200, Inhalt angekommen" ]; }; then
    invalid="usera could not list or download verboten.txt in pass ${pass}"
  fi
}

for uid in usera userb; do
  measure "check_acl aus" "${uid}"
done

"${OCC}" files_external:config "${mount_id}" check_acl true > /dev/null
# The file cache still holds the listing of the first pass; a scan per user
# lists the folder again, now through the ACL check.
for uid in usera userb; do
  "${OCC}" files:scan --quiet --path="/${uid}/files/messung" || echo "files:scan for ${uid} ended non-zero"
done

for uid in usera userb; do
  measure "check_acl an" "${uid}"
done

{
  echo "## Messung A6: SMB-ACL gegen Nextcloud (Plan 39-04)"
  echo
  echo "- Samba: ${samba_version}, Freigabe messung mit vfs acl_xattr, DENY READ fuer userb auf verboten.txt"
  echo "- Positivkontrolle am Samba-Server: usera liest verboten.txt, userb abgewiesen (${denial:-ohne Status}), userb liest frei.txt"
  echo "- Nextcloud: stable34, Backend smb ueber ${smb_client}"
  echo "- Anmeldung: ${auth_variant}"
  echo "- isReadable(): node = Node::isReadable() im Nutzerordner, storage = SMB::isReadable() derselben Datei"
  echo
  echo "| Durchgang | Nutzer | Listing verboten.txt | isReadable() | Download verboten.txt |"
  echo "|-----------|--------|----------------------|--------------|-----------------------|"
  printf '%s\n' "${rows[@]}"
  if [ -n "${invalid}" ]; then
    echo
    echo "Lauf ungueltig: ${invalid}"
  fi
} > "${RESULT_FILE}"

cat "${RESULT_FILE}"

[ -z "${invalid}" ] || fail "run invalid: ${invalid}"
