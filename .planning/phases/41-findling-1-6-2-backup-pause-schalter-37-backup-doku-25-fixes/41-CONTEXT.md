# Phase 41: Findling 1.6.2 , Context

**Gathered:** 2026-11-04 (aus Owner-Freigaben, keine neue discuss-Runde)
**Status:** Ready for planning

<domain>
## Phase Boundary

Release 1.6.2 beider Apps (findling PHP-Companion, findling_backend ExApp) mit genau dem Umfang, der in Issue #37 und #25 öffentlich zugesagt ist, plus den vier Nachaudit-Befunden, die 1.6.1 (Security-only, pypdf) nicht mitnahm. Kein neues Feature darüber hinaus.
</domain>

<decisions>
## Implementation Decisions

### Backup-Pause-Schalter (#37, Owner-GO 30.10.2026)
- D-41-01: Zwei Wege, gleiche Wirkung: `occ findling:pause` / `occ findling:resume` (PHP-Companion) und ein Schalter auf der Admin-Seite.
- D-41-02: In der Pause ruhen Indexer, Embedding und Poller (keine neuen Claims, laufender Batch endet sauber oder wird ohne Retry-Gutschrift-Schaden zurückgegeben).
- D-41-03: Beim Eintritt in die Pause: SQLite-WAL checkpointen (TRUNCATE) und Tantivy committen, damit das Volume konsistent kopierbar ist; erst danach meldet der Status "paused" (Backup darf erst dann starten).
- D-41-04: Die Suche läuft in der Pause weiter (lesend).
- D-41-05: Pause-Zustand übersteht einen Neustart von Container und Nextcloud (kein stilles Auto-Resume).
- D-41-06: Zusage im Issue wörtlich: "indexing stops and everything is flushed to disk while search keeps working".

### Backup-Doku (#37)
- D-41-07: Abschnitt Backup in der Doku: Weg A docker stop / Volume sichern / docker start; Weg B Pause-Schalter; Einstellungen liegen in der NC-Datenbank (appconfig), nicht im Volume; Volume ist komplett neu aufbaubar, Backup spart nur Zeit (OCR/Embeddings); Index enthält extrahierten Text unverschlüsselt, Backup behandeln wie Datei-Backup.
- D-41-08: Doku dreisprachig wie die übrigen Nutzer-Dokus (DE zuerst), kurze Faktenliste (Owner-Regel kurze Produkttexte).

### Issue #25 (Owner-GO 29.10.2026)
- D-41-09: embeddedLeftOut nicht mehr bei LEFT_OUT_EMBEDDED_CEILING=100_000 (status.py:153) überspringen; Zählung asynchron im Hintergrund und gecacht (Muster Kandidat F aus Phase 40), damit AdminViewService::leftOutCounts() beide Zahlen bekommt und der Dedup nicht still ausfällt.
- D-41-10: Repräsentant einer Share-Gruppe in ScanStatsService.php:474 = Mitglied mit größtem files_seen statt kleinster finished-ID.
- D-41-11: Testfälle aus dem Issue: indexedLeftOut 113 851; Mitglieder 28k bis 112k je Share; Nenner ~246k statt 178k.

### Nachaudit 1.6.0 (Owner-Entscheid 29.10.2026)
- D-41-12: F-40N-01 bis F-40N-04 aus 40-NACHAUDIT.md beheben; Entwurf 40-07-PLAN.md (untracked, für 1.6.1 geschrieben) ist Vorlage, nicht verbindlich; jeweils Negativtest zuerst (RED).

### Release
- D-41-13: Version 1.6.2 an allen Lockstep-Stellen, CHANGELOG, Upgrade-Strecke ab v1.5.0 (wie 1.6.1), beide Apps gleiche Version.
- D-41-14: Audit Security/Bugs/Performance über das Delta v1.6.1..Kopf, Fixes ab MEDIUM (Vorlage 40-08).
- D-41-15: Eine schlanke Owner-Runde (Release-Notiz, neue nutzersichtbare Texte, Umlaut-Audit) vor dem Tag (Vorlage 40-09); Store-Text nur ändern, wenn nötig.
- D-41-16: Tag, Signatur, Store-Submit (store-submit.yml) und Issue-Antworten (#37, #25) nur nach Owner-Wort; Issue-Antworten erst NACH Store-Release (Dauerregel). Classifier blockt Tag-Push, Merge, Store-POST: Owner führt diese Schritte aus.
- D-41-17: Keine Inhalte verlassen den Server (Findling-Regel 02.11.); kein externer Dienst.

### Owner-Entscheide 04.11.2026 (offene Fragen aus 41-RESEARCH.md)
- D-41-18: Pause-Eintritt wartet, bis der laufende Batch regulär fertig ist (kein Abbruch); Status "pausing" bis dahin, bei OCR bis ~30 min; Doku sagt: Backup erst bei Status "paused".
- D-41-19: Kann das Backend den Pause-Zustand nach einem Neustart nicht lesen (Profil-Route nicht erreichbar), bleibt es angehalten, Status pause "unknown"; sobald lesbar, normaler Ablauf.
- D-41-20: Rebuild stoppt bei Pause-Wunsch zwischen zwei Bändern und setzt nach Resume per Cursor fort.
- D-41-21: PHP-Crawl-Jobs laufen in der Pause weiter (schreiben nur in die NC-Datenbank), das steht in der Doku.

### Claude's Discretion
- Wo der Pause-Zustand gespeichert wird (appconfig der Companion vs. Backend-Datei), solange D-41-05 hält und es genau eine Quelle der Wahrheit gibt.
- Form des Admin-Schalters und Statustext, im Stil der bestehenden Admin-Seite, l10n-Kette wie üblich.
- Ob die embedded-Zählung den bestehenden Fill-Refresh-Mechanismus nutzt oder einen eigenen Job.
</decisions>

<canonical_refs>
## Canonical References

- `.planning/phases/40-haertung-und-store-einreichung-1-6-0/40-NACHAUDIT.md` , F-40N-01..04
- `.planning/phases/40-haertung-und-store-einreichung-1-6-0/40-07-PLAN.md`, `40-08-PLAN.md`, `40-09-PLAN.md` , Entwürfe (1.6.1), Vorlage
- `.planning/phases/40-haertung-und-store-einreichung-1-6-0/40-AUDIT.md`, `40-VERIFICATION.md` , Lehre Lücke SC1 (Audit muss den ganzen Delta abdecken)
- GitHub Issue #37 (budachst, Backup), Issue #25 (mbozem, Abdeckung)
- `backend/src/findling/api/status.py:153` (LEFT_OUT_EMBEDDED_CEILING), Zeilen 437 und 804
- Bestehender Pausenzustand `paused_low_disk` (`backend/src/findling/config.py:285`, `api/resources.py:330`) , Muster für einen weiteren Pausegrund, `php/lib/Service/AdminViewService.php` (leftOutCounts), `php/lib/Service/ScanStatsService.php:474`
- `docs/store-listing.md` , Release-Abschnitte und Belegmuster
</canonical_refs>

<specifics>
## Specific Ideas

- Issue-#37-Antwort beschreibt bereits den Backup-Ablauf; Doku und Pause müssen dazu passen.
</specifics>

<deferred>
## Deferred Ideas

- 1.7: occ findling:backup/restore (Snapshot-Archiv), F-40-06, Tombstones in `indexed`, italienisches Testset, e5-base Opt-in.
</deferred>
