---
phase: 15-messphase-eine-box-anfahrt
plan: 07
subsystem: docs
tags: [ablaufdatei, erwartung-vorher, vorbedingungen, belegkriterium, drop-caches, aufrufform, box-anfahrt]

# Dependency graph
requires:
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-01, das Laufverzeichnis mit den elf uebernommenen Werkzeugen
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-02, Abschnitt 7 des Runbooks mit zehn Messschritten, den Rueckgabewerten bis 39 und dem Deckel 46 h / 5,40 USD
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-03 bis 15-06, die vier neuen Werkzeuge samt ihren Aufrufvertraegen und Rueckgabewerten
  - phase: 14-modell-entladung-im-leerlauf
    provides: die Sichtprobe aus 14-12 (376,3 MB, 1,37 bis 1,44 s) und der Vorprueflauf auf aarch64 (17,1 MB Zielast)
  - phase: 11-vergleichsmessung
    provides: die p95-Reihe aus docs/audits/2026-09-phase-11/ und Befund L-05
provides:
  - 00-ablauf.md mit zwoelf Schrittzeilen im Gleichschritt mit Abschnitt 7 des Runbooks
  - die Erwartungen E8 bis E14 mit Zahlen, committet VOR der Anfahrt
  - E14, das Belegkriterium des 900-s-Vorschlagswerts ueber seine Folgen statt ueber die Frist
  - der Absatz "Kalt wird hergestellt, nicht bewahrt" mit sync, drop_caches und der mmap-Nebenwirkung
  - die elf Abbruchwerte 29 bis 39 in der Ablaufdatei
  - eine einheitliche Aufrufform fuer alle achtzehn Werkzeuge, mit der chmod-Zeile vor Schritt 0
  - rohdaten/02-vorbedingungen.txt mit acht abgearbeiteten Vorbedingungen und der offenen Freigabezeile
affects: [15-08-deckelfreigabe, 15-09-anfahrt, 15-13-belegkriterium, 15-15-bericht, 15-16-phasenabschluss]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Erwartung wird ergaenzt und nicht umgeschrieben: der datierte Nachtrag laesst den alten Wortlaut stehen, und git diff mit null Loeschungen ist sein Beleg"
    - "Ein Belegkriterium nennt beide Aeste: was gilt, wenn es haelt, und was folgt, wenn jede einzelne Bedingung reisst"
    - "Eine Vorbedingung wird gefahren und nicht erinnert, auch wenn ihr Ergebnis am selben Tag schon einmal notiert wurde"

key-files:
  created:
    - docs/measurements/2026-09-v12-messung/rohdaten/02-vorbedingungen.txt
  modified:
    - docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md

key-decisions:
  - "Die alte Fuenf-Schritt-Tabelle bleibt stehen und bekommt eine Nummernwanderungstabelle daneben; nur die Sprachfaelle wandern, von 4 auf 7"
  - "Die einheitliche Aufrufform ist ./werkzeug.sh plus eine chmod-Zeile vor Schritt 0, nicht sh werkzeug.sh: die sh-Form haette den bereits stehenden Wortlaut der Ablaufdatei und drei Stellen des Runbooks gegen sich"
  - "E9 ist eine Erwartung und kein Planwert: der Deckel rechnet weiter mit 26 h 37 min"
  - "E10 sagt vorher, dass schlechtere Zahlen kein Befund ueber die Suche waeren, weil der Zaehler seit dem 10.09. strenger zaehlt"
  - "E14 bindet den 900-s-Vorschlagswert an E12 UND E13 und nennt fuer jedes Reissen eine andere Folge: E12 gerissen heisst Empfehlung mit Zahl daneben, E13 gerissen heisst falsche Stellschraube"
  - "Die VolumeId des Snapshots steht nicht in der Vorbedingungsdatei, obwohl das Volume tot ist: die Geheimnisregel kennt keine Ausnahme fuer tote Kennungen"
  - "Die Freigabezeile bleibt leer und traegt nur ihren Platzhalter; gefuellt wird sie in 15-08"

patterns-established:
  - "Nachtrag statt Loeschung, mit Datum: der Vorgaengerstand einer Zahl bleibt sichtbar, damit die Differenz ablesbar ist und nicht nur die Steigerung"
  - "Eine Rohdatei der Vorbedingungen nennt je Zeile Kommando, Ausgabe und Urteil, und ein offenes Urteil traegt den Ort seiner spaeteren Pruefung"

requirements-completed: []

# Metrics
duration: 34min
completed: 2026-09-19
---

# Phase 15 Plan 07: Die Erwartung vor der Box Summary

**Die Ablaufdatei traegt zwoelf Schritte, die Erwartungen E8 bis E14 mit Zahlen und das Belegkriterium des 900-s-Vorschlagswerts, und die neun Vorbedingungen sind gefahren, bevor die erste Box-Minute laeuft.**

## Performance

- **Duration:** 34 min
- **Started:** 2026-09-19T21:24:00Z
- **Completed:** 2026-09-19T21:58:00Z
- **Tasks:** 2
- **Files modified:** 2 (eine erweitert, eine neu)

## Accomplishments

- **Die Erwartung dieses Laufs steht mit Zahlen da, bevor die Box existiert.** E8 bis E14 nennen `baumhash-gleich ja`, 26 h 37 min, 2.500 ms und 374,5 ms, den Faktor zwei und die Seitenzahlen 1/2/3, 1,5 s, 300 MB und rund 16 MB. Der Commit `190d5c7` ist ihr Zeitstempel und liegt vor jedem Handgriff an der Box.
- **E14 belegt die Folgen einer Frist und nie die Frist selbst.** Der Vorschlagswert 900 s bleibt, wenn E12 und E13 beide halten; fuer jedes einzelne Reissen steht vorher da, was folgt, und die verkuerzte Ruhezeit (D-02) ist mit ihrer Begruendung und ihrer einen Einschraenkung benannt.
- **Die Reihenfolge ist definiert und nicht erklaert.** "Kalt wird hergestellt, nicht bewahrt" steht als eigener Abschnitt in der Ablaufdatei, mit `sync`, dem Wert `3` nach `/proc/sys/vm/drop_caches`, der Rueckleseprobe `free -h` und der Nebenwirkung auf den mmap-Cache des Tantivy-Index.
- **Acht der neun Vorbedingungen sind abgearbeitet und protokolliert**, mit ihren tatsaechlichen Ausgaben. Die neunte ist der Owner-Checkpoint 15-08 und traegt bis dahin nur ihren Platzhalter.
- **Der offene Punkt aus 15-06 ist geschlossen.** Die Aufrufform gilt jetzt einheitlich fuer alle achtzehn Werkzeuge, und sie ist so gewaehlt, dass weder die Ablaufdatei noch das Runbook dafuer umgeschrieben werden musste.

## Task Commits

1. **Task 1: 00-ablauf.md auf zwoelf Schritte, mit den Erwartungen E8 bis E14** - `190d5c7` (docs)
2. **Task 2: Die neun Vorbedingungen abarbeiten und protokollieren** - `c69624e` (docs)

**Plan metadata:** siehe Schlusscommit dieses Plans (docs: SUMMARY, STATE, ROADMAP)

## Files Created/Modified

- `docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md` - 237 eingefuegte Zeilen, **null geloeschte**. Neu: der datierte Nachtrag im Kopf, Abschnitt 2.1 (zwoelf Schrittzeilen, Nummernwanderung, Aufrufform), Abschnitt 2.2 (kalt wird hergestellt), Abschnitt 3.1 (E8 bis E14), Abschnitt 4.1 (Abbruchwerte 29 bis 39) und der Waechter-Nachtrag in Abschnitt 5.
- `docs/measurements/2026-09-v12-messung/rohdaten/02-vorbedingungen.txt` - neun nummerierte Zeilen mit Kommando, Ausgabe und Urteil, dazu der Preisabgleich und eine Bilanz. ASCII, ohne Umlaute, ohne Kennung und ohne Adresse.

## Decisions Made

**1. Die alte Schritttabelle bleibt, die neue steht daneben.** Der Plan verlangt zwoelf Zeilen und zugleich, dass Abschnitt 2 ergaenzt und nicht umgeschrieben wird. Beides zusammen geht nur so: die fuenf alten Zeilen bleiben im Wortlaut, darunter steht die bindende Tabelle nach Abschnitt 7 des Runbooks, und dazwischen eine kleine Tabelle, die die Nummernwanderung nennt. Von den fuenf alten Nummern wandert genau eine, der Sprachfall-Lauf von 4 auf 7. Ohne diese Zeile haette der bereits stehende Absatz "Zwei Vorbedingungen von Schritt 4" auf den Volllauf gezeigt statt auf die Sprachfaelle.

**2. Die Aufrufform ist `./werkzeug.sh` plus eine chmod-Zeile, nicht `sh werkzeug.sh`.** Beide Formen loesen den offenen Punkt aus 15-06, aber nur eine loest ihn, ohne bestehenden Wortlaut zu brechen. Die `sh`-Form haette drei Stellen des Runbooks und die unveraendert stehenden Zeilen der Ablaufdatei gegen sich gehabt, die beide `./werkzeug.sh` fuehren. Die chmod-Zeile steht deshalb vor Schritt 0, mit `ls -l` als Rueckleseprobe, und die `sh`-Form bleibt ausdruecklich das, was sie heute schon ist: der Weg, auf dem ein Werkzeug ein anderes ruft, so wie `92b-wechsel.sh` den Baumhashbeweis.

**3. E9 bleibt eine Erwartung und wird kein Planwert.** Die Laufzeit soll unter 26 h 37 min liegen, der Deckel rechnet trotzdem mit 26 h 37 min. Ein Planwert, der eine Verbesserung vorwegnimmt, ist genau der Fehler, der den v1.1-Deckel gerissen hat.

**4. E10 sagt vorher, was eine schlechtere Zahl bedeuten wuerde.** Seit dem 10.09.2026 zaehlt der Zaehler abgebrochene Aufrufe nicht mehr als beantwortet (DI-10-01). Ohne diesen Satz VOR dem Lauf waere eine schlechtere p95-Reihe nach dem Lauf eine Erklaerung gewesen; mit ihm ist sie eine vorhergesagte Folge einer bekannten Aenderung.

**5. Die VolumeId bleibt aus der Rohdatei heraus.** Das Datenvolume ist am 11.09.2026 abgebaut worden und die Kennung steht bereits in einer aelteren committeten Rohdatei. Sie hier zu wiederholen haette nichts belegt, was `SnapshotId` nicht schon belegt, und die Geheimnisregel dieser Datei kennt keine Ausnahme fuer tote Kennungen. Erlaubt und benutzt ist allein `snap-03f1d1d9ad9262704`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Der Kopf der Ablaufdatei nannte einen Deckel, den es nicht mehr gibt**
- **Found during:** Task 1
- **Issue:** Der zweite Satz im Kopf fuehrte 42 h und 4,90 USD netto als Deckel. Seit Plan 15-02 steht das Rechenblatt auf 46 h und 5,40 USD netto. Die Ablaufdatei ist das Dokument, das der Operator am Anfahrtstag liest; eine alte Deckelzahl darin ist keine Unschaerfe, sondern eine falsche Abbruchschwelle in der bezahlten Zeit.
- **Fix:** Ein datierter Nachtrag im Kopf nennt den neuen Stand, benennt die drei Posten, die dazugekommen sind, und laesst den Vorgaengerstand ausdruecklich stehen, damit die Differenz ablesbar bleibt (Muster 15-02).
- **Files modified:** docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md
- **Verification:** `46 h` und `5,40 USD` stehen in der Datei, der alte Satz ist unveraendert; `git diff --numstat` meldet 237 Einfuegungen und 0 Loeschungen.
- **Committed in:** `190d5c7`

**2. [Rule 3 - Blocking] Die Aufrufform der Werkzeuge haette auf der Box mit 126 geendet**
- **Found during:** Task 1 (offener Punkt aus 15-06)
- **Issue:** Vierzehn der achtzehn Werkzeuge des Laufverzeichnisses stehen mit `100644` im Index, nur vier mit `100755`. Ein Auscheck auf der Box erbt diese Masken. Der erste Aufruf `./97-cron-vorpruefung.sh vorher` haette dort mit **126** und "Permission denied" geendet, in der bezahlten Zeit und mit einer Meldung, die in keinem der beiden Dokumente erklaert ist.
- **Fix:** Der Abschnitt "Zur Aufrufform" nennt die Masken, die Folge, die eine chmod-Zeile vor Schritt 0 samt Rueckleseprobe, und die eine Form, die danach in beiden Dokumenten gilt. Die `sh`-Form bleibt fuer Werkzeug-ruft-Werkzeug benannt, damit die beiden nicht nebeneinander ungeklaert stehen.
- **Files modified:** docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md
- **Verification:** `git ls-files -s` auf dem Laufverzeichnis zeigt die vierzehn zu vier; der Abschnitt nennt beide Zahlen und alle vier ausfuehrbaren Dateien namentlich.
- **Committed in:** `190d5c7`

**3. [Rule 1 - Bug] Die Planliste der Phase 15 im ROADMAP war zwei Plaene alt**
- **Found during:** Abschluss (State-Updates)
- **Issue:** Die Fortschrittstabelle des ROADMAP stand auf 6/16, die Planliste derselben Phase dagegen auf "4/16 plans complete" mit ungetickten Haken fuer 15-05 und 15-06. Zwei Zahlen fuer denselben Sachverhalt in derselben Datei.
- **Fix:** Haken fuer 15-05, 15-06 und 15-07 gesetzt, die Zeile auf 7/16 und die Tabellenzeile ebenfalls auf 7/16.
- **Files modified:** .planning/ROADMAP.md
- **Verification:** Beide Stellen nennen dieselbe Zahl.
- **Committed in:** Schlusscommit dieses Plans

---

**Total deviations:** 3 auto-fixed (1 fehlende kritische Angabe, 1 blockierend, 1 Bug)
**Impact on plan:** Alle drei betreffen die bezahlte Zeit oder die Lesbarkeit des Fahrplans. Kein Zuwachs am Umfang: zwei Dateien geplant, zwei Dateien geaendert, dazu die Zustandsdateien.

## Issues Encountered

**Der gruene CI-Lauf gehoert nicht zum Kopf des Zweiges.** Die Vorbedingung 1 verlangt die Laufnummer eines gruenen `integration.yml`-Laufs. Gefunden wurde **35469147833** (Commit des Plans 15-04, 2026-09-19T21:01:20Z). Der Lauf darueber, **35470079862** zum Commit des Plans 15-05, ist fehlgeschlagen, und zwar im Schritt "Log every account in and keep its session" des Auftrags `search-parity (stable34, 8.2)` mit der Meldung "the login of minimal was refused". Der Lauf zum heutigen Kopf war zum Zeitpunkt der Ablesung noch nicht fertig.

Das ist **ausserhalb des Umfangs dieses Plans**: der Fehlschlag liegt in der Suchparitaet und beruehrt kein Werkzeug des Laufverzeichnisses. Er ist in `deferred-items.md` der Phase vermerkt und in der Rohdatei als Befund protokolliert, nicht als Abbruch. Fuer die Anfahrt folgt daraus genau das, was die Ablaufdatei ohnehin verlangt: die Laufnummer wird unmittelbar vor Schritt 7 ein zweites Mal geholt.

**Kein Preisunterschied.** Der Abgleich der sechs Saetze gegen Abschnitt 2.3 des Runbooks ergab keine Abweichung; drei Saetze druckt `aws_box.sh prices`, die anderen drei folgen aus ihnen und sind in der Rohdatei nachgerechnet. Es entsteht also keine Zeile fuer den Checkpoint.

## Known Stubs

Keine. Die einzige absichtlich leere Stelle ist die Freigabezeile der Vorbedingung 9, und sie ist als Platzhalter mit ihrem Fuellort benannt: `Anfahrt freigegeben: <Datum>, Deckel <h> h / <USD> USD`, gefuellt in 15-08 und nirgends sonst.

## Verification

| Nr | Pruefung | Ergebnis |
|----|----------|----------|
| 1 | Abschnitt 2 traegt zwoelf Schrittzeilen (0 bis 9 samt 6b und 8b) | GRUEN, je mit Werkzeug, Rohdatei und Aussage |
| 2 | E1 bis E7 byteweise unveraendert | GRUEN, `git diff --numstat` meldet 237 Einfuegungen und **0 Loeschungen** |
| 3 | E8 bis E14 mit ihren Zahlen | GRUEN, `baumhash-gleich ja`, 26 h 37 min, 2.500 ms, 374,5 ms, Faktor zwei, 1/2/3, 1,5 s, 300 MB, 16 MB |
| 4 | E14 nennt beide Bedingungen und beide Folgen | GRUEN, plus die Begruendung der verkuerzten Ruhezeit und ihre eine Einschraenkung |
| 5 | Der Absatz "Kalt wird hergestellt" nennt sync, drop_caches, den Wert 3 und den mmap-Cache | GRUEN |
| 6 | Abschnitt 4 traegt elf neue Zeilen fuer 29 bis 39 | GRUEN, dazu der Satz zur tee-Pipeline und die Ausnahme fuer den Wert 2 |
| 7 | Kein Em-Dash, kein En-Dash, kein gesperrtes Wort, kein Emoji in der Ablaufdatei | GRUEN, nicht-ASCII sind allein ae, oe, ue und ss |
| 8 | Die Vorbedingungsdatei traegt neun Zeilen plus Preisabgleich | GRUEN, sechs erfuellt, 7 und 8 offen mit Begruendung, 9 als Platzhalter |
| 9 | Kein `i-`, kein `vol-`, keine IPv4 in der Vorbedingungsdatei | GRUEN, der Suchbefehl des Plans meldet eine leere Liste |
| 10 | Die Vorbedingungsdatei ist reines ASCII | GRUEN, kein Zeichen ueber 127 |
| 11 | Die CI-Laufnummer ist am Tag dieses Plans neu geholt | GRUEN, 35469147833 statt 35462611738 aus der Recherche |
| 12 | Zeilenenden beider Dateien | GRUEN, LF, kein CR, auch im committeten Blob |
| 13 | `tests/test_measurement_scripts.py` | GRUEN, 348 bestanden |
| 14 | Volle Suite aus `backend/` | GRUEN, **2.380 bestanden, 15 uebersprungen**, unveraendert gegen 15-06 |

## Threat Flags

Keine neue Angriffsflaeche. Die vier Dispositionen des Bedrohungsregisters sind umgesetzt:
- **T-15-18** (Anmeldedaten oder Kennungen in der Rohdatei): nur die beiden Variablennamen ohne Werte, Platzhalter statt Pfad, `VolumeId` fortgelassen, und der Suchbefehl des Plans laeuft leer durch.
- **T-15-19** (eine Erwartung, die zur Erklaerung wird): E8 bis E14 stehen mit Zahlen im Commit `190d5c7`, vor jeder Box-Minute.
- **T-15-20** (vergessene Vorbedingung faellt in der bezahlten Zeit auf): acht abgearbeitet, zwei ausdruecklich `offen` mit dem Ort ihrer Pruefung, eine als Platzhalter des Checkpoints.
- **T-15-SC** (Paketinstallationen): keine. Das einzige genannte Paket ist `jq` aus der Distributionsquelle, und es ist Vorbedingung und keine Auslieferung.

## Runbook-Nachtraege fuer 15-15 (D-10)

- Die Aufrufform steht in `00-ablauf.md` Abschnitt 2.1 und gilt fuer beide Dokumente. Fuer 15-15 bleibt daraus **ein Satz fuer das Runbook**: die chmod-Zeile vor Block 13b, damit ein Leser, der nur das Runbook in der Hand hat, dieselbe Form findet. Vorgemerkt und nicht vergessen; die Anfahrt selbst ist durch die Ablaufdatei gedeckt, die der Operator ohnehin fuehrt.
- Der wirklich gezogene Digest und die wirklich gelesene CI-Laufnummer gehoeren in den Bericht, jeweils neben ihre hier notierte Erwartung.

## User Setup Required

None fuer diesen Plan. Was beim Owner liegt, liegt im Checkpoint 15-08: die Deckelfreigabe mit Datum (Vorbedingung 9) und der Zugang zur DNS-Verwaltung fuer `loadtest.infranode.dev` (Vorbedingung 8).

## Next Phase Readiness

- **15-08** (Deckelfreigabe) findet die Vorbedingungen abgearbeitet vor und bekommt zwei Zeilen zur Entscheidung vorgelegt: die Freigabe mit Datum und den DNS-Zugang. Die Zahlbasis ist gerechnet und gegengeprueft, und der Preisabgleich hat keine Abweichung ergeben.
- **15-09** (Anfahrt) findet die Schrittfolge mit zwoelf Zeilen, die chmod-Zeile vor Schritt 0 und die elf Abbruchwerte 29 bis 39 in der Datei, die der Operator waehrend der Anfahrt fuehrt.
- **15-13** (Belegkriterium) findet E14 vollstaendig ausformuliert vor, mit beiden Bedingungen und beiden Folgen. Was dort zu tun bleibt, ist das Urteil gegen die gemessenen Zahlen und nicht mehr die Festlegung des Kriteriums.
- **15-15** (Bericht) findet die Erwartungen E1 bis E14 an einer Stelle und kann jede Zahl neben ihre Erwartung stellen.
- **MESS-05 bleibt ungetickt.** Die Frontmatter dieses Plans fuehrt es, das Requirement gehoert aber an das Phasenende (15-16), so wie schon in 15-02 bis 15-06.

## Self-Check: PASSED

- `docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md` liegt auf der Platte.
- `docs/measurements/2026-09-v12-messung/rohdaten/02-vorbedingungen.txt` liegt auf der Platte.
- `190d5c7` und `c69624e` stehen in `git log`.

---
*Phase: 15-messphase-eine-box-anfahrt*
*Completed: 2026-09-19*
