---
plan: 15-15
phase: 15-messphase-eine-box-anfahrt
status: complete
completed: 2026-09-21
requirements-completed: []  # MESS-05 wird am Owner-Checkpoint 15-16 abgehakt
---

# 15-15 SUMMARY: Bericht, Runbook-Nachtraege, Pruefsummen-Waechter

Aus einer bezahlten Anfahrt ist ein Beleg geworden, der ohne die Box gelesen
werden kann. Drei Aufgaben, drei Commits, keine Box.

## Task 1: Der Bericht, ein Urteil je Erwartung (Commit 3f504a4)

`docs/measurements/2026-09-v12-messung/README.md`, elf Abschnitte. Die
Freigabezeile im Kopf steht unveraendert.

**Vierzehn Urteile: elf gehalten, drei verfehlt, null nicht entschieden.**
Keine Erwartung ist umformuliert worden; `git diff` auf `00-ablauf.md` ist in
dieser Phase leer, die Datei ist seit dem 19.09.2026 unberuehrt.

| Gehalten | Verfehlt |
|---|---|
| E1, E2, E3, E4, E5, E6, E7, E8, E9, E11, E14 | E10, E12, E13 |

Die drei verfehlten, je mit ihrem Satz im Bericht:

- **E10 ist in die guenstige Richtung verfehlt.** Erwartet war, dass Stufe 8 das
  2.500-ms-Budget mit **kleinerer** Reserve als 374,5 ms haelt; gemessen sind
  **508,0 ms** Reserve. Die Erwartung rechnete mit einer Verschlechterung durch
  die strengere Ausfallzaehlung seit DI-10-01; eingetreten ist eine
  Verbesserung. Verfehlt bleibt verfehlt.
- **E12 reisst im kalten Eckfall** (1.996 ms gegen die 1,5-s-Decke) und haelt im
  warmen (1.418 ms). Genau der Fall, den die Phase-14-Abnahme als moeglich
  benannt hat.
- **E13 ist in ihrer zweiten Haelfte verfehlt**, und der Grund ist ein
  Namensfehler in der Erwartung selbst: die 16 MB sind ein Zuwachs je Zyklus
  aus dem Vorprueflauf, die 628,0 MB der absolute Rueckstand nach **einem**
  Zyklus. Die erste Haelfte, die Messgroesse von MEM-02, haelt mit 377,5 MB.

**Der Abschnitt "Was dieser Lauf nicht besser gemacht hat" hat elf Punkte**,
darunter der nie gelaufene Cron-Wirkungszweig, die nicht entschiedene Wirkung
der Top-up-Route, die nicht abgelesenen Zeilenstaende des Abbruchtors, die
nicht untersuchten sechs fehlgeschlagenen Dateien, die drei Werkzeug-Fixe in
der bezahlten Zeit und die **Wiedervorlage des Korpus-Snapshots** (Q5 der
Recherche, als einzige der fuenf offen geblieben; Q1 bis Q4 sind entschieden
und vollzogen).

**Der DI-10-04-Wirkungsbeleg sagt ausdruecklich, dass er nicht entscheidet.**
19 h 20 min gegen 26 h 37 min, Leerlaufanteil 2,6 statt 22,0 Prozent, und
beide Erklaerungen bleiben moeglich, weil die Instanz aus einem Snapshot neu
aufgebaut und das Abbild gewechselt wurde. Die 5,35 h weniger Leerlauf
erklaeren rund drei Viertel des Zeitgewinns; das restliche Viertel wird nicht
zugeordnet, weil das eine Schaetzung waere.

Die vier Laststufen-Verdikte sind wortgleich mit `97-nebenlaeufigkeit.txt`. Die
drei Protokollbloecke (Konfigurationszweig, Wirkungszweig, Bilanzzeile der
Sprachfaelle) stehen woertlich im Bericht. Die Kostenzeile nennt Laufzeit
(25,75 h), Kosten (2,9831 USD), Deckel (46 h / 5,40 USD) und Differenz
(20,25 h / 2,42 USD darunter), und "Deckel gehalten" steht als Wort da.

Geheimnis-Gate: keine Adresse, keine Instanz- oder Volumekennung, kein
Passwort. Die beiden zulaessigen Ausnahmen (`loadtest.infranode.dev` und
snap-03f1d1d9ad9262704) sind als solche benannt. Kein Em-Dash, kein Emoji, kein
gesperrtes Wort.

## Task 2: Die Nachtraege ins Runbook (Commit 940e77b)

`docs/runbook-messbox.md`, 725 eingefuegte Zeilen, **elf geloeschte, und alle
elf sind die Tabellenzeilen des Rechenblatts, in denen nur die leere
Ist-Spalte gefuellt wurde.** Kein Satz ist ersetzt worden; jede Abweichung steht
als eigene Zeile unter der Erwartung, an der sie aufgefallen ist. 39 Stellen
tragen die Marke "in Phase 15 erstmals vollzogen", 31 Absaetze beginnen mit
"Abweichung:".

**Die Ist-Spalte in Abschnitt 2.1 ist in allen zehn Postenzeilen gefuellt.**
Wo keine eigene Zahl entstanden ist, steht der Grund statt einer Zahl: die
Bloecke 1 bis 9 sind nicht je Block gestempelt worden, also tragen Posten 1 und
2 gemeinsam "rund 0 h 40 min" und Posten 2 den Verweis. Daraus ist ein eigener
Nachtrag geworden: **jeder Block schreibt beim Betreten und Verlassen eine
Zeile mit UTC-Zeitstempel.**

| Posten | Plan | Ist |
|---|---|---|
| Handaufbau + Wiederaufbau (Bloecke 1 bis 9) | 2:30 + 1:30 | rund 0:40 zusammen |
| Abbildwechsel | 1:00 | rund 0:32, in drei Laeufen |
| Volllauf | 26:37 | 19:20 (Untergrenze) |
| MEM-02-Block | 0:45 | 0:03 |
| Laststufen | 1:30 | 0:06 Messzeit |
| Filter und Sortierung | 1:30 | 0:00:11 Messzeit |
| Wiederaufwaermen | 2:00 | 0:07 (bei 120 s Ruhezeit) |
| Sprachfaelle | 1:00 | 0:07 |
| Abbau und Endmessungen | 1:00 | 0:05 Box-Zeit bis zum Anhalten |
| Summe | 39:22 | **25,75 h Box-Laufzeit gesamt** |

**Vier erwartete Ausgaben des Runbooks waren falsch** und bleiben mit ihrer
Richtigstellung daneben stehen: die harte Containergrenze in beiden
cgroup-Feldern (richtig ist 2147483648/**0**, Block 12 und Abschnitt 6), die
91 MB der Systemplatten-Sicherung (richtig sind 385 Dateien und 13M), `docker`
und `ncdata` als vollstaendiger Inhalt des Datentraegers (dort liegt auch
`containerd`, und daran haengt Block 8) und der Arbeitsbaum aus Block 9, den es
nicht gibt.

**Zwei Schritte waren in der geschriebenen Reihenfolge nicht fahrbar:** das
Abbruchtor in Abschnitt 5 (Block 13b leert den Index davor; das Tor hat jetzt
zwei Fassungen, je nach Abbildwechsel) und der Bestandsvorlauf als Schritt 3
(wandert hinter den Volllauf). **Einer ist vergessen worden:** der
Cron-Wirkungszweig, mit dem Handgriff daneben, der das kuenftig verhindert.

**Sechs neue Vorbedingungen** in Abschnitt 3 (Schluesselpaar,
liegengebliebene `.pub`, Herkunft des Arbeitsbaums, die beiden
Konfigurationstexte fuer Docker und containerd, `FINDLING_LOAD_PASSWORD`,
wechselnde eigene Adresse), je mit dem Satz, was sie in der bezahlten Zeit
gekostet haben. Zwei alte Zeilen bleiben stehen und bekommen einen Vermerk
(Zeile 2 und Zeile 7).

**Der 15-03-Nachtrag ist gesetzt:** Abschnitt 7.2 nennt weiterhin den
"Entladezaehler", und darunter steht, dass es ihn ueber eine Prozessgrenze
nicht gibt. Gelesen werden `engineState unloaded` an der Admin-Seite selbst
(nicht ueber `96d-statusbeobachter.py`) und die cgroup-Groesse vor und nach der
Ruhezeit. Rueckgabewert 31 faellt ab jetzt, wenn einer der beiden ausbleibt.

**Abschnitt 9.3 traegt die Schlusszahlen** (25,75 h, 2,9831 USD, Deckel 46 h /
5,40 USD, Differenz 20,25 h / 2,42 USD) und den Satz, **welche Annahme ihren
Schaetzcharakter verloren hat: A8, der Handaufbau.** Geschaetzt 2 h 30 min,
gemessen rund 0 h 40 min fuer die Bloecke 1 bis 9 zusammen, und das mit den
beiden teuersten Abweichungen darin. Zwei Einschraenkungen stehen daneben: die
Zahl ist nicht je Block gestempelt, und sie ist eine Untergrenze, weil die
Sitzungszeit nicht darin steckt.

Dazu: Abschnitt 2.4 hat zwei Zeilen bekommen (Freigabe und Verbrauch), Abschnitt
8 den Nachtrag, dass `destroy` weder Schluesselpaar noch A-Record abraeumt, und
Abschnitt 9.4 die Bilanz des Erstvollzugs.

## Task 3: Die sechs Pruefsummen-Waechter (Commit cdd391f)

`DRIVEN_V12_FASSUNGEN` in `backend/tests/test_measurement_scripts.py`, genau
sechs Eintraege, je mit sha256 und Byteanzahl, mit dem Begruendungsabsatz
darueber. Drei Faelle: der parametrisierte
`test_the_driven_v12_fassung_stays_byte_identical` mit `DRIVEN_FASSUNG_RULE`
als Diagnose, die Mutationsprobe ueber alle sechs, und ein Fall, der die sechs
von `COPIED_TOOLS` getrennt haelt. `-k "driven_v12_fassung"` waehlt **acht**
Faelle aus. `COPIED_TOOLS` ist unberuehrt.

### Ist jedes der sechs seit dem Stand vor der Anfahrt byteweise unveraendert?

**Der Plan nimmt an, keines sei waehrend der Anfahrt geaendert worden. Das ist
fuer zwei der sechs falsch.** Der Befund steht hier und nicht im Sollwert: die
Sollwerte sind wie vorgeschrieben aus dem Zustand **nach** der Anfahrt
abgelesen, und das ist bei allen sechs der Stand, der die committeten Rohdaten
geschrieben hat.

| Datei | Byteweise unveraendert? | Beleg |
|---|---|---|
| `92b-wechsel.sh` | **NEIN** | zwei Fixes am 20.09. in der bezahlten Zeit (d6fb185, ff8e054). Stand davor: `532b5db7...`, 28.370 Byte. Stand jetzt: `8d1f5199...`, 30.400 Byte |
| `94b-grundlast-rueckkehr.sh` | ja | letzter Commit ad4dc89 vom 19.09., vor der Anfahrt |
| `95b-wiederaufwaermen.sh` | ja | letzter Commit c92199d vom 19.09., vor der Anfahrt |
| `97-cron-vorpruefung.sh` | **NEIN** | zwei Commits am 20.09. in der bezahlten Zeit (a9167f2, 6f42c69). Stand davor: `fed2ca78...`, 24.715 Byte. Stand jetzt: `0c84c4ff...`, 26.252 Byte |
| `98c-sprachfaelle.sh` | ja | letzter Commit f889273 vom 16.09., vor der Anfahrt |
| `99c-filter-sortierung.sh` | ja | letzter Commit 1d3a3ec vom 19.09., vor der Anfahrt |

**Warum das trotzdem kein Anlass war, einen Sollwert anzupassen.** Beide
Aenderungen sind mit ausdruecklichem Owner-Wort gefallen, beide beseitigen
einen falschen Abbruch auf einem korrekten Zustand (die Grenze in beiden
cgroup-Feldern, das Cron-Intervall als 5 s statt 300 s), und beide sind mit
boxlosen Tests nachgezogen worden. Die Rohdaten, die im Bericht zitiert werden,
stammen je aus dem Lauf **nach** dem Fix: `92b-wechsel.txt` ist der Stand des
dritten Laufs, `97-cron-vorpruefung-vorher.txt` der Stand nach 6f42c69. Der
Waechter friert damit genau die Fassung ein, die die zitierten Zahlen
geschrieben hat. Der Vorgang selbst steht als Abweichung im Runbook (Abschnitt
7.1) und als Punkt 8 im Bericht.

## Verification

1. `grep -c "Was dieser Lauf nicht besser gemacht hat"` im Bericht: 1. GRUEN.
2. `grep -cE "E1[0-4]"` im Bericht: 18. GRUEN.
3. Em-Dash-, Emoji- und Vokabular-Gate ueber Bericht und Runbook: leer. GRUEN.
4. `grep -c "in Phase 15 erstmals vollzogen"` im Runbook: 39. GRUEN.
5. Leere Ist-Zellen im Runbook: 0. GRUEN.
6. `ruff check`, `ruff format --check`, `pyright`
   (`PYRIGHT_PYTHON_FORCE_VERSION=latest`, 0 errors), `vulture --min-confidence 80`:
   alle GRUEN.
7. `pytest -k "driven_v12_fassung" -q`: 8 bestanden. GRUEN.
8. Volle Suite: **2.394 bestanden, 15 uebersprungen**. Skipzahl unveraendert
   gegen 14-12. GRUEN.
9. Kennungs-Gate ueber beide Dokumente (Instanz-, Volume-, Security-Group-
   Kennungen, IPv4): leer. GRUEN.

## Deviations from Plan

**1. [Befund, kein Fix] Zwei der sechs Messfassungen sind waehrend der Anfahrt
geaendert worden.** Der Plan schreibt "keines der sechs Skripte wurde waehrend
der Anfahrt geaendert, also sind es dieselben Bytes wie vor ihr" und weist an,
eine Abweichung als Befund zu melden statt den Sollwert anzupassen. Genau das
ist geschehen: `92b-wechsel.sh` und `97-cron-vorpruefung.sh` sind am 20.09.
geaendert worden, die Sollwerte stehen unveraendert auf dem Zustand nach der
Anfahrt, und der Befund steht in Task 3 oben mit beiden alten Pruefsummen.
Kein Commit ausserhalb der drei Aufgaben.

**2. [Rule 3] `pyright` mit `PYRIGHT_PYTHON_FORCE_VERSION=latest` gefahren.**
Der `verify`-Block des Plans ruft `uv run pyright` ohne die Variable. Die
Owner-Regel vom 19.09. verlangt sie, weil der CI-pyright neuer ist als der
lokale Cache. Ergebnis mit der neueren Fassung: 0 errors, 0 warnings.

**3. Kein Baumhash nachzuziehen.** Dieser Plan fasst `backend/src/findling/`
und `php/` nicht an; geaendert sind nur `backend/tests/` und zwei Dateien unter
`docs/`. `PACKAGE_TREE_HASH_TODAY` und `PHP_TREE_HASH_TODAY` bleiben
unberuehrt, und die volle Suite bestaetigt es.

## Offen fuer 15-16 (Owner-Checkpoint)

- **MESS-05 und MEM-02 abhaken.** Beide haben ihre Zahl an ihrer Messgroesse.
- **Die Bodensatz-Zahl vorlegen:** 731,9 MB residenter Stand nach einem
  Indexlauf mit entladenem Modell, auf einer 4-GB-Box. Sie ist im Bericht als
  eigene Zahl gefuehrt und ausdruecklich von den 16 MB der Erwartung getrennt.
- **Q5, die Wiedervorlage des Korpus-Snapshots.** Steht im Bericht unter den
  offen gebliebenen Punkten und im Runbook, Abschnitt 8, Schritt 9.
- **Drei Werkzeug-Befunde ohne Fix**, alle im Runbook benannt: die
  Phase-B-Pipeline von `92b-wechsel.sh` verschluckt occ-Fehler, `99c` erwartet
  das Passwort in der Umgebung, `94b` ruft den Abtaster ohne `sh`.

## Naechster Schritt

15-16, der Owner-Checkpoint der Phase.
