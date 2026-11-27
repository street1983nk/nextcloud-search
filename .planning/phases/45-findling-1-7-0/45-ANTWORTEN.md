# Antworten Phase 45

Store-Beleg (45-15 Task 1): Abfrage https://apps.nextcloud.com/api/v1/apps.json am 2026-11-27 00:18:47 UTC: `findling`, erstes Release `1.7.0`, lastModified 2026-11-26T21:29:54Z. `findling_backend` steht nicht in apps.json (External App), Abfrage über appapi_apps.json siehe Zeile darunter. Owner-Sichtprüfung "1.7 ist im Store" (Owner, gemeldet vor 2026-11-27 00:18 UTC, Claude-Code-Chat).
Store-Beleg Backend: Abfrage https://apps.nextcloud.com/api/v1/appapi_apps.json am 2026-11-27 00:29:04 UTC (B9, mehr als 10 Minuten nach der ersten): `findling_backend`, erstes Release `1.7.0`, lastModified 2026-11-26T21:29:55Z. Beide Apps nennen damit 1.7.0 (D-45-16).

## PR #60

Verlauf: foolfitz öffnet am 2026-11-22 09:32 den zweiten Schritt von #53 (body_zh, Schema 3 auf 4 ohne erzwungenen Neuaufbau). Der Owner gibt am 2026-11-22 11:54 die Richtung frei (Han und Latin, BODY_BOOST zh 0.3, Merge nach 1.7.0) und nennt drei Kleinigkeiten; foolfitz liefert sie am selben Tag in drei Commits. Der Owner bittet am 2026-11-22 14:54 um eine Korrektur der Tabelle ("(shipped)" nur in der 0.3-Zeile) und sagt zu: "Yes, please rebase once 1.7.0 is out, I'll ping you here when it's tagged." Letzte Nachricht foolfitz 2026-11-22 15:23: korrigiert in cef6ab37, "I will rebase once 1.7.0 is tagged." Der PR ist offen.

Ping (Entwurf):

1.7.0 is tagged and released: https://github.com/street1983nk/nextcloud-search/releases/tag/v1.7.0

So this is ready for the rebase onto main whenever you have time, as agreed. Thanks for waiting.

Frage an den Owner: "@foolfitz" voranstellen? Empfehlung nein, foolfitz ist Autor des PR und wird bei jedem Kommentar ohnehin benachrichtigt.
Empfehlung Schließen: nein. Der PR ist offen, wartet auf Rebase, Prüfung und Merge.

## #45

Verlauf: chocology bittet am 2026-11-04 11:24 (Findling 1.6.1, SMB-Speicher) um einen Ausschluss je externem Speicher neben dem Schalter für externe Speicher und um eine Anzeige der freien Plätze (oder ein höheres Limit als 64), dazu eine bessere Meldung bei `no_wildcard`. Der Owner sagt am 2026-11-04 11:41 einen Ausschluss je Speicher und die Anzeige der freien Plätze für 1.7 zu. Das ist die letzte Nachricht; seitdem nichts Neues.

Entwurf:

Thanks again for the detailed request. 1.7.0 is in the app store now (update both apps), and it covers both points:

- Under the switch for external storage there is now a list of the storages set up by an admin. Clear the tick of your SMB storage and its documents leave the index at the next comparison run. New folders on it stay out as well, since the whole storage is excluded. Storage that users add themselves still follows the main switch.
- The admin page shows how many slots are free for excluded folders and for excluded patterns. A folder entry with * or ? now points you to "Excluded patterns", and a pattern without * or ? names both ways.

The limit of 64 folders stays, but with the exclusion per storage you shouldn't need the wildcard workaround anymore.

Release: https://github.com/street1983nk/nextcloud-search/releases/tag/v1.7.0
Feature list: https://github.com/street1983nk/nextcloud-search/blob/main/README.en.md#what-findling-does

If you find the time, I'd be glad to hear how it works on your SMB setup.

Empfehlung Schließen: nein, noch nicht. Beide Punkte sind ausgeliefert, aber der Entwurf bittet um eine Rückmeldung aus der SMB-Umgebung; schließen nach der Rückmeldung (oder nach etwa zwei Wochen ohne Antwort, mit Hinweis auf Wiedereröffnen).

## #56

Verlauf: foolfitz öffnet am 2026-11-20 13:29 den zh_TW-Katalog (erster Schritt von #53) und fragt, ob `docs/l10n-chinese.md` auf Englisch bleiben darf. Der PR wurde am 2026-11-22 01:05 gemergt; im PR steht kein Kommentar, die Frage zur Sprache des Dokuments ist dort also noch unbeantwortet (der Entwurf aus 45-PR-REVIEW.md beantwortet sie). Letzte Nachricht: die PR-Beschreibung vom 2026-11-20.

Entwurf:

Thank you, merged and shipped in Findling 1.7.0, which is in the app store now: https://github.com/street1983nk/nextcloud-search/releases/tag/v1.7.0

Keeping docs/l10n-chinese.md in English is fine, no translation needed. The new sentences of 1.7.0 got a first Traditional Chinese version from us, and I've asked you in #53 to look them over.

Empfehlung Schließen: entfällt, der PR ist seit 2026-11-22 gemergt und damit geschlossen.

## #57

Verlauf: foolfitz öffnet am 2026-11-20 13:29 den Fix für `locale()` unter dreiteiligen Locales wie zh_Hant_TW, mit Test samt Positivkontrolle, und schlägt eine CHANGELOG-Zeile vor. Gemergt am 2026-11-22 01:04 UTC; im PR steht kein Kommentar. Der Rückfall auf die Seitensprache (root.lang) wurde von uns nachgezogen und steht im CHANGELOG 1.7.0 ("also when it falls back to the language of the page"). Letzte Nachricht: die PR-Beschreibung vom 2026-11-20.

Entwurf:

Thanks a lot, merged and released in Findling 1.7.0, which is in the app store now: https://github.com/street1983nk/nextcloud-search/releases/tag/v1.7.0

Great catch, and the test with the old function as a control is exactly how we like it. I added one small follow-up on top: the fallback to the page language now gets the same underscore treatment.

Empfehlung Schließen: entfällt, der PR ist seit 2026-11-22 gemergt und damit geschlossen.

## #53

Verlauf: foolfitz schlägt am 2026-11-13 10:16 Chinesisch in vier Schritten vor (zh_TW-Katalog, body_zh, OCR chi_tra, Messbericht) und fragt nach Umfang, Feldname, Snippets und Namen/Titeln. Der Owner sagt am 2026-11-13 15:35 zu (opt-in wie Tschechisch, `body_zh`, Snippets nach den Messungen, Namen und Titel getrennt, Schema-Schritt nach dem Vorbild `body_cs`). Das ist die letzte Nachricht im Issue; Schritt 1 ist #56 (gemergt), Schritt 2 ist PR #60 (offen, Merge nach 1.7.0).

Entwurf:

Quick update: 1.7.0 is in the app store and ships your zh_TW catalogue from #56. Thanks again.

After your PR, 1.7.0 added 33 sentences to php/l10n/zh_TW.json that we translated ourselves: 21 new ones, 2 reworded ones and 10 existing ones that now have a plural form. They are the lines at v1.7.0 that differ from your PR head (51690b2a): mostly the list of external storages and its free slots, the hints for * and ? in folders and patterns, the reason "Blocked by a rule" for files under the Nextcloud Office watermark, the note on a long queue, the warning about file locking, and the example path in "Look up one file". Could you read them over when you have time? A small PR or a comment here, whatever suits you.

body_zh comes with #60, which can be rebased now that 1.7.0 is tagged.

Schlüssel (Stand v1.7.0 gegen 51690b2a, nur zur Information, nicht Teil des Kommentars):
- neu (21): "%1$s of %2$s slots free"; "0 of %s slots free. Remove an entry to add another one."; "1 of %s slots free. This is the last one."; "A long queue has held the comparison run back for longer than its interval. ..."; "A rule keeps Findling from reading the file as any of the users asked, ..."; "A storage you include again is indexed on the next regular comparison run."; "Backups"; "Blocked by a rule"; "External storage is not enabled on this server."; "External storage to index"; "File locking on this server cannot keep background jobs apart: ..."; "Folders take no * or ?. For a pattern like Backup* use \"Excluded patterns\"."; "ID %s"; "No external storage has been set up by an admin."; "Remove indexed content? Excluding the external storage %s ..."; "Remove indexed content? Excluding the external storages %s ..."; "Storage set up by an admin. Clear the tick of a storage ..."; "The list of external storage could not be read. ..."; "This entry contains * or ?, which folders do not support, ..."; "\"Index external storage\" is off, ..."; "alice/files/Contracts/Rent.pdf"
- umformuliert (2): "The file is still there. Check the advanced permissions ... asks its owner first, then its other users in alphabetical order, 20 at most ..."; "This entry has no * or ?. Add whole folders under \"Excluded folders\", or use a pattern like Name*."
- mit Pluralform (10): "_%n file could not be read or got stuck repeatedly. ..._"; "_%n file is searchable. ..._"; "_%n file, %2$s with OCR. About %3$s and about %4$s of index._"; "_%n file, %2$s with OCR._"; "_OCR limit %n page per file, set by %2$s_"; "_Re-embedding of %n document, estimated about %2$s. ..._"; "_Re-embedding of %n document. ..._"; "_Remove indexed content? Excluding %1$s also removes %2$s ..._"; "_Removing an entry takes effect within %n hour, ..._"; "_The share cannot be worked out right now because the backend does not answer. ..._"
Zählung: 387 Schlüssel an v1.7.0 gegen 366 am PR-Kopf, 33 Zeilen neu oder anders (21 + 2 + 10), 12 alte Zeilen entfallen (die 10 Vorgänger der Pluralformen und die 2 alten Fassungen der umformulierten Sätze); Vergleich per `comm` über die sortierten Zeilen beider Stände.

Empfehlung Schließen: nein. #53 ist das Sammel-Issue für alle vier Schritte; body_zh (#60), OCR chi_tra und der Messbericht stehen aus.

## #59

Verlauf: justemu meldet am 2026-11-22 07:55 (Findling 1.6.5, NC 35.0.3, richdocuments 12.0.2), dass zwei Dateien unter dem Wasserzeichen nie indexiert werden: Findling liest als alphabetisch erster Leser (der Freigabe-Empfänger ohne Download), die Secure-View-Richtlinie lehnt ab, es wird kein anderer Leser versucht, und die Admin-Seite nennt einen Speicherausfall. Gewünscht: nächsten Leser versuchen, Richtlinien-Ablehnung eigens ausweisen. Seitdem kein Kommentar, weder von justemu noch von uns; letzte Nachricht ist der Issue-Text vom 2026-11-22 07:55.

Entwurf (vom Owner freigegeben 2026-11-22 08:28):

Thanks a lot for this report, and for tracing it all the way down to `readerOf()` and the secure view wrapper. That saved a lot of time.

You were right on every point: Findling picked the alphabetically first user who could see the file, the content fetch for that user was blocked by the secure view policy, no other reader was tried, and the admin page blamed the storage.

Fixed in 1.7.0:

- The owner of a file is now tried first when they can see it, then everyone else in alphabetical order.
- If the secure view policy refuses the fetch, Findling retries it as the file's owner before giving up.
- A refusal by a policy is shown as such on the admin page instead of "storage was not available".

Your two files should be indexed after the update. If they still show up under errors, please let me know.

Abgleich mit dem Fix: geprüft in 45-21 gegen das Endverhalten am Kopf, je Aussage des Entwurfs eine Abgleich-Zeile darunter; der Entwurfstext selbst bleibt byte-gleich zum Stand 89cc8ddf.
Abgleich Satz 'owner first, then everyone else in alphabetical order': passt. ReaderCandidates::forFile liest den Besitzer über den Home-Mount im selben Durchlauf (ReaderCandidates.php Z. 130-160), readingOrder stellt ihn an den Anfang und kappt bei 20 (Z. 193-200, MAX_READER_TRIES Z. 34); QueueService::readerOf nutzt genau diese Ordnung (QueueService.php Z. 1036); Tests QueueServiceReaderTest (Besitzer zuerst, 20 insgesamt) und ReaderCandidatesTest.
Abgleich Satz 'tries the next one': passt. Der freigegebene Satz lautet seit 89cc8ddf "If the secure view policy refuses the fetch, Findling retries it as the file's owner before giving up." (Freigabe Korrektur 59 45-21). Endverhalten in GatewayReader.php: nur eine belegte Secure-View-Ablehnung (Klasse, Meldung, erster Frame SecureViewWrapper::checkFileAccess, isSecureViewRefusal Z. 145-154) führt zum zweiten Öffnen (open Z. 128-137); mit erkennbarem Besitzer genau ein erneuter Versuch als Besitzer in actAs und danach policy ohne weiteren Kandidaten (openAgain Z. 184-192, E1/E2); jede andere ForbiddenException bricht sofort mit policy ab (Z. 131-134). Nur ohne erkennbaren Besitzer (Team Folder, externer Speicher) fragt Findling bis zu 20 Leser in Lesereihenfolge (Z. 194-203); für diesen Fall sagt der Satz nichts Falsches: es gibt dort keinen Besitzer, als der erneut gelesen werden könnte, und der Satz behauptet keine Ausschließlichkeit; die beiden Dateien aus #59 liegen im Home-Speicher mit Besitzer. Tests GatewayReaderTest (22 Fälle: Erkennung, Besitzer genau einmal, ohne Besitzer Kappung 20, andere Ausnahme bricht ab), live belegt in 45-20 (M1 bis M5, Schritt C).
Abgleich Satz 'shown as such on the admin page': passt. failed(policy_blocked) mit eigenem Label "Blocked by a rule" und eigener Abhilfe (AdminViewService.php Z. 592-593), statt "storage was not available"; Container wertet 403 mit Kopf X-Findling-Refusal: policy als policy_blocked, nie als Ausfall (45-18, I-45-17-01).
Abgleich Satz 'your two files should be indexed after the update': passt. Die Altbestände aus 1.6.x kommen nach dem Update erneut an die Reihe: Re-Check und Catch-up des Pollers plus die einmalige Erneuerung refusal_streaks_1_7_0, die erst bei Begleit-App Generation 4 läuft (U-45-20-01); live belegt in 45-20 Schritt B (M1 über den Abgleich: beide Dateien indexiert).
Abgleich Satz '1.7.0': passt, beide info.xml tragen 1.7.0 (45-08), der Fix liegt vollständig vor dem Prüfkopf von 45-21.
Abgleich Verlauf (45-15, 2026-11-27 00:20 UTC, `gh issue view 59`): passt. Seit dem Issue-Text vom 2026-11-22 07:55 kein Kommentar von justemu oder anderen; nichts Neues, das der Entwurf nicht trifft. Keine Abweichung, die bestehende Freigabe gilt. Der CHANGELOG 1.7.0 (#59) beschreibt dasselbe Endverhalten.

Empfehlung Schließen: nein, noch nicht. Der Entwurf bittet justemu um Meldung, falls die Dateien weiter unter Fehlern stehen; schließen nach seiner Bestätigung oder nach etwa zwei Wochen ohne Antwort.

## #25

Verlauf: mbozem meldet am 2026-10-09 eine doppelt gezählte Abdeckung bei Freigaben, die je Nutzer eingebunden sind; über 1.6.0 bis 1.6.4 wurde die Zählung je Dokument und die Faltung von Unterwurzeln und Schreibweisen ausgeliefert, unsere Nachfrage nach der Abdeckungszahl auf 1.6.4/1.6.5 kam am 2026-11-21 02:47. mbozem antwortet am 2026-11-22 14:55 mit zwei Bremsen des Abgleichs (Nachzählung meldet den Crawl als unfertig, ~160 Aussetzer am Tag; lange Warteschlange über der Ruhemarke 100) und einer vermuteten "JPG-Schleife"; er hat FINDLING_RECONCILE_QUIET_MAX auf 2000 gesetzt. Wir bestätigen beide Punkte am 2026-11-22 16:08 und fragen Logs zur JPG-Schleife ab, er liefert sie am 2026-11-24 14:25; wir fragen am 2026-11-24 15:46 zwei Queue-Abfragen nach und kündigen für 1.7.0 eine Rückfallsicherung an. Letzte Nachricht mbozem 2026-11-24 23:01: alle Zeilen `kind=ocr`, keine Überlappung zwischen den Proben, also echter OCR-Rückstand und keine Schleife; die alte Signatur `requeued=32, slots=1` ist seit dem 21.11. nicht mehr aufgetreten; er bietet an, die Abfragen nach 1.7.0 vorher/nachher zu wiederholen. Die Abdeckungszahl (etwa 18 %) hat er noch nicht bestätigt.

Entwurf:

1.7.0 is in the app store now (update both apps together), and it covers both things you found:

- A recount no longer keeps the comparison run waiting. It runs at most every six hours now, and saved rules still start it within 15 minutes, so the ~160 stand-downs a day are gone.
- A long queue, like your OCR backlog, holds the comparison run back at most twice its interval (two days by default), and never during a crawl. The admin page tells you when it has waited longer than its interval.

You can set FINDLING_RECONCILE_QUIET_MAX back to the default, but you don't have to.

On the JPG rows: your two samples showed a real OCR backlog draining, not a loop, so I don't need more logs. As a safety net, a file that keeps coming back with the same unchanged bytes is now listed as failed after three passes instead of being handed over again (see the changelog: https://github.com/street1983nk/nextcloud-search/blob/v1.7.0/CHANGELOG.md). If you run the two queries again after the update, I'd be glad to see the before and after, and where the coverage figure lands.

Release: https://github.com/street1983nk/nextcloud-search/releases/tag/v1.7.0

Abweichung vom Plan (F3): 45-AUDIT.md führt `Stand F3 (I-45-23-01): offen, wartet auf Logs des Melders`. Die Logs liegen seit 2026-11-24 vor (zwei Kommentare von mbozem), und sie zeigen keinen Schleifen-Auslöser, sondern echten OCR-Rückstand; die Rückfallsicherung steht im CHANGELOG 1.7.0 (#25). Eine erneute Bitte um Logs widerspräche dem Verlauf. Der Entwurf sagt deshalb: keine weiteren Logs nötig, ein Satz zur Rückfallsicherung mit Verweis auf den CHANGELOG. Frage an den Owner, siehe Bericht.

Empfehlung Schließen: nein. Der Owner hatte am 2026-11-11 zugesagt, offen zu lassen, bis mbozem die Abdeckungszahl auf dem Store-Build bestätigt; das steht aus, ebenso sein angebotener Vorher/Nachher-Abgleich nach 1.7.0.

## Gepostet

Gepostet am 2026-11-27 03:56 UTC, wortgleich zu den Entwürfen oben, ohne @-Erwähnung (Freigaben in 45-FREIGABEN.md, 45-15). Nichts geschlossen.
- PR #60: https://github.com/street1983nk/nextcloud-search/pull/60#issuecomment-7209387577
- #45: https://github.com/street1983nk/nextcloud-search/issues/45#issuecomment-7209387813
- PR #56: https://github.com/street1983nk/nextcloud-search/pull/56#issuecomment-7209388070
- PR #57: https://github.com/street1983nk/nextcloud-search/pull/57#issuecomment-7209388292
- #53: https://github.com/street1983nk/nextcloud-search/issues/53#issuecomment-7209388521
- #59: https://github.com/street1983nk/nextcloud-search/issues/59#issuecomment-7209388815
- #25: https://github.com/street1983nk/nextcloud-search/issues/25#issuecomment-7209389092
