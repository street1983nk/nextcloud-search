---
phase: 01-integrationsbeweis
plan: 08
subsystem: infra
tags: [nc_py_api, content-gateway, download2stream, sha256, github-actions, pdf, readonly-invariant]

requires:
  - phase: 01-integrationsbeweis (01-04)
    provides: ExApp-Geruest mit nc/client.py als einziger nc_py_api-Grenze und Gate A
  - phase: 01-integrationsbeweis (01-05)
    provides: PHP-Companion mit dem ExAppRequired-Endpunkt GET /files/{fileId}
  - phase: 01-integrationsbeweis (01-06)
    provides: integration.yml mit Nextcloud-Setup, manual_install-Daemon und ExApp-Registrierung
provides:
  - fetch_file_stream: rechtegeprueftes Lesen von Dateiinhalten als Bytestrom ueber das Content-Gateway
  - findling.tools.read_corpus: Leselauf ueber eine fileId-Liste mit Statusbericht und Exit-Code
  - testdata/corpus: sieben reproduzierbar erzeugte Referenzdateien, zwei davon absichtlich defekt
  - Gate B in der CI: Pruefsummen, mtime, Groesse und Dateizahl vor und nach dem Leselauf
  - Rechte-Negativfall im selben CI-Lauf, zweiter Nutzer bekommt null Bytes
affects: [indexierung, ocr, extraktion, queue, phase-02, phase-03]

tech-stack:
  added: []
  patterns:
    - "Private nc_py_api-API nur in einer Funktion, mit gepruefter Version im Docstring"
    - "Der Rechtefall ist ein Rueckgabewert (None), kein Ausnahmefall"
    - "Testdaten werden von einem Skript erzeugt, nie eingesammelt"
    - "Gegenprobe mit einem anderen Muster als die Umsetzung (Textscan gegen AST-Gate)"

key-files:
  created:
    - backend/src/findling/tools/read_corpus.py
    - backend/src/findling/tools/__init__.py
    - backend/tests/test_gateway_client.py
    - scripts/dev/build_corpus.py
    - testdata/corpus/README.md
    - testdata/corpus/01-text-layer.pdf
    - testdata/corpus/02-scan-no-text-layer.pdf
    - testdata/corpus/03-document.docx
    - testdata/corpus/04-notes.txt
    - testdata/corpus/05-picture.png
    - testdata/corpus/06-zero-bytes.pdf
    - testdata/corpus/07-password-protected.pdf
  modified:
    - backend/src/findling/nc/client.py
    - .github/workflows/integration.yml
    - .gitattributes

key-decisions:
  - "Gate B laeuft als eigener Job readonly-gate, nicht als Anhang am Durchstichjob: ein rotes Nur-Lesen-Gate darf nie mit einer kaputten Suche verwechselbar sein"
  - "fetch_file_stream gibt bei 404 None zurueck, statt eine Ausnahme zu werfen: der Rechtefall ist ein erwartetes Ergebnis, kein Fehler"
  - "Der Referenzkorpus wird von scripts/dev/build_corpus.py aus der Standardbibliothek erzeugt, keine eingesammelten Fremddokumente mit unklarer Lizenz"
  - "testdata/corpus ist in .gitattributes als -text markiert, sonst zerstoert ein Checkout mit autocrlf die Querverweistabelle der PDFs"
  - "Die Manipulationsprobe ist ein workflow_dispatch-Schalter im Job, nicht nur ein Satz in der Doku"

patterns-established:
  - "Statuszeilen statt Inhalten: read_corpus schreibt fileId, Status und Byte-Zahl, nie einen Dateinamen und nie ein Byte des Inhalts"
  - "Die Dateiliste wird einmal eingefroren und beide Male dieselbe Liste gehasht, sonst faellt eine geloeschte Datei durch beide Seiten des diff"
  - "Blockweises Lesen mit festem CHUNK_SIZE, damit eine grosse Datei nie vollstaendig im Speicher liegt"

requirements-completed: [COMP-02, IDX-07]

duration: 32min
completed: 2026-08-15
---

# Phase 1 Plan 08: Content-Gateway und Pruefsummen-Gate Summary

**Der Container liest Dateiinhalte rechtegeprüft als Bytestrom über `download2stream` statt über `ocs()`, und ein CI-Job belegt per sha256, mtime, Größe und Dateizahl über einen Referenzkorpus mit sieben Dateien, dass ein vollständiger Leselauf keine einzige Nutzerdatei anfasst.**

## Performance

- **Duration:** 32 min
- **Started:** 2026-08-15T11:20:00Z
- **Completed:** 2026-08-15T11:52:00Z
- **Tasks:** 2 (Task 1 im TDD-Zyklus, also 3 Commits insgesamt)
- **Files modified:** 15 (12 neu, 3 geändert)

## Accomplishments

- `fetch_file_stream` holt Dateiinhalte über den ExAppRequired-Endpunkt als Bytestrom. Der Abruf läuft bewusst nicht über `ocs()`: dessen bedingungsloses `loads(response.text)` würde an der ersten echten PDF sterben. Der Testfall dazu benutzt deshalb Binärbytes, keine TXT-Datei.
- Der Zugriff auf die private nc_py_api-Funktion sitzt in genau einer Funktion, mit der geprüften Bibliotheksversion und dem Ausweichpfad im Docstring. Ein Update trifft eine Datei.
- Ein Nutzer ohne Recht bekommt `None` und null Bytes, und zwar als normales Ergebnis: ein Leselauf über 10.000 Dateien darf nicht abbrechen, weil eine davon jemand anderem gehört.
- `findling.tools.read_corpus` liest eine fileId-Liste, meldet je Datei gelesen, nicht zugänglich oder Fehler, und setzt Exit-Code 1 nur beim Unerwarteten.
- Sieben Referenzdateien, reproduzierbar aus der Standardbibliothek erzeugt, darunter eine echte RC4-verschlüsselte PDF (Standard Security Handler, Revision 2) und eine Nullbyte-PDF. Alle mit pypdf, Pillow und python-docx gegengeprüft.
- Gate B in der CI vergleicht Prüfsummen, Änderungszeitpunkte, Größen und die Dateizahl um den Leselauf herum, und liest im selben Job dieselben fileIds noch einmal als Nutzer ohne Zugriff.

## Task Commits

1. **Task 1 (RED): fehlschlagende Tests für den Gateway-Lesepfad** - `a419ac3` (test)
2. **Task 1 (GREEN): fetch_file_stream, read_corpus, tools-Paket** - `0cf858a` (feat)
3. **Task 2: Referenzkorpus, Generator, Gate B im Workflow** - `8974bd4` (feat)

**Plan metadata:** siehe letzten Commit dieses Plans (docs)

## Files Created/Modified

- `backend/src/findling/nc/client.py` - `fetch_file_stream`, `create_app_client`, `_CountingSink`, `GATEWAY_PATH`, `CHUNK_SIZE`, Re-Export von `NextcloudException`
- `backend/src/findling/tools/read_corpus.py` - Leselauf über eine fileId-Liste, Statusbericht, Exit-Code
- `backend/src/findling/tools/__init__.py` - Paketdoku: hier darf gedruckt und ein Exit-Code gesetzt werden, im Anwendungscode nicht
- `backend/tests/test_gateway_client.py` - 9 Tests gegen einen Session-Doppelgänger, inklusive Binärnutzlast und unabhängiger Gate-A-Gegenprobe
- `scripts/dev/build_corpus.py` - erzeugt alle sieben Korpusdateien byteidentisch, nur Standardbibliothek
- `testdata/corpus/README.md` - was jede Datei ist und welchen Fehlerpfad sie provoziert
- `.github/workflows/integration.yml` - neuer Job `readonly-gate`, `workflow_dispatch`-Schalter `tamper_probe`, erweiterte Pfadfilter
- `.gitattributes` - `testdata/corpus/** -text`

## Decisions Made

- **Eigener Job statt angehängter Schritte.** Der Durchstichjob endet mit einer Deregistrierung, und ein rotes Gate B ist die schwerwiegendste Aussage, die dieses Projekt produzieren kann. Preis: das Nextcloud-Setup steht doppelt in der YAML-Datei. Das ist billiger als ein Gate, dessen Rot man auf einen kaputten Suchpfad schieben kann.
- **404 als Rückgabewert, nicht als Ausnahme.** Damit ist der Rechtefall im Aufrufer sichtbar und der Fehlerfall bleibt laut.
- **Byte-Zählung im Client statt `fp.tell()` beim Aufrufer.** Die gemeldete Zahl ist damit die Zahl, die über die Leitung ging, und funktioniert auch mit nicht seekbaren Senken.
- **Sequentieller Leselauf.** Nebenläufigkeit würde ein Speicherproblem auf einer 4-GB-Box hinter Parallelität verstecken.
- **fileIds über PROPFIND je Datei, nicht Depth 1 auf den Ordner.** Eine Depth-1-Antwort enthält den Ordner selbst, und das richtige Element mit Shell-Werkzeugen aus XML zu entfernen ist genau die Art Cleverness, die still kippt, wenn sich die Reihenfolge ändert.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `testdata/corpus/** -text` in .gitattributes ergänzt**
- **Found during:** Task 2 (Korpus committen)
- **Issue:** Die Entwicklungsmaschine checkt mit `core.autocrlf=true` aus. Gits Binärheuristik greift nur bei NUL-Bytes; die erzeugten PDFs enthalten keine, wären also als Text behandelt worden. Ein eingefügtes Wagenrücklaufzeichen verschiebt jeden Offset in der Querverweistabelle und macht aus einer gültigen PDF eine kaputte, ohne dass es jemand merkt.
- **Fix:** `testdata/corpus/** -text` mit Begründung im Kommentarblock.
- **Files modified:** `.gitattributes`
- **Verification:** `git cat-file -p :testdata/corpus/01-text-layer.pdf | sha256sum` liefert exakt den Hash des Generators (`4e30d85a...`), ebenso für `04-notes.txt` (`3b716ada...`) und `07-password-protected.pdf` (`f3c54d83...`).
- **Committed in:** `8974bd4`

**2. [Rule 2 - Missing Critical] Generatorskript `scripts/dev/build_corpus.py` angelegt**
- **Found during:** Task 2
- **Issue:** Der Plan verlangt reproduzierbar erzeugte Dateien, benennt aber keine Datei, in der die Erzeugung steht. Ohne Generator wäre der Korpus ein Satz undurchschaubarer Blobs, und eine spätere Erweiterung liefe auf eingesammelte Fremddokumente mit unklarer Lizenz hinaus.
- **Fix:** Ein Skript, nur Standardbibliothek, feste Zeitstempel und feste Dokument-ID, damit ein Neubau byteidentisch ist. Enthält die RC4-Implementierung des PDF-Standard-Security-Handlers für die passwortgeschützte Datei.
- **Files modified:** `scripts/dev/build_corpus.py`
- **Verification:** Zweiter Lauf liefert identische sha256-Werte. `ruff check` und `ruff format --check` mit der Backend-Konfiguration grün; zwei gezielte `# noqa: S105` mit Begründung, weil die Fixture-Passwörter absichtlich veröffentlicht sind.
- **Committed in:** `8974bd4`

**3. [Rule 1 - Bug] `testdata/corpus/.gitkeep` entfernt**
- **Found during:** Task 2
- **Issue:** Der Platzhalter aus der Verzeichnisanlage wäre von `cp -r` mit in die Nextcloud kopiert und als Korpusdatei gehasht worden. Eine Keep-Datei neben echten Daten ist zudem irreführend.
- **Fix:** Entfernt. Git hat die Löschung wegen gleicher Leergröße als Umbenennung nach `06-zero-bytes.pdf` aufgezeichnet; das Nettoergebnis stimmt, `git diff --diff-filter=D HEAD~1 HEAD` meldet keine Löschung.
- **Files modified:** `testdata/corpus/.gitkeep`
- **Verification:** `ls testdata/corpus | wc -l` liefert 8 (sieben Dateien plus README).
- **Committed in:** `8974bd4`

**4. [Rule 3 - Blocking] CI-Kriterium nicht lokal verifizierbar**
- **Found during:** Task 2 (Abnahmeprüfung)
- **Issue:** Das Kriterium `gh run list --workflow=integration.yml --limit 1 --json conclusion` verlangt einen abgeschlossenen CI-Lauf. Dieser Executor darf nicht pushen, und lokal existiert kein PHP.
- **Fix:** Alles lokal Prüfbare wurde geprüft (YAML-Struktur, Shell-Logik des Gates, CLI-Verdrahtung von read_corpus, alle Greps der Abnahmekriterien). Der CI-Nachweis bleibt offen und ist nach dem Push des Orchestrators mit diesem Befehl zu führen:
  ```bash
  gh run list --workflow=integration.yml --limit 2 --json name,conclusion \
    -q '.[] | "\(.name): \(.conclusion)"'
  ```
  Erwartet: beide Jobs `success`. Die Manipulationsprobe danach einmalig scharf schalten:
  ```bash
  gh workflow run integration.yml -f tamper_probe=true
  ```
  Erwartet: `readonly-gate` endet **rot** im Schritt "Gate B, not one byte and not one timestamp has moved".
- **Files modified:** keine
- **Verification:** offen, siehe oben
- **Committed in:** n/a

---

**Total deviations:** 3 auto-fixed (1 Bug, 1 fehlende kritische Funktion, 1 blockierend) plus 1 dokumentierter offener CI-Nachweis
**Impact on plan:** Kein Scope-Creep. Zwei der drei Auto-Fixes sichern die Integrität der Beweisdaten selbst; ohne sie wäre das Gate ein Gate über korrupte Dateien.

## Manipulationsprobe: Beleg

Der Plan verlangt den einmaligen Nachweis, dass das Gate bei absichtlicher Manipulation rot wird. Ohne CI-Zugriff wurde die Befehlskette des Jobs eins zu eins lokal nachgestellt (Git Bash, echte Korpusdateien, kein Nextcloud). Ergebnis:

```
frozen files: 10
== probe 0: untouched run ==
  gate exit: 0 (0 means green, as it must be without tampering)
== probe 1: one byte appended ==
  gate exit: 1 (non zero means red)
6c6
< 3b716adac526aca490761354875309de328485dbdc2346ce2874197d9a93416d *corpus/04-notes.txt
---
> b777e8e9b6c3208fb3db557c557768f5dc2f874f2653225297c6c32cb01115b2 *corpus/04-notes.txt
== probe 2: touch only, checksums untouched ==
  checksum gate exit: 0 (0, a touch changes no content)
  metadata gate exit: 1 (non zero, this is why mtime is compared)
7c7
< corpus2/05-picture.png 1786794513 140
---
> corpus2/05-picture.png 1786794514 140
== probe 3: one file deleted ==
  checksum run exit: 123 (non zero, the frozen list names a file that is gone)
  file list gate exit: 1 (non zero)
```

Vier Aussagen daraus:

1. Ohne Manipulation ist das Gate grün, es ist also kein Dauerrot.
2. Ein angehängtes Byte macht es rot.
3. Ein reines `touch` lässt jede Prüfsumme unverändert und wird trotzdem gefangen. Genau dafür steht der zweite `stat -c`-Lauf im Job.
4. Eine gelöschte Datei bricht den Prüfsummenlauf über die eingefrorene Liste ab **und** fällt im Dateilistenvergleich auf. Ein diff über frisch gesammelte Prüfsummen hätte sie auf beiden Seiten verschwinden lassen.

Die Zahl 10 statt 8 stammt aus zwei lokalen, gitignorierten Dateien im Verzeichnis (`.gitkeep` zum Zeitpunkt des Laufs, `.claude-active`); in der CI existieren nur die acht versionierten Einträge.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: elevation-of-privilege | `backend/src/findling/tools/read_corpus.py` | Das Werkzeug nimmt `--user-id` frei entgegen und liest damit die Dateien beliebiger Nutzer. Das ist keine neue Fähigkeit, sondern die Kommandozeilenform der Gateway-Architektur (der Container nennt eine userId, entscheiden darf die PHP-Seite), und sie setzt den Besitz von `APP_SECRET` voraus. Erwähnenswert bleibt sie, weil damit ein Debugging-Werkzeug im Image liegt, das im Betrieb nichts zu suchen hat. Bei der Image-Härtung in einer späteren Phase prüfen, ob `findling.tools` aus dem Produktionsimage ausgeschlossen wird. |

## Issues Encountered

- **`nc.ocs()` ist für Binärdaten unbrauchbar.** Bekannt aus der Recherche, hier bestätigt: `AsyncNcSessionBasic.ocs()` ruft bedingungslos `loads(response.text)`. Gelöst wie geplant über die private Streaming-Funktion, gekapselt und mit geprüfter Version dokumentiert.
- **Ruff sortierte den Import von `findling.tools` beim RED-Commit in den Fremdpaketblock**, weil das Modul noch nicht existierte. Nach dem GREEN-Schritt korrekt einsortiert; `ruff format --check` ist grün.
- **Keine lokale PHP- oder Nextcloud-Instanz**, deshalb ist der Ende-zu-Ende-Beweis des Gateways ein CI-Nachweis. Lokal abgesichert wurden dafür: Struktur der Workflow-YAML, die Shell-Logik des Gates (siehe Manipulationsprobe), die Verdrahtung der Kommandozeile gegen einen nicht erreichbaren Server (Statuszeilen, Exit-Code 1) und alle Greps der Abnahmekriterien.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- COMP-02 und IDX-07 sind damit erfüllt: das Content-Gateway liefert und verweigert, und beide Nur-Lesen-Gates stehen, bevor der erste Indexierungspfad entsteht.
- Für Phase 2 liegt mit `fetch_file_stream` die einzige nötige Lesefunktion bereit; Extraktoren bekommen ein Dateiobjekt und sehen die Nextcloud nie.
- Der Referenzkorpus deckt in Phase 2 direkt die Fehlerpfade ab (Nullbyte, passwortgeschützt), der große Ratsvorlagen-Korpus kommt wie geplant später dazu.
- **Offen:** der grüne CI-Lauf und die einmalige scharfe Manipulationsprobe nach dem Push, Befehle siehe Abweichung 4.
- **Empfehlung:** `.planning/REQUIREMENTS.md` markiert der Orchestrator (COMP-02, IDX-07); dieser Executor hat auftragsgemäß keine Planungsdateien außer diesem Summary angefasst.

## Self-Check: PASSED

- Alle 13 im Summary genannten neuen Dateien sind versioniert (`git ls-files`).
- Alle drei Task-Commits existieren: `a419ac3`, `0cf858a`, `8974bd4`. Der vierte ist der Commit, der dieses Summary trägt.
- Arbeitsverzeichnis sauber, keine unversionierten Rückstände.
- Fünf Python-Gates zuletzt vollständig grün: 27 Tests, ruff check, ruff format --check, pyright (0 errors), vulture.
- Alle lokal prüfbaren Abnahmekriterien beider Tasks bestanden; das eine CI-Kriterium ist als Abweichung 4 mit Prüfbefehl dokumentiert.

---
*Phase: 01-integrationsbeweis*
*Completed: 2026-08-15*
