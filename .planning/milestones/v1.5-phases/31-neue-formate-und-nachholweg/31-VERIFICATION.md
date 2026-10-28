---
phase: 31-neue-formate-und-nachholweg
verified: 2026-10-12T19:43:27Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
deferred:
  - truth: "Upgrade 1.4.2 -> 1.5.0 mit echtem Versionsschritt (occ upgrade führt Version001500Date20261012000000 aus)"
    addressed_in: "Phase 36"
    evidence: "Phase 36 SC2: 'Upgrade-Strecke 1.4.2 -> 1.5.0 laeuft in CI Ende zu Ende gruen (Nachholweg, Ausschluesse, ohne Umbau bei Werkssprachen)'. Lauf 38292944828 meldet 'the companion of this commit carries 1.4.2 ... without a version step'; der Nachholweg hängt laut Migration-Docblock nicht an der Migration und ist ohne sie bewiesen."
  - truth: "Owner-Abnahme von Produkt und Store-Text in einer gemeinsamen Playwright-Runde mit echten Testdateien (neue Formate)"
    addressed_in: "Phase 36"
    evidence: "Phase 36 SC3: 'Owner hat Store-Text und Produkt in einer gemeinsamen Playwright-Runde mit echten Testdateien abgenommen'"
  - truth: "LOW-accept-Befunde L-31-05, L-31-06, L-31-08, L-31-09 (großer DIFAT-Zyklus, Diagnosezeile recheck_1_5_0, Neustart mitten im Nachholzyklus, Teil B ohne Generationsfrage)"
    addressed_in: "Phase 36"
    evidence: "Phase 36 SC1 (bösartiger Korpus, Archive, Mails, OLE) und SC2 (Upgrade-Strecke); Zielphase je Befund in 31-AUDIT.md, LOW-Entscheidungen"
---

# Phase 31: Neue Formate und Nachholweg, Verifikationsbericht

**Phasenziel:** Nutzer finden Inhalte aus Mails, ZIP-Archiven, Legacy-Word/-Excel und iPhone-Fotos, und Bestandsinstallationen holen bisher übersprungene Dateien nach dem Upgrade von selbst nach
**Verifiziert:** 2026-10-12T19:43:27Z
**Status:** passed
**Re-Verifikation:** Nein, Erstverifikation
**Stand:** main, HEAD 2bd2f7a5. Seit 53fae392 (Stand aller CI-Läufe unten) nur Doku- und Planungsdateien geändert (`git diff --stat 53fae392..HEAD`: `.planning/`, README x3, `docs/store-listing.md`), kein Produktcode.

## Zielerreichung

### Beobachtbare Wahrheiten

| # | Wahrheit | Status | Beleg |
|---|---|---|---|
| 1 | SC1 / FMT-01: `.eml` über Betreff, Absender, Empfänger und Text auffindbar, auch nur mit HTML-Teil | VERIFIED | `backend/src/findling/extract/mail.py` (373 Zeilen) liest Subject/From/To/Cc und den Körper, HTML über `text.html_to_text`; Kopfzeilen gekürzt und budgetiert (H-31-01). Tests `test_a_plain_mail_yields_subject_sender_recipients_and_body`, `test_a_mail_with_only_html_yields_its_text_without_script_and_style` (lokal grün). E2E: Saat `.github/fixtures/upgrade-seed-formats/seed-mail.eml` ist reines `text/html`, das Saatwort steht nur im HTML-Teil; HaRP 38292944828 Store upgrade 5: "mailquendel finds exactly the file id 335" |
| 2 | SC2 / FMT-02: Text aus Datei in ZIP auffindbar, Treffer zeigt Archiv und innere Datei; Bombe endet als sichtbares Skip-Urteil, Container läuft weiter | VERIFIED | `archive.py` mit Tiefen-, Größen-, Anzahl- und Ratengrenze; Tests je Grenze in `test_extract_archive.py` (`test_the_quine_ends_at_the_depth_limit`, `test_a_declared_total_over_the_limit_is_an_archive_limit`, `test_one_entry_over_the_limit_never_reaches_zipfile`, `test_a_member_over_the_ratio_is_an_archive_limit`). E2E 38292944828: "archivquendel finds exactly the file id 336", "the excerpt of the ZIP hit starts with the inner file innen/notiz.txt" (jq prüft `.subline | startswith("innen/notiz.txt: ")`), "the ZIP bomb is skipped/archive_limit in state.db and in findling_file_state", "the container runs, restart count 0" |
| 3 | SC3 / FMT-03, FMT-04, FMT-05: Text aus `.doc`, `.xls`, HEIC/HEIF ohne LibreOffice, amd64 und arm64; `.xls` mit XLSX-Zellgrenze; nicht lesbare OLE-Varianten benannt | VERIFIED | Kein `libreoffice`/`soffice` in `backend/Dockerfile`. `legacy_xls.py:141,199` nutzt `settings().max_cells` und `Reason.TOO_MANY_CELLS` wie `office.py:150,178`; Test `test_the_cell_limit_of_xlsx_holds_for_xls`. Word 6/95 als `unsupported_variant` (M-31-02 gefixt). E2E amd64: wortquendel, zellquendel, fotoquendel, hullequendel je genau eine Datei. arm64: Multi-arch 38292944825, Job "Build and smoke test linux/arm64": "heic page: verdict indexed/-, fotoquendel found: True", "heic ocr in the image: ok"; arm64-Image installiert olefile 0.47 und xlrd 2.0.2 (HaRP-arm-Buildlog), beide `py2.py3-none-any` laut `uv.lock` (siehe Hinweis unten) |
| 4 | SC4 / FMT-06: nach Upgrade von 1.4.2 werden `legacy_format`/nicht unterstützte Dateien ohne Admin nachgeholt; Beweis in Upgrade-CI mit Saat, ohne Vollreindex, ohne Neu-Einbettung | VERIFIED | `worker/catchup.py`, Marke `recheck_1_5_0` (`store/repo.py:194`), verdrahtet in `main.py:448`, `poller.py:509`, `reconcile.py:377-416`. HaRP 38292944828, stable34/ubuntu-24.04, Store upgrade 2b bis 5 success: unter v1.4.2 "six new types and the bomb without a row, the Word file under .docx skipped(legacy_format), the stale file failed(repeatedly_stuck)"; nach dem Upgrade "recheck_1_5_0 read absent before the upgrade and reads done after it", alle sieben Wörter je genau eine Datei, vier Marken unverändert, "nothing was embedded again" (Vektordigest `bf915800...:288:800` gleich), Dokumentzahl genau +7, `rebuildState idle`, kein Reindex-Banner |
| 5 | SC5 / POL-02 / F-29-03: Datei mit veralteter Größe endet nicht als `repeatedly_stuck`, sondern gelesen oder benannt übersprungen; Regressionstest | VERIFIED | `poller.py:1994-2053`: zwei kurze Antworten mit gleicher Länge und gleichem Hash gelten als die Datei, Log nur Zahlen. Tests `test_poller.py` ab Zeile 4945 (Abschnitt F-29-03), `test_gateway_client.py:241`. E2E: unter 1.4.2 "three deliveries read short, the fourth claim wrote failed/repeatedly_stuck", nach dem Upgrade "cachequendel finds exactly the file id 342" und "the file v1.4.2 wrote off as failed(repeatedly_stuck) without a container row is indexed" |
| 6 | Freischaltung: beide Allowlists tragen die neuen Typen | VERIFIED | `php/lib/Service/StorageService.php:144-150` (heic, heif, rfc822, zip, msword, vnd.ms-excel); Parität `test_allowlist_parity.py` (Teil der grünen Suite 38292944805); E2E zeigt die Mimetypen der Saat und die Indexierung |
| 7 | L-30-03 (aus Phase 30, in 31-13 mitzunehmen): jede GITHUB_ENV-Schreibstelle von Store upgrade 2b bis 7 prüft ihren Wert per Muster | VERIFIED | z. B. `deploy-harp.yml:6192-6196` (`REBUILD_VECTORS_BEFORE` gegen `^[0-9a-f]{64}$`), Gates `test_upgrade_seed_steps.py:923,931`, `test_phase31_audit.py:1587` (L-31-07, kein zeilenweises `grep -E` mehr); `30-AUDIT.md` Frontmatter `fixed: [L-30-01, L-30-03]`, `still_open: [L-30-02]` |
| 8 | Audit Security/Bugs/Performance durchgeführt, Befunde vor Abschluss behandelt (Owner-Regel) | VERIFIED | `31-AUDIT.md`: 0 CRITICAL, H-31-01/H-31-02/M-31-01/M-31-02 gefixt in 013d1c58 und 97891f3a; `test_phase31_audit.py` enthält kein `xfail` mehr (grep: 0); offen nur LOW-accept mit Begründung |
| 9 | Doku und Produkttext: `docs/formats.md`, READMEs nennen die neuen Typen, Entwurf vom Owner abgenommen | VERIFIED | `docs/formats.md` (122 Zeilen); `README.md:42-46` nennt DOC, XLS, EML, ZIP, HEIC und verweist auf `docs/formats.md`; Commit 2bd2f7a5 "owner approves the draft of phase 31" |

**Score:** 9/9 Wahrheiten verifiziert

### Zurückgestellte Punkte

| # | Punkt | Adressiert in | Beleg |
|---|---|---|---|
| 1 | Upgrade mit echtem Versionsschritt 1.4.2 -> 1.5.0, also mit gelaufener Migration `Version001500Date20261012000000` | Phase 36 | SC2 von Phase 36. Heute tragen beide `info.xml` 1.4.2, der Lauf tauscht die Dateien ohne Versionsschritt ("No upgrade required"). Die Migration hat einen eigenen Unit-Test (`php/tests/Unit/Version001500Date20261012000000Test.php`), PHP gates grün auf 76ce8463 (letzter Commit unter `php/`) |
| 2 | Gemeinsame Playwright-Abnahme mit echten Testdateien | Phase 36 | SC3 von Phase 36 |
| 3 | L-31-05, L-31-06, L-31-08, L-31-09 (LOW-accept) | Phase 36 | Zielphase je Befund in `31-AUDIT.md`; `embedding.py:1159` (Cursor-Muster, vor Phase 31) in `deferred-items.md` |

### Erforderliche Artefakte

| Artefakt | Erwartet | Status | Details |
|---|---|---|---|
| `backend/src/findling/extract/mail.py` | .eml-Leser | VERIFIED | 373 Zeilen, verdrahtet über `dispatch.py`, E2E belegt |
| `backend/src/findling/extract/archive.py` | ZIP-Leser mit Grenzen | VERIFIED | 590 Zeilen, Warnfilter gegen Mitgliedsnamen im Log (H-31-02) |
| `backend/src/findling/extract/legacy_doc.py`, `cfb.py` | .doc über olefile/Piece Table | VERIFIED | 340 + 350 Zeilen |
| `backend/src/findling/extract/legacy_xls.py` | .xls über xlrd, XLSX-Zellgrenze | VERIFIED | 227 Zeilen |
| `backend/src/findling/extract/image.py` | HEIC/HEIF im Bildpfad | VERIFIED | Opener-Optionen `False,False,False,1` im Image belegt |
| `backend/src/findling/worker/catchup.py`, `reconcile.py`, `recheck.py` | einmaliger Nachholweg Teil A und B | VERIFIED | Marke in `repo.py:194`, E2E absent -> done nach 302 s |
| `backend/src/findling/worker/poller.py` | POL-02 | VERIFIED | Zeilen 1994-2053 |
| `php/lib/Service/StorageService.php` | Allowlist | VERIFIED | Zeilen 144-150 |
| `php/lib/Migration/Version001500Date20261012000000.php` | Minor-Migration 1.5 | VERIFIED (Unit), E2E zurückgestellt | Zähler-Neuzählung und Versionswert; Nachholweg ausdrücklich unabhängig davon |
| `.github/workflows/deploy-harp.yml` Store upgrade 2b bis 7 | Upgrade-CI-Beweis | VERIFIED | Lauf 38292944828 alle Schritte success |
| `docs/formats.md` | Formatdoku | VERIFIED | |

### Key-Link-Verifikation

| Von | Nach | Über | Status | Details |
|---|---|---|---|---|
| PHP-Allowlist | Container-Allowlist | Paritätstest | WIRED | `test_allowlist_parity.py` grün in 38292944805 |
| Upgrade-Start | Nachholweg Teil A | Poller liest `CATCHUP_MARK` | WIRED | Log: Marke `reconcile` während Teil B, danach `done` |
| Teil A | Teil B | Marke `reconcile` -> `Reconcile.run_once` | WIRED | `reconcile.py:377-416` schreibt `CATCHUP_DONE` |
| ZIP-Treffer | Auszug mit innerer Datei | `snippets_for` -> OCS `subline` | WIRED | jq-Prüfung auf `innen/notiz.txt: ` |
| Kurze Antwort x2 | Indexierung statt Aufgabe | `_fetch_once(same_as=...)` | WIRED | E2E Datei 342 indexiert |

### Datenfluss (Level 4)

| Artefakt | Datenvariable | Quelle | Echte Daten | Status |
|---|---|---|---|---|
| Unified-Search-Treffer der Saat | `.ocs.data.entries` | echter OCS-Aufruf gegen NC stable34 mit HaRP | ja, je Wort genau die erwartete file id | FLOWING |
| ZIP-Auszug | `.subline` | Index-Text mit Mitgliedsmarke | ja | FLOWING |

### Verhaltens-Stichproben

| Verhalten | Befehl | Ergebnis | Status |
|---|---|---|---|
| Extraktoren und Nachholweg | `PYTHONUTF8=1 uv run python -m pytest -q tests/test_extract_mail.py tests/test_legacy_doc.py tests/test_legacy_xls.py tests/test_catchup.py tests/test_recheck.py tests/test_archive_snippet.py tests/test_image_heic.py` | 234 passed, 3 skipped, 28 s | PASS |
| ZIP-Grenzen und POL-02 | `... pytest -q tests/test_extract_archive.py tests/test_poller.py -k "archive or stale or short or POL or catch"` | 245 passed, 1 skipped, 35 s | PASS |
| Volle Suite in CI | `gh run view 38292944805 --log` | "5591 passed, 18 skipped" auf 53fae392 | PASS |

### CI-Belege (selbst per `gh run view` geprüft)

| Lauf | Workflow | Commit | Ergebnis |
|---|---|---|---|
| 38292944828 | HaRP deploy (4 Jobs, Upgrade-Strecke auf stable34/ubuntu-24.04) | 53fae392 | success |
| 38292944805 | Python gates | 53fae392 | success, 5591 passed |
| 38292944825 | Multi-arch image (amd64, arm64, Merge) | 53fae392 | success |
| 38292944794 | Integration | 53fae392 | success |
| 38292944962 | Resilience | 53fae392 | success |
| 38292944814 | Security scans | 53fae392 | success |
| 38298627552 | Security scans | 2bd2f7a5 (HEAD) | success |
| 38256198997 | HaRP deploy (Erstbeweis 31-13) | a3911835 | success |
| 38264572714 | PHP gates | 76ce8463 (letzter PHP-Commit) | success |

### Probe-Ausführung

Keine `scripts/*/tests/probe-*.sh` in den Plänen deklariert. Die Image-Proben (`backend/tests/probe_image_ocr_heic.py`) laufen in CI; ihr Ergebnis ist oben aus dem Log des arm64-Jobs zitiert, nicht aus einer SUMMARY.

### Anforderungsabdeckung

| Anforderung | Plan | Beschreibung | Status | Beleg |
|---|---|---|---|---|
| FMT-01 | 31-04, 31-15 | .eml | SATISFIED | Wahrheit 1 |
| FMT-02 | 31-08, 31-09, 31-15 | ZIP mit Grenzen | SATISFIED | Wahrheit 2 |
| FMT-03 | 31-05, 31-15 | .doc ohne LibreOffice | SATISFIED | Wahrheit 3 |
| FMT-04 | 31-06 | .xls mit XLSX-Zellgrenze | SATISFIED | Wahrheit 3 |
| FMT-05 | 31-07 | HEIC/HEIF per OCR, arm64-tauglich | SATISFIED | Wahrheit 3, arm64-Probe |
| FMT-06 | 31-11 bis 31-13 | Nachholweg mit Upgrade-CI-Beweis | SATISFIED | Wahrheit 4 |
| POL-02 | 31-03 | F-29-03 | SATISFIED | Wahrheit 5 |
| L-30-03 | 31-13 | GITHUB_ENV-Musterprüfung | SATISFIED | Wahrheit 7 |
| CZ-01..03 | Phase 30 | Tschechisch | nicht Gegenstand dieser Phase; in der Upgrade-Strecke weiter grün ("smlouve and proc answer one document each after the upgrade, as before it") | |

Verwaiste Anforderungen: keine. REQUIREMENTS.md ordnet Phase 31 genau FMT-01 bis FMT-06 und POL-02 zu, alle von Plänen beansprucht.

### Gefundene Anti-Muster

| Datei | Zeile | Muster | Schwere | Wirkung |
|---|---|---|---|---|
| (alle seit c9ab42a1 geänderten Dateien unter `backend/src`, `php/lib`, `.github`, `scripts`, `docs`, README) | | `TBD`, `FIXME`, `XXX` | | keine Treffer |
| `backend/src/findling/worker/embedding.py` | 1159 | Cursor-Muster wie L-31-01 | Info | vor Phase 31, in `deferred-items.md` erfasst |

Hinweis (Info, keine Lücke): Auf arm64 ist zur Laufzeit nur der HEIC-Weg im Image bewiesen. `.doc`, `.xls`, `.eml` und `.zip` laufen auf arm64 nicht in einer Probe; ihre Leser sind reines Python (olefile und xlrd als `py2.py3-none-any`, `email` und `zipfile` aus der Standardbibliothek), und das arm64-Image installiert beide Pakete laut Buildlog. Eine kleine arm64-Probe mit `.doc`/`.xls` wäre eine billige Ergänzung für den Launch-Korpus der Phase 36.

### Menschliche Prüfung

Keine für diese Phase. Die Sichtabnahme mit echten Testdateien ist als Phase-36-SC3 eingeplant (siehe Zurückgestellte Punkte).

### Zusammenfassung

Alle fünf Erfolgskriterien der ROADMAP sind im Code vorhanden, durch Tests abgesichert und auf einer echten Nextcloud-Installation Ende zu Ende belegt: die Saat der neuen Formate wird unter v1.4.2 nachweislich nicht oder als `legacy_format`/`repeatedly_stuck` beurteilt und nach dem Austausch des Containers ohne Admin-Eingriff, ohne Markenwechsel und ohne Neu-Einbettung nachgeholt. Die beiden HIGH- und beiden MEDIUM-Befunde des Audits sind gefixt, kein Korpusfall steht mehr auf `xfail`. Seit dem Stand der CI-Läufe hat sich kein Produktcode geändert. Der echte Versionsschritt 1.4.2 -> 1.5.0 mit gelaufener Migration ist nicht Teil dieser Phase und als Phase-36-SC2 eingeplant.

---

_Verifiziert: 2026-10-12T19:43:27Z_
_Verifier: Claude (gsd-verifier)_
