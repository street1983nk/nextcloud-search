# Phase 22: Messanfahrt BL-F03 - Research

**Researched:** 2026-09-25
**Domain:** bezahlte Messanfahrt (AWS m7g.large aus Korpus-Snapshot), Messwerkzeugbau boxlos, Tantivy-Anfrageform (disjunction_max)
**Confidence:** HIGH für Codebefunde und Wiederverwendung, MEDIUM für Boxzeiten und Kosten, LOW für den Markenstand des Snapshot-Volumes (nur auf der Box lesbar)

## Summary

Die Anfahrt ist mit vorhandenen Werkzeugen zu rund zwei Dritteln fahrbar: das Runbook `docs/runbook-messbox.md` (Blöcke 1 bis 13b, Abschnitte 5 bis 8), die gefahrenen v1.2-Fassungen in `docs/measurements/2026-09-v12-messung/skripte/` (Baumhash, Cron-Gate, Bestand, Laststufen, ntfy), die ungefahrenen Nachfolgefassungen `92c-wechsel.sh` und `99d-filter-sortierung.sh`, `scripts/ops/search_load.py`, `rss_sampler.sh`, `embed.bench` und das B2-Vorbild `2026-09-nachmessung-m7g/skripte/71-ocrphase.sh`. Neu zu bauen sind W1 bis W3 samt W4-CI-Lauf (wie in der Vorarbeit beschrieben) und zusätzlich fünf Box-Werkzeuge, die die Vorarbeit nicht nennt: ein Wechsel **ohne** `--rm-data`, eine Mehrzyklus-Fassung der Bodensatzmessung, eine Kaltstart-Fassung mit Trefferpflicht, ein Leser für die M-01-Protokollzeilen und die disjunction_max-Probe.

**Der wichtigste Befund dieser Research ist ein Reihenfolgezwang.** `92c-wechsel.sh` führt in Phase B unbedingt `app_api:app:unregister --rm-data` aus (Zeilen 474 bis 480) und leert damit das Backend-Volume. Der Snapshot trägt aber genau den Index, den MESS-08 umbauen soll (Stand 10.09.2026, 52.111 / 37 / 0, Abbild vom 10.09.). Wird 92c wie in v1.2 als erster Wechsel gefahren, braucht MESS-08 vorher einen Vollreindex von rund 19 h 20 min, und der 24-h-Deckel ist gerissen. **Also: erster Wechsel mit einer neuen Fassung, die das Volume behält; 92c läuft als Wirkungsnachmessung zuletzt, nach allen indexabhängigen Messungen.** Dass `unregister` ohne Schalter das Volume behält und eine zweite Registrierung es wieder aufnimmt, ist in CI belegt (`deploy-harp.yml:2891-2895`, "Store uninstall 1/2").

**Der zweite Befund ist ein Loch in MESS-07, das der Owner entscheiden muss.** Die "6 Fehlschläge und 44 übersprungenen Dateien" der Endzahl 52.137 / 44 / 6 lagen im Volume der v1.2-Box, und dieses Volume ist am 21.09. ohne Ende-Snapshot zerstört worden (`rohdaten/07-snapshot-und-abbau.txt`: "ende-snapshot dieser anfahrt: es wurde KEINER erzeugt"). Keine committete Rohdatei nennt eine einzelne Datei. Die Annahme im BACKLOG ("Volume mounten + DB/Log lesen, kein Reindex") ist damit falsch. Der Snapshot trägt nur 52.111 / 37 / 0. Die 44 / 6 sind ohne einen neuen Vollreindex nicht benennbar, und ein Vollreindex sprengt den Deckel. Dritter Befund: **24 h und rund 3,00 USD sind mit B4 nicht gleichzeitig erreichbar**; mit B4 greift der USD-Deckel schon bei rund 17,4 Boxstunden.

**Primary recommendation:** Wave 0 baut alle Werkzeuge boxlos und fährt W4 in CI; danach geht ein Rechenblatt mit drei Owner-Fragen (44/6-Weg, USD-Deckel, disjunction_max-Entscheidungsregel) an den Checkpoint; die Anfahrt läuft in der Ordnung "Volume behalten, de,en-Messungen, Umbau auf sechs Sprachen, disjunction_max-Probe, Wegwerf-Container, 92c zuletzt, B4, Abbau" unter einem Ablaufskript mit hartem Abschalt-Timer auf der Box.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Deckel und Abbruchregel
- **D-01:** Kostendeckel im Rechenblatt: **24 Boxstunden / ~3,00 USD**
  (Rechenwert 11-17 h plus ~40% Reserve). Der Deckel steht als eigene Zeile im
  Rechenblatt, B4 als eigener Deckelposten darin (~1,25 h / ~1,00 USD).
- **D-02:** Bei Erreichen des Deckels: **HARTER STOPP** der Box (Kosten enden
  sofort), fehlende Messungen werden als LUECKEN im Messbericht dokumentiert,
  der Owner entscheidet anhand des Berichts ueber eine Nachfreigabe. Keine
  stillschweigende Verlaengerung.

#### B4-Entscheidungsregel (CI-Vorabkurve)
- **D-03:** W4 (CI-arm64, 4 Kerne) laeuft VOR dem Rechenblatt. Regel fuer B4:
  Slot-Faktor >= 1,5 auf der CI-Kurve heisst **B4 wird gefahren** (also auch im
  Zwischenbereich 1,5-3,0; Owner-Steuerung: Mehrheit der Nutzer hat viele
  Kerne, Kosten nur ~1 USD). Nur unter 1,5 entfaellt B4 (und BL-F04-Stufe 2
  kippt, siehe Research Abschnitt 5 K1).

#### disjunction_max-Folge (MESS-09)
- **D-04:** Faellt die Messung FUER disjunction_max aus, wird die Umsetzung
  **noch in Phase 22 gebaut** (Suchpfad-Aenderung, beweisbar ueber CI und
  lokale Suite, KEINE neue Box-Anfahrt dafuer). Kriterium 4 gilt woertlich:
  umgesetzt oder dokumentiert verworfen. Phase 23 haertet den Endstand.

#### Zeitnot-Prioritaet auf der Box
- **D-05:** Streichreihenfolge bei knapper Boxzeit: zuerst faellt **B7**
  (NL-Automat, kann komplett in CI), dann **B5** (onnx-Kombis, CI-Naeherung
  existiert), dann **B4** (eigener Deckelposten), dann **B2/B3** (OCR-Slots).
  Die BL-F03-Pflichtzahlen (Erfolgskriterien 2-3) und **B1** (kostet 0 min
  Zusatzzeit) fallen NIE; sie sind der Zweck der Phase.

### Claude's Discretion
- Reihenfolge der Messungen innerhalb der Anfahrt (Research Abschnitt 1.5 als
  Startpunkt), Blockzuschnitt, Auswertungsformat der Rohdaten, Gestaltung des
  Rechenblatts (Praezedenz v1.2-Messanfahrt).
- Gestrichene Posten B8/B9/B10 bleiben gestrichen (Research-Begruendung).

### Deferred Ideas (OUT OF SCOPE)
- Tantivy `num_threads` als v1.4-Hebel fuer den Umbauweg (haengt an B6-Ergebnis;
  Vergleichsmessung gehoert in CI, nicht auf die Box) , Research Abschnitt 1.2.
- Marken-Reparatur vectors.py (Gewichts-Praezision in embedding_version),
  bereits im v1.4-Umfang (Owner 25.09.).

### Weitere verbindliche Owner-Vorgaben (aus dem Auftrag, 25.09.)
- Rechenblatt = Owner-Checkpoint VOR dem Boxstart; W4-CI-Kurve VOR dem Rechenblatt.
- Phase 22 und 23 verzahnt: die Box läuft unbeaufsichtigt, während die Phase-23-Härtung lokal läuft.
- `scripts/ops/rss_sampler.sh` bleibt unverändert; NL-Automat-RAM (B7) misst der CI-arm64-Runner, nicht die Box.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MESS-07 | EINE Box-Anfahrt liefert das BL-F03-Bündel: M-01-Zahl, Wirkungsnachmessung 92c/99d, Bodensatz-Zyklus 2, die 6 Fehlschläge und 44 übersprungenen Dateien einzeln benannt, Kaltstartlatenz ohne Leerbegriff; Rechenblatt + Deckel vor dem Start; Runbook-Disziplin | Abschnitte "Wo jede Zahl entsteht", "Architecture Patterns" (Reihenfolge, 92c zuletzt), Pitfalls 1 bis 6; Open Question 1 (44/6 nicht reproduzierbar) |
| MESS-08 | Indexgröße bei sechs befüllten Sprachfeldern am Korpus-Snapshot und Wandzeit des Re-Analyse-Umbaus gegen 19 h 20 min | Abschnitt "Der Umbau auf dem Snapshot-Volume" (Auslöser, Marken, Ablesung, Erwartung Faktor rund 2,5), Pitfall 1 und 7 |
| MESS-09 | disjunction_max-Entscheid auf Messbasis; bei Vorteil umgesetzt, sonst dokumentiert verworfen | Abschnitt "disjunction_max: Codeort, Messung, Umsetzung", zwei in dieser Sitzung gefahrene Proben (Treffermenge, Snippets), Open Question 3 (Entscheidungsregel vorher festschreiben) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

| Regel | Quelle | Wirkung auf Phase 22 |
|---|---|---|
| Code, Bezeichner und Skriptkommentare Englisch oder ASCII; echte Umlaute nur in deutscher Prosa, nie in Code, Pfaden, Keywords | CLAUDE.md "Sprache", globale Regel | Box-Skripte schreiben ASCII (Präzedenz `00-ablauf.md`: "die Skripte ... schreiben ihre Kommentare und Protokollzeilen in ASCII"); Berichte mit Umlauten im Fließtext, **Abschnittsüberschriften der Mess- und Runbookdateien ohne Umlaute**, weil Prüfungen darauf zeigen |
| Keine Em- oder En-Dashes | CLAUDE.md, `test_ops_scripts.py` (DASHES) | gilt für jede neue Datei, als Gate für `scripts/ops/*` bereits erzwungen |
| Python-Qualitätsgates: ruff Vollregelsatz, ruff format, pyright basic, vulture, lokal grün vor Commit | CLAUDE.md "Qualitätsgates" | `scripts/` bekommt in CI nur ruff und ruff format (`python.yml:149-160`); `backend/` alle vier. pyright lokal mit `PYRIGHT_PYTHON_FORCE_VERSION=latest` (Memory-Regel 19.09.) |
| Security/Privacy: keine Inhalte verlassen den Server, keine Telemetrie | CLAUDE.md | Messwerkzeuge drucken nur Zahlen, Kennungen und Prozessnamen (T-02-14); der Korpus ist synthetisch, trotzdem keine Textinhalte in Rohdaten |
| Nach jeder Phase Security-, Bug- und Performance-Audit | CLAUDE.md Owner-Regel 15.08. | Phase 22 braucht am Ende ein Audit (Präzedenz `docs/audits/2026-09-phase-15/`) |
| GSD-Workflow, kein Direkteingriff | CLAUDE.md | Pläne via `/gsd:execute-phase` |
| STATE.md von Hand nachziehen, Python-Schreibzugriffe mit `newline="\n"`, `PACKAGE_TREE_HASH_TODAY` / `PHP_TREE_HASH_TODAY` im selben Commit, wenn `backend/src/findling` bzw. `php/` sich ändert | Auftrag und STATE.md 19-01 | trifft Phase 22 nur beim disjunction_max-Umbau (`backend/src/findling/query/rewrite.py`); die Werkzeuge liegen außerhalb |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Boxaufbau, Typwechsel B4, Abbau, Kosten | Entwicklungsmaschine (AWS CLI, `aws_box.sh`) | Box (Timer) | AWS-Zugangsdaten dürfen nie auf die Box (Runbook Abschnitt 3 Zeile 3); der harte Stopp läuft trotzdem boxseitig über `shutdown -h` |
| Messablauf, Samplers, Rohdaten | Box (Host-Shell, Laufverzeichnis im Klon) | Produktcontainer via `docker exec` | Präzedenz v1.2: Werkzeuge laufen auf dem Wirt, lesen die cgroup selbst |
| M-01 innerer Aufruf | Nextcloud-PHP (`ExAppService::call`, Log-Zeile) | Box (Protokoll-Leser) | die Messstelle liegt absichtlich auf der PHP-Seite (`ExAppService.php:750-769`) |
| Umbau MESS-08 | Produktcontainer (Poller-Startpfad, `index/rebuild.py`) | Statusroute (`rebuildRunning`, `rebuildDone`) | der Umbau startet nur beim Containerstart |
| disjunction_max-Probe | Produktcontainer (read side, `open_index`, `field_plan_for`) | Box (Auswertung) | die Ketten müssen registriert sein; nur das Abbild hat sie mit gleichen Listen |
| B3/B4/B5 | Wegwerf-Container desselben Digests | Box (cpuset, cgroup) | hart verdrahtete Achsen nur so messbar (Vorarbeit 1.1) |
| W4, B7 | GitHub `ubuntu-24.04-arm` (`measure.yml`) | - | kostenlos, native arm64-Hardware |
| disjunction_max-Umsetzung (falls positiv) | Backend `findling/query/rewrite.py` | Tests, Doku | Suchpfad, CI-beweisbar ohne Box (D-04) |

## Standard Stack

Keine neuen Pakete. Alles Folgende ist im Repo oder im Abbild vorhanden.

### Core (wiederverwendet, unverändert)
| Werkzeug | Ort | Zweck in Phase 22 | Status |
|---------|---------|---------|--------------|
| Runbook | `docs/runbook-messbox.md` | Blöcke 1 bis 13, Vorbedingungen 1 bis 15, Abbau-Checkliste Abschnitt 8, Rechenweg 2.5 | gefahren 20./21.09. [VERIFIED: gelesen] |
| `aws_box.sh` | `scripts/ops/aws_box.sh` | `restore`, `start`, `stop`, `status`, `prices`, `destroy` (mit `FINDLING_STATE_BACKUP`) | pinnt nur `m7g.large` (`INSTANCE_TYPE='m7g.large'`, Zeile 91) [VERIFIED: grep] |
| `40b-baumhash.sh/.py` | `docs/measurements/2026-09-v12-messung/skripte/` | Baumhash-Beweis, von 92c/92d gerufen | gefahren, Prüfsummen-Wächter |
| `97-cron-vorpruefung.sh` | ebenda | Cron-Intervall-Gate `vorher` (Abbruch 25/26), `waehrend` (27/28) | gefahren, fix aus v1.2 drin |
| `90-bestand.sh`, `93-nullstand.sh` | ebenda | Endmessung, Markenstand (`state.db` meta), `files by state` | gefahren |
| `96e-ntfy-watch.sh` | ebenda | Meldekette für den unbeaufsichtigten Lauf (Vertrag ist die Datei, die Nachricht ist Zugabe) | gefahren |
| `search_load.py` | `scripts/ops/` | Laststufen 1, 4, 8, 12, 16 (M-01-Träger), Bestandssonde `PROBE_PROGRAM` per `docker exec` | nicht anfassen (Vergleichbarkeit, v1.2-Bericht Abschnitt 5) |
| `rss_sampler.sh` | `scripts/ops/` | anon/file/slab/current/peak alle N s | UNVERÄNDERT (CONTEXT) |
| `92c-wechsel.sh`, `99d-filter-sortierung.sh` | `docs/measurements/2026-09-nachfolgefassungen/skripte/` | Wirkungsnachmessung A1 | "DIESE FASSUNG IST NICHT GEFAHREN", Wächter `NOT_DRIVEN` in `test_measurement_scripts.py:108` |
| `embed.bench` | `backend/src/findling/embed/bench.py` (im Abbild) | B5, onnx-Teil von B4: `--mode tokens-per-second --batch --sequence --threads` | vorhanden (Zeilen 748-767) [VERIFIED: grep] |
| `68-bestand-endungen.py` | `docs/measurements/2026-09-nachmessung-m7g/skripte/` | Vorbild für die Einzelliste: liest `files(path, state, reason)` read-only | Schema-Gegenprobe drin |
| `71-ocrphase.sh` | ebenda | Vorbild B2: frische Charge per WebDAV, `files:scan`, gebundene Beobachtung | gefahren 07.09. |

### Supporting (neu, boxlos zu bauen)
| Werkzeug | Ort (Vorschlag) | Inhalt | Wann |
|---------|---------|---------|-------------|
| W1 `cpu_sampler.sh` | `scripts/ops/` | `cpu.stat usage_usec` der Container-cgroup (Pfadbildung wie `rss_sampler.sh`: `system.slice/docker-<id>.scope` oder `docker/<id>`), Zeile `cpu` aus `/proc/stat`, Abschlusszeile Mittel/Maximum; verweigert statt Nullen | Wave 0, B1/B6 |
| W2 `proc_anon_sampler.sh` | `scripts/ops/` | `docker exec` in den Container, je PID `Name`, `RssAnon`, `VmHWM` aus `/proc/<pid>/status`, nie `cmdline` | Wave 0, B2 |
| W3 `ocr_slot_probe.py` | `scripts/ops/` | N Threads je eigene `ExtractionWorker` (`extract/sandbox.py:287`), `run(path, "application/pdf", size, route="ocr")` (`Route.OCR = "ocr"`, `dispatch.py:69`); Modus `single` ruft tesseract direkt mit und ohne `OMP_THREAD_LIMIT=1` | Wave 0, B3/B4/W4 |
| W4 | `.github/workflows/measure.yml` | neuer Schritt oder Job auf `ubuntu-24.04-arm`: W3 mit N = 1, 2, 4 (`--cpuset-cpus`), `embed.bench --threads` 1, 2, 4, dazu B7 | Wave 0/1, vor dem Rechenblatt |
| `92d-wechsel.sh` | neues Laufverzeichnis `docs/measurements/<datum>-v13-messung/skripte/` | Nachfolgefassung von 92c mit genau zwei Änderungen: **kein `--rm-data`**, und Schritt 1b `occ upgrade` mit gelesenem Rückgabewert | Wave 0 |
| Einzelliste | ebenda, z. B. `90e-einzelliste.py` | `select file_id, path, state, reason from files where state in ('skipped','failed') and deleted_at is null`, read-only (`mode=ro`), gibt Kennung, Endung, Größe, Grund aus | Wave 0 |
| `94c-bodensatz-zyklen.sh` | ebenda | Marke A nach Neustart, dann Zyklus 1 und 2 (je 12 Textdateien WebDAV + `files:scan`, Entladung bei TTL 120 s), Marken C1, C2 **ohne Containerneubau dazwischen** | Wave 0 |
| `95c-kaltstart.sh` | ebenda | Neustart, `drop_caches` auf dem Wirt, erste Suche der Nutzerroute mit einem Begriff, dessen Bestand > 0 vorab aus v1.2-Rohdaten belegt ist; Treffer > 0 ist Pflicht, sonst Wiederholung des ganzen Kaltzyklus (höchstens 3) | Wave 0 |
| M-01-Leser | ebenda, z. B. `91m-langsame-aufrufe.py` | liest `nextcloud.log` (JSON-Zeilen) im Zeitfenster der Stufen, Meldung `Findling: slow backend call`, Felder `path`, `innerMs`, `ceilingMs` | Wave 0 |
| disjunction_max-Probe | ebenda, z. B. `98d-dismax-probe.py` | läuft per `docker cp` + `docker exec` im Produktcontainer (Muster `73-bestand-sonde.py`), vergleicht Summe gegen per-Wort-dismax | Wave 0 |
| Containerneubau mit Umgebung | ebenda, z. B. `92e-umgebung.sh` | `docker inspect` -> Env ersetzen -> `docker create` mit Mounts/Labels/Netz -> `docker start` -> `docker update --memory=2g --memory-swap=2g` -> cgroup zurücklesen | Wave 0, Muster `deploy-harp.yml:4480-4611` |
| Ablaufskript + Deckel-Timer | ebenda, z. B. `00-lauf.sh` | detached, nummerierte Blöcke mit UTC-Stempel beim Betreten und Verlassen, Abbruchwerte unterhalb der `tee`-Pipeline, `sudo shutdown -h +<min>` beim Start | Wave 0 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| 92d (Volume behalten) als erster Wechsel | 92c als erster Wechsel (wie v1.2) | 92c leert das Volume; MESS-08 bräuchte dann einen Vollreindex von rund 19 h 20 min: Deckel gerissen. Nur sinnvoll, wenn der Owner den 44/6-Weg "Vollreindex" wählt (Open Question 1) |
| Umgebungswechsel per Containerneubau aus `docker inspect` | Neuregistrierung mit geänderter `<default>` in der info.xml-Kopie | die Neuregistrierung ist der Weg, den 92c schon geht (Kopie außerhalb des Baums); der Neubau ist in CI "Store upgrade 6" belegt und kommt ohne zweite Registrierung aus. Beide gehen; einer wird gewählt und vorab gegen die lokale Test-Nextcloud geprobt |
| Whole-query dismax (je Feld die ganze Zeile parsen, dann dismax) | per-Wort-dismax | **gemessen in dieser Sitzung:** whole-query verliert Treffer (Dokument mit Wort A in Feld 1 und Wort B in Feld 2 fällt heraus); per-Wort erhält die Treffermenge exakt. Nur per-Wort ist ein reiner Rangvergleich |
| CPU-Zeit per `getrusage(RUSAGE_CHILDREN)` in W3 | `cpu.stat` der eigenen cgroup | RUSAGE_CHILDREN zählt nur beendete und abgewartete Kinder; die `ExtractionWorker`-Kinder leben lang, ihre tesseract-Enkel wartet das Kind ab, nicht die Probe [ASSUMED: POSIX-Semantik]. cgroup `cpu.stat` zählt alles |

**Installation:** keine. W1/W2 sind POSIX-sh, W3 und die Box-Python-Werkzeuge laufen im Abbild (`/app/.venv/bin/python`, Präzedenz `70-ocr.sh:27`) oder mit Standardbibliothek auf dem Wirt (`python3`, Präzedenz `68-bestand-endungen.py`).

## Package Legitimacy Audit

Keine externe Paketinstallation in dieser Phase. slopcheck nicht nötig, kein Eintrag.

## Wo jede Zahl entsteht (Kern dieser Research)

| Zahl | Anforderung | Werkzeug | Existiert? | Wann in der Anfahrt | Anmerkung |
|---|---|---|---|---|---|
| M-01: Dauer des inneren Aufrufs auf Zielhardware | MESS-07 | Laststufen über `search_load.py` + M-01-Leser über `nextcloud.log` | Stufen ja, Leser NEIN | Phase I, de,en | Die Zeile wird nur ab `innerMs >= 1000` geschrieben (`ExAppService.php:165,763`) und nur auf Level info. Die Zahl ist also: Anzahl und Werte der inneren Aufrufe über 1 s je Stufe, Maximum gegen `ceilingMs` 1.500, plus der Kaltstartaufruf. Darunter liegende Aufrufe schreibt das Produkt nicht, und das Produkt wird nicht geändert |
| Wirkungsnachmessung 92c | MESS-07 | `92c-wechsel.sh` unverändert | ja, ungefahren | **zuletzt** vor B4 | Zwei Läufe: provozierter Fehlschlag (z. B. `DAEMON=<nicht-vorhanden>`, Erwartung Rückgabewert 36, `registrierung-gelungen nein`), dann regulär (Erwartung 0, `registrierung-rueckgabewert 0`). Beide leeren das Volume |
| Wirkungsnachmessung 99d | MESS-07 | `99d-filter-sortierung.sh` unverändert | ja, ungefahren | Phase I, stabiler Bestand | liest das Passwort aus `PWFILE` (Vorgabe `$HOME/work/.pw/lasttest`, Zeile 219); Beleg: Lauf ohne `FINDLING_LOAD_PASSWORD` in der Umgebung grün |
| Bodensatz-Zyklus 2 | MESS-07 | `94c-bodensatz-zyklen.sh` | NEIN (94b ist gefahren und prüfsummengeschützt) | Phase I | Messgröße: C2 minus A und C2 minus C1 (Zuwachs je Zyklus); Bezug v1.2: A 103,9, C 731,9, Bodensatz 628,0 MB. Schalter 120 s braucht einen Containerneubau, danach zurück auf 0 |
| 6 Fehlschläge / 44 Übersprungene einzeln | MESS-07 | Einzelliste über `state.db` | NEIN | Phase 0, vor jedem Wechsel | **Nur die 37 Übersprungenen des Snapshot-Stands sind lesbar.** Die 44 / 6 der v1.2-Box sind zerstört. Siehe Open Question 1 |
| Kaltstartlatenz ohne Leerbegriff | MESS-07 | `95c-kaltstart.sh` | NEIN | Phase I, nach Laststufen (Kalt wird hergestellt, Runbook 7.2) | v1.2: 95-spitze traf `EmptyResultGroup`, 95b Ausprägung 3 lieferte "transient 0" Treffer. Trefferpflicht > 0 in der ersten Suche, sonst ganzer Kaltzyklus neu |
| Indexgröße bei sechs Sprachfeldern | MESS-08 | `du -sb` des Indexverzeichnisses im Volume, vorher und nachher, plus Spitze während des Umbaus (`index` + `index.rebuild`) | Befehl ja, Block NEIN | Phase II | Erwartung vorher aufschreiben: Faktor rund 2,5 (je Kette 0,372 des Verzeichnisses, gemessen 24.09. über 2.000 Dokumente, `rebuild.py:292-296`) |
| Wandzeit des Umbaus | MESS-08 | Containerstart-Stempel bis Logzeile "the rebuilt index directory is in place" (`rebuild.py:950`), Statusroute `backend.rebuildRunning/rebuildDone/rebuildTotal` | Lesepunkte ja, Block NEIN | Phase II | gegen 19 h 20 min stellen; Planwert 3 h (obere Schätzung, keine Verbesserung vorwegnehmen, Runbook 2.1) |
| disjunction_max-Entscheid | MESS-09 | `98d-dismax-probe.py` | NEIN | Phase II, nach dem Umbau | braucht sechs befüllte Felder |
| B1 Kernbelegung r je Phase | Kriterium 6 | W1 neben `rss_sampler.sh` ab dem ersten Container | NEIN | durchgehend | r = Box-Belegung aus `/proc/stat` minus Findling-Container aus `cpu.stat`; nach **jedem** Containerneubau neu starten (Pitfall 4) |
| B2 OCR-Charge im Produkt | Kriterium 6 | Muster `71-ocrphase.sh` + W1 + W2 (1 s) | Muster ja | Phase I, vor dem Umbau | 120 einseitige + 20 achtseitige Scans, danach Ordner löschen und Rückgang des Bestands abwarten |
| B3 RAM je OCR-Slot, Faktor 2 Slots | Kriterium 6 | W3 im Wegwerf-Container `--network none --cpuset-cpus 0,1 --memory 2g` | NEIN | Phase III, Produkt im Leerlauf | Faktor unter 1,05 ist Rauschen (A/B 802 gegen 799 s) |
| B4 Kurve 1 bis 16 Kerne | Kriterium 6 | W3 + `embed.bench` auf m7g.4xlarge | Werkzeug NEIN, Typwechsel nur als Research-Rezept | Phase IV, ganz zuletzt | nur bei W4-Faktor >= 1,5 (D-03) |
| B5 onnx Threads/Batch | Kriterium 6 | `embed.bench` 4 Kombinationen, `rss_sampler.sh` gegen den Bench-Container (`--name`) | ja | Phase III | |
| B6 Umbau einkernig? | Kriterium 6 | fällt aus B1 während Phase II ab | über W1 | Phase II | Befund nur benennen; Hebel ist deferred |
| B7 NL-Automat nativ arm64 | Kriterium 6 | Sonde der Komposita-Messung im CI-arm64-Lauf | Sonde ja (`docs/measurements/2026-09-komposita-nl/`) | W4, nicht auf der Box | Bezug: produktnah 24,2 bis 25,3 MB auf amd64 |

## Architecture Patterns

### System Architecture Diagram

```
 Entwicklungsmaschine                         Box m7g.large (Snapshot-Volume)                         GitHub CI arm64
 --------------------                         -------------------------------                         ---------------
 Wave 0: Werkzeuge + Tests  ----------------------------------------------------------------------->  W4: W3 N=1,2,4
         Generalprobe lokal (Test-Nextcloud)                                                           embed.bench T=1,2,4
                                                                                                       B7 NL-Automat
                                          <------------ Artefakt: Slot-Faktor F4 -------------------
 Rechenblatt (D-03 angewandt) --> OWNER-CHECKPOINT (Deckel, 44/6-Weg, dismax-Regel)
        |
        v
 Runbook Bloecke 1-13 (aws_box.sh) ---->  [0] Deckel-Timer (shutdown -h), Samplers W1+rss starten
                                          [0] Markenlesung + Einzelliste (state.db read-only)
                                                 |  Tor: Marken ausser schema/languages/nl gleich? nein -> STOPP+ntfy
                                          [I]  92d: PHP-Haelfte, occ upgrade, register OHNE --rm-data, Grenze, Baumhash
                                                 |  Tor: 52.111/37/0, "nothing to rebuild", kein Vektor-Drift
                                               cron vorher -> Indexgroesse de,en -> M-01 (loglevel info, Stufen 1..16)
                                               -> Kaltstart (Trefferpflicht) -> Bodensatz Zyklen 1+2 (TTL 120, dann 0)
                                               -> 99d -> B2 (140 Scans, W2, cron waehrend) -> B2-Ordner loeschen
                                          [II] Neubau FINDLING_LANGUAGES=de,en,es,it,nl,pt -> Umbau (W1 = B6)
                                               -> Indexgroesse sechs Felder -> dismax-Probe (MESS-09)
                                          [III] Wegwerf-Container: B3 (W3), B5 (bench) ; Endmessungen 90-bestand
                                               -> 92c Fehlschlag-Lauf (36) -> 92c regulaer (0)  [Volume geleert]
 aws stop / modify-instance-attribute     [IV] m7g.4xlarge: AIO stoppen, W3 N=1..16, bench T=1..8
   m7g.4xlarge / start  --------------->       (mem=4G-Drop-in vorher entfernt)
 aws_box.sh stop, Kosten committen,
 destroy (Runbook 8), kein Ende-Snapshot
        |
        v
 Wave 3: performance.md, Laufbericht, language-analyzers.md, Runbook-Nachtraege, Pruefsummen-Waechter
         dismax: umgesetzt (rewrite.py + Ratsche + CI) ODER dokumentiert verworfen --> Owner-Abnahme
```

### Recommended Project Structure
```
docs/measurements/<JJJJ-MM>-v13-messung/     # neues Laufverzeichnis, Name nach Monat der Anfahrt
├── README.md                                # Bericht, Freigabezeile "Anfahrt freigegeben: <Datum>, Deckel ..."
├── skripte/
│   ├── 00-ablauf.md                         # Erwartungen E1..En VOR der Box committet (Zeitstempel = Commit)
│   ├── 00-lauf.sh                           # Ablaufskript, detached, Timer, Bloecke mit UTC-Stempeln
│   ├── 90e-einzelliste.py, 91m-langsame-aufrufe.py
│   ├── 92d-wechsel.sh, 92e-umgebung.sh
│   ├── 94c-bodensatz-zyklen.sh, 95c-kaltstart.sh
│   └── 98d-dismax-probe.py
└── rohdaten/                                # alles, was auf der Box entsteht; OUT zeigt hierher
scripts/ops/cpu_sampler.sh, proc_anon_sampler.sh, ocr_slot_probe.py   # W1..W3, in test_ops_scripts.py aufnehmen
.github/workflows/measure.yml                                         # W4 + B7
```

### Pattern 1: Nachfolgefassung statt Bearbeitung
**What:** Eine gefahrene Messfassung wird nie editiert; eine Änderung ist eine neue Datei mit neuer Nummer, Kopf mit "die eine Änderung gegen X" und Wächter in `backend/tests/test_measurement_scripts.py` (`DRIVEN_V12_FASSUNGEN`, Zeile 343).
**When to use:** 92d (aus 92c), 94c (aus 94b), 95c (aus 95-spitze/95b).
**Konsequenz nach der Anfahrt:** 92c und 99d sind dann gefahren. Ihr Kopfsatz "DIESE FASSUNG IST NICHT GEFAHREN" bleibt byteweise stehen; der Wächter `NOT_DRIVEN` wird im Test durch einen Prüfsummen-Wächter ersetzt, der Bericht nennt das Fahrdatum. Jede neu gefahrene Fassung bekommt ihre Prüfsumme (Regel `00-ablauf.md` Abschnitt 5).

### Pattern 2: OUT immer auf das neue Laufverzeichnis
**What:** Alle gefahrenen v1.2-Werkzeuge schreiben per Vorgabe nach `$SKRIPTE/../rohdaten`, also in das v1.2-Verzeichnis (`40b-baumhash.sh:27`, `90-bestand.sh:34`, `93-nullstand.sh:42`, `94b:157`, `95-spitze.sh:64`, `92c:235`, `99d:201`). Das Ablaufskript setzt `OUT=<neu>/rohdaten` für jeden Aufruf und prüft vor dem Commit `git status docs/measurements/2026-09-v12-messung docs/measurements/2026-09-nachfolgefassungen` auf leer.
**Example:**
```sh
# Muster, im Ablaufskript einmal gesetzt und je Aufruf mitgegeben
OUT="$LAUF/rohdaten"; export OUT
WERKZEUGE="$REPO/docs/measurements/2026-09-v12-messung/skripte"   # 92c-Vorgabe, Zeile 240
OUT="$OUT" "$WERKZEUGE/97-cron-vorpruefung.sh" vorher
```

### Pattern 3: Umgebungswechsel = Containerneubau, Grenze und Pflichtzeilen neu lesen
**What:** `settings()` ist je Prozess gecacht (`config.py:1240`); eine Umgebungsvariable wirkt erst nach Neubau oder Neustart des Containers. Jeder Neubau verliert `docker update --memory`. Nach jedem Neubau: `memory.max` 2147483648 und `memory.swap.max` 0 aus der cgroup lesen (Runbook Block 12, richtiggestellt), `entladeschalter-ist` lesen (Runbook 6.4), Samplers neu starten.
**Source:** `deploy-harp.yml:4488-4611` (Store upgrade 6): `docker inspect` -> `Config.Env` gefiltert -> neue Zeile -> Mounts und Labels übernehmen -> Entrypoint/Cmd gegen das Abbild prüfen -> `docker rm -f`, `docker create`, `docker start`. Die Zertifikatsübernahme `/certs/frp` braucht die Box NICHT, sie läuft ohne HaRP-Tunnel (`95-spitze-nachher.txt`: "HP_SHARED_KEY is not set, no HaRP tunnel is opened"); der Netzmodus der Box ist nicht `host` und muss übernommen statt verlangt werden [VERIFIED: Rohdatei gelesen; Netzmodus ASSUMED, auf der Box lesen].

### Pattern 4: Tor-Abbrüche unterhalb der `tee`-Pipeline, Nummern fortsetzen
**What:** Rückgabewert einer Pipeline gehört zu `tee`, `sh` kennt kein `pipefail`; Abbrüche stehen unterhalb (00-ablauf.md 4, 4.1). Der Katalog 15 bis 39 ist vergeben; neue Werte ab 40 fortsetzen, keine Zahl umhängen.

### Pattern 5: Erwartung vorher committen
**What:** `00-ablauf.md` mit E1 bis En und Zahlen VOR der ersten Boxminute committen; nach der Messung nicht umformulieren; Urteile nur `gehalten`, `verfehlt`, `nicht entschieden` (v1.2-Bericht Abschnitt 3). Für Phase 22 besonders: die Umbau-Erwartung (Planwert 3 h, Schätzung 1 bis 3 h), der Indexfaktor rund 2,5, die dismax-Entscheidungsregel (Open Question 3) und die Bodensatz-Erwartung.

### Pattern 6: Unbeaufsichtigter Lauf mit hartem Stopp auf der Box
**What:** Das Ablaufskript startet mit `nohup`/`setsid` (Präzedenz `96-volllauf.sh` "detached"), schreibt je Block Betreten/Verlassen mit UTC, meldet über `96e-ntfy-watch.sh senden`, und setzt beim Start `sudo shutdown -h +<Restminuten>`. Bei EBS-gestützten Instanzen ist das Standardverhalten eines Herunterfahrens aus dem Betriebssystem "stop" [ASSUMED: AWS-Standard `InstanceInitiatedShutdownBehavior=stop`; `run-instances` in Block 3 setzt nichts anderes; vor der Anfahrt lesend prüfen mit `describe-instance-attribute --attribute instanceInitiatedShutdownBehavior`]. Nach dem B4-Neustart ist der Timer weg und wird mit der Restzeit neu gesetzt.
**Warum:** D-02 verlangt harten Stopp; ein Operator, der Phase 23 lokal fährt, merkt eine abgelaufene Frist sonst zu spät.

### Anti-Patterns to Avoid
- **92c als ersten Wechsel fahren:** leert das Volume, MESS-08 unmöglich im Deckel.
- **Ein Messwerkzeug während der bezahlten Zeit ändern:** Runbook 7.1 verbietet es; v1.2 musste dreimal ausnehmen. Deshalb Generalprobe vorher (lokale Test-Nextcloud, `scripts/dev/compose.yaml`) und W1 bis W3 im CI-arm64.
- **Die Diagnose-Route vor einer Kaltmessung rufen:** lädt das Modell (Abbruch 30, Runbook 7.2). Die disjunction_max-Probe und die Bestandssonde laufen NACH dem Kaltstart.
- **OCR-Sprachen beim Sprachwechsel mitziehen:** `FINDLING_OCR_LANGUAGES` bleibt `deu+eng+fra`, sonst ist B2 nicht mit dem 07.09. vergleichbar; der Startwarnhinweis über nicht abgedeckte Sprachen ist erwartet (`docs/language-analyzers.md` Zeilen 77-84).
- **Den Arbeitsbaum auf der Box während der Anfahrt auf Phase-23-Commits ziehen:** der Baumhash vergleicht Abbild gegen Arbeitsbaum (Abbruch 36/38).

## Der Umbau auf dem Snapshot-Volume (MESS-08, Detail)

**Auslöser.** Der Umbau beantwortet genau drei Marken: `schema_version`, `languages`, `wordlist_hash_nl` (`MARKS_A_REBUILD_ANSWERS`, `rebuild.py:243`). Jede andere Drift (`wordlist_hash`, `analyzer_version`, `index_version`, Indexformat) führt zum Vollreindex über die Generation [VERIFIED: `store/repo.py:717-788`, `index/open.py:217-257`].

**Markenstand, soweit belegt.** Die v1.1-Box (09.09.) und die v1.2-Box (21.09.) trugen beide `analyzer_version = 1`, `index_version = 1`, `schema_version = 1`, `store_schema_version = 2`, `tantivy_version = tantivy v0.26.0, index_format v7`, `wordlist_hash = b1f64012...dde0` (`2026-09-vergleichsmessung-m7g/rohdaten/90-bestand.txt:115-121`, `2026-09-v12-messung/rohdaten/90-bestand.txt:120-128`). Der heutige Code erwartet `ANALYZER_VERSION = 1` (`analyzer.py:138`), `INDEX_VERSION = 1` (`config.py:54`), Store-Schema "2" (`repo.py:63`), denselben deutschen Digest (seit Phase 2 unverändert, `08-01-SUMMARY.md:73`) und Format v7 (0.26.2, in dieser Sitzung gelesen). `schema_version` 1 gegen 2 ist über `LEGACY_SCHEMA_STEPS = {("1","2")}` entschuldigt, fehlende `languages`- und nl-Marken ebenfalls (`repo.py:1448-1526`). **Folge:** unter `de,en` startet nichts, unter sechs Sprachen startet der Umbau und kein Vollreindex. [VERIFIED für die beiden Bezugsboxen; der Stand des Snapshot-Volumes selbst ist LOW, weil der Snapshot vom 11.09. stammt und nach dem 10.09.-Lauf geschrieben wurde; seine `embedding_version` ist in keiner Rohdatei belegt.]

**Konsequenz für den Plan.** Block "Markenlesung" in Phase 0 liest `state.db` read-only vom Wirt (`/mnt/findling/docker/volumes/nc_app_findling_backend_data/_data/state.db`, Pfad aus `71-ocrphase.sh:86`) und hält jede Marke gegen die Erwartung. Weicht eine Nicht-Umbau-Marke ab: harter Tor-Abbruch mit ntfy, kein Wechsel. Weicht nur `embedding_version` ab, läuft nach dem Start eine Vektor-Neueinbettung (rund 5 h, `docs/embeddings.md` 8), die B1, M-01 und den Umbau verfälscht: ebenfalls Tor, Owner entscheidet.

**Ablesung.** Wandzeit = Containerstart (`docker inspect .State.StartedAt`) bis Logzeile "the rebuilt index directory is in place; the schema, language and Dutch marks are current again" (`rebuild.py:950`); daneben die Statusreihe `rebuildRunning`, `rebuildDone`, `rebuildTotal`, `languagesActive` im Muster von `deploy-harp.yml:4629-4680`. Platzprüfung: `may_rebuild` verlangt `aktuell x (1 + 0,40 x 4)` plus `MIN_FREE_BYTES` 524.288.000 frei (`rebuild.py:287-322`); das Volume hatte 22G frei (`90-bestand.txt`). Indexgröße: `du -sb` vor dem Neubau, während des Laufs (Spitze beider Verzeichnisse) und nach dem Tausch; dazu Dokumentzahl aus `occ findling:index`.

## disjunction_max: Codeort, Messung, Umsetzung (MESS-09)

**Codeort.** `backend/src/findling/query/rewrite.py:692-698`: `index.parse_query_lenient(rewritten, default_field_names=searched, field_boosts=dict(plan.boosts), conjunction_by_default=True, allow_regexes=False)`. Gewichte `BODY_BOOST` Zeile 124 (`de` 1.0, `en` 0.8, vier neue 0.6), `NAME_BOOST` 3.0, `TITLE_BOOST` 2.0. Der Plan kommt aus `findling.api.resources.field_plan_for` (Zeile 406). Aufrufer von `build_query`: `api/search.py:248`, `api/snippets.py:187`, `api/diagnose.py:198`. Snippets: `index/search.py:875` (`SnippetGenerator.create(..., FIELD_BODY_DE)`). Rangprobe mit Kipppunkt 0,81: `backend/tests/test_field_plan_ranking.py`.

**In dieser Sitzung gemessen (tantivy 0.26.2, index_format v7, lokales venv):**

```
Parser (heute):  Must[ Should(a:haus, b:haus^0.6) ], Must[ Should(a:garten, b:garten^0.6) ]   -> Summe je Wort
sum                     [(1.1464, 0), (0.7482, 1), (0.5579, 2)]
dismax ganze Zeile      [(0.5579, 0), (0.5579, 2)]          <- Dokument 1 verloren: Treffermenge aendert sich
dismax je Wort, Parse   [(1.023, 0), (0.7482, 1), (0.5579, 2)]   <- gleiche Treffermenge, nur Raenge
dismax je Wort, tie 0.3 [(1.06, 0), (0.7482, 1), (0.5579, 2)]
SnippetGenerator mit dismax-Anfrage: "<b>haus</b> <b>garten</b>"   <- Snippets funktionieren
```
[VERIFIED: Probe im Scratchpad gefahren]. `Query.disjunction_max_query(subqueries, tie_breaker=None)`, `Query.boost_query`, `Query.boolean_query`, `TextAnalyzer.analyze` stehen im Stub (`tantivy.pyi:311-317, 670-672`).

**Bauform, die gemessen und notfalls ausgeliefert wird:** je Wort der bereinigten Zeile und je Feld des Plans `parse_query_lenient(wort, default_field_names=[feld], field_boosts={feld: boost}, conjunction_by_default=True)`, darüber `disjunction_max_query`, über die Wörter `Occur.Must`, danach der Filter wie heute (`_filter_clause`). Der Parser übernimmt die Kettenanalyse je Feld, also auch Komposita und Faltung.

**Grenze der Bauform:** Zeilen mit Operatoren, Phrasen, Klammern oder den Umlautvarianten-Gruppen aus `add_umlaut_variants` ("(a OR b)") zerfallen nicht in Wörter. Die Probe misst deshalb getrennt: (1) Einwortzeilen (der häufigste Fall, und dort ist per-Wort gleich ganze Zeile, also exakt), (2) Mehrwortzeilen ohne Operatoren. Die Produktumsetzung fällt bei Operatoren auf den heutigen Parserweg zurück (`carried_operators`, `carries_one_term` existieren, Zeilen 286, 383).

**Messung auf echten Daten (Vorschlag, VOR der Box in 00-ablauf.md festschreiben):** im Produktcontainer nach dem Umbau, per `docker cp` + `docker exec /app/.venv/bin/python` (Muster `73-bestand-sonde.py`), Index über `open_index` (registriert die Ketten; `Index(...)` direkt wirft "Error getting tokenizer", `rebuild.py`-Kopf), Plan über `field_plan_for`. Anfragemenge: die zehn `TERMS` aus `search_load.py:156`, die Sprachfall-Begriffe aus `98c-sprachfaelle.sh`, und eine feste Stichprobe häufiger Wörter aus der Wortliste von `build_load_corpus.py`. Je Anfrage drei Ranglisten der lexikalischen Hälfte bis Tiefe 100 (`SEARCH_RRF_WINDOW`): Summe mit ausgelieferten Gewichten, dismax tie 0.0, dismax tie 0.1, dazu die **Altplan-Rangliste** (`body_de`, `body_en`, Name, Titel mit denselben Gewichten = das Verhalten bis 1.2.0). Kennzahlen: Überlappung@10, RBO@10 (p 0,9) jeder Form gegen den Altplan, mittlere Rangverschiebung, Treffermengengleichheit (muss bei per-Wort exakt gelten, sonst ist die Probe falsch), Laufzeit je Form (Median über Wiederholungen). Ausgabe nur Zahlen und `file_id`s (T-02-14).

**Warum der Altplan die Messlatte ist:** Erfolgskriterium 3 der v1.3-Roadmap verspricht, dass ein Treffer in mehreren Sprachfeldern sich nicht vor einen besseren Treffer schiebt. Auf dem Lastkorpus stehen alle sechs Felder aus demselben deutschen Text; jede Abweichung der Summenrangliste vom Altplan entsteht durch Ketten, die ein Wort unterschiedlich behandeln, also genau die Verzerrung, die dismax beseitigen soll. Ein Korpus mit Relevanzurteilen gibt es auf der Box nicht [ASSUMED: Vorschlag, Owner/Planer legen die Regel fest].

**Umsetzung, falls positiv (D-04):** eine Funktion neben `build_query` (oder ein Zweig darin) plus Tests: `test_query_rewrite.py` (Anfrageform), `test_field_plan_ranking.py` (die Aussagen 3 und 4 und der Kipppunkt ändern ihre Bedeutung unter dismax und müssen neu vermessen werden, der Modulkopf sagt ausdrücklich "that decision belongs to phase 22"), `test_search_endpoint.py`, Snippet-Test, `docs/language-analyzers.md` Abschnitt "What a question searches" und "Measured numbers". **Ratsche:** `PACKAGE_TREE_HASH_TODAY` (`test_measurement_scripts.py:1097`) im selben Commit. CI-Beweis: `search-parity`- und `deploy-harp`-Sprachfälle (Einwort-`alemanes`-Beweis bleibt Einwort, `docs/language-analyzers.md` 158-170). Das gemessene Abbild ist dann nicht das ausgelieferte 1.3.0; der Bericht nennt das.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Baumhash-Beweis | eigene Hashrechnung im Wechselskript | `40b-baumhash.sh` als Skript rufen | "ein Beweis, der seine eigene Rechnung mitbringt, beweist nur sich selbst" (92c-Kopf, Unterschied 2) |
| Cron-Intervall-Gate | eigene Cronleser | `97-cron-vorpruefung.sh vorher/waehrend` | Lesefehler 5 s statt 300 s war der v1.2-Fix |
| Laststufen | eigenes Lastwerkzeug | `search_load.py` unverändert | Vergleichbarkeit gegen v1.0/v1.1/v1.2 |
| Speicher-Abtastung | `docker stats` | `rss_sampler.sh` (cgroup `memory.stat`) | `docker stats` zählt Seitencache mit (`test_ops_scripts.py` verbietet es) |
| Container mit geänderter Umgebung | freihändiges `docker run` | Rekonstruktion aus `docker inspect` nach `deploy-harp.yml:4488-4611` | Entrypoint/Cmd-, Mount- und Label-Prüfung sind dort ausgefeilt |
| Anfrageanalyse je Kette | eigene Tokenisierung | `parse_query_lenient` je Feld oder `TextAnalyzer.analyze` | Komposita, Faltung, Stoppwörter stecken in den registrierten Ketten |
| Meldekette | eigenes `curl` an ntfy | `96e-ntfy-watch.sh` | loggt jeden HTTP-Code, Mail-Rückfall |
| Kosten und Preise | eigene Preisliste | `aws_box.sh prices` am Anfahrtstag; für m7g.4xlarge ein gezielter `aws pricing get-products`-Filter (kein Gigabyte-Download, Runbook 2.3) | |
| Scan-Material | echte Dokumente | `build_load_corpus.py` (`build_scan_single`, `_scan_pdf(rng, 8)`, Zeilen 1031-1069) im Abbild | D-02 / T-05-18: eine gemietete Maschine sieht nie ein echtes Dokument |

**Key insight:** Jedes Werkzeug, das auf der Box zum ersten Mal läuft, hat in v1.2 bezahlte Zeit gekostet (drei Wechselläufe, Rechtebit 126, Swap-Erwartung, Cron-Leser). Neubau heißt hier nicht nur Code, sondern Generalprobe.

## Common Pitfalls

### Pitfall 1: `--rm-data` zerstört den Messgegenstand
**What goes wrong:** 92c (und 92b) leeren in Phase B das Backend-Volume.
**Why it happens:** v1.2 wollte einen Volllauf von leer; der Schalter ist dort Absicht.
**How to avoid:** Erster Wechsel mit 92d ohne Schalter; 92c nur zuletzt; Zählung der Nextcloud-Instanzen bleibt trotzdem Pflicht.
**Warning signs:** `92c-wechsel.txt` enthält "=== 8. unregister MIT --rm-data"; `occ findling:index` zeigt danach 0 indexiert.

### Pitfall 2: Die 44 / 6 gibt es nicht mehr
**What goes wrong:** Der Plan verspricht "einzeln benannt", der Datenbestand dafür ist zerstört.
**How to avoid:** Owner-Entscheid vor dem Rechenblatt (Open Question 1); Einzelliste der 37 aus dem Snapshot in jedem Fall fahren (Sekunden), als Phase-0-Block vor jedem Wechsel.

### Pitfall 3: USD-Deckel und Stundendeckel widersprechen sich mit B4
**What goes wrong:** 24 h x 0,115841 = 2,78 USD; mit B4 (1,25 h x rund 0,80 USD) kommen 24 h auf rund 3,64 USD. Der 3,00-USD-Deckel greift dann schon nach rund 17,4 h Gesamtzeit (1,44 h B4 mit 15 Prozent Zuschlag, Rest 1,85 USD / 0,115841).
**How to avoid:** Das Rechenblatt nennt beide Grenzen und fragt den Owner, welche gilt (Open Question 2); der Timer auf der Box rechnet mit der früheren.

### Pitfall 4: Samplers sterben beim Containerneubau
**What goes wrong:** `rss_sampler.sh` löst die Container-ID einmal auf; nach Neubau fehlt `memory.stat`, `set -eu` beendet das Skript, B1 hat Lücken.
**How to avoid:** Ablaufskript startet W1 und `rss_sampler.sh` nach jedem Neubau neu (Rohdatei je Containerleben); W1 schreibt beim Wegfall der cgroup eine klare Schlusszeile.

### Pitfall 5: M-01-Zeilen erscheinen nicht
**What goes wrong:** Die Zeile ist `info`; die Nextcloud-Vorgabe `loglevel` ist 2 (warning) [ASSUMED: Nextcloud-Standard; AIO-Stand auf der Box mit `occ config:system:get loglevel` lesen]. Ohne Umstellung zählt der Leser null Zeilen und meldet fälschlich "kein Aufruf über 1 s".
**How to avoid:** Vorher Wert lesen und protokollieren, auf 1 setzen, nach dem Block zurücksetzen; Gegenprobe: eine Kaltstartsuche (rund 2 s außen) muss eine Zeile erzeugen, sonst ist der Leser oder das Level falsch.

### Pitfall 6: Kaltstart mit null Treffern
**What goes wrong:** v1.2 hatte `EmptyResultGroup` (95-spitze) und "transient 0" (95b Ausprägung 3).
**How to avoid:** Begriff mit belegtem Bestand ("Bescheid Antrag" lieferte in 95b 26 Treffer); keine Vorprobe über die Diagnose-Route; Treffer > 0 ist Pflichtbedingung, sonst ganzer Kaltzyklus erneut (Abbruchwert neu, ab 40).

### Pitfall 7: Der Umbau und die Vektorspur laufen gleichzeitig
**What goes wrong:** Weicht `embedding_version` ab, startet eine Neueinbettung in Bändern zu 500 (`poller.py:158`), und die Umbauzeit ist keine reine Umbauzeit.
**How to avoid:** Markenlesung vor dem Wechsel (Tor); im Umbaublock Statusreihe mitschreiben (`embedded` muss konstant bleiben).

### Pitfall 8: B4 unter `mem=4G`
**What goes wrong:** Die Vorarbeit nennt für 16 Slots einmal "1,8 bis 3,2 GB" (1.2) und einmal "3,0 bis 10,2 GB" für 15 Slots (2.4). Unter `mem=4G` und laufendem AIO reißen N = 12 und 16 beim oberen Band.
**How to avoid:** Vor dem Stop den Grub-Drop-in `/etc/default/grub.d/99-mem4g.cfg` entfernen und `update-grub` fahren (der Neustart des Typwechsels ist ohnehin da, also rund 1 min Zusatz); nach dem Start AIO-Container stoppen (Restart-Policy startet sie sonst, Runbook Block 8: "alle Container der Messbox starteten von selbst"); Wegwerf-Container ohne `--memory 2g` oder mit protokollierter Grenze. Nach B4 ist die Box keine Referenzbox mehr, deshalb B4 zuletzt.

### Pitfall 9: aws_box.sh rechnet B4 mit dem falschen Satz
**What goes wrong:** `cmd_stop` schreibt `BOX_LAST_UPTIME_COST_USD` mit dem gepinnten m7g.large-Satz.
**How to avoid:** B4-Kosten in der Kostenrohdatei von Hand aus Start/Stop-Stempeln und dem am Anfahrtstag gelesenen m7g.4xlarge-Satz rechnen; Typwechsel und Rücklesen `describe-instances --query InstanceType` protokollieren. Kapazität m7g.4xlarge in eu-central-1c ist [ASSUMED]; Rückfall m7g.2xlarge, dann fehlen 12 und 16; bei weiterem Fehlschlag zurück auf m7g.large für den Abbau.

### Pitfall 10: Rohdaten verletzen die Geheimnisregel
**What goes wrong:** `backend/tests/test_public_artifacts.py` prüft jede Datei unter `docs/` (IP-Adressen, Kennungen, Schlüsselpräfixe, gesperrtes Vokabular). Container-Logs tragen Brückenadressen und `0.0.0.0`.
**How to avoid:** Gate lokal vor dem Commit der Rohdaten; begründete Ausnahmen nur mit eigenem Satz (Präzedenz D-10 in `03-aufbau.txt`).

### Pitfall 11: Die Box misst ein anderes Abbild als gedacht
**What goes wrong:** `:dev` wandert mit jedem Push auf `backend/**`; Phase 23 pusht parallel.
**How to avoid:** Digest per `docker buildx imagetools inspect` aus dem Lauf der Abbildstrecke des Box-Commits ablesen (Präzedenz `03-aufbau.txt`: "lauf 35471225102 ... merge-job"), Box-Klon auf genau diesen Commit, `git config core.fileMode false`, `chmod +x` im neuen Laufverzeichnis und im v1.2-Werkzeugverzeichnis.

### Pitfall 12: W3-Messung vermischt Probe und Poller
**What goes wrong:** B3/B5 im Wegwerf-Container, während der Produktcontainer arbeitet, misst die Poller-Last mit.
**How to avoid:** Arbeitsvorrat null und `runState idle` vorher ablesen (Vorarbeit 1.5 Punkt 4); `--cpuset-cpus` explizit; 3 Runden, Median, Rauschschwelle 1,05.

## Code Examples

### Wechsel ohne Volumenverlust (Kern von 92d, Skizze)
```sh
# Source: 92c-wechsel.sh:474-534, geaendert: kein --rm-data, Schritt 1b occ upgrade mit Rueckgabewert
occ upgrade >"$WORK/upgrade.log" 2>&1 || upgrade_status=$?
printf 'occ-upgrade-rueckgabewert %s\n' "${upgrade_status:-0}"
occ app_api:app:unregister "$APP_ID" >"$WORK/unregister.log" 2>&1 || unregister_status=$?
occ app_api:app:register "$APP_ID" "$DAEMON" \
    --info-xml /tmp/92d-info-box.xml --wait-finish >"$registerlog" 2>&1 || register_status=$?
sudo docker update --memory=2g --memory-swap=2g "$CONTAINER" >/dev/null
# danach: memory.max / memory.swap.max aus der cgroup, 40b-baumhash, Baumhash im laufenden Container
```

### Einzelliste, read-only
```python
# Source: Muster 68-bestand-endungen.py (mode=ro, Schema-Gegenprobe)
connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
columns = [row[1] for row in connection.execute("pragma table_info(files)")]
rows = connection.execute(
    "select file_id, path, state, reason from files"
    " where state in ('skipped', 'failed') and deleted_at is null order by state, file_id"
)
# Ausgabe: file_id, Endung, Grund; Pfad nur als Basisname des synthetischen Generators
```
Hinweis: die Spalte `file_id` ist im Vorbild nicht gelesen; die Schema-Gegenprobe muss sie verlangen [ASSUMED: Spaltenname, in Wave 0 gegen `store/repo.py` prüfen].

### Per-Wort-dismax (gemessen)
```python
# Source: Probe dieser Sitzung, tantivy 0.26.2
def word_dismax(index, word, plan, tie=None):
    subs = [
        index.parse_query_lenient(word, default_field_names=[field],
                                  field_boosts={field: plan.boosts[field]},
                                  conjunction_by_default=True, allow_regexes=False)[0]
        for field in plan.fields
    ]
    return Query.disjunction_max_query(subs, tie)

query = Query.boolean_query([(Occur.Must, word_dismax(index, w, plan)) for w in words])
```

### W1-Abtastung (Skizze nach rss_sampler.sh)
```sh
# Source: scripts/ops/rss_sampler.sh (Pfadbildung, Verweigerung statt Nullen)
usage=$(awk '$1 == "usage_usec" { print $2 }' "$CGROUP/cpu.stat")
box=$(awk '$1 == "cpu" { print $2+$3+$4+$5+$6+$7+$8+$9, $5 }' /proc/stat)   # gesamt, idle
printf '%s,%s,%s\n' "$(date +%s)" "$usage" "$box"
```

## Rechenblatt-Entwurf (Claude's Discretion, Planwerte aus v1.2-Ist, Rechenweg Runbook 2.5)

| Posten | Planwert | Herleitung |
|---|---:|---|
| Handaufbau und Wiederaufbau (Blöcke 1 bis 13) | 1 h 30 min | Ist v1.2 rund 0 h 40 min, als Untergrenze; Aufschlag für neue Fallen |
| Markenlesung + Einzelliste (Phase 0) | 0 h 10 min | read-only, Sekunden |
| Wechsel 92d mit `occ upgrade` | 0 h 45 min | Ist 0 h 32 min in drei Läufen |
| Zustandsprüfung, Cron vorher, Indexgröße de,en | 0 h 15 min | |
| M-01-Block (Level, fünf Stufen, Leser) | 0 h 30 min | Ist Stufen 0 h 06 min |
| Kaltstart mit Trefferpflicht (bis 3 Zyklen) | 0 h 20 min | Ist 95b 0 h 07 min für vier Ausprägungen |
| Bodensatz Zyklen 1 und 2, zwei Neubauten | 0 h 30 min | Ist 94b 0 h 03 min je Zyklus bei 120 s |
| 99d | 0 h 10 min | Ist 99c 11 s |
| B2 samt Löschen | 0 h 45 min | Vorarbeit 40 min |
| Umbau MESS-08 samt Indexgröße | 3 h 00 min | obere Schätzung, keine Verbesserung vorweggenommen |
| disjunction_max-Probe | 0 h 20 min | |
| B3 + B5 | 0 h 27 min | Vorarbeit 15 + 12 min |
| Endmessungen, Kostenrohdatei | 0 h 15 min | |
| 92c zwei Läufe | 0 h 30 min | |
| Abbau bis Stop | 0 h 10 min | Ist 0 h 05 min |
| Warte- und Sitzungszeit (Tore, Operator-Handgriffe) | 3 h 00 min | v1.2: 25,75 h Box gegen rund 21 h gestempelt |
| **Summe m7g.large** | **12 h 37 min** | x 1,15 = **14,5 h**, x 0,115841 = **1,68 USD** |
| B4 m7g.4xlarge | 1 h 15 min | x 1,15 = 1,44 h, x rund 0,80 = **1,15 USD** |
| **Rechenwert gesamt** | | **rund 16 h / rund 2,83 USD** (im Owner-Rahmen 11 bis 17 h) |
| Deckel D-01 | | 24 h, rund 3,00 USD: siehe Pitfall 3 |

Der m7g.4xlarge-Satz ist gerechnet (8 x 0,0978 = 0,7824 USD/h plus Speicher und IPv4 rund 0,018); Linearität gestützt durch us-east-1 m7g.4xlarge ab 0,6528 USD/h (= 8 x 0,0816) [MEDIUM: cloudprice.net, economize.cloud; nicht die AWS-Preisliste] und die Vorarbeit (m7g.xlarge 0,1955 in eu-central-1, doit.com). Am Anfahrtstag gegenlesen.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 92b schluckt occ-Fehler | 92c prüft den Rückgabewert der Registrierung | Plan 16 (A1) | Wirkung nie gemessen: Phase 22 misst sie |
| 99c Passwort aus Umgebung | 99d aus `PWFILE` | Plan 16 (A1) | Vorbedingung 14 des Runbooks entfällt für 99d |
| Runbook-Tor 52.111/37/0 nach `--rm-data` unlesbar | Tor vor jedem Schalter ablesen; mit 92d bleibt es lesbar | v1.2-Befund L-02 | Das Tor ist in Phase 22 wieder ein echtes Tor |
| Blöcke ohne eigene Zeitmarke | jeder Block schreibt Betreten/Verlassen mit UTC | Runbook 2.1, Nachtrag 21.09. | Pflicht für das Ablaufskript |
| Behauptung "tesseract nutzt beide Kerne" (`performance.md:2886`) | ungemessen, widerspricht `OMP_THREAD_LIMIT=1` (`ocr.py:73,194`) | Vorarbeit 25.09. | B3-Einzelmodus prüft sie; Berichtigung als datierter Nachtrag, nicht als Ersetzung |

**Deprecated/outdated:**
- BACKLOG BL-F03 Punkt 4 ("Volume mounten + DB/Log lesen"): falsch, der Datenbestand existiert nicht mehr.
- Runbook Block 12 "2147483648 in beiden Feldern": richtiggestellt auf `memory.swap.max` 0.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Das Snapshot-Volume trägt dieselben Marken wie die Bezugsboxen, insbesondere eine passende `embedding_version` | Umbau | Vektor-Neueinbettung (rund 5 h) oder Vollreindex; Tor fängt es, kostet aber die Anfahrt |
| A2 | Instanz fährt beim OS-`shutdown -h` in den Zustand stopped | Pattern 6 | harter Stopp wäre ein Terminate: Volume und Korpus weg. Vorher lesend prüfen, sonst Timer über einen anderen Weg |
| A3 | Nextcloud-`loglevel` steht auf der Box auf 2 | Pitfall 5 | M-01 zählt null Zeilen; Gegenprobe fängt es |
| A4 | Netzmodus des Box-Containers ist nicht `host`; Neubau aus `docker inspect` gelingt ohne HaRP-Zertifikate | Pattern 3 | Neubau scheitert in bezahlter Zeit; Generalprobe lokal und Rückfall Neuregistrierung |
| A5 | `files` hat eine Spalte `file_id` | Code Examples | Einzelliste muss anderen Schlüssel nehmen |
| A6 | m7g.4xlarge rund 0,80 USD/h und in eu-central-1c verfügbar | Rechenblatt, Pitfall 9 | B4-Kosten, Rückfall 2xlarge |
| A7 | Altplan-Nähe (RBO) ist ein tragfähiges Vorteilskriterium für dismax | disjunction_max | falsche Entscheidung ohne Relevanzurteile; Owner legt die Regel vorher fest |
| A8 | `RUSAGE_CHILDREN` erfasst die Enkel der langlebigen Kinder nicht | Alternatives | W3-CPU-Zahl zu klein; deshalb cgroup `cpu.stat` |
| A9 | `workflow_dispatch` kann `measure.yml` gegen einen Ref mit geänderter Workflowdatei fahren, solange die Datei auf `main` existiert | W4 | sonst Push auf `main` vor W4 nötig (Owner-Freigabe Push) |

## Open Questions (RESOLVED)

1. **Wie werden die 6 Fehlschläge und 44 Übersprungenen benannt?** (MESS-07, Owner)
   - What we know: das v1.2-Volume ist ohne Ende-Snapshot zerstört; keine Rohdatei nennt Dateien; der Snapshot trägt 52.111 / 37 / 0.
   - What's unclear: ob der Owner (a) "37 des Snapshots einzeln benannt, 44/6 dokumentiert nicht reproduzierbar" akzeptiert, (b) einen v1.3-Vollreindex bezahlt (rund +20 h, dann 92c zuerst, Deckel rund 40 h / 4,70 USD neu zu rechnen), der eine NEUE Endzahl einzeln benennt, oder (c) einen Teilweg (nur die in v1.2 hinzugekommenen Dateien erneut: Sprachfall-Upload, MEM-02-Dateien).
   - Recommendation: (a) als Standard in das Rechenblatt, (b) und (c) mit Kosten daneben; Entscheid am Checkpoint.
   - RESOLVED: Owner-Entscheid am Checkpoint 22-07 (26.09.2026): Weg a, `EINZELWEG=a`; festgehalten in `docs/measurements/2026-09-v13-messung/skripte/00-ablauf.md` Abschnitt 6 und README Abschnitt 4. Kein Block teilweg.
2. **Welcher Deckel gilt, 24 h oder 3,00 USD?** Mit B4 greift 3,00 USD bei rund 17,4 h. Recommendation: Rechenblatt mit 24 h und rund 3,80 USD vorlegen oder 3,00 USD mit effektiv rund 17,4 h; Owner wählt.
   - RESOLVED: Owner-Entscheid am Checkpoint 22-07 (26.09.2026): Variante Stunden, 24 h mit B4, höchstens 3,76 USD, `DECKEL_MINUTEN=1354`, `DECKEL_REST_MINUTEN=86` (Plan 22-07).
3. **Nach welcher Regel "fällt die Messung für disjunction_max aus"?** Recommendation: vorher festschreiben, z. B. "Vorteil, wenn der Median von RBO@10 gegen den Altplan unter dismax um mindestens 0,05 höher liegt als unter der Summe, kein Sprachfall-Eigenrang schlechter wird und die lexikalische Latenz um höchstens 20 Prozent steigt"; tie 0.0 gegen 0.1 mitmessen. Zahlen sind Vorschlag [ASSUMED].
   - RESOLVED: Owner-Entscheid am Checkpoint 22-07 (26.09.2026): der Vorschlag gilt; tie 0.0 und 0.1 nach derselben Regel, bei beiden erfüllt der höhere RBO-Median, bei Gleichstand 0.0. Ohne Ermessen ausformuliert in 00-ablauf.md Abschnitt 6 und E10 (Plan 22-07).
4. **W4-Faktor exakt definieren.** Recommendation: F4 = Seiten je Sekunde bei N = 4 auf `--cpuset-cpus 0-3` geteilt durch Seiten je Sekunde bei N = 1 auf `--cpuset-cpus 0`, Median aus drei Runden; D-03 wendet die Schwelle 1,5 auf F4 an. Vor dem CI-Lauf in den Plan schreiben.
   - RESOLVED: Definition in Plan 22-01 in `measure.yml` festgeschrieben, in 22-06 gemessen (F4 = 3,955), vom Owner am Checkpoint 22-07 (26.09.2026) bestätigt; `B4_GEPLANT=ja`.
5. **Wo liegt `nextcloud.log` in AIO?** Vermutlich im Datenverzeichnis (`/mnt/ncdata/nextcloud.log` im Nextcloud-Container) [ASSUMED]; der Leser nimmt den Pfad aus `occ config:system:get logfile`/`datadirectory`.
   - RESOLVED: per Umsetzung, keine Vorannahme nötig: `00-lauf.sh` und `91m-langsame-aufrufe.py` (Plan 22-02) lesen den Pfad auf der Box aus `occ config:system:get logfile`, sonst `datadirectory` plus `nextcloud.log` (Rückfall `/mnt/ncdata/nextcloud.log`); die Gegenprobe von M-01 (Wert 57) fängt einen falschen Pfad ab.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| AWS CLI v2 | Aufbau, B4, Abbau | ✓ | 2.36.39 | - |
| gh | CI-Laufnummern, W4-Dispatch | ✓ | 2.92.0 | - |
| uv | Gates, Tests | ✓ | 0.11.7 | - |
| docker (lokal) | Generalprobe, Wegwerf-Container-Probe | ✓ | 29.5.2 | - |
| jq | Werkzeuge | ✓ lokal (1.8.1); Box: kam in v1.2 mit `apt-get install docker.io jq` | - | Block 8 installiert mit |
| Sicherung Systemplatte | Block 9 | ✓ `~/.findling-loadtest/systemplatte-2026-09/home-ubuntu-work.tar.gz` | - | - |
| `box.env`-Sicherung | Abbau-Rückblick | ✓ `box.env.bak-2026-09-21` | - | - |
| Korpus-Snapshot `snap-03f1d1d9ad9262704` | Box | laut Runbook ✓, lesende Probe (Vorbedingung 4/5) vor der Anfahrt fahren | - | keiner: ohne ihn keine Anfahrt |
| `ubuntu-24.04-arm` | W4, B7 | ✓ (bereits in `measure.yml`, `python.yml:185`) | 4 vCPU / 16 GB [CITED: docs.github.com] | - |
| lokale Test-Nextcloud | Generalprobe 92d/92e/94c/95c | `scripts/dev/compose.yaml` vorhanden [VERIFIED: ls] | - | nur statische Tests |
| `dig` lokal | Block 10 | ✗ (Runbook-Nachtrag) | - | `nslookup`, `curl --resolve` |

**Missing dependencies with no fallback:** keine lokal. Box-seitig ist alles über Block 8 herstellbar.

## Validation Architecture

(`workflow.nyquist_validation` steht in `.planning/config.json` auf false; der Abschnitt steht auf ausdrücklichen Auftrag.)

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (backend), Gates ruff / ruff format / pyright / vulture |
| Config file | `backend/pyproject.toml` |
| Quick run command | `cd backend && uv run pytest tests/test_ops_scripts.py tests/test_measurement_scripts.py tests/test_public_artifacts.py -x -q` |
| Full suite command | `cd backend && uv run ruff check . && uv run ruff format --check . && PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright && uv run vulture src tests --min-confidence 80 && uv run pytest -q && uv run ruff check --config pyproject.toml ../scripts && uv run ruff format --config pyproject.toml --check ../scripts` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| Krit. 6 / W1, W2 | Shebang, kein Dash, `set -eu`, beide cgroup-Layouts, verweigert statt Nullen, nie `cmdline` | statisch + Verhalten mit `FINDLING_CGROUP_ROOT`-Attrappe | `uv run pytest tests/test_ops_scripts.py -x -q` | ✅ Datei, Parameterliste (Zeile 103) erweitern |
| Krit. 6 / W3 | druckt `arch`, sichtbare CPUs, keine Textinhalte; Modus `single` | Unit (Import mit Attrappe) + CI-arm64-Erstvollzug | `uv run pytest tests/test_ops_scripts.py -k slot -x` + W4-Lauf | ❌ Wave 0 |
| MESS-07 / 92d, 94c, 95c, Leser, Einzelliste | Form, Abbruchwerte unterhalb der Pipeline, OUT-Pflicht, keine `--rm-data`-Zeile in 92d, Trefferpflicht in 95c | statisch (Muster der vorhandenen Wächter) | `uv run pytest tests/test_measurement_scripts.py -x -q` | ❌ Wave 0 |
| MESS-07 / 92c, 99d | byteweise unverändert bis zum Lauf, danach Prüfsumme | Wächter | ebenda | ✅ (`NOT_DRIVEN`), nach dem Lauf umstellen |
| MESS-09 Probe | Treffermengengleichheit per-Wort gegen Summe, nur Zahlen/Kennungen | Unit gegen kleinen Index mit sechs Feldern (Muster `test_field_plan_ranking.py`) | `uv run pytest tests/test_dismax_probe.py -x` | ❌ Wave 0 |
| MESS-09 Umsetzung (falls positiv) | gleiche Treffermenge, Rangfolge nach Regel, Operatorzeilen unverändert, Snippets | Unit + Suite + CI-Sprachfälle | `uv run pytest tests/test_query_rewrite.py tests/test_field_plan_ranking.py tests/test_search_endpoint.py -x` | ✅ Dateien, Fälle neu |
| Rohdaten | Geheimnis- und Vokabularregel über `docs/` | Gate | `uv run pytest tests/test_public_artifacts.py -x -q` | ✅ |
| MESS-07/08 Zahlen | stehen mit Wert und Datum in `docs/performance.md` | manuell + grep im Verifier | `grep -n "v1.3-Anfahrt" docs/performance.md` | manual |
| Box-Messungen selbst | die Zahlen | manual-only (bezahlte Box), Beleg sind Rohdaten + Owner-Abnahme | - | - |

### Sampling Rate
- **Per task commit:** Quick run command
- **Per wave merge:** Full suite command
- **Phase gate:** Full suite grün, W4-Lauf grün, Rohdaten committet, Owner-Abnahme vor `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `scripts/ops/cpu_sampler.sh`, `proc_anon_sampler.sh`, `ocr_slot_probe.py` + Aufnahme in `test_ops_scripts.py`
- [ ] Box-Werkzeuge 92d, 92e, 94c, 95c, Einzelliste, M-01-Leser, dismax-Probe, Ablaufskript + Wächter in `test_measurement_scripts.py`
- [ ] `backend/tests/test_dismax_probe.py` (oder Fälle in einer bestehenden Datei)
- [ ] `measure.yml` W4/B7 + `test_workflow_pins.py` grün
- [ ] `00-ablauf.md` mit Erwartungen und dismax-Regel committet

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | ja (Konten der Box) | Passwort aus `PWFILE` (99d), nie in Argumenten oder Protokollen; AWS-Schlüssel nur in der Umgebung der Entwicklungsmaschine, nie auf der Box |
| V4 Access Control | ja | SSH nur auf `<eigene-adresse>/32` (Block 1), Regel nach Adresswechsel nachziehen (Vorbedingung 15) |
| V5 Input Validation | ja | Werkzeugargumente gegen geschlossene Mengen (`ABBILD_DIGEST` Gestalt `sha256:<hex>`, Exit 2), Workflow-Eingaben per Muster (`measure.yml`) |
| V6 Cryptography | nein | - |
| V8 Data Protection | ja | Messwerkzeuge drucken nur Zahlen, Kennungen, Prozessnamen (T-02-14); synthetischer Korpus; Geheimnisregel-Gate über `docs/` |
| V11 Business Logic / Ressourcen | ja | Deckel-Timer, Zählung der Nextcloud-Instanzen vor jedem `--rm-data` (Abbruch 37), Tag-Sweep beim Abbau |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Zweite Nextcloud am Docker-Dienst löscht Messvolume | Tampering | Zählung unmittelbar vor jedem `--rm-data` (07.09.-Vorfall) |
| Kennungen/IP in öffentlichen Rohdaten | Information Disclosure | `test_public_artifacts.py`, Platzhalter nach Runbook-Geheimnisregel |
| Vergessene Ressource läuft weiter | Denial of Wallet | Tags + Tag-Sweep, harter Timer, Schlüsselpaar-Löschung (Vorbedingung 10) |
| Credentials in Prozessliste | Information Disclosure | Werte nur aus Umgebung/Datei, `aws_box.sh`-Gate |
| Wegwerf-Container mit Netz | Information Disclosure | `--network none` für B3/B5/B4 |

## Sources

### Primary (HIGH confidence)
- Codebasis, gelesen 25.09.2026: `backend/src/findling/query/rewrite.py` (100-175, 575-718), `index/rebuild.py` (Kopf, 243-322, 950), `index/open.py` (217-277), `store/repo.py` (717-788, 1448-1526), `store/vectors.py` (255-273), `extract/sandbox.py` (287-360), `extract/ocr.py` (60-80, 185-200), `embed/bench.py` (748-767), `php/lib/Service/ExAppService.php` (165, 742-770), `backend/appinfo/info.xml` (142, 236, 345-349)
- Mess- und Runbookdokumente: `docs/runbook-messbox.md` (1-998, 1448-1540), `docs/measurements/2026-09-v12-messung/README.md`, `skripte/00-ablauf.md`, `rohdaten/03-aufbau.txt`, `07-snapshot-und-abbau.txt`, `90-bestand.txt`, `95-spitze-nachher.txt`, `95b-wiederaufwaermen-1.txt`, `96-statusseite.jsonl`; `2026-09-nachfolgefassungen/skripte/92c-wechsel.sh`, `99d-filter-sortierung.sh`; `2026-09-nachmessung-m7g/skripte/68-bestand-endungen.py`, `71-ocrphase.sh`; `2026-09-vergleichsmessung-m7g/rohdaten/90-bestand.txt`
- CI: `.github/workflows/measure.yml` (1-130), `deploy-harp.yml` (1200-1215, 2885-2900, 4488-4680)
- Tests: `backend/tests/test_ops_scripts.py`, `test_measurement_scripts.py`, `test_field_plan_ranking.py`, `test_public_artifacts.py`
- Planung: `22-CONTEXT.md`, `22-DISCUSSION-LOG.md`, `ROADMAP.md` Phase 22, `REQUIREMENTS.md` MESS-07..09, `BACKLOG.md` BL-F03, `STATE.md`, `.planning/research/BL-F04-vorarbeit-2026-09-25.md`
- Probe dieser Sitzung: tantivy 0.26.2, Summe gegen dismax (ganze Zeile, je Wort, tie) und SnippetGenerator

### Secondary (MEDIUM confidence)
- [cloudprice.net m7g.4xlarge](https://cloudprice.net/aws/ec2/instances/m7g.4xlarge) und [economize.cloud m7g.4xlarge](https://www.economize.cloud/resources/aws/pricing/ec2/m7g.4xlarge/): us-east-1 ab 0,6528 USD/h, stützt Linearität
- [doit.com m7g.xlarge eu-central-1](https://www.doit.com/compute/spot/eu-central-1/m7g.xlarge) (über die Vorarbeit)
- docs.github.com, github-hosted runners (über die Vorarbeit): `ubuntu-24.04-arm` 4 vCPU / 16 GB

### Tertiary (LOW confidence)
- Nextcloud-Standard `loglevel` 2, AWS-Standard `InstanceInitiatedShutdownBehavior=stop`, `RUSAGE_CHILDREN`-Semantik: Trainingswissen, auf der Box bzw. per API vor der Anfahrt prüfen

## Metadata

**Confidence breakdown:**
- Wiederverwendung und Codeorte: HIGH, Zeilen gelesen
- Reihenfolgezwang 92c / 92d und 44/6-Loch: HIGH, aus Code und Rohdaten belegt
- Markenstand des Snapshot-Volumes: LOW, nur auf der Box lesbar (Tor eingeplant)
- Rechenblatt und B4-Kosten: MEDIUM, aus Ist-Werten und Drittquellen
- disjunction_max-Bauform: HIGH für Semantik (gefahren), MEDIUM für die Entscheidungsregel (Vorschlag)

**Research date:** 2026-09-25
**Valid until:** Beginn der Anfahrt bzw. bis Phase 23 den Such- oder Indexpfad ändert; Preise am Anfahrtstag neu lesen
