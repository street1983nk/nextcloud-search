# Der Abgleich: warum er existiert, wie sein Takt entsteht und wo sein Cursor liegt

Diese Seite beschreibt den ETag-Abgleich (IDX-04, IDX-05): den nächtlichen
Vergleich zwischen der Dateiliste von Nextcloud und dem, was der Container
indexiert hat. Sie ist für zwei Leser geschrieben. Für den Admin, der wissen
will, was da jede Nacht läuft und woran er drehen kann. Und für den Entwickler,
der in einem Jahr auf eine Regelabweichung stößt und sonst annehmen müsste, sie
sei ein Versehen.

## Warum es den Abgleich gibt

Ereignisse sind ein Beschleuniger, nie eine Garantie.

Der übliche Weg einer Änderung ist schnell: jemand speichert eine Datei,
Nextcloud löst ein Ereignis aus, die Companion-App reiht eine Zeile in die
Warteschlange ein, der Container liest sie und schreibt den Index fort. Unter
einer Minute, so steht es in D-01.

Dieser Weg hat aber Lücken, und alle sind Alltag:

- Ein Massenimport über `occ files:scan` erzeugt keine Ereignisse.
- Eine Wiederherstellung aus dem Backup erzeugt keine Ereignisse.
- Ein Listener, der nach einem Update nicht mehr registriert ist, liefert nichts,
  und niemand merkt es.
- Der Papierkorb wird geleert, während der Container gestoppt ist.
- Eine Zeile geht schlicht verloren.

In all diesen Fällen bleibt der Index dauerhaft falsch, und zwar lautlos. Kein
Zähler bewegt sich, keine Fehlermeldung entsteht. Auffallen tut es dem Nutzer,
der eine Datei sucht, die es gibt, und sie nicht findet. Genau diese Klasse hat
das Vorgängerprojekt unbrauchbar gemacht, an dem dieses hier sich abarbeitet.

Der Abgleich ist die Antwort darauf. Er verspricht: nach einem einzigen
vollständigen Zyklus ist der Index korrekt, auch wenn kein einziges Ereignis
angekommen ist.

## Wie er arbeitet

Der Container zieht, die PHP-App liefert nur. Der Ablauf je Scheibe:

1. Ruhe-Gate prüfen. Steht mehr Arbeit in der Warteschlange als
   `FINDLING_RECONCILE_QUIET_MAX` erlaubt, passiert nichts.
2. Taktprüfung gegen die eigene Uhr und die Zeitstempel in der Tabelle
   `reconcile` der Container-Datenbank.
3. Die Mountliste holen (`GET /mounts`).
4. Je Mount eine nach Datei-Id aufsteigende Seite holen
   (`GET /files/slice?storage=&root=&after=&limit=`). Die Seite meldet selbst,
   ob hinter ihr noch etwas liegt.
5. Vergleichen: eine unbekannte Datei-Id oder ein abweichender ETag wird zur
   Inhaltsaufgabe; eine lokal bekannte Datei im Bereich der Seite, die nicht in
   der Seite steht, wird zur Löschaufgabe.

   Eine Ausnahme, und sie ist die vierte Grenze: trägt die Seite für eine dem
   Container völlig unbekannte Datei das Endurteil `failed(repeatedly_stuck)`
   der Nextcloud-Seite, wird sie nicht eingereiht. Der Container merkt sich das
   Urteil in seiner eigenen Tabelle `files`, und zwar gegen den ETag der Seite.
   Damit gilt es genau so lange, wie die Datei sich nicht ändert: ein neuer ETag
   erreicht den zweiten Zweig als gewöhnliche Arbeit, und ein Requeue von Hand
   wirkt ohnehin, weil er die Datei über die Warteschlange ausliefert.

   Ohne diese Regel war das Endurteil für abgleich-gefundene Dateien nie
   endgültig: die Aufgabe-Regel läuft in `QueueService::claim`, ihre Queue-Zeile
   verschwindet dabei, und der Container erfuhr davon nichts. Jede Nacht fand
   der Vergleich dieselbe kaputte Datei unindexiert, reihte sie ein, und
   dieselben drei Auslieferungen endeten wieder mit demselben Urteil. Auf
   50.000 Dateien ist das Dauerlast, deren Ursache in keinem Zähler der App
   sichtbar ist.
6. Beides über `POST /queues/documents/requeue` einreihen, getrennt nach Art.
7. Cursor fortschreiben, kurz pausieren, nächste Scheibe.

Drei Grenzen sind dabei die eigentliche Arbeit, weil der Abgleich als einziger
Teil des Systems aus einer Abwesenheit etwas folgert:

- **Die obere Grenze.** Eine Datei hinter dem Ende der Seite gilt nie als
  gelöscht. Nur eine Seite, die ausdrücklich meldet, die letzte zu sein, darf
  ohne obere Grenze urteilen.
- **Die Vollständigkeit.** Musste die Client-Schicht eine Zeile der Antwort
  verwerfen, weil ihr ein Feld fehlte, ist die Seite unvollständig. Sie darf dann
  aktualisieren und einreihen, aber niemals löschen: eine verworfene Zeile sieht
  genauso aus wie eine gelöschte Datei.
- **Der Transportfehler.** Eine Seite, die nie ankam, beendet die Runde, ohne den
  Cursor zu bewegen. Aus einer ausgebliebenen Antwort folgt nichts.

## Warum der Abgleich nichts in den Index schreibt

Es gibt genau einen Index-Schreiber im Prozess, und er gehört dem Poller. Ein
zweiter wäre ein Sperrkonflikt in Tantivy und würde die Indexierung anhalten.

Der Abgleich schreibt deshalb nie in den Index. Er erzeugt Aufträge, und die
Zweige des Pollers erledigen sie: `kind=content` liest die Datei neu ein,
`kind=delete` nimmt das Dokument aus dem Index, vergisst die Berechtigungen und
setzt den Grabstein. Die erwünschte Nebenwirkung ist, dass der Löschweg genau
einmal existiert statt zweimal.

## Warum der Cursor im Container liegt

Überall sonst in diesem Projekt gilt: Fortschritt gehört in die Datenbank von
Nextcloud, nicht in den Container. Der Crawl-Cursor liegt aus gutem Grund im
Argument des nächsten Hintergrundjobs.

Der Abgleich ist die eine bewusste Ausnahme, und der Grund ist der Unterschied im
Schaden. Ein verlorener Crawl-Cursor bedeutet ein Dokument, das nie jemand
indexiert. Ein verlorener Abgleich-Cursor bedeutet, dass ein Mount noch einmal
gelesen wird. Der Abgleich ist reine, wiederholbare Reparatur: zweimal
ausgeführt liefert er dasselbe Ergebnis wie einmal ausgeführt. Ein verlorener
Cursor kostet also eine Wiederholung und nie Arbeit.

Die Alternative wäre gewesen, die PHP-Seite den Abgleich fahren zu lassen. Das
scheitert an drei Punkten, in aufsteigender Härte: die Zustandstabelle in
Nextcloud kennt gar keine indexierten Zeilen und könnte "im Index, aber nicht
mehr da" nicht bilden; ein Hintergrundjob hat keinen Nutzer und bräuchte eine
öffentlich erreichbare Route im Container; und der Requeue-Schreibweg, den der
Abgleich braucht, existiert für die OCR-Übergabe ohnehin schon.

## Wie der Takt zustande kommt

Der Takt liegt im Container. Ein PHP-Job könnte den Container nicht wecken, und
D-01 verbietet ausdrücklich einen zweiten Weckkanal.

Die Regel lautet: höchstens ein vollständiger Zyklus je
`FINDLING_RECONCILE_MIN_INTERVAL_HOURS`, bevorzugt in der Stunde
`FINDLING_RECONCILE_HOUR` der Containerzeit, und nur bei ruhiger Warteschlange.
Dazu zwei Sonderfälle, die beide nötig sind:

- Eine Runde, die mitten in einem Mount abgebrochen ist, darf sofort weiterlaufen.
  Ein halber Vergleich ist weniger wert als gar keiner.
- Ist die doppelte Mindestpause verstrichen, läuft der Zyklus unabhängig von der
  Stunde. Sonst verlöre eine Box, die nur tagsüber eingeschaltet ist, die
  Garantie ganz.

### Warum das Wartungsfenster von Nextcloud nicht reicht

Es liegt nahe, den Abgleich als zeitunkritischen Nextcloud-Job zu markieren und
darauf zu vertrauen, dass er dann nachts läuft. Das ist auf einer frisch
installierten Instanz falsch.

`cron.php` liest `maintenance_window_start` mit dem Vorgabewert 100, und die
Einschränkung greift nur, wenn die Startstunde bei 23 oder darunter liegt. Ohne
ausdrückliche Konfiguration durch den Admin gibt es also überhaupt kein
Wartungsfenster, und ein "nächtlicher" Job läuft mittags.

Wer `maintenance_window_start` setzt, verschiebt damit auch die Last dieses
Abgleichs. Das ist ein Hinweis und keine Pflichtkonfiguration: Findling soll ohne
Konfiguration funktionieren, deshalb ist der Container so gebaut, dass er auch
mittags erträglich ist. Dafür sorgen die Seitengröße, die Pause zwischen den
Scheiben und vor allem das Ruhe-Gate, das vor jeder einzelnen Scheibe erneut
geprüft wird. Ein Abgleich, der nur nachts erträglich ist, ist ein Abgleich, den
ein Admin abschaltet.

## Die Einstellungen

Alle fünf stehen in der `info.xml` des Backends und werden von `config.py`
gelesen. Ein unbrauchbarer Wert stoppt den Container nie: er fällt auf die
Vorgabe zurück und schreibt den Namen der Variablen ins Protokoll, nie ihren
Wert.

| Variable | Vorgabe | Wirkung |
|---|---|---|
| `FINDLING_RECONCILE_ENABLED` | `true` | Schaltet den Abgleich ganz ab. Aus heißt: der Index ist nur so gut wie der Ereignisstrom. |
| `FINDLING_RECONCILE_HOUR` | `2` | Bevorzugte Stunde der Containerzeit, 0 bis 23. |
| `FINDLING_RECONCILE_MIN_INTERVAL_HOURS` | `24` | Mindestabstand zwischen zwei vollständigen Zyklen. |
| `FINDLING_RECONCILE_QUIET_MAX` | `100` | Wartende Zeilen, ab denen der Abgleich aussetzt (D-03). |
| `FINDLING_RECONCILE_SLICE` | `500` | Dateien je Seite. Die PHP-Seite klemmt jeden Wert über 2000. |

## Was der Abnahmetest prüft

Der Abnahmetest aus IDX-04 lautet wörtlich: Ereignisse blockiert, ein
Abgleichzyklus, Index korrekt.

Konkret heißt das drei Schritte. Erstens werden die Ereignisse ausgeschaltet,
etwa indem der Listener nicht registriert wird oder die Dateien am Listener
vorbei angelegt werden. Zweitens wird eine Datei angelegt, eine geändert und eine
gelöscht. Drittens läuft genau ein Abgleichzyklus, und danach muss die neue Datei
auffindbar sein, die geänderte mit ihrem neuen Inhalt gefunden werden und die
gelöschte in keinem Treffer mehr auftauchen.

Der Schritt gehört neben den bestehenden Ende-zu-Ende-Job in
`.github/workflows/integration.yml`. Was ein Test in diesem Repository allein
nicht zeigen kann, ist das Zusammenspiel mit einer echten Instanz, und genau
darum steht er dort und nicht nur in der Python-Suite.

## Was im Protokoll steht

Ausschließlich Zähler: Mounts, Scheiben, gesehene Dateien, eingereihte Dateien je
Art. Kein Pfad, kein Dateiname, kein Titel. Die Dateiliste ist das Privateste,
was dieser Container liest, und ein Protokoll, das sie mitschreibt, wäre eine
Preisgabe (T-03-1205). Ein Test prüft das mit einem Grep über das Modul, weil
diese Regel nicht absichtlich gebrochen wird, sondern beim Hinzufügen eines
hilfreichen Details.
