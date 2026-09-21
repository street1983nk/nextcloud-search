---
phase: 16-haertung-und-store-einreichung-v1-2-0
angelegt: 2026-09-21
staemme: 3
---

# Flake-Register der Phase 16

**Der Merker, um den es geht: die erste Handlung bei einem roten Ast ist die
Wiederholung und nicht die Fehlersuche. Erst wenn sie Zeile für Zeile dasselbe
liefert, ist es ein Befund.**

Dieses Register wird vom Plan der Abgabe gelesen. Am Ende dieser Phase müssen
sieben Tag-Läufe gleichzeitig grün sein, und die drei Stämme unten sind die
bekannten Gründe, aus denen das ohne jeden Defekt am Erzeugnis scheitern kann.
Sie stehen deshalb hier an einer Stelle und werden im ersten Block der Phase
behandelt, nicht in der Abgabewoche.

Die Überschriften stehen ohne Umlaute, weil Prüfungen und Verweise auf sie
zeigen können; der Fließtext benutzt echte Umlaute. Dieses Dokument nennt
Laufnummern und Schrittnamen und sonst nichts: keine Kennung, keine Adresse,
keinen Passwortinhalt.

## Die drei Staemme

| Kennung | Auftrag und Schritt | Letzter roter Lauf | Gegenprobe | Verdikt | Fix beziehungsweise Merker |
|---|---|---|---|---|---|
| `mutation-423` | `index-search-e2e (pgsql)`, Schritt "Overwrite it eight times while the container is working" | 34555358815 vom 11.09.2026, `curl: (22) The requested URL returned error: 423` nach "revision 8 written" | Wiederholung des fehlgeschlagenen Auftrags am selben Tag grün; ein roter Lauf auf dreizehn in der Geschichte des Auftrags | Fix in dieser Phase | Task 1 des Plans 16-01 (DI-11-05): `write_revision` mit enger Wiederholung, nur auf 423, höchstens dreimal, jeder andere Code scheitert sofort |
| `single-flight-zeit` | volle Suite, Fall `test_with_the_release_on_a_cold_engine_gets_exactly_one_run` | 21.09.2026 im Gate-Protokoll der Phase 15, `assert False is True`, unter Nebenlast auf derselben Maschine | einzeln nachgefahren grün, und der Lauf ohne Nebenlast ebenfalls grün | Fix in dieser Phase | Task 2 des Plans 16-01 (L-11): `ARRIVAL_SECONDS = 30.0` für die Warte-auf-Ankunft-Fälle, `BLOCKED_WARM_SECONDS = 5.0` bleibt an den Obergrenzen |
| `parity-login` | `search-parity (stable34, 8.2)`, Schritt "Log every account in and keep its session" | 35470079862 vom 19.09.2026, die Anmeldung des Kontos `minimal` wurde verweigert | beidseitig eingerahmt: 35469147833 davor grün, 35471225104 danach grün, und dazwischen liegen nur Mess-Skripte, deren Tests und Doku | beobachtet, kein Fix in dieser Phase | erst wiederholen, dann suchen. Wer den Punkt aufnimmt, liest den älteren Befund `parity-login-probe-404` vom 11.09.2026 daneben, bevor er einen von beiden für sporadisch erklärt |

## Was die drei unterscheidet

Die ersten beiden sind behoben, weil ihre Ursache benannt und eng einzufassen
war: eine Sperre, die auf sich warten lässt, und eine Frist, die zwei Fragen
zugleich beantworten sollte. Beide Fixe machen kein Gate weicher. Die
423-Wiederholung gilt ausschließlich für 423, mit einer Obergrenze von drei
und mit der Zahl der Sperrtreffer im Protokoll, damit ein Lauf hinterher sagen
kann, ob die Sperre überhaupt auftrat; null ist die erwartete Zahl. Die zweite
Frist steht nur dort, wo sie gratis ist, nämlich an der Frage, ob ein
Hintergrundlauf stattgefunden hat. Wo ein Fall eine Obergrenze behauptet, bleibt
die kurze Frist stehen, denn dort ist sie die Aussage selbst.

Der dritte Stamm ist bewusst nicht gefixt. Es gibt zwei Fehlschläge desselben
Schritts an zwei verschiedenen Ästen derselben Funktion, und die Deutung ist
offen: der ältere antwortete mit 404 auf der Ergebnisseite, der jüngere
verweigerte die Anmeldung selbst. Ein Fix ohne diese Deutung wäre eine
Vermutung im Erzeugnis, und eine Änderung an der Paritätsstrecke unmittelbar
vor einem Release-Tag ersetzt ein seltenes Flattern durch ein neues Risiko.
Geht der Auftrag in der Abgabewoche rot, gilt der Merker der Kopfzeile.
