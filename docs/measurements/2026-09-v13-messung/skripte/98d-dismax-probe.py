#!/usr/bin/env python3
"""The disjunction_max probe of the v1.3 trip, MESS-09, measured inside the container.

**DIESE FASSUNG IST NICHT GEFAHREN.** No raw file lies next to it; what it
measures on the box is measured on the trip, after the rebuild to six filled
body fields.

**The question.** tantivy sums the contribution of every field a document
matches in. With six body fields filled from the same text, a word every chain
leaves alone collects six contributions while a word only three chains put on
the term of the question collects three; ``field_boosts`` damps that sum and
does not remove it (test_field_plan_ranking.py, tipping point 0.81 on its
probe). ``Query.disjunction_max_query`` takes the best field instead of the
sum. Whether that is better on real data is what this file measures, and only
that: the rule that turns these numbers into a decision is not in this file. It
stands in 00-ablauf.md and is fixed at the owner checkpoint BEFORE the box
starts (D-04), so that no number of this run can choose its own rule.

**The shape that is measured.** Per word of the cleaned line and per field of
the plan ``parse_query_lenient(word, default_field_names=[field],
field_boosts={field: boost}, conjunction_by_default=True,
allow_regexes=False)``, a ``disjunction_max_query`` over the fields, and
``Occur.Must`` over the words. Measured in 22-RESEARCH: this keeps the hit set
of the sum exactly and changes only the ranks. The whole line dismax (one parse
per field of the whole line) loses every document that carries word A in one
field and word B in another; it is kept below as ``line_dismax`` because the
unit test proves that it loses one, and it is never one of the forms measured.

**The four forms per question**, each a ranking of the lexical half down to
SEARCH_RRF_WINDOW:

  summe       the plan that ships, through build_query: the sum
  dismax_t00  per word dismax, tie breaker 0.0
  dismax_t01  per word dismax, tie breaker 0.1
  altplan     LEGACY_PLAN through build_query: the behaviour up to 1.2.0,
              body_de, body_en, name and title, the yardstick of success
              criterion 3

**Rule: there is no second way to the rankings.** The index comes from
``read_side``, which opens it through ``open_index`` and so registers the eight
chains; a bare ``Index(...)`` would raise "Error getting tokenizer". The plan
comes from ``field_plan_for`` over the marks of the directory, the sum and the
old plan from ``build_query``. Only the per word dismax is built here, and it
is built out of the same parser calls.

**What falls back.** A line with operators, a phrase, brackets, a file type or
an umlaut variant ("(a OR b)") does not fall apart into words; the product
would answer it the way it does today. Such a line is counted as ``rueckfall``
and measured with the sum alone. A one word line is ``einwort``: its per word
dismax is one dismax over the fields of its rewritten form, variant included.

**The questions.** The ten TERMS of scripts/ops/search_load.py, the ten terms of
the language cases of 98c-sprachfaelle.sh, and a fixed sample drawn with a seed
out of WORDS of scripts/dev/build_load_corpus.py. That file is copied into the
container next to this one (WORTLISTE); the sample is printed as numbers only.

**What is printed**, and nothing else, because the raw data of a trip go into a
public repository (T-22-10, T-02-14): numbers, classes, form names and file ids.
The text of a question never leaves this tool.

  kennzahl anfragen <quelle> <n>
  anfrage <nr> klasse <einwort|mehrwort|rueckfall|leer>
  anfrage <nr> treffer <form> <n>
  anfrage <nr> spitze <form> <id,id,...|keine>
  anfrage <nr> <overlap10|rbo10|rangverschiebung>_gegen_altplan <form> <wert>
  anfrage <nr> latenz_ms <form> <median>
  treffermenge-ungleich anfrage <nr> <form>
  kennzahl <name>[_<klasse>] <form> <median>

Return codes: 0 measured, 2 no readable index or no word list, 49 the hit set
of the sum and of a per word dismax differ for at least one question, which
means the probe is wrong and none of its ranks may be read.

Call inside the product container:

  docker cp 98d-dismax-probe.py <container>:/tmp/98d-dismax-probe.py
  docker cp build_load_corpus.py <container>:/tmp/build_load_corpus.py
  docker exec <container> /app/.venv/bin/python /tmp/98d-dismax-probe.py

Neither ruff nor pyright run under docs/measurements/**/skripte/; this file
follows the ruff style anyway, and backend/tests/test_dismax_probe.py holds its
arithmetic.
"""

import ast
import os
import random
import statistics
import sys
import time
from pathlib import Path

from tantivy import Occur, Query

from findling.api.resources import field_plan_for, read_side
from findling.config import SEARCH_RRF_WINDOW
from findling.index.analyzer import normalize
from findling.index.schema import FIELD_FILE_ID
from findling.query.rewrite import (
    LEGACY_PLAN,
    add_umlaut_variants,
    build_query,
    carried_operators,
    extract_filters,
)

# scripts/ops/search_load.py, TERMS, in its order. Repeated rather than
# imported: scripts/ is not in the image.
TERMS = (
    "Vertrag beenden",
    "Kuendigung",
    "Widerspruch einlegen",
    "Bescheid",
    "Rechnung bezahlen",
    "Mahnung",
    "Termin absagen",
    "Mitteilung",
    "Antrag stellen",
    "Beschluss",
)

# The ten terms of the language cases, in the order of the cases 1 to 10 of
# docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh (the same
# list 73-bestand-sonde.py carries). The quotation marks of the phrase case are
# part of the line.
SPRACHFAELLE = (
    "Genehmigung",
    "Frist",
    "Mueller",
    "Vertrag",
    '"drei Monate"',
    "bescheid",
    "type:pdf bescheid",
    "Belehrung",
    "Auszug",
    "Erinnerung",
)

WORTLISTE = os.environ.get("WORTLISTE", "/tmp/build_load_corpus.py")  # noqa: S108 - a path inside the container
STICHPROBE_SEED = int(os.environ.get("STICHPROBE_SEED", "22"))
STICHPROBE_EINWORT = int(os.environ.get("STICHPROBE_EINWORT", "20"))
STICHPROBE_ZWEIWORT = int(os.environ.get("STICHPROBE_ZWEIWORT", "20"))
WIEDERHOLUNGEN = int(os.environ.get("WIEDERHOLUNGEN", "5"))

TIEFE = SEARCH_RRF_WINDOW
SPITZE = 10
RBO_P = 0.9

SUMME = "summe"
ALTPLAN = "altplan"
TIES = {"dismax_t00": 0.0, "dismax_t01": 0.1}
FORMEN = (SUMME, *TIES, ALTPLAN)

EINWORT = "einwort"
MEHRWORT = "mehrwort"
RUECKFALL = "rueckfall"
LEER = "leer"

KEIN_INDEX = 2
TREFFERMENGE_UNGLEICH = 49


def klasse_von(text):
    """The class of a line and the words its per word dismax is built from."""
    if carried_operators(text) or "(" in text or ")" in text:
        return RUECKFALL, ()
    residual, extensions = extract_filters(normalize(text))
    if extensions:
        return RUECKFALL, ()
    words = residual.split()
    if not words:
        return LEER, ()
    if len(words) == 1:
        return EINWORT, (add_umlaut_variants(words[0]).strip(),)
    if add_umlaut_variants(residual).strip() != residual.strip():
        return RUECKFALL, ()
    return MEHRWORT, tuple(words)


def word_dismax(index, word, plan, tie):
    """One word over every field of the plan, the best field instead of the sum."""
    subqueries = [
        index.parse_query_lenient(
            word,
            default_field_names=[field],
            field_boosts={field: plan.boosts[field]},
            conjunction_by_default=True,
            allow_regexes=False,
        )[0]
        for field in plan.fields
    ]
    return Query.disjunction_max_query(subqueries, tie)


def dismax_query(index, words, plan, tie):
    """Every word required, each one answered by its best field."""
    clauses = [word_dismax(index, word, plan, tie) for word in words]
    if len(clauses) == 1:
        return clauses[0]
    return Query.boolean_query([(Occur.Must, clause) for clause in clauses])


def line_dismax(index, text, plan, tie):
    """The rejected shape: the whole line per field, then dismax. It loses hits."""
    subqueries = [
        index.parse_query_lenient(
            text,
            default_field_names=[field],
            field_boosts={field: plan.boosts[field]},
            conjunction_by_default=True,
            allow_regexes=False,
        )[0]
        for field in plan.fields
    ]
    return Query.disjunction_max_query(subqueries, tie)


def ranking(index, query, depth=TIEFE):
    """The file ids of the lexical half, in the order the searcher returns them."""
    searcher = index.searcher()
    found = []
    for _, address in searcher.search(query, depth).hits:
        value = searcher.doc(address).get_first(FIELD_FILE_ID)
        if value is not None:
            found.append(int(value))
    return found


def hit_count(index, query):
    """How many documents a query matches, uncapped."""
    return index.searcher().search(query, 1, count=True).count


def same_hits(index, left, right):
    """Whether two queries match exactly the same documents.

    Asked as two counts of a difference rather than by comparing two lists: a
    word of the snapshot matches thousands of documents, and nought documents
    in "left and not right" and in "right and not left" is equality without
    fetching one of them.
    """
    only_left = Query.boolean_query([(Occur.Must, left), (Occur.MustNot, right)])
    only_right = Query.boolean_query([(Occur.Must, right), (Occur.MustNot, left)])
    return hit_count(index, only_left) == 0 and hit_count(index, only_right) == 0


def _depth(a, b, k):
    return min(k, max(len(a), len(b)))


def overlap_at(a, b, k):
    """The share of the first k ids both lists carry. Two empty lists agree."""
    depth = _depth(a, b, k)
    if depth == 0:
        return 1.0
    return len(set(a[:depth]) & set(b[:depth])) / depth


def rbo_at(a, b, k, p=RBO_P):
    """Rank biased overlap down to k, normalised so that identical lists give 1.0.

    The truncated sum of Webber et al. over the agreement at each depth d,
    weighted with p to the power d - 1 and divided by the sum of the weights.
    The depth stops at the longer of the two lists, so that two identical lists
    shorter than k are identical and not penalised for being short.
    """
    depth = _depth(a, b, k)
    if depth == 0:
        return 1.0
    weighted = 0.0
    weights = 0.0
    for d in range(1, depth + 1):
        weight = p ** (d - 1)
        weighted += weight * len(set(a[:d]) & set(b[:d])) / d
        weights += weight
    return weighted / weights


def mean_rank_shift(a, b):
    """The mean distance in ranks of the ids both lists carry, None without one."""
    position = {value: rank for rank, value in enumerate(b)}
    shifts = [abs(rank - position[value]) for rank, value in enumerate(a) if value in position]
    if not shifts:
        return None
    return sum(shifts) / len(shifts)


def median_ms(action, repetitions):
    """The median wall time of an action in milliseconds, and its last result."""
    times = []
    result = None
    for _ in range(max(1, repetitions)):
        start = time.perf_counter()
        result = action()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.median(times), result


def wert(value):
    return "unbestimmt" if value is None else f"{value:.4f}"


def ids(values):
    return ",".join(str(value) for value in values) or "keine"


def _form_queries(index, text, plan, klasse, words):
    """The query builders of every form this class is measured in."""
    forms = {SUMME: lambda: build_query(index, text, plan=plan).query}
    if klasse in (EINWORT, MEHRWORT):
        for name, tie in TIES.items():
            forms[name] = lambda tie=tie: dismax_query(index, words, plan, tie)
        forms[ALTPLAN] = lambda: build_query(index, text, plan=LEGACY_PLAN).query
    return forms


def measure(index, plan, questions, repetitions=WIEDERHOLUNGEN):
    """Every question in every form, printed; the return code of the probe."""
    unequal = 0
    collected = {}
    for number, text in enumerate(questions, start=1):
        klasse, words = klasse_von(text)
        print(f"anfrage {number} klasse {klasse}")
        if klasse == LEER:
            continue
        rankings = {}
        queries = {}
        for form, build in _form_queries(index, text, plan, klasse, words).items():
            latency, (query, order) = median_ms(lambda build=build: _built_and_ranked(index, build), repetitions)
            if query is None:
                continue
            queries[form] = query
            rankings[form] = order
            print(f"anfrage {number} treffer {form} {hit_count(index, query)}")
            print(f"anfrage {number} spitze {form} {ids(order[:SPITZE])}")
            print(f"anfrage {number} latenz_ms {form} {wert(latency)}")
            collected.setdefault(("latenz_ms", form, klasse), []).append(latency)
        if klasse == RUECKFALL or SUMME not in queries:
            continue
        for form in TIES:
            if form in queries and not same_hits(index, queries[SUMME], queries[form]):
                print(f"treffermenge-ungleich anfrage {number} {form}")
                unequal += 1
        if ALTPLAN not in rankings:
            continue
        old = rankings[ALTPLAN]
        for form in (SUMME, *TIES):
            if form not in rankings:
                continue
            new = rankings[form]
            figures = {
                "overlap10_gegen_altplan": overlap_at(new, old, SPITZE),
                "rbo10_gegen_altplan": rbo_at(new, old, SPITZE),
                "rangverschiebung_gegen_altplan": mean_rank_shift(new, old),
            }
            for name, value in figures.items():
                print(f"anfrage {number} {name} {form} {wert(value)}")
                if value is not None:
                    collected.setdefault((name, form, klasse), []).append(value)
    if unequal:
        print(f"treffermenge-ungleich anfragen {unequal}")
        return TREFFERMENGE_UNGLEICH
    _print_medians(collected)
    return 0


def _built_and_ranked(index, build):
    query = build()
    if query is None:
        return None, []
    return query, ranking(index, query)


def _print_medians(collected):
    """The medians per figure and form, over both classes and per class."""
    names = sorted({name for name, _, _ in collected})
    for name in names:
        for form in FORMEN:
            everything = [
                value
                for (other, other_form, klasse), values in collected.items()
                if other == name and other_form == form and klasse != RUECKFALL
                for value in values
            ]
            if everything:
                print(f"kennzahl {name} {form} {wert(statistics.median(everything))}")
            for klasse in (EINWORT, MEHRWORT, RUECKFALL):
                values = collected.get((name, form, klasse))
                if values:
                    print(f"kennzahl {name}_{klasse} {form} {wert(statistics.median(values))}")


def read_wordlist(path):
    """WORDS of build_load_corpus.py, read as a literal and never imported."""
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return ()
    for node in tree.body:
        target = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target.id
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target = node.targets[0].id
        if target == "WORDS" and node.value is not None:
            try:
                value = ast.literal_eval(node.value)
            except ValueError:
                return ()
            return tuple(word for word in value if isinstance(word, str))
    return ()


def stichprobe(words, seed, single, double):
    """A fixed sample: single words and pairs, drawn with one seed."""
    if not words:
        return ()
    rng = random.Random(seed)  # noqa: S311 - a reproducible sample, no secret
    lines = [rng.choice(words) for _ in range(single)]
    lines += [f"{rng.choice(words)} {rng.choice(words)}" for _ in range(double)]
    return tuple(lines)


def main():
    side = read_side()
    if side is None:
        print("abbruch kein-index")
        return KEIN_INDEX
    plan = field_plan_for(side.store.read_meta(), side.index)
    words = read_wordlist(WORTLISTE)
    if not words:
        print("abbruch keine-wortliste")
        return KEIN_INDEX
    sample = stichprobe(words, STICHPROBE_SEED, STICHPROBE_EINWORT, STICHPROBE_ZWEIWORT)
    print(f"kennzahl anfragen terms {len(TERMS)}")
    print(f"kennzahl anfragen sprachfaelle {len(SPRACHFAELLE)}")
    print(f"kennzahl anfragen stichprobe {len(sample)}")
    print(f"kennzahl plan felder {len(plan.fields)}")
    print(f"kennzahl probe tiefe {TIEFE}")
    print(f"kennzahl probe wiederholungen {WIEDERHOLUNGEN}")
    return measure(side.index, plan, TERMS + SPRACHFAELLE + sample)


if __name__ == "__main__":
    sys.exit(main())
