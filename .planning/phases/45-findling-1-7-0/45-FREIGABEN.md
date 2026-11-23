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
