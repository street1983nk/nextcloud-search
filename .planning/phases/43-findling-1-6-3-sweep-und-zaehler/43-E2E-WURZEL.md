# 43-E2E-WURZEL: End-to-End-Beleg mit Unterwurzeln, Schreibweisen und gehashten IDs (Plan 43-26 Task 3)

Lauf-ID: 42991291089
Kopf-SHA: a42d2dc6dcbbf41a55234081aa018aa74f01f064
Ergebnis: ROT. Ein Bein grün (v1.6.2 / native), sechs Beine rot. Der Lauf belegt den Kopf nicht.

Workflow "Coverage end to end", workflow_dispatch, gestartet 2026-11-11 08:58:41 UTC. Alle Uhrzeiten unten sind UTC aus den Job-Logs.

Stand dieses Dokuments: der erste Lauf (Paar oben) war rot und ist unten ausgewertet. Fix 1 ist gepusht und gelaufen, der Lauf ist grün in allen sieben Beinen; sein Paar steht im Abschnitt "Fix 1". `scripts/ci/e2e_head_proof.sh` liest das Paar des letzten Abschnitts mit einer Fix-Zeile, also das von Fix 1. Die Zeilen "Lauf-ID", "Kopf-SHA" und "Ergebnis" oben beschreiben weiter den ersten Lauf und bleiben als Befundhistorie stehen.

## Beine, wie der Lauf sie gezeigt hat

| Bein | Job-ID | smb mode | Ergebnis | Ende | Was gelaufen ist | Womit es endete |
|---|---|---|---|---|---|---|
| gate-crawl / wrapped | 130424561260 | wrapped | rot | 09:05:10 | Aufbau, Proben, Crawl, erster Drain, Urteile nach dem ersten Drain (5 von 5 skipped/unreadable), B1 (Nenner 40 / 40) | "a catch-up round swept before phase A, the run is invalid" (Befund B) |
| gate-queue / wrapped | 130424561343 | wrapped | rot | 09:05:04 | wie gate-crawl / wrapped | "a catch-up round swept before phase A, the run is invalid" (Befund B) |
| gate-queue / native | 130424561568 | native | rot | 09:05:12 | wie gate-crawl / wrapped | "a catch-up round swept before phase A, the run is invalid" (Befund B) |
| v1.6.2 / native | 130424561323 | native | grün | 09:09:19 | ganzes Bein | failures=0, drain_incomplete=0, outage_abort_tolerated=0 |
| upgrade / native | 130424561311 | native | rot | 09:40:45 | ganzes Bein bis zur Ergebnistabelle | failures=1: "upgrade after phase B gone storage verdicts skipped/gone: expected 1, shown 0" (Befund C) |
| upgrade-rc1 / native | 130424561106 | native | rot | 09:00:10 | Samba, Positivkontrollen am Samba-Server, Modusprüfung | "sed: can't read findling-src/php/appinfo/info.xml", Exit 2 (Befund A) |
| upgrade-rc1-cf / native | 130424561615 | native | rot | 09:00:12 | Samba, Positivkontrollen am Samba-Server, Modusprüfung | "sed: can't read findling-src/php/appinfo/info.xml", Exit 2 (Befund A) |

Nicht gelaufen und damit nicht belegt: Phase A und Phase B in den drei Kopf-Beinen gate-crawl und gate-queue; alles nach der Modusprüfung in den beiden rc.1-Beinen (Positivkontrolle 4, beide Mischbetriebsreihenfolgen, Neuaufbau, Rückweg). Für diese Beine gibt es keine Zeile `upgrade_rc1`, `mixed_container_first` oder `mixed_companion_first_pause`, weder ok noch failed.

### Was das Bein upgrade gezeigt hat (rot wegen einer Prüfung)

Diese Zahlen stammen aus einem roten Bein. Sie sind Messwerte dieses Laufs, kein Beleg für den Kopf.

| Größe | Wahrheit | angezeigt |
|---|---|---|
| Phase A Zähler, Dateien auf dem Host | 29 | 33 |
| Phase A Zähler, Wahrheit plus k=4 | 33 | 33 |
| Phase A Nenner (D-43-11-Regel über Inodes: 60) plus k=4 | 64 | 64 |
| Phase A Prozent | nicht null, höchstens 100 | 51 |
| Phase A gelaufene Runden | 0 | 0 |
| Phase B Zähler, Wahrheit plus k=4 | 33 | 33 |
| Phase B Nenner, Wahrheit plus k=4 | 65 | 65 |
| Phase B notReadable | 1 | 1 |
| Positivkontrolle 3 (naiver Zähler minus Dateien auf dem Host) | 16 | 16 |
| a1_rows_checked | 3 | 3 |
| Gehashte IDs, eine je Mechanismus | 4 | 4 |
| Zwillinge in Groß- und Kleinschreibung, Zeilen im Dateicache | 2 | 2 |
| privat.txt hinter [homes], je Nutzer | 2 | 2 |
| Suchprobe W4, Wörter der Wahrheit gefunden | 28 | 28 |
| Suchproben W5 (Zwillinge, Unterwurzeln, [homes]) | 15 | 15 |
| B1 Nenner vorher / nachher | 40 | 40 |
| Urteile der gesperrten Dateien nach Phase B, skipped/unreadable (Container und oc_findling_file_state) | 4 | 4 |
| Urteil der gesperrten Datei auf dem entfernten Speicher, skipped/gone | 1 | 0 |

Ergebniszeilen dieses Beins, wörtlich aus dem Log:

- `upgrade_1_6_2: ok (1.6.2 to the head, container first, backfill 293 s until counting false, 95 living rows)`
- `rollback_1_6_2: ok (doc_key column 1, index 1, a changed file judged and found by 1.6.2)`
- `second_upgrade_rename: ok (122 living rows, bound 660 s)`
- `drain_incomplete=1 (a 1.6.2 companion, the queue did not drain within 1500 s, open=5)`, aus der 1.6.2-Phase vor dem Update wie am 08.11. (dort open=4)

### Positivkontrolle 2 (Bein v1.6.2, grün)

1.6.2 zeigt 85 von 79, die Wahrheit ist 29 von 61. Positivkontrolle 1: "1.6.2 did not sweep within 240 s behind the blocked gate". 5 von 5 Container-Zeilen der gesperrten Dateien failed/gateway_error.

## Befund A (Harness): die rc.1-Beine lesen ein verschobenes Verzeichnis

Beine: upgrade-rc1, upgrade-rc1-cf. Abbruch nach rund 90 s.

Beleg: `2026-11-11T09:00:10.3300823Z sed: can't read findling-src/php/appinfo/info.xml: No such file or directory` (upgrade-rc1), dieselbe Zeile um 09:00:12.60 in upgrade-rc1-cf, danach "Process completed with exit code 2".

Ursache: `scripts/ci/coverage_e2e.sh` las die Version der rc.1-Companion mit `backend_version "${SRC}/php"`. Die Aktion `.github/actions/setup-test-nc` verschiebt dieses Verzeichnis aber (`mv findling-src/php apps/findling`, Zeile 209, im rc.1-Zweig und im Kopf gleich). Nach dem Setup gibt es `findling-src/php` nicht mehr; `findling-src/backend`, `findling-harness` und `findling-162` bleiben, wo der Checkout sie hingelegt hat.

Warum die lokale Gegenprobe aus 43-26 Task 1 das nicht gesehen hat: die simulierte Welt hat die Companion kopiert statt verschoben, und der Aufruf der Stelle war im Treiber nachgeschrieben statt aus dem Skript geschnitten.

Weitere Stellen derselben Art: keine. Alle übrigen Lesezugriffe auf `${SRC}` gehen nach `${SRC}/backend` (BACKEND_DIR, die Catch-up-Marke in store/repo.py, die Version der Backend-Hälfte), alle Lesezugriffe auf die Companion des Kopfes nach `${HARNESS}/php`, der Rückweg nimmt das Release-Archiv von 1.6.2 und `${BASE_SRC}/backend`.

## Befund B (Produkt, aus 43-24): eine frische Installation zählt fünf Minuten lang

Beine: gate-crawl / wrapped, gate-queue / wrapped, gate-queue / native.

Beleg (gate-queue / native): ExApp registriert und armiert um 08:59:37.72 ("ExApp findling_backend successfully registered."); `09:01:38.4594904Z --- B1: the denominator before and after removing the extra storage ---`; `09:05:11.4986986Z compare B1 denominator unchanged: expected 40, shown 40, equal`; `09:05:12.5066804Z ##[error]a catch-up round swept before phase A, the run is invalid`. B1 dauerte 213 s statt 1 s am 08.11. (Lauf 42525415627). Im Containerlog stehen hintereinander "the catch-up cycle after the upgrade is complete", "reconcile round walked, mounts=22 slices=22 seen=95 stale=6" und "doc key backfill, done=95 missing=0 unresolved=0". Die beiden wrapped-Beine zeigen dasselbe Bild (B1 ab 09:02:41.61 und 09:02:55.48, Abbruch 09:05:10.35 und 09:05:04.81, also jeweils rund 335 s nach der Registrierung).

Ursache, am Code geklärt:

1. Die erste Runde der Dokumentschlüssel läuft nicht erst nach 300 s, sondern sofort mit der Armierung (`DocKeyBackfill.run`). Auf einer frischen Installation findet sie aber keine state.db: PUT /enabled armiert Poller und Schlüssel-Task im selben Schritt, und nur der Poller legt die Datenbank an. Die Runde endet als `ROUND_NO_STATE`, ohne Logzeile, und die Schleife wartete danach einen ganzen Takt (`DOC_KEY_TICK_SECONDS`, 300 s).
2. In diesen 300 s trägt die Datenbank keinen Meta-Wert `doc_key_backfill_after`. Die Generationssperre aus 43-24 (`api/coverage.py`, `stored_generation`) antwortet deshalb counting, sobald Zeilen da sind. `read_settled` im Harness wartet auf counting false.
3. Die Runde nach dem Takt setzt alle Schlüssel zurück, auch die 95, die die Aufträge mit docKeyFormat 2 inzwischen geschrieben hatten, und holt sie neu ("done=95").
4. In der Wartezeit lief der einmalige Catch-up-Zyklus (ebenfalls 300 s nach der Armierung, `RECONCILE_TICK_SECONDS`) und fegte. Das Harness erklärt den Lauf dann zu Recht für ungültig (W5).

Dass die erste Runde ohne Zustand endete, steht in keiner Logzeile. Es folgt aus dem Code: eine Runde mit Zustand schreibt den Meta-Wert vor jeder Frage an die Companion, eine gehaltene Runde gibt es in `run` nicht, und eine Ausnahme hätte "doc key round ended in an unexpected" geloggt. Der Zeitpunkt (rund 300 s nach der Armierung plus Abfragetakt) passt dazu.

Folge für Nutzer ohne den Fix: jede frische Installation von 1.6.3 zeigt bis zu fünf Minuten "wird gezählt" und baut danach Schlüssel neu auf, die schon richtig waren. Bei einem Update (state.db vorhanden) läuft die erste Runde sofort; die 293 s im Bein upgrade sind der Cooldown nach dem 404 der 1.6.2-Companion plus Takt und standen so schon am 08.11. im Beleg.

## Befund C (Harness-Erwartung): skipped/gone im Bein upgrade hängt an einer Queue-Zeile, die 1.6.2 mit der neuen Topologie nicht mehr hinterlässt

Bein: upgrade / native.

Beleg: `09:39:00.7568310Z ##[warning]compare upgrade after phase B gone storage verdicts skipped/gone: expected 1, shown 0, different`. Dazu die Diagnosezeilen desselben Schritts: `container file_id=182 storage=20 state=failed/gateway_error attempts=1`, `file_state file_id=182 state=failed/gateway_error updated_at=2026-11-11 09:08:09`, die vier erreichbaren gesperrten Dateien (85, 121, 122, 159) `skipped/unreadable attempts=2`, `updated_at=2026-11-11 09:37:33`, und "refusal streaks renewed once after the update, rows=6".

Ursache, aus Code und drain-Protokoll des Beins hergeleitet:

1. skipped/gone hat genau einen Schreiber: `QueueService::describe` beim Claim einer Queue-Zeile, deren Datei kein Mount mehr zeigt (`usersFor` liefert niemanden). Der Kopf reicht für eine solche Datei keine neue Zeile aus: der Reconcile läuft nur über eingebundene Speicher, und der Sweep stempelt einen Speicher, der nur aus der Mountliste fiel. skipped/gone setzt also voraus, dass beim Entfernen des Speichers noch eine Queue-Zeile der Datei offen liegt.
2. Ob eine Zeile offen liegen bleibt, entscheidet 1.6.2: ein Pass, dessen Ablehnungen `min(5, geclaimt)` Dateien auf mindestens zwei Speichern erreichen, gilt als Ausfall; die abgelehnten Zeilen bleiben belastet in der Queue, der Rest des Passes geht unbelastet zurück (poller.py von 1.6.2, `_count_refusal`, GATEWAY_SAME_STATUS_OUTAGE_AFTER = 5). Ein Pass mit einer Datei eskaliert nie, sein Urteil wird quittiert und die Zeile ist weg.
3. Die Topologie aus 43-25 hat sechs abgelehnte Dateien statt vier: der Speicher von bob in der anderen Schreibweise (Speicher 16) bringt eigene Kopien von gesperrt-alle.txt und gesperrt-bob.txt mit. Die drei Kopf-Beine loggen entsprechend sechs Ablehnungen ("http status 422 for file id 85, 121, 122, 158, 159, 182").
4. Das drain-Protokoll des Beins zeigt die Pässe von 1.6.2: `09:05:07 open=6 outages=0` (der Catch-up-Zyklus hat sechs Zeilen zurückgegeben), `09:06:28 open=6 state=95/1794387969 outages=1` (Pass um 09:06:09 über sechs Zeilen, Ausfall bei der fünften Ablehnung, die sechste geht unbelastet zurück), `09:08:29 open=5 state=95/1794388089` (Pass um 09:08:09 über die eine freie Zeile, quittiert). Genau diese Sekunde trägt das Urteil von Datei 182 in oc_findling_file_state. Die sechste Zeile war demnach die Kopie von carol; das passt dazu, dass ihr Speicher die höchste ID hat und als letzter abgelaufen wird.
5. `09:21:57 open=5 outages=2`: die fünf belasteten Zeilen (85, 121, 122, 158, 159) kommen nach der Sperrfrist wieder und eskalieren erneut. Der Kopf beurteilt sie um 09:37:33, rund 900 s (LOCK_TIMEOUT) später. Für 182 liegt keine Zeile mehr in der Queue, der Kopf fasst die Datei nie an, das Urteil von 09:08:09 bleibt stehen.

Mit vier abgelehnten Dateien (Lauf 42498330790 und die grünen Läufe vom 08.11.) claimte der Wiederholungspass vier, eskalierte bei der vierten, und die Zeile von carol blieb belastet liegen; der Kopf las sie nach der Topologieänderung als skipped/gone. Die Prüfung hat dieses Ergebnis verlangt, ohne die Queue anzusehen.

Was nicht belegt ist: die Pässe selbst stehen in keiner Logzeile des Laufs, der Fehlerschritt druckt nur die letzten 300 Zeilen des Backend-Logs. Belegt sind die Zustandswechsel im drain-Protokoll, die Uhrzeit im Urteil und der Code von 1.6.2. Dass die sechste Zeile die von Datei 182 war, folgt aus beidem zusammen, nicht aus einer eigenen Zeile.

Zwei Annahmen der ersten Diagnose treffen nicht zu: Befund C ist keine Folge von Befund B (das Bein hat seinen eigenen Wartepunkt wait_for_catchup, B1 dauerte dort 2 s), und es liegt nicht an den gehashten Speichern. Dem Harness fehlte außerdem die sechste gesperrte Zeile (gesperrt-bob.txt auf Speicher 16, Datei 158): es hat fünf beurteilt, wo sechs abgelehnt wurden.

Einordnung: erwartetes Verhalten von 1.6.2 unter der neuen Topologie, kein Hinweis auf einen Produktfehler des Kopfes. Zähler, Nenner, notReadable und die Suchproben des Beins stimmen mit der Wahrheit überein. skipped/gone beim Claim ist auch keine Zusage von 1.6.3: der Schreiber existiert seit 1.0, der Sofort-gone-Weg aus #25 ist der Sweep, und den zeigt das Bein in Phase A ("storage sweep, absent=2 gone=1 deselected=0 stamped=1 removed=1").

## Fix 1

Lauf-ID-Fix: 43016026129
Kopf-SHA-Fix: 2261167b3aaacafdf38f3d4b4e6025c04c25c7c3
Ergebnis: GRÜN. Sieben von sieben Beinen success, failures=0 in jedem Bein. Was der Lauf zeigt und was nicht, steht unter "Der Lauf von Fix 1"; die offenen und auffälligen Punkte stehen am Ende dieses Abschnitts.

Freigaben: "Freigabe Push 43-26 Fix1" und "Freigabe Dispatch 43-26 Fix1", Owner "Go", 2026-11-11 12:28, je "Entscheid: ja" (43-FREIGABEN.md).

### Was Fix 1 ändert

| Befund | Art | Änderung | Commits |
|---|---|---|---|
| B | Produkt, TDD | `worker/doc_keys.py`: eine Runde ohne state.db kommt nach `DOC_KEY_NO_STATE_SECONDS` (5 s) wieder statt nach einem Takt; jedes andere Ergebnis einer Runde behält den Takt. Kein neuer Meta- oder AppConfig-Schlüssel, keine Migration, kein Schema. Paket-Baumhash 71385c59 nach 6ef6beba, 83 Dateien | 07eadd03 (RED), e02ff71f (GREEN) |
| A | Harness | `coverage_e2e.sh` liest die Version der installierten Companion aus `apps/findling`; `backend_version` meldet ein fehlendes Verzeichnis beim Namen | a311b827 |
| C | Harness | Die Erwartung für die Kopie auf dem entfernten Speicher hängt an ihrer Bedingung, gemessen bei gestopptem Container direkt vor der Topologieänderung: lag eine Queue-Zeile offen, muss skipped/gone stehen; lag keine offen, muss das Urteil von vorher Byte für Byte unverändert stehen. Das Bein sagt mit `gone_path=exercised` oder `gone_path=not_exercised`, welcher Fall lief. Die sechste gesperrte Zeile (Speicher 16) wird mitbeurteilt. Dazu Diagnosezeilen der Queue vor dem Update und vor der Topologieänderung und das ganze Backend-Log als Artefakt | 76be7820 |

Zusätzlich im Harness, zu Befund B (Commit f4375578): die Beine gate-crawl und gate-queue lesen vor B1 den Zustand statt einer Zeit (Meta-Wert trägt Generation 2, keine Backfill-Runde auf der frischen Installation). Fehlt die Generation, endet das Bein dort als Produktbefund und nicht erst an W5.

Lokale Belege für Fix 1 (vor dem Push erhoben, kein Lauf auf einem Runner):

- Befund B: RED 3 failed, 86 passed (test_doc_keys, alle drei AssertionError); GREEN 92 passed, zwanzigmal hintereinander; 13 Pflichtmodule plus Nachbarn 1325 passed, 7 skipped und 464 passed; Gegenprobe mit 13 einzelnen Mutationen von doc_keys.py, 13 rot, 0 Überlebende.
- Befund A: die Welt der Gegenprobe verschiebt die Companion jetzt wie die Setup-Aktion, und der Anfang des Beins wird aus dem Skript geschnitten. Das Skript des Laufs scheitert darin mit derselben sed-Zeile (6 von 6 Fällen), das neue besteht 34 von 34 Fällen.
- Befund C: judge_locked gegen echte SQLite-Datenbanken im Zustand des Laufs und in den Zuständen darum herum. Das Skript des Laufs zeigt den Fehlschlag des Laufs und den blinden Fleck der sechsten Zeile (5 von 5 Fällen), das neue besteht 18 von 18 Fällen.
- Zustandsprüfung vor B1: 9 von 9 Fällen. Selbsttest von e2e_head_proof.sh: 24 Fälle, 0 Fehler.

Bekannte Grenzen nach Fix 1 (Stand vor dem Lauf; "in diesem Lauf" im dritten Punkt meint den ersten Lauf 42991291089, die Werte des Laufs von Fix 1 stehen unten unter "Zeitreserve"):

- Zwischen der Geburt der state.db und der nächsten Runde (höchstens 5 s) kann ein Auftrag schon einen Schlüssel schreiben; die Runde setzt ihn zurück und holt ihn im selben Zug neu. Antwortet die Companion in diesem Augenblick nicht, wartet der Rest auf den nächsten Takt.
- Bei "Companion zuerst" nimmt ein rc.1-Container Schlüssel im Format 2 ungeprüft an; der Kopf-Container setzt sie mit Generation 2 zurück, weil er sie von Format-1-Schlüsseln nicht unterscheiden kann.
- Zeitabhängigkeit im Harness, schon vor diesem Lauf vorhanden und durch W5 abgesichert: in gate-crawl und gate-queue muss der vom Setup armierte Container innerhalb von 300 s nach der Armierung gestoppt sein, sonst fegt der Catch-up-Zyklus und der Lauf ist ungültig. Gemessen in diesem Lauf: B1 beginnt 121 s (native) und 187 bis 203 s (wrapped) nach der Armierung. Das Produktverhalten ist richtig; lösen ließe sich die Abhängigkeit nur im Harness (Catch-up abwarten und den Sweep-Stempel altern wie in den rc.1-Beinen), das ändert aber die Aussage von Phase A und ist nicht Teil von Fix 1.

### Der Lauf von Fix 1

Workflow "Coverage end to end", workflow_dispatch, angelegt 2026-11-11 11:56:05 UTC, beendet 12:38:27 UTC, Ergebnis success. Der Kopf des Laufs ist zugleich origin/main. Alle Uhrzeiten sind UTC.

Fundstellen: "E <n>" ist Zeile n der Datei coverage-e2e-result.md im Artefakt `coverage-e2e-<Bein>-<smb>` des Laufs, "L <n>" ist Zeile n des Job-Logs (`gh run view --job <Job-ID> --log`), "X <n>" ist Zeile n von exapp.log im selben Artefakt. Jede Zahl unten steht an der genannten Stelle; wo etwas hergeleitet und nicht gemessen ist, steht es dabei.

Reguläre Workflows auf demselben Kopf, alle success: Python gates 43012307369, Security scans 43012307313, Integration 43012307391, Multi-arch image 43012307502, Resilience 43012307350, HaRP deploy 43012307761, OpenSSF Scorecard 43012307346. "PHP and store metadata gates" ist auf diesem Kopf NICHT gelaufen (Pfadfilter: Fix 1 ändert keine Datei unter php/, `git diff a42d2dc6 2261167b -- php` ist leer). Die PHPUnit-Summe stammt vom vorigen Kopf a42d2dc6, Lauf 42987540725: OK (1197 tests, 7647 assertions). Für den Kopf 2261167b gibt es keinen eigenen PHP-Lauf.

#### Beine

| Bein | Job-ID | smb mode (Wahrheit / angezeigt) | Ergebnis | failures | outage_abort_tolerated | drain_incomplete | Fundstelle |
|---|---|---|---|---|---|---|---|
| gate-crawl / wrapped | 130507199589 | wrapped / wrapped | success | 0 | 0 | 0 | E 5, E 109 bis 111 |
| gate-queue / wrapped | 130507198567 | wrapped / wrapped | success | 0 | 0 | 0 | E 5, E 139 bis 141 |
| gate-queue / native | 130507198764 | native / native | success | 0 | 0 | 0 | E 5, E 134 bis 136 |
| v1.6.2 / native | 130507198910 | native / native | success | 0 | 0 | 0 | E 5, E 122 bis 124 |
| upgrade / native | 130507198748 | native / native | success | 0 | 0 | 1 | E 5, E 169 bis 171 |
| upgrade-rc1 / native | 130507198849 | native / native | success | 0 | 0 | 0 | E 5, E 150 bis 152 |
| upgrade-rc1-cf / native | 130507198999 | native / native | success | 0 | 0 | 0 | E 5, E 149 bis 151 |

In keinem der sieben Job-Logs steht eine Zeile mit `##[warning]`, `##[error]` oder dem Wort "different" (je 0 Treffer).

drain_incomplete=1 im Bein upgrade stammt aus der 1.6.2-Phase vor dem Update: "a 1.6.2 companion, the queue did not drain within 1500 s, open=5" (E 71), wie im ersten Lauf. Dazu gehören die einzigen zwei Logzeilen "taken as an outage" des ganzen Laufs (X 42 und X 51 im Bein upgrade, beide vor dem Start des Kopf-Containers, der erst bei X 57 startet). Nach Phase B zählt das Bein 0 solche Zeilen (E 33).

#### Zähler und Nenner je Bein (Wahrheit gegen angezeigt)

"Wahrheit" ist die Zahl der Dateien auf dem Samba-Host über Gerät und Inode, "erwartet" ist Wahrheit plus k, "angezeigt" ist die Zahl der Übersicht.

| Bein | A Zähler Wahrheit / erwartet / angezeigt | A Nenner Regel / erwartet / angezeigt | A % | B Zähler Wahrheit / erwartet / angezeigt | B Nenner Wahrheit / erwartet / angezeigt | notReadable | außerhalb Nenner | a1_rows_checked | B1 vorher / nachher | Fundstelle |
|---|---|---|---|---|---|---|---|---|---|---|
| gate-crawl / wrapped | 29 / 33 / 33 | 31 / 35 / 35 | 94 | 29 / 33 / 33 | 31 / 35 / 35 | 1 / 1 | 0 | 3 / 3 | 40 / 40 | E 21 bis 34 |
| gate-queue / wrapped | 29 / 33 / 33 | 60 / 64 / 64 | 51 | 29 / 33 / 33 | 61 / 65 / 65 | 1 / 1 | 0 | 3 / 3 | 40 / 40 | E 21 bis 34 |
| gate-queue / native | 29 / 33 / 33 | 31 / 35 / 35 | 94 | 29 / 33 / 33 | 61 / 65 / 65 | 1 / 1 | 0 | 3 / 3 | 40 / 40 | E 19 bis 32 |
| upgrade / native | 29 / 33 / 33 | 61 / 65 / 65 | 50 | 29 / 33 / 33 | 61 / 65 / 65 | 1 / 1 | 0 | 3 / 3 | 40 / 40 | E 16 bis 29 |
| upgrade-rc1 / native | 30 / 34 / 34 | 62 / 66 / 66 | 51 | 30 / 34 / 34 | 62 / 66 / 66 | 1 / 1 | 0 | 3 / 3 | 41 / 41 | E 27 bis 40 |
| upgrade-rc1-cf / native | 29 / 33 / 33 | 31 / 35 / 35 | 94 | 29 / 33 / 33 | 61 / 65 / 65 | 1 / 1 | 0 | 3 / 3 | 40 / 40 | E 29 bis 42 |
| v1.6.2 / native | 29 / - / 85 | - / - / 79 | - | 29 / - / 85 | 61 / - / 79 | 1 / - | 0 | - | 95 / 95 | E 15 bis 21 |

Phase A, gelaufene Runden: 0 / 0 in allen sechs Kopf-Beinen. Quote nie über 100 (höchster Wert 94). Das Bein upgrade-rc1 hat eine Datei mehr als die anderen (30 statt 29, 96 statt 95 lebende Zeilen): es legt im Mischbetrieb eine Datei an, um zu zeigen, dass ein Auftrag der rc.1-Companion keinen Schlüssel schreibt (E 24). Der Zusammenhang ist aus dem Ablauf des Beins hergeleitet, das Bein nennt ihn nicht in einer eigenen Zeile.

#### k und Positivkontrolle 3: gemessen gegen hergeleitet

43-25 hat k = 4 und das Soll 16 der Positivkontrolle 3 von Hand hergeleitet, nicht gemessen. Der Lauf hat beide so gezeigt:

- k = 4: in allen sechs Kopf-Beinen liegt die Anzeige in Zähler und Nenner, Phase A und B, genau 4 über der Wahrheit (Tabelle oben). Die Zähler der Freigabe-Identitäten nennen in allen sechs Kopf-Beinen `"hashedVerified":3,"hashedUngrouped":2` (upgrade E 108, upgrade-rc1 E 106, upgrade-rc1-cf E 107, gate-crawl E 97, gate-queue / wrapped E 97, gate-queue / native E 92), also zwei nicht auflösbare Speicher, wie die Herleitung annimmt (zwei Speicher mal zwei Dateien).
- Positivkontrolle 3 (naiver Zähler minus Dateien auf dem Host): Soll 16, gezeigt 16 in allen sechs Kopf-Beinen (gate-crawl E 33, gate-queue / wrapped E 33, gate-queue / native E 31, upgrade E 28, upgrade-rc1 E 39, upgrade-rc1-cf E 41).

Die Konstanten wurden nicht an die Anzeige angepasst; `scripts/ci/coverage_truth.sh` ist seit 43-25 unverändert (`git diff aa5a4ade 2261167b -- scripts/ci/coverage_truth.sh` ist leer).

#### Positivkontrollen 2 und 4, Topologie, Suche

| Größe | gate-crawl / wrapped | gate-queue / wrapped | gate-queue / native | v1.6.2 | upgrade | upgrade-rc1 | upgrade-rc1-cf |
|---|---|---|---|---|---|---|---|
| Gehashte IDs belegt (Speicher mit 32-hex-ID, einer je Mechanismus, Soll 4) | 4, E 6 | 4, E 6 | 4, E 6 | 4, E 6 | 4, E 6 | 4, E 7 | 4, E 7 |
| Zwillinge in Groß- und Kleinschreibung, Zeilen im Dateicache (Soll 2) | 2, E 7 | 2, E 7 | 2, E 7 | 2, E 7 | 2, E 7 | 2, E 8 | 2, E 8 |
| [homes], privat.txt je Nutzer (Soll 2) | 2, E 8 | 2, E 8 | 2, E 8 | 2, E 8 | 2, E 8 | 2, E 9 | 2, E 9 |
| Suchprobe W5, Zeilen wie erwartet (Soll 15 von 15) | 15, E 38 bis 52 | 15, E 38 bis 52 | 15, E 36 bis 50 | 15, E 25 bis 39 | 15, E 37 bis 51 | 15, E 44 bis 58 | 15, E 46 bis 60 |
| Suchgegenprobe W4, Wörter der Wahrheit gefunden | 28 / 28, E 36 | 28 / 28, E 36 | 28 / 28, E 34 | 28 / 28, E 23 | 28 / 28, E 35 | 29 / 29, E 42 | 28 / 28, E 44 |
| Suchfehler in der Zähler-Wahrheit | 0, E 37 | 0, E 37 | 0, E 35 | 0, E 24 | 0, E 36 | 0, E 43 | 0, E 45 |
| Positivkontrolle 4 (Zähler von rc.1, muss über 38 liegen) | entfällt | entfällt | entfällt | entfällt | entfällt | 58, E 20 | 58, E 20 |
| Linkfreigabe ohne Wirkung | nicht eigens gezeigt | nicht eigens gezeigt | nicht eigens gezeigt | nicht eigens gezeigt | nicht eigens gezeigt | nicht eigens gezeigt | nicht eigens gezeigt |

- Suchprobe W5 je Bein: alice und bob finden Bericht.txt und bericht.txt je über ihr eigenes Wort, das Wort der einen Datei liefert die andere nicht (acht Zeilen, die Zwillinge sind zwei Dokumente); carol, alice und bob finden die Dateien unter ihren Unterwurzeln (drei Zeilen); alice und bob finden je ihre privat.txt hinter [homes] und bekommen keinen Eintrag für die des anderen (vier Zeilen).
- Positivkontrolle am Samba-Server in jedem Bein: "the case twins are two files, homes gives each account its own file, the share answers as Daten behind the host in upper case" (zum Beispiel upgrade E 57).
- Positivkontrolle 4: "rc.1 shows 58 documents, 34 files are on the host, the head may show 38" (upgrade-rc1 E 96, upgrade-rc1-cf E 98). Die Schwelle ist strenger als im Plan: der Zähler von rc.1 muss über Wahrheit plus k liegen, nicht nur über der Wahrheit.
- Positivkontrolle 2 (Bein v1.6.2): "1.6.2 shows 85 of 79, truth 29 of 61" (E 80). Positivkontrolle 1: "1.6.2 did not sweep within 240 s behind the blocked gate" (E 78). 6 von 6 Container-Zeilen der gesperrten Dateien failed/gateway_error (E 14).
- Linkfreigabe: jedes Bein legt die Linkfreigabe auf /daten/gemeinsam an (Schritt "public link on a folder of an SMB mount", zum Beispiel upgrade L 1323; scheitert das Anlegen, bricht das Skript ab). Eine eigene Ergebniszeile "ohne Wirkung" gibt es nicht. Dass sie nichts zählt, folgt nur mittelbar aus Zähler und Nenner gleich Wahrheit plus k.

#### Urteile, Sweep, frische Installation

- Gesperrte Dateien nach dem ersten Drain, Kopf-Beine und beide rc.1-Beine: 6 von 6 Container-Zeilen und 6 von 6 Zeilen in oc_findling_file_state skipped/unreadable, 0 Logzeilen "taken as an outage" (gate-crawl E 16 bis 18, gate-queue / wrapped E 16 bis 18, gate-queue / native E 14 bis 16, upgrade-rc1 E 15 bis 17, upgrade-rc1-cf E 15 bis 17). Die sechste Zeile (Datei 158 auf Speicher 16) ist mitbeurteilt.
- Sweep in Phase A, alle sechs Kopf-Beine: "storage sweep, absent=2 gone=1 deselected=0 stamped=1 removed=1" (gate-crawl E 94, gate-queue / wrapped E 94, gate-queue / native E 89, upgrade E 105, upgrade-rc1 E 103, upgrade-rc1-cf E 104); vanished_storages hält den Carol entzogenen Speicher (1).
- Befund B auf dem Runner (die drei gate-Beine, frische Installation): Generation der Dokumentschlüssel nach dem ersten Drain 2 / 2, Backfill-Runden 0 / 0 (gate-crawl E 19 und 20, gate-queue / wrapped E 19 und 20, gate-queue / native E 17 und 18); "B1: both settled reads took 1 s" (E 91, E 91, E 86) statt 213 s im ersten Lauf; storage_sweep_at vor Phase A "not set" (E 92, E 92, E 87). Im Containerlog des Beins gate-queue / native steht vor dem ersten Auftrag "doc key verify, checked=0 corrected=0" (X 22) und keine Zeile "doc key backfill".
- Befund A auf dem Runner: beide rc.1-Beine lesen "installed_version of the companion the leg starts at" 1.6.3-rc.1 / 1.6.3-rc.1 (E 6) und laufen bis zum Ende.
- Kein smbclient unter php -S älter als 60 s, nach den Proben und nach Phase B, in allen Beinen (zum Beispiel upgrade E 66 und E 109).

#### Bein upgrade (1.6.2, Kopf, 1.6.2, Kopf)

- Catch-up 1.5 unter 1.6.2: done nach 210 s (E 14).
- Vor dem Companion-Update: /coverage `{"counting":true,"docKeysMissing":95,"docKeysUnresolved":0,"docKeysCorrected":0}` (E 94). Backfill fertig nach 293 s, 1 Runde: `{"counting":false,"docKeysMissing":0,"docKeysUnresolved":1,"docKeysCorrected":0}` (E 95, L 1567). docKeysUnresolved=1 ist die absichtlich verwaiste Container-Zeile (E 93). Im Containerlog: "doc key backfill waits, the companion has no doc key route, next try in 300 s" (X 68), dann "doc key backfill, done=95 missing=0 unresolved=1" (X 81).
- gone_path: **not_exercised**. Wörtlich: "upgrade after phase B: gone_path=not_exercised (1.6.2 left no queue row for the copy on the gone storage, the head had nothing to claim)" (E 126, L 1631). Vor der Topologieänderung lag für die Kopie von gesperrt-alle.txt auf Speicher 20 keine Queue-Zeile offen: "has 0 open queue row(s), oc_findling_file_state says failed/gateway_error 2026-11-11 12:05:42" (E 103). Nach Phase B steht dasselbe Urteil mit derselben Sekunde (E 32, E 122). Die fünf erreichbaren gesperrten Dateien (85, 121, 122, 158, 159) sind skipped/unreadable mit attempts=2 (E 30, E 31, E 111 bis 121); "refusal streaks renewed once after the update, rows=6" (E 123).
- Folge: das Urteil skipped/gone beim Claim einer Queue-Zeile hat dieser Lauf NICHT gezeigt. Gezeigt ist der Sofort-gone-Weg über den Sweep (oben) und dass der Kopf ein Urteil ohne Queue-Zeile nicht anfasst. Das deckt sich mit der Herleitung in Befund C.
- Rückweg und zweites Update: siehe Ergebniszeilen.

#### Bein upgrade-rc1 (Container zuerst)

- Ausgang: beide Hälften 1.6.3-rc.1 (E 66), Catch-up 1.5 unter rc.1 done nach 200 s (E 18), 95 lebende Zeilen mit einem Schlüssel der Generation 1 (E 19), rc.1 zählt fertig ("counting false and no key missing after 0 s", L 1496).
- Nur der Container auf dem Kopf: nach der ersten Runde trägt keine lebende Zeile mehr einen Schlüssel, 0 von vorher 95 (E 21); /coverage für den Body einer rc.1-Companion 422 (E 22); die Seite zeigt den 1.6.2-Weg, `{"perDocument":false,"counting":false,"percent":89}` (E 23); eine über einen Auftrag der rc.1-Companion indexierte Datei bekommt keinen Schlüssel (E 24, L 1581 und 1582); die Logzeile "another doc key format" erscheint 1 mal (E 98, X 66); für einen Body im Format des Kopfes antwortet der Container `{"counting":true,"docKeysMissing":96}` (E 99).
- Dann die Companion: installed_version 1.6.3 (E 25); Neuaufbau "counting false and no key missing after 281 s" (L 1589), Generation 2 (E 26), "doc key backfill, done=96 missing=0 unresolved=0" (X 140). Danach Zähler und Nenner gleich Wahrheit plus k (Tabelle oben).
- Rückweg auf 1.6.2 und zweites Update: siehe Ergebniszeilen (L 1763 bis 1772).

#### Bein upgrade-rc1-cf (Companion zuerst, Backup-Pause, B1)

- Ausgang wie oben (E 6, E 18, E 19, L 1387 und 1388).
- Nur die Companion auf dem Kopf: /coverage des rc.1-Containers für den Body der Kopf-Companion 422 (E 22, L 1394), für einen Body im eigenen Format 200 (L 1395); die Seite zeigt den 1.6.2-Weg (E 23).
- Backup-Pause, dann der Container auf dem Kopf. Solange die Pause hält: der Meta-Wert beginnt mit "1:" und 95 lebende Zeilen tragen einen Schlüssel, zweimal gelesen (E 24: "meta 1:, 1:", "95, 95"); /coverage 200 mit `{"counting":true,"docKeysMissing":95}` (E 25); die Seite zeigt keine Zahl, `{"perDocument":true,"counting":true,"percent":null}` (E 26); nach 60 s unter der Pause dasselbe, Status paused (E 27, E 100). Im Containerlog steht zwischen "backup pause: paused" (X 75) und "backup pause: running" (X 94) keine Zeile "doc key backfill".
- Nach `occ findling:resume`: "counting false and no key missing after 20 s" (L 1481), Generation 2 (E 28), "doc key backfill, done=95 missing=0 unresolved=0" (X 96). Danach Zähler und Nenner gleich Wahrheit plus k.
- Dieses Bein hat keinen Rückweg und kein zweites Update; dafür gibt es hier keine Zeile, weder ok noch failed (so gebaut, der Rückweg liegt im Bein upgrade-rc1 und im Bein upgrade).

#### Ergebniszeilen

Wörtlich aus den Ergebnisdateien, in dieser Reihenfolge: upgrade E 173 bis 175, upgrade-rc1 E 154 bis 157, upgrade-rc1-cf E 153 und 154.

```
upgrade_1_6_2: ok (1.6.2 to the head, container first, backfill 293 s until counting false, 95 living rows)
rollback_1_6_2: ok (doc_key column 1, index 1, a changed file judged and found by 1.6.2)
second_upgrade_rename: ok (122 living rows, bound 660 s)
mixed_container_first: ok (rebuild 281 s until counting false, 96 living rows)
upgrade_rc1: ok (1.6.3-rc.1 to 1.6.3, container first, rebuild 281 s until counting false, 96 living rows)
rollback_1_6_2: ok (doc_key column 1, index 1, a changed file judged and found by 1.6.2)
second_upgrade_rename: ok (123 living rows, bound 660 s)
mixed_companion_first_pause: ok (rebuild 20 s after the resume until counting false, 95 living rows)
upgrade_rc1: ok (1.6.3-rc.1 to 1.6.3, companion first with a backup pause, rebuild 20 s until counting false, 95 living rows)
```

Zur Schreibweise von second_upgrade_rename: der Plan nennt `second_upgrade_rename=ok`, das Skript schreibt beide Formen. Die Zeile mit Gleichheitszeichen steht im Job-Log und als Notiz in der Ergebnisdatei, die Zeile mit Doppelpunkt ist die Ergebniszeile am Ende. Beide aus dem Lauf:

```
second_upgrade_rename=ok
second_upgrade_rename=ok (bound 2 rounds of 300 s plus 60 s for the start, 122 living rows, took 2 s, /coverage {"counting":false,"docKeysMissing":0,"docKeysUnresolved":0,"docKeysCorrected":1})
second_upgrade_rename=ok (bound 2 rounds of 300 s plus 60 s for the start, 123 living rows, took 2 s, /coverage {"counting":false,"docKeysMissing":0,"docKeysUnresolved":0,"docKeysCorrected":1})
```

Fundstellen: upgrade L 1703 und 1704 (E 167), upgrade-rc1 L 1770 und 1771 (E 148). Das verify von 43-26 Task 3 und `scripts/ci/e2e_head_proof.sh` prüfen diese Zeile nicht.

#### Dauer des Neuaufbaus je 1.000 Zeilen

| Bein | Weg | Dauer bis counting false | lebende Zeilen | rechnerisch je 1.000 Zeilen | woraus die Dauer besteht |
|---|---|---|---|---|---|
| upgrade | 1.6.2 auf Kopf, Container zuerst | 293 s | 95 | 3.084 s | Cooldown von 300 s nach dem 404 der 1.6.2-Companion (X 68) |
| upgrade-rc1 | rc.1 auf Kopf, Container zuerst | 281 s | 96 | 2.927 s | Cooldown von 300 s nach "another doc key format" (X 66) |
| upgrade-rc1-cf | rc.1 auf Kopf, Companion zuerst, nach dem Resume | 20 s | 95 | 211 s | Abfragetakt des Harness und Anlauf der Runde |

Keine dieser Zahlen misst den Durchsatz des Neuaufbaus: bei 95 Zeilen besteht die Dauer aus Wartezeit, nicht aus Arbeit. Als Obergrenze taugt allein die dritte Zeile (211 s je 1.000 Zeilen, selbst sie von der Abfrage bestimmt). Für die Hochrechnung in 43-27 (491.000 Zeilen) bleibt die Messung aus 43-16 die belastbare Zahl (rund 65 s je 1.000 Zeilen auf CI-Hardware, siehe 43-E2E.md); der Lauf hier belegt den Ablauf, nicht die Geschwindigkeit.

#### Laufzeit je Bein gegen die Fristen

Die Frist aus der Matrix (90 oder 150 min) liegt am Messschritt "Build the topology, measure both phases against the truth", nicht am Job; der Job hat 170 min. Zeiten des Schritts aus der Jobs-API des Laufs, Zeiten des Jobs aus `gh run view`.

| Bein | Messschritt von bis | Dauer Messschritt | Frist Messschritt | Dauer Job | Frist Job |
|---|---|---|---|---|---|
| gate-crawl / wrapped | 11:57:03 bis 12:02:57 | 5 min 54 s | 90 min | 6 min 54 s | 170 min |
| gate-queue / wrapped | 11:57:08 bis 12:02:59 | 5 min 51 s | 90 min | 6 min 56 s | 170 min |
| gate-queue / native | 11:57:09 bis 12:02:29 | 5 min 20 s | 90 min | 6 min 25 s | 170 min |
| v1.6.2 / native | 11:57:07 bis 12:07:24 | 10 min 17 s | 90 min | 11 min 21 s | 170 min |
| upgrade / native | 11:57:11 bis 12:38:21 | 41 min 10 s | 90 min | 42 min 18 s | 170 min |
| upgrade-rc1 / native | 11:57:35 bis 12:13:48 | 16 min 13 s | 150 min | 17 min 48 s | 170 min |
| upgrade-rc1-cf / native | 11:57:06 bis 12:09:31 | 12 min 25 s | 150 min | 13 min 27 s | 170 min |

Das längste Bein (upgrade) braucht 46 Prozent seiner Frist, die beiden rc.1-Beine 11 und 8 Prozent.

#### Zeitreserve der gate-Beine gegen den Catch-up nach 300 s

Armierung ist die Logzeile "ExApp findling_backend successfully registered."; der Container muss gestoppt sein, bevor der Catch-up-Zyklus 300 s danach fegt. Der Stopp liegt zwischen dem Ende von B1 und dem Schritt "topology change"; dessen Zeitstempel ist die obere Schranke.

| Bein | Armierung | Beginn B1 | B1 nach der Armierung | "topology change" | gestoppt spätestens nach | Reserve bis 300 s | erster Lauf, Beginn B1 |
|---|---|---|---|---|---|---|---|
| gate-crawl / wrapped | 11:56:58.10 (L 1117) | 12:00:04.43 (L 1329) | 186 s | 12:00:06.09 (L 1334) | 188 s | 112 s | 187 bis 203 s (beide wrapped-Beine) |
| gate-queue / wrapped | 11:57:02.71 (L 1126) | 12:00:08.63 (L 1338) | 186 s | 12:00:10.22 (L 1343) | 188 s | 112 s | 187 bis 203 s (beide wrapped-Beine) |
| gate-queue / native | 11:57:02.33 (L 1185) | 11:59:20.70 (L 1392) | 138 s | 11:59:22.59 (L 1397) | 140 s | 160 s | 121 s |

Mit Fix 1 dauert B1 selbst 1 s. Die Reserve hängt damit an allem davor: Samba, Nextcloud, Proben (in den wrapped-Beinen allein 71 s für die gedrosselten Proben, L 1249 bis 1263 und L 1258 bis 1272), Crawl und Drain (rund 82 s). Sie reichte in diesem Lauf, ist aber eine Eigenschaft des Runners und nicht abgesichert: ein um 112 s langsamerer Aufbau macht die wrapped-Beine wieder ungültig (W5 bricht dann ab, es entsteht keine falsche Zahl).

### Offene und auffällige Punkte trotz grünem Lauf

1. **skipped/gone beim Claim ist nicht gezeigt** (gone_path=not_exercised, Bein upgrade). Ob der Fall eintritt, entscheidet 1.6.2 mit der Zahl der abgelehnten Dateien; mit der Topologie aus 43-25 tritt er nicht ein. Der Zweig `gone_path=exercised` des Harness ist auf keinem Runner gelaufen, nur lokal gegen SQLite.
2. **Der Nenner in Phase A schwankt zwischen den Beinen mit demselben Tor.** Bei "queue busy" zeigen gate-queue / native und upgrade-rc1-cf 35 (Regel 31), gate-queue / wrapped 64 (Regel 60), upgrade 65 (Regel 61), upgrade-rc1 66 (Regel 62). In jedem Bein ist die Anzeige gleich der Regel aus D-43-11 plus k, deshalb ist kein Bein rot. Die Ursache ist aus den Belegen nicht geklärt. Vermutung, nicht belegt: die Regel liest die Zähler des Produkts und die bereits beurteilten Zeilen, und der Unterschied von rund 30 entspricht den 30 Rückstau-Bildern, je nachdem, ob der Poller sie beim Lesen der Übersicht schon übernommen hatte. Phase A prüft damit Anzeige gegen Regel, aber nicht gegen einen festen Wert; für 43-27 zu klären.
3. **"doc key verify, checked=95 corrected=3"** nach der Topologieänderung in den gate-Beinen und im Bein upgrade-rc1-cf (gate-queue / native X 56, upgrade-rc1-cf X 120), "checked=96 corrected=3" im Bein upgrade-rc1 (X 162), "checked=95 corrected=2" im Bein upgrade (X 107). Das Harness prüft diese Zahl nicht. Vermutung, nicht belegt: es sind die Zeilen des Carol entzogenen Speichers, deren Freigabe-Identität mit dem Mount wegfällt (der Weg "Identität ändert sich zwischen Auftrag und Zählung" aus der Verschmelzungsliste von 43-27). Zähler und Nenner stimmen danach in jedem Bein; trotzdem gehört die Zahl in den Audit-Nachtrag.
4. **Zeitabhängigkeit der gate-Beine** (Tabelle oben): Reserve 112 s in den wrapped-Beinen, nicht abgesichert.
5. **Der Cooldown bestimmt die Dauer bei "Container zuerst"**: nach dem Companion-Update vergehen 281 s (rc.1) und 293 s (1.6.2), bis die Seite wieder eine Zahl zeigt, weil das Ende des Cooldowns erst beim nächsten Takt wirkt. Verhalten wie gebaut, für die Texte in 43-12 zu wissen.
6. **Linkfreigabe ohne eigene Ergebniszeile** (siehe oben), nur mittelbar belegt.
7. **PHPUnit lief nicht auf dem Kopf des Laufs** (Pfadfilter), die Summe stammt vom vorigen Kopf a42d2dc6 bei leerem Diff unter php/.
8. **Der parametrisierte rc-Proof (rc-version-proof.yml, rc_version_proof.sh aus Task 1) ist auf diesem Kopf nicht gelaufen.** Der letzte Lauf dieses Workflows ist 42565361965 vom 09.11. auf einem älteren Stand. Er ist nicht Teil des verify von Task 3; belegt ist für ihn nur die lokale Prüfung aus Task 1.
9. **Warnzeilen in den Containerlogs**, alle sieben Beine zusammen: 76 mal "content gateway refused one file, http status 422" (die gesperrten Dateien, erwartet), 72 mal "coverage count without a vector stock" und 24 mal "the vector stock could not be opened, an FileNotFoundError, the search stays lexical" (das Harness startet den Container mit FINDLING_EMBED_ENABLED=false; nicht weiter untersucht), 2 mal "taken as an outage" und 2 mal "indexing pass stopped" (1.6.2-Phase des Beins upgrade, siehe oben). Kein Traceback, keine Zeile ERROR oder CRITICAL.
10. **Nicht Teil dieses Laufs:** Impersonation, ARM, eine echte Fremdinstanz, HaRP im Abnahmetest (HaRP deploy lief als eigener Workflow), mehr als 96 Zeilen im Neuaufbau.
