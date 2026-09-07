#!/bin/sh
# The install path of a stranger, walked on arm64, with the same script as amd64.
#
# The arm64 half of decision E-H5. It is not a second script and not a second
# schedule: it is scripts/dev/aio_install_check.sh with --platform linux/arm64,
# and everything else is the shape of the amd64 run of 06.1-16 so that the two
# protocols can be held against each other.
#
# Two switches deserve their reason in writing.
#
#   --substitute-tag dev: the archive names
#   ghcr.io/street1983nk/findling_backend:1.0.0, and that tag does not exist
#   before the release tag exists. This is the same named finding the amd64 run
#   carries as finding 1, and the script records the substitution rather than
#   hiding it.
#
#   --cron-driver script: a plain nextcloud:apache container runs no cron of its
#   own, so nothing would drive the background jobs and the zero config proof
#   would time out against an empty clock rather than against the app. The
#   script then calls cron.php once per round, which is the identical command a
#   system cron runs, and it counts that call in its own protocol.
set -eu

OUT=/home/ubuntu/work/nachmessung
WORK=/home/ubuntu/work/arm64
REPO=/home/ubuntu/work/repo0918
NC=findling-arm64-nc
PORT=8097

FINDLING_ADMIN_PASS=$(sudo cat /home/ubuntu/work/.pw/arm64-admin)
export FINDLING_ADMIN_PASS

# The table half of the uninstall promises. Without a command that lists the
# oc_findling_* tables the script reports that half as not performed instead of
# silently passing it, so it gets one, and it goes through PDO because sqlite3
# is not installed in that image.
cat > "$WORK/tables.sh" <<'TABLES'
#!/bin/sh
set -eu
sudo docker exec --user www-data findling-arm64-nc php -r '
$pdo = new PDO("sqlite:/var/www/html/data/owncloud.db");
$sql = "select name from sqlite_master where type = \"table\" and name like \"oc_findling%\"";
foreach ($pdo->query($sql) as $row) {
    echo $row[0], PHP_EOL;
}
'
TABLES
chmod +x "$WORK/tables.sh"
echo "-- the table command, driven once before it is armed --"
sh "$WORK/tables.sh" || echo "(no oc_findling table yet, which is the expected state before the install)"

cd "$REPO"
sh scripts/dev/aio_install_check.sh \
    --url "http://localhost:$PORT" \
    --admin admin \
    --exec "sudo docker exec -i --user www-data -w /var/www/html $NC" \
    --companion "$WORK/dist/findling.tar.gz" \
    --backend "$WORK/dist/findling_backend.tar.gz" \
    --version 1.0.0 \
    --daemon harp_arm64 \
    --flavour compose \
    --platform linux/arm64 \
    --substitute-tag dev \
    --cron-driver script \
    --cron-interval 300 \
    --cron-rounds 6 \
    --db-tables-cmd "sh $WORK/tables.sh" \
    --rmi-local-image \
    --log "$OUT/81-arm64-lauf.txt" 2>&1 | tail -80

echo "81-FERTIG" > "$OUT/81-FERTIG"
