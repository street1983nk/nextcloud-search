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
