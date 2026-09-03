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
Messwert. Die Wiederholung derselben Kette auf Nextcloud 32, 33, 34 und 35 in
CI gehört zu Plan 05-08 und ist bis dahin ein offener Punkt.
