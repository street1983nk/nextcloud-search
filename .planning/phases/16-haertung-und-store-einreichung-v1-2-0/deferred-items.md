# Zurueckgestellte Punkte der Phase 16

Diese Datei traegt die Verdikte der Punkte, die diese Phase nicht baut. HART-01
laesst "abgearbeitet ODER dokumentiert entschieden" ausdruecklich zu; was die
Anforderung nicht zulaesst, ist ein Punkt ohne Verdikt. Jeder Eintrag unten
nennt deshalb Kennung, Befund in einem Satz, Verdikt, Begruendung und, wo er
weitergereicht wird, eine Zieladresse. Kein Verdikt lautet "spaeter".

Die Punkte stammen aus zwei Listen: den aufgeschobenen Befunden der Phase 11
(`.planning/milestones/v1.1-phases/11-haertung-und-store-einreichung-v1-1/deferred-items.md`)
und der Befundliste des Phasenaudits 15 (`docs/audits/2026-09-phase-15/README.md`,
Abschnitt 7).

## Wo die uebrigen Befunde der Phase 15 ihr Verdikt bekommen

Damit die Befundliste an einer Stelle vollstaendig adressiert ist, und damit
niemand einen Punkt hier sucht, der woanders steht:

| Befund | Wo er sein Verdikt bekommt | Art |
|---|---|---|
| L-03, L-04 | Plan 16-03 | gebaut, Nachfolgefassungen 92c und 99d |
| L-07 | Plan 16-04, Task 2 | gebaut, `cmd_destroy` nimmt das Schluesselpaar mit |
| L-09 | Plan 16-08, **geschlossen am 21.09.2026** | Erfolgskriterium 4, neu gemessen statt neu behauptet; siehe den Nachtrag unter der Tabelle |
| L-10 | Plaene 16-02 und 16-05 | Gate ueber `docs/`, danach die Bereinigung |
| L-11 | Plan 16-01 | gebaut, zweite Zeitkonstante, dazu das Flake-Register |
| M-01 | Plan 16-06 | die 1,5-Sekunden-Decke und was die Rohdateien ausweisen |
| M-02 | Plaene 16-02 und 16-05 | Geheimnis-Gate mit Ausnahmeliste, danach die Bereinigung |

Die sieben Eintraege unten sind der Rest: vier aus DI-11 und drei Werkzeug- und
Verfahrensbefunde der Phase 15.

### Nachtrag vom 21.09.2026: L-09 ist geschlossen

**Befund.** Erfolgskriterium 4 der Phase 15 war nicht erfuellt: fuenf der zehn
deutschen Sprachfaelle hiessen "nicht messbar", weil die Messinstanz den
Korpus-Snapshot trug und die eigene Datei in rund 52.000 Fremddokumenten mit
denselben Woertern ausserhalb der 64 Rechecks lag.

**Verdikt: geschlossen, gemessen statt behauptet.**

**Der Beleg.** Lauf **35586213137** vom 21.09.2026, Auftrag `index-search-e2e
(sqlite, ubuntu-24.04-arm)` der Werkbank `integration.yml`, 3 min 43 s, success
beim ersten Anlauf. Die Instanz meldet vor dem Korpus `files on the instance
before the corpus: 0` und danach `corpus entries: 39`. **Zehn von zehn
Sprachfaellen gruen, null rot, null ohne Aussage**; alle fuenf zuvor nicht
messbaren Faelle (`Genehmigung`, `Frist`, `Vertrag`, `bescheid`,
`type:pdf bescheid`) tragen jetzt eine Aussage. Der ausfuehrliche Bericht mit
Bedingungen, Gegenueberstellung zur Phase 15 und dem Pflichtabschnitt "Was
dieser Lauf nicht beweist" steht in
`docs/measurements/2026-09-a4-sprachfaelle-ci/README.md`; sein Urteil zum Weg
lautet **traegt**.

**Die Freigabe.** Owner-Entscheid am Checkpoint des Plans 16-08 vom 21.09.2026
im Wortlaut: "Zweig a, zustimmen". Auflage A4 ist damit ueber den kostenlosen
CI-Weg des Entscheids E3 erfuellt, **keine Box, kein Deckel-Abruf**.

**Zieladresse.** Keine. Der Ast bleibt als dauerhaftes Gate stehen und faengt
den naechsten Rueckschritt in einem der zehn Faelle auf arm64 genauso wie auf
amd64.

---

## DI-11-02: eine leere Antwort ohne Protokollspur

**Befund.** Auf Kontrollstufe 8 der v1.1-Anfahrt blieb einer von 80 Vorgaengen
ohne Erklaerung: acht der neun Fehlschlaege gehen auf einen Begriff ohne Treffer
im Lastkorpus, der neunte bekam eine leere Ergebnisgruppe, ohne dass im
Nextcloud-Protokoll im Lastfenster eine Zeile der Apps `findling` oder `app_api`
entstand.

**Verdikt: dokumentiert entschieden, zu.**

**Begruendung, mit Zahlen statt mit Zuversicht.** Plan 11-13 hat am 10.09.2026
genau diesen Fall mit einem eigenen Zustand versehen,
`SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED`, der statt einer leeren Liste
einen Satz zurueckgibt. Die v1.2-Anfahrt vom 21.09.2026 ist MIT diesem Stand
gefahren. Die vier in v1.1 regressiven Laststufen sind je mit "behoben"
entschieden (Bericht `docs/measurements/2026-09-v12-messung/README.md`,
Abschnitt 5: Stufe 4 mit 1.006,8 ms gegen 1.068,0 ms, Stufe 8 mit 1.992,0 ms
gegen 2.125,5 ms, Stufe 12 mit 2.950,6 ms gegen 3.453,4 ms, Stufe 16 mit
4.091,1 ms gegen 4.446,2 ms). Die Gegenrechnung ist unabhaengig vom Lastwerkzeug
im Nextcloud-Protokoll gefahren worden, gezaehlt auf `cURL error 28`: im
Lastfenster 02:10 bis 02:13 **null** Treffer
(`rohdaten/97-nebenlaeufigkeit.txt`, Zeilen 147 und 148). Alle als `failures`
gemeldeten Faelle dieser Anfahrt sind also echte Leertreffer und keine
verschluckten Zeitueberschreitungen; in v1.1 war genau das anders.

**Der Satz, der dazugehoert.** Die v1.1-Box trug den Stand aus 11-13 nicht, weil
sie seit dem 10.09.2026 angehalten war und kein neues Abbild bekam. Der alte
Befund ist damit nicht widerlegt, sondern ueberholt: die Lage, in der er
entstand, gibt es in dieser Fassung nicht mehr, und ein Beweis fuer die damalige
Ursache waere nur mit einer neuen Anfahrt auf einem alten Abbild zu haben. Das
ist Geld fuer eine Frage, deren Antwort nichts mehr aendert.

---

## DI-11-03: der Zaehler unterscheidet leer nicht von abgebrochen

**Befund.** `EmptyResultGroup` zaehlte jede Antwort unter `--min-hits`, gleich ob
ein Containeraufruf abgebrochen war oder die Suche schlicht nichts gefunden hat.

**Verdikt: abgearbeitet in Plan 16-04, Task 1.**

**Begruendung.** Der alte Eintrag hat die Trennung nicht am Termin, sondern an
der Technik zurueckgestellt: die OCS-Route antwortet in beiden Faellen mit
HTTP 200 und einer Ergebnisgruppe ohne Containerteil, ein zweiter Fehlschlagname
waere also ein Name ohne Unterscheidungsmerkmal gewesen. Die Zutat, die fehlte,
ist seit Plan 12-04 da: die Sonde `73-bestand-sonde.py` liest den ungedeckelten
Bestand je Begriff im Prozess des Containers ueber `ranked_sides`. Dieselbe
Frage stellt `scripts/ops/search_load.py` jetzt vor der ersten Laststufe.
Begriffe ohne Bestand heissen ab dann `ohne-treffer` und nicht `fehlschlag`, die
Gesamtzahl steht daneben, damit alte Rohdaten vergleichbar bleiben, und
antwortet die Sonde nicht, dann traegt die Rohdatei die Zeile
`vorlaufsonde: nicht verfuegbar` und die Trennung unterbleibt sichtbar.

**Was dabei benannt und nicht geschlossen ist.** Die Sonde fragt nur die
lexikalische Haelfte und uebergibt `ranked_sides` keine semantische Seite, weil
diese das Abfragemodell laedt und genau den Container aufwaermen wuerde, dessen
Speicher gleich gelesen wird. Ein Begriff ohne lexikalischen Bestand kann
deshalb von der Vektorhaelfte beantwortet werden, und eine leere Antwort auf
einen solchen Begriff faellt auch dann unter `ohne-treffer`, wenn der Aufruf
abgebrochen ist. Das steht als Grenze im Kommentar des Werkzeugs.

---

## DI-11-05: der pgsql-Ast von `index-search-e2e` flattert

**Befund.** Ein Job von sieben endete mit `curl: (22) ... error: 423` nach
`revision 8 written`, also an der WebDAV-Sperre von Nextcloud, auf einem Commit,
der ausschliesslich Planungsdateien aenderte.

**Verdikt: abgearbeitet in Plan 16-01, Task 1.**

**Begruendung.** Die enge Wiederholung auf 423 steht jetzt im Schritt selbst,
statt dass ein neunter blinder Schreibvorgang folgt, und der Stamm ist mit
Kennung, letzter roter Laufnummer, gefahrener Gegenprobe und Verdikt in
`docs/audits/2026-09-phase-16/flake-register.md` gefuehrt. Damit ist der Merker
"erst wiederholen, dann suchen" nicht mehr eine Zeile in einer SUMMARY, sondern
eine Eigenschaft des Auftrags.

---

## DI-11-06: die Suche kennt die Version des Containers nur vom Hoerensagen

**Befund.** `SearchService` entscheidet ueber eine Versionsdrift anhand von
`oc_appconfig.backend_app_version`, also anhand der Antwort, die der Container
gegeben hat, als ihn zuletzt etwas gefragt hat; das Einzige, was ihn je fragt,
ist die Einstellungsseite.

**Verdikt: dokumentiert entschieden, weitergereicht nach v1.2.**

**Begruendung.** Die Aenderung, die den Punkt schliesst, fuehrt die Version in
der Antwort mit, die die Suche ohnehin holt. Das ist eine Protokollaenderung an
beiden Haelften, sie sitzt auf dem Suchpfad, und sie kaeme in derselben Phase,
die eine Abgabe traegt. Genau in dieser Lage hat Plan 11-11 sie schon einmal
zurueckgestellt, und die Begruendung ist heute dieselbe: der Nutzen ist ein
Fenster zwischen Update und erstem Oeffnen der Einstellungsseite, der Einsatz
waere der Pfad, auf dem die Suche jeden Treffer holt.

**Die Kehrseite, ausdruecklich mitgeschrieben.** Solange die Versionsmarke so
gepflegt wird wie heute, braucht **jeder** Minor-Sprung eine Migration nach dem
Muster von `Version001100Date20260911000000`. Das ist der Grund, warum REL-02
fuer den Sprung auf 1.2.0 eine verlangt, und der Satz steht auch im
Klassenkommentar der Migration, weil das die Datei ist, die jemand liest, wenn
er die naechste schreibt. Plan 16-07 schreibt ihn fort.

**Zieladresse.** Ein eigener Milestone nach v1.2, der die Protokollaenderung und
den Wegfall des Migrationszwangs zusammen traegt. Getrennt gebaut waere die
Aenderung ein Umbau ohne Ertrag: erst wenn die Marke bei jeder Suche frisch ist,
darf die Migration je Minor-Sprung entfallen.

---

## L-05: Vorgabebenutzer in zwei Messwerkzeugen

**Befund.** `94b-grundlast-rueckkehr.sh` und `95b-wiederaufwaermen.sh` fuehren
einen Vorgabebenutzer, dem der Messkorpus nicht gehoert; die Suche liefert dann
null Treffer.

**Verdikt: dokumentiert weitergereicht an die naechste Anfahrt.**

**Begruendung, nicht beschoenigt.** Das ist ein echter Defekt der Werkzeuge und
keine Frage der Bedienung. Er hat keine Nutzerwirkung, weil beide Dateien
Messwerkzeuge sind und kein Teil des Erzeugnisses. Seine Behebung verlangt eine
vollstaendige Nachfolgefassung einer 36 Kilobyte grossen Datei, denn die
gefahrenen Fassungen sind eingefroren und werden nicht editiert. Eine
Nachfolgefassung, die niemand faehrt, ist ungetesteter Text.

**Zieladresse.** Der erste Plan der naechsten bezahlten Anfahrt, zusammen mit
L-06. Der Behelf der Phase 15 steht hier als das, was er war: eine kurzzeitige
Gruppenmitgliedschaft auf der Box, danach wieder entfernt.

---

## L-06: der Aufruf einer Datei ohne Ausfuehrungsrecht

**Befund.** `94b-grundlast-rueckkehr.sh` ruft das Messwerkzeug direkt auf,
waehrend die Datei mit Modus 100644 im Baum steht; der Lauf endete mit
`command not found` und Rueckgabewert 32.

**Verdikt: dokumentiert weitergereicht an die naechste Anfahrt.**

**Begruendung.** Dieselbe wie bei L-05, mit einer eigenen Zahl: die betroffene
Nachfolgefassung waere hier eine 30 Kilobyte grosse Datei, und der Fix ist keine
Zeile, sondern eine Entscheidung zwischen zwei Wegen (der Aufruf ueber den
Interpreter oder das Ausfuehrungsrecht im Baum), die in einer Anfahrt und nicht
am Schreibtisch faellt. Beide werden gebaut, wenn sie gebraucht werden.

**Zieladresse.** Der erste Plan der naechsten bezahlten Anfahrt, zusammen mit
L-05. Der Behelf der Phase 15 war ein `chmod +x` auf der Box.

---

## L-08: drei Werkzeuge waehrend der bezahlten Zeit geaendert

**Befund.** Das Runbook verbietet, waehrend einer Anfahrt ein Werkzeug zu
aendern; dreimal ist es geschehen, je mit ausdruecklichem Owner-Wort und je,
weil ein Werkzeug auf einem korrekten Zustand abbrach. Der Pruefsummen-Waechter
aus Plan 15-15 friert den Stand **nach** der Anfahrt ein.

**Verdikt: bleibt als benannte Asymmetrie. Kein Fix.**

**Begruendung.** Ein Waechter, der die Staende von vor den drei Aenderungen
einfroere, wuerde eine Fassung schuetzen, gegen die keine Zahl dieser Anfahrt
gemessen ist. Die Asymmetrie ist nicht aufloesbar, sondern nur benennbar: wer
die Zahlen nachrechnen will, braucht fuer zwei Werkzeuge die Vorgaengerfassung
aus der Historie und nicht die eingefrorene. Die Gegenmassnahme ist deshalb der
Verweis auf die Pruefsummen der Staende davor, und die stehen in
`15-15-SUMMARY.md`.

**Zieladresse.** Keine. Der Punkt ist entschieden und bleibt als Eigenschaft der
Anfahrt stehen, damit ein spaeterer Leser ihn findet, bevor er sich wundert.
