# Zurückgestellte Punkte, Phase 05

Punkte, die während der Ausführung aufgetaucht sind und bewusst nicht im
laufenden Plan erledigt wurden. Jeder Eintrag nennt den Plan, den Grund und den
Ort, an den er gehört.

## Plan 05-04: Ein Nachläufer der Löschexpansion kann eine sofortige Wiederherstellung wieder löschen

**Was:** Die Löschung eines Ordners plant `SubtreeExpandJob` mit `kind=delete`,
und der Job arbeitet den Teilbaum in Bändern von 250 Einträgen ab, mit einem
Cursor im Jobargument und einem selbst geplanten Nachfolger. Holt ein Nutzer den
Ordner zurück, während diese Kette noch läuft, sieht der nächste Nachlaufer die
wiederhergestellten Dateien hinter seinem Cursor und reiht für sie
Löschaufträge ein. `KIND_RANK` macht `delete` zum absorbierenden Element, also
gewinnt die Löschung gegen die Inhaltsaufgabe, die die Wiederherstellung gerade
eingereiht hat. Die Dateien sind danach wieder aus dem Index heraus, und erst
der nächtliche Abgleich holt sie zurück.

**Wie eng das Fenster ist:** Die Kette endet, sobald ein Band leer
zurückkommt, und läuft im Abstand von fünf Sekunden. Der Fall braucht also einen
Ordner, der groß genug für mehrere Bänder ist, und eine Wiederherstellung
innerhalb dieser Sekunden. In der Nachstellung des Plans (drei Dateien, ein
Band) trat er nicht auf: der Nachläufer startete hinter der höchsten Datei-Id
und kam leer zurück, ohne etwas einzureihen.

**Warum nicht hier erledigt:** außerhalb des Plans, und die Behebung ist keine
Zeile. Sie braucht eine Entscheidung darüber, woran ein Teilbaum-Job erkennt,
dass sein Gegenstand nicht mehr gelöscht ist: ein Zeitstempel der Löschung im
Jobargument, gegen den der Job den Zustand des Ankers prüft, oder ein Abbruch,
sobald der Anker nicht mehr im Papierkorb liegt. Beides ist ein neues
Argumentfeld und damit eine Formatänderung an einem Job, der in dieser Phase
noch von anderen Plänen angefasst wird.

**Wohin es gehört:** in einen Folgeplan, der ohnehin an `SubtreeExpandJob`
arbeitet, oder in den Phase-Review. Bis dahin trägt der ETag-Abgleich den Fall,
was seiner Rolle als Sicherung entspricht.

## Plan 05-04: Ein Kommentar in `integration.yml` nennt nur die Scans

**Was:** Der Schritt "Wait until the queue is empty and every file has a
verdict" begründet seine Warteschleife mit "The scans reach the queue twice:
once as a content job, which ends as skipped(no_text_layer), and once more as an
ocr job". Seit diesem Plan gilt derselbe Satz für die vier Bildformate: sie
laufen ebenfalls zweimal durch die Warteschlange. Der Kommentar ist damit
unvollständig, die Schleife selbst bleibt richtig, weil sie auf eine leere
Warteschlange wartet und nicht auf eine feste Zahl von Durchgängen.

**Gemessen:** Ein Lauf über die sieben Bilder des Referenzkorpus braucht mit
dieser Änderung zwei Durchgänge statt einem (Durchgang 1: sieben Übergaben,
Durchgang 2: sechs indexiert, eines übersprungen). Die Endverdikte sind
unverändert, die Zahlen `EXPECTED_INDEXED`/`EXPECTED_SKIPPED`/`EXPECTED_FAILED`
des Gates also auch.

**Warum nicht hier erledigt:** `.github/workflows/integration.yml` steht nicht
in `files_modified` dieses Plans, und mehrere andere Pläne dieser Phase fassen
genau diese Datei an (NC-Versionsmatrix aus D-07 und D-23, Paritätstest aus
D-21). Eine reine Kommentaränderung aus einem parallel laufenden Worktree wäre
ein Konflikt in einer Datei, deren eigentliche Änderung anderswo liegt.

**Wohin es gehört:** in den Plan, der die Matrix in `integration.yml` umbaut.

## Plan 05-04: Der Live-Lauf des OCR-Anteils auf dem vollständigen Stack

**Was:** Das Abnahmekriterium von Task 1 nennt einen Lauf über die Bilddateien
des Referenzkorpus auf dem lokalen Stack, mit dem OCR-Anteil in den Zählern des
Containers und der Nennung auf der Statusseite.

**Was stattdessen gemessen wurde:** derselbe Lauf mit der echten Engine
(tesseract 5.5.0) im Laufzeitimage, gegen einen echten Tantivy-Index und eine
echte Zustandsdatenbank, mit dem Produktions-Extraktor hinter der
Prozessgrenze; Nextcloud war dabei ein Skript. Ergebnis in der Zusammenfassung
des Plans: vorher `text=6, ocr=0`, nachher `text=0, ocr=6`, alle sieben Zeilen
mit `ocr_used=1`. Nicht abgedeckt bleibt allein die Darstellung: dass die
Statusseite diesen Anteil auch anzeigt.

**Warum nicht hier erledigt:** die Statusseite braucht den registrierten
ExApp-Container am laufenden Nextcloud. Der lokale Stack dieses Repositories
bindet die PHP-App aus dem Haupt-Checkout ein, den ein Wave-Executor nicht
anfassen darf, und die HaRP-Stacks der Nachbar-Wellen gehören anderen Agenten.

**Wohin es gehört:** in den phasenweiten Integrationsschritt beziehungsweise in
den Messbericht der Phase (D-06), der den OCR-Anteil ohnehin auf echter Hardware
ausweisen muss.
