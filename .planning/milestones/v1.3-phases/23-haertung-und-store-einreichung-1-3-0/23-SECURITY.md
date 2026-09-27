---
phase: 23
slug: haertung-und-store-einreichung-1-3-0
status: verified
threats_open: 0
asvs_level: 1
created: 2026-09-27
register_authored_at_plan_time: true
---

# Phase 23: Security

> Sicherheitsvertrag der Phase: Threat Register, akzeptierte Risiken und Audit Trail.
> Register vollständig aus den `<threat_model>`-Blöcken von 23-01-PLAN.md bis 23-09-PLAN.md übernommen: 46 Einträge, nämlich 37 nummerierte Threats (T-23-01 bis T-23-37) und neun Plan-Einträge T-23-SC (je Plan einer). Die Zählung "43" im Auftrag deckt sich damit nicht; maßgeblich sind die Plan-Dateien. Disposition: 34 mitigate, 12 accept, 0 transfer.
> Jede Evidence ist am Baum HEAD `e3f3b9e` nachgeprüft, nicht aus den SUMMARY-Dateien übernommen. Nachgefahren vom Auditor: `uv lock --check` (grün, 67 Pakete), pytest über `test_public_artifacts.py`, `test_store_metadata.py`, `test_lockstep_versions.py`, `test_embed_engine.py`, `test_one_load.py` (239 bestanden, 0 rot), `git log 8b060e5..HEAD` (68 Commits, eine Identität, 0 Trailer), anonyme Abfrage des Manifestindex auf ghcr.io, `gh run view` der Läufe 36292802211 und 36304007154, `gh issue view 14`.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| PHP-Companion zu Container | Suchtext kommt über AppAPI-Header authentifiziert an; die Route darf keine Last erzeugen, die andere Nutzer blockiert | Suchtext, Nutzerkennung |
| Anfrage zu Hintergrundarbeit | Ein Request löst den Warmlauf aus, der nach seinem Ende weiterläuft (`BackgroundTasks`) | fester Text `WARM_TEXT` |
| PyPI zu Abbild, Abbild zu Netz | Pakete aus dem Lockfile landen im Container; Netzbibliotheken dürfen nichts nachladen | Pakete, Modell |
| Repositorium zu Store-Seite | Store-Texte werden mit dem Release öffentlich und sind danach nicht editierbar | info.xml-Texte |
| CI-Logs zu Öffentlichkeit | Logs öffentlicher Workflows sind lesbar | Zahlen, Typnamen, maskierte Secrets |
| Migration zu Nextcloud-Datenbank | Löscht Zeilen in `oc_findling_file_state`, schreibt in `oc_findling_queue`, ohne Nutzerkontext | Datei-IDs |
| GitHub-Secret-Store zu Store-API | `APPSTORE_TOKEN` und Signierschlüssel verlassen den Secret-Store nie | Token, Schlüssel |
| Owner-Konto zu Issue | Kommentar erscheint öffentlich im Namen des Owners | Issue-Text |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation (Evidence) | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-23-01 | Denial of Service | Warmlauf pro Tastendruck | mitigate | `embed/engine.py:541-568` `warm_wanted()` mit drei Bedingungen; `engine.py:604-619` `_WARMING`-Flag unter `_LOCK`; `embed/model.py:596-597` Kopfprüfung `if self._engine is not None: return`; Zehnerfall `test_embed_engine.py:1350` parametrisiert `"0"`/`"900"`, `load_count() - before == 1` | closed |
| T-23-02 | Denial of Service | RAM der Gewichte auf 4-GB-Boxen | mitigate | kein `warm()`-Aufruf im Start von `main.py` (einzige Aufrufer: Freigabe-Tick `main.py:403-404` hinter `warm_wanted()` und `api/search.py:380-396`); `request_warm()` nur in `api/search.py:326`; Test `test_no_warm_run_is_wanted_without_a_request` (`test_embed_engine.py:1252`, `"0"`/`"900"`) | closed |
| T-23-03 | Denial of Service | Ladefenster, GIL beim Sessionaufbau | accept | AR-23-01 | closed |
| T-23-04 | Information Disclosure | Logzeilen Warmlauf/Routen | mitigate | `engine.py:113` `WARM_TEXT = "aufwaermen"`, `engine.py:616` bettet nur diese Konstante ein; `api/search.py:342` einzige Logzeile, nur `type(error).__name__`; Test `test_the_warm_text_carries_nothing_of_a_user_and_nothing_of_the_disk` (`test_embed_engine.py:1447`) | closed |
| T-23-05 | Elevation of Privilege | Berechtigungsfilter der Kandidaten | accept | AR-23-02 | closed |
| T-23-SC (01) | Tampering | Installs | accept | AR-23-04 | closed |
| T-23-06 | Tampering | uv.lock-Drift | mitigate | `uv lock --check` vom Auditor gefahren: "Resolved 67 packages", grün; `uv.lock` enthält keinen der sechs entfernten Pakete (fastembed, loguru, mmh3, py-rust-stemmers, requests, urllib3: 0 Treffer); `git diff 8b060e5..HEAD -- backend/uv.lock` ohne neues `name =` | closed |
| T-23-07 | Denial of Service | tokenizers fällt aus dem Abbild | mitigate | `backend/pyproject.toml:44` `"tokenizers==0.23.2"`, `:45` `"numpy==2.5.2"` als direkte Kanten; `.github/workflows/docker.yml:240-241` `find_spec('tokenizers')`/`find_spec('numpy')` am gepushten Digest mit `::error::` | closed |
| T-23-08 | Information Disclosure | huggingface-hub Netzzugriff | mitigate | `backend/Dockerfile:498` `HF_HUB_OFFLINE=1`, Begründung `Dockerfile:482-484` auf tokenizers umgestellt; Prüfschritt `docker.yml:240` mit `--network none` | closed |
| T-23-SC (02) | Tampering | pip | accept | AR-23-04 | closed |
| T-23-09 | Information Disclosure | Store-Text/Issue-Antwort | mitigate | `test_public_artifacts.py` (alle Dateien unter `docs/`, damit `docs/store-listing.md`); Vokabular-Sperre `test_store_metadata.py:196` `BLOCKED_TERM`, Fälle `:1752` (info.xml) und `:1764` (store-listing.md); vom Auditor grün nachgefahren | closed |
| T-23-10 | Repudiation | Store-Text ohne Owner-Abnahme | mitigate | `23-03-PLAN.md:110` `checkpoint:human-verify gate="blocking"`; Abnahme "Text abgenommen" in `23-03-SUMMARY.md:23,63`; Audit `docs/audits/2026-09-phase-23/README.md` Abschnitt 7, Kriterium 2 | closed |
| T-23-11 | Spoofing | Issue-Antwort ohne Freigabe | mitigate | 23-03 lieferte nur Entwurf (`docs/store-listing.md` Teil 6); Posten erst 23-09 nach Owner-Wort "Mit Zitatzeile" (Audit Abschnitt 11, "Die Freigabe des Owners"); Kommentar 07:44:41Z nach den zwei 201, per `gh issue view 14` bestätigt | closed |
| T-23-SC (03) | Tampering | Installs | accept | AR-23-04 | closed |
| T-23-12 | Information Disclosure | neue Log-Zeilen integration.yml/one_load | mitigate | `integration.yml:1836` `EXAPP_SECRET` nur base64 in `AUTHORIZATION-APP-API`, kein `echo` eines Geheimnisses (Grep `echo.*SECRET` 0 Treffer); Ausgaben `:1873-1884`, `:1897` nur Zahlen/HTTP-Code; `tools/one_load.py:538-543` druckt nur Kennzahlzeilen und `verdict=` | closed |
| T-23-13 | Repudiation | CI-Schritt prüft nichts mehr | mitigate | `integration.yml:1866` Trefferpflicht der ersten Suche (`jq -e '... length > 0'` plus HTTP 200); `:1921-1924` unveränderte `jq -e`-Zusicherungen der Paraphrase; Mutationsfälle `test_one_load.py:271,320,334,348` ("it goes red when ...") | closed |
| T-23-14 | Denial of Service | Warteschleife ohne Ende | mitigate | `integration.yml:1893` `warm_deadline=$(( warm_start + 120 ))`, `:1900-1903` `::error::` plus `exit 1` | closed |
| T-23-15 | Spoofing | fremde Autorschaft/Claude-Trailer | mitigate | `git log 8b060e5..HEAD`: 68 Commits, Autor und Committer ausschließlich `street1983nk <k.cherif@outlook.de>`; `co-authored-by`/`claude`/`anthropic` in Commit-Texten: 0 Treffer | closed |
| T-23-SC (04) | Tampering | Installs | accept | AR-23-04 | closed |
| T-23-16 | Tampering | DELETE löscht mehr als gone-Urteile | mitigate | `Version001300Date20260927000000.php:95-98` QueryBuilder mit `createNamedParameter`: `state='skipped'`, `reason='gone'`, `file_id IN` Band (`PARAM_INT_ARRAY`); SELECT `:122-123` identisch gebunden; Tests `Version001300Date20260927000000Test.php:177` (Spalten und Parameter exakt) und `:207` "andere Gründe bleiben" | closed |
| T-23-17 | Tampering | Abbruch mitten im Band | mitigate | `Version001300Date20260927000000.php:90-105` `beginTransaction` je Band, `requeueAs` und DELETE darin, `catch (\Throwable)` mit `rollBack()` und `throw $e`; Tests `:231` (ein `rollBack`, Ausnahme weitergeworfen) und `:251` (2500 Zeilen, drei Transaktionen) | closed |
| T-23-18 | Denial of Service | einmalig viel Arbeit nach Upgrade | accept | AR-23-03 | closed |
| T-23-19 | Information Disclosure | Migrationsausgabe nennt Dateikennungen | mitigate | `Version001300Date20260927000000.php:83` fester Satz, `:110` `sprintf('requeued %d files once judged gone', $total)`, nur Zahl; Tests prüfen den Wortlaut (`Test.php:170`, `:194`) | closed |
| T-23-20 | Elevation of Privilege | neu eingereihte Dateien falsche Nutzer | mitigate | Migration berührt nur Queue und eigene Tabelle, keine Rechteentscheidung (Code `:80-111`, Test `:302` "asks the container for nothing"); Rechteweg `SearchService::readableFile` für alle drei Aufrufer, gelesen in Audit Abschnitt 3 V4; `git diff --stat 8b060e5..HEAD` über SearchService, PathResolverService, GatewayController, QueueService vom Auditor nachgefahren: leer | closed |
| T-23-SC (05) | Tampering | Installs | accept | AR-23-04 | closed |
| T-23-21 | Repudiation | Zusicherung 3 aufgeweicht | mitigate | `deploy-harp.yml:4401-4402,4405` `moved_by_seed` nur für `.container.docs`, `.container.indexed`, `.nextcloud.skipped`; `:4403-4409` alle übrigen Zähler (`skipped`, `failed`, `scheduled`, `running`, `rebuildState`) unter `unchanged` | closed |
| T-23-22 | Repudiation | Migration läuft im CI nicht | mitigate | `deploy-harp.yml:3322-3326`: im Gleichstand-Zweig wird Zusicherung zum Saatfall rot; Saatnachweis `:4413` (gone-Urteil weg) und `:4430`; Logzitat "Updated <findling> to 1.3.0", "the instance performed the app update: 1.2.0 to 1.3.0" in `23-06-SUMMARY.md:107` | closed |
| T-23-23 | Information Disclosure | DB-Passwort/EXAPP_SECRET in echo | mitigate | Saatschritt `deploy-harp.yml:3328-3418` nutzt nur `TESTUSER_PASS` (Wegwerf-Kanarienwert) in `curl -u` und `FINDLING_DB`; Grep `echo.*(PASS|SECRET|TOKEN)` über deploy-harp.yml und integration.yml: 0 Treffer | closed |
| T-23-24 | Tampering | Versionsstellen laufen auseinander | mitigate | `php/appinfo/info.xml:146`, `backend/appinfo/info.xml:163` und `:257` `<image-tag>` je `1.3.0`; `test_lockstep_versions.py:159` (grün nachgefahren); `release.yml:183-191` Vergleich beider info.xml gegen den Tag | closed |
| T-23-SC (06) | Tampering | Installs | accept | AR-23-04 | closed |
| T-23-25 | Tampering | übernommener Text weicht ab | mitigate | Diff-Beleg `23-07-SUMMARY.md:90` ("IDENTICAL clean" für alle sechs); Gates `test_store_metadata.py:1202` (EN-Grenzliste zeichengleich zur Doku) und `:1564` (Abweichung um ein Zeichen fällt durch) | closed |
| T-23-26 | Information Disclosure | Store-Text Vokabular/Kennungen | mitigate | wie T-23-09: `test_store_metadata.py:1752` über beide info.xml, `test_public_artifacts.py` über `docs/`; grün nachgefahren | closed |
| T-23-27 | Denial of Service | ungültige info.xml bricht Upload | mitigate | `test_store_metadata.py:1395` (nicht wohlgeformt), `:1287` (leeres Element), `:1275` (unbekannter Sprachcode); `php.yml:149` `xsltproc pre-info.xslt | xmllint --schema info.xsd`; Store install in deploy-harp (Lauf 36292802231 auf dem Tag success) | closed |
| T-23-SC (07) | Tampering | Installs | accept | AR-23-04 | closed |
| T-23-28 | Repudiation | Audit bestätigt sich selbst | mitigate | Audit Abschnitt 4: sechs Musterfamilien, die das Gate nicht führt, plus Entropiemessung, über 95 Dateien außerhalb von `docs/`; Ausnahmeliste mit eigenen Fragen geprüft (51 Einträge, 0 doppelte Gründe) | closed |
| T-23-29 | Elevation of Privilege | #14-Fix ohne Audit | mitigate | Audit Matrix Zeile 2 und Abschnitt 3 V4: Tabelle je Stelle (`GatewayController`, `QueueService::readerOf`, `SearchService`, `PathResolverService`) inhaltlich gelesen, Befund F-23-04 (LOW, nie falsche Datei) | closed |
| T-23-30 | Repudiation | gewachsene Skipzahl | mitigate | Audit Abschnitt 2 "Die Skipzahl gegen die Referenz": 15 gegen 15, nicht gewachsen; CI 11 übersprungen | closed |
| T-23-31 | Information Disclosure | Auditbericht zitiert Kennungen | mitigate | Bericht liegt unter `docs/` und damit im Bereich von `test_public_artifacts.py` (grün nachgefahren); Abschnitt 9 hält den Lauf vor dem Commit fest | closed |
| T-23-SC (08) | Tampering | Installs | accept | AR-23-04 | closed |
| T-23-32 | Information Disclosure | Store-Token/Schlüssel in Datei/Log | mitigate | `store-submit.yml:80,114,139` Token nur aus `secrets.APPSTORE_TOKEN` in env, `:97,:128,:152` nur im Header; `:165-167` `Remove the key files` mit `if: always()`; `release.yml:525-528` gleiches Aufräumen; Secret-Scan über Phasenordner, Auditbericht, store-listing.md: 0 Treffer; keine `.key`/`.pem` im Index | closed |
| T-23-33 | Spoofing | Paket ohne gültige Signatur | mitigate | `release.yml:358` und `:430` `openssl dgst -sha512 -sign`, `:371` und `:436` `-verify`; Log von Lauf 36292802211 per `gh run view --log`: `Verified OK` genau 2x | closed |
| T-23-34 | Tampering | Abbild ohne arm64 | mitigate | Audit Abschnitt 11 Zeile 4; vom Auditor anonym nachgefragt: `ghcr.io/street1983nk/findling_backend:1.3.0` ist `application/vnd.oci.image.index.v1+json` mit `linux/amd64` und `linux/arm64` | closed |
| T-23-35 | Repudiation | Abgabe ohne Belegkette | mitigate | Audit Abschnitt 11, Tabelle mit acht Zeilen, je Zahl, Laufnummer oder Wortlaut; Lauf 36304007154 `success`, Log `release findling v1.3.0: HTTP 201` und `release findling_backend v1.3.0: HTTP 201` nachgelesen | closed |
| T-23-36 | Denial of Service | Abgabe fällt in Flake | mitigate | `gh run list --commit 744d7e4`: sieben Push-Läufe, alle `success` (Release archives, PHP gates, Multi-arch, HaRP deploy, Python gates, Integration, Resilience); `git rev-list -n1 v1.3.0` = `744d7e4662af...` | closed |
| T-23-37 | Spoofing | Issue-Kommentar/Schließen ohne Freigabe | mitigate | Owner-Worte "Mit Zitatzeile" und "Offen lassen" (Audit Abschnitt 11); `gh issue view 14`: State `OPEN`, letzter Kommentar `street1983nk` 2026-09-27T07:44:41Z | closed |
| T-23-SC (09) | Tampering | Installs | accept | AR-23-04 | closed |

*Status: open / closed. Disposition: mitigate (Umsetzung nötig), accept (dokumentiertes Risiko), transfer (Dritte).*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-23-01 | T-23-03 | Ladefenster D-08: Der Warmlauf startet nach dem Antwortversand (`BackgroundTasks`), die erste Anfrage ist geschützt. Anfragen während des Sitzungsaufbaus warten am Schloss des Halters (onnxruntime hält den GIL) und können den 1,5-s-Deckel reißen. Kein lockfreier Schnellpfad, Owner hat den größeren Eingriff abgelehnt. Benannt in `docs/embeddings.md:824-832`, Test `test_embed_model.py:556` (`test_a_query_inside_the_load_window_waits_for_the_model_lock`), Audit Abschnitt 5.2 mit 669,6 ms auf CI; Zielhardware ungemessen (Audit Abschnitt 9). | Owner (D-08, 23-CONTEXT.md:32) | 2026-09-27 |
| AR-23-02 | T-23-05 | Die semantische Seite ändert nichts am ACL-Vorfilter und am PHP-Recheck; `git diff --stat 8b060e5..HEAD` über die vier Dateien der Berechtigungskette ist leer (vom Auditor nachgefahren), inhaltliche Lesung in Audit Abschnitt 3 V4. | Plan 23-01 (accept-Disposition) | 2026-09-27 |
| AR-23-03 | T-23-18 | Der einmalige Reparaturlauf nach dem Upgrade ist genau die Arbeit, die ohne #14 angefallen wäre; Queue drosselt über den normalen Poller, Bänder zu 1000. Preis in D-04 angenommen, Umfang auf fremden Instanzen ungemessen (Audit Abschnitt 9). | Owner (D-04, 23-CONTEXT.md:22) | 2026-09-27 |
| AR-23-04 | T-23-SC (01 bis 09) | Keine neue Abhängigkeit in der ganzen Phase: `uv.lock`-Diff ohne neues Paket, nur sechs Entfernungen; tokenizers 0.23.2 und numpy 2.5.2 standen schon im Lockfile und sind jetzt direkte Kanten (Audit Abschnitt 5.1, Zeile `pyproject.toml, uv.lock`). Keine PHP- oder npm-Abhängigkeit berührt. | Pläne 23-01 bis 23-09 (accept-Disposition) | 2026-09-27 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags

Keine. Die Threat-Flags-Abschnitte von 23-05, 23-06 und 23-09 melden ausdrücklich keine neue Angriffsfläche und verweisen nur auf registrierte IDs (T-23-16/17/19, T-23-21 bis 24, T-23-32 bis 37).

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-27 | 46 | 46 | 0 | gsd-security-auditor (opus), Stand HEAD e3f3b9e |

Hinweise des Auditors (nicht blockierend):
- Registerzählung: Die Pläne tragen 46 Einträge (37 nummeriert plus neun T-23-SC), nicht 43.
- Sechs SUMMARY-Dateien (23-01 bis 23-04, 23-07, 23-08) haben keinen Abschnitt `## Threat Flags` (Formfehler, keine neue Angriffsfläche gefunden).
- T-23-06: `uv lock --check` ist nur lokale Pflicht, kein CI-Gate; die Docker-Builds laufen mit `uv sync --frozen`, das eine Drift nicht meldet. Heute grün nachgefahren. Ein CI-Schritt `uv lock --check` in python.yml würde die Mitigation dauerhaft machen (Vorschlag, kein Befund).
- T-23-34 ist ein Prozessnachweis vor der Einreichung, kein Gate in store-submit.yml; der heutige Stand des Index wurde unabhängig bestätigt.
- F-23-04 (LOW, PathResolverService-LIKE-Muster) bleibt laut Owner-Wort im v1.4-Backlog; es ist eine Genauigkeitsfrage ohne Rechteüberschreitung und keinem offenen Threat zugeordnet.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-27
