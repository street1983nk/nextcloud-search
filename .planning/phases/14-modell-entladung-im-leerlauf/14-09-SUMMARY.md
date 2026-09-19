---
phase: 14-modell-entladung-im-leerlauf
plan: 09
subsystem: admin-ui
tags: [engine-state, l10n, admin-page, protocol, owner-decision, tdd]

# Dependency graph
requires:
  - phase: 14-modell-entladung-im-leerlauf
    provides: unload_count() aus 14-05, der monotone Entladezaehler, und released_count() aus 14-06, der ihn durchreicht
  - phase: 07-statusseite-und-diagnose
    provides: engine_state() mit seiner festen Rangfolge und die gespiegelte geschlossene Liste in AdminViewService
provides:
  - ENGINE_UNLOADED und der sechste Eintrag in ENGINE_STATES
  - Der Zweig in engine_state() hinter loaded und vor cold
  - Der siebte Satz in beiden Haelften der Admin-Seite, wortgleich
  - Ein Schluessel in sechs Katalogdateien, 199 statt 198
  - Die Zustandstabelle in docs/admin-page.md mit sechs Meldungen
affects: [14-11, 14-12, 15-boxmessung, 16-store-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Zustandswort wird aus einem monotonen Zaehler abgeleitet und nicht aus einem neuen Feld: ein Prozess, der nie entladen hat, kann das Wort dadurch gar nicht melden"
    - "Eine autouse-Fixture in conftest raeumt ein Modulglobal ab, das sonst aus einer Testdatei in die naechste leckt"
    - "Wer eine harte Zahl in einem Gate erhoeht, schreibt den naechsten Herkunftsabsatz in den Docstring"

key-files:
  created: []
  modified:
    - backend/src/findling/embed/engine.py
    - backend/tests/test_embed_engine.py
    - backend/tests/conftest.py
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
    - php/lib/Service/AdminViewService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/tests/Unit/AdminViewServiceTest.php
    - php/l10n/de.json
    - php/l10n/de.js
    - php/l10n/de_DE.json
    - php/l10n/de_DE.js
    - php/l10n/fr.json
    - php/l10n/fr.js
    - docs/admin-page.md
    - docs/l10n-french.md

key-decisions:
  - "Der Zweig steht hinter loaded und vor cold: der Zaehler kann nur sagen, dass eine Freigabe geschehen ist, nie dass der Halter gerade leer ist, und der Halter ist es, der das beantwortet"
  - "Die Katalogeintraege reisen im selben Commit wie die zwei Gate-Literale und die zwei Seitenhaelften, weil das Satz-Gate die neuen Saetze im deutschen Katalog sucht; die im Plan vorgesehene Trennung Task 2 / Task 3 haette einen roten Commit erzeugt"
  - "Der Entladezaehler wird je Testfall auf null gesetzt (conftest, forget_the_release_count), nicht im Container: ohne das entscheidet eine Freigabe in test_embed_model.py, was test_status_endpoint.py drei Dateien spaeter als Zustand liest"
  - "Der Satz zu waiting_for_retry wird praezisiert und nicht geloescht: die Begruendung fuer die zwei Quellen dieses einen Wortes bleibt stehen, und der Zusatz sagt, dass das sechste Wort zu einer anderen Lage gehoert"
  - "php/tests/Unit/AdminViewServiceTest.php bekommt die sechste Zeile seines Datenproviders, obwohl der Plan die Datei nicht nennt: eine gespiegelte Liste ohne Fall fuer den neuen Eintrag ist eine ungeprueftes Wort an einer Vertrauensgrenze"

patterns-established:
  - "Vor dem Einfuegen in eine Katalogdatei wird die Ankerzeile auf ihr trennendes Komma geprueft, und nach dem Einfuegen geht jede der sechs Dateien durch einen Parser statt durch eine Diff-Durchsicht"

requirements-partial:
  - "MEM-05: die Haelfte 'die Admin-Seite zeigt den Zustand' ist erfuellt; die Haelfte 'die one_load-Zusage wird neu formuliert' traegt 14-10"
requirements-completed: []

# Metrics
duration: 35min
completed: 2026-09-19
---

# Phase 14 Plan 09: Das sechste Wort `unloaded` Summary

**Ein Container, der die Gewichte im Leerlauf freigegeben hat, sagt das jetzt: `unloaded` ist der sechste Zustand, beide Haelften der Admin-Seite bilden ihn auf denselben Satz ab, drei Sprachen tragen ihn, und `docs/admin-page.md` behauptet nicht mehr, es gebe kein sechstes Wort.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-09-19T16:55:00Z
- **Completed:** 2026-09-19T17:30:00Z
- **Tasks:** 3 von 3
- **Files modified:** 17 (kein neues Modul, keine neue Abhaengigkeit)

## Accomplishments

### Der Zaehler ist die Quelle, nicht ein neues Feld

`engine_state()` bekommt genau eine Zeile Verhalten:

```
if held is not None and held.loaded:
    return ENGINE_LOADED
if unload_count() > 0:
    return ENGINE_UNLOADED
```

Die Rangfolge ist damit `disabled`, `missing`, `waiting_for_retry`, `loaded`,
`unloaded`, `cold`, und beide Nachbarschaften sind im Docstring begruendet:
hinter `loaded`, weil der Zaehler monoton ist und nur sagen kann, dass eine
Freigabe geschehen ist, waehrend der Halter sagt, ob gerade Gewichte da sind;
vor `cold`, weil `cold` der Zustand ist, der uebrig bleibt, wenn nichts anderes
wahr ist.

Der Zaehler statt eines Feldes hat eine Eigenschaft, die ein Feld nicht haette:
ein frischer Prozess steht auf null und kann das Wort gar nicht melden. Das ist
die Anti-Leerlauf-Klausel des ganzen Zweiges und steht als eigener Testfall da.

### Beide Haelften der Seite, wortgleich

| Stelle | Was dort steht |
|---|---|
| `AdminViewService.php` | `'unloaded'` als sechster Eintrag der gespiegelten geschlossenen Liste |
| `templates/admin.php` | `'unloaded' => $l->t('The model was released to save memory. ...')` |
| `js/admin.js` | `case 'unloaded':` mit demselben Satz, byteweise gleich |

Das Gate `test_both_halves_of_the_page_map_the_same_state_to_the_same_sentence`
haelt die beiden gegen den aus dem Container importierten Satz und ist gruen,
also stimmen alle drei Stellen ueberein, ohne dass eine vierte Schreibweise
entstanden waere.

In den Kommentar beider Haelften und in die Dokumentation ist die Falle
geschrieben, die zu diesem Wort gehoert (PITFALLS 13): ein Container, der
`unloaded` meldet, und eine PHP-App, die es noch nicht kennt, zeigt den
Ausweichsatz "Dieser Container meldet den Zustand des Modells noch nicht". Das
sieht wie ein kaputtes Backend aus und ist nichts als eine Aktualisierung in der
falschen Reihenfolge.

### Sechs Kataloge, drei Sprachen, 199 Schluessel

| Datei | Schluessel | Wortlaut |
|---|---:|---|
| `de.json`, `de.js` | 199 | Das Modell wurde zum Sparen freigegeben. Die nächste Suche antwortet mit Volltexttreffern und lädt es im Hintergrund nach. |
| `de_DE.json`, `de_DE.js` | 199 | byteweise gleich zu den beiden `de`-Dateien |
| `fr.json`, `fr.js` | 199 | Le modèle a été libéré pour économiser de la mémoire. La prochaine recherche répond avec des résultats en texte intégral et le recharge en arrière-plan. |

Alle sechs Dateien sind nach dem Einfuegen durch einen Parser gegangen, nicht
durch eine Diff-Durchsicht: die Lehre aus 13-11 ist, dass ein Einfuegelauf ohne
Trennkommas weder in der Klammerbilanz noch im Diff auffaellt. Die Ankerzeile
wurde zusaetzlich vor dem Schreiben auf ihr Komma geprueft.

`FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` steht unveraendert bei fuenf
Eintraegen: der neue franzoesische Wert ist weder leer noch gleich seinem
Schluessel noch gleich dem deutschen.

### Die zwei Gate-Zahlen, mit ihren Absaetzen

- `test_the_six_sentences_...` heisst jetzt `test_the_seven_sentences_...` und
  prueft `== 7`. Der Docstring sagt, welche die siebte ist, und begruendet, warum
  das Zahlwort im Namen steht.
- `assert len(keys_of["de.json"]) == 199` mit dem Herkunftsabsatz, den der
  Docstring dieser Funktion von jedem verlangt, der die Zahl erhoeht: Anlass,
  Wortlaut, Owner-Entscheid mit Datum und Fundstelle, und der Hinweis, dass der
  franzoesische Wortlaut ungeprueft ist.

### Die Dokumentation der Seite stimmt wieder

`docs/admin-page.md` hat sieben Tabellenzeilen (sechs Meldungen plus "kein
Feld"), die Einleitung nennt sechs Woerter, und der Satz "also gibt es dafuer
kein sechstes Wort" ist praezisiert statt geloescht: die Begruendung fuer die
zwei Quellen von `waiting_for_retry` bleibt stehen, und der Zusatz sagt, dass es
seit dem 19.09.2026 ein sechstes Wort gibt, aber fuer eine andere Lage. Dazu ein
eigener Abschnitt "Die beiden Haelften reisen als Paar". Kein U+2014 und kein
U+2013 in der Datei.

## Task Commits

| Task | Name | Commit |
|---|---|---|
| 1 (RED) | Die Faelle des sechsten Zustands | `c89e88f` |
| 1 (GREEN) | ENGINE_UNLOADED und der Zweig in `engine_state()` | `11dc4ce` |
| 2 + 3A | Beide Seitenhaelften, sechs Kataloge, zwei Gate-Literale | `61be4bc` |
| 3B | `docs/admin-page.md` und `docs/l10n-french.md` | `4f26644` |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Task 2 und der Katalogteil von Task 3 sind ein Commit**

- **Gefunden bei:** Task 2, vor dem ersten Commit dieses Tasks
- **Sache:** Das Satz-Gate prueft nicht nur `len(sentences) == 7`, sondern auch,
  dass jeder dieser Saetze im deutschen Katalog steht. Ein Commit mit den zwei
  Seitenhaelften und den erhoehten Literalen, aber ohne die Katalogeintraege,
  waere rot gewesen; ein Commit mit den Katalogeintraegen vor den Literalen
  ebenso, weil `de.json` dann 199 Schluessel gegen ein Gate mit 198 traegt.
- **Behandlung:** Die sechs Katalogdateien reisen im Commit von Task 2. Die
  Dokumentationshaelfte von Task 3 (`admin-page.md`, `l10n-french.md`) bleibt
  ein eigener Commit. Jeder Commit dieses Plans ist fuer sich gruen.

**2. [Rule 2 - Missing critical] `php/tests/Unit/AdminViewServiceTest.php`**

- **Gefunden bei:** Task 2
- **Sache:** Der Datenprovider `everyStateOfTheEngine` zaehlt die Woerter der
  gespiegelten Liste einzeln auf. Ohne eine sechste Zeile waere `unloaded` das
  einzige Protokollwort ohne Fall an einer Vertrauensgrenze, und der PHPUnit-Lauf
  in CI haette den neuen Eintrag nie beruehrt.
- **Behandlung:** Sechste Zeile ergaenzt, dazu drei Prosastellen in derselben
  Datei von "five" auf "six". Der Fall fuer alles, was nicht in der Liste steht,
  bleibt unveraendert (er fuehrt weiterhin `'unloading'` als Wort eines spaeteren
  Release).

**3. [Rule 3 - Blocking] Zwei Baumhashes statt einem**

- **Gefunden bei:** Task 1 und Task 2, beim vollen Lauf
- **Sache:** Neben `PACKAGE_TREE_HASH_TODAY` (Projektregel, im selben Commit wie
  die Aenderung unter `backend/src/findling/`) gibt es `PHP_TREE_HASH_TODAY` mit
  derselben Mechanik ueber `php/**/*.php`. Der Plan nennt weder den einen noch
  den anderen.
- **Behandlung:** Beide nachgezogen, jeder mit seinem Kettenabsatz. Der
  PHP-Absatz haelt fest, dass nur drei der 64 Dateien ihre Bytes geaendert haben,
  weil die Rezeptur `**/*.php` globt und `js/admin.js` und die sechs Kataloge
  damit gar nicht in diesem Baum liegen.

### Befunde, die der Plan ausdruecklich sehen wollte

**Ein drittes Zahlliteral, aber in einer anderen Datei.** Der Plan warnt, dass
ein drittes Literal in `test_admin_ui_contract.py` ein Befund sei und in die
SUMMARY gehoere. Dort gibt es keines: `grep -c '== 6'` ist 0 und `grep -c '== 7'`
ist 1. Gefunden wurde ein drittes Literal in
`backend/tests/test_embed_engine.py::test_no_state_of_the_closed_set_names_a_place_on_disk`
(`assert len(ENGINE_STATES) == 5`). Es gehoert zu Task 1 und ist dort auf 6
gezogen worden, mit dem Satz im Kommentar, warum die Zahl ausgeschrieben
dasteht.

**Die Schluesselzahl steht in einer anderen Funktion als der Plan sagt.** Der
Plan verortet `assert len(keys_of["de.json"]) == 198` in
`test_the_two_translation_files_carry_the_same_keys`. Tatsaechlich steht sie in
`test_the_german_catalogue_covers_both_german_language_codes`, und dort steht
auch die Absatzkette der Herkunft (173 -> 174 -> 197 -> 198). Der neue Absatz ist
dort angehaengt worden, wo die Kette liegt.

**`docs/l10n-french.md` zaehlt noch 197 Schluessel.** Die Zaehltabelle am Kopf
der Datei ist seit Plan 13-11 nicht mitgewachsen: sie kennt weder `File contents`
vom 19.09.2026 noch den Satz dieses Plans. Der Nachtrag sagt das ausdruecklich
und nennt die harte Zahl im Gate als die massgebliche (199), statt die
abgenommene Zaehltabelle nachtraeglich umzuschreiben.

## Verification

| Stufe | Ergebnis |
|---|---|
| `uv run pytest tests/test_admin_ui_contract.py -q` | 45 passed |
| `uv run pytest -q` (volle Suite) | **2254 passed, 15 skipped** |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 123 files already formatted |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | keine Ausgabe |
| `php -l` (Docker, `php:8.2-cli`) | No syntax errors detected: `AdminViewService.php`, `templates/admin.php`, `tests/Unit/AdminViewServiceTest.php` |
| Alle sechs Katalogdateien geparst | je 199 Schluessel |

Der PHP-Syntaxnachweis lief als
`docker run --rm -v "C:/Users/Student/nextcloud-search/php:/php:ro" php:8.2-cli php -l /php/<datei>`,
also in derselben PHP-Version wie der Lint-Job in CI (Vorgehen aus 13-04).
Lokal gibt es kein `php` auf dem Pfad. `js/admin.js` hat keinen lokalen Linter
im Repo; die Datei ist ueber das Contract-Gate gehalten, das ihre
Zustandszuordnung auswertet, und ueber den CI-Job.

**Nicht gelaufen: die Sichtprobe an der laufenden Instanz** (Verifikation 5 des
Plans). Sie verlangt einen Neubau des Containers, weil `engine_state()` im
Backend-Abbild steckt. Das ist dieselbe Lage wie bei 14-08, und der Lauf gehoert
aus demselben Grund nach 14-12: ein Neubau jetzt wuerde von den noch folgenden
Plaenen dieser Phase sofort wieder entwertet.

## Known Stubs

Keine.

## Acceptance Items (Owner, Phasen-Checkpoint 14-12)

- **Der franzoesische Wortlaut des sechsten Satzes ist nicht muttersprachlich
  geprueft.** `Le modèle a été libéré pour économiser de la mémoire. La prochaine
  recherche répond avec des résultats en texte intégral et le recharge en
  arrière-plan.` Er steht in der Tabelle von `docs/l10n-french.md` und traegt
  dort den datierten Nachtrag vom 19.09.2026, der ihn als ungelesen ausweist.
- **Sichtprobe an der laufenden Instanz** mit
  `FINDLING_EMBED_IDLE_RELEASE_SECONDS=60`: nach einer Suche und einer Ruhephase
  zeigt die Engine-Zeile den neuen Satz, und nach dem ersten Poll des Skripts
  steht derselbe Satz noch da.

## Threat Flags

Keine neue Angriffsflaeche. `ENGINE_STATES` bleibt eine geschlossene Menge
(T-14-33), das Gate haelt beide Seitenhaelften zusammen (T-14-34), der neue Satz
nennt keine Zahl, kein Dokument und keinen Pfad (T-14-35), und die halb
aktualisierte Paarung ist dokumentiert statt verhindert (T-14-36, bewusst
akzeptiert).

## Self-Check: PASSED

Alle in dieser SUMMARY genannten Dateien liegen auf der Platte, alle vier
Commits (`c89e88f`, `11dc4ce`, `61be4bc`, `4f26644`) stehen in der Historie.
