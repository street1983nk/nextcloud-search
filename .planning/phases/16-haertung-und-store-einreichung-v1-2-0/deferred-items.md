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

---

## Nachtrag vom 21.09.2026: der Upgrade-Beweis 1.1.0 auf 1.2.0 ist gebaut, aber nicht gefahren

**Befund.** Plan 16-09 hat den Auftrag `deploy-harp` auf den Sprung 1.1.0 auf
1.2.0 umgestellt (`UPGRADE_FROM_TAG: v1.1.0`, umgedrehte Vorbedingung in "Store
upgrade 1", getauschte Vorbedingung des Vorher-Zustands, neue Zusicherung 6 auf
den zwei Datumsgrenzen des Anbieters). **Task 3, Teil 2 des Plans, das
Auslesen eines echten Laufs, konnte in dieser Ausfuehrung nicht stattfinden:**
der Ausfuehrungsauftrag verbietet das Pushen ausdruecklich, und der Auftrag
laeuft ausschliesslich auf einem Runner. Die Datei ist lokal geprueft (YAML
parst, `sh -n` auf dem ausgeloesten Sondenskript, beide jq-Zweige gegen selbst
gebaute Abbilder, die umgedrehte `<navigations>`-Pruefung gegen `git show
v1.0.3:` und `git show v1.1.0:`), aber lokal gruen ist hier kein Beweis.

**Verdikt: GESCHLOSSEN am 21.09.2026.** Der Push von 73cbca1 hat den Lauf
35594647362 gestartet (HaRP deploy, deploy-harp stable34/ubuntu-24.04,
success). Alle vier Pruefzeilen stehen als echte Ausgaben im Protokoll:
"the companion of v1.1.0 declares the navigation entry" (Store upgrade 1),
"three terms, one file each; no date bounds on the provider" (Store upgrade 3),
"the instance performed the app update: 1.1.0 to 1.2.0" (Store upgrade 4,
erster Zweig, kein notice-Ausweich), "the two date bounds were not declared
before the upgrade and are declared after it" und "all six assurances hold"
(Store upgrade 5). Erfolgskriterium 3 von REL-02 ist damit mit einer
Laufnummer belegt; das Abhaken von REL-02 selbst bleibt bei Plan 16-14.

Urspruengliches Verdikt vor dem Lauf: offen, mit benannter Zieladresse und
Pruefweg, kein Fix noetig.

**Begruendung.** Erfolgskriterium 3 von REL-02 verlangt einen Lauf und keine
Datei. Der Punkt bleibt deshalb bis zur Laufnummer offen und wird nicht als
erledigt gefuehrt, auch wenn der Code steht. Die Lehre aus 11-11 gilt
unveraendert: der erste Lauf eines Beweises, der zum ersten Mal wirklich
greift, findet Fehler, und diese Fehler gehoeren gesucht und nicht weggewartet.

**Zieladresse.** Der Orchestrator der Phase 16, mit dem Push der Commits von
16-09. Der Pruefweg im Einzelnen steht in `16-09-SUMMARY.md`, Abschnitt "Was
der Orchestrator in CI nachsehen muss".

---

## Nachtrag vom 21.09.2026 (Plan 16-13): der Abschluss der Phase-15-Liste

Die Befundliste des Phasenaudits 15 hat elf weitergereichte Punkte. Hier steht
je Punkt, wo er heute steht, damit die Liste an einer Stelle zu Ende gefuehrt
ist und niemand sie aus sieben SUMMARY-Dateien zusammensuchen muss. Der volle
Beleg je Zeile steht in `docs/audits/2026-09-phase-16/README.md`, Abschnitt 7.

| Befund | Stand am 21.09.2026 | Wo |
|---|---|---|
| M-01 | **teilerfuellt**, und das ist die ehrliche Zeile: die Instrumentierung des inneren Aufrufs steht, die Zahl auf Zielhardware steht aus. Sie entsteht auf einer Box und nirgends sonst, und diese Phase hat keine gefahren | Plan 16-06 |
| M-02 | **geschlossen** in drei Schritten: Gate ueber `docs/`, Bereinigung mit Restliste, und die zehnte Familie aus Plan 16-13, die die Luecke schliesst, die beide gelassen hatten (Befund M-16-02) | Plaene 16-02, 16-05, 16-13 |
| L-03 | **behoben** als Nachfolgefassung `92c-wechsel.sh`; Wirkung nicht nachgemessen | Plan 16-03 |
| L-04 | **behoben** als Nachfolgefassung `99d-filter-sortierung.sh`; Wirkung nicht nachgemessen | Plan 16-03 |
| L-05 | weitergereicht, Adresse: erster Plan der naechsten bezahlten Anfahrt | dieser Datei, eigener Abschnitt oben |
| L-06 | weitergereicht, Adresse: erster Plan der naechsten bezahlten Anfahrt | dieser Datei, eigener Abschnitt oben |
| L-07 | **behoben**: `cmd_destroy` nimmt das Schluesselpaar mit und liest es zurueck; nur statisch geprueft | Plan 16-04 |
| L-08 | benannte Asymmetrie, kein Fix, entschieden und begruendet | dieser Datei, eigener Abschnitt oben |
| L-09 | **geschlossen** mit Lauf 35586213137 und dem Owner-Wort "Zweig a, zustimmen" | Plan 16-08, Nachtrag oben |
| L-10 | **behoben**: Vokabularregel im Gate und 52 Ersetzungen in vier Dokumenten; drei Vorkommen bleiben mit je eigenem Grund | Plaene 16-02, 16-05 |
| L-11 | **hat nicht getragen.** Der Fix aus Plan 16-01 ist danach viermal in CI gescheitert; der Punkt lebt als M-16-01 weiter und ist dort zum zweiten Mal behandelt worden | Plaene 16-01 und 16-13 |

---

## L-16-01: derselbe Wettlauf im Nachbarfall der zehn Suchen

**Befund.** `test_ten_searches_in_a_row_do_not_pay_for_ten_loads` faehrt zehn
Anfragen durch den Testclient und liest danach, ob wirklich ein Hintergrundlauf
stattgefunden hat. Er haengt damit an derselben Wurzel wie M-16-01: der
Testclient oeffnet je Anfrage ein eigenes Tor und schliesst es wieder, und eine
Aufgabe, die der Handler mit `create_task` bestellt, ist eine lose Aufgabe auf
dieser Schleife.

**Verdikt: dokumentiert weitergereicht, kein Fix in dieser Phase.**

**Begruendung.** Der Fall ist nie rot gewesen, und der Grund ist zaehlbar: zehn
Anfragen sind zehn Wettlaeufe, und es reicht, wenn einer davon gewonnen wird.
Seine Aussage macht er genau ueber die zehn Anfragen DURCH DIE ROUTE, und ein
Umbau auf die Schleife des Falls, wie ihn M-16-01 bekommen hat, wuerde diese
Aussage ersetzen statt sie zu haerten. Ein Fall, der eine andere Frage
beantwortet, ist kein gehaerteter Fall.

**Zieladresse.** Der naechste Plan, der die Warmlauf-Faelle anfasst. Wer ihn
aufnimmt, liest M-16-01 im Phasenaudit 16 daneben, bevor er eine Frist
verlaengert: eine Frist war dort nie die Ursache.

---

## L-16-02: ein roter Lauf, den kein Plan gelesen hat

**Befund.** Die vier roten Laeufe der Werkbank `python.yml` vom 21.09.2026
(35586354661, 35594647359, 35596116820, 35597353833) sind entstanden, ohne dass
eine SUMMARY dieser Phase sie nennt. Die SUMMARY von Plan 16-10 nennt fuer
denselben Push den gruenen Abbildbau und nicht den roten Gate-Lauf daneben. Ein
Plan liest den Lauf, den er erwartet, und nicht die Laufliste des Pushes.

**Verdikt: dokumentiert weitergereicht als Verfahrensregel.**

**Begruendung.** Das ist kein Fehler eines einzelnen Plans, sondern eine Luecke
in der Form: die Plaene nennen in ihrem `verify` die Laufnummer, die sie
brauchen, und ein Lauf, den kein Plan braucht, hat niemanden, der ihn ansieht.
Genau so ist der Fix aus 16-01 vier Laeufe lang unbemerkt durchgefallen. Die
Gegenmassnahme kostet einen Befehl und keine Werkbank.

**Die Regel, im Wortlaut fuer den naechsten Plan.** Nach einem Push wird
`gh run list` fuer diesen Push gelesen, nicht nur der Lauf, den der Plan
erwartet. Jeder nicht-gruene Lauf wird in der SUMMARY benannt, mit Laufnummer
und Ausgang, bevor sie geschrieben ist. Ein roter Lauf, der nicht benannt ist,
ist ein roter Lauf, der zaehlt.

**Zieladresse.** Plan 16-14 fuer den Tag-Push dieser Phase, und danach der
Planer der naechsten Phase, der die Regel in die `verify`-Bloecke aufnimmt.

---

## L-16-03: der dritte Flake-Stamm bleibt offen

**Befund.** Der Stamm `parity-login` des Flake-Registers ist unveraendert offen.

**Verdikt: beobachtet, kein Fix, wie in Plan 16-01 entschieden.**

**Begruendung.** Er ist in dieser Phase **nicht** wieder aufgetreten; der
Paritaetsauftrag war in jedem Lauf dieser Phase gruen. Die Deutung des Stammes
ist weiterhin offen (zwei Fehlschlaege desselben Schritts an zwei verschiedenen
Aesten derselben Funktion), und ein Fix ohne Deutung waere unmittelbar vor einem
Release-Tag eine Vermutung im Erzeugnis.

**Zieladresse.** Keine neue. Es gilt der Merker der Kopfzeile des
Flake-Registers: geht der Auftrag in der Abgabewoche rot, wird zuerst
wiederholt und dann gesucht, und der aeltere Befund `parity-login-probe-404`
wird daneben gelesen.

---

## L-16-04: eine Annahme ueber den paths-Filter bei Tag-Pushes, die nicht stimmt

**Befund.** Die Kommentare in `.github/workflows/docker.yml` und
`.github/workflows/release.yml` sagen, GitHub wende den `paths`-Filter auf jedes
Push-Ereignis an, Tag-Pushes eingeschlossen, ein Release-Tag auf einem Commit
ohne `backend/**` ueberspringe den Abbildbau also. `release.yml` begruendet damit
sogar, warum es selbst keinen Filter traegt.

**Das Gegenteil ist belegt.** Tag `v1.0.0` sitzt auf `160a289`, und dieser Commit
beruehrt nur `store/media/**`, also keinen einzigen Pfad aus den Filtern der
sechs anderen Werkbaenke. Trotzdem sind am Tag-Push alle sieben Laeufe als
`push` gestartet, und zwar mit echten Jobs statt uebersprungenen: Lauf
**34140924599** baute beide Architekturen und mergte das Manifest, Lauf
**34140924650** fuhr php -l, die info.xml-Validierung und PHPUnit. Bei `v1.0.1`
dasselbe Bild. Geprueft am 21.09.2026 vor dem Tag der Phase 16.

**Verdikt: weitergereicht, kein Fix vor dem Tag.**

**Begruendung.** Der Kommentar haette vor dem Tag geaendert werden koennen, und
genau das waere falsch gewesen: eine Aenderung an `docker.yml` haette den Baum
unter dem Tag von dem Baum getrennt, den das Phasenaudit geprueft hat, und den
Sitz des Tags fuer einen Kommentar bewegt. Die Annahme hat nichts kaputt
gemacht; sie haette nur die Wahl des Tag-Commits unnoetig eingeschraenkt.

**Zieladresse.** Der erste Plan der naechsten Phase, der ohnehin einen Workflow
anfasst. Zu aendern sind zwei Kommentarbloecke, keine Zeile Verhalten. Wer es
aufnimmt, haengt die zwei Laufnummern als Beleg daneben, sonst steht die naechste
Behauptung so unbelegt da wie die jetzige.

---

## L-16-05: eine Zugangsmarke, die beim Setzen schon ueberholt war

**Befund.** Der erste Einreichungslauf (**35617988639**) endete mit
`release findling v1.2.0: HTTP 401`. Die Marke war Minuten vorher frisch geholt
und gesetzt worden. Die Erneuerung hat doppelt ausgeloest beziehungsweise die
Seite zeigte nach dem ersten Klick den aelteren der beiden Werte; eine zweite
Erneuerung macht die erste ungueltig, und auf der Seite sehen beide gleich aus.

**Verdikt: behoben im zweiten Anlauf, die Lehre bleibt als Verfahrensregel.**

**Die Regel, im Wortlaut fuer den naechsten Plan, der eine Marke setzt.** Eine
neu geholte Zugangsmarke wird **vor** dem Setzen gegen die Schnittstelle
geprueft, und zwar mit einem Aufruf, der nichts veraendert: ein leerer Rumpf auf
die Release-Route. Antwortet sie mit HTTP 400 und einem Feldfehler, ist die Marke
gueltig und nur der Rumpf leer. Antwortet sie mit HTTP 401, ist die Marke
ueberholt, und das Setzen unterbleibt. Die Gegenprobe mit dem alten Wert gehoert
dazu, sonst belegt der 400er nur, dass die Route erreichbar ist.

**Was richtig gelaufen ist und so bleiben soll.** Der Lauf hat an der 401
abgebrochen und ist nicht wiederholt worden, bis er zufaellig gruen war. Genau
das verlangt der Plan der Abgabe fuer jeden Code, der nicht 201 ist.

**Zieladresse.** Der Planer des naechsten Releases. Die Regel gehoert in den
Checkpoint-Text der Rotation, nicht in eine SUMMARY, weil sie zwischen zwei
Handgriffen des Owners steht.
