---
phase: 14-modell-entladung-im-leerlauf
plan: 12
subsystem: testing
tags: [audit, asvs, gates, acceptance, acl-parity, memory]

# Dependency graph
requires:
  - phase: 14-modell-entladung-im-leerlauf
    provides: Die Degradationsnaht aus 14-08, das sechste Wort aus 14-09, die neu formulierte Zusage aus 14-10 und die drei Dokumente aus 14-11
  - phase: 14-modell-entladung-im-leerlauf
    provides: Der Vorprueflauf und sein Urteil aus 14-02, das Tor der Phase
provides:
  - Ein Gesamtlauf aller sechs Gate-Stufen in einem Zug, protokolliert
  - Der Auditbericht der Phase mit Gate-Protokoll, ASVS V5/V7/V12, Bug- und Performance-Durchgang
  - Vier neue V4-Paritaetsfaelle: die entladene Runde bleibt hinter dem ACL-Vorfilter
  - Das Sichtprobenprotokoll an der laufenden Instanz, fuenf Erfolgskriterien nachgesehen
affects: [15-boxmessung, 16-store-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Audit-Pfad ohne Gate bekommt ein Gate, statt im Bericht als geprueft zu gelten"
    - "Eine Sichtprobe an der laufenden Instanz misst beide Stellungen und nennt den Abstand zur Decke, nicht nur ihr Unterschreiten"

key-files:
  created:
    - docs/audits/2026-09-phase-14/README.md
  modified:
    - backend/tests/test_semantic_search.py

key-decisions:
  - "Der fehlende V4-Paritaetsfall ist als Befund L-01 behoben und nicht nur protokolliert: die Runde unter may_load=False nimmt einen zweiten Weg durch die Fusion, und ein Weg ohne Gate ist kein geprueter Weg (Lehre aus 13-13)"
  - "Die PHP-Haelfte bekommt keinen eigenen Verhaltensfall, sondern einen Fall, der belegt, dass may_load in keiner PHP-Quelle steht: der finale Recheck kann auf einen Zustand nicht verzweigen, von dem er nie gehoert hat"
  - "Die Sichtprobe 4 wird mit ihrem Abstand zur Decke berichtet und nicht als blosses Unterschreiten: 1,37 bis 1,44 s gegen 0,41 bis 0,48 s warm ist eine duenne Marge, und die Zahl gehoert dem Owner vor die Abnahme"
  - "MEM-02 bleibt ungehakt, weil seine Beleg-Messgroesse ausdruecklich im Text des Requirements steht und auf der Box der Phase 15 entsteht"

patterns-established:
  - "Der Gesamtlauf laeuft zweimal: einmal als Grundstand gegen den Baum vor dem Audit und einmal als Protokolllauf gegen den Baum mit dem Befundfix"
  - "Die drei Stellungen einer neuen Umgebungsvariablen werden an der laufenden Instanz einzeln gefahren: ohne, gueltig, ungueltig"

requirements-completed: [MEM-01, MEM-03, MEM-04, MEM-05]

# Metrics
duration: 195min
completed: 2026-09-19
---

# Phase 14 Plan 12: Abnahme der Phase Summary

**Sechs Gate-Stufen in einem Zug gruen (2262 bestanden, 15 uebersprungen, kein neuer Skip), der Auditbericht der Phase steht mit einem behobenen und zwei weitergereichten LOW-Befunden, und die fuenf Erfolgskriterien sind an der laufenden Instanz nachgesehen: der Container gibt nach 75 s 376 MB zurueck und antwortet danach in 1,43 s lexikalisch.**

## Performance

- **Duration:** 195 min
- **Started:** 2026-09-19T20:05:00Z
- **Completed:** 2026-09-19T23:20:00Z
- **Tasks:** 2 von 2
- **Files modified:** 7 (eine Testdatei, ein neuer Auditbericht, zwei Dokumente nach dem Owner-Entscheid, drei Planungsdateien)

## Accomplishments

### Der Gesamtlauf, zweimal gefahren

Der Lauf ist zweimal gefahren: einmal als Grundstand gegen `eeda446`, den Baum
vor diesem Plan, und einmal als Protokolllauf gegen `b044ae4`, den Baum mit dem
Befundfix. Beide Male alle Stufen gruen, beide Male 15 uebersprungene Faelle.

| Stufe | Grundstand `eeda446` | Protokolllauf `b044ae4` |
|---|---|---|
| `ruff check .` | gruen | gruen |
| `ruff format --check .` | gruen, 123 Dateien | gruen, 123 Dateien |
| `pyright` | 0 errors, 0 warnings | 0 errors, 0 warnings |
| `vulture src tests --min-confidence 80` | gruen | gruen |
| `pytest -q` (VOLLE Suite) | 2258 bestanden, 15 uebersprungen, 215,5 s | **2262 bestanden, 15 uebersprungen, 200,3 s** |
| `ruff check`/`format` ueber `../scripts` | gruen, 10 Dateien | gruen, 10 Dateien |

Dazu die Stufen, die lokal nur teilweise fahrbar sind: `php -l` ueber das
Docker-Abbild `php:8.2-cli` fuer die drei in 14-09 geaenderten Dateien, alle
drei ohne Syntaxfehler; PHPUnit bleibt CI-Sache; die vier Text-Gates einzeln
nachgefahren, 89 bestanden.

**Die Skipzahl ist gegen 13-13 verglichen und unveraendert bei 15.** Alle 15
haengen an der Maschine (kein Modellartefakt, kein `tesseract`, keine
POSIX-Shell, zu wenige nutzbare Kerne, kein Korpusgenerator) und keiner an einer
Zusage. Kein Plan dieser Phase hat einen Skip hinzugefuegt, und keine Schwelle
ist gesenkt worden (T-14-44).

### Der Befund, der in diesem Lauf entstanden und behoben ist

**L-01: der V4-Paritaetsfall fehlte.** Das Research fuehrt V4 unter Vorbehalt:
die Runde unter `may_load=False` nimmt einen zweiten Weg durch die Fusion, und
am Baum gab es keinen Fall, der diese Runde gegen den ACL-Vorfilter stellt. Der
D-19-Pfad war gedeckt, die Rechtefrage unter ihm nicht.

Vier neue Faelle in `backend/tests/test_semantic_search.py`, Commit `b044ae4`:

| Fall | Was er haelt |
|---|---|
| `test_a_degraded_round_gives_a_user_without_a_permission_row_nothing` | carol ohne Rechtezeile bekommt nichts; die leere Vektorliste ist keine Abkuerzung am Vorfilter vorbei |
| `test_a_degraded_round_hands_out_exactly_the_permitted_documents` | alice bekommt genau die erlaubten Kennungen; ein Weg am Vorfilter vorbei waere als gesperrte Kennung sichtbar |
| `test_the_degraded_round_asks_the_prefilter_as_often_as_the_ordinary_one` | genau eine Vorfilterfrage je Runde in beiden Stellungen, und die entladene Runde traegt keinen Kandidaten hinein, den die volle nicht auch traegt |
| `test_the_php_recheck_knows_nothing_about_the_switch` | `may_load` steht in keiner PHP-Quelle |

Der dritte Fall war im ersten Anlauf rot mit einer Gleichheitsbehauptung, und
das war der Fall, der recht hatte: die volle Runde traegt die Beitraege des
Vektorzweigs mit an den Vorfilter, die entladene nicht. Die Behauptung ist
deshalb keine Gleichheit, sondern eine Teilmenge plus die Zahl der Fragen. Das
ist die staerkere Aussage: die Degradation darf weniger tragen, nie mehr, und
nie ohne zu fragen.

### Der Auditbericht

`docs/audits/2026-09-phase-14/README.md`, 383 Zeilen, kein U+2014 und kein
U+2013, sieben Abschnitte:

1. **Gate-Protokoll** mit Tabelle, Testzahl, Commit, den Ersatznachweisen und
   der Herkunft der 15 Skips.
2. **Security.** V5 gehalten (der bereichsgeprueter Leser, Bereich 60 bis 86400,
   Null vor dem Bereich, kein Pfad erhebt eine Ausnahme), V7 gehalten (genau
   **eine** eigene Protokollzeile im ganzen Baum, ohne Suchtext, Dateiname oder
   Zahl; `embed/engine.py` schreibt auf dem Entladeweg gar nichts), V12 gehalten
   (`ctypes.CDLL("libc.so.6")` als Literal, keine Variante mit Pfadargument),
   V4 geprueft mit behobenem Befund. Die fuenf Bedrohungsmuster je mit
   Gegenmassnahme und Stelle.
3. **Bug-Durchgang**, sechs Pfade: fuenf durch Testfall gedeckt (Indexlauf,
   Container ohne Modell, abgeschaltete Semantik, laufender Batch, libc ohne
   `malloc_trim`), einer erklaert und hingenommen (halb aktualisiertes App-Paar,
   T-14-36). Dazu L-02 als benannte Asymmetrie.
4. **Performance-Durchgang:** ein Takt im Ruhezustand kostet eine Uhrenlesung
   und vier billige Fragen; jeder blockierende Aufruf geht durch
   `asyncio.to_thread`, gehalten von einem Gate am Syntaxbaum; die
   Nachwaerm-Aufgabe wird nicht abgewartet; die Zahl steht im Messartefakt und
   nicht im Container-Log.
5. **Annahme A9 gegengeprueft und gehalten:** weder `vulture` noch `pyright`
   haben eine weitere Stelle des sechsten Worts aufgedeckt. Der Bericht zaehlt
   die Stellen aus dem Baum nach.
6. **Befundliste** und 7. was der Bericht nicht sagt.

### Die Sichtproben an der laufenden Instanz

Gefahren auf der Entwicklungsinstanz (Nextcloud 8090, Backend als Host-Prozess
auf 10035, Modell aus `.dev/model`, `FINDLING_EMBED_IDLE_RELEASE_SECONDS=60`).
**Die Instanz laeuft zum Zeitpunkt dieser SUMMARY weiter**, damit der Owner die
sieben Punkte ohne Wartezeit nachsehen kann.

**Sichtprobe 1, Vorprueflauf (Erfolgskriterium 1).** Gelesen.
`docs/measurements/2026-09-entladung-vorpruefung/README.md`: E1 bis E4 alle
gehalten, Median der Rueckgabe 100,0 Prozent ueber fuenf Zyklen auf aarch64,
Gesamturteil "Gehalten", Maschine und Abbilddigest genannt, Erwartung 29 Minuten
vor den Rohdaten festgeschrieben.

**Sichtprobe 2, der Schalter (Erfolgskriterium 2).** Drei Starts, drei
Protokolle:

| Stellung | Protokollzeile |
|---|---|
| ohne die Variable | keine Zeile ueber die Entladung (`grep -c` gleich 0 bei 18 Logzeilen) |
| `=60` | `INFO:findling:findling releases the embedding engine after an idle span` |
| `=3` | `WARNING:findling.config:FINDLING_EMBED_IDLE_RELEASE_SECONDS is outside the range this build was measured for, falling back to the default`, und keine Entladezeile: die Funktion bleibt aus |

Die Warnzeile nennt den Namen der Variablen und nicht ihren Wert, und der
Container ist in allen drei Stellungen gestartet und hat seinen Handschlag mit
AppAPI gemacht.

**Sichtprobe 3, beide Halter (Erfolgskriterium 3).** Eine Suche mit
semantischem Anteil als `testuser` ueber die Unified Search, danach Ruhe:

| Zeitpunkt | `engineState` | RSS des Backend-Prozesses |
|---|---|---|
| nach der Suche | `loaded` | 533,4 MB |
| nach 60 s | `loaded` | 533,5 MB |
| nach 75 s | **`unloaded`** | **157,2 MB** |

Also 376,3 MB zurueck, 70,5 Prozent des gehaltenen Bestandes, auf einer
Windows-Maschine **ohne** `malloc_trim`. Das Protokoll sagt es dazu:
`WARNING:findling.embed.model:this libc offers no malloc_trim, so a release keeps the freed blocks in the arena (FileNotFoundError)`.
Der Bug-Pfad 3.5 des Berichts ist damit nicht nur getestet, sondern an der
laufenden Instanz gesehen; die volle Rueckgabe misst die Box der Phase 15.

**Sichtprobe 4, die erste Suche danach (Erfolgskriterium 4).** Zwei
Entladezyklen, je eine Suche unmittelbar danach, gemessen als Gesamtzeit eines
Aufrufs der Unified-Search-Route von aussen:

| Lage | Zeit | Treffer |
|---|---|---|
| kalt, zweiwortige Zeile (hybrid gemeint) | 1,438 s / 1,434 s | 6, Volltexttreffer |
| kalt, einwortige Zeile (ohne Vektoranteil) | 1,369 s | Treffer vorhanden |
| warm, dieselben Zeilen | 0,483 s / 0,406 s / 0,435 s | 6 |

Die Decke ist gehalten, **aber die Marge ist duenn**: 60 bis 130 ms unter 1,5 s
auf dieser Maschine. Dass auch die einwortige Zeile, die den Vektorzweig gar
nicht betritt, 1,37 s braucht, sagt, woher der Aufschlag kommt: nicht aus der
Degradation, sondern aus dem Nachwaermlauf, der waehrend der Antwort auf einem
Arbeitsfaden die Gewichte liest. Die Zahl gehoert dem Owner vor die Abnahme und
steht deshalb hier und im Checkpoint.

Das Nachwaermen wirkt: nach beiden kalten Suchen stand `engineState` wieder auf
`loaded`, ohne dass jemand eine zweite Suche abgesetzt hatte.

**Kein `cURL error 28` an diesem Tag.** Das Nextcloud-Protokoll fuehrt insgesamt
zehn solche Zeilen, die juengste vom 18.09.2026 16:42 UTC, also vor diesem Lauf.
Waehrend der Sichtproben ist keine dazugekommen.

**Sichtprobe 5, die Zusage und die Seite (Erfolgskriterium 5).** Die
Admin-Seite im entladenen Zustand abgerufen: die serverseitig gerenderte
Engine-Zeile traegt den Satz
"Das Modell wurde zum Sparen freigegeben. Die naechste Suche antwortet mit
Volltexttreffern und laedt es im Hintergrund nach."
Die Browser-Haelfte zieht denselben Satz aus demselben Katalogschluessel
(`php/js/admin.js`, Zweig `case 'unloaded'`, und derselbe Wert in `de.js` wie in
`de.json`), beide Haelften sind also byteweise einig. Der Durchgang im Browser
nach dem ersten Poll des Skripts steht dem Owner zu und ist Punkt 5 des
Checkpoints.

**Sichtprobe 6, franzoesischer Wortlaut. Abgenommen wie vorgelegt.** Der Owner
hat den Satz
`Le modele a ete libere pour economiser de la memoire. La prochaine recherche repond avec des resultats en texte integral et le recharge en arriere-plan.`
(im Katalog mit Akzenten) am Checkpoint gelesen und **ohne Aenderung**
abgenommen. Keine der beiden franzoesischen Katalogdateien ist dafuer angefasst
worden; `docs/l10n-french.md` traegt jetzt den Abnahmevermerk vom 19.09.2026
anstelle des Hinweises, der den Satz als ungelesen auswies.

**Sichtprobe 7, der Sparvorschlag 900 s. Bleibt stehen, deutlicher
gekennzeichnet.** Der Owner hat entschieden, dass der Wert als Vorschlag stehen
bleibt und als Schaetzung klar erkennbar sein muss. `docs/embeddings.md` sagt
jetzt mit denselben Worten wie `config.py`, dass die Zahl geraten ist und bis
zur Messung der Phase 15 eine Schaetzung bleibt. `backend/appinfo/info.xml` ist
unveraendert, weil die Store-Beschreibung mit dem Release reist und der
Vorschlag dort richtig steht. **Befund L-03 ist damit geschlossen**, der Bericht
fuehrt ihn als behoben.

## Owner-Abnahme (Task 2, Checkpoint)

Vorgelegt wurden die sieben Punkte mit ihren gemessenen Ergebnissen. Die Antwort
des Owners vom **19.09.2026**, im Wortlaut:

> 1) Phase 14 gesamt: "abgenommen".
> 2) Der franzoesische Wortlaut des neuen Satzes: abgenommen wie vorgelegt;
>    datiere den Nachtrag in docs/l10n-french.md entsprechend (Owner-Abnahme
>    19.09.2026, Satz unveraendert).
> 3) Der Sparvorschlag 900 s bleibt stehen als klar gekennzeichnete Schaetzung;
>    ziehe dabei docs/embeddings.md auf die deutlichere Formulierung von
>    config.py (Befund L-03 schliessen).

Dazu die Auflage, MEM-02 ausdruecklich offen zu lassen, bis die Messung der
Phase 15 vorliegt.

**Was daraufhin geschehen ist**, alles im Commit `220b7e0`:

| Auflage | Umsetzung |
|---|---|
| Franzoesischer Wortlaut abgenommen | `docs/l10n-french.md` traegt den Abschnitt "Abnahme 19.09.2026 (Phase-Checkpoint 14-12)"; der Satz selbst ist unveraendert, beide fr-Kataloge sind nicht angefasst |
| 900 s als Schaetzung kennzeichnen | `docs/embeddings.md` sagt jetzt "Diese Zahl ist geraten und keine Messung" und zeigt auf die Phase 15, wie `config.py` es tut |
| Befund L-03 schliessen | `docs/audits/2026-09-phase-14/README.md`: L-03 steht als behoben, die Bilanz nennt zwei behobene und einen weitergereichten Befund |
| Der Docstring des Katalog-Gates | `test_admin_ui_contract.py` sagte "The French wording is new and unchecked"; das war ab der Abnahme falsch und ist nachgezogen |
| MEM-01, MEM-03, MEM-04, MEM-05 | in `.planning/REQUIREMENTS.md` abgehakt, die Nachweiszeile nennt die Abnahme |
| MEM-02 | bleibt ungehakt; die Zeile sagt jetzt ausdruecklich, dass die Abnahme dieses Requirement NICHT einschliesst |
| Abnahmesatz mit Datum | `.planning/STATE.md` |
| Phase 14 auf 12/12 | `.planning/ROADMAP.md`, Fortschrittstabelle, Planliste und Meilensteinzeile |

Nach der Abnahme ist `uv run pytest tests/test_admin_ui_contract.py -q` gruen
(das Kriterium des Plans fuer den Fall einer Korrektur am franzoesischen
Wortlaut; es gab keine Korrektur, das Gate ist trotzdem gefahren), und die volle
Suite ist ein zweites Mal gruen gelaufen.

## Task Commits

1. **Task 1a, der V4-Paritaetsfall** - `b044ae4` (test)
2. **Task 1b, der Audit-Durchgang** - `a41227a` (docs)

3. **Task 2, die Auflagen der Abnahme** - `220b7e0` (docs)

Task 2 ist der Owner-Checkpoint. Sein Entscheid selbst ist keine Aenderung; die
drei Auflagen, die er mitgibt, sind es.

## Tests

Vier neue Faelle, keiner mit einem Skip-Marker. Die volle Suite steht danach bei
2262 bestanden (vorher 2258) und unveraendert 15 uebersprungen.

Kein Produktivcode ist in diesem Plan angefasst worden, also sind
`PACKAGE_TREE_HASH_TODAY` und `PHP_TREE_HASH_TODAY` in
`backend/tests/test_measurement_scripts.py` unberuehrt geblieben; die Datei ist
in der vollen Suite gruen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Deckung] Der V4-Paritaetsfall ist angelegt worden**

- **Found during:** Task 1, Teil B, Abschnitt Security
- **Issue:** Der Plan sieht vor, den Fall anzulegen, falls er fehlt. Er fehlte.
- **Fix:** Vier Faelle in `backend/tests/test_semantic_search.py`
- **Verification:** 5 bestanden im Auswahllauf, 73 bestanden ueber die drei
  Rechtedateien zusammen, danach die volle Suite
- **Commit:** `b044ae4`

**2. [Rule 1 - Bug im eigenen neuen Fall] Die Gleichheitsbehauptung des dritten Falles war falsch**

- **Found during:** Task 1, erster Lauf der neuen Faelle
- **Issue:** Der Fall behauptete, die volle und die entladene Runde stellten dem
  Vorfilter dieselbe Kandidatenliste. Sie tun es nicht: der Vektorzweig traegt
  eigene Kandidaten bei.
- **Fix:** Die Behauptung ist jetzt eine Teilmengenbeziehung plus die Zahl der
  Fragen plus die Gleichheit des Nutzers. Das ist die Aussage, die V4 braucht.
- **Commit:** `b044ae4` (vor dem Commit behoben)

**Total deviations:** 2 auto-fixed (1 fehlende Deckung, 1 Bug im neuen Fall).
**Impact:** Keiner davon aendert den Umfang des Plans.

## Authentication Gates

Keine.

## Gates

| Gate | Ergebnis |
|---|---|
| `uv run ruff check .` | gruen |
| `uv run ruff format --check .` | gruen, 123 Dateien |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | gruen |
| `uv run pytest -q` (VOLLE Suite) | **2262 bestanden, 15 uebersprungen**, 200,34 s |
| `uv run ruff check --config pyproject.toml ../scripts` | gruen |
| `uv run ruff format --config pyproject.toml --check ../scripts` | gruen, 10 Dateien |
| `php -l` ueber `php:8.2-cli`, drei Dateien aus 14-09 | keine Syntaxfehler |
| die vier Text-Gates einzeln | 89 bestanden |

## Verification

| Punkt des Plans | Ergebnis |
|---|---|
| 1. Alle sechs Gate-Stufen in einem Zug gruen, protokolliert | ja, Tabelle oben und Abschnitt 1 des Berichts |
| 2. `docs/audits/2026-09-phase-14/README.md` existiert und traegt die vier Abschnitte | ja, plus Befundliste und Geltungsabschnitt |
| 3. Die fuenf Erfolgskriterien sind je mit einem Beleg verknuepft | ja, Abschnitt 5 des Berichts |
| 4. Kein U+2014 und kein U+2013 im Bericht | ja, beide Zaehlungen 0 |
| 5. Der Owner hat geantwortet | ja, 19.09.2026, "abgenommen"; die Antwort steht im Wortlaut oben |

## Issues Encountered

**Die Marge der ersten Suche nach einer Entladung ist duenn.** 1,37 bis 1,44 s
gegen eine Decke von 1,5 s auf dieser Entwicklungsmaschine, gegen 0,41 bis
0,48 s im warmen Zustand. Die Messung mit der einwortigen Zeile zeigt, dass der
Aufschlag nicht aus der Degradation kommt, sondern aus dem Nachwaermlauf, der
waehrend der Antwort laeuft. Auf einer langsameren Box koennte die Marge
aufgezehrt werden. Das ist kein Befund des Audits (die Zusage ist gehalten),
sondern eine Messgroesse fuer die Box der Phase 15, und sie liegt dem Owner am
Checkpoint vor.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsflaeche. Dieser Plan hat vier Testfaelle und ein oeffentliches
Dokument hinzugefuegt, keine Route, keinen Netzpfad, keinen Dateizugriff, keine
Schemaaenderung und keine Abhaengigkeit (T-14-SC).

Die fuenf Dispositionen des Plans:

| Threat ID | Erfuellt durch |
|---|---|
| T-14-44 (Gate gruen durch einen neuen Skip) | Skipzahl 15, gegen 13-13 verglichen, jede Herkunft im Bericht benannt |
| T-14-45 (Degradation umgeht den Vorfilter) | Vier Paritaetsfaelle, angelegt statt protokolliert |
| T-14-46 (Bericht nennt Bestandsgroessen oder Pfade) | Der Bericht nennt Gate-Zahlen und Quelltextstellen, keine Inhalte; vor dem Commit durchgesehen |
| T-14-47 (Franzoesischer Wortlaut gilt als geprueft) | Der datierte Nachtrag weist ihn als ungelesen aus, und er ist Punkt 6 des Checkpoints |
| T-14-SC | Keine Installation in diesem Plan |

## Requirements

`requirements: [MEM-01, MEM-02, MEM-03, MEM-04, MEM-05]`, und nach der Abnahme
sind **vier von fuenf** abgehakt.

- MEM-01, MEM-03, MEM-04 und MEM-05 standen seit ihren Bauplaenen abgehakt in
  `.planning/REQUIREMENTS.md`; dieser Plan hat sie an der laufenden Instanz
  nachgewiesen, und die Nachweiszeile der Rueckverfolgungstabelle nennt jetzt
  die Abnahme vom 19.09.2026.
- **MEM-02 bleibt offen.** Seine Beleg-Messgroesse steht ausdruecklich im Text
  des Requirements ("Rueckkehr zur Grundlast nach einem Indexlauf") und entsteht
  auf der Box der Phase 15. Die heutige Sichtprobe mit 376,3 MB auf einer
  Maschine ohne `malloc_trim` ist ein Hinweis und kein Beleg an dieser
  Messgroesse.

Der Owner hat das Offenbleiben von MEM-02 mit der Abnahme ausdruecklich
bestaetigt.

## User Setup Required

Keine externe Dienstkonfiguration. Fuer die Sichtproben laeuft die
Entwicklungsinstanz weiter: Nextcloud auf 8090, Backend auf 10035 mit
`FINDLING_EMBED_IDLE_RELEASE_SECONDS=60`.

## Next Phase Readiness

**Die Phase ist abgenommen und abgeschlossen**, 12 von 12 Plaenen.

Phase 15 ist die eine Box-Anfahrt. Sie erbt aus dieser Phase drei Auftraege:

1. **MEM-02 schliessen** an der Messgroesse "Rueckkehr zur Grundlast nach einem
   Indexlauf", im A/B ueber den Schalter dieser Phase.
2. **Die Wiederaufwaerm-Kosten messen.** Die Sichtprobe 4 zeigt auf der
   Entwicklungsmaschine 1,37 bis 1,44 s gegen eine Decke von 1,5 s; ob diese
   Marge auf der Box haelt, ist offen und gehoert in den A/B-Schritt 7.2 des
   Runbooks.
3. **Den Vorschlagswert 900 s belegen oder korrigieren.** Er ist heute eine
   gekennzeichnete Schaetzung an zwei Stellen.

## Gates nach der Abnahme

Die drei Auflagen beruehren zwei Dokumente und einen Docstring, also ist die
Kette ein zweites Mal gefahren:

| Gate | Ergebnis |
|---|---|
| `uv run ruff check .` | gruen |
| `uv run ruff format --check .` | gruen, 123 Dateien |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | gruen |
| `uv run pytest tests/test_admin_ui_contract.py -q` | 45 bestanden |
| `uv run pytest -q` (VOLLE Suite) | **2262 bestanden, 15 uebersprungen**, 210,11 s |

Kein Produktivcode angefasst, also keine Bewegung an
`PACKAGE_TREE_HASH_TODAY` und `PHP_TREE_HASH_TODAY`. Keine der beiden
franzoesischen Katalogdateien ist angefasst worden, weil der Wortlaut
unveraendert abgenommen wurde.

## Self-Check: PASSED

- `docs/audits/2026-09-phase-14/README.md`: vorhanden, traegt "Gate-Protokoll",
  zweimal "Erfolgskriterium" und L-03 als behoben.
- `backend/tests/test_semantic_search.py`: vorhanden, traegt die vier neuen
  Faelle.
- `docs/l10n-french.md`: traegt den Abnahmevermerk vom 19.09.2026.
- `docs/embeddings.md`: traegt "Diese Zahl ist geraten und keine Messung".
- Alle drei Commits (`b044ae4`, `a41227a`, `220b7e0`) stehen in der Historie.
- Keine Em-Dashes in dieser Zusammenfassung.

---
*Phase: 14-modell-entladung-im-leerlauf*
*Completed: 2026-09-19*
