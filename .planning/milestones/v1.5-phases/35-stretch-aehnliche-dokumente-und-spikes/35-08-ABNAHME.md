# 35-08: Abnahme der Aehnlich-Ansicht (Playwright, http://localhost:8090)

## Stand

| Punkt | Wert |
|---|---|
| Commit des Haupt-Checkouts | bb3dab5d (main, Wellen 1 bis 6 gemergt) |
| Companion auf 8090 | findling 1.4.2, php/ aus dem Haupt-Checkout eingebunden |
| Backend | Host-Prozess Port 10035, Start ueber register-exapp.sh mit FINDLING_EMBED_MODEL_DIR=.dev/model |
| Nutzer | admin, kollegin, testuser (alle vorhanden, keiner neu angelegt) |
| nextcloud.log-Marke | 5365 Zeilen vor den Proben |
| exapp.log-Marke | 42 Zeilen vor den Proben |

## Eingriffe in den Dev-Stack (Rueckbau am Ende vermerkt)

1. Backend mit Modellverzeichnis neu gestartet (vorher lief es ohne Modell):
   `FINDLING_PORT=8090 FINDLING_EMBED_MODEL_DIR=<repo>/.dev/model sh scripts/dev/register-exapp.sh`.
   Owner-Entscheid 19.10.2026: alle 8499 Dateien einbetten.
2. Die Marke `embedding_version` in `.dev/storage/state.db` stand auf `unknown`.
   Bei `unknown` liefert der Produktcode bewusst keine Nachlieferung (er wartet
   auf `embedded == indexed`); nur ein echter Drift loest die Kette
   Leeren/Stempeln/Nachliefern aus. Fuer den Lauf wurde die Marke deshalb per
   SQL auf den realen Altwert `multilingual-e5-small/int8/384/512` gesetzt
   (anderer Tokendeckel = Drift); die Kette lief danach auf dem Produktpfad.
   Eingriff nur in der Dev-Instanz, kein Codeeintrag.

## Einbettungsstand vor den Proben

438 von 510 lebenden Dokumenten tragen Vektoren; die restlichen 72 haben keinen
gespeicherten Text (Bilder, leere Dateien) und koennen konstruktionsbedingt
keinen Vektor bekommen. Die files-Tabelle haelt 8429 indexierte Zeilen, davon
sind nur 510 lebend (Rest Tombstones des alten Lastkorpus). Quelle der Proben:
Datei 14 (Templates/Triangle.odp, admin) mit 3 Nachbarn (27, 28, 15).

## Proben (Playwright, Chrome, admin auf http://localhost:8090, 19./20.10.2026)

Bildschirmfotos: Scratchpad-Ordner 35-08/ der Session (p1..p8, Pfad unten).

| Nr | Probe | Erwartung | Ergebnis | Foto |
|---|---|---|---|---|
| 1 | Ergebnisseite ?query=Triangle | je Treffer genau ein a.findling-hit__similar als Geschwister NACH a.findling-hit__link, aria mit Titel | GRUEN: 2 Treffer, je 1 Zeilen-Link + 1 Aehnlich-Link, aria "Aehnliche Dokumente zu Triangle.odp" | p1-ergebnisseite-de.png |
| 2 | Tastatur | Tab: erst Zeilen-Link, dann Aehnlich-Link, Fokusrahmen | GRUEN: DOM-Reihenfolge link/similar/link/similar, Tab vom Zeilen-Link landet auf similar, outline auto 1px | p2-tastatur-fokus-de.png |
| 3 | Klick Aehnlich-Link (Datei 14) | Adresse similar=14 + uebrige Parameter; ein App-h1 "Aehnlich zu: Triangle.odp"; Rueckweg; max 10 Treffer; keine Facetten/Pager/weiterer Aehnlich-Link; Quelle nicht in Liste | GRUEN: URL ?cursors=0&page=1&similar=14&fp=...&query=Triangle; 3 Nachbarn /f/27 /f/28 /f/15 (14 nicht dabei); 0 weitere Aehnlich-Links; Dateityp/Zeitraum/Sortierung weg; kein Pager | p3-aehnlich-ansicht-de.png |
| 4 | Rueckweg + Browser-Zurueck | selbe Liste (Filter+Seite), Ausgangszeile markiert | GRUEN: Rueckweg-Link = selbe Liste ohne similar; Browser-Zurueck (back_forward) markiert findling-hit-14 mit SR-Text "zuletzt geoeffnet" | p4-rueckweg-markierung-de.png |
| 5 | Leerzustand (Datei 16, keine Nachbarn) | abgenommener Leersatz + Erklaersatz, keine Zahl | GRUEN: "Keine aehnlichen Dokumente gefunden" + Erklaersatz zeichengleich, keine Zahl | p5-leerzustand-de.png |
| 6 | Negativkontrolle | similar=190 (kollegin) und similar=999999999 zeigen denselben Satz "nicht verfuegbar" byte-gleich; similar=abc = normale Ergebnisseite | GRUEN: app-content beider Seiten byte-identisch (2173 Bytes); h1 "Aehnliche Dokumente" OHNE Dateititel; abc-Antwort byte-gleich zur normalen Ergebnisseite | p6-fremde-datei-de.png |
| 7 | Konsole + nextcloud.log | keine Fehler aus search.js, keine neuen NC-Fehler | GRUEN: Konsole 0 Errors/0 Warnings ueber alle Proben; 5 NC-Logzeilen seit Marke 5365, alle aus den Backend-Neustarts (stale secret, 21:43/23:19 UTC), keine aus den Proben | (Konsole, kein Foto) |
| 8 | Mobil 390 px | Link bricht sauber um, kein Ueberlappen | GRUEN: simTop 770 unter rowBottom 769, keine Ueberlappung, kein horizontales Scrollen | p8-mobil-390px-de.png |

## Wortlaut-Tabelle de/en/fr (live gesehen)

| Element | de | en | fr |
|---|---|---|---|
| Link je Treffer | Aehnliche Dokumente | Similar documents | Documents similaires |
| aria-Label | Aehnliche Dokumente zu %s | Similar documents to %s | Documents similaires a %s |
| h1 | Aehnlich zu: Triangle.odp | Similar to: Triangle.odp | Similaire a : Triangle.odp |
| Rueckweg | Zurueck zu den Treffern | Back to the results | Retour aux resultats |
| Leersatz | Keine aehnlichen Dokumente gefunden | No similar documents found | Aucun document similaire trouve |
| Erklaersatz | Keine Ihrer anderen Dateien ist inhaltlich nah genug. ... | None of your other files is close enough in content. ... | Aucun de vos autres fichiers n'est assez proche par son contenu. ... |
| nicht verfuegbar | Diese Datei ist nicht verfuegbar | This file is not available | Ce fichier n'est pas disponible |

Fotos: p3-aehnlich-ansicht-de/en/fr.png (Umlaute/Akzente in dieser ASCII-Tabelle
vereinfacht; die Kataloge tragen die echten Zeichen, live gegengeprueft).

## Negativkontrolle

Siehe Probe 6: fremde fileid (190, kollegin) und nicht existente fileid
(999999999) liefern byte-identisches app-content-HTML; kein Titel der fremden
Datei auf dem Schirm; similar=abc faellt still auf die normale Ergebnisseite.

## Offene Fragen an den Owner (beantwortet in der Runde)

1. Suchformular in der Aehnlich-Ansicht: Owner folgt der Empfehlung des
   Ausfuehrenden ("was du empfehlst"), Empfehlung und Entscheid: SO BELASSEN.
   Von der Ansicht aus kann direkt eine neue Suche gestartet werden; ein
   Ausblenden waere eine nicht erbetene Aenderung.
2. Jede Seite traegt zwei h1 (das versteckte Nextcloud-h1 plus das App-h1).
   Gilt auch fuer die normale Ergebnisseite, Bestand vor Phase 35, kein
   neuer Befund.

## Gemeinsame Runde und Abnahme

Gemeinsame Runde am 20.10.2026 im Playwright-Chrome auf http://localhost:8090
(admin, Sprache de; en/fr per Protokoll-Screenshots): Ergebnisseite mit Link je
Treffer, Aehnlich-Ansicht zu Triangle.odp (3 Nachbarn), Rueckweg und
Browser-Zurueck mit Markierung, Leerzustand (Datei 16), nicht-verfuegbar
(Datei 190). Keine Aenderungswuensche.

Owner-Abnahme: 20.10.2026, "Abgenommen" (alle Elemente wie vorgelegt; Suchformular bleibt nach Empfehlung sichtbar)

## Aufraeumen

- Keine Testdateien hochgeladen, kein Testnutzer angelegt: nichts zu entfernen
  (kollegin/testuser bestanden vorher und bleiben).
- Admin-Sprache: Ausgangswert de, nach den Runden wieder de (occ user:setting
  admin core lang de).
- Dev-Backend laeuft weiter mit Modellverzeichnis (Owner-Entscheid 19.10.,
  alle Dateien eingebettet); die Marke embedding_version ist durch die
  Produktkette regulaer auf multilingual-e5-small/int8/384/1024 gestempelt,
  der Dev-Eingriff damit ueberholt.
- Befund fuer 35-12 (Audit-Notiz): Bei Marke "unknown" liefert der Code
  keine Nachlieferung (wartet auf embedded == indexed); auf einer Instanz,
  die laenger ohne Modell lief, fuellt sich der Bestand erst nach einem
  echten Drift. Dazu: requeue-te embed-Zeilen weckten den armed-Poller im
  Leerlauf nicht sichtbar auf (Beobachtung 20.10., 5 Zeilen blieben ueber
  Minuten liegen; nach Backend-Neustart sofort verarbeitet).
