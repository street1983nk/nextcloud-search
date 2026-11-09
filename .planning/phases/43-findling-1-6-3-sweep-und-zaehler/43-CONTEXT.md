# Phase 43: Findling 1.6.3, Löschlauf unabhängig vom Quiet-Gate und Zähler pro Dokument (#25) - Context

**Gathered:** 2026-11-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Zwei Fixes aus Issue #25 (Melder mbozem), dann Release 1.6.3:

1. **Löschlauf entkoppeln:** `_sweep_vanished` (backend/src/findling/worker/reconcile.py) läuft heute nur hinter einem vollen Walk über alle Mounts (run_once Schritt 5). Der Walk steht hinter dem Quiet-Gate (`stats.crawling` oder `stats.scheduled >= quiet_max`). Auf einer Instanz mit Dauer-Crawl läuft der Sweep nie, der 30-Tage-Stempel wird nie gesetzt (mbozem: 38x queue_busy, 0x walked in 24 h, `vanished_storages` leer, 31.571 Zeilen auf 13 nicht mehr eingebundenen Speichern). Der Sweep braucht nur eine vollständige Mountliste, keinen Walk.
2. **Zähler pro Dokument:** Der Zähler der Abdeckung (indexiert / gesehen) soll Zähler und Nenner auf dieselbe Menge beziehen: jedes Dokument einmal, Schlüssel (countingKey des Speichers, Pfad). Die PHP-App liefert die Zuordnung storage zu countingKey (StorageService::countingKeyGroups/countingKey gibt es schon) und eine kompakte leaveOut-Liste mit. Der Container zählt distinct (key, path) im Hintergrund (Muster der 1.6.2-Hintergrundzählung). Erwartung bei mbozem: 43.602 / 247.123, etwa 18 % statt 29 %.

Danach: Audit (Security, Bugs, Performance), Owner-Runde, Store-Einreichung 1.6.3. Die Antwort in #25 kommt erst NACH dem Store-Release (Dauerregel).

</domain>

<decisions>
## Implementation Decisions

### Takt des Löschlaufs
- **D-43-01:** Der Sweep läuft einmal pro Abgleich-Takt (gleiche Fälligkeit wie `_is_due`, gleicher Stempel-Mechanismus), NICHT bei jeder 5-Minuten-Runde. Er läuft auch dann, wenn das Quiet-Gate den Walk blockiert (Crawl unfertig oder Warteschlange über quiet_max).
- **D-43-02:** Voraussetzungen bleiben: Mountliste erreichbar, nicht leer, kein verworfener Eintrag (`found.mounts and not found.discarded`, T-36-13). Eine nicht lesbare Warteschlange (`stats.ok` false) ist weiter kein Freibrief: dann kein Sweep in dieser Runde.
- **D-43-03:** Gelöschte und abgewählte Speicher (gone/deselected aus `files.gone_storages`) verlieren ihre Dokumente sofort, auch während eines laufenden Crawls. Löschaufträge gehen wie bisher in Bändern zu REQUEUE_BAND über `_hand_over`.

### 30-Tage-Frist
- **D-43-04:** VANISHED_STORAGE_GRACE_SECONDS bleibt 30 Tage, gezählt ab dem ersten Lauf, der den Speicher vermisst (also ab dem Update auf Bestandsinstanzen). Kein rückwirkender Start, keine Einstellung.
- **D-43-05:** Zu prüfen in der Recherche: Werden Home-Speicher gelöschter Nutzer ohne `oc_storages`-Zeile (mbozem: 215/216/221/226/231) von `gone_storages` als gone erkannt und damit sofort entfernt? Falls nicht, ist das ein Befund für diese Phase (Erwartung des Owners: sie gehen sofort).

### Neue Zahl im Admin
- **D-43-06:** Nach dem Update zeigt die Admin-Seite einmalig einen kurzen Hinweis neben der Abdeckungszahl, sinngemäß: "Ab 1.6.3 zählt jedes Dokument einmal, die Zahl kann sinken." Er verschwindet nach dem ersten vollständigen Zähllauf mit der neuen Zählweise. Dreisprachig DE/EN/FR, nicht extrem kurz, nur nicht sinnlos lang, Text vor Umsetzung dem Owner zeigen.
- **D-43-07:** Die Zählung pro Dokument ersetzt die gruppierte Zahl als Hauptzahl. Dokumente, die nur noch auf einem nicht eingebundenen Speicher liegen (mbozem: 206), zählen nicht als durchsuchbar.

### Warum #25 dreimal als gelöst galt (Owner 07.11.: genau hinsehen)
Verlauf: 1.4.2 (nur eingebundene Speicher im Nenner), 1.6.0 (Gruppierung per countingKey), 1.6.2 (Vektorzahl im Hintergrund, größtes Mitglied vertritt) und am 04.11. von uns geschlossen, ohne Bestätigung des Melders. Jede Release hat die gerade gemeldete Schicht korrigiert, und mbozem fand danach die nächste:
- 1.6.0: Die Korrektur schaltete sich bei mehr als 100.000 ausgelassenen Dokumenten selbst ab (LEFT_OUT_EMBEDDED_CEILING), und der Vertreter war die kleinste ID statt des größten Mitglieds.
- 1.6.2: Der Nenner zählt pro Dokument, der Zähler zieht nur Zeilen pro Speicher ab. Der Index hält eine Zeile pro Mount derselben Freigabe (Schlüssel storage_id, file_id). Dazu kommen Zeilen verschwundener Speicher, die der Sweep nie entfernt.
- Gemeinsame Ursache: Die Tests prüfen Einzelteile (z. B. test_status_leave_out.py). Unser Nachbau (zwei sftp-Mounts, gleiche Sicht, eine Freigabe) bildet die echte Lage nicht ab. Es fehlte die End-to-End-Prüfung "angezeigte Zahl gleich unabhängig berechnete Wahrheit".

Daraus folgt für diese Phase:
- **D-43-08:** Pflicht-Abnahmetest mit einer Topologie wie bei mbozem: mehrere Freigaben, mehrere Nutzer pro Freigabe mit UNTERSCHIEDLICHER Sicht (files_seen je Mitglied verschieden), dieselbe Datei auf zwei Freigaben, Dokumente nur in ausgelassenen Mitgliedern, Dokumente nur auf verschwundenen Speichern, gelöschte Nutzer ohne oc_storages-Zeile, Crawl unfertig und Warteschlange über quiet_max. Die erwartete Zahl wird UNABHÄNGIG berechnet (eigene SQL-/Python-Zählung distinct (Freigabe, Pfad), nicht mit dem Code der Umsetzung, Regel "Gegenprobe nie mit dem Muster der Umsetzung"), dazu eine Positivkontrolle.
- **D-43-09:** Die Recherche prüft, ob Zähler und Nenner danach wirklich dieselbe Menge messen. Offene Frage aus #25: Der Nenner nimmt das größte Mitglied je Gruppe. Bei unterschiedlicher Sicht pro Nutzer (Archiv: 28.303 bis 112.053) kann die Vereinigung größer sein als das größte Mitglied, dann wäre der Nenner zu klein und die Quote könnte über 100 % gehen. Invariante: Quote nie über 100 %, und bei leerer Warteschlange und fertigem Crawl muss die Zahl die tatsächliche Abdeckung zeigen (das war die Ursprungsbeschwerde).
- **D-43-10:** Vor der Store-Einreichung bekommt mbozem einen Testbuild (er hat das angeboten) und prüft seine Zahl, Ziel etwa 18 % bei laufendem Crawl. Den Kommentar mit der Anfrage formuliert Claude, er geht nur mit Owner-Freigabe raus. #25 wird erst geschlossen, wenn mbozem bestätigt, nie vorher von uns.

### Nachträge des Owners (07.11., Planrevision 1)
- **D-43-11:** Dateien, die gelistet, aber nicht lesbar sind (skipped/unreadable, z. B. SMB-ACL), die PHP als failed/repeatedly_stuck aufgibt, und skipped/gone, das nur PHP entscheidet, GEHÖREN ZUM NENNER: nicht durchsuchbar senkt die Abdeckung ehrlich (z. B. 190/200 = 95 %). Die Seite zeigt daneben, wie viele Dateien nicht lesbar oder hängen geblieben sind. Rechnung pro Freigabegruppe, nicht ein globales Maximum: Nenner = Summe über Gruppen und Einzelspeicher von max(PHP_g, judged_g + phpOnly_g); der Zähler ist immer eine Teilmenge; die Quote geht nie über 100 %.
- **D-43-12:** Der einmalige Hinweis (D-43-06) bleibt nach der ersten vollständigen Zählung mit /coverage noch 7 Tage sichtbar und verschwindet dann von selbst (Zeitstempel speichern, nicht beim ersten Ergebnis löschen). Ersetzt den Satz "Er verschwindet nach dem ersten vollständigen Zähllauf" in D-43-06.

- **D-43-13:** KEIN öffentliches GitHub-Pre-Release. mbozem hat ein GitHub-Konto; der Testbuild geht als Workflow-Artefakt (signiertes Companion-Archiv) plus unveränderliches Image :<sha> und eine Test-info.xml an ihn. Der Kommentar erklärt den Download (angemeldet) und nennt den Ablauf der Artefakte (Aufbewahrung in Tagen).

- **D-43-14:** Die Doppelzählung bei Weiterteilung eines SMB-Ordners per Nextcloud-Freigabe und bei verschiedenen Einhängepunkten (Recherche A1) wird in 1.6.3 RICHTIG behoben, nicht nur sichtbar gemacht: Dokumentschlüssel ist der interne Pfad innerhalb der Freigabe (aus oc_filecache.path des Speichers, zusammen mit dem countingKey), nicht files.path (Leserpfad). Dafür eine neue Container-Spalte mit Backfill (erlaubt, STOPP-Regel ausdrücklich erweitert: eine Spalte samt Backfill-Weg, sonst nichts). PHP liefert den Schlüssel gehasht, Pfade bleiben aus Logs (T-36-17). Der Backfill bestehender Zeilen (mbozem: 190.000) ist begrenzt, fortsetzbar und in Upgrade-E2E (1.6.2 -> 1.6.3) und Audit abgedeckt. Das Konzept "known double count" entfällt: der Fall zählt genau einmal.

### Claude's Discretion
- Wo genau der Sweep in run_once eingehängt wird (vor dem Quiet-Gate mit eigener Fälligkeit oder als eigener Zweig nach der Mountliste), solange D-43-01/02 gelten.
- Format der storage-zu-key-Map und der leaveOut-Liste im PHP-Container-Vertrag, Bandgrößen, Indexe für die distinct-Zählung.
- Logzeilen nur mit Zählern und Speicher-IDs, nie Pfade (T-36-17).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Issue und Befund
- GitHub-Issue #25 (street1983nk/nextcloud-search), `gh issue view 25 --comments`: mbozem-Tabelle 05.11., Owner-Zusage "sweep independent of the queue, numerator counted per document"

### Löschlauf
- `backend/src/findling/worker/reconcile.py`: run_once (Schritte 1 bis 5), `_sweep_vanished`, `_quiet`, `_is_due`, VANISHED_STORAGE_GRACE_SECONDS, REQUEUE_BAND
- `.planning/phases/36-*/` (D-36-05, D-36-14, T-36-13, T-36-17, WR-36-02): Ursprung des Sweeps und der Frist

### Zählung
- `php/lib/Service/ScanStatsService.php` totals() und `grouped`
- `php/lib/Service/StorageService.php` countingKeyGroups(), countingKey()
- `php/lib/Service/AdminViewService.php` (coverageShare, Anzeige)
- `.planning/phases/39-*/` (Weg C, D-37-03) und `.planning/phases/41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes/41-CONTEXT.md` (D-41-10, Hintergrundzählung #25)

### Ablauf
- `.planning/phases/41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes/` Pläne 41-08 bis 41-12 als Muster für CI, Audit, Owner-Runde, Tag und Store-Einreichung

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_sweep_vanished` selbst bleibt fast unverändert, nur der Aufrufort und die Bedingung ändern sich.
- `StorageService::countingKey` liefert schon den Schlüssel ohne Nutzeranteil (host + Pfad), nur für COUNTING_KEY_BACKENDS.
- Hintergrundzählung aus 1.6.2 (indexedLeftOut/embeddedLeftOut, antwortet bei mbozem in etwa 1 s).

### Integration Points
- PHP Admin-Status ruft Container-Zählung; Vertrag PHP/Container ist Paritätstest-pflichtig (Muster REQUEUE_BAND-Parität).

</code_context>

<specifics>
## Specific Ideas

- Gegencheck mit mbozem-Zahlen: 43.602 durchsuchbare Dokumente, 247.123 gesehen, etwa 18 %.
- mbozem hat angeboten, Varianten auf seiner Topologie zu testen.

</specifics>

<deferred>
## Deferred Ideas

- Index nur einmal pro Freigabe (Option 2 aus #25): verworfen, die Zeilen pro Mount tragen die Rechteauflösung.
- #45 Mount-Ausschluss und Slot-Anzeige: v1.7.

</deferred>

---

*Phase: 43-findling-1-6-3-sweep-und-zaehler*
*Context gathered: 2026-11-07*

### Nachtrag Owner 07.11. (W1, verschiedene Wurzeln)
- **D-43-15:** Zwei Konfigurationen derselben Freigabe mit verschiedener Wurzel zählen in 1.6.3 noch doppelt. Der Kommentar an mbozem (43-11) fragt, ob er so eine Konfiguration hat. Bestätigt er es, wird es vor dem Store-Release behoben (eigener Zusatzplan und Audit-Nachtrag). Verneint er, bleibt es in 1.6.3 eine bekannte Grenze im Changelog und wird in 1.6.4 behoben. Entscheidungspunkt ist K6 in 43-12.

### Nachtrag Owner 07.11. (DENY-ACE-Hänger, Fix in 1.6.3)
- **D-43-16** (gilt für 43-17 bis 43-19): Der Content-Gateway liest Dateien eines SMB-Speichers ohne Server-Verschlüsselung nicht blockierend mit Fristen: erster Block 30 s, Leerlauf 30 s (beide unter den 90 s des Backends), Lesedeckel MAX_READS gegen die volle stdin-Pipe von smbclient, wachsende Pause bis 200 ms. Ob nicht blockierend gelesen wird, entscheidet der Speicher über instanceOfStorage, nicht die Stream-Schicht (View legt bei aktivem Locking um jeden Stream einen CallbackWrapper). Alle anderen Speicher, verschlüsselte eingeschlossen, werden blockierend gelesen wie bisher. Die Antwort wird nach dem Vorlesen und vor den Headern entschieden: 0 Bytes bei Größe über 0, Frist abgelaufen, fread false, fopen false und FileInUseException ergeben 422 über den bestehenden Zweig; Größe 0 mit EOF ergibt 200 leer. Nach den Headern endet eine stockende Antwort kurz (Container-ShortRead, kein Content-Length), ein Abbruch des Clients beendet das Lesen. Fix-Runde 1 zu 43-18 (Lauf 42418778026): beide Fristen 80 s statt 30 s, weil smbclient bei SMB2 in ganzen Leseblöcken von 8 MiB weiterreicht (Samba 4.19.5 source3/libsmb/clireadwrite.c:363-366); weiter unter den 90 s des Backends.
- Container (43-18): 422 wird skipped(unreadable) und zählt einmal im Nenner und in "nicht lesbar" (präzisiert D-43-11); 500 und alle anderen Ablehnungen bleiben failed(gateway_error). Die gedeckelte Wiederholung gilt für beide Paare als eine Serie. 422 zählt nicht zur Ausfall-Schwelle. Bestandszeilen failed(gateway_error) aus 1.6.2 werden nicht umgeschrieben.
- E2E: gate-crawl und gate-queue im Wrapped-Modus, gate-queue zusätzlich nativ, v1.6.2 und upgrade nativ. Abhilfetext in 43-19.
- Quelle: 43-FREIGABEN.md (Owner-Entscheid DENY-ACE-Hänger, Entscheide F1 bis F4).

### Nachtrag Owner 09.11. (Wurzel-Frage ja, Schreibweisen)
- **D-43-15 bestätigt:** mbozem hat dieselbe Freigabe mit verschiedenen Wurzeln (https://github.com/street1983nk/nextcloud-search/issues/25#issuecomment-6735344512: `192.168.98.246 //Daten` 25-mal mit Wurzel `/`, 17-mal mit `/Arbeitssicherheit` (11), `/Projekte` (2), `/Fue`, `/Allgemein`, `/Arbeitsvorbereitung`, `/QM`). Behebung vor dem Store-Release (Zusatzpläne 43-21 bis 43-29).
- **D-43-17:** Dieselbe Freigabe in zwei Schreibweisen (`192.168.98.246//Daten` 42 Speicher, `//daten` 5, Paare auch auf `.2` und `.231`) zählt einmal: Host und Freigabename werden für die Zählung gefaltet. Quelle: 43-FREIGABEN.md `Freigabe Planung 43-21: "Ja go" (2026-11-09 09:25, Claude Code Terminal) Entscheid: ja`.
- **Leitregel für 43-21 bis 43-29:** Zwei verschiedene Dateien verschmelzen nie zu einem Dokument; im Zweifel nicht gruppieren (zu hoch, nie verschmolzen). Dokumentschlüssel und Freigabe-Identität dienen nur der Zählung.
- Offene Owner-Entscheide OE-1 bis OE-8 stehen in 43-21-PLAN.md Task 1; die Antworten werden dort als Maschinenzeilen in 43-FREIGABEN.md festgehalten und danach hier nachgetragen.
- Owner-Vorgabe 09.11.: "Zeit spielt keine Rolle, Hauptsache alles funktioniert."

### Nachtrag Owner 09.11.: Entscheide OE-1 bis OE-8 (Plan 43-21 Task 1, "Wie empfohlen")

- OE-1 a: Host und Freigabename ASCII-klein verglichen, Wurzel und Pfad ungefaltet, Unicode-Form NFC wie der Dateicache von Nextcloud.
- OE-2 a: lange (gehashte) Speicher-IDs nur über die Konfiguration des externen Speichers und nur bei genau passendem md5 der nachgebauten ID; $user durch die Nutzer-ID ersetzt; nicht Nachbaubares bleibt getrennt und wird als Zahlenfeld in der Overview und stündlich im Log gezeigt (warning bei hashedUngrouped > 0); Passwörter werden nie gelesen.
- OE-3 a: Samba [homes] oder Freigabe gleich Anmeldename nie gruppieren.
- OE-4 a: SFTP nur je Anmeldung (Nutzer@Host[:Port]) gruppieren.
- OE-5 a: Schlüsselformat 2 mit Formatmarke und einmaligem Neuaufbau, im Mischbetrieb nie eine falsche Zahl.
- OE-6 a: PHPUnit lokal per scripts/dev/phpunit_docker.sh für alle PHP-Änderungen in 43-21 bis 43-27 (mindestens 4 GB frei).
- OE-7 a: Samba path mit %U/%S als bekannte Grenze, ein englischer Satz unter Known limitations.
- OE-8 a: 43-11 schließt als "abweichend, abgelöst durch rc.2".
