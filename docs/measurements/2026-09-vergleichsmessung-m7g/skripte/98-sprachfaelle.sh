#!/bin/sh
# The ten German language cases on the box, against an account of their own.
#
# **Why an account of its own, and this is the whole point of the step**
# (pitfall 3). Every case asserts `entries | length == 1`, and the load test
# corpus of this box carries the same words: build_load_corpus.py writes Frist
# (line 179), Genehmigung (182), Grundstuecksverkehrsgenehmigung (186),
# Kuendigungsfrist (195), Vertrag (229) and a sentence with Auszug (608). The
# uniqueness promise of the cases is measured in
# backend/tests/test_corpus_terms.py against the THIRTY NINE FILE reference
# corpus and never against the load corpus. Against the load test account the
# cases would break with length == 2 instead of 1, and they would break for a
# reason that says nothing about the language chain. The ACL chain separates the
# two stocks, so what is needed is an account whose home holds nothing but
# testdata/corpus. The name of that account is a variable and it is expressly
# NOT lasttest.
#
# **The second half of the same pitfall.** Cases 8 to 10 hang on the OCR track,
# because their words exist as pixels and in no other form. The account therefore
# needs a FINISHED OCR pass, and 21 rendered pages at roughly 3,5 s each are a
# few minutes, but they are not nothing. Verdicts are read only once the work
# stock is empty, because skipped:no_text_layer is a TEMPORARY verdict: it is the
# state of a file that has been handed to the scan track and not the state of a
# file that has no text.
#
# **Assumption A7 of the research, and it is why this block may be abandoned.**
# This combination, an account of its own plus the reference corpus plus this
# box, has never been driven. A case can go red because a word does after all
# stand in a second file. This block is therefore its own, abandonable step and
# never a precondition of the report: if it breaks off, that goes into the report
# as a named gap with the CI proof beside it.
#
# The searches run over the OCS route with the OCS-APIRequest header, so over the
# final PHP recheck and not against the container. The account is created with
# occ user:add --password-from-env out of OC_PASS, so the password is never an
# argument (T-10-27); the curl calls take their credential out of a config file
# with mode 600 for the same reason, which is the shape aio_install_check.sh
# uses.
#
# The corpus arrives over WebDAV, which is the path a user takes. A docker cp
# into the data store would be faster and is expressly not the way: the user path
# is the question.
#
# All ten cases are driven even after a red one, and the failures are counted
# rather than thrown: a single red case must not drag nine unmeasured ones behind
# it. The balance line at the end is "sprachfaelle bestanden <n> von 10".
#
# The exit codes: 15 the upload did not deliver 39 files, 16 the work stock was
# still not empty at the round cap, 17 at least one case was red, 18 jq is not on
# this box.
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
# The run number of the last green integration.yml run, set by the caller. It is
# the CI proof the number of this step stands next to.
CI_LAUF="${CI_LAUF:-unbekannt}"

# The seven file names of the cases. Named here so that a rename of a corpus file
# breaks in one place instead of in ten, exactly as integration.yml does it.
SHARED_FILE="${SHARED_FILE:-09-bescheid.pdf}"
NOTICE_FILE="${NOTICE_FILE:-10-kuendigung.docx}"
OVERVIEW_FILE="${OVERVIEW_FILE:-11-uebersicht.odt}"
MEMO_FILE="${MEMO_FILE:-12-aktenvermerk.txt}"
SWISS_FILE="${SWISS_FILE:-15-schweiz-baubewilligung.pdf}"
AUSTRIAN_FILE="${AUSTRIAN_FILE:-16-oesterreich-mitteilung.pdf}"
REMINDER_FILE="${REMINDER_FILE:-30-nur-ein-bild.pdf}"

if ! command -v jq >/dev/null 2>&1; then
    echo "98-sprachfaelle: jq is not on this box, and all twenty assertions read JSON with it" >&2
    echo "98-sprachfaelle: install jq or run this block from a machine that has it" >&2
    exit 18
fi

mkdir -p "$OUT"
ZIEL="$OUT/98-sprachfaelle.txt"
WORK=$(mktemp -d)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT
# One line per red assertion in the second file, one line per red case in the
# first. Both are created empty, so that reading them later is never a question
# about whether anything ran.
: >"$WORK/fehler"
: >"$WORK/fehlertexte"

occ() { sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"; }

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

search() {
    curl -sfS -G -K "$CURLRC" \
        -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
        --data-urlencode "term=$1" \
        "$BASE/ocs/v2.php/search/providers/findling/search" -o "$2"
}

# Which case is being driven. It is a variable rather than an argument of fail,
# because the balance line counts CASES and not assertions: case 1 alone carries
# four of them, and four red assertions of one case are one red case and not
# four. Every case sets it once, right before its first search.
FALL=0

fail() {
    printf 'sprachfall %s ROT: %s\n' "$FALL" "$1"
    cat "$2" 2>/dev/null || true
    printf 'fall %s\n' "$FALL" >>"$WORK/fehler"
    printf 'fall %s: %s\n' "$FALL" "$1" >>"$WORK/fehlertexte"
}

{
    date -u +'sprachfaelle-start %Y-%m-%dT%H:%M:%SZ'
    printf 'konto: %s (ausdruecklich nicht lasttest, siehe Kopf)\n' "$KONTO"
    printf 'korpus: %s\n' "$KORPUS"
    printf 'ci-beleg: integration.yml Lauf %s\n' "$CI_LAUF"

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

    echo "=== Section 4: the ten cases, all of them, red ones counted ==="
    if [ "$(cat "$WORK/index-urteil")" != 'arbeitsvorrat-leer ja' ]; then
        echo "der Arbeitsvorrat ist nicht leer, die Faelle 8 bis 10 haengen an der OCR-Spur"
        echo "und wuerden hier aus dem falschen Grund rot sein; die Faelle laufen trotzdem,"
        echo "und die Bilanz ist mit dieser Zeile daneben zu lesen"
    fi

    # 1. The compound through one of its constituents. The file says
    # Grundstuecksverkehrsgenehmigung, the search says Genehmigung, and the
    # splitter is what closes the gap.
    FALL=1
    start=$(date +%s%N)
    search 'Genehmigung' "$WORK/compound.json" || true
    printf 'eine gewoehnliche Suche antwortete nach %sms\n' "$((($(date +%s%N) - start) / 1000000))"
    jq -e '.ocs.data.entries | length == 1' "$WORK/compound.json" >/dev/null 2>&1 ||
        fail "a compound searched through one constituent did not bring back exactly one file" "$WORK/compound.json"
    jq -e --arg name "$SHARED_FILE" '.ocs.data.entries[0].title == $name' "$WORK/compound.json" >/dev/null 2>&1 ||
        fail "the compound hit is not the German PDF of the corpus" "$WORK/compound.json"
    # The excerpt, and this is the assertion that separates a hit from a hit with
    # content: the subline has to carry the compound out of the document. The
    # fallback subline is the path, and the path does not contain the word.
    jq -e '.ocs.data.entries[0].subline | ascii_downcase | contains("genehmigung")' "$WORK/compound.json" >/dev/null 2>&1 ||
        fail "the subline carries no excerpt from the document" "$WORK/compound.json"
    jq -e '.ocs.data.entries[0].subline | contains("<") | not' "$WORK/compound.json" >/dev/null 2>&1 ||
        fail "the excerpt carries markup, which the search dialog would show verbatim" "$WORK/compound.json"

    # 2. The second compound, in a different file and a different format.
    FALL=2
    search 'Frist' "$WORK/frist.json" || true
    jq -e '.ocs.data.entries | length == 1' "$WORK/frist.json" >/dev/null 2>&1 ||
        fail "Frist did not bring back exactly the notice of termination" "$WORK/frist.json"
    jq -e --arg name "$NOTICE_FILE" '.ocs.data.entries[0].title == $name' "$WORK/frist.json" >/dev/null 2>&1 ||
        fail "the Frist hit is not the DOCX of the corpus" "$WORK/frist.json"

    # 3. The written out umlaut. The file spells Mueller with the character, the
    # search with the two letters, and the query side variant joins them.
    FALL=3
    search 'Mueller' "$WORK/umlaut.json" || true
    jq -e '.ocs.data.entries | length == 1' "$WORK/umlaut.json" >/dev/null 2>&1 ||
        fail "the written out umlaut did not find the file that spells it with the character" "$WORK/umlaut.json"
    jq -e --arg name "$MEMO_FILE" '.ocs.data.entries[0].title == $name' "$WORK/umlaut.json" >/dev/null 2>&1 ||
        fail "the umlaut hit is not the file note of the corpus" "$WORK/umlaut.json"

    # 4. Nominal inflection. The file says Vertraege, the search says Vertrag,
    # and the stemmer is what closes that gap.
    FALL=4
    search 'Vertrag' "$WORK/flexion.json" || true
    jq -e '.ocs.data.entries | length == 1' "$WORK/flexion.json" >/dev/null 2>&1 ||
        fail "the singular did not find the plural" "$WORK/flexion.json"
    jq -e --arg name "$OVERVIEW_FILE" '.ocs.data.entries[0].title == $name' "$WORK/flexion.json" >/dev/null 2>&1 ||
        fail "the inflection hit is not the ODT of the corpus" "$WORK/flexion.json"

    # 5. The phrase. Only the file with the two words in that order.
    FALL=5
    search '"drei Monate"' "$WORK/phrase.json" || true
    jq -e '.ocs.data.entries | length == 1' "$WORK/phrase.json" >/dev/null 2>&1 ||
        fail "the phrase did not bring back exactly one file" "$WORK/phrase.json"
    jq -e --arg name "$NOTICE_FILE" '.ocs.data.entries[0].title == $name' "$WORK/phrase.json" >/dev/null 2>&1 ||
        fail "the phrase hit is not the DOCX of the corpus" "$WORK/phrase.json"

    # 6. The exclusion, and the control that gives it meaning. Bescheid stands in
    # two files on purpose; without the control an exclusion that does nothing
    # would look exactly like one that works, so the control runs FIRST.
    FALL=6
    search 'bescheid' "$WORK/both.json" || true
    jq -e '.ocs.data.entries | length == 2' "$WORK/both.json" >/dev/null 2>&1 ||
        fail "the word that stands in two files did not bring back two files" "$WORK/both.json"
    search 'bescheid -frist' "$WORK/excluded.json" || true
    jq -e '.ocs.data.entries | length == 1' "$WORK/excluded.json" >/dev/null 2>&1 ||
        fail "the minus did not remove the second file" "$WORK/excluded.json"
    jq -e --arg name "$SHARED_FILE" '.ocs.data.entries[0].title == $name' "$WORK/excluded.json" >/dev/null 2>&1 ||
        fail "the exclusion removed the wrong file" "$WORK/excluded.json"

    # 7. The file type. There is no built in Nextcloud filter for it, so it
    # travels inside the search line and becomes a required term on ext.
    FALL=7
    search 'type:pdf bescheid' "$WORK/filetype.json" || true
    jq -e '.ocs.data.entries | length == 1' "$WORK/filetype.json" >/dev/null 2>&1 ||
        fail "the file type filter did not narrow the two hits down to the PDF" "$WORK/filetype.json"
    jq -e --arg name "$SHARED_FILE" '.ocs.data.entries[0].title == $name' "$WORK/filetype.json" >/dev/null 2>&1 ||
        fail "the file type filter kept the wrong file" "$WORK/filetype.json"

    # 8. The third compound, in the scanned Swiss permit. The page says
    # Rechtsmittelbelehrung, the search says Belehrung, and split_compound is
    # what makes the second part of the word a term of its own. Belehrung stands
    # in the whole corpus only inside its compound, which is why this case
    # replaced a search for Vereinbarung that was green without the splitter.
    FALL=8
    search 'Belehrung' "$WORK/belehrung.json" || true
    jq -e '.ocs.data.entries | length == 1' "$WORK/belehrung.json" >/dev/null 2>&1 ||
        fail "Belehrung did not bring back exactly the scanned Swiss permit" "$WORK/belehrung.json"
    jq -e --arg name "$SWISS_FILE" '.ocs.data.entries[0].title == $name' "$WORK/belehrung.json" >/dev/null 2>&1 ||
        fail "the Belehrung hit is not the Swiss permit of the corpus" "$WORK/belehrung.json"
    jq -e '.ocs.data.entries[0].subline | ascii_downcase | contains("belehrung")' "$WORK/belehrung.json" >/dev/null 2>&1 ||
        fail "the Belehrung hit carries no excerpt from the document" "$WORK/belehrung.json"
    jq -e '.ocs.data.entries[0].subline | contains("<") | not' "$WORK/belehrung.json" >/dev/null 2>&1 ||
        fail "the Belehrung excerpt carries markup, which the search dialog would show verbatim" "$WORK/belehrung.json"

    # 9. A compound that exists as pixels and in no other form. The scanned
    # Austrian notice says Grundbuchsauszug, the search says Auszug, and without
    # the OCR track there would be nothing to split in the first place.
    FALL=9
    search 'Auszug' "$WORK/auszug.json" || true
    jq -e '.ocs.data.entries | length == 1' "$WORK/auszug.json" >/dev/null 2>&1 ||
        fail "Auszug did not bring back exactly the scanned Austrian notice" "$WORK/auszug.json"
    jq -e --arg name "$AUSTRIAN_FILE" '.ocs.data.entries[0].title == $name' "$WORK/auszug.json" >/dev/null 2>&1 ||
        fail "the Auszug hit is not the Austrian notice of the corpus" "$WORK/auszug.json"

    # 10. The same shape once more, in the file that is one image and nothing
    # else. It says Zahlungserinnerung, the search says Erinnerung.
    FALL=10
    search 'Erinnerung' "$WORK/erinnerung.json" || true
    jq -e '.ocs.data.entries | length == 1' "$WORK/erinnerung.json" >/dev/null 2>&1 ||
        fail "Erinnerung did not bring back exactly the one page reminder" "$WORK/erinnerung.json"
    jq -e --arg name "$REMINDER_FILE" '.ocs.data.entries[0].title == $name' "$WORK/erinnerung.json" >/dev/null 2>&1 ||
        fail "the Erinnerung hit is not the image only PDF of the corpus" "$WORK/erinnerung.json"

    echo "=== The balance of the ten cases ==="
    # Cases and assertions are counted apart, because they are two different
    # numbers: the balance line is about cases, and the list underneath it is
    # about assertions, of which case 1 alone carries four.
    ROT=$(sort -u "$WORK/fehler" | grep -c . || true)
    ZEILEN=$(grep -c . "$WORK/fehlertexte" 2>/dev/null || true)
    BESTANDEN=$((10 - ROT))
    [ "$BESTANDEN" -ge 0 ] || BESTANDEN=0
    printf 'sprachfaelle bestanden %s von 10\n' "$BESTANDEN"
    printf 'rote faelle %s, rote zusicherungen %s\n' "$ROT" "${ZEILEN:-0}"
    if [ "$ROT" -gt 0 ]; then
        echo "-- die roten Zusicherungen im Wortlaut, jede eine eigene Aussage --"
        cat "$WORK/fehlertexte"
        echo "-- die roten Faelle --"
        sort -u "$WORK/fehler"
    fi

    echo "=== Section 5: the classification of this number ==="
    echo "Fuer diese zehn Faelle gibt es KEINE v1.0-Entsprechung auf dieser Box:"
    echo "weder der Semantiklauf vom 05.09. noch die Nachmessung vom 07.09. hat sie"
    echo "gefahren. Die Zahl dieses Schrittes ist damit eine ERSTMESSUNG neben einem"
    echo "CI-Beleg und keine Vergleichszeile."
    printf 'ci-beleg: der letzte gruene integration.yml-Lauf ist %s\n' "$CI_LAUF"
    echo "Der CI-Lauf misst dieselben zehn Faelle auf amd64 gegen eine frische Instanz"
    echo "mit dem PHP-Entwicklungsserver; dieser Schritt misst sie auf arm64 gegen eine"
    echo "All-in-One-Instanz mit vollem Vektorbestand. Gleich ist die Aussage, nicht die"
    echo "Umgebung."

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
upload=$(cat "$WORK/upload-urteil" 2>/dev/null || echo 'upload-vollstaendig nein')
index=$(cat "$WORK/index-urteil" 2>/dev/null || echo 'arbeitsvorrat-leer nein')
rot=$(sort -u "$WORK/fehler" 2>/dev/null | grep -c . || true)

if [ "$upload" != 'upload-vollstaendig ja' ]; then
    echo "98-sprachfaelle: the upload did not deliver $ERWARTETE_DATEIEN files" >&2
    echo "98-sprachfaelle: a case over a corpus that is not all there says nothing" >&2
    exit 15
fi

if [ "$index" != 'arbeitsvorrat-leer ja' ]; then
    echo "98-sprachfaelle: the work stock was still not empty at the round cap" >&2
    echo "98-sprachfaelle: cases 8 to 10 hang on the OCR track, so their verdicts" >&2
    echo "98-sprachfaelle: would be about an unfinished pass; this block is abandonable" >&2
    echo "98-sprachfaelle: by design (assumption A7) and belongs in the report as a gap" >&2
    exit 16
fi

if [ "${rot:-0}" -gt 0 ]; then
    echo "98-sprachfaelle: $rot of the ten cases were red" >&2
    echo "98-sprachfaelle: every one of them is its own statement, and $ZIEL has them" >&2
    exit 17
fi

echo "98-SPRACHFAELLE-FERTIG"
