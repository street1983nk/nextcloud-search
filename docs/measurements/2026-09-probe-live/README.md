# Live-Lauf Vorab-Prüfung und Profilfläche (Phase 27, Plan 27-15)

Stand 29.09.2026. Belegt die Zustände des Blocks "Leistungsprofil" und der
Probe auf dem lokalen HaRP-Harness, mit HEAD-Abbild und HEAD-Companion.

## Aufbau

- Harness: `scripts/dev/compose-harp.yaml` (Nextcloud 34.0.3, HaRP per Digest),
  Vorproxy und Registry nach `docs/dev-setup.md`, Registry auf 127.0.0.1:5055
- Abbild: `localhost:5055/findling_backend:probe27` aus HEAD 2e3d2dc9,
  Digest in `raw/image.txt`
- Maschine: 12 vCPU, 8163373056 Bytes Docker-VM, siehe `raw/machine.txt`
- Daten: nur synthetisch (`testdata/corpus` plus 500 Dateien aus
  `build_load_corpus.py --dry-run-files`)
- Aufrufe als Admin mit Sitzung und Anfrage-Token wie im Browser; Zugangsdaten
  nur aus Umgebung und ungetrackten Dateien, nie in diesem Ordner
- Verdikte knapp und nicht ohne Produktschalter erzwungen: Speichergrenze des
  ExApp-Containers per `docker update --memory`

## Zustände

| Zustand | erwartet | beobachtet | Rohdatei |
|---|---|---|---|
| Erstaufruf ohne Profil | profileStored false, wirksam economy, nichts gespeichert | profileStored false, gewählt und wirksam economy, Vorschlag standard; `occ config:app:get findling profile` Exit 1 (ungesetzt) | `raw/01-erstaufruf.txt` |
| Probe standard/int8, keine Grenze | fits, gespeichert | fits, Slots 1, need 1535 MiB, available 4764 MiB; danach profile standard, model_precision int8 | `raw/02-fits-probe.txt` |
| Probe performance/int8, Grenze 2600 MiB | nofit mit Ursache, nichts gespeichert | nofit, Ursache memory_short, Slots 5, need 1586 MiB gegen available 1353 MiB; profile bleibt standard | `raw/03-perf-2600m-probe.txt` |
| Probe performance/int8, Grenze 2950 MiB | narrow mit Ursache, nichts gespeichert | narrow, Ursache reserve_thin, Reserve 115 MiB gegen verlangte 235 MiB; profile bleibt standard | `raw/04-perf-2950m-probe.txt` |
| Zweiter Start während einer Probe | busy | erster Start started, zweiter (gleiches Ziel und standard/fp32) je code busy; die laufende Probe endet normal (narrow), profile bleibt standard | `raw/05-busy.txt` |
| Aufwärts ohne Probe über POST admin/profile | abgelehnt | 400 probe_required, profile unverändert | `raw/06-abwaerts.txt` |
| Abwärtsweg economy/int8 ohne Probe | saved | 200 saved, profile economy, Overview gewählt und wirksam economy | `raw/06-abwaerts.txt` |
| Nicht-Admin (testuser, Sitzung) | kein 200, profile unverändert | POST admin/profile/check 403, POST admin/profile 403 (zweimal), GET admin/profile/check 403, GET admin/overview 403; profile vorher und nachher economy; Gegenprobe GET als Admin 200 | `raw/07-nicht-admin.txt` |

## Indexierung während der Probe (D-27-05)

- In 03 und 04 lief die Indexierung des Lastkorpus
- Schritt pause: die übergebenen Dateien fallen auf 0 (04: 10, 2, 2, 0), die
  laufenden werden fertig, `indexed` bleibt ab ocr_one stehen (03: 426, 04: 467)
- Nach der Probe: wieder übergeben (03: 40, 04: 10), `embedded` und der Abbau
  von `scheduled` laufen weiter (04: embedded 251 auf 267, scheduled 313 auf 289)
- Die Probe 02 lief, bevor der Container Arbeit hatte; sie belegt nur das Verdikt

## Speichergrenze

- Ausgangswert: keine Grenze (Memory 0)
- `docker update --memory 0` ändert nichts, eine Grenze lässt sich so nicht
  entfernen; zurückgesetzt durch `app_api:app:unregister` und `register` ohne
  `--rm-data`, danach Memory 0, gleiches Abbild, Datenvolume erhalten, Profil
  economy erhalten

## Owner-Abnahme 29.09.

- Signal: "approved"; gemeinsam per Playwright auf der Adminseite des Harness
  (`/settings/admin/findling`)
- Block "Leistungsprofil" steht vor "Regeln und Grenzen", genau drei Profile
- fp32-Häkchen nur bei Standard und Leistung, mit Größenangabe 448,5 MB
- Knöpfe "Übernehmen und prüfen" und "Bei Sparsam bleiben", kein
  Erweitert-Bereich; "Übernehmen und prüfen" gesperrt ohne Änderung
- Standard/int8 live: Fortschrittszeile "Prüfung läuft: OCR mit einem Slot",
  Hinweis auf pausierte Indexierung, Verdikt Passt, gespeichert (occ profile
  standard), aria-live-Ansage und Fokus auf der Verdikt-Karte, Karte bleibt
  nach Neuladen
- Abwärtsweg auf Sparsam: Knopf heißt "Übernehmen", speichert ohne Probe (occ
  profile economy)
- Befund, behoben in 9d6a11c3: das Auswahlfeld wurde aus `profile.chosen` des
  Containers vorbelegt (hängt eine Runde nach) statt aus dem gespeicherten
  Wert; neu `profileSaved` aus appconfig in AdminViewService, Template und
  admin.js; live bestätigt (economy gespeichert, Container noch standard,
  Auswahl zeigt Sparsam, keine Konsolenfehler)
- Harness-Hinweis ohne Produktfehler: opcache `revalidate_freq` 60 s und der
  `?v=`-Cache von admin.js verzögerten die Sichtbarkeit; im Release wechselt
  die Version
- Einzige Konsolenfehler kamen von Nextcloud user_status (404), nicht von
  Findling
- Nicht live gefahren: fp32 (siehe Lücken)
- Getrennter Befund, nicht Teil von 27-15, eigener Quick-Fix folgt:
  Deckungsgrad zeigte "607 von 587", weil der Nenner `files_seen` nur beim
  einmaligen Crawl entsteht und nach Ereignis-Indexierung nicht mitwächst
  (Altfehler v1.0)

## Lücken

- fp32-Durchlauf nicht gefahren: er lädt 470268510 Bytes aus dem Release und
  stößt bei fits eine Neuberechnung aller Vektoren an; auf der Adminseite als
  standard/fp32 auswählbar, wenn der Owner ihn sehen will
- Die Fläche selbst (Texte, Fokus, Fortschrittszeile) ist in den Rohdaten nur
  über die Routen belegt; die Sichtprüfung steht unter "Owner-Abnahme 29.09."
- Beobachtung ohne Befund: standard hat auf dieser Box 1 Slot; das folgt aus
  der Formel mit MemAvailable rund 4,8 GiB (0,4 x 0,8 x M minus Grundlast)
