#!/bin/sh
# Der Typwechsel der Messboxen der Abnahme-Anfahrt und die Vorpruefung des
# harten Stopps, Phase 28 (D-28-03, D-28-04, D-28-14).
#
# NIE AUF DER BOX AUSFUEHREN. Dieses Werkzeug laeuft nur auf der
# Entwicklungsmaschine; die AWS-Zugangsdaten duerfen die Box nie erreichen.
#
# **DIESE FASSUNG IST NICHT GEFAHREN.** Keine Rohdatei liegt neben ihr. Ihr
# Abnahmekriterium ist Form, statische Analyse und ein Lauf gegen eine
# nachgestellte AWS-Kommandozeile in backend/tests/test_v14_typwechsel.py.
#
# Die Verallgemeinerung von docs/measurements/2026-09-v13-messung/skripte/
# 00-typwechsel.sh. Die v1.3-Fassung kannte zwei feste Typen und einen eigenen
# Rueckfall (D-05 der v1.3). Die Matrix dieser Anfahrt hat sechs Typen auf zwei
# Boxen, und sie ist ein Owner-Entscheid (D-28-04): ein Rueckfall auf einen
# anderen Typ waere eine andere Matrix. Darum gibt es hier keinen.
#
# **Vier Unterbefehle.**
#
#   vorpruefung        liest instanceInitiatedShutdownBehavior der Box. Der
#                      Sicherheitstimer der Kette (D-28-14) ist ein shutdown -h
#                      aus der Box heraus, und der ist nur dann ein Stopp, wenn
#                      dieser Wert stop heisst; bei terminate waeren Volume und
#                      Korpus weg. Jeder andere Wert endet mit 52. Bei stop
#                      steht "vorpruefung-stop-ja <UTC>" in der Rohdatei, und
#                      daraus setzt der Operator VORPRUEFUNG=stop-ja fuer
#                      00-kette.sh.
#   wechsel <zieltyp>  Typ lesen, Architektur vergleichen, vorpruefung, dann
#                      aws_box.sh stop, modify-instance-attribute, aws_box.sh
#                      start, Typ und Zustand zurueckgelesen. Erlaubt sind nur
#                      die sechs Typen der Matrix. Ein Wechsel zwischen m7g und
#                      c7a endet mit 54, bevor irgendetwas ausser einem describe
#                      die Box beruehrt: die Architektur haengt am Abbild, arm
#                      nach x86 ist eine zweite Instanz und kein Typwechsel.
#                      Scheitert der Start an der Kapazitaet, geht der Typ auf
#                      den alten zurueck, die Box bleibt gestoppt, die Zeile
#                      "typwechsel-kapazitaet <typ>" steht in der Rohdatei und
#                      das Werkzeug endet mit 55. Weiter entscheidet der Owner.
#   preis <typ>...     liest die oeffentliche Preiskarte (EU (Frankfurt), Linux,
#                      On Demand; gzip, kein Kontoaufruf) und druckt den Satz je
#                      Typ. Die Preis-API des Kontos ist gesperrt (26.09.: die
#                      v1.3-Fassung endete mit 1). Ein Typ ohne Satz endet mit 1.
#   quota [typ...]     liest kostenlos die vCPU-Quota der Standard-Instanzen
#                      (L-1216C47A) und je Typ die Zonen in eu-central-1, die ihn
#                      anbieten. Ohne Typ alle sechs.
#
# **Warum Stempel.** aws_box.sh stop rechnet seit 28-03 mit dem Satz des Typs,
# den describe-instances meldet. Die Kostenrechnung der Anfahrt braucht
# trotzdem die Zeitpunkte je Typ, und darum schreibt wechsel die Zeile
# "typwechsel <alt> -> <neu> gestoppt <UTC> laeuft <UTC>" samt Epoche.
#
# **Was in die Rohdatei kommt und was nicht.** Die Rohdatei liegt unter docs/
# und faellt unter test_public_artifacts.py. Instanzkennung und Adresse der Box
# stehen dort nur als Platzhalter; die Ausgabe von aws_box.sh, die beide nennt,
# geht auf das Terminal und nicht in die Datei.
#
# **Zwei Boxen.** Jede Box hat ihr eigenes Zustandsverzeichnis, benannt durch
# FINDLING_LOADTEST_DIR (zum Beispiel .../arm und .../x86). Dieses Werkzeug und
# aws_box.sh lesen dasselbe, weil die Umgebung an aws_box.sh weitergeht.
#
# **Die Zugangsdaten** kommen aus der Umgebung, werden hier nur auf Gesetztheit
# geprueft und nie ausgegeben; die Kommandozeile von AWS liest sie selbst
# (T-28-12). preis braucht keine, die Karte ist oeffentlich.
#
# Die Rueckgabewerte:
#
#   1  eine Vorbedingung fehlt (Zugangsdaten, Zustandsdatei, AWS-Kommandozeile,
#      curl) oder die Preiskarte hat einen Typ nicht geliefert
#   2  kein Unterbefehl, ein unbekannter, ein Typ ausserhalb der Matrix oder
#      ein Typ in falscher Form
#   52 instanceInitiatedShutdownBehavior ist nicht stop
#   53 der zurueckgelesene Typ oder Zustand weicht vom geforderten ab
#   54 der Wechsel wuerde die Architektur wechseln
#   55 der Start auf dem Zieltyp scheiterte an der Kapazitaet
set -eu

# Die Entwicklungsmaschine ist Windows, und Git for Windows schreibt jedes
# Argument, das wie ein Unix-Pfad aussieht, in einen Windows-Pfad um. Muster
# aws_box.sh; kein Argument dieses Werkzeugs ist ein Pfad dieser Maschine.
MSYS_NO_PATHCONV=1
MSYS2_ARG_CONV_EXCL='*'
export MSYS_NO_PATHCONV MSYS2_ARG_CONV_EXCL

# Die Matrix aus D-28-03 und D-28-04, und nur sie.
ERLAUBT='m7g.large m7g.4xlarge c7a.xlarge c7a.2xlarge c7a.4xlarge c7a.8xlarge'

benutzung() {
    cat >&2 <<'HINWEIS'
Benutzung: ./00-typwechsel.sh vorpruefung|wechsel <zieltyp>|preis <typ>...|quota [typ...]

  vorpruefung        instanceInitiatedShutdownBehavior muss stop sein, sonst 52
  wechsel <zieltyp>  stop, Typ setzen, start, Typ und Zustand lesen; kein Rueckfall
  preis <typ>...     Stundensatz je Typ aus der oeffentlichen Preiskarte
  quota [typ...]     vCPU-Quota und Zonen mit Angebot in eu-central-1

Zieltypen: m7g.large m7g.4xlarge (arm64), c7a.xlarge c7a.2xlarge c7a.4xlarge
c7a.8xlarge (x86_64). Ein Wechsel zwischen m7g und c7a wird verweigert (54).

Nur auf der Entwicklungsmaschine. Die Zugangsdaten kommen aus der Umgebung.
HINWEIS
}

typ_form_pruefen() {
    case "$1" in
    '' | *[!a-z0-9.]* | .* | *.)
        echo "00-typwechsel: '$1' ist kein Instanztyp" >&2
        benutzung
        exit 2
        ;;
    esac
}

erlaubt() {
    for erlaubter in $ERLAUBT; do
        if [ "$erlaubter" = "$1" ]; then
            return 0
        fi
    done
    return 1
}

familie() {
    case "$1" in
    m7g.*) echo 'arm64' ;;
    c7a.*) echo 'x86_64' ;;
    *) echo 'unbekannt' ;;
    esac
}

if [ "$#" -lt 1 ]; then
    benutzung
    exit 2
fi
SCHRITT=$1
shift
case "$SCHRITT" in
vorpruefung)
    if [ "$#" -ne 0 ]; then
        benutzung
        exit 2
    fi
    ;;
wechsel)
    if [ "$#" -ne 1 ]; then
        benutzung
        exit 2
    fi
    ZIEL=$1
    typ_form_pruefen "$ZIEL"
    if ! erlaubt "$ZIEL"; then
        echo "00-typwechsel: '$ZIEL' gehoert nicht zur Matrix (D-28-04)" >&2
        benutzung
        exit 2
    fi
    ;;
preis)
    if [ "$#" -lt 1 ]; then
        benutzung
        exit 2
    fi
    for typ in "$@"; do
        typ_form_pruefen "$typ"
    done
    ;;
quota)
    for typ in "$@"; do
        typ_form_pruefen "$typ"
    done
    ;;
*)
    echo "00-typwechsel: '$SCHRITT' ist kein Unterbefehl dieses Werkzeugs" >&2
    benutzung
    exit 2
    ;;
esac

if [ "$SCHRITT" != preis ]; then
    # Die einzigen zwei Stellen, an denen diese Namen stehen.
    : "${AWS_ACCESS_KEY_ID:?access key fehlt in der Umgebung}"
    : "${AWS_SECRET_ACCESS_KEY:?secret key fehlt in der Umgebung}"
fi

SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
AWS_BOX="${AWS_BOX:-$REPO/scripts/ops/aws_box.sh}"
# Derselbe Ort wie in aws_box.sh, ausserhalb des Arbeitsbaums.
STATE_DIR="${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}"
STATE_FILE="$STATE_DIR/box.env"
# Der Interpreter fuer das Lesen der Preiskarte. Auf der Entwicklungsmaschine
# kann python3 ein Platzhalter des Stores sein; dann zeigt PYTHON auf den echten.
PYTHON="${PYTHON:-python3}"
# Die oeffentliche Preiskarte, dieselbe, aus der die Satztabelle von aws_box.sh
# am 29.09.2026 gelesen wurde (Manifest 2026-09-25T17:45:21Z).
PREIS_KARTE='https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/EU%20(Frankfurt)/Linux/index.json'
QUOTA_REGION='eu-central-1'
QUOTA_CODE='L-1216C47A'

AWS_BIN=''
aws_finden() {
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
}

mkdir -p "$OUT"
ROH="$OUT/00-typwechsel.txt"

zeile() {
    printf '%s\n' "$*" >>"$ROH"
    printf '%s\n' "$*"
}

jetzt() {
    date -u +%Y-%m-%dT%H:%M:%SZ
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
    wert=$(ec2_text describe-instance-attribute --instance-id "$BOX_INSTANCE_ID" \
        --attribute instanceInitiatedShutdownBehavior \
        --query 'InstanceInitiatedShutdownBehavior.Value')
    zeile "shutdown-verhalten $wert"
    if [ "$wert" != stop ]; then
        zeile "shutdown-ist-stopp nein"
        echo "00-typwechsel: shutdown -h waere auf dieser Box kein Stopp, sondern '$wert'" >&2
        echo "00-typwechsel: keine Kette mit Timer, bevor das Verhalten stop heisst" >&2
        exit 52
    fi
    zeile "shutdown-ist-stopp ja"
    zeile "vorpruefung-stop-ja $(jetzt)"
}

wechsel() {
    zeile "instanz <instanzkennung>"
    alt=$(box_typ)
    zeile "typ-vorher $alt"
    if [ "$alt" = "$ZIEL" ]; then
        zeile "typwechsel-unnoetig $ZIEL"
        return 0
    fi
    # Vor jedem Aufruf, der die Box beruehrt: ein Wechsel ueber die Familie
    # startete eine Instanz mit einem Abbild der falschen Architektur (T-28-14).
    if [ "$(familie "$alt")" != "$(familie "$ZIEL")" ]; then
        zeile "typwechsel-verweigert architektur $alt -> $ZIEL"
        echo "00-typwechsel: $alt ist $(familie "$alt"), $ZIEL ist $(familie "$ZIEL")." >&2
        echo "00-typwechsel: die Architektur haengt am Abbild; dafuer gibt es die zweite Instanz" >&2
        exit 54
    fi
    vorpruefung
    aws_box stop
    gestoppt=$(jetzt)
    gestoppt_epoche=$(date -u +%s)
    # Ausdruecklich geprueft: im Bedingungsteil eines if greift set -e nicht.
    if ! typ_setzen "$ZIEL"; then
        zeile "typ-setzen-gescheitert $ZIEL"
        exit 53
    fi
    if ! aws_box start; then
        danach=$(box_zustand)
        zeile "start-gescheitert typ $ZIEL zustand $danach"
        if [ "$danach" != stopped ]; then
            zeile "zustand-abweichung gefordert stopped ist $danach"
            exit 53
        fi
        # Kein Rueckfall auf einen anderen Typ der Matrix: der Typ geht auf den
        # alten zurueck, und die Box bleibt gestoppt, bis der Owner entscheidet.
        zeile "typwechsel-kapazitaet $ZIEL"
        typ_setzen "$alt"
        typ_pruefen "$alt"
        zeile "box-gestoppt-seit $gestoppt"
        echo "00-typwechsel: $ZIEL hatte keine Kapazitaet; die Box steht gestoppt auf $alt." >&2
        echo "00-typwechsel: kein Rueckfall ohne Owner (D-28-04); die Kosten laufen nur fuer die Platten." >&2
        exit 55
    fi
    laeuft=$(jetzt)
    laeuft_epoche=$(date -u +%s)
    typ_pruefen "$ZIEL"
    zustand=$(box_zustand)
    zeile "zustand-ist $zustand"
    if [ "$zustand" != running ]; then
        zeile "zustand-abweichung gefordert running ist $zustand"
        exit 53
    fi
    zeile "typwechsel $alt -> $ZIEL gestoppt $gestoppt laeuft $laeuft"
    zeile "typwechsel-epoche gestoppt $gestoppt_epoche laeuft $laeuft_epoche"
    adresse=$(ec2_text describe-instances --instance-ids "$BOX_INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].PublicIpAddress')
    zeile "adresse-neu <adresse-der-box>"
    echo "00-typwechsel: neue oeffentliche Adresse $adresse" >&2
    echo "00-typwechsel: den A-Eintrag darauf umstellen und known_hosts erneuern" >&2
    zeile "TYPWECHSEL-FERTIG"
}

preis() {
    if ! command -v curl >/dev/null 2>&1; then
        echo "00-typwechsel: preis braucht curl" >&2
        exit 1
    fi
    karte=$(mktemp)
    trap 'rm -f "$karte"' EXIT
    zeile "preis-gelesen $(jetzt)"
    # Die Karte geht ueber stdout in die Datei und nicht ueber -o: ein curl
    # fuer Windows bekaeme den Pfad aus mktemp wegen MSYS_NO_PATHCONV
    # unuebersetzt und schriebe nach C:\tmp (am 30.09.2026 so geschehen, die
    # Datei hier blieb leer).
    if ! curl -sS --fail --max-time 120 "$PREIS_KARTE" >"$karte"; then
        zeile "preis-karte unlesbar"
        echo "00-typwechsel: die oeffentliche Preiskarte war nicht abrufbar" >&2
        exit 1
    fi
    # Die Karte kommt gzip-verpackt; ob curl sie schon entpackt hat, entscheidet
    # die Signatur der ersten zwei Bytes. Gesucht wird jeder Eintrag, dessen
    # Feld "Instance Type" den Typ nennt; genau ein Satz gilt, mehrere oder
    # keiner heissen unlesbar. Die Karte geht ueber stdin hinein und nicht als
    # Pfad: ein Python fuer Windows liest den Pfad aus mktemp von MSYS nicht.
    # Das Programm traegt keinen Rueckstrich: beim Aufruf eines Windows-Python
    # wurde aus der Folge x1f mit Rueckstrich im Argument ein Steuerzeichen,
    # und das Programm endete am 30.09.2026 mit SyntaxError.
    ergebnis=$("$PYTHON" -c '
import gzip
import json
import sys

raw = sys.stdin.buffer.read()
if raw[:2] == bytes((31, 139)):
    raw = gzip.decompress(raw)
try:
    card = json.loads(raw)
except ValueError:
    print("karte-unlesbar")
    raise SystemExit(0)

rates = {}


def walk(node):
    if isinstance(node, dict):
        kind = node.get("Instance Type")
        price = node.get("price")
        if isinstance(kind, str) and isinstance(price, str):
            rates.setdefault(kind, set()).add(price)
        for value in node.values():
            walk(value)
    elif isinstance(node, list):
        for value in node:
            walk(value)


walk(card)
manifest = card.get("manifest", {}) if isinstance(card, dict) else {}
print("quelle %s" % (manifest.get("publicationDate") or manifest.get("hawkFilePublicationDate") or "unbekannt"))
for kind in sys.argv[1:]:
    found = rates.get(kind, set())
    print("%s %s" % (kind, found.pop() if len(found) == 1 else "unlesbar"))
' "$@" <"$karte") || ergebnis='karte-unlesbar'
    case "$ergebnis" in
    karte-unlesbar*)
        zeile "preis-karte unlesbar"
        exit 1
        ;;
    esac
    fehlt=0
    printf '%s\n' "$ergebnis" >"$karte.zeilen"
    while read -r erstes zweites; do
        if [ "$erstes" = quelle ]; then
            zeile "preis-quelle $zweites"
            continue
        fi
        zeile "preis $erstes $zweites"
        if [ "$zweites" = unlesbar ]; then
            fehlt=1
        fi
    done <"$karte.zeilen"
    rm -f "$karte.zeilen"
    if [ "$fehlt" -ne 0 ]; then
        echo "00-typwechsel: die Preiskarte nennt nicht fuer jeden Typ genau einen Satz" >&2
        exit 1
    fi
    zeile "TYPWECHSEL-PREIS-FERTIG"
}

quota() {
    if [ "$#" -eq 0 ]; then
        # shellcheck disable=SC2086
        set -- $ERLAUBT
    fi
    wert=$("$AWS_BIN" --region "$QUOTA_REGION" --output text service-quotas get-service-quota \
        --service-code ec2 --quota-code "$QUOTA_CODE" --query 'Quota.Value')
    zeile "quota-vcpu-standard $wert"
    for typ in "$@"; do
        zonen=$("$AWS_BIN" --region "$QUOTA_REGION" --output text ec2 describe-instance-type-offerings \
            --location-type availability-zone \
            --filters "Name=instance-type,Values=$typ" \
            --query 'InstanceTypeOfferings[].Location')
        zonen=$(printf '%s\n' $zonen | sort | tr '\n' ' ' | sed 's/ *$//')
        zeile "angebot $typ ${zonen:-keine}"
    done
    zeile "TYPWECHSEL-QUOTA-FERTIG"
}

case "$SCHRITT" in
vorpruefung)
    aws_finden
    zustand_lesen
    zeile "typwechsel-vorpruefung $(jetzt)"
    vorpruefung
    zeile "TYPWECHSEL-VORPRUEFUNG-FERTIG"
    ;;
wechsel)
    aws_finden
    zustand_lesen
    zeile "typwechsel-start $(jetzt)"
    wechsel
    ;;
preis) preis "$@" ;;
quota)
    aws_finden
    quota "$@"
    ;;
esac
