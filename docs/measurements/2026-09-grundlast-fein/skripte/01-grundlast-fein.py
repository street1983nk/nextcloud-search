#!/usr/bin/env python3
"""Which part of the 543,7 MB belongs to whom, one candidate per step.

The step by step base load of the follow up measurement
(2026-09-nachmessung-m7g/rohdaten/63-grundlast.txt) puts 543,7 MB of 678 MB into
exactly two lines: ``11-tokenizer-gelesen`` costs 269,4 MB and
``12-chunker-gebaut-und-gefahren`` another 274,3 MB. Neither of them is the model
weights, which arrive later and cost 391,9 MB of their own. Two lines that big
are an owner nobody has named yet, and a plan built on them would be built on a
guess.

So the two lines are taken apart. Steps 00 to 10 and 13 to 15 are carried over
from ``2026-09-05-semantiklauf-m7g/skripte/52-woher-die-grundlast.py`` word for
word, including their names: the comparability with the follow up measurement
rests on them being the same steps in the same order, and a renamed step turns a
comparison figure into a merely adjacent one. Between them, five separately named
candidates take the place of the two coarse ones:

  11a  the module import of tokenizers, without any instance
  11b  the first tokenizer instance out of tokenizer.json
  12a  the build of the splitter through from_huggingface_tokenizer
  12b  the first chunker run over a text
  12c  the second chunker run over the same text

One informative step follows the whole series:

  16   a SECOND tokenizer instance out of the same file

That last one is a measurement and NOT a proposal. The two tokenizer instances of
this project are a locked decision (.planning/STATE.md:159, confirmed upstream by
semantic-text-splitter): ``Tokenizer.enable_truncation`` is a property of the
object, so one shared instance would carry the 512 token window of the inference
session into ``chunker._first_tokens`` and would silently halve the 1024 token
cap of D-01. A high figure on step 16 does not lift that lock. It is here so that
the price of one instance can be read separately from the price of the module
import, and for no other purpose.

Step 16 sits at the END rather than between 12c and 13 on purpose. An extra
allocation before step 13 would move steps 13 to 15 away from the reference
series, and those three are the ones the comparison with 63-grundlast.txt hangs
on.

The text this script chunks with is a blind text written into this file. No user
content, no file from a volume, no text content in the output. The script opens
no network connection and sends nothing; it reads /proc/self/status, the model
directory of the image and the word list of the image, and it prints numbers.
"""

from __future__ import annotations

import datetime
import os
import platform
from pathlib import Path

# The same sentence the reference script cuts with, repeated the same number of
# times, so that step 12b can be held against the coarse step 12 of the follow up
# measurement instead of merely next to it.
BLINDTEXT = "Ein Satz zum Schneiden, damit der Schneider wirklich arbeitet. " * 60

schritte: list[tuple[str, int]] = []


def rss_kb() -> int:
    for zeile in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        if zeile.startswith("VmRSS:"):
            return int(zeile.split()[1])
    return -1


def merke(name: str) -> None:
    schritte.append((name, rss_kb()))


def umgebung(name: str) -> str:
    return os.environ.get(name, "") or "unknown"


def kopfzeilen() -> list[str]:
    """Architecture, image digest and date, so the numbers keep their machine.

    A measurement without its machine is a claim that gets quoted at the wrong
    hardware (T-06-07). The digest cannot be read from inside a container, so the
    caller hands it over in an environment variable; an empty one is printed as
    unknown rather than left out, because a missing field is easier to notice
    than a missing line.
    """
    jetzt = datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [
        "date=" + jetzt,
        "arch=" + platform.machine(),
        "python=" + platform.python_version(),
        "image_digest=" + umgebung("FINDLING_MEASURE_DIGEST"),
        "image_ref=" + umgebung("FINDLING_MEASURE_IMAGE"),
        "runner_role=" + umgebung("FINDLING_MEASURE_ROLE"),
    ]


def main() -> int:
    merke("00-leerer-prozess")

    from findling.config import settings

    merke("01-config-importiert")
    s = settings()
    merke("02-settings-gelesen")

    from findling.index import analyzer, wordlist

    merke("03-index-module-importiert")

    from findling.embed import chunker, model

    merke("04-embed-module-importiert")

    from findling.store import vectors

    merke("05-store-vectors-importiert")

    from findling.worker import poller

    merke("06-poller-importiert")

    from findling.api import resources

    merke("07-api-resources-importiert")

    from findling import main as hauptmodul

    merke("08-findling-main-importiert")

    # Jetzt die Bauwege, einzeln, in der Reihenfolge des Containers.
    quelle = wordlist.SYSTEM_WORDLIST
    eintraege = wordlist.load_constituents(quelle) if quelle.exists() else []
    if not isinstance(eintraege, list):
        eintraege = list(eintraege)
    schritte.append(("09-wortliste-gelesen-" + str(len(eintraege)), rss_kb()))

    if eintraege:
        analyzer.cached_german_analyzer(wordlist.wordlist_hash(eintraege), tuple(eintraege))
    merke("10-deutscher-automat-gebaut")

    # 11 and 12 of the reference, taken apart. open_tokenizer imports the module
    # inside the function, so the import is pulled out here and paid first: that
    # is the only way the module and the instance end up on separate lines.
    import tokenizers

    merke("11a-tokenizers-modul-importiert")

    tokenizer = model.open_tokenizer(s.embed_model_dir)
    merke("11b-erste-tokenizer-instanz")

    schneider = chunker.make_splitter(
        tokenizer, chunk_tokens=s.embed_chunk_tokens, overlap=s.embed_chunk_overlap
    )
    merke("12a-splitter-gebaut")

    spannen = chunker.chunk_spans(
        BLINDTEXT, tokenizer=tokenizer, splitter=schneider, token_cap=s.embed_token_cap
    )
    schritte.append(("12b-erster-chunkerlauf-" + str(len(spannen)), rss_kb()))

    spannen2 = chunker.chunk_spans(
        BLINDTEXT, tokenizer=tokenizer, splitter=schneider, token_cap=s.embed_token_cap
    )
    schritte.append(("12c-zweiter-chunkerlauf-" + str(len(spannen2)), rss_kb()))

    m = resources.query_model()
    merke("13-modell-objekt-gebaut-lazy")

    ergebnis = m.embed_query("Wie kuendige ich meinen Vertrag zum Monatsende?")
    merke("14-erste-einbettung-gewichte-geladen")

    langer = "Sehr geehrte Damen und Herren, hiermit kuendige ich den Vertrag. " * 60
    m.embed_query(langer)
    merke("15-lange-einbettung-aktivierungen")

    # Informative, and locked: see the module docstring. The instance is built,
    # measured and dropped again; nothing in the product changes because of it.
    zweite = model.open_tokenizer(s.embed_model_dir)
    merke("16-zweite-tokenizer-instanz-informativ")

    zeilen = kopfzeilen()
    zeilen.append("tokenizers_version=" + tokenizers.__version__)
    zeilen.append("vocab_size=" + str(zweite.get_vocab_size()))
    zeilen.append(
        "chunk_tokens="
        + str(s.embed_chunk_tokens)
        + " overlap="
        + str(s.embed_chunk_overlap)
        + " token_cap="
        + str(s.embed_token_cap)
    )
    zeilen.append("embedding_available=" + str(ergebnis.available))
    zeilen.append(
        "module_seen=" + ",".join((vectors.__name__, poller.__name__, hauptmodul.__name__))
    )
    zeilen.append("")
    zeilen.append("-- schritt rss_kb --")
    zeilen.extend(name + " " + str(kb) for name, kb in schritte)
    zeilen.append("")
    zeilen.append("-- zuwachs je schritt --")
    zeilen.append("von                                    nach                                    delta_mb    rss_mb")
    for i in range(1, len(schritte)):
        delta = (schritte[i][1] - schritte[i - 1][1]) / 1024
        gesamt = schritte[i][1] / 1024
        zeilen.append(
            schritte[i - 1][0].ljust(38)
            + " "
            + schritte[i][0].ljust(38)
            + " "
            + format(delta, "9.1f")
            + " "
            + format(gesamt, "9.1f")
        )

    print("\n".join(zeilen))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
