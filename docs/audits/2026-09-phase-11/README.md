---
phase: 11-haertung-und-store-einreichung-v1-1
audited: 2026-09-11
diff: 721bde6..HEAD
files_reviewed: 55
findings:
  critical: 0
  high: 0
  medium: 1
  low: 11
  total: 12
status: issues_found
fix_run: 2026-09-11
fix_commits: ab39d37, 2e8502b
fixed: [M-01, L-05, L-06]
still_open: [L-07, L-08, L-09, L-10, L-11]
---

# Phase 11: Security-, Bug- und Performance-Audit

**Umfang:** `git diff 721bde6..HEAD`, 55 Dateien, 46 Commits. Die Aufteilung
nach Verzeichnis, aus dem Diff gezählt:

| Verzeichnis | Dateien | Was darin liegt |
|---|---:|---|
| `docs/measurements/` | 12 | der Bericht der Werkzeug-Anfahrt, 7 Rohdateien, 3 Skripte, der Ablaufplan |
| `.planning/phases/` | 12 | zehn SUMMARY, `11-VORENTSCHEIDE.md`, `deferred-items.md` |
| `php/l10n/` | 6 | `fr.json`, `fr.js` neu; `de.json`, `de.js`, `de_DE.json`, `de_DE.js` um einen Schlüssel gewachsen |
| `backend/tests/` | 5 | `test_admin_ui_contract`, `test_measurement_scripts`, `test_ops_scripts`, `test_store_metadata`, `test_upgrade_compatibility` (neu) |
| `php/lib/` | 4 | `Service/SearchOutcome.php`, `Service/SearchService.php`, `Controller/PageController.php`, `Search/Provider.php` |
| `php/tests/` | 3 | `SearchServiceTest`, `PageControllerTest`, `ProviderTest` |
| `.github/workflows/` | 1 | `deploy-harp.yml` (arm64-Ast, Release-Asset-Modus, Upgrade-Block) |
| einzeln | 12 | `php/templates/search.php`, beide `info.xml`, `scripts/ops/search_load.py`, drei READMEs, `docs/store-listing.md`, `docs/l10n-french.md`, `docs/performance.md`, `STATE.md`, `ROADMAP.md` |

Dieser Bericht ist nach dem Muster von `docs/audits/2026-09-phase-10/README.md`
geschrieben, das seinerseits auf `docs/audits/2026-09-phase-09/README.md` zeigt,
und liegt nach der Owner-Regel vom 15.08.2026 vor dem Phasenabschluss.

**Was `files_reviewed: 55` genau meint**, damit die Zahl nachzählbar bleibt: es
ist `git diff 721bde6..HEAD --name-only | wc -l` zum Zeitpunkt des Audits, also
vor dem ersten Commit dieses Plans. Die Dateien, die das Audit **selbst**
schreibt (dieser Bericht, die `deferred-items.md` der Phase) und die zwei
Workflow-Köpfe seines Fix-Laufs sind darin nicht enthalten und sind auch nicht
ihr eigener Prüfgegenstand. `.github/workflows/deploy-harp.yml` steht schon in
den 55, weil die Pläne 11-04 und 11-07 sie geändert haben.

## Die eine Frage am Anfang, und diesmal mit der anderen Antwort

Das Phase-10-Audit begann mit einer Frage und beantwortete sie mit einem Wort:
ändert diese Phase Produktionscode? Dort lautete die Antwort nein, und der
ganze Bericht ruhte darauf. **Hier lautet sie ja.** Die Prüfung:

```
git diff 721bde6..HEAD --name-only | grep -E '^(php/|backend/src/)'
```

**Ergebnis: 15 Dateien.** Sechs Katalogdateien, vier Klassen unter `php/lib/`,
ein Template, beide `info.xml`-Beschreibungen (nur `php/appinfo/info.xml` fällt
unter den Ausdruck, `backend/appinfo/info.xml` steht daneben) und drei
PHPUnit-Dateien. Damit gilt der tragende Satz des Vorgängerberichts hier
**nicht**, und jede Einordnung weiter unten muss ohne ihn auskommen.

**Was davon an jeden Nutzer geht, weil es im Companion-Paket liegt:**

| Datei | Wie sie den Nutzer erreicht |
|---|---|
| `php/l10n/fr.json`, `php/l10n/fr.js` | neu, serverseitig und im Browser, 174 Werte |
| `php/l10n/de.json`, `de.js`, `de_DE.json`, `de_DE.js` | je ein Wert mehr, der 174. Schlüssel |
| `php/templates/search.php` | serverseitig gerendert, der neue Textzweig |
| `php/lib/Service/SearchOutcome.php` | der fünfte Zustand |
| `php/lib/Service/SearchService.php` | die Vergabe des Zustands |
| `php/lib/Controller/PageController.php` | die Ausnahme von der Nein-nächste-Seite-Regel |
| `php/lib/Search/Provider.php` | nur ein Kommentar, siehe V4 |
| `php/appinfo/info.xml`, `backend/appinfo/info.xml` | die Beschreibung, dreisprachig, mit der neuen Grundlastzahl |

`scripts/ops/search_load.py` liegt **nicht** im Companion-Paket: es ist ein Messwerkzeug
und wird nicht ausgeliefert. `backend/src/` ist im Diff mit **null** Dateien
vertreten; die Backend-Hälfte ist in dieser Phase nicht angefasst worden.

**Bilanz vorweg:** ein MEDIUM-Befund, in dieser Phase von Plan 11-13 gebaut und
mit Belegstelle geschlossen; elf LOW-Befunde, davon zwei in diesem Lauf
behoben, vier entschieden und hingenommen, fünf mit Zieladresse
weitergereicht; kein CRITICAL und kein HIGH.

---

## 1. Sicherheit

Die zutreffenden ASVS-Kategorien dieser Phase sind **V4, V5, V6 und V14**.
**V2 und V3 treffen nicht zu**, und sie stehen hier trotzdem mit einer eigenen
Überschrift, weil das Vorbild es so hält: eine weggelassene Kategorie ist von
einer geprüften nicht zu unterscheiden.

### V2, Authentifizierung: nicht berührt

`git diff 721bde6..HEAD --name-only` nennt keine Datei, die eine Anmeldung
entgegennimmt, prüft oder weiterreicht. Die drei geänderten Klassen unter
`php/lib/` sind ein Wertobjekt (`SearchOutcome`), ein Dienst
(`SearchService`) und ein Controller (`PageController`); im Diff des
Controllers steht genau eine Methode, `nextUrl`, und in ihr keine Annotation,
kein `NoAdminRequired`, kein `PublicPage` und keine Sitzungsabfrage. Die
Diff-Zeilen sind unten unter V4 vollständig zitiert, also ist diese Aussage
nachprüfbar und nicht behauptet.

`search_load.py` meldet sich als echter Nutzer an und tut es weiterhin über
`--password-env`, also über den **Namen** einer Umgebungsvariablen. Der Diff
des Werkzeugs fasst den Anmeldeweg nicht an; er fügt `--min-hits`, den Zähler
`EmptyResultGroup` und zwei Berichtsschlüssel hinzu.

**Urteil V2: nicht berührt.**

### V3, Sitzungsverwaltung: nicht berührt

Keine Datei dieser Phase legt eine Sitzung an, liest ein Cookie, setzt einen
CSRF-Token oder ändert eine Lebensdauer. Der neue Zweig im Template steht
innerhalb der bestehenden Seite und erbt ihre Sitzung; der Umgang mit dem
`Origin`-Kopf, den das Phase-10-Audit an den Messskripten geprüft hat, ist
unverändert, weil `98b-sprachfaelle.sh` und `search_load.py` ihre Anmeldewege
nicht getauscht haben.

**Urteil V3: nicht berührt.**

### V4, Zugriffskontrolle: die Kategorie, die diese Phase entscheiden muss

Die Leitplanke steht in `.planning/ROADMAP.md:25`: *"Die Berechtigungskette
bleibt unverändert (SQLite-ACL-Vorfilter im Container, finaler PHP-Recheck als
Grenze). Keine Phase dieses Milestones darf eine zweite Grenze aufmachen."*
Der Entscheid V-1a vom 10.09.2026 hat Plan 11-13 scharf gestellt, und dieser
Plan hat als einziger der Phase in die Suchkette hineingeschrieben. Die Frage
lautet also nicht, ob etwas geändert wurde, sondern ob das Geänderte eine
Grenze berührt.

**Erstens, der Vorfilter.** `backend/src/` ist im Diff nicht vertreten. Der
SQLite-ACL-Vorfilter im Container ist in dieser Phase nicht angefasst worden,
und zwar nicht "kaum", sondern mit null Dateien.

**Zweitens, die drei Belegzeilen des PHP-Rechecks.** Jede ist am Arbeitsbaum
beziehungsweise am Diff nachgezählt und nicht abgelesen:

| Belegzeile | Prüfung | Ergebnis |
|---|---|---|
| `MAX_ROUNDS` ist unverändert 3 | `grep -n "MAX_ROUNDS" php/lib/Search/Provider.php` | `70: private const MAX_ROUNDS = 3;` und `239: self::MAX_ROUNDS,` |
| `isReadable()` ist die einzige Berechtigungsfrage geblieben | `grep -rn "isReadable" php/lib/` | zwei Treffer, `SearchService.php:337` die Frage selbst, `SearchService.php:201` ein neuer Kommentar darüber |
| `reduceIds` ist nicht angefasst | `git diff 721bde6..HEAD -- php/lib/Service/SearchService.php \| grep -i reduceIds` | keine geänderte Zeile; die Funktion steht unverändert in `SearchService.php:464`, gerufen in `:266` |

Die **einzige** Zeile des `SearchService`-Diffs, die eines der drei Wörter
trägt, ist diese, und sie ist ein Kommentar:

```
+		// the recheck budget stays where it is, isReadable() below stays the one
```

**Drittens, `php/lib/Search/Provider.php`.** Die Datei steht im Diff und ist
deshalb einzeln zu prüfen. Der maschinelle Schnitt:

```
git diff 721bde6..HEAD -- php/lib/Search/Provider.php \
  | grep -E '^[+-]' | grep -vE '^[+-]{3}' | grep -vE '^[+-]\s*//'
```

**Ergebnis: keine Zeile.** Der gesamte Diff dieser Datei besteht aus
Kommentarzeilen; aus "the four reasons" wurde "the five reasons", dazu ein
Absatz, warum der fünfte Grund im Suchdialog keinen eigenen Satz bekommt. Kein
ausführbares Zeichen hat sich bewegt.

**Viertens, was Plan 11-13 tatsächlich hinzugefügt hat.** Ein Zustand und ein
Text, und beides steht hinter der Grenze und nicht in ihr:

- `SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED`, eine Konstante neben vier
  vorhandenen.
- Die Zählvariable `$decided` in `SearchService`, die das bereits vorhandene
  `$consumed` je Seite summiert. Sie liest und entscheidet nichts; das ist
  T-11-51 und ist in `11-13-SUMMARY.md` am Diff belegt.
- Ein Textzweig in `php/templates/search.php` im Leerzustandsblock.
- Eine Ausnahme in `PageController::nextUrl`. Der ganze Eingriff dort:

```
-		if (!$outcome->hasMore || $page >= self::MAX_PAGE || $outcome->failure !== null) {
+		$runFellShort = $outcome->failure !== null
+			&& $outcome->failure !== SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED;
+
+		if (!$outcome->hasMore || $page >= self::MAX_PAGE || $runFellShort) {
```

Das ist eine Aussage über die Weiterblättern-Regel und keine über eine
Berechtigung. Die nächste Seite läuft durch dieselbe Kette wie die erste; ein
Cursor, der eine Grenze umginge, entstünde hier nicht, weil `hasMore` und
`nextCursor` unverändert vom Dienst kommen und die PHPUnit-Zusicherung aus
11-13 genau das festhält ("die nächste Seite bleibt im neuen Zustand
erhalten", `PageControllerTest`).

**Fünftens, DI-07-03 selbst.** Der Befund, der diese Kategorie in die Phase
gebracht hat, ist unten in Abschnitt 4 als **M-01** mit Verdikt geführt.

**Ein Befund dieser Kategorie, mit umgekehrtem Vorzeichen, und er ist neu.**
Der neue Satz sagt dem Nutzer etwas, das die leere Liste ihm nicht gesagt hat.
Das ist gewollt und vom Owner abgenommen, es ist aber ein Kanal über eine
Vertrauensgrenze und gehört deshalb benannt: unten als **L-01**.

**Urteil V4: in Ordnung.** Keine zweite Grenze, keine bewegte Konstante, kein
ausführbares Zeichen im Provider, und die drei Belegzeilen halten.

### V5, Eingabeprüfung und Ausgabekodierung: 174 neue Werte, maschinell durchgesehen

Die neuen Katalogwerte laufen durch `$l->t(...)` und von dort durch `p(...)`
ins Template. Ein Wert mit Markup wäre damit zwar escaped, aber ein Katalog,
der Markup trägt, ist ein Katalog, den jemand als Markup gemeint hat, und das
gehört gesehen und nicht vermutet.

**Die maschinelle Durchsicht**, über beide Dateien und über Schlüssel wie
Werte:

| Datei | Werte | `<` | `>` | `&` | `"` | `'` |
|---|---:|---:|---:|---:|---:|---:|
| `php/l10n/fr.json`, Werte | 174 | 0 | 0 | 0 | 5 | 50 |
| `php/l10n/fr.json`, Schlüssel | 174 | 0 | 0 | 0 | 7 | 0 |
| `php/l10n/fr.js`, Werte | 174 | 0 | 0 | 0 | 5 | 50 |
| `php/l10n/fr.js`, Schlüssel | 174 | 0 | 0 | 0 | 7 | 0 |

**Ergebnis: keine spitze Klammer, kein Ampersand, in keinem der 348 Werte und
in keinem der 348 Schlüssel.** Die beiden Kataloge sind außerdem
Schlüssel-für-Wert gleich (`fr.json == fr.js` als Python-Vergleich der beiden
geparsten Abbildungen: `True`), und ihre Schlüsselmenge ist die von
`php/l10n/de.json` (`True`).

**Die fünf Anführungszeichen sind keine Neuerung dieser Phase.** Sie stehen an
denselben fünf Stellen in `de.json`, kommen aus dem englischen Quellstring und
sind dort Teil des Satzes (`Run "occ findling:index --restart" to rebuild it`,
`Raise the value under "Largest file to read"`, und drei weitere). Sieben
**Schlüssel** tragen sie ebenfalls, darunter `No file contains "%s"`, also der
Kopf des Leerzustands. Alle laufen durch `p($l->t(...))` und werden zu `&quot;`
beziehungsweise bleiben im Textknoten, je nach Stelle.

**Die 50 Apostrophe sind französische Typografie** (`l'index`, `l'entrée`) und
im JSON mit `\'` geschrieben, weil die Werte in einfache
Anführungszeichen gesetzt waren. Sie sind Prosa und kein Markup.

**Platzhalter:** `sorted(re.findall(r'%\d+\$[sn]|%[sn]', schluessel))` gegen
denselben Ausdruck über den Wert, über alle 174 Paare, Pluralformen
eingeschlossen (fünf Werte sind Listen). **Abweichungen: 0.** Ein verlorener
oder erfundener `%1$s` würde `vsprintf` in einen Fehler laufen lassen; das ist
seit 11-08 auch ein Gate (`test_no_french_value_loses_or_invents_a_placeholder`).

**Was welches Gate prüft, und was ausdrücklich nicht.** Diese Trennung gehört
in den Bericht, weil sie die häufigste Fehlannahme dieses Repositoriums ist:

- **Das Escaping-Gate prüft das Template, nicht den Katalog.**
  `scan_template` in `backend/tests/test_admin_ui_contract.py` sucht
  `print_unescaped` und Inline-Skripte in den Seitenquellen; sein Selbsttest
  `test_unescaped_output_in_the_template_is_reported` mutiert `p($l->t(` zu
  `print_unescaped($l->t(`. Ein Katalogwert kommt in diesem Gate nicht vor,
  und das ist richtig so: escaped wird an der Ausgabestelle.
  `grep -c print_unescaped php/templates/search.php` ist 0.
- **Das Dash-Gate liest die Kataloge mit, seit 11-08.**
  `test_no_file_of_the_page_carries_a_dash_or_an_emoji` fährt `scan_prose`
  über die sechs Seitendateien **und** über `L10N_CATALOGUES`, also über alle
  sechs Katalogdateien. Sein Docstring nennt den Grund namentlich: französische
  Typografie bringt Guillemets und Apostrophe mit, die harmlos sind, aber der
  Gedankenstrich ist im Französischen verbreitet und käme mit dem nächsten
  Wortlaut in eine Datei, die vorher kein Gate dieses Repositoriums je gelesen
  hat.
- Dazu aus 11-08: `test_all_six_catalogues_carry_the_same_keys`,
  `test_every_french_value_carries_a_french_wording` und
  `test_the_french_catalogues_carry_the_french_plural_rule`. Die Pluralregel
  in `fr.js` lautet `nplurals=2; plural=(n > 1);`, also die französische und
  nicht die deutsche.

**T-11-40 ist damit bedient**, und zwar mit Zahlen: 348 Werte, 348 Schlüssel,
null spitze Klammern, null Ampersand, fünf geerbte Anführungszeichen, null
Platzhalterabweichungen.

**Urteil V5: in Ordnung.**

### V6, Kryptografie: die Signaturkette, geprüft bevor sie zum fünften Mal benutzt wird

`.github/workflows/release.yml` steht **nicht** im Diff dieser Phase. Die Kette
ist also unverändert, und geprüft wird sie trotzdem, weil Plan 11-11 sie für
die Abgabe benutzt.

| Zusicherung | Belegstelle | Befund |
|---|---|---|
| Kein `pull_request`-Trigger | `release.yml`, `on:`-Block Zeile 30 bis 39 | genau zwei Wege hinein: ein Tag `v[0-9]+.[0-9]+.[0-9]+` und `workflow_dispatch`. Der Kopfkommentar nennt die Abwesenheit ausdrücklich als die primäre Verteidigung der beiden Signierschlüssel und begründet, warum sie einem `if` vorzuziehen ist: ein Trigger, den es nicht gibt, kann von niemandem erreicht und von keiner späteren harmlos aussehenden Änderung geschwächt werden |
| Der Fingerabdruck läuft über den DER des Public Key | `release.yml:224` bis `:225` | `openssl x509 -noout -pubkey \| openssl pkey -pubin -outform DER \| openssl sha256` . Der Kommentar darüber (`:211` bis `:216`) sagt, warum nicht über den PEM-Text: der ist eine Darstellung, die openssl zufällig druckt, und war deshalb auf der Entwicklungsmaschine grün und im Runner rot |
| `tr -d '\r'` steht an **beiden** Schlüsseln | `release.yml:311` (Companion) und `:427` (Backend) | beide Male mit `umask 077` und mit dem Begründungskommentar darüber (`:305`, `:426`): ein unter Windows abgelegtes Geheimnis trägt CRLF, PHPs openssl liest den Schlüssel dann nicht, und der Fehler sagt nichts über einen Schlüssel |
| Verifikation gegen das Zertifikat statt Vertrauen | `release.yml:367` bis `:369` und `:432` bis `:434` | die erzeugte Signatur wird im selben Lauf gegen den aus dem Zertifikat gezogenen Public Key zurückgeprüft, für beide Hälften |

**T-11-42 ist bedient.** Eine Anmerkung, die in diesen Bericht gehört, weil sie
ein Missverständnis vermeidet: das ist die **Release-Signatur** des Store, nicht
eine Herkunftsattestierung des Container-Abbilds. Für das Abbild gilt weiterhin,
was das Phase-10-Audit richtiggestellt hat: `docker.yml` prüft Manifest und
Provenance als **Prüfpfad**, und das Wort "signiert" steht dafür nirgends.

**Urteil V6: in Ordnung, unverändert seit Phase 10.**

### V14, Konfiguration und Bau

**Der neue arm64-Ast.** `deploy-harp.yml` fährt seit Plan 11-04 vier Äste statt
drei: `stable33`/amd64, `stable34`/amd64, **`stable34`/`ubuntu-24.04-arm`** und
`stable35`/amd64 mit `tolerate-failure: true`. Der arm64-Ast läuft mit
`tolerate-failure: false`, ist also eine Zusage und keine Beobachtung. Das
Versionsfenster ist dabei unverändert geblieben, wie Entscheid **v2-a** vom
10.09.2026 es verlangt: beide `info.xml` tragen weiterhin
`min-version="33" max-version="35"`, und `test_lockstep_versions.py` hält
Fenster und Matrixliste in beide Richtungen zusammen.

**Der Release-Asset-Modus.** `deploy-harp.yml` kann die Store-Install-Strecke
aus den Assets eines veröffentlichten Releases speisen (`RELEASE_TAG`,
`inputs.release_tag`, Zeile 289). Der Upgrade-Beweis von Plan 11-07 zieht
darüber beide Hälften der **v1.0.3** und lädt ohne Fallback: schlägt der
Download fehl, bricht der Schritt mit `::error::` ab (`:2447`), statt still auf
einen lokalen Bau auszuweichen. Der Kommentar sagt den Grund: ein
Upgrade-Beweis, der leise von etwas anderem als dem ausgelieferten Bestand
startet, beweist etwas anderes, als er behauptet. Genau **ein** Ast fährt den
Upgrade-Block, und der Workflow begründet das an Ort und Stelle (`:2351`).

**Die Workflow-Pins.** Über alle neun Workflows:

```
grep -rnE '^\s*uses:' .github/workflows/ | grep -vE '@[0-9a-f]{40}'
```

**Ergebnis: acht Zeilen, und alle acht sind dieselbe lokale Composite-Action**
`./findling-src/.github/actions/setup-test-nc`, davon eine in `deploy-harp.yml`
und die übrigen in `integration.yml` und `resilience.yml`. Eine lokale Action
ist kein Dritter: sie liegt im ausgecheckten Baum und kann keinen fremden Tag
verschieben. **Jede Aktion eines Dritten ist auf einen 40-stelligen Commit-SHA
gepinnt**, in allen neun Workflows. `backend/tests/test_workflow_pins.py` hält
die Form. **T-11-43 ist bedient.**

**Der HaRP-Digest als Manifestindex.** `deploy-harp.yml:79`:

```
HARP_IMAGE: ghcr.io/nextcloud/nextcloud-appapi-harp@sha256:603fdf5c...
```

Ein Digest und kein Tag, und ein Manifestindex und keine Architekturhälfte,
weshalb derselbe Wert für den amd64- und den arm64-Ast steht. Das ist die
Feststellung, die den neuen Ast überhaupt erst erlaubt hat.

**Der Versionsbump an drei Stellen ist ein kommender Vorgang und noch nicht
geschehen.** Stand heute:

| Stelle | Wert |
|---|---|
| `php/appinfo/info.xml:113` | `<version>1.0.3</version>` |
| `backend/appinfo/info.xml:136` | `<version>1.0.3</version>` |
| `backend/appinfo/info.xml:230` | `<image-tag>1.0.3</image-tag>` |

`docker.yml:96` bis `:110` prüft auf einem Tag-Lauf, dass der Git-Tag, beide
`<version>` und der `<image-tag>` **übereinstimmen**, und bricht sonst ab. Der
Auslieferungspfad ist damit an dieser Stelle unbeweglich, und das ist der Satz,
den Abschnitt 5 unten für DI-10-05 braucht. Plan 11-11 setzt alle drei Werte in
einem Zug; wer nur einen setzt, bekommt einen roten Tag-Lauf und kein stilles
Release.

**Die Lieferkette, T-11-SC.**

```
git diff 721bde6..HEAD --name-only \
  | grep -E '(pyproject\.toml|uv\.lock|composer\.(json|lock)|package(-lock)?\.json)'
```

**Ergebnis: keine Zeile.** Diese Phase hat kein Paket installiert. Die
Gegenprobe gegen den ausgelieferten Stand, wie der Plan sie verlangt:
`git diff v1.0.3..HEAD -- backend/pyproject.toml` nennt sechs Zeilen (pypdf
6.16.1 auf 6.16.2, striprtf 0.0.32 auf 0.0.33, lxml 6.1.1 auf 6.1.3, ruff
0.16.4 auf 0.16.6) und `backend/uv.lock` 53 Zeilen. **Diese Bewegung gehört
nicht dieser Phase:** sie steht in Commit `0c77b7b`
("chore(deps): bump the python-minor-and-patch group (#6)"), und
`git merge-base --is-ancestor 0c77b7b 721bde6` bestätigt, dass er **vor** dem
Basis-SHA dieser Phase liegt. Vier Patch-Bumps derselben, bereits vorhandenen
Pakete, keine neue Abhängigkeit, kein neuer Name.

**Urteil V14: in Ordnung, mit einem Befund am Artefaktnamen** (L-06 unten, in
diesem Lauf behoben).

---

## 2. Bugs

Anders als in Phase 10 prüft der Bug-Teil hier **ausführbaren Code**, und zwar
den fünften Zustand, seine Vergabe, seine zwei Ausgabewege und das
Messwerkzeug. Für jeden Randfall steht unten, ob er eingetreten ist, wo das
steht, und was ihn beim nächsten Mal fängt.

### Randfall 1: der neue Zustand schlägt eine Feststellung über den Lauf

**Nicht eingetreten, und es gibt sechs Zusicherungen dagegen.** Ein Lauf, der an
der Decke gestoppt hat oder dessen Container geschwiegen hat, hat über den Rest
nicht entschieden; ihm den neuen Zustand zu geben hieße, mehr zu behaupten, als
der Lauf weiß. Die Vorrangkette in `SearchService` lautet deshalb **Decke,
Schweigen, neuer Zustand**, und `SearchServiceTest` fährt sie in beide
Richtungen ("die Decke gewinnt", "das Schweigen gewinnt").

**Was ihn fängt:** die sechs neuen Fälle in `SearchServiceTest`, CI-Lauf
34530207832, Job "PHPUnit over the companion app", `OK (185 tests, 473
assertions)` gegen 177 vorher.

### Randfall 2: der neue Zustand nimmt oder gibt eine nächste Seite falsch

**Nicht eingetreten.** `PageController::nextUrl` nimmt **genau einen** der fünf
Gründe von der Nein-nächste-Seite-Regel aus, statt die Regel umzuschreiben; die
anderen vier verlieren die nächste Seite weiterhin. Der Diff ist oben unter V4
vollständig zitiert, und `PageControllerTest` trägt einen Fall dafür.

**Der Grund, warum die Ausnahme fachlich stimmt:** in genau diesem Zustand
können die eigenen Dateien des Nutzers hinter den fremden liegen, und eine
weggenommene nächste Seite nähme sie ihm dort weg, wo er sie noch finden könnte.

### Randfall 3: der Leerzustand trägt plötzlich ein Banner über sich

**Nicht eingetreten, und der Beweis ist byteweise geführt.** Die drei
Entscheidungszeilen der Phase 9 sind gegen `git show HEAD:` verglichen und nicht
am Diff abgelesen:

```
IDENTISCH $hasError = $silent || $drift || $noHome;
IDENTISCH $hasHint = !$hasError && ($ceiling || $degraded);
IDENTISCH $showEmpty = $hits === [] && (!$hasQuery || (!$hasError && !$hasHint));
```

`$allRejected` steht als eigene Zeile zwischen `$ceiling` und `$hasError` und
geht in keine der beiden Summen ein. Das Gate der Phase 9 gegen den
ungeschützten Leerzustand sieht damit dieselbe Entscheidung wie vorher.
Belegstelle: `11-13-SUMMARY.md`, Abschnitt "Die drei Zeilen der Phase 9,
byteweise".

### Randfall 4: der 174. Schlüssel steht in fünf von sechs Dateien

**Nicht eingetreten.** Plan 11-13 hat ihn in die vier deutschen Kataloge
gesetzt, Plan 11-08 in die beiden französischen, und
`test_all_six_catalogues_carry_the_same_keys` würde jede Lücke rot machen. Die
harte Katalogzahl im Gate steht auf 174, und sie ist in 11-13 gestiegen und
nicht erst in 11-08, weil der Baum zwischen den beiden Plänen sonst rot
gestanden hätte.

Der maschinelle Gegenbeweis dieses Audits: `set(fr.json) == set(de.json)` ist
`True`, und `fr.json == fr.js` ebenfalls.

### Randfall 5: das Lastwerkzeug zählt weiter falsch, nur anders herum

**Eingetreten, in der milden Form, und es ist DI-11-03 unten.** Der Fix von Plan
11-02 zählt seit dem 10.09.2026 eine Ergebnisgruppe mit weniger als
`--min-hits` Treffern als Fehlschlag `EmptyResultGroup`. Die Anfahrt vom
10.09. hat die beiden Zählungen nebeneinandergelegt
(`docs/measurements/2026-09-werkzeugfixe/README.md`, Abschnitt 3):

| Stufe | Werkzeug `EmptyResultGroup` | Protokoll `cURL error 28` | Begriff ohne Treffer | Summe |
|---|---:|---:|---:|---:|
| 16 | 30 | 14 Vorgänge | 16 | 16 plus 14 gleich 30 |
| 8 | 9 | 0 | 8 | 8 plus 0 gleich **8**, einer bleibt offen |
| 1 | 1 | 0 | 1 | 1 plus 0 gleich 1 |

Zwei der drei Stufen gehen exakt auf. **Der Zähler misst also nicht die
Abbrüche, sondern die leeren Antworten**, und das ist mehr, als der Name einem
eiligen Leser sagt. Der Fix ist trotzdem der, der er sein sollte: `min_hits` und
`hits_per_request` stehen jetzt in jeder Rohdatei, also ist die Zahl lesbar
statt stumm. Vorher meldete das Werkzeug `"failures": 0`, während 17 Aufrufe
abbrachen.

**Die eine Anfrage auf Stufe 8, die übrig bleibt**, ist DI-11-02 unten.

### Eine sechste Prüfung, die kein Randfall der Liste war

`git diff 721bde6..HEAD --diff-filter=D --name-only`: **keine Datei ist in
dieser Phase aus dem Baum verschwunden.** Der Diff besteht aus 8.186
hinzugefügten und 189 entfernten Zeilen über 55 Dateien; die 189 entfernten sind
ersetzte Kommentar- und Textzeilen, keine gelöschte Funktion.

---

## 3. Performance

**Diese Phase hat das Erzeugnis nicht neu vermessen, und der Bericht sagt das
statt eine Zahl zu erfinden.** Die Werkzeug-Anfahrt vom 10.09.2026 hatte den
Auftrag, zwei Werkzeug-Fixe zu beweisen, und war auf vier Stunden und 0,50 USD
gedeckelt. Die Zahlen unten sind deshalb die der Vergleichsmessung, hier gegen
ihre Budgets gehalten und um die zwei Kontrollstufen der Anfahrt ergänzt.

| Größe | Gemessen | Budget oder Decke | Marge | Urteil |
|---|---:|---:|---:|---|
| p95 Stufe 1 | 464,3 ms | 2.500 ms | 2.035,7 ms | gehalten |
| p95 Stufe 4 | 1.068,0 ms | 2.500 ms | 1.432,0 ms | gehalten |
| **p95 Stufe 8 (die Zusage)** | **2.125,5 ms** | **2.500 ms** | **374,5 ms** | **gehalten, 85,0 Prozent** |
| p95 Stufe 12 | 3.453,4 ms | 2.500 ms | minus 953,4 ms | gerissen, wie in 06-11 |
| p95 Stufe 16 | 4.446,2 ms | 2.500 ms | minus 1.946,2 ms | gerissen, wie in 06-11 |
| Kaltstart, voller Bestand | 1.838,4 ms (ganze OCS-Anfrage) | 1.501 ms (innerer Aufruf) | siehe DI-07-02 | ein belegter Abbruch |
| Seitenroute A, erste Seite | 0,332 s | `PAGE_REQUEST_TIMEOUT_SECONDS` 1,5 s | 1,168 s | gehalten |
| Seitenroute C, tiefe Seite | 0,333 s | dieselbe | 1,167 s | gehalten |
| Rundenzahl, Alltag | 1,0 Runde, 1,9 Aufrufe, p95 683,6 ms | `BUDGET_SECONDS` 2,5 s | 1,816 s | gehalten |
| Treffer je Anfrage, Stufe 8 | 5,33 (10.09.: 5,25) | kein Budget, Fingerabdruck | | besser |
| Treffer je Anfrage, Stufe 16 | 4,88 (10.09.: 4,16) | kein Budget, Fingerabdruck | | besser |
| Grundlast im Leerlauf | 103,2 MB | 2 GiB harte Grenze | 1.944,8 MB | gehalten |
| anon-Spitze des Laufs | 1.764,2 MB | 2 GiB harte Grenze | 283,8 MB | gehalten |

**Die Konstanten, gegen die hier gerechnet wird**, jede an ihrer Zeile und alle
in dieser Phase unverändert: `ExAppService::REQUEST_TIMEOUT_SECONDS = 1.5`
(`php/lib/Service/ExAppService.php:95`),
`ExAppService::PAGE_REQUEST_TIMEOUT_SECONDS = 1.5` (`:122`),
`Provider::BUDGET_SECONDS = 2.5` (`php/lib/Search/Provider.php:62`),
`PageController::BUDGET_SECONDS = 3.0`
(`php/lib/Controller/PageController.php:131`).

**Was der neue Zustand kostet:** nichts. Er entsteht aus einer Zählvariablen,
die bereits vorhandene Werte summiert, und er löst keinen zusätzlichen
Containeraufruf aus. `MAX_ROUNDS` ist unverändert 3, und die Schleife dreht im
Alltag weiterhin 1,0 Runden.

### Die vier regressiven Laststufen, ausdrücklich entschieden

`.planning/ROADMAP.md:166` weist diese Entscheidung dieser Phase zu, wörtlich:
*"die Entscheidung, ob die Latenzregression der vier Stufen hingenommen oder
untersucht wird (Phase 11, Härtung)"*. Die Zahlen
(`docs/measurements/2026-09-vergleichsmessung-m7g/README.md`, Abschnitt 8):

| Nebenläufigkeit | p95 06-11 | p95 dieser Lauf | Differenz |
|---:|---:|---:|---:|
| 1 | 481,6 ms | 464,3 ms | minus 3,6 Prozent |
| 4 | 1.009,4 ms | 1.068,0 ms | **plus 5,8 Prozent** |
| 8 | 1.915,0 ms | 2.125,5 ms | **plus 11,0 Prozent** |
| 12 | 3.045,4 ms | 3.453,4 ms | **plus 13,4 Prozent** |
| 16 | 3.782,7 ms | 4.446,2 ms | **plus 17,5 Prozent** |

**Entscheidung: hingenommen für v1.1.0, untersucht in der v1.2-Messplanung.**
Als Befund **L-04** geführt. Die Begründung in vier Sätzen, jeder mit seiner
Zahl:

1. **Die Zusage hält.** Sie steht auf Stufe 8 und wird nicht gesetzt, sondern
   abgelesen: 2.125,5 ms gegen 2.500 ms, 85,0 Prozent des Budgets. Die Stufen 12
   und 16 rissen das Budget schon in 06-11, also ist dort keine Zusage gefallen.
2. **Die Reserve schrumpft, und das ist die eigentliche Nachricht**: von 585,0
   auf 374,5 ms. Sie ist im Messbericht als Verschlechterung benannt
   (Abschnitt 19) und in diesem Bericht nicht kleiner gemacht.
3. **Was untersucht werden müsste, entscheidet keine Lesung, sondern eine
   Messung.** Die Reihe wurde auf anderer Hardware gegen einen anderen
   Vektorbestand gefahren (146.171 Chunks gegen 145.854), und der Werkzeugbefund
   DI-10-01 sagt zusätzlich, dass die 4.446,2 ms der Stufe 16 eher zu günstig
   als zu schlecht sind, weil 17 abgebrochene Aufrufe als beantwortet zählten.
   Eine Untersuchung ohne neue Reihe wäre eine Deutung und keine Ursache.
4. **Eine neue Reihe kostet eine Anfahrt.** Dieselbe Nebenbedingung, aus der
   DI-10-04 weitergereicht wird, gilt hier.

**Wiedervorlage:** die v1.2-Messplanung, in derselben Anfahrt wie DI-10-04, und
mit dem korrigierten Zähler aus Plan 11-02, damit die neue Reihe nicht wieder
Abbrüche als Erfolge zählt.

---

## 4. Der MEDIUM-Befund

### M-01 (MEDIUM): der Nutzer sah eine leere Liste, wo Kandidaten da waren und der Recheck alle verwarf (BEHOBEN)

**Das ist DI-07-03.** Er steht seit Plan 07-02 offen, sein Messteil ist am
10.09.2026 geschlossen worden, und die Entscheidung über das Verhalten hat der
Befund selbst dieser Phase zugewiesen.

**Was:** Die Kandidatenschleife über `MAX_ROUNDS = 3` holt keine zweite Runde
nach, auch dann nicht, wenn der Recheck alle Kandidaten der ersten Runde
verworfen hat. Auf einer Instanz mit großem Fremdbestand findet ein Nutzer mit
wenigen Dateien seine eigenen deshalb nicht, sobald seine Begriffe im
Fremdbestand häufig sind. Für **drei von vier** geprüften Begriffen kam die
Datei des fragenden Kontos unter den ersten **2.000** Kandidaten eines
**52.111er** Fremdbestands nicht vor, für `Bescheid` auf Rang 1.925 von 2.000
(`docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/98b-sprachfaelle-diagnose.txt`).
Der Nutzer sah dabei eine leere Liste **und keine Meldung**.

**Warum MEDIUM und nicht LOW:** weil der Owner es so entschieden hat, und die
Einstufung ist Teil des Entscheids und nicht seine Folge. Wörtlich aus
`.planning/phases/11-haertung-und-store-einreichung-v1-1/11-VORENTSCHEIDE.md`,
Abschnitt V-1, Zeile 116:

> **Entscheid 2026-09-10: v1-a.** DI-07-03 wird in v1.1.0 gefixt, als MEDIUM mit
> der von der Berechtigungskette getrennten Abhilfe. Plan 11-13 ist damit scharf
> und fährt in Welle 2. Der Katalog steigt von 173 auf 174 Schlüssel.

Die **Optionskennung ist v1-a**, das **Datum ist der 10.09.2026**, und Zeile 120
derselben Datei hält fest, dass der Owner keinen eigenen Wortlaut genannt hat,
also der Vorschlag des Dossiers wörtlich gilt.

**Die Belegstelle, ohne die `fixed` eine Behauptung wäre:**
`.planning/phases/11-haertung-und-store-einreichung-v1-1/11-13-SUMMARY.md`. Der
Plan ist gefahren und nicht übersprungen; seine Commits:

| Commit | Was |
|---|---|
| `98688f8` | sechs fehlschlagende Fälle für den Lauf, der Kandidaten bekam und keinen behielt |
| `78ed14c` | der Dienst unterscheidet keine Kandidaten von keinem behaltenen |
| `b04a4e0` | die fünfte Konstante in beiden Aufzählungen und zwei neue Fälle |
| `ce5d88f` | die Ergebnisseite sagt den Satz und behält die nächste Seite |
| `3238517` | der 174. Schlüssel in den vier deutschen Katalogen |
| `cf83e4e` | der Baumhash der PHP-Hälfte bekommt eine zweite Zahl |
| `6ca13e1` | die SUMMARY |

**Was der Nutzer seit dem 10.09.2026 liest**, englischer Quellstring und
deutscher Wortlaut beide aus dem Entscheid, byteweise übernommen:

- `Other files contain this word, but none that you may open.`
- `Andere Dateien enthalten dieses Wort, aber keine, die Sie öffnen dürfen.`

Die Überschrift `No file contains "%s"` bleibt unverändert, denn sie ist auch im
neuen Zustand wahr: keine Datei **dieses** Nutzers enthält das Wort. Nur die
Zeile darunter wechselt.

**Die Prüfung dieses Audits, in den beiden Kategorien, in die der Fix fällt:**

- **V4**, oben: die Berechtigungskette ist am Diff unverändert. Drei
  Belegzeilen, dazu der maschinelle Schnitt über `Provider.php`, der keine
  ausführbare Zeile findet.
- **V5**, oben: der 174. Schlüssel läuft durch `p($l->t(...))`, trägt keine
  Prozent-Direktive, keine spitze Klammer und kein Ampersand, steht in allen
  sechs Katalogdateien und ist in der maschinellen Durchsicht der 348 Werte
  enthalten.

**Warum kein Gate gegen den Rückfall fehlt:** acht neue PHPUnit-Fälle halten das
Verhalten (CI-Lauf 34530207832, `OK (185 tests, 473 assertions)`), und die
Katalogzahl 174 steht hart im Gate.

**Status: geschlossen.** Der Befund ist nicht weitergereicht, nicht entschärft
und nicht umgewidmet worden; er ist gebaut.

---

## 5. Die geerbten Befunde und die LOW-Befunde, jeder mit Verdikt

### L-01 (LOW): der neue Satz ist ein Existenz-Orakel über den Fremdbestand (HINGENOMMEN)

**Was:** Vor dem 10.09.2026 sagte die Ergebnisseite dem Nutzer in diesem Fall
nichts. Seither sagt sie ihm, dass **andere** Dateien dieses Wort enthalten. Das
ist ein Kanal über die Vertrauensgrenze Instanz zu Nutzer: ein angemeldetes
Konto kann Begriff für Begriff erfahren, ob irgendein Dokument der Instanz ihn
trägt, auch wenn es kein einziges davon öffnen darf.

**Warum es trotzdem LOW ist, in vier Feststellungen:**

1. **Der Satz nennt nichts Konkretes.** Keine Zahl, kein Dateiname, kein Pfad,
   kein Eigentümer. Das ist T-11-50, und der Blockkommentar in `search.php` sagt
   den Grund: eine Zahl der verworfenen Kandidaten ließe jeden den Ordner eines
   Fremden begriffsweise vermessen.
2. **Der Kanal ist binär und teuer.** Eine Anfrage liefert ein Ja oder ein Nein
   zu einem Begriff, und jede Anfrage kostet einen vollen Suchlauf über den
   Index mit Recheck.
3. **Er steht nur auf der eigenen Ergebnisseite**, nicht im Suchdialog der
   Unified Search. Der Provider bekommt weiterhin eine leere Gruppe und trägt
   den Grund nur in seine Ablaufspur; der Diff dieser Datei ist reiner
   Kommentar.
4. **Der Owner hat den Wortlaut in Kenntnis der Wirkung abgenommen.** Option a
   des Dossiers beschreibt genau diesen Satz, der Entscheid v1-a nennt ihn
   wörtlich, und die Abhilfe wäre, ihn wegzunehmen, also den Entscheid
   umzudrehen.

**Entscheidung: hingenommen, benannt.** Die Alternative, den Satz nur dann zu
zeigen, wenn der Nutzer irgendeine eigene Datei im Index hat, verschiebt das
Orakel und beseitigt es nicht.

**Wiedervorlage:** wenn eine Instanz das Verhalten abschalten will. Dann ist die
Antwort ein Administratorschalter und kein anderer Satz. Nicht vor v1.2.

### L-02 (LOW): DI-07-02, die Aufrufdecke von 1,5 s hält den Kaltstart nicht aus (HINGENOMMEN)

**Die Zahlen**, aus
`.planning/phases/07-gemeinsame-embedding-engine/deferred-items.md`:

| Größe | Wert | Marge zur Decke 1.500 ms | Rohdatei |
|---|---:|---:|---|
| Kaltstart, voller Bestand, 10.09. 14:05:17Z | 1.838,4 ms | minus 338,4 ms | `rohdaten/95-spitze-nachher.txt` |
| Kaltstart, leerer Bestand, 09.09. | 1.550,4 ms | minus 50,4 ms | `rohdaten/95-spitze-vorher.txt` |
| Reproduktion 1, `Bescheid` | 1.598 ms | minus 98 ms | `rohdaten/95b-kaltstart-reproduktion.txt` |
| Reproduktion 2, `Vertrag beenden` | 1.805 ms | minus 305 ms | dieselbe |
| Reproduktion 3, `Kündigung` | 2.468 ms | minus 968 ms | `rohdaten/95c-kaltstart-reproduktion-teil2.txt` |

**Die Methodik-Korrektur, die der Zahl ihre Schärfe nimmt**
(Bericht Abschnitt 9.2, wörtlich): *"Die gemessenen Dauern sind die Dauer der
ganzen OCS-Anfrage. Die Decke von 1.501 ms gilt nur für den inneren
Containeraufruf."* Daraus folgt beides: eine Gesamtdauer über 1,5 s beweist
keinen Abbruch, und eine darunter beweist keinen Nichtabbruch. Die drei
Reproduktionen liegen über 1,5 s und liefern **je sechs Treffer**, weil der
Seitencache des Wirts die Modellgewichte noch hielt.

**Der eine belegte Abbruch**, `2026-09-10T14:05:17Z`, `cURL error 28: Operation
timed out after 1501 milliseconds`, darunter `Findling: backend unreachable`.
Der letzte Containerstart lag 29 Stunden zurück, der Wirtscache war kalt. **Er
trat genau einmal je Containerstart auf und nicht einmal je Anfrage.**

**Die drei Optionen nebeneinander, wie der Befund sie stellt:**

| Option | Wen sie trifft | Beleglage |
|---|---|---|
| Die Decke heben | **jeden Aufruf jedes Nutzers**, und die Unified Search wartet auf jeden Provider. Alle warten länger, um einen Fall zu retten, der je Containerstart einmal auftritt | die Wirkung ist gemessen: der p95 der Stufe 8 steht bei 2.125,5 ms gegen ein Gruppenbudget von 2.500 ms, also ist dort kein Platz für eine höhere Einzeldecke |
| Die Gewichte beim Containerstart vorwärmen | niemanden im Suchweg, kostet Startzeit und Speicher | **ungemessen** |
| Ein eigener Weg für den ersten Aufruf | nur den ersten Aufruf, fügt aber einen zweiten Zeitweg hinzu | **ungemessen** |

**Entscheidung: LOW, hingenommen für v1.1.0.** Die Begründung:

1. **Die Konstante zu heben, ist die einzige gemessene Option, und sie ist die
   teuerste.** Sie kostet jeden Nutzer bei jeder Suche, für einen Fall, der je
   Containerstart einmal auftritt.
2. **Die beiden billigen Optionen sind ungemessen.** Sie in dieser Phase zu
   bauen, hieße, unmittelbar vor der Abgabe Produktionscode im Suchweg auf
   Verdacht zu ändern, ohne eine Box, die das Ergebnis nachmessen könnte.
3. **Der Nutzer ist seit Plan 11-13 auf der Ergebnisseite nicht mehr wortlos.**
   Ein abgebrochener Containeraufruf ist einer der vier alten Zustände und trägt
   dort sein Banner; wortlos bleibt nur der Suchdialog der Unified Search, und
   das ist die bestehende Linie des Produkts.
4. **Die Schwere folgt der Wirkung, nicht der Marge.** Minus 338,4 ms klingen
   nach MEDIUM; gemessen ist davon eine leere Ergebnisgruppe je Containerstart
   bei kaltem Wirtscache.

**Wiedervorlage, als Bedingung und nicht als Datum:** sobald ein Lauf **mehr als
einen** Abbruch je Containerstart belegt, oder sobald eine Messung das Vorwärmen
mit einer Zahl versieht. Beides gehört in die v1.2-Messplanung. Bis dahin bleibt
DI-07-02 in `deferred-items.md` der Phase 7 stehen, jetzt mit diesem Verdikt.

**Kein Test.** Ein Test, der "der erste Aufruf nach einem Containerstart bleibt
unter 1,5 s" prüft, braucht einen kalten Wirtscache und die Modellgewichte auf
Platte. Auf dem Runner wäre er entweder grün ohne die Aussage zu prüfen oder
dauerhaft rot.

### L-03 (LOW): T-09-29, der volle Vektorscan je Anzeigeseite (HINGENOMMEN, ÜBERNOMMEN)

**In Phase 10 entschieden, hier nur übernommen.** `accept` bleibt, mit den
Zahlen: tiefe Seite **0,333 s** gegen erste Seite **0,332 s**, `limit=100`
0,769 s gegen `limit=20` 0,775 s auf demselben Anmeldeweg. Die Begründung ist
eine andere als vermutet: nicht "der Scan ist billig", sondern **"der Scan läuft
einmal je Anfrage und nicht je Seite"**. Seitentiefe und Trefferzahl sind damit
kein Hebel. **Wiedervorlage** bei einem Vektorbestand, der die Größenordnung von
146.171 Chunks deutlich überschreitet. Belegstelle:
`.planning/phases/10-vergleichsmessung-auf-der-aws-box/10-07-SUMMARY.md` und
`docs/audits/2026-09-phase-10/README.md`, Abschnitt 3.

### L-04 (LOW): die vier regressiven Laststufen (HINGENOMMEN)

Oben in Abschnitt 3 entschieden, mit Zahlen, vier Begründungssätzen und der
Wiedervorlage in der v1.2-Messplanung. Hier nur der Verweis, damit die Zeile in
der Bilanz eine Kennung hat.

### L-05 (LOW): DI-10-05, der aufgeschriebene Digest von `:dev` hält nicht (BEHOBEN)

**Was:** `92-wechsel.sh` schrieb am 10.09.2026 `digest-gleich nein`. Plan 10-02
hatte `sha256:eed6a5fc...` aufgeschrieben, gemessen wurde `sha256:78ab61d8...`.
`:dev` ist ein wandernder Zeiger, und der Pfadfilter von `docker.yml` greift
nach `backend/**`, also verschiebt ein Commit, der nur eine Testdatei
hinzufügt, die Zeichenkette, ohne das Abbild inhaltlich zu ändern. Die Frage,
die Phase 10 an Phase 11 gegeben hat, lautete: darf ein Messlauf gegen `:dev`
prüfen, oder muss er gegen einen unbeweglichen Tag laufen?

**Entscheidung, in drei Sätzen, und sie ist vollzogen und nicht nur
beschlossen:**

1. **Der Baumhash ist der Beweis.** `baumhash-gleich ja` sagt, dass die
   gemessenen Bytes die Bytes des Commits sind; ein abweichender Baumhash hält
   einen Lauf an.
2. **Der aufgelöste Digest ist die Notiz.** Er wird festgehalten, damit ein
   späterer Leser dieselben Bytes wieder adressieren kann; ein Digest, der
   gewandert ist, während der Baumhash hielt, ist ein verschobener Tag und kein
   geändertes Abbild.
3. **Ein Messlauf darf deshalb gegen den wandernden Tag `dev` prüfen**, und der
   aufgelöste Digest wird **mitgeschrieben** statt vorher aufgeschrieben. Ein
   vorab gepinnter Digest wird beim nächsten `backend/**`-Push schal, und genau
   so ist DI-10-05 entstanden.

**Warum das die Auslieferung nicht lockert:** der Auslieferungspfad ist ohnehin
unbeweglich. `docker.yml:96` bis `:110` bricht einen Tag-Lauf ab, wenn der
Git-Tag, beide `<version>` und der `<image-tag>` nicht übereinstimmen. Messen
darf einen wandernden Zeiger haben, Ausliefern nicht.

**Vollzogen in:** dem Kopf von `.github/workflows/measure.yml`, als eigener
Absatz mit den drei Sätzen und dem Verweis auf diesen Abschnitt. **Kein
Produktionscode**, kein Schritt geändert, nur der Kommentar, der die Regel
trägt. Die Datei ist danach gültiges YAML (`yaml.safe_load`).

### L-06 (LOW): DI-11-04, zwei Log-Artefakte hießen `harp-logs-stable34` (BEHOBEN)

**Was:** Der Upload-Schritt von `deploy-harp.yml` nannte das Artefakt
`harp-logs-${{ matrix.server-version }}`. Seit Plan 11-04 gibt es zwei Äste mit
`server-version: stable34`, einen auf `ubuntu-24.04` und einen auf
`ubuntu-24.04-arm`, also zwei Artefakte gleichen Namens im selben Lauf: 13.833
Byte und 7.825 Byte im Lauf 34546421219.

**Warum das mehr ist als ein Schönheitsfehler:** der Upgrade-Block läuft auf
**genau einem** Ast, und seit Plan 11-07 liegen die sieben Beweisdateien des
Upgrades (`upgrade-before.json`, `upgrade-after.json`, das Urteil von
`occ upgrade`, das Containerprotokoll und drei weitere) in genau diesem
Artefaktnamen. Wer "das Artefakt harp-logs-stable34" herunterlädt, bekommt mit
gleicher Wahrscheinlichkeit das ohne die Beweisdateien. Das ist die
Repudiation-Klasse: ein Beweis, den man nicht eindeutig adressieren kann, ist
ein halber Beweis, und Erfolgskriterium 2 dieser Phase ruht darauf.

**Entscheidung: der Runner gehört in den Namen, und der Upgrade-Block bekommt
kein eigenes Artefakt.** Die zweite Variante hätte den Beweis von seinen
Nachbardateien getrennt, die zu seiner Lesart gehören (das Containerprotokoll
neben dem Urteil).

**Warum in dieser Phase behoben und nicht weitergereicht:** es ist eine Zeile,
sie betrifft ausschließlich den Namen eines CI-Artefakts, kein Test liest ihn
(`grep -rn "harp-logs"` findet außerhalb von `deploy-harp.yml` nur Prosa), und
Plan 11-11 fährt `deploy-harp.yml` auf dem Release-Tag ohnehin erneut. Es jetzt
zu tun heißt, dass der Lauf der Abgabe eindeutige Artefakte erzeugt.

**Der Preis, benannt statt verschwiegen:** frühere Berichte führen das Artefakt
unter dem alten Namen. Dieser Name bleibt für die Läufe gültig, die ihn
geschrieben haben; der neue gilt ab hier. Der Kommentar am Schritt sagt beides.

**Neue Form:** `harp-logs-${{ matrix.server-version }}-${{ matrix.runner }}`,
also `harp-logs-stable34-ubuntu-24.04` und `harp-logs-stable34-ubuntu-24.04-arm`.

### L-07 (LOW): DI-10-04, die Ursache der Mehrlaufzeit ist eingegrenzt und nicht bewiesen (WEITERGEREICHT)

**Was:** Der Volllauf brauchte 26 h 37 min gegen 18 h 56 min in 06-11, also plus
40,6 Prozent bei einem Mehrbestand von 0,29 Prozent. Zwei Kandidaten stehen
nebeneinander, und die Daten entscheiden nicht zwischen ihnen: die Kopplung der
beiden Spuren (Indexierung minus 30,9 Prozent, Einbettung minus 24,4 Prozent,
im Gleichschritt) und die Zulauf-Lücken (`vorrat=0` in 62 von 325 Lesungen).
Speicherdruck ist ausgeschlossen.

**Entscheidung: dokumentiert weitergereicht.** Die Begründung, mit Zahlen:

1. **Die Frage entscheidet nur eine Messung, und die braucht einen neuen
   Volllauf.** Entweder ein Lauf, der die Einbettung erst nach der Indexierung
   anstößt, oder eine Instrumentierung, die die Wartezeit des Zulaufs
   mitschreibt. Beides ist eine neue Anfahrt: **26 Stunden und rund 3 USD**.
2. **Der Deckel dieser Phase war 4 Stunden und 0,50 USD** (Freigabe der
   Werkzeug-Anfahrt, Plan 11-06). Die Frage passt nicht hinein, und zwar um eine
   Größenordnung.
3. **Der Befund berührt kein Erfolgskriterium.** Er ist eine Frage an den
   Durchsatz und nicht an die Speicheraussage, und er ist in
   `docs/measurements/2026-09-vergleichsmessung-m7g/README.md`, Abschnitt 19.2,
   als Verschlechterung benannt statt weggelassen.

**Ziel: die v1.2-Messplanung**, zusammen mit dem Box-Wiederaufbau-Runbook, weil
die Box seit dem 10.09.2026 angehalten ist und jede Antwort auf diese Frage
zuerst eine Box braucht. Eingetragen in `deferred-items.md` dieser Phase.

### L-08 (LOW): DI-10-02 und DI-11-01, die Vorprüfung misst einen Antwortdeckel und nicht den Bestand (WEITERGEREICHT, NICHT GESCHLOSSEN)

**Dieser Abschnitt führt einen Befund als offen, der als behoben aussehen
könnte, und das ist Absicht.** Plan 11-03 hat die Nachfolgefassung
`98b-sprachfaelle.sh` gebaut, Plan 11-06 hat sie auf der Box gefahren, und der
Fix hat **nicht** getan, wofür er gebaut wurde.

**Der Box-Beweis**, `docs/measurements/2026-09-werkzeugfixe/README.md`,
Abschnitt 4, Rohdateien `rohdaten/05-sprachfaelle.txt` und
`rohdaten/07-fremdbestand-gegenprobe.txt`: die Vorprüfung misst die Zahl der
**Treffer, die die OCS-Route herausgibt**, und die liegt auf dieser Instanz für
**jeden** geprüften Begriff bei exakt **26**, bei Tiefe 64, 200 und 2000
gleichermaßen, und bei exakt 6 bei Tiefe 5. Die Zahl hängt weder am Begriff noch
an der Tiefe: sie ist ein Deckel der Antwort und nicht der Bestand dahinter.
Die Schwelle ist **64** (`MAX_RECHECKS_ABSOLUTE`), also **kann die Messgröße sie
nie überschreiten**, das dreiwertige Urteil bleibt praktisch zweiwertig, und die
Bilanz lautet `6 von 10, davon 0 nicht messbar`, zahlengleich mit der des
10.09.2026.

**Was der Fix gebracht hat, damit die Bilanz ehrlich ist:** drei der vier
Zusagen halten. Jeder Begriff trägt seine Fremdbestandszahl in einer eigenen
Zeile, die Bilanzzeile nennt zwei Zahlen statt einer, und `CI_LAUF` ist
Pflichteingabe, deren Fehlen den Lauf vor dem ersten Fall beendet. Was nicht
hält, ist die vierte.

**Entscheidung: DI-10-02 bleibt offen, DI-11-01 wird mit ihm zusammengelegt.**
Zwei Kennungen für dieselbe Frage wären genau der Widerspruch, den die Audits
dieses Projekts sonst aufschreiben. Die Begründung, warum hier nicht behoben:

1. **Die nötige Änderung ist eine Änderung an der Messgröße und keine Messung.**
   Gezählt gehört die Zahl der Dokumente im Index, die den Begriff tragen, und
   nicht die Zahl der Treffer, die die Route herausgibt. Ob diese Zahl ohne
   Eingriff in die Berechtigungskette überhaupt erhebbar ist, ist offen, und
   genau diese Frage darf in dieser Phase nicht nebenbei beantwortet werden.
2. **Ein Messskript, das während seines eigenen Laufs nachgebessert wird, macht
   jede Zahl daneben unbelegt.**

**Was die Aussage trotzdem trägt:** der Beweis mit eigenem Index liegt in
`integration.yml`, Job `index-search-e2e`, zuletzt Lauf **34530208024**. Dieser
Lauf fährt dieselben zehn Fälle auf einer frischen Instanz ohne Fremdbestand und
ist grün.

**Ziel: ein eigener Plan ohne Box**, in der v1.2-Härtung, zusammen mit der
Frage, wie ein Fremdbestand ohne Eingriff in die Berechtigungskette gezählt
wird. Eingetragen in `deferred-items.md` dieser Phase.

### L-09 (LOW): DI-11-02, eine leere Antwort ohne Protokollspur (WEITERGEREICHT)

**Was:** Auf Kontrollstufe 8 der Werkzeug-Anfahrt bleiben neun Fehlschläge gegen
acht erklärte. Acht gehen auf den Begriff `Mahnung`, der im Lastkorpus keinen
Treffer trägt. Der neunte bleibt offen: das Nextcloud-Protokoll trägt im Fenster
der Stufe 8 und eine Minute darüber hinaus **keine einzige Zeile** der Apps
`findling` oder `app_api`
(`docs/measurements/2026-09-werkzeugfixe/rohdaten/03-nc-protokoll-abbrueche.txt`).
Diese eine Anfrage bekam eine leere Ergebnisgruppe, ohne dass irgendwo ein
Abbruch entstand.

**Die Vermutung, als Vermutung beschriftet:** DI-07-03, also der Befund, der als
M-01 in dieser Phase gebaut wurde.

**Entscheidung: weitergereicht, und zwar ohne Zusatzmessung beantwortbar.** Das
ist die Pointe dieses Eintrags und der Grund, warum er klein bleibt: Plan 11-13
hat genau diesem Fall den Zustand
`SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED` gegeben, der statt einer leeren
Liste einen Satz zurückgibt. Die Box trug diesen Stand am 10.09.2026 nicht, weil
sie seit dem Vortag angehalten war und kein neues Abbild bekommen hat. **Ein
Lauf mit dem neuen Companion beantwortet die Frage von selbst:** trägt die
Antwort den Satz, war es DI-07-03; bleibt sie leer, war es etwas anderes.

**Warum ein einzelner Vorgang kein Befund ab MEDIUM ist:** einer von 80, ohne
Protokollspur, gegen acht erklärte Fälle derselben Stufe. Eine Aussage trägt das
nicht.

**Ziel: der nächste Box-Lauf**, in der v1.2-Messplanung, als eine Zeile im
Ablaufplan und nicht als eigener Messblock.

### L-10 (LOW): DI-11-03, der Zähler unterscheidet leer nicht von abgebrochen (WEITERGEREICHT)

**Was:** `EmptyResultGroup` zählt jede Antwort mit weniger als `--min-hits`
Treffern, gleich ob ein Containeraufruf abgebrochen ist oder ob die Suche
schlicht nichts gefunden hat. Auf Stufe 16 sind das 14 Abbrüche und 16 leere
Suchen in derselben Zahl 30. Der Name legt die erste Lesart nahe, und die
Erwartung E3 des Ablaufplans ist genau daran gescheitert.

**Geprüft, ob es klein und risikofrei genug für diesen Lauf ist. Es ist es
nicht, und der Grund ist technisch und nicht terminlich:** das Werkzeug **kann**
die beiden Ursachen aus seiner eigenen Sicht nicht trennen. Die OCS-Route
antwortet in beiden Fällen mit HTTP 200 und einer Ergebnisgruppe ohne
Containerteil; der Unterschied steht ausschließlich im Nextcloud-Protokoll auf
der anderen Seite. Ein zweiter Fehlschlagname wäre deshalb ein Name ohne
Unterscheidungsmerkmal, also eine Verschlechterung und keine Verbesserung. Die
tragfähige Fassung nennt stattdessen die Begriffe ohne Treffer, und dafür muss
sie den Bestand kennen, gegen den sie läuft.

**Warum es trotzdem kein Rückschritt ist:** `min_hits` und `hits_per_request`
stehen jetzt in jeder Rohdatei, also ist die Zahl lesbar statt stumm. Vorher
meldete das Werkzeug `"failures": 0`, während 17 Aufrufe abbrachen.

**Ziel: die nächste Fassung von `scripts/ops/search_load.py`**, zusammen mit der
v1.2-Messplanung, weil die Entscheidung zwischen den beiden Wegen (ein zweiter
Name gegen eine Zeile im Bericht, die die Begriffe ohne Treffer benennt) einen
Bestand braucht, gegen den sie geprüft wird. Kein Blocker, keine Box.

### L-11 (LOW): der pgsql-Ast von `index-search-e2e` flattert (WEITERGEREICHT)

**Gefunden von diesem Audit selbst**, beim Nachsehen des CI-Stands der Phase.

**Was:** Der Integration-Lauf **34555358815** auf Commit `2838673`, dem letzten
Commit vor diesem Plan, ist **rot**. Rot ist genau ein Job von sieben,
`index-search-e2e (pgsql)`; `sqlite` und `mysql` sind grün, ebenso die fünf
anderen Jobs. Die Fehlerzeile:

```
revision 8 written
curl: (22) The requested URL returned error: 423
```

**423 ist Locked**, also die WebDAV-Sperre von Nextcloud, und sie fällt im
Schritt "Overwrite it eight times while the container is working", der eine
Datei achtmal im Sekundentakt überschreibt, während der Container arbeitet.

**Warum es kein Produktbefund sein kann:** `2838673` ist der Commit
`docs(11-09): die abgenommenen Store-Texte abschliessen` und ändert
ausschließlich `.planning/ROADMAP.md`, `.planning/STATE.md` und
`11-09-SUMMARY.md`. Kein ausführbares Zeichen hat sich gegenüber dem grünen
Vorlauf bewegt.

**Die Gegenprobe, gefahren statt vermutet:** `gh run rerun 34555358815 --failed`
am 11.09.2026. **Ergebnis: success.** In der Geschichte des Workflows ist das
1 roter Lauf auf 13, und die zwölf davor sind grün.

**Entscheidung: hingenommen als Flattern des Messaufbaus, aber mit Zieladresse**,
weil ein roter Integration-Lauf unmittelbar vor dem Release-Tag teuer ist. Der
Schritt schreibt achtmal ohne auf die Sperre zu warten; ein neunter Schreibvorgang
in dieselbe Sperre hinein ist ein Wettlauf, den der Schritt selbst erzeugt.

**Der Merker für Plan 11-11:** geht der pgsql-Ast auf dem Release-Commit rot,
ist die erste Handlung eine Wiederholung und nicht eine Fehlersuche im Erzeugnis.
Erst wenn die Wiederholung ebenfalls rot ist, ist es ein Befund.

**Ziel:** die v1.2-Härtung, als kleiner Schritt am Mutationsblock von
`integration.yml` (auf 423 warten und wiederholen statt blind weiterzuschreiben).

---

## 6. Was ausdrücklich in Ordnung ist

1. **Die Berechtigungskette ist am Diff unverändert**, mit drei Belegzeilen und
   einem maschinellen Schnitt, der im Provider keine ausführbare Zeile findet.
2. **Kein Paket installiert, keine Abhängigkeitsdatei angefasst**, und die
   Gegenprobe gegen `v1.0.3` zeigt vier Patch-Bumps aus einem Commit **vor** dem
   Basis-SHA dieser Phase.
3. **348 Katalogwerte und 348 Katalogschlüssel ohne spitze Klammer und ohne
   Ampersand**, mit null Platzhalterabweichungen, maschinell und mit der Zahl im
   Bericht.
4. **Die Signaturkette ist unverändert und nachgeprüft**, bevor Plan 11-11 sie
   zum fünften Mal benutzt.
5. **Jede Aktion eines Dritten ist auf einen Commit-SHA gepinnt**, in allen neun
   Workflows; die acht Ausnahmen sind dieselbe lokale Composite-Action.
6. **Keine Datei ist in dieser Phase aus dem Baum verschwunden**
   (`--diff-filter=D` ist leer).
7. **Die drei Entscheidungszeilen der Phase 9 stehen byteweise**, gegen
   `git show HEAD:` geprüft und nicht am Diff abgelesen.
8. **Die vier Dateien im Wurzelverzeichnis sind keine Release-Artefakte im
   Repositorium**, und das ist unten belegt statt übernommen.
9. **Der Upgrade-Beweis startet ohne Fallback**: schlägt der Download der
   v1.0.3-Assets fehl, bricht der Schritt ab, statt still lokal zu bauen.
10. **Das Dash-Gate liest seit 11-08 die Kataloge mit**, also auch die Datei,
    die vorher kein Gate dieses Repositoriums je gelesen hat.

### Die vier Dateien im Wurzelverzeichnis, für Erfolgskriterium 5

Erfolgskriterium 5 spricht von den Release-Artefakten. Im Arbeitsbaum liegen
vier Dateien, die danach aussehen, und dieser Bericht stellt fest, was sie sind,
statt es zu vermuten. Geprüft mit `git ls-files --error-unmatch`,
`git log --oneline --all --` und `git check-ignore -v`:

| Datei | `git ls-files` | Commits über diesen Namen | `.gitignore` |
|---|---|---:|---|
| `findling.tar.gz` | **nicht verfolgt** | 0 | `.gitignore:31` `*.tar.gz` |
| `findling_backend.tar.gz` | **nicht verfolgt** | 0 | `.gitignore:31` `*.tar.gz` |
| `findling.crt` | **nicht verfolgt** | 0 | `.gitignore:5` `*.crt` |
| `findling_backend.crt` | **nicht verfolgt** | 0 | `.gitignore:5` `*.crt` |

**Die beiden Musterzeilen sind `*.tar.gz` (Zeile 31) und `*.crt` (Zeile 5).**
Keiner der vier Namen kommt in der Historie **irgendeines** Branches vor. Es
sind Überbleibsel einer Handprobe und nicht "die Release-Artefakte im Repo".

**Die Artefakte, die das Kriterium meint, sind die vier Assets am
GitHub-Release**, und `store-submit.yml` reicht genau deren URLs ein: Zeile 145
baut `https://github.com/${GITHUB_REPOSITORY}/releases/download/${TAG}`, Zeile
146 holt `${base}/${app}.tar.gz.sig` und bricht ab, wenn das Signatur-Asset
fehlt, Zeile 148 sendet `{download: "${base}/${app}.tar.gz", signature: ...}` an
`https://apps.nextcloud.com/api/v1/apps/releases`. Eingereicht wird also eine
URL am Release und nie eine Datei aus dem Arbeitsbaum.

---

## 7. Bilanz und Gate

| Schwere | Zahl | Stand |
|---|---:|---|
| CRITICAL | 0 | |
| HIGH | 0 | |
| MEDIUM | 1 | M-01 (DI-07-03), in dieser Phase von Plan 11-13 gebaut, Belegstelle `11-13-SUMMARY.md` |
| LOW | 11 | L-01 bis L-11, je mit Entscheidung und Wiedervorlage; L-05 und L-06 in diesem Lauf behoben |

**Der Fix-Lauf dieses Audits, 2026-09-11.** Zwei Befunde sind in ihm behoben
worden, beide ohne Produktionscode:

| Befund | Commit | Datei | Was |
|---|---|---|---|
| L-05 (DI-10-05) | `ab39d37` | `.github/workflows/measure.yml` | die drei Sätze zu Baumhash, Digest und `dev` im Kopf, plus der Satz, warum die Auslieferung davon unberührt bleibt |
| L-06 (DI-11-04) | `2e8502b` | `.github/workflows/deploy-harp.yml` | der Runner im Artefaktnamen, mit dem Kommentar, der den alten Namen für die alten Läufe gültig lässt |

M-01 steht in `fixed`, ist aber nicht in diesem Lauf gebaut worden, sondern von
Plan 11-13 am 10.09.2026. Seine sieben Commits stehen in Abschnitt 4; sie hier
noch einmal unter `fix_commits` zu führen, hieße, einen fremden Lauf als eigenen
auszugeben.

**Zu `still_open`, und warum es nicht leer ist.** Fünf Befunde stehen darin:
L-07 (DI-10-04), L-08 (DI-10-02 und DI-11-01), L-09 (DI-11-02), L-10
(DI-11-03) und L-11 (der flatternde pgsql-Ast). **Alle fünf sind LOW**, jeder trägt ein Verdikt, eine Begründung und
eine Zieladresse, und keiner von ihnen ist ein Befund ab MEDIUM. Die Owner-Regel
vom 15.08.2026 verlangt, dass **jeder Befund ab MEDIUM vor dem Phasenabschluss
fällt**; der einzige dieser Phase ist M-01, und er ist gebaut. `still_open`
heißt hier "nicht geschlossen, aber benannt, entschieden und adressiert", und
nicht "übersehen".

**Die fünf geerbten Kennungen, die dieser Bericht entscheiden musste**, jede mit
ihrem Abschnitt:

| Kennung | Verdikt | Abschnitt |
|---|---|---|
| **DI-07-02** | LOW, hingenommen, Wiedervorlage als Bedingung | 5, L-02 |
| **DI-07-03** | MEDIUM, **gefixt** von Plan 11-13, Beleg `11-13-SUMMARY.md` | 4, M-01 |
| **T-09-29** | accept, übernommen aus Phase 10 mit den Zahlen | 5, L-03 |
| **DI-10-04** | dokumentiert weitergereicht, Ziel v1.2-Messplanung | 5, L-07 |
| **DI-10-05** | entschieden **und vollzogen** im Kopf von `measure.yml` | 5, L-05 |

Dazu die vier Befunde, die in dieser Phase selbst entstanden sind: DI-11-01
(mit DI-10-02 zusammengelegt, L-08), DI-11-02 (L-09), DI-11-03 (L-10) und
DI-11-04 (L-06, behoben). **DI-10-02 ist ausdrücklich nicht geschlossen**, und
Abschnitt 5 führt den Box-Beweis dafür, statt den Fix von Plan 11-03 als Erfolg
zu verbuchen.

**Das Audit-Gate der Owner-Regel vom 15.08.2026 ist gefahren.** Diese Phase
ändert Produktionscode, acht geänderte Dateien gehen im Companion-Paket an
jeden Nutzer, die Berechtigungskette ist am Diff unverändert, die 348 neuen
Katalogwerte sind maschinell auf Markup durchgesehen, und kein Befund bleibt
ohne Verdikt.

**Die Gates des Repositoriums, gefahren am 2026-09-11 in `backend/`:**
`uv run python -m pytest -q` (**2020 passed, 15 skipped**, also genau die
Grundlinie), `uv run ruff check .`, `uv run ruff format --check .`,
`uv run pyright` und `uv run vulture src tests --min-confidence 80`, alle ohne
Befund. Dazu die YAML-Prüfung der beiden in diesem Lauf geänderten Workflows.
Kein PHP-Gate nötig: dieser Plan hat keine PHP-Datei angefasst.

### Der CI-Stand nach dem Fix-Lauf

| Workflow | Lauf | Commit | Ergebnis |
|---|---|---|---|
| HaRP deploy | **34557178548** | `4becbbc` | **success**, alle vier Äste (`stable33`/amd64, `stable34`/amd64, `stable34`/arm64, `stable35`/amd64) |
| Integration, Wiederholung des flatternden Jobs | 34555358815 | `2838673` | **success** (L-11) |

**Der Beweis, dass L-06 wirkt, und er ist die Artefaktliste des Laufs
34557178548:**

```
harp-logs-stable34-ubuntu-24.04        13.823 Byte
harp-logs-stable34-ubuntu-24.04-arm     7.826 Byte
harp-logs-stable33-ubuntu-24.04         7.805 Byte
harp-logs-stable35-ubuntu-24.04         7.815 Byte
```

**Vier Namen, vier Artefakte, keine Kollision.** Das große ist das des
amd64-Astes und trägt die sieben Beweisdateien des Upgrade-Blocks; es ist jetzt
an seinem Namen zu erkennen und nicht mehr nur an seiner Größe. Vor diesem Lauf
hießen die ersten beiden gleich.
