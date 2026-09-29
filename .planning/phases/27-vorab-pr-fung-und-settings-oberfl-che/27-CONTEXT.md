# Phase 27: Vorab-Prüfung und Settings-Oberfläche - Context

**Gathered:** 2026-09-29
**Status:** Ready for planning (vorher ui-phase 27: UI-SPEC vor dem Plan-Schnitt, Projektkonvention)

<domain>
## Phase Boundary

Die Adminseite bekommt ihre erste echte Settings-Fläche (UI-01): ein Auswahlfeld mit genau den drei Profilen (Sparsam, Standard, Leistung), darunter bei Standard/Leistung ein Häkchen für das genauere Suchmodell (fp32), und eine Hinweisfläche mit erkannten Kernen/Speicher, vorgeschlagenem Profil, Verdikt der letzten Probe und den Knöpfen "Übernehmen und prüfen" und "Bei Sparsam bleiben". "Übernehmen und prüfen" fährt im Container eine echte Probe (PRUEF-01: N-Slot-Probe am OCR-Pfad mit mitgelieferter synthetischer Scanseite, RAM-Rechnung mit gemessenen Slot-Kosten, bei fp32-Wunsch Modell-Probe) und liefert "passt", "passt knapp" oder "passt nicht" mit benannter Ursache; gespeichert wird nur bei "passt". Probe- und Schreibroute sind nur für Admins erreichbar (access_level ADMIN, Test); alle neuen Texte stehen in allen acht Sprachkatalogen (16 Dateien) im Gleichstand.

Nicht in dieser Phase: RAM-Messung je Profilstufe auf echter Hardware (Phase 28), Launch-Härtung und Release 1.4.0 (Phase 29), ein Erweitert-Bereich (ADM-04 bleibt), neue Profile oder Zwischenstufen.

</domain>

<decisions>
## Implementation Decisions

Vorentscheide, die hier tragen und NICHT neu verhandelt werden: D-24-01 (Weg B: PHP speichert in appconfig, Container liest je Runde), D-24-02 (Lesefehler = letztes bekanntes Profil, sonst Sparsam), D-24-03 (Anteile, Obergrenzen Standard 4 / Leistung 16 Slots), D-24-06 (Vorschlags-Schwellen 6 GB/3 Kerne bzw. 12 GB/6 Kerne, nur Vorschlag), D-24-07 (gespeichertes Profil bleibt bei Schrumpfung, gewählt vs. wirksam sichtbar), D-25-01/03/04/05/09/10/14 (fp32 nur in Standard/Leistung wählbar, nie automatischer Wechsel, Download nur auf ausdrückliche Admin-Aktion aus dem eigenen GitHub-Release mit festem sha256, Rückweg zu int8 löscht die Datei, Offline-Ablage), D-26-01/04 (Wächter senkt nur die wirksame Stufe, Rückweg nur durch Admin-Aktion mit Bestätigungs-Token), ADM-04 (kein Erweitert-Bereich).

### fp32 auf der Fläche
- **D-27-01 (Owner, 29.09.2026):** Die Genauigkeit erscheint als Häkchen unter dem Profil-Auswahlfeld ("Genaueres Suchmodell (fp32)", Arbeitstext), sichtbar nur bei Standard und Leistung. Die Probe testet Profil und Genauigkeit zusammen; gespeichert werden beide Schlüssel zusammen (Profil-Schlüssel und `model_precision`, D-25-02). Das ist ein Auswahlfeld plus eine Option, ADM-04 gilt als gewahrt.
- **D-27-02 (Owner, 29.09.2026):** Die fp32-Datei wird IN der Probe beschafft: Der Klick auf "Übernehmen und prüfen" mit gesetztem Häkchen ist die ausdrückliche Admin-Aktion im Sinne von D-25-05/D-25-14. Die Probe lädt die Datei (oder nimmt eine selbst abgelegte, D-25-06), prüft den Digest und misst das geladene Modell. Bei "passt" bleibt die Datei liegen und die Neueinbettung startet; bei "passt knapp"/"passt nicht" wird die Datei gelöscht und int8 bleibt aktiv (Platte frei, kein halber Zustand).
- **D-27-03 (Owner, 29.09.2026):** Setzen oder Entfernen des Häkchens zeigt eine Hinweiszeile mit Dokumentzahl und geschätzter Dauer der Neueinbettung (sinngemäß "Neueinbettung von 29.100 Dokumenten, geschätzt ca. 5 h; die Volltextsuche bleibt voll verfügbar"). Kein Bestätigungsdialog. Die Schätzung ist als Schätzung beschriftet (gleiche Linie wie die bestehende Dauer-Beschriftung in docs/admin-page.md).

### Probe-Ablauf
- **D-27-04 (Owner, 29.09.2026):** Die Probe läuft im Hintergrund: Der Klick startet sie, die Seite fragt in kurzen Abständen nach und zeigt eine Fortschrittszeile (sinngemäß "Probe läuft: Modell laden ... OCR mit 4 Slots ..."). Das Ergebnis (Verdikt, Ursache, Zeitpunkt) ist nach einem Neuladen der Seite noch sichtbar. Kein synchroner Request bis zum Verdikt (Proxy-/Gateway-Timeouts, fp32-Download).
- **D-27-05 (Owner, 29.09.2026):** Während der Probe pausiert die Indexierung: Der Poller nimmt keine neue Staffel, eine laufende Staffel endet sauber (Zusagen aus Phase 26 halten), danach läuft alles weiter wie vorher. Die Probe misst die Box ohne mitlaufende Indexlast und kann zusammen mit ihr kein OOM auslösen (SC3).
- **D-27-06 (Owner, 29.09.2026):** Zeitdeckel zweigeteilt: Messteil (OCR und Modellprobe) fester Deckel in der Größenordnung 120 s; der fp32-Download einen eigenen Deckel in der Größenordnung 10 min mit eigenem Verdikt ("Download zu langsam" o. ä.). Endgültige Werte legt die Research fest. Höchstens eine Probe gleichzeitig (SC3).
- **D-27-07 (Owner, 29.09.2026):** Die N-Slot-Probe fährt zweistufig: erst EIN Slot auf der synthetischen Scanseite, das misst die echten Slot-Kosten auf DIESER Box; mit diesem Messwert rechnet die Probe vorab gegen die Speichergrenze, ob das Ziel-N passt; nur wenn ja, fährt sie N Slots gleichzeitig. Keine Leiter 1/2/.../N (sprengt den Zeitdeckel).

### Verdikt und Folgen
- **D-27-08 (Owner, 29.09.2026):** "passt knapp" heißt: Die Rechnung geht auf, aber die Reserve liegt unter einem Sicherheitsabstand (Wert legt die Research fest, gegen Wächter-Schwellen aus Phase 26 abgestimmt). Folge: NICHT speichern; die Seite nennt Ursache und bietet an, die nächstniedrigere Stufe zu prüfen. Gespeichert wird ausschließlich bei "passt" (Anforderung PRUEF-01). Kein "Trotzdem übernehmen".
- **D-27-09 (Owner, 29.09.2026):** Wechsel auf Sparsam und der Wechsel fp32 zu int8 speichern sofort ohne Probe (weniger Last kann nicht "nicht passen"; das ist auch der Rückweg bei "passt nicht"). fp32 zu int8 zeigt die Reindex-Hinweiszeile (D-27-03). Leistung zu Standard ist KEIN sicherer Abwärtsweg und läuft durch die Probe.
- **D-27-10 (Owner, 29.09.2026):** Ein Verdikt verfällt nicht. Es gilt für den Moment des Speicherns; spätere Hardware-Änderungen deckt D-24-07 (wirksame Stufe folgt), Druck deckt der Wächter. Die Seite zeigt Datum und Ergebnis der letzten Probe.

### Texte und Rückwege
- **D-27-11 (Owner, 29.09.2026):** Der zweite Knopf heißt "Bei Sparsam bleiben" statt "Beim sicheren Standard bleiben" (Roadmap SC1): Kollision mit dem Profilnamen "Standard". Der Wortlaut in ROADMAP.md SC1 wird beim Plan-Schnitt angepasst, der Sinn bleibt.
- **D-27-12 (Owner, 29.09.2026):** Nach einer Wächter-Absenkung nennt die Hinweisfläche beide Stufen und die Ursache und bietet "Erneut prüfen" an: Der Knopf fährt die Probe für das GEWÄHLTE Profil; bei "passt" gilt das als Admin-Bestätigung im Sinne von D-26-04 (Bestätigungs-Token über die Profil-Route). Die bisherige occ-Befehlszeile mit Token verschwindet von der Seite.
- **D-27-13 (Owner, 29.09.2026):** occ bleibt als dokumentierter zweiter Schreibweg für Profil und Genauigkeit (Automatisierung, kopflose Boxen). Die Doku sagt ausdrücklich, dass occ die Probe überspringt und dann nur der Wächter absichert; die UI ist der empfohlene Weg.
- **D-27-14 (Owner, 29.09.2026):** Umgebungsvariablen überstimmen nur Einzelwerte (`FINDLING_OCR_MAX_PAGES`, `FINDLING_OCR_DPI`, `FINDLING_EMBED_BATCH_SIZE`, `FINDLING_WRITER_HEAP_BYTES`, `profile.py:276`), nie das Profil oder die Slots. Das Auswahlfeld bleibt frei; die Hinweisfläche nennt überstimmte Werte samt Variable (sinngemäß "OCR-Auflösung 400 dpi durch FINDLING_OCR_DPI"). Die Probe rechnet und misst mit genau diesen wirksamen Werten (DPI und Seitenzahl treiben die Slot-Kosten).

### Claude's Discretion
- Ursachenliste bei "passt nicht"/"passt knapp" (Speicher, Slot-Kosten, Download, Digest, Zeitdeckel, Probe läuft schon, Container nicht erreichbar) als geschlossene Menge; Research legt fest, Anzeigewörter nur aus PHP-Katalogen (T-26-16-Muster).
- Form der Probe-Routen (Start, Stand abfragen) im Container und auf PHP-Seite, Speicherort des Probe-Ergebnisses (state.db oder appconfig), Poll-Intervall, Mechanik der Indexierungs-Pause im Poller.
- Sicherheitsabstand für "passt knapp", genaue Zeitdeckel, Herkunft und Größe der mitgelieferten synthetischen Scanseite (Import-Hygiene und Sandbox-Härtung aus Phase 26 gelten für die Probe-Kinder unverändert).
- Genaue Katalogtexte (Code Englisch; alle neuen Texte in allen acht Katalogen im Gleichstand, Katalog-Gates grün), Platzierung der Fläche auf der bestehenden Adminseite (UI-SPEC legt fest).
- Neues Bedrohungsregister für die Schreibroute: AR-24-02 verfällt mit dieser Phase (erste Schreibroute für das Profil); saveProfile als ADMIN-Frontpage-Route mit CSRF, geschlossene Wertemengen für Profil und Genauigkeit, Probe-Route access_level ADMIN im Container.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phasenrahmen
- `.planning/ROADMAP.md` Phase 27 : Goal, Success Criteria 1-4, UI hint (ui-phase-Gate)
- `.planning/REQUIREMENTS.md` : PRUEF-01, UI-01 (plus Out-of-Scope-Liste)

### Vorentscheide
- `.planning/phases/24-owner-tor-profil-ger-st-und-marken-reparatur/24-CONTEXT.md` : D-24-01..08 (Profilweg, Anteile, Vorschlag, Schrumpfung)
- `.planning/phases/24-owner-tor-profil-ger-st-und-marken-reparatur/24-SECURITY.md` : AR-24-02 (verfällt mit der Schreibroute dieser Phase)
- `.planning/phases/25-einbettungsspur-und-modellwahl/25-CONTEXT.md` : D-25-01..15 (fp32-Wahl, Download, Offline-Weg, Rückweg, Reindex)
- `.planning/phases/26-n-ocr-slots-und-speicherw-chter/26-CONTEXT.md` : D-26-01..16 (Wächter, Rückweg per Token, N Slots, Sandbox-Kinder)
- `.planning/phases/26-n-ocr-slots-und-speicherw-chter/26-SECURITY.md` : T-26-05/07/15/16/17 (Token-Validierung, Profil-Route, Katalog-Gate gegen XSS)
- `.planning/research/BL-F04-vorarbeit-2026-09-25.md` : Slot-Regel 3.1, Hardware-Erkennung 3.3, Security-Abschnitt 8
- `.planning/research/BL-F04-worker-skalierung.md` §6.5 : ADM-04-Grenze

### Bestandscode und Doku
- `docs/admin-page.md` : Aufbau der Seite, "Die vier Schalter", "Keinen Erweitert-Bereich" (ADM-04), Statusroute-Block `profile`
- `docs/profiles.md` : Profile, Owner-Tor, Store-Satz D-24-04
- `php/templates/admin.php` (Wächter-Block ab ~261, occ-Rückwegzeile ~290), `php/js/admin.js`
- `php/lib/Controller/SettingsController.php` (FrontpageRoute-Muster `saveRules`), `php/lib/Controller/ProfileController.php` (heute nur GET, `rejectForeignCaller`)
- `php/lib/Service/AdminViewService.php` (`adminGet('/status', ...)`), `php/lib/Service/ExAppService.php` (Timeouts, proxyRequest)
- `backend/appinfo/info.xml` routes (access_level ADMIN, Muster `^/status$`)
- `backend/src/findling/profile.py` (`resolve`, `_OVERRIDES`, `ProfileSnapshot`), `backend/src/findling/memory_guard.py`, `backend/src/findling/extract/sandbox.py`, `backend/src/findling/worker/poller.py`
- `php/l10n/*.js|*.json` : acht Sprachen, 16 Dateien, Katalog-Gates

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ExAppService::adminGet` + Statusroute ADMIN: der Weg PHP zu Container aus der Admin-Sitzung existiert; die Probe-Routen folgen demselben Muster.
- `SettingsController::saveRules` (POST FrontpageRoute): Vorlage für die neue Profil-Schreibroute (CSRF, Admin-Sitzung).
- `profile.resolve()` liefert Werte samt Quelle (`profile`/`env`): Grundlage für D-27-14 und die Probe-Rechnung.
- `memory_guard.headroom_bytes()` und die Slot-Kosten-Logik aus Phase 26: Grundlage der Vorab-Rechnung (D-27-07).
- Sandbox-Kinder aus Phase 26 (ExtractionWorker, nice, oom_score_adj, RLIMIT_AS): die Probe nutzt dieselben Kinder, keinen neuen Parserpfad.
- fp32-Beschaffung aus Phase 25 (Download, Digest, Offline-Ablage, Löschen): die Probe ruft sie auf, baut sie nicht neu.

### Established Patterns
- Anzeigewörter nur aus PHP-seitigen Maps/Katalogen, Container liefert nur Codes (Katalog-Gate `no_catalogue_value_can_break_the_page`).
- Geschlossene Wertemengen für Profil, Genauigkeit, Stufe, Ursache; Token 32 Kleinbuchstaben-Hex.
- K6: Companion-Änderungen reisen erst mit Release 1.4.0; Container muss mit altem Companion (ohne Schreib- und Probe-Route) weiterlaufen.

### Integration Points
- `worker/poller.py`: Pause-Signal für die Probe (keine neue Staffel, laufende endet sauber).
- `php/templates/admin.php` + `php/js/admin.js`: neue Fläche, Poll der Probe, Hinweiszeilen; occ-Rückwegzeile entfällt (D-27-12).
- `docs/admin-page.md`, `docs/profiles.md`: occ als Weg ohne Probe dokumentieren (D-27-13), neue Fläche beschreiben.

</code_context>

<specifics>
## Specific Ideas

- Hinweisfläche nennt gewählt vs. wirksam mit Ursache (Linie D-24-07/D-26-01) und bei Env-Überstimmung Wert plus Variablenname.
- Reindex-Hinweis mit konkreter Dokumentzahl und beschrifteter Schätzung, Volltextsuche bleibt verfügbar (D-25-07).
- Knopftext "Bei Sparsam bleiben" (D-27-11).

</specifics>

<deferred>
## Deferred Ideas

### Reviewed Todos (not folded)
- Issue #18 Fix-Kandidaten (JPG-Verdikt, HEIF, Download-Größenprüfung): passt nicht zu dieser Phase (Trefferwert 0,2), wartet weiter auf budachsts Antwort und den Slot-Entscheid des Owners.

</deferred>

---

*Phase: 27-vorab-pr-fung-und-settings-oberfl-che*
*Context gathered: 2026-09-29*
