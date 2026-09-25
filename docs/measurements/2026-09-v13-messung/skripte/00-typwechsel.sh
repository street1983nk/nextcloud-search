#!/bin/sh
# Der Typwechsel der Messbox fuer B4 und die Vorpruefung des harten Stopps, v1.3.
#
# NIE AUF DER BOX AUSFUEHREN. Dieses Werkzeug laeuft nur auf der
# Entwicklungsmaschine; die AWS-Zugangsdaten duerfen die Box nie erreichen.
#
# DIESE FASSUNG IST NICHT GEFAHREN. Neben ihr liegt keine Rohdatei. Ihr
# Abnahmekriterium ist Form, statische Analyse und ein Lauf gegen eine
# nachgestellte AWS-Kommandozeile in backend/tests/test_v13_wegwerf.py.
#
# **Vier Unterbefehle.**
#
#   vorpruefung  liest instanceInitiatedShutdownBehavior der Box. Der harte
#                Stopp der Anfahrt (D-02) ist ein shutdown -h aus der Box
#                heraus, und der ist nur dann ein Stopp, wenn dieser Wert stop
#                heisst; bei terminate waeren Volume und Korpus weg (Annahme A2).
#                Jeder andere Wert endet mit 52, und die Anfahrt mit Timer
#                beginnt nicht.
#   hin          Vorpruefung, dann aws_box.sh stop, modify-instance-attribute
#                auf m7g.4xlarge, aws_box.sh start, Typ zurueckgelesen.
#                Scheitert der Start an der Kapazitaet, dasselbe mit
#                m7g.2xlarge und der Zeile b4-rueckfall m7g.2xlarge; scheitert
#                auch das, zurueck auf m7g.large, die Zeile b4-entfallen
#                kapazitaet und Rueckgabe 0: B4 faellt nach D-05 weg, die Box
#                bleibt gestoppt und der Abbau folgt.
#   zurueck      aws_box.sh stop, modify-instance-attribute auf m7g.large, Typ
#                zurueckgelesen, kein Start (der Abbau folgt).
#   preis <typ>  eine gezielte Abfrage der Preis-API fuer genau diesen Typ in
#                eu-central-1, mit sechs Filtern und ohne die Preisliste zu
#                laden. Die Liste der Region ist ueber ein Gigabyte gross.
#
# **Warum Stempel.** aws_box.sh stop rechnet die Laufzeit mit dem gepinnten
# m7g.large-Satz (Pitfall 9). Die B4-Kosten werden deshalb von Hand gerechnet:
# aus den Stempeln typwechsel-hin-laeuft und typwechsel-zurueck-gestoppt und
# dem Satz, den preis am Anfahrtstag gelesen hat. Jeder Unterbefehl schreibt
# darum "typwechsel-<schritt> <UTC>" in die Rohdatei.
#
# **Was in die Rohdatei kommt und was nicht.** Die Rohdatei liegt unter docs/
# und faellt unter test_public_artifacts.py. Instanzkennung und Adresse der Box
# stehen dort nur als Platzhalter; die Ausgabe von aws_box.sh, die beide
# nennt, geht auf das Terminal und nicht in die Datei.
#
# **Die Zugangsdaten** kommen aus der Umgebung, werden hier nur auf Gesetztheit
# geprueft und nie ausgegeben; die Kommandozeile von AWS liest sie selbst
# (T-22-13).
#
# Die Rueckgabewerte, im Katalog dieses Laufverzeichnisses:
#
#   1  eine Vorbedingung fehlt (Zugangsdaten, Zustandsdatei, AWS-Kommandozeile)
#      oder die Preis-API hat keinen Satz geliefert
#   2  kein Unterbefehl, ein unbekannter, oder preis ohne gueltigen Typ
#   52 instanceInitiatedShutdownBehavior ist nicht stop
#   53 der zurueckgelesene Typ oder Zustand weicht vom geforderten ab
set -eu

# Die Entwicklungsmaschine ist Windows, und Git for Windows schreibt jedes
# Argument, das wie ein Unix-Pfad aussieht, in einen Windows-Pfad um. Muster
# aws_box.sh; kein Argument dieses Werkzeugs ist ein Pfad dieser Maschine.
MSYS_NO_PATHCONV=1
MSYS2_ARG_CONV_EXCL='*'
export MSYS_NO_PATHCONV MSYS2_ARG_CONV_EXCL

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: ./00-typwechsel.sh vorpruefung|hin|zurueck|preis <typ>

  vorpruefung  instanceInitiatedShutdownBehavior muss stop sein, sonst 52
  hin          stop, Typ m7g.4xlarge (Rueckfall m7g.2xlarge), start, Typ lesen
  zurueck      stop, Typ m7g.large, Typ lesen, kein start
  preis <typ>  Stundensatz dieses Typs in eu-central-1 aus der Preis-API

Nur auf der Entwicklungsmaschine. Die Zugangsdaten kommen aus der Umgebung.
HINWEIS
}

if [ "$#" -lt 1 ]; then
    benutzung
    exit 2
fi
SCHRITT=$1
shift
case "$SCHRITT" in
vorpruefung | hin | zurueck)
    if [ "$#" -ne 0 ]; then
        benutzung
        exit 2
    fi
    ;;
preis)
    if [ "$#" -ne 1 ]; then
        benutzung
        exit 2
    fi
    PREIS_TYP=$1
    case "$PREIS_TYP" in
    '' | *[!a-z0-9.]* | .* | *.)
        echo "00-typwechsel: '$PREIS_TYP' ist kein Instanztyp" >&2
        benutzung
        exit 2
        ;;
    esac
    ;;
*)
    echo "00-typwechsel: '$SCHRITT' ist kein Unterbefehl dieses Werkzeugs" >&2
    benutzung
    exit 2
    ;;
esac

# Die einzigen zwei Stellen, an denen diese Namen stehen.
: "${AWS_ACCESS_KEY_ID:?access key fehlt in der Umgebung}"
: "${AWS_SECRET_ACCESS_KEY:?secret key fehlt in der Umgebung}"

SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
AWS_BOX="${AWS_BOX:-$REPO/scripts/ops/aws_box.sh}"
# Derselbe Ort wie in aws_box.sh, ausserhalb des Arbeitsbaums.
STATE_DIR="${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}"
STATE_FILE="$STATE_DIR/box.env"
REFERENZ_TYP='m7g.large'
B4_TYP='m7g.4xlarge'
RUECKFALL_TYP='m7g.2xlarge'
# Die Preis-API hat nur zwei Endpunkte; us-east-1 ist einer davon und fuehrt die
# Preise aller Regionen. Der Ort ist der Name, den die API fuer eu-central-1 fuehrt.
PREIS_REGION='us-east-1'
PREIS_ORT='EU (Frankfurt)'

if [ -n "${AWS_CLI:-}" ]; then
    AWS_BIN="$AWS_CLI"
elif command -v aws >/dev/null 2>&1; then
    AWS_BIN='aws'
elif [ -x '/c/Program Files/Amazon/AWSCLIV2/aws.exe' ]; then
    AWS_BIN='/c/Program Files/Amazon/AWSCLIV2/aws.exe'
else
    echo "00-typwechsel: die AWS-Kommandozeile fehlt; AWS_CLI zeigt auf sie" >&2
    exit 1
fi

mkdir -p "$OUT"
ROH="$OUT/00-typwechsel.txt"

zeile() {
    printf '%s\n' "$*" >>"$ROH"
    printf '%s\n' "$*"
}

stempel() {
    zeile "typwechsel-$1 $(date -u +%Y-%m-%dT%H:%M:%SZ) epoch $(date -u +%s)"
}

zustand_lesen() {
    if [ ! -r "$STATE_FILE" ]; then
        echo "00-typwechsel: keine Zustandsdatei unter $STATE_FILE" >&2
        exit 1
    fi
    # shellcheck source=/dev/null
    . "$STATE_FILE"
    : "${BOX_INSTANCE_ID:?Instanzkennung fehlt in der Zustandsdatei}"
    REGION="${BOX_REGION:-eu-central-1}"
}

ec2_text() {
    "$AWS_BIN" --region "$REGION" --output text ec2 "$@"
}

box_typ() {
    ec2_text describe-instances --instance-ids "$BOX_INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].InstanceType'
}

box_zustand() {
    ec2_text describe-instances --instance-ids "$BOX_INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].State.Name'
}

typ_setzen() {
    zeile "typ-gefordert $1"
    ec2_text modify-instance-attribute --instance-id "$BOX_INSTANCE_ID" \
        --instance-type "Value=$1" >/dev/null
}

typ_pruefen() {
    ist=$(box_typ)
    zeile "typ-ist $ist"
    if [ "$ist" != "$1" ]; then
        zeile "typ-abweichung gefordert $1 ist $ist"
        exit 53
    fi
}

# Die Ausgabe von aws_box.sh nennt Kennung und Adresse der Box. Sie geht auf das
# Terminal (stderr) und nicht in die Rohdatei.
aws_box() {
    sh "$AWS_BOX" "$@" >&2
}

vorpruefung() {
    stempel vorpruefung
    wert=$(ec2_text describe-instance-attribute --instance-id "$BOX_INSTANCE_ID" \
        --attribute instanceInitiatedShutdownBehavior \
        --query 'InstanceInitiatedShutdownBehavior.Value')
    zeile "shutdown-verhalten $wert"
    if [ "$wert" != stop ]; then
        zeile "shutdown-ist-stopp nein"
        echo "00-typwechsel: shutdown -h waere auf dieser Box kein Stopp, sondern '$wert'" >&2
        echo "00-typwechsel: keine Anfahrt mit Timer, bevor das Verhalten stop heisst" >&2
        exit 52
    fi
    zeile "shutdown-ist-stopp ja"
}

# Ein Startversuch auf einem Typ. Scheitert der Start und die Box steht danach
# nicht gestoppt, ist das kein Kapazitaetsfall, und das Werkzeug endet mit 53.
versuch() {
    # Ausdruecklich geprueft: im Bedingungsteil eines if greift set -e nicht.
    if ! typ_setzen "$1"; then
        zeile "typ-setzen-gescheitert $1"
        exit 53
    fi
    if aws_box start; then
        return 0
    fi
    danach=$(box_zustand)
    zeile "start-gescheitert typ $1 zustand $danach"
    if [ "$danach" != stopped ]; then
        zeile "zustand-abweichung gefordert stopped ist $danach"
        exit 53
    fi
    return 1
}

hin() {
    vorpruefung
    stempel hin-start
    zeile "instanz <instanzkennung>"
    zeile "typ-vorher $(box_typ)"
    aws_box stop
    stempel hin-gestoppt
    ziel=''
    if versuch "$B4_TYP"; then
        ziel="$B4_TYP"
    elif versuch "$RUECKFALL_TYP"; then
        ziel="$RUECKFALL_TYP"
        zeile "b4-rueckfall $RUECKFALL_TYP"
    else
        typ_setzen "$REFERENZ_TYP"
        typ_pruefen "$REFERENZ_TYP"
        zeile "b4-entfallen kapazitaet"
        stempel hin-ende
        echo "00-typwechsel: weder $B4_TYP noch $RUECKFALL_TYP hatten Kapazitaet." >&2
        echo "00-typwechsel: die Box steht gestoppt auf $REFERENZ_TYP; B4 entfaellt, der Abbau folgt." >&2
        zeile "TYPWECHSEL-HIN-FERTIG"
        return 0
    fi
    stempel hin-laeuft
    typ_pruefen "$ziel"
    adresse=$(ec2_text describe-instances --instance-ids "$BOX_INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].PublicIpAddress')
    zeile "adresse-neu <adresse-der-box>"
    echo "00-typwechsel: neue oeffentliche Adresse $adresse (Runbook Block 10)" >&2
    echo "00-typwechsel: den A-Eintrag darauf umstellen und den Timer der Box neu setzen" >&2
    stempel hin-ende
    zeile "TYPWECHSEL-HIN-FERTIG"
}

zurueck() {
    stempel zurueck-start
    zeile "instanz <instanzkennung>"
    zeile "typ-vorher $(box_typ)"
    aws_box stop
    stempel zurueck-gestoppt
    typ_setzen "$REFERENZ_TYP"
    typ_pruefen "$REFERENZ_TYP"
    # Die Laufzeit auf dem grossen Typ, aus den zwei Stempeln dieser Datei. Sie
    # ist die Grundlage der Handrechnung; der Satz kommt aus preis.
    von=$(awk '$1 == "typwechsel-hin-laeuft" {v = $4} END {print v}' "$ROH")
    bis=$(awk '$1 == "typwechsel-zurueck-gestoppt" {v = $4} END {print v}' "$ROH")
    # Jeder Stempel fuer sich: ein leerer neben einem vollen saehe zusammen wie
    # eine Zahl aus, und die Laufzeit waere dann die ganze Epoche.
    laufzeit=unbestimmt
    case "$von" in
    '' | *[!0-9]*) ;;
    *)
        case "$bis" in
        '' | *[!0-9]*) ;;
        *)
            if [ "$bis" -ge "$von" ]; then
                laufzeit=$((bis - von))
            fi
            ;;
        esac
        ;;
    esac
    zeile "b4-laufzeit-s $laufzeit"
    stempel zurueck-ende
    zeile "TYPWECHSEL-ZURUECK-FERTIG"
}

preis() {
    stempel preis
    antwort=$("$AWS_BIN" --region "$PREIS_REGION" --output json pricing get-products \
        --service-code AmazonEC2 \
        --filters \
        "Type=TERM_MATCH,Field=instanceType,Value=$PREIS_TYP" \
        "Type=TERM_MATCH,Field=location,Value=$PREIS_ORT" \
        "Type=TERM_MATCH,Field=operatingSystem,Value=Linux" \
        "Type=TERM_MATCH,Field=tenancy,Value=Shared" \
        "Type=TERM_MATCH,Field=preInstalledSw,Value=NA" \
        "Type=TERM_MATCH,Field=capacitystatus,Value=Used" \
        --max-items 5 2>/dev/null || true)
    satz=$(printf '%s' "$antwort" | python3 -c '
import json
import sys

try:
    listen = json.load(sys.stdin)["PriceList"]
except (ValueError, KeyError):
    raise SystemExit(0)
saetze = set()
for eintrag in listen:
    produkt = json.loads(eintrag) if isinstance(eintrag, str) else eintrag
    for bedingung in produkt.get("terms", {}).get("OnDemand", {}).values():
        for dimension in bedingung.get("priceDimensions", {}).values():
            wert = dimension.get("pricePerUnit", {}).get("USD")
            if wert is not None and float(wert) > 0:
                saetze.add(wert)
if len(saetze) == 1:
    print(saetze.pop())
' 2>/dev/null || true)
    if [ -z "$satz" ]; then
        zeile "preis $PREIS_TYP unlesbar"
        echo "00-typwechsel: die Preis-API hat keinen eindeutigen Satz geliefert." >&2
        echo "00-typwechsel: laut aws_box.sh prices fehlt dem Konto pricing:GetProducts;" >&2
        echo "00-typwechsel: dann den Satz von Hand aus der oeffentlichen Liste lesen und notieren." >&2
        exit 1
    fi
    zeile "preis $PREIS_TYP $satz"
    zeile "TYPWECHSEL-PREIS-FERTIG"
}

case "$SCHRITT" in
vorpruefung)
    zustand_lesen
    vorpruefung
    zeile "TYPWECHSEL-VORPRUEFUNG-FERTIG"
    ;;
hin)
    zustand_lesen
    hin
    ;;
zurueck)
    zustand_lesen
    zurueck
    ;;
preis) preis ;;
esac
