# Phase 11: Haertung und Store-Einreichung v1.1 - Context

**Gathered:** 2026-09-10
**Status:** Ready for planning

<domain>
## Phase Boundary

v1.1 steht als signiertes App-Paar (findling + findling_backend, gleiche Version) im
Nextcloud App Store, nachdem es jenseits des Happy Path getestet wurde und der Owner
die Texte abgenommen hat. Vorbedingung aus Phase 9: der vollstaendige franzoesische
Katalog (fr.json UND fr.js, Schluesselvergleich auf zwei Sprachpaare erweitert).
Requirement: REL-01.

</domain>

<decisions>
## Implementation Decisions

### Box-Einsatz und Abbau
- **D-01:** Die zwei Werkzeug-Fixes (DI-10-01 Lastwerkzeug zaehlt Ausfaelle als Erfolge,
  DI-10-02 Sprachfall-Skript trennt Berechtigung statt Index) werden mit EINER kurzen
  Box-Anfahrt gegen den echten Lastkorpus bewiesen. Kostendeckel der Anfahrt: ~4 h /
  0,50 USD (dem Owner am Checkpoint vorlegen). Der Index auf der Box ist intakt, kein
  Neuaufbau noetig.
- **D-02:** Der Installationstest aus Release-Artefakten auf amd64 und arm64
  (Erfolgskriterium 1) laeuft auf CI-Runnern beider Architekturen (arm64 nativ lief
  schon in Phase 10). KEINE zweite Nextcloud auf der Mess-Box (Lehre 06.1:
  --rm-data-Falle am selben Docker-Dienst).
- **D-03:** Am Ende von Phase 11 (nach Abgabe und Fix-Beweisen): EBS-Snapshot des
  Korpus-Volumes (~1-2 USD/Monat), danach Instanz und Volumes ABBAUEN. Der Abbau
  braucht am Checkpoint eine eigene Owner-Bestaetigung (zerstoerende Handlung).

### Upgrade-Pfad 1.0.x auf 1.1.0
- **D-04:** v1.1 haelt den bestehenden Index KOMPATIBEL: ein Upgrade von 1.0.x laesst
  Index und Vektorbestand unangetastet. Kein SCHEMA_VERSION-Sprung in dieser Phase.
  Falls die Bestandsaufnahme zeigt, dass Kompatibilitaet nicht haltbar ist, geht die
  Entscheidung mit Beleg zurueck an den Owner (Checkpoint), nicht still in den Plan.
- **D-05:** Sollte je ein Reindex noetig werden, startet er automatisch mit sichtbarem
  Status (Statusseite + Admin-Hinweis), nie still. (Vorratsentscheid; in dieser Phase
  per D-04 nicht vorgesehen.)

### Store-Texte und Franzoesisch
- **D-06 (praezisiert 10.09. nach Research):** Der Store-Text traegt genau EINE
  Kernzahl, die staerkste neue (Grundlast 103,2 MB); der datierte Alt-Neu-Vergleich
  steht im README, auf das der Store-Text verweist. Damit bleiben Kurztext-Regel
  ("hoechstens eine Zahl") und Fortschritts-Story beide intakt. Research-Befund
  beachten: das Gate scan_measured_sentence bindet den Messsatz seit 07.09. an
  README.en.md ALLEIN; beide info.xml tragen nur die qualitative 2-GB-Zusage.
  README.fr.md in derselben Runde nachziehen.
- **D-07:** FR-GATE: Der Owner (franzoesischer Muttersprachler) prueft ALLE
  franzoesischen Zeichenketten (fr.json/fr.js) und den franzoesischen Store-Text als
  eigenen blockierenden Checkpoint VOR der Einreichung.
- **D-08:** Mess-Vorbehalte (Sprachfaelle als Erstmessung, Laufzeit-Untergrenze) stehen
  NICHT im Store-Text, sondern im Messbericht/README; der Store-Text bleibt kurze
  Faktenliste nach der Kurztext-Regel und verweist auf den Bericht.

### Release-Zuschnitt und Timing
- **D-09:** Umfang v1.1.0 = Pflicht (FR-Katalog, Store-Texte mit Messzahlen, drei
  Audits, signierte Abgabe, Upgrade-Beweis) PLUS die zwei Werkzeug-Fixes DI-10-01 und
  DI-10-02 mit Box-Beweis. DI-10-04/05 und T-09-29 nur mitnehmen, falls klein und
  risikofrei; sonst dokumentiert weiterreichen.
- **D-10:** Einreichung SO FRUEH WIE MOEGLICH: sobald alle Gates gruen sind und der
  Owner Texte + FR-Gate abgenommen hat, wird eingereicht, ohne auf den ISV-Call
  (14.09.) zu warten. Das Zielfenster 16.-22.09. ist die Obergrenze, kein Startsignal.
- **D-11 (10.09. nach Research):** Das Versionsfenster von v1.1.0 bleibt bei max
  Nextcloud 34 (NC 35 ist rc4). Der stable35-RE-CHECK-Vermerk vom 16.09. in
  deploy-harp.yml bleibt eigener Merkposten; ein spaeteres 1.1.x hebt das Fenster,
  wenn 35 final ist. Die Einreichung wartet NICHT auf den RE-CHECK.

### Claude's Discretion
- Reihenfolge und Wellenschnitt der Plaene; Zuschnitt der Haertungstests jenseits des
  Happy Path (Muster 06.1: Fehler-/Edge-/Negativ-Pfade, Fremdinstallation).
- Technische Umsetzung des Schluesselvergleichs fuer zwei Sprachpaare.
- Ob die Box-Anfahrt fuer die Fix-Beweise mit dem Upgrade-Kompatibilitaetsbeweis
  kombiniert wird (solange D-02 respektiert bleibt: keine zweite NC am Mess-Docker).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Vorbedingung Franzoesisch
- `docs/l10n-french.md` — Begruendung der Vertagung aus Phase 9, 24 vorbereitete
  Wortlaute der Ergebnisseite, Umfangsdefinition fr.json + fr.js

### Uebergebene Befunde (Umfang D-09)
- `.planning/phases/10-vergleichsmessung-auf-der-aws-box/deferred-items.md` — DI-10-01
  (Lastwerkzeug, mit Belegstellen und zwei Fix-Wegen), DI-10-02 (Sprachfall-Skript),
  DI-10-03 (Store-Text-Nachzug mit Drei-Stellen-Merker), DI-10-04/05
- `.planning/phases/07-gemeinsame-embedding-engine/deferred-items.md` — DI-07-02
  (Kaltstart-Neigung ueber 1,5 s), DI-07-03

### Messzahlen fuer die Store-Texte
- `docs/measurements/2026-09-vergleichsmessung-m7g/README.md` — der abgenommene
  19-Abschnitte-Bericht; Abschnitt 9.2 traegt die Kaltstart-Methodik-Korrektur
  (OCS-Gesamtdauer vs. innerer Containeraufruf), Abschnitt 19 die ehrlichen Posten
- `docs/measurements/2026-09-vergleichsmessung-m7g/00-kernaussage.md` — Kernaussage
  und Owner-Entscheide mit Datum

### Box und Kosten
- `C:/Users/Student/.findling-loadtest/box.env` — Instanz, Volumes, Kostenstand,
  Stop-Historie (ausserhalb des Repos, KEINE Geheimnisse)
- `scripts/ops/aws_box.sh` — start/stop/status; Laufzeitrechnung seit 10-05 korrekt

### Store-Abgabe (Muster v1.0)
- `.github/workflows/store-submit.yml` — Einreichungsweg (Signatur, Token in Secrets)
- Lehre aus 06.1 (steht in `.planning/MILESTONES.md` bzw. NEXT-Historie): wer eine
  Messzahl aendert, aendert DREI Stellen; Gate-Selbsttest beachten

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/tests/tools/search_load.py`: das Lastwerkzeug fuer DI-10-01; Fix-Wege stehen
  in deferred-items (Ergebnisgruppe ohne Containerteil = Fehlschlag, oder Trefferzahl
  je Stufe als Kennzahl)
- Sprachfall-Skript `98-sprachfaelle.sh` unter
  `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/` fuer DI-10-02
- Store-Text-Gate (haelt Messsatz in README.en.md + beiden info.xml deckungsgleich,
  backtick-freier Kopf, Gate-Selbsttest mutiert die Zahl)
- Schluesselvergleich der Kataloge (de/de_DE aus Phase 9) als Vorlage fuer das zweite
  Sprachpaar

### Established Patterns
- Executor-Muster: sequenziell auf main, Basis-SHA je Welle pinnen, Audit-Welle am
  Ende, blockierende Owner-Checkpoints
- Box-Anfahrten IMMER via aws_box.sh mit Owner-Freigabe + Kostendeckel VOR dem Start
- Haertungsmuster 06.1: Fehler-/Edge-/Negativ-Pfade, Fremdinstallation Ende-zu-Ende
  aus Store-Paketen, Uninstall-Zusagen

### Integration Points
- CI: acht Workflows mit Pfadfiltern auf backend/**, php/**, scripts/**; arm64-Runner
  nativ seit Phase 10
- Release: Tag milestone-v*-Muster gilt fuer den Connector, Findling nutzt v*-Tags
  (v1.0.1 etc.); store-submit.yml haengt am Tag

</code_context>

<specifics>
## Specific Ideas

- Der Fortschritt "-85 Prozent Grundlast" (691,8 auf 103,2 MB) ist die staerkste
  ehrliche Story der Store-Texte (D-06).
- FR-Markt-Framing: Owner positioniert sich seit 10.09. als "Compliance and AI Layer
  for Nextcloud in DACH and France"; die FR-Texte sind dafuer ein Qualitaetssignal
  aus erster Hand (Muttersprache des Owners).

</specifics>

<deferred>
## Deferred Ideas

- Box-Wiederaufbau-Runbook aus dem EBS-Snapshot (gehoert zur v1.2-Messplanung, nicht
  in diese Phase; der Snapshot selbst ist D-03).
- Versionsfenster-Anhebung (NC 35) und Release-Notes-Feinschliff: nicht besprochen,
  Claude's Discretion im Rahmen des Bestands (Fenster 32-34, max 35).

</deferred>

---

*Phase: 11-haertung-und-store-einreichung-v1-1*
*Context gathered: 2026-09-10*
