#!/bin/sh
# Walk the cookie login and the result page by hand, the way the parity job does.
#
# The login runs over a cookie jar and not over basic auth with the OCS header,
# because the result page is not an OCS route: it is an ordinary page of the app
# framework, and it answers a request without a session with a redirect to the
# login form rather than with an answer. The GET of the page needs no request
# token of its own, because PageController::index() carries NoCSRFRequired and
# changes nothing on the instance. The token is read out of the login form for
# one single call, the login POST, and for nothing else.
#
# Usage:
#
#     scripts/dev/probe_page_login.sh <user> <password> <term>
#     FINDLING_BASE_URL=http://localhost:8080 \
#       scripts/dev/probe_page_login.sh testuser <password> Genehmigung
#
# It takes the account as arguments and has none built in. The accounts of the
# development instance are in docs/dev-setup.md, and a password in a checked in
# file is a password in the history of a public repository.
#
# It is checked in rather than thrown away after its one run. The next person who
# debugs the search-parity job of .github/workflows/integration.yml wants to walk
# exactly this path by hand, and a script in the repository is cheaper than an
# instruction that goes stale.
#
# Exit code 0 means the page answered with at least one hit row. Everything else
# is exit code 1 with the reason on standard error, and the reason distinguishes
# the three ways of getting no rows: the error block of the page, its empty
# state, and an answer that is not the result page at all.
set -eu

BASE_URL="${FINDLING_BASE_URL:-http://localhost:8090}"

if [ "$#" -ne 3 ]; then
	echo "usage: $0 <user> <password> <term>" >&2
	echo "the base url comes from FINDLING_BASE_URL and defaults to ${BASE_URL}" >&2
	exit 1
fi

USER_NAME=$1
USER_PASS=$2
SEARCH_TERM=$3

WORK=$(mktemp -d)
trap 'rm -rf "${WORK}"' EXIT INT TERM
JAR="${WORK}/cookies.txt"
LOGIN_FORM="${WORK}/login.html"
PAGE="${WORK}/page.html"

# 1. The login form, with the jar that carries the session from here on.
if ! curl -sfS -c "${JAR}" -o "${LOGIN_FORM}" "${BASE_URL}/login"; then
	echo "the login form of ${BASE_URL} could not be fetched, so there is no instance to log in to" >&2
	exit 1
fi

# The token stands in the head of every page of Nextcloud as data-requesttoken.
# Read from the form rather than from a cookie: it is a value the server signs
# for this session, and the login POST is rejected without it.
TOKEN=$(sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' "${LOGIN_FORM}" | head -1)
if [ -z "${TOKEN}" ]; then
	echo "the login form of ${BASE_URL} carries no data-requesttoken, so the login POST cannot be signed" >&2
	exit 1
fi

# 2. The login itself. Not followed: the answer is a redirect either way, and its
# target is what tells a successful login from a refused one. A refused login
# goes back to /login, a successful one goes on into the instance.
#
# The Origin header is not decoration and it is the detail assumption A7 was
# afraid of. LoginController::tryLogin of Nextcloud 34 refuses a login whose
# origin is empty or not a trusted domain before it ever looks at the password,
# with the same redirect back to the form that a wrong password produces. A
# browser sets the header, curl does not, so the probe sets it to the address it
# is talking to.
REDIRECT=$(curl -sS -b "${JAR}" -c "${JAR}" -o /dev/null -w '%{redirect_url}' \
	-H "Origin: ${BASE_URL}" \
	--data-urlencode "user=${USER_NAME}" \
	--data-urlencode "password=${USER_PASS}" \
	--data-urlencode "requesttoken=${TOKEN}" \
	"${BASE_URL}/login")

case "${REDIRECT}" in
*/login | */login\?*)
	echo "the instance sent ${USER_NAME} back to the login form: the password was refused" >&2
	exit 1
	;;
'')
	echo "the login of ${USER_NAME} did not answer with a redirect at all, so the session was not established" >&2
	exit 1
	;;
esac

# 3. The page, with the session and without a token. The same call the parity job
# makes, down to the query parameter.
STATUS=$(curl -sS -b "${JAR}" -c "${JAR}" -o "${PAGE}" -w '%{http_code}' \
	--get --data-urlencode "query=${SEARCH_TERM}" \
	"${BASE_URL}/apps/findling/")

if [ "${STATUS}" != "200" ]; then
	echo "the result page answered ${STATUS} and not 200 for ${USER_NAME}" >&2
	exit 1
fi

# 4. The rows. Counted as occurrences and not as lines, because the row id is the
# contract the parity comparison reads and two rows could share a line.
ROWS=$(grep -o 'id="findling-hit-[0-9]*"' "${PAGE}" | wc -l | tr -d ' ')

if [ "${ROWS}" -gt 0 ]; then
	echo "${USER_NAME} is logged in and the page answers ${ROWS} hit row(s) for '${SEARCH_TERM}'"
	exit 0
fi

# No rows, and the page says which of the three kinds of nothing this is. The
# same three cases the HTML reader of scripts/ci/parity_diff.py tells apart, for
# the same reason: an unreadable answer must never pass as an empty result.
if grep -q 'findling-banner--error' "${PAGE}"; then
	echo "the page rendered its error block for '${SEARCH_TERM}': the backend did not answer, so this is not a result" >&2
	exit 1
fi

if grep -q 'findling-empty' "${PAGE}"; then
	echo "the page rendered its empty state: '${SEARCH_TERM}' has no hits for ${USER_NAME}" >&2
	exit 1
fi

echo "the answer carries neither a hit row nor the empty state, so it is not the result page" >&2
exit 1
