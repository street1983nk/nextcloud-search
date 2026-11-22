# 45-07: Faktenprüfung der drei READMEs (Stand 1.7.0, geprüft am 22.11.2026)

Geprüft gegen Code und Konfiguration auf `main` (Kopf feeef88b plus die Änderungen dieses Plans). Zeilen: README.md (DE) / README.en.md (EN) / README.fr.md (FR).

| Aussage | README | Zeile | Quelle | Ergebnis |
|---|---|---|---|---|
| Nextcloud 33 bis 35 | DE/EN/FR | 73 / 71 / 76 | `php/appinfo/info.xml` :280 und `backend/appinfo/info.xml` :283, `<nextcloud min-version="33" max-version="35"/>` | stimmt |
| AppAPI mit HaRP als Deploy-Ziel | DE/EN/FR | 73 / 71 / 76 | CLAUDE.md Kernentscheidung, `.github/workflows/deploy-harp.yml` | stimmt |
| RAM 4 GB, Messsatz 52.111 Dokumente, Spitze 1.764 MB, 2-GB-Grenze | DE/EN/FR | 74 / 72 / 79 | `MEASURED_SENTENCE*` in `backend/tests/test_store_metadata.py`, Rohdaten `docs/measurements/2026-09-vergleichsmessung-m7g/` | stimmt (Gate grün) |
| 730,2 MB / 730.2 MB / 730,2 Mo, genau einmal je README | DE/EN/FR | 78 / 75 / 82 | `RESIDENT_FIGURE`, Rohdatei `docs/measurements/2026-09-v13-messung/rohdaten/94c-bodensatz-zyklen.txt` | stimmt, je 1 Treffer |
| CPU 2 Kerne, amd64 und arm64, keine GPU | DE/EN/FR | 82 / 79 / 86 | `.github/workflows/docker.yml` Plattform-Matrix, CPU-only-Stack | stimmt |
| Share-Satz (Profile Standard/Leistung) | DE/EN/FR | 83 / 80 / 87 | `SHARE_SENTENCE_*` (Owner-Wortlaut 36-WORTLAUT B1) | stimmt (Gate grün) |
| Leistungsprofile, Sparsam voreingestellt | DE/EN/FR | 39 / 37 / 41 | `backend/src/findling/profile.py` `ECONOMY` | stimmt |
| fp32 nur unter Standard und Leistung, einmalig ladbar | DE/EN/FR | 41 / 39 / 43 | `backend/src/findling/precision.py` :17-21 | stimmt |
| Texterkennung zehn Sprachen, voreingestellt deu+eng+fra | DE/EN/FR | 29 / 29 / 31 | `backend/src/findling/config.py` :478 `OCR_DEFAULT_LANGUAGES`, :507 `OCR_LANGUAGE_ALLOWLIST` (10) | stimmt |
| Suchsprachen: de+en voreingestellt, es, it, nl, pt, cs verfügbar (neu im README) | DE/EN/FR | 50 / 48 / 52 | `config.py` :97 `DEFAULT_LANGUAGES`, :164 `SUPPORTED_LANGUAGES` | stimmt |
| Fünf bekannte Grenzen (neu im README) | DE/EN/FR | 53 / 51 / 55 | Wortlaut je Sprache aus der info.xml; EN wortgleich mit `docs/language-analyzers.md` "Known limitations (short list, HART-05)"; Code: `config.py` :195 `STEMMERLESS_LANGUAGES = {"cs"}`, `index/analyzer.py` `split_compound` nur in der deutschen (:309) und der niederländischen Kette (:503), `ascii_fold` :405, fr nicht in `SUPPORTED_LANGUAGES` | stimmt |
| Ähnliche Dokumente, Link an jedem Treffer | DE/EN/FR | 34 / 33 / 36 | Wortlaut wie info.xml; STR-01, `backend/tests/test_similar_endpoint.py` | stimmt |
| Ausschluss einzelner von Admins angelegter externer Speicher (ab 1.7.0, neu) | DE/EN/FR | 43 / 42 / 45 | 45-02/45-03/45-05: `StorageService::ADMIN_MOUNT_TYPE`, `SettingsService::KEY_EXCLUDED_EXTERNAL_MOUNTS`, `php/templates/admin.php` `#findling-rules-mounts` | stimmt |
| Freie Plätze für Ordner und Muster (ab 1.7.0, neu) | DE/EN/FR | 45 / 44 / 47 | 45-04: `#findling-rules-slots`, `#findling-rules-patterns-slots`, `php/js/admin.js` `refreshSlots()` | stimmt |
| Oberfläche in neun Sprachen inkl. Traditional Chinese (neu) | DE/EN/FR | 47 / 46 / 49 | `ls php/l10n/*.json`: de, de_DE, es, fr, it, nl, pt_BR, pt_PT, zh_TW plus Englisch als Quelle; de_DE ist die Sie-Form desselben Deutsch; PRODUCT.md :35 | stimmt (9) |
| Formatliste inkl. DOC, XLS, EML, ZIP, HEIC | DE/EN/FR | 65 / 63 / 67 | `backend/src/findling/extract/dispatch.py` :101-147 `ALLOWED_MIMETYPES`, `IMAGE_MIMETYPES`; ZIP ohne OCR `docs/formats.md` :8 | stimmt; PPT (alt) wird zu Recht nicht genannt |
| `occ findling:index --status` | DE/EN/FR | Installation | `php/lib/Command/IndexCommand.php` :24 | stimmt |
| Versionsabweichung: Suche antwortet mit nichts, Seite nennt beide Nummern | DE/EN/FR | Installation | `php/lib/Service/ExAppService.php` | stimmt (unverändert seit 1.1, Gates in Phase 11) |
| Tesseract, Tantivy, SQLite mit sqlite-vec | DE/EN/FR | Architektur | `backend/pyproject.toml` (`tantivy==0.26.2`, `sqlite-vec==0.1.9`), `backend/Dockerfile` | stimmt |
| Link Fidelity-Test (GitHub) | DE/EN/FR | 18 / 17 / 18 | `curl` 200 | stimmt |
| Badges python.yml, php.yml, security.yml (Seite und badge.svg) | DE/EN/FR | 5-7 | `curl` je 200 (6 Links, je einmal) | stimmt |
| Relative Links: LICENSE, docs/backup(.en/.fr).md, docs/embeddings.md, docs/formats.md, docs/language-analyzers.md, docs/migrate-from-fulltextsearch(.en/.fr).md, docs/performance.md, docs/privacy.md, store/media/screenshot-search-v2.png | DE/EN/FR | diverse | Datei vorhanden (`test -e`) | alle vorhanden |
| Store-, Shields-, Scorecard-, Best-Practices-Links | DE/EN/FR | 8-11, Installation | nicht abgefragt (Plan: nur GitHub- und Doku-Links; B9 Store-API sparsam) | nicht geprüft, unverändert |

Offene Befunde: keine. Abweichungen, die in allen drei Sprachen gleich zu korrigieren gewesen wären: keine; ergänzt wurden in allen drei Sprachen gleich die Suchsprachen, die fünf Grenzen mit Verweis auf `docs/language-analyzers.md` und die drei Neuerungen von 1.7.0.

## Umlaut-Audit der geänderten deutschen Zeilen

Vorfilter `grep -nE "(ae|oe|ue)[a-z]|ss[^a-z]"` über die hinzugefügten Zeilen von README.md und docs/admin-page.md (`git diff -U0`):

| Treffer | Wort | Urteil |
|---|---|---|
| admin-page.md, Zähler-Absatz | "neuen" | korrekt (neu, kein Umlaut) |
| admin-page.md, Abschnitt Ordnerfeld | "neuer" | korrekt |
| admin-page.md, Tabelle Abgelehnte Eingaben | "neuer" | korrekt |

README.md: kein Treffer. Echte Umlaute in den neuen Zeilen: "ausschließen", "Plätze", "für", "Oberfläche", "Französisch", "Niederländisch", "verfügbar", "Wörter", "zerlegt", "Stammformreduktion" (ohne Umlaut), "Einhängepunkt", "Ausschluss" (kurzes u, ss richtig), "außerdem", "unverändert", "nächsten", "regulären", "hinzuzufügen", "Bildschirmleser". Keine U+2013/U+2014 in README.md, README.en.md, README.fr.md, docs/admin-page.md, docs/language-analyzers.md, docs/l10n-chinese.md.
