---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 26
subsystem: scripts/ci und .github/workflows (Abnahmetest D-43-08), backend/src/findling/worker (Fix 1)
tags: [D-43-08, D-43-10, D-43-15, D-43-17, W5, W12, B1, harness, mixed-operation, backup-pause, rc-proof]
requires: [43-25]
provides: [Beine upgrade-rc1 (Container zuerst) und upgrade-rc1-cf (Companion zuerst mit Backup-Pause), sieben Beine mit eigener Frist am Messschritt, parametrisierter rc-Proof, grüner Lauf 43016026129 auf Kopf 2261167b, 43-E2E-WURZEL.md mit Paar Lauf-ID-Fix und Kopf-SHA-Fix, Runde ohne state.db nach 5 s statt nach einem Takt, gone_path im Bein upgrade]
affects: [43-27, 43-29, 43-12, 43-13]
tech-stack:
  added: []
  patterns: [Erwartung an ihre Bedingung geknüpft statt an ein Ergebnis, Zustand lesen statt Zeit abwarten, Frist am Messschritt damit der Fehlerschritt und der Upload noch laufen, Ergebniszeile je Upgradeweg]
key-files:
  created:
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-E2E-WURZEL.md
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-26-SUMMARY.md
  modified:
    - scripts/ci/coverage_e2e.sh
    - .github/workflows/coverage-e2e.yml
    - .github/workflows/rc-version-proof.yml
    - scripts/ci/rc_version_proof.sh
    - backend/src/findling/worker/doc_keys.py
    - backend/tests/test_doc_keys.py
    - backend/tests/test_measurement_scripts.py
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-FREIGABEN.md
decisions:
  - "Der Lauf 43016026129 auf Kopf 2261167b ist der Beleg für 43-26: sieben Beine success, e2e_head_proof.sh Exit 0. Der erste Lauf 42991291089 auf a42d2dc6 bleibt als Befundhistorie im Kopf von 43-E2E-WURZEL.md stehen, gültig ist das Paar des Abschnitts Fix 1"
  - "Eine Runde der Dokumentschlüssel ohne state.db kommt nach DOC_KEY_NO_STATE_SECONDS (5 s) wieder statt nach einem Takt von 300 s; jedes andere Ergebnis behält den Takt. Kein neuer Meta- oder AppConfig-Schlüssel, keine Migration, kein Schema"
  - "Die Erwartung skipped/gone im Bein upgrade hängt an ihrer Bedingung: lag vor der Topologieänderung eine Queue-Zeile offen, muss skipped/gone stehen, sonst muss das Urteil von vorher unverändert stehen; das Bein nennt den Fall als gone_path=exercised oder not_exercised"
  - "Die Frist aus der Matrix (90 oder 150 min) liegt am Messschritt, der Job hat 170 min, damit Fehlerschritt und Artefakt-Upload nach einer gerissenen Frist noch laufen"
  - "Positivkontrolle 4 verlangt, dass der Zähler von rc.1 über Wahrheit plus k liegt, nicht nur über der Wahrheit"
  - "rc.2 ist gestrichen (Owner 09.11.2026): der rc-Proof ist parametrisiert, sein Standard für rc_version ist 1.6.3-rc.1 und nicht 1.6.3-rc.2; der Versionsnachweis rc.1 auf 1.6.3 liegt in den beiden rc.1-Beinen"
  - "k = 4 und das Soll 16 der Positivkontrolle 3 aus 43-25 sind im Lauf so eingetreten; die Konstanten in coverage_truth.sh sind unverändert"
metrics:
  started: "2026-11-11 (Commit von Task 1 um 07:40 UTC)"
  completed: 2026-11-11T12:55:00Z
  tasks: 3
  files: 9
---

# Phase 43 Plan 26: rc.1-Upgrade-Beine, Push, Dispatch und Auswertung

Der Abnahmetest hat jetzt sieben Beine, darunter das Upgrade von rc.1 in beiden Reihenfolgen (Container zuerst, Companion zuerst mit Backup-Pause), und ist auf dem gepushten Kopf 2261167b in allen sieben Beinen grün (Lauf 43016026129). Der erste Lauf war rot und hat einen Produktfehler aus 43-24 aufgedeckt, der mit Fix 1 per TDD behoben ist. Der grüne Lauf lässt Punkte offen, die unten unter "Bekannte Grenzen und offene Punkte" stehen; der wichtigste: skipped/gone beim Claim hat der Lauf nicht gezeigt (gone_path=not_exercised).

## Tasks

| Task | Inhalt | Commit |
|------|--------|--------|
| 1 | Beine upgrade-rc1 und upgrade-rc1-cf, Fristen je Bein, rc-Proof parametrisiert | 36d1921f |
| 1 | Stand nach Task 1, Checkpoint offen | 92717f5c |
| 2 | Owner-Freigabe Push und Dispatch ("Go für Findling", 11.11.2026 09:29) | a42d2dc6 |
| 3 | Erster Lauf 42991291089 rot, drei Befunde, Fix 1 lokal dokumentiert | 893af895 |
| 3, Fix 1 | Befund B, RED: ein nach der Armierung geborener Zustand bekommt seine Generation binnen Sekunden | 07eadd03 |
| 3, Fix 1 | Befund B, GREEN: Runde ohne state.db nach 5 s statt nach einem Takt | e02ff71f |
| 3, Fix 1 | Befund A: die rc.1-Beine lesen die Companion dort, wo die Setup-Aktion sie hinlegt | a311b827 |
| 3, Fix 1 | Zu Befund B im Harness: Generation 2 und keine Backfill-Runde vor B1 | f4375578 |
| 3, Fix 1 | Befund C: gone-Erwartung an die Queue-Zeile geknüpft, sechste gesperrte Zeile, Diagnosezeilen, Backend-Log als Artefakt | 76be7820 |
| 2, Fix 1 | Owner-Freigabe Push und Dispatch von Fix 1 ("Go", 11.11.2026 12:28) | 2261167b |
| 3 | Lauf 43016026129 grün, Auswertung im Abschnitt Fix 1 von 43-E2E-WURZEL.md | f0ab98f4 |

Außerhalb des Planumfangs, aber im selben ersten Push (in der Umfangszeile der Freigabe genannt): 53373888 (RED) und c93a6f1e (GREEN), der Reset der Dokumentschlüssel läuft in Bändern zu 100.000 Zeilen, je eine Transaktion, damit kein Schreiber auf die ganze Tabelle wartet.

## Was gebaut ist

- **Bein upgrade-rc1 (native, Container zuerst):** Instanz aus rc/1.6.3-rc.1, indexiert, Positivkontrolle 4; nur der Container auf den Kopf (422 für den Body einer rc.1-Companion, 1.6.2-Weg auf der Seite, Logzeile "another doc key format", kein Auftrag schreibt einen Schlüssel); dann die Companion, Neuaufbau, Zahlen gegen die Wahrheit; Rückweg auf 1.6.2 und zweites Update.
- **Bein upgrade-rc1-cf (native, Companion zuerst):** nur die Companion auf den Kopf (422 vom rc.1-Container, 1.6.2-Weg), `occ findling:pause`, dann der Container; unter der Pause counting true und keine Zahl, Positivkontrolle der Sperre per sqlite3 (Meta-Wert beginnt mit "1:" und Zeilen mit Schlüssel größer 0); `occ findling:resume`, Neuaufbau, Zahlen gegen die Wahrheit.
- **Workflow:** sieben Beine, Matrix-Feld timeout (90, für die rc.1-Beine 150), Checkout-Ref rc/1.6.3-rc.1 für beide rc.1-Beine, gepinnte Actions, Backend-Log als Artefakt.
- **rc-Proof:** Eingänge rc_version, from_rc_ref, from_archive_run_id; kein festes 1.6.3-rc.1 mehr im Skript; Zeile "proof inputs rc_version=... from_archive_run_id=...".
- **Fix 1 (Produkt):** `worker/doc_keys.py`, siehe Befund B.

## Die zwei Läufe

| Lauf | Kopf | Ergebnis | Beine grün |
|------|------|----------|-----------|
| 42991291089 | a42d2dc6dcbbf41a55234081aa018aa74f01f064 | failure | 1 von 7 (v1.6.2) |
| 43016026129 | 2261167b3aaacafdf38f3d4b4e6025c04c25c7c3 | success | 7 von 7 |

### Die drei Befunde des ersten Laufs

- **Befund A (Harness), Beine upgrade-rc1 und upgrade-rc1-cf:** "sed: can't read findling-src/php/appinfo/info.xml". Ursache: das Skript las die Version der rc.1-Companion aus einem Verzeichnis, das die Setup-Aktion verschiebt (`mv findling-src/php apps/findling`). Die lokale Gegenprobe aus Task 1 hatte kopiert statt verschoben.
- **Befund B (Produkt, aus 43-24), die drei gate-Beine:** "a catch-up round swept before phase A, the run is invalid". Ursache: auf einer frischen Installation fand die erste Runde der Dokumentschlüssel keine state.db (nur der Poller legt sie an), endete ohne Logzeile und wartete einen Takt von 300 s. So lange trug die Datenbank keine Generation, die Generationssperre antwortete counting, B1 wartete 213 s, und der Catch-up-Zyklus fegte. Folge für Nutzer ohne den Fix: jede frische Installation von 1.6.3 hätte bis zu fünf Minuten "wird gezählt" gezeigt und danach richtige Schlüssel neu aufgebaut.
- **Befund C (Harness-Erwartung), Bein upgrade:** "gone storage verdicts skipped/gone: expected 1, shown 0". Ursache: skipped/gone schreibt nur der Claim einer Queue-Zeile; mit sechs statt vier abgelehnten Dateien (Topologie aus 43-25) hinterlässt 1.6.2 für die Kopie auf dem entfernten Speicher keine Zeile mehr. Erwartetes Verhalten von 1.6.2, kein Fehler des Kopfes; die Prüfung hatte ein Ergebnis verlangt, ohne die Queue anzusehen.

Einzelheiten mit Logzeilen in 43-E2E-WURZEL.md, Abschnitte Befund A, B und C.

### Der grüne Lauf in Zahlen

Alle Zahlen mit Fundstelle (Zeile der Ergebnisdatei oder des Job-Logs) in 43-E2E-WURZEL.md, Abschnitt Fix 1.

| Bein | smb | failures | Zähler B Wahrheit / angezeigt | Nenner B Wahrheit / angezeigt | Nenner A angezeigt | Positivkontrolle 3 | Dauer Messschritt / Frist |
|------|-----|----------|------------------------------|------------------------------|--------------------|--------------------|---------------------------|
| gate-crawl | wrapped | 0 | 29 / 33 | 31 / 35 | 35 | 16 | 5 min 54 s / 90 min |
| gate-queue | wrapped | 0 | 29 / 33 | 61 / 65 | 64 | 16 | 5 min 51 s / 90 min |
| gate-queue | native | 0 | 29 / 33 | 61 / 65 | 35 | 16 | 5 min 20 s / 90 min |
| v1.6.2 | native | 0 | 29 / 85 | 61 / 79 | 79 | entfällt | 10 min 17 s / 90 min |
| upgrade | native | 0 | 29 / 33 | 61 / 65 | 65 | 16 | 41 min 10 s / 90 min |
| upgrade-rc1 | native | 0 | 30 / 34 | 62 / 66 | 66 | 16 | 16 min 13 s / 150 min |
| upgrade-rc1-cf | native | 0 | 29 / 33 | 61 / 65 | 35 | 16 | 12 min 25 s / 150 min |

- **k und Positivkontrolle 3, gemessen gegen hergeleitet:** k = 4 in Zähler und Nenner, Phase A und B, in allen sechs Kopf-Beinen; Positivkontrolle 3 zeigt 16 bei Soll 16 in allen sechs. Beide Werte waren in 43-25 von Hand hergeleitet und sind so eingetreten; coverage_truth.sh ist seither unverändert.
- **Positivkontrolle 4:** rc.1 zeigt 58 Dokumente bei 34 Dateien auf dem Host, Schwelle 38, in beiden rc.1-Beinen.
- **Positivkontrolle 2:** 1.6.2 zeigt 85 von 79, Wahrheit 29 von 61.
- **Gehashte IDs** 4 von 4, **Zwillinge** 2 Zeilen im Dateicache und getrennt gefunden, **[homes]** 2 von 2, **Suchprobe W5** 15 von 15 Zeilen in jedem der sieben Beine.
- **gone_path im Bein upgrade: not_exercised.** Vor der Topologieänderung lag keine Queue-Zeile für die Kopie auf dem entfernten Speicher offen; das Urteil failed/gateway_error von 12:05:42 steht danach unverändert.
- **Ergebniszeilen:** upgrade_1_6_2: ok (Backfill 293 s, 95 Zeilen); upgrade_rc1: ok in beiden Beinen; mixed_container_first: ok (Neuaufbau 281 s, 96 Zeilen); mixed_companion_first_pause: ok (Neuaufbau 20 s nach dem Resume, 95 Zeilen); rollback_1_6_2: ok in upgrade und upgrade-rc1; second_upgrade_rename: ok in upgrade (122 Zeilen) und upgrade-rc1 (123 Zeilen). Das Bein upgrade-rc1-cf hat keinen Rückweg, dort gibt es dafür keine Zeile.
- **Zeitreserve der gate-Beine gegen den Catch-up nach 300 s:** B1 beginnt 186 s (gate-crawl / wrapped), 186 s (gate-queue / wrapped) und 138 s (gate-queue / native) nach der Armierung, gestoppt spätestens nach 188, 188 und 140 s; Reserve 112, 112 und 160 s. B1 selbst dauert 1 s statt 213 s.
- **Dauer des Neuaufbaus je 1.000 Zeilen:** rechnerisch 3.084 s, 2.927 s und 211 s; keine der drei Zahlen misst den Durchsatz (Cooldown und Abfragetakt bei 95 Zeilen). Belastbar bleibt 43-16 mit rund 65 s je 1.000 Zeilen.

## Belege

- **Freigaben (43-FREIGABEN.md):** "Freigabe Push 43-26" und "Freigabe Dispatch 43-26", Owner "Go für Findling", 2026-11-11 09:29, je Entscheid ja, gelesen als Option a (die CHANGELOG-Entwürfe aus 43-23 stehen damit vor der Textrunde 43-12 öffentlich auf main). "Freigabe Push 43-26 Fix1" und "Freigabe Dispatch 43-26 Fix1", Owner "Go", 2026-11-11 12:28, je Entscheid ja. Je genau ein Push und ein Dispatch.
- **Reguläre Workflows auf 2261167b, alle success:** Python gates 43012307369, Security scans 43012307313, Integration 43012307391, Multi-arch image 43012307502, Resilience 43012307350, HaRP deploy 43012307761, OpenSSF Scorecard 43012307346. "PHP and store metadata gates" lief auf diesem Kopf nicht (Pfadfilter, Fix 1 ändert keine PHP-Datei). Die PHPUnit-Summe stammt vom vorigen Kopf a42d2dc6, Lauf 42987540725: OK (1197 tests, 7647 assertions); `git diff a42d2dc6 2261167b -- php` ist leer.
- **verify von Task 3, wörtlich gefahren:** Exit 0. `scripts/ci/e2e_head_proof.sh 2261167b... 43-E2E-WURZEL.md`: "chosen pair: 43016026129", "run 43016026129 success, 7 jobs, on 2261167b..., no code difference". Die fünf Grep-Tore der Ergebniszeilen treffen.
- **Selbsttest e2e_head_proof_selftest.sh:** cases=24 failures=0 skipped=0.
- **Gegenprobe an Kopien außerhalb des Repos (anderes Muster als die Umsetzung, mit Positivkontrolle):** unveränderte Kopie Exit 0. (a) Lauf-ID-Fix auf den roten ersten Lauf: Exit 5, "run 42991291089 ran on a42d2dc6..., the evidence names 2261167b..."; das ganze Paar des ersten Laufs: Exit 4, "the run has 1 successful jobs, 7 are required". (b) Kopf-SHA-Fix passt nicht zum Lauf: Exit 5. (c) je eine der fünf Ergebniszeilen entfernt: das verify endet fünfmal mit Exit 1; das Rot kommt hier aus den Grep-Toren des verify, e2e_head_proof.sh selbst liest die Ergebniszeilen nicht. Zusätzlich ein gerissenes Paar: Exit 3. Danach sha256 der Datei im Repo vor und nach den Proben gleich (5e622824...), cmp gegen die Kopie identisch, git status zeigte nur die beabsichtigte Änderung.
- **Belege des Laufs:** sieben Artefakte (coverage-e2e-result.md und exapp.log je Bein) und sieben Job-Logs per gh gelesen; in keinem Job-Log eine Zeile `##[warning]`, `##[error]` oder "different"; kein Traceback, kein ERROR oder CRITICAL in den Containerlogs.
- **Tests, die die Planungsdateien lesen:** keine (Grep in backend/tests nach 43-E2E-WURZEL und e2e_head_proof ohne Treffer), daher kein pytest in diesem Abschluss.
- **Lokale Belege von Fix 1** (vor dem Push): RED 3 failed, GREEN 92 passed zwanzigmal, 13 Pflichtmodule plus Nachbarn 1325 passed, 7 skipped und 464 passed, 13 Mutationen von doc_keys.py ohne Überlebende; Harness-Gegenproben 34 von 34, 18 von 18 und 9 von 9 Fälle. Einzelheiten in 43-E2E-WURZEL.md.

## Deviations from Plan

**1. rc.2 gestrichen**
- Der Plan nennt als Standard für rc_version 1.6.3-rc.2 und begründet den Push auch mit dem Image für rc.2. Der Owner hat rc.2 am 09.11.2026 gestrichen (43-28 entfällt). Der rc-Proof ist parametrisiert, sein Standard ist 1.6.3-rc.1; der Versionsnachweis rc.1 auf 1.6.3 liegt in den Beinen upgrade-rc1 und upgrade-rc1-cf.

**2. Frist am Messschritt statt am Job**
- Der Plan verlangt `timeout-minutes: ${{ matrix.timeout }}` am Job. Gebaut ist die Frist am Messschritt, der Job hat 170 min, damit der Fehlerschritt und der Upload der Artefakte nach einer gerissenen Frist noch laufen.

**3. Positivkontrolle 4 strenger**
- Verlangt war ein Zähler von rc.1 über der physischen Wahrheit. Geprüft wird über Wahrheit plus k (im Lauf: über 38), sonst könnte die erwartete Abweichung des Kopfes die Kontrolle bestehen.

**4. [Rule 1 - Bug] Befund B, Produktfehler aus 43-24**
- **Found during:** Task 3, erster Lauf.
- **Issue:** Runde ohne state.db wartete einen ganzen Takt, frische Installation zählte bis zu fünf Minuten.
- **Fix:** per TDD in worker/doc_keys.py (DOC_KEY_NO_STATE_SECONDS = 5), Paket-Baumhash 71385c59 nach 6ef6beba.
- **Files modified:** backend/src/findling/worker/doc_keys.py, backend/tests/test_doc_keys.py, backend/tests/test_measurement_scripts.py
- **Commit:** 07eadd03, e02ff71f
- Der Plan sieht bei einem Produktbefund den Stopp an den Koordinator und TDD im zuständigen Plan vor; der Fix lief mit eigener Owner-Freigabe unter 43-26.

**5. [Rule 1 - Bug] Befund A, Harness las ein verschobenes Verzeichnis**
- **Commit:** a311b827

**6. gone-Erwartung an ihre Bedingung geknüpft (Befund C)**
- Das Bein upgrade verlangt skipped/gone nur noch, wenn vor der Topologieänderung eine Queue-Zeile offen lag, sonst das unveränderte Urteil; es nennt den Fall als gone_path. Die sechste gesperrte Zeile wird mitbeurteilt. **Commit:** 76be7820

**7. Zustandsprüfung vor B1**
- Die gate-Beine lesen vor B1 Generation 2 und null Backfill-Runden; fehlt die Generation, endet das Bein dort als Produktbefund. **Commit:** f4375578

**8. head_green im Fix-1-Push ohne PHP-Workflow**
- Der Plan nennt head_green.sh mit "PHP and store metadata gates". Auf dem Kopf von Fix 1 gibt es keinen solchen Lauf (Pfadfilter). Belegt sind Python gates und Security scans auf 2261167b, PHPUnit auf a42d2dc6 bei leerem Diff unter php/.

**9. Zwei Läufe statt einem, zwei Freigabepaare**
- Erster Lauf rot, Fix 1 mit eigenen Zeilen "Fix1", wie der Plan es für rote Beine vorsieht.

**10. Reset der Dokumentschlüssel in Bändern (53373888, c93a6f1e)**
- Nicht Teil des Plans, im ersten Push mitgereist und in der Umfangszeile der Freigabe genannt.

**11. second_upgrade_rename in zwei Schreibweisen**
- Der Plan nennt `second_upgrade_rename=ok`; das Skript schreibt diese Zeile ins Log und zusätzlich die Ergebniszeile `second_upgrade_rename: ok`. Beide stehen im Beleg.

## Bekannte Grenzen und offene Punkte

Trotz grünem Lauf offen oder auffällig:

- **skipped/gone beim Claim ist nicht gezeigt.** gone_path=not_exercised: 1.6.2 hinterlässt mit der Topologie aus 43-25 keine Queue-Zeile für die Kopie auf dem entfernten Speicher. Der Zweig gone_path=exercised ist auf keinem Runner gelaufen, nur lokal gegen SQLite. Gezeigt ist der Sofort-gone-Weg über den Sweep (gone=1 in Phase A aller Kopf-Beine).
- **Der Nenner in Phase A schwankt zwischen Beinen mit demselben Tor** (35, 64, 65, 66 bei "queue busy"). In jedem Bein gleich der Regel aus D-43-11 plus k, deshalb grün. Ursache aus den Belegen nicht geklärt; Vermutung (nicht belegt): ob der Poller die 30 Rückstau-Bilder beim Lesen der Übersicht schon übernommen hatte. Für 43-27 zu klären.
- **"doc key verify, corrected=3"** (im Bein upgrade corrected=2) nach der Topologieänderung, vom Harness nicht geprüft. Vermutung (nicht belegt): die Zeilen des entzogenen Speichers, deren Freigabe-Identität wegfällt. Gehört in den Audit-Nachtrag 43-27 (Weg "Identität ändert sich zwischen Auftrag und Zählung").
- **Zeitabhängigkeit der gate-Beine gegen den Catch-up:** der vom Setup armierte Container muss binnen 300 s gestoppt sein. Reserve in diesem Lauf 112 s (wrapped) und 160 s (native), nicht abgesichert; ein langsamerer Runner macht den Lauf ungültig (W5 bricht ab, es entsteht keine falsche Zahl). Lösbar nur im Harness, ändert dann die Aussage von Phase A.
- **Flakiger Test** test_main_lifespan::test_a_disable_while_the_cycle_waits_silences_it_again: 5 von 60 Läufen rot, schon auf HEAD vor Fix 1 (Angabe der Hauptsitzung, in diesem Abschluss nicht nachgefahren). Offen, nicht behoben.
- **Eine Runde, die beim Eintreffen der Backup-Pause schon läuft, schreibt noch.** Das Bein upgrade-rc1-cf setzt die Pause vor dem Start des Kopf-Containers und zeigt diesen Fall nicht.
- **Das Ende des Cooldowns wirkt erst beim nächsten Takt:** bei "Container zuerst" vergehen nach dem Companion-Update 281 s (rc.1) und 293 s (1.6.2), bis die Seite wieder eine Zahl zeigt. Für die Texte in 43-12 zu wissen.
- **Zwischen der Geburt der state.db und der nächsten Runde (höchstens 5 s)** kann ein Auftrag einen Schlüssel schreiben, den die Runde zurücksetzt und neu holt. Bei "Companion zuerst" nimmt ein rc.1-Container Schlüssel im Format 2 ungeprüft an, der Kopf-Container setzt sie mit Generation 2 zurück.
- **Linkfreigabe ohne eigene Ergebniszeile:** sie wird in jedem Bein angelegt, "ohne Wirkung" folgt nur mittelbar aus Zähler und Nenner gleich Wahrheit plus k.
- **PHPUnit lief nicht auf dem Kopf des Laufs** (siehe Deviation 8).
- **Der parametrisierte rc-Proof ist auf dem Kopf nicht gelaufen.** Letzter Lauf des Workflows: 42565361965 vom 09.11. auf einem älteren Stand. Belegt ist nur die lokale Prüfung aus Task 1.
- **Dauer des Neuaufbaus:** bei 95 Zeilen nicht messbar, siehe oben.
- **drain_incomplete=1 im Bein upgrade** (1.6.2-Phase, open=5) und zwei Logzeilen "taken as an outage" dort: Verhalten von 1.6.2 wie am 08.11., nach Phase B 0 solche Zeilen.
- **Warnzeilen "coverage count without a vector stock" (72) und "the vector stock could not be opened" (24)** in den Containerlogs: das Harness startet ohne Embeddings; nicht weiter untersucht.
- **Nicht Teil dieses Laufs:** Impersonation, ARM, eine echte Fremdinstanz.
- Nichts gepusht in diesem Abschluss: f0ab98f4 und der Commit dieser SUMMARY liegen nur lokal und gehen mit dem nächsten freigegebenen Push (43-27) hinaus. Kein Tag, kein Release, kein Store, kein Kommentar.

## Threat Flags

Keine neue Fläche im Produkt: Fix 1 ändert nur die Wartezeit einer Runde ohne Zustand, keine Route, kein Schema, keinen Schlüssel. T-43-79 (Zeitfenster mit alten Schlüsseln): im Bein upgrade-rc1-cf belegt, unter der Pause counting true, Meta-Wert "1:" und 95 Zeilen mit Schlüssel im selben Augenblick. T-43-80 (Beleg ohne Bindung an den Kopf): e2e_head_proof.sh im verify, Exit 0, Gegenproben rot. T-43-81 (Workflows): nur workflow_dispatch, gepinnte Actions. T-43-82 (Texte ohne Abnahme öffentlich): in der Push-Frage genannt, vom Owner mit "Go für Findling" als Option a freigegeben; die CHANGELOG-Entwürfe aus 43-23 stehen seither öffentlich auf main und warten auf 43-12. Die Ergebnisdateien und Logs nennen Datei-IDs, Speicher-IDs und Dateinamen der Testtopologie eines Wegwerf-Runners, keine Zugangsdaten.

## Self-Check: PASSED

- FOUND: .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-E2E-WURZEL.md (genau ein Paar Lauf-ID-Fix und Kopf-SHA-Fix, fünf Ergebniszeilen am Zeilenanfang), scripts/ci/coverage_e2e.sh, .github/workflows/coverage-e2e.yml, .github/workflows/rc-version-proof.yml, scripts/ci/rc_version_proof.sh, backend/src/findling/worker/doc_keys.py
- FOUND: Commits 36d1921f, 92717f5c, 53373888, c93a6f1e, a42d2dc6, 07eadd03, e02ff71f, a311b827, f4375578, 76be7820, 893af895, 2261167b, f0ab98f4
