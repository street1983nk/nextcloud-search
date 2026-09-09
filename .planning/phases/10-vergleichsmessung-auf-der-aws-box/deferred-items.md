# Deferred items, Phase 10

Befunde, die waehrend der Ausfuehrung dieser Phase aufgefallen sind und
ausserhalb des Plans lagen, in dem sie aufgefallen sind. Kein Fix hier, nur der
Befund und der Ort, an den er gehoert.

Klein heisst in dieser Phase: keine Aenderung an einem Messskript, gegen dessen
Ausgabe schon eine Rohdatei im Repo liegt, keine Aenderung am Messweg waehrend
eines laufenden Vergleichs, hoechstens eine Konstante oder ein Kommentar, und
der Fix passt in denselben Lauf, in dem er gefunden wurde.

---

## DI-10-01 (gefunden in Plan 10-02, Task 1): der Prosa-Ast der Kaltmessung mountet ein Verzeichnis, das es nicht mehr gibt

**Gefunden:** beim Sichten der Artefakte des ersten `workflow_dispatch` von
`measure.yml` (Lauf 34325000302), waehrend die arm64-Rohdatei der Feinmessung
uebernommen wurde.

**Was:** Im Schritt "A, characters per token" von
`.github/workflows/measure.yml` mountet der zweite von drei Aufrufen
`${GITHUB_WORKSPACE}/.planning/phases/06-semantische-suche` nach `/prose:ro`.
Dieses Verzeichnis existiert nicht mehr: die Phasen des Meilensteins v1.0 liegen
seit dem Umbau der Planungsablage unter
`.planning/milestones/v1.0-phases/`. Docker legt fuer einen fehlenden Quellpfad
ein leeres Verzeichnis an, das Werkzeug findet null Dateien und schreibt eine
leere Ausgabe, und der Schritt bleibt **gruen**. Ergebnis in beiden Matrixaesten:
`chars-per-token-prose.txt` mit 0 Byte, waehrend `chars-per-token-corpus.txt`
und `chars-per-token-wordlist.txt` gefuellt sind.

Damit fehlt genau der mittlere der drei Messpunkte. Der Kommentar des Schritts
sagt ausdruecklich, die Wahrheit fuer einen echten Bestand liege **zwischen**
der Prosa- und der Wortlistenzahl; ohne die Prosazahl ist das Intervall offen.

**Warum nicht hier behoben:** Der Befund gehoert nicht zu MESS-01. Die
Zeichen-je-Token-Messung ist eine Zahl der Phase 6 und steht in deren Bericht;
dieser Plan hat die Grundlast nachgeholt und darf den Messweg, gegen den die
Welle 5 lauefen soll, nicht waehrend der Phase umbauen. Ausserdem ist die
Entscheidung nicht klein: welches Verzeichnis an die Stelle tritt, entscheidet,
welche Prosa gemessen wird, und eine andere Prosa ist eine andere Zahl. Die
naheliegende Wahl (`.planning/milestones/v1.0-phases/06-semantische-suche`) ist
inhaltlich dieselbe Ablage, aber das gehoert belegt und nicht angenommen.

**Wohin es gehoert:** in den Plan der Phase 10, der `measure.yml` das naechste
Mal ohnehin anfasst, sonst in Phase 11. Zwei Dinge sind zu tun, und das zweite
ist das wichtigere:

1. Den Mountpfad auf die neue Ablage ziehen und den Lauf einmal dispatchen, bis
   `chars-per-token-prose.txt` nicht mehr leer ist.
2. Den stillen Weg schliessen: ein leerer Mount darf keinen gruenen Schritt
   ergeben. Entweder prueft der Schritt den Quellpfad vor dem `docker run`, oder
   der Aufruf pruefte seine Ausgabe, so wie `40b-baumhash.sh` es seit Plan 10-01
   tut. Ein Messschritt, der ohne Eingabe gruen bleibt, ist dieselbe Fehlerklasse
   wie die leere Baumhash-Rohdatei, wegen der die Welle 1 ueberhaupt stattfand.
