# Phase 28: Abnahme-Anfahrt - Research

**Researched:** 2026-09-29
**Domain:** Messanfahrt auf AWS (EC2 arm64 und x86_64), RAM- und Durchsatzmessung des gebauten Produkts je Profilstufe, Rückfluss der Slot-Kosten in Formel und Probe
**Confidence:** MEDIUM (Rechenblatt, Werkzeuge, Code-Orte HIGH; x86-Umzug des Snapshot-Stacks LOW bis MEDIUM, nie gefahren)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Vorentscheide, die hier tragen und NICHT neu verhandelt werden: D-26-10 (Messbox auf AWS-Guthaben, Konto infranodedev 450315222812, 104,29 USD gültig bis 04.09.2027, NICHT Konto Cherif83; Matrix 4/8/16/32 Kerne x86 plus 16-Kern-ARM m7g als Baseline; vCPU-Quota eu-central-1 = 32, also seriell, Erhöhung auf 48 nur falls seriell zu langsam; Korpus-Snapshot snap-03f1d1d9ad9262704 ist der Messkorpus; NACH der Phase-28-Messung ALLES abbauen inklusive Snapshot, Ziel null laufende AWS-Kosten, Abbau-Beweis dokumentiert), D-24-03 (Anteile, Obergrenzen Standard 4 / Leistung 16 Slots), D-24-06 (Vorschlags-Schwellen), D-26-02/03 (Slot-Drossel und Wächter), D-27-05/07/08 (Probe pausiert Indexierung, zweistufige N-Slot-Probe, "passt knapp" speichert nicht), Store-Regel eine Messzahl (730,2 MB, Gate test_store_metadata.py RESIDENT_FIGURE).

#### Kosten und Abbruch
- **D-28-01 (Owner, 29.09.2026):** Der Kostendeckel ergibt sich aus dem Rechenblatt (Runbook Abschnitt 2, Ist-Werte der letzten Anfahrten als Untergrenze je Posten) für genau den Messumfang aus D-28-06, plus 30 Prozent Reserve. Die Zahl wird dem Owner VOR dem ersten Boxstart vorgelegt und datiert freigegeben (SC1); ohne Freigabe startet keine Box.
- **D-28-02 (Owner, 29.09.2026):** Wird der Deckel während der Anfahrt erreicht: die laufende Zelle wird zu Ende gemessen, keine neue Zelle startet, die Box bleibt stehen bis zum Owner-Wort (weiterlaufende Kosten werden in Kauf genommen, damit nichts verloren geht). Kein automatischer Abbau beim Deckel; der Abbau folgt erst nach Owner-Entscheid oder regulär nach Abschluss (D-26-10).

#### Boxen und Profile
- **D-28-03 (Owner, 29.09.2026):** Referenzbox für Sparsam und den Vergleich zur Store-Zahl ist wie bisher m7g.large (2 vCPU ARM, 4 GB, mem=4G nach Runbook Block 5/12). Sparsam darf dort nicht von der Store-Messzahl abweichen (SC2).
- **D-28-04 (Owner, 29.09.2026):** x86-Matrix auf der Familie c7a (2 GB je Kern): 4, 8, 16, 32 Kerne = c7a.xlarge, c7a.2xlarge, c7a.4xlarge, c7a.8xlarge. Dazu die ARM-Baseline m7g.4xlarge (16 Kerne) aus D-26-10. Begründung: nah an typischer Selfhost-Hardware (4 Kerne / 8 GB), Speicherknappheit wird bei Leistung sichtbar und testet Probe und Wächter.
- **D-28-05 (Owner, 29.09.2026):** Auf JEDER Matrix-Box laufen alle drei Profile. Vor jeder Stufe läuft die Probe über die Settings-Fläche bzw. dieselbe Route (Weg des Produkts, nicht occ); gemessen wird jede Stufe, auch wenn die Probe "knapp" oder "passt nicht" sagt (dann per occ erzwungen, klar markiert). Das Probe-Verdikt wird je Zelle mit der Messung verglichen und im Bericht als Gegenprobe der Probe selbst ausgewiesen.

#### Messumfang
- **D-28-06 (Owner, 29.09.2026):** Jede Zelle (Box x Profil) misst ein festes, OCR-lastiges Teilkorpus (Größenordnung 5.000 Dokumente, genaue Auswahl und Größe legt die Research fest, gleich für alle Zellen, reproduzierbar ausgewählt und committet) mit RAM-Spitze und Durchsatz. Nur Sparsam auf der Referenzbox m7g.large fährt den vollen Korpus (52.111 Dokumente) als Vergleich zur Store-Messzahl.
- **D-28-07 (Owner, 29.09.2026):** fp32 wird auf zwei Zellen mitgemessen: Standard mit fp32 auf einer knappen und einer großzügigen Box (Auswahl legt die Research fest, z. B. c7a.xlarge und c7a.4xlarge). Die Probe lädt die fp32-Datei dort live (Download aus dem eigenen Release, Digest-Prüfung); gemessen wird die RAM-Spitze mit fp32. Das schließt die Lücke aus 27-15/27-VERIFICATION (fp32 nur automatisiert belegt).

#### Rückfluss in Formel und Probe (SC4)
- **D-28-08 (Owner, 29.09.2026):** Die gemessenen Slot-Kosten ersetzen die Schätzwerte in Formel und Probe (insbesondere OCR_SLOT_COST_BYTES = 235 MiB in backend/src/findling/config.py und die davon abgeleiteten Reserven); das ist eine Code-Änderung IN Phase 28 mit Tests. Toleranz: Eine Messung bis +10 Prozent über der Rechnung gilt als von der Rechnung getragen. Liegt eine Stufe darüber oder widerspricht ein Probe-Verdikt der Messung, entscheidet der Owner je Fall, ob die Formel nachgezogen oder die Stufe im Release nicht angeboten wird; der Entscheid wird dokumentiert (SC4).

### Claude's Discretion
- Genaue Auswahl des Teilkorpus (OCR-Anteil, Dokumentarten), solange fest, reproduzierbar und für alle Zellen gleich.
- Reihenfolge der Zellen (seriell, Quota 32), solange die Referenzbox und die Rechenblatt-Freigabe zuerst kommen.
- Welche Box die knappe und welche die großzügige fp32-Zelle ist (D-28-07).
- Form der Rohdaten und des Berichts (Anlehnung an docs/measurements/2026-09-*/ und docs/performance.md).

### Deferred Ideas (OUT OF SCOPE)
- WR-04-Rest aus Phase 27 (OCR-indexierte Dateien mit skipped(no_text_layer) unter "Übersprungen"): Phase 29.
- Security-Hinweise aus secure-phase 27 (F-3 fp32-Marke an der Datei, T-27-39 createElement nicht im Gate): Kandidaten Phase 29.
- Issue #14 (Team-Folder-Leser jenseits der ersten 20 Namen, Neuversuch bei ACL-Änderung): wartet auf Diagnose von budachst, eigener Schnitt danach.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MESS-10 | Abnahme-Anfahrt am gebauten Produkt: RAM-Messung je Profilstufe auf echter Hardware, BEVOR die Settings-UI die Stufe anbietet; Rechenblatt + Kostendeckel VOR dem Boxstart zur Owner-Freigabe, Runbook-Disziplin (Cron-Intervall-Gate, Digest-Wechsel, Rohdaten committen) | Abschnitt "Das Rechenblatt" (SC1), "Zellenablauf" und "Messgrößen" (SC2), "x86-Lücken des Runbooks" und "Abbau" (SC3), "SC4: Rückfluss" (SC4), "Owner-Checkpoints" |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Code, Bezeichner, Protokollzeilen der Skripte in Englisch bzw. ASCII; echte Umlaute nur in deutscher Prosa, nie in Code, Keywords, URLs, YAML.
- Keine Em- oder En-Dashes, keine Emojis.
- Qualitätsgates lokal grün vor jedem Commit: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright` (mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, gleiche Version wie CI), `uv run vulture src tests --min-confidence 80`, `uv run pytest -q`; für `scripts/`: `uv run ruff check --config pyproject.toml ../scripts` und `ruff format --check` (aus `backend/`).
- Commit-Identität `street1983nk <k.cherif@outlook.de>`, keine Claude-Trailer; nie pushen ohne Owner-Wort.
- Während der Research keine AWS-Box starten; lesende, kostenlose Abfragen erst in der Ausführung.
- Store-Texte: höchstens eine Messzahl (730,2 MB), Textänderung nur mit Owner (Phase 29).
- Nach jeder Phase Security-, Bug- und Performance-Audit.
- Öffentliches Repositorium: keine IPs, Instanz-/Volumekennungen, Kontokennung, Passwörter in `docs/` (Gate `backend/tests/test_public_artifacts.py`, Geheimnisregel des Runbooks).
- Owner-Abnahmen von UI gemeinsam per Playwright (Memory-Regel 29.09.); hier nur relevant, falls die Probe über die Fläche statt über die Route gezeigt werden soll.

## Summary

Die Phase ist im Kern eine Anfahrt mit vorhandenen Werkzeugen (Runbook, `aws_box.sh`, Sampler W1 bis W4, Laufskripte der v1.2/v1.3) plus drei echten Neuerungen, die jede Plananzahl bestimmen: (1) die x86-Boxen c7a, für die das Runbook keinen einzigen gefahrenen Block hat (arm64-AMI, arm64-Inhalte im containerd-Store des Snapshots, PostgreSQL-Datenverzeichnis aus arm64), (2) ein festes Teilkorpus und ein frischer Erstindex je Zelle, also rund 20 Nullstände statt einem, und (3) die Probe als Teil jeder Zelle über die Admin-Route mit Sitzung und Anfrage-Token.

Das Rechenblatt kommt mit gelesenen Preisen (öffentliche On-Demand-Preiskarte Frankfurt, Stand 25.09.2026) und konservativen Planwerten (ARM-Seitenrate auch für x86, keine vorweggenommene Verbesserung) auf rund **87,6 Boxstunden und 45,18 USD**, mit 30 Prozent Reserve **114 h / 58,74 USD** (Variante A, 5.000 Dateien). Das ist ein Mehrfaches aller bisherigen Deckel (3 bis 5,40 USD), liegt aber unter dem Guthaben von 104,29 USD. Der größte Einzelposten sind die Ein-Slot-Zellen (Sparsam überall, Standard auf 4 Kernen): Sparsam auf c7a.8xlarge allein kostet rund 8,70 USD. Eine kleinere Teilkorpus-Variante B senkt den Deckel auf rund 48 USD.

SC4 ist eine kleine, gut umrissene Code-Änderung: `OCR_SLOT_COST_BYTES` in `backend/src/findling/config.py` Zeile 889; `EMBED_LANE_RESERVE_BYTES` und `GUARD_RESERVE_BYTES` folgen automatisch. Die Änderung muss NACH allen Zellen fallen, sonst stimmt der Baumhash des gemessenen Abbilds nicht mehr mit dem Arbeitsbaum.

**Primary recommendation:** Erst Rechenblatt und Deckel (Owner), dann ARM (m7g.large voll + Teilkorpus-Zellen, Typwechsel m7g.4xlarge), dann EIN x86-Exemplar mit eigenem Volume aus demselben Snapshot, das per Typwechsel c7a.xlarge -> 2xlarge -> 4xlarge -> 8xlarge läuft; vor dem ersten x86-Messblock ein zeitlich gedeckeltes Machbarkeitstor (amd64-Abbilder, PostgreSQL-Start, REINDEX), das lokal vorher kostenlos geprobt wird.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Rechenblatt, Deckel, Kostenstempel | Entwicklungsmaschine (Operator) | Rohdatei im Repo | AWS-Zugangsdaten nie auf der Box (Muster `00-typwechsel.sh`) |
| Box-Lebenszyklus (Instanz, Volume, Typwechsel, Abbau) | Entwicklungsmaschine, AWS-API | `aws_box.sh`, Runbook-Blöcke | nur dort liegen Anmeldung und Zustandsdatei |
| Zellenablauf (Nullstand, Probe, Trigger, Ende) | Box, Laufskript | Nextcloud occ, Companion-Routen | läuft unbeaufsichtigt, damit Wartezeit keine Boxzeit bindet |
| Probe | Container (`worker/probe_run.py`) | PHP `ProbeService` über `/apps/findling/admin/profile/check` | Weg des Produkts (D-28-05) |
| Profil wirksam machen | Container (liest Profil vom Companion) | PHP appconfig `profile`, `model_precision` | Container fragt nach, Wirkung verzögert |
| RAM-Messung | cgroup des ExApp-Containers (`rss_sampler.sh`, `proc_anon_sampler.sh`) | `memory.events`, OOMKilled | anon statt memory.peak (Seitencache) |
| Durchsatz | Admin-Übersicht `/apps/findling/admin/overview` (Statusreihe) | `occ findling:index` | Verdikte und Vektoren je Zeit |
| Slot-Kosten-Rückfluss | `backend/src/findling/config.py` | Tests, docs/profiles.md, docs/admin-page.md | eine Konstante, abgeleitete Reserven folgen |

## Standard Stack

Keine neuen Bibliotheken. Die Phase benutzt ausschließlich vorhandene Werkzeuge des Repositoriums, Systempakete der Box und die AWS CLI.

### Core (vorhanden, wiederverwenden)
| Werkzeug | Ort | Zweck | Stand |
|---------|---------|---------|--------------|
| `aws_box.sh` | `scripts/ops/` | prices, volume, restore, start, stop, snapshot, status, destroy | gepinnt auf m7g.large (Zeilen 91, 95, 162) [VERIFIED: codebase] |
| `rss_sampler.sh` | `scripts/ops/` | anon/file/slab/current/peak der Container-cgroup, OOM-Beweis | [VERIFIED: codebase] |
| `proc_anon_sampler.sh` | `scripts/ops/` | RssAnon und VmHWM je Prozess (Sandbox-Kind, tesseract) | [VERIFIED: codebase] |
| `cpu_sampler.sh` | `scripts/ops/` | Kernbelegung Container gegen Box (r) | [VERIFIED: codebase] |
| `rss_digest.py` | `scripts/ops/` | Summe je Zeitpunkt, dann Maximum | [VERIFIED: codebase] |
| `ocr_slot_probe.py`, `slot_ladder.py` | `scripts/ops/` | Wegwerf-Proben der Slot-Skalierung | [VERIFIED: codebase] |
| `build_load_corpus.py` | `scripts/dev/` | `allocate()` und `Rng` definieren den Korpus deterministisch | [VERIFIED: codebase] |
| Laufskripte v1.2 | `docs/measurements/2026-09-v12-messung/skripte/` | `92b-wechsel.sh`, `93-nullstand.sh`, `96-volllauf.sh`, `96d-statusbeobachter.py`, `97-cron-vorpruefung.sh`, `40b-baumhash.sh/.py` | [VERIFIED: codebase] |
| Laufskripte v1.3 | `docs/measurements/2026-09-v13-messung/skripte/` | `00-lauf.sh` (Timer), `00-typwechsel.sh`, `92d-wechsel.sh`, `94c-bodensatz-zyklen.sh` (Store-Zahl C1) | [VERIFIED: codebase] |
| `probe_page_login.sh` | `scripts/dev/` | Anmeldung per Cookie, Token aus der Seite, Origin-Kopf | [VERIFIED: codebase] |

### Supporting (Systempakete auf der Box)
| Paket | Zweck | Wann |
|---------|---------|-------------|
| `docker.io`, `jq` (Ubuntu-Archiv) | wie Runbook Block 8 | jede Box |
| `fio` (Ubuntu-Archiv, optional) | Volume-Initialisierung aus dem Snapshot, schneller als dd | einmal je Volume; Rückfall `dd` ohne Installation [CITED: docs.aws.amazon.com/ebs/latest/userguide/ebs-initialize.html] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| manuelle Volume-Initialisierung (fio/dd) | `--volume-initialization-rate 100..300` bei `create-volume` | vorhersagbar (55 GiB bei 300 MiB/s rund 3 min), aber Aufpreis je GiB, Satz nicht gelesen [CITED: AWS-Doku oben]; nur nehmen, wenn der Owner den Satz vorher sieht |
| x86-Stack aus dem Snapshot | frischer Nextcloud-Harness `scripts/dev/compose-harp.yaml` auf der x86-Box plus Kopie des Teilkorpus | lokal auf x86 bewährt (27-15), aber andere Nextcloud (keine AIO, anderes Cron), schwächere Vergleichbarkeit zu den ARM-Zellen; nur als Rückfall B |

**Installation:** keine Paketinstallation auf der Entwicklungsmaschine; auf der Box `sudo apt-get install -y docker.io jq fio`.

## Package Legitimacy Audit

Die Phase installiert keine externen Bibliotheken (npm/PyPI/crates). Einzige Systempakete sind `docker.io`, `jq` (beide schon in v1.2/v1.3 auf der Box installiert) und optional `fio` aus dem Ubuntu-Archiv; slopcheck ist für Distributionspakete nicht zuständig und wurde nicht gefahren.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| fio | Ubuntu-Archiv (apt) | langjährig | n/a | github.com/axboe/fio | nicht anwendbar | Approved, von der AWS-Doku selbst empfohlen [CITED] |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Das Rechenblatt (Forschungsfrage 1, SC1)

### Gelesene Sätze

Gelesen am 29.09.2026 aus der öffentlichen On-Demand-Preiskarte, die auch die Preisseite speist (`https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/EU%20(Frankfurt)/Linux/index.json`, gzip, Publikationsdatum im Manifest 2026-09-25T17:45:21Z). Kein Kontoaufruf. [VERIFIED: öffentliche Preiskarte]

| Typ | vCPU | RAM | Instanz USD/h | Box gesamt USD/h (plus 100 GB gp3 0,013041 plus IPv4 0,005) |
|---|---:|---:|---:|---:|
| m7g.large | 2 | 8 GiB (mem=4G) | 0,0978 | **0,115841** (gleich dem gepinnten Satz) |
| m7g.4xlarge | 16 | 64 GiB | 0,7821 | **0,800141** (gleich v1.3) |
| c7a.xlarge | 4 | 8 GiB | 0,23426 | **0,252301** |
| c7a.2xlarge | 8 | 16 GiB | 0,46852 | **0,486561** |
| c7a.4xlarge | 16 | 32 GiB | 0,93704 | **0,955081** |
| c7a.8xlarge | 32 | 64 GiB | 1,87408 | **1,892121** |
| angehaltene Box (nur 100 GB gp3) | | | | 0,013041 je Stunde |

Die Sätze werden am Anfahrtstag ein zweites Mal gelesen (Runbook 2.3; die Preis-API des Kontos ist gesperrt, `00-typwechsel.sh preis` endete am 26.09. mit 1). Weicht ein Satz ab, wird der Deckel vor der ersten Kommandozeile neu gerechnet.

### Planwerte je Posten (Ist-Werte der letzten Anfahrten als Untergrenze)

| Posten | Planwert | Untergrenze (Ist) | Quelle |
|---|---:|---:|---|
| Handaufbau ARM, Blöcke 1 bis 13 | 1 h 00 | 0 h 12 (v1.3), 0 h 40 (v1.2) | Runbook 2.1 |
| **NEU** Volume-Initialisierung (fio über das ganze Gerät) | 0 h 45 | nie gemessen, Schätzung | AWS-Doku; 55,4 GB geschriebene Blöcke |
| Abbildwechsel auf Phase-27-Stand (PHP-Hälfte, `occ upgrade`, Registrierung, Baumhash) | 0 h 45 | 0 h 00 30 s (92d v1.3), 0 h 32 (v1.2, drei Läufe) | Runbook 13b |
| Cron-Gate vorher | 0 h 15 | Minuten | `97-cron-vorpruefung.sh` |
| **NEU** Zellen-Overhead je Zelle (Nullstand mit `--rm-data`, Bewaffnung, 360 s Frist, Probe bis 120 s Messen plus Pause, Warten auf wirksames Profil, Nachlauf) | 0 h 45 | 92c 0 h 06 19 s; Probe 6 s (27-15) | v1.3-Rohdaten |
| Sparsam voll 52k auf m7g.large, beide Spuren bis zum letzten Vektor | **21 h 15** | 19 h 20 (v1.2, Untergrenze, 4.696 schon indexiert) | 19,33 h x 52.137 / 47.441 |
| 94c Rückkehr zur Grundlast nach dem Vollauf (Store-Zahl C1) | 0 h 15 | 0 h 07 17 s | v1.3 |
| **NEU** Teilkorpus einrichten (Hardlinks, files:scan, Ausschlüsse, Zähltor) | 0 h 20 | nie gemessen | |
| **NEU** x86-Aufbau inkl. amd64-Abbilder, PostgreSQL-Tor, Bewaffnung | 2 h 00 | nie gemessen | |
| Typwechsel (stop, modify, start, A-Record, Bewaffnung) | 0 h 15 bis 0 h 30 | 0 h 17 49 s B4 (v1.3) | |

Lauf-Planwerte des Teilkorpus (Variante A, 5.000 Dateien, 2.691 OCR-Seiten), gerechnet mit der ARM-Rate auch für x86, weil ein Planwert keine Verbesserung vorwegnimmt (Runbook 2.1): 4,1 s je OCR-Seite je Slot (B2 4,09 s, B4 0,263 Seiten/s), Textspur 0,169 s je Datei, Einbettung rund 0,45 s je Text-Datei (19 h 20 min minus 12 h 49 min Text/OCR-Lauf über 52k). [ASSUMED: Übertrag der ARM-Raten, Einbettungsanteil abgeleitet]

| Profil, Slots | Lauf-Planwert |
|---|---:|
| Sparsam (1 Slot, Einbettung inline) | 3 h 50 |
| Standard/Leistung mit 1 Slot (m7g.large; Standard auf c7a.xlarge) | 3 h 20 |
| 3 Slots (Standard c7a.2xlarge, Leistung c7a.xlarge) | 1 h 15 |
| 4 Slots (Standard auf 16/32 Kernen) | 1 h 00 |
| 7 bis 16 Slots (Leistung ab 8 Kernen), einbettungs- und zulaufgebunden | 0 h 45 |
| Standard fp32, 1 Slot (c7a.xlarge), plus Download | 3 h 30 |
| Standard fp32, 4 Slots (c7a.4xlarge), fp32 bettet langsamer ein | 1 h 30 |

Slotzahlen je Box nach der echten Formel (`findling.profile.ocr_slots`, lokal gerechnet mit geschätztem MemAvailable), also das, was die Probe vorschlagen wird:

| Box | Vorschlag | Sparsam | Standard | Leistung |
|---|---|---:|---:|---:|
| m7g.large (mem=4G, Grenze 2g) | economy | 1 | 1 | 1 |
| c7a.xlarge | standard | 1 | 1 | 3 |
| c7a.2xlarge | performance | 1 | 3 | 7 |
| c7a.4xlarge | performance | 1 | 4 | 15 |
| c7a.8xlarge | performance | 1 | 4 | 16 |
| m7g.4xlarge | performance | 1 | 4 | 15 |

[VERIFIED: lokal gerechnet mit backend/src/findling/profile.py; MemAvailable ASSUMED als MemTotal minus 1 GiB]. Befund: auf c7a (2 GB je Kern) ist die Formel überall kernbegrenzt, der Speicherterm greift nirgends. Speicherknappheit wird also nur sichtbar, wenn die GEMESSENE Slot-Kosten deutlich über 235 MiB liegen (fette Mehrseiten-Scans, K2) oder bei fp32 auf der knappen Box.

### Summe und Deckel (Variante A)

| Box | Posten | Stunden | USD |
|---|---|---:|---:|
| m7g.large | Aufbau 1:00, Init 0:45, Wechsel 0:45, Cron 0:15, S-voll 22:15, Teilkorpus 0:20, St-T 4:05, L-T 4:05 | 33,50 | 3,881 |
| m7g.4xlarge | Typwechsel 0:30, S-T 4:35, St-T 1:45, L-T 1:30 | 8,33 | 6,668 |
| c7a.xlarge | x86-Aufbau 2:00, Init 0:45, Wechsel 0:45, Teilkorpus 0:20, Cron 0:15, S-T 4:35, St-T 4:05, L-T 2:00, St-fp32 4:15 | 19,00 | 4,794 |
| c7a.2xlarge | Typwechsel 0:15, S-T 4:35, St-T 2:00, L-T 1:30 | 8,33 | 4,055 |
| c7a.4xlarge | Typwechsel 0:15, S-T 4:35, St-T 1:45, L-T 1:30, St-fp32 2:15 | 10,33 | 9,869 |
| c7a.8xlarge | Typwechsel 0:15, S-T 4:35, St-T 1:45, L-T 1:30 | 8,08 | 15,295 |
| geparkte ARM-Platten während der x86-Hälfte, Abbau | 45,75 h x 0,013041 plus 1 h Abbau | | 0,623 |
| **Summe** | | **87,58 h** | **45,18 USD** |
| **Deckel = Summe x 1,30** | | **114 h** | **58,74 USD** |

```
Deckel (USD) = Summe_je_Box( Stunden_Box x Satz_Box ) + Parkposten, alles x 1,30
Deckel (h)   = Summe der Boxstunden x 1,30   (nur Anzeige; bindend ist USD, weil die Sätze bis Faktor 16 auseinanderliegen)
```

- Optional **Anker-Zelle** Sparsam auf dem Teilkorpus auf m7g.large (4 h 35, 0,53 USD): verbindet die Teilkorpus-Zahlen mit der Referenzbox. Empfohlen, als Owner-Wahl ins Blatt.
- **Variante B** (rund 2.550 Dateien, alle 100 Mehrseiten-Scans, rund 1.740 OCR-Seiten, Lauf-Planwerte x 0,65): rund 76 h / 36,9 USD, Deckel rund **99 h / 48 USD**. Grob gerechnet, nur als Alternative für den Owner.
- Die Sitzungszeit zwischen Blöcken ist NICHT in den Posten (Runbook 9.4). Sie wird durch unbeaufsichtigte Ketten je Box vermieden, nicht durch Reserve.
- Snapshotkosten (2,79 bis 2,99 USD/Monat) laufen bis zur Löschung weiter und gehören nicht in den Deckel (Runbook 2.3), fallen aber wegen D-26-10 am Ende weg.

**Rohdatei-Zeile vor der ersten Minute (Runbook 3, Zeile 9):** `Anfahrt freigegeben: <Datum>, Deckel <h> h / <USD> USD`.

## Architecture Patterns

### System Architecture Diagram

```
Entwicklungsmaschine (AWS-CLI, box.env je Architektur, Rechenblatt)
   |  describe/prices (kostenlos) -> Owner-Freigabe Deckel (SC1)
   v
[ARM-Instanz, Volume V-A aus snap-03f1...] --Typwechsel--> [m7g.4xlarge]
   |                                                         |
   |  je Zelle:                                              | stop, parken
   v                                                         v
 Nullstand (unregister --rm-data, register, Bewaffnung, 93) [x86-Instanz, Volume V-X aus demselben Snapshot]
   |                                                         | Machbarkeitstor (amd64-Abbilder, PostgreSQL, REINDEX)
   v                                                         v
 Probe über /apps/findling/admin/profile/check  ---- nein ---> occ config:app:set ... (markiert "erzwungen")
   | fits (takeOver speichert)                               |
   v                                                         |
 Warten bis overview.effective == Ziel <---------------------+
   |
   v
 Sampler an (rss, proc_anon, cpu, Statusreihe) -> Trigger findling:index --restart -n
   |
   v
 Lauf bis Vorrat 0 und embedded == indexed  -> Nachlauf (Ruhezeit, Entladung, Grundlast)
   |
   v
 Rohdaten abholen (Platzhalter statt Kennungen) -> Deckel-Prüfung vor der nächsten Zelle (D-28-02)
   |
   v
 nach der letzten Zelle: SC4-Auswertung -> Owner je Fall -> Code-Änderung config.py + Tests
   |
   v
 Abbau beider Boxen, Tag-Sweep 17 Regionen, Snapshot löschen, Nullstand der Kosten belegt
```

### Recommended Project Structure

```
docs/measurements/2026-10-abnahme-anfahrt/      # Datum des Anfahrtstags einsetzen
├── README.md                                   # Bericht, Muster v13-messung/README.md
├── skripte/
│   ├── 00-ablauf.md                            # Erwartungen VOR der Messung, inkl. Rechnung je Zelle
│   ├── 00-kette.sh                             # alle Zellen einer Box unbeaufsichtigt, Deckel-Prüfung vor jeder Zelle
│   ├── 00-typwechsel.sh                        # verallgemeinert: Zieltyp als Argument, arm und x86
│   ├── 01-teilkorpus.sh / 01-teilkorpus.py     # Auswahlregel, Hardlinks, Liste mit sha256, Ausschlüsse, Zähltor
│   ├── 10-zelle.sh                             # eine Zelle: Nullstand, Probe, Wirksamkeit, Trigger, Ende, Nachlauf
│   ├── 11-probe-route.py                       # Sitzung, Token, POST/GET check, Verdikt als Rohdatei
│   ├── 12-slotkosten.py                        # proc_anon-Reihe -> Kosten je Slot, Vergleich mit Rechnung
│   └── (Kopien/Ableitungen von 92d, 93, 96d, 97, 40b, 94c)
└── rohdaten/<box>/<zelle>/                     # je Zelle ein Verzeichnis
backend/tests/test_v14_abnahme.py               # boxlose Tests der neuen Skripte, Muster test_v13_wegwerf.py
```

### Pattern 1: Eine Zelle, in fester Reihenfolge

**What:** Jede Zelle beginnt am Nullstand und endet mit Rohdaten und Deckel-Prüfung.
**When to use:** jede der rund 20 Zellen.

1. Vorzustand zurück auf Sparsam/int8 über den Abwärtsweg `POST /apps/findling/admin/profile` (kein Probe nötig), damit ein neuer Container nicht mit dem Profil der vorigen Zelle anläuft.
2. Nullstand: Muster `92d`/`92b` mit `unregister --rm-data` (vor der Zählung "genau eine Nextcloud", Block 13), Registrierung, Bewaffnung (Block 11, Beleg `backendReachable true`), nur auf m7g.large Block 12 (2g/0), Baumhash im laufenden Container. Dann `93-nullstand.sh` ohne Neustart des Vorrats: Volume leer, Endzustände gelesen.
3. `sync; echo 3 | sudo tee /proc/sys/vm/drop_caches`, damit keine Zelle vom Seitencache der vorigen erbt; Zeile in die Rohdatei.
4. Probe (nur Standard/Leistung/fp32; Sparsam ist Abwärtsweg, "keine Probe" protokollieren): `11-probe-route.py`. Verdikt `fits` speichert selbst (`ProbeService::takeOver`). Verdikt `narrow`/`nofit`: `occ config:app:set findling profile --value=<ziel>` (und `model_precision`), Zeile `erzwungen ja grund <verdikt>/<cause>`.
5. Wirksamkeit: Admin-Übersicht bis `effective == ziel` und `slotsInForce` gelesen; notfalls Bewaffnung (disable/enable) erneut, damit der Container beim Start nachfragt. Nie messen, solange `effective` noch das alte Profil nennt (27-15: `profileStored True`, `effective economy`).
6. Sampler starten, dann Trigger `occ findling:index --restart -n` (das `-n` ist Pflicht, sonst "Nothing was changed").
7. Ende = Vorrat 0 und `embedded == indexed` in zwei Lesungen hintereinander; Nachlauf mit Ruhezeit 120 s (D-02 der v1.2) und Grundlast-Lesung.
8. Abholen, Platzhalter statt Kennungen, Kostenstempel; vor der nächsten Zelle Deckel-Prüfung: `bisher_USD + (jetzt - box_start) x Satz >= Deckel_USD` -> keine neue Zelle, Marke schreiben, Box läuft weiter (D-28-02).

### Pattern 2: Reihenfolge der Boxen und Zellen (Quota 32)

| Schritt | Box | Zellen | Anmerkung |
|---|---|---|---|
| 1 | m7g.large (V-A) | S-voll (21 h unbeaufsichtigt), 94c, dann Teilkorpus, St-T, L-T, optional Anker S-T | Referenzbox zuerst (Discretion-Bedingung) |
| 2 | m7g.4xlarge (Typwechsel, `mem=4G` entfernen) | S-T, St-T, L-T | danach stop, ARM bleibt geparkt |
| 3 | c7a.xlarge (neue x86-Instanz, V-X) | Machbarkeitstor, S-T, St-T, L-T, St-fp32-T | billigste Box für das Tor |
| 4 | c7a.2xlarge | S-T, St-T, L-T | |
| 5 | c7a.4xlarge | S-T, St-T, L-T, St-fp32-T | |
| 6 | c7a.8xlarge | S-T, St-T, L-T | 32 vCPU = ganze Quota, ARM muss gestoppt sein |

Innerhalb einer Box: Sparsam zuerst (Basis, wärmt nichts vor, weil Caches geleert werden), dann Standard, Leistung, fp32 zuletzt (danach `model_precision` über den Abwärtsweg zurück auf int8). Angehaltene Instanzen zählen nicht gegen die vCPU-Quota [ASSUMED]; parallel wären m7g.4xlarge und c7a.4xlarge (16 + 16) quotengerecht, D-26-10 verlangt aber seriell.

### Pattern 3: Das Teilkorpus (Forschungsfrage 3)

Der Snapshot-Korpus ist deterministisch nach Kategorie nummeriert (`generate()` zählt über `CATEGORIES` in fester Reihenfolge, Dateiname `{index:05d}-<slug>.<endung>`, Seed `phase5-full`). Offline nachgerechnet mit `allocate(50000)`:

| Kategorie | Bereich im Snapshot | im Teilkorpus A | Auswahlregel |
|---|---|---:|---|
| scan_single | 00001-09916 | 1.800 | 00001-01800 |
| scan_multi | 09917-10016 | 100 (791 Seiten, 2 bis 30 je Datei) | alle |
| text_pdf | 10017-32552 | 1.500 | 10017-11516 |
| ooxml | 32553-42568 | 900 | 32553-33452 |
| opendocument | 42569-47576 | 400 | 42569-42968 |
| plain_text | 47577-49880 | 200 | 47577-47776 |
| image | 49881-49980 | 100 | alle |
| oversize | 49981-50000 | 0 | ausgelassen (nur `too_large`, misst nichts) |
| **Summe** | | **5.000** | 2.000 OCR-Dateien (40 Prozent gegen 20 im Vollkorpus), **2.691 OCR-Seiten** |

[VERIFIED: offline mit `scripts/dev/build_load_corpus.py`, `allocate` und `_scan_page_count`, deckungsgleich mit der Tabelle in docs/performance.md Zeile 1554ff.]

Warum so: die Mehrseiten-Scans tragen die RAM-Spitze einer OCR-Seite und das Seitenlimit (höchstens 30 Seiten, also in allen drei Profilen voll gelesen: Sparsam 30, Standard 100, Leistung 150), die Bilder den zweiten Weg in tesseract, die Text-Kategorien die Textspur und die Einbettung. "Die ersten N je Kategorie" ist eine Regel und keine Zufallsziehung; weil jede Datei ihren eigenen Seed-Strom hat, sind die ersten N eine unverzerrte Stichprobe (Endungsmix von ooxml/opendocument/plain eingeschlossen).

**Zuführung ohne Umbau des Produkts:** Ordner `teilkorpus/` im Home des Kontos `lasttest`, gefüllt mit **Hardlinks** (`cp -al`, gleiche Bytes, kein Plattenplatz, gleiche Rechte `www-data`), danach `occ files:scan --path=lasttest/files/teilkorpus`. Alle übrigen Top-Level-Ordner JEDES Homes (mindestens `loadtest`; Sprachfall- und Drill-Ordner vorher auf der Box inventarisieren) kommen in die Ordner-Ausschlüsse des Produkts (`ExclusionService`, Präfix relativ zur Mount-Wurzel, höchstens 64 Präfixe, appconfig-Schlüssel `exclusions`). Die Ausschlüsse werden VOR dem Nullstand gesetzt, damit keine Aufräumaktion anläuft. Zähltor: nach dem Crawl muss der Vorrat genau 5.000 Dateien kennen, sonst Abbruch der Zelle.

Reihenfolge-Zwang: der Ordner `teilkorpus/` entsteht erst NACH der Vollzelle auf m7g.large, sonst zählt der Vollkorpus 5.000 Duplikate mit. Auf V-X (x86) wird er gleich beim Aufbau angelegt.

**Committet wird:** die Auswahlregel (Skript), die Liste `name,bytes,sha256` der 5.000 Dateien, gelesen auf der Box aus dem Snapshot, und ihre Listen-Prüfsumme (Muster `build_load_corpus`: sha256 über die sortierte Liste). Inhalt ist synthetisch (D-02 von Phase 5), die Liste trägt keine Geheimnisse.

### Pattern 4: Messgrößen (Forschungsfrage 4)

| Größe | Quelle | Regel |
|---|---|---|
| RAM-Spitze der Zelle | `rss_sampler.sh`, Intervall 2 s, **anon**-Maximum der Container-cgroup | die Zahl der Zelle; `memory.peak` nur daneben, weil er den Seitencache des mmap-Index enthält (v1.2: `memory.peak` 2.044.096.512 bei 2-GiB-Grenze) |
| OOM-Beweis | Schlusszeile `rss_sampler.sh`: `memory.events`, OOMKilled, `RestartCount` | vierteilig wie bisher |
| Kosten je Slot | `proc_anon_sampler.sh`, Intervall **1 s**, RssAnon und VmHWM je Prozess | Hauptprozess (langlebige PID) getrennt; je Zeitpunkt Summe über Sandbox-Kinder plus tesseract, geteilt durch `slotsInForce`; Maximum; daneben VmHWM-Paar Kind plus tesseract als Obergrenze (fängt Spitzen zwischen den Abtastungen). Vergleichswert B2: Kind 136,4 plus tesseract 98,8 = 235 MiB |
| Grundlinie Hauptprozess | dieselbe Reihe, Hauptprozess-Maximum mit geladenem Modell | Vergleich mit `MAIN_PROCESS_BASELINE_BYTES` (1.257,5 MiB) |
| fp32-Mehrbedarf | Hauptprozess-Maximum St-fp32 minus St-int8 derselben Box | Vergleich mit `FP32_EXTRA_BYTES` (367 MiB) |
| Nextcloud-Kernlast r | `cpu_sampler.sh` (Box minus Container) während OCR | Vergleich mit `NEXTCLOUD_CORE_LOAD` 0,25 |
| Durchsatz | Statusreihe der Admin-Übersicht alle 120 s (Muster `96d-statusbeobachter.py`) | **Dateien je Stunde** über den ganzen Lauf bis zum letzten Vektor (Verdikte / (t1 minus t0)), **OCR-Seiten je Sekunde** über die reine OCR-Phase, Laufzeit beider Spuren; wie docs/performance.md ("Dateien je Sekunde über den ganzen Lauf", "s je OCR-Datei") |
| Leerlaufanteil | Anteil der Lesungen mit leerem Vorrat | über 10 Prozent heißt: zulaufgebunden (Cron/Top-up), nicht rechengebunden; im Bericht so benennen |
| Wächter | Block `guard` der Statusroute: `effective`, `cause`, `throttled`, `slotsInForce` am Ende | eine Absenkung mitten in der Zelle heißt: gemessen wurde teils eine andere Stufe; markieren |

**Rechnung je Zelle für die +10-Prozent-Regel (D-28-08), VOR der Messung in `00-ablauf.md` festschreiben:**

```
Rechnung_anon = MAIN_PROCESS_BASELINE_BYTES
              + slotsInForce x OCR_SLOT_COST_BYTES
              + (1 + embed_slots) x EMBED_ACTIVATION_BYTES
              + CUTTER_LOAD_BYTES (falls nicht in der Grundlinie enthalten, einmal klären)
              + FP32_EXTRA_BYTES (nur fp32)
              + Writer-Heap des Profils minus Sparsam-Heap
getragen, wenn gemessenes anon-Maximum <= 1,10 x Rechnung_anon
```

Die Summe ist eine Empfehlung, die der Planer gegen `EmbedRunner._need` und `probe.pending_load_bytes` abgleichen muss, damit Rechnung und Produkt dieselben Posten zählen. [ASSUMED]

**Store-Zahl (SC2):** nach der Vollzelle auf m7g.large `94c-bodensatz-zyklen.sh` (zwei Zyklen, Ruhezeit 120 s): Marke C1 gegen 730,2 MB (v1.2 731,9, v1.3 730,2 und 729,3 in der Nachanfahrt). Die Toleranz "weicht nicht ab" ist nicht festgelegt, siehe Open Questions.

### Pattern 5: Die Probe headless über die Produktroute (Forschungsfrage 5)

- Routen (`php/lib/Controller/ProfileSettingsController.php`): `POST /apps/findling/admin/profile/check` mit `profile`, `precision`; `GET /apps/findling/admin/profile/check` (Zustand, führt idempotent das takeOver aus); `POST /apps/findling/admin/profile` nur Abwärtswege. Admin-Übersicht: `GET /apps/findling/admin/overview`. [VERIFIED: codebase]
- Schutz: angemeldeter Admin plus Anfrage-Token der Sitzung, auch für GET (SecurityMiddleware). Also Cookie-Anmeldung nach `probe_page_login.sh` (Token aus `data-requesttoken`, `Origin`-Kopf bei der Anmeldung, sonst Umleitung zurück zum Formular), danach Token aus einer Seite der Sitzung lesen und als Kopf `requesttoken` senden.
- Ablauf: POST check -> alle 2 s GET check bis `state=done` -> Verdikt, Ursache, `numbers` (`slots`, `need`, `available` oder `reserve`/`required`) in die Rohdatei. Die gemessene Slot-Kosten der Probe selbst steht NICHT in `numbers` (`NUMBER_KEYS`), nur indirekt über `need`; für D-28-08 zählt deshalb die Sampler-Reihe.
- Zugangsdaten nur aus Datei oder Umgebung, nie als Argument (Prozessliste), Cookie-Glas in `mktemp -d` und danach gelöscht.
- Erzwingen (D-28-05): `occ config:app:set findling profile --value=standard|performance` und bei fp32 `model_precision --value=fp32`; occ überspringt die Probe, Wirkung "Sekunden bis rund 25 Minuten" (docs/profiles.md). Markierung in der Rohdatei und im Bericht je Zelle.
- Gegenprobe der Probe je Zelle: `fits` gegen "kein Wächtereingriff, kein OOM, Reserve am Tiefpunkt >= 235 MiB"; `narrow` gegen "Reserve am Tiefpunkt < 235 MiB oder Drossel"; `nofit` gegen "Drossel, Absenkung oder OOM". Widerspruch in beide Richtungen ist ein SC4-Fall für den Owner.

### Pattern 6: fp32-Zellen (Forschungsfrage 6)

- **Knapp: c7a.xlarge (4 Kerne, 8 GiB), großzügig: c7a.4xlarge (16 Kerne, 32 GiB)**, wie in D-28-07 genannt. Begründung: c7a.xlarge ist die typische Selfhost-Box aus D-28-04 und die kleinste, auf der Standard vorgeschlagen wird; m7g.large mit 2g-Grenze wäre zwar knapper, rechnerisch sicher "passt nicht" (Grundlinie 1.257,5 plus fp32 367 plus Slot 235 plus Reserve 235 MiB = 2.094,5 MiB > 2.048 MiB) und würde nur einen Erzwingungs-OOM messen.
- Quelle: `https://github.com/street1983nk/nextcloud-search/releases/download/<FP32_RELEASE_TAG>/<FP32_ASSET_NAME>`, 470.268.510 Bytes, sha256 `ca456c06...8665` (`backend/src/findling/embed/weights.py`); Deckel `PROBE_DOWNLOAD_SECONDS` 600 s. [VERIFIED: codebase]
- Reihenfolge-Zwang: Nullstand VOR der fp32-Probe, weil `--rm-data` die geholte Datei mitnimmt; mit leerem Index löst `fits` keine teure Neuberechnung aller Vektoren aus (27-15-Hinweis).
- Gemessen wird zusätzlich der fp32-Mehrbedarf gegen St-int8 derselben Box (siehe Pattern 4).

### x86-Lücken des Runbooks (Forschungsfrage 2)

| Stelle | ARM heute | x86 c7a | Maßnahme |
|---|---|---|---|
| AMI | `ami-0e79e661e73ddfac9` arm64 (Block 3, `aws_box.sh` Zeile 95) | Ubuntu 24.04 amd64 | vor der Anfahrt kostenlos lesen: `aws ec2 describe-images --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"`; auch das arm64-AMI noch einmal lesen (Canonical deregistriert alte) |
| Typwechsel arm -> x86 | `modify-instance-attribute` m7g.large <-> m7g.4xlarge | **nicht möglich**, Architektur hängt am AMI | zweite Instanz; innerhalb c7a Typwechsel xlarge -> 2xlarge -> 4xlarge -> 8xlarge |
| Volume | eines aus dem Snapshot | zweites Volume V-X aus demselben Snapshot | V-A hat arm-Inhalte und bleibt der ARM-Box; beide mit `aws_box.sh restore` umgetaggt |
| Zone | `eu-central-1c` | c7a-Angebot in 1c nicht geprüft | `describe-instance-type-offerings --location-type availability-zone` (kostenlos); sonst V-X in einer Zone mit Angebot erzeugen |
| containerd-Store des Snapshots | arm64-Inhalte der AIO-Abbilder | keine amd64-Schichten | jedes Abbild `docker pull --platform linux/amd64 <tag>`; AIO-Container ggf. über den Mastercontainer neu erzeugen, Volumes bleiben |
| PostgreSQL-Datenverzeichnis (AIO, PostgreSQL 18.6) | auf arm64 initialisiert | Start auf x86_64 offiziell nicht zugesichert (char-Signedness, Ausrichtung) | Tor: Start, `occ status`, `REINDEX DATABASE`, Stichprobe `occ files:scan --path` eines Ordners; Rückfall Dump/Restore auf ARM vor dem Umzug oder Harness B |
| lokale Registry `localhost:5000` | arm64-Abbilder der Box | irrelevant | Abbild per Digest von ghcr (Multi-arch-Index) |
| Block 5 `mem=4G` | nur m7g.large | entfällt | vor dem Typwechsel auf m7g.4xlarge Drop-in entfernen (v1.3-Muster) |
| Block 12 harte Grenze 2g | nur m7g.large | **keine Grenze** empfohlen, damit die Formel die Box sieht | `docker update --memory 0` entfernt eine Grenze nicht (27-15); die Registrierung je Nullstand setzt ohnehin 0 [ASSUMED: keine Grenze gewollt] |
| `aws_box.sh stop`-Kosten | m7g.large-Satz gepinnt | falsch für jeden anderen Typ (Pitfall 9 v1.3) | entweder kleine Werkzeugänderung (Typ aus `describe-instances`, Satztabelle, Test in `test_ops_scripts.py`) oder Stempel mal gelesener Satz von Hand; Empfehlung Werkzeugänderung |
| `box.env` | eine Instanz | zwei Instanzen | zwei Zustandsverzeichnisse über `FINDLING_LOADTEST_DIR` (z. B. `.../arm`, `.../x86`) |
| `00-typwechsel.sh` | Typen m7g fest verdrahtet | c7a-Kette | Zieltyp als Argument, Rückfall-Typen je Familie |
| Shutdown-Verhalten | `stop` (Block 3) | neue Instanz | `--instance-initiated-shutdown-behavior stop` beim Erzeugen, `vorpruefung` vor jeder Kette |
| A-Record, known_hosts | ARM-Adresse | x86-Adresse | nach jedem Start neu setzen, vor dem ersten Daemon-Start (negative DNS-Antwort rund 3 min) |
| Quota | m7g zählt | c7a zählt in dieselbe Standard-Quota | c7a.8xlarge nur bei gestoppter ARM-Box; vorher `service-quotas get-service-quota --service-code ec2 --quota-code L-1216C47A` lesen [ASSUMED: Quota-Code] |

Unverändert bleiben: Security Group und Schlüsselpaar (eine VPC, beide Instanzen), Blöcke 6, 7, 9, 10, 11, 13, Abbildwechsel per Digest mit Baumhash-Beweis, Cron-Gate, Geheimnisregel.

### SC4: Rückfluss in Formel und Probe (Forschungsfrage 7)

| Ort | Heute | Wirkung einer Änderung |
|---|---|---|
| `backend/src/findling/config.py:889` | `OCR_SLOT_COST_BYTES = 235 * MIB` | Formel (`profile._memory_term`), Drossel/Wächter, Probe (`judge` rechnet `max(gemessen, Konstante)`, `first_slot_admitted`) |
| `config.py:916`, `config.py:928` | `EMBED_LANE_RESERVE_BYTES = GUARD_RESERVE_BYTES = OCR_SLOT_COST_BYTES` | folgen automatisch; damit ändern sich Reserve-Schwelle "passt knapp", Wächter-Headroom und Einbettungsreserve mit |
| weitere Formeleingänge | `MAIN_PROCESS_BASELINE_BYTES` 1.257,5 MiB, `FP32_EXTRA_BYTES` 367 MiB, `EMBED_ACTIVATION_BYTES` 27 MiB, `NEXTCLOUD_CORE_LOAD` 0,25 | nur ändern, wenn die Messung mehr als 10 Prozent abweicht und der Owner es entscheidet |
| Test-Pin | `backend/tests/test_config.py:1291` `assert OCR_SLOT_COST_BYTES == 235 * 1024 * 1024` | neuer Wert, Quelle als Kommentar |
| Tests mit Rechenbeispielen | `test_profile.py`, `test_probe.py`, `test_probe_run.py`, `test_guard.py`, `test_poller.py` (Zeile 4226f. nennt "235 MiB" im Kommentar) | Erwartungen neu rechnen, nicht nur Konstante tauschen |
| Baumhash-Pin | `backend/tests/test_measurement_scripts.py:1532f.` `PACKAGE_FILES_TODAY`, `PACKAGE_TREE_HASH_TODAY` | jede Änderung unter `backend/src/findling` bewegt den Hash; Kommentarblock nach dem Muster der Datei; PHP-Pin nur bei PHP-Änderung |
| Texte | `docs/profiles.md` Zeilen 68, 177, 183; `docs/admin-page.md` Zeile 531 ("235 MiB") | nachziehen; Katalogsätze in `php/l10n` prüfen (Grep fand in admin.php keine "235") |
| Store-Gate | `backend/tests/test_store_metadata.py:356` `RESIDENT_FIGURE = "730.2"` | bleibt, außer Sparsam weicht ab (SC2, Owner) |

Reihenfolge: SC4-Änderung erst nach der letzten Zelle. Das gemessene Abbild ist `ghcr.io/street1983nk/findling_backend:<voller SHA von c87a0239>` (letzter gepushter Stand; lokal danach nur Doku-Commits, `git diff origin/main..HEAD -- backend/src php scripts` ist leer). Neue Laufskripte unter `docs/measurements/...` berühren den Baumhash nicht. Die SC4-Änderung macht die Formel nur konservativer, wenn der Wert steigt; eine Nachmessung ist dann nicht zwingend, aber der Bericht sagt, dass die Messung am Vorgängerabbild lief.

### Abbau mit Nachweis (Forschungsfrage 8)

1. Endmessungen und Rohdaten sichern, Kostenrohdatei (Schlusszahlen gegen Deckel, Differenz) committen VOR `destroy` (Runbook 2.6).
2. Je Box: `stop`, Sicherung `box.env`, `FINDLING_STATE_BACKUP`, `destroy` (Instanz, Volume, Security Group erst beim zweiten Abbau, weil beide Instanzen sie teilen).
3. Von Hand: `delete-key-pair` plus Rücklesen `InvalidKeyPair.NotFound`; A-Record entfernen.
4. **Neu gegenüber allen bisherigen Abbauten:** `aws ec2 delete-snapshot --snapshot-id snap-03f1d1d9ad9262704`, Rücklesen `describe-snapshots` mit `InvalidSnapshot.NotFound`; Tag-Sweep über BEIDE Tagwerte (`findling-phase5`, `findling-corpus-keep`) muss leer sein.
5. Kostenüberblick über alle 17 freigeschalteten Regionen: 0 Instanzen, 0 Volumes, 0 Adressen, 0 Schlüsselpaare, 0 eigene AMIs, **0 Snapshots** (bisher "genau einer"). Das Runbook (Abschnitt 8, Schritte 7 bis 9) wird entsprechend fortgeschrieben.
6. Empfohlener Zeitpunkt der Snapshot-Löschung: nach den SC4-Owner-Entscheiden. Muss eine Stufe nachgemessen werden, braucht sie den Snapshot; bis dahin kostet er rund 0,10 USD je Tag. Instanzen und Volumes gehen sofort nach der letzten Zelle.

### Owner-Checkpoints (Forschungsfrage 9)

| Nr | Wann | Was | Blockierend |
|---|---|---|---|
| C1 | vor jeder kostenpflichtigen Ressource | Rechenblatt, Variante A/B, Anker ja/nein, Deckel USD; Zeile "Anfahrt freigegeben: <Datum>, Deckel ..." | ja (SC1) |
| C2 | vor dem x86-Umzug, falls das Machbarkeitstor scheitert | Rückfall Dump/Restore oder Harness B | ja |
| C3 | Deckel erreicht | weiter, abbrechen, Abbau (D-28-02) | ja |
| C4 | nach der Vollzelle | Store-Zahl C1 gegen 730,2 MB, falls außerhalb der Toleranz | ja für REL-04 |
| C5 | nach allen Zellen | je Zelle über +10 Prozent oder mit Probe-Widerspruch: Formel nachziehen oder Stufe nicht anbieten (SC4) | ja |
| C6 | vor `delete-snapshot` | irreversibel, obwohl in D-26-10 beschlossen: Bestätigung "Snapshot löschen" | ja |
| C7 | nach dem Bericht | Push der Commits | ja (Owner-Regel) |

### Anti-Patterns to Avoid
- **Messen, während `effective` noch das alte Profil nennt:** die Zelle misst die falsche Stufe.
- **`findling:purge` als Nullstand:** entfernt die appconfig mit Profil und Ausschlüssen; Nullstand nur über `--rm-data` plus `93-nullstand.sh`.
- **`memory.peak` als RAM-Spitze:** enthält den Seitencache des mmap-Index.
- **Timer mit `shutdown -h` beim Deckel (v1.3-Muster):** widerspricht D-28-02; beim Deckel startet nur keine neue Zelle. Selbstabschaltung nur nach der letzten Zelle einer Kette.
- **Planwerte aus der erhofften x86-Geschwindigkeit:** genau der Fehler, der den v1.1-Deckel gerissen hat.
- **SC4-Änderung vor den Zellen:** Baumhash und Abbild laufen auseinander.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| RAM-Zahl eines Containers | eigene `docker stats`-Schleife | `rss_sampler.sh` | liest die cgroup selbst, OOM-Beweis, Test hält das Docker-Client-Wort fern |
| Summe über Container | Summe der Maxima | `rss_digest.py` | Summe je Zeitpunkt, dann Maximum |
| Wer im Container hält Speicher | `ps`-Parsing mit Argumenten | `proc_anon_sampler.sh` | liest nur Name/RssAnon/VmHWM, keine Pfade (T-02-14) |
| Abbildwechsel | eigenes Register-Skript | `92d-wechsel.sh`/`92b-wechsel.sh`-Muster mit `40b-baumhash.sh` | Digest ist die Notiz, Baumhash der Beweis; alle Fallen der v1.2 sind darin |
| Nullstand | eigene Zählung | `93-nullstand.sh` | 360-s-Frist gegen die langsamste Uhr, `-n` |
| Cron-Takt | Annahme 300 s | `97-cron-vorpruefung.sh` | Rückgabewerte 25/26 erzwingen die Pflichtzeile |
| Store-Zahl | neue Grundlastmessung | `94c-bodensatz-zyklen.sh` | gleiche Messgröße wie 730,2 MB |
| Box-Kosten | Kopfrechnung | `aws_box.sh stop`/`status` (nach Satztabelle) oder Stempel mal gelesener Satz | Kostenhistorie in `box.env`, Rückfluss in 2.1 |
| Teilkorpus-Auswahl | Zufallsziehung | Regel über die Indexbereiche von `allocate(50000)` | reproduzierbar ohne Seed-Verwaltung |

**Key insight:** Jede Falle dieser Anfahrt ist schon einmal in bezahlter Zeit aufgefallen; die Werkzeuge tragen die Korrekturen. Neu gebaut werden nur Kette, Zelle, Probe-Route, Teilkorpus und Slot-Auswertung, und die bekommen boxlose Tests.

## Common Pitfalls

### Pitfall 1: Das Profil wirkt verzögert
**What goes wrong:** Probe speichert (`profileStored true`), Container läuft weiter mit `effective economy` (27-15 Rohdatei 02).
**How to avoid:** Wirksamkeitstor vor dem Trigger; Bewaffnung erneut, wenn nach einer Frist nichts wirkt.
**Warning signs:** `slotsInForce` 1 in einer Standard-Zelle auf 16 Kernen.

### Pitfall 2: Neuer Container läuft mit dem Profil der Vorzelle an
**What goes wrong:** appconfig überlebt `--rm-data`; der Erstindex startet im alten Profil, bevor die Probe läuft.
**How to avoid:** Abwärtsweg auf economy/int8 vor jedem Nullstand; Vorrat erst nach Probe und Wirksamkeit füllen.

### Pitfall 3: Zulaufgebundener Durchsatz auf großen Boxen
**What goes wrong:** 16 Slots leeren den Vorrat schneller, als Crawl und Cron (300 s) nachliefern; die Zahl misst den Zulauf.
**How to avoid:** Leerlaufanteil je Zelle ausweisen; Cron-Gate je Box; Befund benennen statt deuten.

### Pitfall 4: Lazy Loading des Snapshot-Volumes
**What goes wrong:** Blöcke kommen beim ersten Lesen aus S3, die erste Zelle ist langsamer [CITED: AWS-Doku].
**How to avoid:** `fio --filename=/dev/nvmeXn1 --rw=read --bs=1M --iodepth=32 --ioengine=libaio --direct=1 --name=volume-initialize` je Volume vor der ersten Zelle, mit Zeitstempeln; das Gerät über die Größe finden (Block 7), nie über den Namen.

### Pitfall 5: arm64-Inhalte auf der x86-Box
**What goes wrong:** containerd-Store kennt nur arm64-Schichten, Container starten nicht ("exec format error" oder fehlender Inhalt); PostgreSQL-Datenverzeichnis aus arm64.
**How to avoid:** Machbarkeitstor mit Zeitdeckel auf c7a.xlarge; vorher lokal kostenlos proben (Docker Desktop mit qemu: PostgreSQL-18-Cluster unter `--platform linux/arm64` anlegen, dann mit amd64 starten, REINDEX; kleines Multi-arch-Abbild erst arm64, dann amd64 ziehen und denselben Container starten).

### Pitfall 6: Kostenzeilen von `aws_box.sh` für falsche Typen
**What goes wrong:** `stop` rechnet jede Laufzeit mit 0,0978 USD/h (Pitfall 9 der v1.3); auf c7a.8xlarge Faktor 19 zu wenig.
**How to avoid:** Satztabelle je Typ im Werkzeug oder Stempel je Typwechsel; Deckel-Prüfung nie aus `BOX_LAST_UPTIME_COST_USD` allein.

### Pitfall 7: Hardlinks und Ausschlüsse falsch herum
**What goes wrong:** Teilkorpus vor der Vollzelle angelegt (Duplikate), oder ein Top-Level-Ordner vergessen (Zähltor passt nicht).
**How to avoid:** Inventar aller Homes auf der Box, Zähltor exakt 5.000, Ausschlussliste in die Rohdatei.

### Pitfall 8: Wächter senkt mitten in der Zelle ab
**What goes wrong:** gemessene Spitze gehört zu zwei Stufen.
**How to avoid:** `guard`-Block am Ende lesen; Absenkung als Befund der Gegenprobe führen, nicht als Messfehler verwerfen.

### Pitfall 9: Rohdaten mit Kennungen
**What goes wrong:** IP, Instanz- oder Volumekennung, Konto in `docs/` (Gate `test_public_artifacts.py` rot, öffentlicher Commit).
**How to avoid:** Ausgaben von `aws_box.sh` aufs Terminal, in Rohdateien nur Platzhalter; Konto nur als `konto-ist-erwartet ja`.

### Pitfall 10: Ausführungsbit
**What goes wrong:** Laufskripte mit `100644` im Index enden auf der Box mit 126 (v1.2).
**How to avoid:** `git update-index --chmod=+x` vor dem Commit oder `chmod +x` vor dem ersten Block, mit `ls -l`-Rücklesung.

## Code Examples

### Probe über die Route (Kern, Skizze für `11-probe-route.py`)
```python
# Source: php/lib/Controller/ProfileSettingsController.php, scripts/dev/probe_page_login.sh
# stdlib only; the box has python3 but no requests.
import http.cookiejar, json, re, time, urllib.parse, urllib.request

def session(base: str, user: str, password: str) -> tuple[urllib.request.OpenerDirector, str]:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    form = opener.open(f"{base}/login").read().decode()
    token = re.search(r'data-requesttoken="([^"]+)"', form).group(1)
    body = urllib.parse.urlencode({"user": user, "password": password, "requesttoken": token}).encode()
    opener.open(urllib.request.Request(f"{base}/login", body, headers={"Origin": base}))
    page = opener.open(f"{base}/settings/admin/findling").read().decode()
    return opener, re.search(r'data-requesttoken="([^"]+)"', page).group(1)

def probe(opener, token: str, base: str, profile: str, precision: str) -> dict:
    headers = {"requesttoken": token, "Content-Type": "application/json"}
    start = urllib.request.Request(f"{base}/apps/findling/admin/profile/check",
        json.dumps({"profile": profile, "precision": precision}).encode(), headers=headers, method="POST")
    json.load(opener.open(start))
    while True:
        state = json.load(opener.open(urllib.request.Request(
            f"{base}/apps/findling/admin/profile/check", headers=headers)))
        if state.get("state") == "done":   # key names: check against 27-15 raw 02
            return state
        time.sleep(2)
```

### Teilkorpus-Regel (Skizze für `01-teilkorpus.py`)
```python
# Source: scripts/dev/build_load_corpus.py allocate() and generate() ordering
RULE = {"scan_single": 1800, "scan_multi": 100, "text_pdf": 1500, "ooxml": 900,
        "opendocument": 400, "plain_text": 200, "image": 100, "oversize": 0}
# counts = allocate(50000); walk CATEGORIES in order, keep the first RULE[key]
# indices of each category, match files by their five digit prefix, then write
# name,bytes,sha256 read from disk and the sha256 over the sorted list.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| eine Box, ein Volllauf | Matrix mit rund 20 Zellen, Erstindex je Zelle | Phase 28 | Nullstand wird zum häufigsten Posten |
| Deckel in Stunden zum m7g.large-Satz | Deckel in USD je Box-Satz | v1.3 (B4) | Stundenzahl allein sagt nichts mehr |
| Timer schaltet beim Deckel ab | Deckel stoppt nur neue Zellen | D-28-02 | Timerlogik ändern |
| Korpus-Snapshot bleibt | Snapshot wird gelöscht | D-26-10 | Abbau-Checkliste Schritt 8/9 umschreiben |
| manuelle Volume-Initialisierung | optional Provisioned Rate for Volume Initialization | AWS, neu | Aufpreis, nur mit Owner |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | OCR- und Einbettungsraten der m7g.large gelten als Planwert auch für c7a | Rechenblatt | x86 ist vermutlich schneller: Deckel zu hoch, nicht zu niedrig |
| A2 | Einbettung rund 0,45 s je Text-Datei, abgeleitet aus 19 h 20 minus 12 h 49 | Rechenblatt | Leistungs-Zellen länger als 45 min; Reserve fängt es |
| A3 | MemAvailable rund MemTotal minus 1 GiB auf den Matrix-Boxen | Slottabelle | andere Slotzahlen; Probe zeigt die echten |
| A4 | Keine harte Containergrenze auf den Matrix-Boxen gewollt | x86-Lücken | Owner will vielleicht eine Grenze; dann andere Formelwerte |
| A5 | amd64-Pull in einen arm64-befüllten containerd-Store reicht, damit die AIO-Container starten | x86-Lücken | Machbarkeitstor scheitert, Rückfall kostet Zeit |
| A6 | PostgreSQL 18 startet auf x86_64 mit dem arm64-Datenverzeichnis nach REINDEX sauber | x86-Lücken | Datenbank kaputt oder still falsch; Rückfall Dump/Restore |
| A7 | c7a-Typen sind in eu-central-1c verfügbar | x86-Lücken | Volume V-X in anderer Zone erzeugen |
| A8 | Angehaltene Instanzen zählen nicht gegen die vCPU-Quota; Quota-Code L-1216C47A | Pattern 2 | c7a.8xlarge startet nicht |
| A9 | Rechnung_anon-Summe zählt dieselben Posten wie das Produkt | Pattern 4 | +10-Prozent-Urteil falsch |
| A10 | Zellen-Overhead 45 min inkl. bis zu 25 min Wirkungsverzug | Rechenblatt | bei 20 Zellen schnell mehrere Stunden Differenz |
| A11 | Fester Seitenstrom je Datei macht "die ersten N" zur unverzerrten Stichprobe | Teilkorpus | Endungsmix leicht schief; unkritisch |

## Open Questions

1. **Toleranz "Sparsam weicht nicht von der Store-Messzahl ab" (SC2)**
   - What we know: 731,9 (v1.2), 730,2 und 729,3 MB (v1.3) auf derselben Box.
   - What's unclear: eine Grenze ist nirgends festgelegt, und Phasen 24 bis 27 haben Code in den Sparsam-Pfad gebracht.
   - Recommendation: Owner legt vor der Anfahrt fest (Vorschlag: plus/minus 2 Prozent, rund 15 MB); in `00-ablauf.md` vor der Messung.
2. **Anker-Zelle Sparsam-Teilkorpus auf m7g.large**
   - Recommendation: mit ins Blatt (0,53 USD), Owner entscheidet an C1.
3. **Variante A oder B des Teilkorpus**
   - Recommendation: A (entspricht "Größenordnung 5.000"), B nur bei Deckelwunsch unter 50 USD.
4. **Harte Grenze auf Matrix-Boxen**
   - Recommendation: keine, im Protokoll `memory.max max`; Owner bestätigt an C1.
5. **Zeitpunkt der Snapshot-Löschung**
   - Recommendation: nach C5 (SC4-Entscheide), Instanzen und Volumes sofort nach der letzten Zelle.
6. **Standard und Leistung auf der Referenzbox**
   - What we know: D-28-06 spricht von Zellen Box x Profil, SC2 von "Referenzbox und Mehrkern-Box".
   - Recommendation: St-T und L-T auf m7g.large sind im Blatt (rechnerisch 1 Slot, Probe vermutlich "passt nicht" oder "knapp", also erzwungen und ein echter Wächtertest).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| AWS CLI v2 | Box-Lebenszyklus | ✓ | 2.36.39 | nicht nötig |
| gh | CI-Laufnummer (Runbook 3, Zeile 1), Digest | ✓ | 2.92.0 | |
| uv | Gates, Offline-Rechnungen | ✓ | 0.11.7 | |
| python3 | Entwicklungsmaschine | ✓ | 3.13.1 | |
| nslookup, jq (Entwicklungsmaschine) | A-Record, JSON | ✓ | | curl --resolve |
| Sicherung der Systemplatte | Block 9 | ✓ | `~/.findling-loadtest/systemplatte-2026-09/home-ubuntu-work.tar.gz` | |
| privater SSH-Schlüssel | SSH | ✓ | `~/.ssh/findling-loadtest` plus `.pub` (Vorprüfung 10/11: Paar in AWS noch vorhanden?) | neu erzeugen |
| `box.env` | aws_box.sh | ✗ (abgebaut, gewollt) | | Block 4 von Hand, zwei Verzeichnisse |
| AWS-Zugangsdaten infranodedev | alles | nicht geprüft (Research ohne AWS) | | blockierend bis gesetzt |
| Docker Desktop mit arm64-Emulation | lokale Vorprobe Pitfall 5 | nicht geprüft | | Tor nur auf der Box |

**Missing dependencies with no fallback:** AWS-Zugangsdaten in der Umgebung (Owner).
**Missing dependencies with fallback:** `box.env` (von Hand, Block 4).

## Validation Architecture

`workflow.nyquist_validation` ist in `.planning/config.json` `false`; der Abschnitt steht auf ausdrücklichen Wunsch des Orchestrators und ist beratend.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (backend, uv) |
| Config file | `backend/pyproject.toml` |
| Quick run command | `cd backend && uv run pytest -q tests/test_v14_abnahme.py tests/test_config.py -x` |
| Full suite command | `cd backend && uv run ruff check . && uv run ruff format --check . && PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright && uv run vulture src tests --min-confidence 80 && uv run pytest -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MESS-10 / SC1 | Rechenblatt-Zahlen aus den Posten reproduzierbar, Freigabezeile vorhanden | unit (Rechnung aus Tabelle) | `pytest tests/test_v14_abnahme.py -k deckel` | ❌ Wave 0 |
| MESS-10 / SC2 | Teilkorpus-Regel ergibt 5.000 Dateien, 2.691 Seiten, feste Bereiche | unit (offline über `allocate`) | `pytest tests/test_v14_abnahme.py -k teilkorpus` | ❌ Wave 0 |
| MESS-10 / SC2 | Zellenskript verweigert Trigger ohne Wirksamkeit, ohne Digest, bei zwei Nextclouds | unit gegen nachgestellte occ/docker (Muster `test_v13_wegwerf.py`) | `pytest tests/test_v14_abnahme.py -k zelle` | ❌ Wave 0 |
| MESS-10 / SC3 | Kette startet beim Deckel keine neue Zelle und schaltet NICHT ab | unit | `pytest tests/test_v14_abnahme.py -k deckel_erreicht` | ❌ Wave 0 |
| MESS-10 / SC3 | Rohdaten ohne Kennungen | Gate | `pytest tests/test_public_artifacts.py` | ✅ |
| SC4 | neue Slot-Kosten gepinnt, Formel/Probe/Wächter-Erwartungen neu | unit | `pytest tests/test_config.py tests/test_profile.py tests/test_probe.py tests/test_probe_run.py tests/test_guard.py tests/test_poller.py` | ✅ (anpassen) |
| SC4 | Baumhash-Pin nach config-Änderung | unit | `pytest tests/test_measurement_scripts.py -k tree_hash` | ✅ (anpassen) |
| SC2 | Store-Zahl unverändert oder Owner-Entscheid | Gate | `pytest tests/test_store_metadata.py` | ✅ |
| alle | Messung selbst | manual-only (Box) | Rohdaten und Bericht | Anfahrt |

### Sampling Rate
- **Per task commit:** Quick run plus ruff über `../scripts` bei Skriptänderungen.
- **Per wave merge:** Full suite.
- **Phase gate:** Full suite grün, Rohdaten committet, Abbau belegt, vor `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `backend/tests/test_v14_abnahme.py` , boxlose Tests für Kette, Zelle, Probe-Route (gegen einen kleinen lokalen HTTP-Stub), Teilkorpus, Slot-Auswertung, Deckel-Logik
- [ ] `test_ops_scripts.py` erweitern, falls `aws_box.sh` eine Satztabelle je Typ bekommt
- [ ] lokale Vorprobe Pitfall 5 (arm64 -> amd64 containerd und PostgreSQL) mit Rohdatei

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | ja | Admin-Anmeldung per Cookie, Passwort nur aus Datei/Umgebung, nie als Argument; Passwörter der Konten aus der Sicherung, ggf. `occ user:resetpassword` mit stdin |
| V3 Session Management | ja | Cookie-Glas in `mktemp -d`, Löschung per trap; Anfrage-Token je Sitzung |
| V4 Access Control | ja | Profilrouten nur Admin (27-15 belegt 403 für Nicht-Admin); AWS nur von der Entwicklungsmaschine |
| V5 Input Validation | teilweise | Routen prüfen geschlossene Mengen selbst; Skripte prüfen Digest-Gestalt (`sha256:<hex>`) |
| V6 Cryptography | ja | fp32 nur mit sha256-Prüfung (Produkt), Abbild per Digest, Baumhash als Beweis; nichts selbst gebaut |

### Known Threat Patterns for diese Anfahrt

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| AWS-Schlüssel auf der Box oder im Protokoll | Information Disclosure | nur Umgebung der Entwicklungsmaschine, Werkzeuge prüfen nur Gesetztheit (T-22-13) |
| falsches Konto (Cherif83) | Tampering/Kosten | `aws sts get-caller-identity` am Terminal gegen den erwarteten Wert, in der Rohdatei nur `konto-ist-erwartet ja` |
| SSH offen zur Welt | Spoofing | SG-Regel 22 nur `<eigene-adresse>/32`, Adresswechsel nachziehen (Runbook 3, Zeile 15) |
| öffentliche Nextcloud mit Admin-Konto unter `loadtest.infranode.dev` | Elevation | Laufzeit kurz halten, starke Passwörter, Record nach Abbau entfernen; 80/443/UDP 443 nur für AIO |
| Kennungen/IPs in committeten Rohdaten | Information Disclosure | Platzhalter, Gate `test_public_artifacts.py` |
| unverschlüsselter Snapshot und Volumes | Information Disclosure | Inhalt synthetisch (T-05-18), Löschung am Ende mit Nachweis |
| Download der fp32-Datei manipuliert | Tampering | Produkt prüft Größe und sha256, sonst kein Speichern |
| zweite Nextcloud löscht Messvolume per `--rm-data` | Tampering | Zählung "genau eine" unmittelbar vor jedem `--rm-data` (Block 13) |
| Kosten laufen nach dem Abbau weiter | Denial of Wallet | Sweep über 17 Regionen, beide Tagwerte, Snapshot-Nichtexistenz |

## Sources

### Primary (HIGH confidence)
- Codebase: `docs/runbook-messbox.md` (Abschnitte 1 bis 9), `docs/performance.md` (Zeilen 601ff., 1554ff., 1944ff., 2114ff., 4228ff., 4557ff., 4737ff.), `docs/profiles.md`, `scripts/ops/*`, `scripts/dev/build_load_corpus.py`, `backend/src/findling/config.py`, `profile.py`, `probe.py`, `hardware.py`, `embed/weights.py`, `php/lib/Controller/ProfileSettingsController.php`, `php/lib/Service/ExclusionService.php`, `php/lib/Command/*`, Rohdaten `2026-09-probe-live`, `2026-09-v13-messung`, `2026-09-v12-messung/skripte`
- Öffentliche AWS On-Demand-Preiskarte Frankfurt (Manifest 2026-09-25T17:45:21Z), gelesen 29.09.2026
- https://docs.aws.amazon.com/ebs/latest/userguide/ebs-initialize.html , Initialisierung von Volumes aus Snapshots, fio/dd, Provisioned Rate

### Secondary (MEDIUM confidence)
- PostgreSQL pg_upgrade-Doku (https://www.postgresql.org/docs/current/pgupgrade.htm) und Mailinglisten-Thread zu x86_64/ARM64 (https://www.postgresql.org/message-id/CAAP012m48JhfO8J=7ceijFZFKH35oizZPNg3KBhMB-4eTNuE4w@mail.gmail.com): Architekturwechsel des Datenverzeichnisses nicht zugesichert, char-Signedness seit PostgreSQL 18 im Cluster vermerkt

### Tertiary (LOW confidence)
- Verhalten des containerd-Image-Store beim Nachziehen einer zweiten Plattform für bestehende Container (nur Trainingswissen, Vorprobe nötig)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH , alles vorhanden und gelesen
- Rechenblatt: MEDIUM , Sätze gelesen, Laufzeiten aus ARM-Ist-Werten übertragen
- Architecture (Zellenablauf, Teilkorpus, SC4-Orte): HIGH
- x86-Umzug: LOW bis MEDIUM , nie gefahren, Tor und Vorprobe nötig
- Pitfalls: HIGH , überwiegend aus Rohdaten früherer Anfahrten

**Research date:** 2026-09-29
**Valid until:** 2026-10-13 (Preise und AMIs können sich ändern; Sätze am Anfahrtstag neu lesen)
