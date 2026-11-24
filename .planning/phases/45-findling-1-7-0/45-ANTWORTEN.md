# Antworten Phase 45

## #59

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
