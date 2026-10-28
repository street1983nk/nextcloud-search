# 40-03-ABLEITUNG: Die Upgrade-Strecke startet ab v1.5.0

Plan 40-03, REL-06, ROADMAP Phase 40 Erfolgskriterium 2. Jede Zusicherung der Schritte
Store upgrade 0 bis 7, die das Verhalten der Startversion behauptet, ist hier für v1.5.0
aus dem Code von v1.5.0 (Commit 6c953a76) neu abgeleitet. Keine Zusicherung wurde
abgeschwächt: wo eine Saat unter 1.5.0 nichts mehr beweist, tritt eine gleich scharfe
Zusicherung über das Verhalten von 1.5.0 an ihre Stelle, und die Zeile sagt, was sie beweist.

## Vorbedingung (geprüft am 2026-10-28, vor jeder Änderung)

- `gh release view v1.5.0 --json assets`: findling.tar.gz, findling.tar.gz.sig,
  findling_backend.tar.gz, findling_backend.tar.gz.sig vorhanden (dazu die Quell- und
  HEIF-Archive des Releases).
- Image `ghcr.io/street1983nk/findling_backend:1.5.0`: anonymer Manifest-Check gegen die
  Registry-API antwortet HTTP 200 (OCI-Index; Digest laut docs/store-listing.md
  "# Release 1.5.0": sha256:cf805dfa...49d8 mit amd64 und arm64).
- Entscheid v1.5.0 statt v1.5.1: REL-06 nennt v1.5.0; 1.5.1 ändert gegenüber 1.5.0 nur den
  Store-Namen der Companion und zwei Abhängigkeiten, backend/src und jede PHP-Datei sind
  bytegleich. Ein Start auf v1.5.0 beweist damit den Codepfad jeder 1.5.x-Installation.

## Ableitung je Zusicherung

Zitate der Form `datei:zeile` sind per `git show v1.5.0:<datei>` belegt.

| Schritt | Zusicherung (Kurzname, Zeile vorher) | Wert unter v1.4.3 | Wert unter v1.5.0 | Fundstelle im Code von v1.5.0 | Art der Änderung |
|---|---|---|---|---|---|
| 1 | Navigationsblock der Companion (3799) | vorhanden | vorhanden | Release-Archiv v1.5.0, php/appinfo/info.xml trägt `<navigations>` seit v1.1.0 | unverändert (f) |
| 1 | Registrierter Sprachsatz der Startversion | de,en | de,en | backend/appinfo/info.xml:431 (`<default>de,en</default>`) | unverändert |
| 2b | Sidecar `._seed-notes.docx` (4351) | skipped/system_file in beiden Hälften | skipped/system_file in beiden Hälften | backend/src/findling/worker/poller.py:1499 (is_sidecar_name, Reason.SYSTEM_FILE) | unverändert (a) |
| 2b | Graues TIFF (4359) | indexed/, kein Urteil in Nextcloud | indexed/, kein Urteil in Nextcloud | backend/src/findling/extract/image.py:118-124 (Shim für ExtraSamples 0) | unverändert (a) |
| 2b | Saatwort findet genau das Bild (4383) | genau 1 Treffer | genau 1 Treffer | wie oben | unverändert |
| 2b | eml, zip, doc, xls, heic: nie gequeued (4563) | 0 Zeilen in state.db und findling_file_state | indexed/ in state.db, 0 Urteile in findling_file_state | php/lib/Service/StorageService.php:133-157 (ALLOWED_MIMETYPES nennt alle sechs Typen), backend/src/findling/extract/dispatch.py | Saat entfällt mit Ersatz (a): 1.5.0 liest die Typen selbst; die Zusicherung prüft jetzt, dass 1.6.0 die Urteile von 1.5.0 unverändert übernimmt |
| 2b | Word 97 unter .docx (4572) | skipped/legacy_format in beiden Hälften | indexed/, 0 Urteile in Nextcloud | backend/src/findling/extract/cfb.py:122-123 (Stream WordDocument), extract/legacy_doc.py | Saat entfällt mit Ersatz (a) |
| 2b | ZIP-Bombe | nie gequeued (0 Zeilen) | skipped/archive_limit in beiden Hälften | backend/src/findling/extract/archive.py:12-20 (drei Stufen, archive_limit), nc/queue.py:129 (Companion 1.5.0 speichert archive_limit) | neuer Wert (a) |
| 2b | Stale-Datei, feste Ordnung Schritt 5 (4723, 4731) | failed/repeatedly_stuck nach drei kurzen Auslieferungen und zurückdatierten Claims | indexed/ bei der ERSTEN Auslieferung; Logzeilen "download of one file came back short, fetching it once more" (1x) und "the file cache names a stale size, the same N of M bytes arrived twice" (1x), "stayed short twice" 0x, Queue leer | backend/src/findling/worker/poller.py:2010-2041 (POL-02: zweiter Abruf, gleiche Bytezahl und gleicher Hash werden angenommen) | Saat entfällt mit Ersatz (a): gleich scharfe Prüfung über die Annahme-Logzeilen und das Urteil indexed/ |
| 2b | Sieben Wörter nach der Saat (4754) | finden nichts (words_find_nothing) | jedes Wort findet genau seine Datei (words_exact), Positivkontrolle unverändert | wie oben je Format | Saat entfällt mit Ersatz (a) |
| 2b | Ausschluss-Präfix Ausschluss36 (4838-4925) | Form von v1.4.2: Schlüssel `exclusions`, getValueArray, occ als zweiter Schreiber | identische Form | php/lib/Service/ExclusionService.php:236-244 (prefixes), :219 (occ als zweiter Schreiber); php/lib/Listener/FileEventListener.php:441-444 (Verweigerung vor der Queue) | unverändert (e) |
| 3 | Drei Begriffe je genau 1 Datei (5366) | 1/1/1 | 1/1/1 | OCR- und Suchkette unverändert | unverändert |
| 3 | alemanes = 0 (5377) | 0 (Schema 2 ohne body_es) | 0 (Schema 3, aber Registrierung de,en: Feldliste hängt an der Sprachmarke, kein body_es-Feld) | backend/src/findling/index/open.py (Marken aus dem Verzeichnis), info.xml:431 de,en | unverändert (d) |
| 3 | Sprachmarke de,en (5387) | de,en (frisches Verzeichnis gestempelt) | de,en | backend/src/findling/index/open.py:255-261 (stamp der Marken, LANGUAGES_MARK) | unverändert |
| 3 | smlouve/proc = 1/1 (5394) | 1/1 über body_en | 1/1 über body_en | Schema 3 unter de,en füllt body_de/body_en wie Schema 2 | unverändert |
| 3c | recheck_1_4_0 (5553) | done | done (leerer Scan endet in done, auch auf frischer Installation) | backend/src/findling/worker/recheck.py:117, :146 | unverändert (b) |
| 3c | recheck_1_5_0 (5630) | absent (1.4.x kennt die Marke nicht) | done: Teil A läuft in den ersten Runden, Teil B ist der erste Reconcile-Zyklus, den 2b abwartet | backend/src/findling/worker/catchup.py:148-190 (Teil A), worker/reconcile.py:422-431 und :466-471 (Teil B schreibt CATCHUP_DONE) | neuer Wert (b) |
| 3c | Vektorbestand vor dem Upgrade (5541) | stock 0 = Altbestand (Saat der neuen Formate trug keine Vektoren) | stock 0 = Altbestand PLUS Saat; neue Wartebedingung: die sieben indexierten Saatdateien tragen je >= 1 Chunk, recheck_1_5_0 done | backend/src/findling/worker/poller.py (Embedding nach dem Urteil) | verschärft: der ganze Bestand wird eingefroren |
| 3c | Kandidaten des Catch-up im Altbestand (5676) | leer (Bestimmung 31-12) | leer: der Catch-up lief schon auf dem Start; kein Altbestandsurteil ist legacy_format ohne PowerPoint, repeatedly_stuck oder neuer Typ | Scan-Regel unverändert zwischen v1.5.0 und HEAD (git diff leer für catchup.py) | unverändert |
| 3c (neu) | schemaVersion vor dem Upgrade | 2 (nur implizit über Store upgrade 5) | 3, explizite Guard auf upgrade-before.json | backend/src/findling/config.py:58 (SCHEMA_VERSION = 3), index/open.py:256 (SCHEMA_MARK beim Stempeln des frischen Verzeichnisses) | neue Guard (d) |
| 4 | installed_version-Zweig (5807) | 1.4.3 -> 1.5.1/1.6.0, Zweig 1 | 1.5.0 -> 1.6.0, Zweig 1 (Baum trägt 1.6.0 seit plan 40-02) | php/appinfo/info.xml dieses Baums | unverändert (Kommentar neu) |
| 5 | Zähler-Deltas (6340-6348) | docs +7, indexed +7, nextcloud.failed -1, Rest 0 | ALLE 0: beide Marken lesen done, recheck_step und catchup_step kehren auf done sofort zurück, kein Requeue | backend/src/findling/worker/recheck.py:118-119, worker/catchup.py:160-161, worker/reconcile.py (CATCHUP nur unter der Marke reconcile) | neuer Wert (c), exakt verglichen, nie "mindestens" |
| 5 | schemaVersion nach dem Upgrade per Wert (6270) | "2" | "3" | config.py:58, open.py:256 von v1.5.0 | neuer Wert (d) |
| 5 | recheck_1_5_0 (6540) | absent -> done (Gegenprobe des Catch-up) | done -> done (nichts wird nachgeholt) | reconcile.py:466-471 von v1.5.0 | neuer Wert (b) |
| 5 | Stale-Datei nach dem Upgrade (6594) | indexed/ mit 0 Urteilen (durch den Catch-up) | indexed/ mit 0 Urteilen (schon vom Start, bleibt) | poller.py:2036 von v1.5.0 | unverändert im Wert, neue Begründung |
| 5 | Vektorbestand (6515) | stock ohne die acht Saat-IDs == 3c | stock 0 (ganzer Bestand) == 3c | siehe 3c | verschärft |
| 5 | Embedding-Marke, Profil economy, Banner, Driftzeile, Sprachmarke, Czech 1/1, alemanes 0 | unverändert | unverändert | wie bisher | unverändert |
| 5b | 11a-11d Ausschlüsse | Präfix von 1.4.x hält, Muster von 1.5 greift nach einem Vergleichszyklus | identisch; der Präfix wurde vom Start in derselben Form geschrieben | ExclusionService.php:236/527 von v1.5.0 (prefixes/patterns, gleiche Schlüssel) | unverändert (e) |
| 6 | Schemamarke beim Sprachumbau (7445) | 2 vor, 3 nach dem Rebuild | 3 vor und 3 nach dem Rebuild; dass der Rebuild stempelte, beweist die Sprachmarke (nur stamp_after_swap schreibt den neuen Satz in ein bestehendes Verzeichnis) | config.py:58 von v1.5.0 und von HEAD (beide 3) | neuer Wert (d) |
| 7 | Schemamarke Rückweg (7760) | 3/3 | 3/3 | wie 6 | unverändert |

### Antworten auf die Leitfragen

- (a) Urteile der Saat aus 2b unter 1.5.0: Sidecar skipped/system_file (poller.py:1499),
  Bild indexed (image.py:118), die sechs neuen Typen und das Word-97 unter .docx indexed
  (StorageService.php:133, dispatch.py, cfb.py:122, legacy_doc.py), ZIP-Bombe
  skipped/archive_limit (archive.py), Stale-Datei indexed bei der ersten Auslieferung
  (POL-02, poller.py:2010-2041). Die Saat der neuen Formate prüft nicht mehr die
  Nachholung, sondern dass 1.6.0 die Urteile von 1.5.0 unverändert übernimmt.
- (b) Marken in 3c: recheck_1_4_0 done (recheck.py:146, leerer Scan endet in done) und
  recheck_1_5_0 done (catchup.py:190 setzt reconcile, reconcile.py:469 schreibt done am
  Ende des ersten Zyklus, den 2b abwartet). 3c wartet mit dem Budget des Drains darauf.
- (c) Zähler-Deltas in 5: unter einem Start, der schon 1.5 ist, bewegt das Upgrade keinen
  Zähler, kein Urteil, keinen Vektor und keine Marke; die Form der Zusicherung ist die der
  Zeit v1.4.2 -> v1.4.2 (jeder Schritt 0, exakt verglichen).
- (d) schemaVersion: eine Neuinstallation von 1.5.0 stempelt 3 (config.py:58,
  open.py:256), das Upgrade lässt 3 stehen (kein Rebuild unter de,en), Store upgrade 6
  baut 3 -> 3, Store upgrade 7 bleibt 3/3. Für alemanes folgt: 0 vor und nach dem
  Upgrade, weil die Feldliste an der Sprachmarke de,en hängt und nicht an der
  Schemageneration.
- (e) Ausschlussliste: v1.5.0 schreibt und liest Präfixe und Muster in derselben Form wie
  v1.4.2 und wie HEAD (Schlüssel exclusions/exclusion_patterns, getValueArray; git diff
  v1.5.0..HEAD für ExclusionService.php ist leer).
- (f) Navigationseintrag-Prüfung in Store upgrade 1 bleibt: v1.5.0 trägt den Block.

## ::error::-Guards je Schritt (vorher/nachher)

Zählung: `grep -c '::error::'` über den Zeilenbereich des Schritts.

| Schritt | vorher | nachher | Anmerkung |
|---|---|---|---|
| 0 | 0 | 0 | |
| 1 | 2 | 2 | |
| 2 | 2 | 2 | |
| 2b | 35 | 36 | kein Schritt kleiner; Ersatz je entfernter Guard siehe unten |
| 3 | 4 | 4 | |
| 3b | 4 | 4 | |
| 3c | 13 | 15 | neu: schemaVersion-3-Guard und Vektor-Guard der sieben Saatdateien |
| 4 | 15 | 15 | |
| 5 | 35 | 35 | |
| 5b | 12 | 12 | |
| 6 | 32 | 32 | |
| 7 | 15 | 15 | |

Ersatz je entfernter Guard (Schritt, was die Ersatzzeile prüft):

- 2b: die drei Guards der alten Give-up-Ordnung (Zeilen 4714/4723/4731: Queue-Zeile nach dem
  Zurückdatieren, kein failed/repeatedly_stuck im Budget, genau drei kurze Auslieferungen)
  sind ersetzt durch drei gleich scharfe Guards der Annahme-Ordnung: kein indexed/ im Budget
  (POL-02-Regelverstoß), Logzeilen-Verhältnis `short:accepted:stuck != 1:1:0` oder Queue-Zeile
  übrig, und die Endprüfung `restored/stale/stale_recorded/left` (wahre Größe, indexed, kein
  Urteil, keine Queue-Zeile). Die Guard der sechs "nie gequeued"-Typen (4563) ist ersetzt
  durch die Guard "indexed/ mit 0 Urteilen" je Datei; die Guard des Word-97 (4572,
  legacy_format) durch dieselbe indexed-Guard plus die neue Bomben-Guard
  (skipped/archive_limit in beiden Hälften). words_find_nothing nach der Saat (via 4475) ist
  ersetzt durch die words_exact-Guard (jedes Wort genau seine Datei) plus Positivkontrolle.
- 5: die zwei ::error::-Zweige des entfernten moved()-Helpers (unlesbarer Vorher-Wert,
  Bewegung ungleich dem Schritt) sind ersetzt durch die zwei Zahlen-Guards über alle acht
  Zähler je Snapshot-Seite (`all(type == "number")` auf before und after); die Bewegung
  selbst fängt unchanged() je Zähler mit eigener Fehlerzeile.

## Zusicherung 12: die Änderungen von 1.6 überleben das Upgrade (Task 2)

Fünf Teile; die vier lesenden stehen am Ende von Store upgrade 5 (Block "--- 12"),
der eine schreibende (Teil 2) in Store upgrade 5b hinter dessen Regelschreibung,
weil Store upgrade 5 nichts tut, was ein Admin tun würde (SC4,
test_the_assurance_step_does_nothing_an_admin_would_do).

1. coverage.deduplicated und coverage.rulesPending als Boolesche Werte in der
   Übersicht (AdminViewService.php:1998/2001), rulesPending vor jeder
   Regeländerung über die Route false.
2. rulesPending true nach einer Regeländerung: NICHT über occ (der Weg von 5b),
   sondern über POST /admin/rules. Begründung der Abweichung vom Planwortlaut:
   rules_changed_at wird allein von der Route gestempelt
   (SettingsController.php:466 ruft rememberRulesChange nach wirklich
   geändertem Satz), occ config:app:set ist der dokumentierte zweite Weg in die
   Schlüssel, der nie durch die Route läuft (SettingsService.php:316); ein
   occ-Weg könnte den Hinweis nur per Hand-Stempel fälschen. Der POST nutzt das
   App-Passwort und den OCS-APIRequest-Header (derselbe Weg wie overview.sh),
   setzt den Satz in Kraft plus einen Präfix eines nicht existierenden Ordners
   (NieVorhanden40) und nimmt ihn mit einem zweiten POST zurück; die Liste
   liest danach wieder UPGRADE_EXCLUSIONS_BEFORE, Schritte 6 und 7 starten
   unverändert (kein späterer Schritt liest coverage.rulesPending, und der
   Sweep eines Präfixes ohne Dateien räumt nichts).
3. Der installierte de-Katalog zeichengleich zu php/l10n/de.json des Commits
   (jq --slurpfile, kein Literal im Workflow); die drei Sätze von Plan 39-01
   hält backend/tests/test_phase40_audit.py (COVERAGE_SENTENCES) im selben Baum
   fest, sodass eine Umformulierung in 40-04 Test und Katalog gemeinsam bewegt.
4. indexedLeftOut/embeddedLeftOut: im Container über dasselbe report()
   gefragt, das die Route ruft (api/status.py:753), indexedLeftOut gleich der
   Zahl der lebenden indexierten Dokumente der Home-Storage aus state.db im
   selben Zugriff, ohne leaveOut fehlen beide Felder (exclude_if,
   api/status.py:423).
5. Version001600 lief wirklich: Zeile in oc_migrations; backend_app_version
   las vor occ upgrade die Startversion (von den Übersichtsabrufen der
   Schritte 3/3c geschrieben), war unmittelbar danach leer (die Migration
   löscht den Schlüssel), steht nach dem ersten Übersichtsabruf von Schritt 5
   auf der neuen Version, und eine Suche als Nutzer liefert Treffer ohne die
   Logzeile "the two halves report different versions".

Store upgrade 5 heißt seit Task 2 "the eleven assurances after the upgrade"
(1 bis 10 plus 12; 11 ist Store upgrade 5b). Der Zähler-Stichprobenname in
test_cert_rotation_steps.py folgt dem Namen.

## Probe-Läufe auf gsd/40-03-probe

- Task 1 (Kopf c08d4daa, Umbau auf v1.5.0): HaRP deploy Lauf **40776866858**,
  conclusion success, alle vier Matrixzeilen grün: deploy-harp (stable33, 8.2, false,
  ubuntu-24.04), (stable34, 8.2, false, ubuntu-24.04), (stable34, 8.2, false,
  ubuntu-24.04-arm), (stable35, 8.3, false, ubuntu-24.04). Daneben Integration,
  Python gates und Resilience success auf demselben Kopf.
- Task 2, Iteration 0 (Kopf 0bdd6b71): HaRP deploy Lauf **40780234240**, conclusion
  failure. Genau eine rote Zusicherung, Teil 4 von Zusicherung 12 auf stable34 amd64:
  "nextcloud.log carries 2 drift line(s)". Ursache (kein Befund gegen 1.6): die beiden
  Lockstep-Proben des Entwickler-Passes (deploy-harp.yml, lockstep-newer um Zeile 2154
  und lockstep-older um Zeile 2196) treiben vor dem Upgrade absichtlich eine
  Versionsdrift und suchen hindurch, jede schreibt genau eine Zeile "the two halves
  report different versions" in nextcloud.log. Die Zusicherung verlangte null über das
  ganze Log statt "keine NEUE Zeile nach dem Upgrade". Korrektur ohne Abschwächung:
  Store upgrade 4 zeichnet den Zählerstand am Ende des Upgrades auf
  (UPGRADE_DRIFT_LINES_AT_UPGRADE), Teil 4 verlangt den identischen Stand nach der
  Suche; alle übrigen Teile von Zusicherung 12 und alle elf Zusicherungen davor waren
  in dem Lauf grün (drei andere Matrixzeilen success; Python gates, Integration,
  Resilience auf dem Kopf success).
- Task 2, Iteration 1: wird nach dem Lauf ergänzt.

## Mechanisches Inventar (Ausgangsstand 46df0ee1, 147 Treffer)

`grep -nE "UPGRADE_FROM_TAG|recheck|schemaVersion|1\.4\."` je Schrittbereich von
Store upgrade 0 bis 7. Jede Fundstelle eine Zeile; die Zeilennummern sind die des
Ausgangsstands.

| Schritt | Zeile | Treffer | Art | Entscheid |
|---|---|---|---|---|
| 0 | 3725 | `echo "apps/findling still exists, so the ${UPGRADE_FROM_TAG} archive would be laid over the files...` | Meldung | bleibt; die Variable folgt dem Tag |
| 1 | 3738 | `# of UPGRADE_FROM_TAG at the top of this file, where the reason for its` | Kommentar | bleibt (allgemeine Erklärung des Tags) |
| 1 | 3740 | `base="https://github.com/${GITHUB_REPOSITORY}/releases/download/${UPGRADE_FROM_TAG}"` | Wert | bleibt; die Variable folgt dem Tag |
| 1 | 3753 | `echo "::error::${url} could not be loaded, so there is no ${UPGRADE_FROM_TAG} installation to upg...` | Zusicherung | bleibt; die Variable folgt dem Tag |
| 1 | 3787 | `# UPGRADE_FROM_TAG really points at a release this proof understands.` | Kommentar | bleibt (allgemeine Erklärung des Tags) |
| 1 | 3794 | `# UPGRADE_FROM_TAG was v1.1.0 and 1.1.0 was the first release with the` | Kommentar | bleibt (allgemeine Erklärung des Tags) |
| 1 | 3800 | `echo "the companion of ${UPGRADE_FROM_TAG} declares no navigation entry, so this is older than v1...` | Meldung | bleibt; die Variable folgt dem Tag |
| 1 | 3803 | `echo "the companion of ${UPGRADE_FROM_TAG} declares the navigation entry, as every release since ...` | Meldung | bleibt; die Variable folgt dem Tag |
| 1 | 3817 | `# UPGRADE_FROM_TAG again does this check again, because a tag without` | Kommentar | bleibt (allgemeine Erklärung des Tags) |
| 1 | 3829 | `echo "the ${UPGRADE_FROM_TAG} registration created no running container"` | Meldung | bleibt; die Variable folgt dem Tag |
| 1 | 3835 | `echo "the ${UPGRADE_FROM_TAG} registration created no volume, and an upgrade that keeps nothing p...` | Meldung | bleibt; die Variable folgt dem Tag |
| 1 | 3840 | `echo "the ${UPGRADE_FROM_TAG} installation runs as ${container} on the volume ${volume}"` | Meldung | bleibt; die Variable folgt dem Tag |
| 2 | 3860 | `# ${UPGRADE_FROM_TAG}, into a schema that carries no body_es field at` | Kommentar | bleibt (allgemeine Erklärung des Tags) |
| 2 | 4073 | `# The seed of the recheck, and why it has to exist at all (plan 29-11).` | Kommentar | Kommentar: Geschichte bleibt, neuer Absatz für 1.5.0 daneben |
| 2 | 4075 | `# 1.4.0 judges two classes of issues #18 and #22 differently from 1.3.2.` | Kommentar | Kommentar: Geschichte bleibt, neuer Absatz für 1.5.0 daneben |
| 2 | 4080 | `# books both as failed(corrupt). The recheck of D-29-10 (plan 29-09) is` | Kommentar | Kommentar: Geschichte bleibt, neuer Absatz für 1.5.0 daneben |
| 2 | 4109 | `# same two files plan 29-11 sowed for the recheck of D-29-10, an` | Kommentar | Kommentar: Geschichte bleibt, neuer Absatz für 1.5.0 daneben |
| 2 | 4111 | `# 1.4.2 judges both rightly the first time, measured in the code of the` | Kommentar | Kommentar: Geschichte bleibt, neuer Absatz für 1.5.0 daneben |
| 2 | 4113 | `# the first byte (backend/src/findling/worker/poller.py:1480 of v1.4.2,` | Kommentar | Kommentar: Geschichte bleibt, neuer Absatz für 1.5.0 daneben |
| 2b | 4201 | `# The question _is_due of 1.4.2 asks (worker/reconcile.py:645-653):` | Kommentar | Kommentar der Probe: Zitat auf v1.5.0 reconcile.py:897 umgestellt |
| 2b | 4210 | `# written out, because the container asked here runs 1.4.2.` | Kommentar | Kommentar der Probe: Zitat auf v1.5.0 reconcile.py:897 umgestellt |
| 2b | 4291 | `# the Word reader of 1.3.x failed on it (#22); 1.4.2 skips it by name.` | Kommentar | Kommentar: Geschichte bleibt (Urteil identisch unter 1.5.0, poller.py:1499) |
| 2b | 4337 | `echo "::error::the ${UPGRADE_FROM_TAG} container did not judge both seed files within UPGRADE_DRA...` | Zusicherung | bleibt; die Variable folgt dem Tag |
| 2b | 4346 | `# 1.4.2, and "Store upgrade 5" demands them unchanged after the` | Kommentar | bleibt |
| 2b | 4352 | `echo "::error::the sidecar is '${sidecar}' in state.db and '${sidecar_recorded}' in findling_file...` | Zusicherung | bleibt; die Variable folgt dem Tag |
| 2b | 4360 | `echo "::error::the picture is '${tiff}' in state.db with ${tiff_recorded} verdict(s) in findling_...` | Zusicherung | bleibt; die Variable folgt dem Tag |
| 2b | 4383 | `echo "::error::the seed word brings back ${hits} file(s) on the ${UPGRADE_FROM_TAG} installation ...` | Zusicherung | bleibt; die Variable folgt dem Tag |
| 2b | 4392 | `echo "sown: a picture indexed and a sidecar skipped(system_file) under ${UPGRADE_FROM_TAG}, and t...` | Meldung | bleibt; die Variable folgt dem Tag |
| 2b | 4412 | `# its own, and a small ZIP bomb without one. What 1.4.2 makes of` | Kommentar | Kommentar: neu abgeleitet, 1.5.0 liest die sechs Typen selbst (StorageService.php:133) |
| 2b | 4428 | `# listener of 1.4.2 is what decides about them; the stale file` | Kommentar | Kommentar: neu abgeleitet, 1.5.0 liest die sechs Typen selbst (StorageService.php:133) |
| 2b | 4475 | `echo "::error::${word} brings back ${found} file(s) $1, and on ${UPGRADE_FROM_TAG} it has to find...` | Zusicherung | Zusicherung bleibt (words_find_nothing VOR der Saat); nach der Saat tritt words_exact an die Stelle |
| 2b | 4552 | `echo "::error::the ${UPGRADE_FROM_TAG} container did not judge the Word file under the .docx name...` | Zusicherung | Saat entfällt mit Ersatz: alle sieben indexiert statt nie gequeued/legacy_format; Ersatzguards im neuen Block |
| 2b | 4563 | `echo "::error::the ${pair%%=*} seed has ${rows} row(s) in state.db and ${recorded} in findling_fi...` | Zusicherung | Saat entfällt mit Ersatz: alle sieben indexiert statt nie gequeued/legacy_format; Ersatzguards im neuen Block |
| 2b | 4572 | `echo "::error::the Word file under the .docx name is '${ole}' in state.db and '${ole_recorded}' i...` | Zusicherung | Saat entfällt mit Ersatz: alle sieben indexiert statt nie gequeued/legacy_format; Ersatzguards im neuen Block |
| 2b | 4582 | `# The file 1.4.2 gives up on, in the fixed order of plan 31-12 and` | Kommentar | Kommentar: Geschichte bleibt, neuer Absatz POL-02 (poller.py:2036) daneben |
| 2b | 4583 | `# with 1.4.2 writing the verdict itself; no line of this step writes` | Kommentar | Kommentar: Geschichte bleibt, neuer Absatz POL-02 (poller.py:2036) daneben |
| 2b | 4630 | `echo "::error::the ${UPGRADE_FROM_TAG} container did not finish a reconcile cycle within UPGRADE_...` | Zusicherung | bleibt: der erste Reconcile-Zyklus wird weiter abgewartet (jetzt zugleich Teil B des Catch-up) |
| 2b | 4723 | `echo "::error::${UPGRADE_FROM_TAG} did not give the stale file up as failed/repeatedly_stuck with...` | Zusicherung | Saat entfällt mit Ersatz: Annahme bei der ersten Auslieferung (POL-02), Guard 1:1:0 auf die Logzeilen |
| 2b | 4731 | `echo "::error::the give up came after ${short} short read(s) with ${left} queue row(s) left, and ...` | Zusicherung | Saat entfällt mit Ersatz: Annahme bei der ersten Auslieferung (POL-02), Guard 1:1:0 auf die Logzeilen |
| 2b | 4741 | `# written off state stays as 1.4.2 left it.` | Kommentar | Kommentar: neu, die Annahme von 1.5.0 statt des Abschreibens von 1.4.2 |
| 2b | 4754 | `words_find_nothing "on the ${UPGRADE_FROM_TAG} installation after the seed" \|\| exit 1` | Wert | Saat entfällt mit Ersatz: words_exact (jedes Wort genau seine Datei) statt words_find_nothing |
| 2b | 4762 | `echo "sown under ${UPGRADE_FROM_TAG}: six new types and the bomb without a row, the Word file und...` | Meldung | Meldung neu formuliert: alle acht beurteilt, sieben indexiert, Bombe skipped(archive_limit) |
| 2b | 4778 | `# version because the promise is about a rule an admin set on 1.4.x:` | Kommentar | Kommentar: Zitate auf v1.5.0 (ExclusionService.php:236, FileEventListener.php:441); Form unverändert |
| 2b | 4780 | `# read the list 1.4.x wrote, so the list is written in the shape of` | Kommentar | Kommentar: Zitate auf v1.5.0 (ExclusionService.php:236, FileEventListener.php:441); Form unverändert |
| 2b | 4784 | `# v1.4.2:php/lib/Service/ExclusionService.php:173 and` | Kommentar | Kommentar: Zitate auf v1.5.0 (ExclusionService.php:236, FileEventListener.php:441); Form unverändert |
| 2b | 4799 | `#   muster36.geheim36.txt       indexed under 1.4.2; "Store upgrade` | Kommentar | Kommentar: Zitate auf v1.5.0 (ExclusionService.php:236, FileEventListener.php:441); Form unverändert |
| 2b | 4846 | `echo "the prefix list of ${UPGRADE_FROM_TAG} reads ${exclusions_before}"` | Meldung | bleibt; die Variable folgt dem Tag |
| 2b | 4886 | `echo "::error::the ${UPGRADE_FROM_TAG} container did not index the control and the pattern file w...` | Zusicherung | bleibt; die Variable folgt dem Tag |
| 2b | 4899 | `echo "::error::the file under the prefix has ${excluded_rows} row(s) in state.db and '${excluded_...` | Zusicherung | bleibt; die Variable folgt dem Tag |
| 2b | 4922 | `echo "::error::on ${UPGRADE_FROM_TAG} the word under the prefix finds ${hits_excluded} file(s) (d...` | Zusicherung | bleibt; die Variable folgt dem Tag |
| 2b | 4925 | `echo "on ${UPGRADE_FROM_TAG} the word under the prefix finds nothing, the control and the pattern...` | Meldung | bleibt; die Variable folgt dem Tag |
| 2b | 4943 | `#   3, released 1.4.2       de,en      1       1    body_en folds and stems both` | Kommentar | Kommentar-Tabelle: Zeile heißt jetzt released 1.5.0, Werte unverändert (body_en faltet beide) |
| 3 | 4981 | `# state of this installation can be read for? With UPGRADE_FROM_TAG on` | Kommentar | bleibt (allgemeine Erklärung des Tags) |
| 3 | 5001 | `# Two, schemaVersion itself. It is the mark the whole phase is about,` | Kommentar | bleibt |
| 3 | 5016 | `# 37452332294), and the counter sample is the recheck mark of 29-11.` | Kommentar | Kommentar bleibt (Geschichte der Kandidatenwahl) |
| 3 | 5320 | `schemaVersion: $report.schemaVersion,` | Wert | Wert bleibt (Snapshot trägt die Marke; Vorher-Wert jetzt 3, Guard in 3c) |
| 3 | 5360 | `echo "the state of the ${UPGRADE_FROM_TAG} installation:"` | Meldung | bleibt; die Variable folgt dem Tag |
| 3 | 5366 | `echo "::error::not every one of the three terms brings back exactly one file on the ${UPGRADE_FRO...` | Zusicherung | Zusicherung bleibt wortgleich: gilt unter 1.5.0 ebenso (de,en registriert, kein body_es) |
| 3 | 5373 | `# says the schema of ${UPGRADE_FROM_TAG} carries no field that can` | Kommentar | Kommentar bleibt: Schema 3 unter de,en trägt ebenfalls kein body_es-Feld |
| 3 | 5377 | `echo "::error::the question alemanes already brings back $(jq -r '.spanish' "${RUNNER_TEMP}/upgra...` | Zusicherung | Zusicherung bleibt wortgleich: gilt unter 1.5.0 ebenso (de,en registriert, kein body_es) |
| 3 | 5387 | `echo "::error::the ${UPGRADE_FROM_TAG} installation reports the languages mark '$(jq -r '.marks.l...` | Zusicherung | Zusicherung bleibt wortgleich: gilt unter 1.5.0 ebenso (de,en registriert, kein body_es) |
| 3 | 5394 | `echo "::error::smlouve answers $(jq -r '.czech' "${RUNNER_TEMP}/upgrade-before.json") and proc $(...` | Zusicherung | Zusicherung bleibt wortgleich: gilt unter 1.5.0 ebenso (de,en registriert, kein body_es) |
| 3b | 5505 | `# the size it had (plan 29-11): the recheck mark, the embedding mark and` | Kommentar | Kommentar bleibt; recheck_1_5_0 in 3c jetzt done statt absent |
| 3b | 5509 | `# mark recheck_1_5_0 (absent), the catch-up candidates of the old stock` | Kommentar | Kommentar bleibt; recheck_1_5_0 in 3c jetzt done statt absent |
| 3c | 5511 | `- name: Store upgrade 3c, the recheck mark and the vector stock before anything moves` | Meldung | bleibt |
| 3c | 5536 | `recheck=$(seed_probe meta recheck_1_4_0) \|\| exit 1` | Wert | bleibt: recheck_1_4_0 done auch auf frischer 1.5.0 (recheck.py:146) |
| 3c | 5544 | `echo "recheck mark '${recheck}', embedding mark '${embedding}', vector stock ${stock}, seed chunk...` | Meldung | bleibt: recheck_1_4_0 done auch auf frischer 1.5.0 (recheck.py:146) |
| 3c | 5546 | `# The before state of assurance 6 since plan 30-06: 1.4.2 runs the` | Kommentar | Kommentar: Zitat v1.5.0 recheck.py:146, Aussage unverändert |
| 3c | 5547 | `# recheck of D-29-10 once at the first round with the companion of` | Kommentar | Kommentar: Zitat v1.5.0 recheck.py:146, Aussage unverändert |
| 3c | 5549 | `# (backend/src/findling/worker/recheck.py:129 of v1.4.2). An` | Kommentar | Kommentar: Zitat v1.5.0 recheck.py:146, Aussage unverändert |
| 3c | 5550 | `# installation of 1.4.2 therefore carries done before the upgrade,` | Kommentar | Kommentar: Zitat v1.5.0 recheck.py:146, Aussage unverändert |
| 3c | 5553 | `if [ "${recheck}" != "done" ]; then` | Wert | bleibt: recheck_1_4_0 done auch auf frischer 1.5.0 (recheck.py:146) |
| 3c | 5554 | `echo "::error::the ${UPGRADE_FROM_TAG} installation carries the recheck mark '${recheck}' instead...` | Zusicherung | bleibt: recheck_1_4_0 done auch auf frischer 1.5.0 (recheck.py:146) |
| 3c | 5561 | `echo "::error::the ${UPGRADE_FROM_TAG} installation carries no embedding mark ('${embedding}'), s...` | Zusicherung | bleibt (Embedding-Marke, Bestand, Chunks); Warte-Schleife um die sieben neuen Saatdateien erweitert |
| 3c | 5567 | `echo "::error::the vector stock of the ${UPGRADE_FROM_TAG} installation is empty, so 'nothing was...` | Zusicherung | bleibt (Embedding-Marke, Bestand, Chunks); Warte-Schleife um die sieben neuen Saatdateien erweitert |
| 3c | 5574 | `echo "::error::the picture carries ${tiff_chunks} and the sidecar ${sidecar_chunks} chunk(s) on t...` | Zusicherung | bleibt (Embedding-Marke, Bestand, Chunks); Warte-Schleife um die sieben neuen Saatdateien erweitert |
| 3c | 5599 | `# 1. recheck_1_5_0 is absent: 1.4.2 does not know the mark, so the` | Kommentar | neuer Wert: recheck_1_5_0 done statt absent (catchup.py:148-190, reconcile.py:469 von v1.5.0) |
| 3c | 5610 | `#    corpus of "Store upgrade 2" and the code of v1.4.2) found none:` | Kommentar | neuer Wert: recheck_1_5_0 done statt absent (catchup.py:148-190, reconcile.py:469 von v1.5.0) |
| 3c | 5629 | `catchup=$(seed_probe meta recheck_1_5_0) \|\| exit 1` | Wert | neuer Wert: recheck_1_5_0 done statt absent (catchup.py:148-190, reconcile.py:469 von v1.5.0) |
| 3c | 5631 | `echo "::error::the ${UPGRADE_FROM_TAG} installation carries the catch-up mark '${catchup}', and a...` | Zusicherung | neuer Wert: recheck_1_5_0 done statt absent (catchup.py:148-190, reconcile.py:469 von v1.5.0) |
| 3c | 5719 | `echo "recheck_1_5_0 is absent; the old stock of ${old_stock#*:} file(s) has the digest ${old_dige...` | Meldung | neuer Wert: recheck_1_5_0 done statt absent (catchup.py:148-190, reconcile.py:469 von v1.5.0) |
| 4 | 5780 | `# Since plan 36-13 the tree carries 1.5.1 (1.5.0 until 2026-10-22) against the 1.4.3 of the tag,` | Kommentar | Kommentar: aktueller Satz neu (Baum 1.6.0 gegen v1.5.0, Zweig 1), Geschichte bleibt |
| 4 | 5783 | `# UPGRADE_FROM_TAG both carried 1.4.2, so the SECOND branch ran; from plan` | Kommentar | Kommentar: aktueller Satz neu (Baum 1.6.0 gegen v1.5.0, Zweig 1), Geschichte bleibt |
| 4 | 5784 | `# 29-11 to then the tree carried 1.4.0 against the 1.3.2 of the tag` | Kommentar | Kommentar: aktueller Satz neu (Baum 1.6.0 gegen v1.5.0, Zweig 1), Geschichte bleibt |
| 4 | 5791 | `# then never run; so would the signal of the new verdicts the recheck` | Kommentar | Kommentar: Migration heißt jetzt Version001600Date20261028000000, 001400 bleibt als Geschichte |
| 4 | 5814 | `echo "::notice::the companion of this commit carries ${new_companion}, the same version ${UPGRADE...` | Meldung | bleibt (Zweig gleicher Versionen, laeuft hier nicht) |
| 4 | 5815 | `echo "Both sides carry the same version (${UPGRADE_FROM_TAG} and ${new_companion}), so this is th...` | Meldung | bleibt (Zweig gleicher Versionen, laeuft hier nicht) |
| 4 | 5829 | `echo "the ${UPGRADE_FROM_TAG} container runs ${old_image}"` | Meldung | bleibt; die Variable folgt dem Tag |
| 4 | 5848 | `# 29-11 backend/appinfo/info.xml says image-tag 1.4.0, and that tag is` | Kommentar | Kommentar: image-tag heißt jetzt 1.6.0 (plan 40-02), Geschichte bleibt |
| 4 | 6026 | `# sixth reads the recheck mark. Since plan 30-06 (start v1.4.2) the sixth` | Kommentar | Kommentar neu abgeleitet: beide Marken done auf beiden Seiten, jeder Zählerschritt 0 (Tabelle), Saat behaelt Urteile |
| 4 | 6027 | `# reads it as done on both sides, because 1.4.2 already ran the recheck,` | Kommentar | Kommentar neu abgeleitet: beide Marken done auf beiden Seiten, jeder Zählerschritt 0 (Tabelle), Saat behaelt Urteile |
| 4 | 6067 | `# plan 30-06 (D-30-07). 1.4.2 judged both seed files rightly before the` | Kommentar | Kommentar neu abgeleitet: beide Marken done auf beiden Seiten, jeder Zählerschritt 0 (Tabelle), Saat behaelt Urteile |
| 4 | 6070 | `# vectors and no verdict in Nextcloud. Its recheck of D-29-10 reads done` | Kommentar | Kommentar neu abgeleitet: beide Marken done auf beiden Seiten, jeder Zählerschritt 0 (Tabelle), Saat behaelt Urteile |
| 4 | 6071 | `# ("Store upgrade 3c"), and recheck_step returns at once on done` | Kommentar | Kommentar neu abgeleitet: beide Marken done auf beiden Seiten, jeder Zählerschritt 0 (Tabelle), Saat behaelt Urteile |
| 4 | 6072 | `# (backend/src/findling/worker/recheck.py of this tree), so nothing of` | Kommentar | Kommentar neu abgeleitet: beide Marken done auf beiden Seiten, jeder Zählerschritt 0 (Tabelle), Saat behaelt Urteile |
| 4 | 6076 | `# three counters, and only by the step it derives. Under 1.4.2` | Kommentar | Kommentar neu abgeleitet: beide Marken done auf beiden Seiten, jeder Zählerschritt 0 (Tabelle), Saat behaelt Urteile |
| 4 | 6107 | `# of the recheck (+1, +1, +1, -2, +1, -2); from 30-06 to 31-13 every step` | Kommentar | Kommentar neu abgeleitet: beide Marken done auf beiden Seiten, jeder Zählerschritt 0 (Tabelle), Saat behaelt Urteile |
| 4 | 6112 | `# Assurance 9 is the seed itself: the catch-up mark recheck_1_5_0 reads` | Kommentar | Kommentar neu abgeleitet: beide Marken done auf beiden Seiten, jeder Zählerschritt 0 (Tabelle), Saat behaelt Urteile |
| 5 | 6166 | `catchup=$(seed_probe meta recheck_1_5_0 2> /dev/null \|\| echo "unreadable")` | Wert | bleibt done, aber done schon vorher (3c); Zeitzeile neu formuliert |
| 5 | 6204 | `echo "the seed is caught up: recheck_1_5_0 read done $(( catchup_done_at - UPGRADE_FINISHED_AT ))...` | Meldung | bleibt done, aber done schon vorher (3c); Zeitzeile neu formuliert |
| 5 | 6217 | `recheck=$(seed_probe meta recheck_1_4_0 2> /dev/null \|\| echo "unreadable")` | Wert | bleibt: recheck_1_4_0 done vor und nach dem Upgrade |
| 5 | 6221 | `case "${open}:${recheck}:${tiff}:${sidecar}:${vectors}" in` | Wert | bleibt: recheck_1_4_0 done vor und nach dem Upgrade |
| 5 | 6227 | `echo "open=${open} recheck=${recheck} picture=${tiff} sidecar=${sidecar} picture chunks=${vectors...` | Meldung | bleibt: recheck_1_4_0 done vor und nach dem Upgrade |
| 5 | 6263 | `for mark in schemaVersion indexVersion analyzerVersion wordlistHash; do` | Wert | bleibt: vier Marken unverändert |
| 5 | 6266 | `# And the schema mark by value: 2, the one of 1.4.2, although this` | Kommentar | neuer Wert: 3 statt 2 (config.py:58, open.py:256 von v1.5.0), weiter per Wert verglichen |
| 5 | 6269 | `# sides, which is a start that was never 1.4.2.` | Kommentar | neuer Wert: 3 statt 2 (config.py:58, open.py:256 von v1.5.0), weiter per Wert verglichen |
| 5 | 6270 | `if ! jq -e '.marks.schemaVersion == "2"' "${after}" > /dev/null; then` | Wert | neuer Wert: 3 statt 2 (config.py:58, open.py:256 von v1.5.0), weiter per Wert verglichen |
| 5 | 6271 | `echo "::error::the stored schema mark reads '$(jq -r '.marks.schemaVersion' "${after}")' after th...` | Zusicherung | neuer Wert: 3 statt 2 (config.py:58, open.py:256 von v1.5.0), weiter per Wert verglichen |
| 5 | 6274 | `echo "the stored schema mark reads 2 after the upgrade, the 2 of ${UPGRADE_FROM_TAG}, with no reb...` | Meldung | neuer Wert: 3 statt 2 (config.py:58, open.py:256 von v1.5.0), weiter per Wert verglichen |
| 5 | 6335 | `# Every counter exactly: the recheck of D-29-10 hands nothing of the` | Kommentar | Kommentar neu: kein Zähler bewegt sich |
| 5 | 6358 | `echo "--- 3b, the two seed files keep the verdict of ${UPGRADE_FROM_TAG} ---"` | Meldung | bleibt (Saat behaelt Urteil) |
| 5 | 6386 | `echo "the seed word finds exactly the file id ${UPGRADE_SEED_TIFF_ID}, as it did on ${UPGRADE_FRO...` | Meldung | bleibt (Saat behaelt Urteil) |
| 5 | 6417 | `echo "--- 6, the recheck mark stays done, and the languages mark stays de,en ---"` | Meldung | bleibt (done/done, de,en/de,en); Kommentar auf 1.5.0 umgestellt |
| 5 | 6418 | `# Since plan 30-06 the start is v1.4.2, which ran the recheck of` | Kommentar | bleibt (done/done, de,en/de,en); Kommentar auf 1.5.0 umgestellt |
| 5 | 6420 | `# upgrade). After it the mark has to read done again: recheck_step` | Kommentar | bleibt (done/done, de,en/de,en); Kommentar auf 1.5.0 umgestellt |
| 5 | 6438 | `recheck=$(seed_probe meta recheck_1_4_0 \|\| echo "unreadable")` | Wert | bleibt: recheck_1_4_0 done vor und nach dem Upgrade |
| 5 | 6439 | `if [ "${recheck}" != "done" ]; then` | Wert | bleibt: recheck_1_4_0 done vor und nach dem Upgrade |
| 5 | 6440 | `echo "::error::the recheck mark reads '${recheck}' after the upgrade instead of the done it read ...` | Zusicherung | bleibt: recheck_1_4_0 done vor und nach dem Upgrade |
| 5 | 6443 | `echo "the recheck mark read done before the upgrade and reads done after it, nothing was handed b...` | Meldung | bleibt: recheck_1_4_0 done vor und nach dem Upgrade |
| 5 | 6448 | `echo "::error::the report named the languages mark as '${was}' before the upgrade and as '${now}'...` | Zusicherung | bleibt (done/done, de,en/de,en); Kommentar auf 1.5.0 umgestellt |
| 5 | 6480 | `echo "the Spanish question answers $(jq -r '.spanish' "${after}") hits after the upgrade, unchang...` | Meldung | bleibt (alemanes 0 vor und nach dem Upgrade) |
| 5 | 6512 | `# them carried a vector under ${UPGRADE_FROM_TAG} (no row, skipped or` | Kommentar | neu: der ganze Bestand (stock 0) statt ohne die acht Saat-IDs, da die Saat schon unter 1.5.0 Vektoren trägt |
| 5 | 6539 | `catchup=$(seed_probe meta recheck_1_5_0 \|\| echo "unreadable")` | Wert | bleibt done; Meldung neu: done vorher UND nachher statt absent -> done |
| 5 | 6544 | `echo "the catch-up mark recheck_1_5_0 read absent before the upgrade and reads done after it"` | Meldung | bleibt done; Meldung neu: done vorher UND nachher statt absent -> done |
| 5 | 6589 | `# was written off by ${UPGRADE_FROM_TAG} without a container row, and` | Kommentar | Zusicherung bleibt (indexed/, 0 Urteile); Begründung neu: schon 1.5.0 indexierte die Datei (POL-02) |
| 5 | 6595 | `echo "::error::the file ${UPGRADE_FROM_TAG} wrote off as failed(repeatedly_stuck) is '${stale}' i...` | Zusicherung | Zusicherung bleibt (indexed/, 0 Urteile); Begründung neu: schon 1.5.0 indexierte die Datei (POL-02) |
| 5 | 6598 | `echo "the file ${UPGRADE_FROM_TAG} wrote off as failed(repeatedly_stuck) without a container row ...` | Meldung | Zusicherung bleibt (indexed/, 0 Urteile); Begründung neu: schon 1.5.0 indexierte die Datei (POL-02) |
| 5 | 6690 | `echo "### Upgrade from \`${UPGRADE_FROM_TAG}\` on ${MATRIX_SERVER_VERSION} (${MATRIX_RUNNER})"` | Meldung | Zusammenfassung neu formuliert (kein Zähler bewegt, Marken done/done, schemaVersion 3) |
| 5 | 6695 | `echo "- every counter exact: the recheck of D-29-10 read done before and after the upgrade and ha...` | Meldung | Zusammenfassung neu formuliert (kein Zähler bewegt, Marken done/done, schemaVersion 3) |
| 5 | 6696 | `echo "- the catch-up of 1.5 ran without an admin: recheck_1_5_0 absent before and done after; mai...` | Meldung | Zusammenfassung neu formuliert (kein Zähler bewegt, Marken done/done, schemaVersion 3) |
| 5 | 6698 | `echo "- the seed of \`${UPGRADE_FROM_TAG}\` keeps its verdicts: the AppleDouble sidecar is skippe...` | Meldung | Zusammenfassung neu formuliert (kein Zähler bewegt, Marken done/done, schemaVersion 3) |
| 5 | 6701 | `echo "- schemaVersion stays 2 and the languages mark stays de,en, the rebuild state is idle: noth...` | Meldung | Zusammenfassung neu formuliert (kein Zähler bewegt, Marken done/done, schemaVersion 3) |
| 5 | 6718 | `#   a  the prefix Ausschluss36 that 1.4.2 wrote still holds under 1.5:` | Kommentar | Kommentar: der Präfix, den der Start schrieb (statt 1.4.2) |
| 5b | 6802 | `echo "--- 11a, the prefix of ${UPGRADE_FROM_TAG} still holds ---"` | Meldung | bleibt; die Variable folgt dem Tag |
| 5b | 6804 | `echo "::error::the word under the prefix Ausschluss36 brings back ${found} file(s) after the upgr...` | Zusicherung | bleibt; die Variable folgt dem Tag |
| 5b | 6823 | `echo "--- 11b, the prefix list reads as ${UPGRADE_FROM_TAG} wrote it ---"` | Meldung | bleibt; die Variable folgt dem Tag |
| 5b | 6826 | `echo "::error::the prefix list read ${UPGRADE_EXCLUSIONS_BEFORE} on ${UPGRADE_FROM_TAG} and reads...` | Zusicherung | bleibt; die Variable folgt dem Tag |
| 5b | 6905 | `echo "- exclusions: prefix kept, pattern applied. The prefix \`Ausschluss36\` written on \`${UPGR...` | Meldung | bleibt; die Variable folgt dem Tag |
| 5b | 6912 | `# What the block above proves is that an upgrade 1.3.2 to 1.4.0 under the` | Kommentar | Kommentar: Geschichte bleibt; Versionsnennung 1.4.0 versionsneutral gefasst |
| 5b | 6920 | `# UPGRADE_FROM_TAG is an env of the workflow and the matrix is already` | Kommentar | Kommentar: Geschichte bleibt; Versionsnennung 1.4.0 versionsneutral gefasst |
| 5b | 6927 | `# instance is already at 1.4.0 here, the volume already holds the index of` | Kommentar | Kommentar: Geschichte bleibt; Versionsnennung 1.4.0 versionsneutral gefasst |
| 6 | 7443 | `was=$(jq -r '.marks.schemaVersion' "${before}")` | Wert | neuer Wert: 3 -> 3 statt 2 -> 3; der Beweis des Stempelns liegt bei der Sprachmarke (Zusicherung 2) |
| 6 | 7444 | `now=$(jq -r '.marks.schemaVersion' "${after}")` | Wert | neuer Wert: 3 -> 3 statt 2 -> 3; der Beweis des Stempelns liegt bei der Sprachmarke (Zusicherung 2) |
| 7 | 7665 | `if ! jq -e --arg set "${REBUILD_LANGUAGES_NORMALISED}" '.marks.languages == $set and .marks.schem...` | Wert | bleibt: 3 auf beiden Seiten des Rückwegs |
| 7 | 7666 | `echo "::error::the installation reports the languages mark '$(jq -r '.marks.languages' "${before}...` | Zusicherung | bleibt: 3 auf beiden Seiten des Rückwegs |
| 7 | 7758 | `was=$(jq -r '.marks.schemaVersion' "${before}")` | Wert | bleibt: 3 auf beiden Seiten des Rückwegs |
| 7 | 7759 | `now=$(jq -r '.marks.schemaVersion' "${after}")` | Wert | bleibt: 3 auf beiden Seiten des Rückwegs |
