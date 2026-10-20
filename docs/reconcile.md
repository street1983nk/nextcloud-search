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

   Und eine Ausnahme von dieser Ausnahme, siehe den nächsten Abschnitt: trägt
   der Container für dieselbe Datei `skipped(no_text_layer)`, ist das
   Endurteil der Nextcloud-Seite kein Endurteil, sondern eine verlorene
   Übergabe an die OCR-Spur, und die Datei wird eingereiht.

   Und eine Datei unter einer Ausschlussregel folgt eigenen Regeln, siehe den
   Abschnitt "Dateien unter einer Ausschlussregel (D-33-01)".
6. Beides über `POST /queues/documents/requeue` einreihen, getrennt nach Art.
7. Cursor fortschreiben, kurz pausieren, nächste Scheibe.
8. Nach dem letzten Mount einer vollständig gelaufenen Runde: der Nachlauf über
   Speicher, die nicht mehr gelistet sind (`GET /storages/gone?ids[]=`), siehe
   den Abschnitt "Gelöschte, abgewählte und verschwundene Speicher (M-32-02)".

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

## Die verlorene Übergabe an die OCR-Spur, und wie sie sich selbst heilt

Ein Durchgang des Pollers schreibt in vier Schritten: erst das Verdikt in den
Index, dann den Commit, dann das Verdikt in die Zustandsdatenbank, zuletzt die
Quittierung an Nextcloud. Für einen Scan bedeutet das zwei Zeilen an zwei
Stellen: der Container hält `skipped(no_text_layer)`, und aus der Quittierung
entsteht der OCR-Auftrag.

Stirbt der Durchgang zwischen diesen beiden Schritten, bleibt genau eine Hälfte
stehen. Der Container hat sein Verdikt, die OCR-Aufgabe gibt es nie, und die
Queue-Zeile läuft in die Sperrfrist. Passiert das in einer Phase, in der die
Nextcloud-Seite die Zeile abschreibt, weil ihr Auslieferungsbudget verbraucht
ist, entsteht das Paar aus DI-05-23:

| Wer | Urteil |
|---|---|
| Container | `skipped(no_text_layer)` |
| Nextcloud | `failed(repeatedly_stuck)` |

Vor Plan 05-20 war diese Datei damit für immer aus dem Index heraus, und zwar
ohne dass irgendein Zähler es gezeigt hätte. Der Abgleich sah eine bekannte
Datei mit unverändertem ETag, also nichts zu tun; und selbst wenn er sie nicht
gekannt hätte, hätte das abschreibende Endurteil der Seite ihn abgehalten. Beide
Regeln sind einzeln richtig und zusammen genau falsch.

**Was jetzt passiert.** Der Vergleich erkennt das Paar, bevor eine der beiden
Regeln greift, und reiht die Datei als Inhaltsaufgabe ein. Der nächste Durchgang
liest sie neu, findet dieselbe fehlende Textschicht, übergibt sie an die
OCR-Spur, und ab da hat der Container ein eigenes Urteil über die Datei. Damit
feuert der Zweig nicht wieder: eine Reparatur, die jede Nacht läuft, wäre ein
nächtlicher Download jedes Scans der Instanz.

**Wie eng der Zweig ist**, und jede Bedingung schließt genau einen Rückfall aus:

- Der ETag muss übereinstimmen. Eine geänderte Datei ist gewöhnliche Arbeit, und
  eine hier unbekannte Datei ist die Aufgabe-Regel des vorigen Abschnitts.
- Das Urteil des Containers muss der Übergabepunkt sein. `failed(corrupt)` neben
  der Abschreibung sind zwei Hälften, die sich einig sind, dass die Datei nicht
  lesbar ist.
- Die Nextcloud-Seite muss die Zeile abgeschrieben haben. Ein Scan mit lebender
  Queue-Zeile wartet einfach auf seinen OCR-Auftrag.
- OCR muss eingeschaltet sein. Mit `FINDLING_OCR_ENABLED=false` gibt es keine
  zweite Spur, und dann ist `skipped(no_text_layer)` das Endurteil und nichts,
  was man heilen könnte.

**Der Zweitweg bleibt.** `occ findling:index --restart` fängt dieselben Dateien
ein, weil der Neuaufbau jede Datei neu beurteilt. Er ist der schnelle Weg, wenn
jemand die Fehlerliste ansieht und nicht bis zur nächsten Nacht warten will; der
Abgleich ist der Weg, der auch ohne Zuschauer funktioniert.

## Dateien unter einer Ausschlussregel (D-33-01)

Die Regeln selbst kennt nur die PHP-Seite: Ordner-Präfixe und seit 1.5
Ausschlussmuster (`docs/admin-page.md`, Abschnitt "Ausschlussmuster"). Der
Container trägt keine Präfixliste und kein Muster und vergleicht keinen Pfad. Die
Seite des Abgleichs liefert jede Datei des Mounts, auch die ausgeschlossenen, und
markiert eine Datei unter einer Regel von heute live mit `skipped(excluded)`.
Der Container liest nur diese Marke.

**Die Regel seit dem Owner-Entscheid vom 13.10.2026 (D-33-01):** eine Datei, die
der Container kennt und die die Seite markiert, wird beim nächsten Abgleich aus
dem Index entfernt, ob sie sich geändert hat oder nicht. Die Regel von heute
entscheidet. Der Ablauf:

1. Der Vergleich macht aus der bekannten Datei unter der Marke eine
   Inhaltsaufgabe. Der Zweig steht vor dem ETag-Vergleich; ein gleicher ETag hält
   die Datei also nicht mehr im Index. Bekannt heißt: eine lebende Zeile in der
   Tabelle `files`, ein Grabstein zählt nicht.
2. Die PHP-Seite macht beim Abholen (`QueueService::describe()`) aus dieser
   Aufgabe den Löschauftrag, weil die Datei unter einer Regel liegt.
3. Der Poller nimmt das Dokument aus dem Index, vergisst die Berechtigungen und
   setzt den Grabstein.
4. Ab der nächsten Runde ist die Datei für den Container unbekannt und trägt die
   Marke. Dieser Fall bleibt liegen und wird nicht wieder eingereiht.

Die Urteilszeilen der Datei in `findling_file_state` verschwinden dabei mit,
`skipped(no_text_layer)` eingeschlossen: beim Abholen in `describe()` und schon
beim Lesen der Seite für jede Zeile, die sie als ausgeschlossen markiert. Die
Fehlerliste der Verwaltungsseite zeigt danach keine alten Einträge
ausgeschlossener Dateien mehr (Issue #22).

**Was vorher galt.** Der Owner-Entscheid vom 03.10.2026, Teil a (Lauf 7 der
28-07-Kette), regelte nur die dem Container unbekannte Datei unter einer Regel:
sie wird nicht eingereiht und nicht gespeichert. Vorher war sie jede Runde
eingereiht, beim Abholen gelöscht und in der nächsten Runde wieder unbekannt
gefunden worden; diese Menge brach das Ruhe-Gate, und die Runde kam bei jedem
Takt zurück. Den Fall "bekannt und unverändert" regelte der Entscheid nicht, und
der ETag-Vergleich ließ so eine Datei im Index. Ein neuer Ausschluss räumte den
Bestand deshalb nur über den Teilbaum-Job beim Speichern, und was der nicht sah,
blieb für immer auffindbar. D-33-01 erweitert Teil a um genau diesen Fall, im
Sinn des Entscheids.

**Warum der Abgleich dieses Netz sein muss.** Das Räumen beim Speichern (der
Teilbaum-Job für Präfixe, der Kehrjob für Muster) sieht nur, was im Moment des
Speicherns da ist und über die Seite gespeichert wurde. Der Abgleich fängt den
Rest ein:

- eine Regel, die per `occ config:app:set` gesetzt wurde,
- ein Mount, der nach dem Speichern auftaucht, etwa ein neuer Nutzer oder ein
  eingeschalteter Team Folder,
- ein Ordner, der innerhalb eines Mounts unter eine Regel umbenannt wird; der
  Ereignis-Listener markiert dann nur die Zählung als veraltet.

Das gilt für Präfixe und Muster gleich. Die Verzögerung ist der Takt des
Abgleichs, also bis zu `FINDLING_RECONCILE_MIN_INTERVAL_HOURS`, bevorzugt in der
Stunde `FINDLING_RECONCILE_HOUR` und nur bei ruhiger Warteschlange.

**Kein Schleifenrisiko.** Die Mitgliedschaft in den lebenden Zeilen ist die
Bremse: nach dem Grabstein ist die Datei unbekannt und fällt in den Zweig, der
nichts tut. Viele bekannte Dateien unter einer neuen Regel werden in Bändern zu
höchstens 200 Aufträgen eingereiht, und das Ruhe-Gate vor der nächsten Seite
beendet die Runde, bis der Poller sie abgearbeitet hat.

**Der Rückweg.** Eine zurückgenommene Regel nimmt die Marke mit, weil sie live
berechnet und nie gespeichert wird. Im nächsten Zyklus ist die Datei unbekannt
ohne Marke, also gewöhnliche Arbeit, und sie kommt in den Index zurück.

## Gelöschte, abgewählte und verschwundene Speicher (M-32-02)

Bis 1.4 lief der Abgleich nur über die Mounts, die die Liste trägt. Ein Speicher,
der nicht mehr gelistet ist, hat keine Seite, die "gelöscht" sagen könnte: die
Dokumente eines gelöschten Nutzers oder eines entfernten externen Speichers
blieben für immer Kandidaten der Suche. Die PHP-Endprüfung hat sie nie
ausgeliefert, aber sie belegten Plätze im Kandidatenfenster.

Seit 1.5 folgt auf jede vollständig gelaufene Runde ein Nachlauf. Er läuft nur,
wenn alle drei Bedingungen gelten: die Runde endete als `walked`, die Mountliste
war nicht leer, und die Client-Schicht musste keinen Eintrag verwerfen. Eine
leere, unvollständige oder unerreichbare Liste löscht nie etwas, weil sie genauso
aussieht wie eine Instanz, deren Speicher alle verschwunden sind.

Der Ablauf:

1. Speicher, die wieder gelistet sind, verlieren ihren Erstsichtungs-Stempel.
2. Lesezeichen (`reconcile`, `mounts`) von Speichern, die weder gelistet sind
   noch lebende Zeilen haben, werden entfernt. Das schließt Befund F4: ein
   Speicher, der mitten im Walk verschwand, ließ eine Zeile mit
   `after_file_id > 0` zurück, und der Takt hielt die Runde deshalb in jedem
   Tick für unterbrochen.
3. Für alle übrigen nicht gelisteten Speicher mit lebenden Zeilen fragt der
   Container `GET /storages/gone?ids[]=...`, in Bändern zu 256 (die Grenze von
   `ReconcileController::MAX_STORAGE_IDS`). Die Antwort ist
   `{"gone": [int], "deselected": [int]}`. `gone` sind Speicher ohne Zeile in
   `oc_storages`, `deselected` sind Speicher, die nur noch ein per
   Findling-Schalter abgewählter Anbieter trägt (D-36-14). Zahlen, nach denen
   nicht gefragt wurde, verwirft der Container.
4. `gone` und `deselected` verlieren ihre Dokumente sofort. Jeder andere
   Speicher bekommt beim ersten Fehlen einen Stempel in der Tabelle
   `vanished_storages` und verliert seine Dokumente erst, wenn dieser Stempel
   30 Tage alt ist (D-36-05). Die 30 Tage sind fest und haben keinen Schalter.
   Ein externer Speicher, der eine Woche nicht erreichbar ist, kostet so kein
   einziges Dokument.
5. Löschen heißt auch hier: Löschaufträge über `POST /queues/documents/requeue`
   mit `kind=delete`, in Bändern zu 200. Erst wenn alle Bänder eines Speichers
   angekommen sind, vergisst der Container dessen Lesezeichen und Stempel.
   Scheitert ein Band, endet der Nachlauf, und die nächste fällige Runde
   versucht es erneut.

Jede Fehlantwort der Route ist "keine Antwort": ein Transportfehler, eine falsche
Form, eine Nicht-Ganzzahl, und auch das 404 eines Companions der Reihe 1.4.x, der
die Route noch nicht kennt. Dann gelten alle fehlenden Speicher als verschwunden,
und es greift nur die Karenz. Ein Verlust der Tabelle `vanished_storages` setzt
die Karenz neu und kostet nie ein Dokument.

## Warum der Abgleich nichts in den Index schreibt

Es gibt genau einen Index-Schreiber im Prozess, und er gehört dem Poller. Ein
zweiter wäre ein Sperrkonflikt in Tantivy und würde die Indexierung anhalten.

Der Abgleich schreibt deshalb nie in den Index. Er erzeugt Aufträge, und die
Zweige des Pollers erledigen sie: `kind=content` liest die Datei neu ein,
`kind=delete` nimmt das Dokument aus dem Index, vergisst die Berechtigungen und
setzt den Grabstein. Die erwünschte Nebenwirkung ist, dass der Löschweg genau
einmal existiert statt zweimal.

## Die Wiederherstellung aus dem Papierkorb: was sofort passiert

Ein Nutzer holt einen Ordner aus dem Papierkorb zurueck. Das ist keine
Reparatur, sondern eine Absicht, und sie wird darum nicht vom Abgleich
getragen, sondern vom Ereignisweg.

**Was sofort passiert.** `NodeRestoredEvent` trifft die Companion-App. Fuer eine
einzelne Datei reiht sie eine Inhaltsaufgabe ein, fuer einen Ordner denselben
Teilbaum-Job, den auch die Ordner-Freigabe und die Ordner-Loeschung benutzen,
mit dem wiederhergestellten Ordner als Wurzel und `kind=content`. Der Job loest
die Nachkommen bandweise auf und gibt jedem eine Inhaltsaufgabe. Die Dateien
sind damit nach dem naechsten Poller-Durchgang wieder auffindbar und nicht nach
dem naechsten Abgleichzyklus.

Inhaltsaufgaben sind fuer einen Teilbaum die Ausnahme und gelten nur hier: die
Nachkommen eines geloeschten Ordners hat der Container aus dem Index genommen
und mit einem Grabstein versehen, ihr Text ist also wirklich weg. Bei einer
Umbenennung oder einer Freigabe ist er es nicht, und dort bleibt es bei den
Arten, die nichts neu lesen.

**Gemessen am 03.09.2026** auf einer lokalen Instanz (Ordner mit drei Dateien,
Warteschlange vorher leer, kein Abgleich angestossen):

| Schritt | Zeilen in der Warteschlange |
|---|---|
| Ordner geloescht, Teilbaum abgearbeitet | 4 mal `delete` |
| Warteschlange geleert, Ordner wiederhergestellt, vor Plan 05-04 | 0 |
| dasselbe mit dem Teilbaum-Job der Wiederherstellung | 3 mal `content`, mit ihrer echten Groesse |

**Was der Abgleich zusaetzlich abdeckt.** Alles, was am Ereignis vorbeigeht: der
Papierkorb wird geleert oder geraeumt, waehrend der Container steht; jemand
spielt ein Backup zurueck; der Listener ist nach einem Update nicht registriert;
eine Zeile geht verloren. In diesen Faellen ist der Abgleich der einzige Weg
zurueck.

**Die Grenze.** Der Abgleich ist die Sicherung, nicht der Weg. Wer die
Wiederherstellung ihm allein ueberlaesst, verspricht dem Nutzer Sekunden und
liefert bis zu einen Tag.

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

Ruhig heißt dabei zweierlei: weniger wartende Zeilen als
`FINDLING_RECONCILE_QUIET_MAX` und kein unfertiger Crawl. Den Crawl-Zustand
meldet die Companion-App in der Zähler-Antwort als `crawling` (geplanter
`SchedulerJob`, wartende Crawl-Zeile oder gehaltene Scheiben-Sperre). Eine leere
Warteschlange während der Erstindexierung ist keine ruhige Instanz: ein Worker,
der schneller abarbeitet als der Cron-getaktete Crawl liefert, hätte den Abgleich
sonst vorauslaufen lassen, und jede noch nicht gecrawlte Datei wäre zweimal
eingeplant worden (Lauf 8 der Abnahme-Anfahrt, 5000 Durchgänge mit Ergebnis
"unchanged"). Das Protokoll sagt dann
`reconcile stands down, the crawl is unfinished`.

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

## Der einmalige Nachholzyklus nach dem Upgrade auf 1.5

Release 1.5 liest Mails (.eml), ZIP-Dateien, Word und Excel 97 bis 2003 (.doc,
.xls) sowie HEIC/HEIF-Fotos, dazu Word- und Excel-Container unter einem
OOXML-Namen. Der Bestand einer Instanz wird nach dem Upgrade ohne Eingriff des
Admins nachgeholt (FMT-06, D-31-01). Dafür gibt es zwei Teile unter dem
Meta-Schlüssel `recheck_1_5_0` in `state.db`.

**Teil A, Durchlauf über state.db.** Der Poller reiht in Bändern zu höchstens
200 Dateien einmal neu ein:

- `skipped(legacy_format)`, außer PowerPoint (ein altes PowerPoint-Format bleibt
  auch unter 1.5 `legacy_format`),
- jede nicht indexierte Zeile mit einem der sechs neuen Typen. Solche Zeilen
  entstehen nur im Mischfenster, in dem eine 1.5-Companion die neuen Typen
  schon einreiht, ein 1.4.2-Container sie aber als `mime_not_allowed` speichert,
- einmal jede Zeile `failed(repeatedly_stuck)` (D-31-02). Die häufigste Ursache,
  eine veraltete Größe im Dateicache, behebt 1.5 (POL-02).

Teil A startet erst, wenn die Companion Generation 3 meldet und die
Nachprüfung von 1.4 (`recheck_1_4_0`) fertig ist.

**Teil B, ein sofort fälliger Abgleichzyklus.** Die Dateien der neuen Typen
hatten unter 1.4.2 nie eine Zeile im Container, weil die Companion sie gar
nicht eingereiht hat. Nur die Dateiliste findet sie. Deshalb ist nach Teil A
ein Zyklus sofort fällig, unabhängig von Stunde und Mindestpause. Er vergleicht
wie jeder Zyklus nur Metadaten. Das Ruhe-Gate gilt weiter, der Zyklus wartet
also auf eine ruhige Warteschlange. Der erste Durchgang unter der Marke
beginnt jeden Mount von vorn, damit kein halber Zyklus von vorher mitzählt.

Für die Dauer dieses einen Zyklus gelten zwei enge Ausnahmen:

- **Abgeschriebene Dateien ohne Containerzeile.** Hat Nextcloud eine Datei nach
  dem letzten Zyklus von 1.4.2 als `repeatedly_stuck` abgeschrieben, kennt der
  Container sie nicht, und Teil A sieht sie nicht. Ein gewöhnlicher Zyklus
  übernimmt das Endurteil (die vierte Grenze unter "Wie er arbeitet"). Im
  Nachholzyklus reiht er sie stattdessen ein und schreibt nichts. Scheitert sie
  wieder, übernimmt der nächste gewöhnliche Zyklus das Endurteil wie bisher.
  Als Dauerregel brächte die Ausnahme die Dauerlast aus IN-03 zurück, deshalb
  gilt sie nur unter der Marke. Solange der Nachholweg offen ist (Teil A läuft
  oder die Marke steht auf `reconcile`), lässt eine gewöhnliche Runde, die vor
  der Marke begann, solche Dateien ganz liegen: sie schreibt kein Endurteil und
  reiht nichts ein. So bekommt jede Datei ihre zweite Chance genau einmal, im
  Nachholzyklus, auch wenn Teil A mitten in einer laufenden Runde fertig wird
  (Audit 31-15, M-31-01).
- **Falsche Upgrade-Reihenfolge.** Lief eine 1.5-Companion vor dem
  1.4.2-Container, hat der Container die Codes `system_file`, `legacy_format`
  und `unsupported_variant` als 1.3-Ersatz gemeldet (`mime_not_allowed` bzw.
  `image_not_ocrable`). Eine Datei wird nur dann neu beurteilt, wenn der
  Container einen der drei Codes hält und die Nextcloud-Zeile genau dessen
  Ersatzcode trägt. Bei der richtigen Reihenfolge (docs/formats.md, "Upgrade
  order") sind sich beide Seiten einig, und es wird nichts neu gelesen.

**Was nicht passiert.** Kein Vollcrawl, keine Neu-Einbettung, keine Änderung an
indexierten Zeilen, an der Indexgeneration oder an den Vektormarken. Ein
Vollcrawl würde jede Datei der Instanz neu herunterladen, weil der Schnellweg
erst nach dem Download über den Inhalts-Hash vergleicht.

**Auch bei abgeschaltetem Abgleich.** Steht `FINDLING_RECONCILE_ENABLED` auf
`false`, startet der Container trotzdem einen Abgleich im Einmal-Modus. Er
wartet auf Teil A, fährt genau einen Zyklus und endet. Danach bleibt der
Abgleich aus, wie eingestellt. Das Protokoll nennt beide Zeilen:
`findling reconcile is switched off, the index follows events only` und
`one catch-up cycle after the upgrade runs once`. Für alles andere, was den
Abgleich als abgeschaltet erkennt, bleibt er abgeschaltet. Auch dieser Task
läuft nur, solange das Backend aktiviert ist.

**Die Werte der Marke.**

| Wert | Bedeutung |
|---|---|
| fehlt | Teil A hat nicht begonnen |
| Ziffern | Cursor von Teil A, die letzte Datei-ID, deren Band angekommen ist |
| `reconcile` | Teil A ist fertig, der Nachholzyklus ist fällig oder läuft |
| `done` | ein Nachholzyklus ist vollständig durchgelaufen, nichts davon läuft je wieder |

Ein unbekannter Wert startet Teil A wieder bei null.

**Wo der Admin den Stand sieht.** Im Containerprotokoll stehen nur Zahlen:
`the catch-up after the upgrade handed N files back in M bands, one reconcile
cycle follows` nach Teil A und `the catch-up cycle after the upgrade is
complete` nach Teil B. Die Marke selbst steht in der Tabelle `meta` von
`state.db` im Volume des Containers. `occ findling:diagnose` zeigt sie nicht.

## Die Einstellungen

Alle fünf stehen in der `info.xml` des Backends und werden von `config.py`
gelesen. Ein unbrauchbarer Wert stoppt den Container nie: er fällt auf die
Vorgabe zurück und schreibt den Namen der Variablen ins Protokoll, nie ihren
Wert.

| Variable | Vorgabe | Wirkung |
|---|---|---|
| `FINDLING_RECONCILE_ENABLED` | `true` | Schaltet den Abgleich ganz ab. Aus heißt: der Index ist nur so gut wie der Ereignisstrom. Einzige Ausnahme ist der einmalige Nachholzyklus nach dem Upgrade auf 1.5 (Abschnitt oben). |
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
Art. Der Nachlauf über verschwundene Speicher schreibt eine Zeile mit seinen
Zählern (`gone`, `deselected`, `stamped`, `removed`) und den Storage-IDs. Kein
Pfad, kein Dateiname, kein Titel, keine Datei-Id. Die Dateiliste ist das Privateste,
was dieser Container liest, und ein Protokoll, das sie mitschreibt, wäre eine
Preisgabe (T-03-1205). Ein Test prüft das mit einem Grep über das Modul, weil
diese Regel nicht absichtlich gebrochen wird, sondern beim Hinzufügen eines
hilfreichen Details.
