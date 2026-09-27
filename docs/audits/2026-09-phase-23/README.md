---
phase: 23-haertung-und-store-einreichung-1-3-0
audited: 2026-09-27
tree: 8fa035f30117da25005c59a6e8e71abf0d3c3332
commit: b544842b9313e73fe8b108722c9dbf96ee42fa36
scope: "Security voll ueber die ganze App; Bug und Performance gezielt auf git diff v1.2.0..HEAD der Produktpfade (Phasen 18 bis 21, 23) und den Merge 257caac (Issue #14), D-07"
critical: 0
high: 0
medium: 1
low: 4
total: 5
status: medium_and_above_fixed
fixed: [F-23-01, F-23-02, F-23-03]
decided: [F-23-05]
still_open: [F-23-04]
accepted: 2026-09-27
closed_from_earlier: [V-22-01, V-22-02, L-16-01, L-16-04]
---

# Phase 23: Launch-Haertung und Security-, Bug- und Performance-Audit

**Umfang:** die Pläne 23-01 bis 23-07 dieser Phase und der Merge `257caac`
(Issue #14), gelesen gegen den Baum von Commit `b544842`. Der Bericht liegt nach
der Owner-Regel vom 15.08.2026 vor dem Phasenabschluss und nach der Owner-Regel
vom 06.09.2026 vor der Abgabe. Er folgt der Hausform von
`docs/audits/2026-09-phase-16/README.md`: vorn die Haertungsmatrix, dahinter die
Audits, am Ende die Befundliste und was dieser Bericht nicht sagt.

Der Zuschnitt ist Owner-Entscheid D-07 vom 26.09.2026. **Security voll** über die
ganze App, wie vor jeder Abgabe. **Bug und Performance gezielt** auf die Pfade,
die sich seit 1.2.0 geändert haben: Schema, Marken und Umbauweg (18), Frageseite
(19), Kataloge (20), niederländische Komposita (21), Kaltstart-Fix und
gone-Reparaturlauf (23). Dazu der #14-Fix `257caac`, der ohne eigenes
Phasenaudit in den Baum kam und deshalb hier den ausführlichsten Abschnitt hat.

Die Überschriften stehen ohne Umlaute, weil Prüfungen und Verweise auf sie
zeigen; der Fließtext benutzt echte Umlaute. Dieser Bericht nennt Laufnummern,
Dateinamen, Commits und Zahlen und sonst nichts: keine Kennung, keine Adresse,
keinen Inhalt eines Geheimnisses.

**Bilanz vorweg: kein CRITICAL, kein HIGH.** Ein MEDIUM, in diesem Plan mit Test
behoben. Vier LOW: zwei behoben, einer mit Verdikt und Zieladresse
weitergereicht, einer vom Owner entschieden ("So lassen"). Die Haertung ist am
27.09.2026 abgenommen (Abschnitt 10). Dazu
schließt dieser Plan zwei Altbefunde aus Phase 16 (L-16-01 strukturell durch
23-01, L-16-04 mit einem Kommentar-Fix), und die Phase selbst schließt die zwei
Produktbefunde der Phase 22 (V-22-01, V-22-02).

Der MEDIUM gehört in den ersten Absatz, weil er alt ist und erst diese Phase ihn
sichtbar gemacht hat: **Mit eingeschalteter Leerlauf-Freigabe hat der Container
die Gewichte 30 Sekunden nach dem Freigeben wieder geladen, ohne dass jemand
gesucht hätte.** Die Warmlauf-Anforderung einer Suche auf warmer Engine blieb
stehen, und die Freigabe hat sie geerbt (F-23-01). Der Standard 0 war nicht
betroffen, weil dort keine Freigabe läuft.

---

## 1. Die Haertungsmatrix

Die Owner-Regel vom 06.09.2026 nennt acht Pfade. Jeder hat eine Zeile mit dem,
womit geprüft wurde, dem Beleg und dem Urteil.

| Nr. | Pfad | Womit geprueft | Beleg | Urteil |
|---|---|---|---|---|
| 1 | Fehler- und Randpfade | Kaltstart der ersten Suche nach Neustart (D-01), Einwortregel auf `/snippets` (D-02), Migration mit leerem Fall und Rollback (23-05) | integration.yml Lauf **36285187617**: `first search after a restart, cold engine ...: 973 ms on amd64 ... HTTP 200, 1 hits out of the lexical list`, danach `warm run took 0 s`, danach die Paraphrase; `test_snippets_endpoint.py` 29 Fälle mit der D-02-Parametrisierung; `Version001300Date20260927000000Test.php` 8 Fälle (leere Tabelle, Rollback ohne commit und mit weitergeworfener Ausnahme, Bänder 1000/1000/500, zweiter Lauf als no-op) | **gehalten** |
| 2 | Rechtegrenzen | `git diff v1.2.0..HEAD -- php/lib/Service/SearchService.php php/lib/Service/PathResolverService.php php/lib/Controller/GatewayController.php php/lib/Service/QueueService.php` und inhaltliche Lesung (Abschnitt 3, V4) | der Diff stammt vollständig aus `257caac`, seit Phasenbeginn `8b060e5` ist er über diese vier Dateien leer; Gateway liefert Bytes nur über `SearchService::readableFile`, gone nur bei leerer Nutzerliste (`QueueService::describe`), 8 Fälle in `test_php_acl_boundary.py`, 28 in `PathResolverServiceTest.php`, 9 in `QueueServiceReaderTest.php`, 6 in `GatewayControllerTest.php` | **gehalten**, ein LOW in der Admin-Suche (F-23-04), der nie eine falsche Datei nennt |
| 3 | Neustart, Upgrade, Migration | Store upgrade 0 bis 6 mit Saat eines #14-Fehlurteils (23-06), Zusicherung 3 und 3b, probe-92d von v1.2.0 | HaRP deploy Lauf **36288038636** (vier Beine grün): `Updated <findling> to 1.3.0`, `moved by 1 .container.docs 94 to 95`, `moved by -1 .nextcloud.skipped 8 to 7`, `the seed word finds upgrade-gone-seed.txt`, `all seven assurances hold`, Umbau `through after 4 rounds`; probe-92d Lauf **36288064261**: `bestandstor-bestanden ja`, Gegenprobe endet mit 41 | **gehalten** |
| 4 | Kaputte und boesartige Dateien | die bestehenden Suitefälle; die Extraktion ist seit 1.2.0 nicht berührt | 51 Fälle in `test_extract_errors.py`, 21 in `test_extract_edge_paths.py`, 25 in `test_sandbox.py` (davon vier lokal übersprungen, keine POSIX-Shell, in CI gefahren); `extract/errors.py` hat seit 1.2.0 nur den Grund `unreadable` dazubekommen | **gehalten** |
| 5 | Ressourcengrenzen | Lazy-Load ohne Vorwärmen (D-03), ein Warmlauf je Fenster, Reparaturlauf proportional zur gone-Zahl, Ladefenster D-08 | `test_no_warm_run_is_wanted_without_a_request` bei 0 und 900; `test_ten_warm_runs_at_once_pay_for_exactly_one_load`; one_load im Dispatch-Lauf **36286121016**: `engine-loads-after-search=1`, `search-ms=10.3`, `warm-ms=669.6`; Migration liest nur `skipped/gone`-Zeilen und reiht in Bändern zu 1000 ein | **gehalten**, mit dem Befund F-23-01 in der Leerlauf-Freigabe (behoben) und dem Ladefenster D-08 als angenommenem Restrisiko (Abschnitt 5.2) |
| 6 | Fremdinstallation auf frischer Nextcloud | Store install 0 bis 7 auf amd64 (stable33, stable34, stable35) und arm64 (stable34) | HaRP deploy Lauf **36288038636** und auf dem Kopf `68b679a` Lauf **36289457405**, alle Beine success | **gehalten** |
| 7 | Store-Vorgaben | `test_store_metadata.py` mit den neuen Gates aus 23-07 (Messzahl 730.2, vier Grenzpunkte je Text, Doku-Vergleich, Sprachzeile) | 76 Fälle lokal grün; PHP and store metadata gates Lauf **36289457414** auf `68b679a` success, `OK (319 tests, 1186 assertions)`, 52 Dateien ohne Syntaxfehler | **gehalten** |
| 8 | Alle Audits erneut | Security (Abschnitte 3 und 4), Bugs und Performance (Abschnitt 5) | die Abschnitte unten | **gefahren**, ein MEDIUM gefunden und behoben |

### Zu Zeile 1, im Einzelnen

Die Kaltstartroute ist dreistufig nachgemessen: erste Suche nach dem Neustart
mit Trefferpflicht, dann Warten bis `engineState=loaded`, dann die Paraphrase.
Die Dauer der ersten Suche wird gedruckt und nicht zugesichert, weil ein
CI-Runner keine Zielhardware ist. Zugesichert ist das, was V-22-01 und V-22-02
gebrochen hatten: eine Antwort mit Treffern statt einer leeren Gruppe.

Die Einwortregel auf `/snippets` liest dieselben Felder wie `/search`
(`rewritten.operators`, `rewritten.one_term`, `title_only`), also gibt es keine
zweite Definition von "ein Wort". Die Quelle bleibt
`query/rewrite.py::carries_one_term`.

### Zu Zeile 2, weil sie etwas beweisen muss statt behaupten

**Die Berechtigungskette hat sich seit 1.2.0 an genau einer Stelle bewegt, und
das ist `257caac`.** Die Phase 23 selbst hat keine der vier Dateien angefasst:
`git diff --stat 8b060e5..HEAD` über sie ist leer. Was `257caac` geändert hat,
steht inhaltlich in Abschnitt 3 unter V4.

---

## 2. Gate-Protokoll

Gefahren am 27.09.2026 auf der Entwicklungsmaschine (Windows, Python 3.13, uv),
in der Reihenfolge von `.github/workflows/python.yml`, `pyright` mit
`PYRIGHT_PYTHON_FORCE_VERSION=latest` (Regel vom 19.09.2026).

| Stufe | Befehl | Ausgang | Zahl |
|---|---|---|---|
| 1 | `uv run ruff check .` | grün | All checks passed |
| 2 | `uv run ruff format --check .` | grün | 147 Dateien bereits formatiert |
| 3 | `uv run pyright` | grün | 0 errors, 0 warnings, 0 informations |
| 4 | `uv run vulture src tests --min-confidence 80` | grün | keine Ausgabe |
| 5 | `uv run pytest -q` (VOLLE Suite), Baum `6f27930` vor den Fixen | grün bis auf einen Ledgerfall | **3347 bestanden, 15 übersprungen, 1 rot**; der rote Fall ist der Baumhash, weil der Fix von F-23-01 mitten in den laufenden Lauf geschrieben wurde. Ohne diese Überschneidung: 3348 bestanden, gleich dem Stand von 23-07 |
| 5b | `uv run pytest -q` (VOLLE Suite), Baum `b544842` nach den Fixen | grün | **3349 bestanden, 15 übersprungen**, 219,00 s; der eine Fall mehr ist der neue Fall von F-23-01 |
| 6a | `uv run ruff check --config pyproject.toml ../scripts` | grün | All checks passed |
| 6b | `uv run ruff format --config pyproject.toml --check ../scripts` | grün | 14 Dateien bereits formatiert |

### Die Skipzahl gegen die Referenz

| Stand | bestanden | uebersprungen |
|---|---:|---:|
| Referenz aus STATE.md zu Beginn der Phase | 3324 | 15 |
| 23-04 | 3339 | 15 |
| 23-07 | 3348 | 15 |
| dieser Plan, vor den Fixen | 3347 + 1 | 15 |
| **dieser Plan, nach den Fixen** | **3349** | **15** |

**Die Skipzahl steht bei 15 und ist nicht gewachsen.** Alle 15 hängen an der
Maschine (kein Modellartefakt, kein `tesseract`, keine POSIX-Shell, kein
Korpusgenerator). In CI, wo diese Voraussetzungen da sind, stehen 11
übersprungen: Python gates Lauf **36289457406** auf `68b679a` meldet
`3352 passed, 11 skipped`.

### Die Stufen, die hier nicht fahrbar sind

| Stufe | Lage | Ersatznachweis |
|---|---|---|
| `php -l`, PHPUnit | PHPUnit braucht einen Checkout des Servers mit dessen Test-Bootstrap | php.yml Lauf **36289457414** auf `68b679a`: 52 Dateien `No syntax errors detected`, `OK (319 tests, 1186 assertions)`; vor der Phase 311 (Lauf 36262662006 auf `257caac`), +8 aus 23-05 |
| Die Werkbänke mit Instanz | keine Nextcloud auf dieser Maschine, und der Speicher der Maschine trägt keine parallelen Vollstrecken | die sechs Läufe auf `68b679a`, siehe unten, und die Läufe aus 23-04 bis 23-06 |

### Der CI-Stand des letzten gepushten Kopfes

Für Commit `68b679a` (Push 5642800..68b679a) sind alle sechs Werkbänke, die auf
einen Push laufen, **gleichzeitig grün**:

| Werkbank | Lauf | Ausgang |
|---|---|---|
| Python gates | 36289457406 | success |
| PHP and store metadata gates | 36289457414 | success |
| Integration | 36289457408 | success |
| Resilience | 36289457454 | success |
| Multi-arch image | 36289457381 | success |
| HaRP deploy | 36289457405 | success |

Die Fixe dieses Plans (Abschnitt 7) sind gepusht (Merge auf main, Push
68b679a..87e41cd am 27.09.2026). Alle sechs Werkbänke des neuen Kopfes 87e41cd
sind grün, nachgetragen vom Orchestrator:

| Workflow | Lauf (87e41cd) | Ergebnis |
|---|---|---|
| Python gates | 36291849649 | success |
| PHP and store metadata gates | 36291849698 | success |
| Integration | 36291849669 | success |
| Resilience | 36291849646 | success |
| Multi-arch image | 36291849663 | success |
| HaRP deploy | 36291849691 | success |

Damit ist Erfolgskriterium 3 vollständig erfüllt und der Vorbehalt bei F-23-01
("CI des neuen Kopfes steht aus") aufgelöst.

---

## 3. Security, ASVS V2, V4, V5, V6, V7, V12, V14

Voll über die ganze App, wie D-07 es verlangt. Die Phasen 17 bis 22 haben je ein
eigenes Audit (17, 18, 22 unter `docs/audits/`, 19 bis 21 als REVIEW und
SECURITY im Phasenordner). Was hier neu gelesen wurde, ist der Stand heute über
alle Routen und alle Grenzen, mit dem Schwerpunkt auf den Pfaden ohne eigenes
Audit: `257caac` und Phase 23.

### V2, Anmeldedaten: gehalten

Keine neue Anmeldung. Die Anmeldung der ExApp ist unverändert, ein Fall in
`test_search_endpoint.py` hält fest, dass eine Kopfzeile in der richtigen Form
mit falschem Wert 401 bekommt. Die Saat aus 23-06 benutzt nur die vorhandenen
Werte der Werkbank und druckt keinen davon. Die Zugangsmarke des Stores wird
erst in Plan 23-09 berührt, und dort gilt die Regel aus L-16-05.

### V4, Zugriffskontrolle: gehalten, und hier ist der #14-Fix inhaltlich gelesen

**Keine neue Route, kein neues Feld am Rand.** `git diff v1.2.0..HEAD` über
`backend/src` zeigt keinen neuen `ROUTER`-Eintrag, `backend/appinfo/info.xml`
keine neue Route und keine geänderte Zugriffsstufe. Auf der PHP-Seite hat sich
unter `lib/Controller` nur `GatewayController.php` bewegt. Alle Routen der
Einstellungsseite (`/admin/overview`, `/admin/diagnose`, `/admin/rules`,
`/admin/rules/preview`) tragen kein `NoAdminRequired` und sind damit
Admin-Routen; die sieben Container-Routen tragen `ExAppRequired`.

**`SearchService::readableFile` ist die einzige Stelle, die beide Fragen der
Kette stellt**, erreichbar und lesbar, und seit `257caac` fragen alle drei
Aufrufer dort: die Endfilterung der Suche, die Wahl des Lesers in der Queue und
das Gateway. Vorher fragten Queue und Gateway nur die erste Frage. Ein Mitglied
eines Team-Ordners, das eine Datei erreicht, aber wegen der erweiterten Rechte
nicht lesen darf, war damit Leser, und die Datei endete als `skipped(gone)`,
obwohl sie da war. Das ist der Fehler von #14, und er war zugleich eine
Rechtefrage: die Bytes wurden im Namen von jemandem geholt, der sie nicht öffnen
durfte. Heute gilt:

| Stelle | Was sie fragt | Urteil |
|---|---|---|
| `GatewayController` | `readableFile` am Nutzer der Anfrage; nicht sichtbar, nicht lesbar und nicht vorhanden geben dieselbe 404 | **gehalten**, keine Sonde für fremde Dateien |
| `QueueService::readerOf` | die ersten 20 Nutzer der sortierten Liste, je `readableFile`; ohne Leser `unreadable`, nie `gone` | **gehalten**; `gone` nur bei leerer Nutzerliste des Mount-Caches, der einzige Fall, der eine Löschung behaupten darf |
| `SearchService` Endfilterung | `readableFile` am suchenden Nutzer, vor jedem Titel, Pfad und Auszug | **gehalten**, wie seit Audit L5 |
| `PathResolverService` Admin-Suche | Pfad ohne Besitzer über `oc_mounts`: genau eine Wurzel, dann bis zu 20 Mitglieder mit `readableNode`; mit Besitzer nur über denselben Mount | **gehalten** für die Rechte; ein LOW zur Genauigkeit (F-23-04) |

Die Admin-Suche ist die neue Fläche von `257caac`. Sie steht hinter einer
Admin-Route, und ein Admin sieht die Dateien der Instanz ohnehin. Geprüft wurde
deshalb nicht, ob sie etwas verrät, sondern ob sie etwas Falsches sagt: sie
nennt nie die Datei eines anderen mit gleichem Namen. Mit Besitzer vor dem Pfad
antwortet der Rückfall nur, wenn der Besitzer den Pfad über dieselbe Wurzel am
selben Einhängepunkt trägt (`carriesThrough`), und die Antwort für einen
unbekannten Nutzer ist dieselbe Null wie für ein Nicht-Mitglied. Die
LIKE-Muster maskieren den Pfadteil mit `escapeLikeParameter`. Der eine Rest ist
F-23-04: das Muster `/%/files/<Ordner>/` trifft auch einen tieferen Mount eines
anderen Nutzers, dessen eigener Ordner zufällig `files` heißt, und zählt dessen
Wurzel als zweite. Die Folge ist eine Ablehnung, die mit Besitzer vor dem Pfad
aufgelöst wird, und nie eine falsche Antwort.

### V5, Eingaben: gehalten

Die Suchzeile geht weiter durch den nachsichtigen Parser von Tantivy; die
Feldliste kommt seit Phase 19 aus dem Verzeichnis auf der Platte
(`field_plan_for`) und nie aus der getippten Zeile. Die Einwortregel auf
`/snippets` ist eine Verengung, keine neue Eingabe. Die Migration liest nur die
eigene Tabelle und schreibt nur die eigene Queue; alle Werte gehen als benannte
Parameter. SQL mit zusammengesetztem Text gibt es im Backend nur für
Platzhalterlisten aus `?`, und das war vor 1.2.0 schon so.

### V6, Kryptographie: gehalten

Unverändert. Beide Signaturen entstehen in CI; die Schlüssel leben im
Geheimnisspeicher der Werkbank. Die Gegenprobe in Abschnitt 4 findet kein
Schlüsselmaterial.

### V7, was protokolliert und was öffentlich wird: gehalten

Neue Protokollzeilen seit 1.2.0, jede gelesen:

* `QueueService`: `skipped queued files no user asked may read` mit genau einem
  Feld, der Zahl. Kein Dateiname, keine Nutzerkennung.
* Migration `Version001300Date20260927000000`: `no gone verdicts to repair` oder
  `requeued %d files once judged gone`, nur die Zahl.
* Warmlauf (23-01): keine neue Zeile; `api/search.py` protokolliert weiter nur
  den Typnamen einer Ausnahme, nie den Suchtext.
* `index/rebuild.py`, `index/open.py`, `main.py` (Phasen 18 und 21): Typnamen,
  Zähler und feste Sätze. Kein Pfad aus Nutzerdaten, kein Suchtext.
* integration.yml (23-04): druckt die Dauer der ersten Suche, die Trefferzahl
  und die Dauer des Warmlaufs. Das Geheimnis der ExApp geht wie bisher nur
  base64-kodiert in die Kopfzeile und nie in eine Ausgabe.

### V12, Ressourcengrenzen: gehalten, mit einem behobenen Befund

Keine Decke des Produkts ist bewegt worden. Der Kaltstart-Fix lädt nie im
Request (`query_may_load` antwortet bei jedem Schalterwert False), und D-03
bleibt: ohne Suche wird nichts vorgewärmt. Die Leerlauf-Freigabe hat die
Speichergrenze aber nicht gehalten, sobald eine Suche auf warmer Engine
vorausging; das ist F-23-01 in Abschnitt 5.1. Der Reparaturlauf ist einmalig und
proportional zur Zahl der gone-Urteile.

### V14, Konfiguration: gehalten

HART-04 hat die Abhängigkeitsliste dem Container-Ist angeglichen: fastembed,
loguru, mmh3, py-rust-stemmers, requests und urllib3 sind aus dem Lockfile, und
ein neuer Schritt in docker.yml prüft im gepushten Abbild mit `--network none`,
dass fastembed und requests fehlen und tokenizers und numpy da sind (Lauf
**36285187622**, beide Plattformen success). Der Text der Umgebungsvariable
`FINDLING_EMBED_IDLE_RELEASE_SECONDS` sagt jetzt, was der Container tut; der
XML-Kommentar darüber tat es bis zu F-23-03 nicht ganz.

---

## 4. Die Geheimnis-Gegenprobe, mit einem anderen Verfahren

**Eine Gegenprobe mit dem Muster der Umsetzung ist keine Gegenprobe** (Regel vom
02.08.2026). Das Gate `test_public_artifacts.py` ist in dieser Phase unverändert
und selbst das Muster der Umsetzung. Die Gegenprobe unterscheidet sich deshalb
in Reichweite und Verfahren:

* **Reichweite.** Nicht `docs/`, sondern jede Datei, die diese Phase committet
  hat (`git diff --name-only 8b060e5..HEAD`, 54 Dateien), plus die 41 Dateien
  von `257caac`: 95 Dateien in jedem Verzeichnis, darunter `.planning/`,
  `.github/`, `backend/` und `php/`, die das Gate nicht liest.
* **Verfahren.** Ein eigenes Skript mit sechs Musterfamilien, die das Gate
  **nicht** führt, und dazu eine Messung, die kein Muster ist: die Entropie
  zugewiesener Werte. Das Skript lag nur im Arbeitsbaum und ist in keinem
  Commit.

| Familie | Was gesucht wurde | Fuehrt das Gate sie? | Treffer | Urteil |
|---|---|---|---:|---|
| `jwt-und-bearer` | ein Token aus drei punktgetrennten Teilen, und eine Anmeldekopfzeile mit Wert | nein | 0 | sauber |
| `zugangsdaten-in-einer-adresse` | Schema, Benutzer, Doppelpunkt, Wert, Klammeraffe, Rechner | nein | 0 | sauber |
| `herstellermarken-fremder-dienste` | die Präfixe der Zugangsmarken von fünf fremden Diensten, acht Präfixe | nein | 0 | sauber |
| `anwendungspasswort-in-fuenf-gruppen` | fünf Gruppen zu fünf Zeichen, die Form, die Nextcloud selbst vergibt | nein | 0 | sauber |
| `oeffentliche-ipv4` | jede Adresse außerhalb der privaten, der Loopback- und der Dokumentationsnetze | nein, das Gate prüft Adressen nur über seine eigene Maschinenregel | 0 | sauber |
| `elektronische-postadresse` | jede Postadresse | nein | 29 | zwei Adressen, beide Befund-frei, siehe unten |
| `hohe-entropie-in-einer-zuweisung` | Shannon-Entropie ab 4,2 über zugewiesenen Werten ab Länge 20, **kein Muster** | nein, und es kann sie nicht führen | 36 | Bezeichner, Konstantennamen, Korpusdateinamen und eine absichtlich falsche Testanmeldung |

Die Treffer, die eine Erklärung brauchen:

1. **Die 29 Postadressen** sind zwei Adressen. 25 sind die Kontaktadresse der
   Enterprise-Zeile in beiden info.xml, drei READMEs und der Vorlage, seit dem
   11.09.2026 auf Owner-Entscheid dort und zur Veröffentlichung bestimmt (I-01
   aus Phase 16). Vier sind die Autorenadresse der Commits in vier
   Planungsdateien, wo sie als Prüfregel für den Push steht; dieselbe Adresse
   trägt jeder Commit dieses Repositoriums. Kein Befund.
2. **Die 36 Entropietreffer** sind Konstantennamen der Ledger und Gates
   (`V12_IMAGE_SWITCH...`, `DRIVEN_LANGUAGE...`, `LANGUAGE_ANALYZERS...`), zwei
   Statuscode-Namen, ein Korpusdateiname an zwei Stellen in integration.yml,
   die Hälfte davon doppelt gezählt, weil `test_measurement_scripts.py` auch in
   `257caac` geändert ist, und die
   base64-Form von "alice:not-the-secret" in `test_search_endpoint.py`, die
   richtige Form mit falschem Wert, die der Fall für die 401 braucht. Die
   Messung findet Bezeichner, weil ein langer Bezeichner viele verschiedene
   Zeichen hat; das ist der Preis eines Verfahrens nach Dichte statt nach Form.

**Ergebnis: kein Geheimnis in einer Datei dieser Phase und keines in
`257caac`.**

### Die Ausnahmeliste, auf ihre Gruende geprueft

Die Liste ist nicht vom Gate geprüft worden, das sie führt, sondern mit eigenen
Fragen (Bedrohung T-23-28):

| Frage | Antwort |
|---|---|
| Wie viele Einträge? | 51 (49 nach Phase 16, zwei aus den Phasen 17 bis 22; Phase 23 hat keinen hinzugefügt) |
| Kürzester Grund | 95 Zeichen |
| Doppelt benutzter Grund | 0 |
| Grund unter acht Wörtern | 0 |
| Grund, der ein Versprechen statt einer Begründung ist | 0 |
| Eintrag ohne heutigen Fund (Ratsche) | 0, der Fall des Gates ist grün in beide Richtungen |
| Verteilung auf Familien | Muster der Umsetzung 19, Schlüsselwort mit Wert 11, Ressourcenkennung 10, Vokabular 4, Datenträgername 3, Privatschlüsselkopf 2, Base64-Block 2 |

---

## 5. Bug- und Performance-Durchgang, gezielt

Je Pfad: was geprüft wurde, das Urteil und die Befund-ID, falls einer. Die
Pfade der Phasen 18 bis 21 haben eigene Audits mit behobenen MEDIUM und HIGH
(Phase 18: 1 CRIT, 4 HIGH, 8 MEDIUM, alle behoben; 19: 1 HIGH, 5 MEDIUM, alle
behoben; 20 und 21: `threats_open: 0`). Für sie ist hier geprüft, was sich seit
ihrem Audit bewegt hat und ob ihre Schnittstellen zu Phase 23 halten.

### 5.1 Die Pfade im Einzelnen

| Pfad | Was geprueft | Urteil | Befund |
|---|---|---|---|
| `index/rebuild.py` | Einstiegspunkte, Tausch und Rückfall, Protokollzeilen; seit Audit 18 nur die NL-Marke (21) | gehalten; Upgrade-Bein mit Umbau grün (`through after 4 rounds`, rund 7 s in CI) | keiner |
| `index/open.py` | Markenvergleich, NL-Automat, Fehlerpfade mit Typnamen | gehalten | keiner |
| `index/schema.py` | Feldnamen der sechs Sprachen gegen `BODY_BOOST` und `field_plan_for` | gehalten | keiner |
| `index/analyzer.py` | Ketten je Sprache, NL-Komposita nur für nl | gehalten; Grenzen stehen als HART-05-Liste im Store-Text | keiner |
| `index/stopwords.py` | Listen je Sprache, nur Konstanten | gehalten | keiner |
| `index/wordlist_nl.py` | Digest der gespeicherten Liste, Neubau bei Abweichung mit Warnzeile | gehalten | keiner |
| `index/writer.py` | Schreiben mit Sprachmenge, Heap-Grenze unverändert | gehalten | keiner |
| `store/repo.py` | Legacy-Regeln der Marken, `unreadable` in der geschlossenen Liste, SQL nur mit Platzhaltern | gehalten | keiner |
| `api/resources.py` | `field_plan_for` aus dem Verzeichnis, Füllstand mit TTL 30 s, Verdikt mit TTL 5 s | gehalten, der heiße Pfad liest gecachte Werte | keiner |
| `api/status.py` | neue Felder: Sprachen und Umbaufortschritt, nur Zahlen und Codes | gehalten | keiner |
| `query/rewrite.py` | `FieldPlan` eingefroren, Einwortregel als einzige Quelle | gehalten | keiner |
| `config.py` | neue Schalter mit Rückfall auf den Standard und Warnung mit Namen | gehalten | keiner |
| `main.py` | Freigabe-Task: Warmlauf und Freigabe teilen keinen Tick | **Befund**: nach einer Freigabe fand der nächste Tick eine stehengebliebene Anforderung | **F-23-01** |
| `worker/poller.py` | Umbau-Anbindung, Pause und Stopp | gehalten | keiner |
| `php/templates/admin.php` | Ausgabe nur über `p()`, kein `print_unescaped`; Sprachzeile | gehalten; der Text zu `cold` bleibt nach dem Fix wahr | **F-23-05** (entschieden: so lassen) |
| `php/js/admin.js` | kein `innerHTML`, kein `insertAdjacentHTML`; Referenz kommt aus PHP statt aus dem Skript (#14) | gehalten | keiner |
| `Version001300Date20260924000000` | entfernt den gemerkten Backend-Versionsschlüssel, 6 Fälle | gehalten | keiner |
| `Version001300Date20260927000000` | nur `skipped/gone`, Band 1000, eine Transaktion je Band, Rollback und Rethrow, idempotent; eine echt gelöschte Datei kommt über die leere Nutzerliste wieder als gone an | gehalten | keiner |
| `PathResolverService.php` (257caac) | Rückfall über `oc_mounts`, zwei Abfragen, Decken 200 und 20 | gehalten; Genauigkeit des LIKE-Musters | **F-23-04** |
| `QueueService.php` (257caac) | `readerOf` mit Decke 20; Ordner je Claim gecacht, im Normalfall ein Versuch | gehalten; schlimmstenfalls 20 Mount-Aufbauten je Claim und Nutzer | keiner |
| `SearchService.php` (257caac) | `readableFile` und `readableNode`, statisch, die einzige Stelle | gehalten | keiner |
| `GatewayController.php` (257caac) | eine 404 für alle drei Fälle | gehalten | keiner |
| `AdminViewService.php` (257caac) | Grund `unreadable` mit Abhilfe, Hinweis ohne Namen | gehalten | keiner |
| `FileStateService.php` (257caac) | `unreadable` in beiden Listen, gleich mit Python (`test_extract_errors.py`) | gehalten | keiner |
| `embed/engine.py` (23) | `query_may_load` konstant False, `warm_wanted` mit drei Bedingungen, `_WARMING` gegen Doppelstart | **Befund** in `release_if_idle`; Docstring von `warm()` veraltet | **F-23-01**, **F-23-02** |
| `api/search.py` (23) | `BackgroundTasks` statt loser Aufgabe, AST-Gate verlangt genau ein `add_task(warm)` | gehalten; nebenbei schließt das L-16-01 | keiner |
| `api/snippets.py` (23) | `lexical_only` aus denselben Feldern wie `/search`, kein eigener Warmlauf | gehalten | keiner |
| `tools/one_load.py` (23) | Handlerweg wie ein echter Aufrufer, `search-ms` und `warm-ms` getrennt, nur Zahlen | gehalten | keiner |
| `pyproject.toml`, `uv.lock` (23) | nur Entfernungen, keine Versionsverschiebung; tokenizers 0.23.2 und numpy 2.5.2 als direkte Kanten | gehalten | keiner |
| `backend/appinfo/info.xml` (23) | Texte zeichengleich zur Vorlage; XML-Kommentar der Freigabe | Kommentar veraltet | **F-23-03** |

### 5.2 Das Ladefenster D-08, mit Zahl

**Die erste Anfrage nach einem Neustart ist geschützt, Anfragen im Ladefenster
nicht.** Der Warmlauf startet, nachdem die erste Antwort vollständig gesendet
ist (`BackgroundTasks`). Während onnxruntime die Sitzung baut, hält es den GIL,
und eine Anfrage, die in dieses Fenster fällt, wartet am Schloss des Halters.
Sie kann den Deckel von 1,5 s reißen. Das hat der Owner am 27.09.2026
angenommen, und es ist kein Befund dieses Berichts, sondern ein benanntes
Restrisiko.

Die Zahlen, die es dazu gibt:

| Messung | Wert | Quelle |
|---|---|---|
| Warmlauf auf dem CI-Runner (amd64) | **669,6 ms** `warm-ms` | Resilience, Dispatch-Lauf 36286121016 |
| erste Suche nach Neustart, kalte Engine, CI | 973 ms über Apache, OCS, PHP-Provider und beide Hälften | Integration, Lauf 36285187617 |
| Warmlauf bis `engineState=loaded`, CI | 0 s (Auflösung ganze Sekunden) | Integration, Lauf 36285187617 |
| Laden im Request auf der Zielklasse vor dem Fix | innerMs 1505 bis 1596 gegen ceilingMs 1500 | Phase 22, V-22-01 und V-22-02 |

Auf einem CI-Runner ist das Fenster also kürzer als eine Sekunde. Auf der
Zielhardware ist es nach dem Fix **nicht gemessen**; vor dem Fix hat das Laden
mitsamt der Suche den Deckel dort um bis zu 96 ms überschritten. Wer in diesen
Bruchteil einer Sekunde nach der ersten Suche eine zweite schickt, kann eine
leere Gruppe sehen, und die Unified Search fragt beim nächsten Tastenanschlag
erneut.

### 5.3 Die Leerlauf-Freigabe (F-23-01)

Jede hybride Runde fordert einen Warmlauf an, weil `query_may_load` bei jedem
Schalterwert False antwortet, und zwar unabhängig davon, ob die Engine warm ist.
`warm_wanted` sagte dann nur deshalb nein, weil die Engine geladen war; die
Anforderung selbst blieb stehen. Nach der Freigabe fand der nächste Tick der
Freigabe-Task (30 s) diese Anforderung, fragte `warm_wanted`, bekam ja und lud
die Gewichte zurück. Die 250 bis 400 MB, die die Freigabe zurückgeben soll,
waren also höchstens eine halbe Minute frei.

Betroffen war nur, wer die Freigabe eingeschaltet hat; der ausgelieferte Wert
ist 0, und bei 0 gibt es die Freigabe-Task nicht. Der Fehler ist nicht neu: in
1.2.0 war er bei eingeschaltetem Schalter genauso da, weil `query_may_load` dort
bei jedem Wert ungleich 0 False antwortete. Phase 23 hat den Pfad angefasst, und
das Audit hat ihn deshalb gelesen.

Der Fix steht in `release_if_idle`: unter demselben Schloss wie die
Identitätsprüfung wird die Anforderung gelöscht. Die Freigabe ist der Beweis,
dass eine ganze Spanne lang niemand eingebettet hat, also ist eine Anforderung
von davor nichts mehr schuldig. Eine Suche, die nach der Freigabe abgewiesen
wird, setzt sie neu, und ein Fall hält beides fest.

### 5.4 Die Laufzeit der Suite

228,53 s für den vollen Lauf vor den Fixen, in der Größenordnung der Läufe aus
Phase 16 und 22. Keine Aussage über eine Verschlechterung.

---

## 6. Der Stand der Altbefunde

### Aus Phase 22

| Befund | Stand am 27.09.2026 | Beleg |
|---|---|---|
| V-22-01 | **geschlossen** durch 23-01 und 23-04 | `query_may_load` konstant False, Warmlauf nach der Antwort; Integration 36285187617 mit Treffer bei der ersten Suche nach Neustart |
| V-22-02 | **geschlossen** durch 23-01 | Einwortregel, Operatorregel und titleOnly auf `/snippets`; D-02-Parametrisierung in `test_snippets_endpoint.py` |
| L-22-03 bis L-22-08 | unverändert **offen, entschieden** wie in Audit 22 | kein Pfad dieser Phase berührt sie |
| `00-typwechsel.sh` ohne `OUT` | unverändert, Werkzeug gefahren und prüfsummengeschützt | Merker in der Phase-22-Liste: jede weitere Anfahrt setzt `OUT` |
| 94b-Leserfehler (L-22-07) | unverändert, Rohdatei bleibt | wer den Wert zitiert, liest 1.114 MB |
| Versionssprung 1.3.0 | **erledigt** durch 23-06 | beide info.xml auf 1.3.0, `test_lockstep_versions.py` grün |

### Aus Phase 16

| Befund | Schwere | Stand am 27.09.2026 |
|---|---|---|
| L-16-01 | LOW | **geschlossen, strukturell** durch 23-01: der Warmlauf geht über `BackgroundTasks`, und der Testclient führt die Hintergrundaufgabe jeder Antwort aus, bevor `post` zurückkehrt. Den Wettlauf zwischen loser Aufgabe und geschlossenem Tor gibt es nicht mehr |
| L-16-02 | LOW | **gilt als Verfahrensregel** und ist in dieser Phase eingehalten: die Orchestrator-Nachträge von 23-04 und 23-07 nennen jeden Lauf des Pushes |
| L-16-03 | LOW | **beobachtet, nicht wieder aufgetreten** in den Läufen, die die SUMMARYs 23-04 bis 23-07 nennen (alle success); der Merker gilt |
| L-16-04 | LOW | **behoben** in diesem Plan (Commit `ea293cc`): die Kommentare in docker.yml und release.yml behaupten nicht mehr, ein Tag-Push werde vom Pfadfilter aufgehalten, und nennen den gemessenen Fall v1.0.0 |
| L-16-05 | LOW | **gilt als Verfahrensregel** für Plan 23-09: eine neu geholte Zugangsmarke wird vor dem Setzen mit einem leeren Aufruf der Release-Route geprüft |

---

## 7. Die Erfolgskriterien der Phase

| Nr. | Kriterium | Urteil | Artefakt |
|---|---|---|---|
| 1 | Aufräumbefunde geschlossen, Abhängigkeitsliste bildet das Container-Ist ab | **erfüllt** | 23-02: Commits `4cea879`, `40919b6`; docker.yml-Schritt HART-04 in Lauf 36285187622 success auf beiden Plattformen |
| 2 | Admin liest in Doku und Store-Text, was der Sprachausbau nicht leistet | **erfüllt** | 23-03 und 23-07: vier Grenzpunkte in allen sechs Texten, zeichengleich zu `docs/language-analyzers.md`, gehalten von `test_store_metadata.py`; Owner-Abnahme "Text abgenommen" vom 27.09.2026 |
| 3 | Fremdinstallation und Upgrade 1.2.0 auf 1.3.0 inklusive Umbau Ende zu Ende grün; Audit 0 CRIT / 0 HIGH, MEDIUM behoben, LOW entschieden | **erfüllt bis auf die CI des neuen Kopfes** | HaRP deploy 36288038636 und 36289457405, probe-92d 36288064261; dieser Bericht mit 0 / 0 / MEDIUM behoben; die Läufe nach dem Push der Fixe trägt der Orchestrator nach |
| 4 | v1.3.0 eingereicht, 2x HTTP 201, Texte gate-konform und abgenommen | **erfüllt** (Nachtrag 27.09.2026, Plan 23-09) | Texte abgenommen (23-03), Gates grün (23-07); Tag `v1.3.0` auf `744d7e4`, Release 36292802211, Submission 36304007154 mit zweimal HTTP 201, Gegenprobe je App-Seite; Belegkette in Abschnitt 11 |

---

## 8. Befundliste

| ID | Schwere | Befund | Stand |
|---|---|---|---|
| F-23-01 | MEDIUM | Mit eingeschalteter Leerlauf-Freigabe lud der Container die Gewichte beim nächsten Tick der Freigabe-Task zurück, ohne dass jemand gesucht hatte. Jede hybride Runde setzt die Warmlauf-Anforderung, auch auf warmer Engine; `warm_wanted` sagte nur wegen der geladenen Engine nein, die Anforderung blieb stehen, und die Freigabe erbte sie. Vorbestehend seit dem Schalter der Phase 14, im Standard 0 ohne Wirkung | **behoben**: RED `5f9ca5f` (der Fall `test_a_release_does_not_inherit_the_warm_request_of_a_search_on_a_warm_engine` ist ohne Fix rot, mit Fix grün), Fix `0227289` in `embed/engine.py::release_if_idle`, Ledger mit datiertem Absatz; CI des neuen Kopfes steht aus |
| F-23-02 | LOW | Der Docstring von `warm()` nannte nur den Aufrufer der Phase 14 (`asyncio.to_thread`), nicht den Suchhandler mit `BackgroundTasks` | **behoben** in `9304cfc`, Docstring allein, Ledger mit datiertem Absatz |
| F-23-03 | LOW | Der XML-Kommentar über `FINDLING_EMBED_IDLE_RELEASE_SECONDS` in `backend/appinfo/info.xml` begründete den Standard 0 noch mit dem ungemessenen Preis der ersten Suche nach einer Freigabe; seit 1.3.0 zahlt keine Suche dafür | **behoben** in `b544842`, nur der Kommentar; Name, Text, Standard und Store-Texte unverändert |
| F-23-04 | LOW | Die Admin-Suche nach einem Pfad ohne Besitzer (`PathResolverService::rootsCarrying`) sucht Einhängepunkte mit dem Muster `/%/files/<Ordner>/`. Das Prozentzeichen reicht über Schrägstriche, also trifft es auch einen tieferen Mount eines anderen Nutzers, dessen eigener Ordner `files` heißt, und zählt dessen Wurzel als zweite. Folge: eine Ablehnung ("nicht gefunden") für einen auflösbaren Pfad. Nie eine falsche Datei: `carriersOfMountedPath` verwirft die Zeile | **weitergereicht** in `deferred-items.md` mit Verdikt und Zieladresse v1.4-Backlog, vom Owner am 27.09.2026 bestätigt ("Ja, v1.4-Backlog"); Umgehung für den Admin: den Besitzer vor den Pfad setzen |
| F-23-05 | LOW | Der Oberflächentext der Admin-Seite zu `cold` und `unloaded` (admin.php und sieben Sprachdateien) ist nach dem Kaltstart-Fix nicht angepasst; die Doku `docs/admin-page.md` ist präzisiert | **entschieden, so lassen**: Owner-Wort "So lassen" vom 27.09.2026; beide Sätze stimmen, `docs/admin-page.md` erklärt den Unterschied |

**Kein CRITICAL, kein HIGH, kein offener MEDIUM.**

### Punkte zur Vollstaendigkeit, die keine Befunde sind

**I-01** (aus Phase 16, unverändert): die Kontaktadresse der Enterprise-Zeile,
zur Veröffentlichung bestimmt.

**I-03:** Die Autorenadresse der Commits steht in vier Planungsdateien als
Prüfregel für den Push. Jeder Commit des Repositoriums trägt sie ohnehin.

---

## 9. Was dieser Bericht nicht sagt

Er sagt **nichts über das Ladefenster auf Zielhardware**. Die Zahl von 669,6 ms
ist ein CI-Runner. Auf der 4-GB-Box oder auf m7g.large ist der Warmlauf nach dem
Fix nicht gemessen, und die Frage, wie viele Anfragen in dieses Fenster fallen,
hängt an der Tippgeschwindigkeit fremder Nutzer. D-08 ist angenommen, nicht
vermessen.

Er sagt **nichts darüber, wie viele gone-Urteile fremde Instanzen tragen**. Der
Reparaturlauf ist mit einer gesäten Datei in CI bewiesen und mit 2500 Zeilen im
PHPUnit-Fall. Eine Instanz mit sehr vielen Team-Ordnern kann nach dem Upgrade
einen spürbar längeren ersten Scan haben; der Preis ist in D-04 angenommen.

Er sagt **nichts darüber, ob der Fix von F-23-01 in CI trägt**. Er ist lokal rot
ohne Fix und grün mit Fix, und das ist ein Einheitsfall über die Funktion. Kein
Workflow fährt die Freigabe über eine volle Spanne und liest danach den
Ladezähler; der Beweis im Container wäre eine Messanfahrt mit eingeschaltetem
Schalter.

Er sagt **nichts über die Läufe des neuen Kopfes**. Die Fixe dieses Plans sind
committet und nicht gepusht; die Laufnummern trägt der Orchestrator nach dem
Push in diesen Bericht und in die SUMMARY nach.

Er sagt **nichts über `.planning/`, `scripts/` und `testdata/` als
Dauerzustand**. Die Gegenprobe hat die Dateien dieser Phase in allen
Verzeichnissen einmal gelesen; ein Lauf ist kein Gate.

Er sagt **nichts über die Pfade der Phasen 18 bis 21 über ihre eigenen Audits
hinaus**. Der Zuschnitt D-07 prüft dort, was sich seit dem jeweiligen Audit
bewegt hat, und keine zweite Vollprüfung.

Er nennt **keine Adresse außer den zwei zur Veröffentlichung bestimmten, keine
Kennung und keinen Inhalt eines Geheimnisses**. `docs/` ist öffentlich, und
dieser Bericht ist vor dem Commit durch `test_public_artifacts.py` gelaufen.

**Die Freigabe der Haertung liegt beim Owner und nicht in diesem Bericht.** Sie
ist am Checkpoint von Task 3 des Plans 23-08 erteilt worden, siehe Abschnitt 10.

---

## 10. Abnahme

Abgenommen: 27.09.2026

Die Antwort des Owners am Checkpoint von Plan 23-08, Task 3, im Wortlaut der
Auswahl:

| Frage | Owner-Wort | Folge |
|---|---|---|
| A. Abnahme der Haertung | "Haertung abgenommen", ohne Auflagen | Plan 23-09 darf beginnen |
| B. F-23-04 | "Ja, v1.4-Backlog" | kein Fix in 1.3.0, Verdikt und Zieladresse in `deferred-items.md` bestätigt |
| C. Oberflächentext der Admin-Seite zu `cold` und `unloaded` (F-23-05) | "So lassen" | kein Umbau der acht Dateien, `docs/admin-page.md` genügt |

Keine Auflage, also kein benannter Auftrag. Offen bleibt, was Abschnitt 9 sagt:
die Läufe des neuen Kopfes nach dem Push der Fixe und Erfolgskriterium 4.

---

## 11. Die Belegkette der Abgabe 1.3.0

**Nachtrag vom 27.09.2026, aus Plan 23-09.** Das Audit oben steht auf dem Baum
von `87e41cd`; dieser Abschnitt steht auf dem Tag `v1.3.0`. Jede Zeile trägt eine
Zahl, eine Laufnummer oder einen Wortlaut. Keine ist geschätzt und keine ist aus
einem früheren Release übernommen.

Die Zeilen 1 bis 5 sind vor der Freigabe entstanden, die Zeilen 6 bis 8 nach
dem Dispatch.

| Nr. | Was | Beleg |
|---|---|---|
| 1 | **Tag** | `v1.3.0`, annotiert, Tagger street1983nk, auf `744d7e4662af67c728aa9482197990c414c92bd3`, gelesen mit `git rev-list -n 1 v1.3.0`; gepusht um 03:55:13Z |
| 2 | **Release** | Lauf **36292802211**, success, genau vier Anhänge. Im Protokoll: `appinfo/signature.json was written and is not empty`, zweimal `the release signature is 684 base64 characters` und zweimal `Verified OK` aus der Gegenprobe der Signatur gegen das Zertifikat |
| 3 | **Anhaenge** | `findling.tar.gz` **367.593 B**, `findling.tar.gz.sig` **684 B**, `findling_backend.tar.gz` **31.713 B**, `findling_backend.tar.gz.sig` **684 B**. Die Grenze des Stores liegt bei 20.971.520 B; die größere Hälfte liegt bei 1,8 Prozent davon und ist gegenüber v1.2.0 (309.484 B) um 58.109 B gewachsen |
| 4 | **Container-Abbild** | `ghcr.io/street1983nk/findling_backend:1.3.0` ist `application/vnd.oci.image.index.v1+json` mit `linux/amd64` und `linux/arm64`, dazu die zwei Herkunftsbelege als `unknown/unknown`. Anonym abgefragt mit `docker manifest inspect` gegen einen leeren Konfigurationsordner, also ohne Anmeldung, und **vor** der Einreichung |
| 5 | **Release-Notiz** | per `gh release edit v1.3.0 --notes-file` gesetzt; die erste Zeile ist die abgenommene Changelog-Zeile aus `docs/store-listing.md` Teil 6: "Files in team folders (groupfolders) that were wrongly skipped as deleted are now indexed, and the update requeues the affected entries once; thanks to budachst for the report (#14)." Danach die generierten Notizen |
| 6 | **Submission** | Lauf **36304007154**, success, gestartet um 07:43:58Z mit `tag=v1.3.0`, ohne `register`. Kein Lauf davor, kein Lauf danach |
| 7 | **HTTP-Codes** | `release findling v1.3.0: HTTP 201` und `release findling_backend v1.3.0: HTTP 201`, je im Wortlaut der Laufausgabe |
| 8 | **Gegenprobe** | Beide App-Seiten um 07:44:27Z **einzeln** abgefragt, `apps/findling` und `apps/findling_backend`, je HTTP 200: beide nennen **1.3.0** für Nextcloud 34 und 35, mit dem Download-Link auf den Anhang von `v1.3.0`. Die große Katalogdatei ist nicht als Beleg benutzt worden, sie hängt im Cache hinterher |

### Die Freigabe des Owners

Am 27.09.2026 am Checkpoint von Plan 23-09, Task 2, im Wortlaut der Auswahl:

| Frage | Owner-Wort | Folge |
|---|---|---|
| Einreichung | "Einreichen" | Dispatch von `store-submit.yml` mit `tag=v1.3.0`, zwischen Freigabe und Dispatch keine andere Handlung am Repositorium |
| Zugangsmarke | "Unveraendert" | keine 400/401-Probe, das hinterlegte Geheimnis ist benutzt worden; kein Wert steht in einer Datei, einer Laufausgabe oder diesem Bericht |
| Issue-Text | "Mit Zitatzeile" | die Frage von budachst als Zitat voran, danach der abgenommene Wortlaut aus `docs/store-listing.md` Teil 6 unverändert |
| Issue-Status | "Offen lassen" | Issue #14 ist nicht geschlossen worden |

### Die Antwort in Issue #14

Gepostet um 07:44:41Z, nach den zwei 201, als Antwort auf die letzte Frage von
budachst (issuecomment-5849413214, "I can always throw the index away and start
over, can't I?"):
https://github.com/street1983nk/nextcloud-search/issues/14#issuecomment-5853918446.
Das Issue steht weiter auf OPEN.

### Die sieben Tag-Laeufe, alle success

Release archives for the app store **36292802211**, PHP and store metadata gates
**36292802225**, Multi-arch image **36292802188**, HaRP deploy **36292802231**,
Python gates **36292802242**, Integration **36292802244**, Resilience
**36292802273**. Gestartet um 03:55:15Z, der letzte war um 04:10:15Z grün. Kein
Lauf ist wiederholt worden.

### Der Sitz des Tags

Der Tag sitzt auf `744d7e4`, der Spitze von `main`. Gegenüber `87e41cd`, dem
Kopf mit allen Befund-Fixen aus 23-08 und sechs grünen Werkbänken (Python gates
36291849649, PHP 36291849698, Integration 36291849669, Resilience 36291849646,
Multi-arch 36291849663, HaRP deploy 36291849691), tragen die zwei Commits
danach nur Planungsdateien und diesen Bericht, keine Paketdatei. Vor dem Tag ist
nichts committet worden.
