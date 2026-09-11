# Aufgeschobene Befunde der Phase 11

---

## DI-11-01 (gefunden in Plan 11-06, Task 3): die Vorpruefung des Fremdbestands misst einen Antwortdeckel und nicht den Bestand

**Gefunden:** beim Messblock B der Box-Anfahrt, als das Sprachfall-Skript mit
Rueckgabewert 17 endete und kein einziger Fall als nicht messbar galt.

**Was:** Die Nachfolgefassung `98b-sprachfaelle.sh` (Plan 11-03) prueft vor den
zehn Faellen, wie viel Fremdbestand einem Begriff im Weg steht, und vergleicht
diese Zahl mit der Schwelle 64 (`MAX_RECHECKS_ABSOLUTE`). Auf der Mess-Box
liefert die OCS-Route jedem geprueften Begriff exakt **26** Treffer, bei Tiefe
64, 200 und 2000 gleichermassen, und exakt 6 bei Tiefe 5. Die Zahl haengt weder
am Begriff noch an der Tiefe
(`docs/measurements/2026-09-werkzeugfixe/rohdaten/07-fremdbestand-gegenprobe.txt`).

Damit kann die Messgroesse die Schwelle nie ueberschreiten, das dreiwertige
Urteil bleibt praktisch zweiwertig, und die vier Faelle 1, 2, 4 und 6 sind rot
wie am 10.09.2026. Die Bilanz `6 von 10, davon 0 nicht messbar` ist zahlengleich
mit der des 10.09.

**Was der Fix trotzdem gebracht hat:** drei der vier Zusagen halten. Jeder
Begriff traegt seine Fremdbestandszahl in einer eigenen Zeile, die Bilanzzeile
nennt zwei Zahlen statt einer, und `CI_LAUF` ist Pflichteingabe, deren Fehlen
den Lauf vor dem ersten Fall beendet.

**Warum nicht dort behoben:** Ein Messskript, das waehrend seines eigenen Laufs
nachgebessert wird, macht jede Zahl daneben unbelegt. Die Aenderung ist
ausserdem keine Messung, sondern eine Aenderung an der Messgroesse, und sie
braucht eine eigene Ueberlegung: gezaehlt gehoert die Zahl der Dokumente im
Index, die den Begriff tragen, und nicht die Zahl der Treffer, die die Route
herausgibt. Ob diese Zahl ohne Eingriff in die Berechtigungskette ueberhaupt
erhebbar ist, ist offen.

**Wohin es gehoert:** ein eigener Plan, ohne Box. Der Beweis mit eigenem Index
liegt weiterhin in `integration.yml`, Job `index-search-e2e`, zuletzt Lauf
34530208024, und dieser Lauf faehrt dieselben zehn Faelle ohne Fremdbestand.
DI-10-02 bleibt damit offen.

---

## DI-11-02 (gefunden in Plan 11-06, Task 2): eine leere Antwort ohne Protokollspur

**Gefunden:** beim Aufrechnen der beiden Zaehlungen von Messblock A.

**Was:** Die Kontrollstufe 8 meldet neun Fehlschlaege. Acht davon gehen auf den
Begriff `Mahnung`, der im Lastkorpus keinen Treffer traegt. Der neunte bleibt
offen: das Nextcloud-Protokoll traegt im Fenster der Stufe 8 und eine Minute
darueber hinaus keine einzige Zeile der Apps `findling` oder `app_api`
(`docs/measurements/2026-09-werkzeugfixe/rohdaten/03-nc-protokoll-abbrueche.txt`).
Diese eine Anfrage bekam also eine leere Ergebnisgruppe, ohne dass irgendwo ein
Abbruch entstand.

**Vermutung, als Vermutung beschriftet:** DI-07-03, die Kandidatenschleife holt
keine zweite Runde nach, und der Rechteabgleich verwirft unter Last die
Kandidaten einer Runde vollstaendig. Nachgewiesen ist das nicht.

**Was diese Vermutung pruefbar macht:** Plan 11-13 hat am 10.09.2026 genau
diesen Fall mit einem eigenen Zustand versehen,
`SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED`, der statt einer leeren Liste
einen Satz zurueckgibt. Die Box trug diesen Stand nicht, weil sie seit dem
10.09. angehalten war und kein neues Abbild bekommen hat. Ein Lauf mit dem
neuen Companion wuerde die Frage ohne Zusatzmessung beantworten: traegt die
Antwort den Satz, war es DI-07-03; bleibt sie leer, war es etwas anderes.

**Warum nicht dort behoben:** Die Anfahrt hatte den Auftrag, zwei Werkzeug-Fixe
zu beweisen, und sonst nichts. Ein einzelner Vorgang unter 80 traegt keine
Aussage.

**Wohin es gehoert:** zum Audit der Phase 11, als zweite Beobachtung neben
DI-07-03.

---

## DI-11-03 (gefunden in Plan 11-06, Task 2): der neue Zaehler unterscheidet leer nicht von abgebrochen

**Gefunden:** beim Vergleich der Erwartung E3 mit dem Ergebnis.

**Was:** `EmptyResultGroup` zaehlt jede Antwort mit weniger als `--min-hits`
Treffern, gleich ob ein Containeraufruf abgebrochen ist oder ob die Suche
schlicht nichts gefunden hat. Auf Stufe 16 sind das 14 Abbrueche und 16 leere
Suchen in derselben Zahl 30. Der Name legt die erste Lesart nahe, und die
Erwartung E3 (`Stufe 8 zeigt failures == 0`) ist genau daran gescheitert.

**Warum das trotzdem kein Rueckschritt ist:** `min_hits` und `hits_per_request`
stehen jetzt in jeder Rohdatei, also ist die Zahl lesbar statt stumm. Vorher
meldete das Werkzeug `"failures": 0`, waehrend 17 Aufrufe abbrachen.

**Wohin es gehoert:** eine Ueberlegung fuer die naechste Fassung von
`search_load.py`: entweder ein zweiter Fehlschlagname fuer die Antwort, die
nachweislich abgebrochen ist, oder eine Zeile im Bericht, die die Begriffe ohne
Treffer benennt. Kein Blocker, keine Box.

---

## DI-11-04 (gefunden in Plan 11-07): zwei Log-Artefakte heissen "harp-logs-stable34"

**Gefunden:** beim Ablegen der Upgrade-Beweisdateien in das Log-Artefakt von
`deploy-harp.yml`.

**Was:** Der Upload-Schritt nennt das Artefakt
`harp-logs-${{ matrix.server-version }}`. Seit Plan 11-04 gibt es zwei Aeste mit
`server-version: stable34` (amd64 und arm64), also zwei Artefakte gleichen
Namens. Im Lauf 34546421219 sind es 13.833 Byte (der amd64-Ast, mit
`upgrade-before.json`, `upgrade-after.json`, dem Urteil von `occ upgrade` und
dem Containerprotokoll) und 7.825 Byte (der arm64-Ast). Der Upload schlaegt
nicht fehl, beide liegen nebeneinander, aber wer "das Artefakt
harp-logs-stable34" herunterlaedt, weiss nicht, welches der beiden er bekommt,
und genau in diesem Namen liegen ab jetzt die Beweisdateien des
Upgrade-Blocks.

**Warum nicht dort behoben:** Der Name ist seit Plan 11-04 so, gehoert dem
Upload-Schritt und nicht dem Upgrade-Block, und die Regel dieses Plans war,
keinen bestehenden Schritt umzubauen. Die Aenderung ist eine Zeile
(`harp-logs-${{ matrix.server-version }}-${{ matrix.runner }}`), aber sie
aendert den Namen, unter dem jeder frueherer Bericht das Artefakt fuehrt.

**Wohin es gehoert:** zum Audit der Phase 11 (Plan 11-10), gemeinsam mit der
Frage, ob der Runner in den Artefaktnamen soll oder ob der Upgrade-Block ein
eigenes Artefakt bekommt.

---
