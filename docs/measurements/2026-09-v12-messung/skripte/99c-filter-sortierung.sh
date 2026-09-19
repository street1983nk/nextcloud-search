#!/bin/sh
# Der Filter- und Sortierblock des v1.2-Laufs, Schritt 6b der Messreihenfolge.
#
# **Der Anlass ist ein Owner-Entscheid und keine Ableitung.** D-01 vom
# 19.09.2026 (15-CONTEXT.md): Filter und Sortierung bekommen einen EIGENEN
# Messblock auf der Box, Sortierung auf grossem Bestand und Blaettern unter
# Filter. Phase 13 hat beides gebaut und auf einer Entwicklungsinstanz
# geprueft; der Vollbestand von 52.111 Dokumenten existiert nur auf dieser
# einen Box und nur fuer die Dauer dieser Anfahrt. Die dritte Moeglichkeit,
# Stillschweigen, waere die schlechteste (15-RESEARCH.md, Open Question 3).
#
# **Dies ist eine ERSTMESSUNG und keine Vergleichszeile.** Fuer Sortierung und
# fuer Blaettern unter Filter gibt es keinen v1.1-Wert, gegen den sich etwas
# halten liesse: beides entstand erst in Phase 13, also nach jenem Lauf. Die
# Zahlen unten stehen deshalb fuer sich, und im Bericht duerfen sie nicht in
# eine Spalte neben Zahlen geraten, die eine Vorgaengerzeile haben.
#
# **Warum die Seitenroute und nicht die OCS-Route.** Nur die Seitenroute traegt
# types und sort. Die beiden OCS-Provider kennen beide Parameter nicht (Befund
# aus 13-12), also beantwortete eine Messung ueber sie die gestellte Anfrage
# ungefiltert und unsortiert und saehe dabei aus wie eine Filtermessung. Aus
# demselben Grund wird scripts/ops/search_load.py hier NICHT gerufen: es ist
# das geeichte Lastwerkzeug der Stufen aus Schritt 6, es fragt die OCS-Route,
# und ein Aufruf von hier aus maesse ungefiltert und sagte es nirgends. Es wird
# auch nicht angefasst; sein Name kommt in dieser Datei nur in diesem Kommentar
# vor.
#
# **Warum der Begriff zwei Woerter hat.** one_round() schaltet die
# Vektorhaelfte bei einem einzigen Wort ab, und genau daran sind Zeile B und
# Zeile C des Seitenbudget-Berichts gleich teuer geworden (Fallstrick 10, Kopf
# von 99-seitenroute.sh). Der hybride Fall existiert nur in der zweiwortigen
# Gestalt, also wird er in ihr gefahren.
#
# **Warum der Weiter-Link GEZOGEN und nicht GEBAUT wird.** Die Ergebnisseite
# haengt an jeden Blaetterschritt einen Cursor und einen Fingerabdruck; der
# Fingerabdruck laeuft ueber die rohen Adresswerte (PageController::index).
# Eine von Hand zusammengesetzte Adresse ohne fp wirft den Blaetternden auf
# Seite 1 zurueck, und zwar STILL: die Seite antwortet mit 200, sie ist
# schnell, und im Protokoll staende eine huebsche Zahl fuer einen Vorgang, der
# nie stattgefunden hat (13-08). Dieses Werkzeug setzt deshalb ausser Seite 1
# keine Adresse selbst zusammen. Es liest den Weiter-Link mit der Auszeichnung
# findling-pager__step--next aus der Antwort, entschaerft seine HTML-Entitaeten
# und ruft ihn auf.
#
# **Die drei Sortiernamen sind die des Erzeugnisses.** relevance, newest und
# oldest, die Schluessel von SORT_MODES in backend/src/findling/index/search.py.
# Ein vierter Name existiert nicht; ein unbekannter faellt dort still auf
# relevance zurueck, und eine Zeile mit einem erfundenen Namen maesse dann
# relevance unter falscher Ueberschrift. Ein Gate in
# backend/tests/test_measurement_scripts.py liest die drei Namen aus dem
# Quelltext des Pakets und haelt sie gegen die Vorgabe von SORTIERMODI unten,
# damit Werkzeug und Erzeugnis nicht auseinanderlaufen.
#
# **Was Block A misst und was er nicht messen kann.** Unter Sortierung gibt es
# keine Fusion: der Zweig ist rein lexikalisch und jeder Treffer traegt
# score = 0.0 (13-02). Die drei Zahlen sind deshalb untereinander vergleichbar,
# gegen relevance aber nur bedingt, weil relevance die Fusion beider Listen
# einschliesst und die beiden anderen sie gar nicht fahren. Die Zeile
# sortierung-ohne-vektorhaelfte sagt das in der Rohdatei, weil eine Rohdatei
# fuer sich gelesen wird.
#
# **Der Anmeldeweg steht in einer eigenen Zeile.** Basic Auth kostet auf der
# Vergleichsinstanz 0,318 s je Anfrage, die kein angemeldeter Nutzer zahlt
# (Befund M-03 der Phase 9), und zwei Berichte sind nur ueber denselben
# Anmeldeweg vergleichbar. Gemessen wird hier ausschliesslich der Sitzungsweg,
# um Box-Zeit zu sparen; der Verzicht auf die zweite Haelfte steht als Zeile in
# der Rohdatei und nicht nur in diesem Kopf.
#
# **Die Rueckgabewerte tragen je zwei Faelle, wie 32 und 33 es seit 15-04 tun.**
# Abschnitt 7.1 des Runbooks gibt 34 dem Bestand, der noch wuchs, und 35 der
# Stufe ohne Antwortzahlen oder mit einer doppelt ausgelieferten Datei-Kennung.
# Der Plan 15-05 gibt 34 dem Sortierlauf ohne Trefferzahl und 35 dem fehlenden
# Weiter-Link samt stillem Rueckfall auf Seite 1. Beide Lesarten sind
# umgesetzt, keine faellt weg: eine einmal vergebene Zahl wird nicht
# umgehaengt, damit Rohdaten frueherer Laeufe lesbar bleiben (Entscheid 15-02).
#
# **Die Zeilen, die dieses Werkzeug schreibt**, ausgeschrieben statt aus den
# Schleifen unten zusammengedacht. Ein Bericht greift nach Namen, und ein Name,
# der erst zur Laufzeit entsteht, ist in der Datei nicht zu finden:
#
#   entladeschalter-ist, containerstart-ist, speichergrenze-ist,
#   filter-typgruppe-ist, anmeldeweg-ist, sortiermodi-ist, bestand-steht
#
#   sortierung-relevance-ms-median, sortierung-relevance-ms-p95,
#   sortierung-relevance-treffer
#   sortierung-newest-ms-median, sortierung-newest-ms-p95,
#   sortierung-newest-treffer
#   sortierung-oldest-ms-median, sortierung-oldest-ms-p95,
#   sortierung-oldest-treffer
#   sortierung-ohne-vektorhaelfte
#
#   blaettern-seite-1-ms, blaettern-seite-1-treffer,
#   blaettern-seite-1-gemeldete-seitenzahl, und dieselben drei fuer jede
#   weitere geblaetterte Seite
#
# Die Exit-Codes setzen den Katalog dieses Laufverzeichnisses fort:
#
#   2  das Werkzeug wurde mit einem Argument gerufen, das es nicht gibt
#   29 die Stellung des Entladeschalters war nicht ablesbar; ein Lauf ohne
#      protokollierte Stellung gilt als unvollstaendig (Abschnitt 6.4)
#   34 der Bestand wuchs noch, oder ein Sortierlauf hat keine Trefferzahl
#      hergegeben: eine Zeitnahme auf einer Fehlerseite ist keine Messung
#   35 eine Stufe lieferte keine Antwortzahlen, zwei aufeinander folgende
#      Seiten trugen dieselbe Datei-Kennung, es gab keinen Weiter-Link obwohl
#      noch Seiten erwartet wurden, oder eine geholte Seite meldete eine andere
#      Seitenzahl als die geholte: der Cursor war verworfen
set -eu

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: 99c-filter-sortierung.sh

Ohne Argument. Dieses Werkzeug faehrt den Filter- und Sortierblock des
Owner-Entscheids D-01 in EINEM Zug: Block A misst die drei Sortiermodi auf dem
Vollbestand, Block B blaettert unter einem Typfilter durch mehrere Seiten.

Einen Zuschnitt je Block gibt es bewusst nicht. Beide Bloecke messen denselben
Bestand in derselben Aufwaermung; ueber zwei Laeufe gespannt waeren die Zahlen
zweier Bestaende unter einer Ueberschrift.

Stellschrauben stehen als Umgebungsvariablen im Kopf der Datei, darunter
BEGRIFF, FILTER_GRUPPE, SORTIERMODI, SEITEN und RUNDEN. Das Passwort reist
ueber den NAMEN einer Umgebungsvariablen und nie ueber ein Argument.
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
# Der Container der ExApp traegt den Schalter und die cgroup, der der Nextcloud
# fuehrt occ.
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
ADRESSE="${ADRESSE:-https://loadtest.infranode.dev}"
# Das Lastkonto der Box. Gemessen wird als Nutzer und nicht als Admin: die
# Seitenroute filtert am Ende ueber den Ordner des angemeldeten Kontos.
BENUTZER="${BENUTZER:-lasttest}"
# Der NAME der Umgebungsvariablen, nicht ihr Wert. Ein Wert in einem Argument
# stuende in der Prozessliste der Box und in jedem Protokoll, das den Befehl
# aufzeichnet (T-10-27, T-15-06).
PASSWORT_ENV="${PASSWORT_ENV:-FINDLING_LOAD_PASSWORD}"
# Der zweiwortige Begriff. Das Pluszeichen ist das kodierte Leerzeichen, damit
# die Adresse unten ein Wort fuer die Shell bleibt. Warum zwei Woerter, steht
# im Kopf.
BEGRIFF="${BEGRIFF:-Bescheid+Antrag}"
# Die Typgruppe des Filterblocks, ein Schluessel aus TYPE_GROUPS in
# backend/src/findling/query/rewrite.py. Der Lastkorpus traegt pdf, docx, xlsx,
# odt und Klartext, also greifen pdf und documents auf ihm.
FILTER_GRUPPE="${FILTER_GRUPPE:-pdf}"
# Die drei Sortiernamen, in der Reihenfolge von SORT_MODES. Diese Zeile ist die
# einzige Stelle, an der sie stehen, und das Gate haelt sie gegen den Quelltext
# des Pakets.
SORTIERMODI="${SORTIERMODI:-relevance newest oldest}"
# Wie viele Seiten Block B blaettert, Seite 1 eingerechnet.
SEITEN="${SEITEN:-3}"
# Wiederholungen je Zeile. Gemeldet werden Median und p95 nach der Rangregel
# des Seitenbudget-Berichts. Aufwaermanfragen gibt es nicht: Schritt 6b steht
# hinter den Laststufen, der Container ist dort aufgewaermt, und zusaetzliche
# Anfragen je Zeile waeren gekaufte Box-Zeit ohne Aussage.
RUNDEN="${RUNDEN:-5}"

mkdir -p "$OUT"
ZIEL="${ZIEL:-$OUT/99c-filter-sortierung.txt}"
WORK=$(mktemp -d)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT

# Das Passwort kommt aus der Umgebung in eine Datei ohne abschliessenden
# Zeilenumbruch; curl liest den Feldwert daraus. Ein Zeilenumbruch reiste als
# %0A mit und waere Teil des Passworts.
PWFELD="$WORK/pwfeld"
: >"$PWFELD"
chmod 600 "$PWFELD"
eval "printf '%s' \"\${$PASSWORT_ENV:-}\"" >"$PWFELD"
JAR="$WORK/cookies.txt"

occ() {
    sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
}

# Der Arbeitsvorrat aus EINEM Aufruf der Statusausgabe. Muster aus
# 93-nullstand.sh, unveraendert uebernommen.
vorrat_von() {
    awk '/^Work stock/ {found = 1; next}
         found && /^  (scheduled|handed to the worker)/ {sum += $NF}
         END {print sum + 0}' "$1"
}

# Die cgroup des Containers, nach dem Muster von 93-nullstand.sh. Die Kennung
# wird jedes Mal neu gelesen, damit kein stehengebliebener Pfad die cgroup von
# gestern liest.
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

# Jede Zeile des Protokollblocks wird gedruckt UND mitgeschrieben, damit ein
# Bericht die Pflichtzeilen als Block zitieren kann, statt sie aus einer langen
# Rohdatei zusammenzusuchen.
protokoll() {
    printf '%s\n' "$*" >>"$WORK/protokollblock"
    printf '%s\n' "$*"
}

# Die Anmeldung, Schritt fuer Schritt wie scripts/dev/probe_page_login.sh sie
# geht: das Formular mit dem Glas, das Token aus dem Formular, der POST mit
# Token UND Origin. Der Origin-Kopf ist keine Zierde: LoginController weist
# eine Anmeldung, deren Herkunft keine vertraute Domain ist, mit derselben
# Umleitung ab, die ein falsches Passwort erzeugt.
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
    return 0
}

# Ein Aufruf der Seitenroute mit der Sitzung. Schreibt die Antwort in eine
# Datei und gibt "sekunden code" zurueck. Ein fehlgeschlagener Aufruf liefert
# "0 000" und faellt weiter unten als fehlende Antwortzahl auf.
aufrufen() {
    curl -sS -b "$JAR" -c "$JAR" -o "$1" -w '%{time_total} %{http_code}' \
        "$2" 2>/dev/null || printf '0 000'
}

# Die Trefferzeilen einer Antwort. Gezaehlt wird die Auszeichnung der Zeile und
# nicht die Zeile selbst: die Datei-Kennung ist der Vertrag, den auch
# scripts/ci/parity_diff.py liest, und zwei Treffer koennten sich eine Zeile
# teilen.
treffer_von() {
    grep -o 'id="findling-hit-[0-9]*"' "$1" 2>/dev/null | wc -l | tr -d ' '
}

# Die Datei-Kennungen einer Antwort, eine je Zeile. Sie sind der Beleg dafuer,
# dass zwei aufeinander folgende Seiten wirklich zwei Seiten waren.
kennungen_von() {
    grep -o 'id="findling-hit-[0-9]*"' "$1" 2>/dev/null | sed 's/[^0-9]//g' || true
}

# Die Seitenzahl, die die Seite SELBST meldet, aus der Marke des Blaetterns.
# Gelesen werden die Ziffern des Markentextes und kein Adressparameter: die
# Uebersetzung dreht das Wort davor um, die Zahl bleibt eine Zahl. Genau diese
# Ablesung faengt den stillen Rueckfall, denn eine zurueckgeworfene Antwort
# meldet sich als die erste Seite.
gemeldete_seite_von() {
    zahl=$(grep -o 'findling-pager__mark">[^<]*<' "$1" 2>/dev/null |
        head -1 | sed 's/[^0-9]//g')
    [ -n "${zahl:-}" ] || zahl=unlesbar
    printf '%s\n' "$zahl"
}

# HTML-Entitaeten entschaerfen. Die Vorlage druckt jeden Wert escaped; ein href
# aus ihr traegt also &amp; statt & und waere als Adresse ein einziger langer
# Parameter. Das kaufmaennische Und wird zuletzt ersetzt, sonst entstuenden aus
# den anderen Ersetzungen neue Entitaeten.
entschaerfen() {
    sed -e 's/&#0*39;/'\''/g' -e 's/&quot;/"/g' -e 's/&lt;/</g' -e 's/&gt;/>/g' \
        -e 's/&amp;/\&/g'
}

# Der Weiter-Link aus der Antwort, absolut gemacht. Er ist die EINZIGE Quelle
# fuer jede Adresse ausser der ersten: er traegt den Cursor und den
# Fingerabdruck, und eine selbstgebaute Adresse ohne beides maesse den
# Rueckfall statt des Blaetterns.
weiter_link_von() {
    roh=$(grep -o 'findling-pager__step--next" href="[^"]*"' "$1" 2>/dev/null |
        head -1 | sed 's/.*href="//; s/"$//' | entschaerfen)
    [ -n "${roh:-}" ] || return 1
    case "$roh" in
    http://* | https://*) printf '%s\n' "$roh" ;;
    /*) printf '%s%s\n' "$ADRESSE" "$roh" ;;
    *) printf '%s/%s\n' "$ADRESSE" "$roh" ;;
    esac
    return 0
}

# Der Wert an Rang ceil(anteil * n) der sortierten Reihe, OHNE Interpolation.
# Die Regel aus Abschnitt 2 des Seitenbudget-Berichts, ausgeschrieben statt aus
# einer Bibliothek genommen: zwei Berichte sind nur unter derselben Regel
# vergleichbar, und eine interpolierende Funktion erzeugte still eine dritte.
rang_von() {
    datei=$1
    anteil=$2
    n=$(grep -c . "$datei" 2>/dev/null || true)
    [ -n "${n:-}" ] || n=0
    if [ "$n" -lt 1 ]; then
        printf 'unlesbar\n'
        return 0
    fi
    stelle=$(awk -v n="$n" -v a="$anteil" 'BEGIN {
        s = int(a * n)
        if (s < a * n) { s = s + 1 }
        if (s < 1) { s = 1 }
        if (s > n) { s = n }
        print s
    }')
    wert=$(sort -n "$datei" | sed -n "${stelle}p")
    [ -n "${wert:-}" ] || wert=unlesbar
    printf '%s\n' "$wert"
}

# Sekunden in Millisekunden, mit einer Nachkommastelle. Ein Wort bleibt ein
# Wort: eine Null liesse sich als gemessene Null lesen, und das waere genau die
# erfundene Zahl, gegen die dieser Block geschrieben ist.
ms_von() {
    case "${1:-}" in
    '' | unlesbar)
        printf 'unbestimmt\n'
        return 0
        ;;
    esac
    awk -v s="$1" 'BEGIN { printf "%.1f\n", s * 1000 }'
}

# Eine Zeile: RUNDEN Aufrufe derselben Adresse, eine Zeit je Zeile in Sekunden,
# die Statuscodes daneben. Eine Folge schneller Umleitungen saehe sonst aus wie
# eine schnelle Seite.
zeile_fahren() {
    name=$1
    adresse=$2
    : >"$WORK/$name.zeiten"
    : >"$WORK/$name.codes"
    lauf=0
    while [ "$lauf" -lt "$RUNDEN" ]; do
        lauf=$((lauf + 1))
        antwort=$(aufrufen "$WORK/$name.html" "$adresse")
        printf '%s\n' "$antwort" | awk '{print $1}' >>"$WORK/$name.zeiten"
        printf '%s\n' "$antwort" | awk '{print $2}' >>"$WORK/$name.codes"
    done
}

{
    date -u +'filter-sortierung-start %Y-%m-%dT%H:%M:%SZ'
    printf 'messblock=Filter und Sortierung auf dem Vollbestand (D-01, Owner-Entscheid 19.09.2026)\n'
    printf 'erstmessung=ja, es gibt keinen v1.1-Wert fuer Sortierung oder Blaettern unter Filter\n'
    printf 'route=seitenroute, weil nur sie types und sort traegt (Befund 13-12)\n'
    printf 'begriff %s (zwei Woerter, siehe Kopf), runden je zeile %s, seiten %s\n' \
        "$BEGRIFF" "$RUNDEN" "$SEITEN"
    echo "rangregel: Wert an Rang ceil(0,50 * n) bzw. ceil(0,95 * n) der sortierten"
    echo "Reihe, ohne Interpolation, wie Abschnitt 2 des Seitenbudget-Berichts"
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

    # Dieser Block laeuft auf 0. Eine andere Stellung ist kein Abbruch: die
    # beiden Sortierzweige sind ohnehin rein lexikalisch. Sie ist aber ein
    # Befund, der neben den Zahlen stehen muss, denn unter einer
    # eingeschalteten Freigabe kann die relevance-Zeile eine Nachladung
    # enthalten, die die beiden anderen nie zahlen.
    if [ "$SCHALTER" = 0 ]; then
        protokoll "entladeschalter-passt-zum-block=ja, dieser Block laeuft auf 0"
    elif [ "$SCHALTER" != unlesbar ]; then
        protokoll "entladeschalter-passt-zum-block=nein, dieser Block laeuft auf 0 und der Schalter steht auf $SCHALTER"
    fi

    START=$(sudo docker inspect --format '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || true)
    [ -n "${START:-}" ] || START=unlesbar
    protokoll "containerstart-ist=$START"

    # Erwartung 2147483648 in beiden Feldern. Eine Abweichung ist ein
    # protokollierter Befund und kein Abbruch dieses Skripts: der Abbruch dafuer
    # ist Rueckgabewert 39 und gehoert zu Block 13b.
    protokoll "speichergrenze-ist=$(cgroup_wert memory.max)/$(cgroup_wert memory.swap.max)"

    protokoll "filter-typgruppe-ist=$FILTER_GRUPPE"
    protokoll "anmeldeweg-ist=sitzung"
    protokoll "anmeldeweg-zweite-haelfte=verzichtet, um Box-Zeit zu sparen; Basic Auth kostet auf der Vergleichsinstanz 0,318 s je Anfrage (Befund M-03), die kein angemeldeter Nutzer zahlt, und zwei Berichte sind nur ueber denselben Anmeldeweg vergleichbar"
    protokoll "sortiermodi-ist=$SORTIERMODI"

    if [ -f "$WORK/schalter-unlesbar" ]; then
        echo "-- Die Pflichtzeile steht nicht. Gemessen wird nichts mehr, und der Lauf endet"
        echo "   unterhalb der Pipeline. --"
        WEITER=nein
    else
        WEITER=ja
    fi

    if [ "$WEITER" = ja ]; then
        echo "=== 2. Steht der Bestand? ==="
        echo "-- Die Endzahl des Volllaufs muss stehen. Gegen einen wachsenden Bestand"
        echo "   gefahren, maesse die Sortierung zwei verschiedene Bestaende unter einer"
        echo "   Zahl (Abschnitt 7.1, Rueckgabewert 34). --"
        occ findling:index >"$WORK/status.txt" 2>&1 || true
        VORRAT=$(vorrat_von "$WORK/status.txt")
        protokoll "bestand-arbeitsvorrat=$VORRAT"
        if [ "$VORRAT" != 0 ]; then
            protokoll "bestand-steht=nein"
            : >"$WORK/bestand-waechst"
            WEITER=nein
        else
            protokoll "bestand-steht=ja"
        fi
    fi

    if [ "$WEITER" = ja ]; then
        echo "=== 3. Die Sitzung ==="
        if anmelden; then
            echo "anmeldung ok, konto $BENUTZER, weg sitzung"
        else
            echo "anmeldung fehlgeschlagen; jede Zeile darunter traegt dann keine Trefferzahl"
        fi
    fi

    if [ "$WEITER" = ja ]; then
        echo "=== 4. Block A: Sortierung auf grossem Bestand ==="
        echo "-- Dieselbe Anfrage dreimal, je ueber die Seitenroute mit Sitzung. Unter"
        echo "   Sortierung gibt es keine Fusion: der Zweig ist rein lexikalisch und jeder"
        echo "   Treffer traegt score = 0.0 (13-02). --"
        for modus in $SORTIERMODI; do
            adresse="$ADRESSE/apps/findling/?query=$BEGRIFF&sort=$modus"
            printf -- '-- Modus %s, Adresse %s --\n' "$modus" "$adresse"
            zeile_fahren "sortierung-$modus" "$adresse"
            sort "$WORK/sortierung-$modus.codes" | uniq -c
            median=$(rang_von "$WORK/sortierung-$modus.zeiten" 0.50)
            p95=$(rang_von "$WORK/sortierung-$modus.zeiten" 0.95)
            protokoll "sortierung-$modus-ms-median=$(ms_von "$median")"
            protokoll "sortierung-$modus-ms-p95=$(ms_von "$p95")"
            letzter_code=$(tail -1 "$WORK/sortierung-$modus.codes" 2>/dev/null || true)
            treffer=$(treffer_von "$WORK/sortierung-$modus.html")
            if [ "${letzter_code:-000}" != 200 ] || [ "$treffer" -lt 1 ]; then
                protokoll "sortierung-$modus-treffer=keine (http ${letzter_code:-000})"
                echo "-- Dieser Modus hat keine Trefferzahl hergegeben: Seite ohne Trefferblock,"
                echo "   Anmeldung verloren oder HTTP ungleich 200. Eine Zeitnahme auf einer"
                echo "   Fehlerseite ist keine Messung. Der Lauf endet unterhalb der Pipeline. --"
                : >"$WORK/sortierung-ohne-treffer"
            else
                protokoll "sortierung-$modus-treffer=$treffer"
            fi
        done
        protokoll "sortierung-ohne-vektorhaelfte=ja"
        echo "-- Die Zeile darueber im Klartext: unter newest und oldest gibt es keine"
        echo "   Fusion, der Zweig ist rein lexikalisch und jeder Treffer traegt"
        echo "   score = 0.0. Die drei Zahlen sind untereinander vergleichbar; gegen"
        echo "   relevance nur bedingt, weil relevance die Fusion beider Listen"
        echo "   einschliesst und die beiden anderen sie gar nicht fahren. --"
        if [ -f "$WORK/sortierung-ohne-treffer" ]; then
            WEITER=nein
        fi
    fi

    if [ "$WEITER" = ja ]; then
        echo "=== 5. Block B: Blaettern unter Filter ==="
        echo "-- Seite 1 wird gebaut, jede weitere wird GEZOGEN. Der Weiter-Link traegt"
        echo "   Cursor und Fingerabdruck; eine selbstgebaute Adresse ohne fp maesse den"
        echo "   stillen Rueckfall auf Seite 1 und nicht das Blaettern (13-08). --"
        adresse="$ADRESSE/apps/findling/?query=$BEGRIFF&types=$FILTER_GRUPPE&sort=relevance"
        seite=1
        : >"$WORK/kennungen-vorher"
        while [ "$seite" -le "$SEITEN" ]; do
            printf -- '-- Seite %s, Adresse %s --\n' "$seite" "$adresse"
            zeile_fahren "blaettern-$seite" "$adresse"
            sort "$WORK/blaettern-$seite.codes" | uniq -c
            median=$(rang_von "$WORK/blaettern-$seite.zeiten" 0.50)
            protokoll "blaettern-seite-$seite-ms=$(ms_von "$median")"
            treffer=$(treffer_von "$WORK/blaettern-$seite.html")
            gemeldet=$(gemeldete_seite_von "$WORK/blaettern-$seite.html")
            protokoll "blaettern-seite-$seite-treffer=$treffer"
            protokoll "blaettern-seite-$seite-gemeldete-seitenzahl=$gemeldet"

            if [ "$treffer" -lt 1 ]; then
                echo "-- Diese Stufe hat keine Antwortzahlen geliefert. Der Lauf endet"
                echo "   unterhalb der Pipeline. --"
                : >"$WORK/stufe-ohne-zahlen"
                break
            fi

            # Der stille Rueckfall. Eine Antwort, die sich als erste Seite
            # meldet, obwohl eine spaetere geholt wurde, hat den Cursor
            # verworfen: sie antwortet mit 200, sie ist schnell, und im
            # Protokoll staende sonst eine huebsche Zahl fuer einen Vorgang,
            # der nie stattgefunden hat.
            if [ "$seite" -gt 1 ] && [ "$gemeldet" != "$seite" ]; then
                echo "-- Die geholte Antwort meldet sich als Seite $gemeldet, geholt wurde die"
                echo "   Seite $seite ueber ihren eigenen Weiter-Link. Der Cursor ist verworfen"
                echo "   worden, und genau dieser Rueckfall ist still. --"
                : >"$WORK/cursor-verworfen"
                break
            fi

            kennungen_von "$WORK/blaettern-$seite.html" | sort >"$WORK/kennungen-$seite"
            doppelt=$(comm -12 "$WORK/kennungen-vorher" "$WORK/kennungen-$seite" | head -3 | tr '\n' ' ')
            protokoll "blaettern-seite-$seite-kennungen-doppelt=${doppelt:-keine}"
            if [ -n "${doppelt:-}" ]; then
                echo "-- Zwei aufeinander folgende Seiten tragen dieselbe Datei-Kennung. Das ist"
                echo "   ein Befund ueber die Seitenroute und keine Sortierzahl (Abschnitt 7.1). --"
                : >"$WORK/kennung-doppelt"
                break
            fi
            cp "$WORK/kennungen-$seite" "$WORK/kennungen-vorher"

            if [ "$seite" -eq "$SEITEN" ]; then
                break
            fi

            if adresse=$(weiter_link_von "$WORK/blaettern-$seite.html"); then
                protokoll "blaettern-weiter-link-nach-seite-$seite=gezogen"
            else
                echo "-- Auf dieser Seite steht kein Weiter-Link, obwohl noch Seiten erwartet"
                echo "   werden. Hier wird keine Adresse ersatzweise gebaut: eine gebaute"
                echo "   Adresse maesse den Rueckfall. --"
                protokoll "blaettern-weiter-link-nach-seite-$seite=fehlt"
                : >"$WORK/kein-weiter-link"
                break
            fi
            seite=$((seite + 1))
        done
    fi

    echo "=== Der Protokollblock, als Block zitierbar ==="
    cat "$WORK/protokollblock"

    date -u +'filter-sortierung-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Alles Folgende steht UNTERHALB der Pipeline, und nur dort. Der Rueckgabewert
# einer Pipeline, die in tee endet, gehoert zu tee; ein Abbruch innerhalb des
# Blocks verliesse nur die Subshell, und die Verweigerung waere eine Zeile in
# einer Rohdatei, die niemand liest. Gelesen wird deshalb aus den Arbeitsdateien
# unter WORK (Muster aus 97-cron-vorpruefung.sh). Die Reihenfolge der Pruefungen
# ist die Reihenfolge des Ablaufs, damit der erste Befund auch der erste ist,
# der gefallen ist.
if [ -f "$WORK/schalter-unlesbar" ]; then
    echo "99c-filter-sortierung: die Stellung des Entladeschalters war nicht ablesbar" >&2
    echo "99c-filter-sortierung: ein Lauf ohne protokollierte Stellung gilt als unvollstaendig" >&2
    echo "99c-filter-sortierung: das ist Abschnitt 6.4 des Runbooks und keine Formalie" >&2
    exit 29
fi
if [ -f "$WORK/bestand-waechst" ]; then
    echo "99c-filter-sortierung: der Arbeitsvorrat war nicht leer, der Bestand wuchs noch" >&2
    echo "99c-filter-sortierung: die Endzahl des Volllaufs muss stehen, sonst misst die" >&2
    echo "99c-filter-sortierung: Sortierung zwei verschiedene Bestaende unter einer Zahl" >&2
    exit 34
fi
if [ -f "$WORK/sortierung-ohne-treffer" ]; then
    echo "99c-filter-sortierung: ein Sortierlauf hat keine Trefferzahl hergegeben" >&2
    echo "99c-filter-sortierung: Seite ohne Trefferblock, Anmeldung verloren oder HTTP ungleich 200" >&2
    echo "99c-filter-sortierung: eine Zeitnahme auf einer Fehlerseite ist keine Messung" >&2
    exit 34
fi
if [ -f "$WORK/stufe-ohne-zahlen" ]; then
    echo "99c-filter-sortierung: eine Stufe des Blaetterns lieferte keine Antwortzahlen" >&2
    echo "99c-filter-sortierung: eine Stufe ohne Zahlen ist unbrauchbar und wird nicht geschaetzt" >&2
    exit 35
fi
if [ -f "$WORK/cursor-verworfen" ]; then
    echo "99c-filter-sortierung: eine geholte Seite hat eine andere Seitenzahl gemeldet" >&2
    echo "99c-filter-sortierung: der Cursor ist verworfen worden, und dieser Rueckfall ist still" >&2
    echo "99c-filter-sortierung: ohne diesen Abbruch stuende er als schnelle Zahl im Protokoll" >&2
    exit 35
fi
if [ -f "$WORK/kennung-doppelt" ]; then
    echo "99c-filter-sortierung: zwei aufeinander folgende Seiten trugen dieselbe Datei-Kennung" >&2
    echo "99c-filter-sortierung: ein Blaettern, das eine Kennung zweimal ausliefert, ist ein" >&2
    echo "99c-filter-sortierung: Befund ueber die Seitenroute und keine Sortierzahl" >&2
    exit 35
fi
if [ -f "$WORK/kein-weiter-link" ]; then
    echo "99c-filter-sortierung: auf einer Seite stand kein Weiter-Link, obwohl noch Seiten" >&2
    echo "99c-filter-sortierung: erwartet wurden. Ersatzweise gebaut wird hier keine Adresse:" >&2
    echo "99c-filter-sortierung: eine gebaute Adresse ohne fp maesse den Rueckfall auf Seite 1" >&2
    exit 35
fi

echo "99C-FILTER-SORTIERUNG-FERTIG"
