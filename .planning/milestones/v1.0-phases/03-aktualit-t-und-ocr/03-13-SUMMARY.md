---
phase: 03-aktualit-t-und-ocr
plan: 13
subsystem: testing
tags: [ci, github-actions, ocr, tesseract, reconcile, idx-04, dach, gate-b, sandbox, corpus]

# Dependency graph
requires:
  - phase: 03-09
    provides: "Route.OCR, die Frist je Auftrag und der OCR-Zweig des Pollers"
  - phase: 03-10
    provides: "die vier Bildtypen auf beiden Allowlists, die Bildspur und das Paritaets-Gate"
  - phase: 03-12
    provides: "Reconcile.run_once(), der Abgleich als eigene Task, docs/reconcile.md"
  - phase: 03-06
    provides: "der erweiterte Referenzkorpus mit 33 Dateien und testdata/CORPUS.md"
  - phase: 02-indexkern-und-volltextsuche
    provides: "integration.yml mit readonly-gate und index-search-e2e, die Setup-Composite-Action"
provides:
  - "readonly-gate laeuft die ganze Indexierung inklusive OCR-Spur und vergleicht Pruefsummen, Metadaten und Dateiliste danach"
  - "Verdikt-Zaehler: je Korpusdatei genau ein Verdikt, gepruefte Referenz aus testdata/CORPUS.md, plus Deckel-Zaehler"
  - "workflow_dispatch-Schalter missing_verdict_probe als Falsifikation des Zaehlers"
  - "reconcile-and-dach: der IDX-04-Abnahmetest woertlich, mit Nachweis, dass keine Queue-Zeile entstand"
  - "drei DACH-Suchen als Dauergate: ss, scharfes s, oesterreichische Wortform"
  - "timeout-minutes auf allen vier Jobs von integration.yml"
  - "testdata/CORPUS.md nennt je Datei das gemessene Endverdikt und ist maschinenlesbare Referenz"
  - "docs/testing.md nennt die drei Abnahmen der Phase mit ihren Grenzen"
  - "docs/german-analyzer.md: DACH-Abschnitt mit gemessenen Trefferzahlen und der vierten Grenze"
  - "extract/sandbox.py reicht die erzwungene Route ueber die Prozessgrenze"
affects: [04, 05, phasenweiter-integrationsschritt]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Gate darf nicht gruen sein koennen, ohne etwas beruehrt zu haben: neben dem Vergleich steht ein Zaehler, der die Beruehrung belegt"
    - "Die Referenz eines CI-Zaehlers ist ein Dokument im Repository, nicht eine Konstante im Workflow; der Parser prueft sich zuerst selbst"
    - "Jede Falsifikation ist ein Schalter im Job (tamper_probe, missing_verdict_probe), keine Notiz in einem Dokument"
    - "Abnahmen ueber gescannte Inhalte laufen ueber Suchbegriffe, nie ueber erkannten Rohtext"
    - "Ein Negativbefund braucht seine Kontrolle davor: erst findbar, dann nicht mehr findbar"

key-files:
  created: []
  modified:
    - .github/workflows/integration.yml
    - testdata/CORPUS.md
    - docs/testing.md
    - docs/german-analyzer.md
    - docs/ocr.md
    - backend/src/findling/extract/sandbox.py
    - backend/tests/test_sandbox.py
    - .planning/phases/03-aktualit-t-und-ocr/deferred-items.md

key-decisions:
  - "Gate B bleibt ein Job fuer sich und bekommt die OCR-Spur dazu; die beiden Abnahmen mit Suche stehen in einem eigenen vierten Job, damit ein rotes Nur-Lesen-Verdikt nie nach kaputter Suche aussieht"
  - "Die Referenz des Verdikt-Zaehlers ist die Verdikt-Spalte von testdata/CORPUS.md; eine Korpusdatei ohne Zeile dort laesst den Job rot werden, bevor ueberhaupt gezaehlt wird"
  - "Die Verdikte wurden im Laufzeitimage ueber den ganzen Korpus gemessen, Textdurchlauf plus je ein OCR-Durchlauf, statt aus der Doku abgeleitet"
  - "Der IDX-04-Test blockiert die Ereignisse ueber occ files:scan statt ueber eine Testvariable: keine Testschalter im Produktionspfad, und es ist genau der Fall, an dem der Vorgaenger gescheitert ist"
  - "FINDLING_RECONCILE_ENABLED=false auf Job-Ebene macht aus genau ein Abgleichzyklus eine Tatsache statt einer Hoffnung"
  - "Der IDX-04-Test arbeitet in einem eigenen Ordner und nie im Korpus, dessen Unveraenderlichkeit ein anderer Job byteweise misst"
  - "Die DACH-Abnahme prueft Suchbegriffe; ein Rohtextvergleich waere ein Test gegen die tesseract-Version"
  - "Januar findet Jaenner nicht: als vierte Grenze in docs/german-analyzer.md dokumentiert, nirgends zugesichert"

patterns-established:
  - "Selbstpruefung des Parsers vor der Pruefung der Daten: ein Muster, das nichts trifft, ist ein leeres gruenes Gate"
  - "Deckel-Zaehler werden vor jedem moeglichen Abbruch ausgegeben, damit sie auch im Protokoll eines roten Laufs stehen"

requirements-completed: [IDX-04, OCR-01, OCR-02]

# Metrics
duration: 95min
completed: 2026-09-01
---

# Phase 3 Plan 13: Die drei Abnahmen als Dauergates Summary

**Gate B laeuft jetzt die ganze OCR-Spur ueber alle 33 Korpusdateien und kann nicht mehr gruen sein, ohne etwas beruehrt zu haben; daneben stehen der IDX-04-Abnahmetest woertlich und die DACH-Zusage als drei Suchen, und die Grenze Januar findet Jaenner nicht steht als Grenze statt als stilles Versprechen.**

## Performance

- **Duration:** ca. 95 min (ohne die Sichtprobe)
- **Started:** 2026-09-01T15:10:00Z
- **Completed:** 2026-09-01T16:45:00Z
- **Tasks:** 4 (3 automatisch, 1 Sichtprobe des Owners)
- **Files modified:** 8

## Accomplishments

- Die Nur-Lesen-Invariante ist ueber den ganzen OCR-Korpus belegt: `readonly-gate` indexiert die 33 Dateien mit eingeschalteter Engine und vergleicht danach Pruefsummen, Zeitstempel, Groessen und die Dateiliste. Vorher lief dort nur der Download-Pfad, und genau der Renderer und die Engine sind die Spur, auf der das Vorgaengerprojekt Nutzerdaten zerstoert hat.
- Das Gate kann nicht mehr leer gruen sein. Der Verdikt-Zaehler prueft je Datei das Verdikt, das `testdata/CORPUS.md` fuer sie nennt, meldet fehlende, abweichende und mit Grabstein versehene Zeilen einzeln und zaehlt `truncated`, `timeout` und `out_of_memory` getrennt. Der Schalter `missing_verdict_probe` laesst ihn auf Wunsch rot werden.
- Der vierte Job `reconcile-and-dach` fuehrt IDX-04 woertlich aus: neue, geaenderte und entfernte Datei am Ereignisweg vorbei, Nachweis dass keine Queue-Zeile entstand, genau ein Abgleichzyklus, danach alle drei Faelle korrekt, die entfernte Datei fuer beide Nutzer verschwunden.
- Die DACH-Zusage ist ein Dauergate: das Schweizer Dokument ueber `Strasse` und ueber `Straße`, das oesterreichische ueber `Jänner`, jeweils genau ein Treffer, alles ueber die normale Suchroute und nie ueber erkannten Rohtext.
- Ein toter OCR-Pfad wurde dabei gefunden und geschlossen: die erzwungene Route erreichte das Sandbox-Kind gar nicht (siehe Abweichung 1). Ohne diesen Fix waere jeder OCR-Auftrag in einem `TypeError` gestorben, und die Unit-Suite haette es nie gesehen.
- Alle drei Erfolgskriterien haben ihre Grenzen schriftlich: `docs/testing.md` sagt je Abnahme, was sie beweist und was ausdruecklich nicht.

## Task Commits

1. **Abweichung vor Task 1: die erzwungene OCR-Route ueber die Sandbox-Grenze** - `5a31261` (fix)
2. **Task 1: Gate B ueber den OCR-Korpus, mit Verdikt-Zaehler** - `9adef25` (ci)
3. **Task 2: Der IDX-04-Abnahmetest, woertlich** - `d30b2c2` (test)
4. **Task 3: DACH-Abnahme ueber Suchbegriffe und die dokumentierte Grenze** - `8fdef47` (test)
5. **Notiz: zwei veraltete Stellen in dev-setup fuer den Integrationsschritt** - `d83d184` (docs)
6. **Task 4: Sichtprobe des Owners** - keine Codeaenderung in diesem Worktree; der dabei gefundene Fehler wurde auf `main` behoben, Commit `21b2011`

**Plan metadata:** dieser Summary-Commit

## Files Created/Modified

- `.github/workflows/integration.yml` - OCR-Lauf und Verdikt-Zaehler im `readonly-gate`, neuer Job `reconcile-and-dach` mit IDX-04 und den drei DACH-Suchen, `timeout-minutes` auf allen vier Jobs, zweiter Dispatch-Schalter, `testdata/CORPUS.md` in den Pfad-Filtern, die veralteten Erwartungszahlen des e2e-Jobs korrigiert.
- `testdata/CORPUS.md` - die Verdikt-Spalte nennt jetzt das gemessene Endverdikt je Datei, inklusive der Bilder und der Scans, dazu der Absatz, wie die CI diese Spalte liest.
- `docs/testing.md` - Abschnitt ueber die drei Abnahmen der Phase, je mit dem Satz, was sie nicht beweisen.
- `docs/german-analyzer.md` - DACH-Abschnitt mit gemessener Trefferzahl je Begriff und die vierte bekannte Grenze.
- `docs/ocr.md` - Abschnitt, warum die DACH-Abnahme kein Rohtextvergleich ist, mit dem gemessenen Beleg aus dem Container.
- `backend/src/findling/extract/sandbox.py` - `route` als reiner String durch `run` und `extract_guarded`, Umwandlung in eine `Route` im Kind.
- `backend/tests/test_sandbox.py` - Regressionstest fuer die erzwungene Route ueber die Prozessgrenze, dazu die Anpassung des Grep-Tests auf die geaenderte Importzeile.
- `.planning/phases/03-aktualit-t-und-ocr/deferred-items.md` - zwei veraltete Aussagen in `docs/dev-setup.md`.

## Messungen

Vollstaendiger Pipelinelauf im Laufzeitimage `findling-ocr-09-test` ueber alle 33 Korpusdateien, Textdurchlauf zuerst und je ein erzwungener OCR-Durchlauf pro Uebergabe, also genau die Reihenfolge, die `worker/poller.py` erzeugt:

| Ergebnis | Zahl |
|---|---|
| indexed | 22 |
| skipped | 5 |
| failed | 6 |
| indexed(truncated), failed(timeout), failed(out_of_memory) | 0 |

Zweite Messung, echter Tantivy-Index mit echter Konstituentenliste und echtem Abfrage-Parser: `Strasse` 1 Treffer (15), `Straße` 1 Treffer (15), `Jänner` 1 Treffer (16), `Januar` 0 Treffer, `Bebauungsplan` 1 Treffer (13). Zusaetzlich geprueft, dass die sieben Sprachfaelle des bestehenden e2e-Jobs mit den OCR-indexierten Scans eindeutig bleiben (`Genehmigung`, `Frist`, `Mueller`, `Vertrag` und die Phrase je 1, `bescheid` 2, Ausschluss und Dateityp je 1) und dass die vier neuen Begriffe des Abgleichtests je genau eine Datei treffen.

Gegenprobe des Verdikt-Zaehlers, lokal gefahren mit dem aus dem Workflow extrahierten Skript gegen eine synthetische Zustandsdatenbank: sauberer Lauf gruen; fehlendes Verdikt der WebP rot mit der Meldung, warum das schlimmer ist als ein roter Pruefsummenvergleich; abweichendes Verdikt rot; Deckel-Verdikt rot; Grabstein rot; zerstoerte Referenztabelle rot.

## Sichtprobe des Owners (Task 4)

Im Auftrag des Owners vollstaendig durchgefuehrt, Ergebnis je Schritt:

| Schritt | Ergebnis | Beobachtung |
|---|---|---|
| 1 Hochladen | bestanden | Treffer mit Textauszug, nicht mit dem Pfad; beim ersten Poll findbar |
| 2 Umbenennen | bestanden | neuer Name nach 45 s findbar, alter Name 0 Treffer |
| 3 Gescanntes PDF | bestanden nach Gap-Fix | danach genau 1 Treffer auf `13-ratsvorlage-scan.pdf` mit echtem OCR-Snippet, `indexed`, `ocr_used=1`, 1635 Zeichen |
| 4 Foto und Icon | bestanden | `Zahlungsavis` trifft genau `17-beleg.jpg` (indexed, 89 Zeichen aus Pixeln), `22-icon.png` ohne Treffer und ohne Fehler, gemeldet als `skipped(image_not_ocrable)` |
| 5 Freigabe | bestanden | `kollegin` findet nach 45 s, nach Entzug sofort kein Treffer mehr, `testuser` weiterhin |
| 6 Loeschen und Wiederherstellen | bestanden | nach dem Loeschen sofort 0 Treffer fuer beide, nach der Wiederherstellung nach 34 s wieder findbar |
| 7 Laufzeit | bestanden | Provider-Antworten unter 1 s, Heartbeat auf 10035 durchgehend 200 |

**Der Gap, gefunden in Schritt 3 und geschlossen.** Die PDF-OCR-Zweitspur war in der echten Kette tot. `KIND_OCR` gab es in `backend/src/findling/nc/queue.py` und den Zweig im Poller ebenfalls, aber die Art fehlte in der Validierungsmenge `KINDS`. `_kind()` degradierte deshalb jede von der Requeue-Route erzeugte `ocr`-Zeile zu `content`, die Zweitspur beurteilte dieselben Bytes noch einmal als `skipped(no_text_layer)` mit `attempts=2` und `ocr_used=0`, und die Engine lief nie. Der Alt-Test `test_a_kind_this_container_does_not_know_is_a_content_job` schrieb dieses Degradieren von `ocr` sogar ausdruecklich fest, auf dem Stand vor Plan 03-09 und nie nachgezogen, und der Containertest aus 03-09 baute seine `kind=ocr`-Zeile am Parser vorbei und war darum gruen. Reproduziert mit `15-schweiz-baubewilligung.pdf`. Behoben auf `main` mit Commit `21b2011` "fix(03-09): let the ocr kind survive the queue boundary": `KIND_OCR` in `KINDS`, Kommentare nachgezogen, Alt-Test korrigiert, neuer Regressionstest `test_an_ocr_job_keeps_its_kind_across_the_queue_boundary`, 686 Tests gruen, live verifiziert mit beiden Scans als `indexed` und `ocr_used=1`.

Zwei Randnotizen des Laufs:

- `corpus/02-scan-no-text-layer.pdf` steht auf der lokalen Instanz noch auf dem alten `skipped(no_text_layer)` aus der kaputten Aera. Der naechste Abgleich- oder Reindex-Lauf zieht das nach, kein Handlungsbedarf.
- Der Host-Lauf nutzte tesseract 5.4 unter Windows mit `TESSDATA_PREFIX` im Nutzerverzeichnis, das Image nutzt 5.5. Die Zeichenzahlen weichen darum minimal von den Referenzen in `testdata/CORPUS.md` ab (1635 statt 1593, 508 statt 493). Die Suchbegriffe treffen identisch, was genau der Grund ist, warum diese Phase ueber Suchbegriffe abnimmt und nicht ueber erkannten Text.

**Nebenbefund ohne Findling-Bezug:** die OCS-Sharing-API der lokalen Instanz antwortete fuer jeden Pfad mit 404 "Falscher Pfad", auch fuer `Readme.md`; die Freigabe ueber die Files-Oberflaeche funktionierte einwandfrei.

## Decisions Made

- **Gate B bleibt ein Job fuer sich.** Die OCR-Spur kommt in den bestehenden `readonly-gate`, die beiden Abnahmen mit Suche in einen neuen vierten Job. Der Grund steht im Workflow selbst: ein rotes Nur-Lesen-Verdikt ist das schwerste Urteil dieses Projekts und darf nie mit einer kaputten Suche verwechselbar sein.
- **Die Referenz des Zaehlers ist ein Dokument, keine Konstante.** Der Schritt liest die Verdikt-Spalte von `testdata/CORPUS.md`. Eine neue Korpusdatei ohne Zeile dort laesst ihn rot werden, bevor er ueberhaupt zaehlt, und die Selbstpruefung des Musters steht vor allem anderen, weil ein Muster, das nichts trifft, ein leeres gruenes Gate ergibt.
- **Deckel-Zaehler vor dem ersten moeglichen Abbruch.** `truncated`, `timeout` und `out_of_memory` werden ausgegeben, bevor irgendeine Pruefung den Schritt beenden kann, damit sie auch im Protokoll eines roten Laufs stehen.
- **`occ files:scan` statt einer Testvariablen.** Eine Variable, die die Listener abschaltet, waere Testcode im Produktionspfad und stuende auf jeder Installation. Der Scan braucht keinen Schalter, ist die Form, die ein Massenimport und eine Backup-Wiederherstellung haben, und ist genau der Fall, an dem der Vorgaenger gescheitert ist.
- **Der Abgleich des Containers ist im ganzen Job abgeschaltet.** Ein Container, der noch nie einen Zyklus gefahren hat, haelt sich fuer faellig und wuerde irgendwann zwischen Manipulation und Messung selbst loslaufen. Mit `FINDLING_RECONCILE_ENABLED=false` auf Job-Ebene ist genau ein Zyklus eine Tatsache. Ein Neustart des Backends mit anderer Umgebung waere die Alternative gewesen und haette den armierten Zustand aus dem AppAPI-Handschlag verloren.
- **Der Abgleichtest fasst den Korpus nicht an.** Er arbeitet im Ordner `abgleich` mit eigenen Dateien, weil ein Test, der eine Korpusdatei umschreibt, die byteweise Messung des Nachbarjobs entwertet.
- **Zwei echte Umlaute im Workflow, sonst keine.** `Straße` und `Jänner` sind der Gegenstand der Pruefung und koennen nicht umschrieben werden. Alle anderen Testbegriffe sind bewusst ASCII.

## Deviations from Plan

### Auto-fixed Issues

**1. [Regel 1 und 3 - Fehler und Blockade] Die erzwungene OCR-Route erreichte das Sandbox-Kind nicht**

- **Found during:** Vorbereitung von Task 1
- **Issue:** `worker/poller.py` ruft im OCR-Zweig `extract_guarded(..., route=Route.OCR, timeout_seconds=...)` auf. Weder `extract_guarded` noch `ExtractionWorker.run` kannten einen `route`-Parameter, und das Auftragstupel auf der Pipe hatte vier Felder. Belegt mit `TypeError: extract_guarded() got an unexpected keyword argument 'route'`. Jeder OCR-Auftrag waere in der Produktion gestorben, bevor die Engine startet. Die Unit-Suite sah es nicht, weil der Extraktor-Ersatz in `test_poller.py` `route` annimmt. Das Summary von 03-09 beschreibt die Durchreichung als vorhanden, die Historie von `sandbox.py` enthaelt sie nie.
- **Fix:** `route` als `str | None` durch `run` und `extract_guarded`, fuenftes Feld im Auftragstupel, Umwandlung in eine `Route` im Kind, damit der Elternteil den Dispatcher weiterhin nie importiert. Dazu der Regressionstest `test_a_forced_route_survives_the_boundary`, der eine Textdatei als PDF anmeldet: die abgeleitete Route scheitert, die erzwungene liest sie.
- **Files modified:** `backend/src/findling/extract/sandbox.py`, `backend/tests/test_sandbox.py`
- **Verification:** ruff, ruff format, pyright (0 Fehler), vulture, 685 Tests gruen
- **Committed in:** `5a31261`

**2. [Regel 1 - Fehler] Die Erwartungszahlen des e2e-Jobs waren seit Plan 03-10 falsch**

- **Found during:** Task 1
- **Issue:** `index-search-e2e` erwartete 12 indexiert, 7 uebersprungen, 6 gescheitert und begruendete das damit, dass acht Bilddateien nie in den Container gelangen. Seit Plan 03-10 stehen die vier Bildtypen auf der Allowlist. Ohne Korrektur waere der Integrationslauf rot geblieben, und das Abnahmekriterium der ganzen Phase unerreichbar.
- **Fix:** Zahlen auf die gemessenen 22, 5, 6 gesetzt, den Kommentarblock auf den heutigen Stand gebracht, `DRAIN_TIMEOUT` von 420 auf 900 Sekunden angehoben, weil ein Dutzend gerenderter Seiten durch die Engine laeuft, und tesseract auch in diesem Job installiert. Ohne Engine waere jeder Scan ein ehrliches `failed(ocr_unavailable)` und die Messlatte die falsche.
- **Files modified:** `.github/workflows/integration.yml`
- **Verification:** Die 22/5/6 stammen aus dem Pipelinelauf im Laufzeitimage, und die sieben Sprachfaelle wurden gegen den echten Abfrage-Parser nachgemessen.
- **Committed in:** `9adef25`

**3. [Regel 2 - Fehlende Notwendigkeit] `testdata/CORPUS.md` fehlte in den Pfad-Filtern**

- **Found during:** Task 1
- **Issue:** Der Verdikt-Zaehler liest seine Referenz aus `testdata/CORPUS.md`, aber ein Commit, der nur diese Datei aendert, haette den Workflow nicht ausgeloest. Eine Referenz, die sich aendern kann, ohne dass das Gate laeuft, ist keine.
- **Fix:** `testdata/CORPUS.md` in `push` und `pull_request` aufgenommen.
- **Files modified:** `.github/workflows/integration.yml`
- **Committed in:** `9adef25`

**4. [Regel 2 - Fehlende Notwendigkeit] Deckel-Zaehler waren im roten Lauf unsichtbar**

- **Found during:** Task 1, waehrend der lokalen Gegenprobe
- **Issue:** In der ersten Fassung standen die Zaehler fuer `truncated`, `timeout` und `out_of_memory` hinter dem Vergleich je Datei. Ein Deckel-Verdikt weicht immer von der Referenz ab, also endete der Schritt vorher, und die Zahlen erschienen nie im Protokoll, also genau dann nicht, wenn sie gebraucht werden.
- **Fix:** Zaehler nach vorne gezogen und vor jedem moeglichen Abbruch ausgegeben, die Regel selbst als zusaetzlicher Befund erhalten.
- **Files modified:** `.github/workflows/integration.yml`
- **Verification:** Gegenprobe `truncated`: der Lauf meldet jetzt `cap verdicts: truncated=1` und zwei getrennte Fehlerzeilen.
- **Committed in:** `9adef25`

**5. [Regel 1 - Fehler, ausserhalb dieses Worktrees] Die `ocr`-Art ueberlebte die Queue-Grenze nicht**

- **Found during:** Task 4, Schritt 3 der Sichtprobe
- **Issue:** `KIND_OCR` fehlte in der Validierungsmenge `KINDS`, also degradierte `_kind()` jede Requeue-Zeile der zweiten Spur zu `content`. Die Engine lief nie, das Dokument bekam zum zweiten Mal `skipped(no_text_layer)`.
- **Fix:** Auf `main` behoben, Commit `21b2011`, mit korrigiertem Alt-Test und neuem Regressionstest.
- **Files modified:** ausserhalb dieses Worktrees
- **Verification:** 686 Tests gruen, live beide Scans `indexed` mit `ocr_used=1`
- **Committed in:** `21b2011` auf `main`

---

**Total deviations:** 5 (2 Fehler mit Blockadewirkung, 1 Fehler in den Erwartungswerten, 2 fehlende Notwendigkeiten), davon 4 in diesem Worktree behoben und einer auf `main`.
**Impact on plan:** Ohne die Abweichungen 1 und 5 waere keine einzige Aussage dieser Phase ueber OCR belegbar gewesen, und ohne 2 waere der Integrationslauf rot geblieben. Kein Zuwachs am Umfang: alle fuenf betreffen genau die Kette, die dieser Plan zum Dauergate machen soll.

## Issues Encountered

- **Die Verdikte der neuen Korpusdateien waren nirgends belastbar hinterlegt.** `testdata/CORPUS.md` fuehrte fuer die Bilder noch "never crawled in v1" und fuer die Scans den Uebergabezustand `skipped(no_text_layer)`. Geloest durch die Messung im Laufzeitimage und eine Verdikt-Spalte, die das Endverdikt nennt.
- **Die Engine auf dem Runner ist nicht die Engine im Image** (Ubuntu noble liefert eine 5.3er Reihe, Debian trixie 5.5.0). Bewusst so gelassen und im Workflow kommentiert: genau deshalb sind die Zusicherungen Verdikte und Suchbegriffe und nie erkannter Text.
- **`grep -ci 'j.nner'` ist locale-abhaengig.** In einer UTF-8-Locale liefert es 2, in der C-Locale 0, weil dort ein Punkt ein Byte matcht. Der Begriff steht zweimal woertlich als `Jänner` in `integration.yml`.

## Known Gaps

- **Der Integrationslauf selbst ist noch nicht gelaufen.** Dieser Auftrag durfte nicht pushen, also konnte `gh run list --workflow integration.yml` fuer keinen der drei Tasks belegt werden. Alles, was lokal pruefbar war, ist geprueft: YAML laedt, alle 62 `run`-Bloecke sind syntaktisch gueltige Bash, alle drei eingebetteten Python-Bloecke parsen, der Verdikt-Zaehler wurde extrahiert und in fuenf Varianten gefahren, jede Trefferzahl wurde gegen den echten Abfrage-Parser nachgemessen. Der erste echte Lauf gehoert in den phasenweiten Integrationsschritt.
- **Die beiden Falsifikations-Schalter sind auf GitHub noch nie ausgeloest worden.** `tamper_probe` stammt aus Phase 1, `missing_verdict_probe` ist neu. Beide sollten einmal von Hand ueber `workflow_dispatch` gefahren werden, damit die Aussage "das Gate wird rot" nicht wieder nur eine lokale Aussage ist.
- **`docs/dev-setup.md` beschreibt noch den Korpus aus Phase 2** und sagt nichts darueber, dass der lokale Host-Lauf ein eigenes tesseract braucht. Als Eintrag in `deferred-items.md` festgehalten, gehoert in den Integrationsschritt.

## User Setup Required

None - keine externe Dienstkonfiguration noetig. Fuer die lokale Sichtprobe braucht die Entwicklungsmaschine ein `tesseract` im PATH, weil das Backend dort als Host-Prozess laeuft; das steht in `deferred-items.md`.

## Next Phase Readiness

- Die fuenf Erfolgskriterien der Phase sind belegt: vier als CI-Gate, das fuenfte in der Sichtprobe.
- Phase 4 kann auf den Zaehlern aufsetzen: `ocr_used` und die Reason-Codes sind vollstaendig, und `testdata/CORPUS.md` ist die Referenz, gegen die eine Statusseite ihre Zahlen erklaeren kann.
- Offen fuer den Folgeplan am Poller bleiben die zwei Eintraege aus `deferred-items.md` zu Plan 03-10 (Frist fuer mehrseitige Bilder, `ocr_used` im Inhaltszweig).

## Self-Check: PASSED

- `.github/workflows/integration.yml`, `testdata/CORPUS.md`, `docs/testing.md`, `docs/german-analyzer.md`, `docs/ocr.md`, `backend/src/findling/extract/sandbox.py`, `backend/tests/test_sandbox.py`, `.planning/phases/03-aktualit-t-und-ocr/deferred-items.md`: alle vorhanden.
- Commits `5a31261`, `9adef25`, `d30b2c2`, `8fdef47`, `d83d184`: alle in `git log` dieses Worktrees vorhanden.
- Lokale Gates: ruff, ruff format, pyright, vulture, 685 Tests gruen.

---
*Phase: 03-aktualit-t-und-ocr*
*Completed: 2026-09-01*
