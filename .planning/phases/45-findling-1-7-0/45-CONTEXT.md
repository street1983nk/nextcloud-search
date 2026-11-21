# Phase 45: Findling 1.7.0 - Context

**Gathered:** 2026-11-21
**Status:** Ready for planning
**Source:** discuss-phase mit dem Owner (21.11.2026) plus Owner-Entscheide vom 21.11.2026 zum Milestone v1.7

<domain>
## Phase Boundary

Findling 1.7.0 (findling und findling_backend in gleicher Version) im Store: Ausschluss einzelner externer Speicher neben dem Schalter für externe Speicher (#45), Anzeige freier Ausschluss-Plätze, klare Meldungen bei Platzhalterzeichen, Traditional Chinese aus PR #56 und Locale-Fix aus PR #57, kurze Store-Texte mit Verlagerung der Pflichtinhalte in README/Doku, Launch-Härtung, Volltest DE/EN/FR und Store-Release mit Einzelfreigaben. Neue Fähigkeiten außerhalb dieser Liste gehören nicht in diese Phase.

</domain>

<decisions>
## Implementation Decisions

### Ausschluss je externem Speicher (EXCL-04)
- D-45-01: Unter dem Schalter "Externe Speicher indexieren" steht eine Liste aller vom Admin angelegten externen Speicher (files_external, Admin-Mounts) mit Name bzw. Einhängepunkt und Typ (z. B. SMB); Haken = wird indexiert. Gespeichert wird über die files_external-Konfigurations-ID (oc_external_mounts.mount_id), nicht über den Einhängepunkt, damit Umbenennen den Ausschluss nicht bricht.
- D-45-02: Neu angelegte externe Speicher sind automatisch drin (Opt-out). Gespeichert wird die Liste der AUSGESCHLOSSENEN IDs, nicht der zugelassenen.
- D-45-03: Persönliche externe Speicher, die Nutzer selbst anlegen, erscheinen NICHT einzeln in der Liste; sie folgen weiter nur dem Hauptschalter (Datenschutz, Listenlänge).
- D-45-04: Ist der Hauptschalter aus, ist die Liste ausgegraut bzw. ohne Wirkung; die gespeicherten Ausschlüsse bleiben erhalten und greifen wieder, wenn der Schalter an geht.
- D-45-05: Ein ausgeschlossener Speicher verliert seine Dokumente sofort ohne Gnadenfrist, auf demselben Weg wie heute beim Abschalten des Hauptschalters (StorageService::deselected, reconcile forget_storage, D-36-14). Ein wieder zugelassener Speicher wird beim nächsten regulären Abgleich nachindexiert, kein Sofort-Anstoß und keine eigene Fortschrittsanzeige.
- D-45-06: Gelöschte externe Speicher fallen aus der gespeicherten Ausschlussliste heraus bzw. werden ignoriert, ohne Fehler auf der Admin-Seite.

### Freie Plätze und Meldungen (EXCL-05, EXCL-06)
- D-45-07: Unter der Ordnerliste und unter der Musterliste steht je ein Zähler "Noch N von 64 frei" bzw. "Noch N von 32 frei" (Grenzen aus ExclusionService MAX_PREFIXES und MAX_PATTERNS, nicht im Template hart verdrahtet). Er aktualisiert sich beim Hinzufügen und Entfernen ohne Neuladen; beim letzten freien Platz ein Hinweis.
- D-45-08: Ein * oder ? im Ordnerfeld wird künftig abgelehnt (neuer Fehlercode in ExclusionService::validate, serverseitig und im JS) mit Hinweis aufs Musterfeld, sinngemäß: "Ordner ohne * oder ?. Für Muster wie Archiv* das Feld Ausgeschlossene Muster nutzen." Bereits gespeicherte Ordnereinträge mit * oder ? werden auf der Seite markiert, NICHT still gelöscht oder umgedeutet.
- D-45-09: Die bestehende Meldung no_wildcard im Musterfeld wird geschärft und nennt beide Wege mit Beispiel, sinngemäß: "Dieser Eintrag hat kein * oder ?. Ganze Ordner unter Ausgeschlossene Ordner eintragen, oder ein Muster wie Name* verwenden."
- D-45-10: Alle neuen und geänderten Texte in allen 16 Katalogen plus zh_TW (also 17), Umlaut-Audit inklusive.

### PRs #56 und #57 (KAT-03, KAT-04)
- D-45-11: Beide PRs zuerst prüfen (CI grün, Diff lesen), dem Owner zeigen und je PR erst nach Owner-Okay mergen; Mitwirkende bleiben Autor. Erst danach baut die Ausschluss-UI auf dem gemergten Stand auf (admin.js-Konflikte vermeiden). Der root.lang-Nit, PRODUCT.md und CHANGELOG kommen als eigene Commits dazu.
- D-45-12: Neue Schlüssel im zh_TW-Katalog übersetzen wir selbst; nach dem Store-Release fragt der Owner foolfitz in #53 nach Korrekturen. body_zh wird NICHT selbst gebaut (wartet auf foolfitz' eigenen PR).

### Store-Texte (STORE-03, STORE-04)
- D-45-13: Der Entwurf der kurzen Store-Texte (DE/EN/FR, beide Apps) plus Liste der Verlagerungen kommt KURZ VOR DEM RELEASE, wenn alle Funktionen fertig sind, damit er den Endstand beschreibt. Einbau erst nach Owner-Freigabe.
- D-45-14 (Owner 21.11.): Kern im Store-Text bleibt: Datenschutz-Satz, Connector-Satz, Umstiegs-Link, Link auf die GitHub-Doku. Messzahl (730.2 MB), die 5 Grenzen, Formatliste, Share-Satz und "Similar documents" wandern in README bzw. Doku aller drei Sprachen; die bisherigen Gates prüfen sie dort. Länge an 2 bis 3 vergleichbaren Store-Apps messen.

### Release (REL-07)
- D-45-15: Version 1.7.0 für beide Apps. Launch-Härtung (Fehler- und Randpfade, Rechte-Grenzen, Upgrade ab 1.6.5, frische Installation, Audits erneut), Volltest DE/EN/FR ohne Sprachfehler, READMEs aller Sprachen auf aktuelle Fakten prüfen, secure-phase ohne offene Threats, Owner-Abnahme der Härtung (UI gemeinsam per Playwright).
- D-45-16: Tag, Signatur und Store-Abgabe je einzeln vom Owner freigegeben; jeder Push nur nach Owner-Frage. Antworten in #45, #56 und #57 erst nach dem Store-Release. Commits nur als street1983nk ohne Claude-Zeilen, keine closes/fixes vor Issue-Nummern.

### Claude's Discretion
- Exakte Speicherform der Ausschlussliste (App-Config-Schlüssel, JSON-Array von IDs), Endpunkt-Erweiterung von POST /admin/rules und der Vorschau, Darstellung der Liste im bestehenden Vanilla-JS-Stil (nextcloud-ui-Skill, nur Nextcloud-CSS-Variablen), genaue Wortlaute im Rahmen von D-45-08/09, Plan-Schnitt und Wellen.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Anforderungen und Fahrplan
- `.planning/REQUIREMENTS.md`: KAT-03, KAT-04, EXCL-04 bis EXCL-06, STORE-03, STORE-04, REL-07
- `.planning/ROADMAP.md`: Phase 45, Ziel und fünf Erfolgskriterien
- `.planning/STATE.md`: Projektentscheidungen, Regeln (Store-API höchstens alle 10 Minuten, keine closes-Wörter)

### Vorphase
- `.planning/phases/44-php-sicherheits-gates/44-SECURITY.md` und `44-10-SUMMARY.md`: neue PHP- und Workflow-Gates (Psalm-Taint, php-cs-fixer, zizmor, actionlint), die jede Änderung dieser Phase grün halten muss; Hinweis: Image-Digests doppelt in workflow-lint.yml und scripts/dev/php_gates_docker.sh

### Externe Quellen
- GitHub Issue #45 (Ausschluss je Mount, freie Plätze, no_wildcard-Hinweis), PR #56 (zh_TW-Katalog), PR #57 (Locale-Fix admin.js), Issue #53 (Traditional Chinese, body_zh)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `php/lib/Service/SettingsService.php`: KEY_INDEX_EXTERNAL_STORAGE (Zeile ~70), Getter indexExternalStorage(), Rules-Speicherung (~846/868)
- `php/lib/Service/StorageService.php`: providers() (~283-294) nimmt files_external ConfigAdapter auf; deselected() (~1141-1160) liefert storage_ids abgewählter Provider; oc_mounts/oc_external_mounts-Lesung (~887-900) mit mount_id = files_external-Konfigurations-ID
- `php/lib/Service/ExclusionService.php`: MAX_PREFIXES 64, MAX_PATTERNS 32, validate() (~379), validatePatterns() (~590), Fehlercodes inkl. no_wildcard
- `php/lib/Controller/SettingsController.php`: POST /admin/rules (~359), POST /admin/rules/preview (~259)
- `php/lib/Service/AdminViewService.php`: reicht Werte ans Template (~1271-1276)
- `php/templates/admin.php` (Ordnerliste ~1478, Muster ~1514, Schalter ~1588, l10n-Texte ~1034/1049) und `php/js/admin.js` (Vanilla JS, kein Vue; Schalter ~1546, no_wildcard ~1075)
- `backend/src/findling/worker/reconcile.py`: deselected-Verarbeitung (~959-1012), forget_storage ohne Gnadenfrist

### Established Patterns
- Ausschluss wirkt über die Liste deselected der Companion-Antwort; Python kennt nur storage_id
- Integrationstests setzen den Schalter per occ (`.github/workflows/integration.yml` ~2954, ~3118)

### Integration Points
- PR #57 ändert php/js/admin.js, PR #56 neue l10n-Dateien und Contract-Tests: erst mergen, dann bauen (D-45-11)

</code_context>

<specifics>
## Specific Ideas

- Reporter in #45 nutzt SMB-Mounts auf NC 35 mit Findling 1.6.1 und behalf sich mit Mustern wie Foldername*.
- Zähler-Text: "Noch N von 64 frei" (Ordner), "Noch N von 32 frei" (Muster).

</specifics>

<deferred>
## Deferred Ideas

- Eigenes lokales Embedding-Modell per eingehängtem Pfad als Experten-Option (#43, Kommentar 21.11.2026): eigene Phase nach 1.7.0.
- Tippfehler-Toleranz in der Volltextsuche (Tantivy fuzzy) (#43): eigenes Issue vom Melder erbeten, eigene Phase.
- Test, der die zizmor/actionlint-Digests in workflow-lint.yml und php_gates_docker.sh auf Gleichheit prüft (Hinweis aus 44-SECURITY.md): klein, darf in die Härtung dieser Phase, wenn der Planer es passend findet.
- Erhöhung der 64 Ordner-Plätze: nicht verlangt, Anzeige reicht (D-45-07).

</deferred>

---

*Phase: 45-findling-1-7-0*
*Context gathered: 2026-11-21*
