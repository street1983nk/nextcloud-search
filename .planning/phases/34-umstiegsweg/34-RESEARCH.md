# Phase 34: Umstiegsweg - Research

**Researched:** 2026-10-19
**Domain:** Doku (dreisprachige Seite), PHP-Companion (Admin-Hinweis über `IAppManager`), Store-/README-Texte, Textgates
**Confidence:** HIGH für Bestand und Gates (Datei:Zeile), HIGH für die Fakten über fulltextsearch (Quelltext der Repos und App-Store-API am 19.10.2026), MEDIUM für die Abschalt-Schritte (aus Quelltext belegt, auf einer Instanz noch nicht durchgespielt)

Stand des Repos: `main` auf `e00b397b` (der im Auftrag genannte `4098e386` ist ein älterer Dependabot-Commit, #30, nicht HEAD).

<user_constraints>
## User Constraints

Für Phase 34 gibt es keine CONTEXT.md. Bindend sind ROADMAP.md Phase 34 und REQUIREMENTS.md UMST-01 bis UMST-03, wörtlich:

### Locked Decisions

- **UMST-01:** Admin findet eine Doku-Seite "Von fulltextsearch/Elasticsearch umsteigen" (dreisprachig wie die READMEs: de/en/fr) mit Schritten zum Abschalten der alten Apps, Funktionsvergleich als Faktenliste und dem Wortlaut "OCR ohne Dateiaenderung und ohne Elasticsearch" (nie "einzige OCR")
- **UMST-02:** Admin sieht auf der Findling-Admin-Seite einen Hinweis, wenn fulltextsearch (bzw. files_fulltextsearch) parallel aktiviert ist, mit Folge (doppelte Treffer in der Unified Search) und Link auf die Umstiegs-Seite; ohne die alten Apps erscheint nichts
- **UMST-03:** README und Store-Texte verlinken die Umstiegs-Seite (Kurztext-Regel, Owner-Abnahme des Textentwurfs vor Release)
- **ROADMAP Abhängigkeit:** Phasen 31, 32, 33 (Funktionsvergleich nennt nur Geliefertes)
- **ROADMAP SC1:** "die Formulierung 'einzige OCR' kommt nirgends vor (Gate)"

### Claude's Discretion

- Form der dreisprachigen Seite, Platz und Technik des Hinweises, Gate-Bau, Planaufteilung (alles unten als Empfehlung markiert)

### Deferred Ideas (OUT OF SCOPE)

- Ähnliche Dokumente (Phase 35) darf im Funktionsvergleich NICHT stehen.
- Store-Einreichung und Änderung der `info.xml`-Texte selbst: REL-05, Phase 36.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UMST-01 | Dreisprachige Umstiegs-Seite mit Abschalt-Schritten, Funktionsvergleich als Faktenliste, Pflichtformel, nie "einzige OCR" | "Bestand Doku", "Fakten über fulltextsearch", "Abschalt-Schritte", "Gate für die Formel" |
| UMST-02 | Hinweis auf der Admin-Seite bei aktivem fulltextsearch/files_fulltextsearch, mit Folge und Link; sonst nichts | "Admin-Hinweis", Muster 1 bis 3, Pitfalls 1 bis 4 |
| UMST-03 | README de/en/fr und Store-Textentwurf verlinken die Seite (Kurztext, Owner-Abnahme) | "README und Store-Entwurf", Pitfall 5 |
</phase_requirements>

## Project Constraints (aus CLAUDE.md und Owner-Regeln)

- Code Englisch; README dreisprachig (de Standard, en, fr), alle drei gepflegt; keine Em-/En-Dashes; echte Umlaute nur in deutscher Prosa, nie in Code, URLs, Ankern, Dateinamen.
- **Kurze Produkttexte (07.09.2026):** Store/README = Faktenliste, höchstens eine Zahl, Details nur als Verweis auf docs/; Textentwurf vor Release dem Owner zeigen.
- Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Abschluss fixen.
- Gedächtnis-Regeln des Owners: Commits nur als street1983nk ohne Claude-Trailer; UI-Abnahmen gemeinsam per Playwright (29.09.); nicht vermuten, mit Positivkontrolle belegen (01.10.); Produkt-Fix vor Harness-Patch; Parallelpläne nur bei genug RAM.
- Vokabelregel E-H2: der gesperrte Wortstamm (`"arch" + "iv"`, deutsche Formen) ist in deutscher Prosa unter `docs/`, in `docs/store-listing.md` und den deutschen Store-Texten verboten (`test_public_artifacts.py:272-273`, `test_store_metadata.py:196`). Für ZIP-Dateien und für Elasticsearch-Indizes also andere Wörter wählen.

## Summary

Die Phase ist überwiegend Text, aber sie berührt drei Ratschen: den Katalog-Schlüsselzähler (340, `test_admin_ui_contract.py:3655`), die PHP-Baumhash-Ratsche (`PHP_FILES_TODAY = 103`, `test_measurement_scripts.py:960-961`) und das Linkgate des Grenzblocks, das **genau einen** Doku-Link im Template verlangt (`test_admin_ui_contract.py:4576-4578`). Der Hinweis mit Link bricht dieses Gate zwingend; es muss im selben Plan verallgemeinert werden.

Dreisprachige Doku-Seiten gibt es im Repo bisher nicht. `docs/` ist einsprachig (meist Deutsch, einige Englisch); Plan 33-01 hat das ausdrücklich als Projektkonvention festgehalten: "dreisprachig sind nur die READMEs" (`33-01-PLAN.md:62`). UMST-01 verlangt erstmals eine dreisprachige Seite. Empfehlung: das README-Muster übernehmen, drei Dateien mit Sprachumschalter in Zeile 1 (`README.md:1`, `README.en.md:1`, `README.fr.md:1`).

Die Faktenlage über fulltextsearch hat sich seit der Projektgründung verschoben und muss ehrlich auf der Seite landen: Nextcloud pflegt den Stack wieder (fulltextsearch v35.0.0 am 20.09.2026, fulltextsearch_elasticsearch 34.0.3 und 35.0.1 am 07.10.2026). Es gibt inzwischen zwei Drittanbieter-Plattformen **ohne** Elasticsearch (fulltextsearch_sql, fulltextsearch_postgresql). OCR im fulltextsearch-Stack gibt es für Nextcloud 33 bis 35 nicht: files_fulltextsearch_tesseract hat im Store nur ein Release für NC 32. Daneben existieren OCR-Wege außerhalb von fulltextsearch: workflow_ocr schreibt eine neue Dateiversion, und seit 10.10.2026 sucht ocr_search Text in Bildern über einen eigenen OCR-Dienst. Damit ist "einzige OCR" faktisch falsch und die Pflichtformel "OCR ohne Dateiänderung und ohne Elasticsearch" die korrekte, abgrenzende Aussage.

**Primary recommendation:** Drei Dateien `docs/migrate-from-fulltextsearch.md` (de), `.en.md`, `.fr.md`; Hinweis als eigener, nur serverseitig gerenderter Warnbanner im Bannerblock der Admin-Seite, Bedingung `IAppManager::isEnabledForAnyone('fulltextsearch' | 'files_fulltextsearch')`, Link sprachabhängig auf die Tag-URL `blob/v1.5.0`; ein neues Gate-Modul `backend/tests/test_migration_path.py` für Pflichtformel, Verbot und Links; Wortlaut-Checkpoint mit dem Owner als erster Plan.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Erkennen, ob fulltextsearch/files_fulltextsearch aktiv ist | API/Backend (PHP-Companion, `IAppManager`) | , | App-Status ist Server-Zustand (appconfig `enabled`), nur PHP sieht ihn |
| Hinweis rendern, Link wählen (Sprache) | Frontend Server (Template `admin.php`) | Browser (kein Skript nötig) | Bestehende Banner sind serverseitig gerendert (`admin.php:322-401`) |
| Umstiegs-Seite | Statische Doku (GitHub, `docs/`) | , | Doku reist nicht im App-Tarball, Link auf Tag-URL |
| README-/Store-Verweis | Statische Texte (README, `docs/store-listing.md`) | Store (`info.xml`, erst REL-05) | Store-Text reist mit dem Release |
| Gates (Formel, Verbot, Links, Schlüsselzahl, Baumhash) | Tests (`backend/tests/*.py`, pytest) | PHPUnit (CI, `php.yml`) | Textgates leben in pytest, PHP-Logik in PHPUnit |
| Container (findling_backend) | nicht betroffen | , | Keine Python-Änderung nötig, `PACKAGE_TREE_HASH_TODAY` bleibt |

## Bestand im Repo (Frage 1)

### Doku-Seiten

| Befund | Beleg |
|---|---|
| `docs/*.md` sind einsprachig: Deutsch (z. B. `admin-page.md`, `uninstall.md`, `privacy.md`, `ocr.md`) oder Englisch (`formats.md`, `search-filters.md`, `testing.md`) | Kopfzeilen aller 26 Dateien am 19.10.2026 |
| `docs/l10n-*.md` sind KEINE Sprachvarianten von Seiten, sondern Wortlaut-Tabellen der Kataloge (Quelle der `php/l10n/*.json`) | `docs/l10n-french.md:1-5`, `docs/l10n-spanish.md:1-5` |
| Konvention "dreisprachig sind nur die READMEs", deshalb steht der ganze Änderungsweg im übersetzten Satz der Admin-Seite | `33-01-PLAN.md:62` (PE-8) |
| READMEs: Sprachumschalter in Zeile 1, relative Doku-Links (`[docs/formats.md](docs/formats.md)`) | `README.md:1`, `README.md:46`, `README.en.md:1`, `README.fr.md:1` |
| Nächstes inhaltliches Vorbild für Schrittfolgen mit `occ`: `docs/uninstall.md` ("was wann verschwindet") | `docs/uninstall.md:1-5` |

**Empfehlung (Planer-Entscheidung, Owner-Frage O1):** drei Dateien nach README-Muster:

- `docs/migrate-from-fulltextsearch.md` (Deutsch, wie `README.md` Standard)
- `docs/migrate-from-fulltextsearch.en.md`
- `docs/migrate-from-fulltextsearch.fr.md`

Zeile 1 je Datei: `Deutsch | [English](migrate-from-fulltextsearch.en.md) | [Français](migrate-from-fulltextsearch.fr.md)` (jeweils die eigene Sprache ohne Link). Dateiname ASCII und englisch wie alle anderen `docs/`-Namen. Eine einzige Datei mit drei Abschnitten wäre die Alternative, ist aber für Store- und Admin-Links schlechter (Anker statt Datei je Sprache) und bricht das README-Muster.

### Gates, die Doku und Texte heute prüfen

| Gate | Reichweite | Relevanz für Phase 34 | Beleg |
|---|---|---|---|
| `test_public_artifacts.py` | jede Datei unter `docs/` rekursiv: neun Geheimnis-Familien plus Vokabelregel (deutsche Formen des gesperrten Stamms) | neue Seiten werden automatisch geprüft; Vorsicht bei Befehlsbeispielen mit `name=wert` (Familie `schluesselwort-mit-wert`) | `test_public_artifacts.py:1-20`, `60`, `272-273` |
| `test_store_metadata.py` | beide `info.xml`, `README.en.md` als Hauptausgabe, `README.md`/`README.fr.md`, `docs/store-listing.md` | Strich/Emoji-Verbot, Messzahl genau einmal, Vokabelregel im Store-Dokument, Entwurfsabschnitte je Phase | `test_store_metadata.py:119-133`, `196`, `491`, `1190-1219`, `2104-2106` |
| CI `php.yml` | `info.xml` gegen `info.xsd` per xmllint | nur falls `<documentation>` ergänzt wird | `.github/workflows/php.yml:137-157` |
| `test_admin_ui_contract.py` | Template, Skript, Kataloge, Schlüsselzahl, Doku-Link des Grenzblocks | Schlüsselzahl 340, Linkgate "genau ein Link" | `test_admin_ui_contract.py:3655`, `4565-4590`, `4655-4666` |
| `test_measurement_scripts.py` | Baumhash der PHP-Hälfte (`**/*.php`) mit Journal | jede PHP-Änderung bewegt `PHP_TREE_HASH_TODAY`, neue Datei bewegt `PHP_FILES_TODAY` | `test_measurement_scripts.py:900-961`, `2179-2193` |
| REUSE | `path = "**"` deckt neue Dateien ab | keine Aktion | `REUSE.toml:11-15` |

Es gibt **kein** Gate, das prüft, ob ein README eine bestimmte Doku verlinkt. Das muss neu.

### Store-Textentwurf

- `docs/store-listing.md` führt je Phase einen Abschnitt `# Entwurf v1.5.0 (Teil Phase NN)` mit Kopfsatz "**Owner-Abnahme offen, Teil von REL-05; info.xml und READMEs werden erst nach der Abnahme geändert.**" (`docs/store-listing.md:2193-2219` Phase 32, `2221-2279` Phase 33). `info.xml` bleibt bis REL-05 (Phase 36) unverändert.
- Gate-Muster für einen Entwurfsabschnitt: Konstante `DRAFT_OF_PHASE_31` und Abschnittsschnitt (`test_store_metadata.py:491`, `1190-1219`).
- Die Store-Beschreibungen tragen heute genau einen Fremdlink (MCP Connector, `php/appinfo/info.xml:54`, `88`, `122`) und keinen Doku-Link; ein `<documentation>`-Element fehlt (`php/appinfo/info.xml:199-205`).
- **Abweichung für Phase 34:** UMST-03 und SC3 verlangen, dass die READMEs die Seite **in dieser Phase** verlinken. Anders als in 32/33 werden die README-Zeilen also nach der Wortlaut-Abnahme (Plan 34-01) geschrieben; nur `info.xml` bleibt Entwurf.

## Admin-Hinweis (Frage 2)

### API: welche Methode, welche App-IDs

| Frage | Befund | Beleg |
|---|---|---|
| Methode | `IAppManager::isEnabledForAnyone(string $appId): bool`, `@since 32.0.0`; prüft "enabled for everyone or for specific groups" | `nextcloud/server` `lib/public/App/IAppManager.php` (stable33), Abruf 19.10.2026 |
| Nicht nehmen | `isInstalled()` ist `@deprecated 32.0.0`; `isEnabledForUser()` fragt den Admin selbst und verfehlt eine nur für Gruppen aktivierte App | dieselbe Datei; Findling nutzt `isEnabledForUser('app_api', $user)` für einen anderen Zweck (`ExAppService.php:837`) |
| Kosten | `isEnabledForAnyone` liest `getEnabledAppsValues()`, gecacht je Request (`enabledAppsCache`), keine zusätzliche Abfrage pro Aufruf | `lib/private/App/AppManager.php:144-156`, `428-431` (stable33) |
| App-ID des Unified-Search-Anbieters | `fulltextsearch` registriert `UnifiedSearchProvider` mit Name "Full Text Search" | `nextcloud/fulltextsearch` `lib/AppInfo/Application.php:56`, `lib/Search/UnifiedSearchProvider.php:53-55` (stable34) |
| App-ID des Datei-Inhaltsanbieters | `files_fulltextsearch` (`<fulltextsearch><provider>…FilesProvider`), registriert keinen eigenen Unified-Search-Anbieter | `nextcloud/files_fulltextsearch` `appinfo/info.xml:44-45`, `lib/AppInfo/Application.php:51-59` (stable34) |
| Plattform-Apps | `fulltextsearch_elasticsearch`, Drittanbieter `fulltextsearch_sql`, `fulltextsearch_postgresql`; allein ohne `fulltextsearch` ohne Wirkung in der Suchleiste | App-Store-API `platform/34.0.3` und `35.0.0`, 19.10.2026 |
| Findlings Gruppe in der Suchleiste | "File contents" | `php/lib/Search/Provider.php:139-141` |

**Empfehlung Bedingung:** Hinweis sichtbar, wenn `isEnabledForAnyone('fulltextsearch') || isEnabledForAnyone('files_fulltextsearch')`. Genau die zwei IDs aus UMST-02. Die Folge "doppelte Treffer" entsteht über den Anbieter von `fulltextsearch`; `files_fulltextsearch` allein ist ein Rest, den der Admin ebenfalls abschalten soll, deshalb gilt der Hinweis auch dafür.

### Platz auf der Seite und Bauweise

- Alle Banner stehen im Block "Search coverage" (`admin.php:322-401`, Ausgabe `admin.php:403-421`), werden immer gerendert und über `hidden` geschaltet; das Skript schaltet sie bei jedem Poll (`admin.js:2456-2496`).
- Banner tragen nur Text (`'text' => $l->t(...)`), keinen Link. Der einzige Doku-Link der Seite ist der Grenzblock: Satz plus separates `<a href=... target="_blank" rel="noreferrer noopener">` mit dem vorhandenen Schlüssel "Steps in the documentation" (`admin.php:1036`, `1472-1473`; `php/l10n/de.json:183`).
- Die Seite wird über `Settings\Admin::getForm()` mit `AdminViewService::overview()` gefüllt; dieselbe Methode beantwortet den 5-s-Poll (`Settings/Admin.php:44-68`, `SettingsController.php:144-146`). `overview()` liefert feste Schlüssel, nie dünn besetzt (`AdminViewService.php:589-614`).

**Empfehlung (Planer-Entscheidung):**

1. Neuer Schlüssel `parallelSearch` (bool) in `overview()`, berechnet über eine neue kleine Klasse `OCA\Findling\Service\ParallelSearchService` mit Konstante `APP_IDS = ['fulltextsearch', 'files_fulltextsearch']` und Methode `active(): bool` (oder `activeApps(): list<string>`). Eigene Klasse, damit der PHPUnit-Test nur `IAppManager` stubbt und `AdminViewService` (13 Abhängigkeiten, `AdminViewService.php:573-587`) nicht für jeden Fall gebaut werden muss. Einzige weitere Konstruktionsstelle: `SettingsControllerTest.php:131`.
2. Im Template ein eigener Banner `findling-banner-parallel`, Art `warning`, **außerhalb** der `$banners`-Schleife direkt nach ihr im selben `#findling-coverage-banners`, damit der Link neben dem Satz stehen kann (Technik wie Grenzblock: Satz, dann `<a>` mit "Steps in the documentation", kein neuer Linktext-Schlüssel).
3. Nur serverseitig gerendert, das Skript fasst ihn nicht an. Ein App-Wechsel passiert auf der Apps-Seite, danach lädt der Admin diese Seite ohnehin neu. Das hält `admin.js` und dessen Vertragsgates unberührt. Wer ihn im Poll schalten will, braucht einen weiteren `shown(...)`-Aufruf und ein Skriptgate; Nutzen gering.
4. Link sprachabhängig über `IL10N::getLanguageCode()` (`@since 7.0.0`): beginnt mit `de` auf `.md`, mit `fr` auf `.fr.md`, sonst `.en.md`. Die Zuordnung in einer Konstanten-Map im Template, Tag-URL `https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch{,.en,.fr}.md`.

### l10n-Kette (Pflicht bei neuem Satz)

| Schritt | Beleg |
|---|---|
| neuer Schlüssel in allen 16 Katalogen (`de`, `de_DE` als Zwillinge identisch, `es`, `fr`, `it`, `nl`, `pt_BR`, `pt_PT`, je `.json` und `.js`) in einem Commit | `php/l10n/` (16 Dateien); Zwillingsgate `test_admin_ui_contract.py:3611-3615` |
| Schlüsselzahl 340 auf 341 (ein Satz, Linktext wiederverwendet) und neuer Absatz im Docstring ("Whoever moves it next writes the next paragraph") plus Kommentarliste | `test_admin_ui_contract.py:3604-3655` |
| fünf Sprachdokumente tragen die Zeile (`docs/l10n-french.md`, `-spanish`, `-italian`, `-dutch`, `-portuguese`) | Docstring `test_admin_ui_contract.py:3575-3577`, `3596-3598` |
| Platzhalter-Parität G3, Ausnahmen G2 (Wert gleich Englisch) | `test_every_catalogue_carries_the_same_keys`, Docstring ab `test_admin_ui_contract.py:3658` |
| Französisch nach `docs/l10n-french.md` (ASCII-Apostroph, Leerzeichen vor `:`) | `33-WORTLAUT.md:15-17` |

### Baumhash-Ratsche

- Jede Änderung unter `php/**/*.php` bewegt `PHP_TREE_HASH_TODAY` und braucht einen Journal-Absatz "Moved on ... by Plan 34-NN" (`test_measurement_scripts.py:900-961`).
- Neue Klasse `ParallelSearchService.php` plus neuer Test `ParallelSearchServiceTest.php`: `PHP_FILES_TODAY` von 103 auf 105.
- Templates zählen mit (`**/*.php`), die Kataloge nicht (`test_measurement_scripts.py:931-934`).
- Keine Python-Änderung, also bleibt `PACKAGE_TREE_HASH_TODAY` (`test_measurement_scripts.py:2010`).
- Folge für die Wellen: alle Pläne, die PHP anfassen, seriell; reine Doku-Pläne können daneben laufen.

## Fakten über fulltextsearch (Frage 3)

Alle Werte am 19.10.2026 per `gh api` und App-Store-API (`https://apps.nextcloud.com/api/v1/platform/<ver>/apps.json`) abgefragt.

### Pflegestand und Versionen

| App | GitHub (letztes Release) | Store für NC 33 | NC 34 | NC 35 |
|---|---|---|---|---|
| fulltextsearch | v35.0.0 (20.09.2026), Push 18.10.2026 | 33.0.3 (20.09.2026, `>=33 <36`) | 34.0.2 (18.09.2026) | 35.0.0-beta.1 |
| files_fulltextsearch | 35.0.0beta1 (12.08.2026), Push 19.10.2026 | 33.0.0 (19.02.2026) | 34.0.1 (06.08.2026) | 35.0.0-beta.1 |
| fulltextsearch_elasticsearch | v35.0.1 und v34.0.3 (07.10.2026) | 33.0.1 (22.09.2026) | 34.0.3 (07.10.2026) | 35.0.1 |
| files_fulltextsearch_tesseract | 24.0.0 (05/2022); `master` = 31.0.0, `max-version 32`; letzter Commit 19.01.2026 | **keine** | **keine** | **keine** (einziges Store-Release 32.0.0 vom 19.01.2026 für NC 32) |
| fulltextsearch_sql (Drittanbieter, J.-P. Litza) | , | 1.5.1 (14.10.2026, `>=31 <36`) | dto. | dto. |
| fulltextsearch_postgresql (Drittanbieter, A. Lesage) | , | 0.1.4 (10.10.2026, `>=32 <36`) | dto. | dto. |

Folgerungen für die Seite:

- **Nicht schreiben:** "verwaist", "tot", "nicht gepflegt". Der Stack wird seit 08/2026 aktiv gepflegt (Gedächtnis-Notiz 21.09.2026 "Wiederbelebung durch NC GmbH, ES-Client 9.5.0, Vue-Port" stimmt mit den Releases überein). `docs/embeddings.md:497` ("jahrelang verwaist") ist eine historische Aussage und nicht Teil dieser Phase.
- **Nicht schreiben:** "fulltextsearch braucht Elasticsearch". Richtig ist: die Plattform `fulltextsearch_elasticsearch` braucht einen Elasticsearch-Dienst mit dem Plugin ingest-attachment (Wiki `fulltextsearch` "Basic-Installation", Stand 14.06.2026); es gibt zwei Plattformen ohne Suchdienst (oben).
- **Belegbar:** Für Nextcloud 33 bis 35, also Findlings ganzes Versionsfenster, bietet der App Store keine OCR-App für fulltextsearch an.
- fulltextsearch_sql sagt selbst: "Currently can not index office document formats", PDFs nur mit Textebene; Inhalte liegen "twice" in der Datenbank (Store-Beschreibung). fulltextsearch_postgresql liest PDF und Office selbst, nennt kein OCR. Beides darf nur zitiert, nicht bewertet werden.

### Andere OCR-Wege (Grund für das Verbot "einzige OCR")

| App | Was sie tut | Datei verändert? | Beleg |
|---|---|---|---|
| workflow_ocr (R. Windey) | OCR über die Workflow-Engine mit OCRmyPDF, Store-Releases für NC 33 (1.33.2) und 35 (1.35.0) | **ja**: legt eine neue Dateiversion an; Bilder werden als zusätzliche `.pdf` gespeichert | README `R0Wi/workflow_ocr` Z. 165, 200, 224 |
| ocr_search (rurutheGeek, neu seit 10.10.2026) | Text in Bildern über Unified Search, eigener OCR-Dienst (PP-OCRv5, ONNX, CPU), `>=33 <36` | nein (laut Beschreibung), aber Bilder werden an den konfigurierten Dienst geschickt | Store-Beschreibung, `github.com/rurutheGeek/nextcloud-ocr-search` |

Damit ist die Formel "OCR ohne Dateiänderung und ohne Elasticsearch" wahr und abgrenzend, ohne Einzigartigkeit zu behaupten. Empfehlung: Fremd-Apps außerhalb des fulltextsearch-Stacks auf der Seite **nicht** nennen (kein Vergleich, keine Herabwürdigung); das Verbot schützt die Ehrlichkeit über das Gate.

### Was ein Umsteiger verliert (ehrlich zu nennen)

- **Deck-Karten:** Deck registriert einen Inhaltsanbieter für fulltextsearch (`nextcloud/deck` `appinfo/info.xml:80-82`, `lib/Provider/DeckProvider.php`). Findling indexiert nur Dateien. Nach dem Abschalten sind Deck-Karten nicht mehr volltextindexiert (Decks eigene Suche bleibt).
- **Externe Speicher:** bei Findling standardmäßig aus, Team Folders an (`SettingsService.php:400-414`); Schalter auf der Admin-Seite.
- **Voraussetzungen:** Findling braucht AppAPI mit HaRP (Docker) und Nextcloud 33 bis 35 (`README.md` "Anforderungen").

### Funktionsvergleich: nur Geliefertes (Phasen bis 33)

Erlaubte Findling-Zeilen (alle in `main`, Quelle README und `docs/`): Volltextsuche mit deutscher Wortbehandlung; Texterkennung für gescannte PDFs und Bilder in zehn Sprachen, Dateien werden nicht verändert (`README.md:100`); semantische Suche; Dateitypen inklusive EML, ZIP-Inhalt, DOC, XLS, HEIC (Phase 31, `docs/formats.md`); Filter nach Dateityp und Ordner in der Unified Search (Phase 32, `docs/search-filters.md`); Ausschluss von Ordnern und Mustern (Phase 33, `docs/admin-page.md`); Rechteprüfung jedes Treffers; erster Indexlauf startet von selbst; Leistungsprofile. **Verboten:** "Ähnliche Dokumente" (Phase 35), jede Zahl außer höchstens einer (Kurztext-Regel gilt für README/Store, für die Doku-Seite empfohlen).

Empfehlung zur Form: keine Tabelle "besser/schlechter", sondern zwei Faktenlisten "Was Findling mitbringt" und "Was sich beim Umstieg ändert" (Deck, externe Speicher, Voraussetzungen, eine Gruppe "File contents" statt "Full Text Search"). Jede fulltextsearch-Aussage mit Link auf die Quelle.

## Abschalt-Schritte (Frage 3, Fortsetzung)

Aus dem Quelltext belegt; auf einer Instanz noch nicht durchgespielt (Plan-Aufgabe, siehe "Nachweisweg").

| # | Schritt | Beleg | Anmerkung |
|---|---|---|---|
| 1 | Findling installieren, ersten Indexlauf abwarten (Deckungsgrad auf der Verwaltungsseite). Solange beide laufen, erscheint der neue Hinweis. | README "Installation" | Reihenfolge: erst Findling fertig, dann alt abschalten, damit die Suche nie leer ist |
| 2 | Laufende Indexierung stoppen: `occ fulltextsearch:stop`; einen Dienst mit `occ fulltextsearch:live` (systemd-Unit aus dem Wiki) stoppen und deaktivieren | Wiki `Commands.md` (stop, live), `Basic-Installation.md` (Unit mit `Restart=always`); `lib/Command/Stop.php:31` | Ohne Deaktivieren startet `Restart=always` den Befehl nach dem Abschalten der App immer wieder |
| 3 | Index löschen, **solange Apps und Suchdienst noch laufen**: `occ fulltextsearch:reset` | `lib/Command/Reset.php` (stable33/34: `ConfirmationQuestion` plus getippte Bestätigung); `IndexService::resetIndex()` ruft `platform->resetIndex('all')` und leert die lokale Indextabelle; Elasticsearch-Plattform löscht Ingest-Pipeline und Index (`fulltextsearch_elasticsearch` `lib/Service/IndexService.php:114-128`) | interaktiv, nicht skriptbar ohne Eingabe; funktioniert auch für die SQL-/PostgreSQL-Plattform (gleiche Schnittstelle) |
| 4 | Apps abschalten: `occ app:disable files_fulltextsearch fulltextsearch_elasticsearch fulltextsearch` (mehrere IDs in einem Aufruf erlaubt); ggf. auch `files_fulltextsearch_tesseract` | `core/Command/App/Disable.php:30-32` (`IS_ARRAY`, stable33) | statt `fulltextsearch_elasticsearch` die verwendete Plattform-App |
| 5 | Optional entfernen: `occ app:remove <id>` führt Deinstallationsschritte aus, falls vorhanden | `core/Command/App/Remove.php:36-40` (stable34) | fulltextsearch deklariert keine `repair-steps/uninstall` (`appinfo/info.xml` stable34); die Tabellen `fulltextsearch_index` und `fulltextsearch_ticks` (Migrationen `Version2000Date20201208130255`, `Version2400Date202201301329`) bleiben daher vermutlich liegen [zu belegen auf 8090] |
| 6 | Elasticsearch-Dienst außerhalb von Nextcloud stoppen und seine Daten entfernen | Wiki `Basic-Installation.md` | nur der Admin weiß, ob der Dienst noch anderes bedient |
| 7 | **Nextcloud AIO:** die Option "Fulltextsearch" in der AIO-Oberfläche abwählen; ein `occ app:disable` allein wird beim nächsten Containerstart zurückgedreht | `nextcloud/all-in-one` `Containers/nextcloud/entrypoint.sh:1049-1086` (aktiviert/aktualisiert die drei Apps bei `FULLTEXTSEARCH_ENABLED=yes`), `1103-1115` (entfernt sie nur bei `REMOVE_DISABLED_APPS=yes`) | wichtigster Stolperstein für AIO-Nutzer |

Nach Schritt 4 verschwindet der Findling-Hinweis beim nächsten Laden der Seite (Positivkontrolle im Nachweis).

## Wortlaut-Zwänge und Gate (Frage 4)

### Pflichtformel

- de, wörtlich: **"OCR ohne Dateiänderung und ohne Elasticsearch"** (in Prosa mit Umlaut; REQUIREMENTS schreibt ASCII, weil Planungsdateien ASCII sind).
- en/fr: Vorschlag, Owner-Frage O2: "OCR without changing files and without Elasticsearch" / "OCR sans modifier les fichiers et sans Elasticsearch".

### Verbot "einzige OCR"

Bestand: Der einzige heutige Treffer eines naiven Substrings ist eine legitime Formulierung: `docs/performance.md:1025` "keine einzige OCR-Seite". Ein `"einzige OCR" in text`-Gate wäre sofort rot.

**Empfehlung Gate** (neues Modul `backend/tests/test_migration_path.py`, Form wie die anderen Textgates: Befundliste mit Datei und Sprache, Mindestzahl gegen Leerlauf, Selbsttests mit sauberem und mutiertem Muster, verbotene Wörter aus Hälften zusammengesetzt wie `test_store_metadata.py:186-196`):

- Muster, Groß/Klein egal: `\beinzig\w*\s+OCR(?![-\w])`, `\bonly\s+OCR(?![-\w])`, `\bseule?s?\s+OCR(?![-\w])` (en/fr-Entsprechung nach Owner-Antwort O3).
- Reichweite: `docs/**` (ohne `docs/measurements/**` Rohdaten), `README*.md`, `CHANGELOG.md`, beide `info.xml`, `php/templates/**`, `php/l10n/**`, `store/**`. Ausdrücklich nicht `.planning/` (dort steht das Verbot selbst) und nicht `backend/tests/` (Gate selbst).
- Positivkontrolle: Selbsttest, dass `docs/performance.md:1025` gelesen wird und **kein** Befund ist; mutierter Satz "Findling ist die einzige OCR" ist genau ein Befund.
- Gleiches Modul prüft: drei Seiten existieren; Pflichtformel steht in jeder Sprache genau wie abgenommen; Sprachumschalter in Zeile 1; jede README verlinkt die Seite ihrer Sprache relativ; der Phase-34-Entwurf in `docs/store-listing.md` existiert und trägt die Tag-Links; keine U+2013/U+2014.

### Kurztext-Regel

README/Store: eine Zeile, Faktenform, keine Zahl (die Beschreibungen tragen schon genau eine Messzahl, `test_store_metadata.py:1319`). Vorschlag für den Wortlaut-Checkpoint: eine Zeile in "Was Findling kann" bzw. ein Satz unter der Funktionsliste, z. B. de "Umstieg von fulltextsearch/Elasticsearch: Schritte in der Dokumentation" mit Link. Der Satz darf den gesperrten Stamm nicht enthalten.

## README und Store-Entwurf (UMST-03)

| Ort | Linkform | Begründung |
|---|---|---|
| `README.md`, `README.en.md`, `README.fr.md` | relativ, Seite der eigenen Sprache (`docs/migrate-from-fulltextsearch.md` usw.) | Bestandsmuster `README.md:46`; lebt mit `main` |
| Store-Entwurf (sechs Beschreibungen, Abschnitt `# Entwurf v1.5.0 (Teil Phase 34)` in `docs/store-listing.md`) | absolut, Tag-URL `blob/v1.5.0/docs/...` je Sprache | Store-Text reist mit dem Release und ist danach nicht editierbar; gleiche Logik wie PE-8 |
| Admin-Seite | absolut, Tag-URL je Sprache | PE-8 (`33-01-PLAN.md:62`), `admin.php:1036` |
| optional `info.xml` `<documentation><admin>` | eine URL, nicht sprachfähig | `info.xsd` `complexType documentation` (user/admin/developer, je max. 1), Reihenfolge nach `types`, vor `category`; Owner-Frage O6, sonst weglassen |

Bedingung wie in 33-VERIFICATION (`33-VERIFICATION.md:102`): Tag-Links lösen erst mit dem Tag v1.5.0 auf; vor der Einreichung in Phase 36 prüfen. Das Linkgate prüft bis dahin, dass die Zieldatei im Repo existiert.

## Owner-Checkpoints (Frage 5)

| Wo | Art | Inhalt |
|---|---|---|
| 34-01, früh | `checkpoint:decision` (blocking), Ergebnis `34-WORTLAUT.md` wie `33-WORTLAUT.md` | Dateinamen und Form (O1), Pflichtformel en/fr (O2), Verbotsreichweite (O3), Hinweissatz de/en/fr mit Folge, README-Zeile de/en/fr, Store-Zeile de/en/fr, Funktionsvergleich-Zeilen und "Was sich ändert" (O4, O5), Linkform (O6) |
| 34-0x Seite | Owner liest die drei Seiten | gehört in die gemeinsame Abnahme, kein eigener Checkpoint nötig, wenn 34-01 die Zeilen festlegt |
| Gemeinsame Playwright-Runde auf 8090 | `checkpoint:human-verify` | Hinweis mit fulltextsearch aktiv in de/en/fr sichtbar und Link korrekt; nach `app:disable` weg; ohne die Apps nie da; Seiten und README-Links auf GitHub `main` lesen |
| Store-Entwurf | REL-05-artig, bleibt "Owner-Abnahme offen" in `docs/store-listing.md` | Abnahme gemeinsam mit Phase 36, außer der Owner nimmt in 34-01 schon ab |

## Architecture Patterns

### Datenfluss des Hinweises

```
Admin öffnet Verwaltung > Findling
        |
        v
Settings\Admin::getForm()  --> AdminViewService::overview()
                                   |
                                   +--> ParallelSearchService::active()
                                   |        |
                                   |        +--> IAppManager::isEnabledForAnyone('fulltextsearch')
                                   |        +--> IAppManager::isEnabledForAnyone('files_fulltextsearch')
                                   |               (appconfig "enabled", je Request gecacht)
                                   v
                     ['parallelSearch' => bool, ...]  (auch im 5-s-Poll, Skript ignoriert den Schlüssel)
        |
        v
templates/admin.php
   IL10N::getLanguageCode() -> de | fr | sonst en -> Tag-URL der Seite
   <p id="findling-banner-parallel" class="findling-banner findling-banner--warning" [hidden wenn false]>
       Satz (Katalog) + <a href=Tag-URL target=_blank rel="noreferrer noopener">Steps in the documentation</a>
        |
        v
GitHub blob/v1.5.0/docs/migrate-from-fulltextsearch{,.en,.fr}.md
```

### Muster 1: Kleine Prüfklasse mit Konstante

`ParallelSearchService` kennt nur `IAppManager`, eine Konstante mit zwei IDs und eine Methode. Kein Logging der App-Liste nötig (Admin-Seite, keine Geheimnisse), keine Konfiguration.

### Muster 2: Banner mit Link außerhalb der Schleife

Wie der Grenzblock: übersetzter Satz ohne URL, Link als eigenes Element mit vorhandenem Schlüssel. Die URL steht nie im Katalog (keine Umlaute in URL, kein Übersetzer kann sie verbiegen).

### Muster 3: Fester Schlüssel statt dünner Antwort

`parallelSearch` immer vorhanden (bool), in den PHPStan-Shape von `overview()` aufnehmen (`AdminViewService.php:597-612`).

### Anti-Patterns

- Hinweis per `isEnabledForUser()` des Admins: verfehlt Gruppenfreigaben.
- Link-URL im übersetzten Satz: Katalog und Gate würden URL und Sprache vermischen.
- Hinweis im Container (Python) berechnen: der Container weiß nichts über PHP-Apps.
- Seite als drei Abschnitte einer Datei mit Umlaut-Ankern.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| App-Status lesen | eigene appconfig-Abfrage `config:app:get fulltextsearch enabled` | `IAppManager::isEnabledForAnyone()` | kennt Gruppenwerte und "always enabled", gecacht |
| Sprache des Admins | Header oder Nutzereinstellung selbst lesen | `IL10N::getLanguageCode()` | gleiche Quelle wie die Kataloge |
| Verbotsgate | neues Framework | Form der bestehenden Textgates (`test_store_metadata.py`, `test_public_artifacts.py`) | Selbsttests, Mindestzahl, Hälften-Trick schon erprobt |
| Abschalt-Befehle | eigene Löschskripte für Elasticsearch | `occ fulltextsearch:reset` | entfernt Index, Pipeline und lokale Tabelle über die offizielle Schnittstelle |

## Runtime State Inventory

Keine Umbenennung, aber die Phase beschreibt fremden Laufzeit-Zustand, den der Admin räumen muss; für die Seite:

| Category | Items Found | Action Required |
|---|---|---|
| Stored data | Elasticsearch-Index und Ingest-Pipeline; Tabellen `oc_fulltextsearch_index`, `oc_fulltextsearch_ticks` | Schritt 3 (reset) vor Schritt 4; Tabellen-Verbleib auf 8090 belegen und dokumentieren |
| Live service config | AIO-Option "Fulltextsearch" (`FULLTEXTSEARCH_ENABLED`) | in der AIO-Oberfläche abwählen (Schritt 7) |
| OS-registered state | systemd-Unit für `occ fulltextsearch:live` (Wiki-Vorlage mit `Restart=always`) | stoppen und deaktivieren (Schritt 2) |
| Secrets/env vars | AIO: `FULLTEXTSEARCH_PASSWORD` u. a. | keine Aktion durch Findling; Hinweis optional |
| Build artifacts | App-Code unter `custom_apps/` | `occ app:remove` optional (Schritt 5) |

Für Findling selbst: nichts. Kein Schema, keine Marke, kein appconfig-Schlüssel neu.

## Common Pitfalls

### Pitfall 1: Linkgate "genau ein Doku-Link" wird rot
**What goes wrong:** `scan_limits_link()` zählt alle `blob/`-URLs im Template und verlangt genau eine; außerdem verlangt `_TAG_LINK` ein `#anchor` (`test_admin_ui_contract.py:4568-4590`).
**How to avoid:** im selben Plan das Gate verallgemeinern: erwartete Linkmenge = Grenzblock-Link plus drei Seiten-Links; Anker optional; je Link prüfen, dass die Zieldatei unter `docs/` existiert und der Tag `v1.5.0` ist. Selbsttest `test_a_link_with_another_anchor_or_without_a_tag_is_one_finding` mitziehen. `test_phase33_audit.py:2231` zählt nur `limits-per-file` und bleibt grün.
**Warning signs:** "the template carries 4 links into the documentation instead of one".

### Pitfall 2: Falscher Treffer des Verbotsgates
**What goes wrong:** "keine einzige OCR-Seite" (`docs/performance.md:1025`) wird als Verbot gemeldet.
**How to avoid:** Lookahead `(?![-\w])` und Positivkontrolle im Selbsttest.

### Pitfall 3: Schlüsselzahl und fünf Sprachdokumente
**What goes wrong:** Katalog um einen Schlüssel gewachsen, 340 nicht bewegt oder Docstring-Absatz fehlt; Zeile in den fünf `docs/l10n-*.md` fehlt.
**How to avoid:** 16 Kataloge, Zahl, Docstring, Kommentarliste und fünf Tabellen in einem Commit; vorhandenen Linktext "Steps in the documentation" wiederverwenden (dann +1 statt +2).

### Pitfall 4: Baumhash-Ratsche bei parallelen PHP-Plänen
**What goes wrong:** zwei Pläne ändern PHP gleichzeitig, beide schreiben `PHP_TREE_HASH_TODAY`.
**How to avoid:** alle PHP-Änderungen in einen Plan; Doku/README-Pläne parallel dazu erlaubt.

### Pitfall 5: Store-Link auf `blob/main` oder relativ
**What goes wrong:** ein relativer Link funktioniert im Store nicht; `blob/main` zeigt nach dem nächsten Release auf eine andere Fassung.
**How to avoid:** Tag-URL wie PE-8; Prüfung vor Einreichung (Phase 36).

### Pitfall 6: Unehrliche Aussagen über fulltextsearch
**What goes wrong:** "verwaist", "braucht Elasticsearch", "keine OCR möglich" sind heute falsch oder ungenau.
**How to avoid:** nur Aussagen aus der Tabelle "Pflegestand" mit Datum und Link; "Stand 19.10.2026" auf der Seite; Owner liest im Wortlaut-Checkpoint.

### Pitfall 7: AIO dreht das Abschalten zurück
**What goes wrong:** Admin führt `occ app:disable` aus, AIO aktiviert die Apps beim nächsten Start wieder, der Findling-Hinweis kommt zurück.
**How to avoid:** Schritt 7 auf der Seite; der Hinweis selbst ist dann ehrlich.

### Pitfall 8: Gesperrter Wortstamm in deutscher Prosa
**What goes wrong:** Formulierungen rund um ZIP-Inhalte oder "Index sichern" greifen zum gesperrten Wort; `test_public_artifacts.py` wird rot.
**How to avoid:** Wortlaut-Entwurf vor dem Commit durch das Vokabelgate laufen lassen (wie `33-WORTLAUT.md:18-19`).

## Code Examples

Skizzen für den Planer, nicht ausgeführt.

```php
<?php
declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\App\IAppManager;

/**
 * Whether the full text search framework runs next to this app (UMST-02).
 */
final class ParallelSearchService {
	/** The two apps of UMST-02; fulltextsearch registers the unified search provider. */
	public const APP_IDS = ['fulltextsearch', 'files_fulltextsearch'];

	public function __construct(
		private IAppManager $appManager,
	) {
	}

	public function active(): bool {
		foreach (self::APP_IDS as $appId) {
			if ($this->appManager->isEnabledForAnyone($appId)) {
				return true;
			}
		}
		return false;
	}
}
```

```php
// templates/admin.php, near the banners. The tag is spelled once (REL-05 moves it).
$migrationDocsBase = 'https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch';
$languageCode = $l->getLanguageCode();
$migrationDocsUrl = $migrationDocsBase . (str_starts_with($languageCode, 'de') ? '.md' : (str_starts_with($languageCode, 'fr') ? '.fr.md' : '.en.md'));
```

PHPUnit, Kern der drei Fälle (keine App, nur fulltextsearch, nur files_fulltextsearch):

```php
$apps = $this->createMock(IAppManager::class);
$apps->method('isEnabledForAnyone')->willReturnCallback(static fn (string $id): bool => $id === 'files_fulltextsearch');
self::assertTrue((new ParallelSearchService($apps))->active());
```

Gate-Kern (pytest):

```python
FORBIDDEN = re.compile(r"\beinzig\w*\s+" + "O" + r"CR(?![-\w])", re.IGNORECASE)
assert FORBIDDEN.search("bis hierher lief keine einzige OCR-Seite") is None   # positive control
assert FORBIDDEN.search("Findling ist die einzige OCR") is not None
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| fulltextsearch "jahrelang verwaist" (Projektstart 08/2026) | Releases 34.x/35.x durch Nextcloud GmbH | 12.08.2026 bis 07.10.2026 | Seite darf den Pflegestand nicht abwerten |
| fulltextsearch nur mit Elasticsearch | zusätzlich fulltextsearch_sql, fulltextsearch_postgresql (Drittanbieter) | 2025-07 bzw. 2026-09 | Titel nennt "fulltextsearch/Elasticsearch", Schritte gelten für jede Plattform |
| OCR im Stack über files_fulltextsearch_tesseract | kein Store-Release für NC 33 bis 35 | letztes Release 19.01.2026 (NC 32) | Kernaussage der Formel |
| `IAppManager::isInstalled()` | `isEnabledForAnyone()` | NC 32 | Findling (min. NC 33) nutzt die neue Methode |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | Tabellen `oc_fulltextsearch_index`/`_ticks` bleiben nach `app:disable` und `app:remove` liegen | Abschalt-Schritte 5 | Seite sagt Falsches über Reste; auf 8090 belegen |
| A2 | `occ fulltextsearch:reset` läuft ohne konfigurierte Plattform mit verständlichem Fehler statt Absturz | Abschalt-Schritte 3 | Schrittfolge für Instanzen mit totem Suchdienst braucht Alternative |
| A3 | Auf 8090 (NC 34.0.3) lassen sich fulltextsearch 34.0.2 und files_fulltextsearch 34.0.1 aus dem Store installieren und aktivieren, ohne Elasticsearch | Nachweisweg | sonst Hinweis per `occ config:app:set fulltextsearch enabled yes` simulieren (weniger echt) |
| A4 | Doppelte Treffer erscheinen tatsächlich in der Suchleiste, wenn beide mit funktionierender Plattform laufen | Hinweistext | ohne Elasticsearch-Lauf nur aus Quelltext belegt; Satz vorsichtig formulieren ("können doppelt erscheinen") |
| A5 | ocr_search verändert keine Dateien | Andere OCR-Wege | nur Store-Beschreibung; wird auf der Seite nicht genannt, daher geringes Risiko |

## Open Questions (Owner-Fragen für den Wortlaut-Checkpoint 34-01) (RESOLVED in 34-01, 19.10.2026)

1. **O1 Form der Seite:** drei Dateien `docs/migrate-from-fulltextsearch{,.en,.fr}.md` mit Sprachumschalter (Empfehlung) oder eine Datei? Beantwortet durch D-34-01 (34-CONTEXT.md), vermerkt in 34-WORTLAUT.md Abschnitt E.
2. **O2 Pflichtformel en/fr:** "OCR without changing files and without Elasticsearch" / "OCR sans modifier les fichiers et sans Elasticsearch"? Beantwortet: 34-WORTLAUT.md, Abschnitt "Owner-Abnahme" (19.10.2026).
3. **O3 Verbotsreichweite:** nur "einzige OCR" oder auch "only OCR" und "seule OCR"; Dateireichweite wie oben? Beantwortet: 34-WORTLAUT.md, Abschnitt "Owner-Abnahme" (19.10.2026).
4. **O4 Funktionsvergleich:** zwei Faktenlisten ("Was Findling mitbringt", "Was sich ändert") statt Gegenüberstellung; Deck-Verlust und externe Speicher nennen? Beantwortet: 34-WORTLAUT.md, Abschnitt "Owner-Abnahme" (19.10.2026).
5. **O5 Drittanbieter:** fulltextsearch_sql/postgresql auf der Seite erwähnen (für deren Nutzer gilt Schritt 6 nicht) oder nur "die verwendete Plattform-App"? Beantwortet: 34-WORTLAUT.md, Abschnitt "Owner-Abnahme" (19.10.2026).
6. **O6 Links:** Admin-Hinweis sprachabhängig auf Tag-URL `v1.5.0` (Empfehlung) oder fest auf Englisch; `<documentation><admin>` in `info.xml` ergänzen (eine URL, nur bei REL-05)? Beantwortet: 34-WORTLAUT.md, Abschnitt "Owner-Abnahme" (19.10.2026).
7. **O7 Hinweistext:** Vorschlag en "Full text search (fulltextsearch) is switched on next to Findling. Both search the same files, so results can appear twice in the search bar. Switch off the old apps once Findling has finished its first index run."; de/fr entsprechend. Beantwortet: 34-WORTLAUT.md, Abschnitt "Owner-Abnahme" (19.10.2026).
8. **O8 Nachweis mit Elasticsearch:** Doppeltreffer live mit einem Elasticsearch-Container zeigen (RAM ~1 bis 2 GB, Owner-Regel "parallel nur mit Speicher") oder nur Quelltext-Beleg plus Hinweis an/aus? Beantwortet durch D-34-02 (34-CONTEXT.md), vermerkt in 34-WORTLAUT.md Abschnitt E.
9. **O9 README-Platz:** Zeile in "Was Findling kann" oder eigener kurzer Abschnitt "Umstieg" vor "Installation"? Beantwortet: 34-WORTLAUT.md, Abschnitt "Owner-Abnahme" (19.10.2026).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| Dev-Nextcloud `findling-nextcloud` (8090) | Hinweis-Nachweis, Abschalt-Schritte | ja, `status.php` 200 | 34.0.3, Apps aktiv: app_api, findling | , |
| HaRP-Instanz, `nc_app_findling_backend` | nicht nötig | läuft | , | , |
| App Store aus dem Container | Installation fulltextsearch 34.0.2 | nicht geprüft | , | `occ config:app:set fulltextsearch enabled yes` (A3) |
| Docker | `php -l`, Instanz | ja | läuft | , |
| Node | Playwright-Abnahme | ja | v22.21.0 | , |
| uv | pytest-Gates | ja | 0.11.7 | , |
| PHPUnit | `ParallelSearchServiceTest` | nur CI (`php.yml`, stable34-Server) | ^11.5 | , |
| Elasticsearch | nur O8 | nicht vorhanden | , | Quelltext-Beleg |

## Gates dieser Phase

| Gate | Relevant | Warum |
|---|---|---|
| `test_migration_path.py` (neu) | ja | Formel, Verbot, Links, Seiten, README-Verweise, Entwurfsabschnitt |
| `test_admin_ui_contract.py` | ja | Schlüsselzahl, Kataloge, Linkgate (Pitfall 1), Banner |
| `test_measurement_scripts.py -k tree_hash` | ja | PHP-Baumhash 103 auf 105 |
| `test_public_artifacts.py` | ja | neue Seiten unter `docs/` |
| `test_store_metadata.py` | ja | README- und Store-Dokument-Regeln, Strich/Emoji, Vokabel |
| `test_unified_search_plugin.py` (Katalogschlüssel) | prüfen | hält Skriptschlüssel gegen Kataloge |
| `php -l` per `php:8.3-cli` | ja | Template, Service |
| PHPUnit | CI | `ParallelSearchServiceTest`, `SettingsControllerTest` |
| ruff/pyright/vulture | ja | neues pytest-Modul |
| `reuse lint` | ja | neue Dateien (durch `**` gedeckt) |

## Nachweisweg auf 8090 (Vorschlag)

1. Vorher: `occ app:list` ohne fulltextsearch; Admin-Seite in de zeigt **keinen** `findling-banner-parallel` (Negativkontrolle, DOM `hidden`).
2. `occ app:install fulltextsearch` und `occ app:install files_fulltextsearch` (A3); Seite neu laden: Banner sichtbar in de, en, fr (`occ user:setting admin core lang`), Link zeigt auf die Seite der jeweiligen Sprache.
3. Nur `occ app:disable fulltextsearch`: Banner bleibt (files_fulltextsearch aktiv).
4. `occ app:disable files_fulltextsearch`: Banner weg.
5. Reste belegen: `SHOW TABLES LIKE 'oc_fulltextsearch%'` vor und nach `app:remove` (A1), Ergebnis in die Seite.
6. `occ fulltextsearch:reset` ohne Plattform einmal ausführen und Ausgabe festhalten (A2).
7. Aufräumen: beide Apps `app:remove`, Ausgangszustand wie Schritt 1.

## Security Domain

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2 Authentication | nein | , |
| V3 Session Management | nein | , |
| V4 Access Control | ja | Hinweis nur auf der Admin-Einstellungsseite (`ISettings`), keine neue Route |
| V5 Input Validation | nein | keine Eingabe; App-IDs sind Konstanten |
| V6 Cryptography | nein | , |

| Pattern | STRIDE | Mitigation |
|---|---|---|
| Reverse Tabnabbing über externen Link | Tampering | `target="_blank" rel="noreferrer noopener"` wie `admin.php:1473` |
| URL über Katalog manipulierbar | Tampering | URL nur im Template, nie im übersetzten Satz; Ausgabe über `p()` |
| Informationsleck über App-Liste | Information Disclosure | nur ein Bool, nur für Admins, keine Logzeile |
| Seitenlast durch Poll | DoS | `isEnabledForAnyone` gecacht je Request; zwei Array-Lookups je Poll |

## Empfohlene Planaufteilung (6 Pläne)

| Plan | Inhalt | Welle |
|---|---|---|
| 34-01 | Wortlaut-Entwurf `34-WORTLAUT.md` (Seitengerüst de/en/fr mit Formel, Funktionslisten, Schritten; Hinweissatz; README- und Store-Zeile; Linkform) plus `checkpoint:decision` O1 bis O9 | 1 |
| 34-02 | Drei Seiten unter `docs/`, neues Gate `test_migration_path.py` (Formel, Verbot mit Positivkontrolle, Umschalter, keine Striche), Abschalt-Schritte auf 8090 durchspielen (A1, A2, A3) und Befunde in die Seiten | 2 |
| 34-03 | Admin-Hinweis: `ParallelSearchService` plus PHPUnit, `overview()`-Schlüssel, Template-Banner mit Sprach-Link, 16 Kataloge, fünf Sprachdokumente, Schlüsselzahl 341, Linkgate verallgemeinert, Baumhash-Journal (105 Dateien), `docs/admin-page.md` Abschnitt | 2 (parallel zu 34-02, nur 34-03 fasst PHP an) |
| 34-04 | README de/en/fr Verweis, `# Entwurf v1.5.0 (Teil Phase 34)` in `docs/store-listing.md` (Owner-Abnahme offen), CHANGELOG, Gate-Erweiterung README-Links und Entwurfsabschnitt | 3 |
| 34-05 | Gemeinsame Playwright-Abnahme auf 8090 mit dem Owner (`checkpoint:human-verify`), Protokoll `34-05-ABNAHME.md` | 4 |
| 34-06 | Security-, Bug- und Performance-Audit (`34-AUDIT.md`), Befunde fixen | 5 |

Variante kompakt (5 Pläne): 34-04 in 34-02 aufgehen lassen, wenn der Owner in 34-01 die README-Zeile schon abnimmt. UI-SPEC: nach dem Präzedenzfall D-33-02 vermutlich entbehrlich (ein Banner, kein neues Bedienelement); Owner-Entscheid im 34-01-Checkpoint mitfragen.

## Package Legitimacy Audit

Keine neuen Pakete (PHP nutzt OCP, Tests nutzen vorhandenes pytest/PHPUnit). slopcheck nicht nötig.

## Sources

### Primary (HIGH confidence)
- Codebasis `C:\Users\Student\nextcloud-search`, Stand `e00b397b`, alle Datei:Zeile-Angaben oben
- `nextcloud/server` stable33/34: `lib/public/App/IAppManager.php`, `lib/private/App/AppManager.php`, `lib/public/IL10N.php`, `core/Command/App/Disable.php`, `core/Command/App/Remove.php` (gh api, 19.10.2026)
- `nextcloud/fulltextsearch` stable33/34/master: `appinfo/info.xml`, `lib/AppInfo/Application.php`, `lib/Search/UnifiedSearchProvider.php`, `lib/Command/Reset.php`, `lib/Command/Stop.php`, `lib/Service/IndexService.php`, `lib/Migration/*`, `lib/Cron/Index.php` (19.10.2026)
- `nextcloud/fulltextsearch_elasticsearch` `lib/Platform/ElasticSearchPlatform.php`, `lib/Service/IndexService.php` (19.10.2026)
- `nextcloud/files_fulltextsearch` stable34 `appinfo/info.xml`, `lib/AppInfo/Application.php`; `nextcloud/files_fulltextsearch_tesseract` Commits und `appinfo/info.xml` (19.10.2026)
- `nextcloud/deck` `appinfo/info.xml:80-82` (19.10.2026)
- `nextcloud/all-in-one` `Containers/nextcloud/entrypoint.sh:1049-1115` (19.10.2026)
- App-Store-API `https://apps.nextcloud.com/api/v1/platform/{32.0.0,33.0.0,34.0.3,35.0.0}/apps.json` (19.10.2026)
- `nextcloud/appstore` `nextcloudappstore/api/v1/release/info.xsd`, `complexType documentation` (19.10.2026)
- Wiki `nextcloud/fulltextsearch.wiki` `Basic-Installation.md`, `Commands.md` (Stand 14.06.2026)

### Secondary (MEDIUM confidence)
- README `R0Wi/workflow_ocr` (Dateiversion, `.pdf` für Bilder), 19.10.2026
- Store-Beschreibungen von ocr_search, fulltextsearch_sql, fulltextsearch_postgresql (Selbstauskunft der Autoren)

### Tertiary (LOW confidence)
- Gedächtnis-Notiz Kill-Kriterium 21.09.2026 (durch Releases oben bestätigt)

## Metadata

**Confidence breakdown:**
- Bestand und Gates: HIGH, an Datei:Zeile belegt
- Fakten über fulltextsearch: HIGH, aus Quelltext und Store-API vom selben Tag
- Abschalt-Schritte: MEDIUM, Quelltext-belegt, Instanzlauf steht aus (A1 bis A3)
- Hinweis-Bauweise: HIGH, nutzt vorhandene Banner- und Linktechnik

**Research date:** 2026-10-19
**Valid until:** 2026-11-02 (fulltextsearch-Stack bewegt sich gerade schnell; Store-Stand vor dem Schreiben der Seite in 34-02 erneut abfragen)
