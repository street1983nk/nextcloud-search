---
phase: 31-neue-formate-und-nachholweg
audited: 2026-10-12
diff: c9ab42a1..2b5e4426
files_reviewed: 130
findings:
  critical: 0
  high: 2
  medium: 2
  low: 10
  total: 14
status: fixed
fix_run: 2026-10-12
fix_commits: 013d1c58, 97891f3a, 004dc865, 53fae392
fixed: [H-31-01, H-31-02, M-31-01, M-31-02, L-31-01, L-31-02, L-31-03, L-31-07]
still_open: [L-31-04, L-31-05, L-31-06, L-31-08, L-31-09, L-31-10]
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
  Container schreibt den Cursor als `str(file_id)`. Der Re-Check von 1.4
  (`recheck.py`) hat dasselbe Muster, und Teil A wartet auf ihn: ein solcher
  Cursor dort hält den Nachholweg ebenso an (gefahren:
  `test_a_manipulated_cursor_of_the_re_check_of_1_4_starts_again_at_zero`, vor
  dem Fix `OverflowError`, `ValueError` und `[] == [7]`).

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

### L-31-10 (LOW): Das Neu-Urteil kostet je Seite mehr als 10 Prozent, Teil A bandet je Leseblock

- **Ort:** `reconcile.py` (`_substitute_candidates`, eine Abfrage je Seite unter
  der Marke) und `catchup.py:170` bis `190` (Bänder innerhalb eines Leseblocks
  von 2000 Zeilen).
- **Beleg (P4):** bei "Companion zuerst" mit 2 und 5 % Anteil 0,438 und
  0,447 ms je Seite gegen 0,385 und 0,387 ms ohne Prüfung (+13,8 und +15,5 %);
  Teil A schickt 2032 Kandidaten in 100 Bändern statt in 11.
- **Einordnung:** absolut 0,05 bis 0,06 ms je Seite, gegen mindestens 1 s
  Pause je Scheibe und einen HTTP-Seitenabruf; einmal je Installation, im
  Nachholzyklus. Der Anstieg mit dem Anteil ist die Arbeit selbst (gefundene
  Paare). Die 100 Bänder sind 100 kleine Anfragen statt 11 großer, ebenfalls
  einmal.

## Performance

Gemessen am 2026-10-12 zwischen 18:12 und 19:05 auf dem Entwicklungsrechner:
Windows 11 Pro 10.0.26200, Intel Core i5-1335U, 16 GB RAM, CPython 3.13.13 im
uv-Venv des Repos, Stand 02e11bf1 (vor den Fixes). Skripte nur im
Scratch-Verzeichnis, jede Messung allein auf dem Rechner, nie neben der Suite.
Alle Verfahren weichen von denen der Baupläne ab: diese maßen im Prozess mit
`tracemalloc` (31-04, 31-08) oder im Image über `/proc` (31-07); hier misst
jeder Punkt am Prozess selbst, Speicher als `PeakWorkingSetSize` der
Windows-API (resident, das Gegenstück zu VmHWM), bei den Formaten am
Sandbox-Kind.

| Nr. | Messgröße | Wert | Vergleich | Urteil |
|---|---|---|---|---|
| P1 | .eml 48 KiB, nur HTML | kalt 0,043 s, warm 0,002 s, Spitze Kind +6,1 MiB | | in Ordnung |
| P1 | .doc 192 KiB (190 000 Zeichen) | kalt 0,394 s, warm 0,002 s, +33,4 MiB | .docx gleicher Text 0,420 / 0,015 s, +35,8 MiB | in Ordnung |
| P1 | .xls 5000 Zellen | kalt 0,415 s, warm 0,009 s, +34,3 MiB | .xlsx gleiche Zellen 0,415 / 0,039 s, +30,9 MiB | in Ordnung |
| P1 | ZIP mit 50 Mitgliedern (je ein Drittel TXT, DOCX, PDF) | kalt 1,012 s, warm 0,438 s, +119,8 MiB | ein DOCX allein +35,8 MiB | in Ordnung (pdfium, python-docx und numpy im selben Kind) |
| P1 | HEIC 1600 x 600 | kalt 0,114 s, warm 0,017 s, +17,8 MiB | JPEG gleiche Größe 0,103 / 0,011 s, +16,1 MiB | in Ordnung (Dekodieren; ohne Tesseract endet beides als `ocr_unavailable`) |
| P2 | ZIP 1200 TXT-Mitglieder (2 KiB) | Median 0,68 s, `indexed(truncated)` nach 255 Mitgliedern (Textdeckel 512 000 Zeichen) | Frist 120 s, Zeitanteil 90 s | in Ordnung |
| P2 | ZIP 1200 PDF-Mitglieder | Median 3,66 s, `indexed(truncated)` an der Mitgliedergrenze 1000 | | in Ordnung |
| P2 | ZIP 1200 DOCX-Mitglieder, je ein kurzer Absatz | Median 21,64 s, `indexed(truncated)` an der Mitgliedergrenze 1000 | 21,6 ms je Mitglied, 31-08 maß 11,7 ms für einen Mix | in Ordnung, auf einer viermal langsameren Box greift der Zeitanteil (90 s) vor der Frist |
| P2 | ZIP 1200 DOCX-Mitglieder mit 2 KiB Text | Median 5,78 s, Textdeckel nach 255 | | in Ordnung |
| P3 | `snippets_for`, 20 Treffer, 200 Mitglieder, 126 700 Zeichen | 101,3 / 103,8 / 103,0 ms gegen 100,3 / 102,5 / 102,6 ms | Mehrkosten +0,9 / +1,2 / +0,4 % | in Ordnung (Grenze 20 %) |
| P3 | dasselbe bei 449 800 Zeichen (T-31-30, `str.find` über fast den ganzen Textdeckel) | 364,8 / 356,1 / 364,1 ms gegen 357,7 / 360,3 / 362,8 ms | +2,0 / -1,2 / +0,3 % | in Ordnung, im Rauschen |
| P4 | Teil A über 200 000 Zeilen, 2032 Kandidaten (1 %) | 0,235 / 0,249 / 0,251 s Rechenzeit, 100 Bänder, Prozessspitze +3,5 MiB | Bänder je Leseblock von 2000 Zeilen, also 100 statt 11 Anfragen | in Ordnung, siehe L-31-10 |
| P4 | Teil B, Abgleich einer Seite (500) ohne Marke, vor Phase 31 gegen heute (`done`) | 0,370 gegen 0,386 ms | +4,3 % (ein `read_meta` je Seite) | in Ordnung (dauerhaft, Grenze 10 %) |
| P4 | Teil B unter `reconcile`, richtige Reihenfolge, Anteil 0,5 / 2 / 5 % | 0,410 / 0,397 / 0,398 ms, 0 eingereiht | gegen `done` 0,387 / 0,385 / 0,387 ms: +5,9 / +3,1 / +2,8 % | in Ordnung |
| P4 | Teil B unter `reconcile`, Companion zuerst, Anteil 0,5 / 2 / 5 % | 0,400 / 0,438 / 0,447 ms, eingereiht 1022 / 4079 / 10 102 | gegen `done` +3,6 / **+13,8 / +15,5 %** | **L-31-10** |
| P5 | Suchprozess: `import findling.main`, kleiner Index, erste Seite `candidates` und Auszüge | nach Import 71,9 MiB, nach erster Suche 80,2 MiB, Spitze 85,2 MiB | Basis c9ab42a1: 72,1 / 80,4 / 85,4 MiB | in Ordnung (-0,2 MiB, Grenze +5 MiB) |
| P6 | Image und HEIC-RAM (aus 31-01, 31-07) | komprimiert +6,18 MB (amd64), +7,29 MB (arm64); entpackt +27,3 / +16,7 MB; HEIC 48 MP mit einer Arena VmPeak 430,6 MiB (amd64, 81,4 MiB Rest zu 512 MiB), resident 158 bis 363 MiB | RAM-Tabelle in CLAUDE.md: Tesseract-Seite 300 bis 600 MB, Kind-Deckel 512 MiB | in Ordnung, Bewertung unten |

Verfahren im Einzelnen:

- **P1:** je Datei fünfmal ein frischer `ExtractionWorker`; das Kind beurteilt
  zuerst einen abgelehnten Typ (Grundlast 22,5 MiB), dann die Datei kalt (mit
  den Importen des Lesers) und gleich danach warm. Median der fünf Läufe; die
  Spitze ist die des Kinds nach dem kalten Lauf minus die Grundlast. Dateien zur
  Laufzeit gebaut: Word mit dem Verbundschreiber des Korpus, DOCX/XLSX mit
  python-docx/openpyxl, PDF-Mitglieder aus `testdata/corpus/01-text-layer.pdf`.
- **P2:** je ZIP-Datei dreimal ein frisches Kind mit der Produktfrist 120 s,
  Median; Zahl der Abschnitte aus dem Text gezählt.
- **P3:** echte ZIP-Datei durch `extract_zip`, ihr Text in 20 Dokumente mit
  `ext zip`, derselbe Text ohne Marken in 20 Dokumente mit `ext pdf`; das
  Suchwort steht im letzten Mitglied, also am Ende des Textes. 31 Runden in
  abwechselnder Reihenfolge, Median; drei Skriptläufe, alle drei zitiert.
- **P4:** state.db mit 200 000 Zeilen per `executemany` (Saat 31), jeder Lauf
  in einem frischen Unterprozess; Teil A mit einer Queue, die sofort antwortet;
  Teil B über `Reconcile._compare` Seite für Seite (500 Zeilen, Standard von
  `FINDLING_RECONCILE_SLICE`), Median je Seite aus drei Läufen. "Vor Phase 31"
  ist der Quellbaum von c9ab42a1 (`git archive`) im selben Venv.
- **P5:** fünf frische Interpreter je Quellbaum, Median.

**Was das Neu-Urteil im schlechtesten Fall kostet:** eine Store-Abfrage je
Seite (`known_skip_reasons`, gezählt: 400 bei 400 Seiten, unter `done` 0) und
je eingereihter Datei einen Download mit Extraktion. Bei "Companion zuerst"
sind das genau die Dateien mit Ersatzcode, gemessen 1022 / 4079 / 10 102 bei
0,5 / 2 / 5 % von 200 000. Annahme zum Anteil: im CI-Korpus sind 9 von 300
Dateien übersprungen (3 %, Store upgrade 5, Lauf 38256198997), davon trägt nur
ein Teil einen der drei Codes; die Messung deckt 0,5 bis 5 % ab. Bei richtiger
Reihenfolge wird nichts eingereiht.

**Nachholdauer hochgerechnet** (CI 31-13: `done` nach 303 s, alles gefunden
nach 360 s, 300 Dateien): Die 303 s sind fast ganz der Takt des Abgleichs
(`RECONCILE_TICK_SECONDS` 300 s): der Task merkt die Marke beim nächsten Takt.
Bei 200 000 Dateien kommen hinzu: Teil A (Rechenzeit 0,25 s, 100 Anfragen),
das Abarbeiten der eingereihten Dateien (das Ruhetor vor jeder Scheibe wartet,
bis höchstens 100 Zeilen geplant sind; das ist die eigentliche Arbeit, eine
Extraktion je nachgeholter Datei) und der Gang selbst: 400 Scheiben zu je
mindestens 1 s Pause (`SLICE_PAUSE_SECONDS`) plus Seitenabruf, rund 7 bis
10 Minuten Metadaten. Ein Neustart mitten im Zyklus wiederholt diesen Gang
(L-31-06), nicht die Extraktionen.

**Bewertung P6 gegen das RAM-Budget:** Das Image wächst um rund 2 Prozent, das
ist Platte, nicht RAM. Das Kind bleibt unter seinem Deckel von 512 MiB
Adressraum; resident liegt ein 48-MP-HEIC mit 363 MiB im Bereich, den die
Tabelle für eine Tesseract-Seite vorsieht (300 bis 600 MB), und Tesseract läuft
danach als Enkel. Auf einer 4-GB-Box ergibt die Summe aus Hauptprozess
(120 bis 180 MB), Tokenizer (544 MB), Einbettung (250 bis 400 MB), Kind
(bis 363 MiB) und Tesseract (bis 600 MB) höchstens rund 2,1 GB. Kein Befund.

## LOW-Entscheidungen

| Befund | Entscheidung | Grund |
|---|---|---|
| L-31-01 manipulierter Cursor | **fix** (97891f3a) | eine Funktion `resume_after` in recheck.py, von catchup.py mitbenutzt; nur ASCII-Ziffern bis 2^63-1. Die gleiche Stelle in `embedding.py` liegt vor Phase 31 und steht in `deferred-items.md`. |
| L-31-02 negatives Mitglied | **fix** (013d1c58) | eine Zeile in `_copy`, das Versprechen "a broken one stays a name" gilt wieder; zwei Korpusfälle grün. |
| L-31-03 Spiegelcheck | **fix** (Commit mit L-31-07) | `verify` meldet fremde Einträge, `--expect` nimmt nur reine Dateinamen; kein Netz, kein Produktcode. |
| L-31-04 JPEG gegen HEIF | **accept** | Owner-Entscheid aus dem Checkpoint von 31-07, im Docstring begründet (HEIF ohne Draft, Urteil über die Datei gegen die Konfiguration); eine Vereinheitlichung änderte D-29-07 für JPEG und gehört in eine eigene Entscheidung nach v1.5. |
| L-31-05 Office-Mitglied ohne Vorzählung | **accept** | derselbe Weg wie eine einzelne DOCX seit 1.0, begrenzt durch `max_file_bytes`, `_too_large_to_read`, `RLIMIT_AS` und die Frist; der Launch-Korpus der Phase 36 nimmt eine DOCX mit einer Million Köpfen im ZIP auf. |
| L-31-06 Umbenennen und Neustart | **accept** | (a) nur Anzeige, nur Bestand vor 1.5 mit U+001C, endet mit der nächsten Inhaltsextraktion; ein Fix griffe in den heißen Pfad `_rewrite_metadata`. (b) ein Neustart wiederholt rund 7 bis 10 Minuten Metadaten bei 200 000 Dateien (P4), einmal; ein Merker auf der Platte wäre ein weiterer Markenwert. Zielphase 36 (Neustart- und Upgrade-Härtung). |
| L-31-07 zeilenweise Musterprüfung | **fix** (Commit mit L-31-03) | sieben Stellen auf `[[ =~ ]]`, das Gate nimmt nur noch diese Form an (verschärft, nicht aufgeweicht). |
| L-31-08 Teil B ohne Generation | **accept** | ein Rückfall von 3 auf 2 ist kein vorgesehener Weg; Teil A pausiert nachweislich, und der gewöhnliche Abgleich findet Dateien ohne Containerzeile. Zielphase 36 (Upgrade-Matrix). |
| L-31-09 Lücken des Korpus | **accept** | großer DIFAT-Zyklus (ab 7 MB) und eine Diagnosezeile für `recheck_1_5_0` in Phase 36 (Launch-Korpus und Admin-Sicht). |
| L-31-10 Neu-Urteil je Seite, Bänder je Block | **accept** | 0,05 bis 0,06 ms je Seite gegen mindestens 1 s Pause, einmal je Installation; die Bänderzahl kostet 100 statt 11 Anfragen, einmal. |

## Status nach dem Fix-Lauf (12.10.2026)

- 0 CRITICAL, 0 HIGH, 0 MEDIUM offen. Gefixt: H-31-01, H-31-02, L-31-02, M-31-02
  (013d1c58), M-31-01, L-31-01 (97891f3a), L-31-03, L-31-07 (004dc865);
  Schärfung der Word-Fälle 53fae392. `still_open` enthält nur LOW-accept.
  Keine Owner-Frage: kein Fix berührt Schema, Indexmarke oder Analysekette
  (D-30-08); `index/schema.py` und `index/analyzer.py` sind seit c9ab42a1
  unverändert.
- Ein Verdikt ändert sich für eine extreme Mail: eine einzelne Kopfzeile über
  32 KiB (zum Beispiel ein Content-Type mit 10 000 Parametern) macht die Mail
  jetzt `indexed(truncated)`, der Text bleibt vollständig. Eine echte Mail mit
  999 Anhängen bleibt ganz (`test_a_mail_with_999_ordinary_attachments_stays_whole`).
- Lokal vor jedem Fix-Commit: ruff check (backend und ../scripts), ruff format
  --check, pyright latest 0 Fehler, vulture grün, volle Suite: vor 013d1c58
  **5568 passed, 30 skipped, 8 xfailed**; vor 97891f3a **5576 passed,
  30 skipped, 3 xfailed**; vor 004dc865 und vor 53fae392 **5579 passed,
  30 skipped**, kein xfail mehr. Vor dem Audit: 5557 passed, 30 skipped,
  18 xfailed (02e11bf1).
- Baumhash: `PACKAGE_TREE_HASH_TODAY` 71a4df12...a5bd (013d1c58, Journal
  "Plan 31-15, Befund H-31-01, H-31-02, L-31-02 and M-31-02"), dann
  c5498922...09db (97891f3a, Journal "Plan 31-15, Befund M-31-01 and
  L-31-01"); `PACKAGE_FILES_TODAY` bleibt 79. PHP unverändert, das PHP-Paar
  bleibt.
- CI auf 53fae392 (Push `2b5e4426..53fae392`), alle per `gh run watch`
  abgewartet, alle success: Python gates **38292944805** (5591 passed,
  18 skipped; der Korpus lief dort unter Linux mit `RLIMIT_AS`), HaRP deploy
  **38292944828** (vier Jobs; stable34/ubuntu-24.04 Store upgrade 0 bis 7
  success, "all ten assurances hold", `recheck_1_5_0` done nach 302 s, alle
  Wörter nach 357 s, ZIP-Bombe `archive_limit`, Auszug mit
  `innen/notiz.txt`, die geänderten Musterprüfungen in 2b und 3c gefahren),
  Integration 38292944794, Resilience 38292944962, Multi-arch image
  38292944825, Security scans 38292944814, OpenSSF Scorecard 38292944843. PHP
  gates liefen nicht (kein `php/`-Pfad berührt).
- Image `findling_backend:dev` (erzeugt 2026-10-11T06:51Z) mit `--network none`:
  pillow_heif 1.8.0, olefile 0.47, xlrd 2.0.2, Pillow 12.3.0, x265 4.2, wie
  THIRD-PARTY.md und die Pins.

## Was gegengeprüft wurde, nicht nur gelesen

| Prüfung | Verfahren (anders als die Umsetzung) | Ergebnis |
|---|---|---|
| Bomben und kaputte Container | Korpus Byte für Byte gebaut, durch das Sandbox-Kind, Urteil, Worker und Zeit je Fall | alle benannt, keiner über 30 s nach den Fixes |
| Inhalte im Log | `capfd` über den Kind-stderr, Positivkontrolle `DecompressionBombWarning` | vor dem Fix ein Mitgliedsname, danach keiner |
| Kopfzeilen-Kosten | Sandbox-Kind mit Produktfrist 120 s, Dateien bis 7 MB | vor dem Fix drei Timeouts und 96,6 s, danach höchstens 2,66 s |
| Budget nicht zu streng | echte Mail mit 999 Anhängen und gewöhnlichen Kopfzeilen | ganz gelesen, 316 278 von 1 048 576 Budgetzeichen |
| FAT-Schranke und ENDOFCHAIN | 32 echte Altformat-Dateien des Rechners, Namen nicht ausgegeben | Schranke mit 0 Luft gehalten, keine Kette abgelehnt; Word 6 als M-31-02 gefunden |
| Wire-Codes | eigenes Orakel aus den Generationen, alle Codes x 7 Generationen | kein unbekannter Code unverändert |
| Markenwechsel, Neustart, Einmal-Modus | Reconcile mit eigenen Attrappen, echter Poller für den Generationsrückfall | M-31-01 gefunden, Rest gehalten |
| Spiegelcheck | Unterprozess mit Proxy auf geschlossenen Port | L-31-03 gefunden |
| Suchprozess | Importprobe in frischem Interpreter, Speicher gegen den Basisbaum c9ab42a1 | kein Leser geladen, -0,2 MiB |
| Performance | Windows-API am Kind und am Prozess statt `tracemalloc`, Basisbaum per `git archive` | P1 bis P6 in Ordnung, L-31-10 |
| Trennschärfe der Proben | Gegenproben G und F, siehe unten | jede rot |

### Gegenproben

Skript im Scratch-Verzeichnis: je Probe genau eine Ersetzung (muss genau einmal
passen), die genannte Auswahl von `test_phase31_audit.py`, danach die Datei aus
der Sicherung zurück und `filecmp` gleich (bei allen: `restored equal=True`).
Die G-Proben prüfen Grenzen, die vor dem Audit schon hielten; die F-Proben
nehmen einen Fix dieses Plans zurück.

| Probe | Eingriff | rot |
|---|---|---|
| G1 | `archive.py`: `budget.take_entries(count)` entfernt | 1 (10 001 Einträge) |
| G2 | `archive.py`: Tiefengrenze entfernt | 1 (Tiefe 3) |
| G3 | `archive.py`: Mitgliedsdatei nicht gelöscht | 10 von 15 ZIP-Fällen (Rest ohne gelesenes Mitglied) |
| G4c | `legacy_doc.py`: Prüfung von `lcbClx` gegen den Tabellenstrom entfernt | 1 (3 000 000 Stücke) |
| G5 | `cfb.py`: ENDOFCHAIN am Kettenende nicht verlangt | 2 (MiniFAT-Zyklus .doc und .xls) |
| G6 | `text.py`: XML-Parser mit `resolve_entities=True, load_dtd=True` | 1 (Entity im HTML-Teil) |
| G7 | `queue.py`: Generation 2 ohne Ersatz für `archive_limit` | 1 (Generation 2) |
| G8 | `image.py`: HEIF-Opener mit `thumbnails=True` | 1 (nur Hauptbild) |
| G9b | `search.py`: zusätzlich `import findling.extract.archive` | 1 (Importprobe) |
| G10 | `corresponding_source.py`: SHA-Vergleich aus | 1 (manipuliertes Archiv) |
| G11 | `poller.py`: Teil A ohne Generationsbedingung | 1 (Rückfall auf 2) |
| G12 | `reconcile.py`: Einmal-Modus prüft die Marke am Rundenanfang nicht | 1 (Abgleich aus, genau ein Zyklus) |
| G13 | `reconcile.py`: jeder gespeicherte Skip-Code wird geheilt | 1 (gemischte Seite) |
| G14 | `mail.py`: `clean_display_name` gibt den Namen roh zurück | 1 (RFC 2231 mit Bidi und NUL) |
| F1 | `mail.py`: Kürzen auf `MAX_HEADER_CHARS` aus | 1 (To 1 MiB) |
| F2 | `mail.py`: Budget nie erschöpft | 1 (600 Teile mit 8 KiB) |
| F3 | `archive.py`: Warnfilter `default` statt `ignore` | 1 (Log-Probe) |
| F4 | `archive.py`: `OSError` um `archive.open` nicht gefangen | 1 (Verzeichnis-Offset hinter dem Ende; der innere Fall war vor dem Fix rot, siehe S1) |
| F5b | `legacy_doc.py`: nur wIdent 0xA5EC zugelassen | 2 (Word 6/95 offen und verschlüsselt) |
| F6 | `reconcile.py`: Zweig `held` entfernt | 2 (beide M-31-01-Fälle) |
| F7 | `recheck.py`: wieder `mark.isdigit()` allein | 4 (Teil A und Re-Check) |
| F8 | `corresponding_source.py`: fremde Einträge nicht gemeldet | 1 |

Nicht trennscharf und deshalb ersetzt: G4 (die PlcPcd-Länge allein; die
Clx-Länge davor fängt den Fall, G4c trifft sie) und G15 (das vorzeitige Ende der
Zählung ist nur eine Abkürzung, die Grenze hält `take_entries`, G1). F5 (nur der
zweite Teil der Bedingung) blieb grün, weil Word 6 nFib < 0x00C1 trägt; F5b nimmt
den tragenden Teil zurück. Zusätzlich hält der Word-Korpus seit dieser Runde für
vier Fälle das Detail `CorruptDocument` fest, damit ein `struct.error` weiter
unten nicht dasselbe Urteil vortäuscht.
