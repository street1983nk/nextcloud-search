# Pitfalls Research

**Domain:** Nextcloud-ExApp für Suche (OCR + Volltext + Semantik, Zero-Config, kleine Selfhoster-Hardware)
**Researched:** 2026-08-15
**Confidence:** HIGH für die fulltextsearch-Fehlermodi, AppAPI-Mechanik und Wheel-/Multi-Arch-Fakten (Issue-Tracker, offizielle Doku, PyPI live geprüft); MEDIUM für Backup-Abdeckung in AIO und für die Wettbewerbseinschätzung

> Leitsatz dieser Recherche: Das offizielle fulltextsearch-Ökosystem ist nicht an fehlenden Features gescheitert, sondern an Betriebsrobustheit. Hängende Indexläufe, stille Ausfälle nach Updates, Datenverlust in der OCR-Zusatzapp und fehlende Kompatibilitäts-Releases haben es getötet. Genau diese Punkte sind die Produktversprechen dieses Projekts, also dürfen sie nicht als "Polish später" behandelt werden, sondern sind Kernfunktionalität.

## Critical Pitfalls

### Pitfall 1: Der hängende Indexlauf ohne Fortschrittsspeicher

**What goes wrong:**
Der Erstindexlauf läuft stundenlang, bleibt dann an einer Datei oder beim Wechsel auf den zweiten Nutzer stehen und wiederholt nur noch dieselbe Statuszeile. Der Speicher steigt bis zu einem Plateau, der Prozess macht keinen Fortschritt mehr, und ein Abbruch bedeutet: von vorne anfangen. Genau das ist bei fulltextsearch dokumentiert: Issue #311 (RAM wächst von 24 MB auf 566 MB, danach Endlosschleife mit identischer Zeile, ausgelöst beim Übergang auf den zweiten Nutzer, externe CIFS-Storage, offen seit 2018), Issue #404 ("becomes unresponsive at first file"), fulltextsearch_elasticsearch #346 (kein vollständiger Index möglich), plus mehrere Forumsthreads "Cannot complete initial FullTextSearch index".

**Why it happens:**
Der Indexlauf ist ein einzelner, langlaufender, monolithischer Prozess ohne Persistenz des Fortschritts. Der Zustand liegt im Prozessspeicher, nicht in einer Tabelle. Blockierende Aufrufe (Netzwerk-Storage, externer Suchserver, Extraktionswerkzeug) haben kein Timeout, deshalb wird aus einer hängenden Einzeloperation ein hängender Gesamtlauf. Entwickler testen mit 200 sauberen Dateien auf lokaler Platte, nicht mit 500 GB über CIFS.

**How to avoid:**
Der Index ist eine Queue-getriebene Zustandsmaschine, kein Skript. Konkret:
- Jede Datei bekommt eine Zeile in einer Arbeitstabelle mit Zustand (`pending`, `claimed`, `done`, `failed`, `skipped`), `attempts`, `last_error`, `claimed_at`. Fortschritt liegt in der Datenbank, nicht im RAM.
- Jeder Arbeitsschritt hat ein hartes Wanduhr-Timeout und läuft als Subprozess, den man töten kann. Ein Extraktionsprozess, der nicht kooperiert, wird per SIGKILL beendet, die Datei geht auf `failed` mit Grund.
- Stale-Claim-Reaper: alles, was länger als N Minuten `claimed` ist, fällt zurück auf `pending` (mit Zähler). Damit überlebt der Index einen Container-Neustart mitten im Lauf.
- Circuit Breaker pro Fehlerklasse: dreimal dieselbe Datei mit demselben Fehler bedeutet `failed` dauerhaft, nicht Endlosschleife.
- Der Prozess muss jederzeit per SIGTERM sauber abbrechbar sein und beim nächsten Start dort weitermachen, wo er war. Das ist ein Testfall, kein Vorsatz.

**Warning signs:**
Fortschrittszahl steht länger als das Timeout still; RSS steigt monoton über einen Lauf; nach einem Neustart fängt der Lauf bei 0 an; ein einzelner Datei-Typ (großes TIFF, verschlüsseltes PDF, Netzwerk-Mount) taucht immer als letzte Logzeile auf.

**Phase to address:**
Indexkern-Phase (Phase 2). Abnahmekriterium: `docker kill` mitten im Lauf, Neustart, Lauf setzt fort, keine Doppelarbeit außer der einen abgebrochenen Datei.

---

### Pitfall 2: Stiller Ausfall, den erst der Nutzer merkt

**What goes wrong:**
Die Indexierung läuft scheinbar, aber Inhalte fehlen. fulltextsearch-Belege: #597 (nach dem Update 19.0.6 auf 20.0.3 werden keine neuen Dokumente mehr indexiert, `fulltextsearch:test` meldet trotzdem überall "ok"), #857 (`fulltextsearch:reset` indexiert nur neue Dateien nach, alte bleiben unauffindbar, weil ein Zähler nicht mit zurückgesetzt wird), Forumsthread "Fulltextsearch:index runs, indexes files, no content". Der Admin erfährt es Monate später durch einen Nutzer, der ein Dokument nicht findet, das er sicher hochgeladen hat.

**Why it happens:**
Der Statusreport misst die falsche Größe: "Verbindung steht" statt "Anteil der Dateien mit frischem Inhaltsindex". Fehler werden geloggt, aber nicht aggregiert. Es gibt keine Invariante, die man prüfen könnte, und keinen Selbsttest, der eine echte Suchanfrage gegen einen bekannten Testinhalt stellt.

**How to avoid:**
- Die Statusseite zeigt Deckung, nicht Konnektivität: Anzahl indexierbarer Dateien laut Nextcloud-Dateitabelle gegen Anzahl `done`-Zeilen, plus `failed`-Liste mit Grund und Beispielpfaden, plus Alter des ältesten `pending`-Eintrags.
- Ein Deadman: wenn seit X Stunden `pending > 0` ist und die `done`-Zahl sich nicht bewegt, ist der Status "degraded" mit Klartextgrund. Nicht grün.
- Selbsttest-Endpunkt: ein Kanarienvogel-Dokument mit bekanntem Zufallsstring wird indexiert und zurückgesucht. Schlägt der fehl, ist die Suche kaputt, egal was die Verbindungsprüfung sagt.
- Schema- und Modellversion im Index verankern. Ändert sich Tokenizer, Chunking oder Embedding-Modell, wird die betroffene Menge automatisch als `pending` markiert. Ein "Reset", der nicht wirklich alles neu erfasst, ist die exakte Falle aus #857.
- `failed` ist ein Erstklasse-Zustand mit Ursachencode, den die Admin-Seite gruppiert anzeigt ("142 Dateien: passwortgeschütztes PDF", "3 Dateien: Timeout OCR").

**Warning signs:**
Statusseite ist grün, aber die Trefferzahl für ein bekanntes Wort ist 0; `failed`-Tabelle existiert nicht oder ist immer leer; Deckungsgrad wird nie berechnet; nach einem eigenen Release ändert sich das Suchverhalten ohne Reindex.

**Phase to address:**
Indexkern (Phase 2) für die Zähler, Admin-Sichtbarkeit (Phase 6) für die Darstellung. Das Deckungsmaß gehört in beide.

---

### Pitfall 3: Die OCR-Pipeline zerstört Nutzerdaten

**What goes wrong:**
Der schlimmste dokumentierte Fehler des Vorgängerökosystems: files_fulltextsearch_tesseract löscht PDFs, die bei der Ghostscript-Konvertierung (über spatie/pdf-to-image) fehlschlagen. Issue #30 ist seit dem 25.09.2020 offen, das Nextcloud-Forum führt dazu einen Warnthread ("APP w/PDF enabled may delete your pdfs!"), Betroffene mussten auf Snapshots zurück. Ursache im Kern: Die Pipeline schreibt in den Nutzerdatenbereich und räumt bei einem Fehlerpfad das Original mit weg.

**Why it happens:**
OCR-Werkzeugketten sind darauf ausgelegt, Dateien zu erzeugen und zu ersetzen (OCRmyPDF schreibt per Design ein neues PDF). Wer das naiv in einen Indexer einbaut, hat eine Schreiboperation im Datenpfad. Temporärdateien landen im selben Verzeichnis, Aufräumcode kennt den Unterschied zwischen Original und Zwischenprodukt nicht, und der Fehlerpfad ist der am wenigsten getestete Pfad.

**How to avoid:**
- Harte Architekturregel: Der Indexer öffnet Nutzerdateien ausschließlich lesend. Es gibt im gesamten Code keinen Schreib- oder Löschpfad in den Nextcloud-Speicher. Das ist per Test durchsetzbar (Grep-Gate gegen Schreib-APIs des Nextcloud-Clients, plus Integrationstest, der nach einem Lauf über ein Korpus mit kaputten PDFs Prüfsummen aller Quelldateien vergleicht).
- OCR arbeitet auf einer Kopie in einem Scratch-Verzeichnis im Container, das nach jedem Job vollständig geleert wird. Ergebnis ist Text, nicht ein neues PDF. Wir brauchen kein durchsuchbares PDF, wir brauchen Zeichen für den Index. Damit entfällt der komplette Rückschreibpfad und mit ihm die Ghostscript-Datenverlustklasse.
- Kaputte Eingaben sind normal, nicht außergewöhnlich: Ghostscript-Fehler, passwortgeschützte PDFs, Nullbyte-Dateien. Alle enden als `failed` mit Grund, nie als Exception, die den Aufräumcode auslöst.
- In README und Store-Beschreibung explizit: "Diese App verändert niemals Ihre Dateien." Das ist nach der Vorgeschichte ein echtes Verkaufsargument, das die Zielgruppe versteht.

**Warning signs:**
Irgendein Codepfad ruft eine Schreib-, Verschiebe- oder Löschmethode auf dem Nextcloud-Dateisystem auf; Temporärdateien werden neben dem Original abgelegt; OCR-Ergebnis ist eine Datei statt eines Strings; Testkorpus enthält keine absichtlich kaputten PDFs.

**Phase to address:**
OCR-Phase (Phase 3), Regel aber schon in der Foundations-Phase als Architekturinvariante festschreiben. Verifikation: Prüfsummenlauf über ein Korpus mit mindestens zehn bewusst defekten PDFs.

---

### Pitfall 4: OCR frisst CPU und RAM, bis der Server steht

**What goes wrong:**
Auf einer 4-GB-Box mit zwei Kernen läuft OCR eines mehrseitigen Scans, das Nextcloud-Webinterface wird unbenutzbar, oder der Container wird vom OOM-Killer beendet (Exit 137) und startet in einer Schleife neu. Bei OCRmyPDF ist das ein bekanntes Muster: ein 200-MB-PDF kann bei Parallelverarbeitung 10 GB ziehen, und die offizielle Empfehlung lautet, bei OOM mit `--jobs 1` zu wiederholen. Tesseract selbst hat dokumentierte Fälle hoher CPU- und RAM-Last bei großen Bildern. fulltextsearch #218 zeigt die andere Seite: große TIFFs werden gar nicht erst verarbeitet, ohne dass klar wird warum.

**Why it happens:**
Zero-Config verleitet dazu, alle Kerne zu nutzen und alles zu verarbeiten. Der Aufwand von OCR ist nicht proportional zur Dateigröße, sondern zur Pixelfläche mal Seitenzahl, und beides ist aus den Metadaten nicht sichtbar. Auf ARM-Boxen ist die Rechenleistung nochmal um ein Vielfaches geringer, während die Defaults vom Entwicklerlaptop stammen.

**How to avoid:**
- OCR läuft strikt seriell mit genau einem Worker und niedriger Priorität (`nice`, `ionice`). Parallelität ist eine Admin-Option, kein Default. Die Empfehlung "sqrt(N) Prozesse mit `--jobs sqrt(N)`" gilt für Batch-Server, nicht für eine Box, die gleichzeitig Nextcloud bedient.
- Vorprüfung vor jedem OCR-Job: Seitenzahl, Pixeldimensionen, Dateigröße. Über der Schwelle wird herunterskaliert (Äquivalent zu `--tesseract-downsample-large-images`) oder nach N Seiten abgeschnitten. Erste Seiten enthalten fast immer die suchrelevanten Begriffe.
- Hartes Zeit- und Speicherbudget pro Job als Subprozess-Limit (`RLIMIT_AS`, Wanduhr-Timeout). Überschreitung bedeutet `failed: ocr_timeout`, nicht Containertod.
- Selbstkalibrierung statt Konfiguration: beim ersten Start Kerne und verfügbaren Speicher messen und Budgets daraus ableiten. Das ist der ehrliche Zero-Config-Weg, nicht "wir nehmen einfach alles".
- Backpressure: OCR nur, wenn die Systemlast unter einer Schwelle liegt, und pausieren, wenn Nextcloud gerade beschäftigt ist. Ein Indexer, der den Server ausbremst, wird deinstalliert, egal wie gut er sucht.
- Explizit dokumentieren, dass eine Erstindexierung auf ARM Tage dauern kann, mit Restzeitschätzung in der Admin-UI. Erwartungsmanagement verhindert die Hälfte der Supportfälle.

**Warning signs:**
Containerneustarts ohne Absturzlog (das ist der OOM-Killer); Lastdurchschnitt dauerhaft über der Kernzahl; einzelne Dateien mit Verarbeitungszeit über mehreren Minuten; Speicherbedarf skaliert mit der Seitenzahl statt konstant zu bleiben.

**Phase to address:**
OCR-Phase (Phase 3) für Budgets, Härtungsphase (Phase 7) für die Kalibrierung und den ARM-Lasttest auf echter 4-GB-Hardware.

---

### Pitfall 5: Event-Lücken erzeugen Index-Drift, ohne dass es jemand merkt

**What goes wrong:**
Die inkrementelle Indexierung hängt an Datei-Events. Fehlt ein Event, fehlt die Datei dauerhaft im Index, weil nie wieder etwas passiert. fulltextsearch #769 zeigt den Fall in echt: Dateien, die über den Desktop-Client in einen synchronisierten Ordner kommen, lösen statt einer Indexierung eine Löschung aus, offen seit 2023. Genauso #715 und fulltextsearch_elasticsearch #15: gelöschte Dateien und Verzeichnisse bleiben im Index.

**Why it happens:**
Die Zustellung ist ausdrücklich unzuverlässig. Die AppAPI-Doku sagt für den Events Listener wörtlich, dass alle Informationen dem ExApp **asynchron** zugestellt werden, "more like a notification system in order to not slow down the server". Es sind nur wenige Ereignistypen abgedeckt (`node_event` mit created, touched, written, deleted, renamed, copied). Zu Retries, Reihenfolge oder Bestätigungen sagt die Doku nichts, also gibt es keine Zusicherung. Der klassische Webhook-Weg hängt zusätzlich an Hintergrundjobs, die per Default nur alle fünf Minuten laufen, wenn kein eigener Worker eingerichtet ist. Fehlt Cron, fehlen Events. Und Massenoperationen (Restore aus dem Papierkorb, Gruppenordner-Umbau, occ-Import, externer Speicher, der ohne Nextcloud-Schreibpfad befüllt wird) erzeugen überhaupt keine oder unvollständige Events.

**How to avoid:**
- Events sind ein Beschleuniger, niemals die Wahrheitsqülle. Die Wahrheitsqülle ist ein periodischer Abgleichlauf gegen die Nextcloud-Dateiliste: alles mit neuerer `mtime` oder unbekannter `fileid` wird eingereiht, alles im Index ohne Entsprechung fliegt raus.
- Der Abgleich muss billig sein, sonst wird er abgeschaltet. Deshalb inkrementell über ein Wasserzeichen (höchste gesehene `mtime` plus Sicherheitsfenster) und in Häppchen, mit einem vollständigen Tiefenabgleich in größerem Abstand.
- Identität über `fileid` plus Inhaltshash oder ETag, nicht über den Pfad. Umbenennen und Verschieben sind dann Metadaten-Updates, keine Neuindexierung, und ein verpasstes Rename-Event heilt beim nächsten Abgleich.
- Idempotenz: dasselbe Event zweimal darf nichts kaputt machen, ein unbekanntes `deleted` für eine nie indexierte Datei ist ein No-Op und kein Fehler (genau die Verwirrung aus #769).
- Löschungen und Entzug von Freigaben brauchen einen synchronen, schnellen Pfad. Ein Treffer auf ein gelöschtes Dokument ist ein Bug, ein Treffer auf ein entzogenes Dokument ist ein Sicherheitsvorfall (siehe Pitfall 6).
- Die Admin-UI zeigt "letzter erfolgreicher Abgleich vor X" und "seit dem Abgleich per Event verarbeitet: N". Driftet das auseinander, sieht man es.

**Warning signs:**
Neue Dateien tauchen im Test nur auf, wenn man sie über die Weboberfläche hochlädt, aber nicht per Desktop-Client oder WebDAV; gelöschte Dateien erscheinen weiter in Treffern; die Event-Rate fällt auf 0, ohne dass jemand etwas merkt.

**Phase to address:**
Indexkern (Phase 2) für das Abgleich-Design, Event-Integration (Phase 2 oder 3) für den schnellen Pfad. Verifikation: Testszenario, in dem alle Events blockiert werden, muss nach einem Abgleichzyklus denselben Indexzustand ergeben.

---

### Pitfall 6: Berechtigungsleck über Treffer, Snippets und Metadaten

**What goes wrong:**
Nutzer A findet Inhalt aus einem Dokument, das er nicht sehen darf. Das passiert in drei Abstufungen, alle drei sind real: die Datei erscheint in der Trefferliste (Existenz plus Dateiname plus Pfad verraten schon viel), das Snippet zeigt den relevanten Satz im Klartext (das ist echter Inhaltsabfluss, auch ohne Zugriff auf die Datei), oder der Treffer stammt aus einer längst entzogenen Freigabe. Nextcloud dokumentiert die verwandte Schwäche für Context Chat offen: Regeln der App files_accesscontrol werden nicht befolgt, wer per Files-App sieht, kommt per Context Chat ran. fulltextsearch_elasticsearch #15 und fulltextsearch #715 zeigen, dass gelöschte Objekte im Index bleiben, was dasselbe Muster für Entfreigaben nahelegt.

**Why it happens:**
Der Index ist global und deduplizierend (eine Datei, ein Eintrag), die Berechtigung dagegen ist pro Nutzer, pro Gruppe, pro Gruppenordner, pro Link, pro Zugriffsregel und ändert sich jederzeit. Wer Zugriffsrechte in den Index kopiert, hat einen Cache, der veraltet. Wer sie zur Suchzeit prüft, hat ein Performanceproblem und filtert oft erst nach dem Ranking, sodass die Trefferzahl schon leckt. Snippets werden aus dem Index erzeugt und dabei vergessen.

**How to avoid:**
- Autoritative Prüfung zur Suchzeit gegen Nextcloud, nicht gegen den Index. Der Index liefert Kandidaten (`fileid`-Liste), Nextcloud entscheidet Sichtbarkeit für genau diesen Nutzer. Der Index darf als schneller Vorfilter eine Zugriffsmenge führen, aber das Ergebnis muss der Server bestätigen.
- Snippet-Erzeugung ausschließlich nach bestandener Prüfung. Nie Text mitliefern, bevor der Zugriff bestätigt ist. Snippets dürfen niemals aus einem Vorschau-Cache stammen, der die Prüfung umgeht.
- Auch Zähler und Facetten sind Daten. "142 Treffer" bei 3 sichtbaren verrät die Existenz der anderen 139. Nach dem Filtern zählen, notfalls "mehr als 20 Treffer" anzeigen.
- Overfetch-Strategie: mehr Kandidaten holen als angezeigt werden, filtern, dann auffüllen, damit die Ergebnisliste nach dem Filtern nicht löchrig wird. Cursor-basierte Paginierung statt Offset, wie es die Nextcloud-Suchdoku empfiehlt, weil sich die Datenlage zwischen Seiten ändert.
- Kein Abkürzen über ExApp-Systemrechte. Das ist dieselbe Falle wie im Schwesterprojekt (dort Pitfall 6): eine einzige Client-Fabrik, die zwingend eine Nutzeridentität verlangt, kein Systempfad, der Tool-Code erreichbar ist.
- Entfreigabe- und Löschereignisse mit hoher Priorität, plus Ablauffrist auf zwischengespeicherten Zugriffsmengen (kurze TTL), damit ein verpasstes Event maximal Minuten wirkt, nicht Monate.
- Automatisierter Paritätstest als Dauergate: derselbe Suchbegriff als Nutzer B über die normale Nextcloud-Suche und über unsere App muss dieselbe Dokumentmenge liefern. Der Test enthält mindestens: entzogene Freigabe, Gruppenordner mit Teilrechten, Link-Share, files_accesscontrol-Regel, gelöschte Datei im Papierkorb, Datei in externem Speicher.
- files_accesscontrol bewusst behandeln und die Entscheidung dokumentieren. Nextcloud räumt für Context Chat öffentlich ein, dass diese Regeln nicht greifen. Wenn wir sie respektieren, ist das ein Differenzierungsmerkmal; wenn wir es nicht können, muss es in der Store-Beschreibung stehen, bevor es jemand als Sicherheitslücke meldet.

**Warning signs:**
Der Suchpfad enthält Zugriffslogik, die nicht Nextcloud fragt; Snippets werden vor dem Filtern gerendert; Trefferzahlen stammen aus der Engine; keine Testnutzer mit eingeschränkten Rechten in der Testsuite; Antwortzeit sinkt verdächtig, nachdem man "Rechte cachen" eingebaut hat.

**Phase to address:**
Unified-Search-Integration (Phase 5) für die Prüfkette, Foundations (Phase 1) für die Client-Fabrik, Härtung (Phase 7) für die Paritätstestsuite. Dieser Punkt ist das einzige K.-o.-Kriterium des Projekts: alles andere kann man nachbessern, ein Inhaltsabfluss beendet die App im Store.

---

### Pitfall 7: Zero-Config-Defaults, die kleine Server schmelzen

**What goes wrong:**
"Startet von selbst und indexiert alles" bedeutet auf einer realen Instanz: 800 GB Videos, VM-Images, Backup-Archive, node_modules-Ordner aus Sync-Verzeichnissen, ein 4-GB-Archiv, das entpackt werden will, und ein 100.000-Seiten-Scan. Die Platte läuft voll, die CPU ist tagelang belegt, und der Admin deinstalliert. Kontext: Context Chat setzt eine harte Grenze bei 100 MB pro Datei und ignoriert verschlüsselte oder passwortgeschützte Dateien stillschweigend. Die Grenze ist richtig, das stille Ignorieren ist die Falle.

**Why it happens:**
Zero-Config wird als "keine Grenzen" missverstanden statt als "gute Grenzen ohne Nachfragen". Außerdem ist die Versuchung groß, Vollständigkeit als Qualitätsmerkmal zu verkaufen.

**How to avoid:**
- Allowlist statt Blocklist für Dateitypen. Wir indexieren, was wir zuverlässig extrahieren können (PDF, Office-Formate, Text, Markdown, später Mail-Anhänge), alles andere ist `skipped: unsupported_type` und damit sichtbar, nicht unsichtbar. Eine Blocklist ist immer unvollständig, weil neue Endungen schneller entstehen, als man pflegt.
- Typ über Inhaltserkennung, nicht über die Endung. Eine `.pdf`, die in Wahrheit ein 2-GB-Video ist, existiert in freier Wildbahn.
- Harte Defaults, alle überschreibbar, alle in der Admin-UI sichtbar: maximale Dateigröße (Vorschlag 50 MB für Textextraktion, 20 MB für OCR), maximale Seitenzahl für OCR, maximale extrahierte Textlänge pro Dokument (Kappung mit Vermerk), Gesamtbudget für die Indexgröße in Prozent des freien Platzes.
- Archive werden in v1 nicht ausgepackt. Rekursives Auspacken ist eine Zip-Bomben-Angriffsfläche und ein Ressourcenloch.
- Nichts wird stillschweigend übersprungen. Jedes `skipped` hat einen Grund, ist zählbar und in der Admin-UI gruppiert sichtbar, inklusive Hinweis, welche Grenze man anheben müsste. Das ist der Unterschied zwischen "die App kann das nicht" und "die App hat es absichtlich gelassen und sagt es".
- Vorschau vor dem Start: nach der Installation zuerst eine Zählung ("12.412 Dateien passen ins Profil, geschätzt 6 Stunden, geschätzt 900 MB Index"), dann automatischer Start. Kein Konfigurationszwang, aber Transparenz vor dem Ressourcenverbrauch.
- Reihenfolge nach Nutzen: kleine, kürzlich geänderte Textdokumente zuerst, große Scans zuletzt. Dann ist die Suche nach 20 Minuten schon nützlich, statt nach 30 Stunden komplett.

**Warning signs:**
Kein Größenlimit im Code; Extraktion läuft über die Endung; `skipped` existiert nicht als Zustand; die Indexgröße wird nicht gemessen; die erste Nutzererfahrung ist eine leere Trefferliste, weil noch nichts fertig ist.

**Phase to address:**
Indexkern (Phase 2) für Allowlist und Limits, Admin-Sichtbarkeit (Phase 6) für die Sichtbarmachung der Grenzen.

---

### Pitfall 8: Der Index ist Zustand, der nicht rekonstruierbar ist

**What goes wrong:**
Die Platte läuft voll, während die Suchindexdatei geschrieben wird. Oder der Admin macht `occ app_api:app:unregister --rm-data`. Oder AIO stellt aus dem Borg-Backup wieder her, und die Nextcloud-Datenbank ist von gestern, während das ExApp-Volume von heute ist oder gar nicht im Backup war. Ergebnis: Index und Realität passen nicht zusammen, im schlimmsten Fall ist die Indexdatei beschädigt und die App startet nicht mehr.

**Why it happens:**
AppAPI legt pro ExApp ein Docker-Volume `nc_app_<app_id>_data` an, erreichbar über `APP_PERSISTENT_STORAGE`. Beim Unregister wird es per Default absichtlich nicht gelöscht, das ist gut. Aber: Es liegt physisch im Docker-Storage (typisch `/var/lib/docker`), also oft auf der System-Partition und nicht dort, wo der Admin seinen Platz vermutet. Und die AIO-Sicherung deckt zusätzliche Volumes nur ab, wenn sie ausdrücklich eingetragen wurden. Das heißt, ein Restore trennt Index und Datenbank fast garantiert zeitlich (MEDIUM confidence, sollte in der Testphase am echten AIO verifiziert werden).

**How to avoid:**
- Grundhaltung: Der Index ist ein Cache, kein Datenspeicher. Er muss jederzeit aus Nextcloud vollständig neu erzeugbar sein, und dieser Weg wird regelmäßig getestet, nicht nur dokumentiert. Damit ist jedes Backup-Szenario unkritisch.
- Instanzbindung: Nextcloud-Instanz-ID und ein Index-Epoch im Index speichern. Passt die Instanz-ID nicht oder ist die Nextcloud-Datenbank offensichtlich älter als der Index (kleinste Datei-ID rückwärts, Zählersprünge), wird ein voller Abgleich erzwungen statt weiterzuarbeiten. Das fängt den Restore-Fall automatisch.
- Speicherplatz-Wache: vor jedem Schreibblock freien Platz prüfen. Unter der Schwelle geht der Indexer in den Zustand `paused: low_disk` und schreibt nichts mehr, statt eine halbe Transaktion zu hinterlassen. Suche bleibt lesend verfügbar.
- Nur transaktionale Schreibwege verwenden (bei SQLite WAL plus korrektes Synchronisationsniveau, bei Tantivy sauberer Commit statt Halbzustand). Beim Start Integritätsprüfung; bei Beschädigung nicht raten, sondern den Index verwerfen, neu anlegen und den Wiederaufbau starten, sichtbar in der Admin-UI.
- Index-Speicherort und Größe in der Admin-UI anzeigen, inklusive Hinweis auf das Docker-Volume und wie man es sichert oder verschiebt. Das erspart genau den Supportfall "meine Systempartition ist voll".
- Zwei getrennte Admin-Aktionen anbieten: "Index neu aufbauen" (leert und startet neu) und "Abgleich erzwingen" (behält vorhandene Einträge). Die fulltextsearch-Falle aus #857 war ein Reset, der nur halb zurückgesetzt hat. Beide Aktionen müssen genau das tun, was sie versprechen, und den Deckungsgrad danach beweisen.

**Warning signs:**
Kein Integritätscheck beim Start; kein Schreib-Stopp bei wenig Platz; Instanz-ID wird nicht gespeichert; der Neuaufbauweg wurde nie getestet, weil "geht ja nicht kaputt".

**Phase to address:**
Indexkern (Phase 2) für Transaktionen und Instanzbindung, Härtung (Phase 7) für Disk-Full- und Restore-Szenarien.

---

### Pitfall 9: Die App ist auf dem Zielsystem gar nicht installierbar

**What goes wrong:**
Der Nutzer klickt im App Store auf Installieren und bekommt einen Fehler, weil kein Deploy-Daemon eingerichtet ist. ExApps brauchen einen Deploy-Daemon, der Container erzeugt. Auf Managed Hosting ohne Docker gibt es den nicht, und der Ausweg `manual_install` ist ein Entwickler- und Sonderfall, kein Klickpfad. Dazu kommen die Topologie-Klassiker: das Dreieck aus Nextcloud, Daemon und Container muss sich gegenseitig erreichen; AIO hat eigene Netzwerkeigenheiten; der alte Docker Socket Proxy ist abgekündigt und soll mit Nextcloud 35 verschwinden, HaRP ist der neue Weg; und AppAPI ist an Docker-API-Versionen gebunden, was in app_api #712 (November 2025) zu einem harten Ausfall führte: Docker 29 verlangt mindestens API 1.44, AppAPI sprach 1.41, damit ging Deployment weder mit DSP noch mit HaRP.

**Why it happens:**
Die Zielgruppe ist heterogen (AIO, docker-compose, Snap, Managed Hosting, Synology, Raspberry Pi), und der Entwickler testet auf genau einer Topologie. Außerdem liegt der Fehler oft nicht bei uns, sondern in der Schicht darunter, was ihn nicht weniger tödlich für die Bewertung macht.

**How to avoid:**
- Von Tag eins gegen HaRP entwickeln, nicht gegen den abgekündigten Docker Socket Proxy, und die AppAPI-Testbereitstellung dauerhaft grün halten. Das ist dieselbe Lehre wie im Schwesterprojekt (dort Pitfall 4).
- Mindestens zwei Topologien im Test: schlichtes docker-compose und Nextcloud AIO. AIO ist die häufigste Selfhoster-Installation und hat die meisten Eigenheiten.
- Voraussetzungen prominent und ehrlich in der Store-Beschreibung: "benötigt AppAPI und einen Deploy-Daemon (Docker), funktioniert nicht auf Shared Hosting ohne Container". Eine schlechte Bewertung wegen falscher Erwartung kostet mehr als der verlorene Nutzer.
- Docker-API- und AppAPI-Versionsabhängigkeiten als bekanntes Risiko führen und in den Release-Notes eine Kompatibilitätsmatrix pflegen (Nextcloud-Version, AppAPI-Version, getestete Docker-Version). Wenn der nächste Docker-Sprung AppAPI bricht, sind wir vorbereitet und können sofort antworten.
- Eine Diagnoseseite, die die drei Richtungen des Dreiecks aktiv testet und im Klartext sagt, welche Verbindung fehlt. Das verwandelt Supportfälle in Selbsthilfe.

**Warning signs:**
Nur eine Testumgebung; Handshake- oder Heartbeat-Code entsteht spät; keine Aussage zur Docker-Mindestversion; Bugreports der Form "geht bei mir nicht" ohne dass man Topologie unterscheiden kann.

**Phase to address:**
Foundations (Phase 1). Abnahmekriterium: grüne Testbereitstellung auf docker-compose und AIO, bevor Suchlogik entsteht.

---

### Pitfall 10: Der Vektorindex wächst schneller als die Box

**What goes wrong:**
Semantische Suche verlangt Chunking, und Chunking vervielfacht die Objektzahl. 50.000 Dokumente ergeben schnell 500.000 bis 2.000.000 Chunks. Bei 384 Dimensionen in float32 sind das rund 1,5 KB pro Chunk, also mehrere Gigabyte allein an Vektoren, plus den Chunk-Text für Snippets. Und die Suche wird linear langsamer: sqlite-vec macht per Design eine Brute-Force-Suche über alle Vektoren, ein ANN-Index ist erklärtes Ziel, aber noch nicht da (Tracking-Issue #25). Auf einer ARM-Box mit zwei Kernen ist eine Brute-Force-Suche über Millionen Vektoren pro Tastendruck nicht tragbar.

**Why it happens:**
Der Prototyp läuft mit 500 Dokumenten und antwortet in 20 Millisekunden. Die Linearität fällt erst beim echten Datenbestand auf, und dann ist die Architektur festgelegt.

**How to avoid:**
- Vektoren quantisieren. int8 statt float32 senkt den Speicherbedarf um den Faktor 4 bei geringem Qualitätsverlust; binäre Quantisierung als grober Vorfilter mit anschließender Nachbewertung senkt ihn drastisch. Das ist der einzige Weg, Millionen Chunks auf 4 GB RAM ehrlich zu bedienen.
- Keine reine Vektorsuche als Einstieg. Hybrid heißt hier zuerst Volltext (billig, exakt, skaliert), dann Vektorsuche auf einer vorgefilterten Kandidatenmenge statt auf dem Gesamtbestand. Damit ist die Brute-Force-Grenze kein Problem mehr, weil man nie über alles scannt.
- Chunking konservativ: nicht jedes Dokument braucht 200 Chunks. Deckelung pro Dokument, Deduplizierung identischer Chunks (Kopfzeilen, Signaturen, Boilerplate), Mindestlänge für einen Chunk.
- Modellgröße ist eine Produktentscheidung, keine Detailfrage. Ein kleines, quantisiertes Modell mit 384 Dimensionen ist auf dieser Hardware richtig; jede Verdopplung der Dimension verdoppelt Speicher und Suchzeit.
- Messgröße von Anfang an mitführen: Bytes pro indexiertem Dokument. Das ist die Zahl, die dem Admin sagt, was ihn erwartet, und die uns sagt, wann wir zu gierig sind.
- Ein Fallback-Schalter: semantische Suche deaktivierbar, Volltext bleibt. Wenn die Box zu klein ist, degradiert das Produkt, statt zu sterben.

**Warning signs:**
Antwortzeit steigt linear mit dem Bestand; Speicherbedarf des Suchprozesses wächst mit der Indexgröße statt konstant zu bleiben; keine Kennzahl "Bytes pro Dokument"; Tests nur mit Spielzeugkorpora.

**Phase to address:**
Semantik-Phase (Phase 4), mit einem Skalierungstest auf mindestens 50.000 Dokumenten vor der Freigabe.

---

### Pitfall 11: Die Multi-Arch-Falle beim Image-Bau

**What goes wrong:**
Das Image wird auf Alpine gebaut, weil es klein ist, und dann gibt es für die zentralen Abhängigkeiten keine passenden Wheels. Live gegen PyPI geprüft am 15.08.2026: `tantivy` 0.26.0, `onnxruntime` 1.28.0 und `sqlite-vec` 0.1.9 liefern manylinux-Wheels für aarch64 und cp313, aber **keine** musl-Wheels. Auf Alpine bedeutet das: Rust- und C++-Toolchain im Image, Buildzeiten im Stundenbereich, und bei onnxruntime ein Bauvorhaben, das man auf einem Emulator nicht gewinnen will. Zweite Falle: QEMU-Emulation für arm64 im CI macht aus einem 5-Minuten-Build einen 90-Minuten-Build und produziert schwer diagnostizierbare Fehlschläge.

**Why it happens:**
Alpine gilt reflexhaft als "das schlanke Basisimage", und die Wheel-Frage stellt man erst, wenn der Build bricht. Die ARM-Frage stellt sich erst beim ersten Nutzer mit Raspberry Pi oder Ampere-VPS, also nach dem Release.

**How to avoid:**
- Basisimage auf glibc (Debian slim), nicht musl. Das ist die eine Entscheidung, die den ganzen Themenkomplex auflöst.
- Multi-Arch von Anfang an bauen, nicht nachträglich. Native ARM-Runner nutzen, wenn verfügbar; sonst Emulation nur für den finalen Build und mit realistischem Zeitbudget einplanen.
- Alle Abhängigkeiten exakt pinnen und vor jedem Upgrade prüfen, ob es für beide Architekturen und die Zielversion von Python noch Wheels gibt. tantivy-py #371 (kein Wheel für Python 3.13.0 bei Version 0.22) zeigt, dass diese Lücke real auftritt und Projekte blockiert.
- Modellgewichte für die Embeddings ins Image backen, nicht beim ersten Start herunterladen. Ein Download beim Start bricht in Umgebungen ohne ausgehende Verbindung, kostet beim ersten Suchversuch Minuten und macht die Installation von einem fremden Dienst abhängig. Das kostet Imagegröße, aber es ist der Unterschied zwischen "funktioniert nach der Installation" und "funktioniert manchmal".
- Imagegröße trotzdem im Blick behalten: OCR-Sprachdaten sind groß, deshalb nur eine sinnvolle Grundmenge mitliefern und weitere Sprachen als Option.
- Tesseract- und Ghostscript-Versionen pinnen. Ein stiller Basis-Image-Sprung ändert sonst die OCR-Qualität zwischen zwei Releases, ohne dass sich unser Code geändert hat.

**Warning signs:**
Der Dockerfile enthält einen Compiler; CI-Build dauert länger als 30 Minuten; das Image wurde nie auf echter ARM-Hardware gestartet; beim ersten Start geht Netzwerkverkehr nach draußen.

**Phase to address:**
Foundations (Phase 1) für die Basisimage-Entscheidung, Härtung (Phase 7) für den Test auf echter ARM-Hardware.

---

### Pitfall 12: Die Kompatibilitäts-Todesspirale

**What goes wrong:**
Genau das, was fulltextsearch umgebracht hat, und es kann uns identisch treffen. Nextcloud veröffentlicht ein neues Major-Release, die App deklariert es in `info.xml` nicht, verschwindet damit aus dem Store, wird beim Upgrade deaktiviert, und die Nutzer stehen ohne Suche da. Belege aus dem Tracker: #950 ("No update Version available for Nextcloud 34", Juni 2026), #955 ("Will there be a version for Nextcloud 34 and maybe next 35?", Juli 2026), #956 (die App lässt NC 34 hängen, Abhilfe war Deaktivieren), dazu Forumsthreads mit dem Tenor, dass die Volltextsuch-Apps für NC 34/35 nicht kompatibel sind. Jede unbeantwortete Kompatibilitätsfrage kostet Vertraün, und Vertraün ist bei einem Ein-Personen-Projekt das einzige Kapital.

**Why it happens:**
Kompatibilitätspflege ist unsichtbare Arbeit ohne Erfolgserlebnis, sie fällt genau dann an, wenn man an Features arbeiten will, und der Zeitpunkt wird von außen bestimmt. Bei einem Solo-Entwickler kollidiert sie mit jedem anderen Vorhaben.

**How to avoid:**
- Die Architektur so wählen, dass Kompatibilität billig ist. Der Großteil der Logik liegt im Container und ist von der Nextcloud-Version entkoppelt; die PHP-Companion-App bleibt bewusst winzig und benutzt nur öffentliche, stabile Schnittstellen (Suchanbieter-Registrierung plus Weiterleitung). Je kleiner die PHP-Fläche, desto billiger jeder Major-Sprung.
- CI-Lauf gegen die Nextcloud-Entwicklungslinie, nicht nur gegen die aktuelle stabile Version. Bricht etwas, weiß man es Wochen vor dem Release und nicht durch ein Issue.
- Kompatibilitäts-Release als feste, terminierte Aufgabe im Kalender, ausgerichtet am Nextcloud-Releaseplan, nicht als Reaktion auf Issues.
- Öffentliche, ehrliche Kommunikation im README: welche Nextcloud-Versionen getestet sind und wann die nächste geplant ist. Die Vorgeschichte des Ökosystems macht diese Zielgruppe misstrauisch; ein sichtbarer Wartungsrhythmus ist ein Feature.
- Vorsicht bei der Versionsdeklaration: nur bis zur nächsten Version voraus deklarieren, sonst greift man sich Ausfälle wie #956 ein, wo die App auf einer neuen Version zwar lädt, aber die Instanz lahmlegt.

**Warning signs:**
Erstes Issue "Version für NC X?" kommt vor dem eigenen Release; CI kennt nur eine Nextcloud-Version; die PHP-App wächst und benutzt interne Klassen.

**Phase to address:**
Foundations (Phase 1) für die Schnittstellen-Disziplin, Store-Phase (Phase 8) für den Wartungsrhythmus.

---

### Pitfall 13: Store- und Zertifikatspipeline (kurz, siehe Schwesterprojekt)

**What goes wrong:**
Späte Umbenennung entwertet das Zertifikat, weil es an die App-ID gebunden ist; die CSR hängt in der Warteschlange; das Docker-Image ist zum Zeitpunkt der Store-Freigabe noch nicht unter dem in `info.xml` deklarierten Tag abrufbar; `info.xml` fällt durch die Schema-Prüfung.

**Why it happens:**
Die Regeln stehen in Dokumenten, die man zuletzt liest, wenn App-ID, Tabellennamen und Containernamen schon feststehen.

**How to avoid:**
Vollständig recherchiert und dokumentiert im Schwesterprojekt: `C:\Users\Student\nextcloud-mcp-connector\.planning\research\PITFALLS.md`, dort Pitfall 5 und Pitfall 8. Kernpunkte hier nur als Merkposten: App-ID und Anzeigename vor dem ersten Bau-Commit einfrieren (kein "Nextcloud" im Namen), CSR früh einreichen (gemessene Laufzeit im Juli und August 2026: etwa 1 bis 5 Tage, plus Puffer für Rückfragen), Signierschlüssel wie ein Produktionsgeheimnis behandeln, Multi-Arch-Image vor dem Store-Release veröffentlichen, `info.xml` lokal gegen das Schema prüfen, Deinstallation muss restlos aufräumen (hier zusätzlich: das Index-Volume, und die Frage beantworten, ob es beim Entfernen mitgeht oder bewusst bleibt).
Projektspezifische Ergänzung: Diese App verarbeitet Dateiinhalte. Der Store-Text muss von Anfang an klarstellen, dass nichts den Server verlässt, dass keine Datei verändert wird und dass keine Telemetrie stattfindet. Das ist gleichzeitig Compliance und Marketing.

**Phase to address:**
Foundations (Phase 1) für Naming und ID, Store-Phase (Phase 8) für Einreichung.

---

### Pitfall 14: Wettbewerbsrisiko, ohne Alleinstellung zu bauen

**What goes wrong:**
Nextcloud baut Suche und KI-Kontext selbst aus (Context Chat, Context Agent, Assistant-Anbindung an die Unified Search in Hub 26). Wenn unser Produkt sich als "Context Chat, aber kleiner" positioniert, sind wir in dem Moment überflüssig, in dem Nextcloud eine Standardlösung mitliefert. Zusätzlich reales Risiko in die andere Richtung: fulltextsearch könnte einen Wartungsschub bekommen und die "verwaist"-Erzählung entwerten.

**Why it happens:**
Die Versuchung, in Richtung des sichtbaren Trends zu bauen (Chat, RAG, Antworten), ist groß, obwohl genau dort der Wettbewerber sitzt und mehr Ressourcen hat.

**How to avoid:**
- Die Positionierung liegt in den Lücken, die dokumentiert und dauerhaft sind: Context Chat braucht laut offizieller Doku bei reinem CPU-Betrieb mindestens 12 GB RAM, verlangt AVX und AVX2 (womit typische ARM-Boxen ausfallen), kann kein OCR, ignoriert Dateien über 100 MB und passwortgeschützte Dateien stillschweigend, befolgt files_accesscontrol nicht und liefert Antworten statt Treffer. Unser Anspruch ist das Gegenteil: läuft auf 4 GB, läuft auf ARM, kann OCR, respektiert Rechte, liefert Treffer mit Belegstelle.
- Out of Scope ernst nehmen: kein RAG, keine Chat-Antworten. Jede Woche, die in Antwortgenerierung fließt, wird gegen einen Gegner investiert, der dort stärker ist, und nicht in OCR-Robustheit, wo niemand konkurriert.
- Beweisbare Zahlen als Marketing: "Erstindex von 10.000 Dokumenten auf einem Raspberry Pi 5 mit 4 GB in X Stunden, Index Y MB, Suchantwort unter Z Millisekunden". Das kann der Wettbewerber nicht kopieren, ohne seine Architektur zu ändern.
- Kompatibilität als Strategie: Wenn Nextcloud später eine eigene Suchlösung liefert, ist die Weiterexistenz an sauberen, öffentlichen Schnittstellen und an OCR gebunden, nicht an ein Alleinstellungsmerkmal, das per Server-Release verschwinden kann.

**Warning signs:**
Feature-Diskussionen driften Richtung "Antwort auf eine Frage"; die Positionierung im README nennt keine harten Ressourcenzahlen; kein Benchmark auf Zielhardware.

**Phase to address:**
Durchgehend, konkret aber in der Store- und Launch-Phase (Phase 8) beim Verfassen der Positionierung, und in der Härtungsphase (Phase 7) beim Erzeugen der Benchmark-Zahlen.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Fortschritt nur im Prozessspeicher statt in der Datenbank | Indexer ist in einem Tag geschrieben | Genau der Fehlermodus aus fulltextsearch #311; jeder Neustart kostet Stunden; nicht nachrüstbar ohne Umbau | Nie. Das ist das Kernversprechen des Produkts |
| Zugriffsrechte in den Index kopieren statt zur Suchzeit prüfen | Suche wird sehr schnell | Veralteter Rechte-Cache bedeutet Inhaltsabfluss nach Entfreigabe | Nur als Vorfilter mit kurzer Gültigkeit und autoritativer Nachprüfung |
| OCR-Ergebnis als neues PDF zurückschreiben | Nutzer bekommen durchsuchbare PDFs geschenkt | Datenverlustrisiko wie files_fulltextsearch_tesseract #30; Vertraünsverlust ist irreversibel | Nie in v1. Falls je, dann als opt-in in ein separates Zielverzeichnis, niemals ersetzend |
| Nur amd64 ausliefern, ARM später | Halbe CI-Zeit, schnellerer erster Release | Zielgruppe (Raspberry Pi, ARM-VPS) fällt weg, negative Bewertungen, nachträgliche Umstellung des Basisimages | Nur für interne Vorabversionen, nie für ein Store-Release |
| Embedding-Modell beim ersten Start herunterladen | Kleineres Image | Erststart bricht offline; Abhängigkeit von einem fremden Dienst; widerspricht dem Privacy-Versprechen | Nur für optionale Zusatzmodelle, nie für das Standardmodell |
| Semantik erst ausliefern, Volltext nachziehen | Klingt nach dem interessanteren Feature | Ohne exakte Suche nach Dateinamen und Zeichenketten wirkt das Produkt kaputt; Nutzer suchen Rechnungsnummern, keine Bedeutungen | Nie. Volltext ist die Basis, Semantik die Zugabe |
| Einen Suchserver als Sidecar mitliefern, weil es schneller integriert ist | Weniger eigener Code | Zweiter Prozess, zweites Speicherbudget, zweite Fehlerquelle, genau die Setup-Qual, die das Produkt beseitigen soll | Nur als optionales Backend für große Instanzen, nach v1 |
| Fehler nur ins Log schreiben statt in eine Fehlertabelle | Spart die Tabelle und die UI | Stiller Ausfall wie fulltextsearch #597; Admin merkt nichts; Support ohne Datenbasis | Nur während der ersten Prototypen-Iteration |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| AppAPI Events Listener | Events als zuverlässigen Datenstrom behandeln | Doku sagt explizit asynchron und nur wenige Ereignistypen, keine Retry-Zusage. Events beschleunigen, der periodische Abgleich garantiert |
| webhook_listeners | Annehmen, Webhooks kommen sofort | Zustellung hängt an Hintergrundjobs, ohne eigenen Worker per Default im Minutenraster. Latenz einplanen und in der UI ausweisen |
| Unified Search (IProvider) | Ergebnisse ungefiltert samt Snippet zurückgeben | Jeder Anbieter wird per eigenem HTTP-Request aufgerufen; Rechte pro Nutzer im `search()` durchsetzen, Snippet erst nach der Prüfung erzeugen, Cursor- statt Offset-Paginierung |
| AppAPI Deploy-Daemon | Gegen Docker Socket Proxy entwickeln | DSP ist abgekündigt und soll mit NC 35 entfallen; HaRP ist der neue Standard, ExApp-Erreichbarkeit läuft über FRP-Tunnel |
| Docker Engine API | Version als gegeben ansehen | app_api #712: Docker 29 verlangt API 1.44, AppAPI sprach 1.41, Deployment war komplett tot. Kompatibilitätsmatrix pflegen |
| APP_PERSISTENT_STORAGE | Annehmen, das Volume sei gesichert und liege bei den Nutzerdaten | Volume `nc_app_<app_id>_data` liegt im Docker-Storage, bleibt beim Unregister per Default erhalten, ist in AIO-Sicherungen aber nur enthalten, wenn ausdrücklich eingetragen. Index muss rekonstruierbar sein |
| Nextcloud-Dateizugriff aus dem Container | Direkt auf das Dateisystem des Hosts zugreifen | Nur über die Nextcloud-Schnittstellen im Nutzerkontext; externer Speicher, Verschlüsselung und Gruppenordner funktionieren sonst nicht |
| Ghostscript und Tesseract | Als stabile Blackbox behandeln | Versionen pinnen, Ausgabe validieren, Fehlerausgänge als Normalfall behandeln, niemals Rückschreibpfad |
| Nextcloud-Verschlüsselung (server-side encryption) | Ignorieren | Bei aktivierter Verschlüsselung kommt man nur über die Nextcloud-Schicht im Nutzerkontext an Klartext. Früh testen, sonst indexiert man Chiffrat |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Brute-Force-Vektorsuche über den Gesamtbestand | Suchzeit steigt linear mit dem Bestand | Hybrid mit Volltext-Vorfilter, Quantisierung, Kandidatenmenge deckeln | Sprbar ab ca. 100.000 Chunks auf schwacher CPU, unbenutzbar im Millionenbereich |
| Ein Commit pro indexierter Datei | Platten-I/O dominiert, Durchsatz bricht ein | Stapelverarbeitung mit Commit alle N Dokumente oder alle M Sekunden | Ab wenigen tausend Dateien, auf langsamem Speicher sofort |
| Volle Parallelität für OCR | Nextcloud-Weboberfläche wird während der Indexierung zäh | Ein Worker, `nice`, Lastschwelle, Pausieren bei Nutzeraktivität | Auf 2-Kern-Boxen sofort |
| Textextraktion ohne Längenkappung | Ein Dokument erzeugt hunderttausende Chunks und bläht Index und RAM | Kappung pro Dokument, Chunk-Deduplizierung, Mindestlänge | Beim ersten sehr großen Dokument, also unvermeidlich |
| Rechteprüfung erst nach dem Ranking, dann Nachladen in einer Schleife | Suchanfrage macht dutzende Nextcloud-Aufrufe, Antwortzeit im Sekundenbereich | Gebündelte Prüfung für eine Kandidatenliste, ein Aufruf statt N | Ab etwa 20 Treffern pro Anfrage |
| Vollständiger Abgleich bei jedem Durchlauf | CPU-Last alle paar Minuten, Platte läuft dauernd | Inkrementeller Abgleich über Wasserzeichen, Tiefenabgleich selten und nachts | Ab etwa 100.000 Dateien |
| Snippet-Erzeugung durch erneutes Lesen der Originaldatei | Jede Suche löst Dateizugriffe und ggf. Entschlüsselung aus | Kurzen Kontext pro Chunk im Index halten (mit Rechteprüfung davor) | Sofort bei großen Dateien auf langsamem Speicher |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Snippet vor der Rechteprüfung erzeugen oder ausliefern | Direkter Inhaltsabfluss zwischen Nutzern, auch ohne Dateizugriff | Prüfen, dann rendern. Ein einziger Testfall mit entzogener Freigabe im Dauergate |
| Trefferzahl vor dem Filtern melden | Existenz und Umfang fremder Dokumente werden verraten | Erst filtern, dann zählen, oder unscharf ausweisen |
| Systemrechte oder Impersonation im Suchpfad benutzen | Kompletter Umgehungspfad um das Rechtesystem, Store-relevanter Befund | Eine Client-Fabrik, die eine Nutzeridentität erzwingt; kein Systempfad im Suchcode |
| files_accesscontrol-Regeln stillschweigend ignorieren | Genau die Schwäche, die Nextcloud für Context Chat offen dokumentiert | Entweder respektieren oder in der Store-Beschreibung ausweisen. Nicht verschweigen |
| Extrahierten Text oder OCR-Ergebnisse in Logdateien schreiben | Dokumentinhalte landen im Nextcloud-Log, das andere Admins und Backups sehen | Nur Datei-IDs und Fehlercodes loggen, niemals Inhalte, auch nicht im Debug-Modus |
| Papierkorb und Versionen mitindexieren | Gelöschte Dokumente bleiben auffindbar, Löschung wirkt nicht | Papierkorb und Versionshistorie ausschließen; Löschung entfernt sofort aus dem Index |
| Link-Shares und föderierte Shares als vollwertige Nutzer behandeln | Öffentliche Links könnten Suchtreffer erzeugen | Suche nur für angemeldete Nutzer, kein Suchpfad ohne Nutzeridentität |
| Ausgehende Verbindungen aus dem Container (Modell-Download, Update-Check, Telemetrie) | Bricht das Privacy-Versprechen und fällt bei der Store-Prüfung auf | Modelle im Image, keine ausgehenden Verbindungen im Normalbetrieb, dokumentiert |
| Zip-Bomben und ressourcenintensive Eingaben verarbeiten | Denial of Service durch eine hochgeladene Datei | Archive nicht auspacken, Ressourcenlimits pro Job, Pixel- und Seitengrenzen |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Suche liefert während der Erstindexierung nichts, ohne Erklärung | Nutzer hält die App für kaputt und deinstalliert am ersten Tag | Trefferliste zeigt Hinweis "Indexierung läuft: 4.120 von 12.412 Dokumenten durchsucht" |
| Fortschritt nur als Prozentzahl ohne Restzeit | Admin weiß nicht, ob 6 Stunden oder 6 Tage | Durchsatz messen und Restzeit schätzen, plus aktuell bearbeiteter Bereich |
| Übersprungene Dateien unsichtbar lassen | Nutzer sucht ewig nach einem Dokument, das nie indexiert wurde | Gruppierte `skipped`- und `failed`-Liste mit Grund und der Angabe, welche Grenze das ändern würde |
| Semantische Treffer ohne Belegstelle | Nutzer versteht nicht, warum ein Dokument getroffen wurde, und misstraut der Suche | Immer die passende Textstelle zeigen, bei semantischen Treffern kenntlich machen |
| Volltext und Semantik als getrennte Ergebnislisten | Nutzer muss verstehen, was er will, bevor er sucht | Ein Ergebnis, hybrid gerankt, ohne Modus-Auswahl |
| Exakte Suche (Rechnungsnummer, Dateiname) geht in der Semantik unter | Der häufigste reale Suchfall funktioniert schlechter als vorher | Exakte Treffer immer oben, Anführungszeichen als exakte Phrase unterstützen |
| Einstellungsseite mit 20 Optionen | Widerspricht dem Zero-Config-Versprechen und verunsichert | Eine Statusseite, wenige Schalter, alles Weitere hinter "Erweitert" |
| Deinstallation ohne Aussage zum Index | Admin weiß nicht, ob mehrere Gigabyte auf der Platte bleiben | Beim Entfernen ausdrücklich sagen, was mit dem Volume geschieht, und eine Aufräumaktion anbieten |

## "Looks Done But Isn't" Checklist

- [ ] **Indexlauf:** Oft fehlt die Wiederaufnahme. Prüfen: `docker kill` mitten im Lauf, Neustart, Fortsetzung ohne Datenverlust und ohne Neubeginn
- [ ] **Fehlerbehandlung:** Oft fehlt der Testkorpus mit kaputten Eingaben. Prüfen: defektes PDF, passwortgeschütztes PDF, 0-Byte-Datei, falsche Endung, 500-MB-Datei, Datei mit Sonderzeichen und Emojis im Namen, Datei auf externem Speicher
- [ ] **Datenintegrität:** Oft fehlt der Beweis. Prüfen: Prüfsummen aller Quelldateien vor und nach einem vollen Indexlauf identisch
- [ ] **Rechte:** Oft fehlt der Entzugsfall. Prüfen: Freigabe entziehen, danach darf weder Treffer noch Snippet noch Trefferzahl etwas verraten. Zusätzlich Gruppenordner mit Teilrechten und files_accesscontrol
- [ ] **Löschung:** Oft bleibt der Indexeintrag. Prüfen: Datei löschen, Ordner rekursiv löschen, Papierkorb leeren, jeweils sofortige Unauffindbarkeit
- [ ] **Events:** Oft nur über die Weboberfläche getestet. Prüfen: Upload per Desktop-Client, per WebDAV, per occ, per externem Speicher, jeweils mit anschließendem Treffer
- [ ] **Abgleich:** Oft nie ohne Events getestet. Prüfen: Events komplett blockieren, Dateien ändern, nach einem Abgleichzyklus muss der Index korrekt sein
- [ ] **Ressourcen:** Oft nur auf dem Entwicklerrechner gemessen. Prüfen: Vollindex auf 4-GB-ARM-Box, RSS-Kurve über die gesamte Laufzeit, kein OOM, Nextcloud bleibt bedienbar
- [ ] **Speicherplatz:** Oft ungetestet. Prüfen: Platte künstlich füllen, Indexer muss pausieren statt zu beschädigen; danach Platz schaffen, Fortsetzung muss klappen
- [ ] **Neuaufbau:** Oft nur dokumentiert. Prüfen: Index-Volume löschen, App startet, baut neu auf, erreicht denselben Deckungsgrad
- [ ] **Multi-Arch:** Oft nur gebaut, nie gestartet. Prüfen: arm64-Image auf echter ARM-Hardware starten, Handshake, Index, Suche
- [ ] **Deployment:** Oft nur eine Topologie. Prüfen: docker-compose und AIO, jeweils Installation, Update und Deinstallation
- [ ] **Update:** Oft ungetestet. Prüfen: Version installieren, Daten indexieren, auf neue Version aktualisieren, Index muss erhalten und schemakompatibel sein
- [ ] **Deinstallation:** Oft bleiben Reste. Prüfen: PHP-App-Tabellen, Einstellungen, registrierte Event-Listener, Suchanbieter, Volume
- [ ] **Zero-Config:** Oft ist eine Einstellung doch nötig. Prüfen: frische Installation ohne einen einzigen Konfigurationsschritt, erste erfolgreiche Suche protokollieren

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Hängender Indexlauf beim Nutzer | LOW, wenn vorgesorgt | Stale-Claim-Reaper greift automatisch; Admin-Aktion "Lauf zurücksetzen" setzt `claimed` auf `pending`; betroffene Datei landet mit Grund in der Fehlerliste |
| Beschädigter Index | MEDIUM | Integritätsprüfung beim Start erkennt es, Index wird verworfen und neu aufgebaut, Suche meldet währenddessen degradierten Zustand statt Fehler |
| Rechteleck bereits ausgeliefert | HIGH | Sofort Patch-Release, Sicherheitshinweis im Store und README, Snippet-Ausgabe notfalls per Serverkonfiguration abschaltbar machen. Deshalb ist Vorbeugung hier die einzige sinnvolle Strategie |
| Datenverlust durch Schreibpfad | Nicht erstattbar | Existiert nur, wenn die Architekturregel gebrochen wurde. Kein Recovery, nur Prävention. Deshalb Prüfsummen-Gate in der CI |
| OOM-Schleife auf kleiner Box | LOW bis MEDIUM | Beim Start erkennen, dass der letzte Job nicht abgeschlossen wurde, diesen als `failed: suspected_oom` markieren und überspringen statt erneut zu versuchen. Automatisches Herunterregeln der Budgets |
| Index und Nextcloud nach Restore inkonsistent | LOW, wenn Instanzbindung vorhanden | Instanz-ID- und Epoch-Prüfung beim Start erzwingt vollen Abgleich; Admin sieht "Wiederherstellung erkannt, gleiche ab" |
| Nextcloud-Major bricht die App | MEDIUM | Vorgezogene Erkennung durch CI gegen die Entwicklungslinie; Notfallplan ist ein Kompatibilitäts-Release der PHP-App allein, weil der Container versionsunabhängig ist |
| AppAPI oder Docker-API-Bruch (Fall #712) | MEDIUM, extern | Kompatibilitätsmatrix im README, schnelle Kommunikation, Verweis auf die AppAPI-Version. Nicht unser Fehler, aber unser Supportaufkommen |

## Pitfall-to-Phase Mapping

Phasennamen sind Vorschläge für den Roadmap-Zuschnitt.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 9 Deployment und Deploy-Daemon | Phase 1 Foundations (ExApp-Skelett, HaRP, Handshake) | Grüne AppAPI-Testbereitstellung auf docker-compose und AIO |
| 11 Multi-Arch und Wheels | Phase 1 Foundations (Basisimage-Entscheidung) | arm64-Image startet auf echter ARM-Hardware, kein Compiler im Image |
| 13 Store, App-ID, Zertifikat | Phase 1 (Naming) und Phase 8 (Einreichung) | App-ID eingefroren vor dem ersten Bau-Commit, `info.xml` schemavalidiert |
| 3 Datenverlust durch OCR | Phase 1 (Architekturregel) und Phase 3 (OCR) | Prüfsummenlauf über Korpus mit defekten PDFs, Grep-Gate gegen Schreib-APIs |
| 1 Hängender Indexlauf | Phase 2 Indexkern | Kill-und-Fortsetzungstest, Stale-Claim-Reaper unter Test |
| 2 Stiller Ausfall | Phase 2 (Zähler) und Phase 6 (Admin-UI) | Kanarienvogel-Selbsttest, Deckungsgrad wird berechnet und angezeigt |
| 5 Event-Lücken und Drift | Phase 2 Indexkern und Event-Anbindung | Index korrekt auch bei vollständig blockierten Events nach einem Abgleich |
| 7 Zero-Config-Defaults | Phase 2 (Allowlist, Limits) und Phase 6 (Sichtbarkeit) | Vollindex auf einem realistischen Bestand ohne Ressourcenalarm, `skipped` mit Gründen |
| 8 Index als nicht rekonstruierbarer Zustand | Phase 2 (Transaktionen, Instanzbindung) und Phase 7 (Härtung) | Disk-Full-Test, Volume-Lösch-Test, Restore-Simulation |
| 4 OCR-Ressourcen | Phase 3 OCR und Phase 7 Härtung | Lasttest auf 4-GB-ARM, kein OOM, Nextcloud bleibt bedienbar |
| 10 Vektorindex-Wachstum | Phase 4 Semantik | Skalierungstest 50.000 Dokumente, Kennzahl Bytes pro Dokument, Antwortzeit unter Zielwert |
| 6 Berechtigungsleck | Phase 5 Unified Search, Phase 1 Client-Fabrik, Phase 7 Testsuite | Paritätstest gegen die native Nextcloud-Suche für sechs Rechteszenarien, als Dauergate |
| 12 Kompatibilitätsspirale | Phase 1 (schmale PHP-Fläche) und Phase 8 (Wartungsrhythmus) | CI läuft gegen die Nextcloud-Entwicklungslinie, Kompatibilitätsmatrix im README |
| 14 Wettbewerbsrisiko | durchgehend, konkret Phase 7 und 8 | Benchmark-Zahlen auf Zielhardware liegen vor dem Launch vor |

## Sources

Issue-Tracker und Foren (Fehlermodi des Vorgängerökosystems):
- https://github.com/nextcloud/fulltextsearch/issues/311: Indexlauf hängt, RAM-Plateau, Endlosschleife beim zweiten Nutzer (offen seit 2018) (HIGH)
- https://github.com/nextcloud/fulltextsearch/issues/404: Index wird bei der ersten Datei unresponsive (HIGH)
- https://github.com/nextcloud/fulltextsearch/issues/597: keine Indexierung mehr nach Update, Selbsttest meldet trotzdem "ok" (HIGH)
- https://github.com/nextcloud/fulltextsearch/issues/715: Dateien bleiben nach Verzeichnislöschung im Index (HIGH)
- https://github.com/nextcloud/fulltextsearch/issues/769: Upload über Desktop-Sync löst Löschung statt Indexierung aus (offen seit 2023) (HIGH)
- https://github.com/nextcloud/fulltextsearch/issues/857: Reset indexiert alte Dateien nicht neu, Zähler bleibt stehen (HIGH)
- https://github.com/nextcloud/fulltextsearch/issues/950: kein Release für Nextcloud 34 (Juni 2026) (HIGH)
- https://github.com/nextcloud/fulltextsearch/issues/955: Frage nach NC 34/35, unbeantwortet (Juli 2026) (HIGH)
- https://github.com/nextcloud/fulltextsearch/issues/956: App lässt NC 34 hängen, Abhilfe Deaktivieren (HIGH)
- https://github.com/nextcloud/fulltextsearch/issues/218: große TIFF-Dateien werden nicht OCR-verarbeitet (MEDIUM)
- https://github.com/nextcloud/fulltextsearch_elasticsearch/issues/15: gelöschte Dateien bleiben im Index (HIGH)
- https://github.com/nextcloud/fulltextsearch_elasticsearch/issues/346: vollständiger Index nicht möglich (MEDIUM)
- https://github.com/nextcloud/files_fulltextsearch_tesseract/issues/30: PDFs werden bei Ghostscript-Fehler gelöscht (offen seit 09/2020) (HIGH)
- https://help.nextcloud.com/t/warning-full-text-search-files-tesseract-ocr-app-w-pdf-enabled-may-delete-your-pdfs/93151: Forum-Warnthread zum Datenverlust (HIGH)
- https://help.nextcloud.com/t/cannot-complete-initial-fulltextsearch-index/187771: Erstindex lässt sich nicht abschließen (MEDIUM)
- https://help.nextcloud.com/t/fulltextsearch-index-runs-indexes-files-no-content/78265: Index läuft, Inhalte fehlen (MEDIUM)
- https://help.nextcloud.com/t/fulltextsearch-compatibility-for-nc-34-35/246992: Kompatibilitätslage NC 34/35 (MEDIUM)

Offizielle Nextcloud-Dokumentation:
- https://docs.nextcloud.com/server/stable/developer_manual/exapp_development/tech_details/api/events_listener.html: Events sind asynchron, nur `node_event`, keine Retry-Zusage (HIGH)
- https://docs.nextcloud.com/server/stable/admin_manual/webhook_listeners/index.html: Zustellung über Hintergrundjobs, Worker-Empfehlung (HIGH)
- https://docs.nextcloud.com/server/stable/developer_manual/digging_deeper/search.html: IProvider, eigener HTTP-Request pro Anbieter, Cursor statt Offset, `SearchResultEntry` (HIGH)
- https://docs.nextcloud.com/server/stable/admin_manual/ai/app_context_chat.html: 12 GB RAM CPU-only, AVX/AVX2 Pflicht, 100-MB-Grenze, passwortgeschützte Dateien werden still ignoriert, files_accesscontrol wird nicht befolgt (HIGH)
- https://docs.nextcloud.com/server/stable/admin_manual/exapps_management/ManagingExApps.html: `nc_app_<app_id>_data`, `APP_PERSISTENT_STORAGE`, Volume bleibt beim Unregister (HIGH)
- https://docs.nextcloud.com/server/stable/admin_manual/exapps_management/DeployConfigurations.html und ManagingDeployDaemons.html: HaRP als neuer Standard, DSP abgekündigt, Entfernung für NC 35 geplant, `manual_install` als Sonderfall (HIGH)
- https://github.com/nextcloud/app_api/issues/712: Docker 29 verlangt API 1.44, AppAPI sprach 1.41, Deployment tot (11/2025) (HIGH)

Werkzeugkette und Abhängigkeiten:
- https://ocrmypdf.readthedocs.io/en/latest/advanced.html: sqrt(N)-Regel, `--tesseract-downsample-large-images`, `--skip-big` (HIGH)
- https://github.com/ocrmypdf/OCRmyPDF/discussions/1386 und issues/1385: Speicherlimits, OOM-Rückfall auf `--jobs 1` (MEDIUM)
- https://github.com/tesseract-ocr/tesseract/issues/2973: hohe CPU- und RAM-Last mit ocrmypdf (MEDIUM)
- https://github.com/asg017/sqlite-vec/issues/25: ANN-Index offen, aktuell reine Brute-Force-Suche (HIGH)
- https://github.com/quickwit-oss/tantivy-py/issues/371: fehlendes Wheel für Python 3.13 bei Version 0.22 (HIGH)
- PyPI-Abfrage am 15.08.2026: tantivy 0.26.0, onnxruntime 1.28.0, sqlite-vec 0.1.9 mit cp313-Wheels für manylinux aarch64, jeweils **ohne** musl-Wheels; fastembed 0.8.0 als reines py3-none-any (HIGH, live geprüft)

Nextcloud-Produktlinie und Wettbewerb:
- https://nextcloud.com/blog/nextcloud-hub26-spring/: Assistant nutzt Unified Search, Context Agent (MEDIUM)
- https://github.com/nextcloud/context_chat: Positionierung und Grenzen (MEDIUM)

Schwesterprojekt (Store- und Zertifikatspipeline, ExApp-Deployment, Rechtefallen):
- C:\Users\Student\nextcloud-mcp-connector\.planning\research\PITFALLS.md: Pitfalls 4, 5, 6 und 8 (HIGH)

Offene Punkte mit MEDIUM oder LOW confidence, in der Umsetzung zu verifizieren:
- Ob AIO-Borg-Sicherungen die Volumes `nc_app_*` ohne ausdrückliche Konfiguration erfassen (Doku spricht von der Möglichkeit, externe Volumes einzutragen, was auf opt-in hindeutet)
- Ob und wie `occ app_api:app:update` das Volume in allen Daemon-Typen erhält (Doku sagt ja für den Standardfall, praktisch am AIO nachstellen)
- Verhalten von Nextcloud-Suchanbietern bei sehr langsamen Antworten (Doku nennt keine Timeouts; eigene harte Obergrenze setzen, Zielwert unter 500 Millisekunden)

---
*Pitfalls research for: Nextcloud-ExApp für Suche (OCR + Volltext + Semantik, Zero-Config)*
*Researched: 2026-08-15*
