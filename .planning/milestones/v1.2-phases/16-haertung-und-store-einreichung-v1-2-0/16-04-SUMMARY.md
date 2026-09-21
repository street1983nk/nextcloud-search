---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 04
subsystem: ops-tooling
tags: [di-11, l-07, lastwerkzeug, vorlaufsonde, aws, teardown, deferred-items]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: die vier aufgeschobenen Punkte DI-11-02, DI-11-03, DI-11-05 und DI-11-06 im Wortlaut
  - phase: 12-messwerkzeug-runbook-und-terminentscheid
    provides: die In-Container-Sonde 73-bestand-sonde.py, die den ungedeckelten Bestand ueber ranked_sides liest
  - phase: 15-messphase-eine-box-anfahrt
    provides: die Befunde L-05 bis L-08, den v1.2-Messbericht mit den vier Laststufen und die Gegenrechnung auf cURL error 28
provides:
  - scripts/ops/search_load.py mit einer Vorlaufsonde, die ohne Treffer von abgebrochen trennt (DI-11-03)
  - scripts/ops/aws_box.sh mit einem cmd_destroy, das das Schluesselpaar mitnimmt und zurueckliest (L-07)
  - .planning/phases/16-haertung-und-store-einreichung-v1-2-0/deferred-items.md mit sieben Verdikten und der Adressliste der Phase-15-Befunde
  - fuenf neue Faelle in backend/tests/test_ops_scripts.py ueber beide Werkzeuge
affects: [16-08-erfolgskriterium-4, 16-12-phasenaudit, 16-13-launch-haertung, naechste-anfahrt]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Frage, die an der Nutzerroute nicht beantwortbar ist, wird vor dem Lauf im Prozess des Containers gestellt statt nach dem Lauf geraten"
    - "Fail closed in der Oeffentlichkeit: faellt die Sonde aus, traegt die Rohdatei die Zeile vorlaufsonde: nicht verfuegbar und die Trennung unterbleibt sichtbar"
    - "Ein Loeschbefehl ohne Rueckleseprobe ist in den Betriebsskripten kein Nachweis; der Fall prueft die Reihenfolge und nicht die Anwesenheit"
    - "Ein Befehlsname steht in cmd_destroy nur einmal, sonst prueft eine Reihenfolgeprobe die Erwaehnung im Kommentar"

key-files:
  created:
    - .planning/phases/16-haertung-und-store-einreichung-v1-2-0/deferred-items.md
  modified:
    - scripts/ops/search_load.py
    - scripts/ops/aws_box.sh
    - backend/tests/test_ops_scripts.py

key-decisions:
  - "Die Sonde fragt nur die lexikalische Haelfte und uebergibt ranked_sides keine semantische Seite. Eine semantische Seite wuerde das Abfragemodell laden und genau den Container aufwaermen, dessen Speicher unmittelbar danach gelesen wird; die Diagnose-Route traegt denselben Satz. Die Kehrseite ist benannt: ein Begriff ohne lexikalischen Bestand kann von der Vektorhaelfte beantwortet werden, und eine leere Antwort auf ihn faellt auch dann unter ohne-treffer, wenn der Aufruf abgebrochen ist"
  - "Die Sonde laeuft VOR der ersten Speicherablesung und nicht danach. Sie beruehrt den lexikalischen Index selbst, und eine Ablesung nach ihr wuerde diese Beruehrung als Kosten der Last ausweisen"
  - "EmptyResultGroup behaelt seinen Namen und seine Gesamtzahl. Die Trennung kommt als eigener Schluessel empty_result_groups daneben, damit eine Rohdatei dieses Werkzeugs weiterhin gegen eine von vor dem 21.09.2026 gelesen werden kann; das ist die Haelfte von DI-10-01, die beim Schliessen von DI-11-03 nicht verloren gehen darf"
  - "Antwortet die Sonde nur fuer einen Teil der Begriffe, gilt sie als ausgefallen. Eine Trennung auf einem Teil der Begriffe schriebe zwei Lesarten in dieselbe Rohdatei"
  - "Die Sonde gibt bei einem Fehlschlag den Rueckgabewert weiter und nie die Fehlerausgabe des Containers: dieser Strom traegt Pfade der Maschine und moeglicherweise eine Zeile einer Konfiguration"
  - "Das Schluesselpaar wird nach Instanz und Datentraeger geloescht. Ein Abbruch dazwischen liesse sonst eine laufende Instanz zurueck, die niemand mehr betreten und damit auch von innen nicht mehr anhalten kann"
  - "Nur die oeffentliche Haelfte wird geloescht; die private Haelfte liegt auf der Maschine, die sie erzeugt hat, und ist nicht Sache dieses Werkzeugs"
  - "L-07 bekommt keinen eigenen Eintrag in deferred-items.md, sondern eine Zeile in der Adressliste: der Befund ist in diesem Plan gebaut, und ein zurueckgestellter Punkt, der nicht zurueckgestellt ist, waere eine falsche Zeile"

patterns-established:
  - "Vorlaufsonde: die Frage vor dem Lauf stellen, wenn die Antwort nach dem Lauf nicht mehr unterscheidbar ist"
  - "Ein Ausfall der Sonde ist eine Zeile in der Rohdatei und kein Abbruch des Laufs; die stille Rueckkehr zur alten Zaehlung waere der Befund selbst"

requirements-completed: []
requirements-partial:
  - "HART-01: die vier Punkte aus DI-11 haben ihr Verdikt, zwei davon gebaut (DI-11-03 hier, DI-11-05 in 16-01), zwei dokumentiert entschieden (DI-11-02 zu, DI-11-06 weitergereicht). Das Requirement wird erst in 16-13/16-14 abgehakt"

# Metrics
duration: 60 min
completed: 2026-09-21
---

# Phase 16 Plan 04: Die vier DI-11-Punkte und der vollstaendige Abbau Summary

Jeder der vier aufgeschobenen Punkte aus DI-11 hat sein Verdikt: DI-11-03 ist gebaut (eine Vorlaufsonde im Lastwerkzeug, die trefferlose Begriffe vor dem Lauf benennt), DI-11-02 ist mit Zahlen geschlossen, DI-11-06 ist mit Begründung und Zieladresse weitergereicht, DI-11-05 war schon in 16-01 erledigt. Dazu nimmt `cmd_destroy` jetzt das Schlüsselpaar mit und liest es zurück (L-07).

## Was gebaut wurde

**Task 1, die Vorlaufsonde des Lastwerkzeugs (DI-11-03), Commit `daa4661`.**

`scripts/ops/search_load.py` stellt vor der ersten Laststufe je Suchbegriff
einmal dieselbe Frage, die `73-bestand-sonde.py` im Prozess des Containers
stellt: wie viel ungedeckelten Bestand trägt der Index für diesen Begriff.
Gefragt wird über `ranked_sides`, also über die Funktion, mit der eine Suche
dieses Containers ihre beiden Listen baut, und der Weg dorthin ist `docker exec`
mit dem Interpreter des Abbildes, derselbe Weg, den `98c-sprachfaelle.sh` nimmt.
Das ist die Zutat, die DI-11-03 bisher gefehlt hat: von aussen ist die Frage
nicht beantwortbar, weil die OCS-Route einen abgebrochenen Containeraufruf und
eine Suche ohne Treffer mit demselben HTTP 200 und derselben Ergebnisgruppe ohne
Containerteil beantwortet.

Die drei Regeln des Plans halten:

1. Die Zeilen der Sonde stehen als **erster Schlüssel** des Berichts, also im
   Kopf der Rohdatei vor jeder Messzahl, mit dem Wort `vorlaufsonde`, dem
   Zeitstempel, der Liste der trefferlosen Begriffe und je Begriff einer Zeile
   mit Bestand und Fensterbelegung.
2. Die Antworten unter `--min-hits` werden getrennt gezählt. Der neue Schlüssel
   `empty_result_groups` trägt `gesamt`, `ohne-treffer` und `fehlschlag`;
   `failures`, `failure_kinds` und `EmptyResultGroup` bleiben unverändert
   daneben stehen, damit eine Rohdatei gegen eine ältere lesbar bleibt.
3. Fällt die Sonde aus, läuft der Lauf weiter, und die Rohdatei trägt die Zeile
   `vorlaufsonde: nicht verfuegbar` samt Grund; die beiden getrennten Zähler
   fehlen dann **namentlich** statt still durch die alte Zählung ersetzt zu
   werden (T-16-13).

Drei Wege des Ausfalls enden in derselben Zeile: kein Container genannt, das
Programm im Container mit einem Rückgabewert ungleich null, und eine Antwort für
weniger als alle Begriffe. Keiner von ihnen gibt die leere Menge zurück, denn
die leere Menge wäre die Behauptung, jeder Begriff habe Bestand.

**Task 2, der Abbau nimmt das Schluesselpaar mit (L-07), Commit `681097a`.**

`cmd_destroy` in `scripts/ops/aws_box.sh` löscht das Schlüsselpaar nach Instanz
und Datenträger, mit `ec2_soft`, so dass ein Fehlschlag eine Antwort und kein
Abbruch ist. Darauf folgt die Rückleseprobe in der Form der übrigen drei
Ressourcenarten: das Paar wird abgefragt, `resource_gone` liest
`InvalidKeyPair.NotFound` als `gone`, und das Ergebnis geht als eigene Zeile ins
Protokoll. Ein bereits fehlendes Paar endet damit in derselben Zeile und nicht
in einem Fehler. Der Kommentar nennt L-07 und den Handgriff aus 15-14, den der
Block ersetzt.

**Task 3, die dokumentierten Entscheide, Commit `4917463`.**

`.planning/phases/16-haertung-und-store-einreichung-v1-2-0/deferred-items.md`
trägt sieben Einträge, je mit Kennung, Befund in einem Satz, Verdikt, Begründung
und, wo weitergereicht, einer Zieladresse:

| Kennung | Verdikt | Zieladresse |
|---|---|---|
| DI-11-02 | dokumentiert entschieden, zu | keine |
| DI-11-03 | abgearbeitet (Task 1 dieses Plans) | keine |
| DI-11-05 | abgearbeitet (Plan 16-01, Flake-Register) | keine |
| DI-11-06 | dokumentiert entschieden, weitergereicht | eigener Milestone nach v1.2 |
| L-05 | dokumentiert weitergereicht | erster Plan der naechsten Anfahrt |
| L-06 | dokumentiert weitergereicht | erster Plan der naechsten Anfahrt |
| L-08 | benannte Asymmetrie, kein Fix | keine |

DI-11-02 ist mit Zahlen geschlossen und nicht mit Zuversicht: die v1.2-Anfahrt
ist mit `SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED` gefahren, die vier in
v1.1 regressiven Laststufen sind je mit "behoben" entschieden, und die
Gegenrechnung im Nextcloud-Protokoll zählt im Lastfenster 02:10 bis 02:13 **null**
`cURL error 28` (`rohdaten/97-nebenlaeufigkeit.txt`, Zeilen 147 und 148). Der
Satz, der dazugehört, steht mit dabei: die v1.1-Box trug diesen Stand nicht, der
alte Befund ist also nicht widerlegt, sondern überholt.

DI-11-06 trägt die Kehrseite ausdrücklich: solange die Versionsmarke so gepflegt
wird wie heute, braucht **jeder** Minor-Sprung eine Migration nach dem Muster von
`Version001100Date20260911000000`, und das ist der Grund, warum REL-02 eine
verlangt. Plan 16-07 schreibt diesen Satz im Klassenkommentar fort.

Die Kopfzeile der Datei nennt für jeden übrigen Befund der Phase-15-Liste den
Plan, der ihn trägt: L-03 und L-04 in 16-03, L-07 in diesem Plan, L-09 in 16-08,
L-10 in 16-02 und 16-05, L-11 in 16-01, M-01 in 16-06, M-02 in 16-02 und 16-05.
Damit ist die Befundliste des Phasenaudits 15 an einer Stelle vollständig
adressiert.

## Deviations from Plan

### 1. [Rule 2 - fehlende kritische Funktionalitaet] Fuenf Faelle ueber die neuen Zusagen statt keiner

- **Gefunden bei:** Task 1, beim Schreiben der Sonde.
- **Was:** Der Plan führt für Task 1 nur `scripts/ops/search_load.py` in den
  Dateien und verlangt lediglich, dass die bestehenden Fälle grün bleiben. Die
  Bedrohung T-16-13 (die Sonde fällt still aus und die alte Zählung kehrt
  unbemerkt zurück) wäre damit eine Zusage ohne Gate gewesen, und genau das ist
  der Befundtyp, den dieses Projekt an anderer Stelle anprangert.
- **Was daraus wurde:** Vier Fälle in `backend/tests/test_ops_scripts.py` halten
  die vier Zusagen fest: die Sonde benennt die trefferlosen Begriffe und
  schreibt je Begriff eine Zeile; drei Wege des Ausfalls enden in derselben
  Zeile und nie in der leeren Menge; der Bericht trennt `ohne-treffer` von
  `fehlschlag` und behält die Gesamtzahl; eine Rohdatei ohne Sonde trägt die
  Zeile und keinen Trennwert. Dazu zwei Zeilen im bestehenden Schlüsselfall,
  die den Kopf des Berichts (`vorlaufsonde` an Position null) und die Stellung
  von `empty_result_groups` neben `failure_kinds` halten.
- **Dateien:** `backend/tests/test_ops_scripts.py`
- **Commit:** `daa4661`

### 2. [Rule 1 - Bug] Der Befehlsname stand zweimal und machte die Reihenfolgeprobe falsch

- **Gefunden bei:** Task 2, beim ersten Lauf des neuen Falls.
- **Was:** Der Kommentar über dem neuen Block nannte `describe-key-pairs`
  namentlich. Die Reihenfolgeprobe des Falls sucht die erste Fundstelle, und die
  lag damit **vor** dem Löschbefehl; der Fall war rot, obwohl der Code richtig
  war.
- **Fix:** Der Kommentar spricht jetzt von der Antwort des Kontos statt vom
  Befehl. Das ist dieselbe grep-Hygiene, die dieses Repositorium in Plan 06-10
  für Textproben festgelegt hat: ein Name, den ein Fall als Ort liest, steht
  nicht zusätzlich in der Prosa daneben.
- **Commit:** `681097a`

Keine weiteren Abweichungen. Es gab keinen Authentifizierungsfall, keine
Paketinstallation und keine Architekturfrage.

## Verification

| Zusage | Nachweis |
|---|---|
| Die Sonde läuft vor der ersten Laststufe und schreibt ihre Liste in den Kopf der Rohdatei | `vorlaufsonde` ist Schlüssel null des Berichts, gehalten von `test_the_report_puts_the_hits_per_request_next_to_the_hits_total`; der Aufruf steht vor `before = _memory(cgroup)` |
| Sie fragt `ranked_sides` und schreibt je Begriff eine Zeile | `grep -c "ranked_sides" scripts/ops/search_load.py` = 5, `grep -c "DI-11-03"` = 7, Fall `test_the_probe_names_the_terms_the_index_holds_nothing_for` |
| Ausfall der Sonde bleibt sichtbar | Fall `test_the_probe_that_does_not_answer_says_so_instead_of_guessing` (drei Wege), Fall `test_a_report_without_a_probe_carries_the_line_and_no_split` prüft die Zeile im Dateitext |
| Zwei getrennte Zähler plus Gesamtzahl | Fall `test_the_report_splits_the_empty_groups_by_what_the_probe_found`: `{"gesamt": 2, "ohne-treffer": 1, "fehlschlag": 1}` neben `failure_kinds` mit `EmptyResultGroup: 2` |
| `cmd_destroy` löscht das Schlüsselpaar und liest es zurück | `grep -c "L-07" scripts/ops/aws_box.sh` = 2, Fall `test_the_aws_destroy_takes_the_key_pair_with_it_and_reads_it_back`, `sh -n` grün |
| `-k "destroy or key"` wählt mehr als null Fälle | 7 ausgewählt, 7 grün |
| Sieben Einträge mit Verdikt | 7 Überschriften, 7 Zeilen `**Verdikt`, Verify-Befehl des Plans grün (kein Em-Dash, kein En-Dash, kein gesperrtes Wort, reines ASCII) |
| Gates lokal grün | `ruff check`, `ruff format --check`, `PYRIGHT_PYTHON_FORCE_VERSION=latest pyright` (0 errors), `vulture src tests --min-confidence 80` |
| Volle Suite, Skipzahl unverändert | vorher 2.458 bestanden / 15 übersprungen, nachher **2.463 bestanden / 15 übersprungen** (+5 neue Fälle, Skipzahl gleich) |

## Known Stubs

Keine. Beide Werkzeuge sind vollständig verdrahtet; die Vorlaufsonde hat keinen
Platzhalterpfad und keinen Vorgabewert, der eine Messung vortäuschen könnte.

## Was offen bleibt

**Die Vorlaufsonde ist nicht gegen einen echten Container gefahren.** Auf dieser
Maschine gibt es weder Docker noch eine Box, und die bezahlte Box der Phase 15
ist abgebaut. Geprüft sind die Entscheidungen des Werkzeugs gegen gestellte
Antworten, die Syntax des Programms, das in den Container wandert
(`ast.parse`), und die drei Hausregeln der Betriebsskripte. Ob
`/app/.venv/bin/python -c` im laufenden Abbild die drei Importe findet, misst
erst die nächste Anfahrt; die Variable `FINDLING_PROBE_PYTHON` ist genau für den
Fall da, dass der Pfad dort ein anderer ist.

**`cmd_destroy` ist ebenso nur statisch geprüft.** Der Block wird beim nächsten
Abbau zum ersten Mal wirklich laufen. Das ist dieselbe Lage wie bei den
Nachfolgefassungen aus 16-03 und aus demselben Grund.

**DI-11-06 bleibt offen**, mit Verdikt und Zieladresse. Die Kehrseite, der
Migrationszwang je Minor-Sprung, wird in Plan 16-07 gebaut.

**L-05 und L-06 bleiben offen**, mit Adresse in der nächsten bezahlten Anfahrt.

## Self-Check: PASSED

Drei Commits vorhanden (`daa4661`, `681097a`, `4917463`), fuenf genannte Dateien
vorhanden, Verify-Befehle der drei Tasks gruen, volle Suite 2.463 bestanden /
15 uebersprungen.
