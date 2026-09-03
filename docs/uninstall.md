# Findling deinstallieren: was wann verschwindet

Diese Seite beantwortet die Frage, die ein Admin vor dem Abschalten stellt und
nach dem Abschalten nicht mehr stellen kann: was ist jetzt weg. Sie ist für
denselben Leser geschrieben wie `docs/admin-page.md`, also für den Admin, der
wissen will, was ein Befehl anrichtet, bevor er ihn tippt, und für den
Entwickler, der in einem Jahr verstehen muss, warum die Räumung eine
ausdrückliche Absicht verlangt statt einfach zu laufen.

Der Leitsatz dieser Seite: jede Aussage nennt auch ihre Grenze. Was hier steht,
ist gemessen worden, und wo es nur für eine Serverversion gemessen wurde, steht
das dabei.

## Gemessen: wann Nextcloud den Uninstall-Schritt wirklich ausführt

Findling registriert in `php/appinfo/info.xml` einen Schritt unter
`repair-steps/uninstall`. Der naheliegende Schluss wäre, dass dieser Schritt
beim Entfernen der App läuft. Er ist falsch, und das ist der Grund für die
gesamte Mechanik weiter unten.

Der Schritt (`php/lib/Repair/AppUninstallStep.php`) zählt jeden seiner Aufrufe
in den appconfig-Wert `purge_step_calls`. Eine Zeile im occ-Ausgabestrom wird
übersehen, eine Zahl nicht. Gemessen wurde damit die folgende Kette, jeder
Zählerstand direkt nach dem jeweiligen Befehl abgelesen mit
`occ config:app:get findling purge_step_calls`:

| # | Befehl | Zähler danach | Ausgabe des Befehls |
|---|--------|---------------|---------------------|
| 0 | Ausgangslage | nicht gesetzt | |
| 1 | `occ app:enable findling` | nicht gesetzt | `findling 0.3.0 enabled` |
| 2 | `occ app:disable findling` | **1** | `findling 0.3.0 disabled` |
| 3 | `occ app:enable findling` | 1 | `findling 0.3.0 enabled` |
| 4 | `occ app:remove findling --keep-data` | 1 | `Removing app 'findling' but keeping app data (uninstall hooks skipped).` |
| 5 | `occ app:enable findling` | 1 | `findling already enabled` |
| 6 | `occ app:remove findling` | **2** | `Disabled app 'findling' (uninstall steps executed).` |

Gemessen am 3. September 2026 auf Nextcloud 34.0.3 (Image
`nextcloud:34.0.3-apache`, SQLite, App unter `custom_apps/findling`).

Drei Befunde, und alle drei sind das Gegenteil dessen, was der Name
`repair-steps/uninstall` verspricht:

1. **Ein Disable führt den Uninstall-Schritt aus.** Zeile 2, Zähler von nicht
   gesetzt auf 1. Das ist kein Nebeneffekt dieser Instanz, sondern die Mechanik
   von `AppManager::disableApp()`, die nach dem Abschalten
   `executeRepairSteps($appId, $appData['repair-steps']['uninstall'])` aufruft.
2. **Ein Enable führt ihn nicht aus.** Zeilen 1, 3 und 5, Zähler unverändert.
   Beim Enable läuft der Install-Schritt, und der hat seine eigene Marke.
3. **`--keep-data` überspringt ihn.** Zeile 4, Zähler unverändert, und der
   Befehl sagt es selbst: `uninstall hooks skipped`. Ein Remove ohne dieses
   Flag geht dagegen durch das Disable und damit durch den Schritt, Zeile 6.

**Der Schluss daraus.** Ein Uninstall-Schritt, der unbedingt löscht, würde bei
jedem Abschalten die Ausschlussregeln, den Größen-Deckel, die
Deckungsgrad-Zähler und die Arbeitsliste mitnehmen. Ein Admin, der die Suche
für eine Nacht abschaltet, hätte danach eine leere Konfiguration. Genau das
verbietet Entscheid D-16, und Entscheid D-18 verlangt trotzdem eine
rückstandsfreie Entfernung. Beides zusammen geht nur mit einer Absichtsmarke:
der Schritt räumt nur, wenn vorher jemand gesagt hat, dass geräumt werden soll,
und ist ansonsten ein Nichtstun mit einer Zeile im Protokoll. Der Weg, die
Absicht zu erklären, ist `occ findling:purge`.

**Die Grenze dieser Messung.** Sie gilt für Nextcloud 34.0.3 und für sonst
nichts. Der Quellcode von `AppManager::disableApp()` ist in den Zweigen
stable32, stable33 und stable34 wortgleich, aber gelesener Quellcode ist kein
Messwert. Die Wiederholung als Kette über alle vier Serverversionen macht der
Job `deploy-harp` in CI; was er feststellt und was nicht, steht in Abschnitt 5.

## 1. Abschalten oder entfernen: was der Unterschied ist

**Abschalten lässt alles liegen.** `occ app:disable findling` beendet den
Suchanbieter, den Poller und die Ereignisverarbeitung. Die drei Tabellen der
App, alle ihre Einstellungen und ihre Hintergrundjobs bleiben unangetastet.
Gemessen auf derselben Instanz, Zählungen jeweils direkt vor und nach dem
Befehl:

| Zustand | Tabellen | appconfig-Werte | Jobs |
|---------|----------|-----------------|------|
| vor `occ app:disable findling` | 3 | 5 | 1 |
| nach `occ app:disable findling` | 3 | 5 | 1 |

**Entfernen verlangt eine ausdrückliche Absicht.** `occ findling:purge` ohne
Option sagt nur, was eine Räumung mitnehmen würde, und ändert nichts. Lesen ist
die Vorgabe:

```
occ findling:purge
```

Die Ausgabe nennt die drei Hintergrundjobs, die drei Tabellen mit der Angabe, ob
sie existieren, die Zahl der Migrationseinträge und die Zahl der gespeicherten
Einstellungen. Tabellennamen und Zahlen, und ausdrücklich kein Pfad und kein
Dateiname: die Ausgabe eines occ-Befehls landet in der Regel in einem Protokoll.

Die beiden Absichten und ihre Befehlsfolgen:

```
# Ich will die App loswerden, mit allem was sie in der Datenbank hat.
occ findling:purge --arm
occ app:remove findling

# Ich will nur den Datenbestand dieser Hälfte leeren, die App bleibt liegen.
occ findling:purge --now
```

`--arm` setzt die Marke, `--disarm` nimmt sie zurück, `--now` räumt sofort. Alle
drei fragen nach, wenn ein Mensch vor dem Terminal sitzt; ein Aufruf mit
`--no-interaction` gilt als bestätigt, weil CI so ruft.

Gemessen mit gesetzter Marke, jeweils direkt nach dem Befehl:

| Schritt | Tabellen | appconfig-Werte | Jobs |
|---------|----------|-----------------|------|
| `occ findling:purge --arm --no-interaction` | 3 | 6 | 1 |
| `occ app:disable findling` | 0 | 0 | 0 |
| noch einmal `occ app:disable findling` | 0 | 0 | 0 |
| `occ app:enable findling` | 3 | 4 | 1 |

Drei Eigenschaften stehen in dieser Tabelle:

- Die Räumung ist vollständig. Drei Tabellen, alle Einstellungen, alle drei
  Hintergrundjobs.
- Sie ist wiederholbar. Der Schritt läuft bei jedem Abschalten erneut und hält
  fehlende Tabellen aus; ein zweiter Lauf mit gesetzter Marke und drei
  abwesenden Tabellen wurde ausdrücklich gefahren und schrieb keine Zeile ins
  Protokoll der Instanz.
- Sie ist umkehrbar. Nach `occ app:enable findling` legen die Migrationen die
  drei Tabellen wieder an, der Install-Schritt plant die Erstindexierung erneut
  und `occ findling:index` antwortet ohne Fehler.

**Ein Re-Enable braucht keinen Reindex** (Entscheid D-16). Der Suchindex selbst
liegt nicht in der Nextcloud-Datenbank, sondern im Datenvolume des Containers,
und keiner der Befehle dieses Abschnitts fasst es an. Tage OCR-Arbeit auf einer
schwachen Box überleben also jedes Abschalten. Die Grenze dieser Aussage: hier
gemessen ist die Nextcloud-Hälfte, also Tabellen, Einstellungen und Jobs. Dass
die Suchleiste nach dem Wiedereinschalten sofort wieder Treffer liefert, folgt
daraus, dass das Volume unberührt bleibt, und ist als Suchprobe über die ganze
Kette hier nicht gemessen. Gemessen ist inzwischen die Hälfte, auf die es dabei
ankommt: der Job aus Abschnitt 5 meldet die ExApp ohne `--rm-data` ab, findet
das Volume danach unverändert vor und registriert auf demselben Volume erneut.
Eine Suche über die ganze Kette nach einem Wiedereinschalten bleibt ungemessen.

**Eine Nebenwirkung, die der Befehl selbst ausspricht.** `--now` nimmt auch den
Wert `enabled` mit, weil er zu den Einstellungen dieser App gehört. Die App ist
danach abgeschaltet. `occ app:enable findling` bringt sie mit leeren Tabellen
zurück, und der Befehl sagt genau das in seiner Ausgabe.

**Und ein Rückstand, der erst in der Messung auffiel.** Nextcloud führt in der
Kerntabelle `migrations` Buch darüber, welche Migration welcher App gelaufen
ist. Diese Zeilen überleben ein `occ app:remove` und wären damit ein Rückstand,
den Entscheid D-18 verbietet. Schlimmer noch: solange sie stehen, hält Nextcloud
das Schema für aktuell, und eine wieder eingeschaltete App hätte keine Tabellen
mehr und bekäme sie durch kein occ-Kommando zurück. Gemessen und bestätigt.
Die Räumung nimmt deshalb auch diese Zeilen mit, ausschließlich die mit der
App-Kennung `findling`, und genau darum ist die letzte Zeile der Tabelle oben
wieder gesund.

## 2. Das Index-Volume: wo die Bestätigung liegt

Der Suchindex, die Zustandsdatenbank und der Arbeitsbereich des Containers
liegen in einem Docker-Volume, das **AppAPI** gehört und nicht dieser App.
Deshalb gibt es hier keinen eigenen Bestätigungsdialog (Entscheid D-15): die
Bestätigung ist die Standardmechanik von AppAPI, und ein Eigenbau daneben wäre
eine zweite Wahrheit über eine Löschung, die Findling nicht ausführt.

Wo diese Bestätigung liegt, hängt von der Serverversion ab:

- **Nextcloud 32 und 33:** im Seitenbereich der App-Verwaltung gibt es einen
  Schalter, der die Daten beim Entfernen mitnimmt.
- **Nextcloud 34 und 35:** dieses Bedienelement gibt es nicht mehr. Die
  App-Verwaltung wurde umgebaut, und kein Schalter der neuen Oberfläche setzt
  das Kennzeichen. Wer auf einer dieser Versionen danach sucht, sucht
  vergeblich; das ist kein Fehler von Findling.

Der Weg, der auf **allen vier Versionen** gilt:

```
occ app_api:app:unregister findling_backend --rm-data
```

Ohne `--rm-data` bleiben die Daten liegen, und das ist die Vorgabe. Der
Gegenschalter dazu ist bei AppAPI abgekündigt und steht hier deshalb nicht als
Weg: wer die Daten behalten will, lässt das Kennzeichen einfach weg.

Die Grenze dieser Aussage: die Versionsunterschiede stehen aus dem Quellcode der
Serverzweige und der AppAPI fest, und der Weg über die Weboberfläche ist nach wie
vor ungemessen. Dass `--rm-data` das Volume wirklich mitnimmt und dass es
ohne das Kennzeichen wirklich liegen bleibt, stellt der Job aus Abschnitt 5 auf
jeder der vier Serverversionen fest.

## 3. Was auch mit `--rm-data` liegen bleibt

Eine ehrliche Deinstallationsseite nennt die Reste, und es gibt drei:

- **Das gezogene Container-Image** bleibt auf dem Host liegen. Der
  Abmeldepfad von AppAPI entfernt den Container und auf Wunsch das Volume, aber
  kein Image. Wer den Platz braucht, entfernt es mit den Mitteln seiner
  Docker-Installation. Findling tut das nicht von sich aus, weil ein Image auf
  einem Host auch anderen Zwecken dienen kann.
- **Was AppAPI selbst führt**, also der Eintrag der ExApp, die
  Ereignis-Anmeldung und die Zuordnung zum Deploy-Daemon, verschwindet mit der
  Abmeldung der ExApp. Wird nur die Companion-App entfernt und die ExApp nicht
  abgemeldet, bleibt dieser Zustand stehen.
- **Nichts sonst.** Kein systemd-Dienst, kein Eintrag in einer Aufgabenplanung,
  kein Pfad auf dem Host außerhalb von Docker.

**Nutzerdateien bleiben unberührt.** Das ist ausdrücklich keine Zusage dieser
Seite, sondern die Nur-Lesen-Invariante des Projekts mit ihrem eigenen Gate: die
Schreib-Allowlist des Containers hat genau drei Einträge, und ein Test hält
diese Zahl fest. Eine Deinstallation weicht diese Disziplin nicht auf, weil sie
keine neue Schreibroute braucht. Die Grenze: das Gate prüft die Allowlist und
nicht jeden möglichen Schreibvorgang der Welt; was es beweist und was nicht,
steht in `docs/testing.md`.

## 4. Die empfohlene Reihenfolge, und was eine halbe Entfernung bedeutet

Findling besteht aus zwei Teilen, und keiner der beiden zwingt den anderen zur
Deinstallation (Entscheid D-17). Empfohlen ist diese Reihenfolge:

```
# 1. Die ExApp abmelden, mit oder ohne ihre Daten.
occ app_api:app:unregister findling_backend --rm-data

# 2. Die Companion-App entfernen, mit ausdrücklicher Absicht.
occ findling:purge --arm
occ app:remove findling
```

Erst das Backend, dann die Companion-App. Andersherum verliert der Container
seinen Anrufer, während er noch läuft.

Die beiden halben Zustände, und beide sind gutartig:

- **Companion ohne Backend:** die Statusseite zeigt ihren bestehenden Hinweis,
  dass das Backend nicht antwortet, und nennt die zuletzt erfassten Zahlen als
  solche. Die Suchleiste arbeitet weiter, nur ohne die Trefferliste von
  Findling. Kein Fehler, keine hängende Suche.
- **Backend ohne Companion:** der Container läuft weiter und hat keinen Anrufer
  mehr. Er fragt eine Arbeitsliste ab, die es nicht mehr gibt, und zieht sich
  daraufhin zurück: die Pause wächst von 15 Sekunden verdoppelnd bis auf 300
  Sekunden, also höchstens zwölf Versuche in der Stunde. Ins Protokoll schreibt
  er dabei eine Zeile je Fehlschlag für die ersten beiden Durchgänge und eine
  einzige Zeile, wenn er den Zustand erreicht hat, und danach schweigt er, bis
  die Arbeitsliste wieder antwortet. Antwortet sie wieder, ist die Pause sofort
  vorbei: der nächste Durchgang läuft ohne Wartezeit, ein laufender Index wird
  durch den Rückzug nie abgebrochen, und die Suche des Containers antwortet die
  ganze Zeit.

Warum die Obergrenze bei 300 Sekunden liegt und nicht höher oder niedriger: lang
genug, dass ein vergessener Container wochenlang nicht auffällt, kurz genug,
dass eine Wiederinstallation innerhalb von fünf Minuten bemerkt wird. Der Wert
steht als benannte Konstante `RETREAT_MAX_SECONDS` im Container, mit derselben
Begründung daneben.

Die Grenze dieses Abschnitts: gemessen ist die Richtung "Backend ohne
Companion", als Kette und auf allen vier Serverversionen, nämlich in
Feststellung 6 des Jobs aus Abschnitt 5. Die Richtung "Companion ohne Backend"
ist der bestehende Hinweis der Statusseite aus einer früheren Phase und hier
nicht als Kette gefahren.

## 5. Der Beweis in CI: was der Job feststellt und was nicht

Der Job `deploy-harp` (`.github/workflows/deploy-harp.yml`) installiert Findling
auf dem Weg einer Store-Installation, also über einen Deploy-Daemon mit HaRP, und
räumt danach wieder ab. Er läuft über eine Matrix aus vier Serverversionen:
Nextcloud 32, 33 und 34 mit PHP 8.2 und Nextcloud 35 mit PHP 8.3 (Entscheide
D-07 und D-23).

Der Job trifft sechs Feststellungen, jede mit eigener Fehlermeldung, und jede so
gebaut, dass eine leere Ausgabe rot ist und nicht grün:

1. **Ohne Kennzeichen bleibt das Volume.** `occ app_api:app:unregister
   findling_backend` entfernt den Container, und das Volume aus dem
   Installationsschritt liegt danach unverändert da. Diese Feststellung steht
   zuerst, weil sie nach Feststellung 3 nicht mehr zu treffen ist.
2. **Der Weg zurück.** Eine zweite Registrierung gelingt und nimmt genau das
   liegen gebliebene Volume, nicht ein neues. Das ist der Weg, den ein Admin
   nach einem Fehlversuch geht.
3. **Mit Kennzeichen verschwindet das Volume.** Nach `occ app_api:app:unregister
   findling_backend --rm-data` findet dieselbe Suche nach demselben Namen nichts
   mehr, und der Container ist ebenfalls fort.
4. **Ein Abschalten ohne Absicht räumt nichts.** Nach `occ app:disable findling`
   existieren alle drei Tabellen weiter und die Zahl der gespeicherten
   Einstellungen ist größer als null.
5. **Ein Entfernen mit Absicht räumt vollständig.** Nach `occ findling:purge
   --arm` und `occ app:remove findling` existiert keine der drei Tabellen mehr
   und die Zahl der Einstellungen ist null.
6. **Der Container ohne Companion zieht sich zurück.** Nach dem Entfernen der
   Companion-App läuft der Container weiter, meldet den Rückzug mit einer Zeile
   und schreibt danach höchstens fünf weitere Warn- oder Fehlerzeilen. Fünf ist
   die Grenze zwischen Rückzug und Fehlerschleife, und sie zählt den Zuwachs
   gegenüber dem Stand vor dem Entfernen, damit nichts mitgezählt wird, was
   vorher schon dastand.

Feststellung 4 steht vor Feststellung 5 und nicht danach: die Absichtsmarke ist
Einmalgebrauch, und die Aussage "ein Abschalten räumt nichts" lässt sich nur
treffen, solange keine Marke gesetzt ist.

Die Tabellen und die Einstellungen fragt der Job direkt an der Testdatenbank ab
und nicht über occ. Der Grund steht als Kommentar im Job: es gibt kein
occ-Kommando, das die Existenz einer Tabelle meldet, und ein occ-Aufruf, der
scheitert, gibt nichts aus, was sich von "keine Tabellen mehr" nicht
unterscheiden lässt. Der Dialekt wird vor der ersten Abfrage geprüft.

**Und was der Job ausdrücklich nicht feststellt.** Zwei Dinge, beide bewusst:

- **Nicht die Weboberfläche.** Der Job ruft ausschließlich occ auf. Der Schalter
  "Daten löschen" der App-Verwaltung von Nextcloud 32 und 33 (Abschnitt 2) wird
  von ihm nie angefasst und bleibt ungemessen.
- **Nicht das Container-Image.** Dass es liegen bleibt, ist Bauart der AppAPI
  (Abschnitt 3) und kein Fehler, den eine Prüfung finden könnte. Der Job sucht
  deshalb nicht danach.
