---
phase: 14-modell-entladung-im-leerlauf
plan: 11
subsystem: docs
tags: [documentation, runbook, admin, measurement, phase-15, threat-model]

# Dependency graph
requires:
  - phase: 14-modell-entladung-im-leerlauf
    provides: Der Schalter FINDLING_EMBED_IDLE_RELEASE_SECONDS aus 14-03 mit seinem Fenster 0 und 60 bis 86400
  - phase: 14-modell-entladung-im-leerlauf
    provides: Die Degradationsnaht aus 14-08 und der schriftliche Grund, warum api/diagnose.py weiter laedt
  - phase: 14-modell-entladung-im-leerlauf
    provides: Das sechste Wort unloaded aus 14-09 und seine Zustandstabelle in docs/admin-page.md
  - phase: 14-modell-entladung-im-leerlauf
    provides: Die vierte Phase des one_load-Werkzeugs aus 14-10, die den Schalter im Messcontainer auf 0 verlangt
  - phase: 14-modell-entladung-im-leerlauf
    provides: Der Vorprueflauf aus 14-02 mit Rueckgabequote, Bodensatz und Architekturvergleich
provides:
  - docs/embeddings.md Abschnitt 10, der Schalter aus Admin-Sicht
  - Die festgeschriebene Messgroesse "Rueckkehr zur Grundlast nach einem Indexlauf" samt verbotener Alternative
  - Der Bodensatz mit Zahl und Architektur in docs/performance.md
  - docs/runbook-messbox.md Abschnitt 6.4, die Stellung des Schalters als protokollpflichtige Groesse
  - docs/runbook-messbox.md Abschnitt 7.2, der A/B-Messschritt mit Exit-Codes 29 bis 31 und der Aufwaermregel
affects: [14-12, 15-boxmessung, 16-store-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Zahl in einem oeffentlichen Dokument traegt Datum, Maschine und den Verweis auf ihr Messverzeichnis, oder sie steht nicht da"
    - "Eine Stelle, die spaeter einmal eine Zahl bekommt, sagt ausdruecklich, dass sie heute keine hat, und wohin die Messung gehoert"
    - "Ein aelterer Abschnitt, dessen Entscheid ueberholt ist, bekommt einen datierten Nachtrag statt einer Loeschung: die drei Zahlen von damals gelten weiter, nur ihr Schluss nicht mehr"

key-files:
  created: []
  modified:
    - docs/embeddings.md
    - docs/performance.md
    - docs/runbook-messbox.md

key-decisions:
  - "Der alte Abschnitt 'Modell-Entladung nach Leerlauf: nein, mit drei Zahlen' in docs/performance.md bekommt einen datierten Nachtrag, obwohl der Plan ihn nicht nennt: ohne ihn behauptet dasselbe Dokument an zwei Stellen Gegenteiliges, und der Satz 'wird in diesem Milestone nicht mehr geplant' stuende gegen einen gebauten Schalter"
  - "Die Messgroesse steht als ASCII-Bezeichner 'Rueckkehr zur Grundlast nach einem Indexlauf' in Backticks, obwohl docs/performance.md sonst Umlaute in Ueberschriften traegt: sie ist ein Name, gegen den spaeter gegriffen wird, und ein Name traegt keine Umlaute"
  - "Der Messschritt 8 des Runbooks wurde nicht neu angelegt, sondern nachgezogen: die Zeile stand seit 12-08 mit dem Vermerk, der Schalter entstehe in Phase 14. Ein zweiter Schritt daneben haette die Nummerierung der Anfahrt gebrochen"
  - "Die drei neuen Rueckgabewerte 29, 30 und 31 haengen alle an Schritt 8 und stehen in einer eigenen Tabelle in 7.2 statt in 7.1: 7.1 ist die Katalogtabelle der Sprachfall- und Cron-Abbrueche, und der A/B-Schritt bringt seine Bedingungen mit seiner Beschreibung mit"
  - "Je Datei wird die vorgefundene ss/ss-Schreibung fortgefuehrt: embeddings.md und das Runbook schreiben ss, performance.md schreibt das scharfe s. Eine einheitliche Umstellung waere eine Aenderung an 4.000 Zeilen, die dieser Plan nicht anfasst"
  - "Die vier Auspraegungen des A/B beginnen mit den Kaltmessungen: jede Messung waermt den Seitencache des Wirts, und eine einmal gewaermte Kaltmessung ist ohne erneutes Leeren nicht wiederholbar"

patterns-established:
  - "Ein Warnsatz, der eine Messung retten soll, steht als eigener fett gesetzter Absatz und nicht als Nebensatz in einer Tabellenzelle"
  - "Eine protokollpflichtige Groesse bekommt eine Zeile in der Tabelle von Abschnitt 6 UND einen eigenen Unterabschnitt mit ihrer Begruendung, nach dem Muster des Cron-Intervalls aus 6.1"

requirements-completed: []  # MEM-01, MEM-02 und MEM-03 sind gebaut und getestet; ihre Beleg-Messung auf der Box gehoert Phase 15, Begruendung im Abschnitt Requirements

# Metrics
duration: 40min
completed: 2026-09-19
---

# Phase 14 Plan 11: Drei Dokumente ziehen nach Summary

**Ein Admin findet den Schalter jetzt an einer Stelle erklaert, die Messgroesse heisst festgeschrieben "Rueckkehr zur Grundlast nach einem Indexlauf" und nicht "Grundlast minus X", und die eine bezahlte Box-Anfahrt weiss vor der Abfahrt, dass ein Diagnoseaufruf den Container aufwaermt und ihre Kaltmessung damit wertlos macht.**

## Performance

- **Duration:** 40 min
- **Started:** 2026-09-19T21:15:00Z
- **Completed:** 2026-09-19T21:55:00Z
- **Tasks:** 3 von 3
- **Files modified:** 3 (genau die drei der Frontmatter, kein Store-Text, kein README)

## Accomplishments

### Task 1: docs/embeddings.md Abschnitt 10, der Schalter aus Admin-Sicht

Ein neuer Abschnitt am Ende der Seite, in der Reihenfolge, die der Plan
vorgegeben hat: was passiert, wie eingeschaltet wird, was es kostet, was es
bringt, was auf der Seite zu sehen ist, wann man es sein laesst.

| Inhalt | Was dort steht |
|---|---|
| Wirkung | Tokenizer, Splitter und Inferenzsitzung werden freigegeben, die Seiten gehen an das Betriebssystem zurueck, und freigegeben wird nur im echten Leerlauf |
| Einschaltung | `FINDLING_EMBED_IDLE_RELEASE_SECONDS` als Tabelle: `0` aus und Werksstand, `60` bis `86400` ein, alles andere faellt zurueck; Vorschlagswert `900` mit seiner Begruendung |
| Ausschaltung | auf `0` setzen oder entfernen, wirksam beim naechsten Containerstart |
| Preis | die erste Suche nach einer Ruhephase antwortet lexikalisch, waermt im Hintergrund nach, und bezahlt wird je warmem Fenster genau einmal |
| Nutzen | **100,0 Prozent** Rueckgabe, Median ueber fuenf Zyklen, aarch64, 19.09.2026, mit Verweis auf das Messverzeichnis |
| Sichtbarkeit | der Zustand `unloaded` mit seinem Satz und der Verweis auf `docs/admin-page.md` |
| Gegenanzeigen | eine dauerhaft indexierende Box und eine Instanz, auf der die Suche der Hauptweg ist |

Die drei Zahlen sind gegen `backend/src/findling/config.py`
(`EMBED_IDLE_RELEASE_SECONDS = 0`, `EMBED_IDLE_RELEASE_SECONDS_RANGE = (60, 86400)`)
und gegen die Beschreibung der Variablen in `backend/appinfo/info.xml` gelesen
worden, nicht erinnert. Der Abschnitt sagt ausserdem, dass sie genau dort und
nirgends sonst stehen, damit die naechste Aenderung weiss, wohin sie muss.

Eine Zahl, nicht drei: der Abschnitt nennt als Ertrag ausschliesslich die
Rueckgabequote. Der schlechteste Einzelzyklus und der Architekturvergleich
bleiben im Bericht, wo sie hingehoeren.

### Task 2: docs/performance.md, die Messgroesse und der Bodensatz

Ein neuer Abschnitt der obersten Ebene, "Die Entladung im Leerlauf: die Zahl,
die man nicht erfinden darf", mit vier Unterabschnitten:

1. **Die Messgroesse.** Sie heisst `Rueckkehr zur Grundlast nach einem
   Indexlauf`. Die verbotene Alternative steht daneben und mit ihrer
   Begruendung: die Grundlast von 103,2 MB ist seit dem faulen Bau von 07-03
   bereits ohne Modell und ohne Cutter gemessen, eine Differenz zu ihr zoege
   etwas ab, das in ihr nicht steckt. Dazu das Warnzeichen aus Pitfall 5, eine
   Ersparnis hoeher als die gemessene Differenz zwischen vorher und nachher.
2. **Der Aktivierungsspeicher.** +293,8 MB beim ersten `run`, +0,0 MB ueber
   zwanzig weitere, trotz `enable_cpu_mem_arena=False`, mit Quelle
   (14-RESEARCH.md Abschnitt 3.2) und Architektur (x86_64 nativ). Das ist die
   quantitative Begruendung fuer den Namen: nach einem Indexlauf steht genau
   dieser Posten im Container.
3. **Der Bodensatz.** Die Modulimporte von `onnxruntime` und `numpy` kommen nie
   zurueck. Gemessen: rund 16 MB auf aarch64 (15,9 MB im ersten Zyklus, 17,1 MB
   ueber fuenf Zyklen), 16,6 MB auf dem x86_64-Vergleichsast, 12,1 MB in der
   Vorrecherche. Mit dem Satz, der daraus folgt und der in keinen Produkttext
   hineingeschrieben werden darf, ohne ihn zu nennen.
4. **Was bewusst nicht dasteht.** Die Ladezeit nach einer Entladung hat in
   diesem Dokument keine Zahl und bekommt eine auf der Box der Phase 15. Dazu
   die Abgrenzung gegen die drei Kaltstartzahlen, die weiter oben schon stehen
   (1.332,1 ms auf der Box, 1.299 und 1.392 ms in CI): sie messen den ersten
   Ladevorgang nach einem Containerstart und duerfen nicht als
   Wiederaufwaermzahl gelesen werden.

### Task 3: das Runbook der Box-Anfahrt

**Abschnitt 6** hat eine sechste protokollpflichtige Groesse: die Stellung des
Schalters, abgelesen aus der Umgebung des Containers, je Messschritt neu. Die
Einleitung sagt jetzt "sechs Groessen" statt "fuenf". Der neue Unterabschnitt
**6.4** traegt die Pflichtzeile `entladeschalter-ist=<sekunden>` nach dem Muster
von `cron-intervall-ist`, mit vier Begruendungen: der Vergleich braucht beide
Stellungen, der Fehler faellt in keiner Fehlerspalte auf (HTTP 200 mit weniger
Treffern), die Stellung geht bei jeder Registrierung verloren, und der
Messcontainer des `one_load`-Gates braucht `0`, weil `query_may_load()` sonst
die zweite Suchrunde zurueckweist und das warme Fenster null Ladevorgaenge zeigt
(Uebergabe aus 14-10).

**Abschnitt 7** hat den Messschritt 8 nachgezogen, aus "Wiederaufwaerm-Messung,
der Schalter entsteht in Phase 14" wird "Wiederaufwaerm-Kosten, A/B, siehe
7.2, Abbruchpfade 29 bis 31". Der neue Unterabschnitt **7.2** traegt:

- die vier Auspraegungen als Tabelle, in bindender Reihenfolge, Kaltmessungen
  zuerst, mit der Begruendung (jede Messung waermt den Cache);
- den Hinweis, dass jeder Wechsel der Stellung den Container neu baut und
  danach Block 12 und 6.4 neu abgelesen werden;
- **die Aufwaermregel als eigener fett gesetzter Warnsatz**: ein Aufruf der
  Diagnose-Route (`ranked_sides`) LAEDT das Modell, vor einer Kaltmessung darf
  sie nicht gerufen werden; die Fremdbestands-Vorpruefung faehrt danach oder mit
  dem Effekt im Protokoll;
- die zweite Haelfte derselben Falle: nach einer Entladung meldet die
  Diagnose-Route eine volle semantische Seite und die Nutzerrouten eine leere,
  und wer die zwei verwechselt, misst zwei Dinge und nennt sie eine Zahl;
- die Forderung nach dem Beleg, dass ueberhaupt entladen wurde (`unloaded` und
  der Entladezaehler);
- die drei neuen Rueckgabewerte 29, 30 und 31 als Tabelle, mit dem Satz, dass
  sie wie die vier aus 6.1 und 6.2 unterhalb der `tee`-Pipeline stehen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - fehlende kritische Funktionalitaet] Der alte Nein-Abschnitt in docs/performance.md hat einen datierten Nachtrag bekommen**

- **Found during:** Task 2
- **Issue:** `docs/performance.md` traegt seit Phase 07 den Abschnitt
  "Modell-Entladung nach Leerlauf: nein, mit drei Zahlen" und schliesst ihn mit
  dem Satz, die Entladung bleibe in "Future Requirements" und werde in diesem
  Milestone nicht mehr geplant. Der neue Abschnitt derselben Datei beschreibt
  den gebauten Schalter. Ohne Nachtrag behauptet ein oeffentliches Dokument an
  zwei Stellen Gegenteiliges, und ein Leser kann nicht entscheiden, welche
  Stelle aelter ist.
- **Fix:** Ein Absatz "Nachtrag vom 19.09.2026: gebaut, aber als Schalter mit
  Werksstand aus" direkt unter dem alten Schlusssatz. Er widerlegt die drei
  Zahlen nicht, sondern ordnet sie ein: Punkt 1 und 2 stehen unveraendert
  (weder die Spitze eines Indexlaufs noch die Grundlast eines Containers ohne
  Einbettung sinken), Punkt 3 ist durch die Degradationsnaht aus 14-08
  entschaerft und nicht aufgehoben (die erste Suche wartet nicht mehr, der
  Preis ist eine Suche ohne semantische Seite statt einer gerissenen
  1,5-Sekunden-Decke). Am Ende der Verweis auf den neuen Abschnitt.
- **Files modified:** docs/performance.md
- **Commit:** 9332231

**2. [Rule 3 - Blocker] Zeilenenden: alle drei Dateien liegen im Arbeitsbaum als CRLF**

- **Found during:** Task 1
- **Issue:** Die erste Einfuegung mit Python hat den Anbau als CRLF und den
  vorhandenen Text als LF geschrieben, weil `read_text` die Zeilenenden
  vereinheitlicht. `file` meldete danach "CRLF, LF line terminators", und `git`
  warnte beim Hinzufuegen.
- **Fix:** Nach jeder Einfuegung wird die ganze Datei mit
  `write_text(..., newline="")` und `\r\n` geschrieben. `git diff --stat` zeigt
  fuer alle drei Dateien ausschliesslich die neuen Zeilen, keine
  Ganzdatei-Differenz.
- **Files modified:** docs/embeddings.md (Reparatur), danach dasselbe Muster fuer die zwei anderen
- **Commit:** b96175f

### Nicht abgewichen

Kein Store-Text, kein README und keine Datei ausserhalb der drei der Frontmatter
wurde angefasst. Der Phase-16-Checkpoint fuer Store-Texte und README bleibt, wo
der Owner ihn am 19.09.2026 hingelegt hat.

## Requirements

Der Plan fuehrt MEM-01, MEM-02 und MEM-03 in seiner Frontmatter. Keine davon
wird mit diesem Plan abgehakt, und das ist kein Versaeumnis:

| Anforderung | Stand |
|---|---|
| MEM-01 (Schalter, ab Werk aus) | gebaut in 14-03, dokumentiert mit diesem Plan; der A/B-Beleg gehoert Phase 15 |
| MEM-02 (beide Halter frei nach TTL) | gebaut in 14-04 bis 14-07, dokumentiert mit diesem Plan; die Beleg-Messung an der Messgroesse gehoert Phase 15 |
| MEM-03 (Degradation ohne Zeitverlust) | in 14-08 abgehakt, hier nur noch beschrieben |

Dieser Plan liefert die Dokumentation, nicht die Messung. Ein Haken auf einer
Anforderung, deren Beleg auf einer Box entsteht, die noch nicht angefahren ist,
waere genau der Fehler, den Abschnitt 7.2 des Runbooks verhindern soll.

## Verification

| Nr. | Pruefung | Ergebnis |
| --- | -------- | -------- |
| 1 | `grep -c FINDLING_EMBED_IDLE_RELEASE_SECONDS docs/embeddings.md` | 1 |
| 1 | `uv run pytest tests/test_store_metadata.py -q` | 52 passed |
| 2 | `grep -c Grundlast docs/performance.md` | 47 |
| 2 | `grep -qi bodensatz docs/performance.md` | trifft |
| 2 | `grep -c 'Rueckkehr zur Grundlast' docs/performance.md` | 1 |
| 3 | `grep -c FINDLING_EMBED_IDLE_RELEASE_SECONDS docs/runbook-messbox.md` | 2 |
| 3 | `grep -c ranked_sides docs/runbook-messbox.md` | 2 |
| 3 | `grep -qi archiv docs/runbook-messbox.md` | trifft nicht (Vokabular-Gate gehalten) |
| alle | U+2014 und U+2013 in allen drei Dateien | keine |
| alle | `uv run pytest tests/test_store_metadata.py tests/test_measurement_scripts.py -q` | **282 passed** |
| alle | `git diff --name-only` ueber die drei Commits | genau die drei Dateien der Frontmatter |
| alle | Die drei Zahlen gegen `config.py` und `info.xml` | `0`, `(60, 86400)`, `900` identisch |

Keine volle Suite gefahren und kein `ruff`/`pyright`/`vulture`: dieser Plan
faesst keine Zeile Python und keine Zeile PHP an. `PACKAGE_TREE_HASH_TODAY` und
`PHP_TREE_HASH_TODAY` in `backend/tests/test_measurement_scripts.py` bleiben
deshalb unveraendert, und die 230 Faelle dieser Datei sind gruen.

## Known Stubs

Keine. Eine Stelle sagt ausdruecklich, dass sie heute keine Zahl hat: die
Ladezeit nach einer Entladung in `docs/performance.md`. Das ist kein Platzhalter,
sondern die Aussage selbst, mit Grund (nicht gemessen), Zielort (Phase 15, Box)
und Messweg (Runbook Abschnitt 7.2).

## Acceptance Items (Owner, Phasen-Checkpoint 14-12)

- Der Abschnitt 10 von `docs/embeddings.md` ist der Text, den ein fremder Admin
  liest. Er ist laenger als ein Store-Text sein darf, und das ist beabsichtigt
  (Owner-Regel zu kurzen Produkttexten gilt fuer Store und README). Eine
  Sichtprobe auf Tonlage lohnt trotzdem.
- Der Vorschlagswert `900` steht in `info.xml`, in `config.py` als Kommentar und
  jetzt in `docs/embeddings.md`. Er ist bis zur Messung der Phase 15 eine
  begruendete Schaetzung und keine gemessene Zahl; das sagt der Kommentar in
  `config.py` ausdruecklich, `docs/embeddings.md` sagt es nicht mit demselben
  Nachdruck.

## Threat Flags

Keine neue Angriffsflaeche: drei Textdateien, kein Netzpfad, keine Route, kein
Dateizugriff, keine Schemaaenderung, keine neue Abhaengigkeit.

Die vier Dispositionen des Plans sind erfuellt:

| Threat ID | Erfuellt durch |
|---|---|
| T-14-41 (Adressen oder Kennungen im oeffentlichen Runbook) | Die neuen Abschnitte nennen keine Adresse, keine Instanzkennung und keinen Schluessel. Der einzige Klartextname ist der Containername `nc_app_findling_backend`, der seit 12-07 an mehreren Stellen derselben Datei steht |
| T-14-42 (Ersparniszahl ohne ihre Maschine) | Jede Zahl in `embeddings.md` und `performance.md` traegt Datum, Architektur und den Verweis auf das Messverzeichnis; die eine Zahl ohne eigenes Verzeichnis (+293,8 MB) nennt Datei und Abschnitt der Vorrecherche |
| T-14-43 (Nullwert wird Befund) | Die Aufwaermregel steht als eigener Warnsatz in 7.2, mit Rueckgabewert 30 daneben, und die Verwechslung Diagnose gegen Nutzerroute ist ausgeschrieben |
| T-14-SC (Paketinstallationen) | Keine. Dieser Plan hat nichts installiert |

## Self-Check: PASSED

Drei geaenderte Dateien vorhanden, SUMMARY vorhanden, drei Commits im Baum
(`b96175f`, `9332231`, `ce86b78`), keine Em-Dashes in der Zusammenfassung.
