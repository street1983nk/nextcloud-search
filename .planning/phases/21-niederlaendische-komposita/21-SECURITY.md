---
phase: 21
slug: niederlaendische-komposita
status: verified
threats_open: 0
asvs_level: 1
created: 2026-09-25
register_authored_at_plan_time: true
---

# Phase 21: Security

> Sicherheitsvertrag der Phase: Threat Register, akzeptierte Risiken und Audit Trail.
> Register vollständig aus den `<threat_model>`-Blöcken von 21-01-PLAN.md bis 21-09-PLAN.md übernommen (32 Threats: 29 mitigate, 3 accept).
> Jede Evidence ist am Baum vom 25.09.2026 (HEAD `cc56a63`, also EINSCHLIESSLICH der Review-Fixes 24c33fa..f6ea447) nachgeprüft, nicht aus den SUMMARY-Dateien übernommen. Die zentralen Testselektoren wurden vom Auditor nachgefahren (115 + 51 + 2 + 390 bestanden, keiner rot).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Volume `dict/nl-full.txt` zu Automat | Datei auf beschreibbarem Volume speist die Tokenisierung; Schutz ist der Digest-Vergleich (fail closed) | Wortliste, wird zu Tokenizer-Eingabe |
| Paketdatei `/usr/share/dict/dutch` zu Rezept | Eingabedaten aus dem Abbild, gehalten durch exakten Debian-Pin | Wortliste des gepinnten Pakets |
| Debian-Repo zu Abbild | `apt-get install wdutch=1:2.20.19+1-3` beim Image-Build, CI prüft Version, Zeilen, Bytes und Lizenzdatei am gepushten Digest | Paketinhalt |
| Store (state.db) zu Index-Tier | Siebte Marke `wordlist_hash_nl` reist wie die Sprachmarke: nie geseedet, nur hinter dem Verzeichnistausch gestempelt | Versionsmarke |
| Messskript zu Wegwerf-Container | `measure_compounds_nl.sh` mountet Eingaben `:ro`, nur der Ausgabepfad ist beschreibbar | Falllisten, Kennzahlen |
| CI-Sprachbeweis zu Testinstanz | Fall `nlc` lädt ein Dokument in die Wegwerf-Instanz und fragt über die normale Suchroute | Wegwerf-Zugangsdaten (CI-Kanarienwert) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation (Evidence) | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-21-01-01 | Denial of Service | Poller-Generationshub bei Band-Drift | mitigate | `open.py:323` filtert `answered_elsewhere`, `poller.py:356` übergibt `MARKS_A_REBUILD_ANSWERS`; Tests A bis C in `test_poller.py:2491/2520/2543` plus `test_a_dutch_drift_does_not_raise_the_generation` | closed |
| T-21-01-02 | Tampering | fullreindex-Ausweg gegen Fingerabdruck-Schutz | mitigate | Fallback ruft ohne Argument auf (`rebuild.py:1146`), Schutz `REBUILD_MARK == wanted` in `open.py` nach Z. 323; Test `test_the_full_reindex_way_out_raises_the_generation_once_per_drift` | closed |
| T-21-01-03 | Repudiation | fullreindex stempelt die Verzeichnismarken nicht | accept | Per Test festgeschrieben (`test_the_full_reindex_way_out_leaves_the_marks_of_a_directory_as_they_were`), dokumentiert in `docs/dutch-analyzer.md:166-181` (D-08) | closed |
| T-21-SC | Tampering | wdutch-Lieferkette (amd64 und arm64) | mitigate | `Dockerfile:237-244` (Pin `wdutch=1:2.20.19+1-3`), `docker.yml:298-336` prüft Version, Zeilen und Bytes am gepushten Digest, Matrix `docker.yml:73-79` | closed |
| T-21-02-01 | Tampering | Paketbezug ohne Versionsbindung | mitigate | Exakter apt-Pin in einer &&-Kette; Test `test_the_dutch_word_list_is_held_through_its_debian_pin` | closed |
| T-21-02-02 | Compliance | Lizenztext fehlt oder falsch ausgewiesen | mitigate | `Dockerfile:241-244` (`test -s`, `install -m 0444` für COPYING.wdutch), CI prüft die CC-BY-3.0-Zeile und Modus 444 (`docker.yml:322-336`) | closed |
| T-21-02-03 | Denial of Service | Interaktiver apt-Prompt haengt den Build | mitigate | `Dockerfile:238` `DEBIAN_FRONTEND=noninteractive` | closed |
| T-21-03-01 | Tampering | Artefakt `nl-full.txt` auf dem Volume manipuliert | mitigate | `wordlist_nl.py:235-247` (Digest-Vergleich, sonst Neubau aus der Quelle), Identitätsschlüssel mit Größe und mtime (Z. 204); durch CR-01 verstärkt: `errors="replace"` (Z. 158/168); Tests `test_a_tampered_artifact_is_rebuilt_from_the_source`, `test_the_mark_survives_undecodable_bytes_on_the_volume` | closed |
| T-21-03-02 | Tampering | Kette läuft mit fremdem Digest | mitigate | `analyzer.py:489-491` wirft ValueError (fail closed); Test `test_a_chain_for_a_digest_the_volume_does_not_hold_fails_closed` | closed |
| T-21-03-03 | Denial of Service | Zweiter Automat als Speicherlast | mitigate | `analyzer.py:483-484` (ohne nl kein Automat), Singleton Z. 456-461, Liste nach Bau freigegeben (D-02); durch WR-01 verstärkt: `_DUTCH_LOCK` (Z. 205, 485); Tests `test_the_dutch_automaton_is_built_once`, `test_four_threads_opening_with_dutch_at_once_build_one_automaton`, `test_the_list_is_not_held_after_the_digest_is_known` | closed |
| T-21-03-04 | Information Disclosure | `measure()` leakt Listeninhalte | mitigate | `wordlist_nl.py:302-318` gibt nur Zahlen und den Digest aus (T-02-14-Muster) | closed |
| T-21-04-01 | Tampering | Messumgebung weicht vom gepinnten Stand ab | mitigate | `measure_compounds_nl.sh:43,45` nennt die gepinnte Engine, Eingabe-Mounts `:ro` (Z. 96-99, 105, 145-146); Test `test_the_dutch_measurement_script_names_the_pinned_engine` | closed |
| T-21-04-02 | Information Disclosure | Sonde liest Produktivdaten | mitigate | `compound_probe_nl.py:35-36,212,257` liest nur Falllisten, Paketliste und `--against`; kein Zugriff auf state.db oder Index | closed |
| T-21-04-03 | Repudiation | Fixture weicht unbemerkt von der Vollliste ab | mitigate | `compound_probe_nl.py:249-261` vergleicht Token je Wort; `--against`-Lauf belegt in `docs/measurements/2026-09-komposita-nl/README.md:216-217` | closed |
| T-21-05-01 | Integrity | Saat schreibt die siebte Marke vor | mitigate | `repo.py:1593` `seed.pop(_DUTCH_MARK)`; Test `test_the_dutch_mark_is_never_written_by_the_seed` | closed |
| T-21-05-02 | Spoofing | Marke wird ohne Verzeichnistausch gestempelt | mitigate | Nur `open.py:412` (neues Verzeichnis) und `rebuild.py:948` schreiben die Marke, `stamp_after_rebuild` überspringt sie (`open.py:352,491`); Tests in `test_index_open.py:1221/1250` | closed |
| T-21-05-03 | Tampering | Legacy-Erkennung der nl-Liste fällt offen | mitigate | `repo.py:1509-1528`, vier Fälle in `test_the_dutch_exception_falls_closed` (`test_store_repo.py:465-471`) | closed |
| T-21-05-04 | Tampering | Upgrade-Gold verliert die Bestandszusage | mitigate | Gold-Kommentar `test_upgrade_compatibility.py:172-178` nennt beide Ausnahmen; Test `test_an_upgrade_without_dutch_moves_no_seventh_mark` | closed |
| T-21-06-01 | Spoofing | Umbau stempelt vor dem Tausch | mitigate | `rebuild.py:892` (`*, dutch_mark: str` ohne Default), Aufruf Z. 1302 erst nach `swap_in` (Z. 1278); Test `test_a_finished_rebuild_stamps_the_dutch_mark` | closed |
| T-21-06-02 | Denial of Service | nl-Drift löst Vollreindex aus | mitigate | `rebuild.py:243`, `poller.py:356`; Test `test_a_dutch_drift_does_not_raise_the_generation` | closed |
| T-21-06-03 | Tampering | Aufrufer lässt die Marke stillschweigend weg | mitigate | AST-Gates `test_every_caller_in_src_names_the_dutch_mark` / `_choice` mit Gegenproben `test_the_dutch_mark_gate_sees_a_caller_without_it` / `_choice_...` | closed |
| T-21-06-04 | Denial of Service | Unlesbare nl-Liste reißt Statusroute oder Start | mitigate | `resources.py:243,248-256` fängt `(OSError, UnicodeDecodeError)`, Leseseite fängt in `resources.py:714/754` `except Exception`; Test `test_an_unavailable_dutch_list_is_named_as_the_dutch_list` | closed |
| T-21-07-01 | Tampering | Registrierte Kette und Marke laufen auseinander | mitigate | Wie T-21-03-02; Digest kommt aus `dutch_digest_for`, derselben Quelle wie die Marke (`resources.py:714`) | closed |
| T-21-07-02 | Denial of Service | Bedingte Registrierung macht Bestandsindizes unlesbar | mitigate | `open.py:192` registriert ohne Bedingung, `EXPECTED_REGISTRATIONS = 8` (`test_index_open.py:587`); Test `test_open_index_registers_eight_chains_and_hangs_none_of_them_on_a_condition` | closed |
| T-21-07-03 | Denial of Service | Automat wird ohne aktives nl gebaut | mitigate | `test_without_dutch_no_dutch_automaton_is_built` (`test_index_open.py:841-842`), dazu `test_without_dutch_nothing_is_read` | closed |
| T-21-07-04 | Elevation of Privilege | Rechtegrenze verschiebt sich mit dem Schema | accept | Nachgeprüft: Schema-Diff gegen dd8e4d2 ändert nur Kommentare, kein neues Feld; die PHP-Nachprüfung bleibt die einzige Autorität | closed |
| T-21-08-01 | Repudiation | Kompositumfall beweist nichts (Vakuität) | mitigate | `deploy-harp.yml:912-928` (Querprobe), Z. 981 (Ein-Wort-Frage), Z. 1043-1047 (erster Treffer muss die eigene Datei sein); Kollisionsprüfung 21-08-SUMMARY:40 | closed |
| T-21-08-02 | Information Disclosure | Neuer CI-Fall trägt ein Geheimnis aus | accept | Nachgeprüft: Diff fügt nur Aufrufe nach bestehendem Muster `testuser:${TESTUSER_PASS}` hinzu (CI-Kanarienwert, Z. 263), kein neues Geheimnis | closed |
| T-21-08-03 | Tampering | Textgate zählt den fünften Fall nicht | mitigate | `PAGE_CALLS_EXPECTED = 5` (`test_language_proof_steps.py:122`); 30 Tests grün, darunter `test_a_compound_result_page_call_that_went_missing_is_reported` und `test_the_compound_case_that_lost_its_document_is_reported` | closed |
| T-21-09-01 | Repudiation | RAM-Posten ohne Rohdaten | mitigate | `rohdaten/ram.txt` (24,22/25,25/25,19) deckt sich mit `docs/performance.md:4407-4450`; 23-MB-Richtigstellung in Z. 4444 | closed |
| T-21-09-02 | Tampering | Zusicherung wird fürs Grünwerden geändert | mitigate | "Store upgrade 5" byte-identisch zu dd8e4d2 (sha256 vom Auditor geprüft, 356702...); laut 21-09-SUMMARY:96 kein roter Lauf (Prozesskontrolle) | closed |
| T-21-09-03 | Elevation of Privilege | Push ohne Owner-Freigabe | mitigate | 21-09-SUMMARY:82-83: Owner-Freigabe "approved" vor dem Push d074075..3563715 (Prozesskontrolle, nur als Protokoll belegbar) | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-21-01 | T-21-01-03 | Der fullreindex-Ausweg stempelt die Verzeichnismarken bewusst nicht; die Drift bleibt sichtbar und der Band-Umbau (Standardweg) ist die Antwort. Per Test festgeschrieben, in docs/dutch-analyzer.md dokumentiert (D-08, Owner-Entscheid Option 1 am 25.09.2026). | Owner (Checkpoint 21-01) | 2026-09-25 |
| AR-21-02 | T-21-07-04 | Das Schema bekommt kein neues Feld (Diff nur Kommentare); die Rechtegrenze bleibt allein die PHP-Nachprüfung, wie in allen Vorphasen. | Plan 21-07 (accept-Disposition) | 2026-09-25 |
| AR-21-03 | T-21-08-02 | Der fünfte CI-Fall nutzt ausschließlich den bestehenden Wegwerf-Kanarienwert `testuser:${TESTUSER_PASS}`; kein neues Geheimnis im Workflow. | Plan 21-08 (accept-Disposition) | 2026-09-25 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-25 | 32 | 32 | 0 | gsd-security-auditor (opus), Stand HEAD cc56a63 |

Hinweise des Auditors (nicht blockierend):
- 21-08-SUMMARY.md hat keinen Abschnitt `## Threat Flags` (Formfehler, keine neue Angriffsfläche).
- Der Ausgabe-Mount in `measure_compounds_nl.sh:100` ist beschreibbar, weil das Skript dort seine Ergebnisse ablegt; alle Eingaben sind `:ro`.
- Review-Befund IN-04 (`dutch_analyzer` umgeht die Schutzpfade von `snowball_analyzer`) ist bewusst offen dokumentiert (21-REVIEW.md), keinem Threat zugeordnet.
- CR-01 und WR-01 (Review-Fixes nach den SUMMARYs) verstärken T-21-03-01/-02/-03 und T-21-06-04; WR-02 verschiebt keine Mitigation.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-25
