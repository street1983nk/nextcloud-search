# Freigaben Phase 45

Freigabe Merge PR57 45-01: "Go" (2026-11-22 01:04, Claude-Code-Chat, Antwort auf Frage a/b/c mit a = beide mergen) Entscheid: ja
Freigabe Merge PR56 45-01: "Go" (2026-11-22 01:04, Claude-Code-Chat, gleiche Antwort) Entscheid: ja
Entscheid docs/l10n-chinese.md englisch 45-01: "Go" (2026-11-22 01:04, Claude-Code-Chat) Entscheid: ja

Hinweis: Zeiten in UTC. Die Freigaben decken nur die zwei Merges mit --match-head-commit auf die geprüften Köpfe (PR57 168b6b13ba7d03b407e94f9f57a17a2970657457, PR56 51690b2ac926bbbb14df4e3f3b5c0fd40bc078d4), keinen Push eigener Commits und keinen Kommentar.

Freigabe Push 45-06: "Ja" (2026-11-22 03:47, Claude-Code-Chat) Entscheid: ja

Hinweis: Zeit in UTC. Die Freigabe deckt den Push der lokalen Commits 45-01 bis 45-06 samt diesem Freigabe-Commit auf main (kein Tag, keine Store-Aktion, kein Kommentar), einen CI-Warter und höchstens einen Rerun fehlgeschlagener Jobs; keinen zweiten Push eines Fixes.

Freigabe Version 45-08: "A" (2026-11-22 05:01, Claude-Code-Chat) Entscheid: ja
Freigabe Changelog 45-08: "A" (2026-11-22 05:01, Claude-Code-Chat) Entscheid: ja

Hinweis: Zeit in UTC. Antwort A = Version ja, CHANGELOG ja (EN gezeigt, DE/FR inhaltsgleich); A heißt auch: liegt der Tag später als 2026-11-22, wird das Datum von [1.7.0] in CHANGELOG.md, CHANGELOG.de.md und CHANGELOG.fr.md beim Release auf das Tag-Datum angepasst. Kein Push, kein Tag, kein Kommentar.

Freigabe Push 45-09: "Ok" (2026-11-22 05:36, Claude-Code-Chat) Entscheid: ja
Entscheid LOW L-45-09-01 45-09: "Ok" (2026-11-22 05:36, Claude-Code-Chat) Entscheid: beheben
Entscheid LOW L-45-09-02 45-09: "Ok" (2026-11-22 05:36, Claude-Code-Chat) Entscheid: beheben
Entscheid LOW L-45-09-03 45-09: "Ok" (2026-11-22 05:36, Claude-Code-Chat) Entscheid: beheben

Hinweis: Zeit in UTC. Der Owner schrieb zuerst "Qualität hat Vorrang" und gab dann mit "Ok" den überarbeiteten Vorschlag des Koordinators frei. Dieser machte aus L-45-09-02 "beheben" statt "akzeptieren", für alle drei Listen (Ordner, Muster, externe Speicher: die Route lehnt ein JSON-Objekt mit 400 und bestehendem Code ab, das Lesen bleibt duldsam), und verlangte für L-45-09-03 vor dem Fix eine Nachstellung auf einer echten Instanz ohne files_external. L-45-09-01: Obergrenze 1000 beim Lesen, Rest als unbrauchbar gezählt. Die Push-Freigabe deckt genau einen Push aller lokalen Commits samt Fixes und diesem Freigabe-Commit nach grünen lokalen Gates, einen CI-Warter (scripts/ci/head_green.sh) und höchstens einen `gh run rerun <id> --failed`; kein Tag, keine Store-Aktion, kein Kommentar.

Entscheid L-45-09-03 enge Form 45-10: "Ok" (2026-11-22 07:26, Claude-Code-Chat) Entscheid: behalten
Freigabe CHANGELOG-Zeile Objekt-Ablehnung 45-10: "Ok" (2026-11-22 07:26, Claude-Code-Chat) Entscheid: ja

Hinweis: Zeit in UTC. L-45-09-03 bleibt in der engeren Form aus 45-09 (leere Menge nur bei fehlender Tabelle oc_external_mounts, nicht bei deaktiviertem files_external), keine Codeänderung. Die CHANGELOG-Freigabe deckt eine kurze Zeile in [1.7.0] von CHANGELOG.md, CHANGELOG.de.md und CHANGELOG.fr.md zur Ablehnung eines JSON-Objekts oder einer Liste mit Lücken in allen drei Regellisten (L-45-09-02); kein Push, kein Tag, kein Kommentar.

Entscheid Fix #59 in 1.7.0 45-17: "Der fix soll in 1.7" (2026-11-22 08:20, Claude-Code-Chat) Entscheid: ja
Freigabe Antwort Issue #59 45-15: "Passt nach dem Release kannst du es posten" (2026-11-22 08:28, Claude-Code-Chat) Entscheid: ja, Claude postet nach Store-Release, Text vorher gegen den fertigen Fix abgleichen
Freigabe V-45-10-02 und V-45-10-03 45-17: "Wenn das die beste Qualität gewährleistet go" (2026-11-22 08:40, Claude-Code-Chat) Entscheid: beheben
Entscheid Rückfragen 45-17: "Ja bitte" (2026-11-22 08:47, Claude-Code-Chat) Entscheid: policy_blocked wie gateway_error bis 3 Nächte; CHANGELOG-Zeile nur für V-45-10-03, nicht für V-45-10-02; CI-Test mit richdocuments, falls ohne Collabora-Server machbar, sonst Kosten am Checkpoint; Requirement COMP-05
Vorgabe Qualität 45-17: "besser mehr Aufwand für beste Qualität, im Anschluss genau alles prüfen, wir wollen kein 1.7.1 um 1.7.0 zu fixen" (2026-11-22 zwischen 08:47 und 09:25 UTC, Uhrzeit nicht exakt überliefert, Claude-Code-Chat) Entscheid: ja
Entscheid E1 Lesen in actAs nur bei Secure View 45-17: "Go mit Empfehlung" (2026-11-22 09:25, Claude-Code-Chat) Entscheid: ja
Entscheid E2 keine Umgehung des Wasserzeichens 45-17: "Go mit Empfehlung" (2026-11-22 09:25, Claude-Code-Chat) Entscheid: ja
Entscheid E3 keine Textausschnitte unter Secure View 45-17: "Go mit Empfehlung" (2026-11-22 09:25, Claude-Code-Chat) Entscheid: ja, Erkennung an der Quelle belegen oder Owner-Checkpoint mit Optionen (45-22)
Entscheid E4 secure-phase vor dem Tag 45-17: "Go mit Empfehlung" (2026-11-22 09:25, Claude-Code-Chat) Entscheid: ja, 45-16 vor 45-14

Hinweis: Zeiten in UTC, wie vom Koordinator übergeben. Die Zeilen decken keinen Push, keinen Tag und keinen Kommentar; die Antwort auf #59 wird erst nach dem Store-Release in 45-15 gepostet, vorher gegen den fertigen Fix abgeglichen (45-21). E1: Findling öffnet eine Datei weiterhin ohne aktive Person und liest sie nur dann erneut in actAs (zuerst als Besitzer, ohne erkennbaren Besitzer als einer der übrigen Nutzer, höchstens 20), wenn das erste Öffnen nachweislich von der Secure View von Nextcloud Office abgelehnt wurde; die Audit-Protokolle nennen für diese Dateien die lesende Person. E2: Gilt das Wasserzeichen auch für den Besitzer, umgeht Findling die Sperre nicht, sondern antwortet mit 403 policy und dem Urteil policy_blocked. E3: Suchtreffer von Dateien, die für die suchende Person unter Secure View oder Wasserzeichen stehen, zeigen Name und Treffer ohne Textausschnitt; die Erkennung wird an der Quelle belegt oder in 45-22 per Owner-Checkpoint mit Optionen entschieden. E4: Die secure-phase (45-16) läuft vor dem Tag und der Store-Abgabe (45-14). Die Sätze zu E1 bis E4 sind aus dem Plan 45-17 (Abschnitte "Entscheid zum Ort und zur Form des Rückfalls" und Objective) gefasst, die Koordinator-Nachricht selbst lag dem Ausführer nicht im Wortlaut vor.

Freigabe Texte #59 45-17: "Go  und für foolfitz auch" (2026-11-22 11:52, Claude-Code-Chat) Entscheid: ja
Freigabe Texte V-45-10-02 und V-45-10-03 45-17: "Go  und für foolfitz auch" (2026-11-22 11:52, Claude-Code-Chat) Entscheid: ja, Form i
Freigabe CHANGELOG-Zeilen 45-17: "Go  und für foolfitz auch" (2026-11-22 11:52, Claude-Code-Chat) Entscheid: ja
Entscheid allGroups 45-17: "Go  und für foolfitz auch" (2026-11-22 11:52, Claude-Code-Chat) Entscheid: G1
Entscheid Gate 1.6.3-Sätze 45-17: "Go  und für foolfitz auch" (2026-11-22 11:52, Claude-Code-Chat) Entscheid: c1
Entscheid Abgleich-Wartezeit 45-17: "Go  und für foolfitz auch" (2026-11-22 11:52, Claude-Code-Chat) Entscheid: d1
Freigabe Korrektur 59 45-21: "Go  und für foolfitz auch" (2026-11-22 11:52, Claude-Code-Chat) Entscheid: ja

Freigegebener Wortlaut der Korrektur 59 (ersetzt im Entwurf unter `## #59` in 45-ANTWORTEN.md genau den zweiten Punkt unter "Fixed in 1.7.0:"):

- If the secure view policy refuses the fetch, Findling retries it as the file's owner before giving up.

Hinweis: Zeit in UTC, wie vom Koordinator übergeben; das Zitat ist die Antwort des Owners auf die Vorlage des Koordinators mit allen Entscheiden "wie empfohlen" (Texte 1 bis 7 wörtlich wie im Checkpoint-Entwurf, V-45-10-02 Form i, allGroups G1, Gate c1, Wartezeit d1) und der Korrektur des #59-Satzes. Ein Nachbau-Weg (e) war nicht nötig, weil in M1, M2, M3 und M5 gesperrt wurde. Kein Push, kein Tag, kein Kommentar; die Antwort auf #59 bleibt bis nach dem Store-Release in 45-15 liegen. Der Zusatz "und für foolfitz auch" betrifft keinen Punkt dieses Checkpoints und ist hier nicht ausgelegt.

Die Texte 1, 2, 3, 5, 6 und 7 gelten wörtlich wie im Plan 45-17 (Abschnitt "Texte für den Owner-Checkpoint"). Maßgeblich für 45-18 bis 45-20 sind im Einzelnen:

- V-45-10-02, Form i: Bestätigungszeile "/Gemeinsam (ID 11), /Gemeinsam (ID 12)" über den vorhandenen Schlüssel `%1$s (ID %2$s)`, kein neuer Satz, keine CHANGELOG-Zeile.
- G1: allGroups bleibt beim Indexieren wirkungslos wie in 1.6.5 (Öffnen außerhalb von actAs, allGroups greift laut Quelle nur bei gesetzter userId); dokumentiert, Mitglieder sehen durch 45-22 keine Textausschnitte. Task 3 bekommt keinen zusätzlichen Fall.
- c1: Der Gate prüft die 1.6.3-Sätze nur gegen ihre Abnahme in docs/store-listing.md und führt SUPERSEDED_IN_1_7_0 mit dem alten unreadable-Satz.
- d1: 45-20 Schritt 0 wartet die drei Abgleiche echt ab (je mindestens eine Stunde, zusammen etwa drei Stunden, keine Docker-Arbeit daneben).
- Text 4, CHANGELOG [1.7.0] Fixed zu #59, FR (im Plan nur "inhaltsgleich", hier der vorgelegte Wortlaut): "Un fichier soumis au filigrane de Nextcloud Office, par exemple partagé sans téléchargement, est lu au nom de son propriétaire ou d'un autre utilisateur autorisé à le lire, au lieu de finir en « Fichier non récupérable » ; les journaux d'audit indiquent cet utilisateur pour cette lecture. Un fichier que le filigrane bloque pour tous les utilisateurs reçoit son propre motif sur la page d'administration (#59)."

Entscheid Fix #25 in 1.7.0 45-23: "Go" (2026-11-22 17:00, Claude-Code-Chat) Entscheid: ja

Hinweis: Uhrzeit ungefähr (etwa 17:00 UTC, vom Koordinator übergeben; die genaue Zeit steht im Chatverlauf). Die Zeile deckt die Behebung beider belegten Befunde aus Issue #25 (mbozem) in 1.7.0: F1, eine Nachzählung blockiert den Abgleich (45-23), und F2, die Ruhemarke hungert den Abgleich auf großen Instanzen aus (45-24), unter der Owner-Regel "kein 1.7.1 um 1.7.0 zu fixen" (TDD, Mutationsgegenproben, Live-Probe in 45-20, secure-phase vor dem Tag). Einen Mindestabstand der Nachzählung von "etwa 6 h" hat der Owner gebilligt; Wert und Texte legt 45-23 Task 1 noch einmal vor. F3 ("JPG-Schleife") ist nicht gedeckt und wartet auf die Logs des Melders. Kein Push, kein Tag, kein Kommentar.

Entscheid V-02-Regel 45-19: "Go mit den Empfehlungen" (2026-11-22 18:37, Claude-Code-Chat) Entscheid: c

Hinweis: Zeit in UTC, wie vom Koordinator übergeben. Die Antwort des Owners bezieht sich auf die im Chat vorgelegten Empfehlungen, hier auf Option c aus 45-19 Task 0: eine Regel nur nach dem Einhängepunkt, gleich welcher Typ, gesetzt in ExternalMountService und gelesen von Liste und Bestätigung (Beispiel /Share mit SMB/CIFS ID 5, SFTP ID 8, SMB/CIFS ID 17: Liste "SMB/CIFS ID 5", "SFTP ID 8", "SMB/CIFS ID 17", Bestätigung "/Share (ID 5), /Share (ID 8), /Share (ID 17)"). Kein Push, kein Tag, kein Kommentar.

Entscheid E3-Weg 45-22: "Go" (2026-11-23 02:42, Claude-Code-Chat) Entscheid: S3
Hinweis: S3 mit S1 (genaue Prüfung der Freigabe-Attribute) für shareDisabledDownload, wie vom Koordinator im Chat vorgelegt; Ergänzungen (a)+(b) unter shareRead, Schutz vor unbekannten Modi über getKeys('files'), fail-closed
Freigabe CHANGELOG E3 45-22: "Go" (2026-11-23 02:42, Claude-Code-Chat) Entscheid: ja
Entscheid Altbestand 45-22: "Go" (2026-11-23 02:42, Claude-Code-Chat) Entscheid: A1

Freigegebener Wortlaut CHANGELOG E3 (Abschnitt [1.7.0] Fixed):

- EN: "Search results of a file that a user may only see under the watermark of Nextcloud Office show no text excerpt to that user."
- DE: "Suchtreffer einer Datei, die eine Person nur unter dem Wasserzeichen von Nextcloud Office sehen darf, zeigen dieser Person keinen Textausschnitt."
- FR: "Les résultats de recherche d'un fichier qu'un utilisateur ne peut voir que sous le filigrane de Nextcloud Office n'affichent aucun extrait de texte à cet utilisateur."

Hinweis: Zeit in UTC, wie vom Koordinator übergeben; das Zitat ist die Antwort des Owners auf die Empfehlung des Koordinators im Chat. Im Einzelnen: unter shareAll, shareRead, allGroups und allTags gilt S3 wie im Audit (`### E3 Erkennung an der Quelle`): shareAll kein Ausschnitt für fremde Dateien; shareRead fremde Dateien und eigene ohne UPDATE nach (a) Rohrechten aus getByFileIds und (b) isUpdateable() am Knoten aus SearchService::readableFile; allGroups nur für Mitglieder der Liste; allTags über getTagIdsForObjects. Ein unbekannter `watermark_*`-Modus auf yes heißt gar kein Ausschnitt (getKeys('files')); wirft die Erkennung, gibt es keinen Ausschnitt. Unter shareDisabledDownload gilt die genaue Prüfung wie richdocuments PermissionManager Z. 230 bis 232: kein Ausschnitt genau dann, wenn die suchende Person die Datei über eine Freigabe mit download=false sieht, nur mit öffentlichen OCP-APIs; lässt sich nicht sauber an der Quelle belegen, dass dabei die Freigabe des Mounts geprüft wird, oder geht es nicht mit öffentlichen APIs, gilt auch dort reines S3, und der Grund steht im Audit. Sind mehrere Modi an, gilt die Vereinigung aller Unterdrückungen. Altbestand A1: Treffer bleiben, ohne Ausschnitt. Kein neuer Oberflächensatz, keine Textfreigabe nötig. Weil S3 allGroups abdeckt, entfällt die erneute G1/G2-Frage. Kein Push, kein Tag, kein Kommentar.

Freigabe Texte #25 45-23: "Go mit den Empfehlungen" (2026-11-22 18:37, Claude-Code-Chat) Entscheid: ja
Entscheid Regeln Nachzählung 45-23: "Go mit den Empfehlungen" (2026-11-22 18:37, Claude-Code-Chat) Entscheid: r1
Entscheid Rückhalt-Weg 45-23: "Go mit den Empfehlungen" (2026-11-22 18:37, Claude-Code-Chat) Entscheid: z1
Entscheid Mindestabstand 45-23: "Go mit den Empfehlungen" (2026-11-22 18:37, Claude-Code-Chat) Entscheid: 6h
Entscheid Locking 45-23: "Go mit den Empfehlungen" (2026-11-22 18:37, Claude-Code-Chat) Entscheid: l1

Hinweis: Zeit in UTC, wie vom Koordinator übergeben. Die Antwort des Owners bezieht sich auf die im Chat vorgelegten Empfehlungen zu den Punkten (1) bis (5) aus 45-23 Task 1: (1) Texte 1 bis 4 wörtlich wie im Plan 45-23 (Abschnitt "Texte für den Owner-Checkpoint"), deshalb steht keine Wortlautzeile darunter; (2) r1, gespeicherte Regeln stoßen die Nachzählung weiter binnen 15 Minuten an; (3) z1, Rückhalt nur über die Zeit im Container (45-24), ausdrücklich mit der Änderung an D-03 aus Phase 03 (Ruhe-Gate: der Rückhalt öffnet nach 48 h auch während der ersten Indexierung einer frischen Instanz, sobald deren Crawl durch ist) und der Last auf einer 4-GB-Box nach T-45-84; (4) Mindestabstand 6 h, gezählt ab dem Start der letzten Runde, keine Pause (I4); (5) l1, Doku und Hinweis auf der Admin-Seite für einen Locking-Cache, den nur ein Prozess sieht, umgesetzt in 45-25. Text 5 ist von diesen Zeilen nicht gedeckt; seine Freigabe steht getrennt in der Zeile `Freigabe Text 5 45-25`. Kein Push, kein Tag, kein Kommentar.

Freigabe Text 5 45-25: "Ok" (2026-11-23 02:08, Claude-Code-Chat) Entscheid: ja
- Text 5 EN: File locking on this server cannot keep background jobs apart: its locks live in a local cache such as APCu, which cron jobs and the web server do not share. Part of the indexing can then run twice at the same time. Redis or the database as the locking backend avoids this.
- Text 5 DE: Die Dateisperren dieses Servers können Hintergrundjobs nicht auseinanderhalten: Sie liegen in einem lokalen Cache wie APCu, den Cron-Jobs und Webserver nicht teilen. Ein Teil der Indexierung kann dann zweimal gleichzeitig laufen. Mit Redis oder der Datenbank für die Dateisperren passiert das nicht.
- Text 5 FR: Le verrouillage des fichiers de ce serveur ne peut pas séparer les tâches d'arrière-plan : ses verrous se trouvent dans un cache local comme APCu, que les tâches cron et le serveur web ne partagent pas. Une partie de l'indexation peut alors s'exécuter deux fois en même temps. Redis ou la base de données comme système de verrouillage évite cela.
Hinweis: Zeit in UTC, wie vom Koordinator übergeben. Der Koordinator hat im Chat den Wortlaut von Text 5 (EN, DE, FR wie in 45-23-PLAN.md, Abschnitt "Texte für den Owner-Checkpoint", Hinweis der Admin-Seite nur für APCu und ArrayCache als Locking-Cache) und die drei Platzhalter vorgelegt; der Owner antwortete "Ok". Der Koordinator hat diese Antwort im Chat als Freigabe von Text 5 und der drei Platzhalter benannt, und der Owner hat nicht widersprochen. es, it, nl, pt_BR, pt_PT und zh_TW sind maschinelle Entwürfe und nicht Teil der Freigabe. Kein Push, kein Tag, kein Kommentar.

Freigabe Platzhalter 45-25: "Ok" (2026-11-23 02:08, Claude-Code-Chat) Entscheid: ja
- Platzhalter EN: Backups
- Platzhalter DE: Sicherungen
- Platzhalter FR: Sauvegardes
Hinweis: Zeit in UTC, wie vom Koordinator übergeben; dasselbe "Ok" wie bei `Freigabe Text 5 45-25`. Der Koordinator hat es im Chat als Freigabe von Text 5 und der drei Platzhalter des Ordnerfelds der Regeln benannt (I-45-19-01), und der Owner hat nicht widersprochen. Das Musterfeld behält `*.photoslibrary` in jeder Sprache; es, it, nl, pt_BR, pt_PT und zh_TW sind maschinelle Entwürfe nach den Sprachdokus und nicht Teil der Freigabe. Kein Push, kein Tag, kein Kommentar.

Entscheid I-45-23-07 45-26: "Wie empfohlen" (2026-11-23 06:08, Claude-Code-Chat) Entscheid: m1
Hinweis: Zeit in UTC, wie vom Koordinator übergeben. "Wie empfohlen" ist als m1 gelesen, die Empfehlung der Frage. Die vorgelegte Frage enthielt den Inhalt von W6 der Planprüfung von 3d18b701; der Koordinator hat im Chat erklärt, dass m1 die Migration von 1.5 ändert, die wegen I-45-26-01 voraussichtlich ohnehin angepasst wird. Kein Push, kein Tag, kein Kommentar.

Entscheid Befund Erneuerung 45-20: "Ok wie empfohlen" (2026-11-23 12:58, Claude-Code-Chat) Entscheid: f1, MEDIUM
Hinweis: Zeit in UTC, wie vom Koordinator übergeben. Befund aus dem Checkpoint von 45-20 Schritt A: Die einmalige Erneuerung `refusal_streaks_1_7_0` lief beim Start des Containers 1.7.0 auch vor einer Begleit-App 1.6.5 (Generation 3), die die erneuerten Dateien wieder mit 500 ablehnte; drei Belastungen einer Ausfall-Eskalation hätten die Serie vor dem Update der Begleit-App verbraucht. f1: Fix per TDD in 45-20, die Erneuerung setzt ihre Marke erst, wenn das Profil Generation 4 meldet; selbst prüfen, ob Belastungen vor Generation 4 danach keine Spur hinterlassen (attempts, Warteschlangenzeilen mit retries, Abschreibung repeatedly_stuck auf der Nextcloud-Seite), sonst die zweite Variante ergänzen; Mutationsgegenprobe rot; Schritte A und B neu fahren, Instanz vorher nachvollziehbar in den Zustand vor A. Keine eigene CHANGELOG-Zeile, der Befund wurde nie ausgeliefert; der Absatz in docs/formats.md folgt dem neuen Verhalten. Kein Push, kein Tag, kein Kommentar.

Freigabe CHANGELOG I-45-26-01 45-20: "Ok wie empfohlen" (2026-11-23 12:58, Claude-Code-Chat) Entscheid: ja

Freigegebener Wortlaut CHANGELOG I-45-26-01 (Abschnitt [1.7.0], Fix-Gruppe):

- EN: "Updating from 1.3.x no longer stops with an "undefined method" error; the update runs through in one go (it broke with 1.5.0)."
- DE: "Ein Update von 1.3.x bricht nicht mehr mit einem Fehler "undefined method" ab, es läuft in einem Durchgang durch (seit 1.5.0 betroffen)."
- FR: "Une mise à jour depuis 1.3.x ne s'arrête plus avec une erreur « undefined method » ; elle se déroule en une seule fois (problème présent depuis 1.5.0)."

Hinweis: Zeit in UTC, wie vom Koordinator übergeben; dasselbe "Ok wie empfohlen" wie beim Entscheid oben. Die Zeile gehört zum Fix I-45-26-01 (Update aus 1.3.x, 45-26) und steht je Sprache unter "### Fixed", "### Behoben" bzw. "### Corrigé" in [1.7.0], wörtlich, Zeilenumbruch wie bei den übrigen Punkten erlaubt. Kein Push, kein Tag, kein Kommentar.

Entscheid Befund Prüfspur 45-20: "Soviel Aufwand wie nötig Hauptsache beste Qualität" (2026-11-23 15:47, Claude-Code-Chat) Entscheid: a4, MEDIUM
Entscheid Team Folder unter shareAll 45-20: "Soviel Aufwand wie nötig Hauptsache beste Qualität" (2026-11-23 15:47, Claude-Code-Chat) Entscheid: INFO, kein Befund
Entscheid Rückstand F2 45-20: "Soviel Aufwand wie nötig Hauptsache beste Qualität" (2026-11-23 15:47, Claude-Code-Chat) Entscheid: t1, Ersatz t2 nur bei belegtem RAM-Abbruch, t3 nicht

Hinweis: Zeit in UTC, beim Eintrag per `date -u` genommen, weil der Koordinator keine Uhrzeit übergab. Das Zitat ist die Antwort des Owners auf den zweiten Checkpoint von 45-20; der Koordinator hat sie als "jeweils die Option mit der besten Qualität, Aufwand egal" gelesen. a4: die Prüfspur nennt die lesende Person wirklich, über ein `OCP\Log\Audit\CriticalActionPerformedEvent` aus dem Gateway nur bei einem Lesen in actAs (fileid, Pfad, uid, nie Inhalt; ohne admin_audit wirkungslos), dazu die uid in der eigenen info-Zeile des Gateways (a1); TDD mit roten Mutationen, echter Beleg in audit.log; Text 4 bleibt unverändert; a2 (Sitzung setzen) ausgeschlossen; ist a4 an der Quelle nicht tragfähig, neuer Checkpoint. Team Folder unter shareAll: Findling liest nur, was die Person selbst herunterladen darf (groupfolders `GroupFolderStorage::getOwner` Z. 50-61, WebDAV-Gegenprobe), Erwartungstabelle und Doku nennen das. F2: echtes Container-Backend am Kopf mit echtem OCR-Rückstand, streng seriell. Kein Push, kein Tag, kein Kommentar.

Entscheid Schritt C(c) 45-20: "Soviel Aufwand wie nötig Hauptsache beste Qualität" (2026-11-23 15:47, Claude-Code-Chat) Entscheid: c2, LOW
Hinweis: Zeit in UTC; das Zitat ist die Owner-Vorgabe vom zweiten Checkpoint (Zeit wie oben), der Koordinator hat daraus am 2026-11-23 16:23 UTC c2 abgeleitet; keine neuen Nutzertexte, deshalb keine Textfreigabe. Inhalt: die warning-Zeile des Gateways für eine andere ForbiddenException nennt zusätzlich `origin` (Klasse::Funktion des ersten Frames, ohne Klasse nur die Funktion, ohne Frame `unknown`), nie die Meldung, nie Pfade, nie Argumente; TDD mit roten Mutationen (Herkunft fehlt, Meldung geloggt, Argument geloggt); Probe (c) live neu. Die Plan-Erwartung "nextcloud.log zeigt 'Access denied by access control'" war falsch, weil das Gateway die Ausnahme absichtlich fängt; verify von Task 1 prüft deshalb statt der Literalzeile drei Belege: die Quellzeile `throw new ForbiddenException('Access denied by access control', false);` (Operation.php v6.0.1 Z. 118, mit Z. 115-117 wörtlich im Audit), die debug-Zeile von files_accesscontrol "Access denied for path ... matches rules" als Beleg des Wurfs und die warning-Zeile mit `origin`; ohne einen dieser Belege bleibt verify rot. Kein Push, kein Tag, kein Kommentar.

Entscheid Review R-45-21-01 45-21: "Ok" (2026-11-24 02:51, Claude-Code-Chat) Entscheid: beheben
Entscheid Review R-45-21-02 45-21: "Ok" (2026-11-24 02:51, Claude-Code-Chat) Entscheid: beheben
Entscheid Review R-45-21-03 45-21: "Ok" (2026-11-24 02:51, Claude-Code-Chat) Entscheid: beheben
Entscheid Review R-45-21-04 45-21: "Ok" (2026-11-24 02:51, Claude-Code-Chat) Entscheid: beheben
Entscheid Review R-45-21-05 45-21: "Ok" (2026-11-24 02:51, Claude-Code-Chat) Entscheid: beheben
Entscheid Review R-45-21-12 45-21: "Ok" (2026-11-24 02:51, Claude-Code-Chat) Entscheid: beheben
Entscheid Review R-45-21-13 45-21: "Ok" (2026-11-24 02:51, Claude-Code-Chat) Entscheid: beheben
Entscheid Review R-45-21-14 45-21: "Ok" (2026-11-24 02:51, Claude-Code-Chat) Entscheid: beheben
Entscheid Review R-45-21-15 45-21: "Ok" (2026-11-24 02:51, Claude-Code-Chat) Entscheid: beheben
Hinweis: Zeit in UTC, wie vom Koordinator übergeben. Das "Ok" des Owners antwortet auf die Empfehlung des Koordinators "alle 8 beheben, jeweils mit Test vorab": R-45-21-01 bis -04 aus dem Review dieses Executors, dazu die vier Befunde des zweiten Prüfers (R-45-21-12 MEDIUM, R-45-21-13 bis -15 LOW). R-45-21-05 ist U-45-20-03 aus der Gegenprobe 45-20 und schon behoben (c9dc3270, 0f6afac7), die Zeile bestätigt das nur. Für R-45-21-12 gilt die Semantik der Empfehlung: ein ausgeschlossener Speicher bleibt ausgeschlossen, auch wenn Teile davon geteilt sind. Neue nutzersichtbare Texte (UI oder CHANGELOG) aus diesen Fixes gehen nur über einen eigenen Checkpoint mit Entwurf EN, DE und FR. Kein Push, kein Tag, kein Kommentar.

Freigabe Texte Review 45-21: "Ok" (2026-11-24 12:50, Claude-Code-Chat) Entscheid: ja
Entscheid Review R-45-21-19 45-21: "Ok" (2026-11-24 12:50, Claude-Code-Chat) Entscheid: beheben

Freigegebener Wortlaut des Satzes für den Fehlerzustand der Speicherliste (R-45-21-13; Ort: Admin-Seite, Abschnitt Regeln, unter "Externen Speicher indexieren", id findling-rules-mounts-failed, class settings-hint, per p($l->t(...)), nur im Fehlerzustand, wenn Settings\Admin failed meldet):

- EN: The list of external storage could not be read. Saving the rules keeps every external storage that is kept out of the index. Reload the page to see the list again.
- DE: Die Liste der externen Speicher konnte nicht gelesen werden. Beim Speichern der Regeln bleibt jeder ausgeschlossene externe Speicher ausgeschlossen. Laden Sie die Seite neu, um die Liste wieder zu sehen.
- FR: La liste des stockages externes n'a pas pu être lue. L'enregistrement des règles conserve chaque stockage externe exclu de l'index. Rechargez la page pour revoir la liste.

Hinweis: Zeit in UTC, wie vom Koordinator übergeben. Das "Ok" des Owners deckt zwei Punkte: (1) den Satz oben für R-45-21-13 (TDD, 18 Kataloge, Schlüsselzahl 387; de_DE wie de; es, it, nl, pt_BR, pt_PT und zh_TW sind maschinelle Entwürfe nach dem Entwurf des Koordinators, gekennzeichnet wie bisher, und nicht Teil der Freigabe) und (2) die Korrektur des CONTROL-2-Wortlauts in scripts/ci/update_in_process_proof.sh (R-45-21-19: die Meldung "CONTROL 2 BROKEN: ... passed the probe" erschien auch bei einem anders gearteten Fehlschlag, gesehen unter Mutation M49; die Meldung unterscheidet jetzt den bestandenen Lauf von einem Lauf, der aus anderem Grund fehlschlug, mit Test vorab). Kein Push, kein Tag, kein Kommentar.

Freigabe Rückfrage Issue #25 (F3): "Go" (2026-11-24, Claude-Code-Chat) Entscheid: posten
- Gepostet als street1983nk: https://github.com/street1983nk/nextcloud-search/issues/25#issuecomment-7136596839
- Inhalt: zwei SQL-Abfragen auf oc_findling_queue (zweimal im Abstand von 5 bis 10 Minuten, einmal GROUP BY kind) zur Klärung des Auslösers der F3-Schleife, plus Ankündigung des Backstops in 1.7.0 (failed nach drei identischen Durchläufen).
- Wortlaut vom Owner im Chat freigegeben ("Go"), Entwurf vorher gezeigt. Dasselbe Owner-"Ok" vom 24.11. deckt den Umfang von Plan 45-27 (Zählfehler requeueAs, pass-finished-Zeile, Backstop mit Wirkung); Dokumentation dazu im Plan.

Freigabe Text F3 45-27: "Ok" (2026-11-24 16:30, Claude-Code-Chat) Entscheid: ja

Hinweis: Zeit in UTC, wie vom Koordinator übergeben. Das "Ok" des Owners antwortet auf die Checkpoint-Vorlage von 45-27 Task 1 ohne Abweichung, damit gelten die Entwürfe des Plans wörtlich: (1) Text F3 für CHANGELOG [1.7.0] "### Fixed" in EN, DE und FR wie in 45-27-PLAN.md, Abschnitt "Texte für den Owner-Checkpoint" (kein close/fix/resolve-Wort vor der Issue-Nummer); (2) die warning-Zeile des Backstops "one file circles between the queues, %d demanded handovers to the ocr track with the same bytes, file id %d, written off as failed(repeatedly_stuck)" samt Zählweise: die Anzahl sind die VERLANGTEN Übergaben, beim Auslösen drei (zwei erfolgte plus die verweigerte dritte), nur Datei-ID und Anzahl, nie Name oder Pfad (B6); (3) die Feststellung, dass failed(repeatedly_stuck) die bestehenden Sätze der 18 Kataloge nutzt und kein neuer nutzersichtbarer Text entsteht (Schlüsselzahl bleibt 387); entstünde doch einer, stoppt der Executor und holt eine eigene Freigabe mit Entwurf EN/DE/FR und 18 Katalogen; (4) zur Kenntnis genommen: die drei Folge-Punkte I-45-27-01 (H1-Ursache, wartet auf die DB-Antwort des Melders), I-45-27-02 (OCR-Reserve im Claim) und I-45-27-03 (Give-up-Semantik) bleiben offen und werden mit Beleg in 45-AUDIT.md dokumentiert, dazu der Hinweis an 45-10 zu den repeatedly_stuck-Bestands-Konsumenten in deploy-harp.yml. Kein Push, kein Tag, kein Kommentar.

Freigabe Push 45-10: "Go" (2026-11-25 15:21, Claude-Code-Chat) Entscheid: ja
Hinweis: Uhrzeit in UTC ist die des Pushs laut `git reflog show origin/main` (`8c02b706 refs/remotes/origin/main@{2026-11-25 16:21:21 +0100}: update by push`); das "Go" des Owners fiel kurz davor, der Koordinator hat Push und Go übergeben, die genaue Minute des Go steht im Chatverlauf. Gedeckt: genau der Push aff5f1d3..8c02b706 auf main (45-27 und die Planungs-Commits davor), ein CI-Warter (beim Koordinator), höchstens ein Rerun fehlgeschlagener Jobs. Kein Tag, keine Store-Aktion, kein Kommentar. Fixes aus dem Volltest brauchen eine eigene Zeile `Freigabe Push 45-10 Fix`.
