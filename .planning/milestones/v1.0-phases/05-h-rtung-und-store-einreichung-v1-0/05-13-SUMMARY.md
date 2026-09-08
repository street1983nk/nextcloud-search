---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 13
subsystem: infra
tags: [github-actions, supply-chain, pinning, ghcr, digest, provenance, slsa, postgres, timeout, ci-gate]

# Dependency graph
requires:
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: 05-01, die Composite Action setup-test-nc mit pgsql-Zweig und Extensionsliste, sowie das Muster der lokalen Registry im Deploy-Job
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: 05-09, der Job search-parity und das Muster eines Textgates mit Antivakuitaetsklausel
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: test_admin_ui_contract.py als Formvorbild jedes Textgates dieses Repositories
provides:
  - backend/tests/test_workflow_pins.py, ein Offline-Gate ueber alle Workflow-Dateien mit fuenf Regeln und fuenf Selbsttests
  - docker.yml prueft per Digest genau das Image, das nach ghcr geht (ein Bau je Architektur, Push per Digest, Pull per Digest, Smoke gegen den Digest)
  - ein Gate im merge-Job, das die Provenance-Bescheinigungen je Plattform nachzaehlt und ihre Subjekte prueft
  - jeder Job jeder Workflow-Datei traegt timeout-minutes, jede Zahl aus einem echten Lauf abgeleitet
  - pgsql als dritter Dialekt von index-search-e2e, mit einer eigenen Feststellung zum Postgres-Befund M7
  - aufgeloeste Wahrheit ueber alle gepinnten Actions dieses Repositories (siehe Tabelle unten)
affects: [Release-Plan v1.0.0, Phase-Review, jeder kuenftige Plan, der eine Action pinnt oder einen Job hinzufuegt]

# Tech tracking
tech-stack:
  added:
    - postgres:16 als Service-Container von index-search-e2e (nur CI, offizielles Image)
  patterns:
    - Ein Textgate ueber die Werkzeugkette selbst, nicht nur ueber den Produktivcode
    - Die Grenze eines Gates gehoert in seinen Docstring, samt der Angabe, wer den nicht abgedeckten Teil traegt
    - Ein per Digest gezogenes Artefakt statt eines Zwillings: Push-Digest und Pull-Digest stehen beide im Log
    - Jede Deadline nennt die Messung, aus der sie stammt, oder sagt ausdruecklich, dass es keine gibt

key-files:
  created:
    - backend/tests/test_workflow_pins.py
  modified:
    - .github/workflows/docker.yml
    - .github/workflows/integration.yml
    - .github/workflows/php.yml
    - .github/workflows/python.yml
    - .github/workflows/resilience.yml
    - .github/workflows/deploy-harp.yml
    - .github/actions/setup-test-nc/action.yml
    - .planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md

key-decisions:
  - "Der Smoke-Test laeuft gegen ein per Digest zurueckgezogenes Image statt gegen eine lokale Registry: das ist eine Identitaet und keine Gleichheit zweier Digests, und der Preis, ein unbenanntes Manifest nach einem roten Smoke-Test, steht als Kommentar in der Datei"
  - "actions/checkout wird auf 3d3c42e5 vereinheitlicht, also auf v7.0.1, weil zwanzig der einundzwanzig Aufrufe das ohnehin schon fuhren; der Kommentar wird korrigiert statt der SHA getauscht"
  - "Das Pin-Gate liest Text und keinen YAML-Baum, weil der Versionskommentar der Gegenstand von zwei seiner fuenf Regeln ist und ein YAML-Parser Kommentare verwirft"
  - "Regel 5 (eine SHA je Action im ganzen Repository) ist allgemein formuliert und nicht auf setup-uv beschraenkt; sie ist heute erfuellt und zwingt jeden kuenftigen Zweitpin zu einer Entscheidung"
  - "pgsql laeuft bei jedem Push und nicht auf einem Zeitplan: die drei Dialekte sind eine Matrix und laufen parallel, die Wanduhr des Jobs bewegt sich nicht (gemessen 2,5 bis 3,2 Minuten je Dialekt)"
  - "Die Provenance-Zusage wird nicht nur als Kommentar mit Datum festgehalten, sondern als Gate: der merge-Job zaehlt die Bescheinigungen nach und prueft, dass jede auf einer Plattform dieses Index sitzt"

patterns-established:
  - "Ein Gate ueber die Lieferkette gehoert neben die Gates ueber den Code, mit derselben Form: Befundliste, Antivakuitaetsklausel, Selbsttests"
  - "Eine Deadline ohne Messung ist eine Schaetzung und wird als solche benannt; wenn der Job dispatchbar ist, wird er einmal gefahren statt geschaetzt"
  - "Eine Pinnung wird mit gh api aufgeloest und die Ausgabe steht in der Zusammenfassung, weil das Gate diesen Teil offline nicht leisten kann"

requirements-completed: [PKG-05]

# Metrics
duration: 60min
completed: 2026-09-03
---

# Phase 5 Plan 13: Lieferkette und Postgres-Dauergate Summary

**Der Smoke-Test prueft ab jetzt per Digest genau das Image, das nach ghcr geht, ein Offline-Gate findet jede Pinnung, deren Kommentar luegt, jeder Job jeder Workflow-Datei hat eine gemessene Deadline, und Postgres, der Dialekt der Zielumgebung, laeuft bei jedem Commit mit einer eigenen Feststellung zum einzigen Postgres-Befund des Projekts.**

## Performance

- **Duration:** ca. 60 min
- **Tasks:** 3 von 3
- **Files modified:** 9 (1 neu, 8 geaendert)
- **Commits:** 6 Aufgaben-Commits plus dieser Abschluss
- **CI:** sechs Workflows auf dem Arbeitszweig gruen, siehe Belege unten

## Accomplishments

- **Sec-M7 ist geschlossen, und zwar als Identitaet und nicht als Wahrscheinlichkeit.** `docker.yml` baute zweimal je Architektur: einmal lokal fuer den Smoke-Test und ein zweites Mal fuer die Registry. Jetzt gibt es einen Bau, das Ergebnis geht per Digest nach ghcr, wird per Digest zurueckgezogen und der Container wird aus der Digest-Referenz selbst gestartet. Der Beleg steht im Log beider Architekturen: `push digest sha256:cd089b40...` und `pull digest ghcr.io/street1983nk/findling_backend@sha256:cd089b40...` fuer amd64, `sha256:04782f54...` in beiden Zeilen fuer arm64 (Lauf 33766139891).
- **Der Preis dieses Tauschs steht in der Datei, nicht in dieser Zusammenfassung.** Ein roter Smoke-Test hinterlaesst jetzt ein Manifest in der Registry. Es hinterlaesst keinen Tag: `push-by-digest` vergibt keinen, der merge-Job ist die einzige Stelle des Repositories, die einem Digest je einen Namen gibt, und er laeuft nicht, wenn der Bau rot ist. Der verworfene Gegenvorschlag, eine lokale Registry auf Port 5000 wie im Deploy-Job aus 05-01, steht mit seiner Begruendung daneben.
- **Sec-L9 ist beantwortet, und die Antwort hat zwei Haelften.** Wahr: der veroeffentlichte Index traegt vier Eintraege statt zwei, naemlich beide Plattformen und je eine `attestation-manifest`, deren Nutzlast eine in-toto-Aussage mit `predicateType https://slsa.dev/provenance/v1` ist und Quellrepository, Commit und die aufgeloesten Digests der Basisimages nennt. `imagetools create` erhaelt sie also. Nicht wahr: das ist keine Unterschrift. `gh attestation verify` kann sie nicht pruefen, weil dieser Befehl eine GitHub Artifact Attestation erwartet, die dieser Workflow nicht erzeugt. Beide Haelften stehen mit Datum in `docker.yml`, und die wahre Haelfte ist zusaetzlich ein Gate geworden.
- **Sec-M8 war schlimmer als das Inventar wusste, und das Gate haette es gefunden.** Der Plan geht davon aus, dass einer der beiden Checkout-SHAs der richtige ist. Keiner war es: `3d3c42e5` ist v7.0.1, `fbc6f399` ist v5.1.0, und das echte v5.0.0 ist `08c6903c`. Beide Kommentare logen, in einundzwanzig Zeilen ueber sechs Dateien.
- **Ein Gate mit fuenf Regeln und vierzehn Testfaellen, das offline laeuft.** `backend/tests/test_workflow_pins.py` liest alle Dateien unter `.github/workflows` und `.github/actions` als Text und sammelt Befunde mit Datei, Zeile und Grund. In der RED-Runde fand es genau die offenen Positionen und nichts sonst; heute findet es null.
- **Postgres ist ein Dauergate, und die Feststellung dazu hat einen eigenen Namen.** `index-search-e2e` faehrt `sqlite`, `mysql` und `pgsql`. Der Lauf mit `pgsql` ist gruen, `occ config:system:get dbtype` gibt `pgsql` aus, die Verdikte sind identisch mit den beiden anderen Dialekten (22 indexiert, 5 uebersprungen, 6 fehlgeschlagen, 22 Dokumente), und der neue Schritt meldet: "the queue is empty on pgsql, so every claimed row was acknowledged and no transaction was aborted underneath it".
- **Jeder Job jeder Workflow-Datei hat eine Deadline, und keine ist geraten.** Acht Jobs hatten keine. Zwei davon waren nie gelaufen, weil sie nicht auf einen Push feuern; sie wurden einmal ausgeloest statt geschaetzt.

## Task Commits

1. **Task 1: der Smoke-Test prueft das ausgelieferte Image** - `fbbd07a` (fix)
2. **Task 2 (RED): das Pin-Gate** - `e674ba8` (test)
3. **Task 2 (GREEN): die Verstoesse behoben** - `c5b7139` (fix)
4. **Task 3: Postgres als dritter Dialekt** - `950ca93` (feat)
5. **Nachtrag zu Task 2: die zwei geschaetzten Deadlines gemessen** - `1ba63a6` (fix)
6. **Deferred items** - `32bce2d` (docs)

## Files Created/Modified

- `backend/tests/test_workflow_pins.py` (neu, 418 Zeilen, 14 Faelle) - fuenf Regeln, fuenf Selbsttests je genau ein Befund, zwei Antivakuitaetstests, ein Sauberkeitsmuster. Der Docstring nennt die Grenze ausdruecklich: das Gate kann nicht wissen, ob eine SHA wirklich zu der Version gehoert, die ihr Kommentar nennt, weil das eine Netzabfrage waere; es prueft innere Widerspruchsfreiheit, und die aeussere Haelfte wird per `gh api` von Hand gemacht und in der Zusammenfassung des Plans festgehalten, der eine Pinnung bewegt.
- `.github/workflows/docker.yml` (+163/-20) - ein Bau je Architektur, Push per Digest, neuer Schritt "Pull the pushed digest back out of the registry" mit Vergleich beider Digests, Smoke gegen die Digest-Referenz, `timeout-minutes` fuer beide Jobs, der Sec-L9-Befund als Kommentarblock mit Datum und der neue Schritt "Verify the provenance attestations survived the merge".
- `.github/workflows/integration.yml` (+113/-26) - `pgsql` in der Matrix von `index-search-e2e`, Service-Container `postgres:16` mit einer Gesundheitspruefung, die Nutzer und Datenbank nennt, neuer Schritt "The queue really is empty, which is what finding M7 was about", und die zehn Checkout-Kommentare korrigiert. Der Job `search-parity` aus 05-09 ist inhaltlich unberuehrt.
- `.github/workflows/php.yml`, `python.yml`, `resilience.yml` - je zwei `timeout-minutes` mit Messung im Kommentar, dazu die Kommentarkorrekturen an `setup-php` und `setup-uv`.
- `.github/workflows/deploy-harp.yml` (+4/-4) - nur die zwei Checkout-Kommentare, siehe Deviation 2.
- `.github/actions/setup-test-nc/action.yml` (+24/-3) - Checkout und setup-uv vereinheitlicht, `setup-php`-Kommentar auf die exakte Version, und der Sec-L10-Kommentarblock als angenommenes Restrisiko.
- `.planning/phases/.../deferred-items.md` - DI-05-16 und die Erledigung von DI-05-10.

## Die aufgeloesten SHAs

Alle mit `gh api repos/<owner>/<repo>/tags` am 03.09.2026 aufgeloest, keine geraten.

| Action | SHA | Kommentar vorher | Wahrheit | Kommentar jetzt |
|---|---|---|---|---|
| actions/checkout | `3d3c42e5aac5ba805825da76410c181273ba90b1` | v5.0.0 | v7.0.1 (auch v7) | v7.0.1 |
| actions/checkout | `fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09` | v5.0.0 | v5.1.0 (auch v5) | entfernt, auf 3d3c42e5 vereinheitlicht |
| actions/checkout | `08c6903cd8c0fde910a37f88322edcfb5dd907a8` | nirgends | das echte v5.0.0 | nicht verwendet |
| astral-sh/setup-uv | `20cfd1bf945f4377ade1205e4dbc17946fc9a30d` | v10.0.1 | v10.0.1 | v10.0.1 |
| astral-sh/setup-uv | `d0cc045d04ccac9d8b7881df0226f9e82c39688e` | v6 | v6.8.0 (auch v6.8, v6) | entfernt, auf 20cfd1bf vereinheitlicht |
| shivammathur/setup-php | `f3e473d116dcccaddc5834248c87452386958240` | v2 | 2.37.2 (auch v2, master) | 2.37.2 |
| docker/setup-buildx-action | `37fe631027851001ddb9b187196cc803df7f5f0e` | v4.3.0 | v4.3.0 | unveraendert |
| docker/login-action | `dbcb813823bdd20940b903addbd779551569679f` | v4.6.0 | v4.6.0 | unveraendert |
| docker/build-push-action | `53b7df96c91f9c12dcc8a07bcb9ccacbed38856a` | v7.3.0 | v7.3.0 | unveraendert |
| actions/upload-artifact | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | v7.0.1 | v7.0.1 | unveraendert |
| actions/download-artifact | `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` | v8.0.1 | v8.0.1 | unveraendert |

Die fuenf unveraenderten Zeilen sind kein Fuellwerk: nachdem sich zwei von drei geprueften Kommentaren als falsch erwiesen hatten, war die einzige verantwortbare Reaktion, alle zu pruefen und das Ergebnis hinzuschreiben.

## Die Deadlines und woher jede Zahl kommt

| Datei | Job | Gemessen | Deadline | Grund |
|---|---|---|---|---|
| docker.yml | build | 32 bis 55 s warm, 2:30 kalt | 20 | rund acht mal ein kalter Bau |
| docker.yml | merge | 12 bis 22 s | 10 | weit ueber allem Gemessenen |
| php.yml | lint | 12 bis 20 s | 10 | dreissigfach |
| php.yml | app-metadata | 12 bis 36 s | 10 | zwei Netzabrufe im Spiel |
| python.yml | gates | 12 s bis 2:12 | 15 | siebenfach des schlechtesten Falls |
| python.yml | extract-bench-arm | 1:12 (Lauf 33766223084) | 20 | war nie gelaufen, einmal ausgeloest statt geschaetzt |
| resilience.yml | kill-resume | 1:40 bis 2:20 | 40 | NICHT aus der Laufzeit: die eigenen Grenzen des Jobs (MIDRUN_TIMEOUT 300 s, DRAIN_TIMEOUT 1200 s) erlauben 25 Minuten legitimes Warten |
| resilience.yml | measurements | 0:54 (Lauf 33766227097) | 20 | war nie gelaufen, einmal ausgeloest statt geschaetzt |

`integration.yml` und `deploy-harp.yml` hatten ihre Deadlines schon.

## Decisions Made

- **Push nach ghcr statt lokaler Registry.** Der Plan bietet beides an. Die lokale Registry haelt die Registry sauber, macht den Beweis aber zu einer Gleichheit zweier Digests statt zu einer Identitaet eines Artefakts, und sie setzt einen Service-Container in genau den Job, dessen Sinn es ist, dass geprueftes und ausgeliefertes Byte dasselbe Byte ist. Der Zweiglauf war trotzdem moeglich, weil `workflow_dispatch --ref` den Workflow des Zweigs faehrt.
- **Vereinheitlichung auf v7.0.1 statt auf v5.0.0.** Zwanzig der einundzwanzig Aufrufe fuhren `3d3c42e5` bereits, also war die Aenderung mit dem kleinsten Verhaltensrisiko, den einen Ausreisser nachzuziehen und die Kommentare zu korrigieren. Auf das echte v5.0.0 zurueckzugehen waere ein Downgrade von zwei Majors gewesen, das niemand entschieden hat.
- **Das Pin-Gate liest Text.** Ein YAML-Parser verwirft Kommentare, und der Kommentar ist der Gegenstand von zwei der fuenf Regeln. Der Job-Scanner stuetzt sich auf die Einrueckung dieser sechs Dateien und sagt das im Docstring; eine Datei, deren `jobs:`-Block er nicht findet, ist ein Befund und kein stiller Durchlauf.
- **Regel 1 und Regel 5 sind getrennte Funktionen.** Sie ueberlappen, wenn dieselbe Action zwei SHAs mit demselben Kommentar traegt. Getrennt gehalten, damit jeder Selbsttest genau einen Befund seiner eigenen Regel erwarten kann, und weil die beiden verschiedene Dinge sagen: der Kommentar luegt gegen die Version laeuft doppelt.
- **Regel 2 verlangt eine exakte Version im Kommentar, nicht nur irgendeinen.** Die Owner-Regel spricht von setup-uv, der Grund gilt fuer jede Action: `# v6` hinter einer SHA liest sich wie ein beweglicher Major und verschweigt, welches Release wirklich laeuft. Nach der Vereinheitlichung nennt jeder Kommentar mindestens Major und Minor, die Regel ist also erfuellbar und nicht theoretisch.
- **Die Feststellung zur leeren Warteschlange ist ein eigener Schritt.** Die Warteschleife weiter oben wartet ohnehin auf eine leere Warteschlange, meldet einen gebrochenen Quittungsweg aber als "the crawl did not finish within 900 seconds", was sich wie ein langsamer Runner liest und erneut angestossen wird. Der eigene Schritt gibt derselben Tatsache einen eigenen Namen und ueberlebt den naechsten Umbau der Schleife.
- **pgsql bei jedem Push, nicht auf einem Zeitplan.** Der Plan erlaubt den Zeitplan-Zuschnitt, falls die Laufzeit nicht mehr traegt. Die Messung sagt, dass sie traegt: die drei Eintraege sind eine Matrix und laufen parallel (2,5 / 3,2 / 2,8 Minuten im Beweislauf), also kostet der dritte Eintrag Runner-Minuten und keine Rueckmeldezeit. Ein Dialekt, der nur woechentlich geprueft wird, ist ein Dialekt, dessen Bruch ein Nutzer findet.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Beide Checkout-Kommentare logen, nicht nur einer**

- **Found during:** Task 2, bei der Aufloesung per `gh api`
- **Issue:** Der Plan formuliert Sec-M8 als "zwei verschiedene SHAs, ein Kommentar" und gibt vor, mit `gh api repos/actions/checkout/git/ref/tags/v5.0.0` zu ermitteln, "welcher der richtige ist". Die Antwort ist: keiner. v5.0.0 ist `08c6903cd8c0fde910a37f88322edcfb5dd907a8`, und dieser SHA steht nirgends im Repository. `3d3c42e5` ist v7.0.1 und `fbc6f399` ist v5.1.0. Waere der Plan woertlich befolgt worden, waere das Repository auf einen SHA umgestellt worden, der zwei Majors unter dem liegt, was zwanzig Aufrufe seit Monaten fahren, ohne dass jemand diesen Downgrade entschieden haette.
- **Fix:** Auf `3d3c42e5` vereinheitlicht, also auf das, was faktisch laeuft, und alle einundzwanzig Kommentare auf `v7.0.1` korrigiert. Zusaetzlich alle uebrigen neun Pinnungen des Repositories aufgeloest, weil zwei von drei geprueften Kommentaren falsch waren und eine Stichprobe danach keine Aussage mehr ist. Die uebrigen stimmten.
- **Files modified:** alle sechs Workflow-Dateien und die Composite Action
- **Verification:** `gh api repos/actions/checkout/tags` und dieselbe Abfrage fuer die anderen sechs Actions, Ergebnis in der Tabelle oben; alle sechs Workflows danach gruen
- **Committed in:** `c5b7139`

**2. [Rule 3 - Blocking] `deploy-harp.yml` stand nicht in `files_modified`, traegt aber zwei der luegenden Kommentare**

- **Found during:** Task 2, beim ersten Lauf des Gates
- **Issue:** Der Plan nennt fuenf Workflow-Dateien. `deploy-harp.yml` aus 05-01 ist die sechste, sie enthaelt zwei `actions/checkout`-Zeilen mit demselben falschen Kommentar, und das Gate liest bauartbedingt alles unter `.github/workflows`. Die Datei auszulassen haette bedeutet, das Gate rot zu lassen oder es so zuzuschneiden, dass es genau die Datei nicht sieht, die dieselbe Krankheit hat.
- **Fix:** Die beiden Kommentare mitgezogen. Sonst nichts an der Datei; ihre Deadline hatte sie schon, der Rest ist zeilenweise unveraendert.
- **Files modified:** `.github/workflows/deploy-harp.yml` (4 Zeilen, 2 Kommentare)
- **Verification:** `git diff` zeigt fuer diese Datei ausschliesslich die zwei Kommentaraenderungen; der Lauf 33766125483 ist ueber alle vier Serverversionen gruen
- **Committed in:** `c5b7139`

**3. [Rule 2 - Missing Critical] `setup-php` war mit einem Major kommentiert, in zwei Dateien**

- **Found during:** Task 2, beim Aufloesen aller Pinnungen
- **Issue:** Das Inventar nennt Sec-L8 nur fuer setup-uv. `shivammathur/setup-php@f3e473d1` traegt aber ebenfalls den Kommentar `# v2`, und der SHA ist zugleich `master` dieses Repositories. Ein Kommentar, der einen Major nennt, verschweigt genau die Information, wegen der die Owner-Regel existiert.
- **Fix:** Kommentar auf `2.37.2`, die exakte Version, zu der dieser SHA gehoert. Der SHA selbst bleibt.
- **Files modified:** `.github/workflows/php.yml`, `.github/actions/setup-test-nc/action.yml`
- **Verification:** `gh api repos/shivammathur/setup-php/tags`; Regel 2 des Gates deckt den Fall ab und hat einen eigenen Selbsttest
- **Committed in:** `c5b7139`

**4. [Rule 2 - Missing Critical] Die Provenance-Verifikation wurde ein Gate und nicht nur ein Kommentar**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt, die Zusage einmal zu pruefen und das Ergebnis als Kommentar mit Datum festzuhalten. Eine einmal gepruefte Zusage in einem Kommentar ist am Tag danach wieder eine Behauptung, und die Datei begruendet mit genau dieser Zusage, warum `imagetools` benutzt wird und keine Handmontage.
- **Fix:** Zusaetzlich ein Schritt im merge-Job, der den veroeffentlichten Index liest, genau zwei Plattform-Manifeste und genau zwei Bescheinigungen verlangt und prueft, dass die Subjekte der Bescheinigungen genau die beiden Plattform-Digests sind. Die Zaehlung allein waere gruen geblieben bei einem Index mit zwei Bescheinigungen von etwas anderem.
- **Files modified:** `.github/workflows/docker.yml`
- **Verification:** vor dem Commit lokal gegen den echten veroeffentlichten Index gefahren (gruen) und gegen denselben Index mit entfernten Bescheinigungen (rot, Exitcode 1); danach im Lauf 33766139891 gruen
- **Committed in:** `fbbd07a`

**5. [Rule 2 - Missing Critical] Zwei Deadlines waeren Schaetzungen geblieben**

- **Found during:** Task 2, bei der Suche nach den Laufzeiten
- **Issue:** `python.yml/extract-bench-arm` und `resilience.yml/measurements` feuern nicht auf einen Push, und jeder aufgezeichnete Lauf hat sie uebersprungen. Es gab also keine Zahl, aus der eine Deadline haette abgeleitet werden koennen, und das Abnahmekriterium verlangt ausdruecklich eine abgeleitete und keine geratene.
- **Fix:** Beide einmal per `workflow_dispatch` auf dem Arbeitszweig gefahren. Ergebnis 1:12 und 0:54, beide gruen. Die Kommentare tragen jetzt die Messung und die Lauf-Id statt einer Herleitung aus dem, was der Job tut. Die vorherige Herleitung lag um mehr als eine Groessenordnung daneben (geschaetzt bis 33 Minuten, gemessen 1:12), was fuer sich genommen der beste Grund ist, nicht zu schaetzen.
- **Files modified:** `.github/workflows/python.yml`, `.github/workflows/resilience.yml`
- **Verification:** Laeufe 33766223084 und 33766227097
- **Committed in:** `1ba63a6`

---

**Total deviations:** 5 auto-fixed (1 falsche Annahme im Plan mit Beleg, 1 blockierende Datei ausserhalb der Liste, 3 fehlende kritische Ergaenzungen)
**Impact on plan:** Ohne die erste waere das Repository auf einen zwei Majors alten Checkout umgestellt worden, im Namen einer Haertung. Die anderen vier sind der Unterschied zwischen einer Regel, die gilt, und einer, die fuer den Teil gilt, den jemand aufgeschrieben hat.

## Issues Encountered

- **Die Zeilennummern des Plans waren verschoben.** `integration.yml:124` traegt laengst den richtigen SHA, `action.yml:84` ist 179 und `:149` ist 351. Ursache ist Plan 05-09, der 581 Zeilen in `integration.yml` und 61 in die Composite Action gelegt hat. Die Positionen wurden ueber die Inhalte wiedergefunden, nicht ueber die Zeilen.
- **Die Laufzeitangabe des Plans zu `index-search-e2e` war die Deadline und nicht die Laufzeit.** Der Plan warnt, der Job dauere "schon rund 45 Minuten je Dialekt", und bietet deshalb den Zeitplan-Zuschnitt fuer pgsql an. 45 ist der Wert von `timeout-minutes`; gemessen sind 2,5 bis 4,5 Minuten je Dialekt. Der Zuschnitt war damit nicht noetig, und die Begruendung dafuer steht als Kommentar in der Matrix.
- **Ein Selbsttest war in der RED-Runde aus dem falschen Grund gruen.** Der Ersetzungsausdruck, der die schmutzige Probe fuer Regel 1 baut, passte auf keine Stelle der sauberen Probe, also war die Probe sauber und der Test meldete null Befunde. Behoben, indem nur das erste Vorkommen ersetzt wird; danach war er rot und ist jetzt aus dem richtigen Grund gruen.
- **`actionlint` ist auf dieser Maschine nicht vorhanden**, wie schon in 05-09. Ersatz: alle sieben Dateien laden als YAML, jeder einzelne `run`-Block wurde einzeln mit `bash -n` geprueft (8 in `docker.yml`, 79 in `integration.yml`), und danach sind sechs echte CI-Laeufe gruen.
- **`git stash` und flaechige Zuruecksetzungen sind im Worktree verboten.** Task 2 und Task 3 fassen beide `integration.yml` an. Getrennt wurden sie ueber eine Kopie im Scratchpad und ein `git checkout -- .github/workflows/integration.yml` auf genau diese eine Datei, danach die Kommentaraenderung erneut angewandt, committet und die Kopie zurueckgespielt. Beide Commits enthalten deshalb genau ihre eigene Aenderung.
- **Der Zweiglauf von `docker.yml` bewegt den Tag `:dev`.** Das war der Preis fuer den Beweis und er ist nicht eingetreten: der Bau war vollstaendig aus dem Cache, und die beiden Plattform-Manifeste des neuen Index sind bitgleich die des letzten main-Laufs (`0a475dc3` und `df57e651`). `:dev` zeigt also auf denselben Inhalt wie vorher.

## Verification

Alle Laeufe auf dem Zweig `worktree-agent-05-13`, 03.09.2026:

| Workflow | Lauf | Ergebnis |
|---|---|---|
| Multi-arch image | 33766139891 (dispatch) | gruen, beide Architekturen, Push-Digest gleich Pull-Digest, Provenance-Gate gruen |
| Integration | 33766125632 (push) | gruen, sechs Jobs, darunter index-search-e2e (pgsql) in 2,8 min und search-parity in 5,6 min |
| PHP and store metadata gates | 33766125442 (push) | gruen |
| Python gates | 33766223084 (dispatch) | gruen, inklusive extract-bench-arm |
| Resilience | 33766227097 (dispatch) | gruen, inklusive measurements |
| HaRP deploy | 33766125483 (push) | gruen ueber stable32, 33, 34 und 35 |

Die beiden Push-Laeufe von Python und Resilience stehen als `cancelled` in der Liste: die Nebenlaeufigkeitsgruppe beider Dateien hat `cancel-in-progress: true`, und die kurz darauf ausgeloesten Dispatch-Laeufe auf demselben Commit haben sie abgeloest. Abdeckung und Commit sind identisch.

Lokal, vor jedem Commit:

- `cd backend && uv run python -m pytest -q`: 913 bestanden, 11 uebersprungen
- `ruff check .`, `ruff format --check .`, `pyright`, `vulture src tests --min-confidence 80`: alle gruen
- `tests/test_workflow_pins.py`: 14 Faelle, in der RED-Runde 4 rot mit genau den erwarteten Befunden, jetzt 14 gruen und null Befunde ueber dem Baum
- kein Em-Dash (U+2014) und kein En-Dash (U+2013) in einer der geaenderten Dateien, geprueft ueber alle sieben YAML-Dateien

## Known Stubs

Keine. Alle drei Aufgaben sind vollstaendig gebaut, nichts ist als Platzhalter angelegt, und keine der neuen Zusicherungen ist eine Absichtserklaerung ohne Messung.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: supply-chain | `.github/workflows/docker.yml` | Neue Oberflaeche an der Grenze CI zu ghcr: ein roter Smoke-Test hinterlaesst jetzt ein Manifest in der Registry, wo vorher gar nichts hochgeladen wurde. Es traegt keinen Tag, der merge-Job vergibt den einzigen und laeuft in diesem Fall nicht, und die Abwaegung samt verworfener Alternative steht als Kommentar an der Stelle. Bewusst eingegangen, denn die Alternative ist ein Smoke-Test, der ein anderes Artefakt prueft als das ausgelieferte (T-05-53). |
| threat_flag: supply-chain | `.github/workflows/docker.yml` | Die Provenance des veroeffentlichten Images ist unsigniert (buildkit statt GitHub Artifact Attestation). Kein neuer Zustand, aber ein neu belegter: bisher war es eine ungeprüfte Zusage. Als DI-05-16 aufgeschrieben, gehoert in den Release-Plan. |

Bezug zum Threat-Register des Plans: T-05-53, T-05-54 und T-05-55 sind mitigiert und je durch ein Gate getragen; T-05-56 ist wie vorgesehen als Restrisiko angenommen und steht als Kommentarblock in der Composite Action; T-05-SC ist eingehalten, kein neues Sprachpaket, neu bezogen wird allein `postgres:16` aus dem offiziellen Image.

## User Setup Required

Keine. Der Zweig `worktree-agent-05-13` liegt auf origin, damit die CI-Belege dieser Zusammenfassung entstehen konnten; der Orchestrator loescht ihn nach dem Merge.

## Next Phase Readiness

- **PKG-05 ist erfuellt.** Die Lieferkette ist so hart, wie die Dateien behaupten: das gepruefte Artefakt ist das ausgelieferte, jeder Kommentar hinter einer SHA stimmt, keine Version wird doppelt gepinnt, jeder Job hat eine Deadline, und ein Gate findet jeden dieser Verstoesse beim naechsten Mal von selbst.
- **Fuer jeden Plan, der eine Action hinzufuegt oder bewegt:** `backend/tests/test_workflow_pins.py` verlangt eine SHA, einen exakten Versionskommentar und genau eine SHA je Action im ganzen Repository. Der aeussere Teil, die Frage ob die SHA wirklich zu der Version gehoert, bleibt Handarbeit mit `gh api` und gehoert in die Zusammenfassung des jeweiligen Plans.
- **Fuer jeden Plan, der einen Job hinzufuegt:** ohne `timeout-minutes` ist die Gesamtsuite rot. Feuert der Job nicht auf einen Push, ist der billige Weg zu einer echten Zahl ein `gh workflow run --ref <zweig>`.
- **Fuer den Release-Plan (D-26):** DI-05-16, die Signatur der Provenance, ist der offene Rest von Sec-L9.
- **Fuer den Plan des ARM- und AIO-Laufs:** Postgres ist ab jetzt in CI belegt, inklusive des Befunds M7, der die Zielumgebung betrifft. Ein Postgres-Fehler auf der Box ist damit nicht mehr die erste Begegnung des Projekts mit diesem Dialekt.
- **Blocker:** keiner.

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-03*

## Self-Check: PASSED

Alle neun genannten Dateien liegen im Arbeitsbaum, alle sechs Aufgaben-Commits
sind in der Zweighistorie, und `.planning/STATE.md` sowie `.planning/ROADMAP.md`
sind in der Spanne 6d1f091..HEAD unveraendert (der Orchestrator schreibt sie).
Der Job `search-parity` aus 05-09 zeigt gegen den Ausgangsstand null geaenderte
Zeilen.
