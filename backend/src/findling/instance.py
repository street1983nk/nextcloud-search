"""Which Nextcloud instance this persistent volume belongs to (DI-06.1-22).

The problem is not ours and cannot be fixed here. AppAPI names the data volume
of an ExApp after the app and after nothing else, so two Nextcloud instances on
the same docker service mount the same volume under the same name, and
``unregister --rm-data`` in one of them deletes the index, the state database
and the vector stock of the other. On 7 September 2026 that emptied a
measurement volume; the incident is written down in
``docs/measurements/2026-09-nachmessung-m7g``, section 12a. The fix belongs
upstream, and this module is the part that is in our hands: making the
constellation visible before it costs anything.

The mechanism is one file in the root of the volume. The first start of a
container writes the identity of its own instance into it, and every later
start compares. Three outcomes, and the third is the only one that changes
behaviour:

*The marker is ours*, or there is none: nothing happens, and this is the case of
every restart, every update and every re-register of the same instance. The
whole feature is worthless if it produces one false alarm here, which is why an
empty or unparsable marker counts as absent rather than as foreign: a kill
between create and write leaves a zero byte file, and reading that as another
instance would turn one interrupted start into a container that never indexes
again.

*The marker names another instance*: the volume is shared. The caller keeps the
indexing off and says so. Nothing is deleted, nothing is taken over and the
marker is left exactly as it is, because it is the only evidence of the sharing.

*This container cannot name itself*: the mechanism is skipped in silence.
``NEXTCLOUD_URL`` is one of the four variables AppAPI sets for every deployed
container, so a container without it is a bare local run and not a deployment
this check has anything to say about. Guessing here would either block a
healthy deployment or cry wolf, and both are worse than saying nothing.

**The identity is stored as a digest, never as the address it came from.** The
volume is mounted by the container of the other instance too, so a marker
carrying the address of instance A would hand that address to instance B. The
log line follows the rule of the rest of this container and prints a shortened
digest, which is enough to tell two instances apart and carries nothing that
could be read as a location.
"""

import hashlib
import json
import logging
import os
from typing import NamedTuple

from findling.config import settings

LOGGER = logging.getLogger("findling")

# The field of the marker. One name, in one place, because the file is read by
# every later version of this app.
IDENTITY_FIELD = "instance"

# How much of the digest a log line carries. Enough to tell two instances of one
# box apart and to recognise the same one across two starts, and short enough
# that nobody mistakes it for something to look up.
DIGEST_CHARS = 12


class Claim(NamedTuple):
    """Who this volume belongs to, as far as this start could tell.

    Both fields are shortened digests, and both are empty when this container
    has no identity, which is the case the caller treats as "nothing to say".
    ``other`` is empty whenever the volume is ours, so it is the one field a
    caller has to look at to decide anything.
    """

    own: str = ""
    other: str = ""


def fingerprint_of(url: str) -> str:
    """The identity of one instance, as a digest of its normalised address.

    Normalised exactly the way the client library normalises ``NEXTCLOUD_URL``,
    trailing slash and ``index.php`` and all: AppAPI hands the same instance
    through in several spellings, and a digest over the raw value would make one
    instance look like two and would report a finding on an ordinary restart.

    An empty address gives an empty digest and not the digest of the empty
    string. The difference is the whole of claim five: "no identity" has to stay
    distinguishable from "an identity that happens to be blank", otherwise every
    container without the variable would recognise every other one as itself.
    """
    normalised = url.strip().removesuffix("/").removesuffix("/index.php").removesuffix("/")
    if not normalised:
        return ""
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def _own_identity() -> str:
    """The digest of this container's instance, empty when it does not know.

    Read from the environment on every call rather than through ``settings()``.
    ``NEXTCLOUD_URL`` belongs to AppAPI and not to this app, exactly like
    ``APP_VERSION`` on the status route, and a value that AppAPI changed on a
    restart has to be the value this comparison uses.
    """
    return fingerprint_of(os.environ.get("NEXTCLOUD_URL", ""))


def _stored_identity() -> str:
    """The identity in the marker, empty for absent, unreadable or broken.

    Every failure collapses into the same answer on purpose. A marker that
    cannot be read says nothing about which instance owns the volume, and the
    honest reading of "says nothing" is "there is no marker": the caller then
    writes one, and a start that was interrupted halfway repairs itself instead
    of alarming for ever.

    Only the class name of a failure is logged, the rule of every log line that
    touches the volume: the message of an OSError carries the path it was raised
    on, and the path of the volume is not ours to print.
    """
    marker = settings().instance_marker
    if not marker.is_file():
        return ""
    try:
        content = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        LOGGER.warning("the instance marker of this volume could not be read, a %s", type(error).__name__)
        return ""
    if not isinstance(content, dict):
        return ""
    identity = content.get(IDENTITY_FIELD)
    return identity.strip() if isinstance(identity, str) else ""


def _write_the_marker(identity: str) -> None:
    """Leave the identity of this instance in the volume.

    A failure is a warning and never more. The marker is a warning mechanism,
    and a warning mechanism able to stop a container would be worse than no
    warning at all: a volume that is full or read only would keep a perfectly
    healthy deployment from indexing.

    The root is not created here, for the reason the entry point states about
    the arming mark: AppAPI creates the volume before it starts the container,
    and where it did not, the write fails, the warning says so and the container
    comes up exactly as it did before this file existed.
    """
    try:
        settings().instance_marker.write_text(json.dumps({IDENTITY_FIELD: identity}), encoding="utf-8")
    except OSError as error:
        LOGGER.warning("the instance marker could not be written to the volume, an %s", type(error).__name__)


def claim_the_volume() -> Claim:
    """Compare this instance against the marker, and write one where none is.

    Called once per start, off the event loop. Returns what the caller needs to
    decide: an empty ``other`` means carry on, a filled one means this volume
    belongs to somebody else.

    An existing marker of our own is deliberately left untouched instead of
    being rewritten with the same content. Its timestamp then says when this
    instance first claimed the volume, which is the one thing about the file
    worth reading by hand, and a rewrite on every start would replace that with
    the time of the last restart for no gain at all.
    """
    own = _own_identity()
    if not own:
        return Claim()
    stored = _stored_identity()
    if not stored:
        _write_the_marker(own)
        return Claim(own=own[:DIGEST_CHARS])
    if stored == own:
        return Claim(own=own[:DIGEST_CHARS])
    return Claim(own=own[:DIGEST_CHARS], other=stored[:DIGEST_CHARS])


def volume_is_shared() -> bool:
    """True when the marker in the volume names another instance.

    A read of its own rather than a verdict cached from the start, so that the
    status route can be asked in a process whose lifespan never ran, which is
    what a test client without a context manager is, and so that nothing has to
    be invalidated. It writes nothing: the claim above is the one place that
    does, and a status page that took a volume over would be absurd.
    """
    own = _own_identity()
    if not own:
        return False
    stored = _stored_identity()
    return bool(stored) and stored != own
