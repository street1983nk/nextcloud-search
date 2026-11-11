---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 25
subsystem: scripts/ci (Abnahmetest D-43-08)
tags: [D-43-08, D-43-15, D-43-17, OE-2, OE-3, W4, W5, B5, harness, physical-truth]
requires: [43-24]
provides: [Topologie mit Unterwurzeln, anderer Schreibweise, vier gehashten Speicher-IDs, Zwillingen, Linkfreigabe und homes, Anlage-Protokoll mounts.tsv, physische Wahrheit über dev:ino, erwartete Abweichung k=4, Positivkontrolle 3 mit Soll 16, Suchprobe W5, docKeyFormat 2 im Body von POST /coverage nur für den Container des Kopfes, scripts/ci/e2e_head_proof.sh mit Selbsttest]
affects: [43-26, 43-27, 43-12, 43-13]
tech-stack:
  added: []
  patterns: [Wahrheit über Inode statt über Speicher-ID, Serverpfad aus testparm und Anlage-Protokoll, Konstanten mit Herleitung von Hand, Prüfskript mit Selbsttest gegen ein gh-Double]
key-files:
  created:
    - scripts/ci/e2e_head_proof.sh
    - scripts/ci/e2e_head_proof_selftest.sh
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-25-SUMMARY.md
  modified:
    - scripts/ci/coverage_e2e.sh
    - scripts/ci/coverage_truth.sh
decisions:
  - "Ein Host-Alias für alle Mounts (38 Zeichen, /etc/hosts): nur so bleibt die Freigabe für das Produkt dieselbe; mit 127.0.0.1 neben einem Alias wären es für das Produkt zwei Freigaben und die Anzeige läge zu Recht über der physischen Wahrheit. Die Länge ist so gewählt, dass Wurzel / (58) und Wurzel projekt (64) ausgeschrieben bleiben und Wurzel sicherheit (ab 67) gehasht wird"
  - "Vier gehashte Fälle statt der drei aus dem Aktionstext (must_have und verify nennen vier): password::password mit user bob für carol, password::logincredentials für alice und carol, password::global mit dem Samba-Konto dglobal für alice, password::userprovided mit dem Samba-Konto deigen für bob. Die zwei nicht auflösbaren brauchen ein Anmeldekonto ungleich dem Nextcloud-Nutzer, sonst träfe der md5-Nachbau über oc_mounts.user_id"
  - "Zugangsdaten für global und userprovided über ICredentialsManager unter den Namen aus GlobalAuth.php und UserProvided.php (kein Browser, derselbe Aufruf wie hinter den Einstellungsseiten); scheitert das oder fehlt die Speicherzeile unter dem md5, endet der Lauf mit 'harness finding'"
  - "mounts.tsv trägt eine sechste Spalte Anmeldekonto am Samba-Server ('-' heißt: jeder Nutzer als er selbst); ohne sie kennt die Wahrheit das Konto für sudo -u bei global, userprovided und password::password nicht"
  - "k = 4 (zwei nicht auflösbare Speicher mal zwei Dateien in sicherheit) und Soll der Positivkontrolle 3 = 16 (17 Doppelzählungen über Wurzeln und Schreibweise, minus 1 für die zwei privat.txt, die naiv verschmelzen), beide als Konstante mit Herleitung in coverage_truth.sh"
  - "Phase-A-Regel physisch: Baum ist das Verzeichnis der Freigabe laut testparm (bei homes das Heimatverzeichnis), Dokument ist die Inode; nur die Zähler aus oc_findling_scan_stats kommen noch vom Produkt, wie bisher"
  - "a1_rows_checked prüft je Inode: Zeilen auf mindestens zwei Speichern und genau ein Schlüssel, keiner leer; die Schlüsselformel selbst steht nicht mehr in der Wahrheit"
  - "e2e_head_proof.sh ist strenger als verlangt: jeder Abschnitt mit einer Fix-Zeile muss genau ein Paar tragen, nicht nur der letzte; Felder von gh mit Balken statt Tab getrennt, damit ein Lauf ohne conclusion die Felder nicht verschiebt"
metrics:
  started: "2026-11-10 (nur gelesen, am Wochenlimit unterbrochen), fortgesetzt 2026-11-11"
  completed: 2026-11-11T06:45:00Z
  tasks: 2
  files: 4
---

# Phase 43 Plan 25: Abnahmetest mit mbozem-Topologie und physischer Wahrheit

Der Abnahmetest bildet jetzt die Lage aus #25 ab (eine Freigabe mit Wurzel / und Unterwurzeln, andere Schreibweise von Host und Freigabe, gehashte Speicher-IDs) und misst gegen eine Wahrheit, die eine Datei auf dem Samba-Host über Gerät und Inode als ein Dokument zählt, ohne Speicher-ID, Faltung oder Owner-Entscheid. Dazu ein Skript, das einen E2E-Beleg mechanisch an einen Kopf bindet. Alles nur lokal, kein Lauf in GitHub Actions; ob die Topologie auf einem Runner trägt, zeigt erst 43-26.

## Tasks

| Task | Inhalt | Commit |
|------|--------|--------|
| 1 | Topologie, Anlage-Protokoll, docKeyFormat im Body, Suchprobe W5 | 423586d5 |
| 2 | Physische Wahrheit, k, Positivkontrolle 3, e2e_head_proof.sh mit Selbsttest | aa5a4ade |

## Was gebaut ist

- **Topologie (coverage_e2e.sh):** Host-Alias in /etc/hosts, vor der Nutzung per getent in beiden Schreibweisen auf 127.0.0.1 belegt. Mounts: /daten, /archiv, /archiv-zwei wie bisher (jetzt über den Alias), /daten-sicherheit (Wurzel sicherheit, alice und carol), /daten-projekt (Wurzel projekt, bob), /Daten-gross (Freigabe Daten, Host groß, bob), /lang-kennwort, /lang-global, /lang-eigen (je Wurzel sicherheit, je eine Anmeldeart), /heim (Freigabe homes, alice und bob). Dateien: sicherheit-1.txt, sicherheit-2.txt, Bericht.txt und bericht.txt in gemeinsam, privat.txt in beiden Heimatverzeichnissen. Linkfreigabe (shareType 3) auf /daten/gemeinsam über die OCS-API.
- **Belege im Lauf:** die vier Speicher der Unterwurzel haben eine ID über 64 Zeichen, eine Zeile unter dem md5, sind eingehängt, tragen beide Dateien und zählen als 32-hex (Zeile in der Ergebnistabelle); zwei Dateicache-Zeilen für die Zwillinge; privat.txt je Nutzer; Positivkontrollen am Samba-Server (Zwillinge getrennt, homes je Konto, Freigabe antwortet als Daten hinter dem großgeschriebenen Host).
- **Wahrheit (coverage_truth.sh):** Dateicache-Zeile -> oc_mounts.mount_point -> mounts.tsv -> Freigabepfad laut testparm (ohne Pfad: getent passwd) -> Serverpfad -> stat %d:%i. Zähler, Nenner (sudo -u Anmeldekonto, find, Typfilter), notReadable, Phase-A-Regel und a1 über Inoden. Abbruch bei harten Links, bei einem eingehängten Speicher ohne Zeile im Protokoll und bei zwei Serverpfaden für einen Speicher.
- **Erwartung der Kopf-Beine:** angezeigt = Wahrheit + 4 in Zähler und Nenner, Phase A und B; Positivkontrolle 3 nach den Vergleichen.
- **e2e_head_proof.sh:** Exit 0, 2, 3, 4, 5 und 64 nach dem must_have, Ausgabe nur IDs, Zahlen und Status.

## Belege

- **Freigabe:** Der Plan verlangt keine eigene Freigabezeile (kein Push, kein Dispatch). Die Entscheide, von denen er abhängt, stehen in 43-FREIGABEN.md: OE-1 bis OE-8 je "Entscheid: a" (Zeilen 124 bis 131), darunter OE-3 a für homes.
- **Offener Punkt aus 43-24 am Code geprüft:** coverage_body sandte kein docKeyFormat. Beide Bodies des Harness gegen das echte Modell des Kopfes (CoverageRequest in backend/src/findling/api/coverage.py) geprüft: mit docKeyFormat 2 angenommen, ohne abgelehnt (Fehlertyp missing, Feld docKeyFormat). v1.6.2 hat keine Route /coverage, rc.1 hat extra forbid ohne das Feld (git show). post_coverage läuft nur an vier Stellen, alle hinter start_backend aus dem Harness-Checkout. Weitere direkte Aufrufer von POST /coverage in scripts/ci, scripts/dev und .github/workflows: keine (deploy-harp.yml geht über die Overview der Companion).
- **verify-Zeilen des Plans:** Task 1 Exitcode 0, Task 2 Exitcode 0 (mit dem echten gh-Aufruf gegen Lauf 42503731869: Exit 4, "the run has 5 successful jobs, 7 are required").
- **Selbsttest e2e_head_proof_selftest.sh:** 24 Fälle, 0 Fehler, 0 übersprungen; nach dem zweiten Commit wiederholt, gleiches Ergebnis. Ein Fall gegen das echte gh (nur lesend), 23 gegen ein gh-Double vor dem PATH, git immer echt.
- **Gegenprobe e2e_head_proof.sh (zehn Mutationen, je einzeln, Selbsttest danach):** neun rot (Jobzahl 8, Workflow-Prüfung aus, Lauf-SHA-Prüfung aus, conclusion-Prüfung aus, Diff-Prüfung aus, gh-Anmeldung aus, Paar-Prüfung aus, chosen-pair-Zeile weg, andere Pfadliste). Eine überlebt: "section == 0" nur vor der Kopf-SHA-Zeile entfernt; sie ist gleichwertig, weil der Kopf-Satz schon vor der ersten Überschrift geschrieben wird. Danach cmp gegen die Sicherung identisch.
- **Sandbox für coverage_truth.sh** (Scratch, nicht im Repo): echte Dateien und Inoden unter Git Bash, echtes SQL über Pythons sqlite3, Ersatz für sudo, testparm und getent. Verkleinerte Topologie (Wurzel /, andere Schreibweise, Unterwurzel, nicht auflösbarer Speicher, homes, Weiterteilung), Soll von Hand gezählt: 29 Prüfungen grün, 0 rot. Darin die Positivkontrollen: Positivkontrolle 3 gegen die Konstante 16 und gegen eine Datei zu wenig rot, harter Link rot, Speicher ohne Protokollzeile rot, zwei Serverpfade rot, unbekannte Freigabe rot, fehlende physische Tabelle rot, a1 mit zwei Schlüsseln, mit leerem Schlüssel und mit nur einem Speicher je 0. Der erste Lauf war zu Recht rot: 18 Abweichungen aus dem Ersatz (Zeilenenden) und ein falsch gezähltes Soll von mir (26 statt 23 indexierte Zeilen), kein Fehler im Skript; dazu ein echter Befund, siehe Deviation 4.
- **Gegenprobe coverage_truth.sh (vier Mutationen gegen die Sandbox):** Dokument je Zeile statt je Inode in der Phase-A-Regel 6 rot, N1 abgeschaltet 3 rot, Typfilter entfernt 1 rot, Zähler über Speicher und Pfad statt Inode 6 rot. 0 Überlebende. Die Mutationen liefen auf Kopien, das Original blieb unberührt.
- **Gegenprobe der Grep-Tore:** sechs eingepflanzte verbotene Wörter (oc_storages, mount_id, external_config, tr upper, files.path, OE-3) je rot, die Wahrheit von HEAD vor dem Plan rot.
- **Schlüsselformel:** printf '2\000%s\000%s' 'smb::fs.example//daten' 'projekt/r1.txt' ergibt 53808de0..., den Wert aus backend/tests/fixtures/coverage_topology.json.
- **Nextcloud-Quelltext (lokaler Checkout stable34 ec467246):** GlobalAuth.php (password::global, uid '' bei Admin-Mount), UserProvided.php (password::userprovided/ plus Mount-ID), SMB.php getId und Wurzelform, Create.php (validateParam) gelesen und so umgesetzt.
- **pytest mit Modulauswahl, je timeout 540:** test_measurement_scripts, test_phase43_audit, test_phase40_audit, test_store_metadata, test_workflow_contexts: 808 passed, 7 skipped. test_public_artifacts, test_ops_scripts, test_phase30_audit, test_phase31_audit, test_guest_parity, test_workflow_tag_triggers, test_coverage_endpoint: 440 passed. Zusammen 12 Module, 1248 passed, 7 skipped. Freier RAM davor 6,5 GB.
- **Form:** bash -n für alle vier Skripte, keine Nicht-ASCII-Zeichen, keine CR, neue Skripte 100755 und LF. Keine Python-Datei berührt, daher keine Python-Gates.

## Deviations from Plan

**1. Vier gehashte Fälle, sechste Spalte im Protokoll**
- Der Aktionstext nennt drei gehashte Fälle, must_have und verify vier; gebaut sind vier. mounts.tsv hat sechs statt fünf Spalten (Anmeldekonto), siehe Entscheidungen.

**2. Zwei zusätzliche Samba-Konten und ein Host für alle Mounts**
- dglobal und deigen (nur Samba, keine Nextcloud-Nutzer). Auch /daten, /archiv und /archiv-zwei hängen jetzt am Alias statt an 127.0.0.1; die Wurzel wird als "/" statt leer übergeben (laut SMB.php dieselbe ID).

**3. [Rule 1 - Bug] Zwei Stellen des Harness rechneten noch Schlüsselformat 1**
- **Found during:** Task 1 und 2, beim Lesen der Aufrufer.
- **Issue:** a1_rows_checked und die Rename-Prüfung im upgrade-Bein rechneten sha256 über den internen Pfad. Seit 43-22 gilt Format 2; a1 hätte 0 ergeben ("the reshare case tests nothing"), die Rename-Prüfung wäre gescheitert.
- **Fix:** a1 prüft je Inode auf einen gemeinsamen Schlüssel; old_key und new_key in Format 2 mit leerer Freigabe (Home-Speicher).
- **Files modified:** scripts/ci/coverage_truth.sh, scripts/ci/coverage_e2e.sh
- **Commit:** 423586d5, aa5a4ade

**4. [Rule 1 - Bug] Meldungen in Kommandosubstitutionen gingen verloren**
- **Found during:** Task 2, Sandbox (Fall "unbekannte Freigabe" scheiterte ohne Text).
- **Issue:** fail schreibt nach stdout; in tree=$(...) und in $(... | wc -l) landete der Text in der Variablen statt im Log.
- **Fix:** die drei betroffenen fail-Aufrufe schreiben nach stderr, truth_share_path gibt den Fehler mit "|| exit 1" weiter.
- **Commit:** aa5a4ade

**5. Suchprobe und sid_is**
- Die Suchprobe W5 läuft in allen Beinen, auch v1.6.2 (Suche und Rechte hängen nicht an der Zählung). Speicher werden über die exakte ID gesucht (sid_is), weil LIKE in SQLite ASCII-Schreibweise faltet und bob zwei Speicher hat, die sich nur darin unterscheiden.

**6. Docker lief nicht**
- Der Docker-Daemon war nicht erreichbar (dockerDesktopLinuxEngine fehlt). Ich habe ihn nicht gestartet; statt eines Linux-Containers lief die Sandbox unter Git Bash mit Ersatzwerkzeugen.

Sonst plangemäß. Keine STOPP-Regel berührt: kein Produktcode, kein Schema, keine Route, kein Workflow geändert.

## Bekannte Grenzen und offene Punkte

- **Kein Lauf auf einem Runner.** Nicht belegt, erst in 43-26 sichtbar: ob Samba homes als Freigabename "homes" bedient, ob die Zwillinge über SMB als zwei Dateien ankommen, ob der Alias in Großschreibung in smbclient und php-smbclient auflöst, ob files_external die vier Anmeldearten so einhängt (insbesondere global und userprovided über den Credentials Manager), ob testparm den Abschnitt in anderer Schreibweise findet, ob die echte sqlite3-Shell das SQL der Wahrheit annimmt (lokal lief es nur über Pythons sqlite3), ob sudo -u die Rechte so abbildet wie erwartet. Jede dieser Stellen hat eine eigene Abbruchmeldung ("harness finding").
- **k = 4 und das Soll 16 sind hergeleitet, nicht gemessen.** Sie gelten nur, wenn alle erwarteten Dateien indexiert sind und das Produkt die zwei nicht auflösbaren Speicher einzeln zählt. Weicht ein Bein ab, ist zu klären, ob das Produkt oder die Herleitung falsch ist; die Konstanten dürfen nicht an die Anzeige angepasst werden.
- **Die Sandbox prüft keine Rechte:** der sudo-Ersatz ignoriert das Konto, Zwillinge gehen unter NTFS nicht. Die Trennung nach Konto und die Zwillinge sind lokal unbelegt.
- **coverage_body baut die Gruppen weiter nach der alten Regel** (ausgeschriebene IDs, Wurzel im Schlüssel). Aus der Antwort werden nur counting und die doc-key-Zähler gelesen; steht im Kommentar.
- **shellcheck fehlt lokal,** die Skripte sind nur mit bash -n und in den Läufen oben geprüft; das shellcheck-Tor in python.yml sieht sie erst nach einem Push.
- **43-26 muss das Bein-Soll anpassen:** e2e_head_proof.sh verlangt sieben erfolgreiche Jobs, der Workflow hat heute fünf.
- **Laufzeit:** mehr Speicher und Mounts verlängern Crawl und Suchgegenprobe; ob die 90 Minuten je Bein reichen, ist offen.
- Nichts gepusht, kein Dispatch, kein Tag, kein Kommentar. main ist 24 Commits vor origin.

## Threat Flags

Keine neuen Flächen im Produkt. Im Harness (Wegwerf-Runner): ein Eintrag in /etc/hosts, zwei weitere Samba-Konten mit festen Testpasswörtern, das Passwort von bob als Argument von occ files_external:create (password::password) und über die Umgebung an ein PHP-Hilfsskript; nichts davon wird ausgegeben. T-43-76 (Inode, testparm, verbotene Tabellen per verify), T-43-77 (Positivkontrolle 3 und k mit Exit 1) und T-43-78 (Ergebnistabelle nur mit Testnamen, Zahlen und IDs; die Zeile für Wahrheitszeilen ohne Wort nennt nur noch den Dateinamen) sind umgesetzt.

## Self-Check: PASSED

- FOUND: scripts/ci/coverage_truth.sh (%d:%i, testparm, EXPECTED_SEPARATE_K=4, NAIVE_SURPLUS=16), scripts/ci/coverage_e2e.sh (mounts.tsv, docKeyFormat, SMB_HOST), scripts/ci/e2e_head_proof.sh (headSha), scripts/ci/e2e_head_proof_selftest.sh
- FOUND: Commits 423586d5, aa5a4ade
