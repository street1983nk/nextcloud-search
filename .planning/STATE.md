---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Qualitaet und Effizienz
status: executing
stopped_at: Abgeschlossen 11-05-PLAN.md, die vollstaendige FR-Uebersetzungstabelle und das FR-Gate Teil 1 (abgenommen 2026-09-11, keine Korrektur). Welle 3 ist damit zu, Welle 4 offen
last_updated: "2026-09-11T03:20:00.000Z"
last_activity: 2026-09-11
progress:
  total_phases: 5
  completed_phases: 4
  total_plans: 37
  completed_plans: 33
  percent: 89
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-15)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 11 — Haertung und Store-Einreichung v1.1

## Current Position

Phase: 11 (Haertung und Store-Einreichung v1.1) — EXECUTING
Plan: 7 of 13
Status: 11-05 abgeschlossen, Welle 3 ist zu, Welle 4 steht an
Last activity: 2026-09-11

**Naechster Schritt:** Welle 4. Plan 11-05 ist am 11.09.2026 gefahren und
abgeschlossen, und damit ist **Welle 3 vollstaendig**: `docs/l10n-french.md`
traegt eine dreispaltige Tabelle ueber alle 174 Katalogschluessel (173 Zeilen
plus `Findling` als benannte Ausnahme), 24 Wortlaute woertlich aus Phase 9 und
149 neu, und der Owner hat sie als franzoesischer Muttersprachler am
**2026-09-11 ohne eine einzige Korrektur** abgenommen. Die Abnahmezeile steht
datiert in derselben Datei, die 11-08 giessen wird, und nennt sich ausdruecklich
**Teil 1 von 2 (Katalog)**; Teil 2 (Store-Text, `README.fr.md`, die
franzoesischen Teile von `info.xml`) ist Plan 11-09. **Fuer 11-08 gilt drei
Dinge:** die FR-Spalte ist der Wert, ` / ` trennt Singular und Plural und kommt
in genau den fuenf Pluralzeilen vor, und **`Findling` ist der 174. Wert und steht
nicht in der Tabelle, sondern in der Ausnahmenliste** , wer nur die Tabelle
liest, baut ein `fr.json` mit 173 Schluesseln und laesst Gate G1 rot werden. Der
Grund ist ein in 11-05 benannter Befund: `Findling` ist entgegen der bisherigen
Aussage der Datei Schluessel 1 von 174 in `de.json`. Die Pluralregel fuer G4
lautet `nplurals=2; plural=(n > 1);` und steht als Wortlaut in der Datei, die
zweite G2-Ausnahme ist `Page %s`. Die drei Stellen, an denen die Datei noch 173
nannte (Uebergabe aus 11-13), sind in 11-05 bearbeitet und **nicht** an 11-10
weitergereicht worden. **REL-01 bleibt ungehakt.** Plan 11-07
ist am 11.09.2026 gefahren und abgeschlossen: `deploy-harp.yml` faehrt auf dem
ist am 11.09.2026 gefahren und abgeschlossen: `deploy-harp.yml` faehrt auf dem
Ast `stable34/ubuntu-24.04` einen Upgrade-Block (`Store upgrade 0` bis
`Store upgrade 5`), der beide Haelften aus den echten v1.0.3-Release-Assets
installiert, den 39-Datei-Korpus indexiert, auf den HEAD-Stand upgradet und
sechs Dinge zusichert. Lauf **34546421219**, erster Anlauf gruen, alle vier
Aeste: Treffer je 1 fuer Belehrung, Auszug und Erinnerung, `docs` 29,
`indexed` 29, `skipped` 7, `failed` 6, Arbeitsvorrat 0, alle fuenf Marken
identisch (schema/index/analyzer je 1, wordlistHash `b1f64012...`, tantivy
v0.26.0 index_format v7), kein Reindex-Banner, keine
`start_rebuild_on_drift`-Zeile, und der Navigationseintrag aus 09-06 vorher
abwesend und nachher da. Damit ist **Erfolgskriterium 2 der Phase** mit einer
Laufnummer belegt statt mit einer Code-Lesung. Der Block kostet 1 min 32 s bei
32 min 21 s Abstand zu `timeout-minutes: 45`, das also unveraendert bleibt.
Fuer 11-11 heisst das zweierlei: bis zum Versionsbump tragen beide `info.xml`
weiterhin 1.0.3, `occ upgrade` antwortet deshalb `No upgrade required.`, und
der Schritt haelt beide Zweige bereit; ab dem Bump verlangt er, dass
`installed_version` wirklich nachzieht. **REL-01 bleibt ungehakt.** Die EINE
Box-Anfahrt (11-06) ist am 10.09.2026 gefahren und abgeschlossen: DI-10-01 ist
geschlossen (16 Anfragen ohne Treffer plus 14 Abbrueche ergeben die 30 des neuen
Zaehlers, aufgerechnet gegen das Nextcloud-Protokoll), DI-10-02 ist NICHT
geschlossen (die Vorpruefung des Fremdbestands misst einen Antwortdeckel von 26
und kann die Schwelle 64 nie erreichen, Beleg in
docs/measurements/2026-09-werkzeugfixe/rohdaten/07-fremdbestand-gegenprobe.txt).
Die Box ist angehalten, 1,97 h und 0,2285 USD gegen den Deckel 4 h / 0,50 USD.
Drei neue Befunde stehen in der deferred-items.md der Phase: DI-11-01 (die
Messgroesse der Vorpruefung), DI-11-02 (eine leere Antwort ohne Protokollspur,
mit dem 11-13-Fix pruefbar) und DI-11-03 (der Zaehler unterscheidet leer nicht
von abgebrochen). Fuer 11-11 heisst das: der Bestand auf der Box lautet jetzt
52.137 / 44 / 6, nicht mehr 52.111 / 37 / 0, und die Differenz von 39 ist der
Sprachfall-Korpus. Plan 11-13 ist am 10.09.2026
gefahren und abgeschlossen: der Zustand
`SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED` steht im Dienst, der Satz
"Andere Dateien enthalten dieses Wort, aber keine, die Sie oeffnen duerfen."
auf der Ergebnisseite, und `php/l10n/de.json` traegt 174 statt 173 Schluessel.
Fuer 11-05 heisst das: die franzoesische Abdeckung zaehlt 174, und der 174.
Schluessel ist `Other files contain this word, but none that you may open.`
Fuer 11-08: das Gate steht bereits auf 174. Fuer 11-10: DI-07-03 ist
MEDIUM-gefixt, die Berechtigungskette am Diff unveraendert. Der Planzaehler
steht weiter bei 5, weil 11-13 als bedingter Plan der Welle 2 vorgezogen
gefahren ist und 11-05 noch aussteht. 11-04 hat die
Lesart v2-a vollzogen (Matrix und beide `info.xml` unveraendert, Entscheid als
datierter Absatz in `deploy-harp.yml`), 11-11 faehrt sie weiter. Seit 11-04
gilt fuer `deploy-harp.yml`: die Store-Install-Strecke faehrt auf vier Aesten,
einer davon nativ auf `ubuntu-24.04-arm`, und `workflow_dispatch` nimmt eine
Eingabe `release_tag`, die beide Archive vom GitHub-Release laedt statt sie zu
bauen (leer = Alltagsfall, unveraendert). Die Nachverfolgung des
`RE-CHECK DATE: 2026-09-16` am stable35-Ast liegt jetzt bei Plan 11-11.
Fuer jeden kuenftigen Lauf
des Lastwerkzeugs gilt seit 11-02: die Vorgabe von `--min-hits` ist 1, ein Lauf
gegen einen Bestand ohne die zehn festen Begriffe braucht `--min-hits 0`, und
der gefahrene Wert steht als `min_hits` im Bericht. Seit 11-03 gilt fuer die
Sprachfaelle: die Nachfolgefassung liegt unter
`docs/measurements/2026-09-werkzeugfixe/skripte/98b-sprachfaelle.sh`, sie
verlangt `CI_LAUF` als Pflichteingabe (sonst Rueckgabewert 22) und das
Lasttest-Passwort fuer die Vorpruefung (sonst 19), und die gefahrene Fassung
unter `2026-09-vergleichsmessung-m7g/` ist per sha256 gegen Bearbeitung
verriegelt.

## Was Phase 10 geliefert hat

Der Messbericht liegt in `docs/measurements/2026-09-vergleichsmessung-m7g/README.md`,
19 Abschnitte, 1.070 Zeilen, 154 Verweise auf Rohdateien, in der Struktur des
v1.0-Berichts. Der Owner hat ihn am **2026-09-10** abgenommen, ohne eine Zahl
zu beanstanden.

Die Kernzahlen, jede gegen ihre Entsprechung aus 06-11:

- **Grundlast im Leerlauf 103,2 MB gegen 691,8 MB**, minus 588,6 MB (MESS-01)
- **anon-Spitze 1.764,2 MB gegen 1.837,8 MB**, alle drei Schadenszaehler auf
  null, `OOMKilled=false`, `RestartCount=0`

- **`memory.events max` 21.939 gegen 2.796**, `memory.peak` gleich der harten
  Grenze; der Zaehler gehoert dem Indexaufbau und steht nach dem Neustart auf 0

- **p95 Stufe 8 = 2.125,5 ms gegen 2.500 ms Budget**, die Zusage haelt, aber
  die Reserve faellt von 585,0 auf 374,5 ms (MESS-02)

- **Laufzeit 26 h 37 min gegen 18 h 56 min**, plus 40,6 Prozent, Untergrenze
- **52.111 indexiert**, 146.171 Chunks, 1.318,3 Byte je Dokument; 52.111 minus
  150 Drill-Dateien ergibt exakt die 51.961 der Grundlinie

**MESS-01, MESS-02 und MESS-03 sind abgehakt** mit Belegpfad und Kernzahl.
**Erfolgskriterium 2 der Phase steht ausdruecklich auf "teilweise belegt"** und
ist nicht aufgerundet worden (Owner: "So lassen"): vier von fuenf Laststufen
sind regressiv, und die Sprachfaelle stehen auf 6 von 10 mit
Mess-Setup-Vorbehalt.

Das Audit-Gate der Owner-Regel vom 15.08.2026 ist gefahren
(`docs/audits/2026-09-phase-10/README.md`): V2, V3, V4, V7 und V14 je mit
Beleg, alle 47 Threats abgehakt, ein MEDIUM behandelt, fuenf LOW entschieden,
kein CRITICAL und kein HIGH. Die Phase hat **keine Zeile Produktionscode**
geaendert; `git diff af18542..HEAD` nennt keine Datei unter `php/` oder
`backend/src/`.

## Die Box

**Angehalten am 2026-09-10T16:22:50Z**, nicht abgebaut.
`BOX_LAST_UPTIME_HOURS=31.05`, `BOX_LAST_UPTIME_COST_USD=3.5969`, also unter
dem angehobenen Deckel von 34 Stunden und 4,00 USD. Zustand `stopped` um
16:23:15Z aus der API geprueft. Parkkosten 0,3130 USD je Tag; beide
Datentraeger bleiben, mit Korpus, beiden Indizes und den Abbildern.

Beim naechsten Start: die oeffentliche Adresse wechselt, `BOX_IP` und der
A-Record `loadtest.infranode.dev` sind nachzuziehen, und der Container muss
ueber AppAPI neu bewaffnet werden (DI-05-36), sonst indexiert er nicht.

## Was Phase 11 mitbekommt

| ID | Was |
|---|---|
| **REL-01** | Store-Einreichung v1.1, und mit ihr der Nachzug der Messzahlen in `README.md` und `docs/store-listing.md` (DI-10-03). **Merker: eine Messzahl steht an drei Stellen**, `README.en.md` plus beide `info.xml`, und ein Gate haelt sie deckungsgleich |
| **DI-07-02** | Die Entscheidung ueber `REQUEST_TIMEOUT_SECONDS`. Kaltstart auf vollem Bestand 1.838,4 ms gegen 1.500 ms, Marge minus 338,4 ms; der Abbruch ist bei kaltem Wirtscache belegt (`cURL error 28`). Eine hoehere Decke laesst jeden Nutzer laenger warten |
| **DI-07-03** | Die Schleife des Rechteabgleichs holt keine zweite Runde nach; ein Nutzer mit wenigen Dateien findet sie neben grossem Fremdbestand nicht und bekommt eine leere Liste statt einer Meldung |
| **DI-10-01** | `search_load.py` zaehlt abgebrochene Containeraufrufe als Erfolge (17 in Stufe 16 bei `failures: 0`). **Werkzeugseitig behoben in 11-02** (`EmptyResultGroup`, `--min-hits`, `hits_per_request`); der Beweis gegen echte Last steht in 11-06 aus, das Schliessen im Audit 11-10 |
| **DI-10-02** | Der Messaufbau der Sprachfaelle trennt die Berechtigung und nicht den Index |
| **DI-10-04** | Welcher Kandidat die Mehrlaufzeit traegt: Kopplung der Spuren oder Zulauf-Luecken |
| **DI-10-05** | Darf ein Messlauf gegen den wandernden Tag `:dev` pruefen? |
| **T-09-29** | Wiedervorlage bei einem deutlich groesseren Vektorbestand als 146.171 Chunks |

## Performance Metrics

**Velocity:**

- Total plans completed: 94
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 8 | - | - |
| 02 | 14 | - | - |
| 03 | 14 | - | - |
| 04 | 10 | - | - |
| 06.1 | 24 | - | - |
| 7 | 4 | - | - |
| 09 | 8 | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 04 P01 | 12 min | 2 tasks | 3 files |
| Phase 04 P02 | 10 min | 2 tasks | 7 files |
| Phase 04 P03 | 47 min | 3 tasks | 15 files |
| Phase 04 P04 | 25 min | 3 tasks | 9 files |
| Phase 04 P05 | 21 min | 3 tasks | 12 files |
| Phase 04 P06 | 22 min | 3 tasks | 9 files |
| Phase 04 P07 | 25 min | 3 tasks | 16 files |
| Phase 04 P08 | 33 min | 3 tasks | 16 files |
| Phase 04 P09 | 22 min | 3 tasks | 14 files |
| Phase 04 P10 | 19 min plus Sichtprobe | 3 tasks | 11 files |
| Phase 06 P01 | 35min | 3 tasks | 14 files |
| Phase 06 P03 | 3h05m | 3 tasks | 8 files |
| Phase 06 P02 | 2h05m | 3 tasks | 37 files |
| Phase 6 P04 | 30min | 3 tasks | 8 files |
| Phase 6 P05 | 30min | 3 tasks | 8 files |
| Phase 6 P06 | 35min | 3 tasks | 12 files |
| Phase 6 P07 | 38min | 3 tasks | 12 files |
| Phase 6 P08 | 16min | 2 tasks | 6 files |
| Phase 6 P09 | 33min | 3 tasks | 15 files |
| Phase 6 P10 | 32min | 3 tasks | 7 files |
| Phase 09 P05 | 55min | 3 tasks | 5 files |
| Phase 09 P06 | 40min | 3 tasks | 8 files |
| Phase 09 P07 | 50min | 3 tasks | 4 files |
| Phase 09 P08 | 75min | 3 tasks | 16 files |
| Phase 10 P01 | 42min | 3 tasks | 4 files |
| Phase 10 P02 | 25min | 2 tasks | 6 files |
| Phase 10 P03 | 28min | 3 tasks | 8 files |
| Phase 10 P04 | 34min | 3 tasks | 10 files |
| Phase 10 P05 | 80min Sitzung, dazwischen 27h06m Lauf | 4 tasks | 33 files |
| Phase 10 P06 | 2h10m | 5 tasks | 13 files |
| Phase 10 P07 | 2h40m | 4 tasks | 12 files |
| Phase 11 P01 | 30min | 2 tasks | 1 files |
| Phase 11 P02 | 25min | 3 tasks | 3 files |
| Phase 11 P03 | 35min | 3 tasks | 3 files |
| Phase 11 P04 | 70min | 3 tasks | 1 files |
| Phase 11 P13 | 35min | 3 tasks | 14 files |
| Phase 11 P07 | 55min | 2 tasks | 1 files |
| Phase 11 P05 | 30min | 2 tasks | 1 files |

## Accumulated Context

### Roadmap Evolution

- Phase 06.1 inserted after Phase 6: Launch-Haertung vor der Store-Abgabe (Owner-Regel 06.09.2026): ausgiebige Tests jenseits des Happy Path, laeuft VOR Plan 06-12 (URGENT)

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: EIN Store-Erstrelease 1.0.0 mit Volltext, OCR und Semantik. Phasen 1 bis 5 stellen den einreichungsbereiten Zustand her (D-09), Phase 6 ergänzt die Semantik, die Abgabe ist Abschluss von Phase 6 (D-08), hart vor Jahresende 2026 (D-10). Die frühere Staffelung v1.0 jetzt und v1.1 vier bis sechs Wochen später ist überholt und nur noch Fallback
- Roadmap: ACL-Tabelle liegt im ersten Storage-Schema (Phase 2), nicht nachgerüstet
- Roadmap: Integrationsbeweis (IProvider + exAppRequest) steht vor jedem Feature, App-IDs und beide CSRs in Phase 1
- Engine: Tantivy 0.26 plus SQLite-ACL-Vorfilter, finaler PHP-Recheck ist die Sicherheitsgrenze
- OCR strikt index-only, Nutzerdateien werden nie verändert (CI-Prüfsummen-Gate ab Phase 1)
- [Phase 04]: Gate B kennt zwei Routenklassen: ApiRoute (ExApp, ExAppRequired plus rejectForeignCaller) und FrontpageRoute (Admin, kein Zugriffsattribut). Begruendung: Phase 4 legt den ersten PHP-Controller ohne ExAppRequired an; die Klassentrennung musste vor dem Controller stehen, sonst steht der Baum zwischendurch rot
- [Phase 04]: Eine Route mit beiden Attributnamen gilt als Admin-Route. Begruendung: die Admin-Klasse ist die strengere, also wird Vermischung gemeldet statt durchgelassen
- [Phase 04]: php/templates wird per .gitkeep offengehalten, statt den find-Pfad des php -l-Jobs tolerant zu machen. Begruendung: jede tolerante Schreibweise laesst das Gate stumm weniger pruefen als es behauptet
- [Phase 04]: Der Container meldet maxFileBytes aus settings() auch ohne Zustandsdatenbank, damit die PHP-Einstellung an den wirklich durchgesetzten Deckel geklemmt wird
- [Phase 04]: Die Aufteilung der Wahrheit steht woertlich in beiden Docblocks: skipped, failed und die Fehlerliste aus findling_file_state, indexed, truncated, Platz und Versionsmarken aus dem Container
- [Phase 04]: access_level ADMIN deckt nur den AppAPI-Proxy-Weg; der wirksame Schutz der Admin-Seite ist die PHP-Route ohne NoAdminRequired
- [Phase 04]: Der Override-Attribut-Verzicht in den neuen Settings-Klassen: PHP 8.3 gegen die deklarierte min-version 8.2
- [Phase 04]: Die Statuszeile nennt keine Restzeit, solange kein kalibrierter Durchsatz existiert (kein Schaetzwert, der wie eine Messung aussieht)
- [Phase 04]: indexedDisplay waehlt zwischen Container- und Nextcloud-Zahl statt zu verrechnen, damit keine Kachel wegen einer gescheiterten Abfrage auf 0 springt
- [Phase 04]: Stockt-Schwelle 1800 Sekunden, sechs verpasste Runden des Fuenf-Minuten-Systemcrons
- [Phase 04]: SettingsController erweitert Controller und nicht OCSController, damit die Route ausserhalb des OCS-Raums bleibt
- [Phase 04]: Der Nenner des Deckungsgrads entsteht im Crawl (filesSeen minus overCap minus excluded) und nie aus einer zweiten Abfrage; die Subtraktion steht genau einmal in AdminViewService
- [Phase 04]: Idempotenz der Scan-Zaehler nach Variante (a): beginStorage setzt die Zeile bei last_file_id gleich 0 zurueck; der Cursor-Vergleich je Datei wurde verworfen
- [Phase 04]: pdf_seen ist eine eigene Spalte, weil der OCR-Anteil vor dem Lauf ein Intervall ist und keine Zahl
- [Phase 04]: percent ist auch bei stummem Backend null; 0 Prozent Deckung wird nie als Aussage gerendert
- [Phase 04]: Alle Gestalten des Deckungsgrad-Blocks liegen im Markup und werden ueber hidden geschaltet, damit die Kopfzahl ohne Neuladen erscheinen kann und das Skript kein Markup baut
- [Phase 04]: Top-Level-Schluessel indexable entfaellt aus overview(); die Zahl lebt nur noch unter coverage
- [Phase 04]: Der Durchsatz wird gemessen statt vorhergesagt: GET /rates meldet Text- und OCR-Rate getrennt ueber ein geklemmtes Fenster, und die Seite rechnet daraus hoch (ARM-Faktor unbekannt)
- [Phase 04]: Startwerte sind ein eigenes Feld (startupValues) und keine stille Annahme; die Seite beschriftet die Dauer entsprechend
- [Phase 04]: Der OCR-Anteil bleibt ein Intervall, bis die Haelfte der indexierbaren Dateien ein Verdikt hat (MEASURED_OCR_FROM_JUDGED_PERCENT)
- [Phase 04]: Der Platzbedarf entsteht aus backend.indexBytes durch backend.docs und nicht aus dem Quotienten von /rates, damit die Zahl einen gescheiterten /rates-Aufruf ueberlebt
- [Phase 04]: Bei firstIndexDone wird /rates nicht mehr aufgerufen, weil der Block nicht gerendert wird
- [Phase 04]: Ohne gezaehlte Dateien zeigt Block 2 keine Nullzeile, sondern nur den Zaehl-Hinweis
- [Phase 04]: Die Label- und Abhilfe-Abbildung fuehrt 20 Grundcodes, obwohl FileStateService::REASONS 19 hat: excluded steht schon im UI-Vertrag und kommt mit Plan 04-08 in alle drei Grundlisten
- [Phase 04]: page() liest einen null-Grund als kein Filter; MAX_PAGE 50 und 20 Beispiele je Gruppe sind Auflösungskosten und ausdruecklich nicht der MAX_LIST_LENGTH-Gotcha aus CR-01
- [Phase 04]: Beispielpfade werden im Poll nie neu gebaut, nur die Gruppenzahlen, damit geoeffnete Gruppen und Tastaturfokus erhalten bleiben
- [Phase 04]: Aufklapp-Buttons liegen hidden im Markup und werden vom Skript sichtbar gemacht: ohne JavaScript alle Gruppen offen und kein totes Bedienelement
- [Phase 04]: Vorrangregel als Kette ueber sechs benannte Stufen; der Container wird einmal vor der Kette gefragt: Stufe 1 braucht den Grabstein, um geloescht von nie gesehen zu trennen, Stufe 5 das Verdikt; zwei Aufrufe waeren ein zweiter Roundtrip fuer dieselbe Antwort
- [Phase 04]: Wartet oder laeuft entscheidet die Restsperrzeit, nicht eine leere Sperrspalte: Eine freie Zeile traegt die Epoche statt NULL (Perf-Audit H3) und ein abgelaufener Anspruch ist ohne Schreibvorgang wieder frei
- [Phase 04]: App-Version bleibt bei 0.3.0, obwohl der Container eine fuenfte Route bekam: Plan 04-05 hat beide Haelften schon angehoben und beide Plaene liegen im selben Release; ein zweiter Bump haette docker.yml gegen ein nie geschnittenes Git-Tag laufen lassen
- [Phase 04]: Der Ausschluss wird von den Aufrufern angewandt, nicht von der Aufzaehlung: getFilesInMount und getFileSlice liefern jede Zeile, Crawl und Event-Listener rufen den einen Helfer isExcluded. Ein Filter in getFilesInMount haette den Crawl an einem ausgeschlossenen Ordner beendet, die Kachel Ausgeschlossen dauerhaft auf 0 gehalten und die Raeumung von Plan 04-09 gegen genau ihren Zielordner wirkungslos gemacht; ein Filter in getFileSlice haette ueber die final-Marke des Reconcile den Index eines ganzen Mounts geleert.
- [Phase 04]: Kein Config-Lexicon registriert: die Schnittstelle wurde innerhalb des Versionsfensters 32 bis 35 umbenannt, und eine Klassenreferenz, die nur auf einem Teil der Server aufloest, waere ein fataler Fehler beim Booten statt eines fehlenden Komforts. SettingsService und ExclusionService validieren stattdessen defensiv in beide Richtungen.
- [Phase 04]: The clearing of a new exclusion covers every mount the app walks, not only home mounts: The enforcement compares a prefix relative to the root of every mount in the list, and clearing fewer mounts than the crawl excludes would leave index content that nothing removes
- [Phase 04]: The diagnosis is fed the internal path plus the storage instead of the display path: A Team Folder file arrives as TeamX/x.pdf in the display space and as x.pdf in the space the crawl compares, so the display path would be a second path space
- [Phase 04, Sichtprobe]: Erfolgskriterium 3 ist trotz Wortlaut-Abweichung angenommen: die Seite sagt "Vorlaeufige Zahl, X von Y Speicherorten sind durchgezaehlt" statt der D-05-Formulierung und nennt zusaetzlich ausdruecklich, dass auf keine Bestaetigung gewartet wird. D-05 ist der Sache nach erfuellt (Owner-Entscheidung a)
- [Phase 04, Sichtprobe]: Sichtprobe 4 wird per Gap-Closure geschlossen: Skip-Verdikte des Containers werden nicht pro Datei uebergeben, nur Fehler; die Fehlerliste kann sie deshalb nicht gruppieren, die Pro-Datei-Diagnose beantwortet sie sehr wohl (Owner-Entscheidung b, DI-04-03)
- [Phase 04, Sichtprobe]: Ein Ausschluss ist kein Fehler: Kachel, gesenkter Nenner und Diagnose sind der Nachweis, die Fehlerliste bleibt eine Liste von Fehlern (Owner-Entscheidung c zu Sichtprobe 7)
- [Phase 04, Sichtprobe]: Jeder Block besitzt seine eigene [hidden]-Regel, weil eine spezifische display-Regel die User-Agent-Regel des Attributs schlaegt; das Attribut ist seit 04-03 der einzige Schaltmechanismus der Seite
- [Phase 04, Sichtprobe]: Eine Zahl, die die Seite zu halten verspricht, wird dort gemerkt, wo sie wahr war (SettingsService::rememberIndexedCount in appconfig, Schreiben nur bei Aenderung), statt aus einer Tabelle neu berechnet zu werden, die sie bauartbedingt nicht enthaelt
- [Phase 6]: 06-01: A12 positiv, vec0-KNN laeuft unter PRAGMA query_only = 1 auf amd64 und arm64; die Leseseite von repo.py behaelt ihr Pragma
- [Phase 6]: 06-01: A13 positiv, die CPython-Uebersetzung im Abbild traegt enable_load_extension; keine eigene Python-Uebersetzung noetig
- [Phase 6]: 06-01: load_extension muss vor PRAGMA query_only laufen, und sqlite-vec braucht vec_int8() an der Aufrufstelle statt eines nackten Blobs
- [Phase 6]: 06-01: onnx ist eine reine Baugruppe (dependency-group quantize), weil onnxruntime.quantization es importiert und die Laufzeit es nicht tragen soll
- [Phase 6]: 06-01: der Docker-Bau braucht ab jetzt --build-context scripts=./scripts, weil die Modellstufe scripts/dev/quantize_model.py ruft
- [Phase 6]: 06-03: D-05 beantwortet: die E5-Praefixe wirken, 21 bis 31 von 42 Faellen je Sprache bekommen mit Praefix einen anderen Rang; sie helfen aber nur auf Deutsch, und keiner der drei Unterschiede ist von Rauschen zu trennen
- [Phase 6]: 06-03: D-02 gespalten beantwortet: die selbst quantisierte int8-Fassung traegt auf Deutsch (+2,30 Prozent MRR) und Englisch (+5,70 Prozent), auf Franzoesisch faellt sie um 9,24 Prozent und reisst damit die 5-Prozent-Abbruchregel des Plans
- [Phase 6]: 06-03: Die Vektorquantisierung (zweite Stufe, int8 in vec0) kostet auf dem Testset nichts Messbares: keiner der sechs Vergleiche erreicht den doppelten Standardfehler
- [Phase 6]: 06-03: Die lokal erzeugte int8-Datei ist byteidentisch mit der im Abbild aus Plan 06-01; quantize_dynamic ist ueber getrennte Laeufe reproduzierbar
- [Phase 6]: 06-02: D-04 greift nicht. Der gemessene x86/ARM-Faktor fuer Messung B ist hoechstens 1,20 gegen Abbruchschwellen von 5,5 und 9,6; der gedeckelte Erstindex dauert auf nativem aarch64 2 h 58 min bis 4 h 09 min statt der geschaetzten 7 bis 24 Stunden. Owner-Abnahme 05.09.2026: weiter wie geplant, potion bleibt zu, D-04 unangetastet
- [Phase 6]: 06-02: A1 ersetzt (3,2947 bis 3,2972 Zeichen je Token fuer laufende deutsche Prosa, 4,0452 fuer reines Vokabular; geschaetzt waren 3,5), A2 und A3 ersetzt (3.519 bis 4.809 Token je Sekunde auf zwei gepinnten aarch64-Kernen; geschaetzt waren 800 bis 2.000)
- [Phase 6]: 06-02: Unter dem Deckel aus D-01 entscheidet A1 die Laufzeit nicht mehr, sondern nur die Abdeckungszusage aus D-17b: 51.269.632 Token und 100.136 Chunks unabhaengig vom A1-Wert, gemessener Abdeckungsanteil 12,5 statt 13,2 Prozent eines durchschnittlichen Dokuments
- [Phase 6]: 06-02: int8 mit brute force haelt das Zeitbudget auf beiden Architekturen: bei 100.136 Chunks 37,8 ms p95 warm und 153,5 ms kalt je Runde gegen 300 ms, also 4,5 bis 18,4 Prozent des 2,5-Sekunden-Budgets bei MAX_ROUNDS = 3. D-10 und D-08 bleiben richtig
- [Phase 6]: 06-02: Der Tokenizer ist architekturunabhaengig, belegt statt behauptet: die Tokenzahlen auf aarch64 und x86_64 stimmen in allen drei Textsorten auf das letzte Token ueberein (142.396, 163, 247.204)
- [Phase 6]: 06-03: D-02 BESTANDEN nach Owner-Entscheid vom 05.09.2026. Die Abbruchregel wird auf die ausgelieferte Kombination bezogen (int8-Modell mit int8-Vektoren): -3,59 Prozent MRR auf Franzoesisch, unter der 5-Prozent-Grenze, Richtung p = 0,0172. Die Umdeutung des Messpunktes ist dokumentationspflichtig und keine stille Regelaenderung, die Grenze selbst steht unveraendert. Kein Umbau, keine fp32-Auslieferung, Store-Text-Zusage unveraendert nach D-03 und D-17
- [Phase 6]: 06-04: Die Vektoren liegen in einer eigenen vectors.db neben state.db (verwerfbar ohne Volltextverlust, haelt die Ladefaehigkeit fuer Erweiterungen von state.db fern, Pfad bleibt ein Argument); repo.py::_connect bleibt deshalb OHNE enable_load_extension
- [Phase 6]: 06-04: SCHEMA_VERSION steigt auf 2, aber unter einer eigenen Marke store_schema_version. Der Schluessel schema_version traegt die Tantivy-Schemafassung aus config.py; ein Sprung unter diesem Schluessel haette den Volltext-Reindex erzwungen, den D-21 ausschliesst
- [Phase 6]: 06-04: embedding_version ist eine meta-Marke; version_mismatch meldet ihren Drift weiterhin und entscheidet nichts, VECTOR_ONLY_MARKS trennt sie, und version_drift laesst sie aus, damit kein Reindex-Banner auf einem frischen Container steht
- [Phase 6]: 06-04: Kennzahl aus Erfolgskriterium 4 gemessen statt geschaetzt: 43.859.968 Byte fuer 100.136 Chunks, also 438,0 Byte je Chunk und 876,0 je Dokument, 5,8 Prozent des Tantivy-Index (geschaetzt waren 432, 864 und 5,7)
- [Phase 6]: 06-04: nearest deckelt k als Argument (Vorgabe 100, Fenstertiefe aus D-12) und sagt ausdruecklich, dass es die Zahl der besuchten Zeilen nicht deckelt; genau das kaufen die beiden Ausweichpfade, und keiner von beiden ist gebaut (D-10)
- [Phase 6]: 06-05: Chunkgroesse 510 statt 512, weil der ausgelieferte Tokenizer zwei Sondertoken um jeden Text setzt (gemessen 05.09.2026); ein Chunk mit 512 eigenen Token kaeme als 514 an der Sitzung an und verloere seine letzten beiden ohne Fehlermeldung
- [Phase 6]: 06-05: Chunkgroesse 510 und nicht 256, obwohl Messung B Charge 2 bei Sequenz 256 als sparsamste UND schnellste Kombination ausweist: 256 haette die Chunkzahl auf 200.272 verdoppelt, den Scan jeder Nutzersuche verdoppelt und die 250.000er-Schwelle von 125.000 auf 62.500 Dokumente gezogen. Eine Stunde einmalig gegen Kosten bei jeder Suche
- [Phase 6]: 06-05: A11 beantwortet, onnxruntime wird direkt angesteuert. fastembed 0.8.0 reicht von den Sitzungsoptionen ausschliesslich enable_cpu_mem_arena durch (EXPOSED_SESSION_OPTIONS) und die Sequenzlaenge gar nicht, weil preprocessor_utils sie aus tokenizer_config.json liest; die Arena wird abgeschaltet, damit die Aktivierungsspitze nicht zur Dauerlast neben der OCR-Spitze wird
- [Phase 6]: 06-05: D-05 am echten Modell belegt: 9 von 10 deutschen Faellen bekommen mit und ohne Praefixe eine andere Rangfolge, in einem wechselt der beste Treffer. Die Praefixe stehen als benannte Konstanten im Modul, mit Test daneben
- [Phase 6]: 06-05: embedding_unavailable ist eine Konstante in embed/model.py und KEIN neuer Reason in extract/errors.py: jene Liste ist das geschlossene Vokabular eines beurteilten Dateizustands im Gleichschritt mit store/repo.py und der PHP-Beschriftung, und eine ausgebliebene Einbettung sagt nichts darueber, ob die Datei indexiert wurde
- [Phase 6]: 06-05: Zwei Tokenizer-Instanzen aus derselben Datei, weil enable_truncation eine Eigenschaft des Objekts ist: eine geteilte Instanz haette den 1.024-Token-Deckel aus D-01 still auf 512 halbiert
- [Phase 6]: 06-05: Die Zeile 'zwei Chunks je Dokument' aus 06-04 war gerechnet; gemessen sind es zwei bis drei. Kennzahl 4 ist damit ein Boden (5,8 bis rund 8,6 Prozent des Tantivy-Index), und sie haelt an beiden Enden
- [Phase 6]: 06-05: Die geschaetzten 250 bis 400 MB an INDEX_WORKERS werden nicht durch eine zweite Schaetzung ersetzt: die Modellgewichte sind mit 118.101.091 Byte gemessen, die Aktivierungsspitze bleibt ungemessen (A5) und gehoert an den Lasttest der Zweitspur
- [Phase 6]: 06-07: EMBED_LOCK_TIMEOUT_SECONDS = 1800 ist NICHT aus der Einbettungsarbeit hergeleitet (die sind rund 18 s je Charge): ein embed-Auftrag reist im selben Anspruch wie eine volle OCR-Charge und wartet hinter ihr, also braucht er das Timeout der laengsten Art, mit der er sich einen Anspruch teilt. Eine kuerzere Zahl waere failed(repeatedly_stuck) aus T-03-503 fuer die billigste Zeilenart

- [Phase 6]: 06-07: EMBED_CLAIM_BATCH = 8 folgt aus der Passdauer und nicht aus dem RAM. Die Aktivierungsspitze setzt EMBED_BATCH_SIZE = 2, nicht die Chargengroesse der Warteschlange; 8 Zeilen sind rund 18 s im schlechtesten hergeleiteten Fall (1024 Token gegen 3581 Token/s p95 aarch64, Sicherheitsfaktor 8) gegen 73 s bei 32
- [Phase 6]: 06-07: KIND_RANK stellt embed auf 0, neben acl. Ein eigener Rang darunter haette eine Rechteaenderung die wartende Embedding-Zeile verdraengen lassen (Datei dauerhaft ohne Vektoren), gleicher Rang laesst die embed-Zeile die acl-Zeile aufsaugen. Beantwortet dadurch, dass der embed-Zweig replace_acl mit der Nutzerliste seiner Zeile schreibt, nach dem Muster von bug audit M1
- [Phase 6]: 06-07: Die vier Endzustaende eines embed-Auftrags (embedded, no_stored_text, embedding_incomplete, embedding_unavailable) sind benannte Konstanten und werden NIE an Store.record gereicht: ein Dokument ohne Vektoren ist trotzdem indexiert (D-15), und ein Verdikt dort haette die Datei aus dem Index gemeldet und is_unchanged fuer immer auf False gestellt
- [Phase 6]: 06-07: _needs_vectors schliesst den CR-02-Defekt eine Spur weiter: der Schnellpfad quittiert eine unveraenderte, bereits indexierte Datei ohne Schreibvorgang, also waere ein Uebergang, der Nextcloud nicht erreicht hat, nie wiederholt worden. Gefragt wird der Vektorbestand und nicht die Zustandsdatenbank, weil das gespeicherte Verdikt ueber Vektoren nichts sagt
- [Phase 6]: 06-07: Der Plattenplatzvorbehalt zieht auf den IndexBatchWriter (free_bytes, disk_is_tight), damit Index und Vektorbestand ein Verzeichnis gegen eine Zahl fragen; der Zweitspurzweig antwortet mit _DiskTight und laeuft in die bestehende Plattenpause
- [Phase 6]: 06-08: best_chunk_for fragt in der Richtung des Vorfilters (gegebene Dateien, ihr bester Chunk) und rechnet den Abstand je Zeile, weil k eine Bedingung ueber den ganzen Bestand ist
- [Phase 6]: 06-08: snippets_for nimmt das SemanticSide-Buendel statt zweier Parameter, weil ohne Modell nichts eingebettet werden kann
- [Phase 6]: 06-09: Die zweite Deckungszahl entsteht aus einem zweiten Aufruf von AdminViewService::coverageShare mit einem anderen Zaehler und demselben Nenner (indexable), nie aus einem zweiten Rechenweg; ein Gate zaehlt die eine Deklaration und die zwei Aufrufstellen
- [Phase 6]: 06-09: embedded zaehlt Dokumente (COUNT DISTINCT file_id) und nicht Chunks, und es wird im Vektorspeicher gezaehlt statt in einer Spalte von files: eine zweite Stelle, die den Rueckstand zu kennen behauptet, laeuft am ersten verlorenen Schreibvorgang auseinander
- [Phase 6]: 06-09: embedded ist auf der PHP-Seite int|null, weil 'der Container hat die Zahl nicht gemeldet' (aeltere Fassung) und 'kein Dokument hat einen Vektor' zwei Auskuenfte sind; 0 Prozent semantische Deckung waere eine Aussage ueber die zweite
- [Phase 6]: 06-09: Die Herkunftsmarke bleibt in der Admin-Diagnose (D-14). Beide Ranglisten entstehen in index/search.py::_sides, also fahren eine Suchrunde und die Auskunft dieselbe Verschmelzung, und origins wird ausschliesslich in api/diagnose.py gerufen; in api/search.py und index/search.py kommt der Name nicht vor
- [Phase 6]: 06-09: origin fehlt in der Diagnoseantwort, statt null zu sein (response_model_exclude_none): null liest sich als 'gesucht und nichts gefunden' und damit als Urteil ueber eine Suche, die niemand gefahren hat
- [Phase 6]: 06-10: Die Grep-Hygiene laeuft ueber tokenize statt ueber einen Zeilenfilter: alle fuenf Nennungen von prefilter_visible in store/vectors.py stehen in Docstrings, und ein Zeilenfilter haette die Zusicherung an ihrem eigenen Erklaertext scheitern lassen
- [Phase 6]: 06-10: Der Rumpf der zwei Abbild-Schritte ist backend/tests/probe_image_search.py und kein Heredoc in docker.yml; nicht mit test_ benannt, damit pytest ihn nicht einsammelt, und die Modell-weg-Betriebsart braucht kein Modell und ist deshalb lokal gefahren worden
- [Phase 6]: 06-10: Der Integrationslauf holt das int8-Modell aus dem veroeffentlichten Abbild (der Weg von measure.yml) und vergleicht seine sha256 gegen die in 06-03 dreimal gemessene; ein bewusster Modellwechsel muss Dockerfile, Messbericht und diese Zeile zusammen bewegen
- [Phase 6]: 06-10: Der Umschreibungsfall im Integrationslauf behauptet Anwesenheit und nicht Rang; getragen wird die Aussage vom Kontrolllauf mit abgeschalteter Zweitspur, die Rangfrage beantworten der Offline-Schritt und der Messbericht aus 06-03
- [Phase 6]: 06-10: Der Modell-weg-Fixture setzt die Versionsmarken und traegt keinen Vektorbestand, damit degraded von der vierten Ursache aus 06-06 getrieben ist und nicht von einer nie geschriebenen Marke
- [Phase 09]: 09-05: Kein role=alert auf dem Fehlerblock der Ergebnisseite. Die 09-UI-SPEC fuehrt Live-Bereiche mit Keine, die Seite laedt vollstaendig neu, und der Block traegt ohnehin drei Traeger derselben Aussage (Symbol, Ueberschrift, Fliesstext)
- [Phase 09]: 09-05: Der Filter nutzt ein natives Kaestchen ohne die Serverklasse checkbox. Jene Klasse schiebt das Eingabefeld aus dem Sichtfeld und zeichnet einen Ersatz ueber ein Pseudoelement des Labels; ob der Vertrag in stable33 bis stable35 gleich aussieht, ist offline nicht pruefbar, und ein unsichtbares Bedienelement ist teurer als ein ungestyltes
- [Phase 09]: 09-05: Ohne Suchbegriff ist die h1 des Kopfes die Ueberschrift des Leerzustands. Beide Stellen zu fuellen haette denselben Satz zweimal untereinander gestellt; die 09-UI-SPEC laesst die eine h1 ausdruecklich Ergebnis- ODER Leerzustandstitel tragen
- [Phase 09]: 09-05: Der Fehlerblock ohne Home-Verzeichnis traegt Symbol und Ueberschrift und keinen Satz. Die Copy-Tabelle ist geschlossen und haelt fuer diese Ueberschrift nur den Satz ueber Versionen; ihn hier zu zeigen hiesse, eine Administration hinter ein Problem zu schicken, das niemand hat
- [Phase 09]: 09-05: Der Erneut-versuchen-Link nimmt die eigene Adresse nur, wenn sie mit genau einem Schraegstrich beginnt. Eine protokollrelative Referenz haette jemanden, der eine Suche wiederholen wollte, auf einen fremden Host geschickt; sonst tritt die Formularadresse an ihre Stelle
- [Phase 09]: 09-05: Stufe 3 des Rueckkehrvertrags ist tragend statt Zugabe gebaut. Der pageshow-Handler fragt nicht nach dem Back-Forward-Cache, weil no-store die Seite in Firefox davon ausschliesst, und scrollIntoView auf der Zeile scrollt #app-content und ist damit der eigentliche Traeger der Position
- [Phase 09]: 09-05: Die Paginierungsknoepfe ruhen ohne eigene Flaeche auf dem Streifen und nehmen im Hover den Seitengrund. Der Streifen traegt laut 09-UI-SPEC bereits die Hover-Farbe, ein Aufhellen in derselben Farbe waere kein Zustandswechsel; zwei Farben aus dem Budget, keine dritte erfunden
- [Phase 09]: 09-06: Der Navigationsblock steht am Dateiende hinter dem Einstellungsblock, weil die Wurzel-Sequenz des Store-Schemas ihn dort erwartet; pre-info.xslt kopiert navigations unveraendert durch, waehrend settings geleert wird
- [Phase 09]: 09-06: php/img/app.svg ist eine byte-identische Kopie von app-dark.svg statt eines zweiten Symbols. currentColor loest in einem Bildverweis auf Schwarz auf, der Server themt per CSS-Filter, und eine Kopie stellt keine zweite Lizenzfrage
- [Phase 09]: 09-06: Der Einstiegs-Eintrag traegt kein fileId-Attribut und wird an genau einem Merkmal erkannt, seiner Zieladresse. Ein pauschales Ueberspringen aller Eintraege ohne Attribut wuerde den Schutz aufheben, den der Paritaetsvergleicher haelt
- [Phase 09]: 09-06: Gate C liest sechs Dateien, aber die Sondertests der Verwaltungsseite bleiben woertlich auf admin.js. Das Seitenskript bekommt stattdessen zwei eigene Aussagen ueber die Abwesenheit derselben Marker
- [Phase 09]: 09-07: Der Einstiegs-Eintrag wird im JSON-Auszieher an seiner Zieladresse uebersprungen, nie am fehlenden fileId-Attribut. Ein Eintrag ohne Attribut, der diese Adresse nicht traegt, macht die Antwort weiterhin unlesbar
- [Phase 09]: 09-07: Der Paritaetsjob meldet sich per Cookie-Behaelter an und liest die Seite als HTML. Der Origin-Kopf ist Pflicht: LoginController von Nextcloud 34 weist eine Anmeldung ohne vertrauenswuerdigen Ursprung ab, bevor er das Passwort ansieht, und zwar mit derselben Umleitung wie bei einem falschen Passwort
- [Phase 09]: 09-08: Der Leerzustand mit Suchbegriff schweigt unter jedem Banner (Fehlerblock, Obergrenze, Index im Aufbau); ohne Suchbegriff bleibt er stehen, weil eine Einladung nie eine Behauptung ist
- [Phase 09]: 09-08: Deutsch laeuft unter beiden Sprachcodes, de und de_DE, mit byte-identischen Katalogen und einem Gate auf die Gleichheit; der Katalog ist in Sie-Form geschrieben und gehoert damit unter de_DE
- [Phase 09]: 09-08: Der franzoesische Katalog bleibt vertagt, vollstaendig oder gar nicht, vor der Store-Abgabe; die 24 Wortlaute liegen in docs/l10n-french.md, die ROADMAP zeigt bei Phase 11 darauf
- [Phase 09]: 09-08: Sichtprobe 5 sagt die Scrollposition nicht mehr zu; Stufe 2 des Rueckkehrvertrags ist browserabhaengig und in Firefox praktisch abgeschaltet, Stufe 3 ist der tragende Teil
- [Phase 10]: 10-01: Der Baumhash reist als Argument in das Abbild, nicht als Heredoc auf stdin. 40-abbild.sh ist an einem fehlenden -i gescheitert, 61-wechsel.sh hat es ergaenzt und die Ausgabe fehlt trotzdem; ein Argument braucht kein stdin, also entfaellt die Fehlerklasse. Das Skript prueft seine eigene Rohdatei auf drei verankerte baumhash-Zeilen und bricht sonst ab, denn der Vorlaeuferfehler war nicht das -i, sondern dass niemand in die Datei gesehen hat
- [Phase 10]: 10-01: Das Gate ueber die Messskripte hat zwei Geltungsbereiche. Weit (kein Wagenruecklauf, kein Gedankenstrich) ueber alle .py und .sh unter docs/measurements/**/skripte/, weil der Bestand das nach der Renormalisierung erfuellt. Eng (Shebang, kein Maschinenpfad, kein Passwort im Argument) nur ueber das Verzeichnis dieses Laufs, weil 45-suchlast.py sys.path.insert auf /home/ubuntu/work und drillhelfer traegt und Geschichte mit Rohdaten daneben ist. MACHINE_SHAPES wird per ast aus test_ops_scripts.py gelesen, damit es eine Definition fuer beide Gates gibt
- [Phase 10]: 10-01: Die fuenf renormalisierten Messskripte haben keinen Commit-Inhalt: git hatte sie mit LF gespeichert, das CRLF kam aus core.autocrlf beim Auschecken. Committed ist nur die .gitattributes-Regel, und genau sie war die Luecke. Die Altbestaende unter docs/measurements bleiben ruff-unbehandelt, weil CI dort nie laeuft und ein Reformatieren die Herkunft der daneben liegenden Rohdaten verwischen wuerde
- [Phase 10]: 10-02: Die native arm64-Feinmessung stammt aus dem measure.yml-Lauf 34325000302 gegen das Abbild sha256:eed6a5fcb152373e7bf6d7725da774844d4012cfe0cbe02b261f31a865e4cce3 (arm64-Haelfte sha256:ae58d930). Genau diesen Digest muss der Lauf auf der Box in Welle 5 aufloesen; der Runner nennt den Manifestindex, wo die aeltere amd64-Datei einen Plattform-Digest nennt
- [Phase 10]: 10-02: Die emulierte Rohdatei wird umbenannt statt geloescht (01-grundlast-fein-arm64-emuliert.txt), und jede nachgezogene Tabelle nennt die Vorlaeuferzahl mit ihrem Dateinamen. Eine Messreihe, die ihre Geschichte loescht, laesst niemanden nachvollziehen, warum ein Befund einmal anders aussah
- [Phase 10]: 10-02: Der amd64-Ast desselben Laufs wird als 01-grundlast-fein-amd64-runner.txt abgelegt statt nur ausgerechnet. Die alte amd64-Datei bleibt unveraendert, weil der Entscheid von Plan 07-03 auf ihr steht, und die Zahlen der Kontrolle bekommen trotzdem ihre eigene Rohdatei
- [Phase 10]: 10-02: MESS-01 bleibt offen. Dieser Plan hat null Box-Minuten gekostet und keinen Vergleichslauf gefahren; abhaken darf die Kennung der Plan, der die Zahlen auf der Box erzeugt
- [Phase 10]: 10-03: Der Baumhash-Beweis wird in 92-wechsel.sh gerufen und seine Rohdatei zurueckgelesen, nicht nachgebaut: drei baumhash:-Zeilen und baumhash-gleich ja, sonst Abbruch mit 4
- [Phase 10]: 10-03: 95-spitze.sh verweigert den Neustart der Rolle nachher, solange 96-oom-beweis.txt fehlt: die Reihenfolge OOM-Beweis vor Neustart ist erzwungen statt erinnert (T-10-17)
- [Phase 10]: 10-03: Teil D der Grundlast prueft Mountquelle und Ausgabe, weil ein docker run fuer eine fehlende Mountquelle ein leeres Verzeichnis anlegt und das Werkzeug eine leere Datei schreibt (DI-10-01)
- [Phase 10]: 10-04: Der Leser 96c-lesen.py liest indexed und embedded AUSSCHLIESSLICH unter backend und faellt nicht auf die oberste Ebene zurueck; fuenf Zusicherungen machen die falsche Ebene rot, ohne Box (Fallstrick 8)
- [Phase 10]: 10-04: Die Aufnahme des Statusbeobachters ist eine Projektion auf zehn Schluessel und keine Filterliste; ein neues Feld der Verwaltungsseite kann durch eine Projektion nicht durchsickern, durch einen Filter schon (T-10-21)
- [Phase 10]: 10-04: Der OOM-Beweis wird zweimal gelesen und beide Lesungen stehen beschriftet in derselben Rohdatei: bei erkanntem Ende vor jedem Eingriff, und nach den Nachlaufschritten. Eine Suchlastprobe hebt memory.peak
- [Phase 10]: 10-04: Die Bilanzzeile der Sprachfaelle zaehlt FAELLE, die Liste darunter Zusicherungen; Fall 1 traegt vier davon, und vier rote Zusicherungen eines Falls sind ein roter Fall
- [Phase 10]: 10-04: Das Skelett wird vor jedem user:add abgeschaltet und danach zurueckgesetzt, weil Handbuch und Fotoordner in der Heimat die Zaehlzusicherungen zu Aussagen ueber Dokumente machen wuerden, die niemand gewaehlt hat
- [Phase 10]: 10-05: Der Baumhash sortiert nach dem relativen posix-Pfad und nicht nach dem Path-Objekt; die Windows-Variante faltet Gross- und Kleinschreibung, also ergab derselbe Baum zwei Hashes und CI war seit Welle 1 rot. Das Python-Paket bleibt bei 6c47cd21 unter beiden Schluesseln, also wird keine Vergleichszahl retiriert
- [Phase 10]: 10-05: aws_box.sh status nennt die Zeit seit dem letzten Start nur bei laufender Instanz eine Laufzeit; geparkt zaehlte es 52,3 Stunden und 5,80 USD fuer 1,95 gelaufene Stunden, und an dieser Zahl haengt der Kostendeckel des Owners
- [Phase 10]: 10-05: Die Instanzzaehlung vor --rm-data haengt am Repositoriumsnamen und nicht an einem Registry-Pfad; das alte Muster haette MIT der zweiten Nextcloud vom 07.09. genau 1 gezaehlt und den zerstoerenden Befehl durchgelassen
- [Phase 10]: 10-05: MESS-01-Kernzahl gemessen: Grundlast im Leerlauf 103,2 MB gegen 691,8 MB (06-11) und 693,4 MB (Nachmessung), unter der gerechneten Erwartung von 118 bis 150 MB, mit null Poller-Durchgaengen als Beleg fuer den Leerlauf
- [Phase 10]: 10-05: Kaltstart 1.550,4 ms gegen die Decke von 1.500 ms, Marge minus 50,4 ms gegen plus 167,9 ms des Vorwerts; DI-07-02 neigt damit zu ja, und die schlechtere Rolle nachher steht in Plan 10-06 noch aus
- [Phase 10]: 10-05 Task 4: Der Volllauf ist durch, 52.111 indexiert und eingebettet, 37 uebersprungen, 0 fehlgeschlagen, ohne OOM und ohne Neustart; der Waechter hat in Runde 325 von 340 aus eigenem Urteil abgeschaltet
- [Phase 10]: 10-05 Task 4: Die Laufzeit wird gegen die vergleichbare Groesse gestellt: hoechstens 26 h 41 min bis zum letzten Vektor gegen 18 h 56 min (plus 40,9 Prozent), nicht die 27,0 h aus 00-FERTIG, die 25 Minuten Stillebestaetigung enthalten. Ueber der Owner-Erwartung von 22 bis 26 h, und weiterhin eine Untergrenze
- [Phase 10]: 10-05 Task 4: memory.peak hat die harte Grenze erreicht (2.147,5 MB, erstmals 5 h nach dem Anstoss) und memory.events max steht auf 21.939 gegen 2.796; der Ablaufplan hatte hier die Null erwartet. anon dagegen 1.764,2 MB gegen 1.837,8 MB, also weniger Heap und mehr Seitencache
- [Phase 10]: 10-05 Task 4: Der Durchsatz war ueber den ganzen Lauf stabil (32 bis 34 Dok/min), also erklaert kein schleichender Speicherdruck die Mehrlaufzeit; einziger von den Daten gestuetzter Kandidat ist der Zulauf, vorrat=0 in 62 von 325 Lesungen
- [Phase 10]: 10-05 Task 4: 52.111 statt 51.961 ist erklaert und keine Verdiktverschiebung: ocrdrei (120) und neustart (30) vom 07.09. liegen im Baum des indexierten Nutzers, skipped steht in beiden Laeufen auf exakt 37, und der Korpus ist byteweise derselbe
- [Phase 10]: 10-05 Task 4: Bei einer Mengenabweichung erst zaehlen, was auf der Platte liegt, dann die Verdikte befragen. Die Aufklaerung der 150 kam aus zwei Verzeichnisdaten und brauchte keinen einzigen Zugriff auf den Container
- [Phase 10]: Erfolgskriterium 2 der Phase 10 bleibt teilweise belegt statt aufgerundet (Owner 10.09.): vier von fuenf Laststufen regressiv, Sprachfaelle 6 von 10 mit Mess-Setup-Vorbehalt
- [Phase 10]: Der Nachzug der Messzahlen in README.md und docs/store-listing.md faellt in Phase 11 mit der Store-Text-Abnahme, eine Textrunde statt zwei (DI-10-03); Merker: eine Messzahl steht an drei Stellen (README.en.md plus beide info.xml)
- [Phase 10]: T-09-29 bleibt auf accept, jetzt mit Zahlen: der Vektorscan laeuft einmal je Anfrage und nicht je Seite (tiefe Seite 0,333 s gegen erste Seite 0,332 s)
- [Phase 10]: DI-07-02 wird nicht geschlossen: Kaltstart 1.838,4 ms gegen die Aufrufdecke von 1.500 ms, Marge minus 338,4 ms, Entscheidung ueber REQUEST_TIMEOUT_SECONDS an Phase 11
- [Phase 10]: Die AWS-Box ist angehalten und nicht abgebaut (Owner 10.09.); der Abbau ist ein eigener Entscheid mit eigenem Plan in Phase 11
- [Phase 11]: 11-01: V-1 = v1-a, DI-07-03 wird in v1.1.0 gefixt (MEDIUM, Abhilfe von der Berechtigungskette getrennt); Plan 11-13 ist scharf, der Katalog steigt von 173 auf 174 Schluessel, Quellstring 'Other files contain this word, but none that you may open.'
- [Phase 11]: 11-01: V-2 = v2-a, das Versionsfenster bleibt bei min-version 33 und max-version 35; beide info.xml, der stable35-Matrixeintrag und test_lockstep_versions.py bleiben unveraendert, RE-CHECK 16.09. bleibt eigener Merkposten, die Einreichung wartet nicht darauf
- [Phase 11]: 11-02: DI-10-01 behoben, beide Wege zusammen: eine Ergebnisgruppe ohne Containerteil ist der Fehlschlag EmptyResultGroup, --min-hits (Vorgabe 1) macht die Umdeutung ausdruecklich, --min-hits 0 stellt das alte Verhalten her, hits_per_request und min_hits stehen im Bericht
- [Phase 11]: 11-02: Die D-04-Zusage hat einen Waechter, backend/tests/test_upgrade_compatibility.py mit GOLD_V1_0_3 (schema/index/analyzer je 1, tantivy 0.26.0); tantivy_version wird gegen den Banner 'tantivy v0.26.0, index_format v7' gehalten statt gegen den nackten Wert, dazu Zusicherungen auf index_format v7, den Pin tantivy==0.26.0 und wngerman=20161207-15
- [Phase 11]: 11-03: FREMD_SCHWELLE der Sprachfall-Vorpruefung ist 64 (MAX_RECHECKS_ABSOLUTE aus Provider.php) und nicht 1; die Vorpruefung zaehlt je Begriff zweimal, auf der Seite der Faelle und bis Tiefe 64
- [Phase 11]: 11-03: Die gefahrene Fassung 98-sprachfaelle.sh ist per sha256 verriegelt; Fixe an Messskripten entstehen als neue Datei in einem neuen Laufverzeichnis
- [Phase 11]: 11-13: DI-07-03 ist gefixt. Der Dienst unterscheidet 'es gab keine Kandidaten' von 'es gab Kandidaten, und keiner blieb uebrig' (SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED), Vorrang Decke vor Schweigen vor neuem Zustand
- [Phase 11]: 11-13: Der neue Zustand nimmt die naechste Seite nicht weg. PageController nimmt genau diesen einen Grund von der Nein-naechste-Seite-Regel aus, die vier alten verlieren sie weiterhin
- [Phase 11]: 11-13: php/l10n/de.json traegt 174 statt 173 Schluessel. Der 174. ist 'Other files contain this word, but none that you may open.', deutsch 'Andere Dateien enthalten dieses Wort, aber keine, die Sie oeffnen duerfen.'; massgeblich fuer 11-05 (FR-Abdeckung) und 11-08 (Katalog-Gate)
- [Phase 11]: 11-13: Die drei Entscheidungszeilen der Phase 9 ($hasError, $hasHint, $showEmpty) sind byteweise unveraendert; der neue Zustand steht als eigene Zeile daneben und geht in keine der beiden Summen ein
- [Phase 11]: 11-13: PHP_TREE_HASH 4a4c6f62 bleibt als Rohmesswert vom 09.09. stehen und bekommt PHP_TREE_HASH_TODAY cf56a358 neben sich; eine berichtete Vergleichszahl wird nicht retiriert, wenn der Code weiterlaeuft
- [Phase 11]: 11-07: Der Upgrade-Block liegt hinter den sechs Store-Deinstallationszusagen und faehrt auf genau einem Ast (stable34/ubuntu-24.04); jeder Schritt nennt beide Matrixwerte in seiner eigenen if-Bedingung, weil deploy-harp.yml keine Blockbedingung kennt
- [Phase 11]: 11-07: Der Block laeuft NICHT mit gesetztem release_tag. In diesem Modus waere die neue Haelfte dieselben Bytes wie die alte, und der Beweis waere gruen ohne gemessen zu haben; lieber gar nicht laufen als nichts messen
- [Phase 11]: 11-07: Die Datenflagge von app_api:app:unregister kommt im ganzen Upgrade-Block nicht vor, nicht einmal als Zeichenkette in einem Kommentar, damit ein grep darueber leer bleibt (T-11-26); das Volumen des Store-Durchgangs wird mit docker volume rm beim Namen entfernt
- [Phase 11]: 11-07: Die neue Container-Haelfte wird mit info-citest.xml registriert (Abbild dieses Commits aus der lokalen Registratur), weil backend/appinfo/info.xml bis 11-11 weiterhin image-tag 1.0.3 nennt; der Schritt prueft ausdruecklich, dass altes und neues Abbild verschieden sind
- [Phase 11]: 11-07: Jede Zusicherung ueber Unveraendertheit braucht eine Zusicherung ueber eine Aenderung neben sich. Hier ist das der Navigationseintrag aus 09-06, sonst waere ein Upgrade, das nichts bewirkt hat, das gruenste Ergebnis
- [Phase 11]: 11-07: Der Reindex-Zweig von D-05 wird nicht gefahren, seine Abwesenheit wird zugesichert, und das steht als Kommentar im Workflow. Bewegt sich je eine Marke, faellt die Markenzusicherung vor den Abwesenheitszusicherungen, und die Frage gehoert dem Owner
- [Phase 11]: 11-05: Die Schluesselmenge ist aus php/l10n/de.json gezaehlt und nicht aus der Recherche uebernommen. 174 statt 173 ist kein Befund, sondern Entscheid v1-a, und die Datei nennt Plan 11-13 als Herkunft der gestiegenen Zahl, damit ein spaeterer Leser sie nicht fuer Nachlaessigkeit haelt und wieder senkt
- [Phase 11]: 11-05: Die Datei nennt vier Zahlen statt drei, 34 Schluessel mit printf-Direktiven und 29 ohne die fuenf Pluralschluessel. Die Recherche zaehlt 29, eine naive Nachzaehlung findet 34, und ohne den Satz, der beide auseinanderhaelt, haelt die naechste Zaehlung eine der beiden fuer falsch
- [Phase 11]: 11-05: Die Spalten Schluessel und DE der Uebersetzungstabelle werden aus de.json erzeugt und nicht abgetippt; nur die FR-Spalte ist Handarbeit. Damit kann eine Tabellenzeile nicht stillschweigend von dem abweichen, was die App tatsaechlich uebersetzt
- [Phase 11]: 11-05: backend heisst im Franzoesischen durchgehend le service, nach dem seit Phase 9 abgenommenen Wortlaut der Ergebnisseite; wo der Eigenname gemeint ist, bleibt Findling Backend stehen. run heisst passage, a worker heisst un processus de traitement und nicht un travailleur, weil die deutsche Vorlage Arbeiter sagt und ein franzoesischer Leser dort an eine Person denkt. Alle drei vom Owner am 11.09. ausdruecklich bestaetigt
- [Phase 11]: 11-05: Das Register folgt dem Deutschen zeilenweise, Verwaltungsseite im Infinitiv, Ergebnisseite im Vouvoiement. Ein einheitliches Register waere eine Textrunde gewesen, die niemand bestellt hat
- [Phase 11]: 11-05: Vor : ; ? ! steht ein einfaches Leerzeichen und nicht U+00A0 oder U+202F. Das ist die Form des franzoesischen Bestands (README.fr.md, info.xml) und die einzige, die den Katalog nicht mit unsichtbaren Zeichen fuellt, die niemand in einem Diff sieht
- [Phase 11]: 11-05: Findling steht nicht in der Tabelle, wie der Plan es verlangt, aber mit Wortlaut in der benannten G2-Ausnahmenliste. Beides zusammen ist der einzige Weg, der die Abnahmekriterien von 11-05 und Gate G1 von 11-08 gleichzeitig haelt; eine Toleranzschwelle statt der Liste ist ausdruecklich ausgeschlossen
- [Phase 11]: 11-05: Die drei Stellen, an denen docs/l10n-french.md noch 173 nannte, sind hier bearbeitet und nicht an 11-10 weitergereicht worden, weil die Datei in files_modified dieses Plans steht. Die beiden historischen Aussagen behalten ihre damalige Zahl und sind als Geschichte kenntlich, die vorwaertsgerichtete Bedingung nennt jetzt 174

### Pending Todos

[From .planning/todos/pending/ , ideas captured during sessions]

None yet.

### Blockers/Concerns

- Baustart erst nach der Store-Einreichung des Schwesterprojekts nextcloud-mcp-connector (September 2026), Solo-Kapazität
- Kill-Kriterium aktiv: Nextcloud GmbH hat fulltextsearch am 12.08.2026 reaktiviert. Kündigt sie eine Elasticsearch-freie Suche mit OCR an, wird das Projekt neu bewertet (Nextcloud Conference September beobachten)
- CSR-Vorlaufzeit für zwei getrennte App-Store-Einträge ist ein bekanntes Terminrisiko aus dem Schwesterprojekt
- RAM-Spitzen auf ARM sind bisher nur geschätzt, Messlauf steht in Phase 5 aus
- Zwei benannte Luecken aus der Sichtprobe 04-10, beide in .planning/phases/04-admin-sichtbarkeit-und-diagnose/deferred-items.md mit ihrer Schliessform: DI-04-03 (Skip-Verdikte pro fileid uebergeben, damit die Fehlerliste die vier Container-Gruende gruppieren kann) und DI-04-04 (Versionsmarken nach abgeschlossenem Neuaufbau neu stempeln, sonst kann der Reindex-Banner die eigene Abhilfe nie einloesen)
- Das Pruefsummen-Gate ueber das Referenzkorpus nach der Live-Raeumung steht aus und gehoert in die Phasen-Verifikation (Gate A auf Quellcode-Ebene ist gruen, die Write-Allowlist unveraendert bei drei Eintraegen)
- **Kostendeckel fast erreicht (Stand 2026-09-10T13:14Z):** Die Box ist 27,9 h gelaufen und hat 3,23 USD gekostet; der 30-Stunden-Deckel greift am 2026-09-10T15:19:50Z, es bleiben rund 2,1 Stunden. Plan 10-06 braucht darunter Nebenlaeufigkeitsreihe, Bestand, Neustart mit Kaltstart, Seitenroute, Rundenzaehlung und zehn Sprachfaelle. Owner-Entscheid noetig: straff fahren und notfalls die Sprachfaelle opfern, oder Deckel auf 33 bis 34 h und 4,00 USD anheben
- **Die Laufzeit ist die erste Zahl der Phase, die schlechter geworden ist**, und sie ist gross: plus 40,9 Prozent. Erfolgskriterium 2 der Phase verlangt, dass jede Verschlechterung benannt statt weggelassen wird; das gilt fuer die Laufzeit und fuer memory.events max 21.939. Der Bericht in 10-07 braucht dafuer einen eigenen Abschnitt, nicht eine Fussnote
- Vor dem Tag v1.0.0 (Plan 06-12) zu entscheiden: DI-06-02 und DI-06-03 (embedding_version wird nicht gestempelt, reset_for_reindex hat keinen Aufrufer). Plan 06-09 hat die Bedingung geliefert (embedded == indexed bei indexed > 0); es fehlt ein Plan auf dem Indexweg oder eine bewusste Entscheidung in docs/embeddings.md, dass ein Modellwechsel occ findling:index --restart verlangt

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-09-11T03:20:00.000Z
Stopped at: Abgeschlossen 11-05-PLAN.md, die vollstaendige FR-Uebersetzungstabelle und das FR-Gate Teil 1 (abgenommen 2026-09-11, keine Korrektur). Welle 3 ist damit zu
Resume file: None
