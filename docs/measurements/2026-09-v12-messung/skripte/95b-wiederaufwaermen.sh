#!/bin/sh
# Die Wiederaufwaerm-Messung des v1.2-Laufs, Schritt 8 der Messreihenfolge. Sie
# ist EIN Vergleich in vier Auspraegungen, und je Lauf faehrt genau eine.
#
# **Warum dieses Werkzeug bis heute fehlte.** Abschnitt 7.2 des Runbooks fuehrt
# fuer diesen Schritt drei Rueckgabewerte (29, 30, 31) und sagt, sie stuenden
# unterhalb der tee-Pipeline ihres Skripts. Ein solches Skript gab es nicht.
# Was es gab, war 95b-kaltstart-reproduktion.txt aus dem v1.1-Lauf, und das ist
# eine ROHDATEI von Hand: eine Messung, die am 10.09.2026 Zeile fuer Zeile
# getippt wurde, mit einem SyntaxError aus einem inline getippten Einzeiler in
# ihrer letzten Zeile. Eine Rohdatei ist kein Werkzeug. Waehrend der bezahlten
# Anfahrt wird kein Werkzeug mehr geaendert (Abschnitt 7.1), also muss dieses
# vorher stehen und seine Verweigerungspfade boxlos belegt haben.
#
# **Was die vier Auspraegungen messen.** Sie vergleichen zwei Stellungen von
# FINDLING_EMBED_IDLE_RELEASE_SECONDS, also den Schalter aus MEM-01, und sie
# kreuzen sie mit dem Zustand des Seitencaches des Wirts:
#
#   1  Schalter an, Seitencache kalt   die Ruhezeit wird abgewartet, dann eine
#                                      Suche: die Antwortzeit der degradierten
#                                      Suche und die Dauer des Nachwaermens
#   2  Schalter an, Seitencache warm   dieselbe Messung ohne Leeren des Caches
#   3  Schalter aus, Seitencache kalt  der Bezugswert ohne Entladung, nach dem
#                                      Muster 95b-kaltstart-reproduktion
#   4  Schalter aus, Seitencache warm  derselbe Bezugswert ohne Leeren
#
# Eine Auspraegung je Lauf, und das ist keine Bequemlichkeit: jeder Wechsel der
# Stellung baut den Container neu, und nach jedem Neubau werden die harte
# Speichergrenze aus Block 12 und die Pflichtzeile aus Abschnitt 6.4 neu
# ABGELESEN und nicht erinnert. Jede Auspraegung bekommt deshalb ihre eigene
# Rohdatei.
#
# **Warum die Reihenfolge bindend ist.** Jede Messung waermt den Seitencache des
# Wirts, und eine einmal gewaermte Kaltmessung ist nicht wiederholbar, ohne den
# Cache erneut zu leeren. Innerhalb des Schrittes gilt deshalb: erst 1 und 3
# kalt, danach 2 und 4 warm. Und kalt wird HERGESTELLT und nicht bewahrt: die
# Bestandssonde (Schritt 3) faehrt ueber die Diagnose-Route und die Laststufen
# (Schritt 6) laden das Modell absichtlich vor der Reihe, beide liegen vor
# diesem Schritt und beide sind nicht verschiebbar. Jede Auspraegung beginnt
# daher mit einem Containerneustart, und die kalten mit dem geleerten
# Wirtscache danach.
#
# **Warum die semantische Seite an der Nutzerroute abgelesen wird und nie an
# der Diagnose-Route.** Nach einer Entladung meldet die Diagnose-Route eine
# vollstaendige semantische Seite, weil sie LAEDT; sie traegt keine 1,5-s-Decke
# und fragt query_may_load() nicht. Die Nutzerrouten melden im selben Moment
# eine leere Seite, weil sie unter dem Schalter nicht laden duerfen. Wer die
# zwei verwechselt, misst zwei verschiedene Dinge und nennt sie eine Zahl.
# Gemessen wird deshalb ausschliesslich gegen
# /ocs/v2.php/search/providers/findling/search, dieselbe Route, die auch
# scripts/ops/search_load.py fragt. Die Diagnose-Route kommt in dieser Datei
# genau einmal vor: als Suchmuster ueber docker logs, also als Wachposten.
#
# **Wie die semantische Seite abgelesen wird, und was diese Ablesung nicht
# kann.** Die Nutzerroute traegt kein Feld, das "die semantische Haelfte stand"
# sagt; degraded meint den unvollstaendigen Index und nicht die fehlenden
# Gewichte. Abgelesen wird deshalb an der TREFFERZAHL desselben zweiwortigen
# Begriffs gegen eine Referenzzahl aus demselben Lauf: in den Auspraegungen 1
# und 2 ist die Referenz die Waermsuche VOR der Ruhezeit, in 3 und 4 die zweite
# Suche NACH der Messsuche. Beide Referenzen entstehen mit geladenen Gewichten.
# Liegt die gemessene Trefferzahl darunter, fehlte die zweite Liste. Der Begriff
# hat zwei Woerter, weil eine einwortige Zeile seit Plan 06.1-20 ohnehin allein
# aus dem Wortindex beantwortet wird und dann NIE eine semantische Haelfte
# haette, die fehlen koennte.
#
# **Die Nebenwirkung des Leerens, im Klartext.** sync und drop_caches verwerfen
# auch den mmap-Cache des Tantivy-Index. Die kalte Suche misst damit BEIDE
# Haelften kalt, die Semantik und den Volltext, und nicht allein das Nachladen
# der Gewichte. Das ist die gewollte schlechtere Haelfte der Wahrheit: sie ist
# der Fall, den ein Nutzer nach einem Neustart der Box wirklich bekommt. Im
# Bericht muss sie dastehen, sonst liest sich eine Zahl als
# Wiederaufwaermkosten, die zum Teil Indexkosten ist. Geleert wird auf dem WIRT
# und nicht im Container: /proc/sys ist dort nicht beschreibbar, und der Cache
# gehoert ohnehin dem Wirt.
#
# **Abweichung 1, der Entladezaehler.** Abschnitt 7.2 des Runbooks nennt als
# Beleg der Entladung den Zustand unloaded UND den Entladezaehler des
# Containers. Der Zaehler ist ueber eine Prozessgrenze nicht lesbar: er hat
# keine Route, er lebt im Prozess des Containers, und ein docker exec python -c
# startet einen ZWEITEN Prozess mit einem eigenen Zaehler auf null und misst
# nichts. Dieses Skript liest deshalb den Zustand unloaded der Admin-Seite und
# nimmt als zweiten, unabhaengigen Anhaltspunkt die cgroup-Groesse
# memory.current vor und nach der Ruhezeit (rss-vor-ruhezeit,
# rss-nach-ruhezeit). Die Abweichung gehoert als Nachtrag ins Runbook (15-15).
#
# **Abweichung 2, der Statusbeobachter.** 96d-statusbeobachter.py liest zwar die
# Admin-Seite, seine Aufzeichnung ist aber auf sechs Zaehler, runState,
# backendReachable und das genestete Paar projiziert; engineState ist dort NICHT
# darunter, weil das Werkzeug aus dem v1.1-Lauf stammt und der Zustand erst mit
# Phase 14 entstand. Es ist eine gefahrene Fassung und wird nicht geaendert
# (DRIVEN_FASSUNG_RULE). Dieses Skript liest die Admin-Seite deshalb selbst,
# ueber dieselbe Anmeldung und dasselbe data-requesttoken, das 96d benutzt, und
# liest daraus genau ein Feld. Auch diese Abweichung gehoert ins Runbook
# (15-15).
#
# Die Exit-Codes setzen den Katalog dieses Laufverzeichnisses fort. 15 bis 28
# sind in 98c-sprachfaelle.sh und 97-cron-vorpruefung.sh vergeben und bleiben,
# was sie dort sind:
#
#   2  Aufruf ohne Auspraegung oder mit einer unbekannten Auspraegung
#   29 die Stellung des Entladeschalters war nicht ablesbar, oder sie passt
#      nicht zu dem Ast, der gefahren werden soll
#   30 der Container war vor einer Kaltmessung aufgewaermt
#   31 der Ast mit eingeschaltetem Schalter hat keine Entladung erlebt
set -eu

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: 95b-wiederaufwaermen.sh <1|2|3|4>

  1  Schalter an, Seitencache kalt. Ruhezeit abwarten, Cache leeren, messen.
  2  Schalter an, Seitencache warm. Derselbe Ablauf ohne das Leeren.
  3  Schalter aus, Seitencache kalt. Kaltstart-Reproduktion ohne Entladung.
  4  Schalter aus, Seitencache warm. Derselbe Bezugswert ohne das Leeren.

Genau eine Auspraegung je Lauf: jeder Wechsel der Stellung von
FINDLING_EMBED_IDLE_RELEASE_SECONDS baut den Container neu, und jede
Auspraegung bekommt ihre eigene Rohdatei.

Ohne Auspraegung oder mit einer unbekannten Auspraegung endet dieses Skript mit
2, bevor ein Container, eine Adresse oder eine Datei angefasst wird.
HINWEIS
}

AUSPRAEGUNG="${1:-}"
case "$AUSPRAEGUNG" in
1 | 2 | 3 | 4) ;;
*)
    benutzung
    exit 2
    ;;
esac

# Alles, worin sich zwei Maschinen unterscheiden koennen, ist eine Variable mit
# Vorgabe, damit diese Datei keinen Pfad einer Maschine traegt. Die erste
# Vorgabe leitet sich aus dem Ort des Skripts selbst ab, was auf der Box und in
# einer Arbeitskopie gleichermassen haelt.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
# Die Wurzel der Arbeitskopie. Dieses Skript liest sie nicht, es faehrt docker
# und curl; sie steht hier, weil die uebrigen Skripte dieses Laufverzeichnisses
# sie fuehren und ein Boxplan, der sie setzt, daran nicht scheitern soll.
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
# Der Container der ExApp und der der Nextcloud. Der erste traegt den Schalter
# und die cgroup, der zweite ist nur der Nachbar und wird hier nicht gefahren.
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
ADRESSE="${ADRESSE:-https://loadtest.infranode.dev}"
BENUTZER="${BENUTZER:-admin}"
# Der NAME der Umgebungsvariablen, nicht ihr Wert. Ein Wert in einem Argument
# stuende in der Prozessliste der Box und in jedem Protokoll, das den Befehl
# aufzeichnet (T-10-27, T-15-06).
PASSWORT_ENV="${PASSWORT_ENV:-FINDLING_ADMIN_PASSWORD}"
# Die Admin-Seite, ueber die engineState nach draussen reist. Ihr Lesen laedt
# kein Modell, und genau deshalb ist sie hier die Ablesung und nicht die
# Diagnose-Route.
UEBERSICHT="${UEBERSICHT:-/apps/findling/admin/overview}"
# Der zweiwortige Begriff. Zwei Woerter, weil eine einwortige Zeile seit Plan
# 06.1-20 allein aus dem Wortindex beantwortet wird: sie haette nie eine
# semantische Haelfte, die fehlen koennte, und waere als Ablesung blind.
BEGRIFF="${BEGRIFF:-Bescheid Antrag}"
LIMIT="${LIMIT:-100}"
# Die Ruhezeit in Sekunden, also die Frist, nach der die Gewichte freigegeben
# sein sollen. 120 s statt der 900 s des Vorschlagswerts, auf Owner-Entscheid
# D-02 vom 19.09.2026: gemessen wird, was NACH Ablauf der Frist geschieht, und
# nicht, wie lang die Frist ist. Der Mechanismus ist derselbe, die Ersparnis
# sind Stunden Box-Zeit. Die Abweichung ist begruendungspflichtig, und die
# Begruendung steht unten als eigene Protokollzeile.
RUHEZEIT="${RUHEZEIT:-120}"
# Der Vorschlagswert aus backend/appinfo/info.xml, als Zahl und nicht als Wort.
# Er steht hier nur, damit die Abweichung eine Zahl hat, gegen die sie abweicht.
VORSCHLAGSWERT="${VORSCHLAGSWERT:-900}"
RUHEZEIT_GRUND="${RUHEZEIT_GRUND:-D-02 Owner-Entscheid 19.09.2026, derselbe Mechanismus und Stunden gesparte Box-Zeit}"
# Die Karenz oben auf die Ruhezeit. Die Freigabe faellt in einem Aufraeumlauf
# und nicht auf die Sekunde genau; ohne Karenz bekaeme die Messung einen Ast
# ohne Entladung gemeldet, der nur zu frueh gefragt wurde.
KARENZ="${KARENZ:-45}"
# Der Deckel des Nachwaermens in Sekunden. Ueberschreitung ist eine
# protokollierte Zeile und kein Abbruch: eine Zahl ueber dem Deckel ist ein
# Befund und keine Stoerung dieses Laufs.
NACHWAERM_DECKEL="${NACHWAERM_DECKEL:-180}"
# Wie lange nach einem Containerneustart auf die Bereitschaft gewartet wird.
# Gefragt wird die Admin-Seite und NICHT die Suchroute: eine Suche als
# Bereitschaftsprobe waere in den Auspraegungen 3 und 4 die erste Suche
# ueberhaupt und damit genau die Zahl, die gemessen werden soll.
BEREIT_DECKEL="${BEREIT_DECKEL:-180}"
# Der Pfad auf den Statusbeobachter im selben Verzeichnis. Dieses Skript ruft
# ihn nicht (siehe Abweichung 2 im Kopf), fuehrt ihn aber als Vorgabe, damit
# ein Boxplan, der ihn setzt, daran nicht scheitert und damit die Abweichung an
# einer Zeile haengt und nicht nur an einem Absatz. Sein Aufrufvertrag lautet
# "<ziel.jsonl> <intervall-s> <passwortdatei> <adresse> --user <konto>
# --password-env <name> --deckel 1", und die letzte Haelfte davon ist der Grund,
# warum PASSWORT_ENV oben den NAMEN der Variablen fuehrt und nicht ihren Wert:
# beide Werkzeuge nehmen das Passwort aus derselben Umgebungsvariablen und
# keines von beiden aus einem Argument.
BEOBACHTER="${BEOBACHTER:-$SKRIPTE/96d-statusbeobachter.py}"

mkdir -p "$OUT"
ZIEL="${ZIEL:-$OUT/95b-wiederaufwaermen-$AUSPRAEGUNG.txt}"
WORK=$(mktemp -d)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT

# Das Passwort des Kontos kommt aus der Umgebung und wird in eine Datei ohne
# abschliessenden Zeilenumbruch geschrieben; curl liest den Feldwert daraus.
# Ein Zeilenumbruch reiste als %0A mit und waere Teil des Passworts.
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

# jq liegt laut Abschnitt 3 des Runbooks auf der Box. Fehlt es doch, wird die
# Trefferzahl ueber ein Muster gezaehlt und die benutzte Quelle protokolliert:
# eine Zahl mit genannter Herkunft ist besser als ein Abbruch, fuer den dieser
# Schritt keinen Rueckgabewert hat.
if command -v jq >/dev/null 2>&1; then
    JQ=ja
    ZAEHLQUELLE=jq
else
    JQ=nein
    ZAEHLQUELLE=muster
fi

# Jede Zeile des Protokollblocks wird gedruckt UND mitgeschrieben, damit ein
# Bericht die Pflichtzeilen als Block zitieren kann, statt sie aus einer langen
# Rohdatei zusammenzusuchen.
protokoll() {
    printf '%s\n' "$*" >>"$WORK/protokollblock"
    printf '%s\n' "$*"
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

# Die Anmeldung, Schritt fuer Schritt wie 96d-statusbeobachter.py sie geht: das
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

# Genau ein Feld der Admin-Seite, und das Lesen dieser Seite laedt kein Modell.
# Ein Wort, das die Seite nicht hergibt, heisst unbekannt und nicht cold: ein
# geratener Zustand waere hier die halbe Aussage des ganzen Schrittes.
engine_zustand() {
    token=$(cat "$WORK/token" 2>/dev/null || true)
    if [ -z "${token:-}" ]; then
        printf 'unbekannt\n'
        return 0
    fi
    antwort=$(curl -sS -b "$JAR" -c "$JAR" -H 'Accept: application/json' \
        -H "requesttoken: $token" "$ADRESSE$UEBERSICHT" 2>/dev/null || true)
    zustand=$(printf '%s' "${antwort:-}" |
        sed -n 's/.*"engineState"[[:space:]]*:[[:space:]]*"\([A-Za-z_]*\)".*/\1/p' | head -1)
    [ -n "${zustand:-}" ] || zustand=unbekannt
    printf '%s\n' "$zustand"
}

treffer_in() {
    if [ "$JQ" = ja ]; then
        jq -r '.ocs.data.entries | length' "$1" 2>/dev/null || printf 'unklar\n'
    else
        grep -o '"resourceUrl"' "$1" 2>/dev/null | wc -l | tr -d ' '
    fi
}

# Eine Suche gegen die NUTZERROUTE, und nur gegen sie. Die drei Zahlen der
# Runde landen in Arbeitsdateien, damit sie auch unterhalb der Pipeline lesbar
# sind.
suche() {
    antwort=$(curl -sS -G -K "$CURLRC" \
        -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
        --data-urlencode "term=$1" --data-urlencode "limit=$LIMIT" \
        -o "$WORK/$2.json" -w '%{time_total} %{http_code}' \
        "$ADRESSE/ocs/v2.php/search/providers/findling/search" 2>/dev/null || printf '0 000')
    printf '%s\n' "$antwort" | awk '{printf "%d\n", ($1 * 1000) + 0.5}' >"$WORK/$2.ms"
    printf '%s\n' "$antwort" | awk '{print $2}' >"$WORK/$2.code"
    treffer_in "$WORK/$2.json" >"$WORK/$2.treffer"
}

lies() {
    cat "$WORK/$1" 2>/dev/null || printf 'unklar\n'
}

# Die semantische Seite, abgelesen an der Nutzerroute: die gemessene
# Trefferzahl gegen die Referenzzahl desselben Begriffs mit geladenen
# Gewichten. Ist eine der beiden keine Zahl, heisst die Antwort unbestimmt und
# nicht nein: ein Wort gegen eine Zahl zu halten waere eine Rechnung ohne
# Ergebnis.
semantische_seite() {
    gemessen=$1
    referenz=$(cat "$WORK/referenz-treffer" 2>/dev/null || true)
    case "${gemessen:-}" in
    '' | *[!0-9]*)
        printf 'unbestimmt\n'
        return 0
        ;;
    esac
    case "${referenz:-}" in
    '' | *[!0-9]*)
        printf 'unbestimmt\n'
        return 0
        ;;
    esac
    if [ "$referenz" -eq 0 ]; then
        printf 'unbestimmt\n'
    elif [ "$gemessen" -ge "$referenz" ]; then
        printf 'ja\n'
    else
        printf 'nein\n'
    fi
}

# Die Bereitschaft nach einem Neustart, gefragt an der Admin-Seite. Ein Wort,
# das nicht unbekannt ist, heisst: der Container antwortet wieder.
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

# Die Dauer, bis die Gewichte wieder drin sind, im Sekundentakt an derselben
# Admin-Seite abgelesen. Ueber dem Deckel ist eine Zeile und kein Abbruch.
nachwaermdauer() {
    start=$(date +%s)
    verstrichen=0
    dauer=ueber-deckel
    while [ "$verstrichen" -le "$NACHWAERM_DECKEL" ]; do
        if [ "$(engine_zustand)" = loaded ]; then
            dauer=$verstrichen
            break
        fi
        sleep 1
        verstrichen=$(($(date +%s) - start))
    done
    printf '%s\n' "$dauer"
}

# Der Wachposten vor einer Kaltmessung, in zwei voneinander unabhaengigen
# Fragen: der Zustand, den die Admin-Seite meldet, und eine Zeile der
# Diagnose-Route seit dem Containerstart. Der haeufigste Weg zu einem
# aufgewaermten Container ist genau dieser Aufruf.
wachposten() {
    erwartet=$1
    zustand=$(engine_zustand)
    protokoll "engine-zustand-vor-messung $zustand erwartet $erwartet"
    if [ "$zustand" = loaded ] && [ "$erwartet" != loaded ]; then
        printf 'aufgewaermt-grund engineState loaded statt %s\n' "$erwartet" >>"$WORK/aufgewaermt"
    fi
    seit=$(cat "$WORK/containerstart" 2>/dev/null || true)
    if [ -n "${seit:-}" ] && [ "$seit" != unlesbar ] &&
        sudo docker logs --since "$seit" "$CONTAINER" 2>&1 | grep -q '/diagnose'; then
        printf 'aufgewaermt-grund eine Zeile der Diagnose-Route seit dem Containerstart\n' >>"$WORK/aufgewaermt"
    fi
    if [ -f "$WORK/aufgewaermt" ]; then
        cat "$WORK/aufgewaermt"
    fi
}

{
    date -u +'wiederaufwaermen-start %Y-%m-%dT%H:%M:%SZ'
    printf 'auspraegung %s von 4, ruhezeit %s s, karenz %s s, nachwaerm-deckel %s s\n' \
        "$AUSPRAEGUNG" "$RUHEZEIT" "$KARENZ" "$NACHWAERM_DECKEL"
    printf 'begriff %s, deckel der antwortliste %s, trefferzaehlung-quelle %s\n' \
        "$BEGRIFF" "$LIMIT" "$ZAEHLQUELLE"
    printf 'beobachter-vorgabe %s, nicht gerufen (Abweichung 2 im Kopf)\n' "$BEOBACHTER"
    printf 'nachbar-container %s, arbeitskopie %s\n' "$NEXTCLOUD" "$REPO"

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

    # Eine Zahl am falschen Ast ist keine Haelfte des Vergleichs. Die
    # Auspraegungen 1 und 2 verlangen einen Wert groesser null, 3 und 4 genau 0.
    if [ "$SCHALTER" != unlesbar ]; then
        case "$SCHALTER" in
        *[!0-9]*)
            protokoll "entladeschalter-passt-zum-ast=nein, kein Zahlenwert"
            : >"$WORK/schalter-falscher-ast"
            ;;
        *)
            case "$AUSPRAEGUNG" in
            1 | 2)
                if [ "$SCHALTER" -gt 0 ]; then
                    protokoll "entladeschalter-passt-zum-ast=ja, Ast mit Entladung"
                else
                    protokoll "entladeschalter-passt-zum-ast=nein, der Ast mit Entladung verlangt einen Wert groesser null"
                    : >"$WORK/schalter-falscher-ast"
                fi
                ;;
            3 | 4)
                if [ "$SCHALTER" -eq 0 ]; then
                    protokoll "entladeschalter-passt-zum-ast=ja, Bezugsast ohne Entladung"
                else
                    protokoll "entladeschalter-passt-zum-ast=nein, der Bezugsast verlangt genau 0"
                    : >"$WORK/schalter-falscher-ast"
                fi
                ;;
            esac
            ;;
        esac
    fi

    START=$(sudo docker inspect --format '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || true)
    [ -n "${START:-}" ] || START=unlesbar
    printf '%s\n' "$START" >"$WORK/containerstart"
    protokoll "containerstart-ist=$START"
    if [ "$START" = unlesbar ]; then
        protokoll "abstand-zum-start-stunden=unlesbar"
    else
        # Ohne diese Zeile ist warm gegen kalt unbelegt (Abschnitt 6 des
        # Runbooks). Gerechnet wird mit einer Nachkommastelle, weil eine
        # zweite hier Scheingenauigkeit waere.
        STARTSEK=$(date -u -d "$START" +%s 2>/dev/null || true)
        if [ -n "${STARTSEK:-}" ]; then
            protokoll "abstand-zum-start-stunden=$(awk -v jetzt="$(date -u +%s)" -v start="$STARTSEK" \
                'BEGIN {printf "%.1f", (jetzt - start) / 3600}')"
        else
            protokoll "abstand-zum-start-stunden=nicht-rechenbar"
        fi
    fi

    # Erwartung 2147483648 in beiden Feldern. Eine Abweichung ist ein
    # protokollierter Befund und kein Abbruch dieses Skripts: der Abbruch
    # dafuer ist Rueckgabewert 39 und gehoert zu Block 13b.
    protokoll "speichergrenze-ist=$(cgroup_wert memory.max)/$(cgroup_wert memory.swap.max)"

    protokoll "ruhezeit-ist=$RUHEZEIT"
    if [ "$RUHEZEIT" -ne "$VORSCHLAGSWERT" ]; then
        protokoll "ruhezeit-abweichung-grund=$RUHEZEIT_GRUND"
    fi

    if [ -f "$WORK/schalter-unlesbar" ] || [ -f "$WORK/schalter-falscher-ast" ]; then
        echo "-- Die Pflichtzeile steht nicht oder sie steht am falschen Ast. Gemessen wird"
        echo "   nichts mehr: eine Zahl ohne ihre Stellung ist keine Haelfte des Vergleichs,"
        echo "   und der Lauf endet unterhalb der Pipeline. --"
        WEITER=nein
    else
        WEITER=ja
    fi

    if [ "$WEITER" = ja ]; then
        echo "=== 2. Der Ablauf dieser Auspraegung ==="
        echo "-- Containerneustart, weil kalt HERGESTELLT und nicht bewahrt wird --"
        sudo docker restart "$CONTAINER" >/dev/null
        START=$(sudo docker inspect --format '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || true)
        [ -n "${START:-}" ] || START=unlesbar
        printf '%s\n' "$START" >"$WORK/containerstart"
        protokoll "containerstart-nach-neustart=$START"
        if anmelden; then
            echo "anmeldung ok"
        else
            echo "anmeldung fehlgeschlagen, die Admin-Seite ist nicht lesbar und engineState bleibt unbekannt"
        fi
        bereit_warten || echo "-- der Container hat den Bereitschaftsdeckel gerissen, gemessen wird trotzdem --"

        case "$AUSPRAEGUNG" in
        1 | 2)
            echo "-- Eine Waermsuche, damit die Gewichte geladen sind. Ihre Trefferzahl ist die"
            echo "   Referenz, an der die semantische Seite spaeter abgelesen wird. --"
            suche "$BEGRIFF" waermsuche
            protokoll "waermsuche-ms=$(lies waermsuche.ms) code=$(lies waermsuche.code) treffer=$(lies waermsuche.treffer)"
            lies waermsuche.treffer >"$WORK/referenz-treffer"

            protokoll "rss-vor-ruhezeit=$(cgroup_wert memory.current)"
            echo "-- Die Ruhezeit und die Karenz. Die Freigabe faellt in einem Aufraeumlauf und"
            echo "   nicht auf die Sekunde genau. --"
            sleep "$((RUHEZEIT + KARENZ))"
            protokoll "rss-nach-ruhezeit=$(cgroup_wert memory.current)"

            ZUSTAND=$(engine_zustand)
            protokoll "engine-zustand-nach-ruhezeit=$ZUSTAND"
            if [ "$ZUSTAND" != unloaded ]; then
                echo "-- Kein unloaded nach Ruhezeit und Karenz: dieser Ast maesse das Nachwaermen"
                echo "   von etwas, das nie losgelassen wurde. Der Lauf endet unterhalb der"
                echo "   Pipeline; die beiden cgroup-Zahlen oben sind der zweite Anhaltspunkt. --"
                : >"$WORK/keine-entladung"
                WEITER=nein
            fi
            ;;
        3 | 4)
            protokoll "rss-vor-ruhezeit=entfaellt-ohne-entladung"
            protokoll "rss-nach-ruhezeit=entfaellt-ohne-entladung"
            echo "-- Kein Warten, keine Entladung, kein unloaded: dieser Ast ist der Bezugswert,"
            echo "   und seine Messsuche ist die erste Suche ueberhaupt. --"
            ;;
        esac
    fi

    if [ "$WEITER" = ja ]; then
        case "$AUSPRAEGUNG" in
        1 | 3)
            echo "=== 3. Der Seitencache des Wirts, geleert ==="
            echo "-- Auf dem WIRT und nicht im Container. Das Leeren verwirft auch den"
            echo "   mmap-Cache des Tantivy-Index: die Messung danach ist in BEIDEN Haelften"
            echo "   kalt, und genau das bekommt ein Nutzer nach einem Neustart der Box. --"
            sync
            echo 3 | sudo tee /proc/sys/vm/drop_caches
            free -h
            ;;
        2 | 4)
            echo "=== 3. Der Seitencache des Wirts bleibt warm ==="
            echo "-- Diese Auspraegung misst gegen den gewaermten Cache, das Leeren faellt aus --"
            free -h
            ;;
        esac

        case "$AUSPRAEGUNG" in
        1) wachposten unloaded ;;
        3) wachposten cold ;;
        *) protokoll "engine-zustand-vor-messung $(engine_zustand), warmer Ast ohne Wachposten" ;;
        esac

        if [ -f "$WORK/aufgewaermt" ]; then
            echo "-- Der Container war vor dieser Kaltmessung aufgewaermt. Die Messung wird nach"
            echo "   einer erneuten Ruhephase WIEDERHOLT und NIE herausgerechnet; der Lauf endet"
            echo "   unterhalb der Pipeline. --"
            WEITER=nein
        fi
    fi

    if [ "$WEITER" = ja ]; then
        echo "=== 4. Die Messsuche gegen die Nutzerroute ==="
        suche "$BEGRIFF" erste
        protokoll "erste-suche-ms=$(lies erste.ms)"
        protokoll "erste-suche-code=$(lies erste.code)"
        protokoll "treffer-erste-suche=$(lies erste.treffer)"

        echo "=== 5. Die Nachwaermdauer, im Sekundentakt an der Admin-Seite ==="
        DAUER=$(nachwaermdauer)
        protokoll "nachwaermdauer-s=$DAUER"
        if [ "$DAUER" = ueber-deckel ]; then
            protokoll "nachwaermdauer-ueber-deckel=$NACHWAERM_DECKEL"
        fi

        echo "=== 6. Die zweite Suche, mit den Gewichten wieder drin ==="
        suche "$BEGRIFF" zweite
        protokoll "zweite-suche-ms=$(lies zweite.ms)"
        protokoll "zweite-suche-code=$(lies zweite.code)"
        protokoll "treffer-zweite-suche=$(lies zweite.treffer)"

        echo "=== 7. Die semantische Seite, abgelesen an der Nutzerroute ==="
        case "$AUSPRAEGUNG" in
        1 | 2)
            echo "-- Referenz ist die Waermsuche vor der Ruhezeit --"
            ;;
        3 | 4)
            echo "-- Referenz ist die zweite Suche: dieser Ast hat keine Waermsuche, weil seine"
            echo "   Messsuche die erste Suche ueberhaupt sein muss --"
            lies zweite.treffer >"$WORK/referenz-treffer"
            ;;
        esac
        protokoll "referenz-treffer=$(lies referenz-treffer)"
        protokoll "semantische-seite-erste-suche=$(semantische_seite "$(lies erste.treffer)")"
        protokoll "semantische-seite-zweite-suche=$(semantische_seite "$(lies zweite.treffer)")"
    fi

    echo "=== Der Protokollblock, als Block zitierbar ==="
    cat "$WORK/protokollblock"

    date -u +'wiederaufwaermen-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Alles Folgende steht UNTERHALB der Pipeline, und nur dort. Der Rueckgabewert
# einer Pipeline, die in tee endet, gehoert zu tee; ein Abbruch innerhalb des
# Blocks verliesse nur die Subshell, und die Verweigerung waere eine Zeile in
# einer Rohdatei, die niemand liest. Gelesen wird deshalb aus den
# Arbeitsdateien unter WORK (Muster aus 97-cron-vorpruefung.sh).
if [ -f "$WORK/schalter-unlesbar" ]; then
    echo "95b-wiederaufwaermen: die Stellung des Entladeschalters war nicht ablesbar" >&2
    echo "95b-wiederaufwaermen: ein Lauf ohne protokollierte Stellung gilt als unvollstaendig (Abschnitt 6.4)" >&2
    exit 29
fi
if [ -f "$WORK/schalter-falscher-ast" ]; then
    echo "95b-wiederaufwaermen: die gelesene Stellung passt nicht zur Auspraegung $AUSPRAEGUNG" >&2
    echo "95b-wiederaufwaermen: 1 und 2 verlangen einen Wert groesser null, 3 und 4 genau 0" >&2
    echo "95b-wiederaufwaermen: eine Zahl am falschen Ast ist keine Haelfte des Vergleichs" >&2
    exit 29
fi
if [ -f "$WORK/aufgewaermt" ]; then
    echo "95b-wiederaufwaermen: der Container war vor dieser Kaltmessung aufgewaermt" >&2
    cat "$WORK/aufgewaermt" >&2
    echo "95b-wiederaufwaermen: die Messung wird nach einer erneuten Ruhephase wiederholt" >&2
    echo "95b-wiederaufwaermen: und NIE herausgerechnet (Abschnitt 7.2)" >&2
    exit 30
fi
if [ -f "$WORK/keine-entladung" ]; then
    echo "95b-wiederaufwaermen: der Ast mit eingeschaltetem Schalter hat keine Entladung erlebt" >&2
    echo "95b-wiederaufwaermen: kein unloaded nach $RUHEZEIT s Ruhezeit und $KARENZ s Karenz" >&2
    echo "95b-wiederaufwaermen: ohne Freigabe gibt es keine Wiederaufwaermzahl" >&2
    exit 31
fi

echo "95B-WIEDERAUFWAERMEN-FERTIG"
