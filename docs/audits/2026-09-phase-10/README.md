---
phase: 10-vergleichsmessung-auf-der-aws-box
audited: 2026-09-10
diff: af18542..HEAD
files_reviewed: 102
findings:
  critical: 0
  high: 0
  medium: 1
  low: 5
  total: 6
status: issues_found
fix_run: 2026-09-10
fix_commits: 5cefe1f
fixed: [M-01]
still_open: []
---

# Phase 10: Security-, Bug- und Performance-Audit

**Umfang:** `git diff af18542..HEAD`, 102 Dateien, 36 Commits. Die Aufteilung
nach Verzeichnis, aus dem Diff gezaehlt:

| Verzeichnis | Dateien | Was darin liegt |
|---|---:|---|
| `docs/measurements/` | 85 | 60 Rohdateien, 11 Skripte, das Kernaussage-Blatt, der Ablaufplan, der Bericht |
| `.planning/phases/` | 8 | die sieben Plaene und zwei `deferred-items.md` |
| `backend/tests/` | 2 | `test_measurement_scripts.py`, `test_ops_scripts.py` |
| `scripts/ops/` | 1 | `aws_box.sh` |
| einzeln | 6 | `docs/performance.md`, `CLAUDE.md`, `.gitattributes`, `STATE.md`, `ROADMAP.md`, `REQUIREMENTS.md` |

Dieser Bericht ist nach dem Muster von `docs/audits/2026-09-phase-09/README.md`
geschrieben und liegt nach der Owner-Regel vom 15.08.2026 vor dem
Phasenabschluss.

**Der erste Auftrag dieses Audits ist ein Blick in den Diff, und er hat eine
Antwort mit einem Wort.** Die Frage lautet: aendert diese Phase
Produktionscode? Die Pruefung:

```
git diff af18542..HEAD --name-only | grep -E '^(php/|backend/src/)'
```

**Ergebnis: keine einzige Zeile.** Diese Phase misst, sie baut nicht. Die
Audit-Objekte sind deshalb die Messskripte, die Rohdaten, der Bericht und die
geaenderten Projektdokumente, und nicht eine neue Angriffsflaeche im Erzeugnis.
Genau darauf beruht die Einordnung jedes Befundes weiter unten.

Dazu der Satz aus dem Phase-8-Audit, der hier wieder gilt: **ein Auditbefund an
einer Dokumentationszahl bekommt keinen Test, und der Bericht sagt warum, statt
einen zu erfinden.**

**Bilanz vorweg:** ein MEDIUM-Befund, gefixt in diesem Lauf; fuenf LOW-Befunde,
je mit Entscheidung und Wiedervorlage; kein CRITICAL und kein HIGH. Alle 46
nummerierten Threats der sieben Plaene und `T-10-SC` sind unten namentlich
abgehakt.

---

## 1. Sicherheit

Die zutreffenden ASVS-Kategorien dieser Phase sind **V2, V3, V4, V7 und V14**.
**V5 und V6 treffen nicht zu**, und das ist keine Auslassung, sondern folgt aus
dem Diff-Befund oben: es gibt keinen neuen Eingabepfad im Erzeugnis (V5), weil
keine Datei unter `php/` oder `backend/src/` geaendert wurde, und es gibt kein
eigenes Krypto (V6), weil kein Skript dieser Phase etwas verschluesselt,
signiert oder einen Schluessel ableitet. Der einzige Hashvorgang der Phase ist
`hashlib.sha256` in `40b-baumhash.py` und dient dem Vergleich zweier
Dateibaeume, nicht dem Schutz eines Geheimnisses.

### V2, Authentifizierung: kein Passwort in einer Kommandozeile, keins in einer Rohdatei

Die Messskripte melden sich als **echte Nutzer** an, ueber OCS und ueber die
Seitenroute. Das ist Absicht (V4 unten), macht aber Passwoerter zum Thema, weil
ein Argument in der Prozessliste der Box steht und in jedem Protokoll, das den
Befehl aufzeichnet.

**Pruefung 1, am Quelltext aller Skripte des Laufverzeichnisses:**

```
grep -rnE '\-\-password[= ]|\-p [A-Za-z0-9]{8,}|OC_PASS=[A-Za-z0-9]' skripte/ \
  | grep -v 'password-env\|password-from-env'
```

**Ergebnis: keine Zeile.** Gemessen wird ausschliesslich ueber
`search_load.py --password-env` (der **Name** der Umgebungsvariablen, nicht ihr
Wert) und ueber `occ user:add --password-from-env` mit `OC_PASS`. Das Gate aus
Plan 10-01 haelt die anderen Gestalten aus diesem Verzeichnis heraus und ist in
`backend/tests/test_measurement_scripts.py` verankert.

**Pruefung 2, maschinell an jeder der 60 Rohdateien:**

```
grep -rniE 'password[= ]|passwd|OC_PASS=[^ ]|AWS_SECRET|AKIA[0-9A-Z]{16}|ghp_|token=' rohdaten/
```

**Ergebnis: genau eine Zeile, und sie ist kein Geheimnis.**
`rohdaten/98-sprachfaelle.txt:11` traegt die occ-Ausgabe
`Successfully reset password for sprachfall`. Das ist eine Erfolgsmeldung ohne
den Wert; `occ` gibt das gesetzte Passwort nicht aus. Die Zeile bleibt
unveraendert stehen, weil eine geglaettete Rohdatei schlimmer ist als eine
ehrliche.

**Pruefung 3, die AWS-Zugangsdaten.** Sie wurden fuer die `status`- und
`stop`-Aufrufe aus einer Datei **ausserhalb des Arbeitsbaums** in die Umgebung
geladen. Weder ihr Inhalt noch ihr Pfad steht in einer Rohdatei oder in einem
Commit; `rohdaten/93-kosten-und-verbleib.txt` sagt das in Abschnitt 6 selbst.
`box.env` liegt unter `~/.findling-loadtest/` und ist nicht committet.

**Urteil V2: in Ordnung.**

### V3, Sitzungsverwaltung: der Origin-Kopf ist Pflicht und gesetzt

Zwei Wege dieser Phase bauen eine Cookie-Sitzung auf, und der
`LoginController` von Nextcloud 34 weist eine Anmeldung ohne `Origin`-Kopf ab.
Ein fehlender Kopf sieht dabei genau aus wie ein falsches Passwort, also ist er
nicht Dekoration, sondern die Bedingung dafuer, dass die Messung ueberhaupt eine
Messung ist.

| Weg | Stelle | Befund |
|---|---|---|
| `skripte/96d-statusbeobachter.py` | Zeile 215, `headers={"Origin": base_url}` | gesetzt; der Kommentar in Zeile 224 nennt ausdruecklich die Verwechslungsgefahr mit einem falschen Passwort |
| `skripte/99-seitenroute.sh` | Zeile 122, `-H "Origin: $BASE"` | gesetzt, zusammen mit dem Token aus dem Formular und dem Cookie-Jar |

Beide Wege holen den Token aus dem Anmeldeformular und schicken ihn mit; keiner
umgeht die Tokenpruefung. Die Reihen B und D der Seitenroute laufen bewusst
ueber **Basic-Auth** statt ueber die Sitzung, und der Bericht misst den Preis
dieses Weges getrennt (0,443 s je Anfrage am p95), damit keine Zahl den
Anmeldeweg mit der Seite verwechselt.

**Urteil V3: in Ordnung.**

### V4, Zugriffskontrolle: die Kernkategorie dieser Phase

**Erstens der Diff-Befund.** `git diff af18542..HEAD --name-only` nennt **keine
Datei unter `php/` und keine unter `backend/src/`**. Die Berechtigungskette ist
in dieser Phase nicht angefasst worden: kein zweiter Recheck, keine Zeile in
`Provider.php`, kein Weg um den Vorfilter herum. Der Kopf von `99b-runden.sh`
sagt denselben Satz vor der Messung, und der Diff bestaetigt ihn danach.

**Zweitens: jeder Messweg laeuft ueber die Kette und nicht daran vorbei.**

| Messblock | Weg | damit ueber den finalen PHP-Recheck |
|---|---|---|
| Nebenlaeufigkeitsreihe, fuenf Stufen | OCS `search/providers/findling/search` | ja |
| Kaltstart, beide Rollen | dieselbe OCS-Route | ja |
| Sprachfaelle, zehn Faelle | dieselbe OCS-Route, als eigener Nutzer `sprachfall` | ja |
| Seitenroute, Reihen A bis D | `/apps/findling/` beziehungsweise OCS mit `limit=100` | ja |
| Rundenzaehlung, beide Faelle | dieselbe OCS-Route | ja |

**Drittens, und das ist der wichtigste Satz dieses Audits: hat der provozierte
Driftfall jemandem etwas gezeigt, das er nicht sehen durfte?**

Der Aufbau erzeugt absichtlich einen Zustand, in dem der Vorfilter mehr erlaubt
als der Recheck: ein Konto `driftfall` bekommt 20 Freigaben, zwei gezaehlte
Poller-Durchgaenge werden abgewartet, die Kontrolle vor der Ruecknahme liefert
vier Treffer, dann werden die Freigaben um `14:14:14Z` zurueckgenommen **ohne
dem Poller Zeit zu geben**, und sofort wird gefragt. Genau in diesem Fenster
haette der Index noch Kandidaten fuehren koennen, die das Konto nicht mehr sehen
darf.

**Die Antwort steht in `rohdaten/99b-runden-drift.txt` und lautet: nein.**

```
treffer-vor-ruecknahme 4
ruecknahme 2026-09-10T14:14:14Z
fall2 suchen-gefahren        10
fall2 treffer-insgesamt      0
fall2 snippetaufrufe         0
treffer-nach-ruecknahme 0
```

**Null Treffer ueber zehn Suchen, null Snippetaufrufe.** Der Nutzer hat nach der
Ruecknahme keinen einzigen Treffer angezeigt bekommen. Die zehn
Kandidatenaufrufe an den Container fanden statt, aber es kam kein Ergebnis bis
zur Anzeige durch. Dass der Recheck das verhindert hat oder der Vorfilter schon
Bescheid wusste, ist fuer die Sicherheitsfrage gleichgueltig: **die
Berechtigungsgrenze hat in beiden Lesarten gehalten.**

Fuer die **Messfrage** ist es nicht gleichgueltig, und der Bericht sagt das
getrennt: null Treffer bei einer Runde je Suche heisst nach der dreiwertigen
Lesart des Skripts, dass die Drift zu kurz war und der Driftfall nicht erzeugt
wurde. **Die Sicherheitsaussage steht, die Messaussage nicht.** Zwei Fragen,
zwei Antworten, und sie werden hier nicht vermischt.

**Ein Nebenbefund derselben Kategorie, mit umgekehrtem Vorzeichen.** Die
Diagnose der Sprachfaelle zeigt einen Fall, in dem die Grenze **zu gut** haelt:
der Vorfilter rankt ueber den ganzen Index, der Recheck filtert erst danach, und
ein Nutzer mit wenigen Dateien neben 52.111 fremden bekommt eine leere Liste
statt seiner eigenen Datei. Das ist **kein Sicherheitsbefund** (es wird nichts
gezeigt, was nicht gezeigt werden darf), sondern ein Fund- und
Verfuegbarkeitsbefund. Er ist als DI-07-03 an Phase 11 uebergeben.

**Urteil V4: in Ordnung, mit der ausdruecklichen Antwort auf die Driftfrage.**

### V7, Fehlerbehandlung und Protokollierung

**Rohdaten unveraendert committet.** Die 60 Rohdateien tragen die Ausgabe der
Skripte, wie sie entstand. Zwei Faelle sind ausdruecklich zu nennen, weil sie
wie Ausnahmen aussehen und keine sind:

- `rohdaten/99b-runden-alltag.txt` und `rohdaten/99b-runden-drift.txt` sind
  **Auszuege** aus `99b-runden.txt`. Ihre Kopfzeile sagt das, die Quelldatei
  liegt unveraendert daneben, und kein Wert ist geaendert.
- `rohdaten/00-ende.txt` und `rohdaten/48-vektorbestand.txt` sind
  **Auswertungen**, die rechnen statt zu messen. Ihre Kopfzeile sagt das in
  Satz eins und nennt zu jeder Zahl die Rohdatei, aus der sie kommt.

**Kein Ausreisser entfernt.** Reihe A der Seitenroute traegt ein Maximum von
0,445 s gegen einen p95 von 0,332 s, Reihe D eines von 0,825 s. Beide stehen
unveraendert im Bericht.

**Die Statusreihe traegt keinen Namenstraeger.** `96-statusseite.jsonl` hat 812
Aufnahmen; jede traegt Zaehler und Zustandswoerter, keinen Dateinamen, keinen
Pfad, keinen Nutzernamen. Der Docstring von `96d-statusbeobachter.py` nennt die
Regel, und `test_measurement_scripts.py` prueft sie an einer gestellten
Aufnahme.

**Ein Gegenbeispiel, das kein Geheimnis ist, aber genannt gehoert.**
`rohdaten/98-sprachfaelle.txt` enthaelt Dateinamen (`09-bescheid.pdf`) und
Textausschnitte aus den Dokumenten des **Referenzkorpus** des Repositories.
Diese Dateien liegen unter `testdata/corpus` und sind Teil des oeffentlichen
Repositories; es sind keine Nutzerdaten. Gleiches gilt fuer die Pfade in
`93-nullstand.txt`, die auf `loadtest`-Dateien des generierten Korpus zeigen.

**Urteil V7: in Ordnung.**

### V14, Konfiguration

**Die SSH-Regel steht auf genau einer Adresse mit `/32`, revoke vor
authorize.** Geprueft am Quelltext von `scripts/ops/aws_box.sh`:

```
560:  # (T-06.1-78). Revoke first and authorize afterwards: the other order leaves
590:  ec2 revoke-security-group-ingress --group-id "$BOX_SECURITY_GROUP" ...
593:  response=$(ec2_soft authorize-security-group-ingress ...
595:    --ip-permissions "...FromPort=22,ToPort=22,IpRanges=[{CidrIp=$owner/32,...}]")
605:  echo "aws_box: ssh is open to $owner/32 and to nothing else"
```

Die Reihenfolge ist die richtige: die andere liesse fuer einen Moment beide
Adressen offen. Der Kommentar in Zeile 560 nennt den Threat aus Phase 6.1
namentlich (T-06.1-78), aus dem die Regel stammt.

**Die harte cgroup-Grenze wurde nach jeder Registrierung neu gesetzt und
zurueckgelesen, mit Wert im Protokoll.** Belege, jeder mit seiner Rohdatei:

| Zeitpunkt | Gelesener Wert | Rohdatei |
|---|---|---|
| vor jedem Eingriff, aus `docker inspect` | `Memory=2147483648 MemorySwap=2147483648` | `rohdaten/90-bestand.txt` |
| nach der Registrierung, aus der cgroup | `memory.max=2147483648`, `memory.swap.max=0` | `rohdaten/94-grundlast.txt` |
| waehrend des ganzen Laufs, in jeder Ablesung | `memory.max` 2147483648 | `rohdaten/07-oom-beweis.txt`, vier Ablesungen |
| nach dem bewussten Neustart | `memory.max=2147483648` | `rohdaten/95-spitze-nachher.txt` |

`92-wechsel.sh` bricht bei Abweichung mit 9 ab, also ist die Feststellung
erzwungen und nicht erinnert. **Keine Speicherzahl dieses Laufs kommt aus dem
Docker-Klienten**; gelesen wird die cgroup unter
`/sys/fs/cgroup/system.slice/docker-<CID>.scope/`, und ein Test haelt die zwei
Woerter des Klienten aus `rss_sampler.sh` heraus.

**Der Maschinenspeicherdeckel** `mem=4G` steht in `/proc/cmdline` und ist
zurueckgelesen (`rohdaten/90-bestand.txt`, `mem-cap-gefunden ja`).

**Urteil V14: in Ordnung.**

### Lieferkette

`T-10-SC` steht in allen sieben Plaenen. Die Pruefung:

```
git diff af18542..HEAD --name-only \
  | grep -E '(pyproject\.toml|uv\.lock|composer\.(json|lock)|package(-lock)?\.json)'
```

**Ergebnis: keine Zeile.** Diese Phase hat kein Paket installiert und keine
Abhaengigkeitsdatei angefasst. Die neuen Python-Dateien importieren ausser der
Standardbibliothek nichts. Das Abbild wurde **gezogen und nicht auf der Box
gebaut** (`rohdaten/92-wechsel.txt`), und `docker.yml` prueft Manifest und
Provenance.

**Ein Punkt, den dieser Bericht ausdruecklich richtigstellt:** das ist ein
**Pruefpfad** und keine GitHub-Artefakt-Attestierung. Der Messbericht
beschreibt das Abbild in Abschnitt 1 entsprechend und behauptet keine
kryptographisch nachweisbare Herkunftskette. Das war T-10-51, und es ist
eingehalten.

### Threat-Register der Phase, Zeile fuer Zeile

Alle 46 nummerierten Threats der Plaene 10-01 bis 10-06 plus die neun des Plans
10-07 (T-10-47 bis T-10-54) plus `T-10-SC`. Ein Threat ohne Zeile waere ein
Fehlschlag dieses Audits.

**Plan 10-01, die Werkzeugluecken:**

| ID | Umgesetzt, oder warum nicht zutreffend |
|---|---|
| T-10-01 | Umgesetzt und **wirksam geworden**: `40b-baumhash.txt` ist die erste nicht leere Baumhash-Rohdatei dieses Projekts, mit drei `baumhash:`-Zeilen und `baumhash-gleich ja`. In beiden Vorlaeuferberichten blieb genau diese Datei leer. |
| T-10-02 | Umgesetzt: `.gitattributes`-Regel plus Renormalisierung der fuenf Altfaelle. Kein Skript ist im Lauf an einer Shebang gescheitert; alle elf liefen auf der Box. |
| T-10-03 | Umgesetzt und geprueft (V2 oben): kein Passwort in einer Kommandozeile im Verzeichnis dieses Laufs. |
| T-10-04 | Umgesetzt: der Docstring von `40b-baumhash.py` verbietet die Aenderung mit Begruendung, zwei Zusicherungen halten Normalisierung und Pfadabhaengigkeit fest. Das Rezept ist waehrend der Phase nicht geaendert worden. |
| T-10-05 | Umgesetzt: `40b-baumhash.py` gibt ausschliesslich Pfad und Hash aus. `rohdaten/40b-baumhash.txt` traegt keinen Dateiinhalt. |

**Plan 10-02, die native arm64-Feinmessung:**

| ID | Umgesetzt, oder warum nicht zutreffend |
|---|---|
| T-10-06 | Umgesetzt: die emulierte Datei ist umbenannt (`01-grundlast-fein-arm64-emuliert.txt`) und nicht geloescht, und unter jeder nachgezogenen Tabelle steht die Vorlaeuferzahl. |
| T-10-07 | Umgesetzt: der Kopf jeder Rohdatei nennt Runner und `uname -m`. Teil D dieses Laufs traegt `arch=aarch64`. |
| T-10-08 | **Eingetreten und behandelt.** `92-wechsel.sh` schreibt `digest-gleich nein`: der auf der Box aufgeloeste Digest ist nicht der von Plan 10-02 aufgeschriebene. Der Grund steht in der Rohdatei (`:dev` ist ein wandernder Zeiger, der Pfadfilter von `docker.yml` greift nach `backend/**`). Die Feststellung, die entscheidet, ist der Baumhash, und der stimmt. Als LOW-Befund L-05 gefuehrt und als DI-10-05 an Phase 11 uebergeben. |
| T-10-09 | Umgesetzt: die drei Feststellungen vor dem Dispatch (sauberer Baum, `main` gleich `origin/main`, leerer Diff gegen den letzten `docker.yml`-Commit) sind in Plan 10-02 gefahren worden. |
| T-10-10 | Umgesetzt: uebernommen wurde ausschliesslich das Artefakt des Messschritts, nicht das Laufprotokoll. Die V2-Pruefung oben findet in keiner der Rohdateien ein Token. |

**Plan 10-03, das Skriptset vor dem Volllauf:**

| ID | Umgesetzt, oder warum nicht zutreffend |
|---|---|
| T-10-11 | Umgesetzt und **doppelt belegt**: `nextcloud-einzahl ja` in `rohdaten/90-bestand.txt` vor jedem Eingriff, `nextcloud-instanzen 1` in `rohdaten/92-wechsel.txt` unmittelbar vor dem `--rm-data`. Der Aufruf stand vor dem Indexaufbau und nie danach. |
| T-10-12 | Umgesetzt, siehe V14 oben: `memory.max=2147483648` nach der Registrierung aus der cgroup zurueckgelesen. |
| T-10-13 | Umgesetzt: `92-wechsel.sh` prueft die Rohdatei auf drei `baumhash:`-Zeilen und auf das Urteil. |
| T-10-14 | Umgesetzt: `52-woher-die-grundlast.py` und `01-grundlast-fein.py` wurden unveraendert gerufen. Die Schrittnamen in `rohdaten/94-grundlast.txt` sind wortgleich mit denen der Vorlaeufer, weshalb Abschnitt 5.2 des Berichts Zeile fuer Zeile vergleichen kann. |
| T-10-15 | Umgesetzt, siehe V2. |
| T-10-16 | Umgesetzt: `95-spitze.sh` verlangt eine Rolle und schreibt getrennte Rohdateien. Der Bericht fuehrt in Abschnitt 9 **beide** Zahlen mit ihrer Rolle: 1.550,4 ms auf leerem, 1.838,4 ms auf vollem Bestand. |
| T-10-17 | Umgesetzt und belegt: der OOM-Beweis wurde um 13:04:57Z, 13:05:11Z und 13:48:08Z erhoben, der Neustart fand um 14:04:38Z statt. Drei Ablesungen vor dem Eingriff. |
| T-10-18 | Umgesetzt: die Kopie der `info.xml` entstand ausserhalb des Arbeitsbaums; `git diff af18542..HEAD` nennt `backend/appinfo/info.xml` nicht. |

**Plan 10-04, die drei neuen Messbloecke:**

| ID | Umgesetzt, oder warum nicht zutreffend |
|---|---|
| T-10-19 | Umgesetzt und **wirksam**: `96c-lesen.py` liest unter `backend`, und die Statusreihe traegt 812 Aufnahmen mit echten Zahlen statt Nullen. Der Waechter hat das Ende nach 320 von 340 Runden erkannt, also nicht am Deckel. |
| T-10-20 | Umgesetzt: `00-FERTIG` wurde um 13:05:11Z geschrieben, vor dem Aufruf der Meldekette. `rohdaten/99-ntfy-watch.log` traegt den HTTP-Code jedes Versuchs (`http=200` beim Anstoss). Der 403 vom 05.09. ist nicht wiedergekehrt. Kein Schritt hing an einer Nachricht. |
| T-10-21 | Umgesetzt, siehe V7: `96-statusseite.jsonl` traegt keinen Namenstraeger. |
| T-10-22 | Umgesetzt: `search_load.py` statt `45-suchlast.py`, `96d-statusbeobachter.py` zum ersten Mal im Repo, kein Verweis auf `drillhelfer`. Bericht Abschnitt 18.2. |
| T-10-23 | Umgesetzt, aber **nicht ausreichend**, und das ist der Befund M-01 unten: das Konto war `sprachfall` und nicht `lasttest`, seine Heimat enthielt nur `testdata/corpus`, und die sechs kollidierenden Woerter standen im Kopf. Ein eigener Nutzer trennt aber die Berechtigung und nicht den Index. Als DI-10-02 an Phase 11. |
| T-10-24 | Umgesetzt: jede der vier Reihen nennt ihren Anmeldeweg in der Kopfzeile, beide Wege sind gemessen, und der Preis des Anmeldewegs steht als eigene Zahl (0,443 s). |
| T-10-25 | Umgesetzt: zwei getrennte Rohdateien, und Bericht Abschnitt 10 nennt bei beiden Faellen die Herstellung. Der Driftfall ist ausdruecklich als nicht erzeugt gefuehrt. |
| T-10-26 | Umgesetzt, siehe V4: alle Bloecke laufen ueber OCS beziehungsweise die Seitenroute, und der Diff nennt keine Datei unter `php/`. |
| T-10-27 | Umgesetzt, siehe V2: `occ user:add --password-from-env` mit `OC_PASS`, `--password-env` bei `search_load.py`. |

**Plan 10-05, die Anfahrt und der abgesetzte Lauf:**

| ID | Umgesetzt, oder warum nicht zutreffend |
|---|---|
| T-10-28 | Umgesetzt und **wirksam**: `91-korpus.sh` lief um 09:29:45Z, also 29 Minuten vor dem Anstoss, und schrieb `korpus-gleich ja` gegen `bcbef9b2...` und 20.208.046.426 Byte. |
| T-10-29 | Umgesetzt, siehe T-10-01 und T-10-13. |
| T-10-30 | Umgesetzt, siehe V14. |
| T-10-31 | Umgesetzt, siehe T-10-11. |
| T-10-32 | Umgesetzt: die Trockenprobe des Lesers lief gegen eine echte Aufnahme (`vorrat=2040 indexed=1653 embedded=264`), und der Waechter war nicht blind. |
| T-10-33 | Umgesetzt, siehe V14: `aws_box.sh start` zieht die Regel auf die aktuelle Owner-Adresse, revoke vor authorize, `/32`. |
| T-10-34 | Umgesetzt, siehe V2 Pruefung 2 und 3. |
| T-10-35 | Umgesetzt: der Poller lief nicht ins Backoff, sondern hat 50.458 Dokumente eingereiht. `94-grundlast.txt` zeigt die Backoff-Warnungen des **abgeschalteten** Zustands vor dem Anstoss; nach dem Einschalten der PHP-Haelfte kamen sie nicht wieder. |
| T-10-36 | Umgesetzt: die Rohdaten der Grundlast und der ersten Suche waren committet, bevor der Volllauf angestossen wurde. |
| T-10-37 | Umgesetzt: 360 Sekunden gegen Poller-Backoff und zwei Runden des Fuenf-Minuten-Systemcrons; die Gegenprobe fiel nach 361 s mit `arbeitsvorrat-da ja`. Die Urteile der Skripte stehen unveraendert, Nachtraege darunter. |

**Plan 10-06, die Messungen nach dem Lauf:**

| ID | Umgesetzt, oder warum nicht zutreffend |
|---|---|
| T-10-38 | Umgesetzt, siehe T-10-17: drei Ablesungen vor dem Neustart, `95-spitze.sh nachher` bricht ohne `96-oom-beweis.txt` mit 12 ab. |
| T-10-39 | Umgesetzt: der Abschnitt "Was dieser Lauf nicht besser gemacht hat" stand im Kernaussage-Blatt **vor** der Owner-Frage und steht im Bericht als Abschnitt 19 mit dreizehn Punkten. |
| T-10-40 | Umgesetzt: Bericht Abschnitt 11 fuehrt das Wort Erstmessung mit seiner Begruendung (`one_round()`, `side.vectors is not None`), und jede Reihe nennt ihren Anmeldeweg. |
| T-10-41 | Umgesetzt, siehe V2 und V7. |
| T-10-42 | Umgesetzt: `99b-runden.sh` und `98-sprachfaelle.sh` liegen in der **gefahrenen** Fassung unter `skripte/`, mit einem Satz im Kopf, der die Korrektur des `occ`-Wrappers nennt. Bericht Abschnitt 18.3. |
| T-10-43 | Umgesetzt: das Anhalten ist nicht vergessen worden. Die Wahl des Owners aus Punkt 6 hat es mit Zeitpunkt festgehalten nach Plan 10-07 verschoben, und `93-kosten-und-verbleib.txt` Abschnitt 5 fuehrt es als Auftrag. |
| T-10-44 | Umgesetzt: der Abbau ist nicht gefahren worden. Die Owner-Entscheidung vom 10.09. ist mit Datum in `docs/performance.md` unter "Der vierte Verbleib" festgehalten und als Auftrag fuer Phase 11 gefuehrt. |
| T-10-45 | Umgesetzt, siehe V4 und T-10-26. |
| T-10-46 | Umgesetzt: nach dem Neustart um 14:04:39Z steht `memory.max=2147483648` in `rohdaten/95-spitze-nachher.txt`. Die Grenze ist nicht gefallen. |

**Plan 10-07, der Bericht und die Nachzuege:**

| ID | Umgesetzt, oder warum nicht zutreffend |
|---|---|
| T-10-47 | Umgesetzt: Abschnitt 19 in eigener Ueberschrift, dreizehn Unterabschnitte, jeder mit seiner Rohdatei. |
| T-10-48 | Umgesetzt: 154 Verweise auf `rohdaten/` im Bericht, weit ueber den geforderten zehn. Die zwei gerechneten Quotienten in Abschnitt 14 sind ausdruecklich als Rechnung beschriftet. |
| T-10-49 | Umgesetzt, und **an zwei Stellen statt an einer**: der Satz an der urspruenglichen Zeile 3509 ist abgeloest, und eine zweite Fundstelle ("Das p95 ueber den vollen Bestand gehoert Phase 10") ist beim Nachziehen gefunden und ebenfalls abgeloest worden. Beide zeigen jetzt auf den Bericht mit seinem Datum. |
| T-10-50 | Umgesetzt: 1.837,8 MB steht weiter in `docs/performance.md`, und die Abschnitte des Semantiklaufs und der Nachmessung stehen unveraendert neben dem neuen. |
| T-10-51 | Umgesetzt, siehe Lieferkette oben. Das Wort "signiert" kommt im Messbericht fuer das Abbild nicht vor. |
| T-10-52 | Umgesetzt: die vier Erfolgskriterien sind in `ROADMAP.md` einzeln mit dem Abschnitt des Berichts belegt, und **Kriterium 2 ist ausdruecklich als nur teilweise erfuellt gefuehrt**, mit dem, was fehlt und wohin es gehoert. |
| T-10-53 | Umgesetzt, siehe V4: die Frage ist beantwortet, die Antwort ist nein, und der Beleg steht in `rohdaten/99b-runden-drift.txt`. |
| T-10-54 | Umgesetzt: der Nachzug in `README.md` und `docs/store-listing.md` ist als DI-10-03 in `deferred-items.md` der Phase 10 gefuehrt und dem Owner im Checkpoint ausdruecklich als Frage vorgelegt worden. |

**Und ueber alle sieben Plaene:**

| ID | Umgesetzt |
|---|---|
| T-10-SC | Umgesetzt, in allen sieben Plaenen dieselbe Pruefung, siehe Lieferkette oben: `git diff af18542..HEAD --name-only` nennt keine Abhaengigkeitsdatei, und kein Paket wurde installiert. |

---

## 2. Bugs

Das Bug-Audit dieser Phase prueft nicht Produktionscode (es gibt keinen neuen),
sondern die **Zahlen-Randfaelle** des Laufs: die fuenf Faelle, in denen eine
Messung eine Zahl liefert, die richtig aussieht und falsch gelesen wird. Fuer
jeden steht unten, ob er eingetreten ist, wo das steht, und was ihn beim
naechsten Lauf faengt.

### Randfall 1: der Vorrat, der 0 bleibt (Annahme A2)

**Eingetreten, und zwar in einer milden Form.** `93-nullstand.sh` hat nach der
Frist einen Arbeitsvorrat gefunden (`arbeitsvorrat-da ja` nach 361 s), also ist
der Abbruchpfad mit Rueckgabewert 10 nicht gelaufen. **Waehrend** des Laufs
stand `vorrat` allerdings in **62 von 325 Lesungen** auf 0
(`rohdaten/96b-waechter.txt`, gezaehlt), also in 19 Prozent der Runden. Das ist
kein Nullstand, sondern eine Zulauf-Luecke: der Poller hatte nichts zu tun,
obwohl der Lauf nicht fertig war.

**Wo das steht:** Bericht Abschnitt 7, als zweiter Kandidat fuer die
Mehrlaufzeit, und DI-10-04.

**Was ihn beim naechsten Lauf faengt:** `93-nullstand.sh` faengt den Nullstand
**vor** dem Lauf mit Rueckgabewert 10 und einer zweiten Frist. Die Luecken
**waehrend** des Laufs faengt bisher niemand automatisch; der Waechter schreibt
sie mit, aber ohne Urteil. Als LOW-Befund L-01 unten.

### Randfall 2: ein Leser, dessen Zahl ueber viele Runden exakt gleich bleibt (Fallstrick 8)

**Nicht eingetreten.** Die Statusreihe traegt 812 Lesungen mit bewegten Zahlen;
der Abstand `indexed` minus `embedded` schwankte zwischen 0 und 1.399 mit einem
Mittel von 158 (`rohdaten/00-ende.txt`). Ein Leser auf der falschen Ebene haette
Nullen oder eine Konstante geliefert.

**Wo das steht:** `rohdaten/96-statusseite.jsonl` und die Auswertung in
`00-ende.txt`.

**Was ihn faengt:** die fuenf Zusicherungen in
`backend/tests/test_measurement_scripts.py` machen die falsche Ebene rot, ohne
Box, plus die Trockenprobe vor dem Anstoss (T-10-32). Beide waren wirksam.

### Randfall 3: eine anon-Spitze deutlich ueber 2.048 MB ohne Meldung in `memory.events` (Fallstrick 4)

**Nicht eingetreten, und die Gegenprobe ist genau umgekehrt ausgegangen.** Der
hoechste `anon` des Laufs liegt bei 1.764,2 MB, also **unter** 2.048 MB, und
`memory.events` meldet trotzdem kraeftig: `max` steht auf 21.939. Das ist die
gesunde Richtung: der Kernel drueckt den **Dateicache** zurueck (`memory.current`
erreicht 2.048,0 MB), waehrend der Heap Luft hat.

Waere es umgekehrt gewesen (anon ueber der Grenze, `memory.events` auf null),
haette die Messung die falsche cgroup gelesen. Der Sampler nennt seine cgroup in
jeder Rohdatei (`docker-e40bfb29...scope`), und sie ist ueber alle Messbloecke
dieselbe.

**Wo das steht:** Bericht Abschnitte 4, 6 und 13.

**Was ihn faengt:** die Regel aus Muster 3, `anon` und `memory.current` immer
nebeneinander, in jeder der vierzehn Ablesestellen eingehalten. Der Bericht
haette die Diskrepanz sonst nicht zeigen koennen.

### Randfall 4: ein `length == 2` statt `1` bei einem Sprachfall (Fallstrick 3)

**Eingetreten, in der Gegenrichtung, und es ist der MEDIUM-Befund dieser Phase.**
Fall 6 verlangt zwei Dateien und bekam **eine** (`09-bescheid.pdf`); die Faelle
1, 2 und 4 verlangen genau eine Datei und bekamen **null**. Der Fallstrick ist
also nicht in der gefuerchteten Richtung eingetreten (zu viele Treffer aus dem
Lastkorpus), sondern in der umgekehrten: zu wenige, weil der Lastkorpus die
Kandidatenliste fuellt, bevor der Recheck ueberhaupt filtert.

**Wo das steht:** Bericht Abschnitt 12, `rohdaten/98-sprachfaelle.txt`,
`rohdaten/98b-sprachfaelle-diagnose.txt`.

**Was ihn beim naechsten Lauf faengt:** bisher nichts, und genau das ist M-01.

### M-01 (MEDIUM): der Messaufbau der Sprachfaelle trennt die Berechtigung und nicht den Index (BEHANDELT)

**Was:** `98-sprachfaelle.sh` fuehrt einen eigenen Nutzer ein, weil der
Lastkorpus dieselben Woerter traegt. Der Kopf des Skripts nennt Fallstrick 3
und sechs kollidierende Woerter. **Das reicht nicht:** ein eigener Nutzer
trennt die Berechtigung, nicht den Index. Der Vorfilter rankt ueber den ganzen
Index, und bei 52.111 fremden Dokumenten mit denselben Tokens kommt die Datei
des fragenden Kontos unter den ersten 2.000 Kandidaten nicht vor (fuer
`Bescheid` auf Rang 1.925 von 2.000).

**Warum MEDIUM und nicht HIGH:** die Bilanz `6 von 10` ist gemessen und richtig,
sie ist nur falsch **deutbar**. Kein Produktionscode ist betroffen, keine
Sicherheitsgrenze, und der Fehler faellt auf der Seite der Vorsicht: die Zahl
sieht schlechter aus als die Sache. Der CI-Lauf misst dieselben zehn Faelle
gruen (Lauf 34339346666, Commit `0dd007d3`).

**Warum kein Test.** Dies ist ein Befund an einem Messaufbau und an der Deutung
einer Dokumentationszahl, nicht an ausfuehrbarem Produktionscode. Ein Test, der
"der Lastkorpus darf die Begriffe der Sprachfaelle nicht enthalten" prueft,
braucht einen Lastkorpus, und der entsteht nur auf der Box. Ein Test, der auf
dem Runner gruen ist, weil es dort keinen Lastkorpus gibt, waere ein Test, der
genau das nicht prueft, wonach er benannt ist. **Der Bericht sagt das an seiner
Stelle, statt einen zu erfinden.**

**Der Fix in diesem Lauf, und das ist der Grund fuer die Einordnung als
behandelt:** die Deutung ist korrigiert worden, dort wo sie gelesen wird. Bericht
Abschnitt 12 fuehrt die Bilanz als Erstmessung mit Mess-Setup-Vorbehalt und sagt
in einem eigenen Absatz "Es ist also kein Sprachdefekt"; `REQUIREMENTS.md`
traegt denselben Satz im Beleg von MESS-02; `ROADMAP.md` fuehrt Erfolgskriterium
2 als nur teilweise belegt. Die **Aenderung am Skript** braucht eine neue Box
und ist als DI-10-02 an Phase 11 uebergeben. Commit `5cefe1f`.

### Randfall 5: eine Reihe, die 0,3 s ueber der Erwartung liegt und deren Kopfzeile den Anmeldeweg nicht nennt (Fallstrick 9)

**Nicht eingetreten.** Alle vier Reihen der Seitenroute nennen ihren Anmeldeweg
in der Kopfzeile (`Reihe A anmeldeweg sitzung` und so fort), und der Bericht
fuehrt ihn in jeder Tabellenzeile. Die Reihen B und D liegen mit 0,775 und
0,769 s rund 0,44 s ueber den Sitzungsreihen, und diese Differenz ist als Preis
des Anmeldewegs benannt statt der Seite zugeschrieben zu werden.

**Wo das steht:** `rohdaten/99-seitenroute.txt`, Abschnitt "Die Trennung, die
Befund M-03 verlangt"; Bericht Abschnitt 11.

**Was ihn faengt:** T-10-24, umgesetzt im Skript. Der Vorlaeuferbefund M-03 aus
dem Phase-9-Audit ist damit nicht wiederholt worden.

### Eine sechste Pruefung, die kein Randfall der Liste war und trotzdem etwas fand

`git diff af18542..HEAD --stat` gegen die Zahlen des Berichts gehalten: der
Bericht nennt in Abschnitt 18.4 sechsundzwanzig Rohdateien namentlich, im
Verzeichnis liegen sechzig. Die uebrigen sind Varianten derselben Messung
(`95-vorher-stufe-1.json` bis `-8.json`, `97-stufe-1.json` bis `-16.json`,
`99-reihe-a.txt` bis `-d.txt`), und der Bericht fuehrt sie mit Platzhaltern
(`rohdaten/97-stufe-<n>.json`). **Keine Rohdatei ist unerwaehnt**, aber die
Zaehlung ist nur ueber die Platzhalter nachvollziehbar. Als LOW-Befund L-04.

---

## 3. Performance

Die Zahlen dieses Laufs gegen ihre Budgets, jede mit ihrer Quelle im Bericht.

| Groesse | Gemessen | Budget oder Decke | Marge | Urteil |
|---|---:|---:|---:|---|
| p95 Stufe 1 | 464,3 ms | 2.500 ms | 2.035,7 ms | gehalten |
| p95 Stufe 4 | 1.068,0 ms | 2.500 ms | 1.432,0 ms | gehalten |
| **p95 Stufe 8 (die Zusage)** | **2.125,5 ms** | **2.500 ms** | **374,5 ms** | **gehalten, 85,0 Prozent des Budgets** |
| p95 Stufe 12 | 3.453,4 ms | 2.500 ms | minus 953,4 ms | gerissen, wie in 06-11 |
| p95 Stufe 16 | 4.446,2 ms | 2.500 ms | minus 1.946,2 ms | gerissen, wie in 06-11 |
| Kaltstart, voller Bestand | 1.838,4 ms | 1.500 ms je Aufruf | minus 338,4 ms | **gerissen** |
| Kaltstart, leerer Bestand | 1.550,4 ms | 1.500 ms je Aufruf | minus 50,4 ms | gerissen |
| Seitenroute A, Sitzung | 0,332 s | `PAGE_REQUEST_TIMEOUT_SECONDS` 1,5 s | 1,168 s | gehalten |
| Seitenroute C, tiefe Seite | 0,333 s | dieselbe | 1,167 s | gehalten |
| Seitenroute B, Basic-Auth | 0,775 s | dieselbe | 0,725 s | gehalten |
| Seitenroute D, `limit=100` | 0,769 s | dieselbe | 0,731 s | gehalten |
| alle vier Reihen | hoechstens 0,825 s (Maximum D) | `PAGE_BUDGET_SECONDS` 3,0 s | mindestens 2,175 s | gehalten |
| Rundenzahl, Alltag | 1,0 Runde, 1,9 Aufrufe, p95 683,6 ms | Gruppenbudget 2.500 ms | 1.816,4 ms | gehalten |
| Grundlast im Leerlauf | 103,2 MB | 2 GiB harte Grenze | 1.944,8 MB | gehalten |
| anon-Spitze des Laufs | 1.764,2 MB | 2 GiB harte Grenze | 283,8 MB | gehalten |
| `memory.peak` | 2.147.483.648 Byte | 2.147.483.648 Byte | **0 Byte** | an der Grenze, ohne Toetung |
| Indexgroesse, Vektoren | 1.318,3 Byte je Dokument | 1.321,0 (06-11) | minus 2,7 | unveraendert |
| Indexgroesse, Tantivy | 15.093 Byte je Dokument | 15.113 (06-11) | minus 20 | unveraendert |

**Die eine gerissene Decke ist der Kaltstart, und sie ist der Befund, der die
Phase ueberlebt.** Er ist als DI-07-02 mit Zahlen an Phase 11 uebergeben, samt
der Methodik-Korrektur, dass die gemessene Dauer die ganze OCS-Anfrage ist und
die Decke von 1.501 ms nur den inneren Containeraufruf betrifft. Der Abbruch
ist trotzdem belegt (`cURL error 28` um 14:05:17Z bei kaltem Wirtscache), und
die Entscheidung ueber die Konstante gehoert nicht in einen Messplan.

**`memory.peak` auf 0 Byte Marge ist keine Ueberschreitung.** Der Wert zeigt,
dass der Kernel die cgroup bis an die Grenze gefuellt hat und dann
zurueckgedraengt hat, statt zu toeten. Die drei Schadenszaehler stehen auf null,
`OOMKilled=false`, `RestartCount=0`. Es ist die knappste Zahl des Laufs und sie
ist im Bericht als Verschlechterung gefuehrt (Abschnitt 19.6).

### T-09-29 aus Phase 9, entschieden mit den Zahlen dieses Laufs

**Der Threat:** DoS durch einen vollen Vektorscan je Anzeigeseite. Das
Phase-9-Audit hat ihn mit `accept` geschlossen und als Begruendung gegeben,
dass die Zahlen fehlen. Sie liegen jetzt vor.

| Frage | Zahl | Quelle |
|---|---|---|
| Kostet eine tiefe Seite mehr als die erste? | 0,333 s gegen 0,332 s, also **nein** | Bericht 11, `rohdaten/99-seitenroute.txt` |
| Kostet `limit=100` mehr als `limit=20`? | 0,769 s gegen 0,775 s auf demselben Anmeldeweg, also **nein** | dieselbe |
| Was kostet der Vektorbestand gegenueber einer Instanz ohne? | rund 0,21 s je Anfrage (0,332 gegen 0,122 s) | dieselbe |
| Wie viel Marge bleibt im schlechtesten Fall? | 0,725 s zur Aufrufdecke, 2,175 s zum Seitenbudget | dieselbe |

**Entscheidung: `accept` bleibt, jetzt mit Zahlen statt mit deren Abwesenheit.**
Die Begruendung ist eine andere als vermutet: nicht "der Scan ist billig",
sondern **"der Scan laeuft einmal je Anfrage und nicht je Seite"**. Die
Seitentiefe ist damit kein Hebel fuer einen Angreifer, und die Trefferzahl auch
nicht. Der Hebel, der bliebe, ist die reine Anfragerate, und die deckelt die
Nebenlaeufigkeitszusage von acht: dort steht der p95 bei 2.125,5 ms.

**Wiedervorlage:** mit dem naechsten Vektorbestand, der die Groessenordnung von
146.171 Chunks deutlich ueberschreitet. Bis dahin traegt diese Messung die
Entscheidung.

**Kein Test.** Auch dies ist ein Befund an einer Dokumentationszahl. Ein Test,
der "die dritte Seite ist nicht teurer als die erste" prueft, braucht einen
Vektorbestand in der Groessenordnung des Laufs; auf dem Runner mit 26 Dokumenten
waere er gruen, ohne die Aussage zu pruefen.

---

## 4. LOW-Befunde, dokumentiert entschieden

### L-01: die Zulauf-Luecken waehrend des Laufs bekommen kein Urteil

**Was:** `vorrat=0` in 62 von 325 Waechterrunden. `93-nullstand.sh` faengt den
Nullstand **vor** dem Lauf mit Rueckgabewert 10; **waehrend** des Laufs
schreibt der Waechter die Nullen nur mit.

**Entscheidung: hinnehmen fuer diesen Lauf, benennen fuer den naechsten.** Ein
Urteil waehrend des Laufs muesste zwischen einer Luecke und dem Auslauf
unterscheiden, und der Auslauf sieht in den letzten drei Stundenbloecken genauso
aus. Eine Heuristik, die den Lauf am Ende faelschlich fuer krank erklaert,
kostet mehr als sie bringt.

**Wiedervorlage:** mit DI-10-04, wenn die Ursache der Mehrlaufzeit untersucht
wird. Ein Zaehler "Runden mit leerem Vorrat" in der Schlusszeile des Waechters
waere der kleine Teil davon.

### L-02: `rohdaten/99-seitenroute.txt` nennt in der Kopfzeile 145.854 Vektoren statt 146.171

**Was:** Die Kopfzeile begruendet die Erstmessung damit, dass "diese Instanz eine
vectors.db mit 145.854 Vektoren hat". 145.854 ist die Chunk-Zahl aus **06-11**;
diese Instanz traegt 146.171.

**Entscheidung: die Rohdatei bleibt unveraendert, die Korrektur steht im
Bericht.** Eine Rohdatei, deren Text nachtraeglich verbessert wird, belegt nicht
mehr, was das Skript geschrieben hat. Die Aussage der Kopfzeile (diese Instanz
hat einen Vektorbestand, der Vorlaeufer hatte keinen) ist richtig, nur die Zahl
darin ist aus dem Vorlauf uebernommen. Bericht Abschnitt 11 nennt beide Zahlen
und sagt, welche gilt.

**Wiedervorlage:** beim naechsten Lauf von `99-seitenroute.sh`. Die Kopfzeile
sollte die Zahl aus `42d-bestand.py` lesen statt sie im Skript zu fuehren.

### L-03: der Bericht nennt 26 Rohdateien namentlich, im Verzeichnis liegen 60

**Was:** Abschnitt 18.4 fuehrt die Rohdateien mit Platzhaltern
(`rohdaten/97-stufe-<n>.json`), also ist keine unerwaehnt, aber die Zaehlung
"jede Rohdatei mit einem Satz" ist nur ueber die Platzhalter nachvollziehbar.

**Entscheidung: hinnehmen.** Eine Tabelle mit fuenf Zeilen fuer
`97-stufe-1.json` bis `97-stufe-16.json`, die fuenfmal denselben Satz tragen,
macht den Abschnitt laenger und nicht klarer. Die Platzhalterform ist die des
Ablaufplans und damit die eingefuehrte.

**Wiedervorlage:** keine. Diese Entscheidung ist stabil.

### L-04: `skripte/__pycache__/` liegt lokal im Arbeitsbaum

**Was:** Das Ausfuehren von `96d-statusbeobachter.py` hat lokal ein
`__pycache__`-Verzeichnis unter `skripte/` erzeugt. **Es ist nicht committet**
(`git ls-files` nennt keine `.pyc`), und `git status --short` ist sauber, also
greift eine `.gitignore`-Regel.

**Entscheidung: kein Handlungsbedarf.** Der Befund ist geprueft worden, weil ein
committetes Bytecode-Verzeichnis in einem Messverzeichnis eine Rohdatei
vortaeuschen wuerde. Es ist keines committet.

**Wiedervorlage:** keine.

### L-05: der aufgeschriebene Digest von `:dev` haelt nicht

**Was:** `92-wechsel.sh` schreibt `digest-gleich nein`. Plan 10-02 hatte
`sha256:eed6a5fc...` aufgeschrieben, gemessen wurde `sha256:78ab61d8...`.
`:dev` ist ein wandernder Zeiger, und der Pfadfilter von `docker.yml` greift
nach `backend/**`.

**Entscheidung: hinnehmen, weil die Feststellung, die entscheidet, der Baumhash
ist**, und der stimmt (`baumhash-gleich ja`, 54 Dateien identisch in Abbild und
Arbeitsbaum). Ein Wechsel auf unbewegliche Tags ist eine Aenderung an der
Auslieferungskette und gehoert nicht in einen Messplan.

**Wiedervorlage:** Phase 11, als DI-10-05. Die Frage lautet, ob ein Messlauf
gegen `:dev` pruefen darf oder gegen einen unbeweglichen Tag laufen muss.

---

## 5. Was ausdruecklich in Ordnung ist

Damit dieser Bericht nicht nur die Befunde traegt, hier die Dinge, die geprueft
wurden und halten:

1. **Kein Produktionscode geaendert.** 102 Dateien im Diff, keine unter `php/`
   oder `backend/src/`. Eine Messphase, die nichts baut, ist die Messphase, die
   sie sein soll.
2. **Kein Paket installiert, keine Abhaengigkeitsdatei angefasst.**
3. **Der Baumhash-Beweis ist zum ersten Mal in diesem Projekt nicht leer.** Die
   Luecke, die beide Vorlaeuferberichte hatten, ist geschlossen, und der Grund
   dafuer (ein fehlendes `-i` am `docker run`) steht im Bericht statt in einer
   Erinnerung.
4. **Der Korpus ist byteweise derselbe**, geprueft **vor** dem 26-Stunden-Lauf
   und nicht danach.
5. **Der OOM-Beweis ist dreimal vor jedem Eingriff erhoben worden**, und
   `95-spitze.sh nachher` verweigert den Neustart ohne ihn.
6. **Genau eine Nextcloud auf der Box, zweimal gezaehlt**, und der
   `--rm-data`-Aufruf lag vor dem Indexaufbau. Der Vorfall vom 07.09. hat sich
   nicht wiederholt.
7. **Die harte Grenze steht in jeder Ablesung auf 2147483648** und wurde nach
   Registrierung und Neustart aus der cgroup zurueckgelesen.
8. **Die SSH-Regel steht auf genau einer Adresse mit `/32`**, revoke vor
   authorize.
9. **Kein Passwort in einer Kommandozeile, keins in einer Rohdatei**, geprueft
   maschinell ueber alle 60 Rohdateien und alle 11 Skripte.
10. **Der Origin-Kopf ist in beiden Sitzungswegen gesetzt.**
11. **Die Berechtigungsgrenze hat im provozierten Driftzustand gehalten**: null
    Treffer ueber zehn Suchen nach der Ruecknahme.
12. **Kein Ausreisser entfernt, keine Zahl geglaettet**, und die zwei
    Skriptfehler, die waehrend des Laufs korrigiert wurden, stehen mit einem
    Satz im Kopf der gefahrenen Fassung.
13. **Jede Verschlechterung steht in eigener Ueberschrift**, dreizehn an der
    Zahl, und der Abschnitt stand im Kernaussage-Blatt vor der Owner-Frage.
14. **Ein Erfolgskriterium ist als nur teilweise erfuellt gefuehrt**, statt
    aufgerundet zu werden.

---

## 6. Bilanz und Gate

| Schwere | Zahl | Stand |
|---|---:|---|
| CRITICAL | 0 | |
| HIGH | 0 | |
| MEDIUM | 1 | M-01, in diesem Lauf behandelt (Commit `5cefe1f`), Skriptaenderung als DI-10-02 an Phase 11 |
| LOW | 5 | L-01 bis L-05, je mit Entscheidung und Wiedervorlage |

**Das Audit-Gate der Owner-Regel vom 15.08.2026 ist gefahren.** Alle 46
nummerierten Threats der Plaene 10-01 bis 10-06, die acht des Plans 10-07 und
`T-10-SC` sind namentlich abgehakt. Der einzige Befund ab MEDIUM ist behandelt.
Die Frage, ob ein provozierter Driftzustand jemandem etwas gezeigt hat, ist
beantwortet und nicht uebersehen worden.

**Die Gates des Repositories, gefahren am 2026-09-10 in `backend/`:**
`uv run python -m pytest -q`, `uv run ruff check .`,
`uv run ruff format --check .`, `uv run pyright` und
`uv run vulture src tests --min-confidence 80`. Ihre Ergebnisse stehen im
Ausfuehrungsprotokoll des Plans 10-07.
