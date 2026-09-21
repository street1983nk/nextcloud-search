---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Messbeleg und Ausbau
status: in_progress
stopped_at: 16-11 **Entwurf fertig, Owner-Checkpoint offen**: `docs/store-listing.md` traegt die sechs Store-Texte mit der neuen Messzahl **731,9 MB resident nach einem Indexlauf** (ersetzt 103,2 MB im Leerlauf, Entscheid E1), die Sprachzeile mit **neun verfuegbaren Sprachen bei drei voreingestellten**, die neue Grundlast-Zeile der drei READMEs, die Fundstellenliste und das Aenderungsprotokoll (Commit `253abb5`). **Nichts ist ausgeliefert**: beide `info.xml` und die drei READMEs tragen weiter 103,2 MB, die woertliche Uebernahme ist 16-12 NACH der Abnahme. Owner muss entscheiden: Textabnahme im Wortlaut plus Q-6 (Store-Bilder "bleiben" oder "neu"); kein Tag, kein Release
last_updated: "2026-09-22T03:05:00.000Z"
last_activity: 2026-09-21
progress:
  total_phases: 5
  completed_phases: 4
  total_plans: 63
  completed_plans: 59
  percent: 94
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-11)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 16 ausfuehren (14 Plaene, 8 Wellen; Checkpoints in 16-08/16-10/16-11/16-13/16-14)

## Current Position

Phase: 16 (haertung-und-store-einreichung-v1-2-0): **IN ARBEIT**
Plan: 10 von 14 abgeschlossen (16-01 bis 16-10). **Welle 1 bis Welle 4 sind
vollstaendig.** **16-11 laeuft und steht an seinem Owner-Checkpoint**: der
Textentwurf ist geschrieben und committet, die Abnahme fehlt.

16-11 (LAEUFT, Checkpoint offen): **Der Textentwurf der Fassung 1.2.0.** Ein
Commit, `253abb5`, und er fasst genau eine Datei an: `docs/store-listing.md`.
Die RAM-Zeile der sechs Store-Texte nennt dreisprachig **731,9 MB resident nach
einem Indexlauf** statt 103,2 MB im Leerlauf; das Wort "im Leerlauf" ist durch
die Messgroesse ersetzt, weil die neue Zahl eine ANDERE Messgroesse ist (Marke C
vom 21.09.2026, Rohdatei `94b-grundlast-rueckkehr.txt`). Je Text bleibt es bei
genau einer Messzahl, die 103,2 kommt in keinem der sechs Texte mehr vor. Die
Sprachzeile der ersten Haelfte nennt **neun verfuegbare Sprachen bei drei
voreingestellten** (die neun Namen stehen in den READMEs und in der Beschreibung
von `FINDLING_OCR_LANGUAGES`, nicht im Store-Text). Die Grundlast-Zeile der drei
READMEs **verliert den Alt-Neu-Vergleich samt der 85,1 Prozent**: eine
Prozentzahl zwischen zwei Messgroessen waere eine Verbesserung, die nie gemessen
wurde; der alte Vergleich bleibt in `docs/performance.md` fuer seine Bedingungen
gueltig. Der Spitzen-Satz (52.111 Dokumente, 1.764 MB) bleibt zeichengleich
stehen, weil der v1.2-Lauf die Spitze nicht neu gemessen hat. Dazu die
Fundstellenliste (neun Stellen fuer die Zahl, elf fuer die Sprachangabe) und ein
Aenderungsprotokoll mit beiden Eintraegen. Volle Suite 2.472 bestanden / 15
uebersprungen, `test_store_metadata.py` 52 bestanden, ruff/vulture gruen.
**AUSGELIEFERT IST NICHTS**: beide `info.xml` und die drei READMEs tragen
unveraendert 103,2 MB, und die woertliche Uebernahme ist Plan 16-12 nach der
Abnahme. **Der Owner entscheidet zweierlei:** die Textabnahme im Wortlaut und
Q-6, die Store-Bilder vom 07.09.2026 (a: bleiben, b: eigener Plan in Welle 6).
Keine SUMMARY, ROADMAP unveraendert, solange der Checkpoint offen ist.

16-10: **Sechs weitere OCR-Sprachen, der Standard bleibt bei drei.** Der
Owner-Entscheid am Tor lautet im Wortlaut **"Mitfahren"**, der Abbruchpfad ist
nicht gezogen worden, und sein Grund ist auch nicht eingetreten. Zwei Commits.
`a9ee779`: sechs apt-Zeilen (`spa`, `ita`, `nld`, `por`, `dan`, `est`), je mit
dem harten Pin `=1:4.1.0-2` aus derselben `tesseract-lang`-Quelle wie `deu`,
`eng` und `fra`, dazu sechs eigene `--list-langs`-Pruefungen nach der
Installation; `OCR_LANGUAGE_ALLOWLIST` waechst von drei auf neun Eintraege,
**`OCR_DEFAULT_LANGUAGES` bleibt `deu+eng+fra`** (verfuegbar ist nicht
eingeschaltet: neun Sprachen als Standard wuerden jede OCR-Seite jeder
bestehenden Installation langsamer machen); `THIRD-PARTY.md` bekommt eine eigene
Tabelle fuer die sieben spaeter zugekommenen Packs, und dabei ist die Luecke
geschlossen, dass `tesseract-ocr-fra` seit dem 06.09.2026 dort fehlte;
`PACKAGE_TREE_HASH_TODAY` ist im SELBEN Commit auf `7d0e5857...` nachgezogen,
`PACKAGE_FILES` bleibt 54. `01dffa1`: `backend/tests/test_ocr_languages.py`,
drei Faelle, die Liste aus `config.py` gelesen und nicht abgeschrieben, roter
Zustand gestagt und einmal echt gegengeprobt (eine zehnte Sprache `ces` macht
Fall 1 und Fall 2 rot). **Annahme A7 war VOR dem Bau gegen die Paketquelle
nachgesehen** (api.ftp-master.debian.org, Suite stable): alle sechs
`1:4.1.0-2`, main, `Architecture: all`, Quellpaket `tesseract-lang`, zusammen
19,7 MB installiert. **Der Multi-Arch-Bau ist gefahren und gruen: `docker.yml`
Lauf 35597353780** (Push von `01dffa1`), die sechs Pakete und ihre Pruefungen
haben also auf amd64 und arm64 real gebaut. Volle Suite 2.472 bestanden / 15
uebersprungen, Skipzahl unveraendert. **Offen und an 16-11 uebergeben:** elf
Textstellen in fuenf Dateien nennen noch "German, English, French" (beide
`info.xml`, `docs/store-listing.md`, die drei READMEs); die Liste mit
Zeilennummern steht in `16-10-SUMMARY.md`.

16-09: **Der Upgrade-Beweis springt jetzt von v1.1.0.** Vier Commits.
`12fec7d`: Q-5 ist **nachgesehen und nicht geraten**. Der sechste
Engine-Zustand `unloaded` traegt NICHT, aus zwei belegten Gruenden: das Feld
`engineState` steht schon in v1.1.0 in der Admin-Antwort
(`git show v1.1.0:php/lib/Service/AdminViewService.php`, Zeile 1813), und der
Wert haengt an `unload_count() > 0`, also an einer Leerlaufspanne, die dieser
Auftrag nicht faehrt. Gewaehlt ist stattdessen die **Filterliste des
Suchanbieters**, und sie ist billiger als die Recherche annahm: keine
gerenderte Seite noetig, weil `/ocs/v2.php/search/providers` die Filterkarte je
Anbieter traegt (`integration.yml` liest dieselbe Route seit Phase 1).
`snapshot()` schreibt seitdem `searchFilters.declared` und
`searchFilters.dates`. `0f112c3`: die vier Stellen in einem Commit,
`UPGRADE_FROM_TAG: v1.1.0`, die Vorbedingung in "Store upgrade 1" **umgedreht**
(der `<navigations>`-Block MUSS jetzt da sein, das ist die billigste
Zusicherung, dass die Marke auf die 1.1.x-Reihe zeigt), die zweite Vorbedingung
des Vorher-Zustands auf die Abwesenheit der Datumsgrenzen getauscht, und
Zusicherung 6 misst `searchFilters.dates` und nennt Plan 13-06. Die
**Zusicherungen 1 bis 5 sind zeichengleich** (48 Zeilen, maschinell verglichen),
die zwei Zweige des Versionsschritts aus 11-11 bleiben beide stehen.
`607f8d0`: die Ratsche heisst `GOLD_V1_0_AND_V1_1`, die fuenf Werte sind
unveraendert, 6 Faelle wie vorher. `1c61216`: der ungefahrene Lauf bekommt eine
Adresse in `deferred-items.md`.

**Nachgetragen am 21.09.2026: erledigt.** Der Push von `73cbca1` hat den Lauf
**35594647362** gestartet (deploy-harp, stable34/ubuntu-24.04, success), alle
sechs Zusicherungen halten, alle vier Pruefzeilen stehen als echte Ausgaben im
Protokoll. **Erfolgskriterium 3 von REL-02 ist damit belegt**; das Abhaken von
REL-02 selbst bleibt bei Plan 16-14. Der urspruengliche Eintrag, zur
Nachvollziehbarkeit: Task 3 Teil 2 des Plans (einen echten `deploy-harp`-Lauf
auslesen) konnte in der Sitzung nicht stattfinden, weil der Auftrag das Pushen
verbot. Der Pruefweg
(Werkbank, Bein, sechs Pruefzeilen, Belegdateien, Wiederholungsregel bei rot)
steht vollstaendig in `16-09-SUMMARY.md`, Abschnitt "Was der Orchestrator in CI
nachsehen muss". Lokal geprueft ist alles, was ohne Runner pruefbar war: YAML
parst (48 Schritte), `sh -n` auf dem ausgeloesten Sondenskript (250 Zeilen),
beide jq-Zweige gegen selbst gebaute Abbilder im erwarteten Fall und im
Fehlerfall, die umgedrehte `<navigations>`-Pruefung gegen `git show v1.0.3:`
und `git show v1.1.0:`, die Release-Anhaenge von v1.1.0 und die Abbildmarke
`:1.1.0` als Index mit amd64 und arm64. `:1.2.0` liegt erwartungsgemaess noch
nicht in der Registratur (das ist 16-14), weshalb weiterhin `info-citest.xml`
registriert wird.

16-08: **Auflage A4 ist ohne Box erfuellt.** Aufgabe 1
ist verbucht (d34c392): der Auftrag `index-search-e2e` liest seinen Runner jetzt
aus der Matrix, die Achse `runner` traegt `ubuntu-24.04` fuer die drei
bestehenden Kombinationen, und genau ein `include`-Eintrag ergaenzt
`sqlite`/`stable34`/PHP 8.2 auf `ubuntu-24.04-arm`. Lokal nachgerechnet: vier
Kombinationen, drei auf amd64, eine auf arm64. Der Zeitdeckel bleibt bei 45
Minuten, begruendet mit den drei amd64-Laufzeiten von 3:38 bis 3:54 aus Lauf
35582071147. Keine erforderliche Pruefung haengt an den alten Auftragsnamen (das
Regelwerk `protect-main` kennt nur `deletion` und `non_fast_forward`), der
geaenderte `name:` bricht also nichts. **Aufgabe 2 ist gefahren und verbucht**
(b5da459): Lauf **35586213137** vom 21.09.2026, Auftrag `index-search-e2e
(sqlite, ubuntu-24.04-arm)`, 3 min 43 s, success beim ersten Anlauf, keine
Wiederholung noetig. Die Instanz meldet `files on the instance before the
corpus: 0`, danach `corpus entries: 39` und
`indexed=26 skipped=7 failed=6`, also dieselben Verdikte wie auf amd64. **Zehn
von zehn Sprachfaellen gruen, null rot, null ohne Aussage**; alle fuenf in
Phase 15 nicht messbaren Faelle (Genehmigung, Frist, Vertrag, bescheid,
type:pdf bescheid) tragen jetzt eine Aussage. Der Beleg steht in
`docs/measurements/2026-09-a4-sprachfaelle-ci/README.md`, sein Urteil zum Weg
lautet **traegt**. **Aufgabe 3, der Owner-Checkpoint, ist beantwortet:** dem
Owner lag genau ein Zweig vor (Zweig a), seine Antwort im Wortlaut lautet
**"Zweig a, zustimmen"**. Erfolgskriterium 4 der Phase 15 (**L-09**) wird damit
mit Lauf 35586213137 und dem Beleg als erfuellt gefuehrt, **keine Box, kein
Deckel-Abruf**; L-09 steht in `deferred-items.md` als geschlossen. Offene
Merker aus diesem Plan: der `name:` der vier Kombinationen ist neu (keine
erforderliche Pruefung zeigt darauf), der ARM-Ast faehrt nur sqlite, und die
OCR-Fassung der Maschine ist 5.3.4 statt der 5.5.0 des Auslieferungsabbilds.

16-07: **Der Baum sagt 1.2.0.** Die drei Versionsstellen (`php/appinfo/info.xml`
`<version>`, `backend/appinfo/info.xml` `<version>` und das `<image-tag>`
daneben) stehen in einem Commit auf `1.2.0` (734a1b2); `min-version 33` und
`max-version 35` sind unberuehrt, keine Matrix hat sich bewegt, und
`test_lockstep_versions.py` musste dafuer nicht angefasst werden, weil es
bewusst keine Zahl nennt. Der Minor-Sprung hat seine Migration (12e8663):
`php/lib/Migration/Version001200Date20260921000000.php` verwirft in
`postSchemaChange` die veraltete Versionsmarke des Containers, schreibt bewusst
keine an ihre Stelle, ist bei fehlendem Schluessel ein no-op mit Meldung und
fragt den Container nicht; ihr Test traegt sechs Faelle, zwei mehr als die
Vorlage (zweiter Lauf wirft nicht, der Konstruktor bekam nur `IAppConfig`).
`PHP_FILES_TODAY` geht im SELBEN Commit von 64 auf **66** und
`PHP_TREE_HASH_TODAY` auf `7942f09f...`. Der Datumsteil des Namens ist
**20260921** und nicht der Arbeitsname 20260922 aus der Dateiliste des Plans.
Volle Suite 2.469 bestanden / 15 uebersprungen, Skipzahl unveraendert.
**Offen:** `php.yml` ist fuer diese Commits noch nicht gelaufen (kein PHP auf
dieser Maschine, kein Push im Auftrag), **es ist kein Tag gesetzt und kein
Release gebaut** (das ist 16-14), und die Erzaehlung der Spruenge in den
Kommentaren beider `info.xml` endet weiterhin bei 1.1.0 (gehoert zu 16-11).

16-06: Auflage A3 ist gebaut. **Der innere Aufruf misst sich selbst** (f604805):
`hrtime` umschliesst in `ExAppService::call` genau den einen
`proxyRequest`-Aufruf, die Dauer geht in Millisekunden auf eine Nachkommastelle,
und oberhalb der neuen Schwelle `SLOW_CALL_LOG_MILLISECONDS = 1000.0` entsteht
eine `info`-Zeile mit genau drei Feldern (`path`, `innerMs`, `ceilingMs`). Kein
Suchbegriff, kein Dateiname, keine Kennung, kein Rumpf. `ceilingMs` traegt die
Decke, die fuer DIESEN Aufruf galt, also `min(Decke, Restbudget)`. **Alle vier**
Fehlerpfade von `call()` tragen dieselbe Zahl (der Plan nannte drei; der vierte
steht einzeilig und war beim Zaehlen untergegangen). Zwei PHPUnit-Faelle halten
die Zeile oberhalb und das Schweigen unterhalb der Schwelle; ein neues Textgate
`backend/tests/test_exapp_call_instrumentation.py` (e3fb6c5) haelt Sitz der
Messung ueber die Zeilenfolge, Schwellenbedingung, Nutzerinhaltsfreiheit mit
Selbsttest und den Schwellenwert unter der kleinsten Zeitdecke.
`PHP_TREE_HASH_TODAY` ist im SELBEN Commit auf `29dc890b...` nachgezogen,
`PHP_FILES_TODAY` bleibt bei 64. Volle Suite 2.469 bestanden / 15
uebersprungen, Skipzahl unveraendert. **Offen:** `php.yml` ist fuer diese beiden
Commits noch nicht gelaufen (kein PHP auf dieser Maschine, kein Push im
Auftrag), und die Zahl auf Zielhardware liefert erst die naechste Box, so wie
die Auflage es selbst sagt.

16-05: Auflage A2 ist vollstaendig. **Die Altfunde sind bereinigt** (fe3cf8c):
`docs/performance.md` und `docs/install-check.md` tragen Instanz-, Volume- und
Security-Group-Kennung sowie die oeffentlichen Adressen der Boxen nur noch als
Platzhalter, der die ART des Wertes benennt (`<instanzkennung>`,
`<volumekennung>`, `<sicherheitsgruppe>`, `<adresse-der-box>`); die Legende
steht als `PLATZHALTER` im Gate und wird von einem neuen Fall in BEIDE
Richtungen gegen `docs/` gehalten. **Das gesperrte Wort ist weg** (f1c15a1):
52 deutsche Formen in vier Anleitungen ersetzt (Paketdatei, Ablage, ZIP-Datei,
kalte Ablagestufe); es bleiben drei Vorkommen, zweimal der Skriptname und
einmal eine woertlich zitierte englische CI-Ausgabe (E-H2). Die Ausnahmeliste
schrumpft von 50 auf 46 Eintraege, sechs weitere Gruende sind auf den
verbliebenen Bestand nachgezogen. **Was begruendet bleibt:** Rohdaten und
Skripte gefahrener Anfahrten, die oeffentliche Abbildkennung I-01 und die
Korpus-Snapshotkennung (Entscheid E2, Betreiberentscheid vom 11.09.2026).
**Die Historie ist unberuehrt**, zwei neue Commits obendrauf, kein rebase, kein
amend, kein Push; alle alten Commit-Kennungen gelten weiter. Volle Suite 2.464
bestanden / 15 uebersprungen, Skipzahl unveraendert.

16-04: Die vier aufgeschobenen Punkte aus DI-11 haben ihr Verdikt.
**DI-11-03 gebaut** (daa4661): `scripts/ops/search_load.py` fragt vor der
ersten Laststufe je Begriff den ungedeckelten Bestand im Prozess des
Containers ueber `ranked_sides` (Weg: `docker exec` mit dem Interpreter des
Abbildes, wie 98c). Die Zeilen der Sonde stehen als erster Schluessel im Kopf
der Rohdatei, die Antworten unter `--min-hits` werden als `ohne-treffer` und
`fehlschlag` getrennt gezaehlt, die Gesamtzahl und `EmptyResultGroup` bleiben
daneben. Faellt die Sonde aus, traegt die Rohdatei `vorlaufsonde: nicht
verfuegbar` und die Trennung unterbleibt namentlich (T-16-13).
**L-07 gebaut** (681097a): `cmd_destroy` loescht das Schluesselpaar nach
Instanz und Datentraeger und liest es zurueck; ein bereits fehlendes Paar ist
eine Zeile und kein Fehler. **Sieben Verdikte** in
`.planning/phases/16-haertung-und-store-einreichung-v1-2-0/deferred-items.md`
(4917463): DI-11-02 zu (vier Laststufen behoben, null `cURL error 28` im
Lastfenster), DI-11-03 und DI-11-05 abgearbeitet, DI-11-06 weitergereicht nach
v1.2 mit dem Satz zum Migrationszwang, L-05 und L-06 an die naechste Anfahrt,
L-08 als benannte Asymmetrie; die Kopfzeile adressiert L-03, L-04, L-07, L-09,
L-10, L-11, M-01 und M-02 auf ihre Plaene. Fuenf neue Faelle in
`test_ops_scripts.py`, volle Suite 2.463 bestanden / 15 uebersprungen,
Skipzahl unveraendert.
**WICHTIG: beide Werkzeugaenderungen sind nur statisch geprueft**, weder die
Sonde noch der Abbau ist gegen einen echten Container oder ein echtes Konto
gefahren; die naechste Anfahrt misst sie. **HART-01 bleibt offen** und wird
erst in 16-13/16-14 abgehakt.

16-03: Auflage A1 ist gebaut und STATISCH abgenommen. Das neue
Laufverzeichnis `docs/measurements/2026-09-nachfolgefassungen/skripte/`
traegt `92c-wechsel.sh` (bd10eeb) und `99d-filter-sortierung.sh` (3bc7925),
beide als Kopie ihrer Vorgaengerin mit genau einer Sachaenderung: 92c prueft
den Rueckgabewert des occ-Aufrufs der Registrierung und verweigert unterhalb
der Pipeline mit 36 (L-03), 99d liest das Passwort auch aus PWFILE und endet
sonst mit 2 (L-04). Vier neue Waechter in `test_measurement_scripts.py`
(fc8afba), je Fassung einer fuer die Herkunft und einer fuer die behobene
Eigenschaft; das neue Verzeichnis ist der vierte Eintrag in
`NARROW_SCOPE_DIRS`. `DRIVEN_V12_FASSUNGEN` bleibt bei sechs unveraenderten
Pruefsummen, `git diff --stat` nennt weder 92b noch 99c. Volle Suite 2.458
bestanden / 15 uebersprungen, Skipzahl unveraendert.
**WICHTIG: keine der beiden Fassungen ist auf einer Box nachgemessen.** Der
Nicht-gefahren-Satz steht in Versalien im Kopf jeder Datei, wird von einem
Fall gehalten und steht in 16-03-SUMMARY.md. Ihre Wirkung misst erst die
naechste Anfahrt; das ist die dokumentierte Grenze von A1.

16-02: Die Geheimnisregel hat zum ersten Mal ein Gate.
`backend/tests/test_public_artifacts.py` (38ebd9d, 1f25a74) laeuft rekursiv
ueber ALLE Dateien unter `docs/` (heute 389), prueft neun Musterfamilien plus
die Vokabularregel L-10, haelt eine Untergrenze der Dateizahl
(`DOCS_FILES_FLOOR = 380`, Zaehldatum im Kommentar) und einen sauberen plus
einen mutierten Selbsttest je Familie. `AUSNAHMEN` traegt 49 Eintraege nach
(Pfad, Familie), je mit eigenem Grund und ohne einen einzigen Wert; ein Fall
verbietet den veralteten Eintrag, damit Plan 16-05 die Liste mitschrumpfen
muss. Heutiger Bestand: 2 Dateien pem, 10 aws-ressourcenkennung, 10
schluesselwort-mit-wert, 2 base64, 19 muster-der-umsetzung, 6 vokabular; null
bei ssh, aws-zugangskennung, rechnername-der-box und ipv6. Volle Suite 2.444
bestanden / 15 uebersprungen, Skipzahl unveraendert (2.394 + 50 neue Faelle).
**A2 ist zur Haelfte erfuellt**: das Gate steht, die Bereinigung der
redigierbaren Dateien ist Plan 16-05.

16-01: Die drei Flake-Staemme sind behandelt oder benannt: `write_revision` mit
enger 423-Wiederholung in `integration.yml` (DI-11-05, Commit a856563),
`ARRIVAL_SECONDS = 30.0` getrennt von `BLOCKED_WARM_SECONDS = 5.0` in
`test_search_endpoint.py` (L-11, a27ec2c),
`docs/audits/2026-09-phase-16/flake-register.md` plus `ignore` fuer tantivy in
`.github/dependabot.yml` (9b24613).

HART-01 ist NOCH NICHT abgehakt: erledigt ist nur DI-11-05, DI-11-02/03/06
liegen bei Plan 16-04. `parity-login` bleibt beobachtet und ungefixt.
Dependabot-PR #11 liegt weiterhin beim Owner.
NAECHSTES: 16-04 (Rest der Welle 1).

### Vorgeschichte, Phase 15

Phase 15 (messphase-eine-box-anfahrt): **ABGESCHLOSSEN UND ABGENOMMEN (21.09.2026)**
Plan: 16 of 16 abgeschlossen. Task 1 (performance.md, fuenf datierte Nachtraege,
fb2f1ab), Task 2 (Audit der Phase, REQUIREMENTS, STATE, 6ed748d), Task 3
(Owner-Checkpoint): **Abnahme erteilt am 21.09.2026, Antwort im Wortlaut "ziel
ist das wir den usern das best mögliche liefern"**, per Rueckfrage bestaetigt
als Abnahme mit Auflagen. Erfolgskriterium 4 (Sprachfaelle ohne Fremdbestand)
ist als NICHT erfuellt vorgelegt und nicht umgedeutet worden; seine
Nacherfuellung ist Auflage A4. Die Auflagen an Phase 16, im Einzelnen in
15-16-SUMMARY.md: A1 Nachfolgefassungen 92c/99d, A2 Geheimnisregel als CI-Gate
plus 58 Altfunde, A3 M-01-Instrumentierung (innerer Aufruf getrennt von der
Gesamtdauer), A4 kleine Sprachfaelle-Anfahrt (Rechenblatt + Deckel zur
Owner-Freigabe VOR dem Start). Bewusst nicht beauftragt: Top-up-A/B-Attribution
(keine Nutzerwirkung), bleibt notierter Messauftrag.
Status: Milestone v1.2, die 49 Plaene der Phasen 12 bis 15 sind abgeschlossen,
Phase 16 laeuft mit 10 von 14 Plaenen.
Progress: [█████████░] 94% der 63 geplanten Plaene (59 von 63)
Last activity: 2026-09-21 -- 16-10 in zwei Commits gefahren (a9ee779, 01dffa1): Owner-Entscheid "Mitfahren" am Tor, sechs weitere OCR-Sprachpakete mit Pin und je eigener Bau-Pruefung, Positivliste auf neun bei unveraendertem Standard, THIRD-PARTY-Tabelle, neues Gate, Baumhash im selben Commit; Multi-Arch-Bau gruen (35597353780), volle Suite 2.472 bestanden / 15 uebersprungen. Davor: 16-09 in vier Commits gefahren (12fec7d, 0f112c3, 607f8d0, 1c61216): Q-5 nachgesehen, der Beweis springt von v1.1.0, Zusicherung 6 misst die zwei Datumsgrenzen, die Ratsche nennt beide Minor-Reihen. Nach `uv sync` (pypdf 6.18.1 auf 6.19.0, ruff 0.16.7 auf 0.16.8) waren alle Gates schon vor der ersten Aenderung gruen, der neue ruff brachte keine neue Regel zum Tragen; volle Suite 2.469 bestanden / 15 uebersprungen, vorher wie nachher. Davor: 16-01 in drei Commits gefahren (a856563, a27ec2c, 9b24613): enge 423-Wiederholung, zweite Zeitkonstante, Flake-Register und tantivy-Ignoranweisung. Davor: 15-16 Task 1 und Task 2 gefahren und je einzeln committet: `docs/performance.md` traegt die fuenf datierten Nachtraege der Anfahrt (259 Zeilen dazu, keine geloescht), `docs/audits/2026-09-phase-15/README.md` traegt das Phasenaudit (ein MEDIUM, elf LOW, zwei davon geschlossen), MESS-05 und MEM-02 sind in `.planning/REQUIREMENTS.md` je mit Zahl und Rohdateiverweis abgehakt. Volle Suite 2.394 bestanden / 15 uebersprungen, Skipzahl unveraendert. **Offen ist Task 3, die Abnahme der Phase durch den Owner**; danach erst die SUMMARY zu 15-16

**Was der Owner in 15-16 zu entscheiden hat, in drei Zeilen:** die Abnahme der
Phase, das Abhaken von MESS-05 und MEM-02 (beide haben ihre Zahl an ihrer
Messgroesse), und die Kenntnisnahme der Bodensatz-Zahl: 731,9 MB residenter
Stand nach einem Indexlauf mit entladenem Modell, auf einer 4-GB-Box. Offen
bleibt daneben die Wiedervorlage des Korpus-Snapshots (Q5 der Recherche, im
Bericht und im Runbook Abschnitt 8 Schritt 9 benannt).

**Das Belegkriterium des 900-s-Vorschlagswerts steht seit 15-07 fest** (E14 in
`00-ablauf.md`): belegt werden die FOLGEN einer Frist und nie die Frist selbst.
Der Vorschlagswert bleibt bei 900 s, wenn die Rueckkehr zur Grundlast ueber
300 MB liegt UND die erste Suche nach einer Entladung unter 1,5 s bleibt. Fuer
jedes einzelne Reissen steht vorher da, was folgt.

**Die Deckelzahl, die der Owner in 15-08 vorfindet:** 46 Stunden und 5,40 USD
netto, aus zehn Posten mit 39 h 22 min Planwert und 15 Prozent Zuschlag. Der
Vorgaengerstand 42 h / 4,90 USD (16.09.) bleibt im Runbook daneben stehen, die
Untergrenze 31 h / 3,59 USD unveraendert.

**Abnahmesatz.** Der Owner hat die Phase 14 am 19.09.2026 mit dem Wort
"abgenommen" freigegeben, einschliesslich des franzoesischen Wortlauts des
sechsten Engine-Satzes (unveraendert wie vorgelegt) und des Vorschlagswerts
900 s (bleibt stehen, als Schaetzung deutlich gekennzeichnet). MEM-02 ist von
der Abnahme ausdruecklich ausgenommen und bleibt offen, bis die Box-Anfahrt der
Phase 15 an der Messgroesse "Rueckkehr zur Grundlast nach einem Indexlauf"
gemessen hat.

Was 14-12 belegt hat: der Gesamtlauf aller sechs Gate-Stufen in einem Zug gruen
(2262 bestanden, 15 uebersprungen, Skipzahl unveraendert gegen 13-13), der
Auditbericht `docs/audits/2026-09-phase-14/README.md` mit Gate-Protokoll, ASVS
V5/V7/V12, dem geprueften V4-Vorbehalt, sechs Bug-Pfaden, dem
Performance-Durchgang und der Gegenprobe zu Annahme A9. Drei LOW-Befunde, zwei
behoben (L-01 der fehlende V4-Paritaetsfall, L-03 die Kennzeichnung des
Vorschlagswerts), einer als benannte Asymmetrie weitergereicht (L-02).

Die fuenf Erfolgskriterien sind an der laufenden Instanz nachgesehen: der
Schalter meldet sich in allen drei Stellungen richtig (ohne, `=60`, `=3`), der
Container gibt nach 75 s 376,3 MB zurueck und meldet `unloaded`, die erste Suche
danach antwortet in 1,43 s mit Volltexttreffern (warm 0,41 bis 0,48 s), kein
neuer `cURL error 28`, und die Admin-Seite traegt den Satz des sechsten Zustands
in beiden Haelften gleichlautend.

**Offener Messauftrag an Phase 15** (kein Blocker der Phase 14): die Marge der
ersten Suche nach einer Entladung ist auf der Entwicklungsmaschine duenn, 60 bis
130 ms unter der Decke von 1,5 s. Die Ursache liegt im Nachwaermlauf und nicht
in der Degradation; auf einer langsameren Box koennte sie aufgezehrt werden.

Phase 13 ist vollstaendig (Owner-Abnahme 19.09. erteilt, FILT-01..05 und HART-03 erfuellt)

Phase 12 ist vollstaendig: 12-02 hat den stable35-Entscheid am Stichtag
vollzogen (Zweig a, Beweislauf 35095805558 gruen, deploy-harp-Flag gefallen).

## Entscheide aus der Ausfuehrung

- 16-10 (21.09.2026): **Baustein 1 von BL-F02 faehrt in v1.2.0 mit.**
  Owner-Antwort am Tor im Wortlaut: "Mitfahren", bestaetigt per strukturierter
  Rueckfrage, nachdem Stand der Phase, Umfang, Pruefung der Annahme A7 und
  Abbruchpfad vorlagen. Der Abbruchpfad ist nicht gezogen worden.
- 16-10 (21.09.2026): **Der OCR-Standard bleibt bei drei Sprachen, obwohl neun
  verfuegbar sind.** Ein Standard mit neun Sprachen laedt sechs weitere
  traineddata auf jeder Seite jeder bestehenden Installation und waere eine
  Verhaltensaenderung, die niemand bestellt hat. Verfuegbar ist nicht
  eingeschaltet; wer Spanisch will, setzt `FINDLING_OCR_LANGUAGES`.
- 16-10 (21.09.2026): **Die Existenz der sechs Pakete wird vor dem Bau gegen die
  Paketquelle nachgesehen und nicht aus dem Backlog uebernommen.** Ein anderer
  Befund waere allein schon ein Grund fuer den Abbruchpfad gewesen.
- 16-10 (21.09.2026): **Die Store-Texte bleiben in diesem Plan unberuehrt.**
  Neun Sprachen heisst neun Sprachen im Text, dreisprachig und geschlossen in
  Plan 16-11; ein halber Textstand ueber zwei Plaene waere genau die Drift, die
  dieser Plan an anderer Stelle schliesst.
- 16-09 (21.09.2026): **Q-5 ist zugunsten der deklarierten Filter entschieden
  und gegen den sechsten Engine-Zustand.** Der Zustand faellt zweifach: das Feld
  `engineState` steht schon in v1.1.0 in der Admin-Antwort, und der Wert
  `unloaded` haengt an `unload_count() > 0`, also an einer Leerlaufspanne, die
  der Auftrag nicht faehrt. Eine Zusicherung auf einem Wert, der an einer
  Zeitschaltung haengt, waere ein Flattern und kein Beweis.
- 16-09 (21.09.2026): **Der zweite Kandidat wird billiger gelesen, als die
  Recherche annahm.** Die Filterarbeit der Phase 13 braucht kein gerendertes
  Formular: `/ocs/v2.php/search/providers` traegt die Filterkarte je Anbieter,
  und `integration.yml` liest dieselbe Route seit Phase 1 fuer dieselbe Frage.
- 16-09 (21.09.2026): **Die Vorbedingung in "Store upgrade 1" wird umgedreht
  und nicht geloescht.** Sie verlangt jetzt die ANWESENHEIT des
  `<navigations>`-Blocks und ist damit die billigste Zusicherung der Datei, dass
  `UPGRADE_FROM_TAG` wirklich auf die 1.1.x-Reihe zeigt; eine Marke der
  1.0.x-Reihe antwortete ohne den Block.
- 16-09 (21.09.2026): **Die zwei Zweige des Versionsschritts bleiben beide
  stehen**, obwohl heute nur der erste laeuft. Jeder Release-Zyklus geht einmal
  durch den zweiten: zwischen dem Bump eines Baumes und der Veroeffentlichung
  der passenden Marke sind beide Seiten wieder gleich, und ein geloeschter Zweig
  waere ein roter Lauf, den niemand geplant hat.
- 16-09 (21.09.2026): **`navigation` bleibt im Zustandsabbild, ohne noch
  geprueft zu werden.** Es ist das App-Menue der Instanz zu Protokoll; der Leser
  eines roten Laufs soll es nicht raten muessen.
- 16-09 (21.09.2026): **Ein ueberholter Begruendungsabsatz wird datiert unter
  den neuen gestellt statt geloescht.** Der v1.0.3-Absatz von `UPGRADE_FROM_TAG`
  und der alte Wortlaut der umgedrehten Vorbedingung stehen als Vorgaenger da,
  damit ein Leser sieht, warum die alte Fassung in ihrer Zeit richtig war.
- 16-07 (21.09.2026): **Die Migration verwirft die Versionsmarke und schreibt
  keine an ihre Stelle.** Die Zeichenkette `ownVersion` kommt in der Datei nicht
  vor, und das ist maschinell geprueft: eine Instanz, deren Container wirklich
  eine Minor zurueckliegt, bekaeme mit einer geschriebenen Version Einigkeit
  bescheinigt, und das ist die eine Aenderung, die die Zusage leert.
- 16-07 (21.09.2026): **Der Nachweis, dass der Container nicht gefragt wird,
  sitzt auf dem Konstruktor.** Eine Migration erreicht den Container nur ueber
  einen Mitarbeiter, den sie hereingereicht bekommt; ein Konstruktor mit genau
  einem Parameter vom Typ `IAppConfig` ist die Aussage selbst und nicht ihr
  Schatten.
- 16-07 (21.09.2026): **Der Bump steht vor dem Upgrade-Beweis und nicht erst im
  Plan der Abgabe**, begruendete Abweichung vom Ablauf der Phase 11: der Beweis
  springt von `v1.1.0` auf den Baum und liefe ohne die neue Zahl wieder in
  `ERROR_UP_TO_DATE`. Tag und Abgabe bleiben hinter dem Phasenaudit.

- 16-06 (21.09.2026): **Der innere Aufruf wird auf der PHP-Seite gemessen, nicht
  im Container.** Die Decke gehoert dem Aufruf von PHP nach Container, und nur
  PHP kennt seine volle Dauer: Proxy, HaRP, Container und Rueckweg. Eine Messung
  im Container liesse den Proxyweg weg, also genau den Teil, der die Decke
  reissen laesst, ohne dass der Container etwas davon merkt.
- 16-06 (21.09.2026): **Die Schwelle liegt bei 1.000 ms und damit UNTER der
  kleinsten Zeitdecke.** M-01 beschreibt Aufrufe nahe der Decke; eine Schwelle
  auf der Decke saehe genau die nicht. Sie ist eine Protokollschwelle und keine
  Abbruchgrenze: was einen Aufruf beendet, bleibt `min(Decke, Restbudget)`.
- 16-06 (21.09.2026): **`ceilingMs` traegt die Decke dieses Aufrufs, nicht die
  Konstante.** Geschrieben wird `min(Decke, Restbudget)`, weil ein Aufruf mit
  kleinerem Restbudget sonst gegen eine Grenze ausgewiesen wuerde, die fuer ihn
  nie galt; genau diese Verwechslung ist der Kern von M-01.
- 16-06 (21.09.2026): **Alle vier Fehlerpfade von `call()` tragen die gemessene
  Dauer**, nicht die drei, die der Plan zaehlt. Ein Fehlerpfad ohne Wartezeit
  waere eine Luecke genau dort, wohin M-01 sieht.

- 16-04 (21.09.2026): **Die Vorlaufsonde fragt nur die lexikalische Haelfte.**
  Eine semantische Seite wuerde das Abfragemodell laden und genau den
  Container aufwaermen, dessen Speicher unmittelbar danach gelesen wird; die
  Diagnose-Route traegt denselben Satz. Die Kehrseite steht im Kommentar des
  Werkzeugs: ein Begriff ohne lexikalischen Bestand kann von der Vektorhaelfte
  beantwortet werden, und eine leere Antwort auf ihn faellt auch dann unter
  `ohne-treffer`, wenn der Aufruf abgebrochen ist.
- 16-04 (21.09.2026): **`EmptyResultGroup` behaelt Name und Gesamtzahl.** Die
  Trennung kommt als eigener Schluessel daneben, nicht an seine Stelle, damit
  eine Rohdatei gegen eine von vor dem 21.09.2026 lesbar bleibt. Das ist die
  Haelfte von DI-10-01, die beim Schliessen von DI-11-03 nicht verloren gehen
  darf.
- 16-04 (21.09.2026): **Eine Teilantwort der Sonde gilt als Ausfall.** Eine
  Trennung auf einem Teil der Begriffe schriebe zwei Lesarten in dieselbe
  Rohdatei; die leere Menge waere die Behauptung, jeder Begriff habe Bestand.
- 16-04 (21.09.2026): **Das Schluesselpaar wird nach Instanz und Datentraeger
  geloescht**, nie davor: ein Abbruch dazwischen liesse eine laufende Instanz
  zurueck, die niemand mehr betreten und damit von innen nicht mehr anhalten
  kann. Geloescht wird nur die oeffentliche Haelfte.

- 16-02 (21.09.2026): **Zwei Fehlalarm-Mechanismen des Auditberichts sind als
  benannte Regeln in das Gate verengt worden, statt als Ausnahmeeintraege
  gelistet zu werden.** Ein reiner Hexlauf ist eine Pruefsumme, ein Lauf, den
  Schraegstriche in lauter Stuecke unter 40 Zeichen zerlegen, ist ein Pfad, und
  bei der IPv4-Form sind Oktette ueber 255 oder mit fuehrender Null gruppierte
  Zahlen, waehrend die reservierten Bereiche keine Maschine dieses Kontos
  nennen. Beides steht woertlich in der Erklaerung der Treffer des Audits. Ohne
  die Verengung traegt die Ausnahmeliste allein fuer die base64-Familie 30
  Dateien und fuer das Muster der Umsetzung 58 statt 19, und eine Liste dieser
  Groesse ist die Vorstufe der stillen Abschaltung.
- 16-02 (21.09.2026): **Die Ausnahmeliste hat eine Ratsche in beide
  Richtungen.** Ein unbegruendeter Fund macht das Gate rot, und ein Eintrag,
  dessen Fund verschwunden ist, ebenfalls. Ohne die zweite Richtung waere die
  Liste ueber die Phasen nur gewachsen, und Plan 16-05 haette bereinigen
  koennen, ohne die Zeilen mitzunehmen.
- 16-02 (21.09.2026): **Die Vokabularregel liest die englische Endung und nicht
  den Stamm.** Getroffen ist jede Form, der kein e folgt; das ist Entscheid E-H2
  mechanisch gemacht. Der Preis ist bekannt und benannt: der deutsche Plural
  faellt mit der englischen Form zusammen und bleibt ungesehen. Der dritte
  Selbsttest der Familie sagt genau das aus.
- 15-16 Task 3 (21.09.2026): **Phase 15 vom Owner abgenommen, im Wortlaut
  "ziel ist das wir den usern das best mögliche liefern", als Abnahme mit
  Auflagen bestaetigt.** Auflagen A1 bis A4 an Phase 16 (92c/99d,
  Geheimnis-Gate + Altfunde, M-01-Instrumentierung, kleine
  Sprachfaelle-Anfahrt mit Deckel-Freigabe vor Start); Top-up-A/B-Attribution
  bewusst nicht beauftragt. Dependabot-PR #10 (tantivy 0.26.2) wird
  geschlossen, tantivy per Ignore-Anweisung ausgenommen; der Pin bewegt sich
  nur noch bewusst, mit Reindex-Plan.
- 15-16 (21.09.2026): **MESS-05 ist abgehakt, mit einem Vorbehalt, der mit dem
  Haken nicht verschwindet.** Alle vier Messauftraege haben Zahlen mit
  Rohdateiverweis, und der Deckel war vor dem Start freigegeben; das ist die
  Abhakregel des Plans. Der Vorbehalt steht in derselben Statuszeile: die
  Sprachfall-Messung ist auf der Box MIT dem Fremdbestand gefahren, weil der
  Korpus-Snapshot der Fremdbestand ist. Deshalb wird Erfolgskriterium 4 der
  ROADMAP dem Owner als NICHT erfuellt vorgelegt und nicht umgedeutet.
- 15-16 (21.09.2026): **MEM-02 ist abgehakt, und der Haken haengt an einer Zahl
  und nicht an einer Frontmatter.** `rueckkehr-zur-grundlast-mb = 377,5` an der
  Messgroesse "Rueckkehr zur Grundlast nach einem Indexlauf", Rohdatei
  `docs/measurements/2026-09-v12-messung/rohdaten/94b-grundlast-rueckkehr.txt`.
  Die Sichtprobe aus 14-12 (376,3 MB auf einer Maschine ohne malloc_trim) bleibt
  ausdruecklich ein Hinweis; die Naehe der beiden Zahlen ist Zufall und kein
  Beleg. Das ist die zweimal bezahlte Lehre aus 14-01 und 14-04.
- 15-16 (21.09.2026): **Die Zahlen der Anfahrt wandern nach `docs/performance.md`
  als datierte Nachtraege und ersetzen nichts.** Fuenf Nachtraege, je mit Datum,
  Maschine und Verweis auf das Messverzeichnis, dazu fuenf Zeilen in "Stand
  dieses Berichts". Der alte Cron-Befund zu DI-10-04 bleibt stehen, wie er ist,
  einschliesslich des Satzes, der Beleg stehe aus; darunter steht jetzt, dass er
  gefahren ist. Eine alte Zahl bleibt gueltig fuer die Bedingungen, unter denen
  sie entstand (Muster 14-11).
- 15-16 (21.09.2026): **Die Marge der ersten Suche steht mit ihrem ABSTAND zur
  Decke da und nicht als blosses Unterschreiten** (Entscheid aus 14-12). Damit
  wird sichtbar, was der Bericht in seiner Gegenueberstellung nicht betont: drei
  der vier Auspraegungen liegen ueber 1,5 s, und eine davon (Schalter 0, warmer
  Cache, 1.613 ms) hat mit der Entladung nichts zu tun. Gefuehrt als Befund M-01
  des Phasenaudits, weitergereicht an Phase 16.
- 15-16 (21.09.2026): **Die Geheimnis-Gegenprobe des Audits benutzt ein anderes
  Verfahren als die Gates der Umsetzung.** Die Plaene 15-09 bis 15-14 suchten
  Formen von Kennungen (`i-`, `vol-`, IPv4). Die Gegenprobe sucht acht andere
  Familien (PEM-Kopf, SSH-Material, AWS-Zugangskennungen, uebrige
  Ressourcenkennungen, Rechnernamen, Schluesselwort-mit-Wert, IPv6,
  base64-Bloecke ab 40 Zeichen) und laeuft ueber ALLE 80 committeten Dateien der
  Phase statt nur ueber die Rohdaten. Ergebnis: kein Geheimnis, vier erklaerte
  Treffer.

- 15-15: Die drei verfehlten Erwartungen bekommen das Wort "verfehlt" und
  keinen Zusatz, der es weichspuelt, auch E10 nicht, die in die GUENSTIGE
  Richtung verfehlt ist (Stufe 8 haelt das Budget mit 508,0 ms Reserve statt
  mit weniger als 374,5 ms). Eine Erwartung, die nach dem Lauf zu ihrem
  Ergebnis umgebogen wird, ist keine Erwartung mehr, und das gilt in beide
  Richtungen. `00-ablauf.md` ist in dieser Phase unberuehrt geblieben (letzter
  Commit 190d5c7 aus 15-07), also ist der Wortlaut der vierzehn der Wortlaut
  von vor dem Lauf.
- 15-15: E13 ist "verfehlt" und nicht "nicht entschieden", obwohl ihre erste
  Haelfte haelt. Der Riss liegt in der Erwartung selbst: sie vergleicht die
  16 MB Zuwachs JE ZYKLUS aus dem Vorprueflauf mit dem absoluten Rueckstand
  nach EINEM Zyklus. Getrennt wird deshalb die Berichterstattung und nicht die
  Erwartung; die Zahl, die zaehlt, ist 731,9 MB residenter Stand, und sie geht
  als eigene Zahl an den Owner.
- 15-15: E14 ist "gehalten". Die Regel hat entschieden, nur nicht in ihrer
  Hauptzeile, sondern in der E12-Verzweigung, und der Owner ist ihr gefolgt
  ("900 s bleibt + Vorbehalt"). Ein Belegkriterium, das seinen eigenen
  Riss-Fall vorher benannt hat, ist genau dann gehalten, wenn dieser Fall
  eintritt und trotzdem niemand nachverhandelt.
- 15-15: Die Wirkung der Top-up-Route wird im Bericht als NICHT ENTSCHIEDEN
  ausgewiesen, obwohl der Lauf 7 h 17 min kuerzer war. Die Instanz ist aus
  einem Snapshot neu aufgebaut und das Abbild gewechselt; beide Erklaerungen
  bleiben moeglich, und genau dieser Satz stand vor dem Lauf in 00-ablauf.md.
  Die 5,35 h weniger Leerlauf erklaeren rund drei Viertel des Zeitgewinns; das
  restliche Viertel wird NICHT zugeordnet, weil das eine Schaetzung waere.
- 15-15: Die falschen erwarteten Ausgaben des Runbooks werden NICHT ersetzt,
  sondern bekommen ihre Richtigstellung daneben. Vier sind es (harte Grenze in
  beiden cgroup-Feldern, 91 MB der Systemplatten-Sicherung, docker+ncdata als
  vollstaendiger Inhalt, Arbeitsbaum aus Block 9). Eine ersetzte Erwartung
  liesse nicht mehr erkennen, woran ein Werkzeug gescheitert ist, und an der
  ersten von ihnen ist 92b-wechsel.sh gescheitert.
- 15-15: Das Abbruchtor in Abschnitt 5 des Runbooks bekommt ZWEI Fassungen
  statt einer Korrektur, und welche gilt, entscheidet der Abbildwechsel. Mit
  Block 13b davor ist der Indexbeleg 52.111 strukturell nicht mehr ablesbar,
  weil --rm-data das Datenvolume leert; der Korpus tritt an seine Stelle. Der
  Owner hat den Ersatz am 20.09. mit "Weiter, Korpus als Beleg" freigegeben.
- 15-15: Der Entladezaehler bleibt in Abschnitt 7.2 stehen und bekommt den
  Nachtrag, dass es ihn ueber eine Prozessgrenze nicht gibt. Rueckgabewert 31
  faellt ab jetzt am Ausbleiben von `engineState unloaded` ODER der
  cgroup-Differenz, und `engineState` wird an der Admin-Seite SELBST gelesen,
  weil 96d-statusbeobachter.py als gefahrene Fassung nicht geaendert wird.
- 15-15: Die Ist-Spalte des Rechenblatts misst gestempelte MESSZEIT und nicht
  Kosten. Die Differenz zwischen der Summe der Posten und den 25,75 h
  Box-Laufzeit ist Sitzungszeit und ausdruecklich KEINE Reserve; wer den
  naechsten Deckel rechnet, nimmt die Ist-Werte als Untergrenze je Posten.
  Annahme A8 (Handaufbau, geschaetzt 2 h 30 min) hat ihren Schaetzcharakter
  verloren: rund 0 h 40 min fuer die Bloecke 1 bis 9 zusammen, weil kein Block
  eine eigene Zeitmarke geschrieben hat. Der Nachtrag daraus ist ein Handgriff:
  jeder Block stempelt kuenftig Eintritt und Austritt.
- 15-15: Der Pruefsummen-Waechter friert den Stand NACH der Anfahrt ein, auch
  fuer die zwei Fassungen, die waehrend der bezahlten Zeit geaendert wurden
  (92b-wechsel.sh, 97-cron-vorpruefung.sh). Das ist kein Nachgeben: genau
  dieser Stand hat die zitierten Rohdaten geschrieben. Die Annahme des Plans,
  keines der sechs sei geaendert worden, ist als Befund in der SUMMARY
  festgehalten, mitsamt den Pruefsummen der Staende davor.
- 15-15: Der Satz "waehrend der bezahlten Anfahrt wird kein Werkzeug mehr
  geaendert" bleibt im Runbook stehen und bekommt seine Ausnahme
  ausbuchstabiert statt aufgeweicht: geaendert wird nur, wenn ein Werkzeug
  einen Abbruch auf einem KORREKTEN Zustand erzeugt, nur mit Owner-Wort, und
  die Messzahlen stammen dann aus dem Lauf nach dem Fix. Alle drei Fixe dieser
  Anfahrt (d6fb185, ff8e054, 6f42c69) waren von dieser Art.

- 15-06: Das Abbild des Wechsels wird aus ABBILD_REPO und ABBILD_DIGEST
  zusammengesetzt; IMAGE ist keine zweite Stellschraube mehr. Zwei getrennte
  Angaben sind genau der Fall T-10-13, in dem der Baumhash ein Abbild prueft,
  waehrend die Registrierung darunter ein anderes faehrt. ABBILD_DIGEST hat
  keinen Vorgabewert und wird vor dem ersten mkdir geprueft.
- 15-06: Der Rueckgabewert 36 traegt zwei Faelle, wie 32/33 in 15-04 und 34/35
  in 15-05. Der zweite faellt nach der Registrierung: AppAPI setzt
  registry/image:tag zusammen und kennt keinen Digest, also wird die
  Abbildkennung aus dem Container gelesen und gegen die des per Digest
  gezogenen Abbilds gehalten. Das gezogene Abbild wird vorher lokal auf den
  Tag der info.xml gelegt; das ist die Vorkehrung, der Beweis bleibt die
  Kennung aus dem Container.
- 15-06: Die Zaehlung der Nextcloud-Instanzen steht zweimal in der Datei, und
  das Gate misst den ABSTAND und nicht das Vorhandensein. Ein Gate auf blosses
  Vorhandensein bliebe gruen fuer ein zweites --rm-data, das jemand unten
  anhaengt, weil die Zaehlung der Phase A weit darueber steht. Eine unlesbare
  Zaehlung gilt als ungleich eins.
- 15-06: Der Runbook-Aufruf in Block 13b ist auf ABBILD_DIGEST umgestellt
  worden (Abweichung Rule 3). Der bisherige IMAGE-Aufruf haette auf der
  bezahlten Box mit 2 geendet, und der Operator haette den Grund in einem
  Runbook gesucht, das ihn nicht nennt.

- 15-05: Der Filter- und Sortierblock misst ausschliesslich ueber die
  Seitenroute, und `scripts/ops/search_load.py` wird weder angefasst noch
  gerufen. Die beiden OCS-Provider kennen `types` und `sort` nicht (Befund
  13-12); ein Aufruf des Lastwerkzeugs maesse ungefiltert und saehe dabei aus
  wie eine Filtermessung. Ein Gate haelt fest, dass sein Name in der Datei nur
  in Kommentarzeilen vorkommt.
- 15-05: Die drei Sortiernamen werden im Test aus `SORT_MODES` des Pakets
  gelesen und gegen die eine Zeile gehalten, in der das Werkzeug sie fuehrt
  (`SORTIERMODI`). Eine im Test wiederholte Liste waere sich selbst einig an
  dem Tag, an dem das Erzeugnis einen vierten Namen bekommt, und ein
  unbekannter Name faellt dort still auf `relevance` zurueck.
- 15-05: Ausser Seite 1 baut das Werkzeug keine Adresse. Der Weiter-Link wird
  mit seiner Auszeichnung `findling-pager__step--next` aus der Antwort gezogen,
  weil der Fingerabdruck ueber die rohen Adresswerte laeuft und eine gebaute
  Adresse ohne `fp` den stillen Rueckfall auf Seite 1 misst (13-08). Ein Gate
  verbietet die Positionsangabe im Code des Werkzeugs.
- 15-05: Die Rueckgabewerte 34 und 35 tragen je zwei Faelle. Abschnitt 7.1 des
  Runbooks hat ihnen den wachsenden Bestand (34) und die Stufe ohne
  Antwortzahlen samt doppelter Datei-Kennung (35) gegeben, der Plan 15-05 den
  Sortierlauf ohne Trefferzahl (34) und den fehlenden Weiter-Link samt
  verworfenem Cursor (35). Beide Lesarten sind umgesetzt, wie schon bei 32 und
  33 in 15-04.
- 15-05: Die gemeldete Seitenzahl wird aus der Marke des Blaetterns gelesen und
  nicht aus einem Adressparameter. Die Uebersetzung dreht das Wort davor um,
  die Zahl bleibt eine Zahl, und genau diese Ablesung faengt den stillen
  Rueckfall.
- 15-05: Ein Entladeschalter ungleich 0 bricht diesen Block NICHT ab. Er ist
  ein protokollierter Befund neben den Zahlen; abgebrochen wird nur bei
  unlesbarer Stellung (29), weil Abschnitt 6.4 die Zeile und nicht die Stellung
  verlangt.
- 15-04: Der Indexlauf wird ueber den Weg eines Nutzers angestossen und nicht
  ueber `occ findling:index --restart`. Der Befehl kennt nur --status und
  --restart, und --restart stellt rund 52.000 Dokumente neu in die Schlange:
  der Container fiele dann in dieser Messung nie in den Leerlauf und entluede
  nie. Angestossen wird deshalb mit einem Dutzend kleiner Textdateien ueber
  WebDAV plus `files:scan`; der Korpus wird nach der letzten Marke wieder
  entfernt, damit der Bestand der Box derselbe bleibt, gegen den Schritt 9
  misst.
- 15-04: Der Indexlauf wird an der Zahl der eingebetteten Dokumente der
  Admin-Seite belegt (Feld `embedded` unter `backend`) und nicht an der Ausgabe
  von `occ findling:index`. Deren Zaehler `indexed` ist auf der Nextcloud-Seite
  strukturell null und sagt das selbst; die occ-Ausgabe liefert den
  Arbeitsvorrat und steht als zweite Bedingung daneben. Nachtrag ins Runbook in
  15-15.
- 15-04: Gerechnet wird ueber `anon` aus `memory.stat` und nicht ueber
  `memory.current`. `memory.current` zaehlt den Seitencache derselben cgroup
  mit, und der Tantivy-Index ist ein mmap auf der Platte; eine Differenz
  darueber maesse zu einem guten Teil, wie viele Indexbloecke zwischen den
  Marken gelesen wurden. `memory.current` wird in jeder Marke mitgeschrieben,
  weil der docker-Client genau diese Zahl zeigt.
- 15-04: Marke A verlangt einen Containerneustart VOR der Messung. Nach den
  Schritten 4, 6 und 8 ist der Container aufgewaermt; ohne Neustart maesse
  Marke A einen Container mit Tokenizer, Splitter und Sitzung darin und waere
  keine Grundlast vor dem Indexlauf.
- 15-04: Die Rueckgabewerte 32 und 33 tragen je zwei Faelle. Das Runbook hat
  ihnen in 15-02 den fehlenden Bezugswert (32) und den neu gebauten Container
  (33) gegeben, der Plan 15-04 die fehlende Zahl aus der Abtastreihe (32) und
  den ausgebliebenen Indexlauf (33). Keine Bedeutung ist weggefallen; eine
  einmal vergebene Zahl wird nicht umgehaengt. Nachtrag in 15-15.
- 15-04: Der MEM-02-Block verlangt einen Entladeschalter groesser null, und
  eine 0 endet mit 29 wie eine fehlende Stellung. Bei 0 gibt es keine Freigabe,
  die Ruhezeit verginge ohne Wirkung, und die Zahl am Ende waere die Groesse
  eines Containers, der einfach nichts getan hat.
- 15-03: `engineState` wird an der Admin-Seite SELBST gelesen und nicht ueber
  `96d-statusbeobachter.py`. Dessen Aufzeichnung ist auf sechs Zaehler,
  `runState`, `backendReachable` und das genestete Paar projiziert; das Feld ist
  dort nicht darunter, weil das Werkzeug aus dem v1.1-Lauf stammt. Eine
  gefahrene Fassung wird nicht geaendert, also geht das neue Skript dieselbe
  Anmeldung und liest ein Feld. Nachtrag ins Runbook in 15-15.
- 15-03: Der Entladezaehler ist ueber eine Prozessgrenze nicht lesbar (keine
  Route, eigener Zaehler je Prozess). Beleg der Entladung sind deshalb
  `engineState unloaded` UND die cgroup-Groesse `memory.current` vor und nach
  der Ruhezeit als zweiter, unabhaengiger Anhaltspunkt. Nachtrag in 15-15.
- 15-03: Die semantische Seite wird an der Trefferzahl der Nutzerroute gegen
  eine Referenzzahl aus demselben Lauf abgelesen (Waermsuche in 1 und 2, zweite
  Suche in 3 und 4). Die Route traegt kein Feld dafuer, und `degraded` meint den
  unvollstaendigen Index und nicht die fehlenden Gewichte.
- 15-03: Die Bereitschaft nach dem Containerneustart wird an der Admin-Seite
  gefragt und NIE mit einer Suche: eine Suche als Bereitschaftsprobe waere in
  den Auspraegungen 3 und 4 die erste Suche ueberhaupt, also genau die
  Messgroesse.
- 15-03: `exit 2` steht oberhalb der Pipeline, nur 29, 30 und 31 darunter. Ein
  Aufruf ohne Auspraegung darf keine Rohdatei schreiben, und die Pipeline
  schreibt sie.
- 15-02: Die verkuerzte Ruhezeit (D-02) kuerzt den Deckel NICHT. Der Planwert
  der Wiederaufwaerm-Messung bleibt bei 2 h 00 min; ein Planwert, der eine
  Verbesserung vorwegnimmt, ist genau der Fehler, der den v1.1-Deckel gerissen
  hat. Die Ersparnis ist ausgewiesene Reserve, und die Abweichung vom
  Vorschlagswert 900 s ist begruendungspflichtig im Protokoll.
- 15-02: Der Vorgaengerstand des Deckels (42 h / 4,90 USD, 16.09.) wird nicht
  geloescht, sondern neben der neuen Empfehlung gefuehrt. Eine Zahl, die ueber
  Nacht waechst und deren Vorgaenger fehlt, sieht aus wie ein Aufschlag; die
  Differenz von vier Stunden ist die Summe dreier Posten, die vorher schlicht
  nicht im Rechenblatt standen.
- 15-02: Der Abbildwechsel und `baumhash-gleich` widersprechen sich nicht.
  Gewechselt wird einmal, in Block 13b, vor der ersten Messung, und genau dieser
  Vorgang stellt `baumhash-gleich ja` erst her. Ab der ersten Messung gilt die
  Haltebedingung wieder; ein Wechsel waehrend der Messreihe waere ein zweiter
  Messgegenstand unter dem Namen des ersten.
- 15-02: Die Nummern der Rueckgabewerte folgen dem Katalog und nicht der
  Messreihenfolge. Schritt 6b bricht mit 34 und 35 ab, Schritt 8b mit 31 bis 33,
  obwohl 6b zuerst laeuft. Eine einmal vergebene Zahl wird nicht umgehaengt,
  damit Rohdaten frueherer Laeufe lesbar bleiben.
- 15-01: Eine Kopie traegt den Dateimodus ihres Originals mit. Die vier im
  Original ausfuehrbar abgelegten Werkzeuge liegen auch in der Kopie mit 100755
  im Index, die uebrigen sieben mit 100644; damit stimmen Blobkennung UND Modus
  ueberein, und die Gleichheit ist an `git ls-files -s` ablesbar und nicht nur
  an einer Pruefsumme.
- 15-01: Der Kopie-Waechter vergleicht Kopie gegen Original statt gegen eine
  aufgeschriebene Pruefsumme. Bei den gefahrenen Fassungen steht die Zahl in der
  Datei, weil das Original selbst wandern koennte; hier ist genau die Gleichheit
  der beiden Dateien die Zusage, und eine dritte aufgeschriebene Zahl waere eine
  weitere Stelle, die driften kann.
- 15-01: Neben dem Pruefsummenfall haelt ein zweiter Fall die vollstaendige
  Werkzeugliste der Messreihenfolge (vierzehn Namen, elf Kopien plus die drei
  bereits vorhandenen). Die Werkzeuge aus 15-03 bis 15-06 stehen bewusst NICHT
  darin: eine Liste, die kuenftige Dateien nennt, waere heute rot aus einem
  Grund, der kein Befund ist.

- 14-12 (Abnahme): Der fehlende V4-Paritaetsfall wird angelegt und nicht nur
  protokolliert. Die Lehre aus 13-13 gilt: ein Audit-Pfad ohne Gate bekommt ein
  Gate. Vier Faelle in `test_semantic_search.py` halten, dass die entladene
  Runde hinter dem ACL-Vorfilter bleibt und dass `may_load` in keiner PHP-Quelle
  steht.
- 14-12 (Abnahme): Die Sichtprobe zur ersten Suche nach einer Entladung wird
  mit ihrem Abstand zur Decke berichtet und nicht als blosses Unterschreiten.
  1,37 bis 1,44 s kalt gegen 0,41 bis 0,48 s warm ist eine duenne Marge, und die
  Zahl gehoert dem Owner vor die Abnahme; die Ursache liegt im Nachwaermlauf und
  nicht in der Degradation (die einwortige Zeile ohne Vektoranteil misst
  dasselbe).

- 14-11 (Dokumentation): Der alte Abschnitt "Modell-Entladung nach Leerlauf:
  nein, mit drei Zahlen" in `docs/performance.md` wird nicht geloescht, sondern
  bekommt einen datierten Nachtrag. Seine drei Zahlen gelten weiter (die
  Entladung senkt weder die Spitze eines Indexlaufs noch die Grundlast eines
  Containers, der nie eingebettet hat); ueberholt ist nur sein Schluss, und
  Punkt 3 ist durch die Degradationsnaht aus 14-08 entschaerft.

- 14-11: Die Messgroesse steht als ASCII-Bezeichner
  `Rueckkehr zur Grundlast nach einem Indexlauf` in Backticks, obwohl
  `docs/performance.md` sonst Umlaute in Ueberschriften traegt. Sie ist ein
  Name, gegen den spaeter gegriffen wird, und ein Name traegt keine Umlaute.

- 14-11: Der A/B-Messschritt des Runbooks beginnt mit den Kaltmessungen. Jede
  Messung waermt den Seitencache des Wirts, und eine einmal gewaermte
  Kaltmessung ist ohne erneutes Leeren nicht wiederholbar. Die Reihenfolge ist
  deshalb bindend und keine Empfehlung.

- 14-10 (MEM-05, die Zusage): Die Freigabe der vierten Phase laeuft ueber
  `shared_model().release()` und nicht ueber `release_if_idle`. Die Politikstelle
  traegt die Uhr, und ihre Frist kommt aus `embed_idle_release_seconds`, wo null
  das Wort fuer aus ist: in der Werksstellung antwortet sie sofort False und
  wuerde nichts messen, eingeschaltet wuerde das Werkzeug eine Admin-Einstellung
  aussitzen. Gemessen wird die Mechanik der Zusage, nie die Frist.

- 14-10: Nachgeladen wird ueber `drive_the_search_side()` und nicht ueber
  `engine.warm()`. Das Werkzeug misst seit seiner ersten Fassung durch den
  echten Aufrufweg; ein Aufrufer, der aufhoert, ueber den Halter zu gehen, soll
  auffallen statt gemessen zu werden.

- 14-10: Die Mutation "Warmfenster laedt zweimal" haengt am Entladezaehler und
  gilt deshalb erst ab der vierten Phase. Ein von Anfang an gebrochenes
  Single-Flight haette auch den zweiten Track ein zweites Mal laden lassen, das
  Werkzeug waere am alten Zaehler rot geworden, und der Fall haette den falschen
  Befund belegt.

- 14-10: Die Fehlerausgabe des Schritts in `resilience.yml` wird mitgezogen,
  obwohl das Abnahmekriterium des Plans nur Kommentarzeilen vorsah. Der Plan
  verlangt in seinen must_haves ausdruecklich, dass der Erklaertext IM
  FEHLERPFAD die alte Zusage nicht mehr sagt, und genau dort stehen die
  echo-Zeilen. Aufruf, Exit-Behandlung und Artefakt des Schritts sind
  unveraendert.

- 14-09 (MEM-05, das sechste Wort): Der Zustand wird aus dem monotonen
  Entladezaehler abgeleitet und nicht aus einem neuen Feld. Ein Feld haette
  gesetzt werden muessen, ein Zaehler ist schon da, und er hat eine Eigenschaft,
  die hier zaehlt: ein Prozess, der nie entladen hat, steht auf null und kann
  das Wort gar nicht melden. Der Zweig steht hinter `loaded`, weil ein Container,
  der nach einer Freigabe wieder geladen hat, geladen ist.

- 14-09: Die sechs Katalogeintraege reisen im selben Commit wie die zwei
  Seitenhaelften und die zwei Gate-Literale. Das Satz-Gate sucht die neuen Saetze
  im deutschen Katalog, also waere jede andere Reihenfolge ein roter Commit
  gewesen. Die Dokumentationshaelfte ist ein eigener Commit geblieben.

- 14-09: Der Entladezaehler wird je Testfall in `conftest.py` auf null gesetzt
  (`forget_the_release_count`, nach dem Muster von `forget_the_cutter_notice`).
  Ohne das entscheidet eine Freigabe in `test_embed_model.py`, was
  `test_status_endpoint.py` drei Dateien spaeter als Zustand liest. Im Container
  wird nichts zurueckgesetzt, T-14-17 bleibt unberuehrt.

- 14-08 (MEM-03, die Naht): `request_warm()` steht in `one_round` an der Zeile,
  an der die `SemanticSide` ohne Ladeerlaubnis gebaut wird, und nicht im
  Handler. Nur dort sind beide Haelften des Satzes bekannt: dass die Runde
  hybrid gemeint war und dass sie ohne Gewichte antwortet. `one_round` reicht
  Kandidaten zurueck und nicht den Grund, warum keine Vektoren dabei sind; der
  Handler fragt deshalb nur noch `warm_wanted()`.

- 14-08: Der Fall zur Antwortzeit laeuft bewusst **ohne** `TestClient`. Dessen
  Portal wird je Anfrage geoeffnet und beim Schliessen wartet es auf jede
  Aufgabe, die drinnen gestartet wurde; eine Messung um `client.post` herum
  meldet also die Laenge des Hintergrundlaufs, egal was der Handler tut. Unter
  uvicorn ueberlebt der Loop die Anfrage. Der Fall ruft den Handler deshalb
  direkt auf dem Loop des Testfalls.

- 14-08: `api/diagnose.py` bekommt nur einen Kommentar und keinen Schalter. Ein
  Messwerkzeug muss messen koennen, die Route traegt keine 1,5-Sekunden-Decke
  und ist keine Nutzerroute. Die Kehrseite (ein Diagnoseaufruf waermt den
  Container auf und darf vor einer Kaltmessung nicht gemacht werden) gehoert
  ins Runbook 14-11.

- 14-07 (MEM-02, der Aufrufer): Die Entladung bekommt einen eigenen Takt in der
  Lifespan und sitzt NICHT im Leerlaufzweig des Pollers. Ein stummgeschalteter
  Poller wartet in `run()` auf sein Armiert-Ereignis und betritt `run_once` nie
  wieder (`poller.py:543-545`), und genau dieser Container, der nicht indexiert
  und nur gelegentlich durchsucht wird, ist der Fall, fuer den die Entladung
  gebaut ist.

- 14-07: `release_cutter()` steht HINTER einer Freigabe, die `True` geliefert
  hat, und nicht daneben. `release_if_idle` traegt die Uhr und die
  Identitaetspruefung, `release_cutter` traegt keine eigene Frist; ein
  `release_cutter` ohne vorangegangene Freigabe wuerde den Cutter nach jeder
  Ruhephase wegwerfen, auch wenn die Suchseite gerade eingebettet hat.

- 14-07: Bei ausgeschaltetem Schalter gibt es keine Logzeile. Der Werksstand ist
  aus, und eine Zeile bei jedem Start ueber eine Funktion, die niemand
  eingeschaltet hat, ist Rauschen. Der Behavior-Block des Plans verlangte das
  Gegenteil, der begruendete Action-Block hat Vorrang bekommen; der Kommentar im
  Quelltext sagt, warum hier auch spaeter kein `else`-Zweig "zur Symmetrie" mit
  dem Reconcile-Block hingehoert (der Abgleich ist ab Werk AN, deshalb ist seine
  Aus-Zeile ihren Platz wert).

- 14-07: Direkt hinter `_pause` wird das Stopp-Event ein zweites Mal gelesen und
  der Takt abgebrochen. Ohne diesen Blick liefe im Herunterfahren noch ein
  vollstaendiger Takt, und ein dort gestarteter Warmlauf haelt den Prozessausgang
  sekundenlang in einem Threadpool-Thread fest (T-14-26). Das ist eine Zeile
  mehr, als der Plan vorsah, und sie ist es, die das Budget von 5,0 s haltbar
  macht.

- 14-06 (MEM-03, obere Haelfte): `query_may_load()` ist die eine Stelle, an der
  steht, ob eine Suche laden darf, und sie antwortet
  `settings().embed_idle_release_seconds == 0`. Die Degradation haengt damit am
  Schalter und gilt nicht generell: der Vorfall vom 10.09.2026 war die
  allererste Suche eines Containers, der nie entladen hatte, und eine Naht ohne
  Schalter wuerde ihn generell abstellen, waere aber eine Verhaltensaenderung
  ausserhalb des Schalters, und die eine Box-Anfahrt der Phase 15 wuerde zwei
  Aenderungen auf einmal messen. Der Generalfall ist Backlog. `api/diagnose.py`
  ruft die Funktion bewusst nicht und laedt weiter (ein Messwerkzeug muss messen
  koennen); die Kehrseite, dass ein Diagnoseaufruf den Container aufwaermt,
  gehoert ins Runbook 14-11.

- 14-06: `release_if_idle(ttl)` prueft die Identitaet des Halters unter `_LOCK`
  mit `is` und gibt erst danach frei, weil das Nachwaermen aus MEM-03 neben der
  Entlade-Aufgabe laeuft und eine Kollision sonst das gerade bezahlte Ladepaar
  wegwerfen wuerde (T-14-20). Der Auftrag aus 14-05 ist damit erledigt, und er
  ist in `engine.py` gelandet und nicht in `release()`: die Mechanik bleibt
  unten, die Politik steht oben. `release()` wird ausserhalb von `_LOCK`
  gerufen, weil Sammeln und Trimmen blockieren (T-14-16); drei Gates am
  Syntaxbaum halten Lage, `_held`-statt-`shared_model` und `is`-statt-Wert fest.

- 14-06: `ttl <= 0` und `last_use() is None` antworten beide `False`, ohne den
  Halter zu fragen. Null ist das Wort fuer aus und keine Frist von null
  Sekunden; `None` ist ein Halter, der geladen hat und nie eingebettet hat, und
  das ist kein Leerlauf, sondern nichts zum Loslassen (Uebergabe aus 14-05).

- 14-06: Die Zusage "genau ein Laden je warmem Fenster" ist strukturell erfuellt
  und nicht durch das Flag: `_load()` laeuft unter dem Lock des Halters und
  kehrt am Kopf zurueck. `_WARMING` spart die neun wartenden Threadpool-Threads
  und ist im Docstring ausdruecklich als Effizienz und nicht als Zusage
  benannt, damit niemand es spaeter fuer die Zusage haelt. Der Zehn-Threads-Fall
  misst den Zuwachs von `load_count()` und nie ein Byte.

- 14-06: `warm()` laedt ueber `shared_model().embed_query(WARM_TEXT)` und setzt
  damit die Leerlauf-Uhr mit. Das ist die Bedingung und kein Nebeneffekt: ohne
  die Uhr entlaedt der naechste Takt sofort wieder. `WARM_TEXT` ist eine feste
  Modulkonstante ohne Nutzerinhalt und ohne Dateinamen (T-14-22).

- 14-06 (Lehre, dritte Auflage): Der Baumhash musste erneut in jedem
  Produktcode-Commit nachgezogen werden, weil der Plan
  `tests/test_measurement_scripts.py` wieder nicht in `files_modified` fuehrt.
  Das ist jetzt der vierte Plan in Folge. Zusaetzlich neu: die beiden
  `<verify>`-Befehle des Plans (`pytest -k "may_load"` und
  `-k "release_if_idle"`) waehlten mit den urspruenglichen Testnamen keinen
  oder nur einen Fall aus; die Namen wurden nachgezogen. Ein Pruefbefehl, der
  nichts auswaehlt, ist ein gruenes Nichts.

- 14-05 (Suchseite): `release()` gibt unter `self._lock` los und zaehlt, ruft
  `gc.collect()` und `malloc_trim(0)` aber AUSSERHALB davon: beide blockieren,
  und ein gehaltenes Lock wuerde jede gleichzeitige Suche mitblockieren
  (T-14-16). Die Reihenfolge sammeln, dann trimmen ist nicht umkehrbar und wird
  zur Laufzeit und im Quelltext geprueft. Der Vorprueflauf hat die Aufteilung
  gemessen: `gc.collect()` allein 15,1 bis 18,2 Prozent, der Trim die uebrigen
  80,2 bis 84,9. Die Zahlen des Research-Beispiels (20 und 5 Prozent) stammen
  aus der Vorrecherche und sind durch den Lauf ueberholt.

- 14-05: Der Aktivitaetszaehler `_in_flight` steht im SELBEN Lock-Block, in dem
  die Engine gebunden wird, und nicht dahinter. Dazwischen laege ein Fenster,
  in dem eine Freigabe aus einem anderen Thread den Heap eines startenden
  Batches sammeln und trimmen duerfte. Das ist die einzige neue Invariante
  dieser Phase (T-14-15).

- 14-05: `may_load` sitzt an `embed_query` und `_embed` mit Vorgabe `True`,
  `embed_passages` bekommt den Schalter bewusst nicht: ueber einem Indexlauf
  steht keine 1,5-Sekunden-Decke, und nach einer Entladung ist die naechste
  Zeile des Laufs der richtige Moment zum Wiederladen. Die Regel, wann der
  Schalter falsch ist, liegt in 14-06; `model.py` liest keine Einstellung.

- 14-05: Keine Identitaetspruefung in `release()`. Sie wird gebraucht, sobald
  das Nachwaermen aus MEM-03 neben der Entlade-Aufgabe laeuft, also in 14-06
  oder 14-07. Heute kann kein Weg eine Engine laden, ohne im selben Lock-Block
  den Aktivitaetszaehler zu erhoehen. Als Auftrag an den naechsten Planer
  festgehalten, nicht als stillschweigende Auslassung.

- 14-04 (MEM-02, Indexseite): Der Poller bekommt ein oeffentliches Property
  `busy`, das `bool(self._held)` antwortet. Gehaltene Warteschlangenzeilen sind
  die einzige Groesse am Poller, die einen laufenden Durchgang bedeutet; sie
  werden auf allen Wegen geleert, auch im Abbruch und in `unlock_held`.
  `_idle_announced` ist dagegen ein Log-Merker, der in `arm()` zurueckgesetzt
  wird: ein Entlader, der ihn liest, entlaedt nach jedem Armieren einmal falsch
  (Leitplanke 3 der 14-CONTEXT.md). `armed` ist das Gegenteil der Frage,
  `cooldown` ist Warten und keine Arbeit. Alle drei stehen mit Begruendung im
  Docstring.

- 14-04: `release_cutter()` hat drei Antworten in dieser Reihenfolge: bei `busy`
  falsch und nichts angefasst (Pitfall 3, die Gewichte waeren Sekunden spaeter
  wieder da), bei leerem Paar falsch (es gab nichts loszulassen, der Zaehler des
  Aufrufers bleibt ehrlich), sonst beide Felder auf None und wahr. Die
  Arbeitsfrage steht vor der Bestandsfrage, weil ein falsches Ja fuer einen
  arbeitenden Container der Fehler ist, der nirgends rot wird.

- 14-04: Die Halbheit wird am Syntaxbaum ausgeschlossen, nicht an einem Lauf.
  `test_the_release_never_leaves_half_a_cutter_behind` liest `release_cutter`
  ueber `ast.walk` und verlangt, dass die Methode genau `_chunker` und `_model`
  zuweist. Damit ist zugleich das Gate gegen ein Zuruecksetzen von
  `_cutter_absent` und `_cutter_failed_at` gebaut (Pitfall 8), und es haelt auch
  gegen ein drittes Feld, an das heute niemand denkt.

- 14-04: `release_cutter` ruft keine Sammelrunde und keinen Trim, auch nicht im
  Kommentar: der Docstring umschreibt beide Begriffe, weil das
  Acceptance-Gate die Datei auf genau diese Zeichenketten absucht und sonst an
  der eigenen Erklaerung rot wuerde. Die Seitenrueckgabe liegt einmal je Takt in
  `embed/model.py` (14-05).

- 14-04: MEM-02 wird NICHT abgehakt, obwohl die Frontmatter des Plans sie nennt.
  Die Anforderung verlangt beide Speicherhalter und die Messgroesse "Rueckkehr
  zur Grundlast"; dieser Plan baut eine Haelfte und ruft sie nirgends auf. Das
  ist dieselbe Lage wie bei MEM-04 in 14-01, wo der Haken zurueckgenommen werden
  musste. MEM-02 faellt fruehestens mit 14-07.

- 14-04 (Lehre, zweite Auflage): Die Lehre aus 14-03 hat sich sofort wiederholt.
  Der Plan nannte `tests/test_measurement_scripts.py` erneut nicht und verbot
  ihre Aenderung sogar ausdruecklich (Verifikationspunkt 5). Der Baumhash wurde
  in beiden Produktcode-Commits nachgezogen. Die Plaene 14-05 bis 14-11 sollten
  die Datei in ihrer Dateiliste fuehren, statt sie zur Abweichung zu machen.

- 14-03 (MEM-01, Namensentscheid): Die Variable heisst
  **`FINDLING_EMBED_IDLE_RELEASE_SECONDS`** und nicht
  `FINDLING_EMBED_IDLE_SECONDS`. Begruendung aus dem eigenen Bestand: die 15
  bereits ausgelieferten Variablen der info.xml nennen alle Wirkung und nicht
  nur Bedingung, und eine einmal ausgelieferte Variable ist nicht mehr
  umbenennbar. Der Name steht in `config.py` und `appinfo/info.xml` byteweise
  gleich. Der Bereich heisst `EMBED_IDLE_RELEASE_SECONDS_RANGE` nach der
  Hausform der Datei; der Plantext nannte `EMBED_IDLE_RELEASE_RANGE` und
  widersprach damit seinem eigenen Acceptance-Kriterium.

- 14-03: Die Null bekommt einen eigenen Leser
  `_seconds_or_off_from_environment`, den dritten dieser Bauart nach
  `_hour_from_environment` und `_overlap_from_environment`.
  `_bounded_int_from_environment` waere aus beiden Richtungen falsch: mit
  `(0, 86400)` waere eine TTL von drei Sekunden gueltig, mit `(60, 86400)`
  fiele die Null auf den Default zurueck und ein Admin, der abschalten will,
  bekaeme die Funktion, ohne Fehlermeldung. Die Null wird deshalb VOR der
  Bereichspruefung beantwortet, und der Bereich behaelt seine Untergrenze 60.

- 14-03: Der Unterschied zwischen "aus" und "Tippfehler" ist durch eine
  Mutationsprobe abgenommen und nicht nur durch einen Docstring behauptet: der
  Aufruf wurde probeweise gegen `_bounded_int_from_environment` getauscht, genau
  ein Fall wurde rot, und es war der Null-Fall. Danach zurueckgenommen, alle 14
  Faelle wieder gruen.

- 14-03: Ab Werk 0, also aus, und der Kommentar nennt beide Gruende mitsamt
  ihrem Ablaufdatum: die eine bezahlte Box-Anfahrt der Phase 15 muss das Merkmal
  gegen seine eigene Abwesenheit wiegen und braucht beide Stellungen, und ein
  Merkmal mit ungemessenen Wiederaufwaerm-Kosten darf sich unter einer laufenden
  Installation nicht selbst einschalten. 900 s ist der Vorschlagswert der
  info.xml und bis zur Messung geraten.

- 14-03: `FINDLING_EMBED_ENABLED` wurde NICHT in die info.xml aufgenommen. Es ist
  ein Haertungskandidat und kein Requirement dieser Phase, und eine ausgelieferte
  Variable mehr in einem Release, das sie nicht braucht, ist Umfang ohne Anlass.
  Der Befund steht als Kommentar in der Datei, damit Phase 16 ihn findet.

- 14-03 (Lehre): Jede Aenderung an `backend/src/findling/` zieht
  `PACKAGE_TREE_HASH_TODAY` in `tests/test_measurement_scripts.py` nach. Der
  Plan kannte die Datei nicht; sie gehoert ab jetzt in die Dateiliste jedes
  Plans, der das Python-Paket anfasst. Die historische Zahl `PACKAGE_TREE_HASH`
  aus den Rohdaten bleibt dabei unberuehrt.

- 14-02 (OWNER-ENTSCHEID 19.09.2026): Der Owner hat den Ausgang des
  Vorprueflaufs im Wortlaut mit "freigegeben" genannt, ohne Auflage. Damit sind
  14-03 bis 14-12 frei und der Bau der Entladefunktion darf beginnen. Der Satz
  "gemessen, Ergebnis negativ" ist nicht eingetreten.

- 14-02: Der Vorprueflauf ist gefahren und das Tor der Phase ist offen.
  Gemessen wurde am
  19.09.2026 im Lauf 35443822228 auf `ubuntu-24.04-arm` (role target, aarch64,
  Neoverse-N2, vier Kerne) gegen das ausgelieferte Abbild
  `sha256:31c905b212d815d9ba5deea29a44b90bd8564baa3c4a5bd48ea13876ef31e538`.
  Ergebnis: Median der Rueckgabe **100,0 Prozent** (schlechtester Einzelzyklus
  98,4), `trim_rc` in fuenf von fuenf Zyklen 1, `after_gc` mindestens 856,9 MB
  ueber `after_trim`, Zyklus 5 gegen Zyklus 1 minus 1,5 Punkte. E1, E2, E3 und
  E4 sind alle gehalten; der Ausgang des Ablaufdokuments heisst "Gehalten".

- 14-02: MEM-04 ist erfuellt und abgehakt. Anders als in 14-01, wo der Haken
  zurueckgenommen wurde, liegt die Zahl jetzt vor: auf Zielarchitektur, nativ,
  gegen das ausgelieferte Abbild, mit der Maschine daneben.

- 14-02: Ein Bodensatz bleibt und gehoert in den Store-Text. Die Entladung
  fuehrt auf die Grundlast plus rund 16 MB (Zielast 17,1 MB ueber fuenf Zyklen,
  davon 15,9 MB im ersten), weil die Modulimporte von onnxruntime und numpy
  geladen bleiben. Eine Zusage "gibt den Modellspeicher vollstaendig zurueck"
  waere falsch.

- 14-02: Der Vergleichsast x86_64 liefert dieselbe Quote (Median 100,0, gleicher
  Zyklus-1-gegen-5-Abstand). Uebertragbar ist die Rueckgabequote, die Zeit nicht:
  dieser Lauf hat keine Zeit gemessen, und beide Runner sind Vier-Kern-Maschinen
  derselben Flotte und keine m7g.large.

- 14-01: Die Schwelle des Vorprueflaufs steht VOR dem Lauf: E1 verlangt einen
  Median der Rueckgabe von mindestens 60 Prozent auf dem `role: target`-Ast,
  hergeleitet aus 97,2 Prozent nativ x86_64 und 71,4 Prozent unter qemu. Dazu
  E2 (`trim_rc` in vier von fuenf Zyklen 1), E3 (`after_gc` deutlich ueber
  `after_trim`) und E4 (Zyklus 5 hoechstens 10 Punkte unter Zyklus 1). Drei
  Ausgaenge sind benannt, darunter "gemessen, Ergebnis negativ".

- 14-01: Der Vorprueflauf ist ein eingehaengtes Messskript und KEIN vierter
  Modus von `findling.embed.bench`. Ein neuer Bench-Modus stuende erst nach
  einem Push auf main und einem gruenen docker.yml im ausgelieferten Abbild;
  der Vorprueflauf muss aber gegen das ausgelieferte Abbild laufen, bevor
  Produktcode entsteht. Der neue Workflow-Schritt heisst E, weil D die
  Grundlast ist und unter diesem Buchstaben bereits zitiert wird.

- 14-01 (Lehre, Regel 1): Der Zustandsbefehl hat MEM-04 abgehakt, weil die
  Frontmatter des Plans die Anforderung nennt. MEM-04 verlangt aber den Beleg
  auf Zielhardware, und dieser Plan erhebt keine Zahl. Der Haken ist
  zurueckgenommen; MEM-04 faellt in 14-02. Eine Anforderung gehoert an den
  Plan, der sie belegt, nicht an den, der ihr Werkzeug baut.

- 13-12 (gehoert in den Checkpoint 13-13): Das dritte Paritaetsszenario ist in
  der geplanten Form nicht ausdrueckbar. `ask()` fragt die beiden OCS-Provider,
  und keiner von beiden kennt `types` oder `sort`; nur `ask_page` traegt die
  Parameter. Unter einem wegnehmenden Filter meldet `compare_page` daher zu
  Recht `page-missing`. Statt dem Vergleichswerkzeug eine Ausnahme beizubringen
  (das haette seine Schaerfe gekostet) wird die Wegnahme daneben gemessen. Teils
  staerker als geplant, weil sie belegt statt erwartet wird; teils schwaecher,
  weil die extra-Richtung unter dem Filter ueber leeren Mengen steht. Wer das
  schaerfer will, braucht ein Fixture mit einer Bilddatei.

- 13-11: Die franzoesischen Wortlaute der 23 neuen Schluessel sind NICHT
  muttersprachlich geprueft. docs/l10n-french.md war am 11.09. vom Owner
  abgenommen; ein datierter Nachtrag im Abschnitt Abnahme sagt jetzt ausdruecklich,
  dass die neuen Zeilen ungeprueft sind, damit eine abgenommene Datei keine
  ungelesenen Zeilen stillschweigend mittraegt. OFFEN fuer den Owner.

- 13-11 (Lehre): Der erste Einfuegelauf schrieb die Katalogeintraege ohne
  Trennkommas. Klammerbilanz und Diff-Durchsicht haetten das nicht gefunden, der
  JSON-Parser meldete es sofort. Die Parser-Pruefung bleibt Pflichtschritt.

- 13-10 (Planfehler, nicht Umsetzungsfehler): Der verify-Block wollte `grep -c '@media'
  == 2`, die Datei traegt aber seit Phase 9 vier Media Queries; der Plan hatte die zwei
  aus seinem eigenen interfaces-Abschnitt gezaehlt. Die pruefbare Absicht "keine neue
  Media Query" ist eingehalten, die Zahl steht vor und nach dem Plan bei 4.

- 13-10: Das Gate gegen ein Zaehl-Orakel sucht die Woerter des Zaehlens (`count`,
  `total`, `badge`, `disabled`, `$l->n(`) statt einer Ziffernausgabe, weil "Last 7 days"
  und "Last 30 days" selbst Ziffern tragen und ein Ziffern-Gate am ersten Tag rot
  gewesen waere.

- 13-10: Die Region der Leiste wird am Kommentar-Oeffner geschnitten und Blockkommentare
  werden vor dem Scan entfernt, sonst waere das Gate an genau dem Kommentar rot
  geworden, der erklaert, warum es keinen Zaehler gibt. Dieselbe Falle wie bei
  `aria-current` in 13-09.

- 13-09 (Scope-Erweiterung, Rule 3): Das Formular braucht `since` und `until` als
  versteckte Felder, 13-08 uebergibt dem Template aber keine Zeitgrenze und keine
  rohen Adresswerte, nur fertige Chips, Links und Flags. Neu ist deshalb
  `PageController::formFilters()`, die `filterArguments()` nimmt und `query` plus
  `names` entfernt; sie erbt damit drei Eigenschaften, statt sie einzeln zuzusichern.
  Die Alternative, aus den aktiven Chips zurueckzurechnen, waere genau die zweite
  Auslegung des Adresszustands gewesen, die diese Phase verbietet.

- 13-09: Der Kommentar zur Begruendung von `aria-current` nennt die verbotene
  Alternativauszeichnung nicht beim Namen, weil der Pruefblock und das kommende Gate
  aus 13-10 die Datei genau auf diese Zeichenkette absuchen; ein woertlicher
  Kommentar haette das eigene Gate rot gemacht.

- 13-08: Der Fingerabdruck des Cursorpfads laeuft ueber die ROHEN Adresswerte `range`
  und `since`, nicht ueber die daraus errechnete wirksame Untergrenze. Mit der
  wirksamen Grenze wechselte er um Mitternacht und wuerfe jeden Blaetternden ohne
  sichtbaren Grund auf Seite 1.

- 13-08: Die acht Cursorfaelle der Tests binden ihre Adresse ueber einen Helfer
  `bound()` an den von der Seite selbst berechneten Fingerabdruck. Der Plan wollte
  sie unveraendert gruen, was mit der Bindung unvereinbar war: `filterUrl()` schreibt
  nie ein `fp`, ein toleriertes Fehlen haette die Bindung genau im Zielfall
  wirkungslos gemacht.

- 13-06/13-07 (Merge): Beide Plaene zogen auf ihrem eigenen Branch den Baumhash der
  PHP-Haelfte nach, jeder gegen einen Baum mit nur seiner eigenen Aenderung. Der Hash
  laeuft ueber die ganze Haelfte, also ist der gemergte Baum ein dritter Baum mit einem
  dritten Hash; er wurde nach dem Merge mit demselben Rezept neu gelesen
  (6166e963..., weiterhin 64 Dateien). Beide Begruendungsabsaetze bleiben stehen.

- 13-06: `getSupportedFilters()` meldet vier Namen. Ein nicht deklarierter exklusiver
  Filter kostet die ganze Ergebnisgruppe, entweder weil die Oberflaeche den Provider
  gar nicht erst fragt oder weil seine Gruppe in einem 400 endet; fuer den Nutzer sah
  beides gleich aus, Findling war weg, sobald ein Datum gesetzt war (FILT-03).

- 13-07: Die vier Schnellbereiche sind Kalenderfenster in der Zeitzone des Nutzers,
  nicht in der des Servers. Die Tagesarithmetik laeuft ueber `DateInterval`, und die
  zwei Faelle zur engeren Grenze meiden das Paar "dieses Jahr"/"gestern", das am

  1. Januar rot waere.

- 13-05: `SearchService::run` nimmt die Filter als sechsten Parameter, hinter
  `SearchCaps` und ohne Vorgabewert, und reicht dasselbe Objekt an beide
  Containeraufrufe weiter. Der Filter wird auf der PHP-Seite kein zweites Mal
  angewendet: das würde aus jeder Seite eine Stichprobe machen und eine zweite
  Stelle an der Rechtegrenze eröffnen (T-13-23).

- 13-05: Das Änderungsdatum eines Treffers kommt aus `$node->getMTime()` am
  bereits bestätigten Knoten, gelesen hinter der Typprüfung und hinter der
  Leseprüfung. Der Kandidat des Containers trägt zwar ein eigenes `mtime`,
  `filterCandidates()` verwirft es weiterhin, und ein Testfall mit zwei
  absichtlich verschiedenen Zahlen belegt, welcher Wert gewinnt (T-13-22).

- 13-05: `ApprovedHit` trägt fünf Felder; für den Kanarienvogel (`fileId` 0)
  bleibt `mtime` bei 0, weil es dort keinen Knoten gibt. Das Feld ist ein
  Pflichtargument geblieben, damit ein vergessener Aufrufer nicht wie einer
  ohne Datum aussieht.

- 13-05: Die Rechtegrenze ist in Zahl, Reihenfolge und Ort unverändert;
  `test_php_acl_boundary.py` und `test_php_trust_boundary.py` sind grün.

- 13-04: Filter und Sortierung reisen durch die PHP-Haelfte als EIN benanntes
  Wertobjekt `SearchFilters` (`types`, `sort`, `since`, `until`), nach der
  Bauform von `SearchCaps`. Abweichung von jenem Vorbild: es gibt eine statische
  `none()`, weil "nichts eingegrenzt" ein benannter Zustand des Produkts ist und
  keine Zahl, ueber die niemand mehr nachdenkt. Die Begruendung steht im
  Klassen-Docstring.

- 13-04: Das neue Argument steht VOR den beiden Uhrwerten und nicht am Ende der
  Parameterliste, wie der Plantext es vorsah. Beide Uhrwerte tragen einen
  Vorgabewert, und ein Pflichtargument hinter einem optionalen ist seit PHP 8.0
  abgekuendigt. Ohne Vorgabewert bleibt es trotzdem: ein vergessener Aufrufer
  soll nicht aussehen wie einer ohne Filter.

- 13-04: `typeGroupsWithin` laeuft ueber die geschlossene Sechser-Menge und
  nicht ueber die Eingabe. Unbekannter Name, Dublette, Ueberlaenge und
  Reihenfolge sind damit baulich erledigt (T-13-17, T-13-18) statt in vier
  Pruefungen, die einzeln vergessen werden koennen.

- 13-04: Ein Wert in seiner Vorgabe wird nicht in den Rumpf geschrieben. Eine
  ungefilterte Suche schickt damit byteweise die Anfrage von vor dieser Phase,
  und ein echter Wert geht nicht zwischen vier Konstanten unter.

- 13-04: Der `/snippets`-Rumpf traegt `types`, `since` und `until` und an keiner
  Stelle den Sortiermodus (FILT-02). Die Reihenfolge dieser Treffer steht fest,
  bevor der Aufruf gestellt wird.

- 13-04: `filterCandidates()` bleibt unangetastet und laesst weiterhin nur
  `fileId` durch; der Docstring sagt jetzt ausdruecklich, dass das
  Aenderungsdatum aus dem bestaetigten Knoten kommt (13-05) und nie aus der
  Container-Antwort (T-13-20).

- 13-04: `php -l` ist auf dieser Maschine doch moeglich, ueber das offizielle
  Docker-Image `php:8.2-cli` (dieselbe Version wie der Lint-Job in CI). PHPUnit
  bleibt CI-only, weil die Suite eine Auscheckung von nextcloud/server braucht.

- 13-03: Die vier neuen Werte reisen als geschlossene Mengen. `types` ist
  `list[Literal[...]]` ueber die sechs Gruppennamen, `sort` ein `Literal` ueber
  die drei Sortiernamen, `since` und `until` sind `int` mit `ge=0` und
  `le=SEARCH_MTIME_MAX`. Kein Freitext: die Routen tragen `access_level USER`,
  und ein freier String waere ein zweiter Weg in den Abfragebau.

- 13-03: `SEARCH_TYPE_GROUPS_MAX = 6` und `SEARCH_MTIME_MAX = 4_102_444_800`
  (01.01.2100) stehen in `config.py`, je mit Begruendungsabsatz nach dem Muster
  von `SEARCH_OFFSET_MAX`.

- 13-03: Der Sortierterm haengt an derselben `lexical_only`-Zeile und nicht an
  einer zweiten Weiche: `... or sort != "relevance"`. Unter Sortierung gibt es
  keine Fusion, in die eine Vektorliste eingehen koennte.

- 13-03: `sort` steht NICHT in `SnippetsRequest`, und ein `sort` im
  Ausschnitts-Rumpf ist ein 422. Die Ausnahme ist im Gate
  `backend/tests/test_search_fields_lockstep.py` benannt, nicht gezaehlt.

- 13-03: `FIELDS_THAT_MAY_DIFFER` traegt vier Eintraege statt des einen aus dem
  Plantext, weil `limit`, `offset` und `fileIds` schon vor der Phase einseitig
  waren. Jeder Eintrag traegt seine Begruendung; eine Liste und keine Schwelle.

- 13-03: Der Ausschnittsaufruf SCHNEIDET NICHT. `snippets_for` laeuft ueber die
  bestaetigten Kennungen und waehlt keine Dokumente aus; die Filterklausel nennt
  `ext` und `mtime` und markiert im Textfeld nichts. Die drei Felder stehen am
  Modell, damit ein Rumpf beide Modelle passiert (`extra="forbid"` -> 422 -> auf
  der PHP-Seite `null` -> Fehlerblock statt Ausschnitten).

- 13-03: Die Diagnoseroute bekommt die drei Filter als Query-Parameter, aber
  keine Trefferzahl je Typ und keinen Gesamtwert. Ihre Grenze steht im
  Docstring: `ranked_sides` geht nicht durch `_mtimes_of`, sie sieht den Schnitt
  der semantischen Haelfte also nicht.

- 13-03: Der Container lehnt einen unbekannten Gruppen- oder Sortiernamen mit
  422 ab, weil ihn nur die eigene Oberflaeche ruft. Der stille Rueckfall bei
  einer von Hand editierten Adresse ist Aufgabe der PHP-Seite.

- 13-02: Die Sortierung ist ein eigener, rein lexikalischer Zweig
  (`_sorted_round` in `index/search.py`) ohne RRF und ohne Vektorhaelfte, und
  jeder Treffer traegt `score = 0.0`. Unter `order_by_field` liefert tantivy im
  ersten Tupelglied den Feldwert statt des Scores; ein uebernommener Feldwert
  waere ein Zeitstempel als Relevanz.

- 13-02: Der Zweitschluessel `file_id` ist Handarbeit und wird portionsweise
  hergestellt. Gemessen und in diesem Plan nachgestellt: bei gleichem
  Zeitstempel und Einfuegereihenfolge 7, 3, 9, 1 antwortet tantivy 7, 3, 9, 1.
  Eine Gleichstandsgruppe, die an einer Portionsgrenze zerfaellt, ist
  portionsweise sortiert; Duplikate oder Luecken entstehen dabei nicht.

- 13-02: Ein unbekannter Wert in `sort` faellt still auf `relevance` zurueck
  (`SORT_MODES.get`). Die Route prueft bereits am Wire-Modell; eine zweite
  Ausnahme wuerde aus einem Tippfehler in einer Adresse einen HTTP 500 machen.

- 13-02: Dieselbe Filterklausel wirkt jetzt an beiden Stellen. `_mtimes_of`
  nimmt sie als `Occur.Must` ueber die `file_id`-Klauseln; was dort
  herausfaellt, fehlt in `known` und verschwindet aus `merged`. Ohne diese
  zweite Stelle stehen unter dem Chip "PDF" docx-Treffer der semantischen
  Haelfte.

- 13-02: `VECTOR_SCAN_MAX` wird nicht angehoben. Die semantische Haelfte
  schrumpft unter einem engen Filter sichtbar, weil die Chunks VOR dem
  Typschnitt gezogen werden; das ist eine Eigenschaft und kein Defekt.

- 13-02: `semantic` ist im Sortierzweig wirkungslos statt verboten. Die
  Abschaltung durch den Aufrufer folgt in 13-03; die Wirkungslosigkeit hier ist
  die zweite, defensive Haelfte derselben Zusage.

- 13-01: `TYPE_GROUPS` in `query/rewrite.py` ist die einzige Abbildung von
  Gruppe auf Endung im ganzen Projekt, und die bestehende `type:`-Textsyntax
  wurde an dieselbe Tabelle angeschlossen: `type:images` bedeutet ab jetzt
  dasselbe wie der Chip. Ein Wort, das die Tabelle nicht kennt, bleibt wie
  bisher eine rohe Endung.

- 13-01: Textendungen und Gruppenendungen werden vereinigt und nicht
  geschnitten. `type:pdf` plus Chip "Bilder" wäre als Schnittmenge garantiert
  leer, und die Seite könnte das niemandem erklären.

- 13-01: Der strukturierte Gruppenparameter setzt die Operator-Marke
  `FILETYPE` nie; sie hängt ausschließlich am Text `type:`. Genau daran hängt
  FILT-01, und ein eigener Testfall hält es fest.

- 13-01: Die Bereichsabfrage auf `mtime` läuft über die Fast-Spalte,
  `use_inverted_index` bleibt beim Vorgabewert `False`. Mit `True` antwortet
  tantivy 0.26.0 mit einer leeren Trefferliste statt mit einem Fehler, was auf
  der Seite wie "in diesem Zeitraum gibt es nichts" aussieht.

- 13-01: Die Filterklausel liegt zusätzlich als `RewrittenQuery.filter_query`
  bereit, damit Plan 13-02 dieselbe Klausel auf die semantische Hälfte legen
  kann (`index/search.py::_mtimes_of`); ein Filter nur in `query` ließe
  typfremde Vektortreffer durch.

- 12-02: Zweig a greift: v35.0.0 vom 15.09.2026 ist die erste 35er-Marke ohne
  Prerelease-Kennzeichen (prerelease=false UND draft=false, am 16.09. live
  gelesen). Nach D-02 trug der Release-Status allein nicht; der Beweislauf
  35095805558 lief am 16.09. auf dem Baum des Stichtags mit allen vier
  Matrixaesten gruen, ERST DANACH fiel `tolerate-failure` (Owner-Freigabe am
  Checkpoint, Variante 1). Der stable35-Ast von deploy-harp ist ab jetzt
  muss-gruen; ein roter Lauf ist ein Befund und kein Grund, das Flag
  zurueckzudrehen. Beide info.xml blieben unberuehrt (Fenster steht auf
  33 bis 35, D-01).

- 12-08: Das Runbook ist vollstaendig. Abschnitt 6 macht fuenf
  Vergleichbarkeitsgroessen protokollpflichtig (Zeilenstaende 52.111/37/0,
  Cron-Intervall 300 s, m7g.large mit `2147483648`, Zeit seit dem letzten
  Containerstart, Werkzeugstand als Baumhash), Abschnitt 7 gibt jedem der neun
  Messschritte seinen Abbruchpfad und fuehrt alle zwoelf Rueckgabewerte,
  Abschnitt 8 baut in neun Schritten ab (Endmessungen und Historie VOR jedem
  zerstoerenden Schritt, `FINDLING_STATE_BACKUP` vor `destroy`, Tag-Sweep ueber
  `findling-phase5` UND `findling-corpus-keep` danach), Abschnitt 9 fuehrt die
  Kosten ueber `box.env` und schliesst den Kreis zum Deckel-Rechenblatt (D-05).

- 12-08: Waehrend der bezahlten Anfahrt wird kein Werkzeug mehr geaendert. Ein
  Skript, das waehrend seines eigenen Laufs nachgebessert wird, macht jede Zahl
  daneben unbelegt; der Werkzeugstand steht als Baumhash unter den
  protokollpflichtigen Groessen.

- 12-08: MESS-04 und MESS-06 sind erfuellt und abgehakt. Beide sind als
  Werkzeug- und Runbook-Anforderungen formuliert und liegen damit vollstaendig
  in Phase 12; die Anwendung im gefahrenen Messlauf zaehlt in Phase 15 unter
  MESS-05. HART-03 bleibt offen bis zum Vollzug durch 12-02 am 16.09.

- 12-03: `aws_box.sh restore` nimmt die Snapshotkennung aus dem Argument, sonst
  aus `CORPUS_SNAPSHOT_ID` in `box.env`, sonst aus der gepinnten Konstante
  `CORPUS_SNAPSHOT_DEFAULT`. Gesucht wird sie nie.

- 12-03: Ein aus dem Snapshot erzeugtes Volume wird pflichtmaessig auf
  `purpose=findling-phase5` umgetaggt, mit `describe-tags`-Rueckleseprobe und
  Abbruch, solange der geerbte Keep-Tag noch haengt.

- 12-03: `restore` endet beim Anhaengen; das Mounten bleibt ein Runbook-Block.
- 12-03: Annahme A3 ist lesend bestaetigt (Snapshot completed, 100 Prozent,
  60 GB, Tag `purpose=findling-corpus-keep`), Beleg in
  `docs/measurements/2026-09-v12-messung/rohdaten/01-aws-lesende-proben.txt`.

- 12-04: Die Fremdbestandszahl entsteht als
  `searcher.search(query, 1, count=True).count` im Prozess des Containers. Keine
  Route, keine Zahl ueber eine Prozessgrenze, kein Produktionscode angefasst; das
  Zaehl-Orakel aus T-02-93 entsteht gar nicht erst.

- 12-04: Nichtmessbarkeit wird am Rang der eigenen Datei entschieden (in BEIDEN
  Ranglisten fehlend oder schlechter als 64). Bestand und Fensterbelegung stehen
  erklaerend daneben und sind nicht das Urteil.

- 12-04: `NARROW_SCOPE_DIRS` traegt drei Laufverzeichnisse, `98b-sprachfaelle.sh`
  bekommt einen eigenen sha256-Waechter, und `docs/measurements/**` steht in
  beiden Pfadlisten von `python.yml`.

- 12-05: Das Urteil der Sprachfaelle haengt am kleineren der beiden Raenge der
  eigenen Datei gegen die Schwelle 64. Ein Wort statt einer Zahl (`ausserhalb`,
  `keine-kennung`) gilt als ausserhalb und wird nie gegen die Schwelle
  gerechnet.

- 12-05: Die eigenen Datei-Kennungen kommen aus dem Antwortkopf `OC-FileId` des
  Uploads (ohne zweite Abfrage) und reisen ausschliesslich in der Umgebung
  (`DATEI_IDS`), nie in einem Argument.

- 12-07: Der Deckel-Vorschlag fuer Phase 15 wird neu gerechnet statt uebernommen:
  acht Zeitposten, Volllauf mit dem gemessenen Planwert 26 h 37 min und ohne
  Vorwegnahme einer Top-up-Verbesserung, plus 15 Prozent Zuschlag. Ergebnis
  **42 h und 4,90 USD netto**, ausgewiesene Untergrenze 31 h und 3,59 USD. Die
  Freigabe faellt am Phase-15-Checkpoint, nicht im Runbook.

- 12-07: Das Runbook nennt Pfade und Variablennamen, nie Werte. Die
  Snapshotkennung bleibt im Klartext (steht bereits committet, ohne Konto
  nutzlos); Adressen, Instanz- und Volumekennungen stehen als Platzhalter mit
  einem Satz, woher der Wert kommt. Die CIDR-Schreibweise fuer das ganze
  Internet ist deshalb `<ganzes-netz>`.

- 12-07: Abschnittsueberschriften des Runbooks stehen bewusst ohne Umlaute, weil
  Pruefungen und Verweise auf sie zeigen; der Fliesstext traegt echte Umlaute,
  und der Kopf der Datei sagt das. Das Wort "Archiv" kommt in der Datei nicht
  vor (Vokabular-Gate, `docs/` ist oeffentlich).

- 12-06: Das Cron-Intervall ist ab jetzt eine im Skript durchgesetzte
  Messbedingung. `97-cron-vorpruefung.sh` hat zwei Zweige: `vorher` liest den
  Takt aus drei Quellen der Reihe nach und schreibt die Pflichtzeile
  `cron-intervall-ist` (Abbruch 25, wenn keine Quelle antwortet, 26 bei mehr als
  zehn Prozent Abweichung vom Soll 300 s), `waehrend` misst den tatsaechlichen
  Scheibenabstand (Abbruch 27 ohne Zahl, 28 ueber dem Deckel 420 s). Ein reiner
  Konfigurationscheck haette am 10.09.2026 gruen gemeldet, waehrend der Befund
  vorlag (D-07, D-08).

- 12-06: Die Ablesereihe des Wirkungszweiges laeuft mit 120 s und nennt ihr
  Intervall als Pflichtzeile. In v1.1 haben zwei Reihen (194 von 812 gegen 62
  von 325 Lesungen) rund 24 gegen 19 Prozent fuer denselben Sachverhalt
  ergeben; die Zuordnung der Reihen zu den beiden Beobachtern ist Annahme A1 und
  ausdruecklich nicht gesichert.

- 12-06: Der Exit-Code-Katalog des v1.2-Laufverzeichnisses steht bei 28; 12-08
  und Phase 15 setzen bei 29 fort. Der Ablaufplan `00-ablauf.md` schreibt die
  Erwartung E1 bis E7 vor der Anfahrt auf und wird danach nicht mehr angepasst.

- 12-05: `rang-erhoben ja` steht erst nach einem erfolgreichen zweiten
  Sondenlauf. Beide Ursachen (keine Kennung, keine Sonde) enden mit Exit 24
  unter der `tee`-Pipeline. Der Exit-Code-Katalog steht damit bei 24; 12-06
  setzt bei 25 fort.

## Milestone-Reihenfolge v1.2

| Phase | Inhalt | Requirements |
|-------|--------|--------------|
| 12 | Messwerkzeug, Runbook und Terminentscheid (ohne Box) | MESS-04, MESS-06, HART-03 |
| 13 | Filter und Sortierung auf der Ergebnisseite (Backend vor PHP) | FILT-01..05 |
| 14 | Modell-Entladung im Leerlauf (Schalter ab Werk aus) | MEM-01..05 |
| 15 | Messphase, eine Box-Anfahrt | MESS-05 |
| 16 | Haertung und Store-Einreichung v1.2.0 | HART-01, HART-02, REL-02 |

Harte Abhaengigkeiten: 12 vor 15, Backend vor PHP innerhalb 13, 14 vor 15, 16 zuletzt.

## Termine und Owner-Checkpoints

- **16.09.2026**: stable35-Fenster-Entscheid (HART-03, Entscheid v2-a), verankert in Phase 12.
  Beide Zweige sind seit 14.09. fertig ausformuliert in
  `.planning/phases/12-messwerkzeug-runbook-und-terminentscheid/12-STABLE35-ENTSCHEID.md`
  (Plan 12-01); am Stichtag vollzieht Plan 12-02 nur noch nach der dortigen
  siebenschrittigen Checkliste. HART-03 ist erst nach diesem Vollzug erfuellt.

- **Vor der Box-Anfahrt**: neu gerechneter Zeit-/Kostendeckel vom Owner freigegeben (MESS-05, Phase 15); das Rechenblatt steht seit 19.09. (Plan 15-02) in `docs/runbook-messbox.md` Abschnitt 2 und kommt auf **46 h / 5,40 USD netto**, Vorgaengerstand 42 h / 4,90 USD (16.09.), Untergrenze 31 h / rund 3,59 USD. Der 26-h-Vorschlag reisst rechnerisch. Der Preisabgleich vom 19.09. (15-07) hat keine Abweichung der sechs gepinnten Saetze ergeben
- **OFFEN, Task 3 des Plans 15-16**: die **Abnahme der Phase 15** durch den
  Owner. Vorzulegen sind die fuenf Erfolgskriterien der ROADMAP je mit Artefakt
  und je mit einem Wort, die Kostenzeile (Deckel 46 h / 5,40 USD, verbraucht
  25,75 h / 2,9831 USD, Differenz 20,25 h / 2,42 USD darunter), die Befunde des
  Audits und die offenen Punkte aus dem Abschnitt "Was dieser Lauf nicht besser
  gemacht hat". Erfolgskriterium 4 wird als NICHT erfuellt vorgelegt. Auflagen
  des Owners werden als Auftraege an Phase 16 notiert, im Wortlaut und nicht als
  erledigt gefuehrt.
- **Vor dem Bau des Zustandsteils**: engineState-Wortwahl `cold` vs sechstes Wort `unloaded` (MEM-05, Phase 14)
- **Vor dem Bau der Entladung**: Vorprueflauf zur tatsaechlichen RSS-Rueckgabe auf Zielhardware (MEM-04, Phase 14) , ERLEDIGT 19.09.2026, Median 100,0 Prozent auf aarch64, Owner-Entscheid "freigegeben"

## Nach v1.2 (Wiedervorlage)

- Snapshot-Wiedervorlage snap-03f1d1d9ad9262704 (loeschen oder guenstigere
  Speicherklasse, 2,79 bis 2,99 USD je Monat). **Stand 21.09.2026, nach dem
  Entscheid aus 15-14: die Wiedervorlage bleibt OFFEN und wird nicht
  geschlossen.** Der Owner hat den Snapshot am 21.09. zum zweiten Mal bewusst
  behalten ("Abbauen, Korpus-Snapshot behalten", konsistent mit Frage B aus
  15-08), damit eine weitere Anfahrt ohne mehrstuendigen Neuaufbau startet;
  ~55,4 GB, Marke `purpose=findling-corpus-keep`. Er ist damit die einzige
  laufende Box-Kostenstelle. Faellig nach v1.2, benannt als Q5 der
  Phasenrecherche, im Bericht Abschnitt 10 Punkt 10 und im Runbook Abschnitt 8
  Schritt 9.
- Aufraeumbefunde aus der Recherche: fastembed gepinnt aber nicht importiert, numpy als indirekte Abhaengigkeit
- Systemplatten-Skripte Phasen 5-6.1: Repo-Aufnahme erst nach Geheimnis-Durchsicht

## Offene Blocker

- Kill-Kriterium aktiv: kuendigt Nextcloud auf der Conference im September eine
  Elasticsearch-freie Volltextsuche mit OCR an, wird das Projekt neu bewertet

## Deferred Items

Items acknowledged and deferred at milestone close on 2026-09-11:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| debug | kill-resume-di-05-36-red | investigating | 2026-09-11 |
| debug | parity-login-probe-404 | verifying | 2026-09-11 |
| debug | store-install-5-routes-probe | verifying | 2026-09-11 |

Einordnung: alle drei Debug-Sessions gehoeren zu CI-Befunden, deren Fixe laengst
gemerged und gruen sind (parity-login-probe-404: Fix d604880, Probe fragt
/index.php/apps/findling/; store-install-5-routes-probe: Step auf
oc_ex_apps_routes umgebaut; kill-resume-di-05-36-red: DI-05-36 lief in Phase 10/11
gruen durch). Nur der Session-Status wurde nie auf resolved gesetzt.

## Session Continuity

Last session: 2026-09-22T02:10:00.000Z
Stopped at: 16-10 abgeschlossen und damit **Welle 4 vollstaendig**. Zwei Commits (a9ee779, 01dffa1): Owner-Entscheid "Mitfahren" am Tor, sechs Sprachpakete mit Pin und sechs eigenen Bau-Pruefungen, Positivliste auf neun bei unveraendertem Standard deu+eng+fra, THIRD-PARTY-Tabelle samt der bis dahin fehlenden fra-Zeile, neues Gate `test_ocr_languages.py` mit gestagtem rotem Zustand, `PACKAGE_TREE_HASH_TODAY` im selben Commit wie `config.py`. Alle Python-Gates lokal gruen, volle Suite 2.472 bestanden / 15 uebersprungen, Skipzahl unveraendert. **Der Multi-Arch-Bau ist gefahren und gruen (docker.yml 35597353780).** An 16-11 uebergeben: elf Textstellen nennen noch drei Sprachen, die Liste steht in 16-10-SUMMARY.md. KEIN Tag, KEIN Release. Davor: 16-09 abgeschlossen (Welle 4, erster Plan). Vier Commits (12fec7d, 0f112c3, 607f8d0, 1c61216): Q-5 nachgesehen und als Kommentar im Workflow festgehalten, `UPGRADE_FROM_TAG` auf v1.1.0, die vier Stellen umgestellt, Zusicherung 6 auf `searchFilters.dates`, die Ratsche auf `GOLD_V1_0_AND_V1_1`. Zusicherungen 1 bis 5 maschinell als zeichengleich nachgewiesen. Alle Python-Gates lokal gruen, volle Suite 2.469 bestanden / 15 uebersprungen, Skipzahl unveraendert. **Der Auftrag `deploy-harp` ist NICHT gefahren** (kein Push im Auftrag); Erfolgskriterium 3 von REL-02 wartet auf die Laufnummer, der Pruefweg steht in 16-09-SUMMARY.md und der Punkt in `deferred-items.md`. KEIN Tag, KEIN Release. Davor: 16-07 abgeschlossen (Welle 3, erster Plan). Migration, ihr Test und der Nachzug von PHP_FILES_TODAY 66 plus Baumhash in einem Commit (12e8663, der Nachzug MUSS im selben Commit liegen), die drei Versionsstellen auf 1.2.0 in einem zweiten (734a1b2); alle Python-Gates lokal gruen, volle Suite 2.469 bestanden / 15 uebersprungen, Skipzahl unveraendert. Der PHP-Teil (php -l, PHPUnit) ist wieder nicht gelaufen, aus demselben Grund wie in 16-06. KEIN Tag, KEIN Release. Davor: 16-06 abgeschlossen und damit Welle 2 vollstaendig. Die Messung des inneren Aufrufs samt PHP-Faellen und Baumhash-Nachzug in einem Commit (f604805, der Nachzug MUSS im selben Commit liegen), das Python-Textgate in einem zweiten (e3fb6c5); alle Python-Gates lokal gruen, volle Suite 2.469 bestanden / 15 uebersprungen, Skipzahl unveraendert. Der PHP-Teil (php -l, PHPUnit) ist nicht gelaufen: kein PHP auf dieser Maschine und kein Push im Auftrag, `php.yml` startet mit dem Push von selbst. Davor: 16-05 abgeschlossen (Welle 2, erster Plan). Task 1 (Platzhalter fuer Kennungen und Adressen, fe3cf8c) und Task 2 (gesperrtes Wort aus den vier Anleitungen, f1c15a1) je einzeln committet; alle Gates lokal gruen, volle Suite 2.464 bestanden / 15 uebersprungen, Skipzahl unveraendert. Davor: 16-04 abgeschlossen und damit Welle 1 vollstaendig. Task 1 (Vorlaufsonde, DI-11-03, daa4661), Task 2 (Schluesselpaar im Abbau, L-07, 681097a) und Task 3 (sieben dokumentierte Entscheide, 4917463) je einzeln committet; alle Gates lokal gruen, volle Suite 2.463 bestanden / 15 uebersprungen, Skipzahl unveraendert.
Resume file: keine; NAECHSTES ist 16-11 (Welle 5, Textentwurf der sechs Store-Texte; die Antwort aus 16-10 lautet NEUN Sprachen)
