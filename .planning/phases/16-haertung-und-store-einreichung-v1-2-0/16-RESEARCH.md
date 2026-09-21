# Phase 16: Haertung und Store-Einreichung v1.2.0 - Recherche

**Recherchiert:** 2026-09-21
**Domaene:** Release-Haertung und Store-Abgabe eines Nextcloud-App-Paares (PHP-Begleit-App + ExApp), CI-Upgrade-Beweis, Text-Gates, Geheimnis-Gates, eine kleine bezahlte Messanfahrt
**Konfidenz:** HIGH fuer den Repositoriumsbefund, MEDIUM fuer den Store-Prozess, MEDIUM fuer die Kostenschaetzung der A4-Anfahrt

Die Ueberschriften stehen ohne Umlaute, weil Pruefungen und Verweise auf sie zeigen koennen. Der Fliesstext benutzt echte Umlaute. Diese Datei nennt keine Kennung, keine Adresse und keinen Passwortinhalt.

---

## Summary

Phase 16 ist keine Bauphase, sondern eine Abraeumphase mit einer Abgabe am Ende. Der Funktionsumfang von v1.2.0 steht seit Phase 14 fest, die Messzahlen seit Phase 15. Was fehlt, ist dreierlei: die vier Owner-Auflagen A1 bis A4 aus der Abnahme vom 21.09.2026, die vier aufgeschobenen Punkte DI-11-02/03/05/06 aus der letzten Einreichung, und die eigentliche Release-Mechanik (Versionsbump an drei Stellen, Migration, Upgrade-Beweis, Signieren, zweimal HTTP 201).

Der wichtigste einzelne Befund dieser Recherche: **HART-02 ist materiell bereits erfuellt und ausgeliefert.** Der BL-F01-Schlusssatz zur Connector-Synergie steht seit Commit `1c737e6` (Release 1.0.3) in allen sechs Store-Texten, dreisprachig, in beiden `info.xml` und in `docs/store-listing.md`, und er ist im Tag `v1.1.0` enthalten. Der BACKLOG-Eintrag BL-F01 sagt mit Stand 07.09.2026 noch "OFFEN NUR NOCH: der eine Schluss-Satz in den Store-Texten"; dieser Satz ist ueberholt. Was an HART-02 wirklich offen ist, ist etwas anderes und kleiner: **kein Gate haelt diesen Satz fest**, und ein Text ohne Gate ist in diesem Projekt genau die Sorte Zusage, die spaeter unbemerkt verschwindet. Dasselbe gilt fuer die Kernzahl 103,2 MB, die an neun Stellen steht und von keiner Pruefung gegen sich selbst gehalten wird.

Der zweitwichtigste Befund betrifft den Upgrade-Beweis (REL-02, Erfolgskriterium 3). Er ist heute auf den Sprung 1.0.3 auf 1.1.0 verdrahtet, und zwar nicht nur in einer Variablen: `UPGRADE_FROM_TAG` steht auf `v1.0.3`, ein Schritt behauptet ausdruecklich, die alte Haelfte trage **keinen** Navigationseintrag, und die sechste von sechs Zusicherungen nach dem Upgrade verlangt, dass genau dieser Eintrag beim Upgrade **entsteht**. Beides ist ab dem Sprung 1.1.0 auf 1.2.0 falsch, denn 1.1.0 traegt den Eintrag bereits. Ein blosses Hochsetzen der Variablen macht den Beweis rot, und zwar an einer Stelle, die nach einem Produktfehler aussieht. Die sechste Zusicherung braucht einen neuen, v1.2-eigenen sichtbaren Unterschied.

**Primaerempfehlung:** Phase 16 nach dem Muster der Phase 11 in drei Bloecke schneiden, in dieser Reihenfolge: (1) Gates und Werkzeuge ohne Box (A1, A2, DI-11-02/03/05, L-11, Dependabot-Ignoranweisung), (2) Produktarbeit und Beweis (A3, DI-11-06-Entscheid, Upgrade-Beweis auf 1.1.0 umstellen, Migration `Version001200Date...`), (3) Texte, Audit, Abgabe (Messzahl-Gleichschritt, Store-Texte, Phasenaudit, Owner-Abnahme, Tag, zweimal HTTP 201). A4 (die kleine Sprachfaelle-Anfahrt) haengt an einem Owner-Checkpoint mit Rechenblatt und laeuft parallel zu Block 1 und 2, nie waehrend der Abgabe.

---

## User Constraints

**Es gibt heute keine `16-CONTEXT.md`.** Das Verzeichnis `.planning/phases/16-haertung-und-store-einreichung-v1-2-0/` ist leer. Die folgenden Vorgaben sind deshalb nicht aus einer CONTEXT-Datei kopiert, sondern aus der Owner-Abnahme vom 21.09.2026 (`15-16-SUMMARY.md`) und aus `CLAUDE.md`. Sie haben dieselbe Bindungswirkung wie gesperrte Entscheide.

### Gesperrte Entscheide (Owner-Auflagen A1 bis A4, im Wortlaut aus 15-16-SUMMARY.md)

> - **A1: Nachfolgefassungen 92c und 99d.** Die Phase-B-Pipeline von `92b-wechsel.sh` darf occ-Fehler nicht mehr verschlucken, und `99c-filter-sortierung.sh` liest das Passwort aus der Passwortdatei statt es in der Umgebung zu erwarten. Die gefahrenen Fassungen sind eingefroren (DRIVEN_V12_FASSUNGEN); Aenderungen nur als Nachfolgefassung mit neuer Nummer.
> - **A2: Die Geheimnisregel als CI-Gate** plus Bereinigung oder ausdrueckliche Abnahme der 58 Altfunde aus den Phasen 5 bis 12 (Audit-Befund M-02).
> - **A3: M-01-Instrumentierung.** Der innere Aufruf, dem die 1,5-s-Decke gilt, wird getrennt von der Gesamtdauer ausgewiesen. Die Instrumentierung entsteht auf der Dev-Maschine; die Zahl auf Zielhardware liefert erst die naechste Box.
> - **A4: Die kleine Sprachfaelle-Anfahrt planen.** Frische ARM-Box ohne Fremdbestand, eigener Testkorpus, Rechenblatt und Deckel zur Owner-Freigabe vor dem Start. Ziel: Erfolgskriterium 4 (DI-10-02/DI-11-01) erfuellen.

Der Leitsatz der Abnahme, im Wortlaut:

> "ziel ist das wir den usern das best mögliche liefern"

Weitere gesperrte Entscheide aus derselben Sitzung:

- **Dependabot-PR #10 ist geschlossen, tantivy wird per Ignoranweisung ausgenommen.** Der Pin `tantivy==0.26.0` bewegt sich nur noch bewusst und mit Reindex-Plan (Index-Format v7 in 0.26.2 bedeutet Reindex).
- **Bewusst NICHT beauftragt:** die Top-up-A/B-Attribution. Sie bleibt notierter Messauftrag und ist kein Umfang dieser Phase.

### Claude's Discretion

- Der Schnitt der Plaene, ihre Reihenfolge und die Wellenbildung.
- Ob DI-11-02/03/05/06 abgearbeitet oder dokumentiert entschieden werden, je Punkt einzeln begruendet (HART-01 laesst beides ausdruecklich zu).
- Wie das A2-Gate technisch gebaut wird (Ausnahmeliste, Reichweite, Familienzahl).
- Wo A3 instrumentiert wird, solange der innere Aufruf getrennt ausgewiesen ist.
- Ob der Backlog-Kandidat BL-F02 Baustein 1 mitfaehrt (siehe eigener Abschnitt, Empfehlung steht dort).

### Zurueckgestellt, ausserhalb des Umfangs

- Top-up-A/B-Attribution (Owner-Entscheid 21.09.2026).
- BL-F02 Bausteine 2 und 3 (lexikalische Sprachfelder, UI-Kataloge) gehen nach v1.3.
- Q5, die Wiedervorlage des Korpus-Snapshots, faellt **nach** v1.2 an. Achtung: A4 koennte diesen Entscheid beruehren, wenn eine Anfahrt den Snapshot doch noch braucht; siehe offene Frage Q-3.

---

## Phase Requirements

| ID | Beschreibung aus REQUIREMENTS.md | Was diese Recherche dazu liefert |
|----|----------------------------------|----------------------------------|
| HART-01 | DI-11-02/03/05/06 abgearbeitet oder dokumentiert entschieden (u.a. flatternder pgsql-Ast HTTP 423: bei rot erst wiederholen) | Abschnitt "Die vier aufgeschobenen Punkte" mit Wortlaut, Kostenschaetzung und je einem Vorschlag; dazu die heute belegte Fundstelle im Mutationsschritt ohne 423-Behandlung |
| HART-02 | BL-F01-Schlusssatz zur Connector-Synergie in den Store-Texten beider Haelften (EN/DE/FR, Gate-konform) | Abschnitt "HART-02 ist ausgeliefert, das Gate fehlt": Nachweis der neun Fundstellen, Nachweis der fehlenden Pruefung, Vorschlag fuer das Gate |
| REL-02 | v1.2.0 eingereicht: Migration `Version001200Date...`, Ende-zu-Ende-Upgrade-Beweis 1.1.0 auf 1.2.0 in CI, Messzahl an drei Stellen im Gleichschritt, Store-Submission mit 2x HTTP 201 | Abschnitte "Der Upgrade-Beweis", "Die Migration", "Die Messzahl im Gleichschritt", "Der Store-Einreichungsweg" |

---

## Project Constraints (aus CLAUDE.md)

Diese Vorgaben binden jeden Plan der Phase. Sie sind aus `./CLAUDE.md` extrahiert und stehen hier, damit der Planer sie nicht zweimal suchen muss.

| Vorgabe | Wirkung auf Phase 16 |
|---|---|
| **Kurze Produkttexte (Owner, 07.09.2026)** | Store-Beschreibungen sind kurze Faktenlisten, hoechstens eine Zahl im Text, keine Messgeschichten. Der Textentwurf wird dem Owner VOR dem Release gezeigt. Store-Text reist mit dem Release und ist nicht nachtraeglich editierbar |
| **Launch-Haertung vor der Store-Abgabe (Owner, 06.09.2026)** | Vor der Abgabe wird ausgiebig getestet, nicht nur der Happy Path: Fehler- und Randpfade, Rechtegrenzen, Neustart/Upgrade/Migration, kaputte Dateien, Ressourcengrenzen, Fremdinstallation auf frischer Nextcloud, Store-Vorgaben, alle Audits erneut. Die Abgabe startet erst nach Owner-Abnahme der Haertung |
| **Nach jeder Phase Security-, Bug- und Performance-Audit (15.08.2026)** | Phase 16 bekommt `docs/audits/2026-09-phase-16/README.md` nach dem Muster der Phasen 14 und 15, VOR dem Phasenabschluss, und die Befunde ab MEDIUM werden vorher gefixt |
| **Sprache** | Code englisch, Projektkommunikation deutsch, README dreisprachig und alle drei gepflegt, keine Em-Dashes und keine En-Dashes, echte Umlaute nur in deutscher Prosa und nie in Code, Bezeichnern, URLs oder YAML |
| **Qualitaetsgates** | ruff-Vollregelsatz, `ruff format --check`, pyright basic mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, vulture `--min-confidence 80`, volle pytest-Suite. Lokal gruen VOR dem Commit |
| **Lizenz und Privatheit** | AGPL-3.0, Berechtigungsdurchgriff strikt, keine Inhalte verlassen den Server, kein Telemetrie-Phoning |
| **Versionsfenster** | `min-version 33`, `max-version 35` (HART-03, Entscheid v2-a vom 16.09.2026). Der Bump beruehrt nur die drei Versionsstellen, kein Fenster und keine Matrix |
| **Pins** | `tantivy==0.26.0` bleibt exakt (Index-Format v7). `onnxruntime==1.30.0` darf sich nach Phase 15 grundsaetzlich bewegen, aber nur mit eigenem Beweggrund |
| **Vokabular** | Das gesperrte deutsche Wort (Stamm mit "arch" und "iv") kommt in keinem oeffentlichen Artefakt vor; Ausnahme E-H2 fuer den englischen Fachausdruck in einem technischen Kommentar einer ausgelieferten Datei |

---

## Architectural Responsibility Map

| Faehigkeit | Primaere Ebene | Sekundaere Ebene | Begruendung |
|---|---|---|---|
| Store-Text und Store-Metadaten | Auslieferungsartefakt (`php/appinfo/info.xml`, `backend/appinfo/info.xml`) | Dokumentation (`docs/store-listing.md`) | Der Store liest die `info.xml` des hochgeladenen Releases; die Doku ist die Quelle, aus der beide Dateien woertlich beziehen |
| Text-Gleichschritt und Verbote | Test-Ebene (`backend/tests/test_store_metadata.py`) | keine | Es gibt kein PHP auf der Entwicklungsmaschine; ein Gate, das Quellen als Text liest, ist hier mehr wert als die perfekte Pruefung, die es nicht gibt |
| Geheimnis- und Vokabularregel | Test-Ebene (neues Gate ueber `docs/`) | Ausnahmeliste im Gate selbst | Die Regel ist heute je Plan als Suche gefahren; wer eine Datei nicht nennt, prueft sie nicht (M-02) |
| Versionsgleichschritt der drei Stellen | Test-Ebene (`test_lockstep_versions.py`) | Tag-Gate in `docker.yml` | Der taegliche Test stellt die kleine Frage, das Tag-Gate die teure |
| Upgrade-Beweis Ende zu Ende | CI (`deploy-harp.yml`, Job `deploy-harp`, amd64-Ast von stable34) | Ratsche `test_upgrade_compatibility.py` | Nur eine echte Instanz kann `occ upgrade` fahren; die Ratsche haelt die fuenf Marken ohne Instanz |
| Verwerfen der veralteten Versionsmarke | PHP-Migration (`php/lib/Migration/Version001200Date...`) | keine | Eine Migration laeuft im Wartungsmodus, ohne angemeldeten Nutzer, und fragt den Container bewusst nicht |
| Innere Aufrufdauer (A3) | PHP-Begleit-App (`ExAppService::call`) | Container-Protokoll | Die Decke `REQUEST_TIMEOUT_SECONDS = 1.5` wird in `php/lib/Service/ExAppService.php` gesetzt und dort angewandt; die Gesamtdauer der Nutzerroute gehoert einer anderen Ebene |
| Signieren und Hochladen | CI (`release.yml`, `store-submit.yml`) | keine | Die Schluessel und der Token verlassen den GitHub-Secret-Store nie |
| Sprachfall-Messung ohne Fremdbestand (A4) | frische Instanz mit eigenem Testkorpus | `98c-sprachfaelle.sh`, unveraendert | Das Skript bringt seinen Korpus selbst mit, es braucht nur eine Instanz ohne Fremdbestand |

---

## Standard Stack

Diese Phase fuegt **keine neue Laufzeitabhaengigkeit** hinzu. Der Stack ist der der Phasen 13 bis 15 und steht vollstaendig in `CLAUDE.md`. Was hier steht, ist deshalb kein Vorschlag, sondern eine Bestandsaufnahme der Werkzeuge, die die Phase benutzt.

### Kern, unveraendert

| Bestandteil | Version | Rolle in Phase 16 | Quelle |
|---|---|---|---|
| `tantivy` | exakt 0.26.0 | darf sich nicht bewegen, Index-Format v7 | `backend/pyproject.toml:13`, Gate `test_the_engine_is_held_through_its_exact_pin` |
| `onnxruntime` | 1.30.0 | darf sich mit eigenem Beweggrund bewegen | `backend/pyproject.toml:44` |
| `nc-py-api[app]` | 0.30.3 | unveraendert | `backend/pyproject.toml:10` |
| `fastapi` | 0.141.1 | unveraendert | `backend/pyproject.toml:11` |
| `sqlite-vec` | 0.1.9 | unveraendert | `backend/pyproject.toml:54` |

### Werkzeuge der Phase

| Werkzeug | Wo | Wofuer in dieser Phase |
|---|---|---|
| `uv` | lokal und CI | ruff, pyright, vulture, pytest |
| `gh` | lokal | CI-Laeufe nachsehen, Release-Dispatch, Store-Submit-Dispatch, Dependabot-Zustand |
| `openssl` | CI (`release.yml`) | Code-Signatur der Begleit-App und Release-Signatur beider Paketdateien |
| `aws` CLI plus `scripts/ops/aws_box.sh` | lokal | nur fuer A4, und nur nach Owner-Freigabe |
| `98c-sprachfaelle.sh` | `docs/measurements/2026-09-v12-messung/skripte/` | A4, unveraendert wiederverwendbar (siehe Abschnitt A4) |

**Installationsbefehl:** keiner. Wenn BL-F02 Baustein 1 mitfaehrt, kommen sechs Debian-Pakete in `backend/Dockerfile` dazu, aus derselben Quelle und mit derselben Pin-Logik wie `deu`, `eng` und `fra`: `tesseract-ocr-spa`, `-ita`, `-nld`, `-por`, `-dan`, `-est`, je `=1:4.1.0-2`.

### Alternativen, geprueft und verworfen

| Statt | Koennte man | Warum nicht |
|---|---|---|
| Migration im PHP-Teil | die Versionsmarke bei jeder Suche mitfuehren (DI-11-06) | Das ist eine Protokollaenderung an beiden Haelften auf genau dem Pfad, auf dem der Fehler von 11-11 sass. Es waere ein v1.3-Thema, siehe Vorschlag unten |
| eigene Nachfolgefassung fuer die Sprachfaelle | `98d-sprachfaelle.sh` bauen | `98c` braucht keine Aenderung: der Grund der fuenf nicht messbaren Faelle ist der Fremdbestand, nicht das Skript. Eine Nachfolgefassung ohne Anlass kostet ein Gate und gewinnt nichts |
| `krankerl` fuer die Store-Verpackung | die offizielle Verpackungshilfe benutzen | Die Strecke aus `release.yml` und `store-submit.yml` ist gebaut, gemessen und zweimal mit HTTP 201 belegt. Ein Werkzeugwechsel vor einer Abgabe ist genau die Sorte Risiko, die diese Phase nicht eingeht |

---

## Package Legitimacy Audit

Diese Phase installiert **kein neues Paket aus einem Paketverzeichnis**. Die Legitimitaetspruefung entfaellt damit nicht, sondern faellt trivial aus:

| Paket | Verzeichnis | Lage | Verfuegung |
|---|---|---|---|
| keines | - | Phase 16 aendert `backend/pyproject.toml` nicht, ausser der Owner entscheidet sich fuer eine Bewegung des onnxruntime-Pins | entfaellt |

**Wenn BL-F02 Baustein 1 mitfaehrt**, kommen sechs Debian-Pakete dazu. Sie stammen alle aus dem Quellpaket `tesseract-lang` in Debian trixie, sind `Architecture: all` (also auf arm64 und amd64 byteweise dieselben Daten), tragen die Version `1:4.1.0-2` wie die drei bereits eingebauten, und ihre Existenz ist an derselben Stelle belegt wie die von `tesseract-ocr-fra`. Das ist kein Paketverzeichnis-Risiko im Sinne der Slopcheck-Regel, sondern eine Distributionsquelle mit derselben Signaturkette wie das Basis-Abbild. Der Dockerfile-Bau prueft ausserdem nach der Installation mit `tesseract --list-langs`, dass jede Sprache wirklich da ist; dieselbe Pruefung ist fuer die sechs neuen mitzuziehen, sonst ist der Bau fuer sie stumm.

*slopcheck war fuer diese Recherche nicht ausgefuehrt, weil kein Paket aus npm, PyPI oder crates.io neu hinzukommt. Sollte die Planung doch ein neues Python-Paket aufnehmen, gilt das Tor aus der Agentenvorgabe unveraendert.*

---

## Der Befundstand, Punkt fuer Punkt

### HART-02 ist ausgeliefert, das Gate fehlt

**Der Nachweis.** Der Satz steht dreisprachig an neun Stellen:

- `php/appinfo/info.xml` Zeilen 44, 65, 86
- `backend/appinfo/info.xml` Zeilen 91, 110, 129
- `docs/store-listing.md` Zeilen 126, 148, 170 (Haelfte `findling`) und 214, 234, 254 (Haelfte `findling_backend`)

Der Commit heisst `1c737e6` ("feat: the retrieval layer sentence on both store pages, 1.0.3"). `git show v1.1.0:php/appinfo/info.xml` traegt den Satz. Der Satz ist also seit 1.0.3 im Store und war in 1.1.0 dabei. [VERIFIED: git]

**Was daran offen ist.** `grep -n "retrieval layer" backend/tests/test_store_metadata.py` findet nichts. Es gibt eine Pruefung fuer den Datenschutzabsatz aus D-12 (`test_the_privacy_paragraph_of_d_12_stands_in_all_three_languages_of_both_halves`) und keine fuer den Connector-Satz. Die Regeltabelle in `docs/store-listing.md` Zeile 27 fuehrt "Genau EIN Satz Querverweis auf den MCP Connector" als Regel, und diese Regel ist nirgends gefahren. [VERIFIED: grep]

**Der Vorschlag.** Ein Gate nach dem Muster des Datenschutzabsatzes, also drei Konstanten (EN/DE/FR) und ein Fall je Haelfte, plus ein Selbsttest gegen eine gestagte Mutation. Das ist die Form, die dieses Repositorium fuer Textzusagen benutzt, und es kostet rund 40 Zeilen. Zusaetzlich: den Stand-Absatz in `.planning/BACKLOG.md` unter BL-F01 fortschreiben, damit der naechste Leser nicht wieder an einer Aufgabe arbeitet, die seit 1.0.3 erledigt ist.

**Achtung bei der Eins.** Die Regel sagt **genau ein** Satz. Wer fuer v1.2 einen zweiten Querverweis dazuschreibt, verletzt sie. Das Gate sollte deshalb nicht nur die Anwesenheit pruefen, sondern die Anzahl.

### Die Messzahl im Gleichschritt (Erfolgskriterium 4)

**Die heutige Lage.** Zwei getrennte Zahlensysteme, die niemand gegeneinander haelt:

1. Der Messsatz aus 06-11 und 11-09, dreisprachig, in `README.en.md`, `README.md` und `README.fr.md`. Er nennt 52.111 Dokumente und eine Spitze von 1.764 MB. Gehalten von `scan_measured_sentence`, je ein Aufruf je Datei, mit einem Mutationsfall je Sprache. [VERIFIED: `backend/tests/test_store_metadata.py:294-312, 742-758, 942-957`]
2. Die Kernzahl 103,2 MB im Leerlauf, sechsmal in beiden `info.xml` und dreimal in den READMEs. **Von keinem Gate gehalten.** `grep -n "103" backend/tests/test_store_metadata.py` findet nichts. [VERIFIED: grep]

**Was das Erfolgskriterium verlangt.** "Die neue Messzahl steht im Gleichschritt an drei Stellen (README.en.md und beide info.xml)". Das ist eine neue Zusage: heute vergleicht nichts eine README-Zahl mit einer info.xml-Zahl. Das Kriterium verlangt also ein Gate, nicht nur eine Textaenderung.

**Welche Zahl.** Das ist ein Owner-Entscheid und keine Recherchefrage. Die Anfahrt der Phase 15 hat vier Kandidaten geliefert:

| Kandidat | Wert | Herkunft | Eignung fuer einen Store-Text |
|---|---|---|---|
| Grundlast vor dem Indexlauf | 103,9 MB | Marke A, 21.09.2026 | bestaetigt die alte Zahl 103,2 MB fast genau; ein Wechsel waere Kosmetik |
| Rueckkehr zur Grundlast nach einem Indexlauf | **377,5 MB** | MEM-02, Marke B minus C | das ist die neue Zusage von v1.2 und die Zahl, an der MEM-02 abgehakt ist |
| Bodensatz nach einem Zyklus | 628,0 MB | Marke C minus A | ehrlich, aber schwer erklaerbar ohne Kontext |
| Residenter Stand nach Indexlauf mit entladenem Modell | **731,9 MB** | Marke C | die Zahl, die ein Selfhoster auf einer 4-GB-Box wirklich sieht |

Die Kurztext-Regel laesst **hoechstens eine Zahl** zu, und heute steht dort bereits eine (103,2 MB). Es gibt also drei Wege, und alle drei muessen dem Owner vorgelegt werden: die Zahl ersetzen, die Zahl ergaenzen (dann ist die Kurztext-Regel zu pruefen), oder es bei 103,2 belassen und den Messsatz der READMEs auf 52.137 nachziehen. Das ist ein blockierender Checkpoint und nicht Claude's Discretion.

**Eine Falle in den Zahlen.** Der v1.2-Lauf hat die **anon-Spitze eines Volllaufs nicht neu gemessen**. Die 1.764 MB im Messsatz stammen weiter aus der v1.1-Anfahrt. Wer den Messsatz auf 52.137 Dokumente nachzieht, ohne die Spitze mitzunehmen, mischt zwei Laeufe in einem Satz. Die saubere Form ist die, die `docs/performance.md` seit 14-11 benutzt: eine alte Zahl bleibt gueltig fuer die Bedingungen, unter denen sie entstand, und bekommt einen datierten Nachtrag daneben.

### Der Upgrade-Beweis (Erfolgskriterium 3): drei Stellen, die von 1.0.3 erzaehlen

`.github/workflows/deploy-harp.yml` fuehrt den Beweis in sieben Schritten, "Store upgrade 0" bis "Store upgrade 5", auf dem Ast `stable34` und `ubuntu-24.04`. Drei Stellen sind auf den Sprung 1.0.3 auf 1.1.0 verdrahtet:

1. **`UPGRADE_FROM_TAG: v1.0.3`**, Zeile 91, mit einem Begruendungsabsatz darueber. Wird auf `v1.1.0` gesetzt. [VERIFIED: Datei]
2. **Die Vorbedingung im Schritt "Store upgrade 1"**: der Lauf prueft, dass die alte Begleit-App **keinen** `<navigations>`-Block traegt, und bricht ab, wenn doch. Belegt: `git show v1.0.3:php/appinfo/info.xml` hat null Treffer auf `<navigations>`, `git show v1.1.0:...` hat einen. Diese Pruefung geht mit `v1.1.0` als Ausgangspunkt **rot**. [VERIFIED: git + Workflow-Zeilen 2455-2465]
3. **Zusicherung 6 von 6 im Schritt "Store upgrade 5"**: "the navigation entry, and this one HAS to have changed". Der Schritt verlangt, dass `.navigation.findling` vorher abwesend und nachher anwesend ist, und meldet sonst einen Fehler mit dem Text, die Aenderung aus Plan 09-06 muesse auf einer bestehenden Installation ankommen. Auch das geht mit 1.1.0 als Ausgangspunkt rot, weil der Eintrag vorher schon da ist. [VERIFIED: Workflow-Zeilen 3205-3215]

**Was Zusicherung 6 stattdessen misst.** Sie braucht einen sichtbaren Unterschied, den v1.2 gegenueber v1.1 macht und der auf einer bestehenden Installation ankommen muss. Zwei Kandidaten aus dem Funktionsumfang dieses Milestones:

- **Die Filter- und Sortierzeile der Ergebnisseite (Phase 13).** Sie lebt in `php/templates/search.php` und im `PageController`; ein Zustandsabbild vor und nach dem Upgrade koennte sie am gerenderten Formular ablesen.
- **Der sechste Engine-Zustand auf der Admin-Seite (Phase 14, `unloaded`).** Er lebt in `AdminViewService.php` und `templates/admin.php`. Ein Abbild kann pruefen, dass die Seite den Satz nach dem Upgrade fuehrt und vorher nicht.

Die zweite Variante ist die guenstigere, weil das Zustandsabbild die Admin-Seite ohnehin abfragt und das Abbild `upgrade-before.json` und `upgrade-after.json` bereits schreibt.

**Was der Beweis sonst kann.** Der Rest traegt: Zusicherung 1 bis 5 (gleiche Treffer, gleiche fuenf Marken nach D-04, gleiche Dokumentzahlen, kein Reindex-Banner, keine `start_rebuild_on_drift`-Zeile) sind versionsunabhaengig formuliert. Der Versionsschritt in "Store upgrade 4" hat seit 11-11 zwei Zweige und nimmt den richtigen. Die Kommentare nennen allerdings noch 11-11 und 1.1.0 als Zukunft; sie gehoeren nachgezogen, sonst liest der naechste Mensch eine Anleitung fuer ein Release von vorgestern.

**Die Ratsche daneben.** `backend/tests/test_upgrade_compatibility.py` haelt fuenf Marken gegen `GOLD_V1_0_3`. Die Werte sind Literale (`schema_version "1"`, `index_version "1"`, `analyzer_version "1"`, das tantivy-Banner) und haben sich seit 1.0.3 **nicht bewegt**, auch nicht durch die Filter- und Sortierarbeit der Phase 13. Fuer den Sprung 1.1.0 auf 1.2.0 gelten dieselben Werte. Was zu tun ist, ist deshalb klein: der Name der Konstanten und die Meldungstexte sagen "1.0.x" und sollten "1.0.x und 1.1.x" sagen. Inhaltlich aendert sich nichts. [VERIFIED: `test_upgrade_compatibility.py:42-58`]

### Die Migration Version001200Date...

Das Muster steht vollstaendig in `php/lib/Migration/Version001100Date20260911000000.php`, und sein Klassenkommentar sagt selbst, dass er die Datei ist, die jemand liest, wenn er die naechste schreibt. Die Regeln, die er festhaelt:

- **Der Dateiname und der Klassenname muessen zeichengleich sein.** Nextcloud laedt Migrationen ueber den Dateinamen und baut die gleichnamige Klasse; bei einer Abweichung wird die Migration still nie ausgefuehrt, ohne Fehler an irgendeiner Stelle.
- **Der Wert wird verworfen und nicht geraten.** `ownVersion()` hineinzuschreiben waere die eine Aenderung, die die Zusage leert: eine Instanz, deren Container wirklich eine Minor zurueckliegt, bekaeme Einigkeit bescheinigt.
- **Der Lauf ist wiederholbar.** Ein fehlender Schluessel ist ein `no-op` mit einer Meldung, kein Wurf. Nextcloud kann eine Migration nach einem gescheiterten Upgrade wiederholen.
- **Die Migration fragt den Container nicht.** Sie laeuft im Wartungsmodus, ohne angemeldeten Nutzer, und moeglicherweise waehrend AppAPI den Container neu startet.
- **Sie sitzt in `postSchemaChange`**, weil sie Daten und keine Tabelle anfasst.

Dazu gehoert eine PHPUnit-Datei nach dem Muster von `php/tests/Unit/Version001100Date20260911000000Test.php` (sechs Faelle in der Vorlage).

**Der Datumsteil.** `Version001200Date20260911000000` waere falsch datiert. Der Name traegt `Version001200Date<JJJJMMTThhmmss>`; das Datum ist der Tag, an dem die Datei entsteht.

**Die Nebenwirkung, die 11-11 teuer gemacht hat.** Zwei neue PHP-Dateien bewegen die Zaehlung. `PHP_FILES_TODAY` steht heute auf 64 und `PHP_TREE_HASH_TODAY` daneben; beide werden im selben Commit nachgezogen, sonst ist das Messgate rot. Siehe eigener Abschnitt unter "Common Pitfalls".

### Die vier aufgeschobenen Punkte (HART-01)

Alle vier stehen im Wortlaut in `.planning/milestones/v1.1-phases/11-haertung-und-store-einreichung-v1-1/deferred-items.md`.

**DI-11-02, eine leere Antwort ohne Protokollspur.** Eine einzelne Anfrage von 80 bekam in Laststufe 8 der v1.1-Anfahrt eine leere Ergebnisgruppe, ohne dass irgendwo ein Abbruch entstand. Die Vermutung ist DI-07-03. Plan 11-13 hat den Fall inzwischen mit einem eigenen Zustand versehen, `SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED`, der statt einer leeren Liste einen Satz zurueckgibt. Die v1.1-Box trug diesen Stand nicht.

*Lage nach Phase 15:* Die v1.2-Anfahrt ist **mit** diesem Stand gefahren, und die vier regressiven Laststufen sind je mit "behoben" entschieden, gegengerechnet an `cURL error 28` im Nextcloud-Protokoll (null im Lastfenster). Die Frage von DI-11-02 ist damit faktisch beantwortet: der Zustand ist gebaut, die Stufen sind gruen, kein Leertreffer ist mehr ein verschluckter Abbruch. *Vorschlag: dokumentiert entschieden, mit Verweis auf Bericht Abschnitt 5 und die Gegenrechnung. Kosten: eine halbe Stunde Schreibarbeit, keine Box.*

**DI-11-03, der Zaehler unterscheidet leer nicht von abgebrochen.** `EmptyResultGroup` in `scripts/ops/search_load.py` zaehlt jede Antwort unter `--min-hits` als Fehlschlag, gleich ob abgebrochen oder schlicht ohne Treffer. Der Eintrag begruendet ausfuehrlich, warum das Werkzeug die beiden Ursachen aus seiner Sicht **nicht** trennen kann: die OCS-Route antwortet in beiden Faellen mit HTTP 200 und einer Ergebnisgruppe ohne Containerteil. Die tragfaehige Fassung nennt stattdessen die Begriffe ohne Treffer und braucht dafuer den Bestand, gegen den sie laeuft.

*Lage nach Phase 15:* Den Bestand gibt es jetzt. `98c-sprachfaelle.sh` benutzt `73-bestand-sonde.py`, die im Container ueber `ranked_sides` den ungedeckelten Bestand je Begriff liest. Das ist genau die fehlende Zutat. *Vorschlag: abarbeiten, als Nachfolgefassung des Lastwerkzeugs mit einer Vorlaufsonde, die die treffer-losen Begriffe vor dem Lauf benennt und in der Rohdatei ausweist. Kosten: ein Plan ohne Box. Alternative, wenn der Termin druecken sollte: dokumentiert entschieden mit dem Satz, dass die Trennung heute an der Route und nicht am Werkzeug scheitert.*

**DI-11-05, der flatternde pgsql-Ast.** Der Job `index-search-e2e (pgsql)` fiel am 11.09.2026 einmal mit `curl: (22) The requested URL returned error: 423` nach "revision 8 written" aus, im Schritt "Overwrite it eight times while the container is working". 423 ist Locked, also die WebDAV-Sperre von Nextcloud. Die Wiederholung war gruen; ein roter Lauf auf dreizehn. Der Merker lautet: bei rot ist die **erste Handlung eine Wiederholung** und keine Fehlersuche im Erzeugnis.

*Die Fundstelle, heute nachgesehen:* `.github/workflows/integration.yml` Zeilen 2032 bis 2050. Die acht Schreibvorgaenge laufen als schlichte Schleife mit `curl -sfS -u ... -T ...`, ohne jede Behandlung von 423, gefolgt von einem neunten, dem `final`-Schreibvorgang. Es gibt **keine** Warteschleife. [VERIFIED: Datei]

*Vorschlag: abarbeiten, und zwar minimal.* Eine Hilfsfunktion `schreibe_revision`, die den Rueckgabecode liest, bei 423 kurz wartet und hoechstens dreimal wiederholt, und die bei jedem anderen Code sofort scheitert. Das ist genau der Fix, den der Eintrag selbst vorschlaegt ("eine Warteschleife auf 423 statt eines blinden neunten Schreibvorgangs"). Wichtig ist die Enge: eine allgemeine Wiederholung ueber alle Codes wuerde echte Fehler verschlucken. Der Zeitpunkt ist der Anfang der Phase und nicht die Woche der Abgabe, denn der Eintrag warnt ausdruecklich davor, unmittelbar vor dem Release-Tag an der Integrationsstrecke zu bauen.

**DI-11-06, die Suche kennt die Version des Containers nur vom Hoerensagen.** Zwischen einem App-Update und dem ersten Oeffnen der Einstellungsseite hat die Suche keine Versionsmarke und damit kein Drift-Urteil. Der Weg, der es schliesst, ist die Version in der Antwort mitzufuehren, die die Suche ohnehin holt. Das ist eine Protokollaenderung an beiden Haelften.

*Vorschlag: dokumentiert entschieden, mit einer Zieladresse nach v1.2.* Die Begruendung von 11-11 gilt unveraendert und wiegt heute sogar schwerer: die Aenderung sitzt auf dem Suchpfad, sie beruehrt beide Haelften, und sie kaeme in derselben Phase, die eine Abgabe traegt. Der Merker aus dem Klassenkommentar der Migration bleibt dagegen scharf: **solange die Marke so gepflegt wird, braucht jeder Minor-Sprung eine Migration.** Genau das ist REL-02. Wenn der Owner die Protokollaenderung will, gehoert sie in einen eigenen Milestone und schliesst dann auch den Migrationszwang.

### A1: die Nachfolgefassungen 92c und 99d

**Die Einfrierregel.** `backend/tests/test_measurement_scripts.py` fuehrt seit 15-15 die Tabelle `DRIVEN_V12_FASSUNGEN` mit sechs Eintraegen, je Dateiname, sha256 und Bytezahl:

`92b-wechsel.sh`, `94b-grundlast-rueckkehr.sh`, `95b-wiederaufwaermen.sh`, `97-cron-vorpruefung.sh`, `98c-sprachfaelle.sh`, `99c-filter-sortierung.sh`.

Der Waechter wird beim ersten geaenderten Byte rot. Eine Aenderung ist also nur als **neue Datei mit neuer Nummer** moeglich. Das Muster dafuer ist bereits zweimal gefahren (98 auf 98b auf 98c) und hat eine eigene Pruefung: `test_the_successor_points_at_the_driven_fassung_and_lives_beside_it` verlangt, dass die Nachfolgefassung im Kopf auf die gefahrene Fassung zeigt und neben ihr liegt. [VERIFIED: Datei]

**92c.** Zu beheben ist L-03: die Phase-B-Pipeline von `92b-wechsel.sh` verschluckt Fehler des `occ`-Aufrufs; Lauf 1 der Anfahrt endete mit Rueckgabewert 0, ohne dass die Registrierung stattgefunden hatte. In einer Shell-Pipeline liefert der letzte Befehl den Rueckgabewert; `sh` kennt kein `pipefail` (die Skripte tragen `#!/bin/sh`). Die tragfaehige Form ist deshalb, den `occ`-Aufruf aus der Pipeline zu nehmen, in eine temporaere Datei zu schreiben, den Rueckgabewert sofort zu pruefen und erst danach zu filtern.

**99d.** Zu beheben ist L-04: `99c-filter-sortierung.sh` liest das Passwort nicht aus der Passwortdatei, sondern erwartet es in der Umgebung. Das ist kein Sicherheitsdefekt (die Umgebung ist die erlaubte Form nach V14), sondern ein Bruch der Einheitlichkeit. Das Vorbild steht in den uebrigen Werkzeugen desselben Laufverzeichnisses.

**Was A1 NICHT ist.** A1 verlangt keine Messung. Die Nachfolgefassungen werden gebaut und gegen boxlose Tests gruen gefahren; ihre Wirkung auf einer Box misst erst die naechste Anfahrt. Das steht als Punkt 11 in Abschnitt 10 des Berichts und gehoert in die Summary, damit niemand die Fassungen spaeter fuer nachgemessen haelt.

### A2: die Geheimnisregel als CI-Gate, plus die 58 Altfunde

**Die Luecke, in einem Satz aus dem Audit:** die Geheimnisregel ist in diesem Projekt nirgends als Gate gefahren, sondern je Plan als Suche ueber die Dateien, die der Plan selbst nennt. Wer eine Datei nicht nennt, prueft sie nicht.

**Die acht Familien der Gegenprobe**, aus dem Auditbericht Abschnitt 3, als Vorlage fuer das Gate:

| Familie | Was gesucht wird |
|---|---|
| `pem-privatschluessel` | `-----BEGIN ... PRIVATE KEY-----` |
| `ssh-schluesselmaterial` | `ssh-rsa`/`ssh-ed25519`/`ssh-dss` gefolgt von base64 |
| `aws-zugangskennung` | die acht Praefixe mit zwoelf und mehr Folgezeichen |
| `aws-ressourcenkennung` | die uebrigen Praefixe ausser `i-` und `vol-` |
| `rechnername-der-box` | Anbieter-Rechnernamen und interne Namensformen |
| `schluesselwort-mit-wert` | `pass`, `secret`, `token`, `api_key`, `credential`, `pwd` unmittelbar vor `:` oder `=` und einem Wert |
| `ipv6-adresse` | vier bis acht Hexgruppen mit Doppelpunkten |
| `base64-block-ab-40` | zusammenhaengende base64-Zeichen ab Laenge 40 |

Dazu das Muster der Umsetzung (`i-`, `vol-`, IPv4-Form), das im Audit ebenfalls ueber alle Dateien gefahren wurde.

**Der Bau, empfohlene Form.** Ein Testmodul nach dem Muster der bestehenden Textgates dieses Repositoriums:

- eine Anti-Leerlauf-Klausel vorn (das Gate geht rot, wenn es weniger Dateien sieht als eine Untergrenze), sonst ist ein Gate ueber ein verschobenes Verzeichnis gruen ohne Aussage;
- Selbsttests gegen gestagte Muster je Familie, sonst kann ein geloeschter Rumpf null Befunde ueber null Dateien melden und gesund aussehen;
- eine **benannte Ausnahmeliste** mit je einem Grund je Eintrag, nicht mit einem Sammelsatz.

**Die 58 Altfunde: der Entscheid, der dem Owner gehoert.** Sie stehen in 18 Dateien unter `docs/` und stammen aus den Phasen 5 bis 12. Zwei Wege:

1. **Ausnahmeliste, ohne Bereinigung.** Begruendung: alle bezeichneten Ressourcen sind abgebaut und gegen die Anbieter-API als abgebaut zurueckgelesen, die Adressen sind dynamisch vergeben und laengst neu vergeben, und eine nachtraeglich redigierte Rohdatei ist kein Beleg mehr. Die Historie behaelt die Werte ohnehin. Kosten: gering.
2. **Bereinigung der redigierbaren Dateien, Ausnahmeliste nur fuer Rohdaten.** Begruendung: `docs/` ist oeffentlich lesbar und der Owner hat die Regel gesetzt. Kosten: hoeher, und jede geaenderte Rohdatei ist ein Beleg weniger.

**Die harte Randbedingung, die fuer beide Wege gilt:** die alten Commit-Kennungen duerfen nicht umgeschrieben werden. Die Historie bleibt, wie sie ist. Eine Bereinigung ist ein neuer Commit obendrauf und nie ein Umschreiben. [Owner-Regel vom 25.08.2026 aus dem Projektgedaechtnis, hier als bindend behandelt]

**Der Geschwisterbefund L-10.** Das gesperrte Wort steht 116 mal in 17 Dateien unter `docs/`, rund 50 davon in deutschen Formen und damit von der Regel getroffen. Auch diese Regel ist nirgends gefahren, und genau deshalb ist sie 116 mal unbemerkt geblieben. Das Vokabular-Gate existiert bereits, aber nur fuer die Store-Texte und `docs/store-listing.md`. Die Ausdehnung auf `docs/` ist dieselbe Bauaufgabe wie A2 und gehoert in denselben Plan; sie hat dieselbe Ausnahmefrage (Rohdaten der bisherigen Anfahrten bleiben ausgenommen) und dieselbe Entscheidungslage.

### A3: die Instrumentierung des inneren Aufrufs

**Was M-01 sagt.** Drei von vier Auspraegungen der ersten Suche lagen ueber 1,5 s, und eine davon (Schalter 0, warmer Cache, 1.613 ms) hat mit der Entladung nichts zu tun. Die Rohdateien weisen je die Dauer der **ganzen** Anfrage auf der Nutzerroute aus. Die Methodik-Korrektur in `docs/performance.md` haelt seit dem 10.09.2026 fest, dass die Decke von 1.501 ms dem **inneren** Containeraufruf gilt. Ein Abbruch ist in keiner der vier Auspraegungen eingetreten (`code=200` viermal, 26 Treffer dreimal).

**Wo die Decke wirklich sitzt.** `php/lib/Service/ExAppService.php`:

- `REQUEST_TIMEOUT_SECONDS = 1.5` (Zeile 95), die Decke der Unified-Search-Route
- `PAGE_REQUEST_TIMEOUT_SECONDS = 1.5` (Zeile 122), die Decke der eigenen Ergebnisseite
- `ADMIN_REQUEST_TIMEOUT_SECONDS = 2.0` (Zeile 140)
- `private function call(...)` (Zeile 724) ist die eine Stelle, an der der Aufruf gegen den Container abgesetzt wird, und sie bekommt `secondsLeft` und `ceilingSeconds` hereingereicht
- `exAppRequest` wird in `proxyRequest` (um Zeile 658) gerufen

[VERIFIED: Datei]

**Die Empfehlung: instrumentieren auf der PHP-Seite, nicht im Python-Paket.** Der innere Aufruf, dem die Decke gilt, ist der Aufruf **von PHP nach Container**, und nur PHP kennt seine Dauer vollstaendig (Proxy, HaRP, Container, Rueckweg). Eine Messung im Container misst die Handler-Dauer und laesst den Proxyweg weg, also genau den Teil, der die Decke reissen laesst, ohne dass der Container etwas davon merkt. Der Bau ist klein: `hrtime(true)` vor und nach dem Aufruf in `call()`, eine Protokollzeile mit Pfad und Dauer in Millisekunden.

**Drei Randbedingungen, die der Plan tragen muss:**

1. **Die Protokollzeile darf nicht bei jeder Suche auf `info` laufen.** Die Unified Search fragt bei jedem Tastenanschlag; eine Zeile je Anschlag ist Rauschen und keine Messung. Entweder `debug`, oder eine Zeile nur oberhalb einer Schwelle. Die zweite Form ist die brauchbarere, weil sie genau die Faelle protokolliert, die M-01 beschreibt.
2. **Kein Nutzerinhalt in die Zeile.** Kein Suchbegriff, kein Dateiname, keine Kennung. Das Protokoll einer Nextcloud ist kein privater Ort.
3. **Der Baumhash zieht mit.** Jede Aenderung an `php/**/*.php` bewegt `PHP_TREE_HASH_TODAY`; `PHP_FILES_TODAY` nur, wenn eine Datei dazukommt oder verschwindet.

**Was A3 nicht liefert und auch nicht liefern soll.** Die Zahl auf Zielhardware. Die Auflage sagt das selbst: die Instrumentierung entsteht auf der Dev-Maschine, die Zahl liefert erst die naechste Box. Wenn A4 als Anfahrt gefahren wird, kann sie die Zahl nebenbei mitnehmen; das ist ein Posten im Rechenblatt und keine Selbstverstaendlichkeit.

### A4: die kleine Sprachfaelle-Anfahrt

**Das Ziel.** Erfolgskriterium 4 der Phase 15, in seiner ersten Haelfte: die Sprachfall-Messung laeuft **ohne** den Fremdbestand. Der Grund, warum sie es in Phase 15 nicht tat, steht unumwunden im Audit: der Korpus-Snapshot **ist** der Fremdbestand. Fuenf von zehn Faellen hiessen deshalb "nicht messbar", weil die eigene Datei ausserhalb der 64 Rechecks lag, verduennt durch rund 52.000 Fremddokumente mit denselben Woertern.

**Die gute Nachricht: es braucht kein neues Skript.** `98c-sprachfaelle.sh` bringt seinen Korpus selbst mit. Aus seinem Kopf, woertlich: "das eigene Konto, dessen Heimat nichts als testdata/corpus haelt, die 39 Dateien ueber WebDAV, weil das der Weg eines Nutzers ist, der fertige OCR-Durchlauf vor jedem Urteil, und alle zehn Faelle auch nach einem roten." Der Testkorpus ist also `testdata/corpus`, **39 Dateien, zusammen rund 500 KB**. Die in der Aufgabenstellung genannten "26 Dateien" sind nicht der Korpus, sondern der alte Antwortdeckel 26 aus DI-11-01, der mit der neuen Messgroesse weggefallen ist. [VERIFIED: Skriptkopf, `ls testdata/corpus | wc -l`]

Das Skript ist eingefroren, und das ist hier kein Hindernis: **eine gefahrene Fassung darf gefahren werden, nur nicht geaendert.** Eine Nachfolgefassung 98d braucht es nur, wenn sich im Lauf ein Defekt zeigt.

**Die eigentliche Frage ist nicht das Skript, sondern die Instanz.** Das Runbook ist auf den Wiederaufbau aus dem Korpus-Snapshot gebaut (Bloecke 6, 7, 9). Ohne Snapshot gibt es keine Nextcloud auf der Box, und eine frische Installation ist ein eigener Posten, den das Rechenblatt heute nicht kennt.

**Drei Wege, und die Entscheidung gehoert dem Owner.**

| Weg | Was er ist | Kosten | Was er beweist | Was er nicht beweist |
|---|---|---|---|---|
| **A: CI-Ast auf `ubuntu-24.04-arm`** | den Job `index-search-e2e` der `integration.yml` um einen arm64-Ast erweitern; er faehrt dieselben zehn Faelle schon heute auf amd64 gegen eine frische Instanz ohne Fremdbestand | **0 USD**, ein Plan ohne Box | die zehn Faelle auf ARM64, ohne Fremdbestand, wiederholbar und dauerhaft | keine echte Nextcloud mit AppAPI und HaRP, keine harte Speichergrenze, keine m7g-Maschine |
| **B: kleine bezahlte Anfahrt** | frische Box, frische Nextcloud, `98c` unveraendert | Schaetzung unten | genau das, was die Auflage woertlich verlangt | nichts dauerhaft: die naechste Frage kostet wieder |
| **C: beides** | A als dauerhaftes Gate, B einmal als Beleg | Summe | beides | - |

Weg A ist erwaehnenswert, weil das Repositorium den ARM-Runner bereits an drei Stellen benutzt (`docker.yml`, `python.yml`, `measure.yml`, und seit 11-04 auch `deploy-harp.yml`) und Phase 14 ihn ausdruecklich als `role: target` gefahren hat. Der Vorbehalt aus 14-02 gilt aber weiter und muss dem Owner mit vorgelegt werden: der Runner ist eine Vier-Kern-Maschine derselben Flotte und **keine m7g.large**. Fuer eine Aussage ueber Suchqualitaet (und genau das sind die Sprachfaelle) ist das unerheblich; fuer eine Aussage ueber Speicher und Zeit waere es entscheidend.

**Der Rechenblatt-Entwurf fuer Weg B.** Gebaut nach dem Muster aus `docs/runbook-messbox.md` Abschnitt 2, mit der dortigen Regel: die Ist-Werte der Phase 15 sind die **Untergrenze je Posten**, die Sitzungszeit wird gesondert aufgeschlagen, und ein Planwert nimmt keine Verbesserung vorweg.

| Posten | Planwert | Herleitung |
|---|---|---|
| Handaufbau (Security Group, Schluessel, Instanz, harte Grenze, Neustart) | 1 h 00 min | Ist der Phase 15 fuer die Bloecke 1 bis 9 war rund 0 h 40 min, darin steckte aber der Snapshot-Teil; ohne ihn kleiner, mit Aufschlag fuer die Erstfassung des neuen Weges |
| **NEU: frische Nextcloud aufsetzen** (statt Volume aus dem Snapshot) | 1 h 30 min | in keinem bisherigen Rechenblatt enthalten; das Runbook kennt diesen Weg nicht, also Erstvollzug |
| Abbildwechsel auf den v1.2-Stand, beziehungsweise Erstregistrierung | 0 h 45 min | Ist der Phase 15 war 0 h 32 min in drei Laeufen |
| Korpus hochladen, Indexierung samt OCR abwarten | 0 h 30 min | 39 kleine Dateien; das Skript wartet selbst auf den leeren Arbeitsvorrat, `FRIST`, `RUNDEN` und `RUNDENFRIST` behalten ihre Vorgaben |
| Sprachfall-Messung, zehn Faelle | 0 h 30 min | Ist der Phase 15 war 0 h 07 min bei bereits laufender Instanz |
| **Optional: A3-Zahl auf Zielhardware** | 0 h 30 min | nur wenn A3 vor der Anfahrt fertig ist; sonst faellt der Posten weg |
| Abbau und Endmessungen | 0 h 30 min | Ist der Phase 15 war 0 h 05 min Box-Zeit bis zum Anhalten |
| **Summe der Planwerte** | **5 h 15 min** | Addition |

Rechenweg nach Abschnitt 2.5 des Runbooks, mit demselben Zuschlag von 15 Prozent fuer Erstvollzug und Unvorhergesehenes:

```
5,25 h x 1,15 = 6,04 h, aufgerundet 7 h
7 h x 0,115841 USD/h = 0,8109 USD, aufgerundet 0,90 USD
```

**Vorschlag: Deckel 7 Stunden und 0,90 USD netto.** [ASSUMED: die Planwerte der drei neuen Posten sind Schaetzungen ohne Messung, wie Annahme A8 der Phase-15-Recherche; der Stundensatz 0,115841 USD ist gepinnt und am Anfahrtstag ein zweites Mal ueber `scripts/ops/aws_box.sh prices` zu lesen]

Zwei Hinweise, die ins Rechenblatt gehoeren:

- **Der Stundensatz enthaelt 100 GB gp3 (0,013041 USD je Stunde).** Eine Box fuer 39 Dateien braucht keine 100 GB. Wer den Datentraeger kleiner schneidet, senkt den Satz; wer ihn aus Bequemlichkeit gleich laesst, sagt das im Rechenblatt statt es stillschweigend zu tun.
- **Die Snapshotkosten gehoeren nicht in diesen Deckel.** Sie laufen ohnehin weiter (2,79 bis 2,99 USD je Monat) und sind Q5, nicht A4.

**Und die Lehre aus dem Erstvollzug, die hier gilt:** jeder Block stempelt beim Betreten und beim Verlassen eine Zeile mit UTC-Zeitstempel in seine Rohdatei. In Phase 15 hat das kein Block getan, und deshalb stehen die ersten beiden Posten dort bis heute in einer gemeinsamen Zeile.

### L-11 und die anderen offenen LOW-Befunde

| ID | Befund | Vorschlag |
|---|---|---|
| L-03 | `92b` verschluckt occ-Fehler | wird von A1 abgedeckt (92c) |
| L-04 | `99c` liest die Passwortdatei nicht | wird von A1 abgedeckt (99d) |
| L-05 | `94b` und `95b` fuehren `admin` als Vorgabebenutzer, der Korpus gehoert `lasttest` | in dieselbe Nachfolgefassungs-Welle wie A1, oder dokumentiert weitergereicht |
| L-06 | `94b` ruft `sudo "$SAMPLER"` direkt, die Datei steht mit `100644` im Index | dieselbe Welle; der Behelf auf der Box war `chmod +x` |
| L-07 | `aws_box.sh cmd_destroy` loescht das Schluesselpaar nicht mit | klein und ohne Box behebbar; `scripts/ops/aws_box.sh` ist nicht eingefroren |
| L-08 | drei Werkzeuge waehrend der bezahlten Zeit geaendert, der Waechter friert den Stand danach ein | benannte Asymmetrie, bleibt; kein Fix, nur der Verweis auf die Pruefsummen davor in `15-15-SUMMARY.md` |
| L-09 | Erfolgskriterium 4 nicht erfuellt | wird von A4 abgedeckt |
| L-10 | das gesperrte Wort 116 mal unter `docs/` | wird von A2 abgedeckt, wenn das Gate beide Regeln traegt |
| L-11 | `test_with_the_release_on_a_cold_engine_gets_exactly_one_run` ist zeitempfindlich | siehe unten |

**Zu L-11.** Der Fall wartet mit `ran.wait(BLOCKED_WARM_SECONDS)` auf das Eintreffen eines Hintergrundlaufs; `BLOCKED_WARM_SECONDS` ist 5,0 und traegt im Kommentar zwei Aufgaben zugleich: lang genug, dass ein wartender Handler in das Budget darunter faellt, und kurz genug, dass ein frueh endender Fall nichts kostet. Genau diese Doppelrolle ist der Defekt. Fuer die Frage "hat der Lauf stattgefunden" ist eine lange Frist gratis, denn sie kostet nur, wenn der Fall ohnehin scheitert; fuer die Frage "hat der Handler gewartet" ist eine kurze Frist die Aussage. [VERIFIED: `backend/tests/test_search_endpoint.py:597-604, 713-731`]

*Vorschlag: eine zweite Konstante, etwa `ARRIVAL_SECONDS = 30.0`, ausschliesslich fuer die Warte-auf-Ankunft-Faelle; `BLOCKED_WARM_SECONDS` bleibt bei 5,0 fuer die Faelle, die eine Obergrenze behaupten. Das ist eine Zeile plus drei Aufrufstellen und macht kein Gate weicher.*

**Ein dritter Flake-Stamm, der im Audit nicht steht.** Der Lauf 35470079862 vom 19.09.2026 fiel im Auftrag `search-parity (stable34, 8.2)` am Schritt "Log every account in and keep its session" aus, mit der Meldung, die Anmeldung des Kontos `minimal` sei verweigert worden. Er ist beidseitig von gruenen Laeufen eingerahmt und in `.planning/phases/15-messphase-eine-box-anfahrt/deferred-items.md` als Einzelfall eingeordnet, mit dem Hinweis, dass derselbe Schritt am 11.09.2026 schon einmal einen Befund trug (`parity-login-probe-404`). [VERIFIED: `gh run view 35470079862 --log-failed`]

Das Bild ist damit: **drei verschiedene Flake-Familien in der CI dieses Repositoriums** (423 im Mutationsschritt, die zeitempfindliche Single-Flight-Zusage, die verweigerte Anmeldung in der Suchparitaet), und sie sind nirgends zusammen erfasst. Fuer eine Phase, die mit einem Tag-Lauf endet, bei dem sieben Workflows gleichzeitig gruen sein muessen, ist das der praktisch wichtigste Haertungsbefund. Vorschlag: ein Abschnitt "Flake-Register" im Phasenaudit, mit je Stamm der letzten roten Laufnummer, der Gegenprobe und dem Verdikt.

### Der Dependabot-Zustand: eine Ignoranweisung, die nicht im Repositorium steht

Der Owner hat am 21.09.2026 entschieden, tantivy per Ignoranweisung auszunehmen. Der Zustand heute:

- PR #10 ist **geschlossen** (verifiziert).
- Dependabot hat auf den Kommentarbefehl geantwortet: "OK, I won't notify you about tantivy again, unless you unignore it." Diese Ignoranweisung lebt im Zustand des Dienstes und nicht in einer Datei.
- Dependabot hat im selben Zug gewarnt: "This pull request was built based on a group rule. Closing it will not ignore any of these versions in future pull requests. To ignore these dependencies, configure ignore rules in dependabot.yml."
- `.github/dependabot.yml` enthaelt **kein** `ignore:` und das Wort `tantivy` kommt darin nicht vor (verifiziert).

[VERIFIED: `gh pr view 10 --comments`, `grep tantivy .github/dependabot.yml`]

Die Gates haben inzwischen bewiesen, dass sie greifen: der Lauf 35556667085 ist rot geworden mit der Meldung `tantivy_version ist 'tantivy v0.26.2, index_format v7' statt '0.26.0'` und zusaetzlich am Pin-Gate. Das ist der gewuenschte Ausgang. Trotzdem ist eine Ignoranweisung, die nur im Zustand eines fremden Dienstes lebt, eine Regel ohne Datei. *Vorschlag: einen `ignore:`-Eintrag fuer `tantivy` in `.github/dependabot.yml`, mit dem Grund in einem Kommentar daneben (Index-Format v7, Bewegung nur mit Reindex-Plan).*

### Der Store-Einreichungsweg, gegen die aktuelle Store-Doku geprueft

Die Projektregel verlangt, die Prozessdetails vor **jeder** Einreichung gegen die dann aktuelle Store-Doku zu pruefen. Ergebnis der Pruefung am 21.09.2026:

| Punkt | Store-Doku | Was `store-submit.yml` tut | Urteil |
|---|---|---|---|
| Release anlegen | `POST /api/v1/apps/releases` | genau das | unveraendert [CITED: nextcloudappstore.readthedocs.io/en/latest/api/restapi.html] |
| Pflichtfelder Release | `download` (https, tar.gz, hoechstens 20 MB), `signature`, optional `nightly` | `download` und `signature`, kein `nightly` | unveraendert; die groessere Haelfte ist 282 KB, die Grenze also weit weg |
| App registrieren | `POST /api/v1/apps` mit `certificate`, `signature`, **`is_enterprise_only`** | sendet `certificate` und `signature`, kein `is_enterprise_only` | nur fuer die Erstregistrierung relevant, also nicht fuer v1.2.0. Der Schritt laeuft ohnehin nur hinter dem Eingabeschalter `register` [CITED: dieselbe Seite] |
| Anmeldung | `Authorization: Token TOKEN` oder Basic | `Authorization: Token ${APPSTORE_TOKEN}` | unveraendert |
| Antwortcodes Release | 200, 201, 400, 401, 403 | akzeptiert 200 und 201, scheitert sonst | unveraendert |
| Signatur | `openssl dgst -sha512 -sign` ueber die Paketdatei | `release.yml` signiert genau so, `store-submit.yml` uebergibt die `.sig`-Datei des Release-Assets | unveraendert |
| **Token erneuern** | `POST /api/v1/token/new` regeneriert den Kontotoken | nicht abgebildet, der Token ist ein GitHub-Secret | siehe unten [CITED: dieselbe Seite] |

**Die Token-Rotation.** Die Aufgabenstellung nennt sie als offenen Owner-Punkt: der Store-Token stand in einem Box-Snapshot, und seine Rotation ist noch nicht vollzogen. Der Weg dafuer ist zweiteilig und beide Teile gehoeren dem Owner:

1. Auf `apps.nextcloud.com/account/token` einen neuen Token holen, beziehungsweise ueber `POST /api/v1/token/new` erneuern. Der alte wird dabei ungueltig.
2. `gh secret set APPSTORE_TOKEN --repo street1983nk/nextcloud-search` mit dem neuen Wert.

**Die Reihenfolge ist bindend und gehoert in den Plan:** die Rotation findet **vor** dem Dispatch von `store-submit.yml` statt, aber **nach** dem Tag und dem gruenen `release.yml`-Lauf. Wer zwischen Rotation und Einreichung noch etwas anderes macht, riskiert einen Fehlschlag an einer Stelle, an der der Fehlschlag teuer ist (die Assets liegen dann bereits am Tag, aber der Store kennt das Release nicht). Der Beleg, dass die Rotation gewirkt hat, ist derselbe wie der Beleg der Einreichung: zweimal HTTP 201.

**Was die Belegkette aus 11-11 wiederverwendet werden kann**, eins zu eins:

| Was | Wie belegt |
|---|---|
| Tag | `git rev-list -n 1 v1.2.0` nennt den Commit, auf den der Tag laut Freigabe gehoert |
| Release | Laufnummer von `release.yml`, genau vier Assets |
| Assets | vier Dateien mit Bytezahl: beide `.tar.gz` und beide `.tar.gz.sig` |
| Container-Abbild | der Manifestindex in der Registry wird **vor** der Einreichung geprueft und nicht angenommen: `application/vnd.oci.image.index.v1+json` mit `linux/amd64` und `linux/arm64`, anonym abgefragt |
| Submission | Laufnummer von `store-submit.yml`, success |
| HTTP-Codes | `release findling v1.2.0: HTTP 201` und `release findling_backend v1.2.0: HTTP 201` |
| Gegenprobe | beide App-Seiten im Store nennen 1.2.0. Achtung: die grosse `apps.json` haengt im Cache hinterher und ist kein Gegenbeweis |

### Die Store-Bilder: ein Befund, der in keinem Kriterium steht

Die drei Bilder in `store/media/` stammen vom 07.09.2026, also aus der v1.0.0-Zeit (`b5aed7c`, `160a289`). Seitdem hat das Produkt drei sichtbare Aenderungen bekommen: die eigene Ergebnisseite mit Navigationseintrag (Phase 9), die Filter- und Sortierzeile (Phase 13) und den sechsten Engine-Zustand auf der Admin-Seite (Phase 14). `screenshot-admin.png` zeigt die Admin-Seite in ihrem damaligen Stand.

Dazu kommt eine offene Zusage in `store/media/README.md`: die Live-Bestaetigung der drei Bildadressen traegt den Vermerk, dass sie **nach** dem naechsten Stand auf `main` je Datei zu wiederholen und die Tabelle nachzuziehen sei. Die Tabelle nennt bis heute die Groessen der abgeloesten Dateien. [VERIFIED: Datei plus `git log -- store/media/`]

*Vorschlag: dem Owner als Entscheid vorlegen, nicht selbst entscheiden.* Neue Bilder sind aufwendig (Wegwerf-Stack, eigener erzeugter Bestand, Playwright, Sichtprobe) und sie sind kein Erfolgskriterium. Sie sind aber genau das, was der Leitsatz der Abnahme meint. Das Nachziehen der Groessentabelle ist dagegen klein und sollte in jedem Fall passieren.

### BL-F02 Baustein 1: die sechs OCR-Sprachen

**Der Stand.** `backend/Dockerfile` installiert heute `tesseract-ocr` plus `-deu`, `-eng`, `-fra`, `-osd`, je mit `=1:4.1.0-2`, und prueft nach der Installation mit `tesseract --list-langs`, dass `deu`, `eng` und `fra` da sind. `backend/src/findling/config.py` fuehrt `OCR_DEFAULT_LANGUAGES = ("deu", "eng", "fra")` und `OCR_LANGUAGE_ALLOWLIST = frozenset({"deu", "eng", "fra"})`; `FINDLING_OCR_LANGUAGES` wird gegen die Liste geprueft und faellt bei unbekannten Werten mit einer Warnung zurueck. `backend/tests/test_ocr_french.py` liest den Dockerfile als Text und ist das Vorbild fuer die Pruefung. [VERIFIED: Dateien]

**Der Umfang von Baustein 1**, ehrlich aufgezaehlt:

1. Sechs apt-Zeilen (`spa`, `ita`, `nld`, `por`, `dan`, `est`), je mit Pin, plus sechs `--list-langs`-Pruefungen, plus die Lizenzdateien nach dem Muster der bestehenden
2. `OCR_LANGUAGE_ALLOWLIST` von drei auf neun Eintraege; `OCR_DEFAULT_LANGUAGES` bleibt bei dreien (ein Standard mit neun Sprachen macht jede OCR-Seite langsamer)
3. `THIRD-PARTY.md` nachziehen
4. Tests nach dem Muster von `test_ocr_french.py`
5. **Der Store-Text.** Alle sechs Texte nennen heute "German, English, French" als OCR-Sprachen. Neun Sprachen heisst neun Sprachen im Text, dreisprachig, in zwei Dateien und in `docs/store-listing.md`
6. `PACKAGE_TREE_HASH_TODAY` nachziehen, weil `config.py` unter `backend/src/findling` liegt
7. Die Abbildgroesse prueft `docker.yml`; sechs Sprachpakete wachsen das Abbild

**Die Nebenbedingung, die der Backlog setzt:** nur NACH der Phase-15-Messanfahrt (erfuellt, die Anfahrt ist abgebaut) und nur **ohne Terminrisiko** fuer die Einreichung; sonst Folgerelease.

**Und die Zusage, die daran haengt:** die EU-Outreach-Entwuerfe an drei Stellen nennen OCR fuer die jeweilige Sprache als "naechstes Release". Solange die Mails nicht versandt sind, bindet die Zusage nichts. Ob sie versandt sind, weiss diese Recherche nicht.

*Empfehlung: mitnehmen, aber als letzte Welle vor dem Textblock und mit einem ausdruecklichen Abbruchpfad.* Punkt 5 ist der Grund: die Store-Texte sind ohnehin in dieser Phase offen (Messzahl, Connector-Gate), und ein zweiter Durchgang durch dieselben sechs Texte in einem Folgerelease waere derselbe Aufwand noch einmal. Wenn der Bau ins Rutschen kommt, faellt Baustein 1 heraus und die Texte bleiben bei drei Sprachen. Diese Entscheidung gehoert **vor** den Textblock und nicht danach.

---

## Architecture Patterns

### Der Phasenaufbau, aus Phase 11 gelernt

Phase 11 hatte dreizehn Plaene und diese Reihenfolge. Sie hat funktioniert, und die Gruende stehen in den Summaries:

```
11-01  Vorentscheide, Owner-Checkpoint vor dem Bau
11-02  Werkzeug-Fassung (Lastwerkzeug), ohne Box
11-03  Werkzeug-Fassung (Sprachfaelle), ohne Box
11-04  CI-Strecke erweitern (Store-Install auf zwei Runnern)
11-05  Textarbeit, Owner-Abnahme der franzoesischen Fassung
11-06  die kleine bezahlte Anfahrt, mit eigenem Deckel
11-07  Upgrade-Block in deploy-harp.yml
11-08  Kataloge giessen plus vier Katalog-Gates
11-09  Textentwurf fuer das Release, Owner-Abnahme
11-10  Phasenaudit
11-11  Versionsbump, Migration, Tag, Abgabe
11-12  Abbau der Box
11-13  der eine Produktfix, der aus 11-01 kam
```

**Was daran wiederverwendbar ist:**

- **Vorentscheide zuerst, in einem eigenen Plan mit Checkpoint.** Phase 16 hat mindestens vier Entscheide, die vor dem Bau fallen muessen: welche Messzahl in die Texte kommt, wie die 58 Altfunde behandelt werden, welchen Weg A4 geht, und ob BL-F02 Baustein 1 mitfaehrt. Ein `16-VORENTSCHEIDE.md` nach dem Muster von `11-VORENTSCHEIDE.md` ist die richtige Form.
- **Werkzeugarbeit vor Messarbeit.** Die Bauordnung der ROADMAP sagt es fuer 12 vor 15, und es gilt hier fuer A1 vor A4: ein waehrend der Anfahrt korrigiertes Skript entwertet seine eigene Messung.
- **Der Textentwurf ist ein eigener Plan mit Owner-Abnahme.** Store-Text reist mit dem Release und ist danach nicht editierbar.
- **Das Audit kommt vor dem Versionsbump**, nicht danach. In 11-11 stand der Auditbericht mit `critical: 0, high: 0` als Vorbedingung im Abhaengigkeitsgraphen.
- **Die Abgabe ist ein Plan und keine Zeile am Ende eines anderen Plans.**

**Was die Lehre war und in Phase 16 anders laufen sollte:**

- **Ein Beweis, der zum ersten Mal wirklich greift, findet Fehler.** In 11-11 lief der Upgrade-Block fuenf Releases lang in `ERROR_UP_TO_DATE` und deckte mit dem ersten echten Minor-Sprung drei Befunde auf, einer davon im Produkt. Phase 16 faehrt den zweiten echten Minor-Sprung, diesmal mit einer geaenderten Ausgangsversion und einer neu zu bauenden Zusicherung 6. Der Plan sollte **Zeit fuer Befunde einplanen**, nicht nur fuer den Bump.
- **Die erste Handlung bei einem roten Ast ist die Wiederholung**, nicht die Fehlersuche. Erst wenn sie Zeile fuer Zeile dasselbe liefert, ist es ein Befund. Das gilt fuer DI-11-05 ausdruecklich und fuer die anderen beiden Flake-Staemme sinngemaess.
- **Eine Workflow-Aenderung wird vor dem Push gegen einen lokal nachgebauten Zustand gefahren.** In 11-07 waren das alle drei Server-Zweige plus zwei gebaute Fehlerfaelle.
- **Der Tag sitzt auf dem Commit, der die Befunde schon enthaelt**, nicht auf dem Bump-Commit. In 11-11 war das ein Owner-Entscheid und hat den Release gerettet.

### Muster 1: das Textgate dieses Repositoriums

Jedes Textgate hier hat dieselbe Form, und ein neues sollte sie haben:

```python
# Quelle der Form: backend/tests/test_store_metadata.py

# 1. Konstanten fuer Pfade und Erwartungen, oben, mit Begruendung
# 2. eine scan_*-Funktion, die eine Liste von Befunden liefert und nie wirft
# 3. eine Anti-Leerlauf-Klausel: die Dateien existieren, bevor ihr Inhalt beurteilt wird
# 4. ein Fall je Datei, der die Befundliste gegen [] haelt
# 5. Selbsttests gegen gestagte Muster: ein sauberes Muster liefert [],
#    ein mutiertes liefert einen Befund
```

Der vierte und fuenfte Punkt sind nicht Zierat: ohne den Selbsttest kann ein Gate, dessen Rumpf geloescht wurde, null Befunde ueber null Dateien melden und gesund aussehen. Genau dieser Satz steht in den Kopfkommentaren mehrerer dieser Dateien.

### Muster 2: die Nachfolgefassung eines gefahrenen Messwerkzeugs

```
# Quelle: docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh, Kopf

1. Die gefahrene Fassung bleibt byteweise, wo sie ist. Sie ist Teil des Belegs
   ihres Laufs.
2. Die Nachfolgefassung bekommt eine neue Nummer und liegt neben ihr.
3. Ihr Kopf nennt die Vorgaengerin mit vollem Pfad und sagt, was sich aendert
   und was ausdruecklich gleich bleibt.
4. Der Waechter in backend/tests/test_measurement_scripts.py bekommt seinen
   Eintrag: test_the_successor_points_at_the_driven_fassung_and_lives_beside_it.
5. Vorgaben, die die Vergleichbarkeit tragen (Fristen, Rundenzahlen), bleiben
   unveraendert, und das steht im Kopf.
```

### Muster 3: die drei Versionsstellen

```
php/appinfo/info.xml       <version>1.2.0</version>
backend/appinfo/info.xml   <version>1.2.0</version>
backend/appinfo/info.xml   <image-tag>1.2.0</image-tag>
```

Alle drei in **einem** Commit. `backend/tests/test_lockstep_versions.py` stellt die kleine Frage taeglich (sind die drei gleich, und ist jede ein Semver ohne fuehrende Nullen); `.github/workflows/docker.yml` stellt die teure Frage am Tag (stimmen sie mit dem Tag ueberein). Das Gate nennt bewusst **keine** Zahl, damit es nicht die erste Datei ist, die jemand beim Bump bearbeitet. [VERIFIED: `test_lockstep_versions.py`, Kopfkommentar]

### Anti-Muster, die vermieden gehoeren

- **Eine ersetzte Zahl ohne Nachtrag.** `docs/performance.md` fuehrt seit 14-11 die Regel: eine alte Zahl bleibt gueltig fuer die Bedingungen, unter denen sie entstand, und bekommt einen datierten Nachtrag daneben. Eine ersetzte Erwartung liesse nicht mehr erkennen, woran ein Werkzeug gescheitert ist.
- **Ein Beweis, der seine Ausgangsversion nur in einer Variablen fuehrt.** Genau daran haengt heute die halbe Arbeit an `deploy-harp.yml`: zwei weitere Stellen sagen "1.0.3" in Prosa und in einer Zusicherung.
- **Eine Ignoranweisung, die nur im Zustand eines fremden Dienstes lebt.** Siehe Dependabot.
- **Ein Gate mit einer Ausnahmeliste ohne Gruende.** Ein Gate mit benannter Ausnahmeliste ist ehrlicher als eine Regel ohne Gate; eine Ausnahmeliste ohne Gruende ist eine stille Abschaltung.
- **Eine Messung waehrend der Abgabewoche.** A4 gehoert nach vorn oder parallel, nie zwischen Tag und Einreichung.

---

## Dont Hand-Roll

| Aufgabe | Nicht selbst bauen | Stattdessen | Warum |
|---|---|---|---|
| Paketdatei signieren und hochladen | eine lokale Signatur- und Upload-Prozedur | `release.yml` plus `store-submit.yml` | Die Schluessel und der Token verlassen den GitHub-Secret-Store nie; der Store holt genau das Asset, das der Signaturschritt erzeugt hat, es gibt keinen zweiten Bau |
| Versionsgleichschritt pruefen | eine neue Pruefung | `test_lockstep_versions.py`, sie ist da | Ein zweites Gate mit einer eingetragenen Zahl waere die erste Datei, die jemand beim Bump bearbeitet |
| Upgrade-Verhalten pruefen | einen eigenen Testaufbau | den Block in `deploy-harp.yml` umstellen | Er faehrt eine echte Nextcloud mit `occ upgrade` auf einem Datentraeger mit echtem Index; ein Testdoppel wuerde die Migration nie wirklich ausfuehren |
| Kennungen und Adressen suchen | ad-hoc-greps je Plan | ein Gate mit Ausnahmeliste | Genau die Praxis der Einzel-Greps ist M-02: wer eine Datei nicht nennt, prueft sie nicht |
| Sprachfall-Messung | ein neues Skript | `98c-sprachfaelle.sh` unveraendert fahren | Es bringt seinen Korpus, seine zehn Zusicherungen und seine Bestandssonde mit; der Defekt lag am Fremdbestand und nicht am Skript |
| Baumhash nachrechnen | eine eigene Rezeptur | die Rezeptur in `test_measurement_scripts.py` | Eine verbesserte Rezeptur liefert einen anderen Hash und nimmt die Vergleichbarkeit gegen alle frueheren Laeufe mit |
| Migration schreiben | von vorn anfangen | `Version001100Date20260911000000.php` als Vorlage lesen | Ihr Klassenkommentar ist ausdruecklich fuer den geschrieben, der die naechste schreibt |

**Kernsatz.** Diese Phase gewinnt nichts durch neue Mechanik. Fast alles, was sie braucht, ist schon einmal gebaut, gefahren und belegt worden; der Fehler, den sie machen kann, ist, eine funktionierende Strecke kurz vor der Abgabe umzubauen.

---

## Common Pitfalls

### Pitfall 1: der Baumhash wird vergessen

**Was schiefgeht:** Ein Commit aendert `backend/src/findling/**/*.py` oder `php/**/*.php`, und `backend/tests/test_measurement_scripts.py` wird rot.

**Warum:** Vier Konstanten halten den heutigen Baum: `PACKAGE_FILES`, `PACKAGE_TREE_HASH_TODAY`, `PHP_FILES_TODAY`, `PHP_TREE_HASH_TODAY`. Die historischen Zwillinge (`PACKAGE_TREE_HASH`, `PHP_TREE_HASH`, `PHP_FILES`) gehoeren den Rohdaten alter Laeufe und bleiben unberuehrt. Ein Gate prueft sogar ausdruecklich, dass die beiden Zahlen **verschieden** sind, weil die zweite sonst ihren Daseinsgrund verloren haette.

**Wie vermeiden:** `backend/tests/test_measurement_scripts.py` steht in der Dateiliste **jedes** Plans, der Produktcode anfasst. In Phase 14 hat der Plan die Datei viermal in Folge nicht gefuehrt, und viermal musste der Hash als Abweichung nachgezogen werden.

**Fruehwarnzeichen:** Ein Plan, der `files_modified` ohne diese Datei fuehrt und gleichzeitig eine `.py` unter `src/findling` oder eine `.php` nennt.

**Die Zahlen von heute** (Stand `8aed3c0`): `PHP_FILES_TODAY = 64`, `PACKAGE_FILES = 54`. Die Migration plus ihr PHPUnit-Test heben `PHP_FILES_TODAY` auf 66.

### Pitfall 2: der Upgrade-Beweis geht rot an der Navigation

**Was schiefgeht:** `UPGRADE_FROM_TAG` wird auf `v1.1.0` gesetzt, sonst nichts, und der Lauf scheitert zweimal: einmal vor dem Upgrade mit "the v1.0.3 companion already declares a navigation entry", einmal danach an Zusicherung 6.

**Warum:** Beide Stellen behaupten eine Eigenschaft von 1.0.3 und nicht eine Eigenschaft von "der vorigen Version".

**Wie vermeiden:** Drei Stellen in einem Commit aendern, und Zusicherung 6 auf einen v1.2-eigenen sichtbaren Unterschied umstellen.

### Pitfall 3: die Store-Texte laufen auseinander

**Was schiefgeht:** Eine Aenderung erreicht die englische Fassung und nicht die deutsche, oder eine Haelfte und nicht beide. Auf der Store-Seite sieht das nur der, der sie in der betroffenen Sprache liest.

**Wie vermeiden:** Jede Textaenderung geht durch `docs/store-listing.md` (dort stehen alle sechs Texte nebeneinander) und von dort woertlich in beide `info.xml`. `test_store_metadata.py` prueft mechanisch, was mechanisch pruefbar ist: Laengengrenze 128 fuer `name` und `summary`, keine leeren Elemente, Sprachcodes `de` und `fr` (nie `de_DE`), je Elementart jede Sprache genau einmal, keine Em-Dashes, keine En-Dashes, keine Emojis, Bildgroesse unter 2 MiB, https-Adressen mit hinterlegter Datei.

**Was das Gate NICHT prueft:** ob eine Uebersetzung gut ist, ob sie dasselbe sagt, ob der Text idiomatisch ist. Das ist eine Lesung und passiert am Owner-Checkpoint.

**Und die Regel, die leicht bricht:** keine Backticks und keine Tabellen in einer Store-Beschreibung, weil der Store Markdown anders rendert als das Repositorium. Das ist eine Projektregel und steht nicht in der XSD.

### Pitfall 4: ein leeres Element beendet den Upload mit einem Serverfehler

Das ist laut Kopfkommentar von `test_store_metadata.py` das Teuerste, was dieses Projekt ueber den Store weiss, und es wurde am Schwesterprojekt gemessen: ein leeres `description`-Element faellt nicht mit einer Meldung durch die Validierung, sondern beendet den Upload in einem Serverfehler.

### Pitfall 5: die 423-Wiederholung wird zu breit gebaut

**Was schiefgeht:** Eine Wiederholung ueber alle Fehlercodes verschluckt echte Fehler. Der Mutationsschritt existiert, um zu beweisen, dass der Container einer Datei folgt, die sich unter ihm aendert; ein Schritt, der jeden Fehlschlag wegwartet, beweist nichts mehr.

**Wie vermeiden:** Nur 423, mit Obergrenze, und jeder andere Code scheitert sofort und laut.

### Pitfall 6: die Kurztext-Regel wird von der Messzahl gebrochen

Die Regel sagt **hoechstens eine Zahl** im Store-Text. Heute steht dort eine (103,2 MB). Wer eine zweite dazustellt, bricht die Regel des Owners vom 07.09.2026, und der Text ist nach der Einreichung nicht mehr editierbar.

### Pitfall 7: Fixe, die nicht nachgemessen sind, werden fuer nachgemessen gehalten

Kein Werkzeug-Fix der Phase-15-Anfahrt ist in seiner Wirkung auf einer Box nachgemessen worden, und die Nachfolgefassungen 92c und 99d aus A1 werden es auch nicht sein, solange keine Anfahrt sie faehrt. Der Satz gehoert in die Summary, nicht nur in den Kopf des Skripts.

### Pitfall 8: die Abgabe faellt in einen Flake

Sieben Tag-Laeufe muessen gleichzeitig gruen sein. Drei bekannte Flake-Staemme stehen dagegen. Die Gegenmassnahme ist kein neuer Code, sondern eine Reihenfolge: **die drei Staemme werden im ersten Block der Phase behandelt**, nicht in der Abgabewoche, und der Merker "erst wiederholen, dann suchen" steht im Plan der Abgabe, nicht nur in den Notizen.

---

## Code Examples

### Der Kopf der Store-Einreichung, wie er heute laeuft

```yaml
# Quelle: .github/workflows/store-submit.yml
# Zwei Schritte, zwei Endpunkte:
#   POST /api/v1/apps           registriert eine App-Kennung (nur Erstabgabe)
#   POST /api/v1/apps/releases  registriert ein Release
submit() {
  app="$1"
  base="https://github.com/${GITHUB_REPOSITORY}/releases/download/${TAG}"
  signature=$(curl -sfL "${base}/${app}.tar.gz.sig")
  test -n "${signature}" || { echo "${app}: the signature asset of ${TAG} is missing"; exit 1; }
  code=$(jq -n --arg download "${base}/${app}.tar.gz" --arg signature "${signature}" \
           '{download: $download, signature: $signature}' \
         | curl -s -o "${RUNNER_TEMP}/${app}.release.json" -w '%{http_code}' \
             -X POST 'https://apps.nextcloud.com/api/v1/apps/releases' \
             -H "Authorization: Token ${APPSTORE_TOKEN}" \
             -H 'Content-Type: application/json' \
             --data @-)
  echo "release ${app} ${TAG}: HTTP ${code}"
  case "${code}" in
    200|201) echo "${app} ${TAG} is in the store" ;;
    *) echo "${app}: the submission failed"; exit 1 ;;
  esac
}
submit findling
submit findling_backend
```

Der Dispatch dazu, von der Entwicklungsmaschine:

```bash
gh workflow run "Store submission" -f tag=v1.2.0
```

Der Schalter `register` bleibt aus. Beide Kennungen sind seit 1.0.0 registriert, und ein zweiter Registrierungsversuch antwortet mit 400.

### Die Stelle, an der DI-11-05 sitzt

```bash
# Quelle: .github/workflows/integration.yml, Zeilen 2032 bis 2050
# Heute: acht blinde Schreibvorgaenge plus ein neunter, ohne jede 423-Behandlung.
for round in $(seq 1 "${MUTATION_ROUNDS}"); do
  revision "${MUTATION_TERM_BEFORE}" "${round}" "${{ runner.temp }}/mutating-${round}.txt"
  curl -sfS -u "${OWNER_USER}:${OWNER_PASS}" \
    -T "${{ runner.temp }}/mutating-${round}.txt" \
    "http://localhost:8080/remote.php/dav/files/${OWNER_USER}/${MUTATION_FILE}"
  echo "revision ${round} written"
done
```

Die enge Form des Fixes, als Skizze: den Schreibvorgang in eine Funktion ziehen, `-w '%{http_code}'` statt `-f` lesen, bei `423` warten und hoechstens dreimal wiederholen, bei jedem anderen Code ausser `2xx` sofort und laut scheitern, und die Zahl der Wiederholungen in die Ausgabe schreiben, damit ein Lauf hinterher sagen kann, ob die Sperre ueberhaupt aufgetreten ist.

### Die Stelle, an der A3 sitzt

```php
// Quelle: php/lib/Service/ExAppService.php
public const REQUEST_TIMEOUT_SECONDS = 1.5;        // Zeile 95
public const PAGE_REQUEST_TIMEOUT_SECONDS = 1.5;   // Zeile 122
private const ADMIN_REQUEST_TIMEOUT_SECONDS = 2.0; // Zeile 140

private function call(
    string $path,
    string $userId,
    array $body,
    float $secondsLeft = self::REQUEST_TIMEOUT_SECONDS,
    float $ceilingSeconds = self::REQUEST_TIMEOUT_SECONDS
): ?array {                                        // Zeile 724
    // hier sitzt der eine Aufruf, dem die Decke gilt
}
```

### Das Muster des Messzahl-Gates, das gebaut werden muss

```python
# Vorbild: scan_measured_sentence in backend/tests/test_store_metadata.py
# Was heute fehlt: ein Vergleich zwischen der Zahl in README.en.md und der
# Zahl in beiden info.xml. Heute halten drei Faelle je eine README gegen einen
# festgeschriebenen Satz, und die info.xml stehen ausserhalb dieser Pruefung.
#
# Die Form, die das Erfolgskriterium verlangt:
#   1. die Zahl wird EINMAL als Konstante festgelegt
#   2. drei Faelle halten sie gegen README.en.md, php/appinfo/info.xml und
#      backend/appinfo/info.xml
#   3. ein Mutationsfall je Stelle beweist, dass der Fall rot werden kann
```

---

## Environment Availability

Geprueft am 21.09.2026 auf der Entwicklungsmaschine (Windows 11, Git Bash).

| Abhaengigkeit | Gebraucht fuer | Verfuegbar | Version | Ausweichweg |
|---|---|---|---|---|
| `git` | alles | ja | 2.54.0 | - |
| `gh` | CI-Laeufe, Dispatch, Dependabot-Zustand | ja | 2.92.0 | - |
| `uv` | die fuenf Python-Gates | ja | 0.11.7 | - |
| `python` | Testlauf | ja | 3.13.1 | - |
| `openssl` | Signaturpruefung von Hand | ja | 3.5.6 | die Signatur entsteht ohnehin in CI |
| `jq` | Antworten lesen | ja | 1.8.1 | - |
| `curl` | Gegenproben gegen den Store | ja | 8.19.0 | - |
| `docker` | lokale Probeinstallation | ja | 29.5.2 | - |
| `aws` CLI | nur A4, Weg B | ja | 2.36.39 | - |
| `php` | PHP-Lint, PHPUnit | **nein** | - | CI (`php.yml`); die Textgates lesen PHP-Quellen als Text, und der Grund dafuer steht in `docs/testing.md` |
| `composer` | PHP-Abhaengigkeiten | **nein** | - | CI |
| POSIX-Shell fuer die Messwerkzeuge | A1, die Nachfolgefassungen | **nein** auf dieser Maschine | - | vier `skipif` in `test_measurement_scripts.py`; die Waechter pruefen Text, Form und Pruefsumme statt Ausfuehrung. Die Nachfolgefassungen 92c und 99d lassen sich hier bauen und statisch pruefen, aber **nicht ausfuehren** |

**Fehlende Abhaengigkeiten ohne Ausweichweg:** keine.

**Fehlende Abhaengigkeiten mit Ausweichweg:** PHP und Composer (CI), POSIX-Shell (statische Waechter). Der zweite Punkt ist fuer A1 planungsrelevant: die Fassungen 92c und 99d werden in dieser Phase **nicht laufen**, und ihr Abnahmekriterium kann deshalb nur Form, Pruefsumme und statische Analyse sein.

---

## Security Domain

### Zutreffende ASVS-Kategorien

| Kategorie | Trifft zu | Standardmassnahme in dieser Phase |
|---|---|---|
| V2 Authentifizierung | ja | Passwoerter nie als Argument (Gate `test_the_script_of_this_run_puts_no_password_on_a_command_line`); erlaubt ist `--password-env` mit dem **Namen** einer Variablen. A1/99d bringt die Passwortdatei als zweite erlaubte Form |
| V3 Sitzungen | nein | Diese Phase legt keine Sitzung an. Ausnahme: A4 meldet sich an einer Testinstanz an, mit denselben Regeln wie Phase 15 |
| V4 Zugriffskontrolle | ja, bei A4 | SSH auf genau eine Adresse mit Praefixlaenge 32, nie aufgeweicht; die eigene oeffentliche Adresse kann ueber Nacht neu vergeben werden, dann wird die alte Regel entzogen und die neue gesetzt |
| V5 Eingabepruefung | teilweise | Kein neuer Eingang. Die Migration liest einen Konfigurationswert und schreibt keinen |
| V6 Kryptographie | ja | `openssl dgst -sha512 -sign` fuer beide Signaturen, unveraendert; die Schluessel leben ausschliesslich im GitHub-Secret-Store |
| V7 Protokolle und was oeffentlich wird | **ja, der Schwerpunkt** | A2 ist genau diese Kategorie: `docs/` ist oeffentlich lesbar, und die Regel ist nirgends als Gate gefahren. A3 kommt dazu: eine neue Protokollzeile in einer ausgelieferten App darf keinen Nutzerinhalt tragen |
| V12 Ressourcengrenzen | nein | Diese Phase veraendert keine Grenze des Erzeugnisses |
| V14 Konfiguration | ja | Jede Anmeldung kommt aus der Umgebung oder aus einer Passwortdatei, nie aus einem Argument; der Abbilddigest hat keinen Vorgabewert |

### Bedrohungen, die diese Phase neu einbringt

| Muster | STRIDE | Gegenmassnahme |
|---|---|---|
| Der Store-Token lag in einem Snapshot | Information Disclosure | Rotation **vor** dem Dispatch und nach dem Tag; der alte Token wird bei der Erneuerung ungueltig |
| Eine neue Protokollzeile in `ExAppService` traegt einen Suchbegriff oder einen Dateinamen | Information Disclosure | Nur Pfad und Dauer in Millisekunden, nie Inhalt; ein Gate am Syntaxbaum oder als Textsuche haelt das fest |
| Ein Geheimnis-Gate mit zu weiter Ausnahmeliste | Repudiation | Je Eintrag ein Grund, und die Liste ist Teil des Auditberichts |
| Eine 423-Wiederholung verschluckt echte Fehler | Tampering (unbemerkt) | Nur 423, Obergrenze, jeder andere Code scheitert laut |
| Die A4-Box mit einer offenen SSH-Regel | Elevation of Privilege | Praefixlaenge 32, wie in Phase 15, und die Gegenprobe im Audit: keine Regel auf das ganze Netz fuer Port 22 |

### Was die Phase nicht anfassen darf

Die Berechtigungskette. Der ACL-Vorfilter im Container und der abschliessende Recheck in PHP sind die eine Zusage dieses Produkts, die nicht verhandelbar ist, und keine Auflage dieser Phase verlangt eine Aenderung daran. Ein Plan, der sie beruehrt, hat sich verlaufen.

---

## Assumptions Log

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---|---|---|
| A1 | Die Planwerte der drei neuen Posten im A4-Rechenblatt (frische Nextcloud, Korpus, Abbau) sind Schaetzungen ohne Messung | A4 | Der Deckel reisst. Gegenmassnahme: 15 Prozent Zuschlag, und der Owner bekommt die Schaetzung ausdruecklich als Schaetzung vorgelegt, wie Annahme A8 der Phase-15-Recherche |
| A2 | Eine frische Nextcloud auf einer Box ohne Snapshot ist mit dem heutigen Runbook nicht abgedeckt und braucht einen eigenen Ablaufblock | A4 | Der Erstvollzug kostet mehr als geplant; das ist der Grund fuer den eigenen Posten |
| A3 | `98c-sprachfaelle.sh` laeuft ohne Aenderung auf einer frischen Instanz gruen | A4 | Falls nicht, braucht A4 doch eine Nachfolgefassung 98d, und das ist ein zusaetzlicher Plan vor der Anfahrt |
| A4 | Die EU-Outreach-Mails mit der OCR-Zusage sind noch nicht versandt | BL-F02 | Wenn sie versandt sind, bindet die Zusage Baustein 1 an das naechste Release, und der Abbruchpfad faellt weg |
| A5 | Die Owner-Regel "keine alten Commit-Kennungen umschreiben" gilt auch fuer eine Bereinigung der 58 Altfunde | A2 | Sie stammt aus dem Projektgedaechtnis und nicht aus einer Datei dieses Repositoriums; der Owner sollte sie am Checkpoint bestaetigen |
| A6 | Der Store hat seit dem 11.09.2026 keinen Prozessschritt geaendert, der `store-submit.yml` betrifft | Store-Weg | Die Pruefung ist gegen die aktuelle Doku gefahren und hat nur `is_enterprise_only` als Neuerung gefunden, und das betrifft nur die Erstregistrierung. Eine Aenderung, die die Doku nicht nennt, faellt erst beim Dispatch auf |
| A7 | Die sechs neuen tesseract-Pakete existieren in Debian trixie mit Version `1:4.1.0-2` und `Architecture: all` | BL-F02 | Nicht in dieser Sitzung gegen sources.debian.org geprueft; die Aussage stammt aus dem BACKLOG-Eintrag und aus den Pin-Kommentaren des Dockerfiles. Vor dem Bau einmal nachsehen |
| A8 | Der Kandidat fuer Zusicherung 6 (sechster Engine-Zustand auf der Admin-Seite) ist im Zustandsabbild ablesbar | Upgrade-Beweis | Wenn nicht, ist die Filter- und Sortierzeile der zweite Kandidat; einer von beiden traegt |

---

## Open Questions

**Q-1: Welche Messzahl geht in die Store-Texte?**
- Was bekannt ist: vier Kandidaten mit Zahl und Rohdateiverweis, und die Kurztext-Regel laesst hoechstens eine Zahl zu.
- Was unklar ist: ob die Zahl 103,2 MB ersetzt, ergaenzt oder belassen wird, und ob der Messsatz der READMEs auf 52.137 Dokumente nachzieht.
- Empfehlung: blockierender Owner-Checkpoint im ersten Block der Phase, mit allen vier Kandidaten und der Kurztext-Regel daneben. Ohne diesen Entscheid kann das Gate fuer Erfolgskriterium 4 nicht gebaut werden.

**Q-2: Wie werden die 58 Altfunde behandelt?**
- Was bekannt ist: beide Wege sind gangbar, der Schaden ist gering, die Regelverletzung ist real, und die Historie bleibt in jedem Fall.
- Was unklar ist: ob der Owner Bereinigung will oder eine ausdrueckliche Abnahme.
- Empfehlung: derselbe Checkpoint, mit der Zahl der betroffenen Dateien je Kategorie und einer Kostenzeile je Weg.

**Q-3: Welchen Weg geht A4?**
- Was bekannt ist: drei Wege mit Kosten, und der CI-Weg ist kostenlos und dauerhaft, beweist aber nicht dasselbe.
- Was unklar ist: wie eng der Owner "frische ARM-Box" meint.
- Empfehlung: derselbe Checkpoint, mit dem Rechenblatt-Entwurf fuer Weg B und dem Vorbehalt aus 14-02 fuer Weg A. Die Anfahrt startet ohne Freigabe nicht, das ist die Auflage im Wortlaut.

**Q-4: Faehrt BL-F02 Baustein 1 mit?**
- Was bekannt ist: der Umfang, die sieben Arbeitsschritte, und die Nebenbedingung "nur ohne Terminrisiko".
- Was unklar ist: der Versandstand der EU-Outreach-Mails.
- Empfehlung: derselbe Checkpoint. Wenn ja, dann als letzte Welle vor dem Textblock, mit ausdruecklichem Abbruchpfad.

**Q-5: Was traegt Zusicherung 6 des Upgrade-Beweises?**
- Was bekannt ist: die Navigation taugt nicht mehr, zwei Kandidaten stehen bereit.
- Was unklar ist: ob der sechste Engine-Zustand im heutigen Zustandsabbild ablesbar ist, ohne den Abbildschritt umzubauen.
- Empfehlung: im Plan des Upgrade-Blocks als erste Aufgabe nachsehen, nicht raten. Der Abbildschritt schreibt `upgrade-before.json` und `upgrade-after.json`; wenn der Zustand dort fehlt, ist die Filter- und Sortierzeile der Ausweg.

**Q-6: Werden die Store-Bilder erneuert?**
- Was bekannt ist: sie sind vom 07.09.2026, das Produkt hat seitdem drei sichtbare Aenderungen bekommen, und die Groessentabelle in `store/media/README.md` traegt eine offene Wiedervorlage.
- Was unklar ist: ob der Owner den Aufwand will.
- Empfehlung: Entscheid vorlegen. Die Groessentabelle wird in jedem Fall nachgezogen, das ist klein und steht seit dem 07.09. offen.

---

## Sources

### Primaer (HIGH)

Alles Folgende ist in dieser Sitzung im Baum `8aed3c0` gelesen worden.

- `.planning/REQUIREMENTS.md` (HART-01, HART-02, REL-02 und Statustabelle)
- `.planning/ROADMAP.md`, Phase-16-Block mit fuenf Erfolgskriterien und dem Backlog-Kandidaten
- `.planning/STATE.md`, Entscheide aus der Ausfuehrung
- `.planning/phases/15-messphase-eine-box-anfahrt/15-16-SUMMARY.md`, Owner-Abnahme und Auflagen A1 bis A4 im Wortlaut
- `.planning/phases/15-messphase-eine-box-anfahrt/deferred-items.md`, L-10 und M-02 im Einzelnen
- `docs/audits/2026-09-phase-15/README.md`, Befunde M-01, M-02, L-01 bis L-11, die acht Familien der Gegenprobe
- `docs/measurements/2026-09-v12-messung/README.md`, Abschnitte 6, 8.2 und 10
- `docs/runbook-messbox.md`, Abschnitt 2 (Rechenblatt, Kostensaetze, Rechenweg, Deckel-Geschichte)
- `.planning/BACKLOG.md`, BL-F01 und BL-F02 im Wortlaut
- `.planning/milestones/v1.1-phases/11-haertung-und-store-einreichung-v1-1/deferred-items.md`, DI-11-01 bis DI-11-06
- `.planning/milestones/v1.1-phases/11-haertung-und-store-einreichung-v1-1/11-11-SUMMARY.md`, die Abgabe von v1.1.0 mit ihrer Belegkette
- `.github/workflows/store-submit.yml`, `release.yml`, `deploy-harp.yml` (Zeilen 87 bis 91, 2412 bis 2470, 2900 bis 2990, 3130 bis 3225), `integration.yml` (Zeilen 2020 bis 2060), `dependabot.yml`
- `php/lib/Migration/Version001100Date20260911000000.php`, `php/lib/Service/ExAppService.php`
- `php/appinfo/info.xml`, `backend/appinfo/info.xml`, `docs/store-listing.md`, `store/media/README.md`
- `backend/tests/test_store_metadata.py`, `test_lockstep_versions.py`, `test_upgrade_compatibility.py`, `test_measurement_scripts.py`, `test_search_endpoint.py`, `test_admin_ui_contract.py`, `test_ops_scripts.py`
- `backend/pyproject.toml`, `backend/Dockerfile`, `backend/src/findling/config.py`, `backend/src/findling/api/search.py`
- `docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh`, Kopf
- `git show v1.0.3:php/appinfo/info.xml`, `git show v1.1.0:php/appinfo/info.xml`, `git log -S "forms the retrieval layer"`
- `gh run list`, `gh run view 35470079862 --log-failed`, `gh run view 35556667085 --log-failed`, `gh pr view 10 --comments`, `gh pr list`

### Sekundaer (MEDIUM)

- `https://nextcloudappstore.readthedocs.io/en/latest/api/restapi.html`, abgerufen am 21.09.2026: Endpunkte, Pflichtfelder, Anmeldungsform, Antwortcodes, `POST /api/v1/token/new`, Groessengrenze der Paketdatei 20 MB
- `https://nextcloudappstore.readthedocs.io/en/latest/developer.html`, abgerufen am 21.09.2026: Signaturverfahren `openssl dgst -sha512 -sign`

### Tertiaer (LOW, gekennzeichnet)

- Die Owner-Regel gegen das Umschreiben alter Commit-Kennungen stammt aus dem Projektgedaechtnis und nicht aus einer Datei dieses Repositoriums (Annahme A5)
- Der Versandstand der EU-Outreach-Mails ist dieser Recherche unbekannt (Annahme A4)
- Die Existenz der sechs tesseract-Pakete in trixie ist aus dem BACKLOG uebernommen und nicht gegen sources.debian.org nachgesehen (Annahme A7)

---

## Metadata

**Konfidenz je Bereich**

| Bereich | Stufe | Grund |
|---|---|---|
| Repositoriumsbefund (Gates, Workflows, Tests, Texte) | HIGH | alles in dieser Sitzung im Baum gelesen, mehrere Aussagen zusaetzlich gegen git und gegen CI-Laeufe geprueft |
| HART-02 ist ausgeliefert | HIGH | Commit, Tag und neun Fundstellen einzeln nachgesehen |
| Der Upgrade-Beweis braucht drei Aenderungen | HIGH | die drei Stellen sind zitiert, die Navigationsfrage ist gegen beide Tags nachgerechnet |
| Store-Prozess | MEDIUM | gegen die aktuelle Doku geprueft, aber nicht gefahren; eine undokumentierte Aenderung faellt erst beim Dispatch auf |
| A4-Kostenschaetzung | MEDIUM | drei der sieben Posten sind Erstschaetzungen ohne Messung; die Kostensaetze sind gepinnt und am Anfahrtstag erneut zu lesen |
| BL-F02-Umfang | MEDIUM | die sieben Arbeitsschritte sind aus dem Baum abgeleitet, die Paketverfuegbarkeit ist uebernommen und nicht nachgesehen |
| Flake-Landschaft | MEDIUM | drei Staemme belegt, aber keiner ist systematisch gezaehlt worden; eine Auswertung ueber alle Laeufe des Monats wuerde das Bild schaerfen |

**Recherchedatum:** 2026-09-21
**Gueltig bis:** 2026-10-05 fuer den Repositoriumsbefund (er veraltet mit dem ersten Commit dieser Phase), 2026-10-21 fuer den Store-Prozess

**Was diese Recherche nicht sagt.** Sie sagt nichts darueber, ob die Nachfolgefassungen 92c und 99d auf einer Box tun, was sie sollen: auf dieser Maschine gibt es keine POSIX-Shell, und eine Box gibt es nicht mehr. Sie sagt nichts darueber, welche Messzahl in den Store-Text gehoert; das ist ein Owner-Entscheid und wurde bewusst nicht vorweggenommen. Sie sagt nichts darueber, ob die 58 Altfunde bereinigt werden sollen, und sie nennt keinen von ihnen: ein Recherchedokument, das sie zitierte, waere die neunzehnte Datei, die sie traegt.
