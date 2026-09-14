#!/bin/sh
# Die Cron-Vorpruefung des v1.2-Laufs. Sie ist ZWEITEILIG: ein
# Konfigurationszweig vor dem Lauf und ein Wirkungszweig waehrend des Laufs.
#
# **Warum dieser Schritt ueberhaupt existiert.** Der Vergleichslauf vom
# 10.09.2026 war 5,85 h von 26,6 h ohne Arbeitsvorrat (194 von 812 Lesungen,
# Baseline 0,10 h), weil der Zulauf am 5-Minuten-Systemcron hing, der auf der
# Box nur alle rund 12 Minuten eine Scheibe von etwa 870 Zeilen lieferte,
# waehrend die Baseline bis zu 49.601 Zeilen Vorlauf hielt
# (docs/performance.md, Zeile 158). Der Leerlauf ist damit der groesste einzelne
# Posten der Mehrlaufzeit jenes Laufs, und er ist keine Eigenschaft des
# Erzeugnisses, sondern eine der Messbedingung.
#
# **Die Lesart, die den zweiten Zweig erzwingt.** Der Systemcron stand NOMINAL
# auf fuenf Minuten. Die tatsaechliche Scheibenauslieferung lag bei rund zwoelf
# Minuten. Ein Vorpruefschritt, der nur die KONFIGURATION liest, also
# backgroundjobs_mode, den Cron-Container oder die crontab, haette am 10.09.2026
# GRUEN gemeldet, waehrend der Befund vorlag. Ein solcher Check erfuellt MESS-06
# dem Buchstaben nach und verfehlt den Befund. Deshalb hat dieses Skript zwei
# Zweige, und der zweite ist nicht optional: er misst den Abstand zwischen zwei
# Zulaufscheiben, also die Wirkung und nicht die Einstellung.
#
# **Warum die Durchsetzung im Skript steht und nicht in einer Checkliste.** Ein
# Lauf ohne protokolliertes Intervall gilt als unvollstaendig (D-07), und die
# Durchsetzung ist fail-closed (D-08): menschliche Schritte werden vergessen,
# das war die v1.1-Falle. Eine Zeile in einem Runbook haette den Befund vom
# 10.09. nicht verhindert; ein Abbruch verhindert ihn.
#
# Die Quellen, die dieser Schritt liest, in dieser Reihenfolge:
#
#   1. der Hintergrundauftrags-Modus der Instanz, ueber
#      occ config:app:get core backgroundjobs_mode. Der Sollwert ist cron
#   2. die Wartezeit der Cron-Schleife im All-in-One-Container: das Skript, das
#      cron.php in einer Schleife ruft, ist im Container lesbar, und seine
#      Schlafdauer IST der Takt
#   3. die crontab des Wirts fuer den Dienstnutzer, also der Weg, den eine
#      Installation ohne eigenen Cron-Container nimmt
#   4. der Abstand zwischen den beiden juengsten Werten von
#      occ config:app:get core lastcron, bei zwei Lesungen im Abstand von
#      SOLL_INTERVALL Sekunden. Diese Quelle ist bereits eine Messung und keine
#      Konfiguration, und sie ist die langsamste von allen; sie steht deshalb
#      zuletzt, und sie ist immer noch besser als gar keine Zahl
#   5. (nur im Zweig waehrend) der Arbeitsvorrat der PHP-Haelfte, ueber
#      occ findling:index, genau einmal je Runde
#
# Was ueber den Cron ausserdem bekannt ist und hier nicht vergessen werden darf:
# All-in-One ruft cron.php alle fuenf Minuten, und der ERSTE Auftrag der App
# reiht noch nichts ein. Zwei Runden des Systemcrons sind deshalb abzuwarten,
# bevor ein leerer Arbeitsvorrat eine Aussage ist statt eines Artefakts
# (93-nullstand.sh, Kopf; 96-volllauf.sh; 98b-sprachfaelle.sh).
#
# Die Exit-Codes setzen den Katalog dieses Laufverzeichnisses fort. 15 bis 24
# sind in 98c-sprachfaelle.sh vergeben und bleiben, was sie dort sind:
#
#   2  Aufruf ohne Zweig oder mit einem unbekannten Zweig
#   25 die Cron-Konfiguration war auf keiner der bekannten Quellen lesbar
#   26 das gelesene Intervall weicht vom Soll ab
#   27 der Wirkungszweig wurde nicht gefahren oder nicht protokolliert
#   28 der gemessene Scheibenabstand liegt ueber dem Deckel
set -eu

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: 97-cron-vorpruefung.sh <vorher|waehrend>

  vorher     Konfigurationszweig, VOR dem Lauf. Liest Modus und Takt, schreibt
             die Pflichtzeile cron-intervall-ist und bricht ab, wenn keine
             Quelle antwortet oder das Intervall vom Soll abweicht.
  waehrend   Wirkungszweig, WAEHREND des Laufs. Misst den Abstand zwischen zwei
             Zulaufscheiben und bricht ab, wenn keine Zahl entsteht oder der
             gemessene Abstand ueber dem Deckel liegt.

Ohne Zweig oder mit einem unbekannten Zweig endet dieses Skript mit 2, weil ein
Lauf ohne protokolliertes Intervall als unvollstaendig gilt (D-07).
HINWEIS
}

ZWEIG="${1:-}"
case "$ZWEIG" in
vorher | waehrend) ;;
*)
    benutzung
    exit 2
    ;;
esac

# Alles, worin sich zwei Maschinen unterscheiden koennen, ist eine Variable mit
# Vorgabe, damit diese Datei keinen Pfad einer Maschine traegt. Die erste Vorgabe
# leitet sich aus dem Ort des Skripts selbst ab, was auf der Box und in einer
# Arbeitskopie gleichermassen haelt.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
# Die Wurzel der Arbeitskopie. Dieses Skript liest sie nicht, es faehrt nur occ
# und docker; sie steht hier, weil die uebrigen Skripte dieses Laufverzeichnisses
# sie fuehren und ein Boxplan, der sie setzt, daran nicht scheitern soll.
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
# Der Container, in dem die Cron-Schleife laeuft, und das Skript darin. Beide
# Vorgaben sind eine Wette auf die Bauform von All-in-One und werden in Phase 15
# erstmals gegen eine echte Box geprueft. Antwortet die Quelle nicht, ist das
# kein Abbruch, sondern der Uebergang zur naechsten Quelle.
CRON_CONTAINER="${CRON_CONTAINER:-nextcloud-aio-nextcloud}"
CRON_SKRIPT="${CRON_SKRIPT:-/cron.sh}"
# Der Nutzer, unter dem eine Installation ohne eigenen Cron-Container ihre
# crontab fuehrt.
DIENSTNUTZER="${DIENSTNUTZER:-www-data}"
# Fuenf Minuten sind die Messbedingung aus D-07: der Anfahrt-Ablauf setzt den
# Systemcron der Messinstanz explizit auf diesen Wert und protokolliert den
# Ist-Zustand. Der Wert steht in Sekunden, damit jede Quelle in derselben
# Einheit antwortet.
SOLL_INTERVALL="${SOLL_INTERVALL:-300}"
# Die zugelassene Abweichung in Prozent. Zehn Prozent lassen die Schwankung
# eines Cron-Laufs durch, der seine eigene Arbeit noch beendet, und halten die
# zwoelf Minuten des v1.1-Befundes sicher draussen.
TOLERANZ_PROZENT="${TOLERANZ_PROZENT:-10}"

mkdir -p "$OUT"
ZIEL="${ZIEL:-$OUT/97-cron-vorpruefung-$ZWEIG.txt}"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# Der occ-Wrapper in der passwortlosen Fassung aus 93-nullstand.sh. Kein
# Passwort auf einer Kommandozeile: ein Argument steht in der Prozessliste der
# Box und in jedem Protokoll, das den Befehl aufzeichnet (T-10-27).
occ() {
    sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
}

# Die beiden Bloecke der Statusausgabe, aus EINEM Aufruf gelesen statt aus zwei:
# sie sind zwei Quellen, aber zweimal zu fragen liesse sie einander
# widersprechen (93-nullstand.sh).
vorrat_von() {
    awk '/^Work stock/ {found = 1; next}
         found && /^  (scheduled|handed to the worker)/ {sum += $NF}
         END {print sum + 0}' "$1"
}

# Jede Zeile des Protokollblocks wird gedruckt UND mitgeschrieben, damit ein
# Bericht die drei Pflichtzeilen als Block zitieren kann, statt sie aus einer
# langen Rohdatei zusammenzusuchen.
protokoll() {
    printf '%s\n' "$*" >>"$WORK/protokollblock"
    printf '%s\n' "$*"
}

# Quelle 2. Die Wette: All-in-One faehrt die Cron-Schleife in einem Container,
# dessen Skript cron.php ruft und zwischen zwei Runden schlaeft. Die Schlafdauer
# in diesem Skript IST der Takt, und sie ist eine Konfiguration und keine
# Messung.
quelle_aio_cron() {
    sudo docker exec "$CRON_CONTAINER" sh -c "cat $CRON_SKRIPT" 2>/dev/null |
        awk '{for (i = 1; i < NF; i++) if ($i == "sleep" && $(i + 1) ~ /^[0-9]+$/) {print $(i + 1); exit}}'
}

# Quelle 3. Die Wette: die Instanz haengt an der crontab des Wirts, wie jede
# Installation ohne eigenen Cron-Container. Gelesen wird die Zeile, die cron.php
# ruft, und aus ihrem Minutenfeld wird eine Sekundenzahl.
quelle_crontab() {
    sudo crontab -u "$DIENSTNUTZER" -l 2>/dev/null |
        awk '/cron\.php/ && $1 ~ /^\*\/[0-9]+$/ {sub(/^\*\//, "", $1); print $1 * 60; exit}'
}

# Quelle 4. Die Wette: die Instanz schreibt den Zeitpunkt ihres letzten
# Cron-Laufs fort, und zwei Lesungen im Abstand des Solls ergeben den Takt.
# Diese Quelle ist bereits eine MESSUNG und keine Konfiguration, und sie kostet
# SOLL_INTERVALL Sekunden. Sie steht deshalb zuletzt. Ticken die beiden Lesungen
# nicht auseinander, nennt sie keine Zahl: dass der Takt dann groesser als das
# Soll ist, weiss man, aber welche Zahl er hat, nicht.
quelle_lastcron() {
    erste=$(occ config:app:get core lastcron 2>/dev/null | tr -dc '0-9') || true
    sleep "$SOLL_INTERVALL"
    zweite=$(occ config:app:get core lastcron 2>/dev/null | tr -dc '0-9') || true
    if [ -n "${erste:-}" ] && [ -n "${zweite:-}" ] && [ "$zweite" -gt "$erste" ]; then
        printf '%s\n' "$((zweite - erste))"
    fi
}

if [ "$ZWEIG" = vorher ]; then
    {
        date -u +'cron-vorpruefung-vorher-start %Y-%m-%dT%H:%M:%SZ'
        printf 'soll-intervall %s s, toleranz %s prozent\n' "$SOLL_INTERVALL" "$TOLERANZ_PROZENT"

        echo "=== 1. Der Hintergrundauftrags-Modus der Instanz ==="
        echo "-- Sollwert cron. ajax und webcron takten nach Besuchern und nicht nach einer Uhr --"
        modus=$(occ config:app:get core backgroundjobs_mode 2>/dev/null | tr -d ' \t') || true
        [ -n "${modus:-}" ] || modus=unlesbar
        protokoll "cron-modus-ist $modus"

        echo "=== 2. Das Intervall, aus den bekannten Quellen der Reihe nach ==="
        quelle=keine
        intervall=

        echo "-- Quelle aio-cron-container: die Schlafdauer der Cron-Schleife im Container --"
        intervall=$(quelle_aio_cron || true)
        if [ -n "${intervall:-}" ]; then
            quelle=aio-cron-container
        else
            echo "   (der Container oder das Skript darin ist nicht lesbar, weiter zur naechsten Quelle)"
            echo "-- Quelle wirts-crontab: die Zeile des Dienstnutzers, die cron.php ruft --"
            intervall=$(quelle_crontab || true)
            if [ -n "${intervall:-}" ]; then
                quelle=wirts-crontab
            else
                echo "   (keine cron.php-Zeile in der crontab, weiter zur letzten und langsamsten Quelle)"
                echo "-- Quelle lastcron-abstand: zwei Lesungen im Abstand von $SOLL_INTERVALL s --"
                echo "   (das ist bereits eine Messung und keine Konfiguration, aber besser als gar keine Zahl)"
                intervall=$(quelle_lastcron || true)
                if [ -n "${intervall:-}" ]; then
                    quelle=lastcron-abstand
                else
                    echo "   (die beiden Lesungen sind nicht auseinandergetickt: der Takt ist groesser"
                    echo "    als $SOLL_INTERVALL s, welche Zahl er hat, sagt diese Quelle nicht)"
                fi
            fi
        fi

        echo "=== 3. Das Ergebnis, als Pflichtzeile des Messprotokolls ==="
        protokoll "cron-intervall-quelle $quelle"
        if [ -n "${intervall:-}" ]; then
            protokoll "cron-intervall-ist $intervall"
            printf '%s\n' "$intervall" >"$WORK/cron-intervall"
        else
            protokoll "cron-intervall-ist unlesbar"
            printf 'unlesbar\n' >"$WORK/cron-intervall"
        fi

        echo "=== 4. Das Soll setzen und zuruecklesen, statt es nur zu pruefen ==="
        echo "-- D-07 verlangt, dass der Ablauf den Systemcron der Messinstanz EXPLIZIT auf"
        echo "   fuenf Minuten setzt. Das Setzen ist ein Handgriff auf der Box und steht hier"
        echo "   als Befehl, nicht als Behauptung: --"
        printf 'cron-soll-setzen-befehl sudo crontab -u %s -e, Minutenfeld der cron.php-Zeile auf */%s setzen\n' \
            "$DIENSTNUTZER" "$((SOLL_INTERVALL / 60))"
        printf 'cron-soll-setzen-befehl-aio Schlafdauer in %s:%s auf %s setzen und den Container neu starten\n' \
            "$CRON_CONTAINER" "$CRON_SKRIPT" "$SOLL_INTERVALL"
        echo "-- DIESER SCHRITT IST IN PHASE 15 ERSTMALS VOLLZOGEN. Bis dahin ist er gelesen"
        echo "   und nicht gefahren, und dieses Skript tut nicht so, als waere er es. --"
        echo "-- Die Ruecklesung fragt die beiden Konfigurationsquellen erneut. Die dritte"
        echo "   Quelle wird nicht wiederholt: sie ist eine Messung und kostet ihre Frist ein"
        echo "   zweites Mal, ohne eine Konfiguration zurueckzulesen. --"
        zurueck=$(quelle_aio_cron || true)
        [ -n "${zurueck:-}" ] || zurueck=$(quelle_crontab || true)
        [ -n "${zurueck:-}" ] || zurueck=unlesbar
        printf 'cron-soll-ruecklesung %s\n' "$zurueck"

        echo "=== 5. Der Protokollblock, als Block zitierbar ==="
        cat "$WORK/protokollblock"

        date -u +'cron-vorpruefung-vorher-ende %Y-%m-%dT%H:%M:%SZ'
    } 2>&1 | tee "$ZIEL"
else
    {
        date -u +'cron-vorpruefung-waehrend-start %Y-%m-%dT%H:%M:%SZ'
        echo "Der Wirkungszweig entsteht in Aufgabe 2 dieses Plans."
        date -u +'cron-vorpruefung-waehrend-ende %Y-%m-%dT%H:%M:%SZ'
    } 2>&1 | tee "$ZIEL"
fi

# Alles Folgende steht UNTERHALB der Pipeline, und nur dort. Der Rueckgabewert
# einer Pipeline, die in tee endet, gehoert zu tee; ein Abbruch innerhalb des
# Blocks verliesse nur die Subshell, und die Verweigerung waere eine Zeile in
# einer Rohdatei, die niemand liest. Gelesen wird deshalb aus der Arbeitsdatei
# und nicht aus der Pipeline (Muster aus 93-nullstand.sh und 98c-sprachfaelle.sh).
if [ "$ZWEIG" = vorher ]; then
    gelesen=$(cat "$WORK/cron-intervall" 2>/dev/null || echo unlesbar)
    case "$gelesen" in
    '' | *[!0-9]*)
        echo "97-cron-vorpruefung: keine der bekannten Quellen hat ein Cron-Intervall genannt" >&2
        echo "97-cron-vorpruefung: ein Lauf ohne protokolliertes Intervall gilt als unvollstaendig (D-07)" >&2
        exit 25
        ;;
    esac
    untere=$((SOLL_INTERVALL * (100 - TOLERANZ_PROZENT) / 100))
    obere=$((SOLL_INTERVALL * (100 + TOLERANZ_PROZENT) / 100))
    if [ "$gelesen" -lt "$untere" ] || [ "$gelesen" -gt "$obere" ]; then
        echo "97-cron-vorpruefung: das gelesene Intervall $gelesen s liegt nicht zwischen $untere und $obere s" >&2
        echo "97-cron-vorpruefung: die Messbedingung aus D-07 ist damit nicht hergestellt" >&2
        exit 26
    fi
fi

echo "97-CRON-VORPRUEFUNG-FERTIG"
