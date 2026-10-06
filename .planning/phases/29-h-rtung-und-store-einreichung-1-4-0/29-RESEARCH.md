# Phase 29: Härtung und Store-Einreichung 1.4.0 - Research

**Researched:** 2026-10-06
**Domain:** Release-Härtung einer Nextcloud-ExApp (Python 3.13, Pillow-TIFF/JPEG-Interna, CFB/OLE-Kopf, State-DB-Verdikte, CI-Upgrade-Strecke, Store-Submission)
**Confidence:** HIGH für Code-Befunde und Pillow-Verhalten (lokal gegen Pillow 12.3.0 reproduziert), MEDIUM für Upgrade-/K6-Mechanik (aus Code und Workflow gelesen, nicht in CI gefahren), LOW für den Pillow-Upstream-PR-Zuschnitt

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Übernommen (nicht neu verhandelt)
- **D-24-04:** Der Anteils-Satz für den 1.4.0-Store-Text steht WÖRTLICH fest und wird nicht umformuliert.
- Owner-Regeln: Store/README = Faktenliste mit einer Messzahl, Entwurf vor der Abgabe dem Owner zeigen; Launch-Härtung vor der Store-Abgabe, Abgabe erst nach Owner-Abnahme; nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Abschluss fixen.
- Die Store-Messzahl kommt aus Phase 28 (Owner-Entscheid SC4/Store-Zahl in 28-11).

#### Upgrade-Strecke
- **D-29-01:** Der Upgrade-Test läuft **1.3.2 auf 1.4.0** (aktueller Store-Stand), nicht 1.3.0. Erfolgskriterium 2 der Roadmap wird entsprechend gelesen. Bestandsinstallation landet in Sparsam ohne Neu-Einbettung und ohne Umbau.

#### Issue-Fixes im Umfang (Owner 01.10., Empfehlung übernommen)
- **D-29-02 (#22):** Dateien, deren Name mit `._` beginnt (AppleDouble, macOS-Metadaten), werden immer als ausgeschlossen übersprungen (Verdikt wie "Excluded by a rule" bzw. eine passende bestehende Reason), ohne Einstellung. Mac-Bundles (.key usw.) sind KEIN Sonderfall in 1.4.0 (Rückfrage an budachst offen).
- **D-29-03 (#21):** `FINDLING_MAX_CELLS` (Default 200.000) wird in `backend/appinfo/info.xml` als Deploy-Option deklariert, mit Beschreibung wie `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES`. Keine Anzeige der Limits in der Admin-Seite in 1.4.0.
- **D-29-04 (#18):** Download-Größenprüfung: die heruntergeladenen Bytes werden gegen die Sollgröße geprüft; ein abgeschnittener Download wird als vorübergehender Fehler erneut versucht und nicht als "beschädigt" verbucht.

#### Öffentliche #18-Zusagen (Owner 06.10., alle sechs im Umfang; Quelle: .planning/todos/pending/2026-10-04-issue-18-zusagen-und-lock-timeout.md Abschnitt A, Kommentare 5970113095/5971965802/5974358682)
- **D-29-05:** Sidecar-Skip: `._*` (deckt D-29-02) UND `~$*` (Office-Lockstubs) überspringen mit ehrlichem Verdikt.
- **D-29-06:** TIFF-Decode-Shim, zwei Achsen (Dateien werden INDEXIERBAR): (a) fehlende OPEN_INFO-Einträge Grau+Extrakanal mit ExtraSamples 0/1; (b) SampleFormat-Normalisierung NUR für echtes SampleFormat 0 auf Spec-Default 1. Float16 (SampleFormat 3) wird NICHT normalisiert, bekommt ein ehrliches Urteil. Dazu Upstream-PR an Pillow vorschlagen.
- **D-29-07:** Große JPEGs per Pillow-draft-Mode bei reduzierter Skalierung dekodieren (OCR skaliert ohnehin auf 3500 px) + Header-Vorabschätzung Breite x Höhe x Kanäle gegen den Adressraum-Deckel, ehrliches Urteil statt "beschädigt".
- **D-29-08:** OLE-Sniff: Kopf d0cf11e0 unter OOXML-Endung ergibt ein ehrliches Verdikt; legacy (.xls-Streams "Workbook"/"Book") von passwortgeschützt ("EncryptionInfo"/"EncryptedPackage") unterscheiden.
- **D-29-09:** Fehlerdetail je Datei speichern (echte Reader-Exception-Klasse statt pauschal corrupt, T-02-56-konform ohne Pfad/Message-Inhalte).
- **D-29-10:** NACHPRÜFUNG der Altbestände nach dem Upgrade: Verdikte kleben an der etag; die Fix-Klassen (D-29-05..08 plus Download-Größenprüfung D-29-04) müssen aktiv neu geprüft werden. Öffentlich zugesagt ("re-checked after the upgrade, no manual cleanup").

#### Weitere Owner-Entscheide 06.10. (per Auswahlfrage)
- **D-29-11:** Box-gebundene Belege (Fall-1-Belege mit nextcloud.log/NPA_TIMEOUT/HaRP, fp32-Rückkehr-Vollständigkeitsbeleg mit Statusreihe bis embedded=indexed und leerer EMBEDDING_BACKLOG_MARK, Fall-2-Feldlauf, 250-MiB-Feldlauf an Zelle 11) werden VERSCHOBEN auf die nächste ohnehin nötige Anfahrt. Phase 29 bleibt boxlos. Die Fall-1-Diagnosezeile (Entscheid A aus dem Debug embed-handover) wird trotzdem in 29 eingebaut, nur der Feldbeleg wartet.
- **D-29-12:** note_index_files-Verdrahtung: Der Vollindex-Term (MAIN_PROCESS_PER_FILE_BYTES, 6 KiB/Datei, Quick 261005-vit) wird in 1.4.0 in die Laufzeit-Slotrechnung verdrahtet; die 12-slotkosten-Rechnung bekommt den Term ebenfalls.
- **D-29-13:** Lauf-9-Lock-Timeout (OCR-zu-Embed-Übergabe, Todo-Abschnitt B): mindestens Ausnahme-Details im requeue-Log (queue.py); Debug-Vertiefung boxlos soweit möglich.
- **D-29-14:** Kleine Härtungs-Hygiene im Umfang: aws_box.sh-Schlüsselpaar-Rest-Liste-Fix, StarletteDeprecationWarning beheben.

### Claude's Discretion
- Genaue Reason/Verdikt-Zuordnung für `._*` und `~$*` (bestehende Reason bevorzugt, sonst neue mit PHP-Parität und Übersetzungen), Ort der Prüfung (Crawl/Queue vs. Container), Retry-Mechanik der Größenprüfung im bestehenden Lease-/Attempts-Modell.
- Mechanik der Altbestands-Nachprüfung (D-29-10): wie die Fix-Klassen identifiziert und neu eingereiht werden (Verdikt-basiert, ohne Vollreindex), Migrations-/Upgrade-Haken.
- Umsetzung der Vollindex-Term-Verdrahtung (D-29-12) im bestehenden Slotkosten-Modell (config.py/probe.py).

### Deferred Ideas (OUT OF SCOPE)
- #18 eigenes Verdikt "abgeschnitten" (truncated) statt "beschädigt": erst nach belegtem Befund, Kandidat 1.4.1.
- #21 Limits in der Admin-Seite anzeigen.
- #22 Ausschlussmuster als Einstellung, Sonderbehandlung von Mac-Bundles.
- HEIF/HEIC-Opener (Hypothese aus #18, nicht belegt).
- Box-gebundene Belege (D-29-11): Fall-1-Feldbelege, fp32-Rückkehr-Vollständigkeitsbeleg, Fall-2-Feldlauf, 250-MiB-Feldlauf; nächste Anfahrt.
- Float-TIFF-Decode (SampleFormat 3): nur evaluieren, NICHT zugesagt (Korrektur 05.10.).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REL-04 | v1.4.0 eingereicht: beide Apps in gleicher Version (PHP-Kopplung K6: KIND_BATCH/Art-Filter sind Companion-Release), Härtung + Audits wie gehabt, Store-Texte gate-konform mit Owner-Abnahme (inkl. Anteils-Aussage "Findling nimmt höchstens X der Box" im Owner-Wortlaut) | Versionsstellen und Lockstep-Gate (Abschnitt "Release-Mechanik"), Pflicht-Migration Version0014xx für `backend_app_version`, UPGRADE_FROM_TAG v1.2.0 auf v1.3.2 inkl. Neubau der Saat-Zusicherung, store-submit.yml-Ablauf (2x HTTP 201), D-24-04-Satz und Messzahl-Gate `RESIDENT_FIGURE = "730.2"`, K6-Gefahr neuer Reason-Codes gegen eine alte Companion |
</phase_requirements>

## Summary

Phase 29 ist zur Hälfte Produktarbeit (sechs öffentlich zugesagte #18-Fixklassen plus #21/#22) und zur Hälfte Release-Mechanik nach dem Muster der Phase 23 (Pläne 23-01 bis 23-09: Fixes, Textentwurf mit Owner-Checkpoint, Versionssprung plus Ende-zu-Ende-Strecken, Übernahme der Texte mit Gates, Härtung plus Audit, Abgabe). Alle Produktfixe sind mit Bordmitteln lösbar, **keine neue Laufzeit-Abhängigkeit ist nötig**: der TIFF-Shim ist eine Laufzeit-Ergänzung des Moduldicts `PIL.TiffImagePlugin.OPEN_INFO`, der JPEG-Fix ist `Image.draft()` plus `exif_transpose(..., in_place=True)`, der OLE-Sniff ist ein kleiner stdlib-Leser des CFB-Verzeichnisses.

Die wichtigsten Befunde, die der Planer kennen muss, weil sie nicht in CONTEXT.md stehen: (1) Der Shim für Grau+Extrakanal funktioniert nur mit dem Ziel `("LA", "LA")`; die "richtige" Abbildung `("L", "L;16B")` scheitert auf dem libtiff-Pfad (komprimierte Dateien), `La` lässt sich nicht nach `L` konvertieren (lokal reproduziert). (2) Der SampleFormat-0-Shim hilft nur unkomprimierten Dateien; libtiff selbst lehnt SampleFormat 0 ab ("Bad value 0"), komprimierte SF0-Dateien enden mit `OSError: decoder error -2` und brauchen das ehrliche Urteil. (3) Der Speicherfresser großer JPEGs ist nicht der Decoder allein, sondern `ImageOps.exif_transpose` (lädt voll und gibt eine volle Kopie zurück) VOR `thumbnail`; gemessen auf 8192x5464: CMYK 467 MiB auf 131 MiB, RGB 466 MiB auf 48 MiB Spitze. (4) Die Fall-1-Diagnosezeile aus D-29-11/D-29-13 ist **bereits committet** (a0ac5aee, `nc/queue.py:625-640`), sie muss nur verifiziert werden. (5) `UPGRADE_FROM_TAG` steht noch auf `v1.2.0` (`deploy-harp.yml:113`), und die gone-Saat-Zusicherung (Store upgrade 2b, 3, 3b) wird beim Sprung von v1.3.2 zwangsläufig rot, weil die Migration Version001300 dort nicht mehr läuft. (6) Neue Reason-Codes an eine Companion 1.3.2 lassen die **ganze** Quittung mit HTTP 400 scheitern (`QueueController.php:479/528`), das ist eine K6-Falle für die Update-Reihenfolge.

**Primary recommendation:** Phase-23-Schnitt übernehmen (Fixes, Textentwurf, Versionssprung + Upgrade-Strecke mit neuer Saat, Text-Übernahme + Gates, Härtung + Audit, Abgabe), die sechs #18-Klassen als drei neue skipped-Reasons (`system_file`, `legacy_format`, `unsupported_variant`) plus bestehende Reasons umsetzen, die Nachprüfung D-29-10 containerseitig als einmaligen, per Meta-Marke gesicherten requeue-Lauf in Bändern unter 256 bauen, und neue Reasons sowie die Nachprüfung an die Fähigkeit der Companion koppeln.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `._*`/`~$*`-Skip (D-29-05) | Backend (Poller vor dem Download) | PHP (Reason-Liste, Label, l10n) | Der Job trägt `path`/`title` (`nc/queue.py:164-165`); Entscheid vor dem ersten Byte wie `judge()` (`worker/poller.py:1426-1433`); PHP-Exclusion bleibt Admin-Regel und wird nie gespeichert (`worker/reconcile.py:106-120`) |
| TIFF-Shim, JPEG-draft, Header-Schätzung (D-29-06/07) | Backend Extraktionskind (`extract/image.py`) | , | Läuft im Sandbox-Kind unter RLIMIT_AS; Pillow-Zustand ist prozesslokal |
| OLE-Sniff (D-29-08) | Backend Extraktionskind (`extract/dispatch.py:248` / `extract/office.py`) | PHP (Labels) | Inhaltseigenschaft der Datei, gehört vor die ZIP-Leser |
| Fehlerdetail je Datei (D-29-09) | Backend State-DB (neue Tabelle) | Backend `/diagnose`, PHP `occ findling:diagnose` | Verdikt bleibt geschlossene Liste; Detail ist Diagnosedatum |
| Download-Größenprüfung (D-29-04) | Backend (`nc/client.py:_stream_file`, Poller) | PHP Queue (retries/lock) | Nur der Container sieht die gelieferten Bytes |
| Altbestands-Nachprüfung (D-29-10) | Backend (State-DB-Auswahl + `requeue`) | PHP (`requeueAs` legt fehlende Zeilen an) | Verdikte und Pfade liegen in `state.db`; PHP-Migrationen dürfen den Container nicht fragen |
| Vollindex-Term (D-29-12) | Backend `profile.py` (note_*-Muster) | Messskript `12-slotkosten.py` | Snapshot wird nur in note_*-Settern berechnet |
| Versionskopplung K6, Migration | PHP Companion (`appinfo/info.xml`, `lib/Migration`) | Backend info.xml | `backend_app_version` muss pro Minor verworfen werden |
| Upgrade-/Fremdinstallations-Beweis | CI (`deploy-harp.yml`) | , | Einzige Stelle mit echtem `occ upgrade` |
| Store-Abgabe | CI (`release.yml`, `store-submit.yml`) | Owner (Freigabe, Token) | Signaturschlüssel nur im Secret-Store |

## Project Constraints (from CLAUDE.md)

- Python-Qualitätsgates in `backend/` lokal grün VOR jedem Commit: `uv run ruff check .`, `uv run ruff format --check .`, `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` (0 errors), `uv run vulture src tests --min-confidence 80`, `uv run pytest -q` (Vollsuite zuletzt 4436 passed / 25 skipped, ca. 525 s).
- `filterwarnings = ["error::DeprecationWarning"]` (`backend/pyproject.toml:133`): jede echte DeprecationWarning ist ein roter Test.
- Keine neuen Abhängigkeiten ohne Not; Pillow ist exakt auf `==12.3.0` gepinnt (`pyproject.toml:28`), Dependabot bewegt Pins.
- Code und Bezeichner Englisch; echte Umlaute nur in deutscher Prosa, nie in Code/Keys/URLs/YAML; keine Em-/En-Dashes (Gate `test_no_store_text_carries_a_dash_or_an_emoji`).
- README dreisprachig (DE Standard, EN, FR), alle drei pflegen.
- Owner-Regeln: Store/README = kurze Faktenliste mit genau einer Messzahl (`scan_one_measured_figure`), Entwurf vor Release dem Owner zeigen; Launch-Härtung vor der Abgabe, Abgabe erst nach Owner-Abnahme; nach jeder Phase Security-/Bug-/Performance-Audit, Befunde vor Abschluss fixen.
- Commits: Autor laut Repo-Konfiguration, keine Claude-Trailer; Push nur auf Owner-Wort (Phase-28-Lehre T-28-69: jeder Push und jeder Merge einzeln wörtlich bestätigen lassen).
- GitHub-Release-Beschreibungen englisch als Faktenliste (Owner-Regel 02.10.); Issue-Antworten erst nach Owner-Freigabe; fremde PRs/Issues nicht eigenmächtig schließen.
- Kein Bau ohne belegte Ursache (Debug-Lehre embed-handover, Owner-Entscheid "A: Nur Diagnose").
- GSD-Workflow: keine direkten Repo-Edits außerhalb eines GSD-Plans.

## Standard Stack

### Core (alles bereits im Baum, nichts neu)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pillow | 12.3.0 (uv.lock:562, gepinnt) | TIFF-Shim, `Image.draft`, `exif_transpose(in_place=True)` | Bereits direkte Kante; alle Experimente gegen genau diese Version gefahren [VERIFIED: backend/.venv pillow-12.3.0.dist-info] |
| stdlib `struct` | Python 3.13 | CFB/OLE-Header und Verzeichnis lesen | Keine Abhängigkeit, Format durch MS-CFB spezifiziert |
| stdlib `resource` | Python 3.13 (POSIX) | RLIMIT_AS lesen für die Header-Schätzung | Gleiche Quelle wie `extract/sandbox.py:104-117` |
| httpx | 0.28.1 | Download-Stream (`nc/client.py:233`) | Bestehend |
| nc_py_api | 0.30.3 | OCS-Aufrufe (requeue), `NPA_TIMEOUT` Default 30 | Bestehend [VERIFIED: .venv nc_py_api/options.py:21] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib-CFB-Leser | `olefile` | Neue Abhängigkeit, nicht im Lockfile; für vier Streamnamen unverhältnismäßig |
| Ganzdatei-Bytescan nach UTF-16-Namen | CFB-Verzeichnis lesen | Bytescan ist einfacher (so hat budachst geprüft), liest aber 12 bis 15 MB pro Datei und kann im Inhalt eines Legacy-Dokuments falsch anschlagen; Verzeichnislesen ist präzise und liest wenige Sektoren |
| `filterwarnings`-Eintrag gegen die Starlette-Warnung | Dev-Abhängigkeit `httpx2` | `httpx2` (github.com/pydantic/httpx2, erste Version 11.05.2026) wird von Starlette 1.6.0 empfohlen, slopcheck stuft es aber als [SUS] (Typosquat-Nähe zu httpx) ein; Owner-Regel "keine neuen Abhängigkeiten" |
| Umbau von 58 `TestClient(`-Stellen in 28 Testdateien auf `httpx.ASGITransport` | , | Großer Umbau ohne Produktnutzen; ASGITransport ist in httpx 0.28 nur async |

**Installation:** keine.

**Version verification:** `pillow 12.3.0`, `starlette 1.6.0`, `fastapi 0.142.2`, `httpx 0.28.1`, `niquests 3.21.0` aus `backend/.venv/Lib/site-packages/*.dist-info` gelesen [VERIFIED: lokale venv].

## Package Legitimacy Audit

Diese Phase installiert keine Pakete. Geprüft wurde nur die eine Kandidatin, die ein Fix-Weg für D-29-14 bräuchte.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| httpx2 | PyPI | 5 Monate (0.0.0 am 11.05.2026, 2.13.1 am 23.09.2026, 18 Releases) | nicht erhoben | github.com/pydantic/httpx2 (laut PyPI-Metadaten) | [SUS] "Suspiciously close to 'httpx'" | Nicht empfohlen; falls der Owner diesen Weg will: `checkpoint:human-verify` vor der Installation |
| olefile | PyPI | , | , | , | nicht geprüft | Nicht empfohlen (stdlib reicht) |

**Packages removed due to slopcheck [SLOP] verdict:** keine
**Packages flagged as suspicious [SUS]:** httpx2 (nur relevant, wenn der Owner den Dependency-Weg für D-29-14 wählt)

## Architecture Patterns

### Datenfluss der Phase (Ist plus neue Haken)

```
Nextcloud (PHP Companion)                         Container (findling_backend)
-------------------------                         ----------------------------
Crawl / Event -> oc_findling_queue  --claim-->  Poller._handle(job)
                                                  |  [NEU D-29-05] Basisname ._* / ~$* -> skipped(system_file), kein Download
                                                  |  judge(mime,size) -> Route oder Verdikt
                                                  v
                                                fetch_file_stream -> scratch
                                                  |  [NEU D-29-04] written < job.size -> vorübergehend, kein Verdikt
                                                  v
                                                Sandbox-Kind (RLIMIT_AS)
                                                  |-- Route DOCX/PPTX/XLSX: [NEU D-29-08] CFB-Kopf?
                                                  |       EncryptionInfo/EncryptedPackage -> skipped(encrypted)
                                                  |       Workbook/Book/WordDocument/...   -> skipped(legacy_format)
                                                  |-- Route OCR + Bild: [NEU D-29-06] OPEN_INFO-Shim
                                                  |       [NEU D-29-07] Header-Schätzung, draft, exif in_place
                                                  |       unknown pixel mode / SF0 komprimiert -> skipped(unsupported_variant)
                                                  v
                                                ExtractionOutcome (+ [NEU D-29-09] detail = Ausnahmeklasse)
                                                  |
                    <--acknowledge (Reason-Liste!)-+-- state.db files (+ neue Tabelle file_errors)
oc_findling_file_state                            |
                                                [NEU D-29-10] einmaliger Nachprüfungslauf:
<--requeue(file_ids, content), Band <= 200 -------  failed(corrupt|out_of_memory) + Sidecar-Namen
                                                [NEU D-29-12] profile.note_index_files(store.indexed_alive())
```

### Pattern 1: TIFF-Shim als Laufzeit-Ergänzung von OPEN_INFO (D-29-06a/b)

**Was:** `PIL.TiffImagePlugin.OPEN_INFO` ist ein Moduldict, das `_setup()` zur Laufzeit befragt (`TiffImagePlugin.py:1537-1541`, Schlüssel `(ByteOrder, Photometric, SampleFormat, FillOrder, BitsPerSample, ExtraSamples)`). Fehlende Schlüssel enden in `SyntaxError("unknown pixel mode")`, das `Image.open` als `UnidentifiedImageError` meldet. `MAX_SAMPLESPERPIXEL` wird beim Import berechnet (`:278`), die neuen Schlüssel haben höchstens 2 bzw. 6 Samples und ändern ihn nicht.

**Belegt in dieser Session (Pillow 12.3.0, Windows, Testdateien selbst erzeugt):**

| Datei | ohne Shim | Shim `("LA","LA")` | Shim `("L","L;16B")` / `("La","La")` |
|---|---|---|---|
| Grau+Extra, ExtraSamples 0, raw | UnidentifiedImageError | OK, `convert("L")` liefert den Grauwert | `L;16B` OK nur raw |
| Grau+Extra, ExtraSamples 0, LZW/Deflate (libtiff) | UnidentifiedImageError | OK | `ValueError: unknown raw mode` (libtiff-Pfad schreibt `;16B` in `;16N` um, `TiffImagePlugin.py:1604-1605`) |
| Grau+Extra, ExtraSamples 1 | UnidentifiedImageError | OK | `La`: `conversion from La to L not supported` |
| ExtraSamples 2 (Kontrolle) | OK | OK | , |

Der budachst-Dump (`issuecomment` 13:09 am 03.10.) zeigt Tag 338 = 0, Tag 277 = 2, Tag 258 = (8,8), big-endian, unkomprimiert; der Schlüssel ist also `(MM, 1, (1,), 1, (8, 8), (0,))`.

**SampleFormat 0 (D-29-06b), belegt:**

| Datei | ohne Shim | Shim "jede `(1,)`-Zeile auch als `(0,)`" |
|---|---|---|
| L / RGB, SF 0, raw | UnidentifiedImageError | OK, Pixel korrekt |
| L / RGB, SF 0, LZW | UnidentifiedImageError | `open` OK, `load()` wirft `OSError: decoder error -2`; libtiff meldet auf stderr `_TIFFVSetField: Bad value 0 for "SampleFormat" tag` |
| RGB, SF 3 (Float-Klasse) | UnidentifiedImageError | unverändert UnidentifiedImageError (gewollt, D-29-06) |

Folge: Achse b macht nur unkomprimierte SF0-Dateien lesbar. Komprimierte SF0-Dateien brauchen vor dem Laden ein ehrliches Urteil (`picture.format == "TIFF"`, `tag_v2.get(339)` enthält 0, `picture.info["compression"] != "raw"`). Achtung: Die Variantenklasse aus #18 (der "PNG"-TIFF) war nach budachsts letztem Probe **SampleFormat 3**, nicht 0; SF0 ist eine aus dem Experiment abgeleitete, im Feld nicht beobachtete Klasse.

**Unterscheidung "nicht unterstützte Variante" gegen "Müll":** `Image.open` verschluckt die Ursache. Direkt `TiffImagePlugin.TiffImageFile(path)` aufrufen, wenn die ersten vier Bytes `II*\0` oder `MM\0*` sind: eine nicht abbildbare Variante wirft `SyntaxError('unknown pixel mode')`, kaputte IFDs andere Meldungen (`'no more images in TIFF file'` im Test). Lokal belegt.

### Pattern 2: Große JPEGs (D-29-07)

**Ursache im Code:** `extract/image.py:223` ruft `ImageOps.exif_transpose(picture)` vor `thumbnail` auf. In Pillow 12.3.0 ruft `exif_transpose` zuerst `image.load()` (volle Dekodierung) und gibt ohne Drehung `image.copy()` zurück (`ImageOps.py:711` und `:757`). `thumbnail` ruft zwar intern `draft()` auf, aber erst nach dem Laden (wirkungslos) und mit `reducing_gap=2.0` auf das Doppelte des Ziels, sodass bei 8192x5464 gegen 3500 der Faktor 1 herauskommt.

**`JpegImageFile.draft(mode, size)` (JpegImagePlugin.py:428-466):** wirkt nur vor `load()` und nur einmal (`decoderconfig`-Sperre); Skala `s` aus {8,4,2,1} = größte, bei der `size` noch erreicht wird (`min(w//size_w, h//size_h)`); Moduswechsel nur RGB nach `L`/`YCbCr`; CMYK bleibt CMYK, wird aber skaliert; bei Nicht-JPEG gibt die Basisklasse `None` zurück (gefahrlos aufrufbar).

**Gemessen (Spitzen-Working-Set, Windows, 8192x5464, EXIF-Orientierung 6, Endbild jeweils 2334x3500):**

| Weg | CMYK | RGB |
|---|---|---|
| heute (`exif_transpose` + `thumbnail`) | 467 MiB | 466 MiB |
| `draft("L", Ziel)` vor `exif_transpose` | 174 MiB | 59 MiB |
| `draft` + `exif_transpose(in_place=True)` | 131 MiB | 48 MiB |

Das Ziel für `draft` muss das seitenverhältnistreue Endmaß sein (z. B. 3500x2334), nicht `(3500, 3500)`: sonst ergibt `min(8192//3500, 5464//3500) = 1` keine Reduktion. Mit `(3500, 2334)` wird `s = 2`, also 4096x2732. Unter RLIMIT_AS zählt Adressraum statt Working Set; die Größenordnung (Faktor 3,5 bis 10) bleibt die Begründung.

**Header-Schätzung:** nach `draft` steht `picture.size`/`picture.mode` fest; Schätzung `w * h * len(picture.getbands()) * bytes_je_kanal * 2` (geladenes Bild plus Arbeitskopie bei `in_place`). Vergleich gegen `resource.getrlimit(RLIMIT_AS)[0]` minus aktuelles `VmSize` aus `/proc/self/status`; auf Plattformen ohne beides keine Schätzung (Windows-Tests). Urteil bei Überschreitung: `failed(out_of_memory)` (bestehende, ehrliche Reason). Der Faktor 2 ist aus der Tabelle abgeleitet und gehört in einen Test mit kleinem Kunstdeckel, nicht in eine Feldbehauptung.

### Pattern 3: OLE/CFB-Sniff (D-29-08)

**Wo:** `extract/dispatch.py:_run_ooxml_route` (Zeile 248) vor `office.extract_*`, also nur für die drei OOXML-Routen; echte `.doc/.xls/.ppt`-Mimetypes bleiben `mime_not_allowed` (`dispatch.py:131-133`).

**Wie (MS-CFB, stdlib):** Kopf `d0cf11e0a1b11ae1`; Offset 0x1E Sector Shift (9 oder 12), 0x2C Anzahl FAT-Sektoren, 0x30 erster Verzeichnissektor, 0x4C die ersten 109 DIFAT-Einträge. Verzeichnissektoren über die FAT-Kette lesen; Eintrag = 128 Byte, Name UTF-16LE in den ersten 64 Byte, Länge bei 0x40. Harte Deckel: maximale Sektorzahl der Kette, Zyklus-Schutz (besuchte Sektoren), nur DIFAT aus dem Header (109 Einträge reichen für Verzeichnisketten in Dateien bis rund 7 MB FAT-Abdeckung bei 512er-Sektoren, darüber Rückfall), bei jedem Lesefehler Rückfall auf "OLE ohne Klassifikation". Namen: `EncryptionInfo` und `EncryptedPackage` ergeben `skipped(encrypted)` (bestehend, Label "Password protected"); `Workbook`, `Book`, `WordDocument`, `PowerPoint Document` ergeben `skipped(legacy_format)`. budachsts Datei: `EncryptionInfo yes / EncryptedPackage yes / Workbook no / Book no` (06:01 am 04.10.).

[ASSUMED] Die genauen CFB-Offsets stammen aus Trainingswissen zu MS-CFB; vor dem Bau gegen die Spezifikation [MS-CFB] Abschnitt 2.2 prüfen und mit einer selbst erzeugten Testdatei abdecken.

Einfacherer Rückfall, falls der Verzeichnisleser zu teuer wird: Chunk-Scan der Datei nach den UTF-16LE-Namen mit Überlappung (konstanter Speicher). Dann im Code benennen, dass der Inhalt eines Legacy-Dokuments theoretisch falsch anschlagen kann.

### Pattern 4: Sidecar-Skip vor dem Download (D-29-05, Discretion)

- **Ort:** `worker/poller.py` direkt vor `judge(job.mime, job.size)` (Zeile 1426), mit `PurePosixPath(job.path).name` (Fallback `job.title`). Kein Download, keine Engine, ein Verdikt. Gleiche Prüfung im Nachprüfungslauf (D-29-10) über die `path`-Spalte der State-DB, in Python und nicht per SQL `LIKE` (siehe Pitfall 6).
- **Reason:** NICHT `excluded` wiederverwenden. `excluded` ist ein Live-Zeichen der PHP-Seite, das per Design nie gespeichert wird (`worker/reconcile.py:106-120`, Kommentar "never written into the files table"); ein gespeichertes `skipped(excluded)` würde den Reconcile-Zweig `stored is None and ... EXCLUDED` (Zeile 502) und die Seite "Remove the matching entry under Excluded folders" (`AdminViewService.php:479-482`) belügen. Empfehlung: neue skipped-Reason `system_file`, Label etwa "System or helper file", Abhilfe "None. macOS metadata files (._) and Office lock files (~$) carry no document content."
- **Kosten einer neuen Reason (PHP-Parität):** `extract/errors.py` `Reason` + `STATE_REASONS`; `store/repo.py` `STATE_REASONS` (Paritätstest); `php/lib/Service/FileStateService.php` `REASONS` (102) und `STATE_REASONS` (151); `AdminViewService.php` `REASON_TEXT` (442ff); 16 l10n-Dateien (`php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{js,json}`); Kontrakttests `test_admin_ui_contract.py`, `test_extract_errors.py`. Bei drei neuen Reasons diese Arbeit einmal bündeln.

### Pattern 5: Fehlerdetail je Datei (D-29-09)

- `ExtractionOutcome` (frozen, `errors.py:191-236`) um ein optionales Feld `detail: str | None` erweitern, gefüllt in `from_exception` (`errors.py:239-255`) mit `f"{klass.__module__}.{klass.__qualname__}"` der geworfenen Klasse (nur Klassenname, nie Message: T-02-56) und an den expliziten CORRUPT-Stellen `extract/image.py:113-116` und `:136-139`, die heute ohne Klasse urteilen.
- **Speicher:** `store/schema.sql` kennt nur `CREATE ... IF NOT EXISTS`, es gibt keinen ALTER-Mechanismus (`repo.py:49-63`, "It is a mark, not a migration"). Eine neue Spalte in `files` würde einen Migrationsweg erfinden. Empfehlung nach dem Muster von Phase 6: neue Tabelle `file_errors(file_id INTEGER PRIMARY KEY, error_class TEXT NOT NULL, recorded_at INTEGER)` per `IF NOT EXISTS`; bestehende DBs absorbieren das beim nächsten Öffnen ohne Reindex; `record()` schreibt/löscht im selben Transaktionsblock.
- **Ausgabe:** `api/diagnose.py` Modell (Zeilen 85-111) um `errorClass` ergänzen; `php/lib/Command/DiagnoseCommand.php` eine Zeile `error class`; AdminViewService-Diagnose durchreichen. Prozessgrenze: das Detail muss den Pickle-Weg Kind zu Eltern überleben (frozen dataclass mit slots, Feld mit Default am Ende).

### Pattern 6: Download-Größenprüfung (D-29-04, Discretion)

- **Ist:** `_stream_file` (`nc/client.py:233-266`) zählt `written` und prüft nur die Obergrenze; `_fetch_file` (`worker/poller.py:1870-1893`) behandelt jede Ausnahme als `_GatewayDown` (stoppt den ganzen Pass).
- **Soll:** nach dem Stream `written` gegen `job.size` vergleichen; `written < job.size` ist ein vorübergehender Fehler je Datei, der den Pass NICHT stoppt. Empfehlung: eigene Ausnahme `ShortRead` (analog `FileTooLargeError`), im Poller: ein sofortiger zweiter Download im selben Pass; bleibt er kurz, die Zeile ohne Verdikt freigeben (weder `done` noch `failed`), sodass sie über das bestehende Lease-/retries-Modell der PHP-Queue wiederkommt und nach erschöpften Versuchen als `repeatedly_stuck` endet, nie als `corrupt`.
- **Sollgröße:** Bei `requeueAs` legt PHP fehlende Zeilen mit `size = 0` an (`QueueMapper.php` requeueAs, Insert-Zweig); laut Kommentar wird beim Claim aus dem Knoten aufgelöst. [ASSUMED] dass `job.size` beim Claim frisch aus dem Dateicache kommt; vor dem Bau in `QueueService::describe` prüfen. `job.size <= 0` heißt: keine Prüfung möglich, nicht als kurz werten.
- `written > job.size` ist kein Abschneiden (Datei gewachsen), bleibt unter dem bestehenden `FileTooLargeError`-Deckel.

### Pattern 7: Altbestands-Nachprüfung (D-29-10, Discretion)

- **Warum der Container und nicht eine PHP-Migration:** `is_unchanged` überspringt nur `state = 'indexed'` (`store/repo.py:393-397`), ein neu eingereihter failed-Fall wird also wirklich neu extrahiert. Die Pfade für die Sidecar-Klasse und die Verdikte stehen in `state.db`; PHP-Migrationen laufen in `occ upgrade` im Wartungsmodus und dürfen den Container nicht fragen (`Version001300Date20260924000000.php`, Klassenkommentar).
- **Mechanik:** einmaliger Lauf, gesichert durch eine Meta-Marke in `state.db` (z. B. `recheck_mark = "1.4.0-fixclasses"`; Muster wie `EMBEDDING_BACKLOG_MARK`/Cursor in `worker/embedding.py`). Auswahl: lebende Zeilen (`deleted_at IS NULL`) mit `state = 'failed' AND reason IN ('corrupt','out_of_memory')` plus alle Zeilen, deren Basisname mit `._` oder `~$` beginnt (Zustand egal: ein `._notes.txt` kann als `indexed` Müll im Index stehen). Übergabe per `DocumentQueue.requeue(ids, kind=KIND_CONTENT)` in Bändern `<= 200` (PHP `MAX_LIST_LENGTH = 256`, Muster `REQUEUE_BAND` aus reconcile, Lehre aus a0ac5aee), Cursor über `file_id` aufsteigend, Marke erst nach dem letzten Band schreiben. `requeueAs` legt fehlende Queue-Zeilen an (`QueueMapper.php` requeueAs).
- **Kein Umbau:** die Generation (`index_version`) wird NICHT angehoben (sonst Vollreindex, `index/open.py:323-338`), die Vektor-Marke bleibt. Das erfüllt D-29-01 "ohne Umbau".
- **Offen zu prüfen:** ob `ocr_failed` dazugehört. `image.py:129-135` mappt den Tod der Engine am Adressraum auf `OCR_FAILED`; mit `draft` sinkt das Engine-Bild nicht (die Engine bekommt ohnehin höchstens 3500 px). Empfehlung: nicht aufnehmen, im Audit begründen.
- **Mengen:** budachst ca. 6.685 corrupt + 1.827 out_of_memory (03.10.); in Bändern zu 200 sind das rund 43 Aufrufe, unkritisch.

### Pattern 8: Vollindex-Term zur Laufzeit (D-29-12, Discretion)

- **Ist:** `profile.main_process_bytes(index_files)` und `ocr_slots(..., index_files=0)` existieren (`profile.py:183-241`), aber `_profile_values` ruft `ocr_slots(profile, hardware, weights=weights)` ohne Term (`:260`); der Docstring sagt "No caller hands a file count in yet" (`:43-48`).
- **Soll nach dem note_*-Muster (`profile.py:397-447`):** Modulzustand `_INDEX_FILES`, Setter `note_index_files(count)`, der den Snapshot nur bei Änderung neu rechnet; `_compute(...)` und `_profile_values` bekommen den Wert durchgereicht; `reset()` setzt ihn zurück. Aufrufer: der Poller nach einem Pass mit Verdikten bzw. beim Start, mit `store.indexed_alive()` (`repo.py:1066`, lebende indexierte Dokumente). Empfehlung: auf ganze Tausend abrunden, damit der Snapshot nicht pro Pass neu entsteht und die Statusroute ruhig bleibt.
- **Wirkung:** Sparsam bleibt Wert für Wert gleich (Economy ignoriert den Term, `profile.py:225-229`; Pin-Test `test_economy_is_todays_constants_value_for_value`). Standard/Leistung verlieren mit wachsendem Bestand Slots; die Probe (`probe.judge`, `probe.py:207-226`) liest Kopfraum live und braucht den Term nicht, `probe_run.py:647` liest aber `resolution.values.ocr_slots` und sieht nach der Verdrahtung die kleinere Slotzahl (gewollt, im Test festhalten).
- **12-slotkosten.py:** `calculation()` (`docs/measurements/2026-10-abnahme-anfahrt/skripte/12-slotkosten.py:280`) addiert `MAIN_PROCESS_BASELINE_BYTES + slots*OCR_SLOT_COST_BYTES + loads + fp32`. Term additiv über ein optionales `--dateien N` (Default 0) ergänzen, damit bestehende Ausgaben bytegleich bleiben; die `CELLS`-Tabelle optional um die Dateizahl je Zelle (5.000 bzw. 52.137) erweitern. Tests in `backend/tests/test_measurement_scripts.py` pinnen Ausgaben.

### Pattern 9: D-29-13 requeue-Diagnose

**Bereits erledigt:** Commit a0ac5aee hat `DocumentQueue.requeue` (`nc/queue.py:610-649`) die Warnung "could not hand %d files to another track, %s status=%s after %.1f s" gegeben (Ausnahmetyp, HTTP-Status, Dauer, nie Text, T-24-19), mit zwei Diagnosetests in `test_queue_client.py`; die Folge-Warnung "could not move N files to the embed track, they run into the lock timeout" steht in `worker/embedding.py:276`. Owner-Entscheid Fall 1 = "A: Nur Diagnose" (`.planning/debug/embed-handover-lock-timeout.md`). Für Phase 29 bleibt: Verifikation, dass beide Zeilen im Ist stehen, und die boxlose Vertiefung als reine Analyse: `NPA_TIMEOUT` ist ein `int` (Default 30, `nc_py_api/options.py:21`) und wird an niquests als einzelner Timeout übergeben (`nc_py_api/_session.py:297`); Hypothese "30 s Connect + 30 s Read = 60 s" ist mit einem lokalen Test gegen einen absichtlich hängenden Server prüfbar, ohne Box. Kein Verhaltensbau (Owner-Entscheid A).

### Pattern 10: Release-Mechanik (REL-04, nach Phase 23)

1. **Versionsstellen in einem Commit:** `php/appinfo/info.xml` `<version>` (heute 1.3.2, Zeile 146), `backend/appinfo/info.xml` `<version>` (163) und `<image-tag>`; `backend/pyproject.toml` bleibt 0.1.0. Gate `backend/tests/test_lockstep_versions.py`, `release.yml:179-190` prüft Tag gegen beide Versionen.
2. **Pflicht-Migration:** "Every minor step needs a migration of this shape" (`php/lib/Migration/Version001300Date20260924000000.php`): eine `Version001400Date2026100X` verwirft `backend_app_version`, sonst antwortet die Suche nach dem Update leer, bis jemand die Einstellungsseite öffnet (in CI gemessen beim Sprung 1.0.3 auf 1.1.0). Mit PHPUnit-Test wie `php/tests/Unit/Version001300Date20260924000000Test.php`.
3. **Upgrade-Strecke:** `UPGRADE_FROM_TAG: v1.2.0` (`.github/workflows/deploy-harp.yml:113`) auf `v1.3.2` (Assets vorhanden: findling.tar.gz(.sig), findling_backend.tar.gz(.sig)); alle Texte, die "1.3.0 against the 1.2.0" erzählen (Zeilen 2902, 4032, 4059, 4092, 4240, 4271, 4567), umstellen. Bump VOR dem Beweis, sonst `ERROR_UP_TO_DATE` und der Migrationszweig läuft nie (Lehre 11-11, `deploy-harp.yml:4012-4021`).
4. **Neue Saat statt gone-Saat:** Store upgrade 2b sät ein `skipped(gone)` wie #14 es schrieb, und Zusicherung 3/3b erwartet dessen Reparatur durch Version001300 (`deploy-harp.yml:4265-4292`, `:4424`). Von v1.3.2 aus läuft Version001300 nicht mehr: 3/3b werden rot. Ersatz nach Muster 23-05/23-06: in Store upgrade 2 (Stand 1.3.2) eine `._seed.docx`-Datei und ein Grau+Extra-TIFF ablegen, die 1.3.2 nachweislich als `failed(corrupt)` verbucht; nach dem Upgrade zusichern: Sidecar als `skipped(system_file)`, TIFF `indexed` und per Suchwort findbar, ohne dass `index_version` steigt und ohne Neu-Einbettung (Vektor-Marke und `embedded`-Zähler unverändert), Profil `economy`.
5. **Fremdinstallation:** Schritte "Store install 0 bis 7" bestehen; nach dem Bump einfach mitlaufen lassen.
6. **Store-Texte:** Entwurf in `docs/store-listing.md` (Struktur Teil 1 bis 7 wie 1.3.0, Zeilen 865-1277), Owner-Checkpoint, dann wörtliche Übernahme in sechs `<description>` (php und backend, je en/de/fr). Gates `test_store_metadata.py`: genau eine Messzahl je Beschreibung (`scan_one_measured_figure`), `RESIDENT_FIGURE = "730.2"` bleibt (28-11: "store=kein Fall", C1 = 743,9 MB im Band), keine Dashes/Emojis.
7. **Abgabe:** `gh workflow run store-submit.yml -f tag=v1.4.0`, erwartet "release findling v1.4.0: HTTP 201" und "release findling_backend v1.4.0: HTTP 201"; Gegenprobe je App-Seite; Token-Frage an den Owner (L-16-05: neu geholtes Token vorher per leerem Aufruf prüfen, 400 = gültig, 401 = überholt); Release-Beschreibung englisch als Faktenliste; danach Antworten in #15, #18, #19, #21, #22 nur nach Owner-Freigabe.

### Anti-Patterns to Avoid
- **`excluded` speichern:** bricht Reconcile-Semantik und Abhilfetext (siehe Pattern 4).
- **SampleFormat pauschal normalisieren:** Float-Bits als Integer gelesen ergeben Müll; nur exakt `(0,)` (Korrektur 05.10.).
- **`Image.MAX_IMAGE_PIXELS = None`:** nimmt den Bombenschutz weg (`image.py:57-63`); `draft` umgeht ihn nicht, der Check läuft beim `open` gegen die volle Größe.
- **Nachprüfung über `index_version`:** löst einen Vollreindex aus und verletzt D-29-01.
- **Requeue-Bänder über 256:** PHP lehnt die ganze Liste mit 400 ab (a0ac5aee-Lehre).
- **Neue Reason-Codes ohne Fähigkeitsprüfung der Companion:** siehe Pitfall 1.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TIFF-Varianten dekodieren | eigener TIFF-Leser oder Byte-Patch der Datei | `OPEN_INFO`-Ergänzung, Pillow/libtiff dekodiert | Kompression, Strips, Byteorder, Predictor liegen in Pillow/libtiff |
| JPEG verkleinert dekodieren | eigenes Resampling nach Volldekodierung | `Image.draft()` (libjpeg DCT-Skalierung) | Nur so sinkt der Speicher schon im Decoder |
| EXIF-Drehung | eigene Orientierungstabelle | `ImageOps.exif_transpose(..., in_place=True)` | 8 Orientierungen, Tag-Bereinigung |
| Retry/Lease einer Datei | eigener Retry-Zähler im Container | PHP-Queue `retries`/`locked_at` + `repeatedly_stuck` | Überlebt Neustarts, ist schon die eine Wahrheit |
| Neu-Einreihen | eigener Queue-Insert | `requeueAs` über `DocumentQueue.requeue` | Legt fehlende Zeilen an, setzt retries 0 |
| Versionskopplung | Version in der Suchantwort | Migration pro Minor (bestehendes Muster) | Protokollwechsel in beiden Hälften wäre ein Release-Risiko |

**Key insight:** Jeder Fix dieser Phase hat im Baum schon ein Muster (note_*-Setter, requeue-Bänder, Migration pro Minor, IF-NOT-EXISTS-Tabellen, Saat-Zusicherung). Neu erfunden werden müssen nur der CFB-Verzeichnisleser und drei Reason-Codes.

## Runtime State Inventory

Die Phase ist kein Rename, aber ein Upgrade mit Datennachprüfung; daher die Inventur.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `state.db` Tabelle `files`: Verdikte `failed(corrupt)`/`failed(out_of_memory)` und Sidecar-Zeilen (budachst: 4.486 Sidecars/Lockstubs, 2.199 echte corrupt, 1.827 out_of_memory am 03.10.); `oc_findling_file_state` (Nextcloud-DB) spiegelt dieselben Verdikte | Datenmigration zur Laufzeit: einmaliger Nachprüfungslauf (Pattern 7), PHP-Spiegel wird über die normale Quittung überschrieben |
| Live service config | `oc_appconfig` `findling/backend_app_version` (aufgezeichnete Containerversion) | PHP-Migration Version0014xx verwirft den Wert (Pflicht pro Minor) |
| OS-registered state | Keine. Container und Companion registrieren nichts beim Betriebssystem; verifiziert per grep über `php/lib` und `backend/src` | keine |
| Secrets/env vars | `APPSTORE_TOKEN`, `APP_PRIVATE_KEY`, `BACKEND_PRIVATE_KEY` (GitHub Secrets, `store-submit.yml:80-82`); neue Deploy-Option `FINDLING_MAX_CELLS` wird von AppAPI mit Default als echte Umgebungsvariable gesetzt | Token-Frage an Owner; `FINDLING_MAX_CELLS`-Default exakt `200000` = `config.MAX_CELLS` (sonst Override-Fehllesung, Pitfall 4) |
| Build artifacts | Abbild-Tag `1.4.0` in ghcr (multi-arch); Pins `PACKAGE_TREE_HASH_TODAY`/`PHP_TREE_HASH_TODAY`/Dateizahlen in `backend/tests/test_measurement_scripts.py:776` und `:1602` | Bei jeder Codeänderung nachziehen (Pitfall 5) |

## Common Pitfalls

### Pitfall 1: Neue Reason-Codes gegen eine Companion 1.3.2 (K6)
**What goes wrong:** `failureList`/`skipList` in `php/lib/Controller/QueueController.php:479` und `:528` lehnen bei einem unbekannten Reason die GESAMTE Quittung ab (`return null` -> `badList()` 400). Ein Container 1.4.0 neben einer Companion 1.3.2 quittiert dann keinen einzigen Stapel mehr; Zeilen kreisen bis `repeatedly_stuck`.
**Why it happens:** ExApp und Companion werden im Store getrennt aktualisiert; die Reihenfolge wählt der Admin.
**How to avoid:** Neue Codes nur senden, wenn die Companion sie kennt. Fähigkeitssignal existiert schon: die Profilroute antwortet bei einer Companion vor 1.4.0 mit 404 (`nc/queue.py:578-600`). Sauberer: die Profilantwort der 1.4.0-Companion um ein explizites Feld (z. B. `verdicts: 2`) erweitern; ohne Signal auf die alten Codes zurückfallen (`system_file` und `unsupported_variant` auf `corrupt`, `legacy_format` auf `mime_not_allowed`) und den Nachprüfungslauf (D-29-10) erst starten, wenn das Signal da ist.
**Warning signs:** Container-Log "rejected"/400 bei acknowledge, PHP-Log "rejected a malformed queue list".

### Pitfall 2: Der TIFF-Shim mit dem "schönen" Rohmodus
**What goes wrong:** `("L","L;16B")` oder `("La","La")` sehen korrekter aus, scheitern aber auf dem libtiff-Pfad bzw. bei `convert("L")` (belegt, Pattern 1).
**How to avoid:** `("LA","LA")` für ExtraSamples 0 und 1; `_encode_frame` wandelt ohnehin nach `L` und verwirft den Kanal. Test mit raw UND LZW/Deflate, beide Byteorders.

### Pitfall 3: Shim-Schlüssel, die Pillow später selbst mitbringt
**What goes wrong:** Dependabot hebt Pillow; enthält die neue Version eigene Einträge (z. B. nach einem angenommenen Upstream-PR), überschreibt der Shim sie still.
**How to avoid:** Nur Schlüssel ergänzen, die fehlen (`setdefault`-Semantik), und ein Test, der die Abwesenheit der Schlüssel in der gepinnten Version festhält und bei einem Pillow-Bump mit klarer Meldung rot wird ("Shim prüfen/zurückbauen").

### Pitfall 4: Deklarierte Defaults werden als Admin-Override gelesen
**What goes wrong:** AppAPI injiziert jeden in `info.xml` deklarierten Default als echte Umgebungsvariable; weicht er von `config.py` ab, überstimmt er das Profil auf jeder Box (`backend/tests/test_info_xml_defaults.py`, Moduldocstring).
**How to avoid:** Für D-29-03 `<default>200000</default>` exakt gleich `config.MAX_CELLS` (`config.py:245`), und `"FINDLING_MAX_CELLS": str(config.MAX_CELLS)` in `EXPECTED` des Tests ergänzen.

### Pitfall 5: Baumhash-Pins bewegen sich mit jeder Codeänderung
**What goes wrong:** `PACKAGE_TREE_HASH_TODAY`, `PACKAGE_FILES_TODAY` (71) und `PHP_TREE_HASH_TODAY`, `PHP_FILES_TODAY` (88) in `backend/tests/test_measurement_scripts.py` werden rot, sobald `backend/src/findling` oder `php/` sich ändert; neue Dateien (CFB-Leser, Migration) ändern zusätzlich die Zahl.
**How to avoid:** Jeder Plan mit Codeänderung zieht die Pins mit Kommentar nach; bei parallelen Wellen kollidieren die Pins, also entweder seriell planen oder einen Abschluss-Task pro Welle, der die Pins einmal setzt.

### Pitfall 6: SQL-`LIKE` mit `_` und `~$`
**What goes wrong:** In `LIKE` ist `_` ein Platzhalter für ein beliebiges Zeichen; `'%/._%'` (so stand es in den #18-Abfragen) trifft auch `/.x...`, also jede versteckte Datei.
**How to avoid:** Basisname in Python prüfen (`name.startswith(("._", "~$"))`) oder `ESCAPE` verwenden.

### Pitfall 7: Info-Text der Adressraum-Variable ist unter Profilen falsch
**What goes wrong:** Die Beschreibung von `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES` sagt "Only one document is read at a time, so the number is the peak and not a multiple" (`backend/appinfo/info.xml`, Variable bei Zeile 537). Ab 1.4.0 laufen unter Standard/Leistung N Kinder, jedes mit eigenem RLIMIT_AS.
**How to avoid:** Text im Textentwurf mit dem Owner neu fassen (gleicher Satz gilt sinngemäß für die neue `FINDLING_MAX_CELLS`-Beschreibung). Außerdem rät der Abhilfetext von `out_of_memory` "lower the size cap" (`AdminViewService.php:507-510`), was für Bilder falsch ist; Kandidat für dieselbe Textrunde.

### Pitfall 8: Upgrade-Zusicherungen, die vom Ausgangstag abhängen
**What goes wrong:** Mit `UPGRADE_FROM_TAG: v1.3.2` werden die gone-Zusicherungen 3/3b rot (Pattern 10, Punkt 4); "Store upgrade 6" (Sprachwechsel-Umbau) bleibt gültig, muss aber neu gelesen werden; der `run`-Block von "Store upgrade 3" liegt bei rund 20,7k Zeichen und darf vor einem `${{ }}`-Ausdruck nicht wachsen (STATE.md, Deferred Items).
**How to avoid:** Workflow-Änderung vor dem Push gegen einen lokal nachgebauten Zustand fahren (Lehre 16-RESEARCH), Zeit für Befunde einplanen ("Ein Beweis, der zum ersten Mal wirklich greift, findet Fehler"), roter Ast zuerst wiederholen, Tag auf den Commit, der die Befunde schon enthält.

### Pitfall 9: aws_box.sh, Schlüsselpaar-ID statt Name
**What goes wrong:** Der Tag-Sweep vergleicht `tag['ResourceId']` (`scripts/ops/aws_box.sh:1395-1409`). Bei Schlüsselpaaren ist das die Schlüsselpaar-ID (`key-...`), nicht der Name `findling-loadtest` (`SSH_KEY_NAME`, Zeile 111).
**How to avoid:** In `cmd_destroy` beim `shared=`-Aufbau (Zeile 1277) die ID per `describe-key-pairs --key-names "$SSH_KEY_NAME"` (`KeyPairs[0].KeyPairId`) ergänzen; Test in `backend/tests/test_ops_scripts.py` (dort liegen die bestehenden aws_box-Tests). [ASSUMED] dass describe-tags für Key Pairs die `key-`ID als ResourceId liefert; vor dem Fix per AWS-Doku bestätigen (boxlos, kein AWS-Aufruf nötig).

### Pitfall 10: `in_place`-Drehung bei Mehrseiten-TIFF
**What goes wrong:** `_read_frames` (`image.py:189-197`) springt per `seek`; eine `in_place`-Drehung verändert `picture.im` des offenen Bildes.
**How to avoid:** `draft` und `in_place` nur im Ein-Bild-Fall (`n_frames == 1`) oder je Frame nach `seek` frisch anwenden; Testfall mit zweiseitigem TIFF und Orientierungstag.

## Code Examples

### TIFF-Shim (lokal gegen Pillow 12.3.0 verifiziert, raw und LZW)
```python
# Source: Experiment dieser Session gegen backend/.venv (Pillow 12.3.0)
from PIL import TiffImagePlugin

def _register_tiff_variants() -> None:
    info = TiffImagePlugin.OPEN_INFO
    added: dict[tuple, tuple[str, str]] = {}
    for order in (TiffImagePlugin.II, TiffImagePlugin.MM):
        # Grey plus one unspecified (0) or associated (1) extra channel.
        added[(order, 1, (1,), 1, (8, 8), (0,))] = ("LA", "LA")
        added[(order, 1, (1,), 1, (8, 8), (1,))] = ("LA", "LA")
    # SampleFormat 0 is not in the specification; 1 is its default.
    for key, value in list(info.items()):
        if key[2] == (1,):
            added[key[:2] + ((0,),) + key[3:]] = value
    for key, value in added.items():
        info.setdefault(key, value)  # never overwrite an entry Pillow ships
```

### JPEG verkleinert dekodieren (gemessen, Pattern 2)
```python
# Source: JpegImagePlugin.draft (Pillow 12.3.0, Zeilen 428-466), Messung dieser Session
width, height = picture.size
longest = max(width, height)
if longest > _MAX_EDGE_PIXELS and getattr(picture, "n_frames", 1) == 1:
    factor = _MAX_EDGE_PIXELS / longest
    picture.draft("L", (max(1, round(width * factor)), max(1, round(height * factor))))
ImageOps.exif_transpose(picture, in_place=True)
```

### Variante gegen Müll unterscheiden
```python
# Source: Experiment dieser Session; TiffImagePlugin._setup wirft SyntaxError("unknown pixel mode")
from PIL import TiffImagePlugin

def _is_unsupported_tiff_variant(path: str) -> bool:
    with open(path, "rb") as handle:
        if handle.read(4) not in (b"II*\x00", b"MM\x00*"):
            return False
    try:
        TiffImagePlugin.TiffImageFile(path).close()
    except SyntaxError as error:
        return str(error) == "unknown pixel mode"
    except Exception:
        return False
    return False
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Starlette-TestClient mit `httpx` | Starlette empfiehlt `httpx2` und warnt mit `StarletteDeprecationWarning` (UserWarning-Unterklasse, nicht DeprecationWarning) | Starlette 1.6.0 (im Lock seit Dependabot #24, aae091bd) | Warnung wird vom `error::DeprecationWarning`-Filter NICHT erfasst; Fix: gezielter `filterwarnings`-Eintrag `ignore:Using .httpx. with .starlette.testclient. is deprecated:starlette.exceptions.StarletteDeprecationWarning` mit Begründungskommentar (Empfehlung) oder Owner-Entscheid für `httpx2` als Dev-Abhängigkeit |
| Pillow ignoriert unspezifizierte Extrakanäle nur bei PlanarConfiguration 2 | unverändert auf Pillow main | PR python-pillow/Pillow#9514, gemergt 30.03.2026 | Präzedenz für einen Upstream-Vorschlag "contiguous grey + unspecified extra" |

**Upstream-PR-Zuschnitt (D-29-06, nur Vorschlag):** Pillow main hat weiterhin nur `(II|MM, 1, (1,), 1, (8, 8), (2,)) -> ("LA","LA")` und für Palette `(.., 3, .., (8, 8), (0,)) -> ("P","PX")` mit `{IMAGING_MODE_P, IMAGING_RAWMODE_PX, 16, unpackL16B}` in `Unpack.c` [VERIFIED: raw.githubusercontent.com/python-pillow/Pillow/main]. Ein sauberer PR bräuchte einen neuen Rohmodus `LX` für Modus `L` analog `PX` (C-Änderung in `Unpack.c` plus Modus-Tabelle) und Testbilder; die rein Python-seitige Abbildung auf `LA` ist semantisch angreifbar (unspezifiziert ist nicht Alpha). Empfehlung: zuerst ein Issue mit der Repro-Datei (selbst erzeugt, keine budachst-Datei) und Verweis auf #9514 eröffnen, PR erst nach Rückmeldung; Owner-Freigabe vor dem Posten (Außenkommunikation). [ASSUMED] Aufwand und Annahmebereitschaft upstream.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | CFB-Offsets (0x1E, 0x2C, 0x30, 0x4C, 128-Byte-Einträge, Name 64 Byte UTF-16LE) | Pattern 3 | Sniff erkennt nichts oder falsch; Tests mit selbst erzeugter CFB-Datei fangen es |
| A2 | `job.size` kommt beim Claim frisch aus dem Dateicache, auch für per `requeueAs` mit `size = 0` angelegte Zeilen | Pattern 6 | Falsche Kurz-Erkennung; Gegenmittel `job.size <= 0` nicht prüfen |
| A3 | Ein abgeschnittener Download kommt bei Content-Length meist als `httpx.RemoteProtocolError` (dann heute schon `_GatewayDown`), die neue Prüfung fängt den Rest (chunked/Proxy) | Pattern 6 | Prüfung ist dann rein defensiv, kein Schaden |
| A4 | describe-tags liefert für Key Pairs die `key-`ID als ResourceId | Pitfall 9 | Fix greift nicht; Test mit simulierter Antwort |
| A5 | Faktor 2 der Header-Schätzung reicht unter RLIMIT_AS (Adressraum, nicht RSS) | Pattern 2 | Zu viele oder zu wenige out_of_memory-Urteile; im Feld erst bei nächster Anfahrt prüfbar (D-29-11) |
| A6 | Upstream-Pillow nimmt einen `LX`-Rohmodus an | State of the Art | Nur Außenwirkung, Shim bleibt |
| A7 | 60 s im Fall 1 = Connect plus Read bei `NPA_TIMEOUT` 30 | Pattern 9 | Nur Analyse, kein Bau |

## Open Questions (RESOLVED)

Alle fünf Fragen sind mit der jeweiligen Empfehlung entschieden. Die Empfehlungen gelten als Owner-Vorgabe (CONTEXT-Ergänzung 06.10., Owner-Entscheide per Auswahlfrage); die Pläne setzen sie um, der Owner ratifiziert sie in Plan 29-02 Teil 9 nur noch, eine Abweichung dort wäre eine neue Owner-Entscheidung mit Nacharbeit.

1. **(RESOLVED) Verdikt-Art für `legacy_format` und `unsupported_variant`: skipped oder failed?**
   - What we know: `errors.py:3-9`: skipped = "entschieden, nicht zu indexieren", failed = "wollten und konnten nicht"; Präzedenz `encrypted` und `mime_not_allowed` sind skipped; öffentlich zugesagt ist nur "honest verdict" bzw. "named password-protected or legacy format".
   - What's unclear: ob der Owner diese Klassen im Fehlerzähler der Statusseite sehen will.
   - Recommendation: skipped (keine Admin-Aktion möglich, wie `mime_not_allowed`); dem Owner im Textentwurf-Checkpoint mit vorlegen, dort entstehen ohnehin die Labels.
   - Resolution: skipped, auch für `system_file`. Umgesetzt in 29-01 (Reasons unter State.SKIPPED), genutzt in 29-05/29-07/29-08; 29-02 Teil 9 ratifiziert.

2. **(RESOLVED) D-29-14 Starlette: Filter oder `httpx2`?**
   - What we know: Warnung ist testseitig (`src` nutzt keinen TestClient), `httpx2` ist [SUS] und neu.
   - Recommendation: gezielter Filter mit Kommentar und Verweis auf den Starlette-Quelltext; Owner kurz bestätigen lassen, dass "beheben" so gemeint ist.
   - Resolution: gezielter filterwarnings-Eintrag, kein `httpx2` ([SUS], neue Abhängigkeit). Umgesetzt in 29-03; 29-02 Teil 9 ratifiziert.

3. **(RESOLVED) Englische und französische Fassung des D-24-04-Satzes**
   - What we know: D-24-04 ist deutsch und wörtlich gesperrt; Store-Texte gibt es in en/de/fr (`php/appinfo/info.xml:36/64/92`).
   - Recommendation: Übersetzungen im Textentwurf vorlegen und wörtlich abnehmen lassen; MT-Übersetzungen WR-02/WR-10 aus Phase 27 bei derselben Lektüre mitlesen (STATE.md Zeile 244).
   - Resolution: wie empfohlen; Vorschlag in 29-02 Teil 1, wörtliche Abnahme im Checkpoint 29-02, Übernahme in 29-12.

4. **(RESOLVED) Gehört `ocr_failed` in die Nachprüfung?**
   - Recommendation: nein (Pattern 7), im Audit begründen.
   - Resolution: nein. 29-09 schließt `ocr_failed` aus der Auswahl aus (Test), 29-14 begründet es im Audit; 29-02 Teil 9 ratifiziert.

5. **(RESOLVED) Pillow-Upstream: Issue oder PR, und wann?**
   - Recommendation: Issue nach dem Release mit selbst erzeugter Repro-Datei, Owner-Freigabe des Texts.
   - Resolution: Issue zuerst, nach dem Release, Text in 29-02 Teil 8 abgenommen, Posten in 29-16 nach erneuter Owner-Freigabe; PR erst nach Rückmeldung.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | alle Python-Gates | ✓ | 0.11.7 | , |
| gh | CI-Belege, Release, Issues | ✓ | 2.92.0 | , |
| Docker | lokale Test-Nextcloud, ggf. PHPUnit | ✓ | 29.5.2 | , |
| php / composer | PHPUnit, `php -l` | ✗ | , | CI-Job `php.yml` (bisheriges Vorgehen "php -l/PHPUnit = CI-Vorbehalt") oder PHP im Docker-Container |
| AWS | , | nicht nötig | , | Phase ist boxlos (D-29-11) |

**Missing dependencies with no fallback:** keine.
**Missing dependencies with fallback:** PHP lokal fehlt; PHP-Änderungen (Reasons, Labels, l10n, Migration, Diagnose) werden über CI `php.yml` belegt, der Workflow ist pfadgetriggert auf `php/`.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein (unverändert) | , |
| V3 Session Management | nein | , |
| V4 Access Control | ja (Nachprüfung, requeue) | `requeue` nur über `ExAppRequired`-Route (`QueueController.php:300ff`), keine neue Route |
| V5 Input Validation | ja | CFB-Leser mit Deckeln und Zyklusschutz; TIFF/JPEG unverändert hinter `MAX_IMAGE_PIXELS` und RLIMIT_AS; Reason-Codes geschlossene Liste in beiden Hälften |
| V6 Cryptography | nein (Signatur nur in CI, unverändert) | `release.yml`, Secrets |
| V7 Error Handling and Logging | ja | Fehlerdetail nur Klassenname (T-02-56), nie Pfad/Message; Logzeilen ohne Ausnahmetext (T-24-19) |
| V12 Files and Resources | ja | Sidecar-Skip vor Download; Größenprüfung; Adressraumdeckel |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Präparierte CFB-Datei mit FAT-Zyklus oder riesiger Sektorzahl | DoS | Besuchte-Sektoren-Menge, Höchstzahl Sektoren, nur Header-DIFAT, Rückfall statt Ausnahme |
| Dekompressionsbombe als JPEG/TIFF | DoS | `Image.MAX_IMAGE_PIXELS = 50_000_000` bleibt, Header-Schätzung, RLIMIT_AS |
| Shim verändert globalen Pillow-Zustand | Tampering | Nur fehlende Schlüssel, nur im Extraktionskind, Test gegen Pillow-Bump |
| Ausnahmetext mit Pfad im Log/Detail | Information Disclosure | Nur `module.qualname` der Klasse speichern |
| Store-Token/Schlüssel in Log oder SUMMARY | Information Disclosure | Nur Secret-Store, Cleanup-Schritt `store-submit.yml`, 400/401-Probe ohne Wertausgabe |
| Push/Merge ohne wörtliches Owner-Wort | Repudiation | Jede Push-/Merge-Aktion einzeln bestätigen lassen (T-28-69) |

## Launch-Härtung: Abdeckung Erfolgskriterium 1 (Ist-Stand der Tests)

| Szenario | Vorhandene Tests (Datei:Testname) | Lücke / Kandidat |
|---|---|---|
| OOM mitten in N Slots | `test_slots_kill.py:212` `test_a_killed_child_mid_pass_is_retried_alone_and_indexed_once`; `test_guard.py:167/175` | Zwei gleichzeitig getötete Kinder im selben Pass, beide solo nachgeholt, nur das schuldige wird `out_of_memory` |
| Kill beider Spuren | `test_slots_kill.py:171` (Hauptprozess mitten im Pass) | Expliziter Test: Kill eines OCR-Slots UND der Embed-Spur im selben Pass, Vektoren und Verdikte vollständig nach Wiederanlauf |
| Hardware-Schrumpfung | `test_precision.py:212` `test_an_active_fp32_stays_on_a_shrunk_box`; `test_profile.py:129` | Neustart auf kleinerer Hardware mit gewähltem Leistung-Profil: Vorschlag/Wirksam-Meldung und Slotzahl fallen, ohne Datenverlust |
| Profilwechsel mitten im Vektor-Reindex | `test_embedding_track.py:1692` `test_the_redelivery_carries_on_in_the_next_process`, `:1775` | Profilwechsel (Economy <-> Standard) während Band-Wiederauslieferung läuft; Cursor läuft zu Ende |
| Modellwechsel mitten im Vektor-Reindex | `test_embedding_track.py:1522/1569` | Zweiter Präzisionswechsel (int8->fp32->int8) bevor das erste Neuschreiben fertig ist: Bestand endet konsistent, Marke stimmt |
| Umgebungsvariable gegen Profil | `test_profile.py` (SOURCE_ENV), `test_info_xml_defaults.py` | `FINDLING_MAX_CELLS` neu in `EXPECTED`; Vollindex-Term mit gesetzter Override-Variable |
| Upgrade 1.3.2 -> 1.4.0 | `test_embedding_track.py:1619` (v1.3-Marke = int8) | CI-Saat D-29-10 (Pattern 10) |

Die Liste ist aus Testnamen erschlossen; ein Härtungsplan sollte jede Zeile durch Lesen des Tests bestätigen, bevor er eine Lücke baut.

## Sources

### Primary (HIGH confidence)
- Lokaler Code: `backend/src/findling/extract/{image,errors,dispatch,office,sandbox}.py`, `worker/{poller,reconcile,embedding}.py`, `nc/{queue,client}.py`, `profile.py`, `config.py`, `probe.py`, `store/{repo.py,schema.sql}`, `api/diagnose.py`; `php/lib/Controller/QueueController.php`, `Service/{FileStateService,AdminViewService,QueueService,ExAppService}.php`, `Db/QueueMapper.php`, `Migration/Version001300Date20260924000000.php`; `backend/appinfo/info.xml`, `php/appinfo/info.xml`; `.github/workflows/{deploy-harp,store-submit,release}.yml`; `scripts/ops/aws_box.sh`; Tests `test_info_xml_defaults.py`, `test_measurement_scripts.py`, `test_store_metadata.py`, `test_lockstep_versions.py`
- Pillow 12.3.0 Quelltext in `backend/.venv` (`TiffImagePlugin.py:151-276, 1460-1610`, `JpegImagePlugin.py:428-466`, `Image.py` open/thumbnail, `ImageOps.py` exif_transpose) und eigene Experimente (Scratchpad `shim.py`, `sf2.py`, `shim2.py`, `draft.py`, `cls.py`)
- Starlette 1.6.0 `testclient.py:32-50`, `exceptions.py:36`
- GitHub Issue street1983nk/nextcloud-search#18, Kommentare 5946430467 bis 5977317984 (per `gh api` gelesen)
- `.planning/debug/embed-handover-lock-timeout.md`, `28-14-SUMMARY.md`, Phase-23-Pläne 23-01 bis 23-09

### Secondary (MEDIUM confidence)
- Pillow main (`raw.githubusercontent.com/python-pillow/Pillow/main/src/PIL/TiffImagePlugin.py`, `src/libImaging/Unpack.c`), PR #9514
- PyPI JSON `httpx2` (Releasedaten, Projekt-URLs), slopcheck-Urteil [SUS]

### Tertiary (LOW confidence)
- MS-CFB-Offsets aus Trainingswissen (A1), AWS describe-tags-Semantik für Key Pairs (A4)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, nichts Neues, Versionen aus der venv gelesen
- Architecture: HIGH für Produktpfade (Datei:Zeile belegt), MEDIUM für K6/Upgrade (aus Code/Workflow gelesen, nicht gefahren)
- Pitfalls: HIGH für Pillow (reproduziert), MEDIUM für CI-Folgen des Tagwechsels

**Research date:** 2026-10-06
**Valid until:** 2026-10-20 (Dependabot bewegt Pins wöchentlich; Pillow-Bump würde den Shim-Abschnitt berühren)
