# Phase 25: Einbettungsspur und Modellwahl - Context

**Gathered:** 2026-09-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Auf Boxen mit Profil Standard oder Leistung laeuft die Einbettung als eigener Nebenlaeufer neben der OCR (H1, PAR-01): eigener Anspruch mit Art-Filter (PHP-Route, KIND embed), schreibt nur in vectors.db, beruehrt den Tantivy-Writer nicht. In Sparsam bleibt IDX-08 woertlich (OCR und Einbettung nie gleichzeitig), in Standard/Leistung ist IDX-08 eine RAM-Bedingung gegen die cgroup-Grenze (PAR-04). Der Admin waehlt e5-small int8 (Default) oder fp32 (MOD-02); nach dem Wechsel laeuft der Vektor-Reindex, die Suche antwortet weiter, fp32 kommt ueber den am Owner-Tor entschiedenen Nachladeweg (D-24-05).

Nicht in dieser Phase: N OCR-Slots und Speicherwaechter (Phase 26), Settings-UI und Vorab-Pruefung (Phase 27), Abnahme-Anfahrt (Phase 28), Release 1.4.0 (Phase 29).

</domain>

<decisions>
## Implementation Decisions

Vorentscheide aus Phase 24, die hier tragen und NICHT neu verhandelt werden: D-24-01 (Weg B, OCS-Route, Abfrage je Runde), D-24-02 (Fehler = letztes bekanntes Profil, sonst Sparsam), D-24-05 (fp32 = Nachladen bei Opt-in, Digest-Pruefung, klares Verdikt offline, Start laedt nie etwas), D-24-07 (gespeicherte Wahl bleibt bei Schrumpfung, gewaehlt vs. wirksam gemeldet). Siehe `.planning/phases/24-owner-tor-profil-ger-st-und-marken-reparatur/24-CONTEXT.md`.

### fp32-Wahl und Kopplung ans Profil (MOD-02)
- **D-25-01 (Owner, 28.09.2026):** fp32 ist in den Profilen Standard und Leistung waehlbar, in Sparsam nie. Die RAM-Schranke der Slot-Formel rechnet den fp32-Mehrbedarf ein.
- **D-25-02 (Owner, 28.09.2026):** Bis zur Settings-UI (Phase 27) setzt der Admin die Praezision ueber einen EIGENEN occ-Schluessel (Arbeitsname `model_precision`, Werte `int8` | `fp32`, Default int8), getrennt vom Profil-Schluessel. Gelesen ueber dieselbe OCS-Route bzw. denselben Abfrageweg wie das Profil (Weg B, D-24-01), mit derselben Fehlersemantik (D-24-02: letzter bekannter Wert, sonst int8) und geschlossener Wertemenge.
- **D-25-03 (Owner, 28.09.2026):** Die Praezision wechselt NIE automatisch, weil jeder Wechsel ein kompletter Vektor-Reindex ist. Faellt die wirksame Stufe durch Hardware-Schrumpfung auf Sparsam (D-24-07), bleibt fp32 aktiv; nur die Slots folgen Sparsam. Die Statusroute meldet den Zustand (sinngemaess "fp32 gewaehlt, Box knapp").
- **D-25-04 (Owner, 28.09.2026):** Scheitert das Beschaffen von fp32 (offline, Proxy, falscher Digest), bleibt int8 aktiv, kein Reindex, klares Verdikt ("fp32 nicht verfuegbar, int8 bleibt aktiv"). Kein automatisches Wiederholen im Hintergrund; ein neuer Versuch nur auf erneute Admin-Aktion.

### fp32-Quelle und Offline-Weg
- **D-25-05 (Owner, 28.09.2026):** Download-Quelle ist ein Asset im eigenen GitHub-Release (street1983nk/nextcloud-search), sha256 fest im Code. Keine zweite Quelle, kein HuggingFace-Rueckfall. Der Download passiert nur auf die ausdrueckliche Admin-Wahl, nie beim Start und nie im Hintergrund (Projektregel: kein Telemetrie-Phoning, Modell nicht beim Start laden).
- **D-25-06 (Owner, 28.09.2026):** Offline-Weg: Legt ein Admin die fp32-Datei selbst ins persistente Verzeichnis und stimmt der Digest, wird sie ohne Download genutzt (Zielgruppe abgeschottete Behoerdennetze, SIB-Box/openDesk). Falscher Digest = dasselbe Verdikt wie D-25-04.

### Suche waehrend des Vektor-Reindex
- **D-25-07 (Owner, 28.09.2026):** Waehrend der Neueinbettung antwortet die lexikalische Suche vollstaendig, die semantische Haelfte nur aus bereits in der neuen Praezision eingebetteten Dokumenten und waechst mit dem Fortschritt. Kein Blau/Gruen (keine zwei Modelle gleichzeitig im RAM, kein doppelter Vektorbestand). int8- und fp32-Vektoren mischen sich nie (T-24-02, Marke aus Plan 24-01).
- **D-25-08 (Owner, 28.09.2026):** Die Adminseite zeigt Praezision plus Fortschritt (sinngemaess "Modell fp32, Neueinbettung 42 % (12.300 von 29.100)"). Quelle sind die bestehenden embedded-Zaehler der Statusroute; die Anzeige laeuft ueber die bestehende Statusflaeche, nicht ueber die neue Settings-UI (Phase 27).

### Rueckweg fp32 zu int8
- **D-25-09 (Owner, 28.09.2026):** Wechselt der Admin zurueck auf int8, wird die fp32-Datei geloescht (Platte frei), auch eine selbst abgelegte (Owner hat die Variante "nur heruntergeladene loeschen" ausdruecklich nicht gewaehlt). Ein erneuter Wechsel auf fp32 laedt neu bzw. braucht eine neu abgelegte Datei. Der Rueckwechsel loest wie jeder Praezisionswechsel den Vektor-Reindex aus.

### Nachentscheide aus der Phase-Research (28.09.2026)
- **D-25-10 (Owner, 28.09.2026):** Ist fp32 aktiv und stellt der Admin das Profil auf Sparsam, bleibt fp32 aktiv, bis der Praezisionsschluessel auf int8 steht. Nur der Praezisionsschluessel loest einen Wechsel aus, ein Profilwechsel nie. Die Statusroute meldet den Zustand (sinngemaess "fp32 aktiv, in Sparsam nicht vorgesehen, bitte auf int8 stellen"). D-25-01 gilt damit fuer die WAHL (Download/Wechsel auf fp32 nur in Standard/Leistung), nicht als Zwangsrueckweg.
- **D-25-11 (Owner, 28.09.2026):** Ist in Standard/Leistung die RAM-Bedingung fuer die parallele Einbettung nicht erfuellt, laeuft die Einbettung seriell wie in Sparsam weiter (in derselben Schleife nach der OCR), statt Zeilen warten zu lassen. SC2 "sonst wartet sie" ist damit als "wartet auf die OCR, nicht parallel" gelesen.
- **D-25-12 (Owner, 28.09.2026):** In Phase 25 laeuft in Standard UND Leistung genau EIN Einbettungs-Laeufer neben der OCR. Die Konstante embed_slots = 2 fuer Leistung bleibt stehen, wird aber erst mit dem N-Slot-Umbau in Phase 26 wirksam (Sperren um die geteilte Engine gehoeren dorthin).
- **D-25-13 (Owner, 28.09.2026):** Die Adminseite zeigt in Phase 25 eine Zeile auf der BESTEHENDEN Statusflaeche (Praezision plus Fortschritt, D-25-08), mit neuen Texten in allen acht Sprachkatalogen im Gleichstand (Katalog-Gate haelt). Keine neue Settings-Flaeche (Phase 27).
- **D-25-14 (Research-Empfehlung uebernommen):** "Erneute Admin-Aktion" fuer einen neuen fp32-Versuch (D-25-04) = ein im laufenden Prozess beobachteter Wechsel des Praezisionsschluessels von int8 auf fp32. Der Startzustand der Praezision kommt aus Marke plus verifizierter Datei, nie aus einem Lesefehler (ein Gateway-Aussetzer beim Start darf keinen fp32-Bestand loeschen).
- **D-25-15 (Research-Empfehlung uebernommen):** Proxy-Netze: HTTPS_PROXY ist ueber AppAPI nicht setzbar; die Antwort fuer solche Boxen ist der Offline-Weg (D-25-06), dokumentiert.

### Claude's Discretion
- Abbruchsemantik zweier Nebenlaeufer, Kill/Neustart mitten in beiden Spuren ohne Zeilenverlust und ohne Doppeleinbettung, gleichzeitige state.db-Zugriffe ohne Fehlerverdikte (Research-Flag der Roadmap).
- Form des Art-Filters am PHP-Anspruch (KIND embed) und der Companion-Aenderung; die Aenderung erscheint erst mit Release 1.4.0 (K6), der Container muss mit einem Companion ohne Art-Filter weiterlaufen.
- Form der RAM-Bedingung fuer den Start der Einbettungsspur in Standard/Leistung (gegen formula_memory_bytes bzw. die cgroup-Grenze) und das Warteverhalten.
- Mitnahme des idle-Guards fuer EmbeddingModel.release() aus dem Phase-23-Backlog: mit zwei Nebenlaeufern auf der geteilten Engine akut; der Plan-Schnitt entscheidet die Aufnahme.
- Asset-Name, Upload-Weg des fp32-Assets und Ablagepfad im persistenten Verzeichnis; Umgang mit einem Praezisionswechsel, waehrend noch ein Reindex laeuft.
- Genaue Texte der Verdikte und Statusfelder (Code Englisch; die eine Statuszeile aus D-25-13 in allen acht Katalogen, alle weiteren Seitentexte erst mit Phase 27).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phasenrahmen
- `.planning/ROADMAP.md` Phase 25 : Goal, Success Criteria 1-4, Research-Flag, Mitnahme-Kandidat idle-Guard
- `.planning/REQUIREMENTS.md` : PAR-01, PAR-04, MOD-02 (plus IDX-08-Wortlaut fuer Sparsam)

### Vorentscheide
- `.planning/phases/24-owner-tor-profil-ger-st-und-marken-reparatur/24-CONTEXT.md` : D-24-01..08, insbesondere D-24-05 (fp32-Lieferweg) und D-24-07 (Schrumpfung)
- `.planning/phases/24-owner-tor-profil-ger-st-und-marken-reparatur/24-REVIEW.md` : IN-02 (weights-Default von embedding_mark als Driftfalle fuer Phase 25)
- `.planning/phases/24-owner-tor-profil-ger-st-und-marken-reparatur/24-SECURITY.md` : T-24-02-Hinweis (Poller muss die tatsaechlich geladene Praezision uebergeben)
- `.planning/research/BL-F04-vorarbeit-2026-09-25.md` : Vorarbeit zu Profilen, Slot-Regel 3.1, Anteile 3.2, Wege 6.4, Risiken K1-K8

### Projektregeln
- `CLAUDE.md` : Modell ins Image backen, kein Download beim Start; keine Telemetrie; Qualitaetsgates
- `docs/embeddings.md` : Marke, Praezision, Reindex-Verhalten
- `docs/profiles.md` : Profile, Owner-Tor, Store-Satz

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/src/findling/store/vectors.py:271` `embedding_mark(model, *, tokens, weights=WEIGHTS_INT8)`: kennt seit Plan 24-01 die Praezision; fp32 haengt `/fp32` an.
- `backend/src/findling/embed/engine.py:413` `release_if_idle(ttl_seconds)` und `embed/model.py:634` `EmbeddingModel.release()`: bestehender Entlade-Mechanismus (Plan 14-07, TOCTOU-Fix WR-02 aus Phase 23).
- `backend/src/findling/profile.py`: ProfileValues mit `embed_slots` (Sparsam 0 = gleiche Schleife, Standard/Leistung aus Konstanten), `snapshot()`, `effective()`.
- `backend/src/findling/nc/queue.py:505` `DocumentQueue.profile()` plus `nc/client.py:477` `read_profile`: Muster fuer das Lesen des Praezisions-Schluessels (geschlossene Menge, Fehler = None).
- `php/lib/Controller/ProfileController.php` und `php/lib/Service/SettingsService.php::profile()`: Muster fuer die zweite Lese-Route bzw. ein erweitertes Antwortfeld.
- `backend/src/findling/config.py:1212` `_embed_model_dir()`: Modellverzeichnis als Image-Konstante mit Env-Fallback.

### Established Patterns
- Poller mit Uebergabe an die zweite Spur (`worker/poller.py:866` `_hand_over(..., kind=KIND_EMBED)`, `:1263` `_embed_the_body`, `:1925` `_embed_ready`): heute laeuft die Einbettung in derselben Schleife wie die OCR (IDX-08).
- Queue-Arten `KIND_EMBED` in `nc/queue.py:77` und `php/lib/Db/QueueMapper.php:61`; Batch-Groessen-Paritaet `QueueService::KIND_BATCH` gegen `config.py` per Test.
- Marken-Drift leert die Kette und bettet neu ein (T-24-02); int8-Marke bytegleich zu 1.3.x.
- Nur lesende OCS-GETs ohne Allowlist-Eintrag (Read-only-Gate); Gate B `rejectForeignCaller` als erste Anweisung jeder ExApp-Route.

### Integration Points
- `embedding_mark`-Aufrufe mit int8-Default: `worker/poller.py:2111` und `api/resources.py:265`. Beide muessen ab Phase 25 die tatsaechlich geladene Praezision uebergeben (IN-02, T-24-02).
- Statusroute `api/status.py` (profile-Block, `_embedded()` Zaehler) fuer D-25-03 und D-25-08.
- Lifespan in `main.py` (Hardware-Erkennung vor Poller) fuer den Start des zweiten Nebenlaeufers.

</code_context>

<specifics>
## Specific Ideas

- Verdikt-Wortlaut sinngemaess: "fp32 nicht verfuegbar, int8 bleibt aktiv" (aus D-24-05 uebernommen).
- Anzeige sinngemaess: "Modell fp32, Neueinbettung 42 % (12.300 von 29.100)".
- Offline-Weg ausdruecklich fuer abgeschottete Behoerdennetze (Bundescloud-Outreach: SIB-Box, openDesk).

</specifics>

<deferred>
## Deferred Ideas

- Blau/Gruen-Reindex (alte Vektoren bis zum Abschluss aktiv): verworfen fuer die Zielhardware (doppelter RAM und Plattenplatz), nicht vorgemerkt.
- Automatisches Wiederholen eines gescheiterten fp32-Downloads: verworfen (D-25-04).

### Reviewed Todos (not folded)
- Issue #18 Fix-Kandidaten (JPG-Verdikt, HEIF, Download-Groessenpruefung): passt nicht zum Umfang von Phase 25 (Trefferquote 0,2, nur Stichwort); wartet weiter auf budachsts Antwort, Slot-Entscheid (Phase 29 oder Einschub) beim Owner.

</deferred>

---

*Phase: 25-einbettungsspur-und-modellwahl*
*Context gathered: 2026-09-28*
