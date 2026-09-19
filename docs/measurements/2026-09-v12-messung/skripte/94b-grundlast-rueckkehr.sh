#!/bin/sh
# Der MEM-02-Block des v1.2-Laufs, Schritt 8b der Messreihenfolge. Er misst die
# Messgroesse "Rueckkehr zur Grundlast nach einem Indexlauf" und nichts daneben.
#
# **Warum MEM-02 ueberhaupt noch offen ist.** Die Abnahme der Phase 14 hat genau
# dieses eine Requirement ausdruecklich offengelassen: der Schalter
# FINDLING_EMBED_IDLE_RELEASE_SECONDS ist gebaut, seine Wirkung auf den Speicher
# ist auf der Zielarchitektur aber nie in einem Container gemessen worden, der
# vorher wirklich eingebettet hat. Die fuenf Zyklen des Vorprueflaufs vom
# 19.09.2026 liefen hintereinander im selben Prozess und ohne Nextcloud daneben.
# MEM-02 faellt auf dieser Box oder gar nicht, und deshalb steht sein Werkzeug
# hier, bevor die Box steht: waehrend der bezahlten Anfahrt wird kein Werkzeug
# mehr geaendert (Abschnitt 7.1 des Runbooks).
#
# **Warum die Messgroesse so heisst und keine andere sein darf.** Der Abschnitt
# zur Messgroesse in docs/performance.md sagt es woertlich: gemessen wird die
# Differenz zwischen "vor der Entladung" und "nach der Entladung", NACH einem
# Indexlauf. Die Gegenrichtung, also eine Differenz gegen die Grundlast eines
# Containers, der nie eingebettet hat, ist verboten, und das ist keine
# Wortklauberei. Die Grundlast ist seit dem faulen Bau von Plan 07-03 bereits
# OHNE Modell, OHNE Tokenizer und OHNE Splitter gemessen; in einem Container,
# der noch nichts eingebettet hat, liegt von alledem nichts im Speicher. Eine
# Differenz gegen diese Zahl zoege etwas ab, das in ihr gar nicht steckt, und
# waere nach oben erfunden. Das Warnzeichen dafuer steht im selben Abschnitt:
# eine genannte Ersparnis, die hoeher ist als die gemessene Differenz zwischen
# den beiden Marken. Die verbotene Formulierung kommt in diesem Werkzeug an
# keiner Stelle vor, auch nicht in einer Erklaerung, weil der naechste Leser sie
# sonst als Definition zitiert. Ein Gate in test_measurement_scripts.py haelt
# das fest.
#
# **Warum Marke A nicht die Bezugszahl ist.** Marke A steht trotzdem da, und sie
# steht erklaerend daneben: sie ist die Grundlast dieses Containerlebens, bevor
# irgendetwas eingebettet hat, und sie beantwortet die Frage, wie weit die
# Freigabe zurueckfuehrt. Gerechnet wird gegen Marke B, die Groesse unmittelbar
# nach dem Indexlauf. Erst dort stehen Tokenizer, Splitter, Sitzung und der
# Aktivierungsspeicher im Container, und genau darauf zielt die Freigabe. Der
# Aktivierungsspeicher ist der groesste dieser Posten: die Vorrecherche zur
# Phase 14 hat fuer den ersten run einer Sitzung +293,8 MB gemessen, und ueber
# zwanzig weitere Laeufe kamen +0,0 MB dazu.
#
# **Warum der Bodensatz ausgewiesen und nicht weggerechnet wird.** Die Freigabe
# fuehrt nicht auf den Stand vor dem Laden zurueck, sondern auf diesen plus
# einen Rest: die Modulimporte von onnxruntime und numpy bleiben geladen, egal
# wie oft entladen wird. Der Vorprueflauf vom 19.09.2026 hat den Rest auf
# aarch64 mit rund 16 MB gemessen (15,9 MB im ersten Zyklus, 17,1 MB ueber fuenf
# Zyklen). Dieses Werkzeug schreibt ihn als eigene Zeile bodensatz-mb neben das
# Ergebnis. Wer ihn wegrechnet, verspricht eine Rueckkehr auf die Grundlast, die
# es nicht gibt, und der Satz, der aus ihm folgt, gehoert in jeden Produkttext:
# der Container kehrt nicht auf die Grundlast eines Containers zurueck, der nie
# eingebettet hat, sondern auf diese plus rund 16 MB.
#
# **Warum dieses Werkzeug kein Argument nimmt.** Ein Aufruf
# "94b-grundlast-rueckkehr.sh <vorher|nachher>" waere der naheliegende Zuschnitt
# und ist ausdruecklich nicht der richtige: die Differenz zweier Marken ist nur
# innerhalb EINES Containerlebens eine Aussage. Ein zweiter Lauf spannte sie
# ueber zwei Containerleben, und ein neu gebauter Container startet auf seiner
# Grundlast, nicht auf der Stelle, an der der erste aufgehoert hat. Deshalb
# misst dieses Werkzeug in einem Zug, und ein uebergebenes Argument endet mit 2
# und der Benutzung auf stderr, damit niemand einen zweiten Zweig vermutet, den
# es nicht gibt. Die 2 steht als einzige Zahl OBERHALB der Pipeline: eine
# Verweigerung, die den Zuschnitt bestreitet, darf keine Rohdatei schreiben, und
# die Pipeline schreibt sie. Dieselbe Aufteilung faehrt 95b-wiederaufwaermen.sh
# seit Plan 15-03.
#
# **Welche Zahl aus der cgroup gelesen wird.** anon aus memory.stat, und nicht
# memory.current. Die Begruendung steht im Kopf von scripts/ops/rss_sampler.sh:
# anon ist der Heap, memory.current zaehlt den Seitencache derselben cgroup mit,
# und der Tantivy-Index ist ein mmap auf der Platte. Eine Differenz ueber
# memory.current maesse zu einem guten Teil, wie viele Indexbloecke zwischen den
# beiden Marken gelesen wurden. memory.current wird trotzdem in jeder Marke
# mitgeschrieben, weil der erste Leser, der den docker-Client nach dem Speicher
# des Containers fragt, eine Zahl auf memory.current bekommt und die Differenz
# erklaert finden soll statt versteckt.
#
# **Wie der Indexlauf angestossen wird, und warum nicht ueber occ.**
# occ findling:index kennt genau zwei Schalter, --status und --restart, und
# --restart stellt den vollen Bestand der Box neu in die Schlange: rund 52.000
# Dokumente, also Stunden, in denen der Container nie in den Leerlauf faellt und
# nie entlaedt. Angestossen wird deshalb ueber den Weg eines Nutzers, wie ihn
# 98c-sprachfaelle.sh geht: eine Handvoll kleiner Textdateien ueber WebDAV, dann
# files:scan, dann warten, bis die Einbettungsspur gearbeitet hat. Der Korpus
# wird nach der letzten Marke wieder entfernt, damit der Bestand der Box
# derselbe bleibt, gegen den Schritt 9 misst; die Zeilen dazu stehen im
# Protokoll.
#
# **Woran der Indexlauf abgelesen wird.** An der Zahl der eingebetteten
# Dokumente der Admin-Seite (Feld embedded unter backend), vor und nach dem
# Lauf, als die beiden Pflichtzeilen indexlauf-vorher und indexlauf-nachher. Die
# Ausgabe von occ findling:index steht in denselben Zeilen daneben, kann die
# Frage aber nicht beantworten: ihr Zaehler indexed ist auf der Nextcloud-Seite
# strukturell null und sagt das selbst ("indexed is counted by the backend
# container and never written here"). Sie liefert den Arbeitsvorrat, und der ist
# hier die zweite Bedingung: erst wenn er leer ist, ist der Lauf durch und die
# Ruhezeit beginnt an einem Container, der nichts mehr zu tun hat. Bewegt sich
# die Zahl der eingebetteten Dokumente nicht, endet dieses Werkzeug mit 33:
# ohne Indexlauf ist die Messgroesse eine andere, und die Zahl waere die
# Grundlast eines Containers, der nie eingebettet hat.
#
# **Abweichung, der Statusbeobachter.** 96d-statusbeobachter.py liest dieselbe
# Admin-Seite, seine Aufzeichnung ist aber projiziert und traegt engineState
# nicht. Es ist eine gefahrene Fassung und wird nicht geaendert
# (DRIVEN_FASSUNG_RULE). Dieses Skript liest die Seite deshalb selbst, ueber
# dieselbe Anmeldung und dasselbe data-requesttoken, genau wie
# 95b-wiederaufwaermen.sh es seit Plan 15-03 tut. Die Abweichung gehoert als
# Nachtrag ins Runbook (15-15).
#
# **Abweichung, die Belegung der Rueckgabewerte.** Abschnitt 7.1 des Runbooks
# fuehrt fuer diesen Schritt 32 als "die Grundlast vor dem Indexlauf wurde nicht
# abgetastet" und 33 als "der Container wurde zwischen den beiden Abtastungen
# neu gebaut". Beide Faelle sind hier erhalten und beide Zahlen tragen zusaetz-
# lich den Fall, den der Plan 15-04 ihnen gibt: 32 faellt, wenn die Abtastreihe
# oder der Bezugswert keine Zahl hergibt, 33, wenn kein Indexlauf stattfand oder
# der Container die Reihe zerrissen hat. Keine der beiden Bedeutungen ist
# weggefallen; auch das ist ein Nachtrag fuer 15-15.
#
# Die Exit-Codes setzen den Katalog dieses Laufverzeichnisses fort:
#
#   2  das Werkzeug wurde mit einem Argument gerufen, das es nicht gibt
#   29 die Stellung des Entladeschalters war nicht ablesbar oder sie passt nicht
#      zu diesem Block
#   31 nach Ruhezeit und Karenz stand kein unloaded: es gab keine Entladung,
#      also gibt es keine Rueckkehr zu messen (derselbe Befund wie in 7.2)
#   32 die Abtastreihe oder der Bezugswert hat keine Zahl hergegeben
#   33 es hat kein Indexlauf stattgefunden, oder der Container hat die Reihe
#      zwischen den Marken zerrissen
set -eu

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: 94b-grundlast-rueckkehr.sh

Ohne Argument. Dieses Werkzeug misst die Messgroesse "Rueckkehr zur Grundlast
nach einem Indexlauf" in EINEM Zug: Grundlast vor dem Indexlauf, Indexlauf,
Groesse unmittelbar danach, Ruhezeit, Groesse nach der Entladung.

Einen Zuschnitt <vorher|nachher> mit zwei Laeufen gibt es bewusst nicht. Die
Differenz zweier Marken ist nur innerhalb eines Containerlebens eine Aussage;
ueber zwei Laeufe gespannt maesse sie einen Containerneustart und keine
Freigabe.

Stellschrauben stehen als Umgebungsvariablen im Kopf der Datei, darunter
RUHEZEIT, KARENZ, ABTASTINTERVALL und INDEXLAUF_DECKEL.
HINWEIS
}

if [ "$#" -ne 0 ]; then
    benutzung
    exit 2
fi

# Alles, worin sich zwei Maschinen unterscheiden koennen, ist eine Variable mit
# Vorgabe, damit diese Datei keinen Pfad einer Maschine traegt. Die erste
# Vorgabe leitet sich aus dem Ort des Skripts selbst ab, was auf der Box und in
# einer Arbeitskopie gleichermassen haelt.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
# Der Container der ExApp und der der Nextcloud. Der erste traegt den Schalter
# und die cgroup, der zweite fuehrt occ.
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
ADRESSE="${ADRESSE:-https://loadtest.infranode.dev}"
BENUTZER="${BENUTZER:-admin}"
# Der NAME der Umgebungsvariablen, nicht ihr Wert. Ein Wert in einem Argument
# stuende in der Prozessliste der Box und in jedem Protokoll, das den Befehl
# aufzeichnet (T-10-27, T-15-06).
PASSWORT_ENV="${PASSWORT_ENV:-FINDLING_ADMIN_PASSWORD}"
# Die Admin-Seite, ueber die engineState und die Zahl der eingebetteten
# Dokumente nach draussen reisen. Ihr Lesen laedt kein Modell.
UEBERSICHT="${UEBERSICHT:-/apps/findling/admin/overview}"
# Die Ruhezeit in Sekunden, also die Frist, nach der die Gewichte freigegeben
# sein sollen. 120 s statt der 900 s des Vorschlagswerts, auf Owner-Entscheid
# D-02 vom 19.09.2026: gemessen wird, was NACH Ablauf der Frist geschieht, und
# nicht, wie lang die Frist ist. Der Mechanismus ist derselbe, die Ersparnis
# sind Stunden Box-Zeit. Die Begruendung steht unten als eigene Protokollzeile.
RUHEZEIT="${RUHEZEIT:-120}"
# Der Vorschlagswert aus backend/appinfo/info.xml, als Zahl und nicht als Wort.
# Er steht hier nur, damit die Abweichung eine Zahl hat, gegen die sie abweicht.
VORSCHLAGSWERT="${VORSCHLAGSWERT:-900}"
RUHEZEIT_GRUND="${RUHEZEIT_GRUND:-D-02 Owner-Entscheid 19.09.2026, derselbe Mechanismus und Stunden gesparte Box-Zeit}"
# Die Karenz oben auf die Ruhezeit. Die Freigabe faellt in einem Aufraeumlauf
# und nicht auf die Sekunde genau; ohne Karenz bekaeme die Messung einen Lauf
# ohne Entladung gemeldet, der nur zu frueh gefragt wurde.
KARENZ="${KARENZ:-45}"
# Der Takt der Abtastung waehrend der Ruhezeit, in Sekunden. Es ist der Takt,
# den rss_sampler.sh von Haus aus faehrt, und er bleibt es, damit die Reihe mit
# den Reihen der Vorlaeufe vergleichbar ist.
ABTASTINTERVALL="${ABTASTINTERVALL:-5}"
# Die Sekunden, die dem angestossenen Indexlauf hoechstens gegeben werden. Mehr
# ist ein Befund und kein Grund zu warten: der Poller laeuft bis zu 300 s in den
# Backoff, und der Fuenf-Minuten-Systemcron braucht zwei Runden, also sind 900 s
# der Boden und nicht das Ziel.
INDEXLAUF_DECKEL="${INDEXLAUF_DECKEL:-900}"
# Wie lange nach dem Containerneustart auf die Bereitschaft gewartet wird.
# Gefragt wird die Admin-Seite und NICHT die Suchroute: eine Suche laedt die
# Gewichte und machte die Marke A zu einer Zahl mit Modell darin.
BEREIT_DECKEL="${BEREIT_DECKEL:-180}"
# Die beiden Helfer aus scripts/ops/, UNVERAENDERT aufgerufen. Das ist nicht
# Ordnungsliebe: ihre Reihen und ihre Ueberschriften sind die Vergleichs-
# schluessel gegen die Vorlaeufe, und ein angepasster Abtaster machte die Zahl
# dieses Blocks mit den Zahlen von v1.1 unvergleichbar (T-15-11). Ein Gate ueber
# den sha256 beider Dateien haelt das fest.
SAMPLER="${SAMPLER:-$REPO/scripts/ops/rss_sampler.sh}"
DIGEST="${DIGEST:-$REPO/scripts/ops/rss_digest.py}"
# Der Ordner im Konto des Benutzers, in den der kleine Korpus des Indexlaufs
# hochgeladen wird, und die Zahl seiner Dateien. Klein, weil der Lauf nur die
# Einbettungsspur in Gang bringen muss und den Bestand der Box nicht aendern
# soll.
ORDNER="${ORDNER:-mem02-indexlauf}"
INDEXLAUF_DATEIEN="${INDEXLAUF_DATEIEN:-12}"

mkdir -p "$OUT"
ZIEL="${ZIEL:-$OUT/94b-grundlast-rueckkehr.txt}"
WORK=$(mktemp -d)
chmod 700 "$WORK"
ABTASTUNG="$WORK/abtastung"
mkdir -p "$ABTASTUNG"

# Der Abtaster laeuft im Hintergrund und wird am Ende der Ruhezeit mit TERM
# beendet. Bricht das Skript vorher ab, darf er nicht als Waise weiterlaufen und
# die cgroup der naechsten Messung abtasten.
ABTAST_PID=''
aufraeumen() {
    if [ -n "${ABTAST_PID:-}" ]; then
        sudo kill -TERM "$ABTAST_PID" 2>/dev/null || true
    fi
    rm -rf "$WORK"
}
trap aufraeumen EXIT

# Das Passwort des Kontos kommt aus der Umgebung und wird in eine Datei ohne
# abschliessenden Zeilenumbruch geschrieben; curl liest den Feldwert daraus. Ein
# Zeilenumbruch reiste als %0A mit und waere Teil des Passworts.
PWFELD="$WORK/pwfeld"
: >"$PWFELD"
chmod 600 "$PWFELD"
eval "printf '%s' \"\${$PASSWORT_ENV:-}\"" >"$PWFELD"
CURLRC="$WORK/curlrc"
: >"$CURLRC"
chmod 600 "$CURLRC"
{
    printf 'user = "%s:' "$BENUTZER"
    cat "$PWFELD"
    printf '"\n'
} >"$CURLRC"
JAR="$WORK/cookies.txt"

# Die Laufkennung. Sie haengt an Ordnername und Dateiinhalt, damit ein zweiter
# Lauf desselben Werkzeugs wirklich neue Dokumente einbettet: gleiche Namen mit
# gleichem Inhalt waeren unveraendert, und die Einbettungsspur haette nichts zu
# tun.
LAUF=$(date -u +%Y%m%dT%H%M%SZ)
ZIELORDNER="$ORDNER/$LAUF"

occ() {
    sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
}

# Die beiden Bloecke der Statusausgabe, aus EINEM Aufruf gelesen: zwei Quellen,
# aber zweimal fragen liesse sie einander widersprechen. Muster aus
# 93-nullstand.sh, unveraendert uebernommen.
vorrat_von() {
    awk '/^Work stock/ {found = 1; next}
         found && /^  (scheduled|handed to the worker)/ {sum += $NF}
         END {print sum + 0}' "$1"
}

# Die cgroup des Containers, nach dem Muster von 93-nullstand.sh und
# 95-spitze.sh. Die Kennung wird JEDES MAL neu gelesen: ein Neustart baut den
# Container neu, und ein stehengebliebener Pfad laese die cgroup von gestern.
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

# anon aus memory.stat, die Zahl, gegen die gerechnet wird. Begruendung im Kopf.
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

# Eine Differenz zweier Marken, in MB und mit einer Nachkommastelle. Ist eine
# der beiden keine Zahl, heisst das Ergebnis unbestimmt und nicht null: eine
# Null laese sich als gemessene Null lesen, und das waere genau die erfundene
# Zahl, gegen die dieser ganze Block geschrieben ist.
differenz_mb() {
    case "${1:-}${2:-}" in
    '' | *[!0-9]*)
        printf 'unbestimmt\n'
        return 0
        ;;
    esac
    awk -v links="$1" -v rechts="$2" 'BEGIN { printf "%.1f\n", (links - rechts) / 1048576 }'
}

# Jede Zeile des Protokollblocks wird gedruckt UND mitgeschrieben, damit ein
# Bericht die Pflichtzeilen als Block zitieren kann, statt sie aus einer langen
# Rohdatei zusammenzusuchen.
protokoll() {
    printf '%s\n' "$*" >>"$WORK/protokollblock"
    printf '%s\n' "$*"
}

# Die Anmeldung, Schritt fuer Schritt wie 95b-wiederaufwaermen.sh sie geht: das
# Formular mit dem Glas, das Token aus dem Formular, der POST mit Token und
# Origin, und danach noch eine Seite fuer ein frisches data-requesttoken, weil
# die Admin-Route ohne diesen Kopf mit einer Zurueckweisung antwortet.
anmelden() {
    rm -f "$JAR"
    curl -sfS -c "$JAR" -o "$WORK/login.html" "$ADRESSE/login" || return 1
    token=$(sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' "$WORK/login.html" | head -1)
    [ -n "${token:-}" ] || return 1
    weiter=$(curl -sS -b "$JAR" -c "$JAR" -o /dev/null -w '%{redirect_url}' \
        -H "Origin: $ADRESSE" \
        --data-urlencode "user=$BENUTZER" \
        --data-urlencode "password@$PWFELD" \
        --data-urlencode "requesttoken=$token" \
        "$ADRESSE/login" || true)
    case "$weiter" in
    '' | */login | */login\?*) return 1 ;;
    esac
    curl -sfS -b "$JAR" -c "$JAR" -o "$WORK/nach-anmeldung.html" "$ADRESSE/settings/admin" || return 1
    token=$(sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' "$WORK/nach-anmeldung.html" | head -1)
    [ -n "${token:-}" ] || return 1
    printf '%s\n' "$token" >"$WORK/token"
    return 0
}

# Eine Ablesung der Admin-Seite. Das Lesen dieser Seite laedt kein Modell, und
# genau deshalb ist sie hier die Quelle und nicht die Diagnose-Route.
uebersicht_holen() {
    token=$(cat "$WORK/token" 2>/dev/null || true)
    : >"$WORK/uebersicht.json"
    [ -n "${token:-}" ] || return 0
    curl -sS -b "$JAR" -c "$JAR" -H 'Accept: application/json' \
        -H "requesttoken: $token" -o "$WORK/uebersicht.json" \
        "$ADRESSE$UEBERSICHT" 2>/dev/null || : >"$WORK/uebersicht.json"
    return 0
}

# Ein Wort, das die Seite nicht hergibt, heisst unbekannt und nicht cold: ein
# geratener Zustand waere hier die halbe Aussage des ganzen Schrittes.
engine_zustand() {
    uebersicht_holen
    zustand=$(sed -n 's/.*"engineState"[[:space:]]*:[[:space:]]*"\([A-Za-z_]*\)".*/\1/p' \
        "$WORK/uebersicht.json" 2>/dev/null | head -1)
    [ -n "${zustand:-}" ] || zustand=unbekannt
    printf '%s\n' "$zustand"
}

# Die Zahl der eingebetteten Dokumente, das Feld embedded unter backend. Es ist
# die einzige Quelle, die den Indexlauf belegen kann: der Zaehler indexed der
# Nextcloud-Seite ist strukturell null und sagt das selbst.
eingebettet() {
    uebersicht_holen
    zahl=$(sed -n 's/.*"embedded"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p' \
        "$WORK/uebersicht.json" 2>/dev/null | head -1)
    [ -n "${zahl:-}" ] || zahl=unlesbar
    printf '%s\n' "$zahl"
}

# Die Bereitschaft nach dem Neustart, gefragt an der Admin-Seite. Ein Wort, das
# nicht unbekannt ist, heisst: der Container antwortet wieder.
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

{
    date -u +'grundlast-rueckkehr-start %Y-%m-%dT%H:%M:%SZ'
    printf 'messgroesse=Rueckkehr zur Grundlast nach einem Indexlauf\n'
    printf 'ruhezeit %s s, karenz %s s, abtastintervall %s s, indexlauf-deckel %s s\n' \
        "$RUHEZEIT" "$KARENZ" "$ABTASTINTERVALL" "$INDEXLAUF_DECKEL"
    printf 'abtaster %s, digest %s, beide unveraendert gerufen\n' "$SAMPLER" "$DIGEST"
    printf 'nachbar-container %s, arbeitskopie %s, laufkennung %s\n' "$NEXTCLOUD" "$REPO" "$LAUF"

    echo "=== 1. Die Pflichtzeilen, VOR der Messung ==="
    echo "-- Ohne sie sind die Zahlen daneben nicht falsch, sie sind unbelegt (Abschnitt 6.4) --"

    if sudo docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$CONTAINER" \
        >"$WORK/umgebung" 2>/dev/null; then
        SCHALTER=$(awk -F= '/^FINDLING_EMBED_IDLE_RELEASE_SECONDS=/ {print $2; exit}' "$WORK/umgebung")
        if [ -z "${SCHALTER:-}" ]; then
            SCHALTER=0
            protokoll "entladeschalter-ist=$SCHALTER werksstand"
        else
            protokoll "entladeschalter-ist=$SCHALTER"
        fi
    else
        SCHALTER=unlesbar
        protokoll "entladeschalter-ist=unlesbar"
        : >"$WORK/schalter-unlesbar"
    fi

    # Dieser Block braucht den eingeschalteten Schalter. Bei 0 gibt es keine
    # Freigabe, die Ruhezeit verginge ohne Wirkung, und die Zahl am Ende waere
    # die Groesse eines Containers, der einfach nichts getan hat.
    if [ "$SCHALTER" != unlesbar ]; then
        case "$SCHALTER" in
        *[!0-9]*)
            protokoll "entladeschalter-passt-zum-block=nein, kein Zahlenwert"
            : >"$WORK/schalter-unlesbar"
            ;;
        *)
            if [ "$SCHALTER" -gt 0 ]; then
                protokoll "entladeschalter-passt-zum-block=ja, Freigabe eingeschaltet"
            else
                protokoll "entladeschalter-passt-zum-block=nein, der MEM-02-Block verlangt einen Wert groesser null"
                : >"$WORK/schalter-unlesbar"
            fi
            ;;
        esac
    fi

    START=$(sudo docker inspect --format '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || true)
    [ -n "${START:-}" ] || START=unlesbar
    protokoll "containerstart-ist=$START"

    # Erwartung 2147483648 in beiden Feldern. Eine Abweichung ist ein
    # protokollierter Befund und kein Abbruch dieses Skripts: der Abbruch dafuer
    # ist Rueckgabewert 39 und gehoert zu Block 13b.
    protokoll "speichergrenze-ist=$(cgroup_wert memory.max)/$(cgroup_wert memory.swap.max)"

    protokoll "ruhezeit-ist=$RUHEZEIT"
    if [ "$RUHEZEIT" -ne "$VORSCHLAGSWERT" ]; then
        protokoll "ruhezeit-abweichung-grund=$RUHEZEIT_GRUND"
    fi

    if [ -f "$WORK/schalter-unlesbar" ]; then
        echo "-- Die Pflichtzeile steht nicht oder sie steht gegen diesen Block. Gemessen wird"
        echo "   nichts mehr, und der Lauf endet unterhalb der Pipeline. --"
        WEITER=nein
    else
        WEITER=ja
    fi

    if [ "$WEITER" = ja ]; then
        echo "=== 2. Marke A: die Grundlast vor dem Indexlauf ==="
        echo "-- Containerneustart zuerst, denn Marke A ist die Groesse eines Containers,"
        echo "   der in DIESEM Leben noch nichts eingebettet hat. Nach den Schritten 4, 6"
        echo "   und 8 ist der Container aufgewaermt, und ohne Neustart maesse Marke A"
        echo "   einen Container mit Tokenizer, Splitter und Sitzung darin. --"
        sudo docker restart "$CONTAINER" >/dev/null
        START=$(sudo docker inspect --format '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || true)
        [ -n "${START:-}" ] || START=unlesbar
        printf '%s\n' "$START" >"$WORK/containerstart-a"
        protokoll "containerstart-nach-neustart=$START"
        if anmelden; then
            echo "anmeldung ok"
        else
            echo "anmeldung fehlgeschlagen, die Admin-Seite ist nicht lesbar und engineState bleibt unbekannt"
        fi
        bereit_warten || echo "-- der Container hat den Bereitschaftsdeckel gerissen, gemessen wird trotzdem --"

        MARKE_A=$(anon_von)
        printf '%s\n' "$MARKE_A" >"$WORK/marke-a"
        protokoll "marke-a-grundlast-vor-indexlauf=$(mb_von "$MARKE_A") MB (anon $MARKE_A byte)"
        protokoll "marke-a-memory-current=$(cgroup_wert memory.current)"
        echo "-- Marke A ist die Bezugszahl NICHT. Sie steht erklaerend daneben und sagt, wie"
        echo "   weit die Freigabe zurueckfuehrt. Gerechnet wird gegen Marke B. --"
        protokoll "engine-zustand-bei-marke-a=$(engine_zustand)"

        VORHER=$(eingebettet)
        printf '%s\n' "$VORHER" >"$WORK/eingebettet-vorher"
        occ findling:index >"$WORK/status-vorher.txt" 2>&1 || true
        protokoll "indexlauf-vorher=$VORHER eingebettete Dokumente, arbeitsvorrat $(vorrat_von "$WORK/status-vorher.txt")"
    fi

    if [ "$WEITER" = ja ]; then
        echo "=== 3. Der Indexlauf, angestossen auf dem Weg eines Nutzers ==="
        echo "-- Eine Handvoll kleiner Textdateien ueber WebDAV, danach files:scan. Nicht"
        echo "   findling:index --restart: das stellte rund 52.000 Dokumente neu in die"
        echo "   Schlange, und der Container fiele in dieser Messung nie in den Leerlauf. --"
        mkdir -p "$WORK/korpus"
        nummer=1
        while [ "$nummer" -le "$INDEXLAUF_DATEIEN" ]; do
            {
                printf 'Messlauf %s, Datei %s von %s.\n' "$LAUF" "$nummer" "$INDEXLAUF_DATEIEN"
                printf 'Dieser Text gehoert zum MEM-02-Block der Messphase und dient einem Zweck:\n'
                printf 'die Einbettungsspur des Containers in Gang zu bringen, damit Tokenizer,\n'
                printf 'Splitter, Sitzung und Aktivierungsspeicher wirklich im Speicher stehen.\n'
                printf 'Bescheid, Antrag, Vermerk, Protokoll, Gebuehrenordnung, Widerspruch.\n'
                printf 'Der Ordner wird nach der letzten Marke wieder entfernt.\n'
            } >"$WORK/korpus/mem02-$LAUF-$nummer.txt"
            nummer=$((nummer + 1))
        done

        BASISORDNER="$ADRESSE/remote.php/dav/files/$BENUTZER"
        curl -sS -o /dev/null -K "$CURLRC" -X MKCOL "$BASISORDNER/$ORDNER" || true
        curl -sS -o /dev/null -K "$CURLRC" -X MKCOL "$BASISORDNER/$ZIELORDNER" || true
        : >"$WORK/upload.txt"
        for pfad in "$WORK/korpus"/*; do
            name=$(basename "$pfad")
            code=$(curl -sS -o /dev/null -w '%{http_code}' -K "$CURLRC" \
                -T "$pfad" "$BASISORDNER/$ZIELORDNER/$name" || echo 000)
            printf '%s %s\n' "$code" "$name" >>"$WORK/upload.txt"
        done
        HOCHGELADEN=$(awk '$1 ~ /^2/ {n++} END {print n + 0}' "$WORK/upload.txt")
        protokoll "indexlauf-korpus-hochgeladen=$HOCHGELADEN von $INDEXLAUF_DATEIEN nach $ZIELORDNER"
        occ files:scan --path="/$BENUTZER/files/$ZIELORDNER" 2>&1 | tail -4 || true

        echo "-- Gewartet wird auf ZWEI Bedingungen: die Zahl der eingebetteten Dokumente hat"
        echo "   sich bewegt, und der Arbeitsvorrat ist leer. Die zweite ist noetig, weil die"
        echo "   Ruhezeit sonst an einem Container liefe, der noch zu tun hat. --"
        date -u +'indexlauf-start %Y-%m-%dT%H:%M:%SZ'
        verstrichen=0
        beginn=$(date +%s)
        NACHHER="$VORHER"
        VORRAT=unklar
        while [ "$verstrichen" -le "$INDEXLAUF_DECKEL" ]; do
            sleep 15
            verstrichen=$(($(date +%s) - beginn))
            NACHHER=$(eingebettet)
            occ findling:index >"$WORK/status-nachher.txt" 2>&1 || true
            VORRAT=$(vorrat_von "$WORK/status-nachher.txt")
            printf 'indexlauf-zwischenstand s=%s eingebettet=%s arbeitsvorrat=%s\n' \
                "$verstrichen" "$NACHHER" "$VORRAT"
            case "$VORHER$NACHHER" in
            *[!0-9]*) continue ;;
            esac
            if [ "$NACHHER" -gt "$VORHER" ] && [ "$VORRAT" -eq 0 ]; then
                break
            fi
        done
        date -u +'indexlauf-ende %Y-%m-%dT%H:%M:%SZ'
        printf '%s\n' "$NACHHER" >"$WORK/eingebettet-nachher"
        protokoll "indexlauf-nachher=$NACHHER eingebettete Dokumente, arbeitsvorrat $VORRAT"
        protokoll "indexlauf-dauer-s=$verstrichen von hoechstens $INDEXLAUF_DECKEL"

        BEWEGT=nein
        case "$VORHER$NACHHER" in
        '' | *[!0-9]*) ;;
        *)
            if [ "$NACHHER" -gt "$VORHER" ]; then
                BEWEGT=ja
            fi
            ;;
        esac
        protokoll "indexlauf-stattgefunden=$BEWEGT"
        if [ "$BEWEGT" != ja ]; then
            echo "-- Ohne bewegten Stand der eingebetteten Dokumente hat kein Indexlauf"
            echo "   stattgefunden. Die Messgroesse waere dann eine andere, und die Zahl waere"
            echo "   die Grundlast eines Containers, der nie eingebettet hat. Der Lauf endet"
            echo "   unterhalb der Pipeline. --"
            : >"$WORK/kein-indexlauf"
            WEITER=nein
        fi
    fi

    if [ "$WEITER" = ja ]; then
        echo "=== 4. Marke B: die Groesse unmittelbar nach dem Indexlauf ==="
        echo "-- Das ist die Zahl, gegen die gerechnet wird. Hier stehen Tokenizer, Splitter,"
        echo "   Sitzung und der Aktivierungsspeicher im Container. --"
        MARKE_B=$(anon_von)
        printf '%s\n' "$MARKE_B" >"$WORK/marke-b"
        protokoll "marke-b-vor-der-entladung=$(mb_von "$MARKE_B") MB (anon $MARKE_B byte)"
        protokoll "marke-b-memory-current=$(cgroup_wert memory.current)"
        protokoll "engine-zustand-bei-marke-b=$(engine_zustand)"

        echo "=== 5. Die Ruhezeit, abgetastet mit rss_sampler.sh ==="
        echo "-- $RUHEZEIT s Ruhezeit plus $KARENZ s Karenz. Die Freigabe faellt in einem"
        echo "   Aufraeumlauf und nicht auf die Sekunde genau. --"
        sudo "$SAMPLER" "$CONTAINER" "$ABTASTINTERVALL" "$ABTASTUNG/$CONTAINER.csv" \
            >"$WORK/sampler.log" 2>&1 &
        ABTAST_PID=$!
        sleep "$((RUHEZEIT + KARENZ))"
        sudo kill -TERM "$ABTAST_PID" 2>/dev/null || true
        wait "$ABTAST_PID" 2>/dev/null || true
        ABTAST_PID=''
        echo "-- die Meldungen des Abtasters --"
        sed 's/^/  /' "$WORK/sampler.log" 2>/dev/null || true

        ZUSTAND=$(engine_zustand)
        protokoll "engine-zustand-nach-ruhezeit=$ZUSTAND"
        if [ "$ZUSTAND" != unloaded ]; then
            echo "-- Kein unloaded nach Ruhezeit und Karenz: es gab keine Entladung, also gibt es"
            echo "   keine Rueckkehr zu messen. Derselbe Befund und dieselbe Zahl wie in"
            echo "   Abschnitt 7.2 des Runbooks. Der Lauf endet unterhalb der Pipeline. --"
            : >"$WORK/keine-entladung"
            WEITER=nein
        fi
    fi

    if [ "$WEITER" = ja ]; then
        echo "=== 6. Marke C: die Groesse nach der Entladung, und der Digest ==="
        MARKE_C=$(anon_von)
        printf '%s\n' "$MARKE_C" >"$WORK/marke-c"
        protokoll "marke-c-nach-der-entladung=$(mb_von "$MARKE_C") MB (anon $MARKE_C byte)"
        protokoll "marke-c-memory-current=$(cgroup_wert memory.current)"

        # Die Reihe muss EIN Containerleben sein. Ein neu gebauter Container
        # startet auf seiner Grundlast, und die Differenz waere dann ein
        # Neustart und keine Freigabe (Rueckgabewert 33 des Runbooks).
        START_C=$(sudo docker inspect --format '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || true)
        [ -n "${START_C:-}" ] || START_C=unlesbar
        protokoll "containerstart-bei-marke-c=$START_C"
        if [ "$START_C" != "$(cat "$WORK/containerstart-a" 2>/dev/null || echo unlesbar)" ]; then
            echo "-- Der Container wurde zwischen den Marken neu gebaut. Die Reihe ist"
            echo "   zerrissen, und der Lauf endet unterhalb der Pipeline. --"
            : >"$WORK/reihe-unterbrochen"
            WEITER=nein
        fi

        echo "-- rss_digest.py ueber die Abtastreihe der Ruhezeit, unveraendert gerufen --"
        if python3 "$DIGEST" "$ABTASTUNG" >"$WORK/digest.txt" 2>"$WORK/digest.err"; then
            cat "$WORK/digest.txt"
        else
            echo "der Digest hat keine Reihe gefunden:"
            sed 's/^/  /' "$WORK/digest.err" 2>/dev/null || true
        fi
        SPITZE=$(awk -F: '/^total, peak:/ {gsub(/[^0-9]/, "", $2); print $2; exit}' \
            "$WORK/digest.txt" 2>/dev/null || true)
        [ -n "${SPITZE:-}" ] || SPITZE=unlesbar
        protokoll "abtastreihe-spitze-mb=$SPITZE"
        protokoll "abtastreihe-zeilen=$(grep -c '^findling-rss ' "$ABTASTUNG/$CONTAINER.csv" 2>/dev/null || echo 0)"
        if [ "$SPITZE" = unlesbar ] || [ "$(cat "$WORK/marke-a" 2>/dev/null || echo unlesbar)" = unlesbar ]; then
            echo "-- Ohne Zahl aus der Abtastreihe oder ohne Bezugswert vor dem Indexlauf ist die"
            echo "   Rueckkehr keine Messgroesse, sondern eine Zahl. Der Lauf endet unterhalb der"
            echo "   Pipeline. --"
            : >"$WORK/keine-abtastung"
            WEITER=nein
        fi
    fi

    if [ "$WEITER" = ja ]; then
        echo "=== 7. Das Ergebnis ==="
        protokoll "rueckkehr-zur-grundlast-mb=$(differenz_mb "$MARKE_B" "$MARKE_C")"
        protokoll "bodensatz-mb=$(differenz_mb "$MARKE_C" "$MARKE_A")"
        echo "-- Der Bodensatz kommt nie zurueck: die Modulimporte von onnxruntime und numpy"
        echo "   bleiben geladen, egal wie oft entladen wird. Auf aarch64 sind dafuer rund"
        echo "   16 MB gemessen (2026-09-entladung-vorpruefung, Abschnitt 6). Er wird"
        echo "   ausgewiesen und nicht weggerechnet: der Container kehrt nicht auf die"
        echo "   Grundlast eines Containers zurueck, der nie eingebettet hat, sondern auf"
        echo "   diese plus diesen Rest. --"
        protokoll "messgroesse=Rueckkehr zur Grundlast nach einem Indexlauf"
        protokoll "bezugszahl=marke-b-vor-der-entladung, nicht marke-a-grundlast-vor-indexlauf"
    fi

    echo "=== 8. Der Korpus des Indexlaufs, wieder entfernt ==="
    echo "-- Der Bestand der Box ist der, gegen den Schritt 9 misst. Die Entfernung steht"
    echo "   hinter der letzten Marke und kann keine Zahl mehr beruehren. --"
    ENTFERNT=$(curl -sS -o /dev/null -w '%{http_code}' -K "$CURLRC" \
        -X DELETE "$ADRESSE/remote.php/dav/files/$BENUTZER/$ZIELORDNER" || echo 000)
    protokoll "indexlauf-korpus-entfernt=$ENTFERNT ($ZIELORDNER)"

    echo "=== Der Protokollblock, als Block zitierbar ==="
    cat "$WORK/protokollblock"

    date -u +'grundlast-rueckkehr-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Alles Folgende steht UNTERHALB der Pipeline, und nur dort. Der Rueckgabewert
# einer Pipeline, die in tee endet, gehoert zu tee; ein Abbruch innerhalb des
# Blocks verliesse nur die Subshell, und die Verweigerung waere eine Zeile in
# einer Rohdatei, die niemand liest. Gelesen wird deshalb aus den Arbeitsdateien
# unter WORK (Muster aus 97-cron-vorpruefung.sh). Die Reihenfolge der Pruefungen
# ist die Reihenfolge des Ablaufs, damit der erste Befund auch der erste ist,
# der gefallen ist.
if [ -f "$WORK/schalter-unlesbar" ]; then
    echo "94b-grundlast-rueckkehr: die Stellung des Entladeschalters war nicht ablesbar" >&2
    echo "94b-grundlast-rueckkehr: oder sie steht auf 0, und dann gibt es keine Freigabe" >&2
    echo "94b-grundlast-rueckkehr: ein Lauf ohne protokollierte Stellung gilt als unvollstaendig (Abschnitt 6.4)" >&2
    exit 29
fi
if [ -f "$WORK/kein-indexlauf" ]; then
    echo "94b-grundlast-rueckkehr: der Stand der eingebetteten Dokumente hat sich nicht bewegt" >&2
    echo "94b-grundlast-rueckkehr: ohne Indexlauf ist die Messgroesse eine andere" >&2
    echo "94b-grundlast-rueckkehr: die Zahl waere die Grundlast eines Containers, der nie eingebettet hat" >&2
    exit 33
fi
if [ -f "$WORK/reihe-unterbrochen" ]; then
    echo "94b-grundlast-rueckkehr: der Container wurde zwischen den Marken neu gebaut" >&2
    echo "94b-grundlast-rueckkehr: ein neu gebauter Container startet auf seiner Grundlast" >&2
    echo "94b-grundlast-rueckkehr: die Differenz waere ein Neustart und keine Freigabe" >&2
    exit 33
fi
if [ -f "$WORK/keine-entladung" ]; then
    echo "94b-grundlast-rueckkehr: nach Ruhezeit und Karenz stand kein unloaded" >&2
    echo "94b-grundlast-rueckkehr: es gab keine Entladung, also gibt es keine Rueckkehr zu messen" >&2
    exit 31
fi
if [ -f "$WORK/keine-abtastung" ]; then
    echo "94b-grundlast-rueckkehr: die Abtastreihe oder der Bezugswert hat keine Zahl hergegeben" >&2
    echo "94b-grundlast-rueckkehr: eine Rueckkehr ohne den Wert, zu dem zurueckgekehrt wird," >&2
    echo "94b-grundlast-rueckkehr: ist keine Messgroesse, sondern eine Zahl" >&2
    exit 32
fi

echo "94B-GRUNDLAST-RUECKKEHR-FERTIG"
