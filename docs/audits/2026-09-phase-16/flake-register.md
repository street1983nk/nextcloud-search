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
| `single-flight-zeit` | volle Suite, Fall `test_with_the_release_on_a_cold_engine_gets_exactly_one_run` | **35597353833 vom 21.09.2026, 12:07Z**, `assert False is True`, und drei weitere am selben Tag (35586354661, 35594647359, 35596116820), alle vier MIT der Frist aus 16-01 | vier rote Läufe auf acht abgeschlossene seit dem Fix, also keine Wiederholung nötig: der Lauf hat sich selbst dreimal wiederholt | **erster Fix hat nicht getragen, zweiter Fix in dieser Phase** | Plan 16-13, Befund M-16-01: der Fall wird auf der Schleife des Falls gefahren statt durch den Testclient, und die Aufgabe wird abgewartet statt ein Ereignis. Die Frist aus 16-01 bleibt, sie war nie die Ursache |
| `parity-login` | `search-parity (stable34, 8.2)`, Schritt "Log every account in and keep its session" | 35470079862 vom 19.09.2026, die Anmeldung des Kontos `minimal` wurde verweigert | beidseitig eingerahmt: 35469147833 davor grün, 35471225104 danach grün, und dazwischen liegen nur Mess-Skripte, deren Tests und Doku | beobachtet, kein Fix in dieser Phase | erst wiederholen, dann suchen. Wer den Punkt aufnimmt, liest den älteren Befund `parity-login-probe-404` vom 11.09.2026 daneben, bevor er einen von beiden für sporadisch erklärt |

## Nachtrag vom 21.09.2026: der zweite Stamm ist zweimal behandelt worden

**Der erste Fix hat nicht getragen, und das steht hier, weil ein Register, das
nur die erfolgreichen Fixe führt, die Frage beantwortet, die niemand stellt.**

Plan 16-01 hat den Stamm als Lastempfindlichkeit gedeutet und ihm eine lange
Frist gegeben: eine Ankunftsfrage darf dreißig Sekunden warten. Danach ist der
Fall in CI **viermal** rot gegangen, am 21.09.2026 zwischen 10:00Z und 12:07Z,
dreimal auf einem Push und einmal auf dem Zeitplan. Vier rote von acht
abgeschlossenen Läufen dieses Auftrags seit dem Fix: das ist kein Flattern mehr,
sondern ein Befund, und die Wiederholung, die der Merker verlangt, hat der
Auftrag selbst geliefert.

Die Deutung des ersten Fixes war falsch, und die roten Läufe beweisen es: ein
Lauf, der mit dreißig Sekunden Geduld scheitert, scheitert nicht an der Geduld.
Die Ursache steht in Plan 16-13 (M-16-01): der Testclient öffnet je Anfrage ein
eigenes Tor und schließt es wieder, und die Aufgabe, die der Handler mit
`create_task` bestellt, ist eine lose Aufgabe auf dieser Schleife. Ob sie ihren
ersten Zeitschlitz bekommt, bevor das Tor zugeht, ist ein Wettlauf. Der zweite
Fix nimmt den Wettlauf heraus, statt länger auf sein Ergebnis zu warten.

**Die Frist aus 16-01 bleibt trotzdem stehen.** Sie war nie die Ursache, aber
die Trennung der zwei Fragen (Ankunft gegen Obergrenze) ist unabhängig davon
richtig, und zwei weitere Stellen benutzen sie.

## Was die drei unterscheidet

Die ersten beiden sind behoben, weil ihre Ursache benannt und eng einzufassen
war: eine Sperre, die auf sich warten lässt, und ein Wettlauf zwischen einer
bestellten Aufgabe und dem Tor, das sich hinter ihr schließt. Beide Fixe machen
kein Gate weicher. Die 423-Wiederholung gilt ausschließlich für 423, mit einer
Obergrenze von drei und mit der Zahl der Sperrtreffer im Protokoll, damit ein
Lauf hinterher sagen kann, ob die Sperre überhaupt auftrat; null ist die
erwartete Zahl. Der zweite Fall sagt nach dem Umbau mehr als vorher und nicht
weniger: er wartet die Aufgabe ab, statt auf ein Ereignis zu hoffen, und liest
die Zahl der Läufe danach statt mittendrin.

Der dritte Stamm ist bewusst nicht gefixt. Es gibt zwei Fehlschläge desselben
Schritts an zwei verschiedenen Ästen derselben Funktion, und die Deutung ist
offen: der ältere antwortete mit 404 auf der Ergebnisseite, der jüngere
verweigerte die Anmeldung selbst. Ein Fix ohne diese Deutung wäre eine
Vermutung im Erzeugnis, und eine Änderung an der Paritätsstrecke unmittelbar
vor einem Release-Tag ersetzt ein seltenes Flattern durch ein neues Risiko.
Geht der Auftrag in der Abgabewoche rot, gilt der Merker der Kopfzeile.
