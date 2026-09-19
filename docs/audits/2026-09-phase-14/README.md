---
phase: 14-modell-entladung-im-leerlauf
audited: 2026-09-19
tree: b044ae4651ab12b1a9900d7367bb5396e85e80d4
findings:
  critical: 0
  high: 0
  medium: 0
  low: 3
  total: 3
status: issues_found
fixed: [L-01]
still_open: [L-02, L-03]
---

# Phase 14: Security-, Bug- und Performance-Audit

**Umfang:** die elf Plaene 14-01 bis 14-11 dieser Phase, gelesen gegen den Baum
von Commit `b044ae4`. Dieser Bericht liegt nach der Owner-Regel vom 15.08.2026
vor dem Phasenabschluss und ist nach dem Muster von
`docs/audits/2026-09-phase-11/README.md` geschrieben.

Die Ueberschriften stehen ohne Umlaute, weil Pruefungen und Verweise auf sie
zeigen; der Fließtext benutzt echte Umlaute.

**Bilanz vorweg:** kein CRITICAL, kein HIGH, kein MEDIUM. Drei LOW-Befunde,
einer davon in diesem Lauf behoben (der fehlende V4-Paritaetsfall), zwei mit
Zieladresse weitergereicht. Die technische Hälfte der Phase ist durch; was
offen bleibt, ist der Owner-Entscheid am Checkpoint 14-12.

---

## 1. Gate-Protokoll

Der Gesamtlauf ist in einem Zug gegen denselben Baum gefahren, in der
Reihenfolge, in der `.github/workflows/python.yml` ihn fährt. Gelaufen am
19.09.2026 gegen `b044ae4`, auf der Entwicklungsmaschine (Windows, Python 3.13,
uv).

| Stufe | Befehl | Ausgang | Zahl |
|---|---|---|---|
| 1 | `uv run ruff check .` | gruen | All checks passed |
| 2 | `uv run ruff format --check .` | gruen | 123 Dateien bereits formatiert |
| 3 | `uv run pyright` | gruen | 0 errors, 0 warnings, 0 informations |
| 4 | `uv run vulture src tests --min-confidence 80` | gruen | keine Ausgabe |
| 5 | `uv run pytest -q` (VOLLE Suite) | gruen | **2262 bestanden, 15 uebersprungen**, 200,34 s |
| 6a | `uv run ruff check --config pyproject.toml ../scripts` | gruen | All checks passed |
| 6b | `uv run ruff format --config pyproject.toml --check ../scripts` | gruen | 10 Dateien bereits formatiert |

Die volle Suite und nicht `tests/unit`: die Lehre vom 17.09.2026 ist, dass ein
prozessweites Leck nur im vollen Lauf rot war.

### Die Stufen, die hier nur teilweise fahrbar sind

| Stufe | Lage | Ersatznachweis |
|---|---|---|
| PHP-Lint | kein `php` auf dem Pfad dieser Maschine | `docker run --rm -v ".../php:/php:ro" php:8.2-cli php -l` über die drei in 14-09 geänderten Dateien, also in derselben PHP-Version wie der CI-Job |
| PHPUnit | die Suite braucht eine Auscheckung von `nextcloud/server` | bleibt CI-Sache; die vier Text-Gates unten lesen denselben Quelltext lokal |
| Text-Gates | laufen in der vollen Suite mit | zusätzlich einzeln nachgefahren: **89 bestanden** über `test_php_acl_boundary.py`, `test_php_trust_boundary.py`, `test_admin_ui_contract.py`, `test_search_fields_lockstep.py` |

Der PHP-Syntaxnachweis im Wortlaut:

```
No syntax errors detected in /php/lib/Service/AdminViewService.php
No syntax errors detected in /php/templates/admin.php
No syntax errors detected in /php/tests/Unit/AdminViewServiceTest.php
```

### Skips: kein neuer, kein gelockertes Gate

**15 uebersprungene Fälle, und das ist die Zahl aus 13-13.** Der Stand der
Phase 13 waren 15 vorbestehende Umgebungs-Skips; 14-08 hat die Zahl bei 15
bestätigt, und dieser Lauf bestätigt sie ein drittes Mal. Kein Plan dieser
Phase hat einen Skip hinzugefügt.

Woher die 15 kommen, aus dem Baum gezählt und nicht behauptet:

| Ort | Bedingung | Art |
|---|---|---|
| `tests/test_embed_model.py` (`needs_model`) | kein Modellartefakt auf einer Entwicklungsmaschine | Umgebung |
| `tests/test_ocr.py` (`needs_engine`) | kein `tesseract` im Pfad | Umgebung |
| `tests/test_poller.py` (`needs_engine`) | dasselbe | Umgebung |
| `tests/test_sandbox.py` (`ONLY_POSIX` plus zwei Laufzeitpruefungen) | kein POSIX, zu wenige nutzbare Kerne, zu kleines Stack-Limit | Umgebung |
| `tests/test_measurement_scripts.py` (vier `skipif`) | keine POSIX-Shell auf dieser Maschine | Umgebung |
| `tests/conftest.py` | der Korpusgenerator liegt nicht, wo er erwartet wird | Umgebung |

Alle 15 hängen an der Maschine und keiner an einer Zusage. Damit ist T-14-44
erledigt: dieses Gruen ist nicht durch einen neuen Skip entstanden, und keine
Schwelle wurde gesenkt.

---

## 2. Security, ASVS V5, V7, V12

Die zutreffenden Kategorien dieser Phase stehen in `14-RESEARCH.md` Abschnitt
17. V2, V3 und V6 treffen nicht zu, und sie stehen hier trotzdem mit einer
Zeile, weil eine weggelassene Kategorie von einer geprüften nicht zu
unterscheiden ist: die Phase fügt keine Route hinzu, legt keine Sitzung an und
fasst kein kryptographisches Verfahren an.

### V5, Eingabepruefung: gehalten

Die eine neue Umgebungsvariable `FINDLING_EMBED_IDLE_RELEASE_SECONDS` geht
durch `_seconds_or_off_from_environment` in `backend/src/findling/config.py`,
den dritten Leser dieser Bauform. Der Bereich ist
`EMBED_IDLE_RELEASE_SECONDS_RANGE = (60, 86400)`, der Vorgabewert
`EMBED_IDLE_RELEASE_SECONDS = 0`.

Drei Eigenschaften, je mit der Zeile, die sie trägt:

- **Unsinn fällt auf den Default.** `int()` wirft, die Warnung nennt den
  **Namen** der Variablen und nie ihren Wert, und der Leser gibt den Default
  zurück. Dasselbe für einen Wert außerhalb des Bereichs.
- **Der Container stoppt nie.** Kein Pfad dieses Lesers erhebt eine Ausnahme.
  Das ist die Hausform dieses Moduls und die Gegenmaßnahme zu T-02-74: ein
  falsches Zeichen in einem Admin-Formular darf keinen Container erzeugen, der
  auf einer unbeaufsichtigten Maschine nicht mehr startet.
- **Die Null ist die Ausnahme vor dem Bereich.** Sie wird vor der
  Bereichspruefung beantwortet, damit der Boden von 60 s stehen bleiben kann und
  ein Admin, der die eine Zahl tippt, die "aus" bedeutet, nicht ungefragt das
  Merkmal bekommt.

**Urteil V5: gehalten.**

### V7, Fehlerbehandlung und Protokoll: gehalten

Die Entladung schreibt im ganzen Baum genau eine eigene Protokollzeile:

```
backend/src/findling/main.py:419
LOGGER.info("findling releases the embedding engine after an idle span")
```

Sie trägt keinen Suchtext, keinen Dateinamen, keine Trefferzahl und keine
Speichergröße. Die zweite Zeile des Pfades ist die des gescheiterten Takts,
und sie nennt ausschließlich `type(error).__name__`; die dritte ist die
Warnung einer libc ohne `malloc_trim`, die den Typnamen der `OSError` oder
`AttributeError` mitgibt und sonst nichts. `grep` über `LOGGER.` in
`embed/engine.py` liefert **null** Treffer: der Entladeweg der Engine schreibt
selbst gar nichts.

Das ist die Gegenmaßnahme zu T-02-14 und zugleich zum vierten Bedrohungsmuster
unten: die Messwerte gehören in das Messartefakt, nicht in das Container-Log.

**Urteil V7: gehalten.**

### V12, Dateien und Ressourcen: gehalten

`ctypes.CDLL` steht an genau einer Stelle des Baums:

```
backend/src/findling/embed/model.py:205
ctypes.CDLL("libc.so.6").malloc_trim(0)
```

Der Name ist ein Literal. Keine Einstellung, keine Umgebungsvariable und kein
Pfad aus einer Konfiguration erreicht diese Zeile; es gibt keine Variante mit
einem Pfadargument. Der Schutzschalter darum fängt `OSError` und
`AttributeError` und nicht alles, so dass eine libc ohne `malloc_trim` ein
unterstützter Container bleibt und ein anderer Fehler sichtbar wird.

**Urteil V12: gehalten.**

### V4, Zugriffskontrolle: mit Vorbehalt geprueft, Befund L-01 behoben

Das Research führt V4 als "nein, aber mit Vorbehalt": der ACL-Vorfilter und der
finale PHP-Recheck sind unberührt, aber die Runde unter `may_load=False` nimmt
einen zweiten Weg durch die Fusion, und ein Weg, den niemand gegangen ist, darf
nicht als gedeckt gelten (T-14-45).

**Befund L-01: der Paritätsfall fehlte.** Am Baum vor diesem Plan gab es keinen
Fall, der eine Suche unter `may_load=False` gegen den ACL-Vorfilter stellt. Der
D-19-Pfad war gedeckt, die Rechtefrage unter ihm nicht.

**Behoben in diesem Lauf**, nach der Lehre aus 13-13, dass ein Audit-Pfad ohne
Gate ein Gate bekommt. Vier neue Fälle in
`backend/tests/test_semantic_search.py`, Commit `b044ae4`:

| Fall | Was er hält |
|---|---|
| `test_a_degraded_round_gives_a_user_without_a_permission_row_nothing` | carol hat keine Rechtezeile; die leere Vektorliste macht die Fusion nicht zur Abkürzung am Vorfilter vorbei |
| `test_a_degraded_round_hands_out_exactly_the_permitted_documents` | alice bekommt genau die erlaubten Dokumente; ein Weg am Vorfilter vorbei wäre als gesperrte Kennung sichtbar und auf keine andere Weise |
| `test_the_degraded_round_asks_the_prefilter_as_often_as_the_ordinary_one` | genau eine Vorfilterfrage je Runde in beiden Stellungen, mit demselben Nutzer, und die entladene Runde trägt keinen Kandidaten hinein, den die volle nicht auch trägt |
| `test_the_php_recheck_knows_nothing_about_the_switch` | `may_load` steht in keiner PHP-Quelle; der finale Recheck kann auf einen Zustand nicht verzweigen, von dem er nie gehört hat |

Der letzte Fall ist die Begründung, warum die PHP-Hälfte keinen eigenen
Verhaltensfall braucht: dass der Recheck überhaupt und an genau einer Stelle
gestellt wird, hält `test_php_acl_boundary.py` seit Phase 9 (89 Fälle der vier
Text-Gates gruen, siehe Abschnitt 1).

**Urteil V4: geprüft, Befund behoben, Vorbehalt aufgelöst.**

### Die fuenf Bedrohungsmuster aus 14-RESEARCH.md 17

| Muster | STRIDE | Gegenmaßnahme | Wo sie steht |
|---|---|---|---|
| TTL sehr klein gesetzt, der Container lädt und entlädt pausenlos | Denial of Service | Bereichsgeprüfter Leser mit Untergrenze 60 s, `0` als einziger Sonderwert | `config.py::_seconds_or_off_from_environment`, `EMBED_IDLE_RELEASE_SECONDS_RANGE` |
| Suchlast gegen einen entladenen Container, jede Anfrage startet einen Warmlauf | Denial of Service | Single-Flight des Halters; der Warmlauf läuft unter dem Lock, und zehn Anfragen hintereinander heben `load_count()` um genau eins | `embed/engine.py::warm`, Fall aus 14-08 |
| `ctypes.CDLL` mit einem Pfad aus der Umgebung | Elevation of Privilege | Fester Name `libc.so.6`, Schutzschalter nur für `OSError` und `AttributeError` | `embed/model.py:205` |
| Speicherzahlen im Log verraten die Bestandsgröße | Information Disclosure | Eine Zeile "entladen" ohne Zahl; die Messwerte stehen im Messartefakt | `main.py:419`, `docs/measurements/2026-09-entladung-vorpruefung/` |
| Ein Gate, das sich selbst gruen nullt | Repudiation | Beide Zähler monoton, `engine.reset()` nullt keinen von beiden; die Rot-Fähigkeit ist per Mutation belegt (fünf Mutationsfälle) | `embed/model.py::load_count` und `unload_count`, 14-10 |

---

## 3. Bug-Durchgang

Die Pfade, die kein Gate von sich aus abdeckt, einzeln durchgesehen. Jeder
endet mit einem der drei Urteile.

### 3.1 Entladung waehrend eines Indexlaufs: durch Testfall gedeckt

Der Takt fragt `poller.busy` und lässt nicht los, solange ein Lauf arbeitet
(`main.py::_release_when_idle`). Das ist Pitfall 3 des Research: ein Loslassen
zwischen zwei Stapeln wäre das Nachladen Sekunden später, also aus einer
Ersparnis eine Kosten, ohne dass irgendwo etwas rot wird.
Deckung: `test_a_tick_with_a_busy_poller_releases_nothing`,
`test_a_tick_with_an_idle_poller_releases_both_holders`.

### 3.2 Entladung bei einem Container ohne Modell: durch Testfall gedeckt

`release_if_idle` liest den Halter über `_held` und nie über `shared_model`,
baut also unterwegs nichts. Ein leerer Halter beantwortet die Frage mit False,
und ein Verzeichnis ohne Artefakte meldet `missing` statt `cold`.
Deckung: `test_release_if_idle_leaves_an_empty_holder_alone_and_does_not_fill_it`,
`test_release_if_idle_does_nothing_for_an_engine_that_never_loaded`,
`test_a_directory_without_the_artifacts_is_reported_as_missing`.

### 3.3 Entladung bei abgeschalteter Semantik: durch Testfall gedeckt

Ein Container mit abgeschalteter zweiter Hälfte meldet `disabled` und nicht
`cold`, und `query_may_load` bleibt True, solange die Freigabe aus ist. Ein
Container ohne Semantik hat nichts, was ein Takt loslassen könnte, und der Takt
existiert bei ausgeschaltetem Schalter gar nicht erst: die dritte
Lifespan-Aufgabe wird nur angelegt, wo `embed_idle_release_seconds > 0` ist.
Deckung: `test_a_container_with_the_second_half_switched_off_says_so_and_not_cold`,
`test_query_may_load_stays_true_while_the_release_is_switched_off`,
`test_the_release_task_is_not_created_when_the_switch_is_off`.

### 3.4 Entladung waehrend eines laufenden Batches: durch Testfall gedeckt

Die zweite Hälfte von 3.1, eine Ebene tiefer: der Aktivitätszähler des Modells
hält eine Freigabe während eines laufenden Stapels auf, und der nächste Stapel
nach einer Freigabe liest die Artefakte wieder ein.
Deckung: `test_a_release_during_a_batch_leaves_the_engine_standing`,
`test_the_next_batch_after_a_release_reads_the_artifacts_again`,
`test_an_empty_batch_does_not_end_an_idle_span`.

### 3.5 libc ohne malloc_trim: durch Testfall gedeckt, und die Kosten sind beziffert

Der Schutzschalter fängt `OSError` und `AttributeError`, die Freigabe läuft
weiter, und die Warnung wird genau einmal je Prozess gesagt.
Deckung: `test_a_libc_without_malloc_trim_does_not_stop_a_release` und der Fall,
der die Reihenfolge `gc.collect()` vor `malloc_trim(0)` am Quelltext festhält.

**Was auf so einer libc ausfällt, steht als Zahl im Vorprüflauf:**
`gc.collect()` allein gibt zwischen 15,1 und 18,2 Prozent zurück,
`malloc_trim(0)` die übrigen 80,2 bis 84,9 Prozent. Der Schutzschalter ist also
kein toter Zweig, sondern die Stelle, an der vier Fünftel der Rückgabe ausfallen
würden. Das ist **erklärt und hingenommen**: eine libc ohne `malloc_trim` ist
ein unterstützter Container, der die Entladung nur schlechter bezahlt bekommt.

### 3.6 Halb aktualisiertes App-Paar: erklaert und hingenommen

Ein Container, der `unloaded` meldet, und eine Companion-App, die das Wort noch
nicht kennt: der Wert fällt durch `ENGINE_STATES` und landet im letzten Satz
der Seite, "This container does not report the state of the model yet". Das
liest sich wie ein kaputtes Backend und ist nichts als zwei Hälften auf
verschiedenen Ständen.

Bewusst nicht verhindert (T-14-36). Beide Hälften reisen als Paar (REL-02), der
Kommentar in `php/templates/admin.php` schreibt genau diesen Fall aus, und
`docs/admin-page.md` sagt es dem Admin, der sie einzeln aktualisiert hat. Der
Preis einer Verhinderung wäre eine Versionsweiche in der Vorlage, also eine
zweite Wahrheit über die Zustandsworte.

**Befund L-02 (weitergereicht):** die Gegenrichtung, eine Companion-App, die das
Wort kennt, und ein Container, der es nicht meldet, ist unauffällig und braucht
nichts. Sie steht hier nur, damit die Asymmetrie benannt ist.

---

## 4. Performance-Durchgang

Am Code und an den Zahlen.

### 4.1 Was ein Takt kostet

`RELEASE_TICK_SECONDS = 30.0`. Ein Durchgang im Ruhezustand ist: eine
Einstellungsabfrage aus dem Cache, ein `warm_wanted()`, eine Abfrage
`poller.busy`, ein `_held()` und **eine Uhrenlesung** (`time.monotonic()` in
`release_if_idle`). Kein Dateizugriff, keine Datenbankabfrage, kein Bau. Auf
einem Container, auf dem niemand sucht, ist das der ganze Preis des Merkmals.

### 4.2 gc.collect und malloc_trim laufen nie auf dem Event Loop

Jeder blockierende Aufruf des Takts geht durch `asyncio.to_thread`, und das ist
nicht nur behauptet: `test_every_blocking_call_of_the_tick_runs_in_a_worker_thread`
liest den Syntaxbaum von `_release_when_idle` und hält es fest. Die Freigabe
selbst läuft außerhalb des Halter-Locks, damit sie nicht jede nebenläufige
`shared_model`-Frage mitblockiert (T-14-16).

### 4.3 Die Nachwaerm-Aufgabe verzoegert keine Antwort

Der Route-Handler legt genau eine Aufgabe auf den Loop, auf dem er ohnehin
läuft, und wartet nicht auf sie. Gehalten von einem Gate am Syntaxbaum (genau
ein `create_task`-Aufrufknoten, kein `await` darauf, `_WARM_TASKS` als Referenz)
und von einem Zeitfall, der ohne `TestClient` läuft, weil dessen Portal je
Anfrage auf angestoßene Aufgaben wartet und damit die Länge des
Hintergrundlaufs melden würde statt die der Antwort.

### 4.4 Die Zahl steht im Bericht und nicht im Container-Log

Die Rückgabequote der Vorprüfung, 100,0 Prozent Median über fünf Zyklen auf
aarch64, steht in `docs/measurements/2026-09-entladung-vorpruefung/README.md`
mit Maschine, Abbilddigest und Rohdaten. Im Container-Log steht die Zeile ohne
Zahl (Abschnitt 2, V7).

### 4.5 Annahme A9 gegengeprueft

A9 behauptet, die vier Katalog-Gates und das Literal `6` seien die vollständige
Kostenfolge eines sechsten Worts, und verlangt einen Gesamtlauf als Gegenprobe.
**Gefahren, und A9 hält.** `vulture` und `pyright` sind beide ohne Ausgabe
beziehungsweise mit null Befunden durchgelaufen; keiner von beiden hat eine
weitere Stelle des sechsten Worts aufgedeckt.

Die Stellen, aus dem Baum gezählt und nicht aus der Annahme übernommen:

| Ort | Was dort steht |
|---|---|
| `backend/src/findling/embed/engine.py` | der Zustand selbst und die geschlossene Menge |
| `php/lib/Service/AdminViewService.php` | `ENGINE_STATES` mit sechs Worten |
| `php/templates/admin.php` | der Satz der serverseitigen Hälfte |
| `php/js/admin.js` | der Satz der Browser-Hälfte |
| `php/tests/Unit/AdminViewServiceTest.php` | der PHPUnit-Fall |
| `php/l10n/de.json`, `de.js`, `de_DE.json`, `de_DE.js`, `fr.json`, `fr.js` | je ein Wert mehr, sechs Dateien |
| `docs/admin-page.md`, `docs/embeddings.md`, `docs/runbook-messbox.md` | die drei Dokumente, die das Wort erklären |

**Befund L-03 (weitergereicht):** `docs/embeddings.md` nennt den Vorschlagswert
900 s weniger nachdrücklich als Schätzung, als `config.py` es tut. Das ist eine
Frage an den Owner (Punkt 7 des Checkpoints) und keine Codeänderung.

---

## 5. Die fuenf Erfolgskriterien der Phase, je mit Beleg

Die Kriterien stehen in `.planning/ROADMAP.md`, Phase 14.

| Nr. | Erfolgskriterium (Kurzform) | Beleg |
|---|---|---|
| 1 | Ein Vorprüflauf weist die RSS-Rückgabe auf Zielhardware aus, BEVOR gebaut wird | `docs/measurements/2026-09-entladung-vorpruefung/README.md`: E1 bis E4 alle gehalten, Median 100,0 Prozent auf aarch64, Erwartung im Commit `6387d2d` 29 Minuten vor den Rohdaten `64257e0` |
| 2 | Genau eine benannte Umgebungsvariable, TTL in Sekunden, 0 gleich aus, ab Werk aus | `config.py::_seconds_or_off_from_environment`, `EMBED_IDLE_RELEASE_SECONDS = 0`, Bereich (60, 86400); Abschnitt 2 dieses Berichts (V5) |
| 3 | Nach Ablauf der TTL sind beide Speicherhalter frei | `main.py::_release_when_idle` gibt Engine und Cutter je Takt frei, den Cutter nur hinter einer Freigabe, die wirklich geschah; Messgröße festgeschrieben in `docs/performance.md` (der Zahlenbeleg entsteht auf der Box der Phase 15, MEM-02) |
| 4 | Die erste Suche danach antwortet lexikalisch innerhalb 1,5 s und wärmt nach | Degradationsnaht aus 14-08, V4-Paritätsfälle dieses Berichts, `_WARM_TASKS` und der Zeitfall ohne `TestClient` |
| 5 | Die Admin-Seite zeigt den Zustand nach der neu formulierten one_load-Zusage, und das Gate prüft genau diese Zusage | Das sechste Wort `unloaded` in beiden Hälften und sechs Katalogen (14-09); die neu formulierte Zusage an drei Stellen gleichlautend und fünf Mutationsfälle statt drei (14-10) |

Erfolgskriterium 3 ist gebaut und getestet; seine **Messgröße** "Rückkehr zur
Grundlast nach einem Indexlauf" wird auf der Box der Phase 15 gemessen. MEM-02
bleibt aus genau diesem Grund offen, und `.planning/REQUIREMENTS.md` sagt es
seit 14-11.

---

## 6. Befundliste

| ID | Schwere | Befund | Stand |
|---|---|---|---|
| L-01 | LOW | Kein Paritätsfall, der eine Suche unter `may_load=False` gegen den ACL-Vorfilter stellt | **behoben**, vier Fälle in `test_semantic_search.py`, Commit `b044ae4` |
| L-02 | LOW | Die Gegenrichtung des halb aktualisierten App-Paars ist nirgends benannt | weitergereicht, Abschnitt 3.6; kein Handlungsbedarf, nur eine Asymmetrie |
| L-03 | LOW | `docs/embeddings.md` nennt 900 s weniger deutlich als Schätzung, als `config.py` es tut | weitergereicht an den Owner-Checkpoint 14-12, Punkt 7 |

Kein CRITICAL, kein HIGH, kein MEDIUM.

---

## 7. Was dieser Bericht nicht sagt

Er sagt nichts über das Verhalten an der laufenden Instanz. Die sieben
Sichtproben des Checkpoints 14-12 sind die andere Hälfte der Abnahme, und die
Freigabe der Phase liegt beim Owner und nicht in diesem Bericht.

Er nennt keine Bestandsgröße, keinen Pfad einer Instanz und keinen Dateinamen
aus einem Bestand (T-14-46). `docs/` ist öffentlich, und dieser Bericht ist vor
dem Commit darauf durchgesehen worden.
