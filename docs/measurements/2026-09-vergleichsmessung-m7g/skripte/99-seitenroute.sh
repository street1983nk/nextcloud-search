#!/bin/sh
# The result page of phase 9 on the target hardware, in both login paths.
#
# **Pitfall 10, in three sentences, because it decides what this number is.** Row
# C of the page budget report was the hybrid, expensive case by design and was
# measured as expensive as row B, because one_round() switches the vector side on
# only if side.vectors is not None and that instance had no vectors.db at all. On
# this box it does have one, with 145.854 vectors. The figure of this box is
# therefore a FIRST MEASUREMENT and not a comparison line, and it is the figure
# that turns T-09-29, closed in phase 9 with accept and the reason that the
# numbers were missing, into a decision with numbers behind it.
#
# **Why the term has two words.** one_round() switches the vector side off for a
# single term, which is exactly how row B and row C of the predecessor report
# ended up costing the same. A two word term is the only shape in which the
# hybrid case exists, so it is the shape all four rows are driven with.
#
# **The four rows and their addresses.** A is the page route with a cookie
# session, /apps/findling/?query=<begriff>. B is the same address with basic
# auth. C is the session again on a deep page, /apps/findling/?query=<begriff>
# with page=3 appended, which is the fourth display page and the case the offset
# ceiling is about. D is the dialog route with basic auth and limit=100, which is
# the counterpart of the 0,538 s of the predecessor report.
#
# **Why both login paths are measured** (pitfall 9, finding M-03 of phase 9).
# Basic auth costs 0,318 seconds per request on the comparison instance, which no
# logged in user pays. Section 5.2 of the page budget report had assigned that
# time to the permission recheck; section 6.3 corrected it. Two reports are
# comparable only over the same login path, so the header line of every row names
# its own, and the session path is the one of scripts/dev/probe_page_login.sh,
# including the Origin header: LoginController of Nextcloud 34 refuses a login
# whose origin is not a trusted domain with the same redirect a wrong password
# produces.
#
# **The three figures every row is held against**, all of them out of section 6.3
# of the page budget report and all of them written the way that report writes
# them: 0,122 s p95 for the page route over a session, 0,445 s p95 for the same
# address over basic auth, and 0,538 s p95 for the dialog route with limit=100.
# Next to them stand the two ceilings, PAGE_REQUEST_TIMEOUT_SECONDS at 1,5 s per
# call and PAGE_BUDGET_SECONDS at 3,0 s per page.
#
# **The rank rule, and it is the same one the predecessor report used** (its
# section 2): p50 and p95 are rank values without Interpolation, the value at
# rank ceil(0,50 * n) and at rank ceil(0,95 * n) of the sorted row, with n equal
# to 20 the tenth and the nineteenth value. No numpy, no percentile function of
# its own: two reports are comparable only under the same rule.
#
# **No outlier is removed.** The row stands complete in its raw file, one value
# per line in seconds, unprocessed, and a maximum far above the p95 gets a line
# of its own with the number of the repetition it came from. A row that has been
# cleaned up is a row about a decision somebody made afterwards.
#
# The password never becomes an argument: the basic auth rows read their
# credential out of a curl config file with mode 600, which is the shape
# aio_install_check.sh uses (T-10-27).
#
# The exit code: 19 means a row has fewer usable values than it needs, so its p95
# would be a statement about the requests that happened to work.
set -eu

# Everything a machine could differ in is a variable with a default, so this file
# carries no path of one machine. The first default is derived from the location
# of the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
OUT="${OUT:-$SKRIPTE/../rohdaten}"
BASE="${BASE:-https://loadtest.infranode.dev}"
KONTO="${KONTO:-lasttest}"
# The password file of the load test account on the box. The value goes into a
# curl config file and never into a command line.
PWFILE="${PWFILE:-$HOME/work/.pw/lasttest}"
# The two word term, and the reason it has two words is in the head. The plus is
# the encoded space, so the address below stays one word for the shell.
BEGRIFF="${BEGRIFF:-Bescheid+Antrag}"
# Twenty repetitions per row, which is the n of the predecessor report, plus five
# warm up requests that do not enter the raw data.
N="${N:-20}"
AUFWAERMEN="${AUFWAERMEN:-5}"
TIEFE="${TIEFE:-3}"
LIMIT="${LIMIT:-100}"
# A maximum more than this many times the p95 gets its own line. It is a named
# factor and not a judgement: nothing is removed, the line only points at it.
AUSREISSER_FAKTOR="${AUSREISSER_FAKTOR:-2.0}"

mkdir -p "$OUT"
ZIEL="$OUT/99-seitenroute.txt"
WORK=$(mktemp -d)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT

KONTOPW=$(sudo cat "$PWFILE")
CURLRC="$WORK/curlrc"
printf 'user = "%s:%s"\n' "$KONTO" "$KONTOPW" >"$CURLRC"
chmod 600 "$CURLRC"
# The same value once more without a newline, for the form field of the login
# POST. curl reads a field value out of a file with name@datei, so the password
# does not have to become an argument for the session path either; a trailing
# newline would travel as %0A and be part of the password.
PWFELD="$WORK/pwfeld"
printf '%s' "$KONTOPW" >"$PWFELD"
chmod 600 "$PWFELD"
JAR="$WORK/cookies.txt"

# The addresses of the four rows. The page route of phase 9 is
# /apps/findling/?query=<begriff>&page=<n>, and the dialog route is the OCS route
# of the predecessor report with limit=100.
SEITE="$BASE/apps/findling/?query=$BEGRIFF"
SEITE_TIEF="$BASE/apps/findling/?query=$BEGRIFF&page=$TIEFE"
DIALOG="$BASE/ocs/v2.php/search/providers/findling/search?term=$BEGRIFF&limit=$LIMIT"

# The cookie session, step by step the way probe_page_login.sh walks it: the form
# with the jar, the token out of the form, the POST with the token AND the Origin
# header, and after that the jar carries the session.
anmelden() {
    rm -f "$JAR"
    curl -sfS -c "$JAR" -o "$WORK/login.html" "$BASE/login" || return 1
    token=$(sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' "$WORK/login.html" | head -1)
    if [ -z "$token" ]; then
        echo "die Anmeldeseite traegt kein data-requesttoken, die Anmeldung ist nicht zu unterschreiben"
        return 1
    fi
    weiter=$(curl -sS -b "$JAR" -c "$JAR" -o /dev/null -w '%{redirect_url}' \
        -H "Origin: $BASE" \
        --data-urlencode "user=$KONTO" \
        --data-urlencode "password@$PWFELD" \
        --data-urlencode "requesttoken=$token" \
        "$BASE/login" || true)
    case "$weiter" in
    */login | */login\?*)
        echo "die Instanz hat das Konto auf die Anmeldeseite zurueckgeschickt"
        return 1
        ;;
    '')
        echo "die Anmeldung hat gar nicht mit einer Umleitung geantwortet"
        return 1
        ;;
    esac
    return 0
}

# One row, n repetitions, one number per line in seconds. The status code is
# collected next to it, because a row of fast 302s would otherwise look like a
# fast page.
reihe() {
    datei=$1
    weg=$2
    adresse=$3
    : >"$datei"
    : >"$datei.codes"
    lauf=0
    while [ "$lauf" -lt "$((N + AUFWAERMEN))" ]; do
        lauf=$((lauf + 1))
        case "$weg" in
        sitzung)
            antwort=$(curl -sS -b "$JAR" -c "$JAR" -o /dev/null \
                -w '%{time_total} %{http_code}' "$adresse" || echo "0 000")
            ;;
        basic)
            antwort=$(curl -sS -K "$CURLRC" -H 'OCS-APIRequest: true' -o /dev/null \
                -w '%{time_total} %{http_code}' "$adresse" || echo "0 000")
            ;;
        esac
        # The warm up requests are driven and thrown away, exactly as the
        # predecessor report did it.
        if [ "$lauf" -le "$AUFWAERMEN" ]; then
            continue
        fi
        printf '%s\n' "$(printf '%s\n' "$antwort" | awk '{print $1}')" >>"$datei"
        printf '%s\n' "$(printf '%s\n' "$antwort" | awk '{print $2}')" >>"$datei.codes"
    done
}

{
    date -u +'seitenroute-start %Y-%m-%dT%H:%M:%SZ'
    printf 'begriff: %s (zwei Woerter, siehe Kopf)\n' "$BEGRIFF"
    printf 'wiederholungen je reihe: %s, davon aufwaermen: %s\n' "$N" "$AUFWAERMEN"
    echo "rangregel: Wert an Rang ceil(0,50 * n) bzw. ceil(0,95 * n) der sortierten"
    echo "Reihe, ohne Interpolation, wie Abschnitt 2 des Seitenbudget-Berichts"
    echo "erstmessung: diese Instanz HAT eine vectors.db mit 145.854 Vektoren, der"
    echo "Vorlaeuferbericht hatte keine; die Zahlen unten sind keine Vergleichszeile"

    echo "=== The cookie session, once, for rows A and C ==="
    if anmelden; then
        echo "anmeldung-sitzung ja" >"$WORK/anmeldung"
    else
        echo "anmeldung-sitzung nein" >"$WORK/anmeldung"
    fi
    cat "$WORK/anmeldung"

    echo "=== Reihe A: Seitenroute, Anmeldeweg SITZUNG, erste Seite ==="
    printf 'adresse: %s\n' "$SEITE"
    reihe "$OUT/99-reihe-a.txt" sitzung "$SEITE"
    sort "$OUT/99-reihe-a.txt.codes" | uniq -c

    echo "=== Reihe B: Seitenroute, Anmeldeweg BASIC-AUTH, erste Seite ==="
    printf 'adresse: %s\n' "$SEITE"
    reihe "$OUT/99-reihe-b.txt" basic "$SEITE"
    sort "$OUT/99-reihe-b.txt.codes" | uniq -c

    echo "=== Reihe C: Seitenroute, Anmeldeweg SITZUNG, Seite $TIEFE ==="
    printf 'adresse: %s\n' "$SEITE_TIEF"
    reihe "$OUT/99-reihe-c.txt" sitzung "$SEITE_TIEF"
    sort "$OUT/99-reihe-c.txt.codes" | uniq -c

    echo "=== Reihe D: Dialogweg, Anmeldeweg BASIC-AUTH, limit=$LIMIT ==="
    printf 'adresse: %s\n' "$DIALOG"
    reihe "$OUT/99-reihe-d.txt" basic "$DIALOG"
    sort "$OUT/99-reihe-d.txt.codes" | uniq -c

    echo "=== Die Auswertung, nach der Rangregel des Vorlaeuferberichts ==="
    python3 - "$OUT" "$N" "$AUSREISSER_FAKTOR" "$WORK/urteil" <<'PY'
import math
import pathlib
import sys

ordner = pathlib.Path(sys.argv[1])
erwartet = int(sys.argv[2])
faktor = float(sys.argv[3])
urteil = pathlib.Path(sys.argv[4])


def de(zahl: float, stellen: int = 3) -> str:
    """German decimal separator, as the reports write it."""
    return f"{zahl:.{stellen}f}".replace(".", ",")


def rang(werte: list[float], anteil: float) -> float:
    """The value at rank ceil(anteil * n), one based, WITHOUT interpolation.

    The rule of section 2 of the page budget report, written out rather than
    taken from a library: two reports are comparable only under the same rule,
    and a percentile function that interpolates would silently produce a third.
    """
    stelle = max(1, math.ceil(anteil * len(werte)))
    return werte[min(stelle, len(werte)) - 1]


# The three figures of section 6.3 that have a counterpart here, and the two
# ceilings. PAGE_REQUEST_TIMEOUT_SECONDS and PAGE_BUDGET_SECONDS are the PHP
# constants of ExAppService and PageController.
DECKE_AUFRUF = 1.5
DECKE_BUDGET = 3.0
REIHEN = (
    ("A", "99-reihe-a.txt", "Seitenroute, SITZUNG, erste Seite", "sitzung", 0.122),
    ("B", "99-reihe-b.txt", "Seitenroute, BASIC-AUTH, erste Seite", "basic-auth", 0.445),
    ("C", "99-reihe-c.txt", "Seitenroute, SITZUNG, tiefe Seite", "sitzung", 0.122),
    ("D", "99-reihe-d.txt", "Dialogweg, BASIC-AUTH, limit=100", "basic-auth", 0.538),
)

vollstaendig = True
for name, datei, was, weg, vorwert in REIHEN:
    pfad = ordner / datei
    rohe = []
    if pfad.is_file():
        for zeile in pfad.read_text(encoding="utf-8").splitlines():
            try:
                wert = float(zeile.strip())
            except ValueError:
                continue
            if wert > 0:
                rohe.append(wert)
    print(f"-- Reihe {name}: {was} --")
    print(f"Reihe {name} anmeldeweg      {weg}")
    if len(rohe) < erwartet:
        print(f"Reihe {name} unvollstaendig  {len(rohe)} von {erwartet} brauchbaren Werten")
        print(f"Reihe {name} p95             nicht gebildet, weil die Reihe unvollstaendig ist")
        vollstaendig = False
        continue
    werte = sorted(rohe)
    p50 = rang(werte, 0.50)
    p95 = rang(werte, 0.95)
    print(f"Reihe {name} n                {len(werte)}")
    print(f"Reihe {name} min              {de(werte[0])} s")
    print(f"Reihe {name} p50              {de(p50)} s")
    print(f"Reihe {name} p95              {de(p95)} s")
    print(f"Reihe {name} max              {de(werte[-1])} s")
    print(f"Reihe {name} vorwert          {de(vorwert)} s (Seitenbudget 6.3, gleicher Anmeldeweg)")
    print(f"Reihe {name} abstand-vorwert  {de(p95 - vorwert)} s")
    print(f"Reihe {name} decke-aufruf     {de(DECKE_AUFRUF)} s, marge {de(DECKE_AUFRUF - p95)} s")
    print(f"Reihe {name} decke-budget     {de(DECKE_BUDGET)} s, marge {de(DECKE_BUDGET - p95)} s")
    if p95 > vorwert:
        print(f"Reihe {name} einordnung       teurer als der Vorlaeufer, und das ist die Erwartung:")
        print(f"Reihe {name}                  jene Instanz hatte keine vectors.db (Fallstrick 10)")
    # The outlier gets a line and its repetition number, and it stays in the row.
    if werte[-1] > faktor * p95:
        stelle = rohe.index(werte[-1]) + 1
        print(f"Reihe {name} ausreisser       {de(werte[-1])} s in Wiederholung {stelle},")
        print(f"Reihe {name}                  mehr als {de(faktor, 1)} mal p95; nicht entfernt, siehe Rohdatei")

print("-- Die Trennung, die Befund M-03 verlangt --")
print("Der Preis des Anmeldewegs ist die Differenz der Reihen A und B am p95, und")
print("kein angemeldeter Nutzer bezahlt ihn. Auf der Vergleichsinstanz waren es")
print("0,318 s je Anfrage.")
urteil.write_text("seitenroute-vollstaendig " + ("ja" if vollstaendig else "nein") + "\n", encoding="utf-8")
PY
    cat "$WORK/urteil"

    date -u +'seitenroute-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Everything below the pipeline, because the return code of a pipeline belongs to
# tee: an exit inside the block above would only leave the subshell, and the
# refusal would be a line in the raw file that nobody reads.
urteil=$(cat "$WORK/urteil" 2>/dev/null || echo 'seitenroute-vollstaendig nein')

if [ "$urteil" != 'seitenroute-vollstaendig ja' ]; then
    echo "99-seitenroute: at least one row has fewer than $N usable values" >&2
    echo "99-seitenroute: its p95 would be a statement about the requests that happened" >&2
    echo "99-seitenroute: to work, and the status codes next to the row say which" >&2
    exit 19
fi

echo "99-SEITENROUTE-FERTIG"
