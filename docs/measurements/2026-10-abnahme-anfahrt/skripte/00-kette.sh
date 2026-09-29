#!/bin/sh
# Alle Zellen einer Box, unbeaufsichtigt, mit Deckel-Pruefung vor jeder Zelle
# und dem Sicherheitstimer (Phase 28, D-28-02, D-28-14).
#
# **DIESE FASSUNG IST NICHT GEFAHREN.** Keine Rohdatei liegt neben ihr; was sie
# auf der Box faehrt, faehrt sie auf der Anfahrt.
#
# Benutzung: ./00-kette.sh <box>
#
# Gestartet auf der Box, abgesetzt, zum Beispiel:
#   setsid nohup ./00-kette.sh m7g.large >rohdaten/m7g.large-kette.log 2>&1 </dev/null &
#
# Die drei Regeln, die nicht im Gedaechtnis eines Operators liegen duerfen:
#
#   1. Der Sicherheitstimer (D-28-14). Beim Start setzt die Kette
#      sudo shutdown -h +<min>, min = (1,20 x DECKEL_USD - bisher) / SATZ_USD_H
#      in Minuten, und liest die geplante Abschaltung zurueck. Ohne Ruecklesung
#      startet keine Zelle (81). Ein Herunterfahren aus dem Betriebssystem ist
#      ein Stopp und kein Terminate, und das belegt 00-typwechsel.sh vorpruefung
#      auf der Entwicklungsmaschine VOR dem Start; ihr Ergebnis steht als Marke
#      VORPRUEFUNG=stop-ja in der Laufwertedatei, und ohne die Marke startet die
#      Kette nicht (80). Ist Deckel x 1,20 schon beim Start erreicht, faehrt die
#      Box sofort herunter (82): das ist der Timer mit Rest null.
#   2. Der Deckel (D-28-02). Vor JEDER Zelle: bisher = BISHER_USD +
#      (jetzt - BOX_START_EPOCH) / 3600 x SATZ_USD_H. Ist bisher >= DECKEL_USD,
#      startet keine neue Zelle, die Marke deckel-erreicht wird geschrieben, und
#      die Kette endet mit 83. Die Box laeuft WEITER: kein shutdown, kein Abbau,
#      nichts geht verloren, bis der Owner entscheidet (Checkpoint C3). Nur der
#      Sicherheitstimer vom Start haelt sie an, falls niemand antwortet.
#   3. Das Kettenende. Nach der letzten Zelle sudo shutdown -h +2: zwei Minuten
#      fuer das Abholen per ssh, dann Stopp.
#
# Endet eine Zelle mit einem Rueckgabewert ungleich 0, endet die Kette (84) und
# zieht den Timer auf ABBRUCH_FRIST Minuten vor, wenn er spaeter laege; eine
# haltende Box soll nicht bis zum Sicherheitsstopp Geld kosten, und der Operator
# kann in der Frist eingreifen (sudo shutdown -c). Ein Stopp ist kein Abbau.
#
# Je Minute ein Herzschlag in rohdaten/<box>/00-herzschlag.txt (Zeit und
# laufende Zelle), damit der Executor von aussen lesen kann, ob die Kette lebt.
#
# Die Laufwerte stehen in LAUFWERTE (Vorgabe $HOME/work/v14-lauf.env, Rechte
# 600), eine Zeile NAME=WERT je Wert, gelesen und nie ausgefuehrt:
#
#   DECKEL_USD       der Deckel der Anfahrt in USD (02-rechenblatt.py deckel)
#   BISHER_USD       die Kosten vor dem Start dieser Box in USD
#   SATZ_USD_H       der Satz dieser Box in USD je Stunde
#   BOX_START_EPOCH  date +%s beim Start dieser Box
#   ZELLEN           die Zellen in Reihenfolge, durch Leerzeichen getrennt,
#                    je Zelle name:profil:praezision:korpus, zum Beispiel
#                    S-T:economy:int8:teil St-T:standard:int8:teil
#   ABBILD_DIGEST    sha256:<64 Hexziffern> (liest auch 10-zelle.sh)
#   VORPRUEFUNG      stop-ja, von Hand nach 00-typwechsel.sh vorpruefung
#
# Rueckgabewerte:
#
#   0   alle Zellen gemessen, Stopp in zwei Minuten
#   2   Aufruf oder Laufwerte unvollstaendig, vor dem ersten Befehl
#   80  die Marke VORPRUEFUNG=stop-ja fehlt
#   81  die geplante Abschaltung ist nicht zurueckzulesen oder falsch
#   82  Deckel x 1,20 ist beim Start erreicht, die Box faehrt herunter
#   83  der Deckel ist erreicht, keine neue Zelle, die Box laeuft weiter
#   84  eine Zelle endete mit einem Fehler, der Timer ist vorgezogen
#
# ASCII, weil die Box ihr Gebietsschema nicht garantiert.
set -eu

SKRIPTE=$(cd "$(dirname "$0")" && pwd)
LAUF=$(cd "$SKRIPTE/.." && pwd)
OUT="${OUT:-$LAUF/rohdaten}"
ZELLE_SKRIPT="${ZELLE_SKRIPT:-$SKRIPTE/10-zelle.sh}"
LAUFWERTE="${LAUFWERTE:-$HOME/work/v14-lauf.env}"
# Wo systemd die geplante Abschaltung ablegt (USEC, MODE); gelesen wird diese
# Datei und nicht die Ausgabe des Befehls, der sie setzt.
GEPLANT_DATEI="${GEPLANT_DATEI:-/run/systemd/shutdown/scheduled}"
HERZ_TAKT="${HERZ_TAKT:-60}"
ABBRUCH_FRIST="${ABBRUCH_FRIST:-60}"

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: ./00-kette.sh <box>

Die Laufwerte stehen in LAUFWERTE (Vorgabe $HOME/work/v14-lauf.env, Rechte 600):
DECKEL_USD, BISHER_USD, SATZ_USD_H, BOX_START_EPOCH, ZELLEN
(name:profil:praezision:korpus, durch Leerzeichen getrennt), ABBILD_DIGEST,
VORPRUEFUNG=stop-ja.
HINWEIS
}

verweigern() {
    echo "00-kette: $1" >&2
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

ist_betrag() {
    case "${1:-}" in
    '' | *[!0-9.]* | *.*.* | .* | *.) return 1 ;;
    esac
    return 0
}

ueber_null() {
    awk -v wert="$1" 'BEGIN { exit !(wert + 0 > 0) }'
}

[ "$#" -eq 1 ] || verweigern "ein Argument, die Box"
BOX=$1
case "$BOX" in
'' | *[!A-Za-z0-9._-]*) verweigern "box '$BOX' ist kein Name aus Buchstaben, Ziffern, Punkt, Strich" ;;
esac

DECKEL_USD=$(laufwert DECKEL_USD)
BISHER_USD=$(laufwert BISHER_USD)
SATZ_USD_H=$(laufwert SATZ_USD_H)
BOX_START_EPOCH=$(laufwert BOX_START_EPOCH)
ZELLEN=$(laufwert ZELLEN)
ABBILD_DIGEST=$(laufwert ABBILD_DIGEST)
VORPRUEFUNG=$(laufwert VORPRUEFUNG)

ist_betrag "$DECKEL_USD" && ueber_null "$DECKEL_USD" || verweigern "DECKEL_USD fehlt oder ist kein Betrag ueber 0"
ist_betrag "$BISHER_USD" || verweigern "BISHER_USD fehlt oder ist kein Betrag"
ist_betrag "$SATZ_USD_H" && ueber_null "$SATZ_USD_H" || verweigern "SATZ_USD_H fehlt oder ist kein Betrag ueber 0"
ist_zahl "$BOX_START_EPOCH" && [ "$BOX_START_EPOCH" -gt 0 ] || verweigern "BOX_START_EPOCH fehlt oder ist keine Zahl"
# Ein Start in der Zukunft verlaengerte den Deckel still.
[ "$BOX_START_EPOCH" -le $(($(date +%s) + 300)) ] || verweigern "BOX_START_EPOCH liegt in der Zukunft"
case "$ABBILD_DIGEST" in
sha256:*) hex=${ABBILD_DIGEST#sha256:} ;;
*) verweigern "ABBILD_DIGEST fehlt oder hat nicht die Form sha256:<64 Hexziffern>" ;;
esac
case "$hex" in
'' | *[!0-9a-f]*) verweigern "ABBILD_DIGEST hat nicht die Form sha256:<64 Hexziffern>" ;;
esac
[ "${#hex}" -eq 64 ] || verweigern "ABBILD_DIGEST hat nicht die Form sha256:<64 Hexziffern>"

[ -n "$ZELLEN" ] || verweigern "ZELLEN ist leer"
for eintrag in $ZELLEN; do
    felder=$(printf '%s\n' "$eintrag" | awk -F: '{print NF}')
    [ "$felder" -eq 4 ] || verweigern "Zelle '$eintrag' hat nicht die Form name:profil:praezision:korpus"
    name=$(printf '%s\n' "$eintrag" | cut -d: -f1)
    profil=$(printf '%s\n' "$eintrag" | cut -d: -f2)
    praezision=$(printf '%s\n' "$eintrag" | cut -d: -f3)
    korpus=$(printf '%s\n' "$eintrag" | cut -d: -f4)
    case "$name" in
    '' | *[!A-Za-z0-9._-]*) verweigern "Zellname '$name' ist kein Name" ;;
    esac
    case "$profil" in
    economy | standard | performance) ;;
    *) verweigern "Zelle '$name': unbekanntes Profil '$profil'" ;;
    esac
    case "$praezision" in
    int8 | fp32) ;;
    *) verweigern "Zelle '$name': unbekannte Praezision '$praezision'" ;;
    esac
    [ "$praezision" = int8 ] || [ "$profil" != economy ] || verweigern "Zelle '$name': fp32 nur mit standard oder performance"
    case "$korpus" in
    voll | teil) ;;
    *) verweigern "Zelle '$name': Korpus muss voll oder teil sein" ;;
    esac
done

if [ "$VORPRUEFUNG" != stop-ja ]; then
    echo "00-kette: die Marke VORPRUEFUNG=stop-ja fehlt; erst 00-typwechsel.sh vorpruefung, dann die Kette" >&2
    exit 80
fi

KOUT="$OUT/$BOX"
mkdir -p "$KOUT"
KETTENDATEI="$KOUT/00-kette.txt"
HERZ="$KOUT/00-herzschlag.txt"
PROTOKOLL="$KOUT/00-kette-protokoll.txt"
WORK=$(mktemp -d)
chmod 700 "$WORK"
HERZ_PID=''

aufraeumen() {
    [ -z "$HERZ_PID" ] || kill "$HERZ_PID" 2>/dev/null || true
    rm -rf "$WORK"
}
trap aufraeumen EXIT

utc() {
    date -u +%Y-%m-%dT%H:%M:%SZ
}

zeile() {
    printf '%s\n' "$*" >>"$KETTENDATEI"
    printf '%s\n' "$*"
}

kosten_jetzt() {
    awk -v bisher="$BISHER_USD" -v satz="$SATZ_USD_H" -v start="$BOX_START_EPOCH" -v jetzt="$(date +%s)" \
        'BEGIN { printf "%.4f\n", bisher + (jetzt - start) / 3600 * satz }'
}

deckel_erreicht() {
    KOSTEN=$(kosten_jetzt)
    awk -v kosten="$KOSTEN" -v deckel="$DECKEL_USD" 'BEGIN { exit !(kosten >= deckel) }'
}

# --- Der Sicherheitstimer, D-28-14 ------------------------------------------
KOSTEN=$(kosten_jetzt)
minuten=$(awk -v deckel="$DECKEL_USD" -v kosten="$KOSTEN" -v satz="$SATZ_USD_H" \
    'BEGIN { m = (1.2 * deckel - kosten) / satz * 60; if (m < 0) m = 0; printf "%d\n", m }')
zeile "kette-start $BOX $(utc) bisher $KOSTEN deckel $DECKEL_USD satz $SATZ_USD_H"
if [ "$minuten" -le 0 ]; then
    zeile "sicherheitsstopp-erreicht $(utc) bisher $KOSTEN"
    sudo shutdown -h now >/dev/null 2>&1 || true
    exit 82
fi
sudo shutdown -h +"$minuten" >/dev/null 2>&1 || true
soll=$(($(date +%s) + minuten * 60))
geplant=$(sudo cat "$GEPLANT_DATEI" 2>/dev/null | awk -F= '$1 == "USEC" {print $2; exit}' || true)
modus=$(sudo cat "$GEPLANT_DATEI" 2>/dev/null | awk -F= '$1 == "MODE" {print $2; exit}' || true)
if ! ist_zahl "$geplant"; then
    zeile "timer-unlesbar $(utc)"
    echo "00-kette: die geplante Abschaltung ist nicht zurueckzulesen, die Box hat KEINEN Sicherheitstimer" >&2
    exit 81
fi
TIMER_EPOCH=$((geplant / 1000000))
abstand=$((TIMER_EPOCH - soll))
[ "$abstand" -ge 0 ] || abstand=$((0 - abstand))
case "$modus" in
poweroff | halt) ;;
*)
    zeile "timer-falscher-modus $(utc) modus ${modus:-leer}"
    exit 81
    ;;
esac
if [ "$abstand" -gt 120 ]; then
    zeile "timer-abweichung $(utc) abstand-s $abstand"
    exit 81
fi
zeile "timer-gesetzt minuten $minuten abschaltung $(date -u -d "@$TIMER_EPOCH" +%Y-%m-%dT%H:%M:%SZ)"

abbruch_timer() {
    rest=$(((TIMER_EPOCH - $(date +%s)) / 60))
    if [ "$rest" -gt "$ABBRUCH_FRIST" ]; then
        sudo shutdown -h +"$ABBRUCH_FRIST" >/dev/null 2>&1 || true
        zeile "timer-vorgezogen $(utc) auf-minuten $ABBRUCH_FRIST"
    fi
}

# --- Der Herzschlag ----------------------------------------------------------
printf 'keine\n' >"$WORK/aktuell"
printf 'herzschlag %s zelle keine\n' "$(utc)" >"$HERZ"
(
    while :; do
        printf 'herzschlag %s zelle %s\n' "$(utc)" "$(cat "$WORK/aktuell" 2>/dev/null || echo keine)" >"$HERZ"
        sleep "$HERZ_TAKT"
    done
) >/dev/null 2>&1 </dev/null &
HERZ_PID=$!

# --- Die Zellen, mit dem Deckel vor jeder (D-28-02) --------------------------
for eintrag in $ZELLEN; do
    name=$(printf '%s\n' "$eintrag" | cut -d: -f1)
    profil=$(printf '%s\n' "$eintrag" | cut -d: -f2)
    praezision=$(printf '%s\n' "$eintrag" | cut -d: -f3)
    korpus=$(printf '%s\n' "$eintrag" | cut -d: -f4)
    if deckel_erreicht; then
        zeile "deckel-erreicht $(utc) bisher $KOSTEN"
        zeile "keine-neue-zelle $name die-box-laeuft-weiter"
        printf 'deckel-erreicht %s bisher %s naechste %s\n' "$(utc)" "$KOSTEN" "$name" >"$KOUT/00-DECKEL-ERREICHT"
        exit 83
    fi
    printf '%s\n' "$name" >"$WORK/aktuell"
    zeile "zelle-start $name $profil/$praezision korpus $korpus $(utc) bisher $KOSTEN"
    status=0
    ZELLE_KORPUS="$korpus" sh "$ZELLE_SKRIPT" "$BOX" "$name" "$profil" "$praezision" \
        >>"$PROTOKOLL" 2>&1 </dev/null || status=$?
    zeile "zelle-ende $name rueckgabe $status $(utc)"
    if [ "$status" -ne 0 ]; then
        zeile "kette-abbruch zelle $name rueckgabe $status $(utc)"
        abbruch_timer
        exit 84
    fi
done

zeile "kette-ende $(utc) bisher $(kosten_jetzt)"
sudo shutdown -h +2 >/dev/null 2>&1 || true
exit 0
