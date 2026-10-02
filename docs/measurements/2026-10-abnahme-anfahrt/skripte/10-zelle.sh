#!/bin/sh
# Eine Messzelle der Abnahme-Anfahrt (Phase 28), vom Nullstand bis zu den
# Rohdaten, in fester Reihenfolge (Pattern 1 der Research).
#
# **DIESE FASSUNG IST NICHT GEFAHREN.** Keine Rohdatei liegt neben ihr; was sie
# auf der Box faehrt, faehrt sie auf der Anfahrt.
#
# Benutzung: ./10-zelle.sh <box> <zelle> <profil> <praezision>
#
#   box         Name der Box fuer den Rohdatenpfad, zum Beispiel m7g.large
#   zelle       Name der Zelle, zum Beispiel St-T oder St-fp32-T
#   profil      economy, standard oder performance
#   praezision  int8 oder fp32 (fp32 nur mit standard oder performance)
#
# Die Reihenfolge, und jeder Schritt schreibt eine Zeile "schritt <name>":
#
#   abwaerts                 Vorzustand ueber den Abwaertsweg auf economy/int8
#                            (POST /apps/findling/admin/profile), damit der
#                            neue Container nicht im Profil der Vorzelle anlaeuft
#   zaehlung-eine-nextcloud  genau eine Nextcloud an diesem Docker-Dienst,
#                            unmittelbar vor dem --rm-data (Block 13, 07.09.)
#   nullstand                unregister --rm-data
#   registrierung            Abbild per Digest, Registrierung ueber AppAPI
#   vorrat-tor               der Arbeitsvorrat der PHP-Haelfte, gelesen VOR der
#                            Bewaffnung: hier kann nur Altbestand eines
#                            frueheren Laufs stehen, ein Vorrat ungleich 0 ist
#                            Abbruch 73 (BLOCKER-28-07, Lauf 4)
#   bewaffnung               disable/enable, Beleg backendReachable true in der
#                            Admin-Uebersicht (Block 11)
#   grenze                   nur mit GRENZE_2G=ja (m7g.large, Block 12, 2g/0)
#   baumhash                 40b-baumhash.sh und der Baumhash im laufenden
#                            Container
#   93b-nullstand            die vier Quellen des Nullstands, gelesen ohne den
#                            Neuaufbau anzustossen (Ableitung von
#                            93-nullstand.sh, siehe dort); Quelle 4 wird nur
#                            noch protokolliert, das Vorrats-Urteil faellt am
#                            vorrat-tor
#   drop-caches              sync und drop_caches, damit keine Zelle vom
#                            Seitencache der vorigen erbt
#   probe                    11-probe-route.py ueber die Produktroute; economy
#                            ist ein Abwaertsweg und braucht keine; narrow oder
#                            nofit: occ erzwingt, Zeile "erzwungen ja" (D-28-05)
#   wirksamkeit              die Admin-Uebersicht meldet effective == Ziel und
#                            slotsInForce; zur Haelfte der Frist einmal neu
#                            bewaffnet; ohne Wirkung KEIN Trigger (Pitfall 1)
#   sampler                  rss_sampler.sh 2 s, proc_anon_sampler.sh 1 s,
#                            cpu_sampler.sh, 96d-statusbeobachter.py 120 s
#   trigger                  beim Teilkorpus zuerst die zaehlmarke aus der
#                            Datenbank (max(updated_at) der file_state-Tabelle,
#                            unmittelbar vor dem Trigger), dann
#                            occ findling:index --restart -n (ohne -n fragt occ
#                            zurueck und aendert nichts); beim Teilkorpus danach
#                            das Zaehltor 5000 (01-teilkorpus.py zaehltor) mit
#                            teilkorpus- und zellscharfer Frischzaehlung
#   ende                     Vorrat 0 und embedded == indexed in zwei Lesungen
#                            hintereinander
#   nachlauf                 Ruhezeit 120 s, Grundlast, guard-Block, Marke
#                            waechter-absenkung (Pitfall 8: markiert, nicht
#                            verworfen), OOM-Schlusszeile: OOMKilled und
#                            RestartCount aus docker inspect, StartedAt, oom und
#                            oom_kill aus memory.events der cgroup (seit
#                            01.10.2026, nach dem stopp nicht mehr lesbar)
#   abholen                  Rohdaten liegen unter rohdaten/<box>/<zelle>/
#
# Die Laufwerte stehen in LAUFWERTE (Vorgabe $HOME/work/v14-lauf.env, Rechte
# 600), eine Zeile NAME=WERT je Wert, gelesen und nie ausgefuehrt:
#
#   ABBILD_DIGEST   sha256:<64 Hexziffern>, das gemessene Abbild
#   GRENZE_2G       ja (nur m7g.large) oder nein (Matrix-Boxen, D-28-03)
#   PWFILE          Passwortdatei des Administrators, fuer den Benutzer der
#                   Box lesbar; das Passwort steht nie auf einer Kommandozeile
#   ADRESSE         optional, die Adresse der Instanz
#
# Der Korpus kommt aus der Umgebung: ZELLE_KORPUS=voll (Vorgabe) oder teil;
# 00-kette.sh setzt ihn je Zelle.
#
# In den Rohdaten stehen keine Adresse, keine Instanz- und keine Volumekennung
# (T-28-10): die Adresse geht nur an die Werkzeuge, nie in eine Zeile, und das
# Protokoll des Statusbeobachters wird vor dem Ablegen gefiltert.
#
# Rueckgabewerte:
#
#   2   Aufruf oder Laufwerte unvollstaendig (auch ABBILD_DIGEST ohne die
#       Gestalt sha256:<64 Hexziffern>), vor dem ersten Befehl an die Box
#   59  das Rohdatenverzeichnis der Zelle ist nicht leer
#   60  der Abwaertsweg auf economy/int8 hat nicht gespeichert
#   61  nicht genau eine Nextcloud; kein --rm-data
#   62  unregister --rm-data gescheitert
#   63  Abbild oder Registrierung gescheitert
#   64  die Grenze 2g/0 steht nicht in der cgroup
#   65  keine Bewaffnung: backendReachable wird nicht true
#   66  kein Baumhash-Beweis, oder der laufende Container traegt ein anderes Paket
#   67  der Nullstand ist nicht leer oder nicht lesbar (93b-nullstand.sh)
#   68  die Probe endete weder mit fits noch mit narrow/nofit, oder occ konnte
#       nicht erzwingen
#   69  effective ist nach der Frist nicht das Ziel; kein Trigger
#   70  der Trigger hat nichts angestossen
#   71  Teilkorpus: das Zaehltor 5000 ist verfehlt, oder die zaehlmarke ist
#       nicht lesbar (ohne Marke ist das Tor nicht pruefbar)
#   72  das Ende (Vorrat 0, embedded == indexed) kam nicht in der Frist
#   73  der Arbeitsvorrat traegt Altbestand eines frueheren Laufs (vorrat-tor,
#       vor der Bewaffnung); --rm-data raeumt die NC-Queue nicht
#
# ASCII, weil die Box ihr Gebietsschema nicht garantiert.
set -eu

SKRIPTE=$(cd "$(dirname "$0")" && pwd)
LAUF=$(cd "$SKRIPTE/.." && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$LAUF/rohdaten}"
# Die gefahrenen Werkzeuge der v1.2-Anfahrt bleiben in ihrem Verzeichnis.
WERKZEUGE="${WERKZEUGE:-$SKRIPTE/../../2026-09-v12-messung/skripte}"
PROBE_ROUTE="${PROBE_ROUTE:-$SKRIPTE/11-probe-route.py}"
NULLSTAND="${NULLSTAND:-$SKRIPTE/93b-nullstand.sh}"
TEILKORPUS="${TEILKORPUS:-$SKRIPTE/01-teilkorpus.py}"
STATUSBEOBACHTER="${STATUSBEOBACHTER:-$WERKZEUGE/96d-statusbeobachter.py}"
RSS_SAMPLER="${RSS_SAMPLER:-$REPO/scripts/ops/rss_sampler.sh}"
ANON_SAMPLER="${ANON_SAMPLER:-$REPO/scripts/ops/proc_anon_sampler.sh}"
CPU_SAMPLER="${CPU_SAMPLER:-$REPO/scripts/ops/cpu_sampler.sh}"
LAUFWERTE="${LAUFWERTE:-$HOME/work/v14-lauf.env}"

CONTAINER="${CONTAINER:-nc_app_findling_backend}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
DB_CONTAINER="${DB_CONTAINER:-nextcloud-aio-database}"
DB_PREFIX="${DB_PREFIX:-oc_}"
DAEMON="${DAEMON:-harp_aio}"
APP_ID="${APP_ID:-findling_backend}"
ABBILD_REPO="${ABBILD_REPO:-ghcr.io/street1983nk/findling_backend}"
IMAGE_TAG="${IMAGE_TAG:-dev}"
ADRESSE="${ADRESSE:-https://loadtest.infranode.dev}"
BENUTZER="${BENUTZER:-admin}"
# Die Zaehlung wie in 92d-wechsel.sh, woertlich.
SERVER_IMAGES="${SERVER_IMAGES:-(^|/)aio-nextcloud:|(^|/)nextcloud:}"
CGROUP_ROOT="${CGROUP_ROOT:-/sys/fs/cgroup}"
DROP_CACHES="${DROP_CACHES:-/proc/sys/vm/drop_caches}"
ERWARTETE_GRENZE="${ERWARTETE_GRENZE:-2147483648}"
ERWARTETER_SWAP="${ERWARTETER_SWAP:-0}"

# Fristen und Takte in Sekunden.
BEWAFFNUNG_FRIST="${BEWAFFNUNG_FRIST:-300}"
BEWAFFNUNG_TAKT="${BEWAFFNUNG_TAKT:-10}"
WIRK_FRIST="${WIRK_FRIST:-1800}"
WIRK_TAKT="${WIRK_TAKT:-30}"
KORPUS_FRIST="${KORPUS_FRIST:-360}"
ENDE_FRIST="${ENDE_FRIST:-108000}"
ENDE_TAKT="${ENDE_TAKT:-120}"
RUHE="${RUHE:-120}"
STATUS_TAKT="${STATUS_TAKT:-120}"
CPU_TAKT="${CPU_TAKT:-5}"
ZELLE_KORPUS="${ZELLE_KORPUS:-voll}"

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: ./10-zelle.sh <box> <zelle> <economy|standard|performance> <int8|fp32>

fp32 nur mit standard oder performance. Die Laufwerte (ABBILD_DIGEST, GRENZE_2G,
PWFILE) stehen in LAUFWERTE, Vorgabe $HOME/work/v14-lauf.env; der Korpus kommt
aus ZELLE_KORPUS (voll oder teil).
HINWEIS
}

verweigern() {
    echo "10-zelle: $1" >&2
    benutzung
    exit 2
}

laufwert() {
    [ -r "$LAUFWERTE" ] || return 0
    awk -v name="$1" 'index($0, name "=") == 1 {
        wert = substr($0, length(name) + 2)
        gsub(/^["\047]|["\047]$/, "", wert)
        print wert
        exit
    }' "$LAUFWERTE"
}

ist_zahl() {
    case "${1:-}" in
    '' | *[!0-9]*) return 1 ;;
    esac
    return 0
}

name_pruefen() {
    case "$2" in
    '' | *[!A-Za-z0-9._-]*) verweigern "$1 '$2' ist kein Name aus Buchstaben, Ziffern, Punkt, Strich" ;;
    esac
}

[ "$#" -eq 4 ] || verweigern "vier Argumente, nicht $#"
BOX=$1
ZELLE=$2
PROFIL=$3
PRAEZISION=$4
name_pruefen box "$BOX"
name_pruefen zelle "$ZELLE"
case "$PROFIL" in
economy | standard | performance) ;;
*) verweigern "unbekanntes Profil '$PROFIL'" ;;
esac
case "$PRAEZISION" in
int8 | fp32) ;;
*) verweigern "unbekannte Praezision '$PRAEZISION'" ;;
esac
[ "$PRAEZISION" = int8 ] || [ "$PROFIL" != economy ] || verweigern "fp32 gibt es nur mit standard oder performance"
case "$ZELLE_KORPUS" in
voll | teil) ;;
*) verweigern "ZELLE_KORPUS muss voll oder teil sein" ;;
esac

ABBILD_DIGEST=$(laufwert ABBILD_DIGEST)
case "$ABBILD_DIGEST" in
sha256:*) hex=${ABBILD_DIGEST#sha256:} ;;
*) verweigern "ABBILD_DIGEST fehlt oder hat nicht die Form sha256:<64 Hexziffern>" ;;
esac
case "$hex" in
'' | *[!0-9a-f]*) verweigern "ABBILD_DIGEST hat nicht die Form sha256:<64 Hexziffern>" ;;
esac
[ "${#hex}" -eq 64 ] || verweigern "ABBILD_DIGEST hat nicht die Form sha256:<64 Hexziffern>"
GRENZE_2G=$(laufwert GRENZE_2G)
case "$GRENZE_2G" in
ja | nein) ;;
*) verweigern "GRENZE_2G muss ja oder nein sein" ;;
esac
PWFILE=$(laufwert PWFILE)
PWFILE="${PWFILE:-$HOME/work/.pw/admin}"
wert=$(laufwert ADRESSE)
[ -z "$wert" ] || ADRESSE=$wert
IMAGE="$ABBILD_REPO@$ABBILD_DIGEST"

ZOUT="$OUT/$BOX/$ZELLE"
if [ -d "$ZOUT" ] && [ -n "$(ls -A "$ZOUT" 2>/dev/null)" ]; then
    echo "10-zelle: das Rohdatenverzeichnis der Zelle ist nicht leer, eine Zelle misst nur einmal" >&2
    exit 59
fi
mkdir -p "$ZOUT"
ZELLDATEI="$ZOUT/10-zelle.txt"
OCCLOG="$ZOUT/10-zelle-befehle.txt"
WORK=$(mktemp -d)
chmod 700 "$WORK"
: >"$WORK/pids"

# Die Werkzeuge der Probe lesen Adresse, Konto und Passwortdatei aus der
# Umgebung, das Passwort selbst liest nur 11-probe-route.py.
FINDLING_BASE_URL=$ADRESSE
FINDLING_ADMIN_USER=$BENUTZER
FINDLING_ADMIN_PWFILE=$PWFILE
export FINDLING_BASE_URL FINDLING_ADMIN_USER FINDLING_ADMIN_PWFILE

sampler_stoppen() {
    while read -r pid; do
        [ -n "$pid" ] || continue
        sudo kill -TERM "$pid" 2>/dev/null || true
    done <"$WORK/pids"
    : >"$WORK/pids"
}

aufraeumen() {
    sampler_stoppen
    rm -rf "$WORK"
}
trap aufraeumen EXIT

utc() {
    date -u +%Y-%m-%dT%H:%M:%SZ
}

zeile() {
    printf '%s\n' "$*" >>"$ZELLDATEI"
    printf '%s\n' "$*"
}

ablegen() {
    cat "$1" >>"$ZELLDATEI"
    cat "$1"
}

schritt() {
    zeile "schritt $1 $(utc)"
}

abbruch() {
    code=$1
    shift
    zeile "zelle-abbruch rueckgabe $code grund $* $(utc)"
    echo "10-zelle: $*" >&2
    exit "$code"
}

occ() {
    sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
}

db_lesen() {
    # Eine SQL-Zeile gegen die Nextcloud-Datenbank, psql -At im DB-Container.
    # Benutzer und Datenbank kommen aus der Umgebung des Containers, kein
    # Passwort auf einer Kommandozeile (T-28-10). Ein Fehler liefert unlesbar.
    sudo docker exec "$DB_CONTAINER" sh -c \
        'exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "$1"' psql "$1" \
        2>/dev/null || printf 'unlesbar\n'
}

route() {
    python3 "$PROBE_ROUTE" "$@"
}

uebersicht() {
    route uebersicht 2>/dev/null || true
}

feld() {
    printf '%s\n' "$2" | tr ' ' '\n' | sed -n "s/^$1=//p" | head -n 1
}

jetzt() {
    date +%s
}

nextclouds_zaehlen() {
    anzahl=$(sudo docker ps --format '{{.Image}}' 2>/dev/null | grep -Ec "$SERVER_IMAGES" || true)
    case "${anzahl:-}" in
    '' | *[!0-9]*) printf 'unlesbar\n' ;;
    *) printf '%s\n' "$anzahl" ;;
    esac
}

scope_von() {
    cid=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER" 2>/dev/null || true)
    [ -n "${cid:-}" ] || return 1
    printf '%s/system.slice/docker-%s.scope\n' "$CGROUP_ROOT" "$cid"
}

cgroup_wert() {
    pfad=$(scope_von) || {
        printf 'unlesbar\n'
        return 0
    }
    sudo cat "$pfad/$1" 2>/dev/null || printf 'unlesbar\n'
}

vorrat_von() {
    awk '/^Work stock/ {found = 1; next}
         found && /^  (scheduled|handed to the worker)/ {sum += $NF}
         END {print sum + 0}' "$1"
}

bewaffnen() {
    occ app_api:app:disable "$APP_ID" >>"$OCCLOG" 2>&1 || true
    occ app_api:app:enable "$APP_ID" >>"$OCCLOG" 2>&1 || true
}

zeile "zelle-start $ZELLE box $BOX ziel $PROFIL/$PRAEZISION korpus $ZELLE_KORPUS $(utc)"
zeile "abbild-digest $ABBILD_DIGEST"

# --- 1. Der Abwaertsweg, vor jedem Nullstand (Pitfall 2) ---------------------
schritt abwaerts
abwaerts_status=0
route abwaerts >"$WORK/abwaerts.txt" 2>&1 || abwaerts_status=$?
ablegen "$WORK/abwaerts.txt"
[ "$abwaerts_status" -eq 0 ] || abbruch 60 "der Abwaertsweg auf economy/int8 hat nicht gespeichert ($abwaerts_status)"

# --- 2. und 3. Die Zaehlung, unmittelbar vor dem --rm-data (T-28-07) ---------
schritt zaehlung-eine-nextcloud
nextclouds_zaehlen >"$WORK/instanzen"
zeile "nextcloud-instanzen $(cat "$WORK/instanzen")"
[ "$(cat "$WORK/instanzen")" = 1 ] || abbruch 61 "nicht genau eine Nextcloud, ein --rm-data traefe jede Instanz"
schritt nullstand
if ! occ app_api:app:unregister "$APP_ID" --rm-data >>"$OCCLOG" 2>&1; then
    occ app_api:app:unregister "$APP_ID" --rm-data --force >>"$OCCLOG" 2>&1 ||
        abbruch 62 "unregister --rm-data ist gescheitert"
fi
zeile "unregister-rm-data ja"

# --- 4. Registrierung, Abbild per Digest --------------------------------------
schritt registrierung
sudo docker pull "$IMAGE" >>"$OCCLOG" 2>&1 || abbruch 63 "das Abbild laesst sich nicht per Digest ziehen"
sudo docker tag "$IMAGE" "$ABBILD_REPO:$IMAGE_TAG" >>"$OCCLOG" 2>&1 || abbruch 63 "das Abbild laesst sich nicht auf den Tag legen"
# Die Kopie der info.xml entsteht AUSSERHALB des Arbeitsbaums, damit der
# Baumhash daneben gilt (T-10-18).
sed "s|<image-tag>[^<]*</image-tag>|<image-tag>$IMAGE_TAG</image-tag>|" \
    "$REPO/backend/appinfo/info.xml" >"$WORK/10-info-box.xml"
cp "$WORK/10-info-box.xml" "$ZOUT/10-info-box.xml"
sudo docker cp "$WORK/10-info-box.xml" "$NEXTCLOUD:/tmp/10-info-box.xml" >>"$OCCLOG" 2>&1 || true
sudo docker exec "$NEXTCLOUD" chown 33:33 /tmp/10-info-box.xml >>"$OCCLOG" 2>&1 || true
register_status=0
occ app_api:app:register "$APP_ID" "$DAEMON" --info-xml /tmp/10-info-box.xml --wait-finish \
    >>"$OCCLOG" 2>&1 || register_status=$?
zeile "registrierung-rueckgabewert $register_status"
[ "$register_status" -eq 0 ] || abbruch 63 "die Registrierung ist gescheitert"

# --- 4b. Das Vorrats-Tor, VOR der Bewaffnung (BLOCKER-28-07) ------------------
# Die Position traegt, weil vor der Bewaffnung kein Container nachschieben
# kann: ein Vorrat ungleich 0 ist hier zwingend Altbestand eines frueheren
# Laufs (Lauf 3: 3420 Altauftraege). Lauf-4-Beleg fuer die Verschiebung: der
# frisch bewaffnete Container zieht sich den Crawl binnen 6-16 s selbst ueber
# die Top-up-Route (POST /queues/documents/topup -> CrawlAdvanceService,
# first_index_scheduled=1 ueberlebt --rm-data); am 93b-Schritt sah das Tor
# deshalb frische fileids (54347 ff.) statt Altbestand und war unpassierbar.
# bestand_lesen() ist erst nach dem Trigger definiert, hier wird inline
# gelesen.
schritt vorrat-tor
occ findling:index >"$WORK/vorrat-tor.txt" 2>&1 || true
altvorrat=$(vorrat_von "$WORK/vorrat-tor.txt")
zeile "vorrat-tor altvorrat $altvorrat"
if [ "$altvorrat" != 0 ]; then
    abbruch 73 "der Arbeitsvorrat traegt $altvorrat Altauftraege eines frueheren Laufs, --rm-data raeumt die NC-Queue nicht"
fi

# --- 5. Bewaffnung, Beleg backendReachable true (Block 11) --------------------
schritt bewaffnung
bewaffnen
beginn=$(jetzt)
while :; do
    erreichbar=$(feld backendReachable "$(uebersicht)")
    [ "$erreichbar" != true ] || break
    vergangen=$(($(jetzt) - beginn))
    if [ "$vergangen" -ge "$BEWAFFNUNG_FRIST" ]; then
        zeile "bewaffnung backendReachable ${erreichbar:-unlesbar} nach-s $vergangen"
        abbruch 65 "backendReachable wird nicht true"
    fi
    sleep "$BEWAFFNUNG_TAKT"
done
zeile "bewaffnung backendReachable true nach-s $(($(jetzt) - beginn))"

# --- 6. Die Grenze, nur auf m7g.large (Block 12, D-28-03, D-28-12) -------------
schritt grenze
if [ "$GRENZE_2G" = ja ]; then
    sudo docker update --memory=2g --memory-swap=2g "$CONTAINER" >>"$OCCLOG" 2>&1 || true
    grenze=$(cgroup_wert memory.max)
    swap=$(cgroup_wert memory.swap.max)
    zeile "speichergrenze-ist $grenze/$swap"
    if [ "$grenze" = "$ERWARTETE_GRENZE" ] && [ "$swap" = "$ERWARTETER_SWAP" ]; then
        zeile "grenze-gesetzt ja"
    else
        zeile "grenze-gesetzt nein"
        abbruch 64 "die Grenze 2g/0 steht nicht in der cgroup"
    fi
else
    zeile "grenze keine"
fi

# --- 7. Der Baumhash, als Skript gerufen, und im laufenden Container ----------
schritt baumhash
baumhash_status=0
IMAGE="$IMAGE" OUT="$ZOUT" REPO="$REPO" sh "$WERKZEUGE/40b-baumhash.sh" \
    >>"$OCCLOG" 2>&1 || baumhash_status=$?
zeile "40b-baumhash-rueckgabewert $baumhash_status"
BAUMHASH="$ZOUT/40b-baumhash.txt"
gezaehlt=0
[ ! -s "$BAUMHASH" ] || gezaehlt=$(grep -c '^baumhash: ' "$BAUMHASH" || true)
if [ "$gezaehlt" -ne 3 ] || ! grep -q '^baumhash-gleich ja$' "$BAUMHASH"; then
    zeile "baumhash-beweis nein zeilen $gezaehlt"
    abbruch 66 "kein Baumhash-Beweis"
fi
abbild_hash=$(sed -n 's/^abbild-baumhash: //p' "$BAUMHASH" | head -n 1)
sudo docker cp "$WERKZEUGE/40b-baumhash.py" "$CONTAINER:/tmp/40b-baumhash.py" >>"$OCCLOG" 2>&1 || true
lauf_hash=$(sudo docker exec "$CONTAINER" /app/.venv/bin/python /tmp/40b-baumhash.py \
    /app/.venv/lib/python3.13/site-packages/findling '**/*.py' 2>/dev/null |
    sed -n 's/^baumhash: //p' | head -n 1)
zeile "baumhash-im-laufenden-container ${lauf_hash:-unlesbar}"
if [ -z "${abbild_hash:-}" ] || [ "${lauf_hash:-}" != "$abbild_hash" ]; then
    abbruch 66 "der laufende Container traegt ein anderes Paket als das gepruefte Abbild"
fi
zeile "baumhash-beweis ja"

# --- 8. Der Nullstand, gelesen und nicht angestossen --------------------------
schritt 93b-nullstand
nullstand_status=0
OUT="$ZOUT" sh "$NULLSTAND" >>"$OCCLOG" 2>&1 || nullstand_status=$?
zeile "93b-nullstand-rueckgabewert $nullstand_status"
# Quelle 4 wird hier nur protokolliert: frische Befuellung am 93b-Schritt ist
# unschaedlich, der Trigger (findling:index --restart) raeumt sie seit 93i
# selbst. Das Altbestand-Urteil (Abbruch 73) faellt am vorrat-tor VOR der
# Bewaffnung.
[ "$nullstand_status" -eq 0 ] || abbruch 67 "der Nullstand ist nicht leer oder nicht lesbar"

# --- 9. Seitencache leeren ------------------------------------------------------
schritt drop-caches
sync
echo 3 | sudo tee "$DROP_CACHES" >/dev/null
zeile "caches-geleert ja"

# --- 10. Die Probe ueber die Produktroute (D-28-05) ---------------------------
schritt probe
if [ "$PROFIL" = economy ]; then
    zeile "probe keine abwaertsweg"
else
    probe_status=0
    route pruefen "$PROFIL" "$PRAEZISION" >"$ZOUT/11-probe.txt" 2>&1 || probe_status=$?
    zeile "probe-rueckgabewert $probe_status"
    case "$probe_status" in
    0) zeile "erzwungen nein" ;;
    30 | 31)
        letzte=$(grep '^verdikt ' "$ZOUT/11-probe.txt" | tail -n 1 || true)
        verdikt=$(printf '%s\n' "$letzte" | awk '{print $2}')
        ursache=$(printf '%s\n' "$letzte" | awk '{print $4}')
        occ config:app:set findling profile --value="$PROFIL" >>"$OCCLOG" 2>&1 ||
            abbruch 68 "occ konnte das Profil nicht erzwingen"
        if [ "$PRAEZISION" = fp32 ]; then
            occ config:app:set findling model_precision --value=fp32 >>"$OCCLOG" 2>&1 ||
                abbruch 68 "occ konnte die Praezision nicht erzwingen"
        fi
        zeile "erzwungen ja grund ${verdikt:-unlesbar}/${ursache:-unlesbar}"
        ;;
    *) abbruch 68 "die Probe endete mit $probe_status" ;;
    esac
fi

# --- 11. Das Wirksamkeitstor (Pitfall 1, T-28-11) -----------------------------
schritt wirksamkeit
beginn=$(jetzt)
neu=nein
while :; do
    stand=$(uebersicht)
    wirksam=$(feld effective "$stand")
    slots=$(feld slotsInForce "$stand")
    if [ "$wirksam" = "$PROFIL" ] && ist_zahl "$slots"; then
        break
    fi
    vergangen=$(($(jetzt) - beginn))
    if [ "$vergangen" -ge "$WIRK_FRIST" ]; then
        zeile "wirksamkeit nein effective ${wirksam:-unlesbar} nach-s $vergangen"
        abbruch 69 "effective ist nach $vergangen s nicht $PROFIL, kein Trigger"
    fi
    if [ "$neu" = nein ] && [ $((vergangen * 2)) -ge "$WIRK_FRIST" ]; then
        bewaffnen
        neu=ja
        zeile "wirksamkeit neu-bewaffnet $(utc)"
    fi
    sleep "$WIRK_TAKT"
done
zeile "$stand"
zeile "wirksamkeit ja effective $wirksam slotsInForce $slots nach-s $(($(jetzt) - beginn))"

# --- 12. Die Sampler, vor dem Trigger -------------------------------------------
schritt sampler
setsid nohup sudo sh "$RSS_SAMPLER" "$CONTAINER" 2 "$ZOUT/rss.csv" \
    >"$ZOUT/rss.log" 2>&1 </dev/null &
printf '%s\n' "$!" >>"$WORK/pids"
setsid nohup sudo sh "$ANON_SAMPLER" "$CONTAINER" 1 "$ZOUT/anon.csv" \
    >"$ZOUT/anon.log" 2>&1 </dev/null &
printf '%s\n' "$!" >>"$WORK/pids"
setsid nohup sudo sh "$CPU_SAMPLER" "$CONTAINER" "$CPU_TAKT" "$ZOUT/cpu.csv" \
    >"$ZOUT/cpu.log" 2>&1 </dev/null &
printf '%s\n' "$!" >>"$WORK/pids"
setsid nohup python3 "$STATUSBEOBACHTER" "$ZOUT/96d-status.jsonl" "$STATUS_TAKT" "$PWFILE" "$ADRESSE" \
    --user "$BENUTZER" >"$WORK/96d.log" 2>&1 </dev/null &
printf '%s\n' "$!" >>"$WORK/pids"
zeile "sampler rss 2 anon 1 cpu $CPU_TAKT status $STATUS_TAKT gestartet $(utc)"

# --- 13. Der Trigger, mit -n ----------------------------------------------------
schritt trigger
# Die Zaehlmarke des Zaehltors, gelesen unmittelbar VOR dem Trigger (nur
# Teilkorpus): max(updated_at) ueber die file_state-Tabelle. Alles, was die
# Zelle selbst schreibt, liegt strikt danach; Altzustaende liegen davor.
# Das Format-Tor haelt die Marke aus der SQL-Einsetzung heraus: nur Ziffern,
# Bindestrich, Doppelpunkt, Punkt und Leerzeichen. Ohne lesbare Marke ist
# das Zaehltor nicht pruefbar, die Zelle darf nicht messen (Abbruch 71).
if [ "$ZELLE_KORPUS" = teil ]; then
    marke=$(db_lesen "select coalesce(max(updated_at), timestamp '1970-01-01 00:00:00') from ${DB_PREFIX}findling_file_state")
    case "$marke" in
    '' | *[!0-9.:\ -]*) abbruch 71 "zaehlmarke unlesbar" ;;
    esac
    zeile "zaehlmarke $marke"
fi
trigger_status=0
occ findling:index --restart -n >"$WORK/trigger.txt" 2>&1 || trigger_status=$?
ablegen "$WORK/trigger.txt"
if [ "$trigger_status" -ne 0 ] || grep -q 'Nothing was changed' "$WORK/trigger.txt"; then
    abbruch 70 "der Trigger hat nichts angestossen"
fi
zeile "trigger ja $(utc)"

bestand_lesen() {
    occ findling:index >"$WORK/bestand.txt" 2>&1 || true
}

if [ "$ZELLE_KORPUS" = teil ]; then
    # Das Zaehltor nach dem Crawl (T-28-03): was der Vorrat kennt, plus die
    # FRISCHEN Endzustaende der Zelle, plus was das Backend schon EINGEBETTET
    # hat. indexiert zaehlt nicht mit: der Vorrat sinkt im Takt von embedded,
    # eine Index-Fertigstellung ist vorratsneutral, indexiert steckt also
    # einmal im Vorrat und einmal in indexed (Beleg Abbruch 71: summe 6937
    # statt 5000). Die Endzustaende kommen NICHT aus den globalen occ-Zaehlern:
    # oc_findling_file_state ueberlebt --rm-data UND --restart, Lauf 5 zaehlte
    # darum 5041 = 5000 Teilkorpus-Dateien + 41 fremde Altzustaende und brach
    # faelschlich ab. Gezaehlt werden nur Zeilen mit updated_at nach der
    # Zaehlmarke des Triggers UND Pfad files/teilkorpus/% (Join oc_filecache):
    # zeit- und pfadscharf statt global.
    # Gegen das Leserace (bestand und uebersicht liegen Sekunden auseinander)
    # wird embedded vor und nach bestand_lesen gelesen und nur bei Gleichheit
    # gewertet, hoechstens 6 Versuche.
    sleep "$KORPUS_FRIST"
    eingebettet=unlesbar
    stand=''
    frisch=unlesbar
    versuch=0
    while [ "$versuch" -lt 6 ]; do
        versuch=$((versuch + 1))
        vorher=$(feld embedded "$(uebersicht)")
        bestand_lesen
        frisch=$(db_lesen "select s.state, count(*)
  from ${DB_PREFIX}findling_file_state s
  join ${DB_PREFIX}filecache f on f.fileid = s.file_id
 where s.state in ('skipped','failed')
   and s.updated_at > timestamp '$marke'
   and f.path like 'files/teilkorpus/%'
 group by s.state")
        stand=$(uebersicht)
        nachher=$(feld embedded "$stand")
        if ist_zahl "$vorher" && [ "$vorher" = "$nachher" ]; then
            eingebettet=$nachher
            break
        fi
    done
    [ "$eingebettet" != unlesbar ] || zeile "zaehlung-instabil nach-versuchen $versuch"
    vorrat=$(vorrat_von "$WORK/bestand.txt")
    # Fehlende Staaten fehlen in der group-by-Ausgabe als Zeile: auf 0
    # vorbelegen. Ein unlesbarer DB-Stand bleibt unlesbar, das Zaehltor
    # scheitert dann ueber die ist_zahl-Pruefung.
    uebersprungen=0
    fehlgeschlagen=0
    case "$frisch" in
    *unlesbar*)
        uebersprungen=unlesbar
        fehlgeschlagen=unlesbar
        ;;
    *)
        wert=$(printf '%s\n' "$frisch" | awk -F'|' '$1 == "skipped" {print $2; exit}')
        [ -z "$wert" ] || uebersprungen=$wert
        wert=$(printf '%s\n' "$frisch" | awk -F'|' '$1 == "failed" {print $2; exit}')
        [ -z "$wert" ] || fehlgeschlagen=$wert
        ;;
    esac
    indexiert=$(feld indexed "$stand")
    summe=unlesbar
    if ist_zahl "$vorrat" && ist_zahl "$uebersprungen" && ist_zahl "$fehlgeschlagen" && ist_zahl "$eingebettet"; then
        summe=$((vorrat + uebersprungen + fehlgeschlagen + eingebettet))
    fi
    zeile "zaehlung vorrat $vorrat uebersprungen-frisch ${uebersprungen:-unlesbar} fehlgeschlagen-frisch ${fehlgeschlagen:-unlesbar} eingebettet ${eingebettet:-unlesbar} indexiert ${indexiert:-unlesbar} summe $summe"
    zaehltor_status=0
    python3 "$TEILKORPUS" zaehltor "$summe" >"$WORK/zaehltor.txt" 2>&1 || zaehltor_status=$?
    ablegen "$WORK/zaehltor.txt"
    [ "$zaehltor_status" -eq 0 ] || abbruch 71 "das Zaehltor 5000 ist verfehlt ($summe)"
fi

# --- 14. Das Ende: Vorrat 0, embedded == indexed, zweimal ---------------------
schritt ende
beginn=$(jetzt)
treffer=0
absenkung=nein
while :; do
    bestand_lesen
    vorrat=$(vorrat_von "$WORK/bestand.txt")
    stand=$(uebersicht)
    indexiert=$(feld indexed "$stand")
    eingebettet=$(feld embedded "$stand")
    waechter=$(feld guardEffective "$stand")
    gedrosselt=$(feld throttled "$stand")
    zeile "lesung t=$(($(jetzt) - beginn))s vorrat $vorrat indexed ${indexiert:-unlesbar} embedded ${eingebettet:-unlesbar} guard ${waechter:-unlesbar} throttled ${gedrosselt:-unlesbar}"
    case "${waechter:-}" in
    '' | keine | unlesbar | "$PROFIL") ;;
    *) absenkung=ja ;;
    esac
    [ "$gedrosselt" != true ] || absenkung=ja
    # indexed ueber 0, damit der leere Anfang vor dem ersten Cron-Lauf kein Ende ist.
    if [ "$vorrat" = 0 ] && ist_zahl "$indexiert" && [ "$indexiert" -gt 0 ] && [ "$indexiert" = "$eingebettet" ]; then
        treffer=$((treffer + 1))
    else
        treffer=0
    fi
    [ "$treffer" -lt 2 ] || break
    if [ $(($(jetzt) - beginn)) -ge "$ENDE_FRIST" ]; then
        abbruch 72 "das Ende kam nicht in $ENDE_FRIST s"
    fi
    sleep "$ENDE_TAKT"
done
zeile "ende vorrat 0 embedded gleich indexed zweimal $(utc)"

# --- 15. Nachlauf: Ruhezeit, Grundlast, guard-Block ---------------------------
schritt nachlauf
sleep "$RUHE"
anon=$(cgroup_wert memory.stat | awk '$1 == "anon" {print $2; exit}')
zeile "grundlast anon ${anon:-unlesbar} nach-ruhe-s $RUHE"
stand=$(uebersicht)
zeile "guard effective=$(feld guardEffective "$stand") cause=$(feld guardCause "$stand") throttled=$(feld throttled "$stand") slotsInForce=$(feld slotsInForce "$stand")"
zeile "waechter-absenkung $absenkung"
# Die OOM-Schlusszeile, solange Container und cgroup stehen: nach dem Stopp der
# Box sind beide weg. OOMKilled und RestartCount sagen, ob der Hauptprozess
# fiel; oom_kill aus memory.events zaehlt auch einen getoeteten Kindprozess
# (OCR, ein docker exec eines Abtasters), der keinen Neustart ausloest.
oom_zustand=$(sudo docker inspect -f '{{.State.OOMKilled}} {{.RestartCount}} {{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || printf 'unlesbar unlesbar unlesbar')
oom_ereignisse=$(cgroup_wert memory.events)
oom_zahl=$(echo "$oom_ereignisse" | awk '$1 == "oom" {print $2; exit}')
oom_kills=$(echo "$oom_ereignisse" | awk '$1 == "oom_kill" {print $2; exit}')
oom_getoetet=$(echo "$oom_zustand" | awk '{print $1}')
oom_neustarts=$(echo "$oom_zustand" | awk '{print $2}')
oom_start=$(echo "$oom_zustand" | awk '{print $3}')
zeile "oom oomkilled ${oom_getoetet:-unlesbar} restartcount ${oom_neustarts:-unlesbar} containerstart ${oom_start:-unlesbar} memory-events oom ${oom_zahl:-unlesbar} oom_kill ${oom_kills:-unlesbar}"
sampler_stoppen

# --- 16. Abholen ------------------------------------------------------------------
schritt abholen
# Das Protokoll des Statusbeobachters kann die Adresse tragen; abgelegt wird es
# nur mit Platzhalter (T-28-10).
sed "s|$ADRESSE|<adresse>|g" "$WORK/96d.log" >"$ZOUT/96d.log" 2>/dev/null || : >"$ZOUT/96d.log"
zeile "abholbereit ja dateien $(ls "$ZOUT" | wc -l | tr -d ' ')"
zeile "10-ZELLE-FERTIG $ZELLE"
