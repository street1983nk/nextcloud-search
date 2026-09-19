#!/usr/bin/env python3
"""Der Vorprueflauf: kommt der Speicher nach einem Loslassen zurueck.

Gemessen werden vier Marken je Zyklus, gelesen als VmRSS aus
/proc/self/status nach dem Muster von index/wordlist.py::rss_bytes:

  baseline    nach den Modulimporten, vor dem ersten Laden
  loaded      nach Tokenizer, Splitter, Encoder, Sitzung und einem run
  after_gc    nach dem Loslassen aller Halter plus gc.collect()
  after_trim  nach malloc_trim(0), mit dessen Rueckgabewert

Daraus die eine Groesse, an der die Phase haengt:

  rueckgabe_prozent = (loaded - after_trim) / (loaded - baseline) * 100

Der Nenner ist loaded - baseline und nicht loaded, weil der Bodensatz der
Modulimporte von onnxruntime und numpy nicht zurueckkommen kann: die Module
bleiben geladen. Die Erwartung E1 bis E4 zu diesen Zahlen steht in
00-ablauf.md und ist VOR diesem Lauf geschrieben.

Fuenf Zyklen und nicht einer. glibc hebt M_MMAP_THRESHOLD waehrend der
Freigabe grosser Bloecke dynamisch an, und deshalb muss Zyklus 5 nicht
aussehen wie Zyklus 1: spaetere Ladungen koennen aus der Arena bedient
werden statt per mmap, und dann gibt malloc_trim weniger zurueck. Ein
einziger Zyklus waere kein Beleg fuer einen Container, der Wochen laeuft.

Das Skript oeffnet keine Netzwerkverbindung und sendet nichts. Es liest
/proc/self/status und das Modellverzeichnis des Abbilds, und es druckt
ausschliesslich Zahlen und Kopfzeilen: keinen Dateinamen, keinen Pfad einer
Maschine, keinen Suchtext und keinen Inhalt des Blindtextes (T-06-06,
T-02-14). Der Text, mit dem geschnitten und eingebettet wird, steht als
Konstante in dieser Datei.
"""

from __future__ import annotations

import argparse
import ctypes
import datetime
import gc
import os
import platform
import statistics
from pathlib import Path
from typing import Any, NamedTuple

# Derselbe Satz, mit dem 01-grundlast-fein.py schneidet, in derselben
# Wiederholung: dann liegen die Ladezahlen dieses Laufs neben denen der
# Feinmessung und nicht nur in ihrer Naehe.
BLINDTEXT = "Ein Satz zum Schneiden, damit der Schneider wirklich arbeitet. " * 60

# So viele Stuecke gehen als ein Batch durch den Graphen. Acht ist die obere
# Kante der Batchgroesse, mit der das Erzeugnis einbettet; der erste run ist
# der Posten, um den es hier geht, und er soll nicht kleiner ausfallen als im
# Betrieb.
BATCH = 8

# Fester Name, nie ein Pfad aus der Umgebung oder von der Kommandozeile
# (T-14-01). Eine Bibliothek, deren Name von aussen kommt, waere ein Weg,
# fremden Code in diesen Prozess zu laden.
LIBC = "libc.so.6"

# Was gemeldet wird, wenn diese libc kein malloc_trim hat. Kein Abbruch: das
# Ergebnis "diese Basis kann es nicht" ist selbst eine Antwort auf die Frage
# des Laufs, und ein Sturz mitten im Zyklus waere keine.
TRIM_UNAVAILABLE = -1


class Messung(NamedTuple):
    """Die vier Marken eines Zyklus plus der Rueckgabewert von malloc_trim."""

    nummer: int
    baseline_kb: int
    loaded_kb: int
    after_gc_kb: int
    after_trim_kb: int
    trim_rc: int

    @property
    def rueckgabe_prozent(self) -> float:
        geladen = self.loaded_kb - self.baseline_kb
        if geladen <= 0:
            return 0.0
        return (self.loaded_kb - self.after_trim_kb) / geladen * 100.0

    def zeile(self) -> str:
        return " ".join(
            (
                "zyklus=" + str(self.nummer),
                "baseline_kb=" + str(self.baseline_kb),
                "loaded_kb=" + str(self.loaded_kb),
                "after_gc_kb=" + str(self.after_gc_kb),
                "after_trim_kb=" + str(self.after_trim_kb),
                "trim_rc=" + str(self.trim_rc),
                "rueckgabe_prozent=" + format(self.rueckgabe_prozent, ".1f"),
            )
        )


def rss_kb() -> int:
    for zeile in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        if zeile.startswith("VmRSS:"):
            return int(zeile.split()[1])
    return -1


def umgebung(name: str) -> str:
    return os.environ.get(name, "") or "unknown"


def kopfzeilen() -> list[str]:
    """Architektur, Abbild-Digest und Datum, damit die Zahlen ihre Maschine behalten.

    Eine Messung ohne ihre Maschine ist eine Behauptung, die an der falschen
    Hardware zitiert wird (T-06-07). Der Digest ist aus einem Container heraus
    nicht lesbar, also reicht ihn der Aufrufer in einer Umgebungsvariablen
    herein; ein leerer Wert wird als unknown gedruckt und nicht weggelassen,
    weil ein fehlendes Feld leichter auffaellt als eine fehlende Zeile.
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


def _return_free_pages() -> int:
    """Ganze freie Seiten zurueckgeben, und schweigen, wo die libc das nicht kann.

    Die Reihenfolge ist nicht verhandelbar: erst die Referenzen loesen (das tut
    der Aufrufer), dann gc.collect(), dann malloc_trim(0). Ein gc.collect()
    allein gibt einen kleinen Teil zurueck, weil glibc die freigegebenen Bloecke
    in der Arena behaelt; der wirksame Schritt ist der zweite.

    Der Rueckgabewert wird durchgereicht und gedruckt: 1 heisst, dass etwas an
    das Betriebssystem ging, 0 heisst, dass nichts ging. Eine schoene
    Prozentzahl neben einem durchgehenden 0 waere kein Beleg, sondern ein
    Hinweis, dass die Rueckgabe woanders herkommt (Erwartung E2).

    Gefangen werden OSError und AttributeError, und nur die beiden: die erste
    ist die Basis ohne diese libc, die zweite die libc ohne diese Funktion.
    """
    gc.collect()
    try:
        libc = ctypes.CDLL(LIBC)
        return int(libc.malloc_trim(0))
    except (OSError, AttributeError):
        return TRIM_UNAVAILABLE


def _ein_batch(encoder: Any, session: Any, stuecke: list[str]) -> Any:
    """Ein echter Batch durch den Graphen, damit der Aktivierungsspeicher im Bild ist.

    Der erste run ist der groesste Einzelposten der ganzen Ladung, er bleibt
    danach liegen, obwohl enable_cpu_mem_arena False ist, und er verschwindet
    erst mit der Entladung. Ein Zyklus ohne run wuerde die Frage um ihren
    groessten Posten bringen.

    Vorbild ist embed/model.py::_run_encoded, ohne Pooling und ohne
    Normalisierung: hier wird kein Vektor gebraucht, nur der Speicher, den der
    Lauf belegt. Das Ergebnis wird zurueckgegeben und vom Aufrufer bis zur Marke
    loaded festgehalten.
    """
    import numpy

    kodiert = encoder.encode_batch(stuecke[:BATCH] if stuecke else [BLINDTEXT])
    ids = numpy.asarray([stueck.ids for stueck in kodiert], dtype=numpy.int64)
    maske = numpy.asarray([stueck.attention_mask for stueck in kodiert], dtype=numpy.int64)
    futter = {
        "input_ids": ids,
        "attention_mask": maske,
        "token_type_ids": numpy.zeros_like(ids),
    }
    akzeptiert = frozenset(eingang.name for eingang in session.get_inputs())
    ausgaenge = [ausgang.name for ausgang in session.get_outputs()[:1]]
    return session.run(ausgaenge, {name: wert for name, wert in futter.items() if name in akzeptiert})


def zyklus(nummer: int, model_dir: Path, s: Any) -> Messung:
    """Ein voller Lade- und Entladezyklus, vier Marken lang."""
    baseline = rss_kb()

    # Die Module liegen schon in sys.modules, main hat sie vor dem ersten
    # Zyklus importiert. Diese Namen kosten hier eine Nachschlagung und kein
    # Kilobyte, und genau deshalb ist baseline die Marke vor dem Laden und
    # nicht die Marke vor den Importen.
    import onnxruntime

    from findling.embed import chunker, model

    # Der Halter der Indexseite: der schlichte Tokenizer und der Splitter, den
    # er baut. Ein Schnitt darueber, damit der Splitterbau wirklich bezahlt ist
    # und nicht nur angelegt.
    tokenizer = model.open_tokenizer(model_dir)
    splitter = chunker.make_splitter(tokenizer, chunk_tokens=s.embed_chunk_tokens, overlap=s.embed_chunk_overlap)
    stuecke = splitter.chunks(BLINDTEXT)

    # Der Halter der Suchseite, zweite Instanz desselben tokenizer.json, mit
    # Truncation und Padding wie embed/model.py::_open_encoder es setzt. Zwei
    # Instanzen sind die verriegelte Entscheidung dieses Projekts, weil
    # enable_truncation eine Eigenschaft des Objekts ist; hier sind sie
    # zusaetzlich die Messwahrheit, denn der Container haelt im Betrieb beide.
    encoder = model.open_tokenizer(model_dir)
    encoder.enable_truncation(max_length=s.embed_sequence_len)
    marke = model.PAD_MARKER
    pad_id = encoder.token_to_id(marke)
    if pad_id is None:
        marke, pad_id = model.FALLBACK_PAD_MARKER, 0
    encoder.enable_padding(pad_id=pad_id, pad_token=marke)

    # Die Sitzung mit denselben drei Optionen wie embed/model.py::_open_session.
    # Wiederholt und nicht importiert, weil _open_session privat ist: ein
    # Messskript, das in die privaten Namen eines Moduls greift, bricht beim
    # naechsten Umbau still, und ein Messskript, das den Namen oeffentlich
    # machen laesst, aendert das Erzeugnis wegen einer Messung. Drei Zeilen
    # Wiederholung sind der kleinere Preis; sie stehen unter der Aufsicht
    # dieses Kommentars.
    optionen = onnxruntime.SessionOptions()
    optionen.intra_op_num_threads = model.THREADS
    optionen.inter_op_num_threads = 1
    optionen.enable_cpu_mem_arena = False
    session = onnxruntime.InferenceSession(
        str(model_dir / model.MODEL_FILE), optionen, providers=["CPUExecutionProvider"]
    )

    versteckt = _ein_batch(encoder, session, stuecke)
    loaded = rss_kb()

    # Loslassen, und zwar alles: die beiden Tokenizer, der Splitter, die
    # Sitzung und das Ergebnis des Laufs. Danach die erste Einsammlung, und die
    # Marke dazwischen. Sie ist der Beleg, dass malloc_trim und nicht
    # gc.collect() der wirksame Schritt ist (Erwartung E3).
    #
    # del und nicht eine Zuweisung von None: die Wirkung auf den Zaehler der
    # Referenzen ist dieselbe, aber eine Zuweisung an einen Namen, der danach
    # nie mehr gelesen wird, ist eine tote Zuweisung und wird zu Recht gemeldet.
    del tokenizer, splitter, stuecke, encoder, session, versteckt
    gc.collect()
    after_gc = rss_kb()

    trim_rc = _return_free_pages()
    after_trim = rss_kb()

    return Messung(
        nummer=nummer,
        baseline_kb=baseline,
        loaded_kb=loaded,
        after_gc_kb=after_gc,
        after_trim_kb=after_trim,
        trim_rc=trim_rc,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="RSS returned after a release, one line per cycle")
    parser.add_argument(
        "--cycles",
        type=int,
        default=5,
        help="how many load and release cycles to run, five by default",
    )
    args = parser.parse_args()
    if args.cycles < 1:
        print("cycles has to be at least 1")
        return 2

    # Alle Importe vor der ersten Marke. Was hier faellt, faellt in den
    # Bodensatz und nicht in die gemessene Ladung, und der Bodensatz ist genau
    # der Teil, der nicht zurueckkommen kann.
    import numpy  # noqa: F401  der Batch entsteht im Zyklus, bezahlt wird der Import hier
    import onnxruntime
    import tokenizers

    from findling.config import settings
    from findling.embed import chunker, model  # noqa: F401  dasselbe fuer die Bauwege

    s = settings()

    messungen = [zyklus(nummer, s.embed_model_dir, s) for nummer in range(1, args.cycles + 1)]

    zeilen = kopfzeilen()
    zeilen.append("tokenizers_version=" + tokenizers.__version__)
    zeilen.append("onnxruntime_version=" + onnxruntime.__version__)
    zeilen.append(
        " ".join(
            (
                "cycles=" + str(args.cycles),
                "batch=" + str(BATCH),
                "threads=" + str(model.THREADS),
                "sequence_len=" + str(s.embed_sequence_len),
                "chunk_tokens=" + str(s.embed_chunk_tokens),
                "overlap=" + str(s.embed_chunk_overlap),
            )
        )
    )
    zeilen.append("")
    zeilen.append("-- zyklen --")
    zeilen.extend(messung.zeile() for messung in messungen)
    zeilen.append("")

    # Die beiden Zeilen, die E1 und E4 ohne Nachrechnen ablesbar machen. Eine
    # Erwartung, fuer deren Pruefung ein Leser erst einen Taschenrechner
    # braucht, wird beim Lesen der Rohdatei geschaetzt statt geprueft.
    quoten = [messung.rueckgabe_prozent for messung in messungen]
    zeilen.append("median_rueckgabe_prozent=" + format(statistics.median(quoten), ".1f"))
    zeilen.append("zyklus1_minus_zyklus5_punkte=" + format(quoten[0] - quoten[-1], ".1f"))

    print("\n".join(zeilen))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
