---
phase: 16-haertung-und-store-einreichung-v1-2-0
audited: 2026-09-21
tree: 86aa2ad2129f99cd646948763e09d097893fbf4d
commit: 67661e5a216b14103a3e169fc8705ab8f7fe1b63
findings:
  critical: 0
  high: 0
  medium: 2
  low: 3
  total: 5
status: issues_found
fixed: [M-16-01, M-16-02]
still_open: [L-16-01, L-16-02, L-16-03]
---

# Phase 16: Launch-Haertung und Security-, Bug- und Performance-Audit

**Umfang:** die dreizehn Plaene 16-01 bis 16-13 dieser Phase, gelesen gegen den
Baum von Commit `67661e5` und gegen den Arbeitsbaum, in dem die Fixe dieses
Berichts entstanden sind. Er liegt nach der Owner-Regel vom 15.08.2026 vor dem
Phasenabschluss und nach der Owner-Regel vom 06.09.2026 vor der Abgabe, und er
ist nach dem Muster von `docs/audits/2026-09-phase-15/README.md` geschrieben.

Die Überschriften stehen ohne Umlaute, weil Prüfungen und Verweise auf sie
zeigen; der Fließtext benutzt echte Umlaute. Dieser Bericht nennt Laufnummern,
Dateinamen und Zahlen und sonst nichts: keine Kennung, keine Adresse, keinen
Passwortinhalt.

**Diese Phase ist die erste, die zwei Berichte in einem schreibt.** Die
Owner-Regel vom 06.09.2026 verlangt vor einer Abgabe eine Haertung, die nicht
nur den glücklichen Pfad abgeht, und die Owner-Regel vom 15.08.2026 verlangt
nach jeder Phase ein Audit. Beides steht hier, und die Haertung steht vorn, weil
sie die Frage stellt, aus der die Befunde dieses Berichts gekommen sind.

**Bilanz vorweg: kein CRITICAL, kein HIGH.** Zwei MEDIUM, beide in diesem Plan
behoben, und drei LOW, alle drei mit Adresse. Der wichtigere der zwei MEDIUM ist
unangenehm und gehört deshalb in den ersten Absatz: **ein Fix dieser Phase hat
nicht getragen, und vier rote Läufe am selben Tag haben es gesagt, ohne dass ein
Plan sie gelesen hätte.** Der zweite ist ein Wert in einem öffentlichen
Dokument, den die Bereinigung der Phase nicht sehen konnte, weil das Gate dieser
Phase nur die Namensform eines einzigen Anbieters kannte.

---

## 1. Die Haertungsmatrix

Die Owner-Regel nennt acht Pfade. Jeder bekommt hier eine Zeile mit dem, womit
geprüft wurde, dem Beleg und dem Urteil. Ein Urteil ohne Beleg wäre ein Vorsatz,
und genau das soll die Matrix ersetzen.

| Nr. | Pfad | Womit geprueft | Beleg | Urteil |
|---|---|---|---|---|
| 1 | Fehler- und Randpfade | die vier stillen Fehlerpfade von `ExAppService::call`, der Degradationspfad ohne Gewichte, die leere Ergebnisgruppe, ohne Treffer gegen abgebrochen | 43 PHPUnit-Fälle in `ExAppServiceTest.php`, fünf Fälle in `test_exapp_call_instrumentation.py`, 50 Fälle in `test_search_endpoint.py`, 70 in `test_ops_scripts.py` | **gehalten**, mit einem Befund, der keinen Pfad des Erzeugnisses betrifft (M-16-01) |
| 2 | Rechtegrenzen | `git diff` über die Berechtigungskette seit dem Phasenbeginn, dazu die vier Gates, die sie halten | `git diff --stat 8aed3c0..HEAD` über `Provider.php`, `SearchService.php`, `ApprovedHit.php`, `PathResolverService.php`, `SearchCaps.php`, `SearchFilters.php`, `backend/src/findling/query` und `backend/src/findling/api`: **leere Ausgabe**; 17 + 8 + 21 + 27 + 18 Fälle | **unberuehrt und belegt** |
| 3 | Neustart, Upgrade, Migration | der Auftrag `deploy-harp` mit seinen sechs Zusicherungen, die Migration mit ihrem wiederholten Lauf, die sechs Abbau-Schritte | Lauf **35594647362** vom 21.09.2026 und erneut **35603906848** auf dem heutigen Baum, je `all six assurances hold`; sechs Fälle in `Version001200Date20260921000000Test.php`; 15 Fälle in `test_uninstall_contract.py` | **gehalten** |
| 4 | Kaputte und boesartige Dateien | die bestehenden Fälle der Suite, plus die Verdikt-Zählung der Integrationsstrecke | 51 Fälle in `test_extract_errors.py`, 21 in `test_extract_edge_paths.py`, 25 in `test_sandbox.py` (davon vier übersprungen, keine POSIX-Shell); Lauf 35586213137 zählt 39 Dateien mit Verdikt, `indexed=26 skipped=7 failed=6` | **gehalten**, die vier Auslassungen hängen an der Maschine |
| 5 | Ressourcengrenzen | die harte Speichergrenze, die Deckel des OCR-Pfades, die Zeitdecken, und der Stand von M-01 | `MIN_FREE_BYTES = 524_288_000`, `OCR_MAX_PAGES = 30`, `MAX_CELLS`, `REQUEST_TIMEOUT_SECONDS = 1.5`, `PAGE_REQUEST_TIMEOUT_SECONDS = 1.5`, `MIN_CALL_SECONDS = 0.3`, neu `SLOW_CALL_LOG_MILLISECONDS = 1000.0` | **unveraendert**, keine Grenze des Erzeugnisses ist bewegt worden; M-01 bleibt **teilerfuellt** (Abschnitt 6) |
| 6 | Fremdinstallation auf frischer Nextcloud | der Store-Install-Ast und der arm64-Ast | `Store install 0` bis `Store install 7` im Auftrag `deploy-harp`, zuletzt grün in 35603906848; `index-search-e2e (sqlite, ubuntu-24.04-arm)`, Lauf **35586213137**, `files on the instance before the corpus: 0` | **gehalten** |
| 7 | Store-Vorgaben | Längengrenzen, leere Elemente, Sprachcodes, Bildgrößen, keine Backticks und keine Tabellen, genau ein Connector-Satz, genau eine Messzahl | 67 Fälle in `test_store_metadata.py`, je Zusage ein Mutationsfall; `php.yml` Lauf **35603906800** grün, der die `info.xml` gegen das Schema schickt | **gehalten** |
| 8 | Alle Audits erneut | Security (Abschnitt 3 und 4), Bugs (Abschnitt 7), Performance (Abschnitt 5) | die drei Abschnitte unten | **gefahren**, zwei MEDIUM gefunden und behoben |

### Zu Zeile 1, im Einzelnen

Die vier stillen Fehlerpfade sind der unerreichbare Container, ein Statuscode ab
400, ein Rumpf über der Grenze und ein Rumpf, der sich nicht lesen lässt. Alle
vier tragen seit Plan 16-06 die gemessene Dauer des inneren Aufrufs, und der
vierte ist dabei erst aufgefallen: der Plan sprach von dreien. Ein Fehlerpfad
ohne Wartezeit wäre eine Lücke genau dort, wohin M-01 sieht.

Der Degradationspfad ohne Gewichte hat vier eigene Fälle: eine fehlende
Indexdatei antwortet leer und mit dem Vermerk, der Kanarienvogel antwortet auch
ohne Index, eine Versionsdrift antwortet weiter, und eine Runde unter der
Entladung antwortet so wie ein Container ohne Modell. Keiner dieser Pfade wirft.

Die Trennung von "ohne Treffer" und "abgebrochen" ist Plan 16-04 und die
Schließung von DI-11-03. Der Schlüssel `empty_result_groups` trägt `gesamt`,
`ohne-treffer` und `fehlschlag`, und fällt die Vorlaufsonde aus, dann fehlen die
zwei getrennten Zahlen **namentlich**, statt still durch die alte Zählung ersetzt
zu werden.

### Zu Zeile 2, weil sie die eine ist, die etwas beweisen muss statt behaupten

**Die Berechtigungskette ist in dieser Phase nicht angefasst worden**, und das
ist nicht die Aussage eines Plans, sondern die leere Ausgabe eines Diffs über
acht Orte seit dem letzten Commit der Phase 15.

Eine Datei der Kette ist berührt: `php/lib/Service/ExAppService.php`. Ihr Diff
über die ganze Phase umfasst 42 hinzugefügte und **eine** geänderte Zeile, und
die eine geänderte ist eine Protokollzeile, die ein Feld dazubekommt. Kein
Rückgabepfad, keine Bedingung, keine Decke und keine Prüfung des Aufrufers hat
sich bewegt.

---

## 2. Gate-Protokoll

Der Gesamtlauf ist in einem Zug gefahren, in der Reihenfolge, in der
`.github/workflows/python.yml` ihn fährt, am 21.09.2026 auf der
Entwicklungsmaschine (Windows, Python 3.13, uv), `pyright` mit
`PYRIGHT_PYTHON_FORCE_VERSION=latest`, damit lokal dieselbe Fassung prüft wie in
CI (Regel vom 19.09.2026).

| Stufe | Befehl | Ausgang | Zahl |
|---|---|---|---|
| 1 | `uv run ruff check .` | grün | All checks passed |
| 2 | `uv run ruff format --check .` | grün | 126 Dateien bereits formatiert |
| 3 | `uv run pyright` | grün | 0 errors, 0 warnings, 0 informations |
| 4 | `uv run vulture src tests --min-confidence 80` | grün | keine Ausgabe |
| 5 | `uv run pytest -q` (VOLLE Suite), vor den Fixen | grün | **2487 bestanden, 15 übersprungen**, 210,78 s |
| 5b | `uv run pytest -q` (VOLLE Suite), nach den Fixen | grün | **2491 bestanden, 15 übersprungen**, 225,77 s |
| 6a | `uv run ruff check --config pyproject.toml ../scripts` | grün | All checks passed |
| 6b | `uv run ruff format --config pyproject.toml --check ../scripts` | grün | 10 Dateien bereits formatiert |

Die volle Suite und nicht `tests/unit`: die Lehre vom 17.09.2026 ist, dass ein
prozessweites Leck nur im vollen Lauf rot war.

### Die Skipzahl gegen den Stand vor der Phase

| Stand | bestanden | uebersprungen |
|---|---:|---:|
| 14-12, Abnahme der Phase 14 (19.09.2026) | 2262 | 15 |
| 15-16, Abnahme der Phase 15 (21.09.2026), **Stand vor dieser Phase** | 2394 | 15 |
| 16-12, Stand vor diesem Plan | 2487 | 15 |
| **dieser Lauf (21.09.2026)** | **2491** | **15** |

**97 Fälle mehr als vor der Phase, und kein einziger übersprungener mehr.** Die
Skipzahl steht seit 13-13 unverändert bei 15, und alle 15 hängen an der Maschine
(kein Modellartefakt, kein `tesseract`, keine POSIX-Shell, kein Korpusgenerator)
und keiner an einer Zusage. **Eine gewachsene Skipzahl wäre ein Befund**; sie ist
nicht gewachsen. Ein Grün, das durch einen neuen Skip entstanden wäre, wäre
keines.

### Die Stufen, die hier nicht fahrbar sind

| Stufe | Lage | Ersatznachweis |
|---|---|---|
| PHP-Lint, PHPUnit | kein PHP und kein Composer auf dieser Maschine | `php.yml` Lauf **35603906800** grün auf dem heutigen Baum; im Baum gezählt: 232 PHPUnit-Fälle in 15 Dateien, davon 43 auf `ExAppService` und 6 auf die neue Migration |
| Die Werkbänke, die eine Instanz brauchen | keine Nextcloud auf dieser Maschine | sechs Werkbänke, gleichzeitig grün auf demselben Commit, siehe unten |

### Der CI-Stand des heutigen Baums

Alle sechs Werkbänke, die auf einen Push laufen, sind für Commit `67661e5`
**gleichzeitig grün**:

| Werkbank | Lauf | Ausgang |
|---|---|---|
| Python gates | 35603907050 | success |
| Resilience | 35603906880 | success |
| HaRP deploy | 35603906848 | success |
| PHP and store metadata gates | 35603906800 | success |
| Multi-arch image | 35603906783 | success |
| Integration | 35603906685 | success |

Die siebte der sieben Läufe, die das Flake-Register für den Tag verlangt, ist
die Release-Werkbank, und die läuft erst auf einem Tag. Das ist Plan 16-14.

### Ein Befund aus dem Gate-Protokoll selbst

Dieselbe Werkbank `python.yml` ist am 21.09.2026 **viermal rot** gewesen, und
zwar nach dem Fix, der genau diesen Fall beheben sollte. Das ist Befund
**M-16-01** und steht in Abschnitt 7.

---

## 3. Security, ASVS V2, V4, V6, V7, V12, V14

Die zutreffenden Kategorien stehen in `16-RESEARCH.md`, Abschnitt "Security
Domain". V3 und V5 treffen nicht zu und stehen hier trotzdem mit einer Zeile,
weil eine weggelassene Kategorie von einer geprüften nicht zu unterscheiden ist.

### V2, Anmeldedaten: gehalten

Die Phase legt keine neue Anmeldung an. Die eine Stelle, an der sie das Thema
berührt, ist Auflage A1: die Nachfolgefassung `99d-filter-sortierung.sh` liest
das Feld der Anmeldung jetzt auch aus der Datei und nicht nur aus der Umgebung,
und der Wert wandert dabei in **keine** Shellvariable, sondern unmittelbar in
eine Datei mit Modus 600. Das ist strenger als das Vorbild und hält auch unter
`set -x`. Das Gate `test_the_script_of_this_run_puts_no_password_on_a_command_line`
liest jedes Werkzeug des Laufverzeichnisses und ist grün, das neue eingeschlossen.

### V4, Zugriffskontrolle: gehalten, und zwar unberuehrt

Die Kategorie hat in dieser Phase zwei Hälften. Die erste ist die
Berechtigungskette des Erzeugnisses, und Zeile 2 der Haertungsmatrix belegt mit
einem leeren Diff, dass sie unangetastet ist. Die zweite wäre eine Box gewesen;
Auflage A4 ist über den kostenlosen CI-Weg erfüllt worden, also gab es in dieser
Phase **keine gemietete Maschine, keine Firewallregel und keinen Fernzugang**.
Was Phase 15 unter dieser Kategorie zu prüfen hatte, entfällt hier ersatzlos, und
das ist die günstigste Art, eine Kategorie zu halten.

### V6, Kryptographie: gehalten

Unverändert. Beide Signaturen entstehen in CI, die Schlüssel leben im
Geheimnisspeicher der Werkbank und kommen in keiner Datei dieses Baumes vor. Die
Gegenprobe in Abschnitt 4 hat mit zwei unabhängigen Familien nach
Schlüsselmaterial gesucht und **null** gefunden.

### V7, was oeffentlich wird: der Schwerpunkt, und hier liegt ein Befund

`docs/` ist öffentlich lesbar, und diese Phase hat die Regel dafür zum ersten Mal
zu einem Gate gemacht (16-02) und den Altbestand bereinigt (16-05). Beides hält.

**Und beides hat eine Lücke gelassen.** Das Gate führt seit dem 21.09.2026 neun
Geheimnisfamilien plus die Vokabularregel, und alle vier Familien, die eine
Ressource an ihrem Namen erkennen, kennen die Namensform **eines** Anbieters.
Dieses Projekt hat Boxen bei zwei Anbietern gemietet. Der Name, den der zweite
für den Einhängepunkt eines Datenträgers bildet, trägt dessen Kennung im Namen,
und er stand nach der Bereinigung weiter an drei Stellen in einem redigierbaren
Dokument. Das ist Befund **M-16-02**, und er ist in diesem Plan behoben: das
Dokument ist redigiert, das Gate hat eine zehnte Familie, und die drei Rohdateien
der gefahrenen Anfahrt, in denen der Name bleibt, stehen mit je einem eigenen
Grund auf der Ausnahmeliste.

Die zweite Hälfte dieser Kategorie ist neu in dieser Phase: **eine ausgelieferte
App schreibt seit Plan 16-06 eine Protokollzeile.** Sie steht auf `info`, nur
oberhalb von 1.000 ms, und trägt genau drei Felder: den Pfad, die gemessene Dauer
und die Decke, die für diesen Aufruf galt. Kein Suchbegriff, kein Dateiname,
keine Nutzerkennung, kein Rumpf. Zwei Seiten halten das fest: ein PHPUnit-Fall
liest die Zeile nach und ein Python-Textgate liest **vollständige Anweisungen**
der Quelle statt einzelner Zeilen, weil die Felder einer Warnung unter der Zeile
stehen, die den Logger nennt.

### V12, Ressourcengrenzen: nicht beruehrt

Keine Grenze des Erzeugnisses hat sich bewegt (Zeile 5 der Matrix). Die sechs
neuen Sprachpakete sind **verfügbar und nicht eingeschaltet**: der Standard bleibt
bei drei Sprachen, und ein eigener Fall hält diese Zahl fest. Eine Installation,
die nichts einstellt, zahlt für die sechs keine einzige Seite mehr.

### V14, Konfiguration: gehalten

Die eine neue Konstante der Phase ist eine Protokollschwelle und keine
Umgebungsvariable; sie ist nicht einstellbar und kann deshalb auch nicht falsch
eingestellt werden. Die neue Positivliste der OCR-Sprachen behandelt einen
unbekannten Wert wie bisher: Warnung mit dem **Namen** und nie dem Wert,
Rückfall auf den Standard, kein Wurf.

### V3, V5: treffen nicht zu

Keine Sitzung wird angelegt. Ein neuer Eingang ist nicht entstanden: die
Migration liest einen Konfigurationswert und schreibt keinen, und die Routen des
Containers sind unverändert.

---

## 4. Die Geheimnis-Gegenprobe, mit einem anderen Verfahren

**Eine Gegenprobe mit dem Muster der Umsetzung ist keine Gegenprobe.** Diese
Regel steht seit dem 02.08.2026 in den Owner-Regeln, und sie hat in dieser Phase
einen neuen Anlass: **das Gate aus Plan 16-02 ist jetzt selbst das Muster der
Umsetzung.** Es ist über `docs/` gelaufen, es ist über jeden Commit dieser Phase
gelaufen, und wenn ein Geheimnis in einer Form in den Baum geraten wäre, die
seine zehn Regeln nicht kennen, hätte es sie alle übersehen.

Die Gegenprobe unterscheidet sich deshalb in beidem, in der Reichweite und im
Verfahren:

* **Reichweite.** Nicht `docs/`, sondern **alle 72 Dateien, die diese Phase
  committet hat**, in jedem Verzeichnis. Das Gate reicht über ein Verzeichnis,
  die Gegenprobe über eine Änderungsmenge; zusammen decken sie beides ab. Danach
  ein zweiter Lauf über alle 405 Dateien unter `docs/`, nach der Lehre von M-02.
* **Verfahren.** Sechs Musterfamilien, die das Gate **nicht** führt, und dazu
  eine Messung, die überhaupt kein Muster ist: die Entropie zugewiesener Werte.

| Familie | Was gesucht wurde | Fuehrt das Gate sie? | Treffer in den 72 Dateien | Urteil |
|---|---|---|---:|---|
| `jwt-und-bearer` | ein Token in drei punktgetrennten Teilen, und eine Anmeldekopfzeile mit Wert | nein | 0 | sauber |
| `zugangsdaten-in-einer-adresse` | Schema, Benutzer, Doppelpunkt, Wert, Klammeraffe, Rechner | nein | 0 | sauber |
| `herstellermarken-fremder-dienste` | die Präfixe der Zugangsmarken von sechs fremden Diensten | nein | 0 | sauber |
| `anwendungspasswort-in-fuenf-gruppen` | fünf Gruppen zu fünf Zeichen, die Form, die Nextcloud selbst vergibt | nein | 0 | sauber |
| `hexgeheimnis-in-einer-zuweisung` | 32 und mehr Hexzeichen hinter einem Bezeichner, der kein Prüfsummenwort ist | nein, das Gate liest jeden reinen Hexlauf als Prüfsumme | 14 | Prüfsummen, Baumhashes und eine Modellfassung, siehe unten |
| `elektronische-postadresse` | jede Postadresse | nein | 22 | eine einzige Adresse, und die ist zur Veröffentlichung bestimmt (I-01) |
| `hohe-entropie-in-einer-zuweisung` | Shannon-Entropie ab 4,2 über zugewiesenen Werten ab Länge 20, **kein Muster** | nein, und es kann sie nicht führen | 15 | Pfade und ein Lizenzetikett |

**Das Ergebnis: kein Geheimnis in einer Datei dieser Phase.** Die Treffer, die
eine Erklärung brauchen, je einzeln:

1. **Die 14 Hexläufe** sind vierzehn Prüfsummen: der Modellabgleich der
   Integrationsstrecke, zwei Abbildprüfungen des Dockerfiles, die Modellfassung
   des Anbieters (ein öffentlicher Stand eines öffentlichen Modells), die beiden
   Baumhashes und ihre historischen Zwillinge, die Prüfsummen der eingefrorenen
   Messfassungen. Keiner ist ein Zugangsmittel; jeder ist eine Zusage, die rot
   wird, wenn sich etwas bewegt.
2. **Die 22 Postadressen** sind **eine** Adresse an sieben Stellen: die
   Kontaktadresse der Enterprise-Zeile, die seit dem 11.09.2026 auf Owner-Entscheid
   in beiden Store-Texten steht und deren ganzer Zweck die Veröffentlichung ist.
   Geführt als I-01, kein Befund.
3. **Die 15 Entropietreffer** sind vierzehn Pfade und ein Lizenzetikett. Die
   Entropiemessung findet Pfade, weil ein Pfad viele verschiedene Zeichen hat;
   das ist der Preis eines Verfahrens, das nach Dichte statt nach Form sucht, und
   es ist der Grund, warum es überhaupt etwas Neues finden könnte.

### Der zweite Lauf, ueber das ganze Verzeichnis docs/

Nach der Lehre von M-02 ist dieselbe Gegenprobe ein zweites Mal gelaufen, über
alle 405 Dateien unter `docs/` statt nur über die 72 dieser Phase. Die vier
gefährlichen Familien bleiben bei **null**. Zwei Dinge kommen hinzu:

1. **Der Name des Einhängepunktes des zweiten Anbieters**, in vier Dateien, drei
   davon Rohdaten einer gefahrenen Anfahrt und eine ein redigierbares Dokument.
   Das ist **M-16-02**, behoben.
2. **Eine Installationskennung einer abgebauten Testinstanz** in einer Rohdatei.
   Sie ist kein Zugangsmittel, sie benennt eine Instanz, die es seit dem
   04.09.2026 nicht mehr gibt, und eine Rohdatei einer gefahrenen Anfahrt wird
   nicht nachträglich redigiert. Geführt als I-02, kein Befund.

### Die Ausnahmeliste, auf ihre Gruende geprueft

Das ist die zweite Hälfte der Bedrohung T-16-48: ein Gate mit einer zu weiten
Ausnahmeliste bestätigt sich selbst. Die Liste ist deshalb **nicht** vom Gate
geprüft worden, das sie führt, sondern von einem eigenen Lauf mit eigenen Fragen:

| Frage | Antwort |
|---|---|
| Wie viele Einträge? | 46 vor diesem Plan, 49 danach (die drei Rohdateien der zehnten Familie) |
| Kürzester Grund | 95 Zeichen, also mehr als das Vierfache der Mindestlänge |
| Doppelt benutzter Grund | 0 |
| Grund unter acht Wörtern | 0 |
| Grund, der ein Versprechen statt einer Begründung ist | 0 |
| Eintrag ohne heutigen Fund (Ratsche) | 0, geprüft von einem Fall des Gates in beide Richtungen |

Die letzte Frage ist die wichtigste und hat in Plan 16-05 zum ersten Mal
zugeschlagen: sechs Gründe sagten damals sinngemäß "ein Dokument, das ein
späterer Plan noch ändern kann", und das ist eine Verfallsanzeige und keine
Begründung. Heute steht kein solcher Satz mehr auf der Liste.

### Die Mutationsprobe der neuen Familie

Eine Familie, die nie rot war, ist eine Behauptung. Die zehnte ist deshalb einmal
echt ausgelöst worden: mit dem Wert zurück im redigierten Dokument meldet das
Gate `['performance.md']` statt der leeren Liste, und mit der Redaktion ist es
grün. Der Baum ist danach zurückgesetzt worden; die Probe liegt in keinem Commit.

---

## 5. Performance-Durchgang

Diese Phase hat an drei Stellen etwas gebaut, das Laufzeit oder Platz kosten
kann. Alle drei werden hier einzeln beurteilt, und keine Zahl steht hier, die
nicht gemessen ist.

### 5.1 Die Instrumentierung des inneren Aufrufs

Zwei Uhrablesungen je innerem Aufruf und eine Rundung. Das ist die
billigste Messung, die die Sprache anbietet, und sie sitzt um genau eine
Anweisung. Die Protokollzeile entsteht **nur** oberhalb von 1.000 ms; unterhalb
schweigt die App, und ein eigener Fall je Richtung hält beides fest. Der Grund
für die Schwelle steht in der Quelle: die Unified Search fragt bei jedem
Tastenanschlag, und eine Zeile je Anschlag wäre Rauschen und keine Messung.

**Was hier nicht gemessen ist:** was die Zeile auf einer 4-GB-Box kostet. Sie ist
nie auf einer gelesen worden, weil es in dieser Phase keine gab.

### 5.2 Die sechs Sprachpakete

Zuwachs an Nutzlast: **19,7 MB installiert**, rund 7,6 MB als Paketdateien je
Architektur, vor dem Bau gegen die Paketquelle nachgesehen und nach dem Bau
mehrarchitektur-grün (Lauf 35597353780). Der Standard bleibt bei drei Sprachen,
also **kostet keine bestehende Installation eine Seite mehr**. Eine
Vorher-Nachher-Zahl der Abbildgröße nennt dieser Bericht bewusst nicht: die
Werkbank führt kein Größen-Tor, und eine Zahl ohne Messung wäre eine Behauptung.

### 5.3 Die Migration

Sie läuft einmal, im Wartungsmodus, ohne angemeldeten Nutzer, und sie fragt den
Container nicht. Ein zweiter Lauf ist ein no-op, und genau das ist einer ihrer
sechs Fälle. Der gefahrene Beweis steht in den Läufen 35594647362 und
35603906848.

### 5.4 Die Laufzeit der Suite selbst

210,78 s vor den Fixen und 225,77 s danach, bei vier zusätzlichen Fällen. Der
Unterschied liegt in der Größenordnung der Schwankung zwischen zwei Läufen
derselben Maschine und wird hier **nicht** als Messung einer Verschlechterung
ausgewiesen.

### 5.5 Der Stand der 1,5-Sekunden-Frage (M-01)

Unverändert offen, und das ist kein Versäumnis dieser Phase, sondern ihr
vereinbarter Umfang. Was jetzt da ist: die getrennte Zahl für den inneren
Aufruf, die Schwelle darunter, die Zeile mit drei Feldern, und ein Gate, das Sitz
und Schweigen festhält. Was fehlt: **die Zahl selbst**. Sie entsteht auf einer
Box und nirgends sonst.

---

## 6. Der Stand der vier Auflagen A1 bis A4

Je Auflage der Beleg **und** das, was nicht belegt ist. Die zweite Spalte ist die
wichtigere.

### A1: Nachfolgefassungen 92c und 99d

**Belegt.** `92c-wechsel.sh` prüft den Rückgabewert des `occ`-Aufrufs, bevor die
Ausgabe durch den Filter läuft, und bricht mit 36 ab, wenn die Registrierung
nicht stattgefunden hat. `99d-filter-sortierung.sh` liest das Feld der Anmeldung
aus der Datei, mit Abbruch 2 bei leerem Feld. Vier Wächter halten je Fassung die
Herkunft und die behobene Eigenschaft. Die sechs gefahrenen Fassungen sind
byteweise unberührt.

**NICHT belegt: die Wirkung.** Keine der beiden Fassungen ist gefahren worden.
Es gibt keine Rohdatei neben ihnen, und es wird keine geben, bis jemand sie
fährt. Der Satz steht in Versalien im Kopf jeder der beiden Dateien, und ein
Wächter je Fassung hält ihn dort fest.

### A2: Die Geheimnisregel als Gate, plus die Altfunde

**Belegt.** Das Gate liest jede Datei unter `docs/` rekursiv, heute 405, gegen
zehn Regeln, und es ist grün: **55 Fälle**. Die Bereinigung hat dreizehn Werte und
52 gesperrte Wörter aus vier Dokumenten genommen. Die Restliste trägt 49 Einträge
mit je einem eigenen Grund, und eine Ratsche zwingt sie zu schrumpfen, wenn ein
Fund verschwindet.

**NICHT belegt: die Reichweite über `docs/` hinaus.** `.planning/`, `scripts/`
und `testdata/` haben dieses Gate nicht. Die Gegenprobe dieses Berichts ist
einmal über alle 72 Dateien der Phase gelaufen, also auch über diese
Verzeichnisse, und hat dort nichts gefunden; **ein einmaliger Lauf ist aber kein
Gate**, und das ist der Unterschied, den M-02 gelehrt hat.

Und: **diese Auflage hat in diesem Bericht einen eigenen Befund bekommen**
(M-16-02). Ein Gate, das nur die Namensform eines Anbieters kennt, prüft die
Dateien des anderen nicht.

### A3: Die Instrumentierung des inneren Aufrufs

**Belegt.** `hrtime` um genau einen Aufruf, eine Schwelle darunter, drei Felder,
alle vier Fehlerpfade, fünf Fälle im Textgate, zwei PHPUnit-Fälle je Richtung.

**NICHT belegt: eine Zahl auf Zielhardware.** Es gibt keine. Die Auflage sagt das
selbst ("die Zahl auf Zielhardware liefert erst die naechste Box"), und weil A4
über den CI-Weg erfüllt wurde, hat diese Phase keine Box gefahren, die sie hätte
mitnehmen können. Der Preis dieser Entscheidung steht hier, damit er nicht
untergeht.

### A4: Die Sprachfaelle ohne Fremdbestand

**Belegt und abgenommen.** Lauf **35586213137** vom 21.09.2026, Auftrag
`index-search-e2e (sqlite, ubuntu-24.04-arm)`, 3 min 43 s, success beim ersten
Anlauf, `files on the instance before the corpus: 0`, `corpus entries: 39`, zehn
von zehn Sprachfällen grün. Owner-Wort am Checkpoint des Plans 16-08: "Zweig a,
zustimmen". Keine Box, kein Deckel-Abruf.

**NICHT belegt, und der Vorbehalt des Weges gehört dazu:** keine echte Nextcloud
mit AppAPI und HaRP, keine Maschine des Zieltyps, keine harte Speichergrenze,
keine Zeit- oder Speicheraussage, keine Aussage über das Verhalten unter
Fremdbestand, keine über Datenbankdialekte, und **eine andere OCR-Fassung als im
Auslieferungsabbild** (5.3.4 gegen 5.5.0), woran die drei gescannten Fälle
hängen.

---

## 7. Befundliste

| ID | Schwere | Befund | Stand |
|---|---|---|---|
| M-16-01 | MEDIUM | Der Fix des Flake-Stammes `single-flight-zeit` aus Plan 16-01 hat nicht getragen. Der Fall `test_with_the_release_on_a_cold_engine_gets_exactly_one_run` ist am 21.09.2026 **viermal** in CI rot gegangen (35586354661, 35594647359, 35596116820, 35597353833), jedes Mal MIT der neuen Frist von dreißig Sekunden. Die Deutung "lastempfindlich" war falsch: der Testclient öffnet je Anfrage ein eigenes Tor und schließt es wieder, und die Aufgabe, die der Handler bestellt, ist eine lose Aufgabe auf dieser Schleife. Ob sie ihren ersten Zeitschlitz bekommt, bevor das Tor zugeht, ist ein Wettlauf, und eine längere Frist entscheidet ihn nicht | **behoben** in diesem Plan: der Fall läuft auf der Schleife des Falls statt durch den Testclient und wartet die Aufgabe ab, genau wie sein Nachbar, der denselben Grund seit Phase 14 im Docstring trägt. Zwölf von zwölf Wiederholungen grün. Das **Flake-Register** trägt den Nachtrag, dass der erste Fix nicht getragen hat |
| M-16-02 | MEDIUM | Die vier Familien des Gates aus Plan 16-02, die eine Ressource an ihrem Namen erkennen, kennen die Namensform **eines** Anbieters; dieses Projekt hat bei zweien gemietet. Der Name, den der zweite für den Einhängepunkt eines Datenträgers bildet, trägt dessen Kennung und stand nach der Bereinigung von Plan 16-05 weiter an drei Stellen in einem redigierbaren Dokument unter `docs/`. Gefunden hat ihn nicht das Gate, sondern die Gegenprobe dieses Berichts, und genau dafür gibt es sie | **behoben** in diesem Plan: das Dokument trägt an allen drei Stellen die Platzhalterform, die es an einer vierten schon vorher benutzt hat; das Gate hat eine zehnte Familie mit Kommentar, sauberer und mutierter Probe; die drei Rohdateien der gefahrenen Anfahrt vom 04.09.2026 stehen mit je einem eigenen Grund auf der Ausnahmeliste; die Mutationsprobe ist gefahren |
| L-16-01 | LOW | Derselbe Wettlauf wie M-16-01 steckt im Nachbarfall `test_ten_searches_in_a_row_do_not_pay_for_ten_loads`: er fährt zehn Anfragen durch den Testclient und liest danach, ob wirklich ein Lauf stattgefunden hat. Er ist nie rot gewesen, weil zehn Anfragen zehn Chancen sind und eine reicht | weitergereicht mit Adresse in `deferred-items.md`; kein Fix in dieser Phase, weil der Fall seine Aussage genau über die zehn Anfragen durch die Route macht und ein Umbau sie ersetzen statt härten würde |
| L-16-02 | LOW | Die vier roten Läufe aus M-16-01 sind entstanden, ohne dass eine SUMMARY dieser Phase sie nennt. Die SUMMARY von Plan 16-10 nennt den grünen Abbildbau desselben Pushes und nicht den roten Gate-Lauf daneben. Ein Plan liest den Lauf, den er erwartet, und nicht die Laufliste des Pushes | weitergereicht als Verfahrensregel in `deferred-items.md`: nach einem Push wird `gh run list` für diesen Push gelesen und jeder nicht-grüne Lauf benannt, bevor die SUMMARY geschrieben wird |
| L-16-03 | LOW | Der dritte Flake-Stamm `parity-login` ist unverändert offen. Er ist in dieser Phase **nicht** wieder aufgetreten; der Paritätsauftrag war in allen Läufen dieser Phase grün | beobachtet, kein Fix, wie in Plan 16-01 entschieden. Der Merker gilt: bei rot erst wiederholen, dann suchen, und den älteren Befund daneben lesen |

**Kein CRITICAL, kein HIGH.**

### Zwei Punkte zur Vollstaendigkeit, die keine Befunde sind

**I-01:** Die Kontaktadresse der Enterprise-Zeile steht an sieben Stellen in
Store-Texten und READMEs. Sie ist seit dem 11.09.2026 auf Owner-Entscheid dort,
ihr Zweck ist die Veröffentlichung, und eine Zeile, die um ein Angebot bittet,
ohne zu sagen wohin, wäre keine. Kein Befund.

**I-02:** Eine Installationskennung einer am 04.09.2026 abgebauten Testinstanz
steht in einer Rohdatei einer gefahrenen Anfahrt. Sie ist kein Zugangsmittel, die
Instanz gibt es nicht mehr, und eine Rohdatei wird nach dem Lauf nicht redigiert.
Kein Befund.

### Der Stand der aus Phase 15 weitergereichten Befunde

| Befund | Schwere in Phase 15 | Stand am 21.09.2026 |
|---|---|---|
| M-01 | MEDIUM | **teilerfuellt.** Die Instrumentierung steht (16-06), die Zahl auf Zielhardware steht aus. Sie entsteht auf einer Box und nirgends sonst |
| M-02 | MEDIUM | **geschlossen**, in drei Schritten: Gate über `docs/` (16-02), Bereinigung und Restliste (16-05), und die zehnte Familie dieses Plans, die die Lücke schließt, die beide gelassen hatten |
| L-03 | LOW | **behoben** als Nachfolgefassung `92c-wechsel.sh` (16-03); Wirkung nicht nachgemessen |
| L-04 | LOW | **behoben** als Nachfolgefassung `99d-filter-sortierung.sh` (16-03); Wirkung nicht nachgemessen |
| L-05 | LOW | weitergereicht mit Adresse: erster Plan der nächsten bezahlten Anfahrt |
| L-06 | LOW | weitergereicht mit Adresse: erster Plan der nächsten bezahlten Anfahrt |
| L-07 | LOW | **behoben** (16-04): `cmd_destroy` nimmt das Schlüsselpaar mit und liest es zurück; nur statisch geprüft |
| L-08 | LOW | benannte Asymmetrie, kein Fix, entschieden und begründet |
| L-09 | LOW | **geschlossen** am 21.09.2026 mit Lauf 35586213137 und dem Owner-Wort "Zweig a, zustimmen" |
| L-10 | LOW | **behoben**: Vokabularregel im Gate (16-02) und 52 Ersetzungen in vier Dokumenten (16-05); drei Vorkommen bleiben mit je eigenem Grund |
| L-11 | LOW | **hat nicht getragen.** Der Fix aus 16-01 ist viermal in CI gescheitert; der Befund lebt als M-16-01 weiter und ist dort zum zweiten Mal behandelt |

Zehn von elf weitergereichten Befunden haben ihr Verdikt bekommen. Der elfte,
L-11, ist der unangenehme, und er steht nicht als erledigt in dieser Tabelle,
sondern als das, was er war.

---

## 8. Was dieser Bericht nicht sagt

Er sagt **nichts über das Verhalten auf Zielhardware**. Diese Phase hat keine
Box gefahren, weil Auflage A4 über den kostenlosen Weg erfüllt worden ist, und
das ist die richtige Entscheidung gewesen und hat trotzdem einen Preis: die
Instrumentierung aus A3 ist nie auf einer 4-GB-Box gelesen worden, und die Frage,
die M-01 stellt, ist damit weiter offen.

Er sagt **nichts darüber, ob die Nachfolgefassungen aus A1 tun, was sie sollen**.
Beide sind statisch abgenommen und keine ist gefahren.

Er sagt **nichts darüber, ob der zweite Fix des Stammes `single-flight-zeit` in
CI trägt**. Er ist auf dieser Maschine zwölfmal grün, und genau das war der erste
Fix auch. Der Beweis ist der nächste Push, und wenn der Fall danach wieder rot
wird, ist das kein Flattern mehr, sondern ein dritter Anlauf.

Er sagt **nichts über die sieben gleichzeitig grünen Tag-Läufe**, die das
Flake-Register für den Tag verlangt. Auf dem heutigen Baum sind sechs Werkbänke
gleichzeitig grün; die siebte läuft erst auf einem Tag, und der Tag ist Plan
16-14.

Er sagt **nichts über `.planning/`, `scripts/` und `testdata/` als Dauerzustand**.
Die Gegenprobe hat sie einmal gelesen und nichts gefunden. Ein Lauf ist kein
Gate, und diese Unterscheidung ist genau der Befund M-02, den diese Phase geerbt
hat.

Er nennt **keine Adresse, keine Kennung und keinen Passwortinhalt**, auch nicht
die aus M-16-02: ein Bericht, der sie zitierte, wäre die Datei, die sie trägt.
`docs/` ist öffentlich, und dieser Bericht ist vor dem Commit mit demselben
Verfahren durchgesehen worden, das in Abschnitt 4 steht, und zusätzlich von dem
Gate, das er selbst um eine Familie erweitert hat.

**Die Freigabe der Phase liegt beim Owner und nicht in diesem Bericht.** Sie ist
am Tag dieses Berichts noch nicht erteilt; der Checkpoint ist Task 3 des Plans
16-13, und ohne ihn beginnt die Abgabe nicht (Owner-Regel vom 06.09.2026).
