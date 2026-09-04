---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 18
subsystem: packaging
tags: [store, media, screenshots, playwright, release, signing, github-actions, openssl, textual-gate]

# Dependency graph
requires:
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: 05-17, der Absichtskommentar an der Stelle der screenshot-Elemente und das Store-Gate, das die Mindestzahl ausdrücklich diesem Plan überlässt
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: 05-13, die vereinheitlichten Action-Pinnungen und die Regel, dass jede Deadline ihre Messung nennt oder sich als Schätzung ausweist
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: 05-15, die require-dev-Abhängigkeit, deren Abwesenheit im Archiv dieser Plan zusagt und prüft
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: die Verwaltungsseite mit Deckungsgrad und Pro-Datei-Diagnose, die der zweite Screenshot zeigt
provides:
  - D-13 erfüllt: zwei kuratierte Screenshots der echten Oberfläche und ein Header-Bild liegen unter store/media und sind aus beiden Einträgen per https verlinkt
  - Das Store-Gate erzwingt ab jetzt mindestens ein screenshot-Element je App und die Existenz der lokalen Bilddatei
  - D-09 vorbereitet: ein Workflow-Lauf erzeugt für beide Hälften ein XSD-validiertes, größengeprüftes und signiertes Archiv samt Release-Signatur
  - Die beiden Signaturarten sind getrennt benannt, in der richtigen Reihenfolge erzeugt und gegen das geholte Zertifikat verifiziert
  - Die Fingerprint-Tabelle aus docs/certificates.md wird im Lauf maschinell geprüft statt von Hand
  - docs/certificates.md trägt den Abschnitt Release-Lauf mit gemessenen Werten und eine auf neun Punkte erweiterte Checkliste
affects: [05-19-tag-v1-0-0, 05-20-verwaltungsseite, phase-review, phase-06-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Store-Bild entsteht aus einem Wegwerf-Stack mit erzeugtem Bestand, nicht aus dem Referenzkorpus der CI und nicht aus dem Alltagsstack des Owners"
    - "Ein Deckungsgrad unter hundert Prozent ist das bessere Werbebild, weil die Diagnose der Gegenstand ist"
    - "Die Antivakuitätsklausel einer Bildregel prüft die Datei hinter der Adresse, nicht nur die Form der Adresse"
    - "Die Fork-Abwehr eines Signierjobs ist die Abwesenheit des pull_request-Triggers und keine Bedingung in einem Schritt: eine Bedingung kann ein späterer Edit abschwächen"
    - "Ein Archiv wird einmal gebaut und nie neu gebaut, weil die Release-Signatur den Bytes gehört und tar.gz nicht byte-reproduzierbar ist"
    - "Ein Archiv wird genau einmal gelistet und jede Prüfung liest diese Liste: tar in eine Pipe mit grep -q bricht größenabhängig mit SIGPIPE ab"
    - "Was ein Lauf zusagt, wird im Lauf behauptet und geprüft, nicht im Kommentar beschrieben"

key-files:
  created:
    - store/media/README.md
    - store/media/header.png
    - store/media/screenshot-search.png
    - store/media/screenshot-admin.png
    - .github/workflows/release.yml
  modified:
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - backend/tests/test_store_metadata.py
    - docs/certificates.md
    - .planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md

key-decisions:
  - "Das Header-Bild ist das erste screenshot-Element und kein eigenes Feld, weil eine Store-Seite nur Screenshots hat und das erste das ist, das jeder sieht"
  - "Die Companion-Hälfte trägt alle drei Bilder, die Backend-Hälfte Header und Verwaltungsbild und ausdrücklich nicht das Suchbild: mit dieser Hälfte sucht niemand, sie ist der Container, den ein Administrator installiert"
  - "Die Bildadressen zeigen auf den Zweig main und nicht auf einen Tag: ein kaputtes Bild soll mit einem Commit zu reparieren sein und nicht mit einem Release"
  - "Der Deckungsgrad im Verwaltungsbild bleibt bei 87 Prozent statt 100, nach Rückfrage und ausdrücklichem Owner-Entscheid, weil die kennwortgeschützte Datei die Diagnose zeigt"
  - "Das Gate verlangt, dass jede Bildadresse in store/media dieses Repositories zeigt: ein Bild auf einem fremden Server ist ein Ausfall, den hier niemand beheben kann"
  - "release.yml hat keinen pull_request-Trigger, und das ist die Umsetzung der Fork-Regel aus docs/certificates.md in einer Form, die kein Edit versehentlich aufweicht"
  - "workflow_dispatch ist kein Loch in dieser Regel: ein Dispatch setzt Schreibrecht auf dieses Repository voraus, und ein Probelauf ohne echte Signatur würde nichts proben"
  - "gh release create statt einer fremden Action: die CLI liegt auf dem Runner und fügt einem Job mit zwei Signaturschlüsseln keine vierte Partei und keine Pinnung hinzu"
  - "Nur die Companion-Hälfte wird code-signiert, weil die Integritätsprüfung PHP-Dateien der Instanz sieht und die ExApp keine liefert; der Grund steht als Kommentar, damit der fehlende Schritt nicht als Versehen gelesen wird"
  - "Die Staging-Schritte benutzen eine Einschlussliste statt einer Ausschlussliste, damit ein neues Verzeichnis unter php/ erst benannt werden muss, bevor es ausgeliefert wird"
  - "LICENSE und THIRD-PARTY.md reisen in beiden Archiven mit, weil neun Apache-2.0-Icon-Pfade im Companion-Archiv liegen und die Zuschreibung dazugehört"

patterns-established:
  - "Ein Workflow, der nicht dispatchbar ist, wird Schritt für Schritt lokal nachgefahren, und was dabei offen bleibt, wird einzeln benannt statt als erfüllt behauptet"
  - "Eine Gegenprobe gehört zu jeder Ausschlussliste: ein absichtlich falsch gebautes Archiv muss von derselben Schleife gefangen werden"
  - "Jeder run-Block eines nicht ausführbaren Workflows geht durch bash -n, mit GitHub-Ausdrücken durch einen Platzhalter ersetzt"

requirements-completed: [PKG-05]

# Metrics
duration: ca. 3h 30m über drei Sitzungen
completed: 2026-09-04
---

# Phase 5 Plan 18: Die Store-Medien und die Release-Strecke Summary

**Beide Store-Einträge zeigen jetzt Bilder der echten Oberfläche, darunter einen Treffer aus dem Inhalt zweier Dokumente in der gewohnten Unified Search und eine Verwaltungsseite mit 87 Prozent Deckungsgrad und einer Fehlergruppe, ein Gate verhindert einen leeren Bildrahmen, und ein Workflow erzeugt für beide Hälften ein XSD-validiertes, größengeprüftes und signiertes Archiv samt verifizierter Release-Signatur, ohne Testcode darin und ohne Schlüssel im Log. Der CI-Probelauf selbst steht als DI-05-33 offen, weil er einen Push braucht.**

## Performance

- **Duration:** rund 3 h 30 min, über drei Sitzungen (zweimal durch ein Limit unterbrochen, nicht durch einen Sachfehler)
- **Tasks:** 3, davon einer ein blockierender Checkpoint
- **Commits:** 5

## Accomplishments

Die Medien. Ein Wegwerf-Stack mit eigenem Projektnamen und eigenem Port (DI-05-07-A) auf Port 8091, darin acht selbst erzeugte deutsche Bürodokumente und ein Konto `Verwaltung`. Kein Dokument, kein Name und keine Adresse darin ist echt. Daraus drei Bilder mit Playwright, alle drei vom Owner am 04.09.2026 freigegeben:

| Bild | Maße | Größe | Was es zeigt |
|---|---|---|---|
| `screenshot-search.png` | 1440 x 700 | 111 KiB | die Unified Search mit `Kündigungsfrist`, Gruppe `File contents`, zwei Treffer mit Textauszug |
| `screenshot-admin.png` | 1440 x 1100 | 153 KiB | Deckungsgrad 87 Prozent, 7 von 8, vier Zähler, Fehlergruppe `Password protected`, Einzelabfrage |
| `header.png` | 1440 x 810 | 165 KiB | eine Überschrift, eine Zeile, Space Grotesk, das echte SVG der App |

Das Suchwort ist mit Absicht `Kündigungsfrist`: es steht im Inhalt zweier Dokumente und in keinem Dateinamen, also ist das Bild eines dieser App und nicht der Dateiliste. Der Bestand enthält mit Absicht eine kennwortgeschützte PDF-Datei, damit der Deckungsgrad nicht 100 Prozent ist; der Owner hat das nach Rückfrage ausdrücklich so entschieden, weil die Diagnose sichtbar sein soll.

Das Gate. `backend/tests/test_store_metadata.py` prüft jetzt zusätzlich zwei Dinge, die das Schema nicht kann: mindestens ein Bild je App, und dass hinter jeder Adresse wirklich eine Datei unter `store/media` liegt. Eine Adresse ohne Bild besteht jede Schemaprüfung und ist auf der Store-Seite ein leerer Rahmen. Sechs neue Selbsttests, plus eine Antivakuitätsklausel über das Medienverzeichnis selbst.

Die Release-Strecke. `.github/workflows/release.yml` macht in einem Lauf: stagen, Store-Validierungspfad über die gestagte `info.xml`, beide Größengrenzen als eigene Schritte mit eigener Meldung, `occ integrity:sign-app` auf der Companion-Hälfte, packen mit genau einem Top-Level-Ordner, dann die Release-Signatur über dieses Archiv und deren Verifikation gegen das geholte Zertifikat. Dazu die Fingerprint-Prüfung aus `docs/certificates.md`, jetzt maschinell für beide Hälften.

## Task Commits

| Task | Commit | Was |
|---|---|---|
| 1 | `94bd451` | die drei Bilder, `store/media/README.md`, die screenshot-Elemente in beiden `info.xml` |
| 1 | `9ee8fc0` | die zwei Medienregeln im Store-Gate, mit sechs Selbsttests |
| 1 | `8eacd11` | DI-05-30 bis DI-05-32 |
| 2 | (Checkpoint) | Owner-Freigabe, Secret-Stand, Entscheid zum Probelauf |
| 3 | `d2b6fe2` | `release.yml` und der Abschnitt Release-Lauf in `docs/certificates.md` |
| 3 | `d0fedb8` | DI-05-33 und DI-05-34 |

## Files Created/Modified

Erzeugt: `store/media/README.md`, `store/media/header.png`, `store/media/screenshot-search.png`, `store/media/screenshot-admin.png`, `.github/workflows/release.yml`.

Geändert: `php/appinfo/info.xml` (drei screenshot-Elemente, Absichtskommentar ersetzt), `backend/appinfo/info.xml` (zwei), `backend/tests/test_store_metadata.py` (zwei Regeln, sechs Selbsttests), `docs/certificates.md` (Abschnitt Release-Lauf, Checkliste auf neun Punkte), `deferred-items.md` (fünf Einträge).

## Decisions Made

Siehe `key-decisions` im Kopf. Die drei, die am weitesten reichen:

Die Bildadressen zeigen auf `main` und nicht auf einen Tag. Ein Bild muss erreichbar sein, solange der Eintrag steht, und ein kaputtes Bild soll mit einem Commit zu reparieren sein.

`release.yml` hat keinen `pull_request`-Trigger. `docs/certificates.md` verlangt, dass ein Fork-Workflow diese Schlüssel nie erreicht. Ein Trigger, den es nicht gibt, ist für jeden unerreichbar, und anders als ein `if` kann ihn kein späterer Edit abschwächen. Der zusätzliche Wächterschritt scheitert laut statt still zu überspringen, weil ein übersprungener Signierschritt ein unsigniertes Archiv erzeugt, das fertig aussieht.

Das Archiv wird einmal gebaut und nie neu gebaut. Die Release-Signatur gehört den Bytes, und `tar.gz` ist nicht byte-reproduzierbar. Das Schwesterprojekt dieses Autors hat das auf seinem 0.1.8-Release gemessen, 45710 Bytes lokal gegen 45546 veröffentlicht, und rechnet die Signatur seither über das heruntergeladene Asset. Dieser Workflow braucht den Schritt nicht, weil er dieselbe Datei signiert und hochlädt.

## Deviations from Plan

### Auto-fixed Issues

Ein echter Fehler, gefunden von der Generalprobe und in beiden Fassungen behoben. Meine Prüfschleife hatte `tar -tzf "$archive" | grep -q ...`. `grep -q` verlässt die Pipe beim ersten Treffer, `tar` bekommt SIGPIPE, während es noch schreibt, und unter `pipefail` meldet die ganze Pipeline einen Fehler. Das ist schlimmer als ein gewöhnlicher Fehler, weil er von der Archivgröße abhängt: die fünf Einträge des Backend-Archivs waren durch, bevor `grep` ging, und sahen richtig aus; die 67 Einträge des Companion-Archivs nicht, und zwei vorhandene Dateien wurden als fehlend gemeldet. Jetzt wird jedes Archiv genau einmal in eine Datei gelistet und jede Prüfung liest diese Datei. Derselbe Fix steht in `release.yml` und in der Probe.

Zwei Umgebungsfunde der Entwicklungsmaschine, die nur die Probe betreffen und nicht den Workflow. `MSYS_NO_PATHCONV=1`, das `docs/certificates.md` für die interaktive Schlüsselerzeugung nennt, ist das falsche Werkzeug, sobald dasselbe Kommando auch Dateipfade hat: es schaltet die Pfadumwandlung für jedes Argument ab, und ein Ausgabepfad unter `/tmp` erreicht ein natives `openssl` wörtlich. Richtig ist `-subj "//CN=findling"`. Und Prozess-Substitution `<(...)` erzeugt `/dev/fd`-Pfade, die das native `openssl` nicht öffnen kann; deshalb schreibt der Verifikationsschritt jetzt echte Dateien, in der Probe und im Workflow, damit lokal genau die Form läuft, die auch in CI läuft. Der erste Fund steht als Absatz in `docs/certificates.md`.

### Nicht behoben, sondern notiert

Fünf Einträge in `deferred-items.md`. DI-05-30, zwei Sätze der Verwaltungsseite stehen ohne Punkt aneinander, und der Absatz steht im öffentlichen Store-Bild; gehört zu Plan 05-20, der die Vorlage ohnehin anfasst. DI-05-31, `.gitattributes` führt `store/media` nicht. DI-05-32, ein gesperrter Begriff steht als englisches Wort in einem öffentlichen Kommentar, und ob die Regel ihn trifft, ist eine Owner-Entscheidung. DI-05-33 und DI-05-34, siehe unten.

## TDD Gate Compliance

Beide neuen Medienregeln haben Selbsttests, die rot werden: eine Adresse ohne Bild, eine Adresse auf fremdem Host, eine Adresse in einem Unterverzeichnis, ein Eintrag ohne Bild, plus die zwei Formregeln. Dazu eine Rot-Probe am echten Baum: `header.png` verschoben, das Gate meldet `the screenshot address names 'header.png', which does not exist under store/media`, zurückgenommen.

Die Ausschlussliste des Archivs hat eine Gegenprobe: ein absichtlich mit `tests`, `phpunit.xml` und `composer.json` gebautes Archiv wird von derselben Schleife gefangen, und die zwei nicht eingebauten Verstöße bleiben still.

## Issues Encountered

Die Aufnahme der Bilder hatte vier Hürden, alle in `store/media/README.md` festgehalten: die Skelettdateien von Nextcloud zählen in den Nenner des Deckungsgrads und müssen vor dem Anlegen des Kontos aus `skeletondirectory` verschwinden; der Erstlauf-Assistent legt sein Fenster über die Oberfläche; die Wortliste des deutschen Analysators muss für einen Host-Prozess einmal gebaut werden; und SQLite streitet sich mit dem laufenden Poller, sodass eine Anmeldung mit `database is locked` zurückkommen kann, was die Aufnahme mit einem erneuten Versuch beantwortet.

Der CI-Probelauf ist nicht gefahren. `workflow_dispatch` setzt voraus, dass die Datei auf einem Zweig im entfernten Repository liegt, und dieser Ausführer darf nicht pushen. Statt die Abnahmebedingung als erfüllt zu behaupten, ist jeder Schritt lokal nachgefahren und der Rest einzeln benannt, siehe DI-05-33.

## Verification

Lokal belegt, am 04.09.2026:

| Beweis | Ergebnis |
|---|---|
| `uv run python -m pytest -q` | 975 passed, 11 skipped |
| `ruff check`, `ruff format --check`, `pyright`, `vulture` | sauber |
| Store-Validierungspfad, beide `info.xml`, gepinnte XSD im Wegwerf-Abbild | `- validates` |
| Store-Validierungspfad über die gestagten Dateien | `- validates` |
| `occ integrity:sign-app` gegen Nextcloud 34.0.3 | `Successfully signed`, `signature.json` 10697 Bytes |
| Companion-Archiv | 220913 Bytes, 67 Einträge, ein Top-Level `findling/` |
| Backend-Archiv | 26807 Bytes, 5 Einträge, ein Top-Level `findling_backend/` |
| Beide Release-Signaturen | 684 base64-Zeichen, `openssl dgst -verify` sagt `Verified OK` |
| Ausschlussliste plus Gegenprobe | grün, und die Gegenprobe fängt genau die drei eingebauten Verstöße |
| Alle 23 `run`-Blöcke | `bash -n` ohne Fehler |
| Beide Zertifikate live geholt | Subject und Fingerprint stimmen mit der Tabelle in `docs/certificates.md` |
| Bildadressen | 91, 102 und 101 Zeichen gegen die Grenze von 256 |
| Typografie | kein U+2014, kein U+2013, kein Emoji in den geänderten Dateien |

Die Bildadressen antworten heute 404, weil sie auf `main` zeigen und dieser Zweig nicht gemergt ist. Nach dem Merge lösen sie auf.

## User Setup Required

Nichts mehr für diesen Plan. Der Owner hat am 04.09.2026 die drei Bilder freigegeben, den Deckungsgrad von 87 Prozent nach Rückfrage bestätigt, und bestätigt, dass `APP_PRIVATE_KEY`, `BACKEND_PRIVATE_KEY` und `APPSTORE_TOKEN` als Repository-Secrets liegen. Der Entscheid zum Probelauf lautet: nur Artefakte, kein GitHub-Release.

Offen für den Vorgang, der diesen Zweig merged:

```
gh workflow run release.yml --ref main
```

Danach die gemessene Spanne in `timeout-minutes` eintragen (DI-05-34) und die vier Punkte aus DI-05-33 abhaken.

Der Wegwerf-Stack läuft noch, damit ein neues Aufnehmen nach dem DI-05-30-Fix billig ist. Abräumen:

```
docker compose -p findling-shot down -v
```

## Next Phase Readiness

Plan 05-19 kann den Tag `v1.0.0` setzen: beide Hälften stehen auf 1.0.0, der `image-tag` auch, `release.yml` prüft alle drei gegen den Tag, und die Entscheidung reguläres Release oder Vorabversion steht dort erneut zur Wahl. Plan 05-20 arbeitet an der Verwaltungsseite und hat mit DI-05-30 einen Textfund von hier.

Phase 6 hat jetzt alles außer dem Upload: signierte Archive, Release-Signaturen als eigene Dateien, eine https-Download-URL, sobald ein Tag läuft, und `APPSTORE_TOKEN`.

## Self-Check: PASSED

Die Abnahmebedingungen von Task 1 sind erfüllt. Von Task 3 sind alle erfüllt außer der ersten, dem grünen `workflow_dispatch`-Lauf, und das ist als DI-05-33 mit der Begründung und den vier verbleibenden Punkten festgehalten statt als erfüllt behauptet.
