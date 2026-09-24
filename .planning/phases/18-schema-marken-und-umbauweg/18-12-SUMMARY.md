---
phase: 18-schema-marken-und-umbauweg
plan: 12
subsystem: infra
tags: [ci, github-actions, upgrade-proof, rebuild, languages, schema-version, vectors, LEX-08]

# Dependency graph
requires:
  - phase: 18-schema-marken-und-umbauweg
    provides: "Plan 18-03: die sechste Marke languages im Bericht von findling.tools.index_status; Plan 18-09: rebuild_the_index als vierte Lifespan-Aufgabe; Plan 18-10: rebuildRunning, rebuildDone, rebuildTotal und languagesActive in GET /status und in der Overview der Adminseite"
  - phase: 16-store-abgabe-v12
    provides: "Der Release v1.2.0, aus dem die Upgrade-Strecke jetzt faehrt, und die Fassung der Zusicherung 6 auf den Datumsgrenzen des Providers"
  - phase: 11-store-installationsweg
    provides: "Der Block Store upgrade 0 bis 5, die geteilte Probe upgrade-probe.sh und die Regel, dass jeder Schritt seine Bedingung einzeln traegt"
provides:
  - "UPGRADE_FROM_TAG auf v1.2.0, mit dem Grund des Wechsels und beiden Vorgaengern auf Aktenlage"
  - "Zusicherung 6 auf der Sprachmarke statt auf den Datumsgrenzen, samt Kandidatenpruefung und umgestellter Gegenbedingung"
  - "snapshot() traegt marks.languages und container.rebuildState, letzteres mit Leerwertabbruch vor jq -n"
  - "Der Schritt Store upgrade 6 mit neun Zusicherungen ueber den Umbau"
  - "REBUILD_BUDGET_SECONDS, REBUILD_LANGUAGES und REBUILD_LANGUAGES_NORMALISED als benannte Werte im env-Kopf"
affects: [18-13, 18-14, 19]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine gestorbene Zusicherung wird ersetzt und nicht gestrichen: die Gegenbedingung vor dem Wechsel wandert in derselben Aenderung mit, weil Abwesenheit vorher das ist, was Anwesenheit nachher zu einer Aussage macht"
    - "Ein Zustandswechsel, der Sekunden dauert, braucht einen billigen Leser: das teure Werkzeug wird einmal vorbereitet (ein App-Passwort) und die Schleife macht danach nur noch einen Aufruf"
    - "Eine Messung mitten in einem Lauf wird eingeklammert: die Kanarienabfrage steht zwischen zwei Fortschrittsmessungen und die Momentaufnahme traegt beide, sonst ist mitten drin eine Behauptung"
    - "Eine Rekonstruktion eines Containers bricht bei jeder Form ab, die sie nicht versteht, statt sie zu raten: Netzwerkmodus, Entrypoint, Cmd, Mountart und das Zielvolume werden einzeln geprueft"
    - "Zwei Logfenster statt eines: --until fuer die Frage was waehrend des Laufs geschah, das ganze Log fuer die Frage wie oft etwas geschah"

key-files:
  created: []
  modified:
    - .github/workflows/deploy-harp.yml

key-decisions:
  - "container.rebuildState wird am Volume gelesen (Existenz von index.rebuild) und nicht in der Overview: rebuildRunning ist ein Prozesswert und meldet idle, wenn der Prozess weg ist, waehrend ein halb gebautes Verzeichnis auf der Platte liegt"
  - "Zusicherung 6 traegt beide Haelften in einem Vergleich: abwesend vorher UND genau de,en nachher; der zweite Teil ist der Gegenbeweis dazu, dass auf diesem Bein niemand eine Sprachmenge gesetzt hat"
  - "FINDLING_LANGUAGES wird als es,de,en gesetzt und de,en,es erwartet, damit Zusicherung 2 die Normalisierung wirklich prueft"
  - "Der Umbau wird durch Neubau des Containers aus seinem eigenen docker inspect ausgeloest, nicht durch eine zweite Registrierung; --net host macht die Rekonstruktion kurz und jede unverstandene Form bricht ab"
  - "Zusicherung 7 liest das Logfenster bis zum Ende des Umbaus, Zusicherung 8 das ganze Log; ein Indexierungspass nach dem Umbau ist gewoehnliche Arbeit und kein Verstoss"
  - "rebuild-env.list wird bewusst nicht als Artefakt kopiert: sie traegt APP_SECRET, und der Schritt gibt nur die Namen der Eintraege aus"
  - "REBUILD_BUDGET_SECONDS ist 300 und nicht die 900 des Indexierungspasses, weil der Umbau keine Datei liest; der Wert steht im env-Kopf mit der Herleitung daneben"

patterns-established:
  - "Der Leser einer Zustandsaenderung beweist sich selbst, bevor die Aenderung angestossen wird: der billige Overview-Leser muss den Ruhezustand sehen, sonst waere ein nicht gesehenes Banner kein Befund ueber das Banner"
  - "Vorbedingungen stehen vor dem Eingriff und Zusicherungen danach, und eine Vorbedingung, die trivial gruen waere (vectors.db abwesend), ist selbst ein Befund"

requirements-completed: [LEX-08]

# Metrics
duration: ~95min
completed: 2026-09-24
---

# Phase 18 Plan 12: Die umgedrehte Beweisstrecke Summary

**Die Upgrade-Strecke faehrt jetzt von v1.2.0 und bleibt dabei Zeile fuer Zeile stehen, ihre am Tagwechsel gestorbene sechste Zusicherung liest statt der Datumsgrenzen die neue Sprachmarke, und daneben steht ein zweiter Schritt, der den Umbau selbst in neun Zusicherungen beweist, von der Suche mitten im Lauf bis zur bytegleichen vectors.db.**

## Performance

- **Duration:** ~95 min
- **Completed:** 2026-09-24
- **Tasks:** 2 (je ein atomarer Commit)
- **Files created:** 0, **modified:** 1

## Accomplishments

- **`UPGRADE_FROM_TAG` steht auf `v1.2.0`, und der Grund steht dabei.** Der neue Absatz sagt, warum der Wechsel die schaerfste Aussage der Phase ist und nicht Aufraeumarbeit: 1.3.0 traegt einen Schemaschritt, also ist dies der eine Milestone, in dem "keine Marke bewegt sich" eine Aussage mit Zaehnen ist. Sie haelt nur, weil `schema_version` erst nach einem Umbau gestempelt wird und der Umbau unter der Werkseinstellung `de,en` gar nicht startet. Beide Vorgaenger (v1.0.3, v1.1.0) bleiben auf Aktenlage, mit der Lehre daneben, dass dieser Wert mit jedem Release schal wird.
- **Der bestehende Block ist unversehrt.** Der Diff entfernt ausserhalb der ersetzten Zusicherung 6 keine einzige Nicht-Kommentarzeile; gegengeprueft mit `git diff -U0 | grep '^-'` ueber den ganzen Block. Was sonst noch anders ist, sind nachgezogene Begruendungen an drei Stellen, deren Text mit dem Tag falsch geworden waere: die Navigations-Vorpruefung (sie schliesst jetzt alles unterhalb v1.1.0 aus statt alles ausserhalb 1.1.x), der Registry-Absatz (`:1.2.0` als das Image, das der Release von Phase 16 gepusht hat, mit beiden geprueften Vorgaengern daneben) und der Kopfkommentar von "Store upgrade 5".
- **Die gestorbene Zusicherung hat einen dokumentierten Nachfolger.** Die Kandidatenpruefung steht bei `index_report()`, in der Form, die der Block bei `declared_filters()` vorgibt, und nennt drei Kandidaten: die zwei Umbau-Banner von Plan 18-10 (auf einer ruhenden Installation beide falsch, also ausserhalb eines laufenden Umbaus stumm), `schemaVersion` selbst (bewegt sich unter der Werkseinstellung gerade nicht, eine Bewegungs-Zusicherung waere auf genau dem Lauf rot, den der Block gruen beweisen soll) und die Sprachmarke, die traegt.
- **Die Gegenbedingung ist mitgewandert.** "Store upgrade 3" verlangte bis heute die Abwesenheit der Datumsgrenzen; jetzt verlangt es `.marks.languages == null`. Der Bericht von 1.2.0 kennt den Schluessel nicht, also antwortet jq `null` und nicht die leere Zeichenkette, und dieser Unterschied steht als Satz daneben.
- **Zusicherung 6 traegt beide Haelften in einem Vergleich:** abwesend vorher und genau `de,en` nachher. Die zweite Haelfte ist keine Kosmetik: dieses Bein setzt kein `FINDLING_LANGUAGES`, also waere jeder andere Wert eine Sprachmenge, die niemand gesetzt hat, und der Umbau, der ihr folgen wuerde, ist genau das, was die fuenf Zusicherungen darueber gerade verneint haben.
- **`snapshot()` waechst um zwei Felder.** `marks.languages` kommt wie die anderen fuenf Marken aus `--argjson report`; `container.rebuildState` bekommt einen eigenen Helfer, eine eigene Shellvariable und einen eigenen Leerwertabbruch vor `jq -n` (T-18-12-03). Ein `unchanged`-Vergleich in "Store upgrade 5" nutzt den neuen Wert, damit er kein unbenutztes Feld ist.
- **"Store upgrade 6" beweist den Umbau in neun Zusicherungen,** jede mit einer Bedeutungszeile, alle ueber `fail=1` statt `exit 1`, und der Schritt traegt seine Bedingung ausgeschrieben wie jeder andere des Blocks.
- **Der Umbau wird durch einen Neubau des Containers ausgeloest, nicht durch eine zweite Registrierung.** Der Container wird aus seinem eigenen `docker inspect` wieder erzeugt, mit genau einem geaenderten Umgebungseintrag. Alles, was die Rekonstruktion nicht versteht, beendet den Schritt statt geraten zu werden: ein anderer Netzwerkmodus als `host`, ein ueberschriebenes `Entrypoint` oder `Cmd` (gegen das Image verglichen), eine Mountart ausserhalb volume und bind, ein fehlendes Zielvolume, eine leer gewordene Umgebungsliste.
- **Die mittlere Momentaufnahme existiert ueberhaupt erst durch einen billigen Leser.** `overview.sh` holt bei jedem Aufruf ein frisches App-Passwort, was eine Sekunde und mehr kostet; gegen einen Umbau ueber 39 Dokumente ist das zu grob. Der Schritt holt das Passwort einmal (auf beiden Wegen, die `overview.sh` kennt, und ohne den Wert je auszugeben) und macht danach pro Runde einen `curl`. Der Leser beweist sich selbst vor dem Neustart am Ruhezustand: ohne diesen Gegenbeleg waere ein nicht gesehenes Banner kein Befund ueber das Banner.
- **Die Kanarienabfrage ist eingeklammert.** Sie steht zwischen zwei Fortschrittsmessungen, beide muessen `rebuildRunning == true` melden, und die Momentaufnahme `rebuild-during.json` traegt beide samt `rebuildDone`/`rebuildTotal` und dem Trefferstand. Damit ist "mitten im Lauf" gemessen und nicht behauptet.
- **Die Wartelogik hat eine Obergrenze und eine Fehlermeldung.** `REBUILD_BUDGET_SECONDS = 300`, hergeleitet aus der Messung im Modulkopf von `index/rebuild.py` (683 Dokumente je Sekunde) und aus dem, wofuer das Budget wirklich bezahlt: Containerstart und Aufbau der sechs Analyseketten. Die Schleife pausiert 0,2 Sekunden, solange das Fenster offen sein kann, und zwei Sekunden, nachdem es erwischt wurde.
- **Zusicherung 9 misst am Artefakt.** `sha256sum` auf `vectors.db` im Container, vor und nach dem Umbau; eine vorher abwesende Datei ist eine Vorbedingung, die den Schritt beendet, weil zwei Abwesenheiten nichts ueber eine Neu-Einbettung sagen.
- Alle vier Gates gruen, volle Suite **2712 passed / 15 skipped**.

## Task Commits

1. **Task 1: Tagwechsel und Nachfolger fuer die gestorbene Zusicherung** - `ae28f09` (feat)
2. **Task 2: Store upgrade 6, der Umbau** - `36105cd` (feat)

## Files Created/Modified

- `.github/workflows/deploy-harp.yml` (3454 auf 4156 Zeilen)
  - env-Kopf: `UPGRADE_FROM_TAG` auf `v1.2.0` mit neuem Begruendungsabsatz und beiden Vorgaengern; neu `REBUILD_BUDGET_SECONDS`, `REBUILD_LANGUAGES`, `REBUILD_LANGUAGES_NORMALISED`, jedes mit Herleitung.
  - "Store upgrade 1": zwei nachgezogene Begruendungen (Navigationseintrag, Registry-Tag), keine geaenderte Pruefung.
  - Geteilte Probe: Kandidatenpruefung bei `index_report()`, neuer Helfer `rebuild_state()`, `snapshot()` um `marks.languages` und `container.rebuildState` samt Leerwertabbruch erweitert.
  - "Store upgrade 3": Gegenbedingung von den Datumsgrenzen auf die Sprachmarke umgestellt, mit beiden Vorgaengerfassungen auf Aktenlage.
  - "Store upgrade 5": Kopfkommentar nachgezogen, Zusicherung 6 ersetzt, ein `unchanged`-Vergleich auf `container.rebuildState`, Zusammenfassungszeile angepasst.
  - "Store upgrade 6": neuer Schritt, Zeile 3613 bis 4088 samt Kopfkommentar, mit Vorbedingungen, Containerneubau, Beobachtungsschleife und neun Zusicherungen.
  - Sammelschritt: sieben neue Beweisdateien in der Kopierliste, `rebuild-env.list` ausdruecklich nicht, Kommentar nachgezogen.

## Decisions Made

- **`container.rebuildState` wird am Volume gelesen, nicht in der Overview.** Die beiden beantworten verschiedene Fragen. `rebuildRunning` ist ein Prozesswert und meldet `idle`, sobald der Prozess weg ist, waehrend ein halb gebautes `index.rebuild` auf der Platte liegt. Ein Vorher-Nachher-Bild ist ein Bild des Volumes, also ist das Verzeichnis die richtige Quelle; die Overview wird in "Store upgrade 6" fuer die andere Frage gelesen, ob das Banner waehrend des Laufs oben war.
- **`FINDLING_LANGUAGES=es,de,en` und erwartet wird `de,en,es`.** Eine bereits sortierte Menge liesse eine Normalisierung, die nicht stattfindet, unbemerkt durchgehen. Die Marke ist das, wogegen der naechste Start vergleicht: eine unnormalisierte wuerde bei jedem Start einen Umbau bestellen. Spanisch und nicht Italienisch, Niederlaendisch oder Portugiesisch, weil der Owner-Entscheid E-17-3 und `docs/language-analyzers.md` an Spanisch geschrieben sind.
- **Zwei Logfenster.** `docker logs --until <Umbauende>` fuer Zusicherung 7, weil ein Indexierungspass NACH dem Umbau gewoehnliche Arbeit ist und kein Verstoss; das ganze Log fuer Zusicherung 8, weil die Driftzeile einmal pro Drift geschrieben wird und die Frage lautet, wie oft. Der Container ist frisch erzeugt, also ist sein Log genau der Umbaulauf und sein Nachlauf.
- **`pass finished, claimed=` ist das Muster des Extraktionspfads.** Der Extraktionspfad selbst schreibt keine Zeile (nachgesehen in `extract/` und `worker/`), aber jeder Pass mit geclaimten Zeilen schreibt diese eine. Ihre Abwesenheit ist die Abwesenheit jedes Passes, und ohne Pass gibt es weder Extraktion noch tesseract.
- **Der Neubau des Containers statt einer zweiten Registrierung.** So verlangt es der Plan, und der Preis dafuer ist eine Rekonstruktion, die abbricht statt zu raten. `--net host` (vom `app_api:daemon:register` weiter oben in derselben Datei gesetzt) macht sie kurz: keine Ports, keine Netzwerke, keine Aliase.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Der billige Overview-Leser samt eigenem App-Passwort**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt eine Momentaufnahme mitten im Lauf. Der vorhandene Weg zur Overview (`overview.sh`) holt bei jedem Aufruf ein frisches App-Passwort ueber `occ` beziehungsweise OCS; das kostet eine Sekunde und mehr. Der Umbau traegt 39 Dokumente, also waere der Leser groeber als das Fenster und die Zusicherung 3 waere ein Wuerfelwurf statt einer Messung.
- **Fix:** Der Schritt holt das App-Passwort einmal (dieselben zwei Wege wie `overview.sh`, in derselben Reihenfolge, der Wert wird nie ausgegeben) und macht danach pro Runde genau einen `curl`. Dazu die Gegenprobe des Lesers vor dem Neustart: er muss den Ruhezustand sehen, sonst bricht der Schritt ab.
- **Files modified:** `.github/workflows/deploy-harp.yml`
- **Verification:** Schrittskript mit `bash -n` geprueft; die Logik der Einklammerung gegen Attrappen gefahren (siehe Issues).
- **Committed in:** `36105cd`

**2. [Rule 2 - Missing Critical] Der Status der Kanarienabfrage wird aus dem Aufruf genommen, nicht aus einer Substitution**

- **Found during:** Task 2
- **Issue:** Die erste Fassung schrieb `hits=$(term_hits Belehrung || echo "")` und las danach `$?`. Damit war der Status immer 0, und ein fail-closed-Abbruch von `term_hits` (HTTP ungleich 200, unlesbarer Rumpf) waere als leere Trefferzahl durchgegangen, die sich wie "null Treffer" liest. Genau die Unterscheidung ist der Inhalt von Zusicherung 5.
- **Fix:** `if hits=$(term_hits Belehrung); then status=0; else status=1; hits=""; fi`, und die Zusicherung prueft `canaryFailed == false` UND `canaryHits >= 1`.
- **Files modified:** `.github/workflows/deploy-harp.yml`
- **Verification:** Gegenprobe gefahren: eine Momentaufnahme mit leerer Trefferzahl und `canaryFailed == true` faellt durch die Zusicherung.
- **Committed in:** `36105cd`

**3. [Rule 1 - Bug] Die Schleife pausierte nicht, wenn der Container nicht antwortete**

- **Found during:** Task 2
- **Issue:** Die erste Fassung pausierte nur, nachdem das Fenster erwischt war. Waehrend der Container hochfaehrt, antwortet die Overview mit `backendReachable: false` und HTTP 200, also waere die Schleife ohne Pause gegen eine gerade startende Instanz gelaufen.
- **Fix:** 0,2 Sekunden Pause, solange das Fenster offen sein kann, zwei Sekunden danach, mit dem Absatz daneben, warum die kurze Pause weder null noch eine Sekunde ist.
- **Files modified:** `.github/workflows/deploy-harp.yml`
- **Verification:** Schrittskript `bash -n`; die Bedingung ist unter beiden Zweigen erreichbar.
- **Committed in:** `36105cd`

**4. [Rule 2 - Missing Critical] Drei nachgezogene Begruendungen, die mit dem Tag falsch geworden waeren**

- **Found during:** Task 1
- **Issue:** Der Plan nennt eine Stelle (die Navigations-Vorpruefung). Zwei weitere Absaetze behaupteten nach dem Tagwechsel Unwahres: der Registry-Absatz nannte `:1.1.0` als das Image, das der Vorgaenger faehrt, und der Kopfkommentar von "Store upgrade 5" nannte die Datumsgrenzen als Inhalt der sechsten Zusicherung.
- **Fix:** Beide nachgezogen, jeweils mit dem Vorgaenger auf Aktenlage statt ueberschrieben, wie es der Stil dieser Datei verlangt.
- **Files modified:** `.github/workflows/deploy-harp.yml`
- **Verification:** `git diff -U0 | grep '^-'` zeigt ausserhalb der ersetzten Zusicherung keine entfernte Nicht-Kommentarzeile.
- **Committed in:** `ae28f09`

---

**Total deviations:** 4 auto-fixed (3 fehlende kritische Funktionalitaet, 1 Bug)
**Impact on plan:** Kein Scope-Zuwachs. Alle vier halten Zusicherungen ehrlich, die der Plan verlangt; ohne Nummer 1 und 2 waere Zusicherung 3 beziehungsweise 5 gruen, ohne gemessen zu haben.

## Issues Encountered

- **Keine der vier Gates prueft diese Datei inhaltlich.** `test_workflow_pins.py` prueft Pins und Job-Deadlines, `test_lockstep_versions.py` die Matrix gegen die zwei `info.xml`; beide waren und bleiben gruen, keine brauchte eine Aenderung. Statt sie nachzuruesten (das waere ein eigener Plan) wurde die Datei mit den Mitteln geprueft, die hier stehen: YAML ueber `yaml.safe_load` (49 Schritte, alle acht Upgrade-Schritte mit ausgeschriebener Bedingung), jeder der 45 `run`-Bloecke einzeln mit `bash -n` nach Ersetzung der GitHub-Ausdruecke, der Heredoc-Inhalt der geteilten Probe getrennt davon, und die jq-Ausdruecke gegen Attrappen gefahren.
- **Gegenproben statt Behauptungen, gefahren und wieder entfernt.** Drei Wegwerfskripte belegten: das `snapshot`-Objekt baut mit den zwei neuen Feldern; ein Bericht ohne den Schluessel `languages` antwortet `null` (die Form, auf die Zusicherung 6 und ihre Gegenbedingung sich stuetzen); das `rebuild-during`-Objekt baut und die Kanarien-Zusicherung liest es, waehrend eine leere Trefferzahl mit gesetztem Fehlerstand durchfaellt; die drei Aeste der ersten Zusicherung antworten ueber acht Wertepaare richtig, `null`, leer und ein Rueckschritt eingeschlossen; der Mount-Ausdruck baut `type=volume,...` und `type=bind,...,readonly`. Die Skripte sind nach dem Lauf geloescht, das Arbeitsverzeichnis ist sauber.
- **Ein Restrisiko, das bewusst stehen bleibt und nicht entschaerft wurde.** Zusicherung 3 und 5 haengen daran, dass das Fenster des Umbaus laenger ist als eine Runde des Lesers. Gemessen ist nur die Traggeschwindigkeit (683 Dokumente je Sekunde), nicht der Aufbau der sechs Analyseketten auf einem Runner; faellt das Fenster kuerzer aus als rund 0,3 Sekunden, wird der Schritt rot. Das ist die richtige Richtung, in die geirrt wird: ein rotes Gate ist ein Befund ueber die Messstelle, ein weiches Gate waere eine Zusicherung, die nichts sagt. Wenn es eintritt, ist die Antwort ein feinerer Leser oder ein groesserer Korpus, nicht ein gestrichener Vergleich.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: secret-handling | `.github/workflows/deploy-harp.yml` | Der neue Schritt nimmt ein App-Passwort des Admin-Kontos und haelt es in einer Shellvariablen. Es wird nie ausgegeben (nur seine Laenge) und lebt nur fuer die Dauer des Schritts auf einer Wegwerfinstanz. Im threat_model des Plans nicht benannt. |
| threat_flag: secret-handling | `.github/workflows/deploy-harp.yml` | `rebuild-env.list` unter `RUNNER_TEMP` traegt die ganze Umgebung des ExApp-Containers samt `APP_SECRET`. Sie wird bewusst nicht in die Artefakte kopiert, und der Schritt gibt nur die Namen ihrer Eintraege aus; beides steht als Kommentar an Ort und Stelle. Im threat_model des Plans nicht benannt. |

## Next Phase Readiness

- Die Strecke ist beidseitig: der bestehende Block beweist, dass ein Upgrade unter der Werkseinstellung nichts bewegt, der neue, dass ein Sprachwechsel den Umbau ausloest und dieser nichts kostet.
- Offen fuer den naechsten Plan beziehungsweise fuer den ersten gruenen Lauf: die Zahlen im Absatz zu `timeout-minutes: 45` sind weiterhin Schaetzungen aus Plan 06.1-12; der neue Schritt passt rechnerisch in die Marge (Containerstart plus hoechstens `REBUILD_BUDGET_SECONDS` plus zwei Momentaufnahmen), aber gemessen ist das erst nach dem ersten Lauf.
- Der erste Lauf der Strecke ist der Beleg fuer Erfolgskriterium 1 und 5 der Phase; bis dahin sind beide Behauptungen geschrieben und nicht gefahren.

## Self-Check: PASSED

- `.github/workflows/deploy-harp.yml` vorhanden, 4156 Zeilen
- `.planning/phases/18-schema-marken-und-umbauweg/18-12-SUMMARY.md` vorhanden
- Commit `ae28f09` in der Historie
- Commit `36105cd` in der Historie
- Keine Datei geloescht, Arbeitsverzeichnis sauber
- Der Diff der zwei Commits ist reines ASCII, also keine Em-Dashes und keine Umlaute in YAML

---
*Phase: 18-schema-marken-und-umbauweg*
*Completed: 2026-09-24*
