# Phase 26: N OCR-Slots und Speicherwächter - Context

**Gathered:** 2026-09-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Auf Mehrkern-Boxen mit Profil Standard oder Leistung teilt sich die OCR-Spur auf N Slots auf (PAR-02): Semaphore, N Sandbox-Kinder mit je eigener Pipe und eigenem Zaehler, Sperre um IndexBatchWriter.add(); die Zusagen "mindestens einmal ausliefern, hoechstens einmal indexieren" halten unter Parallelitaet, belegt durch einen Kill-Test in Linux-CI. Der Anspruch liefert genug OCR-Zeilen (KIND_BATCH[ocr]-Erhoehung als Companion-Aenderung, Sperrfrist-Ableitung neu gefasst). Ein Speicherwaechter (PAR-03) drosselt Slots bei knapper cgroup und senkt nach wiederholtem memory.events max oder einem OOM-Kill die wirksame Stufe, sichtbar gemeldet. Mit dem N-Slot-Umbau wird ausserdem embed_slots = 2 fuer Leistung wirksam (D-25-12: Sperren um die geteilte Engine gehoeren in diese Phase). os.nice fuer die Sandbox-Kinder kommt FEST in diese Phase (A12, Feldbeleg Issue #19).

Nicht in dieser Phase: Settings-UI und Vorab-Pruefung (Phase 27), AWS-Matrix-Messung am gebauten Produkt (Phase 28, Entscheide unten festgeschrieben), Release 1.4.0 (Phase 29).

</domain>

<decisions>
## Implementation Decisions

Vorentscheide, die hier tragen und NICHT neu verhandelt werden: D-24-03 (Slotformel 3.1, Obergrenzen Standard 4 / Leistung 16, Sparsam fest 1 Slot), D-24-07 (gespeichertes Profil bleibt bei Schrumpfung, gewaehlt vs. wirksam gemeldet), D-25-11 (RAM-Bedingung nicht erfuellt = seriell weiter, nicht warten), D-25-12 (embed_slots = 2 fuer Leistung wird erst mit dieser Phase wirksam). Basis fuer den Waechter ist der Phase-25-Leser `memory_guard.headroom_bytes` (anon statt memory.current, cgroup-v1-Fallback auf MemAvailable).

### Speicherwaechter: Eskalation und Rueckweg (PAR-03)
- **D-26-01 (Owner, 28.09.2026):** Nach dem Ausloeser senkt der Waechter NUR die wirksame Stufe, nie das gespeicherte Profil (D-24-07 gilt). Die Absenkung wird als EIGENER persistenter Merker abgelegt (z. B. appconfig-Schluessel ueber die bestehende Schreib-/Leseroute), damit sie einen Neustart nach OOM-Kill ueberlebt und keine Absturzschleife entsteht. Statusroute und Adminseite melden gewaehlt vs. wirksam plus Ursache.
- **D-26-02 (Owner, 28.09.2026):** Erste Eskalationsstufe (Slot-Drossel) ist rechnerisch je Runde: Vor jedem Staffel-Start prueft der Poller gegen `headroom_bytes`, ob ein weiterer Slot (Kosten_je_Slot + Reserve) passt; wenn nein, startet er weniger Kinder. Kein neues Kernelsignal noetig.
- **D-26-03 (Owner, 28.09.2026):** Ausloeser der Stufen-Absenkung: zwei memory.events-max-Ereignisse (Delta-Zaehlung) innerhalb eines gleitenden Fensters (Groessenordnung 10 Minuten, endgueltigen Wert legt die Research fest) ODER ein einzelner beobachteter OOM-Kill (Sandbox-Kind vom Kernel gekillt bzw. memory.events oom_kill steigt) senken sofort um eine Stufe.
- **D-26-04 (Owner, 28.09.2026):** Rueckweg nur durch Admin-Aktion: Der Absenk-Merker bleibt, bis der Admin das Profil neu setzt oder bestaetigt (occ, ab Phase 27 die Settings-UI mit Probe). Kein automatisches Anheben (kein Flattern); die Seite nennt Stufe, Ursache und den Rueckweg.

### Anspruchsgroesse, Sperrfrist und K6-Uebergang (PAR-02)
- **D-26-05 (Owner, 28.09.2026):** KIND_BATCH[ocr] wird FEST auf 32 erhoeht (2 x Obergrenze 16 Slots Leistung): Doppelpuffer, damit Slots waehrend des naechsten Anspruchs Nachschub haben. Kein neuer Routen-Parameter; der Paritaetstest QueueService::KIND_BATCH gegen config.py bleibt einfach.
- **D-26-06 (Owner, 28.09.2026):** Sperrfrist-Neuableitung per Formel: Sperrfrist = ceil(Batchzeilen / wirksame Slots) x Datei-Zeitdeckel (aus OCR_MAX_PAGES x Seiten-Timeout) + Marge. Sparsam (1 Slot, 32 Zeilen) bekommt automatisch eine lange Frist, Leistung eine kurze. Die Formel lebt im Container.
- **D-26-07 (Owner, 28.09.2026):** Alter Companion (K6-Uebergangsfenster): adaptiv, Slots = min(N, gelieferte Zeilen). Der Poller startet nie mehr Kinder, als der Anspruch Zeilen geliefert hat; kein Versionscheck, kein Sonderpfad. Mit neuem Companion entfaltet sich N von selbst.
- **D-26-08 (Owner, 28.09.2026):** Der Kill-Test in Linux-CI (SC2, N >= 4) deckt BEIDE Faelle ab: (1) SIGKILL auf den Hauptprozess mitten in einer halben Staffel (der OOM-Kill-Fall) und (2) Kill eines einzelnen Sandbox-Kindes, waehrend die anderen weiterlaufen. Beide enden mit: jede Datei genau einmal im Index, keine Zeile verloren.

### Messung des Durchsatzfaktors (SC3)
- **D-26-09 (Owner, 28.09.2026):** Phase 26 misst NUR in CI: Leiter 1 vs 2 vs 4 Slots auf dem arm64-CI-Runner (4 Kerne) mit dem bestehenden Messwerkzeug und Korpus der Phase-22-Anfahrt; der Zugewinn je Stufe wird gegen die Rauschgrenze 1,05 (Vorarbeit 2.5) gehalten, Rohdaten committet. Sparsam liest weiterhin mit genau einem Slot, der Pin-Test bleibt gruen.
- **D-26-10 (Owner, 28.09.2026, FESTGESCHRIEBEN FUER PHASE 28):** Die AWS-Matrix-Messung laeuft NICHT in Phase 26, sondern einmal in Phase 28 am gebauten Produkt (MESS-10, mit Rechenblatt und Kostendeckel vor dem Boxstart). Festgeschriebene Entscheide: Messbox auf AWS-Guthaben, Konto infranodedev 450315222812 (104,29 USD gueltig bis 04.09.2027; NICHT das Konto Cherif83); Matrix 4/8/16/32 Kerne x86 plus 16K-ARM m7g (Baseline-vergleichbar); vCPU-Quota eu-central-1 = 32, also seriell fahren (Erhoehung auf 48 nur, falls seriell zu langsam); Korpus-Snapshot snap-03f1d1d9ad9262704 bleibt bis dahin Messkorpus; NACH der Phase-28-Messung ALLES abbauen inklusive Snapshot (null laufende Kosten).

### Slot-Prioritaet os.nice (A12, Issue #19)
- **D-26-11 (Owner, 28.09.2026):** os.nice kommt FEST in diese Phase (Feldbeleg Issue #19: UI-Timeout unter Indexlast). Umfang: NUR die N Sandbox-Kinder starten mit nice 10 (tesseract-Subprozesse erben die Stufe). Der Hauptprozess (Suche, API, Einbettung) bleibt normal; die Einbettung wird weiter ueber Threadzahl/Batchgroesse gezuegelt. Das nice gilt in ALLEN Profilen, auch Sparsam mit einem Slot (der #19-Beleg kam aus dem Ein-Slot-Betrieb).
- **D-26-12 (Owner, 28.09.2026):** Beleg zweiteilig: (1) CI-Zusicherung, dass jedes Kind mit der Stufe laeuft (inklusive Vererbung an tesseract); (2) einmalige Live-Latenzprobe auf dem nc35-Harness (status.php/Suche unter Volllast mit und ohne nice), Ergebnis in den Phasen-Beweis und als Zahlbeleg-Grundlage fuer die Issue-#19-Antwort.

### Nachentscheide aus der Phase-Research (28.09.2026)
- **D-26-13 (Owner, 28.09.2026, ersetzt die Mechanik von D-26-06):** Sperrfrist als Zeilenbeschnitt statt Frist-Formel: Die feste PHP-Lease (1800 s) bleibt unveraendert, der Container behaelt je wirksamem Slot etwa 2 Zeilen des Anspruchs und gibt den Ueberschuss sofort per unlock zurueck (Auslieferung wird erstattet, retries bleiben korrekt). Kein neuer Lease-Parameter in der Claim-Route. Achtung Research-Befund: die alte Ableitung ueber OCR_JOB_SECONDS_MAX ergaebe bei 32 Zeilen einen negativen Wert, die Rechnung laeuft ueber Zeilen je Slot.
- **D-26-14 (Owner, 28.09.2026, praezisiert D-26-05):** KIND_BATCH[ocr] = 32 gilt NUR im Lane index (Standard/Leistung); im Lane all (Sparsam, Altbestand) bleibt es bei 2. Sonst fraessen OCR-Zeilen das gemeinsame Budget (Einbettung verhungert) und ein 1.3-Container bekaeme 32 Zeilen auf einmal. Paritaetstest deckt beide Werte.
- **D-26-15 (Owner, 28.09.2026, verfeinert D-26-03):** Ein max-Ereignis zaehlt nur, wenn memory.events max steigt UND der anon-Headroom unter ~235 MiB liegt (Kernel zaehlt max schon bei harmloser Cache-Rueckgewinnung; Eigenmessung 2796 Ereignisse ohne Schaden). Fenster 600 s, die zwei Ereignisse mindestens 60 s auseinander.
- **D-26-16 (Owner, 28.09.2026):** Ein Kind-Prozessende ohne SIGTERM (externer Kill, exitcode -9) waehrend einer Mehr-Slot-Staffel zaehlt als OOM-Kill im Sinne von D-26-03 (deckt Boxen ohne cgroup-Limit ab, Vorarbeit A9). Gegenmittel aus der Research uebernommen: oom_score_adj 1000 in jedem Kind (der Killer trifft zuerst ein Kind, nie den Hauptprozess), und ein extern gekilltes Kind erzeugt KEIN Verdikt fuer die Datei; die Datei laeuft danach allein erneut (heutiges Verhalten waere Dateiverlust ueber failed(corrupt)/failed(ocr_failed)).

### Claude's Discretion
- OOM-Kette R1 im Detail (memory.events-Semantik unter cgroup v2, Delta-Zaehlung, Verhalten in der HaRP-Umgebung, Verhalten auf v1-Hosts ohne Signal) und der endgueltige Fensterwert fuer D-26-03: Research legt fest.
- Abbruchsemantik halber Staffeln im Detail (Reihenfolge ack vs. Index-Commit unter N Slots, Zusammenspiel mit dem retries-Zaehler in QueueMapper), solange D-26-08 beweisbar haelt.
- Platzierung und Form der Semaphore, Aufteilung Anspruchszeilen -> Kinder (Work-Stealing vs. feste Zuteilung), Form der Sperre um IndexBatchWriter.add().
- Form der Sperren um die geteilte Embedding-Engine fuer embed_slots = 2 (D-25-12) und die Mitnahme des idle-Guards, falls Phase 25 ihn nicht abgedeckt hat.
- Genauer Schluesselname und Wertemenge des Absenk-Merkers (D-26-01), Wortlaut der Status-/Ursachen-Meldungen (Code Englisch; neue Seitentexte in allen acht Katalogen im Gleichstand, Katalog-Gate haelt). Research-Empfehlung uebernommen: Merker in der eigenen state.db statt appconfig (kein Schreibweg nach Nextcloud noetig, Gate A unberuehrt); Rueckweg-Erkennung ueber einen Bestaetigungs-Token in der Profil-Route.
- Live-Latenzprobe D-26-12: os.nice wirkt nur innerhalb derselben cgroup (Research); die Probe misst Findling-Suche und status.php GETRENNT, damit der #19-Beleg das Richtige zeigt.
- Schnitt des CI-Kill-Tests (Harness, Korpusgroesse, Laufzeitbudget) und der CI-Messleiter (D-26-09).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phasenrahmen
- `.planning/ROADMAP.md` Phase 26 : Goal, Success Criteria 1-4, Research-Flag (OOM-Kette R1, halbe Staffeln, Sperrfristen bei KIND_BATCH[ocr] = 2N)
- `.planning/REQUIREMENTS.md` : PAR-02, PAR-03 (plus PROF-01-Slotformel und Out-of-Scope: OMP_THREAD_LIMIT=1 bleibt, Skalierung nur ueber Prozesse/Slots)

### Vorentscheide
- `.planning/phases/24-owner-tor-profil-ger-st-und-marken-reparatur/24-CONTEXT.md` : D-24-03 (Anteile/Obergrenzen), D-24-07 (Schrumpfung, gewaehlt vs. wirksam)
- `.planning/phases/25-einbettungsspur-und-modellwahl/25-CONTEXT.md` : D-25-11 (seriell statt warten), D-25-12 (embed_slots = 2 wird HIER wirksam)
- `.planning/phases/25-einbettungsspur-und-modellwahl/25-RESEARCH.md` : Pitfall 7 (anon statt memory.current), Grundlage von memory_guard.py
- `.planning/research/BL-F04-vorarbeit-2026-09-25.md` : Slot-Regel 3.1, Rauschgrenze 2.5, Risiken K1-K10 (insbesondere R1/OOM und K4/UI-Last), Security-Abschnitt 8

### Bestandscode
- `backend/src/findling/memory_guard.py` : headroom_bytes/anon_bytes, die Basis des Waechters
- `backend/src/findling/extract/sandbox.py` : das eine langlebige Extraktions-Kind (spawn, RLIMIT_AS, Recycling-Regeln, Import-Hygiene) als Vorlage fuer N Kinder
- `backend/src/findling/profile.py` : ProfileValues.ocr_slots/embed_slots, ocr_slots()-Formel, effective()
- `php/lib/Service/QueueService.php` + `php/lib/Db/QueueMapper.php` : claimBatch/unlock, retries-Zaehlung, KIND_BATCH (Paritaetstest gegen config.py)
- `backend/src/findling/index/writer.py` : IndexBatchWriter (die zu sperrende Stelle)

### Projektregeln und Doku
- `CLAUDE.md` : Qualitaetsgates, Hardware-Ziel, Owner-Regel Audits nach jeder Phase
- `docs/profiles.md` : Profile, Owner-Tor, Store-Satz (Waechter-Meldungen muessen dazu passen)
- Issue #19 (budachst) : Feldbeleg UI-Timeout, Grundlage fuer D-26-11/12

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `memory_guard.headroom_bytes()` (Phase 25): fertiger, injizierbarer Leser fuer die Slot-Drossel D-26-02; wirft nie, loggt nie.
- `extract/sandbox.py`: langlebiges spawn-Kind mit RLIMIT_AS, Deadline und Recycling; N Instanzen davon sind der Kern von PAR-02. Der Kind-Start ist der Ort fuer os.nice (D-26-11).
- `profile.py` `ocr_slots()`/`ProfileValues`: Slotzahl je Profil steht; die Phase verdrahtet sie mit echten parallelen Kindern.
- Messwerkzeug + Korpus der Phase-22-Anfahrt (docs/performance.md, Basiszahlen B1-B5) fuer die CI-Messleiter D-26-09.
- Statusroute `api/status.py` profile-Block (gewaehlt vs. wirksam seit Phase 24): der Waechter haengt Stufe + Ursache dort an.

### Established Patterns
- Lease-Mechanik: claimBatch erhoeht retries, unlock senkt; vierter Claim entdeckt die Erschoepfung (QueueService-Docblock). Sperrfrist-Formel D-26-06 setzt hier an.
- Paritaetstest KIND_BATCH (PHP) gegen config.py (Python) in tests/test_config.py: bei der 32er-Erhoehung beidseitig pflegen.
- Sparsam-Pin Wert fuer Wert (test_config.py-Muster): D-26-09 verlangt, dass der Pin-Test gruen bleibt; das neue nice ist bewusst KEINE Sparsam-Abweichung (D-26-11 gilt ueberall).
- K6-Kopplung: Companion-Aenderungen reisen erst mit Release 1.4.0; der Container muss bis dahin mit altem Companion laufen (D-26-07, gleiches Muster wie der Art-Filter aus Phase 25).

### Integration Points
- `worker/poller.py`: heutige Staffel-Schleife mit extract_guarded; hier entstehen Semaphore, Kinder-Pool und die Sperre um IndexBatchWriter.add().
- `worker/embedding.py` + `embed/engine.py`: Sperren um die geteilte Engine fuer embed_slots = 2 (D-25-12).
- `php/lib/Service/QueueService.php`: KIND_BATCH[ocr]-Erhoehung + Sperrfrist (Companion-Aenderung dieser Phase).
- Persistenter Absenk-Merker: gleiche Schreib-/Leseroute wie das Profil (Weg B, D-24-01), neuer Schluessel.

</code_context>

<specifics>
## Specific Ideas

- Waechter-Meldung nennt sichtbar BEIDE Werte plus Ursache, sinngemaess "gewaehlt Leistung, wirksam Standard (Speicher knapp, 2x memory.events max)" - gleiche Linie wie D-24-07.
- Die Live-Latenzprobe (D-26-12) soll als Zahlbeleg fuer die Issue-#19-Antwort taugen (Antwort selbst erst nach Owner-Freigabe, Owner-Regel).
- Falsches AWS-Konto Cherif83 nicht verwechseln (D-26-10, Owner-Merker 28.09.).

</specifics>

<deferred>
## Deferred Ideas

- AWS-Matrix-Messung, Quota-Erhoehung auf 48, Snapshot-Abbau: Phase 28 (D-26-10 haelt die Entscheide fest).
- Issue #18 Fix-Kandidaten (JPG-Verdikt, HEIF, Download-Groessenpruefung): weiterhin nicht Teil von v1.4-Phase-26; wartet auf budachsts Antwort, Slot-Entscheid beim Owner (pending todo vom 28.09.).

</deferred>

---

*Phase: 26-n-ocr-slots-und-speicherw-chter*
*Context gathered: 2026-09-28*
