# Phase 11: Haertung und Store-Einreichung v1.1 - Research

**Researched:** 2026-09-10
**Domain:** Release-Engineering (Nextcloud App Store, zwei signierte Haelften), Lokalisierung (FR-Katalog), Upgrade-Kompatibilitaet, Messwerkzeug-Fixe, AWS-Abbau
**Confidence:** HIGH fuer alles, was am Quellcode belegt ist; MEDIUM fuer AWS-Snapshot-Preise; LOW nur bei den ausgewiesenen Open Questions

---

<user_constraints>
## User Constraints (aus 11-CONTEXT.md)

### Locked Decisions

- **D-01:** Die zwei Werkzeug-Fixes (DI-10-01 Lastwerkzeug zaehlt Ausfaelle als Erfolge,
  DI-10-02 Sprachfall-Skript trennt Berechtigung statt Index) werden mit EINER kurzen
  Box-Anfahrt gegen den echten Lastkorpus bewiesen. Kostendeckel der Anfahrt: ~4 h /
  0,50 USD (dem Owner am Checkpoint vorlegen). Der Index auf der Box ist intakt, kein
  Neuaufbau noetig.
- **D-02:** Der Installationstest aus Release-Artefakten auf amd64 und arm64
  (Erfolgskriterium 1) laeuft auf CI-Runnern beider Architekturen (arm64 nativ lief
  schon in Phase 10). KEINE zweite Nextcloud auf der Mess-Box (Lehre 06.1:
  --rm-data-Falle am selben Docker-Dienst).
- **D-03:** Am Ende von Phase 11 (nach Abgabe und Fix-Beweisen): EBS-Snapshot des
  Korpus-Volumes (~1-2 USD/Monat), danach Instanz und Volumes ABBAUEN. Der Abbau
  braucht am Checkpoint eine eigene Owner-Bestaetigung (zerstoerende Handlung).
- **D-04:** v1.1 haelt den bestehenden Index KOMPATIBEL: ein Upgrade von 1.0.x laesst
  Index und Vektorbestand unangetastet. Kein SCHEMA_VERSION-Sprung in dieser Phase.
  Falls die Bestandsaufnahme zeigt, dass Kompatibilitaet nicht haltbar ist, geht die
  Entscheidung mit Beleg zurueck an den Owner (Checkpoint), nicht still in den Plan.
- **D-05:** Sollte je ein Reindex noetig werden, startet er automatisch mit sichtbarem
  Status (Statusseite + Admin-Hinweis), nie still. (Vorratsentscheid; in dieser Phase
  per D-04 nicht vorgesehen.)
- **D-06:** In den v1.1-Store-Texten fuehren die NEUEN Messzahlen (Grundlast 103,2 MB,
  anon-Spitze 1.764,2 MB), die v1.0-Zahlen stehen als datierter Vergleich daneben
  (Muster der 06.1-Korrektur b4a18c5). Drei-Stellen-Regel beachten: README.en.md +
  beide info.xml (Gate haelt sie deckungsgleich), dazu README.fr.md in derselben Runde.
- **D-07:** FR-GATE: Der Owner (franzoesischer Muttersprachler) prueft ALLE
  franzoesischen Zeichenketten (fr.json/fr.js) und den franzoesischen Store-Text als
  eigenen blockierenden Checkpoint VOR der Einreichung.
- **D-08:** Mess-Vorbehalte (Sprachfaelle als Erstmessung, Laufzeit-Untergrenze) stehen
  NICHT im Store-Text, sondern im Messbericht/README; der Store-Text bleibt kurze
  Faktenliste nach der Kurztext-Regel und verweist auf den Bericht.
- **D-09:** Umfang v1.1.0 = Pflicht (FR-Katalog, Store-Texte mit Messzahlen, drei
  Audits, signierte Abgabe, Upgrade-Beweis) PLUS die zwei Werkzeug-Fixes DI-10-01 und
  DI-10-02 mit Box-Beweis. DI-10-04/05 und T-09-29 nur mitnehmen, falls klein und
  risikofrei; sonst dokumentiert weiterreichen.
- **D-10:** Einreichung SO FRUEH WIE MOEGLICH: sobald alle Gates gruen sind und der
  Owner Texte + FR-Gate abgenommen hat, wird eingereicht, ohne auf den ISV-Call
  (14.09.) zu warten. Das Zielfenster 16.-22.09. ist die Obergrenze, kein Startsignal.

### Claude's Discretion

- Reihenfolge und Wellenschnitt der Plaene; Zuschnitt der Haertungstests jenseits des
  Happy Path (Muster 06.1: Fehler-/Edge-/Negativ-Pfade, Fremdinstallation).
- Technische Umsetzung des Schluesselvergleichs fuer zwei Sprachpaare.
- Ob die Box-Anfahrt fuer die Fix-Beweise mit dem Upgrade-Kompatibilitaetsbeweis
  kombiniert wird (solange D-02 respektiert bleibt: keine zweite NC am Mess-Docker).

### Deferred Ideas (AUSSERHALB DES UMFANGS)

- Box-Wiederaufbau-Runbook aus dem EBS-Snapshot (gehoert zur v1.2-Messplanung, nicht
  in diese Phase; der Snapshot selbst ist D-03).
- Versionsfenster-Anhebung (NC 35) und Release-Notes-Feinschliff: nicht besprochen,
  Claude's Discretion im Rahmen des Bestands (Fenster 32-34, max 35).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Beschreibung (aus REQUIREMENTS.md) | Was diese Recherche dafuer liefert |
|----|------------------------------------|------------------------------------|
| REL-01 | v1.1 ist im Nextcloud App Store eingereicht (beide Apps, signiert, Store-Texte nach der Kurztext-Regel, Entwurf vor Einreichung dem Owner gezeigt) | Der exakte gefahrene v1.0.x-Abgabeweg (Abschnitt 3, mit Laufnummern und HTTP-201-Belegen), die drei Stellen, an denen die Version steigt, die Gate-Liste, die vor dem Tag gruen sein muss, und die Text-Mechanik samt der Feststellung, dass der Drei-Stellen-Merker aus DI-10-03 seit 07.09.2026 ueberholt ist (Abschnitt 6) |

Erfolgskriterien der ROADMAP, jeweils mit dem Bestand dagegen gehalten:

| # | Kriterium | Bestand | Luecke |
|---|-----------|---------|--------|
| 1 | Beide Apps gleiche Version, signiert, frische NC installiert sie aus den Release-Artefakten auf amd64 UND arm64 und findet ohne Handgriff Inhalte | `deploy-harp.yml`, Schritte "Store install 1 bis 7", vollstaendig, amd64, ueber drei Serverversionen | arm64-Ast fehlt; die Archive werden lokal gebaut statt vom GitHub-Release geladen |
| 2 | Upgrade 1.0.x auf 1.1.0 laesst den Index unangetastet oder verlangt sichtbar einen Reindex, kein stiller Verlust | Kompatibilitaet ist am Code belegt (Abschnitt 2); Driftmechanik mit sichtbarem Banner existiert (`start_rebuild_on_drift`) | Kein CI-Test faehrt den Upgrade-Pfad. Kein Ratschen-Test, der einen kuenftigen Marken-Sprung rot macht |
| 3 | Security-, Bug- und Performance-Audit erneut gefahren, ab MEDIUM gefixt, LOW dokumentiert entschieden | Muster `docs/audits/2026-09-phase-10/README.md`, Frontmatter-Schema steht | Audit der Phase 11 fehlt; drei geerbte Befunde (DI-07-02, DI-07-03, T-09-29) muessen darin entschieden werden |
| 4 | Store-Texte kurze Faktenlisten, Owner hat Entwurf abgenommen | Kurztext-Regel und Gate stehen | Zahlentausch offen; Konflikt D-06 gegen Kurztext-Regel, siehe Open Question 1 |
| 5 | v1.1 eingereicht, Release-Artefakte im Repo entsprechen dem Eingereichten | `release.yml` baut, signiert und haengt genau die vier Dateien an das Release; `store-submit.yml` reicht genau diese URLs ein | Die vier Dateien im Repo-Wurzelverzeichnis (`findling.tar.gz` usw., Stand 07.09.) sind aelter als der Code, siehe Open Question 5 |
</phase_requirements>

---

## Project Constraints (aus CLAUDE.md)

Diese Direktiven sind bindend und stehen im Rang locked decisions gleich.

| Direktive | Quelle | Folge fuer Phase 11 |
|-----------|--------|---------------------|
| **Kurze Produkttexte (07.09.2026):** Store-Beschreibungen und READMEs sind kurze Faktenlisten. Keine Messgeschichten, **hoechstens eine Zahl im Text**, Details nur als Verweis auf `docs/`. Entwurf vor dem Release dem Owner zeigen | Owner-Regeln | Kollidiert mit D-06 in der woertlichen Lesart, siehe Open Question 1 |
| **Launch-Haertung vor der Store-Abgabe (06.09.2026):** Fehler- und Randpfade, Rechte-Grenzen, Neustart/Upgrade/Migration, kaputte und boesartige Dateien, Ressourcengrenzen, Fremdinstallation auf frischer Nextcloud, Store-Vorgaben, alle Audits erneut. Abgabe startet erst nach Owner-Abnahme der Haertung | Owner-Regeln | Definiert den Haertungsumfang (Abschnitt 5). "Upgrade" ist der einzige Pfad dieser Liste, der in 06.1 noch nicht gefahren wurde |
| **Nach jeder Phase Security-, Bug- und Performance-Audit (15.08.2026),** Befunde ab MEDIUM vor Phasen-Abschluss fixen | Owner-Regeln | Audit-Welle am Ende, Muster `docs/audits/2026-09-phase-10/` |
| Sprache: Code Englisch; README dreisprachig (`README.md` de, `README.en.md` en, `README.fr.md` fr), alle drei werden gepflegt; keine Em-Dashes; echte Umlaute nur in deutscher Prosa, nie in Code | Constraints | FR-Katalog fuegt sich hier ein; `.planning/`-Dokumente dieses Projekts nutzen durchgaengig ae/oe/ue |
| Qualitaetsgates: ruff-Vollregelsatz, pyright basic, vulture, CI-Gates, lokal gruen vor Commit | Constraints | Jede Task-Verifikation braucht `uv run python -m pytest -q && uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run vulture src tests --min-confidence 80` |
| Sicherheitsgrenze: SQLite-ACL-Vorfilter im Container plus finaler PHP-Recheck, keine zweite Grenze | ROADMAP, Phasen-Konvention | Verbietet die naheliegendste Loesung fuer DI-07-03, siehe Abschnitt 5.4 |
| RAM-Budget-Tabelle traegt seit 10-07 die Zeile "Tokenizer und Splitter, 544 MB" | CLAUDE.md, Abschnitt "RAM-Budget auf einer 4-GB-Box" | Beim Zahlentausch mitlesen, damit die Tabelle nicht gegen die neuen Store-Zahlen laeuft |
| GSD-Workflow: keine direkten Repo-Edits ausserhalb eines GSD-Kommandos | GSD Workflow Enforcement | Gilt fuer die Ausfuehrung, nicht fuer diese Recherche |

---

## Summary

Die Phase hat einen sehr guten Ausgangspunkt und genau vier echte Baustellen.

**Der Upgrade-Pfad ist unkritisch, und das ist am Code belegt, nicht vermutet.** Alle
fuenf Marken, die `findling.index.open.expected_versions()` gegen den Bestand haelt,
sind zwischen `v1.0.3` und HEAD unveraendert: `SCHEMA_VERSION = 1` und
`INDEX_VERSION = 1` in `backend/src/findling/config.py` (die Datei hat gegen `v1.0.3`
einen leeren Diff), `ANALYZER_VERSION = 1` in `backend/src/findling/index/analyzer.py`,
`tantivy==0.26.0` unveraendert in `backend/pyproject.toml`, und der `wordlist_hash`
haengt an `wngerman=20161207-15` in `backend/Dockerfile`, die ebenfalls einen leeren
Diff hat. `backend/src/findling/store/repo.py` mit `SCHEMA_VERSION = "2"` fuer
`state.db` ist unveraendert, und `php/lib/Migration/` hat seit `v1.0.3` keine neue
Datei bekommen. **D-04 ist damit haltbar; ein Rueckgang an den Owner ist nicht
erforderlich.** Was fehlt, ist nicht die Kompatibilitaet, sondern ihr Beweis: kein
Workflow faehrt heute einen Upgrade-Pfad, und keine Ratsche macht einen kuenftigen
Marken-Sprung rot.

**Der FR-Katalog ist der groesste Einzelposten der Phase und er ist Uebersetzungsarbeit,
nicht Technik.** `php/l10n/de.json` fuehrt **173 Schluessel**, davon **29 mit
printf-Platzhaltern** und **5 mit Pluralformen**. Vorbereitet sind in
`docs/l10n-french.md` genau **24** davon, also die Ergebnisseite. **149 Zeichenketten
sind noch nicht uebersetzt.** Technisch neu sind drei Dinge: die franzoesische
Pluralregel ist eine andere als die deutsche (`nplurals=2; plural=(n > 1);` gegen
`(n != 1)`), der bestehende Schluesselvergleich vergleicht die deutschen Kataloge als
**Text** und darf das fuer Franzoesisch gerade nicht tun, und an die Stelle der
Textgleichheit gehoert die **Platzhalter-Parität je Schluessel** als Ersatzinvariante.

**Die Store-Mechanik ist gebaut und gefahren, aber der Merker aus DI-10-03 ist
ueberholt.** Die "Drei-Stellen-Regel" (README.en.md plus beide `info.xml`) galt bis zum
07.09.2026. Seither bindet `scan_measured_sentence` in
`backend/tests/test_store_metadata.py` den Messsatz an **README.en.md allein**, weil der
Owner die Store-Beschreibungen auf kurze Faktenlisten reduziert hat. Die beiden
`info.xml` tragen nur noch die qualitative Zusage "hard 2 GB limit (measured)", die
sich durch den Zahlentausch **nicht aendert**. Wer nach dem Drei-Stellen-Gate sucht,
sucht nach etwas, das es nicht mehr gibt.

**Primary recommendation:** Fuenf Wellen. Welle 1 der FR-Katalog mit seinen neuen Gates
(reine Textarbeit, kein Produktionscode, blockierender FR-Checkpoint am Ende). Welle 2
die zwei Werkzeug-Fixe im Code plus die Upgrade-Ratsche, alles lokal gruen. Welle 3 die
EINE Box-Anfahrt mit den beiden Fix-Beweisen unter dem 4-h-Deckel. Welle 4 die
CI-Haertung: arm64-Ast fuer den Store-Install und der Upgrade-Pfad in
`deploy-harp.yml`. Welle 5 Store-Texte, Audit, Versionsbump, Tag, Abgabe, danach
Snapshot und Abbau als eigener Plan mit eigener Freigabe.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| FR-Uebersetzungskatalog (`fr.json`) | PHP-Companion (Server) | , | `$l->t()` laeuft serverseitig im Template, Nextcloud liest die `.json` aus PHP |
| FR-Uebersetzungskatalog (`fr.js`) | Browser | , | `OC.L10N.register` laedt den Katalog im Browser; `search.js`/`admin.js` bauen dort Text |
| Schluesselvergleich / Platzhalter-Gate | CI (Python-Test) | , | Die Gates dieses Projekts leben ausnahmslos in `backend/tests/`, auch wenn sie PHP-Dateien lesen |
| Upgrade-Kompatibilitaet des Index | Backend-Container (Python) | AppAPI | `expected_versions()` und `start_rebuild_on_drift` entscheiden im Container; AppAPI zieht das neue Abbild |
| Upgrade-Kompatibilitaet der Tabellen | PHP-Companion (Migration) | , | `php/lib/Migration/`, unveraendert, also kein Schritt |
| Sichtbarkeit eines Reindex (D-05) | PHP-Companion (Adminseite) | Backend (`/status`) | Banner und Statuszeile lesen den Containerzustand, entscheiden ihn nicht |
| Archivbau und Signatur | CI (`release.yml`) | , | Die einzigen Stellen, an denen die beiden Signierschluessel liegen |
| Store-Registrierung | CI (`store-submit.yml`) | apps.nextcloud.com | Token verlaesst den Secret-Store nie |
| Abbild fuer `image-tag` | CI (`docker.yml`) | ghcr.io | AppAPI zieht `ghcr.io/street1983nk/findling_backend:<image-tag>` bei der Installation |
| Lastmessung / Sprachfaelle | Betriebswerkzeug (`scripts/ops/`, Messskripte) | AWS-Box | Kein Produktionscode, aber unter denselben Gates |
| Box-Lebenszyklus, Snapshot, Abbau | Betriebswerkzeug (`scripts/ops/aws_box.sh`) | AWS EC2/EBS | Ein Ort fuer Kosten- und Nichtexistenz-Rechnung |

---

## 1. FR-Katalog: Bestandsaufnahme und was fehlt

### 1.1 Was heute existiert

**Vier Katalogdateien, alle deutsch:**

```
php/l10n/de.json      20.637 Byte
php/l10n/de.js        19.939 Byte
php/l10n/de_DE.json   20.637 Byte   byteweise identisch mit de.json
php/l10n/de_DE.js     19.939 Byte   byteweise identisch mit de.js
```

Es gibt **keine** `fr.json` und **keine** `fr.js`. [VERIFIED: `ls php/l10n/`]

**Aber Franzoesisch steht bereits im Store-Text.** Beide `info.xml` fuehren
`<name lang="fr">`, `<summary lang="fr">` und `<description lang="fr">`, und
`docs/store-listing.md` haelt alle drei Sprachen nebeneinander. `README.fr.md` existiert
und wird gepflegt. Der Nutzer sieht heute also einen franzoesischen Store-Eintrag und
danach eine englische Oberflaeche. [VERIFIED: `php/appinfo/info.xml`, Zeilen 30-95]

**Die exakte Schluesselmenge, aus der Datei gezaehlt** [VERIFIED: `json.load` ueber
`php/l10n/de.json`]:

| Groesse | Wert |
|---|---:|
| Schluessel in `de.json` | **173** |
| davon mit printf-Platzhaltern (`%s`, `%1$s`, `%n`, ...) | **29** |
| davon mit Pluralformen (Wert ist eine Liste) | **5** |
| `pluralForm` in `de.json` | `nplurals=2; plural=(n != 1);` |
| In `docs/l10n-french.md` vorbereitet | **24** |
| **Noch zu uebersetzen** | **149** |

Die fuenf Pluralschluessel: `%n minute`, `%n hour`, `%n day`, `and %n more`,
`A worker holds this file. The claim runs out in %n second if nothing acknowledges it.`

### 1.2 Der bestehende Schluesselvergleich (Phase 9) und was er tut

Beide Gates stehen in `backend/tests/test_admin_ui_contract.py`.

**`test_the_two_translation_files_carry_the_same_keys`** (ab Zeile 896) vergleicht
`de.json` gegen `de.js`: die JSON wird geparst, aus der `.js` wird zwischen dem ersten
`{` und dem letzten `}` das Objekt herausgeschnitten und geparst, dann werden die
**Schluesselmengen** gleichgesetzt. Zusaetzlich wird ein einzelner geloeschter Eintrag
namentlich als abwesend gefordert (`"Indexing, about %s left"`, IN-02).

**`test_the_german_catalogue_covers_both_german_language_codes`** (ab Zeile 918)
vergleicht die vier deutschen Dateien und tut dabei zwei verschiedene Dinge:

1. `de_DE.json` gegen `de.json` und `de_DE.js` gegen `de.js` als **vollstaendige
   Textgleichheit** (`twin.read_text() == language.read_text()`), begruendet damit, dass
   jeder Satz in der Sie-Form geschrieben ist und ein zweiter, informeller Katalog eine
   Textrunde waere, die niemand bestellt hat.
2. Die vier Schluesselmengen als `frozenset` in ein Set gelegt, dessen Laenge 1 sein
   muss, und **`assert len(keys_of["de.json"]) == 173`** als harte Zahl.

### 1.3 Was die Erweiterung auf zwei Sprachpaare braucht

`docs/l10n-french.md`, Abschnitt "Bedingung, unter der der franzoesische Katalog kommt",
sagt es fuer die Schluessel bereits ausdruecklich: *"Anders als bei Deutsch ist es dort
**keine** Gleichheit der Dateien."* Franzoesisch kennt die Du-Sie-Teilung nicht, also
gibt es kein `fr_CA` und keinen Zwilling.

Damit ist die Umsetzung fuer die Discretion-Frage entschieden: **das zweite Sprachpaar
ist `fr.json` gegen `fr.js`, nicht `fr` gegen `fr_XX`.** Der Vergleich ist
Schluesselgleichheit, und an die Stelle der Textgleichheit tritt eine Invariante, die
Franzoesisch tatsaechlich halten kann.

**Empfohlene Gate-Struktur** (vier Zusicherungen, alle in
`backend/tests/test_admin_ui_contract.py`, damit der Ort einer ist):

| Gate | Was es prueft | Warum es rot werden kann |
|------|---------------|--------------------------|
| G1 Schluesselgleichheit ueber alle sechs Dateien | `de.json`, `de.js`, `de_DE.json`, `de_DE.js`, `fr.json`, `fr.js` haben dieselbe Schluesselmenge | Ein Schluessel, der nur in einer Sprache angelegt wird, ist eine halbe Oberflaeche |
| G2 Vollstaendigkeit | Kein FR-Wert ist leer und keiner ist mit dem englischen Schluessel identisch, ausser bei den benannten Ausnahmen | Ein Katalog mit 24 von 173 ist genau das, was `docs/l10n-french.md` verhindern will |
| G3 **Platzhalter-Parität** | Fuer jeden Schluessel ist die Multimenge der `%`-Direktiven im FR-Wert dieselbe wie im Schluessel | Der Ersatz fuer die Textgleichheit. Ein verlorenes `%2$s` ist ein `vsprintf`, das die Datei nicht mehr nennt. Heute: 29 Schluessel betroffen, 0 Abweichungen im Deutschen |
| G4 Pluralform | `fr.json` traegt `"pluralForm": "nplurals=2; plural=(n > 1);"`, `fr.js` denselben String als vierten Parameter von `OC.L10N.register`, und die 5 Pluralschluessel tragen genau 2 Formen | Die franzoesische Regel unterscheidet sich von der deutschen. Wer die deutsche kopiert, bekommt bei n=0 die falsche Form |

**Ausnahmenliste fuer G2, aus `docs/l10n-french.md` und aus dem Bestand:** `Findling`
ist in allen drei Sprachen gleich und ist deshalb ueberhaupt kein
Uebersetzungsschluessel (die Datei erklaert genau das als Grund fuer 24 statt 25).
Weitere Ausnahmen sind moeglich (Eigennamen, `%s`-only-Zeilen) und gehoeren als benannte
Liste in den Test, nicht als Toleranzschwelle.

**Die harte Zahl 173** in `test_the_german_catalogue_covers_both_german_language_codes`
muss beim Anlegen von `fr.json` nicht steigen: der FR-Katalog fuegt keine Schluessel
hinzu, er uebersetzt die vorhandenen. Wer die Zahl trotzdem anfasst, hat einen
Schluessel erfunden.

**Kein Dash-Gate ueber `php/l10n/`.** `test_no_file_of_the_page_carries_a_dash_or_an_emoji`
liest sechs Dateien der beiden Seiten (Template, Stylesheet, Skript, je Seite), keine
Katalogdatei. Franzoesische Typographie bringt Guillemets (« ») und Apostrophe mit, die
harmlos sind, aber der Gedankenstrich ist es nicht: er ist in franzoesischer
Zeitungstypographie gebraeuchlich und wuerde sich ohne Gate einschleichen. **Empfehlung:
das Dash-/Emoji-Gate auf die sechs Katalogdateien ausdehnen.** Kostet zwei Zeilen und
schliesst genau die Luecke, die die Sprache mitbringt.

### 1.4 Die 24 vorbereiteten Wortlaute, geprueft

Die Tabelle in `docs/l10n-french.md` ist verwendbar wie sie ist. Geprueft wurde:

- **Platzhalter:** Zeile 5 `Results for "%s"` -> `Résultats pour « %s »`, Zeile 7
  `%1$s in %2$s` -> `%1$s dans %2$s`, Zeile 13 `Page %s` -> `Page %s`. Alle drei tragen
  dieselben Direktiven in derselben Zahl. G3 waere gruen.
- **Echte Akzente und Guillemets:** vorhanden (`Résultats`, `numérisés`,
  `« %s »`). Punkt 4 der Bedingungsliste ist erfuellt.
- **Kein Gedankenstrich** in den 24 Wortlauten. [VERIFIED: Sichtpruefung der Tabelle]
- **Apostrophe** sind ASCII (`D'autres`, `l'intérieur`, `n'est`), nicht das typographische
  U+2019. Das ist konsistent mit `README.fr.md` und mit den franzoesischen
  Store-Texten in `info.xml` (`d'elles-même`, `l'utilisateur`). **Empfehlung: dabei
  bleiben**, ein gemischter Apostroph-Bestand ist eine Diff-Falle.
- **Der 25. Eintrag** (`Findling` als Navigationsname und Seitenname) ist korrekt als
  Nicht-Schluessel begruendet. `php/appinfo/info.xml` traegt ihn im
  `<navigations>`-Block als festen Text.

**Was die 24 nicht abdecken:** die Verwaltungsseite. Die fuenf Pluralschluessel und der
grosse Teil der 29 Platzhalter-Schluessel liegen dort (`%n minute`, `%1$s of %2$s
indexable files are searchable`, die Verdikt-Labels und ihre Abhilfen aus
`test_every_reason_of_the_closed_list_has_a_label_and_a_remedy`). Das ist der
eigentliche Uebersetzungsaufwand.

### 1.5 Reihenfolge, die das FR-Gate (D-07) billig macht

Der Owner soll **alle** franzoesischen Zeichenketten lesen. 173 Zeilen in einer
XML-losen Ansicht sind zumutbar, 173 Zeilen als Diff ueber zwei JSON-Dateien plus zwei
JS-Dateien sind es nicht. **Empfehlung:** die Uebersetzung entsteht zuerst als eine
dreispaltige Tabelle (Schluessel / DE / FR) in `docs/l10n-french.md`, der Owner liest
diese eine Tabelle, und erst danach werden `fr.json` und `fr.js` mechanisch daraus
erzeugt. Das ist genau das Muster, das `docs/store-listing.md` fuer die Store-Texte
schon fuehrt, und es macht das FR-Gate zu einem Lesevorgang statt zu vier.

---

## 2. Upgrade-Pfad 1.0.x auf 1.1.0 (D-04)

### 2.1 Der Befund in einem Satz

**Nichts, was den Index oder den Vektorbestand identifiziert, hat sich seit `v1.0.3`
geaendert. D-04 ist haltbar.**

### 2.2 Die Belege, Marke fuer Marke

`backend/src/findling/index/open.py::expected_versions()` (Zeile 123) definiert die
fuenf Marken, gegen die ein bestehender Index geprueft wird. Der Vergleich selbst liegt
in `findling.store.repo.Store.version_mismatch`, und eine fehlende Marke zaehlt dort als
Unterschied.

| Marke | Quelle | Wert | Diff `v1.0.3..HEAD` |
|-------|--------|------|---------------------|
| `schema_version` | `backend/src/findling/config.py:41` `SCHEMA_VERSION = 1` | `1` | **leer**, die ganze Datei hat keinen Diff |
| `index_version` (lokale Generation) | `backend/src/findling/config.py:46` `INDEX_VERSION = 1` | `1` | **leer** |
| `analyzer_version` | `backend/src/findling/index/analyzer.py:73` `ANALYZER_VERSION = 1` | `1` | **leer**, `analyzer.py` steht nicht im Diffstat |
| `wordlist_hash` | `backend/src/findling/index/wordlist.py`, gebaut aus `/usr/share/dict/ngerman` | haengt an `wngerman=20161207-15` | `wordlist.py` +10 Zeilen, **ausschliesslich Docstring** (Messnotiz zu 21 statt 16 Komposita). `backend/Dockerfile` hat **keinen Diff**, das Paket ist exakt gepinnt |
| `tantivy_version` | `backend/pyproject.toml`, `tantivy==0.26.0` | `0.26.0` | unveraendert; der `pyproject.toml`-Diff betrifft nur `pypdf 6.16.1->6.16.2`, `striprtf 0.0.32->0.0.33`, `lxml 6.1.1->6.1.3`, `ruff 0.16.4->0.16.6` |

[VERIFIED: `git diff v1.0.3..HEAD -- backend/src/findling/config.py` liefert leere
Ausgabe; `git diff --stat v1.0.3..HEAD -- backend/src/findling/index/ backend/src/findling/store/ backend/src/findling/embed/ backend/src/findling/config.py` nennt nur
`embed/engine.py`, `embed/model.py` und `index/wordlist.py`]

**Weitere Bestaende, die haetten brechen koennen und nicht brechen:**

- `backend/src/findling/store/repo.py` mit `SCHEMA_VERSION: Final = "2"` und
  `STORE_SCHEMA_MARK = "store_schema_version"` fuer `state.db`: **kein Diff**.
- `php/lib/Migration/`: fuenf Dateien, alle `Version001000Date2026*`, **keine neue seit
  `v1.0.3`**. Die `dirty`-Spalte, die der geaenderte `QueueMapper` neu abfragt, wird
  bereits von `Version001000Date20260901000000.php` angelegt. [VERIFIED:
  `grep -l dirty php/lib/Migration/*.php`]
- `backend/src/findling/embed/model.py` (+50): zwei neue Properties
  (`artifacts_absent`, `load_cooling_down`) und ein Delegat `artifacts_present`. Kein
  Modellwechsel, keine Dimensionsaenderung, `fastembed` in `pyproject.toml`
  unveraendert. `vectors.db` bleibt gueltig.
- `php/lib/Db/QueueMapper.php` (+79): `requeueAs` behandelt schmutzige Zeilen anders
  (sie werden zurueckgegeben statt auf die nachlaufende Spur geschoben). Reine
  Verhaltensaenderung ueber eine bestehende Spalte, keine Schemaaenderung.

### 2.3 Was sich beim Upgrade tatsaechlich bewegt, und wo es klemmen kann

Drei Dinge aendern sich, und alle drei sind Auslieferungs- und nicht Datenfragen:

1. **Das Abbild.** `backend/appinfo/info.xml:230` traegt `<image-tag>1.0.3</image-tag>`.
   Fuer v1.1.0 muss `docker.yml` das Abbild unter dem Tag `1.1.0` fuer beide
   Architekturen nach `ghcr.io/street1983nk/findling_backend` geschoben haben, **bevor**
   die Store-Abgabe laeuft, sonst schlaegt bei jedem Nutzer der Pull fehl. Der
   Tag-Trigger von `docker.yml` erledigt das automatisch, ist aber pfadgefiltert auf
   `backend/**`. Der Releasecommit beruehrt `backend/appinfo/info.xml`, also greift der
   Filter. Trotzdem: **das Vorhandensein des Tags in ghcr ist vor der Abgabe zu pruefen**,
   nicht anzunehmen.
2. **Der Navigationseintrag.** `php/appinfo/info.xml` hat gegen `v1.0.3` genau eine
   funktionale Aenderung: einen `<navigations>`-Block am Dateiende. Der Kommentar
   daneben nennt die Upgrade-Eigenheit selbst: *"An instance that already has this app
   installed sees the entry only after an app update. Nextcloud reads the navigation out
   of the INSTALLED appinfo/info.xml in AppManager::loadApp()."* Das ist ein
   Pruefpunkt des Upgrade-Tests, kein Risiko.
3. **Die ExApp-Registrierung.** Ein Upgrade der Container-Haelfte laeuft ueber
   `app_api:app:unregister` **ohne** `--rm-data` und eine erneute Registrierung mit dem
   neuen `image-tag`. Genau diese Zusage ist heute schon getestet:
   `deploy-harp.yml`, "Store uninstall 1, an unregister without the flag keeps the
   volume" und "Store uninstall 2, a second registration picks up the volume it left".
   **Der Upgrade-Beweis ist eine Rekombination vorhandener Schritte, kein Neubau.**
   Nachzuziehen ist danach die harte Grenze: `aws_box.sh start` nennt es ausdruecklich,
   *"after every app_api:app:register the hard memory limit is gone"*.

### 2.4 Wie man Upgrade-Kompatibilitaet in CI prueft

**Empfehlung: zwei Zusicherungen auf zwei Ebenen, beide klein.**

**(a) Die Ratsche, rein lokal, kostet Sekunden.** Ein Test in `backend/tests/`, der
`expected_versions()` mit einem festen Wortlisten-Digest aufruft und die fuenf Werte
gegen eine eingecheckte Goldtabelle des Standes `v1.0.3` haelt. Faellt eine Marke, wird
der Test rot mit dem Satz "ein Upgrade von 1.0.x wuerde jetzt einen Reindex ausloesen,
das ist eine Owner-Entscheidung (D-04)". Das ist das billigste Werkzeug, das die
D-04-Zusage ueber die Phase hinaus traegt, und es ist genau die Ratschen-Bauform, die
dieses Projekt schon fuer die RSS-Grundlast fuehrt.

**(b) Der Ende-zu-Ende-Beweis in `deploy-harp.yml`**, als eigener Block hinter den
Store-Install-Schritten:

1. Beide Haelften **aus den GitHub-Release-Assets von `v1.0.3`** installieren
   (`https://github.com/street1983nk/nextcloud-search/releases/download/v1.0.3/findling.tar.gz`
   und `findling_backend.tar.gz`). Das ist derselbe Weg, den `store-submit.yml` dem
   Store nennt, also der Bestand, den ein Nutzer wirklich hat.
2. Testnutzer, Korpus, `occ files:scan`, warten bis der Arbeitsvorrat leer ist, dann
   festhalten: Trefferzahl fuer drei feste Begriffe, `occ findling:index --status` mit
   indexiert/uebersprungen/fehlgeschlagen, und die fuenf Marken aus dem
   Index-Metadatensatz (ueber `findling.tools.index_status`, das sie unter
   `schemaVersion` usw. ausgibt).
3. Upgrade fahren: die Companion-Dateien der v1.1.0-Archive ueber `apps/findling`
   auspacken und `occ upgrade` laufen lassen; die Container-Haelfte per
   `app_api:app:unregister` (ohne `--rm-data`) und erneuter Registrierung mit dem neuen
   `image-tag` auf das neue Abbild heben.
4. Zusichern: **dieselben Trefferzahlen**, **dieselben fuenf Marken**, **dieselbe
   Dokumentzahl**, **kein Reindex-Banner** und **keine Zeile im Containerprotokoll, die
   `start_rebuild_on_drift` meldet**. Zusaetzlich: der Navigationseintrag ist jetzt da,
   er war vorher nicht da.

**Warum das der richtige Zuschnitt ist:** Erfolgskriterium 2 verlangt "unangetastet oder
sichtbar", und die Sichtbarkeit ist bereits gebaut. `start_rebuild_on_drift` in
`index/open.py` hebt die lokale Generation und schreibt den Fingerabdruck der Marken
daneben, damit ein Neustart mitten im Wiederaufbau nicht von vorn anfaengt. Der
Reindex-Banner nennt `occ findling:index --restart` als Abhilfe. **D-05 ist also nicht
nur Vorrat, sondern bereits Bestand** und muss nur im Upgrade-Test als der nicht
gefahrene Zweig benannt werden.

**Kostenschaetzung:** Der Block verdoppelt im schlimmsten Fall die Laufzeit eines
`deploy-harp`-Astes. Der Ast misst heute 3 bis 5 Minuten plus die Store-Install-Strecke;
`timeout-minutes` steht auf 45. **Empfehlung: den Upgrade-Block nur im Ast `stable34`
fahren**, nicht in allen dreien. Ein Upgrade-Pfad ist eine Aussage ueber die App, nicht
ueber die Serverversion.

---

## 3. Release-Pipeline: wie v1.0.x lief und was v1.1.0 braucht

### 3.1 Der gefahrene Weg, aus den Laeufen belegt

**Vier Tags, vier Releases, fuenf Store-Submissions, alle erfolgreich.** [VERIFIED:
`gh release list`, `gh run list --workflow=store-submit.yml`]

| Tag | Release erstellt | Store-Submission |
|-----|------------------|------------------|
| v1.0.0 | 2026-09-07T15:58:32Z | Lauf 34143894059, 2026-09-07T16:34:28Z |
| v1.0.1 | 2026-09-07T17:13:24Z | Lauf 34146823898 |
| v1.0.2 | 2026-09-07T19:14:47Z | Lauf 34154892880 |
| v1.0.3 | 2026-09-08T00:14:08Z | Laeufe 34172340601 und **34172689400** |

Der Log des letzten Laufs, woertlich:

```
release findling v1.0.3: HTTP 201
findling v1.0.3 is in the store
release findling_backend v1.0.3: HTTP 201
findling_backend v1.0.3 is in the store
```

Die Store-API bestaetigt es von aussen: `apps.nextcloud.com/api/v1/apps.json?version=34.0.0`
listet fuer `findling` die Releases `1.0.3, 1.0.2, 1.0.1, 1.0.0`. [VERIFIED: curl gegen
die Store-API am 2026-09-10]

**Jedes Release traegt genau vier Assets:** `findling.tar.gz`, `findling.tar.gz.sig`,
`findling_backend.tar.gz`, `findling_backend.tar.gz.sig`. [VERIFIED: `gh release view v1.0.3`]

### 3.2 Die Kette, Glied fuer Glied

**Ausloeser:** ein Tag `v[0-9]+.[0-9]+.[0-9]+` auf `main`.

**`release.yml`** (nicht pfadgefiltert, ausdruecklich):
1. Prueft `GITHUB_REPOSITORY == street1983nk/nextcloud-search` und dass das Ereignis ein
   Tag-Push oder ein Dispatch ist. Ein `pull_request`-Trigger existiert nicht, und diese
   Abwesenheit ist die Hauptverteidigung der Schluessel.
2. **Version-Gate:** Tag, `php/appinfo/info.xml` `<version>` und
   `backend/appinfo/info.xml` `<version>` muessen uebereinstimmen.
3. Holt Store-Transform und Schema von `nextcloud/appstore`, gepinnt auf
   `APPSTORE_SHA = eda850ba61407c6e4da3e23316614c6126406652`.
4. Holt beide Zertifikate aus `nextcloud/app-certificate-requests` und prueft
   Subject (`RFC2253`) und den SHA-256 ueber den **DER** des Public Key gegen die zwei
   Fingerabdruecke aus `docs/certificates.md`.
5. Installiert eine Wegwerf-Nextcloud (`SERVER_VERSION = stable34`), nur damit
   `occ integrity:sign-app` seine Dienste findet.
6. **Companion:** staging (`scripts/release/store-archive.sh stage-companion`),
   `xsltproc`+`xmllint` gegen die transformierte `info.xml`, 512-KB-Grenze,
   `integrity:sign-app` (Codesignatur **in** das Verzeichnis), packen,
   20-MB-Grenze, Release-Signatur **ueber** das Tarball, und die Signatur wird gegen das
   Zertifikat verifiziert statt geglaubt.
7. **Backend:** dasselbe **ohne** `integrity:sign-app` (die Haelfte liefert keinen PHP-Code
   in die Instanz, es gaebe nichts zu hashen), mit Release-Signatur.
8. `assert-contents` ueber beide Archive.
9. `gh release create` mit den vier Dateien.

**Die Reihenfolge ist der Kern und steht als Kommentar im Workflow:** stage, Codesignatur,
packen, Release-Signatur. Ein Vertauschen der letzten beiden produziert "Invalid
signature" vom Store ohne Hinweis darauf, welche der zwei Signaturen falsch war. Und:
**das Archiv wird nie zweimal gebaut**, weil ein `tar.gz` nicht byte-reproduzierbar ist.

**`store-submit.yml`** (nur `workflow_dispatch`):
- Eingaben: `tag`, `register` (nur bei der Erstregistrierung), `direct_download`/
  `direct_signature` (Direktmodus fuer die Schwester-App).
- Fuer jede Haelfte: die `.sig` vom Release-Asset laden, `{download, signature}` als
  JSON an `POST https://apps.nextcloud.com/api/v1/apps/releases` mit
  `Authorization: Token ${APPSTORE_TOKEN}`.
- Akzeptiert **200 und 201**, alles andere ist ein Fehlschlag. Gemessen kam 201.
- Schluesseldateien werden mit `if: always()` geloescht.

**Secrets:** `APPSTORE_TOKEN`, `APP_PRIVATE_KEY`, `BACKEND_PRIVATE_KEY`. Alle drei
verlassen den GitHub-Secret-Store nicht. `tr -d '\r'` am Schluessel ist Pflicht und mit
einer Laufnummer begruendet (33895245084).

### 3.3 Was fuer v1.1.0 zu tun ist

| # | Handlung | Ort | Falle |
|---|----------|-----|-------|
| 1 | `<version>1.1.0</version>` | `php/appinfo/info.xml:113` | , |
| 2 | `<version>1.1.0</version>` | `backend/appinfo/info.xml:136` | , |
| 3 | `<image-tag>1.1.0</image-tag>` | `backend/appinfo/info.xml:230` | Wird von `test_lockstep_versions.py` **und** von `docker.yml` **und** von `release.yml` geprueft. Drei Gates, ein Wert |
| 4 | Alle drei in **einem** Commit | , | Ein Bump auf einer Seite allein macht `docker.yml` rot, bevor es baut |
| 5 | `docker.yml` hat das Abbild `1.1.0` fuer amd64 **und** arm64 in ghcr | ghcr.io | Der Tag-Push loest es aus; **vor der Abgabe pruefen, nicht annehmen** |
| 6 | Tag `v1.1.0` auf `main` | git | `release.yml` und `docker.yml` haengen beide daran |
| 7 | GitHub-Release mit vier Assets entsteht | `release.yml` | , |
| 8 | `store-submit.yml` mit `tag=v1.1.0`, `register=false` | manuell | `register` bleibt aus, die Ids sind seit 07.09. registriert |
| 9 | Beide Antworten sind 201, im Log belegt | , | Erfolgskriterium 5 |

**Kriterium 5 ("Release-Artefakte im Repo entsprechen dem Eingereichten") ist mit dieser
Kette automatisch erfuellt**, weil `store-submit.yml` genau die URL des Release-Assets
uebergibt, das `release.yml` signiert und hochgeladen hat. Es gibt keinen zweiten Bau.
Zu klaeren bleiben nur die vier Dateien im Repo-Wurzelverzeichnis, siehe Open Question 5.

### 3.4 Gates, die vor dem Tag gruen sein muessen

Acht Workflows, die relevanten fuer die Abgabe:

| Workflow | Was es fuer die Abgabe beweist | Ausloeser fuer den Releasecommit |
|----------|-------------------------------|----------------------------------|
| `php.yml` (`lint`, `app-metadata`, `phpunit`) | Store-Metadaten-Gates, `APPSTORE_SHA`-Gleichheit mit `release.yml`, PHPUnit | Pfadfilter auf `php/**`, `.github/workflows/release.yml` |
| `python.yml` (`gates`, `extract-bench-arm`) | ruff, pyright, vulture, pytest inklusive aller Textgates | `backend/**` |
| `docker.yml` | Abbild fuer beide Architekturen, Smoke-Test, Versions-Gate | `backend/**`, Tags |
| `integration.yml` (`walking-skeleton`, `readonly-gate`, `index-search-e2e`) | die zehn deutschen Sprachfaelle auf amd64 gegen eine frische Instanz mit eigenem Index, amd64-Kaltstartzahl | `backend/**`, `php/**` |
| `deploy-harp.yml` | Fremdinstallation aus den Store-Archiven, Drift, sechs Deinstallations-Zusagen, je zweimal | `backend/**`, `php/**`, `scripts/release/**` |
| `resilience.yml` | Kill/Resume, DI-05-36 | `backend/**` |
| `release.yml` | die Abgabe selbst | Tag |
| `measure.yml` | Wave-0-Messungen, nur `workflow_dispatch` | , |

---

## 4. Werkzeug-Fixe und Box-Beweis (D-01)

### 4.1 Pfadkorrektur, bevor irgendwer sucht

11-CONTEXT.md nennt `backend/tests/tools/search_load.py`. **Diese Datei existiert nicht.**
Das Lastwerkzeug liegt unter **`scripts/ops/search_load.py`** (437 Zeilen). Es wird von
`backend/tests/test_ops_scripts.py` als `SEARCH_LOAD = OPS_DIR / "search_load.py"`
bewacht. [VERIFIED: `find . -name search_load.py`]

### 4.2 DI-10-01: das Lastwerkzeug zaehlt Abbrueche als Erfolge

**Die Stelle, exakt.** `_one_search` (ab Zeile 178) liest die OCS-Antwort und tut:

```python
entries = payload.get("ocs", {}).get("data", {}).get("entries")
if not isinstance(entries, list):
    return (elapsed_ms, 0, "MalformedAnswer")
return (elapsed_ms, len(entries), None)
```

Eine leere Liste ist eine Liste. Bricht der Containeraufruf ab, antwortet die OCS-Route
mit **HTTP 200** und einer Ergebnisgruppe ohne Containerteil, `entries` ist `[]`,
`failure` ist `None`, und der Bericht schreibt `"failures": 0`.

**Der Fingerabdruck ist bereits im Bericht:** `hits_total` steht heute schon im Report,
aber nur als Summe ueber die ganze Stufe und ohne Bezug zur Anfragezahl. Die Tabelle in
`00-kernaussage.md` (5,40 / 5,40 / 5,25 / 4,81 / **4,16** Treffer je Anfrage) ist von
Hand ausgerechnet.

**Die zwei Wege aus `deferred-items.md`, bewertet:**

| Weg | Was er tut | Vorteil | Nachteil |
|-----|-----------|---------|----------|
| A: Ergebnisgruppe ohne Containerteil = Fehlschlag | `entries == []` fuehrt zu `failure="EmptyResultGroup"` | Der Zaehler stimmt sofort, `failures` ist wieder das, was das Wort sagt | Eine echte Nullsuche waere ab jetzt ein Fehlschlag. Das Werkzeug hat 10 feste `TERMS`; auf einer fremden Instanz treffen die nicht zwangslaeufig, und dann meldet das Werkzeug 100 Prozent Fehlschlaege fuer eine kerngesunde Instanz |
| B: Trefferzahl je Stufe als eigene Kennzahl | `hits_per_request` in den Report | Kein Risiko, keine Umdeutung einer bestehenden Zahl, der Fingerabdruck wird ohne Protokoll lesbar | Zaehlt den Ausfall weiter als Erfolg. Der Befund lautet aber woertlich *"Ein Messwerkzeug, das einen Ausfall als Erfolg zaehlt, ist der unangenehmere Befund von beiden"* |

**Empfehlung: beide, in einer Aenderung, mit einem Schalter, der die Umdeutung
ausdruecklich macht.**

- Neuer Parameter `--min-hits N`, Vorgabe **1**. Eine Antwort mit weniger Treffern wird
  zu `failure = "EmptyResultGroup"`. `--min-hits 0` stellt das alte Verhalten her und
  ist der Ausweg fuer eine Instanz, deren Bestand die `TERMS` nicht traegt.
- `hits_per_request` (auf eine Nachkommastelle gerundet) immer im Report, neben
  `hits_total`.
- Der Modulkopf bekommt einen Absatz nach dem Muster der uebrigen: was die Zahl vorher
  bedeutete, warum sie falsch war, mit der Laufnummer und der Rohdatei.

**Warum ein Vorgabewert von 1 und nicht 0:** Das Werkzeug misst Suchlast gegen einen
Bestand, in dem seine zehn Begriffe stehen. Eine Antwort ohne Treffer ist dort kein
Messergebnis, sondern ein Loch. Der Vorgabewert soll die Wahrheit sagen, und der Schalter
soll die Ausnahme benennen.

**Gates, die mitziehen:** `backend/tests/test_ops_scripts.py` fuehrt ab Zeile 472 eine
Reihe `test_the_load_tool_*`. Neue Zusicherungen gehoeren dorthin, insbesondere: ein
gestellter Beispielreport mit `entries == []` wird als Fehlschlag gezaehlt, und mit
`--min-hits 0` nicht.

### 4.3 DI-10-02: das Sprachfall-Skript trennt die Berechtigung, nicht den Index

**Der Befund, praezise.** `98-sprachfaelle.sh` fuehrt ein eigenes Konto ein
(`KONTO=sprachfall`, ausdruecklich nicht `lasttest`), weil der Lastkorpus dieselben
Woerter traegt. Ein eigenes Konto trennt aber die **Berechtigung**, nicht den **Index**:
der Vorfilter rankt ueber den ganzen Index, der Recheck filtert erst danach. Bei 52.111
Fremddokumenten mit denselben Tokens bleibt nichts uebrig. Fuer `Genehmigung`, `Frist`
und `Vertrag` kommt unter den ersten 2.000 Kandidaten keine Datei des fragenden Kontos
vor, fuer `Bescheid` steht sie auf Rang 1.925.

**Die drei denkbaren Wege, alle bewertet:**

| Weg | Was er kostet | Urteil |
|-----|---------------|--------|
| **B1** Begriffe waehlen, die im Lastkorpus nachweislich selten sind | Die zehn Faelle haengen an konkreten Dateien des 39-Datei-Referenzkorpus (`09-bescheid.pdf`, `10-kuendigung.docx`, ...). Andere Begriffe hiessen neue Korpusdateien, also Aenderungen an `testdata/corpus`, an `backend/tests/test_corpus_terms.py` und an den zehn Faellen in `integration.yml` | **Nicht klein.** Ein Korpuswechsel mitten in der Haertung ist genau die Art Aenderung, die Vergleichbarkeit kostet |
| **B2** Eigener Index auf der Box | Ohne zweite Nextcloud (D-02 verbietet sie) bliebe nur ein zweiter Container mit eigenem Datenverzeichnis, gefahren an AppAPI vorbei. Dann laufen die Faelle aber gegen die Container-Route statt ueber OCS, und der finale PHP-Recheck faellt aus der Messung | **Verworfen.** Die zehn Faelle sind Aussagen ueber den Nutzerweg. Ohne OCS messen sie etwas anderes |
| **B3** Das Skript deckt seine eigene Grenze auf, und der eigene Index bleibt dort, wo er schon ist: in CI | Eine Vorpruefung im Skript plus eine Bindung an den CI-Beleg | **Empfohlen** |

**B3 im Einzelnen, und warum es der ehrliche Fix ist:**

1. **Vorpruefung Fremdbestand.** Vor den zehn Faellen fragt das Skript jeden der zehn
   Begriffe **als das Lasttest-Konto** ueber dieselbe OCS-Route und schreibt die
   Trefferzahl mit. Ein Begriff mit vielen Fremdtreffern kann seinen Fall nicht tragen.
2. **Dreiwertiges Urteil statt zweiwertigem.** Der Fall wird `GRUEN`, `ROT` oder
   **`NICHT MESSBAR (Fremdbestand N Treffer)`**. Die Bilanzzeile wird
   `sprachfaelle bestanden 6 von 10, davon 4 nicht messbar` statt `6 von 10`. Damit
   verschwindet genau der Fehler, den DI-10-02 benennt: das Skript meldet keinen
   Sprachdefekt mehr, wo keiner ist. Das dreiwertige Lesen ist im Repository bereits
   etabliert, `99b-runden.sh` tut es fuer den Driftfall.
3. **Der eigene Index existiert und wird benannt.** `integration.yml`, Job
   `index-search-e2e`, faehrt dieselben zehn Faelle auf amd64 gegen eine frische Instanz
   **ohne Fremdbestand**, und sie sind gruen (Lauf 34339346666, Commit 0dd007d3, in
   MESS-02 zitiert). Das **ist** die Messung mit eigenem Index. Was fehlt, ist die
   Bindung: das Skript schrieb am 10.09. `ci-beleg: der letzte gruene
   integration.yml-Lauf ist unbekannt`, weil `CI_LAUF` nicht gesetzt war. Der Fix ist,
   die Laufnummer zur Pflichteingabe zu machen und die Zeile `unbekannt` zum
   Abbruchgrund, nicht zur Notiz.

**Wichtige Nebenbedingung: das gefahrene Skript wird nicht angefasst.** Der Kopf von
`98-sprachfaelle.sh` sagt selbst, dass die Fassung unter `skripte/` die gefahrene ist
(*"Beide Fassungen unter skripte/ sind die gefahrenen, mit einem Satz im Kopf"*, Punkt 9
der Liste "Was dieser Lauf nicht besser gemacht hat"). Ein nachtraeglicher Edit
faelschte den Messbestand. **Die Nachfolgefassung gehoert in ein neues
Messverzeichnis**, Vorschlag `docs/measurements/2026-09-werkzeugfixe/skripte/`, mit einem
Kopfsatz, der auf das Original zeigt.

**Gates, die mitziehen:** `backend/tests/test_measurement_scripts.py` erfasst jedes
Skript unter `docs/measurements/*/skripte/` (Fixture `measurement_script`,
`test_the_wide_scope_covers_every_measurement_and_skips_what_is_not_a_script`). Fuer die
neue Datei gelten damit automatisch: kein Wagenruecklauf, kein Gedankenstrich, Shebang,
kein Maschinenpfad, kein Passwort auf der Kommandozeile.

### 4.4 Beweis-Design fuer die EINE Box-Anfahrt (D-01)

**Kostenrahmen.** Laufender Satz `0,1158 USD/h` (0,0978 Box + 0,0130 Speicher + 0,0050
Adresse). Vier Stunden sind **0,46 USD**, also unter dem Deckel von 0,50 USD. Geparkt
kostet die Box `0,3130 USD/Tag`. [VERIFIED: `scripts/ops/aws_box.sh`, `cmd_prices`;
`box.env` `BOX_PARKED_COST_USD_PER_DAY`]

**Zustand vor der Anfahrt** [VERIFIED: `box.env`]:

```
BOX_INSTANCE_ID=i-06b1d913f5c6f669b     m7g.large, eu-central-1c, Ubuntu 24.04 arm64
VOLUME_ID=vol-04c5b59fe9417babd         60 GB gp3, "findling-corpus", /mnt/findling
BOX_STOPPED_ISO=2026-09-10T16:22:50Z    angehalten
BOX_LAST_UPTIME_HOURS=31.05             letzter Lauf, 3,5969 USD
```

**Die Anfahrtsliste, in dieser Reihenfolge. Jeder Punkt ist eine bekannte Falle.**

| # | Handlung | Beleg / Falle |
|---|----------|---------------|
| 0 | **Owner-Freigabe mit Deckel VOR dem Start** einholen | Hausregel des Projekts, in `deferred-items.md` Phase 10 als harte Nebenbedingung |
| 1 | `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` aus `C:/Users/Student/.findling-aws.env` in die Umgebung, **nie in ein Argument** | `aws_box.sh` nennt beide genau einmal, in der Existenzpruefung |
| 2 | `scripts/ops/aws_box.sh start` | Schreibt die neue `BOX_IP` und zieht die SSH-Regel auf die aktuelle Owner-Adresse nach (revoke vor authorize). **Die IP wechselt bei jedem Start** |
| 3 | A-Record `loadtest.infranode.dev` ist **nicht** setzbar (keine DNS-Zugaenge). Ersatz: Eintrag in `/etc/hosts` **der Box** auf die Adresse des Apache-Containers | **Diese Adresse wechselt bei JEDEM Maschinenstart.** Sie hat am 07.09. einmal zugeschlagen (Apache wanderte 172.18.0.6 -> 172.18.0.4, der Poller fand die Warteschlange nicht mehr). Der Pruefbefehl steht als Kommentar in `/etc/hosts` |
| 4 | `occ app_api:app:disable findling_backend && occ app_api:app:enable findling_backend` | **DI-05-36**: nach jedem Containerstart, der nicht von AppAPI kommt, indexiert er nicht mehr. `aws_box.sh start` nennt es als Punkt 4 seiner Nachlese |
| 5 | Falls irgendwo `app_api:app:register` lief: `docker update --memory=2g --memory-swap=2g` | Punkt 5 derselben Nachlese. Ohne das misst man gegen keine Grenze |
| 6 | `free -h` = 3.9Gi, `nproc` = 2, `uname -m` = aarch64 | Der `mem=4G`-Kernelparameter ist der ganze Sinn der Box |
| 7 | Index-Intaktheit feststellen, **bevor** gemessen wird: `occ findling:index --status` muss 52.111 indexiert / 37 uebersprungen / 0 fehlgeschlagen zeigen | Wenn nicht, ist die Anfahrt zu Ende und der Owner entscheidet neu. Kein Neuaufbau unter einem 4-h-Deckel |

**Messblock A, DI-10-01** (Dauer geschaetzt 10 bis 15 Minuten):

- Stufe 16 nachfahren: `search_load.py --concurrency 16 --rounds 10 --limit 5
  --container nc_app_findling_backend --json .../01-lastwerkzeug-stufe16.json`.
  Das sind 160 Anfragen, wie am 10.09.
- Kontrollstufe 8 mit denselben Parametern: `.../02-lastwerkzeug-stufe08.json`.
- **Der Beweis ist die Uebereinstimmung zweier unabhaengiger Zaehlungen:** die Zahl der
  `cURL error 28`-Zeilen im Nextcloud-Protokoll im Zeitfenster des Laufs gegen den neuen
  `failures`-Zaehler des Werkzeugs. Protokollausschnitt als
  `.../03-nc-protokoll-abbrueche.txt` mitschreiben, mit Start- und Endzeitstempel des
  Laufs darueber.
- **Erwartung, die vorher hingeschrieben gehoert:** Stufe 16 zeigt `failures > 0` und
  `hits_per_request` deutlich unter dem Wert der Stufe 8; Stufe 8 zeigt `failures == 0`.
  Trifft die Erwartung nicht, ist das ein Ergebnis und kein Grund fuer eine zweite
  Anfahrt: die 17 Abbrueche vom 10.09. haengen an der Kaltheit des Wirtscaches, und der
  ist nach 30 Stunden Stillstand anders kalt als er es war.

**Messblock B, DI-10-02** (Dauer geschaetzt 15 bis 30 Minuten):

- Die Nachfolgefassung des Sprachfall-Skripts fahren. Das Konto `sprachfall` und seine
  39 Dateien liegen noch auf der Box, das Skript erkennt das selbst
  (*"das Konto existiert schon, es wird nicht neu angelegt"*).
- **`FRIST` herabsetzen.** Das Skript schlaeft per Vorgabe 360 Sekunden, bevor es den
  Arbeitsvorrat zum ersten Mal liest, weil der Poller-Backoff bis 300 s laeuft und AIO
  `cron.php` nur alle fuenf Minuten ruft. Bei einem bereits indexierten Bestand ist das
  verschenkte Laufzeit: `FRIST=60 RUNDEN=10` uebergeben. Beides sind bereits Variablen
  mit Vorgabewert.
- **Der Beweis:** die Vorpruefung schreibt fuer jeden der zehn Begriffe die
  Fremdbestand-Trefferzahl mit, die vier bekannten Faelle erscheinen als
  `NICHT MESSBAR`, die sechs anderen bleiben `GRUEN`, und die Bilanzzeile nennt beide
  Zahlen. Zusaetzlich: die Zeile `ci-beleg` traegt eine Laufnummer und nicht `unbekannt`.

**Nach den Messungen:** `aws_box.sh stop` (schreibt Laufzeit und Kosten selbst nach
`box.env`), dann Kosten gegen den Deckel im Bericht ausweisen. Der Abbau ist ein
**eigener Plan** mit **eigener Freigabe**, siehe Abschnitt 8.

**Zur Discretion-Frage "Box-Anfahrt mit Upgrade-Beweis kombinieren":** **Nein.** Der
Upgrade-Beweis braucht eine Nextcloud, auf der 1.0.x installiert ist. Auf der Box laeuft
eine Instanz mit v1.1-Stand und dem Messindex; sie auf 1.0.x zurueckzudrehen hiesse, den
Messbestand zu gefaehrden, und eine zweite Nextcloud verbietet D-02 mit einer teuren
Begruendung. Der Upgrade-Beweis gehoert nach CI (Abschnitt 2.4). Die Box beweist die
zwei Werkzeug-Fixe gegen echte Last, sonst nichts.

---

## 5. Haertungsumfang

### 5.1 Das 06.1-Muster, gegen den CI-Bestand gehalten

Die Owner-Regel vom 06.09.2026 nennt neun Pfade. Fuer jeden: was ihn heute abdeckt.

| Pfad des 06.1-Musters | Abgedeckt durch | Belegstelle | Fuer v1.1 erneut faellig? |
|-----------------------|-----------------|-------------|---------------------------|
| Fehlerpfade | `integration.yml` Sonden `tamper_probe`, `missing_verdict_probe`, `mutation_skip_probe`; `test_extract_errors.py` | `.github/workflows/integration.yml:65-90` | **Nein**, laeuft auf jedem Push |
| Randpfade | `test_extract_edge_paths.py`, `test_exclusion_path_space.py`, `test_snippet_offsets.py` | `backend/tests/` | **Nein** |
| Negativpfade / Rechte-Grenzen | `test_acl_prefilter.py`, `test_php_acl_boundary.py`, `test_php_trust_boundary.py`, `test_semantic_boundary.py`, `test_guest_parity.py`, `integration.yml` Job `readonly-gate` | , | **Nein** |
| Neustart | `resilience.yml` Job `kill-resume`, dazu die DI-05-36-Zusicherung "A restart that nobody armed keeps indexing" | `.github/workflows/resilience.yml:311` | **Nein** |
| **Upgrade / Migration** | **nichts** | , | **JA. Das ist der neue Pfad der Phase.** Abschnitt 2.4 |
| Kaputte und boesartige Dateien | Der 39-Datei-Referenzkorpus fuehrt sechs absichtlich kaputte Dateien (Nullbytes, abgeschnittener Trailer, Seitenbaum-Zyklus); `SEARCH_QUERY_MAX_CHARS=512`, `SEARCH_QUERY_MAX_DEPTH=32`, die ZIP-Bombe-Grenze | `backend/src/findling/config.py:184-200`, `testdata/CORPUS.md` | **Nein** |
| Ressourcengrenzen | `SEARCH_SCAN_MAX=10_000`, harte 2-GiB-cgroup-Grenze, RSS-Ratsche in CI, Messbericht Abschnitt a (drei Schadenszaehler auf null) | , | **Nein**, durch Phase 10 frisch belegt |
| Fremdinstallation Ende-zu-Ende aus Store-Paketen | `deploy-harp.yml`, "Store install 1 bis 7" ueber drei Serverversionen | `.github/workflows/deploy-harp.yml:1203-1964` | **Teilweise**: nur amd64, und die Archive werden lokal gebaut statt vom Release geladen. Siehe 5.2 |
| Deinstallations-Zusagen | `deploy-harp.yml`, "Store uninstall 1 bis 6", je zweimal (Entwickler- und Storepfad) | `:1965-2123` | **Nein** |
| Store-Vorgaben | `test_store_metadata.py` (Schema-Kanten, drei Sprachen, Laengen, Bildgroessen, Kategorien, Lizenz, Vokabular-Gate), `release.yml` (xsltproc+xmllint, 512 KB, 20 MB) | , | **Nein** |
| Alle Audits erneut | `docs/audits/2026-09-phase-10/README.md` als Muster | , | **JA**, Erfolgskriterium 3 |

**Fazit:** Von den neun Pfaden ist genau einer nicht abgedeckt, und die ROADMAP nennt
ihn im Erfolgskriterium 2 beim Namen. Der Rest ist Bestand mit Belegstelle. Die
Haertungsarbeit dieser Phase ist deshalb **schmal und benennbar**: Upgrade, arm64,
Release-Artefakte statt lokalem Bau, Audit.

### 5.2 Fremdinstallation auf amd64 und arm64 (D-02)

**Was existiert.** `deploy-harp.yml` laeuft auf `runs-on: ubuntu-24.04` (amd64) mit einer
Matrix ueber drei Serverversionen (`stable33`/PHP 8.2, `stable34`/PHP 8.2,
`stable35`/PHP 8.3 mit `tolerate-failure: true`). Die Store-Install-Strecke baut beide
Archive mit `scripts/release/store-archive.sh`, signiert die Companion-Haelfte, nimmt
die Entwicklerinstallation **vollstaendig** weg, installiert die Companion aus dem
Archiv und laesst die Instanz jede Datei per Integritaetspruefung verifizieren, zieht das
Abbild **ohne jede Anmeldung** aus ghcr, registriert die ExApp aus dem Archiv und sucht
Inhalte, ohne dass irgendwer etwas konfiguriert.

**Das ist inhaltlich genau Erfolgskriterium 1, auf einer Architektur.**

**Was fehlt, und wie teuer es ist.**

| Luecke | Fix | Aufwand / Risiko |
|--------|-----|------------------|
| arm64 fehlt | `runner` in die Matrix aufnehmen und `runs-on: ${{ matrix.runner }}` setzen; `ubuntu-24.04-arm` ist in diesem Repository etabliert (`docker.yml`, `python.yml` Job `extract-bench-arm`, `measure.yml`) | Der HaRP-Digest ist ein **Manifestindex mit linux/amd64 und linux/arm64**, ausdruecklich deshalb so gepinnt (Kommentar bei `HARP_IMAGE`). Das Backend-Abbild wird je Ast lokal gebaut, auf arm64 also nativ. **Empfehlung: nur EIN arm64-Ast, auf `stable34`.** Sechs Aeste sind sechs Instanzen fuer eine Aussage, die einer traegt |
| Archive werden lokal gebaut, nicht vom Release geladen | Ein zusaetzlicher Modus, der `findling.tar.gz`/`findling_backend.tar.gz` von einer Release-Tag-URL laedt statt sie zu bauen | Genau das braucht auch der Upgrade-Test (Abschnitt 2.4), der die v1.0.3-Assets laden muss. **Einmal bauen, zweimal nutzen** |
| `stable35` steht auf `tolerate-failure: true` | Der Kommentar nennt **RE-CHECK DATE: 2026-09-16** und benennt "die Store-Einreichung" als den Plan, der die Nachverfolgung haelt | Kollidiert mit D-10, siehe Open Question 2 |

**Was ausdruecklich NICHT getan wird:** eine zweite Nextcloud auf der Mess-Box. Die
Begruendung steht in `box.env` als Schadensbericht des 07.09.: der arm64-Installationslauf
lief auf einer zweiten, frischen Nextcloud am selben Docker-Dienst, seine
Deinstallations-Zusage 3 fuehrte `app_api:app:unregister --rm-data` aus, der Volumenname
leitet sich allein aus der App-Kennung ab, und damit war das **Messvolumen der ersten
Instanz** geloescht. D-02 ist die Lehre daraus.

### 5.3 Die drei geerbten Befunde, die im Audit entschieden werden muessen

| Befund | Stand | Was Phase 11 damit tut |
|--------|-------|------------------------|
| **DI-07-02** Kaltstart reisst `REQUEST_TIMEOUT_SECONDS = 1,5 s` | Gemessen, **nicht geschlossen**, ausdruecklich an Phase 11 uebergeben. 1.838,4 ms Gesamtdauer bei kaltem Wirtscache, ein belegter Abbruch um 14:05:17Z mit null Treffern und ohne Fehlermeldung fuer den Nutzer | Das ist eine **Entscheidung im Audit**, keine Messung. Die Optionen stehen im Befund: Decke heben (trifft jeden Aufruf jedes Nutzers), Gewichte beim Containerstart vorwaermen, oder ein eigener Weg fuer den ersten Aufruf. Die letzten beiden sind ungemessen. **Empfehlung: als LOW dokumentiert entscheiden** und im Store-Text nicht erwaehnen; der Fall tritt genau einmal je Containerstart bei kaltem Wirtscache auf, und die Methodik-Korrektur aus Abschnitt 9.2 des Berichts nimmt der Zahl ihre Schaerfe (gemessen ist die ganze OCS-Anfrage, gedeckelt nur der innere Aufruf) |
| **DI-07-03** die Kandidatenschleife holt keine zweite Runde nach | Messteil geschlossen (1,0 Runde, 1,9 Aufrufe je Suche im Alltag). Offen ist die **Frage an den Rechteabgleich**: auf einer Instanz mit grossem Fremdbestand findet ein Nutzer mit wenigen Dateien seine eigenen nicht und bekommt eine leere Liste statt einer Meldung | **Der unangenehmste Punkt der Phase.** Es ist ein echter Produktbefund (Punkt 5 der Liste "Was dieser Lauf nicht besser gemacht hat"). Der Rechteabgleich ist die Berechtigungskette, und die ROADMAP verbietet, sie anzufassen. **Empfehlung: als MEDIUM aufnehmen, aber die Abhilfe von der Kette trennen.** Was ohne Eingriff in die Kette geht: der Nutzer bekommt statt einer leeren Liste einen Hinweis, wenn die Runde Kandidaten hatte und der Recheck alle verworfen hat. Das ist ein Text und eine Bedingung in `SearchService`/`Provider`, kein zweiter Filter. **Das braucht einen Owner-Entscheid**, siehe Open Question 3 |
| **T-09-29** DoS, voller Vektorscan je Anzeigeseite | In Phase 10 **entschieden**: `accept` bleibt, jetzt mit Zahlen (tiefe Seite 0,333 s gegen erste Seite 0,332 s, der Scan laeuft einmal je Anfrage und nicht je Seite), Wiedervorlage bei deutlich groesserem Vektorbestand | **Nichts zu tun.** Als entschieden ins Phase-11-Audit uebernehmen, mit Verweis auf `10-07-SUMMARY.md`. Siehe Abschnitt 7 |

### 5.4 Was das Audit als Objekt hat

Der Diff der Phase 11 wird, anders als der der Phase 10, **Produktionscode enthalten**:
`php/l10n/fr.*` (Auslieferungsdateien, sie liegen im Companion-Archiv),
`php/appinfo/info.xml`, `backend/appinfo/info.xml`, `scripts/ops/search_load.py`, neue
Tests, geaenderte Workflows. Das Phase-10-Audit konnte mit einem Satz sagen "diese Phase
misst, sie baut nicht"; dieses kann es nicht.

**Vorgeschlagene ASVS-Kategorien** (Phase 10 fuehrte V2, V3, V4, V7, V14):

| Kategorie | Gilt | Warum |
|-----------|------|-------|
| V4 Access Control | ja | DI-07-03 beruehrt den Rechteabgleich, wenn auch nur in der Frage |
| V5 Input Validation / Output Encoding | ja | Die 173 FR-Werte laufen durch `$l->t()` und werden im Template ausgegeben. Das Escaping-Gate (`test_the_page_breaks_none_of_the_checkable_prohibitions`) prueft das Template, nicht den Katalog. Ein FR-Wert mit `<` waere die neue Flaeche |
| V7 Error Handling | ja | Der leere Trefferzustand aus DI-07-03 ist ein Fehlerzustand ohne Meldung |
| V14 Configuration / Build | ja | Versionsbump an drei Stellen, Signaturkette, Workflow-Pins (`test_workflow_pins.py`), der neue arm64-Runner |
| V2/V3 Auth/Session | nein | Unveraendert. Ausdruecklich als "nicht beruehrt" benennen, nicht weglassen |

---

## 6. Store-Text-Mechanik

### 6.1 Der Drei-Stellen-Merker aus DI-10-03 ist ueberholt, und das ist wichtig

**DI-10-03 sagt:** *"wer eine Messzahl in einem nach aussen sichtbaren Text aendert,
aendert drei Stellen ... Die Zahl steht in `README.md`, in `README.en.md` und in beiden
`info.xml`, und ein Gate haelt sie deckungsgleich."* D-06 uebernimmt diesen Merker.

**Der Code sagt etwas anderes.** `backend/tests/test_store_metadata.py`,
`scan_measured_sentence`, Docstring woertlich:

> *"Until 07.09.2026 the sentence stood in three files, README.en.md and the English
> description of both halves, and this gate held them equal. The owner decided on
> 07.09.2026 that the store descriptions are short fact lists and carry no measurement
> narrative, so the sentence lives in README.en.md alone now and the numbers stay in
> docs/performance.md."*

Und der einzige Aufruf:

```python
def test_the_measured_sentence_stands_in_the_readme() -> None:
    assert scan_measured_sentence("README.en.md", README.read_text(encoding="utf-8")) == []
```

**Es gibt heute genau EINE maschinell gehaltene Stelle: `README.en.md`.** Die beiden
`info.xml` tragen nur noch die qualitative Zusage, und die aendert der Zahlentausch
nicht:

```
- RAM: 4 GB is enough, the container runs under a hard 2 GB limit (measured)
```

**Folge fuer die Planung:** Wer nach dem Drei-Stellen-Gate sucht, findet es nicht und
haelt das fuer eine Regression. Der Merker muss im Plan **korrigiert weitergegeben**
werden, sonst kostet er eine Suche und im schlimmsten Fall einen Rueckbau des
Owner-Entscheids vom 07.09.

### 6.2 Der Messsatz heute und morgen

`MEASURED_SENTENCE` (Zeile 279), woertlich:

```
On a 4-GB ARM64 box with 51,961 indexed documents and the semantic search active, the
container peaked at 1,813 MB of resident anonymous memory, under a hard 2 GB limit
enforced by the kernel.
```

Der Vergleich laeuft ueber `collapse()`, also nach Zusammenziehen jeder
Whitespace-Folge; ein Zeilenumbruch ist kein Unterschied. Der Selbsttest
(`test_a_text_without_the_measured_sentence_is_reported`) mutiert `1,813` zu `1,913`.

**Der Zahlentausch beruehrt drei Werte im Satz** (die neuen aus
`00-kernaussage.md`, Abschnitte a und b):

| Groesse | alt | neu | Rohdatei |
|---|---|---|---|
| indizierte Dokumente | 51.961 | **52.111** | `rohdaten/48-vektorbestand.txt` |
| anon-Spitze | 1.813 MB | **1.764 MB** (1.764,2 MB, 2026-09-10T08:12:24Z) | `rohdaten/00-ende.txt` aus `rohdaten/96-volllauf.csv` |
| harte Grenze | 2 GB | unveraendert | `rohdaten/07-oom-beweis.txt` |

Neu hinzu kommt die Grundlast: **103,2 MB gegen 691,8 MB**, also **minus 588,6 MB** oder
**minus 85,1 Prozent** (`rohdaten/94-grundlast.txt`). Das ist die Zahl, die 11-CONTEXT.md
unter "Specific Ideas" als staerkste ehrliche Story nennt.

### 6.3 Die Stellen, die beim Zahlentausch von Hand mitziehen

| Datei | Was drin steht | Aenderung |
|-------|----------------|-----------|
| `README.en.md` | Der Messsatz woertlich, im Abschnitt "Requirements" | **Ja**, und `MEASURED_SENTENCE` im Test in derselben Aenderung, sonst ist das Gate rot |
| `backend/tests/test_store_metadata.py` | `MEASURED_SENTENCE` | **Ja** |
| `README.md` (deutsch) | Nur die qualitative Zusage ("4 GB genuegen, harte 2-GB-Grenze (gemessen)") | Nur, wenn der Messsatz dreisprachig werden soll. Heute traegt ihn nur die englische Fassung |
| `README.fr.md` | Nur die qualitative Zusage ("4 Go suffisent ... limite stricte de 2 Go (mesuré)") | Dieselbe Frage, dieselbe Antwort. Wenn ja, dann in derselben Runde (D-06 verlangt es) |
| `php/appinfo/info.xml`, `backend/appinfo/info.xml` | Nur die qualitative Zusage, dreisprachig | **Nein**, ausser der Owner hebt den Entscheid vom 07.09. auf |
| `docs/store-listing.md` | Die Vorlage aller sechs Store-Texte | Nur, wenn die `info.xml` sich aendern. Das Gate `test_the_store_listing_document_avoids_the_blocked_term_counting_every_line` liest die Datei |
| `docs/performance.md` | Alle Zahlen mit Methode | Nachzug der v1.1-Zahlen, ohne Kurztext-Regel |
| `CLAUDE.md`, RAM-Budget-Tabelle | Die Zeile "Tokenizer und Splitter, 544 MB" (seit 10-07) | Gegenlesen, damit sie nicht gegen die neue Grundlast laeuft |

### 6.4 Das Vokabular-Gate, Belegstelle

`backend/tests/test_store_metadata.py`:

- `BLOCKED_TERM = "arch" + "iv"` (Zeile 172), aus zwei Haelften zusammengesetzt, damit
  das Gate nicht selbst traegt, was es fernhalten soll.
- `scan_german_prose_of_an_info` prueft die **deutschen** `name`/`summary`/`description`
  beider `info.xml`, **ohne** XML-Kommentare (Entscheid E-H2 vom 06.09.2026: die Regel
  gilt fuer deutsche Prosa in oeffentlichen Texten).
- `scan_german_document` prueft `docs/store-listing.md` **einschliesslich** jeder Zeile.
- `test_the_exception_of_e_h2_is_exercised_and_not_only_claimed` beweist, dass der
  englische Fachausdruck in einem technischen Kommentar von `backend/appinfo/info.xml`
  noch steht **und** dass das Gate ihn stehen laesst. Wer den Kommentar umformuliert,
  macht diesen Test rot und muss E-H2 neu lesen, bevor er etwas anfasst.

**Nicht abgedeckt:** `README.md`, `README.fr.md`, `README.en.md`, `php/l10n/*`,
`docs/performance.md`. Wer den Begriff dort hineinschreibt, faellt durch kein Gate.
Vor dem Push ist das Gate lokal zu fahren, so wie es die globale Owner-Regel verlangt.

### 6.5 `README.fr.md`, Stand

Existiert, 2.702 Byte, gepflegt (Stand 07.09.2026, dieselbe Mtime wie die beiden
anderen). Struktur deckungsgleich mit `README.en.md`: Sprachleiste, Was Findling kann,
Dateitypen, `## Prérequis`, Installation, `## Confidentialité`, `## Mesures`, Lizenz. Der
Abschnitt Prérequis traegt heute die qualitative Zusage und keine Messzahl. **Es gibt
kein Gate, das die drei READMEs gegeneinander haelt.** Ihre Gleichlaeufigkeit ist heute
eine Regel in `CLAUDE.md` und keine Maschine. Falls der Messsatz dreisprachig wird, waere
ein Gate nach dem Muster von `scan_measured_sentence` mit drei Wortlauten die
zuverlaessige Bauform, und es waere eine kleine Aenderung.

---

## 7. DI-10-04, DI-10-05, T-09-29: klein und risikofrei oder weiterreichen?

| Befund | Was er verlangt | Urteil | Begruendung |
|--------|-----------------|--------|-------------|
| **DI-10-04** Ursache der Mehrlaufzeit (26 h 37 min gegen 18 h 56 min, plus 40,6 Prozent) ist eingegrenzt und nicht bewiesen | Entweder ein Lauf, der die Einbettung erst nach der Indexierung anstoesst, oder eine Instrumentierung, die die Wartezeit des Zulaufs mitschreibt. **Beides ist ein neuer Volllauf** | **WEITERREICHEN**, dokumentiert | Ein Volllauf dauert 26 Stunden und kostet rund 3 USD. Der Deckel der Phase ist 4 Stunden und 0,50 USD (D-01). Der Befund beruehrt kein Erfolgskriterium und ist in Abschnitt 19.2 des Berichts als Verschlechterung benannt. **Gehoert in die v1.2-Messplanung, zusammen mit dem Box-Wiederaufbau-Runbook**, das 11-CONTEXT.md dorthin vertagt |
| **DI-10-05** der aufgeschriebene Digest von `:dev` haelt nicht | Die Frage: darf ein Messlauf gegen `:dev` pruefen, oder muss er gegen einen unbeweglichen Tag laufen? | **MITNEHMEN**, als Entscheidung ohne Codeaenderung | Klein und risikofrei, weil die tragende Feststellung schon existiert: der **Baumhash** (`baumhash-gleich ja`, 54 Dateien) ist der Beweis, der Digest die Notiz. Der Auslieferungspfad ist bereits unbeweglich: `docker.yml` prueft auf einem Tag, dass Tag, beide `<version>` und `<image-tag>` uebereinstimmen. Der Entscheid lautet also: **`:dev` bleibt fuer Messlaeufe zulaessig, der Baumhash ist der Beweis, der aufgeloeste Digest wird mitgeschrieben und nicht vorher aufgeschrieben.** Das sind drei Saetze im Phase-11-Audit und eine Praezisierung im Kopf von `measure.yml`. Kein Produktionscode |
| **T-09-29** DoS, voller Vektorscan je Anzeigeseite | , | **BEREITS ERLEDIGT**, nur uebernehmen | In Phase 10 mit Zahlen entschieden: `accept` bleibt, der Vektorscan laeuft einmal je Anfrage und nicht je Seite (tiefe Seite 0,333 s gegen erste Seite 0,332 s), Wiedervorlage bei deutlich groesserem Vektorbestand (`10-07-SUMMARY.md`, Zeilen 45, 192, 262). Aufwand fuer Phase 11: eine Zeile im Audit mit Verweis. **Kein Umfang** |

---

## 8. EBS-Snapshot und Abbau (D-03)

### 8.1 Was `aws_box.sh` heute kann und was nicht

Sieben Unterbefehle: `prices`, `create`, `volume`, `status`, `stop`, `start`, `destroy`.
**Es gibt keinen `snapshot`.** [VERIFIED: `usage()`, Zeilen 137-148]

`cmd_destroy` (Zeile 683) tut in dieser Reihenfolge: Instanz terminieren und auf
`instance-terminated` warten, Volume loeschen, Security Group loeschen, dann die
Nichtexistenz aller drei einzeln gegen die API pruefen, dann ein **Sweep nach dem Tag**
`purpose=findling-phase5` ueber `ec2 describe-tags`, und zum Schluss
`rm -f "$STATE_FILE"`.

**Zwei Fallen, die aus dem Code folgen und in keinem Dokument stehen:**

1. **Der Sweep wuerde den Snapshot als Leiche melden.** Er listet **jede** Ressource mit
   dem Tag ausser der gerade terminierten Instanz und setzt `failed=1`. Ein Snapshot mit
   `purpose=findling-phase5` macht `destroy` rot, die Meldung *"something is left over"*
   erscheint, und die Zustandsdatei bleibt liegen. Der Abbau saehe fehlgeschlagen aus,
   obwohl er richtig lief.
2. **`STATE_FILE` ist `box.env`, und `destroy` loescht es.** `STATE_FILE="$STATE_DIR/box.env"`
   (Zeile 103). Die Datei traegt die gesamte Historie der Box: Instanz, Volume, jede
   Stop-/Start-Runde mit Laufzeit und Kosten, den Schadensbericht vom 07.09., den
   DI-05-36-Befund. **Vor dem `destroy` muss ihr Inhalt gesichert sein**, sonst ist die
   Kostenrechnung des Projekts weg.

### 8.2 Der empfohlene Weg, Schritt fuer Schritt

**Reihenfolge ist hier die ganze Sicherheit: erst sichern, dann pruefen, dann
zerstoeren.**

```
# 0  Instanz ist angehalten. Ein Snapshot eines angehaengten, beschriebenen
#    Datentraegers ist nur absturzkonsistent; ein Snapshot eines Datentraegers
#    an einer gestoppten Instanz ist sauber.
aws_box.sh status                     # Zustand muss "stopped" sein

# 1  Snapshot anlegen. NICHT mit purpose=findling-phase5 taggen, sonst faellt
#    der Sweep von cmd_destroy darueber.
aws ec2 create-snapshot --region eu-central-1 \
  --volume-id vol-04c5b59fe9417babd \
  --description "findling corpus and index, v1.1 Vergleichsmessung 2026-09-10, 52111 Dokumente" \
  --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Name,Value=findling-corpus-2026-09},{Key=purpose,Value=findling-corpus-keep}]'

# 2  Warten, mit dem Waiter der CLI und nicht mit einer eigenen Schleife
#    (Hausregel seit 04.09.).
aws ec2 wait snapshot-completed --region eu-central-1 --snapshot-ids snap-XXXX

# 3  Unabhaengig nachlesen. Das ist die Verifikation, nicht der Waiter.
aws ec2 describe-snapshots --region eu-central-1 --snapshot-ids snap-XXXX \
  --query 'Snapshots[0].{State:State,Progress:Progress,VolumeSize:VolumeSize,VolumeId:VolumeId,StartTime:StartTime,OwnerId:OwnerId,Encrypted:Encrypted}'
# Erwartet: State=completed, Progress=100%, VolumeSize=60, VolumeId=vol-04c5b59fe9417babd

# 4  Snapshot-Id und die Ausgabe von Schritt 3 in box.env schreiben UND in den
#    Phasenbericht. box.env wird in Schritt 6 geloescht.

# 5  Owner-Bestaetigung fuer die zerstoerende Handlung einholen (D-03).

# 6  Abbau.
aws_box.sh destroy
```

**Die Abbau-Reihenfolge innerhalb von `destroy` stimmt bereits** und ist im Skript
begruendet: die Instanz geht **vor** dem Volume, weil ein benutztes Volume nicht
loeschbar ist und ein Abhaengen bei laufenden Schreibvorgaengen das Dateisystem
beschaedigt.

**Was mit `terminate` sonst noch verschwindet:** die 40-GB-gp3-Systemplatte, die
ueblicherweise `DeleteOnTermination=true` traegt. Sie enthaelt die lokale Registry mit den
Messabbildern und `/home/ubuntu/work`. **Vor dem Abbau pruefen**, ob dort noch etwas
liegt, das kein Gegenstueck im Repository hat. Die Rohdaten der Phase 10 liegen
vollstaendig unter `docs/measurements/2026-09-vergleichsmessung-m7g/`, also duerfte die
Antwort "nein" sein, aber sie gehoert festgestellt und nicht angenommen.

### 8.3 Zwei Bauformen, und was ich empfehle

| Bauform | Aufwand | Bewertung |
|---------|---------|-----------|
| Von Hand, mit den Befehlen oben, dokumentiert im Phasenbericht | Null Codeaenderung | Der Sweep-Konflikt wird durch den anderen Tag umgangen, aber niemand haelt das fest |
| **`aws_box.sh snapshot` als achter Unterbefehl** | Etwa 40 Zeilen plus Testanpassung | **Empfohlen.** Der Snapshot bekommt einen Ort, die Verifikation wird Teil des Werkzeugs statt einer Erinnerung, und `cmd_destroy` kann den einen erwarteten Ueberlebenden ausdruecklich kennen statt ihn als Leiche zu melden |

**Gate, das dabei mitzieht:** `backend/tests/test_ops_scripts.py`,
`test_the_aws_tool_names_its_seven_subcommands_in_the_usage` (Zeile 252). Der Test
zaehlt **sieben**. Ein achter Unterbefehl macht ihn rot, und das ist die richtige Menge
Reibung: er ist genau dafuer da.

### 8.4 Kosten

| Posten | Satz | Quelle |
|--------|------|--------|
| Box laufend | 0,1158 USD/h (0,0978 + 0,0130 + 0,0050) | `aws_box.sh`, gepinnt, Quelle in `cmd_prices` genannt |
| Box geparkt | 0,3130 USD/Tag = **9,39 USD/Monat** | `box.env` `BOX_PARKED_COST_USD_PER_DAY` |
| gp3-Speicher | 0,0952 USD/GB-Monat | `aws_box.sh` `PRICE_GP3_GB_MONTH` |
| **EBS-Snapshot, Standardstufe** | **rund 0,05 USD/GB-Monat** | [ASSUMED] Websuche, US-East-Grundsatz, EU-Regionen leicht darueber. Der reproduzierbare Weg steht in `cmd_prices`: die oeffentliche Bulk-Preisliste `pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/eu-central-1/index.csv` filtern. Dieses Konto kann `pricing:GetProducts` nicht lesen |

Ein Snapshot bezahlt **belegte Bloecke**, nicht die 60 GB Volumengroesse, und er ist
inkrementell. Der Korpus belegt rund 20 GB, dazu Index (786 MB), `vectors.db` (69 MB),
`state.db` und Docker-Wurzel. **Schaetzung: 25 bis 40 GB, also 1,25 bis 2,00 USD/Monat**,
was die Groessenordnung in D-03 ("~1-2 USD/Monat") bestaetigt. Gegen 9,39 USD/Monat
geparkt spart der Abbau rund **7,50 bis 8,15 USD/Monat**. Die exakte Zahl steht nach dem
Snapshot in `describe-snapshots` unter `VolumeSize` und in der Rechnung, und sie gehoert
in den Phasenbericht statt in eine Schaetzung.

---

## Standard Stack

**Diese Phase fuehrt kein neues Paket ein, und das ist eine Entscheidung, keine
Feststellung.** Ein Release, das neue Abhaengigkeiten mitbringt, ist ein Release, das
seine Lieferkette neu beweisen muss, und die Phase hat dafuer keinen Platz.

| Vorhandenes Werkzeug | Version | Rolle in dieser Phase | Belegstelle |
|---|---|---|---|
| tantivy (Python-Bindungen) | 0.26.0 | **Unveraendert lassen.** Der Wert steht als `tantivy_version` in den Indexmarken; ein Bump waere ein Reindex fuer jeden Bestandsnutzer | `backend/pyproject.toml` |
| wngerman (Debian) | 20161207-15 | **Unveraendert lassen.** Quelle des `wordlist_hash` | `backend/Dockerfile:206` |
| pytest / ruff / pyright / vulture | 9.1.1 / 0.16.6 / 1.1.411 / 2.16 | Die Gates der neuen FR-Tests | `backend/pyproject.toml` |
| `actions/checkout` | 3d3c42e5... (v7.0.1) | Alle Workflows pinnen auf SHA, `test_workflow_pins.py` haelt die Form | `.github/workflows/*` |
| `shivammathur/setup-php` | f3e473d1... (2.37.2) | `release.yml`, `php.yml` | , |
| `nextcloud/appstore` (Transform+Schema) | SHA `eda850ba...` | Store-Validierung in `release.yml`, identisch mit `php.yml` | `release.yml` `APPSTORE_SHA` |
| `ghcr.io/nextcloud/nextcloud-appapi-harp` | Digest `sha256:603fdf5c...` | Manifestindex mit amd64 **und** arm64, deshalb taugt derselbe Pin fuer den neuen arm64-Ast | `deploy-harp.yml` `HARP_IMAGE` |
| GitHub-Runner `ubuntu-24.04-arm` | , | Der arm64-Ast fuer D-02 | in `docker.yml`, `python.yml`, `measure.yml` etabliert |

### Alternatives Considered

| Statt | Koennte man | Warum nicht |
|---|---|---|
| Upgrade-Test in `deploy-harp.yml` | Eigener Workflow `upgrade.yml` | Die halbe Maschinerie (Server-Checkout, HaRP, lokale Registry, Testnutzer) waere dupliziert. `deploy-harp.yml` haelt sie schon und hat mit "Store uninstall 2" den Kern des Upgrades bereits gebaut |
| FR-Gates in `test_admin_ui_contract.py` | Neue Datei `test_l10n_french.py` | Der de/de_DE-Vergleich lebt in `test_admin_ui_contract.py`. Zwei Orte fuer eine Frage sind genau der Widerspruch, den die Audits dieses Projekts sonst aufschreiben |
| `aws_box.sh snapshot` | Von Hand mit dokumentierten Befehlen | Siehe 8.3. Der Sweep-Konflikt ist real und nur im Werkzeug dauerhaft loesbar |
| `--min-hits` in `search_load.py` | Immer harte Fehlschlagzaehlung ohne Schalter | Dann meldet das Werkzeug auf einer Instanz ohne die zehn Begriffe 100 Prozent Fehlschlaege. Der Schalter macht die Umdeutung ausdruecklich |

**Installation:** keine.

---

## Package Legitimacy Audit

**Nicht anwendbar: diese Phase installiert kein externes Paket.**

Geprueft: `backend/pyproject.toml` hat gegen `v1.0.3` nur Patch-Bumps bestehender,
exakt gepinnter Abhaengigkeiten (`pypdf 6.16.1->6.16.2`, `striprtf 0.0.32->0.0.33`,
`lxml 6.1.1->6.1.3`, `ruff 0.16.4->0.16.6`), keine neue Zeile. Der Plan sollte diesen
Zustand halten: ein Paketzugang in der Haertungsphase muss durch die Legitimitaetspruefung
und ist damit ein eigener Vorgang, kein Nebenzug.

Sollte sich waehrend der Ausfuehrung doch ein Bedarf ergeben, gilt der Gate-Ablauf
(slopcheck, Registry-Pruefung im richtigen Oekosystem, `npm view <pkg> scripts.postinstall`
bei Node) unveraendert.

---

## Architecture Patterns

### Systemarchitektur der Abgabe

```
  Arbeitsbaum (main)
       |
       |  Commit: 3x Version (php info.xml, backend info.xml, image-tag)
       v
  git tag v1.1.0  --> push
       |
       +------------------------------> docker.yml  (Tag-Trigger, Pfadfilter backend/**)
       |                                   | Version-Gate: Tag == version == image-tag
       |                                   | build amd64 (ubuntu-24.04)
       |                                   | build arm64 (ubuntu-24.04-arm)
       |                                   v
       |                                ghcr.io/street1983nk/findling_backend:1.1.0
       |                                   (Manifestindex, beide Plattformen)
       |
       +------------------------------> release.yml  (Tag-Trigger, KEIN Pfadfilter)
                                           | Version-Gate (unabhaengig, absichtlich doppelt)
                                           | Zertifikate holen + Fingerabdruck DER pruefen
                                           | Wegwerf-NC installieren (nur fuer occ)
                                           |
                                     Companion                    Backend
                                       stage                        stage
                                       xsltproc+xmllint             xsltproc+xmllint
                                       512 KB                       512 KB
                                       integrity:sign-app           (bewusst KEINE Codesignatur)
                                       pack                         pack
                                       20 MB                        20 MB
                                       Release-Signatur             Release-Signatur
                                       verify gegen Zertifikat      verify gegen Zertifikat
                                           |                            |
                                           +------------+---------------+
                                                        v
                                              assert-contents (beide)
                                                        v
                                       gh release create v1.1.0 + 4 Assets
                                                        |
                       (manuell)                        v
       store-submit.yml  --------> liest .sig vom Asset, POST /api/v1/apps/releases
                                   je Haelfte, akzeptiert 200|201
                                                        v
                                          apps.nextcloud.com
                                                        |
                                                        v
                          Nutzerinstanz: Companion aus tar.gz, ExApp zieht
                          ghcr...:1.1.0 ueber AppAPI/HaRP, Volume bleibt
```

**Was der Leser daran ablesen soll:** Es gibt genau **einen** Bau des Archivs, und die
Signatur gehoert zu genau diesen Bytes. Jede Bauform, die das Archiv zweimal erzeugt,
erzeugt eine Signatur zu einer Datei, die niemand hat.

### Pattern 1: Die Ratsche gegen die eigene Zusage

**Was:** Eine Zusage, die eine Phase gibt, wird als Test hinterlegt, der rot wird, wenn
eine spaetere Phase sie unbemerkt bricht.
**Wann:** Immer, wenn ein Owner-Entscheid eine Konstante festnagelt.
**Beispiel:** D-04 sagt "Index bleibt kompatibel". Der Test dazu:

```python
# Quelle des Musters: backend/tests/test_lockstep_versions.py und die RSS-Ratsche
# aus Plan 06.1-04. Beide sind Zusagen, die als Test leben.
GOLD_V1_0_3 = {
    "schema_version": "1",
    "index_version": "1",
    "analyzer_version": "1",
    "tantivy_version": "0.26.0",
}

def test_an_upgrade_from_1_0_x_would_not_trigger_a_reindex() -> None:
    """D-04 vom 2026-09-10: v1.1 haelt den Index kompatibel.

    Faellt dieser Test, ist das keine Reparatur, sondern eine Owner-Frage: eine
    veraenderte Marke bedeutet fuer jeden Bestandsnutzer einen Neuaufbau.
    """
    current = expected_versions(digest="ignored")
    for mark, gold in GOLD_V1_0_3.items():
        assert current[mark] == gold, (
            f"{mark} ist {current[mark]!r} statt {gold!r}; ein Upgrade von 1.0.x "
            f"wuerde jetzt einen Reindex ausloesen (D-04)"
        )
```

### Pattern 2: Das dreiwertige Messurteil

**Was:** Ein Messfall, der aus Gruenden des Aufbaus keine Aussage tragen kann, wird
`nicht messbar` und nicht `rot`.
**Wann:** Wenn die Umgebung die Zusage aushebeln kann, ohne dass das Erzeugnis defekt ist.
**Bestand:** `99b-runden.sh` liest den Driftfall bereits dreiwertig
(*"null Treffer und eine Runde je Suche heisst, der Vorfilter wusste schon Bescheid und
die Drift war zu kurz"*). DI-10-02 bekommt dasselbe Muster.

### Pattern 3: Die Kopie eines gefahrenen Messskripts statt seiner Bearbeitung

**Was:** Skripte unter `docs/measurements/<lauf>/skripte/` sind die gefahrenen Fassungen
und Teil des Belegs. Ein Fix entsteht als neue Datei in einem neuen Laufverzeichnis, mit
einem Kopfsatz, der auf das Original zeigt.
**Warum:** Ein nachtraeglich veraendertes Messskript macht jede Zahl daneben unbelegt.

### Anti-Patterns

- **Eine zweite Nextcloud am selben Docker-Dienst.** Kostete am 07.09. das Messvolumen
  der ersten Instanz, weil sich der Volumenname allein aus der App-Kennung ableitet.
  D-02 ist die Lehre.
- **Den Drei-Stellen-Merker aus DI-10-03 woertlich befolgen.** Er beschreibt einen
  Zustand vor dem 07.09.2026. Abschnitt 6.1.
- **Das Archiv zweimal bauen.** `tar.gz` ist nicht byte-reproduzierbar; das
  Schwesterprojekt hat den Unterschied auf seinem 0.1.8-Release gemessen (45.710 Byte
  lokal gegen 45.546 veroeffentlicht).
- **Eine Marke heben, um "aufzuraeumen".** Jede der fuenf Marken kostet jedem
  Bestandsnutzer einen Neuaufbau von rund 26 Stunden.
- **Den FR-Katalog gegen den deutschen auf Textgleichheit pruefen.** Das Gate fuer de/de_DE
  tut das mit Absicht; fuer Franzoesisch waere es sinnlos und wuerde die falsche
  Invariante festnageln.

---

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---|---|---|---|
| Store-Schema-Validierung | Eigene XSD-Pruefung | `xsltproc pre-info.xslt` + `xmllint --schema info.xsd`, gepinnt auf `APPSTORE_SHA` | Der Store validiert **nach** der Transform. Eine Direktvalidierung prueft ein Dokument, das nie eingereicht wird |
| Zertifikat-Identitaet | Textvergleich der `openssl`-Ausgabe | SHA-256 ueber den **DER** des Public Key, Subject mit `-nameopt RFC2253` | Gemessen: OpenSSL 3.0.13 und 3.5.6 drucken fuer denselben Schluessel verschiedene Digests ueber den PEM-Text und schreiben `CN = x` gegen `CN=x`. Lauf 33894444190 |
| Warten auf AWS | Eigene Warteschleife | `aws ec2 wait <waiter>` | Hausregel seit 04.09.: feste 15-s-Intervalle, begrenzte Versuchszahl. Ein selbstgebauter Loop hat diesem Projekt die Regel eingebracht |
| Nichtexistenz einer AWS-Ressource | `describe` und "kein Fehler heisst weg" | Die drei Formen, die `aws_box.sh` benennt: `state=terminated`, `InvalidVolume.NotFound`, `InvalidGroup.NotFound`, plus Sweep nach Tag | Eine terminierte Instanz antwortet bis zu einer Stunde weiter. Alles, was das Skript nicht lesen kann, zaehlt als noch da |
| Archiv-Inhalt zusichern | Eigene Pruefung im Workflow | `scripts/release/store-archive.sh assert-contents` | `deploy-harp.yml` installiert aus denselben Archiven und faehrt dieselben Pruefungen. Zwei Kopien waeren zwei Meinungen darueber, was ausgeliefert werden darf |
| Katalog-Konsistenz | Sichtpruefung | Die vier Gates aus Abschnitt 1.3 | Diese App hat keinen String-Extraktor; die Kataloge sind handgeschrieben. Was keine Maschine haelt, laeuft auseinander |
| Reindex-Sichtbarkeit (D-05) | Neuer Banner | `start_rebuild_on_drift` plus vorhandener Reindex-Banner | Ist gebaut, inklusive Fingerabdruck-Merker, damit ein Neustart mitten im Wiederaufbau nicht von vorn anfaengt |

**Kerneinsicht:** Fast alles, was diese Phase braucht, ist im Repository bereits einmal
richtig geloest. Die Arbeit besteht darin, vorhandene Bauteile neu zu kombinieren
(Upgrade-Test aus den Deinstallations-Zusagen, arm64 aus dem Runner-Muster anderer
Workflows) und **nicht** darin, Neues zu erfinden. Die einzige echte Neuarbeit sind 149
franzoesische Zeichenketten.

---

## Runtime State Inventory

Diese Phase ist kein Rename, aber sie beruehrt Laufzeitzustand ausserhalb des
Arbeitsbaums, und dieser Zustand entscheidet ueber Erfolg oder Fehlschlag der Abgabe.

| Kategorie | Gefundenes | Erforderliche Handlung |
|-----------|-----------|------------------------|
| **Gespeicherte Daten** | AWS-Volume `vol-04c5b59fe9417babd`: Korpus (50.000 Dateien, ~20 GB), Tantivy-Index (786.506.160 Byte), `vectors.db` (68.695.896 Byte), `state.db`, Docker-Wurzel | Snapshot **vor** dem Abbau (D-03), Verifikation `State=completed` vor `terminate` |
| **Lebende Dienstkonfiguration** | Store-Eintraege `findling` und `findling_backend` auf apps.nextcloud.com mit den Releases 1.0.0 bis 1.0.3, **nach der Abgabe nicht editierbar**. ghcr-Paket `findling_backend` mit den Tags `1.0.0` bis `1.0.3` und `dev` | v1.1.0 als neues Release anhaengen. Das ghcr-Paket muss oeffentlich sein, sonst schlaegt der anonyme Pull beim Nutzer fehl (`docker.yml` nennt den Hinweis) |
| **Vom Betriebssystem registrierter Zustand** | Auf der Box: AppAPI-Registrierung der ExApp, lokale Registry `localhost:5000`, `/etc/hosts`-Pin auf die Apache-Container-Adresse, `/etc/default/grub.d/99-mem4g.cfg`, fstab-Eintrag fuer `/mnt/findling` per UUID | Nach jedem Maschinenstart: `/etc/hosts` neu pinnen (die Adresse wechselt), DI-05-36-disable/enable, harte Grenze pruefen |
| **Geheimnisse und Umgebungsvariablen** | GitHub-Secrets `APPSTORE_TOKEN`, `APP_PRIVATE_KEY`, `BACKEND_PRIVATE_KEY`. AWS-Zugangsdaten in `C:/Users/Student/.findling-aws.env`. SSH-Schluessel `C:/Users/Student/.ssh/findling-loadtest`. Security-Group-Regel Port 22 auf die aktuelle Owner-Adresse | Keine Aenderung. Die SG-Regel zieht `aws_box.sh start` selbst nach (revoke vor authorize) |
| **Bauartefakte** | `findling.tar.gz`, `findling.tar.gz.sig`, `findling_backend.tar.gz`, `findling_backend.tar.gz.sig` sowie `findling.crt` und `findling_backend.crt` im **Repository-Wurzelverzeichnis**, alle mit Mtime 2026-09-07 18:02, also aelter als jeder Commit der Phasen 8 bis 10 | Siehe Open Question 5 |
| **Zustandsdatei** | `C:/Users/Student/.findling-loadtest/box.env`, ausserhalb des Repositoriums, mit der gesamten Kosten- und Schadenshistorie | **Inhalt sichern, bevor `aws_box.sh destroy` sie loescht** |

---

## Common Pitfalls

### Pitfall 1: Nach dem Drei-Stellen-Gate suchen

**Was schiefgeht:** Der Plan sucht das Gate, das README.en.md und beide `info.xml`
deckungsgleich haelt, findet es nicht, und haelt das fuer eine Regression, die zu
reparieren ist.
**Warum:** DI-10-03 und D-06 beschreiben den Zustand vor dem Owner-Entscheid vom
07.09.2026, den Plan 06.1-19 umgesetzt hat.
**Vermeidung:** Der Docstring von `scan_measured_sentence` ist die aktuelle Quelle.
Vor jeder Textarbeit lesen.
**Warnzeichen:** Ein Task, der die Messzahl in eine `info.xml` schreiben will.

### Pitfall 2: Das gefahrene Messskript bearbeiten

**Was schiefgeht:** `98-sprachfaelle.sh` wird an Ort und Stelle korrigiert.
**Warum:** Es liegt unter `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/` und
ist Teil des Belegs; sein Kopf sagt selbst, dass die Fassung dort die gefahrene ist.
**Vermeidung:** Neues Laufverzeichnis, neue Datei, Kopfsatz mit Verweis.
**Warnzeichen:** Ein Diff, der eine Datei unter einem abgeschlossenen Messverzeichnis
anfasst.

### Pitfall 3: Die Container-Adresse nach dem Box-Start

**Was schiefgeht:** Der Poller findet die Warteschlange nicht mehr, alles sieht aus wie
ein Produktdefekt.
**Warum:** Ohne DNS-Zugang steht in `/etc/hosts` der Box ein Pin auf die Adresse des
Apache-Containers, und die wechselt bei **jedem** Maschinenstart (am 07.09. wanderte sie
von 172.18.0.6 auf 172.18.0.4 und hat genau einmal zugeschlagen).
**Vermeidung:** Der Pruefbefehl steht als Kommentar ueber dem Eintrag in `/etc/hosts`.
Vor jeder Messung fahren.
**Warnzeichen:** `vorrat` bleibt stehen, obwohl Dateien da sind.

### Pitfall 4: Der Container indexiert nach dem Start nicht (DI-05-36)

**Was schiefgeht:** Nach jedem Containerstart, der nicht von AppAPI kommt, auch nach
einem Maschinenneustart, indexiert der Container nicht mehr, und zwar stumm.
**Vermeidung:** `occ app_api:app:disable findling_backend && occ app_api:app:enable
findling_backend`. `aws_box.sh start` nennt es als Punkt 4 seiner Nachlese;
`resilience.yml` haelt die Gegenprobe als Zusicherung.
**Warnzeichen:** Kein `pass finished` und kein `armed and the work stock is empty` im
Protokoll.

### Pitfall 5: Die harte Speichergrenze nach einer Registrierung

**Was schiefgeht:** Nach `app_api:app:register` ist die 2-GB-cgroup-Grenze weg, und jede
Messung danach misst gegen keine Grenze.
**Vermeidung:** `docker update --memory=2g --memory-swap=2g`, danach aus der cgroup
zurueckgelesen. Punkt 5 der Nachlese von `aws_box.sh start`.

### Pitfall 6: Der Sweep von `destroy` haelt den Snapshot fuer eine Leiche

**Was schiefgeht:** Der Snapshot traegt `purpose=findling-phase5`, der Sweep meldet ihn,
`destroy` endet mit Exit 1 und die Zustandsdatei bleibt liegen.
**Vermeidung:** Anderer Tag (`purpose=findling-corpus-keep`) oder ein `destroy`, das den
einen erwarteten Ueberlebenden kennt. Abschnitt 8.1.

### Pitfall 7: `destroy` loescht `box.env`

**Was schiefgeht:** Die gesamte Kosten- und Schadenshistorie der Box ist weg.
**Vermeidung:** Inhalt vor dem Abbau in den Phasenbericht uebernehmen.
**Warnzeichen:** Ein Plan, der `destroy` fahren will, ohne vorher `box.env` gelesen zu
haben.

### Pitfall 8: Die deutsche Pluralregel nach Franzoesisch kopieren

**Was schiefgeht:** `fr.json` traegt `nplurals=2; plural=(n != 1);`, und bei n=0 erscheint
die Pluralform, wo Franzoesisch den Singular verlangt.
**Vermeidung:** `nplurals=2; plural=(n > 1);` in `fr.json` und als vierter Parameter von
`OC.L10N.register` in `fr.js`. Gate G4.
**Warnzeichen:** Ein `fr.js`, das per Copy-Paste aus `de.js` entstanden ist.

### Pitfall 9: Ein verlorener Platzhalter in einer Uebersetzung

**Was schiefgeht:** `%1$s in %2$s` wird zu `%s dans %s` oder verliert einen Teil. 29 der
173 Schluessel sind betroffen.
**Vermeidung:** Gate G3, Platzhalter-Parität je Schluessel.
**Warnzeichen:** Ein Wortlaut, der schoener klingt als das englische Original.

### Pitfall 10: Der Tag ohne das Abbild

**Was schiefgeht:** `v1.1.0` steht im Store, aber `ghcr.io/street1983nk/findling_backend:1.1.0`
existiert nicht, und jede Nutzerinstallation scheitert am Pull.
**Warum:** `docker.yml` ist auf `backend/**` pfadgefiltert, und GitHub wendet den Filter
auch auf Tag-Pushes an.
**Vermeidung:** Der Releasecommit beruehrt `backend/appinfo/info.xml`, also greift der
Filter. Trotzdem **vor der Abgabe pruefen**, dass der Manifestindex fuer `1.1.0` mit
beiden Plattformen in ghcr liegt. Der Workflow-Kopf beschreibt den Fall ausdruecklich.

### Pitfall 11: Der Wagenruecklauf im Signierschluessel

**Was schiefgeht:** `openssl_sign` liefert `false`, und Nextcloud stirbt mit
`base64_encode(): Argument #1 ($string) must be of type string, bool given`. Die Meldung
sagt nichts ueber einen Schluessel.
**Vermeidung:** `tr -d '\r'` steht bereits in `release.yml` an beiden Schluesseln, mit
der Laufnummer 33895245084 als Beleg. Nicht wegoptimieren.

---

## Code Examples

### Der Schluesselvergleich fuer zwei Sprachpaare

```python
# Quelle des Musters: backend/tests/test_admin_ui_contract.py,
# test_the_two_translation_files_carry_the_same_keys (Zeile 896).
# Der Ausschnitt aus der .js ist derselbe: das Objekt zwischen der ersten
# geschweiften Klammer und der letzten.
import json
import re
from pathlib import Path

L10N = Path("php/l10n")
_DIRECTIVE = re.compile(r"%(?:\d+\$)?[sdn]|%%")


def _keys(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return set(json.loads(source)["translations"])
    return set(json.loads(source[source.index("{") : source.rindex("}") + 1]))


def test_all_six_catalogues_carry_the_same_keys() -> None:
    """G1. Sechs Dateien, drei Sprachcodes, eine Schluesselmenge.

    Franzoesisch kommt hier als Schluesselvergleich hinzu und NICHT als
    Textvergleich: de und de_DE tragen dieselben Woerter, fr und de tragen
    verschiedene. docs/l10n-french.md, Punkt 3 der Bedingungsliste.
    """
    paths = [L10N / name for name in ("de.json", "de.js", "de_DE.json", "de_DE.js", "fr.json", "fr.js")]
    missing = [p.name for p in paths if not p.is_file()]
    assert missing == [], f"{missing} fehlen, also urteilt dieses Gate ueber weniger als es soll"

    sets = {p.name: _keys(p) for p in paths}
    assert len({frozenset(v) for v in sets.values()}) == 1, f"die Kataloge weichen ab: {sorted(sets)}"
    assert len(sets["de.json"]) == 173


def test_every_french_value_carries_the_placeholders_of_its_key() -> None:
    """G3, der Ersatz fuer die Textgleichheit, die es fuer Franzoesisch nicht gibt.

    Heute betrifft das 29 der 173 Schluessel. Ein verlorenes %2$s ist kein
    Schoenheitsfehler: $l->t() reicht die Werte an vsprintf weiter.
    """
    catalogue = json.loads((L10N / "fr.json").read_text(encoding="utf-8"))["translations"]
    findings = []
    for key, value in catalogue.items():
        forms = value if isinstance(value, list) else [value]
        for form in forms:
            if sorted(_DIRECTIVE.findall(key)) != sorted(_DIRECTIVE.findall(form)):
                findings.append(f"fr.json: {key!r} verliert oder erfindet einen Platzhalter")
    assert findings == []


def test_the_french_catalogue_carries_the_french_plural_rule() -> None:
    """G4. Franzoesisch zaehlt anders als Deutsch: bei n=0 steht der Singular."""
    assert json.loads((L10N / "fr.json").read_text(encoding="utf-8"))["pluralForm"] == "nplurals=2; plural=(n > 1);"
    assert "nplurals=2; plural=(n > 1);" in (L10N / "fr.js").read_text(encoding="utf-8")
```

### Die Fehlschlagzaehlung im Lastwerkzeug (DI-10-01)

```python
# scripts/ops/search_load.py, _one_search. Der Unterschied zum Bestand ist die
# eine Zeile mit min_hits: eine Ergebnisgruppe ohne Containerteil ist bei einer
# Anfrage, die Treffer erwartet, kein Erfolg.
# Beleg: docs/measurements/2026-09-vergleichsmessung-m7g/README.md, Abschnitt 9.3.
    entries = payload.get("ocs", {}).get("data", {}).get("entries")
    if not isinstance(entries, list):
        return (elapsed_ms, 0, "MalformedAnswer")
    if len(entries) < min_hits:
        # HTTP 200 mit leerer Ergebnisgruppe ist die Antwort der OCS-Route auf
        # einen abgebrochenen Containeraufruf. Am 10.09. standen so 17 Abbrueche
        # der Stufe 16 im Nextcloud-Protokoll neben "failures": 0 im Bericht.
        return (elapsed_ms, len(entries), "EmptyResultGroup")
    return (elapsed_ms, len(entries), None)
```

und im Report:

```python
    report["hits_total"] = sum(sample.hits for sample in samples)
    # Der Fingerabdruck ohne Protokoll: 5,40 je Anfrage auf den Stufen 1 und 4,
    # 4,16 auf Stufe 16. Das ist der zweite der beiden Wege aus DI-10-01, und er
    # steht neben dem ersten statt an seiner Stelle.
    report["hits_per_request"] = round(report["hits_total"] / len(samples), 2) if samples else 0.0
```

---

## State of the Art

| Frueherer Stand | Aktueller Stand | Seit wann | Bedeutung fuer Phase 11 |
|---|---|---|---|
| Messsatz an drei Stellen, Gate haelt sie gleich | Messsatz nur in `README.en.md`, Store-Texte sind kurze Faktenlisten | Owner-Entscheid 07.09.2026, umgesetzt in 06.1-19 | Der Merker aus DI-10-03/D-06 ist ueberholt (Abschnitt 6.1) |
| Nur `de`-Katalog | `de` und `de_DE`, vier Dateien, Gate haelt sie textgleich | Phase 9, 09.09.2026 | Die Vorlage fuer das zweite Sprachpaar, aber mit anderer Invariante |
| Nextcloud-Fenster 32-34 | min-version 33, max-version 35 | E-H1, 06.09.2026 | `deploy-harp.yml` faehrt genau 33/34/35, `test_lockstep_versions.py` haelt Fenster und Matrix zusammen |
| Lizenz-Kurzform `agpl` | `AGPL-3.0-or-later` (SPDX) | 06.1-19, 07.09.2026 | Nichts zu tun, beide Haelften sind gleichgezogen |
| Kategorie nur `files` | `search` zuerst, dann `files` | 04.09.2026, gegen die Store-API gemessen | Nichts zu tun |
| T-09-29 `accept` ohne Begruendung | `accept` mit Zahlen, Wiedervorlage bei groesserem Vektorbestand | Phase 10, 10.09.2026 | Abschnitt 7 |
| Nur `:dev` und Commit-SHA in ghcr | Tag-Trigger publiziert genau den Tag, den `image-tag` nennt | Phase 5 | Voraussetzung fuer den Bump auf 1.1.0 |

**Abgekuendigt / ueberholt:**

- `README.md` als englische Fassung: `README.md` ist seit 06.09.2026 deutsch, Englisch
  liegt in `README.en.md`. Der Kommentar an `README = REPO_ROOT / "README.en.md"` in
  `test_store_metadata.py` sagt es.
- Der Pfad `backend/tests/tools/search_load.py` aus 11-CONTEXT.md: das Werkzeug liegt
  unter `scripts/ops/search_load.py`.
- Der Drei-Stellen-Merker, siehe oben.

---

## Assumptions Log

| # | Behauptung | Abschnitt | Risiko, wenn falsch |
|---|-----------|-----------|---------------------|
| A1 | EBS-Snapshot Standardstufe kostet in eu-central-1 rund 0,05 USD/GB-Monat | 8.4 | Gering. D-03 nennt ~1-2 USD/Monat und die Groessenordnung stimmt. Der exakte Wert steht nach dem Snapshot in der Rechnung, der Abfrageweg in `cmd_prices` |
| A2 | Der Snapshot belegt 25 bis 40 GB der 60-GB-Volumengroesse | 8.4 | Gering. EBS-Snapshots bezahlen geschriebene Bloecke; ein Volume, auf dem ein 20-GB-Korpus und ein 786-MB-Index liegen, hat mehr Bloecke beschrieben als sein Dateisystem heute nutzt. Die Zahl ist nach dem Snapshot messbar |
| A3 | Ein arm64-Ast in `deploy-harp.yml` laeuft ohne weitere Anpassung | 5.2 | Mittel. Der HaRP-Digest traegt arm64 nachweislich, das Backend-Abbild wird lokal gebaut, `ubuntu-24.04-arm` ist im Repository etabliert. Ungeprueft ist, ob jedes `apt`-Paket und jede `setup-php`-Version des Jobs auf arm64 vorliegt. **Der erste Lauf ist der Beweis, und ein roter erster Lauf ist ein Befund und kein Rueckschlag** |
| A4 | Die Upgrade-Strecke passt in das `timeout-minutes: 45` eines `deploy-harp`-Astes | 2.4 | Mittel. Deshalb die Empfehlung, sie nur auf `stable34` zu fahren. Die erste gruene Messung ersetzt die Schaetzung |
| A5 | Das Konto `sprachfall` und seine 39 Dateien liegen noch indexiert auf der Box | 4.4 | Mittel. Falls nicht, kostet der Wiederaufbau die 360-s-Frist plus OCR (21 Seiten a rund 3,5 s) plus Indexierung, also grob 20 bis 30 Minuten zusaetzlich. Passt in den 4-h-Deckel, aber die Anfahrtsliste muss den Fall kennen |
| A6 | Die 17 Abbrueche der Stufe 16 sind auf der Box reproduzierbar | 4.4 | Mittel. Sie haengen an der Kaltheit des Wirtscaches. Deshalb ist der Beweis als **Uebereinstimmung zweier Zaehlungen** angelegt und nicht als "es muessen 17 sein" |
| A7 | Der Owner will die Grundlastzahl 103,2 MB in den Texten fuehren | 6.2 | Gering, D-06 sagt es. Aber die Form kollidiert mit der Kurztext-Regel, siehe Open Question 1 |

---

## Open Questions (RESOLVED)

Alle sechs Fragen sind in der Planung der Phase 11 geroutet. Jede traegt
unter ihrer Ueberschrift die Zeile, die sagt, wohin sie gegangen ist.

### 1. D-06 gegen die Kurztext-Regel: wie viele Zahlen darf der Store-Text tragen?

RESOLVED: geroutet nach Plan 11-09, der Text-Checkpoint legt dem Owner beide
Fassungen vor.

**Was wir wissen:** D-06 verlangt, dass in den v1.1-Store-Texten die neuen Messzahlen
fuehren (Grundlast 103,2 MB, anon-Spitze 1.764,2 MB) und die v1.0-Zahlen als datierter
Vergleich danebenstehen, also vier Zahlen. Die Kurztext-Regel des Owners vom 07.09.2026,
woertlich in `CLAUDE.md`: *"Keine Messgeschichten und keine Erzaehlabsaetze; hoechstens
eine Zahl im Text, Details nur als Verweis auf docs/."* Der Code hat die Regel bereits
vollzogen: der Messsatz steht nur noch in `README.en.md`, die `info.xml` tragen die
qualitative Zusage.

**Was unklar ist:** Ob D-06 den Entscheid vom 07.09. aufhebt oder ob "Store-Texte" in
D-06 die READMEs meint, die den Messsatz ohnehin tragen.

**Empfehlung:** Die auslegungsaermere Lesart planen und dem Owner am Text-Checkpoint
beide Fassungen vorlegen:
- Die beiden `info.xml` bleiben unveraendert (kurze Faktenliste, eine qualitative Zusage,
  Verweis auf `docs/`).
- `README.en.md` traegt den fortgeschriebenen Messsatz mit den neuen Zahlen; der
  Vorher-Nachher-Vergleich (691,8 -> 103,2 MB, minus 85 Prozent, Stand 10.09.2026) steht
  darunter als **eine** Zeile mit Datum und Verweis auf den Bericht.
- `README.md` und `README.fr.md` ziehen in derselben Runde nach.

Das erfuellt D-06 der Sache nach (neue Zahlen fuehren, alte datiert daneben), haelt die
Kurztext-Regel dort ein, wo sie nachweislich gemeint war (der Store-Eintrag), und
respektiert D-08 (Vorbehalte nur im Bericht).

### 2. `stable35` mit `tolerate-failure` und D-10

RESOLVED: geroutet nach Plan 11-01 als Vorentscheid V-2; die Umsetzung des
Entscheids liegt in 11-04 (Matrix und Lockstep-Test) und 11-11 (Versionsbump).

**Was wir wissen:** `deploy-harp.yml` traegt am `stable35`-Eintrag einen ausfuehrlichen
Kommentar mit **RE-CHECK DATE: 2026-09-16** und dem Satz: *"Der Plan, der die
Nachverfolgung haelt, ist 06-12, die Store-Einreichung, weil es der naechste Plan nach
diesem Datum ist."* Das ist heute Phase 11. Nextcloud 35 ist am 2026-09-10 noch
Vorabversion: die neueste 35er-Marke ist `v35.0.0rc4` vom 2026-09-10, als Prerelease
gekennzeichnet; die neueste echte Freigabe ist `v34.0.4`. [VERIFIED:
`gh api repos/nextcloud/server/releases`]

**Was unklar ist:** D-10 will so frueh wie moeglich einreichen, moeglicherweise vor dem
16.09. Dann ist die Bedingung fuer das Entfernen der Flagge nicht erfuellt, und der
Kommentar verlangt, dass sie samt Absatz stehen bleibt.

**Empfehlung:** Die Flagge bleibt, wenn die Abgabe vor dem 16.09. laeuft. Der
Phase-11-Plan haelt die Nachverfolgung ausdruecklich fest: **Wiedervorlage am 16.09.**,
und wenn 35.0.0 dann final ist, faellt die Flagge in einer eigenen kleinen Aenderung.
`max-version="35"` bleibt in beiden `info.xml` unveraendert, denn der Ast lief am 07.09.
schon einmal gruen (Lauf 34114937751). **Das braucht eine Owner-Bestaetigung**, weil es
gegen den Wortlaut des Kommentars ein Aufschub ist.

### 3. DI-07-03: bekommt der Nutzer eine Meldung statt einer leeren Liste?

RESOLVED: geroutet nach Plan 11-01 als Vorentscheid V-1; bei v1-a baut der
bedingte Plan 11-13 den Zustand und den Schluessel, bei v1-b wird 11-13
dokumentiert uebersprungen und 11-10 entscheidet den Befund als LOW.

**Was wir wissen:** Auf einer Instanz mit grossem Fremdbestand findet ein Nutzer mit
wenigen Dateien seine eigenen nicht, sobald seine Begriffe im Fremdbestand haeufig sind.
Er bekommt keine Fehlermeldung, sondern eine leere Liste. Die Schleife
(`MAX_ROUNDS = 3` in `php/lib/Search/Provider.php:70`) holt keine zweite Runde nach, auch
wenn der Recheck alle Kandidaten der ersten verworfen hat (gemessen: 1,0 Runde je Suche).
Punkt 5 der Liste "Was dieser Lauf nicht besser gemacht hat".

**Was unklar ist:** Ob das ein MEDIUM-Befund ist, der vor dem Phasenabschluss zu fixen
ist (Owner-Regel 15.08.2026), oder ein LOW, der dokumentiert entschieden wird. Der
naheliegende Fix (mehr Runden, groesseres Kandidatenfenster) fasst den Rechteabgleich an,
und die ROADMAP verbietet das ausdruecklich.

**Empfehlung:** Als **MEDIUM** ins Audit aufnehmen und die Abhilfe von der
Berechtigungskette trennen. Was ohne zweiten Filter geht: die Ergebnisseite und der
Suchdialog unterscheiden "es gab keine Kandidaten" von "es gab Kandidaten, und der
Recheck hat alle verworfen", und im zweiten Fall steht ein Satz statt einer leeren
Liste. Das ist ein Zustand mehr in `SearchOutcome` und ein Katalogschluessel, keine neue
Grenze. **Dem Owner am Checkpoint vorlegen**, weil es ein Zeichenkettenzugang kurz vor
dem FR-Gate ist: jeder neue Schluessel muss in alle sechs Kataloge, und das FR-Gate
liest ihn mit.

### 4. Wird der Messsatz dreisprachig?

RESOLVED: geroutet nach Plan 11-09, Task 2, mit dem Gate ueber drei Wortlaute.

**Was wir wissen:** `README.md` und `README.fr.md` tragen heute nur die qualitative
Zusage, `README.en.md` den vollen Messsatz. Es gibt kein Gate, das die drei READMEs
gegeneinander haelt. `CLAUDE.md` verlangt, dass alle drei gepflegt werden.

**Was unklar ist:** Ob die deutsche und die franzoesische Fassung den Messsatz bekommen
sollen. Dagegen spricht die Kurztext-Regel, dafuer der Gleichbehandlungsanspruch der drei
Sprachen und das FR-Markt-Framing aus 11-CONTEXT.md.

**Empfehlung:** Ja, alle drei, und ein Gate nach dem Muster von
`scan_measured_sentence` mit drei Wortlauten. Das ist eine kleine Aenderung, sie schliesst
eine Luecke, die heute nur eine Regel ist, und sie faellt in dieselbe Textrunde, die D-06
ohnehin verlangt. **Dem Owner am Text-Checkpoint mit vorlegen.**

### 5. Die vier Archive im Repository-Wurzelverzeichnis

RESOLVED: geroutet nach Plan 11-10, Task 3, Herkunft feststellen und
entscheiden.

**Was wir wissen:** `findling.tar.gz` (238.827 Byte), `findling_backend.tar.gz`
(30.976 Byte), `findling.crt`, `findling_backend.crt` liegen im Wurzelverzeichnis, alle
mit Mtime 2026-09-07 18:02, also aus der v1.0.1-Zeit. Erfolgskriterium 5 verlangt: *"die
Release-Artefakte im Repo entsprechen dem, was eingereicht wurde."*

**Was unklar ist:** Ob diese Dateien "die Release-Artefakte im Repo" im Sinne des
Kriteriums sind oder Ueberbleibsel einer Handprobe. Fuer Ueberbleibsel spricht, dass
`release.yml` nach `dist/` schreibt und die Assets an das GitHub-Release haengt; im
Repository liegen sie nirgends. Die `.crt`-Dateien sind oeffentlich und harmlos.

**Empfehlung:** Herkunft feststellen (`git log -- findling.tar.gz`). Sind sie
Ueberbleibsel, gehoeren sie in `.gitignore` und aus dem Baum, und Kriterium 5 ist ueber
die Identitaet von signiertem und eingereichtem Asset erfuellt, wie in Abschnitt 3.3
beschrieben. Sind sie bewusst dort, muessen sie mit dem v1.1.0-Release erneuert werden,
und dann braucht es ein Gate, das ihre Uebereinstimmung mit dem Release haelt, sonst
wiederholt sich das Problem beim naechsten Release. **Kleine Frage, aber sie steht direkt
in einem Erfolgskriterium.**

### 6. Zeitpunkt des Abbaus gegen die Nachvollziehbarkeit der Abgabe

RESOLVED: geroutet nach Plan 11-12, Task 3, der Abbau-Checkpoint stellt die
Frage nach Store-Stand und Wartezeit.

**Was wir wissen:** D-03 setzt den Abbau ans Ende der Phase, nach Abgabe und
Fix-Beweisen. Eine Store-Abgabe kann eine Rueckfrage der Store-Betreiber nach sich
ziehen, und eine abgebaute Box laesst sich in Stunden nicht wiederherstellen.

**Was unklar ist:** Ob der Abbau unmittelbar nach der Abgabe laufen soll oder erst nach
einer Wartezeit.

**Empfehlung:** Der Abbau ist ohnehin ein eigener Plan mit eigener Freigabe. Sein
Checkpoint sollte die Frage stellen: *"Steht v1.1.0 im Store und ist eine Woche ohne
Rueckfrage vergangen?"* Geparkt kostet die Box in dieser Woche 2,19 USD. Das ist billiger
als jede Ueberraschung, und es ist eine Owner-Entscheidung und keine Planannahme.

---

## Environment Availability

| Abhaengigkeit | Gebraucht fuer | Verfuegbar | Version | Ausweichweg |
|---|---|---|---|---|
| `git` | alles | ja | , | , |
| `gh` (GitHub CLI) | Release, Store-Submission-Dispatch, Laufnummern fuer den CI-Beleg | ja, authentifiziert | `gh release list` und `gh run list` liefen | , |
| `python` (System) | Tabellen- und Katalogpruefungen | ja | 3.13, aber global defekt (Projektregel: fuer Python-Aufgaben `uv` nutzen) | `uv run python` |
| `uv` | Backend-Tests, ruff, pyright, vulture | ja | in `backend/` etabliert | , |
| `curl` | Store-API, AWS-Bulk-Preisliste | ja | , | , |
| AWS CLI v2 | Box, Snapshot, Abbau | ja, unter `/c/Program Files/Amazon/AWSCLIV2/aws.exe`; `aws_box.sh` findet sie selbst | , | `AWS_CLI` zeigt darauf |
| AWS-Zugangsdaten | dito | ausserhalb des Repositoriums, `C:/Users/Student/.findling-aws.env` | IAM-User `findling-loadtest`, `AmazonEC2FullAccess` | **Kann `pricing:GetProducts` nicht.** Preise sind in `aws_box.sh` gepinnt |
| SSH-Schluessel der Box | Messblöcke A und B | `C:/Users/Student/.ssh/findling-loadtest` | , | , |
| GitHub-Secrets `APPSTORE_TOKEN`, `APP_PRIVATE_KEY`, `BACKEND_PRIVATE_KEY` | Abgabe | ja, seit 07.09. fuenfmal erfolgreich benutzt | , | keiner, und das ist Absicht |
| GitHub-Runner `ubuntu-24.04-arm` | arm64-Ast (D-02) | ja, in drei Workflows etabliert | , | , |
| DNS-Zugang fuer `loadtest.infranode.dev` | A-Record nach dem Box-Start | **nein** | , | `/etc/hosts`-Pin auf der Box, mit der Falle aus Pitfall 3 |
| Docker lokal | , | nicht noetig | , | Alle Installationstests laufen in CI |

**Fehlende Abhaengigkeiten ohne Ausweichweg:** keine.

**Fehlende Abhaengigkeiten mit Ausweichweg:** DNS-Zugang (`/etc/hosts`-Pin);
`pricing:GetProducts` (gepinnte Saetze plus oeffentliche Bulk-Preisliste).

---

## Security Domain

### Anwendbare ASVS-Kategorien

| ASVS-Kategorie | Gilt | Standard-Kontrolle in diesem Repository |
|---|---|---|
| V2 Authentication | nein | Unveraendert. Ausdruecklich als "nicht beruehrt" ins Audit, nicht weglassen |
| V3 Session Management | nein | Unveraendert |
| V4 Access Control | **ja** | SQLite-ACL-Vorfilter im Container plus finaler PHP-Recheck. Kein Task dieser Phase darf eine zweite Grenze aufmachen. DI-07-03 beruehrt die Frage, nicht die Kette |
| V5 Input Validation / Output Encoding | **ja** | Die 173 FR-Werte gehen durch `$l->t()` ins Template. Escaping-Gate `test_the_page_breaks_none_of_the_checkable_prohibitions`; `SEARCH_QUERY_MAX_CHARS=512`, `SEARCH_QUERY_MAX_DEPTH=32` unveraendert |
| V6 Cryptography | **ja** | Nichts selbst bauen: `openssl dgst -sha512 -sign` und `occ integrity:sign-app`, Verifikation gegen das Zertifikat statt Vertrauen, Fingerabdruck ueber den DER |
| V7 Error Handling / Logging | **ja** | Kein Geheimnis in einer Ausgabe (`_authorization` in `search_load.py` ist die einzige Stelle, an der die Zugangsdaten ueberhaupt vorkommen). Der leere Trefferzustand aus DI-07-03 ist ein Fehlerzustand ohne Meldung |
| V14 Configuration / Build | **ja** | Alle `uses`-Zeilen auf Commit-SHA gepinnt (`test_workflow_pins.py`), `APPSTORE_SHA` in zwei Workflows gleich (von `php.yml` geprueft), HaRP-Digest statt Tag, `wngerman` exakt gepinnt, Basisabbild per Digest |

### Bekannte Bedrohungsmuster fuer diesen Stapel

| Muster | STRIDE | Standard-Abhilfe im Bestand |
|---|---|---|
| Signierschluessel erreicht einen Fork | Elevation of Privilege | `release.yml` hat **keinen** `pull_request`-Trigger, und die Abwesenheit ist ausdruecklich die Hauptverteidigung: ein Trigger, den es nicht gibt, kann kein `if` schwaechen |
| Verschobener Action-Tag = Codeausfuehrung im Job mit beiden Schluesseln | Tampering | Alle Actions auf Commit-SHA gepinnt, `test_workflow_pins.py` haelt die Form |
| Unsigniertes Archiv sieht fertig aus | Spoofing | Die Signierschritte sind eigene Schritte, die **fehlschlagen** koennen, statt Bedingungen, die still uebersprungen werden |
| Archiv wird nach der Signatur neu gebaut | Tampering | Wird nie zweimal gebaut. Das Schwesterprojekt hat den Unterschied auf seinem 0.1.8-Release gemessen (45.710 gegen 45.546 Byte) |
| `--rm-data` loescht ein fremdes Volume | Denial of Service | Der Volumenname leitet sich allein aus der App-Kennung ab. D-02, plus die Instanzzaehlung aus 10-05, die am Repositoriumsnamen und nicht an einem Registry-Pfad haengt |
| Zugangsdaten im Prozesslisting | Information Disclosure | Passwoerter kommen nie als Argument: `OC_PASS` per `--preserve-env`/`-e`, curl per Konfigurationsdatei mit Modus 600, AWS-Zugangsdaten aus der Umgebung. Gate: `test_the_script_of_this_run_puts_no_password_on_a_command_line` |
| Store-Upload mit leerem `info.xml`-Element | Denial of Service (fremd) | Ein leeres Element endet den Upload in einem Serverfehler statt in einer Validierungsmeldung. Gate: `scan_info` in `test_store_metadata.py` |
| Uebersetzung schmuggelt Markup ein | Cross-Site Scripting | V5. Das Template escaped, aber die 173 neuen FR-Werte sollten im Audit einmal auf `<` und `&` durchgesehen werden |
| Snapshot bleibt beim Abbau haengen oder wird mitgeloescht | Denial of Service (eigen) | Abschnitt 8.1, beide Richtungen |

---

## Sources

### Primaer (HIGH confidence), alles am Quellcode dieses Repositoriums

- `backend/src/findling/config.py` (SCHEMA_VERSION, INDEX_VERSION, SEARCH_SCAN_MAX, SEARCH_QUERY_MAX_*)
- `backend/src/findling/index/analyzer.py` (ANALYZER_VERSION), `index/open.py`
  (`expected_versions`, `start_rebuild_on_drift`), `index/wordlist.py`
- `backend/src/findling/store/repo.py` (STORE_SCHEMA_MARK, SCHEMA_VERSION "2")
- `backend/src/findling/embed/model.py`, `embed/engine.py`
- `backend/tests/test_admin_ui_contract.py` (Zeilen 83-120, 896-957), `test_store_metadata.py`
  (Zeilen 102, 163-172, 276-282, 580-650, 694-698, 1020-1072), `test_lockstep_versions.py`,
  `test_ops_scripts.py`, `test_measurement_scripts.py`, `test_store_repo.py`, `test_index_open.py`
- `php/appinfo/info.xml`, `backend/appinfo/info.xml`, `php/lib/Migration/*`,
  `php/lib/Db/QueueMapper.php`, `php/lib/Search/Provider.php`, `php/lib/Service/ExAppService.php`
- `php/l10n/de.json`, `de.js`, `de_DE.json`, `de_DE.js` (173 Schluessel, 29 mit Platzhaltern,
  5 Pluralformen, aus der Datei gezaehlt)
- `.github/workflows/release.yml`, `store-submit.yml`, `docker.yml`, `deploy-harp.yml`,
  `integration.yml`, `php.yml`, `python.yml`, `resilience.yml`, `measure.yml`
- `scripts/ops/aws_box.sh`, `scripts/ops/search_load.py`, `backend/Dockerfile`,
  `backend/pyproject.toml`
- `docs/l10n-french.md`, `docs/store-listing.md`, `docs/certificates.md`,
  `README.md`/`README.en.md`/`README.fr.md`
- `docs/measurements/2026-09-vergleichsmessung-m7g/00-kernaussage.md` und
  `skripte/98-sprachfaelle.sh`
- `docs/audits/2026-09-phase-10/README.md`
- `.planning/phases/10-vergleichsmessung-auf-der-aws-box/deferred-items.md`,
  `.planning/phases/07-gemeinsame-embedding-engine/deferred-items.md`,
  `.planning/phases/10-.../10-07-SUMMARY.md`, `.planning/STATE.md`, `.planning/ROADMAP.md`,
  `.planning/REQUIREMENTS.md`, `CLAUDE.md`
- `C:/Users/Student/.findling-loadtest/box.env`
- `git diff v1.0.3..HEAD` in mehreren Zuschnitten, `git tag -l`, `git log`

### Primaer, externe Feststellungen mit Werkzeug (HIGH)

- `gh release list`, `gh release view v1.0.3 --json assets`,
  `gh run list --workflow=store-submit.yml`, `gh run view 34172689400 --log`
  (HTTP 201 fuer beide Haelften)
- `gh api repos/nextcloud/server/releases` (Stand NC 35: `v35.0.0rc4`, Prerelease,
  2026-09-10; neueste Freigabe `v34.0.4`)
- `curl https://apps.nextcloud.com/api/v1/apps.json?version=34.0.0`
  (findling: 1.0.3, 1.0.2, 1.0.1, 1.0.0 im Store)

### Sekundaer (MEDIUM)

- AWS EBS-Preisseite (regionale Tabelle nicht abrufbar), plus Websuche zur
  Snapshot-Standardstufe. Der reproduzierbare Weg fuer dieses Projekt steht in
  `cmd_prices` und ist die oeffentliche Bulk-Preisliste. Quellen:
  [Amazon EBS pricing](https://aws.amazon.com/ebs/pricing/),
  [Understand billing for Amazon EBS snapshots](https://repost.aws/knowledge-center/ebs-snapshot-billing)

### Tertiaer (LOW), zur Validierung markiert

- Die Schaetzung des belegten Snapshot-Umfangs (25 bis 40 GB). Wird nach dem Snapshot
  durch `describe-snapshots` und die Rechnung ersetzt.

---

## Metadata

**Konfidenz im Einzelnen:**

| Bereich | Stufe | Grund |
|---------|-------|-------|
| Upgrade-Kompatibilitaet (D-04) | **HIGH** | Fuenf Marken einzeln gegen `v1.0.3` diffed, `config.py` mit leerem Diff, Dockerfile-Pin geprueft, Migrationsliste geprueft |
| FR-Katalog: Umfang und Gates | **HIGH** | Schluessel, Platzhalter und Pluralformen aus der Datei gezaehlt; beide Bestandsgates gelesen; `docs/l10n-french.md` gegen die Wortlaute geprueft |
| Release-Pipeline | **HIGH** | Beide Workflows vollstaendig gelesen, fuenf Submissions und vier Releases ueber `gh` belegt, Store-API von aussen bestaetigt |
| Store-Text-Mechanik | **HIGH** | Gate-Quelltext gelesen; der ueberholte Drei-Stellen-Merker ist am Docstring und am einzigen Aufruf belegt |
| Werkzeug-Fixe | **HIGH** | Beide Werkzeuge vollstaendig gelesen, die fehlerhafte Stelle in `_one_search` benannt |
| Haertungsumfang / CI-Abdeckung | **HIGH** | Alle acht Workflows nach Job, Trigger, Runner und Schrittnamen aufgenommen |
| Box-Anfahrt | **HIGH** fuer die Fallenliste (`box.env` und `aws_box.sh` nennen jede beim Namen), **MEDIUM** fuer die Zeitschaetzung |
| EBS-Snapshot | **HIGH** fuer Ablauf und die zwei Fallen (Code gelesen), **MEDIUM** fuer die Kosten |
| DI-07-03-Abhilfe | **LOW** | Der Vorschlag ist plausibel und respektiert die Kette, aber ungebaut und ungemessen. Ausdruecklich Owner-Frage |

**Recherchedatum:** 2026-09-10
**Gueltig bis:** 2026-10-10 fuer die Codebefunde (sie sind an Commit `3bd861d` gebunden
und aendern sich nur mit dem Repository). **2026-09-16 fuer die NC-35-Frage**, weil an
diesem Tag die Wiedervorlage der `tolerate-failure`-Flagge faellig ist.
