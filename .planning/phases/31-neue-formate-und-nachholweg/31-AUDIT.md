---
phase: 31-neue-formate-und-nachholweg
audited: 2026-10-12
diff: c9ab42a1..2b5e4426
files_reviewed: 130
findings:
  critical: 0
  high: 2
  medium: 2
  low: 9
  total: 13
status: issues_found
---

# Phase 31: Security-, Bug- und Performance-Audit

**Umfang:** `git diff c9ab42a1..2b5e4426` (Basis = Elternteil von 0fc8da9e, dem
ersten Commit mit "(31-01)"; 53 Commits). Ohne `.planning/` sind es 130 Dateien,
14 494 Zeilen dazu, 605 weg (mit Planung 148 Dateien, 16 904 dazu, 650 weg).
Produktiver Code und Abläufe: 49 Dateien unter `backend/src`, `php/lib`,
`.github` und `scripts` (4811 dazu, 252 weg), vor allem `extract/{mail,archive,
legacy_doc,legacy_xls,cfb,image,dispatch,text,sandbox,errors}.py`,
`worker/{catchup,reconcile,poller,recheck}.py`, `nc/{client,queue}.py`,
`index/search.py`, `store/repo.py`, `config.py`, `main.py`, die Migration
`Version001500Date20261012000000.php`, `StorageService.php`,
`StorageCrawlJob.php`, `deploy-harp.yml` und `scripts/release/corresponding_source.py`.

Die Proben stehen als Regressionstests in `backend/tests/test_phase31_audit.py`.
Der Korpus wird zur Testlaufzeit gebaut, und zwar anders als in den Bauplänen:
ZIP-Dateien Byte für Byte aus den PKWARE-Sätzen (die Baupläne nehmen `zipfile`
und patchen), Verbunddateien mit einem eigenen kleinen Schreiber für FAT,
MiniFAT, Verzeichnis und DIFAT, Arbeitsmappen Satz für Satz (BIFF8), Mails als
rohe Bytes, HEIC über den Encoder von pillow-heif und danach Box für Box
geschnitten oder gepatcht. Jede Datei läuft durch `ExtractionWorker`, also den
echten Kindprozess mit Frist (60 s im Korpus, halbe Produktfrist) und auf Linux
mit `RLIMIT_AS`; jeder Fall prüft benanntes Urteil, lebenden Worker (die
nächste Aufgabe wird beantwortet) und eine Laufzeit unter 30 s.

**Wo gelaufen:** alle Korpusfälle lokal (Windows 11, ohne `RLIMIT_AS`, ohne
Tesseract) und in CI python.yml auf Linux mit `RLIMIT_AS` (512 MiB); die
Laufnummern stehen unter "Status nach dem Fix-Lauf".

## Security

### S1 Bösartiger Formatkorpus durch den Sandbox-Pfad

Gefahren: `uv run python -m pytest -q tests/test_phase31_audit.py -rxX` am
12.10.2026, vor jedem Fix: **74 passed, 16 xfailed** in 266,7 s; danach zwei
weitere Fälle (Word 6) und der Generationsfall, ebenfalls gefahren.

| Gruppe | Fälle | Ergebnis vor dem Fix |
|---|---|---|
| ZIP | 15 plus Mail mit ZIP-Anhang: Rate-Bombe mit gelogener kleiner Größe (deklariert 1000, real 20 MiB Nullen), gelogene große Größe, zweiter Endsatz im Kommentar, ZIP64-Locator mit widersprüchlichen Zahlen, Offsets 0xFFFFFFFF, Verzeichnis-Offset hinter dem Dateiende, lokaler Kopf hinter dem Ende, Name 64 KiB, Name mit NUL und beiden Trennern, 10 000 Einträge gleichen Namens, 10 001 Einträge, innere ZIP mit Overlap, innere ZIP mit negativem Mitglied, Tiefe 3, .eml in ZIP in ZIP | 13 benannt und schnell; 2 rot: **L-31-02** |
| ZIP als Mail-Anhang | Anhang `paket.zip` mit Wort im Inhalt | Name gefunden, Inhalt nicht (D-31-04) |
| Mail | 5000 Kopfzeilen, Betreff 1 MiB, To 1 MiB (zweimal), kaputtes base64 und quoted-printable, RFC-2231-Name mit `../`, U+202E und NUL, Content-Type mit 10 000 Parametern, Boundary-Kollision, message/rfc822 1000-fach, Content-Type 1 MiB, 600 Teile mit 8 KiB Content-Type, HTML-Teil mit externer Entity und mit SYSTEM-Doctype | 5 rot: **H-31-01**; Entity und Doctype lesen den Kanarienvogel nicht |
| Word (.doc) | Kontrolle, 3 000 000 deklarierte Stücke, 100 000 überlappende Stücke, fc genau am Stromende und eins dahinter (8 Bit und Unicode), nFib 0x00C0/0x00C1/0xFFFF, WordDocument 0 Byte, DIFAT-, MiniFAT-, Verzeichnis-, FAT-Zyklus, FAT mit 20 000 Sektoren deklariert; Word 6/95 (wIdent 0xA5DC) | alle benannt und schnell; Word 6/95 rot: **M-31-02** |
| Excel (.xls) | Kontrolle, FILEPASS hinter BOF, CONTINUE-Kette über Sektorgrenzen (1500 Strings, 31 KiB Strom), SST mit gelogener Zahl 2^31-1, Zelle (65535, 255), unbekannte BIFF-Version, String-Index hinter der Tabelle, MiniFAT-Zyklus unter dem Workbook | alle benannt und schnell |
| HEIC | Kontrolle, 100 000 x 100 000 deklariert (ispe, clap entfernt), vier Schnitte, ftyp heic mit JPEG-Inhalt, mit Vorschaubild | alle benannt; nur das Hauptbild wird geöffnet (eigener Prozess: Optionen `False False False`, 640 x 200, ein Frame, keine Vorschau in `info`, Kontrolle: die Datei trägt `thmb`) |

Einzelheiten, gefahren und nicht nur gelesen:

- **Bomben deklarieren und belegen nicht.** Die 20-MiB-Nullen sind 20 KiB
  komprimiert; `zipfile` hält an der deklarierten Größe an, die CRC schlägt
  fehl, das Mitglied bleibt Name, das nächste wird gelesen (`kleinwort`
  gefunden). Gelogen groß endet als `skipped(archive_limit)` vor dem Lesen.
- **Kein Pfad aus Namen.** Nach jedem ZIP-Fall liegt im Arbeitsverzeichnis
  genau die Korpusdatei, keine `.part`-Datei und nichts unter einem
  Mitgliedsnamen (Assertion im Test). NUL und `\` werden von `zipfile` und
  `clean_display_name` behandelt; der Name ist Anzeige, nie Pfad.
- **10 000 Einträge gleichen Namens:** 4,2 s, `indexed(truncated)` an der
  Mitgliedergrenze 1000; 10 001 Einträge: `archive_limit` vor `ZipFile`.
- **Mail im ZIP im ZIP an der Tiefengrenze** wird gelesen (Betreff gefunden),
  eine dritte Ebene beendet die ganze Datei als `archive_limit`.
- **XXE/SSRF im HTML-Teil:** Datei-URI eines Kanarienvogels im Temp-Verzeichnis
  als externe Entity (XML-Weg) und als SYSTEM-Doctype (HTML-Weg): kein Wort des
  Kanarienvogels im Text, der Betreff schon.
- **HEIC 100 000 x 100 000:** `skipped(too_large)` in 0,01 s; der Test entfernt
  dazu die `clap`-Box, sonst schneidet sie die Größe auf 640 x 200 zurück
  (gemessen: mit `clap` ergibt dieselbe Datei die echte Größe).
- **DIFAT-Zyklus:** Ein echter Zyklus braucht mehr als 109 FAT-Sektoren, also
  rund 7 MB Datei; mit kleiner Datei endet er an `check_fat_size` oder an
  olefiles DIFAT-Prüfung, beides `failed(corrupt)`. Der große Fall ist dem
  Launch-Korpus der Phase 36 überlassen (L-31-09).

### S2 Inhalte im Log

Gefahren: `test_no_line_of_the_corpus_run_carries_a_name_a_subject_or_an_address`
mit einem frischen Worker über zehn Dateien mit den Wörtern `mitgliedgeheim`,
`ueberlappgeheim`, `betreffgeheim`, `absendergeheim`, `anhanggeheim`,
`blattgeheim`, `zellgeheim`, `olegeheim`, gelesen über `caplog` und `capfd`
(das Kind erbt den stderr-Deskriptor). Positivkontrolle: ein HEIC mit 60 MP
zwischen Pixeldeckel (50 MP) und dem Doppelten lässt Pillow eine
`DecompressionBombWarning` ohne Inhalt schreiben; sie kommt im Probe an, auch
unter Windows.

Ergebnis: **rot, H-31-02.** Der Kind-stderr enthält
`archive.py:439: UserWarning: Overlapped entries: 'ueberlappgeheim.txt' (possible zip bomb)`.
Alle übrigen Wörter fehlen in jeder Zeile.

### S3 Gefahrene Musterprüfungen über den Diff

- `git diff --name-only c9ab42a1..HEAD` ohne `.planning/` (130 Dateien) per
  `grep -n "extractall\|shell=True\|str(error)\|str(exc)\|logfile=sys"` außerhalb
  der Tests: drei Treffer, alle nur Vergleiche, nie Log:
  `archive.py:136` (`str(error).startswith(_OVERLAP)`), `image.py:458`
  (`== "unknown pixel mode"`, vor Phase 31), `legacy_xls.py:180` (Vergleich mit
  den festen xlrd-Meldungen). Kein `extractall`, kein `shell=True`, xlrd schreibt
  in `_SINK`.
- Gedankenstriche: `git diff c9ab42a1..HEAD | grep "^+" | LC_ALL=C.UTF-8 grep -cP "\x{2013}|\x{2014}"`
  ergibt 0. Positivkontrolle: dieselbe Zeile findet eine Probedatei mit U+2013.
- **Suchprozess lädt keinen Leser:** `test_the_search_module_loads_no_reader_of_phase_31`
  importiert `findling.index.search` in einem frischen Interpreter: kein
  `findling.extract.*`, kein olefile, xlrd, pillow_heif, `email.parser`,
  `zipfile`. Die Speicherseite ist unter P5 gemessen.
- **Allowlist-Parität und Urteilslisten:** `test_allowlist_parity.py`,
  `test_extract_errors.py` (PHP-Paare und PHP-Reason-Liste gegen Python),
  `test_store_metadata.py`: 168 passed; mit `test_store_repo.py`
  (STATE_REASONS von repo.py) und `test_upgrade_seed_steps.py`: 280 passed.
- **Codes auf dem Draht:** `test_no_code_reaches_a_companion_that_does_not_know_it`
  über alle `Reason` x Generationen None, 0, 1, 2, 3, 4, 99 und beide Listen,
  mit eigenem Orakel (die Codes, die jede Generation dazubrachte, aus 31-02):
  kein unbekannter Code erreicht eine Companion unverändert, `archive_limit`
  geht an Generation 2 als `too_large` bzw. `corrupt`, bekannte Codes reisen
  unverändert. Grün.
- **THIRD-PARTY.md gegen das Image:** `test_third_party_versions.py` hält jede
  Zeile unter `/app/.venv` gegen die Pins; das Image installiert `uv sync
  --frozen` aus genau diesen Pins. Zusätzlich im Image `findling_backend:dev`
  nachgesehen (siehe Status). REUSE: Security scans **38268035444** auf
  2b5e4426: "Congratulations! Your project is compliant with version 3.3 of
  the REUSE Specification", pip-audit "No known vulnerabilities found".
- **deploy-harp und Workflows:** `git diff c9ab42a1..HEAD -- .github/workflows/ | grep '^+.*uses:'`
  nennt nur per SHA gepinnte Actions (upload/download-artifact, setup-php,
  setup-uv). `${{` in hinzugefügten Zeilen von deploy-harp.yml: 0. L-30-03 an
  jeder GITHUB_ENV-Stelle: Gate `test_every_value_is_checked_before_it_goes_into_the_environment`
  grün. Neu: die Prüfungen aus 31-12 matchen zeilenweise, siehe **L-31-07**.
- **Quellspiegel:** `scripts/release/corresponding_source.py --verify-only` als
  Unterprozess mit Proxy auf einen geschlossenen Port (kein Netz): echtes
  Archiv 0, manipuliert und fehlend ungleich 0; fremdes Archiv daneben und ein
  Name mit `../` ergeben 0, siehe **L-31-03**.

## Bugs

- **Nachholweg, manipulierte Marke** (`test_a_manipulated_cursor_of_part_a_starts_again_at_zero`):
  `-5`, leer, `text`, ` 12` beginnen bei 0 und erreichen `reconcile`.
  `99999999999999999999` wirft `OverflowError` (SQLite INTEGER), U+00B2 wirft
  `ValueError` aus `int()`, arabisch-indische Ziffern werden als Cursor 12
  gelesen: **L-31-01**.
- **Rückfall der Companion von 3 auf 2**
  (`test_a_companion_falling_back_to_generation_2_pauses_part_a_and_breaks_nothing`,
  echter Poller): Teil A mit Generation 3 bis zu einem gescheiterten Band,
  dann drei Runden Generation 2 (kein Band, Cursor `200` bleibt), dann wieder 3:
  Bänder 200, 200, 200, 50, das gescheiterte Band genau einmal wiederholt,
  alle 450 Kandidaten genau einmal angekommen, Marke `reconcile`. Teil B liest
  die Generation nicht: **L-31-08**.
- **Markenwechsel mitten im Zyklus:**
  `test_a_hand_switch_to_done_in_the_middle_of_the_cycle_ends_the_second_chance`
  grün (Datei 10 unter `reconcile` übergeben, Datei 20 nach `done` wie vor dem
  Upgrade aufgegeben, keine doppelt). Zwei Fälle rot, **M-31-01**: die Marke
  springt während einer gewöhnlichen Runde auf `reconcile` (Teil A endet im
  Poller, während der Abgleich läuft), dann bekommt Datei 20 zwei Chancen
  (`[10, 20, 20]` statt `[10, 20]`); und eine Aufgabe während Teil A läuft
  (Cursor `50`) geht verloren (`[]` statt `[10]`).
- **Neustart mitten im Nachholzyklus**
  (`test_a_restart_in_the_middle_of_the_cycle_walks_it_again_from_the_front`):
  der neue Prozess beginnt bei 0, läuft jede Seite einmal und schreibt `done`;
  die Datei der ersten Seite wird dabei ein zweites Mal übergeben. Kosten unter
  P4, Entscheidung **L-31-06**.
- **Einmal-Modus** (`test_with_the_reconcile_off_exactly_one_cycle_runs_and_then_none`,
  `test_a_restart_inside_the_one_cycle_runs_it_once_more_and_ends`,
  `test_the_one_cycle_is_never_the_active_reconcile`): genau ein `run_once`,
  danach bei zwei Tagen vorgestellter Uhr keiner; ein neuer Prozess mitten im
  Zyklus läuft genau einen Zyklus und endet; `active_reconcile()` ist None und
  liest `_CATCHUP_RECONCILE` nicht. Grün.
- **Gezieltes Neu-Urteil** (`test_a_mixed_page_hands_back_exactly_the_pairs_of_a_substitute`):
  eine Seite mit allen drei Codes je gegen Ersatzcode, gleichen Code und fremden
  Code, dazu ein echter Code gegen einen fremden Ersatz: genau die drei
  Ersatzcode-Paare werden eingereiht. Grün.
- **FAT-Schranke und ENDOFCHAIN an echten Dateien** (Frage aus 31-05/31-06):
  32 Altformat-Dateien dieses Rechners außerhalb des Repos (17 aus Downloads,
  11 Vorlagen einer Office-Installation, 4 weitere), Namen nicht ausgegeben.
  Deklarierte FAT minus Bedarf: bei allen 30 Verbunddateien **0** (Schranke
  "Bedarf plus 1" hält mit einem Sektor Luft). `walk_stream` über WordDocument,
  0Table/1Table, Workbook, Book: **kein** Kettenfehler, ENDOFCHAIN überall am
  Ende. Urteile: 29 indexed, 2 `unsupported_variant` (keine Office-Dateien: ein
  Graphviz-`.dot`, eine Lucene-`.doc`), 1 `failed(corrupt)`: ein Word-6-Dokument
  einer Office-Installation (wIdent 0xA5DC, nFib 0x68) wird als beschädigt
  gemeldet statt als `unsupported_variant`: **M-31-02**.
- **JPEG `out_of_memory` gegen HEIF `too_large`** (offen aus 31-07): gelesen
  und gegen den Code gehalten (`image.py:398` bis `412`), **L-31-04**.
- **Office-Mitglied ohne Vorzählung** (offen aus 31-08): `_ooxml` ruft
  `_run_ooxml_route`, das `_too_large_to_read` mit eigener `ZipFile` fragt;
  die Zahl der Köpfe der inneren DOCX zählt niemand, **L-31-05**.
- **Umbenennen .txt nach .zip mit U+001C** (offen aus 31-09):
  `poller.py:1940` übernimmt `stored_body` unverändert, `_is_archive` liest die
  neue Endung, **L-31-06**.
- **`occ findling:diagnose` zeigt `recheck_1_5_0` nicht** (offen aus 31-11 und
  31-14): Die Marke steht in state.db, der Stand ist über die Logzeilen und die
  Status-API sichtbar, ein Befehl fehlt. Kein Fehlverhalten, eine
  Sichtbarkeitslücke, **L-31-09**.

## Befunde

### H-31-01 (HIGH): Kopfzeilen einer Mail halten den einzigen Indexer bis zur Frist fest

- **Ort:** `backend/src/findling/extract/mail.py:114` bis `126` und `200` bis
  `212`; die Kosten liegen im Kopfzeilen-Parser der Standardbibliothek
  (`email.policy.default`, `_header_value_parser`), den `message[name]`,
  `get_content_type()`, `get_filename()` und der Feedparser selbst aufrufen.
- **Beleg (gefahren, Sandbox-Kind, 120 s Frist):** `To` mit 100 000 Adressen
  (1,19 MB Datei) **120,05 s, `failed(timeout)`**; dasselbe mit Namen
  (1,42 MB) 120,03 s, timeout; `Content-Type` mit 100 000 Parametern (0,99 MB)
  120,03 s, timeout; 900 Teile mit je 8 KiB `Content-Type` (7,1 MB) 96,6 s;
  Betreff 1 MiB 14,1 s. Im Prozess: `To` 4000 Adressen 0,345 s, 2000 0,132 s
  (überlinear), Betreff 160 KB 0,44 s, 1 MB 14 s.
- **Warum HIGH:** Eine Datei von gut 1 MB, weit unter `max_file_bytes`
  (50 MiB), belegt den einzigen Extraktionsplatz zwei Minuten und endet ohne
  Text; auf einer ARM-Box wird schon ein Bruchteil davon zum Timeout. Gleiche
  Klasse und gleiche Einstufung wie H1 des Sicherheitsaudits (RTF-Regex,
  `text.py:90`). Die Vorzählung `count_parts` begrenzt die Zahl der Teile,
  nicht die Länge einer Kopfzeile.
- **Fix:** eine Richtlinie, die jede Kopfzeile vor dem Parser auf eine
  gemessene Länge kürzt und je Mail ein Budget an geparsten Zeichen führt;
  ist es erschöpft, gilt der Weg "nur Kopfzeilen" wie bei zu vielen Teilen,
  Urteil `indexed(truncated)`.

### H-31-02 (HIGH): Der Name eines ZIP-Mitglieds landet im Containerlog

- **Ort:** `backend/src/findling/extract/archive.py:439` (`archive.open(info)`);
  CPython 3.13 `zipfile/__init__.py:1698` bis `1709`: zeigt das nächste
  Mitglied auf denselben lokalen Kopf (`_end_offset == header_offset`), warnt
  `zipfile` statt `BadZipFile` zu werfen, und die Warnung zitiert
  `orig_filename`.
- **Beleg:** Log-Probe oben, Kind-stderr unter Windows (über `capfd`):
  `UserWarning: Overlapped entries: 'ueberlappgeheim.txt' (possible zip bomb)`.
  Der Docstring von archive.py verspricht "only class names leave this
  module".
- **Warum HIGH:** Inhalt einer Nutzerdatei im Log (Projektregel T-02-56,
  privacy.md). Die Zeile entsteht einmal je Kindprozess (Warnfilter "default").
- **Fix:** die Warnung um `archive.open` abfangen und verwerfen; eine
  Wiederholung desselben Kopfs liest Daten, die das gemeinsame Lesebudget
  ohnehin zählt (keine Verstärkung über das Budget hinaus).

### M-31-01 (MEDIUM): Die Ausnahme für Abgeschriebene greift in der falschen Runde

- **Ort:** `backend/src/findling/worker/reconcile.py:579` bis `605`
  (`_compare` liest die Marke je Seite, die Ausnahme hängt nur an
  `== CATCHUP_RECONCILE`), dazu `run_once` Zeile 383 (die Runde gilt nur als
  Nachholzyklus, wenn sie unter der Marke begann).
- **Beleg:** zwei rote Tests oben. (a) Eine gewöhnliche Runde läuft, Teil A
  endet im Poller und setzt `reconcile`: die restlichen Seiten wenden die
  Ausnahme schon an, der folgende Nachholzyklus noch einmal, Datei 20 bekommt
  zwei Chancen. (b) Teil A steht mit Cursor `50` (ein Band kam nicht an), eine
  gewöhnliche Runde schreibt für Datei 10 das 1.4-Aufgeben, Teil A ist an 10
  schon vorbei, der Nachholzyklus sieht eine bekannte Zeile mit gleichem ETag:
  Datei 10 bekommt keine Chance (D-31-02 "jede einmal").
- **Warum MEDIUM:** Ein Versprechen der Phase (FMT-06, D-31-02) hängt an der
  zeitlichen Lage zweier Tasks. Wirkung (b): eine Datei bleibt aufgegeben und
  unauffindbar, obwohl 1.5 sie lesen könnte; Wirkung (a): eine zusätzliche
  Auslieferungsrunde. Kein Absturz, kein falscher Text.
- **Fix:** Solange der Nachholweg offen ist (Marke ist Cursor oder `reconcile`),
  wird eine abgeschriebene Datei ohne Zeile in einer gewöhnlichen Runde weder
  aufgegeben noch übergeben; nur der Nachholzyklus übergibt sie, einmal. Fehlt
  die Marke oder steht sie auf `done`, gilt die Regel von 1.4.

### M-31-02 (MEDIUM): Word 6 und Word 95 heißen beschädigt statt nicht lesbare Variante

- **Ort:** `backend/src/findling/extract/legacy_doc.py:234` bis `239`: wIdent
  wird vor nFib geprüft, und nur 0xA5EC gilt.
- **Beleg:** echte Word-6-Datei (wIdent 0xA5DC, nFib 0x68, Verbunddatei ohne
  Tabellenstrom) ergibt `failed(corrupt)`, Detail `CorruptDocument`; Korpusfälle
  `test_a_word_6_or_95_file_is_an_unsupported_variant_and_not_a_damaged_one`
  (unverschlüsselt und mit fEncrypted) rot. Docstring und D-31-03 versprechen
  `skipped(unsupported_variant)` für "Word 6 and 95 and older".
- **Warum MEDIUM:** falsches, aber benanntes Urteil über eine heile Datei, also
  dieselbe Fehlerklasse wie #18 (D-29-08); die Statusseite sagt "beschädigt",
  der Re-Check von 1.4 holt `corrupt` sogar noch einmal ab.
- **Fix:** wIdent 0xA5DC (Word 6/95) als ältere Variante erkennen: verschlüsselt
  bleibt `encrypted`, sonst `unsupported_variant`; jede andere Kennung bleibt
  `corrupt`.

### L-31-01 (LOW): Ein manipulierter Cursor von Teil A hält den Nachholweg an

- **Ort:** `backend/src/findling/worker/catchup.py:148` bis `150`
  (`int(mark) if mark.isdigit() else 0`). Dasselbe Muster in `recheck.py:87`
  (1.4) und `embedding.py:1159` (älter).
- **Beleg:** gefahren, siehe Bugs. Eine Ausnahme je Runde, der Poller schreibt
  eine Warnung mit Klassennamen und versucht es in der nächsten Runde wieder,
  ohne Ende.
- **Einordnung:** nur durch ein von Hand verändertes state.db erreichbar; der
  Container schreibt den Cursor als `str(file_id)`.

### L-31-02 (LOW): Ein negatives Mitglied beendet die ganze ZIP-Datei als beschädigt

- **Ort:** `backend/src/findling/extract/archive.py:438` bis `443`: `_copy`
  fängt um `archive.open` nur `BadZipFile`; ein negativer lokaler Offset (der
  Verzeichnis-Offset liegt hinter der Datei, `zipfile` verschiebt alle Köpfe
  um die Differenz) wirft `OSError` aus `seek`.
- **Beleg:** gefahren: äußere Datei `failed(corrupt)` mit Detail
  `builtins.OSError`; als innere ZIP-Datei beendet sie die äußere (`aussenwort`
  fehlt). Der Docstring von `_read_inner` verspricht "A broken one stays a
  name".
- **Einordnung:** trifft nur die eigene, absichtlich kaputte Datei.

### L-31-03 (LOW): Der Spiegelcheck lässt Fremdes und `../` durch

- **Ort:** `scripts/release/corresponding_source.py:130` bis `141` (`verify`
  prüft nur die erwarteten Namen) und `227` bis `234` (`_parse_expect` nimmt
  jeden Namen).
- **Beleg:** gefahren, fremdes Archiv daneben: Exitcode 0; `--expect ../x=...`
  prüft eine Datei außerhalb des Verzeichnisses: Exitcode 0.
- **Einordnung:** `publish` lädt nur die vier Namen hoch; ein fremdes Archiv
  käme also nicht in den Spiegel. Der Check sagt aber "alles in Ordnung" über
  ein Verzeichnis, das mehr enthält als behauptet.

### L-31-04 (LOW): JPEG über der Schätzung `failed(out_of_memory)`, HEIF `skipped(too_large)`

- **Ort:** `backend/src/findling/extract/image.py:406` bis `412`.
- **Einordnung:** bewusst in 31-07 (Owner-Checkpoint) so gebaut und im
  Docstring begründet: HEIF hat keinen Draft, die deklarierte Größe ist das
  Urteil; JPEG wird per Draft verkleinert, eine Überschreitung danach ist die
  Ausnahme von D-29-07. Die Ungleichheit ist sichtbar (verschiedene Wörter auf
  der Statusseite für verwandte Fälle).

### L-31-05 (LOW): Ein Office-Mitglied öffnet seine ZipFile ohne Vorzählung

- **Ort:** `archive.py:504` bis `510`, `office.py:71` bis `81`.
- **Einordnung:** gleich wie eine einzelne DOCX seit 1.0; begrenzt durch
  `max_file_bytes` je Mitglied, `_too_large_to_read`, `RLIMIT_AS` (eine DOCX mit
  einer Million Köpfen endet als `out_of_memory` der ganzen ZIP-Datei) und die
  Frist. Kein neuer Weg, nur eine neue Tür zu einem alten.

### L-31-06 (LOW): Umbenennen und Neustart, zwei Preise des Nachholwegs und des Auszugs

- **Ort:** `poller.py:1940` (Umbenennen übernimmt den gespeicherten Text) und
  `reconcile.py:270` bis `274` (Merker im Speicher).
- **Einordnung:** (a) eine vor 1.5 indexierte .txt mit U+001C, umbenannt in
  .zip, zeigt bis zur nächsten Inhaltsextraktion eine eigene Zeile als
  Präfix; Inhalt bleibt der eigene, nur Anzeige. (b) ein Neustart mitten im
  Nachholzyklus läuft ihn von vorn und übergibt die schon gesehenen
  Abgeschriebenen ein zweites Mal; Kosten gemessen unter P4.

### L-31-07 (LOW): Die Musterprüfungen aus 31-12 matchen Zeile für Zeile

- **Ort:** `.github/workflows/deploy-harp.yml:3837`, `3969`, `4078`, `4795`,
  `4852`, `4860`, `4875` (`printf '%s' "$x" | grep -Eq '^...$'`).
- **Beleg:** `grep -E` prüft jede Zeile einzeln, `335\n412` besteht `^[0-9]+$`;
  Gate `test_no_pattern_check_of_the_upgrade_steps_matches_line_by_line` rot.
- **Einordnung:** die Werte kommen einzeilig aus `sqlite3` der CI-Instanz, ein
  zweizeiliger Wert würde GITHUB_ENV laut scheitern lassen statt still
  durchzugehen. 31-13 nutzt schon `[[ =~ ]]`.

### L-31-08 (LOW): Teil B fragt die Generation der Companion nicht

- **Ort:** `reconcile.py:383` bis `416`.
- **Einordnung:** Teil A pausiert bei Generation 2 (gefahren, siehe Bugs).
  Teil B läuft, wenn die Marke einmal `reconcile` sagt, auch unter einer
  Companion der Generation 2 zu Ende; deren Seiten tragen die neuen Typen
  nicht (1.4.2 filtert nach Mimetyp), der Nachholzyklus wäre dann für diese
  Typen verbraucht. Ein Rückfall von 3 auf 2 ist kein vorgesehener Weg (die
  Upgrade-Reihenfolgen in docs/formats.md gehen nur nach oben), und der
  gewöhnliche Abgleich findet Dateien ohne Containerzeile ohnehin.

### L-31-09 (LOW): Was der Korpus dieser Phase nicht abdeckt

- DIFAT-Zyklus mit mehr als 109 FAT-Sektoren (Datei ab rund 7 MB) und
  `occ findling:diagnose` ohne Zeile für `recheck_1_5_0`.
- **Einordnung:** beides keine Fehlfunktion; der große DIFAT-Fall gehört in
  den Launch-Korpus (Phase 36), die Diagnosezeile ist eine Sichtbarkeitsfrage.

## Performance

(folgt mit Task 2)

## LOW-Entscheidungen

(folgt mit Task 3)

## Was gegengeprüft wurde, nicht nur gelesen

(folgt mit Task 3)
