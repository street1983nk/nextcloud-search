# Der Ablauf der Vergleichsmessung, in seiner Reihenfolge

Diese Datei ist der Ablaufplan des Laufs vom Verzeichnis
`docs/measurements/2026-09-vergleichsmessung-m7g/`. Sie beschreibt den Lauf,
bevor er stattfindet, und sie ist die Datei, aus der Kriterium 4 seinen Satz
"wiederholbar beschrieben" bezieht. Wer den Lauf ein zweites Mal fahren will,
liest diese Datei von oben nach unten und ruft die Skripte in der genannten
Reihenfolge.

Zwei Dinge stehen vorweg, weil sie den ganzen Rest tragen:

- **Der Lauf kostet Box-Stunden, und der Deckel ist 30 Stunden.** Alles, was
  ohne Box festgestellt werden kann, ist vor der Anfahrt festgestellt (Wellen 1
  und 2 dieser Phase haben null Box-Minuten gekostet).
- **Zwei Feststellungen können den Lauf retten, bevor er 19 Stunden kostet:**
  die Korpus-Prüfsumme (Schritt 2) und der Baumhash (Schritt 3). Beide laufen
  **vor** dem Indexaufbau, beide haben eine Urteilszeile, und beide brechen mit
  einem Rückgabewert ungleich null ab. Ein Fehlbefund nach dem Indexaufbau
  kostet den ganzen Lauf.

---

## 0. Der Lauf vom 09.09.2026, wie er wirklich abgesetzt wurde

Diese Zeilen sind nachgetragen, als der Lauf lief, damit die Datei nicht nur
beschreibt, was geschehen soll, sondern auch belegt, was geschehen ist.

| Sache | Wert |
|---|---|
| **Anstoss des Volllaufs** | **2026-09-09T09:58:42Z**, über `96-volllauf.sh`, abgesetzt mit `setsid nohup` |
| Gegenprobe | 2026-09-09T10:04:43Z, also nach 361 s, Urteil `arbeitsvorrat-da ja` |
| Erwartete Laufzeit | rund 19 Stunden für den Neuaufbau, Gesamtlaufzeit der Box 22 bis 26 Stunden |
| **Kostendeckel** | **30 Stunden und 3,50 USD netto**, vom Owner am 09.09. bestätigt; laufend 0,1158 USD je Stunde |
| Box | `i-06b1d913f5c6f669b`, angefahren 2026-09-09T09:20:06Z, Adresse 3.69.147.2 |
| Startpunkt des Laufs | `vorrat=2040 indexed=1653 embedded=264`, aus der Trockenprobe des Lesers |
| Laufzeit-Vorbehalt | `indexed` stand beim Anstoss über null, also ist die gemessene Laufzeit eine **Untergrenze** und wird als eine berichtet |
| Beobachter | Sampler 5 s (vier Aufnahmen vor dem Anstoss), Statusbeobachter 120 s, Wächter mit Rundendeckel 340, Meldekette im Wartemodus |
| Meldekette | `http=200` beim Anstoss. Der 403 vom 05.09. ist nicht wiedergekehrt, der Vertrag bleibt trotzdem die Datei `00-FERTIG` |

Warum der Startpunkt nicht null ist, in zwei Sätzen: Schritt 4 füllt die
Warteschlange mit `findling:index --restart -n`, und weil Schritt 3 die PHP-App
einschaltet, hat der Poller sie sofort zu bedienen begonnen. Für die Grundlast
in Schritt 5 ist die App deshalb wieder abgeschaltet und der Container neu
gestartet worden, damit "Modell nie geladen, noch keine Suche" auch stimmt;
eingeschaltet wurde sie erst wieder unmittelbar vor dem Anstoss. Die 1.653
Dateien, die dabei schon im Index lagen, sind der Preis dafür, und er steht
hier statt in einer Fussnote.

---

## 1. Die Anfahrt, und was `aws_box.sh start` ausdrücklich nicht erledigt

`scripts/ops/aws_box.sh start` startet die Instanz, liest die neue öffentliche
Adresse und zieht die SSH-Regel der Security Group auf die aktuelle Adresse des
Owners nach (revoke vor authorize). Es nennt danach selbst, was **offen**
bleibt. Die offenen Punkte, mit dem, was jeweils zu tun ist:

| Offener Punkt | Was zu tun ist |
|---|---|
| **A-Record `loadtest.infranode.dev`** | Der Record zeigt auf eine Adresse, die die Box seit dem 05.09. nicht mehr hat. Er ist auf die neue Adresse zu setzen. Rückfall 1: den `/etc/hosts`-Pin der Box **nach jedem Maschinenneustart** neu aus `docker inspect` des Apache-Containers bilden, weil ein Neustart die Adressen der Docker-Brücke neu verteilt (Fallstrick 7: Apache wanderte von `172.18.0.6` auf `172.18.0.4`, der alte Pin liess den Poller 300 Sekunden ins Backoff laufen). Rückfall 2: mit `curl --resolve` arbeiten statt mit `/etc/hosts`. |
| **Der Container ist nach einem Maschinenstart nicht bewaffnet** | DI-05-36. `occ app_api:app:disable findling_backend`, danach `occ app_api:app:enable findling_backend`. Der Beweis der Bewaffnung ist ein gezählter Poller-Durchgang im Protokoll, kein abgelesener Zustand. |
| **Die harte Speichergrenze ist nach jeder Registrierung weg** | `docker update --memory=2g --memory-swap=2g`, und `memory.max` sowie `memory.swap.max` **aus der cgroup** zurücklesen. Erwartungswert `2147483648`. Schritt 3 tut das selbst und bricht bei Abweichung ab. |

**Die Regel, die über allem steht: auf dieser Box läuft in Phase 10 genau eine
Nextcloud.** Kein Installationslauf, kein Fremdtest, keine zweite Instanz. Der
Volumenname einer ExApp folgt allein aus ihrer App-Kennung, und am 07.09. hat
eine zweite, frische Nextcloud am selben Docker-Dienst mit
`app_api:app:unregister --rm-data` das Messvolumen der **ersten** Instanz
entfernt. `docker ps` belegt die Einzahl, und zwar **vor** dem ersten
`--rm-data`: Schritt 1 zählt die laufenden Nextcloud-Instanzen, Schritt 3
zählt sie unmittelbar vor dem Aufruf noch einmal und bricht bei mehr als einer
ab.

Von diesem Windows-Rechner aus gilt zusätzlich Fallstrick 12: Git für Windows
schreibt Pfadargumente um (`/dev/sdf` wurde zu `C:/Program Files/Git/dev/sdf`).
`aws_box.sh` schaltet das für seinen Prozess ab; jedes neue Skript, das von
hier gegen die Box oder gegen die AWS-API läuft, muss dasselbe tun.

---

## 2. Die Schrittfolge

Jede Zeile nennt das Skript, die Rohdatei, die es erzeugt, und die Aussage, an
der der Schritt hängt. Die Schritte 96 bis 99b sind mit Plan 10-04 gebaut, und
ihre Rohdateinamen stehen seither hier: eine Reihenfolge ist nur als ganze eine
Reihenfolge.

| Nr | Skript | Rohdatei | Die Aussage, an der der Schritt hängt |
|---|---|---|---|
| 1 | `90-bestand.sh` | `90-bestand.txt` | Der Zustand der Box vor jedem Eingriff: `memory.events` ungelesen, `mem=4G` aus `/proc/cmdline`, Platz auf `/mnt/findling`, Inhalt des Volumens, Zahl der laufenden Nextcloud-Instanzen. Ohne diese Zahlen beschreibt jede spätere Messung das Aufräumen und nicht den Lauf. |
| 2 | `91-korpus.sh` | `91-korpus.txt` | Kriterium 1, erste Hälfte: es ist derselbe Korpus. 50.000 Dateien, 20.208.046.426 Byte, Listen-Prüfsumme `bcbef9b2...`. Urteilszeile `korpus-gleich ja` oder `nein`. **Vor** dem Indexaufbau. |
| 3 | `92-wechsel.sh` | `92-wechsel.txt`, `40b-baumhash.txt`, `92-info-box.xml` | Kriterium 1, zweite Hälfte: es ist derselbe Codestand. `:dev` gezogen, Digest festgehalten, Baumhash im Abbild gegen den Arbeitsbaum (gerufen wird `40b-baumhash.sh`, nicht nachgebaut), PHP-Hälfte eingespielt, Registrierung, harte Grenze aus der cgroup zurückgelesen. |
| 4 | `93-nullstand.sh` | `93-nullstand.txt` | Der Lauf startet auf einem Nullstand, der mit Zahlen belegt ist: Volumeninhalt, `oc_findling_file_state`, die Marken in `meta`, die Ausgabe von `occ findling:index`. Danach `findling:index --restart -n` und die Wartefrist aus Abschnitt 4. |
| 5 | `94-grundlast.sh` | `94-grundlast.txt` | **Die MESS-01-Kernzahl.** Grundlast im Leerlauf: Container gestartet, bewaffnet, Modell nie geladen, noch keine Suche. Vier Teile: A die Grundlinie, B der Fussabdruck der Gewichte allein, C die Aufschlüsselung Schritt für Schritt aus `52-woher-die-grundlast.py`, D die feine Zerlegung in fünf benannte Posten aus `01-grundlast-fein.py`. |
| 6 | `95-spitze.sh vorher` | `95-spitze-vorher.txt`, `95-vorher-stufe-<n>.json` | Die erste Suche als **Ereignis** auf leerem Vektorbestand: lesen, genau eine Suche gegen einen Container, der noch nie eine gesehen hat, wieder lesen. Danach die Stufen 1, 4 und 8. |
| 7 | `96-volllauf.sh`, danach abgesetzt `96b-waechter.sh` und `96e-ntfy-watch.sh warten` | `96-volllauf-start.txt`, `96-volllauf.csv`, `96-statusseite.jsonl`, `96b-waechter.txt`, `96-suchlast-nachlauf.json`, `96-suchlast-danach.json`, `96-vektorbestand.txt`, **`96-oom-beweis.txt`**, `00-FERTIG`, `99-ntfy-watch.log` | Kriterium 1 und 2: der Volllauf, rund 19 Stunden, abgesetzt. Sampler (5 s) und Statusbeobachter (120 s) starten **vor** dem Anstoss, der Wächter hat einen Rundendeckel von 340 Runden à 300 s, und `00-FERTIG` ist der Vertrag. Die Gesamtspitze und die Laufzeit entstehen hier und nirgends sonst. Der OOM-Beweis am Ende beider Spuren geht in eine eigene Rohdatei `96-oom-beweis.txt`, weil Schritt 9 ohne diese Datei den Neustart verweigert. Wartefristen: 20 s nach dem Start der Beobachter, 360 s bis zur Gegenprobe. Abbruch: `96-volllauf.sh` endet mit 14, wenn nach der Frist kein Arbeitsvorrat da ist, und startet den Wächter dann **nicht**; der Wächter endet mit 13 am Rundendeckel (unvollständiger Lauf) und mit 14, wenn keine einzige brauchbare Aufnahme vorlag. |
| 8 | `97-nebenlaeufigkeit.sh` | `97-nebenlaeufigkeit.txt`, `97-stufe-<n>.json` | **Die p95-Hälfte von MESS-02.** Fünf Stufen 1, 4, 8, 12, 16, zehn Runden je Stufe, 410 Anfragen, über die OCS-Route und damit über den finalen PHP-Recheck. Die Zusage steht auf Stufe 8. |
| 9 | `95-spitze.sh nachher` | `95-spitze-nachher.txt`, `95-nachher-stufe-<n>.json` | DI-07-02: der Kaltstart auf **vollem** Vektorbestand, also der schlechtere der beiden Fälle. Setzt einen bewussten `docker restart` des Backendcontainers voraus, den das Skript selbst absetzt. **Die Reihenfolge ist zwingend: der OOM-Beweis wird VOR dem Neustart erhoben**, weil ein Neustart `memory.peak` und `memory.events` zurücksetzt. Erzwungen statt erinnert: ohne `96-oom-beweis.txt` bricht `95-spitze.sh nachher` mit 12 ab. |
| 10 | `98-sprachfaelle.sh` | `98-sprachfaelle.txt` | MESS-02, die zehn Sprachfälle. Sie brechen gegen den Lasttest-Nutzer, weil der Lastkorpus dieselben Wörter führt (Fallstrick 3), also **eigener Nutzer** (Vorgabe `sprachfall`, ausdrücklich nicht `lasttest`), dessen Heimat nur `testdata/corpus` enthält, 39 Dateien über WebDAV, abgeschlossener OCR-Durchgang, Verdikte erst bei leerem Arbeitsvorrat. Bilanzzeile `sprachfaelle bestanden <n> von 10`. Wartefristen: 360 s vor der ersten Ablesung, danach bis zu 40 Runden à 60 s auf einen leeren Arbeitsvorrat. Abbruch: 15 (nicht 39 Dateien hochgeladen), 16 (Vorrat am Rundendeckel nicht leer), 17 (mindestens ein Fall rot), 18 (kein `jq` auf der Box). **Dieser Block ist abbrechbar und keine Vorbedingung des Berichts** (Annahme A7). |
| 11 | `99-seitenroute.sh` | `99-seitenroute.txt`, `99-reihe-a.txt` bis `99-reihe-d.txt` (je ein Wert pro Zeile, Sekunden, unbearbeitet) | T-09-29: die Anzeigeseite auf einer Instanz, die eine `vectors.db` **hat**. Erstmessung, kein Vergleich. Vier Reihen à 20 Wiederholungen plus 5 Aufwärmanfragen, beide Anmeldewege getrennt (Sitzung und Basic-Auth), weil Basic-Auth 0,318 s je Anfrage kostet (Fallstrick 9), dazu eine tiefe Seite und der Dialogweg mit `limit=100`. Rangregel wie Abschnitt 2 des Seitenbudget-Berichts, ohne Interpolation. Abbruch: 19, wenn eine Reihe weniger als 20 brauchbare Werte hat. |
| 12 | `99b-runden.sh` | `99b-runden.txt`, `99b-fall1.json`, `99b-fall2-vor-ruecknahme.json`, `99b-fall2.json` | DI-07-03: die Rundenzählung des Rechteabgleichs, in zwei getrennten Fällen. Fall 1 ist der Alltag (das Konto, das alle Dateien besitzt), Fall 2 der **absichtlich erzeugte** Driftfall (Freigabe zurückgenommen, gefragt bevor der Index davon weiss). Der Bericht muss beide Fälle mit ihrer Herstellung nennen. Wartefrist: 2 x 90 s mit gezähltem Poller-Durchgang, bevor die Rechte als aufgenommen gelten. Abbruch: 20 (das Zugriffsprotokoll trägt keine Anfragezeile, die Zählung wäre keine Messung), 21 (der Driftfall liess sich nicht erzeugen, ein Befund über die Box). |
| 13 | Gegenproben: `68-bestand-endungen.py`, `42d-bestand.py`, Indexgrösse | `96-vektorbestand.txt` (Chunks, Dokumente, Byte je Dokument, aus Schritt 7), dazu die Ausgabe des Endungsvergleichs | Kriterium 3: der Endungsvergleich, Chunks und Dokumente und Byte je Dokument, und die Grösse des Tantivy-Index auf der Platte. `42d-bestand.py` und die Grössen des Datenspeichers erhebt der Wächter am Ende von Schritt 7 selbst; der Endungsvergleich über `68-bestand-endungen.py` wird hier von Hand nachgezogen. Sie laufen **vor** dem Abbau und nicht danach (T-06.1-79, und am 07.09. hat sich genau das ausgezahlt). |

Danach: Rohdaten und Skripte herunterholen und committen, Owner-Checkpoint
"Bericht abgenommen", dann `aws_box.sh stop`, das die Laufzeit und die Kosten in
`box.env` schreibt.

---

## 3. Die Ablesestellen von `memory.events`

An **jeder** dieser Stellen wird `memory.events` gelesen, und zwar **vor** dem
Eingriff, der an der Stelle stattfindet. Wer nach dem Aufräumen liest, misst das
Aufräumen und nicht den Lauf (T-06.1-75, und die Lehre aus 06-11). Diese Liste
wird in Abschnitt 13 des Berichts zur Tabelle, mit allen sechs Zählern je Zeile.

| Nr | Ablesestelle | Skript |
|---|---|---|
| 1 | Vor jedem Eingriff dieses Laufs, als Nullpunkt | `90-bestand.sh` |
| 2 | Nach der Registrierung und nach dem Setzen der harten Grenze | `92-wechsel.sh` |
| 3 | Vor dem Absetzen von `findling:index --restart` | `93-nullstand.sh` |
| 4 | Vor Teil A der Grundlast, bevor die Messung etwas anfasst | `94-grundlast.sh` |
| 5 | Nach Teil B und C, damit die zwei Lesungen die Gewichte einklammern | `94-grundlast.sh` |
| 6 | Vor der ersten Suche, Rolle `vorher` | `95-spitze.sh vorher` |
| 7 | Nach der ersten Suche und nach jeder Stufe, Rolle `vorher` | `95-spitze.sh vorher` |
| 8 | Vor dem Anstoss des Volllaufs, also bevor die App eingeschaltet wird | `96-volllauf.sh` |
| 9 | Am Übergang von der ersten auf die zweite Spur, und noch einmal nach der Suchlastprobe im Nachlauf | `96b-waechter.sh` |
| 10 | Am Ende beider Spuren, **vor** jedem Eingriff: der OOM-Beweis nach `96-oom-beweis.txt` | `96b-waechter.sh` |
| 11 | Vor der Nebenläufigkeitsreihe und nach jeder ihrer fünf Stufen | `97-nebenlaeufigkeit.sh` |
| 12 | Vor der ersten Suche, Rolle `nachher`, nach dem bewussten Neustart | `95-spitze.sh nachher` |
| 13 | Am Ende des Wächters, nach den Nachlaufschritten, als Nachtrag in dieselbe Datei `96-oom-beweis.txt` | `96b-waechter.sh` |

Zwei Ablesestellen dieser Liste sind mit Plan 10-04 dazugekommen, weil sie sonst
zwischen den Zeilen gestanden hätten:

- **Nach der Suchlastprobe bei vollem Bestand** (Teil von Stelle 13). Der Wächter
  liest die Zähler zweimal: Stelle 10 unmittelbar bei erkanntem Ende, **vor**
  jedem Eingriff, und Stelle 13 am Ende seiner Nachlaufschritte. Beide Lesungen
  stehen in derselben Rohdatei und sind beschriftet. Der Grund für die Teilung:
  eine Suchlastprobe hebt `memory.peak`, und ein Spitzenwert, der nach ihr
  gelesen wird, ist der Spitzenwert der Messung und nicht der des Laufs.
- **Vor dem Neustart der Rolle `nachher`** ist keine eigene Stelle, sondern genau
  Stelle 10: `95-spitze.sh nachher` liest die Zähler noch ein letztes Mal, bevor
  es `docker restart` absetzt, und verweigert den Neustart mit 12, solange
  `96-oom-beweis.txt` fehlt.

Zu jeder Lesung gehört die Regel aus Muster 3: **anon und `memory.current`
immer nebeneinander.** anon ist der Heap, `memory.current` zählt den
Seitencache derselben cgroup mit, und der Tantivy-Index ist ein mmap. Eine
Store-Aussage aus `memory.peak` beschreibt die App schlechter als sie ist, eine
aus anon allein ist die billigere Hälfte der Wahrheit. Der Abstand lag in der
Lastreihe der Nachmessung über alle Stufen bei rund 86 MB und wuchs mit der
Nebenläufigkeit nicht.

**Keine Speicherzahl dieses Laufs kommt aus dem Docker-Klienten.** Der Klient
liefert eine Zahl auf `memory.current`-Basis. Gelesen wird die cgroup unter
`/sys/fs/cgroup/system.slice/docker-<CID>.scope/`, und `rss_sampler.sh` tut das
selbst; ein Test hält die zwei Wörter des Klienten aus dem Skript heraus.

---

## 4. Die Wartefristen, jede gegen die langsamste beteiligte Uhr

Eine Wartefrist gegen die Uhr zu bemessen, an die man gerade gedacht hat, ist
Fallstrick 11: die Gegenprobe des Semantiklaufs erklärte den Lauf 52 Sekunden zu
früh für tot.

| Wartefrist | Dauer | Die Uhren, gegen die sie bemessen ist |
|---|---|---|
| Nach `occ findling:index --restart -n`, bevor ein Arbeitsvorrat als Aussage gilt | **mindestens 360 s** | Der Poller-Backoff läuft bis **300 s**, und AIO ruft `cron.php` nur alle **fünf Minuten**, wobei der **erste** Auftrag der App noch nichts einreiht. Es sind also zwei Runden des Fünf-Minuten-Systemcrons abzuwarten. 360 Sekunden ist die Untergrenze, nicht der Zielwert. |
| Nach der Registrierung, bevor die Bewaffnung gezählt wird | 2 x 90 s | Der Poller-Durchgang wird im Protokoll **gezählt** und nicht als Zustand abgelesen: ein Zustand, der zum falschen Zeitpunkt abgelesen wird, sieht aus wie eine Bewegung (Lehre aus Drill 1b, 05-21). |
| Zwischen den Stufen der Nebenläufigkeitsreihe | 20 s | Damit die folgende Stufe sich selbst misst und nicht den Nachlauf der vorigen. |
| Nach dem Start des Samplers, bevor die erste Suche läuft | 6 s | Das Intervall des Samplers ist 2 s; drei Aufnahmen vor dem Ereignis sind der Nullpunkt, gegen den die Spitze gelesen wird. |
| Nach dem Start von Sampler und Statusbeobachter, bevor der Volllauf angestossen wird | 20 s | Der Sampler muss seine Kopfzeile geschrieben und der Beobachter sich angemeldet und **eine** Aufnahme gemacht haben, denn gegen genau diese Aufnahme läuft die Trockenprobe des Lesers (Fallstrick 8). |
| Nach dem Anstoss des Volllaufs, bevor die Gegenprobe ein Urteil ist | **mindestens 360 s** | Dieselben zwei Uhren wie oben: Poller-Backoff bis 300 s und zwei Runden des Fünf-Minuten-Systemcrons. |
| Zwischen zwei Runden des Wächters | 300 s | 340 Runden à 300 s sind gut ein Tag und eine halbe Nacht. Das Ende gilt erst, wenn der Vorrat leer ist **und** `embedded` drei Aufnahmen lang stillsteht, also nach 15 Minuten Ruhe. |
| Nach dem WebDAV-Upload der Sprachfälle, bevor Verdikte gelesen werden | 360 s, danach bis zu 40 x 60 s | Erst die Frist der beiden langsamen Uhren, dann Runde für Runde auf einen leeren Arbeitsvorrat. `skipped:no_text_layer` ist ein **vorübergehendes** Verdikt: es ist der Zustand einer Datei, die an die Scan-Spur übergeben wurde, und nicht der Zustand einer Datei ohne Text. |
| Nach dem Anlegen der Freigaben der Rundenzählung, bevor die Rechte als aufgenommen gelten | 2 x 90 s | Der Poller-Durchgang wird gezählt, und die Kontrolle ist eine Suche des Driftkontos mit mehr als null Treffern: ein Zustand, der zum falschen Zeitpunkt abgelesen wird, sieht aus wie eine Bewegung. |

**Was zu tun ist, wenn der Arbeitsvorrat nach den 360 Sekunden auf null steht.**
Das ist kein Erfolg und kein Abbruch, sondern Annahme A2 der Recherche:
`occ findling:index --restart` stand auf der Box eingestellt, die Notiz war zwei
Tage alt und die Box war seither aus. `93-nullstand.sh` schreibt in diesem Fall
`arbeitsvorrat-da nein` und endet mit 10. Dann wird der Befehl **erneut**
abgesetzt, wieder mit `-n`, und die Frist läuft von vorn. Erst wenn der Vorrat
nach einer zweiten Frist auf null bleibt, ist das ein Befund über die Box und
gehört in den Bericht. Die Grundlast darf in keinem der beiden Fälle so gelesen
werden, als sei der Lauf angefahren.

**Das Urteil des Skripts bleibt stehen, und der Nachtrag wird darunter
geschrieben.** Ein Skript, dessen Urteil nachträglich überschrieben wird,
erzeugt eine Rohdatei, die nicht mehr belegt, was gemessen wurde.

---

## 5. Die Abbruchpfade

| Abbruchpfad | Bedingung | Was geschieht |
|---|---|---|
| **Korpus-Prüfsumme** | `91-korpus.sh` schreibt `korpus-gleich nein`, weil die Listen-Prüfsumme nicht `bcbef9b2...` ist oder die Bytezahl nicht 20.208.046.426 | **Abbruch vor dem Indexaufbau.** Der Befund geht in den Bericht: Kriterium 1 verlangt "mit dem vorhandenen v1.0-Korpus", und ein anderer Korpus macht jede Vergleichszahl zu einer Zahl über einen anderen Gegenstand. Danach `aws_box.sh stop`, weil ein 19-Stunden-Lauf auf einem fremden Korpus 19 Stunden für nichts ist. |
| **Baumhash** | `40b-baumhash.sh` schreibt `baumhash-gleich nein`, oder die Rohdatei `40b-baumhash.txt` trägt weniger als drei `baumhash:`-Zeilen | **Abbruch.** Kriterium 1 wäre nicht belegbar: jede Zahl nach dieser Zeile gehörte zu einem unbekannten Stand. Der Schritt beendet sich mit 4 (Ungleichstand) oder 3 (unvollständige Rohdatei), und `92-wechsel.sh` geht nicht weiter. Beide Vorläuferberichte haben an genau dieser Stelle eine leere Rohdatei hinterlassen und die Gleichheit trotzdem behauptet. |
| **Rundendeckel des Wächters** | Der Wächter des Volllaufs erreicht seinen Rundendeckel, ohne dass beide Spuren fertig sind | **Kein Abbruch der Messung, sondern ein unvollständiger Lauf.** Die bis dahin erhobenen Zahlen werden gesichert (Sampler-CSV, `memory.events`, Zwischenstand des Bestands), und der Bericht weist den Lauf ausdrücklich als unvollständig aus. Eine Laufzeit ohne Ende ist keine Laufzeit, und sie darf nicht als eine berichtet werden. |
| **Kostendeckel** | Die Box erreicht **30 Stunden** Laufzeit (Szenario A plus vier Stunden Reserve, rund 3,50 USD netto) | **Anhalten.** Der Deckel ist der Wert, den der Owner-Checkpoint vor der Anfahrt bestätigt. Was bis dahin erhoben ist, wird gesichert und berichtet; der Rest wird als offen benannt. Der laufende Satz ist 0,1158 USD je Stunde, angehalten 0,3130 USD je Tag. |

Dazu die Rückgabewerte der Skripte, weil jeder von ihnen im Bericht auftauchen
kann. Jeder steht auch im Kopf seiner Datei:

| Wert | Skript | Bedeutung |
|---|---|---|
| 2 | `95-spitze.sh` | unbekannte Rolle |
| 4, 3 | `92-wechsel.sh` | Baumhash ungleich, unvollständige Rohdatei |
| 5 | `90-bestand.sh`, `92-wechsel.sh` | mehr als eine Nextcloud |
| 6, 7 | `91-korpus.sh` | Korpus weicht ab, keine Lesung |
| 8, 9 | `92-wechsel.sh` | unsauberer Arbeitsbaum, harte Grenze falsch |
| 10 | `93-nullstand.sh` | kein Arbeitsvorrat |
| 11 | `94-grundlast.sh` | Teil D leer |
| 12 | `95-spitze.sh nachher` | `96-oom-beweis.txt` fehlt |
| 13 | `96b-waechter.sh` | Rundendeckel erreicht, **unvollständiger Lauf** |
| 14 | `96-volllauf.sh`, `96b-waechter.sh` | kein Arbeitsvorrat nach der Frist, beziehungsweise keine brauchbare Aufnahme |
| 15, 16, 17, 18 | `98-sprachfaelle.sh` | Upload unvollständig, Vorrat nicht leer, Fall rot, kein `jq` |
| 19 | `99-seitenroute.sh` | eine Reihe hat zu wenige brauchbare Werte |
| 20, 21 | `99b-runden.sh` | Zugriffsprotokoll ohne Anfragezeile, Driftfall nicht erzeugbar |
| 0 | `96e-ntfy-watch.sh` | **immer**: kein Schritt darf daran hängen, dass eine Nachricht ankommt |

Zu jedem der vier Pfade gehört derselbe Satz: **die bis dahin erhobenen Zahlen
werden committet, bevor irgendetwas abgebaut wird.** Am 07.09. war das der
Unterschied zwischen einem teuren Vorfall und einem verlorenen Lauf: alle
Messzahlen waren um 06:23Z im Repository, das Volumen fiel um 06:46Z.

---

## 6. Was in dieser Reihenfolge bewusst **nicht** vorkommt

- **Das Abbild auf der Box bauen.** Kostet rund 40 Minuten gedeckelter Laufzeit
  und erzeugt einen Stand, den nur diese Maschine kennt. `:dev` trägt den
  Backend-Stand von HEAD, und der Beweis dafür ist der Baumhash aus Schritt 3,
  nicht die Digest-Zeichenkette.
- **Eine zweite Nextcloud, ein Installationslauf, ein Fremdtest.** Siehe
  Abschnitt 1.
- **Eine eigene Zeile Messlogik, wo ein vorhandenes Skript dieselbe Frage
  beantwortet.** Kriterium 3 verlangt Vergleichbarkeit Zeile für Zeile. Die
  Schrittnamen von `52-woher-die-grundlast.py` sind die Vergleichsschlüssel;
  eine umbenannte Zeile macht aus einer Vergleichszahl eine bloss benachbarte.
- **Ein Passwort in einem Argument.** Ein Argument steht in der Prozessliste der
  Box und in jedem Protokoll, das den Befehl aufzeichnet. `search_load.py`
  nimmt `--password-env` mit dem **Namen** der Umgebungsvariablen, und ein Gate
  über dieses Verzeichnis hält die anderen Gestalten heraus.
