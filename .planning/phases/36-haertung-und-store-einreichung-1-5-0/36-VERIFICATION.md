---
phase: 36-haertung-und-store-einreichung-1-5-0
verified: 2026-10-28T13:05:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
notes:
  - "SC2-Wortlaut '1.4.2 -> 1.5.0' wird per Owner-Entscheid D-36-13 (20.10.2026) als '1.4.3 -> 1.5.0' gelesen (tatsaechlicher Store-Stand); Abweichung ist im ROADMAP-Urteilsblock und in REQUIREMENTS.md (HART-06, Vermerk 36-16) dokumentiert und zaehlt nicht als Gap."
---

# Phase 36: Haertung und Store-Einreichung 1.5.0, Verification Report

**Phase Goal:** Findling 1.5.0 ist ueber den Happy Path hinaus gehaertet und beide Apps sind nach Owner-Abnahme im Store eingereicht
**Verified:** 2026-10-28 (Verifikationsstand main 7a5b40b8)
**Status:** passed
**Re-verification:** No, Erstverifikation (keine fruehere 36-VERIFICATION.md)

## Goal Achievement

Goal-backward geprueft gegen die fuenf Success Criteria aus ROADMAP.md (Roadmap-Vertrag). SUMMARY-Behauptungen wurden nicht uebernommen, sondern gegen Code, lokale Testlaeufe und die GitHub-API gehalten.

### Observable Truths

| # | Truth (Success Criterion) | Status | Evidence |
|---|---|---|---|
| 1 | Audit endet 0 CRIT / 0 HIGH; boesartige Archive, Mails, OLE-Dateien aus einem Testkorpus enden als benannte Urteile ohne Absturz und ohne Speicherueberlauf | VERIFIED | 36-AUDIT.md Frontmatter: critical 0, high 0, medium 0, low 4 (3 gefixt mit Commits 69815132/38e54d32/6dee66f4, L-36-04 begruendet akzeptiert), status fixed. Korpus live nachgefahren: `uv run --no-sync pytest tests/test_phase36_hostile_corpus.py` ergibt **64 passed in 8.57s**, 0 xfail im Modul (grep). Generatoren in `backend/tests/hostile.py` (D-36-01, keine Binaerdateien im Repo). Urteil `skipped(blocked_malicious)` durch die ganze Kette verdrahtet: alle 8 Extraktoren (archive/cfb/odf/office/mail/image/legacy_doc/errors), config.py, queue.py, repo.py, PHP FileStateService/AdminViewService/ProfileController, Label "blocked as malicious" in allen **16** l10n-Katalogen |
| 2 | Upgrade-Strecke Store-Version -> 1.5.0 laeuft in CI Ende zu Ende gruen; Fremdinstallation auf frischer Nextcloud funktioniert | VERIFIED | `.github/workflows/deploy-harp.yml:168` `UPGRADE_FROM_TAG: v1.4.3` (D-36-13). HaRP-Lauf **39584388860**: per `gh run view` conclusion **success**. Fremdinstallation aus Release-Assets: Lauf **39590105344** conclusion **success** (4 Matrixzeilen); zusaetzlich lokale Fremdinstallation auf frischer NC 34.0.3 (Port 8096) in 36-ABNAHME.md protokolliert (Release-Tarballs mit SHA-256, Image-Digest, HaRP-Tunnel mTLS) |
| 3 | Owner hat Store-Text und Produkt in einer gemeinsamen Playwright-Runde mit echten Testdateien abgenommen | VERIFIED | 36-ABNAHME.md: Runde 21.10.2026 auf frischer Instanz 8096 mit echten Testdateien (Korpus, neue Formate, Tschechisch, Aehnlich, Sammelklasse-Proben); P1 bis P8 gruen; sechs Store-Texte zeichengleich zu 36-WORTLAUT B1 (sha256 je Text); Zeile 124-126: Frage "abgenommen oder Einwaende je Punkt", Antwort woertlich **"okok"**, Owner-Abnahme 21.10.2026 |
| 4 | Beide Apps 1.5.0 eingereicht (2x HTTP 201), Beleg in docs/store-listing.md | VERIFIED | Tag v1.5.0 existiert im Repo (git tag). Lauf **39598694849** "Store submission": per `gh run view` conclusion **success**, created 2026-10-21T12:19:35Z, Kopf 6c953a76. docs/store-listing.md Abschnitt Release 1.5.0 (Punkte 10-12): findling HTTP 201 12:19:46Z, findling_backend HTTP 201 12:19:47Z, plus Gegenprobe von aussen (Store-Seiten 200, Katalog-Abrufe). 1.5.1 folgte (Lauf 39865809204, ebenfalls 2x HTTP 201) |
| 5 | M-32-02 behoben: Dokumente geloeschter Nutzer verlassen den Index beim naechsten Abgleich; verschwundene externe Speicher nach 30 Tagen Karenz; Beleg mit Positivkontrolle | VERIFIED | Code: `php/lib/Controller/ReconcileController.php:173` ApiRoute GET `/storages/gone` (ExApp-Guard, 412 live belegt in 36-AUDIT S1/S2), `StorageService::classifyAbsent()` (Zeile 404); Backend `worker/reconcile.py:186` `VANISHED_STORAGE_GRACE_SECONDS = 30 * 86_400`, Sweep-Logik Zeilen 816-845. CI-Integrationstest dauerhaft in `.github/workflows/integration.yml` (geloeschter Nutzer, per SQL um 31 Tage rueckdatierter vanished-Stempel, abgeschalteter Speicher, "the control stayed" = Positivkontrolle). Live-Beleg 36-M3202-BELEG.md (Dev 8090, zwei unabhaengige Orakel, Sicherung vorher). Lokal: 25 vanished-Tests passed |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `backend/tests/test_phase36_hostile_corpus.py` | 64 Korpusfaelle, 7 Familien, kein xfail | VERIFIED | 12 Testfunktionen, 7 parametrize-Bloecke, 64 Faelle, Lauf gruen (8,57 s), 0 xfail |
| `backend/tests/hostile.py` | deterministische Generatoren, keine Binaerdateien im Repo | VERIFIED | existiert; Proben in 36-ABNAHME nur im Scratch erzeugt |
| `backend/src/findling/extract/errors.py` | Entity-Bomb-Probe auf "amplification factor" (WR-36-01-Fix) | VERIFIED | Zeile 299 `_AMPLIFICATION: Final = "amplification factor"` samt Begruendungskommentar; Regressionstest `test_a_tag_named_amplification_is_no_entity_bomb` laeuft gruen (12 passed im -k-Lauf) |
| `backend/src/findling/worker/reconcile.py` + `nc/files.py` | Docstrings sagen, was der Sweep tut (WR-36-02-Fix) | VERIFIED | Diff 3580cd45 geprueft: beide Prosa-Stellen nennen jetzt beide Haelften (nichts sofort, abgelaufener Stempel wird dennoch gekehrt); Baumhash im selben Commit nachgezogen |
| `php/lib/Controller/ReconcileController.php` | Route /storages/gone mit Guard und Eingabegrenzen | VERIFIED | ApiRoute Zeile 173; Trust-Boundary-Gate und Live-412-Proben in 36-AUDIT S1/S2 |
| `.github/workflows/deploy-harp.yml` | Upgrade-Strecke ab v1.4.3, Fremdinstallations-Beweis | VERIFIED | UPGRADE_FROM_TAG v1.4.3 (Zeile 168); Laeufe 39584388860 und 39590105344 success (gh API) |
| `docs/store-listing.md` | Beleg Release 1.5.0 mit 2x HTTP 201 | VERIFIED | Punkte 10-12 mit Zeitstempeln und Gegenprobe |
| 16 l10n-Kataloge | Wortlaut der Sammelklasse | VERIFIED | 16 Dateien in php/l10n tragen "blocked as malicious" |
| `36-AUDIT.md`, `36-ABNAHME.md`, `36-M3202-BELEG.md` | Audit-, Abnahme- und M-32-02-Belege | VERIFIED | vorhanden, inhaltlich konsistent mit Code und CI |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| Extraktoren (archive/odf/office/mail/image/cfb) | Urteil blocked_malicious | 8 Signaturcodes (zip_ratio, zip_overlap, zip_traversal, cfb_cycle, image_pixels, mail_nesting, xml_entities, package_entries) | WIRED | grep ueber backend/src: alle Extraktoren plus config/queue/repo tragen den Code; Review 36-REVIEW bestaetigt die Logikpfade |
| Urteil | Admin-Karte / /diagnose / Kataloge | FileStateService, AdminViewService, ProfileController, 16 Kataloge | WIRED | PHP-Seite traegt den Code; Live-Sichtprobe 36-ABNAHME: diagnose zeigt skipped/blocked_malicious mit Detail zip_traversal bzw. image_pixels, Admin-Karte de "Datei als boesartig gesperrt" |
| Container-Abgleich | PHP /storages/gone | files.gone_storages -> classifyAbsent | WIRED | reconcile._sweep_vanished ruft die Route; Live-Beleg 8090 und CI-Integrationstest fahren die Strecke Ende zu Ende |
| Release-Tag v1.5.0 | Store | store-submit.yml Lauf 39598694849 | WIRED | gh API: success; 2x HTTP 201 im Beleg |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Korpus 64 Faelle enden als benannte Urteile ohne Absturz | `uv run --no-sync pytest tests/test_phase36_hostile_corpus.py -q` | 64 passed in 8.57s | PASS |
| WR-36-01-Regression (Tag namens amplification bleibt corrupt) | `pytest tests/test_extract_signatures.py -k "amplification or entity_bomb"` | 12 passed | PASS |
| M-32-02-Sweep-Logik | `pytest tests/ -k vanished` | 25 passed | PASS |
| CI-Laufergebnisse (Upgrade, Fremdinstallation, Submission) | `gh run view 39584388860 / 39590105344 / 39598694849` | je conclusion success | PASS |

Volle Suite (Vorgabe des Koordinators, 28.10.2026): 6177 passed, 263 skipped; einzige lokale Ausfaelle sind 26 Docker-gebundene Audit-Tests (docker run haengt auf dieser Maschine, in CI gruen) plus 2 Last-Flakes, die isoliert 5x gruen laufen. Nicht erneut gefahren.

### Probe Execution

SKIPPED: das Projekt nutzt keine `scripts/*/tests/probe-*.sh`-Konvention (find leer); die runnable Checks liefen als Behavioral Spot-Checks oben.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| HART-06 | Phase 36 (36-07 bis 36-15) | Launch-Haertung: Audit 0 CRIT/0 HIGH, boesartiger Korpus, Upgrade-Strecke in CI, Fremdinstallation | SATISFIED | REQUIREMENTS.md [x] Complete mit Vermerk D-36-13; alle Teilbelege oben verifiziert |
| REL-05 | Phase 36 (36-01, 36-14 bis 36-16) | Store-Einreichung 1.5.0 beider Apps nach Text- und Produktabnahme | SATISFIED | REQUIREMENTS.md [x] Complete; Abnahme okok 21.10., Submission success, 2x HTTP 201 |

Keine verwaisten Requirements: REQUIREMENTS.md mappt auf Phase 36 genau HART-06 und REL-05.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| keine | - | kein TBD/FIXME/XXX in backend/src, php/lib, php/js; "placeholder"-Treffer sind Fachbegriffe (PPTX-Platzhalterformen, Versions-Platzhalter), keine Stubs | - | - |

Code-Review 36-REVIEW.md: 0 critical, 2 warnings, beide in 3580cd45 gefixt und hier im Code plus per Regressionstest verifiziert; 6 Info-Punkte ohne Blocker-Charakter.

### Human Verification Required

Keine offenen Punkte. Die menschliche Verifikation dieser Phase war die gemeinsame Owner-Abnahme (Playwright-Runde 21.10.2026, P1 bis P8, Urteil "okok", 36-ABNAHME.md) und ist dokumentiert abgeschlossen; die Einreichung ist extern gegengeprueft (Store-Seiten 200, Katalogabrufe).

### Gaps Summary

Keine Gaps. Alle fuenf Success Criteria sind im Code, in CI-Laeufen (per GitHub-API bestaetigt) und in den Belegdokumenten nachvollziehbar erfuellt. Die einzige Abweichung vom ROADMAP-Wortlaut (Upgrade-Start v1.4.3 statt v1.4.2) ist ein dokumentierter Owner-Entscheid (D-36-13) und kein Mangel. Nachlaufende LOW-Befunde L-36-05/L-36-06 waren von Beginn an als Ziel 1.5.1 deklariert und sind mit dem inzwischen eingereichten 1.5.1 ausserhalb dieses Phasenumfangs behandelt.

---

_Verified: 2026-10-28T13:05:00Z_
_Verifier: Claude (gsd-verifier)_
