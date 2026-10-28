# Phase 34: Umstiegsweg, Kontext

Owner-Entscheide (Stand 19.10.2026), gesperrt für die Planung. Grundlage: 34-RESEARCH.md (19.10.2026), ROADMAP.md Phase 34, REQUIREMENTS.md UMST-01 bis UMST-03.

## Entscheide

- **D-34-01 Form der Umstiegs-Seite (beantwortet O1):** Drei Dateien nach README-Muster: `docs/migrate-from-fulltextsearch.md` (Deutsch, Standard), `docs/migrate-from-fulltextsearch.en.md`, `docs/migrate-from-fulltextsearch.fr.md`. Zeile 1 jeder Datei ist der Sprachumschalter wie `README.md:1` (eigene Sprache ohne Link, die beiden anderen verlinkt). Dateinamen ASCII und englisch. Owner-Wort 19.10.2026.
- **D-34-02 Nachweis des Admin-Hinweises (beantwortet O8):** UMST-02 wird per PHPUnit mit einem `IAppManager`-Stub belegt (keine App, nur fulltextsearch, nur files_fulltextsearch, beide) plus einer Banner-Sichtprobe auf 8090 mit simuliertem App-Flag. KEIN Elasticsearch-Container (RAM), die Folge "doppelte Treffer" bleibt aus dem Quelltext belegt (fulltextsearch registriert einen eigenen Unified-Search-Anbieter). Owner-Wort 19.10.2026.

## Planer-Entscheidungen (aus 34-RESEARCH, Owner kann in 34-01 widersprechen)

- **PE-34-1 Prüfklasse:** neue Klasse `OCA\Findling\Service\ParallelSearchService` mit Konstante `APP_IDS = ['fulltextsearch', 'files_fulltextsearch']` und `active(): bool` über `IAppManager::isEnabledForAnyone()` (seit NC 32, gecacht je Request). Nicht `isEnabledForUser()` (verfehlt Gruppenfreigaben), nicht `isInstalled()` (deprecated). Plattform-Apps (`fulltextsearch_elasticsearch`, `fulltextsearch_sql`, `fulltextsearch_postgresql`) lösen den Hinweis nicht aus, weil sie allein nichts in die Suchleiste bringen.
- **PE-34-2 Bauweise des Hinweises:** fester Schlüssel `parallelSearch` (bool) in `AdminViewService::overview()`; im Template ein eigener Banner `findling-banner-parallel` (Art `warning`) außerhalb der `$banners`-Schleife im selben `#findling-coverage-banners`, nur serverseitig gerendert; das Skript `php/js/admin.js` fasst ihn nicht an (App-Wechsel geschieht auf der Apps-Seite, danach lädt der Admin ohnehin neu). Link als eigenes `<a target="_blank" rel="noreferrer noopener">` mit dem vorhandenen Schlüssel "Steps in the documentation"; die URL steht nie im Katalog.
- **PE-34-3 Linkform:** Admin-Hinweis und Store-Entwurf verlinken absolut auf die Tag-URL `https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch{,.en,.fr}.md`, sprachabhängig über `IL10N::getLanguageCode()` (beginnt mit `de`: `.md`, mit `fr`: `.fr.md`, sonst `.en.md`); drei vollständige URL-Literale in einer Map im Template, kein zusammengesetzter String. READMEs verlinken relativ die Seite ihrer Sprache. Tag-Links gehen erst mit dem Tag v1.5.0 auf; bis dahin prüft ein Gate, dass die Zieldatei im Repo existiert (wie PE-8 in Phase 33).
- **PE-34-4 Gate:** neues Modul `backend/tests/test_migration_path.py` (Pflichtformel je Sprache, Verbot "einzige OCR" und Entsprechungen mit Positivkontrolle `docs/performance.md:1025`, Sprachumschalter, Links, Ehrlichkeitswörter, keine Halbgeviert- oder Geviertstriche; ab 34-04 auch README-Verweise und Store-Entwurfsabschnitt). Verbotene Wörter aus Hälften zusammengesetzt wie `test_store_metadata.py:186-196`, Quelltext nur ASCII.
- **PE-34-5 Linkgate verallgemeinert:** `scan_limits_link()` (`test_admin_ui_contract.py:4573-4596`) verlangt heute genau einen Doku-Link mit Anker. Es wird im PHP-Plan 34-03 so verallgemeinert, dass genau die erwartete Menge gilt (Grenzblock-Link mit Anker plus drei Seiten-Links ohne Anker), jeder auf Tag `v1.5.0`, jede Zieldatei unter `docs/` vorhanden.
- **PE-34-6 Alle PHP-Änderungen in einem Plan (34-03):** PHP-Baumhash `PHP_FILES_TODAY` 103 auf 105 (Service plus PHPUnit-Test), Schlüsselzahl 340 auf 340 plus neue Schlüssel (Erwartung 341).
- **PE-34-7 info.xml bleibt unverändert** bis REL-05 (Phase 36). Ein `<documentation><admin>`-Element (O6) wird höchstens als Owner-Antwort notiert und in Phase 36 umgesetzt.

## Leitplanken (bindend für Wortlaut und Seiten)

- **Pflegestand ehrlich:** fulltextsearch wird wieder gepflegt (fulltextsearch v35.0.0 am 20.09.2026, fulltextsearch_elasticsearch v35.0.1 und v34.0.3 am 07.10.2026). Die Wörter "verwaist", "tot", "nicht gepflegt" (und en/fr-Entsprechungen) sind auf der Umstiegs-Seite verboten. Store-Stand vor dem Schreiben der Seiten (34-02) neu abfragen, Datum "Stand <TT.MM.JJJJ>" auf die Seite.
- **Nicht schreiben:** "fulltextsearch braucht Elasticsearch". Richtig: die Plattform-App `fulltextsearch_elasticsearch` braucht einen Elasticsearch-Dienst; es gibt Drittanbieter-Plattformen ohne Suchdienst.
- **Pflichtformel de wörtlich:** "OCR ohne Dateiänderung und ohne Elasticsearch" (in Prosa mit Umlaut; REQUIREMENTS schreibt ASCII). en/fr nach Owner-Antwort O2.
- **"einzige OCR" nie**, auch nicht verneint oder zitiert, in keiner Sprache und keiner ausgelieferten Datei (Gate). Ausnahme nur der bestehende, sachfremde Satz `docs/performance.md:1025` "keine einzige OCR-Seite" (Bindestrich-Fortsetzung), den das Gate per Lookahead nicht trifft und als Positivkontrolle liest.
- **Funktionsvergleich nur Geliefertes** (Phasen bis 33, alles in `main`): Volltextsuche mit deutscher Wortbehandlung, Texterkennung für gescannte PDFs und Bilder ohne Dateiänderung, semantische Suche, Dateitypen inklusive EML, ZIP-Inhalt, DOC, XLS, HEIC, Filter nach Dateityp und Ordner, Ausschluss von Ordnern und Mustern, Rechteprüfung jedes Treffers, erster Indexlauf von selbst, Leistungsprofile. "Ähnliche Dokumente" (Phase 35) ist verboten. Höchstens eine Zahl.
- **Verluste ehrlich nennen:** Deck-Karten werden nicht mehr volltextindexiert; externe Speicher bei Findling standardmäßig aus; Voraussetzungen AppAPI mit HaRP und Nextcloud 33 bis 35; Gruppe "File contents" statt "Full Text Search".
- **Keine Herabwürdigung** fremder Apps; Fremd-OCR-Apps außerhalb des fulltextsearch-Stacks werden nicht genannt (Research-Empfehlung, Owner kann in O5 anders entscheiden).
- Vokabelregel E-H2 (gesperrter Wortstamm in deutscher Prosa unter `docs/`, `test_public_artifacts.py:272-273`), keine Halbgeviert- oder Geviertstriche, keine Emojis, Umlaute nur in deutscher Prosa, nie in URLs, Ankern, Dateinamen, Code.
- Kurztext-Regel für README und Store: eine Zeile, Faktenform, keine weitere Zahl.

## Offene Owner-Fragen für den Wortlaut-Checkpoint 34-01

O1 und O8 sind durch D-34-01 und D-34-02 beantwortet und werden nicht erneut gefragt.

- **O2 Pflichtformel en/fr:** Vorschlag "OCR without changing files and without Elasticsearch" / "OCR sans modifier les fichiers et sans Elasticsearch".
- **O3 Verbotsgate-Reichweite:** nur "einzige OCR" oder auch "only OCR" und "seule(s) OCR"; Dateireichweite `docs/**` (ohne `docs/measurements/**`), `README*.md`, `CHANGELOG.md`, beide `info.xml`, `php/templates/**`, `php/l10n/**`, `store/**` nur Textdateien (`.md`, `.txt`, `.xml`, `.json`, `.html`; Bilder wie PNG ausgenommen); Bindestrich-Ausnahme `docs/performance.md:1025` per Lookahead `(?![-\w])` bestätigen.
- **O4 Vergleichsform:** zwei Faktenlisten "Was Findling mitbringt" und "Was sich beim Umstieg ändert" statt Gegenüberstellung; Deck-Verlust und externe Speicher darin nennen.
- **O5 Drittanbieter:** fulltextsearch_sql und fulltextsearch_postgresql auf der Seite erwähnen oder nur "die verwendete Plattform-App".
- **O6 Admin-Hinweis-Link und info.xml:** sprachabhängig auf Tag-URL (Empfehlung) oder fest Englisch; `<documentation><admin>` in `info.xml` in Phase 36 ergänzen ja/nein.
- **O7 Hinweissatz-Wortlaut** de/en/fr mit Folge "doppelte Treffer" (Vorschlag en im Research).
- **O9 README-Verweis-Platz:** Zeile in "Was Findling kann" oder eigener kurzer Abschnitt "Umstieg" vor "Installation".
- **O10 UI-SPEC:** entbehrlich wie D-33-02 (ein Banner, kein neues Bedienelement), Empfehlung ja.

## Deferred (nicht in dieser Phase)

- Ähnliche Dokumente (Phase 35) im Funktionsvergleich.
- Änderung der `info.xml`-Texte und Store-Einreichung (REL-05, Phase 36); auch ein `<documentation>`-Element.
- Live-Nachweis doppelter Treffer mit Elasticsearch (D-34-02).
- Korrektur der historischen Aussage `docs/embeddings.md:497` ("jahrelang verwaist").
