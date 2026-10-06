---
phase: 28
slug: abnahme-anfahrt
status: open
threats_total: 71
threats_closed: 70
threats_open: 1
asvs_level: standard
block_on: open_threats
register_authored_at_plan_time: true
created: 2026-10-06
---

# Phase 28: Security

> Sicherheitsvertrag der Phase: Bedrohungsregister, akzeptierte Risiken, Prüfpfad.
> Register aus den 14 `<threat_model>`-Blöcken von 28-01-PLAN.md bis 28-14-PLAN.md, T-28-01 bis T-28-71, ohne Dubletten (71 Einträge, 68 mitigate, 3 accept, 0 transfer).
> Jede Mitigation ist an Datei:Zeile, Rohdatei, Testname oder Commit am HEAD 1a115cd9 belegt; SUMMARY-Behauptungen gelten nicht als Beleg, sie zeigen nur, wo gesucht wurde.
> Gates am HEAD vom Auditor selbst gefahren (Windows, Git Bash, `PYTHONUTF8=1`): `test_public_artifacts.py`, `test_v14_teilkorpus.py`, `test_v14_typwechsel.py`, `test_v14_zelle.py`, `test_ops_scripts.py`, `test_store_metadata.py`, `test_config.py` 640 passed; `test_measurement_scripts.py`, `test_probe.py`, `test_profile.py`, `test_guard.py` 663 passed.
> Unabhängige Gegenprobe zum Gate (eigenes Muster, nicht das des Gates): über `docs/measurements/2026-10-abnahme-anfahrt/` keine öffentliche IPv4 (nur Docker-intern 172.18.0.x und 0.0.0.0), 0 Treffer für `i-`, `vol-`, `sg-`, `snap-`, `ami-`, `eni-`, `eipalloc-`, `AKIA`, `ASIA`, `ec2-*-*`; der einzige 12-stellige Treffer ist ein Baumhash-Präfix (README.md:70). Kennungen stehen als Platzhalter `<instanzkennung>`, `<volumekennung>`, `<sicherheitsgruppe>`, `<adresse-der-box>`, `<eigene-adresse>`, `<korpus-snapshot>`.
> **Box-Threats durch Abbau gegenstandslos:** Beide Boxen, Datenvolumes, Security Group, Schlüsselpaar, A-Record (28-10, `rohdaten/08-abbau-boxen.txt`) und der Korpus-Snapshot (28-13, `rohdaten/09-abbau-snapshot.txt`) sind abgebaut und zurückgelesen; Bestand über 17 Regionen 0 Instanzen, 0 Volumes, 0 Adressen, 0 Schlüsselpaare, 0 eigene AMIs, 0 Snapshots (09-abbau-snapshot.txt:101-103). Threats, deren Angriffsfläche eine laufende Box war (SSH, öffentliche Nextcloud, Daten auf der Box, Quota, Deckel), sind für die Laufzeit belegt und tragen zusätzlich die Disposition "gegenstandslos seit Abbau". Das ist keine Lücke.
> Abkürzungen: `M/` = `docs/measurements/2026-10-abnahme-anfahrt/`, `S/` = `M/skripte/`, `R/` = `M/rohdaten/`, Tests unter `backend/tests/`.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Repository -> öffentliches GitHub | alles unter docs/ und die Historie werden mit dem Push öffentlich | Rohdaten, Bericht, Commits |
| Rechenblatt -> Owner-Freigabe | eine falsche Zahl führt zu einem falschen Deckel | Sätze, Stunden, Deckel |
| Skript -> Nextcloud-Adminrouten | Admin-Sitzung mit requesttoken über das öffentliche Netz der Box | Passwort, Cookie |
| Kette -> Boxzustand | Timer und Stopp entscheiden über Kosten und Datenverlust | shutdown, Deckel |
| Entwicklungsmaschine -> AWS-API | Zugangsdaten des Kontos, kostenpflichtige und zerstörende Aufrufe | Credentials, Kennungen |
| Werkzeugausgabe -> Rohdatei | Kennungen dürfen nicht hinein | Terminal vs. Datei |
| Internet -> Box | öffentliche Nextcloud mit Admin unter loadtest.infranode.dev, SSH | HTTP, SSH |
| GitHub-Release / Registry -> Box | fp32-Datei, amd64-Abbilder | 470.268.510 Byte, Digests |
| DNS-Zone -> Internet | Record zeigt sonst auf eine fremd vergebene Adresse | A-Record |
| Messung -> Produktformel | falscher Wert verstellt Probe und Wächter auf allen Installationen | OCR_SLOT_COST_BYTES |
| Admin -> Profilwahl | Probe entscheidet, ob eine Stufe gespeichert wird | Verdikt |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status | Evidence |
|-----------|----------|-----------|-------------|------------|--------|----------|
| T-28-01 | Denial of Wallet | 02-rechenblatt.py | mitigate | Sätze als Daten, Test pinnt 45,18/58,74 USD, fehlender Satz bricht ab | closed | S/02-rechenblatt.py:25-27, :50, :67 (`EXIT_MISSING_RATE = 3`), :82 (`RATES_OF_29_09`); test_v14_teilkorpus.py:326-327, :331 `test_deckel_prints_45_18_and_58_74_with_the_rates_of_29_09`, :369 `test_a_missing_rate_ends_the_sheet_instead_of_counting_zero` |
| T-28-02 | Info Disclosure | 01-teilkorpus.py liste | mitigate | nur Dateiname, Bytes, sha256; NARROW_SCOPE_DIRS; Gate | closed | S/01-teilkorpus.py:239-253 (`name,bytes,sha256`, Prüfsumme); test_v14_teilkorpus.py:172-174 (`str(tmp_path) not in answer.stdout`); test_measurement_scripts.py:80, :112 (`V14_RUN_DIR` in `NARROW_SCOPE_DIRS`); test_public_artifacts.py:60 (`DOCS_DIR`), :737 |
| T-28-03 | Tampering | Teilkorpus-Auswahl | mitigate | feste Regel, Listen-Prüfsumme, Zähltor exakt 5000 | closed | S/01-teilkorpus.py:85-110 (feste Bänder über `allocate(50000)`, `SUBSET_FILES = 5000`), :253; test_v14_teilkorpus.py:131, :158, :240 `test_zaehltor_passes_exactly_5000`; M/teilkorpus-liste.txt (5.000 Zeilen, `listen-pruefsumme f6b3dd70...`) |
| T-28-04 | Repudiation | Erwartungen nachträglich angepasst | mitigate | 00-ablauf.md vor dem ersten Boxstart committet | closed | Commit b1d4cc16 (2026-09-30 15:14:14Z) vor LaunchTime 16:53:40Z (R/90-kosten.txt:5, :7). Einzige spätere Änderung 3d1c6d72 (03.10.) streicht nur Zellen 3, 4, 10 per Owner-Entscheid; Rechnung und Grenze der übrigen Zellen im Diff unverändert, Ursprung in der Historie lesbar |
| T-28-05 | Info Disclosure | 11-probe-route.py Passwort | mitigate | nur Datei/Umgebung, Argument verweigert, nie ausgegeben | closed | S/11-probe-route.py:156-160 (`refuse_password_arguments`), :163-175 (`FINDLING_ADMIN_PWFILE`, `FINDLING_ADMIN_PASSWORD`), :364; test_v14_zelle.py:346 `test_probe_route_refuses_a_password_as_an_argument`, :356 |
| T-28-06 | Info Disclosure | Cookie-Glas | mitigate | mkdtemp, Löschung per finally bzw. trap | closed | S/11-probe-route.py:374 (`tempfile.mkdtemp`), :386-387 (`finally: shutil.rmtree`); S/10-zelle.sh:244, :265, :267 (`trap aufraeumen EXIT`); S/93b-nullstand.sh:52-54; test_v14_zelle.py:368 `test_probe_route_removes_its_cookie_jar` |
| T-28-07 | Tampering | --rm-data gegen falsche Nextcloud | mitigate | Zählung genau eine unmittelbar davor, sonst eigener Code | closed | S/10-zelle.sh:324-328 (`nextclouds_zaehlen`), :369-371 (`abbruch 61`), :373 (`--rm-data` erst danach); test_v14_zelle.py:747 `test_cell_refuse_two_nextclouds_before_any_rm_data` (Rückgabe 61, kein `--rm-data`-Aufruf) |
| T-28-08 | Denial of Wallet | Kette über den Deckel | mitigate | Deckel-Prüfung vor jeder Zelle, Sicherheitstimer Deckel x 1,20 als shutdown -h, vorpruefung-Marke | closed | S/00-kette.sh:16-19, :179 (`VORPRUEFUNG=stop-ja` Pflicht), :214, :219-227 (`shutdown -h +minuten`), :272-280 (Prüfung je Zelle in der Schleife); test_v14_zelle.py:1258 `test_kette_timer_is_set_at_cap_times_1_20_and_the_end_stops_the_box`, :1323; Feld: `timer-gesetzt` je Kette in R/*/00-kette.txt |
| T-28-09 | Tampering | Datenverlust beim Deckel | mitigate | kein automatischer Abbau oder Stopp beim Deckel | closed | S/00-kette.sh:25-27 ("Die Box laeuft WEITER: kein shutdown, kein Abbau"), :280 (`00-DECKEL-ERREICHT`); test_v14_zelle.py:1276 `test_kette_deckel_starts_no_cell_and_does_not_stop_the_box`, :1366; keine AWS-Aufrufe in S/00-kette.sh, S/10-zelle.sh (grep 0) |
| T-28-10 | Info Disclosure | Rohdaten mit Kennungen | mitigate | Platzhalter, Gate beim Commit | closed | test_public_artifacts.py:737 grün am HEAD; unabhängige Gegenprobe siehe Kopf. Historie siehe AR-28-04 |
| T-28-11 | Repudiation | Messung der falschen Stufe | mitigate | Wirksamkeitstor vor dem Trigger, erzwungen-Markierung, waechter-absenkung | closed | S/10-zelle.sh:497, :511 (`erzwungen ja/nein`), :518-531 (`abbruch 69`), :707 (`waechter-absenkung`); test_v14_zelle.py:786 `test_cell_refuse_the_trigger_while_the_old_profile_is_in_force` (69), :820, :1081; Feld: `wirksamkeit ja` in allen 18 R/<typ>/<zelle>/10-zelle.txt |
| T-28-12 | Info Disclosure | AWS-Zugangsdaten | mitigate | nur Gesetztheit prüfen, nie ausgeben | closed | test_ops_scripts.py:727 `test_the_aws_tool_demands_both_credentials_and_never_prints_them` grün; R/01-vorbedingungen.txt:22 ("ausgabe nicht gedruckt") |
| T-28-13 | Denial of Wallet | falscher Satz in Kostenzeilen | mitigate | Satztabelle je Typ, unbekannter Typ bricht ab | closed | scripts/ops/aws_box.sh:192 (`INSTANCE_RATES`, sechs Typen), :219, :341, :739, :885; test_ops_scripts.py:1026, :1037, :1047, :1069 `test_the_aws_tool_ends_red_for_a_type_without_a_rate_and_prints_no_cost` |
| T-28-14 | Tampering | Typwechsel über die Architektur | mitigate | Wechsel über Familiengrenze verweigert | closed | S/00-typwechsel.sh:97, :122-125 (`familie`), :296-298 (Rückgabe 54); test_v14_typwechsel.py:341 `test_the_switch_refuses_to_cross_the_architecture_with_nothing_but_a_describe` |
| T-28-15 | DoS | gemeinsame SG beim ersten Abbau gelöscht | mitigate | destroy prüft weitere Instanzen, lässt Gruppe stehen | closed | scripts/ops/aws_box.sh:1252-1278 (`others`, "security group kept, still used by another instance"), :1332-1338; test_ops_scripts.py:1161 `test_the_aws_destroy_keeps_the_security_group_while_another_instance_uses_it`, :1180; Feld: R/08-abbau-boxen.txt:237. Gegenstandslos seit Abbau |
| T-28-16 | Tampering | shutdown als terminate | mitigate | vorpruefung verlangt stop, sonst 52 | closed | S/00-typwechsel.sh:20-26, :71, :273-283 (`exit 52`, `vorpruefung-stop-ja`); test_v14_typwechsel.py:280 `test_the_precheck_ends_with_52_when_a_shutdown_would_not_be_a_stop`; Feld: R/06-aufbau-x86.txt:53, :272 |
| T-28-17 | Info Disclosure | Kennungen in Rohdateien | mitigate | Werkzeugausgabe aufs Terminal, Rohdatei nur Stempel und Platzhalter, Gate | closed | R/90-kosten.txt:1-3 ("nur typen und zeiten, keine kennungen"); R/01-vorbedingungen.txt:14; test_public_artifacts.py grün; Gegenprobe siehe Kopf |
| T-28-18 | Info Disclosure | Runbook | mitigate | nur Platzhalter, Gate | closed | docs/runbook-messbox.md:504-540 (`<eigene-adresse>`), Block 14 (`<db-nutzer>`, `<datenbank>`, `<box>`); test_public_artifacts.py:737 (deckt `docs/` rekursiv) grün; IPv4-Treffer im Runbook nur deutsch formatierte Bytezahl (:750) |
| T-28-19 | Spoofing | SSH-Regel der x86-Box | mitigate | SG-Regel 22 nur eigene Adresse /32, Adresswechsel per start | closed | docs/runbook-messbox.md:1228 (Block 14, "SSH-Regel 22 nur auf `<eigene-adresse>/32`"); scripts/ops/aws_box.sh:959-988; R/06-aufbau-x86.txt:73. Gegenstandslos seit Abbau (SG `InvalidGroup.NotFound`, R/08-abbau-boxen.txt) |
| T-28-20 | Tampering | still falsches PostgreSQL nach Architekturwechsel | mitigate | Tor mit REINDEX und bt_index_check, Rückfälle, Vorprobe | closed | docs/runbook-messbox.md:1315-1342 (Schritt 5, Zeitdeckel, REINDEX, `bt_index_check`, Dump/Restore oder Harness B); R/00-vorprobe-x86.txt; R/06-aufbau-x86.txt:198-203 (656 B-Bäume rc 0 vor und nach REINDEX), :216 |
| T-28-21 | Denial of Wallet | Snapshot bleibt nach der Phase | mitigate | Abbau-Checkliste bis 0 Snapshots, Sweep 17 Regionen | closed | docs/runbook-messbox.md:2355 (Schritt 6b), :2383 (Schritt 7); R/09-abbau-snapshot.txt:29-34 (`InvalidSnapshot.NotFound`), :101-103 (0 Snapshots, 17 Regionen), Nachlesung Commit 4d468329 |
| T-28-22 | Tampering | Vorprobe-Pull fremder Abbilder | accept | siehe AR-28-01 | closed | R/00-vorprobe-x86.txt:5-7, :486-494 (nur offizielle Docker-Hub-Abbilder, lokal, aufgeräumt) |
| T-28-23 | Tampering | falsches Konto | mitigate | get-caller-identity gegen erwartetes Konto, Rohdatei ja/nein | closed | R/01-vorbedingungen.txt:18-25 (`konto-ist-erwartet ja`); R/09-abbau-snapshot.txt:15-16 |
| T-28-24 | Info Disclosure | Zugangsdaten, Kontokennung | mitigate | nur Gesetztheit, Kennungen nur aufs Terminal, Gate | closed | R/01-vorbedingungen.txt:7-14, :22, :77; test_ops_scripts.py:727; Gegenprobe (kein 12-stelliges Konto, kein AKIA/ASIA) siehe Kopf |
| T-28-25 | Denial of Wallet | Boxstart ohne Freigabe | mitigate | blockierender Checkpoint, keine Instanz vor dem Signal | closed | R/02-rechenblatt-freigabe.txt:118-121 (Owner-Signal wörtlich, Freigabezeile); R/01-vorbedingungen.txt:112-117 (0 Instanzen, 0 Volumes); Commit cb49fa70 16:49:42Z vor LaunchTime 16:53:40Z |
| T-28-26 | Denial of Wallet | veraltete Sätze | mitigate | Sätze am Tag neu gelesen, Deckel neu gerechnet | closed | R/02-rechenblatt-freigabe.txt:7-11 (`preis-gelesen 2026-09-30T16:17:39Z`), :36-37 (gerechnet mit Satzdatei der Tageslesung), :51-85 |
| T-28-27 | Spoofing | SSH-Zugang | mitigate | Regel 22 nur /32, privater Schlüssel nur lokal | closed | R/03-aufbau-arm.txt:17 (`tcp 22 <eigene-adresse>/32`); scripts/ops/aws_box.sh:973-978; Schlüsselpaar `InvalidKeyPair.NotFound` (R/08-abbau-boxen.txt:297). Gegenstandslos seit Abbau |
| T-28-28 | EoP | öffentliche Nextcloud mit Admin | mitigate | starke Passwörter, 80/443 nur AIO, kurze Laufzeit, Record nach Abbau entfernt | closed | R/03-aufbau-arm.txt:17-18 (22 /32, 80/443), :144-148, :179-181 (Passwortdateien 600, per stdin); R/08-abbau-boxen.txt:315-322 (Record gelöscht, Rücklesung 0, zwei Resolver NXDOMAIN). Gegenstandslos seit Abbau |
| T-28-29 | Info Disclosure | AWS-Zugangsdaten auf der Box | mitigate | nie auf die Box, AWS nur auf der Entwicklungsmaschine | closed | S/00-typwechsel.sh:5-6 ("NIE AUF DER BOX AUSFUEHREN"); box-seitige Skripte S/00-kette.sh, S/10-zelle.sh, S/93b-nullstand.sh, S/11-probe-route.py ohne `aws`/`AWS_` (grep 0); Box-Stopps von innen per shutdown, nicht per AWS (R/90-kosten.txt). Gegenstandslos seit Abbau |
| T-28-30 | Info Disclosure | Kennungen in Rohdaten | mitigate | Platzhalter, Gate vor jedem Commit | closed | Gate grün am HEAD, Gegenprobe siehe Kopf. Historie siehe AR-28-04 |
| T-28-31 | Denial of Wallet | Lauf über den Deckel | mitigate | Deckel-Prüfung, Timer x 1,20, Box nach der Zelle gestoppt | closed | wie T-28-08; S/00-kette.sh:297 (Kettenende `shutdown -h +2`); R/m7g.large/00-shutdown-beleg.txt; R/90-kosten.txt:164-170 (34,09 USD, Sicherheitstimer nie ausgelöst) |
| T-28-32 | Tampering | falsches Abbild gemessen | mitigate | Digest-Wechsel plus Baumhash im laufenden Container | closed | `abbild-digest` und `baumhash-beweis ja` in allen 18 R/<typ>/<zelle>/10-zelle.txt (6a0c13be für 1, 2; d33bfcae für 5, 6; 5ed5742c für 7 bis 21); R/40b-baumhash.txt, R/92d-wechsel.txt. Abweichung: drei Stände statt nur c87a0239, je Stand belegt (M/README.md Abschnitt 2) |
| T-28-33 | Info Disclosure | Daten auf der Box | accept | siehe AR-28-02 | closed | Korpus aus scripts/dev/build_load_corpus.py (synthetisch, T-05-18); Box und Snapshot gelöscht |
| T-28-34 | Info Disclosure | teilkorpus-liste.txt | accept | siehe AR-28-03 | closed | M/teilkorpus-liste.txt: Kopf `name,bytes,sha256`, 5.000 Zeilen, 0 Zeilen mit `/` |
| T-28-35 | Tampering | falsche Dateimenge | mitigate | Zähltor exakt 5000 | closed | S/10-zelle.sh:661-664 (`abbruch 71`); test_v14_zelle.py:875 `test_cell_teilkorpus_demands_the_count_gate`; Feld: `zaehltor bestanden 5000` in allen 17 Teilkorpus-Zellen |
| T-28-36 | Tampering | falsche Stufe | mitigate | Wirksamkeitstor, Abwärtsweg vor Nullstand, Markierung | closed | wie T-28-11; R/c7a.*/St-fp32-T/99-rueckkehr-int8.txt (Abwärtsweg belegt) |
| T-28-37 | Denial of Wallet | Deckel | mitigate | Prüfung je Zelle, Timer mit neuem Satz nach Typwechsel, Stopp nach Kette | closed | `kette-start ... satz <typsatz>` und `timer-gesetzt` je Typ in R/m7g.4xlarge/00-kette.txt, R/c7a.*/00-kette.txt (z. B. c7a.8xlarge satz 1.892121, 1491 min); `aws_box.sh stop` 06:15:06Z (28-07) |
| T-28-38 | Info Disclosure | Kennungen und Adresse | mitigate | Platzhalter, Gate | closed | HEAD sauber (Gate grün, Gegenprobe); Commits e66ef86a und 21721984 trugen zwei Box-Adressen in R/05-typwechsel-arm.txt, vom Gate beim nächsten Commit gefunden und in 147a6ed8 durch `<adresse-der-box>` ersetzt. Rest in der gepushten Historie: AR-28-04 |
| T-28-39 | Spoofing | SSH nach Adresswechsel | mitigate | start verschiebt die Regel, widerruft vor dem Autorisieren | closed | scripts/ops/aws_box.sh:973 (`revoke-security-group-ingress`) vor :976-978 (`authorize ... $owner/32`); test_ops_scripts.py:691 `test_the_aws_start_moves_the_ssh_rule_and_revokes_before_it_authorizes`. Gegenstandslos seit Abbau |
| T-28-40 | Tampering | fp32-Download | mitigate | Produkt prüft Größe und sha256, Rohdatei belegt | closed | backend/src/findling/embed/weights.py:52-53 (`FP32_SHA256`, `FP32_BYTES`), :68, :146-155; R/c7a.xlarge/St-fp32-T/ und R/c7a.4xlarge/St-fp32-T/: Fortschritt bis 470268510, `storedPrecision=fp32`, kein `wrong_digest` (grep 0) |
| T-28-41 | Tampering | Abbild auf x86 | mitigate | Multi-arch-Digest, Baumhash im Container | closed | R/06-aufbau-x86.txt:161, :262 (`baumhash-beweis ja`), :265 (amd64-Variante per Digest); 10-zelle.txt aller x86-Zellen `abbild-digest sha256:5ed5742c`, `baumhash-beweis ja` |
| T-28-42 | Tampering | defekte DB nach Architekturwechsel | mitigate | REINDEX, occ status, Stichprobe, Owner-Tor | closed | R/06-aufbau-x86.txt:4-6 (Owner-Weg x86-tor), :87, :198-206 (amcheck, REINDEX, occ status maintenance false), :216 |
| T-28-43 | Denial of Wallet | Tor läuft aus dem Ruder | mitigate | Zeitdeckel 1 h 30 | closed | docs/runbook-messbox.md:1315 (Zeitdeckel 1 h 30 min), :1339-1342; R/06-aufbau-x86.txt:216 (`bestanden dauer 45 min ... zeitdeckel 90 min`) |
| T-28-44 | DoS | vCPU-Quota | mitigate | ARM gestoppt vor x86-Start, Quota gelesen | closed | R/06-aufbau-x86.txt:18-19 (`quota-vcpu-standard 32.0`), :26 (m7g.4xlarge stopped). Gegenstandslos seit Abbau |
| T-28-45 | Info Disclosure | Kennungen, Adresse | mitigate | Platzhalter, Gate | closed | Gate grün, Gegenprobe siehe Kopf; R/06-aufbau-x86.txt:12 |
| T-28-46 | Spoofing | SSH | mitigate | gemeinsame SG mit Regel 22 nur /32 | closed | wie T-28-19, T-28-27. Gegenstandslos seit Abbau |
| T-28-47 | Denial of Wallet | c7a.8xlarge 1,89 USD/h | mitigate | Deckel je Zelle, Timer mit Typsatz, Stopp am Kettenende | closed | R/c7a.8xlarge/00-kette.txt (`satz 1.892121`, `timer-gesetzt minuten 1491`, `kette-ende ... bisher 34.0001`); R/90-kosten.txt:164 (34,09 USD gegen 59,43) |
| T-28-48 | DoS | Quota 32 vCPU | mitigate | ARM-Box gestoppt belegt vor dem Wechsel | closed | R/06-aufbau-x86.txt:26 (04.10.); keine eigene Statuszeile direkt vor dem c7a.8xlarge-Wechsel (28-09 Abweichung 5), indirekt belegt durch erfolgreichen Start mit voller Quota. Gegenstandslos seit Abbau |
| T-28-49 | Tampering | stiller Ersatztyp | mitigate | kein Rückfall-Typ, Owner entscheidet | closed | S/00-typwechsel.sh:14-15, :74 (55), :318-325 ("kein Rueckfall ohne Owner"); test_v14_typwechsel.py:365 `test_the_switch_without_capacity_leaves_the_box_stopped_and_falls_back_to_nothing` |
| T-28-50 | Info Disclosure | Rohdaten | mitigate | Platzhalter, Gate | closed | Gate grün, Gegenprobe siehe Kopf |
| T-28-51 | Repudiation | Kosten nach Abbau nicht belegbar | mitigate | Schlusszahlen vor dem Abbau committet | closed | R/90-kosten.txt:147-170 (Tabelle je Typ, Sicherheitstimer NEIN); Commit d4835808 (17:38:41Z) vor erstem destroy 17:38:46Z (R/08-abbau-boxen.txt:227, :232) |
| T-28-52 | Denial of Wallet | übrig gebliebene Ressourcen | mitigate | Tag-Sweep 17 Regionen, beide Tagwerte, Rücklesen | closed | R/08-abbau-boxen.txt:300-303 (terminated, `InvalidVolume.NotFound`), Sweep 17 x 2; R/09-abbau-snapshot.txt:37-103. Werkzeugrest: `aws_box.sh` cmd_destroy führt das gemeinsame Schlüsselpaar nicht in `shared` (:1277), erster destroy endete deshalb mit 1 (R/08-abbau-boxen.txt:253-261); Komfortfehler, Abbau selbst belegt, Deferred 28-10 |
| T-28-53 | Spoofing | verwaister A-Record | mitigate | Record entfernen, belegen | closed | R/08-abbau-boxen.txt:315-322 (Rücklesung 0 Records, NXDOMAIN zweier Resolver) |
| T-28-54 | Tampering | Abbau vor dem Sichern | mitigate | Owner-Checkpoint, Zahlen vorher committet, box.env-Sicherung | closed | R/08-abbau-boxen.txt:6 (Owner wörtlich "Ja, beide abbauen"), :45-55 (Sicherungen, cmp/sha256), :227; Commit d4835808 vor 754fa75c |
| T-28-55 | DoS | SG beim ersten Abbau gelöscht | mitigate | SG geschont, x86 zuerst | closed | R/08-abbau-boxen.txt:232-237 (x86 17:38:46Z, "security group kept"), :275 (ARM 17:40:00Z); aws_box.sh:1252-1278 |
| T-28-56 | Info Disclosure | Kennungen im Abbau-Protokoll | mitigate | Platzhalter, Gate | closed | R/08-abbau-boxen.txt:237, :247 (`<instanzkennung>`, `<volumekennung>`), :55; Gate grün |
| T-28-57 | Tampering | Erwartung nachträglich angepasst | mitigate | Rechnung aus 00-ablauf.md, Urteil aus 12-slotkosten.py | closed | M/auswertung.txt (Rohausgaben `12-slotkosten.py slots/rechnung/fp32` im Anhang); 00-ablauf.md siehe T-28-04 |
| T-28-58 | Repudiation | Owner-Entscheid nicht nachvollziehbar | mitigate | Signal wörtlich, datiert | closed | M/README.md:386-391 (Abschnitt 14, 05.10.2026, Signal wörtlich); 28-11-SUMMARY.md Task 2 |
| T-28-59 | Info Disclosure | Kennungen im Bericht | mitigate | Gate | closed | Gate grün; M/README.md:70 nur Digests und Baumhash-Präfixe |
| T-28-60 | Tampering | Store-Zahl still geändert | mitigate | test_store_metadata.py grün, nur per Owner | closed | test_store_metadata.py:356 (`RESIDENT_FIGURE = "730.2"`), grün am HEAD; Owner "store=kein Fall" (M/README.md:391) |
| T-28-61 | DoS | zu niedriger Slot-Kostenwert, OOM | mitigate | Owner-bestätigter Wert, Probe nimmt max(gemessen, Konstante) | closed | backend/src/findling/config.py:886-896 (`OCR_SLOT_COST_BYTES = 250 * MIB`, Quelle und Owner-Datum), :933, :945 (Reserven folgen); backend/src/findling/probe.py:217 (`cost = max(slot_cost, OCR_SLOT_COST_BYTES)`), :288; test_probe.py, test_guard.py, test_profile.py grün. Abweichung vom Planwortlaut: nicht "Maximum des VmHWM-Paars" (448 MiB), sondern 250 MiB nach Tragekriterium, weil B2 ein RssAnon-Paar ist (28-11 Abweichung 4); Owner-Entscheid M/README.md:391. Rest: AR-28-05 |
| T-28-62 | Tampering | Tests nur mechanisch angepasst | mitigate | Erwartungen neu gerechnet, keine Tests gelöscht | closed | Commits 2f26d9fb und e3d28dfd: 0 entfernte `def test_` (git show); Rechenwege in test_profile.py (28-12-SUMMARY nennt Stellen, im Diff geprüft); RED-Commits 66bf7a44, 655cd037 vor GREEN |
| T-28-63 | Repudiation | Baumhash driftet unbemerkt | mitigate | Pin neu gemessen mit Kommentar, PHP-Pin unverändert | closed | test_measurement_scripts.py:1602 (`PACKAGE_TREE_HASH_TODAY`, über 27db8b41 in 2f26d9fb zu fc0576e7 in e3d28dfd), :776 (`PHP_TREE_HASH_TODAY` seit 13993fd9 unverändert); grün am HEAD |
| T-28-64 | EoP | "nicht anbieten" still umgesetzt | mitigate | Owner-Checkpoint vor jeder php/-Änderung | closed | Owner wählte für alle sechs Fälle "nachziehen", keine Stufe gestrichen (M/README.md:391); `git diff --stat 18602c48 HEAD -- php` leer. Gegenstandslos mangels Fall |
| T-28-65 | Tampering | Löschung im falschen Konto oder zu früh | mitigate | Owner-Checkpoint nach SC4, get-caller-identity | closed | R/09-abbau-snapshot.txt:15-16 (`konto erwartet ja` 19:10:29Z vor delete 19:10:41Z); Owner wörtlich "Loeschen" (28-13-SUMMARY); SC4 vorher (M/README.md Abschnitt 14) |
| T-28-66 | Denial of Wallet | Restkosten | mitigate | Sweep 17 Regionen, beide Tagwerte, alles 0 | closed | R/09-abbau-snapshot.txt:37-103 (sechs Zahlen 0 über 17 Regionen, ungefiltert), :131-134 (Nachlesung, Commit 4d468329) |
| T-28-67 | Info Disclosure | unverschlüsselter Snapshot | mitigate | Inhalt synthetisch, Löschung mit Nachweis | closed | R/09-abbau-snapshot.txt:29-34 (`InvalidSnapshot.NotFound` zweimal); Korpus synthetisch (T-05-18) |
| T-28-68 | Info Disclosure | Kennungen in Rohdatei | mitigate | Platzhalter, Gate | closed | R/09-abbau-snapshot.txt:10 (`<korpus-snapshot>`, Konto nur ja/nein); Gate grün |
| T-28-69 | Info Disclosure | ungewollter Push | mitigate | Push nur nach checkpoint:decision, weitere Pushes nur mit erneutem Owner-Wort | **open** | Belegt: C7 wörtlich "Pushen wie es ist" (28-14-SUMMARY.md:40-46) für die Schübe 18602c48..ab634401 und ab634401..42e07168. **Nicht belegt:** (1) dritter Push aae091bd..1a115cd9 (reflog `origin/main@{0}: update by push`, Commits 4d468329, 5eb99faa, 688617bc, 1a115cd9); 28-14-SUMMARY.md:52 kündigt ihn "nach Owner-Wort" an, ein Owner-Wort dafür steht in keinem Artefakt. (2) Squash-Merge von Dependabot-PR #24 (aae091bd) auf GitHub, vom Wortlaut "Pushen wie es ist" nicht erkennbar gedeckt |
| T-28-70 | Info Disclosure | Kennungen in gepushten Rohdaten | mitigate | Gate vor jedem Commit, lokal grün vor dem Push | closed | Gate am HEAD grün (55 Tests in test_public_artifacts.py, Teil der 640); 28-14-SUMMARY lokale Gates grün vor Push. Gate war bei e66ef86a und 21721984 rot (zwei Box-Adressen, R/05-typwechsel-arm.txt) und in .planning/STATE.md (f432c5c7, außerhalb des Gate-Bereichs) stand eine Adresse; alle drei Commits sind gepusht. Bewusst akzeptiert: AR-28-04 |
| T-28-71 | Repudiation | offene Belege als erledigt gemeldet | mitigate | offene Belege als human_needed, Abnahme-Checkpoint | closed | 28-14-SUMMARY.md SC4 "human_needed für Feldbeleg und Laufzeit", SC3 Restpunkte; Owner-Abnahme wörtlich "approved" 06.10.2026 mit Liste der offenen Punkte (28-14-SUMMARY.md, Abschnitt Owner-Abnahme) |

*Status: open, closed. Disposition: mitigate (Umsetzung nötig), accept (dokumentiertes Risiko), transfer (Dritter).*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-28-01 | T-28-22 | Die lokale x86-Vorprobe zog nur offizielle Docker-Hub-Abbilder (`postgres:18.6`, `busybox:1.37`, `alpine:3`), ohne veröffentlichten Port, mit Speichergrenze, auf der Entwicklungsmaschine (R/00-vorprobe-x86.txt:5-7). Container, Volume, `postgres:18.6` und `busybox:1.37` sind entfernt; die arm64-Variante von `alpine:3` blieb, weil ein anderes lokales Abbild sie teilt (:486-494). Kein Fremdcode erreicht Box oder Repository. | Owner (Plan 28-04, Register zur Planzeit) | 2026-09-29 |
| AR-28-02 | T-28-33 | Der Korpus auf der Box ist synthetisch (scripts/dev/build_load_corpus.py, T-05-18), keine Nutzerdaten. Box, Volumes und Snapshot sind gelöscht (R/08-abbau-boxen.txt, R/09-abbau-snapshot.txt). | Owner (Plan 28-06, Register zur Planzeit) | 2026-09-30 |
| AR-28-03 | T-28-34 | teilkorpus-liste.txt trägt nur synthetische Dateinamen, Bytes und sha256 (D-02 Phase 5), keine Maschinenpfade (0 Zeilen mit `/`). | Owner (Plan 28-07, Register zur Planzeit) | 2026-10-01 |
| AR-28-04 | T-28-38, T-28-70 (Rest) | Drei gepushte Commits (e66ef86a, 21721984 unter docs/, f432c5c7 in .planning/STATE.md) tragen öffentliche Adressen der Messboxen; am HEAD sind sie durch Platzhalter ersetzt. Die Adressen gehörten AWS-Instanzen, die abgebaut und deren Adressen an AWS zurückgegeben sind (R/08-abbau-boxen.txt, R/09-abbau-snapshot.txt:102: 0 Adressen in 17 Regionen); der A-Record ist entfernt. Der Owner entschied am Checkpoint C7 in Kenntnis genau dieses Punkts, ohne Historien-Umschreibung zu pushen. Hinweis: .planning/ liegt außerhalb des Gates test_public_artifacts.py. | Owner, C7 wörtlich "Pushen wie es ist" (28-14-SUMMARY.md:40-46) | 2026-10-05 |
| AR-28-05 | T-28-61 (Rest) | `OCR_SLOT_COST_BYTES` = 250 MiB ist nur rechnerisch und per Test belegt, kein Feldlauf mit dem neuen Wert; Zelle 11 liegt genau an der Grenze 1,100; der Vollindex-Term (`MAIN_PROCESS_PER_FILE_BYTES`, config.py:910) ist ohne Laufzeit-Verdrahtung. Schutznetz im Code bleibt: Probe rechnet mit max(gemessen, Konstante) (probe.py:217), Wächter mit Reserve 250 MiB (config.py:945). Als Phase-29-Kandidaten notiert. | Owner, Abnahme wörtlich "approved" mit diesen offenen Punkten (28-14-SUMMARY.md, Owner-Abnahme) | 2026-10-06 |

*Akzeptierte Risiken tauchen in späteren Audits nicht erneut auf.*

---

## Unregistered Flags

Keine. Die Threat-Flags-Abschnitte in 28-01, 28-02, 28-03, 28-04 und 28-10-SUMMARY.md melden keine neue Fläche und verweisen nur auf registrierte IDs; 28-05 bis 28-09 und 28-11 bis 28-14 haben keinen Threat-Flags-Abschnitt (28-07, 28-08, 28-09 sind rückwirkende Close-outs vom 05.10.2026 aus Rohdaten und Commits).

### Informative Beobachtungen (keine neue Angriffsfläche, keine Blocker)

- **I-1 (28-06, 28-10):** AWS-Zugang per `aws configure export-credentials` in die Umgebung, in 28-10 über einen temporären, nicht committeten Wrapper, der Kennungen in der Ausgabe ersetzt. Gleicher Pfad wie T-28-12/T-28-24, nichts davon im Repo (Gegenprobe AKIA/ASIA 0).
- **I-2 (28-06):** Cloudflare-A-Record per Zonen-API je Start umgesetzt; Endzustand entfernt (T-28-53).
- **I-3 (28-08/28-09):** Box lief auf 5ed5742c (Multi-Arch zu 18602c48) statt c87a0239; durch T-28-32/T-28-41 je Zelle belegt.
- **I-4 (28-14):** Workflow "PHP and store metadata gates" lief auf dem Phasenstand nicht (Pfadfilter); `php/` seit 18602c48 unverändert, letzter grüner Lauf 37176289202.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-06 | 71 | 70 | 1 | Claude (gsd-security-auditor) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [ ] `threats_open: 0` confirmed (offen: T-28-69)
- [ ] `status: verified` set in frontmatter

**Approval:** offen. T-28-69 schließt, sobald das Owner-Wort für den dritten Push (aae091bd..1a115cd9) und für den Dependabot-Merge #24 wörtlich und datiert in 28-14-SUMMARY.md steht, oder der Owner beides nachträglich bestätigt und das dort vermerkt ist; danach /gsd:secure-phase 28 erneut.
