# Phase 41: Owner-Vorlage Abnahme Findling 1.6.2 (eine Runde)

Stand: 04.11.2026, 11:05 Uhr

Antwort "wie empfohlen" übernimmt jede Empfehlung; Abweichungen als "H1 b" nennen. Nicht genannte Punkte gelten als wie empfohlen. Bei einem eigenen Wortlaut bitte en, de und fr nennen.

Ehrlich vorab: eine Sichtung der Pause in einer laufenden Instanz ist ohne lokales docker nicht möglich. Diese Runde legt Texte, Diffs und CI-Belege vor; die UI-Sichtung ist ein Owner-Punkt nach dem Release. Nichts ist getaggt, nichts eingereicht.

## Schon entschieden, nur protokolliert (keine Frage)

- D-41-01: Pause auf zwei Wegen, gleiche Wirkung: `occ findling:pause` / `occ findling:resume` und Schalter auf der Admin-Seite.
- D-41-02 bis D-41-04: in der Pause ruhen Indexer, Embedding und Poller; erst nach Checkpoint und Commit meldet der Status "paused"; die Suche läuft weiter.
- D-41-05, D-41-19: die Pause übersteht Neustarts; ist der Wunsch nach einem Neustart nicht lesbar, bleibt die Indexierung angehalten (Status "unknown").
- D-41-07, D-41-08: Backup-Doku mit Weg A (docker stop) und Weg B (Pause), dreisprachig, Kurzfassung.
- D-41-09 bis D-41-11 (#25): Vektorzahl auch über 100 000 im Hintergrund gezählt; größtes Mitglied vertritt die Share-Gruppe.
- D-41-12: Nachaudit-Fixes F-40N-01 bis F-40N-04 (u. a. Retry für gateway_error, 408/429 als Ausfall).
- D-41-13, D-41-14: 1.6.2 in beiden Apps; Audit über v1.6.1..Kopf, Fixes ab MEDIUM.
- D-41-16: Tag, Einreichung und Issue-Antworten nur nach Owner-Wort; Issue-Antworten erst nach dem Store-Release.
- D-41-17: keine Inhalte verlassen den Server, kein externer Dienst.
- D-41-18: Pause wartet auf das Ende des laufenden Stapels (kein Abbruch).
- D-41-20: ein Rebuild hält zwischen zwei Bändern an und setzt nach dem Resume fort.
- D-41-21: PHP-Crawl-Jobs laufen in der Pause weiter (schreiben nur in die NC-Datenbank).

## Block H: neue Katalogsätze (Admin-Seite)

Die Kataloge sind nach dem englischen Quellsatz gekeyt: ein neuer en-Wortlaut ändert den Schlüssel in allen 16 Katalogen (php/l10n/*.json und *.js), in admin.js bzw. AdminViewService.php, im Vertragstest und den fünf Tabellen docs/l10n-*.md, und er braucht vor dem Tag eine neue grüne CI-Runde. es, it, nl, pt_PT und pt_BR sind maschineller Entwurf unter Vorbehalt und gehen mit. Wortlaute zeichengleich aus php/l10n/de.json und fr.json.

**H1: Hinweis zu gateway_error (Plan 41-01, Schlüsselwechsel)**

Grund: der alte Satz versprach einen Neuversuch beim nächsten Lauf, den es bei einer Datei mit gleichem ETag nicht gab; seit 1.6.2 holt der nächtliche Abgleich sie bis zu dreimal neu.

| | alt (1.6.1) | neu (1.6.2) |
|---|---|---|
| en | The next run tries again. | Nextcloud could not open the file, often because its storage was not available. The nightly comparison tries it again up to three times, and a change to the file tries it at once. |
| de | Wird beim nächsten Lauf erneut versucht. | Nextcloud konnte die Datei nicht öffnen, oft weil ihr Speicher nicht verfügbar war. Der nächtliche Abgleich versucht es bis zu dreimal erneut, eine Änderung an der Datei sofort. |
| fr | Une nouvelle tentative aura lieu au prochain passage. | Nextcloud n'a pas pu ouvrir le fichier, souvent parce que son stockage n'était pas disponible. La comparaison nocturne réessaie jusqu'à trois fois, et une modification du fichier relance aussitôt. |

- (a) neu so annehmen.
- (b) eigener Wortlaut (en/de/fr).
- Empfehlung: (a); sagt, was tatsächlich passiert (höchstens drei Neuversuche, Änderung sofort).

**H2: sechs Sätze zur Pause (Plan 41-06, neu)**

| Nr. | en | de | fr |
|---|---|---|---|
| H2.1 Schalter | Pause indexing | Indexierung pausieren | Mettre l'indexation en pause |
| H2.2 Schalter | Resume indexing | Indexierung fortsetzen | Reprendre l'indexation |
| H2.3 pausiert | Indexing is paused for a backup. Search keeps working. | Die Indexierung ist für ein Backup pausiert. Die Suche läuft weiter. | L'indexation est en pause pour une sauvegarde. La recherche continue de fonctionner. |
| H2.4 wird pausiert | Pausing: the current batch finishes first. Start the backup when the status says paused. | Pause wird vorbereitet: der laufende Stapel endet zuerst. Das Backup erst starten, wenn der Status pausiert meldet. | Mise en pause : le lot en cours se termine d'abord. Lancez la sauvegarde quand le statut indique en pause. |
| H2.5 unlesbar | The pause state cannot be read yet, so indexing stays stopped. | Der Pausenzustand ist noch nicht lesbar, deshalb bleibt die Indexierung angehalten. | L'état de pause n'est pas encore lisible, l'indexation reste donc arrêtée. |
| H2.6 Backend zu alt | The backend does not know the pause yet. Update both apps to the same version. | Das Backend kennt die Pause noch nicht. Beide Apps auf dieselbe Version aktualisieren. | Le backend ne connaît pas encore la pause. Mettez à jour les deux applications vers la même version. |

- (a) so annehmen.
- (b) eigener Wortlaut je Nummer (en/de/fr).
- Empfehlung: (a); kurz, jeder Zustand sagt, was der Admin tun soll (Backup erst bei pausiert).

## Block B: Store-Text 1.6.2

Was sich gegenüber 1.6.1 ändert: Version und image-tag 1.6.2, die sechs Doku-Links auf blob/v1.6.2, in der Companion-info.xml zwei neue `<command>`-Einträge (PauseCommand, ResumeCommand; nicht sichtbar im Store-Text). Namen, die sechs Beschreibungen, der discussion-Link 249775 und der Cross-Promo-Satz bleiben Wort für Wort wie 1.6.1 (D-41-15: nur ändern, wenn nötig). Was 1.6.2 bringt, zeigt der Store über CHANGELOG.md [1.6.2].

Diff-Auszug (`git diff v1.6.1..HEAD -- backend/appinfo/info.xml php/appinfo/info.xml`, je Sprache gleich):

```
-Switching from fulltextsearch/Elasticsearch: [steps in the documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.6.1/docs/migrate-from-fulltextsearch.en.md)
+Switching from fulltextsearch/Elasticsearch: [steps in the documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.6.2/docs/migrate-from-fulltextsearch.en.md)
-	<version>1.6.1</version>
+	<version>1.6.2</version>
-			<image-tag>1.6.1</image-tag>
+			<image-tag>1.6.2</image-tag>
-	<commands>...IndexCommand...DiagnoseCommand...PurgeCommand</commands>
+	<commands>...IndexCommand...DiagnoseCommand...PurgeCommand...PauseCommand...ResumeCommand</commands>
```

- (a) bestätigt: so einreichen.
- (b) Änderung nennen.
- Empfehlung: (a); Kurztext-Regel, keine neue Beschreibung nötig.

## Block C: Release-Notiz v1.6.2 (englisch, Faktenliste)

```
Findling 1.6.2. Update both apps; the backup pause needs both on 1.6.2.
- Backup pause: occ findling:pause [--wait], occ findling:resume and a switch on the admin page. Indexing stops and everything is flushed to disk while search keeps working; the pause survives restarts (#37).
- Backup guide in German, English and French (#37).
- Coverage: the vector figure of left out storages is also counted above 100,000 documents, and the largest member represents a share group (#25).
- Files of a storage that was away come back: the nightly comparison tries a gateway_error file again up to three times, and a large unavailable storage no longer holds up the files behind it (#36).
- HTTP 408 and 429 from a proxy count as an outage; a fill level refresh that could not start no longer stops the language line.

**Full Changelog**: https://github.com/street1983nk/nextcloud-search/compare/v1.6.1...v1.6.2
```

- (a) so ins Release übernehmen.
- (b) Änderung nennen.
- Empfehlung: (a); fünf Punkte aus CHANGELOG [1.6.2], keine Messgeschichte.

## Block D: Audit 1.6.2

Audit 41-09 über v1.6.1..738a1373 (audited_head 738a13731f6448aa97f0a752d5553c6c54db3e85): 0 CRIT, 0 HIGH, 0 MEDIUM, 4 LOW, 4 INFO; kein Fix nötig, seitdem kein Code-Pfad geändert (danach nur backend/tests/test_phase41_audit.py und .planning). CI auf 738a1373: HaRP deploy 41803255633 (Upgrade-Strecke mit Zusicherung 13), Security scans 41803255432, OpenSSF Scorecard 41803255431; Python gates 41793610965, Integration 41793611053, Resilience 41793610962, Multi-arch image 41793610951 auf eb4284bc (vom Kopf nur in deploy-harp.yml verschieden); PHP and store metadata gates 41792859857 auf f12649a2 (gleicher php/-Baum), alle success.

F-41A-02 (Catch-up-Fenster von Millisekunden, einmal je Upgrade) geht ohne Owner-Frage nach v1.7. Drei Owner-LOW:

**D1: F-41A-03, Container ohne Companion bleibt still auf "unknown"**

Ohne Companion hält das Backend alle Schreiber (wie D-41-19 entschieden), schreibt aber keine Erklärung ins Log und liest den Wunsch 240 mal je Stunde ohne Rückzugsleiter. Keine Daten in Gefahr (ohne Companion gibt es ohnehin keine Queue).

- (a) annehmen für 1.6.2; v1.7: einmalige WARNING-Zeile und Rückzugsleiter.
- (b) wie (a), plus ein Doku-Satz in docs/backup*.md (dreisprachig, neuer Doku-Commit vor dem Tag).
- Empfehlung: (a); kein Nutzerfall verletzt, der Satz würde einen Zustand erklären, den die Backup-Doku sonst nicht berührt.

**D2: F-41A-01, Stopp eines pausierten Containers schreibt zwei leere Meta-Zeilen**

Nur wenn während einer Kopie nach Weg B der Container gestoppt oder neu gestartet wird. Werte logisch gleich, Volume neu aufbaubar.

- (a) Fix in v1.7 (drei Zeilen in watch.py).
- (b) Fix in 1.6.2 (neuer Code-Kopf, Nachaudit, volle CI-Runde vor dem Tag).
- (c) nur Doku-Satz jetzt: "während der Kopie den Container nicht neu starten" (dreisprachig).
- Empfehlung: (a); Randfall, kein Datenverlust, ein Fix vor dem Tag kostet Nachaudit und volle CI.

**D3: F-41A-04, fp32-Sweep und fp32-Abruf schreiben in der Pause**

Nur nach einem Vorab-Check mit fp32; betrifft models/, nicht den Index; Gewichte werden bei Bedarf neu geholt.

- (a) Fix in v1.7.
- (b) Fix in 1.6.2 (wie D2 b).
- Empfehlung: (a).

## Block E: Umlaut-Audit (Regel 24.10.2026)

Umfang: alle in 1.6.2 neuen oder geänderten deutschen Texte. Vorfilter `grep -nE "(ae|oe|ue)[a-z]|ss[^a-z]"`, dazu eine Suche nach ss statt ß und ASCII-Umlauten (gross, heiss, ausser, schliess, mass, fuer, ueber, koenn, muess, waehr); jede Fundstelle von Hand geprüft.

| Text | Vorfilter-Treffer | echte Funde |
|---|---|---|
| php/l10n/de.json, sieben neue Werte | 1 (zuerst) | 0 |
| php/l10n/de_DE.json, sieben neue Werte | 1 (zuerst) | 0 |
| docs/backup.md (52 Zeilen) | 2 (dauert, aktuellen) | 0 |
| docs/admin-page.md, 40 neue Zeilen | 1 (dauern) | 0 |
| docs/reconcile.md, 30 neue Zeilen | 2 (Dauerlast, neuer) | 0 |
| docs/store-listing.md, Entwurf v1.6.2 (deutsche Prosa) | 4 (neuen, dass, zuerst, englisches does) | 0 |
| README.md, neue Zeile | 0 | 0 |

Ergebnis: 11 Vorfilter-Treffer, 0 echte Funde; keine Korrektur, also kein Block-E-Punkt zur Entscheidung.

## Block G: Backup-Doku (#37)

Drei Dateien, gleiche Gliederung, Kurzfassung als Faktenliste (D-41-08):

| Datei | Zeilen | Abschnitte |
|---|---|---|
| [docs/backup.md](../../../docs/backup.md) | 52 | Was wo liegt; Weg A: Container stoppen; Weg B: Pause, die Suche läuft weiter; Wiederherstellen |
| [docs/backup.en.md](../../../docs/backup.en.md) | 50 | What lives where; Route A: stop the container; Route B: pause, search keeps working; Restoring |
| [docs/backup.fr.md](../../../docs/backup.fr.md) | 52 | Où se trouve quoi; Voie A : arrêter le conteneur; Voie B : pause, la recherche continue; Restaurer |

Inhalt: Einstellungen liegen in appconfig (normales NC-Backup), Volume ist neu aufbaubar, Index enthält Text unverschlüsselt (Backup schützen); Backup erst bei "pausiert"; Pause übersteht Neustarts; Crawl-Jobs laufen weiter; nach Wiederherstellen `occ findling:resume` nicht vergessen. Gate test_backup_docs.py hält den Klartext-Satz in allen drei Sprachen.

- (a) so.
- (b) Änderung nennen.
- Empfehlung: (a).

## Block K: Kenntnis (keine Entscheidung)

- K1: Instanz mit nur einer Storage und globalem 500: jede Datei endet failed(gateway_error) mit höchstens vier Anfragen je Datei und Version; der Gateway-Satz erscheint dabei bewusst nicht (E-40-07-02).
- K2: W-1 (gehäufte gleiche Fehler eskalieren ohne Gutschrift) bleibt, greift aber nur, wenn ein zweiter Speicher betroffen ist; ein einzelner Speicher (auch Storage 0) eskaliert allein nie.
- K3: UPGRADE_FROM_TAG bleibt v1.5.0; die Upgrade-Strecke belegt, dass nach dem Upgrade nichts pausiert ist (Zusicherung 13, HaRP deploy 41803255633: running, pauseWished false, kein `findling/paused` in oc_appconfig).
- K4: bekannte Grenze: Zeilen, die 1.6.0/1.6.1 als gateway_error geschrieben haben, tragen eine alte, hohe Versuchszahl und werden nicht automatisch wiederholt; Abhilfe `occ findling:index --restart` (steht in docs/reconcile.md).
- K5: "Pause wird vorbereitet" kann bei OCR bis etwa 30 Minuten dauern (kein Abbruch, D-41-18); steht in der Doku und im Satz H2.4.
- K6: Mischbetrieb: Companion 1.6.2 mit Backend 1.6.1 zeigt H2.6 "Update both apps to the same version.", occ pause endet mit Exit 1; Companion 1.6.1 mit Backend 1.6.2 läuft normal ohne Pause.

## Block I: Außentexte (Entwürfe, Owner postet)

**I1: Forum-Post** (Thread 249775, Datei `C:/Users/Student/Desktop/Findling_1.6.2_Forum_ENTWURF.md`), wörtlich:

```
Findling 1.6.2 is in the store (update both apps together).

New in 1.6.2:
- Backup pause: occ findling:pause --wait, occ findling:resume, or a switch on the admin page. Indexing stops and everything is on disk, search keeps working
- The pause survives restarts of the container and Nextcloud
- Backup guide in German, English and French
- Coverage on large instances with per-user mounts: the dedup no longer switches itself off above 100,000 documents
- Files of a storage that was away are tried again by the nightly comparison

Changelog: https://github.com/street1983nk/nextcloud-search/releases/tag/v1.6.2
```

**I2: Antwort Issue #37** (erst nach dem Store-Release), wörtlich:

```
1.6.2 is in the app store now (update both apps), with the pause I mentioned. A backup now works like this:

1. `occ findling:pause --wait` (returns once the status says paused), or the switch "Pause indexing" on the admin page, then wait until it says paused
2. Back up the volume `nc_app_findling_backend_data`
3. `occ findling:resume`, or "Resume indexing"

Search keeps working the whole time. The full guide, including restore: https://github.com/street1983nk/nextcloud-search/blob/v1.6.2/docs/backup.en.md

Let me know if this fits your backup setup.
```

**I3: Antwort Issue #25** (erst nach dem Store-Release), wörtlich:

```
1.6.2 is in the app store now (update both apps). Both points from your last comment are in: the vector figure is now worked out in the background above 100,000 documents too, so the dedup no longer switches itself off, and the member with the most files seen represents a share group. The first figure can take a reload or two after the update, since the count runs in the background.

Could you check whether the page now shows something close to 100% for your four shares?
```

- (a) so.
- (b) Änderung je Text nennen.
- Empfehlung: (a); kurz, ohne "Closes", die Issues schließt der Owner nach der Rückmeldung.

## Block F: GO für Tag und Einreichung

EIN Wort für ZWEI unumkehrbare Handlungen, die der Owner selbst ausführt (D-41-16): (1) Tag v1.6.2 annotiert auf den grünen, auditierten Kopf <sha> und Push des Tags, (2) danach Auslösen des Workflows Store submission für beide Apps. Claude bereitet Befehle und Belege vor und prüft danach jede Belegzeile.

Kopf heute: Code-Kopf 738a1373 = audited_head; letzter Commit außerhalb .planning ist 4e369f55 (nur backend/tests/test_phase41_audit.py). Nach dem Entscheid setzt Task 3 den Gesamttext in docs/store-listing.md mit Gate in backend/tests/test_store_metadata.py; der Tag-Kopf ist dann dieser Commit (`git log -1 --format=%H -- . ':!.planning'`), Bedingung: leerer Code-Diff zu 738a1373 und alle sieben Workflows grün per `scripts/ci/head_green.sh`. Da Task 3 backend/tests berührt, laufen Python gates dort neu und decken auch test_phase41_audit.py ab (auf 4e369f55 und 703aad3e gibt es noch keinen CI-Lauf, siehe Belegzeile unten). Der sha steht danach in 41-ABNAHME.md.

CI zum Stand dieser Vorlage: siehe Abschnitt "CI-Beleg der Vorlage" am Ende.

- (a) GO.
- (b) warten.
- Empfehlung: (a).

## Nach dem Release (keine Entscheidung, nur Kenntnis)

- Issue-Antworten #37 und #25 (I2, I3) postet der Owner (Plan 41-12), erst danach ggf. Schließen.
- Forum-Post (I1) postet der Owner.
- UI-Sichtung der Pause (Schalter, Sätze H2.1 bis H2.6) und des Hinweises H1 auf einer laufenden Instanz durch den Owner.
- v1.7-Merkliste: F-41A-01 bis F-41A-04 (deferred-items.md).

## CI-Beleg der Vorlage

Wird nach dem Push dieser Vorlage ergänzt.
