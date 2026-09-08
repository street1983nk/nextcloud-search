# Phase 5: Härtung und Store-Einreichung v1.0 - Context

**Gathered:** 2026-09-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Die Betriebsversprechen werden auf echter 4-GB-ARM-Hardware belegt statt behauptet
(RSS-Kurve als dokumentierte Store-Zahl), der Rechte-Paritätstest über sechs
Szenarien läuft als CI-Dauergate, beide Apps installieren/laufen/deinstallieren
sauber auf docker-compose und AIO über HaRP (NC 32 bis 34), und am Phasenende
liegt eine signierte, XSD-validierte, einreichungsBEREITE Release-Kandidatur
beider Apps vor. WICHTIGE ÄNDERUNG (Owner-Entscheid 03.09.2026): Die tatsächliche
Store-Einreichung erfolgt NICHT mehr in Phase 5, sondern gebündelt mit v1.1
(Semantik) nach Phase 6. Phase 5 endet "ein Klick bis zur Abgabe".

</domain>

<decisions>
## Implementation Decisions

### ARM-Lasttest (Erfolgskriterium 1)
- **D-01:** Zielhardware ist eine gemietete Hetzner CAX11 (Ampere ARM, 2 vCPU,
  4 GB RAM, ~4 EUR/Monat). Claude bestellt sie im bestehenden Hetzner-Konto des
  Owners, dokumentiert die Kosten und löscht die Box nach abgeschlossenem Test.
  Da die CAX11 nur 40 GB Disk hat, wird ein Hetzner-Volume (~50 GB) angehängt.
- **D-02:** Lastkorpus ist SYNTHETISCH und deterministisch generiert (Prinzip
  von scripts/dev/build_corpus.py skaliert): ~50.000 Dateien / ~20 GB, Mix nach
  realer Verteilung (Text-PDFs, Scans, Office, Bilder), OCR-Anteil ~20 %.
  Keine echten Dokumente auf der Miet-Box. Implikation akzeptiert: Volllauf
  dauert auf 4-GB-ARM voraussichtlich 1 bis 2 Tage (OCR ist der Flaschenhals).
- **D-03:** Bestanden heißt: Volllauf OHNE OOM UND Container-Peak-RSS unter
  einem festen Budget. Budgetwert ist Claude-Diskretion (Größenordnung 2,5 GB,
  damit Nextcloud+DB daneben Luft haben); die Zahl wird als dokumentierter
  Grenzwert Teil der Store-Aussage.
- **D-04:** Auf der Box läuft Nextcloud AIO + Findling via HaRP: der Lasttest
  erledigt damit zugleich den AIO-Deploy-Beweis aus PKG-03 auf der knappsten
  Zielumgebung. Der compose-Deploy-Beweis läuft separat in CI/lokal.
- **D-05:** Der ARM-Lauf spielt zusätzlich Kern-Störfälle real durch:
  docker kill mitten im OCR-Lauf + Neustart (Resume an der Zustandsmarke,
  IDX-02 auf echter Hardware), Backend-Offline-Probe (Suche degradiert sauber),
  Platte-fast-voll (paused_low_disk + Warnung sichtbar). Ergebnisse gehen in
  den Messbericht.
- **D-06:** Dokumentation der Messung: voller Bericht (Kurve, Methode, Korpus,
  Störfall-Drills) als docs/performance.md im Repo; verdichtete Kernaussage
  ("Volllauf 50k Dateien auf 4-GB-ARM, Peak X GB") in Store-Beschreibung und
  README.
- **D-07:** NC-Versionsmatrix: Install/Run/Uninstall läuft als CI-Matrix über
  Nextcloud 32 + 33 + 34 (bestehenden integration.yml-Aufbau erweitern, der
  heute auf stable34 läuft).

### Einreichung und Versionierung (Erfolgskriterium 4, GEÄNDERT)
- **D-08:** BÜNDEL-EINREICHUNG: v1.0 (Volltext+OCR) wird NICHT allein
  eingereicht, sondern gemeinsam mit der Semantik aus Phase 6 als EIN
  Store-Erstrelease. Dieser Entscheid ersetzt den offenen PROJECT.md-Punkt
  "Release-Staffelung wird zur Einreichungs-Option".
- **D-09:** Phase 5 endet EINREICHUNGSBEREIT: signierte, XSD-validierte
  Release-Artefakte beider Apps, Store-Texte fertig, ein Klick bis zur Abgabe.
  Das Roadmap-Kriterium 4 ("liegt im Store") ist entsprechend als
  "einreichungsbereit" zu lesen; die tatsächliche Abgabe ist Abschluss von
  Phase 6. Implikation: die RSS-Store-Zahl wird nach Phase 6 mit aktiver
  Semantik erneut belegt (deckt sich mit dem Phase-6-Kriterium "im selben
  RAM-Budget").
- **D-10:** Deadline: Die GEMEINSAME Einreichung bleibt hart vor Jahresende
  2026 (Phase 5 UND Phase 6 bis Dezember; Scope-Kürzung schlägt Termin).
  FALLBACK: Gefährdet Phase 6 das Ziel, wird doch gestaffelt eingereicht
  (v1.0 allein, v1.1 als Update).
- **D-11:** Versionierung LOCKSTEP: beide Apps (findling + findling_backend)
  tragen immer dieselbe Versionsnummer und werden paarweise released; exakte
  Major.Minor-Prüfung im Code. Das Store-Erstrelease heißt 1.0.0 (Semantik ist
  Teil der 1.0-Story: "Volltext + OCR + semantische Suche ab Tag 1").
- **D-12:** Store-Text dreisprachig EN/DE/FR (Muster nextcloud-mcp-connector
  inklusive Übersetzungs-Nachzieh-Regel) mit eigenem Privacy-Block: alles läuft
  lokal im Container, keine Inhalte verlassen den Server, kein
  Telemetrie-Phoning; Index at rest unverschlüsselt wird transparent benannt
  (Host-Sache). Die MCP-Connector-Synergie wird im Store-Text NICHT behauptet
  (erst nach bestandenem Content-Hit-Fidelity-Test, siehe Connector-Backlog).
  Vokabular-Gate für public Artefakte beachten.
- **D-13:** Store-Medien: Claude erstellt kuratierte Screenshots der echten UI
  via Playwright von der Dev-Instanz (Suche mit Treffern, Admin-Seite mit
  Deckungsgrad/Diagnose) plus ein schlichtes Header-Bild nach der
  Bildpost-Linie des Owners (visuell-first, Space Grotesk, echte SVG-Logos,
  keine Emojis).
- **D-14:** Zertifikats-Status GEKLÄRT (03.09. live geprüft): beide CSR-PRs
  (nextcloud/app-certificate-requests #1165 findling, #1166 findling_backend)
  am 19.08. gemergt, beide .crt liegen im appstore-Repo. Signieren ist
  entblockt; Schlüssel liegen in ~/.findling-secrets/ (docs/certificates.md).

### Uninstall-Cleanup (PKG-04, Erfolgskriterium 3)
- **D-15:** Die Bestätigung fürs Löschen des Index-Volumes ist die
  AppAPI-Standardmechanik (ExApps-Admin-UI-Checkbox "Daten löschen" bzw.
  occ app_api:app:unregister --rm-data). KEIN Eigenbau-Dialog; die Doku
  erklärt, was --rm-data bei Findling konkret entfernt.
- **D-16:** DISABLE bedeutet: Suche aus, Index bleibt. Provider, Poller und
  Event-Verarbeitung stoppen; Index, Queue und Einstellungen bleiben liegen;
  Re-Enable ist sofort wieder suchfähig ohne Reindex (Tage OCR-Arbeit auf
  4-GB-Boxen bleiben erhalten).
- **D-17:** Teilentfernung degradiert SANFT: ohne Backend zeigt die
  Companion-Seite den bestehenden "Backend nicht installiert"-Banner; ohne
  Companion läuft der Container leer weiter. Beide Fälle dokumentiert,
  empfohlene Deinstall-Reihenfolge in der Doku, kein erzwungener Kopplungszwang.
- **D-18:** Queue-Tabellen und Preferences (NC-DB, Besitz Companion) werden
  beim Companion-Remove entfernt: app:remove findling löscht via
  Uninstall-Step die eigenen Tabellen (Queue, Scan-Stats, File-State) und alle
  appconfig-Werte rückstandsfrei. Disable lässt alles liegen (D-16).

### Härtungs-Umfang
- **D-19:** Beide Deferred Items aus Phase 4 gehören in Phase 5: DI-04-03
  (Skip-Verdikte pro fileid an die NC-Seite übergeben, damit die Fehlerliste
  alle vier Gruppen zeigt und Sichtprobe-4 voll erfüllt ist) und DI-04-04
  (Versionsmarken nach einem Rebuild neu stempeln, damit die dokumentierte
  Reindex-Banner-Abhilfe occ findling:index --restart das Banner wirklich
  löscht). Quelle: .planning/phases/04-admin-sichtbarkeit-und-diagnose/deferred-items.md.
- **D-20:** ALLE offenen Review-Reste aus früheren Phasen werden in Phase 5
  abgearbeitet (Owner-Entscheid "Alles abarbeiten", bewusst gegen die
  schlankere Empfehlung): der Researcher inventarisiert unerledigte Mediums/
  Lows aus den Phase-2/3/4-Audits (u.a. die in 03-CONTEXT.md gelisteten
  M1/M2/M5/M8/M9 und Sec-L2/L4/L5/L6, soweit noch offen) und die Phase-4-Infos
  IN-01..IN-07 aus 04-REVIEW.md; der Planner plant sie ein. Spannungsfeld zur
  Dezember-Deadline ist durch den Staffelungs-Fallback (D-10) abgefedert.

### Paritätstest (SRCH-04, Erfolgskriterium 2)
- **D-21:** Parität heißt SICHTBARKEITS-PARITÄT: je Szenario und Testdatei
  liefert Findling einen Treffer GENAU DANN, wenn die native Suche die Datei
  (per Namenssuche) dem Nutzer zeigt. Verglichen wird die Berechtigungsmenge
  in beide Richtungen (auch verpasste Treffer sind ein Fail), nicht Ranking
  oder Trefferzahl.
- **D-22:** Szenario 6 "eingeschränkter Nutzer" wird DOPPELT belegt: als
  CI-Szenario ein gruppenloser Minimal-Nutzer (keine Gruppen, kein
  Team-Folder-Zugang, genau ein empfangener View-only-Share, sieht nur diesen
  einen Inhalt); zusätzlich ein Gastnutzer über die guests-App als manuelle
  Probe vor der Einreichung (keine guests-Abhängigkeit in der CI-Matrix).

### Nachträge nach Research (Owner-Entscheide 03.09.2026)
- **D-23:** NC 35 kommt REIN: CI-Matrix wird NC 32+33+34+35, info.xml
  max-version 35. Betriebsversprechen auch auf NC 35 belegt.
- **D-24:** PHPUnit-Rückstand KOMPLETT abarbeiten: alle 12 dokumentierten,
  bisher ungetesteten Verhaltensweisen bekommen Tests in Phase 5
  (passt zu D-20 "alle Review-Reste" und zur Regel "Tests: alle Paths").
- **D-25:** Konflikt D-16/D-18 aufgelöst per ABSICHTSMARKE + occ findling:purge:
  Disable/Remove ohne Absicht lässt alle Daten liegen (D-16 bleibt wahr);
  Räumung läuft nur bei expliziter Absicht (--rm-data setzt die Marke für den
  repair-steps/uninstall-Lauf, alternativ räumt der Admin per occ
  findling:purge). Hintergrund: AppManager::disableApp() führt
  repair-steps/uninstall bereits beim DISABLE aus (NC 32/33/34, siehe
  05-RESEARCH.md).
- **D-26:** Release-Tag v1.0.0 wird ENDE PHASE 5 gesetzt; signierte Releases
  entstehen in Phase 5 ("einreichungsbereit" = ein Klick bis zur Abgabe).
  release.yml-Trigger auf v*-Tags ist hier gewollt. Die Einreichung selbst
  bleibt gebündelt nach Phase 6 (D-09 unverändert).
- **D-27 (Claude-Diskretion, analog Connector):** <donation>-Element kommt in
  den Store-Eintrag, gleicher Link wie beim MCP Connector
  (paypal.me/KhaledCherifDev).

### Claude's Discretion
- Konkreter Peak-RSS-Budgetwert (Größenordnung 2,5 GB) und Messwerkzeug/
  Messkadenz (z.B. cgroup memory.current-Sampling) auf der Box.
- Generator-Design des 50k-Lastkorpus (Dateiverteilung, Größenverteilung,
  Sprachen), solange deterministisch und reproduzierbar.
- Ausgestaltung der CI-Matrix (Job-Zuschnitt, Laufzeit-Budgets, welche der
  bestehenden Integrationsjobs die Matrix erben).
- Technischer Zuschnitt des Paritätstests (Fixture-Aufbau der 6 Szenarien,
  OCS-Suchaufrufe, Marker-Dateien) nach dem Vorbild der bestehenden
  Integrationsjobs.
- Uninstall-Implementierung im Detail (Migration/Repair-Step, was der
  Backend-Container bei --rm-data selbst entfernt).
- Reihenfolge der Arbeitspakete innerhalb der Phase.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap und Anforderungen
- `.planning/ROADMAP.md` — Phase-5-Ziel + 4 Erfolgskriterien (Kriterium 4 per D-09 als "einreichungsbereit" zu lesen)
- `.planning/REQUIREMENTS.md` — SRCH-04, PKG-03, PKG-04, PKG-05
- `.planning/PROJECT.md` — Constraints (4-8 GB RAM, ARM, NC 32-34 max 35, AGPL, Solo-Dev, Jahresende-Ziel), Key Decisions

### Phase-4-Erbe
- `.planning/phases/04-admin-sichtbarkeit-und-diagnose/deferred-items.md` — DI-04-03 + DI-04-04 (per D-19 in Phase 5 gezogen)
- `.planning/phases/04-admin-sichtbarkeit-und-diagnose/04-REVIEW.md` — Info-Findings IN-01..IN-07 (per D-20 inventarisieren)
- `.planning/phases/04-admin-sichtbarkeit-und-diagnose/04-SECURITY.md` — Threat-Register-Muster + T-04-64-Prüfsummen-Nachweis (Vorbild für Störfall-Drills)
- `.planning/phases/03-aktualit-t-und-ocr/03-CONTEXT.md` — Abschnitt "Aus den Phase-2-Audits in diese Phase verschoben" (Inventar-Startpunkt für D-20)

### Store und Signierung
- `docs/certificates.md` — Signing-Ablauf, Schlüsselablage ~/.findling-secrets/, Fingerprint-Verfahren
- `docs/store-identity.md` — eingefrorene App-IDs
- `.github/workflows/php.yml` — Store-Transform (APPSTORE_SHA gepinnt), XSD-Validierung, settings-Finding-Assertion
- Externes Vorbild: nextcloud-mcp-connector (Store-Listing EN/DE/FR, info.xml-Description-Regel, Release-Pipeline; Gotcha: leere info.xml-Elemente -> Store-500)

### Betrieb und Tests
- `docs/testing.md` — Gate-Landschaft (readonly-gate, Verdikt-Zähler, reconcile-and-dach), was jedes Gate beweist und was nicht
- `.github/workflows/integration.yml` — bestehender Aufbau (stable34), Basis für die 32/33/34-Matrix und den Paritätstest-Job
- `.github/workflows/docker.yml` — Multi-Arch-Build (arm64 nativ), Manifest-Prüfung
- `backend/tests/test_allowlist_parity.py` — bestehendes Paritäts-Testmuster (Namensgeber, anderer Gegenstand)
- `scripts/dev/build_corpus.py` — deterministisches Korpus-Prinzip (Vorbild für den 50k-Generator)
- `scripts/dev/compose.yaml` + `docs/dev-setup.md` — lokaler Stack (Port 8090, testuser-Korpus)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `readonly-gate`-CI-Job (integration.yml): frisst bereits Korpus + Prüfsummenvergleich; Muster für Störfall-Drills und die NC-Versionsmatrix.
- `docker.yml`: baut arm64 nativ (kein QEMU) und prüft das Manifest; das dev-Image kann direkt auf der CAX11 laufen.
- `build_corpus.py`: deterministische Datei-Generatoren für alle relevanten Typen inkl. kaputter PDFs; skalierbar zum Lastkorpus-Generator.
- Phase-4-Admin-Seite: zeigt Deckungsgrad/Fehlerliste/Diagnose; liefert die Screenshots-Motive (D-13) und die Beobachtbarkeit während des Lasttests.
- `occ findling:diagnose` + `occ findling:index --restart`: Betriebswerkzeuge für die Drills.

### Established Patterns
- Privacy-Vertrag Container->PHP (nur fileids/Zahlen/Codes) gilt unverändert für alles Neue.
- Nur-Lesen-Invariante: Gate A/B bleiben unverletzlich; die Schreib-Allowlist hat exakt drei Einträge (test_write_allowlist_has_exactly_three_entries) — Uninstall-Räumung im Container muss innerhalb dieser Disziplin bleiben bzw. als AppAPI-seitige Volume-Löschung laufen, nicht als neue Schreibroute.
- INDEX_WORKERS=1, Writer-Heap 50 MB: das RAM-Budget-Fundament, gegen das der Lasttest misst.
- Lockstep-Kompatibilität: /status kennt Versionsfelder (Phase 4); exakte Major.Minor-Prüfung dockt dort an.

### Integration Points
- integration.yml-Matrix (server-version heute ['stable34']) -> ['stable32','stable33','stable34'].
- Companion-Uninstall: Migration/Repair-Step in php/lib/Migration/ (D-18).
- info.xml beider Apps: Version, max-version 35, Store-Description EN/DE/FR (D-12); pre-info.xslt-Verhalten beachten (T-04-04-Akzeptanz).
</code_context>

<specifics>
## Specific Ideas

- Store-Zahl-Formulierung als Vertrauensanker: "Volllauf 50.000 Dateien auf einer 4-GB-ARM-Box, Peak-RSS X GB, ohne OOM" — ehrlich gemessen, mit verlinktem Messbericht.
- Store-Text-Vorbild ist das eigene MCP-Connector-Listing (EN/DE/FR, kein Backtick/Tabelle in der Description).
- Header-Bild nach der Bildpost-Linie des Owners: visuell-first, 1 Headline + 1 Zeile, Space Grotesk, echte SVGs, keine Emojis.

</specifics>

<deferred>
## Deferred Ideas

- Roadmap-Formal-Edit (Kriterium 4 auf "einreichungsbereit" umformulieren + gemeinsame Einreichung als Phase-6-Abschluss verankern): Owner hat den Edit JETZT nicht beauftragt; die Entscheidung ist hier in D-08/D-09 verbindlich festgehalten. Der Planner darf das Kriterium entsprechend interpretieren; ein formaler Roadmap-Edit kann beim plan-phase mitlaufen.
- MCP-Connector-Synergie sichtbar machen (Cross-Links, Content-Hit-Fidelity-Test, Store-Hinweise "works great with"): NACH der tatsächlichen v1.0-Einreichung, Trigger und Ablauf stehen im Connector-Backlog (BL-01..03) und im Memory.
- Launch-Kommunikation (Forum-Post, Announcements) gehört zur Einreichung nach Phase 6, nicht in Phase 5.

</deferred>

---

*Phase: 5-Härtung und Store-Einreichung v1.0*
*Context gathered: 2026-09-03*
