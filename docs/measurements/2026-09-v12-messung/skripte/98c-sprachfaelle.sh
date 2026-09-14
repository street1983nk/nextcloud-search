#!/bin/sh
# Die zehn deutschen Sprachfaelle auf der Box, Nachfolgefassung fuer DI-10-02
# und DI-11-01.
#
# **Wo die gefahrene Fassung liegt, und dass sie liegen bleibt.** Der Lauf vom
# 10.09.2026 (Plan 11-03, Werkzeugfixe) hat
# docs/measurements/2026-09-werkzeugfixe/skripte/98b-sprachfaelle.sh gefahren.
# Jene Datei ist Teil des Belegs jenes Laufs, ihre Rohdaten liegen unter
# docs/measurements/2026-09-werkzeugfixe/rohdaten/, und sie bleibt byteweise
# identisch: ein Messskript, das nachtraeglich bearbeitet wird, macht jede Zahl
# neben sich unbelegt. Der Waechter
# test_the_successor_language_case_script_stays_byte_identical in
# backend/tests/test_measurement_scripts.py wird beim ersten geaenderten Byte
# drueben rot. DIESE Datei ist die Nachfolge, in einem eigenen Laufverzeichnis,
# und sie aendert genau eine Sache: die Messgroesse hinter der
# Messbarkeitspruefung wechselt von der Trefferzahl der gedeckelten OCS-Route
# auf den Rang der eigenen Datei in den beiden Ranglisten, gemessen im Prozess
# des Containers. Alles andere, vom Konto ueber den Korpus bis zu den zehn
# Zusicherungen, bleibt wie in 98b.
#
# **Warum die alte Messgroesse nicht messen konnte, wonach sie gefragt wurde.**
# Die Vorpruefung von 98b hat jeden Begriff ueber die OCS-Route gefragt, einmal
# mit der Seite der Faelle und einmal mit einer ausdruecklichen Tiefe von 64.
# Die Gegenprobe 72-fremdbestand.py vom 10.09.2026 hat dieselbe Route mit vier
# Tiefen und mit Begriffen gefragt, die in keinem der zehn Faelle vorkommen, und
# fuer jeden Begriff und jede Tiefe dieselbe Zahl 26 gemessen. 26 ist ein Deckel
# der Antwort und nicht der Bestand dahinter. Eine Zahl, die bei 26 stehen
# bleibt, erreicht die Schwelle 64 nie; das dreiwertige Urteil faellt damit auf
# zweiwertig zurueck, und die vier Faelle, die DI-10-02 beschreibt, bleiben rot
# statt nicht messbar zu heissen.
#
# **Was diese Fassung stattdessen misst.** Die Sonde 73-bestand-sonde.py laeuft
# IM Container und fragt keine Route: sie liest den Index ueber ranked_sides,
# also ueber dieselbe Funktion, mit der eine Suche dieses Containers ihre beiden
# Haelften baut. Je Begriff liefert sie den ungedeckelten Bestand, die Belegung
# beider Ranglisten und, sobald die eigenen Datei-Kennungen uebergeben sind, den
# Rang der eigenen Datei in jeder der beiden Listen. Keine Trefferzahl ueberquert
# dabei eine Prozessgrenze; das Zaehl-Orakel aus T-02-93 entsteht gar nicht
# erst.
#
# **Warum die Schwelle 64 heisst und warum der Rang sie erreichen kann.**
# php/lib/Search/Provider.php deckelt mit MAX_RECHECKS_ABSOLUTE = 64 die Zahl der
# Kandidaten, die eine einzelne Suche noch einmal in die Hand nimmt. Das ist das
# Fenster, in dem die eigene Datei landen muss. Ein Rang ist eine Position und
# kein gedeckelter Zaehler, er kann also jeden Wert annehmen, den die Liste
# hergibt, und 64 ist fuer ihn erreichbar. Die Begruendung, warum der Rang und
# nicht der Bestand das Urteil traegt, steht ueber der Funktion messbar weiter
# unten.
#
# **Die einzige strukturelle Aenderung gegenueber 98b: ein Abschnitt 3b.** Der
# Bestand ist vor dem Hochladen messbar, der Rang der eigenen Datei erst danach.
# Abschnitt 0 faehrt die Sonde deshalb ohne Kennungen und schreibt den Bestand
# hin, Abschnitt 3b faehrt sie nach Upload und Indexierung ein zweites Mal, mit
# den Kennungen aus dem Antwortkopf der Uploads, und liest die beiden Raenge.
#
# Alles, was das Original verspricht, bleibt versprochen: das eigene Konto,
# dessen Heimat nichts als testdata/corpus haelt, die 39 Dateien ueber WebDAV,
# weil das der Weg eines Nutzers ist, der fertige OCR-Durchlauf vor jedem
# Urteil, und alle zehn Faelle auch nach einem roten. FRIST, RUNDEN und
# RUNDENFRIST behalten ihre Vorgaben, weil eine geaenderte Vorgabe die
# Vergleichbarkeit mit dem Original kosten wuerde.
#
# Passwoerter werden nie zu Argumenten (T-10-27): occ liest OC_PASS aus der
# Umgebung, die curl-Konfigurationsdatei hat Modus 600, und die eigenen
# Datei-Kennungen reisen ebenfalls ausschliesslich in der Umgebung (DATEI_IDS).
#
# Die Exit-Codes: 15 der Upload hat nicht 39 Dateien geliefert, 16 der
# Arbeitsvorrat war am Rundendeckel noch nicht leer, 17 mindestens ein MESSBARER
# Fall war rot, 18 jq liegt nicht auf dieser Box, 19 die Vorpruefung des
# Fremdbestands konnte nicht gefahren werden, 22 CI_LAUF traegt keine Laufnummer,
# 23 kein einziger Fall war messbar, 24 Abschnitt 3b konnte keine
# Datei-Kennungen erheben.
set -eu

# Alles, worin sich zwei Maschinen unterscheiden koennen, ist eine Variable mit
# Vorgabe, damit diese Datei keinen Pfad einer Maschine traegt. Die erste Vorgabe
# leitet sich aus dem Ort des Skripts selbst ab, was auf der Box und in einer
# Arbeitskopie gleichermassen haelt.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
BASE="${BASE:-https://loadtest.infranode.dev}"
KORPUS="${KORPUS:-$REPO/testdata/corpus}"
# Das Konto der Faelle. Ausdruecklich nicht lasttest: in jener Heimat liegt der
# Lastkorpus, und die Begriffe der Faelle stehen darin.
KONTO="${KONTO:-sprachfall}"
ORDNER="${ORDNER:-corpus}"
# Das Konto, dem die 52.111 Dokumente gehoeren. Diese Fassung fragt es nicht mehr
# ueber eine Route, sie misst den Bestand im Container; der Name bleibt im Kopf
# der Rohdatei stehen, weil er sagt, gegen welchen Fremdbestand gemessen wurde.
LASTKONTO="${LASTKONTO:-lasttest}"
# Die Passwortdatei des Lastkontos auf der Box. Diese Fassung liest sie NICHT
# mehr: die Vorpruefung fragt keine Route und braucht deshalb kein zweites
# Konto-Passwort. Die Variable bleibt, weil der Boxplan sie uebergibt und ein
# Lauf, der sie setzt, nicht daran scheitern soll.
PWFILE="${PWFILE:-$HOME/work/.pw/lasttest}"
# Die Zahl der Dateien des Referenzkorpus. Hingeschrieben statt aus dem
# Verzeichnis gezaehlt, weil eine Pruefung, die ihre eigene Erwartung zaehlt, sich
# selbst recht gibt, egal welche Dateien angekommen sind.
ERWARTETE_DATEIEN="${ERWARTETE_DATEIEN:-39}"
# Die Frist, bevor ein Arbeitsvorrat als Antwort gilt, gegen die langsamste
# beteiligte Uhr: der Poller-Backoff laeuft bis zu 300 s, und AIO ruft cron.php
# nur alle fuenf Minuten.
FRIST="${FRIST:-360}"
RUNDEN="${RUNDEN:-40}"
RUNDENFRIST="${RUNDENFRIST:-60}"
# Der Container, in dem die Sonde laeuft, und die Sonde selbst. Beide Vorgaben
# folgen 94-grundlast.sh: dort wandert das Werkzeug mit docker cp in denselben
# Container und wird mit dem Python der Anwendung gefahren.
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
SONDE="${SONDE:-$SKRIPTE/73-bestand-sonde.py}"
# Der Rang, ab dem ein Fall seine Aussage nicht mehr tragen kann. 64 ist
# MAX_RECHECKS_ABSOLUTE aus php/lib/Search/Provider.php:90, also der Deckel der
# Kandidaten, die eine einzelne Suche noch einmal prueft. Die alte Schwelle des
# Fremdbestands ist ersatzlos weg, samt ihrer Tiefe: beide haben eine
# Trefferzahl gemeint, und eine Trefferzahl ist nicht mehr die Messgroesse.
RANG_SCHWELLE="${RANG_SCHWELLE:-64}"
# Die Laufnummer des letzten gruenen integration.yml-Laufs. Keine Vorgabe: sie
# ist der CI-Beleg, neben dem die Zahlen dieses Schrittes stehen, und ein Lauf
# ohne sie endet unten.
CI_LAUF="${CI_LAUF:-}"

# Die sieben Dateinamen der Faelle. Hier benannt, damit eine Umbenennung einer
# Korpusdatei an einer Stelle bricht statt an zehn, genau wie integration.yml es
# haelt. Abschnitt 3b liest dieselben Namen noch einmal, um die Kennung der
# eigenen Datei je Fall zu finden.
SHARED_FILE="${SHARED_FILE:-09-bescheid.pdf}"
NOTICE_FILE="${NOTICE_FILE:-10-kuendigung.docx}"
OVERVIEW_FILE="${OVERVIEW_FILE:-11-uebersicht.odt}"
MEMO_FILE="${MEMO_FILE:-12-aktenvermerk.txt}"
SWISS_FILE="${SWISS_FILE:-15-schweiz-baubewilligung.pdf}"
AUSTRIAN_FILE="${AUSTRIAN_FILE:-16-oesterreich-mitteilung.pdf}"
REMINDER_FILE="${REMINDER_FILE:-30-nur-ein-bild.pdf}"

# Die Laufnummer zuerst, vor allem anderen. Sie kostet nichts, sie braucht keine
# Box, und sie ist die eine Verweigerung, die vor dem ersten Fall kommen muss
# statt nach dem letzten.
case "$CI_LAUF" in
    '' | *[!0-9]*)
        echo "98c-sprachfaelle: CI_LAUF traegt keine Laufnummer eines gruenen integration.yml-Laufs" >&2
        echo "98c-sprachfaelle: jener Lauf faehrt dieselben zehn Faelle auf einer frischen" >&2
        echo "98c-sprachfaelle: Instanz ohne Fremdbestand, und er ist die Haelfte der Aussage," >&2
        echo "98c-sprachfaelle: die diese Box nicht machen kann. Ohne ihn sind die Zahlen" >&2
        echo "98c-sprachfaelle: dieses Laufs unvollstaendig, also startet der Lauf nicht (DI-10-02)." >&2
        echo "98c-sprachfaelle: gh run list --workflow=integration.yml --status success" >&2
        exit 22
        ;;
esac

if ! command -v jq >/dev/null 2>&1; then
    echo "98c-sprachfaelle: jq liegt nicht auf dieser Box, und alle Zusicherungen lesen JSON damit" >&2
    echo "98c-sprachfaelle: jq installieren oder diesen Block von einer Maschine fahren, die es hat" >&2
    exit 18
fi

mkdir -p "$OUT"
# Die Rohdatei des neuen Laufverzeichnisses; ihr Name folgt der Nummerierung
# dieses Verzeichnisses und nicht der des Originals.
ZIEL="${ZIEL:-$OUT/05-sprachfaelle.txt}"
WORK=$(mktemp -d)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT
# Eine Zeile je roter Zusicherung in der zweiten Datei, eine Zeile je rotem Fall
# in der ersten, eine Zeile je nicht messbarem Fall in der dritten. Alle drei
# werden leer angelegt, damit ihr spaeteres Lesen nie die Frage ist, ob ueberhaupt
# etwas gelaufen ist.
: >"$WORK/fehler"
: >"$WORK/fehlertexte"
: >"$WORK/nichtmessbar"
# Das Verzeichnis behaelt seinen Namen aus 98b, obwohl darin jetzt ein Rang
# steht: es ist dieselbe Stelle mit derselben Aufgabe, und ein umbenanntes
# Verzeichnis wuerde den Vergleich der beiden Fassungen ohne Not erschweren.
mkdir -p "$WORK/fremd"

# Der Wrapper traegt OC_PASS ueber die zwei Schichten, die es sonst schlucken
# wuerden, und nur wenn es gesetzt ist: sudo raeumt unter env_reset die Umgebung,
# und docker exec gibt von sich aus nichts weiter. Der Wert bleibt aus jeder
# Argumentliste heraus, was T-10-27 verlangt.
occ() {
    if [ -n "${OC_PASS:-}" ]; then
        sudo --preserve-env=OC_PASS docker exec -e OC_PASS \
            --user www-data "$NEXTCLOUD" php occ "$@"
    else
        sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
    fi
}

# Der Arbeitsvorrat aus EINEM Aufruf des Statusbefehls. Zwei Bloecke einer
# Ausgabe statt zwei Aufrufen, weil zweimal fragen zwei Antworten erlaubt, die
# einander widersprechen.
vorrat_von() {
    awk '/^Work stock/ {found = 1; next}
         found && /^  (scheduled|handed to the worker)/ {sum += $NF}
         END {print sum + 0}' "$1"
}

# Der kleinere der beiden Raenge aus der Zeile der Sonde ($1 der Begriff, $2 die
# Ausgabedatei), oder das Wort ausserhalb. Der kleinere, weil die Fusion die
# eigene Datei nicht schlechter stellt als ihre bessere der beiden Positionen,
# und ausserhalb, sobald keine der beiden Angaben eine Zahl ist: ausserhalb und
# keine-kennung sind Worte, und ein Wort gegen eine Schwelle zu rechnen waere
# eine Rechnung, die kein Ergebnis hat. Der Schluessel traegt das ganze
# geklammerte Feld, damit begriff='bescheid' nicht auch die Zeile von
# begriff='type:pdf bescheid' trifft.
rang_aus_sonde() {
    awk -v schluessel="begriff='$1'" '
        index($0, schluessel) == 0 { next }
        {
            lex = ""
            sem = ""
            for (i = 1; i <= NF; i++) {
                if (substr($i, 1, 9) == "rang_lex=") { lex = substr($i, 10) }
                if (substr($i, 1, 9) == "rang_sem=") { sem = substr($i, 10) }
            }
            lex_zahl = (lex ~ /^[0-9]+$/)
            sem_zahl = (sem ~ /^[0-9]+$/)
            if (lex_zahl && sem_zahl) {
                if (lex + 0 < sem + 0) { print lex } else { print sem }
            } else if (lex_zahl) {
                print lex
            } else if (sem_zahl) {
                print sem
            } else {
                print "ausserhalb"
            }
            gefunden = 1
            exit
        }
        END { if (gefunden != 1) { print "ausserhalb" } }
    ' "$2"
}

# Das Passwort des Kontos. Hier erzeugt, aus der Umgebung und aus einer
# curl-Konfigurationsdatei benutzt, nie in ein Argument oder eine Rohdatei
# geschrieben.
KONTOPW=$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')
CURLRC="$WORK/curlrc"
printf 'user = "%s:%s"\n' "$KONTO" "$KONTOPW" >"$CURLRC"
chmod 600 "$CURLRC"

search() {
    curl -sfS -G -K "$CURLRC" \
        -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
        --data-urlencode "term=$1" \
        "$BASE/ocs/v2.php/search/providers/findling/search" -o "$2"
}

# Welcher Fall gerade faehrt. Eine Variable statt eines Arguments von fail, weil
# die Bilanzzeile FAELLE zaehlt und nicht Zusicherungen: Fall 1 allein traegt
# vier davon, und vier rote Zusicherungen eines Falls sind ein roter Fall.
FALL=0

# Eine rote Zusicherung, und der Rang der eigenen Datei steht in derselben Zeile.
# Ein Leser, der neben einem roten Fall einen kleinen Rang sieht, weiss, dass
# dieser Fall von der deutschen Sprachkette handelt und nicht vom Fremdbestand.
fail() {
    rang=$(cat "$WORK/fremd/$FALL" 2>/dev/null || echo '-')
    printf 'sprachfall %s ROT: %s (Rang der eigenen Datei %s, Schwelle %s)\n' \
        "$FALL" "$1" "${rang:--}" "$RANG_SCHWELLE"
    cat "$2" 2>/dev/null || true
    printf 'fall %s\n' "$FALL" >>"$WORK/fehler"
    printf 'fall %s: %s\n' "$FALL" "$1" >>"$WORK/fehlertexte"
}

# Das erste der beiden Urteile, und es kommt fuer jeden Fall zuerst. In
# $WORK/fremd/<fall> steht der kleinere der beiden Raenge der eigenen Datei oder
# das Wort ausserhalb.
#
# Warum der Rang und nicht der Bestand entscheidet: die Fusion ordnet nach RRF,
# also nach der Summe der Kehrwerte der Raenge. Jedes Dokument, das in BEIDEN
# Listen vor der eigenen Datei liegt, liegt mit beiden Summanden vor ihr und
# damit auch in der fusionierten Liste. Ein Rang schlechter als 64 in beiden
# Listen kann deshalb durch keine Fusion in die Reichweite der 64 Rechecks
# kommen, und ein Fall, dessen Aussage darin ertrinkt, ist nicht rot, sondern
# nicht messbar.
messbar() {
    rang=$(cat "$WORK/fremd/$1" 2>/dev/null || echo '')
    if [ -z "$rang" ]; then
        printf 'sprachfall %s NICHT MESSBAR (Rang nicht erhoben)\n' "$1"
        printf 'fall %s\n' "$1" >>"$WORK/nichtmessbar"
        return 1
    fi
    case "$rang" in
        *[!0-9]*)
            # ausserhalb, keine-kennung oder was die Sonde sonst hingeschrieben
            # hat: in keinem dieser Faelle steht die eigene Datei in einer der
            # beiden Listen, und ein Vergleich gegen eine Schwelle waere hier
            # eine Rechnung mit einem Wort.
            printf 'sprachfall %s NICHT MESSBAR (eigene Datei in keiner der beiden Listen: %s)\n' \
                "$1" "$rang"
            printf 'fall %s\n' "$1" >>"$WORK/nichtmessbar"
            return 1
            ;;
    esac
    if [ "$rang" -gt "$RANG_SCHWELLE" ]; then
        printf 'sprachfall %s NICHT MESSBAR (Rang %s, Schwelle %s)\n' "$1" "$rang" "$RANG_SCHWELLE"
        printf 'fall %s\n' "$1" >>"$WORK/nichtmessbar"
        return 1
    fi
    return 0
}

# Das zweite Urteil, und nur ein messbarer Fall erreicht es je. Ein Fall, der
# keine rote Zusicherung geschrieben hat, ist gruen, und er sagt das auch: ein
# Lauf, der fuer sechs von zehn Faellen nichts druckt, liest sich wie sechs
# Faelle, die nie gelaufen sind.
urteil() {
    if grep -q "^fall $1\$" "$WORK/fehler" 2>/dev/null; then
        return 0
    fi
    rang=$(cat "$WORK/fremd/$1" 2>/dev/null || echo '-')
    printf 'sprachfall %s GRUEN (Rang der eigenen Datei %s)\n' "$1" "${rang:--}"
}

{
    date -u +'sprachfaelle-start %Y-%m-%dT%H:%M:%SZ'
    printf 'konto: %s (ausdruecklich nicht %s, siehe Kopf)\n' "$KONTO" "$LASTKONTO"
    printf 'korpus: %s\n' "$KORPUS"
    printf 'ci-beleg: integration.yml Lauf %s\n' "$CI_LAUF"

    echo "=== Abschnitt 0: der Bestand im Index, im Prozess gemessen (DI-10-02) ==="
    echo "-- hier wird weder eine Route noch ein Konto gefragt: eine Trefferzahl ueber"
    echo "   die Prozessgrenze waere das Zaehl-Orakel aus T-02-93. Die alte Fassung hat"
    echo "   ueber die OCS-Route fuer jeden Begriff und jede Tiefe 26 gemessen, also den"
    echo "   Deckel der Antwort und nicht den Bestand dahinter --"
    printf 'fremdbestand-konto:    %s (gemessen wird sein Bestand, nicht seine Antwort)\n' "$LASTKONTO"
    printf 'rang-schwelle:         %s (MAX_RECHECKS_ABSOLUTE, siehe Kopf)\n' "$RANG_SCHWELLE"
    echo 'vorpruefung-gefahren nein' >"$WORK/vorpruefung-urteil"
    if [ ! -f "$SONDE" ]; then
        echo "die Sonde liegt nicht neben diesem Skript: $SONDE"
        echo "ohne sie gibt es keine Messgroesse, die die Schwelle je erreichen kann"
    elif ! sudo docker cp "$SONDE" "$CONTAINER:/tmp/73-bestand-sonde.py" 2>"$WORK/sonde.err"; then
        echo "die Sonde konnte nicht in den Container $CONTAINER getragen werden"
        cat "$WORK/sonde.err" 2>/dev/null || true
    elif ! sudo docker exec "$CONTAINER" /app/.venv/bin/python /tmp/73-bestand-sonde.py \
            >"$WORK/bestand-vorlauf.txt" 2>"$WORK/sonde.err"; then
        echo "die Sonde ist im Container nicht durchgelaufen"
        cat "$WORK/bestand-vorlauf.txt" 2>/dev/null || true
        cat "$WORK/sonde.err" 2>/dev/null || true
    else
        cat "$WORK/bestand-vorlauf.txt"
        echo 'vorpruefung-gefahren ja' >"$WORK/vorpruefung-urteil"
    fi
    # Der Abbruch mit 19 steht NICHT hier, sondern unter der Pipeline: ein exit
    # in diesem Block verliesse nur die Subshell, und die Verweigerung waere eine
    # Zeile in einer Rohdatei, die niemand liest.
    cat "$WORK/vorpruefung-urteil"

    echo "=== Abschnitt 1: das Konto, dessen Heimat nichts als den Korpus halten soll ==="
    # Das Skelett wird zuerst abgeschaltet, und das ist keine Ordnungsliebe: ohne
    # diesen Schritt legt Nextcloud in jede neue Heimat ein Handbuch, einen
    # Bilderordner und eine Liesmich, und die Zaehlzusicherungen der zehn Faelle
    # waeren Aussagen ueber Dokumente, die niemand gewaehlt hat. integration.yml
    # macht genau das, aus genau diesem Grund. Der vorherige Wert wird zuerst
    # gelesen und am Ende dieses Blocks zurueckgeschrieben.
    SKELETON_VORHER=$(occ config:system:get skeletondirectory 2>/dev/null || true)
    printf 'skeletondirectory vorher: %s\n' "${SKELETON_VORHER:-(leer oder nicht gesetzt)}"
    occ config:system:set skeletondirectory --value='' 2>&1 || true

    if occ user:info "$KONTO" >/dev/null 2>&1; then
        echo "das Konto existiert schon, es wird nicht neu angelegt"
        echo "-- Achtung: seine Heimat muss NUR den Korpus enthalten, sonst sind die"
        echo "   Faelle rot aus dem falschen Grund. Dieser Block ist abbrechbar (A7). --"
        # Das Passwort eines bestehenden Kontos ist hier unbekannt, es wird also
        # aus der Umgebung neu gesetzt. Nie ueber ein Argument.
        OC_PASS="$KONTOPW" occ user:resetpassword --password-from-env "$KONTO" 2>&1 || true
    else
        OC_PASS="$KONTOPW" occ user:add --password-from-env "$KONTO" 2>&1
    fi
    occ user:info "$KONTO" 2>&1 | sed -n '1,6p' || true

    echo "=== Abschnitt 2: der Korpus ueber WebDAV, der Weg eines Nutzers ==="
    ZIELORDNER="$BASE/remote.php/dav/files/$KONTO/$ORDNER"
    curl -sS -o /dev/null -K "$CURLRC" -X MKCOL "$ZIELORDNER" || true
    date -u +'upload-vor %Y-%m-%dT%H:%M:%SZ'
    : >"$WORK/dateiids.txt"
    for pfad in "$KORPUS"/*; do
        name=$(basename "$pfad")
        code=$(curl -sS -o /dev/null -D "$WORK/kopf.txt" -w '%{http_code}' -K "$CURLRC" \
            -T "$pfad" "$ZIELORDNER/$name" || echo 000)
        printf '%s %s\n' "$code" "$name" >>"$WORK/upload.txt"
        # Die Kennung der eigenen Datei wird HIER erhoben und nicht spaeter: ein
        # Rang ist erst messbar, wenn die Datei existiert, und ihre Kennung ist
        # beim Hochladen ohne zweite Abfrage zu haben. Nextcloud gibt OC-FileId
        # mit einem Instanz-Suffix aus (etwa 00000023oc9mn3rmbkgs); die
        # Datei-Kennung ist allein der fuehrende Zifferblock, und seine
        # fuehrenden Nullen gehoeren zur Auffuellung und nicht zur Zahl.
        kennung=$(sed -n 's/^[Oo][Cc]-[Ff]ile[Ii]d:[[:space:]]*\([0-9][0-9]*\).*$/\1/p' \
            "$WORK/kopf.txt" 2>/dev/null | tail -1 | sed 's/^0*//')
        if [ -n "$kennung" ]; then
            printf '%s %s\n' "$name" "$kennung" >>"$WORK/dateiids.txt"
        fi
    done
    date -u +'upload-nach %Y-%m-%dT%H:%M:%SZ'
    awk '{print $1}' "$WORK/upload.txt" | sort | uniq -c
    HOCHGELADEN=$(awk '$1 ~ /^2/ {n++} END {print n + 0}' "$WORK/upload.txt")
    KENNUNGEN=$(grep -c . "$WORK/dateiids.txt" 2>/dev/null || true)
    printf 'dateien-hochgeladen %s\n' "$HOCHGELADEN"
    printf 'dateien-erwartet    %s\n' "$ERWARTETE_DATEIEN"
    printf 'datei-kennungen     %s (aus dem Antwortkopf OC-FileId)\n' "${KENNUNGEN:-0}"
    if [ "$HOCHGELADEN" -eq "$ERWARTETE_DATEIEN" ]; then
        echo 'upload-vollstaendig ja' >"$WORK/upload-urteil"
    else
        echo 'upload-vollstaendig nein' >"$WORK/upload-urteil"
        grep -v '^2' "$WORK/upload.txt" || true
    fi
    cat "$WORK/upload-urteil"
    occ files:scan --path="/$KONTO/files/$ORDNER" 2>&1 | tail -6 || true

    echo "=== Abschnitt 3: die Indexierung, gegen die langsamste Uhr ==="
    echo "-- zuerst $FRIST s, weil der Poller-Backoff bis zu 300 s laeuft und der"
    echo "   Fuenf-Minuten-Systemcron zwei Runden braucht, bevor der erste Auftrag der"
    echo "   Anwendung ueberhaupt in der Schlange steht (Pitfall 11) --"
    sleep "$FRIST"
    runde=0
    vorrat=-1
    while [ "$runde" -lt "$RUNDEN" ]; do
        runde=$((runde + 1))
        occ findling:index >"$WORK/status.txt" 2>&1 || true
        vorrat=$(vorrat_von "$WORK/status.txt")
        date -u +"indexierung runde=$runde vorrat=$vorrat %Y-%m-%dT%H:%M:%SZ"
        if [ "$vorrat" -eq 0 ]; then
            break
        fi
        sleep "$RUNDENFRIST"
    done
    if [ "$vorrat" -eq 0 ]; then
        echo 'arbeitsvorrat-leer ja' >"$WORK/index-urteil"
    else
        echo 'arbeitsvorrat-leer nein' >"$WORK/index-urteil"
    fi
    cat "$WORK/index-urteil"
    echo "-- und erst JETZT die Verdikte, weil skipped:no_text_layer ein vorlaeufiges"
    echo "   Verdikt ist und ein frueheres Lesen die Scan-Spur als Fehlschlag meldete --"
    cat "$WORK/status.txt"

    echo "=== Abschnitt 3b: der Rang der eigenen Datei, im Prozess gemessen ==="
    # Dieser Abschnitt steht zwischen der Indexierung und den Faellen und nicht
    # in Abschnitt 0, und das ist die einzige strukturelle Aenderung gegenueber
    # 98b: der Rang der eigenen Datei ist erst messbar, wenn die Datei existiert
    # und indexiert ist. Der Bestand ist vorher messbar, deshalb misst Abschnitt
    # 0 ihn und dieser Abschnitt den Rang.
    echo 'rang-erhoben nein' >"$WORK/rang-urteil"
    # Fall, Begriff und die Datei, die der Fall in der Antwort erwartet, an einer
    # einzigen Stelle. Das Here-Document steht NICHT in Anfuehrungszeichen,
    # anders als die Begriffsliste von 98b: die Dateinamen sind oben Variablen,
    # damit eine Umbenennung an einer Stelle bricht, und dafuer muessen sie hier
    # eingesetzt werden. Es wird einmal in eine Arbeitsdatei geschrieben, weil
    # beide Schleifen dieses Abschnitts dieselbe Zuordnung lesen. Die Faelle 6
    # und 7 fragen dieselbe Datei mit zwei verschiedenen Suchzeilen; das ist kein
    # Versehen dieser Tabelle.
    cat >"$WORK/zuordnung" <<ZUORDNUNG
1|Genehmigung|$SHARED_FILE
2|Frist|$NOTICE_FILE
3|Mueller|$MEMO_FILE
4|Vertrag|$OVERVIEW_FILE
5|"drei Monate"|$NOTICE_FILE
6|bescheid|$SHARED_FILE
7|type:pdf bescheid|$SHARED_FILE
8|Belehrung|$SWISS_FILE
9|Auszug|$AUSTRIAN_FILE
10|Erinnerung|$REMINDER_FILE
ZUORDNUNG
    DATEI_IDS=''
    while IFS='|' read -r nummer begriff datei; do
        [ -n "$nummer" ] || continue
        kennung=$(awk -v gesucht="$datei" '$1 == gesucht {print $2}' \
            "$WORK/dateiids.txt" 2>/dev/null | tail -1)
        if [ -z "$kennung" ]; then
            printf 'fall %s: keine Kennung fuer %s, der Fall gilt als ausserhalb\n' \
                "$nummer" "$datei"
            printf 'ausserhalb\n' >"$WORK/fremd/$nummer"
            continue
        fi
        printf 'fall %s: %s traegt die Kennung %s\n' "$nummer" "$datei" "$kennung"
        if [ -z "$DATEI_IDS" ]; then
            DATEI_IDS="$begriff=$kennung"
        else
            DATEI_IDS="$DATEI_IDS,$begriff=$kennung"
        fi
    done <"$WORK/zuordnung"

    if [ -z "$DATEI_IDS" ]; then
        echo "keine einzige Datei-Kennung erhoben: entweder ist der Upload gescheitert,"
        echo "oder der Antwortkopf trug kein OC-FileId. Ohne Kennung gibt es keinen Rang,"
        echo "und ohne Rang faellt das Urteil auf zweiwertig zurueck (DI-10-02)."
    else
        # Die Kennungen reisen ausschliesslich in der Umgebung, nie in einem
        # Argument: sudo raeumt unter env_reset auf, und docker exec gibt von
        # sich aus nichts weiter, also wird beiden Schichten genau diese eine
        # Variable genannt.
        export DATEI_IDS
        if ! sudo --preserve-env=DATEI_IDS docker exec -e DATEI_IDS "$CONTAINER" \
                /app/.venv/bin/python /tmp/73-bestand-sonde.py \
                >"$WORK/bestand-rang.txt" 2>"$WORK/rang.err"; then
            echo "die Sonde ist im zweiten Lauf nicht durchgelaufen"
            cat "$WORK/bestand-rang.txt" 2>/dev/null || true
            cat "$WORK/rang.err" 2>/dev/null || true
        else
            cat "$WORK/bestand-rang.txt"
            echo 'rang-erhoben ja' >"$WORK/rang-urteil"
        fi
    fi
    cat "$WORK/rang-urteil"

    if [ "$(cat "$WORK/rang-urteil")" = 'rang-erhoben ja' ]; then
        echo "-- je Fall der kleinere der beiden Raenge, und genau diese Zahl liest das"
        echo "   erste der beiden Urteile --"
        while IFS='|' read -r nummer begriff datei; do
            [ -n "$nummer" ] || continue
            rang=$(rang_aus_sonde "$begriff" "$WORK/bestand-rang.txt")
            printf '%s\n' "$rang" >"$WORK/fremd/$nummer"
            printf 'rang fall %s begriff %s: %s (Schwelle %s), datei %s\n' \
                "$nummer" "$begriff" "$rang" "$RANG_SCHWELLE" "$datei"
        done <"$WORK/zuordnung"
    fi

    echo "=== Abschnitt 4: die zehn Faelle, dreiwertig beurteilt ==="
    if [ "$(cat "$WORK/index-urteil")" != 'arbeitsvorrat-leer ja' ]; then
        echo "der Arbeitsvorrat ist nicht leer, die Faelle 8 bis 10 haengen an der OCR-Spur"
        echo "und wuerden hier aus dem falschen Grund rot sein; die Faelle laufen trotzdem,"
        echo "und die Bilanz ist mit dieser Zeile daneben zu lesen"
    fi

    # 1. Das Kompositum ueber einen seiner Bestandteile. Die Datei sagt
    # Grundstuecksverkehrsgenehmigung, die Suche sagt Genehmigung, und der
    # Zerleger schliesst die Luecke.
    FALL=1
    if messbar 1; then
        start=$(date +%s%N)
        search 'Genehmigung' "$WORK/compound.json" || true
        printf 'eine gewoehnliche Suche antwortete nach %sms\n' "$((($(date +%s%N) - start) / 1000000))"
        jq -e '.ocs.data.entries | length == 1' "$WORK/compound.json" >/dev/null 2>&1 ||
            fail "a compound searched through one constituent did not bring back exactly one file" "$WORK/compound.json"
        jq -e --arg name "$SHARED_FILE" '.ocs.data.entries[0].title == $name' "$WORK/compound.json" >/dev/null 2>&1 ||
            fail "the compound hit is not the German PDF of the corpus" "$WORK/compound.json"
        # Der Auszug, und das ist die Zusicherung, die einen Treffer von einem
        # Treffer mit Inhalt trennt: die Unterzeile muss das Kompositum aus dem
        # Dokument tragen. Die Ersatzunterzeile ist der Pfad, und der Pfad
        # enthaelt das Wort nicht.
        jq -e '.ocs.data.entries[0].subline | ascii_downcase | contains("genehmigung")' "$WORK/compound.json" >/dev/null 2>&1 ||
            fail "the subline carries no excerpt from the document" "$WORK/compound.json"
        jq -e '.ocs.data.entries[0].subline | contains("<") | not' "$WORK/compound.json" >/dev/null 2>&1 ||
            fail "the excerpt carries markup, which the search dialog would show verbatim" "$WORK/compound.json"
        urteil 1
    fi

    # 2. Das zweite Kompositum, in einer anderen Datei und einem anderen Format.
    FALL=2
    if messbar 2; then
        search 'Frist' "$WORK/frist.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/frist.json" >/dev/null 2>&1 ||
            fail "Frist did not bring back exactly the notice of termination" "$WORK/frist.json"
        jq -e --arg name "$NOTICE_FILE" '.ocs.data.entries[0].title == $name' "$WORK/frist.json" >/dev/null 2>&1 ||
            fail "the Frist hit is not the DOCX of the corpus" "$WORK/frist.json"
        urteil 2
    fi

    # 3. Der ausgeschriebene Umlaut. Die Datei schreibt Mueller mit dem Zeichen,
    # die Suche mit den zwei Buchstaben, und die Variante auf der Frageseite
    # fuehrt beide zusammen.
    FALL=3
    if messbar 3; then
        search 'Mueller' "$WORK/umlaut.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/umlaut.json" >/dev/null 2>&1 ||
            fail "the written out umlaut did not find the file that spells it with the character" "$WORK/umlaut.json"
        jq -e --arg name "$MEMO_FILE" '.ocs.data.entries[0].title == $name' "$WORK/umlaut.json" >/dev/null 2>&1 ||
            fail "the umlaut hit is not the file note of the corpus" "$WORK/umlaut.json"
        urteil 3
    fi

    # 4. Die Beugung des Substantivs. Die Datei sagt Vertraege, die Suche sagt
    # Vertrag, und der Stemmer schliesst diese Luecke.
    FALL=4
    if messbar 4; then
        search 'Vertrag' "$WORK/flexion.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/flexion.json" >/dev/null 2>&1 ||
            fail "the singular did not find the plural" "$WORK/flexion.json"
        jq -e --arg name "$OVERVIEW_FILE" '.ocs.data.entries[0].title == $name' "$WORK/flexion.json" >/dev/null 2>&1 ||
            fail "the inflection hit is not the ODT of the corpus" "$WORK/flexion.json"
        urteil 4
    fi

    # 5. Die Phrase. Nur die Datei mit den zwei Woertern in dieser Reihenfolge.
    FALL=5
    if messbar 5; then
        search '"drei Monate"' "$WORK/phrase.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/phrase.json" >/dev/null 2>&1 ||
            fail "the phrase did not bring back exactly one file" "$WORK/phrase.json"
        jq -e --arg name "$NOTICE_FILE" '.ocs.data.entries[0].title == $name' "$WORK/phrase.json" >/dev/null 2>&1 ||
            fail "the phrase hit is not the DOCX of the corpus" "$WORK/phrase.json"
        urteil 5
    fi

    # 6. Der Ausschluss, und die Kontrolle, die ihm seinen Sinn gibt. Bescheid
    # steht mit Absicht in zwei Dateien; ohne die Kontrolle saehe ein Ausschluss,
    # der nichts tut, genau wie einer aus, der wirkt, also laeuft die Kontrolle
    # ZUERST.
    FALL=6
    if messbar 6; then
        search 'bescheid' "$WORK/both.json" || true
        jq -e '.ocs.data.entries | length == 2' "$WORK/both.json" >/dev/null 2>&1 ||
            fail "the word that stands in two files did not bring back two files" "$WORK/both.json"
        search 'bescheid -frist' "$WORK/excluded.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/excluded.json" >/dev/null 2>&1 ||
            fail "the minus did not remove the second file" "$WORK/excluded.json"
        jq -e --arg name "$SHARED_FILE" '.ocs.data.entries[0].title == $name' "$WORK/excluded.json" >/dev/null 2>&1 ||
            fail "the exclusion removed the wrong file" "$WORK/excluded.json"
        urteil 6
    fi

    # 7. Der Dateityp. Nextcloud hat dafuer keinen eingebauten Filter, also
    # reist er in der Suchzeile mit und wird zu einem Pflichtbegriff auf ext.
    FALL=7
    if messbar 7; then
        search 'type:pdf bescheid' "$WORK/filetype.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/filetype.json" >/dev/null 2>&1 ||
            fail "the file type filter did not narrow the two hits down to the PDF" "$WORK/filetype.json"
        jq -e --arg name "$SHARED_FILE" '.ocs.data.entries[0].title == $name' "$WORK/filetype.json" >/dev/null 2>&1 ||
            fail "the file type filter kept the wrong file" "$WORK/filetype.json"
        urteil 7
    fi

    # 8. Das dritte Kompositum, in der gescannten Schweizer Bewilligung. Die
    # Seite sagt Rechtsmittelbelehrung, die Suche sagt Belehrung, und
    # split_compound macht den zweiten Teil des Wortes zu einem eigenen Begriff.
    # Belehrung steht im ganzen Korpus nur innerhalb seines Kompositums.
    FALL=8
    if messbar 8; then
        search 'Belehrung' "$WORK/belehrung.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/belehrung.json" >/dev/null 2>&1 ||
            fail "Belehrung did not bring back exactly the scanned Swiss permit" "$WORK/belehrung.json"
        jq -e --arg name "$SWISS_FILE" '.ocs.data.entries[0].title == $name' "$WORK/belehrung.json" >/dev/null 2>&1 ||
            fail "the Belehrung hit is not the Swiss permit of the corpus" "$WORK/belehrung.json"
        jq -e '.ocs.data.entries[0].subline | ascii_downcase | contains("belehrung")' "$WORK/belehrung.json" >/dev/null 2>&1 ||
            fail "the Belehrung hit carries no excerpt from the document" "$WORK/belehrung.json"
        jq -e '.ocs.data.entries[0].subline | contains("<") | not' "$WORK/belehrung.json" >/dev/null 2>&1 ||
            fail "the Belehrung excerpt carries markup, which the search dialog would show verbatim" "$WORK/belehrung.json"
        urteil 8
    fi

    # 9. Ein Kompositum, das als Pixel und in keiner anderen Form existiert. Die
    # gescannte oesterreichische Mitteilung sagt Grundbuchsauszug, die Suche sagt
    # Auszug, und ohne die OCR-Spur gaebe es gar nichts zu zerlegen.
    FALL=9
    if messbar 9; then
        search 'Auszug' "$WORK/auszug.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/auszug.json" >/dev/null 2>&1 ||
            fail "Auszug did not bring back exactly the scanned Austrian notice" "$WORK/auszug.json"
        jq -e --arg name "$AUSTRIAN_FILE" '.ocs.data.entries[0].title == $name' "$WORK/auszug.json" >/dev/null 2>&1 ||
            fail "the Auszug hit is not the Austrian notice of the corpus" "$WORK/auszug.json"
        urteil 9
    fi

    # 10. Dieselbe Form noch einmal, in der Datei, die ein Bild ist und sonst
    # nichts. Sie sagt Zahlungserinnerung, die Suche sagt Erinnerung.
    FALL=10
    if messbar 10; then
        search 'Erinnerung' "$WORK/erinnerung.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/erinnerung.json" >/dev/null 2>&1 ||
            fail "Erinnerung did not bring back exactly the one page reminder" "$WORK/erinnerung.json"
        jq -e --arg name "$REMINDER_FILE" '.ocs.data.entries[0].title == $name' "$WORK/erinnerung.json" >/dev/null 2>&1 ||
            fail "the Erinnerung hit is not the image only PDF of the corpus" "$WORK/erinnerung.json"
        urteil 10
    fi

    echo "=== Die Bilanz der zehn Faelle, mit beiden Zahlen in einer Zeile ==="
    # Faelle und Zusicherungen werden getrennt gezaehlt, weil sie zwei
    # verschiedene Zahlen sind: die Bilanzzeile handelt von Faellen, die Liste
    # darunter von Zusicherungen, von denen Fall 1 allein vier traegt. Die zweite
    # Zahl der Bilanzzeile ist die, um die es DI-10-02 geht: eine Bilanz mit
    # einer Zahl ist genau das Missverstaendnis, das aus vier nicht messbaren
    # Faellen vier rote gemacht hat.
    ROT=$(sort -u "$WORK/fehler" | grep -c . || true)
    NICHTMESSBAR=$(sort -u "$WORK/nichtmessbar" | grep -c . || true)
    ZEILEN=$(grep -c . "$WORK/fehlertexte" 2>/dev/null || true)
    BESTANDEN=$((10 - ROT - NICHTMESSBAR))
    [ "$BESTANDEN" -ge 0 ] || BESTANDEN=0
    printf 'sprachfaelle bestanden %s von 10, davon %s nicht messbar\n' "$BESTANDEN" "$NICHTMESSBAR"
    printf 'rote faelle %s, nicht messbare faelle %s, rote zusicherungen %s\n' \
        "$ROT" "$NICHTMESSBAR" "${ZEILEN:-0}"
    if [ "$ROT" -gt 0 ]; then
        echo "-- die roten Zusicherungen im Wortlaut, jede eine eigene Aussage --"
        cat "$WORK/fehlertexte"
        echo "-- die roten Faelle --"
        sort -u "$WORK/fehler"
    fi
    if [ "$NICHTMESSBAR" -gt 0 ]; then
        echo "-- die nicht messbaren Faelle. Sie sind KEIN Sprachbefund: die eigene Datei"
        echo "   steht in beiden Ranglisten ausserhalb der $RANG_SCHWELLE Rechecks oder gar"
        echo "   nicht darin, und keine Fusion bringt sie von dort in Reichweite (DI-10-02) --"
        sort -u "$WORK/nichtmessbar"
    fi

    echo "=== Abschnitt 5: die Einordnung dieser Zahlen ==="
    echo "Fuer diese zehn Faelle gibt es KEINE v1.0-Entsprechung auf dieser Box:"
    echo "weder der Semantiklauf vom 05.09. noch die Nachmessung vom 07.09. hat sie"
    echo "gefahren. Die Zahl dieses Schrittes ist damit eine ERSTMESSUNG neben einem"
    echo "CI-Beleg und keine Vergleichszeile."
    printf 'ci-beleg: integration.yml Lauf %s\n' "$CI_LAUF"
    echo "Genau dieser Lauf faehrt dieselben zehn Faelle auf einer FRISCHEN Instanz OHNE"
    echo "Fremdbestand, auf amd64, gegen den PHP-Entwicklungsserver (Job"
    echo "index-search-e2e). Er ist die Messung mit eigenem Index, nach der DI-10-02"
    echo "verlangt, und deshalb ist seine Laufnummer hier Pflicht und keine Notiz."
    echo "Dieser Schritt misst dieselbe Aussage auf arm64 gegen eine All-in-One-Instanz"
    echo "mit vollem Vektorbestand und 52.111 Fremddokumenten. Gleich ist die Aussage,"
    echo "nicht die Umgebung, und wo die eigene Datei ausserhalb beider Ranglisten"
    echo "steht, steht NICHT MESSBAR und kein Urteil."

    echo "=== Die Skeletteinstellung, zurueckgeschrieben wie sie war ==="
    if [ -n "${SKELETON_VORHER:-}" ]; then
        occ config:system:set skeletondirectory --value="$SKELETON_VORHER" 2>&1 || true
    else
        occ config:system:delete skeletondirectory 2>&1 || true
    fi
    occ config:system:get skeletondirectory 2>&1 || echo "(nicht gesetzt, wie vorher)"

    date -u +'sprachfaelle-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Alles unterhalb der Pipeline, weil der Rueckgabewert einer Pipeline zu tee
# gehoert: ein exit innerhalb des Blocks oben verliesse nur die Subshell, und die
# Verweigerung waere eine Zeile in einer Rohdatei, die niemand liest.
vorpruefung=$(cat "$WORK/vorpruefung-urteil" 2>/dev/null || echo 'vorpruefung-gefahren nein')
rang=$(cat "$WORK/rang-urteil" 2>/dev/null || echo 'rang-erhoben nein')
upload=$(cat "$WORK/upload-urteil" 2>/dev/null || echo 'upload-vollstaendig nein')
index=$(cat "$WORK/index-urteil" 2>/dev/null || echo 'arbeitsvorrat-leer nein')
rot=$(sort -u "$WORK/fehler" 2>/dev/null | grep -c . || true)
nichtmessbar=$(sort -u "$WORK/nichtmessbar" 2>/dev/null | grep -c . || true)

if [ "$vorpruefung" != 'vorpruefung-gefahren ja' ]; then
    echo "98c-sprachfaelle: die Vorpruefung des Fremdbestands konnte nicht gefahren werden" >&2
    echo "98c-sprachfaelle: ohne sie waere jedes Urteil wieder zweiwertig, und genau das" >&2
    echo "98c-sprachfaelle: ist der Inhalt von DI-10-02; $ZIEL sagt, woran es lag" >&2
    exit 19
fi

if [ "$rang" != 'rang-erhoben ja' ]; then
    echo "98c-sprachfaelle: Abschnitt 3b konnte keine Datei-Kennungen erheben" >&2
    echo "98c-sprachfaelle: ohne den Rang der eigenen Datei gibt es keine Messgroesse," >&2
    echo "98c-sprachfaelle: die die Schwelle $RANG_SCHWELLE erreichen kann, und jeder Fall" >&2
    echo "98c-sprachfaelle: hiesse NICHT MESSBAR aus dem falschen Grund; $ZIEL sagt, woran" >&2
    echo "98c-sprachfaelle: es lag (kein OC-FileId im Antwortkopf oder keine Sonde)" >&2
    exit 24
fi

if [ "$upload" != 'upload-vollstaendig ja' ]; then
    echo "98c-sprachfaelle: der Upload hat nicht $ERWARTETE_DATEIEN Dateien geliefert" >&2
    echo "98c-sprachfaelle: ein Fall ueber einen Korpus, der nicht ganz da ist, sagt nichts" >&2
    exit 15
fi

if [ "$index" != 'arbeitsvorrat-leer ja' ]; then
    echo "98c-sprachfaelle: der Arbeitsvorrat war am Rundendeckel noch nicht leer" >&2
    echo "98c-sprachfaelle: die Faelle 8 bis 10 haengen an der OCR-Spur, ihre Urteile" >&2
    echo "98c-sprachfaelle: handelten also von einem unfertigen Durchlauf; dieser Block" >&2
    echo "98c-sprachfaelle: ist entwurfsgemaess abbrechbar (Annahme A7) und gehoert als" >&2
    echo "98c-sprachfaelle: Luecke in den Bericht" >&2
    exit 16
fi

if [ "${nichtmessbar:-0}" -ge 10 ]; then
    echo "98c-sprachfaelle: nicht einer der zehn Faelle war auf dieser Instanz messbar" >&2
    echo "98c-sprachfaelle: ein Lauf, in dem die eigene Datei zu jedem Begriff ausserhalb" >&2
    echo "98c-sprachfaelle: beider Ranglisten steht, ist eine Aussage ueber die Instanz und" >&2
    echo "98c-sprachfaelle: nicht ueber die Sprachkette; der in $ZIEL genannte CI-Lauf ist" >&2
    echo "98c-sprachfaelle: der, der sie misst" >&2
    exit 23
fi

if [ "${rot:-0}" -gt 0 ]; then
    echo "98c-sprachfaelle: $rot der messbaren Faelle waren rot" >&2
    echo "98c-sprachfaelle: jeder davon ist eine eigene Aussage, und $ZIEL hat sie" >&2
    exit 17
fi

echo "98C-SPRACHFAELLE-FERTIG"
