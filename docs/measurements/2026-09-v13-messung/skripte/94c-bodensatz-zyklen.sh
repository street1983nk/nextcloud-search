#!/bin/sh
# Der Bodensatz-Zyklus 2 des v1.3-Laufs, MESS-07 Punkt 3.
#
# NACHFOLGEFASSUNG von
# docs/measurements/2026-09-v12-messung/skripte/94b-grundlast-rueckkehr.sh.
# 94b ist gefahren, pruefsummengeschuetzt und bleibt unberuehrt; alles, was hier
# anders ist, steht in dieser Datei und nicht als Aenderung dort.
#
# DIESE FASSUNG IST NICHT GEFAHREN. Neben ihr liegt keine Rohdatei; was sie auf
# der Box misst, misst die v1.3-Anfahrt.
#
# **Die Frage, die 94b offengelassen hat.** Der v1.2-Lauf hat EINEN Zyklus
# gemessen: Marke A nach dem Neustart 103,9 MB, Marke C nach Indexlauf und
# Entladung 731,9 MB, ein Bodensatz von 628,0 MB. Das ist weit mehr als die rund
# 16 MB des Vorprueflaufs vom 19.09.2026, und eine Zahl aus einem Zyklus sagt
# nicht, ob der Rest einmal anfaellt und dann steht oder mit jedem Indexlauf
# weiter waechst. Das zweite waere ein Leck, das erste ein Preis. Beantwortet
# wird das nur von einem zweiten Zyklus im SELBEN Containerleben.
#
# **Was dieses Werkzeug misst.** Marke A nach dem Neustart, dann Zyklus 1
# (Korpus hochladen, files:scan, warten bis eingebettet und Arbeitsvorrat leer,
# Entladung abwarten), Marke C1, dann Zyklus 2 identisch in einem zweiten
# Ordner, Marke C2. Die beiden Ergebniszeilen sind zyklus2-minus-a und
# zyklus2-minus-c1. Liegt die zweite nahe null, ist der Bodensatz ein Preis, der
# einmal anfaellt; waechst sie um den Betrag von C1 minus A, waechst er mit
# jedem Lauf.
#
# **Die zwei Aenderungen gegen 94b.**
#
#   1  Zwei Zyklen statt einem, OHNE Containerneubau dazwischen. Zwischen C1
#      und C2 steht kein Neustart, kein Neubau und kein Aufruf des
#      Umgebungswerkzeugs; ein Gate in test_v13_zyklen.py haelt das fest. Die
#      Stellung des Entladeschalters setzt das Ablaufskript VOR diesem Werkzeug
#      per 92e-umgebung.sh FINDLING_EMBED_IDLE_RELEASE_SECONDS=120, und danach
#      zurueck; dieses Werkzeug liest sie nur.
#   2  Die Stellung muss 120 sein und nicht nur groesser null. Die Ruhezeit
#      unten rechnet mit 120 s; eine andere Stellung liesse die Entladung vor
#      oder nach der Ablesung fallen, und das Werkzeug endet dann mit 47.
#
# **Was ausdruecklich gleich bleibt.** anon aus memory.stat und nicht
# memory.current, die Helfer anon_von, mb_von, differenz_mb (unbestimmt statt
# 0) und protokoll, der Weg eines Nutzers fuer den Indexlauf (WebDAV und
# files:scan, nie findling:index --restart), die Admin-Seite als Quelle fuer
# engineState und embedded, der Abtaster rss_sampler.sh unveraendert gerufen,
# und die Rueckgabewerte 29, 31, 32, 33 in ihrer Bedeutung aus 94b.
#
# **Woher das Passwort kommt.** Zuerst aus der Umgebungsvariablen, deren NAMEN
# PASSWORT_ENV traegt, sonst aus der Datei, auf die PWFILE zeigt. Es landet in
# einer Datei unter WORK mit Modus 600 und von dort in einer curl-Konfiguration
# (-K); auf einer Kommandozeile steht es nie (T-22-11).
#
# Die Exit-Codes setzen den Katalog fort, 46 und 47 sind neu:
#
#   2  das Werkzeug wurde mit einem Argument gerufen, das es nicht gibt
#   29 die Stellung des Entladeschalters war nicht ablesbar
#   31 nach Ruhezeit und Karenz stand kein unloaded
#   32 eine Marke oder die Abtastreihe hat keine Zahl hergegeben
#   33 ein Zyklus hat keinen Indexlauf ausgeloest, oder der Container hat die
#      Reihe zwischen den Marken zerrissen
#   46 ein Zyklus ist nicht abgeschlossen: kein Passwort, Upload unvollstaendig,
#      Frist ueberschritten, oder der Block ist nicht bis zu seinem Ende gelaufen
#   47 die Stellung des Entladeschalters ist beim Start nicht 120
set -eu

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: 94c-bodensatz-zyklen.sh

Ohne Argument. Dieses Werkzeug misst in EINEM Containerleben: Marke A nach dem
Neustart, Zyklus 1, Marke C1, Zyklus 2, Marke C2. Die Differenz zweier Marken
ist nur innerhalb eines Containerlebens eine Aussage, darum gibt es keinen
Zuschnitt, der einen Zyklus allein faehrt.

Der Entladeschalter muss vorher auf 120 stehen (Umgebungswerkzeug 92e). Stellschrauben
stehen als Umgebungsvariablen im Kopf der Datei, darunter ZYKLUS_DECKEL,
RUHEZEIT, KARENZ und INDEXLAUF_DATEIEN.
HINWEIS
}

if [ "$#" -ne 0 ]; then
    benutzung
    exit 2
fi

SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
ADRESSE="${ADRESSE:-https://loadtest.infranode.dev}"
BENUTZER="${BENUTZER:-admin}"
# Der NAME der Umgebungsvariablen, nicht ihr Wert (T-10-27, T-15-06).
PASSWORT_ENV="${PASSWORT_ENV:-FINDLING_ADMIN_PASSWORD}"
# Die Datei, aus der das Passwort kommt, wenn die Umgebung es nicht traegt. Die
# Vorgabe ist die von 96-volllauf.sh desselben Kontos.
PWFILE="${PWFILE:-$HOME/work/.pw/admin}"
UEBERSICHT="${UEBERSICHT:-/apps/findling/admin/overview}"
# Die Stellung, die der Entladeschalter beim Start haben muss, und die Ruhezeit,
# die daraus folgt. D-02 vom 19.09.2026: 120 s statt 900 s, derselbe
# Mechanismus und Stunden gesparte Box-Zeit.
ENTLADESCHALTER_SOLL="${ENTLADESCHALTER_SOLL:-120}"
RUHEZEIT="${RUHEZEIT:-$ENTLADESCHALTER_SOLL}"
KARENZ="${KARENZ:-45}"
ABTASTINTERVALL="${ABTASTINTERVALL:-5}"
# Die Frist je Zyklus in Sekunden, vom Upload bis zum leeren Arbeitsvorrat. 900 s
# sind der Boden aus 94b (Poller-Backoff bis 300 s, zwei Cron-Runden).
ZYKLUS_DECKEL="${ZYKLUS_DECKEL:-900}"
BEREIT_DECKEL="${BEREIT_DECKEL:-180}"
SAMPLER="${SAMPLER:-$REPO/scripts/ops/rss_sampler.sh}"
DIGEST="${DIGEST:-$REPO/scripts/ops/rss_digest.py}"
ORDNER="${ORDNER:-mess07-bodensatz}"
INDEXLAUF_DATEIEN="${INDEXLAUF_DATEIEN:-12}"

mkdir -p "$OUT"
ZIEL="${ZIEL:-$OUT/94c-bodensatz-zyklen.txt}"
WORK=$(mktemp -d)
chmod 700 "$WORK"
ABTASTUNG="$WORK/abtastung"
mkdir -p "$ABTASTUNG"

ABTAST_PID=''
aufraeumen() {
    if [ -n "${ABTAST_PID:-}" ]; then
        sudo kill -TERM "$ABTAST_PID" 2>/dev/null || true
    fi
    rm -rf "$WORK"
}
trap aufraeumen EXIT

# Das Passwort ohne abschliessenden Zeilenumbruch: er reiste sonst als %0A mit.
PWFELD="$WORK/pwfeld"
: >"$PWFELD"
chmod 600 "$PWFELD"
eval "printf '%s' \"\${$PASSWORT_ENV:-}\"" >"$PWFELD"
PASSWORT_QUELLE=umgebung
if [ ! -s "$PWFELD" ]; then
    sudo cat "$PWFILE" 2>/dev/null | tr -d '\n' >"$PWFELD" || true
    PASSWORT_QUELLE=datei
fi
if [ ! -s "$PWFELD" ]; then
    PASSWORT_QUELLE=keine
fi
CURLRC="$WORK/curlrc"
: >"$CURLRC"
chmod 600 "$CURLRC"
{
    printf 'user = "%s:' "$BENUTZER"
    cat "$PWFELD"
    printf '"\n'
} >"$CURLRC"
JAR="$WORK/cookies.txt"

LAUF=$(date -u +%Y%m%dT%H%M%SZ)
BASISORDNER="$ADRESSE/remote.php/dav/files/$BENUTZER"

occ() {
    sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
}

vorrat_von() {
    awk '/^Work stock/ {found = 1; next}
         found && /^  (scheduled|handed to the worker)/ {sum += $NF}
         END {print sum + 0}' "$1"
}

scope_von() {
    cid=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER" 2>/dev/null || true)
    [ -n "${cid:-}" ] || return 1
    printf '/sys/fs/cgroup/system.slice/docker-%s.scope\n' "$cid"
}

cgroup_wert() {
    pfad=$(scope_von) || {
        printf 'unlesbar\n'
        return 0
    }
    sudo cat "$pfad/$1" 2>/dev/null || printf 'unlesbar\n'
}

anon_von() {
    pfad=$(scope_von) || {
        printf 'unlesbar\n'
        return 0
    }
    wert=$(sudo cat "$pfad/memory.stat" 2>/dev/null | awk '$1 == "anon" {print $2; exit}')
    [ -n "${wert:-}" ] || wert=unlesbar
    printf '%s\n' "$wert"
}

mb_von() {
    case "${1:-}" in
    '' | *[!0-9]*)
        printf 'unlesbar\n'
        return 0
        ;;
    esac
    awk -v bytes="$1" 'BEGIN { printf "%.1f\n", bytes / 1048576 }'
}

# Ist eine der beiden Marken keine Zahl, heisst das Ergebnis unbestimmt und nicht
# null: eine Null laese sich als gemessene Null.
differenz_mb() {
    case "${1:-}${2:-}" in
    '' | *[!0-9]*)
        printf 'unbestimmt\n'
        return 0
        ;;
    esac
    awk -v links="$1" -v rechts="$2" 'BEGIN { printf "%.1f\n", (links - rechts) / 1048576 }'
}

protokoll() {
    printf '%s\n' "$*" >>"$WORK/protokollblock"
    printf '%s\n' "$*"
}

containerstart() {
    start=$(sudo docker inspect --format '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || true)
    [ -n "${start:-}" ] || start=unlesbar
    printf '%s\n' "$start"
}

anmelden() {
    rm -f "$JAR"
    curl -sfS -c "$JAR" -o "$WORK/login.html" "$ADRESSE/login" || return 1
    zeichen=$(sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' "$WORK/login.html" | head -1)
    [ -n "${zeichen:-}" ] || return 1
    weiter=$(curl -sS -b "$JAR" -c "$JAR" -o /dev/null -w '%{redirect_url}' \
        -H "Origin: $ADRESSE" \
        --data-urlencode "user=$BENUTZER" \
        --data-urlencode "password@$PWFELD" \
        --data-urlencode "requesttoken=$zeichen" \
        "$ADRESSE/login" || true)
    case "$weiter" in
    '' | */login | */login\?*) return 1 ;;
    esac
    curl -sfS -b "$JAR" -c "$JAR" -o "$WORK/nach-anmeldung.html" "$ADRESSE/settings/admin" || return 1
    zeichen=$(sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' "$WORK/nach-anmeldung.html" | head -1)
    [ -n "${zeichen:-}" ] || return 1
    printf '%s\n' "$zeichen" >"$WORK/token"
    return 0
}

# Die Admin-Seite; ihr Lesen laedt kein Modell.
uebersicht_holen() {
    zeichen=$(cat "$WORK/token" 2>/dev/null || true)
    : >"$WORK/uebersicht.json"
    [ -n "${zeichen:-}" ] || return 0
    curl -sS -b "$JAR" -c "$JAR" -H 'Accept: application/json' \
        -H "requesttoken: $zeichen" -o "$WORK/uebersicht.json" \
        "$ADRESSE$UEBERSICHT" 2>/dev/null || : >"$WORK/uebersicht.json"
    return 0
}

engine_zustand() {
    uebersicht_holen
    zustand=$(sed -n 's/.*"engineState"[[:space:]]*:[[:space:]]*"\([A-Za-z_]*\)".*/\1/p' \
        "$WORK/uebersicht.json" 2>/dev/null | head -1)
    [ -n "${zustand:-}" ] || zustand=unbekannt
    printf '%s\n' "$zustand"
}

eingebettet() {
    uebersicht_holen
    zahl=$(sed -n 's/.*"embedded"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p' \
        "$WORK/uebersicht.json" 2>/dev/null | head -1)
    [ -n "${zahl:-}" ] || zahl=unlesbar
    printf '%s\n' "$zahl"
}

bereit_warten() {
    versuch=0
    while [ "$versuch" -lt "$BEREIT_DECKEL" ]; do
        versuch=$((versuch + 1))
        zustand=$(engine_zustand)
        if [ "$zustand" != unbekannt ]; then
            printf 'bereit-nach-s %s zustand %s\n' "$versuch" "$zustand"
            return 0
        fi
        sleep 1
    done
    printf 'bereit-nach-s ueber-deckel-%s\n' "$BEREIT_DECKEL"
    return 1
}

# Eine Marke: anon und memory.current, und der Containerstart daneben, damit die
# Reihe gegen den Start von Marke A gehalten werden kann.
marke() {
    name=$1
    wert=$(anon_von)
    printf '%s\n' "$wert" >"$WORK/$name"
    protokoll "$name $(mb_von "$wert") MB anon $wert byte"
    protokoll "$name-memory-current $(cgroup_wert memory.current)"
    protokoll "$name-engine-zustand $(engine_zustand)"
    case "$wert" in
    '' | *[!0-9]*) : >"$WORK/keine-zahl" ;;
    esac
    start=$(containerstart)
    protokoll "$name-containerstart $start"
    if [ "$start" != "$(cat "$WORK/containerstart-a" 2>/dev/null || echo unlesbar)" ]; then
        : >"$WORK/reihe-unterbrochen"
    fi
}

# Ein Zyklus. Jeder bekommt seinen eigenen Ordner und seinen eigenen
# Dateiinhalt, damit die Einbettungsspur im zweiten Zyklus wirklich neue
# Dokumente vor sich hat. Er setzt WEITER=nein und eine Arbeitsdatei, wenn er
# nicht abschliesst; ein exit stuende hier in der Subshell des tee-Blocks und
# verliesse nur sie.
zyklus() {
    n=$1
    zielordner="$ORDNER/$LAUF-c$n"
    printf '%s\n' "$zielordner" >>"$WORK/ordner"
    echo "=== Zyklus $n: Korpus nach $zielordner, files:scan, warten ==="
    vorher=$(eingebettet)
    occ findling:index >"$WORK/status-vorher-$n.txt" 2>&1 || true
    protokoll "zyklus$n-vorher eingebettet $vorher arbeitsvorrat $(vorrat_von "$WORK/status-vorher-$n.txt")"

    mkdir -p "$WORK/korpus-$n"
    nummer=1
    while [ "$nummer" -le "$INDEXLAUF_DATEIEN" ]; do
        {
            printf 'Messlauf %s, Zyklus %s, Datei %s von %s.\n' "$LAUF" "$n" "$nummer" "$INDEXLAUF_DATEIEN"
            printf 'Dieser Text gehoert zum Bodensatz-Zyklus der v1.3-Anfahrt und dient einem\n'
            printf 'Zweck: die Einbettungsspur des Containers ein weiteres Mal in Gang zu bringen.\n'
            printf 'Bescheid, Antrag, Vermerk, Protokoll, Gebuehrenordnung, Widerspruch.\n'
            printf 'Der Ordner wird nach der letzten Marke wieder entfernt.\n'
        } >"$WORK/korpus-$n/mess07-$LAUF-c$n-$nummer.txt"
        nummer=$((nummer + 1))
    done
    curl -sS -o /dev/null -K "$CURLRC" -X MKCOL "$BASISORDNER/$ORDNER" || true
    curl -sS -o /dev/null -K "$CURLRC" -X MKCOL "$BASISORDNER/$zielordner" || true
    : >"$WORK/upload-$n.txt"
    for pfad in "$WORK/korpus-$n"/*; do
        name=$(basename "$pfad")
        code=$(curl -sS -o /dev/null -w '%{http_code}' -K "$CURLRC" \
            -T "$pfad" "$BASISORDNER/$zielordner/$name" || echo 000)
        printf '%s %s\n' "$code" "$name" >>"$WORK/upload-$n.txt"
    done
    hochgeladen=$(awk '$1 ~ /^2/ {n++} END {print n + 0}' "$WORK/upload-$n.txt")
    protokoll "zyklus$n-hochgeladen $hochgeladen von $INDEXLAUF_DATEIEN"
    if [ "$hochgeladen" -ne "$INDEXLAUF_DATEIEN" ]; then
        printf 'zyklus %s upload %s von %s\n' "$n" "$hochgeladen" "$INDEXLAUF_DATEIEN" >>"$WORK/zyklus-offen"
        WEITER=nein
        return 0
    fi
    occ files:scan --path="/$BENUTZER/files/$zielordner" 2>&1 | tail -4 || true

    date -u +"zyklus$n-start %Y-%m-%dT%H:%M:%SZ"
    beginn=$(date +%s)
    verstrichen=0
    nachher="$vorher"
    vorrat=unklar
    fertig=nein
    while [ "$verstrichen" -le "$ZYKLUS_DECKEL" ]; do
        sleep 15
        verstrichen=$(($(date +%s) - beginn))
        nachher=$(eingebettet)
        occ findling:index >"$WORK/status-nachher-$n.txt" 2>&1 || true
        vorrat=$(vorrat_von "$WORK/status-nachher-$n.txt")
        printf 'zyklus%s-zwischenstand s=%s eingebettet=%s arbeitsvorrat=%s\n' \
            "$n" "$verstrichen" "$nachher" "$vorrat"
        case "$vorher$nachher$vorrat" in
        *[!0-9]*) continue ;;
        esac
        if [ "$nachher" -gt "$vorher" ] && [ "$vorrat" -eq 0 ]; then
            fertig=ja
            break
        fi
    done
    date -u +"zyklus$n-ende %Y-%m-%dT%H:%M:%SZ"
    protokoll "zyklus$n-nachher eingebettet $nachher arbeitsvorrat $vorrat"
    protokoll "zyklus$n-dauer-s $verstrichen von hoechstens $ZYKLUS_DECKEL"

    bewegt=nein
    case "$vorher$nachher" in
    '' | *[!0-9]*) ;;
    *)
        if [ "$nachher" -gt "$vorher" ]; then
            bewegt=ja
        fi
        ;;
    esac
    protokoll "zyklus$n-indexlauf-stattgefunden $bewegt"
    if [ "$bewegt" != ja ]; then
        printf 'zyklus %s\n' "$n" >>"$WORK/kein-indexlauf"
        WEITER=nein
        return 0
    fi
    if [ "$fertig" != ja ]; then
        printf 'zyklus %s frist %s s ueberschritten, arbeitsvorrat %s\n' \
            "$n" "$ZYKLUS_DECKEL" "$vorrat" >>"$WORK/zyklus-offen"
        WEITER=nein
        return 0
    fi

    echo "-- Die Ruhezeit: $RUHEZEIT s plus $KARENZ s Karenz, dann muss unloaded stehen --"
    sleep "$((RUHEZEIT + KARENZ))"
    zustand=$(engine_zustand)
    protokoll "zyklus$n-engine-zustand-nach-ruhezeit $zustand"
    if [ "$zustand" != unloaded ]; then
        printf 'zyklus %s zustand %s\n' "$n" "$zustand" >>"$WORK/keine-entladung"
        WEITER=nein
    fi
    return 0
}

{
    date -u +'bodensatz-zyklen-start %Y-%m-%dT%H:%M:%SZ'
    printf 'ruhezeit %s s, karenz %s s, abtastintervall %s s, zyklus-deckel %s s, dateien je zyklus %s\n' \
        "$RUHEZEIT" "$KARENZ" "$ABTASTINTERVALL" "$ZYKLUS_DECKEL" "$INDEXLAUF_DATEIEN"
    printf 'abtaster %s, digest %s, beide unveraendert gerufen\n' "$SAMPLER" "$DIGEST"
    printf 'nachbar-container %s, laufkennung %s\n' "$NEXTCLOUD" "$LAUF"
    # Bezug v1.2 (94b, 21.09.2026): marke-a 103,9 MB, marke-c 731,9 MB,
    # Bodensatz 628,0 MB. Er steht hier als Kommentar und nicht als Zeile der
    # Rohdatei, damit keine Zahl eines anderen Laufs in dieser gelesen wird.

    echo "=== 1. Die Pflichtzeilen, VOR der Messung ==="
    protokoll "passwort-quelle $PASSWORT_QUELLE"
    if [ "$PASSWORT_QUELLE" = keine ]; then
        printf 'kein passwort in %s und keines in PWFILE\n' "$PASSWORT_ENV" >>"$WORK/zyklus-offen"
    fi

    if sudo docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$CONTAINER" \
        >"$WORK/umgebung" 2>/dev/null; then
        SCHALTER=$(awk -F= '/^FINDLING_EMBED_IDLE_RELEASE_SECONDS=/ {print $2; exit}' "$WORK/umgebung")
        if [ -z "${SCHALTER:-}" ]; then
            SCHALTER=0
            protokoll "entladeschalter-ist $SCHALTER werksstand"
        else
            protokoll "entladeschalter-ist $SCHALTER"
        fi
    else
        SCHALTER=unlesbar
        protokoll "entladeschalter-ist unlesbar"
        : >"$WORK/schalter-unlesbar"
    fi
    case "$SCHALTER" in
    unlesbar) ;;
    '' | *[!0-9]*)
        protokoll "entladeschalter-passt-zum-block nein, kein Zahlenwert"
        : >"$WORK/schalter-unlesbar"
        ;;
    *)
        if [ "$SCHALTER" -eq "$ENTLADESCHALTER_SOLL" ]; then
            protokoll "entladeschalter-passt-zum-block ja, $ENTLADESCHALTER_SOLL"
        else
            protokoll "entladeschalter-passt-zum-block nein, verlangt sind $ENTLADESCHALTER_SOLL"
            : >"$WORK/schalter-nicht-soll"
        fi
        ;;
    esac
    protokoll "speichergrenze-ist $(cgroup_wert memory.max)/$(cgroup_wert memory.swap.max)"

    if [ -f "$WORK/schalter-unlesbar" ] || [ -f "$WORK/schalter-nicht-soll" ] || [ -f "$WORK/zyklus-offen" ]; then
        echo "-- Eine Pflichtzeile fehlt oder steht gegen diesen Block. Gemessen wird nichts,"
        echo "   und der Lauf endet unterhalb der Pipeline. --"
        WEITER=nein
    else
        WEITER=ja
    fi

    if [ "$WEITER" = ja ]; then
        echo "=== 2. Neustart und Marke A ==="
        echo "-- Der einzige Neustart dieses Werkzeugs. Danach bleibt der Container bis"
        echo "   Marke C2 derselbe. --"
        sudo docker restart "$CONTAINER" >/dev/null
        containerstart >"$WORK/containerstart-a"
        protokoll "containerstart-nach-neustart $(cat "$WORK/containerstart-a")"
        if anmelden; then
            echo "anmeldung ok"
        else
            echo "anmeldung fehlgeschlagen, engineState und embedded bleiben unlesbar"
        fi
        bereit_warten || echo "-- Bereitschaftsdeckel gerissen, gemessen wird trotzdem --"
        sudo "$SAMPLER" "$CONTAINER" "$ABTASTINTERVALL" "$ABTASTUNG/$CONTAINER.csv" \
            >"$WORK/sampler.log" 2>&1 &
        ABTAST_PID=$!
        marke marke-a
    fi

    if [ "$WEITER" = ja ]; then
        zyklus 1
    fi
    if [ "$WEITER" = ja ]; then
        marke marke-c1
    fi
    if [ "$WEITER" = ja ]; then
        zyklus 2
    fi
    if [ "$WEITER" = ja ]; then
        marke marke-c2
    fi

    if [ -n "${ABTAST_PID:-}" ]; then
        sudo kill -TERM "$ABTAST_PID" 2>/dev/null || true
        wait "$ABTAST_PID" 2>/dev/null || true
        ABTAST_PID=''
        echo "-- rss_digest.py ueber die Abtastreihe von Marke A bis zum Ende --"
        if python3 "$DIGEST" "$ABTASTUNG" >"$WORK/digest.txt" 2>"$WORK/digest.err"; then
            cat "$WORK/digest.txt"
        else
            sed 's/^/  /' "$WORK/digest.err" 2>/dev/null || true
        fi
        # Die erste ganze Zahl der Zeile und nicht alle Ziffern des Feldes nach
        # dem ersten Doppelpunkt: rss_digest.py schreibt "total, peak: 1698 MB,
        # at 2026-09-25T23:15:00Z", und das Feld reicht bis in die Uhrzeit. Die
        # Vorgaengerin 94b klebte so Datum und Stunde an die Megabyte
        # (11142026092103 in ihrer Rohdatei); Befund der Generalprobe 22-06.
        SPITZE=$(awk '/^total, peak:/ {
                for (i = 3; i <= NF; i++) if ($i ~ /^[0-9]+$/) { print $i; exit }
                exit
            }' "$WORK/digest.txt" 2>/dev/null || true)
        [ -n "${SPITZE:-}" ] || SPITZE=unlesbar
        protokoll "abtastreihe-spitze-mb $SPITZE"
        if [ "$SPITZE" = unlesbar ] && [ "$WEITER" = ja ]; then
            : >"$WORK/keine-zahl"
        fi
    fi

    if [ "$WEITER" = ja ]; then
        echo "=== 3. Das Ergebnis ==="
        A=$(cat "$WORK/marke-a" 2>/dev/null || echo unlesbar)
        C1=$(cat "$WORK/marke-c1" 2>/dev/null || echo unlesbar)
        C2=$(cat "$WORK/marke-c2" 2>/dev/null || echo unlesbar)
        protokoll "zyklus1-minus-a $(differenz_mb "$C1" "$A")"
        protokoll "zyklus2-minus-a $(differenz_mb "$C2" "$A")"
        protokoll "zyklus2-minus-c1 $(differenz_mb "$C2" "$C1")"
        echo "-- zyklus2-minus-c1 nahe null: der Bodensatz faellt einmal an. Nahe"
        echo "   zyklus1-minus-a: er waechst mit jedem Indexlauf. --"
    fi

    echo "=== 4. Die Ordner der Zyklen, wieder entfernt ==="
    if [ -f "$WORK/ordner" ]; then
        while IFS= read -r zielordner; do
            entfernt=$(curl -sS -o /dev/null -w '%{http_code}' -K "$CURLRC" \
                -X DELETE "$BASISORDNER/$zielordner" || echo 000)
            protokoll "ordner-entfernt $entfernt $zielordner"
        done <"$WORK/ordner"
    fi

    echo "=== Der Protokollblock, als Block zitierbar ==="
    cat "$WORK/protokollblock"
    date -u +'bodensatz-zyklen-ende %Y-%m-%dT%H:%M:%SZ'
    : >"$WORK/block-durchgelaufen"
} 2>&1 | tee "$ZIEL"

# Unterhalb der Pipeline, und nur hier: der Rueckgabewert einer Pipeline, die in
# tee endet, gehoert zu tee. Gelesen wird aus den Arbeitsdateien unter WORK, in
# der Reihenfolge des Ablaufs.
if [ -f "$WORK/schalter-unlesbar" ]; then
    echo "94c-bodensatz-zyklen: die Stellung des Entladeschalters war nicht ablesbar" >&2
    exit 29
fi
if [ -f "$WORK/schalter-nicht-soll" ]; then
    echo "94c-bodensatz-zyklen: der Entladeschalter steht nicht auf $ENTLADESCHALTER_SOLL" >&2
    echo "94c-bodensatz-zyklen: das Ablaufskript setzt ihn vorher per 92e-umgebung.sh" >&2
    exit 47
fi
if [ -f "$WORK/zyklus-offen" ]; then
    echo "94c-bodensatz-zyklen: ein Zyklus ist nicht abgeschlossen" >&2
    cat "$WORK/zyklus-offen" >&2
    exit 46
fi
if [ -f "$WORK/kein-indexlauf" ]; then
    echo "94c-bodensatz-zyklen: der Stand der eingebetteten Dokumente hat sich nicht bewegt" >&2
    cat "$WORK/kein-indexlauf" >&2
    exit 33
fi
if [ -f "$WORK/reihe-unterbrochen" ]; then
    echo "94c-bodensatz-zyklen: der Container wurde zwischen den Marken neu gestartet" >&2
    echo "94c-bodensatz-zyklen: die Differenz waere ein Neustart und kein Bodensatz" >&2
    exit 33
fi
if [ -f "$WORK/keine-entladung" ]; then
    echo "94c-bodensatz-zyklen: nach Ruhezeit und Karenz stand kein unloaded" >&2
    cat "$WORK/keine-entladung" >&2
    exit 31
fi
if [ -f "$WORK/keine-zahl" ]; then
    echo "94c-bodensatz-zyklen: eine Marke oder die Abtastreihe hat keine Zahl hergegeben" >&2
    exit 32
fi
# Fail closed: ohne die Endmarke ist der Block irgendwo abgebrochen, und ohne
# diese Zeile endete das Werkzeug dann mit 0 (Klasse L-03, deferred-items 22-02).
if [ ! -f "$WORK/block-durchgelaufen" ]; then
    echo "94c-bodensatz-zyklen: der Block ist nicht bis zu seinem Ende gelaufen" >&2
    exit 46
fi

echo "94C-BODENSATZ-ZYKLEN-FERTIG"
