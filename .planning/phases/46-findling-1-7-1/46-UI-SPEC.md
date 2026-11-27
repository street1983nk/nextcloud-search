---
phase: 46
slug: findling-1-7-1
status: draft
base: .planning/phases/45-findling-1-7-0/45-UI-SPEC.md
created: 2026-11-27
---

# Phase 46: UI-Vertrag (Nachtrag zu 45-UI-SPEC)

Es gilt 45-UI-SPEC.md vollständig. Dieser Nachtrag ändert nur drei Stellen der Admin-Seite. Keine neue Farbe, kein neues Icon, keine neue Komponente, keine neue Zeichenkette außer den geänderten Katalogwerten. Nur Nextcloud-CSS-Variablen (nextcloud-ui), Hell und Dunkel über das Theming.

## 1. Hilfesatz der Ordnerliste (EXCL-07)

| Element | 1.7.0 | 1.7.1 |
|---|---|---|
| `#findling-rules-exclusions-help`, DE | "... Beispiel: Backups" | "... Beispiel: Sicherungen" |
| FR | "... Exemple : Backups" | "... Exemple : Sauvegardes" |
| EN | "... Example: Backups" | unverändert |
| ES, IT, NL, pt_BR, pt_PT, zh_TW | "... Backups" | Ende gleich dem Platzhalter des Katalogs (Copias de seguridad, Backup, Back-ups, Backup, Cópias de segurança, 備份) |

Der Platzhalter `#findling-rules-new` bleibt, wie 45-25 ihn gesetzt hat. Die Regel aus 45-UI-SPEC "Hilfesatz bleibt unverändert" ist für diesen einen Satz aufgehoben (E-46-01).

## 2. Enter in den Eingabefeldern (EXCL-08)

| Eingabe | Erwartung |
|---|---|
| Enter in `#findling-rules-new` mit gültigem Wert | Eintrag erscheint in der Liste wie nach Klick auf "Ausschluss hinzufügen", Feld leer, Fokus bleibt im Feld, Hinweis "ungespeichert" erscheint |
| Enter in `#findling-rules-patterns-new` mit gültigem Wert | ebenso für "Muster hinzufügen" |
| Enter bei leerem, doppeltem, zu langem Wert, voller Liste, Platzhalterzeichen im Ordnerfeld | dieselbe Feldmeldung wie beim Knopf, Wert bleibt im Feld |
| Enter während einer IME-Komposition (`isComposing`, keyCode 229) | nichts wird hinzugefügt, die Komposition wird bestätigt |
| Shift/Strg/Alt/Meta plus Enter | nichts |

Kein sichtbarer Unterschied im Ruhezustand; kein neuer Hinweistext.

## 3. Fehlerliste unter 360 px (ADM-05)

Ab 360 px gilt das Layout von 1.7.0 (drei Spalten Grund, Dateien, Zustand; Bilder `abn/22-v07-*` aus 45). Unter 360 px steht der Chip des Zustands unter dem Grund. Varianten (Owner wählt in 46-03, E-46-03):

- **A:** Spalte Zustand (Kopf und Zellen) unter 360 px ausgeblendet; im Zeilenkopf eine zweite Fassung des Chips, nur unter 360 px sichtbar. Zu jeder Breite genau eine Fassung im Accessibility-Baum.
- **B:** Template mit zweiter Zeile je Gruppe für Anzahl und Zustand, nur unter 360 px sichtbar, die Zellen der ersten Zeile entsprechend ausgeblendet; Tabellensemantik bleibt (kein `display: block` an Tabellenelementen).

Abnahmekriterien beider Varianten: bei 320 px kein Wort mitten im Wort umbrochen (Silbentrennung mit Bindestrich zulässig), keine waagerechte Scrollleiste, Chip ganz, Anzahl lesbar, Kontrast unverändert; bei 375 und 1280 px pixelgleich oder gleichwertig zu 1.7.0 (Vergleichsbild).

## Prüfmatrix

DE, EN, FR je 1280, 375 und 320 px, hell und dunkel; dazu zh_TW einmal bei 320 px hell (lange Wörter fehlen dort, aber die IME-Probe von Abschnitt 2 läuft in zh_TW).
