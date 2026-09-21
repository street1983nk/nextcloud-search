---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 14
subsystem: release
tags: [rel-02, hart-02, abgabe, store, tag, signatur, token-rotation, belegkette]

# Dependency graph
requires:
  - phase: 16-haertung-und-store-einreichung-v1-2-0
    provides: die Owner-Abnahme der Launch-Haertung aus 16-13, ohne die diese Abgabe nach der Owner-Regel vom 06.09.2026 nicht beginnen darf
  - phase: 16-haertung-und-store-einreichung-v1-2-0
    provides: den Versionsbump und die Migration aus 16-07, den Upgrade-Beweis aus 16-09, die ausgelieferten Texte und die zwei Gates aus 16-12
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: die Belegkette der v1.1.0-Abgabe als Form und den Owner-Entscheid zum Sitz des Tags
provides:
  - "v1.2.0 im Nextcloud App Store, beide Haelften, je mit HTTP 201 belegt"
  - "das GitHub-Release v1.2.0 mit genau vier signierten Anhaengen"
  - "ghcr.io/street1983nk/findling_backend:1.2.0 als Manifestindex mit linux/amd64 und linux/arm64"
  - "die Belegkette der Abgabe als Abschnitt 9 des Phasenaudits, acht Zeilen je mit Zahl"
  - "zwei neue LOW-Verdikte: L-16-04 (widerlegte Annahme zum paths-Filter bei Tag-Pushes) und L-16-05 (die ueberholte Zugangsmarke)"
  - "HART-02 und REL-02 abgehakt, damit alle 17 Requirements des Milestones v1.2"
affects: [milestone-abschluss-v1.2]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Belegkette nennt auch den Fehlschlag: die sieben gruenen Zeilen bekommen eine achte, weil eine Kette, die nur den gelungenen zweiten Anlauf zeigt, die Frage beantwortet, die niemand stellt"
    - "Eine neu geholte Zugangsmarke wird vor dem Setzen gegen die Schnittstelle geprueft, mit einem Aufruf, der nichts veraendert, und mit der Gegenprobe gegen den alten Wert"
    - "Eine Annahme in einem Workflow-Kommentar wird vor dem Tag geprueft und nach dem Tag korrigiert: der Baum unter dem Tag bleibt der Baum, den das Phasenaudit gelesen hat"
    - "Vor einem Release wird nichts mehr committet, was nicht in die Paketdatei kommt; jeder Vorbereitungscommit kostet eine CI-Runde und bewegt den Sitz des Tags"

key-files:
  created:
    - .planning/phases/16-haertung-und-store-einreichung-v1-2-0/16-14-SUMMARY.md
  modified:
    - docs/audits/2026-09-phase-16/README.md
    - .planning/phases/16-haertung-und-store-einreichung-v1-2-0/deferred-items.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md

key-decisions:
  - "Der Tag sitzt auf f827145 und nicht auf dem Bump-Commit 734a1b2: zwischen Bump und Abgabe sind die zwei Befunde des Phasenaudits behoben worden, und ein Tag auf dem Bump haette eine Fassung ausgeliefert, deren Fehler in der Belegkette daneben stehen"
  - "Vor dem Tag ist nichts committet worden. Die Vorbereitung hat nur geprueft und nichts geaendert; ein Vorbereitungscommit haette main ueber den gepushten, fuenffach gruenen Stand hinausgeschoben und eine weitere CI-Runde erzwungen, ohne dass sich an den Paketdateien etwas aendert"
  - "Der widerlegte Workflow-Kommentar (L-16-04) wird NACH dem Tag korrigiert. Eine Aenderung an docker.yml haette den Baum unter dem Tag von dem Baum getrennt, den das Phasenaudit geprueft hat, und das fuer einen Kommentar"
  - "Der Fehlschlag des ersten Dispatch steht als eigene Zeile in der Belegkette und als eigener Befund im Bericht, statt als Fussnote der gelungenen Einreichung"
  - "Die Gegenprobe ist je App-Seite einzeln gefahren; die grosse Katalogdatei ist ausdruecklich nicht als Beleg benutzt worden, weil sie im Cache hinterherhaengt"
  - "Der zweite Anlauf ist kein Wiederholen bis gruen: zwischen 401 und 201 liegt eine Ursache, eine Pruefung und ein neuer Wert, und der Lauf mit dem alten Wert ist nicht noch einmal gestartet worden"

patterns-established:
  - "Nach jedem Remote-Schritt wird die ganze Laufliste gelesen und nicht nur der erwartete Lauf (L-16-02, hier zum ersten Mal angewendet: sieben Tag-Laeufe einzeln benannt)"
  - "Eine Zugangsmarke erscheint in keiner Datei, keinem Protokoll und keiner SUMMARY; die Belege sind Antwortcodes und Uhrzeiten"

requirements-completed: [HART-02, REL-02]
requirements-partial: []

# Metrics
duration: 120 min
completed: 2026-09-21
---

# Phase 16 Plan 14: Die Abgabe Summary

v1.2.0 steht als signiertes App-Paar im Nextcloud App Store, beide Hälften mit HTTP 201 belegt, und der Weg dahin hat einen Befund gefunden, der zwischen zwei Handgriffen des Owners saß: die erneuerte Zugangsmarke war beim Setzen schon überholt, der erste Dispatch antwortete 401, und der Lauf hat abgebrochen statt zu wiederholen.

## Das Owner-Wort, im Wortlaut

Vorgelegt wurden am 21.09.2026 per strukturierter Rückfrage: die Belegkette aus dem Tag-Lauf (Tag mit Commit, Laufnummer, vier Anhänge mit Bytezahl, Manifestindex mit beiden Architekturen), die Laufliste der sieben grünen Tag-Läufe und die Abnahme der Härtung aus 16-13.

**Antwort des Owners, im Wortlaut:**

> "Go, einreichen"

Die Rotation der Zugangsmarke ist am selben Tag vom Owner beauftragt und ausgeführt worden, in der vom Plan verlangten Reihenfolge: **nach** dem Tag und dem grünen Release-Lauf, **vor** dem Dispatch der Einreichung. Zwischen Rotation und Dispatch liegt keine andere Handlung am Repositorium.

## Die Belegkette, acht Zeilen

| Nr. | Was | Beleg |
| --- | --- | --- |
| 1 | Tag | `v1.2.0`, annotiert, auf `f827145574500e4a3e608e96a93c3a8ae48c4f23` |
| 2 | Release | Lauf **35612545646**, genau vier Anhänge; zweimal `Verified OK`, zweimal `684 base64 characters`, `appinfo/signature.json was written and is not empty` |
| 3 | Anhänge | `findling.tar.gz` 309.484 B, `findling.tar.gz.sig` 684 B, `findling_backend.tar.gz` 29.817 B, `findling_backend.tar.gz.sig` 684 B (Grenze 20.971.520 B) |
| 4 | Container-Abbild | `application/vnd.oci.image.index.v1+json` für 1.2.0 mit `linux/amd64` und `linux/arm64`, anonym abgefragt **vor** der Einreichung |
| 5 | Submission | Lauf **35618848300**, success |
| 6 | HTTP-Codes | `release findling v1.2.0: HTTP 201` und `release findling_backend v1.2.0: HTTP 201` |
| 7 | Gegenprobe | beide App-Seiten einzeln abgefragt, beide nennen **1.2.0**; die große Katalogdatei ist nicht als Beleg benutzt worden |
| 8 | Der Fehlschlag davor | Lauf **35617988639**, `release findling v1.2.0: HTTP 401`, Abbruch ohne Wiederholung |

**Die sieben Tag-Läufe, alle success:** Release 35612545646, PHP 35612546138, Multi-arch 35612545993, HaRP deploy 35612546034, Python 35612545258, Integration 35612545589, Resilience 35612545272. Der Tag ist um 14:29:52Z gepusht worden, der letzte der sieben war um 14:44:21Z grün.

Damit ist auch die offene Frage aus 16-13 beantwortet: **der zweite Fix des Flake-Stammes `single-flight-zeit` trägt in CI.** Er ist im Tag-Lauf der Python-Werkbank grün, nachdem der Fall am selben Tag viermal rot gewesen war.

## Der Befund der Abgabe

**L-16-05, die überholte Zugangsmarke.** Der erste Dispatch (15:18:01Z, Lauf 35617988639) endete mit HTTP 401. Die Marke war Minuten vorher frisch geholt worden, aber die Erneuerung hatte doppelt ausgelöst beziehungsweise die Seite zeigte nach dem ersten Klick den älteren der beiden Werte; eine zweite Erneuerung macht die erste ungültig, und auf der Seite sehen beide gleich aus.

Was daraus geworden ist: die Marke wird seither **vor** dem Setzen gegen die Schnittstelle geprüft, mit einem Aufruf, der nichts verändert. Ein leerer Rumpf auf die Release-Route antwortet mit HTTP 400 und einem Feldfehler, wenn die Marke gültig ist, und mit HTTP 401, wenn sie überholt ist. Beide Fälle sind gefahren worden, der 400er mit dem neuen Wert und der 401er als Gegenprobe mit dem alten, damit der 400er nicht bloß die Erreichbarkeit der Route belegt. Das Geheimnis ist um 15:24Z gesetzt worden, der zweite Dispatch lief um 15:25:34Z und antwortete zweimal 201.

**Der Lauf hat nicht wiederholt, bis er grün war.** Zwischen 401 und 201 liegen eine Ursache, eine Prüfung und ein neuer Wert. Das ist genau das, was der Plan für jeden Code verlangt, der nicht 201 ist.

**Kein Wert einer Zugangsmarke steht in einer Datei, einer Laufausgabe, einer SUMMARY oder im Bericht.** Die Belege sind Antwortcodes und Uhrzeiten.

**L-16-04, eine Annahme, die nicht stimmt.** Die Kommentare in `docker.yml` und `release.yml` sagen, GitHub wende den `paths`-Filter auch auf Tag-Pushes an, ein Tag auf einem Commit ohne `backend/**` überspringe den Abbildbau also. Da der vorgesehene Tag-Commit `f827145` nur `.planning/` berührt, war das vor dem Tag die entscheidende Frage. Sie ist mit zwei Laufnummern widerlegt worden: Tag `v1.0.0` sitzt auf `160a289`, das nur `store/media/**` berührt, und trotzdem sind dort alle sieben Läufe mit echten Jobs gelaufen (34140924599 baute beide Architekturen und mergte das Manifest, 34140924650 fuhr php -l, info.xml-Validierung und PHPUnit). Der Kommentar ist **nicht** vor dem Tag geändert worden, und das ist der Entscheid: der Baum unter dem Tag bleibt der Baum, den das Phasenaudit gelesen hat.

## Die Vorbereitung, und warum sie nichts committet hat

Vor dem Tag ist geprüft und nichts geändert worden:

- die drei Versionsstellen im Gleichschritt: `php/appinfo/info.xml`, `backend/appinfo/info.xml` und der `<image-tag>` daneben, alle auf 1.2.0
- die Migration `Version001200Date20260921000000.php` liegt, die Gleichschritt-Gates der Messzahl sind Teil der grünen Suite
- alle sechs Gate-Stufen grün, volle Suite **2491 bestanden / 15 übersprungen**, exakt die Referenz aus 16-13
- ein Trockenlauf der Paketbildung: beide Hälften stagen sauber, `info.xml` 16.995 B und 28.144 B gegen die Grenze von 524.288 B. Die Packstufe verweigert auf dieser Maschine korrekt den Dienst, weil der Arbeitsbaum CRLF trägt; die Bytezahlen der Paketdateien entstehen deshalb erst im Lauf, und genau so stehen sie in der Belegkette
- die Laufliste des letzten Pushes (f827145): fünf Läufe, alle grün

Ein Vorbereitungscommit hätte `main` über diesen geprüften Stand hinausgeschoben und vor dem Tag eine weitere CI-Runde von rund einer Viertelstunde erzwungen, ohne an den Paketdateien etwas zu ändern. Die zwei Befunde dieses Plans sind deshalb erst nach der Einreichung committet worden.

## Die Zustandspflege

- `.planning/REQUIREMENTS.md`: **HART-02** und **REL-02** abgehakt, je mit Beleg in der Traceability-Tabelle und je mit dem Vorbehalt, der mit dem Haken nicht verschwindet. Bei HART-02: belegt ist der ausgelieferte Wortlaut in beiden `info.xml` und das Gate mit Anzahlprüfung, **nicht** nachgesehen ist, wie der Store den Satz auf der Seite rendert. Bei REL-02: der Haken hängt am zweiten Dispatch, und die Gegenprobe belegt, dass beide App-Seiten 1.2.0 nennen, nicht dass eine fremde Instanz 1.2.0 installiert hat. Damit sind **alle 17 Requirements** des Milestones abgehakt.
- `.planning/ROADMAP.md`: Phase 16 abgehakt, die fünf Erfolgskriterien je mit Urteil und Beleg, Plantabelle auf 14/14, Fortschrittstabelle auf Complete.
- `.planning/STATE.md`: Kopf (`status: phase_complete`, `stopped_at`, `last_updated`, `progress` auf 63/63 und 100 Prozent), "Current Position" neu geschrieben, fünf Entscheide dieses Plans, Session-Block nachgezogen.

## Deviations from Plan

### Bewusste Abweichungen

**1. Die Belegkette hat acht Zeilen statt sieben.** Der Plan nennt sieben. Die achte ist der Fehlschlag des ersten Dispatch. Eine Kette, die nur den gelungenen zweiten Anlauf nennt, wäre genau die Lücke, die dieselbe Phase bei M-16-01 an sich selbst gefunden hat.

**2. Zwei Dateien mehr als angekündigt.** Der Plan nennt vier Dateien; dazu gekommen ist `deferred-items.md` mit den zwei neuen Verdikten. Das ist keine Ausweitung, sondern die Hausregel der Phase an einem Ort, an dem der Plan die Befunde noch nicht kennen konnte.

**3. Task 1 und Task 3 sind in zwei Händen gelaufen.** Jede Handlung am entfernten Repositorium (Tag, Push, Dispatch) hat der Auftraggeber ausgeführt, die Vorbereitung, die Prüfwege, die Belegkette und die Zustandspflege diese Ausführung. Die Belegzeilen sind deshalb übernommene Laufausgaben und keine selbst gefahrenen Befehle; die Gegenprobe der zwei App-Seiten und die anonyme Abfrage des Manifestindex sind hier gefahren worden.

### Auto-fixed Issues

Keine. Es ist in diesem Plan keine Zeile Erzeugniscode angefasst worden.

## Auth Gates

Einer, und er war der Kern des Plans: die Erneuerung der Store-Zugangsmarke. Sie ist ein Owner-Handgriff, sie stand im Plan als blockierender Checkpoint, und sie ist in der vorgeschriebenen Reihenfolge ausgeführt worden. Ihr Beleg ist derselbe wie der Beleg der Einreichung, zweimal HTTP 201, und der Umweg über einen 401 steht als L-16-05 im Bericht.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche. Die sechs Bedrohungen des Plans sind je belegt: **T-16-52** (die alte Marke stand in einem Snapshot) durch die vollzogene Rotation, deren Wirkung der 401 des alten Werts sogar beweist; **T-16-53** (Paketdatei ohne gültige Signatur) durch die zwei Signaturschritte und die zwei `Verified OK` im Release-Lauf; **T-16-54** (Abbild ohne arm64) durch den anonym abgefragten Manifestindex vor der Einreichung; **T-16-55** (Abgabe ohne Belegkette) durch Abschnitt 9 mit acht Zeilen je mit Zahl; **T-16-56** (die Abgabe fällt in einen Flake, während der Tag schon liegt) durch sieben gleichzeitig grüne Tag-Läufe ohne einen einzigen roten Ast; **T-16-SC** gegenstandslos, keine Abhängigkeit und kein Installationsbefehl.

## Was offen bleibt

- **Der Milestone-Abschluss v1.2** steht aus: Milestonezeile der ROADMAP, Ablage der Phasen, Rückblick. Es ist kein Plan mehr offen.
- **Die drei Commits dieses Plans sind nicht gepusht.**
- **L-16-04 ist nicht gefixt**, nur belegt und mit Adresse weitergereicht: zwei Kommentarblöcke in zwei Workflows, keine Zeile Verhalten.
- **M-01 bleibt teilerfüllt.** Die Zahl auf Zielhardware entsteht auf einer Box und nirgends sonst.
- **Die Store-Bilder stammen weiter aus der 1.0.0-Zeit.** Der Punkt ist in 16-RESEARCH als Owner-Entscheid vorgemerkt und war kein Erfolgskriterium.

## Self-Check: PASSED

- `git rev-list -n 1 v1.2.0` nennt `f827145574500e4a3e608e96a93c3a8ae48c4f23`, den Commit der Belegkette.
- `docs/audits/2026-09-phase-16/README.md`: vorhanden, 617 Zeilen, Abschnitt 9 enthaelt beide `HTTP 201`-Wortlaute und die acht Zeilen der Kette.
- `.planning/REQUIREMENTS.md`: drei Treffer auf `REL-02`, kein `- [ ]` mehr in der Liste, kein `Pending` in der Traceability-Tabelle.
- `deferred-items.md`, `16-14-SUMMARY.md`, `ROADMAP.md`, `STATE.md`: vorhanden und nachgezogen; alle Dateien reines LF.
- Commits `10d74c1`, `f8bc9f7` und `cf1145e`: in `git log` vorhanden; `git diff --diff-filter=D f827145..HEAD` nennt keine geloeschte Datei.
- Alle Gate-Stufen gruen, volle Suite **2491 bestanden / 15 uebersprungen**, Skipzahl unveraendert.
- Der Arbeitsbaum ist sauber, und es ist nicht gepusht worden.
