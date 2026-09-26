#!/bin/sh
# Der Produktcontainer, neu gebaut mit genau einer geaenderten
# Umgebungsvariable, fuer die v1.3-Anfahrt.
#
# **DIESE FASSUNG IST NICHT GEFAHREN.** Neben ihr liegt keine Rohdatei. Ihr
# Abnahmekriterium ist Form, statische Analyse, ein Lauf gegen einen
# nachgestellten Docker-Klienten in backend/tests/test_v13_wechsel.py und die
# Generalprobe gegen die lokale Test-Nextcloud. Was sie auf der Box bewirkt,
# misst erst die Anfahrt.
#
# **Wozu.** Zwei Messbloecke der Anfahrt brauchen denselben Container mit einer
# anderen Stellung: der Umbau (MESS-08) eine andere Sprachmenge in
# FINDLING_LANGUAGES, der Bodensatz (94c) einen Entladeschalter
# FINDLING_EMBED_IDLE_RELEASE_SECONDS ungleich 0 und danach wieder 0. Eine
# Registrierung ueber AppAPI kaeme dafuer nicht in Frage: sie laeuft ueber die
# info.xml, und jede Aenderung dort waere eine Aenderung des Arbeitsbaums, gegen
# den der Baumhash gefuehrt wird. Der Container wird deshalb aus seinem eigenen
# docker inspect nachgebaut, nach dem Muster des Schritts "Store upgrade 6" in
# .github/workflows/deploy-harp.yml, der denselben Neubau fuer
# FINDLING_LANGUAGES in der CI faehrt.
#
# **Genau ein Schalter, und nur einer von zweien.** Das Argument hat die Gestalt
# NAME=WERT, und NAME ist FINDLING_LANGUAGES oder
# FINDLING_EMBED_IDLE_RELEASE_SECONDS. Jeder andere Name endet mit 2, bevor eine
# Rohdatei entsteht. FINDLING_OCR_LANGUAGES wird ausdruecklich verweigert: die
# OCR-Sprachen sind kein Messgegenstand dieser Anfahrt, und ein Neubau, der sie
# verstellt, liesse jede OCR-Zahl danach gegen eine andere Maschine laufen. Der
# Wert wird gegen eine enge Zeichenmenge geprueft, weil er als Zeile in eine
# env-Datei geht: Kleinbuchstaben und Komma fuer die Sprachen, Ziffern fuer die
# Sekunden.
#
# **Was aus dem inspect uebernommen wird**, und nur das: Abbild, Umgebung ohne
# die Zielzeile plus die neue Zeile, Mounts (volume und bind), Labels,
# Restart-Policy und NetworkMode. Das Netz wird aus .HostConfig.NetworkMode
# uebernommen und nicht als host verlangt: auf der Box laeuft der Container im
# Netz, das AppAPI ihm gegeben hat, und die CI-Fassung kennt nur den Fall host.
# Dazu die Netzaliase des alten Containers in diesem Netz, und traegt er keinen,
# die App-Kennung: HaRP findet die ExApp nach seinem naechsten Neustart sonst
# nicht mehr (Befund der Anfahrt am 26.09.2026, README 6.4).
# Entrypoint und Cmd werden gegen das Abbild geprueft und nicht uebernommen;
# ueberschreibt der Container eins von beiden, endet das Werkzeug mit 43, bevor
# etwas entfernt wird. Traegt der Container unter /certs/frp die drei Dateien des
# HaRP-Tunnels, werden sie in den neuen Container getragen, bevor er startet
# (Befund des CI-Laufs 35997241359, Kopf des Schritts in deploy-harp.yml);
# traegt er sie nicht, steht das als Zeile in der Rohdatei.
#
# **Die Umgebung traegt APP_SECRET.** Ausgegeben werden deshalb nur die Namen
# der Umgebung (cut -d= -f1) und der Wert des einen Schalters, nie eine ganze
# Zeile. Die env-Datei liegt unter WORK mit Rechten 600 und faellt mit dem trap
# weg.
#
# **Was ein Neubau wegwirft, wird neu gesetzt und zurueckgelesen**, wie in
# Schritt 11 und 12 von 92c: docker update --memory=2g --memory-swap=2g, danach
# memory.max und memory.swap.max AUS DER CGROUP gegen 2147483648 und 0
# (Swap-Anteil, siehe 92c), sonst 42; daneben die Zeilen schalter-ist und
# entladeschalter-ist aus der Umgebung des neuen Containers.
#
# Die Rueckgabewerte, im Katalog dieses Laufverzeichnisses:
#
#   2  kein Argument, mehr als eines, keine Gestalt NAME=WERT, ein Name, der
#      kein Schalter dieses Werkzeugs ist, oder ein Wert ausserhalb seiner
#      Zeichenmenge
#   42 die harte Grenze steht nach dem Neubau nicht in der cgroup
#   43 der Container ist nicht in der Gestalt, die dieses Werkzeug nachbauen
#      kann (inspect unlesbar, Entrypoint oder Cmd ueberschrieben, ein Mount
#      ausser volume und bind, keine Umgebung), oder der Neubau selbst ist
#      gescheitert, oder der neue Container traegt den Schalter nicht mit dem
#      geforderten Wert. Ist der alte Container da schon entfernt, stellt 92d
#      ihn ueber die Registrierung wieder her.
#
# Die Zeilen, die dieses Werkzeug schreibt:
#
#   neubau-start, schalter-gefordert, container-lesbar, abbild-ist,
#   netz-ist, restart-ist, netz-aliase, entrypoint-gleich, umgebung-namen, schalter-vorher,
#   mounts-uebernommen, labels-uebernommen, tunnel-zertifikate,
#   neubau-gelungen, speichergrenze-ist, grenze-erwartet, grenze-gesetzt,
#   schalter-ist, entladeschalter-ist, neubau-fertig
set -eu

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: ./92e-umgebung.sh NAME=WERT

Genau ein Argument. NAME ist FINDLING_LANGUAGES (WERT aus Kleinbuchstaben und
Komma, etwa de,en,fr) oder FINDLING_EMBED_IDLE_RELEASE_SECONDS (WERT aus
Ziffern, 0 schaltet das Entladen ab). Die OCR-Sprachen stellt dieses Werkzeug
nicht um. Die uebrigen Stellschrauben stehen als Umgebungsvariablen im Kopf der
Datei, darunter CONTAINER, OUT, ERWARTETE_GRENZE und ERWARTETER_SWAP.
HINWEIS
}

if [ "$#" -ne 1 ]; then
    benutzung
    exit 2
fi
ZUWEISUNG=$1
case "$ZUWEISUNG" in
?*=*) ;;
*)
    echo "92e-umgebung: das Argument hat nicht die Gestalt NAME=WERT" >&2
    benutzung
    exit 2
    ;;
esac
SCHALTER=${ZUWEISUNG%%=*}
WERT=${ZUWEISUNG#*=}

# Geprueft BEVOR ein Verzeichnis angelegt oder eine Rohdatei geschrieben wird.
case "$SCHALTER" in
FINDLING_LANGUAGES)
    case "$WERT" in
    '' | *[!a-z,]*)
        echo "92e-umgebung: der Wert fuer $SCHALTER besteht nicht nur aus Kleinbuchstaben und Komma" >&2
        benutzung
        exit 2
        ;;
    esac
    ;;
FINDLING_EMBED_IDLE_RELEASE_SECONDS)
    case "$WERT" in
    '' | *[!0-9]*)
        echo "92e-umgebung: der Wert fuer $SCHALTER besteht nicht nur aus Ziffern" >&2
        benutzung
        exit 2
        ;;
    esac
    ;;
FINDLING_OCR_LANGUAGES) { echo "92e-umgebung: FINDLING_OCR_LANGUAGES wird verweigert, die OCR-Sprachen sind kein Messgegenstand" >&2; benutzung; exit 2; } ;;
*)
    echo "92e-umgebung: $SCHALTER ist kein Schalter dieses Werkzeugs" >&2
    benutzung
    exit 2
    ;;
esac

# Alles, worin sich zwei Maschinen unterscheiden koennen, ist eine Variable mit
# Vorgabe.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
OUT="${OUT:-$SKRIPTE/../rohdaten}"
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
# Die App-Kennung der ExApp, unter der HaRP sie im Netz sucht; der Alias des
# Neubaus, wenn der alte Container keinen traegt.
APP_KENNUNG="${APP_KENNUNG:-findling_backend}"
# Die harte Grenze in Byte und der Swap-Anteil, so wie die cgroup sie meldet;
# dieselben Vorgaben und dieselbe Begruendung wie in 92c.
ERWARTETE_GRENZE="${ERWARTETE_GRENZE:-2147483648}"
ERWARTETER_SWAP="${ERWARTETER_SWAP:-0}"
# Der Name des Entladeschalters aus Phase 14, fuer die Zeile entladeschalter-ist.
ENTLADESCHALTER="${ENTLADESCHALTER:-FINDLING_EMBED_IDLE_RELEASE_SECONDS}"

mkdir -p "$OUT"
ZIEL="${ZIEL:-$OUT/92e-umgebung-$SCHALTER-$(date -u +%Y%m%dT%H%M%SZ).txt}"
umask 077
WORK=$(mktemp -d)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT
ENVDATEI="$WORK/umgebung-neu.list"

# Die cgroup des Containers, nach dem Muster von 92c. Die Kennung wird jedes Mal
# neu gelesen, weil der Neubau sie wechselt.
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

# Ein Feld des inspect, ueber eine Vorlage und ohne jq, das auf der Box nicht
# vorausgesetzt ist.
feld() {
    sudo docker inspect --format "$1" "$CONTAINER" 2>/dev/null
}

# Der Wert EINES Namens aus einer Umgebungsliste, und nur dieser eine.
wert_von() {
    awk -v name="$1" 'index($0, name "=") == 1 { print substr($0, length(name) + 2); exit }' "$2"
}

{
    date -u +'neubau-start %Y-%m-%dT%H:%M:%SZ'
    printf 'schalter-gefordert %s %s\n' "$SCHALTER" "$WERT"

    echo "=== 1. Der Container, wie er jetzt laeuft, aus docker inspect ==="
    if sudo docker inspect "$CONTAINER" >"$WORK/inspect.json" 2>/dev/null; then
        echo "container-lesbar ja"
    else
        echo "container-lesbar nein"
        : >"$WORK/gestalt-fremd"
    fi

    if [ ! -f "$WORK/gestalt-fremd" ]; then
        abbild=$(feld '{{.Config.Image}}' || true)
        netz=$(feld '{{.HostConfig.NetworkMode}}' || true)
        restart=$(feld '{{.HostConfig.RestartPolicy.Name}}' || true)
        printf 'abbild-ist %s\n' "${abbild:-unlesbar}"
        printf 'netz-ist %s\n' "${netz:-unlesbar}"
        printf 'restart-ist %s\n' "${restart:-keine}"
        if [ -z "${abbild:-}" ] || [ -z "${netz:-}" ]; then
            : >"$WORK/gestalt-fremd"
        fi
    fi

    if [ ! -f "$WORK/gestalt-fremd" ]; then
        # Die Netzaliase (Nachtrag 26.09.2026, Befund README 6.4 der Anfahrt).
        # HaRP loest die ExApp ueber ihre App-Kennung im Namensdienst des Netzes
        # auf; ein Neubau ohne Alias ist nach dem naechsten Neustart von HaRP
        # nicht mehr erreichbar. Uebernommen werden die Aliase des alten
        # Containers in genau diesem Netz, ohne seinen Namen und ohne seine
        # Kurzkennung, die Docker jedem Container von selbst gibt. Traegt er
        # keinen, bekommt der neue die App-Kennung. Die Netze host, bridge und
        # none kennen keine Aliase.
        : >"$WORK/aliase.list"
        case "$netz" in
        host | bridge | none | container:*)
            echo "netz-aliase keine quelle netz-ohne-aliase"
            ;;
        *)
            kurz=$(feld '{{.Id}}' | cut -c1-12 || true)
            feld '{{range $name, $netz := .NetworkSettings.Networks}}{{range $netz.Aliases}}{{$name}}|{{.}}{{println}}{{end}}{{end}}' |
                awk -F'|' -v netz="$netz" -v name="$CONTAINER" -v kurz="${kurz:-}" \
                    '$1 == netz && $2 != "" && $2 != name && $2 != kurz && !gesehen[$2]++ { print $2 }' \
                    >"$WORK/aliase.list" || true
            if [ -s "$WORK/aliase.list" ]; then
                printf 'netz-aliase %s quelle alter-container\n' "$(tr '\n' ' ' <"$WORK/aliase.list")"
            else
                printf '%s\n' "$APP_KENNUNG" >"$WORK/aliase.list"
                printf 'netz-aliase %s quelle app-kennung\n' "$APP_KENNUNG"
            fi
            ;;
        esac
    fi

    if [ ! -f "$WORK/gestalt-fremd" ]; then
        echo "=== 2. Entrypoint und Cmd gegen das Abbild, nicht uebernommen ==="
        for vorlage in '{{json .Config.Entrypoint}}' '{{json .Config.Cmd}}'; do
            meins=$(feld "$vorlage" || printf 'unlesbar')
            seins=$(sudo docker image inspect --format "$vorlage" "$abbild" 2>/dev/null || printf 'unlesbar')
            if [ "$meins" = unlesbar ] || [ "$meins" != "$seins" ]; then
                printf 'entrypoint-gleich nein %s: %s gegen %s im Abbild\n' "$vorlage" "$meins" "$seins"
                : >"$WORK/gestalt-fremd"
            fi
        done
        if [ ! -f "$WORK/gestalt-fremd" ]; then
            echo "entrypoint-gleich ja"
        fi
    fi

    if [ ! -f "$WORK/gestalt-fremd" ]; then
        echo "=== 3. Die Umgebung, ohne die Zielzeile und mit der neuen ==="
        feld '{{range .Config.Env}}{{println .}}{{end}}' >"$WORK/umgebung-alt.list" || true
        chmod 600 "$WORK/umgebung-alt.list"
        grep -v "^$SCHALTER=" "$WORK/umgebung-alt.list" | grep -v '^$' >"$ENVDATEI" || true
        chmod 600 "$ENVDATEI"
        if [ ! -s "$ENVDATEI" ]; then
            echo "umgebung-namen keine"
            : >"$WORK/gestalt-fremd"
        else
            vorher=$(wert_von "$SCHALTER" "$WORK/umgebung-alt.list")
            printf 'schalter-vorher %s %s\n' "$SCHALTER" "${vorher:-nicht-gesetzt}"
            printf '%s=%s\n' "$SCHALTER" "$WERT" >>"$ENVDATEI"
            # Die Namen und nie die Werte: APP_SECRET steht in dieser Liste.
            printf 'umgebung-namen %s\n' "$(cut -d= -f1 "$ENVDATEI" | sort | tr '\n' ' ')"
        fi
    fi

    if [ ! -f "$WORK/gestalt-fremd" ]; then
        echo "=== 4. Mounts und Labels ==="
        feld '{{range .Mounts}}{{.Type}}|{{.Name}}|{{.Source}}|{{.Destination}}|{{.RW}}{{println}}{{end}}' |
            awk -F'|' '
                $1 == "volume" { printf "type=volume,source=%s,target=%s%s\n", $2, $4, ($5 == "true" ? "" : ",readonly"); next }
                $1 == "bind" { printf "type=bind,source=%s,target=%s%s\n", $3, $4, ($5 == "true" ? "" : ",readonly"); next }
                NF > 0 { print "UNSUPPORTED " $1 }
            ' >"$WORK/mounts.list" || true
        if grep -q '^UNSUPPORTED' "$WORK/mounts.list"; then
            echo "mounts-uebernommen nein"
            cat "$WORK/mounts.list"
            : >"$WORK/gestalt-fremd"
        else
            printf 'mounts-uebernommen %s\n' "$(tr '\n' ' ' <"$WORK/mounts.list")"
        fi
        feld '{{range $name, $wert := .Config.Labels}}{{$name}}={{$wert}}{{println}}{{end}}' |
            grep -v '^$' >"$WORK/labels.list" || true
        printf 'labels-uebernommen %s\n' "$(cut -d= -f1 "$WORK/labels.list" | tr '\n' ' ')"
    fi

    if [ ! -f "$WORK/gestalt-fremd" ]; then
        echo "=== 5. Die Zertifikate des HaRP-Tunnels, falls der Container welche traegt ==="
        if sudo docker exec "$CONTAINER" sh -c \
            'test -r /certs/frp/client.crt && test -r /certs/frp/client.key && test -r /certs/frp/ca.crt' \
            2>/dev/null; then
            if sudo docker cp "$CONTAINER:/certs/frp" - >"$WORK/zertifikate.tar" 2>/dev/null; then
                echo "tunnel-zertifikate uebernommen"
            else
                echo "tunnel-zertifikate unlesbar"
                : >"$WORK/gestalt-fremd"
            fi
        else
            echo "tunnel-zertifikate keine"
        fi
    fi

    if [ ! -f "$WORK/gestalt-fremd" ]; then
        echo "=== 6. Der Neubau: entfernen, anlegen, Zertifikate, starten ==="
        # Die Argumente ueber set --, weil sh keine Felder kennt und jedes
        # Argument mit Leerzeichen sonst zerfiele. Kein --network host: das Netz
        # ist das des alten Containers.
        set -- --name "$CONTAINER" --network "$netz" --env-file "$ENVDATEI"
        if [ -n "${restart:-}" ] && [ "$restart" != no ]; then
            set -- "$@" --restart "$restart"
        fi
        while IFS= read -r mount; do
            if [ -n "$mount" ]; then
                set -- "$@" --mount "$mount"
            fi
        done <"$WORK/mounts.list"
        while IFS= read -r label; do
            if [ -n "$label" ]; then
                set -- "$@" --label "$label"
            fi
        done <"$WORK/labels.list"
        while IFS= read -r alias; do
            if [ -n "$alias" ]; then
                set -- "$@" --network-alias "$alias"
            fi
        done <"$WORK/aliase.list"
        sudo docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
        if sudo docker create "$@" "$abbild" >/dev/null 2>"$WORK/create.err"; then
            if [ -f "$WORK/zertifikate.tar" ]; then
                sudo docker cp - "$CONTAINER:/certs" <"$WORK/zertifikate.tar" || : >"$WORK/gestalt-fremd"
            fi
            if [ ! -f "$WORK/gestalt-fremd" ] && sudo docker start "$CONTAINER" >/dev/null 2>"$WORK/start.err"; then
                echo "neubau-gelungen ja"
            else
                echo "neubau-gelungen nein, der Start ist gescheitert"
                cat "$WORK/start.err" 2>/dev/null || true
                : >"$WORK/gestalt-fremd"
            fi
        else
            echo "neubau-gelungen nein, docker create ist gescheitert"
            cat "$WORK/create.err"
            : >"$WORK/gestalt-fremd"
        fi
    fi

    if [ ! -f "$WORK/gestalt-fremd" ]; then
        echo "=== 7. Die harte Grenze, neu gesetzt, weil ein Neubau sie wegwirft ==="
        if ! sudo docker update --memory=2g --memory-swap=2g "$CONTAINER" >/dev/null; then
            echo "docker update ist gescheitert, die cgroup entscheidet trotzdem"
        fi
        echo "-- zurueckgelesen aus der cgroup und nicht aus dem Klienten --"
        gemessene_grenze=$(cgroup_wert memory.max)
        gemessener_swap=$(cgroup_wert memory.swap.max)
        printf 'speichergrenze-ist %s/%s\n' "$gemessene_grenze" "$gemessener_swap"
        printf 'grenze-erwartet %s/%s\n' "$ERWARTETE_GRENZE" "$ERWARTETER_SWAP"
        if [ "$gemessene_grenze" = "$ERWARTETE_GRENZE" ] && [ "$gemessener_swap" = "$ERWARTETER_SWAP" ]; then
            echo "grenze-gesetzt ja"
        else
            echo "grenze-gesetzt nein"
            : >"$WORK/grenze-fehlt"
        fi

        echo "=== 8. Der Schalter und der Entladeschalter, aus dem neuen Container ==="
        if feld '{{range .Config.Env}}{{println .}}{{end}}' >"$WORK/umgebung-ist.list"; then
            chmod 600 "$WORK/umgebung-ist.list"
            ist=$(wert_von "$SCHALTER" "$WORK/umgebung-ist.list")
            printf 'schalter-ist %s %s\n' "$SCHALTER" "${ist:-nicht-gesetzt}"
            if [ "${ist:-}" != "$WERT" ]; then
                : >"$WORK/gestalt-fremd"
            fi
            stellung=$(wert_von "$ENTLADESCHALTER" "$WORK/umgebung-ist.list")
            if [ -z "${stellung:-}" ]; then
                printf 'entladeschalter-ist %s werksstand\n' 0
            else
                printf 'entladeschalter-ist %s\n' "$stellung"
            fi
        else
            echo "schalter-ist unlesbar"
            echo "entladeschalter-ist unlesbar"
            : >"$WORK/gestalt-fremd"
        fi
    fi

    date -u +'neubau-fertig %Y-%m-%dT%H:%M:%SZ'
    # Die letzte Zeile des Blocks. Bricht ein Befehl darueber unter set -eu ab,
    # verlaesst er nur die Subshell, und ohne diese Marke endete das Werkzeug
    # unten mit 0, ohne dass jemand gesehen haette, dass der Neubau halb stand.
    : >"$WORK/block-durchgelaufen"
} 2>&1 | tee "$ZIEL"

# Alles Folgende steht UNTERHALB der Pipeline, aus dem Grund, den 92c nennt:
# der Rueckgabewert einer Pipeline, die in tee endet, gehoert zu tee.
if [ -f "$WORK/gestalt-fremd" ] || [ ! -f "$WORK/block-durchgelaufen" ]; then
    echo "92e-umgebung: der Container $CONTAINER ist nicht in der Gestalt, die dieses Werkzeug" >&2
    echo "92e-umgebung: nachbauen kann, oder der Neubau ist gescheitert; die Rohdatei $ZIEL" >&2
    echo "92e-umgebung: nennt den Schritt. Fehlt der Container jetzt, stellt 92d ihn her" >&2
    exit 43
fi
if [ -f "$WORK/grenze-fehlt" ]; then
    echo "92e-umgebung: die cgroup meldet nicht $ERWARTETE_GRENZE/$ERWARTETER_SWAP in memory.max/memory.swap.max" >&2
    echo "92e-umgebung: ein Lauf gegen einen Container ohne die harte Grenze misst eine andere Maschine" >&2
    exit 42
fi

echo "92E-UMGEBUNG-FERTIG"
