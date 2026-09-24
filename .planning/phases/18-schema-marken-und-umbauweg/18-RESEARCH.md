# Phase 18: Schema, Marken und Umbauweg - Research

**Recherchiert:** 2026-09-24
**Domäne:** tantivy-Schemawechsel auf Bestandsindizes, Re-Analyse-Umbau, Versionsmarken, Upgrade-Beweisstrecke
**Konfidenz:** HIGH für den Umbauweg und die Marken (alles am eigenen Baum gemessen), MEDIUM für Plattenplatz-Hochrechnung und Laufzeit (synthetischer Korpus, echte Zahl erst in Phase 22)

---

## Zusammenfassung

Der Re-Analyse-Umbau ist mit der vorhandenen tantivy-API vollständig baubar, und
zwar ohne einen einzigen Trick: **alle acht Felder, die ein Dokument braucht, kommen
aus `Searcher.doc(address).to_dict()` heraus**, `body_en` ist rekonstruierbar, weil es
denselben Text trägt wie `body_de`. Ich habe den ganzen Durchlauf am 2026-09-24 mit
dem gepinnten `tantivy 0.26.2` aus `backend/.venv` gefahren: 3.000 Dokumente aus einem
Index mit dem echten `build_schema()` in ein Verzeichnis mit dem Dreizehn-Felder-Schema,
bandweise über `file_id`, und die Gegenprobe `alle Felder aller Dokumente feldweise
gleich` steht auf `True`. Die Wiederaufnahme braucht **keinen neuen Zustand in
`state.db`**: das halbfertige neue Verzeichnis ist sein eigener Fortschrittsmerker, weil
`file_id` ein Fast Field ist und `search(all_query, limit=1, order_by_field="file_id",
order=Order.Desc)` die höchste bereits kopierte Nummer in einer Abfrage liefert.

Die heikelste Einzelfrage der Phase, der sechste Merker, hat eine Falle, die im
Owner-Entscheid E-17-4 noch nicht benannt ist: `_seed_meta()` schreibt **jeden fehlenden
Merker mit dem erwarteten Wert**, weil der Poller `open_store(..., meta=expected)` ruft.
Ein sechster Merker, der einfach in `expected_versions()` aufgenommen wird, wird auf
einer Bestandsinstallation also mit dem Wert gesät, den die laufende Umgebungsvariable
gerade fordert. Damit meldet `version_mismatch` genau dann keine Abweichung, wenn der
Admin die Sprache umschaltet, also genau dann nicht, wenn der Merker gebraucht wird. Die
empfohlene Lösung dreht das um: der Merker wird aus der Saat **herausgehalten**, und
sein Fehlen wird in `version_mismatch` als "die Installation hat eine Teilmenge von
de,en" gelesen. Diese Ausnahme ist eng, beweisbar und schließt sich selbst, sobald der
Merker einmal geschrieben wurde.

Der Zwischenzustands-Beweis ist in dieser Phase billiger als er klingt: `DEFAULT_FIELDS`
bleibt in Phase 18 bei vier Feldern, und diese vier existieren in Schema 1 **und** in
Schema 2. Der `ValueError`-Pfad ist also nicht erreichbar, weil es keine Feldliste gibt,
die ein unbekanntes Feld nennen könnte. Beweisbar ist das als Mengeninklusion plus ein
AST-Wächter nach dem Muster von Plan 17-03, nicht als Integrationstest.

**Primärempfehlung:** `index/rebuild.py` als Bandlauf über `Query.range_query` auf
`file_id`, Fortschritt aus dem halbfertigen Zielverzeichnis, Verzeichnistausch mit
geschlossenen Handles über `Path.rename`, Sprachmerker außerhalb der Saat mit
Teilmengenregel in `version_mismatch`, und `DEFAULT_FIELDS` rührt diese Phase nicht an.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Begründung |
|------------|-------------|----------------|-------------|
| Sechs Körperfelder im Schema | Container, Indexkern (`index/schema.py`) | - | Das Schema wird einmal geschrieben und für die Lebensdauer des Verzeichnisses gelesen; nur `build_schema()` entscheidet darüber |
| Kettenregistrierung für sechs Sprachen | Container, Indexkern (`index/open.py`) | - | Die einzige Stelle, die einen Index öffnet; Registrierung ist Teil des Öffnens |
| Befüllung nach `FINDLING_LANGUAGES` | Container, Schreibseite (`index/writer.py`) | Config (`config.py:_languages`) | `IndexBatchWriter.add()` ist der einzige Verbraucher der aktiven Sprachmenge |
| Re-Analyse-Umbau | Container, neues Modul `index/rebuild.py` | Lifespan-Aufgabe (`main.py`) | Der Index liegt nur im Container; ein Vorgang mit Lebensdauer, Fortschritt und Abbruchverhalten gehört nicht in `open.py` |
| Drift-Erkennung Sprachmenge | Container, Store (`store/repo.py`) + `index/open.py` | - | `expected_versions()` weiß, was der Code erzeugt; `version_mismatch` weiß, was auf der Platte steht |
| Plattenplatz-Vorprüfung | Container, `index/rebuild.py` | `index/writer.py` (`free_bytes`, `disk_is_tight`) | Der Bodenwert ist schon da und darf kein zweites Mal geschrieben werden |
| Fortschrittsanzeige / Banner | PHP-Companion (`templates/admin.php`) | Container `GET /status` | Der Container misst, die Adminseite erzählt; der Text ist Übersetzungsgut |
| Startwarnung OCR-Mismatch | Container, Lifespan (`main.py`) | `config.py` | Eine Warnung über zwei Einstellungen gehört dorthin, wo beide gelesen sind |
| Lockstep-Migration 1.3.0 | PHP-Companion (`lib/Migration/`) | - | Sie verwirft eine aufgezeichnete Backendversion; sie ist **nicht** der Ort des Indexumbaus |
| Upgrade-Beweis | CI (`deploy-harp.yml`) | - | Nur dort steht eine echte Nextcloud mit einer echten Vorversion |

---

## Standard Stack

Diese Phase bringt **keine neue Abhängigkeit**. Alles Nötige steht schon im Baum.

### Kern

| Baustein | Version | Zweck | Warum dieser |
|----------|---------|-------|--------------|
| `tantivy` | 0.26.2 (gepinnt in `backend/pyproject.toml:13`) | Index, Schema, Bandlauf, Verzeichnistausch | Bereits gepinnt, Pin wurde in Plan 17-08 bewegt und darf in dieser Phase nicht wieder bewegt werden [VERIFIED: `backend/pyproject.toml`, `.venv` meldet `tantivy v0.26.2, index_format v7`] |
| `shutil` / `os` / `pathlib` | stdlib | `disk_usage`, `rename`, `rmtree` | `shutil.disk_usage` steht schon in `index/writer.py:376` und misst dieselbe Platte |
| `asyncio` | stdlib | Lifespan-Aufgabe des Umbaus | Vorbild `_release_when_idle` in `main.py:254` |

### Was NICHT gebraucht wird

| Verlockung | Warum nein |
|------------|-----------|
| Ein Migrationsframework | Es gibt genau eine Migration dieses Typs, und sie ist ein Verzeichnistausch |
| `shutil.move` | Der Bezeichner `move` steht in `FORBIDDEN_IDENTIFIERS` des Readonly-Gates (`backend/tests/test_readonly_gate.py:63`); `Path.rename` und `os.replace` sind nicht darauf [VERIFIED: Gate liest jedes `ast.Attribute` und jeden `ast.Name`, Zeile 340-347] |
| Ein zweiter Fortschrittszustand in `state.db` | Der halbfertige Zielindex ist der Fortschritt, siehe Pattern 2 |
| Neue Pakete jeglicher Art | Siehe Package Legitimacy Audit |

**Installation:** keine.

---

## Package Legitimacy Audit

**Diese Phase installiert kein einziges externes Paket.** Weder `backend/pyproject.toml`
noch `php/composer.json` bekommen einen neuen Eintrag; der `tantivy`-Pin steht seit Plan
17-08 auf 0.26.2 und wird in Phase 18 ausdrücklich nicht bewegt (er ist der Merker
`tantivy_version`, und eine bewegte Marke ist eine Owner-Frage).

| Package | Registry | Disposition |
|---------|----------|-------------|
| (keines) | - | Nicht zutreffend |

**Wegen slopcheck-Verdikt entfernte Pakete:** keine.
**Als verdächtig markierte Pakete:** keine.

slopcheck wurde nicht gefahren, weil es keine Kandidatenliste gibt. Sollte ein Plan
dieser Phase wider Erwarten ein Paket vorschlagen, gilt das Gate ungemildert: erst
slopcheck, dann `pip index versions`, dann ein `checkpoint:human-verify`.

---

## Architecture Patterns

### Systemüberblick: der Umbau im Betrieb

```
                       Container (eine Instanz, ein Volume)
 +---------------------------------------------------------------------------+
 |                                                                           |
 |  Lifespan                                                                 |
 |    +-- Poller (Task 1) ---- IndexWriter auf  $VOL/index   <-- Lock A      |
 |    +-- Reconcile (Task 2)                                                 |
 |    +-- Release (Task 3)                                                   |
 |    +-- UMBAU (Task 4, NEU) - IndexWriter auf $VOL/index.rebuild <- Lock B |
 |                                                                           |
 |  Leseseite (resources._OPEN, zwischengespeichert nach index_dir)          |
 |          |                                                                |
 |          v                                                                |
 |     $VOL/index  (Schema 1, antwortet die ganze Zeit weiter)               |
 |                                                                           |
 +---------------------------------------------------------------------------+

 Ablauf:

 Start -> version_mismatch meldet {schema_version, languages}
        |
        v
  [1] Vorpruefung:  Index lesbar?  Platz fuer zwei Verzeichnisse?  Schema-Sprung = 1?
        |  nein --> Abbruch VOR dem Start, Banner mit Zahl, Rueckfallweg benannt
        v  ja
  [2] Poller silence(), laufenden Durchgang auslaufen lassen, Writer schliessen
        |
        v
  [3] Bandlauf:  file_id-Band aus $VOL/index lesen
                 --> Dokument neu bauen (8 gespeicherte Werte + n Koerperfelder)
                 --> in $VOL/index.rebuild schreiben
                 --> commit je Band (das ist die Absturzkoernung)
                 ^                                            |
                 +--------------  Cursor = max(file_id) ------+
                                  im Zielindex, gelesen per
                                  order_by_field, KEIN neuer
                                  Zustand in state.db
        |
        v
  [4] Endprobe:  num_docs(neu) == num_docs(alt) ?  sonst Abbruch ohne Tausch
        |
        v
  [5] Handles zu (beide Indizes, Leseseitencache), dann
      index -> index.retired ; index.rebuild -> index ; rmtree(index.retired)
        |
        v
  [6] Marken schreiben: schema_version=2, languages=<aktiv>, REBUILD_MARK leeren
        |
        v
  [7] Leseseitencache verwerfen, Poller arm()
```

### Empfohlene Dateistruktur

```
backend/src/findling/index/
  rebuild.py        # NEU: Vorpruefung, Bandlauf, Tausch, Rueckfall
  schema.py         # 9 -> 13 Felder, FIELDS waechst
  open.py           # 4 -> 8 register_tokenizer, expected_versions() +1 Merker
  writer.py         # add(): Schleife ueber die aktiven Sprachen statt _index_english
backend/src/findling/
  config.py         # SCHEMA_VERSION = 2, _languages() gegen SNOWBALL_NAME statt DEFAULT_LANGUAGES
  api/status.py     # languagesActive, languagesFilled, rebuild-Fortschritt
  api/resources.py  # reset_read_side() fuer den Tausch
  main.py           # Lifespan-Aufgabe + Startwarnung OCR
php/
  lib/Migration/Version001300Date2026MMDD000000.php   # Kopie des Lockstep-Musters
  templates/admin.php                                  # sechstes Banner
  l10n/{de,de_DE,fr}.{json,js}                         # neue Schluessel im Gleichstand
.github/workflows/
  deploy-harp.yml   # zweiter, umgedrehter Schritt NEBEN dem bestehenden
```

### Pattern 1: Der Bandlauf statt tiefer Offsets

**Was:** Der Durchlauf über den alten Index läuft in `file_id`-Bändern mit
`Query.range_query`, nicht mit wachsendem `offset` auf `Query.all_query()`.

**Wann:** Immer. Ein `search(all_query, limit=1000, offset=51000)` lässt tantivy intern
52.000 Treffer sammeln, um 1.000 herauszugeben; über den ganzen Lauf ist das quadratisch.
Der Bandlauf über ein Fast Field ist linear.

**Gemessen am 2026-09-24** (Datei `/tmp/probe18h.py`, `tantivy 0.26.2`, 3.000 Dokumente
zu je rund 2,5 kB, vier Ketten, diese Entwicklungsmaschine): **683 Dokumente je Sekunde,
4,39 s Gesamtlauf, Feldgleichheit aller 3.000 Dokumente `True`**. Die deutsche Kette mit
dem 276.496-Einträge-Zerlegungsautomaten lief in dieser Probe **nicht** mit, weil
`/usr/share/dict/ngerman` auf dieser Maschine nicht existiert; der echte Lauf ist
deshalb langsamer, und um wie viel, sagt erst `findling.index.analyzer.measure()` im
Container. [VERIFIED: eigene Messung 2026-09-24]

```python
# Source: eigene Messung 2026-09-24, tantivy 0.26.2 aus backend/.venv
from tantivy import FieldType, Order, Query

BAND = 500

cursor = _resume_cursor(target)          # siehe Pattern 2
while True:
    band = Query.range_query(
        source.schema, FIELD_FILE_ID, FieldType.Unsigned, cursor + 1, _UPPER_BOUND, True, True
    )
    hits = reader.search(band, limit=BAND, order_by_field=FIELD_FILE_ID, order=Order.Asc).hits
    if not hits:
        break
    for _score, address in hits:
        stored = reader.doc(address).to_dict()
        writer.add_document(_document_from(stored, languages))
        cursor = int(stored[FIELD_FILE_ID][0])
    writer.commit()                      # ein Band ist die Absturzkoernung
```

**Gemessene Eigenschaften von `to_dict()`** (2026-09-24, echtes `build_schema()`):

| Beobachtung | Wert |
|---|---|
| Rückgabeform | `dict[str, list[value]]`, immer Listen, auch bei einem Wert |
| Enthaltene Schlüssel | genau die acht gespeicherten: `body_de`, `ext`, `file_id`, `mtime`, `name`, `path`, `storage_id`, `title` |
| `body_en` | fehlt, weil `stored=False`; rekonstruierbar aus `body_de` |
| Leere Zeichenkette | kommt als `[""]` zurück, der Schlüssel verschwindet nicht |
| `mtime` negativ | kommt als `-5` zurück, Integer-Feld ist i64 |
| `storage_id` groß | `2**40` kommt unversehrt zurück |
| Reihenfolge ohne `order_by_field` | Einfügereihenfolge, aber darauf wird nicht gebaut |

### Pattern 2: Das Zielverzeichnis ist sein eigener Fortschrittsmerker

**Was:** Nach einem Neustart fragt der Umbau den halbfertigen Zielindex nach der
höchsten bereits kopierten `file_id` und setzt dort fort. Es gibt keinen Fortschritts-
zähler in `state.db`, keinen Batch-Marker und keine zweite Generation.

**Warum das hält:** `file_id` ist `fast=True` (`index/schema.py:87`), die Sortierung ist
also eine Spaltenabfrage und kein Scan. Ein Absturz zwischen zwei Commits verwirft das
unvollständige Band; tantivy öffnet auf dem Stand des letzten Commits, was das
Writer-Modul für `kill -9` schon gemessen hat (`index/writer.py:8-15`). Die neu
geschriebenen Dokumente sind idempotent, also kostet die Wiederholung eines Bandes
nichts.

```python
# Source: eigene Messung 2026-09-24
def _resume_cursor(target: Index) -> int:
    """Die hoechste bereits uebertragene file_id, 0 auf einem leeren Zielindex."""
    target.reload()
    searcher = target.searcher()
    if searcher.num_docs == 0:
        return 0
    top = searcher.search(Query.all_query(), limit=1, order_by_field=FIELD_FILE_ID, order=Order.Desc)
    return int(searcher.doc(top.hits[0][1]).to_dict()[FIELD_FILE_ID][0])
```

**Die Bedingung, ohne die das falsch wird:** Der Poller darf während des Umbaus nicht in
den alten Index schreiben. Sonst landet ein Dokument mit einer `file_id` unterhalb des
Cursors im Quellindex und wird nie kopiert. `Poller.silence()` und `Poller.arm()`
existieren bereits (`worker/poller.py:509, 519`). Die Arbeit geht dabei nicht verloren:
die Warteschlange liegt in Nextcloud, die Zeilen bleiben `scheduled` und werden nach dem
`arm()` abgearbeitet. Das ist zugleich die Antwort auf `INDEX_WORKERS = 1`: während des
Umbaus ruht die OCR-Spitze, und die beiden RAM-Spitzen treffen sich nicht.

### Pattern 3: Der Verzeichnistausch, und was ihn auf Windows sprengt

**Gemessen am 2026-09-24 auf dieser Maschine (Windows 11, NTFS):**

| Versuch | Ergebnis |
|---|---|
| `os.rename` auf das **offene** Quellverzeichnis (lebender `Searcher`, mmaps) | `PermissionError`, WinError 5, "Zugriff verweigert" |
| Dasselbe nach `del searcher; del index; gc.collect()` | OK |
| `os.rename` des **offenen** Zielverzeichnisses an die Zielstelle | `PermissionError`, WinError 5 |
| `shutil.rmtree` des stillgelegten Verzeichnisses | OK |

Auf Linux, wo der Container läuft, gelingt `rename` auch bei offenen Deskriptoren, weil
POSIX über Inodes umbenennt [CITED: POSIX `rename(2)`, `unlink(2)`]. Das ist aber genau
die Falle: **auf Linux würde der Tausch mit offenen Handles scheinbar funktionieren, und
die Leseseite hätte danach einen Index in der Hand, den es im Dateisystem nicht mehr
gibt.** Der Code muss deshalb ohnehin alle Handles schließen, und dann läuft dieselbe
Reihenfolge auch auf der Entwicklungsmaschine grün. Das ist keine Windows-Rücksicht,
das ist die einzige korrekte Reihenfolge, und Windows macht sie nur lauter.

```python
# Source: eigene Messung 2026-09-24, Reihenfolge so und nicht anders
# 1. Zielindex committen, wait_merging_threads(), Objekt loslassen
# 2. Quellindex loslassen (Poller-Writer ist schon zu)
# 3. Leseseitencache verwerfen (resources), sonst haelt _OPEN die alten mmaps
# 4. index -> index.retired
# 5. index.rebuild -> index
# 6. rmtree(index.retired)
```

Die Leseseite ist die unterschätzte Hälfte. `resources._OPEN` wird unter
`index_dir` zwischengespeichert (`api/resources.py:285`), und der Pfad **ändert sich
beim Tausch nicht**. Der vorhandene Invalidierungszweig greift also nicht, und ohne eine
neue, ausdrückliche `reset_read_side()` antwortet jede Suche bis zum nächsten
Containerstart aus dem stillgelegten Verzeichnis. Auf Linux tut sie das schweigend und
scheinbar fehlerfrei.

### Pattern 4: Der sechste Merker ohne Bestands-Reindex

Das ist die heikelste Einzelfrage der Phase, und der Owner-Entscheid E-17-4 nennt die
Auflage, ohne den vollständigen Weg zu kennen. Hier ist er, am Code gelesen.

**Der Mechanismus heute:**

```
worker/poller.py:322-324
    expected = expected_versions(build_artifact().digest)
    store = open_store(settings().state_db, meta=expected)   # <-- die Saat
    start_rebuild_on_drift(store, expected)

store/repo.py:1394-1404 (_seed_meta)
    seed = dict(_DEFAULT_META)
    seed.update(meta or {})              # der ERWARTETE Wert gewinnt
    for key, value in seed.items():
        if key not in stored:            # nur fehlende Schluessel
            store.write_meta(key, value)
```

**Die Falle:** Ein sechster Merker, der nur in `expected_versions()` ergänzt wird, ist
auf jeder Bestandsinstallation zunächst nicht gespeichert. Die Saat schreibt ihn dann
mit **genau dem Wert, den die laufende Umgebungsvariable gerade fordert**. Für eine
Instanz mit Werkseinstellung `de,en` ist das zufällig richtig und es passiert nichts,
also sieht die Sache im Test grün aus. Für die eine Instanz, die beim Upgrade
gleichzeitig `FINDLING_LANGUAGES=de,en,es` setzt, schreibt die Saat `de,en,es`,
`version_mismatch` findet keine Abweichung, der Umbau unterbleibt, und Spanisch bleibt
für den ganzen Bestand leer. Der Merker verfehlt sein Ziel exakt in dem Fall, für den
er gebaut wird. Der Docstring von `open_store` warnt genau davor: "an open that silently
repaired it would destroy that evidence before anybody looked."

**Empfohlene Umsetzung, Option A (drei enge Eingriffe):**

1. `expected_versions()` bekommt die Sprachmenge als **zweiten Parameter**, nicht als
   `settings()`-Lesung im Modul. Begründung: `digest` wird heute schon hereingereicht
   statt gelesen, und ein Parameter macht die vier Aufrufstellen sichtbar
   (`api/resources.py:139`, `worker/poller.py:322`, `worker/poller.py:1833`,
   `tools/one_load.py:265`). Der Wert ist `",".join(settings().languages)`; die
   Normalisierung nach Schemafeldreihenfolge liefert `_languages()` schon heute, weil es
   über die geordnete Konstante iteriert und nicht über die Eingabe
   (`config.py:1076`), und der Kommentar an `SNOWBALL_NAME` (`config.py:121-127`) sagt
   ausdrücklich, dass diese Ordnung ab Phase 18 einen Merker speist.

2. `_seed_meta()` hält genau diesen einen Schlüssel heraus. Muster und Präzedenz sind
   im Baum vorhanden: `EMBEDDING_MARK` wird bewusst aus `expected_versions()`
   herausgehalten und erst in `api/resources.py:146` angehängt, und
   `stamp_after_rebuild` überspringt `index_version` mit einem eigenen Absatz. Eine
   dritte benannte Ausnahme dieser Bauart ist kein neues Muster.

3. `Store.version_mismatch` bekommt die dritte `if`-Zeile, neben
   `_generation_at_least` und dem in Plan 17-07 ergänzten `_index_format_matches`:

```python
# Source: Vorschlag, gebaut nach dem Muster von repo.py:1315 und :1327
def _languages_are_legacy(stored: str | None, expected: str) -> bool:
    """True when the mark was never written and the expectation fits what could have been.

    A mark that was never written counts as diverging everywhere else in this file,
    and rightly so: an unnamed analyzer could be any analyzer. This one mark is the
    exception, and the reason is provable rather than convenient. Up to and including
    1.2.0, _languages() filtered FINDLING_LANGUAGES against DEFAULT_LANGUAGES, which
    was ("de", "en") in every release: no installation in the field can carry a body
    field outside that pair, because no released build could write one. So an absent
    mark is compatible with any expectation that stays inside the pair, and with
    nothing else. The first stamp writes the mark, and from then on this branch is
    never taken again.
    """
    if stored is not None:
        return False
    return set(expected.split(",")) <= set(LEGACY_LANGUAGES)
```

**Die vier Fälle, durchgerechnet:**

| Bestand | `FINDLING_LANGUAGES` nach dem Upgrade | Erwartung | Gespeichert | Verdikt | Richtig? |
|---|---|---|---|---|---|
| 1.2.0, Werkseinstellung | ungesetzt | `de,en` | fehlt | Teilmenge, kein Drift | ja, D-04 gehalten |
| 1.2.0, `de` gesetzt | `de` | `de` | fehlt | Teilmenge, kein Drift | ja, kein Reindex für eine Instanz, die nichts geändert hat |
| 1.2.0, Werkseinstellung | `de,en,es` | `de,en,es` | fehlt | keine Teilmenge, Drift | ja, der Umbau startet |
| 1.3.0, Merker steht auf `de,en,es` | `de,en` | `de,en` | `de,en,es` | Ungleichheit, Drift | ja, das Abschalten greift auch (PITFALLS Nr. 6, "Gegenlauf") |

**Die eine bekannte Lücke, die diese Option bewusst offen lässt:** eine Instanz mit
`FINDLING_LANGUAGES=de`, die nach dem Upgrade auf `de,en` wechselt, bekommt keinen Drift,
weil `de,en` eine Teilmenge ist. Das ist **genau das heutige Verhalten** (es gibt heute
gar keinen Merker), also keine Verschlechterung, und es schließt sich beim ersten
beliebigen Drift von selbst. Es gehört als Satz in `docs/` und als Test, damit es
niemand für ein Versehen hält.

**Option B, zum Vergleich:** Das Fehlen hart als `"de,en"` lesen statt als Teilmenge.
Eine Zeile kürzer, aber sie schickt jede Instanz mit `FINDLING_LANGUAGES=de` beim
Upgrade in einen Reindex, den nichts rechtfertigt. Nicht empfohlen. Die Teilmengenregel
kostet ein `set(...) <= set(...)` und einen Absatz.

**Option C, das Gegenstück zu E-17-4 Option b:** den Sprachwechsel über einen eigenen
Zustand in `state.db` statt über `expected_versions()` erkennen. Der Owner hat am
23.09.2026 Option a gewählt; C ist hier nur benannt, damit der Planer weiß, dass die
Entscheidung getroffen ist und nicht neu aufgemacht wird.

**Was `stamp_after_rebuild` angeht:** die Funktion iteriert über `expected` und schreibt
alles außer `index_version`, der neue Merker fährt also mit. Sie ist aber die falsche
Stelle für den Re-Analyse-Umbau: ihr Tor ist `verdicts_older_than(generation) == 0`,
und der Umbau rührt keine Verdikte an. Der Umbau braucht eine eigene, schmale
Stempelfunktion, die nach dem erfolgreichen Tausch `schema_version` und `languages`
schreibt und `REBUILD_MARK` leert. Zwei Stempler mit einem Namen wären der klassische
Weg, wie ein halber Index sich für fertig erklärt.

### Pattern 5: Die sichere Reihenfolge für den Zwischenzustand

Die Frage lautet: welche Reihenfolge aus Schema-Erweiterung, Merker, Umbau und
Feldlisten-Freischaltung lässt den `ValueError`-Pfad nie erreichbar werden?

**Gemessen am 2026-09-24 auf `tantivy 0.26.2`, damit die Annahme nicht aus 0.26.0 stammt:**

| Vorgang | Ergebnis |
|---|---|
| `parse_query_lenient(..., default_field_names=["body_de","body_es"])` gegen ein Schema ohne `body_es` | ``ValueError: Field `body_es` is not defined in the schema.`` (in 0.26.2 mit Backticks, nicht mit Apostrophen wie in der Milestone-Research notiert) |
| Dasselbe, wenn `body_es` im Schema steht, seine Kette aber **nicht registriert** ist | kein Fehler, die Abfrage läuft |
| `writer.add_document(doc)` mit einem Feldnamen, den das Schema nicht kennt | kein Fehler, das Feld ist danach spurlos weg (`{'file_id': [999]}`) |
| `writer.add_document(doc)`, wenn das Schema ein Textfeld trägt, **dessen Kette nicht registriert ist** | ``ValueError: Schema error: 'Error getting tokenizer for field: body_es'`` , **auch wenn das Dokument dieses Feld gar nicht trägt** |

Der letzte Punkt ist neu gegenüber allen bisherigen Recherchedokumenten und er ist
bindend: **`open_index` muss alle sechs Körperketten immer registrieren, unabhängig von
`FINDLING_LANGUAGES`.** Wer die Registrierung an die aktive Sprachmenge hängt, bekommt
auf jeder Instanz, die nicht alle sechs Sprachen führt, bei jedem einzelnen Schreibvorgang
eine `ValueError`, also einen Indexer, der nichts mehr indexiert. Die Kosten dafür sind
null: der Docstring von `snowball_analyzer` hält fest, dass die Snowball-Ketten in
tantivy einkompiliert sind und nichts mitbringen; nur die deutsche Kette kostet die 23 MB,
und die wird ohnehin immer gebaut.

**Die sichere Reihenfolge:**

1. `schema.py` trägt dreizehn Felder, `open.py` registriert acht Ketten,
   `SCHEMA_VERSION = 2`. **Bestandsindizes sind davon unberührt**, weil
   `Index.open()` das persistierte Schema liest und `build_schema()` auf einer
   Bestandsinstallation gar nicht mehr gerufen wird (`index/open.py:97`).
2. Der Sprachmerker kommt dazu (Pattern 4). Erst jetzt kann der Umbau überhaupt
   ausgelöst werden.
3. Der Umbau läuft und tauscht das Verzeichnis.
4. Der Stempel hebt `schema_version` auf `2`.
5. **Phase 19** macht `DEFAULT_FIELDS` und `FIELD_BOOSTS` zu Funktionen des gespeicherten
   `schema_version`-Merkers.

**Warum der Pfad in Phase 18 nicht erreichbar ist, als prüfbarer Satz:** `DEFAULT_FIELDS`
bleibt `[body_de, body_en, name, title]`, und diese vier Namen stehen in Schema 1 wie in
Schema 2. Der Beweis ist eine Mengeninklusion und kein Integrationstest:

```python
def test_the_query_fields_exist_in_both_schema_generations() -> None:
    assert set(DEFAULT_FIELDS) <= set(FIELDS_SCHEMA_1)
    assert set(DEFAULT_FIELDS) <= set(FIELDS)
    assert set(TITLE_ONLY_FIELDS) <= set(FIELDS_SCHEMA_1)
```

Dazu ein AST-Wächter nach dem Muster von Plan 17-03, der rot wird, sobald ein
`body_`-Feldname in `DEFAULT_FIELDS` oder `FIELD_BOOSTS` auftaucht, der nicht in
Schema 1 steht, **solange** die Feldliste noch eine Konstante ist. Der Wächter ist der
Teil, der in Phase 19 bewusst umgebaut wird, und genau deshalb muss er in Phase 18
existieren: er macht die Phasengrenze zu einer Codegrenze.

Zusätzlich gehört ein Test dazu, der `build_query` gegen einen **echten Schema-1-Index**
fährt und zusichert, dass er weder wirft noch eine leere degradierte Antwort erzeugt.
Ein Nachbau des Schemas im Test genügt nicht; die Fixture muss aus `build_schema()`
einer festgehaltenen Feldliste kommen.

### Pattern 6: Plattenplatz-Vorprüfung

**Gemessen am 2026-09-24** (`/tmp/probe18d.py`, 2.000 Dokumente, 9,88 MB Text, echte
Snowball-Ketten für es/it/nl/pt, englische Kette als Platzhalter für die deutsche):

| Aufbau | Verzeichnisgröße | Faktor gegen den Text | Delta |
|---|---|---|---|
| 9 Felder, `de,en` (heutiges Schema) | 2.277.376 B | 0,231 | Bezug |
| 13 Felder, vier davon **leer** | 2.286.432 B | 0,232 | **+9.056 B, +0,40 %** |
| 13 Felder, alle sechs befüllt | 5.692.365 B | 0,576 | +3.414.989 B, +150 % |

**Korrektur an E-17-2:** Der Entscheid sagt "Leere Felder kosten gemessen null Byte auf
der Platte". Gemessen sind **+0,40 % über 2.000 Dokumente**, also rund 4,5 Byte je
Dokument Schema- und Segmentbuchführung. Praktisch nichts, und die Entscheidung wird
davon nicht berührt; die Zahl gehört trotzdem in die Doku, weil "null Byte" eine
Behauptung ist, die eine Messung widerlegt, und die nächste Person misst nach.

**Je zusätzlich befüllter Kette:** `(5.692.365 - 2.277.376) / 4 = 853.747 B`, also
**0,086 mal die Textmenge**. Das deckt sich mit dem dokumentierten Faktor 0,076 für
eine ungespeicherte Kette (`index/schema.py:10-20`) und bestätigt die Hochrechnung der
Milestone-Research unabhängig.

**Hochrechnung auf die Box:** heute 785.308.851 B bei Faktor rund 0,45
(`docs/performance.md:2923`), also rund 1,745 GB extrahierter Text. Vier weitere
befüllte Ketten kosten `4 * 0,086 * 1,745 GB = rund 600 MB`, neuer Index also **rund
1,39 GB**, Spitze während des Umbaus **rund 2,17 GB**. [ASSUMED für den echten Korpus,
weil mein Testtext künstlich und stark repetitiv ist; die echte Zahl fällt in Phase 22
als Nebenprodukt des ersten echten Umbaus an, MESS-08.]

**Empfohlene Laufzeitregel** (keine der drei Zahlen ist geraten, alle drei sind
begründbar):

```
benoetigt = groesse(alter_index) * (1 + 0.40 * anzahl_neu_befuellter_sprachen)
gate      = shutil.disk_usage(volume).free >= benoetigt + settings().min_free_bytes
```

Der Faktor 0,40 je Sprache liegt oberhalb des gemessenen 0,372
(`0,086 / 0,231`) und unterhalb einer Verdoppelung; er ist bewusst konservativ, weil ein
Abbruch vor dem Start billig ist und ein Abbruch mitten im Lauf teuer. `MIN_FREE_BYTES`
selbst wird **nicht** angefasst: es ist der Boden für den laufenden Betrieb, und der
Umbau addiert seinen Bedarf darauf, statt den Boden abzusenken. `index/repo.py` hat mit
`_index_bytes` bereits eine Größensummierung über `rglob`, die wiederverwendet werden
kann statt neu geschrieben zu werden.

**Was bei zu wenig Platz passiert:** Abbruch VOR dem Start, eine Logzeile mit der
fehlenden Bytezahl (nie mit einem Pfad, Hausregel), ein Banner, das die Zahl nennt, und
der benannte Rückfall. Der Rückfall ist kein neuer Code: `start_rebuild_on_drift` hebt
die Generation, das vorhandene Reindex-Banner nennt `occ findling:index --restart`, und
`reset_for_reindex` räumt die Verdikte. Auslösbar heißt: der Admin muss ihn
auslösen können, ohne eine Umgebungsvariable zu erfinden. Empfehlung: eine
Umgebungsvariable `FINDLING_REBUILD_FALLBACK=fullreindex`, Muster `_flag_from_environment`
aus `config.py`, damit die Entscheidung im Container bleibt und nicht in einer
PHP-Route landet, die Rechte braucht.

### Anti-Patterns

- **Den Umbau in die PHP-Migration legen.** Eine Migration läuft in `occ upgrade`, im
  Wartungsmodus, ohne angemeldeten Nutzer, und AppAPI startet den Container
  möglicherweise gerade neu. Ein ein- bis dreistündiger Lauf dort verwandelt ein
  App-Update in einen Ausfall. Der Klassenkommentar von
  `Version001200Date20260921000000.php:55-61` sagt es für den kleineren Fall bereits.
- **Das vorhandene Reindex-Banner wiederverwenden.** Es nennt
  `occ findling:index --restart` als Heilmittel. Während eines billigen Umbaus kostet
  dieser Rat den Nutzer 19 Stunden aus Versehen. Der Umbau braucht ein eigenes Banner mit
  eigenem Text: warten, Fortschritt, und der Satz, dass die Suche weiter antwortet.
- **`start_rebuild_on_drift` für den Umbau missbrauchen.** Die Funktion hebt die
  Generation, damit ein Crawl die Dateien wieder liest. Der Re-Analyse-Umbau liest gar
  keine Dateien. Beides zugleich wäre ein Crawl neben einem Umbau, also genau die
  doppelte Last, die der Umbau vermeiden soll.
- **`DEFAULT_LANGUAGES` auf sechs Einträge erweitern.** Die Konstante ist die
  Werkseinstellung und bleibt `("de", "en")` (E-17-3 Option a). Was sich ändert, ist der
  Filter in `_languages()`: er muss gegen die Schlüssel von `SNOWBALL_NAME` filtern statt
  gegen `DEFAULT_LANGUAGES`, sonst fällt jede neue Sprache stumm heraus. Das ist die eine
  Zeile, die den Unterschied zwischen "sechs Sprachen sind möglich" und "zwei Sprachen
  sind möglich, sechs Felder existieren" ausmacht.
- **`shutil.move` für den Tausch.** Bezeichnerverbot des Readonly-Gates.
- **Den Vektorbestand mitnehmen.** `vectors.db` bleibt unberührt: das Modell ist
  sprachneutral, die Chunkgrenzen sind Zeichenoffsets in `body_de`, und `body_de` trägt
  nach dem Umbau denselben Text an denselben Offsets. `embedding_mark` steht bewusst
  außerhalb von `expected_versions()` (`api/resources.py:144-149`) und bewegt sich nicht.

---

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---|---|---|---|
| Fortschritt eines langen Laufs | Zählertabelle in `state.db` | `_resume_cursor()` aus dem Zielindex | Ein zweiter Zustand neben dem Index kann von ihm abweichen; der Index kann von sich selbst nicht abweichen |
| Freier Platz | Zweiter `disk_usage`-Aufruf auf einem anderen Pfad | `IndexBatchWriter.free_bytes()` / `disk_is_tight()` | Zwei Pfade auf einem Volume sind zwei Antworten auf eine Frage; der Docstring von `free_bytes` sagt genau das |
| Indexgröße | Eigene `rglob`-Summe | `_index_bytes` in `store/repo.py` | Existiert, fängt `OSError` ab und loggt ohne Pfad |
| Vergleich der Marken | Eigene Gleichheitsschleife | `Store.version_mismatch` mit einer benannten dritten Ausnahme | Der Ort, an dem `index_version` und `tantivy_version` ihre Ausnahmen schon haben |
| Dokumentenaufbau | Feldnamen als Literale | Die Konstanten aus `index/schema.py` | Gemessen: `Document.from_dict` und `add_text` verschlucken einen unbekannten Namen spurlos |
| Löschen des alten Verzeichnisses | `delete_index()` | `retire_directory()` / `discard_directory()` | `delete` steht in `FORBIDDEN_IDENTIFIERS` |
| Lockstep-Migration | Neu erfinden | `Version001200Date20260921000000.php` kopieren, Datum und Klassenname anpassen | Zehn Zeilen, doppellaufsicher, fragt den Container nicht |
| Leseseiten-Neuöffnung | Prozessneustart erzwingen | Neue `reset_read_side()` in `api/resources.py` | Der Cache hängt am Pfad, und der Pfad ändert sich beim Tausch nicht |

**Kerneinsicht:** In diesem Modul ist fast jede Mechanik, die der Umbau braucht, schon
einmal gebaut worden, nur für einen anderen Anlass. Die Arbeit der Phase ist
Zusammensetzen und Benennen, nicht Erfinden. Die einzige wirklich neue Mechanik ist der
Verzeichnistausch, und der ist sechs Zeilen mit einer sehr strengen Reihenfolge.

---

## Runtime State Inventory

Phase 18 ist kein Rename, aber sie bewegt Laufzeitzustand, deshalb steht die Inventur hier.

| Kategorie | Gefunden | Handlung |
|---|---|---|
| Gespeicherte Daten | `$VOL/index` (tantivy, Schema 1 auf jeder Bestandsinstallation); `$VOL/state.db` Tabelle `meta` mit fünf Marken plus `rebuild_for`, `embedding_version`, `store_schema`, `created_at`, `instance_id`; `$VOL/vectors.db` | Index: Umbau. `meta`: ein neuer Schlüssel `languages`, außerhalb der Saat. `vectors.db`: unberührt, ausdrücklich |
| Lebende Dienstkonfiguration | Nextcloud `appconfig` Schlüssel `backend_app_version` (`ExAppService::KEY_BACKEND_VERSION`), liegt in der Nextcloud-Datenbank und nicht in git | Migration `Version001300Date...` verwirft ihn, Muster 1:1 aus 1.2.0 |
| OS-registrierter Zustand | Keiner. Der Container hält keinen Cron, keinen Dienst und keine Systemregistrierung; die Warteschlange liegt in Nextcloud. Geprüft per `grep` über `backend/src` nach `crontab`, `systemd`, `schtasks`: null Treffer | keine |
| Geheimnisse und Umgebungsvariablen | `FINDLING_LANGUAGES` (Name unverändert, Wertebereich wächst von `{de,en}` auf `{de,en,es,it,nl,pt}`); `FINDLING_OCR_LANGUAGES` (unverändert); möglicher neuer Schalter `FINDLING_REBUILD_FALLBACK` | Kein Schlüssel wird umbenannt, also kein SOPS- oder CI-Eingriff. Der erweiterte Wertebereich gehört in `docs/` und in den Store-Text |
| Build-Artefakte | Der laufende Container trägt das alte Image; das neue Image bringt dreizehn Felder mit. Kein egg-info, kein kompiliertes Artefakt mit Feldnamen | keine |
| Nicht in git liegende Zustände | `$VOL/instance.json` (Volume-Marker, `claim_the_volume`), `$VOL/dict/` (Wortliste) | unberührt; der Umbau darf keinen von beiden anfassen |

**Der eine Zustand, den die Inventur aufdeckt und den man leicht übersieht:**
`resources._OPEN` ist ein **Prozesszustand**, kein Plattenzustand, und er überlebt den
Verzeichnistausch. Er steht nirgends in einer Datei und taucht in keinem Backup auf,
weshalb ihn eine Datei-Inventur nie finden würde.

---

## Common Pitfalls

### Pitfall 1: Der Merker wird gesät und schweigt genau dann, wenn er reden soll

**Was schiefgeht:** `open_store(..., meta=expected)` schreibt den neuen Merker mit dem
erwarteten Wert, also meldet `version_mismatch` nie eine Abweichung, und der Umbau
startet nie.
**Warum es passiert:** Die Saat ist als Hilfe gebaut ("ein Container, dessen Marken
unbekannt sind, meldet ewig Drift") und wird hier zum Betrug.
**Vermeidung:** Pattern 4. Merker aus der Saat heraushalten, Fehlen als Teilmenge lesen.
**Warnzeichen:** Ein Test, der den Merker setzt und danach prüft, dass kein Drift
gemeldet wird, ist grün, ohne irgendetwas zu beweisen. Der aussagekräftige Test setzt
den Merker **nicht** und prüft beide Richtungen.

### Pitfall 2: Die Kette wird an die aktive Sprachmenge gehängt

**Was schiefgeht:** `open_index` registriert nur die Ketten der aktiven Sprachen; auf
jeder Instanz, die nicht alle sechs führt, wirft der erste `add_document` eine
`ValueError` "Error getting tokenizer for field: body_es", und der Indexer steht.
**Warum es passiert:** Es klingt sparsam, und es ist der Reflex aus "nur befüllen, was
aktiv ist". Die Befüllung hängt an der Sprachmenge, die **Registrierung nicht**.
**Vermeidung:** Alle sechs immer registrieren. Kosten gemessen: null, die Snowball-Ketten
sind in tantivy einkompiliert.
**Warnzeichen:** `if language in settings().languages: index.register_tokenizer(...)`.
[VERIFIED: eigene Messung 2026-09-24]

### Pitfall 3: Der Tausch gelingt auf Linux und bricht die Leseseite

**Was schiefgeht:** POSIX benennt über Inodes um, der Tausch gelingt also auch mit
offenen mmaps. Der zwischengespeicherte `ReadSide` hält danach ein Verzeichnis, das im
Dateisystem nicht mehr existiert, und antwortet aus dem Bestand von vorgestern, bis der
Container neu startet. Kein Fehler, kein Log, keine Zahl bewegt sich.
**Warum es passiert:** Der Cache ist unter `index_dir` abgelegt, und `index_dir` ist nach
dem Tausch derselbe Pfad, also greift der vorhandene Invalidierungszweig nicht.
**Vermeidung:** Ausdrückliche `reset_read_side()` vor dem Tausch, unter `_LOCK`, mit
`store.close()` und `vectors.close()` wie im vorhandenen Zweig (`api/resources.py:294`).
**Warnzeichen:** Auf Windows fällt derselbe Fehler laut auf die Nase (`PermissionError`,
WinError 5). Ein Test, der auf Windows übersprungen wird, verliert genau diesen
Wächter. Den Test also **nicht** skippen, sondern die Reihenfolge so bauen, dass er auf
beiden Systemen grün ist.

### Pitfall 4: Der Poller schreibt während des Umbaus weiter

**Was schiefgeht:** Ein Dokument, das nach dem Vorbeilauf des Cursors in den alten Index
geschrieben wird, ist nach dem Tausch verschwunden. Die Dokumentzahl stimmt, weil die
Zahl vom neuen Index kommt.
**Vermeidung:** `Poller.silence()` vor dem Lauf, in-flight-Durchgang auslaufen lassen,
Writer schließen, erst dann Band 1. `arm()` erst nach dem Tausch. Die Arbeit geht nicht
verloren, weil die Warteschlange in Nextcloud liegt.
**Warnzeichen:** `nextcloud.scheduled` steigt während des Umbaus, und niemand hat es
erklärt. In der CI-Strecke ist genau das die Zusicherung: der Wert darf sich bewegen und
muss danach wieder auf null sein.

### Pitfall 5: Die Sperrklinke wird grün gemacht statt umgedreht

**Was schiefgeht:** `backend/tests/test_upgrade_compatibility.py` hält
`GOLD_V1_0_AND_V1_1["schema_version"] = "1"` und sagt im Kopf ausdrücklich, dass ein
roter Lauf hier keine Reparatur ist, sondern eine Frage an den Owner. Der Sprung auf
`SCHEMA_VERSION = 2` macht `test_an_upgrade_from_1_0_x_or_1_1_x_would_not_trigger_a_reindex`
rot, und der bequeme Weg ist ein Edit.
**Vermeidung:** Die Freigabe liegt vor (E-17-1 bis E-17-4, alle Option a, 23.09.2026).
Der Test wird also **umgeschrieben mit Begründungsabsatz und Datum**, nicht angepasst.
Empfohlene Form nach dem Vorbild der Plan-17-07-Lösung: eine zweite Goldtabelle
`GOLD_V1_3` neben der alten, ein Test, der den Sprung als **genau eine Stufe** festhält
(`int(neu) - int(alt) == 1`), und `ALL_MARKS` bekommt den sechsten Eintrag.
**Warnzeichen:** Ein Diff, der eine Zeile in dieser Datei ändert, ohne einen Absatz
danebenzustellen.

### Pitfall 6: Die umgedrehte CI-Strecke ersetzt die bestehende

**Was schiefgeht:** "Store upgrade 5" wird entschärft, damit es mit dem bewegten
`schemaVersion` grün bleibt. Danach hat das Projekt für den einen Milestone, in dem der
Upgrade-Pfad wirklich gefährlich ist, keinen Upgrade-Wächter mehr.
**Vermeidung:** Ein **zweiter Schritt daneben**. Details unter "Die umgedrehte
Beweisstrecke".
**Warnzeichen:** Ein Diff an `deploy-harp.yml`, der Zeilen aus "Store upgrade 5" entfernt.

### Pitfall 7: Der Umbau hängt an einem Merker, der nur nach dem Upgrade greift

**Was schiefgeht:** Die Drift wird nur im Poller-Startpfad geprüft
(`worker/poller.py:324`). Ein Admin, der `FINDLING_LANGUAGES` ändert, startet den
Container neu, also greift das. Ein Admin, der die Variable ändert und **nicht**
neustartet, bekommt nichts, weil `settings()` mit `lru_cache` gecacht ist.
**Vermeidung:** Das ist akzeptabel und heutiges Verhalten für jede
`FINDLING_`-Variable; es muss aber in der Doku stehen ("Sprachwechsel wirkt nach dem
Neustart des Containers"), sonst ist es ein Supportfall.
**Warnzeichen:** Eine Adminseite, die die neue Sprache als aktiv zeigt, während der
Container sie nicht kennt.

### Pitfall 8: Die Katalogschlüssel werden nur in einer Sprache nachgezogen

**Was schiefgeht:** Das neue Banner, die Fortschrittszeile und die Platzwarnung bekommen
Schlüssel in `de.json`, und `de_DE`, `fr` bleiben zurück. Das Gate
`test_all_six_catalogues_carry_the_same_keys` fällt rot, was gut ist; die harte Zahl
`assert len(keys_of["de.json"]) == 199` fällt ebenfalls, was leicht als Fehler statt als
Aufforderung gelesen wird.
**Vermeidung:** Sechs Dateien im Gleichstand (`de.json`, `de.js`, `de_DE.json`,
`de_DE.js`, `fr.json`, `fr.js`), die Zahl in
`backend/tests/test_admin_ui_contract.py:1545` **beim Planstart aus der Datei zählen**
und mit der Zahl der neuen Schlüssel fortschreiben. Französisch nach dem Muster von
`docs/l10n-french.md` mit datiertem Vorbehalt.
[VERIFIED: 2026-09-24, `php/l10n/` trägt genau diese sechs Dateien, `de.json` hat 199
Übersetzungsschlüssel]

---

## Code Examples

### Ein Dokument aus dem alten Index in das neue Schema

```python
# Source: eigene Messung 2026-09-24 mit tantivy 0.26.2 und dem echten build_schema();
# die Feldgleichheit aller 3000 Dokumente wurde danach mit to_dict() geprueft und war True.
def _document_from(stored: Mapping[str, list[object]], languages: Sequence[str]) -> Document:
    """One document of the old index, rebuilt under the new schema.

    Every value comes back as a one element list, and every one of the eight stored
    fields is present even when it is the empty string: measured on 2026-09-24, a
    document written with ext="" and body_de="" comes back as {"ext": [""], ...}, so a
    missing key means a document this writer never produced and is a finding rather
    than a default.
    """
    document = Document()
    document.add_unsigned(FIELD_FILE_ID, int(stored[FIELD_FILE_ID][0]))
    document.add_unsigned(FIELD_STORAGE_ID, int(stored[FIELD_STORAGE_ID][0]))
    document.add_text(FIELD_NAME, str(stored[FIELD_NAME][0]))
    document.add_text(FIELD_TITLE, str(stored[FIELD_TITLE][0]))
    document.add_text(FIELD_PATH, str(stored[FIELD_PATH][0]))
    document.add_text(FIELD_EXT, str(stored[FIELD_EXT][0]))
    # body_de is the only stored copy of the text in the whole system, and body_en was
    # never stored because it carries the same string. So one read feeds every chain.
    body = str(stored[FIELD_BODY_DE][0])
    for code in languages:
        document.add_text(BODY_FIELD[code], body)
    document.add_integer(FIELD_MTIME, int(stored[FIELD_MTIME][0]))
    return document
```

Wichtig: `body_de` wird **immer** geschrieben, auch wenn `de` nicht aktiv ist, weil es
die einzige gespeicherte Textkopie ist und der Snippetgenerator daraus schneidet
(`index/search.py:875`). Das ist heute schon so (`index/writer.py:270`) und darf sich in
dieser Phase nicht ändern, sonst verliert eine Instanz mit
`FINDLING_LANGUAGES=es` alle Textausschnitte. Der Unterschied zwischen "Feld wird
gespeichert" und "Feld wird durch die deutsche Kette analysiert" ist die Stelle, an der
der nächste Leser stolpert, und er gehört als Absatz in `writer.py`.

### Die Vorprüfung

```python
# Source: Vorschlag, Zahlen aus der Messung 2026-09-24
@dataclass(frozen=True, slots=True)
class RebuildVerdict:
    """Why a rebuild may or may not start, with the numbers behind the answer."""
    may_start: bool
    reason: str
    needed_bytes: int
    free_bytes: int


def may_rebuild(index_dir: Path, new_language_count: int) -> RebuildVerdict:
    current = _index_bytes(index_dir)
    # 0.40 per newly filled chain. Measured on 2026-09-24: a filled chain costs 0.086
    # times the extracted text against a base index at 0.231, so 0.372; the figure here
    # sits above it on purpose, because an abort before the start costs a log line and
    # an abort in the middle costs the whole run.
    needed = int(current * (1 + 0.40 * new_language_count))
    free = shutil.disk_usage(index_dir).free
    floor = settings().min_free_bytes
    if free < needed + floor:
        return RebuildVerdict(False, "not enough room for two index directories", needed, free)
    return RebuildVerdict(True, "", needed, free)
```

### Der Tausch

```python
# Source: eigene Messung 2026-09-24. The order is the whole content of this function.
def swap_in(target: Path, live: Path) -> None:
    """Put the rebuilt directory in the place of the live one.

    Every handle on both directories has to be gone before the first rename. On Linux
    the rename would succeed with open mmaps, and that is the trap rather than the
    convenience: the reading side would then answer out of a directory that no longer
    has a name, silently and for as long as the process lives. Measured on Windows the
    same call refuses with PermissionError, WinError 5, which is why the suite catches
    the mistake on the development machine instead of in the field.

    Named swap_in and retire rather than delete or move: gate A of
    backend/tests/test_readonly_gate.py forbids both identifiers in every module of
    this package.
    """
    retired = live.with_name(live.name + ".retired")
    live.rename(retired)
    target.rename(live)
    shutil.rmtree(retired, ignore_errors=False)
```

### Die Startwarnung bei OCR-Mismatch

```python
# Source: Vorschlag. Die Codetabelle ist die Umkehrung der bestehenden Konstanten.
# config.py: SNOWBALL_NAME hat die sechs Zweibuchstabencodes,
# OCR_LANGUAGE_ALLOWLIST hat {deu, eng, fra, spa, ita, nld, por, dan, est},
# OCR_DEFAULT_LANGUAGES ist ("deu", "eng", "fra").
TESSERACT_NAME: Final = {"de": "deu", "en": "eng", "es": "spa", "it": "ita", "nl": "nld", "pt": "por"}


def warn_on_uncovered_languages() -> None:
    """One line at startup when a body language has no scanner behind it.

    The trap this closes has a name in the research, the Buchstabensalat-Falle: a scan
    in a language tesseract was not asked for comes out as plausible looking rubbish,
    the rubbish is indexed, and nothing anywhere says the document was never readable.
    A warning and never a refusal: an instance that indexes born digital Spanish files
    and scans nothing at all is perfectly healthy, and a container that refuses to start
    over an environment variable is the worse answer to a typo (the house rule of
    config.py).
    """
    ocr = set(settings().ocr_languages)
    missing = [code for code in settings().languages if TESSERACT_NAME[code] not in ocr]
    if missing:
        LOGGER.warning(
            "FINDLING_LANGUAGES carries %d language(s) the OCR languages do not cover; "
            "scanned pages in them are recognised with the wrong model and land in the index as noise",
            len(missing),
        )
```

Die Warnung nennt die **Anzahl** und nicht die Sprachnamen, weil die Hausregel dieses
Projekts lautet, dass eine Warnung den Variablennamen nennt und nie den Wert
(`config.py`, mehrfach). Für die Adminseite ist das anders: dort sind die Namen die
eigentliche Information, und sie kommen über `GET /status` als Liste.

### Die Diagnoseanzeige: aktiv gegen befüllt

```python
# Source: eigene Messung 2026-09-24. terms_with_prefix(field, "", limit=1) answers
# [] for a field whose term dictionary is empty and [(term, count)] otherwise.
def filled_languages(searcher: Searcher) -> tuple[str, ...]:
    return tuple(
        code for code in SNOWBALL_NAME if searcher.terms_with_prefix(BODY_FIELD[code], "", limit=1)
    )
```

Gemessen: `body_de -> [('hallo', 1), ('welt', 1)]`, `body_es -> [('hol', 1), ('mund', 1)]`
(gestemmt, also läuft die Kette), `body_it -> []`. Das ist die einzige Antwort auf
"befüllt", die aus dem Index selbst kommt statt aus einem Merker.

**Kostenvorbehalt:** `terms_with_prefix` mit leerem Präfix läuft nach der eigenen
Dokumentation über das gesamte Termwörterbuch des Feldes, und `limit` schneidet erst
danach zu. Auf einem Index mit 52.000 Dokumenten ist das nicht gemessen. Empfehlung:
diese Messung gehört in die **Diagnoseroute** (`api/diagnose.py`, auf Anfrage), nicht in
`GET /status`, das bei jedem Tastendruck der Unified Search mitläuft. Für `/status`
reicht der gespeicherte `languages`-Merker, der genau sagt, unter welcher Sprachmenge der
Index gebaut wurde. [ASSUMED für die Kosten; billig nachzumessen im Container und ein
Kandidat für Phase 22.]

---

## Die umgedrehte Beweisstrecke in deploy-harp.yml

### Wie parametrisiert statt kopiert wird

Der bestehende Block "Store upgrade 0" bis "Store upgrade 5" hängt heute an drei
Bedingungen, die in **jedem** Schritt einzeln stehen, weil die Datei keine
Block-Bedingung kennt (der Kommentar ab Zeile 2350 sagt das ausdrücklich):

```yaml
if: matrix.server-version == 'stable34' && matrix.runner == 'ubuntu-24.04' && env.RELEASE_TAG == ''
```

`UPGRADE_FROM_TAG` steht als `env` am Kopf der Datei (Zeile 100), heute auf `v1.1.0`.

**Empfehlung, und zwar ausdrücklich nicht die naheliegende.** Der Reflex ist, den ganzen
Block über eine Matrix zweimal zu fahren. Das geht hier nicht sauber, weil
`UPGRADE_FROM_TAG` eine `env`-Variable des Workflows ist und die Matrix bereits von
`server-version` und `runner` belegt ist; eine dritte Dimension würde die Anzahl der Äste
verdoppeln und den Kommentar "Warum exakt ein Bein" ungültig machen.

Der billigere Weg: **`UPGRADE_FROM_TAG` wandert von `v1.1.0` auf `v1.2.0`, und der
bestehende Block bleibt Zeile für Zeile stehen.** Daneben kommt ein neuer Schritt
"Store upgrade 6, der Umbau", der auf demselben Zustand aufsetzt, den "Store upgrade 5"
hinterlässt. Das ist die Form, die Pitfall 3 der Milestone-Research verlangt ("nicht
entschärft, sondern umgedreht, als eigener Schritt neben dem alten"), und sie kostet
keine zweite Registrierung: der Umbau wird auf der bereits aufgerüsteten Instanz
ausgelöst, indem `FINDLING_LANGUAGES` gesetzt und der Container neu gestartet wird.

Achtung auf die Konsequenz des Tagwechsels: **"Store upgrade 5" wird von v1.2.0 aus
gefahren und muss dabei grün bleiben.** Genau das ist der Beweis für Erfolgskriterium 1.
Ein Upgrade 1.2.0 auf 1.3.0 mit Werkseinstellung `de,en` bewegt keine der fünf Marken,
weil `schema_version` erst nach einem Umbau gestempelt wird und der Umbau ohne
Sprachwechsel gar nicht startet. Das ist die schärfste und unerwartetste Zusicherung der
ganzen Phase, und sie fällt kostenlos an, wenn der Merker nach Pattern 4 gebaut ist.

Zwei Stellen im bestehenden Block brauchen eine Anpassung wegen des Tagwechsels:

| Stelle | Heute | Nach dem Wechsel |
|---|---|---|
| Zeile 2479-2486, Vorprüfung "die Companion von UPGRADE_FROM_TAG erklärt den Navigationseintrag" | prüft, dass es eine 1.1.x-Release ist | bleibt gültig, 1.2.0 erklärt ihn auch; der Kommentar muss die Begründung nachziehen |
| Zusicherung 6, "die zwei Datumsgrenzen des Providers, und diese MUSS sich geändert haben" | `false` vor dem Upgrade, `true` danach | **fällt um**: die Datumsgrenzen sind seit Plan 13-06 in 1.2.0 drin, also `true` vor und `true` nach. Braucht einen neuen sichtbaren Unterschied zwischen 1.2.0 und 1.3.0, sonst geht der Beweis verloren, dass überhaupt etwas ausgetauscht wurde |

Der nächstliegende Ersatz für Zusicherung 6 ist der neue `languages`-Eintrag im Bericht
von `findling.tools.index_status`: er existiert in 1.2.0 nicht und in 1.3.0 schon, er
kostet keine Renderzeit und er wird über denselben `index_report()`-Helfer gelesen, den
die Probe ohnehin hat. Der Kommentarblock bei Zeile 2705, der die Kandidatenprüfung für
die heutige Zusicherung 6 dokumentiert, ist die Vorlage für die Begründung.

### Was der neue Schritt behauptet

Die Probe `snapshot()` (Zeile 2772) wird um zwei Felder erweitert, nicht neu geschrieben:
`marks.languages` und `container.rebuildState`. `index_status.py` bekommt den sechsten
Eintrag in `_VERSION_KEYS` und die Fortschrittszahlen.

| # | Zusicherung | Wie gemessen |
|---|---|---|
| 1 | `schemaVersion` hat sich bewegt, **und zwar um genau eine Stufe** | `[ "$(( now - was ))" = "1" ]` auf den beiden Werten aus der Probe |
| 2 | `marks.languages` steht nach dem Lauf auf der gesetzten Menge, normalisiert nach Schemafeldreihenfolge | `jq -r '.marks.languages'` gleich `de,en,es` und nicht `es,de,en` |
| 3 | Das Umbau-Banner **erschien** und ist danach **weg** | drei Momentaufnahmen: vor dem Neustart, mitten im Lauf, danach. Die mittlere ist die, die heute fehlt |
| 4 | Die Trefferzahlen für `Belehrung`, `Auszug`, `Erinnerung` sind nach dem Umbau **wieder identisch** mit den Werten davor | derselbe `term_hits`-Helfer, dieselben drei Begriffe, deren Einzigartigkeit `backend/tests/test_corpus_terms.py` festhält |
| 5 | Eine Suche mitten im Umbau antwortet **mit Treffern und nicht leer** | Kanarienabfrage gegen `term_hits Belehrung` während des Laufs; erwartet 1, niemals 0 und niemals HTTP != 200 |
| 6 | `container.docs` ist nach dem Umbau gleich | die Dokumentzahl kommt aus dem Index; ein verlorenes Dokument fällt hier auf |
| 7 | **Kein Nextcloud-Aufruf und kein OCR-Prozess** während des Umbaus | `nextcloud.scheduled` und `nextcloud.running` sind vor und nach dem Umbau gleich; im Containerlog keine Zeile des Extraktionspfads |
| 8 | Genau **eine** Zeile `built by different code` im Log, nicht null und nicht zwei | zwei hieße, der Neustart hat den Umbau neu angestoßen, also greift `REBUILD_MARK` nicht |
| 9 | `vectors.db` ist bytegleich | `docker exec ... sha256sum` vor und nach dem Umbau |

Zusicherung 9 ist in keiner der vier Recherchen benannt und ist die billigste Absicherung
des ganzen Schritts: sie beweist die Zusage "keine Neu-Einbettung" direkt am Artefakt
statt über ein abwesendes Logmuster.

### Die Sprachfälle auf Feldebene, ohne Fremdbestand

LEX-08 und Erfolgskriterium 5 verlangen sie in dieser Phase **auf Feldebene**, weil die
Frageseite erst in Phase 19 geöffnet wird. Konkret heißt das: ein Test baut einen Index
mit ausschließlich spanischen Dokumenten, schreibt sie nach `body_es`, und fragt mit
`parse_query_lenient(..., default_field_names=["body_es"])` direkt gegen das Feld, nicht
über `build_query`. "Ohne Fremdbestand" ist die Lehre aus v1.1
(`.planning/milestones/v1.1-phases/10-.../deferred-items.md:74`): bei 52.111 fremden
Dokumenten mit denselben Tokens trägt ein Rangbeweis nichts mehr, also läuft der
Sprachfall auf einem Index, der nur die Fälle der einen Sprache enthält.

**Warnung zu meiner eigenen Probe:** In `/tmp/probe18h.py` hat auch die alte Kette
`arrendamientos` gefunden, weil ich die englische Kette als Platzhalter für die deutsche
benutzt habe und Porter das Plural-s ebenfalls streicht. Ein Sprachfall muss deshalb ein
Wortpaar wählen, dessen Stamm **nur** der Snowball-Stemmer der Zielsprache zusammenführt.
Die dafür gemessene Tabelle liegt bereits vor:
`docs/measurements/2026-09-analyseketten/` und `docs/language-analyzers.md` aus Plan 17-06
(65 Formfamilien, 573 Paare). Die Fälle werden von dort genommen und nicht neu erfunden.

---

## State of the Art

| Alter Stand | Aktueller Stand | Seit wann | Bedeutung für Phase 18 |
|---|---|---|---|
| `tantivy 0.26.0`, Marke als Volltext verglichen | `tantivy 0.26.2`, nur die `index_format`-Hälfte entscheidet | 23.09.2026, Pläne 17-07 / 17-08 | Der Pin darf in dieser Phase **nicht** bewegt werden; `_index_format_matches` ist die Präzedenz für die dritte Ausnahme |
| `ValueError`-Text `Field 'body_es' is not defined` (Apostrophe, 0.26.0) | ``Field `body_es` is not defined`` (Backticks, 0.26.2) | 0.26.2 | Ein Test, der auf den Fehlertext matcht, muss den neuen Wortlaut treffen; besser auf `ValueError` und den Feldnamen matchen statt auf die Satzzeichen |
| `Index.is_compatible(path)` unbekannt | existiert in 0.26.2 und meldet ohne Wurf, ob ein Verzeichnis geöffnet werden kann | 0.26.x | Kandidat für die Vorprüfung: "alter Index lesbar?" ohne einen `Index.open`-Versuch mit Ausnahmebehandlung [VERIFIED: eigene Messung 2026-09-24, liefert `True` auf einem frischen Verzeichnis] |
| `Searcher.terms_with_prefix` unbekannt | existiert, `(field, prefix, filter_query=None, limit=None)` | 0.26.x | Die Antwort auf "welches Sprachfeld ist wirklich befüllt" |
| `Schema` introspektierbar? | nein, `dir(tantivy.Schema)` ist leer | 0.26.0 und 0.26.2 | Die Feldliste kann nicht aus dem offenen Index kommen; die Quelle bleibt der `schema_version`-Merker (bestätigt die Milestone-Research an der laufenden Fassung) |

**Überholt und nicht mehr übernehmen:**

- Die Aussage aus E-17-2, leere Felder kosteten "null Byte". Gemessen sind +0,40 %.
- Die Zusicherung 6 der Upgrade-Strecke (Datumsgrenzen). Sie stirbt am Tagwechsel auf
  v1.2.0 und braucht einen Nachfolger.

---

## Project Constraints (aus CLAUDE.md)

| Direktive | Konsequenz für diese Phase |
|---|---|
| Python-Qualitätsgates lokal grün **vor** dem Commit: `uv run python -m pytest -q`, `ruff check`, `ruff format --check`, `pyright`, `vulture` | Jeder Plan endet damit; ein roter Lauf ist ein Befund und wird gelesen, bevor etwas geändert wird |
| `INDEX_WORKERS = 1`, OCR-Spitze und Einbettungsspitze dürfen sich nie treffen | Der Umbau ruht den Indexierungspass; ein zweiter `IndexWriter` mit eigenem 50-MB-Heap läuft nie neben OCR |
| RAM-Budget 4 bis 8 GB, ARM-tauglich | Bandgröße so wählen, dass ein Band nicht mehr als eine Handvoll MB Text im Speicher hält; 500 Dokumente bei 15 kB sind 7,5 MB, unbedenklich |
| Code englisch, Umlaute **nie** in Code, Keywords, URLs, YAML | Bezeichner, Logtexte und Kommentare englisch und ASCII; Umlaute nur in deutscher Prosa wie diesem Dokument und in Katalogwerten |
| Keine Em-Dashes | gilt auch für Kommentare und Katalogtexte |
| README dreisprachig gepflegt (`README.md` DE, `README.en.md`, `README.fr.md`) | Wenn der Sprachausbau die READMEs berührt, dann alle drei |
| Kurze Produkttexte: Store und README als Faktenliste, höchstens eine Messzahl, Owner-Abnahme vor dem Release | betrifft Phase 23, aber die Formulierungen des Umbau-Banners werden hier geboren |
| Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Phase-Abschluss fixen | einplanen |
| Berechtigungs-Durchgriff strikt, keine Inhalte verlassen den Server | Der Umbau rührt weder `nc/` noch `extract/` an; das Readonly-Gate hält das fest |
| Owner-Regel: Launch-Härtung vor der Store-Abgabe | Phase 23 |

---

## Security Domain

### Anwendbare ASVS-Kategorien

| ASVS-Kategorie | Trifft zu | Standardkontrolle |
|---|---|---|
| V2 Authentication | nein | Der Umbau hat keine Route mit Nutzerkontext; der Auslöser ist eine Umgebungsvariable plus Neustart |
| V3 Session Management | nein | keine Sitzung beteiligt |
| V4 Access Control | ja, mittelbar | Der Index wird kopiert, nicht die ACL-Tabelle; `store/repo.py` bleibt unberührt, also wandert keine Berechtigung mit. Ein Test muss festhalten, dass der Umbau keine `acl`-Zeile anfasst |
| V5 Input Validation | ja | `FINDLING_LANGUAGES` geht über die geschlossene `LANGUAGE_ALLOWLIST` (Plan 17-02); ohne sie erreicht ein Tippfehler `Filter.stopword` und kostet in 0.26.0 einen Rust-Panic, in 0.26.2 eine `ValueError` |
| V6 Cryptography | nein | keine neue Kryptographie; `wordlist_hash` bleibt wie er ist |
| V7 Error Handling und Logging | ja | Logzeilen nennen nie einen Pfad und nie einen Nutzertext; die Hausregel `type(error).__name__` gilt auch im neuen Modul |
| V12 Files and Resources | ja | `rmtree` auf einem Verzeichnis unter `APP_PERSISTENT_STORAGE`; der Pfad kommt aus `findling.config` und nie aus einer Warteschlangenzeile |

### Bekannte Bedrohungsmuster für diesen Stack

| Muster | STRIDE | Standardabwehr |
|---|---|---|
| Ein `rmtree` mit einem Pfad, der nicht aus der Konfiguration kommt | Tampering / Denial | Der Zielpfad wird aus `settings().index_dir` abgeleitet und nie hereingereicht; ein Test hält fest, dass `retire_directory` nur unter dem Volume arbeitet |
| Ein Feldname, der aus der Umgebung in eine Query wandert | Injection | Der Feldname wird aus `SNOWBALL_NAME` gebildet, das eine geschlossene Abbildung ist; nie aus einer Zeichenkette zusammengesetzt |
| Sprachname als Subprozessargument (OCR) | Injection | `OCR_LANGUAGE_ALLOWLIST` schließt das seit Phase 3 (T-03-502); die neue Warnung liest die Liste, sie schreibt sie nicht |
| Ein halber Umbau, der sich als fertig stempelt | Repudiation | Der Stempel steht **nach** der Endprobe `num_docs(neu) == num_docs(alt)` und nach dem Tausch, nie davor |
| Ein Nutzertext im Log | Information Disclosure | Die Umbauzeilen zählen Dokumente und nennen nie ein Dokument |

**Der Hauptbefund dieser Domäne** ist kein klassisches Sicherheitsloch, sondern ein
Integritätsrisiko: ein Umbau, der abbricht, nachdem das Quellverzeichnis stillgelegt
wurde und bevor das Zielverzeichnis an seinem Platz ist, hinterlässt eine Installation
ohne Index. Der Tausch muss deshalb die kürzestmögliche Sequenz sein (zwei
Umbenennungen, dann erst das Löschen), und der Startpfad muss eine Instanz erkennen, die
ein `index.retired` oder ein `index.rebuild` und kein `index` vorfindet, und daraus das
Richtige machen. Dieser Aufräumpfad ist in keiner der vier Recherchen benannt und gehört
in einen eigenen Plan.

---

## Environment Availability

| Abhängigkeit | Gebraucht für | Verfügbar | Version | Rückfall |
|---|---|---|---|---|
| `tantivy` in `backend/.venv` | Alle Messungen und Tests | ja | `tantivy v0.26.2, index_format v7` | - |
| Python 3.13 via uv | Suite und Gates | ja | wie gepinnt | - |
| `/usr/share/dict/ngerman` (deutsche Wortliste) | Messung der **deutschen** Kettengeschwindigkeit | **nein** auf der Entwicklungsmaschine | - | `findling.index.analyzer.measure()` im Container oder auf der Box; die Bestandstests umgehen das über Fixtures |
| Docker / Test-Nextcloud | Ende-zu-Ende-Umbau | nicht geprüft in dieser Sitzung | - | Die CI-Strecke ist der eigentliche Beweis; lokal reichen Unittests auf echten Indizes |
| Korpus-Snapshot `snap-03f1d1d9ad9262704` | Echte Indexgröße und Umbaudauer | vorhanden, aber Box angehalten | - | Phase 22 (MESS-08); bis dahin bleiben die Zahlen als Schätzung markiert |

**Fehlende Abhängigkeiten ohne Rückfall:** keine. Die Phase ist lokal vollständig
entwickelbar und testbar; nur zwei Zahlen (echte Indexgröße, echte Umbaudauer) brauchen
die Box und sind ausdrücklich nach Phase 22 vertagt.

---

## Assumptions Log

| # | Behauptung | Abschnitt | Risiko, falls falsch |
|---|---|---|---|
| A1 | Der neue Index ist rund 1,39 GB groß, Spitze 2,17 GB | Pattern 6 | Der Platzgate-Faktor ist zu knapp oder zu großzügig; messbar in Phase 22, der Faktor ist eine Konstante und eine Zeile |
| A2 | Der Umbau dauert ein bis drei Stunden auf der Box | Zusammenfassung | Wenn er länger dauert, braucht das Banner eine ehrlichere Schätzung und der Store-Text eine Zeile; keine Architekturfolge |
| A3 | Der Faktor 0,40 je neu befüllter Sprache ist konservativ genug | Pattern 6 | Zu knapp bedeutet Abbruch mitten im Lauf; deshalb liegt er oberhalb des gemessenen 0,372 |
| A4 | `terms_with_prefix` mit leerem Präfix ist auf 52.000 Dokumenten bezahlbar | Code Examples | Falls nicht, wandert "befüllt" vom Termwörterbuch auf den gespeicherten Merker; eine Zeile |
| A5 | `Path.rename` gelingt auf Linux mit geschlossenen Handles | Pattern 3 | POSIX-Semantik, praktisch sicher; die CI-Strecke beweist es nebenbei |
| A6 | Keine Instanz im Feld trägt ein `languages`-Meta, das nicht von diesem Code stammt | Pattern 4 | Grundlage der Teilmengenregel; belegt dadurch, dass der Schlüssel bis 1.2.0 nirgends geschrieben wird |
| A7 | Ein `FINDLING_REBUILD_FALLBACK`-Schalter ist die richtige Form für den auslösbaren Rückfall | Pattern 6 | Alternative wäre ein `occ`-Unterbefehl, der aber die PHP-Hälfte berührt und eine Route braucht; Owner-Frage, falls der Planer sie stellen will |
| A8 | Der Ersatz für Zusicherung 6 ist der neue `languages`-Eintrag im Bericht | Beweisstrecke | Falls das zu dünn ist, braucht es einen anderen sichtbaren 1.2-gegen-1.3-Unterschied; der Kommentarblock bei Zeile 2705 zeigt, wie so eine Kandidatenprüfung dokumentiert wird |

---

## Open Questions (RESOLVED durch die Plaene: Q-Aufraeumpfad -> 18-08, Rueckfall-Ausloeser -> Umgebungsvariable in 18-06, Katalogzahl -> Zaehl-Auftrag in 18-10)

1. **Wer löst den Umbau aus, wenn der Admin die Variable setzt, ohne neu zu starten?**
   - Was feststeht: `settings()` ist `lru_cache`-gecacht, der Drift wird im
     Poller-Startpfad geprüft (`worker/poller.py:324`).
   - Was offen ist: ob eine Doku-Zeile reicht oder ob `PUT /enabled` die Prüfung
     wiederholen soll.
   - Empfehlung: Doku-Zeile. Eine zweite Prüfstelle wäre ein zweites Gedächtnis.

2. **Was passiert mit einem Container, der ein `index.rebuild` und kein `index` vorfindet?**
   - Was feststeht: Dieser Zustand ist zwischen den beiden Umbenennungen erreichbar, und
     das Zeitfenster ist Millisekunden.
   - Was offen ist: der Aufräumpfad beim Start. Kein Vorbild im Baum;
     `_raise_generation_for_lost_index` behandelt nur den umgekehrten Fall.
   - Empfehlung: eigener Plan, mit drei Fällen (nur `index`, `index` plus `index.rebuild`,
     nur `index.rebuild`, nur `index.retired`) und einem Test je Fall.

3. **Wird der Umbau auch bei reinem Abschalten einer Sprache gefahren?**
   - Was feststeht: Der Merker meldet die Abweichung in beide Richtungen (PITFALLS Nr. 6
     verlangt genau das).
   - Was offen ist: ob ein voller Umbau gerechtfertigt ist, nur um Terme einer nicht mehr
     gewünschten Sprache loszuwerden.
   - Empfehlung: ja, derselbe Weg, weil eine Sonderbehandlung ein zweiter Codepfad mit
     eigenen Fehlern wäre. Die Ersparnis ist real (der Index schrumpft), und der Lauf ist
     derselbe.

4. **Wie viele neue Katalogschlüssel braucht das Banner genau?**
   - Was feststeht: sechs Dateien, heute 199 Schlüssel, harte Zahl in
     `test_admin_ui_contract.py:1545`.
   - Was offen ist: die Zahl hängt am Wortlaut, und der Wortlaut hängt daran, ob
     Fortschritt und Platzwarnung getrennte Sätze sind.
   - Empfehlung: die Zahl beim Planstart aus der Datei zählen, nicht aus diesem Dokument
     übernehmen.

5. **Trägt die Startwarnung Sprachnamen oder nur eine Anzahl?**
   - Was feststeht: Die Hausregel von `config.py` nennt den Variablennamen, nie den Wert.
   - Was offen ist: ob diese Regel hier greift, denn der Sprachcode ist kein Nutzerinhalt.
   - Empfehlung: Anzahl im Log, Namen auf der Adminseite. So bleibt die Regel unverletzt
     und der Admin bekommt trotzdem die Information.

---

## Sources

### Primär (HIGH, eigene Messung am 2026-09-24 mit `tantivy 0.26.2` aus `backend/.venv`)

- Bandlauf, Wiederaufnahme und Feldparität über 3.000 Dokumente: 683 Dok/s, Parität `True`
- `to_dict()`-Verhalten für acht gespeicherte Felder, leere Zeichenketten, negative
  `mtime`, große `storage_id`
- `order_by_field` und `Order.Desc/Asc` auf dem `file_id`-Fast-Field
- `Query.range_query(schema, "file_id", FieldType.Unsigned, lo, hi, True, True)`
- Unbekanntes Feld beim Schreiben: stumm verschluckt
- `parse_query_lenient` mit schemafremdem Feld: `ValueError` mit Backticks
- Nicht registrierte Kette eines vorhandenen Textfeldes: `add_document` wirft, auch ohne
  dieses Feld im Dokument
- Verzeichnistausch mit offenen mmaps auf Windows: `PermissionError`, WinError 5
- Indexgröße 9 Felder gegen 13 leer gegen 13 befüllt: +0,40 % / +150 %
- `terms_with_prefix(field, "", limit=1)` als Füllstandsprobe
- `Index.is_compatible(path)` existiert und antwortet ohne Wurf

### Primär (HIGH, eigener Baum, gelesen am 2026-09-24)

- `backend/src/findling/index/{schema,open,writer,analyzer}.py`
- `backend/src/findling/store/repo.py` (`version_mismatch`, `_seed_meta`, `open_store`,
  `_generation_at_least`, `_index_format_matches`, `reset_for_reindex`,
  `verdicts_older_than`)
- `backend/src/findling/query/rewrite.py` (`DEFAULT_FIELDS`, `FIELD_BOOSTS`, `build_query`)
- `backend/src/findling/api/{search,resources,status,diagnose}.py`
- `backend/src/findling/{config,main}.py`, `backend/src/findling/worker/poller.py`
- `backend/src/findling/tools/index_status.py`
- `backend/tests/{test_upgrade_compatibility,test_readonly_gate,test_admin_ui_contract}.py`
- `.github/workflows/deploy-harp.yml` (Zeilen 80-115, 2310-2380, 2600-2880, 3256-3400)
- `php/lib/Migration/Version001200Date20260921000000.php`, `php/templates/admin.php`,
  `php/l10n/`

### Primär (HIGH, Planungsbestand)

- `.planning/phases/17-owner-tor-und-analyseketten/17-GRUNDSATZ-ENTSCHEID.md`
  (E-17-1 bis E-17-8, alle auf Option a, vollzogen 23.09.2026)
- `.planning/research/ARCHITECTURE.md` Teile A und B, `.planning/research/PITFALLS.md`
  Nr. 1, 2, 3, 6, 7, `.planning/research/SUMMARY.md`
- `.planning/ROADMAP.md` Phase 18, `.planning/REQUIREMENTS.md` LEX-02 bis LEX-08

### Sekundär (MEDIUM)

- `docs/performance.md` (785.308.851 B Indexgröße, 19 h 20 min Volllauf) , übernommen
  aus dem Baum, nicht selbst nachgemessen
- POSIX `rename(2)` / `unlink(2)`-Semantik für den Linux-Tausch , Standardwissen, in
  dieser Sitzung nicht auf Linux nachgemessen

### Tertiär (LOW, zur Validierung markiert)

- Die Hochrechnung der Umbaudauer auf ein bis drei Stunden. Meine Messung lief ohne die
  deutsche Kette, weil die Wortliste lokal fehlt. Phase 22 (MESS-08) liefert die Zahl.

---

## Metadata

**Konfidenz im Einzelnen:**

| Bereich | Stufe | Grund |
|---|---|---|
| Re-Analyse-Weg und Vollständigkeit | HIGH | Ende zu Ende gefahren, Feldparität aller Dokumente geprüft |
| Wiederaufnahme | HIGH | `order_by_field` auf dem Fast Field gemessen, Cursor vor und nach dem Lauf gelesen |
| Verzeichnistausch | HIGH für Windows (gemessen), MEDIUM für Linux (POSIX-Semantik, hier nicht ausführbar) |
| Sechster Merker | HIGH | Der Saatpfad ist Zeile für Zeile gelesen, alle vier Fälle durchgerechnet |
| Zwischenzustands-Beweis | HIGH | Beide Fehlerbilder auf 0.26.2 nachgemessen, nicht aus 0.26.0 übernommen |
| Plattenplatz | MEDIUM | Faktor gemessen, aber auf synthetischem Text; echte Zahl in Phase 22 |
| Laufzeit | LOW | Ohne die deutsche Kette gemessen |
| CI-Strecke | MEDIUM | Die Datei ist gelesen, der Umbau dort aber nie gefahren |
| Kataloge | HIGH | Sechs Dateien und die Zahl 199 am Baum gezählt |

**Recherchedatum:** 2026-09-24
**Gültig bis:** 2026-10-24 für die Codebefunde; die tantivy-Messungen gelten, solange
der Pin auf 0.26.2 steht, und werden mit jedem Pin-Sprung ungültig.
