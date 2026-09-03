# Phase 5: Härtung und Store-Einreichung v1.0 - Research

**Researched:** 2026-09-03
**Domain:** Betriebsnachweis auf ARM-Hardware, AppAPI/HaRP-Deploy (compose + AIO), Rechte-Paritätstest gegen die native Nextcloud-Suche, Uninstall-Semantik von Nextcloud, App-Store-Einreichung
**Confidence:** HIGH für alles, was aus Nextcloud-Quellcode, der Store-XSD und dem eigenen Repo belegt ist. MEDIUM für Hetzner-Preise und Laufzeitschätzungen. LOW für den ARM-Geschwindigkeitsfaktor von Tesseract.

## Summary

Diese Phase hat vier Gegenstände, und drei davon sind grösser als sie im Kontext klingen. Erstens: **HaRP ist in diesem Repo noch nie gelaufen.** CI und lokale Entwicklung registrieren die ExApp bis heute als `manual-install`-Daemon mit einem Host-Prozess (`scripts/dev/register-exapp.sh:178`), das Laufzeitimage wird nur im Docker-Smoke-Test von `docker.yml` einzeln gestartet. PKG-03 verlangt aber "HaRP-Deploy auf docker-compose UND AIO getestet". Beide Beweise sind also Neubau, nicht Erweiterung einer Matrix. Zweitens: **Nextcloud führt die `repair-steps/uninstall` bereits beim DISABLE aus**, in NC 32, 33 und 34 gleichermassen (`AppManager::disableApp()`, im Quellcode aller drei Zweige gelesen). D-16 ("Disable lässt Index, Queue und Einstellungen liegen") und D-18 ("app:remove löscht via Uninstall-Step die Tabellen") widersprechen sich damit gegenseitig, sobald der Uninstall-Step unbedingt löscht. Drittens: **die Peak-RSS-Messung ist mit `docker stats` oder `memory.peak` nicht ehrlich messbar**, weil beide den Page-Cache des mmap-gelegten Tantivy-Index mitzählen; die belastbare Zahl ist `anon` aus `memory.stat`.

Der Paritätstest dagegen ist gut vorgezeichnet und billiger als erwartet: die native Suche ist der Provider `files`, ihr `term`-Filter ist wörtlich ein `LIKE '%term%'` auf der Spalte `name` über `$userFolder->search()`, und jeder Treffer trägt die `fileId` als Attribut. Die Vergleichsmenge ist damit eine Menge von fileids auf beiden Seiten, und die bestehenden Integrationsjobs liefern das ganze Gerüst (OCS-Aufrufe, Shares über die files_sharing-API, zwei Nutzer, zwei Dialekte). Die eine harte Falle: `SearchQuery::LIMIT_DEFAULT` ist **5**, gedeckelt auf 25 aus der App-Konfiguration. Ohne ausdrücklichen `limit`-Parameter vergleicht der Test zwei abgeschnittene Listen und wird grün, ohne etwas zu beweisen.

Store-seitig ist alles entblockt und die harten Grenzen sind bekannt: Archiv maximal 20 MB, `info.xml` unter 512 KB, Screenshots https und maximal 2 MiB, `POST /api/v1/apps/releases` mit `{download, signature, nightly}`, Beschreibung mehrsprachig über `lang="de"` und `lang="fr"` (nicht `de_DE`), Reihenfolge der Elemente ist eine XSD-`sequence` und `screenshot` gehört zwischen `repository` und `dependencies`.

**Primary recommendation:** Die Phase in vier Blöcke schneiden und den HaRP-Block zuerst bauen, weil alles andere daran hängt: (1) HaRP-Deploy in CI über NC 32/33/34 plus Uninstall-Semantik, (2) Paritätstest als eigener Job auf demselben Gerüst, (3) ARM-Lauf auf der CAX11 mit AIO-HaRP, Postgres und ehrlicher `anon`-Messung, (4) Store-Artefakte und Review-Reste. Den Peak-RSS-Grenzwert nicht auf 2,5 GB setzen, sondern das Gate auf 2,0 GB `anon` und die Store-Zahl auf den gemessenen Wert; 2,5 GB passen auf einer 4-GB-Box neben AIO nicht.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**ARM-Lasttest (Erfolgskriterium 1)**
- **D-01:** Zielhardware ist eine gemietete Hetzner CAX11 (Ampere ARM, 2 vCPU, 4 GB RAM, ~4 EUR/Monat). Claude bestellt sie im bestehenden Hetzner-Konto des Owners, dokumentiert die Kosten und löscht die Box nach abgeschlossenem Test. Da die CAX11 nur 40 GB Disk hat, wird ein Hetzner-Volume (~50 GB) angehängt.
- **D-02:** Lastkorpus ist SYNTHETISCH und deterministisch generiert (Prinzip von scripts/dev/build_corpus.py skaliert): ~50.000 Dateien / ~20 GB, Mix nach realer Verteilung (Text-PDFs, Scans, Office, Bilder), OCR-Anteil ~20 %. Keine echten Dokumente auf der Miet-Box. Implikation akzeptiert: Volllauf dauert auf 4-GB-ARM voraussichtlich 1 bis 2 Tage (OCR ist der Flaschenhals).
- **D-03:** Bestanden heisst: Volllauf OHNE OOM UND Container-Peak-RSS unter einem festen Budget. Budgetwert ist Claude-Diskretion (Grössenordnung 2,5 GB, damit Nextcloud+DB daneben Luft haben); die Zahl wird als dokumentierter Grenzwert Teil der Store-Aussage.
- **D-04:** Auf der Box läuft Nextcloud AIO + Findling via HaRP: der Lasttest erledigt damit zugleich den AIO-Deploy-Beweis aus PKG-03 auf der knappsten Zielumgebung. Der compose-Deploy-Beweis läuft separat in CI/lokal.
- **D-05:** Der ARM-Lauf spielt zusätzlich Kern-Störfälle real durch: docker kill mitten im OCR-Lauf + Neustart (Resume an der Zustandsmarke, IDX-02 auf echter Hardware), Backend-Offline-Probe (Suche degradiert sauber), Platte-fast-voll (paused_low_disk + Warnung sichtbar). Ergebnisse gehen in den Messbericht.
- **D-06:** Dokumentation der Messung: voller Bericht (Kurve, Methode, Korpus, Störfall-Drills) als docs/performance.md im Repo; verdichtete Kernaussage ("Volllauf 50k Dateien auf 4-GB-ARM, Peak X GB") in Store-Beschreibung und README.
- **D-07:** NC-Versionsmatrix: Install/Run/Uninstall läuft als CI-Matrix über Nextcloud 32 + 33 + 34 (bestehenden integration.yml-Aufbau erweitern, der heute auf stable34 läuft).

**Einreichung und Versionierung (Erfolgskriterium 4, GEÄNDERT)**
- **D-08:** BÜNDEL-EINREICHUNG: v1.0 (Volltext+OCR) wird NICHT allein eingereicht, sondern gemeinsam mit der Semantik aus Phase 6 als EIN Store-Erstrelease. Dieser Entscheid ersetzt den offenen PROJECT.md-Punkt "Release-Staffelung wird zur Einreichungs-Option".
- **D-09:** Phase 5 endet EINREICHUNGSBEREIT: signierte, XSD-validierte Release-Artefakte beider Apps, Store-Texte fertig, ein Klick bis zur Abgabe. Das Roadmap-Kriterium 4 ("liegt im Store") ist entsprechend als "einreichungsbereit" zu lesen; die tatsächliche Abgabe ist Abschluss von Phase 6. Implikation: die RSS-Store-Zahl wird nach Phase 6 mit aktiver Semantik erneut belegt (deckt sich mit dem Phase-6-Kriterium "im selben RAM-Budget").
- **D-10:** Deadline: Die GEMEINSAME Einreichung bleibt hart vor Jahresende 2026 (Phase 5 UND Phase 6 bis Dezember; Scope-Kürzung schlägt Termin). FALLBACK: Gefährdet Phase 6 das Ziel, wird doch gestaffelt eingereicht (v1.0 allein, v1.1 als Update).
- **D-11:** Versionierung LOCKSTEP: beide Apps (findling + findling_backend) tragen immer dieselbe Versionsnummer und werden paarweise released; exakte Major.Minor-Prüfung im Code. Das Store-Erstrelease heisst 1.0.0 (Semantik ist Teil der 1.0-Story: "Volltext + OCR + semantische Suche ab Tag 1").
- **D-12:** Store-Text dreisprachig EN/DE/FR (Muster nextcloud-mcp-connector inklusive Übersetzungs-Nachzieh-Regel) mit eigenem Privacy-Block: alles läuft lokal im Container, keine Inhalte verlassen den Server, kein Telemetrie-Phoning; Index at rest unverschlüsselt wird transparent benannt (Host-Sache). Die MCP-Connector-Synergie wird im Store-Text NICHT behauptet (erst nach bestandenem Content-Hit-Fidelity-Test, siehe Connector-Backlog). Vokabular-Gate für public Artefakte beachten.
- **D-13:** Store-Medien: Claude erstellt kuratierte Screenshots der echten UI via Playwright von der Dev-Instanz (Suche mit Treffern, Admin-Seite mit Deckungsgrad/Diagnose) plus ein schlichtes Header-Bild nach der Bildpost-Linie des Owners (visuell-first, Space Grotesk, echte SVG-Logos, keine Emojis).
- **D-14:** Zertifikats-Status GEKLÄRT (03.09. live geprüft): beide CSR-PRs (nextcloud/app-certificate-requests #1165 findling, #1166 findling_backend) am 19.08. gemergt, beide .crt liegen im appstore-Repo. Signieren ist entblockt; Schlüssel liegen in ~/.findling-secrets/ (docs/certificates.md).

**Uninstall-Cleanup (PKG-04, Erfolgskriterium 3)**
- **D-15:** Die Bestätigung fürs Löschen des Index-Volumes ist die AppAPI-Standardmechanik (ExApps-Admin-UI-Checkbox "Daten löschen" bzw. occ app_api:app:unregister --rm-data). KEIN Eigenbau-Dialog; die Doku erklärt, was --rm-data bei Findling konkret entfernt.
- **D-16:** DISABLE bedeutet: Suche aus, Index bleibt. Provider, Poller und Event-Verarbeitung stoppen; Index, Queue und Einstellungen bleiben liegen; Re-Enable ist sofort wieder suchfähig ohne Reindex (Tage OCR-Arbeit auf 4-GB-Boxen bleiben erhalten).
- **D-17:** Teilentfernung degradiert SANFT: ohne Backend zeigt die Companion-Seite den bestehenden "Backend nicht installiert"-Banner; ohne Companion läuft der Container leer weiter. Beide Fälle dokumentiert, empfohlene Deinstall-Reihenfolge in der Doku, kein erzwungener Kopplungszwang.
- **D-18:** Queue-Tabellen und Preferences (NC-DB, Besitz Companion) werden beim Companion-Remove entfernt: app:remove findling löscht via Uninstall-Step die eigenen Tabellen (Queue, Scan-Stats, File-State) und alle appconfig-Werte rückstandsfrei. Disable lässt alles liegen (D-16).

**Härtungs-Umfang**
- **D-19:** Beide Deferred Items aus Phase 4 gehören in Phase 5: DI-04-03 (Skip-Verdikte pro fileid an die NC-Seite übergeben, damit die Fehlerliste alle vier Gruppen zeigt und Sichtprobe-4 voll erfüllt ist) und DI-04-04 (Versionsmarken nach einem Rebuild neu stempeln, damit die dokumentierte Reindex-Banner-Abhilfe occ findling:index --restart das Banner wirklich löscht). Quelle: .planning/phases/04-admin-sichtbarkeit-und-diagnose/deferred-items.md.
- **D-20:** ALLE offenen Review-Reste aus früheren Phasen werden in Phase 5 abgearbeitet (Owner-Entscheid "Alles abarbeiten", bewusst gegen die schlankere Empfehlung): der Researcher inventarisiert unerledigte Mediums/Lows aus den Phase-2/3/4-Audits (u.a. die in 03-CONTEXT.md gelisteten M1/M2/M5/M8/M9 und Sec-L2/L4/L5/L6, soweit noch offen) und die Phase-4-Infos IN-01..IN-07 aus 04-REVIEW.md; der Planner plant sie ein. Spannungsfeld zur Dezember-Deadline ist durch den Staffelungs-Fallback (D-10) abgefedert.

**Paritätstest (SRCH-04, Erfolgskriterium 2)**
- **D-21:** Parität heisst SICHTBARKEITS-PARITÄT: je Szenario und Testdatei liefert Findling einen Treffer GENAU DANN, wenn die native Suche die Datei (per Namenssuche) dem Nutzer zeigt. Verglichen wird die Berechtigungsmenge in beide Richtungen (auch verpasste Treffer sind ein Fail), nicht Ranking oder Trefferzahl.
- **D-22:** Szenario 6 "eingeschränkter Nutzer" wird DOPPELT belegt: als CI-Szenario ein gruppenloser Minimal-Nutzer (keine Gruppen, kein Team-Folder-Zugang, genau ein empfangener View-only-Share, sieht nur diesen einen Inhalt); zusätzlich ein Gastnutzer über die guests-App als manuelle Probe vor der Einreichung (keine guests-Abhängigkeit in der CI-Matrix).

### Claude's Discretion
- Konkreter Peak-RSS-Budgetwert (Grössenordnung 2,5 GB) und Messwerkzeug/Messkadenz (z.B. cgroup memory.current-Sampling) auf der Box.
- Generator-Design des 50k-Lastkorpus (Dateiverteilung, Grössenverteilung, Sprachen), solange deterministisch und reproduzierbar.
- Ausgestaltung der CI-Matrix (Job-Zuschnitt, Laufzeit-Budgets, welche der bestehenden Integrationsjobs die Matrix erben).
- Technischer Zuschnitt des Paritätstests (Fixture-Aufbau der 6 Szenarien, OCS-Suchaufrufe, Marker-Dateien) nach dem Vorbild der bestehenden Integrationsjobs.
- Uninstall-Implementierung im Detail (Migration/Repair-Step, was der Backend-Container bei --rm-data selbst entfernt).
- Reihenfolge der Arbeitspakete innerhalb der Phase.

### Deferred Ideas (OUT OF SCOPE)
- Roadmap-Formal-Edit (Kriterium 4 auf "einreichungsbereit" umformulieren + gemeinsame Einreichung als Phase-6-Abschluss verankern): Owner hat den Edit JETZT nicht beauftragt; die Entscheidung ist hier in D-08/D-09 verbindlich festgehalten. Der Planner darf das Kriterium entsprechend interpretieren; ein formaler Roadmap-Edit kann beim plan-phase mitlaufen.
- MCP-Connector-Synergie sichtbar machen (Cross-Links, Content-Hit-Fidelity-Test, Store-Hinweise "works great with"): NACH der tatsächlichen v1.0-Einreichung, Trigger und Ablauf stehen im Connector-Backlog (BL-01..03) und im Memory.
- Launch-Kommunikation (Forum-Post, Announcements) gehört zur Einreichung nach Phase 6, nicht in Phase 5.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SRCH-04 | Berechtigungs-Parität: automatisierter Paritätstest gegen die native Nextcloud-Suche über 6 Rechteszenarien | Abschnitt "Pattern 2: Paritätstest gegen den Provider `files`"; verifizierte Fakten zu `FilesSearchProvider` (id `files`, `term` = `LIKE '%x%'` auf `name`, `fileId` als Attribut), `LIMIT_DEFAULT = 5`, Deckel `unified_search_max_results_per_request = 25`; groupfolders-occ-Befehle für Szenario 4; guests 4.9.0 für NC 32-34 für die manuelle Probe |
| PKG-03 | Lauffähig auf 4-GB-ARM (Lasttest belegt), NC 32-34 (max-version 35), HaRP-Deploy auf docker-compose UND AIO getestet | Abschnitt "Pattern 1: HaRP-Deploy"; AIO registriert `harp_aio` selbst (Quellcode `AIODockerActions::registerAIOHarpDaemonConfig`), beide HaRP-Images sind arm64, `app_api` hat stable32/33/34-Zweige, PHP-Untergrenzen 8.1/8.2/8.2; Messmethode `memory.stat anon` statt `docker stats`; Korpus- und Laufzeitrechnung |
| PKG-04 | Uninstall-Cleanup: Unregister entfernt Queue-Tabellen, Preferences und (nach Bestätigung) das Index-Volume | Abschnitt "Pitfall 1: Uninstall-Repair-Steps laufen beim Disable"; `app_api:app:unregister --rm-data` im Quellcode gelesen, Daten bleiben ohne Flag erhalten; "Delete data on remove" existiert in NC 32/33, fehlt in NC 34; `IAppConfig::deleteApp()` (@since 29) und `IDBConnection::dropTable()` (@since 8) |
| PKG-05 | v1.0-Store-Einreichung vor Jahresende 2026; signierte Releases, info.xml XSD-validiert | Abschnitt "Store-Einreichung"; `POST /api/v1/apps/releases`, 20-MB-Archivgrenze, info.xml < 512 KB, Screenshot https und 2 MiB, XSD-Elementreihenfolge, `lang`-Codes `de`/`fr`, semver-Muster; php.yml validiert beide info.xml schon auf dem echten Store-Pfad |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| HaRP-Deploy-Beweis (compose) | CI-Runner (GitHub Actions) | HaRP-Container | Der Beweis muss wiederholbar sein, also gehört er in einen Job und nicht auf eine Box |
| HaRP-Deploy-Beweis (AIO) | Miet-Hardware (CAX11) | AIO-Mastercontainer | Die HaRP-Container-Wahl in AIO ist ein Klick in der AIO-Weboberfläche, nicht per env steuerbar |
| NC-Versionsmatrix 32/33/34 | CI-Runner | Composite Action `setup-test-nc` | Server- und app_api-Zweig sind schon Eingaben der Action; die Matrix erbt sie |
| Sichtbarkeits-Parität | Nextcloud/PHP-Tier | CI-Runner als Fahrer | Die Sicherheitsgrenze ist der PHP-Recheck; der Vergleich muss deshalb über die echte OCS-Route beider Provider laufen |
| Peak-RSS-Messung | Host der Box (cgroup v2) | ExApp-Container | Nur der Host sieht die cgroup des Containers vollständig; die Zahl darf nicht aus dem Container selbst behauptet werden |
| Störfall-Drills (kill, offline, Platte voll) | Miet-Hardware | Vorbild `resilience.yml` kill-resume | D-05 verlangt sie auf echter Hardware; der CI-Job bleibt als Regressionsgate bestehen |
| Uninstall-Räumung der NC-Tabellen | Nextcloud/PHP-Tier (Companion) | Nextcloud AppManager | Die Tabellen gehören der PHP-Hälfte; der Container darf keine NC-DB anfassen |
| Uninstall-Räumung des Index-Volumes | AppAPI/Deploy-Daemon | ExApp-Container | Das Volume ist AppAPI-Besitz; eine eigene Schreibroute im Container würde die Nur-Lesen-Allowlist aufweichen |
| Lockstep-Versionsprüfung zur Laufzeit | Nextcloud/PHP-Tier | ExApp-Container (`/status`) | Der Companion kennt seine eigene Version über `IAppManager::getAppVersion` und muss die Gegenseite fragen |
| Store-Metadaten und Signatur | Repo + Release-Automation | apps.nextcloud.com | Signatur nur über das Artefakt, das auch veröffentlicht wird |
| Store-Medien (Screenshots, Header) | Dev-Instanz + Repo | raw.githubusercontent.com als https-Host | Der Store speichert nur URLs, keine Bilder |

## Standard Stack

Diese Phase führt **keine neue Bibliothek** ein. Was sie braucht, ist entweder schon gepinnt oder ist ein Werkzeug der Zielplattform.

### Core (alles bereits im Projekt)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pillow | wie gepinnt in backend/pyproject.toml | Glyphen für die Scan-Seiten des Lastkorpus | `scripts/dev/build_corpus.py` nutzt sie schon, mit SHA-256-geprüfter DejaVu-Schrift; kein neuer Abhängigkeitsposten [VERIFIED: scripts/dev/build_corpus.py:64, :493] |
| stdlib (`zipfile`, `zlib`, `struct`, `hashlib`) | Python 3.13 | PDF-, DOCX-, ODT-Erzeugung im Generator | Der bestehende Generator ist bewusst stdlib-first; der 50k-Generator erbt das [VERIFIED: scripts/dev/build_corpus.py:55-62] |
| pytest | wie gepinnt | Textuelle Gates (Gate A/B/C, Paritätsgates) | Alle PHP-Gates dieses Projekts sind Python-Tests über PHP-Quellen [CITED: docs/testing.md] |

### Supporting (Zielplattform-Werkzeuge, keine Projekt-Abhängigkeit)
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| `ghcr.io/nextcloud/nextcloud-appapi-harp:release` | release-Tag | HaRP-Deploy-Daemon für compose und CI | Manifest trägt linux/amd64 UND linux/arm64 [VERIFIED: docker manifest inspect, 2026-09-03] |
| `ghcr.io/nextcloud-releases/aio-harp` | AIO-Kanal | HaRP-Container innerhalb von AIO | Manifest trägt amd64 und arm64 [VERIFIED: docker manifest inspect, 2026-09-03] |
| `groupfolders` | 20.1.9 (NC 32) / 21.0.9 (NC 33) / 22.0.6 (NC 34) | Team-Folder-Szenario des Paritätstests | Über `occ app:install groupfolders` beziehbar, für alle drei Zielversionen vorhanden [VERIFIED: apps.nextcloud.com/api/v1/platform/{32,33,34}.0.0/apps.json] |
| `guests` | 4.9.0 (für 32, 33 und 34 identisch) | Gastnutzer-Probe aus D-22, manuell | Vorhanden für alle drei Versionen [VERIFIED: apps.nextcloud.com apps.json] |
| Hetzner Cloud REST API (curl) | v1 | CAX11 und Volume bestellen, Kosten belegen, Box löschen | Die `hcloud`-CLI (v1.67.0, 2026-07-24) ist NICHT installiert; curl gegen `https://api.hetzner.cloud/v1` braucht nur `HCLOUD_TOKEN` und keinen neuen Binärdownload [VERIFIED: `command -v hcloud` leer; github.com/hetznercloud/cli releases] |
| `openssl dgst -sha512 -sign` | System-OpenSSL | Store-Release-Signatur | Vom Store vorgeschrieben [CITED: nextcloud/appstore docs/developer.rst] |
| `occ integrity:sign-app` | NC 32-34 | Signatur IM Archiv (signature.json) | Anderer Gegenstand als die Store-Signatur, siehe Pitfall 8 [CITED: docs/certificates.md] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| curl gegen die Hetzner-API | `hcloud`-CLI installieren | Bequemer, aber ein neuer Binärdownload auf der Entwicklungsmaschine für drei API-Aufrufe; curl reicht und lässt sich im Messbericht wörtlich zitieren |
| `memory.stat`-`anon`-Sampling | `docker stats --no-stream` (wie in resilience.yml) | `docker stats` rechnet `memory.current` minus `inactive_file`; der AKTIVE File-Cache des mmap-Index bleibt drin und würde die Zahl um Gigabyte verfälschen. Für die bestehende CI-Messung (leerer Index) ist es in Ordnung, für den 20-GB-Lauf nicht |
| `memory.peak` | `memory.stat`-Sampling | `memory.peak` ist bequem (ein Wert, kein Sampler), enthält aber Page-Cache. Beide erheben und beide dokumentieren, die Store-Zahl aus `anon` |
| Lokale Registry in CI | Image nach ghcr pushen und von dort ziehen | Ein Push je CI-Lauf ist teuer und verschmutzt die Registry; `registry:2` auf `localhost:5000` plus ein `<registry>`-Ersatz in einer temporären info.xml ist reproduzierbar und offline |
| Postgres in die CI-Matrix | Nur der ARM-Lauf beweist Postgres | Ein einziger Lauf auf einer Miet-Box ist kein Dauergate. Empfehlung: `pgsql` als dritter Matrix-Eintrag von `index-search-e2e`, weil AIO Postgres fährt und der Perf-Befund M7 ausdrücklich einen Postgres-spezifischen Transaktionsbruch benennt |

**Installation:** Keine. Der einzige neue Paketbezug ist ein `occ app:install groupfolders` INNERHALB der CI-Instanz, also ein Nextcloud-App-Store-Bezug, kein Sprachpaket.

## Package Legitimacy Audit

Diese Phase installiert **keine** externen Sprachpakete (kein npm, kein PyPI, kein crates.io). Der Lastkorpus-Generator läuft auf stdlib plus dem bereits gepinnten Pillow, die Paritäts- und Deploy-Gates auf dem bereits gepinnten pytest, und die Store-Signatur auf System-OpenSSL.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| *(keine neuen Pakete)* | - | - | - | - | nicht nötig | - |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

Zwei Bezüge sind trotzdem Fremdcode und gehören in die Prüfung des Planners:

| Bezug | Art | Prüfform |
|-------|-----|----------|
| `groupfolders` aus dem Nextcloud App Store | PHP-App in der CI-Instanz | Nur in CI, nie im Release; die drei Versionen sind über die Store-API bestätigt. Die App ist ein Nextcloud-GmbH-Repo (`nextcloud/groupfolders`) [VERIFIED: apps.nextcloud.com, github.com/nextcloud/groupfolders] |
| `ghcr.io/nextcloud/nextcloud-appapi-harp:release` | Container-Image | `release` ist ein beweglicher Tag. Für CI und für die Box auf **Digest** pinnen, wie es der Dockerfile-Basisimage-Digest im Projekt schon tut, sonst ändert ein Upstream-Push die Bedeutung des Deploy-Beweises |

*slopcheck ist auf dieser Maschine installiert (`/c/Users/Student/.local/bin/slopcheck`) und wurde nicht gebraucht, weil die Paketliste leer ist.*

## Architecture Patterns

### System Architecture Diagram

```
                    ┌─────────────────────── Phase-5-Beweisketten ───────────────────────┐

(A) CI-Runner (GitHub Actions, ubuntu-24.04)
    │
    ├─ setup-test-nc (composite)  ──► nextcloud/server @ stable32|33|34
    │      │                          app_api        @ stable32|33|34
    │      └─ php -S 0.0.0.0:8080  (PHP_CLI_SERVER_WORKERS>=4)
    │
    ├─[NEU]─ registry:2 @ localhost:5000  ◄── docker build ./backend
    │
    ├─[NEU]─ appapi-harp container  ──(/var/run/docker.sock)──► Docker Engine
    │            │  :8780 http    :8782 frp
    │            ▼
    │      occ app_api:daemon:register  ... --harp --harp_shared_key ... --net host
    │      occ app_api:app:register findling_backend <daemon> --info-xml <tmp/info.xml>
    │            │                                  (registry auf localhost:5000 ersetzt)
    │            ▼
    │      HaRP zieht Image ──► erzeugt ExApp-Container ──► Handshake /init /heartbeat
    │            │
    │            ├─► Suche:  Browser/curl ─► /ocs/v2.php/search/providers/findling/search
    │            │              └─ Provider.php ─► exAppRequest ─► HaRP ─► ExApp /search
    │            │                                   └─ PHP-Recheck (Sicherheitsgrenze)
    │            │
    │            └─► Uninstall: occ app_api:app:unregister findling_backend --rm-data
    │                           occ app:remove findling      (Uninstall-Repair-Step)
    │
    └─[NEU]─ Paritätsjob:
             Fixtures (6 Szenarien) ─► occ files:scan ─► Index abwarten
                     │
                     ├─► GET .../providers/files/search?term=<marker>&limit=N     ──► Menge N_files
                     └─► GET .../providers/findling/search?term=<marker>&limit=N  ──► Menge N_findling
                                                    │
                                          Vergleich beider fileid-Mengen,
                                          symmetrisch (Diff in beide Richtungen)

(B) Hetzner CAX11 (arm64, 2 vCPU, 4 GB, 40 GB root + 50 GB Volume)
    │
    ├─ Docker data-root und NEXTCLOUD_DATADIR auf /mnt/<volume>
    │
    ├─ AIO-Mastercontainer :8080/:8443  ──(Weboberfläche über SSH-Tunnel)──►
    │      └─ optionale Container: NUR "HaRP" an, alles andere aus
    │             │
    │             ├─ nextcloud-aio-apache :443
    │             ├─ nextcloud-aio-nextcloud (php-fpm)
    │             ├─ nextcloud-aio-postgresql   ◄── ERSTER Postgres-Lauf des Projekts
    │             ├─ nextcloud-aio-redis
    │             └─ nextcloud-aio-harp  :8780 (im Netz "nextcloud-aio")
    │                    │
    │                    └─ AppAPI registriert Daemon "harp_aio" SELBST
    │                          (THIS_IS_AIO + HARP_ENABLED=yes + HP_SHARED_KEY)
    │                          └─► ExApp-Container findling_backend
    │
    ├─ Lastkorpus: build_load_corpus.py --seed ... --files 50000 --bytes 20G
    │      └─ direkt in <datadir>/<user>/files, chown 33:33, dann occ files:scan
    │
    └─ Messung (Host):  Sampler alle 5 s
           /sys/fs/cgroup/system.slice/docker-<id>.scope/memory.stat  ─► anon (Wahrheit)
           .../memory.peak, .../memory.current                        ─► Kontext
           .../memory.events                                          ─► oom, oom_kill == 0
           docker inspect .State.OOMKilled                            ─► false
                     │
                     ▼
              docs/performance.md  ──verdichtet──►  info.xml description (EN/DE/FR) + README

(C) Store-Strecke
    php/appinfo/info.xml  ─┐
    backend/appinfo/info.xml ┴─► xsltproc pre-info.xslt ─► xmllint --schema info.xsd  (php.yml, existiert)
                                │
    git tag v1.0.0 ─────────────┴─► docker.yml: tag == beide <version> == <image-tag>
                                │
    tar.gz (ein Top-Level-Ordner) ─► occ integrity:sign-app (signature.json IM Archiv)
                                   ─► openssl dgst -sha512 -sign KEY | openssl base64  (Store-Signatur)
                                   ─► GitHub Release (https-Download, < 20 MB)
                                   ─► POST /api/v1/apps/releases {download, signature}   [Phase 6]
```

### Recommended Structure der neuen Artefakte

```
.github/workflows/
├── integration.yml            # erbt die 32/33/34-Matrix; neuer Job "search-parity"
└── deploy-harp.yml    [NEU]   # HaRP-Deploy: install, run, uninstall, ueber NC 32/33/34
.github/actions/
└── setup-test-nc/action.yml   # erweitern: pdo_pgsql, php -S auf 0.0.0.0, groupfolders optional
scripts/
├── dev/
│   ├── build_load_corpus.py   [NEU] deterministischer 50k/20GB-Generator
│   └── compose-harp.yaml      [NEU] compose-Stack MIT HaRP (der heutige ist manual-install)
└── ops/                       [NEU]
    ├── hetzner_box.sh         [NEU] Box + Volume anlegen, Kosten ausgeben, loeschen
    └── rss_sampler.sh         [NEU] cgroup-v2-Sampler, CSV nach stdout
docs/
├── performance.md             [NEU] D-06: Kurve, Methode, Korpus, Drills, Grenzwert
├── uninstall.md               [NEU] D-15/D-17: was --rm-data entfernt, Reihenfolge, Teilentfernung
└── store-listing.md           [NEU] D-12: die drei Sprachfassungen als Quelle der info.xml-Texte
php/lib/
├── Migration/UninstallStep.php[NEU] oder Repair/AppUninstallStep.php (siehe Pitfall 1)
└── Service/ExAppService.php   erweitern: Major.Minor-Lockstep-Pruefung (D-11)
backend/src/findling/
└── api/status.py              erweitern: eigene App-Version aus APP_VERSION melden (D-11)
backend/tests/
├── test_store_metadata.py     [NEU] Gate: em-dash/Emoji/Umlaute/Laenge in beiden info.xml
└── test_lockstep_versions.py  [NEU] Gate: beide <version> und <image-tag> identisch
```

### Pattern 1: HaRP-Deploy statt manual-install

**What:** Ein Deploy-Daemon mit `accepts-deploy-id = docker-install` und dem Flag `--harp`, der das Laufzeitimage aus einer Registry zieht und den ExApp-Container selbst erzeugt. Das ist der Weg, den eine Store-Installation nimmt, und der Weg, den PKG-03 verlangt.

**When to use:** Für jeden Beweis, der eine Aussage über die Installation trifft. `manual-install` beweist die HTTP-Schnittstelle und die Signaturköpfe, aber nicht das Image, nicht das Volume, nicht die Routenliste aus dem Archiv und nicht den Uninstall.

**Warum das hier Neubau ist:** `scripts/dev/register-exapp.sh:178-181` registriert `"Manual Install" manual-install http`, und `.github/actions/setup-test-nc/action.yml:214` tut dasselbe. Kein Job dieses Repos hat HaRP je gestartet.

**Example (host-Modus, der für den CI-Runner passende):**
```bash
# Source: nextcloud/app_api lib/Command/Daemon/RegisterDaemon.php, addUsage-Zeile 2
docker run -d --name appapi-harp -h appapi-harp \
  -e HP_SHARED_KEY="$HARP_KEY" \
  -e NC_INSTANCE_URL="http://localhost:8080" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD/certs:/certs" \
  -p 8780:8780 -p 8782:8782 \
  ghcr.io/nextcloud/nextcloud-appapi-harp@sha256:<digest>

./occ app_api:daemon:register \
  harp_proxy_host "Harp Proxy (Host)" "docker-install" "http" "localhost:8780" \
  "http://localhost:8080" \
  --harp --harp_frp_address "localhost:8782" --harp_shared_key "$HARP_KEY" \
  --net host --set-default

./occ app_api:app:register findling_backend harp_proxy_host \
  --info-xml "$RUNNER_TEMP/info-local-registry.xml" --wait-finish
```

`--net host` ist hier der Trick, der die Rückrichtung löst: der ExApp-Container teilt den Netz-Namensraum des Runners und erreicht damit `localhost:8080`, wo `php -S` hört. Ohne `--net host` müsste der Runner-Server auf `0.0.0.0` binden und die Instanz-URL auf die Bridge-Adresse zeigen, mit `trusted_domains` und `overwrite.cli.url` im Schlepptau. `--net` hat den Vorgabewert `host` [VERIFIED: RegisterDaemon.php:42].

### Pattern 2: Paritätstest gegen den Provider `files`

**What:** Zwei OCS-Aufrufe pro Szenario und Marker, beide als derselbe Nutzer, beide mit ausdrücklichem `limit`, und ein symmetrischer Mengenvergleich der `fileId`-Attribute.

**Die verifizierten Grundlagen:**
- Provider-Id der nativen Dateisuche ist `files`, in NC 32 und NC 34 identisch [VERIFIED: apps/files/lib/Search/FilesSearchProvider.php:51]
- Der `term`-Filter wird wörtlich zu `new SearchComparison(ISearchComparison::COMPARE_LIKE, 'name', '%' . $filter->get() . '%')` und läuft über `$userFolder->search($fileQuery)` [VERIFIED: FilesSearchProvider.php:110-152]. Die native Suche ist also eine Namenssuche über die Sichtbarkeitsmenge des Nutzers, genau wie D-21 es annimmt.
- Jeder Treffer trägt `$searchResultEntry->addAttribute('fileId', (string)$result->getId())` [VERIFIED: FilesSearchProvider.php:138]. Der Vergleich braucht keine Titel und keine Pfade.

**Fixture-Regel, die daraus folgt:** Ein Marker-Token muss **im Dateinamen UND im Inhalt** stehen. Die native Seite sieht nur den Namen, Findling nur den Inhalt (plus den Namen). Ein Marker nur im Inhalt macht die native Seite blind und den Test wertlos; ein Marker nur im Namen macht Findling blind und erzeugt einen Fehlalarm. Marker in Kleinbuchstaben und ASCII halten: `LIKE` ist auf SQLite ASCII-case-insensitive und auf MariaDB collation-abhängig, ein Umlaut im Marker macht die Parität zu einer Collation-Frage.

**Example:**
```bash
# Source: bestehendes Muster aus .github/workflows/integration.yml:1021 ff.
ask() {  # $1 provider, $2 user, $3 pass, $4 term, $5 out
  curl -sf -u "$2:$3" -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
    --get --data-urlencode "term=$4" --data-urlencode 'limit=100' \
    "http://localhost:8080/ocs/v2.php/search/providers/$1/search" -o "$5"
}
ids() { python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))['ocs']['data']
print('\n'.join(sorted(e['attributes']['fileId'] for e in d['entries'])))
" "$1"; }

# Vor dem ersten Aufruf: den Deckel hochsetzen, sonst schneidet der Server ab.
./occ config:app:set core unified_search_max_results_per_request --value=100
```

**Anti-Pattern, das hier tödlich ist:** ohne `limit` zu fragen. `SearchQuery::LIMIT_DEFAULT` ist **5** [VERIFIED: lib/private/Search/SearchQuery.php:16], und der Serverdeckel `unified_search_max_results_per_request` ist **25** [VERIFIED: core/AppInfo/ConfigLexicon.php:99, in stable32, 33 und 34 identisch]. Zwei auf fünf Einträge gekürzte Listen sind fast immer gleich und beweisen nichts.

**Szenario-Aufbau (die sechs aus SRCH-04, mit den verifizierten Befehlen):**

| # | Szenario | Aufbau |
|---|----------|--------|
| 1 | Eigene Dateien | `occ user:add`, Korpusteil ins Home, `occ files:scan` |
| 2 | Empfangener Share | `POST /ocs/v2.php/apps/files_sharing/api/v1/shares` (Muster liegt in integration.yml:954) |
| 3 | Entzogener Share | `DELETE /ocs/v2.php/apps/files_sharing/api/v1/shares/{id}`, danach beide Seiten erneut fragen |
| 4 | Team Folder | `occ app:install groupfolders` + `occ app:enable groupfolders`, dann `occ groupfolders:create <name>`, `occ groupfolders:group <id> <gruppe> read write` [VERIFIED: nextcloud/groupfolders lib/Command/Create.php:28, Group.php:42] |
| 5 | Gruppenwechsel | `occ group:adduser` / `occ group:removeuser`, danach erneut fragen. Achtung: das ACL-Vorfilter-Update kommt über die Share-Ereignisse und den Teilbaum-Job, nicht sofort |
| 6 | Eingeschränkter Nutzer (CI) | Nutzer ohne jede Gruppe, ein einziger View-only-Share (`permissions=1`), kein Team-Folder-Zugang |
| 6b | Gastnutzer (manuell) | `occ app:install guests` (4.9.0 für 32-34), Gast anlegen, dieselbe Vergleichsprozedur von Hand |

### Pattern 3: Ehrliche Speichermessung auf cgroup v2

**What:** Ein Sampler auf dem Host, der `memory.stat` liest und `anon` als Wahrheit nimmt, `memory.peak`/`memory.current` als Kontext protokolliert und `memory.events` als OOM-Beweis.

**Why:** `memory.current` ist laut Kernel-Dokumentation "the total amount of memory currently being used by the cgroup and its descendants" und rechnet ausdrücklich "page cache and anonymous memory" zusammen; `memory.peak` ist "the max memory usage recorded for the cgroup" auf derselben Grundlage [CITED: docs.kernel.org/admin-guide/cgroup-v2.html]. Der Tantivy-Index liegt als mmap auf der Platte, also wandert jeder gelesene Indexblock in den File-Cache derselben cgroup. Auf einem 20-GB-Korpus ist der File-Cache der grösste Posten und gleichzeitig vollständig rückgewinnbar. Eine Store-Aussage aus `memory.peak` wäre falsch und würde die App schlechter darstellen als sie ist.

`anon` ist "amount of memory used in anonymous mappings such as brk(), sbrk(), and mmap(MAP_ANONYMOUS)" [CITED: dieselbe Quelle], also genau der Heap, den INDEX_WORKERS=1, der Writer-Heap und Tesseract erzeugen.

**Example:**
```bash
# Source: Kernel-Doku cgroup-v2, Interface-Dateien memory.stat / memory.events
cg=/sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' nc-app-findling_backend).scope
while :; do
  awk -v t="$(date +%s)" '
    $1=="anon"{a=$2} $1=="file"{f=$2} $1=="slab"{s=$2}
    END{printf "%s,%d,%d,%d\n", t, a, f, s}' "$cg/memory.stat"
  sleep 5
done | tee rss.csv
# Abschluss:
cat "$cg/memory.peak" "$cg/memory.current"
cat "$cg/memory.events"                      # oom 0, oom_kill 0
docker inspect -f '{{.State.OOMKilled}}' nc-app-findling_backend   # false
```

Zwei Robustheitshinweise: der cgroup-Pfad hängt am Cgroup-Treiber. Mit dem systemd-Treiber (Vorgabe auf Ubuntu 24.04) ist es `system.slice/docker-<id>.scope`, mit `cgroupfs` ist es `/sys/fs/cgroup/docker/<id>`. Der Sampler soll beide Formen probieren und beim Fehlschlag abbrechen statt Nullen zu schreiben. Und: der Containername, den AppAPI baut, kommt aus `buildExAppContainerName($appId)`; er ist im Skript nicht zu raten, sondern per `docker ps --filter` nach der Registrierung zu ermitteln.

**Zusätzlicher Beweis, der stärker ist als eine Beobachtung:** nach der Registrierung `docker update --memory=2g --memory-swap=2g <container>` setzen und den Volllauf unter der harten Grenze fahren. Ein Lauf, der unter `memory.max` durchläuft, ist ein belastbarer Satz; ein beobachteter Spitzenwert ist nur eine Momentaufnahme. AppAPI kennt `resourceLimits.memory` nur im Deploy-Config eines Daemons und nicht als occ-Option [VERIFIED: DockerActions.php:591, RegisterDaemon.php ohne entsprechende Option], deshalb ist `docker update` auf der Box der praktikable Weg.

### Pattern 4: Store-Beschreibung dreisprachig, in XSD-Reihenfolge

**What:** Je Sprache ein eigenes Element, `lang`-Attribut aus der 84-Werte-Enumeration der XSD.

**Die harten Regeln aus der gepinnten XSD (APPSTORE_SHA 5c4373d7):**
- Reihenfolge ist eine `xs:sequence`: `id, name+, summary+, description+, version, licence+, author+, namespace?, types?, documentation?, category+, website?, discussion?, bugs, repository?, screenshot{0,10}, donation{0,10}, dependencies, background-jobs?, repair-steps?, two-factor-providers?, commands?, settings?, ... , external-app?` [VERIFIED: info.xsd:11-78]
- `name` und `summary` sind `l10n-string`, also **maximal 128 Zeichen**; `description` ist `l10n-text` ohne Längengrenze [VERIFIED: info.xsd:120-135]
- `lang` akzeptiert `de`, `fr`, `en`. **`de_DE` ist NICHT in der Liste** [VERIFIED: 84 Enumerationswerte in info.xsd]
- Je Element-Art muss `@lang` eindeutig sein (`uniqueNameL10n`, `uniqueSummaryL10n`, `uniqueDescriptionL10n`) [VERIFIED: info.xsd:81-92]
- `description` ist `non-empty-string`: ein leeres Element fällt durch [VERIFIED: info.xsd:17, :129]
- `screenshot` ist eine `secure-url`: `https://.+`, **maximal 256 Zeichen** [VERIFIED: info.xsd:301-310, secure-url]
- `version` ist semver ohne Build-Metadaten: `(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?` [VERIFIED: info.xsd semver]

**Example:**
```xml
<!-- Source: gepinnte info.xsd des Store, Reihenfolge und Typen wie oben -->
<name>Findling</name>
<name lang="de">Findling</name>
<name lang="fr">Findling</name>
<summary>Zero-config full text search for your files</summary>
<summary lang="de">Volltextsuche für Ihre Dateien, ohne Konfiguration</summary>
<summary lang="fr">Recherche plein texte pour vos fichiers, sans configuration</summary>
<description><![CDATA[...]]></description>
<description lang="de"><![CDATA[...]]></description>
<description lang="fr"><![CDATA[...]]></description>
```

Die Beschreibung darf Markdown enthalten [CITED: nextcloud/appstore docs/developer.rst]. Aus dem Schwesterprojekt gilt: keine Backticks und keine Tabellen in der Description, weil der Store sie nicht so rendert, wie es im Repo aussieht.

### Anti-Patterns to Avoid

- **Uninstall-Repair-Step, der unbedingt löscht.** Läuft beim Disable mit. Siehe Pitfall 1, es ist der wichtigste Befund dieser Recherche.
- **Der Paritätstest vergleicht Trefferzahlen.** D-21 sagt Mengen, und zwar symmetrisch. Eine gleiche Anzahl bei unterschiedlichen Dateien ist ein Fehlschlag, der als Erfolg gelesen würde.
- **Die Store-Zahl aus `docker stats` oder `memory.peak`.** Siehe Pattern 3.
- **HaRP-Image über den `release`-Tag beziehen.** Ein beweglicher Tag macht den Deploy-Beweis unwiederholbar. Auf Digest pinnen, wie das Basisimage im Dockerfile.
- **Die 32/33/34-Matrix auf alle vier Integrationsjobs legen.** `readonly-gate` und `index-search-e2e` dauern schon je 45 Minuten; drei Serverversionen mal zwei Dialekte mal OCR-Lauf sprengt jedes Feedback-Fenster. Die Matrix gehört auf den neuen, schlanken Deploy-Job (install/run/uninstall) und auf `walking-skeleton`; die teuren Jobs behalten stable34 und laufen zusätzlich als `schedule` über die Matrix. Der Kommentar in integration.yml:101 nimmt genau diese Aufteilung vorweg.
- **Screenshots aus der CI-Instanz.** Die CI-Instanz hat 33 Korpusdateien mit Namen wie `09-bescheid.pdf` und sechs absichtlich kaputten PDFs. Ein Store-Screenshot davon ist ehrlich, aber unattraktiv. D-13 nennt die Dev-Instanz, und das ist richtig.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bestätigung fürs Löschen des Index-Volumes | Eigener Dialog auf der Admin-Seite | `occ app_api:app:unregister --rm-data` bzw. die AppAPI-Oberfläche | D-15; das Volume gehört AppAPI, und die Löschung läuft über `dockerActions->removeExApp(..., removeData: true)` bzw. `removeVolume(buildExAppVolumeName($appId))` [VERIFIED: app_api lib/Command/ExApp/Unregister.php:106, :135-139] |
| appconfig-Werte einzeln löschen | Schleife über alle bekannten Schlüssel | `IAppConfig::deleteApp(string $app)` | @since 29.0.0, also im ganzen Fenster 32-35 verfügbar; eine Schleife über bekannte Schlüssel lässt genau die Schlüssel liegen, die eine spätere Version hinzufügt [VERIFIED: lib/public/IAppConfig.php:522] |
| Tabellen löschen | Rohes `DROP TABLE` per SQL | `IDBConnection::tableExists()` + `IDBConnection::dropTable()` | @since 8.0.0, dialektneutral, und `tableExists` macht den Schritt idempotent, was er sein MUSS (siehe Pitfall 1) [VERIFIED: lib/public/IDBConnection.php:310, :335] |
| ARM-Box bestellen | Eigene Terraform-/Ansible-Strecke | Drei curl-Aufrufe gegen `api.hetzner.cloud/v1` (`POST /servers`, `POST /volumes`, `DELETE /servers/{id}`) | Für eine Box, die nach dem Test gelöscht wird, ist Infrastruktur-als-Code Ballast; die Aufrufe gehören wörtlich in den Messbericht |
| Deterministischer Lastkorpus | Neues Generator-Framework | `scripts/dev/build_corpus.py` als Vorlage skalieren | Der bestehende Generator hat schon PDF-, DOCX-, ODT- und Scan-Erzeugung, eine SHA-256-geprüfte Schrift und einen Glyph-Assert; er braucht nur einen Seed, eine Verteilung und eine Mengensteuerung [VERIFIED: scripts/dev/build_corpus.py, 1181 Zeilen] |
| Store-Signatur | Eigene Signaturberechnung | `openssl dgst -sha512 -sign KEY ARCHIVE \| openssl base64` | Vom Store wörtlich vorgegeben; jede Abweichung endet in "Invalid signature" ohne Hinweis, welche Hälfte falsch war [CITED: nextcloud/appstore docs/developer.rst] |
| Archiv-Signatur im Tarball | Selbst gebaute signature.json | `occ integrity:sign-app` | Anderes Verfahren, anderer Zweck, schon dokumentiert [CITED: docs/certificates.md] |
| OOM-Nachweis | Log nach "Killed" durchsuchen | `memory.events` (`oom`, `oom_kill`) plus `docker inspect .State.OOMKilled` | Der Kernel führt die Zähler selbst; eine Textsuche im Log findet den Fall nicht, in dem ein Kindprozess der cgroup getötet wurde |

**Key insight:** Fast alles, was diese Phase braucht, existiert entweder in Nextcloud, in AppAPI oder in diesem Repo schon. Der Eigenbau-Anteil ist klein und liegt genau an drei Stellen: der Lastkorpus-Generator, der RSS-Sampler und der Uninstall-Schritt. Alles andere ist Verdrahtung von Vorhandenem.

## Runtime State Inventory

> Diese Phase ist keine Umbenennung, aber PKG-04 stellt genau die Frage, die dieses Inventar beantwortet: welcher Laufzeitzustand überlebt eine Deinstallation. Deshalb hier, mit demselben Raster.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Datenbanktabellen (NC-DB, Besitz Companion)** | Vier Migrationen legen Tabellen an: `Version001000Date20260816000000` (Queue mit `findling_q_locked`, `findling_q_stor`), `Version001000Date20260901000000` (Index `findling_q_free`, `findling_q_stor` gedroppt), `Version001000Date20260902000000` (`findling_q_kind`), `Version001000Date20260903000000` und `...20260904000000` (Scan-Stats, File-State). Namen der Tabellen sind über die Mapper zu ermitteln, nicht zu raten | Uninstall-Schritt mit `tableExists` + `dropTable`, idempotent, siehe Pitfall 1 |
| **appconfig (NC-DB)** | Mindestens: `enabled`, `installed_version`, `types`, `AppInstallStep::FIRST_INDEX_SCHEDULED`, `SchedulerJob::LAST_JOB_RUN`, die vier Regel-Schalter und die Ausschlussliste aus `SettingsService`/`ExclusionService`, `rememberContainerCap`, `rememberIndexedCount` | `IAppConfig::deleteApp('findling')`. Achtung: das löscht auch `enabled` und `installed_version`, was bei einem Disable-Lauf des Repair-Steps fatal wäre |
| **Background jobs (oc_jobs)** | `SchedulerJob`, `StorageCrawlJob`, `SubtreeExpandJob`. `IndexCommand` entfernt und legt `SchedulerJob` neu an [VERIFIED: php/lib/Command/IndexCommand.php:95-97] | Uninstall muss alle drei aus `IJobList` entfernen, sonst laufen sie nach dem Löschen der App weiter und werfen Autoload-Fehler in jedem Cron-Durchgang |
| **ExApp-Datenvolume (Docker)** | `APP_PERSISTENT_STORAGE` des Containers: Tantivy-Index, `state.db`, Scratch. Volumename kommt aus `buildExAppVolumeName($appId)` | Wird von AppAPI gelöscht, aber NUR mit `--rm-data`; ohne Flag bleibt es liegen ("data is kept by default") [VERIFIED: Unregister.php:53] |
| **Container und Image (Docker)** | ExApp-Container plus das gezogene `ghcr.io/street1983nk/findling_backend:<tag>` | Container entfernt AppAPI; das **Image bleibt liegen** (kein `removeImage` im Unregister-Pfad). In `docs/uninstall.md` benennen, nicht selbst löschen |
| **AppAPI-eigener Zustand** | Zeile in AppAPI-Tabellen (`ex_apps`), Event-Listener-Registrierung, Daemon-Zuordnung | `unregisterExApp` erledigt das [VERIFIED: ExAppsPageController.php:504] |
| **Nextcloud-Suchprovider-Registrierung** | Kein persistenter Zustand: `registerSearchProvider` läuft in `Application::register()`, verschwindet mit dem Disable | Keine |
| **Dateien der Nutzer** | Keine. Die Nur-Lesen-Invariante gilt, die Schreib-Allowlist hat genau drei Einträge und ein Gate hält das fest | Keine. Der Uninstall darf diese Disziplin nicht aufweichen |
| **Sonstiger OS-Zustand** | Keiner. Kein systemd-Unit, kein Taskplaner-Eintrag, kein Host-Pfad. Alles läuft in Containern und im Nextcloud-Cron | Keine, ausdrücklich geprüft |

**Die kanonische Frage für D-17:** wenn nur eine Hälfte entfernt wird, was bleibt? Ohne Companion läuft der Container weiter, hat aber keinen Anrufer mehr; er pollt eine Queue, die auf ein 404 oder ein `['error' => ...]` läuft, und die Event-Listener-Registrierung von AppAPI zeigt auf eine App, die es nicht gibt. Das ist der Fall, der im Container einen Rückzugspfad braucht (Backoff statt Fehlerschleife im Log) und in `docs/uninstall.md` die empfohlene Reihenfolge begründet: **erst die ExApp abmelden, dann die Companion-App entfernen.**

## Common Pitfalls

### Pitfall 1: Die `repair-steps/uninstall` laufen beim DISABLE, nicht beim Remove

**What goes wrong:** D-18 verlangt, dass `occ app:remove findling` die eigenen Tabellen und alle appconfig-Werte löscht, und D-16 verlangt, dass ein Disable nichts anfasst. Beides über einen unbedingten Uninstall-Repair-Step ist unmöglich.

**Why it happens:** `AppManager::disableApp()` setzt `enabled = no` und führt danach `executeRepairSteps($appId, $appData['repair-steps']['uninstall'])` aus. Das steht wortgleich in stable32 (`AppManager.php:676-680`), stable33 (`:686-690`) und stable34 (`:707-711`) [VERIFIED: nextcloud/server, alle drei Zweige gelesen 2026-09-03]. `occ app:remove` ruft genau dieses `disableApp()` und danach `Installer::removeApp()`, das nur noch Dateien löscht; der Docblock von `removeApp` behauptet zwar "call uninstall repair steps", der Rumpf tut es nicht [VERIFIED: core/Command/App/Remove.php:85-102, lib/private/Installer.php:438-466]. `occ app:disable` nimmt denselben Weg. Der einzige Unterschied ist `occ app:remove --keep-data`, das das Disable und damit die Steps überspringt.

Folge ohne Gegenmaßnahme: ein Admin, der die Suche für eine Nacht abschaltet, verliert die Ausschlussregeln, den Grössen-Deckel, die Deckungsgrad-Zähler und die Queue. Der Index im Container überlebt, die Suche wäre nach dem Re-Enable also tatsächlich sofort wieder da (D-16 in seinem Kern erfüllt), aber alle Einstellungen wären weg, und das ist ein Datenverlust in dem Bereich, in dem Phase 4 gerade Vertrauen aufgebaut hat.

**How to avoid:** Drei gangbare Formen, in der Reihenfolge der Empfehlung:

1. **Absichtsmarke (empfohlen).** Der Uninstall-Repair-Step löscht nur, wenn eine ausdrückliche Absicht hinterlegt ist, und ist ansonsten ein No-op mit einer Logzeile. Die Absicht setzt ein eigener Befehl, den `docs/uninstall.md` nennt:
   ```
   occ findling:purge          # setzt die Marke, sagt was passieren wird
   occ app:remove findling     # der Step raeumt, weil die Marke steht
   ```
   Vorteil: D-16 bleibt wörtlich wahr, D-18 bleibt erfüllbar, und der Schritt ist auf jedem der drei Server gleich. Nachteil: zwei Befehle statt einem, was in der Doku steht statt in der Mechanik. Variante davon: `occ findling:purge` räumt sofort selbst und braucht überhaupt keinen Repair-Step; dann ist der Weg noch einfacher, allerdings entfällt die Räumung bei einem Remove über die Weboberfläche.
2. **Nur das Idempotente löschen.** Der Step entfernt die Background-Jobs und die reine Buchhaltung (Queue-Zeilen, Scan-Stats), lässt aber Tabellen und appconfig stehen. Die Migrationen legen die Tabellen beim nächsten Enable wieder an. Vorteil: ein Befehl. Nachteil: D-18 ist nicht erfüllt, es bleiben Tabellen und Einstellungen liegen.
3. **Argv-Erkennung.** Der Step schaut in `$_SERVER['argv']` nach `app:remove`. Funktioniert für den occ-Weg und bricht beim Remove aus der Weboberfläche. Nicht empfehlen, aber der Vollständigkeit wegen genannt.

**Warning signs:** Ein Plan, der einen Uninstall-Repair-Step ohne Bedingung anlegt. Der Beleg dafür, dass die Wahl richtig getroffen wurde, ist eine Messung und kein Argument: einen Step anlegen, der nur eine Logzeile schreibt, dann `occ app:disable findling`, `occ app:enable findling` und `occ app:remove findling` laufen lassen und protokollieren, wie oft die Zeile erscheint. Auf allen drei Serverversionen. Diese Messung gehört in den ersten Plan der Phase, nicht in die Verifikation.

**Zwingende Eigenschaft in jedem Fall:** Der Step muss idempotent sein und einen fehlenden Zustand aushalten. Er läuft mehrfach, weil jeder Disable ihn auslöst, und er läuft potenziell bevor die Tabellen existieren.

### Pitfall 2: In NC 34 gibt es die Checkbox "Daten löschen" nicht mehr

**What goes wrong:** D-15 stützt die Bestätigung auf "ExApps-Admin-UI-Checkbox 'Daten löschen' bzw. occ ... --rm-data". Die Checkbox existiert in NC 32 und NC 33, in NC 34 nicht.

**Why it happens:** In NC 32 und 33 rendert `apps/settings/src/components/AppStoreSidebar/AppDetailsTab.vue` einen `NcCheckboxRadioSwitch` mit dem Text "Delete data on remove", gebunden an `removeData` [VERIFIED: stable32 AppDetailsTab.vue:93-98; in stable33 derselbe Text vorhanden]. NC 34 hat die App-Verwaltung in eine neue App `apps/appstore` umgebaut. Dort ruft `actionRemove` `store.uninstallApp(app.id)`, das für ExApps `exApps.uninstallApp(appId)` aufruft, und `uninstallExApp(appId, removeData = false)` verwendet die Vorgabe [VERIFIED: stable34 apps/appstore/src/actions/actionRemove.ts, store/apps.ts:148-171, service/exAppApi.ts:68-71]. Ein Suchlauf über alle `.vue`/`.ts`-Dateien von `apps/appstore/src` findet `removeData` ausschliesslich in `exAppApi.ts`; kein Bedienelement setzt es. Auch auf `master` (also NC 35) ist es so.

Die serverseitige API kann es weiterhin: `ExAppsPageController::uninstallApp(string $appId, bool $removeContainer = true, bool $removeData = false)` mit `#[PasswordConfirmationRequired]` [VERIFIED: app_api lib/Controller/ExAppsPageController.php:483].

**How to avoid:** `docs/uninstall.md` sagt es versionsabhängig: auf NC 32 und 33 der Schalter im Seitenbereich der App, auf NC 34 und 35 `occ app_api:app:unregister findling_backend --rm-data`. Und Erfolgskriterium 3 ("nach Bestätigung das Index-Volume") wird pro Serverversion belegt, nicht einmal pauschal. Der occ-Weg ist auf allen drei Versionen der verlässliche und gehört deshalb in den CI-Deploy-Job.

**Warning signs:** Eine Doku, die "Checkbox" ohne Versionsangabe sagt. Ein Admin auf NC 34, der den Schalter sucht, findet ihn nicht und hält das für einen Fehler von Findling.

### Pitfall 3: HaRP war noch nie an, und das ist mehr Arbeit als eine Matrix-Zeile

**What goes wrong:** Der Plan liest D-07 als "server-version-Liste erweitern" und übersieht, dass PKG-03 einen Deploy-Weg verlangt, den dieses Repo nicht hat.

**Why it happens:** Beide Registrierungspfade des Projekts sind `manual-install`: `scripts/dev/register-exapp.sh:178` und `.github/actions/setup-test-nc/action.yml:214`. `manual-install` erzeugt keinen Container, zieht kein Image, legt kein Volume an und liest die Routen nicht aus dem Archiv. Der Docker-Smoke-Test in `docker.yml:143` startet das Image direkt mit selbst gebautem Auth-Header, also ebenfalls ohne AppAPI. Damit sind drei Dinge, die eine echte Installation ausmacht, bisher unbelegt: der Image-Pull durch den Daemon, das Volume und der Uninstall.

**How to avoid:** Einen eigenen, schlanken Job `deploy-harp` bauen, der genau install/run/uninstall macht und die 32/33/34-Matrix trägt, und ihn nicht in die bestehenden 45-Minuten-Jobs einbauen. Bausteine, die dafür verifiziert vorliegen: HaRP-Image mit arm64 und amd64, `app_api` hat `stable32`, `stable33` und `stable34` als Zweige [VERIFIED: api.github.com/repos/nextcloud/app_api/branches/*], `--net host` löst die Rückrichtung zu `php -S`, `--info-xml` nimmt einen lokalen Pfad, `--wait-finish` macht den Handshake synchron [VERIFIED: Register.php:54, :56].

**Warning signs:** Ein Plan, in dem "HaRP" nur in der Doku vorkommt und in keiner Workflow-Datei. Und ein zweiter: ein Deploy-Job, der grün wird, ohne dass irgendwo `docker ps` den ExApp-Container zeigt.

### Pitfall 4: Der Registry-Zwang des Deploy-Daemons in CI

**What goes wrong:** Der Daemon zieht `registry/image:image-tag` aus `backend/appinfo/info.xml`, also `ghcr.io/street1983nk/findling_backend:1.0.0`. In einem CI-Lauf auf einem Feature-Zweig existiert dieser Tag nicht.

**How to avoid:** Eine lokale Registry und eine temporäre info.xml:
```bash
docker run -d -p 5000:5000 --name registry registry:2
docker build -t localhost:5000/findling_backend:citest ./backend
docker push localhost:5000/findling_backend:citest
sed -e 's|<registry>ghcr.io</registry>|<registry>localhost:5000</registry>|' \
    -e 's|<image>street1983nk/findling_backend</image>|<image>findling_backend</image>|' \
    -e 's|<image-tag>[^<]*</image-tag>|<image-tag>citest</image-tag>|' \
    backend/appinfo/info.xml > "$RUNNER_TEMP/info-citest.xml"
./occ app_api:app:register findling_backend harp_proxy_host \
  --info-xml "$RUNNER_TEMP/info-citest.xml" --wait-finish
```
Wichtig: die temporäre Datei ist **nur** für die Registrierung. Das Release-Archiv trägt `backend/appinfo/info.xml` unverändert, weil AppAPI die Routen daraus liest. Der Kommentarkopf von `backend/appinfo/info.xml` sagt das schon; ein Job, der die Ersetzung versehentlich in den Tarball trägt, würde eine App ohne Suchroute ausliefern, und zwar ohne Fehlermeldung.

### Pitfall 5: Der 50k-Korpus muss so geschnitten sein, dass der Lauf in zwei Tagen fertig ist

**What goes wrong:** OCR ist der Flaschenhals, INDEX_WORKERS ist 1, und die Seitenzahl je Scan multipliziert direkt in die Laufzeit. Ein Korpus mit im Schnitt drei Seiten je Scan sprengt das Zeitfenster aus D-02.

**Die Rechnung, offen gelegt:**

| Posten | Menge | Kosten je Einheit | Summe |
|--------|-------|-------------------|-------|
| Scans mit OCR, einseitig | 9.900 | ~4,5 s Tesseract + ~1 s Rasterung [ASSUMED, ARM-Faktor unbekannt] | 15,1 h |
| Scans mit OCR, mehrseitig (2 bis 30 Seiten) | 100, im Schnitt 8 Seiten | 5,5 s je Seite | 1,2 h |
| Textdateien (PDF-Text, Office, ODF, Text) | 40.000 | 0,15 bis 0,30 s (Download, Extraktion, Writer) | 1,7 bis 3,3 h |
| Crawl und Queue (Postgres, Bänder von 250) | 50.000 Zeilen | - | Minuten |
| **Gesamt** | | | **18 bis 20 h** |

Grundlage der 4,5 s: `docs/ocr.md` nennt gemessen etwa 2 s je saubere A4-Seite bei 300 dpi auf einem Laptop-Kern; die Phase-4-Entscheidung sagt ausdrücklich "ARM-Faktor unbekannt". Ein Faktor 2 bis 2,5 gegenüber einem modernen Laptop-Kern ist für Ampere Altra plausibel, aber **nicht gemessen** [ASSUMED].

**How to avoid:** Verteilung so festlegen, dass die OCR-Menge die Steuergrösse ist, nicht die Byte-Menge. Konkreter Vorschlag für den Generator:

| Anteil | Dateien | Typ | Grösse je Datei | Summe |
|--------|---------|-----|-----------------|-------|
| 20 % | 9.900 | Scan-PDF, 1 Seite, 300 dpi | ~350 KB | 3,5 GB |
| 0,2 % | 100 | Scan-PDF, 2 bis 30 Seiten | 0,7 bis 10 MB | 0,3 GB |
| 45 % | 22.500 | Text-PDF, mehrseitige deutsche Prosa | ~450 KB | 10,1 GB |
| 20 % | 10.000 | DOCX/XLSX/PPTX | ~350 KB | 3,5 GB |
| 10 % | 5.000 | ODT/ODS | ~300 KB | 1,5 GB |
| 4,6 % | 2.300 | TXT/MD/CSV, teils cp1252 | ~100 KB | 0,2 GB |
| 0,2 % | 100 | Bilder (JPG/PNG/TIFF/WEBP) | ~500 KB | 0,05 GB |
| Zusatz | 20 | über dem 50-MB-Deckel | 55 MB | 1,1 GB |
| **Summe** | **~50.000** | | | **~20 GB** |

Die zwanzig Dateien über dem Deckel sind Absicht: sie belegen `too_large` und den gesenkten Nenner des Deckungsgrads unter Last, was auf 33 Dateien nicht messbar war.

Der Generator läuft **auf der Box**, nicht auf der Entwicklungsmaschine: 20 GB über WebDAV oder scp zu schieben kostet mehr Zeit als sie zu erzeugen. Also direkt in das Datenverzeichnis schreiben, dann `chown -R 33:33` (AIO fährt www-data als uid 33), dann `occ files:scan --path=...`. Zwei Seeds dokumentieren: einer für den Volllauf, einer klein (500 Dateien) für den Trockenlauf, mit dem die ganze Kette einmal in 20 Minuten durchgeprüft wird, bevor 20 Stunden investiert werden.

### Pitfall 6: Der ARM-Lauf ist der erste Postgres-Lauf des Projekts

**What goes wrong:** Ein Dialektfehler, der in 20 Stunden Lauf zuschlägt, kostet den ganzen Lauf.

**Why it happens:** `index-search-e2e` fährt `database: ['sqlite', 'mysql']` [VERIFIED: integration.yml:804], die Composite Action installiert `pdo_sqlite` und `pdo_mysql` und kennt kein `pgsql` [VERIFIED: setup-test-nc/action.yml:80, :106-113]. AIO fährt `ghcr.io/nextcloud-releases/aio-postgresql` [VERIFIED: all-in-one php/containers.json]. Der Perf-Befund M7 aus Phase 2 benennt ausdrücklich einen Postgres-spezifischen Bruch ("record() innerhalb offener Transaktion bricht auf PostgreSQL die GANZE Transaktion (aborted) -> Ack schlägt fehl, Queue nie leer; MariaDB/SQLite nicht betroffen"). Behoben wurde er über UPDATE-first, aber nie auf Postgres ausprobiert.

**How to avoid:** Vor dem 20-Stunden-Lauf einen Kurzlauf mit 500 Dateien auf derselben Box fahren, und unabhängig davon `pgsql` als dritten Matrix-Eintrag von `index-search-e2e` einziehen (Service-Container `postgres:16`, Extensions `pgsql, pdo_pgsql` in der Composite Action, `--database=pgsql`). Das ist die billigste Absicherung dieser Phase und macht aus einem Einzelbefund ein Dauergate.

### Pitfall 7: Ohne gültiges Zertifikat scheitert die Rückrichtung auf AIO

**What goes wrong:** AIO setzt `NC_INSTANCE_URL=https://$NC_DOMAIN` für HaRP und `nextcloud_url = 'https://' . getenv('NC_DOMAIN')` im Deploy-Config [VERIFIED: all-in-one php/containers.json harp-Block; app_api AIODockerActions.php:122, :143]. Der ExApp-Container ruft Nextcloud unter dieser URL. Mit `SKIP_DOMAIN_VALIDATION=true` und einem selbstsignierten Zertifikat läuft jede TLS-Prüfung des Containers ins Leere.

**How to avoid:** Eine echte Subdomain für die Dauer des Tests, DNS-only (nicht über einen Proxy), damit AIO per ACME-http-Challenge auf Port 80 ein Zertifikat bekommt. Der Owner betreibt eine Cloudflare-verwaltete Domain, ein A-Record ist eine Minute Arbeit und nach dem Test wieder weg. Der Umweg über `SKIP_DOMAIN_VALIDATION` ist ausdrücklich der Rückfallplan und nicht der Plan, weil er die Fehlersuche in einem 20-Stunden-Lauf um eine Ursache erweitert, die nichts mit Findling zu tun hat.

Ports, die die Box offen braucht: 80/tcp (ACME und Weiterleitung), 443/tcp (Apache), 8080/tcp oder 8443/tcp (AIO-Oberfläche, besser nur über SSH-Tunnel), 22/tcp. 3478 nicht, weil Talk aus bleibt [CITED: nextcloud/all-in-one readme].

### Pitfall 8: Zwei Signaturen, die gern verwechselt werden

**What goes wrong:** Ein Release wird signiert, der Store nimmt es nicht an, und niemand weiss, welche der beiden Signaturen falsch war.

**Why it happens:** Es sind zwei Verfahren mit demselben Schlüssel:

| Signatur | Befehl | Wo sie landet | Wer sie prüft |
|----------|--------|---------------|---------------|
| Code-Signatur | `occ integrity:sign-app --privateKey= --certificate= --path=` | `appinfo/signature.json` **im** Archiv | Die Integritätsprüfung der Nextcloud-Instanz |
| Release-Signatur | `openssl dgst -sha512 -sign KEY archive.tar.gz \| openssl base64` | Feld `signature` im API-Aufruf | apps.nextcloud.com beim Upload |

Beide sind nötig. Die Release-Signatur muss nach **jeder** Änderung am Tarball neu erzeugt werden, also insbesondere nach dem Signieren [CITED: nextcloud/appstore docs/developer.rst; docs/certificates.md]. Reihenfolge: bauen, `integrity:sign-app`, packen, `openssl dgst`, hochladen.

**Harte Grenzen, die vorher geprüft sein müssen:** Archiv maximal **20 MB**, `info.xml` kleiner als **512 KB**, genau **ein** Top-Level-Ordner mit kleingeschriebenem ASCII-Namen, `appinfo/info.xml` darin, Download-URL zwingend https [VERIFIED: nextcloud/appstore docs/api/restapi.rst]. `backend/appinfo/info.xml` ist heute etwa 20 KB, also unkritisch, aber der Prüfschritt kostet nichts und gehört in die Release-Automation.

### Pitfall 9: Das Vokabular- und Typografie-Gate deckt die Store-Texte nicht ab

**What goes wrong:** D-12 verlangt "Vokabular-Gate für public Artefakte beachten", und die globalen Regeln des Owners verbieten Em-Dashes und Emojis und verlangen echte Umlaute. Gate C prüft genau das, aber nur über **drei Dateien** der Admin-Seite (`templates/admin.php`, `js/admin.js`, `css/admin.css`) [VERIFIED: backend/tests/test_admin_ui_contract.py:129-180]. Ein Em-Dash in der deutschen Store-Beschreibung fällt durch kein Gate.

**How to avoid:** Ein neues Textgate über beide `info.xml` und über `README.md`: kein U+2014, kein U+2013, kein Emoji, `summary` je Sprache unter 128 Zeichen, jede `lang`-Angabe aus der XSD-Enumeration, jede Screenshot-URL https und unter 256 Zeichen. Das ist ein pytest von dreissig Zeilen und schliesst die Lücke, die genau bei der Auslieferung aufgeht. Ein solches Gate ist ausserdem der Ort, an dem die Übersetzungs-Nachzieh-Regel aus D-12 mechanisch wird: fehlt eine der drei Sprachen an einem Element, das die anderen haben, ist der Test rot.

### Pitfall 10: Ein Peak-RSS-Budget von 2,5 GB passt auf der Zielbox nicht

**What goes wrong:** Der Grenzwert wird gesetzt, der Lauf hält ihn ein, und die Store-Aussage ist trotzdem schwächer als die App verdient, oder die Box kippt, weil AIO daneben nicht genug übrig hat.

**Die Rechnung aus den Projektkonstanten:**

| Posten | Wert | Quelle |
|--------|------|--------|
| Python, FastAPI, uvicorn, nc_py_api | 120 bis 180 MB | STACK.md-Budgettabelle |
| Kompositum-Automat (full) | 43 MB, genau einmal je Prozess | Perf-Audit Phase 2, gemessen |
| Tantivy-Writer-Heap | 50 MB konfiguriert (`WRITER_HEAP_BYTES = 50_000_000`) | backend/src/findling/config.py:132 |
| Ausstehender Batch im Writer | bis 64 MB (`BATCH_MAX_BYTES = 67_108_864`) | config.py:99 |
| SQLite-Cache | 10 bis 120 MB | STACK.md |
| Extraktions-Kindprozess | bis 512 MB Adressraum (`EXTRACT_ADDRESS_SPACE_BYTES`) | config.py:108 |
| Tesseract, eine A4-Seite bei 300 dpi | 300 bis 600 MB | STACK.md, docs/ocr.md |
| **Ungünstigster gleichzeitiger Stand** | **~1,6 bis 1,7 GB** | |

Auf der anderen Seite: AIO fährt Apache, php-fpm, Postgres, Redis und HaRP. 700 MB bis 1,1 GB ist eine plausible Grundlast, gemessen ist sie nicht. Bei 4 GB gesamt und 2,5 GB Budget bliebe im schlechten Fall nichts.

**Empfehlung (dies ist ausdrücklich Claude-Diskretion nach D-03):**
- **Gate:** der Lauf gilt als bestanden, wenn der Spitzenwert von `anon` unter **2,0 GB** bleibt und `memory.events` `oom` und `oom_kill` beide 0 zeigen.
- **Härtungsprobe:** derselbe Lauf zusätzlich unter `docker update --memory=2g --memory-swap=2g`. Ein Lauf unter harter Grenze ist die stärkere Aussage.
- **Store-Zahl:** der **gemessene** Spitzenwert, nicht das Gate. "Volllauf über 50.000 Dateien auf einer 4-GB-ARM-Box, Spitze X,Y GB, kein OOM" mit Verweis auf `docs/performance.md`.
- **Vor allem:** die AIO-Grundlast VOR der Installation von Findling messen und im Bericht neben die Findling-Kurve legen. Erst diese zwei Zahlen zusammen beantworten die Frage, die ein Selfhoster wirklich hat.

Der Bericht muss ausserdem `memory.peak` und den File-Cache-Anteil nennen und erklären, warum die Store-Zahl aus `anon` kommt. Sonst rechnet der erste Leser, der `docker stats` aufruft, andere Zahlen nach und hält den Bericht für falsch.

### Pitfall 11: D-11 braucht ein Feld, das `/status` heute nicht hat

**What goes wrong:** "Exakte Major.Minor-Prüfung im Code" wird an `/status` angedockt, aber `/status` meldet `indexVersion` und `analyzerVersion`, also Index-Formatmarken, nicht die App-Version [VERIFIED: backend/src/findling/api/status.py:177-178].

**How to avoid:** AppAPI injiziert `APP_VERSION` in den ExApp-Container [VERIFIED: app_api DockerActions.php:1170, `sprintf('APP_VERSION=%s', $params['version'])`], und `resilience.yml:452` setzt die Variable im Messlauf schon von Hand. Der Container kann seine registrierte Version also autoritativ melden, ohne eine neue Konstante zu backen. Die PHP-Seite holt ihre eigene über `IAppManager::getAppVersion('findling')` und vergleicht Major und Minor. Bei Abweichung: kein Fehler, sondern ein eigener Zustand auf der Admin-Seite und ein leeres Suchergebnis mit klarer Meldung, weil ein Protokollbruch zwischen den Hälften genau die Situation ist, in der stumme Treffer schlimmer sind als keine. `scripts/dev/register-exapp.sh` muss `APP_VERSION` dann auch für den Host-Prozess setzen.

### Pitfall 12: `php -S` bindet auf localhost, und die Matrix hat eine PHP-Untergrenze

**What goes wrong:** Der Deploy-Job wird gebaut, der Container startet, und niemand versteht, warum der Handshake scheitert.

**Details:** `composer run serve` startet `PHP_CLI_SERVER_WORKERS=${NEXTCLOUD_WORKERS:=4} php -S ${NEXTCLOUD_HOST:=localhost}:${NEXTCLOUD_PORT:=8080}` [VERIFIED: nextcloud/server composer.json, scripts.serve]. Vier Worker sind da, aber die Bindung ist `localhost`. Mit `--net host` beim Daemon ist das gelöst; ohne muss `NEXTCLOUD_HOST=0.0.0.0` gesetzt und `trusted_domains` erweitert werden.

Die PHP-Untergrenzen der Zielversionen: NC 32 verlangt mindestens PHP 8.1, NC 33 und NC 34 mindestens 8.2, NC 35 (master) mindestens 8.3 [VERIFIED: lib/versioncheck.php in stable32/33/34/master]. Die App deklariert `<php min-version="8.2"/>`. Ein einziger PHP-Eintrag `8.2` deckt die Matrix 32/33/34 also vollständig ab; ein Matrix-Kreuzprodukt über PHP-Versionen ist unnötig. Sobald NC 35 in die Matrix käme, bräuchte diese Zeile PHP 8.3.

## Code Examples

### Hetzner-Box und Volume per API, mit Kostenbeleg
```bash
# Source: api.hetzner.cloud/v1 (Standardressourcen servers, volumes, actions)
: "${HCLOUD_TOKEN:?token fehlt}"
h=(-H "Authorization: Bearer $HCLOUD_TOKEN" -H "Content-Type: application/json")

curl -s "${h[@]}" https://api.hetzner.cloud/v1/server_types \
  | python3 -c "import json,sys;[print(t['name'],t['cores'],t['memory'],t['disk'],t['architecture'],
      [p['location']+':'+p['price_monthly']['gross'] for p in t['prices']][:3])
      for t in json.load(sys.stdin)['server_types'] if t['name'].startswith('cax')]"

curl -s "${h[@]}" -X POST https://api.hetzner.cloud/v1/servers -d '{
  "name":"findling-arm-loadtest","server_type":"cax11","image":"ubuntu-24.04",
  "location":"nbg1","start_after_create":true,"labels":{"purpose":"findling-phase5"}}'

curl -s "${h[@]}" -X POST https://api.hetzner.cloud/v1/volumes -d '{
  "name":"findling-corpus","size":50,"server":<SERVER_ID>,
  "automount":true,"format":"ext4"}'

# Nach dem Test, und das ist Teil des Auftrags aus D-01:
curl -s "${h[@]}" -X DELETE https://api.hetzner.cloud/v1/volumes/<VOLUME_ID>
curl -s "${h[@]}" -X DELETE https://api.hetzner.cloud/v1/servers/<SERVER_ID>
```
Preise nicht aus dieser Recherche in den Bericht schreiben, sondern aus `server_types` und `pricing` desselben Kontos: die API liefert die Preise, die tatsächlich abgerechnet werden.

### Uninstall-Schritt, idempotent und mit Absichtsmarke
```php
// Skizze zu Pitfall 1, Variante 1. Der Step laeuft bei JEDEM Disable.
public function run(IOutput $output): void {
    if (!$this->appConfig->getValueBool(Application::APP_ID, self::PURGE_INTENT, false)) {
        $output->info('Findling: disable, nothing is removed. Run occ findling:purge first to clear the data.');
        return;
    }
    foreach ([QueueMapper::TABLE, ScanStatsService::TABLE, FileStateService::TABLE] as $table) {
        if ($this->db->tableExists($table)) {
            $this->db->dropTable($table);
            $output->info(sprintf('Findling: dropped %s', $table));
        }
    }
    foreach ([SchedulerJob::class, StorageCrawlJob::class, SubtreeExpandJob::class] as $job) {
        $this->jobList->remove($job);
    }
    // Zuletzt, weil es die Marke selbst mitnimmt.
    $this->appConfig->deleteApp(Application::APP_ID);
}
```
Die echten Tabellennamen aus den Mappern beziehen, nicht abschreiben. `deleteApp` steht am Ende, weil es `enabled` und `installed_version` mitnimmt.

### Symmetrischer Mengenvergleich, der auch verpasste Treffer meldet
```python
# D-21 verlangt beide Richtungen. Ein Vergleich von Groessen waere kein Beweis.
native = set(open("native.ids").read().split())
findling = set(open("findling.ids").read().split())
missing = native - findling      # Findling zeigt zu wenig: Funktionsfehler
extra = findling - native        # Findling zeigt zu viel: Sicherheitsfehler
if missing or extra:
    print(f"scenario {name}: missing={sorted(missing)} extra={sorted(extra)}")
    raise SystemExit(1)
```
`extra` und `missing` getrennt melden und getrennt benennen: die eine Richtung ist ein Fehler, die andere ist ein Sicherheitsvorfall. Ein Test, der beides als "parity failed" ausgibt, verschenkt die Diagnose.

### Store-Release, in der Reihenfolge, in der es funktioniert
```bash
# Source: docs/certificates.md + nextcloud/appstore docs/{developer,api/restapi}.rst
php occ integrity:sign-app --privateKey="$RUNNER_TEMP/findling.key" \
  --certificate="$RUNNER_TEMP/findling.crt" --path="$BUILD/findling"
tar -czf findling.tar.gz -C "$BUILD" findling            # genau ein Top-Level-Ordner
[ "$(stat -c%s findling.tar.gz)" -lt 20971520 ] || { echo "archive over 20 MB"; exit 1; }
[ "$(stat -c%s "$BUILD/findling/appinfo/info.xml")" -lt 524288 ] || { echo "info.xml over 512 KB"; exit 1; }
sig=$(openssl dgst -sha512 -sign "$RUNNER_TEMP/findling.key" findling.tar.gz | openssl base64 -A)
# Upload erst in Phase 6 (D-09):
# curl -H "Authorization: Token $APPSTORE_TOKEN" -H 'Content-Type: application/json' \
#   -d "{\"download\":\"https://github.com/.../findling.tar.gz\",\"signature\":\"$sig\"}" \
#   https://apps.nextcloud.com/api/v1/apps/releases
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Docker Socket Proxy als Deploy-Daemon | HaRP | Docker Socket Proxy ist "deprecated, scheduled for removal in Nextcloud 35" [VERIFIED: app_api RegisterDaemon.php:36, AIODockerActions.php:21-25] | Die Projektentscheidung "HaRP von Anfang an" war richtig. Für AIO heisst es: der HaRP-Container ist nicht die Zukunftsvariante, er ist auf NC 35 die einzige |
| App-Verwaltung in `apps/settings` | Eigene App `apps/appstore` | NC 34 | Die Checkbox "Delete data on remove" ist dabei verschwunden, siehe Pitfall 2. Auch andere UI-Annahmen über die App-Seite sind ab NC 34 neu zu prüfen |
| `\OC_App::executeRepairSteps` | `AppManager::executeRepairSteps` als Instanzmethode | NC 34 | Für uns folgenlos, aber ein Beleg, dass dieser Codebereich in Bewegung ist; die Disable-Semantik ist in allen drei Zweigen identisch |
| NC 34 als aktueller Stand | NC 35 steht unmittelbar an: `v35.0.0rc2` am 27.08.2026 veröffentlicht [VERIFIED: api.github.com/repos/nextcloud/server/releases] | August 2026 | Zum Einreichungszeitpunkt im Dezember ist NC 35 draussen. `max-version 35` macht die App dort installierbar, die Matrix testet sie dort nicht. Siehe Open Questions |
| `fulltextsearch` verwaist | Am 12.08.2026 reaktiviert, `fulltextsearch 34.0.1` und `files_fulltextsearch 34.0.1` im Store für NC 34 [VERIFIED: apps.nextcloud.com apps.json] | August 2026 | Das Kill-Kriterium aus STATE.md bleibt aktiv. Für Phase 5 ohne Handlungsbedarf, aber die Store-Beschreibung sollte sich nicht über die Konkurrenz definieren |

**Deprecated/outdated im Projektkontext:**
- `exAppRequestWithUserInit()`: deprecated seit AppAPI 3.0.0, wird nicht verwendet. Unverändert korrekt.
- `--keep-data` von `app_api:app:unregister`: "[deprecated, data is kept by default]" [VERIFIED: Unregister.php:53]. Die Doku darf es nicht mehr nennen; `--rm-data` ist der aktive Schalter.

## Project Constraints (from CLAUDE.md)

Aus `./CLAUDE.md` (Projekt) und den globalen Regeln, soweit sie diese Phase binden:

| Direktive | Konsequenz für Phase 5 |
|-----------|------------------------|
| Code und README englisch, Projektkommunikation deutsch | `docs/performance.md` und `docs/uninstall.md`: englisch oder deutsch? Bisherige Doku ist gemischt (`docs/admin-page.md` deutsch, `docs/testing.md` englisch). Empfehlung: Betriebsdoku deutsch wie admin-page.md, Store-Texte in ihren drei Sprachen |
| Keine Em-Dashes, echte Umlaute nur in deutscher Prosa, nie in Code | Betrifft neu genau die Store-Texte; Gate fehlt, siehe Pitfall 9 |
| Keine Emojis, Icons als SVG | Header-Bild und Screenshots nach D-13 ohne Emoji |
| Python-Gates: ruff-Vollregelsatz, pyright basic, vulture, lokal grün vor Commit | Gilt für Generator, Sampler und neue Tests. `vulture --min-confidence 80` hat `should_flush` bisher nicht gemeldet, ein neuer toter Helfer würde also auch durchkommen; das ist kein Freibrief |
| `uv run python -m pytest`, nicht `uv run pytest` | In Abnahmebedingungen so schreiben; ein früherer Plan hat hier abgewichen |
| Kein Co-Authored-By-Trailer | Gilt für alle Commits der Phase |
| Nach jedem Edit committen und pushen | `commit_docs: true` in config.json; RESEARCH.md wird committet |
| GSD-Workflow: keine direkten Repo-Edits ausserhalb eines GSD-Kommandos | Der ARM-Lauf ist Ausführung, nicht Edit; die Artefakte daraus (docs/performance.md) entstehen in einem Plan |
| Secrets nie ins Repo, nie ins Log | Neu hinzu: `HCLOUD_TOKEN` und der HaRP-`HP_SHARED_KEY`. Der HaRP-Key ist in CI ein Testwert, auf der Box ein echtes Geheimnis (AIO erzeugt es selbst und legt es als Secret ab) |
| Owner sendet Outreach selbst | Die Store-Einreichung selbst ist Phase 6 (D-09); Phase 5 erzeugt nur Artefakte |

## Review-Reste-Inventar (D-20)

Alle Positionen unten wurden am 03.09.2026 gegen den Arbeitsbaum geprüft (grep bzw. Quelltext gelesen), nicht aus den Berichten abgeschrieben.

### Bereits geschlossen, kein Handlungsbedarf

Die in 03-CONTEXT.md nach Phase 3 verschobenen Positionen sind **alle erledigt**, geschlossen in Plan 03-14 [VERIFIED: Quelltext plus 03-14-SUMMARY.md]:

| Befund | Beleg im Arbeitsbaum |
|--------|----------------------|
| Perf-M1 (Poller-Öffnen blockiert den Event-Loop) | `poller.py:383` `await asyncio.to_thread(self._open)` |
| Perf-M2 (Batch-Text gehalten) | `poller.py:874` `outcome = replace(outcome, text="")` |
| Perf-M5 (usersFor ohne Deckel) | `QueueService.php:56` `MAX_USERS = 500`, `userIdsTruncated` |
| Perf-M8 (getUserFolder je Zeile) | Ordner-Cache je Claim in `QueueService.php:630` |
| Perf-M9 (MAX_LIST_LENGTH 1000) | `QueueController.php:77` = 256 |
| Sec-L2 (script/style im XHTML-Zweig) | `text.py:67` `_INVISIBLE_TAGS = ("{*}script", "{*}style")` |
| Sec-L4 (kein Gate für die ExApp-Grenze) | `backend/tests/test_php_trust_boundary.py` existiert (Gate B) |
| Sec-L5 (kein isReadable) | `Provider.php:302` |
| Sec-L6 (getMessage im Log) | `grep getMessage() php/lib/Controller` ist leer |

Ebenfalls geschlossen und ausdrücklich geprüft: Sec-C1 (`SEARCH_OFFSET_MAX`), Sec-C2 (`_max_bracket_depth`), Sec-H1 (`_MAX_RTF_BYTES = 256 * 1024`), Sec-M1 (`has_more=len(permitted) > offset + limit`), Sec-M3 (`SEARCH_QUERY_MAX_CHARS`), Sec-M4 (`EXTRACT_ARCHIVE_MEMBER_MAX_BYTES`), Sec-M5 (Byte-Deckel in `_stream_file`), Sec-M6 (env-Bereinigung im Kind), Sec-L3 (`os.killpg`), Bug-H1 bis H5, Perf-H1 bis H5, Perf-M6, Perf-M7, Bug-M2, Bug-M5. Bug-L3 (`GATEWAY_ERROR` toter Code) ist kein Befund mehr: der Code ist inzwischen auf der PHP-Seite als Label und in `FileStateService` als gültiges Paar geführt, also ein reservierter Wert und keine Leiche.

### Offen, gehört nach D-20 in diese Phase

**Gruppe A: Phase-4-Review, sieben Infos, bewusst nicht behoben** [Quelle: 04-REVIEW.md]

| ID | Kurz | Ort | Aufwand |
|----|------|-----|---------|
| IN-01 | `index_bytes()` warnt bei jedem Poll für den normalen Frischzustand | `store/repo.py:915`, gerufen aus `status.py:151`, `rates.py:138` | klein |
| IN-02 | Tote Übersetzung "Indexing, about %s left" | `php/l10n/de.json:10`, `de.js:11` | klein |
| IN-03 | Prozentzahl wechselt nach dem ersten Poll von NBSP auf normales Leerzeichen | `templates/admin.php:191` vs `js/admin.js:318` | klein |
| IN-04 | Backslash-Umwandlung macht Dateien mit Backslash im Namen nicht diagnostizierbar | `PathResolverService.php:204` | klein, Entscheidung nötig (fixen oder dokumentieren) |
| IN-05 | Docblock in `Section.php` begründet den Verzicht auf `#[\Override]` falsch | `php/lib/Settings/Section.php:22-27` | klein |
| IN-06 | `_OPEN`/`_MARKS` ohne Lock aus Worker-Threads, Store-Verbindung leckt | `api/resources.py:58-59, 156-194`; identisch mit Bug-Audit M7 | mittel |
| IN-07 | `.`-Segment in einer Ausschlussregel wird gespeichert und trifft nie | `ExclusionService.php:207-225` | klein |

**Gruppe B: Phase-3-Review, drei Infos, bewusst nicht behoben** [Quelle: 03-REVIEW.md]

| ID | Kurz | Ort |
|----|------|-----|
| IN-01 | Widersprüchliche Kommentare zur Zahl der kaputten PDFs | `integration.yml:863` und `:1212` gegen `testdata/CORPUS.md:17` |
| IN-02 | `getSize()` läuft auch für Löschungen, vor der Ausnahme | `FileEventListener.php:356` |
| IN-03 | `failed(repeatedly_stuck)` erreicht die Container-DB nie, der Abgleich reiht nächtlich neu ein | `QueueService.php:151`, `QueueMapper.php:487`, `reconcile.py:364` |

Gruppe-B-IN-03 ist die inhaltlich schwerste Position dieses Inventars: sie ist kein Kosmetikpunkt, sondern eine Aufgabe-Regel, die für abgleich-gefundene Dateien nie endgültig wird. Auf 50.000 Dateien wird daraus messbare Dauerlast, und der ARM-Lauf ist genau der Ort, an dem man es sehen würde. Empfehlung: **vor** dem Volllauf beheben.

**Gruppe C: Phase-3-Deferred, drei Positionen** [Quelle: 03/deferred-items.md]

| Kurz | Ort | Bemerkung |
|------|-----|-----------|
| Ein Bild kommt als Inhaltsjob und bekommt die kurze Frist (120 s statt 660 s) | `worker/poller.py`, Inhaltszweig | Ein mehrseitiges TIFF endet als `failed(timeout)` statt `indexed(truncated)`. Der Lastkorpus enthält Bilder; wenn mehrseitige TIFFs hineinkommen, schlägt es zu |
| `ocr_used` wird für Bilder nicht gesetzt | dieselbe Stelle | Macht den OCR-Aufwand für Bilder unsichtbar, also auch im Messbericht |
| Ein wiederhergestellter Ordner braucht den ETag-Abgleich | Restore-Zweig `FileEventListener` | War für Plan 03-12 vorgesehen; ob dort behandelt, ist im Rahmen dieser Recherche **nicht** verifiziert und vom Planner zu prüfen |

**Gruppe D: Phase-4-Deferred, zwei Positionen ausserhalb von D-19** [Quelle: 04/deferred-items.md]

| ID | Kurz | Warum es hierher gehört |
|----|------|-------------------------|
| DI-04-01 | `register-exapp.sh` deklariert eine von fünf Routen, mit einem Kommentar, der Parität behauptet | Genau die Klasse Fehler, die "läuft hier, bricht in CI". Wenn der HaRP-Job kommt, wird die Routenliste ohnehin aus `info.xml` gelesen; die Position löst sich dort mit |
| DI-04-02 | Der Dev-Backend-Prozess muss nach einem Plan mit neuer Route neu gestartet werden | Eine Zeile in `docs/dev-setup.md` oder ein Versionsvergleich im Skript |

**Gruppe E: Phase-2-Audits, noch offene Lows und zwei Mediums**

CI und Lieferkette:

| ID | Kurz | Stand geprüft |
|----|------|---------------|
| Sec-M7 | Der Smoke-Test prüft Build A (`load`), nach ghcr geht Build B (`push-by-digest`) | Offen: `docker.yml:122` baut lokal und testet, `:204` baut/pusht erneut. Fix: einmal bauen, per Digest pushen, `pull @digest`, Smoke gegen den Digest |
| Sec-M8 | Action-SHA-Kommentare stimmen nicht | Offen und belegbar: `actions/checkout@3d3c42e5...` und `actions/checkout@fbc6f399...` sind **zwei verschiedene SHAs, beide als "v5.0.0" kommentiert**. Eine Pinning-Verteidigung, deren Kommentar lügt, ist wertlos |
| Sec-L8 | Zwei `setup-uv`-Majors | Offen: `python.yml` nutzt `@20cfd1bf # v10.0.1`, `setup-test-nc/action.yml` nutzt `@d0cc045d # v6`. Deckt sich mit der Owner-Regel "seit v8 exakte Version pinnen" |
| Sec-L7 | `inputs.*` direkt in `run:` interpoliert | Offen: `setup-test-nc/action.yml:106` ff. Heute nur Literale, aber die Matrix-Erweiterung dieser Phase fügt neue Eingaben hinzu, also gerade jetzt zu härten |
| Sec-L9 | Provenance-Zusage nie verifiziert | Offen |
| Sec-L10 | Actions laden zur Laufzeit Binaries (setup-php, setup-uv) | Offen, strukturell; als Restrisiko dokumentieren |
| Perf-LOW | `timeout-minutes` fehlt | Offen in `docker.yml`, `php.yml`, `python.yml`, `resilience.yml` (nur `integration.yml` hat vier). Default sind 360 Minuten |
| Sec-L1 | Die PHP-`info.xml` verschweigt den gespeicherten Dokumenttext, die Backend-`info.xml` ist ehrlich | Offen. Fällt in D-12 zusammen mit dem Privacy-Block: der Absatz gehört in beide Beschreibungen, in allen drei Sprachen |

Code-Lows:

| ID | Kurz | Stand geprüft |
|----|------|---------------|
| Bug-L1 | `<=` verschmilzt angrenzende Hervorhebungen | Offen, `index/search.py:229` |
| Bug-L2 | `decode()` ohne `errors=` kann bei Byte-Offset mitten im Zeichen werfen | Offen, `index/search.py:225` |
| Bug-L4 | `--status` zeigte immer `indexed 0` | Wahrscheinlich geschlossen: `IndexCommand::status()` liest heute `fileStateService->counts()`. Ob `indexed` dort geführt wird, ist nach dem Docblock-Split von Phase 4 zweifelhaft und **zu prüfen** |
| Bug-L8 | `_files_handled++` nach `_ask()` überschreibt den Recycle-Reset nach Timeout | Offen, `extract/sandbox.py:254` gegen `:330` |
| Perf-LOW | `CHUNK_SIZE` 64 KB, 800 `to_thread`-Hops je 50-MB-Datei | Offen, `nc/client.py:88`. Auf ARM mit 20 GB Download der spürbarste Posten dieser Liste |
| Perf-LOW | `acl_totals` COUNT(DISTINCT) als Full-Scan | Offen, `store/repo.py:840`, nur Statusseite. Auf 50k Dateien wird der Admin-Poll teuer |
| Perf-LOW | `degraded()` je Suche (`read_meta` + `disk_usage`) | Offen, `api/resources.py:197` |
| Perf-LOW | `char_ranges` dekodiert den Präfix je Bereich neu | Offen, `index/search.py:203` |
| Perf-LOW | Off-by-one bei `MAX_ATTEMPTS`: vier Auslieferungen statt drei | Offen, `QueueService.php:153` (`getRetries() > 3`) |
| Perf-LOW | `should_flush` toter Code, `_pending_bytes` erzeugt eine UTF-8-Vollkopie je Dokument | Offen, `index/writer.py:177`, `:220`. Der zweite Teil ist auf 20 GB Korpus kein Kosmetikpunkt |

**Empfohlene Reihenfolge innerhalb von D-20:** zuerst die drei Positionen, die den 20-Stunden-Lauf beeinflussen (Gruppe-B-IN-03, `CHUNK_SIZE`, `_pending_bytes`-Vollkopie), dann die zwei Bildzweig-Positionen aus Gruppe C, dann Sec-M7/M8/L7/L8 und die `timeout-minutes` (alle CI, alle billig, alle vor dem Release relevant), dann der Rest. Alles Kleine lässt sich in zwei bis drei Sammelplänen bündeln; einzelne Pläne für Einzeiler kosten mehr Verwaltung als Code.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | HaRP lokal, Image-Bau, cgroup-Messung | ja | 29.5.2 | keiner nötig |
| `gh` | Store-Zertifikate holen, Release anlegen | ja | 2.92.0 | curl |
| slopcheck | Paketprüfung | ja | vorhanden | nicht gebraucht (keine neuen Pakete) |
| `hcloud`-CLI | Box bestellen | **nein** | - | curl gegen `api.hetzner.cloud/v1` (empfohlen) |
| `ctx7`-CLI / Context7-MCP | Bibliotheksdoku | **nein** | - | WebFetch gegen die Primärquellen; für diese Phase ausreichend, weil alle Antworten aus Nextcloud-Quellcode und der Store-XSD kommen |
| `HCLOUD_TOKEN` | Box bestellen | **unbekannt** | - | **Kein Fallback.** Der Owner muss einen API-Token mit Schreibrechten im bestehenden Projekt bereitstellen, sonst ist D-01 nicht ausführbar |
| DNS-Eintrag für die Box | AIO-Zertifikat, HaRP-Rückrichtung | **unbekannt** | - | `SKIP_DOMAIN_VALIDATION=true` mit selbstsigniertem Zertifikat, aber mit dem TLS-Risiko aus Pitfall 7 |
| SSH-Zugang und SSH-Key im Hetzner-Konto | Box bedienen | **unbekannt** | - | Passwort per Konsole, unbequem und schlechter |
| Browser-Zugang zur AIO-Oberfläche | HaRP-Container aktivieren (kein env dafür) | über SSH-Tunnel machbar | - | keiner; die Auswahl der optionalen Container ist in AIO nur in der Weboberfläche möglich |
| `~/.findling-secrets/` mit beiden Schlüsseln | Signieren | laut docs/certificates.md vorhanden | - | keiner |
| GitHub-Secrets `APP_PRIVATE_KEY`, `BACKEND_PRIVATE_KEY`, `APPSTORE_TOKEN` | Release-Automation | **unbekannt, ob gesetzt** | - | Lokales Signieren durch den Owner |
| PHP auf der Entwicklungsmaschine | PHP-Änderungen prüfen | **nein** (dokumentiert) | - | `docker run php:8.3-cli ... php -l`, so wie bisher |
| Playwright | Store-Screenshots von der Dev-Instanz | über MCP, laut Owner-Memory in Gebrauch | - | Screenshots von Hand |

**Missing dependencies with no fallback:**
- `HCLOUD_TOKEN` mit Schreibrechten. Ohne ihn ist der ganze ARM-Block blockiert. Der Planner sollte einen `checkpoint:human-verify` an den Anfang des ARM-Blocks setzen.
- Zugang zur AIO-Weboberfläche zum Aktivieren des HaRP-Containers.

**Missing dependencies with fallback:**
- `hcloud`-CLI, `ctx7`: beide durch curl bzw. WebFetch ersetzbar.
- DNS-Eintrag: durch `SKIP_DOMAIN_VALIDATION` ersetzbar, mit benanntem Risiko.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | ja | Unverändert Nextcloud: OCS mit Basic/Session, `#[ExAppRequired]` plus `rejectForeignCaller` an jeder ApiRoute, Gate B hält es. Der Paritätstest legt sechs Testkonten an, alle mit Wegwerf-Passwörtern und nur in CI |
| V3 Session Management | ja | Die Admin-Route verlangt Session plus CSRF-Token (keine der vier verbotenen Attribute), `#[PasswordConfirmationRequired]` liegt auf dem AppAPI-Uninstall |
| V4 Access Control | **Kern dieser Phase** | SRCH-04 ist ein Access-Control-Test. Die Grenze bleibt der PHP-Recheck über `getUserFolder()->getFirstNodeById()` plus `isReadable()`; der Paritätstest prüft sie, er ersetzt sie nicht |
| V5 Input Validation | ja | Bereits gedeckelt: Query-Länge, Offset, Klammertiefe, Listenlängen. Neu zu deckeln: nichts, solange der Uninstall keine neue Route bekommt. Der `--info-xml`-Pfad in CI ist kein Nutzerpfad |
| V6 Cryptography | ja | RSA-4096-Signaturschlüssel, SHA-512-Signatur, beides nach Store-Vorgabe. Kein Eigenbau. Neu: `HP_SHARED_KEY` als Geheimnis zwischen HaRP und AppAPI |
| V7 Error Handling / Logging | ja | Die Regel "statischer Satz plus `exception`-Feld, nie eine Bibliotheksmeldung" gilt auch für den Uninstall-Step. Ein Step, der einen SQL-Fehler wörtlich loggt, leakt Tabellennamen und Pfade |
| V12 Files | ja | Nur-Lesen-Invariante bleibt unverletzt. Der Uninstall darf keine vierte Schreibroute anlegen; die Volume-Löschung läuft über AppAPI, nicht über den Container |
| V14 Configuration | ja | Neu: HaRP braucht `/var/run/docker.sock`. Das ist Root-Äquivalent auf dem Host und ist genau der Grund, warum HaRP existiert (statt den Socket an jede App zu geben). In der Doku benennen: wer Findling installiert, hat einen Deploy-Daemon mit Docker-Zugriff, und das ist eine Eigenschaft von AppAPI, nicht von Findling |

### Known Threat Patterns for diese Phase

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Uninstall-Step löscht bei einem Disable die Konfiguration | Denial of Service (Datenverlust) | Absichtsmarke, Idempotenz, Messung auf allen drei Serverversionen (Pitfall 1) |
| Paritätstest wird durch den Trefferdeckel grün, ohne zu prüfen | Repudiation (falscher Nachweis) | Ausdrückliches `limit`, Serverdeckel hochsetzen, plus ein Selbsttest, der eine absichtlich verletzte Parität rot werden lässt. Das Repo hat für dieses Muster Vorbilder (`tamper_probe`, `missing_verdict_probe`) |
| Signaturschlüssel im Build-Log | Information Disclosure | Regeln aus `docs/certificates.md` unverändert: Datei unter `$RUNNER_TEMP`, Löschung in einem `if: always()`-Schritt, Signaturjob nur auf Tags des Standardzweigs, nie auf Fork-PRs |
| Beweglicher `release`-Tag des HaRP-Images | Tampering | Auf Digest pinnen |
| Action-SHA-Kommentar stimmt nicht mit dem SHA überein | Tampering | Sec-M8, in dieser Phase zu beheben; die Prüfung skripten, nicht von Hand nachlesen |
| Der Lastkorpus enthält versehentlich echte Dokumente | Information Disclosure | D-02 ist eindeutig: rein synthetisch. Der Generator soll seinen Seed und eine Prüfsumme über die Dateiliste ausgeben, damit "synthetisch" belegt und nicht behauptet ist |
| Miet-Box bleibt nach dem Test stehen, mit Nextcloud, Admin-Passwort und offenem Port 443 | Information Disclosure, Kosten | D-01 verlangt die Löschung. Als Schritt mit `if: always()`-Charakter planen, plus ein Label auf Box und Volume, damit ein Vergessen auffindbar ist |
| `SKIP_DOMAIN_VALIDATION` bleibt gesetzt und das Ergebnis wird als AIO-Beweis verkauft | Repudiation | Wenn der Rückfallplan gezogen wird, gehört das in den Bericht, mit der Aussage, was damit nicht bewiesen ist |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Tesseract braucht auf einem Ampere-Altra-Kern etwa 4,5 s je A4-Seite bei 300 dpi (Faktor 2 bis 2,5 gegenüber der gemessenen Laptop-Zahl aus docs/ocr.md) | Pitfall 5 | Bei Faktor 4 dauert der Volllauf 30 bis 35 h, bei Faktor 6 über zwei Tage. Gegenmaßnahme: Kurzlauf mit 500 Dateien auf der Box messen und die OCR-Menge danach festlegen, bevor der Volllauf startet |
| A2 | AIO-Grundlast auf arm64 mit 4 GB liegt bei 700 MB bis 1,1 GB | Pitfall 10 | Wenn es deutlich mehr ist, ist auch 2,0 GB als Gate zu hoch. Gegenmaßnahme: Grundlast VOR der Findling-Installation messen und das Gate danach endgültig festlegen |
| A3 | CAX11 kostet 5,99 EUR/Monat bzw. 0,0096 EUR/h, Volumes 0,057 EUR/GB/Monat (Stand nach der Anpassung vom 15.06.2026) | Standard Stack | Nur Kostenaussage im Bericht. Gegenmaßnahme: Preise aus `server_types` und `pricing` desselben Kontos ziehen, nicht aus einer Websuche |
| A4 | Ein 50-GB-Volume plus 40 GB Root reichen für 20 GB Korpus, Docker-Images und den Index | Pitfall 5 | Index bei 20 GB Korpus grob 3 bis 6 GB, Images 2 bis 3 GB. Reicht, aber nur wenn Docker-`data-root` und `NEXTCLOUD_DATADIR` auf dem Volume liegen. Gegenmaßnahme: beides vor dem ersten AIO-Start umstellen; `NEXTCLOUD_DATADIR` darf nach der Installation nicht mehr geändert werden |
| A5 | Der HaRP-Deploy in GitHub Actions funktioniert mit `--net host` und `php -S` | Pattern 1, Pitfall 12 | Die Bausteine sind einzeln verifiziert, die Kombination nicht. Gegenmaßnahme: erster Plan der Phase ist ein Spike, der genau das grün macht, bevor die Matrix darauf gebaut wird |
| A6 | `occ app:install groupfolders` läuft in CI ohne Store-Zugangsdaten | Pattern 2 | Wenn nicht, Tarball aus dem GitHub-Release der passenden Major-Version entpacken. Kein Blocker, nur ein anderer Schritt |
| A7 | Das ACL-Vorfilter-Update nach einem Gruppenwechsel (Szenario 5) trifft schnell genug ein, um im Testfenster geprüft zu werden | Pattern 2 | Wenn der Teilbaum-Job erst im nächsten Cron-Durchgang läuft, braucht der Test eine ausdrückliche Cron-Auslösung plus Warteschleife, wie es `reconcile-and-dach` schon macht |
| A8 | Bug-L4 (`--status` zeigt `indexed 0`) ist inzwischen geschlossen | Review-Reste-Inventar | Nur eine Position mehr oder weniger im Inventar. Vom Planner in einem Satz zu prüfen |
| A9 | Die Position "wiederhergestellter Ordner braucht den ETag-Abgleich" wurde in Plan 03-12 behandelt | Review-Reste-Inventar, Gruppe C | Falls nicht, ist es eine echte Lücke in IDX-04 und keine Kosmetik |

## Open Questions (RESOLVED)

Alle fuenf Fragen wurden am 03.09.2026 vom Owner entschieden und als Nachtraege D-23 bis D-27 in 05-CONTEXT.md festgehalten.

1. **NC 35 ist zur Einreichung draussen, aber nicht in der Matrix.** RESOLVED: D-23 (Matrix + max-version 35).
   - Was wir wissen: `v35.0.0rc2` wurde am 27.08.2026 veröffentlicht; die Apps deklarieren `max-version 35`, sind dort also installierbar. NC 35 verlangt PHP 8.3 und entfernt den Docker Socket Proxy.
   - Was unklar ist: ob der Owner das Risiko trägt, für eine Serverversion freizugeben, die kein Gate abdeckt.
   - Empfehlung: `stable35` als vierten Matrix-Eintrag des neuen, schlanken Deploy-Jobs aufnehmen, sobald der Zweig existiert, mit `php-version: 8.3` für diesen Eintrag und `continue-on-error: true` bis NC 35 GA ist. Alternative: `max-version` auf 34 senken, was aber die Reichweite zum Einreichungszeitpunkt beschneidet. Owner-Entscheid.

2. **Der PHPUnit-Rückstand: zwölf benannte Verhaltensweisen ohne Test.** RESOLVED: D-24 (komplett rein).
   - Was wir wissen: `docs/testing.md` listet zwölf reine Logik-Eigenschaften der PHP-Hälfte, alle ohne Test, alle als Spezifikation ausformuliert, und benennt auch den Weg (Server auschecken, App nach `apps/findling`, `tests/bootstrap.php`). Elf davon sind Unit-Test-Material.
   - Was unklar ist: ob das unter D-20 fällt. Es ist kein Review-Befund, sondern eine dokumentierte Lücke. Es ist zugleich der grösste Qualitätshebel dieser Phase, und die Infrastruktur (Server-Checkout je Version) baut diese Phase ohnehin.
   - Empfehlung: als eigenen, klar abgegrenzten Block anbieten (Schätzung ein bis zwei Tage) und dem Owner die Wahl lassen. Wenn der Dezember drückt, ist das der ehrlichste Kürzungskandidat, weil die Lücke dokumentiert ist und nicht verschwiegen.

3. **Wo wohnt der Uninstall-Räumbefehl?** RESOLVED: D-25 (Absichtsmarke + occ findling:purge).
   - Was wir wissen: Pitfall 1 lässt drei Formen zu. `occ findling:purge` ist ein dritter occ-Befehl neben `findling:index` und `findling:diagnose`.
   - Was unklar ist: ob der Owner einen dritten Befehl will oder die Räumung lieber als Schalter auf der Admin-Seite hat (was aber D-15 "kein Eigenbau-Dialog" berührt).
   - Empfehlung: occ-Befehl. Die Admin-Seite hat mit der Ausschluss-Räumung schon eine destruktive Bestätigung; eine zweite dort erhöht die Fehlbedienungsfläche, und ein Purge ist ein Betriebsvorgang, kein Alltagsklick.

4. **`<donation>` in der Store-Beschreibung?** RESOLVED: D-27 (rein, Link wie Connector).
   - Was wir wissen: Die XSD erlaubt bis zu zehn `donation`-Elemente; das Schwesterprojekt nextcloud-mcp-connector hat Spenden live (paypal.me).
   - Was unklar ist: nicht entschieden, in CONTEXT.md nicht erwähnt.
   - Empfehlung: als Frage an den Owner beim plan-phase, nicht eigenmächtig aufnehmen. Kosten: eine Zeile in beiden info.xml.

5. **Wie wird die "einreichungsbereite" Kandidatur aus D-09 nachprüfbar abgelegt?** RESOLVED: D-26 (Tag v1.0.0 + signierte Releases Ende Phase 5).
   - Was wir wissen: Phase 5 endet mit signierten Artefakten, aber ohne Upload. Ein Tag `v1.0.0` würde `docker.yml` auslösen und das Image unter `1.0.0` veröffentlichen, was in Ordnung ist; das GitHub-Release wäre der https-Download für den späteren API-Aufruf.
   - Was unklar ist: ob Phase 5 den Tag schon setzen soll (dann ist der Store-Upload wirklich ein Klick) oder ob der Tag zu Phase 6 gehört (dann muss Phase 5 die Artefakte als Build-Artefakte ablegen und Phase 6 baut neu).
   - Empfehlung: Tag und GitHub-Release in Phase 5 setzen, den Store-Upload in Phase 6. Dann ist "ein Klick bis zur Abgabe" wörtlich wahr, das Image liegt unter dem Tag, den `info.xml` nennt, und Phase 6 fügt nur die Semantik hinzu und hebt auf `1.0.0` in einem zweiten Anlauf. Achtung auf den Nebeneffekt: ein öffentliches Release `1.0.0`, das noch nicht im Store ist, könnte von Nutzern gefunden und installiert werden. Alternative: Pre-Release-Tag `v1.0.0-rc.1` (das semver-Muster der XSD erlaubt Vorabversionen, der Store würde es als Beta führen). Owner-Entscheid.

## Sources

### Primary (HIGH confidence)
- `nextcloud/server`, Zweige `stable32`, `stable33`, `stable34`, `master`: `lib/private/App/AppManager.php` (Uninstall-Steps beim Disable), `lib/private/Installer.php`, `core/Command/App/Remove.php`, `lib/versioncheck.php`, `apps/files/lib/Search/FilesSearchProvider.php`, `core/Controller/UnifiedSearchController.php`, `lib/private/Search/SearchQuery.php`, `core/AppInfo/ConfigLexicon.php`, `lib/public/IAppConfig.php`, `lib/public/IDBConnection.php`, `apps/settings/src/components/AppStoreSidebar/AppDetailsTab.vue` (32/33), `apps/appstore/src/**` (34)
- `nextcloud/app_api`, `main`: `lib/Command/ExApp/Unregister.php`, `lib/Command/ExApp/Register.php`, `lib/Command/Daemon/RegisterDaemon.php`, `lib/Controller/ExAppsPageController.php`, `lib/DeployActions/DockerActions.php`, `lib/DeployActions/AIODockerActions.php`, `lib/Migration/DataInitializationStep.php`; Zweigexistenz `stable32`/`stable33`/`stable34` über die GitHub-API bestätigt
- `nextcloud/appstore` @ `5c4373d7d026a8f7c7838cc9990fecaf19e8e682`: `info.xsd` (Elementreihenfolge, l10n-Codes, semver, secure-url, repair-steps, screenshot-Grenze); `docs/developer.rst` und `docs/api/restapi.rst` (Release-API, 20-MB-Grenze, info.xml < 512 KB, Signaturbefehl)
- `nextcloud/all-in-one`, `main`: `php/containers.json` (`nextcloud-aio-harp`, `nextcloud-aio-postgresql`), `Containers/nextcloud/entrypoint.sh` (HARP_ENABLED-Logik), `readme.md`, `compose.yaml`
- `nextcloud/groupfolders`, `master`: `lib/Command/Create.php`, `Group.php`, `ACL.php`
- `docs.kernel.org/admin-guide/cgroup-v2.html`: `memory.current`, `memory.peak`, `memory.stat` (`anon`, `file`, `slab`), `memory.events` (`oom`, `oom_kill`)
- `apps.nextcloud.com/api/v1/platform/{32,33,34}.0.0/apps.json` und `appapi_apps.json`: Verfügbarkeit von `groupfolders`, `guests`, `fulltextsearch`; `app_api` ist nicht darin, weil es ein Shipped-App ist
- `docker manifest inspect` gegen `ghcr.io/nextcloud-releases/aio-harp:latest` und `ghcr.io/nextcloud/nextcloud-appapi-harp:release`: beide linux/amd64 und linux/arm64
- Eigenes Repo, gelesen und gegrept am 03.09.2026: `.github/workflows/{integration,php,docker,resilience}.yml`, `.github/actions/setup-test-nc/action.yml`, `scripts/dev/{register-exapp.sh,compose.yaml,build_corpus.py}`, `php/appinfo/info.xml`, `backend/appinfo/info.xml`, `backend/src/findling/**`, `php/lib/**`, `docs/{certificates,store-identity,testing,admin-page}.md`, alle Audit- und Review-Berichte der Phasen 2 bis 4

### Secondary (MEDIUM confidence)
- `docs.nextcloud.com/server/stable/admin_manual/exapps_management/DeployConfigurations.html`: HaRP-`docker run`, Ports 8780/8781/8782, `HP_SHARED_KEY`, `NC_INSTANCE_URL`, `HP_TRUSTED_PROXY_IPS`; die dortige Aussage "AppAPI erzeugt für AIO den Docker-Socket-Proxy-Daemon" ist gegenüber dem AppAPI-Quellcode veraltet, der auch `harp_aio` erzeugt
- Websuche zu Hetzner-Preisen (mehrere Anbieter-Vergleichsseiten, September 2026): CAX11 2 vCPU Ampere Altra, 4 GB, 40 GB NVMe, 5,99 EUR/Monat bzw. 0,0096 EUR/h nach der Anpassung vom 15.06.2026; Volumes 0,057 EUR/GB/Monat. Für den Bericht durch die Konto-API zu ersetzen
- `github.com/hetznercloud/cli` Releases: v1.67.0 vom 24.07.2026

### Tertiary (LOW confidence)
- Der ARM-Geschwindigkeitsfaktor von Tesseract (A1). Grundlage ist die eigene Laptop-Messung in `docs/ocr.md` plus eine Schätzung; ausdrücklich zu messen, nicht zu glauben
- Die AIO-Grundlast auf arm64 mit 4 GB (A2). Die AIO-Dokumentation nennt keine RAM-Untergrenze

## Metadata

**Confidence breakdown:**
- Uninstall-Semantik (Pitfall 1, 2): HIGH. Quellcode aller drei Serverzweige und der AppAPI gelesen, nicht aus Dokumentation abgeleitet. Die eine offene Stelle ist die Wahl der Gegenmaßnahme, und die ist eine Entscheidung, keine Tatsache
- Paritätstest (Pattern 2): HIGH. Provider-Id, Filterübersetzung, `fileId`-Attribut, Limit-Vorgabe und Serverdeckel sind alle im Quellcode belegt, in mehreren Zweigen verglichen
- Store-Einreichung (Pattern 4, Pitfall 8): HIGH für die XSD- und API-Grenzen (gepinnte Schemadatei, Store-Doku), MEDIUM für den ExApp-spezifischen Ablauf, weil die Store-Doku externe Apps nicht eigens behandelt. Das Schwesterprojekt hat den Weg aber schon gegangen
- HaRP-Deploy (Pattern 1, Pitfall 3, 4): HIGH für die Feststellung, dass es fehlt, und für die Bausteine (Befehle, Optionen, Images, AIO-Automatik). MEDIUM für die konkrete CI-Verdrahtung, die noch niemand grün gesehen hat (A5)
- Speichermessung (Pattern 3, Pitfall 10): HIGH für die Methode (Kernel-Doku plus Projektkonstanten), MEDIUM für die empfohlene Zahl, weil die AIO-Grundlast ungemessen ist
- Lastkorpus und Laufzeit (Pitfall 5): MEDIUM. Die Verteilung ist rechenbar, der OCR-Faktor auf ARM ist es nicht
- Review-Reste-Inventar: HIGH. Jede Position einzeln gegen den Arbeitsbaum geprüft; zwei Positionen ausdrücklich als "zu prüfen" markiert statt behauptet
- Hetzner-Kosten: MEDIUM. Websuche, kein Kontozugriff

**Research date:** 2026-09-03
**Valid until:** 2026-10-03 für die Nextcloud- und AppAPI-Befunde, und deutlich kürzer für NC 35: sobald `stable35` existiert, sind die Aussagen zu Disable-Semantik, App-Verwaltungs-UI und Docker-Socket-Proxy gegen diesen Zweig neu zu prüfen. Die Store-XSD ist auf einen SHA gepinnt und altert nur, wenn `APPSTORE_SHA` bewegt wird.
