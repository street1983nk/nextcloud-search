---
phase: 18-schema-marken-und-umbauweg
audited: 2026-09-24
tree: 424f611d10785603f27e23a8a0daf6daa2124aa3
commit: 32366e13473ba79c3a5ae798fc88a719f0aacc16
scope: "git diff dfc871c..HEAD, 66 Dateien, Produktionskern backend/src/findling und php/ sowie .github/workflows/deploy-harp.yml"
findings:
  critical: 1
  high: 4
  medium: 8
  low: 12
  total: 25
status: issues_found
fixed: []
still_open: [C-18-01, H-18-01, H-18-02, H-18-03, H-18-04, M-18-01, M-18-02, M-18-03, M-18-04, M-18-05, M-18-06, M-18-07, M-18-08, L-18-01, L-18-02, L-18-03, L-18-04, L-18-05, L-18-06, L-18-07, L-18-08, L-18-09, L-18-10, L-18-11, L-18-12]
---

# Phase 18: Security-, Bug- und Performance-Audit

**Umfang:** die zwoelf Plaene 18-01 bis 18-12 plus die zwei Debug-Sitzungen
(`upgrade5-schema-drift-languages`, `upgrade6-rebuild-timeout`), gelesen gegen
den Baum von Commit `32366e1`. Der Bericht liegt nach der Owner-Regel vom
15.08.2026 vor dem Phasenabschluss und ist nach dem Muster von
`docs/audits/2026-09-phase-17/README.md` geschrieben.

Die Ueberschriften stehen ohne Umlaute, weil Pruefungen und Verweise auf sie
zeigen; der Fliesstext benutzt echte Umlaute. Dieser Bericht nennt Dateinamen,
Zeilennummern und Zahlen und sonst nichts.

**Bilanz vorweg: ein CRITICAL, vier HIGH, acht MEDIUM, zwoelf LOW.** Das ist
der erste Bericht dieser Reihe mit einem CRITICAL, und der Grund ist nicht ein
Randfall, sondern der Normalweg.

Der Kern in einem Satz: **`swap_in` benennt und loescht ein Indexverzeichnis,
auf dem der Poller die ganze Zeit einen offenen `IndexWriter` haelt.** Der
Modulkopf von `rebuild.py` behauptet in Schritt 2 seiner Reihenfolge das
Gegenteil ("The poller's writer is already closed at this point, because
silencing it is the first thing the caller of plan 18-09 does"). Diese Zusage
ist nicht eingeloest: `Poller.silence()` loescht ein Flag und sonst nichts, der
Writer wird in `Poller._open()` genau einmal gebaut und erst in `aclose()`
wieder abgegeben. Nach einem erfolgreichen Umbau schreibt der wieder scharf
gestellte Poller in ein Verzeichnis, das `shutil.rmtree` bereits entfernt hat.
Das ist stiller Datenverlust auf dem gluecklichen Pfad (C-18-01).

Daneben stehen drei Befunde, die alle dieselbe Wurzel haben, naemlich dass der
Umbau keinen Weg zurueck kennt: die Stilllegung wartet nicht auf den laufenden
Indexlauf (H-18-01), die Wiederaufnahme prueft das Schema des halb gefuellten
Zielverzeichnisses nicht (H-18-02), und ein einziges verlorenes Dokument setzt
den Umbau dauerhaft fest, weil `counts_match` eine Gleichheit ist und der
Cursor nie zurueckgeht (H-18-04). Dazu ein Startpfad ohne Schutznetz:
`recover_the_index_directories` laeuft ungefangen im Lifespan und kann den
Container dauerhaft am Start hindern (H-18-03).

**Was geprueft und entkraeftet wurde:** die Pfadableitung der drei Verzeichnisse
ist sauber (Abschnitt 2.1), die fuenf Zustaende der Aufraeumung decken alle acht
Kombinationen ab (Abschnitt 3.5), die drei Legacy-Ausnahmen lassen in keiner
Kombination einen fremden Index als kompatibel durch (Abschnitt 2.2), die
Banner-Ausgaben sind in beiden Haelften korrekt escaped (Abschnitt 2.4), der
private frp-Schluessel landet nicht im Workflow-Log und nicht im Artefakt
(Abschnitt 2.3), `rebuild_progress` als Modulglobal ist unter uvicorn
unbedenklich (Abschnitt 4.2), und doppelte `file_id` im Quellindex sind
ausgeschlossen (Abschnitt 3.3).

---

## 1. Was geprueft wurde

| Nr. | Pfad | Womit geprueft | Beleg | Urteil |
|---|---|---|---|---|
| 1 | Lebensdauer des Poller-Writers ueber den Tausch | Quelltextlesung der Aufrufkette `lifespan` zu `Poller.run` zu `_open` zu `IndexBatchWriter.__init__` | `poller.py:1510-1511`, `writer.py:174`, `poller.py:541-549`, `main.py:671` gegen `main.py:693` | **offener Writer auf dem geloeschten Verzeichnis** (C-18-01) |
| 2 | Was `silence()` zusagt und was es tut | Quelltextlesung `Poller.silence`, `Poller.busy`, `run_once` | `poller.py:519-526` loescht nur `_armed`; kein Aufrufer wartet auf `busy` | **Bedingung von `transfer_documents` nicht hergestellt** (H-18-01) |
| 3 | Wiederaufnahme in ein fremdes Zielverzeichnis | Quelltextlesung `open_index`, `transfer_documents`, `stamp_after_swap` | `open.py:118` liest bei vorhandenem Verzeichnis das persistierte Schema; `rebuild.py:760-762` stempelt trotzdem | **stiller Stempel auf ein altes Schema** (H-18-02) |
| 4 | Startpfad der Aufraeumung | Quelltextlesung `main.py:565`, `discard_directory` | kein `try` um `recover_the_index_directories`, `rmtree(ignore_errors=False)` | **Startverhinderung moeglich** (H-18-03) |
| 5 | Abbruchbedingung des Bandlaufs | Quelltextlesung `_resume_cursor`, Bandabfrage, `counts_match` | `rebuild.py:396`, `rebuild.py:495-510`, `rebuild.py:372-374` | **kein Selbstheilungspfad** (H-18-04) |
| 6 | Pfadableitung der drei Verzeichnisse | Quelltextlesung `config.py:1280`, `_storage_root`, beide `with_name` | `index_dir = root / "index"`, `.name` nie leer, keine Aufrufereingabe | **kein Traversal**, ein MEDIUM zu Symlinks (M-18-04) |
| 7 | Die drei Legacy-Ausnahmen in Kombination | Fallmatrix ueber `index_version`, `tantivy_version`, `schema_version`, `languages` | `repo.py:1431-1490`, `LEGACY_SCHEMA_STEPS` als Paarmenge, `_languages_are_legacy` faellt bei jedem gespeicherten Wert geschlossen | **kein fremder Index wird kompatibel**, ein LOW (L-18-06) |
| 8 | Zertifikatsuebergabe per docker cp | Quelltextlesung des Schritts und der Artefaktliste | `deploy-harp.yml:3947-3977` gegen `deploy-harp.yml:4329-4340`, `rebuild-env.list` und `rebuild-certs.tar` sind beide nicht in der Kopierliste | **kein Schluessel im Log und kein Schluessel im Artefakt**, zwei LOW (L-18-09, L-18-10) |
| 9 | Escaping der zwei neuen Banner | Quelltextlesung Vorlage und Skript | `admin.php:343-355` druckt jedes Feld durch `p()`, `admin.js` schreibt durch `text()` in `textContent` | **kein XSS**, ein LOW zur `$`-Ersetzung (L-18-08) |
| 10 | Lesekappe waehrend des Tauschs | Quelltextlesung `reset_read_side`, `filled_languages`, `read_side` | `resources.py:497` liest ausserhalb der Sperre, `resources.py:519` schreibt innerhalb | **zwei Wettlaeufe** (M-18-02, M-18-03) |
| 11 | Kosten der Fuellstandssonde | Quelltextlesung, tantivy-Dokumentation zu `terms_with_prefix` | `resources.py:509` sondiert immer alle sechs Felder, Fenster 30 s | **Kosten wachsen mit der Indexgroesse** (M-18-08) |
| 12 | `rebuild_progress` als Modulglobal | Quelltextlesung, GIL-Betrachtung, `RebuildProgress` ist `frozen` und `slots` | eine Zuweisung je Band, ein Leser im Statusfaden | **kein Wettlauf**, kein Befund |
| 13 | Doppelte `file_id` im Quellindex | Quelltextlesung `IndexBatchWriter.add` | `writer.py:258` loescht per Term vor jedem Einfuegen, Deletes wirken auf kleinere Opstamps | **ausgeschlossen**, kein Befund |
| 14 | Acht Kombinationen der drei Verzeichnisnamen | Fallmatrix gegen die fuenf Zweige | `rebuild.py:677-716`, alle acht landen in einem der fuenf Zweige | **vollstaendig**, ein LOW (L-18-07) |
| 15 | Rechtegrenze | Quelltextlesung aller neuen Routenfelder und der PHP-Seite | `/status` bleibt `ADMIN`, keine neue Route, keine neue Umgehung | **unveraendert**, kein Befund |

---

## 2. Security

### 2.1 Verzeichnistausch und Aufraeumpfad: die Pfadableitung

Die Frage war, ob ueber `index.rebuild` oder `index.retired` ein Pfad in das
`rmtree` von `discard_directory` gelangt, den ein Aufrufer gewaehlt hat.

**Nein.** Die drei Namen entstehen an genau zwei Stellen, und beide leiten sie
mit `Path.with_name` aus `settings().index_dir` ab: `rebuild.py:547` fuer den
stillgelegten Namen, `rebuild.py:675-676` fuer beide Geschwister im
Aufraeumpfad. `settings().index_dir` ist `root / "index"` (`config.py:1280`),
`root` kommt aus `APP_PERSISTENT_STORAGE` oder aus dem Systemtemp
(`config.py:1129-1140`). Der Name des Verzeichnisses ist damit in jedem Fall
`index`, `with_name` kann also nie mit dem leeren Namen scheitern, und die
angehaengten Endungen enthalten weder `/` noch `..`. Keine Route, kein
Anfragefeld und kein Nextcloud-Knoten erreicht diese Ableitung.

Auch die Suche nach weiteren Loeschstellen ist leer: im ganzen Baum unter
`backend/src/findling/` gibt es genau ein `shutil.rmtree` (`rebuild.py:561`)
und genau drei `rename` (`rebuild.py:548`, `599`, `683`, `695`). Der Beweis,
den Zustand 3 des Aufraeumpfads fuehrt (nur `swap_in` entfernt jemals den Namen
`index`), haelt deshalb innerhalb der Anwendung.

**Die eine Luecke ist kein Traversal, sondern ein Symlink**, und sie steht als
M-18-04 unten: keine der drei Stellen fragt, ob `index` ein symbolischer Link
ist.

### 2.2 Die Legacy-Ausnahmen in Kombination

`Store.version_mismatch` kennt seit dieser Phase vier Ausnahmen statt zwei
(`repo.py:755-770`). Die Frage des Owners war, ob ein praeparierter Index ueber
eine Kombination davon als kompatibel durchrutscht.

Die vier im Einzelnen:

| Marke | Regel | Faellt sie geschlossen? |
|---|---|---|
| `index_version` | gespeicherter Wert darf ueber der Grundlinie stehen | ja, ein fehlender Wert ist eine Abweichung |
| `tantivy_version` | nur das `index_format` wird verglichen | ja, `_index_format_matches` verlangt beide Banner |
| `schema_version` | nur das Paar `("1", "2")` | ja, Paarmenge statt Zahlenvergleich, `None` und `unknown` bekommen nichts |
| `languages` | nur ein **fehlender** Wert, und nur gegen eine Erwartung innerhalb von `("de", "en")` | ja, `repo.py:1487` gibt bei jedem gespeicherten Wert `False` zurueck |

**Die Kombination, die am weitesten traegt**, ist gespeichert
`schema_version = "1"` zusammen mit fehlendem `languages` bei einer Erwartung
`de,en`. Dann meldet `version_mismatch` nichts, und genau das ist gewollt: der
Index aus 1.2.0 mit neun Feldern beantwortet jede Anfrage, die dieser
Abfragebauer stellt, weil `set(DEFAULT_FIELDS) <= set(FIELDS_SCHEMA_1)` gilt.
Ein praeparierter Index gewinnt daraus nichts, denn wer die Marken in
`state.db` schreiben kann, hat bereits Schreibrechte auf dem Volume des
Containers und damit auf den Index selbst. Es gibt keinen Weg, der von einer
Nutzer- oder Adminanfrage in diese Tabelle fuehrt.

**Was die Kombination kostet, ist keine Sicherheitsluecke, sondern eine stille
Qualitaetsluecke**, und sie steht als L-18-06: eine Instanz, die unter 1.2.0
auf `de` lief und beim Upgrade `en` einschaltet, bekommt keine Abweichung
gemeldet, weil `de,en` innerhalb des Paares liegt. `body_en` bleibt leer, die
englische Kette wird trotzdem angefragt. Das ist im Quelltext
(`repo.py:1476-1485`), in `docs/language-analyzers.md` und in einem Testfall
benannt und vom Owner so entschieden, deshalb LOW und nicht MEDIUM.

Eine Nebenwirkung, die nirgends steht: `stamp_after_rebuild` schreibt die
Marken nur, wenn es vorher eine Abweichung oder eine `REBUILD_MARK` gab
(`open.py:288-293`). Auf einer Installation, die nie driftet, wird
`languages` also **nie** geschrieben, und die Ausnahme bleibt dauerhaft offen
statt sich mit dem ersten Stempel zu schliessen. Das gehoert zu L-18-06.

### 2.3 Das docker-cp-Zertifikatmuster in der CI

Geprueft wurde, ob der private Schluessel `client.key` in ein Schrittlog oder in
ein hochgeladenes Artefakt gelangt.

**In das Log nicht.** `deploy-harp.yml:3956` schreibt den Tar-Strom mit `>` in
eine Datei unter `RUNNER_TEMP`, es gibt kein `cat`, kein `base64` und kein
`head` darauf. Die Umgebungsliste wird ausdruecklich nur mit
`cut -d= -f1` gedruckt (`deploy-harp.yml:3903-3906`), `APP_SECRET` erscheint
also nur als Name. Das App-Passwort wird nur mit seiner Laenge gedruckt
(`deploy-harp.yml:3824`).

**In das Artefakt auch nicht.** Der Sammelschritt kopiert eine namentliche
Positivliste nach `harp-logs` (`deploy-harp.yml:4329-4340`), und weder
`rebuild-certs.tar` noch `rebuild-env.list` stehen darin; `rebuild-env.list`
ist sogar mit Begruendung ausgeschlossen. Das ist sauber gebaut.

Zwei Reste bleiben und sind LOW, weil die Matrix auf `ubuntu-24.04` und
`ubuntu-24.04-arm` laeuft, also auf fluechtigen Runnern: die Tar-Datei mit dem
privaten Schluessel bleibt mit der Standardmaske liegen und wird nicht geloescht
(L-18-09), und das App-Passwort steht bei jedem `curl` in der Prozessliste
(L-18-10). Beide werden zu MEDIUM, sobald dieser Workflow jemals auf einem
selbst gehosteten Runner laeuft.

### 2.4 Escaping der zwei neuen Banner

Beide Haelften sind korrekt.

**PHP:** Die Bannerschleife druckt jedes Feld durch `p()`, also durch den
escapenden Drucker: `kind`, `id` und `icon` in `admin.php:343-344`, der Text in
`admin.php:355`. Die Sprachzeile geht denselben Weg (`admin.php:401`). Die
Werte selbst haben vorher `AdminViewService::text()` passiert
(`AdminViewService.php:1920-1927`), das `PlainText::bounded` anwendet, also
saeubert und kappt. `rebuildBlockedBytes` geht durch `counter()`
(`AdminViewService.php:1859-1863`), das nur nicht negative Ganzzahlen
durchlaesst.

**JavaScript:** Alle drei neuen Zeilen schreiben ueber `text()`, also ueber
`textContent`, nicht ueber `innerHTML`. Ein Markup-Fragment aus dem Container
landet als sichtbarer Text und nicht als Element.

Der einzige Rest ist L-18-08: `String.prototype.replace` interpretiert
`$&`, `` $` `` und `$'` im **Ersatz**, und `languagesActive` wird dort
ungefiltert eingesetzt.

### 2.5 Rechtegrenze

Unveraendert. Die Phase fuegt keine Route hinzu; die fuenf neuen Felder reisen
in der bestehenden Antwort von `GET /status`, die in `info.xml` weiterhin
`ADMIN` fuehrt. Kein neues Feld traegt einen Pfad, einen Dateinamen oder einen
Benutzernamen: `languagesActive` und `languagesFilled` sind Listen aus
Zweibuchstabencodes, die drei Umbauzahlen sind Zahlen. Die Endfilterung der
Suche bleibt in PHP, der Umbau liest ausschliesslich aus dem eigenen Index und
schreibt ausschliesslich in das eigene Volume.

---

## 3. Bugs

### 3.1 Der offene Writer des Pollers (die Wurzel von C-18-01)

Die Reihenfolge, die der Modulkopf von `rebuild.py:39-51` als sechs Schritte
aufschreibt, ist richtig gedacht. Schritt 2 lautet "let the source index go.
The poller's writer is already closed at this point, because silencing it is
the first thing the caller of plan 18-09 does".

Dieser Satz ist falsch, und zwar aus drei unabhaengigen Gruenden:

1. `Poller.silence()` (`poller.py:519-526`) ruft `self._armed.clear()` und
   sonst nichts. Es schliesst keinen Writer und gibt keine Sperre zurueck.
2. Der Writer wird in `Poller._open()` (`poller.py:1510-1511`) genau einmal
   gebaut, in `IndexBatchWriter.__init__` (`writer.py:174`) sofort als
   `index.writer(...)` materialisiert und erst in `Poller.aclose()`
   (`poller.py:541-549`) wieder abgegeben. Er lebt also so lange wie die
   Poller-Instanz, nicht so lange wie ein Durchlauf.
3. Der Zeitplan spielt gegen den Umbau. Der Lifespan schaltet den Poller in
   `main.py:671` scharf und legt die Umbauaufgabe erst in `main.py:693` an.
   Bis `rebuild_the_index` ueberhaupt bei `silence()` (`rebuild.py:893`)
   ankommt, ist es durch `_rebuild_is_due`, `open_store` und `build_artifact()`
   gelaufen, und `build_artifact()` liest die Wortliste mit 276496 Eintraegen
   samt Pruefsumme. Der Poller braucht fuer sein `_open()` nach eigener
   Messung 1,5 bis 3 Sekunden. Der Writer ist also mit hoher Sicherheit offen,
   bevor der Umbau das erste Mal etwas sagt.

Was daraus folgt, steht unter C-18-01.

### 3.2 Die Bedingung, die transfer_documents selbst nennt

`transfer_documents` schreibt in seinen eigenen Docstring
(`rebuild.py:448-454`): "The poller may not write into the source index while
this runs. The cursor only ever moves forward, so a document that arrives below
it lands in the source after the band that would have taken it and is never
carried over. Silencing the poller is the job of the caller."

Der Aufrufer stellt diese Bedingung nicht her. `silence()` kehrt sofort zurueck;
ein Durchlauf, der gerade in `run_once` steckt, arbeitet seine Anspruchsliste
zu Ende und ruft `flush()`, also `writer.commit()` auf den Quellindex. Der
Kommentar in `rebuild.py:888-892` sagt das sogar ausdruecklich ("The in flight
pass is allowed to run out"), ohne die Folge zu ziehen. Ein Dokument mit einer
`file_id` unterhalb des Cursors, das in diesem Fenster ankommt, wird nie
uebertragen. Bei der Erstindexierung eines Mounts sind die `file_id` beliebig
verteilt, "unterhalb des Cursors" ist also der Regelfall und nicht die
Ausnahme. Das ist H-18-01.

### 3.3 Warum es keine doppelten file_id gibt

Geprueft, weil eine Dublette genau an der Bandgrenze ein Dokument verlieren
wuerde: das Band ist auf `band_documents` begrenzt und aufsteigend nach
`file_id` sortiert, die naechste Runde beginnt bei `cursor + 1`
(`rebuild.py:495-504`). Laegen zwei Dokumente mit derselben `file_id` beidseits
einer Bandgrenze, waere das zweite verloren.

Sie koennen nicht existieren. `IndexBatchWriter.add` (`writer.py:258`) setzt vor
jedem Einfuegen ein `delete_documents_by_query` auf den `file_id`-Term ab, und
tantivy wendet Loeschungen auf Dokumente mit kleinerem Opstamp an. Auch zwei
Auftraege fuer dieselbe Datei in einem Stapel enden also mit genau einem
Dokument. Kein Befund.

### 3.4 Wiederaufnahme: leeres Ziel, korruptes Ziel, fremdes Ziel

Drei Faelle, drei verschiedene Urteile.

**Leeres Ziel** ist sauber. `_resume_cursor` (`rebuild.py:392-397`) laedt neu,
sieht `num_docs == 0` und antwortet 0; das Band beginnt bei 1. Der einzige
Rest ist, dass eine `file_id` von 0 damit nie uebertragen wird (L-18-01).

**Korruptes Ziel** ist nicht behandelt. `open_index` (`open.py:118`) fragt
`Index.exists(...)` und ruft bei True `Index.open(...)`. Ein `index.rebuild`,
dessen `meta.json` ein harter Abbruch halb geschrieben hat, faellt genau in
diesen Zweig, `Index.open` wirft, und der Aufraeumpfad des naechsten Starts
behaelt das Verzeichnis ausdruecklich (Zustand 2, `rebuild.py:709-714`). Es gibt
keinen Pfad, der ein unbrauchbares Zielverzeichnis verwirft. Der Umbau scheitert
damit bei jedem Start erneut, und die Protokollzeile nennt nur den Typnamen.
Das ist Teil von H-18-04.

**Fremdes Ziel** ist der schwerste der drei. Ein `index.rebuild`, das aus einer
aelteren Codefassung stammt, wird von `Index.open` mit dem **persistierten**
Schema geoeffnet; `build_schema()` kommt nie zum Zug. `add_document` nimmt
einen Feldnamen, den dieses Schema nicht kennt, kommentarlos an und verwirft den
Wert, was `schema.py:92-95` selbst gemessen hat. Der Bandlauf traegt also
vollstaendig in ein veraltetes Schema ueber, `counts_match` ist zufrieden, weil
es nur Dokumente zaehlt, und `stamp_after_swap` (`rebuild.py:760-762`) schreibt
danach die **aktuelle** `SCHEMA_VERSION` und den **aktuellen** Sprachsatz. Das
Ergebnis ist genau der Zustand, gegen den die ganze Phase gebaut ist: ein Index,
der sich als aktuell ausweist und es nicht ist, ohne Banner und ohne Abweichung.
Das ist H-18-02.

Dieselbe Mechanik greift ohne Codewechsel, wenn ein Admin `FINDLING_LANGUAGES`
aendert, waehrend ein halb gefuelltes Ziel liegt: die erste Haelfte traegt den
alten Satz, die zweite den neuen, gestempelt wird der neue.

### 3.5 Die fuenf Zustaende des Aufraeumpfads

Geprueft, ob es einen sechsten gibt. Alle acht Kombinationen der drei
Verzeichnisnamen landen in einem der fuenf Zweige von `rebuild.py:677-716`:

| live | rebuild | retired | Zweig | Urteil |
|---|---|---|---|---|
| nein | nein | nein | `NOTHING_TO_PUT_IN_ORDER` | richtig, erster Start |
| nein | ja | nein | Ziel anheben | richtig |
| nein | nein | ja | Stillgelegtes zurueck | richtig |
| nein | ja | ja | Ziel anheben, Stillgelegtes verwerfen | richtig, `swap_in` hatte `counts_match` bestanden |
| ja | nein | nein | `NOTHING_TO_PUT_IN_ORDER` | richtig, Normalfall |
| ja | nein | ja | Stillgelegtes verwerfen | richtig |
| ja | ja | nein | Ziel behalten | richtig |
| ja | ja | ja | Stillgelegtes verwerfen, Ziel bleibt liegen | richtig, Ziel wird spaeter wieder aufgenommen |

**Zu Grossschreibungskollisionen:** auf einem Dateisystem, das Gross- und
Kleinschreibung nicht unterscheidet, bleiben `index`, `index.rebuild` und
`index.retired` drei verschiedene Namen; ein `Index` auf der Platte wuerde von
`is_dir()` und `rename()` gleichermassen getroffen. Keine Kollision, kein
Befund.

**Was der Zweig nicht abdeckt**, ist ein `index.rebuild`, das eine **Datei** und
kein Verzeichnis ist: `target.is_dir()` ist dann False, der Aufraeumpfad sieht
nichts, und `open_index` scheitert spaeter an `mkdir` mit `FileExistsError`
(L-18-05). Und Zustand 3 hebt zwar das Ziel an, stempelt aber nicht, weil nur
`rebuild_the_index` stempelt (L-18-07).

### 3.6 reset_read_side unter Last

Zwei getrennte Wettlaeufe, beide MEDIUM.

**Der erste** sitzt in `filled_languages` (`resources.py:497` gegen
`resources.py:519`): `read_side()` wird **ausserhalb** der Sperre gelesen, der
Cache **innerhalb** geschrieben. Laeuft `reset_read_side()` dazwischen, fuellt
der spaetere Schreiber den gerade geleerten `_FILLED`-Eintrag wieder mit dem
Messwert des stillgelegten Verzeichnisses, und weil sich der Pfad beim Tausch
nicht aendert, passt der Schluessel. Die Admin-Seite meldet bis zu 30 Sekunden
lang den Zustand vor dem Umbau (M-18-02). `degraded()` hat dieselbe Form.

**Der zweite** ist groesser. In `rebuild.py:922-923` stehen `drop_read_side()`
und `swap_in(...)` als zwei aufeinanderfolgende Anweisungen ohne gemeinsame
Sperre. Eine Suche, die in diesem Fenster ankommt, ruft `read_side()`, findet
den Cache leer, oeffnet das Live-Verzeichnis und legt das Handle ab. Kurz darauf
benennt `swap_in` dieses Verzeichnis um und `discard_directory` entfernt es. Auf
Linux gelingt beides, weil ueber Inodes umbenannt wird; das zwischengespeicherte
Handle beantwortet danach jede Suche aus einem Verzeichnis, das es nicht mehr
gibt, und zwar bis zum Neustart des Containers. Das ist genau Fallstrick 3 der
Phasenrecherche, gegen den `reset_read_side` geschrieben wurde, und das Fenster
ist offen geblieben (M-18-03).

### 3.7 Doppellaufschutz der Lifespan-Aufgabe

Geprueft und in Ordnung, mit einer Einschraenkung. Innerhalb eines Prozesses
gibt es genau eine Aufgabe: `main.py:690-693` legt sie einmal an, sie ist keine
Schleife, und sie endet nach einem Lauf. Ueber mehrere Container hinweg schuetzt
`shared_volume.other` (`main.py:692`). `rebuild_the_index` ist gegen einen
zweiten Aufruf im selben Prozess nur an einer Stelle gehaertet, naemlich der
Ruecksetzung von `_BLOCKED_BYTES` (`rebuild.py:840`); mehr braucht es beim
heutigen einzigen Aufrufer nicht. Kein Befund.

Die Abschaltung dagegen haelt nicht, was sie zusagt (M-18-07): `rebuilding.cancel()`
in `main.py:717` beendet die wartende Aufgabe, nicht den Arbeitsfaden in
`asyncio.to_thread`. Der Faden laeuft weiter, `asyncio.run` verbindet sich am
Ende ueber `shutdown_default_executor` ohnehin mit ihm, und `REBUILD_STOP_SECONDS`
begrenzt deshalb nichts. Schlimmer: der abgekoppelte Faden kann die beiden
Umbenennungen und das `rmtree` noch ausfuehren, waehrend der Rest des Lifespans
bereits aufraeumt.

### 3.8 filled_languages gegen einen Index der alten Generation

`resources.py:509` baut das Ergebnis in **einem** Generatorausdruck ueber alle
sechs Eintraege von `BODY_FIELD`. Ein Index mit neun Feldern kennt `body_es`
nicht, `terms_with_prefix` wirft, und der `except`-Zweig darueber
(`resources.py:516`) verwirft die **ganze** Liste und antwortet `()`. Das ist
der Normalzustand jeder Installation, die aus 1.2.0 kommt und noch nicht
umgebaut hat, also genau der Installation, fuer die diese Zeile geschrieben
wurde. Die Admin-Seite schreibt dann "Sprachen des Index: de,en eingeschaltet,
mit Text im Index." mit einer leeren zweiten Liste, behauptet also, keine
einzige Kette trage Text. Der Kommentar im Quelltext nennt diesen Fall
ausdruecklich als "the realistic shape of this failure" und waehlt trotzdem die
schlechteste Behandlung. Das ist M-18-01.

---

## 4. Performance

### 4.1 Kosten des Bandlaufs

Die Bandgroesse von 500 ist begruendet und die Groessenordnung stimmt: 500 mal
15 kB sind 7,5 MB gleichzeitig gehalten, deutlich unter dem Writer-Heap von
50 MB. Die Bandabfrage laeuft ueber das schnelle Feld statt ueber einen
wachsenden Offset (`rebuild.py:495-504`), was den quadratischen Verlauf
vermeidet, den der Kommentar dort misst. `wait_merging_threads()` steht im
`finally` und damit auf jedem Ausgang. Kein Befund.

Eine Anmerkung ohne Befundnummer: `settings()` wird in `transfer_documents`
dreimal aufgerufen (`rebuild.py:472`, `483` zweimal). Die Funktion ist laut
`config.py:1240` per `@lru_cache` einmal pro Prozess zwischengespeichert, also kostenlos.

### 4.2 rebuild_progress als Modulglobal

Geprueft, kein Befund. `_PROGRESS` wird pro Band genau einmal zugewiesen
(`rebuild.py:312`), `RebuildProgress` ist `frozen=True, slots=True`, also
unveraenderlich, und eine Zuweisung an ein Modulglobal ist unter dem GIL
atomar. Der Leser (`rebuild_progress`, gerufen aus dem Statusfaden) kann eine
alte oder eine neue Instanz sehen, nie eine halbe. Ein zerrissener Wert ist
ausgeschlossen, weil die drei Zahlen in einem Objekt reisen und nicht in drei
Globalen. Uvicorn faehrt hier einen Worker; selbst mit mehreren waere die
Antwort pro Prozess richtig und die Umbauaufgabe liefe wegen
`shared_volume.other` ohnehin nur einmal.

### 4.3 Kosten der Statusroute je Aufruf

Die Route laeuft vollstaendig in `asyncio.to_thread` (`status.py:487-490`), die
Ereignisschleife wird also nicht blockiert. Das war die wichtigste Frage und sie
ist sauber beantwortet.

Neu hinzugekommen ist trotzdem eine Messung, deren Kosten mit der Indexgroesse
wachsen: `filled_languages` sondiert **alle sechs** Termwoerterbuecher, auch auf
einer Instanz, die nur `de` faehrt, und `terms_with_prefix` laeuft laut der im
Quelltext zitierten Dokumentation das ganze Woerterbuch ab, bevor das Limit
greift. Bei den 560 MB Indexverzeichnis, die `schema.py` fuer 100000 Dateien
hochrechnet, sind das sechs vollstaendige Woerterbuchlaeufe alle 30 Sekunden,
solange eine Admin-Seite offen ist, auf einer 4-GB-Box. Das ist M-18-08.

Der Rest der Route ist unveraendert: `index_bytes` laeuft wie bisher ueber das
Verzeichnis, die Store-Verbindung wird pro Aufruf geoeffnet und geschlossen.

### 4.4 Zwei Indexverzeichnisse auf kleinen Boxen

Die Vorpruefung ist bewusst konservativ (0,40 statt der gemessenen 0,372 je
Kette) und rechnet den Mindestfreiraum obendrauf statt hinein
(`rebuild.py:249-265`). Das ist die richtige Richtung.

Zwei Einschraenkungen: bei einer Wiederaufnahme wird der volle Bedarf erneut
verlangt, obwohl die Haelfte schon auf dem Volume liegt (L-18-03), und bei einem
symbolisch verlinkten Indexverzeichnis misst `shutil.disk_usage(index_dir)` das
Zielvolume, waehrend `index.rebuild` auf dem Elternvolume angelegt wird
(M-18-04). Im zweiten Fall pruft die Vorpruefung das falsche Dateisystem.

---

## 5. Die CRITICAL und HIGH im Einzelnen

### C-18-01: Der Tausch loescht ein Verzeichnis, auf dem der Poller einen offenen IndexWriter haelt

**Datei:** `backend/src/findling/index/rebuild.py:548`, `:561`, `:564-606`;
`backend/src/findling/worker/poller.py:519-526`, `:1510-1511`;
`backend/src/findling/index/writer.py:174`; `backend/src/findling/main.py:343-355`

**Befund.** `swap_in` benennt das Live-Verzeichnis um und `discard_directory`
entfernt es mit `shutil.rmtree`. Zu diesem Zeitpunkt haelt der Poller einen
`IndexWriter` auf genau diesem Verzeichnis: er wird in `Poller._open()` einmal
gebaut und erst in `aclose()` abgegeben, und `silence()` loescht nur ein Flag.
Der Modulkopf von `rebuild.py:42-43` behauptet ausdruecklich das Gegenteil.

**Folge, in zwei Schritten.** Erstens kann das `rmtree` mit einem `OSError`
enden, wenn die Merge-Faeden des Poller-Writers waehrend des Laufs Dateien
anlegen; `ignore_errors=False` ist gewollt, die Ausnahme steht aber ausserhalb
des `try` in `swap_in` und reisst `stamp_after_swap` mit, sodass die Marken alt
bleiben und der Umbau bei jedem weiteren Start erneut laeuft. Zweitens, und das
ist der schwerere Teil: `arm()` im `finally` (`rebuild.py:927`) stellt den
Poller wieder scharf, und dessen Writer zeigt weiterhin auf das entfernte
Verzeichnis. Auf Linux schreibt er in Inodes ohne Namen; jedes danach indexierte
Dokument ist verloren, ohne dass irgendwo etwas gemeldet wird, bis der Container
neu startet. Das ist stiller Datenverlust auf dem Normalweg, denn der Umbau
laeuft nur auf Installationen, die `was_enabled` sind, also genau dort, wo der
Poller seinen Writer offen hat.

**Kein Test deckt das ab.** `backend/tests/test_index_rebuild.py` uebergibt an
allen sechs Stellen Attrappen (`:1094`), die nur ein Journal fuehren; die
Zeitachse mit einem echten Poller wird nirgends gespielt.

**Fix-Vorschlag.** Die Zusage des Modulkopfes wirklich einloesen. Der Poller
braucht eine Methode, die den Writer freigibt und `self._writer = None` setzt,
und `_silence_the_poller` in `main.py:343` muss sie nach dem Abwarten von
`busy` aufrufen:

```python
# poller.py
async def stand_down(self) -> None:
    """Silence, wait for the pass in flight, and give the index handle back."""
    self._armed.clear()
    while self.busy:
        await asyncio.sleep(_STAND_DOWN_TICK)
    await self.unlock_held()
    writer, self._writer = self._writer, None
    if writer is not None:
        writer.close()          # commit + wait_merging_threads + drop the Index
    self._queue = None          # so that _open() builds a fresh handle on arm()
```

`_open()` baut Store, Writer und Queue beim naechsten `arm()` ohnehin neu auf,
sobald `self._queue` None ist. Ergaenzend: `discard_directory` gehoert in den
`try` von `swap_in`, damit ein Rest auf dem Volume den Stempel nicht verhindert.

### H-18-01: silence() wartet nicht auf den laufenden Indexlauf

**Datei:** `backend/src/findling/main.py:343-355`;
`backend/src/findling/worker/poller.py:519-526`;
`backend/src/findling/index/rebuild.py:448-454`, `:888-893`

**Befund.** `transfer_documents` nennt die Bedingung, unter der es richtig
arbeitet, selbst: der Poller darf waehrend des Laufs nicht in den Quellindex
schreiben. Der Aufrufer stellt sie nicht her. `silence()` kehrt sofort zurueck,
der laufende Durchlauf arbeitet seinen Stapel zu Ende und committet. Der
Kommentar in `rebuild.py:888-892` erlaubt das ausdruecklich.

**Folge.** Ein Dokument, das in diesem Fenster mit einer `file_id` unterhalb des
Cursors ankommt, wird nie uebertragen. Bei der Erstindexierung eines Mounts sind
die `file_id` beliebig verteilt, das ist also kein Randfall. `counts_match`
schlaegt fehl, der Lauf endet in `RUN_INCOMPLETE`, und ab dort greift H-18-04.

**Fix-Vorschlag.** Derselbe `stand_down`-Aufruf wie in C-18-01; er loest beide
Befunde. Wenn ein Warten auf `busy` nicht gewuenscht ist, muss `rebuild_the_index`
den Quellzaehler **vor** dem ersten Band und **nach** dem letzten vergleichen
und bei Abweichung ohne Tausch abbrechen, statt sich auf den Vergleich mit dem
Ziel zu verlassen.

### H-18-02: Die Wiederaufnahme prueft Schema und Sprachsatz des Zielverzeichnisses nicht

**Datei:** `backend/src/findling/index/rebuild.py:472-483`, `:760-762`;
`backend/src/findling/index/open.py:118`; `backend/src/findling/index/schema.py:92-95`

**Befund.** `open_index` oeffnet ein vorhandenes `index.rebuild` mit
`Index.open`, also mit dem **persistierten** Schema. Bleibt ein halb gefuelltes
Ziel ueber einen Codewechsel hinweg liegen (was der Aufraeumpfad ausdruecklich
so will, `rebuild.py:709-714`), traegt der naechste Lauf in das alte Schema
ueber. Feldnamen, die dieses Schema nicht kennt, verwirft `add_document`
kommentarlos, wie `schema.py:92-95` selbst gemessen hat. `counts_match` zaehlt
nur Dokumente und ist zufrieden, `swap_in` installiert das Verzeichnis, und
`stamp_after_swap` schreibt die aktuelle `SCHEMA_VERSION` und den aktuellen
Sprachsatz darueber.

**Folge.** Ein Index, der sich als aktuell ausweist und es nicht ist: die neuen
Ketten sind leer, es gibt keine Abweichung, kein Banner und keinen zweiten
Versuch. Dasselbe passiert ohne Codewechsel, wenn `FINDLING_LANGUAGES` waehrend
eines liegengebliebenen Umbaus geaendert wird; das Ergebnis ist dann ein Index,
dessen eine Haelfte den alten und dessen andere Haelfte den neuen Sprachsatz
traegt.

**Fix-Vorschlag.** Beim Wiederaufsetzen pruefen, ob das Ziel zum laufenden Code
passt, und es sonst verwerfen statt fortzuschreiben:

```python
target = open_index(target_dir, constituents)
if target.schema != build_schema():
    LOGGER.warning("the half filled target was built by other code, it is discarded and started again")
    del target
    shutil.rmtree(target_dir)
    target = open_index(target_dir, constituents)
```

Vergleicht `Schema` nicht sauber, dann eine Merkerdatei `.rebuild-for` mit dem
`_fingerprint(expected)` in das Zielverzeichnis legen und beim Wiederaufsetzen
gegen den aktuellen Fingerabdruck halten. Der Fingerabdruck existiert bereits
(`open.py:196-204`), er wird hier nur nicht benutzt.

### H-18-03: recover_the_index_directories laeuft ungefangen im Lifespan

**Datei:** `backend/src/findling/main.py:565`;
`backend/src/findling/index/rebuild.py:552-561`, `:702-708`

**Befund.** `await asyncio.to_thread(recover_the_index_directories)` steht ohne
`try`. Die Funktion benennt um und ruft `discard_directory`, das bewusst mit
`ignore_errors=False` arbeitet. Ein Zustand, in dem das Verwerfen scheitert
(Symlink, Rechteproblem, ein `.nfs*`-Rest, ein Volume ohne Schreibrecht), wirft
damit aus dem Lifespan heraus.

**Folge.** Der Container startet nicht. Zustand 5 (`index.retired` neben einem
`index`) ist dabei der unangenehmste, denn in ihm ist die Suche vollstaendig
arbeitsfaehig: das Produkt faellt aus, weil ein Rest auf dem Volume nicht
weggeht. Der Zustand bleibt beim naechsten Start derselbe, es gibt also keine
Selbstheilung, sondern einen Neustartkreis unter AppAPI.

**Fix-Vorschlag.** Dieselbe Behandlung wie bei der vierten Lifespan-Aufgabe
geben: fangen, den Typnamen protokollieren und weiterlaufen. Die Anweisung
darueber begruendet nur, **warum** vor den Aufgaben aufgeraeumt wird, nicht,
warum ein Fehler dabei toedlich sein muesste.

```python
try:
    await asyncio.to_thread(recover_the_index_directories)
except Exception as error:
    LOGGER.error(
        "the index directories could not be put in order, an %s; the container starts on what is there",
        type(error).__name__,
    )
```

Zusaetzlich in `recover_the_index_directories` die beiden `discard_directory`
-Aufrufe (`rebuild.py:688`, `:707`) einzeln fangen: ein nicht loeschbarer Rest
darf die **Umbenennung** daneben nicht verhindern.

### H-18-04: Ein einziges verlorenes Dokument setzt den Umbau dauerhaft fest

**Datei:** `backend/src/findling/index/rebuild.py:359-374`, `:377-397`,
`:495-510`, `:906-918`; `backend/src/findling/main.py:692`

**Befund.** Der Abschluss haengt an `counts_match`, also an einer **Gleichheit**
zweier Dokumentzahlen (`rebuild.py:372-374`). Der Cursor geht nie zurueck: er
wird aus dem hoechsten `file_id` des Ziels gelesen (`rebuild.py:396`), und das
Band beginnt bei `cursor + 1`.

Fehlt dem Ziel auch nur ein Dokument, liefert der naechste Lauf keinen einzigen
Treffer mehr (der Cursor steht bereits am oberen Ende), schreibt nichts, und
`counts_match` schlaegt wieder fehl. Das gilt fuer jede Ursache: H-18-01, ein
korruptes Ziel, eine `file_id` von 0 (L-18-01), ein Loeschauftrag, der die
Quelle waehrend des Laufs schrumpfen laesst (dann ist das Ziel sogar groesser
als die Quelle, und die Gleichheit scheitert in der anderen Richtung).

**Folge.** Der Umbau laeuft bei **jedem** Containerstart erneut ueber den
gesamten Bestand, ohne je fertig zu werden. `index.rebuild` bleibt dauerhaft auf
dem Volume liegen und kostet ungefaehr die Groesse des Index. Die neu
eingeschalteten Sprachen funktionieren nie. Das Fortschrittsbanner und die
Abweichung bleiben stehen, und der Admin hat keinen Hebel: `FINDLING_REBUILD_FALLBACK`
wird nur im ersten Zweig gelesen (`rebuild.py:849`) und raeumt das liegengebliebene
Verzeichnis nicht weg.

**Fix-Vorschlag.** Drei kleine Aenderungen, die zusammen einen Ausweg bilden:

1. In `rebuild_the_index` bei `RUN_INCOMPLETE` mitzaehlen, ob der Lauf
   **Fortschritt** hatte (`run.documents_written > 0`). Ein zweiter
   fortschrittsloser Lauf verwirft das Zielverzeichnis und faengt frisch an,
   statt es ein drittes Mal zu versuchen.
2. `counts_match` auf `>=` umstellen und den Fall `target > source`
   protokollieren, statt ihn wie einen Fehlbetrag zu behandeln.
3. Ein `index.rebuild`, das `Index.open` nicht oeffnen kann, verwerfen statt
   durchzureichen (gleiche Stelle wie H-18-02).

---

## 6. Die MEDIUM im Einzelnen

### M-18-01: filled_languages verwirft alle sechs Messungen, wenn eine wirft

**Datei:** `backend/src/findling/api/resources.py:506-518`

Der Generatorausdruck ueber `BODY_FIELD.items()` steht in **einem** `try`. Auf
einem Index der alten Generation wirft `terms_with_prefix("body_es", ...)`, und
`except Exception` liefert `()` fuer alle sechs. Das ist der Normalzustand jeder
Installation aus 1.2.0, also genau die, fuer die diese Zeile gebaut wurde: die
Admin-Seite behauptet dann, keine Kette trage Text.

**Fix:** je Feld fangen, oder vorher gegen die Felder des geoeffneten Schemas
filtern.

```python
filled: list[str] = []
for code, field in BODY_FIELD.items():
    try:
        if searcher.terms_with_prefix(field, "", limit=1):
            filled.append(code)
    except Exception as error:
        LOGGER.debug("the chain %s could not be probed, an %s", code, type(error).__name__)
```

### M-18-02: filled_languages fuellt den gerade geleerten Cache wieder mit alten Werten

**Datei:** `backend/src/findling/api/resources.py:497`, `:503`, `:519`

`read_side()` wird ausserhalb der Sperre gelesen, `_FILLED` innerhalb
geschrieben. Laeuft `reset_read_side()` dazwischen, traegt der spaetere
Schreiber den Messwert des stillgelegten Verzeichnisses wieder ein, und der
Pfadschluessel passt, weil der Tausch den Pfad nicht bewegt. Bis zu 30 Sekunden
falscher Fuellstand nach dem Umbauende, also genau in dem Moment, fuer den die
Zeile gebaut wurde. `degraded()` hat dieselbe Form (`resources.py:456`).

**Fix:** eine Generationszahl neben den Caches fuehren, die `reset_read_side`
erhoeht, und beim Schreiben verwerfen, wenn sie sich geaendert hat. Alternativ
`side` innerhalb derselben Sperre holen.

### M-18-03: Zwischen drop_read_side und swap_in ist die Lesekappe nicht gesperrt

**Datei:** `backend/src/findling/index/rebuild.py:922-923`;
`backend/src/findling/api/resources.py:301`, `:376-421`

Eine Suche, die in das Fenster zwischen den beiden Anweisungen faellt, oeffnet
das Live-Verzeichnis neu und legt das Handle ab; kurz darauf wird dieses
Verzeichnis umbenannt und entfernt. Auf Linux gelingt beides, und das Handle
beantwortet danach dauerhaft aus einem Verzeichnis ohne Namen. Das ist der
Fallstrick, gegen den `reset_read_side` geschrieben wurde, und er ist offen
geblieben.

**Fix:** ein Riegel, den `read_side()` respektiert. Zum Beispiel ein
`_SWAPPING`-Flag unter `_LOCK`, das `read_side()` dazu bringt, `None` zu
antworten, gesetzt von `drop_read_side()` und geloescht vom Aufrufer nach
`swap_in`. Zwei Systemaufrufe lang beantwortet die Suche dann leer, was ohnehin
der dokumentierte Zustand dieses Fensters ist.

### M-18-04: Ein symbolisch verlinktes Indexverzeichnis bricht Vorpruefung und Aufraeumen

**Datei:** `backend/src/findling/index/rebuild.py:249-265`, `:547-561`, `:674-676`

Keine der drei Stellen fragt, ob `index` ein Symlink ist. Ist er es (ein
gaengiger Weg, den Index auf ein groesseres Volume zu legen), dann:

- misst `shutil.disk_usage(index_dir)` das **Zielvolume**, waehrend
  `index.rebuild` per `with_name` auf dem **Elternvolume** angelegt wird: die
  Platzpruefung prueft das falsche Dateisystem,
- benennt `retire_directory` den **Link** um und `target.rename(live)` legt ein
  echtes Verzeichnis an: der Index wandert stillschweigend auf das Elternvolume,
- wirft `shutil.rmtree` auf einen Symlink einen `OSError`, sodass
  `stamp_after_swap` ausfaellt und der Umbau bei jedem Start erneut anlaeuft.

**Fix:** in `rebuild_the_index` nach `live.is_dir()` ein
`if live.is_symlink(): return NO_LIVE_DIRECTORY` mit eigener Verdikt-Zeile und
einer Protokollzeile, oder die drei Namen aus `live.resolve()` ableiten. Beides
mit einem Satz in `docs/`.

### M-18-05: Das Platzbanner nennt den Neustart nicht, obwohl er noetig ist

**Datei:** `backend/src/findling/index/rebuild.py:315-341`;
`php/templates/admin.php:328-336`; `backend/src/findling/main.py:692`

`_BLOCKED_BYTES` wird nur am Anfang von `rebuild_the_index` zurueckgesetzt, und
diese Funktion laeuft genau einmal pro Containerstart. Der Text des Banners
sagt "Free that much, or set the environment variable
FINDLING_REBUILD_FALLBACK=fullreindex". Ein Admin, der Platz freigibt, wartet
danach vergeblich: das Banner bleibt stehen, und der Umbau startet erst beim
naechsten Neustart des Backends.

**Fix:** den Satz um den Neustart ergaenzen, in allen sechs Katalogen. Der
Alternativweg braucht ihn ebenfalls, denn eine geaenderte Umgebungsvariable wird
ohne Neustart nicht gelesen.

### M-18-06: _rebuild_is_due faengt nur OSError und stirbt an einer kaputten state.db

**Datei:** `backend/src/findling/main.py:386-397`

`open_read_only` (`repo.py:1581-1582`) liest direkt nach dem Verbinden ein
`PRAGMA journal_mode`. Eine Datei, die keine SQLite-Datenbank ist, wirft dort
`sqlite3.DatabaseError`; eine 0-Byte-`state.db`, die ein harter Kill
hinterlaesst, oeffnet sauber und wirft bei der ersten Abfrage
`sqlite3.OperationalError`. Der `except OSError` in `main.py:392` faengt
keines von beiden, und `resources.version_drift(store)` in `main.py:396` ist gar
nicht eingefasst. Die Folge ist ein Lifespan, der wirft, also ein Container, der
nicht startet.

Genau dieser Fall ist in `api/status.py:463-472` schon einmal aufgetreten und
dort mit `except (OSError, sqlite3.Error)` behandelt worden, mit einem
ausfuehrlichen Kommentar. Der neue Startpfad hat das Muster nicht uebernommen.
Der gleiche Fehler steht (schon vor dieser Phase) in
`resources.report_version_drift` (`resources.py:536`), weshalb dieser Befund den
Ausgang heute nicht aendert; er verdoppelt ihn.

**Fix:** `except (OSError, sqlite3.Error)` und den `version_drift`-Aufruf mit in
den `try` nehmen. Bei dieser Gelegenheit dasselbe in `report_version_drift`.

### M-18-07: REBUILD_STOP_SECONDS begrenzt nichts

**Datei:** `backend/src/findling/main.py:83-94`, `:705-719`

`rebuilding.cancel()` bricht die wartende Aufgabe ab, nicht den Arbeitsfaden in
`asyncio.to_thread`. Der Faden laeuft weiter; `asyncio.run` wartet beim
Herunterfahren ueber `shutdown_default_executor` ohnehin auf ihn. Die Zusage
des Kommentars ("a container that made its orchestrator wait for one is a
container the orchestrator kills") wird also nicht eingeloest, die Abschaltung
dauert so lange wie das laufende Band.

Schlimmer als die Wartezeit ist, was der abgekoppelte Faden danach noch tun
darf: `counts_match`, `drop_read_side`, zwei Umbenennungen und ein `rmtree`,
waehrend der Lifespan bereits Poller und Reconcile abraeumt.

**Fix:** entweder ehrlich warten (`await rebuilding` ohne Kappung, mit dem
Argument, dass `should_stop` zwischen zwei Baendern greift und ein Band kurz
ist), oder nach dem Timeout eine Abbruchmarke setzen, die `swap_in` vor der
ersten Umbenennung prueft. Der Kommentar muss in beiden Faellen die
tatsaechliche Semantik nennen.

### M-18-08: Die Fuellstandssonde laeuft ueber alle sechs Woerterbuecher

**Datei:** `backend/src/findling/api/resources.py:83-95`, `:509`

`terms_with_prefix(field, "", limit=1)` laeuft nach der im Quelltext zitierten
Dokumentation das gesamte Termwoerterbuch des Feldes ab, bevor das Limit greift.
Die Zeile tut das fuer alle sechs Felder, auch auf einer Instanz, die nur `de`
faehrt, und wiederholt es alle 30 Sekunden, solange eine Admin-Seite pollt. Bei
den 560 MB Index, die `schema.py` fuer 100000 Dateien hochrechnet, sind das
sechs vollstaendige Woerterbuchlaeufe pro Fenster auf einer 4-GB-Box. Die Route
laeuft zwar im Arbeitsfaden, belegt damit aber einen Platz im Default-Executor,
den sich Suche und Indexierung teilen.

**Fix:** nur die Felder aus `settings().languages` sondieren, plus `body_de`,
und das Fenster fallen lassen: `reset_read_side()` invalidiert den Wert bereits
beim einzigen Ereignis, das ihn wirklich bewegt, und die erste Fuellung einer
neuen Kette darf eine Minute spaeter sichtbar werden.

---

## 7. Die LOW im Einzelnen

**L-18-01: Eine file_id von 0 wird nie uebertragen.**
`rebuild.py:394-396` antwortet 0 fuer ein leeres Ziel, das Band beginnt bei
`cursor + 1`, also bei 1. Nextcloud vergibt heute keine 0, der Verlust waere
aber dauerhaft und wuerde ueber H-18-04 den ganzen Umbau festsetzen. Fix: einen
Sentinel unterhalb des Wertebereichs verwenden, oder die untere Grenze beim
leeren Ziel auf 0 setzen.

**L-18-02: cursor + 1 laeuft bei der hoechsten file_id ueber.**
`rebuild.py:499` bildet `cursor + 1`; steht der Cursor bei `2**64 - 1`, liegt
die untere Grenze ausserhalb des u64-Bereichs, und die Bindung wirft statt die
Schleife zu beenden. Fix: vor der Bandbildung `if cursor >= _HIGHEST_FILE_ID:
break`.

**L-18-03: Die Vorpruefung rechnet beim Wiederaufsetzen den vollen Bedarf.**
`rebuild.py:249-254` misst nur das Live-Verzeichnis und verlangt den vollen
Bedarf, obwohl ein halb gefuelltes `index.rebuild` bereits Platz belegt. Ein
Lauf, der bei 90 Prozent abgebrochen ist, kann damit abgelehnt werden, obwohl
er nur noch 10 Prozent braucht. Fix: `index_bytes(target)` vom Bedarf abziehen.

**L-18-04: Ein KeyError aus _document_from ist nicht diagnostizierbar.**
`rebuild.py:418-434` greift ohne Vorgabewert zu, was richtig ist; die Ausnahme
wird aber in `main.py:459-465` nur als Typname protokolliert, ohne Feld und ohne
`file_id`. Dazu kann `writer.wait_merging_threads()` im `finally`
(`rebuild.py:522`) selbst werfen und die Urspruengsausnahme ersetzen. Fix: den
Feldnamen in `_document_from` fangen und in einer eigenen Ausnahme mitfuehren
(kein Pfad, kein Inhalt), und das `wait_merging_threads` mit
`contextlib.suppress` gegen Maskierung sichern.

**L-18-05: index.rebuild als Datei statt als Verzeichnis wird uebersehen.**
`recover_the_index_directories` fragt ueberall `is_dir()`; eine gleichnamige
Datei ist fuer alle fuenf Zweige unsichtbar, und `open_index` scheitert spaeter
an `path.mkdir` mit `FileExistsError`. Fix: `exists() and not is_dir()` als
eigenen, protokollierten Zweig.

**L-18-06: Das Einschalten von en auf einer de-Instanz laeuft ohne Umbau durch.**
`repo.py:1476-1489`. Vom Owner entschieden und an drei Stellen dokumentiert,
deshalb LOW. Nicht dokumentiert ist der Nebeneffekt aus `open.py:288-293`: auf
einer Installation, die nie driftet, wird die Marke `languages` **nie**
geschrieben, die Ausnahme schliesst sich also nicht von selbst. Fix: den Satz
in `docs/language-analyzers.md` um diese Haelfte ergaenzen.

**L-18-07: Zustand 3 des Aufraeumpfads hebt das Ziel an, stempelt aber nicht.**
`rebuild.py:683-689` schliesst den Tausch ab, ohne `stamp_after_swap` zu rufen
(was hier auch schwierig waere, weil kein Store offen ist). Die Marken bleiben
also alt, und der naechste Start baut denselben, bereits richtigen Index ein
zweites Mal vollstaendig um. Kein Datenverlust, aber ein voller Durchlauf und
zeitweise die doppelte Verzeichnisgroesse. Fix: den Zustand als Rueckgabewert
an den Lifespan durchreichen und dort einmalig stempeln.

**L-18-08: String.replace interpretiert `$`-Folgen im Ersatz.**
`php/js/admin.js` setzt `languagesActive` und `languagesFilled` als Ersatz in
`.replace('%1$s', ...)` ein; `$&`, `` $` `` und `$'` im Ersatz werden von
JavaScript ausgewertet. Kein XSS, weil das Ergebnis in `textContent` landet,
aber ein entstellter Satz. Fix: die Ersetzung als Funktion uebergeben,
`.replace('%1$s', () => languagesActive)`.

**L-18-09: Der private frp-Schluessel bleibt im RUNNER_TEMP liegen.**
`.github/workflows/deploy-harp.yml:3947`, `:3956`, `:3977`.
`rebuild-certs.tar` enthaelt `client.key`, wird mit der Standardmaske angelegt
und nie entfernt. Auf den fluechtigen Runnern der Matrix ist das folgenlos, auf
einem selbst gehosteten waere es ein Befund. Fix: `umask 077` vor dem `docker
cp` und `rm -f "${certs}"` direkt nach dem zweiten `docker cp`.

**L-18-10: Das App-Passwort steht in der Prozessliste des Runners.**
`.github/workflows/deploy-harp.yml:3829-3835`. `curl -u "admin:${apppw}"`
uebergibt das Geheimnis als Argument. Fix: `--netrc-file` oder
`-u "admin:$(cat file)"` vermeiden und stattdessen `-H "Authorization: Basic ..."`
ueber eine Datei mit `--config`.

**L-18-11: docker rm -f vor docker create.**
`.github/workflows/deploy-harp.yml:3975-3976`. Scheitert `docker create`, ist
der Container weg und der Lauf endet ohne Backend, statt an einem
wiederherstellbaren Punkt. Nur CI, deshalb LOW. Fix: den neuen Container unter
einem Zwischennamen anlegen, erst dann den alten entfernen und umbenennen.

**L-18-12: _run_the_rebuild oeffnet den Store ohne meta.**
`main.py:414`. `open_store` ohne `meta=` saat `_DEFAULT_META`, also unter
anderem `schema_version = "unknown"` fuer jede Marke, die noch fehlt. Heute
unerreichbar, weil `_rebuild_is_due` vorher bereits eine Abweichung mit
vorhandenen Marken festgestellt hat, aber eine Falle fuer den naechsten
Aufrufer. Fix: die erwarteten Marken uebergeben wie in `poller._open_state`,
oder in einem Satz begruenden, warum hier keine Saat erwuenscht ist.

---

## 8. Was geprueft und nicht beanstandet wurde

- **Pfadableitung der drei Verzeichnisse.** Kein Aufrufer waehlt einen Pfad,
  `with_name` kann nicht mit leerem Namen scheitern, es gibt im ganzen Paket
  genau ein `rmtree` und drei `rename`. Abschnitt 2.1.
- **Die drei Legacy-Ausnahmen in Kombination.** Jede faellt einzeln geschlossen,
  und keine Kombination laesst einen fremden Index als kompatibel durch.
  Abschnitt 2.2.
- **Der private Schluessel in der CI.** Weder im Schrittlog noch im Artefakt;
  die Kopierliste ist eine Positivliste und schliesst `rebuild-env.list`
  ausdruecklich aus. Abschnitt 2.3.
- **Escaping beider neuer Banner und der Sprachzeile.** `p()` in PHP,
  `textContent` im Skript, `PlainText::bounded` und `counter()` davor.
  Abschnitt 2.4.
- **Rechtegrenze.** Keine neue Route, kein neues Zugriffsniveau, kein Pfad und
  kein Benutzername in den fuenf neuen Feldern. Abschnitt 2.5.
- **Doppelte file_id im Quellindex.** Durch das Loeschen per Term vor jedem
  Einfuegen ausgeschlossen. Abschnitt 3.3.
- **Die fuenf Zustaende des Aufraeumpfads.** Alle acht Kombinationen der drei
  Namen sind abgedeckt, Grossschreibung kollidiert nicht. Abschnitt 3.5.
- **Doppellaufschutz der Lifespan-Aufgabe.** Eine Aufgabe, keine Schleife,
  `shared_volume.other` als zweite Schranke. Abschnitt 3.7.
- **rebuild_progress als Modulglobal.** Eine Zuweisung, ein unveraenderliches
  Objekt, unter dem GIL atomar; ein zerrissener Wert ist ausgeschlossen.
  Abschnitt 4.2.
- **Die Statusroute laeuft im Arbeitsfaden.** Die Ereignisschleife wird nicht
  blockiert. Abschnitt 4.3.
- **Bandgroesse und wait_merging_threads.** 500 Dokumente sind gegen Writer-Heap
  und RAM-Budget begruendet, das Warten steht auf jedem Ausgang. Abschnitt 4.1.
- **Die Migration Version001300Date20260924000000.** Wiederholungsfest, greift
  den Container nicht an, Klassenname und Dateiname sind identisch, der
  gedroppte Wert wird nicht durch eine Vermutung ersetzt.
- **Die sechs l10n-Kataloge.** Alle drei neuen Schluessel stehen in allen sechs
  Dateien, die Platzhalter `%1$s`, `%2$s` und `%s` stimmen in Zahl und Form mit
  den englischen Quellen ueberein.

---

## 9. Wie die Zahlen dieses Berichts nachzumessen sind

```bash
# Umfang
git diff --stat dfc871c..HEAD

# C-18-01: der Writer lebt so lange wie der Poller
grep -n "_writer" backend/src/findling/worker/poller.py
sed -n '519,526p' backend/src/findling/worker/poller.py     # silence() loescht nur ein Flag
sed -n '171,176p' backend/src/findling/index/writer.py      # der IndexWriter entsteht im Konstruktor
sed -n '671p;693p' backend/src/findling/main.py             # arm() 22 Zeilen vor der Umbauaufgabe

# H-18-02: das Ziel wird mit dem persistierten Schema geoeffnet
sed -n '117,119p' backend/src/findling/index/open.py

# H-18-03: kein try um die Aufraeumung
sed -n '560,570p' backend/src/findling/main.py

# M-18-01 und M-18-08: eine Ausnahme fuer sechs Sonden, sechs Sonden immer
sed -n '497,520p' backend/src/findling/api/resources.py

# Nur ein rmtree und drei rename im ganzen Paket
grep -rn "rmtree\|\.rename(" backend/src/findling/

# Die CI laesst weder den Schluessel noch die Umgebung in das Artefakt
sed -n '4329,4342p' .github/workflows/deploy-harp.yml
```
