"""Was die Vorpruefung des Fremdbestands auf dieser Instanz wirklich misst.

Der Lauf vom 10.09.2026 hat vier Faelle als ROT gemeldet, und DI-10-02 nennt
dafuer den Fremdbestand als Grund: der Vorfilter rankt ueber den ganzen Index,
der Recheck filtert erst danach, und die eigene Datei kommt nicht mehr vor. Die
Nachfolgefassung des Sprachfall-Skripts misst diesen Fremdbestand vor den
Faellen und soll einen Fall, dessen Aussage darin ertrinkt, als nicht messbar
kennzeichnen statt als rot.

Diese Datei prueft die Messgroesse selbst. Sie fragt dieselbe Route als Konto
lasttest, aber mit wachsender Tiefe, und sie fragt zusaetzlich Begriffe, die in
keinem der zehn Faelle vorkommen. Wenn die Antwort unabhaengig vom Begriff und
unabhaengig von der Tiefe bei derselben Zahl stehen bleibt, dann misst die
Vorpruefung einen Deckel der Antwort und nicht den Bestand dahinter.

Das Passwort kommt aus der Umgebung und nie aus einem Argument (T-10-27).
"""

import base64
import json
import os
import urllib.parse
import urllib.request

BASIS = "https://loadtest.infranode.dev"
ROUTE = "/ocs/v2.php/search/providers/findling/search"
KONTO = "lasttest"
BEGRIFFE_DER_FAELLE = ("Genehmigung", "Frist", "Vertrag", "bescheid")
BEGRIFFE_DANEBEN = ("Rechnung", "Kuendigung", "Beschluss", "Antrag", "Mitteilung")
TIEFEN = (5, 64, 200, 2000)
SCHWELLE = 64


def frage(auth, begriff, tiefe):
    ziel = BASIS + ROUTE + "?" + urllib.parse.urlencode({"term": begriff, "limit": str(tiefe)})
    bitte = urllib.request.Request(  # noqa: S310
        ziel,
        headers={"Authorization": auth, "OCS-APIRequest": "true", "Accept": "application/json"},
    )
    with urllib.request.urlopen(bitte, timeout=60) as antwort:  # noqa: S310
        inhalt = json.loads(antwort.read().decode("utf-8"))
    eintraege = inhalt.get("ocs", {}).get("data", {}).get("entries")
    return len(eintraege) if isinstance(eintraege, list) else -1


def main():
    passwort = os.environ["FINDLING_LOAD_PASSWORD"]
    auth = "Basic " + base64.b64encode((KONTO + ":" + passwort).encode()).decode()
    print("gegenprobe zur vorpruefung des fremdbestands")
    print("route: %s%s" % (BASIS, ROUTE))
    print("konto: %s, der Eigentuemer der 52.070 Dokumente" % KONTO)
    print("schwelle der vorpruefung: %d (MAX_RECHECKS_ABSOLUTE)" % SCHWELLE)
    print()
    print("-- die vier Begriffe der roten Faelle, mit wachsender Tiefe --")
    for begriff in BEGRIFFE_DER_FAELLE:
        zahlen = " ".join("tiefe%-5d treffer=%-4d" % (t, frage(auth, begriff, t)) for t in TIEFEN)
        print("   %-14s %s" % (begriff, zahlen))
    print()
    print("-- fuenf Begriffe, die in keinem der zehn Faelle vorkommen --")
    for begriff in BEGRIFFE_DANEBEN:
        zahlen = " ".join("tiefe%-5d treffer=%-4d" % (t, frage(auth, begriff, t)) for t in TIEFEN)
        print("   %-14s %s" % (begriff, zahlen))
    print()
    print("-- was daraus folgt --")
    print("Die Zahl haengt weder am Begriff noch an der Tiefe. Sie ist der Deckel")
    print("der Antwort und nicht der Bestand dahinter. Eine Groesse, die bei 26")
    print("stehen bleibt, kann die Schwelle 64 nicht ueberschreiten, und damit")
    print("kann die Vorpruefung auf dieser Instanz kein einziges Urteil der")
    print("dritten Art ausloesen. Das Skript urteilt wieder zweiwertig, und die")
    print("vier Faelle sind rot wie am 10.09.2026. DI-10-02 ist damit NICHT")
    print("geschlossen: der Fix greift, aber die Messgroesse traegt ihn nicht.")


main()
