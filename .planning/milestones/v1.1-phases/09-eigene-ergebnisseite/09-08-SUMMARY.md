---
phase: 09-eigene-ergebnisseite
plan: 08
subsystem: abnahme
tags: [sichtproben, ui-vertrag, l10n, de_DE, audit, security, performance, bugfix]

requires:
  - phase: 09-eigene-ergebnisseite
    provides: "09-05: Template, Stil, Skript und die 24 Copy-Elemente"
  - phase: 09-eigene-ergebnisseite
    provides: "09-06: Navigationseintrag, Einstiegs-Eintrag im Suchdialog, Gate C ueber sechs Dateien"
  - phase: 09-eigene-ergebnisseite
    provides: "09-07: der dritte Vergleich im Paritaetsjob und scripts/dev/probe_page_login.sh"
  - phase: 09-eigene-ergebnisseite
    provides: "09-01: docs/measurements/2026-09-seitenbudget/ als Vorhersage des Budgets"
provides:
  - Das Protokoll der 22 Abnahme-Sichtproben, jede mit einem von drei Ergebnissen
  - 09-UI-SPEC.md auf approved, mit drei begruendeten Nachzuegen
  - docs/l10n-french.md, die 24 vertagten franzoesischen Wortlaute mit ihrer Bedingung
  - docs/audits/2026-09-phase-09/README.md, der erste Auditbericht unter docs/audits/
  - php/l10n/de_DE.json und de_DE.js, die App spricht Deutsch unter beiden Sprachcodes
  - Der Leerzustand schweigt, wenn ein Banner die Leere schon erklaert hat
  - Abschnitt 6.3 des Seitenbudget-Berichts, der 0,318 s Passwortpruefung von der Suche trennt
affects: [10, 11]

tech-stack:
  added: []
  patterns:
    - "Eine Anzeigeentscheidung, die von einer anderen abhaengt, wird neben ihr getroffen und nicht an der Stelle, an der sie wirkt: $showEmpty steht bei $hasError und $hasHint"
    - "Ein zweiter Sprachcode ist eine byte-identische Kopie plus ein Gate auf die Gleichheit, nicht eine zweite Textrunde; die Begruendung steht am Gate und nicht im Commit"
    - "Eine Zahl aus einem Messbericht ist erst vergleichbar, wenn der Anmeldeweg derselbe ist: Basic-Auth kostet auf dieser Instanz 0,318 s je Anfrage"
    - "Ein Auditbefund an einer Dokumentationszahl bekommt keinen Test, und der Bericht sagt warum, statt einen zu erfinden"

key-files:
  created:
    - docs/l10n-french.md
    - docs/audits/2026-09-phase-09/README.md
    - php/l10n/de_DE.json
    - php/l10n/de_DE.js
  modified:
    - .planning/phases/09-eigene-ergebnisseite/09-UI-SPEC.md
    - php/templates/search.php
    - backend/tests/test_admin_ui_contract.py
    - scripts/ci/slow_backend.py
    - docs/measurements/2026-09-seitenbudget/README.md
    - docs/store-listing.md
    - .planning/ROADMAP.md

key-decisions:
  - "Sichtprobe 5 nennt die Scrollposition nicht mehr als Zusage, und die Begruendung steht mit Recherchedatum darunter statt in einem Commit"
  - "Stufe 2 des Rueckkehrvertrags heisst browserabhaengig und in Firefox praktisch abgeschaltet, Stufe 3 heisst tragend: die Umsetzung aendert sich nicht, nur die Zusage wird wahr"
  - "Der Leerzustand mit Suchbegriff schweigt unter jedem Banner, der ohne Suchbegriff bleibt stehen: eine Einladung ist nie eine Behauptung"
  - "de_DE bekommt dieselben Worte wie de, weil dieser Katalog durchgehend in der Sie-Form geschrieben ist; ein duzender zweiter Katalog waere eine unbestellte Textrunde"
  - "Der franzoesische Katalog bleibt vertagt, vollstaendig oder gar nicht, mit einem Zeiger aus der ROADMAP bei Phase 11"
  - "Zwei h1 im Dokument bleiben stehen: die erste kommt vom Core-Rahmen jeder App-Seite, LOW und vom Owner akzeptiert"

patterns-established:
  - "Abnahme einer Phase an der laufenden Instanz: 16 Proben maschinell mit curl und Cookie-Behaelter, 6 mit dem Auge, jede Zeile mit einem von drei Ergebnissen"

requirements-completed: [UI-01, UI-02, UI-03]

duration: 75min
completed: 2026-09-09
---

# Phase 9 Plan 08: Abnahme, Nachzuege und die drei Audits Summary

**Die Phase ist abgenommen, und die Abnahme hat zwei Fehler gefunden, die kein Test gefunden hatte: die Seite stellte "Keine Datei enthaelt X" unter den Satz "Die Suche antwortet gerade nicht", und wer in Nextcloud "Deutsch (Sie)" gewaehlt hatte, las die ganze App auf Englisch.**

## Performance

- **Duration:** rund 75 min
- **Tasks:** 3, davon einer ein blockierender Owner-Checkpoint
- **Files:** 16 (4 neu, 12 geaendert), 1318 Zeilen dazu, 16 weg
- **Commits:** 5

## Das Sichtprobenprotokoll, 22 Zeilen

Gefahren gegen die laufende Instanz auf Port 8090, Nextcloud 34.0.3, App 1.0.3,
`testuser` und `kollegin`, 438 indexierte Dateien. 16 Proben maschinell mit
`curl` und Sitzungs-Cookie, 6 vom Owner mit dem Auge, Abnahme am 09.09.2026.

| # | Probe | Ergebnis | Beleg oder Satz |
|---|---|---|---|
| 1 | Einstieg aus dem Dialog | bestanden | `Show all results` letzter Eintrag der Gruppe, Ziel `/apps/findling/?query=Genehmigung`, `attributes: []` |
| 2 | Wenige Treffer, kein Einstieg | bestanden | `Belehrung`: 1 Treffer, `isPaginated=false`, kein Eintrag |
| 3 | Zweimal vor, zweimal zurueck | bestanden | Seite 2 und Seite 1 zeichengleich mit dem Hinweg, 75 Ids ueber drei Seiten, davon 75 einmalig, `value="Genehmigung"` bleibt im Feld |
| 4 | Treffer oeffnen, zurueck, Markierung, Fokus | bestanden (Owner-Abnahme 09.09.) | |
| 5 | Dasselbe ohne JavaScript, Chromium und Firefox | bestanden (Owner-Abnahme 09.09., beide Engines) | Geprueft gegen die **umformulierte** Fassung: gleiche Seite, gleiche Suche, keine Markierung, keine Fehlermeldung |
| 6 | Lesezeichen auf Seite 3 | bestanden | Tiefe Adresse ohne `requesttoken`: HTTP 200, Seite 3, 25 Zeilen, kein CSRF-Fehler |
| 7 | Cursorpfad verfaelscht | bestanden | Sieben Varianten, jedes Mal still Seite 1, HTTP 200, kein Fehlerblock, kein Logeintrag |
| 8 | Zwei Nutzer, geteilt und nicht geteilt | bestanden | `testuser` 25 Zeilen, `kollegin` genau eine, `fileid` 190, die geteilte Datei; Pfad aus ihrem eigenen Node |
| 9 | Backend gestoppt | **abweichend, gefixt** | Fehlerblock richtig (200, Symbol, Ueberschrift, Satz, `Erneut versuchen`, kein 500). Darunter stand der Leerzustand: Befund M-01, gefixt in `52db222` |
| 10 | Backend verlangsamt | bestanden | 900 ms: eine Trefferzeile nach 1,17 s, kein Fehlerblock. 10 s: Fehlerblock nach 1,55 s. Brauchte den Fix `0c53c4d` |
| 11 | Versionsabweichung | bestanden | Eigener Fehlerblock, keine Versionsnummer im Dokument, keine Trefferzeile |
| 12 | Suche ohne Treffer | bestanden | Leerzustand mit Suchbegriff und drei Schritten, kein Wort ueber Rechte |
| 13 | Seite ohne Suchbegriff | bestanden | Leerzustand und `autofocus` maschinell, der Fokus im Feld vom Owner (Abnahme 09.09.) |
| 14 | `<script>`, Umlaute, 300 Zeichen | bestanden | Dreifach escaped, Umlaute laufen durch, auf 255 gekuerzt. Zusatz: ungueltiges UTF-8 gilt als kein Suchbegriff, ohne Fehlermeldung |
| 15 | Hervorhebung bei Umlauten | bestanden | `<mark>` genau um `Grundstuecksverkehrsgenehmigung` und `Kuendigungsfrist`, UTF-8-Bytes intakt; das Bild vom Owner (Abnahme 09.09.) |
| 16 | Dunkles Theme, Hoher Kontrast | bestanden (Owner-Abnahme 09.09.) | Einschliesslich des Paares Fehlerflaeche zu Fehlersymbol, das der Server nicht auf Kontrast prueft |
| 17 | Tastatur allein | bestanden | 25 Zeilen, genau ein Link je Zeile, kein `tabindex`, kein `outline: none`; Fokusring vom Owner (Abnahme 09.09.) |
| 18 | Screenreader ueber eine Trefferzeile | bestanden (Owner-Abnahme 09.09.) | Accessible Name maschinell belegt: `00247-stellungnahme.docx in lastkorpus/00247-stellungnahme.docx` |
| 19 | Handybreite unter 640px | bestanden (Owner-Abnahme 09.09.) | Vier `@media`-Bloecke, davon einer `pointer: coarse` |
| 20 | Englisch und Deutsch | **abweichend, gefixt** | `lang=de` vollstaendig deutsch, `lang=de_DE` alles englisch: Befund M-02, gefixt in `0175b56` |
| 21 | *(neu)* Jenseits der Offset-Decke | **abweichend, gefixt** | Hinweisbanner "Es gibt weitere Treffer" und kein Fehlerblock, wie verlangt; der Leerzustand darunter war Teil von M-01 |
| 22 | *(neu)* Viele genehmigte gegen ueberwiegend verworfene Kandidaten | bestanden | `testuser` 25 Zeilen mit Pager, `kollegin` eine ohne Pager, auf keiner Seite ein Satz, eine Zahl oder ein Symbol ueber Entferntes |

**Kein Ergebnis "nicht durchfuehrbar".** Das war zur Halbzeit anders: DI-09-05
hatte festgestellt, dass die lokale Instanz nicht indexiert, womit 14 der 22
Proben keinen echten Treffer gesehen haetten. Die Ursache war kein Defekt der
Maschine, sondern ein Artefakt aus der Zeit vor Plan 06.1-17: das
Wortlisten-Artefakt heisst seit damals `de-full.txt`, in `.dev/storage/dict/` lag
nur die alte `de.txt`, und der Poller starb an jedem Durchgang mit einem
`FileNotFoundError`, bevor er eine Datei anfasste. Nach dem Nachziehen im
Dev-Bestand: 438 indexiert, 23 gescheitert (die OCR-Dateien, kein `tesseract` auf
dem Host), 10 uebersprungen, und die Seite liefert zwoelf volle Anzeigeseiten.
Kein Repositoriumsstand war betroffen. **DI-09-05 ist damit geschlossen.**

## Accomplishments

- **Drei Vertragszeilen nachgezogen, jede mit Begruendung und Datum.** Sichtprobe 5
  sagt die Scrollposition nicht mehr zu und traegt beide verifizierten Ursachen
  bei sich. Der Rueckkehrvertrag nennt Stufe 2 browserabhaengig und in Firefox
  praktisch abgeschaltet und Stufe 3 tragend. Die Zeile zum fehlenden Auszug nennt
  die Zweizeiligkeit der Trefferzeile, gegen `search.php` Zeile 198 bis 208
  geprueft; dieselbe Aussage in der Trefferzeilen-Anatomie wurde mitgezogen, weil
  sie sonst weiter das Gegenteil gesagt haette. **`09-UI-SPEC.md` steht auf
  `approved`.**
- **`docs/l10n-french.md`**, 24 Zeilen, jede maschinell byte-gleich mit der
  FR-Spalte der Copy-Tabelle, jeder englische Quellstring als Schluessel in allen
  vier deutschen Katalogen nachgewiesen. Dazu die Vertagungsbegruendung und die
  fuenf Bedingungen fuer einen vollstaendigen Katalog. `ROADMAP.md` zeigt bei
  Phase 11 mit einer Zeile darauf. **DI-09-04 ist damit geordnet vertagt statt
  offen.**
- **Zwei MEDIUM-Befunde der Abnahme gefixt, jeder mit einem Test, der ohne ihn rot
  ist**, und beide Rot wurden hergestellt und nicht behauptet: der Leerzustand
  gegen das Template von `0c53c4d`, der Katalog gegen eine geloeschte und eine
  geaenderte Datei.
- **Ein dritter MEDIUM-Befund aus dem Performance-Nachlauf**: der Messbericht von
  Plan 09-01 schrieb 0,318 Sekunden Passwortpruefung dem Rechteabgleich zu.
  Abschnitt 6.3 trennt das mit fuenf frischen Reihen von je 20 Wiederholungen.
- **`docs/audits/2026-09-phase-09/README.md`**: ASVS V3, V4, V5 und V7 ueber die
  vier neuen Flaechen, alle 31 Threats der sieben Plaene namentlich abgehakt, die
  Zahlen-Randfaelle live gefahren, der Testumzug aus Plan 09-03 maschinell
  gegengelesen, sechs LOW-Befunde je mit Entscheidung und Wiedervorlage.
- **Die Seitenroute haelt ihr Budget mit Faktor 25.** p95 0,122 s gegen 3,0 s, und
  gleich gemessen ist sie 0,093 s schneller als der Dialogweg mit `limit=100`,
  nicht ein Viertel langsamer, wie die Recherche erwartet hatte.

## Task Commits

1. **Task 1: Die zwei Nachzuege und die franzoesischen Wortlaute** - `24cb778` (docs)
2. **Task 2, Vorarbeit: der Stub band nur auf Loopback** - `0c53c4d` (fix, Regel 3)
3. **Task 2, Befund M-01: der Leerzustand schweigt unter einem Banner** - `52db222` (fix)
4. **Task 2, Befund M-02: die App spricht Deutsch unter beiden Sprachcodes** - `0175b56` (feat)
5. **Task 3: die drei Audits und der Fix von M-03** - `1019930` (docs)

## Verification

| Pruefung | Ergebnis |
|---|---|
| `uv run pytest -q` (ganze Backend-Suite) | 1792 passed, 15 skipped, 140,60 s |
| `test_admin_ui_contract.py` allein | 35 passed (vorher 33) |
| `test_the_empty_state_of_the_page_does_not_speak_over_a_banner` gegen das Template von `0c53c4d` | rot, zwei Befunde |
| `test_the_german_catalogue_covers_both_german_language_codes` ohne `de_DE.json` | rot |
| dasselbe mit einem geaenderten Wert in `de_DE.json` | rot, "have drifted apart" |
| `ruff check .` / `format --check .` ueber `backend` und `../scripts` | gruen, 119 plus 10 Dateien |
| `pyright` / `vulture src tests` | 0 errors, 0 warnings / still |
| `php -l` ueber alle 46 PHP-Dateien der App im Container | keine Meldung |
| `scripts/dev/validate_info_xml.sh php/appinfo/info.xml` | gruen, Transform und Schema gegen appstore `eda850ba` |
| Blobs von `de.json` gegen `de_DE.json` und `de.js` gegen `de_DE.js` im Index | je identischer Hash |
| Die 24 FR-Wortlaute gegen die Copy-Tabelle | 24 von 24 byte-gleich |
| Die 24 englischen Quellstrings in `de.json` und `de.js` | 24 von 24 vorhanden |
| Alle 31 Threats der Plaene 09-01 bis 09-08 im Auditbericht | 31 von 31 abgehakt |
| Em-Dash, En-Dash, Emoji in allen 16 Dateien | 0 / 0 / 0 |
| Live: die fuenf Zustaende der Seite nach dem Fix M-01 | Treffer, Nullergebnis, ohne Suche, Decke, Drift: jeder genau ein Block |
| Live: `testuser` auf `de_DE` | vollstaendig deutsch, 25 Zeilen, `lang="de-DE"`, kein englischer Rest |
| Performance-Nachlauf, fuenf Reihen mit je 20 Wiederholungen | p95 0,122 s (Seite, Sitzung) gegen ein Budget von 3,0 s |

**Was nicht gefahren werden konnte, mit demselben Grund wie in den drei Plaenen
davor.** `php.yml` (PHPUnit ueber 143 PHP-Testfaelle) und `integration.yml` (der
Paritaetsjob mit dem dritten Vergleich) brauchen den Runner: auf dieser Maschine
gibt es kein PHP ausser dem im Container und keine `require-dev`-Abhaengigkeiten,
und der Paritaetsjob braucht eine frische Nextcloud samt Crawl. Der Auditbericht
sagt denselben Satz an seiner Stelle. Der erste Lauf beider Jobs gehoert an den
Push dieser Welle; das Abnahmekriterium "die gesamte CI ist gruen" ist damit
lokal so weit erfuellt, wie es lokal erfuellbar ist, und der Rest ist eine Zeile
im Protokoll des Runners.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Der verlangsamte Stub war aus dem Container unerreichbar**

- **Found during:** Task 2, Sichtprobe 10
- **Issue:** `scripts/ci/slow_backend.py` band auf `127.0.0.1`. In CI ist das
  richtig und das engere Bindeverhalten, weil Nextcloud dort auf demselben Runner
  laeuft. Auf der Entwicklungsmaschine laeuft Nextcloud im Container und erreicht
  den Hostprozess unter `host.docker.internal`; die Seite zeigte deshalb den
  Fehlerblock eines abwesenden Backends und belegte Sichtprobe 9 ein zweites Mal
  statt Sichtprobe 10 ein erstes.
- **Fix:** `FINDLING_SLOW_BACKEND_HOST` mit dem alten Wert als Standard, die
  Startzeile druckt die wirklich gebundene Adresse. Derselbe Stolperstein und
  derselbe Wortlaut wie in `scripts/dev/register-exapp.sh`, wo er gelernt wurde.
- **Files modified:** `scripts/ci/slow_backend.py`
- **Commit:** `0c53c4d`

**2. [Rule 1 - Bug] Der Leerzustand sprach ueber den Fehlerblock hinweg**

- **Found during:** Task 2, Sichtproben 9, 10 und 21
- **Issue:** Block 4 rendert, sobald die Trefferliste leer ist. Bei gestopptem
  Backend, bei Versionsdrift und jenseits der Offset-Decke stand deshalb "Keine
  Datei enthaelt X. Versuchen Sie ein anderes Wort" unter dem Banner, das gerade
  gesagt hatte, dass die Suche nicht stattgefunden hat. Der erste Block bittet zu
  warten, der zweite schickt den Nutzer den Begriff umschreiben. Erreichbar ohne
  Handarbeit, und im Pfad von Erfolgskriterium 5.
- **Fix:** Eine Entscheidung, `$showEmpty`, neben der Bannerentscheidung. Der
  Leerzustand ohne Suchbegriff bleibt unter jedem Banner stehen, weil eine
  Einladung nie eine Behauptung ist. Zeile im Zustands-Inventar nachgezogen.
- **Files modified:** `php/templates/search.php`,
  `backend/tests/test_admin_ui_contract.py`, `09-UI-SPEC.md`
- **Commit:** `52db222`

**3. [Rule 2 - Missing critical functionality] Die App sprach nur einen der zwei deutschen Sprachcodes**

- **Found during:** Task 2, Sichtprobe 20
- **Issue:** Nextcloud fuehrt `de` und `de_DE` als zwei Sprachen und liefert im
  Core fuer jede einen Katalog. Diese App lieferte nur `de`, also las jeder Nutzer
  auf `de_DE` die ganze App im englischen Quellstring, Ergebnisseite und
  Verwaltungsseite. Die Instanz hatte fuer `testuser` genau `de_DE` gesetzt.
- **Fix:** `de_DE.json` und `de_DE.js` mit denselben Worten, im Index
  byte-identisch, plus ein Gate auf die Gleichheit. Owner-Entscheid vom
  09.09.2026: in dieser Phase und nicht in Phase 11.
- **Files modified:** `php/l10n/de_DE.json`, `php/l10n/de_DE.js`,
  `backend/tests/test_admin_ui_contract.py`, `docs/store-listing.md`,
  `docs/l10n-french.md`, `09-UI-SPEC.md`
- **Commit:** `0175b56`

**4. [Rule 1 - Bug] Der Messbericht schrieb die Passwortpruefung dem Rechteabgleich zu**

- **Found during:** Task 3, Performance-Nachlauf
- **Issue:** Abschnitt 5.2 von `docs/measurements/2026-09-seitenbudget/README.md`
  ordnet "rund neun Zehntel der Zeit" dem Anfragebau, dem Vorfilter und dem
  Rechteabgleich zu. 0,318 Sekunden davon sind die Passwortpruefung der
  Messmethode, die kein angemeldeter Nutzer bezahlt. Phase 10 vergleicht Zahl fuer
  Zahl gegen diesen Bericht.
- **Fix:** Abschnitt 6.3 mit fuenf Reihen, der Trennung und dem Satz, dass zwei
  Berichte nur bei gleichem Anmeldeweg vergleichbar sind. Ohne Test, weil der
  Befund eine Aussage in einem Bericht ist und kein Verhalten von Code; dasselbe
  Vorgehen wie bei M-04 und M-06 des Phase-8-Audits.
- **Files modified:** `docs/measurements/2026-09-seitenbudget/README.md` und
  fuenf neue Rohdatendateien
- **Commit:** `1019930`

### Bewusste Auslegungen des Plans

**5. Der Abnahmestand steht auf `approved`, die sechs Zeilen des Checker-Sign-Offs
darueber bleiben offen.** Der Plan verlangt `**Approval:** approved`. Die sechs
Dimensionen anzukreuzen haette einen Checker-Lauf behauptet, den es in dieser
Phase nicht gab. Stattdessen steht unter der Zeile, was von ihnen als Text
pruefbar ist und wo es haengt (Gate C ueber sechs Dateien) und dass der Rest im
Sichtprobenprotokoll steht.

**6. Das Frontmatter der 09-UI-SPEC wurde von `draft` auf `approved` gezogen.**
Der Plan nennt nur die Zeile am Dateiende. Ein Dokument, dessen Ende `approved`
sagt und dessen Kopf `draft`, ist genau die Art Widerspruch, die dieses Audit
sonst als Befund aufschreibt.

**7. Die Zeile zum fehlenden Auszug wurde an zwei Stellen nachgezogen.** Der Plan
nennt das Zustands-Inventar. Dieselbe Aussage steht in der Trefferzeilen-Anatomie
("steht der Pfad an seiner Stelle, genau wie im Dialog"), und sie dort stehen zu
lassen haette einen Vertrag ergeben, der sich auf zwei Seiten selbst widerspricht.

**8. Der Bericht liegt unter `docs/audits/` und nicht bei der Phase.** Der Plan
gibt den Pfad vor, und es ist der erste Bericht dort; die vier fruehreren liegen
bei ihren Phasen unter `.planning/`. Die Struktur des Phase-8-Audits ist
fortgeschrieben, einschliesslich Frontmatter, LOW-Entscheidungen und
"Was ausdruecklich in Ordnung ist".

**9. Die Umgebung der Sichtproben wurde hergestellt, bevor sie gefahren wurden.**
Das Backend lief nicht, und der Dev-Bestand indexierte nicht. Beides gehoert nach
dem Checkpoint-Protokoll zur Vorbereitung einer human-verify-Probe und nicht in
die Probe selbst. Angefasst wurde ausschliesslich `.dev/`, keine Repositoriumsdatei.

## Threat Model

| Threat ID | Umsetzung |
|---|---|
| T-09-28 (Repudiation, nicht dokumentierte Abweichung einer Sichtprobe) | Das Protokoll oben fuehrt alle 22 Proben. Drei Abweichungen sind als solche benannt und gefixt, die sechs Augen-Proben tragen das Datum ihrer Owner-Abnahme. Kein "nicht durchfuehrbar" musste stehen bleiben, weil die Ursache aus DI-09-05 gefunden und behoben wurde |
| T-09-05 (Information Disclosure, Rueckschluss auf verworfene Kandidaten) | Sichtprobe 22 stellt beide Faelle gegeneinander: 25 genehmigte gegen eine genehmigte von vielen Kandidaten, und keine Seite traegt einen Satz, eine Zahl oder ein Symbol darueber. Das Security-Audit prueft dieselbe Frage am Quelltext und benennt die eine Restaussage (der Weiter-Knopf haengt an `hasMore`) als L-04 |
| T-09-17 (Information Disclosure, falsche Fehlermeldung an der Offset-Decke) | Live gegen 1200 und 1201 gefahren: bei 1200 findet die Suche statt, bei 1201 erscheint das Hinweisbanner zur Obergrenze und nicht der Fehlerblock. Der Leerzustand darunter war Befund M-01 und ist weg |
| T-09-29 (DoS, voller Vektorscan je Anzeigeseite) | accept, wie geplant, und der Bericht entscheidet gegen eine Massnahme mit Begruendung: auf dieser Instanz gibt es keine `vectors.db`, der zweiwortige Fall ist hier lexikalisch, und die Zahlen fuer den hybriden Fall (p95 524 ms) stehen im Semantiklauf-Bericht. Wenn eine Massnahme begruendbar wird, dann mit den Zahlen der Phase 10 |
| T-09-30 (Tampering, verlorener Testfall beim Umzug) | Maschinell gegengelesen: 14 alte Faelle, 7 unveraendert vorhanden, 7 umbenannt, jedes der 16 Ziele der Zuordnungstabelle existiert, kein alter Name ohne Erklaerung. Heute 16 plus 21 Faelle in den zwei Klassen |
| T-09-SC (Supply Chain) | Kein Paket installiert. `git diff --name-only` ueber alle Abhaengigkeitsdateien der Phase liefert keine Zeile, und genau dieser Blick in den Diff war der Auftrag |

Neue Angriffsflaeche dieses Plans: keine. Er legt keine Route an, keinen Endpunkt
und keinen Schreibvorgang. Die zwei neuen Katalogdateien sind Daten, die
Nextcloud liest, und ihr Inhalt ist byte-identisch mit dem, der seit Phase 4
ausgeliefert wird.

## Notes for Future Phases

- **Die Abnahme hat gefunden, was die Gates nicht fanden.** Zwei der drei
  MEDIUM-Befunde kommen aus dem Sichtprobenprotokoll und keiner aus einem Test.
  Fuer die Launch-Haertung der Phase 11 heisst das: die Sichtproben sind nicht die
  Zeremonie nach der Arbeit, sie sind ein eigener Fund-Kanal.
- **Phase 10 vergleicht gegen `docs/measurements/2026-09-seitenbudget/` und muss
  Abschnitt 6.3 lesen, bevor sie eine Zahl uebernimmt.** Basic-Auth kostet auf
  dieser Instanz 0,318 s je Anfrage; zwei Berichte sind nur bei gleichem
  Anmeldeweg vergleichbar.
- **Der franzoesische Katalog ist die einzige offene Vorbedingung der Abgabe, die
  aus dieser Phase kommt.** `docs/l10n-french.md` traegt die Wortlaute und die
  fuenf Bedingungen, die ROADMAP zeigt bei Phase 11 darauf. Anders als bei Deutsch
  ist es dort **keine** Dateigleichheit: Franzoesisch kennt die Du-Sie-Teilung der
  beiden deutschen Codes nicht.
- **Wer die Drift-Sichtprobe nachfaehrt, setzt den Schluessel danach auf leer und
  wartet ein paar Sekunden.** `occ config:app:delete` erreichte den Webprozess
  nicht sofort, `occ config:app:set` schon; die Instanz zeigte danach einen
  Fehlerblock ueber eine Drift, die es nicht mehr gab.
- **`de_DE` ist ab jetzt eine Datei, die mitwaechst.** Wer einen Schluessel in
  `de.json` anlegt und `de_DE.json` vergisst, faellt ueber
  `test_the_german_catalogue_covers_both_german_language_codes`, und zwar mit dem
  Satz "have drifted apart" und nicht mit einer halb deutschen Oberflaeche.

## Deferred Issues

| Id | Punkt | Warum offen |
|---|---|---|
| DI-09-06 | `docs/testing.md` beschreibt den Paritaetsjob noch als Vergleich zweier Antworten und kennt die dritte Menge nicht | Unveraendert aus Plan 09-07 und ausserhalb der Dateiliste dieses Plans. Gehoert in Phase 11, wo die Doku fuer die Abgabe ohnehin durchgesehen wird |
| DI-09-07 | `docs/certificates.md` nennt 67 Archiveintraege; die Zahl stammt aus einem Release-Lauf vor den Phasen 5 bis 9 und ist um die zwei neuen Kataloge staler geworden | L-02 des Auditberichts. Eine geratene Zahl waere schlechter als eine erkennbar alte; der Release-Lauf der Phase 11 druckt die richtige |
| DI-09-08 | Ein laufender Indexlauf kann eine Suche in den Fehlerblock schicken (einmal beobachtet unter etwa 45 Abrufen) | L-05 des Auditberichts. Aeltere Eigenschaft des Worker-Loops, der Dialog ist genauso betroffen, ein Fix waere eine Aenderung am Loop und damit ein eigener Plan. Wiedervorlage: Phase 11, Ressourcengrenzen |

**Geschlossen mit diesem Plan:** DI-09-02 (die Abnahme-Sichtproben, alle 22 sind
gefahren), DI-09-03 (Sichtprobe 5 ist umformuliert und begruendet), DI-09-04 (die
franzoesischen Wortlaute liegen in `docs/l10n-french.md`, die Vertagung ist
entschieden und die ROADMAP zeigt darauf), DI-09-05 (die lokale Instanz indexiert
wieder, Ursache gefunden).

## Self-Check: PASSED

- `docs/l10n-french.md`, `docs/audits/2026-09-phase-09/README.md`,
  `php/l10n/de_DE.json` und `php/l10n/de_DE.js` liegen auf der Platte.
- `09-UI-SPEC.md` traegt `**Approval:** approved (09.09.2026, Plan 09-08)` und
  `status: approved` im Frontmatter.
- `.planning/ROADMAP.md` nennt bei Phase 11 den Pfad `docs/l10n-french.md`.
- Die fuenf Commits `24cb778`, `0c53c4d`, `52db222`, `0175b56` und `1019930`
  stehen in `git log`.
- Der Arbeitsbaum war vor dem Schreiben dieser Datei sauber.
