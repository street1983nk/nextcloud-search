---
phase: 15-messphase-eine-box-anfahrt
plan: 02
subsystem: docs
tags: [runbook, deckel, kostenrechnung, abbildwechsel, drop-caches, messreihenfolge, box-anfahrt]

# Dependency graph
requires:
  - phase: 12-messwerkzeug-runbook-terminentscheid
    provides: docs/runbook-messbox.md mit Deckel-Rechenblatt, Bloecken 1 bis 13 und der Messreihenfolge
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-01, das Laufverzeichnis 2026-09-v12-messung mit den elf uebernommenen Werkzeugen
  - phase: 14-modell-entladung-im-leerlauf
    provides: FINDLING_EMBED_IDLE_RELEASE_SECONDS, der Entladeschalter und seine Pflichtzeile
provides:
  - Deckel-Rechenblatt mit zehn Posten, 39 h 22 min Planwert und der Empfehlung 46 h / 5,40 USD netto
  - Block 13b Abbildwechsel auf den v1.2-Stand, per Digest, mit Rueckgabewerten 36 bis 39
  - die Aufloesung des Widerspruchs zwischen baumhash-gleich und dem noetigen Abbildwechsel
  - sync plus drop_caches als Befehl fuer "kalt", samt Nebenwirkung und Fuenf-Prozent-Warnschwelle
  - Messschritte 6b (Filter und Sortierung) und 8b (MEM-02) mit Werkzeug, Rohdatei und Abbruchpfaden
affects: [15-03-wiederaufwaermen, 15-04-grundlast-rueckkehr, 15-05-filter-sortierung, 15-06-abbildwechsel, 15-07-ablauf, 15-08-deckelfreigabe, 15-09-anfahrt]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deckelrechnung mit ausgewiesenem Vorgaengerstand: die alte Zahl bleibt neben der neuen stehen, damit die Differenz ablesbar ist und nicht nur die Steigerung"
    - "Eine Messbedingung ist ein Befehl mit Rueckleseprobe, kein Wort: sync, drop_caches mit Wert 3, free -h"
    - "Rueckgabewerte werden in der Reihenfolge ihrer Entstehung vergeben und nie umgehaengt, damit alte Rohdaten lesbar bleiben"

key-files:
  created: []
  modified:
    - docs/runbook-messbox.md

key-decisions:
  - "Die verkuerzte Ruhezeit (D-02) kuerzt den Deckel nicht: der Planwert der Wiederaufwaerm-Messung bleibt bei 2 h 00 min, die Ersparnis ist ausgewiesene Reserve"
  - "Der Vorgaengerstand 42 h / 4,90 USD vom 16.09. bleibt neben der Empfehlung 46 h / 5,40 USD stehen, damit die Differenz von vier Stunden als drei benannte Posten lesbar ist"
  - "Der Abbildwechsel findet einmal statt, vor der ersten Messung, und stellt baumhash-gleich ja erst her; danach gilt die Haltebedingung wieder unveraendert"
  - "Die Nummern der Rueckgabewerte folgen dem Katalog und nicht der Messreihenfolge: 6b bricht mit 34 und 35 ab, 8b mit 31 bis 33"

patterns-established:
  - "Jeder Messschritt der Anfahrt hat ein Werkzeug, eine Rohdatei und mindestens einen Abbruchpfad; zehn Schritte, keine Ausnahme"
  - "Eine Luecke im Runbook wird vor der Box geschlossen, weil sie auf der Box eine Box-Stunde kostet und die Vergleichbarkeit dazu"

requirements-completed: []

# Metrics
duration: 35 min
completed: 2026-09-19
---

# Phase 15 Plan 02: Runbook-Nachtraege und das neu gerechnete Deckel-Rechenblatt Summary

**Das Runbook beschreibt die Anfahrt dieser Phase jetzt vollstaendig: zehn Posten ergeben 39 h 22 min Planwert und eine Deckelempfehlung von 46 Stunden / 5,40 USD netto, Block 13b wechselt das Abbild per Digest vor der ersten Messung, "kalt" ist ein Befehl mit Rueckleseprobe, und die Messreihenfolge traegt zehn Schritte statt neun.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-09-19T20:10:00Z
- **Completed:** 2026-09-19T20:45:00Z
- **Tasks:** 3 von 3
- **Files modified:** 1 (`docs/runbook-messbox.md`, von 1.102 auf 1.310 Zeilen)

## Accomplishments

- **Das Deckel-Rechenblatt traegt alle zehn Posten dieser Anfahrt.** Drei fehlten: der Abbildwechsel (1 h 00 min), der MEM-02-Block (0 h 45 min) und der vom Owner am 19.09. bestellte Filter- und Sortierblock (1 h 30 min). Die Summe ist beim Schreiben nachgerechnet worden und lautet 2.362 Minuten, also 39 h 22 min; mit 15 Prozent Zuschlag sind das 45,27 h, aufgerundet 46 h, und 5,3287 USD, aufgerundet 5,40 USD.
- **Der Owner findet in 15-08 eine Zahlbasis und nicht nur eine Zahl.** Untergrenze (31 h / 3,59 USD), Vorgaengerstand (42 h / 4,90 USD vom 16.09.) und Empfehlung (46 h / 5,40 USD vom 19.09.) stehen in einer Tabelle nebeneinander, mit einer Spalte, die sagt, was jeweils darin steckt. Die Rechnung ist nachvollziehbar, ohne eine Datei ausserhalb des Runbooks zu oeffnen.
- **Die groesste Falle der Anfahrt ist geschlossen.** Der Snapshot traegt das Abbild vom 10.09.2026; ein Volllauf dagegen haette einen Container ohne Top-up-Route, ohne die Phase-13-Filter und ohne den Entladeschalter gemessen. Erfolgskriterium 2 waere unerfuellbar gewesen, Erfolgskriterium 5 ebenso, und aufgefallen waere es fruehestens beim Auswerten. Block 13b wechselt das Abbild vor der Zustandspruefung.
- **Der Widerspruch zwischen `baumhash-gleich` (Haltebedingung) und dem noetigen Abbildwechsel steht als aufgeloester Satz in Abschnitt 6:** gewechselt wird einmal, vor der ersten Messung, und dieser Vorgang stellt `baumhash-gleich ja` erst her. Wer das Runbook von oben nach unten abarbeitet, stolpert nicht mehr ueber zwei Abschnitte, die sich widersprechen.
- **"Kalt" ist eine Bedingung mit einem Befehl.** `sync`, dann der Wert `3` nach `/proc/sys/vm/drop_caches` auf dem Wirt, dann `free -h` als Rueckleseprobe. Daneben die Nebenwirkung im Klartext (das Leeren verwirft auch den mmap-Cache des Tantivy-Index, die kalte Suche misst also beide Haelften kalt) und die Warnschwelle: mehr als fuenf Prozent Unterschied zwischen zwei Kaltmessungen heisst, die Bedingung ist nicht hergestellt.
- **Der Aufwaermkonflikt loest sich selbst.** Bestandssonde (Schritt 3) und Laststufen (Schritt 6) waermen den Container und sind nicht verschiebbar; die Kaltmessungen des Schrittes 8 laufen deshalb nach Schritt 6 und 7, je mit Containerneustart und geleertem Wirtscache. Kalt wird hergestellt, nicht bewahrt.
- **Zehn Messschritte, jeder mit Werkzeug, Rohdatei und Abbruchpfad.** Neu sind 6b (`99c-filter-sortierung.sh`, Abbrueche 34 und 35) und 8b (`94b-grundlast-rueckkehr.sh`, Abbrueche 31 bis 33). Schritt 8 nennt jetzt das Werkzeug `95b-wiederaufwaermen.sh` statt des Musters `95b-kaltstart-reproduktion`, das eine Rohdatei von Hand ist und kein Werkzeug. Abschnitt 7.1 traegt acht neue Bedingungszeilen fuer die Werte 32 bis 39.
- **Block 10 sagt, dass `dig` auf der Entwicklungsmaschine fehlt**, mit beiden Rueckfaellen (`nslookup`, `curl --resolve`). Ein fehlendes Werkzeug, das erst auf der Box auffaellt, kostet Box-Minuten fuer eine Installation.

## Task Commits

Each task was committed atomically:

1. **Task 1: Abschnitt 2, das Deckel-Rechenblatt neu gerechnet** - `cf2c5b2` (docs)
2. **Task 2: Block 13b Abbildwechsel und die Aufloesung des Baumhash-Widerspruchs** - `38adeb9` (docs)
3. **Task 3: Der Befehl fuer "kalt", und zwei neue Messschritte** - `344becf` (docs)

**Plan metadata:** siehe den docs-Commit dieses Plans

## Files Created/Modified

- `docs/runbook-messbox.md` - Abschnitt 2.1 auf zehn Posten und 39 h 22 min, Abschnitt 2.3 um das Alter der Kostensaetze, Abschnitt 2.5 auf 46 h / 5,40 USD mit Standtabelle, Block 10 um den `dig`-Nachtrag, Block 13b neu, Abschnitt 6 um die Aufloesung des Widerspruchs, Abschnitt 7 um die Schritte 6b und 8b, Abschnitt 7.1 um acht Rueckgabewerte, Abschnitt 7.2 um den Befehl fuer "kalt" und die Reihenfolgenregel

## Decisions Made

- **Die verkuerzte Ruhezeit kuerzt den Deckel nicht.** Der Owner hat entschieden, dass die Entlade-Messungen die Frist auf 60 bis 120 s statt 900 s stellen (D-02). Der Planwert der Wiederaufwaerm-Messung bleibt trotzdem bei 2 h 00 min: ein Planwert, der eine Verbesserung vorwegnimmt, ist genau der Fehler, der den v1.1-Deckel gerissen hat (geplant rund 19 h, gebraucht 26 h 37 min). Die gesparte Wartezeit ist ausgewiesene Reserve, und die Abweichung vom Vorschlagswert ist begruendungspflichtig im Protokoll und keine stille Praxis.
- **Der Vorgaengerstand wird nicht geloescht.** Eine Deckelzahl, die von 42 auf 46 waechst und deren Vorgaenger fehlt, sieht aus wie ein Aufschlag. Die Differenz von vier Stunden ist die Summe dreier Posten, die die Anfahrt ohnehin faehrt und die im alten Rechenblatt schlicht fehlten; die Tabelle in 2.5 macht das ablesbar.
- **Der Digest wird protokolliert, aber er belegt nichts.** Gezogen wird per Digest statt ueber `:dev`, weil `:dev` wandert. Der Beweis der Identitaet bleibt der Baumhash: der Pfadfilter der Abbildstrecke reicht bis in `backend/**`, also bewegt schon ein neuer Testdatei-Commit den Digest, ohne eine Zeile des Abbilds zu aendern (Befund L-05 der Phase 11).
- **Die Rueckgabewerte folgen dem Katalog, nicht der Reihenfolge.** Schritt 6b bricht mit 34 und 35 ab, Schritt 8b mit 31 bis 33, obwohl 6b zuerst laeuft. Die Werte sind in der Reihenfolge vergeben, in der die Werkzeuge entstehen (15-03 bis 15-06); eine einmal vergebene Zahl wird nicht umgehaengt, damit Rohdaten frueherer Laeufe lesbar bleiben. Ein Absatz im Runbook sagt das, damit die Luecke nicht als Fehler gelesen wird.
- **`31` wird von Schritt 8b mitbenutzt und nicht verdoppelt.** Der Befund ist derselbe wie in 7.2 (ein Ast ohne Entladung), und derselbe Befund bekommt keine zweite Zahl.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Die verkuerzte Frist stand nur in Abschnitt 2.1 und nicht dort, wo sie gefahren wird**

- **Found during:** Task 3
- **Issue:** Task 1 hat die Owner-Entscheidung D-02 (Frist 60 bis 120 s statt 900 s) im Deckel-Rechenblatt vermerkt. Abschnitt 7.2, der den Messschritt selbst beschreibt, sprach weiter ausschliesslich vom "Vorschlagswert". Wer auf der Box nur Abschnitt 7 liest, und das ist der Normalfall waehrend einer Messung, haette 900 s gestellt und damit zweimal 15 Minuten reine Wartezeit bezahlt, gegen eine ausdrueckliche Owner-Entscheidung.
- **Fix:** Ein Absatz in 7.2 nennt die verkuerzte Frist mit ihrem Entscheid (D-02), mit der Begruendungspflicht und mit dem Hinweis, dass der tatsaechlich gestellte Wert in der Pflichtzeile aus 6.4 steht. Der Vorschlagswert 900 s bleibt als gekennzeichnete Schaetzung unberuehrt.
- **Files modified:** `docs/runbook-messbox.md`
- **Commit:** `344becf`

**2. [Rule 3 - Blocking issue] Zeilenfortsetzung im Befehlsblock von Block 13b**

- **Found during:** Task 2
- **Issue:** Der `ssh`-Aufruf in Block 13b war ueber zwei Zeilen mit Backslash geschrieben; beim Schreiben der Datei ist der Backslash verloren gegangen, und stehen geblieben waere ein einzeiliger Befehl mit fuenf Leerzeichen an der Bruchstelle. Auf der Box haette er zwar noch funktioniert, aber die Datei haette etwas anderes gezeigt, als sie meint.
- **Fix:** Der Block ist auf drei einfache Zeilen ohne Fortsetzungszeichen umgeschrieben (`cd` in das Laufverzeichnis, danach der Aufruf mit `IMAGE=...`). Das ist ausserdem naeher an dem, was auf der Box wirklich getippt wird.
- **Files modified:** `docs/runbook-messbox.md`
- **Commit:** `38adeb9`

Beide Punkte sind in den regulaeren Task-Commits enthalten; es gibt keinen eigenen Fix-Commit.

## Issues Encountered

None. Der Plan traf die Datei so an, wie er sie beschrieben hatte; alle sieben Textanker sassen beim ersten Versuch.

## Verification

| Nr | Pruefung | Ergebnis |
|----|----------|----------|
| 1 | `grep -c "Block 13b"` liefert mindestens 1 | GRUEN, 3 Zeilen |
| 2 | `grep -c "drop_caches"` liefert mindestens 1 | GRUEN |
| 3 | `grep -c "92b-wechsel"` liefert mindestens 1 | GRUEN, 3 Zeilen |
| 4 | Summenzeile 39 h 22 min, nachgerechnet | GRUEN, 150+90+60+1597+45+90+90+120+60+60 = 2.362 min = 39 h 22 min |
| 5 | Rechenweg 39,37 h x 1,15 = 45,27 h und 46 x 0,115841 = 5,3287 USD | GRUEN, beide unabhaengig nachgerechnet |
| 6 | Zehn Postenzeilen plus Summenzeile in 2.1 | GRUEN |
| 7 | Untergrenze 31 h / 3,59 USD unveraendert | GRUEN |
| 8 | Planwert der Wiederaufwaerm-Messung unveraendert 2 h 00 min | GRUEN |
| 9 | Rueckgabewerte 32 bis 39 je mit Bedingungszeile in 7.1 | GRUEN, acht neue Zeilen |
| 10 | `95b-wiederaufwaermen`, `94b-grundlast-rueckkehr`, `99c-filter-sortierung` im Runbook genannt | GRUEN |
| 11 | Kein U+2014, kein U+2013, kein Emoji, kein gesperrtes Wort | GRUEN |
| 12 | Datei durchgehend CRLF wie vorgefunden | GRUEN, 1.310 CRLF, kein einzelnes LF und kein einzelnes CR |
| 13 | `tests/test_measurement_scripts.py` gruen nach jedem Task | GRUEN, 298 bestanden |
| 14 | Volle Suite aus `backend/` | GRUEN, 2.330 bestanden, 15 uebersprungen (Skipzahl unveraendert gegen 15-01) |
| 15 | Mindestlaenge 1.150 Zeilen aus den must_haves | GRUEN, 1.310 Zeilen |

Zur Geheimnisregel (T-15-03): die neuen Bloecke nennen `<box>`, `<checkout>` und `<digest>` als Platzhalter mit je einem Satz zu ihrer Herkunft. Keine Adresse, keine Volume- oder Kontokennung ist dazugekommen; `snap-03f1d1d9ad9262704` bleibt die einzige ausgenommene Kennung und ist unberuehrt.

## Known Stubs

Keine. Die vier Werkzeuge, die das Runbook jetzt beim Namen nennt (`92b-wechsel.sh`, `94b-grundlast-rueckkehr.sh`, `95b-wiederaufwaermen.sh`, `99c-filter-sortierung.sh`), liegen noch nicht im Laufverzeichnis. Das ist kein Stub, sondern die Reihenfolge dieser Phase: sie entstehen in 15-03 bis 15-06, und `TOOLS_THE_MEASUREMENT_ORDER_NAMES` nimmt jeden Namen mit seinem eigenen Plan auf. Bis dahin ist das Runbook die Zusage, gegen die diese vier Plaene bauen.

## User Setup Required

None. Der Owner-Checkpoint 15-08 (Deckelfreigabe mit Datum) bleibt unveraendert vor Welle C; dieser Plan liefert ihm die Zahl, er gibt sie frei oder aendert sie.

## Next Phase Readiness

- **15-03 bis 15-06** koennen anschliessen: jedes der vier Werkzeuge hat jetzt seinen Platz in der Messreihenfolge, seine Rohdatei und seine Rueckgabewerte im Runbook stehen (29 bis 31 fuer 15-03, 31 bis 33 fuer 15-04, 34 und 35 fuer 15-05, 36 bis 39 fuer 15-06). Die Plaene bauen gegen eine geschriebene Zusage und muessen sie nicht erfinden.
- **15-07** (00-ablauf.md auf zehn Schritte) findet die Reihenfolge samt Aufloesung des Aufwaermkonflikts und den Befehl fuer "kalt" vor; die Ablaufdatei kann sie uebernehmen, statt sie zu erzeugen.
- **15-08** bekommt 46 h / 5,40 USD netto mit ausgewiesenem Vorgaengerstand und Untergrenze.
- **MESS-05 bleibt ungetickt.** Die Anforderung gehoert an das Phasenende (15-16) und nicht an diesen Plan, obwohl die Frontmatter sie fuehrt.

## Self-Check: PASSED

- `docs/runbook-messbox.md` auf der Platte gefunden, 1.310 Zeilen, durchgehend CRLF.
- Alle drei Task-Commits in der Historie: `cf2c5b2`, `38adeb9`, `344becf`.
- Keine Loeschung in den drei Commits (`git diff --diff-filter=D` leer).
- Volle Suite aus `backend/` gruen (2.330 bestanden, 15 uebersprungen).

---
*Phase: 15-messphase-eine-box-anfahrt*
*Completed: 2026-09-19*
