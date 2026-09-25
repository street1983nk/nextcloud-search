#!/bin/sh
# Der Ablauf der v1.3-Anfahrt (Phase 22), unbeaufsichtigt, mit hartem Stopp.
#
# **DIESE FASSUNG IST NICHT GEFAHREN.** Keine Rohdatei liegt neben ihr; was sie
# auf der Box faehrt, faehrt sie auf der Anfahrt.
#
# Warum es dieses Skript gibt. Die Box laeuft allein, waehrend die Haertung der
# Phase 23 lokal laeuft. Drei Dinge duerfen deshalb nicht im Gedaechtnis eines
# Operators liegen, sondern muessen Code sein:
#
#   1. Der Deckel (D-01) und der harte Stopp (D-02). Beim Start setzt dieses
#      Skript sudo shutdown -h +<Restminuten>, gerechnet aus DECKEL_MINUTEN und
#      BOX_START_EPOCH, und liest die geplante Abschaltung zurueck. Ohne
#      Ruecklesung laeuft keine Messung (55). Ein Herunterfahren aus dem
#      Betriebssystem ist ein Stopp und kein Terminate; das beweist
#      00-typwechsel.sh vorpruefung VOR dem Start, auf der Entwicklungsmaschine.
#   2. Die Streichreihenfolge (D-05). B7 laeuft nie auf der Box (CI). Vor B2, B3,
#      B5 und B4 fragt zeit_fuer, ob Planminuten plus Reserve bis zur Abschaltung
#      reichen; B5 faellt vor B4, B4 vor B2 und B3. Die Pflichtbloecke der
#      Erfolgskriterien 2 und 3 und B1 haben KEINE Zeitpruefung: sie sind der
#      Zweck der Phase, und reicht die Zeit fuer sie nicht, stoppt der Timer.
#   3. Die Trennung von BL-F03 und BL-F04. Kein BL-F04-Block aendert eine
#      Umgebungsvariable des Produktcontainers. Die einzigen Neubauten ueber
#      92e-umgebung.sh sind die Entladefrist 120 fuer den Bodensatz, die Frist 0
#      zurueck, und die sechs Sprachen fuer MESS-08. Die OCR-Sprachen bleiben
#      unangetastet, sonst waere B2 nicht mit dem 07.09. vergleichbar.
#
# Unterbefehle:
#
#   start [ablauf|b4]   startet den Ablauf (oder b4) abgesetzt ueber setsid
#                       nohup, voll umgeleitet nach rohdaten/00-lauf-protokoll.txt
#   ablauf              der ganze Ablauf im Vordergrund (start ruft diesen)
#   status              letzte Blockzeile, geplante Abschaltung, Streichungen
#   b4                  nach dem Typwechsel auf m7g.4xlarge: Timer aus
#                       DECKEL_REST_MINUTEN neu, alle Container anhalten,
#                       00-wegwerf.sh b4, B4-FERTIG, Abschaltung
#
# Die Laufwerte stehen in einer Datei ausserhalb des Repos, LAUFWERTE, Vorgabe
# $HOME/work/v13-lauf.env, Rechte 600, eine Zeile NAME=WERT je Wert. Gelesen
# werden nur diese Namen, und die Datei wird nicht ausgefuehrt:
#
#   DECKEL_MINUTEN       der Deckel der ganzen Anfahrt in Minuten (Rechenblatt)
#   BOX_START_EPOCH      date +%s beim ersten Start der Box
#   B4_GEPLANT           ja oder nein (D-03, aus F4 der CI-Kurve)
#   EINZELWEG            a (37 des Snapshots) oder b (Vollreindex, 92c zuerst)
#   ABBILD_DIGEST        sha256:<64 Hexziffern>, das gemessene Abbild
#   DECKEL_REST_MINUTEN  nur fuer b4: die Restminuten nach dem Typwechsel
#   PWFILE               Passwortdatei des Administrators (Vorgabe unten)
#   PWFILE_LASTTEST      Passwortdatei des Lastkontos (Vorgabe unten)
#
# Kein Passwort steht in dieser Datei, auf einer Kommandozeile oder in einer
# Rohdatei: die Werkzeuge lesen ihre Passwortdatei selbst, und fuer die
# Laststufen wird das Passwort des Lastkontos nur in der Umgebung einer
# Subshell gesetzt, damit 99d nachweislich ohne es laeuft (E7).
#
# Zur Pipeline-Regel des Verzeichnisses (Pattern 4). Der Rueckgabewert einer
# Pipeline gehoert zu tee, und ein exit in einem Block, der in tee endet,
# verliesse nur die Subshell. Dieses Skript hat deshalb gar keine tee-Pipeline
# um seine Bloecke: jeder Block laeuft in der Hauptshell, seine Ausgabe geht
# ueber die Umleitung von start nach 00-lauf-protokoll.txt, und jeder
# Tor-Abbruch ist ein exit der Hauptshell. Die Arbeitsdateien liegen unter WORK
# (700). Endet der Lauf anders als ueber seinen Abschluss, schreibt die
# EXIT-Falle die Zeile 00-abbruch mit dem Rueckgabewert, meldet ueber
# 96e-ntfy-watch.sh und zieht den Timer auf ABBRUCH_FRIST Minuten vor, damit
# eine haltende Box nicht bis zum Deckel Geld kostet.
#
# Rueckgabewerte dieses Skripts (Katalog in 00-ablauf.md, Abschnitt 4):
#
#   2   Aufruf oder Laufwerte unvollstaendig, vor der ersten Zeile
#   54  das v1.2- oder das Nachfolgeverzeichnis im Box-Klon ist nicht sauber
#   55  die geplante Abschaltung ist nicht zurueckzulesen, oder der Deckel ist
#       beim Start schon erreicht
#   56  nach B2 kehrt der Bestand nicht auf den Stand vor B2 zurueck
#   57  die Gegenprobe von M-01 findet im Kaltstart-Fenster keine Zeile
#   58  der Umbau (oder der Vollreindex in Weg b) laeuft in die Frist vor dem
#       Timer, oder embedded bewegt sich waehrend des Umbaus
#   sonst der Rueckgabewert des Werkzeugs, dessen Tor gerissen ist (36 bis 45)
#
# ASCII, weil die Box ihr Gebietsschema nicht garantiert.
set -eu

SKRIPTE=$(cd "$(dirname "$0")" && pwd)
LAUF=$(cd "$SKRIPTE/.." && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
# Einmal gesetzt und exportiert: jedes Werkzeug schreibt hierher, und kein
# Werkzeug der v1.2 schreibt in sein eigenes Verzeichnis (T-22-19).
OUT="$LAUF/rohdaten"
export OUT

WERKZEUGE="${WERKZEUGE:-$REPO/docs/measurements/2026-09-v12-messung/skripte}"
NACHFOLGE="${NACHFOLGE:-$REPO/docs/measurements/2026-09-nachfolgefassungen/skripte}"
ALT_V12="docs/measurements/2026-09-v12-messung"
ALT_NACHFOLGE="docs/measurements/2026-09-nachfolgefassungen"
CPU_SAMPLER="${CPU_SAMPLER:-$REPO/scripts/ops/cpu_sampler.sh}"
RSS_SAMPLER="${RSS_SAMPLER:-$REPO/scripts/ops/rss_sampler.sh}"
ANON_SAMPLER="${ANON_SAMPLER:-$REPO/scripts/ops/proc_anon_sampler.sh}"
LAST="${LAST:-$REPO/scripts/ops/search_load.py}"
MELDEKETTE="${MELDEKETTE:-$WERKZEUGE/96e-ntfy-watch.sh}"
LAUFWERTE="${LAUFWERTE:-$HOME/work/v13-lauf.env}"
# Wo systemd die geplante Abschaltung ablegt (USEC, MODE); die Ruecklesung liest
# diese Datei und nicht die Ausgabe des Befehls, der sie setzt.
GEPLANT_DATEI="${GEPLANT_DATEI:-/run/systemd/shutdown/scheduled}"
# Die Abholmarke, die 00-abholen.sh auf der Entwicklungsmaschine per ssh setzt.
ABGEHOLT="${ABGEHOLT:-$HOME/work/abgeholt}"
ABHOL_WARTE="${ABHOL_WARTE:-1500}"
ABBRUCH_FRIST="${ABBRUCH_FRIST:-60}"
GRUB_DROPIN="${GRUB_DROPIN:-/etc/default/grub.d/99-mem4g.cfg}"

CONTAINER="${CONTAINER:-nc_app_findling_backend}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
ADRESSE="${ADRESSE:-https://loadtest.infranode.dev}"
BENUTZER="${BENUTZER:-admin}"
KONTO="${KONTO:-lasttest}"
UEBERSICHT="${UEBERSICHT:-/apps/findling/admin/overview}"
ABBILD_REPO="${ABBILD_REPO:-ghcr.io/street1983nk/findling_backend}"
DATA_ROOT="${DATA_ROOT:-/mnt/findling}"
VOLUME="${VOLUME:-$DATA_ROOT/docker/volumes/nc_app_findling_backend_data/_data}"
DATENBANK="${DATENBANK:-$VOLUME/state.db}"

# Die Takte. 5 s fuer B1 wie die Speicherreihe der v1.2, 1 s fuer W2 in B2,
# 30 s fuer die Statusreihe des Umbaus, 60 s fuer den Platz.
ABTASTTAKT="${ABTASTTAKT:-5}"
ANON_TAKT="${ANON_TAKT:-1}"
UMBAU_TAKT="${UMBAU_TAKT:-30}"
PLATZ_TAKT="${PLATZ_TAKT:-60}"
STUFEN="${STUFEN:-1 4 8 12 16}"
RUNDEN="${RUNDEN:-10}"
PAUSE="${PAUSE:-20}"

# B2: 120 einseitige und 20 achtseitige synthetische Scans, der Seed fest.
B2_EINSEITIG="${B2_EINSEITIG:-120}"
B2_ACHTSEITIG="${B2_ACHTSEITIG:-20}"
B2_SEED="${B2_SEED:-phase-22-b2}"
B2_ORDNER="${B2_ORDNER:-mess22-b2}"
B2_DECKEL="${B2_DECKEL:-2400}"
B2_RUECKKEHR_FRIST="${B2_RUECKKEHR_FRIST:-1800}"
# Der Bestand des Snapshots, das Tor von 92d; in Weg b gilt der Stand vor B2.
BESTAND_SNAPSHOT="52111 37 0"
VOLLREINDEX_TAKT="${VOLLREINDEX_TAKT:-120}"
VOLLREINDEX_RUHE="${VOLLREINDEX_RUHE:-8}"

# Die Erwartung E1 aus 00-ablauf.md, Abschnitt 3: die Marken des Snapshots
# gegen die Konstanten des Codes. schema_version und languages sind Marken, die
# der Umbau beantwortet; ihre Abweichung ist erwartet und kein Befund.
ERWARTUNG_ANALYZER="analyzer_version=1"
ERWARTUNG_INDEX="index_version=1"
ERWARTUNG_STORE="store_schema_version=2"
ERWARTUNG_SCHEMA="schema_version=2"
ERWARTUNG_WORTLISTE="wordlist_hash=b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0"
ERWARTUNG_TANTIVY="tantivy_version=tantivy v0.26.2, index_format v7"
ERWARTUNG_VEKTOREN="embedding_version=multilingual-e5-small/int8/384/1024"
ERWARTUNG_SPRACHEN="languages=de,en"

# Planminuten und Reserven, aus dem Rechenblatt-Entwurf der Research. zeit_fuer
# rechnet mit ihnen gegen die zurueckgelesene Abschaltung.
PLAN_B2=45
PLAN_B3=15
PLAN_B5=12
PLAN_B4=75
PLAN_UMBAU=180
PLAN_98D=20
PLAN_ENDE=15
PLAN_92C=30
PLAN_ABHOLEN=20

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: ./00-lauf.sh start [ablauf|b4] | ablauf | status | b4

  start    startet den Ablauf (oder b4) abgesetzt, voll umgeleitet
  ablauf   der Ablauf im Vordergrund, Weg a oder b nach EINZELWEG
  status   letzte Blockzeile, geplante Abschaltung, gestrichene Bloecke
  b4       nach dem Typwechsel: Timer aus DECKEL_REST_MINUTEN, Container
           anhalten, 00-wegwerf.sh b4, B4-FERTIG, Abschaltung

Die Laufwerte stehen in LAUFWERTE (Vorgabe $HOME/work/v13-lauf.env, Rechte 600):
DECKEL_MINUTEN, BOX_START_EPOCH, B4_GEPLANT (ja|nein), EINZELWEG (a|b),
ABBILD_DIGEST (sha256:<64 Hexziffern>), fuer b4 DECKEL_REST_MINUTEN.
HINWEIS
}

verweigern() {
    echo "00-lauf: $1" >&2
    benutzung
    exit 2
}

BEFEHL="${1:-}"
ZIELBEFEHL=''
case "$BEFEHL" in
start)
    ZIELBEFEHL="${2:-ablauf}"
    case "$ZIELBEFEHL" in
    ablauf | b4) ;;
    *) verweigern "start kennt nur ablauf und b4, nicht '$ZIELBEFEHL'" ;;
    esac
    ;;
ablauf | b4 | status) ZIELBEFEHL=$BEFEHL ;;
*) verweigern "ohne bekannten Unterbefehl laeuft nichts" ;;
esac

# Eine Zeile NAME=WERT aus der Laufwertedatei, ohne sie auszufuehren.
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

digest_pruefen() {
    case "$ABBILD_DIGEST" in
    sha256:*) hex=${ABBILD_DIGEST#sha256:} ;;
    *) verweigern "ABBILD_DIGEST fehlt oder hat nicht die Form sha256:<64 Hexziffern>" ;;
    esac
    case "$hex" in
    '' | *[!0-9a-f]*) verweigern "ABBILD_DIGEST hat nicht die Form sha256:<64 Hexziffern>" ;;
    esac
    [ "${#hex}" -eq 64 ] || verweigern "ABBILD_DIGEST hat nicht die Form sha256:<64 Hexziffern>"
}

DECKEL_MINUTEN=$(laufwert DECKEL_MINUTEN)
BOX_START_EPOCH=$(laufwert BOX_START_EPOCH)
B4_GEPLANT=$(laufwert B4_GEPLANT)
EINZELWEG=$(laufwert EINZELWEG)
ABBILD_DIGEST=$(laufwert ABBILD_DIGEST)
DECKEL_REST_MINUTEN=$(laufwert DECKEL_REST_MINUTEN)
PWFILE_ADMIN=$(laufwert PWFILE)
PWFILE_LAST=$(laufwert PWFILE_LASTTEST)
# Die beiden Passwortdateien der Box, wie in 94c und 99d.
PWFILE_ADMIN="${PWFILE_ADMIN:-$HOME/work/.pw/admin}"
PWFILE_LAST="${PWFILE_LAST:-$HOME/work/.pw/lasttest}"

case "$ZIELBEFEHL" in
ablauf)
    ist_zahl "$DECKEL_MINUTEN" && [ "$DECKEL_MINUTEN" -gt 0 ] ||
        verweigern "DECKEL_MINUTEN fehlt in $LAUFWERTE oder ist keine Zahl ueber 0"
    ist_zahl "$BOX_START_EPOCH" && [ "$BOX_START_EPOCH" -gt 0 ] ||
        verweigern "BOX_START_EPOCH fehlt in $LAUFWERTE oder ist keine Zahl"
    # Ein Start in der Zukunft verlaengerte den Deckel still.
    [ "$BOX_START_EPOCH" -le $(($(date +%s) + 300)) ] ||
        verweigern "BOX_START_EPOCH liegt in der Zukunft"
    case "$B4_GEPLANT" in
    ja | nein) ;;
    *) verweigern "B4_GEPLANT muss ja oder nein sein" ;;
    esac
    case "$EINZELWEG" in
    a | b) ;;
    *) verweigern "EINZELWEG muss a oder b sein" ;;
    esac
    digest_pruefen
    ;;
b4)
    ist_zahl "$DECKEL_REST_MINUTEN" && [ "$DECKEL_REST_MINUTEN" -gt 0 ] ||
        verweigern "DECKEL_REST_MINUTEN fehlt in $LAUFWERTE oder ist keine Zahl ueber 0"
    digest_pruefen
    ;;
esac

utc() {
    date -u +%Y-%m-%dT%H:%M:%SZ
}

LAUFDATEI="$OUT/00-lauf.txt"
PROTOKOLL="$OUT/00-lauf-protokoll.txt"

if [ "$BEFEHL" = status ]; then
    if [ -f "$LAUFDATEI" ]; then
        printf 'letzte-blockzeile %s\n' "$(tail -1 "$LAUFDATEI")"
    else
        echo "letzte-blockzeile keine, der Lauf hat nicht begonnen"
    fi
    if [ -f "$OUT/00-timer.txt" ]; then
        printf 'timer %s\n' "$(tail -1 "$OUT/00-timer.txt")"
    fi
    if [ -s "$OUT/00-gestrichen.txt" ]; then
        cat "$OUT/00-gestrichen.txt"
    else
        echo "gestrichen keine"
    fi
    exit 0
fi

if [ "$BEFEHL" = start ]; then
    mkdir -p "$OUT"
    # Voll umgeleitet und abgesetzt, Muster 96-volllauf.sh: ein Hintergrund-
    # prozess, der die Ausgabe dieser Shell offen hielte, haelte die ssh-Sitzung
    # des Operators fest.
    setsid nohup sh "$SKRIPTE/00-lauf.sh" "$ZIELBEFEHL" >>"$PROTOKOLL" 2>&1 </dev/null &
    printf '00-lauf %s abgesetzt, pid %s, protokoll %s\n' "$ZIELBEFEHL" "$!" "$PROTOKOLL"
    echo "00-LAUF-GESTARTET"
    exit 0
fi

mkdir -p "$OUT"
WORK=$(mktemp -d)
chmod 700 "$WORK"
: >"$WORK/abtaster.pids"
AKTUELLER_BLOCK=vorlauf
LEBEN=0
DURCH_SIGNAL=nein

occ() {
    sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
}

lauf_zeile() {
    printf '%s\n' "$*" >>"$LAUFDATEI"
    printf '%s\n' "$*"
}

block_betreten() {
    AKTUELLER_BLOCK=$1
    lauf_zeile "$1-start $(utc)"
}

block_verlassen() {
    lauf_zeile "$1-ende $(utc)"
}

melden() {
    KENNUNG="Findling 22 v1.3-Anfahrt" sh "$MELDEKETTE" senden "$1" "$2" "${3:-default}" \
        >/dev/null 2>&1 || true
}

# Ein Tor ist gerissen. Die Zeile und die Meldung; der exit steht beim Aufrufer,
# damit jeder Abbruchwert im Code als eigene Zeile lesbar ist.
tor_melden() {
    lauf_zeile "tor-abbruch $AKTUELLER_BLOCK rueckgabe $1 grund $2 $(utc)"
    : >"$WORK/tor-gemeldet"
    melden "v1.3 Tor-Abbruch $1" "Block $AKTUELLER_BLOCK: $2. Der Timer wird auf $ABBRUCH_FRIST min vorgezogen." high
}

# Ein Befund ist kein Abbruch: der Block hat keine Zahl oder eine rote Zahl
# geliefert, der Zustand der Box ist aber der erwartete, und die folgenden
# Pflichtbloecke messen weiter.
befund() {
    lauf_zeile "befund $AKTUELLER_BLOCK $1 $(utc)"
    melden "v1.3 Befund $AKTUELLER_BLOCK" "$1" default
}

# --- Der Timer, D-01 und D-02 ------------------------------------------------

rest_bis_deckel() {
    jetzt=$(date +%s)
    printf '%s\n' "$((DECKEL_MINUTEN - (jetzt - BOX_START_EPOCH) / 60))"
}

# Setzt die Abschaltung auf +MINUTEN und liest sie zurueck. Ohne Ruecklesung
# gibt es keinen Deckel, und ohne Deckel laeuft keine Messung.
timer_setzen() {
    rest=$1
    if [ "$rest" -le 0 ]; then
        printf 'timer-deckel-erreicht %s rest %s\n' "$(utc)" "$rest" >>"$OUT/00-timer.txt"
        tor_melden 55 "der Deckel ist beim Start schon erreicht"
        sudo shutdown -h now >/dev/null 2>&1 || true
        exit 55
    fi
    sudo shutdown -h +"$rest" >/dev/null 2>&1 || true
    soll=$(($(date +%s) + rest * 60))
    geplant=$(sudo cat "$GEPLANT_DATEI" 2>/dev/null | awk -F= '$1 == "USEC" {print $2; exit}' || true)
    modus=$(sudo cat "$GEPLANT_DATEI" 2>/dev/null | awk -F= '$1 == "MODE" {print $2; exit}' || true)
    if ! ist_zahl "$geplant"; then
        printf 'timer-unlesbar %s datei %s\n' "$(utc)" "$GEPLANT_DATEI" >>"$OUT/00-timer.txt"
        tor_melden 55 "die geplante Abschaltung ist nicht zurueckzulesen, die Box hat KEINEN Deckel"
        exit 55
    fi
    TIMER_EPOCH=$((geplant / 1000000))
    abstand=$((TIMER_EPOCH - soll))
    [ "$abstand" -ge 0 ] || abstand=$((0 - abstand))
    case "$modus" in
    poweroff | halt) ;;
    *)
        printf 'timer-falscher-modus %s modus %s\n' "$(utc)" "${modus:-leer}" >>"$OUT/00-timer.txt"
        tor_melden 55 "die geplante Abschaltung ist kein Herunterfahren (${modus:-leer})"
        exit 55
        ;;
    esac
    if [ "$abstand" -gt 120 ]; then
        printf 'timer-abweichung %s abstand-s %s\n' "$(utc)" "$abstand" >>"$OUT/00-timer.txt"
        tor_melden 55 "die geplante Abschaltung liegt $abstand s neben dem Deckel"
        exit 55
    fi
    printf '%s\n' "$TIMER_EPOCH" >"$WORK/timer-epoch"
    printf 'timer-gesetzt %s rest-minuten %s modus %s\n' "$(utc)" "$rest" "$modus" >>"$OUT/00-timer.txt"
    printf 'timer-abschaltung %s\n' "$(date -u -d "@$TIMER_EPOCH" +%Y-%m-%dT%H:%M:%SZ)" >>"$OUT/00-timer.txt"
    lauf_zeile "timer-abschaltung $(date -u -d "@$TIMER_EPOCH" +%Y-%m-%dT%H:%M:%SZ)"
}

rest_bis_timer() {
    ende=$(cat "$WORK/timer-epoch" 2>/dev/null || echo 0)
    printf '%s\n' "$(((ende - $(date +%s)) / 60))"
}

# Ein Abbruch soll die Box nicht bis zum Deckel halten. Der Timer wird auf
# ABBRUCH_FRIST Minuten vorgezogen, wenn er spaeter laege; der Operator kann in
# dieser Frist eingreifen (sudo shutdown -c).
abbruch_timer() {
    rest=$(rest_bis_timer)
    if [ "$rest" -gt "$ABBRUCH_FRIST" ]; then
        sudo shutdown -h +"$ABBRUCH_FRIST" >/dev/null 2>&1 || true
        printf 'timer-vorgezogen %s auf-minuten %s\n' "$(utc)" "$ABBRUCH_FRIST" >>"$OUT/00-timer.txt"
    fi
}

# --- Die Streichlogik, D-05 --------------------------------------------------

# Die Reserve, die nach einem Block fuer die Bloecke bleiben muss, die im Rang
# ueber ihm stehen und noch kommen. B2 und B3 reservieren B4 NICHT, weil B4 vor
# ihnen faellt; B5 reserviert B4 und B3, weil B5 vor beiden faellt (D-05).
reserve_fuer() {
    case "$EINZELWEG" in
    a) pflicht_92c=$PLAN_92C ;;
    *) pflicht_92c=0 ;;
    esac
    b4_teil=0
    [ "$B4_GEPLANT" != ja ] || b4_teil=$PLAN_B4
    b3_teil=$PLAN_B3
    [ ! -f "$WORK/b3-gefahren" ] || b3_teil=0
    case "$1" in
    b2) printf '%s\n' "$((PLAN_UMBAU + PLAN_98D + PLAN_ENDE + pflicht_92c + PLAN_ABHOLEN))" ;;
    b3) printf '%s\n' "$((PLAN_ENDE + pflicht_92c + PLAN_ABHOLEN))" ;;
    b5) printf '%s\n' "$((PLAN_ENDE + pflicht_92c + PLAN_ABHOLEN + b4_teil + b3_teil))" ;;
    b4) printf '%s\n' "$PLAN_ABHOLEN" ;;
    esac
}

# zeit_fuer BLOCK PLANMINUTEN RESERVEMINUTEN: 0, wenn beides bis zur
# Abschaltung passt; sonst die Streichzeile und 1.
zeit_fuer() {
    rest=$(rest_bis_timer)
    bedarf=$(($2 + $3))
    if [ "$rest" -lt "$bedarf" ]; then
        printf 'gestrichen %s rest %s bedarf %s\n' "$1" "$rest" "$bedarf" >>"$OUT/00-gestrichen.txt"
        lauf_zeile "gestrichen $1 rest $rest bedarf $bedarf $(utc)"
        melden "v1.3 gestrichen $1" "Rest $rest min, Bedarf $bedarf min (Plan $2, Reserve $3). D-05." default
        return 1
    fi
    lauf_zeile "zeit-fuer $1 rest $rest bedarf $bedarf"
    return 0
}

# --- Die Waechter der Altverzeichnisse ---------------------------------------

altverzeichnisse_pruefen() {
    schmutz=$(git -C "$REPO" status --porcelain -- "$ALT_V12" "$ALT_NACHFOLGE" 2>&1) ||
        schmutz="git-status-fehlgeschlagen"
    if [ -n "$schmutz" ]; then
        printf '%s\n' "$schmutz" >"$WORK/altverzeichnisse.txt"
        lauf_zeile "altverzeichnisse-sauber nein $(utc)"
        tor_melden 54 "das v1.2- oder das Nachfolgeverzeichnis im Box-Klon ist nicht sauber"
        exit 54
    fi
    lauf_zeile "altverzeichnisse-sauber ja"
}

# --- B1, die Abtaster je Containerleben (Pitfall 4) ---------------------------

abtaster_stoppen() {
    while read -r pid; do
        [ -n "$pid" ] || continue
        sudo kill -TERM "$pid" 2>/dev/null || true
    done <"$WORK/abtaster.pids"
    : >"$WORK/abtaster.pids"
}

# Jeder Neubau und jeder Neustart gibt dem Container eine neue cgroup, und ein
# Abtaster, der die alte loest, endet mit seiner Schlusszeile. Deshalb je
# Containerleben eine eigene Datei fuer W1 und fuer rss_sampler.sh.
abtaster_neu() {
    abtaster_stoppen
    LEBEN=$((LEBEN + 1))
    cpu="$OUT/b1-cpu-$LEBEN-$1.csv"
    rss="$OUT/b1-rss-$LEBEN-$1.csv"
    setsid nohup sudo sh "$CPU_SAMPLER" "$CONTAINER" "$ABTASTTAKT" "$cpu" \
        >"$OUT/b1-cpu-$LEBEN-$1.log" 2>&1 </dev/null &
    printf '%s\n' "$!" >>"$WORK/abtaster.pids"
    setsid nohup sudo sh "$RSS_SAMPLER" "$CONTAINER" "$ABTASTTAKT" "$rss" \
        >"$OUT/b1-rss-$LEBEN-$1.log" 2>&1 </dev/null &
    printf '%s\n' "$!" >>"$WORK/abtaster.pids"
    start=$(sudo docker inspect --format '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || echo unlesbar)
    lauf_zeile "abtaster leben $LEBEN nach $1 containerstart $start $(utc)"
}

# --- Gemeinsame Leser --------------------------------------------------------

vorrat_von() {
    awk '/^Work stock/ {found = 1; next}
         found && /^  (scheduled|handed to the worker)/ {sum += $NF}
         END {print sum + 0}' "$1"
}

zahl_oder_unlesbar() {
    if ist_zahl "${1:-}"; then
        printf '%s\n' "$1"
    else
        printf 'unlesbar\n'
    fi
}

# Der Bestand als "indexiert uebersprungen fehlgeschlagen". indexiert aus der
# state.db des laufenden Containers, read-only, weil die PHP-Haelfte diese Zahl
# nie schreibt; die beiden anderen aus occ findling:index (wie 92d, Schritt 17).
bestand_lesen() {
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
    occ findling:index >"$WORK/bestand.txt" 2>&1 || true
    uebersprungen=$(awk '$1 == "skipped" {print $2; exit}' "$WORK/bestand.txt")
    fehlgeschlagen=$(awk '$1 == "failed" {print $2; exit}' "$WORK/bestand.txt")
    printf '%s %s %s\n' "$(zahl_oder_unlesbar "$indexiert")" \
        "$(zahl_oder_unlesbar "$uebersprungen")" "$(zahl_oder_unlesbar "$fehlgeschlagen")"
}

groesse_von() {
    wert=$(sudo du -sb "$1" 2>/dev/null | awk '{print $1}' || true)
    zahl_oder_unlesbar "$wert"
}

# Das Passwort des Administrators ohne Zeilenumbruch in eine Datei 600, und eine
# curl-Konfiguration daneben. Beides unter WORK, beides nie auf eine
# Kommandozeile.
PWFELD="$WORK/pwfeld"
CURLRC="$WORK/curlrc"
JAR="$WORK/cookies.txt"
zugang_bauen() {
    : >"$PWFELD"
    chmod 600 "$PWFELD"
    sudo cat "$PWFILE_ADMIN" 2>/dev/null | tr -d '\n' >"$PWFELD" || true
    : >"$CURLRC"
    chmod 600 "$CURLRC"
    {
        printf 'user = "%s:' "$BENUTZER"
        cat "$PWFELD"
        printf '"\n'
    } >"$CURLRC"
}

anmelden() {
    rm -f "$JAR"
    curl -sfS -c "$JAR" -o "$WORK/login.html" "$ADRESSE/login" || return 1
    zeichen=$(sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' "$WORK/login.html" | head -1)
    [ -n "${zeichen:-}" ] || return 1
    weiter=$(curl -sS -b "$JAR" -c "$JAR" -o /dev/null -w '%{redirect_url}' \
        -H "Origin: $ADRESSE" \
        --data-urlencode "user=$BENUTZER" \
        --data-urlencode "password@$PWFELD" \
        --data-urlencode "requesttoken=$zeichen" \
        "$ADRESSE/login" || true)
    case "$weiter" in
    '' | */login | */login\?*) return 1 ;;
    esac
    curl -sfS -b "$JAR" -c "$JAR" -o "$WORK/nach-anmeldung.html" "$ADRESSE/settings/admin" || return 1
    zeichen=$(sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' "$WORK/nach-anmeldung.html" | head -1)
    [ -n "${zeichen:-}" ] || return 1
    printf '%s\n' "$zeichen" >"$WORK/zeichen"
    return 0
}

# Die Admin-Seite als eine Zeile JSON mit den fuenf Feldern der Umbaureihe.
# Findet der Leser kein Feld, meldet er sich einmal neu an.
statuszeile() {
    for versuch in 1 2; do
        zeichen=$(cat "$WORK/zeichen" 2>/dev/null || true)
        : >"$WORK/uebersicht.json"
        if [ -n "${zeichen:-}" ]; then
            curl -sS -b "$JAR" -c "$JAR" -H 'Accept: application/json' \
                -H "requesttoken: $zeichen" -o "$WORK/uebersicht.json" \
                "$ADRESSE$UEBERSICHT" 2>/dev/null || : >"$WORK/uebersicht.json"
        fi
        zeile=$(python3 - "$WORK/uebersicht.json" "$(utc)" <<'PY' || true
import json
import sys

FELDER = ("rebuildRunning", "rebuildDone", "rebuildTotal", "languagesActive", "embedded")


def finden(knoten, name):
    if isinstance(knoten, dict):
        if name in knoten:
            return knoten[name]
        for wert in knoten.values():
            treffer = finden(wert, name)
            if treffer is not None:
                return treffer
    if isinstance(knoten, list):
        for wert in knoten:
            treffer = finden(wert, name)
            if treffer is not None:
                return treffer
    return None


try:
    with open(sys.argv[1], encoding="utf-8") as datei:
        daten = json.load(datei)
except (OSError, ValueError):
    daten = {}
zeile = {"zeit": sys.argv[2]}
for feld in FELDER:
    zeile[feld] = finden(daten, feld)
print(json.dumps(zeile, sort_keys=True))
PY
)
        case "$zeile" in
        *'"embedded": null'*'"rebuildDone": null'* | '')
            [ "$versuch" -eq 1 ] && anmelden || true
            ;;
        *)
            printf '%s\n' "$zeile"
            return 0
            ;;
        esac
    done
    if [ -n "${zeile:-}" ]; then
        printf '%s\n' "$zeile"
    else
        printf '{"zeit": "%s"}\n' "$(utc)"
    fi
}

feld_von() {
    printf '%s\n' "$1" | python3 -c '
import json
import sys
wert = json.loads(sys.stdin.read() or "{}").get(sys.argv[1])
print("unlesbar" if wert is None else str(wert).lower())
' "$2" 2>/dev/null || printf 'unlesbar\n'
}

# 97-cron-vorpruefung.sh waehrend neben einem Block, abgesetzt. Sein
# Rueckgabewert ist ein Befund ueber den Takt und kein Tor dieses Laufs.
cron_waehrend_starten() {
    (
        rc=0
        ZIEL="$OUT/97-cron-vorpruefung-waehrend-$1.txt" sh "$WERKZEUGE/97-cron-vorpruefung.sh" waehrend \
            >"$WORK/97-waehrend-$1.log" 2>&1 || rc=$?
        printf '%s\n' "$rc" >"$WORK/97-waehrend-$1.rc"
    ) </dev/null &
    printf '%s\n' "$!" >"$WORK/97-waehrend-$1.pid"
}

cron_waehrend_beenden() {
    pid=$(cat "$WORK/97-waehrend-$1.pid" 2>/dev/null || true)
    if [ -f "$WORK/97-waehrend-$1.rc" ]; then
        lauf_zeile "97-waehrend-$1-rueckgabewert $(cat "$WORK/97-waehrend-$1.rc")"
    else
        [ -z "${pid:-}" ] || kill -TERM "$pid" 2>/dev/null || true
        lauf_zeile "97-waehrend-$1 beendet-durch-lauf $(utc)"
    fi
}

# Ein Neubau ueber 92e mit genau einem Schalter. Danach neue Abtaster.
neubau_92e() {
    rc=0
    sh "$SKRIPTE/92e-umgebung.sh" "$1" || rc=$?
    lauf_zeile "92e $1 rueckgabewert $rc"
    if [ "$rc" -ne 0 ]; then
        tor_melden "$rc" "92e-umgebung.sh $1 ist gescheitert, der Produktcontainer ist in keinem benannten Zustand"
        exit "$rc"
    fi
    abtaster_neu "$2"
}

# --- Die Bloecke -------------------------------------------------------------

block_marken() {
    block_betreten p0-marken
    rc=0
    sudo python3 "$SKRIPTE/90e-einzelliste.py" marken --database "$DATENBANK" \
        --erwartung "$ERWARTUNG_ANALYZER" --erwartung "$ERWARTUNG_INDEX" \
        --erwartung "$ERWARTUNG_STORE" --erwartung "$ERWARTUNG_SCHEMA" \
        --erwartung "$ERWARTUNG_WORTLISTE" --erwartung "$ERWARTUNG_TANTIVY" \
        --erwartung "$ERWARTUNG_VEKTOREN" --erwartung "$ERWARTUNG_SPRACHEN" \
        >"$OUT/90e-marken.txt" 2>&1 || rc=$?
    cat "$OUT/90e-marken.txt"
    lauf_zeile "90e-marken-rueckgabewert $rc"
    if [ "$rc" -ne 0 ]; then
        tor_melden "$rc" "das Markentor (44 Index, 45 Vektorspur) ist gerissen, kein Wechsel"
        exit "$rc"
    fi
    block_verlassen p0-marken
}

block_einzelliste() {
    block_betreten einzelliste
    rc=0
    sudo python3 "$SKRIPTE/90e-einzelliste.py" liste --database "$DATENBANK" \
        >"$OUT/$1" 2>"$WORK/einzelliste.err" || rc=$?
    lauf_zeile "90e-liste-rueckgabewert $rc datei $1"
    if [ "$rc" -ne 0 ]; then
        tor_melden "$rc" "die Einzelliste ist nicht lesbar"
        exit "$rc"
    fi
    block_verlassen einzelliste
}

block_92d() {
    block_betreten p1-92d
    rc=0
    ABBILD_DIGEST="$ABBILD_DIGEST" sh "$SKRIPTE/92d-wechsel.sh" || rc=$?
    lauf_zeile "92d-rueckgabewert $rc"
    if [ "$rc" -ne 0 ]; then
        tor_melden "$rc" "der Wechsel 92d ist gescheitert (36 bis 41)"
        exit "$rc"
    fi
    abtaster_neu 92d
    block_verlassen p1-92d
}

block_cron_vorher() {
    block_betreten cron-vorher
    rc=0
    sh "$WERKZEUGE/97-cron-vorpruefung.sh" vorher || rc=$?
    lauf_zeile "97-vorher-rueckgabewert $rc"
    if [ "$rc" -ne 0 ]; then
        tor_melden "$rc" "der Cron-Konfigurationszweig ist gerissen (25, 26)"
        exit "$rc"
    fi
    block_verlassen cron-vorher
}

indexgroesse() {
    block_betreten "indexgroesse-$1"
    {
        printf 'indexgroesse-%s %s\n' "$1" "$(utc)"
        printf 'index-bytes %s\n' "$(groesse_von "$VOLUME/index")"
        printf 'index-rebuild-bytes %s\n' "$(groesse_von "$VOLUME/index.rebuild")"
        printf 'bestand %s\n' "$(bestand_lesen)"
    } | tee "$OUT/indexgroesse-$1.txt"
    block_verlassen "indexgroesse-$1"
}

nextcloud_log_holen() {
    pfad=$(occ config:system:get logfile 2>/dev/null || true)
    if [ -z "${pfad:-}" ]; then
        daten=$(occ config:system:get datadirectory 2>/dev/null || true)
        pfad="${daten:-/mnt/ncdata}/nextcloud.log"
    fi
    sudo docker exec "$NEXTCLOUD" cat "$pfad" >"$WORK/nextcloud.log" 2>/dev/null || : >"$WORK/nextcloud.log"
}

# M-01, die Laststufen unter loglevel 1, dann der Kaltstart als Gegenprobe.
block_m01() {
    block_betreten m01
    M01="$OUT/m01-langsame-aufrufe.txt"
    loglevel_vorher=$(occ config:system:get loglevel 2>/dev/null || true)
    printf 'loglevel-vorher %s %s\n' "${loglevel_vorher:-ungesetzt}" "$(utc)" | tee -a "$M01"
    occ config:system:set loglevel --value=1 --type=integer >/dev/null 2>&1 || true
    printf 'loglevel-waehrend %s\n' "$(occ config:system:get loglevel 2>/dev/null || echo unlesbar)" | tee -a "$M01"

    for stufe in $STUFEN; do
        von=$(utc)
        lauf_zeile "m01-stufe-$stufe-von $von"
        (
            FINDLING_LOAD_PASSWORD=$(sudo cat "$PWFILE_LAST" 2>/dev/null || true)
            export FINDLING_LOAD_PASSWORD
            sudo -E python3 "$LAST" \
                --base-url "$ADRESSE" --user "$KONTO" --password-env FINDLING_LOAD_PASSWORD \
                --concurrency "$stufe" --rounds "$RUNDEN" --container "$CONTAINER" \
                >"$OUT/m01-stufe-$stufe.json" 2>"$OUT/m01-stufe-$stufe.err" || true
        )
        bis=$(utc)
        lauf_zeile "m01-stufe-$stufe-bis $bis"
        nextcloud_log_holen
        python3 "$SKRIPTE/91m-langsame-aufrufe.py" --log "$WORK/nextcloud.log" \
            --von "$von" --bis "$bis" --stufe "$stufe" >>"$M01" 2>&1 || true
        sleep "$PAUSE"
    done

    rc=0
    PWFILE="$PWFILE_ADMIN" sh "$SKRIPTE/95c-kaltstart.sh" || rc=$?
    lauf_zeile "95c-rueckgabewert $rc"
    abtaster_neu kaltstart
    fenster=$(awk '$1 == "kaltstart-fenster" {print $2, $3}' "$OUT/95c-kaltstart.txt" 2>/dev/null | tail -1 || true)
    gegenprobe=unklar
    if [ -n "${fenster:-}" ]; then
        nextcloud_log_holen
        python3 "$SKRIPTE/91m-langsame-aufrufe.py" --log "$WORK/nextcloud.log" \
            --von "${fenster% *}" --bis "${fenster#* }" --stufe kaltstart >"$WORK/kaltstart-91m.txt" 2>&1 || true
        cat "$WORK/kaltstart-91m.txt" >>"$M01"
        gegenprobe=$(awk '$1 == "stufe" && $2 == "kaltstart" {print $4; exit}' "$WORK/kaltstart-91m.txt")
    fi

    if [ -n "${loglevel_vorher:-}" ]; then
        occ config:system:set loglevel --value="$loglevel_vorher" --type=integer >/dev/null 2>&1 || true
    else
        occ config:system:delete loglevel >/dev/null 2>&1 || true
    fi
    printf 'loglevel-danach %s %s\n' "$(occ config:system:get loglevel 2>/dev/null || echo ungesetzt)" "$(utc)" |
        tee -a "$M01"

    if [ "$rc" -ne 0 ]; then
        befund "95c endete mit $rc, die Kaltstartlatenz hat keine gueltige erste Suche; M-01-Gegenprobe nicht entschieden"
    else
        printf 'm01-gegenprobe kaltstart langsame-aufrufe %s\n' "${gegenprobe:-unklar}" | tee -a "$M01"
        case "${gegenprobe:-unklar}" in
        '' | 0 | unklar)
            tor_melden 57 "die Gegenprobe von M-01 findet im Kaltstart-Fenster keine Zeile (Level oder Leser falsch)"
            exit 57
            ;;
        esac
    fi
    block_verlassen m01
}

block_bodensatz() {
    block_betreten bodensatz
    neubau_92e FINDLING_EMBED_IDLE_RELEASE_SECONDS=120 ttl-120
    rc_94c=0
    PWFILE="$PWFILE_ADMIN" sh "$SKRIPTE/94c-bodensatz-zyklen.sh" || rc_94c=$?
    lauf_zeile "94c-rueckgabewert $rc_94c"
    abtaster_neu bodensatz
    # Die Frist geht in jedem Fall auf 0 zurueck, auch nach einem Befund in 94c,
    # denn jede folgende Messung laeuft unter 0 wie die v1.2.
    neubau_92e FINDLING_EMBED_IDLE_RELEASE_SECONDS=0 ttl-0
    [ "$rc_94c" -eq 0 ] || befund "94c endete mit $rc_94c, der Bodensatz hat keine Zahl"
    block_verlassen bodensatz
}

block_99d() {
    block_betreten 99d
    # E7: 99d liest sein Passwort aus PWFILE, und der Beweis ist ein Lauf, in
    # dessen Umgebung die Variable nicht steht. Der Wert wird nie gedruckt.
    unset FINDLING_LOAD_PASSWORD 2>/dev/null || true
    lastvariable=ungesetzt
    [ -z "${FINDLING_LOAD_PASSWORD:-}" ] || lastvariable=gesetzt
    lauf_zeile "99d-umgebung FINDLING_LOAD_PASSWORD $lastvariable"
    rc=0
    PWFILE="$PWFILE_LAST" sh "$NACHFOLGE/99d-filter-sortierung.sh" || rc=$?
    lauf_zeile "99d-rueckgabewert $rc"
    [ "$rc" -eq 0 ] || befund "99d endete mit $rc"
    block_verlassen 99d
}

b2_scans_bauen() {
    mkdir -p "$WORK/b2-scans"
    sudo docker run --rm -i --network none --cpuset-cpus 0 --user "$(id -u):$(id -g)" \
        -e PYTHONDONTWRITEBYTECODE=1 \
        -e PYTHONPATH=/repo/scripts/dev \
        -e B2_SEED="$B2_SEED" -e B2_EINSEITIG="$B2_EINSEITIG" -e B2_ACHTSEITIG="$B2_ACHTSEITIG" \
        -v "$REPO/scripts/dev:/repo/scripts/dev:ro" \
        -v "$REPO/testdata/fonts:/repo/testdata/fonts:ro" \
        -v "$WORK/b2-scans:/scan" \
        --entrypoint /app/.venv/bin/python "$ABBILD_REPO@$ABBILD_DIGEST" - <<'PY'
import os

import build_load_corpus as corpus

seed = os.environ["B2_SEED"]
for nummer in range(int(os.environ["B2_EINSEITIG"])):
    with open(f"/scan/b2-einseitig-{nummer:03d}.pdf", "wb") as datei:
        datei.write(corpus._scan_pdf(corpus.Rng(seed, f"einseitig-{nummer}"), 1))
for nummer in range(int(os.environ["B2_ACHTSEITIG"])):
    with open(f"/scan/b2-achtseitig-{nummer:02d}.pdf", "wb") as datei:
        datei.write(corpus._scan_pdf(corpus.Rng(seed, f"achtseitig-{nummer}"), 8))
PY
}

# B2, die OCR-Charge im Produkt, nach dem Muster von 71-ocrphase.sh: synthetische
# Scans ueber WebDAV, files:scan, W2 mit 1 s, der Cron-Wirkungszweig daneben,
# Beobachtung bis Vorrat 0, dann Ordner loeschen und Rueckkehr des Bestands.
block_b2() {
    block_betreten b2
    B2="$OUT/b2-ocr-charge.txt"
    soll=$1
    lauf_zeile "b2-bestand-soll $soll"
    rc=0
    b2_scans_bauen || rc=$?
    anzahl=$(find "$WORK/b2-scans" -name 'b2-*.pdf' | wc -l | tr -d ' ')
    erwartet=$((B2_EINSEITIG + B2_ACHTSEITIG))
    printf 'b2-scans %s von %s seiten %s\n' "$anzahl" "$erwartet" "$((B2_EINSEITIG + 8 * B2_ACHTSEITIG))" | tee "$B2"
    if [ "$rc" -ne 0 ] || [ "$anzahl" -ne "$erwartet" ]; then
        befund "B2 hat keine vollstaendige Charge gebaut ($anzahl von $erwartet)"
        block_verlassen b2
        return 0
    fi

    setsid nohup sudo sh "$ANON_SAMPLER" "$CONTAINER" "$ANON_TAKT" "$OUT/b2-anon.csv" \
        >"$OUT/b2-anon.log" 2>&1 </dev/null &
    anon_pid=$!
    cron_waehrend_starten b2

    basis="$ADRESSE/remote.php/dav/files/$BENUTZER"
    curl -sS -o /dev/null -K "$CURLRC" -X MKCOL "$basis/$B2_ORDNER" || true
    printf 'b2-upload-vor %s\n' "$(utc)" | tee -a "$B2"
    : >"$WORK/b2-upload.txt"
    for pfad in "$WORK/b2-scans"/b2-*.pdf; do
        name=$(basename "$pfad")
        code=$(curl -sS -o /dev/null -w '%{http_code}' -K "$CURLRC" -T "$pfad" "$basis/$B2_ORDNER/$name" || echo 000)
        printf '%s %s\n' "$code" "$name" >>"$WORK/b2-upload.txt"
    done
    printf 'b2-upload-nach %s hochgeladen %s von %s\n' "$(utc)" \
        "$(awk '$1 ~ /^2/ {n++} END {print n + 0}' "$WORK/b2-upload.txt")" "$erwartet" | tee -a "$B2"
    occ files:scan --path="/$BENUTZER/files/$B2_ORDNER" 2>&1 | tail -4 || true

    beginn=$(date +%s)
    gesehen=nein
    null_in_folge=0
    while [ $(($(date +%s) - beginn)) -le "$B2_DECKEL" ]; do
        sleep 15
        occ findling:index >"$WORK/b2-status.txt" 2>&1 || true
        vorrat=$(vorrat_von "$WORK/b2-status.txt")
        printf 'b2-lesung %s vorrat %s\n' "$(utc)" "$vorrat" >>"$B2"
        if [ "$vorrat" -gt 0 ]; then
            gesehen=ja
            null_in_folge=0
        elif [ "$gesehen" = ja ]; then
            null_in_folge=$((null_in_folge + 1))
            [ "$null_in_folge" -lt 2 ] || break
        fi
    done
    printf 'b2-vorrat-null %s gesehen %s\n' "$(utc)" "$gesehen" | tee -a "$B2"
    sudo kill -TERM "$anon_pid" 2>/dev/null || true
    cron_waehrend_beenden b2

    curl -sS -o /dev/null -K "$CURLRC" -X DELETE "$basis/$B2_ORDNER" || true
    printf 'b2-ordner-geloescht %s\n' "$(utc)" | tee -a "$B2"
    beginn=$(date +%s)
    ist=unlesbar
    while [ $(($(date +%s) - beginn)) -le "$B2_RUECKKEHR_FRIST" ]; do
        ist=$(bestand_lesen)
        printf 'b2-rueckkehr %s bestand %s\n' "$(utc)" "$ist" >>"$B2"
        [ "$ist" != "$soll" ] || break
        sleep 30
    done
    printf 'b2-rueckkehr-ende %s bestand %s soll %s\n' "$(utc)" "$ist" "$soll" | tee -a "$B2"
    if [ "$ist" != "$soll" ]; then
        tor_melden 56 "nach B2 steht der Bestand auf $ist statt $soll"
        exit 56
    fi
    block_verlassen b2
}

# MESS-08: der Umbau auf sechs Sprachen, beobachtet bis zur Logzeile.
block_umbau() {
    block_betreten p2-umbau
    UMBAU="$OUT/umbau-status.jsonl"
    PLATZ="$OUT/umbau-platz.txt"
    neubau_92e FINDLING_LANGUAGES=de,en,es,it,nl,pt umbau
    start=$(sudo docker inspect --format '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || true)
    lauf_zeile "umbau-containerstart ${start:-unlesbar}"
    cron_waehrend_starten umbau
    anmelden || true
    frist=$(($(cat "$WORK/timer-epoch") - PLAN_ABHOLEN * 60))
    embedded_erst=''
    runde=0
    ende=''
    platz_alle=$((PLATZ_TAKT / UMBAU_TAKT))
    [ "$platz_alle" -ge 1 ] || platz_alle=1
    while :; do
        jetzt=$(date +%s)
        if [ "$jetzt" -ge "$frist" ]; then
            : >"$WORK/umbau-frist"
            break
        fi
        zeile=$(statuszeile)
        printf '%s\n' "$zeile" >>"$UMBAU"
        eingebettet=$(feld_von "$zeile" embedded)
        if ist_zahl "$eingebettet"; then
            if [ -z "$embedded_erst" ]; then
                embedded_erst=$eingebettet
            elif [ "$eingebettet" != "$embedded_erst" ]; then
                printf 'embedded-bewegt %s von %s auf %s\n' "$(utc)" "$embedded_erst" "$eingebettet" >>"$PLATZ"
                : >"$WORK/umbau-vektorspur"
                break
            fi
        fi
        if [ $((runde % platz_alle)) -eq 0 ]; then
            printf 'platz %s index %s index.rebuild %s\n' "$(utc)" \
                "$(groesse_von "$VOLUME/index")" "$(groesse_von "$VOLUME/index.rebuild")" >>"$PLATZ"
        fi
        if [ -n "${start:-}" ]; then
            ende=$(sudo docker logs --timestamps --since "$start" "$CONTAINER" 2>&1 |
                grep -m1 'the rebuilt index directory is in place' | awk '{print $1}' || true)
            [ -z "${ende:-}" ] || break
        fi
        runde=$((runde + 1))
        sleep "$UMBAU_TAKT"
    done
    cron_waehrend_beenden umbau
    printf '%s\n' "$(statuszeile)" >>"$UMBAU"
    if [ -n "${ende:-}" ] && [ -n "${start:-}" ]; then
        von=$(date -u -d "$start" +%s 2>/dev/null || echo '')
        bis=$(date -u -d "$ende" +%s 2>/dev/null || echo '')
        if ist_zahl "$von" && ist_zahl "$bis"; then
            lauf_zeile "umbau-wandzeit-s $((bis - von)) von $start bis $ende"
        else
            lauf_zeile "umbau-wandzeit-s unbestimmt von $start bis $ende"
        fi
    fi
    printf 'platz-nachher %s index %s index.rebuild %s\n' "$(utc)" \
        "$(groesse_von "$VOLUME/index")" "$(groesse_von "$VOLUME/index.rebuild")" >>"$PLATZ"
    if [ -f "$WORK/umbau-vektorspur" ]; then
        tor_melden 58 "embedded hat sich waehrend des Umbaus bewegt, die Umbauzeit ist keine reine Umbauzeit"
        exit 58
    fi
    if [ -f "$WORK/umbau-frist" ]; then
        tor_melden 58 "der Umbau hat die Frist vor dem Timer erreicht"
        exit 58
    fi
    block_verlassen p2-umbau
    indexgroesse sechs-felder
}

block_98d() {
    block_betreten 98d
    rc=0
    sudo docker cp "$SKRIPTE/98d-dismax-probe.py" "$CONTAINER:/tmp/98d-dismax-probe.py" || rc=$?
    sudo docker cp "$REPO/scripts/dev/build_load_corpus.py" "$CONTAINER:/tmp/build_load_corpus.py" || rc=$?
    if [ "$rc" -eq 0 ]; then
        sudo docker exec -e WORTLISTE=/tmp/build_load_corpus.py "$CONTAINER" \
            /app/.venv/bin/python /tmp/98d-dismax-probe.py \
            >"$OUT/98d-dismax-probe.txt" 2>"$WORK/98d.err" || rc=$?
    fi
    lauf_zeile "98d-rueckgabewert $rc fehlerzeilen $(wc -l <"$WORK/98d.err" 2>/dev/null | tr -d ' ' || echo 0)"
    [ "$rc" -eq 0 ] || befund "98d endete mit $rc (2 kein Index oder keine Wortliste, 49 ungleiche Treffermenge)"
    block_verlassen 98d
}

block_b3() {
    block_betreten b3
    rc=0
    ABBILD_DIGEST="$ABBILD_DIGEST" PWFILE="$PWFILE_ADMIN" sh "$SKRIPTE/00-wegwerf.sh" b3 || rc=$?
    lauf_zeile "b3-rueckgabewert $rc"
    : >"$WORK/b3-gefahren"
    [ "$rc" -eq 0 ] || befund "00-wegwerf.sh b3 endete mit $rc"
    block_verlassen b3
}

block_b5() {
    block_betreten b5
    rc=0
    ABBILD_DIGEST="$ABBILD_DIGEST" PWFILE="$PWFILE_ADMIN" sh "$SKRIPTE/00-wegwerf.sh" b5 || rc=$?
    lauf_zeile "b5-rueckgabewert $rc"
    [ "$rc" -eq 0 ] || befund "00-wegwerf.sh b5 endete mit $rc"
    block_verlassen b5
}

block_endmessungen() {
    block_betreten endmessungen
    rc=0
    sh "$WERKZEUGE/90-bestand.sh" || rc=$?
    lauf_zeile "90-bestand-rueckgabewert $rc"
    [ "$rc" -eq 0 ] || befund "90-bestand.sh endete mit $rc"
    block_verlassen endmessungen
}

# Die Wirkungsnachmessung von 92c, zwei Laeufe. Der erste mit einem Daemon, den
# es nicht gibt: erwartet ist 36 und "registrierung-gelungen nein". Der zweite
# regulaer: erwartet ist 0. Beide leeren das Volumen, deshalb in Weg a zuletzt.
# Danach 93-nullstand.sh als Gegenprobe des geleerten Volumens und als Anstoss
# des Arbeitsvorrats.
block_92c() {
    block_betreten 92c
    rc=0
    ABBILD_DIGEST="$ABBILD_DIGEST" DAEMON=nicht-vorhanden ZIEL="$OUT/92c-wechsel-fehlschlag.txt" \
        sh "$NACHFOLGE/92c-wechsel.sh" || rc=$?
    lauf_zeile "92c-fehlschlag-rueckgabewert $rc erwartet 36"
    [ "$rc" -eq 36 ] || befund "92c mit einem Daemon, den es nicht gibt, endete mit $rc statt 36"
    rc=0
    ABBILD_DIGEST="$ABBILD_DIGEST" sh "$NACHFOLGE/92c-wechsel.sh" || rc=$?
    lauf_zeile "92c-regulaer-rueckgabewert $rc erwartet 0"
    [ "$rc" -eq 0 ] || befund "92c regulaer endete mit $rc statt 0"
    abtaster_neu 92c
    rc=0
    sh "$WERKZEUGE/93-nullstand.sh" || rc=$?
    lauf_zeile "93-nullstand-rueckgabewert $rc"
    [ "$rc" -eq 0 ] || befund "93-nullstand.sh endete mit $rc"
    block_verlassen 92c
}

# Weg b: nach 92c der Vollreindex beider Spuren, bis der Vorrat ruht und
# embedded steht. Die Frist ist die vor dem Timer.
block_vollreindex() {
    block_betreten vollreindex
    VOLL="$OUT/vollreindex-status.txt"
    anmelden || true
    frist=$(($(cat "$WORK/timer-epoch") - PLAN_ABHOLEN * 60))
    ruhe=0
    eingebettet_vorher=''
    while :; do
        if [ "$(date +%s)" -ge "$frist" ]; then
            tor_melden 58 "der Vollreindex hat die Frist vor dem Timer erreicht"
            exit 58
        fi
        occ findling:index >"$WORK/voll-status.txt" 2>&1 || true
        vorrat=$(vorrat_von "$WORK/voll-status.txt")
        eingebettet=$(feld_von "$(statuszeile)" embedded)
        printf 'vollreindex-lesung %s vorrat %s embedded %s\n' "$(utc)" "$vorrat" "$eingebettet" >>"$VOLL"
        if [ "$vorrat" -eq 0 ] && [ "$eingebettet" = "$eingebettet_vorher" ]; then
            ruhe=$((ruhe + 1))
        else
            ruhe=0
        fi
        eingebettet_vorher=$eingebettet
        [ "$ruhe" -lt "$VOLLREINDEX_RUHE" ] || break
        sleep "$VOLLREINDEX_TAKT"
    done
    printf 'vollreindex-ende %s bestand %s\n' "$(utc)" "$(bestand_lesen)" | tee -a "$VOLL"
    block_verlassen vollreindex
}

b4_vorbereiten() {
    block_betreten b4-vorbereitung
    sudo rm -f "$GRUB_DROPIN"
    sudo update-grub >"$WORK/update-grub.txt" 2>&1 || befund "update-grub ist gescheitert"
    lauf_zeile "b4-vorbereitet grub-dropin-entfernt $([ -e "$GRUB_DROPIN" ] && echo nein || echo ja)"
    block_verlassen b4-vorbereitung
}

# Wartet auf die Abholmarke, die juenger ist als die Endmarke, hoechstens
# ABHOL_WARTE Sekunden. Ein harter Stopp soll nichts kosten, was schon auf der
# Box lag.
abholung_abwarten() {
    marke=$(awk '{for (i = 1; i < NF; i++) if ($i == "epoch") {print $(i + 1); exit}}' "$1" 2>/dev/null || true)
    ist_zahl "$marke" || marke=$(date +%s)
    grenze=$(($(date +%s) + ABHOL_WARTE))
    while [ "$(date +%s)" -lt "$grenze" ]; do
        abgeholt=$(cat "$ABGEHOLT" 2>/dev/null || true)
        if ist_zahl "$abgeholt" && [ "$abgeholt" -gt "$marke" ]; then
            printf 'abholung-bestaetigt %s\n' "$(utc)"
            return 0
        fi
        sleep 30
    done
    printf 'abholung-nicht-bestaetigt %s nach %s s\n' "$(utc)" "$ABHOL_WARTE"
    return 0
}

abschluss() {
    block_betreten abschluss
    abtaster_stoppen
    altverzeichnisse_pruefen
    b4_zustand=nicht-geplant
    if [ "$B4_GEPLANT" = ja ]; then
        if zeit_fuer b4 "$PLAN_B4" "$(reserve_fuer b4)"; then
            b4_vorbereiten
            b4_zustand=vorbereitet
        else
            b4_zustand=gestrichen
        fi
    fi
    block_verlassen abschluss
    printf 'fertig %s epoch %s weg %s b4 %s\n' "$(utc)" "$(date +%s)" "$EINZELWEG" "$b4_zustand" >"$OUT/00-FERTIG"
    : >"$WORK/fertig"
    melden "v1.3 Ablauf fertig" "Weg $EINZELWEG, B4 $b4_zustand. Die Box wartet auf die Abholung und schaltet dann ab." default
    abholung_abwarten "$OUT/00-FERTIG"
    sudo shutdown -h now >/dev/null 2>&1 || true
}

weg_a() {
    block_marken
    block_einzelliste 90e-einzelliste.json
    block_92d
    block_cron_vorher
    indexgroesse de-en
    block_m01
    block_bodensatz
    block_99d
    if zeit_fuer b2 "$PLAN_B2" "$(reserve_fuer b2)"; then
        block_b2 "$BESTAND_SNAPSHOT"
    fi
    block_umbau
    block_98d
    if zeit_fuer b3 "$PLAN_B3" "$(reserve_fuer b3)"; then
        block_b3
    fi
    if zeit_fuer b5 "$PLAN_B5" "$(reserve_fuer b5)"; then
        block_b5
    fi
    block_endmessungen
    block_92c
}

weg_b() {
    block_92c
    block_vollreindex
    block_einzelliste 90e-einzelliste-nach-vollreindex.json
    block_cron_vorher
    indexgroesse de-en
    block_m01
    block_bodensatz
    block_99d
    if zeit_fuer b2 "$PLAN_B2" "$(reserve_fuer b2)"; then
        block_b2 "$(bestand_lesen)"
    fi
    block_umbau
    block_98d
    if zeit_fuer b3 "$PLAN_B3" "$(reserve_fuer b3)"; then
        block_b3
    fi
    if zeit_fuer b5 "$PLAN_B5" "$(reserve_fuer b5)"; then
        block_b5
    fi
    block_endmessungen
}

# --- Die Fallen --------------------------------------------------------------

signal_abbruch() {
    DURCH_SIGNAL=ja
    printf '00-abbruch-durch-signal %s\n' "$(utc)" >>"$LAUFDATEI"
    exit 143
}

beim_ende() {
    rc=$?
    set +e
    if [ ! -f "$WORK/fertig" ]; then
        printf '00-abbruch %s block %s rueckgabe %s\n' "$(utc)" "$AKTUELLER_BLOCK" "$rc" >>"$LAUFDATEI"
        printf '00-abbruch %s block %s rueckgabe %s\n' "$(utc)" "$AKTUELLER_BLOCK" "$rc" >"$OUT/00-ABBRUCH"
        abtaster_stoppen
        if [ ! -f "$WORK/tor-gemeldet" ]; then
            melden "v1.3 Abbruch $rc" "Block $AKTUELLER_BLOCK endete unerwartet mit $rc." high
        fi
        [ "$DURCH_SIGNAL" = ja ] || abbruch_timer
    fi
    rm -rf "$WORK"
}

trap beim_ende EXIT
trap signal_abbruch TERM

zugang_bauen

if [ "$BEFEHL" = b4 ]; then
    block_betreten b4-timer
    timer_setzen "$DECKEL_REST_MINUTEN"
    block_verlassen b4-timer
    altverzeichnisse_pruefen
    block_betreten b4
    # Die Restart-Policy hat nach dem Typwechsel alle Container der Box
    # gestartet; B4 misst auf einer leeren Maschine (Pitfall 8).
    laufende=$(sudo docker ps -q)
    if [ -n "$laufende" ]; then
        # Ein Container, der sich nicht anhalten laesst, faellt in 00-wegwerf.sh
        # als 51 auf; das Anhalten selbst beendet den Lauf nicht.
        # shellcheck disable=SC2086
        sudo docker stop $laufende >/dev/null || true
    fi
    lauf_zeile "b4-container-angehalten $(printf '%s\n' "$laufende" | grep -c . || true)"
    lauf_zeile "b4-kernel-mem $(tr ' ' '\n' </proc/cmdline | awk -F= '$1 == "mem" {print $2; f = 1} END {if (!f) print "ungesetzt"}')"
    rc=0
    ABBILD_DIGEST="$ABBILD_DIGEST" sh "$SKRIPTE/00-wegwerf.sh" b4 || rc=$?
    lauf_zeile "b4-rueckgabewert $rc"
    block_verlassen b4
    printf 'b4-fertig %s epoch %s rueckgabe %s\n' "$(utc)" "$(date +%s)" "$rc" >"$OUT/B4-FERTIG"
    : >"$WORK/fertig"
    melden "v1.3 B4 fertig" "00-wegwerf.sh b4 endete mit $rc. Die Box wartet auf die Abholung und schaltet dann ab." default
    abholung_abwarten "$OUT/B4-FERTIG"
    sudo shutdown -h now >/dev/null 2>&1 || true
    exit 0
fi

# Der Ablauf. Der Timer steht vor jedem Messblock.
block_betreten p0-timer
timer_setzen "$(rest_bis_deckel)"
block_verlassen p0-timer
altverzeichnisse_pruefen
lauf_zeile "lauf weg $EINZELWEG b4-geplant $B4_GEPLANT abbild $ABBILD_DIGEST"
melden "v1.3 Ablauf gestartet" "Weg $EINZELWEG, B4 $B4_GEPLANT, Abschaltung $(date -u -d "@$(cat "$WORK/timer-epoch")" +%H:%MZ)." default
abtaster_neu start

case "$EINZELWEG" in
a) weg_a ;;
b) weg_b ;;
esac

abschluss
