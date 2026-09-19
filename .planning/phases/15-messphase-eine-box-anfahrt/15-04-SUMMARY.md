---
phase: 15-messphase-eine-box-anfahrt
plan: 04
subsystem: measurement-tooling
tags: [messwerkzeug, mem-02, grundlast, entladung, bodensatz, indexlauf, box-anfahrt]

# Dependency graph
requires:
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-01, das Laufverzeichnis, der Kopie-Waechter und TOOLS_THE_MEASUREMENT_ORDER_NAMES
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-02, Schritt 8b der Messreihenfolge und die Rueckgabewerte 31 bis 33 in Abschnitt 7.1
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-03, die Hausform des Werkzeugs, das Lesen von engineState an der Admin-Seite und die Position der Abbrueche
  - phase: 14-modell-entladung-im-leerlauf
    provides: FINDLING_EMBED_IDLE_RELEASE_SECONDS, engine_state() mit dem Wort unloaded, das offengelassene MEM-02
  - phase: 12-messwerkzeug-runbook-terminentscheid
    provides: 97-cron-vorpruefung.sh als Hausform, NARROW_SCOPE_DIRS und a_boxless_run
provides:
  - docs/measurements/2026-09-v12-messung/skripte/94b-grundlast-rueckkehr.sh, drei Marken in einem Zug, Rueckgabewerte 2, 29, 31, 32, 33
  - sieben boxlose Testfaelle des Werkzeugs in backend/tests/test_measurement_scripts.py
  - V12_BASELOAD_RETURN, MEASURE_OF_MEM_02, FORBIDDEN_MEASURE, BASELOAD_RETURN_ABORTS, RSS_SAMPLER, RSS_DIGEST und die zwei sha256-Sollwerte als benannte Konstanten
  - zwei weitere Runbook-Nachtraege fuer 15-15 (Beleg des Indexlaufs, Doppelbelegung von 32 und 33)
affects: [15-07-ablauf, 15-09-anfahrt, 15-15-bericht, 15-16-phasenabschluss]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Messgroesse, die eine bequemere Nachbarin hat, bekommt ein Gate gegen die Nachbarin und nicht nur einen Absatz im Kopf"
    - "Ein Gate ueber einen Wortlaut streicht Kommentare NICHT, wenn der Wortlaut auch in einer Erklaerung nicht stehen darf; ein Gate ueber eine Position streicht sie sehr wohl"
    - "Ein Pruefsummen-Waechter ueber eine Datei mit gemischten Zeilenenden rechnet ueber die Bytes ohne Wagenruecklauf, sonst ist er auf einer der beiden Maschinen rot"

key-files:
  created:
    - docs/measurements/2026-09-v12-messung/skripte/94b-grundlast-rueckkehr.sh
  modified:
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Der Indexlauf wird ueber den Weg eines Nutzers angestossen (WebDAV plus files:scan) und nicht ueber occ findling:index --restart, das 52.000 Dokumente neu in die Schlange stellte"
  - "Belegt wird der Indexlauf an der Zahl der eingebetteten Dokumente der Admin-Seite, weil der Zaehler indexed der Nextcloud-Seite strukturell null ist"
  - "Gerechnet wird ueber anon aus memory.stat und nicht ueber memory.current, weil der Seitencache des mmap-Index sonst mitzaehlte"
  - "Marke A verlangt einen Containerneustart vor der Messung, sonst ist sie keine Grundlast vor dem Indexlauf"
  - "Die Rueckgabewerte 32 und 33 tragen je zwei Faelle, den des Runbooks und den des Plans; keine Bedeutung faellt weg"
  - "Ein Entladeschalter auf 0 endet mit 29 wie eine fehlende Stellung: ohne Freigabe gibt es in diesem Block nichts zu messen"
  - "94b-grundlast-rueckkehr.sh tritt in TOOLS_THE_MEASUREMENT_ORDER_NAMES ein, im selben Commit wie die Datei"

patterns-established:
  - "Ein Werkzeug, dessen Messgroesse eine erfundene Nachbarin hat, nennt seine eigene woertlich und die Nachbarin nirgends, auch nicht im erklaerenden Kommentar"
  - "Ein Messblock, der den Bestand der Box beruehrt, raeumt hinter der letzten Marke wieder auf und protokolliert beides"

requirements-completed: []

# Metrics
duration: 35 min
completed: 2026-09-19
---

# Phase 15 Plan 04: Das Werkzeug der Messgroesse von MEM-02 Summary

**MEM-02 hat sein Werkzeug: `94b-grundlast-rueckkehr.sh` misst in einem Zug drei Marken, rechnet gegen die richtige von ihnen, belegt den Indexlauf an einer Zahl statt an einer Annahme, weist den Bodensatz aus statt ihn wegzurechnen, und ein Gate verbietet die bequemere Messgroesse im Quelltext, auch im Kommentar.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-09-19T22:00:00Z
- **Completed:** 2026-09-19T22:35:00Z
- **Tasks:** 2 von 2
- **Files modified:** 2 (1 neu, 1 geaendert)

## Accomplishments

- **Das eine offengelassene Requirement hat jetzt ein Werkzeug.** Die Abnahme der Phase 14 hat MEM-02 ausdruecklich offengelassen; sein Beleg faellt auf dieser Box oder gar nicht. Das Werkzeug steht vor der Box, weil Abschnitt 7.1 des Runbooks waehrend der bezahlten Anfahrt jede Aenderung an einem Werkzeug verbietet.
- **Drei Marken, eine Bezugszahl, und die richtige.** `marke-a-grundlast-vor-indexlauf` steht erklaerend daneben und sagt, wie weit die Freigabe zurueckfuehrt; gerechnet wird `marke-b-vor-der-entladung` minus `marke-c-nach-der-entladung`. Das ist der ganze Unterschied zwischen einer gemessenen und einer erfundenen Ersparnis: die Grundlast ist seit dem faulen Bau von Plan 07-03 bereits ohne Modell und ohne Cutter gemessen, und eine Differenz gegen sie zoege etwas ab, das in ihr gar nicht steckt.
- **Die verbotene Formulierung kommt in der Datei nicht vor, und ein Gate haelt das fest.** Es streicht Kommentarzeilen ausdruecklich **nicht**: der naechste Leser zitiert eine Erklaerung als Definition, und eine Rohdatei wird fuer sich gelesen, weit weg von dem Dokument, das den Satz zurechtgerueckt haette. Die gestellte Probe zeigt den Unterschied zum Pipeline-Gate, das Kommentare sehr wohl streicht, statt ihn zu behaupten.
- **Der Indexlauf wird belegt und nicht angenommen.** `indexlauf-vorher` und `indexlauf-nachher` fuehren die Zahl der eingebetteten Dokumente und den Arbeitsvorrat. Bewegt sich die erste nicht, endet der Lauf mit **33**: ohne Indexlauf ist die Messgroesse eine andere, und die Zahl waere die Grundlast eines Containers, der nie eingebettet hat. Gewartet wird auf zwei Bedingungen, bewegte Zahl **und** leerer Arbeitsvorrat, weil die Ruhezeit sonst an einem Container liefe, der noch zu tun hat.
- **Der Bodensatz steht als eigene Zeile da.** `bodensatz-mb` ist `marke-c` minus `marke-a`, mit dem Satz daneben, dass er nie zurueckkommt: die Modulimporte von onnxruntime und numpy bleiben geladen, auf aarch64 mit rund 16 MB gemessen. Wer ihn wegrechnet, verspricht eine Rueckkehr auf die Grundlast, die es nicht gibt.
- **Die beiden Helfer aus `scripts/ops/` werden unveraendert gerufen, und zwei sha256-Waechter halten das.** `git status --porcelain scripts/ops/` ist leer, und die Sollwerte sind aus den vorhandenen Dateien abgelesen und als Modulkonstanten festgehalten, nicht aus der Datei unter Test nachgerechnet.
- **Sieben boxlose Faelle belegen die Verweigerung, bevor die erste bezahlte Minute laeuft.** Vier parametrisierte Faelle (`vorher`, `nachher`, `--help`, `1`) enden mit 2, mit der Benutzung auf stderr, leerem `stdout` und leerem `tmp_path`; drei weitere halten die Messgroesse, die Position der vier Abbrueche und die Unveraendertheit der beiden Helfer.
- **Der Block raeumt hinter sich auf.** Der kleine Korpus des Indexlaufs wird nach der letzten Marke wieder entfernt und die Entfernung protokolliert, damit der Bestand der Box derselbe bleibt, gegen den Schritt 9 misst.

## Task Commits

Each task was committed atomically:

1. **Task 1: 94b-grundlast-rueckkehr.sh** - `ad4dc89` (feat)
2. **Task 2: Boxlose Tests und das Gate gegen die falsche Messgroesse** - `75f66a2` (test)

**Plan metadata:** siehe den docs-Commit dieses Plans

## Files Created/Modified

- `docs/measurements/2026-09-v12-messung/skripte/94b-grundlast-rueckkehr.sh` - das Werkzeug des Messschritts 8b, drei Marken, Rueckgabewerte 2, 29, 31, 32, 33
- `backend/tests/test_measurement_scripts.py` - `V12_BASELOAD_RETURN`, `MEASURE_OF_MEM_02`, `FORBIDDEN_MEASURE`, `BASELOAD_RETURN_ABORTS`, `RSS_SAMPLER`, `RSS_DIGEST`, die zwei sha256-Sollwerte, `lf_bytes_of()` und vier Testfunktionen (sieben Faelle); `94b-grundlast-rueckkehr.sh` in `TOOLS_THE_MEASUREMENT_ORDER_NAMES`

## Decisions Made

- **Der Indexlauf wird ueber den Weg eines Nutzers angestossen.** `occ findling:index` kennt genau zwei Schalter, `--status` und `--restart`, und `--restart` stellt den vollen Bestand der Box neu in die Schlange: rund 52.000 Dokumente, also Stunden, in denen der Container nie in den Leerlauf faellt und nie entlaedt. Ein Werkzeug, das so anstiesse, koennte seine eigene Messgroesse nie erreichen. Angestossen wird deshalb mit einem Dutzend kleiner Textdateien ueber WebDAV plus `files:scan`, dem Weg, den `98c-sprachfaelle.sh` seit Plan 12-06 geht.
- **Belegt wird der Indexlauf an der Admin-Seite, nicht an der occ-Ausgabe.** Der Plan nennt "Zeilenstaende aus `occ findling:index`". Die Ausgabe dieses Befehls kann die Frage nicht beantworten: ihr Zaehler `indexed` ist auf der Nextcloud-Seite strukturell null und sagt das in derselben Ausgabe selbst ("indexed is counted by the backend container and never written here"). Die Zahl der eingebetteten Dokumente steht im Feld `embedded` unter `backend` der Admin-Uebersicht, und dort liest das Werkzeug sie. Die occ-Ausgabe bleibt in denselben beiden Pflichtzeilen stehen und liefert den Arbeitsvorrat, der die zweite Wartebedingung ist.
- **Gerechnet wird ueber `anon` und nicht ueber `memory.current`.** Die Begruendung steht im Kopf von `scripts/ops/rss_sampler.sh` und gilt hier woertlich: `memory.current` zaehlt den Seitencache derselben cgroup mit, und der Tantivy-Index ist ein mmap auf der Platte. Eine Differenz darueber maesse zu einem guten Teil, wie viele Indexbloecke zwischen den Marken gelesen wurden. `memory.current` steht in jeder Marke daneben, weil der erste Leser, der den docker-Client fragt, genau diese Zahl bekommt und die Differenz erklaert finden soll statt versteckt.
- **Marke A verlangt einen Containerneustart vor der Messung.** Schritt 8b steht hinter den Schritten 4, 6 und 8; der Container ist dort laengst aufgewaermt. Ohne Neustart maesse Marke A einen Container mit Tokenizer, Splitter und Sitzung darin, waere also keine Grundlast vor dem Indexlauf, sondern eine zweite Marke B. Der Neustart hat einen zweiten Nutzen: er ist der Startzeitpunkt, gegen den bei Marke C geprueft wird, ob die Reihe ein Containerleben geblieben ist.
- **Die Rueckgabewerte 32 und 33 tragen je zwei Faelle.** Abschnitt 7.1 des Runbooks hat ihnen in 15-02 den fehlenden Bezugswert (32) und den neu gebauten Container (33) gegeben; der Plan 15-04 gibt ihnen die fehlende Zahl aus der Abtastreihe (32) und den ausgebliebenen Indexlauf (33). Beide Lesarten sind umgesetzt, statt eine von beiden zu streichen: eine einmal vergebene Zahl wird nicht umgehaengt, damit Rohdaten frueherer Laeufe lesbar bleiben (Entscheid 15-02).
- **Ein Entladeschalter auf 0 endet mit 29.** Der Plan verlangt 29 fuer die fehlende Stellung. Eine gelesene 0 ist keine fehlende Stellung, aber sie ist genauso toedlich fuer diesen Block: ohne Freigabe verginge die Ruhezeit ohne Wirkung, und die Zahl am Ende waere die Groesse eines Containers, der einfach nichts getan hat. `entladeschalter-passt-zum-block` benennt den Fall, und der Abbruch ist derselbe.
- **Die sha256-Waechter rechnen ueber die Bytes ohne Wagenruecklauf.** `scripts/ops/rss_digest.py` liegt in dieser Arbeitskopie mit CRLF und im Blob mit LF, weil die Datei ausgecheckt wurde, bevor `scripts/ops/*.py text eol=lf` in `.gitattributes` stand. Ein Waechter ueber die rohen Bytes waere auf genau einer der beiden Maschinen rot, gleichgueltig auf welcher er gemessen wurde, und ein Gate, das auf einem gruenen Baum rot ist, wird binnen einer Woche abgeschaltet.
- **`exit 2` steht oberhalb der Pipeline.** Das erste Akzeptanzkriterium von Task 1 verlangt alle fuenf Zeichenketten hinter der `tee`-Pipeline; fuer `exit 2` ist das nicht erfuellbar und nicht gewollt, weil derselbe Plan in Task 2 ein leeres Zielverzeichnis verlangt und die Pipeline die Rohdatei schreibt. Umgesetzt ist die Fassung aus Task 2, dieselbe Aufteilung wie in 15-03.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Der im Plan genannte Beleg des Indexlaufs kann den Indexlauf nicht belegen**

- **Found during:** Task 1
- **Issue:** Der Plan nennt "Zeilenstaende aus `occ findling:index` vor und nach dem Lauf" als Quelle fuer die Frage, ob sich der Stand der eingebetteten Dokumente bewegt hat. Diese Ausgabe fuehrt die Zahl nicht: `IndexCommand::status()` druckt den Arbeitsvorrat und die Endzustaende aus `findling_file_state`, und ihr `indexed` ist auf dieser Seite strukturell null. Ueber diesen Weg waere der Rueckgabewert 33 nie gefallen oder immer, und das Werkzeug haette seine Vorbedingung mit einer Zahl geprueft, die sich nie bewegt.
- **Fix:** Die beiden Pflichtzeilen fuehren die Zahl der eingebetteten Dokumente aus dem Feld `embedded` der Admin-Uebersicht, gelesen ueber dieselbe Anmeldung, die schon 15-03 geht, und daneben den Arbeitsvorrat aus der occ-Ausgabe als zweite Wartebedingung. Die Abweichung steht als eigener Kommentarabsatz im Kopf des Skripts.
- **Files modified:** `docs/measurements/2026-09-v12-messung/skripte/94b-grundlast-rueckkehr.sh`
- **Commit:** `ad4dc89`

**2. [Rule 1 - Bug] Ein Anstoss ueber `findling:index --restart` haette die eigene Messgroesse unerreichbar gemacht**

- **Found during:** Task 1
- **Issue:** Der naheliegende Anstoss eines Indexlaufs ist `occ findling:index --restart -n`, so machen es `93-nullstand.sh` und `96-volllauf.sh`. Hier waere er ein Fehler: er stellt rund 52.000 Dokumente in die Schlange, der Container arbeitet stundenlang, faellt nie in den Leerlauf und entlaedt nie. Der Lauf endete zuverlaessig mit 31, und zwar aus einem Grund, der kein Befund ist.
- **Fix:** Ein Dutzend kleiner Textdateien ueber WebDAV, `files:scan`, warten auf bewegte Zahl und leeren Arbeitsvorrat, Deckel `INDEXLAUF_DECKEL`. Der Korpus wird nach der letzten Marke wieder entfernt, und beide Schritte stehen im Protokoll, weil ein Messblock, der den Bestand der Box aendert, das sagen muss.
- **Files modified:** `docs/measurements/2026-09-v12-messung/skripte/94b-grundlast-rueckkehr.sh`
- **Commit:** `ad4dc89`

**3. [Rule 2 - Missing critical functionality] Marke A ohne Containerneustart waere eine zweite Marke B**

- **Found during:** Task 1
- **Issue:** Der Plan sagt fuer Marke A "die cgroup-Groesse des Containers, bevor irgendetwas eingebettet hat". Schritt 8b laeuft hinter den Schritten 4, 6 und 8; in diesem Containerleben hat laengst alles eingebettet. Ohne Neustart traege Marke A Tokenizer, Splitter und Sitzung, und der ausgewiesene Bodensatz waere negativ oder nahe null, also genau die Zahl, die dieser Block nicht erfinden darf.
- **Fix:** Containerneustart, Bereitschaft an der Admin-Seite abgefragt, dann Marke A. Der Startzeitpunkt wird festgehalten und bei Marke C gegengeprueft; weicht er ab, endet der Lauf mit 33 (der Fall des Runbooks).
- **Files modified:** `docs/measurements/2026-09-v12-messung/skripte/94b-grundlast-rueckkehr.sh`
- **Commit:** `ad4dc89`

**4. [Rule 2 - Missing critical functionality] Das neue Werkzeug fehlte in der Vollstaendigkeitsliste der Messreihenfolge**

- **Found during:** Task 1
- **Issue:** 15-01 hat `TOOLS_THE_MEASUREMENT_ORDER_NAMES` mit der Zusage angelegt, dass die Werkzeuge der Plaene 15-04 bis 15-06 die Liste mit ihren eigenen Plaenen betreten. Task 2 des Plans nennt diesen Schritt nicht. Ohne ihn waere die Liste eine Vollstaendigkeitspruefung, die ein Werkzeug der Messreihenfolge nicht kennt.
- **Fix:** `94b-grundlast-rueckkehr.sh` steht in der Liste, die Zahl im Waechter ist von 15 auf 16 gezogen, im selben Commit wie die Datei (Projektregel).
- **Files modified:** `backend/tests/test_measurement_scripts.py`
- **Commit:** `ad4dc89`

### Abweichungen vom Wortlaut der Akzeptanzkriterien

- **`exit 2` steht nicht unterhalb der Pipeline.** Das vierte Akzeptanzkriterium von Task 1 verlangt alle fuenf Zeichenketten hinter der `tee`-Pipeline. Fuer `exit 2` ist das nicht erfuellbar: derselbe Plan verlangt in Task 1 einen Abbruch, bevor irgendetwas angefasst wird, und in Task 2 ein leeres `tmp_path`; die Pipeline schreibt die Rohdatei. Task 2 loest den Widerspruch selbst auf und prueft nur 29, 31, 32 und 33 unterhalb des Schnitts. Umgesetzt ist die Fassung aus Task 2, und ein Testfall haelt beide Seiten: die vier darunter, `exit 2` darueber.
- **Die Marken tragen zwei Zahlen statt einer.** Neben `marke-x-...` steht je eine Zeile `marke-x-memory-current`. Gerechnet wird ausschliesslich mit `anon`; die zweite Zahl steht da, weil der docker-Client sie zeigt und ein Leser die Differenz erklaert finden soll.

## Runbook-Nachtraege fuer 15-15 (D-10)

Zwei weitere Stellen kommen zu den beiden Nachtraegen aus 15-03 dazu:

1. **Abschnitt 8b, Beleg des Indexlaufs.** Dass die Zahl der eingebetteten Dokumente nur an der Admin-Seite zu haben ist und nicht aus `occ findling:index`, gehoert in den Schritt, in dem sie gebraucht wird.
2. **Abschnitt 7.1, Rueckgabewerte 32 und 33.** Beide tragen jetzt je zwei Faelle. Die Tabelle nennt bisher nur einen davon; der zweite gehoert daneben, mit dem Satz, dass keine Bedeutung weggefallen ist.

## Known Stubs

Keine. Das Skript hat keinen Pfad, der eine Zahl erfindet: wo eine Quelle nicht antwortet, steht `unlesbar`, `unbekannt`, `unklar` oder `unbestimmt`, und keines dieser Worte geht als Zahl durch. Eine Differenz aus einem Wort ist `unbestimmt` und ausdruecklich nicht null, weil eine Null sich als gemessene Null laese. `99c-filter-sortierung.sh` und `92b-wechsel.sh` fehlen weiterhin im Laufverzeichnis; das ist die Reihenfolge dieser Phase (15-05 und 15-06) und kein Stub dieses Plans.

## Issues Encountered

Ein Werkzeug, das die Box nicht hat, kann boxlos nur an seinen Verweigerungspfaden und an seinem Wortlaut geprueft werden. Die Messpfade selbst (Neustart, Upload, Indexlauf, Ruhezeit, Abtastung, Digest) sind auf dieser Maschine nicht fahrbar; belegt sind Syntax, Aufrufvertrag, die Position der Abbrueche, die Messgroesse und die Unveraendertheit der beiden Helfer. Der erste echte Lauf ist Schritt 8b der Anfahrt, und Abschnitt 7.1 verbietet dann jede Aenderung am Werkzeug: was dort auffaellt, wird notiert und nach dem Abbau korrigiert.

## Verification

| Nr | Pruefung | Ergebnis |
|----|----------|----------|
| 1 | `sh -n` auf dem neuen Skript | GRUEN |
| 2 | Die Messgroesse steht woertlich in der Datei (drei Fundstellen) | GRUEN |
| 3 | Die Gegenformulierung steht an keiner Stelle, Kommentare eingeschlossen | GRUEN, null Fundstellen |
| 4 | `exit 29`, `exit 31`, `exit 32`, `exit 33` unterhalb der `tee`-Pipeline, `exit 2` oberhalb | GRUEN, Testfall mit gestellter Probe |
| 5 | Boxlose Verweigerung: 2, leeres `stdout`, leeres Zielverzeichnis, vier Gestalten | GRUEN, vier parametrisierte Faelle plus Handprobe |
| 6 | Die fuenf Marken- und Ergebniszeilen sind vorhanden | GRUEN, alle fuenf |
| 7 | `rss_sampler.sh` und `rss_digest.py` werden gerufen, `git status --porcelain scripts/ops/` ist leer | GRUEN |
| 8 | Die beiden sha256-Sollwerte stimmen mit dem Blob ueberein (Bytes ohne CR) | GRUEN |
| 9 | Gates ueber `NARROW_SCOPE_DIRS` fuer den neuen Pfad (Shebang, CR, Dash, Maschinenpfad, Passwort) | GRUEN, fuenf zusaetzliche Faelle |
| 10 | `-k "baseload_return_tool"` waehlt mindestens sieben Faelle | GRUEN, 7 bestanden, 317 abgewaehlt |
| 11 | `ruff check`, `ruff format --check`, `pyright`, `vulture` | GRUEN, alle vier ohne Befund |
| 12 | Volle Suite aus `backend/`, Skipzahl unveraendert | GRUEN, 2.356 bestanden, **15 uebersprungen** (unveraendert gegen 15-01 bis 15-03) |
| 13 | Kein Em-Dash, kein Umlaut, kein Emoji im Skript | GRUEN, die Datei ist durchgehend ASCII |
| 14 | Zeilenenden wie bei den Geschwistern | GRUEN, LF, kein einziges CR |

Zur Testzahl: 2.344 im Stand 15-03, plus fuenf Faelle der engen Gate-Familien ueber den einen neuen Pfad, plus sieben neue Faelle ergibt 2.356. Die Rechnung geht ohne Rest auf, es ist also kein Fall stillschweigend verschwunden.

## Threat Flags

Keine neue Angriffsflaeche. Die vier Dispositionen des Bedrohungsregisters sind umgesetzt: T-15-09 (Marke A steht erklaerend daneben, gerechnet wird gegen Marke B, und ein Gate verbietet die Gegenformulierung im Quelltext), T-15-10 (Rueckgabewert 33 an der Zahl der eingebetteten Dokumente), T-15-11 (sha256-Waechter ueber beide `scripts/ops/`-Helfer), T-15-SC (keine Abhaengigkeit wird installiert; das Skript ist POSIX-`sh` und nutzt `docker`, `curl`, `sed`, `awk` und `python3` fuer den vorhandenen Digest). Das Passwort reist wie in 15-03 ueber den NAMEN einer Umgebungsvariablen in eine Datei mit `chmod 600` und steht in keinem Argument (T-15-06).

## User Setup Required

None. Der Owner-Checkpoint 15-08 (Deckelfreigabe) ist von diesem Plan nicht beruehrt und steht weiter vor Welle C.

## Next Phase Readiness

- **15-05** (`99c-filter-sortierung.sh`, der Owner-Messblock D-01) kann anschliessen und findet hier dasselbe Muster wie 15-03 es hinterlassen hat, ergaenzt um zwei Dinge: ein Gate gegen die bequemere Messgroesse und ein Aufraeumen hinter einem Block, der den Bestand der Box beruehrt.
- **15-07** (`00-ablauf.md` auf zehn Schritte) kann den Aufrufvertrag `94b-grundlast-rueckkehr.sh` ohne Argument und den Rohdateinamen `94b-grundlast-rueckkehr.txt` uebernehmen, dazu die Stellschrauben `RUHEZEIT`, `KARENZ`, `ABTASTINTERVALL` und `INDEXLAUF_DECKEL`.
- **15-15** (Bericht) nimmt die zwei Runbook-Nachtraege oben auf, zusaetzlich zu den zweien aus 15-03.
- **MEM-02 bleibt ungetickt.** Dieser Plan baut das Werkzeug; der Beleg entsteht auf der Box (Schritt 8b der Anfahrt). **MESS-05 bleibt ebenfalls ungetickt**, es gehoert an das Phasenende (15-16), obwohl die Frontmatter des Plans beide fuehrt.

## Self-Check: PASSED

- `docs/measurements/2026-09-v12-messung/skripte/94b-grundlast-rueckkehr.sh` auf der Platte gefunden, `sh -n` fehlerfrei.
- `backend/tests/test_measurement_scripts.py` traegt `V12_BASELOAD_RETURN` und die vier neuen Testfunktionen.
- Beide Task-Commits liegen in der Historie: `ad4dc89`, `75f66a2`.
- Keine Loeschung in beiden Commits (`git diff --diff-filter=D` leer).
- Volle Suite aus `backend/` gruen (2.356 bestanden, 15 uebersprungen).

---
*Phase: 15-messphase-eine-box-anfahrt*
*Completed: 2026-09-19*
