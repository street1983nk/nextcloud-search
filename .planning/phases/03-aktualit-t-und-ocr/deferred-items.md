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
