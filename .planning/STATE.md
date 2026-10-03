---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: Leistungsprofile
status: executing
stopped_at: "28-07 Task 1: Blocker D-24-07 geloest (Quick 261003-d3y), naechster Executor-Lauf 7 der Kette"
last_updated: "2026-10-03T08:05:00.000Z"
last_activity: 2026-10-03
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 62
  completed_plans: 54
  percent: 67
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-27 after v1.3 milestone)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 28, Abnahme-Anfahrt

## Current Position

Phase: 28 (Abnahme-Anfahrt), in Ausführung
Plan: 7 of 14
Status: Executing (28-07: Blocker D-24-07 geloest per Quick 261003-d3y; naechster Lauf 7 der Kette)
Last activity: 2026-10-03

Progress: [█████████░] 87%

## Naechster Schritt

**28-07 Task 1: Executor-Lauf 7 der Kette (AWS-Login durch den Owner nötig).**
Owner-Entscheid 03.10. zu D-24-07 umgesetzt (Quick 261003-d3y, 52390ff7..3d1c6d72, NUR LOKAL):
die Probe prüft vor jeder Messung die Vorschlags-Schwellen (profile.suggest) und sagt
darunter nofit hardware_short ohne Messung; Zellen 3, 4 (m7g.large St-T/L-T) und 10
(c7a.xlarge L-T) gestrichen, Matrix 18 Zellen; 10-zelle.sh bricht bei hardware_short mit
74 ab. Für Lauf 7: LAUFWERTE ZELLEN ohne die gestrichenen Zellen setzen; das Abbild muss
den Probe-Fix tragen (neuer Digest), sonst misst die Box den alten Stand.

Vorgeschichte (Lauf 5, 02.10.):
Lauf 5 (02.10., Start 8, Kette 05:58:50Z): die Tor-Verschiebung 261002-af9 wirkt im Feld,
vorrat-tor altvorrat 0 BESTANDEN (05:59:00Z, zwischen Registrierung und Bewaffnung kann
kein Container nachschieben). Alle Tore bis zum Trigger grün (Grenze 2g/0, Baumhash ja,
Wirksamkeit economy slotsInForce 1). ABER: Zähltor nach 3600 s verfehlt mit 5041 statt
5000, Abbruch 71 um 06:59:16Z. Ursache belegt (243aabf9, 04-teilkorpus-arm.txt Lauf 5,
Dateiidentität gegen oc_filecache): der Teilkorpus selbst ist EXAKT vollständig
(vorrat 3535 + eingebettet 1465 = 5000); die 41 zuviel sind sämtlich Alt-Endzustände
AUSSERHALB des Teilkorpus in oc_findling_file_state (35 skipped + 6 failed: 20x too_large
loadtest/drill-CSVs, 9x Beispieldateien der Homes, 12x sprachfall corpus/*; updated_at
30.09./01.10., kein Eintrag unter files/teilkorpus). Diese Tabelle gehört der PHP-Hälfte
und überlebt --rm-data UND --restart (93i räumt nur oc_findling_queue); das Zähltor
summiert die globalen Zähler übersprungen/fehlgeschlagen mit. Die Formel aus 261001-vl0
war an Lauf 2 kalibriert, wo die 41 eine Crawl-Lücke zufällig exakt füllten. Optionen
für den Owner (Werkzeugänderung nur mit Owner-Wort, Runbook 7.1): a) Zähltor zählt nur
Zustände von Dateien unter files/teilkorpus (Pfadfilter im Werkzeug, kein Produkteingriff,
empfohlen), b) Produkt-Fix: --restart räumt auch oc_findling_file_state (Verlängerung
von 93i, ändert den Notfallhebel), c) oc_findling_file_state vor dem Kettenstart von
Hand leeren (Eingriff in Produktzustand). Stand: Box-Klon auf fcbb1273, Box von innen
gestoppt (shutdown 07:09:39Z, Stopp-Verhalten belegt) bei 3,21 USD (Deckel 59,43).
ACHTUNG: aws_box.sh stop steht aus, die AWS-Sitzung ist abgelaufen (Owner loggt ein);
BOX_STOPPED_ISO fehlt in box.env, Stoppzeit 07:09:39Z steht in 90-kosten.txt.

(28-06 fertig: S-voll 19,58 h, C1 743,9 MB innerhalb, Box geparkt; Owner-Signal "weiter".
28-05 fertig: Owner-Freigabe 30.09.2026, Deckel 119,82 h / 59,43 USD mit Anker, Timer 71,32 USD, Guthaben 104,11 USD; cb49fa70. 28-01 fertig: Teilkorpus, Rechenblatt, Slotkosten,
00-ablauf.md; b8e8c785. 28-02 fertig: 11-probe-route.py, 10-zelle.sh, 93b-nullstand.sh,
00-kette.sh, 59 boxlose Tests; 1976584a. 28-03 fertig: aws_box.sh Satztabelle/Architektur/
SG-Schonung, 00-typwechsel.sh mit Zieltyp; b1191dc5. 28-04 fertig: Runbook x86/USD-Deckel/
Abbau bis 0 Snapshots, Vorprobe "postgres ja abbilder ja"; 9d08f30f. Alles nur lokal).

Phase-27-Abschluss (2026-09-29): 16/16 Plaene in 7 Wellen; Owner-Abnahmen 27-01, 27-15
(gemeinsam per Playwright) und Phase ("ok abgenommen"); Push-Entscheid "push-now" =
106 Commits (d91305df..a8e3d7ea), HaRP-Routen-Ratsche um /probe und /probe/state
erweitert (2b9de323); Code-Review 1C/11W/7I, 12/12 gefixt (918f340d..d25c85e8);
Verifikation human_needed 4/4; zweiter Push bis c87a0239, alle sechs Workflows gruen
(PHPUnit 36596834116). Offen: fp32-Zweig nur automatisiert belegt; MT-Uebersetzungen
WR-02/WR-10 beim Release-Text lesen; WR-04-Rest (no_text_layer in "Uebersprungen")
nach Phase 29 verschoben. Quick 260929-kii (Deckungsgrad-Nenner) mitgereist.

Phase-26-Abschluss (2026-09-29): 14/14 Plaene in 6 Wellen, Verifikation passed 4/4;
Push-Entscheid Owner "Ja" = 229 Commits gepusht (cce78abd..d91305df), CI komplett gruen:
SC2-Kill-Test (Lauf 36522819711), PHPUnit 386 Tests (36522819728, erledigt auch
24-HUMAN-UAT Test 1 und die 25-03/25-04-Posten), arm64-Messleiter (36523219615,
Faktoren 2,000/1,979 gegen 1,05, Gesamt 3,958 = W4-Obergrenze, kein K1-Rueckfall).
Code-Review 1C/2W/4I: CR-01 halt-Rennfenster (91fefe8f), WR-01 unlock_held im
Catch-all (777f3a59), WR-02 Merker-Reihenfolge (15eb03d5) alle GEFIXT mit RED-Beleg;
IN-01..04 dokumentiert offen. Owner-Abnahmen: Latenzprobe D-26-12 (nice kappt
Ausreisser, p50/p95 unveraendert, Zahlbeleg-Grundlage fuer Issue #19) und Phase 26
gesamt. Entscheide D-26-01..16 in 26-CONTEXT.md. Commits nach dem Push wieder NUR LOKAL.

Phase-25-Abschluss (2026-09-28): 12/12 Plaene, Code-Review 0C/4W/4I, alle 4 Warnings
gefixt (00ecee3, 25ec895, 8ca5983, be2779c); Verifikation passed 4/4; Suite 3711 gruen.
fp32-Release model-e5-small-fp32-614241f live und immutable (Upload durch Orchestrator
im Owner-Auftrag, Gegenprobe committet). Entscheide D-25-01..15 in 25-CONTEXT.md.

Phase 24 secure (2026-09-28): SECURED 24/24 (22 mitigate, 2 accept AR-24-01/02), 29a6cd6.
AR-24-02 (Schreibweg nur occ) verliert mit der Schreibroute in Phase 27 seine Begruendung.

Phase-24-Abschluss (2026-09-28): Code-Review 0C/2W/6I, WR-01 (637c02b) und WR-02 (d0705e4)
gefixt; Verifikation 5/5 Kriterien (human_needed); Live-UAT bestanden mit einem Befund
(memory.max ueber MemTotal hob die Profilschwelle an), gefixt in b345fa3. Offen in
24-HUMAN-UAT.md nur Test 1: PHPUnit (php.yml) nach dem naechsten Push, Push-Entscheid beim Owner.

## Accumulated Context

### Entscheidungen

Volle Liste in PROJECT.md (Key Decisions) und .planning/milestones/v1.3-ROADMAP.md.
Fuer v1.4 unmittelbar tragend:

- Kein Vorwaermen beim Start, Ladefenster-Restrisiko akzeptiert (D-03/D-08, AR-23-01);
  ein Schnellpfad in model.py ist bewusst NICHT gebaut.

- dismax ist auf Messbasis verworfen (MESS-09); die Rangprobe-Grenze 0,81 steht in
  docs/language-analyzers.md.

- Sprachmenge ist sechster Versionsmerker, wird nie gesaet; Schema-1-Bestand ist designierter
  Zwischenzustand, keine Drift (Debug upgrade5, vierte Ausnahme in version_mismatch).

- Store-Regeln: eine Messzahl (730,2 MB), Gate test_store_metadata.py (RESIDENT_FIGURE),
  Tag im Store nie verschieben (v1.3.0 liegt auf 744d7e4).

- Roadmap v1.4 (27.09.): Reihenfolge 24 -> 29 streng seriell als Sicherheitsbedingung
  (MOD-01 vor jedem Modellschalter, H1 vor H2, N-Slot-Probe nach H2, Abnahme-Anfahrt vor
  Release). Rueckfall bei K1: Phase 26 schrumpft auf Befund, Entscheid datiert vor H2-Bau.

- 28-01 (29.09.): Teilkorpus-Bereiche und Seitenziehung als Kopie im Box-Skript (kein Pillow,
  kein sys.path), per Test gegen build_load_corpus gepinnt. Rechnung_anon zaehlt Gewichte,
  Schneider und eine Aktivierung nicht doppelt (in MAIN_PROCESS_BASELINE_BYTES aus B2),
  Spurreserve abgezogen. Deckel-Vorschlag 58,74 USD, mit Anker-Zelle 59,43 USD (Saetze
  29.09.), Freigabe durch den Owner offen (SC1, Checkpoint C1).

- 28-02 (29.09.): Zelle nutzt 93b-nullstand.sh (vier Quellen ohne Neuaufbau) statt
  93-nullstand.sh, weil 93 den Vorrat vor Probe und Wirksamkeit fuellte (Pitfall 2).
  Ende der Zelle zusaetzlich indexed > 0. Kette: Deckel vor jeder Zelle ohne shutdown
  (83, Box laeuft weiter), Timer bei Deckel x 1,20 bleibt stehen, fehlgeschlagene Zelle
  beendet die Kette (84) und zieht den Timer auf 60 min vor; Marke VORPRUEFUNG=stop-ja
  als Laufwert von Hand nach 00-typwechsel.sh vorpruefung.

- 28-03 (30.09.): aws_box.sh rechnet mit dem Satz des Typs aus describe-instances (Tabelle
  der sechs Typen, Preiskarte 29.09.); Typ ohne Satz: stop parkt trotzdem, schreibt keine
  Kostenzahl, endet 1. destroy schont bei geteilter Security Group auch das Schluesselpaar
  und nimmt die andere Instanz samt Volumes aus dem Tag-Sweep. 00-typwechsel.sh: nur
  innerhalb einer Familie (54), ohne Kapazitaet Typ zurueck und Box gestoppt (55), kein
  Rueckfall. Zone in aws_box.sh bleibt fest eu-central-1c (A7 offen fuer 28-05).

- 28-04 (30.09.): lokale Vorprobe arm64 nach amd64 (qemu, containerd-Store): postgres:18.6
  startet mit arm64-Datenverzeichnis, amcheck und REINDEX sauber, Signedness signed;
  amd64-Variante wird zu arm64-Tag nachgezogen. Ergebnis "postgres ja abbilder ja", Tor auf
  der Box bleibt Pflicht (AIO-glibc nicht geprueft). Runbook: Deckel in USD je Box-Satz,
  Block 7b fio, Block 14 x86-Box mit Tor 1 h 30, 7.3 Kette, Abbau bis 0 Snapshots
  (Snapshot erst nach SC4 und Owner-Wort C6). Zone 1c fuer c7a = Pruefpunkt Block 14 Schritt 0.

### Termine und Owner-Checkpoints

- **Issue #14 (budachst):** Antwort mit Zitat gepostet (issuecomment-5853918446), Issue bleibt
  OFFEN, bis budachst nach dem Upgrade bestaetigt. Nicht selbst schliessen (Owner-Regel).

- **Kill-Kriterium:** Ende September einmalig die Nextcloud-Conference-Nachberichte ansehen,
  danach quartalsweise. Zuletzt geprueft 21.09.2026: NICHT ausgeloest.

- **Findling-Pro-Entscheid:** vertagt auf 03.11.2026 (Go-Kriterium >=10 Grenzen-Anfragen oder
  1 Pilotkunde >250 Nutzer; Stand 21.09.: null Signale).

- **Korpus-Snapshot snap-03f1d1d9ad9262704:** bleibt im Standard-Tier (~2,85 USD/Monat,
  dritter Behalten-Entscheid); naechste Wiedervorlage beim v1.4-Close.

### Offene Blocker

- **GELOEST 03.10. (Quick 261003-d3y): Owner-Entscheid P2 + Zellen 3/4/10 gestrichen.**
  Probe prüft die Vorschlags-Schwellen (nofit hardware_short), Zellenwerkzeug Abbruch 74.
  Ursprünglicher Befund:
- ~~**28-07 Zelle St-T, Abbruch 69 (Lauf 6, 02.10.):**~~ Probe sagt fits (2,03 GB verfuegbar,
  1,61 GB noetig), Profil standard gespeichert, wirksam blieb economy: profile.effective()
  deckelt auf suggest(), und suggest verlangt fuer Standard >= 6 GB UND >= 3 Kerne (Referenzbox:
  2 Kerne, 2 GB Grenze). Produktwiderspruch Probe vs. Wirksamkeit, auf der Admin-Seite sichtbar
  ("Fits" und zugleich "less hardware than the chosen profile needs"). Der geplante
  Erzwingen-Weg der Zellen 3/4 wird ebenso gedeckelt. Owner-Entscheid: Semantik D-24-07
  (Probe vor Schwelle oder Schwelle in die Probe) und Umgang mit den Zellen St-T/L-T auf
  m7g.large. Beleg 06545083, 04-teilkorpus-arm.txt Lauf 6. Box geparkt, 3,88 von 59,43 USD.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 261003-d3y | 28-07 D-24-07 P2: Probe prüft vor der Messung die Vorschlags-Schwellen über profile.suggest (nofit hardware_short, keine Pause/Download/Kinder), Ursache in PHP/JS/16 Katalogen; Zellen 3/4/10 gestrichen (18 Zellen), 10-zelle Abbruch 74 | 2026-10-03 | 3d1c6d72 | Done (4408 Tests grün, 2 lokale CRLF-Artefakte 11-probe-route.py; php -l = CI-Vorbehalt) | [261003-d3y-d-24-07-nachschaerfung-p2-probe-prueft-v](./quick/261003-d3y-d-24-07-nachschaerfung-p2-probe-prueft-v/) |
| 261002-cvf | 28-07 Zaehltor zaehlt zeit- und pfadscharf (Zaehlmarke vor dem Trigger, nur frische files/teilkorpus-Zustaende via psql; Beleg 5041 -> 5000, Kalibrierfalle 4959 -> 71) | 2026-10-02 | a2b0fcf9 | Done (545 Tests gruen) | [261002-cvf-zaehltor-teilkorpus-scharfe-zaehlquelle](./quick/261002-cvf-zaehltor-teilkorpus-scharfe-zaehlquelle/) |
| 261002-af9 | 28-07 Vorrats-Tor vor die Bewaffnung gezogen (Schritt vorrat-tor, Abbruch 73 beziffert Altbestand; 93b-rc-13 zurueckgebaut; Nachschub nach Bewaffnung bricht nicht mehr ab) | 2026-10-02 | c04e7431 | Done (543 Tests gruen) | [261002-af9-vorrats-tor-vor-die-bewaffnung-ziehen](./quick/261002-af9-vorrats-tor-vor-die-bewaffnung-ziehen/) |
| 261002-93i | 28-07 Blocker-Fix a+b: occ findling:index --restart raeumt den Arbeitsvorrat (QueueMapper/QueueService::clear(), Produkt-Fix fuer den Notfallhebel) + 93b-Nullstand urteilt ueber den Vorrat (rc 13) + 10-zelle Abbruch 73 vor Samplern/Trigger | 2026-10-02 | 599a74d2 | Done (65+477 Tests gruen; php -l/PHPUnit = CI-Vorbehalt) | [261002-93i-findling-restart-raeumt-arbeitsvorrat-nu](./quick/261002-93i-findling-restart-raeumt-arbeitsvorrat-nu/) |
| 261001-vl0 | 28-07 Zaehltor: Formel zaehlt eingebettet statt indexiert (Vorrat enthaelt offene Einbettungsauftraege), Leserace per Doppellesung stabilisiert, Beleg-Test 6937 -> 5000 + Positivkontrolle + Race-Test | 2026-10-01 | 6d114659 | Done (64 Tests gruen auf main) | [261001-vl0-findling-28-07-zaehltor-fix-formel-auf-e](./quick/261001-vl0-findling-28-07-zaehltor-fix-formel-auf-e/) |
| 260929-kii | Deckungsgrad-Nenner waechst mit neuen Dateien (ScanRecountJob, Nachzaehlung absolut, Satz statt Prozent bei Zaehler > Nenner) | 2026-09-29 | bbb4f406 | Verified | [260929-kii-deckungsgrad-nenner-waechst-mit-neuen-da](./quick/260929-kii-deckungsgrad-nenner-waechst-mit-neuen-da/) |
| 260929-s7p | Issue #14: Team-Folder-Dateien mit ACL als Mitglied lesen (ReaderContext), Datei-ID in der Fehlerliste, CI-Job team-folder-acl; Auslieferung als 1.3.1 | 2026-09-29 | 0556d06d | Needs Review (PHPUnit + CI-Job nach Push) | [260929-s7p-issue14-acl-reader-context](./quick/260929-s7p-issue14-acl-reader-context/) |

### Pending Todos

- 1 pending: Issue #18 Fix-Kandidaten einplanen (JPG-Verdikt, HEIF, Download-Groessenpruefung)
  -- wartet auf budachst-Antwort (issuecomment-5865917799), Slot-Entscheid beim Owner
  (.planning/todos/pending/2026-09-28-issue-18-jpg-verdikt-heif-download-fixes.md)

## Deferred Items

Aus Phase 23 (Details in phases-Archiv v1.3-phases/23-*/deferred-items.md):

- F-23-04 -> v1.4-Backlog.
- idle-Guard fuer EmbeddingModel.release() -> v1.4 (Mitnahme-Kandidat Phase 25, Plan-Schnitt prueft).
- IN-01..03 dokumentiert offen (23-REVIEW.md).
- Aufraeumen: Worktree nextcloud-search-worktrees/issue-14 plus Branch
  fix/issue-14-teamfolder-acl loeschen (Dateisperre pruefen).

Aeltere Merker:

- Zwei Prosastellen nennen noch `DEFAULT_FIELDS`: `store/repo.py:128` und `:1448`
  (naechster Plan, der repo.py ohnehin oeffnet, nimmt sie mit).

- Leerer Textauszug bei reinem Sprachfeld-Treffer (SnippetGenerator haengt an FIELD_BODY_DE,
  Annahme A5): seit v1.3 in der veroeffentlichten Grenzenliste; Behebung waere eigener Plan
  mit Owner-Entscheid.

- run-Block "Store upgrade 3" in deploy-harp.yml bei ~20,7k Zeichen: vor einem
  ${{ }}-Ausdruck dort erst kuerzen oder Werte per env:-Block hereinreichen.

- L-16-04-Kommentarfix beim naechsten Workflow-Plan (paths-Filter gilt nicht fuer Tag-Pushes).
- Systemplatten-Skripte Phasen 5-6.1: Repo-Aufnahme erst nach Geheimnis-Durchsicht.
- Estnischer Stemmer nicht verfuegbar: aktiv an die Buerokratt/OS2ai-Spur kommunizieren.
- Auditor-Hinweise aus 23-SECURITY.md (beide advisory): uv lock --check laeuft in keinem
  CI-Schritt; arm64-Manifestcheck war Einmal-Nachweis, store-submit.yml prueft ihn nicht selbst.

## Session Continuity

Last session: 2026-10-03T08:05:00.000Z
Stopped at: Quick 261003-d3y fertig (D-24-07 P2 umgesetzt); 28-07 Lauf 7 wartet auf AWS-Login des Owners
Resume file: None

## Operator Next Steps

- /gsd:execute-phase 25 (25-01 wartet auf den Owner-Upload)
- Push-Entscheid (alles lokal); nach dem Push php.yml pruefen (24-HUMAN-UAT Test 1)
