# Phase 29: Härtung und Store-Einreichung 1.4.0 - Context

**Gathered:** 2026-10-01 (ergänzt 2026-10-06 nach Phase-28-Abschluss, Owner-Entscheide per Auswahlfrage)
**Status:** Ready for planning

<domain>
## Phase Boundary

Findling 1.4.0 als signiertes App-Paar im Store: Launch-Härtung der Parallelpfade aus Phase 25 bis 27, Audits auf 0 CRIT / 0 HIGH, Fremdinstallation und Upgrade-Strecke Ende zu Ende grün, beide Apps auf 1.4.0 (PHP-Kopplung K6), Store-Texte gate-konform mit Owner-Abnahme (REL-04). Dazu drei kleine Issue-Fixes aus der Community, die der Owner am 01.10. in den Umfang genommen hat.

</domain>

<decisions>
## Implementation Decisions

### Übernommen (nicht neu verhandelt)
- **D-24-04:** Der Anteils-Satz für den 1.4.0-Store-Text steht WÖRTLICH fest und wird nicht umformuliert.
- Owner-Regeln: Store/README = Faktenliste mit einer Messzahl, Entwurf vor der Abgabe dem Owner zeigen; Launch-Härtung vor der Store-Abgabe, Abgabe erst nach Owner-Abnahme; nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Abschluss fixen.
- Die Store-Messzahl kommt aus Phase 28 (Owner-Entscheid SC4/Store-Zahl in 28-11).

### Upgrade-Strecke
- **D-29-01:** Der Upgrade-Test läuft **1.3.2 auf 1.4.0** (aktueller Store-Stand), nicht 1.3.0. Erfolgskriterium 2 der Roadmap wird entsprechend gelesen. Bestandsinstallation landet in Sparsam ohne Neu-Einbettung und ohne Umbau.

### Issue-Fixes im Umfang (Owner 01.10., Empfehlung übernommen)
- **D-29-02 (#22):** Dateien, deren Name mit `._` beginnt (AppleDouble, macOS-Metadaten), werden immer als ausgeschlossen übersprungen (Verdikt wie "Excluded by a rule" bzw. eine passende bestehende Reason), ohne Einstellung. Mac-Bundles (.key usw.) sind KEIN Sonderfall in 1.4.0 (Rückfrage an budachst offen).
- **D-29-03 (#21):** `FINDLING_MAX_CELLS` (Default 200.000) wird in `backend/appinfo/info.xml` als Deploy-Option deklariert, mit Beschreibung wie `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES`. Keine Anzeige der Limits in der Admin-Seite in 1.4.0.
- **D-29-04 (#18):** Download-Größenprüfung: die heruntergeladenen Bytes werden gegen die Sollgröße geprüft; ein abgeschnittener Download wird als vorübergehender Fehler erneut versucht und nicht als "beschädigt" verbucht.

### Öffentliche #18-Zusagen (Owner 06.10., alle sechs im Umfang; Quelle: .planning/todos/pending/2026-10-04-issue-18-zusagen-und-lock-timeout.md Abschnitt A, Kommentare 5970113095/5971965802/5974358682)
- **D-29-05:** Sidecar-Skip: `._*` (deckt D-29-02) UND `~$*` (Office-Lockstubs) überspringen mit ehrlichem Verdikt.
- **D-29-06:** TIFF-Decode-Shim, zwei Achsen (Dateien werden INDEXIERBAR): (a) fehlende OPEN_INFO-Einträge Grau+Extrakanal mit ExtraSamples 0/1; (b) SampleFormat-Normalisierung NUR für echtes SampleFormat 0 auf Spec-Default 1. Float16 (SampleFormat 3) wird NICHT normalisiert, bekommt ein ehrliches Urteil. Dazu Upstream-PR an Pillow vorschlagen.
- **D-29-07:** Große JPEGs per Pillow-draft-Mode bei reduzierter Skalierung dekodieren (OCR skaliert ohnehin auf 3500 px) + Header-Vorabschätzung Breite x Höhe x Kanäle gegen den Adressraum-Deckel, ehrliches Urteil statt "beschädigt".
- **D-29-08:** OLE-Sniff: Kopf d0cf11e0 unter OOXML-Endung ergibt ein ehrliches Verdikt; legacy (.xls-Streams "Workbook"/"Book") von passwortgeschützt ("EncryptionInfo"/"EncryptedPackage") unterscheiden.
- **D-29-09:** Fehlerdetail je Datei speichern (echte Reader-Exception-Klasse statt pauschal corrupt, T-02-56-konform ohne Pfad/Message-Inhalte).
- **D-29-10:** NACHPRÜFUNG der Altbestände nach dem Upgrade: Verdikte kleben an der etag; die Fix-Klassen (D-29-05..08 plus Download-Größenprüfung D-29-04) müssen aktiv neu geprüft werden. Öffentlich zugesagt ("re-checked after the upgrade, no manual cleanup").

### Weitere Owner-Entscheide 06.10. (per Auswahlfrage)
- **D-29-11:** Box-gebundene Belege (Fall-1-Belege mit nextcloud.log/NPA_TIMEOUT/HaRP, fp32-Rückkehr-Vollständigkeitsbeleg mit Statusreihe bis embedded=indexed und leerer EMBEDDING_BACKLOG_MARK, Fall-2-Feldlauf, 250-MiB-Feldlauf an Zelle 11) werden VERSCHOBEN auf die nächste ohnehin nötige Anfahrt. Phase 29 bleibt boxlos. Die Fall-1-Diagnosezeile (Entscheid A aus dem Debug embed-handover) wird trotzdem in 29 eingebaut, nur der Feldbeleg wartet.
- **D-29-12:** note_index_files-Verdrahtung: Der Vollindex-Term (MAIN_PROCESS_PER_FILE_BYTES, 6 KiB/Datei, Quick 261005-vit) wird in 1.4.0 in die Laufzeit-Slotrechnung verdrahtet; die 12-slotkosten-Rechnung bekommt den Term ebenfalls.
- **D-29-13:** Lauf-9-Lock-Timeout (OCR-zu-Embed-Übergabe, Todo-Abschnitt B): mindestens Ausnahme-Details im requeue-Log (queue.py); Debug-Vertiefung boxlos soweit möglich.
- **D-29-14:** Kleine Härtungs-Hygiene im Umfang: aws_box.sh-Schlüsselpaar-Rest-Liste-Fix, StarletteDeprecationWarning beheben.

### Claude's Discretion
- Genaue Reason/Verdikt-Zuordnung für `._*` und `~$*` (bestehende Reason bevorzugt, sonst neue mit PHP-Parität und Übersetzungen), Ort der Prüfung (Crawl/Queue vs. Container), Retry-Mechanik der Größenprüfung im bestehenden Lease-/Attempts-Modell.
- Mechanik der Altbestands-Nachprüfung (D-29-10): wie die Fix-Klassen identifiziert und neu eingereiht werden (Verdikt-basiert, ohne Vollreindex), Migrations-/Upgrade-Haken.
- Umsetzung der Vollindex-Term-Verdrahtung (D-29-12) im bestehenden Slotkosten-Modell (config.py/probe.py).

### Folded Todos
- `.planning/todos/pending/2026-10-01-issue-21-22-budachst.md` (#21 nur Deklaration, #22 `._*`; `~$*` kommt über D-29-05 dazu)
- `.planning/todos/pending/2026-09-28-issue-18-jpg-verdikt-heif-download-fixes.md` (Download-Größenprüfung + die Phase-29-Kandidaten aus dem Nachtrag 02.10., gedeckt durch D-29-08/09)
- `.planning/todos/pending/2026-10-04-issue-18-zusagen-und-lock-timeout.md` (Abschnitt A komplett = D-29-05..10, Abschnitt B = D-29-13)

</decisions>

<canonical_refs>
## Canonical References

- `.planning/ROADMAP.md` - Phase 29, Erfolgskriterien 1 bis 4
- `.planning/REQUIREMENTS.md` - REL-04
- `.planning/phases/24-owner-tor-profil-ger-st-und-marken-reparatur/24-CONTEXT.md` - D-24-04 (Store-Satz wörtlich)
- `.planning/phases/26-n-ocr-slots-und-speicherw-chter/` - D-26-16 (ChildKilled statt corrupt), Grundlage der Antworten an #15/#18
- `.planning/phases/28-abnahme-anfahrt/` - Messzahlen, Store-Zahl, performance.md
- GitHub Issues #15, #18, #21, #22 (street1983nk/nextcloud-search) - Verlauf und Zusagen an budachst
- `backend/appinfo/info.xml` - Deploy-Optionen (FINDLING_EXTRACT_ADDRESS_SPACE_BYTES als Vorlage)
- `backend/src/findling/extract/sandbox.py` - Kill-/Absturzbehandlung

</canonical_refs>

<code_context>
## Existing Code Insights

- `FINDLING_MAX_CELLS` wird in `backend/src/findling/config.py` schon gelesen (`_int_from_environment`), fehlt nur in info.xml.
- "Excluded folders" ist heute ein Präfix-Abgleich ohne Muster (php/templates/admin.php, AdminViewService "Excluded by a rule").
- Auf main gilt seit Phase 26: SIGKILL eines Sandbox-Kinds = ChildKilled (Retry), Kinder mit oom_score_adj 1000 und nice 10.

</code_context>

<specifics>
## Specific Ideas

- Nach dem Release in #15, #18, #19, #21, #22 kurz melden, was 1.4.0 davon löst (Owner-Freigabe der Texte wie üblich).

</specifics>

<deferred>
## Deferred Ideas

- #18 eigenes Verdikt "abgeschnitten" (truncated) statt "beschädigt": erst nach belegtem Befund, Kandidat 1.4.1.
- #21 Limits in der Admin-Seite anzeigen.
- #22 Ausschlussmuster als Einstellung, Sonderbehandlung von Mac-Bundles.
- HEIF/HEIC-Opener (Hypothese aus #18, nicht belegt).
- Box-gebundene Belege (D-29-11): Fall-1-Feldbelege, fp32-Rückkehr-Vollständigkeitsbeleg, Fall-2-Feldlauf, 250-MiB-Feldlauf; nächste Anfahrt.
- Float-TIFF-Decode (SampleFormat 3): nur evaluieren, NICHT zugesagt (Korrektur 05.10.).

</deferred>

---

*Phase: 29-h-rtung-und-store-einreichung-1-4-0*
*Context gathered: 2026-10-01*
