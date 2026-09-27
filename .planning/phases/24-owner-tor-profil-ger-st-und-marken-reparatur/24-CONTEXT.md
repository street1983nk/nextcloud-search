# Phase 24: Owner-Tor, Profil-Gerüst und Marken-Reparatur - Context

**Gathered:** 2026-09-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Die Grundsatzentscheide des Milestones v1.4 sind schriftlich und datiert gefallen (dieses Dokument IST das Owner-Tor), bevor Code sie implizit trifft. Danach liefert die Phase: Profile als Anteils-Formel an der erkannten Hardware (PROF-01), Sparsam Wert für Wert gepinnt (PROF-02), den entschiedenen Profil-Weg in den Container (PROF-03), cgroup-bewusste Hardware-Erkennung mit Profil-Vorschlag ohne Umschalten (HW-01) und die Vektor-Marke mit Gewichtspräzision samt Upgrade-Verhalten (MOD-01). KEINE Nebenläufigkeit (Phase 25/26), KEINE Settings-UI (Phase 27), KEINE Probe (Phase 27).

</domain>

<decisions>
## Implementation Decisions

**Owner-Tor vollzogen am 27.09.2026.** Alle drei Tor-Entscheide (Success Criterion 1) sind gefallen; ab jetzt darf Code geschrieben werden, der Profilweg, Anteile und Lieferweg berührt.

### Profil-Weg in den Container (Owner-Tor Teil 1, PROF-03)
- **D-24-01 (Owner, 27.09.2026):** Weg B aus der Vorgänger-Research 6.4: Die PHP-Seite bekommt eine OCS-Route (Muster `queues/documents/stats`), der Container fragt das Profil einmal je Runde ab. Live-Wechsel ohne Container-Neustart; die Adminseite speichert das Profil PHP-seitig (appconfig). Der `config.settings()`-lru_cache muss dafür geschichtet werden (statische Werte vs. Profilwerte). Weg A (Umgebungsvariable, Neustart) und Weg C (Datei im Persistenzpfad) sind verworfen.
- **D-24-02 (Owner, 27.09.2026):** Fehlersemantik der Profilabfrage: Der Container merkt sich das zuletzt erfolgreich gelesene Profil für die laufende Prozesslebensdauer; war noch nie eines lesbar (Erststart, Companion ohne Route), läuft Sparsam. Kein Flattern bei kurzen Gateway-Aussetzern, fail-safe beim Erststart.
- Bereits gelockt (REQUIREMENTS PROF-03): Eine gesetzte Umgebungsvariable überstimmt das Profil sichtbar (eine Wahrheit).

### Anteile und Store-Satz (Owner-Tor Teil 2, PROF-01)
- **D-24-03 (Owner, 27.09.2026):** Anteile nach Research-Vorschlag 3.2: Standard = 50 % der Kerne / 40 % des Speichers, OCR-Obergrenze 4 Slots; Leistung = Kerne minus 1 / 60 % des Speichers, OCR-Obergrenze 16 Slots. Sparsam bleibt fest 1 Slot ohne Anteile (gepinnt). Slotzahl nach der Regel aus Vorarbeit 3.1: `OCR-Slots = max(1, min(floor(Anteil_Kerne x C - r), floor((M_frei - Grundlinie - Reserve) / Kosten_je_Slot)))`.
- **D-24-04 (Owner, 27.09.2026, WÖRTLICH für den 1.4.0-Store-Text):** "Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware hat, gibt per Profil höchstens die Hälfte der Box frei (Profil Standard) oder alles bis auf einen Kern (Profil Leistung)." Dieser Satz reist mit Release 1.4.0 (REL-04) und wird nicht umformuliert.

### fp32-Lieferweg (Owner-Tor Teil 3, MOD-02/K7)
- **D-24-05 (Owner, 27.09.2026):** Nachladen bei Opt-in. int8 bleibt wie heute ins Abbild gebacken (Zero-Config unverändert, kein +352 MB für alle). fp32 wird erst geladen, wenn der Admin es ausdrücklich wählt: Download ins persistente Verzeichnis mit Digest-Prüfung, klares Verdikt bei Offline/Proxy ("fp32 nicht verfügbar, int8 bleibt aktiv"). Die Regel "Modell ins Image backen, kein Download beim Start" (CLAUDE.md) bleibt gewahrt: der START lädt weiterhin nichts, nur die ausdrückliche Admin-Aktion lädt. K7-Neuprüfungs-Vorbehalt der Nicht-Spaltung wird nicht berührt. (Der Bau des Nachladewegs selbst liegt in Phase 25/MOD-02; Phase 24 legt nur den Weg fest und baut die Marke.)

### Vorschlags-Schwellen und Rückstufung (HW-01)
- **D-24-06 (Owner, 27.09.2026):** Vorschlags-Schwellen nach Research 3.2: Standard wird ab 6 GB und 3 Kernen vorgeschlagen, Leistung ab 12 GB und 6 Kernen, darunter Sparsam. Nur Vorschlag über die Statusroute, nie automatisches Hochschalten.
- **D-24-07 (Owner, 27.09.2026):** Bei Hardware-Schrumpfung bleibt das GESPEICHERTE Profil stehen; der Container arbeitet selbsttätig auf der größten noch passenden Stufe und meldet beides (gewählt vs. wirksam) über die Statusroute an die Seite. Wächst die Hardware wieder, gilt ohne Zutun wieder das gewählte Profil. Kein stilles Umschreiben von Admin-Entscheidungen.

### Claude's Discretion
- Download-Quelle und Signatur-/Digest-Mechanik des fp32-Nachladens (Researcher prüft; Festlegung spätestens im Phase-25-Plan, Phase 24 dokumentiert den Entscheid nur).
- Technischer Schnitt der lru_cache-Schichtung in `config.py` (statisch vs. profilabhängig) und die genaue Form der OCS-Route.
- Form der Marken-Erweiterung in `store/vectors.py` (heute `model/int8/384/tokens`, `vectors.py:273`), solange gilt: alte Marke ohne Präzisionsangabe wird als int8 gelesen und löst KEINEN Reindex aus (Schnittentscheid Roadmap 27.09., verhindert 5-h-Zwangs-Reindex bei allen Beständen).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Research (Grundlage des Owner-Tors)
- `.planning/research/BL-F04-vorarbeit-2026-09-25.md` , Anteils-Formel 3.1, Profil-Startwerte 3.2, Hardware-Erkennung 3.3 (inkl. Fallen-Tabelle), Wechselmechanik/Marken-Lücke 3.4, fp32 3.5, Risiken K1-K10, Security-Abschnitt 8
- `.planning/research/BL-F04-worker-skalierung.md` §6.4 , Wege A/B/C (Entscheid: B), lru_cache-Befund `config.py`, "eine Wahrheit"-Regel; §6.5 ADM-04-Grenze

### Requirements und Roadmap
- `.planning/REQUIREMENTS.md` , PROF-01..03, HW-01, MOD-01 (Phase-24-Anteil), Out-of-Scope-Liste
- `.planning/ROADMAP.md` , Phase-24-Success-Criteria (5 Punkte), Serialisierungs-Begründung (MOD-01 VOR jedem Modellschalter, K8)

### Bestandscode und -dokumente (von der Research belegt, Stand 25.09.)
- `backend/src/findling/config.py` , `settings()` lru_cache (~1240), `INDEX_WORKERS` (81), Bereichsprüfer `_bounded_int_from_environment`
- `backend/src/findling/store/vectors.py` , `embedding_version`-Marke ohne Präzision (273), `EMBEDDING_DIMENSIONS` (81), Längenprüfung (636)
- `backend/tests/test_config.py` , Pin-Test-Muster (INDEX_WORKERS) für den Sparsam-Pin
- `docs/embeddings.md` §8 , automatischer Vektor-Reindex über die Marke (Baubestand seit E-H4)
- `docs/admin-page.md` , ADM-04 ("Was die Seite bewusst nicht kann"), Statusroute/`GET /rates`
- `backend/appinfo/info.xml` , Umgebungsvariablen-Deklaration (337-473), access_level-Mechanik

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Statusroute existiert bereits (Adminseite liest sie; `docs/admin-page.md`): Erkennung + Vorschlag werden dort ANGEHÄNGT, keine neue Fläche in dieser Phase
- Pin-Test-Muster `test_config.py`/`INDEX_WORKERS` für den Wert-für-Wert-Pin von Sparsam
- Vektor-Reindex-Mechanik über `embedding_version` (Marke leeren, Bänder zu 500, Suche bleibt lexikalisch) ist Baubestand; es fehlt NUR die Präzision in der Marke
- Store-Gate `test_store_metadata.py` (RESIDENT_FIGURE 730,2 MB) sichert Success Criterion 3 ab

### Established Patterns
- OCS-Routen-Muster `queues/documents/stats` auf der PHP-Seite (Vorlage für die Profil-Route)
- `_bounded_int_from_environment` in `config.py` für Bereichsprüfung; Profilname als geschlossene Menge (Security §8 der Vorarbeit)
- Hardware-Erkennung: `os.process_cpu_count()` + `/sys/fs/cgroup/cpu.max` (Minimum), `memory.max`, bei `max` `/proc/meminfo` `MemAvailable` (nicht MemTotal); Fallen-Tabelle in Vorarbeit 3.3 beachten (A9: HaRP setzt meist kein Limit)

### Integration Points
- PHP-Companion: neue OCS-Route = Companion-Änderung, reist erst mit Release 1.4.0 (K6); Container muss bis dahin mit Companion OHNE Route laufen (D-24-02 deckt das ab)
- `config.settings()`-Cache-Schichtung ist die strukturelle Vorarbeit für alle Profilwerte der Phasen 25/26

</code_context>

<specifics>
## Specific Ideas

- Store-Satz D-24-04 ist wörtlicher Owner-Text, Begründung des Owners: für Nutzer am einfachsten, sichersten, zuverlässigsten und "Geschwindigkeit maximiert" (lädt Nutzer mit starker Hardware aktiv zum Profilwechsel ein, führt aber mit dem unveränderten Sparsam-Versprechen)
- Meldung "gewählt vs. wirksam" (D-24-07) soll auf der Seite sichtbar beide Werte nennen, nicht nur einen Warnhinweis

</specifics>

<deferred>
## Deferred Ideas

- Bau des fp32-Nachladewegs (Download, Digest, Entladen) , Phase 25 (MOD-02); Phase 24 dokumentiert nur den entschiedenen Weg und baut die Marke
- N-Slot-Berechnung wird in Phase 24 nur als Formel + gemeldete Werte gebaut (Success Criterion 2); echte Slots kommen mit Phase 25/26
- idle-Guard `EmbeddingModel.release()` , Mitnahme-Kandidat Phase 25 (steht schon in ROADMAP)

</deferred>

---

*Phase: 24-Owner-Tor, Profil-Gerüst und Marken-Reparatur*
*Context gathered: 2026-09-27*
