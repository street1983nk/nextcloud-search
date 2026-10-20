# Phase 36: Haertung und Store-Einreichung 1.5.0 - Context

**Gathered:** 2026-10-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Findling 1.5.0 wird ueber den Happy Path hinaus gehaertet (boesartiger
Formatkorpus, Upgrade-Strecke 1.4.2 -> 1.5.0 in CI, Fremdinstallation,
M-32-02 Index-Hygiene fuer geloeschte Nutzer und verschwundene externe
Speicher) und beide Apps werden nach Owner-Abnahme (Store-Text + Produkt in
einer gemeinsamen Playwright-Runde) im Store eingereicht (2x HTTP 201,
Beleg in docs/store-listing.md). Requirements: HART-06, REL-05.

</domain>

<decisions>
## Implementation Decisions

### Boesartiger Formatkorpus (Owner-Entscheide 20.10.2026)
- **D-36-01:** Der Korpus lebt als Generatoren in den Tests: Testhelfer
  bauen die boesartigen Dateien zur Laufzeit deterministisch (Muster
  build_cfb aus Phase 29). KEINE boesartigen Binaerdateien im public Repo.
- **D-36-02:** Umfang ERWEITERT: Pflichtfamilien aus dem Erfolgskriterium
  (Archive: Bomben, Pfad-Traversal, Verschachtelung; Mails; OLE-Dateien)
  PLUS XML-Bomben (Billion Laughs in ODF/OOXML), Bild-Dekompressionsbomben
  (TIFF/PNG), uebergrosse Einzeleintraege und polyglotte Dateien.
- **D-36-03:** Boesartige Dateien enden in einer NEUEN Urteilsklasse: EINE
  Sammelklasse (Arbeitsname blocked_malicious, endgueltiger Name und
  Wortlaute ueber den Vorabplan) fuer alle Familien, der Detailgrund steht
  in der Diagnose-Zeile (file_errors + /diagnose + Admin-Karte).
- **D-36-04:** Die neuen Wortlaute (Admin-Karte, /diagnose, Kataloge) gehen
  de/en/fr als Wortlaut-Vorabplan an den Owner (Muster 34-01/35-01), BEVOR
  sie in Code und die 16 Kataloge reisen.

### M-32-02 Nachweis (Owner-Entscheide 20.10.2026)
- **D-36-05:** Die 30-Tage-Karenz fuer verschwundene externe Speicher wird
  im Test per SQL-Rueckdatierung des Erstsichtungs-Zeitstempels gerafft
  (Muster Drift-Marke 35-08). Die 30 Tage bleiben fest im Code, KEIN
  Produkt-Schalter nur fuer Testbarkeit.
- **D-36-06:** Beleg zweigleisig: Live-Beleg auf der Dev-Instanz 8090 mit
  Positivkontrolle (zweiter Nutzer bleibt im Index) PLUS dauerhafter
  Integrationstest in CI gegen Regression.

### Textstellen (Owner-Entscheide 20.10.2026)
- **D-36-07:** docs/embeddings.md:497 "fulltextsearch jahrelang verwaist":
  Praeteritum bleibt, Halbsatz ergaenzen, dass fulltextsearch seit 2026
  wieder gepflegt wird, aber weiterhin Elasticsearch-gekoppelt ist.
- **D-36-08:** Store-Text backend/appinfo/info.xml:113 "half of the box"
  wird praezisiert auf die Maschine, auf der das Backend laeuft (analog zur
  Admin-Karten-Praezisierung aus 1.4.1), in EN/DE/FR; der neue Wortlaut
  laeuft durch die Store-Text-Abnahme.

### Release-Ablauf (Owner-Entscheide 20.10.2026)
- **D-36-09:** L-35-06: httpx/httpcore-Logger im Image auf WARNING heben,
  damit fileid/userId nicht mehr im Standardlog stehen; Debug bleibt per
  Loglevel-Umschaltung moeglich.
- **D-36-10:** release.yml haengt zusaetzlich Quellpakete (git archive des
  Tags) als Release-Assets an (Merker aus Phase 34, wird mit v1.5.0
  umgesetzt).
- **D-36-11:** Fremdinstallation: CI-Beweis amd64 auf frischer Nextcloud
  (Muster 06.1-16) PLUS einmalige lokale Docker-Fremdinstallation mit
  Sichtprobe. KEINE Box-Anfahrt, keine Mietkosten.
- **D-36-12 (Bestand, bestaetigt):** Einreichungs-Reihenfolge wie 1.4.2:
  Checkpoint-Plaene (Push/Tag/Submission) seriell auf main ohne Worktree,
  jedes Push-Wort einzeln; nach dem Tag die Tag-Links blob/v1.5.0 in
  docs/store-listing.md und READMEs pruefen, DANN Owner-Abnahme, dann
  2x Submission mit Beleg in docs/store-listing.md.

### Claude's Discretion
- Definition "verschwundener externer Speicher" und die Abgleich-Mechanik
  (Research klaert die Storage-Semantik in oc_storages/oc_filecache).
- Konkrete Grenzwerte der Entpack-/Parserlimits (Kompressionsverhaeltnis,
  Verschachtelungstiefe, Eintragszahl) aus Research ableiten.
- Aufbau der Generator-Helfer und Verteilung auf Testmodule.
- Technik des Quellpaket-Schritts in release.yml (git archive je App oder
  ein Gesamtarchiv).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements und Entwuerfe
- `.planning/REQUIREMENTS.md` , HART-06 und REL-05 im Wortlaut (REL-05
  nennt die Textabnahme-Teile: D-30-06 Tschechisch-Grenzeintrag,
  Dateitypen-Liste, README-Zeilen, Urteils-Wortlaute, Grenzlisten-Frage)
- `docs/store-listing.md` , Entwuerfe "# Entwurf v1.5.0" der Phasen 30
  (Zeile 2020), 31 (2081), 32 (2193), 33 (2221), 34 (2282); Tag-URLs
  blob/v1.5.0 loesen erst mit dem Tag auf, vor Einreichung pruefen

### Haertungs-Vorbilder und offene Befunde
- `docs/measurements/` + `backend/tests/conftest.py` , build_cfb-Muster
  fuer synthetische Testdateien (Phase 29)
- `.planning/phases/35-stretch-aehnliche-dokumente-und-spikes/35-SECURITY.md`
  und Audit-Notizen , L-35-06 (httpx-INFO nennt fileid/userId, Bestand)
- `backend/appinfo/info.xml` Zeile 113 , "half of the box"-Satz (D-36-08)
- `docs/embeddings.md` Zeile ~497 , "jahrelang verwaist"-Absatz (D-36-07)

### Release-Mechanik
- `.github/workflows/release.yml` , gh release create haengt heute nur
  findling.tar.gz(.sig) + findling_backend.tar.gz(.sig) an (D-36-10)
- `docs/certificates.md` und `docs/store-identity.md` , Signatur- und
  Einreichungsweg
- `.github/workflows/store-submit.yml` , manueller Submissions-Workflow
  (2x HTTP 201, Muster 1.4.2)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Fehlerklassen-Infrastruktur aus 1.4.0: file_errors je Datei, /diagnose,
  Admin-Karte , die neue Sammelklasse D-36-03 haengt sich dort ein.
- Upgrade-Beweis-Muster in CI (1.3.2->1.4.0, zuletzt 1.4.2): Saat-Dateien,
  ERROR_UP_TO_DATE-Falle beachten (Versionsbump VOR Upgrade-Beweis).
- Injection-Korpus und Baumhash-/Katalog-Gates (16 Kataloge, Zahlengate,
  Linkgate) , jede neue Katalogzeile zieht die Gates nach.
- acceptance-Skripte der Phasen 1-3x als Regressionsrahmen.

### Established Patterns
- Wortlaut-Vorabplan (34-01/35-01): UI-/Urteilstexte de/en/fr zur Abnahme,
  bevor sie in Code und Kataloge reisen.
- Checkpoint-Plaene fuer Push/Tag/Submission seriell auf main, nicht
  autonom (Lehre Phase 29).
- SQL-Eingriffe fuer Testzustaende mit Protokoll und Rueckbau (35-08).

### Integration Points
- Index-Abgleich/Reconcile (ETag-Reconcile, Phase-33-Netz D-33-01) , dort
  haengt M-32-02 (geloeschte Nutzer, verschwundene Speicher) ein.
- Extraktoren (Archive, Mail, OLE/CFB-Sniff, ODF/OOXML via lxml, Pillow)
  , dort greifen die neuen Limits und die Sammelklasse.

</code_context>

<specifics>
## Specific Ideas

- Arbeitsname der Sammelklasse: blocked_malicious (endgueltiger Name und
  alle Wortlaute via Vorabplan, D-36-04).
- Positivkontrolle beim M-32-02-Beleg: zweiter Nutzer bleibt im Index
  (Regel: Gegenchecks mit Positivkontrolle).
- Merker aus NEXT.md fuer diese Phase sind alle in Entscheidungen
  ueberfuehrt: Tag-Links (D-36-12), embeddings.md:497 (D-36-07), L-35-06
  (D-36-09), info.xml-Satz (D-36-08), release.yml-Quellpakete (D-36-10).

</specifics>

<deferred>
## Deferred Ideas

- 186 DB-Abfragen je Poll (deferred-items, Bestand vor Phase 34): bleibt
  v1.6-Kandidat, KEIN Umbau in der Haertungsphase; nur neu bewerten, falls
  das Performance-Audit einen Release-Blocker daraus macht.
- Embedding-Wechsel granite r2, #25-Dedup, Reranker, CLIP, whisper.cpp:
  Future-Liste v1.6 in REQUIREMENTS.md, nicht Teil von Phase 36.

</deferred>

---

*Phase: 36-haertung-und-store-einreichung-1-5-0*
*Context gathered: 2026-10-20*
