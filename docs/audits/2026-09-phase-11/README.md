---
phase: 11-haertung-und-store-einreichung-v1-1
audited: 2026-09-11
diff: 721bde6..HEAD
files_reviewed: 55
findings:
  critical: 0
  high: 0
  medium: 1
  low: 10
  total: 11
status: issues_found
fix_run: pending
fix_commits: pending
fixed: pending
still_open: pending
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

**Was davon an jeden Nutzer geht, weil es im Companion-Archiv liegt:**

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

`scripts/ops/search_load.py` liegt **nicht** im Archiv: es ist ein Messwerkzeug
und wird nicht ausgeliefert. `backend/src/` ist im Diff mit **null** Dateien
vertreten; die Backend-Hälfte ist in dieser Phase nicht angefasst worden.

**Bilanz vorweg:** ein MEDIUM-Befund, in dieser Phase von Plan 11-13 gebaut und
mit Belegstelle geschlossen; zehn LOW-Befunde, davon zwei in diesem Lauf
behoben, vier entschieden und hingenommen, vier mit Zieladresse
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
