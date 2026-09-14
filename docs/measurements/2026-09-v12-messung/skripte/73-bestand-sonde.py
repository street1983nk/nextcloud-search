#!/usr/bin/env python3
"""Der ungedeckelte Bestand des Index je Begriff, im Prozess des Containers gemessen.

**Der Befund, der diese Datei nötig macht.** Die Vorprüfung des Fremdbestands
fragt heute die OCS-Route. Die Gegenprobe 72-fremdbestand.py vom 10.09.2026 hat
dieselbe Route mit vier Tiefen und mit Begriffen gefragt, die in keinem der zehn
Fälle vorkommen, und für jeden Begriff und jede Tiefe dieselbe Zahl 26 gemessen.
Diese Zahl ist ein Deckel der Antwort und nicht der Bestand dahinter. Sie kann
die Schwelle 64 nie erreichen, das dreiwertige Urteil fällt damit auf zweiwertig
zurück und die vier Fälle bleiben rot (DI-10-02 und DI-11-01).

**Was diese Datei misst.** Je Begriff drei Zahlen und zwei Ränge: den Bestand des
Index, also die Zahl der Dokumente, die den Begriff tragen, die Belegung der
beiden Ranglisten, aus denen die Fusion das Ergebnis baut, und, wenn eine eigene
Datei-Kennung übergeben wurde, den Rang dieser Datei in jeder der beiden Listen.

**Regel eins: die Zählung bleibt im Container.** Keine Route, kein Draht, kein
Passwort und keine Zahl über eine Prozessgrenze. Eine Trefferzahl, die diese
Grenze überquert, ist das Zähl-Orakel aus T-02-93; eine Zahl, die sie nie
überquert, ist keines. Deshalb läuft diese Datei im Container und nicht dagegen.

**Regel zwei: es gibt keinen zweiten Weg zu den beiden Ranglisten.** Gefragt wird
ranked_sides, also dieselbe Funktion, über die eine Suche dieses Containers ihre
beiden Hälften baut. Ein Nachbau würde eine Suche beantworten, die dieser
Container nie gefahren hat, und der Unterschied wäre eine Marke, die meistens
stimmt.

Die eigenen Datei-Kennungen kommen aus der Umgebungsvariable DATEI_IDS und nie
aus einem Argument. Fehlt sie, misst die Sonde nur Bestand und Fensterbelegung;
das ist der Vorlauf vor dem Hochladen der eigenen Dateien.
"""

import os
import sys

from findling.api.resources import query_model, read_side
from findling.config import settings
from findling.index.search import SemanticSide, ranked_sides
from findling.query.rewrite import build_query

# Die zehn Begriffe der Sprachfaelle, in der Reihenfolge der Faelle 1 bis 10 von
# docs/measurements/2026-09-werkzeugfixe/skripte/98b-sprachfaelle.sh. Die
# Anfuehrungszeichen des Phrasenfalls sind Teil der Suchzeile und kein Zitat.
BEGRIFFE = (
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

# MAX_RECHECKS_ABSOLUTE aus php/lib/Search/Provider.php:90. So viele Treffer
# nimmt der Recheck der PHP-Seite hoechstens noch einmal in die Hand.
SCHWELLE = 64

# SEARCH_RRF_WINDOW aus backend/src/findling/config.py:547. ranked_sides
# schneidet beide Listen auf dieses Fenster, die beiden Fensterzahlen saettigen
# also hier und sind oberhalb davon keine Aussage mehr.
FENSTER_DECKEL = 100

KEINE_SEITE = "keine-lesbare-seite"
KEINE_ZEILE = "keine-suchbare-zeile"
OHNE_KENNUNG = "keine-kennung"
AUSSERHALB = "ausserhalb"


def kennungen():
    """Die eigenen Datei-Kennungen aus der Umgebung, nie aus einem Argument.

    Form: DATEI_IDS='Genehmigung=1234,Frist=5678'. Ein Paar ohne Zahl wird
    stillschweigend verworfen, denn der Vorlauf ohne eigene Dateien ist ein
    gueltiger Lauf und kein Fehler.
    """
    gefunden = {}
    for paar in os.environ.get("DATEI_IDS", "").split(","):
        stueck = paar.strip()
        if "=" not in stueck:
            continue
        name, _, wert = stueck.partition("=")
        name = name.strip()
        wert = wert.strip()
        if name and wert.isdigit():
            gefunden[name] = int(wert)
    return gefunden


def rang(liste, datei_id):
    """Die 1-basierte Position der eigenen Datei in einer Rangliste."""
    if datei_id is None:
        return OHNE_KENNUNG
    if datei_id not in liste:
        return AUSSERHALB
    return str(liste.index(datei_id) + 1)


def messe(text, datei_id):
    """Bestand, Fensterbelegung und beide Raenge fuer einen Begriff."""
    side = read_side()
    if side is None:
        return KEINE_SEITE
    rewritten = build_query(side.index, text, title_only=False)
    if rewritten.query is None:
        return KEINE_ZEILE
    # Die ungedeckelte Zahl. count ist im Typstub der installierten tantivy
    # 0.26.0 NICHT deklariert, zur Laufzeit aber vorhanden: am 14.09.2026 gegen
    # backend/.venv gemessen, 300 Dokumente indexiert, limit 10, count liefert
    # 300. Unter docs/measurements/**/skripte/ laeuft weder ruff noch pyright,
    # der fehlende Stub ist hier also folgenlos.
    bestand = side.index.searcher().search(rewritten.query, 1, count=True).count
    semantic = None
    if side.vectors is not None and settings().embed_enabled:
        semantic = SemanticSide(vectors=side.vectors, model=query_model(), text=text)
    sides = ranked_sides(side.index, rewritten.query, semantic=semantic)
    return (
        bestand,
        len(sides.lexical),
        len(sides.semantic),
        rang(sides.lexical, datei_id),
        rang(sides.semantic, datei_id),
    )


def zeile(text, ergebnis):
    """Eine Zeile je Begriff, ausgerichtet und mit grep herausziehbar."""
    feld = "'" + text + "'"
    if isinstance(ergebnis, str):
        return "bestand begriff=%-22s %s" % (feld, ergebnis)
    return "bestand begriff=%-22s index=%-7d fenster_lex=%-5d fenster_sem=%-5d rang_lex=%-13s rang_sem=%s" % (
        (feld,) + ergebnis
    )


def main():
    ids = kennungen()
    print("bestandssonde, im prozess des containers gemessen")
    print("schwelle der messbarkeit: %d (MAX_RECHECKS_ABSOLUTE)" % SCHWELLE)
    print("deckel beider ranglisten: %d (SEARCH_RRF_WINDOW)" % FENSTER_DECKEL)
    print("eigene datei-kennungen uebergeben: %d von %d" % (len(ids), len(BEGRIFFE)))
    print()
    for begriff in BEGRIFFE:
        ergebnis = messe(begriff, ids.get(begriff))
        print(zeile(begriff, ergebnis))
        if ergebnis == KEINE_SEITE:
            print("abbruch: dieser container hat keinen lesbaren index, es ist nichts gemessen")
            return 2
    print()
    print("-- was daraus folgt --")
    print("Ein Fall ist NICHT MESSBAR, wenn die eigene Datei in BEIDEN Listen")
    print("fehlt oder in beiden Listen einen Rang groesser als %d hat." % SCHWELLE)
    print("Die Begruendung liegt in der Fusion: RRF ordnet nach der Summe der")
    print("Kehrwerte der Raenge, und jedes Dokument, das in BEIDEN Listen vor")
    print("der eigenen Datei liegt, liegt mit beiden Summanden vor ihr und")
    print("damit auch in der fusionierten Liste. Ein Rang schlechter als %d in" % SCHWELLE)
    print("beiden Listen kann deshalb durch keine Fusion in die Reichweite der")
    print("%d Rechecks kommen, und ein Fall, dessen Aussage darin ertrinkt, ist" % SCHWELLE)
    print("nicht rot, sondern nicht messbar.")
    print("bestand und fensterbelegung stehen als erklaerende Zahlen daneben:")
    print("die erste sagt, wie viele Dokumente des Index den Begriff tragen,")
    print("die beiden anderen, wie voll das Fenster ist, das der Recheck")
    print("abschreitet. Keine der drei ist das Urteil. Die Frage von DI-10-02")
    print("beantwortet allein der Rang.")
    return 0


sys.exit(main())
