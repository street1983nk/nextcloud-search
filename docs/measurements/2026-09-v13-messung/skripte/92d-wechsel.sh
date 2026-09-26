#!/bin/sh
# Der Abbildwechsel auf den v1.3-Stand, OHNE das Volumen des Snapshots zu
# leeren.
#
# Dies ist die NACHFOLGEFASSUNG von
# docs/measurements/2026-09-nachfolgefassungen/skripte/92c-wechsel.sh, und ihr
# Anlass ist Befund 1 der Recherche zu Phase 22, der Reihenfolgezwang. 92c
# leert in Phase B mit unregister --rm-data das Datenvolumen des Backends, und
# auf diesem Volumen liegt der fertige Index des Snapshots mit 52.137
# indexierten, 44 uebersprungenen und 6 fehlgeschlagenen Dateien. Ist er weg,
# braucht die Messung des Umbaus (MESS-08) zuerst einen Vollreindex von rund 19
# Stunden, und das sprengt den Deckel der Anfahrt. Der erste Wechsel der
# Anfahrt ist deshalb diese Fassung; 92c bleibt das Werkzeug fuer einen Lauf,
# der ausdruecklich bei null anfangen soll. 92c selbst wird nicht editiert.
#
# **DIESE FASSUNG IST NICHT GEFAHREN.** Neben ihr liegt keine Rohdatei. Ihr
# Abnahmekriterium ist Form, statische Analyse und die Generalprobe gegen die
# lokale Test-Nextcloud. Was sie auf der Box wirklich bewirkt, misst erst die
# Anfahrt. Wer hier Zahlen sucht, findet keine, und das ist kein Versehen.
#
# **Die zwei Aenderungen gegen 92c.**
#
# 1. **unregister ohne --rm-data.** Das Volumen des Snapshots bleibt mit
#    52.137 / 44 / 6 stehen, und die Registrierung darunter haengt den neuen
#    Container an genau dieses Volumen, weil sein Name allein aus der
#    App-Kennung folgt. Die Zaehlung der laufenden Nextcloud-Instanzen bleibt
#    trotzdem Pflicht und steht weiter unmittelbar ueber dem unregister: ein
#    unregister ohne Schalter zerstoert kein Volumen, aber es trifft die
#    ExApp jeder Instanz an diesem Docker-Dienst. Neu ist das Bestandstor nach
#    der Registrierung: indexiert aus der state.db des laufenden Containers,
#    uebersprungen und fehlgeschlagen aus occ findling:index, und weicht eine
#    der drei Zahlen von 52137 / 44 / 6 ab, endet das Werkzeug mit **41**.
#    indexiert kommt nicht aus occ, weil die PHP-Haelfte diese Zahl nie
#    schreibt; occ findling:index sagt das in seiner eigenen Ausgabe
#    ("indexed is counted by the backend container and never written here").
#
# 2. **Schritt 1b, occ upgrade, mit gelesenem Rueckgabewert.** Lauf 1 der
#    v1.2-Anfahrt scheiterte daran, dass die Nextcloud nach dem Einspielen der
#    neuen PHP-Haelfte auf "requires upgrade" stand; im eingeschraenkten Modus
#    fehlt der Namensraum app_api:app, und die Registrierung lief nie (Runbook,
#    Nachtrag zu Block 13b). Die PHP-Haelfte kommt deshalb VOR das unregister,
#    unmittelbar danach laeuft occ upgrade, und erst dann unregister und
#    register. Der Rueckgabewert von occ upgrade wird nach dem Muster der
#    Registrierung aus 92c gelesen: der Aufruf schreibt in eine eigene Datei
#    unter WORK, sein Rueckgabewert wird unmittelbar danach geprueft und als
#    occ-upgrade-rueckgabewert protokolliert, und erst danach laeuft seine
#    Ausgabe in die Rohdatei. Ist er weder 0 noch 3 (3 ist ERROR_UP_TO_DATE,
#    nichts zu tun, und kein Fehlschlag), faellt der Rest der Phase B aus, und
#    unterhalb der Pipeline endet das Werkzeug mit **40**.
#
# **Was ausdruecklich gleich bleibt**, damit ein Bericht dieser Fassung neben
# einem Bericht von 92c gelesen werden kann:
#
#   - alle Rueckgabewerte mit ihrer Bedeutung, 2, 36, 37, 38 und 39, und keine
#     Zahl wird umgehaengt; 40 und 41 sind neu und kommen aus dem Katalog
#     dieses Laufverzeichnisses
#   - alle Fristen und alle Vorgabewerte, einschliesslich ERWARTETE_GRENZE,
#     ERWARTETER_SWAP, VERSION und IMAGE_TAG
#   - die Zusammensetzung des Abbilds aus ABBILD_REPO und ABBILD_DIGEST, samt
#     der Pflichtangabe sha256:<hex> ohne Vorgabewert
#   - WERKZEUGE zeigt weiter auf docs/measurements/2026-09-v12-messung/skripte,
#     und der Baumhash wird dort per 40b-baumhash.sh als Skript gerufen
#   - die Grenze wird aus der cgroup gelesen, und die Zeile entladeschalter-ist
#     steht unmittelbar daneben
#   - die Zaehlung der laufenden Nextcloud-Instanzen in Phase A und
#     unmittelbar ueber dem unregister in Phase B
#   - der Ort der Verweigerungen unterhalb der Pipeline und die Namen aller
#     Zeilen, die 92c schreibt, mit einer Ausnahme: die zweite Zaehlung heisst
#     nextcloud-instanzen-vor-unregister, weil es den Schalter, nach dem sie
#     in 92c hiess, hier nicht mehr gibt
#
# **Der eigene Name.** Das Werkzeug nennt sich 92d, schreibt 92d-wechsel.txt
# und 92d-info-box.xml und meldet 92D-WECHSEL-FERTIG. OUT zeigt ohne Vorgabe
# von aussen auf das rohdaten-Verzeichnis neben diesem, also in das
# Laufverzeichnis der v1.3-Anfahrt.
#
# **Die zwei Baumhash-Werkzeuge liegen nicht neben dieser Datei.** Sie sind
# gefahrene Fassungen und bleiben im Laufverzeichnis der v1.2-Anfahrt; die
# Variable WERKZEUGE unten zeigt dorthin.
#
# Der Kopf von 92c steht ab hier fast unveraendert darunter, weil er diese
# Fassung genauso beschreibt; wo er vom Schalter --rm-data spricht, gilt fuer
# diese Fassung Aenderung 1 oben. Die vier Unterschiede, die er nennt, gelten
# gegen docs/measurements/2026-09-vergleichsmessung-m7g/skripte/92-wechsel.sh.
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
# als Rohdatei $OUT/92d-info-box.xml liegen, damit der Bericht zeigen kann,
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
#      baumhash-gleich nein; ODER der occ-Aufruf der Registrierung ist
#      gescheitert (L-03); ODER der Container laeuft nach der Registrierung
#      auf einer anderen Abbildkennung als der geprueften
#   37 mehr als eine Nextcloud laeuft an diesem Docker-Dienst, oder die Zaehlung
#      war nicht lesbar
#   38 der Arbeitsbaum ist nicht sauber
#   39 die harte Grenze hat die Registrierung nicht ueberlebt
#   40 occ upgrade ist gescheitert (Schritt 1b), also weder 0 noch 3;
#      unregister und register sind dann nicht gefahren
#   41 das Bestandstor nach der Registrierung meldet nicht 52137 indexiert, 44
#      uebersprungen und 6 fehlgeschlagen, oder eine der drei Zahlen war nicht
#      lesbar
#
# **Die Zeilen, die dieses Werkzeug schreibt**, ausgeschrieben statt aus dem
# Ablauf unten zusammengedacht. Ein Bericht greift nach Namen:
#
#   nextcloud-instanzen, nextcloud-instanzen-vor-unregister
#   arbeitsbaum-unberuehrt
#   abbild-digest-gefordert, abbild-digest-ist, abbild-digest-gleich,
#   abbild-id-ist
#   baumhash-zeilen, baumhash-gleich, baumhash-beweis
#   php-verzeichnis-ist, php-app-ist
#   occ-upgrade-rueckgabewert, occ-upgrade-gelungen, occ-upgrade-stand
#   unregister-rueckgabewert, volumen-nach-unregister
#   registrierung-rueckgabewert, registrierung-gelungen
#   speichergrenze-ist, grenze-erwartet, grenze-gesetzt
#   entladeschalter-ist
#   abbild-im-container-ist, baumhash-im-laufenden-container,
#   abbild-im-container-gleich, containerstart-ist
#   bestandstor, bestandstor-erwartet, bestandstor-bestanden
set -eu

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: ABBILD_DIGEST="sha256:<64 Hexziffern>" ./92d-wechsel.sh

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
    echo "92d-wechsel: ABBILD_DIGEST ist nicht gesetzt oder leer" >&2
    benutzung
    exit 2
    ;;
sha256:*) ;;
*)
    echo "92d-wechsel: ABBILD_DIGEST traegt nicht die Gestalt sha256:<hex>" >&2
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
# Das Verzeichnis der beiden Baumhash-Werkzeuge. Sie liegen NICHT neben dieser
# Datei: sie sind gefahrene Fassungen und bleiben im Laufverzeichnis der
# Anfahrt. Eine eigene Variable mit Vorgabe, damit eine spaetere Anfahrt sie
# umhaengen kann, ohne in den Rumpf zu sehen.
WERKZEUGE="${WERKZEUGE:-$SKRIPTE/../../2026-09-v12-messung/skripte}"

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
# Das Bestandstor aus Aenderung 1, die drei Zahlen des Snapshots vom 11.09.2026.
# Bis zum 26.09.2026 standen hier 52111 / 37 / 0 (Runbook Abschnitt 5, der Stand
# vor dem Upload der 39 Sprachfall-Dateien am 10.09.); die Anfahrt hat am
# Bestandstor 52137 / 44 / 6 gelesen, und der Owner hat diesen Stand am
# 26.09.2026 als Sollwert bestaetigt (Checkpoint 22-08). Dieselben drei Zahlen
# stehen als BESTAND_SNAPSHOT in 00-lauf.sh; test_v13_wechsel.py prueft, dass
# beide Stellen gleich sind. Stellschrauben nur fuer die Generalprobe gegen eine
# lokale Test-Nextcloud; auf der Box gelten die Vorgaben.
BESTAND_INDEXIERT="${BESTAND_INDEXIERT:-52137}"
BESTAND_UEBERSPRUNGEN="${BESTAND_UEBERSPRUNGEN:-44}"
BESTAND_FEHLGESCHLAGEN="${BESTAND_FEHLGESCHLAGEN:-6}"

mkdir -p "$OUT"
ZIEL="${ZIEL:-$OUT/92d-wechsel.txt}"
BAUMHASH="$OUT/40b-baumhash.txt"
INFO_KOPIE="$OUT/92d-info-box.xml"
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

# Eine Zahl oder das Wort unlesbar, fuer das Bestandstor. Ein leeres Feld ist
# keine 0, und eine 0, die nie gelesen wurde, bestuende das Tor fuer
# fehlgeschlagen, ohne dass jemand nachgesehen haette.
zahl_oder_unlesbar() {
    case "${1:-}" in
    '' | *[!0-9]*) printf 'unlesbar\n' ;;
    *) printf '%s\n' "$1" ;;
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
        echo "-- Ungleich eins. Phase B faellt aus, und zwar ganz: ein unregister traefe"
        echo "   die ExApp jeder laufenden Instanz (07.09.2026). --"
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
        "$REPO/backend/appinfo/info.xml" >"$WORK/92d-info-box.xml"
    grep -E '<registry>|<image>|<image-tag>' "$WORK/92d-info-box.xml"
    cp "$WORK/92d-info-box.xml" "$INFO_KOPIE"
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
    sh "$WERKZEUGE/40b-baumhash.sh" || baumhash_status=$?
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
    echo "92d-wechsel: die Zaehlung meldet $(cat "$WORK/instanzen") statt genau einer Nextcloud" >&2
    echo "92d-wechsel: ein unregister traefe die ExApp jeder laufenden Instanz, weil ihr" >&2
    echo "92d-wechsel: Name und ihr Volumen allein aus der App-Kennung folgen (07.09.2026)" >&2
    exit 37
fi
if [ -s "$WORK/status.txt" ]; then
    echo "92d-wechsel: backend/appinfo/info.xml ist im Arbeitsbaum nicht sauber" >&2
    echo "92d-wechsel: ein Baumhash gegen einen veraenderten Arbeitsbaum belegt nichts," >&2
    echo "92d-wechsel: und der gemessene Stand waere nicht der Stand des Repositoriums" >&2
    exit 38
fi
if [ -f "$WORK/baumhash-fehlt" ]; then
    echo "92d-wechsel: der Baumhashbeweis hat nicht drei Hashes und ein ja hergegeben" >&2
    echo "92d-wechsel: Erfolgskriterium 1 waere nicht belegbar, und jede Zahl unterhalb" >&2
    echo "92d-wechsel: dieser Zeile gehoerte zu einem Zustand, den niemand benennen kann" >&2
    exit 36
fi

# Phase B, und ab hier wird die Box veraendert.
{
    # Die ganze Phase A geht in die Rohdatei, damit eine Datei den Schritt traegt.
    cat "$WORK/vorlauf.txt"

    date -u +'wechsel-start %Y-%m-%dT%H:%M:%SZ'

    echo "=== 6. Der Datenspeicher vor dem Wechsel, und er muss danach derselbe sein ==="
    sudo docker volume ls --filter name=findling_backend --format '{{.Name}}' || true

    echo "=== 7. Die PHP-Haelfte dieses Stands, in den Container der Nextcloud ==="
    # Vor dem unregister und nicht danach wie in 92c, weil occ upgrade darunter
    # die neue PHP-Haelfte braucht und das unregister darunter den Namensraum
    # app_api:app, den eine Nextcloud auf "requires upgrade" nicht anbietet.
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

    echo "=== 7b. occ upgrade, Schritt 1b des Runbooks, mit gelesenem Rueckgabewert ==="
    # Aenderung 2 dieser Fassung, nach dem Muster der Registrierung unten. Der
    # Aufruf verlaesst die Ausgabekette dieses Blocks: er schreibt in eine
    # eigene Datei unter WORK, sein Rueckgabewert wird unmittelbar danach
    # geprueft und in einer Arbeitsdatei vermerkt, und erst danach laeuft seine
    # Ausgabe in die Rohdatei. Ein gescheitertes upgrade laesst die Nextcloud
    # im eingeschraenkten Modus, und dort fehlt der Namensraum app_api:app.
    upgradelog=$(mktemp "$WORK/92d-upgrade.XXXXXX")
    upgrade_status=0
    occ upgrade >"$upgradelog" 2>&1 || upgrade_status=$?
    cat "$upgradelog"
    printf 'occ-upgrade-rueckgabewert %s\n' "$upgrade_status"
    # 0 und 3 sind beide ein gelungenes upgrade. 3 ist ERROR_UP_TO_DATE der
    # Nextcloud (core/Command/Upgrade.php): es gab nichts zu tun, etwa weil die
    # PHP-Haelfte schon auf diesem Stand war oder ein zweiter Lauf dieses
    # Werkzeugs folgt. deploy-harp.yml fuehrt dieselbe Regel ("Store upgrade 4").
    # Die erste Fassung verlangte 0 allein und haette eine Nextcloud, die 3
    # meldet, mit 40 abgewiesen, obwohl nichts gescheitert war; Befund beim Bau
    # der CI-Probe von 22-06 (probe-92d.yml) aus deploy-harp.yml gelesen. Die
    # Probe selbst sah auf Nextcloud 34 fuer "No upgrade required." eine 0.
    case "$upgrade_status" in
    0 | 3)
        echo "occ-upgrade-gelungen ja"
        if [ "$upgrade_status" -eq 3 ]; then
            echo "occ-upgrade-stand aktuell"
        fi
        ;;
    *)
        echo "occ-upgrade-gelungen nein"
        : >"$WORK/upgrade-fehlt"
        echo "-- Das upgrade ist gescheitert. unregister und register fallen aus, und"
        echo "   dieser Lauf endet unterhalb der Pipeline. --"
        ;;
    esac
    occ app:enable "$PHP_APP" 2>&1 || true
    occ app:list 2>&1 | grep -i -A1 "$PHP_APP" | head -6 || true
    printf 'php-app-ist %s\n' "$PHP_APP"

    if [ ! -f "$WORK/upgrade-fehlt" ]; then
        echo "=== 8. Die Zaehlung noch einmal, unmittelbar ueber dem unregister ==="
        # Zwischen dieser Zaehlung und der aus Phase A liegen ein Pull, ein
        # Baumhashlauf und ein upgrade. In dieser Zeit kann eine zweite Instanz
        # gestartet worden sein, und die erste Zaehlung sagte dann nichts mehr
        # ueber diesen Moment.
        nextclouds_zaehlen >"$WORK/instanzen-b"
        printf 'nextcloud-instanzen-vor-unregister %s\n' "$(cat "$WORK/instanzen-b")"
        if [ "$(cat "$WORK/instanzen-b")" = 1 ]; then
            echo "=== 8b. unregister OHNE Schalter, das Volumen des Snapshots bleibt ==="
            # Aenderung 1 dieser Fassung. Ohne den Schalter entfernt AppAPI den
            # Container und die Registrierung, das Volumen mit state.db, Index
            # und Vektorbestand bleibt stehen, und die Registrierung darunter
            # haengt den neuen Container an genau dieses Volumen.
            unregisterlog=$(mktemp "$WORK/92d-unregister.XXXXXX")
            unregister_status=0
            if ! occ app_api:app:unregister "$APP_ID" >"$unregisterlog" 2>&1; then
                occ app_api:app:unregister "$APP_ID" --force >>"$unregisterlog" 2>&1 ||
                    unregister_status=$?
            fi
            cat "$unregisterlog"
            printf 'unregister-rueckgabewert %s\n' "$unregister_status"
            echo "-- der Datenspeicher danach, er muss noch da sein --"
            sudo docker volume ls --filter name=findling_backend --format '{{.Name}}' \
                >"$WORK/volumen-danach" 2>/dev/null || true
            printf 'volumen-nach-unregister %s\n' "$(tr '\n' ' ' <"$WORK/volumen-danach")"
            sudo docker ps -a --filter name=findling_backend --format '{{.Names}} {{.Status}}' || true
        else
            : >"$WORK/zweite-instanz-b"
            echo "-- Die Zaehlung meldet nicht genau eine Instanz. Das unregister wird NICHT"
            echo "   gefahren, und dieser Lauf endet unterhalb der Pipeline. --"
        fi
    fi

    if [ ! -f "$WORK/upgrade-fehlt" ] && [ ! -f "$WORK/zweite-instanz-b" ]; then
        echo "=== 10. Die Registrierung ueber AppAPI, die zugleich die Scharfstellung ist ==="
        # AppAPI setzt registry/image:tag zusammen und kennt keinen Digest. Damit
        # der Zeiger auf das gepruefte Abbild zeigt, wird das gezogene Abbild
        # vorher lokal auf genau diesen Tag gelegt. Der Beweis bleibt trotzdem die
        # Kennung, die unten aus dem Container gelesen wird.
        sudo docker tag "$IMAGE" "$ABBILD_REPO:$IMAGE_TAG"
        sudo docker cp "$INFO_KOPIE" "$NEXTCLOUD:/tmp/92d-info-box.xml"
        sudo docker exec "$NEXTCLOUD" chown 33:33 /tmp/92d-info-box.xml
        date -u +'register-start %Y-%m-%dT%H:%M:%SZ'
        # L-03, die eine Aenderung von 92c gegen 92b, unveraendert. Der Aufruf
        # verlaesst die Ausgabekette dieses Blocks: er schreibt in eine eigene
        # Datei unter WORK, sein Rueckgabewert wird unmittelbar danach geprueft
        # und in einer Arbeitsdatei vermerkt, und erst danach laeuft seine
        # Ausgabe durch den Filter in die Rohdatei. In einer Pipeline liefert
        # der letzte Befehl den Rueckgabewert, hier also tee, und sh kennt kein
        # pipefail; ein gescheiterter Aufruf verliess deshalb nur diese
        # Subshell, und das Werkzeug endete mit 0, ohne dass registriert worden
        # war. Die Datei liegt unter WORK und faellt mit dem trap oben weg.
        registerlog=$(mktemp "$WORK/92d-register.XXXXXX")
        register_status=0
        occ app_api:app:register "$APP_ID" "$DAEMON" \
            --info-xml /tmp/92d-info-box.xml --wait-finish >"$registerlog" 2>&1 ||
            register_status=$?
        cat "$registerlog"
        printf 'registrierung-rueckgabewert %s\n' "$register_status"
        if [ "$register_status" -eq 0 ]; then
            echo "registrierung-gelungen ja"
        else
            echo "registrierung-gelungen nein"
            : >"$WORK/registrierung-fehlt"
        fi
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

        echo "=== 14. Der Zustand der ExApp und das erhaltene Volumen, von dem sie startet ==="
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
        sudo docker cp "$WERKZEUGE/40b-baumhash.py" "$CONTAINER:/tmp/40b-baumhash.py" 2>/dev/null || true
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

        echo "=== 17. Das Bestandstor, 52137 / 44 / 6, nach der Registrierung ==="
        # Neu in dieser Fassung, und es ist der Beweis fuer Aenderung 1: steht
        # der Snapshot nach dem Wechsel noch da, ist MESS-08 ohne Vollreindex
        # messbar. indexiert kommt aus der state.db des laufenden Containers,
        # read-only, weil die PHP-Haelfte diese Zahl nie schreibt; uebersprungen
        # und fehlgeschlagen kommen aus occ findling:index, der Zustandstabelle
        # der Nextcloud. Eine Zahl, die nicht lesbar ist, heisst unlesbar und
        # nicht 0, und unlesbar besteht das Tor nicht.
        indexiert=$(sudo docker exec "$CONTAINER" /app/.venv/bin/python -c '
import os
import sqlite3
pfad = os.path.join(os.environ["APP_PERSISTENT_STORAGE"], "state.db")
verbindung = sqlite3.connect("file:" + pfad + "?mode=ro", uri=True)
zeile = verbindung.execute(
    "select count(*) from files where state = ? and deleted_at is null", ("indexed",)
).fetchone()
print(zeile[0])
' 2>/dev/null || true)
        occ findling:index >"$WORK/findling-index.txt" 2>&1 || true
        cat "$WORK/findling-index.txt"
        uebersprungen=$(awk '$1 == "skipped" {print $2; exit}' "$WORK/findling-index.txt")
        fehlgeschlagen=$(awk '$1 == "failed" {print $2; exit}' "$WORK/findling-index.txt")
        indexiert=$(zahl_oder_unlesbar "$indexiert")
        uebersprungen=$(zahl_oder_unlesbar "$uebersprungen")
        fehlgeschlagen=$(zahl_oder_unlesbar "$fehlgeschlagen")
        printf 'bestandstor indexiert %s uebersprungen %s fehlgeschlagen %s\n' \
            "$indexiert" "$uebersprungen" "$fehlgeschlagen"
        printf 'bestandstor-erwartet indexiert %s uebersprungen %s fehlgeschlagen %s\n' \
            "$BESTAND_INDEXIERT" "$BESTAND_UEBERSPRUNGEN" "$BESTAND_FEHLGESCHLAGEN"
        if [ "$indexiert" = "$BESTAND_INDEXIERT" ] &&
            [ "$uebersprungen" = "$BESTAND_UEBERSPRUNGEN" ] &&
            [ "$fehlgeschlagen" = "$BESTAND_FEHLGESCHLAGEN" ]; then
            echo "bestandstor-bestanden ja"
            : >"$WORK/bestand-bestanden"
        else
            echo "bestandstor-bestanden nein"
        fi
    fi

    date -u +'wechsel-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Alles Folgende steht UNTERHALB der Pipeline, und nur dort. Der Rueckgabewert
# einer Pipeline, die in tee endet, gehoert zu tee; ein Abbruch innerhalb des
# Blocks verliesse nur die Subshell, und die Verweigerung waere eine Zeile in
# einer Rohdatei, die niemand liest. Gelesen wird deshalb aus den Arbeitsdateien
# unter WORK, in der Reihenfolge des Ablaufs.
if [ -f "$WORK/upgrade-fehlt" ]; then
    echo "92d-wechsel: occ upgrade ist gescheitert (Schritt 1b), die Nextcloud steht" >&2
    echo "92d-wechsel: vermutlich im eingeschraenkten Modus. unregister und register" >&2
    echo "92d-wechsel: sind nicht gefahren; die Ausgabe des upgrade steht in $ZIEL" >&2
    exit 40
fi
if [ -f "$WORK/zweite-instanz-b" ]; then
    echo "92d-wechsel: die Zaehlung unmittelbar vor dem unregister meldet $(cat "$WORK/instanzen-b")" >&2
    echo "92d-wechsel: statt genau einer Nextcloud. Das unregister ist nicht gefahren worden," >&2
    echo "92d-wechsel: und bis zur Klaerung wird nichts weiter getan (07.09.2026)" >&2
    exit 37
fi
if [ -f "$WORK/registrierung-fehlt" ]; then
    echo "92d-wechsel: der occ-Aufruf der Registrierung ist gescheitert (L-03)" >&2
    echo "92d-wechsel: die ExApp laeuft nicht auf dem geprueften Abbild, weil sie gar" >&2
    echo "92d-wechsel: nicht registriert worden ist. Das ist derselbe unbelegte Stand" >&2
    echo "92d-wechsel: wie ein Container auf einer fremden Abbildkennung, und er traegt" >&2
    echo "92d-wechsel: deshalb dieselbe Zahl" >&2
    exit 36
fi
if [ -f "$WORK/grenze-fehlt" ]; then
    echo "92d-wechsel: die cgroup meldet nicht $ERWARTETE_GRENZE/$ERWARTETER_SWAP in memory.max/memory.swap.max" >&2
    echo "92d-wechsel: ein Lauf, der gegen 4 GB misst, waehrend 2 GiB gemeint sind," >&2
    echo "92d-wechsel: misst eine andere Maschine als v1.1 und keine Abweichung" >&2
    exit 39
fi
if [ -f "$WORK/abbild-fremd" ]; then
    echo "92d-wechsel: der Container laeuft auf einer anderen Abbildkennung als der" >&2
    echo "92d-wechsel: geprueften. Der Baumhash hat ein Abbild belegt, gemessen wuerde" >&2
    echo "92d-wechsel: ein anderes, und das ist derselbe unbelegte Stand wie ein" >&2
    echo "92d-wechsel: fehlender Baumhash" >&2
    exit 36
fi
# Das Tor ist das einzige, das eine Marke fuer das Bestehen verlangt und nicht
# eine fuer das Scheitern: bricht der Block vorher unter set -eu ab, fehlt die
# Marke, und ein Wechsel, dessen Bestand niemand gezaehlt hat, endet hier und
# nicht mit 0.
if [ ! -f "$WORK/bestand-bestanden" ]; then
    echo "92d-wechsel: das Bestandstor meldet nicht $BESTAND_INDEXIERT / $BESTAND_UEBERSPRUNGEN / $BESTAND_FEHLGESCHLAGEN" >&2
    echo "92d-wechsel: (indexiert / uebersprungen / fehlgeschlagen). Der Snapshot steht nach" >&2
    echo "92d-wechsel: dem Wechsel nicht mehr so da, wie er gemessen werden soll, und MESS-08" >&2
    echo "92d-wechsel: wuerde einen anderen Bestand messen. Der Owner entscheidet neu" >&2
    exit 41
fi

echo "92D-WECHSEL-FERTIG"
