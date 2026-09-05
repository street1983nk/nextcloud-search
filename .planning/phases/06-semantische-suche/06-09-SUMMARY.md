---
phase: 06-semantische-suche
plan: 09
subsystem: backend
tags: [d-16, d-14, zweite-deckungszahl, herkunftsmarke, ein-rechenweg, wr-01, admin-seite]

# Dependency graph
requires:
  - phase: 06-semantische-suche
    provides: "06-04: vectors.db, chunks_of und die Zaehloperationen des Vektorspeichers"
  - phase: 06-semantische-suche
    provides: "06-06: origins(), seit dort ungerufen bereitstehend, und SemanticSide"
  - phase: 06-semantische-suche
    provides: "06-07: die Zweitspur, die den Bestand fuellt und damit die Zahl bewegt"
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "coverage(), der eine Nenner aus overview(), die hidden-Bauart der Bloecke und die zwei Vertragstests"
provides:
  - "store/vectors.py::document_count, die Dokumente mit Vektor statt der Chunks"
  - "api/status.py::StatusResponse.embedded, enthalten in indexed und nie daneben addiert"
  - "api/status.py::NO_VECTORS_YET und VECTORS_UNREADABLE, die zwei Notizen der zweiten Spur"
  - "api/diagnose.py::DiagnoseResponse.embedded, .chunks und .origin"
  - "api/diagnose.py::NO_ORIGIN, die vierte Marke neben den dreien aus fusion.py"
  - "index/search.py::_sides, die eine Stelle, an der beide Ranglisten entstehen"
  - "index/search.py::ranked_sides und RankedSides, der Zugang der Admin-Diagnose"
  - "AdminViewService::coverageShare, ein Rechenweg fuer beide Deckungszahlen"
  - "AdminViewService::optionalCounter, die Trennung von 'null Vektoren' und 'nicht gemeldet'"
  - "der Block findling-semantic auf der Admin-Seite, live bei jedem Poll"
affects: [06-10 Gates, 06-11 Lasttest, 06-12 Store-Abgabe]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zwei Zahlen derselben Art entstehen aus einem Aufruf derselben Methode mit einem anderen Zaehler, nie aus zwei Rechenwegen"
    - "Eine Zahl, die fehlen kann, wird auf der Leseseite als null gefuehrt und nie als 0, weil 0 eine Aussage ist"
    - "Eine Antwort traegt eine Notiz, also werden zwei Befunde geordnet statt aneinandergehaengt"
    - "Ein Feld, das nur auf Nachfrage existiert, fehlt in der Antwort und ist nie null-gefuellt"
    - "Eine Zahl, die sich in genau der Phase bewegt, in der alle anderen stillstehen, gehoert in den Fingerabdruck des Pollings"

key-files:
  created: []
  modified:
    - backend/src/findling/api/status.py
    - backend/src/findling/api/diagnose.py
    - backend/src/findling/index/search.py
    - backend/src/findling/store/vectors.py
    - backend/tests/test_status_endpoint.py
    - backend/tests/test_diagnose_endpoint.py
    - backend/tests/test_admin_ui_contract.py
    - php/lib/Service/AdminViewService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/de.json
    - php/l10n/de.js
    - php/tests/Unit/AdminViewServiceTest.php
    - docs/admin-page.md
    - .planning/phases/06-semantische-suche/deferred-items.md

key-decisions:
  - "embedded zaehlt Dokumente (COUNT DISTINCT file_id) und nicht Chunks: ein Dokument traegt zwei bis drei Chunks, also stuende eine Chunkzahl neben einer Dokumentzahl auf derselben Seite und waere um das Zwei- bis Dreifache zu gross"
  - "Die Zahl wird im Vektorspeicher gezaehlt und bekommt keine Spalte in files: die zweite Stelle, die den Rueckstand zu kennen behauptet, laeuft am ersten verlorenen Schreibvorgang auseinander"
  - "Eine Antwort traegt eine Notiz, also sind die zwei Befunde geordnet: die Zustandsdatenbank schlaegt den Vektorspeicher, weil ohne sie gar keine Zahl existiert und ohne den Bestand genau eine"
  - "coverageShare ist public static und nicht privat, nach dem Vorbild von progressStamp: die Abnahmekriterien dieses Plans verlangen PHPUnit-Faelle ueber genau diese Arithmetik, und die Alternative waere ein Test aus zwoelf Attrappen"
  - "embedded ist auf der PHP-Seite int|null: 'der Container hat nichts gemeldet' (aeltere Fassung) und 'kein Dokument hat einen Vektor' sind zwei Auskuenfte, und 0 Prozent waere eine Aussage ueber die zweite"
  - "origin ist abwesend statt null, ueber response_model_exclude_none, weil null als 'gesucht und nichts gefunden' gelesen wuerde"
  - "Die Herkunft entsteht ueber _sides, dieselbe Funktion, die eine Suchrunde ihre zwei Listen bauen laesst; origins selbst wird ausschliesslich in diagnose.py gerufen und steht in keiner der beiden Suchdateien"
  - "ranked_sides fragt keinen Vorfilter, und das ist eine Eigenschaft des Aufrufers: die Diagnose ist admin-seitig, nennt die Datei selbst und laeuft nicht je Treffer (D-14)"
  - "Der zweite Block wird vom Skript bei jedem Poll geschrieben und steht im Fingerabdruck, sonst friert genau die Zahl ein, deren Bewegung der Grund fuer den Block ist"

patterns-established:
  - "Ein Vertragstest ueber einen Schluessel prueft ihn mit Wortgrenzen, wenn ein zweiter Schluessel ihn als Praefix enthaelt"
  - "Ein Gate ueber 'ein Rechenweg' zaehlt Aufrufstellen und nicht Namensnennungen, damit eine bessere Erklaerung es nicht rot macht"

requirements-completed: [SEM-01]

# Metrics
duration: 33min
completed: 2026-09-05
---

# Phase 6 Plan 09: Die zweite Deckungszahl und die Herkunft eines Treffers Summary

**Der Admin sieht ab jetzt beide Spuren getrennt: wie viele Dokumente indexiert sind und wie viele davon einen Vektor tragen, gerechnet aus einem Aufruf derselben Methode mit demselben Nenner. Und er kann für eine Datei und einen Suchbegriff erfahren, ob sie lexikalisch, semantisch, aus beidem oder gar nicht gefunden wurde, über dieselbe Verschmelzung, die eine Suche fährt, in der Admin-Diagnose und nirgends sonst.**

## Performance

- **Duration:** rund 33 min
- **Started:** 2026-09-05T08:51:00Z
- **Completed:** 2026-09-05T09:24:00Z
- **Tasks:** 3 von 3
- **Files modified:** 15 (0 neu, 15 geändert)
- **Tests:** 1.338 bestanden, 13 übersprungen (vorher 1.312), also 26 neue Fälle

## Accomplishments

- **Die zweite Zahl ist ein zweiter Aufruf, und das ist als Gate festgehalten.** `AdminViewService::coverageShare()` steht genau einmal da und wird genau zweimal gerufen; ein Test in `test_admin_ui_contract.py` zählt die Aufrufstellen und war im Lauf rot, als eine davon durch eine gleichwertige Inline-Rechnung ersetzt wurde. Zwei Rechenwege für dieselbe Art Zahl hätten am Tag ihrer Entstehung übereingestimmt und am Tag der ersten Korrektur nicht mehr, und auf der Seite wäre das nicht zu sehen gewesen.
- **"Fehlt die Zahl" und "die Zahl ist null" sind zwei Auskünfte geblieben.** Der Container meldet `embedded` immer, aber eine ältere Fassung meldet sie nicht, und genau dieser Fall ist der gefährliche: ohne Trennung stünde auf einer Instanz mit vollständiger Semantik "0 Prozent auffindbar nach Bedeutung", nachdem jemand die zwei Hälften in der falschen Reihenfolge aktualisiert hat. `optionalCounter()` führt das Feld deshalb als `int|null`, und der zweite Prozentwert ist dann null und wird als Satz gerendert statt als Zahl.
- **Ein fehlender Vektorspeicher kostet genau ein Feld und nie die Antwort.** Vier Zustände sind als Fälle belegt: keine Datei, eine Null-Byte-Datei, eine Datei, die keine SQLite-Datenbank ist, und eine Box, auf der vec0 nicht lädt. Alle vier antworten mit HTTP 200, `embedded` gleich 0 und einer Notiz, und jede Volltextzahl derselben Antwort bleibt gültig (WR-01). Die Notizen sind geordnet: ist auch die Zustandsdatenbank kaputt, gewinnt deren Notiz, weil dann gar keine Zahl existiert.
- **Die Herkunftsmarke ist an genau einer Stelle im Baum, und ein grep hält das fest.** `origins` kommt in `api/search.py` null mal vor und in `index/search.py` null mal, obwohl die zwei Listen, die sie braucht, dort entstehen. Möglich ist das, weil `_sides` die eine Stelle ist, an der beide Ranglisten gebaut werden: eine Suchrunde ruft sie und `ranked_sides` ruft sie, und die Diagnose setzt `origins` darüber. Der Feldmengen-Test von `Candidate` ist unverändert grün.
- **Der Block der Seite ist live und nicht einmalig gerendert.** Während der Einbettung steht die Volltexthälfte still, also ist die semantische Zahl die einzige, die sich bewegt. Ohne sie im Fingerabdruck des Pollings hätte `render()` den Durchgang übersprungen und die Seite hätte genau in der Phase eingefroren, für die der Block gebaut wurde.

## Task Commits

1. **Task 1 (RED): Das Gatter über der zweiten Deckungszahl und einem fehlenden Vektorspeicher** - `ea20b7e` (test)
2. **Task 1 (GREEN): embedded, die zweite Deckungszahl des Containers** - `689b07d` (feat)
3. **Task 2 (RED): Das Gatter über der Herkunftsmarke und der Zweitspur einer Datei** - `39283bd` (test)
4. **Task 2 (GREEN): Die Diagnose sagt, welche Hälfte der Suche ein Dokument gefunden hat** - `dd2ba35` (feat)
5. **Task 3: Die zweite Deckungszahl auf der Admin-Seite** - `6bb1043` (feat)
6. **Der Nachtrag zu DI-06-02 und DI-06-03** - `4b5ff72` (docs)

## Files Created/Modified

- `backend/src/findling/api/status.py` - `embedded` mit dem Kommentar in der Form des `truncated`-Kommentars, `_embedded()` mit dem eigenen Fehlerpfad, zwei neue Notizen und ein Kopfabsatz zur zweiten Spur
- `backend/src/findling/store/vectors.py` - `document_count()`, Dokumente statt Chunks, mit der Begründung gegen eine Spalte in `files`
- `backend/src/findling/api/diagnose.py` - `embedded`, `chunks`, `origin`, `NO_ORIGIN`, `_second_track()`, `_origin_of()`, der zweite Query-Parameter und `response_model_exclude_none`
- `backend/src/findling/index/search.py` - `_sides()`, `ranked_sides()`, `RankedSides`; `candidates()` baut seine Listen ab jetzt über dieselbe Funktion
- `backend/tests/test_status_endpoint.py` - sechs Verhaltensfälle der zweiten Zahl und drei statische (Wortlaut des Kommentars, kein Row-Spread, kein Gedankenstrich)
- `backend/tests/test_diagnose_endpoint.py` - zehn Fälle über die vier Marken, die zwei Dateifelder und den kaputten Bestand, dazu vier statische
- `backend/tests/test_admin_ui_contract.py` - der Schlüsseltest über die drei Hälften der Seite, seine Rotprobe und das Gate über "ein Rechenweg, zwei Aufrufe"
- `php/lib/Service/AdminViewService.php` - `coverageShare()`, `optionalCounter()`, die zwei neuen Schlüssel unter `coverage` und das achtzehnte Feld unter `backend`
- `php/templates/admin.php` - der Block `findling-semantic` mit vier Gestalten, jede mit ihrer eigenen hidden-Regel
- `php/js/admin.js` - `semanticBlock()` und die zwei neuen Werte im Fingerabdruck
- `php/l10n/de.json`, `php/l10n/de.js` - vier neue Zeilen, in beiden Katalogen gleich (IN-02)
- `php/tests/Unit/AdminViewServiceTest.php` - vier Fälle über die geteilte Arithmetik und ihre Grenzen
- `docs/admin-page.md` - der Abschnitt "Die zweite Zahl: auffindbar nach Bedeutung"
- `.planning/phases/06-semantische-suche/deferred-items.md` - der Nachtrag zu DI-06-02 und DI-06-03

## Die vier Marken und wo sie herkommen

| Marke | Bedeutung | Herkunft |
|---|---|---|
| `lexical` | nur die Engine hat das Dokument beigetragen | `fusion.origins` aus der lexikalischen Liste |
| `semantic` | nur der Vektorzweig hat es beigetragen | dieselbe Funktion, aus der semantischen Liste |
| `both` | beide Listen führen es | dieselbe Funktion, Überschneidung der beiden |
| `none` | keine der beiden Listen führt es | `diagnose.NO_ORIGIN`, weil `origins` nur über Dokumente ihrer Listen spricht |

## Decisions Made

- **`embedded` zählt Dokumente und nicht Chunks.** Unter dem Deckel aus D-01 trägt ein Dokument zwei bis drei Chunks (gemessen 05.09.2026), also wäre eine Chunkzahl auf derselben Seite um das Zwei- bis Dreifache größer als die Zahl, deren Anteil sie sein soll. Ein Testfall legt drei Chunks in ein Dokument und eine in vier weitere und verlangt die Antwort 5; ein `COUNT(*)` hätte 7 geliefert und überall sonst plausibel ausgesehen.
- **Die Zahl kommt aus dem Vektorspeicher und bekommt keine Spalte in `files`.** Der Bestand ist die einzige Stelle, die es weiss, und eine zweite Stelle, die den Rückstand zu kennen behauptet, ist der Klassenfehler, gegen den der Kopfkommentar von `repo.py` schreibt: die beiden stimmen bis zum ersten verlorenen Schreibvorgang überein und danach leise nicht mehr. Der Preis ist ein indizierter Scan von `chunks_file` je Statusaufruf, und diese Route fragt eine Admin-Seite.
- **Eine Antwort trägt eine Notiz, also sind die Befunde geordnet und nicht aneinandergehängt.** Die Zustandsdatenbank schlägt den Vektorspeicher, und der Grund ist eine Größenordnung: ohne sie hat die Antwort gar keine Zahlen, ohne den Bestand fehlt genau eine. Ein Testfall macht beide kaputt und verlangt die Notiz der Zustandsdatenbank.
- **`coverageShare` ist öffentlich und statisch.** Der Plan sagt "derselben privaten Methode", und die Abnahmekriterien desselben Plans verlangen drei PHPUnit-Fälle über genau diese Arithmetik. Beides zusammen geht nicht: `coverage()` ist privat und braucht zwölf Attrappen, um überhaupt gerufen zu werden. `progressStamp()` steht seit Plan 05-14 mit derselben Begründung öffentlich und statisch in derselben Klasse, also folgt die zweite Zahl dem Vorbild der ersten Ausnahme statt eine neue zu erfinden. Die Eigenschaft, auf die es dem Plan ankommt, ist unverändert: ein Rechenweg, zwei Aufrufe, ein Nenner, und ein Gate zählt genau das.
- **`origin` fehlt in der Antwort, statt null zu sein.** `response_model_exclude_none` an der Route macht das möglich, und es ist sicher, weil `origin` das einzige Feld dieses Modells ist, das null sein darf: jedes andere hat eine Zahl, einen Wahrheitswert oder eine leere Zeichenkette als Vorgabe, also kann nichts sonst mit verschwinden. Der Unterschied ist nicht kosmetisch: `null` liest sich als "gesucht und nichts gefunden", und das ist eine andere Auskunft als "niemand hat gefragt".
- **Ein leerer Suchbegriff ist kein Suchbegriff.** Ein Feld, das ein Admin leer gelassen hat, kommt als leere Zeichenkette an, und es mit `none` zu beantworten wäre ein Urteil über eine Suche, die niemand gefahren hat. Der Wert wird beschnitten und ein leerer gilt als nicht gestellt.
- **Die zwei Listen entstehen an einer Stelle.** `_sides()` ist die Antwort auf "dieselbe Verschmelzung und kein zweiter Rechenweg": `candidates()` ruft sie für die Antwort eines Nutzers, `ranked_sides()` für die Auskunft eines Admins. Damit bleibt `origins` in `diagnose.py` und taucht in keiner der beiden Suchdateien auf, was das Gate dieses Plans festhält, und die Marke spricht über die Suche, die dieser Container wirklich fährt.
- **Der zweite Block gehört in den Fingerabdruck.** Das Skript rendert nur, wenn sich etwas geändert hat, und die Einbettung ist genau der Zeitraum, in dem sich sonst nichts ändert. Ohne `coverage.embedded` und `coverage.embeddedPercent` in dieser Zeile wäre der Block über Stunden auf dem Wert von 09:00 Uhr stehen geblieben, neben einer ersten Zahl, die live ist.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Funktion] Der zweite Block wäre eingefroren gewesen**

- **Found during:** Task 3, beim Lesen von `admin.js`
- **Issue:** Die Dateiliste von Task 3 führt `php/js/admin.js` nicht. Ohne das Skript wäre der Block genau einmal serverseitig gerendert worden, und zwar in dem Moment, in dem der Admin die Seite öffnet. Während des Einbettungslaufs steht die Volltexthälfte still, also ist die semantische Zahl die einzige, die sich bewegt: die Seite hätte sie eingefroren gezeigt, neben einer ersten Zahl, die sich alle fünf Sekunden aktualisiert. Zwei Zeilen waren nötig und beide sind kritisch, denn `render()` vergleicht einen Fingerabdruck und hätte den Durchgang ohne die neuen Werte gar nicht erst ausgeführt.
- **Fix:** `semanticBlock()`, aus `coverageBlock()` heraus gerufen, damit es nur einen Leser des `coverage`-Teilbaums gibt, und `coverage.embedded` plus `coverage.embeddedPercent` im Fingerabdruck, mit der Begründung als Kommentar an der Zeile.
- **Files modified:** php/js/admin.js
- **Verification:** `test_every_half_of_the_page_carries_the_second_coverage_figure` führt das Skript als dritte Hälfte und ging in der Rotprobe rot.
- **Committed in:** `6bb1043`

**2. [Rule 2 - Fehlende kritische Funktion] Vier neue Sätze ohne deutsche Fassung**

- **Found during:** Task 3
- **Issue:** Der Block bringt vier neue Zeichenketten durch `$l->t()`. Ohne Eintrag in beiden Katalogen zeigt eine deutsche Instanz den englischen Quelltext, und zwar nur in diesem einen Block, direkt unter einer deutschen Kopfzahl. `php/l10n/de.json` und `php/l10n/de.js` stehen nicht in der Dateiliste des Plans, sind aber durch IN-02 aneinander gebunden und werden von Hand gepflegt.
- **Fix:** Vier Zeilen in beiden Dateien, wortgleich, mit echten Umlauten.
- **Files modified:** php/l10n/de.json, php/l10n/de.js
- **Verification:** `test_the_two_translation_files_carry_the_same_keys` ist grün, beide Kataloge führen 143 Schlüssel.
- **Committed in:** `6bb1043`

### Abweichungen, die keine Autoreparatur sind, sondern eine Auslegung des Plans

**3. `coverageShare` ist öffentlich und statisch, nicht privat**

Siehe "Decisions Made". Der Plan verlangt "einen zweiten Aufruf derselben
privaten Methode" und gleichzeitig drei PHPUnit-Fälle über deren Verhalten.
Die Eigenschaft, um die es geht, ist erfüllt und zusätzlich als Gate
festgehalten; die Sichtbarkeit folgt dem Vorbild von `progressStamp()`.

**4. `embedded` ist auf der PHP-Seite `int|null`**

Der Plan sagt "fehlt embedded, ist der zweite Prozentwert null". Mit einem
gewöhnlichen `counter()` wäre "fehlt" von "ist 0" nicht zu unterscheiden
gewesen, also gibt es `optionalCounter()` für dieses eine Feld. Der Container
selbst meldet die Zahl immer; der Fall betrifft eine PHP-Hälfte, die neuer ist
als ihr Container.

**5. Der PHPUnit-Fall zu "fehlt embedded" prüft die Arithmetik, nicht die Abbildung**

Auf der Ebene von `coverageShare` sind "stummer Container" und "Zahl nicht
gemeldet" dasselbe Argument, nämlich `available = false`. Wo die zwei Fälle
auseinandergehen, ist `coverage()`, und die Methode ist privat und ohne zwölf
Attrappen nicht erreichbar. Der Übergang von "Schlüssel fehlt" nach `false`
wird deshalb vom Python-Gate gehalten, das `$backendReachable && $embeddedKnown`
im Quelltext verlangt. Der Datensatz des PHPUnit-Falls nennt beide Lesarten in
seinem Namen.

**6. `store/vectors.py` und `index/search.py` stehen nicht in den Dateilisten ihrer Aufgaben**

Beides schreibt der Plan im Fließtext derselben Aufgaben vor. Task 1: "Liegt in
store/vectors.py noch keine passende Operation vor, kommt sie dort dazu und
nicht hier; der SQL bleibt unter store/." Task 2 verlangt, dass die Herkunft
"über dieselbe Verschmelzung wie eine Suche" entsteht, und zugleich, dass
`origins` in `index/search.py` nicht vorkommt. Beides zusammen geht nur, wenn
die Indexschicht die zwei Listen herausgibt und die API-Schicht die Marke daraus
bildet, also sind `_sides`, `ranked_sides` und `RankedSides` dort entstanden.

**7. Das grep-Kriterium über den Tokendeckel ist nicht wörtlich erfüllbar**

Das Abnahmekriterium verlangt `grep -c '1024\|1.024' php/templates/admin.php`
gleich 0. Die Datei enthält die Zahl zweimal, seit Phase 4, in der Umrechnung
von Bytes in Kibibyte (`while ($value >= 1024 ...)`), und beide Zeilen sind von
diesem Plan nicht berührt. Gemeint ist D-01, der Tokendeckel, und der wird
nirgends beworben: der Text des neuen Blocks nennt beide Spuren und keine Zahl.
Die zwei Fundstellen umzuschreiben wäre eine Änderung an einer
Byte-Formatierung ohne jeden Bezug zur Sache.

**8. `deferred-items.md` steht nicht in der Dateiliste**

DI-06-02 und DI-06-03 waren diesem Plan ausdrücklich zugewiesen. Sie sind hier
nicht geschlossen, und die Begründung steht als Nachtrag in der Datei, siehe
unten.

---

**Total deviations:** 2 autorepariert (beide fehlende kritische Funktionen), 6 Auslegungen
**Impact on plan:** Keine Ausweitung des Umfangs. Beide Autoreparaturen betreffen die Eigenschaft, die dieser Plan zusichert: dass der Admin die zweite Spur wirklich sieht, in seiner Sprache und in Bewegung.

## DI-06-02 und DI-06-03: weitergereicht, mit geschärfter Schließform

Beide bleiben offen, und der Grund ist nicht Zeitmangel, sondern die Richtung
des Schreibens. Dieser Plan baut drei **lesende** Flächen: `GET /status`,
`GET /diagnose` und die Admin-Seite. Beide Punkte brauchen einen Schreibvorgang
auf dem Indexweg, DI-06-03 einen Stempel der Marke `embedding_version`,
DI-06-02 einen Aufruf von `reset_for_reindex` beziehungsweise `forget_all` bei
deren Drift. Das gehört neben `Poller._stamp_if_rebuilt` und nicht in eine
Statusroute; eine Route, die beim Lesen stempelt, wäre genau die Nebenwirkung,
die dieses Projekt an drei Stellen ausschließt (`open_read_only`,
`PRAGMA query_only`, und der Testfall "asking for the status changes nothing").

Was dieser Plan beiträgt, ist die Bedingung, die bisher gefehlt hat, plus zwei
Fallen, die der nächste Plan nicht neu entdecken muss. Alles steht in
`deferred-items.md`:

1. "Vollständig" heißt `embedded == indexed` bei `indexed > 0`, mit
   `VectorStore.document_count()` als Zähler und ausdrücklich nicht mit
   `chunk_count`/`vector_count`: die beiden beantworten "ist der Löschweg
   heil", nicht "trägt jedes Dokument einen Vektor".
2. Der Stempel gehört nicht in `expected_versions()`, weil ein Sprung darin den
   Volltext-Reindex erzwingt, den D-21 ausschließt. `VECTOR_ONLY_MARKS` trennt
   die Marke aus genau diesem Grund.
3. Die Ordnung bei einem Drift ist zwingend: erst `forget_all`, dann die neue
   Marke, dann die Wiedervorlage. Umgekehrt stünde die Marke der neuen Fassung
   über einem Bestand der alten, und das bemerkt niemand mehr.

Die Schließform ist präzisiert und terminiert: ein eigener Plan auf dem
Indexweg, spätestens vor dem Tag `v1.0.0` aus Plan 06-12, oder eine bewusste
Entscheidung mit einem Satz in `docs/embeddings.md`, dass ein Modellwechsel
`occ findling:index --restart` verlangt. Beides ist vertretbar, aber es muss
getroffen und aufgeschrieben werden, denn ein Release, das einen Modellwechsel
nicht bemerkt, liefert still schlechtere Treffer und hat dafür keine Anzeige.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: denial-of-service | backend/src/findling/api/diagnose.py | Mit einem Suchbegriff fährt diese Route ab jetzt eine vollständige Kandidatenrunde, also eine Engine-Suche plus eine Einbettung plus einen Scan des Vektorbestands, gemessen 37,8 ms p95 warm. Sie stand nicht im Bedrohungsregister des Plans, weil dort die Rechenkosten der Herkunftsauskunft nicht vorkommen. Der Zugang ist unverändert: `access_level ADMIN` in `backend/appinfo/info.xml` (als Test festgehalten), `bruteforce_protection` auf 401, und der wirksame Schutz ist die PHP-Route ohne `NoAdminRequired`. Ohne Suchbegriff kostet die Route weiterhin zwei indizierte Abfragen. |

## Issues Encountered

- **Der ruff-Befund im RED-Commit von Task 2 ist nachträglich in denselben Commit gefaltet worden.** Die Importreihenfolge (I001) fiel erst nach dem Commit auf; der Stand war nicht geschoben, also ist der Commit ergänzt worden statt einen Reparaturcommit zu bekommen. Alle ruff-Läufe dieses Plans sind mit `--no-cache` gefahren, nach der Lehre aus 06-07.
- **Ein Editor-Schreibvorgang hat ein geschütztes Leerzeichen als Zeichen statt als Escape in `admin.js` gelegt.** Der Vertragstest IN-03 verlangt die Escape-Schreibweise auf beiden Seiten der Seite und die Abwesenheit des Zeichens selbst; die Stelle ist über ein Byte-genaues Skript berichtigt worden, und beide Dateien tragen die Escape-Form jetzt zweimal.
- **Die Rotprobe der Vertragstests ist gefahren worden und steht nicht nur als Zusicherung da.** Einmal mit umbenanntem `embeddedPercent` im Template (rot, mit der erwarteten Meldung) und einmal mit einer der zwei Aufrufstellen von `coverageShare` durch eine Inline-Rechnung ersetzt (rot). Beide Male ist der Stand danach über `git checkout` zurückgeholt worden.
- **PHPUnit ist lokal weiterhin nicht fahrbar**, aus dem in 06-07 festgehaltenen Grund: `php/tests/bootstrap.php` läuft im Autoload-Raum von `nextcloud/server`, den `composer.json` ausdrücklich nur in CI installiert. Die drei geänderten PHP-Dateien sind stattdessen mit `php -l` in `docker run --rm php:8.3-cli` geprüft, alle ohne Syntaxfehler. Die neuen Fälle rufen ausschliesslich eine statische Methode ohne Konstruktor, also hängt ihr Lauf an keiner Attrappe.
- **Die AWS-Box ist nicht angefasst worden.** Dieser Plan misst nichts; die einzige genannte Messzahl (37,8 ms p95 warm) stammt aus dem Bericht von 06-02 und steht bereits in `vectors.py`.

## Offene Verifikation

Keine. Alle Gates sind lokal grün gelaufen: `pytest` mit 1.338 bestandenen und
13 übersprungenen Tests, `ruff check . --no-cache`, `ruff format --check .`,
`pyright` mit 0 Fehlern und `vulture` ohne Befund, jeweils im CI-Umfang
`backend`, dazu `php -l` über die drei geänderten PHP-Dateien. Die
Abnahmegreps: `embedded` steht 7 mal in `api/status.py`, 11 mal in
`AdminViewService.php` und 6 mal in `admin.php`, `origins` steht 0 mal in
`api/search.py` und 0 mal in `index/search.py`, `**row` steht 0 mal in
`api/status.py`, `prefilter_visible` steht unverändert 2 mal in
`index/search.py`, und weder Geviert- noch Halbgeviertstrich stehen in einer der
fünfzehn geänderten Dateien. Die neun vorbestehenden Markdown-Formatbefunde
oberhalb von `backend` (DI-06-01) sind unverändert und nicht Gegenstand dieses
Plans.

## User Setup Required

None. Ein Container ohne Vektorspeicher zeigt auf der Seite einen Satz statt
einer zweiten Zahl und ist sonst unverändert. Ein Admin, der die Herkunft eines
Treffers wissen will, hängt seinen Suchbegriff als zweiten Parameter an die
Diagnose-Route; ohne ihn antwortet sie wie bisher plus zwei Feldern. Keine neue
Einstellung, keine neue Abhängigkeit.

## Next Phase Readiness

- **Plan 06-10 findet zwei fertige grep-Kandidaten vor.** `origins` ist in beiden Suchdateien null mal, und `prefilter_visible` steht weiterhin genau zweimal in `index/search.py`, obwohl dieser Plan eine zweite Rangfolgen-Funktion hinzugefügt hat. Beide Zusicherungen liegen heute in Endpunktsuiten und gehören nach `test_semantic_boundary.py`, mit dem Kommentarfilter, den jener Plan vorsieht.
- **Plan 06-11 hat einen zweiten Messgegenstand auf der Statusroute.** Je Aufruf kommt ab jetzt ein `COUNT(DISTINCT file_id)` über `chunks` dazu, indiziert, aber über den ganzen Bestand. Bei 100.136 Chunks ist das die Größenordnung eines Indexscans und wird von einer Seite gefragt, die alle fünf Sekunden pollt.
- **Plan 06-12 erbt eine Aussage, die im Store-Text stehen kann:** die Seite nennt beide Spuren getrennt und meldet nie hundert Prozent, solange Dokumente ohne Vektor übrig sind.
- **Ein Blocker für die Abgabe, benannt:** DI-06-02 und DI-06-03, siehe oben. Sie sind kein Blocker für 06-10 und 06-11, aber einer für den Tag `v1.0.0`, solange die Entscheidung dazu nicht getroffen ist.

## Self-Check: PASSED

Alle fünfzehn geänderten Dateien liegen auf der Platte, alle sechs Commits
(`ea20b7e`, `689b07d`, `39283bd`, `dd2ba35`, `6bb1043`, `4b5ff72`) stehen in
`git log`. Zusätzlich geprüft: `origins` ist 0 in `api/search.py` und 0 in
`index/search.py`, `prefilter_visible` ist unverändert 2 in `index/search.py`,
`**row` ist 0 in `api/status.py`, beide Übersetzungskataloge führen dieselben
143 Schlüssel, und weder Geviert- noch Halbgeviertstrich stehen in einer der
geänderten Dateien oder in dieser Zusammenfassung.

---
*Phase: 06-semantische-suche*
*Completed: 2026-09-05*
