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

    date -u +'sprachfaelle-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Alles unterhalb der Pipeline, weil der Rueckgabewert einer Pipeline zu tee
# gehoert: ein exit innerhalb des Blocks oben verliesse nur die Subshell.
vorpruefung=$(cat "$WORK/vorpruefung-urteil" 2>/dev/null || echo 'vorpruefung-gefahren nein')

if [ "$vorpruefung" != 'vorpruefung-gefahren ja' ]; then
    echo "98c-sprachfaelle: die Vorpruefung des Fremdbestands konnte nicht gefahren werden" >&2
    echo "98c-sprachfaelle: ohne sie waere jedes Urteil wieder zweiwertig, und genau das" >&2
    echo "98c-sprachfaelle: ist der Inhalt von DI-10-02; $ZIEL sagt, woran es lag" >&2
    exit 19
fi

echo "98C-SPRACHFAELLE-FERTIG"
