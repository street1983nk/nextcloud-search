# Phase 36: Härtung und Store-Einreichung 1.5.0 - Research

**Researched:** 2026-10-20
**Domain:** Launch-Härtung (bösartiger Formatkorpus, Index-Hygiene M-32-02, Upgrade-Strecke), Release- und Store-Mechanik
**Confidence:** HIGH für Code-Befunde (gelesen und teils live gemessen), MEDIUM für Grenzwert-Empfehlungen (Abwägung, keine Messreihe)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Boesartiger Formatkorpus (Owner-Entscheide 20.10.2026)
- **D-36-01:** Der Korpus lebt als Generatoren in den Tests: Testhelfer
  bauen die boesartigen Dateien zur Laufzeit deterministisch (Muster
  build_cfb aus Phase 29). KEINE boesartigen Binaerdateien im public Repo.
- **D-36-02:** Umfang ERWEITERT: Pflichtfamilien aus dem Erfolgskriterium
  (Archive: Bomben, Pfad-Traversal, Verschachtelung; Mails; OLE-Dateien)
  PLUS XML-Bomben (Billion Laughs in ODF/OOXML), Bild-Dekompressionsbomben
  (TIFF/PNG), uebergrosse Einzeleintraege und polyglotte Dateien.
- **D-36-03:** Boesartige Dateien enden in einer NEUEN Urteilsklasse: EINE
  Sammelklasse (Arbeitsname blocked_malicious, endgueltiger Name und
  Wortlaute ueber den Vorabplan) fuer alle Familien, der Detailgrund steht
  in der Diagnose-Zeile (file_errors + /diagnose + Admin-Karte).
- **D-36-04:** Die neuen Wortlaute (Admin-Karte, /diagnose, Kataloge) gehen
  de/en/fr als Wortlaut-Vorabplan an den Owner (Muster 34-01/35-01), BEVOR
  sie in Code und die 16 Kataloge reisen.

#### M-32-02 Nachweis (Owner-Entscheide 20.10.2026)
- **D-36-05:** Die 30-Tage-Karenz fuer verschwundene externe Speicher wird
  im Test per SQL-Rueckdatierung des Erstsichtungs-Zeitstempels gerafft
  (Muster Drift-Marke 35-08). Die 30 Tage bleiben fest im Code, KEIN
  Produkt-Schalter nur fuer Testbarkeit.
- **D-36-06:** Beleg zweigleisig: Live-Beleg auf der Dev-Instanz 8090 mit
  Positivkontrolle (zweiter Nutzer bleibt im Index) PLUS dauerhafter
  Integrationstest in CI gegen Regression.

#### Textstellen (Owner-Entscheide 20.10.2026)
- **D-36-07:** docs/embeddings.md:497 "fulltextsearch jahrelang verwaist":
  Praeteritum bleibt, Halbsatz ergaenzen, dass fulltextsearch seit 2026
  wieder gepflegt wird, aber weiterhin Elasticsearch-gekoppelt ist.
- **D-36-08:** Store-Text backend/appinfo/info.xml:113 "half of the box"
  wird praezisiert auf die Maschine, auf der das Backend laeuft (analog zur
  Admin-Karten-Praezisierung aus 1.4.1), in EN/DE/FR; der neue Wortlaut
  laeuft durch die Store-Text-Abnahme.

#### Release-Ablauf (Owner-Entscheide 20.10.2026)
- **D-36-09:** L-35-06: httpx/httpcore-Logger im Image auf WARNING heben,
  damit fileid/userId nicht mehr im Standardlog stehen; Debug bleibt per
  Loglevel-Umschaltung moeglich.
- **D-36-10:** release.yml haengt zusaetzlich Quellpakete (git archive des
  Tags) als Release-Assets an (Merker aus Phase 34, wird mit v1.5.0
  umgesetzt).
- **D-36-11:** Fremdinstallation: CI-Beweis amd64 auf frischer Nextcloud
  (Muster 06.1-16) PLUS einmalige lokale Docker-Fremdinstallation mit
  Sichtprobe. KEINE Box-Anfahrt, keine Mietkosten.
- **D-36-12 (Bestand, bestaetigt):** Einreichungs-Reihenfolge wie 1.4.2:
  Checkpoint-Plaene (Push/Tag/Submission) seriell auf main ohne Worktree,
  jedes Push-Wort einzeln; nach dem Tag die Tag-Links blob/v1.5.0 in
  docs/store-listing.md und READMEs pruefen, DANN Owner-Abnahme, dann
  2x Submission mit Beleg in docs/store-listing.md.

### Claude's Discretion
- Definition "verschwundener externer Speicher" und die Abgleich-Mechanik
  (Research klaert die Storage-Semantik in oc_storages/oc_filecache).
- Konkrete Grenzwerte der Entpack-/Parserlimits (Kompressionsverhaeltnis,
  Verschachtelungstiefe, Eintragszahl) aus Research ableiten.
- Aufbau der Generator-Helfer und Verteilung auf Testmodule.
- Technik des Quellpaket-Schritts in release.yml (git archive je App oder
  ein Gesamtarchiv).

### Deferred Ideas (OUT OF SCOPE)
- 186 DB-Abfragen je Poll (deferred-items, Bestand vor Phase 34): bleibt
  v1.6-Kandidat, KEIN Umbau in der Haertungsphase; nur neu bewerten, falls
  das Performance-Audit einen Release-Blocker daraus macht.
- Embedding-Wechsel granite r2, #25-Dedup, Reranker, CLIP, whisper.cpp:
  Future-Liste v1.6 in REQUIREMENTS.md, nicht Teil von Phase 36.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HART-06 | Launch-Härtung vor Abgabe: Audit Security/Bugs/Performance (0 CRIT/0 HIGH), bösartige Archive/Mails/OLE-Dateien als Testkorpus, Upgrade-Strecke 1.4.2 -> 1.5.0 in CI, Fremdinstallation | Abschnitte "Bösartiger Korpus: Bestand und Lücken", "Neue Urteilsklasse", "M-32-02", "Upgrade-Strecke", Pitfalls 1 bis 9, Befunde F1 bis F6 |
| REL-05 | Store-Einreichung 1.5.0 beider Apps (Owner-Abnahme Text + Playwright-Runde vorher), Beleg in docs/store-listing.md; Textabnahme: Tschechisch-Grenzeintrag (D-30-06), Dateitypen-Liste, README-Zeilen, Urteils-Wortlaute, Grenzlisten-Frage | Abschnitte "Release-Mechanik", "Store-Texte", Pitfalls 10 bis 14, Befund F1 (Quellpakete) |
</phase_requirements>

## Summary

Phase 36 ist kein Neubau, sondern das Schließen von Lücken in einer schon stark gehärteten Codebasis. Der bösartige Korpus existiert zu großen Teilen bereits: `backend/tests/test_phase31_audit.py` baut ZIP-, Mail-, Word-, Excel- und HEIC-Fälle byte- bzw. sektorweise zur Laufzeit und schickt jeden durch den echten Sandbox-Kindprozess (`ExtractionWorker`, RLIMIT_AS 512 MiB, Frist). `archive.py` zählt das ZIP-Zentralverzeichnis vor `zipfile`, teilt ein Budget über alle Ebenen und kennt Verhältnis-, Tiefen-, Eintrags- und Überlappungsgrenzen. Die Aufgabe der Phase ist daher: (a) die fehlenden Familien ergänzen (XML-Bomben, Bildbomben, Polyglotte, übergroße Einträge, ZIP-basierte Office-Container), (b) eine neue Sammelklasse in die gesamte Verdikt-Kette einziehen (Python-Liste, Store-Liste, PHP-Listen, Wire-Fallbacks, REASON_TEXT, 16 Kataloge, 5 Sprachtabellen, Baumhash-Ratschen), (c) M-32-02 im Abgleich lösen, (d) die Upgrade-Strecke um Ausschlüsse erweitern und (e) die Release-Kette inklusive Quellpflicht sauber fahren.

Drei Befunde aus dieser Recherche sind release-relevant und stehen nicht in CONTEXT.md: **(1) Die GPL-Quellpakete sind falsch versioniert.** pillow-heif wurde per Dependabot (#30, 19.10.) auf 1.8.1 gehoben; dessen `libheif/build_libs.py` lädt x265 **4.3** und libheif **1.23.6**, `scripts/release/corresponding_source.py` und THIRD-PARTY.md nennen aber x265 4.2 und libheif 1.23.4. Ein Release mit diesen Assets würde die falsche korrespondierende Quelle anbieten (verifiziert am sdist 1.8.1). **(2) Der Store führt 1.4.3, nicht 1.4.2** (Tag v1.4.3 auf Zweig `release/1.4.x`, eingereicht 12.10.). `UPGRADE_FROM_TAG` steht noch auf v1.4.2; die eigene Lehre im Workflow-Kommentar sagt, der Wert gehört auf das neueste veröffentlichte Release. **(3) ODF/OOXML öffnen ihr ZIP ohne Vorzählung:** eine 50-MiB-Datei mit 1 Mio. Zentralverzeichnis-Einträgen kostete in der Messung 454 MiB Python-Heap und 32 s allein für `ZipFile()`, knapp unter dem RLIMIT_AS von 512 MiB.

XML-Bomben sind dagegen schon abgefangen, und zwar von den Bibliotheken selbst: libxml2 2.14.6 (im Image) bzw. 2.11.9 (Windows-Wheel) bricht Billion Laughs und Quadratic Blowup mit "Maximum entity amplification factor exceeded" ab, expat 2.8.2 (stdlib, von openpyxl genutzt) mit "limit on input amplification factor". Beides wurde in dieser Session im laufenden Image `findling_backend:1.4.3` gemessen. Was fehlt, ist nur die Zuordnung: heute landet das als `failed(xml_invalid)` bzw. `failed(corrupt)` statt in der neuen Klasse.

**Primary recommendation:** Neue Klasse als `skipped(blocked_malicious)` mit Detailcode in `file_errors.error_class`, in Generation 3 einhängen (1.5.0 ist unveröffentlicht, kein Generationssprung nötig); M-32-02 als Nachlauf eines vollständig gelaufenen Abgleichs mit neuer Lese-Route `GET /storages/gone` und neuer Tabelle `vanished_storages`; Quellpaket-Liste vor dem Tag auf pillow-heif 1.8.1 korrigieren; `UPGRADE_FROM_TAG` erst NACH dem Versionsbump auf v1.4.3 ziehen.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Erkennung bösartiger Dateien, Grenzwerte | Container: Extraktions-Kind (`backend/src/findling/extract/`) | , | Nur das Kind liest Bytes; RLIMIT_AS und Frist liegen dort |
| Klassenliste und Detailcode speichern | Container: `extract/errors.py` + `store/repo.py` (state.db, `file_errors`) | PHP: `FileStateService` (findling_file_state) | Zwei geschlossene Listen, ein Test hält sie gleich |
| Wire-Übersetzung für ältere Companions | Container: `nc/queue.py` (Fallback-Tabellen je Generation) | PHP: `ProfileController::VERDICTS_GENERATION` | Companion und Container werden von AppAPI getrennt aktualisiert |
| Anzeige Label/Abhilfe/Detail | PHP: `AdminViewService::REASON_TEXT`, `php/js/admin.js`, 16 Kataloge | Container: `/diagnose` liefert `errorClass` | Texte leben nur in PHP und Katalogen |
| M-32-02: verschwundene Storages erkennen | Container: `worker/reconcile.py` (Nachlauf nach ROUND_WALKED) | PHP: neue Lese-Route `ReconcileController` (Existenz in `oc_storages`) | Nur PHP sieht `oc_storages`; nur der Container kennt seine Storages |
| M-32-02: Dokumente entfernen | Container: Poller-Löschzweig über `requeue(kind=delete)` | PHP: Queue | "Nichts im Abgleich schreibt den Index" (reconcile.py Kopf) |
| Karenz-Zeitstempel | Container: state.db (neue Tabelle) | , | Abgleich-Lesezeichen leben bewusst im Container |
| Upgrade-Beweis, Fremdinstallation | CI: `.github/workflows/deploy-harp.yml` | lokal: `scripts/dev/compose-harp.yaml` | Bestehender Store-install- und Store-upgrade-Pfad |
| Release-Assets, Quellpflicht | CI: `.github/workflows/release.yml` | `scripts/release/corresponding_source.py` | Unveränderliche Releases: alles im selben `gh release create` |
| Einreichung | CI: `.github/workflows/store-submit.yml` | Owner-Checkpoint | 2x HTTP 201, Beleg in docs/store-listing.md |

## Standard Stack

Keine neuen Pakete. Alles läuft mit dem Bestand (verifiziert in `backend/uv.lock` und im laufenden Image):

### Core (Bestand, relevant für die Härtung)
| Library | Version | Purpose | Schutz, verifiziert |
|---------|---------|---------|---------------------|
| lxml | 6.1.3 (libxml2 2.14.6 im Image, 2.11.9 im Windows-Wheel) | ODF, HTML, python-docx, python-pptx | Entity-Amplification-Grenze greift sofort, auch beim Standard-Parser [VERIFIED: Probe im Image findling_backend:1.4.3] |
| stdlib expat | 2.8.2 (Image), 2.7.5 (Windows) | openpyxl read_only (`xml.etree` iterparse) | "limit on input amplification factor" nach 0,7 bis 1,3 s, 56 bis 66 MiB [VERIFIED: Probe im Image] |
| Pillow | 12.3.0 | Bilder, TIFF | `MAX_IMAGE_PIXELS` = 50 MP gesetzt (image.py:77), `MAX_TEXT_CHUNK` 1 MiB, `MAX_TEXT_MEMORY` 64 MiB, zirkuläre TIFF-IFD-Erkennung in `_seek` [VERIFIED: venv-Introspektion] |
| pillow-heif | 1.8.1 | HEIC | bündelt libheif 1.23.6, x265 4.3, libde265 1.1.3 [VERIFIED: `libheif_info()` und sdist `build_libs.py`] |
| zipfile (stdlib 3.13) | , | ZIP, ODF, OOXML | verweigert überlappende Einträge (CVE-2024-0450), hält Lesen auf deklarierte Größe |
| openpyxl / python-docx / python-pptx | 3.1.5 / 1.2.0 / 1.0.2 | OOXML | eigene Parser, Schutz kommt aus libxml2/expat (oben) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Bibliotheksschutz gegen XML-Bomben | defusedxml | Unnötig: beide Parser-Kerne brechen schon ab (gemessen). Neue Abhängigkeit ohne Gewinn, openpyxl würde sie nur optional nutzen |
| Fehlermeldungstext zur Erkennung | DOCTYPE-Vorprüfung im Part | OOXML/OPC verbietet DTDs in Paketteilen [ASSUMED: ECMA-376 Part 2]; eine Vorprüfung auf `<!DOCTYPE`/`<!ENTITY` im ersten Block ist deterministischer als Meldungsvergleich, kostet aber einen zweiten Lesezugriff je Part |

**Installation:** keine.

## Package Legitimacy Audit

Diese Phase installiert keine externen Pakete. slopcheck nicht ausgeführt, weil nichts zu prüfen ist.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (keine) | , | , | , | , | , | , |

**Packages removed:** none. **Packages flagged:** none.

## Architecture Patterns

### Datenfluss der neuen Urteilsklasse

```
Datei (Nextcloud) --> Poller --> Sandbox-Kind (RLIMIT_AS, Frist)
                                   |
                                   v
                        dispatch.judge(mime) -> Route
                                   |
             +---------------------+----------------------+
             v                     v                      v
     archive.py / office.py   image.py / odf.py      mail.py / cfb.py
     (Signatur erkannt?)      (Bombe erkannt?)       (Tiefe/Zyklus?)
             |  ja                 |  ja                  |  ja
             +----------+----------+----------+-----------+
                        v                     v
   ExtractionOutcome.skipped(BLOCKED_MALICIOUS, detail="zip_ratio")   sonst: bisherige Urteile
                        |
                        v
   Poller._record -> store.record(..., error_class=detail) -> state.db files + file_errors
                        |
                        +--> Ack an PHP: nc/queue._wire_reason(gen) --> gen 3: blocked_malicious
                        |                                              gen 2/None: too_large
                        v
   /diagnose -> errorClass -> AdminViewService -> Admin-Karte (Label, Abhilfe, Detail)
```

### Datenfluss M-32-02

```
Reconcile.run_once (fällig, ruhig)
   |
   v  files.mounts()  (unavailable oder leer -> nichts folgern)
   v  alle gelisteten Mounts bis zum Ende gewalkt (ROUND_WALKED)?  nein -> Ende
   |  ja
   v  known = Storages mit lebenden Zeilen in state.db
   v  absent = known - gelistete Storages
   v  GET /storages/gone?ids=...  (PHP prüft oc_storages; 404/Fehler -> gone = leer)
   |
   +--> gone (kein oc_storages-Eintrag: gelöschter Nutzer, gelöschter Speicher)
   |       -> requeue(alle file_ids, kind=delete) in Bändern zu 200
   |       -> reconcile-/mounts-/vanished-Zeile des Storage entfernen
   |
   +--> absent - gone (Eintrag existiert: abgehängt, Schalter aus, nicht mehr anwendbar)
   |       -> vanished_storages: first_missing_at setzen, falls neu
   |       -> now - first_missing_at >= 30 Tage? -> requeue(delete), Zeilen entfernen
   |
   +--> gelistete Storages: vanished_storages-Zeile löschen (Rückkehr setzt Karenz zurück)
```

### Recommended Structure (neue/geänderte Dateien)
```
backend/src/findling/extract/errors.py     # Reason.BLOCKED_MALICIOUS, skipped(..., detail=)
backend/src/findling/extract/archive.py    # OverLimit trägt optional einen Signaturcode; Vorzählung als öffentliche Hilfe
backend/src/findling/extract/office.py     # Vorzählung des Zentralverzeichnisses, Amplification -> Klasse
backend/src/findling/extract/odf.py        # dito
backend/src/findling/extract/image.py      # Bildbombe -> Klasse (Regel siehe unten)
backend/src/findling/extract/mail.py       # Verschachtelungstiefe deterministisch
backend/src/findling/store/schema.sql      # CREATE TABLE IF NOT EXISTS vanished_storages
backend/src/findling/store/repo.py         # STATE_REASONS, living_storages(), vanished-Methoden, forget_storage()
backend/src/findling/nc/files.py           # gone_storages(ids) -> set[int] | None
backend/src/findling/nc/queue.py           # Fallback-Tabellen gen 2/None
backend/src/findling/worker/reconcile.py   # Nachlauf nach ROUND_WALKED
backend/src/findling/main.py               # httpx/httpcore auf WARNING (D-36-09)
php/lib/Controller/ReconcileController.php # GET /storages/gone
php/lib/Service/FileStateService.php       # beide Listen
php/lib/Service/AdminViewService.php       # REASON_TEXT-Zeile
php/l10n/*.js|*.json (16)                  # neue Schlüssel
docs/l10n-*.md (5), docs/formats.md        # Sprachtabellen, Skip codes
backend/tests/hostile.py                   # NEU: Generatoren (kein Testmodul)
backend/tests/test_phase36_hostile_corpus.py
backend/tests/test_phase36_audit.py
```

### Pattern 1: Signatur statt Grenze
**What:** `archive_limit` bleibt für ehrlich große oder tiefe ZIP-Dateien; `blocked_malicious` nur dort, wo eine Angriffssignatur vorliegt, die kein normales Werkzeug erzeugt.
**Why:** Die Sammelklasse sagt "bösartig". Eine Datei mit 10 001 Einträgen oder drei Ebenen Verschachtelung entsteht auch durch Backups; ein Verhältnis von 1:1000 nur aus Nullen, überlappende Einträge oder `../`-Namen nicht. Außerdem prüft die Upgrade-CI heute `skipped/archive_limit` für die Tiefe-3-Saat (deploy-harp.yml:5700, 6134); die bleibt damit grün.
**Empfehlung der Zuordnung (für den Vorabplan, D-36-04):**

| Familie | Signal | Heute | Empfehlung | Detailcode |
|---|---|---|---|---|
| ZIP | Mitglied >= 1 MiB und Verhältnis > 100 (`ARCHIVE_MAX_RATIO`) | archive_limit | blocked_malicious | `zip_ratio` |
| ZIP | überlappende Einträge (zipfile "Overlapped entries") | archive_limit | blocked_malicious | `zip_overlap` |
| ZIP | Mitgliedsname mit `..`-Segment, absolutem Pfad, Laufwerksbuchstabe oder NUL | indexed (Name bereinigt) | blocked_malicious | `zip_traversal` |
| ZIP | > 10 000 Einträge, Zentralverzeichnis > 8 MiB, Summe > 256 MiB, Tiefe > 2 | archive_limit | archive_limit (bleibt) | , |
| ODF/OOXML | Zentralverzeichnis > 10 000 Einträge (NEU, siehe F3) | out_of_memory oder timeout möglich | blocked_malicious | `package_entries` |
| ODF/OOXML/HTML-Mail | XMLSyntaxError/ParseError mit Amplification-Meldung | xml_invalid bzw. corrupt | blocked_malicious | `xml_entities` |
| Bild | Pillow `DecompressionBombError` (> 100 MP) UND Pixel je Dateibyte > 1000 | too_large | blocked_malicious | `image_pixels` |
| Bild | > 100 MP ohne das Verhältnis (z. B. echte 102-MP-Mittelformataufnahme) | too_large | too_large (bleibt) | , |
| Mail | message/rfc822-Verschachtelung > 32 Ebenen | failed(corrupt) | blocked_malicious | `mail_nesting` |
| OLE/CFB | Zyklus in FAT-, MiniFAT-, DIFAT- oder Verzeichniskette | corrupt bzw. benanntes Urteil | blocked_malicious | `cfb_cycle` |
| OLE/CFB | sonstige Strukturfehler | corrupt | corrupt (bleibt) | , |
| Polyglott | PDF+ZIP, GIFAR, JPEG+ZIP | Leser je Mimetype | KEINE eigene Klasse; Test verlangt nur benanntes Urteil | , |
| Übergroßer Einzeleintrag | Mitglied > max_file_bytes / Part > 64 MiB | Name only / too_large | bleibt | , |

Die Schwellen 32 (Mailtiefe) und 1000 (Pixel je Byte) sind [ASSUMED] Abwägungen, keine Messungen: ein weißer 1-bit-Scan in CCITT G4 erreicht ohne Weiteres mehrere tausend Pixel je Byte, deshalb greift die Regel erst oberhalb der Pillow-Grenze von 100 MP.

### Pattern 2: Detail ohne Inhalt
**What:** Der Detailcode reist im bestehenden Feld `error_class` (state.db `file_errors`, `/diagnose` `errorClass`, Admin-Karte). Form `[A-Za-z0-9_.]{1,200}` ist auf beiden Seiten Pflicht (`repo.py:555`, `AdminViewService::ERROR_CLASS_PATTERN`).
**Wichtig:** `ExtractionOutcome.skipped()` nimmt heute kein `detail` an (errors.py:247); die Methode bekommt einen Schlüsselwort-Parameter. `Poller` reicht `outcome.detail` schon unabhängig vom Zustand weiter (poller.py:2160). `php/js/admin.js:751` sagt im Kommentar, die Fehlerklasse gebe es nur bei `failed`; die Anzeige selbst ist aber nur an `errorClass !== ''` gebunden (admin.js:810). Das Label "Error class: %s" passt für einen Signaturcode schlecht: eigenes Label im Vorabplan ("Detail: %s" o. ä.).

### Pattern 3: Signaturcode ohne Meldungstext
Die Erkennung von Amplification und Überlappung braucht den Meldungstext der Ausnahme. Das Muster existiert: `archive._is_overlap` vergleicht `str(error).startswith(...)`, loggt nie. Für XML: `"amplification" in str(error)`; der Text wird nie gespeichert und nie geloggt (T-02-56). Ein Test baut die echten Ausnahmen (Muster `test_extract_errors.py`), damit eine geänderte Bibliotheksmeldung rot wird statt still auf `xml_invalid` zurückzufallen.

### Anti-Patterns to Avoid
- **Neue Verdikt-Generation 4:** unnötig. Generation 3 ist mit 1.5.0 noch nicht veröffentlicht (Store: 1.4.3). Die neue Klasse gehört in Generation 3, wie `archive_limit` (31-02).
- **`blocked_malicious` unter `failed`:** "failed" zählt die Statusseite als Fehler und heißt "wir wollten und konnten nicht". Eine verweigerte Datei ist eine Entscheidung; `skipped` passt, wie bei `archive_limit`.
- **Verschwundene Storages per `files.page()` walken:** `IFileAccess::getByAncestorInStorage` wirft "Could not fetch storage root", wenn der Root fehlt (Core `FileAccess.php:117`); die Route antwortet 500, der Container liest `unavailable` und beendet JEDEN Abgleich mit `ROUND_UNAVAILABLE`. Das würde den Abgleich dauerhaft blockieren.
- **Löschen ohne Bestätigung durch PHP:** eine leere oder unvollständige Mountliste (Migration, DB-Störung) darf nie zu Sofortlöschung führen. Sofort nur bei bestätigtem fehlenden `oc_storages`-Eintrag, sonst Karenz.

## Bösartiger Korpus: Bestand und Lücken

### Was es schon gibt (nicht neu bauen)
- `backend/tests/test_phase31_audit.py`: `build_zip`/`Member` (APPNOTE-Records), 17 ZIP-Fälle (lügende Größen, Überlappung, 10 001 Einträge, Tiefe 3, Name 64 KiB, `..\\..\\boese/../x\x00`), 12 Mail-Fälle (1000-fach verschachtelt, 1-MiB-Header, 10 000 Parameter, Bidi-/Traversal-Dateiname), CFB-Fälle über einen eigenen Sektorschreiber (DIFAT-, MiniFAT-, Verzeichnis-, FAT-Zyklen), Excel-BIFF8, HEIC box-weise, Log-Sonde mit Positivkontrolle, Wire-Codes je Generation.
- `backend/tests/conftest.py:578-719`: `cfb_entry`, `build_cfb`, `cfb_with_difat`.
- Fixture `worker` (module scope) mit `ExtractionWorker(max_files=1000, timeout_seconds=60)` und `_named_and_quick` (benanntes Urteil, Kind lebt, < 30 s).

### Was fehlt (D-36-02)
| Familie | Fall (Generator) | Erwartung |
|---|---|---|
| XML-Bombe ODT | `content.xml` mit 10 Ebenen x 10 Entities | blocked_malicious/xml_entities, < 1 s |
| XML-Bombe DOCX/PPTX | `word/document.xml` bzw. Folie mit Bombe | dito (python-docx/pptx parsen mit lxml) |
| XML-Bombe XLSX | Blatt mit Bombe (expat-Weg, 1,3 s, 66 MiB) | dito |
| Quadratic Blowup | eine 20-KB-Entity 20 000-mal | dito |
| Tiefe XML-Verschachtelung | 10 000 geschachtelte Elemente | xml_invalid (libxml2-Tiefengrenze 256 ohne huge_tree) [ASSUMED] |
| ZIP-basierter Container mit 1 Mio. Einträgen | `.docx`/`.odt`/`.xlsx` aus reinen Zentralverzeichnis-Records (50 MiB) | blocked_malicious/package_entries, ohne `ZipFile()` |
| PNG-Bombe | IHDR 20 000 x 20 000, IDAT aus deflate-Nullen | blocked_malicious/image_pixels |
| PNG-Textbombe | zTXt > 1 MiB dekomprimiert | benanntes Urteil (Pillow `MAX_TEXT_CHUNK` greift) |
| TIFF-IFD-Zyklus | IFD zeigt auf sich selbst | benanntes Urteil, kein Hängen (Pillow prüft `_frame_pos`) |
| TIFF mit 100 000 IFDs | Kette kleiner Seiten | benanntes Urteil unter Frist (OCR-Seitendeckel) |
| Polyglott | PDF mit angehängtem ZIP als `.pdf` und als `.zip`; JPEG+ZIP | je ein benanntes Urteil, kein Absturz |
| Übergroßer Einzeleintrag | ZIP-Mitglied deklariert > 50 MiB | Name im Text, Datei indexiert |
| ZIP-Traversal | `../x.txt`, `/etc/x`, `C:\\x`, NUL | blocked_malicious/zip_traversal, kein Schreibzugriff unter Mitgliedsnamen |
| Mail-Tiefe | rfc822 33-fach | blocked_malicious/mail_nesting |

### Generator-Aufbau (Claude's Discretion, Empfehlung)
- Neues Hilfsmodul `backend/tests/hostile.py` (kein `test_`-Präfix, pytest sammelt es nicht), Import per `from hostile import ...` wie heute `from conftest import ...`. `build_zip`, `Member`, `_same_offset_twice`, `_with_end` dorthin verschieben und in `test_phase31_audit.py` importieren, damit es eine Kopie gibt.
- Jeder Generator ist rein und deterministisch (keine Zeit, kein Zufall ohne Seed), liefert `bytes`, Bomben deklarieren ihre Größe statt sie zu tragen (Muster 31-15: "Bombs declare their size and do not carry it").
- Testmodul `test_phase36_hostile_corpus.py`: eine Fall-Tabelle je Familie wie `_ZIP_CASES` (Name -> Generator, Urteil, Detailcode, Befund-ID), parametrisiert, durch die module-scope-Fixture `worker`.
- "Ohne Speicherüberlauf" belegt die Linux-CI (`python.yml`, ubuntu): dort gilt RLIMIT_AS, ein Überlauf würde `failed(out_of_memory)` statt des erwarteten Urteils liefern. Auf Windows lokal gibt es kein RLIMIT_AS; die Fälle laufen dort trotzdem, beweisen aber nur Urteil und Laufzeit.
- Nur ASCII im Testcode, Umlaute als Escapes (Konvention der Audit-Module).

## Neue Urteilsklasse: alles, was nachzieht

Vorlage ist Commit `aa498caf` (31-02, archive_limit), der 37 Dateien berührte. Pflichtliste:

| # | Stelle | Was |
|---|---|---|
| 1 | `extract/errors.py` | `Reason.BLOCKED_MALICIOUS`, in `STATE_REASONS[SKIPPED]`; `skipped(reason, *, detail=None)`; Docstring zu `detail` erweitern |
| 2 | `store/repo.py:301` | gleiche Zeile in `STATE_REASONS` (Test vergleicht beide Listen) |
| 3 | `nc/queue.py:170-196` | `_SKIPPED_FALLBACK_BY_GENERATION[2]` und `[None]`: `blocked_malicious -> too_large`; `_FAILED_FALLBACK_BY_GENERATION[2]`/`[None]`: `-> corrupt`; Kommentar zu Generation 3 |
| 4 | `php/lib/Service/FileStateService.php:119,171` | beide Listen |
| 5 | `php/lib/Controller/ProfileController.php:44-52` | Docblock zu Generation 3 (Konstante bleibt 3) |
| 6 | `php/lib/Service/AdminViewService.php:527` | REASON_TEXT-Zeile (Label, Abhilfe); ggf. `archive_limit`-Abhilfe ohne "too densely packed" |
| 7 | `php/js/admin.js:750-810` | Label des Detailcodes; Kommentar "only for a failed file" |
| 8 | 16 Kataloge `php/l10n/*.js|*.json` | neue Schlüssel; `test_admin_ui_contract.py:3680` Zahl 348 anheben mit Begründungsabsatz |
| 9 | 5 Sprachtabellen `docs/l10n-{dutch,french,italian,portuguese,spanish}.md` | Zeilen je Schlüssel |
| 10 | `docs/formats.md` | Abschnitt "Skip codes" |
| 11 | `test_phase31_audit.py:1075-1100` | Liste "codes each generation added" um den neuen Code in Generation 3 |
| 12 | `test_extract_errors.py`, `test_queue_client.py`, `php/tests/Unit/ProfileControllerTest.php` | Drift- und Fallback-Fälle |
| 13 | `test_measurement_scripts.py:1014,2088` | `PHP_TREE_HASH_TODAY` und `PACKAGE_TREE_HASH_TODAY` neu messen (Ratsche: neuer Wert muss sich vom alten unterscheiden) |
| 14 | `scripts/ci/make_upgrade_seed_formats.py`, `deploy-harp.yml` | nur falls eine Saat ihre Klasse wechselt (bei Pattern-1-Zuordnung: nein) |

**Vokabelregel (E-H2):** der Wortstamm "Archiv" ist in deutscher Prosa und in docs/store-listing.md gesperrt; Wortlaute sagen "ZIP-Datei". Gilt für alle neuen Labels und Abhilfen.

## M-32-02: Semantik und Mechanik

### Was Nextcloud beim Löschen tut (verifiziert im Core NC 34.0.3 der Dev-Instanz)
- **Nutzer löschen:** `OC\Authentication\Listeners\UserDeletedFilesCleanupListener` merkt sich bei `BeforeUserDeletedEvent` den Home-Storage und ruft bei `UserDeletedEvent` `$storage->rmdir('')` und `Cache::clear()`; `Cache::clear()` löscht alle `oc_filecache`-Zeilen des Storage UND die `oc_storages`-Zeile (`Cache.php:877-887`). `UserMountCacheListener` entfernt die `oc_mounts`-Zeilen (`removeUserMounts` auf `postDelete`). [VERIFIED: Quelltext im Container findling-nextcloud]
- **Externen Speicher löschen (files_external):** `StoragesService::removeStorage` ruft `Storage::cleanByMountId`, das `oc_filecache`, `oc_storages` und `oc_mounts` der Speicher löscht (`StoragesService.php:416-433`, `Storage.php:162`). [VERIFIED]
- **Speicher abgehängt, Nutzer nicht mehr anwendbar, Findling-Schalter (Team-Ordner/externe Speicher) aus:** `oc_storages` bleibt, nur die Mountliste von Findling enthält ihn nicht mehr (`StorageService::providers()`, `getDistinctMounts`). [VERIFIED: Code]

### Definition (Empfehlung)
- **gelöscht** = Storage hat lebende Zeilen in state.db, steht nicht in der Mountliste, und `oc_storages` kennt die numerische ID nicht mehr -> Löschaufträge im selben Nachlauf ("beim nächsten Abgleich").
- **verschwunden** = Storage nicht in der Mountliste, `oc_storages`-Eintrag existiert -> Erstsichtung stempeln, nach 30 Tagen Löschaufträge. Rückkehr in die Mountliste löscht den Stempel.
- Ein abgeschalteter Findling-Schalter fällt damit unter "verschwunden" (30 Tage). Ob das gewollt ist, ist eine Owner-Frage (siehe Open Questions 2).

### Neue Lese-Route (PHP)
`GET /ocs/v2.php/apps/findling/storages/gone?ids[]=...` in `ReconcileController`, gleiche Attribut-Trias und `rejectForeignCaller()` wie `mounts()`, Liste per `intList` begrenzt (QueueController-Muster, 256), Antwort `{"gone": [ids ohne oc_storages-Zeile]}`, eine Abfrage `SELECT numeric_id FROM storages WHERE numeric_id IN (...)`. GET braucht keinen Eintrag in `OCS_WRITE_ALLOWLIST` (ReconcileController-Docblock). Ein 1.4.x-Companion antwortet 404: der Container behandelt jede Nicht-200-Antwort als "unbekannt" und folgert nur die Karenz.

### Persistenz der Karenz
Neue Tabelle in `store/schema.sql`, `IF NOT EXISTS` wie `file_errors` (D-29-09), kein Sprung von `store.repo.SCHEMA_VERSION` ("2"):
```sql
CREATE TABLE IF NOT EXISTS vanished_storages (
    storage_id       INTEGER PRIMARY KEY,
    first_missing_at INTEGER NOT NULL      -- epoch seconds of the first round that missed it
);
```
Die Phase-30-Sperre ("spätere v1.5-Phasen ändern weder Schema noch Indexmarken") betrifft das Tantivy-Schema `config.SCHEMA_VERSION = 3` und die Indexmarken; eine absorbierbare state.db-Tabelle ist davon nicht erfasst (Präzedenz `file_errors`). Rückdatierung im Test (D-36-05):
```sql
UPDATE vanished_storages SET first_missing_at = first_missing_at - 31 * 86400 WHERE storage_id = ?;
```
Konstante fest im Code, z. B. `VANISHED_STORAGE_GRACE_SECONDS: Final = 30 * 86_400` in `reconcile.py`, kein `FINDLING_*`-Schalter.

### Mitzuräumen (latenter Befund F4)
`_RECONCILE_STATE_SQL` (repo.py:613) zählt `unfinished` über alle Zeilen der Tabelle `reconcile`. Wurde ein Walk auf Storage X unterbrochen (`after_file_id > 0`) und verschwindet X danach, bleibt `unfinished > 0` für immer; `_is_due` antwortet dann bei jedem Takt (300 s) True und jede Runde walkt alle Mounts von vorn. Das Aufräumen eines Storage muss deshalb auch seine `reconcile`- und `mounts`-Zeile löschen; zusätzlich Zeilen ohne lebende Dokumente und ohne Mount. [MEDIUM: aus Code gelesen, nicht gefahren; Regressionstest vorsehen]

### Live-Lage auf der Dev-Instanz 8090 (gelesen 20.10.)
| storage_id | oc_storages | in oc_mounts | lebende Dokumente | erwartetes Verhalten |
|---|---|---|---|---|
| 2, 3, 4 | home::admin, home::testuser, home::kollegin | ja | 55, 371, 49 | bleiben (Positivkontrolle) |
| 7 | sftp::u1@findling-sftp//upload/ | nein | 30 | Karenz-Stempel, nach Rückdatierung Löschung |
| 14 | fehlt (carol, gelöscht in 32-08) | nein | 1 (Datei 2970) | Löschung im ersten Abgleich |
| 15 | fehlt | nein | 49 | Löschung im ersten Abgleich |

Die `reconcile`-Tabelle trägt Zeilen für 12 und 13 ohne Dokumente: Kandidaten für das Aufräumen aus F4. Der Live-Beleg braucht daher keine künstliche Saat; vor dem Lauf `state.db` sichern (Muster 35-08: Protokoll und Rückbau).

### CI-Integrationstest (D-36-06)
Heimat: Job `reconcile-and-dach` in `.github/workflows/integration.yml:2365ff.`, der bereits genau einen Zyklus per `Reconcile().run_once()` gegen eine echte Nextcloud fährt. Ergänzen: Nutzer anlegen, Datei indexieren, `occ user:delete`, ein Zyklus -> Dokument weg, Kontrollnutzer bleibt; files_external-Lokalspeicher (`occ files_external:create`) indexieren, Findling-Schalter "externe Speicher" aus, ein Zyklus -> Stempel, Dokument bleibt; SQL-Rückdatierung, ein Zyklus -> Dokument weg; zweiter verschwundener Speicher ohne Rückdatierung bleibt (Gegenprobe).

## Upgrade-Strecke

### Bestand (deploy-harp.yml)
- `UPGRADE_FROM_TAG: v1.4.2` (Zeile 148), Schritte "Store upgrade 0" bis "7" (Zeilen 3370 bis ca. 7200), Matrixzeile `stable34` + `ubuntu-24.04` + `RELEASE_TAG == ''`.
- Belegt heute: Nachholweg (`recheck_1_5_0`, neue Typen per Wort gefunden, Wire-Substitute), Bestand ohne Umbau unter Werkssprachen (Marken, Zähler, Vektoren unverändert), cs-Umbau hin und zurück (Schritte 6, 7), ZIP-Bombe `skipped/archive_limit`.
- **Nicht belegt: Ausschlüsse.** Weder Präfix-Ausschlüsse von 1.4.x (`appconfig exclusions`) noch Muster von 1.5 (`exclusionPatterns`, `ExclusionService::FIELD_PATTERNS`) kommen in der Strecke vor (grep über Schritte 3370 bis 7237). Erfolgskriterium 2 nennt sie ausdrücklich.

### Ergänzung Ausschlüsse (Empfehlung)
Unter der alten Version: Präfix `Ausschluss36` setzen (Format von 1.4.x, `getValueArray` auf `SettingsService::KEY_EXCLUSIONS`), `/Ausschluss36/a.txt` und Kontrolldatei mit eigenem Wort anlegen, abarbeiten. Nach dem Upgrade: Ausschlussdatei weiter nicht gefunden, Kontrolle gefunden, Präfixliste unverändert lesbar; dann ein Muster der 1.5 (z. B. `*.geheim36`) setzen, Abgleich fällig machen, Treffer verschwindet (D-33-01), Kontrolle bleibt.

### Versionssprung und ERROR_UP_TO_DATE
"Store upgrade 4" (Zeilen 5308 bis 5348) hat zwei Zweige: Versionen gleich -> Dateitausch ohne Sprung (läuft heute, Baum und Tag tragen 1.4.2); Versionen verschieden -> `installed_version` MUSS danach der neuen entsprechen, sonst rot. Zwei Folgen:
1. Der echte Beweis 1.4.x -> 1.5.0 entsteht erst mit dem Bump-Commit (beide `info.xml` `<version>1.5.0</version>`, Backend `<image-tag>1.5.0</image-tag>`, CHANGELOG `[1.5.0]`). Der Bump muss VOR dem Upgrade-Nachweis auf main liegen; das Image 1.5.0 muss dafür nicht im Registry stehen (Schritt nutzt `info-citest.xml`).
2. Wird `UPGRADE_FROM_TAG` auf v1.4.3 gezogen, solange der Baum noch 1.4.2 sagt, liegt ein ÄLTERER Companion auf der Platte als installiert; `occ upgrade` macht nichts, Zweig 1 meldet rot. Reihenfolge daher: erst Bump auf 1.5.0, dann (im selben oder einem späteren Commit) `UPGRADE_FROM_TAG: v1.4.3` samt Kommentarabsatz nach dem Muster der Zeilen 89 bis 147.

### v1.4.3 statt v1.4.2 (Befund F2)
v1.4.3 (12.10., Zweig `release/1.4.x`, Commit 0f088d05) ist der Stand im Store; Unterschied zu v1.4.2 nur Scroll-Fix in PHP plus Versionsstellen. Assets und Image `findling_backend:1.4.3` (amd64+arm64) existieren (docs/store-listing.md:2388-2392; Image läuft lokal als `nc_app_findling_backend`). Die Schritte "2b" usw. nennen "1.4.2" teils wörtlich in Namen und Meldungen; mitziehen. ROADMAP und REQUIREMENTS sagen 1.4.2; Owner-Bestätigung über den Plan einholen (Open Questions 1).

## Release-Mechanik

### release.yml (D-36-10)
- Releases sind unveränderlich (`isImmutable: true`, belegt in 31-01); ein späteres `gh release upload` endet mit HTTP 422. Alle Assets müssen im einen `gh release create` (release.yml:503-515) stehen, ebenso im Artefakt-Upload (480-490) für die Probe ohne Release.
- Pflicht laut Checkliste docs/store-listing.md:2316-2363: vor dem Release-Schritt `python3 scripts/release/corresponding_source.py fetch dist/source`, dann die vier Dateien `dist/source/pillow_heif-*.tar.gz`, `x265_*.tar.gz`, `libde265-*.tar.gz`, `libheif-*.tar.gz` mitgeben; danach Prüfschritt `gh release download ... && corresponding_source.py --verify-only`.
- D-36-10 wörtlich: zusätzlich ein `git archive` des Tags. Empfehlung: ein Gesamtarchiv `findling-<version>-source.tar.gz` mit `git archive --format=tar.gz --prefix=findling-<version>/ "${GITHUB_REF_NAME}"` (deterministisch für denselben Commit und dieselbe git-Version [ASSUMED]), `actions/checkout` mit `fetch-depth: 0` oder Tag-Fetch nötig, falls der Checkout flach ist.
- `fetch` lädt aus vier externen Quellen (PyPI, GitHub Releases von Multicorewareinc/x265 und strukturag). Fällt eine aus, scheitert das Release. Rückfall vorsehen: Assets eines Spiegel-Pre-Releases herunterladen und mit `--verify-only` prüfen.

### Befund F1: Quellpaket-Liste veraltet (vor dem Tag beheben)
| Archiv | corresponding_source.py / THIRD-PARTY.md | pillow-heif 1.8.1 `libheif/build_libs.py` |
|---|---|---|
| pillow_heif | 1.8.1 | 1.8.1 |
| x265 | **4.2** | **4.3** (`.../x265/releases/download/4.3/x265_4.3.tar.gz`) |
| libde265 | 1.1.3 | 1.1.3 |
| libheif | **1.23.4** | **1.23.6** (`.../libheif/releases/download/v1.23.6/libheif-1.23.6.tar.gz`) |

[VERIFIED: sdist pillow_heif-1.8.1 von files.pythonhosted.org in dieser Session gelesen; Windows-Wheel meldet `libheif 1.23.6`, `x265 4.3+1`]. Zu tun: Liste und Hashes neu, THIRD-PARTY.md-Tabelle, im gebauten Linux-Image `LICENSES_bundled.txt` des Wheels gegenprüfen, `test_corresponding_source.py`/`test_third_party_versions.py` so schärfen, dass ein Pin-Bump ohne Liste rot wird (Dependabot #30 kam durch). Der Spiegel `source-1.5-dev.2` trägt noch pillow_heif 1.8.0; für das `:dev`-Image einen neuen Spiegel `source-1.5-dev.3` per `publish --tag` anlegen (Owner-Wort, weil öffentlich).

### Logging (D-36-09)
`main.py:924` `logging.basicConfig(level=log_level().upper())` im Lifespan. Direkt danach: wenn `log_level() != "debug"`, `logging.getLogger("httpx").setLevel(logging.WARNING)` und `logging.getLogger("httpcore").setLevel(logging.WARNING)`. Damit bleibt `FINDLING_LOG_LEVEL=debug` der Weg zurück. Test: caplog nach einem simulierten OCS-Abruf ohne INFO-Zeile mit `userId`; mit debug vorhanden (Positivkontrolle).

### Store-Texte und Tag-Links
- `blob/v1.5.0` steht heute nur in den Phase-34-Entwürfen (docs/store-listing.md:2299-2301), noch nicht in `info.xml` oder READMEs. Nach dem Übernehmen in die sechs Beschreibungen erst nach dem Tag per `curl -sI` auf 200 prüfen.
- D-36-08: Der "half of the box"-Satz steht SECHSMAL: `backend/appinfo/info.xml:113,144,175` UND `php/appinfo/info.xml:67,101,135`. CONTEXT nennt nur backend:113.
- Phase 35 (Ähnliche Dokumente) hat weder Store-Entwurf noch CHANGELOG-Eintrag unter `[Unreleased]`. Gehört in die Gesamtabnahme REL-05 (Open Questions 4).
- Teil Phase 31 ist abgenommen (12.10.), Teil Phase 30 und der Gesamttext sind offen; die Dateitypen-Liste wird per Gate zeichengleich gegen den Entwurf gehalten (`test_every_file_type_list_stands_in_the_draft_of_phase_31_character_for_character`).

### Reihenfolge der Checkpoint-Pläne (D-36-12, konkret)
1. Wortlaut-Vorabplan (neue Klasse, `archive_limit`-Abhilfe, Detail-Label, D-36-08, Ähnlich-Zeile) -> Owner-Abnahme.
2. Bau, Korpus, M-32-02, Logging, Quellliste; Audit 0 CRIT/HIGH.
3. Bump-Commit 1.5.0 + `UPGRADE_FROM_TAG: v1.4.3` -> Push (Owner-Wort) -> alle Workflows grün inkl. Upgrade-Zweig 1.
4. Tag v1.5.0 (Owner-Wort) -> release.yml (Pakete, Signaturen, Quellpakete, git archive) + docker.yml (Image 1.5.0 amd64/arm64) -> Assets und Manifest anonym prüfen.
5. Tag-Links prüfen; `deploy-harp.yml` per `workflow_dispatch release_tag=v1.5.0` (Fremdinstallation aus den echten Assets, amd64 und arm64) + lokale Docker-Fremdinstallation (compose-harp, Port 8096 wie 1.4.3).
6. Gemeinsame Playwright-Abnahme Store-Text + Produkt mit echten Testdateien.
7. `store-submit.yml --ref main -f tag=v1.5.0` -> 2x HTTP 201 -> Beleg in docs/store-listing.md, Katalog-Gegenprobe (Cache-Verzug wie bei 1.4.3 einplanen).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Billion Laughs / Quadratic Blowup | eigenen Entity-Zähler oder defusedxml | libxml2/expat-Amplification-Grenze (gemessen) + Meldungsvergleich | schon in beiden Parser-Kernen, sofortiger Abbruch |
| ZIP-Zentralverzeichnis zählen | zweiten Parser für ODF/OOXML | `archive.count_central_directory` / `_central_directory` öffentlich machen und wiederverwenden | CPython-genaue Nachbildung existiert und ist getestet |
| Dekompressionsbombe Bild | eigenen PNG/TIFF-Header-Parser | `Image.MAX_IMAGE_PIXELS` + `DecompressionBombError` + `_implausible` | Pillow liest nur Header vor dem Fehler |
| Löschen von Dokumenten verschwundener Storages | Indexschreiber im Abgleich | `queue.requeue(ids, kind=KIND_DELETE)` in Bändern `REQUEUE_BAND` | ein Indexschreiber (Tantivy-Lock), Löschpfad existiert einmal |
| Storage-Existenz prüfen | `files.page()` auf fremden Root | neue Lese-Route gegen `oc_storages` | `page()` wirft 500 und blockiert den Abgleich |
| Korrespondierende Quelle | eigene Download-Logik in YAML | `corresponding_source.py fetch` / `--verify-only` | SHA-256-Prüfung, getestet |
| Generationsfallback | neue Generation 4 | Gen-3-Eintrag + Fallback-Tabellen 2/None | 1.5.0 unveröffentlicht |

**Key insight:** fast jede Abwehr existiert schon in Bibliothek oder Code; die Arbeit ist Zuordnung, Wiederverwendung und Nachweis, nicht neue Parser.

## Common Pitfalls

### Pitfall 1: Klasse ohne Fallback erreicht einen 1.4.x-Companion
**What goes wrong:** ein 1.4.3-Companion verweigert die GANZE Skip-Liste mit 400, sobald ein Code unbekannt ist (QueueController), der Batch kreist.
**How to avoid:** Fallback-Tabellen für Generation 2 und None; der Test "no code reaches a companion that does not know it" (31-15) muss den Code kennen.

### Pitfall 2: Detail nur bei failed
**What goes wrong:** `ExtractionOutcome.skipped()` verwirft den Detailcode, die Admin-Karte zeigt nichts.
**How to avoid:** `detail`-Parameter für `skipped`; `__post_init__`-Regeln unverändert; Test, der ein skipped-Urteil mit Detail bis `/diagnose` verfolgt.

### Pitfall 3: Meldungstext in Log oder DB
**What goes wrong:** die Amplification-Meldung zitiert Zeile/Spalte, andere Meldungen Dateinamen (T-02-56).
**How to avoid:** nur vergleichen, nie speichern; Log-Sonde aus 31-15 auf die neuen Fälle erweitern (SECRETS um Namen der neuen Generatoren).

### Pitfall 4: ODF/OOXML-Vorzählung bricht legitime große Dateien
**What goes wrong:** zu niedrige Eintragsgrenze verweigert echte PPTX mit vielen Medien.
**How to avoid:** dieselbe Grenze wie ZIP (10 000), kein Verhältnis-Test für Office-Container (XML komprimiert legitim stark), Gegenprobe mit großer echter PPTX/XLSX aus `testdata/`.

### Pitfall 5: Abgleich folgert aus einer leeren oder gestörten Mountliste
**What goes wrong:** Sofortlöschung eines ganzen Index.
**How to avoid:** Nachlauf nur nach `ROUND_WALKED`, nie bei leerer Liste; Sofortlöschung nur mit bestätigtem `gone` aus PHP; Route-Fehler = keine Folgerung.

### Pitfall 6: Rückkehrender Speicher behält alten Stempel
**How to avoid:** jeder gelistete Storage löscht seine `vanished_storages`-Zeile in derselben Runde; Test "verschwindet 20 Tage, kommt zurück, verschwindet erneut -> Karenz beginnt neu".

### Pitfall 7: Ewig "unfinished" (F4)
Siehe M-32-02. Test: `reconcile`-Zeile mit `after_file_id > 0` für einen Storage, der nicht gelistet ist; nach dem Nachlauf ist `reconcile_state().unfinished == 0`.

### Pitfall 8: UPGRADE_FROM_TAG vor dem Bump gezogen
Siehe Upgrade-Strecke. Folge: Zweig 1 von "Store upgrade 4" rot. Bump zuerst.

### Pitfall 9: Windows-Lauf beweist keinen Speicherdeckel
Lokal fehlt RLIMIT_AS; "ohne Speicherüberlauf" gilt erst mit grünem `python.yml` auf ubuntu bzw. im Image.

### Pitfall 10: Quellpakete nachträglich anhängen
Unmöglich bei unveränderlichen Releases. Alles in `gh release create`; vor dem Tag per `workflow_dispatch` (create_release=false) proben, Artefakt prüfen.

### Pitfall 11: Falsche korrespondierende Quelle (F1)
Vor dem Tag beheben; sonst wäre v1.5.0 unveränderlich mit falschen Quellpaketen veröffentlicht und nur ein 1.5.1 könnte es heilen.

### Pitfall 12: Satz nur in einer info.xml geändert (D-36-08)
Sechs Stellen in zwei Dateien; die Beschreibungen beider Apps tragen denselben Text.

### Pitfall 13: Vokabelregel
"Archiv" in deutscher Prosa und in docs/store-listing.md gesperrt; Gate prüft.

### Pitfall 14: Store-Text nach dem Tag nicht mehr änderbar
Der Text reist mit dem Release. Wortlaut-Abnahme (Vorabplan) VOR dem Bump-Commit; die Playwright-Runde nach dem Tag ist Bestätigung. Ein Einwand dort heißt 1.5.1.

## Code Examples

### Signaturcode an OverLimit (archive.py, Skizze)
```python
class OverLimit(Exception):
    """A limit of D-31-07 is reached; skipped(archive_limit) or, with a signature, skipped(blocked_malicious)."""

    def __init__(self, signature: str | None = None) -> None:
        super().__init__(signature or "limit")
        self.signature = signature  # a code out of the closed detail list, never a name


# in extract_zip
except OverLimit as over:
    if over.signature is not None:
        return ExtractionOutcome.skipped(Reason.BLOCKED_MALICIOUS, detail=over.signature)
    return ExtractionOutcome.skipped(Reason.ARCHIVE_LIMIT)
```

### Amplification erkennen, ohne die Meldung zu behalten (odf.py/office.py)
```python
# Source: Muster archive._is_overlap; Meldungen gemessen in findling_backend:1.4.3
_AMPLIFICATION = ("amplification",)  # libxml2: "Maximum entity amplification factor exceeded"
                                     # expat:   "limit on input amplification factor ... breached"

def _is_entity_bomb(error: Exception) -> bool:
    """Compared, never logged: the message quotes line and column of the file."""
    return any(word in str(error) for word in _AMPLIFICATION)
```

### Nachlauf im Abgleich (reconcile.py, Skizze)
```python
VANISHED_STORAGE_GRACE_SECONDS: Final = 30 * 86_400  # fixed, D-36-05

async def _sweep_vanished(self, store: Store, files: FileList, queue: DocumentQueue, listed: set[int]) -> None:
    if not listed:
        return  # an empty mount list is never evidence (Pitfall 5)
    known = await asyncio.to_thread(store.living_storages)
    absent = sorted(known - listed)
    gone = await files.gone_storages(absent) if absent else set()  # None on 404/error -> set()
    now = int(self._clock())
    await asyncio.to_thread(store.clear_vanished, listed)
    for storage in absent:
        if storage in (gone or set()):
            due = True
        else:
            first = await asyncio.to_thread(store.mark_vanished, storage, now)  # returns first_missing_at
            due = now - first >= VANISHED_STORAGE_GRACE_SECONDS
        if due:
            ids = await asyncio.to_thread(store.living_file_ids, storage)
            if await self._hand_over(queue, (), ids):
                await asyncio.to_thread(store.forget_storage, storage)  # reconcile, mounts, vanished rows
```

### Logging (main.py, nach basicConfig)
```python
if log_level() != "debug":
    # L-35-06: httpx names the OCS path with fileid and userId at INFO.
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)
```

## Audit-Rahmen (Wiederverwendung)

- Muster: `NN-AUDIT.md` mit YAML-Kopf (`findings`, `fixed`, `still_open`), Abschnitte Security/Bugs/Performance, Befund-IDs `C/H/M/L-36-NN`, Owner-Regel 20.10.: auch LOW wird behandelt; Probes als Regressionstests in `test_phase36_audit.py` (Docker-Proben überspringbar, Instanzproben per Umgebungsvariablen `FINDLING_AUDIT36_*` wie 34).
- Umfang für die Launch-Härtung: nicht nur der Phasen-Diff, sondern Milestone-weit `git diff v1.4.2..HEAD` (bzw. Merge-Basis von v1.4.3) über `backend/src`, `php/lib`, Workflows; alle `test_phase3*_audit.py` erneut grün; offene LOWs aus 32 (L-32-01, 03, 04, 05, 07) und 35 (L-35-02) neu bewerten.
- Bereits jetzt bekannte Befunde dieser Recherche: F1 (Quellpakete, Einstufung HIGH als Lizenzpflicht vor Release), F2 (Upgrade-Ausgangsversion), F3 (ODF/OOXML-Vorzählung, MEDIUM), F4 (ewig unfinished, MEDIUM), F5 (Ausschlüsse fehlen in der Upgrade-Strecke), F6 (Phase-35-Funktion ohne Store-/CHANGELOG-Zeile).
- RAM-Regel: 3,4 GB frei gemessen; Korpus, Volltestlauf und Playwright seriell, nie parallel.

## Runtime State Inventory

Phase ist kein Rename; relevant ist nur der Laufzeitzustand für M-32-02 und das Release.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | state.db der Dev-Instanz: Storages 7, 14, 15 mit 30/1/49 lebenden Dokumenten ohne Mount; `reconcile`-Zeilen 12, 13 ohne Dokumente | Live-Beleg nutzt sie; vorher `state.db` sichern |
| Live service config | GitHub: Spiegel-Pre-Release `source-1.5-dev.2` mit pillow_heif 1.8.0; Store-Katalog führt 1.4.3 | neuer Spiegel nur mit Owner-Wort; Katalog-Gegenprobe nach Einreichung |
| OS-registered state | keine | keine (verifiziert: keine Task-Registrierung im Projekt) |
| Secrets/env vars | `APPSTORE_TOKEN`, zwei Signaturschlüssel in release.yml/store-submit.yml unverändert | keine |
| Build artifacts | `ghcr.io/street1983nk/findling_backend:1.5.0` entsteht erst mit dem Tag; `.dev/` Host-Backend 1.4.2 auf 8090 | nach Python-Änderungen `FINDLING_PORT=8090 scripts/dev/register-exapp.sh` |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | alle Python-Gates | ✓ | 0.11.7 | , |
| backend/.venv (Python 3.13.13) | Tests, Proben | ✓ | 3.13.13 | , |
| Docker | Image-Proben, lokale Fremdinstallation | ✓ | 29.5.2 | , |
| gh CLI | Release-/Asset-Prüfung, Workflows | ✓ | 2.92.0 | , |
| Dev-Instanz findling-nextcloud :8090 | M-32-02-Live-Beleg | ✓ | NC 34.0.3, HTTP 200 | , |
| HaRP-Testinstanz :8096 | lokale Fremdinstallation | ✓ (Container läuft) | NC 34.0.3 | compose-harp neu aufsetzen |
| files_external (Dev) | Speicher-Fälle | ✓ | 1.26.0 | , |
| freier RAM | Korpus + Playwright | 3,4 GB | , | seriell arbeiten |

**Missing dependencies with no fallback:** keine.

## Security Domain

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein (unverändert, AppAPI-Signatur) | , |
| V4 Access Control | ja | neue Route mit `ExAppRequired` + `rejectForeignCaller()` (App-ID-Header), nur GET, keine Pfade/Namen in der Antwort |
| V5 Input Validation | ja | Generatoren-Korpus; geschlossene Code-Listen; `intList` mit Obergrenze; Detailcode-Form `[A-Za-z0-9_.]{1,200}` |
| V7 Logging | ja | keine Meldungstexte, httpx/httpcore auf WARNING (D-36-09), Log-Sonde mit Positivkontrolle |
| V10 Malicious Code / V12 Files | ja | RLIMIT_AS, Frist, keine Entpackung unter Mitgliedsnamen, Amplification-Grenzen |
| V14 Configuration / Supply Chain | ja | korrespondierende Quelle korrekt (F1), unveränderliche Releases, SHA-256-Prüfung |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| ZIP-/Paket-Bombe | DoS | Vorzählung, Budget, Verhältnis, RLIMIT_AS |
| XML Entity Expansion | DoS | libxml2/expat-Grenzen, `resolve_entities=False` |
| Zip Slip | Tampering | nie entpacken, Scratch-Dateien nach Nummer, Traversal als Signatur |
| Pixel-Flut | DoS | `MAX_IMAGE_PIXELS`, Draft, Adressraum-Schätzung |
| Verwaiste Dokumente fremder Nutzer | Information Disclosure (nur Kandidatenplätze) | M-32-02-Nachlauf; PHP-Recheck bleibt die Autorität |
| Fremder Container liest Storage-Liste | Information Disclosure | App-ID-Abgleich wie bei `mounts()` |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Schwellen Mailtiefe 32 und 1000 Pixel je Byte | Pattern 1 | falsch-positive Sperre echter Dateien oder verfehlte Bombe; Vorabplan entscheidet |
| A2 | OPC/ECMA-376 verbietet DTDs in Paketteilen | Alternatives | nur relevant, wenn statt Meldungsvergleich eine DOCTYPE-Vorprüfung gewählt wird |
| A3 | libxml2-Tiefengrenze 256 ohne huge_tree | Korpus-Lücken | Erwartung des Tiefe-Falls wäre anders; Test zeigt es |
| A4 | `git archive` ist für Commit und git-Version deterministisch | Release-Mechanik | nur Prüfsummen-Vergleich betroffen |
| A5 | Groupfolders-Storage-IDs: mehrere Team-Ordner können einen Storage teilen | M-32-02 | Granularität storage_id statt (storage_id, root_id); ein gelöschter Team-Ordner in einem geteilten Storage würde nicht erkannt (heute schon so beim Abgleich) |
| A6 | Store-Katalog übernimmt 1.5.0 erst nach Cache-Verzug | Reihenfolge | nur Zeitpunkt der Gegenprobe |

## Open Questions

1. **Upgrade-Ausgangsversion v1.4.3 statt v1.4.2?**
   - Bekannt: Store und Nutzer stehen auf 1.4.3; die Strecke-Lehre sagt "neuestes veröffentlichtes Release". ROADMAP/REQUIREMENTS nennen 1.4.2.
   - Empfehlung: v1.4.3 (nach dem Bump), Kriterium als erfüllt werten, weil 1.4.3 sich nur im PHP-Scroll-Fix unterscheidet; Owner bestätigt im Plan.
2. **Abgeschalteter Findling-Schalter (Team-Ordner/externe Speicher) = 30 Tage Karenz?**
   - Bekannt: Schalter-aus lässt `oc_storages` stehen und fällt nach der Definition unter "verschwunden". Treffer aus solchen Speichern bestehen den PHP-Recheck weiter, solange der Nutzer lesen darf.
   - Empfehlung: ja, gleiche Regel (kein Sonderweg); in docs/admin-page.md:124-128 die "bewusste Grenze" ersetzen.
3. **D-36-10 "git archive" vs. Checkliste "vier Quellpakete".**
   - Bekannt: Der Merker aus NEXT.md/STATE.md meint die vier GPL/LGPL-Quellpakete (Pflicht); das Diskussionslog beschreibt "git archive des Tags".
   - Empfehlung: beides im selben `gh release create`; die vier sind nicht verhandelbar.
4. **Ähnliche Dokumente (Phase 35) im Store-Text und CHANGELOG?**
   - Empfehlung: Funktionszeile im Vorabplan anbieten (Kurztext-Regel), CHANGELOG-Eintrag ergänzen.
5. **Bildbomben und Pfad-Traversal: wirklich gesperrt statt heute too_large/indexed?**
   - D-36-03 verlangt eine Klasse für alle Familien; Pattern 1 schlägt die engere Signaturregel vor. Der Vorabplan legt beides als Tabelle vor.

## Sources

### Primary (HIGH confidence)
- Repo-Code gelesen: `extract/{errors,archive,odf,office,image,dispatch}.py`, `store/{repo.py,schema.sql}`, `nc/queue.py`, `worker/{reconcile,poller}.py`, `main.py`, `php/lib/Controller/ReconcileController.php`, `php/lib/Service/{StorageService,AdminViewService}.php`, `.github/workflows/{deploy-harp,release,store-submit,integration,python}.yml`, `scripts/release/corresponding_source.py`, `docs/store-listing.md`, `backend/tests/test_phase31_audit.py`, `conftest.py`
- Nextcloud-Core 34.0.3 im Container findling-nextcloud: `UserDeletedFilesCleanupListener.php`, `Files/Cache/Cache.php::clear`, `Files/Cache/Storage.php::cleanByMountId`, `Files/Cache/FileAccess.php::getByAncestorInStorage/getDistinctMounts`, `files_external/.../StoragesService.php::removeStorage`
- Laufzeitproben dieser Session: XML-Bomben gegen alle Parser (Windows-venv und Image `findling_backend:1.4.3`), `ZipFile()` mit 1 Mio. Einträgen (454 MiB, 32 s), Pillow-Grenzen, `pillow_heif.libheif_info()`
- `pillow_heif-1.8.1.tar.gz` (files.pythonhosted.org), `libheif/build_libs.py` Zeilen 22 bis 24
- state.db und `oc_storages`/`oc_mounts` der Dev-Instanz (nur lesend)

### Secondary (MEDIUM confidence)
- Planungsdokumente: 32-AUDIT.md (M-32-02), 35-AUDIT.md (L-35-06), STATE.md, NEXT.md-Merker

### Tertiary (LOW confidence)
- Schwellenwert-Abwägungen A1, A3, A5

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, keine neuen Pakete, Schutzmechanismen gemessen
- Architecture: HIGH für Kette der Urteilsklasse und Core-Semantik, MEDIUM für M-32-02-Entwurf (nicht gefahren)
- Pitfalls: HIGH für F1 bis F3 (verifiziert), MEDIUM für F4 (Code gelesen)

**Research date:** 2026-10-20
**Valid until:** 2026-11-03 (Release-nah; Dependabot kann Pins weiter verschieben)
