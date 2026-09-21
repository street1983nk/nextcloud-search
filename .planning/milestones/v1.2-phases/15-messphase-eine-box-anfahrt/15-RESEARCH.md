# Phase 15: Messphase, eine Box-Anfahrt , Research

**Recherchiert:** 2026-09-19
**Domain:** Bezahlte AWS-Messanfahrt (m7g.large, eu-central-1c) mit Erstvollzug des Wiederaufbau-Runbooks; Messprotokollfuehrung, Kostendeckel, Vergleichbarkeitsbedingungen
**Confidence:** HIGH fuer den Bestand (alles an Dateien und Zeilen dieses Repositoriums gelesen), HIGH fuer die Luecken (an den Dateien belegt, nicht vermutet), MEDIUM fuer die Preissaetze (gepinnt seit 04.09., nur indirekt gegengeprueft), MEDIUM fuer die neu geschaetzten Zeitposten

---

## Summary

Diese Phase baut kein Erzeugnis, sie **vollzieht ein Verfahren**. Das Verfahren steht
vollstaendig geschrieben: `docs/runbook-messbox.md` (1102 Zeilen, neun Abschnitte, 24
Kommandobloecke) beschreibt Anfahrt, Messreihenfolge, Vergleichbarkeitsbedingungen, Abbau
und Kostenfuehrung, und `docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md`
beschreibt fuenf der Messschritte mit vorher aufgeschriebenen Erwartungen E1 bis E7. Die
Planung dieser Phase ist deshalb ueberwiegend **Uebersetzungsarbeit**: aus dem Runbook
werden Plaene mit Abnahmekriterien, und die wenigen Stellen, an denen das Runbook noch
kein Werkzeug hat, werden **vor** der ersten bezahlten Minute gebaut.

Genau diese Stellen sind der eigentliche Befund dieser Recherche. Es sind fuenf, alle an
Dateien belegt und keine davon in einem Plan bisher benannt: (1) das Laufverzeichnis
`2026-09-v12-messung/skripte/` enthaelt **drei** Skripte, die Messreihenfolge des Runbooks
verlangt aber neun Bloecke, also muessen sechs Werkzeuge aus dem v1.1-Verzeichnis kopiert
werden (Regel C.3: kopieren, nie editieren). (2) Fuer den Messschritt 8 (Wiederaufwaerm-
Kosten, vier Auspraegungen, Rueckgabewerte 29/30/31) gibt es **ueberhaupt kein Skript**;
`95b-kaltstart-reproduktion` ist der Name einer Rohdatei von Hand, kein Werkzeug. (3) Das
Runbook hat **keinen Block fuer den Abbildwechsel**, obwohl der Wirkungsbeleg zwingend den
v1.2-Stand mit der Top-up-Route braucht und Abschnitt 6 einen gleichen Baumhash als
Vergleichbarkeitsbedingung fordert. (4) Das Leeren des Seitencaches ist in 7.2 als
Bedingung genannt, aber **kein Befehl steht dafuer im Runbook**. (5) Der Deckel des
Runbooks (42 h / 4,90 USD) rechnet zwei Posten nicht mit, die aus den Phasen 13 und 14
dazugekommen sind.

Der Kostendeckel ist der einzige harte Owner-Checkpoint und er blockiert alles: ohne
freigegebene Zahl mit Datum startet die Anfahrt nicht (Runbook Abschnitt 3, Zeile 9).
Diese Recherche rechnet ihn mit zwei Nachtragsposten neu auf **44 Stunden und 5,10 USD
netto**, Untergrenze unveraendert 31 h / 3,59 USD, und legt die Rechnung offen, damit der
Owner sie pruefen statt glauben kann.

**Primaere Empfehlung:** Die Phase in drei Wellen schneiden. Welle A ohne Box (Werkzeuge
komplettieren, Ablaufdatei fortschreiben, Deckel rechnen), Welle B ist **ein einziger
Owner-Checkpoint** (Deckelfreigabe mit Datum), Welle C ist die Anfahrt selbst, gefuehrt
als begleitete Sitzung entlang des Runbooks, mit dem Abbau als letztem Beweis. Kein Plan
der Welle C darf ein Werkzeug aendern.

---

## User Constraints (aus ROADMAP, REQUIREMENTS und den Entscheiden der Phase 12)

**Es gibt kein `15-CONTEXT.md`.** Das Verzeichnis
`.planning/phases/15-messphase-eine-box-anfahrt/` ist leer (geprueft 2026-09-19). Die
bindenden Vorgaben stammen deshalb aus drei Quellen, die alle bereits entschieden sind und
wie gesperrte Entscheide zu behandeln sind.

### Gesperrte Entscheide (Phase 12, `12-CONTEXT.md:33-79`)

| Kennung | Entscheid | Folge fuer Phase 15 |
|---|---|---|
| D-04 | Der Wirkungsbeleg laeuft gegen den **Vollkorpus** (52.111 Dokumente), kein Teilkorpus-Werkzeug | Der Volllauf ist mit 26 h 37 min Planwert zu decken, nicht zu kuerzen |
| D-05 | Das Deckel-Rechenblatt wird **vor jeder Anfahrt neu gerechnet**, aus zuletzt gemessenen Posten | Erster Plan der Phase, vor jeder Kommandozeile |
| D-06 | Zielinstanz bleibt **m7g.large** (ARM, eu-central-1c) | Kein Instanztypwechsel, auch nicht zum Sparen |
| D-07 | Cron-Intervall wird auf 5 Minuten festgenagelt **und** protokolliert | Pflichtzeile `cron-intervall-ist`, Abbruch 25/26 |
| D-08 | Durchsetzung **fail-closed im Skript**, nicht in einer Checkliste | `97-cron-vorpruefung.sh` faehrt, seine Rueckgabewerte gelten |
| D-09 | Hauptpfad ist der **Wiederaufbau aus `snap-03f1d1d9ad9262704`** | Neuaufbau von null ist nicht ausgearbeitet und keine Rueckfallebene |
| D-10 | Der Erstvollzug **validiert das Runbook woertlich**; Abweichungen bleiben als eigene Zeile stehen | Jeder Block mit der Marke "in Phase 15 erstmals vollzogen" wird nachgetragen, nicht ueberschrieben |
| D-11 | Abbau und Kostenfuehrung sind **Pflichtteile** | Der Abbau ist Erfolgskriterium 5, nicht Aufraeumarbeit |

### Aus der ROADMAP (`.planning/ROADMAP.md:207-220`)

Fuenf Erfolgskriterien, woertlich zu erfuellen; sie stehen unten in der Tabelle
"Erfolgskriterien und ihre Belegartefakte" mit den Rohdateien, die sie belegen.

### Aus dem Runbook, bindend und nicht verhandelbar

- **Waehrend der bezahlten Anfahrt wird kein Werkzeug mehr geaendert**
  (`docs/runbook-messbox.md:772-775`). Ein Skript, das waehrend seines Laufs nachgebessert
  wird, macht jede Zahl daneben unbelegt.
- **Die Messreihenfolge ist bindend** (`:724-741`), ebenso die Reihenfolge der vier
  A/B-Auspraegungen (`:781-790`): jede Messung waermt den Seitencache, eine einmal
  gewaermte Kaltmessung ist ohne erneutes Leeren nicht wiederholbar.
- **Die Geheimnisregel** (`:8-15`): keine IP-Adressen, keine lebenden Instanz- oder
  Volumekennungen, keine Passwortinhalte, keine Kontokennung in einer committeten Datei.
  Ausgenommen ist allein `snap-03f1d1d9ad9262704`.
- **Die Zustandspruefung ist ein Abbruchpfad** (`:562-594`): 52.111 / 37 / 0 / 3.9Gi / 2 /
  aarch64. Weicht eine Zahl ab, endet die Anfahrt und der Owner entscheidet neu.

### Ausdruecklich ausserhalb dieser Phase

- Teilkorpus-Werkzeug (D-04 abgelehnt, `12-CONTEXT.md:113-116`).
- Neuaufbau-von-null-Runbook (D-09, nur Verweis).
- Werkzeugkorrekturen jeder Art waehrend der Anfahrt; sie gehoeren in die Zeit nach dem
  Abbau.
- Die Sprachbausteine aus dem BACKLOG: eine Schemaaenderung vor der Messung zerstoert den
  v1.1-Vergleich (`.planning/BACKLOG.md:168-170`).

---

## Project Constraints (from CLAUDE.md)

| Direktive | Wirkung in dieser Phase |
|---|---|
| Projektkommunikation Deutsch, **keine Em-Dashes** (U+2014, U+2013) | Gilt fuer Bericht, Plaene, Rohdaten-Kopfzeilen; ein Gate zaehlt sie in Messskripten (`test_the_measurement_script_carries_no_dash`) |
| Echte Umlaute nur in deutscher Prosa, **nie in Code, Schluesseln, Ueberschriften, die geprueft werden** | Die Abschnittsueberschriften des Runbooks und der Ablaufdateien stehen bewusst ohne Umlaute; Rohdaten der Box sind ASCII, weil das Gebietsschema der Box niemand garantiert |
| Keine Emojis | Gilt auch fuer Rohdaten und Berichte |
| Python-Qualitaetsgates (ruff-Vollregelsatz, pyright basic, vulture), **lokal gruen vor Commit** | Jedes neue Python-Messwerkzeug (z.B. die Auswertung der Wiederaufwaerm-Messung) faellt darunter; `python.yml` laeuft auf `scripts/**` an |
| Nach jeder Phase Security-, Bug- und Performance-Audit | Muster: `docs/audits/2026-09-phase-14/README.md` |
| Kurze Produkttexte, hoechstens eine Zahl, Details nur als Verweis | Betrifft die Nachfuehrung der Messzahl in Phase 16, nicht diese Phase; hier nur der Merker: eine Messzahl steht an **drei** Stellen (README.en.md und beide `info.xml`) und ein Gate haelt sie deckungsgleich |
| Repo ist **oeffentlich** | Verschaerft die Geheimnisregel des Runbooks: alles, was hier committet wird, ist veroeffentlicht |
| GSD-Workflow: keine direkten Repo-Aenderungen ausserhalb eines GSD-Befehls | Auch die Rohdaten der Box wandern ueber Plaene ins Repositorium |

---

## Phase Requirements

| ID | Beschreibung | Was die Recherche dazu beitraegt |
|---|---|---|
| **MESS-05** | EINE Box-Anfahrt liefert DI-10-04-Wirkungsbeleg, Untersuchung der vier regressiven Laststufen, Sprachfall-Messung ohne Fremdbestand, Wiederaufwaerm-Kosten der Entladung; Deckel vorher neu gerechnet und freigegeben (`.planning/REQUIREMENTS.md:28`) | Abschnitt "Inventar der offenen Messauftraege" (jeder Auftrag mit Datei-Anker), Abschnitt "Deckel-Rechenblatt, neu gerechnet" |
| **MEM-02** (mitgereist, offen) | Nach Ablauf der TTL sind beide Speicherhalter frei, belegt an der Messgroesse `Rueckkehr zur Grundlast nach einem Indexlauf` (`.planning/REQUIREMENTS.md`, ROADMAP Phase 14 SC 3; ausdruecklich offengelassen in `14-12-SUMMARY.md`) | Eigener Messblock, heute in keiner Zeitrechnung enthalten; Definition der Messgroesse in `docs/performance.md:3609-3660` |
| **Auflage 1 aus 14-12** | Marge der ersten Suche nach einer Entladung ist duenn (1,37 bis 1,44 s gegen 1,5 s auf der Entwicklungsmaschine) | Gehoert in den A/B-Schritt 7.2, Auspraegung 1 und 2; die Box ist langsamer als die Entwicklungsmaschine |
| **Auflage 2 aus 14-12** | Wiederaufwaerm-Kosten messen | Messschritt 8, vier Auspraegungen; **Werkzeug fehlt** |
| **Auflage 3 aus 14-12** | Vorschlagswert 900 s belegen oder korrigieren | Offene Frage, siehe "Open Questions" Nr. 2 |

---

## Architectural Responsibility Map

Diese Phase hat keine Softwarearchitektur, sondern eine **Betriebsarchitektur**. Die
Zuordnung entscheidet, welche Aufgabe ueberhaupt autonom ausfuehrbar ist.

| Faehigkeit | Primaere Ebene | Sekundaere Ebene | Begruendung |
|---|---|---|---|
| Deckelfreigabe mit Datum | **Owner** | , | Runbook 3.9 und 2.6: eine Anfahrt ohne Deckel ist eine offene Rechnung |
| AWS-Ressourcen erzeugen, anhalten, abbauen | **Entwicklungsmaschine** ueber `scripts/ops/aws_box.sh` | AWS-API | Anmeldung liegt als Datei ausserhalb des Arbeitsbaums; `aws_box.sh` liest sie ausschliesslich aus der Umgebung |
| A-Record `loadtest.infranode.dev` | **Owner** (Zonenverwalter) | Rueckfall `/etc/hosts`-Pin oder `curl --resolve` auf der Box | Kein API-Zugang im Repositorium; Runbook Block 10 |
| Betriebssystem der Box (grub `mem=4G`, fstab, Docker-`data-root`) | **SSH auf die Box** | , | Runbook Bloecke 5 bis 9, keiner davon ist ein AWS-Aufruf |
| Nextcloud-Ebene (Bewaffnung, Registrierung, `occ`) | **`docker exec` auf der Box** | , | Runbook Bloecke 11 bis 13 |
| Containerinterne Messgroessen (Bestandssonde, Entladezaehler, `one_load`) | **In-Container-Python ueber `docker cp` plus `docker exec`** | , | `73-bestand-sonde.py` misst ungedeckelt im Prozess, nicht ueber eine Route |
| Lasterzeugung | **Box, gegen die OCS-Route** ueber `scripts/ops/search_load.py` | , | Gemessen wird der Weg des Nutzers, nicht der Containeraufruf |
| Rohdaten, Bericht, Nachtraege ins Runbook | **Repositorium** (`docs/measurements/2026-09-v12-messung/`) | Git | Was nicht committet ist, ist nach dem Abbau nicht mehr erhebbar |
| Abbildherstellung (v1.2-Stand auf die Box) | **ghcr.io plus Registrierung auf der Box** | lokale Registry der Box aus dem Snapshot | Siehe Pitfall 1 dieser Recherche: hier fehlt ein Runbook-Block |

---

## Inventar der offenen Messauftraege

Jeder Auftrag mit Fundstelle, damit der Planer nicht suchen muss.

### 1. DI-10-04, der Wirkungsbeleg (Erfolgskriterium 2)

| Frage | Antwort | Fundstelle |
|---|---|---|
| Was ist der Befund? | Der v1.1-Volllauf brauchte **26 h 37 min** gegen 18 h 56 min in v1.0, plus 40,6 Prozent bei 0,29 Prozent Mehrbestand. Zwei Kandidaten (Kopplung der Spuren, Zulauf-Luecken), die Daten entscheiden nicht zwischen ihnen | `.planning/milestones/v1.1-phases/10-.../deferred-items.md:135-165` |
| Was ist seither passiert? | Die Ursache ist als Cron-Wirkung **geklaert** (5,85 h von 26,6 h ohne Arbeitsvorrat, 194 von 812 Lesungen, Baseline 0,10 h) und durch die **Top-up-Route behoben** (`POST /queues/documents/topup`, Budget 20 s, Scheiben-Lock gegen den Cron). **Der Beleg der Wirkung braucht einen neuen Volllauf und steht aus** | `docs/performance.md:158` |
| Was ist zu tun? | Ein Volllauf gegen den Vollkorpus mit dem v1.2-Abbild, mit protokolliertem Cron-Intervall und allen sechs Vergleichbarkeitsgroessen | Runbook Schritt 4, `docs/runbook-messbox.md:736` |
| Womit? | Muster `96-volllauf.sh` mit dem Beobachter `96b-waechter.sh`, dazu `96c-lesen.py`, `96d-statusbeobachter.py` | `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/` |
| Woran bricht es ab? | Kein eigener Rueckgabewert. Der Abbruch liegt **vor** ihm (Nullstandsbeleg, Schritt 1) und **neben** ihm (Cron-Wirkungszweig, Rueckgabewerte 27 und 28) | Runbook 7.1 |
| Vergleichszahl | 26 h 37 min ist der **Planwert**, nicht die Erwartung. Der Planwert nimmt keine Verbesserung vorweg (genau dieser Fehler hat den v1.1-Deckel gerissen) | `docs/runbook-messbox.md:125-129` |

### 2. Die vier regressiven Laststufen (Erfolgskriterium 3)

Die Zahlen, gegen die entschieden wird (`docs/audits/2026-09-phase-11/README.md:509-545`):

| Nebenlaeufigkeit | p95 v1.0 (06-11) | p95 v1.1 | Differenz | Budget 2.500 ms |
|---:|---:|---:|---:|---|
| 1 | 481,6 ms | 464,3 ms | minus 3,6 % | gehalten |
| 4 | 1.009,4 ms | 1.068,0 ms | **plus 5,8 %** | gehalten |
| 8 | 1.915,0 ms | 2.125,5 ms | **plus 11,0 %** | gehalten, Reserve faellt von 585,0 auf 374,5 ms |
| 12 | 3.045,4 ms | 3.453,4 ms | **plus 13,4 %** | gerissen (auch schon in v1.0) |
| 16 | 3.782,7 ms | 4.446,2 ms | **plus 17,5 %** | gerissen (auch schon in v1.0) |

Der Beschluss von Phase 11: hingenommen fuer v1.1.0, **untersucht in der v1.2-Messplanung**,
"in derselben Anfahrt wie DI-10-04, und mit dem korrigierten Zaehler aus Plan 11-02, damit
die neue Reihe nicht wieder Abbrueche als Erfolge zaehlt"
(`docs/audits/2026-09-phase-11/README.md:541-545`).

Erfolgskriterium 3 verlangt je Stufe ein Verdikt: **behoben, erklaert oder bewusst
hingenommen**. Drei Randbedingungen, die das Verdikt tragen:

- Die neue Reihe laeuft gegen einen **anderen Vektorbestand** und ein **anderes Abbild**
  als v1.1. Wo Vergleichbarkeit nicht herstellbar ist, wird die Zahl als Erstmessung
  gefuehrt und nicht als Vergleichszeile (`PITFALLS.md` Pitfall 16).
- Jede Stufe wird gegen eine **unabhaengige Quelle** aufgerechnet, das Nextcloud-Protokoll
  im selben Zeitfenster; der Fingerabdruck ist **Treffer je Anfrage** (5,40 auf den Stufen
  1 und 4, 4,16 auf Stufe 16 in v1.1). Eine Stufe mit fallender Trefferdichte ist
  verdaechtig, auch bei `failures: 0` (Pitfall 18).
- `scripts/ops/search_load.py` wird **nicht angefasst** (`docs/runbook-messbox.md:684-687`).

Werkzeug: Muster `97-nebenlaeufigkeit.sh` (`STUFEN="1 4 8 12 16"`, `RUNDEN`, Passwort ueber
`--password-env`, nie auf der Kommandozeile) und `95-spitze.sh` fuer die einmaligen
Erstkosten. Wichtig fuer die Reihenfolge: `97-nebenlaeufigkeit.sh` **laedt das Modell
absichtlich vor der Reihe** (Zeilen 34-37 des Skriptkopfes), es waermt den Container also
auf und darf vor keiner Kaltmessung des Schrittes 8 laufen.

### 3. Sprachfaelle, DI-10-02 und DI-11-01 (Erfolgskriterium 4)

| Frage | Antwort | Fundstelle |
|---|---|---|
| Was war kaputt? | Die Vorpruefung fragte die OCS-Route und bekam fuer **jeden** Begriff exakt **26** Treffer, bei Tiefe 64, 200 und 2000 gleichermassen, 6 bei Tiefe 5. 26 ist ein **Deckel der Antwort**, nicht der Bestand. Die Schwelle 64 (`MAX_RECHECKS_ABSOLUTE`) war damit unerreichbar, das dreiwertige Urteil fiel auf zweiwertig zurueck, vier Faelle blieben rot | `docs/audits/2026-09-phase-11/README.md:833-858` |
| Was ist der 52.111er-Fremdbestand? | Der Lastkorpus der Box traegt dieselben Woerter wie die Sprachfaelle. Ein eigenes Konto trennt die **Berechtigung**, nicht den **Index**: der Vorfilter rankt ueber den ganzen Bestand. Fuer `Bescheid` stand die eigene Datei auf Rang 1.925 von 2.000 | `docs/measurements/2026-09-werkzeugfixe/skripte/00-ablauf.md:33`, `00-ablauf.md:96` (E3) der v12-Fassung |
| Was ist die neue Messgroesse? | Der Bestand entsteht **im Prozess des Containers** ueber `ranked_sides` und `count`, ungedeckelt; die Messbarkeit haengt am **Rang der eigenen Datei** in den beiden Ranglisten statt an einer Trefferzahl. Schwelle unveraendert 64 | `docs/measurements/2026-09-v12-messung/skripte/73-bestand-sonde.py:36-38,59,102-125` |
| Werkzeug | `98c-sprachfaelle.sh` (44 kB, Phase 12, **noch nie gefahren**), Abschnitt 0 ruft die Sonde vor dem Upload, Abschnitt 3b ein zweites Mal nach Upload und Indexierung | `docs/measurements/2026-09-v12-messung/skripte/98c-sprachfaelle.sh` |
| Vorbedingungen | `CI_LAUF` (sonst Rueckgabewert 22), `jq` auf der Box (sonst 18), fahrbare Sonde (sonst 19 vor dem Upload, 24 nach der Indexierung) | Runbook 3.1, 3.7, 7.1 |
| Kontrollbeleg ohne Fremdbestand | `integration.yml`, Job `index-search-e2e` faehrt dieselben zehn Faelle auf frischer Instanz und ist gruen | `docs/audits/2026-09-phase-11/README.md:855-857` |
| Erwartung, vorher notiert | E1: Bestand je Begriff **ueber 26**; E2: Fensterbelegung saettigt bei **100** (`SEARCH_RRF_WINDOW`); E3: mindestens einer der vier roten Faelle ist jetzt messbar oder wird mit Rangangabe als nicht messbar ausgewiesen | `docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md:94-96` |

### 4. Wiederaufwaerm-Kosten der Entladung und MEM-02 (Erfolgskriterium 5)

Vier Auspraegungen, Reihenfolge bindend (`docs/runbook-messbox.md:785-790`):

| Nr | `FINDLING_EMBED_IDLE_RELEASE_SECONDS` | Seitencache | Gemessen wird |
|---|---|---|---|
| 1 | Vorschlagswert (900) | **kalt**, Wirtscache vorher geleert | Antwortzeit der degradierten Suche und die Dauer des Nachwaermens daneben |
| 2 | Vorschlagswert (900) | warm | dieselbe Messung nach erneuter Ruhezeit |
| 3 | `0` | **kalt** | Bezugswert ohne Entladung, Muster `95b-kaltstart-reproduktion` |
| 4 | `0` | warm | derselbe Bezugswert ohne Leeren |

Drei Fallen, die das Runbook als Abbruchpfade fuehrt:

- **Rueckgabewert 30:** Ein Aufruf der Diagnose-Route (`ranked_sides`) **laedt das Modell**.
  Vor einer Kaltmessung darf sie deshalb nicht gerufen werden. Die Fremdbestands-Vorpruefung
  (Schritt 3) faehrt **nach** den Kaltmessungen 1 und 3 oder nimmt den Aufwaermeffekt ins
  Protokoll. Eine aufgewaermte Kaltmessung wird **nicht herausgerechnet**, sondern nach
  einer erneuten Ruhephase wiederholt (`:798-810`).
- **Die zweite Haelfte derselben Falle:** Nach einer Entladung meldet die Diagnose-Route
  eine vollstaendige semantische Seite, weil sie laedt, die Nutzerrouten im selben Moment
  eine leere, weil sie unter dem Schalter nicht laden duerfen. Ob die semantische Seite
  steht, wird **an der Nutzerroute** abgelesen (`:812-819`).
- **Rueckgabewert 31:** Der Ast mit eingeschaltetem Schalter braucht den Beleg, dass
  entladen wurde: Zustand `unloaded` auf der Statusseite **und** Entladezaehler ueber null
  (`:821-824`).
- **Rueckgabewert 29:** Die Stellung des Schalters ist Pflichtzeile je Messschritt
  (`entladeschalter-ist=<sekunden>`). Die Schritte 1 bis 7 und 9 laufen auf **0**, Schritt 8
  faehrt beide Stellungen (`:631`, `:689-713`).
- **Der Messcontainer des `one_load`-Gates hat den Schalter auf `0`** (`:715-720`): das
  Werkzeug `findling.tools.one_load` gibt in seiner vierten Phase selbst frei und laedt
  ueber eine zweite echte Suchrunde nach; bei einem Wert ungleich 0 weist
  `query_may_load()` die zweite Runde zurueck und das Werkzeug meldet einen Befund, den es
  nicht gibt.

**MEM-02 haengt daneben und ist ein eigener Block.** Die Messgroesse heisst
`Rueckkehr zur Grundlast nach einem Indexlauf` und heisst ausdruecklich **nicht**
"Grundlast minus X" (`docs/performance.md:3609-3622`). Gemessen wird die Differenz
zwischen "vor der Entladung" und "nach der Entladung", **nach einem Indexlauf**, weil erst
dann Tokenizer, Splitter, Sitzung und der Aktivierungsspeicher (plus 293,8 MB beim ersten
`run`) im Container stehen. Der Bodensatz, der nie zurueckkommt, ist auf aarch64 mit rund
**16 MB** gemessen (`docs/measurements/2026-09-entladung-vorpruefung/`). Werkzeug:
`scripts/ops/rss_sampler.sh` und `rss_digest.py`, beide vorhanden und unveraendert.

### 5. Was noch mitreist

| Auftrag | Herkunft | Anmerkung |
|---|---|---|
| Marge der ersten Suche nach einer Entladung auf langsamerer Hardware | `14-12-SUMMARY.md`, "Issues Encountered" | 1,37 bis 1,44 s gegen 1,5 s auf der Entwicklungsmaschine, warm 0,41 bis 0,48 s; Ursache ist der Nachwaermlauf, nicht die Degradation |
| Vorschlagswert 900 s belegen oder korrigieren | `14-12-SUMMARY.md`, "Next Phase Readiness" Punkt 3 | Heute gekennzeichnete Schaetzung an zwei Stellen (`backend/appinfo/info.xml:469`, `docs/embeddings.md`) |
| Runbook-Nachtraege | D-10 | Jeder Block mit der Marke "in Phase 15 erstmals vollzogen" bekommt seine tatsaechliche Ausgabe; Abweichungen bleiben als eigene Zeile stehen |
| Pruefsummen-Waechter fuer die gefahrenen Fassungen | `00-ablauf.md:148-151` der v12-Fassung | Nach dem Lauf fuer `98c-sprachfaelle.sh` und `97-cron-vorpruefung.sh` in `backend/tests/test_measurement_scripts.py` nachziehen |
| Snapshot-Wiedervorlage | Runbook 8.9 | Nach v1.2 entscheiden: loeschen oder guenstigere Speicherklasse; **nicht** Teil dieser Phase |

---

## Erfolgskriterien und ihre Belegartefakte

Die Tabelle ist als Vorlage fuer die `must_haves` der Plaene gedacht.

| SC | Beleg | Artefakt |
|---|---|---|
| 1 | Zeile `Anfahrt freigegeben: <Datum>, Deckel <h> h / <USD> USD` im Bericht des Laufs, geschrieben **vor** der ersten Minute | `docs/measurements/2026-09-v12-messung/README.md` plus Owner-Antwort im Plan-Summary |
| 2 | Volllauf-Zeitreihe, Waechterprotokoll, beide Cron-Zweige, alle sechs Vergleichbarkeitsgroessen | `rohdaten/96-volllauf.csv`, `rohdaten/96b-waechter.txt`, `rohdaten/97-cron-vorpruefung-vorher.txt`, `rohdaten/97-cron-vorpruefung-waehrend.txt`, `rohdaten/04-bestand-vor-der-messung.txt`, `rohdaten/93-nullstand.txt` |
| 3 | Fuenf Stufen mit p95, Trefferdichte, Gegenrechnung gegen das Nextcloud-Protokoll, **je Stufe ein Verdikt** | `rohdaten/95-*.json`, `rohdaten/95-*.csv`, `rohdaten/97-nebenlaeufigkeit.txt`, Abschnitt im Bericht |
| 4 | Dreiwertiges Urteil je Fall am Rang, Bilanzzeile mit zwei Zahlen, `ci-beleg` mit Laufnummer, Abschnitt 0 und 3b der Sonde | `rohdaten/05-sprachfaelle.txt` |
| 5 | Vier Auspraegungen mit `entladeschalter-ist`, Zeit seit Containerstart, `unloaded` plus Entladezaehler, MEM-02-Differenz, danach der vollstaendige Abbau mit drei Nichtexistenz-Nachweisen und Tag-Sweep ueber beide Tagwerte | `rohdaten/95b-wiederaufwaermen-*.txt`, `rohdaten/90-bestand.txt`, `rohdaten/96-vektorbestand.txt`, `rohdaten/93-kosten-und-verbleib.txt`, `rohdaten/<nr>-abbau.txt` |

---

## Deckel-Rechenblatt, neu gerechnet (Erfolgskriterium 1)

### Kostensaetze

Sechs gepinnte Saetze aus `scripts/ops/aws_box.sh:162-166`, Abfrage vom 04.09.2026, netto
in USD. Die regionale Preisliste wird bewusst nicht heruntergeladen (ueber ein Gigabyte),
und dem Zugang dieses Kontos fehlt ausserdem `pricing:GetProducts`
(`docs/performance.md`, Abschnitt "Der ARM-Lauf, AWS").

| Satz | Wert | Pruefung in dieser Sitzung |
|---|---|---|
| m7g.large, eu-central-1 | 0,097800 USD/h | [CITED: doit.com/compute, eu-central-1] `m7g.xlarge` steht dort auf 0,1955 USD/h; die Haelfte davon ist 0,09775, also deckungsgleich mit dem gepinnten Satz. **Nicht** direkt auf der AWS-Preisseite nachgelesen |
| gp3, eu-central-1 | 0,0952 USD je GB und Monat | [CITED: aws.eu/ebs/pricing, Websuche] ausdruecklich 0,0952 USD je GiB-Monat fuer diese Region |
| Speicheranteil bei 100 GB (60 GB Datentraeger plus 40 GB Systemplatte) | 0,013041 USD/h | [VERIFIED: nachgerechnet] 0,0952 x 100 / 730 = 0,0130411 |
| oeffentliche IPv4 | 0,005000 USD/h | [ASSUMED] gepinnt, in dieser Sitzung nicht gegengeprueft |
| **laufend gesamt** | **0,115841 USD/h** | [VERIFIED: nachgerechnet] 0,0978 + 0,013041 + 0,005 |
| angehalten | 0,3130 USD je Tag | [ASSUMED] gepinnt |
| Snapshot, dauerhaft | 2,79 bis 2,99 USD je Monat | gehoert **nicht** in den Stundendeckel, sondern in die Monatsrechnung (`docs/runbook-messbox.md:158-160`) |

### Zeitposten, mit zwei Nachtraegen

Die ersten acht Zeilen sind das Rechenblatt des Runbooks (`:114-123`), die beiden mit
**NEU** markierten sind der Nachtrag dieser Recherche.

| Posten | Planwert | Quelle |
|---|---:|---|
| Handaufbau der Maschine (SG, Schluessel, Instanz, `mem=4G`, Neustart) | 2 h 30 min | nirgends gemessen, Annahme A8, ausdruecklich Schaetzung |
| Wiederaufbau aus dem Snapshot und Ruestzeit (Volume, Mount, Docker, Rueckspielung, A-Record, Bewaffnung) | 1 h 30 min | v1.1: 38 min bei bestehender Box, Aufschlag geschaetzt |
| **NEU: Abbildwechsel auf den v1.2-Stand** (Pull, Registrierung, PHP-Haelfte, harte Grenze, Baumhash) | **1 h 00 min** | Muster `92-wechsel.sh`; im Rechenblatt des Runbooks nicht enthalten, siehe Pitfall 1 |
| Volllauf beide Spuren bis zum letzten Vektor | 26 h 37 min | v1.1, Abschnitt 7 des Berichts, **gemessen** |
| **NEU: MEM-02-Block** (Grundlast vor und nach dem Indexlauf, Freigabe abwarten, `rss_sampler`) | **0 h 45 min** | MEM-02 ist in keiner Zeile des Runbook-Rechenblatts enthalten |
| Untersuchung der vier regressiven Laststufen, je ein Entscheid | 1 h 30 min | neu in v1.2, geschaetzt |
| Wiederaufwaerm-Messung in vier Auspraegungen | 2 h 00 min | neu in v1.2, geschaetzt; bei TTL 900 s knapp, siehe Hinweis unten |
| Sprachfall-Messung mit der neuen Messgroesse, inklusive Erstvollzug | 1 h 00 min | neu in v1.2, geschaetzt |
| Abbau und Endmessungen | 1 h 00 min | v1.1 Abschnitt 17 und der Abbaulauf vom 11.09.2026 |
| **Summe** | **37 h 52 min** | Runbook-Summe 36 h 07 min plus 1 h 45 min Nachtrag |

### Der Rechenweg

```
Deckel (Stunden) = Summe der Zeitposten x (1 + Zuschlag 15 Prozent fuer Erstvollzug)
37,87 h x 1,15 = 43,55 h, aufgerundet 44 h
44 h x 0,115841 USD/h = 5,0970 USD, aufgerundet 5,10 USD
```

| Vorschlag | Stunden | USD netto | Anmerkung |
|---|---:|---:|---|
| Untergrenze | 31 h | 3,59 USD | so viel hat der v1.1-Lauf bei **kleinerem** Arbeitsumfang verbraucht; ein Vorschlag darunter ist gerissen, bevor er ausgesprochen ist |
| Runbook-Stand (16.09.) | 42 h | 4,90 USD | ohne Abbildwechsel und ohne MEM-02-Block |
| **Empfehlung dieser Recherche** | **44 h** | **5,10 USD** | mit beiden Nachtragsposten |

**Die Deckel-Geschichte, damit die Zahl ihren Massstab hat** (`:164-168`): Owner-Deckel vom
09.09. waren 30 h / 3,50 USD, am 10.09. um 15:20Z gerissen und auf 34 h / 4,00 USD
angehoben, verbraucht wurden am Ende 31,05 h / 3,5969 USD.

**Drei Stellschrauben, falls der Owner kuerzen will** (Pitfall 15, `PITFALLS.md:336-341`):
Deckel anheben, oder Teilkorpus (kostet die Vergleichbarkeit und widerspricht D-04), oder
den Volllauf detached ueber Nacht fahren und alles davor und danach so buendeln, dass keine
Box-Stunde auf einen Menschen wartet. Die dritte ist die einzige, die nichts kostet, und
sie ist in v1.1 bereits bewaehrt.

**Hinweis zur Wiederaufwaerm-Messung und zum Vorschlagswert:** Auspraegung 1 und 2 warten
je eine volle Ruhezeit ab. Beim Vorschlagswert 900 s sind das zweimal 15 Minuten reine
Wartezeit plus zwei Containerneubauten (Schalterwechsel), nach jedem davon werden die harte
Speichergrenze und die Pflichtzeile neu abgelesen. Zwei Stunden sind dafuer knapp
kalkuliert. Der zulaessige Bereich der Variablen ist 60 bis 86400 Sekunden
(`backend/appinfo/info.xml:469`); eine kuerzere Frist waere billiger, weicht aber vom
Wortlaut des Runbooks ab ("Vorschlagswert ... im Protokoll mit seinem Wert genannt", `:792`).
Das ist eine Owner-Frage, keine Ermessensfrage des Planers.

### Wohin die Schlusszahlen VOR dem Abbau geschrieben werden

`aws_box.sh destroy` loescht `box.env`, und damit die einzige Kosten- und Schadenshistorie
der Box. Das ist am 11.09.2026 bereits eingetreten. Vor dem Abbau wandern deshalb
`BOX_LAST_UPTIME_HOURS`, `BOX_LAST_UPTIME_COST_USD`, der freigegebene Deckel und die
Differenz in eine committete Rohdatei, nach dem Muster von
`docs/measurements/2026-09-werkzeugfixe/rohdaten/07-snapshot-und-abbau.txt`, Abschnitt 5
(`docs/runbook-messbox.md:193-206`, Abbau-Schritt 2).

---

## Die Ausfuehrungsform: was vor der Box entsteht und was auf der Box laeuft

### Welle A, ohne Box-Zeit, vollstaendig autonom ausfuehrbar

| Aufgabe | Warum vor der Box | Belegstelle |
|---|---|---|
| Sechs Messwerkzeuge aus dem v1.1-Verzeichnis in `2026-09-v12-messung/skripte/` **kopieren** (`90-bestand.sh`, `93-nullstand.sh`, `95-spitze.sh`, `96-volllauf.sh`, `96b-waechter.sh`, `96c-lesen.py`, `96d-statusbeobachter.py`, `97-nebenlaeufigkeit.sh`, `40b-baumhash.sh/.py`) | Gefahrene Skripte werden nie editiert, Nachfolgefassungen bekommen ein neues Laufverzeichnis | `ARCHITECTURE.md` C.1 und C.3; `test_the_driven_language_case_script_stays_byte_identical` |
| **Das fehlende Werkzeug der Wiederaufwaerm-Messung bauen** (vier Auspraegungen, Rueckgabewerte 29, 30, 31, alle unterhalb der `tee`-Pipeline) | Es existiert nicht; `95b-kaltstart-reproduktion` ist eine Rohdatei von Hand | siehe Pitfall 2 |
| **Einen dokumentierten Befehl zum Leeren des Seitencaches** festlegen und in die Ablaufdatei schreiben | Das Runbook fordert die Bedingung, nennt aber keinen Befehl | siehe Pitfall 4 |
| Ablaufdatei `00-ablauf.md` des v12-Verzeichnisses auf neun Schritte fortschreiben, mit **vorher notierten Erwartungen** E8 ff. fuer die neuen Bloecke | "Die Erwartung steht weiter unten mit Zahlen da, damit sie nach der Messung nicht zur Erklaerung des Ergebnisses werden kann"; Beweis ist der Commit-Zeitstempel | `00-ablauf.md:4-7`, Praezedenz in `2026-09-entladung-vorpruefung/README.md` (Erwartung 29 Minuten vor den Rohdaten committet) |
| Neun Vorbedingungen des Runbooks Abschnitt 3 abarbeiten und protokollieren | Jede kostet sonst bezahlte Minuten | `docs/runbook-messbox.md:217-230` |
| Deckel-Rechenblatt neu rechnen und dem Owner vorlegen | D-05 | `:101-206` |
| Gate-Anpassung pruefen: `NARROW_SCOPE_DIRS` deckt das v12-Verzeichnis bereits ab | Kein neues Laufverzeichnis noetig, wenn in `2026-09-v12-messung` gemessen wird | `backend/tests/test_measurement_scripts.py:1167-1183` |
| Trockenlauf aller neuen Skripte, soweit ohne Box moeglich (Syntax, `--help`, Verweigerungspfade) | "Skripte, die auf der Box laufen, muessen vorher auf der Box gelaufen sein"; wo das nicht geht, wenigstens die Verweigerungspfade testen (Muster: die zwei boxlosen Tests aus WR-04) | Pitfall 18; `test_measurement_scripts.py:1250-1288` |

### Welle B, der eine Owner-Checkpoint

Deckelfreigabe mit Datum. Ohne sie startet nichts. Dem Owner gehoeren dabei vorgelegt: das
neu gerechnete Rechenblatt, die Deckel-Geschichte (30 h gerissen, 34 h gehalten, 31,05 h
verbraucht), die drei Stellschrauben und die Frage nach dem Vorschlagswert 900 s gegen eine
kuerzere Ruhezeit.

### Welle C, die Anfahrt

**Autonom ausfuehrbar oder nicht?** Die Anmeldung liegt vor
(`C:/Users/Student/.findling-aws.env`, in dieser Sitzung als vorhanden geprueft), und
Phase 12 hat mit ihr bereits drei kostenlose lesende AWS-Proben gefahren
(`12-03-SUMMARY.md:131`: "Die AWS-Anmeldung lag vor und ist gueltig"). Technisch ist die
Kette also fahrbar. Drei Stellen sind es trotzdem nicht ohne Menschen:

1. **Der A-Record** `loadtest.infranode.dev` wird beim Zonenverwalter gesetzt; dafuer gibt
   es im Repositorium keinen Zugang (Runbook 3.8 fuehrt ihn als eigene Vorbedingung).
   Rueckfaelle: `/etc/hosts`-Pin nach jedem Maschinenneustart neu bilden, oder
   `curl --resolve`.
2. **Der Deckel** ist eine Freigabe, keine Ausfuehrung.
3. **Die Dauer.** Der Volllauf laeuft 26 Stunden; kein Plan-Ausfuehrungslauf sitzt daneben.
   Der Lauf gehoert detached gestartet, mit `96b-waechter.sh` als Beobachter, und die
   Auswertung ist ein eigener Plan danach.

**Empfehlung:** Welle C wird als **begleitete Sitzung** geplant, nicht als autonome
Ausfuehrung. Die Plaene schreiben die Kommandobloecke, die erwarteten Ausgaben und die
Abbruchbedingungen vor; ausgefuehrt wird Block fuer Block, und jede tatsaechliche Ausgabe
geht sofort in die Rohdatei. Das ist genau die Form, die das Runbook D-10 vorsieht, und es
ist die einzige, die beim ersten Vollzug eines 1102-Zeilen-Verfahrens ehrlich ist.

---

## Bindende Reihenfolge auf der Box

Aus `docs/runbook-messbox.md:724-741` und `:781-790`, zusammengezogen mit den zwei Fallen,
die die Reihenfolge erzwingen.

```
Aufbau (Bloecke 1 bis 13)
  1 Security Group, 2 Schluessel, 3 Instanz, 4 box.env von Hand, 5 mem=4G + Neustart
  6 restore (Volume aus dem Snapshot), 7 mounten ueber die UUID
  8 Docker-data-root VOR dem ersten Daemonstart, 9 Systemplatte zurueckspielen
  10 A-Record, 11 Bewaffnung (disable/enable, GEZAEHLTER Pollerdurchgang)
  12 harte Speichergrenze AUS DER CGROUP, 13 genau EINE Nextcloud
        |
        v
[LUECKE: Abbildwechsel auf den v1.2-Stand, siehe Pitfall 1]
        |
        v
Schritt 1  Zustandspruefung  -> 52.111 / 37 / 0 / 3.9Gi / 2 / aarch64, sonst ENDE
           Nullstandsbeleg   -> 93-nullstand.sh, dann findling:index --restart -n
Schritt 2  Cron vorher       -> Pflichtzeile cron-intervall-ist  (Abbruch 25, 26)
Schritt 3  Bestandssonde     -> Abschnitt 0 von 98c              (Abbruch 19)
           ACHTUNG: die Sonde faehrt ueber ranked_sides und WAERMT den Container
Schritt 4  Volllauf          -> detached, mit 96b-waechter.sh daneben
Schritt 5  Cron waehrend     -> neben dem Volllauf               (Abbruch 27, 28)
Schritt 6  Laststufen 1/4/8/12/16 -> laedt das Modell absichtlich vorher
Schritt 7  Sprachfaelle      -> CI_LAUF=<nr> ./98c-sprachfaelle.sh (15..19, 22..24)
Schritt 8  Wiederaufwaermen  -> KALT zuerst (1, dann 3), danach warm (2, 4)  (29, 30, 31)
Schritt 9  Endmessungen und Gegenproben VOR jedem zerstoerenden Schritt
        |
        v
Abbau 1 erheben, 2 box.env in die Rohdatei und auf origin, 3 stop + snapshot,
      4 Snapshot unabhaengig nachlesen (der Waiter gibt nach 10 min auf, der
        Snapshot brauchte am 11.09. rund 52 min), 5 FINDLING_STATE_BACKUP,
      6 destroy, 7 Tag-Sweep ueber BEIDE Tagwerte, 8 Kostenueberblick,
      9 was bewusst stehen bleibt
```

**Der Konflikt, den der Planer aufloesen muss:** Schritt 3 (Bestandssonde) und Schritt 6
(Laststufen) waermen den Container auf, Schritt 8 braucht kalte Auspraegungen. Das Runbook
loest ihn fuer Schritt 3 ausdruecklich ("faehrt sie **nach** den Kaltmessungen 1 und 3 oder
nimmt den Aufwaermeffekt ins Protokoll"), sagt aber zugleich, dass Schritt 3 vor dem
Hochladen der 39 Dateien und damit vor Schritt 7 liegt. Die sauberste Auflosung: die
Kaltmessung des Schrittes 8 wird **nach** Schritt 6 und 7 gefahren, mit vorherigem
Containerneustart **und** geleertem Wirtscache; dann ist "kalt" hergestellt statt bewahrt.
Diese Auflosung gehoert als Zeile in die Ablaufdatei, bevor die Box steht.

---

## Standard Stack

Diese Phase installiert nichts. Ihr Stack sind Werkzeuge, die im Repositorium liegen.

### Kern

| Werkzeug | Ort | Zweck | Zustand |
|---|---|---|---|
| `aws_box.sh` | `scripts/ops/aws_box.sh` (56 kB, neun Unterbefehle) | Volume aus Snapshot, Start, Stopp, Snapshot, Abbau, Preise | fertig seit 12-03, `restore` noch nie erzeugend gefahren |
| `search_load.py` | `scripts/ops/search_load.py` | Laststufen ueber die OCS-Route, p95, Trefferdichte, cgroup daneben | **gefixt und geeicht seit 10.09., wird nicht mehr angefasst** |
| `rss_sampler.sh`, `rss_digest.py` | `scripts/ops/` | cgroup-Abtastung fuer Grundlast und MEM-02 | unveraendert |
| `97-cron-vorpruefung.sh` | `docs/measurements/2026-09-v12-messung/skripte/` (24 kB) | Cron-Konfigurations- und Wirkungszweig, fail-closed | Phase 12, noch nie gefahren |
| `98c-sprachfaelle.sh` | ebenda (44 kB) | Sprachfaelle mit Rangsemantik, Abschnitt 0 und 3b | Phase 12, noch nie gefahren |
| `73-bestand-sonde.py` | ebenda | ungedeckelte Bestandsmessung im Containerprozess | Phase 12, noch nie gefahren |
| `findling.tools.one_load` | `backend/src/findling/tools/one_load.py` | Beweis der one_load-Zusage, vier Phasen | Phase 14; **Schalter im Messcontainer auf 0** |

### Zu kopieren (aus `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/`)

| Werkzeug | Wofuer | Aenderung |
|---|---|---|
| `96-volllauf.sh`, `96b-waechter.sh`, `96c-lesen.py`, `96d-statusbeobachter.py` | Wirkungsbeleg DI-10-04 | kopieren, nicht editieren |
| `97-nebenlaeufigkeit.sh` | vier regressive Laststufen | kopieren; Stufenliste steht bereits auf `1 4 8 12 16` |
| `95-spitze.sh` | Erstkosten der Einbettung, getrennt von der Stufenreihe | kopieren |
| `90-bestand.sh`, `93-nullstand.sh`, `91-korpus.sh` | Bestand, Nullstandsbeleg, Korpuspruefung | kopieren |
| `40b-baumhash.sh` und `40b-baumhash.py` | Vergleichbarkeitsgroesse "Werkzeugstand" | unveraendert, per Test reproduziert |
| `92-wechsel.sh` | **Abbildwechsel**, siehe Pitfall 1 | Muster; als Nachfolgefassung mit neuer Nummer, nicht editiert |

### Neu zu bauen

| Werkzeug | Zweck | Muss koennen |
|---|---|---|
| Wiederaufwaerm-Messung (Arbeitsname `95b-wiederaufwaermen.sh`) | Schritt 8, vier Auspraegungen | Schalterstellung ablesen und als `entladeschalter-ist=` schreiben (29), Diagnoseaufruf vor einer Kaltmessung erkennen (30), `unloaded` und Entladezaehler pruefen (31), alle drei **unterhalb** der `tee`-Pipeline; Seitencache leeren; erste Suche und Nachwaermdauer getrennt messen |
| MEM-02-Block (Arbeitsname `94b-grundlast-rueckkehr.sh`) | Rueckkehr zur Grundlast nach einem Indexlauf | RSS vor der Freigabe, nach der Freigabe, Differenz; keine erfundene Ersparnis gegen die Grundlast eines Containers, der nie eingebettet hat |

**Installation:** keine. Auf der Box wird `jq` gebraucht (Vorbedingung 7); es kommt aus der
Ubuntu-Paketquelle der Box und ist keine Registry-Abhaengigkeit.

---

## Package Legitimacy Audit

**Nicht zutreffend, und das ist belegt statt behauptet.** Diese Phase installiert kein
Paket aus einer Paketregistry: kein `npm install`, kein `pip install`, keine Aenderung an
`backend/pyproject.toml` oder `backend/uv.lock`. Die einzige Fremdsoftware, die auf der Box
dazukommt, ist `jq` aus der Distributionsquelle der Ubuntu-Box, und es ist eine
Vorbedingung, kein Bestandteil der Auslieferung.

`slopcheck` wurde deshalb nicht gefahren. Sollte ein Plan dieser Phase wider Erwarten eine
Abhaengigkeit hinzufuegen wollen, gilt die Regel unveraendert: erst Registry-Pruefung und
`slopcheck`, dann `checkpoint:human-verify`, dann Installation.

Ein Pin ist trotzdem erwaehnenswert, weil er die Vergleichbarkeit traegt:
`onnxruntime==1.30.0` (`backend/pyproject.toml:44`, `backend/uv.lock:213`). Er bleibt in
dieser Phase **eingefroren**; ein Versionssprung zwischen Abbildbau und Messung wuerde die
Speicher- und Ladezahlen unvergleichbar machen. Offene Dependabot-Vorschlaege gibt es
derzeit keine (`gh pr list --state open` liefert eine leere Liste, geprueft 2026-09-19).

---

## Runtime State Inventory (Zustand ausserhalb des Repositoriums)

Diese Phase ist keine Umbenennung, aber sie lebt fast vollstaendig von Zustand, der nicht
im Repositorium liegt. Die Kategorien sind deshalb sinngemaess uebernommen.

| Kategorie | Was gefunden wurde | Handlung |
|---|---|---|
| **Gespeicherte Daten** | Korpus-Snapshot `snap-03f1d1d9ad9262704`: `State completed`, `Progress 100%`, `VolumeSize 60`, `purpose=findling-corpus-keep`, rund 55,4 GB geschriebene Bloecke; enthaelt Docker-`data-root`, lokale Registry, `ncdata` mit 50.000 Lastdateien, Tantivy-Index und Vektorablage im Zustand vom 10.09. (52.111 Dokumente) | lesend geprueft am 14.09. (`rohdaten/01-aws-lesende-proben.txt`); in Phase 15 erstmals erzeugend benutzt |
| **Lebende Dienstkonfiguration** | A-Record `loadtest.infranode.dev` zeigt seit dem 11.09.2026 ins Leere; die Zone liegt beim externen Verwalter, nicht im Repositorium | Owner setzt ihn neu; zwei Rueckfaelle im Runbook Block 10 |
| **Betriebssystem-registrierter Zustand** | Es gibt **keine** `box.env` mehr (`~/.findling-loadtest/` enthaelt nur `systemplatte-2026-09/`, in dieser Sitzung geprueft). Ohne sie brechen `volume`, `restore`, `stop`, `start`, `snapshot` in `require_state` ab, `create` verweigert grundsaetzlich, `status` faellt weich auf die Tagsuche zurueck | Block 4 schreibt `BOX_INSTANCE_ID` und `BOX_SECURITY_GROUP` von Hand neu; alles Weitere haengt `aws_box.sh` selbst an |
| **Geheimnisse und Umgebungsvariablen** | `C:/Users/Student/.findling-aws.env` (126 Byte, vorhanden), Passwortdateien der Konten `admin` und `lasttest` in `home-ubuntu-work.tar.gz`, SSH-Schluessel wird neu erzeugt. Auf der Box: `FINDLING_EMBED_IDLE_RELEASE_SECONDS` reist als Umgebungsvariable der ExApp und **geht bei jeder Registrierung verloren**, genau wie die harte Speichergrenze | Alle drei bleiben ausserhalb des Arbeitsbaums; die Schalterstellung wird nach jeder Registrierung **neu abgelesen**, nie erinnert |
| **Bauartefakte** | Sicherung der Systemplatte `home-ubuntu-work.tar.gz`: 3.971.065 Byte, sha256 `fad3e7ce...3584a` , **in dieser Sitzung gegen `07-snapshot-und-abbau.txt` Abschnitt 4 geprueft und identisch**. Die lokale Registry im Snapshot traegt das Abbild vom 10.09., **nicht** den v1.2-Stand | Vorbedingung 2 damit erfuellt; der Abbildstand ist die Luecke aus Pitfall 1 |

---

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---|---|---|---|
| Volume aus dem Snapshot erzeugen, umtaggen, anhaengen | eigene `aws ec2`-Kette | `aws_box.sh restore` | liest vor jeder Erzeugung, nimmt ein vorhandenes Volume auf statt ein zweites zu erzeugen, taggt pflichtmaessig um und liest zurueck; WR-01 hat den Fremdvolume-Pfad bereits geschlossen |
| Laufzeit und Kosten der Box rechnen | Taschenrechner im Bericht | `aws_box.sh stop` schreibt `BOX_LAST_UPTIME_HOURS` und `BOX_LAST_UPTIME_COST_USD` | die Startzeit fuehrt die API auf die Sekunde; eine nachgereichte Zahl waere eine Schaetzung |
| Cron-Takt pruefen | `backgroundjobs_mode` lesen | `97-cron-vorpruefung.sh` mit **beiden** Zweigen | ein Konfigurationszweig allein haette am 10.09. gruen gemeldet, waehrend der Befund vorlag |
| Fremdbestand messen | OCS-Route abfragen | `73-bestand-sonde.py` im Containerprozess | die Route deckelt bei 26, egal welcher Begriff und welche Tiefe |
| Lasterzeugung | eigenes Lastskript | `search_load.py`, byteidentisch | jede Aenderung macht die Stufenzahlen gegen v1.1 unvergleichbar |
| Nachweis, dass die Box den Repo-Stand traegt | Digest von `:dev` aufschreiben | `40b-baumhash.sh` | `:dev` ist ein wandernder Zeiger; der Pfadfilter von `docker.yml` greift nach `backend/**`, also verschiebt schon eine neue Testdatei den Digest (DI-10-05) |
| Beweis der Bewaffnung | `app_api:app:list` ablesen | gezaehlter Pollerdurchgang im Protokoll | ein abgelesener Zustand war schon einmal gruen, waehrend nichts lief (DI-05-36) |
| Beweis, dass eine Ressource weg ist | Tag-Abfrage | Rueckleseprobe je Ressourcenart | die Tag-Abfrage antwortet aus einem nachlaufenden Verzeichnis; am 11.09. meldete sie zwei Datentraeger, die die API bereits als `InvalidVolume.NotFound` fuehrte |

**Kernsatz:** In dieser Domaene ist jedes selbstgebaute Werkzeug ein zweiter Messgegenstand.
Was gemessen werden soll, ist das Erzeugnis, nicht das Werkzeug.

---

## Common Pitfalls

### Pitfall 1: Das Abbild auf der Box ist der Stand vom 10.09., und niemand hat es gemerkt

**Was schiefgeht:** Der Snapshot traegt die lokale Registry der Box mit dem Abbild vom
10.09.2026. Der Volllauf misst dann einen Container **ohne** Top-up-Route, **ohne** die
Filter aus Phase 13 und **ohne** den Entladeschalter aus Phase 14. Erfolgskriterium 2 waere
damit unerfuellbar (es verlangt den Volllauf "mit Top-up-Fix"), Erfolgskriterium 5 ebenso
(es verlangt A/B ueber einen Schalter, den dieses Abbild nicht kennt).

**Warum es passiert:** Das Runbook hat **keinen Block fuer den Abbildwechsel**. Block 8
prueft nur, dass die Registry aus dem Snapshot antwortet
(`{"repositories":["findling_backend"]}`, `:459-462`). Abschnitt 6 verlangt dagegen den
Baumhash als Vergleichbarkeitsgroesse und haelt den Lauf an, wenn dort `nein` steht
(`:630`). Beide Saetze zusammen ergeben eine Luecke, die erst auf der Box auffaellt.

**Wie vermeiden:** In Welle A einen Block "Abbildwechsel" nach dem Muster von
`92-wechsel.sh` schreiben und in die Ablaufdatei aufnehmen. Der Kopf jenes Skripts nennt
die Abhaengigkeitskette woertlich: erst die PHP-Haelfte (Verzeichnis **muss** `findling`
heissen, sonst findet der Klassenlader nichts und es gibt nirgends eine Fehlermeldung),
dann die Registrierung, dann die harte Grenze aus der cgroup. `unregister --rm-data` nur
**vor** dem Indexaufbau und nie danach, und nie ohne die Zaehlung der laufenden
Nextcloud-Instanzen davor.

**Warnzeichen:** `baumhash-gleich nein`. Ein Volllauf, dessen Durchsatz genau dem v1.1-Lauf
gleicht. Ein Statusfeld, das `unloaded` nicht kennt.

### Pitfall 2: Der Messschritt 8 hat Rueckgabewerte, aber kein Skript

**Was schiefgeht:** Das Runbook fuehrt fuer Schritt 8 die Abbrueche 29, 30 und 31 und sagt,
sie stuenden "unterhalb der `tee`-Pipeline ihres Skripts" (`:826-829`). Ein solches Skript
gibt es nicht. `95b-kaltstart-reproduktion` ist eine **Rohdatei** von Hand aus dem v1.1-Lauf
(`docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/95b-kaltstart-reproduktion.txt`),
und sie enthaelt sogar einen `SyntaxError` aus einem inline getippten Python-Einzeiler.

**Warum es passiert:** Phase 12 hat drei Skripte gebaut, Phase 14 hat den Schalter gebaut,
und niemand hatte den Auftrag, das Messwerkzeug dazwischen zu bauen. `ARCHITECTURE.md` C.4
hat es vorhergesagt ("Fuer die Entladung fehlt ein Werkzeug, und es ist klein").

**Wie vermeiden:** In Welle A bauen, mit den drei Rueckgabewerten, und die Verweigerungspfade
boxlos testen, so wie WR-04 es fuer 98c und 97 verlangt hat.

**Warnzeichen:** Im Plan der Anfahrt steht "Messung nach dem Muster 95b" ohne Dateinamen.

### Pitfall 3: Der Resume ueber 52.000 fertige Zeilen, gemeldet als grandiose Verbesserung

**Was schiefgeht:** Der Snapshot traegt den **fertigen** Index. Wer ihn einspielt und einen
"Volllauf" anstoesst, misst einen Resume und meldet eine Verbesserung, die es nie gegeben
hat.

**Warum es passiert:** Der Snapshot ist als Korpusquelle gedacht, traegt aber Korpus **und**
Index (`:596-613`). Schon in v1.1 lagen beim Anstoss 1.653 Dateien im Index, weshalb dessen
Durchsatz eine Untergrenze ist.

**Wie vermeiden:** Nullstand **vor** dem Anstoss mit Zahlen belegen (Muster
`93-nullstand.sh`: Inhalt des Datentraegers, Zeilenstaende in `oc_findling_file_state`, die
Marken in `meta`, `occ findling:index`), dann `findling:index --restart -n` und die
Wartefrist. Zeigt die Ablesung danach keinen Nullstand, wird **nicht** angestossen.

**Warnzeichen:** unplausibel hoher Durchsatz in den ersten Minuten.

### Pitfall 4: "Seitencache geleert" ohne Befehl

**Was schiefgeht:** Zwei der vier Auspraegungen sind als "kalt, Cache des Wirts vorher
geleert" definiert, aber im ganzen Runbook steht kein Befehl dafuer (in dieser Sitzung
gegrept: `drop_caches` kommt nicht vor). Jede Person macht es anders, und "kalt" wird zu
einem Wort statt zu einer Bedingung.

**Wie vermeiden:** Den Befehl festlegen, in die Ablaufdatei schreiben und im Protokoll
belegen (`sync`, dann `/proc/sys/vm/drop_caches` mit dem Wert 3, als Wirt und nicht im
Container). Dazu die Nebenwirkung benennen: das Leeren verwirft auch den mmap-Cache des
Tantivy-Index, also misst die "kalte" Suche beide Haelften kalt. Das ist die gewollte
schlechtere Haelfte der Wahrheit, aber es muss dastehen.

**Warnzeichen:** Zwei Kaltmessungen unterscheiden sich um mehr als das Rauschband von fuenf
Prozent.

### Pitfall 5: Der Deckel ist kleiner als der Lauf (Pitfall 15 der Milestone-Recherche)

Der 26-h-Vorschlag reisst rechnerisch, weil der letzte Volllauf allein 26 h 37 min gedauert
hat. In v1.1 ist der 30-h-Deckel am 10.09. um 15:20Z gerissen und wurde auf 34 h angehoben.
**Wie vermeiden:** von der gemessenen Laufzeit ausgehen, nicht von der erhofften; der
Planwert des Volllaufs nimmt keine Verbesserung vorweg.

### Pitfall 6: Die Vergleichbarkeit bricht an fuenf Stellen gleichzeitig (Pitfall 16)

Startzustand, Cron-Intervall, der Fix selbst, das Lastwerkzeug, der Seitencache des Wirts.
Alle fuenf sind unauffaellig, und alle fuenf sind als protokollpflichtige Groessen in
Abschnitt 6 des Runbooks abgebildet. **Der Wirkungsbeleg laeuft mit derselben
Schalterstellung wie v1.1**, also mit `FINDLING_EMBED_IDLE_RELEASE_SECONDS=0`; sonst misst
er zwei Aenderungen auf einmal.

### Pitfall 7: Das Messwerkzeug zaehlt Ausfaelle als Erfolge (Pitfall 18)

Stufe 16 meldete `failures: 0` bei 160 Anfragen, waehrend das Nextcloud-Protokoll im selben
Fenster 17 abgebrochene Containeraufrufe mit `cURL error 28` fuehrte, also 10,6 Prozent. Der
Zaehler ist seit dem 10.09. korrigiert (DI-10-01 geschlossen). **Wie vermeiden:** jede Stufe
gegen das Nextcloud-Protokoll aufrechnen, Trefferdichte mitfuehren, und die korrigierte
Zaehlung als Grund benennen, warum die neuen Stufenzahlen schlechter aussehen duerfen als
die alten.

### Pitfall 8: Eine zweite Nextcloud loescht das Messvolumen der ersten

Am 07.09.2026 hat eine zweite, frische Nextcloud am selben Docker-Dienst mit
`app_api:app:unregister --rm-data` das Messvolumen der **ersten** geloescht, weil der
Volumenname einer ExApp allein aus ihrer App-Kennung folgt. **Wie vermeiden:** Block 13
zaehlt, und die Zaehlung wird unmittelbar vor **jedem** `--rm-data` wiederholt. Liefert sie
mehr als 1, wird nichts weiter getan.

### Pitfall 9: Der Abbau loescht die Historie, die den Bericht traegt

`destroy` loescht `box.env`, und damit jede Anhalte- und Startzeit, den Schadensbericht vom
07.09. und den DI-05-36-Befund. Am 11.09. ist das bereits eingetreten. **Wie vermeiden:**
Abbau-Schritt 2 vor Schritt 6, Werte durch Platzhalter ersetzen, committen und **vor** dem
Abbau auf `origin` bringen.

### Pitfall 10: Der Waiter der CLI gilt als Urteil

Der Snapshot-Waiter gibt nach zehn Minuten auf; am 11.09. stand der Snapshot da bei
8 Prozent und brauchte rund 52 Minuten. Ein zweiter Aufruf ohne Kennung waere ein zweiter
Snapshot und eine zweite Rechnung. **Wie vermeiden:** `aws_box.sh snapshot <kennung>` liest
nur zurueck und erzeugt nichts.

### Pitfall 11: Git fuer Windows schreibt Pfadargumente um

Aus `/dev/sdf` wurde ein Windows-Pfad unterhalb des Git-Installationsverzeichnisses; der
Aufruf lief durch und meinte etwas anderes, als er sagte. **Wie vermeiden:** in jedem neuen
Skript, das von dieser Maschine gegen die Box oder die AWS-API laeuft, die Pfadumschreibung
fuer den eigenen Prozess abschalten, so wie `aws_box.sh` es tut.

### Pitfall 12: `sudo` raeumt die Umgebung, `docker exec` gibt keine weiter

In v1.1 mussten zwei Messskripte **waehrend** des Laufs korrigiert werden, weil `OC_PASS`
nirgends ankam. Das ist genau der Fehler, den die Regel "waehrend der Anfahrt wird kein
Werkzeug geaendert" teuer macht. **Wie vermeiden:** Passwoerter ueber `--password-env`
(Name, nie Wert), und der Gate-Test `test_the_script_of_this_run_puts_no_password_on_a_command_line`
haelt es fest.

---

## Code Examples

### Deckelfreigabe, die Zeile, die vor der ersten Minute geschrieben wird

```text
# Quelle: docs/runbook-messbox.md:227 (Vorbedingung 9)
Anfahrt freigegeben: 2026-09-__, Deckel 44 h / 5,10 USD
```

### Die sechs protokollpflichtigen Vergleichbarkeitsgroessen, je Messblock

```sh
# Quelle: docs/runbook-messbox.md:624-631
ssh <box> 'sudo docker exec --user www-data nextcloud-aio-nextcloud php occ findling:index'
./97-cron-vorpruefung.sh vorher                      # Pflichtzeile cron-intervall-ist
scripts/ops/aws_box.sh status                        # Instanztyp
ssh <box> 'docker exec nc_app_findling_backend cat /sys/fs/cgroup/memory.max'
ssh <box> 'docker exec nc_app_findling_backend cat /sys/fs/cgroup/memory.swap.max'
ssh <box> "docker inspect --format '{{.State.StartedAt}}' nc_app_findling_backend"
./40b-baumhash.sh                                    # baumhash-gleich
ssh <box> "docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' \
    nc_app_findling_backend" | grep FINDLING_EMBED_IDLE_RELEASE_SECONDS
```

### Die Pflichtzeile des Entladeschalters

```text
# Quelle: docs/runbook-messbox.md:689-695
entladeschalter-ist=0          # Schritte 1 bis 7 und 9
entladeschalter-ist=900        # Schritt 8, Auspraegung 1 und 2
```

### Der Nullstandsbeleg vor dem Anstoss

```sh
# Quelle: docs/runbook-messbox.md:596-613, Muster 93-nullstand.sh
ssh <box> 'sudo docker exec --user www-data nextcloud-aio-nextcloud php occ findling:index'
# Zeilenstaende in oc_findling_file_state und die Marken in meta ablesen
ssh <box> 'sudo docker exec --user www-data nextcloud-aio-nextcloud \
    php occ findling:index --restart -n'
# danach erneut ablesen: zeigt die Ablesung keinen Nullstand, wird NICHT angestossen
```

### Der Beweis der Bewaffnung, gezaehlt statt abgelesen

```sh
# Quelle: docs/runbook-messbox.md:507-524 (DI-05-36)
ssh <box> 'sudo docker exec --user www-data nextcloud-aio-nextcloud \
    php occ app_api:app:disable findling_backend'
ssh <box> 'sudo docker exec --user www-data nextcloud-aio-nextcloud \
    php occ app_api:app:enable findling_backend'
ssh <box> 'docker logs --since 5m nc_app_findling_backend 2>&1 | grep -c "poll"'
# Erwartung: groesser als null. app_api:app:list zaehlt hier ausdruecklich NICHT
```

### Tag-Sweep ueber beide Tagwerte

```sh
# Quelle: docs/runbook-messbox.md:971-988
aws ec2 describe-tags --region eu-central-1 \
    --filters "Name=tag:purpose,Values=findling-phase5"
aws ec2 describe-tags --region eu-central-1 \
    --filters "Name=tag:purpose,Values=findling-corpus-keep"
# Ein Tag-Treffer ist ein Hinweis und kein Urteil: jeder Treffer wird nach seiner
# Art zurueckgelesen, und nur was noch antwortet, zaehlt als Ueberbleibsel
```

---

## State of the Art: was sich seit dem letzten Lauf geaendert hat

| Alt (Stand 10.09.2026, der Zustand im Snapshot) | Neu (Stand 19.09.2026, der zu messende Zustand) | Folge fuer die Messung |
|---|---|---|
| Zulauf haengt am Systemcron, Leerlauf bis 12 Minuten je Scheibe | **Top-up-Route**: ein Container mit leerem Claim fuehrt die naechste Crawl-Scheibe selbst aus (Budget 20 s, Scheiben-Lock) | genau die Wirkung, die der Volllauf belegen soll |
| Keine Filter, keine Sortierung | Phase 13: Typgruppen, Zeitraum, Sortierung, Cursor | aendert an Durchsatz und Grundlast nichts, darf mitlaufen; eigene Messbloecke waeren eigene Rohdateien |
| Modell bleibt geladen, bis der Container endet | Phase 14: `FINDLING_EMBED_IDLE_RELEASE_SECONDS`, ab Werk **aus**, sechster Zustand `unloaded`, Degradationsnaht, Nachwaermen im Hintergrund | ermoeglicht A/B in einer Anfahrt (Pitfall 19 der Milestone-Recherche) |
| Fremdbestands-Vorpruefung ueber die OCS-Route, gedeckelt bei 26 | Bestandssonde im Containerprozess ueber `ranked_sides`, ungedeckelt, Rangsemantik gegen Schwelle 64 | Erfolgskriterium 4 wird ueberhaupt erst pruefbar |
| Lastwerkzeug zaehlt abgebrochene Aufrufe als beantwortet | `search_load.py` gefixt (`min_hits`, `hits_per_request`, `EmptyResultGroup`) | die neuen Stufenzahlen sind ehrlicher und duerfen schlechter aussehen |
| Kein Runbook, Erfahrung verstreut in drei Berichten | `docs/runbook-messbox.md`, 1102 Zeilen, 24 Kommandobloecke | Erstvollzug validiert es woertlich (D-10) |
| Versionsfenster bis NC 34 | stable35 entschieden am 16.09. (Zweig a, Beweislauf 35095805558) | beruehrt die Messung nicht, gehoert zu Phase 16 |

**Ueberholt und nicht mehr benutzen:** `98-sprachfaelle.sh` und `98b-sprachfaelle.sh` (beide
byteidentisch eingefroren als Beweisstuecke, Nachfolger ist `98c`); die OCS-Route als
Bestandsmass; der Digest von `:dev` als Identitaetsbeweis (Baumhash ist der Beweis, der
Digest die Notiz daneben).

---

## Environment Availability

Geprueft auf der Entwicklungsmaschine am 2026-09-19.

| Abhaengigkeit | Gebraucht fuer | Vorhanden | Version | Rueckfall |
|---|---|---|---|---|
| AWS CLI v2 | `aws_box.sh`, alle EC2-Aufrufe | ja | 2.36.39 | , |
| `gh` | Laufnummer des gruenen `integration.yml`-Laufs | ja | 2.92.0 | , |
| `python3` | Messskripte, `rss_digest.py` | ja | 3.13.1 | , |
| `uv` | Gates vor dem Commit | ja | 0.11.7 | , |
| `jq` (Entwicklungsmaschine) | Auswertung | ja | 1.8.1 | , |
| `jq` (Box) | `98c-sprachfaelle.sh`, sonst Rueckgabewert 18 | **unbekannt** | , | Vorbedingung 7 prueft es, sobald die Box steht; `apt-get install jq` kostet Sekunden |
| `ssh`, `scp` | alle Box-Handgriffe | ja | OpenSSH 10.3p1 | , |
| `dig` | Block 10, `dig +short loadtest.infranode.dev` | **nein** | , | `nslookup` (vorhanden unter `/c/WINDOWS/system32`) oder `curl --resolve` (Rueckfall 2 des Runbooks); die Runbook-Zeile bekommt einen Nachtrag |
| AWS-Anmeldung | alles | ja | `~/.findling-aws.env`, 126 Byte | , |
| Sicherung der Systemplatte | Block 9 | ja | 3.971.065 Byte, sha256 geprueft und identisch | keiner. Ohne sie fehlen die Passwortdateien beider Konten |
| `box.env` | `require_state` aller Unterbefehle | **nein** | , | Block 4 schreibt zwei Felder von Hand neu; das ist der vorgesehene Weg |
| Gruener `integration.yml`-Lauf | `CI_LAUF` | ja | **35462611738** (success, main, 2026-09-19T18:53:12Z) | vor der Anfahrt neu holen, damit die Nummer zum gemessenen Stand passt |
| Zugang zur DNS-Zone | Block 10 | **Owner** | , | `/etc/hosts`-Pin, `curl --resolve` |

**Fehlend ohne Rueckfall:** keines.
**Fehlend mit Rueckfall:** `dig` (nslookup oder `curl --resolve`), `box.env` (Block 4),
`jq` auf der Box (Installation, Sekunden).

---

## Security Domain

Diese Phase schreibt keinen Produktcode, erzeugt aber die groesste Geheimnis- und
Kostenoberflaeche des Milestones: Cloud-Anmeldung, SSH-Schluessel, zwei Kontopasswoerter,
eine oeffentlich erreichbare Nextcloud und ein oeffentliches Repositorium, in das die
Rohdaten wandern.

### Zutreffende ASVS-Kategorien

| Kategorie | Trifft zu | Standardkontrolle in dieser Phase |
|---|---|---|
| V2 Authentifizierung | ja | Passwoerter der Konten `admin` und `lasttest` ausschliesslich aus `~/work/.pw/`, Uebergabe ueber `--password-env` (Name, nie Wert) |
| V3 Sitzungsverwaltung | nein | keine neue Sitzungslogik |
| V4 Zugriffskontrolle | mittelbar | SSH ausschliesslich von genau einer Adresse mit Praefixlaenge 32; die drei offenen Regeln sind 80, 443 TCP und 443 UDP |
| V5 Eingabevalidierung | nein | kein neuer Eingabepfad |
| V6 Kryptographie | ja | Schluesselpaar wird neu erzeugt, der private Teil verlaesst die erzeugende Maschine nie und gehoert in keine Sicherung, die irgendwohin synchronisiert |
| V7 Fehlerbehandlung und Protokollierung | ja | Rohdaten werden committet; Adressen und Kennungen werden beim Uebernehmen durch Platzhalter ersetzt |
| V14 Konfiguration | ja | Anmeldung nur aus der Umgebung, nie als Argument (steht sonst in der Prozessliste und in der Shell-Historie); Zustandsdatei ausserhalb des Arbeitsbaums |

### Bedrohungsmuster dieser Anfahrt

| Muster | STRIDE | Gegenmassnahme |
|---|---|---|
| Geheimnis landet im oeffentlichen Repositorium (IP, Volume-Kennung, Kontokennung, Passwortdatei) | Information Disclosure | Geheimnisregel im Runbook-Kopf; genau ein Pfad ins Repositorium, ueber Abbau-Schritt 2 mit Platzhalterersetzung |
| Anmeldedaten in Prozessliste oder Shell-Historie | Information Disclosure | `aws_box.sh` liest sie ausschliesslich aus der Umgebung; ein Gate-Test haelt fest, dass je Name genau eine expandierende Zeile existiert |
| Passwort auf einer Kommandozeile eines Messskripts | Information Disclosure | `test_the_script_of_this_run_puts_no_password_on_a_command_line` |
| Offene Nextcloud im Internet waehrend 26 Stunden Volllauf | Elevation of Privilege | Nur 80, 443 offen; Instanz existiert nur fuer die Dauer der Anfahrt; Abbau ist Erfolgskriterium |
| Ressource laeuft nach dem Abbau unbemerkt weiter und kostet | Denial of Wallet | Rueckleseprobe je Ressourcenart, Tag-Sweep ueber **beide** Tagwerte, Kostenueberblick ueber alle freigeschalteten Regionen |
| Gerissener Deckel ohne Abbruchpunkt | Denial of Wallet | Owner-Freigabe mit Datum; Abbruchpfade in Abschnitt 5 und den Rueckgabewerten 15 bis 31 |
| Ein zweiter Docker-Dienstnutzer loescht das Messvolumen | Tampering | Zaehlung vor jedem `--rm-data` |

---

## Empfohlener Plan-Zuschnitt

Vorschlag, nicht bindend; der Planer schneidet nach `granularity: coarse`.

**Welle A, ohne Box-Zeit (parallelisierbar)**

1. Werkzeuge kopieren und das Laufverzeichnis komplettieren; Gate-Lage pruefen
   (`NARROW_SCOPE_DIRS` deckt das v12-Verzeichnis bereits ab).
2. Wiederaufwaerm-Werkzeug bauen (Rueckgabewerte 29, 30, 31; Seitencache-Befehl; vier
   Auspraegungen) plus boxlose Verweigerungstests.
3. MEM-02-Block bauen (Grundlast vor und nach dem Indexlauf).
4. Abbildwechsel-Block schreiben (Muster `92-wechsel.sh`) und als Runbook-Nachtrag
   einreihen.
5. `00-ablauf.md` auf neun Schritte fortschreiben, **mit vorher notierten Erwartungen**;
   Deckel-Rechenblatt neu rechnen; neun Vorbedingungen abarbeiten und protokollieren.

**Welle B, der Owner-Checkpoint**

6. Deckelfreigabe mit Datum. Blockierend. Ohne sie endet die Phase hier.

**Welle C, die Anfahrt (sequenziell, begleitet)**

7. Aufbau Bloecke 1 bis 13 plus Abbildwechsel, jede erwartete Ausgabe nachtragen.
8. Zustandspruefung und Nullstandsbeleg (Abbruchpfad).
9. Volllauf detached mit beiden Cron-Zweigen (der lange Block).
10. Laststufen mit je einem Verdikt; Sprachfaelle; Wiederaufwaerm-A/B; MEM-02-Block.
11. Endmessungen, Kostenzeilen, Abbau, Tag-Sweep, Kostenueberblick.

**Welle D, nach dem Abbau**

12. Bericht `docs/measurements/2026-09-v12-messung/README.md` mit dem Abschnitt "Was dieser
    Lauf nicht besser gemacht hat"; Runbook-Nachtraege; Pruefsummen-Waechter fuer die
    gefahrenen Fassungen; `docs/performance.md` fortschreiben; Audit der Phase.

---

## Assumptions Log

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---|---|---|
| A1 | Die Preissaetze von 0,0978 USD/h (m7g.large) und 0,005 USD/h (IPv4) gelten am Anfahrtstag noch; der Instanzsatz ist nur indirekt gegengeprueft (halber m7g.xlarge-Satz) | Deckel-Rechenblatt | Der Deckel ist in USD falsch. Wirkung klein: bei plus 10 Prozent sind es 5,61 statt 5,10 USD. Die Stundenzahl bleibt der harte Deckel |
| A2 | Der Abbildwechsel kostet rund 1 Stunde Box-Zeit | Deckel-Rechenblatt | Unterschaetzt; der 15-Prozent-Zuschlag deckt eine halbe Stunde Abweichung |
| A3 | Der MEM-02-Block laesst sich in 45 Minuten neben den anderen Messungen fahren | Deckel-Rechenblatt | Unterschaetzt, falls die Ruhezeit je Durchgang voll abgewartet werden muss |
| A4 | Die zwei Stunden fuer die vier A/B-Auspraegungen reichen beim Vorschlagswert 900 s | Deckel-Rechenblatt | Reisst; Gegenmittel ist eine kuerzere Ruhezeit, aber das ist eine Owner-Frage |
| A5 | Die lokale Registry im Snapshot traegt den Stand vom 10.09. und nicht den v1.2-Stand | Pitfall 1 | Falls doch aktuell, entfaellt der Abbildwechsel und der Deckel sinkt um eine Stunde. Pruefbar erst auf der Box, in Block 8 |
| A6 | Phase 15 misst im bestehenden Laufverzeichnis `2026-09-v12-messung` und legt kein neues an | Welle A | Bei einem neuen Verzeichnis muss `NARROW_SCOPE_DIRS` erweitert werden, sonst faellt der Gate-Test |
| A7 | `jq` liegt auf der frisch gebauten Box nicht vor | Environment Availability | Kostet Sekunden, kein Risiko; die Vorbedingung faengt es ab |
| A8 | Der Handaufbau dauert 2 h 30 min | Deckel-Rechenblatt | Uebernommen aus Annahme A8 der Phasenrecherche, nirgends gemessen; die Zeile verliert beim Rueckfluss als erste ihren Schaetzcharakter |

---

## Open Questions (RESOLVED)

> Aufloesung 19.09.2026, alle fuenf Fragen sind entschieden: Q1 (Abbild)
> per Vorentscheid D-04 in 15-CONTEXT.md, umgesetzt in 15-06. Q2
> (900-s-Beleg) als Erwartung E14 in 15-07, Checkpoint in 15-13. Q3
> (Filter/Sortier-Block) per Owner-Entscheid D-01, umgesetzt in 15-05.
> Q4 (Ausfuehrungsform) als begleitete Sitzung 15-09 bis 15-14. Q5
> (Snapshot) bewusst eskaliert als Frage B des Checkpoints 15-08.

1. **Welches Abbild misst die Box?**
   - Was wir wissen: Der Snapshot traegt die lokale Registry mit dem Abbild vom 10.09.; der
     Wirkungsbeleg braucht zwingend die Top-up-Route (seit 11.09.) und der A/B-Schritt den
     Schalter aus Phase 14.
   - Was unklar ist: Ob das Abbild ueber `ghcr.io/street1983nk/findling_backend:dev` gezogen
     oder in die lokale Registry der Box gespielt wird, und ob der PHP-Teil mitwandern muss
     (er muss, wegen der Filter aus Phase 13 und der sechsten Zustandszeile aus Phase 14).
   - Empfehlung: Block nach dem Muster `92-wechsel.sh` in Welle A schreiben, PHP-Haelfte
     zuerst, dann Registrierung, dann harte Grenze aus der cgroup; Baumhash als Beweis.

2. **Was wuerde den Vorschlagswert 900 s "belegen"?**
   - Was wir wissen: 900 s ist heute eine gekennzeichnete Schaetzung an zwei Stellen; die
     Phase-14-Abnahme verlangt "belegen oder korrigieren".
   - Was unklar ist: Eine Frist laesst sich in einer Anfahrt nicht belegen, nur ihre Folgen.
     Messbar sind die zurueckgegebenen MB und die Wiederaufwaermkosten; daraus ergibt sich
     eine Empfehlung, kein Beweis.
   - Empfehlung: Als Owner-Frage in die Deckelvorlage aufnehmen und das Kriterium vorab
     festlegen (z.B. "die Frist bleibt bei 900 s, wenn die Wiederaufwaermung unter X ms
     bleibt und die Rueckgabe ueber Y MB liegt").

3. **Bekommen Filter und Sortierung einen eigenen Messblock?**
   - Was wir wissen: Die ROADMAP nennt als weiche Abhaengigkeit "Phase 13 sollte stehen,
     damit die Sortierung auf grossem Bestand mitgeprueft wird"; die fuenf Erfolgskriterien
     verlangen es nicht, und die Messreihenfolge des Runbooks hat keinen Block dafuer.
   - Empfehlung: Als kleinen Zusatzblock neben Schritt 6 fuehren (eigene Rohdatei, eigene
     Zeile im Rechenblatt) oder ausdruecklich als "nicht gemessen" in den Bericht schreiben.
     Stillschweigen waere die schlechteste der drei Moeglichkeiten.

4. **Wer fuehrt die Anfahrt aus?**
   - Was wir wissen: Die Anmeldung liegt vor und Phase 12 hat lesende AWS-Aufrufe autonom
     gefahren. Der A-Record braucht den Owner, der Volllauf laeuft 26 Stunden.
   - Empfehlung: begleitete Sitzung, Block fuer Block, mit sofortiger Rohdatenablage; der
     Volllauf detached, seine Auswertung ein eigener Plan.

5. **Bleibt der Korpus-Snapshot nach dieser Anfahrt stehen?**
   - Was wir wissen: Er kostet 2,79 bis 2,99 USD je Monat und ist die Grundlage jeder
     weiteren Anfahrt; das Runbook fuehrt die Wiedervorlage ausdruecklich "nach v1.2".
   - Empfehlung: nicht in dieser Phase entscheiden, aber die Frage in den Bericht schreiben,
     damit sie in Phase 16 nicht verloren geht.

---

## Sources

### Primaer (HIGH, in dieser Sitzung am Original gelesen)

- `docs/runbook-messbox.md` (1102 Zeilen, vollstaendig) , Deckel-Rechenblatt, Vorbedingungen,
  Aufbaubloecke, Zustandspruefung, Vergleichbarkeitsbedingungen, Messreihenfolge, A/B-Schritt
  7.2, Abbau-Checkliste, Kostenfuehrung
- `docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md` , die fuenf Schritte, E1 bis
  E7, der Abbruchkatalog 15 bis 28
- `docs/audits/2026-09-phase-11/README.md:509-545, 806-880` , die vier regressiven
  Laststufen mit Zahlen, L-07 (DI-10-04), L-08 (DI-10-02 und DI-11-01)
- `.planning/milestones/v1.1-phases/10-.../deferred-items.md:135-165` , DI-10-04 im Wortlaut
- `docs/performance.md:154-158, 3609-3680, 4035-4075` , Top-up-Fix, Messgroesse von MEM-02,
  Bodensatz, `cURL error 28` vom 10.09., Kostenrechnung des ARM-Laufs
- `.planning/research/PITFALLS.md:325-456` , Pitfalls 15 bis 19
- `.planning/research/ARCHITECTURE.md`, Teil C , Bestand und Aenderungsbedarf der
  Messwerkzeuge, Byte-Identitaets-Regel, das fehlende Wiederaufwaerm-Werkzeug
- `.planning/phases/12-CONTEXT.md`, `12-VERIFICATION.md`, `12-03-SUMMARY.md` , D-01 bis
  D-11, Zustand der Werkzeuge, AWS-Anmeldung bestaetigt
- `.planning/phases/14-modell-entladung-im-leerlauf/14-12-SUMMARY.md` , die drei Auftraege an
  Phase 15, die duenne Marge, MEM-02 offen
- `scripts/ops/aws_box.sh:141-170, 252-280, 650-740` , gepinnte Saetze, `cmd_prices`,
  Kostenfelder
- `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/92-wechsel.sh` (Kopf) und
  `97-nebenlaeufigkeit.sh` (Kopf) , Abbildwechsel-Muster, Stufenreihe, Passwortregel
- `backend/tests/test_measurement_scripts.py:1040-1215` , Gate-Umfang, `NARROW_SCOPE_DIRS`,
  Pruefsummen-Waechter
- `backend/appinfo/info.xml:466-471` , Schalter, Wertebereich 60 bis 86400, Vorschlagswert 900

### In dieser Sitzung selbst gemessen (HIGH)

- sha256 von `home-ubuntu-work.tar.gz` gegen `07-snapshot-und-abbau.txt` Abschnitt 4:
  identisch (`fad3e7ce...3584a`, 3.971.065 Byte)
- Werkzeugstand der Entwicklungsmaschine: AWS CLI 2.36.39, gh 2.92.0, Python 3.13.1,
  uv 0.11.7, jq 1.8.1, OpenSSH 10.3p1, `dig` fehlt
- `gh run list --workflow=integration.yml --status success --limit 1` , Lauf 35462611738
- `gh pr list --state open` , leer, kein offener Dependabot-Vorschlag

### Sekundaer (MEDIUM, Websuche gegen offizielle Quelle abgeglichen)

- gp3 in eu-central-1: 0,0952 USD je GiB-Monat , https://www.aws.eu/ebs/pricing/
- m7g.xlarge in eu-central-1: 0,1955 USD/h (halber Satz ergibt 0,09775 fuer large) ,
  https://compute.doit.com/spot/eu-central-1/m7g.xlarge
- m7g.large Eckdaten (2 vCPU, 8 GiB) , https://instances.vantage.sh/aws/ec2/m7g.large

### Tertiaer (LOW, nicht weiter verfolgt)

- Keine. Alle Aussagen dieser Recherche stehen entweder im Repositorium oder sind oben als
  Annahme gefuehrt.

---

## Metadata

**Confidence im Einzelnen:**

- Inventar der offenen Messauftraege: **HIGH** , jeder Auftrag mit Datei und Zeile belegt
- Die fuenf Luecken: **HIGH** , negativ belegt durch gezielte Suche (kein Abbildblock, kein
  `drop_caches`, kein Skript mit den Rueckgabewerten 29 bis 31, drei statt neun Skripte im
  Laufverzeichnis, zwei fehlende Zeitposten)
- Deckel-Rechenblatt: **MEDIUM** , die Rechnung ist nachvollzogen, zwei der Posten sind neu
  geschaetzt und die Preissaetze nur indirekt gegengeprueft
- Ausfuehrungsform und Reihenfolge: **HIGH** fuer das Runbook, **MEDIUM** fuer die
  Auflosung des Aufwaermkonflikts zwischen Schritt 3, 6 und 8 (eine Empfehlung, kein Zitat)
- Environment Availability: **HIGH** , in dieser Sitzung gemessen

**Recherchedatum:** 2026-09-19
**Gueltig bis:** 2026-10-19 fuer den Bestand; die Preissaetze gehoeren am Anfahrtstag noch
einmal gegen `aws_box.sh prices` gelesen, weil `describe-instance-types` kostenlos ist und
die Zahl dann aus der Quelle statt aus dieser Datei stammt.
