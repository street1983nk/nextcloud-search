# Phase 31: Neue Formate und Nachholweg - Research

**Researched:** 2026-10-10
**Domain:** Textextraktion (.eml, ZIP, .doc, .xls, HEIC/HEIF), einmaliger Nachholweg nach dem Upgrade, Download-Größenprüfung (F-29-03)
**Confidence:** HIGH für Code-Ist-Stand, Bibliotheken und Lizenzen (alles per Befehl geprüft); MEDIUM für Grenzwerte und RAM-Annahmen (Vorschläge, im Plan zu messen)

## Summary

Die neuen Formate lassen sich ohne LibreOffice und ohne neues Schemafeld bauen: `.eml` mit der Standardbibliothek (`email`, `policy.default`), ZIP mit `zipfile` plus eigener Grenzprüfung vor dem Öffnen, `.doc` mit **olefile 0.47** (BSD-2-Clause) plus eigener Piece-Table-Auswertung nach [MS-DOC], `.xls` mit **xlrd 2.0.2** (BSD) und HEIC/HEIF mit **pillow-heif 1.8.0**. Die Anforderung nennt "pi-heif oder gleichwertig": **pi-heif ist seit pillow-heif 1.5.0 eingestellt, 1.4.0 vom 10.06.2026 ist seine letzte Version** (Upstream-CHANGELOG #431). pillow-heif 1.8.0 (22.09.2026) bringt libheif 1.23.4 und libde265 1.1.3, `py.typed`, cp313-Wheels für `manylinux_2_28_aarch64` und `x86_64`; die Binär-Wheels stehen wegen des mitgelieferten x265 unter GPLv2-or-later (Quelltextkopf von x265 4.2 geprüft), was mit AGPL-3.0 verträglich ist. pyright basic läuft mit allen drei Paketen fehlerfrei (gebündelte typeshed-Stubs für olefile/xlrd, `py.typed` bei pillow-heif), lokal geprüft mit pyright 1.1.414.

Der wichtigste Code-Befund betrifft FMT-06: **echte `.doc`/`.xls`/`.eml`/`.zip`/`.heic`-Dateien stehen in keiner Datenbank.** Die PHP-Crawl-Abfrage filtert per Mimetyp (`StorageService::getFilesInMount` mit `getAllowedMimeIds()`), der Event-Listener ebenso; diese Dateien wurden nie in die Queue gelegt und haben weder in `state.db` noch in `findling_file_state` eine Zeile. `skipped(legacy_format)` tragen nur OLE-Dateien **unter OOXML-Namen** (`.docx`/`.xlsx`/`.pptx`, `cfb.ole_verdict`). Ein Nachholweg nur über `state.db` (wie die 1.4-Nachprüfung) findet die echten Altdateien also nicht. Empfohlen wird ein zweiteiliger, containerseitiger Einmal-Lauf hinter einem neuen Generationssignal: (1) eine 1.5-Nachprüfung der `state.db`-Zeilen (Muster `worker/recheck.py`, neue Marke), (2) ein sofort fälliger Abgleich-Zyklus des bestehenden ETag-Abgleichs (`worker/reconcile.py`), der dank erweiterter PHP-Allowlist die nie gesehenen Dateien als unbekannt erkennt und in Bändern zu 256 neu einreiht, ohne bestehende Treffer anzufassen und ohne Datei-Download des Restbestands.

POL-02 (F-29-03) hat eine eindeutige Ursache: `_stream_file` wirft `ShortRead`, sobald weniger Bytes kommen als die Queue (Dateicache-Größe) nennt; zweimal kurz heißt "Zeile ohne Urteil zurück", bis die PHP-Aufgaberegel `failed(repeatedly_stuck)` schreibt. Sauberer Fix: zwei kurze Antworten mit **gleicher Bytezahl und gleichem Inhalts-Hash** sind die echte Datei, der Cache ist veraltet; dann wird normal extrahiert. Das ändert D-29-04 nur für genau diesen Fall (der ursprüngliche Schutz gegen zufällige Abbrüche bleibt).

**Primary recommendation:** Ein gemeinsamer "Format-Generation 3"-Schritt: Allowlists beidseitig erweitern, ein neuer Skip-Code `archive_limit`, VERDICTS_GENERATION 2 auf 3, danach containerseitig Nachprüfung plus erzwungener Abgleich-Zyklus unter einer Marke `recheck_1_5_0`; Extraktoren als eigene Module im Sandbox-Kind, ZIP ohne OCR und mit Grenzprüfung vor `ZipFile()`.

<user_constraints>
## User Constraints (aus 30-CONTEXT.md, Owner-Tor für den ganzen Milestone v1.5)

Für Phase 31 existiert keine eigene CONTEXT.md. Bindend sind die Milestone-Entscheide aus `.planning/phases/30-owner-tor-schema-und-tschechisch/30-CONTEXT.md`, wörtlich:

### Locked Decisions
- **D-30-03 ZIP-Treffer (FMT-02, Phase 31):** EIN Treffer je Archiv. Das Archiv ist ein Dokument, Text aller inneren Dateien zusammen; das Snippet nennt die innere Datei. KEIN neues Schemafeld noetig.
- **D-30-04 Nachholweg (FMT-06, Phase 31):** Alle neu lesbaren Typen werden nach dem Upgrade nachgeholt: bisher als `legacy_format` uebersprungene .doc/.xls plus alle .eml/.zip/.heic, in Baendern wie die 1.4-Altbestands-Nachpruefung, ohne bestehende Treffer anzufassen.
- **D-30-07 Upgrade-Beweis:** Beide Richtungen in deploy-harp (de,en -> de,cs Umbau und zurueck), wie in v1.3; UPGRADE_FROM_TAG auf v1.4.2 umziehen, Schritte 2b/3c/5 entsprechend anpassen.
- **D-30-08 Schema-Einmaligkeit:** Phase 30 ist der einzige Schemaschritt (SCHEMA_VERSION 2 -> 3, LEGACY_SCHEMA_STEPS ("2","3"),("1","3")). Der Plan muss als Pruefzeile festhalten, dass der Ordnerfilter (Phase 32) ueber die `path`-Spalte in state.db ohne Schemafeld auskommt (Annahme A5).
- Aus "Folge fuer Phase 30": Da D-30-03 kein Schemafeld braucht, ist die einzige Schema-/Markenaenderung des Milestones das tschechische Koerperfeld (CZ-02).
- Aus ROADMAP (Reihenfolge-Logik): "Die Formate (Phase 31) bauen auf diesem eingefrorenen Schema auf und bringen nur den Nachholweg fuer bisher uebersprungene Dateien mit."
- Aus 30-AUDIT.md, L-30-03 (accept): "Vektordigest ungeprüft in GITHUB_ENV ... wird mitgenommen, sobald Phase 31 die Strecke ohnehin anfasst (Andockblock FMT-06)."

### Claude's Discretion
- Owner-Linie aus 30-CONTEXT.md: "Nachentscheide nach Research (10.10.2026, Claude nach Empfehlung, Owner-Linie 'Rueckfragen minimal', Veto jederzeit)". Konkrete Grenzwerte (ZIP-Tiefe, Anzahl, Rate), Wahl der HEIC-Bibliothek innerhalb von "pi-heif oder gleichwertig", Codewahl für Skip-Urteile und Testkorpus liegen damit bei Claude, mit Veto-Recht des Owners.

### Deferred Ideas (OUT OF SCOPE)
- `.msg` (extract-msg GPL-3, laut v1.5-Recherche "spaeter").
- `.ppt` (Legacy-PowerPoint) ist in FMT-01..05 nicht genannt und bleibt `legacy_format`.
- Weitere Archivformate (7z, rar, tar, gz): nicht Teil von FMT-02.
- Der große bösartige Formatkorpus der Launch-Härtung gehört zu Phase 36; Phase 31 liefert die gezielten Regressionstests je Format.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FMT-01 | `.eml`: Betreff, Absender, Empfänger, Textteil; HTML-Teil als Text | stdlib `email` + `policy.default` dekodiert RFC-2047-Kopfzeilen und Transfer-Encodings (lokal geprüft); `get_body(("plain","html"))`; HTML über die gehärtete lxml-Strecke aus `extract/text.py`. Muster 2, Pitfalls 4 bis 6 |
| FMT-02 | ZIP-Inhalte, Treffer zeigt Archiv + innere Datei; Grenzen Tiefe, Gesamtgröße, Anzahl, Rate; Skip-Urteil statt Absturz | `zipfile` 3.13 (Overlap-Schutz CVE-2024-0450, Größe pro Eintrag beim Lesen begrenzt); EOCD-Vorprüfung der Eintragszahl (gemessen: 100 000 Einträge = 55,7 MiB Spitze); Mitgliedsmarke im Text plus Snippet-Nachbearbeitung ohne Schemafeld. Muster 3 und 4 |
| FMT-03 | `.doc` ohne LibreOffice, nicht lesbare Varianten mit benanntem Urteil | olefile 0.47 + Piece Table nach [MS-DOC] 2.4.1 (FibBase, Clx, FcCompressed verifiziert); `fEncrypted` -> `encrypted`, `nFib` < 0x00C1 -> benanntes Urteil. Muster 5 |
| FMT-04 | `.xls` mit xlrd, gleiche Zellgrenze wie XLSX | xlrd 2.0.2, `on_demand`, `ragged_rows=True`, `formatting_info=False`, Zählung gegen `settings().max_cells`, `too_many_cells`; Verschlüsselung über `XLRDError("Workbook is encrypted")`. Muster 6 |
| FMT-05 | HEIC/HEIF per OCR, arm64-tauglich | pillow-heif 1.8.0 (pi-heif eingestellt); Pillow-Plugin in den bestehenden Bildpfad (`extract/image.py`), `Image.MAX_IMAGE_PIXELS` greift (lokal geprüft). Muster 7 |
| FMT-06 | Bestand holt bisher übersprungene Dateien nach dem Upgrade selbst nach, Upgrade-CI-Beweis | Befund: neue Typen haben keine DB-Zeile; Nachprüfung `state.db` plus erzwungener Abgleich-Zyklus hinter VERDICTS_GENERATION 3. Muster 8, Andockblock deploy-harp Zeile 3641 |
| POL-02 | Veraltete Cache-Größe endet nicht mehr als `repeatedly_stuck` (F-29-03) | Ursache in `nc/client.py:_stream_file` und `worker/poller.py:_fetch_file` belegt; Fix "zweimal gleich kurz und gleicher Hash = echte Datei". Muster 9 |
</phase_requirements>

## Project Constraints (aus CLAUDE.md und Owner-Regeln)

- Python 3.13 + uv, alle Abhängigkeiten exakt gepinnt in `backend/pyproject.toml` und `uv.lock`.
- Qualitätsgates lokal grün vor jedem Commit: ruff-Vollregelsatz, `ruff format --check`, pyright basic (lokal mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`), vulture, pytest mit Coverage-Boden 90 %.
- Code und Bezeichner Englisch, ASCII; deutsche Prosa mit echten Umlauten; keine Gedankenstriche (U+2014, U+2013); keine Emojis.
- Lizenz AGPL-3.0: jede neue Abhängigkeit muss verträglich sein und in `THIRD-PARTY.md` (und bei mitgelieferten Fremddateien in `REUSE.toml`) stehen.
- Security/Privacy: keine Inhalte, Pfade oder Dateinamen in Logs (T-02-56); Berechtigungs-Durchgriff unverändert (PHP-Endprüfung); kein Netzwerkzugriff aus dem Container außer den bekannten Zielen.
- Hardware-Ziel 4 bis 8 GB RAM, arm64 gleichwertig; Extraktion im Sandbox-Kind mit `RLIMIT_AS` 512 MiB und 120 s Frist (`config.py:260,265`).
- Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Abschluss fixen.
- Kurze Produkttexte; Store-Text-Entwurf vor Release dem Owner zeigen (REL-05, Phase 36).
- Commits nur als `street1983nk <k.cherif@outlook.de>`, keine Claude-Trailer.
- Jeder Minor-Schritt braucht eine PHP-Migration, die `backend_app_version` verwirft (Klassenkommentar `Version001400Date20261006000000`).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Allowlist der Mimetypen (Crawl, Listener, Diagnose) | PHP-Companion (`StorageService::ALLOWED_MIMETYPES`) | Container (`dispatch.ALLOWED_MIMETYPES`) | Zwei Listen mit Paritätstest `test_allowlist_parity.py`; beide Seiten müssen halten |
| Format-Extraktion (.eml, ZIP, .doc, .xls, HEIC) | Container, Sandbox-Kind (`findling/extract/`) | ; | Fremde Bytes nur im Kind mit `RLIMIT_AS` und Frist |
| Skip-/Fehlerurteile, geschlossene Liste | Container (`extract/errors.py`, `store/repo.py`) | PHP (`FileStateService`, `AdminViewService`, l10n) | Drei Listen, Driftgegenprobe in `test_extract_errors.py` |
| Nachholweg nach Upgrade | Container (`worker/recheck.py`, `worker/reconcile.py`) | PHP liefert Dateiliste und Queue | Nur der Container kennt Generationssignal und Marken; Queue lebt in Nextcloud |
| Snippet mit innerer Datei | Container (`index/search.py:snippets_for`) | PHP zeigt Subline als Text | Kein Schemafeld (D-30-03); Text liegt gespeichert in `body_de` |
| Größenprüfung beim Download (POL-02) | Container (`nc/client.py`, `worker/poller.py`) | PHP-Gateway liefert Bytes | Die Abweichung ist erst nach dem Lesen sichtbar |
| Abdeckungszahl (Nenner) | PHP (`StorageCrawlJob` Zählmodus, `ScanRecountJob`) | ; | Nenner zählt nur Allowlist-Typen; nach Erweiterung neu zählen |
| Upgrade-Beweis | CI `deploy-harp.yml` (Store upgrade 2b, 3c, 5) | ; | Andockblock bei Zeile 3641 vorbereitet |

## Ist-Stand im Code (Belege)

| Befund | Ort | Folge für Phase 31 |
|---|---|---|
| Container-Allowlist: 14 Typen + 4 Bildtypen, HEIC ausdrücklich draußen | `extract/dispatch.py:88-119` | `message/rfc822`, `application/zip`, `application/msword`, `application/vnd.ms-excel`, `image/heic`, `image/heif` ergänzen; Docstrings mit Begründung "HEIC stays out" anpassen |
| PHP-Allowlist identisch, gleicher HEIC-Absatz | `php/lib/Service/StorageService.php:80-130` | Spiegelbildlich; Paritätstest liest die PHP-Konstante |
| PHP `OCR_CERTAIN_MIMETYPES` (Abdeckungs-Intervall) | `php/lib/BackgroundJobs/StorageCrawlJob.php:122-128` | `image/heic`, `image/heif` ergänzen |
| Crawl, Listener und Abgleich-Seite filtern per Mimetyp in der Abfrage | `StorageService::getFilesInMount` (`getAllowedMimeIds()`), `FileEventListener.php:381`, `ShareEventListener.php:170` | Neue Typen haben **keine** Zeile in `state.db`/`findling_file_state` |
| `legacy_format` nur für OLE unter OOXML-Endung | `extract/cfb.py:86-106`, `dispatch._run_ooxml_route` | 1.5 kann diese Dateien lesen: `WordDocument` -> .doc-Extraktor, `Workbook`/`Book` -> xlrd, `PowerPoint Document` bleibt `legacy_format` |
| 1.4-Nachprüfung: Bänder zu `REQUEUE_BAND`, Cursor in Meta-Schlüssel, Start nur bei VERDICTS_GENERATION | `worker/recheck.py`, `poller.py:930`, `store/repo.py:185` (`RECHECK_MARK = "recheck_1_4_0"`) | Vorlage für `recheck_1_5_0` |
| Abgleich: unbekannte Datei = Arbeit, bekannte Datei mit gleichem ETag = nichts | `worker/reconcile.py:431-520` | Nimmt neue Typen automatisch auf, aber nur alle 24 h um 2 Uhr (`RECONCILE_MIN_INTERVAL_HOURS = 24`, `RECONCILE_HOUR = 2`, `config.py:579-583`) |
| Abgleich "sofort fällig" nur bei unterbrochenem Lauf oder ohne letzten Abschluss | `reconcile.py:_is_due` (Zeile 633ff) | Erzwungener Zyklus braucht eine eigene Fälligkeitsregel |
| Ein Vollcrawl lädt jede Datei erneut herunter (Hash-Vergleich nach Download) | `poller.py:1503-1519` (`_fetch_file`, dann `is_unchanged`) | Neu-Crawl als Nachholweg wäre faktisch ein Vollreindex der Bytes: **nicht** verwenden |
| `ShortRead` bei weniger Bytes als `expected` | `nc/client.py:233-287` | Ursache F-29-03 |
| Zweimal kurz: Zeile ohne Urteil zurück, bis `repeatedly_stuck` | `poller.py:1502-1511`, `poller.py:1966-1978` | Fix-Ort POL-02 |
| XLSX-Zellgrenze `MAX_CELLS = 200_000`, Urteil `too_many_cells` | `config.py:278`, `extract/office.py:138-183` | Gleiche Grenze und gleiches Urteil für .xls |
| ZIP-Bombenprüfung für OOXML/ODF über deklarierte Größen | `extract/office.py:52-81`, `config.py:362,382` (64 MiB je Mitglied, 256 MiB gesamt) | Wiederverwendbar für FMT-02 |
| Bildpfad: `Image.MAX_IMAGE_PIXELS = 50_000_000`, Draft, Adressraum-Schätzung, EXIF-Drehung | `extract/image.py:56-66, 284-330, 569` | HEIC hängt sich hier ein |
| Snippet aus gespeichertem `body_de`, Fragment per `SnippetGenerator`, Highlights als Zeichenbereiche | `index/search.py:831-893` | Ort der "innere Datei"-Nachbearbeitung |
| Typfilter-Gruppen | `query/rewrite.py:190-215`; `eml` steht schon in `text` | `doc`/`dot` zu `documents`, `xls`/`xlt` zu `spreadsheets`, `heic`/`heif` zu `images`; `zip` in keiner Gruppe (siehe offene Fragen) |
| Neue Urteilscodes brauchen Fähigkeitssignal der Companion | `nc/queue.py:124-180` (`VERDICTS_GENERATION = 2`, Fallback-Tabellen) | Neuer Code -> Generation 3 plus Fallback |
| Urteilslabels in 8 Sprachen x 2 Dateien + 5 l10n-Dokus | `php/l10n/*.js|json`, `docs/l10n-*.md`, `AdminViewService.php:440-520` | Jeder neue oder geänderte englische Satz kostet 16 Dateien plus Doku |
| THIRD-PARTY.md driftet bereits | `THIRD-PARTY.md:158-168` nennt pypdf 6.16.1, charset-normalizer 3.5.1, lxml 6.1.1, striprtf 0.0.32; gepinnt sind 6.19.0, 3.5.2, 6.1.3, 0.0.33 | Beim Ergänzen der drei neuen Pakete mitkorrigieren |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `email` (stdlib) | Python 3.13 | .eml parsen, RFC-2047/2231 dekodieren | `policy.default` liefert `EmailMessage` mit `get_body()` und dekodierten Kopfzeilen [VERIFIED: lokale Probe CPython 3.13.13] |
| `zipfile` (stdlib) | Python 3.13 | ZIP lesen | Overlap-Erkennung (`BadZipFile("Overlapped entries")`, CVE-2024-0450), `_left = file_size` begrenzt jedes Mitglied auf die deklarierte Größe, `metadata_encoding` [VERIFIED: Quelltext der lokalen 3.13.13] |
| `olefile` | 0.47 (01.12.2023) | OLE2/CFB-Streams lesen für .doc | BSD-2-Clause, rein Python, Schleifen mit fester Länge gegen FAT-Zyklen, 28 Mio. Downloads/Monat [VERIFIED: PyPI-JSON, Wheel-Lizenztext, pypistats 10.10.2026] |
| `xlrd` | 2.0.2 (14.06.2025) | .xls (BIFF2 bis BIFF8) | BSD-3-Clause (plus BSD-Hinweis), liest seit 2.0 nur noch .xls, 67 Mio. Downloads/Monat, Repo aktiv (Push 15.07.2026) [VERIFIED: PyPI-JSON, Wheel-LICENSE, GitHub-API] |
| `pillow-heif` | 1.8.0 (22.09.2026) | HEIC/HEIF als Pillow-Plugin | Quelltext BSD-3-Clause, Wheels GPLv2-or-later wegen x265; libheif 1.23.4 (LGPLv3), libde265 1.1.3 (LGPLv3); cp313 `manylinux_2_26/2_28_aarch64` und `manylinux_2_27/2_28_x86_64`; `py.typed` seit 1.7.0 [VERIFIED: PyPI-JSON, Wheel-Inhalt, LICENSES_bundled.txt, CHANGELOG, x265-Quelltextkopf] |

### Supporting (bereits im Stack)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `lxml` | 6.1.3 | HTML-Teil der Mail zu Text | Gleiche gehärtete Parser wie `extract/text.py` |
| `charset-normalizer` | 3.5.2 | Fallback, wenn ein Mail-Teil einen unbekannten Zeichensatz meldet | `get_content()` wirft dann `LookupError` (lokal geprüft) |
| `pillow` | 12.3.0 | Bildpfad, Plugin-Host für HEIF | pillow-heif verlangt `pillow>=11.1.0` [VERIFIED: PyPI requires_dist] |
| `pypdfium2`, `python-docx`, `python-pptx`, `openpyxl`, `striprtf` | wie gepinnt | Extraktion innerer ZIP-Dateien | Über die vorhandenen Routen, ohne OCR |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pillow-heif 1.8.0 | pi-heif 1.4.0 | **Abgelehnt:** eingestellt, letzte Version 10.06.2026 mit libheif 1.23.0 und libde265 1.1.0; die Fixes aus 1.6 bis 1.8 (Use-after-free #453, Segfault bei ungültigem UTF-8 #478) bekommt es nie [VERIFIED: CHANGELOG pillow_heif] |
| pillow-heif-Wheel | Debian `libheif1` + `libheif-plugin-libde265` und pillow-heif aus dem sdist gebaut | Spart 11 MiB x265 im Image und bringt Debian-Sicherheitsupdates, kostet aber Build-Werkzeugkette in der Build-Stufe und einen eigenen Versionsabgleich; für v1.5 nicht empfohlen [ASSUMED] |
| olefile + eigener Piece-Table-Leser | `cfb.py` zu einem Stream-Leser ausbauen | cfb.py liest nur das Verzeichnis, kennt weder MiniFAT noch DIFAT jenseits von 109 Einträgen; ein zweiter vollständiger CFB-Leser wäre Handarbeit an genau der Stelle, an der olefile 20 Jahre Härtung hat |
| eigener .doc-Leser | antiword, catdoc, wvWare, LibreOffice | Vom Auftrag ausgeschlossen (antiword) bzw. zusätzliche Binärpakete/Prozesse; catdoc/wv GPL-Systempakete |
| xlrd | eigener BIFF-Leser | Kein Grund: xlrd ist der Standard, rein Python |
| Abgleich-Zyklus als Nachholweg | PHP-Crawl im Mimetyp-Filtermodus (neuer `StorageCrawlJob`-Modus aus einer Migration) | Schneller (nur neue Typen), aber startet unabhängig davon, ob der Container schon 1.5 ist; ein 1.4.2-Container würde die eingereihten Dateien als `mime_not_allowed` gegen ihren ETag speichern und sie dann nie wieder anfassen |

**Installation:**
```bash
cd backend
uv add olefile==0.47 xlrd==2.0.2 pillow-heif==1.8.0
```

**Version verification (10.10.2026, PyPI-JSON):** olefile 0.47 Upload 2023-12-01; xlrd 2.0.2 Upload 2025-06-14; pillow-heif 1.8.0 Upload 2026-09-22 (Upstream-CHANGELOG führt 1.9.0 in Arbeit mit libheif 1.23.5, #491; bei Erscheinen vor dem Bau neu bewerten).

## Package Legitimacy Audit

slopcheck 0.6.1 (`slopcheck scan requirements.txt`) am 10.10.2026: alle vier geprüften Namen `[OK]`.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| olefile | PyPI | Releases seit 2017 sichtbar, 0.47 von 12/2023 | 27,95 Mio./Monat | github.com/decalage2/olefile (nicht archiviert) | [OK] | Approved |
| xlrd | PyPI | 1.0.0 von 2016, 2.0.2 von 06/2025 | 67,05 Mio./Monat | github.com/python-excel/xlrd (Push 15.07.2026) | [OK] | Approved |
| pillow-heif | PyPI | 1.3.0 bis 1.8.0 im Jahr 2026, Trusted Publishing seit 1.5.0 | 18,61 Mio./Monat | github.com/bigcat88/pillow_heif (Push 10.10.2026) | [OK] | Approved |
| pi-heif | PyPI | 1.4.0 von 06/2026, eingestellt | ; | gleiche Quelle | [OK] | Nicht verwenden (eingestellt) |

**Packages removed due to slopcheck [SLOP] verdict:** keine
**Packages flagged as suspicious [SUS]:** keine
Python-Wheels führen bei der Installation keinen Code aus (keine `setup.py`), ein Postinstall-Risiko wie bei npm entfällt.

## Architecture Patterns

### System Architecture Diagram

```
Nextcloud filecache ──(Crawl/Listener/Abgleich, Mimetyp-Filter = PHP-Allowlist + 6 neue Typen)──> Queue (oc_findling_queue)
                                                                                              │ claim
                                                                                              v
Container-Poller ── download über Gateway ──> Scratch-Datei ──┬─ Bytes == erwartet ODER (2x gleich kurz, gleicher Hash) ─> Sandbox-Kind
      │                                                        └─ 2x ungleich kurz ─> Zeile zurück (wie bisher)
      │                                                                                 │ judge(mime, size)
      │                                                                                 v
      │                                     ┌── message/rfc822 ─> mail.extract_eml ──> Kopfzeilen + Text/HTML-Teil (+ Anhangnamen)
      │                                     ├── application/zip ─> archive.extract_zip ─ EOCD-Vorprüfung ─> Grenzen ─> je Mitglied: Route nach Endung (ohne OCR)
      │                                     │                                                                     └─ Überschreitung ─> skipped(archive_limit)
      │                                     ├── application/msword ─> Sniff: OLE ─> legacy_doc.extract_doc | {\rtf ─> RTF | PK ─> DOCX | sonst unsupported_variant
      │                                     ├── application/vnd.ms-excel ─> Sniff: OLE ─> legacy_xls.extract_xls | PK ─> XLSX | sonst unsupported_variant
      │                                     ├── image/heic, image/heif ─> image.extract_image (Pillow + pillow-heif) ─> Tesseract
      │                                     └── OOXML-Name mit OLE: WordDocument ─> .doc, Workbook/Book ─> .xls, PowerPoint ─> legacy_format
      │                                                                                 v
      │                                                       ExtractionOutcome ─> Index (body_* Felder, kein neues Feld) + state.db + Quittung an PHP
      │
      └── Einmal-Nachholweg (nur wenn Companion VERDICTS_GENERATION 3 meldet):
            Teil A: state.db-Durchlauf (legacy_format, Zeilen mit neuem Mimetyp) ─> requeue in Bändern ─> Marke recheck_1_5_0
            Teil B: erzwungener Abgleich-Zyklus ─> Dateiliste je Mount (PHP, jetzt mit neuen Typen) ─> unbekannt = requeue in Bändern ─> Marke done

Suche: /snippets ─> SnippetGenerator(body_de) ─> Fragment ─> Position im gespeicherten Text ─> letzte Mitgliedsmarke davor ─> "innere/datei.pdf: Fragment" (Highlights verschoben)
```

### Recommended Project Structure

```
backend/src/findling/extract/
├── mail.py          # .eml: Kopfzeilen, Body, Anhangnamen, Teil-/Tiefengrenze
├── archive.py       # ZIP: EOCD-Vorprüfung, Grenzen, Mitgliedsschleife, Mitgliedsmarken
├── legacy_doc.py    # .doc: olefile + FIB + Clx/PlcPcd + FcCompressed
├── legacy_xls.py    # .xls: xlrd mit Zellgrenze
├── image.py         # + pillow-heif-Registrierung (bestehend)
├── text.py          # + html_to_text(str) für die Mail (Refactor ohne Verhaltensänderung)
└── dispatch.py      # Allowlist, Routen MAIL/ZIP/DOC/XLS, Endungstabelle für ZIP-Mitglieder
backend/src/findling/worker/
├── recheck.py       # + 1.5-Auswahl und Marke, oder Schwestermodul catchup.py
└── reconcile.py     # + "einmal sofort fällig" für den Nachholweg
backend/src/findling/index/search.py   # Mitgliedsname vor dem Fragment
backend/src/findling/nc/client.py, worker/poller.py  # POL-02
php/lib/Service/StorageService.php, BackgroundJobs/StorageCrawlJob.php, Controller/ProfileController.php (VERDICTS_GENERATION 3),
php/lib/Service/FileStateService.php (Code archive_limit), AdminViewService.php (Label), php/l10n/* (16 Dateien),
php/lib/Migration/Version001500Date2026MMDD000000.php (backend_app_version verwerfen, Nenner neu zählen lassen)
```

### Muster 1: Eine Format-Generation, ein Signal

**What:** Alle neuen Routen und der neue Code `archive_limit` reisen unter VERDICTS_GENERATION 3. Der Container behandelt 2 und 3 als bekannt (Fallback-Tabellen je Generation), der Nachholweg startet nur bei 3.
**When to use:** Immer, wenn Container und Companion nicht im selben Moment aktualisiert werden (AppAPI-Update und App-Update laufen getrennt).
**Warum:** `_verdicts()` akzeptiert heute **nur exakt** `VERDICTS_GENERATION` (`queue.py:172-180`). Wird die Konstante auf 3 gehoben, behandelt ein 1.5-Container eine 1.4.2-Companion (meldet 2) wie eine ohne Signal und würde auch `system_file`/`legacy_format`/`unsupported_variant` auf die 1.3-Fallbacks abbilden. Die Funktion muss eine Menge bekannter Generationen kennen und die Fallback-Abbildung je Code nach Generation wählen.

### Muster 2: .eml (FMT-01)

**What:** `BytesParser(policy=policy.default).parse(handle)`; Kopfzeilen `Subject`, `From`, `To`, `Cc` über `str(msg[name])` (dekodiert, lokal geprüft: `=?utf-8?q?J=C3=BCrgen?=` -> "Jürgen", ISO-8859-1-Kodierung ebenso); Text über `msg.get_body(preferencelist=("plain", "html"))`, bei HTML über die gehärtete lxml-Strecke; Anhangnamen über `part.get_filename()` beim Durchlauf von `msg.iter_attachments()`.
**Scope-Empfehlung Anhänge:** In 1.5 **nur die Namen** der Anhänge indexieren, nicht deren Inhalt. FMT-01 verlangt Kopfzeilen und Textteil; Anhanginhalte wären eine zweite Archivlogik mit eigenen Grenzen (Zeitbudget, Tiefe bei weitergeleiteten `message/rfc822`-Teilen). Die ZIP-Mitgliedsschleife (Muster 3) könnte später wiederverwendet werden.
**Grenzen:** Dateigröße wie bisher (50 MiB, `MAX_FILE_BYTES`); MIME-Teile zählen und bei mehr als z. B. 1 000 Teilen oder Tiefe über 50 abbrechen. Lokal gemessen: 500 verschachtelte `multipart`-Ebenen parsen in 0,18 s, 2 000 Ebenen enden in `RecursionError` [VERIFIED: lokale Probe]. `RecursionError` ist ein `RuntimeError` und würde ohne eigene Behandlung zu `failed(corrupt)`; das ist vertretbar, besser ist eine Tiefenprüfung über die Rohzeilen vor dem Parsen oder ein Abfangen mit benanntem Urteil.

### Muster 3: ZIP mit Grenzprüfung vor dem Öffnen (FMT-02)

**What:** Drei Stufen, jede bricht mit `skipped(archive_limit)` ab:
1. **EOCD-Vorprüfung** (eigene 40 Zeilen mit `struct`): End-of-Central-Directory (und ZIP64-EOCD) aus den letzten 65 557 Bytes lesen, Gesamtzahl der Einträge und Größe des Zentralverzeichnisses prüfen, **bevor** `ZipFile()` alle `ZipInfo`-Objekte baut. Gemessen: ein 9,8-MB-Archiv mit 100 000 leeren Einträgen kostet beim Öffnen 55,7 MiB Spitze und 3,2 s [VERIFIED: lokale Messung, tracemalloc]; ein 50-MB-Archiv wäre damit rund das Fünffache, nahe an `RLIMIT_AS`.
2. **Deklarationsprüfung** über `infolist()`: Summe `file_size` gegen `EXTRACT_ARCHIVE_TOTAL_MAX_BYTES` (256 MiB), Rate `file_size / max(compress_size, 1)` je Mitglied, Verschachtelungstiefe.
3. **Lesen mit Zählung:** Mitglieder in eine Datei neben der Scratch-Datei streamen (Name aus laufender Nummer, nie aus dem Archivpfad), Bytes mitzählen, nach der Extraktion löschen.

**Vorgeschlagene Grenzen (Claude's Discretion, Veto möglich):**

| Grenze | Vorschlag | Begründung |
|---|---|---|
| Einträge im Zentralverzeichnis | 10 000 | Weit über normalen Projektarchiven, unter der gemessenen RAM-Schwelle |
| Entpackte Gesamtgröße (deklariert) | 256 MiB (= vorhandene Konstante) | Halbes `RLIMIT_AS`, fünffache Dateigröße; gleiche Begründung wie `config.py:369-381` |
| Einzelmitglied | über `max_file_bytes` (50 MiB) wird das Mitglied übergangen, das Archiv läuft weiter | Gleiches Maß wie für Einzeldateien |
| Kompressionsrate | Mitglied über 1 MiB mit Rate über 100:1 = Bombe | Deflate erreicht höchstens etwa 1032:1 [ASSUMED]; Textdateien liegen typisch weit darunter |
| Verschachtelung | Tiefe 2 (ein inneres ZIP wird gelesen); tieferes ZIP = ganzes Archiv `archive_limit` | Erfüllt "Tiefe über Grenze = sichtbares Skip-Urteil"; Quine-Archive enden hier |
| Gelesene Mitglieder mit Text | 1 000, danach Abbruch mit `indexed(truncated)` | Zeitbudget 120 s gilt für das ganze Archiv |
| Zeitbudget | Mitgliedsschleife stoppt bei 75 % von `extract_timeout_seconds`, Ergebnis `indexed(truncated)` | Sonst verliert ein großes Archiv durch den Kill alles |

**Innere Typen:** Zuordnung über die Endung (es gibt keinen Nextcloud-Mimetyp im Archiv): pdf (nur Textschicht, ohne OCR), docx, pptx, xlsx, odt/ods/odp, html/htm/xhtml, rtf, txt/md/csv, eml, doc, xls, zip (Tiefe). **Bilder und gescannte PDFs ohne OCR**: eine Tesseract-Seite kostet 300 bis 600 MB und mehrere Sekunden (CLAUDE.md, RAM-Budget), das sprengt das 120-s-Budget des ganzen Archivs. OOXML/ODF-Mitglieder zählen nicht als Verschachtelung, ihre eigenen Bombenprüfungen (`office._too_large_to_read`) greifen pro Mitglied.
**Verschlüsselte Mitglieder:** `ZipInfo.flag_bits & 0x1` vorher prüfen und überspringen (sonst `RuntimeError` mit Mitgliedsnamen in der Meldung, lokal geprüft). AES (Methode 99) und Deflate64 (9) werfen `NotImplementedError("That compression method is not supported")`: überspringen. Sind alle Mitglieder verschlüsselt: `skipped(encrypted)`.
**Pfadnamen-Kodierung:** `zipfile` dekodiert ohne UTF-8-Flag (Bit 11) als cp437. Deutsche Windows-Archive ohne Flag sind meist cp850; ä, ö, ü, Ä, Ö, Ü, ß liegen in cp437 und cp850 auf denselben Codepunkten (0x84, 0x94, 0x81, 0x8E, 0x99, 0x9A, 0xE1) [ASSUMED: Codepage-Tabellen, im Test gegenprüfen]. Kein eigenes Raten nötig; Steuerzeichen und Bidi-Zeichen (U+202A bis U+202E, U+2066 bis U+2069) aus dem Anzeigenamen entfernen, Länge kappen.
**Pfad-Traversal:** Es wird nie unter dem Archivpfad geschrieben, nur unter einer laufenden Nummer im Scratch-Verzeichnis. Der Name ist reiner Anzeigetext.

### Muster 4: "Snippet nennt die innere Datei" ohne Schemafeld (D-30-03)

**What:** Der Archivtext besteht aus Abschnitten `"\x1c" + anzeigename + "\n" + mitgliedstext + "\n\n"`. U+001C (File Separator) wird aus allen Mitgliedstexten entfernt, damit nur die Marken ihn tragen. In `snippets_for` (und für den Vektorpfad in `_passage_of`) nach dem Fragment: Position des Fragments im gespeicherten `body_de` suchen (`str.find`), mit `rfind("\x1c", 0, pos)` die letzte Marke davor bestimmen, Namen bis zum Zeilenende lesen, Ausgabe `f"{name}: {fragment}"`, Highlight-Bereiche um `len(name) + 2` verschieben, U+001C aus dem angezeigten Fragment entfernen.
**Warum so:** `body_de` ist gespeichert (`index/schema.py:169`, `stored=True`); tantivys Fragment ist ein Ausschnitt des gespeicherten Textes. Der Tokenizer verwirft das Steuerzeichen, der Name selbst wird mitindexiert: eine Suche nach "rechnung.pdf" findet das Archiv. Kein Feld, keine Marke, kein Umbau (D-30-08 bleibt wahr).
**Grenze:** Steht das Fragment vor der ersten Marke (kann nicht vorkommen, der Text beginnt mit einer Marke) oder taucht es mehrfach auf, gilt die erste Fundstelle; schlimmstenfalls nennt die Subline ein Nachbarmitglied mit gleichem Wortlaut.

### Muster 5: .doc über Piece Table (FMT-03)

**What:** Nach [MS-DOC] 2.4.1 "Retrieving Text" [CITED: learn.microsoft.com/en-us/openspecs/office_file_formats/ms-doc/01d5d8c4-cf9c-4ef9-80fd-439e763cfe01]:
1. `olefile.OleFileIO(path, raise_defects=olefile.DEFECT_INCORRECT)`; ohne Stream `WordDocument` -> `unsupported_variant`.
2. FibBase aus den ersten 32 Bytes: `wIdent` muss 0xA5EC sein, `nFib` (SHOULD 0x00C1), Bits `fEncrypted`, `fWhichTblStm`, `fObfuscated` [CITED: learn.microsoft.com/.../ms-doc/26fb6c06-4e5c-4778-ab4e-edbf26a545bb]. `fEncrypted` -> `skipped(encrypted)`; `nFib` unter 0x00C1 (Word 6/95 und älter) -> `skipped(unsupported_variant)`.
3. Table-Stream `1Table` oder `0Table` nach `fWhichTblStm`; fehlt er -> `failed(corrupt)`.
4. `fcClx`/`lcbClx` aus FibRgFcLcb97 (abgeleitet: Fib-Offset 0x01A2/0x01A6; FibBase 32 + csw 2 + fibRgW 28 + cslw 2 + fibRgLw 88 + cbRgFcLcb 2 = 154, fcClx ist Paar 33 -> 154 + 33 x 8 = 418) [ASSUMED: gegen Seite FibRgFcLcb97 prüfen, wie bei cfb.py].
5. Clx: Folge von Prc (erstes Byte 0x01, `cbGrpprl` 2 Bytes, überspringen) bis zum Pcdt (Byte 0x02, `lcb` 4 Bytes) [CITED: .../ms-doc/bad26767-b575-44d3-9da3-96378d56ce14]. PlcPcd: n = (lcb - 4) / 12 Stücke, `aCp` (n+1) x 4 Bytes, `aPcd` n x 8 Bytes (fc an Offset 2 im Pcd).
6. FcCompressed: Bit 30 = `fCompressed`. 0: UTF-16LE ab `fc`, 2 Bytes je Zeichen. 1: 8-Bit ab `fc/2`, **Latin-1 mit genau der Sondertabelle 0x82..0x9F aus der Spezifikation** [CITED: .../ms-doc/aa2e55a2-f4f2-4795-bab5-6d9d7a0ed249]. Achtung: das ist **nicht cp1252**, denn 0x80 (€), 0x8E (Ž) und 0x9E (ž) fehlen in der Tabelle.
7. Nachbearbeitung: 0x0D, 0x0B, 0x0C -> Zeilenumbruch; 0x07 (Zellende) -> Tab; Feldcodes zwischen 0x13 und 0x14 verwerfen, Feldergebnis zwischen 0x14 und 0x15 behalten; 0x01, 0x08 (Objektanker) entfernen [ASSUMED: aus Spezifikationskapiteln, im Plan gegen [MS-DOC] 2.8.25/Feldkapitel prüfen].
**Fallstricke:** "fast-saved" (`fComplex`) ist mit Word 97+ durch die Piece Table abgedeckt: Stücke stehen in CP-Reihenfolge, ihre fc nicht; Prc-Blöcke vor dem Pcdt müssen übersprungen werden. Jede `fc`/Länge gegen die Stream-Länge prüfen, Stückzahl gegen `lcb` begrenzen, Lesen beim Zeichendeckel `max_text_chars` beenden.
**Sniff vor dem Extraktor:** Viele `.doc` sind in Wahrheit RTF ("{\rtf"), HTML ("Word-HTML"-Export) oder DOCX (umbenannt). Signatur prüfen: OLE -> .doc-Leser, `{\rtf` -> `text.extract_rtf`, `PK\x03\x04` -> `office.extract_docx`, `<` nach Leerraum -> `text.extract_html`, sonst `skipped(unsupported_variant)` [ASSUMED: Häufigkeit aus Erfahrung; die Routen existieren].

### Muster 6: .xls über xlrd (FMT-04)

**What:** `xlrd.open_workbook(path, on_demand=True, formatting_info=False, ragged_rows=True, logfile=<Nullsenke>)`, Blätter einzeln über `sheet_by_index`, Zellen zählen gegen `config.settings().max_cells`, bei Überschreitung `skipped(too_many_cells)` (identisch zu `office.extract_xlsx`), danach `unload_sheet(i)`; am Ende `release_resources()`.
**Belege aus xlrd 2.0.2:** `on_demand`, `ragged_rows`, `formatting_info`, `use_mmap`, `logfile` sind Parameter von `open_workbook` (pyright-Signatur aus gebündelten Stubs gelesen). FILEPASS-Record -> `XLRDError("Workbook is encrypted")` (`book.py:943`); nicht unterstützte BIFF-Version -> `XLRDError("BIFF version ... is not supported")` (`book.py:84`); `inspect_format` erkennt eine ZIP-Signatur als xlsx (`__init__.py:66-76`) [VERIFIED: Wheel-Quelltext].
**Werte wie bei XLSX:** Datumszellen (`XL_CELL_DATE`) über `xlrd.xldate_as_datetime(value, book.datemode)`; ganzzahlige Floats als `int` ausgeben (openpyxl liefert `3`, xlrd `3.0`), Fehlerzellen und leere Zellen auslassen.
**Grenze ehrlich benannt:** xlrd parst ein Blatt vollständig, bevor `nrows` bekannt ist. Die Zellgrenze schützt den Index, die Speicher-Spitze eines einzelnen riesigen Blatts schützt nur `RLIMIT_AS` (dann `failed(out_of_memory)`). `ragged_rows=True` ist Pflicht: im Standardmodus füllt `put_cell_unragged` jede Zeile auf die größte Spaltenzahl auf (`sheet.py:714ff`), eine einzige Zelle bei (65535, 255) erzeugt so 16,7 Mio. Einträge.
**Sniff wie bei .doc:** OLE -> xlrd, `PK` -> `office.extract_xlsx`, HTML/XML-Spreadsheet 2003 -> `text.extract_html`, Text/CSV-Export mit `.xls`-Endung -> `text.extract_plain`.

### Muster 7: HEIC/HEIF im Bildpfad (FMT-05)

**What:** In `extract/image.py` beim Import einmal `pillow_heif.register_heif_opener(thumbnails=False, depth_images=False, aux_images=False, decode_threads=1)`; `image/heic` und `image/heif` in `IMAGE_MIMETYPES` (und PHP-Liste, `OCR_CERTAIN_MIMETYPES`).
**Belege:** Lokal mit pillow-heif 1.8.0: libheif 1.23.4, Decoder "libde265 1.1.3"; `Image.open` liefert Format `HEIF`, `DecompressionBombError`/`DecompressionBombWarning` aus `Image.MAX_IMAGE_PIXELS` greifen auch für HEIF; ein abgeschnittener Kopf ergibt `UnidentifiedImageError`, eine am Ende gekürzte Datei beim `load()` aber `ValueError` (nicht `OSError`) [VERIFIED: lokale Probe]. Orientierung: libheif wendet irot/imir an, das Plugin setzt die EXIF-Orientierung auf 1 zurück (`set_orientation`), `ImageOps.exif_transpose` in `image.py:569` dreht also nicht doppelt [VERIFIED: misc.py v1.8.0].
**Warum die Optionen:** `thumbnails=False` hält den neuen `draft()`-Weg aus 1.8.0 (eingebettete Vorschaubilder) aus dem OCR-Pfad; `image._decode_smaller` ruft `draft()` für große Bilder auf, und ein Vorschaubild ist für OCR wertlos. `depth_images`/`aux_images` aus verkleinert die Angriffsfläche. `decode_threads=1`, weil jeder Decoder-Thread unter `RLIMIT_AS` eigenen Stack-Adressraum belegt und das Kind ohnehin seriell arbeitet [ASSUMED: Thread-Stack-Wirkung, im Plan messen].
**RAM:** 24-MP-iPhone-HEIC (5712 x 4284) ergibt etwa 98 MiB als RGB in Pillow (4 Byte je Pixel) mal Arbeitskopie; 48-MP-"HEIF Max" (8064 x 6048) etwa 195 MiB plus libheif-eigene Puffer. Die bestehende Adressraum-Schätzung (`_WORKING_COPIES = 2`, auf JPEG kalibriert) unterschätzt HEIC, weil libheif zusätzlich YCbCr-Ebenen und den RGB-Puffer hält und Draft bei HEIC nicht verkleinert [ASSUMED: im Plan auf amd64 und arm64 messen, Faktor ggf. je Format].

### Muster 8: Nachholweg FMT-06 (Kernbefund und Empfehlung)

**Befund:** D-30-04 geht von "bisher als `legacy_format` übersprungenen .doc/.xls" aus. Im Code tragen `legacy_format` nur OLE-Dateien unter OOXML-Endung; echte `.doc`/`.xls`/`.eml`/`.zip`/`.heic` hat 1.4.2 nie in die Queue gelegt, sie haben **keine Zeile** (Crawl, Listener und Abgleich filtern per Mimetyp in der Abfrage, siehe Ist-Stand). Ein Nachholweg, der nur `state.db` durchläuft, holt sie also nicht nach.

**Empfehlung (Container, einmalig, hinter VERDICTS_GENERATION 3, Marke `recheck_1_5_0`):**
- **Teil A, state.db-Durchlauf** (Muster `worker/recheck.py`, eigene Auswahlfunktion): lebende Zeilen `skipped(legacy_format)` (jetzt lesbar als .doc/.xls) und jede nicht indexierte Zeile, deren gespeicherter Mimetyp zu den sechs neuen gehört (fängt das Mischfenster ab, in dem eine 1.5-Companion schon neue Dateien einreiht, ein 1.4.2-Container sie aber als `mime_not_allowed` speichert). Bänder `REQUEUE_BAND`, Cursor in der Marke, Fortsetzung nach Neustart, "done" am Ende.
- **Teil B, erzwungener Abgleich-Zyklus:** Nach Teil A eine Meta-Marke setzen, die `Reconcile._is_due` als "sofort fällig" liest (wie "nie gelaufen"), und erst nach einem vollständig beendeten Zyklus auf "done". Der Abgleich holt nur Metadaten (Datei-ID, ETag, Größe, Mimetyp, Zeit) über die Dateiliste, vergleicht gegen `known_etags` und reiht Unbekanntes in Bändern zu höchstens 256 ein (`QueueController::MAX_LIST_LENGTH`). Bestehende Treffer mit gleichem ETag werden nicht angefasst, nichts wird heruntergeladen oder neu eingebettet. Die Ruhe-Regel des Abgleichs (`_quiet_gate`) bleibt, er startet also erst, wenn die Queue leer ist.
- **Nicht** einen Vollcrawl auslösen (Migration -> `SchedulerJob`): der lädt jede Datei erneut über das Gateway, weil die schnelle Erkennung erst nach dem Download per Hash vergleicht (`poller.py:1503-1519`).
- **PHP-Seite:** Migration `Version001500Date...` verwirft `backend_app_version` (Pflicht je Minor) und markiert den Nenner als veraltet (`SettingsService::markScanStale`), damit `ScanRecountJob` binnen 15 Minuten neu zählt; sonst zeigt die Abdeckung nach dem Upgrade "mehr durchsuchbar als indexierbar" (Issue-#25-Klasse).

**CI-Beweis (deploy-harp, Andockblock Zeile 3641):**
- Store upgrade 2b: Saatdateien säen (eine `.eml` mit nur HTML-Teil, eine `.zip` mit innerer `.txt`, eine `.doc`, eine `.xls`, eine `.heic`, eine OLE-`.docx`), jede mit eigenem Saatwort. Unter 1.4.2 belegen: neue Typen ohne Zeile in `state.db` und `findling_file_state`, OLE-`.docx` = `skipped/legacy_format`, Saatwörter ohne Treffer.
- Store upgrade 3c: zusätzlich `recheck_1_5_0` abwesend.
- Store upgrade 5: **ohne** `findling:index --restart` (sonst Admin-Eingriff) innerhalb des Budgets: alle Saatwörter finden genau ihre Datei, `recheck_1_5_0 = done`, Indexgeneration und Einbettungsmarke unverändert, Vektorbestand nur um die Saat-Chunks gewachsen, die Chunks und Urteile des Restbestands unverändert. Die heutigen "nichts bewegt sich"-Zusicherungen von Schritt 5 müssen dafür in "Altbestand unverändert" und "Saat neu" getrennt werden.
- L-30-03 mitnehmen: jede Zeile, die in `GITHUB_ENV` schreibt (`REBUILD_VECTORS_BEFORE` Zeile 5301, `UPGRADE_EMBEDDING_MARK`/`UPGRADE_VECTOR_STOCK` in 3c, neue Saat-IDs), vorher per Musterprüfung (`^[0-9a-f]{64}$`, `^[0-9]+$` usw.) prüfen.

### Muster 9: POL-02, veraltete Größe im Dateicache

**Ursache:** `_stream_file` vergleicht die gelesenen Bytes mit `expected` (Größe aus der Queue = Dateicache) und wirft `ShortRead`, wenn weniger kommen (`client.py:286-287`). `_fetch_file` versucht es genau einmal erneut; zweimal kurz gibt die Zeile ohne Urteil und ohne Unlock zurück (`poller.py:1502-1511`), die Queue zählt Auslieferungen und schreibt nach der dritten `failed(repeatedly_stuck)`. Ist der Cache dauerhaft zu groß (externer Speicher außerhalb von Nextcloud geändert, Größe bei serverseitiger Verschlüsselung), endet jede solche Datei dort (deferred-items.md 29, F-29-03).
**Fix:** In `_fetch_file` beide Versuche vergleichen: gleiche Bytezahl **und** gleicher Inhalts-Hash (der `_HashingSink` liefert ihn ohnehin) heißt "das ist die Datei"; dann den zweiten Read normal weiterreichen (Extraktion, Urteil wie jede andere Datei). Unterschiedliche Längen oder Hashes bleiben der vorübergehende Fehler von D-29-04. Bei 0 Bytes zweimal gleich: normaler Weg -> `failed(empty_file)` aus `judge`. Logzeile nur mit Zahlen ("file cache size is stale, read N of M bytes twice"), nie Pfad.
**Altfälle:** Bereits als `repeatedly_stuck` aufgegebene Dateien liegen im Container als `give_up`-Zeile gegen ihren ETag (`reconcile.py:505-517`) und kommen ohne ETag-Wechsel nie zurück. Ob die 1.5-Nachprüfung sie einmal mitnimmt, ist eine offene Frage (siehe unten).
**Restrisiko:** Ein Proxy, der jede Antwort an derselben Stelle abschneidet, sähe ebenfalls zweimal gleich aus. D-29-04 kam aus #18 Fall 2 (Abbruch hinter Proxy); dort war der Abbruch nicht reproduzierbar gleich [ASSUMED]. Abmilderung: Wenn `written` ein Vielfaches gängiger Puffergrößen ist (z. B. glatte MiB), trotzdem als vorübergehend werten; im Plan entscheiden.

### Anti-Patterns to Avoid

- **Vollcrawl als Nachholweg:** lädt den ganzen Datenbestand neu herunter (Hash nach Download).
- **Nachholweg nur über `state.db`:** findet die neuen Typen nicht, sie haben keine Zeile.
- **VERDICTS_GENERATION auf 3 heben, ohne 2 weiter zu akzeptieren:** bricht die 1.4-Codes gegenüber einer 1.4.2-Companion.
- **cp1252 für komprimierte .doc-Stücke:** falsche Zeichen bei 0x80/0x8E/0x9E.
- **xlrd im Standardmodus (`ragged_rows=False`) oder mit `logfile=sys.stdout`:** Speicherbombe bzw. Blattnamen (Dateiinhalt) im Log (`sheet.py:609` gibt den Blattnamen mit `%r` aus).
- **Archivpfade als Dateinamen auf der Platte:** unnötige Traversal-Fläche; laufende Nummer nehmen.
- **`str(exception)` bei zipfile/xlrd:** Meldungen enthalten Mitgliedsnamen bzw. Inhalte; nur Klassennamen als `detail` (wie `from_exception`).
- **OCR in ZIP-Mitgliedern:** sprengt das 120-s-Budget und den RAM.
- **Neuer Code je Grenzfall** (`zip_too_deep`, `zip_too_many`...): jeder Code kostet 16 l10n-Dateien plus Doku plus drei Listen.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CFB/OLE-Streams lesen (FAT, MiniFAT, DIFAT) | Ausbau von `cfb.py` zu einem Stream-Leser | olefile 0.47 | Ketten, MiniStream, Schleifenschutz; cfb.py bleibt reiner Sniff |
| BIFF-Parsing | eigener .xls-Leser | xlrd 2.0.2 | Shared Strings, CONTINUE-Records, Codepages, Datumsformate |
| HEVC/HEIF-Dekodierung | nichts Eigenes | pillow-heif 1.8.0 | Codec |
| MIME-Parsing, RFC 2047/2231, Transfer-Encodings | eigener Header-Dekoder | `email` mit `policy.default` | Viele Randfälle, CPython pflegt Sicherheitsfixes |
| Overlap-Zip-Bomben | eigene Overlap-Erkennung | `zipfile` ab 3.12.2/3.13 (CVE-2024-0450) | Bereits im Interpreter |
| HTML zu Text | zweite HTML-Strecke | `extract/text.py` (gehärtete lxml-Parser) als `html_to_text(str)` | Eine Strecke, XXE/SSRF schon geschlossen |

**Key insight:** Selbst bauen nur dort, wo es keine gepflegte permissive Bibliothek gibt: die Word-Piece-Table (rund 150 Zeilen nach Spezifikation) und die EOCD-Vorprüfung (rund 40 Zeilen). Beides ist klein, spezifikationsgebunden und mit selbst gebauten Testdateien prüfbar.

## Runtime State Inventory

Phase 31 ist kein Umbenennungsschritt, verändert aber gespeicherten Zustand beim Upgrade.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `state.db`: Zeilen `skipped(legacy_format)` (OLE unter OOXML-Namen), ggf. `give_up`-Zeilen `failed(repeatedly_stuck)`; Meta-Marken `recheck_1_4_0` (done) | Neue Marke `recheck_1_5_0`; Datenmigration = Neu-Einreihen in Bändern, kein SQL-Umschreiben von Urteilen |
| Live service config | PHP `findling_file_state` hält keine Zeilen für neue Typen; `findling_scan_stats` (Nenner) zählt nur Allowlist-Typen | Nenner per `markScanStale` neu zählen lassen |
| OS-registered state | Keine (AppAPI-Container, keine Systemdienste) | Keine, geprüft an Dockerfile und info.xml |
| Secrets/env vars | Keine neuen; ggf. neue optionale `FINDLING_*`-Grenzen, falls Admins sie stellen sollen (nicht empfohlen für v1.5) | Keine |
| Build artifacts | Image wächst um pillow-heif (Wheel 6,4 MB, entpackt rund 15,8 MB, davon libx265 11,4 MB), olefile, xlrd | `THIRD-PARTY.md`-Tabelle, Bau-Prüfung in `docker.yml` (HEIC-Dekodierung auf beiden Architekturen) |

## Common Pitfalls

### Pitfall 1: Nachholweg findet nichts
**What goes wrong:** Nach dem Upgrade bleiben alle alten .eml/.zip/.doc/.xls/.heic unauffindbar, nur neu hochgeladene erscheinen.
**Why it happens:** Kein DB-Eintrag (Mimetyp-Filter), Abgleich erst in 24 bis 48 h.
**How to avoid:** Muster 8, Teil B. CI ohne `--restart`.
**Warning signs:** CI-Schritt 5 wird nur mit `--restart` grün.

### Pitfall 2: Generationssprung bricht 1.4-Codes
**What goes wrong:** Mit `VERDICTS_GENERATION = 3` gelten 2-Companions als "ohne Signal", `system_file` wird zu `mime_not_allowed`.
**How to avoid:** Menge bekannter Generationen, Fallback je Code und Generation; Test gegen beide.

### Pitfall 3: Mischfenster speichert falsche Urteile dauerhaft
**What goes wrong:** Companion 1.5 reiht neue Typen ein, Container noch 1.4.2 speichert `mime_not_allowed` gegen den ETag; der Abgleich sieht später "bekannt, gleicher ETag" und lässt sie liegen.
**How to avoid:** Teil A wählt jede nicht indexierte Zeile mit neuem Mimetyp.

### Pitfall 4: Unbekannter Zeichensatz in Mail-Teilen
**What goes wrong:** `get_content()` wirft `LookupError` (lokal geprüft mit `charset=x-unknown-zz`).
**How to avoid:** Abfangen, Rohbytes über `get_payload(decode=True)` an `text._decode` (charset-normalizer).

### Pitfall 5: XHTML-Mailteil mit XML-Deklaration
**What goes wrong:** `lxml.etree.fromstring(str)` mit Kodierungsdeklaration wirft `ValueError`.
**How to avoid:** `html_to_text` bekommt Bytes (`.encode("utf-8")` und Deklaration entfernen) oder nutzt für Mails nur den HTML-Parser.

### Pitfall 6: Rekursion bei verschachtelten MIME-Teilen
**What goes wrong:** 2 000 Ebenen -> `RecursionError` (gemessen), wird ohne Behandlung `failed(corrupt)`.
**How to avoid:** Tiefen-/Teilgrenze, Urteil `archive_limit` oder `corrupt` bewusst wählen und testen.

### Pitfall 7: ZIP-Zentralverzeichnis als Speicherbombe
**What goes wrong:** `ZipFile()` baut alle `ZipInfo`-Objekte vor jeder eigenen Prüfung.
**How to avoid:** EOCD-Vorprüfung (Muster 3, Stufe 1).

### Pitfall 8: Meldungstexte mit Inhalt im Log
**What goes wrong:** `RuntimeError("File 'geheim.txt' is encrypted...")`, xlrd-Warnungen mit Blattnamen.
**How to avoid:** Flags vorher prüfen, xlrd `logfile` auf Nullsenke, nur Klassennamen als `detail`; der bestehende Grep-Test gegen Pfade im Log deckt neue Module mit ab.

### Pitfall 9: xlrd ohne `ragged_rows`
Siehe Muster 6; eine Zelle am Blattende erzeugt 16,7 Mio. Listeneinträge.

### Pitfall 10: .doc als RTF/HTML/DOCX verkleidet
**How to avoid:** Signatur-Sniff vor dem OLE-Leser (Muster 5), sonst `failed(corrupt)` für lesbare Dateien.

### Pitfall 11: HEIC-Thumbnails im OCR-Pfad
**What goes wrong:** Seit pillow-heif 1.8.0 kann `draft()` ein eingebettetes Vorschaubild wählen ("smallest thumbnail that is not smaller than size", `as_plugin.py:84-101`).
**How to avoid:** `thumbnails=False` bei der Registrierung. Bei der heutigen Draft-Zielgröße (3 500 px) wäre kein Vorschaubild groß genug, die Option macht es aber unabhängig von künftigen Zielgrößen.

### Pitfall 12: Adressraum-Schätzung für HEIC zu knapp
**How to avoid:** Faktor für HEIF messen (24 MP und 48 MP, amd64 und arm64), sonst stirbt das Kind mit `MemoryError` statt eines ehrlichen `skipped(too_large)`.

### Pitfall 13: Zusicherungen von Store upgrade 5
**What goes wrong:** Schritt 5 verlangt heute "das Upgrade bewegt keinen Zähler, kein Urteil, keinen Vektor, keine Marke"; der Nachholweg bewegt genau das für die Saat.
**How to avoid:** Zusicherungen in Altbestand (unverändert) und Saat (neu indexiert) trennen, nie lockern.

### Pitfall 14: Highlight-Versatz im Snippet
**What goes wrong:** Präfix "name: " verschiebt alle Zeichenbereiche.
**How to avoid:** Bereiche verschieben und im Test die markierten Wörter aus dem ausgelieferten Text lesen.

### Pitfall 15: l10n-Kette
**What goes wrong:** Ein neuer Code oder ein geänderter Hilfetext ohne alle 16 PHP-l10n-Dateien und fünf `docs/l10n-*.md` lässt englischen Text in der Oberfläche stehen.
**How to avoid:** Ein einziger neuer Code (`archive_limit`), Textänderungen gebündelt (`mime_not_allowed`-Hilfe nennt die neuen Formate).

## Code Examples

### .eml (Skizze)
```python
# Quelle: CPython email-Doku (policy.default, get_body); Verhalten lokal geprüft 10.10.2026
from email import policy
from email.parser import BytesParser

_HEADERS = ("subject", "from", "to", "cc")

def extract_eml(path: str) -> ExtractionOutcome:
    with open(path, "rb") as handle:
        message = BytesParser(policy=policy.default).parse(handle)
    parts = [str(message[name]) for name in _HEADERS if message[name] is not None]
    body = message.get_body(preferencelist=("plain", "html"))
    if body is not None:
        parts.append(_body_text(body))  # LookupError -> Rohbytes an text._decode; html -> text.html_to_text
    parts += [name for part in message.iter_attachments() if (name := part.get_filename())]
    return cap_text("\n".join(part for part in parts if part.strip()))
```

### ZIP: Eintragszahl vor `ZipFile()`
```python
# Quelle: PKWARE APPNOTE 4.3.16 (EOCD) und 4.3.14 (ZIP64-EOCD) [ASSUMED: Offsets im Plan gegen APPNOTE prüfen]
_EOCD_SIGNATURE = b"PK\x05\x06"
_EOCD_MIN = 22
_COMMENT_MAX = 0xFFFF

def declared_entries(handle: BinaryIO, size: int) -> int | None:
    tail_len = min(size, _EOCD_MIN + _COMMENT_MAX)
    handle.seek(size - tail_len)
    tail = handle.read(tail_len)
    at = tail.rfind(_EOCD_SIGNATURE)
    if at < 0 or at + _EOCD_MIN > len(tail):
        return None  # zipfile soll BadZipFile melden
    (total,) = struct.unpack_from("<H", tail, at + 10)
    if total == 0xFFFF:
        return _zip64_total(handle, size - tail_len + at)  # Locator 20 Bytes davor
    return total
```

### .doc: Text aus einem Stück
```python
# Quelle: [MS-DOC] 2.4.1 Retrieving Text, 2.9.73 FcCompressed (Tabelle 0x82..0x9F)
_FC_COMPRESSED_BIT = 0x40000000
_SPECIAL = {0x82: "\u201a", 0x83: "\u0192", 0x84: "\u201e", 0x85: "\u2026", 0x86: "\u2020",
            0x87: "\u2021", 0x88: "\u02c6", 0x89: "\u2030", 0x8A: "\u0160", 0x8B: "\u2039",
            0x8C: "\u0152", 0x91: "\u2018", 0x92: "\u2019", 0x93: "\u201c", 0x94: "\u201d",
            0x95: "\u2022", 0x96: "\u2013", 0x97: "\u2014", 0x98: "\u02dc", 0x99: "\u2122",
            0x9A: "\u0161", 0x9B: "\u203a", 0x9C: "\u0153", 0x9F: "\u0178"}
_COMPRESSED_TABLE = str.maketrans({chr(byte): char for byte, char in _SPECIAL.items()})

def piece_text(word: bytes, fc_raw: int, chars: int) -> str:
    if fc_raw & _FC_COMPRESSED_BIT:
        start = (fc_raw & ~_FC_COMPRESSED_BIT) // 2
        raw = word[start : start + chars]
        if len(raw) != chars:
            raise CorruptDocument  # wird zu failed(corrupt)
        return raw.decode("latin-1").translate(_COMPRESSED_TABLE)
    start = fc_raw & 0x3FFFFFFF
    raw = word[start : start + 2 * chars]
    if len(raw) != 2 * chars:
        raise CorruptDocument
    return raw.decode("utf-16-le", errors="replace")
```
(Im Repo-Code müssen die Unicode-Zeichen als Escapes stehen, wie oben, weil Gedankenstrich-Zeichen U+2013/U+2014 sonst als Literal im Quelltext landen.)

### .xls
```python
# Quelle: xlrd 2.0.2 open_workbook-Signatur (pyright, gebündelte Stubs), book.py:943
import os
import xlrd

def extract_xls(path: str) -> ExtractionOutcome:
    limit = config.settings().max_cells
    with open(os.devnull, "w", encoding="ascii") as sink:
        try:
            book = xlrd.open_workbook(path, on_demand=True, formatting_info=False, ragged_rows=True, logfile=sink)
        except xlrd.XLRDError as error:
            if str(error) == "Workbook is encrypted":  # feste Meldung ohne Inhalt
                return ExtractionOutcome.skipped(Reason.ENCRYPTED)
            return ExtractionOutcome.from_exception(error)
        try:
            seen, parts = 0, []
            for index in range(book.nsheets):
                sheet = book.sheet_by_index(index)
                for row in range(sheet.nrows):
                    values = sheet.row_values(row)
                    seen += len(values)
                    if seen > limit:
                        return ExtractionOutcome.skipped(Reason.TOO_MANY_CELLS)
                    parts += [_cell_text(book, sheet, row, col) for col in range(len(values))]
                book.unload_sheet(index)
        finally:
            book.release_resources()
    return cap_text("\n".join(part for part in parts if part and part.strip()))
```

### HEIC-Registrierung
```python
# Quelle: pillow_heif v1.8.0 as_plugin.register_heif_opener, options.py; lokal geprüft
import pillow_heif

pillow_heif.register_heif_opener(thumbnails=False, depth_images=False, aux_images=False, decode_threads=1)
```

### POL-02
```python
# Ort: worker/poller.py _fetch_file; Prinzip, nicht fertiger Code
async def _fetch_file(self, job: QueueJob) -> _Read | None:
    try:
        return await self._fetch_once(job)
    except ShortRead as first:
        LOGGER.info("download of one file came back short, fetching it once more")
        first_cut = first  # trägt written und content_hash (ShortRead um diese zwei Zahlen erweitern)
    try:
        return await self._fetch_once(job)
    except ShortRead as second:
        if second.written == first_cut.written and second.content_hash == first_cut.content_hash:
            LOGGER.info("the file cache names a stale size, the same %d bytes arrived twice", second.written)
            return await self._fetch_once(job, accept_short=True)  # oder den zweiten Read behalten statt verwerfen
        raise
```
(Besser als ein dritter Download: beim zweiten Versuch die Scratch-Datei nicht verwerfen, sondern bei Gleichheit direkt als `_Read` zurückgeben.)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pi-heif als schlanke Decoder-Variante | nur noch pillow-heif | pillow-heif 1.5.0, 22.07.2026 (#431) | FMT-05 nennt pi-heif; gleichwertig ist pillow-heif |
| pillow-heif ohne Typinformation | `py.typed` (1.7.0), Exporte für Pyright korrigiert (1.8.0, #490) | 06.09. und 22.09.2026 | pyright basic ohne Ausnahmen |
| zipfile ohne Overlap-Schutz | `BadZipFile("Overlapped entries")` | CPython 3.12.2/3.11.8 (CVE-2024-0450) | Quoted-overlap-Bomben fängt der Interpreter |
| xlrd liest auch xlsx | xlrd 2.x nur .xls | 2.0.0, 11.12.2020 | xlsx bleibt bei openpyxl |

**Deprecated/outdated:**
- pi-heif: eingestellt, keine Sicherheitsupdates mehr.
- Der Docstring in `dispatch.py` ("Container formats such as compressed archives are not opened at all", "Legacy Office ... outside v1", "HEIC ... stay out") und der Gegenabsatz in `StorageService.php` werden mit dieser Phase falsch und müssen ersetzt werden; der Paritätstest verlangt den identischen Absatz auf beiden Seiten.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | fcClx/lcbClx liegen im Fib an 0x01A2/0x01A6 (abgeleitet aus Feldgrößen) | Muster 5 | Kein Text aus .doc; Test mit LibreOffice-Datei deckt es sofort auf |
| A2 | Steuerzeichen-Behandlung 0x07/0x13..0x15/0x01/0x08 wie beschrieben | Muster 5 | Feldcodes oder Müll im Index |
| A3 | cp437 und cp850 decken deutsche Umlaute auf gleichen Codepunkten | Muster 3 | Falsche Mitgliedsnamen in der Subline |
| A4 | Deflate-Höchstrate etwa 1032:1, Rate 100:1 trifft keine üblichen Textdateien | Muster 3 | Fehlurteile `archive_limit` bei stark redundanten Logs/CSV |
| A5 | `decode_threads=1` spart Adressraum unter `RLIMIT_AS` | Muster 7 | Nur Leistung; messen |
| A6 | HEIC braucht einen höheren Speicherfaktor als JPEG | Muster 7, Pitfall 12 | Kind stirbt statt ehrlichem Urteil |
| A7 | Viele `.doc`/`.xls` sind RTF/HTML/CSV/DOCX unter Altendung | Muster 5/6 | Nur Mehraufwand im Sniff, kein Risiko |
| A8 | #18 Fall 2 schnitt nicht reproduzierbar gleich ab | Muster 9 | Proxy mit fester Kappung würde abgeschnittene Dateien indexieren |
| A9 | Debian-libheif-Weg spart Image-Größe, kostet Build-Aufwand | Alternatives | Nur Entscheidungsgrundlage |
| A10 | EOCD-Offsets (Feld "total entries" bei +10, ZIP64-Locator 20 Bytes vor EOCD) | Code Examples | Vorprüfung greift nicht; zipfile-Ausnahme bleibt Netz |

## Open Questions

1. **Bereits aufgegebene `repeatedly_stuck`-Dateien einmal mitnehmen? (Owner-Entscheid möglich)**
   - Was wir wissen: Der POL-02-Fix wirkt nur für künftige Downloads; aufgegebene Dateien kommen ohne ETag-Wechsel nie zurück.
   - Unklar: `repeatedly_stuck` entsteht auch durch andere Ursachen (Kind-Abstürze), ein Nachlauf kostet höchstens drei Auslieferungen je Datei.
   - Empfehlung: in Teil A des Nachholwegs aufnehmen (einmalig, gebändert); Owner-Veto möglich, da D-30-04 es nicht nennt.

2. **D-30-04-Wortlaut gegen Code-Realität (Owner-Info, kein Entscheid nötig)**
   - D-30-04 spricht von "als `legacy_format` übersprungenen .doc/.xls"; echte .doc/.xls hatten nie eine Zeile. Die Empfehlung (Teil A + B) erfüllt die Absicht vollständig. Kurz bestätigen lassen.

3. **Skip-Code für Grenzüberschreitungen: ein neuer Code `archive_limit` (Owner-Entscheid wegen sichtbarem Wortlaut)**
   - Alternativen: `too_large` wiederverwenden (Hilfetext "Raise the value under 'Largest file to read'" wäre irreführend) oder mehrere Codes (l10n-Kosten).
   - Empfehlung: genau ein Code, Label etwa "Archive over the safety limits", Hilfe "None. Archives that are too deep, too large or too densely packed are skipped so the container keeps running."

4. **Nicht lesbare .doc/.xls-Varianten: welcher Code?**
   - Empfehlung: `unsupported_variant` mit verallgemeinertem Label ("Variant of this format that cannot be read"); `legacy_format` bleibt für PowerPoint-Altformat unter `.pptx`. Beides ändert sichtbaren Text (l10n-Kette); Store-Text-Abnahme REL-05.

5. **`zip` in einer der sechs Typfilter-Gruppen?**
   - Was wir wissen: Phase 32 liefert genau sechs Gruppen (`SearchFilters::TYPES`), `zip` passt in keine.
   - Empfehlung: in keiner Gruppe, als Grenze in `docs/search-filters.md` nennen; `doc`/`dot` zu documents, `xls`/`xlt` zu spreadsheets, `heic`/`heif` zu images.

6. **Mail-Anhänge: nur Namen oder auch Inhalt?**
   - Empfehlung: nur Namen in 1.5 (FMT-01 verlangt keine Anhänge); Inhalt als späterer Ausbau über die ZIP-Mitgliedsschleife. Owner-Veto möglich.

7. **ZIP-Grenzwerte als Admin-Einstellung?**
   - Empfehlung: nein, feste Konstanten in `config.py` mit Begründung (Zero-Config); Phase 33 zeigt Grenzwerte nur an (#21).

8. **pillow-heif-Wheel mit 11,4 MB ungenutztem x265-Encoder**
   - Empfehlung: in Kauf nehmen; Debian-Weg erst, wenn die Image-Größe zum Problem wird. Lizenzlage (GPLv2-or-later) in THIRD-PARTY.md ausführlich begründen.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | Abhängigkeiten, Tests | ✓ | 0.11.7 | ; |
| Python 3.13 (über uv) | Backend | ✓ | 3.13.13 lokal, Image 3.13.15 | ; |
| pyright | Gate | ✓ | 1.1.414 | ; |
| LibreOffice (lokal) | Testdateien .doc/.xls erzeugen (eigener Inhalt) | ✓ | `C:\Program Files\LibreOffice\program\soffice.exe` | Testdateien per eigenem CFB-Builder (`conftest.build_cfb`) |
| pillow-heif-Encoder (x265 im Wheel) | HEIC-Testdateien zur Testlaufzeit erzeugen | ✓ | 1.8.0, auch Windows-Wheel | committete Fixture |
| Docker | Image-Bau lokal | ✓ | 29.5.2 | CI |
| PHP lokal | PHP-Tests | ✗ | ; | PHP-Gates nur in CI (`php.yml`, phpunit im Server-Checkout) |
| gh CLI | CI-Läufe beobachten | ✓ | 2.92.0 | ; |

**Missing dependencies with no fallback:** keine.
**Missing dependencies with fallback:** PHP lokal fehlt, Prüfung über CI.

## Validation Architecture

> `workflow.nyquist_validation` ist in `.planning/config.json` auf `false`; der Abschnitt steht hier, weil der Auftrag ihn ausdrücklich verlangt.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1, pytest-asyncio 1.4.0, pytest-cov 7.1.0; PHP: phpunit in CI |
| Config file | `backend/pyproject.toml` (`[tool.pytest.ini_options]`, `filterwarnings error::DeprecationWarning`) |
| Quick run command | `cd backend && uv run pytest -q tests/test_extract_mail.py tests/test_extract_archive.py tests/test_legacy_doc.py tests/test_legacy_xls.py tests/test_ocr.py -x` |
| Full suite command | `cd backend && uv run pytest -q -rs --cov=src/findling --cov-report=term` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FMT-01 | Betreff/Absender/Empfänger (RFC 2047), Plain-Teil, Nur-HTML-Mail ohne script/style, unbekannter Zeichensatz, Anhangname, Tiefe/Teilzahl | unit | `uv run pytest tests/test_extract_mail.py -x` | ❌ Wave 0 |
| FMT-02 | innere Datei findbar, Snippet "innen.txt: ...", Highlights verschoben; Bomben: Einträge über Grenze (EOCD), Gesamtgröße, Rate, Tiefe/Quine, verschlüsselte und AES-Mitglieder, Overlap -> Urteil, nie Absturz; cp437/UTF-8-Namen | unit + Snippet-Integration | `uv run pytest tests/test_extract_archive.py tests/test_snippet_offsets.py -x` | ❌ / ✅ (erweitern) |
| FMT-03 | LibreOffice-.doc (komprimiert und Unicode), Tabelle, Feldcode, Sondertabelle 0x80/0x82, verschlüsselt (`fEncrypted`), Word 6 (`nFib`), RTF/DOCX/HTML unter .doc, kaputte Kette (olefile DEFECT_INCORRECT) | unit | `uv run pytest tests/test_legacy_doc.py -x` | ❌ Wave 0 |
| FMT-04 | Werte, Datum, Ganzzahl, Zellgrenze per `FINDLING_MAX_CELLS` klein = `too_many_cells`, verschlüsselt, xlsx unter .xls, ragged | unit | `uv run pytest tests/test_legacy_xls.py -x` | ❌ Wave 0 |
| FMT-05 | HEIC mit Text -> OCR-Treffer (Image-Probe), Bombe über `MAX_IMAGE_PIXELS`, abgeschnittene Datei -> Urteil, Orientierung | unit + Image-Probe in `docker.yml` (amd64 + arm64) | `uv run pytest tests/test_ocr.py -k heic -x` | ✅ (erweitern) |
| FMT-01..05 | Allowlist-Parität PHP/Python, jede Route hat Extraktor, Typgruppen | unit | `uv run pytest tests/test_allowlist_parity.py tests/test_extract_documents.py -x` | ✅ (erweitern) |
| FMT-06 | Auswahl Teil A (legacy_format, neue Mimetypen, nicht indexiert), Bänder, Cursor, Neustart, done; Teil B Fälligkeit einmalig; Start nur bei Generation 3, Generation 2 weiter bekannt | unit | `uv run pytest tests/test_recheck.py tests/test_reconcile.py tests/test_queue_client.py -x` | ✅ (erweitern) |
| FMT-06 | 1.4.2 -> 1.5 ohne Admin-Eingriff, Saat findbar, Altbestand unverändert | CI e2e | `deploy-harp.yml` Store upgrade 2b/3c/5 | ✅ (Andockblock) |
| POL-02 | zweimal gleich kurz + gleicher Hash -> extrahiert; ungleich kurz -> wie bisher ohne Urteil; 0 Bytes -> `empty_file` | unit (Regressionstest) | `uv run pytest tests/test_poller.py -k short -x` | ✅ (erweitern) |
| alle | Urteilsliste dreifach gleich (Python, Store, PHP), neuer Code mit Fallback | unit | `uv run pytest tests/test_extract_errors.py -x` | ✅ (erweitern) |
| alle | keine Pfade/Namen im Log | unit | bestehender Log-Grep-Test, neue Module einbeziehen | ✅ |

### Sampling Rate
- **Per task commit:** Quick run plus `uv run ruff check`, `uv run ruff format --check`, `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright`, `uv run vulture`.
- **Per wave merge:** Full suite.
- **Phase gate:** Full suite grün, CI Python gates, Docker-Build (beide Architekturen mit HEIC-Probe), deploy-harp grün über alle Store-upgrade-Schritte.

### Wave 0 Gaps
- [ ] `backend/tests/test_extract_mail.py`: FMT-01
- [ ] `backend/tests/test_extract_archive.py`: FMT-02 inklusive Bombenkorpus (zur Testlaufzeit gebaut: deflate-Rate, 10 001 Einträge, Tiefe 3, Quine-artig selbstreferenzierend, Overlap nach Fifield, AES-Methode 99)
- [ ] `backend/tests/test_legacy_doc.py`, `backend/tests/test_legacy_xls.py`: FMT-03/04
- [ ] Testdateien: `.doc`/`.xls` mit LibreOffice aus eigenem Inhalt erzeugen (REUSE: eigenes Werk, AGPL), zusätzlich minimal per `conftest.build_cfb` gebaute OLE-Dateien mit WordDocument/1Table-Streams (Builder um Stream-Inhalte erweitern)
- [ ] HEIC-Testbild zur Laufzeit über pillow-heif erzeugen (Encoder im Wheel, auch Windows)
- [ ] Saatdateien für deploy-harp unter `.github/fixtures/` mit Erzeugerskript und Byte-Vergleichstest (Muster `test_upgrade_seed_fixture.py`)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein | unverändert (AppAPI) |
| V3 Session Management | nein | ; |
| V4 Access Control | ja, indirekt | Snippet-Pfad bleibt hinter `prefilter_visible` und PHP-Recheck; Mitgliedsnamen sind Dokumentinhalt und dürfen nur dort erscheinen |
| V5 Input Validation | ja | Grenzprüfungen vor dem Parsen (EOCD, deklarierte Größen, MIME-Tiefe, Zellgrenze, Pixelgrenze), Sandbox-Kind mit `RLIMIT_AS` und Frist |
| V6 Cryptography | nein | verschlüsselte Inhalte werden nicht geöffnet (`encrypted`) |
| V7 Error Handling/Logging | ja | nur Klassennamen als `detail`, keine Meldungstexte (zipfile/xlrd enthalten Namen), xlrd-`logfile` stumm |
| V12 Files and Resources | ja | keine Pfade aus Archiven auf die Platte, temporäre Dateien mit laufender Nummer, sofort löschen |
| V14 Configuration/Dependencies | ja | exakte Pins, Dependabot, THIRD-PARTY/REUSE, Lizenzprüfung |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Zip-Bombe (Rate, Gesamtgröße, Overlap, rekursiv/Quine) | Denial of Service | EOCD-Vorprüfung, deklarierte Größen, Rate, Tiefe, zipfile-Overlap-Schutz, `RLIMIT_AS`, 120 s |
| Riesiges Zentralverzeichnis | DoS | Eintragszahl vor `ZipFile()` |
| Pfad-Traversal in Mitgliedsnamen | Tampering | nie unter Mitgliedsnamen schreiben |
| Bidi-/Steuerzeichen im Mitgliedsnamen (Spoofing in der Subline) | Spoofing | Steuer- und Bidi-Zeichen entfernen, Länge kappen |
| Tief verschachtelte MIME-Teile | DoS | Tiefen-/Teilgrenze, `RecursionError` mit Urteil |
| XXE/SSRF im HTML-Teil | Information Disclosure | bestehende lxml-Parser (`resolve_entities=False`, `no_network=True`) |
| OLE mit kaputten oder zyklischen Sektorketten | DoS | olefile-Schleifen fester Länge, `DEFECT_INCORRECT`; cfb-Sniff bleibt mit eigenem Zyklenschutz |
| xls-Speicherbombe über weit entfernte Zellen | DoS | `ragged_rows=True`, Zellgrenze, `RLIMIT_AS` |
| HEIF-Decoder-Schwachstellen (libheif/libde265) | Elevation/DoS | aktuelles pillow-heif, Thumbnails/Depth/Aux aus, Sandbox-Kind, Dependabot |
| Inhalt in Logs (Mitgliedsnamen, Blattnamen) | Information Disclosure | Flags vorher prüfen, stumme Logsenken, bestehender Log-Grep-Test |

## Sources

### Primary (HIGH confidence)
- Repo-Code, gelesen am 10.10.2026: `backend/src/findling/extract/{dispatch,cfb,errors,office,image,text,sandbox}.py`, `worker/{recheck,reconcile,poller}.py`, `nc/{client,queue}.py`, `index/search.py`, `query/rewrite.py`, `config.py`; `php/lib/Service/StorageService.php`, `BackgroundJobs/{StorageCrawlJob,SchedulerJob,ScanRecountJob}.php`, `Repair/AppInstallStep.php`, `Migration/Version001400Date20261006000000.php`; `.github/workflows/deploy-harp.yml` (Zeilen 80-140, 3386-3663, 4221-4289, 5285-5310); `THIRD-PARTY.md`, `REUSE.toml`
- PyPI-JSON (10.10.2026): olefile, xlrd, pi-heif, pillow-heif, pillow (Versionen, Upload-Daten, Wheels, requires_dist)
- Wheel-Inhalte: pillow_heif-1.8.0 aarch64 (libheif 1.23.4, libde265 1.1.3, libx265, `py.typed`), olefile-0.47 und xlrd-2.0.2 (LICENSE-Texte, Quelltext)
- https://github.com/bigcat88/pillow_heif/blob/master/CHANGELOG.md (pi-heif eingestellt, 1.5.0 bis 1.8.0)
- https://raw.githubusercontent.com/bigcat88/pillow_heif/v1.8.0/LICENSES_bundled.txt, `as_plugin.py`, `options.py`, `misc.py`
- https://bitbucket.org/multicoreware/x265_git/raw/4.2/source/encoder/encoder.cpp (GPL "version 2 ... or any later version")
- [MS-DOC FibBase](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-doc/26fb6c06-4e5c-4778-ab4e-edbf26a545bb), [Retrieving Text](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-doc/01d5d8c4-cf9c-4ef9-80fd-439e763cfe01), [Clx](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-doc/bad26767-b575-44d3-9da3-96378d56ce14), [FcCompressed](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-doc/aa2e55a2-f4f2-4795-bab5-6d9d7a0ed249)
- nextcloud/server `resources/config/mimetypemapping.dist.json` auf stable33, stable34, master: eml -> message/rfc822, zip -> application/zip, doc/dot -> application/msword, xls/xlt -> application/vnd.ms-excel, heic -> image/heic, heif -> image/heif
- Lokale Proben (CPython 3.13.13, Windows): email-Parsing, MIME-Rekursion, zipfile-Verschlüsselung/Overlap/Speicher, pillow-heif-Rundlauf, pyright 1.1.414 basic ohne Fehler, Importe unter `-W error::DeprecationWarning`

### Secondary (MEDIUM confidence)
- CVE-2024-0450 (zipfile quoted-overlap) über cve.circl.lu, gegengeprüft am Quelltext ("Overlapped entries")
- pypistats.org (Downloads), GitHub-API (Repo-Status)
- slopcheck 0.6.1 (alle [OK])

### Tertiary (LOW confidence)
- Deflate-Höchstrate, Thread-Stack-Wirkung, HEIC-Speicherfaktor, Häufigkeit verkleideter .doc/.xls (siehe Assumptions Log)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, Versionen, Lizenzen, Wheels und pyright per Befehl belegt
- Architecture: HIGH für Befunde im Code, MEDIUM für den Nachholweg-Entwurf (an zwei bestehende, getestete Mechanismen angelehnt)
- Pitfalls: MEDIUM-HIGH, die meisten lokal reproduziert, Speicherfaktoren offen

**Research date:** 2026-10-10
**Valid until:** 2026-11-09 (pillow-heif bewegt sich schnell, 1.9.0 mit libheif 1.23.5 ist angekündigt; vor dem Bau neu prüfen)
