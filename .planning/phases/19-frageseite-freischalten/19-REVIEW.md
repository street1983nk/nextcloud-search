---
phase: 19-frageseite-freischalten
reviewed: 2026-09-25
depth: deep
files_reviewed: 18
findings:
  high: 1
  medium: 5
  low: 7
  total: 13
status: issues_found
fixed: 2026-09-25
fix_status: all_addressed
fix_range: 6f35cbe..7f75456
---

# Phase 19: Security-, Bug- und Performance-Audit

**Geprueft:** 2026-09-25
**Spanne:** 982a39b..HEAD (41 Commits)
**Tiefe:** deep (Produktionscode vollstaendig, Aufrufketten ueber Modulgrenzen, CI-Strecke, neue Waechter)
**Ergebnis:** 1 HIGH, 5 MEDIUM, 7 LOW. Kein CRITICAL.
**Behebung:** 2026-09-25, Commits `6f35cbe..7f75456` (8 Stueck, je ein Befund
oder eine Befundgruppe). HIGH und alle fuenf MEDIUM behoben, sechs der sieben
LOW behoben, L-19-05 gemessen statt gegated (Begruendung beim Befund). Gates vor
jedem Commit gruen: ruff, ruff format, pyright (latest), vulture, volle Suite
(2875 passed, 15 skipped).

## Zusammenfassung

Das Sicherheitstor der Phase steht: die Feldliste haengt an der gespeicherten Marke, die
Gegenprobe am Verzeichnis faengt die Sicherungs-Mischung, der Vorgabewert von `plan` ist der
eingefrorene Bestandsplan, und keine der drei Aufrufstellen kann eine Ausnahme nach aussen
lassen. Die Messungen M-1 bis M-4 der Recherche sind im Code wiederzufinden, und die
CI-Wortpaare habe ich nachgerechnet: keines von ihnen wird von der deutschen oder der
englischen Kette zusammengefuehrt, der Beweis traegt also.

Der schwerste Befund ist kein Wurf und kein Leck, sondern eine fehlende Invalidierung. Der
Feldplan wird einmal je Oeffnung berechnet, aber die beiden Marken, aus denen er entsteht,
werden nach dem Oeffnen weiter geschrieben, und nichts wirft die Lesehaelfte danach weg. Auf
einer echten Installation kann der Umbau vollstaendig durchlaufen, und die neuen Sprachfelder
werden trotzdem bis zum naechsten Containerstart nicht durchsucht. Die CI sieht das nicht,
weil sie den Umbau dort ueber einen Containerneustart ordert.

Die Performance-Fragen des Auftrags sind sauber beantwortet: `field_plan_for` laeuft einmal je
Oeffnung, `doc_freq` kommt im ganzen Paket nur an dieser einen Stelle vor, und
`filled_languages` wird vom Anfragepfad nicht gerufen. Eine kleine neue Allokation je Anfrage
ist dazugekommen (L-19-03).

---

## HIGH

### H-19-01: Der Feldplan ueberlebt das Stempeln der Marken, die ihn bestimmen

**BEHOBEN** in `6f35cbe`. Beide Pfade. Der Fensterpfad wie vorgeschlagen:
`stamp_after_swap` steht jetzt im `try` des Tauschs und VOR
`let_read_side_open()`, das Fenster ist zu. Der Pollerpfad abweichend vom
Vorschlag und begruendet: `worker/poller.py` importiert `api.resources` nicht
(Schichtregel des Moduls, siehe Kopf von `index/rebuild.py`), deshalb nimmt
`Poller` einen `marks_stamped`-Callback, den die Lifespan mit
`resources.reset_read_side` fuellt, genau an der Naht, an der sie auch die
beiden Riegelhaelften in den Umbau reicht. Rot-vor-Fix gefahren: der
Reihenfolgetest in `test_index_rebuild.py` hielt die alte Reihenfolge als
Erwartung fest und fiel (`At index 3 diff: 'let_read_side_open' != 'stamp'`); er
liest jetzt zusaetzlich die Marken in dem Moment, in dem der Riegel faellt.
`test_read_side.py:441-449` ist umgedreht: die Aussage "einmal je Oeffnung, nie
je Anfrage" und die Invariante "ein Stempel hinter dem Riegel wird von der
naechsten Oeffnung gesehen" sind jetzt zwei Aussagen statt einer, die den Befund
als Erwartung hielt. Dazu zwei Pollerfaelle und ein Lifespan-Verdrahtungsfall.

**Kategorie:** bug (stille Wirkungslosigkeit der ganzen Phase)

**Dateien:**
- `backend/src/findling/index/rebuild.py:1235-1252`
- `backend/src/findling/index/open.py:326-331`
- `backend/src/findling/worker/poller.py:723`, `backend/src/findling/worker/poller.py:1953`
- `backend/src/findling/api/resources.py:551-558` (Berechnungsstelle)

**Beschreibung:**
`ReadSide.field_plan` entsteht in `read_side()` aus `store.read_meta()` und wird nur durch
`reset_read_side()` wieder fallen gelassen. Der Umbau ruft diese Invalidierung ueber
`hold_the_read_side_shut()` **vor** den beiden Umbenennungen und gibt sie im `finally` mit
`let_the_read_side_open()` sofort wieder frei. Die Marken, die den Plan bestimmen, werden aber
erst **danach** geschrieben:

```
drop_read_side()                  # rebuild.py:1235, Lesehaelfte verworfen, Riegel hoch
swap_in(...)                      # rebuild.py:1237
let_read_side_open()              # rebuild.py:1239, Riegel runter
(live / TARGET_MARK_FILE).unlink  # rebuild.py:1249-1250
stamp_after_swap(store, ...)      # rebuild.py:1251, hier erst werden schema_version
                                  #                  und languages geschrieben
```

Eine Suchanfrage, die zwischen Zeile 1239 und Zeile 1251 eintrifft, oeffnet die Lesehaelfte
neu, liest die **alten** Marken und berechnet `LEGACY_PLAN`. Danach passt `index_dir`
weiterhin zur Einstellung, also gibt `read_side()` den zwischengespeicherten Griff bis zum
Prozessende zurueck. Ergebnis: der Umbau ist durch, das Verzeichnis traegt dreizehn Felder,
die Marke sagt Schema 2 mit sechs Sprachen, und die Suche erreicht bis zum Neustart nur
`body_de` und `body_en`. Kein Log sagt es, kein Wert der Administrationsseite sagt es.

Das Fenster ist schmal, aber die Unified Search fragt je Tastendruck, und der Umbau ist genau
der Moment, in dem jemand auf der Suchseite steht und nachsieht.

Derselbe Klasse-Fehler steht ein zweites Mal und dort ohne jedes Zeitfenster: der Poller ruft
auf jedem leeren Durchlauf `_stamp_if_rebuilt()` (`poller.py:723`), das ueber
`stamp_after_rebuild` alle erwarteten Marken schreibt (`open.py:326-329`), darunter
`schema_version` und `languages`. Niemand verwirft danach die Lesehaelfte, und die ist zu
diesem Zeitpunkt praktisch immer offen.

Dass es so ist und nicht anders, haelt die Suite sogar als Erwartung fest:
`backend/tests/test_read_side.py:441-449` schreibt die Sprachmarke, ruft absichtlich kein
`reset_read_side()` und behauptet `again is first`. Der Kommentar begruendet das damit, dass
ein Plan, der sich ohne Reset bewegt, je Anfrage berechnet waere. Das ist richtig, beweist
aber nur, dass nicht gerechnet wird, nicht dass die Invalidierung existiert.

**Warum die CI es nicht faengt:** "Store upgrade 6" ordert den Umbau ueber einen Neubau des
Containers aus dessen eigenem `docker inspect` heraus
(`.github/workflows/deploy-harp.yml:4370-4400`). Der Prozess, der Zusicherung 10 beantwortet
("die spanische Frage findet genau ein Dokument"), ist deshalb fast immer ein frischer, der
die Marken erst nach dem Stempeln liest. Die Zusicherung ist gruen und sagt ueber diesen Pfad
nichts.

**Fixvorschlag:**

```python
# index/rebuild.py, statt der heutigen Reihenfolge
        drop_read_side()
        try:
            swapped = swap_in(target, live, should_stop)
            if not swapped:
                return RUN_STOPPED_EARLY
            with contextlib.suppress(OSError):
                (live / TARGET_MARK_FILE).unlink(missing_ok=True)
            # Gestempelt wird, WAEHREND der Riegel noch oben ist. Die erste
            # Anfrage danach oeffnet und liest die neuen Marken (H-19-01).
            stamp_after_swap(store, languages)
        finally:
            let_read_side_open()
        return REBUILD_THROUGH
```

Fuer den Poller genuegt die Invalidierung hinter dem Stempel, weil dort kein Riegel existiert:

```python
# worker/poller.py::_stamp_if_rebuilt
            stamped = stamp_after_rebuild(self._store_or_die(), marks)
            if stamped:
                # Die Marken haben sich bewegt, also ist der Feldplan einer
                # offenen Lesehaelfte von vorhin (H-19-01).
                resources.reset_read_side()
            return stamped
```

Dazu ein Fall in `test_read_side.py`, der die heutige Zusicherung umdreht: Marke schreiben,
den Stempelpfad laufen lassen, und danach muss `read_side()` einen Griff mit `body_es`
liefern, ohne dass der Test selbst `reset_read_side()` ruft.

---

## MEDIUM

### M-19-01: Die Gegenprobe prueft nicht den Plan, den sie herausgibt

**BEHOBEN** in `ec823b8`. `_probed` fragt jeden Namen, der zum Parser geht,
genau einmal (Feldliste, Gewichte, Dateinamen-Antwort), laesst die fehlenden
weg statt den ganzen Plan fallen zu lassen, und `field_plan_for` ist eine
Kaskade: berechneter Plan, dann Bestandsplan, beide geprobt, dann `EMPTY_PLAN`.
`build_query` bekommt die Kurzschlusszeile, weil eine leere Feldliste die eine
Eingabe ist, die den lenient-Parser werfen laesst. Abweichung vom Vorschlag:
der Entwurf im Bericht probt `body_es` zweimal (einmal aus `fields`, einmal aus
`boosts`) und schreibt dann zwei Warnzeilen fuer ein Feld; `asked` haelt das auf
eine.

**Kategorie:** security / bug (Verfuegbarkeit des Suchpfads)

**Datei:** `backend/src/findling/api/resources.py:418-433`

**Beschreibung:**
Die `doc_freq`-Sonde laeuft ueber `bodies`, also ausschliesslich ueber die Koerperfelder des
**berechneten** Plans. Nicht geprueft werden:

1. `FIELD_NAME` und `FIELD_TITLE`, die in Zeile 433 trotzdem in `fields` und in `boosts`
   landen.
2. Der Rueckfallplan selbst. Jeder der sechs `return LEGACY_PLAN`-Pfade gibt einen Plan
   heraus, der nie gegen das Verzeichnis gehalten wurde.

Nach Messung M-1 wirft `parse_query_lenient` fuer einen Namen, den das Schema nicht kennt, und
zwar aus `default_field_names` **und** aus `field_boosts`. Der Wurf landet in den
`except Exception` von `api/search.py:344`, `api/snippets.py:236` und `api/diagnose.py:229`
und erzeugt genau das Bild, gegen das die Phase gebaut ist: eine dauerhaft leere Suche mit
einer Warnzeile je Anfrage.

Heute ist kein Verzeichnis im Umlauf, dem `body_de`, `body_en`, `name` oder `title` fehlt,
also ist der Befund latent. Er wird scharf, sobald eine spaetere Schemastufe eines dieser vier
Felder fallen laesst oder umbenennt, denn dann ist der Rueckfall der garantierte Ausfall. Ein
Sicherheitstor mit ungepruefter Rueckfallseite ist kein Tor.

**Fixvorschlag:** Die Sonde auf den Plan legen, der wirklich herausgeht, und die Felder
entfernen, die werfen, statt auf einen ungeprueften zweiten Plan zu springen:

```python
def _probed(plan: FieldPlan, index: Index) -> FieldPlan | None:
    """Der Plan ohne die Felder, die das Verzeichnis nicht kennt, oder None."""
    searcher = index.searcher()
    kept: list[str] = []
    for field in (*plan.fields, *plan.boosts):
        if field in kept:
            continue
        try:
            searcher.doc_freq(field, "")
        except Exception as error:
            LOGGER.warning(
                "the field %s is not in the directory the marks describe, an %s",
                field,
                type(error).__name__,
            )
            continue
        kept.append(field)
    fields = tuple(name for name in plan.fields if name in kept)
    if not fields:
        return None
    return FieldPlan(
        fields=fields,
        boosts={name: weight for name, weight in plan.boosts.items() if name in kept},
        title_only=tuple(name for name in plan.title_only if name in kept),
    )
```

`field_plan_for` gibt dann `_probed(computed, index) or _probed(LEGACY_PLAN, index) or
FieldPlan((), {}, ())` zurueck. Fuer den leeren Plan braucht `build_query` eine
Kurzschlusszeile ("kein Feld, keine Anfrage"), die dieselbe leere Antwort liefert wie ein
Suchtext ohne Term, statt die Ausnahme zu provozieren.

### M-19-02: `BODY_BOOST` und `BODY_FIELD` stehen ohne Gleichschritt nebeneinander

**BEHOBEN** in `9f8c142`, Testseite wie vorgeschlagen: Mengengleichheit ueber
`BODY_BOOST`, `BODY_FIELD` und `SUPPORTED_LANGUAGES`, dazu eine Gegenprobe mit
ausgeduennter Gewichtstabelle gegen ein echtes Verzeichnis, und die
Rueckfallzeile im vorhandenen Mengenfall. Kein Produktionscode: die Abbildungen
sind bewusst geschlossen, gefehlt hat der Fall, der es merkt.

**Kategorie:** bug

**Dateien:** `backend/src/findling/query/rewrite.py:111`, `backend/src/findling/api/resources.py:414`

**Beschreibung:**
`boosts = {BODY_FIELD[code]: BODY_BOOST[code] for code in BODY_FIELD if code in active}` liest
zwei geschlossene Abbildungen, die in zwei Modulen stehen und durch nichts aneinander gehalten
werden. `SUPPORTED_LANGUAGES` (`config.py:148`) ist eine dritte Liste derselben Codes. Die
Phase hat mit `es`, `it`, `nl` und `pt` gerade vier Eintraege gleichzeitig in drei Listen
geschrieben, und die Roadmap nennt Franzoesisch fuer nach v1.3.

Faellt ein Code in `BODY_BOOST` aus, wirft die Zeile eine `KeyError`, die das aeussere
`except Exception` (Zeile 435) einsammelt. Ergebnis: **jede** Installation faellt still auf den
Bestandsplan zurueck, mit einer einzigen Warnzeile je Oeffnung, die "an KeyError" sagt und
sonst nichts.

Die Suite faengt das nur halb. `test_every_language_set_weighs_exactly_the_fields_it_searches`
(`test_query_fields_plan.py:290-306`) behauptet `set(plan.boosts) == set(plan.fields)`, und
diese Aussage gilt fuer `LEGACY_PLAN` genauso; der Fall bliebe gruen. Rot wuerde allein
`test_language_cases_query_path.py:123`, wo der Testaufbau selbst ueber `BODY_BOOST[code]`
geht, und zwar mit einer `KeyError` statt mit einer Aussage.

**Fixvorschlag:** Einen Gleichschrittfall neben die Abbildungen legen und die vorhandene
Mengenaussage schaerfen:

```python
def test_every_body_field_has_exactly_one_weight() -> None:
    assert set(BODY_BOOST) == set(BODY_FIELD) == set(SUPPORTED_LANGUAGES)

# und in test_query_fields_plan.py, damit ein stiller Rueckfall auffaellt:
    if {"es", "it", "nl", "pt"} & set(languages.split(",")):
        assert plan != LEGACY_PLAN, "the plan fell back instead of opening the field list"
```

### M-19-03: Der Rueckfall auf den Bestandsplan ist von aussen unsichtbar

**BEHOBEN** in `315eaf0`. `languagesSearched` steht neben `languagesActive` und
`languagesFilled` und kommt aus dem Feldplan; `plan_falls_short` misst beim
Oeffnen, ob der Plan weniger erreicht als die Marken versprechen, haengt als
`ReadSide.plan_is_short` daneben und ist die fuenfte Ursache in `degraded()`.
Bewusst NICHT mitgezogen: die PHP-Seite. Der Fixvorschlag des Berichts verlangt
sie nicht, die Phase fasst `php/` nicht an, und ein dritter Platzhalter in einem
in drei Sprachen uebersetzten Satz (plus l10n-Paare und PHP-Baumhash) gehoert in
den Plan, der die Seite besitzt. Der Wert reist in der Antwort mit, die die
Seite ohnehin holt, und der Merker ist ueber `degraded` schon heute sichtbar.

**Kategorie:** bug (Betreibbarkeit)

**Dateien:** `backend/src/findling/api/status.py:299-300`,
`backend/src/findling/api/status.py:405`, `backend/src/findling/api/resources.py:426-431`

**Beschreibung:**
Faellt `field_plan_for` zurueck, meldet die Administrationsseite unveraendert
`languagesActive` aus der Marke beziehungsweise aus den Einstellungen und `languagesFilled`
aus dem echten Termwoerterbuch. Beide sagen "sechs Sprachen sind aktiv und gefuellt", waehrend
die Suche nur `body_de` und `body_en` erreicht. Der einzige Hinweis ist eine Warnzeile im
Containerlog, die genau einmal je Oeffnung faellt und damit im Rauschen des Starts steht.

Die Uebersicht ist die Seite, auf die ein Admin schaut, wenn Treffer fehlen. Sie beantwortet
die Frage "welche Felder erreicht eine Frage gerade" heute nicht, obwohl der Wert seit dieser
Phase als eingefrorener Wert auf `ReadSide` liegt und kostenlos ablesbar ist.

**Fixvorschlag:** Einen dritten Sprachwert neben die beiden vorhandenen legen, aus dem Plan
statt aus den Einstellungen:

```python
# api/status.py
    languagesSearched: str = ""
...
    side = resources.read_side()
    plan = side.field_plan if side is not None else LEGACY_PLAN
    languagesSearched = ",".join(
        code for code, field in BODY_FIELD.items() if field in plan.fields
    )
```

Zusaetzlich gehoert der Rueckfall in `degraded()`: eine Instanz, deren Frage weniger Felder
erreicht, als ihre Marke verspricht, antwortet nachweislich unvollstaendig, und genau dafuer
ist der Merker da.

### M-19-04: Das aeussere `except Exception` macht Programmierfehler zur Betriebsmeldung

**BEHOBEN** in `f33799c`, wie vorgeschlagen: der aeussere Fang sagt `error`
statt `warning` und einen eigenen Satz ("in this build"), die erwartete
Sondenausnahme wird eine Ebene tiefer pro Feld gefangen und benannt. Verhalten
unveraendert, die Unterscheidung ist les- und alarmierbar.

**Kategorie:** bug (Diagnostizierbarkeit)

**Datei:** `backend/src/findling/api/resources.py:434-440`

**Beschreibung:**
Der aeussere Fang steht um die ganze Funktion und schreibt fuer jede Ursache dieselbe
Warnzeile "the field plan could not be computed". Dahinter stehen zwei voellig verschiedene
Sachverhalte: eine echte Abweichung zwischen `state.db` und Verzeichnis, und ein Fehler im
eigenen Code (`KeyError` aus M-19-02, `AttributeError` nach einer Umbenennung, `TypeError`
nach einer geaenderten Signatur). Der erste ist eine Meldung an den Betreiber, der zweite
gehoert in die Testsuite, und beide sehen im Log identisch aus.

Dass der Fang breit ist, ist richtig und im Docstring gut begruendet. Falsch ist nur, dass er
nicht unterscheidet.

**Fixvorschlag:** Die erwartete Sondenausnahme schmal fangen (das tut die innere Schleife
bereits) und die aeussere Zeile auf `LOGGER.error` mit eigener Formulierung heben, die "das
ist ein Fehler dieses Builds" sagt statt "die Marken passen nicht". Verhalten bleibt gleich,
die Unterscheidung wird les- und alarmierbar.

### M-19-05: `stamp_after_rebuild` schreibt Marken, fuer die es nicht zustaendig ist

**BEHOBEN** in `252ada4`, wie vorgeschlagen: `_MARKS_OF_A_DIRECTORY` haelt die
drei Marken, die dieser Stempel nicht schreibt, mit je einer Begruendung
daneben. Die Aufrufstellen wurden vorher geprueft: `_aged_state` und
`_drifted_store` saeen Schema und Sprachen passend und driften nur ueber den
Wortlisten-Digest, `_seed_meta` laesst die Sprachmarke ohnehin aus und
`_languages_are_legacy` liest ihre Abwesenheit als Bestand. `test_lifecycle`,
`test_poller` und `test_index_open` bleiben gruen ohne Nacharbeit; ein neuer
Fall haelt die beiden Marken gegen den Stempel fest.

**Kategorie:** bug

**Datei:** `backend/src/findling/index/open.py:326-330`

**Beschreibung:**
`stamp_after_rebuild` schreibt **alle** erwarteten Marken mit genau einer Ausnahme
(`index_version`). Seit Phase 19 sind zwei davon sicherheitsrelevant: `schema_version` ist das
Tor der Feldliste, `languages` bestimmt sie. Beide beschreiben ein Verzeichnis, dieser Stempel
laeuft aber nach einem Neudurchlauf der Bestaende **im vorhandenen Verzeichnis**, nicht nach
einem Verzeichnisumbau. Genau darum hat `stamp_after_swap` (`index/rebuild.py:871-915`) die
beiden Marken als eigene, dritte Funktion bekommen; der dortige Docstring nennt "zwei Stempler
unter einem Namen" als klassischen Weg, auf dem ein halber Index sich fuer vollstaendig
erklaert (T-18-07-03).

Der Pfad ist heute schmal, weil eine Schema- oder Sprachabweichung den Verzeichnisumbau
ausloest und der Poller waehrenddessen steht. Er ist nicht zu: ein Umbau, der mit
`RUN_INCOMPLETE` oder `RUN_STOPPED_EARLY` endet, gibt den Poller wieder frei, und der naechste
leere Durchlauf stempelt bei leerer Arbeitsliste beide Marken als aktuell. Danach ist das
Banner unten, die Marke verspricht Felder, die das Verzeichnis nicht traegt, und allein die
`doc_freq`-Sonde steht noch dazwischen.

**Fixvorschlag:** Die beiden Marken genauso ueberspringen wie `index_version`, mit einer Zeile
Begruendung daneben:

```python
# Die zwei Marken, die ein Verzeichnis beschreiben, und nicht diesen Durchlauf.
# Geschrieben werden sie allein von index.rebuild.stamp_after_swap, hinter dem
# Verzeichnistausch, denn nur dort ist wahr, was sie behaupten.
_DIRECTORY_MARKS: Final = frozenset({SCHEMA_MARK, LANGUAGES_MARK, _LOCAL_GENERATION})
...
    for key, value in expected.items():
        if key in _DIRECTORY_MARKS:
            continue
        store.write_meta(key, value)
```

---

## LOW

### L-19-01: Die Sprachmarke wird ohne `strip` und ohne `lower` gelesen

**BEHOBEN** in `62f3d4a`, wie vorgeschlagen, mit vier parametrisierten Faellen.

**Kategorie:** bug
**Datei:** `backend/src/findling/api/resources.py:403-404`

`{code for code in stored.split(",") if code}` liest `"de, en"` als `{"de", " en"}` und
`"DE,EN"` als `{"DE", "EN"}`. Beim ersten faellt eine ganze Sprache lautlos aus der Feldliste,
beim zweiten bleibt nichts uebrig und der Rueckfall greift. Der Schreibweg
(`config.py::_languages` ueber `SUPPORTED_LANGUAGES`) erzeugt das heute nicht, aber diese
Funktion liest eine Datei, die aus einer Sicherung, aus einer aelteren Ausgabe oder aus einer
Hand kommen kann, und behandelt jede andere Unschaerfe ausdruecklich tolerant.

**Fix:** `active = {code.strip().lower() for code in stored.split(",") if code.strip()} or set(LEGACY_LANGUAGES)`

### L-19-02: `FieldPlan` ist eingefroren, `boosts` ist es nicht

**BEHOBEN** in `62f3d4a`: `MappingProxyType` in `LEGACY_PLAN`, in `EMPTY_PLAN`
und in jedem berechneten Plan; die Annotation war bereits `Mapping`, also aendert
sich kein Aufrufer. Der Hash-Punkt bleibt bestehen (auch ein Proxy hasht nicht)
und steht jetzt als bekannte Grenze im Docstring.

**Kategorie:** security (Haertung) / quality
**Dateien:** `backend/src/findling/query/rewrite.py:92`, `backend/src/findling/query/rewrite.py:128-133`

`frozen=True` schuetzt die Zuweisung des Feldes, nicht dessen Inhalt. `LEGACY_PLAN.boosts` ist
ein gewoehnliches, prozessweit erreichbares `dict`. Ein einziges
`LEGACY_PLAN.boosts["body_es"] = 0.6` irgendwo im Prozess macht den Rueckfallplan zu genau dem
Wurf, gegen den er gebaut ist, auf jeder Bestandsinstallation und dauerhaft. Das ist der Wert,
den die Phase ausdruecklich als Fail-Closed-Linie fuehrt; er sollte auch wirklich
unveraenderlich sein.

Nebenbei: `frozen=True` erzeugt ein `__hash__`, das wegen des `dict` bei jedem Aufruf
`TypeError` wirft. Heute hasht niemand einen Plan, aber ein `functools.cache` ueber eine
Funktion mit `plan`-Parameter waere eine unangenehme Ueberraschung.

**Fix:** `boosts` als `MappingProxyType` anlegen, in `LEGACY_PLAN` und im Aufbau von
`field_plan_for`. `fields` und `title_only` sind bereits Tupel und brauchen nichts.

### L-19-03: Zwei neue Allokationen je Anfrage im heissen Pfad

**BEWUSST ABGELEHNT**, dokumentiert in `62f3d4a` neben der Zeile, was der
Bericht als zweite Moeglichkeit ausdruecklich anbietet. Acht Eintraege gegen
einen mit 2,26 us gemessenen Parser, beide Werte gehen in eine native Erweiterung,
die behalten darf, was sie bekommt, und die Alternative legt eine zweite
Darstellung der Feldliste auf einen Wert, dessen ganzer Sinn es ist, EINE zu sein.

**Kategorie:** performance
**Datei:** `backend/src/findling/query/rewrite.py:621-622`

Vor der Phase wurden die Modulkonstanten direkt weitergereicht
(`default_field_names=DEFAULT_FIELDS`, `field_boosts=FIELD_BOOSTS`). Jetzt steht dort
`list(plan.title_only) if title_only else list(plan.fields)` und `dict(plan.boosts)`: eine
Liste und ein Woerterbuch je Anfrage, beide hoechstens acht Eintraege gross. Gegen die
gemessenen 2,26 us des Parsers ist das Rauschen, und die Kopie schuetzt den Modulwert vor
einer Bibliothek, die ihn behalten koennte (siehe L-19-02).

Es ist trotzdem eine Regression gegenueber dem Stand davor und genau die Frage, die der
Auftrag unter "keine neuen Allokationen im heissen Suchpfad" stellt, also steht sie hier.

**Fix (optional):** Die beiden fertigen Formen einmal auf dem eingefrorenen Wert ablegen, als
`field(init=False)`, im `__post_init__` ueber `object.__setattr__` gesetzt, damit die Anfrage
nur noch liest. Alternativ bewusst ablehnen und den Grund neben die Zeile schreiben.

### L-19-04: Der Docstring von `build_query` verspricht mehr, als M-1 haelt

**BEHOBEN** in `62f3d4a`, wie vorgeschlagen.

**Kategorie:** quality
**Datei:** `backend/src/findling/query/rewrite.py:551-556`

Dort steht: "Never raises on user input. A stray quotation mark, a regular expression, **a
field that does not exist**: all of them come back as an entry in `errors`". Fuer die
Nutzereingabe stimmt das und ist gemessen (M-1, vierte Zeile). Fuer die vom Code gestellte
Feldliste stimmt es seit derselben Messung nicht: `default_field_names` und `field_boosts`
werfen beide. Der Satz steht ausgerechnet ueber dem Parameter `plan`, dessen ganze Begruendung
dieser Wurf ist, und liest sich damit als Entwarnung fuer genau dieses Risiko.

**Fix:** Den Satz auf die Eingabe einschraenken und den zweiten Fall danebenstellen: "a field
that does not exist **in the typed line**: an entry in `errors`. A field that does not exist
in `plan`: a `ValueError` out of the parser, which is why `plan` is computed against the
directory and never composed here (M-1)."

### L-19-05: Der Sprachbeweis wartet nicht, bis seine vier Dokumente aus dem Index sind

**TEILWEISE BEHOBEN** in `7f75456`: gemessen und gemeldet, kein hartes Gate.
Begruendung. Erstens gibt es `term_hits` in diesem Schritt nicht, die Funktion
steht in "Store upgrade" und Shellfunktionen ueberleben keinen Schrittwechsel.
Zweitens, und das ist der Grund: nach dem DELETE treibt nichts mehr die
Warteschlange, die Loeschung wird erst von einer Cron-Runde ausgetragen, und
niemand hat je gemessen, wie lange das auf dieser Instanz dauert. Ein hartes
Gate auf eine ungemessene Zeit kann die ganze Strecke rot faerben, ohne dass
etwas kaputt ist. Der eingebaute Block treibt die Cron-Runde, fragt die vier
Fragen, sagt nach wie vielen Runden die Dokumente draussen sind und warnt sonst
mit den Sprachen, die noch antworten. Sobald ein Lauf die Zahl gedruckt hat, ist
das Budget gemessen und der Block kann das Gate werden.

**Kategorie:** bug (CI-Verlaesslichkeit)
**Datei:** `.github/workflows/deploy-harp.yml:1067-1089`

Der Schritt loescht die vier Dateien ueber WebDAV und prueft nur den HTTP-Status. Der
Kommentar begruendet die Loeschung damit, dass spaetere Schritte auf dem Bestand messen, auf
dem sie gemessen wurden: "Store upgrade 2" behauptet fuer `Belehrung`, `Auszug` und
`Erinnerung` je genau eine Datei, und diese Suche ist hybrid.

Die Loeschung in Nextcloud und das Verschwinden aus dem Findling-Index sind zwei Ereignisse.
Dazwischen liegen der Loeschauftrag ueber den Ereignishoerer oder der naechste Abgleich. Der
Schritt wartet auf keins von beiden. Die Begruendung traegt also nur, solange die Zustellung
schnell genug ist, und das ist genau die Art Annahme, die diese Datei sonst ueberall misst,
statt sie zu setzen.

**Fix:** Hinter das DELETE eine kurze Schleife mit eigenem, kleinem Budget, die je Sprache
fragt, bis `.ocs.data.entries | length == 0` ist, und mit klarer Meldung abbricht, statt den
spaeteren Schritt raten zu lassen. Die Zaehlfunktion dafuer gibt es bereits (`term_hits`,
Zeile 3258).

### L-19-06: Das Anwendungskennwort der CI wird nicht maskiert

**BEHOBEN** in `7f75456`, wie vorgeschlagen, an beiden Stellen
(`language-apppw.txt` und `rebuild-apppw.txt`).

**Kategorie:** security (CI)
**Datei:** `.github/workflows/deploy-harp.yml:838-852`

`apppw` wird aus der `occ`-Ausgabe beziehungsweise aus `getapppassword` gezogen und danach in
`curl -u "admin:${apppw}"` benutzt. Ausgegeben wird nur die Laenge, das ist richtig. Zwei
Kleinigkeiten fehlen trotzdem:

1. Kein `::add-mask::`. Ein spaeterer `set -x`, eine Fehlermeldung von `curl` oder ein Lauf
   mit `ACTIONS_STEP_DEBUG` wuerde den Wert ungeschwaerzt ins Protokoll schreiben.
2. `${RUNNER_TEMP}/language-apppw.txt` bleibt im Klartext auf dem Laeufer stehen.

Kein Leck in die Artefakte: der Sammelschritt (Zeile 4874-4880) arbeitet mit einer
Positivliste, und diese Datei steht nicht darin. Das Kennwort gehoert zu einer Wegwerfinstanz
mit dem Admin-Kennwort `password`. Deshalb LOW und nicht hoeher.

**Fix:** Direkt hinter die Entnahme `echo "::add-mask::${apppw}"`, und die Datei nach dem
`grep` mit `rm -f` wegnehmen. Dasselbe gilt fuer `rebuild-apppw.txt` in "Store upgrade 6".

### L-19-07: `grep -cF` zaehlt Zeilen, nicht Vorkommen

**BEHOBEN** in `7f75456`, wie vorgeschlagen. Dritte Stelle gleicher Bauart
(`info-upgrade.xml`, Zeile 3875 des alten Stands) mitgezogen.

**Kategorie:** bug (CI-Waechter)
**Dateien:** `.github/workflows/deploy-harp.yml:652`, `.github/workflows/deploy-harp.yml:3867`

Beide Waechter begruenden sich ausdruecklich damit, dass der Ersetzungsausdruck genau einmal
vorkommen muss, weil `sed` sonst eine Zeile umschreibt, auf die niemand gezielt hat. Gezaehlt
wird aber mit `grep -cF`, und das zaehlt **Zeilen mit mindestens einem Treffer**. Zwei
Vorkommen in einer Zeile erfuellen den Waechter und werden von `sed` beide ersetzt, weil kein
`1` im Ersetzungsbefehl steht.

Die `info.xml` ist zeilenweise formatiert, der Fall ist heute also nicht erreichbar. Der
Waechter behauptet aber etwas anderes, als er prueft, und das ist die Art Luecke, die
auffaellt, sobald jemand die Datei einmal neu formatiert.

**Fix:** `grep -oF ... | wc -l` statt `grep -cF ...`, dann stimmen Aussage und Messung
ueberein.

---

## Geprueft und sauber (verifizierte Nicht-Befunde)

**Sicherheit des Suchpfads**

- Nutzereingabe kann den `ValueError`-Pfad nicht ausloesen. `body_es:vertrag` in der
  Suchleiste erzeugt einen Eintrag in `errors` und keine Ausnahme (M-1, vierte Zeile);
  `test_query_fields_plan.py:100-110` haelt die Gegenprobe fest.
- `allow_regexes=False` und `conjunction_by_default=True` stehen unveraendert am einzigen
  Parseraufruf (`rewrite.py:623-624`); der Tiefenwaechter `SEARCH_QUERY_MAX_DEPTH` steht
  weiterhin vor allem anderen und zaehlt auf der Rohzeile (`rewrite.py:578`).
- `field_plan_for` wirft nicht. Jeder Pfad endet in einem Plan, und alle drei Aufrufstellen
  (`search.py:248`, `snippets.py:187`, `diagnose.py:198`) liegen zusaetzlich in einem
  `except Exception`, das mit einer leeren, als degraded markierten Antwort endet.
- Die neue Warnzeile fuehrt Feldnamen und Ausnahmetyp und sonst nichts;
  `test_query_fields_plan.py:275-294` prueft ausdruecklich auf die Abwesenheit von `/` und von
  Backslash, und die Funktion bekommt ueberhaupt keinen Suchtext.
- Die Fehlerliste des Parsers bleibt auf `debug` und wird nur gezaehlt (`rewrite.py:627-629`).
  Kein Suchbegriff erreicht `info` oder hoeher.
- Der Anti-Feature-Waechter traegt Gegenproben: `test_no_language_detection.py` laesst ein
  gestelltes Muster mit Textparameter rot werden und meldet bei geleerter Quelle einen Befund
  je Aussage statt null.

**Randfaelle der Marken**

- `schema_version` als `"1"`, `"3"`, `""`, `"abc"`, `UNKNOWN_VERSION` und als fehlende Marke
  enden alle im Bestandsplan; parametrisiert geprueft (`test_query_fields_plan.py:170-185`).
- Fehlende und leere Sprachmarke werden mit derselben Legacy-Regel gelesen wie
  `store/repo._languages_are_legacy`; `LEGACY_LANGUAGES` wird importiert und nicht ein zweites
  Mal geschrieben (`resources.py:404`).
- Ein unbekannter Sprachcode wird uebergangen, weil ueber `BODY_FIELD` iteriert wird und nicht
  ueber die Marke; eine Marke, die nur Unbekanntes nennt, faellt zurueck, statt einen Plan aus
  `name` und `title` allein zu bauen (`resources.py:410-412`).
- `body_de` ist kein Sonderfall: eine Instanz mit `languages="es"` durchsucht die deutsche
  Kette nicht (Pitfall 7, `test_query_fields_plan.py:218-229`).
- `LEGACY_PLAN` deckt sich mit dem echten Schema-1-Feldsatz; `test_schema_generations.py`
  haelt die vier Namen gegen die eingefrorene Neunerliste und gegen beide Indexgenerationen.
- `set(plan.boosts) <= set(plan.fields)` fuer den eingefrorenen Plan und `==` fuer jeden
  berechneten. Pitfall 1 ist geschlossen; die Schwaeche des Falls steht unter M-19-02.
- Gelesen werden die Marken einer echten `state.db` und nicht die eines handgebauten
  Woerterbuchs: `test_query_fields_plan.py:309-340` seedet und stempelt eine Datenbank und
  belegt dabei, dass die Saat `languages` wirklich auslaesst (T-18-05-01).

**Sperren und Wiederoeffnung**

- Der Feldplan wird innerhalb von `_LOCK` gerechnet, zusammen mit den Griffen, die er
  beschreibt. Gelesen wird er ohne Sperre, und das ist richtig: `ReadSide` ist eingefroren, das
  Feld wird nach dem Bau nie geschrieben, und der Griff wird als Ganzes getauscht.
- Der Plan braucht keinen eigenen Generationszweig. `degraded()` und `filled_languages()`
  brauchen ihn, weil sie ihre Seite ausserhalb der Sperre nehmen und ihren Eintrag innerhalb
  schreiben; der Plan entsteht innerhalb, zusammen mit den Griffen. Die Begruendung im
  Kommentar (`resources.py:140-148`) ist korrekt. Die verbleibende Luecke ist H-19-01 und liegt
  auf der Seite des Stempels, nicht der Sperre.
- `_SWAPPING`, `hold_the_read_side_shut` und `let_the_read_side_open` sind unveraendert und
  weiterhin als Paar mit `finally` gefuehrt; M-18-03 bleibt geschlossen.
- Der Meta-Lesevorgang hat ein eigenes `try` bekommen, damit eine `state.db`, die verbindet und
  dann die erste Abfrage verweigert, keine Lesehaelfte kostet (`resources.py:545-550`). Das ist
  eine Verbesserung gegenueber dem Stand davor.

**Performance**

- `field_plan_for` laeuft einmal je Oeffnung und nicht je Anfrage: der einzige Aufruf steht in
  `read_side()` in dem Zweig, der die Griffe baut (`resources.py:557`).
- `doc_freq` kommt im ganzen Paket genau einmal vor, naemlich in dieser Sonde. Keine Sonde im
  Anfragepfad.
- `filled_languages()` wird von `field_plan_for` nicht gerufen (T-19-03-06 gehalten); der
  Termwoerterbuchlauf und seine 30-Sekunden-Fensterung bleiben in der Diagnose.
- Vier bis sechs `doc_freq`-Aufrufe zu gemessenen 0,26 us je Oeffnung sind neben dem
  Registrieren der Analysatorketten (0,44 s allein fuer das deutsche Automat) nicht messbar.
- Das Schrittbudget der CI ist gemessen und nicht geraten: `LANGUAGE_PROOF_BUDGET_SECONDS`
  steht auf 600 gegen 172 s auf dem langsamsten Ast (arm64, Lauf 36074155306), mit einer
  zweiten Lesung von 163 s eine Stunde davor. Die Schleife verlaesst sich beim Treffer und
  schlaeft keine geratene Pause.

**CI-Strecke**

- Keine Injektionsflaeche: jeder Wert in `jq`, `sed` und `curl` ist entweder ein Literal aus
  der Datei oder kommt aus `${{ matrix.* }}`, also aus der Workflow-Definition. Die einzigen
  Werte von aussen sind HTTP-Statuscodes und `jq`-Ausgaben, und beide werden vor der
  Verwendung geprueft.
- `term_hits` faellt geschlossen: ein anderer Status als 200 und eine Antwort, die `jq` nicht
  lesen kann, geben `return 1`, und der Zaehler wird mit `case ''|*[!0-9]*` gegen alles
  geprueft, was kein reiner Zahlwert ist, bevor er als `--argjson` in `jq` geht.
- `TESTUSER_PASS` steht nur in den `curl`-Zeilen und wird nie ausgegeben.
- Die ausgelieferte `backend/appinfo/info.xml` ist unveraendert; die Ersetzung trifft nur die
  Kopie in `RUNNER_TEMP`, und die vorhandene Zeile `git -C findling-src diff --quiet` steht
  weiterhin dahinter (T-19-07-03 gehalten). Der Upgrade-Ast dreht die Sprachvorgabe
  ausdruecklich auf `de,en` zurueck, damit die Registrierung unter der Werkseinstellung laeuft.
- Der Sprachbeweis traegt kein `if:` und laeuft damit auf allen vier Aesten einschliesslich
  arm64 (Pitfall 3 vermieden); `test_language_proof_steps.py` haelt die Abwesenheit der
  Bedingung fest und liest die beiden gegateten Schritte als Gegenbeispiel.
- Die Probe behauptet `entries | length` und nie `entries[0].subline`; der leere Textauszug
  eines reinen Sprachfeldtreffers (M-4, Pitfall 4) ist damit korrekt nicht als Fehler
  verdrahtet, und die Grenze steht in `docs/language-analyzers.md` unter "Known limits"
  (Zeile 356 folgende), so wie Annahme A5 es vorsieht. Fuer Store-Text und Grenzenliste des
  Releases ist Phase 23 zustaendig; dort gehoert der Punkt auf die Liste.
- Die Wortwahl des Beweises haelt Pitfall 2 stand. Nachgerechnet fuer alle vier Paare: die
  deutsche Kette traegt bewusst keinen Faltfilter (`index/analyzer.py`, Abschnitt "The German
  branch has no folding filter"), deshalb bleibt die akzentuierte Dokumentform von der
  ASCII-Frage getrennt, und die englische Porter-Kette fuehrt keines der vier Paare zusammen.
  Nur die jeweils eigene Kette tut es. Die zusaetzliche Zusicherung auf den Dateinamen des
  ersten Treffers macht den Beweis eindeutig.
- Die drei spanischen Zusicherungen lesen als Kette 0, 0, 1 ueber drei Zustaende hinweg und
  liegen in einem eigenen Snapshot-Schluessel statt als vierter Eintrag unter `.terms`, womit
  die Vorbedingung `[.terms[]] | all(. == 1)` unangetastet bleibt (T-19-08-03 gehalten).
- Die Vorbedingung des Beweises liest `languagesActive` aus der Uebersicht und bricht ab, wenn
  die Instanz nicht mit sechs Sprachen laeuft (T-19-07-02 gehalten).
- Die Artefakte werden ueber eine Positivliste kopiert; `rebuild-env.list` mit dem
  `APP_SECRET` ist ausdruecklich nicht darin, und die beiden Kennwortdateien dieser Phase sind
  es ebenfalls nicht.
- `scripts/dev/measure_chains.sh` faehrt `set -eu`, quotet jede Variable, prueft die
  Eingabeverzeichnisse und das Vorhandensein von `uv` vor dem Lauf und enthaelt kein `eval` und
  keine Interpolation aus fremder Quelle. Geaendert wurden nur die erwarteten Messzahlen im
  Kommentarkopf.

**Abhaengigkeiten**

- `backend/pyproject.toml` und `backend/uv.lock` sind ueber die ganze Spanne unveraendert. Kein
  Paket ist dazugekommen, und keines aus der Spracherkennungsfamilie ist vorhanden; der
  Waechter aus Plan 19-05 liest beide Dateien und faellt geschlossen, wenn eine davon fehlt.
- `php/` ist in dieser Phase nicht angefasst worden. Die PHP-Seite reicht den Begriff durch und
  kennt keine Sprache, so wie die Verantwortungskarte es vorsieht.

---

## Empfohlene Reihenfolge der Behebung

1. **H-19-01** vor dem Phasenabschluss. Ohne diesen Fix haengt das Ergebnis der Phase auf einer
   echten Installation vom Zufall ab, und die CI kann es nicht zeigen.
2. **M-19-01** und **M-19-05** zusammen: beide betreffen die Belastbarkeit des Tors, und der
   zweite macht den ersten seltener noetig.
3. **M-19-02**, **M-19-03**, **M-19-04**: Gleichschritt, Sichtbarkeit, Unterscheidbarkeit.
   Klein, und sie verhindern, dass ein spaeterer Rueckfall wieder lange unbemerkt bleibt.
4. Die LOW-Befunde in einem gemeinsamen Durchgang; **L-19-05**, **L-19-06** und **L-19-07**
   gehoeren dabei in denselben Commit wie der Workflow, damit die Textgates einmal statt
   dreimal laufen.

---

_Geprueft: 2026-09-25_
_Pruefer: Claude (gsd-code-reviewer), adversarial_
_Tiefe: deep_

_Behoben: 2026-09-25, Commits `6f35cbe..7f75456`_
_Behebung: Claude (gsd-code-fixer)_
_Offen aus dieser Runde: L-19-05 als Messung statt als Gate (Begruendung beim
Befund); die PHP-Seite von M-19-03 gehoert in den Plan, der die Adminseite
besitzt._
