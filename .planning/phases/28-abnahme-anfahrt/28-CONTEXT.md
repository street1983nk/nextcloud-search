# Phase 28: Abnahme-Anfahrt - Context

**Gathered:** 2026-09-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Für jede Profilstufe (Sparsam, Standard, Leistung) werden RAM-Spitze und Erstindex-Durchsatz des GEBAUTEN Produkts (Stand nach Phase 27, mit Probe und Settings-Fläche) auf echter Hardware gemessen, bevor ein Release die Stufe anbietet (MESS-10). Vorher liegen Rechenblatt und Kostendeckel beim Owner und sind datiert freigegeben; die Anfahrt folgt dem Runbook (Cron-Intervall-Gate, Digest-Wechsel, Rohdaten committen, Abbau mit Nachweis). Die gemessenen Slot-Kosten fließen in Formel und Probe zurück (SC4).

Nicht in dieser Phase: Launch-Härtung, Audits der Parallelpfade und Store-Einreichung 1.4.0 (Phase 29), neue Profile oder Zwischenstufen, neue Settings-Texte außer dem, was ein Formel-Nachzug zwingend verlangt.

</domain>

<decisions>
## Implementation Decisions

Vorentscheide, die hier tragen und NICHT neu verhandelt werden: D-26-10 (Messbox auf AWS-Guthaben, Konto infranodedev 450315222812, 104,29 USD gültig bis 04.09.2027, NICHT Konto Cherif83; Matrix 4/8/16/32 Kerne x86 plus 16-Kern-ARM m7g als Baseline; vCPU-Quota eu-central-1 = 32, also seriell, Erhöhung auf 48 nur falls seriell zu langsam; Korpus-Snapshot snap-03f1d1d9ad9262704 ist der Messkorpus; NACH der Phase-28-Messung ALLES abbauen inklusive Snapshot, Ziel null laufende AWS-Kosten, Abbau-Beweis dokumentiert), D-24-03 (Anteile, Obergrenzen Standard 4 / Leistung 16 Slots), D-24-06 (Vorschlags-Schwellen), D-26-02/03 (Slot-Drossel und Wächter), D-27-05/07/08 (Probe pausiert Indexierung, zweistufige N-Slot-Probe, "passt knapp" speichert nicht), Store-Regel eine Messzahl (730,2 MB, Gate test_store_metadata.py RESIDENT_FIGURE).

### Kosten und Abbruch
- **D-28-01 (Owner, 29.09.2026):** Der Kostendeckel ergibt sich aus dem Rechenblatt (Runbook Abschnitt 2, Ist-Werte der letzten Anfahrten als Untergrenze je Posten) für genau den Messumfang aus D-28-06, plus 30 Prozent Reserve. Die Zahl wird dem Owner VOR dem ersten Boxstart vorgelegt und datiert freigegeben (SC1); ohne Freigabe startet keine Box.
- **D-28-02 (Owner, 29.09.2026):** Wird der Deckel während der Anfahrt erreicht: die laufende Zelle wird zu Ende gemessen, keine neue Zelle startet, die Box bleibt stehen bis zum Owner-Wort (weiterlaufende Kosten werden in Kauf genommen, damit nichts verloren geht). Kein automatischer Abbau beim Deckel; der Abbau folgt erst nach Owner-Entscheid oder regulär nach Abschluss (D-26-10).

### Boxen und Profile
- **D-28-03 (Owner, 29.09.2026):** Referenzbox für Sparsam und den Vergleich zur Store-Zahl ist wie bisher m7g.large (2 vCPU ARM, 4 GB, mem=4G nach Runbook Block 5/12). Sparsam darf dort nicht von der Store-Messzahl abweichen (SC2).
- **D-28-04 (Owner, 29.09.2026):** x86-Matrix auf der Familie c7a (2 GB je Kern): 4, 8, 16, 32 Kerne = c7a.xlarge, c7a.2xlarge, c7a.4xlarge, c7a.8xlarge. Dazu die ARM-Baseline m7g.4xlarge (16 Kerne) aus D-26-10. Begründung: nah an typischer Selfhost-Hardware (4 Kerne / 8 GB), Speicherknappheit wird bei Leistung sichtbar und testet Probe und Wächter.
- **D-28-05 (Owner, 29.09.2026):** Auf JEDER Matrix-Box laufen alle drei Profile. Vor jeder Stufe läuft die Probe über die Settings-Fläche bzw. dieselbe Route (Weg des Produkts, nicht occ); gemessen wird jede Stufe, auch wenn die Probe "knapp" oder "passt nicht" sagt (dann per occ erzwungen, klar markiert). Das Probe-Verdikt wird je Zelle mit der Messung verglichen und im Bericht als Gegenprobe der Probe selbst ausgewiesen.

### Messumfang
- **D-28-06 (Owner, 29.09.2026):** Jede Zelle (Box x Profil) misst ein festes, OCR-lastiges Teilkorpus (Größenordnung 5.000 Dokumente, genaue Auswahl und Größe legt die Research fest, gleich für alle Zellen, reproduzierbar ausgewählt und committet) mit RAM-Spitze und Durchsatz. Nur Sparsam auf der Referenzbox m7g.large fährt den vollen Korpus (52.111 Dokumente) als Vergleich zur Store-Messzahl.
- **D-28-07 (Owner, 29.09.2026):** fp32 wird auf zwei Zellen mitgemessen: Standard mit fp32 auf einer knappen und einer großzügigen Box (Auswahl legt die Research fest, z. B. c7a.xlarge und c7a.4xlarge). Die Probe lädt die fp32-Datei dort live (Download aus dem eigenen Release, Digest-Prüfung); gemessen wird die RAM-Spitze mit fp32. Das schließt die Lücke aus 27-15/27-VERIFICATION (fp32 nur automatisiert belegt).

### Rückfluss in Formel und Probe (SC4)
- **D-28-08 (Owner, 29.09.2026):** Die gemessenen Slot-Kosten ersetzen die Schätzwerte in Formel und Probe (insbesondere OCR_SLOT_COST_BYTES = 235 MiB in backend/src/findling/config.py und die davon abgeleiteten Reserven); das ist eine Code-Änderung IN Phase 28 mit Tests. Toleranz: Eine Messung bis +10 Prozent über der Rechnung gilt als von der Rechnung getragen. Liegt eine Stufe darüber oder widerspricht ein Probe-Verdikt der Messung, entscheidet der Owner je Fall, ob die Formel nachgezogen oder die Stufe im Release nicht angeboten wird; der Entscheid wird dokumentiert (SC4).

### Nachentscheide nach der Research (Owner, 29.09.2026, alle = Empfehlung)
- **D-28-09:** Teilkorpus Variante A: 5.000 Dateien nach der festen Regel aus 28-RESEARCH.md (1.800 einseitige Scans, alle 100 Mehrseiten-Scans, 100 Bilder, 3.000 Textdateien; 40 Prozent OCR, 2.691 Seiten). Deckel-Größenordnung laut Research rund 59 USD (Rechenblatt + 30 Prozent), die endgültige Zahl gibt der Owner vor dem Boxstart frei (D-28-01).
- **D-28-10:** Toleranz für "Sparsam weicht nicht von der Store-Messzahl ab": plus/minus 2 Prozent um 730,2 MB. Innerhalb bleibt der Store-Text; außerhalb entscheidet der Owner über die Store-Zahl.
- **D-28-11:** Zusätzliche Anker-Zelle Sparsam mit Teilkorpus auf m7g.large (rund 0,53 USD): verbindet Volllauf und Teilkorpus auf derselben Box.
- **D-28-12:** Keine harte Speichergrenze auf den Matrix-Boxen, sie messen den vollen Box-RAM. Nur die Referenzbox m7g.large bleibt auf mem=4G wie die Store-Messung.
- **D-28-13:** Boxen sofort nach der letzten Zelle abbauen; der Korpus-Snapshot wird erst nach den SC4-Entscheiden des Owners gelöscht (falls eine Nachmessung nötig wird), dann mit Nachweis (D-26-10: null laufende Kosten am Ende).
- **D-28-14:** Ergänzt D-28-02: Beim Deckel Stopp und Rückfrage; zusätzlich STOPPT (nicht löscht) ein Sicherheitstimer die Instanz bei Deckel plus 20 Prozent, falls der Owner nicht antwortet. Nichts geht verloren.

### Claude's Discretion
- Genaue Auswahl des Teilkorpus (OCR-Anteil, Dokumentarten), solange fest, reproduzierbar und für alle Zellen gleich.
- Reihenfolge der Zellen (seriell, Quota 32), solange die Referenzbox und die Rechenblatt-Freigabe zuerst kommen.
- Welche Box die knappe und welche die großzügige fp32-Zelle ist (D-28-07).
- Form der Rohdaten und des Berichts (Anlehnung an docs/measurements/2026-09-*/ und docs/performance.md).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase und Anforderungen
- `.planning/ROADMAP.md` Abschnitt "Phase 28: Abnahme-Anfahrt" - Ziel und SC1 bis SC4
- `.planning/REQUIREMENTS.md` MESS-10 - Owner-Auflage 24.09. (Messung vor Angebot der Stufe)
- `.planning/phases/26-n-ocr-slots-und-speicherw-chter/26-CONTEXT.md` D-26-10 - festgeschriebene Boxen-, Konto-, Quota- und Abbauentscheide
- `.planning/phases/27-vorab-pr-fung-und-settings-oberfl-che/27-CONTEXT.md` D-27-05..10 - Probe-Ablauf und Verdikte
- `.planning/phases/27-vorab-pr-fung-und-settings-oberfl-che/27-VERIFICATION.md` - offene Punkte (fp32 live)

### Anfahrt und Messung
- `docs/runbook-messbox.md` - Rechenblatt (Abschnitt 2), Kostensätze (2.3), Rechenweg (2.5), Aufbau-Blöcke 1 bis 13b, Zustandsprüfung (5), Abbau
- `docs/performance.md` - Ziel der Messzahlen (SC2), bisherige Messkapitel
- `docs/measurements/2026-09-vergleichsmessung-m7g/`, `docs/measurements/2026-09-nachmessung-m7g/`, `docs/measurements/2026-09-slot-leiter-ci/`, `docs/measurements/2026-09-probe-live/` - Vorlagen für Rohdaten und Berichte
- `testdata/CORPUS.md` - Korpusbeschreibung

### Store-Regel
- `backend/tests/test_store_metadata.py` - RESIDENT_FIGURE (eine Messzahl, 730,2 MB)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/ops/aws_box.sh`: Box-Lebenszyklus (start, prices, destroy), Snapshot-Restore
- `scripts/ops/rss_sampler.sh`, `proc_anon_sampler.sh`, `cpu_sampler.sh`, `rss_digest.py`: RAM- und CPU-Aufzeichnung, Digest (Werkzeuge W1 bis W4 aus Phase 22)
- `scripts/ops/slot_ladder.py`, `ocr_slot_probe.py`: Slot-Leiter und Slot-Kosten-Messung (Phase 26)
- `scripts/ops/latency_probe.py`, `search_load.py`: Latenz unter Last (Phase 26, D-26-12)
- `scripts/dev/build_load_corpus.py`, `build_corpus.py`: Korpus-Aufbau, Grundlage für das feste Teilkorpus

### Established Patterns
- Rechenblatt und Deckel vor Boxstart, Ist-Werte als Untergrenze (Runbook 2.1, 2.5)
- Rohdaten committen unter `docs/measurements/<datum>-<name>/` mit README
- Messzahlen im Store-Text nur eine Zahl (Owner-Regel kurze Produkttexte)

### Integration Points
- `backend/src/findling/config.py` OCR_SLOT_COST_BYTES (235 MiB), EMBED_LANE_RESERVE_BYTES, GUARD_RESERVE_BYTES: Ziel des Formel-Nachzugs (D-28-08)
- `backend/src/findling/probe.py`, `guard.py`: nutzen die Slot-Kosten
- `php/lib/Service/ProbeService.php` und die Profil-Route: Weg der Probe je Zelle (D-28-05)
- Baumhash-Pins in `backend/tests/test_measurement_scripts.py` bei jeder Änderung an Messskripten oder php/

</code_context>

<specifics>
## Specific Ideas

- Die Probe wird selbst mitgemessen: je Zelle Verdikt gegen Messung (D-28-05), das ist die erste Feldprobe der Phase-27-Probe auf mehreren Boxen.
- fp32 live auf zwei Zellen schließt die offene Lücke aus Phase 27 (D-28-07).

</specifics>

<deferred>
## Deferred Ideas

- WR-04-Rest aus Phase 27 (OCR-indexierte Dateien mit skipped(no_text_layer) unter "Übersprungen"): Phase 29.
- Security-Hinweise aus secure-phase 27 (F-3 fp32-Marke an der Datei, T-27-39 createElement nicht im Gate): Kandidaten Phase 29.
- Issue #14 (Team-Folder-Leser jenseits der ersten 20 Namen, Neuversuch bei ACL-Änderung): wartet auf Diagnose von budachst, eigener Schnitt danach.

</deferred>

---

*Phase: 28-abnahme-anfahrt*
*Context gathered: 2026-09-29*
