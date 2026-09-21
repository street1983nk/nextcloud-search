---
plan: 15-10
phase: 15-messphase-eine-box-anfahrt
status: complete
completed: 2026-09-20
requirements-completed: []  # MESS-05 an 15-16
---

# 15-10 SUMMARY: Zustandspruefung, Owner-Tor, Nullstand

## Owner-Entscheid am Abbruchtor (im Wortlaut, 20.09.2026)

Vorgelegt wurde: der Korpus ist beweisbar die richtige Box (52.114 Dokumente
unter home::lasttest, 20G ncdata, konsistent mit den 52.111 der
Snapshot-Beschreibung), Speicher/Kerne/Architektur/cgroup korrekt, Cron nach
dem Fix auf 300 s. ABER: das Abbruchtor des Runbooks (Abschnitt 5) will
52.111 indexiert sehen, und dieser Beleg ist nicht mehr ablesbar, weil Block
13b (in 15-09) planmaessig per unregister --rm-data das Backend-Datenvolume
mit dem fertigen Index geleert hat.

**Owner: "Weiter, Korpus als Beleg."** Der Korpus belegt die Box, der Index
wird ohnehin auf Null gesetzt. Der Tor-Widerspruch geht als Runbook-Befund an
15-15.

## Die sechs Vergleichbarkeitsgroessen (04-bestand-vor-der-messung.txt)

| Groesse | Soll | Ist |
|---|---|---|
| Korpus (Ersatz fuer indexiert) | 52.111 | 52.114 Dokumente, 20G |
| uebersprungen / fehlgeschlagen | 37 / 0 | Zwischenstand 44 / 6 (In-Arbeit des neuen Abbilds, Endzahl misst der Volllauf) |
| Gesamtspeicher | 3.9Gi | 3.9Gi |
| Kerne | 2 | 2 |
| Architektur | aarch64 | aarch64 |
| Instanztyp | m7g.large | m7g.large |
| cgroup memory.max / swap.max | 2147483648 / 0 | 2147483648 / 0 |
| Cron-Intervall | 300 s | 300 s |
| Entladeschalter | 0 | 0 |
| baumhash-gleich | ja | ja |

## Werkzeug-Fix in diesem Plan (mit Owner-Wort, Ausnahme No-Edit)

- 6f42c69: `97-cron-vorpruefung.sh` las das Intervall falsch (5 s statt
  300 s). Zwei Ursachen, beide auf der Box verifiziert: der `match()`-Ausdruck
  verlor unter mawk das `m` von `sleep 5m`, und der Anker `cron.php` traf auch
  die pgrep-Zeile des Trap-Handlers (`sleep 5`). Jetzt feldbasiert, verankert
  an der Aufrufzeile `php -f ... cron.php`, mit Einheitenuebersetzung s/m/h.
  Vorstufen d6fb185/... in 15-09.

## Nullstand (93-nullstand.txt)

Vor `--restart` war der Index NICHT null (der Poller hatte seit dem
Abbildwechsel 02:42 gebaut: state.db 528K, vectors.db 1.8M, tantivy 40
Dateien/23M) - ehrlich als solcher erfasst. `occ findling:index --restart -n`
hebt laut IndexCommand.php die Generation, sodass ALLE Dokumente neu gelesen
werden (Marken erst am Ende des Neubaus gestempelt); der Index wird also nicht
physisch getruncatet, aber jeder der 52k Dateien wird neu verarbeitet, was der
Volllauf messen soll. Nach der 360-s-Frist Arbeitsvorrat 500 und steigend
(`arbeitsvorrat-da ja`), rc=0. Der Neubau laeuft.

## Was verschoben wurde und warum

Die Bestandssonde (73-bestand-sonde.py, 15-10 Task 3) misst den
Sprachbegriff-Bestand im Index (Erwartung E1: je Begriff > 26 Treffer). Sie
setzt einen gebauten Index voraus, den Block 13b geleert hat; auf dem
mitten im Neubau stehenden Index misst sie Teilzahlen. Sie wandert deshalb
hinter den Volllauf (15-11), zusammen mit den Sprachfaellen (15-12), wo der
Index steht. Dieselbe Wurzel wie der Tor-Befund: Abschnitt 5/6 des Runbooks
stammt aus dem Ablauf ohne Abbildwechsel. Nachtrag 15-15.

## Verification

1. Sechs Zustandszahlen abgelesen und dem Owner vorgelegt: GRUEN.
2. cron-intervall-ist 300 (nach Fix): GRUEN.
3. Nullstand belegt (Generation gehoben, Warteschlange gefuellt): GRUEN.
4. Bestandssonde: nach hinten gestellt (Index-Voraussetzung), begruendet.
5. Geheimnis-Gate ueber 04-bestand und 93-nullstand leer.

## Naechster Schritt

15-11: Volllauf detached anstossen (96-volllauf.sh) mit Waechter und
Beobachtern. Laufzeit rund 26 h. Indexiert-am-Trigger > 0 (Poller-Vorlauf),
daher ist die gemessene Laufzeit eine UNTERGRENZE, wie 96-volllauf.sh es fuer
diesen Fall selbst vorschreibt.
