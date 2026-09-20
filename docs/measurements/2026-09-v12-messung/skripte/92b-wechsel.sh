#!/bin/sh
# Der Abbildwechsel auf den v1.2-Stand, Block 13b des Runbooks.
#
# Dies ist die NACHFOLGEFASSUNG von
# docs/measurements/2026-09-vergleichsmessung-m7g/skripte/92-wechsel.sh. Die
# Vorgaengerin ist gefahren worden, ihre Rohdaten liegen neben ihr, und damit
# ist sie Teil des Belegs: sie wird nicht editiert und nicht kopiert. Vier
# Unterschiede stehen unten, jeder mit seiner Begruendung.
#
# **Warum dieser Block ueberhaupt existiert.** Der Snapshot der Box traegt die
# lokale Registry mit dem Abbild vom 10.09.2026. Ein Volllauf gegen dieses
# Abbild misst einen Container ohne Top-up-Route, ohne die Filter aus Phase 13
# und ohne den Entladeschalter aus Phase 14. Erfolgskriterium 2 waere damit
# unerfuellbar, weil das alte Abbild genau den Fix nicht kennt, dessen Wirkung
# belegt werden soll, und Erfolgskriterium 5 ebenso, weil es den
# MEM-01-Schalter misst, den nur der neue Stand traegt.
#
# **Die Aufloesung des Widerspruchs, und sie gehoert in diesen Kopf.** Das
# Runbook fuehrt baumhash-gleich nein als Haltebedingung des Laufs und
# verlangt zugleich einen Abbildwechsel. Beides gilt, weil der Wechsel EINMAL
# stattfindet, VOR der ersten Messung, und weil er genau der Vorgang ist, der
# baumhash-gleich ja herstellt. Danach ist der Baumhash wieder das, was er
# vorher war: die Abbruchbedingung. Ein Abbildwechsel WAEHREND der Messreihe
# ist kein Nachtrag, sondern ein zweiter Messgegenstand, und Zahlen aus zwei
# Messgegenstaenden gehoeren nicht in eine Spalte.
#
# Die vier Unterschiede gegen die Vorgaengerin:
#
# 1. **Das Abbild kommt per Digest** und nicht ueber den Zeiger :dev
#    (Vorentscheid D-04, 15-CONTEXT.md). :dev wandert: jeder gruene Lauf der
#    Abbildstrecke schiebt ihn weiter, und der Pfadfilter von docker.yml reicht
#    bis in backend/**, also verschiebt schon eine neue Testdatei den Zeiger,
#    ohne eine Zeile des Abbilds zu aendern. Ein Bericht, der :dev nennt, nennt
#    keinen Stand. ABBILD_DIGEST hat deshalb KEINEN Vorgabewert: fehlt sie oder
#    ist sie leer, endet dieses Werkzeug mit exit 2 und der Benutzung auf
#    stderr, bevor eine Rohdatei entsteht. Nach dem Pull wird der Digest aus dem
#    Abbild zurueckgelesen und als Zeile abbild-digest-ist protokolliert. Der
#    Digest ist die Notiz, der Baumhash ist der Beweis (Befund L-05 der Phase
#    11, und Abschnitt 6 des Runbooks sagt es woertlich). IMAGE ist hier
#    folgerichtig keine Stellschraube mehr, sondern folgt aus ABBILD_REPO und
#    ABBILD_DIGEST; die Vorgaengerin hatte beides getrennt und konnte so einen
#    Baumhash gegen ein anderes Abbild fuehren als die Registrierung darunter.
#
# 2. **Der Baumhash entscheidet.** 40b-baumhash.sh wird als Skript gerufen und
#    nicht als Heredoc nachgebaut; seine Rohdatei wird zurueckgelesen, und dort
#    muessen drei verankerte baumhash:-Zeilen und baumhash-gleich ja stehen.
#    Alles andere endet mit **36**. Nachgebaut saehe die Rechnung anders aus als
#    die, die den Vergleichswert erzeugt hat, und ein Beweis, der seine eigene
#    Rechnung mitbringt, beweist nur sich selbst. Beide Vorgaengerberichte haben
#    die Gleichheit behauptet und diesen Schritt LEER gelassen; der eigentliche
#    Fehler war nicht das fehlende -i, sondern dass niemand danach in die Datei
#    gesehen hat.
#
# 3. **Die Abhaengigkeitskette ist erzwungen und nicht beschrieben.** Erst die
#    PHP-Haelfte in ein Verzeichnis, das findling heissen MUSS: unter jedem
#    anderen Namen findet der Klassenlader nichts, der Suchanbieter bleibt
#    unsichtbar, und es gibt NIRGENDS eine Fehlermeldung, die das sagt. Dann die
#    Registrierung, die den Container neu baut. Dann die harte Grenze, weil die
#    Registrierung sie wegwirft; gelesen wird sie AUS DER CGROUP und nicht aus
#    der Antwort von docker update oder aus docker inspect, mit 2147483648 in
#    memory.max und 0 in memory.swap.max (docker-Semantik: --memory-swap ist
#    die Summe, der Swap-Anteil dieser Maschine ist 0, wie auf der v1.1-Box,
#    siehe 90-bestand.txt). Greift sie nicht: **39**. Ein Lauf, der
#    gegen 4 GB misst, waehrend 2 GiB gemeint sind, misst eine andere Maschine
#    als v1.1. Unmittelbar daneben wird die Stellung von
#    FINDLING_EMBED_IDLE_RELEASE_SECONDS neu abgelesen und als
#    entladeschalter-ist protokolliert, weil sie bei jeder Registrierung genauso
#    verloren geht wie die Grenze und weil Abschnitt 6.4 des Runbooks die Zeile
#    verlangt.
#
# 4. **unregister --rm-data laeuft vor dem Indexaufbau und nie danach**, und nie
#    ohne die Zaehlung der laufenden Nextcloud-Instanzen unmittelbar davor.
#    Liefert die Zaehlung nicht genau 1: **37**, und es wird nichts weiter
#    getan. Am 07.09.2026 hat eine zweite Nextcloud am selben Docker-Dienst mit
#    diesem Schalter das Messvolumen der ERSTEN geloescht, weil der Volumenname
#    einer ExApp allein aus ihrer App-Kennung folgt. Die Zaehlung steht deshalb
#    zweimal in dieser Datei: einmal in Phase A als Verweigerung vor der ersten
#    veraendernden Zeile, und einmal in Phase B unmittelbar ueber dem Schalter
#    selbst. Die zweite ist nicht die Wiederholung der ersten: zwischen beiden
#    liegen ein Pull und ein Baumhashlauf, und in dieser Zeit kann eine zweite
#    Instanz gestartet worden sein.
#
# Unveraendert aus der Vorgaengerin uebernommen: die Kopie der info.xml entsteht
# AUSSERHALB des Arbeitsbaums, und danach muss
# git status --porcelain backend/appinfo/info.xml leer sein, sonst **38**. Ein
# Baumhash gegen einen veraenderten Arbeitsbaum belegt nichts. Die Kopie bleibt
# als Rohdatei $OUT/92b-info-box.xml liegen, damit der Bericht zeigen kann,
# womit registriert wurde (T-10-18).
#
# **Der Rueckgabewert 36 traegt zwei Faelle**, wie 32 und 33 es seit 15-04 tun
# und 34 und 35 seit 15-05. Der erste ist der Baumhash aus Unterschied 2. Der
# zweite steht am Ende von Phase B: die Registrierung laeuft ueber die info.xml,
# und die traegt einen Tag und keinen Digest, weil AppAPI registry/image:tag
# zusammensetzt. Ein Tag ist wieder ein wandernder Zeiger, also wird nach der
# Registrierung die Kennung des Abbilds AUS DEM CONTAINER gelesen und gegen die
# Kennung des per Digest gezogenen Abbilds gehalten. Weichen sie ab, laeuft die
# Messung gegen einen anderen Stand als den geprueften, und das ist derselbe
# unbelegte Stand wie ein fehlender Baumhash. Damit dieser Fall die Ausnahme
# bleibt und nicht die Regel, wird das gezogene Abbild vor der Registrierung
# lokal auf den Tag der info.xml gelegt.
#
# Die Rueckgabewerte, im Katalog dieses Laufverzeichnisses:
#
#   2  ABBILD_DIGEST fehlt, ist leer oder hat nicht die Gestalt eines Digests,
#      oder das Werkzeug wurde mit einem Argument gerufen, das es nicht gibt
#   36 der Baumhash fehlt, ist nicht dreifach verankert oder meldet
#      baumhash-gleich nein; ODER der Container laeuft nach der Registrierung
#      auf einer anderen Abbildkennung als der geprueften
#   37 mehr als eine Nextcloud laeuft an diesem Docker-Dienst, oder die Zaehlung
#      war nicht lesbar
#   38 der Arbeitsbaum ist nicht sauber
#   39 die harte Grenze hat die Registrierung nicht ueberlebt
#
# **Die Zeilen, die dieses Werkzeug schreibt**, ausgeschrieben statt aus dem
# Ablauf unten zusammengedacht. Ein Bericht greift nach Namen:
#
#   nextcloud-instanzen, nextcloud-instanzen-vor-rm-data
#   arbeitsbaum-unberuehrt
#   abbild-digest-gefordert, abbild-digest-ist, abbild-digest-gleich,
#   abbild-id-ist
#   baumhash-zeilen, baumhash-gleich, baumhash-beweis
#   php-verzeichnis-ist, php-app-ist
#   speichergrenze-ist, grenze-erwartet, grenze-gesetzt
#   entladeschalter-ist
#   abbild-im-container-ist, baumhash-im-laufenden-container,
#   abbild-im-container-gleich, containerstart-ist
set -eu

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: ABBILD_DIGEST="sha256:<64 Hexziffern>" ./92b-wechsel.sh

Ohne Argument. Die eine Pflichtangabe ist die Umgebungsvariable ABBILD_DIGEST,
der Digest des Release-Abbilds des Phase-14-Abschlusses. Sie hat bewusst keinen
Vorgabewert: der Zeiger :dev wandert mit jedem gruenen Lauf der Abbildstrecke,
und der Pfadfilter von docker.yml reicht bis in backend/**, also verschiebt
schon eine neue Testdatei den Zeiger, ohne eine Zeile des Abbilds zu aendern.
Ein Vorgabewert waere hier eine Vorgabe fuer den Messgegenstand.

Der Digest wird vor der Anfahrt aus der Abbildstrecke abgelesen. Die uebrigen
Stellschrauben stehen als Umgebungsvariablen im Kopf der Datei, darunter
ABBILD_REPO, IMAGE_TAG, CONTAINER, NEXTCLOUD, DAEMON, ERWARTETE_GRENZE und
ERWARTETER_SWAP (Vorgabe 0, der Swap-Anteil der cgroup, nicht die Grenze).
HINWEIS
}

if [ "$#" -ne 0 ]; then
    benutzung
    exit 2
fi

# Die Pflichtangabe, geprueft BEVOR ein Verzeichnis angelegt oder eine Rohdatei
# geschrieben wird. Ein Lauf, der vor seiner ersten Messung endet, hat nichts
# aufzuschreiben. Die Gestalt wird mitgeprueft, weil ein halber Digest sonst
# erst im Pull auffiele, also hinter der ersten Zeile der Rohdatei.
case "${ABBILD_DIGEST:-}" in
'')
    echo "92b-wechsel: ABBILD_DIGEST ist nicht gesetzt oder leer" >&2
    benutzung
    exit 2
    ;;
sha256:*) ;;
*)
    echo "92b-wechsel: ABBILD_DIGEST traegt nicht die Gestalt sha256:<hex>" >&2
    benutzung
    exit 2
    ;;
esac

# Alles, worin sich zwei Maschinen unterscheiden koennen, ist eine Variable mit
# Vorgabe, damit diese Datei keinen Pfad einer Maschine traegt. Die erste
# Vorgabe leitet sich aus dem Ort des Skripts selbst ab, was auf der Box und in
# einer Arbeitskopie gleichermassen haelt.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"

# Das Abbild, und es wird hier zusammengesetzt statt uebergeben. Ein eigenes
# IMAGE neben einem eigenen Digest waere genau der Fall, in dem der Baumhash ein
# anderes Abbild prueft als die Registrierung darunter faehrt.
ABBILD_REPO="${ABBILD_REPO:-ghcr.io/street1983nk/findling_backend}"
IMAGE="$ABBILD_REPO@$ABBILD_DIGEST"

CONTAINER="${CONTAINER:-nc_app_findling_backend}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
DAEMON="${DAEMON:-harp_aio}"
APP_ID="${APP_ID:-findling_backend}"
# Das Verzeichnis der PHP-Haelfte unter custom_apps. Es MUSS findling heissen,
# und die Zeile weiter unten prueft das, statt es nur zu behaupten.
PHP_APP="${PHP_APP:-findling}"
PFLICHTNAME_PHP=findling

# Das Abbild, das die Nextcloud selbst traegt, fuer die Zaehlung aus Unterschied
# 4. Woertlich die Vorgabe der Vorgaengerin, und sie bleibt woertlich: sie ist am
# 09.09.2026 an der Box korrigiert worden, nachdem die Schreibweise des Docker
# Hub auf dieser Box 0 Server bei genau einem laufenden gezaehlt hatte. Die
# zweite Alternative haelt die von Hand gebaute Gestalt nextcloud:<tag> in der
# Zaehlung, und das ist die Gestalt, die die zweite Instanz vom 07.09. hatte.
SERVER_IMAGES="${SERVER_IMAGES:-(^|/)aio-nextcloud:|(^|/)nextcloud:}"

# Die Fassung, die dieser Arbeitsbaum traegt, und der Tag, auf den die Kopie der
# info.xml gestellt wird. Der Tag ist der Zeiger, den AppAPI zieht; das gezogene
# Abbild wird vor der Registrierung lokal auf ihn gelegt.
VERSION="${VERSION:-1.1.0}"
IMAGE_TAG="${IMAGE_TAG:-dev}"
# Die harte Grenze in Byte, so wie die cgroup sie meldet.
ERWARTETE_GRENZE="${ERWARTETE_GRENZE:-2147483648}"
# Der erwartete Swap-Anteil AUS DER CGROUP, und er ist 0 und nicht die Grenze.
# docker update --memory=2g --memory-swap=2g bedeutet Summe = 2 GiB, also
# Swap-Anteil 0, und genau so stand es auf der v1.1-Box:
# docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/90-bestand.txt
# traegt memory.swap.max=0 neben memory.max=2147483648. Die urspruengliche
# Fassung dieses Werkzeugs erwartete die Grenze in BEIDEN Feldern und haette
# jede korrekte Maschine mit 39 abgewiesen; Befund der Anfahrt vom 20.09.2026,
# Fix mit Owner-Wort in der begleiteten Sitzung.
ERWARTETER_SWAP="${ERWARTETER_SWAP:-0}"
# Der Name des Entladeschalters aus Phase 14. Er reist als Umgebungsvariable der
# ExApp und wird nach der Registrierung neu abgelesen.
ENTLADESCHALTER="${ENTLADESCHALTER:-FINDLING_EMBED_IDLE_RELEASE_SECONDS}"

mkdir -p "$OUT"
ZIEL="${ZIEL:-$OUT/92b-wechsel.txt}"
BAUMHASH="$OUT/40b-baumhash.txt"
INFO_KOPIE="$OUT/92b-info-box.xml"
WORK=$(mktemp -d)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT

occ() {
    sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
}

# Die Zaehlung der laufenden Nextcloud-Instanzen. Eine Zaehlung, die nicht
# gelesen werden kann, liefert das Wort unlesbar und nicht die Zahl 0: 0 sieht
# aus wie eine Antwort und ist keine, und ungleich 1 ist beides.
nextclouds_zaehlen() {
    anzahl=$(sudo docker ps --format '{{.Image}}' 2>/dev/null | grep -Ec "$SERVER_IMAGES" || true)
    case "${anzahl:-}" in
    '' | *[!0-9]*) printf 'unlesbar\n' ;;
    *) printf '%s\n' "$anzahl" ;;
    esac
}

# Die cgroup des Containers, nach dem Muster von 93-nullstand.sh und
# 99c-filter-sortierung.sh. Die Kennung wird jedes Mal neu gelesen, damit kein
# stehengebliebener Pfad die cgroup von gestern liest.
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

# Phase A, und nichts darin veraendert etwas. Jedes Urteil dieser Phase geht in
# eine eigene Arbeitsdatei, weil der Rueckgabewert einer Pipeline, die in tee
# endet, zu tee gehoert, und weil der Abbruch vor dem ersten veraendernden
# Befehl der Phase B fallen muss und nicht danach.
{
    date -u +'wechsel-vorlauf %Y-%m-%dT%H:%M:%SZ'
    echo "abbild: $IMAGE"
    echo "repo: $REPO"
    printf 'abbild-digest-gefordert %s\n' "$ABBILD_DIGEST"

    echo "=== 1. Wie viele Nextcloud-Instanzen laufen an diesem Docker-Dienst ==="
    echo "-- jeder laufende Container, damit die Zahl darunter nachpruefbar ist --"
    sudo docker ps --format '{{.Names}}  {{.Image}}  {{.Status}}' || true
    nextclouds_zaehlen >"$WORK/instanzen"
    printf 'nextcloud-instanzen %s\n' "$(cat "$WORK/instanzen")"
    if [ "$(cat "$WORK/instanzen")" != 1 ]; then
        : >"$WORK/zweite-instanz"
        echo "-- Ungleich eins. Phase B faellt aus, und zwar ganz: --rm-data traefe das"
        echo "   Volumen jeder laufenden Instanz (07.09.2026). --"
    fi

    echo "=== 2. Der Arbeitsbaum und die Kopie der info.xml, vor dem Pull ==="
    printf 'die Fassung dieses Baums: '
    grep -m1 -o "<version>[^<]*</version>" "$REPO/backend/appinfo/info.xml"
    printf 'der image-tag dieses Baums: '
    grep -m1 -o "<image-tag>[^<]*</image-tag>" "$REPO/backend/appinfo/info.xml"
    if ! grep -q "<image-tag>$VERSION</image-tag>" "$REPO/backend/appinfo/info.xml"; then
        echo "Hinweis: der image-tag ist nicht $VERSION; das sed unten stellt, was dort steht, auf $IMAGE_TAG"
    fi
    # Die Kopie entsteht unter WORK und damit AUSSERHALB des Arbeitsbaums. Ein
    # sed in den Baum hinein waere die eine Zeile, die den Baumhash daneben
    # wertlos machte.
    sed "s|<image-tag>[^<]*</image-tag>|<image-tag>$IMAGE_TAG</image-tag>|" \
        "$REPO/backend/appinfo/info.xml" >"$WORK/92b-info-box.xml"
    grep -E '<registry>|<image>|<image-tag>' "$WORK/92b-info-box.xml"
    cp "$WORK/92b-info-box.xml" "$INFO_KOPIE"
    echo "die Kopie bleibt als $INFO_KOPIE liegen, damit der Bericht zeigen kann, womit registriert wurde"
    echo "-- und der Arbeitsbaum muss von alldem unberuehrt sein (T-10-18) --"
    (cd "$REPO" && git status --porcelain backend/appinfo/info.xml) >"$WORK/status.txt" 2>&1 || true
    if [ -s "$WORK/status.txt" ]; then
        echo "arbeitsbaum-unberuehrt nein"
        cat "$WORK/status.txt"
    else
        echo "arbeitsbaum-unberuehrt ja"
    fi

    echo "=== 3. Das Abbild, per Digest gezogen und nicht ueber :dev ==="
    # Gezogen und nicht auf der Box gebaut: ein Bau kostet rund vierzig Minuten
    # eines gedeckelten Laufs und erzeugt denselben Code unter einem anderen
    # Schichtenhash. Was der Bericht braucht, ist der Beweis der Gleichheit, und
    # der ist der Baumhash.
    sudo docker pull "$IMAGE"
    sudo docker image inspect "$IMAGE" \
        --format 'Id={{.Id}} Arch={{.Architecture}} Created={{.Created}} Digest={{index .RepoDigests 0}}'
    sudo docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}}' |
        sed 's/.*@//' >"$WORK/digest"
    sudo docker image inspect "$IMAGE" --format '{{.Id}}' >"$WORK/abbild-id"
    printf 'abbild-digest-ist %s\n' "$(cat "$WORK/digest")"
    printf 'abbild-id-ist %s\n' "$(cat "$WORK/abbild-id")"
    if [ "$(cat "$WORK/digest")" = "$ABBILD_DIGEST" ]; then
        echo "abbild-digest-gleich ja"
    else
        echo "abbild-digest-gleich nein"
        echo "BEFUND: das gezogene Abbild meldet einen anderen Digest zurueck als den"
        echo "  geforderten. Das ist ein Befund fuer den Bericht und keine Abbruchzeile:"
        echo "  entschieden wird unten am Baumhash, weil der Digest die Notiz ist und der"
        echo "  Baumhash der Beweis (Befund L-05 der Phase 11)."
    fi

    echo "=== 4. Der Baumhash, als eigener Schritt mit eigener Rohdatei ==="
    # Gerufen und nicht nachgebaut. Uebergeben und nicht dem Zufall gleicher
    # Vorgaben ueberlassen: beide Dateien tragen dieselben Vorgabewerte, also
    # haette eine nicht exportierte Ueberschreibung hier den Baumhash gegen ein
    # Abbild gefuehrt und die Registrierung unten gegen ein anderes. Das ist der
    # Fehlschlag T-10-13 mit einem gruenen Schritt davor.
    export IMAGE OUT REPO
    baumhash_status=0
    sh "$SKRIPTE/40b-baumhash.sh" || baumhash_status=$?
    printf '40b-baumhash-rueckgabewert %s\n' "$baumhash_status"
    if [ -s "$BAUMHASH" ]; then
        gezaehlt=$(grep -c '^baumhash: ' "$BAUMHASH" || true)
        printf 'baumhash-zeilen %s (drei werden erwartet)\n' "$gezaehlt"
        sed -n 's/^\(baumhash-gleich .*\)$/\1/p' "$BAUMHASH"
        if [ "$gezaehlt" -eq 3 ] && grep -q '^baumhash-gleich ja$' "$BAUMHASH"; then
            echo "baumhash-beweis ja"
        else
            echo "baumhash-beweis nein"
            : >"$WORK/baumhash-fehlt"
        fi
    else
        echo "die Rohdatei $BAUMHASH fehlt oder ist leer"
        echo "baumhash-beweis nein"
        : >"$WORK/baumhash-fehlt"
    fi

    echo "=== 5. Was das Abbild fuer die semantische Haelfte und fuer die OCR mitbringt ==="
    sudo docker run --rm --network none --entrypoint /bin/sh "$IMAGE" -c '
      echo "-- das Modellverzeichnis --"
      ls -la /usr/local/share/findling/model
      echo "-- sha256 der int8-Datei, also des Abbildinhalts und nicht des Arbeitsbaums --"
      find /usr/local/share/findling/model -name "*.onnx" -exec sha256sum {} \;
      echo "-- die wirklich installierten Tesseract-Sprachen --"
      tesseract --list-langs 2>&1
      echo "-- die Vorgabewerte der Umgebung --"
      env | grep -i "FINDLING\|HF_HUB" | sort
    '

    date -u +'wechsel-vorlauf-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$WORK/vorlauf.txt"

# Die drei Verweigerungen der Phase A, jede von ihnen vor dem ersten Befehl, der
# etwas veraendert. Die Reihenfolge ist die Reihenfolge des Ablaufs, damit der
# erste Befund auch der erste ist, der gefallen ist.
if [ -f "$WORK/zweite-instanz" ]; then
    echo "92b-wechsel: die Zaehlung meldet $(cat "$WORK/instanzen") statt genau einer Nextcloud" >&2
    echo "92b-wechsel: --rm-data traefe das Volumen jeder laufenden Instanz, weil der" >&2
    echo "92b-wechsel: Volumenname einer ExApp allein aus ihrer App-Kennung folgt (07.09.2026)" >&2
    exit 37
fi
if [ -s "$WORK/status.txt" ]; then
    echo "92b-wechsel: backend/appinfo/info.xml ist im Arbeitsbaum nicht sauber" >&2
    echo "92b-wechsel: ein Baumhash gegen einen veraenderten Arbeitsbaum belegt nichts," >&2
    echo "92b-wechsel: und der gemessene Stand waere nicht der Stand des Repositoriums" >&2
    exit 38
fi
if [ -f "$WORK/baumhash-fehlt" ]; then
    echo "92b-wechsel: der Baumhashbeweis hat nicht drei Hashes und ein ja hergegeben" >&2
    echo "92b-wechsel: Erfolgskriterium 1 waere nicht belegbar, und jede Zahl unterhalb" >&2
    echo "92b-wechsel: dieser Zeile gehoerte zu einem Zustand, den niemand benennen kann" >&2
    exit 36
fi

# Phase B, und ab hier wird die Box veraendert.
{
    # Die ganze Phase A geht in die Rohdatei, damit eine Datei den Schritt traegt.
    cat "$WORK/vorlauf.txt"

    date -u +'wechsel-start %Y-%m-%dT%H:%M:%SZ'

    echo "=== 6. Der Datenspeicher vor dem Wechsel ==="
    sudo docker volume ls --filter name=findling_backend --format '{{.Name}}' || true

    echo "=== 7. Die Zaehlung noch einmal, unmittelbar ueber dem Schalter ==="
    # Zwischen dieser Zaehlung und der aus Phase A liegen ein Pull und ein
    # Baumhashlauf. In dieser Zeit kann eine zweite Instanz gestartet worden
    # sein, und die erste Zaehlung sagte dann nichts mehr ueber diesen Moment.
    nextclouds_zaehlen >"$WORK/instanzen-b"
    printf 'nextcloud-instanzen-vor-rm-data %s\n' "$(cat "$WORK/instanzen-b")"
    if [ "$(cat "$WORK/instanzen-b")" = 1 ]; then
        echo "=== 8. unregister MIT --rm-data, mit Absicht, und vor dem Indexaufbau ==="
        # Ein leeres Volumen ist, was dieser Lauf will: beide Haelften sollen bei
        # null anfangen, und eine liegengebliebene state.db liesse den Container
        # Dateien an ihrer file_id wiedererkennen und ueberspringen. Nach dem
        # Indexaufbau waere derselbe Schalter der Verlust des Messgegenstands.
        occ app_api:app:unregister "$APP_ID" --rm-data 2>&1 ||
            occ app_api:app:unregister "$APP_ID" --rm-data --force 2>&1 || true
        echo "-- der Datenspeicher danach, es darf keiner uebrig sein --"
        sudo docker volume ls --filter name=findling_backend --format '{{.Name}}' || true
        sudo docker ps -a --filter name=findling_backend --format '{{.Names}} {{.Status}}' || true
    else
        : >"$WORK/zweite-instanz-b"
        echo "-- Die Zaehlung meldet nicht genau eine Instanz. Der Schalter wird NICHT"
        echo "   gefahren, und dieser Lauf endet unterhalb der Pipeline. --"
    fi

    if [ ! -f "$WORK/zweite-instanz-b" ]; then
        echo "=== 9. Die PHP-Haelfte dieses Stands, in den Container der Nextcloud ==="
        # Das Verzeichnis MUSS findling heissen. Unter jedem anderen Namen findet
        # der Klassenlader nichts, der Suchanbieter bleibt unsichtbar, und es gibt
        # nirgends eine Fehlermeldung, die das sagt. Deshalb steht der Name hier
        # nicht nur als Vorgabe, sondern als Bedingung.
        if [ "$PHP_APP" != "$PFLICHTNAME_PHP" ]; then
            echo "PHP_APP ist $PHP_APP und nicht $PFLICHTNAME_PHP; der Name wird zurueckgestellt"
            PHP_APP="$PFLICHTNAME_PHP"
        fi
        printf 'php-verzeichnis-ist %s\n' "$PHP_APP"
        sudo docker exec "$NEXTCLOUD" rm -rf "/var/www/html/custom_apps/$PHP_APP"
        sudo docker cp "$REPO/php" "$NEXTCLOUD:/var/www/html/custom_apps/$PHP_APP"
        sudo docker exec "$NEXTCLOUD" chown -R 33:33 "/var/www/html/custom_apps/$PHP_APP"
        sudo docker exec "$NEXTCLOUD" sh -c 'ls -la /var/www/html/custom_apps/findling | head -5'
        occ app:enable "$PHP_APP" 2>&1 || true
        occ app:list 2>&1 | grep -i -A1 "$PHP_APP" | head -6 || true
        printf 'php-app-ist %s\n' "$PHP_APP"

        echo "=== 10. Die Registrierung ueber AppAPI, die zugleich die Scharfstellung ist ==="
        # AppAPI setzt registry/image:tag zusammen und kennt keinen Digest. Damit
        # der Zeiger auf das gepruefte Abbild zeigt, wird das gezogene Abbild
        # vorher lokal auf genau diesen Tag gelegt. Der Beweis bleibt trotzdem die
        # Kennung, die unten aus dem Container gelesen wird.
        sudo docker tag "$IMAGE" "$ABBILD_REPO:$IMAGE_TAG"
        sudo docker cp "$INFO_KOPIE" "$NEXTCLOUD:/tmp/92b-info-box.xml"
        sudo docker exec "$NEXTCLOUD" chown 33:33 /tmp/92b-info-box.xml
        date -u +'register-start %Y-%m-%dT%H:%M:%SZ'
        occ app_api:app:register "$APP_ID" "$DAEMON" \
            --info-xml /tmp/92b-info-box.xml --wait-finish 2>&1
        date -u +'register-ende %Y-%m-%dT%H:%M:%SZ'

        echo "=== 11. Die harte Grenze, neu gesetzt, weil eine Registrierung sie wegwirft ==="
        sudo docker update --memory=2g --memory-swap=2g "$CONTAINER" >/dev/null
        sudo docker inspect "$CONTAINER" \
            --format 'Image={{.Config.Image}} StartedAt={{.State.StartedAt}} Restart={{.HostConfig.RestartPolicy.Name}}' || true
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

        echo "=== 12. Die Stellung des Entladeschalters, unmittelbar daneben ==="
        # Sie geht bei jeder Registrierung genauso verloren wie die Grenze, und
        # Abschnitt 6.4 des Runbooks verlangt die Zeile und nicht die Stellung.
        if sudo docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$CONTAINER" \
            >"$WORK/umgebung" 2>/dev/null; then
            stellung=$(awk -F= -v name="$ENTLADESCHALTER" \
                '$1 == name {print $2; exit}' "$WORK/umgebung")
            if [ -z "${stellung:-}" ]; then
                printf 'entladeschalter-ist %s werksstand\n' 0
            else
                printf 'entladeschalter-ist %s\n' "$stellung"
            fi
        else
            echo "entladeschalter-ist unlesbar"
        fi

        echo "=== 13. memory.events, und anon neben memory.current wie ueberall in diesem Lauf ==="
        cgroup_wert memory.events
        cgroup_wert memory.stat | grep -E '^(anon|file|slab) ' || true
        printf 'memory.current=%s memory.peak=%s\n' \
            "$(cgroup_wert memory.current)" "$(cgroup_wert memory.peak)"

        echo "=== 14. Der Zustand der ExApp und das leere Volumen, von dem sie startet ==="
        occ app_api:app:list 2>&1 | head -30 || true
        sudo docker volume ls --filter name=findling_backend --format '{{.Name}}' || true
        sudo docker exec "$CONTAINER" sh -c 'ls -la /nc_app_findling_backend_data' 2>&1 || true

        echo "=== 15. Laeuft der Container auf der geprueften Abbildkennung? ==="
        # Der zweite Fall des Rueckgabewerts 36. Die info.xml traegt einen Tag, und
        # ein Tag ist wieder ein wandernder Zeiger; geprueft worden ist ein Digest.
        # Die Kennungen selbst sind seit Docker 29 mit containerd-Store kein
        # Vergleichspaar mehr: inspect eines repo@digest liefert den Index-Digest,
        # .Image des Containers den aufgeloesten Plattform- beziehungsweise
        # Config-Digest, und der Deploy des Daemons zieht den Tag frisch. Zwei
        # verschiedene Kennungsarten desselben Inhalts lasen sich am 20.09.2026
        # als fremdes Abbild (Befund der Anfahrt, Fix mit Owner-Wort). Verglichen
        # wird deshalb der Beweis selbst und nicht die Notiz: der Baumhash des
        # Pakets IM LAUFENDEN Container gegen den abbild-baumhash aus 40b. Das
        # ist woertlich die Rangordnung aus dem Kopf dieser Datei.
        im_container=$(sudo docker inspect --format '{{.Image}}' "$CONTAINER" 2>/dev/null || true)
        [ -n "${im_container:-}" ] || im_container=unlesbar
        printf 'abbild-im-container-ist %s\n' "$im_container"
        abbild_hash=$(sed -n 's/^abbild-baumhash: //p' "$BAUMHASH" | head -n 1)
        sudo docker cp "$SKRIPTE/40b-baumhash.py" "$CONTAINER:/tmp/40b-baumhash.py" 2>/dev/null || true
        lauf_hash=$(sudo docker exec "$CONTAINER" /app/.venv/bin/python /tmp/40b-baumhash.py \
            /app/.venv/lib/python3.13/site-packages/findling '**/*.py' 2>/dev/null \
            | sed -n 's/^baumhash: //p' | head -n 1)
        [ -n "${lauf_hash:-}" ] || lauf_hash=unlesbar
        printf 'baumhash-im-laufenden-container %s\n' "$lauf_hash"
        if [ -n "${abbild_hash:-}" ] && [ "$lauf_hash" = "$abbild_hash" ]; then
            echo "abbild-im-container-gleich ja"
        else
            echo "abbild-im-container-gleich nein"
            : >"$WORK/abbild-fremd"
        fi

        echo "=== 16. Das Protokoll dieses Starts ==="
        START=$(sudo docker inspect "$CONTAINER" --format '{{.State.StartedAt}}' 2>/dev/null || true)
        printf 'containerstart-ist %s\n' "${START:-unlesbar}"
        if [ -n "${START:-}" ]; then
            sudo docker logs --timestamps --since "$START" "$CONTAINER" 2>&1 | tail -30 || true
        fi
    fi

    date -u +'wechsel-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Alles Folgende steht UNTERHALB der Pipeline, und nur dort. Der Rueckgabewert
# einer Pipeline, die in tee endet, gehoert zu tee; ein Abbruch innerhalb des
# Blocks verliesse nur die Subshell, und die Verweigerung waere eine Zeile in
# einer Rohdatei, die niemand liest. Gelesen wird deshalb aus den Arbeitsdateien
# unter WORK, in der Reihenfolge des Ablaufs.
if [ -f "$WORK/zweite-instanz-b" ]; then
    echo "92b-wechsel: die Zaehlung unmittelbar vor --rm-data meldet $(cat "$WORK/instanzen-b")" >&2
    echo "92b-wechsel: statt genau einer Nextcloud. Der Schalter ist nicht gefahren worden," >&2
    echo "92b-wechsel: und bis zur Klaerung wird nichts weiter getan (07.09.2026)" >&2
    exit 37
fi
if [ -f "$WORK/grenze-fehlt" ]; then
    echo "92b-wechsel: die cgroup meldet nicht $ERWARTETE_GRENZE/$ERWARTETER_SWAP in memory.max/memory.swap.max" >&2
    echo "92b-wechsel: ein Lauf, der gegen 4 GB misst, waehrend 2 GiB gemeint sind," >&2
    echo "92b-wechsel: misst eine andere Maschine als v1.1 und keine Abweichung" >&2
    exit 39
fi
if [ -f "$WORK/abbild-fremd" ]; then
    echo "92b-wechsel: der Container laeuft auf einer anderen Abbildkennung als der" >&2
    echo "92b-wechsel: geprueften. Der Baumhash hat ein Abbild belegt, gemessen wuerde" >&2
    echo "92b-wechsel: ein anderes, und das ist derselbe unbelegte Stand wie ein" >&2
    echo "92b-wechsel: fehlender Baumhash" >&2
    exit 36
fi

echo "92B-WECHSEL-FERTIG"
