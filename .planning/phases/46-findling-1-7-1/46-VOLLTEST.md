# Volltest 46-07: Findling 1.7.1

Stand: 2026-11-27, Fenster `Freigabe Docker-Fenster 46-07` (vorher 4,8 GiB frei, `docker ps -q` leer; ein Stack `findling-vt` mit app und backend, danach gestoppt, `docker ps -q` leer). Playwright per Skript (Chromium headless 147, Playwright 1.59.1), das Playwright-MCP war getrennt. Bilder unter `bilder/volltest/`.

## Stand

| Teil | Stand |
|---|---|
| Repository-Kopf | 029d7307 (Code gleich audited_head 1a0abda0d6e9686d7ecc74e51cc959962cf0fa21, ci_head 6003b35352bb5be89ec0e85a1319129b209debc7) |
| Begleit-App | php/ des Arbeitsbaums am Kopf, in den Container gemountet, `installed_version` 1.7.1 nach `occ upgrade` |
| Container | Image `findling-backend:45-10-head` (Backend-Code von 1.7.0; seit v1.7.0 ist unter backend/src nichts geändert, `git diff --stat v1.7.0..HEAD -- backend/src` leer), meldet 1.7.0 |
| Nextcloud | 34.0.3 (SQLite), Instanz und Saat aus dem Volltest 45 |

Hinweis: Den Container in 1.7.1 neu zu bauen hätte nur die Versionsnummer geändert. Diese Konstellation (Begleit-App 1.7.1, Container 1.7.0) ist genau der Zwischenstand des Updates "Begleit-App zuerst"; der Store-Container 1.7.1 läuft in CI (HaRP deploy, frische Installation und Upgrade).

## Probentabelle

| Probe | Sprache | Breite | Thema | Erwartung | Ergebnis | Bild |
|---|---|---|---|---|---|---|
| P-UPD | alle | - | - | Update 1.7.0 -> 1.7.1, Begleit-App zuerst, Suche direkt danach mit Treffer vor dem ersten Aufruf der Admin-Seite, keine Drift-Warnung | grün: `occ upgrade` "Update successful", installed_version 1.7.1, backend_app_version bleibt 1.7.0 (gleiche Minor-Version, keine Migration); 12:49:52 UTC OCS-Suche als testuser nach `vt45home`: 1 Treffer `Notiz-Home.txt` mit Ausschnitt, vor jedem Aufruf der Admin-Seite; Zeilen "report different versions" im nextcloud.log vorher 0, nachher 0 | keins (OCS) |
| P-HLP | DE | 1280 | hell | Hilfesatz endet auf den Platzhalter | "... Beispiel: Sicherungen" / "Sicherungen" | volltest/probes-p-hlp-de.png |
| P-HLP | EN | 1280 | hell | wie oben | "... Example: Backups" / "Backups" | volltest/probes-p-hlp-en.png |
| P-HLP | FR | 1280 | hell | wie oben | "... Exemple : Sauvegardes" / "Sauvegardes" | volltest/probes-p-hlp-fr.png |
| P-HLP | zh_TW | 1280 | hell | wie oben | "... 範例：備份" / "備份" | volltest/probes-zh-p-hlp-zh_TW.png |
| P-ENT | DE | 1280 | hell | Enter fügt in Ordner- und Musterfeld hinzu (Feld leer, Fokus bleibt); Enter leer: empty; Enter doppelt: Meldung, Wert bleibt; Shift+Enter nichts; Enter mit `Archiv*`: wildcard, Wert bleibt | alle 9 Teilproben grün ("Einen Ordnerpfad eingeben.", "Dieser Pfad ist bereits ausgeschlossen.", "Ein Muster eingeben.", "Dieses Muster steht bereits in der Liste.", "Ordner ohne * oder ?. ...") | volltest/probes-p-ent-de.png |
| P-ENT | EN | 1280 | hell | wie oben | alle 9 grün ("Enter a folder path.", "This path is already excluded.", ...) | volltest/probes-p-ent-en.png |
| P-ENT | FR | 1280 | hell | wie oben | alle 9 grün ("Saisir un chemin de dossier.", "Ce chemin est déjà exclu.", ...) | volltest/probes-p-ent-fr.png |
| P-ENT | zh_TW | 1280 | hell | wie oben | alle 9 grün ("請輸入資料夾路徑。", "此路徑已被排除。", ...) | volltest/probes-zh-p-ent-zh_TW.png |
| P-XSS | DE, EN, FR, zh_TW | 1280 | hell | `<img src=x onerror="window.__p46=1">` per Enter steht als Text in der Liste, nichts ausgeführt | je: als Text ja, ausgeführt nein, kein img in der Liste, Konsole leer | - |
| P-IME | zh_TW | 1280 | hell | Enter während einer Komposition über CDP (`Input.imeSetComposition` "ㄅㄟ", `Input.dispatchKeyEvent` Enter mit keyCode 229) fügt nichts hinzu; danach fügt ein gewöhnliches Enter das komponierte Wort hinzu | 62 -> 62 Zeilen während der Komposition, danach 62 -> 63 mit "備份" | volltest/ime-p-ime-zh_TW.png |
| P-IME | zh_Hant_TW | 1280 | hell | wie oben unter der Sprache zh_Hant_TW (Nextcloud fällt dort auf Englisch zurück, KAT-04) | wie oben, grün | volltest/ime-p-ime-zh_Hant_TW.png |
| P-IME Positivkontrolle | zh_TW | 1280 | hell | lokale, nicht committete Mutation ohne `isComposing` und ohne keyCode 229: die Komposition fügt hinzu | rot wie verlangt: 62 -> 63 während der Komposition; admin.js danach zurückgesetzt, `git status` leer | volltest/ime-ctl-p-ime-zh_TW.png |
| P-320 | DE, EN, FR | 320, 375, 1280 | hell, dunkel | Fehlerliste ohne Wortbruch ohne Bindestrich (Messung "bare" aus 46-LAYOUT-320.md), kein waagerechtes Scrollen | überall 0 Wortbrüche ohne Bindestrich, 0 px Scrollen; Brüche mit Silbentrennung DE 6/10/3, EN 2/3/0, FR 7/6/1 wie am GREEN-Stand von 46-03 | volltest/vt-<lang>-<breite>-<thema>.png |

## Playwright-Matrix

Ganze Admin-Seite (Vollbild), DE, EN, FR je 1280, 375 und 320 px, hell und dunkel, 18 Bilder `volltest/<lang>-<breite>-<thema>.png`, dazu `volltest/zh_TW-320-light.png`: waagerechtes Scrollen überall 0 px, Konsole ohne Fehler in allen 19 Aufnahmen.

## Sprachprüfung

Geändert seit 1.7.0 sind nur der Hilfesatz der Ordnerliste (18 Kataloge, je das Ende) und die CHANGELOGs. Im Browser gesehen: DE "Beispiel: Sicherungen", EN "Example: Backups", FR "Exemple : Sauvegardes" (geschütztes Leerzeichen vor dem Doppelpunkt wie im übrigen Satz), zh_TW "範例：備份" (vollbreiter Doppelpunkt wie im übrigen Satz). Positivkontrolle: die Probe P-HLP meldet einen alten Katalogwert als Fehler (Gate 46-01, Mutation fr.js rot; im Browser hätte P-HLP mit dem Stand 1.7.0 "Beispiel: Backups" gegen "Sicherungen" gezeigt). Kein Sprachfehler gefunden.

## impeccable

Regelblock und Fehlerliste nach nextcloud-ui und impeccable durchgesehen (Bilder der Matrix und aus 46-LAYOUT-320.md): keine neue Farbe, kein neues Icon, nur Nextcloud-Variablen; der Chip unter dem Grund nutzt Abstand `--default-grid-baseline` und dieselbe Chip-Komponente wie die Spalte; hell und dunkel gleichwertig; Fokus bleibt nach Enter im Feld. Kein Befund.

## Umlaut-Audit

Vorfilter `grep -nE "(ae|oe|ue)[a-z]|ss[^a-z]"` über die in v1.7.0..HEAD hinzugefügten Zeilen:

| Datei | Zeilen | Treffer | Bewertung |
|---|---|---|---|
| php/l10n/de.json, de_DE.json, de.js, de_DE.js | je 1 | 0 | - |
| CHANGELOG.de.md | 12 | 0 | - |
| README.md | 0 | 0 | - |
| docs/admin-page.md | 18 | 0 | - |
| docs/store-listing.md | 76 | 9 | "Abschluss", "Ausschluss", "Phasenabschluss", "bauen", englische Workflow-Wörter (success, process): keine Ersatzschreibung |
| docs/l10n-french.md, -italian.md, -spanish.md | je 1 | je 1 | französische, italienische, spanische Wörter ("génériques", "questa", "muestran"): keine Ersatzschreibung |
| übrige docs/l10n-*.md | je 1 | 0 | - |

Gedankenstriche U+2013/U+2014 in allen hinzugefügten Zeilen außerhalb .planning: 0.

## Befunde

Keine. Alle Proben grün, die Positivkontrollen rot wie verlangt.

## Owner-Abnahme

Offen (46-07 Task 2, gemeinsame Abnahme per Playwright).
