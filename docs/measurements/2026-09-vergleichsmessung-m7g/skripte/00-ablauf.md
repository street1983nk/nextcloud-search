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
der der Schritt hängt. Die Schritte 96 bis 99b werden in Plan 10-04 gebaut; sie
stehen hier schon, weil eine Reihenfolge nur als ganze eine Reihenfolge ist, und
Plan 10-04 ergänzt ihre Rohdateinamen.

| Nr | Skript | Rohdatei | Die Aussage, an der der Schritt hängt |
|---|---|---|---|
| 1 | `90-bestand.sh` | `90-bestand.txt` | Der Zustand der Box vor jedem Eingriff: `memory.events` ungelesen, `mem=4G` aus `/proc/cmdline`, Platz auf `/mnt/findling`, Inhalt des Volumens, Zahl der laufenden Nextcloud-Instanzen. Ohne diese Zahlen beschreibt jede spätere Messung das Aufräumen und nicht den Lauf. |
| 2 | `91-korpus.sh` | `91-korpus.txt` | Kriterium 1, erste Hälfte: es ist derselbe Korpus. 50.000 Dateien, 20.208.046.426 Byte, Listen-Prüfsumme `bcbef9b2...`. Urteilszeile `korpus-gleich ja` oder `nein`. **Vor** dem Indexaufbau. |
| 3 | `92-wechsel.sh` | `92-wechsel.txt`, `40b-baumhash.txt`, `92-info-box.xml` | Kriterium 1, zweite Hälfte: es ist derselbe Codestand. `:dev` gezogen, Digest festgehalten, Baumhash im Abbild gegen den Arbeitsbaum (gerufen wird `40b-baumhash.sh`, nicht nachgebaut), PHP-Hälfte eingespielt, Registrierung, harte Grenze aus der cgroup zurückgelesen. |
| 4 | `93-nullstand.sh` | `93-nullstand.txt` | Der Lauf startet auf einem Nullstand, der mit Zahlen belegt ist: Volumeninhalt, `oc_findling_file_state`, die Marken in `meta`, die Ausgabe von `occ findling:index`. Danach `findling:index --restart -n` und die Wartefrist aus Abschnitt 4. |
| 5 | `94-grundlast.sh` | `94-grundlast.txt` | **Die MESS-01-Kernzahl.** Grundlast im Leerlauf: Container gestartet, bewaffnet, Modell nie geladen, noch keine Suche. Vier Teile: A die Grundlinie, B der Fussabdruck der Gewichte allein, C die Aufschlüsselung Schritt für Schritt aus `52-woher-die-grundlast.py`, D die feine Zerlegung in fünf benannte Posten aus `01-grundlast-fein.py`. |
| 6 | `95-spitze.sh vorher` | `95-spitze-vorher.txt`, `95-vorher-stufe-<n>.json` | Die erste Suche als **Ereignis** auf leerem Vektorbestand: lesen, genau eine Suche gegen einen Container, der noch nie eine gesehen hat, wieder lesen. Danach die Stufen 1, 4 und 8. |
| 7 | `96-volllauf.sh` mit Wächter (Plan 10-04) | Plan 10-04, darunter `96-oom-beweis.txt` | Kriterium 1 und 2: der Volllauf, rund 19 Stunden, abgesetzt. Sampler daneben, Wächter mit Rundendeckel, `00-FERTIG` als Vertrag. Die Gesamtspitze und die Laufzeit entstehen hier und nirgends sonst. Der OOM-Beweis am Ende beider Spuren geht in eine eigene Rohdatei `96-oom-beweis.txt`, weil Schritt 9 ohne diese Datei den Neustart verweigert. |
| 8 | `97-nebenlaeufigkeit.sh` | `97-nebenlaeufigkeit.txt`, `97-stufe-<n>.json` | **Die p95-Hälfte von MESS-02.** Fünf Stufen 1, 4, 8, 12, 16, zehn Runden je Stufe, 410 Anfragen, über die OCS-Route und damit über den finalen PHP-Recheck. Die Zusage steht auf Stufe 8. |
| 9 | `95-spitze.sh nachher` | `95-spitze-nachher.txt`, `95-nachher-stufe-<n>.json` | DI-07-02: der Kaltstart auf **vollem** Vektorbestand, also der schlechtere der beiden Fälle. Setzt einen bewussten `docker restart` des Backendcontainers voraus, den das Skript selbst absetzt. **Die Reihenfolge ist zwingend: der OOM-Beweis wird VOR dem Neustart erhoben**, weil ein Neustart `memory.peak` und `memory.events` zurücksetzt. Erzwungen statt erinnert: ohne `96-oom-beweis.txt` bricht `95-spitze.sh nachher` mit 12 ab. |
| 10 | `98-sprachfaelle.sh` (Plan 10-04) | Plan 10-04 | MESS-02, die zehn Sprachfälle. Sie brechen gegen den Lasttest-Nutzer, weil der Lastkorpus dieselben Wörter führt (Fallstrick 3), also **eigener Nutzer**, dessen Heimat nur `testdata/corpus` enthält, 39 Dateien über WebDAV, abgeschlossener OCR-Durchgang, Verdikte erst bei leerem Arbeitsvorrat. |
| 11 | `99-seitenroute.sh` (Plan 10-04) | Plan 10-04 | DI-07-03 und T-09-29: die Anzeigeseite auf einer Instanz, die eine `vectors.db` **hat**. Erstmessung, kein Vergleich. Beide Anmeldewege getrennt, Sitzung und Basic-Auth, weil Basic-Auth 0,318 s je Anfrage kostet (Fallstrick 9). |
| 12 | `99b-runden.sh` (Plan 10-04) | Plan 10-04 | Die Rundenzählung des Rechteabgleichs, gegen den Befund M-03 der Phase 9. |
| 13 | Gegenproben: `68-bestand-endungen.py`, `42d-bestand.py`, Indexgrösse | Plan 10-04 | Kriterium 3: der Endungsvergleich, Chunks und Dokumente und Byte je Dokument, und die Grösse des Tantivy-Index auf der Platte. Sie laufen **vor** dem Abbau und nicht danach (T-06.1-79, und am 07.09. hat sich genau das ausgezahlt). |

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
| 8 | Vor dem Anstoss des Volllaufs | Plan 10-04 |
| 9 | Am Uebergang von der ersten auf die zweite Spur | Plan 10-04 |
| 10 | Am Ende beider Spuren, **vor** jedem Eingriff: der OOM-Beweis | Plan 10-04 |
| 11 | Vor der Nebenläufigkeitsreihe und nach jeder ihrer fünf Stufen | `97-nebenlaeufigkeit.sh` |
| 12 | Vor der ersten Suche, Rolle `nachher`, nach dem bewussten Neustart | `95-spitze.sh nachher` |
| 13 | Am Ende des Laufs, vor dem Abbau | Plan 10-04 |

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
