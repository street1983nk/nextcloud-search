# Phase 20: UI-Kataloge es/it/nl/pt - Research

**Recherchiert:** 2026-09-24
**Domäne:** Nextcloud-App-Übersetzungskataloge (`l10n/*.json` und `l10n/*.js`), Sprachcode-Auflösung, Pluralregeln, parametrisierte Katalog-Gates
**Konfidenz:** HIGH für alle Ladepfad-, Plural- und Gate-Befunde (an der laufenden Test-Nextcloud 34.0.3 und am eigenen Baum gemessen), MEDIUM für die Prozessfragen, die ein Owner-Entscheid sind

---

## Zusammenfassung

Der Ladepfad ist **vor** der Übersetzungsarbeit geklärt, und zwar nicht aus dem Quellbaum
gelesen, sondern an der laufenden Test-Nextcloud gefahren: `getL10nFilesForApp()` baut den
Dateinamen aus dem Sprachcode **ohne jede Kürzung**. Eine Probe mit einer echten
`php/l10n/pt.json` (die Test-Nextcloud mountet `php/` direkt als
`custom_apps/findling`) liefert für einen Nutzer auf `pt_PT` und `pt_BR` `code=en`. Der
Kern kennt kein `pt`, also kann auch niemand auf `pt` stehen. Ergebnis: **zehn Dateien,
alle unter `php/l10n/`**, `es`, `it`, `nl`, `pt_PT`, `pt_BR` je `.json` und `.js`. Die
ExApp braucht keine: sie hat kein Verzeichnis in der Nextcloud, ihre einzigen
übersetzten Texte sind Store-Metadaten in `backend/appinfo/info.xml`, und jeder Satz, den
der Container über sich selbst sagen lässt, reist als Code und wird auf der PHP-Seite in
Worte gefasst.

**Die Schlüsselzahl ist heute 202**, gezählt am 2026-09-24 aus `php/l10n/de.json`, nicht
199 und erst recht nicht 174. Plan 18-10 hat sie am selben Tag von 199 auf 202 gehoben.
Beim Planstart erneut zählen, weil Phase 19 zwar keine Katalogdatei anfasst, aber der
Absatzzwang im Docstring von `test_the_german_catalogue_covers_both_german_language_codes`
an der Zahl hängt.

Die Phase hat einen **Fund, der größer ist als ihr Auftrag**: die fünf Pluralschlüssel der
bestehenden Kataloge sind im falschen Format geschrieben und liefern heute in Deutsch und
Französisch für jede Anzahl außer 1 den **englischen** Quellstring. Nextcloud sucht einen
Plural unter dem zusammengesetzten Schlüssel `_singular_::_plural_` (PHP: `L10N::n`,
JS: `_"+t+"_::_"+n+"_` im gebündelten `@nextcloud/l10n`); Findlings Kataloge tragen den
blanken Singular als Schlüssel mit einer Liste als Wert. Gemessen an der laufenden
Instanz: `de` bei n=2 antwortet `2 days`, `fr` bei n=2 antwortet `2 days`. Über alle
mitgelieferten Nextcloud-Apps sind 120 von 120 Plural-Einträgen zusammengesetzt und 0
blank. Ohne diesen Fix ist Erfolgskriterium 1 ("keine englischen Reste") für die neuen
Sprachen nicht erreichbar, und da das Gate Schlüsselgleichheit über **alle** Kataloge
fordert, muss der Fix alle sechs bestehenden Dateien gleichzeitig mitnehmen.

**Primäre Empfehlung:** Erst den Ladepfad-Beweis und die Pluralregeln festnageln (beides
liegt unten fertig vor), dann in einer Welle 0 das Pluralschlüssel-Format in den sechs
bestehenden Katalogen reparieren und die Gates parametrisieren, danach die zehn neuen
Dateien aus einem Generator gießen, mit drei Formen für es/it/pt_BR/pt_PT, bei denen Form 1
und Form 2 denselben Wortlaut tragen.

---

<phase_requirements>
## Phase Requirements

| ID | Beschreibung (aus REQUIREMENTS.md) | Wo die Recherche trägt |
|----|-------------------------------------|------------------------|
| KAT-01 | UI-Kataloge für es, it, nl, pt_BR und pt_PT im Gleichstand mit EN/DE/FR (Schlüsselzahl aus `de.json` ZÄHLEN); Nextcloud kennt kein `pt`, also zehn neue Dateien (php + backend); `nplurals=3` für es/it/pt_BR/pt_PT korrekt, Gates parametrisiert statt vier Kopien des FR-Blocks | Abschnitt "Dateiorte und Ladepfad" (zehn Dateien, alle in `php/l10n/`, Begründung warum die ExApp keine braucht), "Pluralformen" (Regeln aus den Kerndateien gelesen, PHP/JS-Divergenz gemessen), "Pattern 3" (Gate-Parametrisierung als Tabelle je Sprache), "Die Zahl heute" (202) |
| KAT-02 | Übersetzungen maschinell erstellt plus Review mit datiertem Vorbehalt (FR-Muster; Muttersprachler-Gate ausdrücklich NICHT Pflicht); der pt-Sprachcode-Ladepfad wird VOR der Übersetzungsarbeit an der laufenden Test-Nextcloud verifiziert | Abschnitt "Ladepfad, an der laufenden Instanz bewiesen" (Beweis liegt vor, Rezept zum Nachfahren steht da), "Pattern 5: Der datierte Vorbehalt nach FR-Muster", "Der maschinelle Prozess (E-17-5)" |
</phase_requirements>

---

## User Constraints

Es gibt **keine** `20-CONTEXT.md` (`has_context: false`). An ihre Stelle treten drei
Quellen, die für die Planung dieselbe Bindungskraft haben:

### Gesperrte Entscheide (Owner-Tor Phase 17, `17-GRUNDSATZ-ENTSCHEID.md`)

- **E-17-5, Katalogprozess:** Option a, maschinell plus Community-Review mit datiertem
  Vorbehalt, **ohne** Muttersprachler-Gate. Vollzug ausdrücklich: "Phase 20
  (Parallelpfad) erzeugt zehn Katalogdateien und trägt je Katalog den datierten
  Vorbehalt ein." Option b (Muttersprachler-Gate vor Auslieferung) ist nicht gewählt.
- **Beweisgrundlage laut Entscheid:** "das ausgelieferte französische Katalogpaar und
  sein Vorbehalt; die Schlüsselzahl-Gates fangen Lücken, nicht Wortwahl."

### Gesperrt durch die Roadmap (Erfolgskriterien Phase 20)

1. Nutzer auf es, it, nl, pt_BR, pt_PT sieht Findling vollständig in dieser Sprache,
   inklusive Fehler- und Diagnosetexten, keine englischen Reste.
2. Jeder neue Katalog führt dieselbe Schlüsselzahl wie `de.json`, **aus der Datei
   gezählt**; das Gate ist parametrisiert statt viermal kopiert und fällt rot, sobald ein
   Katalog zurückbleibt.
3. Pluralformen stimmen gegen die **Kerndateien der Ziel-Nextcloud** (`nplurals=3` für
   es/it/pt_BR/pt_PT, 2 für nl); gelesen, nicht erinnert.
4. Der pt-Ladepfad ist **VOR** der Übersetzungsarbeit an der laufenden Test-Nextcloud
   verifiziert; zehn Dateien liegen am richtigen Ort.
5. Jeder Katalog trägt einen datierten Review-Vorbehalt nach FR-Muster; kein
   Muttersprachler-Gate blockiert die Auslieferung.

### Claude's Discretion (offen, Empfehlung unten)

- Ob der Pluralschlüssel-Fund in dieser Phase repariert wird oder als eigener Befund
  herausfällt (siehe Open Question 1, Empfehlung: in dieser Phase, Welle 0).
- Aufteilung und Form der Doku-Dateien für den Vorbehalt (ein `docs/l10n-<sprache>.md` je
  Sprache gegen eine Sammeldatei).
- Wie der Gleichstands-Nachweis in CI verankert wird (Pfadfilter gegen Zusatzschritt).

### Ausdrücklich außerhalb (Deferred)

- Getrennte pt_BR/pt_PT-Wortlaute **für die Suche selbst** (REQUIREMENTS "Future
  Requirements"). Betrifft nicht die UI-Kataloge, die sehr wohl getrennt sind.
- Französisches Körperfeld, niederländische Komposita (Phase 21), Messphase (22),
  Store-Texte und Store-Kurztexte in den vier neuen Sprachen (offene Frage 10 der
  Milestone-Research, Owner-Entscheid, Kurztext-Regel, gehört zu Phase 23).
- Ein Sprachumschalter in der UI (Out of Scope des Milestones).

---

## Project Constraints (from CLAUDE.md)

| Direktive | Was sie für diese Phase heißt |
|-----------|-------------------------------|
| Code englisch, Projektkommunikation deutsch | Katalog**schlüssel** bleiben englisch (sie sind der Quellstring), Werte sind die Zielsprache. Planungsdokumente deutsch. |
| Keine Em-Dashes | Gilt doppelt: `scan_prose` läuft bereits über alle Kataloge und meldet U+2014 und U+2013. Maschinelle es/pt-Übersetzungen liefern gern Halbgeviertstriche. |
| Echte Umlaute nur in deutscher Prosa, nie in Code | Katalogwerte sind Prosa und tragen echte Akzente (`información`, `perché`, `één`, `utilizador`). Dateinamen und Schlüssel bleiben ASCII. |
| Keine Emojis, Icons als SVG | `scan_prose` prüft es über die Kataloge mit. |
| Python-Qualitätsgates (ruff-Vollregelsatz, pyright basic mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, vulture), lokal grün vor Commit | Die Gate-Änderungen liegen in `backend/tests/test_admin_ui_contract.py`, also im Geltungsbereich. |
| Nach jeder Phase Security-, Bug- und Performance-Audit | Gilt auch für diese Phase, siehe Security Domain unten. |
| GSD-Workflow, keine direkten Repo-Änderungen außerhalb | Diese Recherche hat zwei Probedateien angelegt und wieder entfernt, `git status` ist sauber. |
| Kurze Produkttexte, Owner-Abnahme vor Release | Betrifft Store-Texte, nicht die UI-Kataloge. Falls die Phase Store-Sprachen anfassen will: Owner-Tor. |

Arbeitsregel aus dem Auftrag, **präzisiert durch Messung**: "jede Änderung unter
`backend/src/findling` oder `php/` zieht `PACKAGE_TREE_HASH_TODAY` bzw.
`PHP_TREE_HASH_TODAY` nach" gilt nur für die Dateimuster der Rezepte. Die Rezepte laufen
über `**/*.py` unter `backend/src/findling` und über `**/*.php` unter `php`
(`docs/measurements/2026-09-*/skripte/40b-baumhash.py`, `path.glob(pattern)`;
`backend/tests/test_measurement_scripts.py:1074` und `:1096`). **Katalogdateien
(`.json`, `.js`) und Testdateien liegen in keinem der beiden Bäume.** Plan 18-10 sagt
dasselbe im Klartext: "Katalogdateien und `admin.js` liegen ausserhalb des Musters." Eine
reine Katalog-und-Test-Phase bewegt also **keinen** Baumhash, und wer einen bewegt, hat
eine `.php`- oder `src/findling`-Datei angefasst, die nicht in diese Phase gehört.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Übersetzte Sätze der Adminseite und der Ergebnisseite beim ersten Render | Frontend Server (PHP, `templates/*.php` über `$l->t()`/`$l->n()`) | - | Nextcloud lädt `php/l10n/<lang>.json` über `OC\L10N\Factory` in die PHP-Seite |
| Übersetzte Sätze, die das Skript nach jedem Poll neu setzt | Browser / Client (`php/js/admin.js` über `t('findling', ...)`) | Frontend Server (liefert `l10n/<lang>.js` als Script) | `Util::addScript('findling','admin')` hängt automatisch `findling/l10n/<lang>` davor |
| Auswahl des Sprachcodes | Frontend Server (`Factory::findLanguage`/`languageExists`) | - | Exakter Dateiname, keine Kürzung; entscheidet über jede der zehn Dateien |
| Pluralauswahl | geteilt: PHP über Symfony `IdentityTranslator` (Sprachcode), JS über die deklarierte `pluralForm` | - | **Zwei verschiedene Regelquellen**, siehe Pitfall 2 |
| Gleichstand und Typografie der Kataloge | CI / Test (`backend/tests/test_admin_ui_contract.py`) | - | Einziger Ort, an dem ein zurückgebliebener Katalog rot wird |
| Auslieferung der Kataloge ins Store-Paket | Build / Release (`scripts/release/store-archive.sh`) | - | `cp -R php/l10n`, keine Dateiliste, neue Dateien reisen automatisch mit |
| Diagnose- und Fehlertexte, die aus dem Container stammen | Frontend Server (PHP übersetzt Codes zu Sätzen) | API / Backend (liefert nur Codes) | Der Container schickt `reason`-Codes, `AdminViewService` macht Worte daraus |

---

## Standard Stack

### Kern

| Werkzeug | Version | Zweck | Warum Standard |
|----------|---------|-------|----------------|
| Nextcloud-Katalogformat `l10n/<lang>.json` + `l10n/<lang>.js` | NC 33 bis 35 | die einzige Form, die Nextcloud lädt | `Factory::getL10nFilesForApp` liest genau `<appdir>/l10n/<lang>.json`, `Util::addScript` hängt `<app>/l10n/<lang>` davor [VERIFIED: Serverquelle in der laufenden Test-Nextcloud 34.0.3] |
| `python -m json` / stdlib `json` | Python 3.13 | Kataloge lesen, zählen, gießen | Der Bestand wird schon so geprüft (`catalogue_of()` in `test_admin_ui_contract.py`) |
| `pytest` über `backend/tests/test_admin_ui_contract.py` | vorhanden | das Gate | einziger Ort, der Kataloge überhaupt liest |
| laufende Test-Nextcloud `findling-nextcloud` (Image `nextcloud:34.0.3-apache`) | läuft seit 6 Tagen | Ladepfad- und Sichtproben | `php/` ist als `custom_apps/findling` **gebunden**, jede Datei ist sofort live [VERIFIED: `docker inspect`] |

### Unterstützend

| Werkzeug | Zweck | Wann |
|----------|-------|------|
| `docker exec -u www-data findling-nextcloud php /var/www/html/occ ...` | Nutzersprache setzen, App-Liste prüfen | Sichtprobe je Sprache |
| kleines Python-Skript json -> js | die `.js` mechanisch aus der `.json` gießen | jede der zehn Dateien, siehe Code Examples |
| `.github/workflows/integration.yml`, Job `search-parity` | Cookie-Login auf die Ergebnisseite | automatisierter Sprachbeweis in CI |
| `scripts/dev/probe_page_login.sh` | dieselbe Strecke von Hand | lokale Sichtprobe |

### Ausdrücklich NICHT verwenden

| Naheliegend | Warum nicht |
|-------------|-------------|
| `occ l10n:createjs findling es` | Der Befehl existiert, liest seine Quelle aber aus `l10n/<lang>.php` (`loadTranslations()` wirft `UnexpectedValueException`, wenn die Datei fehlt) und schreibt **beide** Dateien nur, wenn sie noch nicht existieren. Findling hat keine `.php`-Kataloge. Unbrauchbar. [VERIFIED: `core/Command/L10n/CreateJs.php` in der laufenden Instanz] |
| Transifex oder ein anderer Übersetzungsdienst | Das Projekt führt bewusst keinen externen Dienst; E-17-5 wählt Community-Review im Repo |
| ein neues Python-Paket für Übersetzung (`argostranslate`, `deep-translator`, ...) | Diese Phase installiert **nichts**. Die Wortlaute entstehen beim Ausführen, die Gates prüfen sie mechanisch. Ein Übersetzungspaket im Backend wäre eine Abhängigkeit im ausgelieferten Image für eine Aufgabe, die einmal anfällt |
| `backend/l10n/` anlegen | Die ExApp hat kein App-Verzeichnis in der Nextcloud (`ls /var/www/html/custom_apps` zeigt nur `findling`), also lädt Nextcloud dort nichts. [VERIFIED] |

**Installation:** keine. Diese Phase legt Textdateien an und ändert Tests.

---

## Package Legitimacy Audit

**Nicht anwendbar.** Phase 20 installiert kein externes Paket, weder im Backend
(`backend/pyproject.toml` unberührt) noch in der PHP-Hälfte (`php/composer.json`
unberührt). Die Standard-Stack-Tabelle oben nennt ausschließlich bereits vorhandene
Werkzeuge und Nextcloud-Bordmittel.

| Package | Registry | Disposition |
|---------|----------|-------------|
| - | - | keine neue Abhängigkeit in dieser Phase |

---

## Architecture Patterns

### Dateiorte und Ladepfad

```
php/                                  <- ist in der Test-Nextcloud als custom_apps/findling gemountet
├── l10n/
│   ├── de.json   de.js               <- Bestand
│   ├── de_DE.json de_DE.js           <- zeichengleiche Kopie von de.*
│   ├── fr.json   fr.js               <- Bestand
│   ├── es.json   es.js               <- NEU
│   ├── it.json   it.js               <- NEU
│   ├── nl.json   nl.js               <- NEU
│   ├── pt_PT.json pt_PT.js           <- NEU
│   └── pt_BR.json pt_BR.js           <- NEU (eigener Wortlaut, KEINE Kopie von pt_PT)
├── templates/{admin,search}.php      <- $l->t() und $l->n(), 1. Render
└── js/{admin,search}.js              <- t('findling', ...) und n('findling', ...), jeder Poll

backend/tests/test_admin_ui_contract.py   <- alle Gates, L10N_CATALOGUES waechst 6 -> 16
docs/l10n-french.md                        <- Muster fuer Wortwahl, Typografie, Vorbehalt
docs/l10n-<sprache>.md                     <- NEU, je Sprache
```

Datenfluss, damit klar ist, warum es **zwei** Dateien je Sprache sind und warum der
Dateiname exakt stimmen muss:

```
Nutzer hat core/lang = "pt_PT"
        |
        v
 PHP-Render der Seite                          Browser, jeder Poll
        |                                              |
 Factory::get('findling','pt_PT')             Util::addScript('findling','admin')
        |                                              |
 validateLanguage -> languageExists            addTranslations('findling')
        |  (Dateiliste von php/l10n/*.json)            |  findLanguage('findling')
        |                                              v
        |                                     <script src=".../findling/l10n/pt_PT.js">
        v                                              |
 getL10nFilesForApp:                                   v
   "<appdir>/l10n/" . "pt_PT" . ".json"        OC.L10N.register("findling", {...}, "<pluralForm>")
   KEINE Kuerzung auf "pt"                             |
        |                                              v
        v                                     t('findling', key) / n('findling', s, p, count)
 $l->t(key) / $l->n(s,p,count)                  Regel: die DEKLARIERTE pluralForm
 Regel: Symfony IdentityTranslator
        ueber den Sprachcode
```

### Ladepfad, an der laufenden Instanz bewiesen (Erfolgskriterium 4)

Der Beweis ist **schon erbracht** und hier dokumentiert, damit die Planung ihn nicht
erfinden muss. Gefahren am 2026-09-24 gegen `findling-nextcloud` (`nextcloud:34.0.3-apache`,
`php -v` = 8.5.9):

1. `ls core/l10n/ | grep -E '^(es|it|nl|pt)'` liefert
   `es es_EC es_MX it nl pt_BR pt_PT` je als `.js` und `.json`. **Kein `pt`.**
   [VERIFIED: laufende Test-Nextcloud]
2. `findAvailableLanguages(null)` (die Liste, aus der die persönlichen Einstellungen die
   Sprachen anbieten): `es=yes it=yes nl=yes pt_PT=yes pt_BR=yes pt=no`.
   [VERIFIED: Sonde über `lib/base.php`]
3. Mit einer echten `php/l10n/pt.json` (Wert `Findling` -> `PROBE_PT`):

   | angefragte Sprache | `languageExists('findling', lang)` | `getLanguageCode()` | `t('Findling')` |
   |---|---|---|---|
   | `pt` | yes | `pt` | `PROBE_PT` |
   | `pt_PT` | **no** | **`en`** | `Findling` |
   | `pt_BR` | **no** | **`en`** | `Findling` |
   | `es`, `it`, `nl` | no (noch kein Katalog) | `en` | `Findling` |
   | `fr`, `de_DE` | yes | `fr`, `de_DE` | (Bestand) |

   [VERIFIED: eigene Sonde, 2026-09-24; Probedatei danach entfernt, `git status` sauber]

4. Der Code dazu, damit niemand die Tabelle für Erinnerung hält
   (`lib/private/L10N/Factory.php`):

```php
// Source: nextcloud/server 34.0.3, lib/private/L10N/Factory.php:571 ff.
private function getL10nFilesForApp(string $app, string $lang): array {
    $i18nDir = $this->findL10nDir($app);
    $transFile = strip_tags($i18nDir) . strip_tags($lang) . '.json';
    // ... isSubDirectory(...) && file_exists($transFile) -> laden, sonst nichts
}
// validateLanguage() davor: languageExists() nein -> findLanguage(), und findLanguage
// prueft jede Stufe erneut mit languageExists(). Nirgends wird "pt_PT" zu "pt" gekuerzt.
```

**Folge für die Planung:** Die `LanguageIterator`-Kürzung, die die Milestone-Research als
Hoffnung für einen einzigen `pt`-Katalog genannt hat, gilt für Benachrichtigungen und
Mails, **nicht** für den Dateiladepfad der App-Kataloge. Die offene Frage 7 der
Milestone-Research ist damit beantwortet: `pt_PT` **und** `pt_BR`, vier Dateien für
Portugiesisch.

**Nebenbefund, als benannte Grenze zu dokumentieren:** Der Kern liefert auch `es_EC` und
`es_MX`. Ein Nutzer auf `es_MX` bekommt Findling nicht auf Spanisch, aus demselben Grund,
aus dem `de_DE` 2026-09-09 vier statt zwei deutsche Dateien erzwungen hat. Das FR-Muster
hat dieselbe Frage für `fr_CA` mit "wird nicht ausgeliefert" beantwortet
(`test_admin_ui_contract.py:110-114`). Empfehlung: gleich entscheiden, Grenze in der
Doku benennen, **nicht** vier weitere Dateien bauen. [ASSUMED für die Auswirkung auf reale
Nutzer, VERIFIED für den Mechanismus]

### Die Zahl heute

| Größe | Wert | gezählt aus |
|---|---:|---|
| Schlüssel in `php/l10n/de.json` | **202** | `json.load(...)["translations"]`, 2026-09-24 |
| davon Pluralschlüssel (Wert ist eine Liste) | 5 | dieselbe Zählung |
| davon mit printf-Direktiven (`%%`, `%1$s`, `%s`, `%n`) | **40** | Regex `PRINTF_DIRECTIVE` aus dem Gate (die 37 in `docs/l10n-french.md` sind der Stand vom 11.09.) |
| Dateien mit Wert `|` (Pipe) | 0 | siehe Pitfall 4 |
| Schlüssel mit nacktem `%` außerhalb einer Direktive | 0 | siehe Pitfall 3 |
| Schlüssel in `fr.json`, `de_DE.json` | 202, 202 | dieselbe Zählung |
| harte Zahl im Gate | 202 | `test_admin_ui_contract.py`, `assert len(keys_of["de.json"]) == 202` |

**Regel, die an der Zahl hängt:** Der Docstring über der harten Zahl verlangt wörtlich
"Whoever raises it next writes the next paragraph". Wer die Zahl anfasst, schreibt den
Absatz. Wer die **Schlüsselnamen** ändert (Pluralfix), schreibt ihn ebenfalls, auch wenn
die Zahl stehen bleibt: der Absatz ist das Gedächtnis dieser Datei.

### Pluralformen, aus den Kerndateien der Ziel-Nextcloud gelesen

Gelesen am 2026-09-24 aus `/var/www/html/core/l10n/<lang>.json` der laufenden Instanz,
Feld `pluralForm`:

| Sprache | `pluralForm` der Kerndatei (wörtlich) | nplurals |
|---|---|---|
| `es` | `nplurals=3; plural=n == 1 ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;` | 3 |
| `it` | `nplurals=3; plural=n == 1 ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;` | 3 |
| `nl` | `nplurals=2; plural=(n != 1);` | 2 |
| `pt_PT` | `nplurals=3; plural=(n == 0 \|\| n == 1) ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;` | 3 |
| `pt_BR` | `nplurals=3; plural=(n == 0 \|\| n == 1) ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;` | 3 |
| `fr` (nur zur Einordnung) | `nplurals=3; ...` wie pt | 3 |
| `de`, `de_DE` | `nplurals=2; plural=(n != 1);` | 2 |

[VERIFIED: laufende Test-Nextcloud 34.0.3, `php -r` über die Kerndateien]

Damit ist Erfolgskriterium 3 vorgeklärt: `nplurals=3` für es/it/pt_BR/pt_PT, 2 für nl,
genau wie die Roadmap sagt. **Die Zeichenkette wörtlich übernehmen**, nicht nachbauen.

Der Nebenbefund aus `PITFALLS.md` bestätigt sich: der heutige Kern führt `fr` mit
`nplurals=3`, Findlings `fr.json` und die harte Konstante `FRENCH_PLURAL_FORM` stehen auf
`nplurals=2; plural=(n > 1);`. Das ist **kein** Fehler, den diese Phase anfassen muss
(siehe Pitfall 2: die französische Zwei-Formen-Variante ist in beiden Halbzeiten korrekt),
aber die Gate-Konstante muss sprachweise werden, damit `fr` bei 2 bleiben kann, während
`es` auf 3 geht.

### Pattern 1: Der Pluralschlüssel ist zusammengesetzt, nicht blank

**Was:** Nextcloud speichert einen Plural unter dem Schlüssel `_<singular>_::_<plural>_`
und nicht unter dem Singular allein.

**Beleg, PHP** (`lib/private/L10N/L10N.php:93`):

```php
// Source: nextcloud/server 34.0.3
public function n(string $text_singular, string $text_plural, int $count, array $parameters = []): string {
    $identifier = "_{$text_singular}_::_{$text_plural}_";
    if (isset($this->translations[$identifier])) {
        return (string)new L10NString($this, $identifier, $parameters, $count);
    }
    if ($count === 1) { return (string)new L10NString($this, $text_singular, $parameters, $count); }
    return (string)new L10NString($this, $text_plural, $parameters, $count);   // <- englisch, wenn der Katalog nur den Singular kennt
}
```

**Beleg, JS** (`dist/core-common.js`, gebündeltes `@nextcloud/l10n`):

```js
// Source: nextcloud/server 34.0.3, dist/core-common.js (minifiziert, hier lesbar gesetzt)
function ngettext(app, singular, plural, count, vars, options) {
  const id = "_" + singular + "_::_" + plural + "_"
  const bundle = options?.bundle ?? getAppTranslations(app)
  const value = bundle.translations[id]
  if (value !== undefined && Array.isArray(value)) {
    return translate(app, value[bundle.pluralFunction(count)], vars, count, options)
  }
  return translate(app, count === 1 ? singular : plural, vars, count, options)
}
// und in translate(): let g = bundle.translations[text] || text; g = Array.isArray(g) ? g[0] : g
```

**Gemessen am Bestand** (`$l->n('%n day','%n days',$n)` gegen die laufende Instanz mit
den heutigen Katalogen):

| Sprache | n=1 | n=2 | n=5 |
|---|---|---|---|
| `de` | `1 Tag` | **`2 days`** | **`5 days`** |
| `fr` | `1 jour` | **`2 days`** | **`5 days`** |

[VERIFIED: eigene Sonde, 2026-09-24]

**Gegenprobe über den Bestand der Nextcloud selbst:** über alle `apps/*/l10n/de.json` der
Instanz stehen **120 Plural-Einträge, alle zusammengesetzt, kein einziger blank**.
[VERIFIED]

**Wann anwenden:** für alle fünf Pluralschlüssel in allen sechzehn Dateien, gleichzeitig.
Ein halber Umbau ist ein rotes G1-Gate (Schlüsselmengen stimmen nicht mehr überein).

**Was sich dadurch ändert:**

```
vorher:  "%n day": ["%n Tag", "%n Tage"]
nachher: "_%n day_::_%n days_": ["%n Tag", "%n Tage"]
```

Die Schlüsselzahl bleibt 202. Die fünf betroffenen Schlüssel:
`%n minute`, `%n hour`, `%n day`, `and %n more`,
`A worker holds this file. The claim runs out in %n second if nothing acknowledges it.`
Der jeweilige Plural-Quellstring steht an der Aufrufstelle:
`php/templates/admin.php:192,195,198,719,723`, `php/lib/Service/AdminViewService.php:956`,
`php/js/admin.js:126,129,131`.

### Pattern 2: Drei Formen schreiben, Form 1 und Form 2 gleich halten

**Was:** Für es/it/pt_BR/pt_PT tragen die fünf Pluralwerte **drei** Formen, und die
zweite und dritte sind wortgleich.

**Warum das kein Schlendrian ist, sondern eine Messung:** PHP und JS wählen den Index aus
**verschiedenen Quellen**. PHP liest die deklarierte `pluralForm` überhaupt nicht
(`L10N::load()` übernimmt nur `$json['translations']`), sondern gibt die mit `|`
verbundenen Formen an Symfonys `IdentityTranslator` mit dem **Sprachcode**. Gemessen mit
Katalogen, die `FORM0/FORM1/FORM2` tragen:

| Sprache | PHP wählt bei n=0 | n=1 | n=2 | n=5 | n=1000000 |
|---|---|---|---|---|---|
| `es` | FORM1 | FORM0 | FORM1 | FORM1 | FORM1 |
| `it` | FORM1 | FORM0 | FORM1 | FORM1 | FORM1 |
| `nl` | FORM1 | FORM0 | FORM1 | FORM1 | FORM1 |
| `pt_PT` | FORM1 | FORM0 | FORM1 | FORM1 | FORM1 |
| `pt_BR` | **FORM0** | FORM0 | FORM1 | FORM1 | FORM1 |

[VERIFIED: eigene Sonde, 2026-09-24. **PHP erreicht FORM2 nie.**]

Die JS-Seite dagegen wertet die deklarierte Regel aus und wählt für `es` bei n=2 den
Index **2**. Stünde in Form 1 die Millionen-Variante und in Form 2 der normale Plural,
liefe die Seite beim ersten Render anders als nach dem ersten Poll: `2 de dias` im Server-
HTML, `2 dias` im Browser.

**Dass der Kern selbst in diese Falle läuft**, ist gemessen und die Begründung dafür, dem
Kern hier **nicht** zu folgen:

| Kerndatei | Plural-Einträge | mit 3 Formen | davon Form 1 == Form 2 |
|---|---:|---:|---:|
| `core/l10n/es.json` | 6 | 6 | **6** |
| `core/l10n/it.json` | 6 | 6 | **6** |
| `core/l10n/pt_PT.json` | 8 | 8 | 6 |
| `core/l10n/pt_BR.json` | 9 | 9 | **0** |

`pt_BR` schreibt konsequent `["%n resultado", "%n de resultados", "%n resultados"]`, also
die Millionen-Form auf Index 1, und rendert damit auf der PHP-Seite bei n=2 `2 de
resultados`. Für unsere fünf Schlüssel (Minuten, Stunden, Tage, "and %n more", Sekunden
einer Sperre) kommt eine Million nie vor. **Entscheid für diese Phase:** drei Formen
deklarieren (Kriterium 3 erfüllt), Form 1 und Form 2 wortgleich als normalen Plural
setzen, und diesen Entscheid mit dieser Messung in der Sprachdoku begründen.

Die eine verbleibende Abweichung, als benannte Grenze zu dokumentieren: bei **n=0** wählt
JS für `pt_PT` (Regel `(n==0||n==1)?0:...`) den **Singular**, PHP den Plural. Betroffen ist
höchstens die Sekundenzeile der Sperre; die drei Zeitspannen laufen über
`max(1, ...)`-Schwellen, und "and %n more" wird nur bei Rest > 0 gerendert.

### Pattern 3: Die Gates einmal parametrisieren statt viermal kopieren

Heute stehen fünf Katalog-Gates in `backend/tests/test_admin_ui_contract.py`. Sie sind
sauber gebaut: vier von fünf tragen schon eine Scanner-Funktion mit Selbsttest und
Anti-Leerlauf-Klausel. Zu ändern ist die **Datenseite**, nicht die Logik.

| Gate (Testname) | heute | Änderung |
|---|---|---|
| `test_the_two_translation_files_carry_the_same_keys` | `de.json` gegen `de.js` | unverändert lassen, es ist die IN-02-Klammer für Deutsch |
| `test_the_german_catalogue_covers_both_german_language_codes` | Textgleichheit `de` gegen `de_DE`, plus harte Zahl 202 | Zahl bleibt; **kein** Analogon für `pt_PT` gegen `pt_BR` bauen, die beiden sind absichtlich verschieden (`ficheiro`/`arquivo`, `utilizador`/`usuário`, `ecrã`/`tela`) |
| `test_all_six_catalogues_carry_the_same_keys` | Tupel `L10N_CATALOGUES` mit 6 Pfaden, `scan_key_sets` | Tupel auf 16, Logik trägt unverändert. Testnamen mitziehen ("six" stimmt nicht mehr) |
| `test_every_french_value_carries_a_french_wording` | `scan_french_completeness` + eine globale Ausnahmeliste | Scanner in `scan_completeness(name, catalogue, exceptions)` umbenennen, Ausnahmeliste **je Sprache** als Mapping mit Begründung je Eintrag (Listen, keine Schwellwerte, das ist der ausdrückliche Entwurfsentscheid im Docstring) |
| `test_no_french_value_loses_or_invents_a_placeholder` | `scan_placeholder_parity` über `fr.*` | sprachunabhängig, auf alle 16 Dateien ausdehnen **und** für zusammengesetzte Pluralschlüssel reparieren (siehe unten) |
| `test_the_french_catalogues_carry_the_french_plural_rule` | zwei Konstanten `FRENCH_PLURAL_FORM`/`GERMAN_PLURAL_FORM` | ein Mapping `PLURAL_FORM_OF = {"de": ..., "de_DE": ..., "fr": ..., "es": ..., "it": ..., "nl": ..., "pt_PT": ..., "pt_BR": ...}` mit der **wörtlich** aus der Kerndatei gelesenen Zeichenkette, plus die Formenzahl je Sprache |
| `test_no_file_of_the_page_carries_a_dash_or_an_emoji` | `scan_prose` über `L10N_CATALOGUES` | wächst automatisch mit dem Tupel |

**Die Falle bei der Platzhalterparität nach dem Pluralfix:** `scan_placeholder_parity`
vergleicht die Direktiven des Schlüssels mit denen jeder Form. Ein zusammengesetzter
Schlüssel `_%n day_::_%n days_` trägt **zwei** `%n`, jede Form trägt eines. Das Gate
würde rot, obwohl alles stimmt. Der Scanner muss einen Schlüssel, der `_::_` enthält, an
dieser Marke teilen und gegen die Hälften vergleichen (Singularhälfte gegen Form 0, Plural-
hälfte gegen alle weiteren Formen). Das ist die einzige echte Logikänderung der Phase.

**Empfohlene Datenform** (eine Tabelle, aus der jedes Gate sich bedient):

```python
# Source: Vorschlag, gebaut nach dem Muster von L10N_CATALOGUES und
# FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY in test_admin_ui_contract.py
CATALOGUE_LANGUAGES = {
    # code: (pluralForm woertlich aus core/l10n/<code>.json, Formenzahl, Ausnahmen mit Grund)
    "de":    (GERMAN_PLURAL_FORM, 2, {}),
    "de_DE": (GERMAN_PLURAL_FORM, 2, {}),
    "fr":    (FRENCH_PLURAL_FORM, 2, FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY),
    "es":    (SPANISH_PLURAL_FORM, 3, {"Findling": "...", "PDF": "..."}),
    ...
}
```

### Pattern 4: Die `.js` wird gegossen, nicht getippt

Zwei Dateien je Sprache mit identischer Schlüsselmenge, von Hand gepflegt, sind die Form,
die `test_the_two_translation_files_carry_the_same_keys` überhaupt erst nötig gemacht hat.
Für zehn neue Dateien ist Handarbeit die teuerste Fehlerquelle. Die `.js` ist eine reine
Funktion der `.json`; das Rezept steht in den Code Examples. Format des Bestands, das der
Generator treffen muss: 4 Leerzeichen Einrückung, LF, abschließender Zeilenumbruch, UTF-8
ohne BOM [VERIFIED: `file` und Bytezählung über die sechs Bestandsdateien].

### Pattern 5: Der datierte Vorbehalt nach FR-Muster

`docs/l10n-french.md` ist das Muster und hat eine Struktur, die sich eins zu eins
übertragen lässt:

| Abschnitt in `docs/l10n-french.md` | Was er leistet | Für es/it/nl/pt |
|---|---|---|
| "Die Schlüsselmenge, aus der Datei gezählt" | Zahl mit Herkunft, nicht aus der Recherche übernommen | übernehmen, 202 |
| "Wortwahl" | die Entscheide, die Entscheidungen und keine Übersetzungen sind (`le service` für "the backend") | je Sprache drei bis fünf Begriffe festlegen und begründen: backend, run, worker, index, coverage |
| "Typografie" | echte Akzente, ASCII-Apostroph, kein Gedankenstrich, Platzhalter wie im Schlüssel | übernehmen, sprachspezifisch ergänzen (es: `¿`/`¡`; pt: kein NBSP; nl: `één` mit echten Akzenten) |
| "Pluralformen" | die Regel und warum sie nicht die deutsche ist | übernehmen, plus die Drei-Formen-Messung aus Pattern 2 |
| "Die Tabelle" | Schlüssel, DE, Zielsprache, maschinell erzeugt | 202 Zeilen je Sprache |
| "Ausnahmen für das Vollständigkeitsgate G2" | benannte Liste mit Grund je Eintrag | je Sprache eigene Liste |
| "Maschinelle Prüfungen" | Ergebnistabelle der Scanner | übernehmen |
| "Abnahme" / "Nachtrag ..." | **der datierte Vorbehalt** | siehe Wortlaut unten |

**Der Vorbehalt, im Wortlaut des Bestands** (`docs/l10n-french.md`, Nachtrag 24.09.2026):
"Alle drei stehen oben in der Tabelle und sind maschinell geprüft (Schlüsselmenge,
Platzhalter-Parität, echte Akzente). **Vom Owner noch nicht gelesen**, also gehören sie zur
Abnahme der Phase 18 ... Das steht hier, damit eine abgenommene Datei nicht stillschweigend
Zeilen mitträgt, die niemand abgenommen hat."

Für die vier neuen Sprachen fällt der Owner als Muttersprachler weg (E-17-5). Der
Vorbehalt lautet sinngemäß: maschinell erzeugt am `<Datum>`, maschinell geprüft gegen
`<Liste der Gates>`, **von keinem Muttersprachler gelesen**, Community-Review offen unter
`<Ort>`, Auslieferung wartet nicht darauf. Datum und Plannummer gehören hinein, wie im
FR-Bestand.

**Ort des Reviews:** Die Milestone-Research schlägt ein GitHub-Issue je Sprache mit der
Tabelle vor, passend zum Reddit-Nutzer, der Hilfe angeboten hat (BACKLOG BL-F02, Anlass
14./15.09.2026). Das ist eine Owner-Frage, kein Bauentscheid: das Issue-Anlegen und
Anschreiben ist Außenkommunikation und fällt unter die Regel, dass der Owner sendet.

### Anti-Patterns

- **`pt.json` anlegen.** Wird nie geladen, jedes Gate ist grün, die Arbeit ist unsichtbar.
  Oben bewiesen, nicht vermutet.
- **`pt_BR` als Kopie von `pt_PT`** nach dem `de`/`de_DE`-Muster. Die beiden sind echte
  Varietäten mit verschiedenen Alltagswörtern; eine Textgleichheitsprüfung wäre die
  falsche Klammer, genau wie sie es für `fr` gegen `de` wäre.
- **Die Gates viermal kopieren.** Genau das verbietet KAT-01 und Erfolgskriterium 2.
- **Die Zahl 199 oder 174 übernehmen.** 202, aus der Datei, am Plantag erneut.
- **Die deutsche Pluralregel in die neuen Dateien kopieren.** Der Unterschied ist genau
  eine Zeichenkette und fällt in keinem Diff auf.
- **Einen `backend/l10n/`-Ordner bauen.** Nextcloud lädt dort nichts.
- **Im selben Commit eine `.php`-Datei oder etwas unter `backend/src/findling` anfassen.**
  Dann wird ein Baumhash fällig, den diese Phase sonst nicht braucht, und der Fußabdruck
  kollidiert mit Phase 19.

---

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---|---|---|---|
| Pluralauswahl | eine eigene Formenwahl in PHP oder JS | die zwei vorhandenen Wege korrekt bedienen: zusammengesetzter Schlüssel plus wörtliche `pluralForm` aus der Kerndatei | Die Auswahl passiert in Symfony bzw. im gebündelten `@nextcloud/l10n`. Falsch bedient antwortet sie in Englisch, nicht mit einem Fehler |
| Pluralregel-Zeichenketten | die Regeln aus CLDR-Wissen tippen | `core/l10n/<lang>.json` der Ziel-Nextcloud lesen und wörtlich übernehmen | Erfolgskriterium 3 verlangt es ausdrücklich; die es/it-Regel mit dem `% 1000000`-Zweig tippt niemand fehlerfrei aus dem Kopf |
| `.js` aus `.json` | zehn Dateien von Hand doppelt pflegen | ein Generator von zwanzig Zeilen | `test_the_two_translation_files_carry_the_same_keys` existiert nur, weil Handarbeit hier schon einmal auseinandergelaufen ist |
| Sprachcode-Auflösung | raten, ob Nextcloud `pt_PT` auf `pt` kürzt | die Sonde aus "Ladepfad" fahren | Kostet vier Minuten, spart zehn falsch benannte Dateien |
| Katalogprüfung | ein neues Prüfskript neben den Gates | die fünf vorhandenen Scanner parametrisieren | Sie tragen Selbsttests und Anti-Leerlauf-Klauseln, ein zweites Werkzeug wäre ein zweites Ding, das richtig bleiben muss |
| Sichtprobe je Sprache | Screenshots | `occ user:setting <user> core lang es` plus die Cookie-Login-Strecke aus `scripts/dev/probe_page_login.sh` | Wiederholbar, in CI hebbar |

**Kerngedanke:** In dieser Domäne ist fast jeder Fehler **still**. Ein falscher Dateiname,
eine falsche Pluralregel, ein verlorener Platzhalter, ein blanker Pluralschlüssel: nichts
davon erzeugt eine Fehlermeldung. Es erzeugt eine Oberfläche, die aussieht wie übersetzt
und es an der Stelle nicht ist, die niemand ansieht. Deshalb ist jede Behauptung dieser
Phase entweder von einem Gate gehalten oder an der laufenden Instanz gemessen.

---

## Runtime State Inventory

Die Phase ist keine Migration, trägt aber Zustand außerhalb des Git-Baums, weil die
Test-Nextcloud `php/` **direkt einbindet**.

| Kategorie | Befund | Handlung |
|---|---|---|
| Gespeicherte Daten | Nutzersprache steht in `oc_preferences` (`core`/`lang`) der Test-Nextcloud. Für die Sichtprobe je Sprache wird sie gesetzt und muss danach zurück | `occ user:setting <user> core lang <code>` setzen und am Ende auf den Ausgangswert zurück, sonst steht die Testinstanz danach auf Portugiesisch |
| Laufende Dienstkonfiguration | Container `findling-nextcloud` (`nextcloud:34.0.3-apache`) bindet `C:/Users/Student/nextcloud-search/php` nach `/var/www/html/custom_apps/findling`. **Jede Datei, die die Phase in `php/l10n/` anlegt, ist sofort live, und jede Probedatei liegt im Repo** | Probedateien nach jeder Sonde löschen und `git status` prüfen. Diese Recherche hat es zweimal gebraucht |
| OS-registrierter Zustand | keiner. Keine Aufgabenplanung, kein pm2, kein systemd berührt Kataloge | keine |
| Geheimnisse und Umgebungsvariablen | keine. Kataloge tragen keine Konfiguration; `FINDLING_REBUILD_FALLBACK` kommt im Text eines Schlüssels vor, bleibt aber als ASCII-Bezeichner unübersetzt | keine |
| Build-Artefakte und Caches | `data/appdata_*/js` der Test-Nextcloud ist **leer** [VERIFIED], also kein JS-Combiner-Cache, der einen neuen Katalog verschluckt. Die installierte App meldet `1.2.0` in `appinfo/info.xml`, die Instanz zeigt beim `occ` die Meldung "requires upgrade"; das ist der Bestand vor dem Release und blockiert die Sonden nicht | Sollte ein Katalog trotz korrekten Namens nicht erscheinen: Browser-Cache vor Nextcloud-Cache verdächtigen |
| Auslieferungspfad | `scripts/release/store-archive.sh:76` kopiert `l10n` als ganzes Verzeichnis, `occ integrity:sign-app` signiert über alle Dateien, Archivgrenze 20 MB gegen heute 238 KB | keine Änderung nötig, zehn Dateien zu je rund 24 KB sind unkritisch |

---

## Common Pitfalls

### Pitfall 1: `pt.json` statt `pt_PT.json` und `pt_BR.json`

**Was schiefgeht:** Eine Datei statt vier, jedes Gate grün, kein Nutzer sieht Portugiesisch.
**Warum:** Die `LanguageIterator`-Kürzung gilt für Benachrichtigungen, nicht für den
Katalogladepfad. **Vermeidung:** Der Beweis oben; vor der Übersetzungsarbeit fahren,
nicht danach (Erfolgskriterium 4). **Frühwarnzeichen:** `languageExists('findling','pt_PT')`
antwortet `false`, obwohl eine Datei existiert.

### Pitfall 2: Die Pluralregel nur an einer Stelle gepflegt, oder aus dem Kopf

**Was schiefgeht:** drei Varianten desselben Fehlers.
(a) `pluralForm` steht in der `.json`, aber nicht als vierter Parameter von
`OC.L10N.register` in der `.js`; dann rendert der Browser anders als der Server.
(b) Die Regel wird nachgebaut statt aus der Kerndatei kopiert; der `% 1000000`-Zweig ist
lang genug, dass ein Tippfehler unbemerkt bleibt.
(c) Drei Formen deklariert, aber nur zwei geschrieben; die JS-Seite greift auf Index 2 und
bekommt `undefined`.
**Vermeidung:** Regelzeichenkette einmal je Sprache als Konstante im Gate, aus der
Kerndatei gelesen, und ein Gate, das die Formenzahl je Pluralschlüssel gegen `nplurals`
prüft. **Frühwarnzeichen:** Eine Seite, die nach dem ersten Poll andere Worte zeigt als
beim Laden.

### Pitfall 3: Ein nacktes Prozentzeichen im Wortlaut legt die Seite lahm

**Was schiefgeht:** Spanisch und Portugiesisch schreiben Prozent mit Leerzeichen ("50 % de
los archivos"). `L10NString::__toString()` ruft am Ende `vsprintf($text, $this->parameters)`.
Gemessen an PHP 8.5.9: `vsprintf("50 % de los archivos", [])` wirft
`ValueError: The arguments array must contain 1 items, 0 given`. Das ist kein falscher
Text, das ist eine kaputte Seite. [VERIFIED: 2026-09-24]
**Warum das heutige Gate es nicht fängt:** `PRINTF_DIRECTIVE` zählt nur erkannte
Direktiven; `% d` mit Leerzeichen wird von `%[sdn]` nicht erfasst, die Parität bleibt
grün.
**Vermeidung:** Ein zusätzlicher Scanner: jedes `%` in einem Wert muss Teil einer
erkannten Direktive sein (Anzahl der `%`-Zeichen gleich der Anzahl der von
`PRINTF_DIRECTIVE` verbrauchten). `%%` ist die erlaubte Schreibweise für ein literales
Prozentzeichen und wird korrekt zu `%` (gemessen). **Frühwarnzeichen:** keines, bis die
Seite weiß bleibt.

### Pitfall 4: Ein Pipe-Zeichen im Wortlaut

**Was schiefgeht:** `L10NString::__toString()` verbindet die Pluralformen mit `|` und gibt
vorher auf: `if (str_contains($pipeCheck, '|')) return 'Can not use pipe character in
translations';`. Der Nutzer liest dann diesen englischen Satz statt seiner Übersetzung.
**Vermeidung:** Scanner über alle Werte, `|` verboten. Der Bestand hat heute null Pipes
[VERIFIED], also ist das Gate von Anfang an grün und nicht vakuumsdicht.

### Pitfall 5: Der Katalog-Gate läuft in CI gar nicht

**Was schiefgeht:** Die Gates liegen in `backend/tests/test_admin_ui_contract.py`, also in
einem Python-Test. `.github/workflows/python.yml` filtert auf `backend/**`, `scripts/**`,
`docs/measurements/**` und sich selbst. **`php/**` ist nicht dabei.** Ein Commit, der nur
Kataloge anfasst, startet `php.yml` (php -l, info.xml, PHPUnit) und `integration.yml`,
aber **nicht** die Katalog-Gates. Erfolgskriterium 2 verlangt ein Gate, das rot fällt;
ein Gate, das nicht läuft, fällt nicht.
**Vermeidung:** `php/l10n/**` in beide Pfadlisten von `python.yml` aufnehmen, mit einem
Begründungsabsatz in der Form, die diese Datei für jeden Eintrag führt. Die Alternative
("jeder Katalogcommit fasst ohnehin einen Test an") hält genau bis zum ersten
Wortlaut-Nachtrag.
[VERIFIED: Pfadlisten in `python.yml:5-34` und `php.yml:17-30`, Joblisten geprüft]

### Pitfall 6: Der Gleichstand wird für `pt_PT`/`pt_BR` als Textgleichheit gebaut

**Was schiefgeht:** Das `de`/`de_DE`-Muster verführt dazu, die vier portugiesischen Dateien
byteweise gleich zu halten. Dann ist eine der beiden Varietäten falsch, und zwar dauerhaft,
weil ein Gate sie festhält. **Vermeidung:** Schlüsselgleichheit ja, Textgleichheit nein.
Die Unterschiede sind real und bekannt (`ficheiro`/`arquivo`, `utilizador`/`usuário`,
`ecrã`/`tela`, `a transferir`/`baixando`).

### Pitfall 7: Die Schlüsselzahl wird aus diesem Dokument übernommen

**Was schiefgeht:** 202 ist der Stand vom 2026-09-24. Phase 19 fasst laut ihren neun
Plänen **keine** Katalogdatei an (geprüft: `files_modified` aller neun Pläne), aber ein
Nachtrag, ein Hotfix oder eine Umplanung kann die Zahl bewegen.
**Vermeidung:** Beim Planstart zählen:
`python -c "import json,io;print(len(json.load(io.open('php/l10n/de.json',encoding='utf-8'))['translations']))"`.

### Pitfall 8: Der Begründungsabsatz fehlt

**Was schiefgeht:** Der Docstring über der harten Zahl verlangt ihn wörtlich; ein Diff, der
die Zahl oder die Schlüsselnamen ohne Absatz bewegt, ist genau der Fehler, vor dem die
Datei warnt, und der nächste Leser senkt die Zahl wieder.

### Pitfall 9: Die maschinelle Übersetzung bringt Typografie mit

**Was schiefgeht:** Halbgeviertstriche (es/pt lieben sie), typografische Apostrophe
(U+2019), geschützte Leerzeichen (U+00A0, U+202F), gelegentlich ein Emoji.
`scan_prose` fängt Striche und Emojis über alle Kataloge. Apostroph und geschütztes
Leerzeichen fängt es **nicht**; der FR-Bestand hat sie als maschinelle Prüfung in
`docs/l10n-french.md` geführt und nicht als Test. **Vermeidung:** dieselbe Prüfliste je
Sprache in der Doku führen und das Ergebnis eintragen, oder sie zum Gate heben.

### Pitfall 10: Der Fußabdruck wächst über die Phase hinaus

**Was schiefgeht:** Ein Commit, der "nebenbei" `AdminViewService.php` oder etwas unter
`backend/src/findling` anfasst, zieht einen Baumhash nach und kollidiert mit Phase 19
(die `query/rewrite.py`, `index/open.py`, `api/*.py` und `test_measurement_scripts.py`
anfasst). **Vermeidung:** Erwarteter Fußabdruck dieser Phase: `php/l10n/**`,
`backend/tests/test_admin_ui_contract.py`, `docs/l10n-*.md`, optional
`.github/workflows/python.yml` und `.github/workflows/integration.yml` (beide von Phase 19
**nicht** angefasst, geprüft) und höchstens eine neue Testdatei. **`test_measurement_scripts.py`
bleibt unberührt.**

---

## Code Examples

### Den Ladepfad an der laufenden Instanz beweisen (vor der Übersetzungsarbeit)

```bash
# Source: eigene Sonde, 2026-09-24, Container findling-nextcloud (nextcloud:34.0.3-apache)
# 1. Welche Sprachcodes kennt der Kern ueberhaupt?
docker exec findling-nextcloud sh -c 'ls /var/www/html/core/l10n/ | grep -E "^(es|it|nl|pt)"'

# 2. Einen Probekatalog anlegen. ACHTUNG: php/ ist in den Container gebunden,
#    die Datei liegt damit im Repo und muss danach weg.
cat > php/l10n/pt.json <<'JSON'
{ "translations": { "Findling": "PROBE_PT" }, "pluralForm": "nplurals=2; plural=(n != 1);" }
JSON

# 3. Die Frage stellen, die zaehlt.
cat > /tmp/probe.php <<'PHP'
<?php
require_once '/var/www/html/lib/base.php';
$f = \OCP\Server::get(\OCP\L10N\IFactory::class);
echo "verfuegbar: " . implode(',', $f->findAvailableLanguages('findling')) . "\n";
foreach (['pt','pt_PT','pt_BR','es','it','nl'] as $lang) {
    $l = $f->get('findling', $lang);
    printf("%-7s exists=%-4s code=%-6s t(Findling)=%s\n",
        $lang, $f->languageExists('findling',$lang)?'yes':'no', $l->getLanguageCode(), $l->t('Findling'));
}
PHP
docker exec -i findling-nextcloud sh -c 'cat > /var/www/html/probe.php' < /tmp/probe.php
MSYS_NO_PATHCONV=1 docker exec -u www-data findling-nextcloud php /var/www/html/probe.php

# 4. Aufraeumen, und zwar beides.
rm -f php/l10n/pt.json
docker exec findling-nextcloud rm -f /var/www/html/probe.php
git status --short   # muss leer sein
```

Erwartete und am 2026-09-24 erhaltene Ausgabe: `pt` lädt, `pt_PT` und `pt_BR` landen auf
`en`.

### Die Pluralregeln aus den Kerndateien lesen

```bash
# Source: eigene Messung, 2026-09-24
docker exec findling-nextcloud sh -c 'cd /var/www/html/core/l10n && for f in es it nl pt_BR pt_PT; do
  printf "%s\t" "$f"
  php -r "echo json_decode(file_get_contents(\"\$argv[1].json\"),true)[\"pluralForm\"], PHP_EOL;" "$f"
done'
```

### Die `.js` aus der `.json` gießen

```python
# Source: Vorschlag, Format abgelesen an php/l10n/de.js und php/l10n/fr.js
import json
from pathlib import Path

def cast_js(code: str) -> None:
    """Schreibt l10n/<code>.js aus l10n/<code>.json, im Format des Bestands."""
    data = json.loads(Path(f"php/l10n/{code}.json").read_text(encoding="utf-8"))
    body = json.dumps(data["translations"], ensure_ascii=False, indent=4)
    # Der Bestand ruecke den Rumpf um vier Leerzeichen ein und haengt die Regel als
    # vierten Parameter an. ensure_ascii=False, weil echte Akzente gefordert sind.
    inner = "\n".join("    " + line for line in body.splitlines()[1:-1])
    text = (
        'OC.L10N.register(\n    "findling",\n    {\n'
        f"{inner}\n"
        "},\n"
        f'"{data["pluralForm"]}");\n'
    )
    Path(f"php/l10n/{code}.js").write_text(text, encoding="utf-8", newline="\n")
```

`newline="\n"` ist Projektregel und hier zusätzlich Pflicht: der Bestand ist LF, ein
CRLF-Katalog würde die Textgleichheitsprüfung der deutschen Zwillinge auf einer anderen
Maschine kippen.

### Die Sichtprobe je Sprache

```bash
# Source: Muster aus scripts/dev/probe_page_login.sh und .github/workflows/integration.yml
# Sprache setzen, Seite holen, Sprache zuruecksetzen.
MSYS_NO_PATHCONV=1 docker exec -u www-data findling-nextcloud \
  php /var/www/html/occ user:setting testuser core lang es
FINDLING_BASE_URL=http://localhost:8090 scripts/dev/probe_page_login.sh testuser "<pass>" factura
# danach: grep auf einen spanischen Satz aus dem Katalog UND auf einen englischen,
# der nicht mehr vorkommen darf.
```

### Der zusammengesetzte Pluralschlüssel, wie er aussehen muss

```json
{
  "translations": {
    "_%n day_::_%n days_": ["%n día", "%n días", "%n días"],
    "_%n hour_::_%n hours_": ["%n hora", "%n horas", "%n horas"]
  },
  "pluralForm": "nplurals=3; plural=n == 1 ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;"
}
```

Form 1 und Form 2 wortgleich, aus dem in Pattern 2 gemessenen Grund.

---

## State of the Art

| Früher | Heute | Seit wann | Bedeutung |
|---|---|---|---|
| PHP wertet die `pluralForm`-Zeichenkette des Katalogs aus | PHP übergibt die mit `|` verbundenen Formen an Symfonys `IdentityTranslator` und wählt über den **Sprachcode**; `pluralForm` wird von `L10N::load()` gar nicht gelesen | in NC 34.0.3 so vorgefunden | Die deklarierte Regel wirkt nur im Browser. Form 1 muss der normale Plural sein |
| App-Skripte brauchen ein eigenes `Util::addTranslations` | `Util::addScript($app, $file)` hängt die Übersetzung automatisch davor, solange der Dateiname nicht `l10n` enthält | `lib/public/Util.php:137-141` | Findling ruft `addTranslations` nirgends und braucht es auch nicht |
| `occ l10n:createjs` als Standardweg | setzt `l10n/<lang>.php` als Quelle voraus, die es seit Jahren nicht mehr gibt | `core/Command/L10n/CreateJs.php` | Für dieses Projekt unbrauchbar, Generator selbst bauen |
| Katalogzahl 174 (Backlog), 199 (Milestone-Research) | **202** | 24.09.2026, Plan 18-10 | Jede ältere Zahl in einem Dokument ist Geschichte, nicht Vorgabe |

**Veraltet und nicht mehr zu verwenden:**
- Die Annahme aus `FEATURES.md`, `LanguageIterator` kürze `pt_BR` auf `pt` und ein Katalog
  bediene beide. Für Kataloge widerlegt.
- Die Erwartung aus `ARCHITECTURE.md` D.3, es/it/nl/pt_PT führten `nplurals=2` und nur
  `pt_BR` weiche ab. Gelesen: es/it/pt_BR/pt_PT führen alle `nplurals=3`, nur `nl` zwei.

---

## Assumptions Log

| # | Behauptung | Abschnitt | Risiko, wenn falsch |
|---|---|---|---|
| A1 | Die Wortlaute entstehen beim Ausführen der Pläne (durch das Modell), nicht über einen externen Dienst; das ist die Lesart von "maschinell" in E-17-5 | Standard Stack, Der maschinelle Prozess | Falls der Owner einen benannten Übersetzungsdienst erwartet, ändert sich die Herkunftsangabe im Vorbehalt, nicht der Bau |
| A2 | `es_EC` und `es_MX` werden nicht ausgeliefert, analog zur `fr_CA`-Entscheidung | Ladepfad, Nebenbefund | Zwei bis vier weitere Dateien, gleiche Mechanik |
| A3 | Der Community-Review findet als GitHub-Issue je Sprache statt | Pattern 5 | Ort des Reviews ändert sich im Vorbehaltstext |
| A4 | Die vier neuen Sprachen kommen **nicht** in die Store-Texte (`<summary lang=...>`) dieser Phase | User Constraints, Deferred | Falls doch: `test_store_metadata.py`, `ALLOWED_LANGUAGES`, `docs/store-listing.md`, beide `info.xml` und die Kurztext-Regel mit Owner-Abnahme kommen dazu; das ist eine eigene Plangruppe |
| A5 | Der Pluralschlüssel-Fix gehört in diese Phase | Open Question 1 | Wenn nein: Erfolgskriterium 1 ist für fünf Sätze nicht erfüllt, und der Fix kostet später sechzehn statt sechs Dateien |
| A6 | Die Nutzersprache der Test-Nextcloud darf für Sichtproben gesetzt und zurückgesetzt werden | Runtime State Inventory | Eine vergessene Rücksetzung verwirrt die nächste Sitzung an der Instanz |

---

## Open Questions

1. **Wird der Pluralschlüssel-Fund in Phase 20 repariert?**
   - Was wir wissen: Der Fund ist gemessen (de und fr antworten bei n != 1 englisch), die
     Ursache ist eindeutig (blanker statt zusammengesetzter Schlüssel), der Bestand der
     Nextcloud belegt das richtige Format 120 zu 0, und wegen G1 muss der Fix alle
     Kataloge gleichzeitig treffen.
   - Was unklar ist: ob der Owner eine Reparatur am **bestehenden** deutschen und
     französischen Katalog innerhalb einer Katalogphase will, oder einen eigenen Befund.
   - Empfehlung: **in dieser Phase, als Welle 0**, vor den zehn neuen Dateien. Begründung:
     Erfolgskriterium 1 verlangt "keine englischen Reste"; nach den zehn neuen Dateien
     kostet derselbe Fix sechzehn statt sechs Dateien; und der Fix ist mechanisch (fünf
     Schlüssel umbenennen, ein Scanner um die `_::_`-Teilung erweitern). Als
     `checkpoint:human-verify` am Anfang der Phase vorlegen, weil er über den Auftrag
     hinausgeht.

2. **Ein `docs/l10n-<sprache>.md` je Sprache oder eine Sammeldatei?**
   - Was wir wissen: Das FR-Muster ist eine Datei je Sprache mit 202 Tabellenzeilen. Vier
     Sprachen (pt mit zwei Spalten) ergeben vier Dateien zu je rund 25 KB.
   - Empfehlung: vier Dateien (`l10n-spanish.md`, `l10n-italian.md`, `l10n-dutch.md`,
     `l10n-portuguese.md` mit pt_PT und pt_BR nebeneinander). Eine Sammeldatei wäre eine
     Tabelle mit sieben Spalten, die niemand liest, und der Review je Sprache braucht
     genau eine Datei zum Verlinken.

3. **Wird `python.yml` um `php/l10n/**` erweitert, oder bekommt der Gleichstand einen
   eigenen Schritt?**
   - Empfehlung: Pfadliste erweitern. Billiger, und die Datei erklärt jeden Eintrag ohnehin
     in Prosa, das Muster ist da.

4. **Kommt der automatisierte Sprachbeweis (Erfolgskriterium 1) in `integration.yml`?**
   - Was wir wissen: Der Job `search-parity` fährt schon den Cookie-Login auf die
     Ergebnisseite, `integration.yml` triggert bereits auf `php/**`, und Phase 19 fasst
     diese Datei nicht an (Phase 19 arbeitet in `deploy-harp.yml`).
   - Empfehlung: ja, ein Schritt je Sprache, der die Nutzersprache setzt, die Seite holt
     und auf einen Satz aus dem Katalog **und** auf die Abwesenheit eines bekannten
     englischen Satzes prüft. Ohne das ist Kriterium 1 nur eine Sichtprobe, die nie wieder
     läuft.

5. **Wortwahl-Entscheide je Sprache, wer entscheidet?**
   - Das FR-Muster hat drei Begriffe als Entscheidung und nicht als Übersetzung markiert
     (`le service`, `passage`, `un processus de traitement`). Für vier Sprachen ohne
     Muttersprachler fällt die Entscheidung beim Bau und wird in der Sprachdoku begründet,
     unter dem Vorbehalt. Kein Tor, aber ein Abschnitt je Datei.

---

## Environment Availability

| Abhängigkeit | Gebraucht für | Verfügbar | Version | Rückfall |
|---|---|---|---|---|
| Test-Nextcloud `findling-nextcloud` | Ladepfad-Beweis, Pluralregeln, Sichtprobe | ja | `nextcloud:34.0.3-apache`, PHP 8.5.9, läuft seit 6 Tagen | zweite Instanz `nc35-nc` (`nextcloud:35.0.0`) für die Obergrenze des Fensters |
| Bind-Mount `php/` -> `custom_apps/findling` | Kataloge sofort live | ja | - | `docker cp`, dann aber kein Live-Bezug zum Repo |
| Docker | alle Sonden | ja | Docker Desktop, WSL2 `docker-desktop` läuft | keiner |
| `occ` in der Instanz | Nutzersprache setzen | ja | meldet "requires upgrade", die benötigten Befehle stehen trotzdem | Sprache über `oc_preferences` direkt |
| `uv` / `pytest` im Backend | Gates lokal fahren | ja (`backend/.venv` vorhanden, ruff-Caches bis 0.16.8) | - | keiner |
| Zweite Instanz `nc35-nc` | Gegenprobe der Pluralregeln auf NC 35 | ja, läuft | `nextcloud:35.0.0-apache-local` | - |
| Externer Übersetzungsdienst | - | nicht gebraucht | - | - |

**Fehlend ohne Rückfall:** keine.
**Empfehlung:** Die Pluralregeln zusätzlich gegen `nc35-nc` gegenlesen, bevor sie als
Konstanten im Gate landen. Das Versionsfenster ist NC 33 bis 35; die Regeln stammen aus
34.0.3. Zwei Zeilen Aufwand, und es schließt die einzige verbliebene Versionsannahme.

---

## Security Domain

### Anwendbare ASVS-Kategorien

| ASVS-Kategorie | Betroffen | Standardkontrolle in dieser Phase |
|---|---|---|
| V2 Authentication | nein | Kataloge tragen keine Authentifizierung |
| V3 Session Management | nein | - |
| V4 Access Control | nein | Kataloge sind für jeden angemeldeten Nutzer lesbar und tragen keine Daten |
| V5 Input Validation / Output Encoding | **ja** | Katalogwerte landen als Text in HTML. Geprüft: kein `print_unescaped`, kein `echo $l->t(...)`, kein `innerHTML`, kein `insertAdjacentHTML` in `php/templates/*.php` und `php/js/*.js` [VERIFIED]. Die Ausgabe läuft über `p()` (escaped) und `textContent` |
| V6 Cryptography | nein (mittelbar) | Die Store-Signatur (`occ integrity:sign-app`) deckt jede neue Datei automatisch ab, keine Dateiliste zu pflegen |
| V7 Error Handling / Logging | **ja** | Siehe Pitfall 3: ein Wortlaut kann eine `ValueError` in `vsprintf` auslösen und die Seite zerlegen |

### Bekannte Bedrohungsmuster für diesen Stack

| Muster | STRIDE | Standardminderung |
|---|---|---|
| Ein Wortlaut mit nacktem `%` zerlegt die Seite | Denial of Service | Scanner: jedes `%` gehört zu einer erkannten Direktive; `%%` für ein literales Prozentzeichen |
| Ein Wortlaut mit `|` ersetzt den Satz durch eine englische Fehlermeldung | Tampering (unbeabsichtigt) | Scanner: `|` in Katalogwerten verboten |
| Ein Wortlaut verliert `%2$s` und nennt die Datei nicht mehr, über die er spricht | Tampering / Verwirrung | `scan_placeholder_parity`, auf alle 16 Dateien ausgedehnt |
| Markup in einem Katalogwert | Cross-Site Scripting | Ausgabe ist durchgängig escaped [VERIFIED]; zusätzlich fängt `scan_prose` keine Tags, also bleibt die Escaping-Disziplin die Kontrolle. Eine neue `print_unescaped`-Stelle wäre der Regressionsweg |
| Zehn neue Dateien im signierten Paket | Supply Chain | `integrity:sign-app` signiert über den Baum, `store-archive.sh` kopiert das Verzeichnis, keine Liste kann veralten |

Nach dieser Phase steht das übliche Security-, Bug- und Performance-Audit an
(Owner-Regel 15.08.2026). Der Prüfschwerpunkt ist hier klein und benannt: die zwei
Scanner oben und die Escaping-Stellen.

---

## Der maschinelle Prozess (E-17-5), konkret für die Pläne

1. **Quelle der Wortlaute:** Die 202 englischen Schlüssel plus die deutsche Spalte aus
   `de.json` als Kontext. Die Zielsprache entsteht beim Ausführen und wird in
   `docs/l10n-<sprache>.md` als Tabelle festgehalten, aus der die zwei Dateien mechanisch
   gegossen werden. Das ist exakt der FR-Weg ("Aus dieser Tabelle entstehen `fr.json` und
   `fr.js` mechanisch, ohne zweite Textrunde").
2. **Maschinelle Prüfungen je Sprache**, Ergebnis in die Doku (Muster: Abschnitt
   "Maschinelle Prüfungen" in `docs/l10n-french.md`):
   Schlüsselmenge vollständig; Platzhalterparität über alle 40 Schlüssel mit Direktiven;
   Pluralschlüssel mit der richtigen Formenzahl; Pluralschlüsselmenge gleich der deutschen;
   U+2019, U+2014, U+2013, U+00A0, U+202F je null; Werte identisch mit dem Quellstring
   gezählt und **einzeln benannt**.
3. **Der datierte Vorbehalt** je Katalog, Wortlaut nach Pattern 5.
4. **Kein Tor.** Die Auslieferung wartet nicht (E-17-5, Option a). Der Owner bekommt die
   Sprachdoku zur Kenntnis, nicht zur Freigabe.
5. **Umfang je Sprache:** 202 Schlüssel, davon 5 Plural (drei Formen für es/it/pt_BR/pt_PT,
   zwei für nl) und 40 mit Direktiven. Fünf Sprachcodes, also fünf Tabellen; `pt_PT` und
   `pt_BR` teilen sich eine Datei mit zwei Spalten, tragen aber zwei echte Wortlaute.

---

## Sources

### Primär (HIGH)

- **Laufende Test-Nextcloud `findling-nextcloud` (`nextcloud:34.0.3-apache`, PHP 8.5.9),
  gemessen 2026-09-24.** Eigene Sonden über `lib/base.php`:
  Sprachcodeliste des Kerns; `findAvailableLanguages` mit und ohne App;
  `languageExists`/`getLanguageCode`/`t()` für `pt`, `pt_PT`, `pt_BR`, `es`, `it`, `nl`,
  `fr`, `de_DE`; `n()` für n = 0, 1, 2, 5, 1000000, 2000000, 1000001 mit blankem und mit
  zusammengesetztem Pluralschlüssel und mit zwei wie drei Formen; `vsprintf` mit nacktem
  und verdoppeltem Prozentzeichen; Plural-Schlüsselformat über alle `apps/*/l10n/de.json`
  (120 zusammengesetzt, 0 blank); `pluralForm` und Formenvergleich in
  `core/l10n/{es,it,nl,pt_BR,pt_PT,fr,de,de_DE}.json`.
- **Serverquelltext in derselben Instanz:** `lib/private/L10N/Factory.php`
  (`get`, `validateLanguage`, `languageExists`, `findLanguage`, `getL10nFilesForApp`),
  `lib/private/L10N/L10N.php` (`n`, `load`, `getIdentityTranslator`),
  `lib/private/L10N/L10NString.php`, `lib/public/Util.php` (`addScript`,
  `addTranslations`), `core/Command/L10n/CreateJs.php`, `dist/core-common.js`
  (gebündeltes `@nextcloud/l10n`).
- **Eigener Baum, gelesen 2026-09-24:** `php/l10n/*.{json,js}` (202 Schlüssel, 5 Plural,
  40 mit Direktiven, LF, keine Pipes), `backend/tests/test_admin_ui_contract.py`
  (Konstanten, fünf Scanner, sieben Gates), `backend/tests/test_measurement_scripts.py`
  (Baumhash-Rezepte und ihre Wurzeln), `docs/measurements/*/skripte/40b-baumhash.py`,
  `scripts/release/store-archive.sh`, `.github/workflows/{python,php,integration,release}.yml`,
  `php/templates/{admin,search}.php`, `php/js/{admin,search}.js`,
  `php/lib/Service/AdminViewService.php`, `php/appinfo/info.xml`, `docs/l10n-french.md`,
  `.gitattributes`.
- **Planungsunterlagen (HIGH):** `.planning/ROADMAP.md` (Phase 20),
  `.planning/REQUIREMENTS.md` (KAT-01, KAT-02), `.planning/STATE.md`,
  `.planning/phases/17-owner-tor-und-analyseketten/17-GRUNDSATZ-ENTSCHEID.md` (E-17-5),
  `.planning/phases/18-schema-marken-und-umbauweg/{18-10-PLAN,18-10-SUMMARY,18-PATTERNS}.md`,
  `.planning/phases/19-frageseite-freischalten/19-0*-PLAN.md` (Kollisionsprüfung),
  `.planning/research/{ARCHITECTURE,FEATURES,PITFALLS,SUMMARY}.md`, `.planning/BACKLOG.md`
  (BL-F02).

### Sekundär (MEDIUM)

- `.planning/research/PITFALLS.md` Abschnitt Kataloge: nennt `nplurals=3` für
  es/it/pt_BR/pt_PT aus dem Serverrepository. **Durch die eigene Messung an der laufenden
  Instanz bestätigt und damit auf HIGH gehoben.**
- `.planning/research/ARCHITECTURE.md` D.2/D.3: zehn Dateien und die Gate-Liste. Zahlen
  (199) und Pluralerwartung (nplurals=2 für es/it/nl/pt_PT) sind überholt, die Struktur
  trägt.

### Tertiär (LOW, zur Validierung markiert)

- `.planning/research/FEATURES.md`: `LanguageIterator` kürze `pt_BR` auf `pt`, ein Katalog
  bediene beide. **Für den Katalogladepfad widerlegt** (Sonde oben). Für
  Benachrichtigungen und Mails unangetastet, dort aber für diese Phase ohne Belang.

---

## Metadata

**Konfidenz im Einzelnen:**

- Dateiorte und Ladepfad: **HIGH**. An der laufenden Instanz gefahren, mit echter
  Probedatei und Gegenprobe über drei Sprachcodes.
- Pluralregeln: **HIGH** für NC 34.0.3 (aus den Kerndateien gelesen), **MEDIUM** für das
  ganze Versionsfenster (33 bis 35); die Gegenprobe gegen `nc35-nc` ist billig und
  empfohlen.
- Pluralschlüssel-Fund und die PHP/JS-Divergenz: **HIGH**. Quelltext gelesen, Verhalten
  gemessen, Gegenprobe über 120 Plural-Einträge der mitgelieferten Apps.
- Gate-Parametrisierung: **HIGH**. Alle sieben Gates gelesen, Änderungsstellen benannt.
- Baumhash- und CI-Befunde: **HIGH**. Rezepte und Pfadlisten gelesen.
- Prozessfragen (Review-Ort, Store-Sprachen, es_MX): **MEDIUM bis LOW**, weil
  Owner-Entscheide, im Assumptions Log geführt.

**Recherchedatum:** 2026-09-24
**Haltbar bis:** rund 30 Tage. Die einzigen beweglichen Teile sind die Schlüsselzahl (bei
jedem Plan neu zählen) und die Nextcloud-Nebenversion der Testinstanz.
