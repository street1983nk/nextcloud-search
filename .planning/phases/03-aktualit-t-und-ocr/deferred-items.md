# Zurückgestellte Punkte, Phase 03

Punkte, die während der Ausführung aufgetaucht sind und bewusst nicht im laufenden
Plan erledigt wurden. Jeder Eintrag nennt den Plan, den Grund und den Ort, an den
er gehört.

## Plan 03-03: Sichtprobe Löschen und Wiederherstellen im Test-Nextcloud

**Was:** Datei löschen, als zweiter Nutzer (`kollegin`) nach einem Wort aus dem
Inhalt suchen, kein Treffer erwartet; Datei wiederherstellen, nach dem nächsten
Poller-Durchgang wieder ein Treffer erwartet. Letztes Abnahmekriterium von Task 3
des Plans 03-03.

**Warum nicht hier erledigt:**

1. Der Container `findling-nextcloud` bindet die PHP-App aus dem Haupt-Checkout
   `C:\Users\Student\nextcloud-search\php` ein und nicht aus dem Worktree dieser
   Welle. Ein Wave-Executor darf den Haupt-Checkout nicht anfassen, also kann der
   neue Listener dort nicht wirksam werden.
2. Der ExApp-Container mit dem Python-Backend läuft derzeit nicht. Ohne ihn gibt
   es keinen Poller-Durchgang, den die Sichtprobe abwarten könnte.

**Wohin es gehört:** in den phasenweiten Integrationsschritt, nachdem die Welle in
den Haupt-Checkout zusammengeführt ist. Passend zu dem End-to-End-Job, den Pattern
3 der Phasenrecherche für `.github/workflows/integration.yml` vorsieht.

**Ersatzdeckung bis dahin:** `test_deleted_file_is_gone_for_another_user` in
`backend/tests/test_poller.py` führt denselben Beweis gegen einen echten Tantivy-
Index und eine echte SQLite, aus der Sicht eines zweiten Nutzers. Was der Test
nicht abdeckt, ist die Nextcloud-Seite: dass die drei Ereignisse tatsächlich
feuern und die Zeile in der Queue landet.

## Plan 03-04: Sichtprobe Ordner-Freigabe im Test-Nextcloud

**Was:** Ordner mit mehreren Dateien freigeben, als Empfänger nach einem Wort aus
einer der Dateien suchen und sie finden; Freigabe entziehen, danach kein Treffer
mehr. Letztes Abnahmekriterium von Task 3 des Plans 03-04.

**Warum nicht hier erledigt:** dieselben zwei Gründe wie bei der Sichtprobe aus
Plan 03-03. Der Container `findling-nextcloud` bindet die PHP-App aus dem
Haupt-Checkout ein, den ein Wave-Executor nicht anfassen darf, und der
ExApp-Container mit dem Poller läuft nicht.

**Wohin es gehört:** in den phasenweiten Integrationsschritt nach dem
Zusammenführen der Welle.

**Ersatzdeckung bis dahin:** `test_unshare_with_empty_user_list_clears_the_prefilter`
in `backend/tests/test_acl_prefilter.py` führt den Beweis für die Container-Seite
gegen eine echte SQLite, aus der Sicht des Nutzers, dem die Freigabe entzogen
wurde. Nicht abgedeckt bleibt die Nextcloud-Seite: dass die drei Share-Ereignisse
feuern und dass der Teilbaum-Job die Nachkommen wirklich auflöst.

## Plan 03-04: Ein wiederhergestellter Ordner braucht den ETag-Abgleich

**Was:** `NodeRestoredEvent` auf einen Ordner reiht nichts für dessen Nachkommen
ein. Die Dateien darin tragen nach dem Löschen einen Tombstone und sind aus dem
Index genommen; sie brauchen also Inhaltsjobs, und `content` ist bewusst keine der
Arten, die `SubtreeExpandJob` verteilt (ein Teilbaum aus Inhaltsjobs ist ein
Neu-Crawl).

**Warum nicht hier erledigt:** ausserhalb des Plans, und der zuständige Mechanismus
ist bereits benannt. Ein Teilbaum mit `kind=content` wäre ein zweiter Weg zum
Neu-Crawl neben dem ETag-Abgleich.

**Wohin es gehört:** Plan 03-12 (ETag-Abgleich). Der Fall "lokal als gelöscht
markiert, in der Seite wieder vorhanden" ist dort ohnehin zu behandeln.

**Zwischenzustand:** ein wiederhergestellter Ordner wird beim nächsten
Abgleichlauf wieder auffindbar, nicht binnen Sekunden. Der Grund steht als
Kommentar im Restore-Zweig von `FileEventListener`.
