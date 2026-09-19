---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Messbeleg und Ausbau
status: executing
stopped_at: Completed 15-01-PLAN.md
last_updated: "2026-09-19T20:05:00.000Z"
last_activity: 2026-09-19
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 49
  completed_plans: 34
  percent: 69
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-11)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 15: messphase-eine-box-anfahrt

## Current Position

Phase: 15 (messphase-eine-box-anfahrt): **IN AUSFUEHRUNG, Welle A ohne Box**
Plan: 1 von 16 abgeschlossen (15-01)
Status: Phase 14 ist abgenommen. Phase 15 laeuft; 15-01 hat das Laufverzeichnis
der Anfahrt mit elf byteweise uebernommenen Werkzeugen bestueckt und den
Kopie-Waechter gesetzt. Naechster Plan ist 15-02 (Runbook, Deckel, Block 13b).
Progress: [███████░░░] 69% der 49 geplanten Plaene (34 von 49; Phase 16 ist noch nicht geplant)
Last activity: 2026-09-19 -- 15-01, die elf Kopien und ihr Waechter.

**Abnahmesatz.** Der Owner hat die Phase 14 am 19.09.2026 mit dem Wort
"abgenommen" freigegeben, einschliesslich des franzoesischen Wortlauts des
sechsten Engine-Satzes (unveraendert wie vorgelegt) und des Vorschlagswerts
900 s (bleibt stehen, als Schaetzung deutlich gekennzeichnet). MEM-02 ist von
der Abnahme ausdruecklich ausgenommen und bleibt offen, bis die Box-Anfahrt der
Phase 15 an der Messgroesse "Rueckkehr zur Grundlast nach einem Indexlauf"
gemessen hat.

Was 14-12 belegt hat: der Gesamtlauf aller sechs Gate-Stufen in einem Zug gruen
(2262 bestanden, 15 uebersprungen, Skipzahl unveraendert gegen 13-13), der
Auditbericht `docs/audits/2026-09-phase-14/README.md` mit Gate-Protokoll, ASVS
V5/V7/V12, dem geprueften V4-Vorbehalt, sechs Bug-Pfaden, dem
Performance-Durchgang und der Gegenprobe zu Annahme A9. Drei LOW-Befunde, zwei
behoben (L-01 der fehlende V4-Paritaetsfall, L-03 die Kennzeichnung des
Vorschlagswerts), einer als benannte Asymmetrie weitergereicht (L-02).

Die fuenf Erfolgskriterien sind an der laufenden Instanz nachgesehen: der
Schalter meldet sich in allen drei Stellungen richtig (ohne, `=60`, `=3`), der
Container gibt nach 75 s 376,3 MB zurueck und meldet `unloaded`, die erste Suche
danach antwortet in 1,43 s mit Volltexttreffern (warm 0,41 bis 0,48 s), kein
neuer `cURL error 28`, und die Admin-Seite traegt den Satz des sechsten Zustands
in beiden Haelften gleichlautend.

**Offener Messauftrag an Phase 15** (kein Blocker der Phase 14): die Marge der
ersten Suche nach einer Entladung ist auf der Entwicklungsmaschine duenn, 60 bis
130 ms unter der Decke von 1,5 s. Die Ursache liegt im Nachwaermlauf und nicht
in der Degradation; auf einer langsameren Box koennte sie aufgezehrt werden.

Phase 13 ist vollstaendig (Owner-Abnahme 19.09. erteilt, FILT-01..05 und HART-03 erfuellt)

Phase 12 ist vollstaendig: 12-02 hat den stable35-Entscheid am Stichtag
vollzogen (Zweig a, Beweislauf 35095805558 gruen, deploy-harp-Flag gefallen).

## Entscheide aus der Ausfuehrung

- 15-01: Eine Kopie traegt den Dateimodus ihres Originals mit. Die vier im
  Original ausfuehrbar abgelegten Werkzeuge liegen auch in der Kopie mit 100755
  im Index, die uebrigen sieben mit 100644; damit stimmen Blobkennung UND Modus
  ueberein, und die Gleichheit ist an `git ls-files -s` ablesbar und nicht nur
  an einer Pruefsumme.
- 15-01: Der Kopie-Waechter vergleicht Kopie gegen Original statt gegen eine
  aufgeschriebene Pruefsumme. Bei den gefahrenen Fassungen steht die Zahl in der
  Datei, weil das Original selbst wandern koennte; hier ist genau die Gleichheit
  der beiden Dateien die Zusage, und eine dritte aufgeschriebene Zahl waere eine
  weitere Stelle, die driften kann.
- 15-01: Neben dem Pruefsummenfall haelt ein zweiter Fall die vollstaendige
  Werkzeugliste der Messreihenfolge (vierzehn Namen, elf Kopien plus die drei
  bereits vorhandenen). Die Werkzeuge aus 15-03 bis 15-06 stehen bewusst NICHT
  darin: eine Liste, die kuenftige Dateien nennt, waere heute rot aus einem
  Grund, der kein Befund ist.

- 14-12 (Abnahme): Der fehlende V4-Paritaetsfall wird angelegt und nicht nur
  protokolliert. Die Lehre aus 13-13 gilt: ein Audit-Pfad ohne Gate bekommt ein
  Gate. Vier Faelle in `test_semantic_search.py` halten, dass die entladene
  Runde hinter dem ACL-Vorfilter bleibt und dass `may_load` in keiner PHP-Quelle
  steht.
- 14-12 (Abnahme): Die Sichtprobe zur ersten Suche nach einer Entladung wird
  mit ihrem Abstand zur Decke berichtet und nicht als blosses Unterschreiten.
  1,37 bis 1,44 s kalt gegen 0,41 bis 0,48 s warm ist eine duenne Marge, und die
  Zahl gehoert dem Owner vor die Abnahme; die Ursache liegt im Nachwaermlauf und
  nicht in der Degradation (die einwortige Zeile ohne Vektoranteil misst
  dasselbe).

- 14-11 (Dokumentation): Der alte Abschnitt "Modell-Entladung nach Leerlauf:
  nein, mit drei Zahlen" in `docs/performance.md` wird nicht geloescht, sondern
  bekommt einen datierten Nachtrag. Seine drei Zahlen gelten weiter (die
  Entladung senkt weder die Spitze eines Indexlaufs noch die Grundlast eines
  Containers, der nie eingebettet hat); ueberholt ist nur sein Schluss, und
  Punkt 3 ist durch die Degradationsnaht aus 14-08 entschaerft.

- 14-11: Die Messgroesse steht als ASCII-Bezeichner
  `Rueckkehr zur Grundlast nach einem Indexlauf` in Backticks, obwohl
  `docs/performance.md` sonst Umlaute in Ueberschriften traegt. Sie ist ein
  Name, gegen den spaeter gegriffen wird, und ein Name traegt keine Umlaute.

- 14-11: Der A/B-Messschritt des Runbooks beginnt mit den Kaltmessungen. Jede
  Messung waermt den Seitencache des Wirts, und eine einmal gewaermte
  Kaltmessung ist ohne erneutes Leeren nicht wiederholbar. Die Reihenfolge ist
  deshalb bindend und keine Empfehlung.

- 14-10 (MEM-05, die Zusage): Die Freigabe der vierten Phase laeuft ueber
  `shared_model().release()` und nicht ueber `release_if_idle`. Die Politikstelle
  traegt die Uhr, und ihre Frist kommt aus `embed_idle_release_seconds`, wo null
  das Wort fuer aus ist: in der Werksstellung antwortet sie sofort False und
  wuerde nichts messen, eingeschaltet wuerde das Werkzeug eine Admin-Einstellung
  aussitzen. Gemessen wird die Mechanik der Zusage, nie die Frist.

- 14-10: Nachgeladen wird ueber `drive_the_search_side()` und nicht ueber
  `engine.warm()`. Das Werkzeug misst seit seiner ersten Fassung durch den
  echten Aufrufweg; ein Aufrufer, der aufhoert, ueber den Halter zu gehen, soll
  auffallen statt gemessen zu werden.

- 14-10: Die Mutation "Warmfenster laedt zweimal" haengt am Entladezaehler und
  gilt deshalb erst ab der vierten Phase. Ein von Anfang an gebrochenes
  Single-Flight haette auch den zweiten Track ein zweites Mal laden lassen, das
  Werkzeug waere am alten Zaehler rot geworden, und der Fall haette den falschen
  Befund belegt.

- 14-10: Die Fehlerausgabe des Schritts in `resilience.yml` wird mitgezogen,
  obwohl das Abnahmekriterium des Plans nur Kommentarzeilen vorsah. Der Plan
  verlangt in seinen must_haves ausdruecklich, dass der Erklaertext IM
  FEHLERPFAD die alte Zusage nicht mehr sagt, und genau dort stehen die
  echo-Zeilen. Aufruf, Exit-Behandlung und Artefakt des Schritts sind
  unveraendert.

- 14-09 (MEM-05, das sechste Wort): Der Zustand wird aus dem monotonen
  Entladezaehler abgeleitet und nicht aus einem neuen Feld. Ein Feld haette
  gesetzt werden muessen, ein Zaehler ist schon da, und er hat eine Eigenschaft,
  die hier zaehlt: ein Prozess, der nie entladen hat, steht auf null und kann
  das Wort gar nicht melden. Der Zweig steht hinter `loaded`, weil ein Container,
  der nach einer Freigabe wieder geladen hat, geladen ist.

- 14-09: Die sechs Katalogeintraege reisen im selben Commit wie die zwei
  Seitenhaelften und die zwei Gate-Literale. Das Satz-Gate sucht die neuen Saetze
  im deutschen Katalog, also waere jede andere Reihenfolge ein roter Commit
  gewesen. Die Dokumentationshaelfte ist ein eigener Commit geblieben.

- 14-09: Der Entladezaehler wird je Testfall in `conftest.py` auf null gesetzt
  (`forget_the_release_count`, nach dem Muster von `forget_the_cutter_notice`).
  Ohne das entscheidet eine Freigabe in `test_embed_model.py`, was
  `test_status_endpoint.py` drei Dateien spaeter als Zustand liest. Im Container
  wird nichts zurueckgesetzt, T-14-17 bleibt unberuehrt.

- 14-08 (MEM-03, die Naht): `request_warm()` steht in `one_round` an der Zeile,
  an der die `SemanticSide` ohne Ladeerlaubnis gebaut wird, und nicht im
  Handler. Nur dort sind beide Haelften des Satzes bekannt: dass die Runde
  hybrid gemeint war und dass sie ohne Gewichte antwortet. `one_round` reicht
  Kandidaten zurueck und nicht den Grund, warum keine Vektoren dabei sind; der
  Handler fragt deshalb nur noch `warm_wanted()`.

- 14-08: Der Fall zur Antwortzeit laeuft bewusst **ohne** `TestClient`. Dessen
  Portal wird je Anfrage geoeffnet und beim Schliessen wartet es auf jede
  Aufgabe, die drinnen gestartet wurde; eine Messung um `client.post` herum
  meldet also die Laenge des Hintergrundlaufs, egal was der Handler tut. Unter
  uvicorn ueberlebt der Loop die Anfrage. Der Fall ruft den Handler deshalb
  direkt auf dem Loop des Testfalls.

- 14-08: `api/diagnose.py` bekommt nur einen Kommentar und keinen Schalter. Ein
  Messwerkzeug muss messen koennen, die Route traegt keine 1,5-Sekunden-Decke
  und ist keine Nutzerroute. Die Kehrseite (ein Diagnoseaufruf waermt den
  Container auf und darf vor einer Kaltmessung nicht gemacht werden) gehoert
  ins Runbook 14-11.

- 14-07 (MEM-02, der Aufrufer): Die Entladung bekommt einen eigenen Takt in der
  Lifespan und sitzt NICHT im Leerlaufzweig des Pollers. Ein stummgeschalteter
  Poller wartet in `run()` auf sein Armiert-Ereignis und betritt `run_once` nie
  wieder (`poller.py:543-545`), und genau dieser Container, der nicht indexiert
  und nur gelegentlich durchsucht wird, ist der Fall, fuer den die Entladung
  gebaut ist.

- 14-07: `release_cutter()` steht HINTER einer Freigabe, die `True` geliefert
  hat, und nicht daneben. `release_if_idle` traegt die Uhr und die
  Identitaetspruefung, `release_cutter` traegt keine eigene Frist; ein
  `release_cutter` ohne vorangegangene Freigabe wuerde den Cutter nach jeder
  Ruhephase wegwerfen, auch wenn die Suchseite gerade eingebettet hat.

- 14-07: Bei ausgeschaltetem Schalter gibt es keine Logzeile. Der Werksstand ist
  aus, und eine Zeile bei jedem Start ueber eine Funktion, die niemand
  eingeschaltet hat, ist Rauschen. Der Behavior-Block des Plans verlangte das
  Gegenteil, der begruendete Action-Block hat Vorrang bekommen; der Kommentar im
  Quelltext sagt, warum hier auch spaeter kein `else`-Zweig "zur Symmetrie" mit
  dem Reconcile-Block hingehoert (der Abgleich ist ab Werk AN, deshalb ist seine
  Aus-Zeile ihren Platz wert).

- 14-07: Direkt hinter `_pause` wird das Stopp-Event ein zweites Mal gelesen und
  der Takt abgebrochen. Ohne diesen Blick liefe im Herunterfahren noch ein
  vollstaendiger Takt, und ein dort gestarteter Warmlauf haelt den Prozessausgang
  sekundenlang in einem Threadpool-Thread fest (T-14-26). Das ist eine Zeile
  mehr, als der Plan vorsah, und sie ist es, die das Budget von 5,0 s haltbar
  macht.

- 14-06 (MEM-03, obere Haelfte): `query_may_load()` ist die eine Stelle, an der
  steht, ob eine Suche laden darf, und sie antwortet
  `settings().embed_idle_release_seconds == 0`. Die Degradation haengt damit am
  Schalter und gilt nicht generell: der Vorfall vom 10.09.2026 war die
  allererste Suche eines Containers, der nie entladen hatte, und eine Naht ohne
  Schalter wuerde ihn generell abstellen, waere aber eine Verhaltensaenderung
  ausserhalb des Schalters, und die eine Box-Anfahrt der Phase 15 wuerde zwei
  Aenderungen auf einmal messen. Der Generalfall ist Backlog. `api/diagnose.py`
  ruft die Funktion bewusst nicht und laedt weiter (ein Messwerkzeug muss messen
  koennen); die Kehrseite, dass ein Diagnoseaufruf den Container aufwaermt,
  gehoert ins Runbook 14-11.

- 14-06: `release_if_idle(ttl)` prueft die Identitaet des Halters unter `_LOCK`
  mit `is` und gibt erst danach frei, weil das Nachwaermen aus MEM-03 neben der
  Entlade-Aufgabe laeuft und eine Kollision sonst das gerade bezahlte Ladepaar
  wegwerfen wuerde (T-14-20). Der Auftrag aus 14-05 ist damit erledigt, und er
  ist in `engine.py` gelandet und nicht in `release()`: die Mechanik bleibt
  unten, die Politik steht oben. `release()` wird ausserhalb von `_LOCK`
  gerufen, weil Sammeln und Trimmen blockieren (T-14-16); drei Gates am
  Syntaxbaum halten Lage, `_held`-statt-`shared_model` und `is`-statt-Wert fest.

- 14-06: `ttl <= 0` und `last_use() is None` antworten beide `False`, ohne den
  Halter zu fragen. Null ist das Wort fuer aus und keine Frist von null
  Sekunden; `None` ist ein Halter, der geladen hat und nie eingebettet hat, und
  das ist kein Leerlauf, sondern nichts zum Loslassen (Uebergabe aus 14-05).

- 14-06: Die Zusage "genau ein Laden je warmem Fenster" ist strukturell erfuellt
  und nicht durch das Flag: `_load()` laeuft unter dem Lock des Halters und
  kehrt am Kopf zurueck. `_WARMING` spart die neun wartenden Threadpool-Threads
  und ist im Docstring ausdruecklich als Effizienz und nicht als Zusage
  benannt, damit niemand es spaeter fuer die Zusage haelt. Der Zehn-Threads-Fall
  misst den Zuwachs von `load_count()` und nie ein Byte.

- 14-06: `warm()` laedt ueber `shared_model().embed_query(WARM_TEXT)` und setzt
  damit die Leerlauf-Uhr mit. Das ist die Bedingung und kein Nebeneffekt: ohne
  die Uhr entlaedt der naechste Takt sofort wieder. `WARM_TEXT` ist eine feste
  Modulkonstante ohne Nutzerinhalt und ohne Dateinamen (T-14-22).

- 14-06 (Lehre, dritte Auflage): Der Baumhash musste erneut in jedem
  Produktcode-Commit nachgezogen werden, weil der Plan
  `tests/test_measurement_scripts.py` wieder nicht in `files_modified` fuehrt.
  Das ist jetzt der vierte Plan in Folge. Zusaetzlich neu: die beiden
  `<verify>`-Befehle des Plans (`pytest -k "may_load"` und
  `-k "release_if_idle"`) waehlten mit den urspruenglichen Testnamen keinen
  oder nur einen Fall aus; die Namen wurden nachgezogen. Ein Pruefbefehl, der
  nichts auswaehlt, ist ein gruenes Nichts.

- 14-05 (Suchseite): `release()` gibt unter `self._lock` los und zaehlt, ruft
  `gc.collect()` und `malloc_trim(0)` aber AUSSERHALB davon: beide blockieren,
  und ein gehaltenes Lock wuerde jede gleichzeitige Suche mitblockieren
  (T-14-16). Die Reihenfolge sammeln, dann trimmen ist nicht umkehrbar und wird
  zur Laufzeit und im Quelltext geprueft. Der Vorprueflauf hat die Aufteilung
  gemessen: `gc.collect()` allein 15,1 bis 18,2 Prozent, der Trim die uebrigen
  80,2 bis 84,9. Die Zahlen des Research-Beispiels (20 und 5 Prozent) stammen
  aus der Vorrecherche und sind durch den Lauf ueberholt.

- 14-05: Der Aktivitaetszaehler `_in_flight` steht im SELBEN Lock-Block, in dem
  die Engine gebunden wird, und nicht dahinter. Dazwischen laege ein Fenster,
  in dem eine Freigabe aus einem anderen Thread den Heap eines startenden
  Batches sammeln und trimmen duerfte. Das ist die einzige neue Invariante
  dieser Phase (T-14-15).

- 14-05: `may_load` sitzt an `embed_query` und `_embed` mit Vorgabe `True`,
  `embed_passages` bekommt den Schalter bewusst nicht: ueber einem Indexlauf
  steht keine 1,5-Sekunden-Decke, und nach einer Entladung ist die naechste
  Zeile des Laufs der richtige Moment zum Wiederladen. Die Regel, wann der
  Schalter falsch ist, liegt in 14-06; `model.py` liest keine Einstellung.

- 14-05: Keine Identitaetspruefung in `release()`. Sie wird gebraucht, sobald
  das Nachwaermen aus MEM-03 neben der Entlade-Aufgabe laeuft, also in 14-06
  oder 14-07. Heute kann kein Weg eine Engine laden, ohne im selben Lock-Block
  den Aktivitaetszaehler zu erhoehen. Als Auftrag an den naechsten Planer
  festgehalten, nicht als stillschweigende Auslassung.

- 14-04 (MEM-02, Indexseite): Der Poller bekommt ein oeffentliches Property
  `busy`, das `bool(self._held)` antwortet. Gehaltene Warteschlangenzeilen sind
  die einzige Groesse am Poller, die einen laufenden Durchgang bedeutet; sie
  werden auf allen Wegen geleert, auch im Abbruch und in `unlock_held`.
  `_idle_announced` ist dagegen ein Log-Merker, der in `arm()` zurueckgesetzt
  wird: ein Entlader, der ihn liest, entlaedt nach jedem Armieren einmal falsch
  (Leitplanke 3 der 14-CONTEXT.md). `armed` ist das Gegenteil der Frage,
  `cooldown` ist Warten und keine Arbeit. Alle drei stehen mit Begruendung im
  Docstring.

- 14-04: `release_cutter()` hat drei Antworten in dieser Reihenfolge: bei `busy`
  falsch und nichts angefasst (Pitfall 3, die Gewichte waeren Sekunden spaeter
  wieder da), bei leerem Paar falsch (es gab nichts loszulassen, der Zaehler des
  Aufrufers bleibt ehrlich), sonst beide Felder auf None und wahr. Die
  Arbeitsfrage steht vor der Bestandsfrage, weil ein falsches Ja fuer einen
  arbeitenden Container der Fehler ist, der nirgends rot wird.

- 14-04: Die Halbheit wird am Syntaxbaum ausgeschlossen, nicht an einem Lauf.
  `test_the_release_never_leaves_half_a_cutter_behind` liest `release_cutter`
  ueber `ast.walk` und verlangt, dass die Methode genau `_chunker` und `_model`
  zuweist. Damit ist zugleich das Gate gegen ein Zuruecksetzen von
  `_cutter_absent` und `_cutter_failed_at` gebaut (Pitfall 8), und es haelt auch
  gegen ein drittes Feld, an das heute niemand denkt.

- 14-04: `release_cutter` ruft keine Sammelrunde und keinen Trim, auch nicht im
  Kommentar: der Docstring umschreibt beide Begriffe, weil das
  Acceptance-Gate die Datei auf genau diese Zeichenketten absucht und sonst an
  der eigenen Erklaerung rot wuerde. Die Seitenrueckgabe liegt einmal je Takt in
  `embed/model.py` (14-05).

- 14-04: MEM-02 wird NICHT abgehakt, obwohl die Frontmatter des Plans sie nennt.
  Die Anforderung verlangt beide Speicherhalter und die Messgroesse "Rueckkehr
  zur Grundlast"; dieser Plan baut eine Haelfte und ruft sie nirgends auf. Das
  ist dieselbe Lage wie bei MEM-04 in 14-01, wo der Haken zurueckgenommen werden
  musste. MEM-02 faellt fruehestens mit 14-07.

- 14-04 (Lehre, zweite Auflage): Die Lehre aus 14-03 hat sich sofort wiederholt.
  Der Plan nannte `tests/test_measurement_scripts.py` erneut nicht und verbot
  ihre Aenderung sogar ausdruecklich (Verifikationspunkt 5). Der Baumhash wurde
  in beiden Produktcode-Commits nachgezogen. Die Plaene 14-05 bis 14-11 sollten
  die Datei in ihrer Dateiliste fuehren, statt sie zur Abweichung zu machen.

- 14-03 (MEM-01, Namensentscheid): Die Variable heisst
  **`FINDLING_EMBED_IDLE_RELEASE_SECONDS`** und nicht
  `FINDLING_EMBED_IDLE_SECONDS`. Begruendung aus dem eigenen Bestand: die 15
  bereits ausgelieferten Variablen der info.xml nennen alle Wirkung und nicht
  nur Bedingung, und eine einmal ausgelieferte Variable ist nicht mehr
  umbenennbar. Der Name steht in `config.py` und `appinfo/info.xml` byteweise
  gleich. Der Bereich heisst `EMBED_IDLE_RELEASE_SECONDS_RANGE` nach der
  Hausform der Datei; der Plantext nannte `EMBED_IDLE_RELEASE_RANGE` und
  widersprach damit seinem eigenen Acceptance-Kriterium.

- 14-03: Die Null bekommt einen eigenen Leser
  `_seconds_or_off_from_environment`, den dritten dieser Bauart nach
  `_hour_from_environment` und `_overlap_from_environment`.
  `_bounded_int_from_environment` waere aus beiden Richtungen falsch: mit
  `(0, 86400)` waere eine TTL von drei Sekunden gueltig, mit `(60, 86400)`
  fiele die Null auf den Default zurueck und ein Admin, der abschalten will,
  bekaeme die Funktion, ohne Fehlermeldung. Die Null wird deshalb VOR der
  Bereichspruefung beantwortet, und der Bereich behaelt seine Untergrenze 60.

- 14-03: Der Unterschied zwischen "aus" und "Tippfehler" ist durch eine
  Mutationsprobe abgenommen und nicht nur durch einen Docstring behauptet: der
  Aufruf wurde probeweise gegen `_bounded_int_from_environment` getauscht, genau
  ein Fall wurde rot, und es war der Null-Fall. Danach zurueckgenommen, alle 14
  Faelle wieder gruen.

- 14-03: Ab Werk 0, also aus, und der Kommentar nennt beide Gruende mitsamt
  ihrem Ablaufdatum: die eine bezahlte Box-Anfahrt der Phase 15 muss das Merkmal
  gegen seine eigene Abwesenheit wiegen und braucht beide Stellungen, und ein
  Merkmal mit ungemessenen Wiederaufwaerm-Kosten darf sich unter einer laufenden
  Installation nicht selbst einschalten. 900 s ist der Vorschlagswert der
  info.xml und bis zur Messung geraten.

- 14-03: `FINDLING_EMBED_ENABLED` wurde NICHT in die info.xml aufgenommen. Es ist
  ein Haertungskandidat und kein Requirement dieser Phase, und eine ausgelieferte
  Variable mehr in einem Release, das sie nicht braucht, ist Umfang ohne Anlass.
  Der Befund steht als Kommentar in der Datei, damit Phase 16 ihn findet.

- 14-03 (Lehre): Jede Aenderung an `backend/src/findling/` zieht
  `PACKAGE_TREE_HASH_TODAY` in `tests/test_measurement_scripts.py` nach. Der
  Plan kannte die Datei nicht; sie gehoert ab jetzt in die Dateiliste jedes
  Plans, der das Python-Paket anfasst. Die historische Zahl `PACKAGE_TREE_HASH`
  aus den Rohdaten bleibt dabei unberuehrt.

- 14-02 (OWNER-ENTSCHEID 19.09.2026): Der Owner hat den Ausgang des
  Vorprueflaufs im Wortlaut mit "freigegeben" genannt, ohne Auflage. Damit sind
  14-03 bis 14-12 frei und der Bau der Entladefunktion darf beginnen. Der Satz
  "gemessen, Ergebnis negativ" ist nicht eingetreten.

- 14-02: Der Vorprueflauf ist gefahren und das Tor der Phase ist offen.
  Gemessen wurde am
  19.09.2026 im Lauf 35443822228 auf `ubuntu-24.04-arm` (role target, aarch64,
  Neoverse-N2, vier Kerne) gegen das ausgelieferte Abbild
  `sha256:31c905b212d815d9ba5deea29a44b90bd8564baa3c4a5bd48ea13876ef31e538`.
  Ergebnis: Median der Rueckgabe **100,0 Prozent** (schlechtester Einzelzyklus
  98,4), `trim_rc` in fuenf von fuenf Zyklen 1, `after_gc` mindestens 856,9 MB
  ueber `after_trim`, Zyklus 5 gegen Zyklus 1 minus 1,5 Punkte. E1, E2, E3 und
  E4 sind alle gehalten; der Ausgang des Ablaufdokuments heisst "Gehalten".

- 14-02: MEM-04 ist erfuellt und abgehakt. Anders als in 14-01, wo der Haken
  zurueckgenommen wurde, liegt die Zahl jetzt vor: auf Zielarchitektur, nativ,
  gegen das ausgelieferte Abbild, mit der Maschine daneben.

- 14-02: Ein Bodensatz bleibt und gehoert in den Store-Text. Die Entladung
  fuehrt auf die Grundlast plus rund 16 MB (Zielast 17,1 MB ueber fuenf Zyklen,
  davon 15,9 MB im ersten), weil die Modulimporte von onnxruntime und numpy
  geladen bleiben. Eine Zusage "gibt den Modellspeicher vollstaendig zurueck"
  waere falsch.

- 14-02: Der Vergleichsast x86_64 liefert dieselbe Quote (Median 100,0, gleicher
  Zyklus-1-gegen-5-Abstand). Uebertragbar ist die Rueckgabequote, die Zeit nicht:
  dieser Lauf hat keine Zeit gemessen, und beide Runner sind Vier-Kern-Maschinen
  derselben Flotte und keine m7g.large.

- 14-01: Die Schwelle des Vorprueflaufs steht VOR dem Lauf: E1 verlangt einen
  Median der Rueckgabe von mindestens 60 Prozent auf dem `role: target`-Ast,
  hergeleitet aus 97,2 Prozent nativ x86_64 und 71,4 Prozent unter qemu. Dazu
  E2 (`trim_rc` in vier von fuenf Zyklen 1), E3 (`after_gc` deutlich ueber
  `after_trim`) und E4 (Zyklus 5 hoechstens 10 Punkte unter Zyklus 1). Drei
  Ausgaenge sind benannt, darunter "gemessen, Ergebnis negativ".

- 14-01: Der Vorprueflauf ist ein eingehaengtes Messskript und KEIN vierter
  Modus von `findling.embed.bench`. Ein neuer Bench-Modus stuende erst nach
  einem Push auf main und einem gruenen docker.yml im ausgelieferten Abbild;
  der Vorprueflauf muss aber gegen das ausgelieferte Abbild laufen, bevor
  Produktcode entsteht. Der neue Workflow-Schritt heisst E, weil D die
  Grundlast ist und unter diesem Buchstaben bereits zitiert wird.

- 14-01 (Lehre, Regel 1): Der Zustandsbefehl hat MEM-04 abgehakt, weil die
  Frontmatter des Plans die Anforderung nennt. MEM-04 verlangt aber den Beleg
  auf Zielhardware, und dieser Plan erhebt keine Zahl. Der Haken ist
  zurueckgenommen; MEM-04 faellt in 14-02. Eine Anforderung gehoert an den
  Plan, der sie belegt, nicht an den, der ihr Werkzeug baut.

- 13-12 (gehoert in den Checkpoint 13-13): Das dritte Paritaetsszenario ist in
  der geplanten Form nicht ausdrueckbar. `ask()` fragt die beiden OCS-Provider,
  und keiner von beiden kennt `types` oder `sort`; nur `ask_page` traegt die
  Parameter. Unter einem wegnehmenden Filter meldet `compare_page` daher zu
  Recht `page-missing`. Statt dem Vergleichswerkzeug eine Ausnahme beizubringen
  (das haette seine Schaerfe gekostet) wird die Wegnahme daneben gemessen. Teils
  staerker als geplant, weil sie belegt statt erwartet wird; teils schwaecher,
  weil die extra-Richtung unter dem Filter ueber leeren Mengen steht. Wer das
  schaerfer will, braucht ein Fixture mit einer Bilddatei.

- 13-11: Die franzoesischen Wortlaute der 23 neuen Schluessel sind NICHT
  muttersprachlich geprueft. docs/l10n-french.md war am 11.09. vom Owner
  abgenommen; ein datierter Nachtrag im Abschnitt Abnahme sagt jetzt ausdruecklich,
  dass die neuen Zeilen ungeprueft sind, damit eine abgenommene Datei keine
  ungelesenen Zeilen stillschweigend mittraegt. OFFEN fuer den Owner.

- 13-11 (Lehre): Der erste Einfuegelauf schrieb die Katalogeintraege ohne
  Trennkommas. Klammerbilanz und Diff-Durchsicht haetten das nicht gefunden, der
  JSON-Parser meldete es sofort. Die Parser-Pruefung bleibt Pflichtschritt.

- 13-10 (Planfehler, nicht Umsetzungsfehler): Der verify-Block wollte `grep -c '@media'
  == 2`, die Datei traegt aber seit Phase 9 vier Media Queries; der Plan hatte die zwei
  aus seinem eigenen interfaces-Abschnitt gezaehlt. Die pruefbare Absicht "keine neue
  Media Query" ist eingehalten, die Zahl steht vor und nach dem Plan bei 4.

- 13-10: Das Gate gegen ein Zaehl-Orakel sucht die Woerter des Zaehlens (`count`,
  `total`, `badge`, `disabled`, `$l->n(`) statt einer Ziffernausgabe, weil "Last 7 days"
  und "Last 30 days" selbst Ziffern tragen und ein Ziffern-Gate am ersten Tag rot
  gewesen waere.

- 13-10: Die Region der Leiste wird am Kommentar-Oeffner geschnitten und Blockkommentare
  werden vor dem Scan entfernt, sonst waere das Gate an genau dem Kommentar rot
  geworden, der erklaert, warum es keinen Zaehler gibt. Dieselbe Falle wie bei
  `aria-current` in 13-09.

- 13-09 (Scope-Erweiterung, Rule 3): Das Formular braucht `since` und `until` als
  versteckte Felder, 13-08 uebergibt dem Template aber keine Zeitgrenze und keine
  rohen Adresswerte, nur fertige Chips, Links und Flags. Neu ist deshalb
  `PageController::formFilters()`, die `filterArguments()` nimmt und `query` plus
  `names` entfernt; sie erbt damit drei Eigenschaften, statt sie einzeln zuzusichern.
  Die Alternative, aus den aktiven Chips zurueckzurechnen, waere genau die zweite
  Auslegung des Adresszustands gewesen, die diese Phase verbietet.

- 13-09: Der Kommentar zur Begruendung von `aria-current` nennt die verbotene
  Alternativauszeichnung nicht beim Namen, weil der Pruefblock und das kommende Gate
  aus 13-10 die Datei genau auf diese Zeichenkette absuchen; ein woertlicher
  Kommentar haette das eigene Gate rot gemacht.

- 13-08: Der Fingerabdruck des Cursorpfads laeuft ueber die ROHEN Adresswerte `range`
  und `since`, nicht ueber die daraus errechnete wirksame Untergrenze. Mit der
  wirksamen Grenze wechselte er um Mitternacht und wuerfe jeden Blaetternden ohne
  sichtbaren Grund auf Seite 1.

- 13-08: Die acht Cursorfaelle der Tests binden ihre Adresse ueber einen Helfer
  `bound()` an den von der Seite selbst berechneten Fingerabdruck. Der Plan wollte
  sie unveraendert gruen, was mit der Bindung unvereinbar war: `filterUrl()` schreibt
  nie ein `fp`, ein toleriertes Fehlen haette die Bindung genau im Zielfall
  wirkungslos gemacht.

- 13-06/13-07 (Merge): Beide Plaene zogen auf ihrem eigenen Branch den Baumhash der
  PHP-Haelfte nach, jeder gegen einen Baum mit nur seiner eigenen Aenderung. Der Hash
  laeuft ueber die ganze Haelfte, also ist der gemergte Baum ein dritter Baum mit einem
  dritten Hash; er wurde nach dem Merge mit demselben Rezept neu gelesen
  (6166e963..., weiterhin 64 Dateien). Beide Begruendungsabsaetze bleiben stehen.

- 13-06: `getSupportedFilters()` meldet vier Namen. Ein nicht deklarierter exklusiver
  Filter kostet die ganze Ergebnisgruppe, entweder weil die Oberflaeche den Provider
  gar nicht erst fragt oder weil seine Gruppe in einem 400 endet; fuer den Nutzer sah
  beides gleich aus, Findling war weg, sobald ein Datum gesetzt war (FILT-03).

- 13-07: Die vier Schnellbereiche sind Kalenderfenster in der Zeitzone des Nutzers,
  nicht in der des Servers. Die Tagesarithmetik laeuft ueber `DateInterval`, und die
  zwei Faelle zur engeren Grenze meiden das Paar "dieses Jahr"/"gestern", das am

  1. Januar rot waere.

- 13-05: `SearchService::run` nimmt die Filter als sechsten Parameter, hinter
  `SearchCaps` und ohne Vorgabewert, und reicht dasselbe Objekt an beide
  Containeraufrufe weiter. Der Filter wird auf der PHP-Seite kein zweites Mal
  angewendet: das würde aus jeder Seite eine Stichprobe machen und eine zweite
  Stelle an der Rechtegrenze eröffnen (T-13-23).

- 13-05: Das Änderungsdatum eines Treffers kommt aus `$node->getMTime()` am
  bereits bestätigten Knoten, gelesen hinter der Typprüfung und hinter der
  Leseprüfung. Der Kandidat des Containers trägt zwar ein eigenes `mtime`,
  `filterCandidates()` verwirft es weiterhin, und ein Testfall mit zwei
  absichtlich verschiedenen Zahlen belegt, welcher Wert gewinnt (T-13-22).

- 13-05: `ApprovedHit` trägt fünf Felder; für den Kanarienvogel (`fileId` 0)
  bleibt `mtime` bei 0, weil es dort keinen Knoten gibt. Das Feld ist ein
  Pflichtargument geblieben, damit ein vergessener Aufrufer nicht wie einer
  ohne Datum aussieht.

- 13-05: Die Rechtegrenze ist in Zahl, Reihenfolge und Ort unverändert;
  `test_php_acl_boundary.py` und `test_php_trust_boundary.py` sind grün.

- 13-04: Filter und Sortierung reisen durch die PHP-Haelfte als EIN benanntes
  Wertobjekt `SearchFilters` (`types`, `sort`, `since`, `until`), nach der
  Bauform von `SearchCaps`. Abweichung von jenem Vorbild: es gibt eine statische
  `none()`, weil "nichts eingegrenzt" ein benannter Zustand des Produkts ist und
  keine Zahl, ueber die niemand mehr nachdenkt. Die Begruendung steht im
  Klassen-Docstring.

- 13-04: Das neue Argument steht VOR den beiden Uhrwerten und nicht am Ende der
  Parameterliste, wie der Plantext es vorsah. Beide Uhrwerte tragen einen
  Vorgabewert, und ein Pflichtargument hinter einem optionalen ist seit PHP 8.0
  abgekuendigt. Ohne Vorgabewert bleibt es trotzdem: ein vergessener Aufrufer
  soll nicht aussehen wie einer ohne Filter.

- 13-04: `typeGroupsWithin` laeuft ueber die geschlossene Sechser-Menge und
  nicht ueber die Eingabe. Unbekannter Name, Dublette, Ueberlaenge und
  Reihenfolge sind damit baulich erledigt (T-13-17, T-13-18) statt in vier
  Pruefungen, die einzeln vergessen werden koennen.

- 13-04: Ein Wert in seiner Vorgabe wird nicht in den Rumpf geschrieben. Eine
  ungefilterte Suche schickt damit byteweise die Anfrage von vor dieser Phase,
  und ein echter Wert geht nicht zwischen vier Konstanten unter.

- 13-04: Der `/snippets`-Rumpf traegt `types`, `since` und `until` und an keiner
  Stelle den Sortiermodus (FILT-02). Die Reihenfolge dieser Treffer steht fest,
  bevor der Aufruf gestellt wird.

- 13-04: `filterCandidates()` bleibt unangetastet und laesst weiterhin nur
  `fileId` durch; der Docstring sagt jetzt ausdruecklich, dass das
  Aenderungsdatum aus dem bestaetigten Knoten kommt (13-05) und nie aus der
  Container-Antwort (T-13-20).

- 13-04: `php -l` ist auf dieser Maschine doch moeglich, ueber das offizielle
  Docker-Image `php:8.2-cli` (dieselbe Version wie der Lint-Job in CI). PHPUnit
  bleibt CI-only, weil die Suite eine Auscheckung von nextcloud/server braucht.

- 13-03: Die vier neuen Werte reisen als geschlossene Mengen. `types` ist
  `list[Literal[...]]` ueber die sechs Gruppennamen, `sort` ein `Literal` ueber
  die drei Sortiernamen, `since` und `until` sind `int` mit `ge=0` und
  `le=SEARCH_MTIME_MAX`. Kein Freitext: die Routen tragen `access_level USER`,
  und ein freier String waere ein zweiter Weg in den Abfragebau.

- 13-03: `SEARCH_TYPE_GROUPS_MAX = 6` und `SEARCH_MTIME_MAX = 4_102_444_800`
  (01.01.2100) stehen in `config.py`, je mit Begruendungsabsatz nach dem Muster
  von `SEARCH_OFFSET_MAX`.

- 13-03: Der Sortierterm haengt an derselben `lexical_only`-Zeile und nicht an
  einer zweiten Weiche: `... or sort != "relevance"`. Unter Sortierung gibt es
  keine Fusion, in die eine Vektorliste eingehen koennte.

- 13-03: `sort` steht NICHT in `SnippetsRequest`, und ein `sort` im
  Ausschnitts-Rumpf ist ein 422. Die Ausnahme ist im Gate
  `backend/tests/test_search_fields_lockstep.py` benannt, nicht gezaehlt.

- 13-03: `FIELDS_THAT_MAY_DIFFER` traegt vier Eintraege statt des einen aus dem
  Plantext, weil `limit`, `offset` und `fileIds` schon vor der Phase einseitig
  waren. Jeder Eintrag traegt seine Begruendung; eine Liste und keine Schwelle.

- 13-03: Der Ausschnittsaufruf SCHNEIDET NICHT. `snippets_for` laeuft ueber die
  bestaetigten Kennungen und waehlt keine Dokumente aus; die Filterklausel nennt
  `ext` und `mtime` und markiert im Textfeld nichts. Die drei Felder stehen am
  Modell, damit ein Rumpf beide Modelle passiert (`extra="forbid"` -> 422 -> auf
  der PHP-Seite `null` -> Fehlerblock statt Ausschnitten).

- 13-03: Die Diagnoseroute bekommt die drei Filter als Query-Parameter, aber
  keine Trefferzahl je Typ und keinen Gesamtwert. Ihre Grenze steht im
  Docstring: `ranked_sides` geht nicht durch `_mtimes_of`, sie sieht den Schnitt
  der semantischen Haelfte also nicht.

- 13-03: Der Container lehnt einen unbekannten Gruppen- oder Sortiernamen mit
  422 ab, weil ihn nur die eigene Oberflaeche ruft. Der stille Rueckfall bei
  einer von Hand editierten Adresse ist Aufgabe der PHP-Seite.

- 13-02: Die Sortierung ist ein eigener, rein lexikalischer Zweig
  (`_sorted_round` in `index/search.py`) ohne RRF und ohne Vektorhaelfte, und
  jeder Treffer traegt `score = 0.0`. Unter `order_by_field` liefert tantivy im
  ersten Tupelglied den Feldwert statt des Scores; ein uebernommener Feldwert
  waere ein Zeitstempel als Relevanz.

- 13-02: Der Zweitschluessel `file_id` ist Handarbeit und wird portionsweise
  hergestellt. Gemessen und in diesem Plan nachgestellt: bei gleichem
  Zeitstempel und Einfuegereihenfolge 7, 3, 9, 1 antwortet tantivy 7, 3, 9, 1.
  Eine Gleichstandsgruppe, die an einer Portionsgrenze zerfaellt, ist
  portionsweise sortiert; Duplikate oder Luecken entstehen dabei nicht.

- 13-02: Ein unbekannter Wert in `sort` faellt still auf `relevance` zurueck
  (`SORT_MODES.get`). Die Route prueft bereits am Wire-Modell; eine zweite
  Ausnahme wuerde aus einem Tippfehler in einer Adresse einen HTTP 500 machen.

- 13-02: Dieselbe Filterklausel wirkt jetzt an beiden Stellen. `_mtimes_of`
  nimmt sie als `Occur.Must` ueber die `file_id`-Klauseln; was dort
  herausfaellt, fehlt in `known` und verschwindet aus `merged`. Ohne diese
  zweite Stelle stehen unter dem Chip "PDF" docx-Treffer der semantischen
  Haelfte.

- 13-02: `VECTOR_SCAN_MAX` wird nicht angehoben. Die semantische Haelfte
  schrumpft unter einem engen Filter sichtbar, weil die Chunks VOR dem
  Typschnitt gezogen werden; das ist eine Eigenschaft und kein Defekt.

- 13-02: `semantic` ist im Sortierzweig wirkungslos statt verboten. Die
  Abschaltung durch den Aufrufer folgt in 13-03; die Wirkungslosigkeit hier ist
  die zweite, defensive Haelfte derselben Zusage.

- 13-01: `TYPE_GROUPS` in `query/rewrite.py` ist die einzige Abbildung von
  Gruppe auf Endung im ganzen Projekt, und die bestehende `type:`-Textsyntax
  wurde an dieselbe Tabelle angeschlossen: `type:images` bedeutet ab jetzt
  dasselbe wie der Chip. Ein Wort, das die Tabelle nicht kennt, bleibt wie
  bisher eine rohe Endung.

- 13-01: Textendungen und Gruppenendungen werden vereinigt und nicht
  geschnitten. `type:pdf` plus Chip "Bilder" wäre als Schnittmenge garantiert
  leer, und die Seite könnte das niemandem erklären.

- 13-01: Der strukturierte Gruppenparameter setzt die Operator-Marke
  `FILETYPE` nie; sie hängt ausschließlich am Text `type:`. Genau daran hängt
  FILT-01, und ein eigener Testfall hält es fest.

- 13-01: Die Bereichsabfrage auf `mtime` läuft über die Fast-Spalte,
  `use_inverted_index` bleibt beim Vorgabewert `False`. Mit `True` antwortet
  tantivy 0.26.0 mit einer leeren Trefferliste statt mit einem Fehler, was auf
  der Seite wie "in diesem Zeitraum gibt es nichts" aussieht.

- 13-01: Die Filterklausel liegt zusätzlich als `RewrittenQuery.filter_query`
  bereit, damit Plan 13-02 dieselbe Klausel auf die semantische Hälfte legen
  kann (`index/search.py::_mtimes_of`); ein Filter nur in `query` ließe
  typfremde Vektortreffer durch.

- 12-02: Zweig a greift: v35.0.0 vom 15.09.2026 ist die erste 35er-Marke ohne
  Prerelease-Kennzeichen (prerelease=false UND draft=false, am 16.09. live
  gelesen). Nach D-02 trug der Release-Status allein nicht; der Beweislauf
  35095805558 lief am 16.09. auf dem Baum des Stichtags mit allen vier
  Matrixaesten gruen, ERST DANACH fiel `tolerate-failure` (Owner-Freigabe am
  Checkpoint, Variante 1). Der stable35-Ast von deploy-harp ist ab jetzt
  muss-gruen; ein roter Lauf ist ein Befund und kein Grund, das Flag
  zurueckzudrehen. Beide info.xml blieben unberuehrt (Fenster steht auf
  33 bis 35, D-01).

- 12-08: Das Runbook ist vollstaendig. Abschnitt 6 macht fuenf
  Vergleichbarkeitsgroessen protokollpflichtig (Zeilenstaende 52.111/37/0,
  Cron-Intervall 300 s, m7g.large mit `2147483648`, Zeit seit dem letzten
  Containerstart, Werkzeugstand als Baumhash), Abschnitt 7 gibt jedem der neun
  Messschritte seinen Abbruchpfad und fuehrt alle zwoelf Rueckgabewerte,
  Abschnitt 8 baut in neun Schritten ab (Endmessungen und Historie VOR jedem
  zerstoerenden Schritt, `FINDLING_STATE_BACKUP` vor `destroy`, Tag-Sweep ueber
  `findling-phase5` UND `findling-corpus-keep` danach), Abschnitt 9 fuehrt die
  Kosten ueber `box.env` und schliesst den Kreis zum Deckel-Rechenblatt (D-05).

- 12-08: Waehrend der bezahlten Anfahrt wird kein Werkzeug mehr geaendert. Ein
  Skript, das waehrend seines eigenen Laufs nachgebessert wird, macht jede Zahl
  daneben unbelegt; der Werkzeugstand steht als Baumhash unter den
  protokollpflichtigen Groessen.

- 12-08: MESS-04 und MESS-06 sind erfuellt und abgehakt. Beide sind als
  Werkzeug- und Runbook-Anforderungen formuliert und liegen damit vollstaendig
  in Phase 12; die Anwendung im gefahrenen Messlauf zaehlt in Phase 15 unter
  MESS-05. HART-03 bleibt offen bis zum Vollzug durch 12-02 am 16.09.

- 12-03: `aws_box.sh restore` nimmt die Snapshotkennung aus dem Argument, sonst
  aus `CORPUS_SNAPSHOT_ID` in `box.env`, sonst aus der gepinnten Konstante
  `CORPUS_SNAPSHOT_DEFAULT`. Gesucht wird sie nie.

- 12-03: Ein aus dem Snapshot erzeugtes Volume wird pflichtmaessig auf
  `purpose=findling-phase5` umgetaggt, mit `describe-tags`-Rueckleseprobe und
  Abbruch, solange der geerbte Keep-Tag noch haengt.

- 12-03: `restore` endet beim Anhaengen; das Mounten bleibt ein Runbook-Block.
- 12-03: Annahme A3 ist lesend bestaetigt (Snapshot completed, 100 Prozent,
  60 GB, Tag `purpose=findling-corpus-keep`), Beleg in
  `docs/measurements/2026-09-v12-messung/rohdaten/01-aws-lesende-proben.txt`.

- 12-04: Die Fremdbestandszahl entsteht als
  `searcher.search(query, 1, count=True).count` im Prozess des Containers. Keine
  Route, keine Zahl ueber eine Prozessgrenze, kein Produktionscode angefasst; das
  Zaehl-Orakel aus T-02-93 entsteht gar nicht erst.

- 12-04: Nichtmessbarkeit wird am Rang der eigenen Datei entschieden (in BEIDEN
  Ranglisten fehlend oder schlechter als 64). Bestand und Fensterbelegung stehen
  erklaerend daneben und sind nicht das Urteil.

- 12-04: `NARROW_SCOPE_DIRS` traegt drei Laufverzeichnisse, `98b-sprachfaelle.sh`
  bekommt einen eigenen sha256-Waechter, und `docs/measurements/**` steht in
  beiden Pfadlisten von `python.yml`.

- 12-05: Das Urteil der Sprachfaelle haengt am kleineren der beiden Raenge der
  eigenen Datei gegen die Schwelle 64. Ein Wort statt einer Zahl (`ausserhalb`,
  `keine-kennung`) gilt als ausserhalb und wird nie gegen die Schwelle
  gerechnet.

- 12-05: Die eigenen Datei-Kennungen kommen aus dem Antwortkopf `OC-FileId` des
  Uploads (ohne zweite Abfrage) und reisen ausschliesslich in der Umgebung
  (`DATEI_IDS`), nie in einem Argument.

- 12-07: Der Deckel-Vorschlag fuer Phase 15 wird neu gerechnet statt uebernommen:
  acht Zeitposten, Volllauf mit dem gemessenen Planwert 26 h 37 min und ohne
  Vorwegnahme einer Top-up-Verbesserung, plus 15 Prozent Zuschlag. Ergebnis
  **42 h und 4,90 USD netto**, ausgewiesene Untergrenze 31 h und 3,59 USD. Die
  Freigabe faellt am Phase-15-Checkpoint, nicht im Runbook.

- 12-07: Das Runbook nennt Pfade und Variablennamen, nie Werte. Die
  Snapshotkennung bleibt im Klartext (steht bereits committet, ohne Konto
  nutzlos); Adressen, Instanz- und Volumekennungen stehen als Platzhalter mit
  einem Satz, woher der Wert kommt. Die CIDR-Schreibweise fuer das ganze
  Internet ist deshalb `<ganzes-netz>`.

- 12-07: Abschnittsueberschriften des Runbooks stehen bewusst ohne Umlaute, weil
  Pruefungen und Verweise auf sie zeigen; der Fliesstext traegt echte Umlaute,
  und der Kopf der Datei sagt das. Das Wort "Archiv" kommt in der Datei nicht
  vor (Vokabular-Gate, `docs/` ist oeffentlich).

- 12-06: Das Cron-Intervall ist ab jetzt eine im Skript durchgesetzte
  Messbedingung. `97-cron-vorpruefung.sh` hat zwei Zweige: `vorher` liest den
  Takt aus drei Quellen der Reihe nach und schreibt die Pflichtzeile
  `cron-intervall-ist` (Abbruch 25, wenn keine Quelle antwortet, 26 bei mehr als
  zehn Prozent Abweichung vom Soll 300 s), `waehrend` misst den tatsaechlichen
  Scheibenabstand (Abbruch 27 ohne Zahl, 28 ueber dem Deckel 420 s). Ein reiner
  Konfigurationscheck haette am 10.09.2026 gruen gemeldet, waehrend der Befund
  vorlag (D-07, D-08).

- 12-06: Die Ablesereihe des Wirkungszweiges laeuft mit 120 s und nennt ihr
  Intervall als Pflichtzeile. In v1.1 haben zwei Reihen (194 von 812 gegen 62
  von 325 Lesungen) rund 24 gegen 19 Prozent fuer denselben Sachverhalt
  ergeben; die Zuordnung der Reihen zu den beiden Beobachtern ist Annahme A1 und
  ausdruecklich nicht gesichert.

- 12-06: Der Exit-Code-Katalog des v1.2-Laufverzeichnisses steht bei 28; 12-08
  und Phase 15 setzen bei 29 fort. Der Ablaufplan `00-ablauf.md` schreibt die
  Erwartung E1 bis E7 vor der Anfahrt auf und wird danach nicht mehr angepasst.

- 12-05: `rang-erhoben ja` steht erst nach einem erfolgreichen zweiten
  Sondenlauf. Beide Ursachen (keine Kennung, keine Sonde) enden mit Exit 24
  unter der `tee`-Pipeline. Der Exit-Code-Katalog steht damit bei 24; 12-06
  setzt bei 25 fort.

## Milestone-Reihenfolge v1.2

| Phase | Inhalt | Requirements |
|-------|--------|--------------|
| 12 | Messwerkzeug, Runbook und Terminentscheid (ohne Box) | MESS-04, MESS-06, HART-03 |
| 13 | Filter und Sortierung auf der Ergebnisseite (Backend vor PHP) | FILT-01..05 |
| 14 | Modell-Entladung im Leerlauf (Schalter ab Werk aus) | MEM-01..05 |
| 15 | Messphase, eine Box-Anfahrt | MESS-05 |
| 16 | Haertung und Store-Einreichung v1.2.0 | HART-01, HART-02, REL-02 |

Harte Abhaengigkeiten: 12 vor 15, Backend vor PHP innerhalb 13, 14 vor 15, 16 zuletzt.

## Termine und Owner-Checkpoints

- **16.09.2026**: stable35-Fenster-Entscheid (HART-03, Entscheid v2-a), verankert in Phase 12.
  Beide Zweige sind seit 14.09. fertig ausformuliert in
  `.planning/phases/12-messwerkzeug-runbook-und-terminentscheid/12-STABLE35-ENTSCHEID.md`
  (Plan 12-01); am Stichtag vollzieht Plan 12-02 nur noch nach der dortigen
  siebenschrittigen Checkliste. HART-03 ist erst nach diesem Vollzug erfuellt.

- **Vor der Box-Anfahrt**: neu gerechneter Zeit-/Kostendeckel vom Owner freigegeben (MESS-05, Phase 15); das Rechenblatt steht seit 14.09. in `docs/runbook-messbox.md` Abschnitt 2 und kommt auf **42 h / 4,90 USD netto**, Untergrenze 31 h / rund 3,59 USD. Der 26-h-Vorschlag reisst rechnerisch
- **Vor dem Bau des Zustandsteils**: engineState-Wortwahl `cold` vs sechstes Wort `unloaded` (MEM-05, Phase 14)
- **Vor dem Bau der Entladung**: Vorprueflauf zur tatsaechlichen RSS-Rueckgabe auf Zielhardware (MEM-04, Phase 14) , ERLEDIGT 19.09.2026, Median 100,0 Prozent auf aarch64, Owner-Entscheid "freigegeben"

## Nach v1.2 (Wiedervorlage)

- Snapshot-Wiedervorlage snap-03f1d1d9ad9262704 (loeschen oder Archive-Tier, rund 2,9 USD/Monat)
- Aufraeumbefunde aus der Recherche: fastembed gepinnt aber nicht importiert, numpy als indirekte Abhaengigkeit
- Systemplatten-Skripte Phasen 5-6.1: Repo-Aufnahme erst nach Geheimnis-Durchsicht

## Offene Blocker

- Kill-Kriterium aktiv: kuendigt Nextcloud auf der Conference im September eine
  Elasticsearch-freie Volltextsuche mit OCR an, wird das Projekt neu bewertet

## Deferred Items

Items acknowledged and deferred at milestone close on 2026-09-11:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| debug | kill-resume-di-05-36-red | investigating | 2026-09-11 |
| debug | parity-login-probe-404 | verifying | 2026-09-11 |
| debug | store-install-5-routes-probe | verifying | 2026-09-11 |

Einordnung: alle drei Debug-Sessions gehoeren zu CI-Befunden, deren Fixe laengst
gemerged und gruen sind (parity-login-probe-404: Fix d604880, Probe fragt
/index.php/apps/findling/; store-install-5-routes-probe: Step auf
oc_ex_apps_routes umgebaut; kill-resume-di-05-36-red: DI-05-36 lief in Phase 10/11
gruen durch). Nur der Session-Status wurde nie auf resolved gesetzt.

## Session Continuity

Last session: 2026-09-19T20:05:00.000Z
Stopped at: Completed 15-01-PLAN.md, elf byteweise uebernommene Messwerkzeuge im Laufverzeichnis der Anfahrt, Kopie-Waechter gruen
Resume file: None
