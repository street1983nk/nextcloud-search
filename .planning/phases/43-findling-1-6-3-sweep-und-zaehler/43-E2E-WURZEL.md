# 43-E2E-WURZEL: End-to-End-Beleg mit Unterwurzeln, Schreibweisen und gehashten IDs (Plan 43-26 Task 3)

Lauf-ID: 42991291089
Kopf-SHA: a42d2dc6dcbbf41a55234081aa018aa74f01f064
Ergebnis: ROT. Ein Bein grün (v1.6.2 / native), sechs Beine rot. Der Lauf belegt den Kopf nicht.

Workflow "Coverage end to end", workflow_dispatch, gestartet 2026-11-11 08:58:41 UTC. Alle Uhrzeiten unten sind UTC aus den Job-Logs.

Stand dieses Dokuments: erster Lauf ausgewertet, Fix 1 liegt lokal vor, ist nicht gepusht und nicht gelaufen. `scripts/ci/e2e_head_proof.sh` liest deshalb weiter das Paar oben und endet für jeden Kopf ungleich 0 (der Lauf ist nicht grün). Das ist der richtige Zustand, solange kein grüner Lauf existiert.

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

Lauf steht aus, Freigabe des Owners offen. Die Commits liegen nur lokal auf main; nichts ist gepusht, kein Workflow ist gestartet. Die beiden Zeilen für Lauf und Kopf dieses Abschnitts kommen erst nach dem nächsten Lauf dazu, bis dahin trägt der Abschnitt absichtlich kein Paar.

| Befund | Art | Änderung | Commits |
|---|---|---|---|
| B | Produkt, TDD | `worker/doc_keys.py`: eine Runde ohne state.db kommt nach `DOC_KEY_NO_STATE_SECONDS` (5 s) wieder statt nach einem Takt; jedes andere Ergebnis einer Runde behält den Takt. Kein neuer Meta- oder AppConfig-Schlüssel, keine Migration, kein Schema. Paket-Baumhash 71385c59 nach 6ef6beba, 83 Dateien | 07eadd03 (RED), e02ff71f (GREEN) |
| A | Harness | `coverage_e2e.sh` liest die Version der installierten Companion aus `apps/findling`; `backend_version` meldet ein fehlendes Verzeichnis beim Namen | a311b827 |
| C | Harness | Die Erwartung für die Kopie auf dem entfernten Speicher hängt an ihrer Bedingung, gemessen bei gestopptem Container direkt vor der Topologieänderung: lag eine Queue-Zeile offen, muss skipped/gone stehen; lag keine offen, muss das Urteil von vorher Byte für Byte unverändert stehen. Das Bein sagt mit `gone_path=exercised` oder `gone_path=not_exercised`, welcher Fall lief. Die sechste gesperrte Zeile (Speicher 16) wird mitbeurteilt. Dazu Diagnosezeilen der Queue vor dem Update und vor der Topologieänderung und das ganze Backend-Log als Artefakt | 76be7820 |

Zusätzlich im Harness, zu Befund B (Commit f4375578): die Beine gate-crawl und gate-queue lesen vor B1 den Zustand statt einer Zeit (Meta-Wert trägt Generation 2, keine Backfill-Runde auf der frischen Installation). Fehlt die Generation, endet das Bein dort als Produktbefund und nicht erst an W5.

Lokale Belege für Fix 1 (kein Lauf auf einem Runner):

- Befund B: RED 3 failed, 86 passed (test_doc_keys, alle drei AssertionError); GREEN 92 passed, zwanzigmal hintereinander; 13 Pflichtmodule plus Nachbarn 1325 passed, 7 skipped und 464 passed; Gegenprobe mit 13 einzelnen Mutationen von doc_keys.py, 13 rot, 0 Überlebende.
- Befund A: die Welt der Gegenprobe verschiebt die Companion jetzt wie die Setup-Aktion, und der Anfang des Beins wird aus dem Skript geschnitten. Das Skript des Laufs scheitert darin mit derselben sed-Zeile (6 von 6 Fällen), das neue besteht 34 von 34 Fällen.
- Befund C: judge_locked gegen echte SQLite-Datenbanken im Zustand des Laufs und in den Zuständen darum herum. Das Skript des Laufs zeigt den Fehlschlag des Laufs und den blinden Fleck der sechsten Zeile (5 von 5 Fällen), das neue besteht 18 von 18 Fällen.
- Zustandsprüfung vor B1: 9 von 9 Fällen. Selbsttest von e2e_head_proof.sh: 24 Fälle, 0 Fehler.

Bekannte Grenzen nach Fix 1:

- Zwischen der Geburt der state.db und der nächsten Runde (höchstens 5 s) kann ein Auftrag schon einen Schlüssel schreiben; die Runde setzt ihn zurück und holt ihn im selben Zug neu. Antwortet die Companion in diesem Augenblick nicht, wartet der Rest auf den nächsten Takt.
- Bei "Companion zuerst" nimmt ein rc.1-Container Schlüssel im Format 2 ungeprüft an; der Kopf-Container setzt sie mit Generation 2 zurück, weil er sie von Format-1-Schlüsseln nicht unterscheiden kann.
- Zeitabhängigkeit im Harness, schon vor diesem Lauf vorhanden und durch W5 abgesichert: in gate-crawl und gate-queue muss der vom Setup armierte Container innerhalb von 300 s nach der Armierung gestoppt sein, sonst fegt der Catch-up-Zyklus und der Lauf ist ungültig. Gemessen in diesem Lauf: B1 beginnt 121 s (native) und 187 bis 203 s (wrapped) nach der Armierung. Das Produktverhalten ist richtig; lösen ließe sich die Abhängigkeit nur im Harness (Catch-up abwarten und den Sweep-Stempel altern wie in den rc.1-Beinen), das ändert aber die Aussage von Phase A und ist nicht Teil von Fix 1.
