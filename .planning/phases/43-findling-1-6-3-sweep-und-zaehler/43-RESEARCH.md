# Phase 43: Findling 1.6.3, Löschlauf unabhängig vom Quiet-Gate und Zähler pro Dokument (#25) - Research

**Researched:** 2026-11-07
**Domain:** Container-Abgleich (reconcile.py), PHP/Container-Zählvertrag der Abdeckung, Release 1.6.3
**Confidence:** HIGH für Code-Befunde (alles am Code mit Zeilen belegt), MEDIUM für Denominator-Empfehlung und Testbuild-Übergabe

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Takt des Löschlaufs
- **D-43-01:** Der Sweep läuft einmal pro Abgleich-Takt (gleiche Fälligkeit wie `_is_due`, gleicher Stempel-Mechanismus), NICHT bei jeder 5-Minuten-Runde. Er läuft auch dann, wenn das Quiet-Gate den Walk blockiert (Crawl unfertig oder Warteschlange über quiet_max).
- **D-43-02:** Voraussetzungen bleiben: Mountliste erreichbar, nicht leer, kein verworfener Eintrag (`found.mounts and not found.discarded`, T-36-13). Eine nicht lesbare Warteschlange (`stats.ok` false) ist weiter kein Freibrief: dann kein Sweep in dieser Runde.
- **D-43-03:** Gelöschte und abgewählte Speicher (gone/deselected aus `files.gone_storages`) verlieren ihre Dokumente sofort, auch während eines laufenden Crawls. Löschaufträge gehen wie bisher in Bändern zu REQUEUE_BAND über `_hand_over`.

#### 30-Tage-Frist
- **D-43-04:** VANISHED_STORAGE_GRACE_SECONDS bleibt 30 Tage, gezählt ab dem ersten Lauf, der den Speicher vermisst (also ab dem Update auf Bestandsinstanzen). Kein rückwirkender Start, keine Einstellung.
- **D-43-05:** Zu prüfen in der Recherche: Werden Home-Speicher gelöschter Nutzer ohne `oc_storages`-Zeile (mbozem: 215/216/221/226/231) von `gone_storages` als gone erkannt und damit sofort entfernt? Falls nicht, ist das ein Befund für diese Phase (Erwartung des Owners: sie gehen sofort).

#### Neue Zahl im Admin
- **D-43-06:** Nach dem Update zeigt die Admin-Seite einmalig einen kurzen Hinweis neben der Abdeckungszahl, sinngemäß: "Ab 1.6.3 zählt jedes Dokument einmal, die Zahl kann sinken." Er verschwindet nach dem ersten vollständigen Zähllauf mit der neuen Zählweise. Dreisprachig DE/EN/FR, nicht extrem kurz, nur nicht sinnlos lang, Text vor Umsetzung dem Owner zeigen.
- **D-43-07:** Die Zählung pro Dokument ersetzt die gruppierte Zahl als Hauptzahl. Dokumente, die nur noch auf einem nicht eingebundenen Speicher liegen (mbozem: 206), zählen nicht als durchsuchbar.

#### Warum #25 dreimal als gelöst galt
- **D-43-08:** Pflicht-Abnahmetest mit einer Topologie wie bei mbozem: mehrere Freigaben, mehrere Nutzer pro Freigabe mit UNTERSCHIEDLICHER Sicht (files_seen je Mitglied verschieden), dieselbe Datei auf zwei Freigaben, Dokumente nur in ausgelassenen Mitgliedern, Dokumente nur auf verschwundenen Speichern, gelöschte Nutzer ohne oc_storages-Zeile, Crawl unfertig und Warteschlange über quiet_max. Die erwartete Zahl wird UNABHÄNGIG berechnet (eigene SQL-/Python-Zählung distinct (Freigabe, Pfad), nicht mit dem Code der Umsetzung, Regel "Gegenprobe nie mit dem Muster der Umsetzung"), dazu eine Positivkontrolle.
- **D-43-09:** Die Recherche prüft, ob Zähler und Nenner danach wirklich dieselbe Menge messen. Offene Frage aus #25: Der Nenner nimmt das größte Mitglied je Gruppe. Bei unterschiedlicher Sicht pro Nutzer (Archiv: 28.303 bis 112.053) kann die Vereinigung größer sein als das größte Mitglied, dann wäre der Nenner zu klein und die Quote könnte über 100 % gehen. Invariante: Quote nie über 100 %, und bei leerer Warteschlange und fertigem Crawl muss die Zahl die tatsächliche Abdeckung zeigen (das war die Ursprungsbeschwerde).
- **D-43-10:** Vor der Store-Einreichung bekommt mbozem einen Testbuild (er hat das angeboten) und prüft seine Zahl, Ziel etwa 18 % bei laufendem Crawl. Den Kommentar mit der Anfrage formuliert Claude, er geht nur mit Owner-Freigabe raus. #25 wird erst geschlossen, wenn mbozem bestätigt, nie vorher von uns.

### Claude's Discretion
- Wo genau der Sweep in run_once eingehängt wird (vor dem Quiet-Gate mit eigener Fälligkeit oder als eigener Zweig nach der Mountliste), solange D-43-01/02 gelten.
- Format der storage-zu-key-Map und der leaveOut-Liste im PHP-Container-Vertrag, Bandgrößen, Indexe für die distinct-Zählung.
- Logzeilen nur mit Zählern und Speicher-IDs, nie Pfade (T-36-17).

### Deferred Ideas (OUT OF SCOPE)
- Index nur einmal pro Freigabe (Option 2 aus #25): verworfen, die Zeilen pro Mount tragen die Rechteauflösung.
- #45 Mount-Ausschluss und Slot-Anzeige: v1.7.
</user_constraints>

## Project Constraints (from CLAUDE.md)

- Python 3.13 über uv (lokales System-Python defekt); PHP nur über Docker (`scripts/dev/phpunit_docker.sh`), Docker läuft derzeit nicht, PHP-Prüfung also über CI (`php.yml`, Job "PHPUnit over the companion app").
- Qualitätsgates Python: ruff-Vollregelsatz, pyright basic (lokal mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`), vulture, lokal grün vor Commit; ruff-format.
- Code Englisch; echte Umlaute nur in deutscher Prosa, nie in Code/URLs/YAML; keine Em-/En-Dashes; keine Emojis.
- Security/Privacy: keine Inhalte verlassen den Server, Berechtigungs-Durchgriff strikt, Logzeilen nur Zähler und IDs (T-36-17, T-04-06, T-39-01).
- Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde ab MEDIUM vor Abschluss fixen; Launch-Härtung vor Store-Abgabe; Produkttexte kurz, Textentwurf vor Release dem Owner zeigen; Umlaut-Audit aller nutzersichtbaren Texte.
- Neue nutzersichtbare Strings in allen ausgelieferten Katalogen (`php/l10n`: de, de_DE, es, fr, it, nl, pt_BR, pt_PT), `backend/tests/test_admin_ui_contract.py` prüft das; Glossare `docs/l10n-*.md` mitziehen.
- Commits nur als street1983nk <k.cherif@outlook.de>, keine Claude-Session-Zeilen, kein "closes #N" in Commit-Texten; vor jedem Push/Merge/Kommentar den Owner fragen; Issue-Antworten erst nach Store-Release; #25 erst nach Bestätigung durch mbozem schließen.

## Summary

Der Sweep hängt heute ausschließlich hinter einem vollständigen Walk (`reconcile.py:537-543`), und der Walk steht hinter `_quiet` (`reconcile.py:498-500`, `974-1001`). Bei Dauer-Crawl erreicht `run_once` nie Schritt 3, also wird die Mountliste nie gelesen und `vanished_storages` nie gestempelt; das deckt sich exakt mit mbozems Log (38x queue_busy, 0x walked). Der Fix braucht einen **eigenen Fälligkeitsstempel** für den Sweep (Meta-Key), weil die Walk-Fälligkeit `_is_due` aus der `reconcile`-Tabelle abgeleitet wird und auf einer blockierten Instanz dauerhaft "fällig" sagt (`unfinished > 0` oder `last_finished_at` alt), was ohne eigenen Stempel einen Sweep alle 5 Minuten ergäbe. D-43-05 ist am Code beantwortet: `StorageService::classifyAbsent` (`StorageService.php:422-479`) meldet jede gefragte ID ohne `oc_storages`-Zeile als gone; die Home-Speicher gelöschter Nutzer gehen also im ersten Sweep sofort, und Löschaufträge haben in der PHP-Warteschlange Vorrang vor Inhalt und OCR (`QueueMapper::KINDS`, `QueueMapper.php:75-81`).

Für den Zähler gilt: Der Container speichert `path` pro Zeile, und zwar relativ zum Nutzerordner des lesenden Nutzers (`QueueService.php:914`, `ltrim($userFolder->getRelativePath(...))`), also etwa `Daten/Projekte/x.pdf`. Bei einer Freigabe, die über eine Speicherkonfiguration pro Nutzer eingebunden ist, ist der Einhängepunkt für alle Nutzer gleich, damit ist (countingKey, path) ein tragfähiger Dokumentschlüssel. Der Benchmark auf 188.600 synthetischen Zeilen (22 Gruppenmitglieder, 165.000 gruppierte Zeilen) zählt distinct (Gruppe, Pfad) in einem Durchlauf über `files_storage` in etwa 0,3 s; ein neuer Index ist nicht nötig. Zwei Befunde nebenbei: `Store.counts()` (`repo.py:1070-1080`) zählt Tombstones mit (der Tombstone setzt nur `deleted_at`, `repo.py:572-574`), der heutige Zähler `indexed` enthält also gelöschte Dokumente; und der heutige Abzug über `indexed_in_storages` arbeitet pro Zeile, nicht pro Dokument (die Ursache aus #25).

Zu D-43-09: Mit "größtes Mitglied" im Nenner und Vereinigung im Zähler messen beide NICHT dieselbe Menge, sobald kein Mitglied alle anderen umfasst. Über 100 % geht die Anzeige trotzdem nie, weil `coverageShare` bei `counted > indexable` null liefert (`AdminViewService.php:2360-2375`); dann zeigt die Seite statt einer Quote den Satz "wird neu gezählt", was falsch wäre. Eine echte Vereinigung im Nenner ist mit `files_seen` (ein Zähler pro Speicher) nicht machbar. Empfohlen wird eine **Untergrenze der Vereinigung aus dem Container**: `judgedDocuments` = distinct (Schlüssel, Pfad) über alle lebenden Zeilen eingebundener Speicher, deren Urteil zur Nennermenge gehört; Nenner = max(PHP-Nenner, judgedDocuments). Damit gilt Zähler ≤ judgedDocuments ≤ Nenner immer, und bei leerer Warteschlange und fertigem Crawl ist judgedDocuments die Vereinigung, die Quote also die tatsächliche Abdeckung.

**Primary recommendation:** Sweep mit eigenem Meta-Stempel `storage_sweep_at` nach der gleichen Kadenzregel wie `_is_due` (Intervall, bevorzugte Stunde, 2x-Ausweg), eingehängt nach dem `stats.ok`-Teil des Quiet-Gates und vor dem Walk; Zählung pro Dokument über einen neuen POST-Vertrag `{mounted, groups}` mit Hintergrundzählung und Cache nach dem 1.6.2-Muster, Antwort `{documents, embeddedDocuments, judgedDocuments}`, Nenner = max(gruppierter PHP-Nenner, judgedDocuments).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fälligkeit und Ausführung des Sweeps | Container (worker/reconcile.py) | PHP (Mountliste, gone_storages) | Kadenz gehört dem Container (D-01 aus Phase 3, kein zweiter Weckkanal); nur PHP sieht oc_storages/oc_mounts |
| Klassifikation gone/deselected | PHP (StorageService::classifyAbsent) | Container (Frist 30 Tage) | Container darf nie aus einer leeren Liste allein löschen |
| Löschen der Dokumente | PHP-Warteschlange (kind delete) bis Container-Poller | Container (tombstone) | einziger Löschpfad des Projekts (forget_storage-Docstring, `repo.py:1560-1570`) |
| Gruppierung (countingKey) und Mountmenge | PHP (StorageService, AdminViewService) | Container | Speicher-ID-Strings und oc_mounts kennt nur PHP |
| Zählung distinct (Schlüssel, Pfad) | Container (state.db, vectors.db) | PHP (übergibt Map) | nur der Container kennt Pfade und Urteile; Pfade verlassen ihn nie |
| Nenner, Quote, Hinweistext | PHP (AdminViewService, Template, admin.js) | Container (judgedDocuments) | eine Stelle rechnet die Quote (D-16-Prinzip `coverageShare`) |

## Standard Stack

Keine neuen Abhängigkeiten. Alles mit vorhandenen Mitteln:

| Baustein | Version | Zweck | Beleg |
|---------|---------|-------|-------|
| SQLite (Python stdlib) | 3.50.4 lokal (uv-Python) | `json_each` für die Mitglieder-Map, distinct-Zählung read-only | [VERIFIED: lokal `sqlite3.sqlite_version`] |
| FastAPI-Route im Container | vorhanden | neuer Admin-POST nach dem Muster `/probe` | [VERIFIED: backend/appinfo/info.xml:397-403] |
| `ExAppService::adminSend` | vorhanden | POST mit JSON-Body vom Admin an den Container | [VERIFIED: ExAppService.php:754-758] |
| Hintergrund-Thread mit Cache | vorhanden (1.6.2) | Single-Flight-Zählung, TTL 300 s, max. 4 Schlüssel | [VERIFIED: status.py:149-181, 874-974] |

## Package Legitimacy Audit

Diese Phase installiert keine externen Pakete. slopcheck nicht nötig.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
                Container-Runde (alle 300 s, reconcile.run)
                              |
                 backup gehalten? --ja--> warten (keine Runde)
                              |
                       queue.stats()
                 nicht ok --> ROUND_QUEUE_UNAVAILABLE, kein Sweep (D-43-02)
                              |
             busy (crawling / scheduled>=quiet_max)    ruhig
                    |                                    |
             Sweep fällig? (Meta storage_sweep_at,   Walk fällig? (_is_due)
             Kadenzregel wie _is_due)                 Sweep fällig?
                    |  ja                                |
                    v                                    v
             files.mounts()  -- unavailable --> back_off, Ende
                    |
        mounts leer oder discarded? --ja--> kein Sweep (T-36-13)
                    |
             _sweep_vanished(listed)
               living_storages - listed = absent
               files.gone_storages(absent) --> PHP classifyAbsent
                  gone (kein oc_storages) / deselected --> sofort
                  sonst --> Stempel, nach 30 Tagen
               _hand_over(delete) in Bändern zu 200 --> PHP-Queue (delete vor content/ocr)
                    |
             alles übergeben? --ja--> Meta storage_sweep_at = jetzt
                    |
             busy: Ende mit queue_busy | ruhig + Walk fällig: Walk wie bisher

  Admin-Seite (PHP overview)
     getMounts() --> mounted ids
     countingKeyGroups(mounted) --> groups
     ScanStatsService::totals(mounted, groups) --> grouped indexable (Nenner PHP)
     adminSend('/coverage', {mounted, groups})  --> Container
            Cache-Treffer? --> {documents, embeddedDocuments, judgedDocuments}
            sonst Hintergrund-Thread startet, Antwort counting=true
     Nenner = max(grouped indexable, judgedDocuments)
     Quote = coverageShare(documents, Nenner)
     Hinweis D-43-06 sichtbar, solange Flag gesetzt; erste vollständige Antwort löscht Flag
```

### Befund 1: Wo der Sweep hängt und warum er nie läuft

- `run_once` (`reconcile.py:484-552`): Schritt 1 `_quiet` (Z. 498-500) kehrt bei busy sofort zurück; Schritt 2 `_is_due` (Z. 517-518); Schritt 3 Mountliste (Z. 523-526); Schritt 4 Walk (Z. 531-535); Schritt 5 Sweep nur nach komplettem Walk und `found.mounts and not found.discarded` (Z. 537-543). [VERIFIED: Code]
- `_walk` prüft das Quiet-Gate vor jedem Slice erneut (Z. 585-587); eine Runde, die mitten im Walk busy wird, endet ebenfalls ohne Sweep. [VERIFIED: Code]
- `_is_due` (Z. 1003-1033) leitet die Fälligkeit aus `reconcile_state()` ab: `MAX(finished_at)` und Anzahl Mounts mit `after_file_id > 0` (`repo.py:648-650`). Ein unterbrochener Walk ist immer fällig. Auf einer blockierten Instanz ist daher `_is_due` dauernd wahr; als Sweep-Fälligkeit taugt es nicht (D-43-01 verlangt einmal pro Takt). [VERIFIED: Code]

### Pattern 1: Eigener Sweep-Stempel mit gemeinsamer Kadenzregel

**What:** Die Schwanzlogik von `_is_due` (Intervall `min_interval_hours`, bevorzugte Stunde `hour`, Ausweg bei 2x Intervall, "nie gelaufen = sofort fällig") in eine reine Funktion `_cadence_due(last_at)` ziehen und für Walk und Sweep verwenden. Der Sweep liest seinen letzten Zeitpunkt aus einem neuen Meta-Key (Vorschlag `storage_sweep_at`, Zahl als String, wie die anderen Meta-Werte via `read_meta`/`write_meta`, `repo.py:863-872`). Keine Schemaänderung nötig, `meta` ist frei verschlüsselt.

**Stempel setzen:** nur, wenn `_sweep_vanished` vollständig durchlief (alle Bänder angenommen). Dafür gibt `_sweep_vanished` künftig `bool` zurück (heute `None`, bricht bei Queue-Fehler in Z. 955-957 ab). Bei False: `_back_off()` und kein Stempel, die nächste Runde nach dem Cooldown versucht es erneut (Cooldown verdoppelt bis 1 h, `reconcile.py:1077-1079`).

**Einhängepunkt (Empfehlung):**

```python
# Skizze, nicht final
gate = await self._quiet(queue)
if gate == ROUND_QUEUE_UNAVAILABLE:          # D-43-02: kein Freibrief
    return RoundResult(gate)
catchup = ...  # Schritt 1b nur, wenn gate is None (wie heute)
walk_due = gate is None and await asyncio.to_thread(self._is_due, store)
sweep_due = await asyncio.to_thread(self._sweep_due, store)
if not walk_due and not sweep_due:
    return RoundResult(gate or ROUND_NOT_DUE)
found = await files.mounts()
if found.unavailable:
    self._back_off(); return RoundResult(ROUND_UNAVAILABLE)
if sweep_due and found.mounts and not found.discarded and self._backup_release.is_set():
    if await self._sweep_vanished(store, files, queue, frozenset(m.storage_id for m in found.mounts)):
        await asyncio.to_thread(store.write_meta, SWEEP_MARK, str(int(self._clock())))
    else:
        self._back_off()
if not walk_due:
    return RoundResult(gate or ROUND_NOT_DUE)
# Schritt 4 Walk unverändert; Schritt 5 entfällt (der Sweep lief schon vor dem Walk,
# oder er war nicht fällig).
```

Gründe: (a) Die Mountliste wird nur abgefragt, wenn Walk oder Sweep fällig ist, also einmal pro Takt im busy-Fall, nicht alle 5 Minuten. (b) T-36-13 bleibt wörtlich als Bedingung erhalten. (c) Der Sweep hängt nicht mehr vom Walk-Ergebnis ab, auch ein mitten im Walk abgebrochener Takt hat schon gesweept. (d) Catch-up (`CATCHUP_*`): Schritt 1b und `rewind_reconcile_walk` bleiben am ruhigen Pfad; der Sweep berührt `CATCHUP_MARK` nicht. Im `once`-Modus (Reconcile aus, Catch-up offen, `main.py:1277-1281`) ruft `run` nur unter `CATCHUP_RECONCILE` `run_once` auf (`reconcile.py:445-455`), ein Sweep dort entspricht dem bisherigen Sweep nach dem Catch-up-Walk. Bei ausgeschaltetem Reconcile (`FINDLING_RECONCILE_ENABLED=false`) läuft weiter kein Sweep; das ist Status quo und durch D-43 nicht verlangt. (e) Backup-Pause (#37): `run` startet keine Runde bei gehaltener Pause (Z. 433-437), `_in_flight` schützt den Übergang (Z. 444); zusätzlich `_backup_release.is_set()` vor dem Sweep und zwischen zwei Speichern prüfen, damit eine während der Runde gesetzte Pause nicht hinter ~160 Bändern (mbozem nach Ablauf der Frist: 31.571 IDs) warten muss. Ein Abbruch wegen Pause ist kein Fehler: kein Stempel, kein back_off.

**Tests, die sich ändern:** `test_the_sweep_only_follows_a_full_walk_without_a_discard` (`backend/tests/test_reconcile_vanished.py:378-387`) ist eine Quelltext-Sonde auf die alte Reihenfolge und muss durch eine neue Sonde ersetzt werden (Guard vor Aufruf, Aufruf unabhängig vom Walk). Die Fakes `_Queue.stats()` liefern immer `scheduled=0` (Z. 67-68); für die busy-Fälle braucht es einen konfigurierbaren `QueueStats` (`crawling=True`, `scheduled>=quiet_max`, `ok=False`).

### Befund 2 (D-43-05): Gelöschte Home-Speicher sind gone

- Container fragt mit allen abwesenden IDs (`reconcile.py:933-942`), in Bändern zu `GONE_LOOKUP_BAND` (`files.py:357-390`).
- PHP-Route `GET /storages/gone` (`ReconcileController.php:153-200`) ruft `classifyAbsent`; diese liest `numeric_id` aus `oc_storages` und erklärt jede gefragte ID ohne Zeile zu gone (`StorageService.php:443-466`). [VERIFIED: Code]
- mbozems 215/216/221/226/231 haben laut seiner Tabelle keine `oc_storages`-Zeile, also gone, also sofort Löschaufträge im ersten Sweep nach dem Update. Kein Befund, Erwartung des Owners erfüllt. [VERIFIED: Code plus Melderdaten]
- Die 8 alten `//Daten`-Speicher (Nutzer deaktiviert oder umbenannt) haben noch `oc_storages`-Zeilen und keinen abgeschalteten Provider: Stempel, Entfernen 30 Tage nach dem ersten Sweep (D-43-04).
- Löschaufträge werden in der PHP-Queue vor content/ocr abgeholt (`QueueMapper::KINDS` Reihenfolge acl, delete, metadata, content, ocr, embed; `QueueMapper.php:75-81`, Priorität "in der Abfolge der claimBatch-Aufrufe", Z. 334-337). "Sofort" gilt also auch bei vollem OCR-Rückstau. [VERIFIED: Code]
- Randnotiz (LOW): Zeilen mit `storage_id <= 0` würden als abwesend gestempelt, weil `classifyAbsent` IDs ≤ 0 verwirft (Z. 425-428), und nach 30 Tagen gelöscht. Seit dem WR-01-Fix (`QueueService.php:842-857`) entstehen keine solchen Zeilen mehr; mbozems Tabelle zeigt keine. Empfehlung: `absent` im Sweep auf IDs > 0 filtern, ein Test dazu.

### Befund 3: Datenweg der Abdeckungszahl heute (1.6.2)

1. `AdminViewService::overview` (`AdminViewService.php:645-690`): Mountliste über `StorageService::getMounts()`, Gruppen über `countingKeyGroups($mountedStorageIds)` nur bei `indexExternalStorage()`, dann `ScanStatsService::totals($mounted, $groups)`.
2. `ScanStatsService::totals` (`ScanStatsService.php:394-438`) liest pro eingebundenem Speicher die Zähler aus `oc_findling_scan_stats`; `leftOutMembers` (Z. 451-506) wählt je Gruppe das Mitglied mit den meisten `files_seen`, alle anderen eingebundenen Mitglieder kommen nach `leftOutStorageIds`; `grouped` summiert ohne sie.
3. `leaveOutParameters` (Z. 2206-2225): Komma-Liste, höchstens `LEAVE_OUT_MAX_IDS` und `LEAVE_OUT_MAX_LENGTH`, sonst kein Parameter.
4. Container `GET /status?leaveOut=` (`status.py:1032-1055`): `indexedLeftOut` = `indexed_in_storages` (`repo.py:1686-1702`, lebende indexierte Zeilen pro Speicher-Band), `embeddedLeftOut` synchron bis 100.000, darüber Hintergrund-Thread mit Cache (`status.py:837-974`).
5. `figures` (`AdminViewService.php:2293-2333`): Zähler = `backend.indexed - indexedLeftOut`; `backend.indexed` ist `Store.counts()['indexed']` (`status.py:738`), und `counts()` filtert `deleted_at` NICHT (`repo.py:1070-1080`, Tombstone setzt nur `deleted_at`, `repo.py:572-574`). Nenner = grouped `filesSeen - overCap - excluded - refused`.
6. `coverage` (Z. 2031-2120) und `coverageShare` (Z. 2360-2375): abgerundet, unter 100 gehalten, solange etwas fehlt, null bei `counted > indexable`.

**Warum der Zähler falsch ist:** Abzug pro Zeile der ausgelassenen Mitglieder; Dokumente, die mehrfach in behaltenen Speichern liegen, bleiben mehrfach; Dokumente nur in ausgelassenen Mitgliedern fallen ganz heraus; Zeilen nicht eingebundener Speicher und Tombstones bleiben drin. Das sind vier unabhängige Abweichungen, nicht eine.

### Pattern 2: Zählung pro Dokument (neuer Vertrag)

**Dokumentschlüssel:** (Gruppenindex, `files.path`) für Zeilen eingebundener Gruppenmitglieder; (Speicher-ID, `files.path`) für alle anderen eingebundenen Speicher. `path` ist der Pfad relativ zum Nutzerordner des Lesers (`QueueService.php:914`), Leser ist der erste Nutzer, der die Datei lesen kann (`readerOf`, `QueueService.php:987-1010`). Für einen Speicher pro Nutzer ist das der Nutzer selbst und der Einhängepunkt der Konfiguration ist für alle gleich, also gleiche Datei, gleicher Pfad. [VERIFIED: Code]

**Grenzfälle des Schlüssels (dokumentieren, nicht lösen):** (a) zwei Speicherkonfigurationen mit gleichem Host/Share/Root, aber verschiedenem Einhängepunkt; (b) ein Nutzer teilt einen Ordner seines SMB-Mounts per Nextcloud-Freigabe, und der Empfänger sortiert alphabetisch vor dem Eigentümer und wird Leser. Beides erzeugt Doppelzählung im Zähler (Richtung "zu hoch"), die Klammer aus Pattern 3 hält die Quote trotzdem ≤ 100 %. Ein Schlüssel auf dem internen Pfad wäre robuster, verlangt aber eine neue Spalte und eine Nachbefüllung von 190.000 Zeilen; nicht für 1.6.3. [ASSUMED: Häufigkeit der Grenzfälle]

**Mountmenge:** D-43-07 verlangt, dass Zeilen nicht eingebundener Speicher nicht zählen. Der Container kennt die aktuelle Mountmenge nicht (nur die des letzten Sweeps). Empfehlung: PHP schickt die Menge mit, dieselbe, die auch den Nenner bildet (`$mountedStorageIds`, Z. 655-658). Weil diese Liste auf großen Instanzen (Tausende Home-Speicher) die 8000 Zeichen von `LEAVE_OUT_MAX_LENGTH` sprengt, geht sie als JSON-Body:

- **Neue Container-Route** `POST /coverage`, `access_level` ADMIN, in `backend/appinfo/info.xml` deklariert (HaRP gleicht Routen mit `re.match` ab, `info.xml:330-336`; Muster `/probe`, Z. 397-403).
- **Body:** `{"mounted": [int, ...], "groups": [[int, ...], ...]}`. Grenzen (Vorschlag): `mounted` ≤ 50.000 IDs, `groups` ≤ 1000 Mitglieder gesamt (wie `LEAVE_OUT_MAX_IDS`), jede ID kanonische positive Ganzzahl ≤ 18 Stellen, Gruppen disjunkt, jedes Mitglied in `mounted`; sonst 422 vor jeder Abfrage (pydantic-Modell mit `max_length`, wie T-39-02).
- **Antwort:** `{"documents": int|null, "embeddedDocuments": int|null, "judgedDocuments": int|null, "counting": bool}`. Nur Zahlen (T-04-06, T-39-04).
- **PHP:** `adminSend('/coverage', ...)` (`ExAppService.php:754-758`, liefert `kind` ok/unreachable/missing). `missing` (404, Container 1.6.2) heißt: alter Weg über `leaveOut` wie in 1.6.2. Der Container 1.6.3 beantwortet `leaveOut` auf `/status` weiter, für eine Companion 1.6.2 (Update-Reihenfolge).

**SQL (read-only, eine Verbindung wie `embedded_in_storages`, `repo.py:2001-2042`):**

```sql
-- ?1 = JSON der Gruppen, ?2 = JSON der Mountmenge
WITH member(storage_id, grp) AS MATERIALIZED (
  SELECT CAST(m.value AS INTEGER), CAST(g.key AS INTEGER)
    FROM json_each(?1) g, json_each(g.value) m),
mounted(storage_id) AS MATERIALIZED (
  SELECT CAST(value AS INTEGER) FROM json_each(?2))
SELECT
  (SELECT COUNT(*) FROM mounted s CROSS JOIN files f INDEXED BY files_storage
     ON f.storage_id = s.storage_id
    WHERE f.state = 'indexed' AND f.deleted_at IS NULL
      AND s.storage_id NOT IN (SELECT storage_id FROM member))
+ (SELECT COUNT(*) FROM (SELECT DISTINCT m.grp, f.path
     FROM member m CROSS JOIN files f INDEXED BY files_storage ON f.storage_id = m.storage_id
    WHERE f.state = 'indexed' AND f.deleted_at IS NULL));
```

`embeddedDocuments`: gleiche Form mit `AND EXISTS (SELECT 1 FROM vec.chunks c WHERE c.file_id = f.file_id)` über die angehängte Vektor-DB (Muster `_EMBEDDED_IN_STORAGES_SQL`, `repo.py:459-463`). `judgedDocuments`: gleiche Form ohne `state = 'indexed'`, aber mit Ausschluss der Urteile, die der Nenner selbst abzieht oder die kein Dokument mehr sind (Pattern 3).

**Kosten (gemessen):** 188.600 Zeilen, 22 Gruppenmitglieder, 165.000 gruppierte Zeilen, Pfade ~80 Zeichen, lokal (Windows-Laptop, SQLite 3.50.4): CTE mit `json_each` und Plan über `files_state` 1,1 bis 1,8 s; mit `MATERIALIZED` und `INDEXED BY files_storage` 0,29 bis 0,32 s (Plan: `SEARCH f USING INDEX files_storage (storage_id=?)`, `USE TEMP B-TREE FOR DISTINCT`). Ein partieller Index `(storage_id, path) WHERE state='indexed' AND deleted_at IS NULL` brachte nichts (Planer wählte ihn nicht). Kein neuer Index. [VERIFIED: Benchmark in dieser Session] Die DISTINCT-Temp-B-Baum-Größe liegt bei ~165.000 Schlüsseln, RAM-unkritisch; `temp_store` bleibt Standard.

**Hintergrund und Cache (Muster 1.6.2):** synchron bis zu einer Schwelle lebender Zeilen in `mounted` (Vorschlag 100.000, wie `LEFT_OUT_EMBEDDED_SYNC_CEILING`), darüber Single-Flight-Thread, Cache-Schlüssel = sha256 der kanonischen Anfrage (sortierte IDs), Stock-Identität aus (Pfad, st_dev, st_ino) von state.db UND vectors.db, TTL 300 s ab Ende der Zählung, höchstens 4 Schlüssel (`status.py:160-181`, `_cached_left_out` Z. 874-894). Vor dem ersten Ergebnis antwortet der Container `counting: true` mit null-Feldern; die Seite zeigt dann den Satz "wird gezählt" statt einer alten Zahl (nicht wie in 1.6.2 stillschweigend die 1.5-Zahl).

**Instanzen ohne Gruppen:** Empfehlung, den neuen Vertrag immer zu nutzen, wenn der Container ihn kennt. Dann gilt D-43-07 überall, und die Tombstones fallen auch dort aus dem Zähler.

### Pattern 3 (D-43-09): Nenner als Untergrenze der Vereinigung

**Messen Zähler und Nenner dieselbe Menge?** Nein, nicht allgemein. Nenner je Gruppe = indexierbare Dateien des größten Mitglieds R; Zähler je Gruppe = indexierte Dokumente der Vereinigung aller Mitglieder. Gleichheit nur, wenn R alle anderen umfasst (typisch: Administrator-Konto sieht alles). mbozems Archiv (28.303 bis 112.053) schließt das nicht aus. Messung A6 aus Phase 39 zeigt, dass SMB gesperrte Dateien trotzdem listet (`39-04-SUMMARY.md:39`); unterschiedliche `files_seen` entstehen also eher über Ordner, die ein Nutzer nicht betreten darf. [VERIFIED: Code; ASSUMED: Ursache der Sichtunterschiede bei mbozem]

**Kann die Quote über 100 % gehen?** Angezeigt nie: `coverageShare` liefert null bei `counted > indexable`, die Seite zeigt dann den Satz "wird neu gezählt" (`admin.php:483`). Das wäre in diesem Fall eine falsche Aussage, und es gäbe gar keine Quote. Unterhalb von 100 % kann die Quote zu hoch sein, ohne dass man es sieht.

**Vereinigung im Nenner, echt:** braucht pro Gruppe die Zahl der verschiedenen Pfade über die Dateilisten aller Mitglieder mit den Crawl-Regeln (Typfilter, verschlüsselt, Größe, Ausschlüsse). `files_seen` ist nur ein Zähler pro Speicher (`ScanStatsService::add`, Z. 166-182), eine Vereinigung lässt sich daraus nicht bilden. Machbar wäre ein Hintergrundjob mit `COUNT(DISTINCT path_hash)` über `oc_filecache` der Mitglieder (bei mbozem ~1,3 Mio. Zeilen, auf MySQL Sekunden, [ASSUMED]). Das wäre aber eine zweite Implementierung der Crawl-Regeln, genau das, wovor `coverageShare` und `figures` warnen (zwei Rechnungen driften). Für 1.6.3 nicht empfohlen.

**Empfehlung, Untergrenze aus dem Container:** `judgedDocuments` = distinct Dokumentschlüssel über lebende Zeilen der eingebundenen Speicher mit beliebigem Urteil, außer den Gründen, die nicht zur Nennermenge gehören: `skipped/mime_not_allowed` (zieht der Nenner als refused ab), `skipped/excluded` (Ausschlussregel, zieht der Nenner als excluded ab), `skipped/gone` (kein Dokument mehr). `too_large` bleibt drin: die PHP-Größengrenze wird PHP-seitig als Urteil festgehalten (`StorageCrawlJob.php:324`, `FileEventListener.php:481`) und erreicht den Container nicht, der Container-Grund `too_large` kommt aus `archive_limit`/`blocked_malicious` (`nc/queue.py:180-182`) und steht im Nenner. PHP rechnet dann:

```
Nenner = max(gruppierter Nenner aus figures(), judgedDocuments)
Zähler = documents
```

Eigenschaften: Zähler ≤ judgedDocuments (jede indexierte Zeile ist geurteilt) ≤ Nenner, also nie über 100 %, also `coverageShare` liefert immer eine Zahl, sobald ein Nenner da ist. Bei leerer Warteschlange und fertigem Crawl hat jede Datei jedes Mitglieds ein Urteil, judgedDocuments ist dann die Vereinigung der indexierbaren Dokumente, und die Quote zeigt die tatsächliche Abdeckung (die Ursprungsbeschwerde). Während des Crawls bleibt der PHP-Nenner maßgeblich (größer), und `provisional` ist ohnehin gesetzt. Für mbozem: PHP-Nenner ~247.000, judgedDocuments deutlich kleiner (43.602 indexiert plus die geurteilten übrigen), also Nenner 247.123 und ~18 %, wie in D-43-10 erwartet. Kosten: eine dritte Zählung derselben Form, ~0,3 s. Abweichung pro Gruppe statt global wäre während des Crawls genauer, verlangt aber per-Gruppe-Nenner aus PHP (refused pro Speicher). Global reicht für die Invariante. [VERIFIED: Code-Logik; Rechenbeispiel aus Melderdaten]

Offen für die Planung: Dateien, die PHP selbst aufgibt (`failed(repeatedly_stuck)`) erreichen den Container nicht; stehen sie im PHP-Nenner, bleibt eine kleine Lücke, die echt ist (sie sind nicht durchsuchbar).

### Pattern 4 (D-43-06): Einmaliger Hinweis

- **Zustand:** neuer AppConfig-Key in `SettingsService`, Muster `KEY_RULES_CHANGED_AT` (`SettingsService.php:224, 338-360`), Vorschlag `coverage_per_document_hint` (int 0/1).
- **Setzen:** neue Migration `Version001603Date2026111X000000::postSchemaChange` (Muster `Version001600Date20261028000000.php`, idempotent). Nur auf Bestandsinstanzen: Flag nur, wenn `oc_findling_scan_stats` mindestens eine Zeile hat (es gab also schon eine Zahl). Ob `installed_version` in `postSchemaChange` auf Frischinstallationen leer ist, ist nicht geprüft [ASSUMED], daher die Tabellenprüfung als Signal.
- **Löschen:** in `overview()`, sobald `/coverage` eine vollständige Antwort liefert (`counting=false`, `documents` und `judgedDocuments` nicht null). Ein Container 1.6.2 löscht das Flag nie, korrekt, weil dort noch die alte Zählung gilt.
- **Anzeige:** `<p class="settings-hint" id="findling-coverage-per-document" hidden>` neben der Abdeckungszahl in `php/templates/admin.php` (Muster Z. 483-501), Umschalten in `php/js/admin.js` wie `findling-coverage-rules-pending`, Feld `coverage.perDocumentHint` im Overview-JSON.
- **i18n:** englischer Quelltext im Template; Übersetzungen in allen acht Katalogen `php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{js,json}` (der 1.6.2-Satz zum Regelwechsel steht in allen acht), `test_admin_ui_contract.py` prüft Vollständigkeit; Glossare `docs/l10n-{french,italian,spanish,dutch,portuguese}.md` ergänzen. Die deploy-harp-Strecke vergleicht den installierten de-Katalog zeichengleich (`deploy-harp.yml:6795-6803`).
- **Entwurf für die Owner-Runde (vor Umsetzung zeigen):**
  - DE: "Ab Version 1.6.3 zählt jedes Dokument einmal, auch wenn eine Freigabe für jeden Nutzer einzeln eingebunden ist. Die Zahl kann deshalb niedriger sein als vorher."
  - EN: "Since version 1.6.3, every document counts once, even when a share is mounted separately for each user. The figure can therefore be lower than before."
  - FR: "Depuis la version 1.6.3, chaque document compte une seule fois, même si un partage est monté séparément pour chaque utilisateur. Le chiffre peut donc être plus bas qu'avant."

### Anti-Patterns to Avoid
- **`_is_due` als Sweep-Fälligkeit:** auf blockierten Instanzen dauernd wahr, ergibt Sweep alle 5 Minuten.
- **Sweep-Stempel auch bei abgebrochenem Sweep setzen:** dann warten verbleibende gone-Speicher einen ganzen Takt.
- **Mountmenge aus `vanished_storages` ableiten statt von PHP:** hinkt bis zu 48 h hinterher, fehlt bei ausgeschaltetem Reconcile, und gone-Speicher verlieren ihren Stempel in `forget_storage` (`repo.py:1560-1570`), bevor der Poller sie begräbt.
- **`Store.counts()['indexed']` als Zähler:** enthält Tombstones.
- **Zählung pro Gruppe als eigene Abfrage pro Gruppe ohne `INDEXED BY files_storage`:** Planer nimmt `files_state` und scannt pro Gruppe alle indexierten Zeilen (gemessen 0,15 bis 0,2 s je Gruppe, linear in der Gruppenzahl).
- **Pfade, Hosts, Shares oder Nutzer in Logzeilen oder Antwort:** nur Zähler und IDs (T-36-17, T-39-01).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hintergrundzählung mit Cache | neuer Thread-/Cache-Mechanismus | Muster `_cached_left_out`/`_start_left_out_refresh`/`_refresh_left_out` (`status.py:874-974`) | Single-Flight, Stock-Identität, TTL ab Zählende, Neustart nach RuntimeError sind dort schon gelöst und getestet |
| Bänder für Löschaufträge | eigene Schleife | `_hand_over` (`reconcile.py:886-909`), REQUEUE_BAND-Paritätstest | Controller-Limit 256 (CR-01) |
| ID-Listen an SQLite | `IN (?,?,...)` mit Platzhalterbändern für tausende IDs | `json_each(?)` mit einem Parameter | keine Variablengrenze, read-only-tauglich |
| Admin-POST an den Container | eigener Transport | `ExAppService::adminSend` | Fehlerfälle ok/unreachable/missing/busy schon unterscheidbar |
| Abwesenheitsklassifikation | Container-Heuristik | `files.gone_storages` / `classifyAbsent` | nur PHP sieht oc_storages/oc_mounts |

## Laufzeitzustand (neu oder berührt)

| Kategorie | Befund | Aktion |
|----------|--------|--------|
| Stored data (state.db) | neuer Meta-Key `storage_sweep_at`; `vanished_storages` wird auf Bestandsinstanzen erstmals gefüllt (Frist startet ab Update, D-43-04); Tombstones bleiben dauerhaft, `counts()` zählt sie | Code; keine Datenmigration |
| Live service config (PHP) | neuer AppConfig-Key `coverage_per_document_hint` | Migration setzt, overview löscht; Uninstall-Step prüfen, ob er App-Keys räumt |
| OS-registered state | keiner, verifiziert: Container-Tasks werden in `main.py` zur Laufzeit gebaut | keine |
| Secrets/env vars | keine neuen; `FINDLING_RECONCILE_*` unverändert, keine neue Einstellung für die Frist (Test `test_the_grace_is_a_fixed_constant_and_no_setting`) | keine |
| Build artifacts | ExApp-Routen in `backend/appinfo/info.xml` (neue Route `/coverage`) werden erst mit dem ExApp-Update registriert | Upgrade-Strecke prüft die Route nach dem Update |

## Common Pitfalls

### Pitfall 1: Sweep-Fälligkeit aus dem Walk-Zustand
**What goes wrong:** Sweep alle 5 Minuten oder nie. **Why:** `reconcile_state` misst den Walk, nicht den Sweep. **How to avoid:** eigener Meta-Stempel, Test mit Uhr-Fake über zwei Takte im busy-Zustand: genau ein Sweep pro Takt. **Warning signs:** Logzeile "storage sweep" öfter als einmal pro Tag.

### Pitfall 2: Dauer-busy-Instanz hat nie einen Stempel
**What goes wrong:** Erster Sweep wartet auf die konfigurierte Stunde. **How to avoid:** "nie gelaufen = sofort fällig" auch für den Sweep (wie `_is_due`, Z. 1022-1023), dann läuft er beim ersten Tick nach dem Update.

### Pitfall 3: Quote fällt nach Update auf "wird gezählt" statt Zahl
**What goes wrong:** Hintergrundzählung noch nicht fertig. **How to avoid:** synchron unter der Schwelle; darüber eigener Satz plus D-43-06-Hinweis; Test `join_*_refresh` wie 1.6.2.

### Pitfall 4: Gemischte Versionen
**What goes wrong:** Companion 1.6.3 mit Container 1.6.2 (404 auf `/coverage`) oder umgekehrt. **How to avoid:** `missing` fällt auf den 1.6.2-Weg zurück; Container behält `leaveOut`. Upgrade-Strecke in `deploy-harp.yml` deckt beide Reihenfolgen ab (Muster Zusicherung 12, Z. 6755-6850).

### Pitfall 5: Test bildet die Lage nicht ab (Ursache der drei Fehlversuche)
**What goes wrong:** Einzelteile grün, Gesamtzahl falsch. **How to avoid:** D-43-08-Abnahme mit unabhängiger Wahrheit (siehe Validierung), Fixture mit unterschiedlicher Sicht pro Nutzer.

### Pitfall 6: Testbuild mit Endversion
**What goes wrong:** mbozem installiert 1.6.3 als Testbuild; ändert sich danach Code, bietet der Store ihm die echte 1.6.3 nicht an (gleiche Version). **How to avoid:** Testbuild mit kleinerer Version (siehe Release), oder jede Änderung nach dem Test geht als neue Patchversion.

### Pitfall 7: Viele Löschaufträge nach Fristablauf
**What goes wrong:** 31.571 Löschaufträge in einer Runde auf einer vollen Warteschlange. **Why harmless:** delete wird vor content/ocr abgeholt, `_forget` ist idempotent; Bänder zu 200. **Check:** `stats.scheduled` steigt kurz; Quiet-Gate bleibt länger busy, das ist gewollt.

## Code Examples

### Kadenzregel als reine Funktion (Skizze aus `_is_due`, `reconcile.py:1026-1033`)
```python
def _cadence_due(self, last_at: int | None) -> bool:
    if last_at is None:
        return True
    elapsed = self._clock() - last_at
    interval = self._min_interval * 3600.0
    if elapsed < interval:
        return False
    if self._hour_of() == self._hour:
        return True
    return elapsed >= 2 * interval
```

### Single-Flight-Cache (bestehendes Muster, `status.py:874-894`)
```python
key = frozenset(int(storage_id) for storage_id in leave_out)   # neu: sha256 der kanonischen Anfrage
stock = _stock_id(vectors_db)                                  # neu: state.db und vectors.db
with _LEFT_OUT_LOCK:
    cached = _LEFT_OUT_CACHE.get(key)
    if cached is not None and stock is not None and cached[2] == stock:
        if now - cached[1] >= LEFT_OUT_CACHE_SECONDS:
            _start_left_out_refresh(key)
        return cached[0]
    _start_left_out_refresh(key)
    return None
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Nenner alle Speicher | nur eingebundene Speicher | 1.4.2 | Altzeilen raus aus dem Nenner |
| Nenner pro Speicher | Gruppierung per countingKey, kleinste ID | 1.6.0 | Decke 100.000 schaltete Korrektur ab |
| kleinste ID, Vektorzahl synchron | größtes Mitglied, Vektorzahl im Hintergrund | 1.6.2 | Zähler weiter pro Zeile |
| Zähler = indexed (inkl. Tombstones) minus Zeilen ausgelassener Mitglieder | Zähler = distinct Dokumente eingebundener Speicher; Nenner = max(PHP, judgedDocuments) | 1.6.3 (diese Phase) | Zähler und Nenner auf derselben Menge, Quote ≤ 100 % |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Grenzfälle des Pfadschlüssels (verschiedene Einhängepunkte, Freigabe aus SMB-Mount an alphabetisch früheren Nutzer) sind selten | Pattern 2 | Zähler zu hoch; Klammer hält Quote ≤ 100 %, Abweichung bliebe unsichtbar |
| A2 | Unterschiedliche `files_seen` bei mbozem entstehen über Ordnerrechte | Pattern 3 | nur Testtopologie betroffen; Fixture deckt beides ab |
| A3 | `COUNT(DISTINCT path_hash)` über oc_filecache dauert auf MySQL Sekunden | Pattern 3 (verworfen) | keins, Variante nicht empfohlen |
| A4 | `installed_version` ist in `postSchemaChange` bei Frischinstallation leer | Pattern 4 | deshalb Tabellenprüfung als Signal empfohlen |
| A5 | AppAPI `app_api:app:update --info-xml` vergleicht Versionen mit `version_compare`, und `1.6.3-rc.1` < `1.6.3` | Release | Testbuild würde Store-Update blockieren oder sich nicht installieren lassen |
| A6 | Nextcloud akzeptiert eine Companion-Version `1.6.3-rc.1` bei manueller Installation | Release | Testbuild der Companion nur über Versionsnummer der Endversion möglich |
| A7 | Synchrone Schwelle 100.000 lebender Zeilen bleibt auf ARM unter ~1 s | Pattern 2 | Seite lädt langsamer; Schwelle senken |

## Open Questions (RESOLVED)

1. **(RESOLVED) Neue Route `/coverage` oder Erweiterung von `GET /status`?** Entschieden in 43-04: neue Route POST /coverage, `leaveOut` auf /status bleibt für gemischte Versionen.
   - Bekannt: GET-Parameter sind auf 8000 Zeichen begrenzt; die Mountliste großer Instanzen passt nicht hinein; HaRP verlangt deklarierte Routen.
   - Empfehlung: neue POST-Route, Abwägung im Plan dokumentieren. Alternative ohne neue Route: `GET /status?groups=` plus Container-seitiger Ausschluss über `vanished_storages`, mit den oben genannten Lücken.
2. **(RESOLVED) Wie bekommt mbozem den Testbuild technisch?** Entschieden in 43-10 (Branch rc/1.6.3-rc.1, signiertes Archiv per release.yml-Dispatch, Image :<sha>, Test-info.xml, A5/A6-Nachweis auf frischer Instanz und HaRP) und 43-11 (Kommentar mit Owner-Freigabe). Siehe Release-Abschnitt; Owner entscheidet über Version und Weg, A5/A6 vorher in einer frischen Testinstanz (CI oder lokal per Docker) nachweisen.
3. **(RESOLVED) Gibt es auf mbozems Instanz Tombstones mit state indexed?** Für den Fix nicht relevant: 43-03 filtert `deleted_at` in `counts()` und in der neuen Zählung. Seine 190.080 "living indexed" passen zur angezeigten Zahl; ob `counts()` dort mehr zählt, lässt sich nur dort prüfen. Für den Fix egal, der neue Zähler filtert `deleted_at`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv / Python 3.13 | Backend-Tests, Gates | ✓ | uv 0.11.7 | , |
| SQLite mit `json_each` | Zählung | ✓ | 3.50.4 (lokal); Image python:3.13-slim-trixie bringt eigene Version, im Docker-Smoke prüfen | Platzhalterbänder |
| Docker | PHPUnit lokal (`scripts/dev/phpunit_docker.sh`), lokale Testinstanz | ✗ (Daemon läuft nicht) | , | CI `php.yml`, `integration.yml`, `deploy-harp.yml` |
| gh CLI | Issue lesen, Workflow-Dispatch, Release-Belege | ✓ | 2.92.0 | , |

**Missing dependencies with no fallback:** keine.
**Missing dependencies with fallback:** Docker lokal, Ersatz CI.

## Validierung und Testarchitektur

(`workflow.nyquist_validation` ist false; trotzdem Teststrategie für D-43-08, weil der Owner sie verlangt.)

### Ebenen

| Ebene | Harness | Inhalt | Befehl |
|------|---------|--------|--------|
| Container-Einheit Sweep | `backend/tests/test_reconcile_vanished.py`, `test_reconcile.py`, `test_backup_pause.py`, `test_catchup.py` | busy (crawling, scheduled ≥ quiet_max), `stats.ok=False` (kein Sweep), leere/verworfene Liste, genau ein Sweep pro Takt über Uhr-Fake, Stempel nur bei Erfolg, Pause während Sweep, Catch-up-Runde, IDs ≤ 0 | `cd backend && uv run pytest tests/test_reconcile_vanished.py -x` |
| Container-Einheit Zählung | neu `backend/tests/test_coverage_per_document.py` (Muster `test_status_leave_out.py`) | Vertrag, 422-Fälle, Cache, Stock-Wechsel, Hintergrund, nur Zahlen in der Antwort | `uv run pytest tests/test_coverage_per_document.py -x` |
| PHP-Einheit | `php/tests/Unit/AdminViewServiceTest.php`, `ScanStatsServiceTest.php`, `StorageServiceTest.php`, `RouteSecurity` | Nenner-Klammer `max`, Fallback `missing`, Hinweis-Flag setzen/löschen, Body-Aufbau | CI `php.yml` |
| Vertragsparität | neu: gemeinsame JSON-Fixture (Topologie + erwartete Zahlen), gelesen von einem PHP-Test und einem Python-Test | beide Hälften gegen dieselbe Wahrheit | beide Suiten |
| Ende zu Ende (Pflicht D-43-08) | Samba-Harness aus `smb-acl-measure.yml` / `scripts/ci/smb_acl_measure.sh` (Samba auf dem Runner, Nutzer mit eigenen Zugangsdaten, setup-test-nc) in einem neuen Job, oder `integration.yml` Job `reconcile-and-dach` | echte Nextcloud, echte Zählung, Wahrheit unabhängig | CI dispatch |

### Topologie der Abnahme (D-43-08)

- Zwei Samba-Shares `Daten` und `Archiv`, eine Speicherkonfiguration je Share mit Nutzer-Zugangsdaten, drei bis vier Nutzer.
- Unterschiedliche Sicht: Unterordner mit Unix-/Samba-Rechten nur für bestimmte Nutzer betretbar (A6 zeigt, dass Dateisperren allein die Liste nicht verkleinern), so dass `files_seen` je Mitglied verschieden ist und KEIN Mitglied alle anderen umfasst (der Fall aus D-43-09).
- Dieselbe Datei (gleicher Inhalt, gleicher Name) auf `Daten` und `Archiv` (zwei Dokumente, zwei Schlüssel).
- Dokumente nur in einem ausgelassenen Mitglied.
- Ein Nutzer, dem die Konfiguration entzogen wird (Speicher verschwindet aus oc_mounts, oc_storages bleibt: Stempel).
- Ein gelöschter Nutzer mit indexiertem Home (oc_storages-Zeile weg: gone, sofort).
- Quiet-Gate blockiert: `FINDLING_RECONCILE_QUIET_MAX` klein setzen und Warteschlange darüber halten, oder Crawl künstlich unfertig lassen; Grenzen von `_int_from_environment` vorher prüfen (`config.py:1739`).
- Kurzer Takt: `FINDLING_RECONCILE_MIN_INTERVAL_HOURS` auf das Minimum, Stunde passend.

### Unabhängige Wahrheit und Positivkontrolle

- **Nenner-Wahrheit:** aus dem Samba-Dateisystem selbst: `find` pro Share, je Nutzer mit dessen Rechten (`sudo -u <user> find`), Vereinigung pro Share in Shell/`sort -u`, minus Typfilter nach eigener Liste. Nicht über Findling-Code und nicht über `files.path`.
- **Zähler-Wahrheit:** fileids der indexierten lebenden Zeilen aus state.db, aufgelöst über `oc_filecache` (storage, internal path) und `oc_storages.id` (Share per `sed` aus dem ID-String), distinct (Share, interner Pfad), eingeschränkt auf Speicher in `oc_mounts`. Andere Spalte (interner Pfad statt `files.path`), andere Sprache (SQL/Shell statt Python), anderer Schlüsselweg: unabhängig im Sinne der Regel.
- **Positivkontrolle:** ein Lauf, in dem die Prüfung rot werden muss: z. B. eine zusätzliche Datei nur in einem nicht eingebundenen Speicher, deren Mitzählen die erwartete Zahl um 1 verfehlt, oder Vergleich gegen eine absichtlich um 1 verschobene Erwartung; der Job muss genau dort scheitern.
- **Sweep-Abnahme:** nach einem Takt bei blockiertem Gate: Logzeile `storage sweep, absent=... gone=1 ... stamped=1`, `vanished_storages` enthält den entzogenen Speicher, die Zeilen des gelöschten Homes sind Tombstones; Gegenprobe: Logzeile "reconcile round queue_busy" im selben Zeitraum, kein "walked".

### Sampling
- Pro Task: betroffene pytest-Datei; PHP über CI-Lauf des Branches.
- Vor Audit: volle Backend-Suite seriell (RAM), ruff/pyright/vulture, CI grün inkl. neuem E2E-Job.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein (AppAPI-Signatur unverändert) | , |
| V3 Session Management | nein | , |
| V4 Access Control | ja | neue Route `access_level` ADMIN, `#[ExAppRequired]`-Muster PHP-seitig unverändert; RouteSecurity-Allowlist pflegen, falls PHP-Routen sich ändern |
| V5 Input Validation | ja | pydantic-Modell mit Längen- und Mustergrenzen, 422 vor jeder Abfrage (T-39-02); `json_each` nur mit gebundenen Parametern |
| V6 Cryptography | nein (sha256 nur als Cache-Schlüssel, `hashlib`) | , |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Pfad/Host/Nutzer in Antwort oder Log | Information Disclosure | nur Zahlen und Speicher-IDs; Grep-Test wie `test_the_sweep_logs_counters_and_storage_ids_and_never_a_path` |
| Riesige Body-Listen als DoS | Denial of Service | Obergrenzen, Single-Flight, Cache mit max. 4 Schlüsseln |
| Sweep löscht aus leerer/gestörter Liste | Tampering | T-36-13-Bedingung, `stats.ok`, gone nur per PHP-Bestätigung, keine Einstellung für die Frist |
| Cache-Vergiftung durch neue Listen | Tampering | Schlüsselgrenze, Stock-Identität |

## Release-Mechanik (Muster 41-08 bis 41-12)

- **41-08 Bump:** `backend/appinfo/info.xml` (version, image-tag), `php/appinfo/info.xml` (version, derzeit 1.6.2 Z. 179), `CHANGELOG.md`, `docs/store-listing.md`, `deploy-harp.yml` (Upgrade-Strecke weiter ab v1.5.0, neue Zusicherungen: `/coverage` antwortet, Hinweis-Flag gesetzt und nach erster Zählung gelöscht, Migration in oc_migrations), `test_lockstep_versions.py`, `test_store_metadata.py`, `test_upgrade_seed_steps.py`. Neu gegenüber 41: eine PHP-Migration (41 hatte keine).
- **41-09 Audit:** Delta v1.6.2 bis Code-Kopf (seit v1.6.2 nur 4 Zeilen PHP-Code aus Phase 42 plus diese Phase), gefahrene Proben, Fixes ab MEDIUM, `audited_head`.
- **41-10 Owner-Runde:** Vorlage mit Hinweistext DE/EN/FR, Store-Text, Changelog, Issue-Kommentar für den Testbuild; Umlaut-Audit.
- **41-11 Tag und Store:** Owner pusht Tag `v1.6.3` und führt Store-POST aus; `docker.yml` baut `:1.6.3` nur bei Tag `vX.Y.Z` (Z. 634-646), `release.yml` signiert und veröffentlicht.
- **41-12 Issue-Antworten:** ABWEICHUNG für #25: Antwort erst nach Store-Release, Schließen erst nach Bestätigung durch mbozem (D-43-10); 41-12 hatte #25 selbst geschlossen.

### Testbuild für mbozem (D-43-10) vor der Store-Einreichung

- **Backend-Image:** jeder Push auf main baut multi-arch und taggt `ghcr.io/street1983nk/findling_backend:<commit-sha>` und `:dev` (`docker.yml:634`). Der SHA-Tag ist unveränderlich und eignet sich für den Testbuild. Ein `workflow_dispatch` von `docker.yml` auf einem Branch verschiebt `:dev`; das beachten, falls CI `:dev` nutzt.
- **Companion-Archiv:** `release.yml` per `workflow_dispatch` mit `create_release=false` baut, signiert (Guard lässt dispatch zu, Z. 147-175) und lädt Artefakte hoch, ohne Release. Artefakte sind für eingeloggte GitHub-Nutzer herunterladbar und laufen ab (Standard 90 Tage). [ASSUMED: Retention-Einstellung des Repos]
- **Version:** Empfehlung Testbranch mit Version `1.6.3-rc.1` in beiden info.xml (Lockstep-Tests grün halten), damit die spätere Store-1.6.3 als Update erscheint (A5/A6 vorher auf einer frischen Testinstanz nachweisen). Der Tag-Pfad ist davon unberührt, weil `docker.yml` und `release.yml` nur `vX.Y.Z` taggen bzw. veröffentlichen.
- **Installation beim Melder:** Companion: Archiv nach `custom_apps/findling` entpacken, `occ upgrade`; Backend: `occ app_api:app:update findling_backend --info-xml <Test-info.xml mit image-tag=<sha>>` (Option laut Nextcloud-Doku vorhanden) [CITED: docs.nextcloud.com/server/latest/admin_manual/exapps_management/ManagingExApps.html]. Ob `update` ohne höhere Version greift (`--force-update`), vorher prüfen.
- **Kommentar an mbozem:** Claude entwirft, Owner gibt frei; Inhalt: was der Testbuild ändert, wie installieren, welche Zahl er erwarten soll (~18 % bei laufendem Crawl), welche Logzeile den Sweep belegt, Rückweg auf 1.6.2.

## Sources

### Primary (HIGH confidence)
- Code: `backend/src/findling/worker/reconcile.py` (run_once 484-552, _sweep_vanished 912-971, _quiet 974-1001, _is_due 1003-1033), `backend/src/findling/store/repo.py` (counts 1070-1080, tombstone 1164-1191, Sweep-Helfer 1523-1595, indexed_in_storages 1686-1702, embedded_in_storages 2001-2042), `backend/src/findling/store/schema.sql`, `backend/src/findling/api/status.py` (149-181, 725-750, 837-1055), `backend/src/findling/nc/files.py` (296-390)
- Code: `php/lib/Service/StorageService.php` (classifyAbsent 422-479, countingKeyGroups 482-535, countingKey 546-578), `php/lib/Service/ScanStatsService.php` (totals 394-438, leftOutMembers 451-506), `php/lib/Service/AdminViewService.php` (overview 645-690, coverage 2031-2120, leaveOutParameters 2206-2225, leftOutCounts 2239-2252, figures 2293-2333, coverageShare 2360-2375), `php/lib/Service/QueueService.php` (842-857, 914, 987-1010), `php/lib/Db/QueueMapper.php` (75-81, 334-355), `php/lib/Controller/ReconcileController.php` (153-200), `php/lib/Service/ExAppService.php` (676-758, 882-896)
- Workflows: `.github/workflows/docker.yml`, `release.yml`, `smb-acl-measure.yml`, `deploy-harp.yml`, `php.yml`
- GitHub-Issue #25 komplett (`gh issue view 25 --comments`)
- Benchmark in dieser Session (Skripte unter dem Scratchpad, 188.600 Zeilen)

### Secondary (MEDIUM confidence)
- [Nextcloud Admin Manual, Managing ExApps](https://docs.nextcloud.com/server/latest/admin_manual/exapps_management/ManagingExApps.html): `app_api:app:update [--info-xml] [--force-update]`, `app_api:app:register --info-xml`

### Tertiary (LOW confidence)
- Verhalten von `version_compare` bei rc-Versionen in Nextcloud/AppAPI (A5, A6), nicht in dieser Session geprüft

## Metadata

**Confidence breakdown:**
- Sweep-Einhängung: HIGH, vollständig am Code belegt
- D-43-05: HIGH, Code plus Melderdaten
- Zählvertrag und Kosten: HIGH für Datenweg und Messung, MEDIUM für Routenwahl
- Nenner-Empfehlung D-43-09: MEDIUM, logisch belegt, braucht die E2E-Abnahme
- Testbuild-Übergabe: MEDIUM bis LOW, Versionsvergleich ungeprüft

**Research date:** 2026-11-07
**Valid until:** 2026-12-07 (Codebasis stabil; bei Änderungen an reconcile.py oder status.py neu prüfen)
