---
phase: 15-messphase-eine-box-anfahrt
audited: 2026-09-21
tree: b4f9c81d7b13778e7bd78a0a9c153e0641c1c956
commit: fb2f1ab22e6b5f5d3f402e3977d6b79d9fe822e8
findings:
  critical: 0
  high: 0
  medium: 2
  low: 11
  total: 13
status: issues_found
fixed: [L-01, L-02]
still_open: [M-01, M-02, L-03, L-04, L-05, L-06, L-07, L-08, L-09, L-10, L-11]
---

# Phase 15: Security-, Bug- und Performance-Audit

**Umfang:** die sechzehn Pläne 15-01 bis 15-16 dieser Phase, gelesen gegen den
Baum von Commit `fb2f1ab`. Dieser Bericht liegt nach der Owner-Regel vom
15.08.2026 vor dem Phasenabschluss und ist nach dem Muster von
`docs/audits/2026-09-phase-14/README.md` geschrieben.

Die Überschriften stehen ohne Umlaute, weil Prüfungen und Verweise auf sie
zeigen; der Fließtext benutzt echte Umlaute.

**Diese Phase hat keinen Produktcode geschrieben, und deshalb verschiebt sich
der Schwerpunkt dieses Berichts.** Unter `backend/src/findling` und unter `php/`
ist in den sechzehn Plänen keine Zeile geändert worden; was entstanden ist,
sind Messwerkzeuge, ein Laufverzeichnis, ein Runbook, Rohdaten einer bezahlten
Anfahrt und ein Bericht. Ein Audit, das hier nach Eingabeprüfung und
Rechtegrenze suchte, prüfte etwas, das diese Phase nicht angefasst hat. Die
Angriffsfläche dieser Phase ist eine andere und liegt in zwei Richtungen:
**erstens** in dem, was in öffentlich lesbare Dateien geraten ist, denn diese
Phase committet Rohdaten einer echten Maschine, und **zweitens** in der Frage,
ob die Zahlen halten, was sie behaupten. Beide bekommen hier ihren eigenen
Abschnitt.

**Bilanz vorweg:** kein CRITICAL, kein HIGH. Zwei MEDIUM: einer betrifft die
Aussagekraft einer Zahl und nicht ihre Richtigkeit (M-01), der zweite ist der
Fund der Geheimnis-Gegenprobe, sobald man sie über das ganze Verzeichnis `docs/`
laufen lässt statt nur über die Dateien dieser Phase (M-02). Elf LOW-Befunde,
zwei davon durch die Runbook-Nachträge aus 15-15 geschlossen, neun als benannte
Punkte weitergereicht.

**In den 80 committeten Dateien dieser Phase steht kein Geheimnis**, geprüft mit
einem anderen Suchmuster als dem der Umsetzung. Der Satz gilt für diese Phase und
nicht für `docs/` insgesamt, und genau diese Unterscheidung ist M-02.

---

## 1. Gate-Protokoll

Der Gesamtlauf ist in einem Zug gegen denselben Baum gefahren, in der
Reihenfolge, in der `.github/workflows/python.yml` ihn fährt. Gelaufen am
21.09.2026 auf der Entwicklungsmaschine (Windows, Python 3.13, uv), `pyright`
mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, damit lokal dieselbe Fassung prüft
wie in CI.

| Stufe | Befehl | Ausgang | Zahl |
|---|---|---|---|
| 1 | `uv run ruff check .` | grün | All checks passed |
| 2 | `uv run ruff format --check .` | grün | 123 Dateien bereits formatiert |
| 3 | `uv run pyright` | grün | 0 errors, 0 warnings, 0 informations |
| 4 | `uv run vulture src tests --min-confidence 80` | grün | keine Ausgabe |
| 5 | `uv run pytest -q` (VOLLE Suite) | grün | **2394 bestanden, 15 übersprungen**, 194,55 s |
| 6a | `uv run ruff check --config pyproject.toml ../scripts` | grün | All checks passed |
| 6b | `uv run ruff format --config pyproject.toml --check ../scripts` | grün | 10 Dateien bereits formatiert |

Die volle Suite und nicht `tests/unit`: die Lehre vom 17.09.2026 ist, dass ein
prozessweites Leck nur im vollen Lauf rot war.

### Die Zahlen gegen den Stand der Phase 14

| Stand | bestanden | übersprungen |
|---|---:|---:|
| 14-12, Abnahme der Phase 14 (19.09.2026) | 2262 | 15 |
| 15-15, nach dem Prüfsummen-Wächter (21.09.2026) | 2394 | 15 |
| **dieser Lauf (21.09.2026, Commit `fb2f1ab`)** | **2394** | **15** |

**132 Fälle mehr als in 14-12, und kein einziger übersprungener mehr.** Die
132 sind die Tests der Phase 15: die Werkzeug-Wächter der Pläne 15-01 bis
15-07 und der Prüfsummen-Wächter aus 15-15 über die sechs gefahrenen
Messfassungen. Die Skipzahl ist seit 13-13 unverändert 15, und alle 15 hängen
an der Maschine (kein Modellartefakt, kein `tesseract`, kein POSIX, keine
POSIX-Shell, kein Korpusgenerator) und keiner an einer Zusage. Ein Grün, das
durch einen neuen Skip entstanden wäre, wäre keines.

### Ein Befund aus dem Gate-Protokoll selbst

Ein Lauf der vollen Suite, der zeitgleich mit den statischen Stufen auf
derselben Maschine lief, meldete **einen** Fehlschlag:
`tests/test_search_endpoint.py::test_with_the_release_on_a_cold_engine_gets_exactly_one_run`,
`assert False is True`. Einzeln nachgefahren ist derselbe Fall grün, und der
Lauf ohne Nebenlast ist es ebenfalls. Der Fall misst ein Single-Flight über
eine Zeitgrenze und ist damit lastempfindlich. Geführt als **L-11**; er steht
hier und nicht im Papierkorb, weil ein Gate, das unter Last kippt, im nächsten
CI-Lauf als echter Fehlschlag erscheinen kann.

### Die Stufen, die hier nicht fahrbar sind

| Stufe | Lage | Ersatznachweis |
|---|---|---|
| PHP-Lint, PHPUnit | in dieser Phase ist unter `php/` keine Zeile geändert worden | `git diff --stat` über die Phase nennt kein `php/`-Ziel; der Baumhash der PHP-Hälfte ist unverändert |
| Shell-Werkzeuge des Laufverzeichnisses | keine POSIX-Shell auf dieser Maschine | vier `skipif` in `test_measurement_scripts.py`, plus der Prüfsummen-Wächter aus 15-15, der die sechs gefahrenen Fassungen byteweise festhält |

---

## 2. Security, ASVS V2, V4, V6, V7, V14

Die zutreffenden Kategorien dieser Phase sind die einer Anfahrt auf eine
gemietete Maschine mit zwei Konten, einem Schlüsselpaar, einer Security Group
und einem öffentlichen Verzeichnis, in das Rohdaten wandern. V3, V5 und V12
treffen nicht zu, und sie stehen hier trotzdem mit einer Zeile, weil eine
weggelassene Kategorie von einer geprüften nicht zu unterscheiden ist: die
Phase fügt keine Route hinzu, prüft keine Eingabe eines Nutzers und fasst
keine Ressourcengrenze des Erzeugnisses an.

### V2, Anmeldedaten: gehalten

Die Anfahrt führt zwei Konten, `admin` der AIO-Instanz und `lasttest` als
Eigentümer des Korpus. Kein Passwort steht in einer committeten Datei, und
keines steht in einer Kommandozeile.

Der Nachweis ist ein Gate und keine Sichtprobe:
`test_the_script_of_this_run_puts_no_password_on_a_command_line` liest **jedes**
Werkzeug des Laufverzeichnisses und prüft es gegen `passwords_on_a_command_line`.
Verboten sind `--password <wert>`, `--password=<wert>` und die Kurzform `-p`
hinter einem Programm, das ein Passwort nimmt; erlaubt ist genau die Form, die
`search_load.py` benutzt: `--password-env` mit dem **Namen** einer
Umgebungsvariablen. Der Grund steht als Bedrohung T-10-03 daneben: ein Argument
steht in der Prozessliste, und ein Protokoll behält es.

Die Passwörter selbst liegen außerhalb des Repositoriums, in einer
Passwortdatei und in der gesicherten `box.env`; beide sind mit dem Abbau der Box
nicht in das Repositorium gewandert (15-14).

### V4, Zugriffskontrolle auf die Maschine: gehalten, mit einem Handgriff

SSH steht auf genau einer Adresse mit **Präfixlänge 32**, und zwar auf der des
Owners. Die Security Group der Anfahrt trug vier Regeln: tcp 22 auf
`<eigene-adresse>/32`, tcp 80, tcp 443 und udp 443 auf das ganze Netz. Die drei
offenen Regeln sind die, die ein AIO mit eigenem Zertifikat braucht; udp 443
stammt aus DI-05-35 (HTTP/3-Ankündigung des Apache).

**Der Handgriff, den der Erstvollzug erzwungen hat:** die eigene öffentliche
Adresse wurde über Nacht neu vergeben, und die Regel zeigte am Morgen auf eine
fremde Adresse. Vollzogen wurde `revoke-security-group-ingress` auf die alte und
`authorize-security-group-ingress` auf die neue Adresse, nach dem Muster von
`cmd_start`. **Die Präfixlänge 32 ist dabei nie aufgeweicht worden**, und die
Box war über HTTPS durchgehend erreichbar. Der Vorgang steht als Nachtrag im
Runbook, Abschnitt der wiederkehrenden Handgriffe.

Geprüft und ohne Befund: in keiner Rohdatei und in keinem Werkzeug steht eine
Regel auf `0.0.0.0/0` für Port 22.

### V6, Schluesselmaterial: gehalten

Das Schlüsselpaar `findling-loadtest` ist in Block 2 neu erzeugt worden, 2048
Bit RSA, Rechte `-rw-------`, und der private Teil hat die Maschine des Owners
nie verlassen. In den committeten Dateien steht die **Kopfzeile** eines privaten
Schlüssels an drei Stellen, und zwar je als Beschreibung einer erwarteten
Dateiform ("die Datei beginnt mit ..."), zweimal im Runbook und einmal in
`03-aufbau.txt`. Die Gegenprobe in Abschnitt 3 hat gezielt nach dem **Rumpf**
gesucht, also nach base64-Blöcken und nach `ssh-rsa`/`ssh-ed25519`-Material:
**null Treffer**. Eine Kopfzeile ohne Rumpf ist ein Formhinweis und kein
Schlüssel.

Nach dem Abbau ist das Paar gelöscht; `describe-key-pairs` meldet
`InvalidKeyPair.NotFound` (15-14). Dass `cmd_destroy` es nicht selbst löscht,
ist Befund **L-07**.

### V7, was in ein oeffentliches Verzeichnis geht: gehalten

`docs/` ist öffentlich lesbar, und diese Phase committet 25 Rohdateien einer
echten Maschine. Die Regel der Pläne lautet: keine Kennung, keine Adresse, kein
Passwortinhalt, Platzhalter statt Wert. Zwei Werte sind ausdrücklich
ausgenommen, weil sie bereits vor dieser Phase committet waren und kein
Geheimnis sind: der öffentliche Name `loadtest.infranode.dev` und der
Korpus-Snapshot `snap-03f1d1d9ad9262704`.

Der Nachweis ist die Gegenprobe in Abschnitt 3 und nicht die Wiederholung des
Gates, das die Umsetzung schon gefahren hat.

### V14, Konfiguration: gehalten

Jede Anmeldung der Werkzeuge kommt aus der Umgebung oder aus einer
Passwortdatei, nie aus einem Argument. Der Abbilddigest kommt als
`ABBILD_DIGEST` aus der Umgebung und hat keinen Vorgabewert, damit kein Lauf
still ein anderes Abbild misst als das genannte (Entscheid 15-06). Dass
`99c-filter-sortierung.sh` die Passwortdatei nicht liest und nur die
Umgebungsvariable kennt, ist Befund **L-04**; es ist ein Bruch der Einheitlichkeit
und **kein** Sicherheitsdefekt, weil die Umgebung genau die erlaubte Form ist.

### V3, V5, V12: treffen nicht zu

Keine Sitzung wird angelegt, keine Eingabe eines Nutzers geprüft, keine
Ressourcengrenze des Erzeugnisses verändert. Die harte Speichergrenze der Box
ist eine Messbedingung und keine Zusage des Erzeugnisses.

---

## 3. Die Geheimnis-Gegenprobe

**Eine Gegenprobe mit dem Muster der Umsetzung ist keine Gegenprobe.** Diese
Regel steht seit dem 02.08.2026 in den Owner-Regeln, und sie hat hier einen
konkreten Anlass: die Pläne 15-09 bis 15-14 haben je ein Gate gefahren, das
**dieselbe** Suche ausführt. Wäre ein Geheimnis in einer Form in die Dateien
geraten, die dieses Muster nicht kennt, hätten alle sechs Gates es sechsmal
übersehen.

**Das Muster der Umsetzung** (aus dem `verify` der Pläne 15-09 bis 15-14),
gesucht wurden Formen von Kennungen:

```
\b(?:i-[0-9a-f]{8,}|vol-[0-9a-f]{8,}|\d{1,3}(?:\.\d{1,3}){3})\b
```

**Das Muster der Gegenprobe**, ein anderes Verfahren: nicht die Form einer
Kennung, sondern acht Familien, die ein Geheimnis an seinem Kontext oder an
einer anderen Form erkennen. Gelaufen über **alle 80 in dieser Phase
committeten Dateien** und nicht nur über die Rohdaten:

| Familie | Was gesucht wurde | Treffer | Urteil |
|---|---|---:|---|
| `pem-privatschluessel` | `-----BEGIN ... PRIVATE KEY-----` | 3 | Formhinweise ohne Rumpf, siehe V6 |
| `ssh-schluesselmaterial` | `ssh-rsa`/`ssh-ed25519`/`ssh-dss` gefolgt von `AAAA...` | 0 | sauber |
| `aws-zugangskennung` | `AKIA`, `ASIA`, `AIDA`, `AROA`, `AGPA`, `ANPA`, `ANVA`, `APKA` mit 12 und mehr Folgezeichen | 0 | sauber |
| `aws-ressourcenkennung-ohne-i-und-vol` | `snap-`, `ami-`, `subnet-`, `sg-`, `eni-`, `acl-`, `rtb-`, `igw-`, `vpc-`, `pcx-`, `nat-` | 2 | beide `ami-0e79e661e73ddfac9`, siehe I-01 |
| `rechnername-der-box` | `ec2-...compute.amazonaws.com`, `ip-<vier Zahlen>`, `*.compute.internal` | 0 | sauber |
| `schluesselwort-mit-wert` | `pass`/`passwort`/`password`/`secret`/`token`/`api_key`/`credential`/`pwd` unmittelbar vor `:` oder `=` und einem Wert | 4 | drei Bezeichner ohne Wert, ein Testliteral, siehe unten |
| `ipv6-adresse` | vier bis acht Gruppen Hexziffern mit Doppelpunkten | 0 | sauber |
| `base64-block-ab-40` | zusammenhängende base64-Zeichen ab Länge 40 | 37 | 36 davon sha256-Summen, eine ein Pfad, siehe unten |

**Das Ergebnis: kein Geheimnis in einer committeten Datei dieser Phase.** Die
vier Treffer, die eine Erklärung brauchen, je einzeln:

1. **Die drei Kopfzeilen privater Schlüssel** stehen in `03-aufbau.txt` und im
   Runbook, je in einem Satz der Form "die Datei beginnt mit ...". Der Rumpf
   fehlt, und zwei unabhängige Familien der Gegenprobe (`ssh-schluesselmaterial`
   und `base64-block-ab-40`) bestätigen das.
2. **`password=secret`** steht in `backend/tests/test_measurement_scripts.py`
   und ist der Beispielsatz, an dem das Gate geprüft wird, das Passwörter auf
   Kommandozeilen **findet**. Ein Gate gegen Passwörter braucht ein
   Beispielpasswort, und dieses ist erfunden.
3. **`password = _password(arguments)` und `token = request_token(...)`** in
   `96d-statusbeobachter.py` sind Bezeichner ohne Wert.
4. **Der eine base64-Treffer, der keine sha256-Summe ist**, ist der Pfad
   `/mnt/findling/ncdata/lasttest/files/loadtest` aus `90-bestand.txt`. Er nennt
   den Kontonamen des Lastkontos und kein Geheimnis; die Schrägstriche
   gehören zum base64-Alphabet und sind der Grund, warum das Muster ihn
   überhaupt aufgreift. Ein Fehlalarm, der stehen bleibt, weil ein enger
   gefasstes Muster weniger findet.

**Die Gegenrichtung, zur Ehrlichkeit:** das Muster der Umsetzung ist zusätzlich
über alle 80 Dateien gefahren worden statt nur über die Rohdaten, die es in
den Plänen sah. Neun Treffer, alle erklärt und keiner ein Geheimnis: sechs
sind mit Punkten gruppierte Zahlen, drei sind die Brückenadresse des
Docker-Netzes und die Bindadresse `0.0.0.0`. Eine öffentliche Adresse der Box
steht in keiner Zeile dieser Phase.

### Der Fund, der erst ausserhalb der Phase auftaucht: Befund M-02

Dieselbe Gegenprobe, ein zweites Mal gefahren, diesmal über **das ganze
Verzeichnis `docs/`** statt nur über die 80 Dateien dieser Phase. Sie findet in
**18 Dateien 58 Werte** der Art, die die Regel dieser Phase verbietet: eine
Instanzkennung, zwei Volumekennungen, eine Security-Group-Kennung und rund zwanzig
öffentliche IPv4-Adressen, darunter die der Box und die des Owners. Die Werte
stehen hier nicht; ein Auditbericht, der sie zitierte, wäre die neunzehnte Datei.

**Keiner dieser Werte stammt aus Phase 15.** Sie stammen aus den Phasen 5 bis 12,
und einer von ihnen liegt sogar im Laufverzeichnis dieser Anfahrt: die Datei
`rohdaten/01-aws-lesende-proben.txt` trägt eine Volumekennung und ist am
18.09.2026 mit Plan 12-03 committet worden, also vor dieser Phase.

**Wie schwer das wiegt.** Alle bezeichneten Ressourcen sind seit dem 11.09.2026
beziehungsweise dem 21.09.2026 abgebaut und gegen die API als abgebaut
zurückgelesen; die Adressen sind dynamisch vergeben und längst an andere
gegangen. Der praktische Schaden ist deshalb gering. Die Regelverletzung ist
trotzdem real, und die Lehre ist die eigentliche Nachricht: **die Geheimnisregel
ist in diesem Projekt nirgends als Gate gefahren, sondern je Plan als Suche über
die Dateien, die der Plan selbst nennt.** Wer eine Datei nicht nennt, prüft sie
nicht. Vorschlag an Phase 16: die acht Familien dieser Gegenprobe als Testfall
über `docs/` fahren, mit einer benannten Ausnahmeliste für die Altbestände, die
nicht mehr redigiert werden.

---

## 4. Der Erstvollzug als Befund

Diese Anfahrt war der erste Vollzug von `docs/runbook-messbox.md` als Kette.
Ein Runbook, das aus Skripten und älteren Berichten zusammengetragen ist, sagt
beim ersten Vollzug die Wahrheit über sich selbst, und diese hier hat an 31
Stellen von ihr abgewichen.

**Die vier falschen erwarteten Ausgaben**, die ein Werkzeug hätten abbrechen
lassen oder es getan haben:

| Stelle | Was das Runbook erwartete | Was die Maschine sagte | Folge |
|---|---|---|---|
| Block 12, cgroup | die harte Grenze in **beiden** Feldern | `memory.max` 2147483648 bei `memory.swap.max` **0** | `92b-wechsel.sh` brach mit 39 ab, auf einer korrekten Maschine |
| Block 9, Sicherung | 91 MB | die Zahl misst den lebenden Altstand und nicht die Sicherung | nur Verwirrung |
| Block 7, Inhalt des Datenträgers | `docker` und `ncdata` als vollständiger Inhalt | dazu der containerd-Store | Abbilder landeten zunächst auf der Systemplatte |
| Block 9, Arbeitsbaum | ein Arbeitsbaum liegt vor | keiner | Checkout auf der Box von Hand |

**Der Widerspruch im Tor.** Abschnitt 5 des Runbooks will vor der Messung
52.111 indexierte Dokumente sehen. Block 13b, der Abbildwechsel, leert das
Datenvolume des Backends planmäßig mit `unregister --rm-data`. Beides
zusammen kann nicht stehen: nach dem Wechsel ist der Beleg des Tors
strukturell nicht mehr ablesbar. Vorgelegt wurde der Korpus selbst (52.114
Dokumente, 20G), und der Owner hat am 20.09.2026 entschieden: **"Weiter, Korpus
als Beleg."** Geführt als **L-02**, geschlossen: 15-15 hat dem Abschnitt zwei
Fassungen gegeben, und welche gilt, entscheidet der Abbildwechsel.

**Schließt der Nachtrag aus 15-15 diese Stellen?** Für die vier falschen
Erwartungen und für das Tor: ja, und zwar in der Form, die 15-15 gewählt hat,
nämlich als Richtigstellung **neben** der alten Erwartung und nicht an ihrer
Stelle. Das ist die richtige Form, denn an der ersten dieser Erwartungen ist ein
Werkzeug gescheitert, und eine ersetzte Erwartung ließe nicht mehr erkennen,
woran. Nicht geschlossen sind die sechs Werkzeugbefunde **L-03** bis **L-08**:
sie stehen benannt im Bericht und im Runbook, aber kein Werkzeug ist geändert
worden, und **kein Fix dieser Anfahrt ist in seiner Wirkung nachgemessen**.

**Die drei Änderungen während der bezahlten Zeit.** Das Runbook verbietet in
Abschnitt 7.1, während der Anfahrt ein Werkzeug zu ändern. Dreimal ist es
geschehen (`d6fb185`, `ff8e054`, `6f42c69`), je mit ausdrücklichem Owner-Wort
und je, weil ein Werkzeug auf einem **korrekten** Zustand abbrach. Die Zahlen
daneben stammen je aus dem Lauf nach dem Fix. Der Prüfsummen-Wächter aus 15-15
friert den Stand **nach** der Anfahrt ein, auch für die zwei geänderten
Fassungen, und die Prüfsummen der Stände davor stehen in der SUMMARY des
Plans 15-15. Das ist eine benannte Asymmetrie und geführt als **L-08**: wer die
Zahlen dieser Anfahrt nachrechnen will, braucht für zwei Werkzeuge die
Vorgängerfassung aus der Historie und nicht die eingefrorene.

---

## 5. Performance-Durchgang

Diese Phase hat nichts gebaut, was langsamer oder schneller sein könnte. Der
Durchgang prüft deshalb, ob die gemessenen Zahlen tragen, was sie tragen
sollen.

### 5.1 Die Laststufen: die Verdikte halten der Gegenrechnung stand

Alle vier in v1.1 regressiven Stufen unterschreiten ihre v1.1-Zahl, bei
gehaltener oder besserer Trefferdichte. Die Gegenrechnung ist unabhängig vom
Lastwerkzeug geführt worden, nämlich auf `cURL error 28` im Protokoll der
Nextcloud: **null** im Lastfenster. Damit sind die gemeldeten Ausfälle echte
Leertreffer und keine verschluckten Zeitüberschreitungen. Genau das war in v1.1
anders, und genau deshalb ist die Gegenrechnung hier gefahren worden.

Die Reserve auf Stufe 8 wächst von 374,5 auf 508,0 ms. Die Erwartung E10 hatte
eine Verschlechterung erwartet und ist deshalb **verfehlt**; der Bericht lässt
das Wort stehen, obwohl die Abweichung in die günstige Richtung geht. Das ist
richtig so.

### 5.2 Befund M-01: die 1,5-s-Decke, und was die Rohdateien nicht ausweisen

| Ausprägung | Schalter | Cache | erste Suche | Abstand zur Decke | Code | Treffer |
|---|---|---|---:|---:|---|---:|
| 1 | 120 s | kalt | 1.996 ms | minus 496 ms | 200 | 26 |
| 2 | 120 s | warm | 1.418 ms | plus 82 ms | 200 | 26 |
| 3 | 0 | kalt | 2.051 ms | minus 551 ms | 200 | 0 (transient) |
| 4 | 0 | warm | 1.613 ms | minus 113 ms | 200 | 26 |

**Drei von vier Ausprägungen liegen über 1,5 s, und eine davon hat mit der
Entladung nichts zu tun** (Ausprägung 4, Schalter 0, warmer Cache). Das ist die
wichtigere Hälfte des Befundes: die Decke reißt nicht wegen der Entladung,
sondern auf dieser Maschine überhaupt.

**Was die Rohdateien ausweisen und was nicht.** Gemessen ist je die Dauer der
ganzen Anfrage auf der Nutzerroute. Die Methodik-Korrektur in
`docs/performance.md` hält seit dem 10.09.2026 fest, dass die Decke von
1.501 ms dem **inneren** Containeraufruf gilt und eine Gesamtdauer über 1,5 s
deshalb keinen Abbruch beweist. Die vier Rohdateien weisen die innere Dauer
nicht aus. Was sie ausweisen: `erste-suche-code=200` in allen vier Fällen und
26 Treffer in drei von vieren. **Ein Abbruch ist in keiner der vier
Ausprägungen eingetreten.**

Der Bericht führt E12 trotzdem als verfehlt, und das ist richtig, weil E12 den
Wortlaut "die erste Suche nach einer Entladung bleibt unter 1,5 s" trägt und
nicht "der innere Aufruf". Was offen bleibt, ist die Frage, die MEM-03 wirklich
stellt: ob der innere Aufruf seine Decke hält. Sie ist auf dieser Anfahrt nicht
beantwortet worden und braucht ein Messwerkzeug, das die innere Dauer mit
ausweist. Weitergereicht an Phase 16.

### 5.3 Die Gegenprobe zu einer Annahme: die Wirkung der Top-up-Route

Die Anfahrt hätte eine bequeme Zahl liefern können: 7 h 17 min kürzer, der
Leerlaufanteil von 22,0 auf 2,6 Prozent gefallen. Der Bericht weist die Wirkung
trotzdem als **nicht entschieden** aus, weil die Instanz aus einem Snapshot neu
aufgebaut und das Abbild gewechselt wurde und damit zwei Erklärungen möglich
bleiben. Geprüft: der Satz steht im Commit `190d5c7` vom 19.09.2026 in
`skripte/00-ablauf.md`, also vor der ersten Box-Minute, und ist nach dem Lauf
nicht umgeschrieben worden. **Die Annahme hält der Gegenprobe stand**, und die
5,35 h weniger Leerlauf, die rund drei Viertel des Zeitgewinns erklären, sind
die einzige Zuordnung, die vorgenommen wird.

---

## 6. Die fuenf Erfolgskriterien der Phase, je mit Beleg

Die Kriterien stehen in `.planning/ROADMAP.md`, Phase 15. Ein nicht erfülltes
Kriterium wird hier nicht umgedeutet.

| Nr. | Erfolgskriterium (Kurzform) | Beleg | Urteil |
|---|---|---|---|
| 1 | Deckel vor dem Start neu gerechnet und vom Owner freigegeben | `15-08-SUMMARY.md`: "Freigegeben, 46 h / 5,40 USD" am 20.09.2026, Rechenblatt mit zehn Posten im Runbook; verbraucht 25,75 h und 2,9831 USD (`rohdaten/93-kosten-und-verbleib.txt`) | **erfüllt** |
| 2 | DI-10-04-Wirkungsbeleg als Volllauf gegen den Korpus-Snapshot, mit protokolliertem Cron-Intervall und Vergleichbarkeitsbedingungen | Volllauf 19 h 20 min (`rohdaten/96b-waechter.txt`, `96-volllauf.csv`), `cron-intervall-ist 300` mit Quelle (`97-cron-vorpruefung-vorher.txt`), sechs Vergleichbarkeitsgrößen im Bericht Abschnitt 2 | **erfüllt**, mit zwei benannten Vorbehalten: die Zeilenstände des Tors waren nicht mehr ablesbar (Owner-Entscheid, L-02), und der Wirkungszweig des Cron-Checks lief nicht live (L-01). Die WIRKUNG der Route ist im Bericht als nicht entschieden ausgewiesen |
| 3 | Die vier regressiven Laststufen untersucht und je Stufe entschieden | `rohdaten/97-nebenlaeufigkeit.txt`, vier Verdikte "behoben", wortgleich im Bericht Abschnitt 5, mit unabhängiger Gegenrechnung aus dem Nextcloud-Protokoll | **erfüllt** |
| 4 | Die Sprachfall-Messung läuft **ohne** den 52.111er-Fremdbestand und liefert Zahlen über der bisherigen Deckelung | `rohdaten/05-sprachfaelle.txt`: gefahren wurde **mit** dem Fremdbestand, denn er ist der Korpus dieser Box; fünf der zehn Fälle heißen deshalb "nicht messbar". Die zweite Hälfte hält: die Bestandssonde misst 33.226 bis 51.965 statt des alten Deckels von 26 | **nicht erfüllt** in seiner ersten Hälfte. Die Messung ohne Fremdbestand existiert nur als CI-Lauf 35471225104 auf amd64 gegen eine frische Instanz, und der Bericht nennt ihn selbst "die Haelfte der Aussage, die diese Box nicht machen kann" |
| 5 | Wiederaufwärm-Kosten gemessen und ausgewiesen (warm/kalt, mit/ohne Seitencache, A/B über den Schalter); die Box danach abgebaut | `rohdaten/95b-wiederaufwaermen-1..4.txt` und `95b-gegenueberstellung.txt`, vier Ausprägungen über beide Schalterstellungen; Abbau in `07-snapshot-und-abbau.txt`, je Ressourcenart gegen die API zurückgelesen | **erfüllt** |

**Zu Kriterium 4, ohne Beschönigung.** Es ist so, wie es dasteht, auf dieser
Box nicht erfüllbar gewesen: der Korpus-Snapshot **ist** der Fremdbestand, und
eine Messung ohne ihn hätte eine zweite Instanz oder einen Teilkorpus
gebraucht. Das ist kein Ausführungsfehler der Anfahrt, sondern ein Kriterium,
das sich mit der gewählten Messanlage nicht verträgt. Es wird dem Owner als
nicht erfüllt vorgelegt, mit genau diesem Satz und ohne Vorschlag, wie man es
anders lesen könnte. Geführt als **L-09**.

---

## 7. Befundliste

| ID | Schwere | Befund | Stand |
|---|---|---|---|
| M-01 | MEDIUM | Die 1,5-s-Decke der ersten Suche reißt auf der Zielhardware in drei von vier Ausprägungen, auch ohne Entladung; die Rohdateien weisen nur die Gesamtdauer aus und nicht den inneren Aufruf, dem die Decke gilt | weitergereicht an Phase 16; ein Abbruch ist in keiner Ausprägung eingetreten (`code=200`) |
| M-02 | MEDIUM | Die Geheimnis-Gegenprobe über das ganze Verzeichnis `docs/` findet in 18 Dateien 58 Werte der Art, die diese Phase verbietet: eine Instanz-, zwei Volume- und eine Security-Group-Kennung sowie rund zwanzig öffentliche IPv4-Adressen. Keiner stammt aus Phase 15; die Regel ist nirgends als Gate gefahren | weitergereicht an Phase 16; alle bezeichneten Ressourcen sind abgebaut, der praktische Schaden ist gering, die Lücke im Verfahren nicht |
| L-01 | LOW | Der Wirkungszweig der Cron-Vorprüfung lief während des Volllaufs nie; seine Zahlen sind nachträglich aus der 120-s-Statusreihe gerechnet | **behoben** im Ablauf und im Runbook (15-15): der Start des Zweiges ist eine eigene Zeile; nicht nachgemessen |
| L-02 | LOW | Das Abbruchtor (Abschnitt 5) und der Abbildwechsel (Block 13b) widersprechen sich: nach `--rm-data` ist der Torbeleg strukturell nicht mehr ablesbar | **behoben** (15-15): zwei Fassungen des Tors, die Auswahl entscheidet der Abbildwechsel; Owner-Entscheid vom 20.09.2026 im Bericht |
| L-03 | LOW | Die Phase-B-Pipeline von `92b-wechsel.sh` verschluckt Fehler des `occ`-Aufrufs: Lauf 1 endete mit Rückgabewert 0, ohne dass die Registrierung stattgefunden hatte | weitergereicht, unverändert |
| L-04 | LOW | `99c-filter-sortierung.sh` liest das Passwort nicht aus der Passwortdatei, sondern erwartet es in der Umgebung | weitergereicht; kein Sicherheitsdefekt, die Umgebung ist die erlaubte Form (V14) |
| L-05 | LOW | `94b-grundlast-rueckkehr.sh` und `95b-wiederaufwaermen.sh` führen `admin` als Vorgabebenutzer, der Korpus gehört aber `lasttest`; die Suche liefert dann null Treffer | weitergereicht; Behelf auf der Box war eine kurzzeitige Gruppenmitgliedschaft, danach entfernt |
| L-06 | LOW | `94b-grundlast-rueckkehr.sh` ruft `sudo "$SAMPLER"` direkt, die Datei steht mit `100644` im Index: `command not found`, Abbruch 32 | weitergereicht; Behelf war `chmod +x` auf der Box |
| L-07 | LOW | `aws_box.sh cmd_destroy` löscht das Schlüsselpaar nicht mit | weitergereicht; in 15-14 von Hand geschlossen und gegen die API zurückgelesen |
| L-08 | LOW | Drei Werkzeuge sind während der bezahlten Zeit geändert worden; der Prüfsummen-Wächter friert den Stand **nach** der Anfahrt ein | weitergereicht als benannte Asymmetrie; die Prüfsummen der Stände davor stehen in `15-15-SUMMARY.md` |
| L-09 | LOW | Erfolgskriterium 4 der ROADMAP ist in seiner ersten Hälfte nicht erfüllt: die Sprachfall-Messung lief mit dem Fremdbestand, weil er der Korpus dieser Box ist | dem Owner am Checkpoint 15-16 als nicht erfüllt vorgelegt |
| L-10 | LOW | Das in öffentlichen Artefakten gesperrte Wort steht in einer Rohdatei DIESER Phase (`rohdaten/03-aufbau.txt`, Zeile 145, deutscher Satz) und darüber hinaus **116 mal in 17 Dateien** unter `docs/`, davon rund 50 in deutschen Formen; die Regel ist nirgends durch ein Gate gedeckt | weitergereicht an Phase 16; die Rohdatei bleibt unangetastet (eine gefahrene Rohdatei wird nach der Anfahrt nicht mehr redigiert), aufgenommen in `deferred-items.md` |
| L-11 | LOW | `test_with_the_release_on_a_cold_engine_gets_exactly_one_run` ist zeitempfindlich und fiel einmal unter Nebenlast aus | weitergereicht; einzeln und ohne Nebenlast grün |

Kein CRITICAL, kein HIGH.

**I-01, kein Befund, zur Vollständigkeit:** die Abbildkennung
`ami-0e79e661e73ddfac9` steht in `03-aufbau.txt` und im Runbook. Sie benennt ein
öffentliches Ubuntu-Abbild des Anbieters, gilt für jedes Konto in derselben
Region und ist kein Geheimnis. Sie bleibt stehen, weil ein Runbook ohne
Abbildkennung nicht nachvollziehbar ist.

---

## 8. Was dieser Bericht nicht sagt

Er sagt nichts darüber, ob die Werkzeugfixe dieser Anfahrt auf einer Box tun,
was sie sollen. Drei Werkzeuge sind während der bezahlten Zeit geändert und
gegen boxlose Tests grün; die Wirkung misst erst die nächste Anfahrt. Er sagt
auch nichts über die sechs fehlgeschlagenen und 44 übersprungenen Dateien des
Endstandes: sie sind gezählt und nicht untersucht.

Er sagt nichts über das Verhalten an einer laufenden Instanz, denn es gibt
keine mehr: die Box ist am 21.09.2026 abgebaut worden. Was bleibt, sind der
Korpus-Snapshot, die committeten Rohdaten und dieser Bericht.

Die Freigabe der Phase liegt beim Owner und nicht in diesem Bericht. Sie ist am
Tag dieses Berichts noch nicht erteilt; der Checkpoint ist Task 3 des Plans
15-16.

Er nennt keine Adresse, keine Instanz- oder Volumekennung und keinen
Passwortinhalt, auch nicht die aus Befund M-02: ein Bericht, der sie zitierte,
wäre die neunzehnte Datei, die sie trägt. `docs/` ist öffentlich, und dieser
Bericht ist vor dem Commit mit demselben Verfahren durchgesehen worden, das in
Abschnitt 3 steht.
