# 34-05: Protokoll der gemeinsamen Owner-Abnahme

Stand: 19.10.2026, Commit ace53f3a (main, 34-01 bis 34-04 gemergt), Dev-Instanz
Nextcloud 34.0.3 auf http://localhost:8090 (`scripts/dev/compose.yaml`, Dienst
`app`, Backend als Host-Prozess), Admin-Sprache zu Beginn de, nextcloud.log
Marke 5336 Zeilen.

Ausgangszustand: `occ app:list` ohne fulltextsearch und files_fulltextsearch,
keine appconfig-Zeile `enabled` fuer beide IDs (config:app:get je leer, exit 1).

Bildschirmfotos im Scratch dieser Session:
`C:\Users\Student\AppData\Local\Temp\claude\C--Users-Student\6665a6d1-bd54-427c-8253-95680556dfca\scratchpad\34-05\`

## Proben (Task 1)

| Nr | Probe | Erwartung | Ergebnis | Foto |
| --- | --- | --- | --- | --- |
| 1 | Negativkontrolle ohne Flags | `#findling-banner-parallel` im DOM, `hidden`, nichts sichtbar | wie erwartet (hiddenAttr true, display none, Elternblock `findling-coverage-banners`) | p1-negativ-de.png |
| 2a | Flag `fulltextsearch` = yes, de | Banner sichtbar, Satz laut 34-WORTLAUT (B), Link de-Tag-URL, `target="_blank"`, `rel="noreferrer noopener"` | wie erwartet, Satz zeichengleich, href `blob/v1.5.0/docs/migrate-from-fulltextsearch.md` | p2-banner-de.png |
| 2b | dieselbe Probe, Admin-Sprache en | Satz en zeichengleich, Link `.en.md` | wie erwartet | p2-banner-en.png |
| 2c | dieselbe Probe, Admin-Sprache fr | Satz fr zeichengleich, Link `.fr.md` | wie erwartet | p2-banner-fr.png |
| 2d | Owner-Aenderung in der Runde: Doku-Link als Button mit Rahmen | Rahmen 2px currentColor, Theme-Radius, fett, Hover/Fokus unterstrichen | umgesetzt (Template-Klasse `findling-banner__link` + admin.css), live gesehen, Owner: "jetzt sieht es gut aus" | p2b-banner-de-button.png |
| 3 | nur `files_fulltextsearch` = yes | Banner sichtbar | wie erwartet | (DOM-Pruefung, visible true) |
| 4 | `fulltextsearch` nur fuer Gruppe `findling-probe`, Admin nicht Mitglied | Banner sichtbar (isEnabledForAnyone, nicht isEnabledForUser) | wie erwartet | p4-gruppenflag.png |
| 5 | Flags entfernt, Seite neu geladen | Banner wieder `hidden`; Poll laeuft 8 s ohne Skriptfehler, Banner bleibt wie gerendert (PE-34-2) | wie erwartet, 0 Konsolenfehler | p5-flags-weg-hidden.png |
| 6 | Admin-Sprache es mit gesetztem Flag | Satz aus dem es-Katalog, Link zeigt auf `.en.md` | wie erwartet | p6-es-fallback-en.png |
| 7 | Konsole und nextcloud.log ueber alle Proben | keine Fehler aus admin.js, keine neuen Logzeilen durch die simulierten Flags | 0 Konsolenfehler (alle Runden), Log unveraendert 5336 Zeilen, kein Rueckfall noetig | (Messwerte) |
| 8a | GitHub `main`: drei Seiten rendern | Titel, Sprachumschalter, vier Abschnitte, Codebloecke | de/en/fr wie erwartet, Umschalter je die zwei anderen Sprachen | p8-seite-de.png, p8-seite-en.png, p8-seite-fr.png |
| 8b | READMEs de/en/fr | Abschnitt direkt vor "Installation", abgenommener Wortlaut, Link auf die Seite der eigenen Sprache | wie erwartet in allen drei Dateien | p8-readme-de.png, p8-readme-en.png, p8-readme-fr.png |
| 9 | Store-Entwurf aufbereitet | Abschnitt `# Entwurf v1.5.0 (Teil Phase 34)` als Text fuer die Runde | siehe Abschnitt Store-Entwurf unten | (Textprobe) |

Hinweis zu den Tag-Links: die Banner-Links zeigen auf `blob/v1.5.0/...`; der
Tag-Link geht erst mit v1.5.0 auf. Gelesen wurden die Seiten deshalb ueber
`blob/main/docs/migrate-from-fulltextsearch*.md`.

Keine rote Probe. Ein Befund aus der Runde selbst: der Doku-Link war ein
nackter Link und dem Owner zu unauffaellig; als Owner-Aenderung umgesetzt
(Zeile 2d), Gates danach gruen (695 Tests der drei Gate-Module, `php -l`
sauber, Baumhash-Ratsche mit Journalabsatz Plan 34-05 nachgezogen).

## Wortlaut-Tabelle der sichtbaren neuen Texte

| Text | de | en | fr | Foto |
| --- | --- | --- | --- | --- |
| Banner-Satz | Mindestens eine App des Volltextsuche-Frameworks (fulltextsearch, files_fulltextsearch) ist neben Findling aktiviert. Treffer aus derselben Datei koennen dann doppelt in der Suchleiste erscheinen. Diese Apps deaktivieren, sobald Findlings erster Indexlauf abgeschlossen ist. | At least one app of the full text search framework (fulltextsearch, files_fulltextsearch) is enabled next to Findling. Results from the same file can then appear twice in the search bar. Disable these apps once Findling has finished its first index run. | Au moins une application du framework de recherche plein texte (fulltextsearch, files_fulltextsearch) est activee a cote de Findling. Les resultats d'un meme fichier peuvent alors apparaitre deux fois dans la barre de recherche. Desactiver ces applications une fois la premiere indexation de Findling terminee. | p2-banner-de/en/fr.png |
| Banner-Link (Button) | Schritte in der Dokumentation | Steps in the documentation | Etapes dans la documentation | p2b-banner-de-button.png |
| README-Abschnitt | Schritte zum Abschalten von fulltextsearch/Elasticsearch und was sich aendert: docs/migrate-from-fulltextsearch.md. | Steps to switch off fulltextsearch/Elasticsearch and what changes: docs/migrate-from-fulltextsearch.en.md. | Etapes pour desactiver fulltextsearch/Elasticsearch et ce qui change : docs/migrate-from-fulltextsearch.fr.md. | p8-readme-de/en/fr.png |

(Franzoesische Akzente stehen in den Katalogen und Seiten korrekt; diese
Tabelle ist ASCII-vereinfacht, massgeblich sind 34-WORTLAUT.md und die Fotos.)

## Store-Entwurf (Probe 9, fuer Entscheid in der Runde)

Abschnitt `# Entwurf v1.5.0 (Teil Phase 34)` aus `docs/store-listing.md`:
eine Verweiszeile je Sprache, gleich in beiden Store-Eintraegen, hinter der
Funktionsliste, vor dem MCP-Connector-Absatz, absolute Tag-URL, keine Zahl:

- en: Switching from fulltextsearch/Elasticsearch: [steps in the documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.en.md)
- de: Umstieg von fulltextsearch/Elasticsearch: [Schritte in der Dokumentation](https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.md)
- fr: Passer de fulltextsearch/Elasticsearch a Findling : [etapes dans la documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.fr.md)

Wortlaut vom Owner am 19.10.2026 abgenommen (34-WORTLAUT D); offen ist die
foermliche Release-Abnahme (REL-05, info.xml erst in Phase 36).

## Gemeinsame Runde (Task 2)

Gefahren am 19.10.2026 mit dem Owner am geteilten Playwright-Browser: Banner
in de gelesen (mit Flag), Owner-Aenderung "der doku button braucht ein rahmen"
sofort umgesetzt und erneut gezeigt ("jetzt sieht es gut aus"), en und fr laut
Protokoll, Flag-Wechsel live gesehen, Seiten und READMEs auf GitHub `main`.

Offene Entscheide des Owners in der Runde: Gesamt-Abnahme und Entscheid zum
Store-Entwurf (abnehmen oder offen bis REL-05). Beide fielen am 19.10.2026,
siehe unten.

## Owner-Abnahme (Task 2/3)

Owner-Abnahme: 19.10.2026, "abgenommen" (Phase 34 gesamt; eine Aenderung in der Runde: "bei dem banner fehlt was der doku buttom braucht ein rahmen" -> Doku-Link als Button mit Rahmen umgesetzt, danach "jetzt sieht es gut aus"; Store-Entwurf auf Nachfrage ebenfalls abgenommen, Antwort "Auch abgenommen", info.xml bleibt bis REL-05)

Owner-Wort woertlich: "abgenommen" (19.10.2026); zum Store-Entwurf auf die
Nachfrage "Gilt das abgenommen auch fuer den Store-Entwurf ...": "Auch
abgenommen". Folge: Kopfsatz in docs/store-listing.md auf "Owner-Abnahme
19.10.2026", Gate-Konstante DRAFT_HEAD mitgezogen; info.xml unveraendert bis
REL-05 (Phase 36).

## Aufraeumen (Task 3)

Alle simulierten Flags entfernt (config:app:delete fulltextsearch enabled;
files_fulltextsearch war schon weg, Gruppe findling-probe geloescht),
Admin-Sprache wieder de (Ausgangswert), Banner wieder hidden: Beleg
p9-aufgeraeumt-hidden.png.
