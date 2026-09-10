#!/bin/sh
# The ten German language cases on the box, the successor fassung for DI-10-02.
#
# **Where the driven fassung lies, and that it stays where it lies.** The run of
# 10.09.2026 (plan 10-06) drove
# docs/measurements/2026-09-vergleichsmessung-m7g/skripte/98-sprachfaelle.sh.
# That file is part of the evidence of that run and stays byte identical: a
# measurement script that is edited afterwards makes every figure next to it
# unsupported. The watchman
# test_the_driven_language_case_script_stays_byte_identical in
# backend/tests/test_measurement_scripts.py turns red on the first changed byte
# over there. THIS file is the successor, in a run directory of its own, and the
# difference between the two files is the subject of DI-10-02.
#
# **What DI-10-02 says, in its own words: an account of its own separates the
# PERMISSION and not the INDEX.** The head of the original introduces the
# account `sprachfall` because the load corpus carries the same six words. That
# reasoning is right about the permission and silent about the ranking. The
# prefilter ranks over the WHOLE index, the final PHP recheck filters afterwards
# on what the asking account may see, and with 52.111 foreign documents carrying
# the same tokens there is nothing left to show. The diagnosis of 10.09.
# (rohdaten/98b-sprachfaelle-diagnose.txt) measured it: for `Genehmigung`,
# `Frist` and `Vertrag` not one file of the asking account appears among the
# first 2.000 candidates, for `Bescheid` it stands at rank 1.925 of 2.000. The
# balance line "sprachfaelle bestanden 6 von 10" of that run is therefore a
# measured figure and NOT a statement about the German language chain. That is
# the whole of DI-10-02.
#
# **The three things this fassung does differently, and nothing else:**
#
#   1. **Vorpruefung Fremdbestand.** Before the ten cases every term is asked
#      ONCE MORE, as the load test account that owns the 52.111 documents, over
#      the same OCS route. The answer says how much foreign stock stands between
#      the asking account and its own file.
#   2. **A three valued verdict instead of a two valued one.** GRUEN, ROT, or
#      NICHT MESSBAR (Fremdbestand N Treffer). The order of the checks is
#      binding: first the foreign stock against the threshold, then the verdict
#      of the case. A case that is not measurable gets no second verdict beside
#      it, and the balance line carries both figures. The three valued reading
#      is already established in this repository: 99b-runden.sh reads the drift
#      case that way for the same kind of reason.
#   3. **CI_LAUF becomes a required input.** The measurement with an index of
#      its own exists and it runs in CI: integration.yml, job index-search-e2e,
#      drives these same ten cases on a fresh instance WITHOUT foreign stock.
#      What was missing on 10.09. was the binding, because CI_LAUF was not set
#      and the raw file therefore carried a ci-beleg line with no run number in
#      it. A run without that number now ends before the first case instead of
#      noting the gap.
#
# **Why the threshold is 64 and not a round number.** php/lib/Search/Provider.php
# caps the candidates a single search examines at MAX_RECHECKS_ABSOLUTE = 64;
# that ceiling is the window the own file has to land in. A foreign stock that
# fills the window can push the own file out of it entirely, and the diagnosis
# measured how far out: rank 1.925 of 2.000 for Bescheid, not even within 2.000
# for the other three. Below 64 the window still has room, and the six green
# cases of 10.09. are exactly the terms whose foreign stock is zero: `Mueller`
# has one single hit in the whole index and that hit is the own file. A single
# foreign hit is therefore NOT a reason to call a case unmeasurable, and the
# threshold does not pretend it is. What the pre check does instead is write the
# figure down for EVERY term, whatever the verdict, so that a red case with a
# foreign stock below the threshold carries that number in its own line and
# nobody reads it as a language finding.
#
# **Two counts per term, and the second one is why.** The cases send no limit,
# so they get the page of the dialog, and the pre check asks with exactly that
# page first: that number is comparable to what the cases see. A count that the
# page caps at a handful can never reach a threshold taken from a window of 64,
# so the pre check asks a second time with an explicit depth of 64, and THAT is
# the number the threshold is compared against. Both stand in the same line.
#
# Everything the original promises stays promised, and the sections below it are
# unchanged in substance: the account of its own whose home holds nothing but
# testdata/corpus, the 39 files over WebDAV because that is the path a user
# takes, the finished OCR pass before any verdict is read, and all ten cases
# driven even after a red one. FRIST, RUNDEN and RUNDENFRIST keep their old
# defaults, because the box plan of 11-06 hands over FRIST=60 RUNDEN=10 and a
# changed default would cost the comparability with the original.
#
# Passwords never become arguments (T-10-27): occ reads OC_PASS out of the
# environment, and both curl config files have mode 600. The load test password
# comes out of the environment or out of a file that is read with sudo, and it
# never travels in an argument either.
#
# The exit codes: 15 the upload did not deliver 39 files, 16 the work stock was
# still not empty at the round cap, 17 at least one MEASURABLE case was red, 18
# jq is not on this box, 19 the pre check of the foreign stock could not be
# driven, 22 CI_LAUF carries no run number, 23 not a single case was measurable.
set -eu

# Everything a machine could differ in is a variable with a default, so this file
# carries no path of one machine. The first default is derived from the location
# of the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
BASE="${BASE:-https://loadtest.infranode.dev}"
KORPUS="${KORPUS:-$REPO/testdata/corpus}"
# The account of the cases. Expressly not lasttest: that home holds the load
# corpus, and the six words above stand in it.
KONTO="${KONTO:-sprachfall}"
ORDNER="${ORDNER:-corpus}"
# The account of the pre check, and it is the opposite one on purpose: the owner
# of the 52.111 documents, because the question is how much of the ranking its
# stock takes up.
LASTKONTO="${LASTKONTO:-lasttest}"
# The password file of the load test account on the box, the same default
# 99b-runden.sh uses. Read with sudo into a variable, never into an argument. If
# FINDLING_LOAD_PASSWORD is already set in the environment, the file is not read.
PWFILE="${PWFILE:-$HOME/work/.pw/lasttest}"
# The number of files the reference corpus holds. Written down rather than
# counted from the directory, because a check that counts its own expectation
# agrees with itself no matter which files arrived.
ERWARTETE_DATEIEN="${ERWARTETE_DATEIEN:-39}"
# The waiting period before a work stock counts as an answer, against the
# slowest clock involved: the poller backoff runs up to 300 s and AIO calls
# cron.php only every five minutes.
FRIST="${FRIST:-360}"
RUNDEN="${RUNDEN:-40}"
RUNDENFRIST="${RUNDENFRIST:-60}"
# The foreign stock from which on a case can no longer carry its statement, and
# the depth the pre check counts to. Both are MAX_RECHECKS_ABSOLUTE of
# php/lib/Search/Provider.php, which is the ceiling on the candidates one search
# examines; the head explains why that number and not a round one.
FREMD_SCHWELLE="${FREMD_SCHWELLE:-64}"
FREMD_TIEFE="${FREMD_TIEFE:-64}"
# The run number of the last green integration.yml run. NOT a default any more:
# it is the CI proof the number of this step stands next to, and a run without it
# ends below.
CI_LAUF="${CI_LAUF:-}"

# The seven file names of the cases. Named here so that a rename of a corpus file
# breaks in one place instead of in ten, exactly as integration.yml does it.
SHARED_FILE="${SHARED_FILE:-09-bescheid.pdf}"
NOTICE_FILE="${NOTICE_FILE:-10-kuendigung.docx}"
OVERVIEW_FILE="${OVERVIEW_FILE:-11-uebersicht.odt}"
MEMO_FILE="${MEMO_FILE:-12-aktenvermerk.txt}"
SWISS_FILE="${SWISS_FILE:-15-schweiz-baubewilligung.pdf}"
AUSTRIAN_FILE="${AUSTRIAN_FILE:-16-oesterreich-mitteilung.pdf}"
REMINDER_FILE="${REMINDER_FILE:-30-nur-ein-bild.pdf}"

# The run number first, before anything at all happens. It costs nothing, it
# needs no box, and it is the one refusal that has to come before the first case
# rather than after the last one.
case "$CI_LAUF" in
    '' | *[!0-9]*)
        echo "98b-sprachfaelle: CI_LAUF carries no run number of a green integration.yml run" >&2
        echo "98b-sprachfaelle: that run drives these same ten cases on a fresh instance" >&2
        echo "98b-sprachfaelle: without foreign stock, and it is the half of the statement" >&2
        echo "98b-sprachfaelle: this box cannot make. Without it the figures of this run" >&2
        echo "98b-sprachfaelle: are incomplete, so the run does not start (DI-10-02)." >&2
        echo "98b-sprachfaelle: gh run list --workflow=integration.yml --status success" >&2
        exit 22
        ;;
esac

if ! command -v jq >/dev/null 2>&1; then
    echo "98b-sprachfaelle: jq is not on this box, and all twenty assertions read JSON with it" >&2
    echo "98b-sprachfaelle: install jq or run this block from a machine that has it" >&2
    exit 18
fi

mkdir -p "$OUT"
# The raw file of the new run directory, and its name follows the numbering of
# that directory rather than the one of the original.
ZIEL="${ZIEL:-$OUT/05-sprachfaelle.txt}"
WORK=$(mktemp -d)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT
# One line per red assertion in the second file, one line per red case in the
# first, one line per unmeasurable case in the third. All three are created
# empty, so that reading them later is never a question about whether anything
# ran.
: >"$WORK/fehler"
: >"$WORK/fehlertexte"
: >"$WORK/nichtmessbar"
mkdir -p "$WORK/fremd"

# The wrapper carries OC_PASS across the two layers that would otherwise eat it,
# and only when it is set: sudo clears the environment under env_reset, and
# docker exec passes none on of its own accord. The value stays out of every
# argument list, which is what T-10-27 asks for.
occ() {
    if [ -n "${OC_PASS:-}" ]; then
        sudo --preserve-env=OC_PASS docker exec -e OC_PASS \
            --user www-data "$NEXTCLOUD" php occ "$@"
    else
        sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
    fi
}

# The work stock out of one call of the status command. Two blocks of one output
# rather than two calls, because asking twice would let two answers disagree.
vorrat_von() {
    awk '/^Work stock/ {found = 1; next}
         found && /^  (scheduled|handed to the worker)/ {sum += $NF}
         END {print sum + 0}' "$1"
}

# The password of the account. Generated here, used out of the environment and
# out of a curl config file, and never written into an argument or a raw file.
KONTOPW=$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')
CURLRC="$WORK/curlrc"
printf 'user = "%s:%s"\n' "$KONTO" "$KONTOPW" >"$CURLRC"
chmod 600 "$CURLRC"
# The config file of the pre check. Its path is fixed here, its content is
# written in section 0, because the password is read there.
LASTRC="$WORK/lastcurlrc"

search() {
    curl -sfS -G -K "$CURLRC" \
        -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
        --data-urlencode "term=$1" \
        "$BASE/ocs/v2.php/search/providers/findling/search" -o "$2"
}

# The same route and the same header as the cases, asked as the owner of the
# load corpus. With an empty second argument it sends no limit either, which is
# the page the cases get; with a number it sends that limit.
fremd_suche() {
    if [ -n "$2" ]; then
        curl -sfS -G -K "$LASTRC" \
            -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
            --data-urlencode "term=$1" --data-urlencode "limit=$2" \
            "$BASE/ocs/v2.php/search/providers/findling/search" -o "$3"
    else
        curl -sfS -G -K "$LASTRC" \
            -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
            --data-urlencode "term=$1" \
            "$BASE/ocs/v2.php/search/providers/findling/search" -o "$3"
    fi
}

# Which case is being driven. It is a variable rather than an argument of fail,
# because the balance line counts CASES and not assertions: case 1 alone carries
# four of them, and four red assertions of one case are one red case and not
# four. Every case sets it once, right before its first search.
FALL=0

# A red assertion, and the foreign stock of its term stands in the same line.
# Below the threshold a term may still have a stock, and a reader who sees the
# zero next to a red case knows that this one is about the language chain.
fail() {
    fremd=$(cat "$WORK/fremd/$FALL" 2>/dev/null || echo 0)
    printf 'sprachfall %s ROT: %s (Fremdbestand %s Treffer, Schwelle %s)\n' \
        "$FALL" "$1" "${fremd:-0}" "$FREMD_SCHWELLE"
    cat "$2" 2>/dev/null || true
    printf 'fall %s\n' "$FALL" >>"$WORK/fehler"
    printf 'fall %s: %s\n' "$FALL" "$1" >>"$WORK/fehlertexte"
}

# The first of the two verdicts, and it comes first for every case. A case whose
# term the foreign stock has taken over is NICHT MESSBAR and gets no second
# verdict beside it: a case that cannot carry a statement must not carry one.
messbar() {
    fremd=$(cat "$WORK/fremd/$1" 2>/dev/null || echo '')
    if [ -z "$fremd" ]; then
        printf 'sprachfall %s NICHT MESSBAR (Fremdbestand nicht erhoben)\n' "$1"
        printf 'fall %s\n' "$1" >>"$WORK/nichtmessbar"
        return 1
    fi
    if [ "$fremd" -ge "$FREMD_SCHWELLE" ]; then
        printf 'sprachfall %s NICHT MESSBAR (Fremdbestand %s Treffer)\n' "$1" "$fremd"
        printf 'fall %s\n' "$1" >>"$WORK/nichtmessbar"
        return 1
    fi
    return 0
}

# The second verdict, and only a measurable case ever reaches it. A case that
# has written no red assertion is green, and it says so: a run in which nothing
# is printed for six of ten cases reads like six cases that never ran.
urteil() {
    if grep -q "^fall $1\$" "$WORK/fehler" 2>/dev/null; then
        return 0
    fi
    fremd=$(cat "$WORK/fremd/$1" 2>/dev/null || echo 0)
    printf 'sprachfall %s GRUEN (Fremdbestand %s Treffer)\n' "$1" "${fremd:-0}"
}

{
    date -u +'sprachfaelle-start %Y-%m-%dT%H:%M:%SZ'
    printf 'konto: %s (ausdruecklich nicht %s, siehe Kopf)\n' "$KONTO" "$LASTKONTO"
    printf 'korpus: %s\n' "$KORPUS"
    printf 'ci-beleg: integration.yml Lauf %s\n' "$CI_LAUF"

    echo "=== Abschnitt 0: die Vorpruefung des Fremdbestands (DI-10-02) ==="
    echo "-- gefragt wird jeder Begriff als das Konto, dem der Lastkorpus gehoert, ueber"
    echo "   dieselbe OCS-Route. Die Zahl daneben sagt, ob der Fall seine Aussage"
    echo "   ueberhaupt tragen kann; die Faelle selbst fragen danach als $KONTO --"
    echo 'vorpruefung-gefahren nein' >"$WORK/vorpruefung-urteil"
    if [ -z "${FINDLING_LOAD_PASSWORD:-}" ]; then
        FINDLING_LOAD_PASSWORD=$(sudo cat "$PWFILE" 2>/dev/null || true)
    fi
    if [ -z "${FINDLING_LOAD_PASSWORD:-}" ]; then
        echo "das Passwort des Kontos $LASTKONTO steht weder in der Umgebung"
        echo "(FINDLING_LOAD_PASSWORD) noch in der Datei, auf die PWFILE zeigt."
        echo "Ohne die Vorpruefung waere jedes Urteil wieder zweiwertig, und genau das"
        echo "ist der Befund DI-10-02. Der Lauf endet hier, statt ihn zu wiederholen."
        exit 19
    fi
    printf 'user = "%s:%s"\n' "$LASTKONTO" "$FINDLING_LOAD_PASSWORD" >"$LASTRC"
    chmod 600 "$LASTRC"
    printf 'fremdbestand-konto:    %s\n' "$LASTKONTO"
    printf 'fremdbestand-schwelle: %s Treffer (MAX_RECHECKS_ABSOLUTE, siehe Kopf)\n' "$FREMD_SCHWELLE"
    printf 'fremdbestand-tiefe:    %s\n' "$FREMD_TIEFE"
    # The ten terms in the order of their cases. Cases 6 and 7 ask the same word,
    # which is not an oversight of this table: case 6 asks it plain and case 7
    # behind a file type filter, and both stand or fall with the same stock.
    while IFS='|' read -r nummer begriff; do
        [ -n "$nummer" ] || continue
        if ! fremd_suche "$begriff" '' "$WORK/fremd-seite.json"; then
            echo "die Vorpruefung konnte den Begriff $begriff nicht fragen (Seite)"
            exit 19
        fi
        if ! fremd_suche "$begriff" "$FREMD_TIEFE" "$WORK/fremd-tiefe.json"; then
            echo "die Vorpruefung konnte den Begriff $begriff nicht fragen (Tiefe)"
            exit 19
        fi
        seite=$(jq -e -r '.ocs.data.entries | length' "$WORK/fremd-seite.json" 2>/dev/null || echo '')
        tiefe=$(jq -e -r '.ocs.data.entries | length' "$WORK/fremd-tiefe.json" 2>/dev/null || echo '')
        if [ -z "$seite" ] || [ -z "$tiefe" ]; then
            echo "die Antwort auf $begriff traegt keine lesbare Trefferliste"
            cat "$WORK/fremd-tiefe.json" 2>/dev/null || true
            exit 19
        fi
        printf '%s\n' "$tiefe" >"$WORK/fremd/$nummer"
        printf 'fremdbestand %s %s (Seite der Faelle), %s (bis Tiefe %s), Fall %s\n' \
            "$begriff" "$seite" "$tiefe" "$FREMD_TIEFE" "$nummer"
    done <<'BEGRIFFE'
1|Genehmigung
2|Frist
3|Mueller
4|Vertrag
5|"drei Monate"
6|bescheid
7|type:pdf bescheid
8|Belehrung
9|Auszug
10|Erinnerung
BEGRIFFE
    echo 'vorpruefung-gefahren ja' >"$WORK/vorpruefung-urteil"
    cat "$WORK/vorpruefung-urteil"

    echo "=== Section 1: the account, whose home is to hold nothing but the corpus ==="
    # The skeleton is switched off first, and this is not tidiness: without it
    # Nextcloud drops a manual, a photo folder and a readme into every new home,
    # and the counter assertions of the ten cases would be statements about
    # documents nobody chose. integration.yml does exactly this, for exactly this
    # reason. The previous value is read first and put back at the end.
    SKELETON_VORHER=$(occ config:system:get skeletondirectory 2>/dev/null || true)
    printf 'skeletondirectory vorher: %s\n' "${SKELETON_VORHER:-(leer oder nicht gesetzt)}"
    occ config:system:set skeletondirectory --value='' 2>&1 || true

    if occ user:info "$KONTO" >/dev/null 2>&1; then
        echo "das Konto existiert schon, es wird nicht neu angelegt"
        echo "-- Achtung: seine Heimat muss NUR den Korpus enthalten, sonst sind die"
        echo "   Faelle rot aus dem falschen Grund. Dieser Block ist abbrechbar (A7). --"
        # The password of an existing account is unknown here, so it is reset out
        # of the environment. Never an argument.
        OC_PASS="$KONTOPW" occ user:resetpassword --password-from-env "$KONTO" 2>&1 || true
    else
        OC_PASS="$KONTOPW" occ user:add --password-from-env "$KONTO" 2>&1
    fi
    occ user:info "$KONTO" 2>&1 | sed -n '1,6p' || true

    echo "=== Section 2: the corpus over WebDAV, the path a user takes ==="
    ZIELORDNER="$BASE/remote.php/dav/files/$KONTO/$ORDNER"
    curl -sS -o /dev/null -K "$CURLRC" -X MKCOL "$ZIELORDNER" || true
    date -u +'upload-vor %Y-%m-%dT%H:%M:%SZ'
    for pfad in "$KORPUS"/*; do
        name=$(basename "$pfad")
        code=$(curl -sS -o /dev/null -w '%{http_code}' -K "$CURLRC" \
            -T "$pfad" "$ZIELORDNER/$name" || echo 000)
        printf '%s %s\n' "$code" "$name" >>"$WORK/upload.txt"
    done
    date -u +'upload-nach %Y-%m-%dT%H:%M:%SZ'
    awk '{print $1}' "$WORK/upload.txt" | sort | uniq -c
    HOCHGELADEN=$(awk '$1 ~ /^2/ {n++} END {print n + 0}' "$WORK/upload.txt")
    printf 'dateien-hochgeladen %s\n' "$HOCHGELADEN"
    printf 'dateien-erwartet    %s\n' "$ERWARTETE_DATEIEN"
    if [ "$HOCHGELADEN" -eq "$ERWARTETE_DATEIEN" ]; then
        echo 'upload-vollstaendig ja' >"$WORK/upload-urteil"
    else
        echo 'upload-vollstaendig nein' >"$WORK/upload-urteil"
        grep -v '^2' "$WORK/upload.txt" || true
    fi
    cat "$WORK/upload-urteil"
    occ files:scan --path="/$KONTO/files/$ORDNER" 2>&1 | tail -6 || true

    echo "=== Section 3: the indexing, against the slowest clock ==="
    echo "-- $FRIST s first, because the poller backoff runs up to 300 s and the five"
    echo "   minute system cron needs two rounds before the first job of the app has"
    echo "   queued anything (pitfall 11) --"
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
    echo "-- and only NOW the verdicts, because skipped:no_text_layer is a temporary"
    echo "   verdict and reading it earlier would report the scan track as a failure --"
    cat "$WORK/status.txt"

    echo "=== Section 4: the ten cases, dreiwertig beurteilt ==="
    if [ "$(cat "$WORK/index-urteil")" != 'arbeitsvorrat-leer ja' ]; then
        echo "der Arbeitsvorrat ist nicht leer, die Faelle 8 bis 10 haengen an der OCR-Spur"
        echo "und wuerden hier aus dem falschen Grund rot sein; die Faelle laufen trotzdem,"
        echo "und die Bilanz ist mit dieser Zeile daneben zu lesen"
    fi

    # 1. The compound through one of its constituents. The file says
    # Grundstuecksverkehrsgenehmigung, the search says Genehmigung, and the
    # splitter is what closes the gap.
    FALL=1
    if messbar 1; then
        start=$(date +%s%N)
        search 'Genehmigung' "$WORK/compound.json" || true
        printf 'eine gewoehnliche Suche antwortete nach %sms\n' "$((($(date +%s%N) - start) / 1000000))"
        jq -e '.ocs.data.entries | length == 1' "$WORK/compound.json" >/dev/null 2>&1 ||
            fail "a compound searched through one constituent did not bring back exactly one file" "$WORK/compound.json"
        jq -e --arg name "$SHARED_FILE" '.ocs.data.entries[0].title == $name' "$WORK/compound.json" >/dev/null 2>&1 ||
            fail "the compound hit is not the German PDF of the corpus" "$WORK/compound.json"
        # The excerpt, and this is the assertion that separates a hit from a hit
        # with content: the subline has to carry the compound out of the
        # document. The fallback subline is the path, and the path does not
        # contain the word.
        jq -e '.ocs.data.entries[0].subline | ascii_downcase | contains("genehmigung")' "$WORK/compound.json" >/dev/null 2>&1 ||
            fail "the subline carries no excerpt from the document" "$WORK/compound.json"
        jq -e '.ocs.data.entries[0].subline | contains("<") | not' "$WORK/compound.json" >/dev/null 2>&1 ||
            fail "the excerpt carries markup, which the search dialog would show verbatim" "$WORK/compound.json"
        urteil 1
    fi

    # 2. The second compound, in a different file and a different format.
    FALL=2
    if messbar 2; then
        search 'Frist' "$WORK/frist.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/frist.json" >/dev/null 2>&1 ||
            fail "Frist did not bring back exactly the notice of termination" "$WORK/frist.json"
        jq -e --arg name "$NOTICE_FILE" '.ocs.data.entries[0].title == $name' "$WORK/frist.json" >/dev/null 2>&1 ||
            fail "the Frist hit is not the DOCX of the corpus" "$WORK/frist.json"
        urteil 2
    fi

    # 3. The written out umlaut. The file spells Mueller with the character, the
    # search with the two letters, and the query side variant joins them.
    FALL=3
    if messbar 3; then
        search 'Mueller' "$WORK/umlaut.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/umlaut.json" >/dev/null 2>&1 ||
            fail "the written out umlaut did not find the file that spells it with the character" "$WORK/umlaut.json"
        jq -e --arg name "$MEMO_FILE" '.ocs.data.entries[0].title == $name' "$WORK/umlaut.json" >/dev/null 2>&1 ||
            fail "the umlaut hit is not the file note of the corpus" "$WORK/umlaut.json"
        urteil 3
    fi

    # 4. Nominal inflection. The file says Vertraege, the search says Vertrag,
    # and the stemmer is what closes that gap.
    FALL=4
    if messbar 4; then
        search 'Vertrag' "$WORK/flexion.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/flexion.json" >/dev/null 2>&1 ||
            fail "the singular did not find the plural" "$WORK/flexion.json"
        jq -e --arg name "$OVERVIEW_FILE" '.ocs.data.entries[0].title == $name' "$WORK/flexion.json" >/dev/null 2>&1 ||
            fail "the inflection hit is not the ODT of the corpus" "$WORK/flexion.json"
        urteil 4
    fi

    # 5. The phrase. Only the file with the two words in that order.
    FALL=5
    if messbar 5; then
        search '"drei Monate"' "$WORK/phrase.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/phrase.json" >/dev/null 2>&1 ||
            fail "the phrase did not bring back exactly one file" "$WORK/phrase.json"
        jq -e --arg name "$NOTICE_FILE" '.ocs.data.entries[0].title == $name' "$WORK/phrase.json" >/dev/null 2>&1 ||
            fail "the phrase hit is not the DOCX of the corpus" "$WORK/phrase.json"
        urteil 5
    fi

    # 6. The exclusion, and the control that gives it meaning. Bescheid stands in
    # two files on purpose; without the control an exclusion that does nothing
    # would look exactly like one that works, so the control runs FIRST.
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

    # 7. The file type. There is no built in Nextcloud filter for it, so it
    # travels inside the search line and becomes a required term on ext.
    FALL=7
    if messbar 7; then
        search 'type:pdf bescheid' "$WORK/filetype.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/filetype.json" >/dev/null 2>&1 ||
            fail "the file type filter did not narrow the two hits down to the PDF" "$WORK/filetype.json"
        jq -e --arg name "$SHARED_FILE" '.ocs.data.entries[0].title == $name' "$WORK/filetype.json" >/dev/null 2>&1 ||
            fail "the file type filter kept the wrong file" "$WORK/filetype.json"
        urteil 7
    fi

    # 8. The third compound, in the scanned Swiss permit. The page says
    # Rechtsmittelbelehrung, the search says Belehrung, and split_compound is
    # what makes the second part of the word a term of its own. Belehrung stands
    # in the whole corpus only inside its compound, which is why this case
    # replaced a search for Vereinbarung that was green without the splitter.
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

    # 9. A compound that exists as pixels and in no other form. The scanned
    # Austrian notice says Grundbuchsauszug, the search says Auszug, and without
    # the OCR track there would be nothing to split in the first place.
    FALL=9
    if messbar 9; then
        search 'Auszug' "$WORK/auszug.json" || true
        jq -e '.ocs.data.entries | length == 1' "$WORK/auszug.json" >/dev/null 2>&1 ||
            fail "Auszug did not bring back exactly the scanned Austrian notice" "$WORK/auszug.json"
        jq -e --arg name "$AUSTRIAN_FILE" '.ocs.data.entries[0].title == $name' "$WORK/auszug.json" >/dev/null 2>&1 ||
            fail "the Auszug hit is not the Austrian notice of the corpus" "$WORK/auszug.json"
        urteil 9
    fi

    # 10. The same shape once more, in the file that is one image and nothing
    # else. It says Zahlungserinnerung, the search says Erinnerung.
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
    # Cases and assertions are counted apart, because they are two different
    # numbers: the balance line is about cases, and the list underneath it is
    # about assertions, of which case 1 alone carries four. The second figure of
    # the balance line is the one DI-10-02 is about: a bilanz with one figure is
    # exactly the misreading that turned four unmeasurable cases into four red
    # ones.
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
        echo "-- die nicht messbaren Faelle. Sie sind KEIN Sprachbefund: ihr Begriff hat"
        echo "   im Lastkorpus so viel Fremdbestand, dass die Kandidatenliste voll ist,"
        echo "   bevor eine eigene Datei darin vorkommt (DI-10-02) --"
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
    echo "nicht die Umgebung, und wo der Fremdbestand die Aussage frisst, steht NICHT"
    echo "MESSBAR und kein Urteil."

    echo "=== The skeleton setting, put back the way it was ==="
    if [ -n "${SKELETON_VORHER:-}" ]; then
        occ config:system:set skeletondirectory --value="$SKELETON_VORHER" 2>&1 || true
    else
        occ config:system:delete skeletondirectory 2>&1 || true
    fi
    occ config:system:get skeletondirectory 2>&1 || echo "(nicht gesetzt, wie vorher)"

    date -u +'sprachfaelle-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Everything below the pipeline, because the return code of a pipeline belongs to
# tee: an exit inside the block above would only leave the subshell, and the
# refusal would be a line in the raw file that nobody reads.
vorpruefung=$(cat "$WORK/vorpruefung-urteil" 2>/dev/null || echo 'vorpruefung-gefahren nein')
upload=$(cat "$WORK/upload-urteil" 2>/dev/null || echo 'upload-vollstaendig nein')
index=$(cat "$WORK/index-urteil" 2>/dev/null || echo 'arbeitsvorrat-leer nein')
rot=$(sort -u "$WORK/fehler" 2>/dev/null | grep -c . || true)
nichtmessbar=$(sort -u "$WORK/nichtmessbar" 2>/dev/null | grep -c . || true)

if [ "$vorpruefung" != 'vorpruefung-gefahren ja' ]; then
    echo "98b-sprachfaelle: the pre check of the foreign stock could not be driven" >&2
    echo "98b-sprachfaelle: without it every verdict would be two valued again, which" >&2
    echo "98b-sprachfaelle: is the whole of DI-10-02; $ZIEL says at which term it ended" >&2
    exit 19
fi

if [ "$upload" != 'upload-vollstaendig ja' ]; then
    echo "98b-sprachfaelle: the upload did not deliver $ERWARTETE_DATEIEN files" >&2
    echo "98b-sprachfaelle: a case over a corpus that is not all there says nothing" >&2
    exit 15
fi

if [ "$index" != 'arbeitsvorrat-leer ja' ]; then
    echo "98b-sprachfaelle: the work stock was still not empty at the round cap" >&2
    echo "98b-sprachfaelle: cases 8 to 10 hang on the OCR track, so their verdicts" >&2
    echo "98b-sprachfaelle: would be about an unfinished pass; this block is abandonable" >&2
    echo "98b-sprachfaelle: by design (assumption A7) and belongs in the report as a gap" >&2
    exit 16
fi

if [ "${rot:-0}" -gt 0 ]; then
    echo "98b-sprachfaelle: $rot of the measurable cases were red" >&2
    echo "98b-sprachfaelle: every one of them is its own statement, and $ZIEL has them" >&2
    exit 17
fi

if [ "${nichtmessbar:-0}" -ge 10 ]; then
    echo "98b-sprachfaelle: not one of the ten cases was measurable on this instance" >&2
    echo "98b-sprachfaelle: a run in which every term drowns in the foreign stock is a" >&2
    echo "98b-sprachfaelle: statement about the instance and not about the language" >&2
    echo "98b-sprachfaelle: chain; the CI run named in $ZIEL is the one that measures it" >&2
    exit 23
fi

echo "98B-SPRACHFAELLE-FERTIG"
