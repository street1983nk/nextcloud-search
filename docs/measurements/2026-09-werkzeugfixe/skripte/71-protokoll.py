"""Die Abbrueche im Nextcloud-Protokoll im Zeitfenster des Lastlaufs, gezaehlt.

Zweite, vom Lastwerkzeug unabhaengige Zaehlung derselben Sache (DI-10-01). Sie
liest das Protokoll der Nextcloud und nicht die Antworten, die das Werkzeug
gesehen hat.

Eine Falle steckt in der Zaehlung selbst, und sie wird hier ausgewiesen statt
umgangen: EIN abgebrochener Aufruf hinterlaesst ZWEI Zeilen, eine von app_api
mit dem cURL-Text und eine von findling, die ihn als exception weiterreicht.
Wer Zeilen zaehlt, zaehlt doppelt. Gezaehlt wird deshalb nach reqId, also nach
Vorgang, und beide Zeilenzahlen stehen zur Kontrolle daneben.

Nutzerinhalte bleiben draussen (T-10-41): aus jeder Zeile stehen nur Zeit,
Stufe, App, reqId und der Teil der Meldung, an dem die Aussage haengt.
"""

import json
import sys

FENSTER = [
    ("stufe16", "2026-09-10T23:35:10Z", "2026-09-10T23:36:06Z"),
    ("stufe08", "2026-09-10T23:36:23Z", "2026-09-10T23:36:51Z"),
]
MUSTER = "cURL error 28"


def zeit(eintrag):
    # Das Protokoll schreibt 2026-09-10T23:35:17+00:00, die Fenster tragen Z.
    return str(eintrag.get("time", "")).replace("+00:00", "Z")


def ausschnitt(eintrag):
    meldung = eintrag.get("message")
    if isinstance(meldung, dict):
        meldung = json.dumps(meldung, ensure_ascii=False)
    roh = str(meldung) if MUSTER in str(meldung) else json.dumps(
        eintrag.get("exception", ""), ensure_ascii=False
    )
    stelle = roh.find(MUSTER)
    if stelle < 0:
        return roh[:150]
    return roh[max(0, stelle - 55):stelle + 95].replace("\n", " ")


def main():
    zeilen = [json.loads(z) for z in sys.stdin if z.strip().startswith("{")]
    print("zaehlung der abbrueche im nextcloud-protokoll")
    print("muster: %s" % MUSTER)
    print("protokoll: /var/www/html/data/nextcloud.log")
    print("gezaehlt wird nach reqId, also nach Vorgang, nicht nach Zeile")
    print()
    for name, beginn, ende in FENSTER:
        treffer = [
            e for e in zeilen
            if beginn <= zeit(e) <= ende and MUSTER in json.dumps(e, ensure_ascii=False)
        ]
        je_app = {}
        for e in treffer:
            je_app[e.get("app")] = je_app.get(e.get("app"), 0) + 1
        vorgaenge = {e.get("reqId") for e in treffer}
        print("=== fenster %s ===" % name)
        print("beginn %s" % beginn)
        print("ende   %s" % ende)
        print("curl-error-28-vorgaenge %d" % len(vorgaenge))
        print("curl-error-28-zeilen %d" % len(treffer))
        for app in sorted(je_app, key=str):
            print("  davon zeilen app=%s %d" % (app, je_app[app]))
        print("-- die Vorgaenge, je einer mit seiner ersten Zeile --")
        gesehen = set()
        for e in treffer:
            if e.get("reqId") in gesehen:
                continue
            gesehen.add(e.get("reqId"))
            print("  %s reqId=%s app=%s" % (zeit(e), e.get("reqId"), e.get("app")))
            print("    %s" % ausschnitt(e))
        print()


main()
