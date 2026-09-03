---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 12
subsystem: infra
tags: [nextcloud-aio, harp, appapi, postgres, ocr, tesseract, cgroup-v2, load-testing, openpyxl, ghcr]

# Dependency graph
requires:
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: die laufende Box mit AIO über HaRP, die gemessene Grundlast und den Messbericht aus Plan 05-10
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: Korpusgenerator, RSS-Sampler und Box-Werkzeug aus Plan 05-05
  - phase: 03-aktualit-t-und-ocr
    provides: die Laptopmessung von 1984 ms je OCR-Seite in docs/ocr.md, gegen die der Faktor gerechnet wird
provides:
  - D-04 belegt: Findling läuft auf der Box über den von AppAPI selbst angelegten AIO-HaRP-Daemon und liefert Suchtreffer über OCS und über eine angemeldete Sitzung der Weboberfläche
  - Der gemessene OCR-Faktor auf x86, 2517 ms je Seite gegen 1984 ms auf dem Laptop, und die Einordnung, dass er je Zeichen bei 0,87 liegt und damit kein Hardwarenachteil ist
  - Eine Laufzeitprognose des Volllaufs aus gemessenen Posten, rund 13 h auf x86 statt der geschätzten 18 bis 20 h
  - Der erste PostgreSQL-Lauf des Projekts, ausgewertet, mit Perf-M7 erstmals auf Postgres belegt behoben
  - D-03 erfüllt: der Grenzwert steht als Zahl mit Rechnung aus drei Eingangsgrößen, zwei davon gemessen
  - Ein Fehler, der jede Tabellendatei jeder Instanz unindexierbar machte, gefunden und behoben
  - Rohdaten des Trockenlaufs unter docs/measurements/, unabhängig vom Fortbestand der Box
affects: [05-13, 05-14-volllauf-und-abbau, store-aussage-peak-rss, arm-wiederholungslauf, phase-review]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Den gemessenen Codestand als Digest benennen, nicht als Versionsnummer: die Registry führt ein Kennzeichen je Commit, und das ist die einzige Angabe, die Jahre später noch dasselbe bedeutet"
    - "Ein Werkzeug, das eine gepinnte Bibliothek braucht, läuft im Abbild der Anwendung und nicht im System-Python der Messmaschine"
    - "Eine Prüfsumme über erzeugte Dateien gilt nur zusammen mit der Umgebung, die sie erzeugt hat, sobald gerendert wird"
    - "Eine Bibliothek, die den Dateinamen prüft, bekommt einen Datenstrom: ein Datenstrom trägt keinen Namen"
    - "Zwei unabhängige Messungen derselben Größe gegeneinander stellen, statt einer zu glauben"
    - "Der Grenzwert wird vor dem Lauf festgelegt und in der Zusammenfassung zitierbar abgelegt"

key-files:
  created:
    - docs/measurements/2026-09-03-trockenlauf-cpx22/README.md
    - docs/measurements/2026-09-03-trockenlauf-cpx22/dry-run.csv
    - docs/measurements/2026-09-03-trockenlauf-cpx22/dry-run-2.csv
    - docs/measurements/2026-09-03-trockenlauf-cpx22/dry-report.csv
  modified:
    - docs/performance.md
    - backend/src/findling/extract/office.py
    - backend/tests/test_extract_documents.py
    - backend/tests/test_ops_scripts.py
    - .planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md

key-decisions:
  - "Das Abbild wurde gezogen und nicht gebaut, weil docker.yml jeden Commit unter seiner SHA ablegt und der Tag 5c82598 genau der Stand des Arbeitsbaums ist; das Kennzeichen 0.3.0 aus info.xml existiert in der Registry nicht, weil der Freigabe-Tag erst am Ende der Phase gesetzt wird (D-26)"
  - "Der Korpus wird im Abbild der ExApp erzeugt und nicht mit einem nachinstallierten Pillow auf der Box, damit kein Paket auf die Messmaschine kommt, das nicht ohnehin im Container läuft (T-05-SC)"
  - "Der Grenzwert bleibt bei 2,0 GB: die Rechnung mit der gemessenen Grundlast bestätigt die Empfehlung der Recherche, 2,5 GB ließen nur 909 MB für Kernel und Seitencache"
  - "Der xlsx-Befund wurde behoben und nicht nur notiert, weil er jede Tabelle jeder Instanz betrifft und weil ein Volllauf mit diesem Fehler 20 Stunden lang den falschen Pfad gemessen hätte"
  - "Die Wirkung der Korrektur wurde auf der Box mit einem dort gebauten Abbild belegt und nicht nur in der Testsuite, weil der Befund erst im Zusammenspiel von Poller und Extraktion sichtbar wurde"
  - "Der stehengebliebene Fehlschlag in der Fehlerliste (DI-05-21) wurde NICHT behoben: die Abhilfe entscheidet darüber, was die Zustandstabelle bedeutet, und berührt die Aufgeben-Regel nach drei Versuchen"

patterns-established:
  - "Trockenlauf vor Volllauf: zwanzig Minuten, die zwanzig Stunden absichern, und die sich hier in der ersten Minute bezahlt gemacht haben"
  - "Eine Testsuite, die jede Datei unter dem Namen ihres Formats anlegt, ist blind für den Namen, unter dem die Datei wirklich ankommt"
  - "Drei Zahlen getrennt führen: Grenzwert, gemessener Spitzenwert, memory.peak"

requirements-completed: [PKG-03]

# Metrics
duration: 1h 05m
completed: 2026-09-03
---

# Phase 5 Plan 12: Findling auf der Box, der Trockenlauf und der Grenzwert Summary

**Findling läuft über den AIO-HaRP-Daemon auf der Miet-Box und liefert Suchtreffer, ein Trockenlauf über 500 Dateien ist in 7 Minuten 38 Sekunden durchgelaufen und hat dabei einen Fehler gefunden, der jede Tabellendatei jeder Instanz unindexierbar machte, der OCR-Faktor ist mit 2517 ms je Seite gemessen statt geschätzt, die Prognose für den Volllauf steht bei rund 13 Stunden auf x86 statt der veranschlagten 18 bis 20, und der Grenzwert ist eine Zahl mit Rechnung: 2,0 GB.**

## Performance

- **Duration:** 1h 05m
- **Started:** 2026-09-03T18:35:00Z
- **Completed:** 2026-09-03T19:40:00Z
- **Tasks:** 3, davon einer mit einem eingeschobenen Fehlerbefund samt Korrektur
- **Files modified:** 9 Dateien, davon 4 neu

## Accomplishments

- **D-04 ist belegt, und zwar mit einem Befehl.** Der Weg, den Plan 05-01 gegen docker-compose mühsam freiräumen musste, ist unter AIO ein einziger Aufruf: `occ app_api:app:register findling_backend harp_aio --info-xml ... --wait-finish`, beim ersten Versuch erfolgreich. Container, Datenspeicher und Registrierung sind einzeln protokolliert, und eine Suche liefert über die OCS-Route wie über eine echte angemeldete Sitzung je fünf Treffer mit Textausschnitt aus dem Dateiinhalt.
- **Der gemessene Codestand ist benannt.** Das Kennzeichen `0.3.0` aus `info.xml` existiert in der Registry nicht; `docker.yml` legt aber jeden Commit unter seiner SHA ab, und dieser Tag ist genau der Stand des Arbeitsbaums. Gezogen wurde `ghcr.io/street1983nk/findling_backend:5c82598...`, Index-Digest `sha256:bb8f17e7...`, der beide Architekturen trägt. Die Quelldatei blieb unberührt.
- **Der Trockenlauf hat den Fehler gefunden, für den er da war.** 32 von 500 Dateien endeten als `failed(corrupt)`, und zwar genau die 32 Tabellen. Ursache: openpyxl prüft die Dateiendung, bevor es ein Byte liest, und der Poller übergibt seine Zwischendatei `job-<id>.part`. **Jede Tabellendatei jeder Instanz war betroffen**, und keiner der 47 Fälle der Formatprüfung hat es gesehen, weil jeder seine Testdatei unter dem Namen seines Formats anlegt. Behoben, mit Testfall, und auf der Box mit einem dort gebauten Abbild belegt: danach 587 indexiert, null Fehlschläge, und eine Suche nach einem Wort aus einer Tabellenzelle findet die Tabelle.
- **Der OCR-Faktor steht, und er sagt etwas anderes als die Zahl vermuten lässt.** 2517 ms je Seite gegen 1984 ms auf dem Laptop, also Faktor 1,27. Die Korpusseite trägt aber 46 Prozent mehr Zeichen, und tesseract kostet Zeichen und keine Fläche: je 1000 Zeichen sind es 734 ms gegen 848 ms, also **Faktor 0,87**. Der geteilte x86-Kern der Miet-Box ist nicht langsamer als der Laptopkern. Der ARM-Faktor bleibt ausdrücklich offen.
- **Die Prognose ist gerechnet statt geschätzt: rund 13 h für 50.000 Dateien auf x86.** Der Posten, der die Recherche auf 18 bis 20 h brachte, war die OCR-Sekundenzahl, und sie hat sich halbiert (2,80 s statt 5,5 s je Seite). Zwei Wege zur selben Zahl, die um 2 Prozent auseinanderliegen: aus den Einzelposten 13,1 h, linear aus dem Trockenlauf 12,8 h.
- **Der erste PostgreSQL-Lauf des Projekts ist ausgewertet, und Perf-M7 ist erstmals auf Postgres belegt behoben.** Die 32 Fehlschläge sind genau der Pfad, den M7 benennt, 32 Mal über acht Durchgänge. Die Warteschlange lief trotzdem vollständig leer, kein Ack blieb hängen, und im Datenbankprotokoll steht kein einziges `current transaction is aborted`.
- **Der Grenzwert ist eine Zahl mit Rechnung, festgelegt vor dem Lauf, den er beurteilt.** 2,0 GB für `anon`, aus 3814 MB nutzbarem Speicher, 345 MB gemessener Grundlast und 381 MB gemessener Spitze. Dazu die Härtungsprobe wortwörtlich, auf der Box ausprobiert, samt der Eigenheit, dass sich die Grenze mit `docker update` nicht wieder abnehmen lässt.

## Task Commits

1. **Task 1: Findling läuft auf der Box, und eine Suche antwortet** - `d773ac6` (docs)
2. **Zwischenbefund (RED): OOXML muss am Inhalt erkannt werden** - `8d31920` (test)
3. **Zwischenbefund (GREEN): Tabellen werden am Inhalt gelesen** - `f44ff25` (fix)
4. **Task 2: Der Trockenlauf mit 500 Dateien, und der OCR-Faktor auf ARM** - `e72dde2` (feat)
5. **Task 3: Der Grenzwert wird eine Zahl, und die Härtungsprobe wird vorbereitet** - `6a0fb1b` (docs)

**Plan-Metadaten:** dieser SUMMARY (docs)

## Files Created/Modified

- `docs/performance.md`: drei neue Abschnitte. "Installation auf der Box" (Codestand mit Digest, Registrierungsweg, die drei Feststellungen, Begleit-App, Dialekt, beide Suchbeweise, die Statusseite Kachel für Kachel), "Der Trockenlauf" (Korpus samt der an die Umgebung gebundenen Prüfsumme, der xlsx-Befund, Verdikte, OCR-Messung auf zwei Wegen, Prognosetabelle, Speicher, Indexgröße, PostgreSQL-Befund, Beobachtungen unter Last) und "Der Grenzwert, jetzt aus gemessenen Größen" (Rechnung, die drei getrennten Zahlen, Härtungsprobe, die drei Antworten für den Fall, dass sie greift). Der Bericht wächst von 554 auf 1213 Zeilen.
- `docs/measurements/2026-09-03-trockenlauf-cpx22/`: 500 Zeilen Korpusmanifest mit SHA-256 je Datei, zwei Messreihen des Samplers, beide Sampler-Kopfzeilen mit dem aufgelösten cgroup-Pfad, und ein README mit Umgebung, Spalten und Nachbauanleitung.
- `backend/src/findling/extract/office.py`: `extract_xlsx` bekommt einen offenen Datenstrom statt eines Pfades, mit der Begründung an der Stelle, an der sie steht.
- `backend/tests/test_extract_documents.py`: ein Fall über docx, pptx und xlsx unter dem Namen `job-4711.part`, also unter dem Namen, den der Poller wirklich übergibt.
- `backend/tests/test_ops_scripts.py`: Formatierung, siehe Deviations.
- `deferred-items.md`: DI-05-20 und DI-05-21.

## Decisions Made

- **Gezogen statt gebaut, für den Messlauf.** `info.xml` nennt `0.3.0`, und das gibt es auf ghcr nicht, weil der Freigabe-Tag nach D-26 erst am Ende der Phase gesetzt wird. Der Ausweg war weder ein Bau auf der Box noch eine erfundene Version, sondern die Feststellung, dass `docker.yml` jeden Commit unter seiner SHA ablegt. Damit ist der gemessene Stand nicht nur benannt, sondern über den Digest festgenagelt, und dieser Digest trägt beide Architekturen, also misst der ARM-Lauf später denselben Code (T-05-49).
- **Der Korpus entsteht im Abbild der ExApp.** Der Generator braucht Pillow, und die Box hat es nicht. Ein `pip install` auf der Messmaschine wäre ein Paketbezug außerhalb der Sperrdatei gewesen, also läuft der Generator in dem Container, dessen Pillow ohnehin gepinnt ist. Nebeneffekt: die Messung und die Erzeugung teilen dieselben Bibliotheksfassungen, was den Prüfsummenbefund unten überhaupt erst sichtbar gemacht hat.
- **Grenzwert bleibt 2,0 GB.** Die Recherche empfahl die Zahl, D-03 stellte sie ins Ermessen, und die Rechnung mit der jetzt gemessenen Grundlast bestätigt sie: 3814 minus 345 minus 2048 lässt 1421 MB für Kernel und Seitencache. Bei 2,5 GB wären es 909 MB, und das ist der Bereich, in dem der Kernel räumt statt zu arbeiten. Keine Abweichung von der Empfehlung, aber jetzt mit zwei gemessenen statt zwei geschätzten Eingangsgrößen.
- **Der xlsx-Befund wurde behoben, nicht nur notiert.** Er trifft jede Instanz, er macht den Volllauf zu einer Messung des falschen Pfades, und die Abhilfe ist eine Zeile mit einem Kommentar. Das ist Rule 1 und keine Ermessensfrage.
- **DI-05-21 wurde nicht behoben.** Ein Fehlschlag bleibt in der Fehlerliste stehen, auch wenn die Datei danach indexiert wird. Die Abhilfe entscheidet darüber, was die Zustandstabelle bedeutet, und die Aufgeben-Regel nach drei Versuchen hängt an genau der Spur, die dabei gelöscht würde. Das ist Rule 4, also ein Befund und keine Änderung.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Keine einzige Tabellendatei war indexierbar**

- **Found during:** Task 2, in der Auswertung des Trockenlaufs
- **Issue:** 32 von 500 Dateien standen auf `failed(corrupt)`, und zwar genau die 32 `.xlsx`. `openpyxl.load_workbook` prüft die Dateiendung, bevor es die Datei öffnet, und wirft `InvalidFileException` für alles außerhalb von `.xlsx`, `.xlsm`, `.xltx`, `.xltm`. Der Poller übergibt der Extraktion aber nie den Namen aus Nextcloud, sondern seine Zwischendatei `job-<Warteschlangen-Id>.part`. Die Ausnahme steht in keiner Übersetzungstabelle und wird deshalb zu `failed(corrupt)`, also zu "Datei beschädigt" auf der Statusseite. Das war keine Eigenheit des Lastkorpus: **jede Tabellendatei jeder Instanz war betroffen**, seit es die Zwischendatei gibt. python-docx und python-pptx öffnen ihr Paket am Inhalt und sind nicht betroffen, was erklärt, warum nur dieses eine Format ausfiel.
- **Warum es keine Prüfung gesehen hat:** jeder der 47 Fälle in `test_extract_documents.py` legt seine Testdatei unter dem Namen ihres Formats an, und dieselbe Blindheit steckte im Integrationsauftrag, der einen echten Korpus mit echten Namen kopiert.
- **Fix:** `extract_xlsx` übergibt einen offenen Datenstrom statt eines Pfades. Ein Datenstrom trägt keinen Namen, an dem sich prüfen ließe, also liest der Lader den Inhalt, wie es die beiden anderen Formate ohnehin tun. Dazu ein Testfall über alle drei OOXML-Formate unter dem Namen `job-4711.part`.
- **Files modified:** backend/src/findling/extract/office.py, backend/tests/test_extract_documents.py
- **Verification:** Der Testfall war vor der Korrektur rot für xlsx und grün für docx und pptx (Commit `8d31920`), danach grün für alle drei. Auf der Box zusätzlich mit einem dort gebauten Abbild belegt: der Container meldet 587 indexiert und 0 fehlgeschlagen, alle 32 Tabellen tragen `indexed`, und eine Suche nach `Zahlungseingang` liefert unter ihren 25 Treffern eine `.xlsx`.
- **Committed in:** `8d31920` (rot), `f44ff25` (grün)

**2. [Rule 3 - Blocking] `ruff format` war auf dem Ausgangsstand rot**

- **Found during:** Task 2, beim Prüfen der eigenen Änderung gegen die Gates
- **Issue:** `backend/tests/test_ops_scripts.py` aus Plan 05-10 hatte zwei Zeilen mit einfachen statt doppelten Anführungszeichen. `ruff format --check .` über das ganze Repository war damit rot, und die Projektregel verlangt beide Gates grün vor dem Push. Die eigene Änderung ließ sich so nicht sauber gegen die Gates prüfen.
- **Fix:** `ruff format` auf genau diese eine Datei.
- **Files modified:** backend/tests/test_ops_scripts.py
- **Verification:** `ruff format --check .` meldet 85 Dateien formatiert, `ruff check .` alle Prüfungen bestanden.
- **Committed in:** `f44ff25`

### Nicht behoben, sondern notiert

**3. [Rule 4 - Architectural] Ein Fehlschlag bleibt in der Fehlerliste stehen (DI-05-21)**

Nach der Korrektur meldet der Container 587 indexiert und 0 fehlgeschlagen, die Nextcloud-Seite weiterhin 32 `failed(corrupt)`, und `occ findling:diagnose` nennt für eine dieser Dateien "Datei beschädigt", während dieselbe Datei über die Suche zu finden ist. `QueueService::acknowledge()` schreibt nur für Fehlschläge und Übersprungene, also räumen erfolgreiche Dateien ihre alte Zeile nicht weg. Die Abhilfe entscheidet darüber, was die Zustandstabelle bedeutet, und die Aufgeben-Regel nach drei Versuchen hängt an derselben Spur. Notiert als DI-05-21, mit dem Hinweis für 05-14, dass der Volllauf auf einer geräumten Zustandstabelle starten sollte.

**4. [Rule 4 - Architectural] Ein Mount, den es beim ersten Durchgang nicht gab, fehlt im Nenner (DI-05-20)**

Direkt nach dem Anlegen eines zweiten Nutzers stand der Deckungsgrad auf 88 von 49, also über hundert Prozent und auf hundert gedeckelt. Heilt mit `occ findling:index --restart` und spätestens mit dem nächtlichen Vergleich. Notiert als DI-05-20.

---

**Total deviations:** 2 auto-fixed (1 Bug, 1 blockierend), 2 als Befund notiert (beide Rule 4)
**Impact on plan:** Der Bug ist der eigentliche Ertrag des Plans und liegt genau in seinem Auftrag: "die ganze Kette einmal in kurzer Form, bevor zwanzig Stunden investiert werden". Kein zusätzlicher Umfang, kein neues Paket. Auf der Box wurde nur das gepinnte Abbild ausgeführt und einmal aus der bestehenden Sperrdatei gebaut (T-05-SC gehalten).

## Issues Encountered

- **Die Prüfsumme des Korpus stimmt nicht mit der aus Plan 05-05 überein.** Seed `phase5-dry` liefert im Abbild `afe5de55...` bei 246.452.632 Byte, auf dem Entwicklungsrechner `cac56ed1...` bei 245.695.552 Byte, ein Unterschied von 0,31 Prozent. Zwei Läufe im Abbild liefern beide Male dieselbe Zahl, die Erzeugung ist also deterministisch, aber sie ist es innerhalb einer Umgebung: die Scans werden gerendert, und Schriftrasterung und Kompression hängen an Pillow, FreeType und zlib. Aufgelöst, indem beide Werte mit ihrer Umgebung im Bericht stehen und die Zusage genauer gefasst wird: reproduzierbar ist das Paar aus Seed und Abbild-Digest.
- **Der `docker restart` eines von AppAPI erzeugten Containers zerreißt den HaRP-Tunnel.** Nach einem Neustart meldet der Container `HP_SHARED_KEY is not set, no HaRP tunnel is opened` und der Poller läuft nicht mehr. Der Weg zurück ist `occ app_api:app:unregister` ohne `--rm-data` und eine neue Registrierung; der Datenspeicher bleibt dabei erhalten, was hier nebenbei die Zusage aus D-16 auf AIO belegt hat. Für Plan 05-14 heißt das: den Container nicht neu starten, sondern neu registrieren.
- **`occ findling:index --restart` fragt nach und tut ohne `-n` nichts.** Die Rückfrage ist richtig, aber in einem Skript bleibt sie unbeantwortet, der Befehl endet mit "Nothing was changed", und der Aufrufer denkt, der Neuaufbau laufe.
- **`occ files:scan --path=...` meldet auf einem noch nie vollständig durchsuchten Nutzerverzeichnis `Error during scan: mkdir(): File exists`.** Nextcloud und nicht Findling. Ein vorheriges `occ files:scan <nutzer>` räumt es aus.
- **Eine Anmeldung über `/login` ohne `Origin`-Kopfzeile antwortet mit HTTP 200 und `loginErrors: ["invalidOrigin"]`.** Wer nur den Statuscode prüft, hält das für eine geglückte Anmeldung und rätselt danach über 401 auf jedem folgenden Aufruf. Gekostet hat das eine halbe Stunde und steht deshalb im Bericht.
- **`docker update --memory` lässt sich nicht rückgängig machen.** `--memory=0` tut nichts, `--memory=-1` wird abgewiesen. Der Container trägt die harte Grenze von 2 GB jetzt und behält sie, bis er neu erzeugt wird.

## User Setup Required

Keine für diesen Plan. Unverändert bestehen bleibt: `HCLOUD_TOKEN` liegt in `C:\Users\Student\.findling-hcloud.env` und wird bis zum Abbau in 05-14 gebraucht, und die Box kostet weiter Geld.

## Next Phase Readiness

**Der Grenzwert, zum Zitieren in Plan 05-14, in einer Zeile:**

> Der Volllauf besteht, wenn er ohne Speichertod durchläuft und der höchste `anon`-Wert des Findling-Containers unter **2,0 GB** (2.147.483.648 Byte) bleibt, gefahren unter `docker update --memory=2g --memory-swap=2g nc_app_findling_backend`.

**Zustand der Box, die weiterläuft und nicht abgebaut wurde:**

| Angabe | Wert |
|---|---|
| Box | 164459278, `62.238.114.125`, `https://loadtest.infranode.dev`, läuft |
| Container | die sieben von AIO, dazu `nc_app_findling_backend` und eine lokale Registry auf 5000 |
| **Abbild im Container** | **`localhost:5000/findling_backend:05-12-fix`, auf der Box gebaut aus dem Stand von `f44ff25`** |
| harte Speichergrenze | **bereits gesetzt: `Memory=2147483648`**, und mit `docker update` nicht mehr abnehmbar |
| Nutzer | `admin` und `lasttest` (Kennwort `findling-box-probe-2026`, Wegwerfkonto der Messung) |
| Bestand | 104 Dateien der Instanz plus 500 des Trockenlaufs unter `lasttest/files/loadtest`, 246 MB |
| Volume | 41 GB frei von 49 GB |
| Zustandstabelle | trägt 32 veraltete `failed(corrupt)`-Zeilen, siehe DI-05-21 |

**Drei Punkte, die Plan 05-14 vor dem Volllauf zu erledigen hat:**

1. **Das Abbild muss die Korrektur tragen.** Der Volllauf darf nicht gegen das gezogene Kennzeichen `5c82598...` laufen, sonst misst er wieder den Fehlerpfad für alle Tabellen. Entweder gegen ein neues, von `docker.yml` unter der SHA von `f44ff25` oder später abgelegtes Abbild, oder gegen ein auf der Box gebautes, wie es jetzt läuft. Welcher Weg gewählt wurde, gehört wie hier in den Bericht.
2. **Der Trockenlauf-Korpus und die veralteten Verdikte gehören weg**, sonst trägt der Fehlerbericht des Volllaufs 32 Zeilen über Dateien, die längst indexiert sind, und der Deckungsgrad rechnet 500 zusätzliche Dateien mit.
3. **Die harte Grenze steht schon**, muss aber nach jeder Neuregistrierung neu gesetzt und mit `docker inspect` gegengeprüft werden: jede Registrierung erzeugt einen neuen Container ohne Grenze.

**Was für den ARM-Lauf gilt:** keine einzige Zahl dieses Plans trägt die Store-Aussage. Der OCR-Faktor, die Prognose, der Spitzenwert und die Indexgröße sind x86-Zahlen. Belastbar über beide Architekturen hinweg sind nur die Befunde: der xlsx-Fehler, das PostgreSQL-Ergebnis, der Registrierungsweg unter AIO und die drei Beobachtungen an der Statusseite.

## Self-Check: PASSED

| Prüfung | Ergebnis |
|---|---|
| `docs/performance.md` | vorhanden, 1213 Zeilen (vorher 554) |
| `docs/measurements/2026-09-03-trockenlauf-cpx22/` | 5 Dateien plus README |
| Commits `d773ac6`, `8d31920`, `f44ff25`, `e72dde2`, `6a0fb1b` | alle im Log |
| `uv run python -m pytest -q` | 955 bestanden, 11 übersprungen |
| `ruff check .` | alle Prüfungen bestanden |
| `ruff format --check .` | 85 Dateien formatiert |
| `pyright` | 0 Fehler, 0 Warnungen |
| `vulture` | ohne Befund |
| `git status --porcelain backend/appinfo/info.xml` | leer (T-05-50 gehalten) |
| Gedankenstriche in `docs/performance.md` und im README | keine |
| Emojis in den geänderten Dateien | keine |
| Box, Volume und Firewall | unangetastet, kein `destroy` |
| `.planning/STATE.md`, `.planning/ROADMAP.md` | nicht angefasst |
| Hintergrundläufe auf der Box | beendet, per `ps` geprüft |

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-03*
