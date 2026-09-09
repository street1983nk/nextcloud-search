# Phase 10: Vergleichsmessung auf der AWS-Box , Recherche

**Recherchiert:** 2026-09-09
**Domäne:** Reproduzierbare Speicher- und Latenzmessung auf gemieteter ARM-Hardware, Vergleich gegen eine bestehende Baseline
**Konfidenz:** HIGH für die Bestandsaufnahme im Repo, MEDIUM für Laufzeit und Kosten, LOW für den Zustand der Box (seit 07.09.2026 nicht angefasst, und diese Recherche hat ihn bewusst nicht angefasst)

---

## Summary

Diese Phase baut nichts Neues. Sie fährt einen Lauf auf einer Maschine, die seit dem 07.09.2026 angehalten ist, und stellt seine Zahlen neben die des v1.0-Laufs. Das Repo ist dafür ungewöhnlich gut vorbereitet: es gibt zwei vollständige Vorläufer-Messberichte mit Skripten und Rohdaten (`2026-09-05-semantiklauf-m7g` als v1.0-Baseline, `2026-09-nachmessung-m7g` als bereits gefahrener Zeile-für-Zeile-Vergleich gegen diese Baseline), ein gepflegtes Box-Werkzeug mit sieben Unterbefehlen und eingebauter Kostenrechnung (`scripts/ops/aws_box.sh`), ein box-unabhängiges Lastwerkzeug (`scripts/ops/search_load.py`) und einen Sampler samt Auswerter (`rss_sampler.sh`, `rss_digest.py`). Die Form des Berichts ist damit nicht zu erfinden, sondern abzuschreiben. [VERIFIED: Dateien im Repo gelesen]

Der eine harte Befund, der die ganze Planung bestimmt: **der Index auf dem Datenträger existiert nicht mehr.** Der arm64-Installationslauf vom 07.09. hat über `app_api:app:unregister --rm-data` das Volumen `nc_app_findling_backend_data` der Messinstanz gelöscht, mitsamt `state.db`, `vectors.db` und dem 785 MB grossen Tantivy-Index. Der Korpus (50.000 Dateien, 20 GB) hat überlebt, weil er im Datenspeicher von Nextcloud liegt und nicht im ExApp-Volumen. `occ findling:index --restart` ist auf der Box bereits eingestellt, das heisst: **der nächste Start der Box zieht rund 19 Stunden Neuaufbau nach sich, ob man ihn will oder nicht.** [VERIFIED: `docs/measurements/2026-09-nachmessung-m7g/README.md` Abschnitt 12a, `docs/performance.md` Zeile 3791 bis 3799, `~/.findling-loadtest/box.env`]

Daraus folgt die zentrale Empfehlung, und sie dreht den Zwang in einen Vorteil: der Neuaufbau ist kein Rüstverlust, er **ist** die Messung. Ein Volllauf mit Semantik über 51.961 Dokumente ist genau das, was der v1.0-Bericht gemessen hat, und nur er liefert die Gesamtspitze, die Laufzeit, `memory.events` über den ganzen Lauf und einen p95 über den vollen Vektorbestand als vergleichbare Grössen. Eine kürzere Variante gegen den Bestand ist nicht möglich, weil es keinen Bestand mehr gibt.

**Primäre Empfehlung:** Einen Lauf planen, der die Form von `2026-09-05-semantiklauf-m7g` wiederholt und die Vergleichsspalten von `2026-09-nachmessung-m7g` benutzt: Anfahrt und Wiederanlaufpfad, Baumhash-Beweis mit Rohdatei, Grundlast-Aufschlüsselung (das ist die MESS-01-Kernzahl, denn dort schlägt der faule Bau aus Plan 07-03 zu), dann der 19-Stunden-Volllauf unter Sampler und Wächter, danach die Nebenläufigkeitsreihe, die Kaltstartmessung für DI-07-02, die Rundenzählung für DI-07-03, die zehn Sprachfälle gegen einen eigenen Nutzer und die Seitenroute aus Phase 9. Erwartete Box-Laufzeit 22 bis 26 Stunden, erwartete Kosten 2,55 bis 3,01 USD netto. Owner-Freigabe für Anfahrt, Dauer und Kostendeckel vor dem ersten `aws_box.sh start`.

---

## Project Constraints (aus CLAUDE.md)

Direktiven mit derselben Verbindlichkeit wie gesperrte Entscheidungen. [CITED: `CLAUDE.md`]

| Direktive | Was das für Phase 10 heisst |
|---|---|
| **Owner-Regel 15.08.2026:** Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde ab MEDIUM vor Phasen-Abschluss fixen | Die Phase ist ohne die drei Audits nicht abgeschlossen. Bei einer Messphase sind die Audit-Objekte die neuen Skripte und der Bericht, nicht neuer Produktionscode |
| **Owner-Regel 07.09.2026 (Kurztext-Regel):** nach aussen sichtbarer Text ist eine kurze Faktenliste, höchstens eine Zahl im Text | Wenn Phase 10 Zahlen in README oder Store-Text zieht, gilt die Regel. Der Messbericht selbst ist kein nach aussen sichtbarer Text und darf lang sein |
| **Sicherheitsgrenze unverändert:** SQLite-ACL-Vorfilter im Container, finaler PHP-Recheck ist die Grenze | Kein Messweg darf die Grenze umgehen. Die Sprachfälle und die Lastreihe laufen über die OCS-Route beziehungsweise die Seitenroute, also über den Recheck |
| **Keine Em-Dashes** (U+2014, U+2013) | Gilt für Bericht, Skripte, Kommentare. `backend/tests/test_ops_scripts.py::test_the_script_carries_neither_a_dash_nor_a_carriage_return` macht es für `scripts/ops` rot |
| **Echte Umlaute nur in deutscher Prosa, nie in Code**; Code und Kommentare englisch | Messskripte englisch kommentiert, Bericht deutsch mit echten Umlauten. So sind die Vorläufer gebaut |
| **Qualitätsgates lokal grün vor Commit:** ruff Vollregelsatz, `ruff format --check`, pyright basic, vulture, über das **ganze** Repo | Jedes neue Python-Messskript unter `docs/measurements/.../skripte/` und jede Änderung an `scripts/ops/` muss durch. `ruff check .` und `ruff format --check .` über das ganze Repo, nicht nur über die geänderten Dateien |
| **Kein Telemetrie-Phoning, keine Inhalte verlassen den Server** | Messskripte senden nichts. Die Meldekette (ntfy) ist die einzige Ausnahme und sendet nur Zustandswörter, keine Inhalte |
| **RAM-Budget-Tabelle in CLAUDE.md** kennt keinen Posten "Tokenizer und Splitter" | Die Feinmessung hat ihn mit 544 MB gemessen, grösser als das Modell. Ob die Tabelle nachgezogen wird, **entscheidet der Owner**; die Feinmessung hat CLAUDE.md ausdrücklich nicht angefasst. Phase 10 hat die Zahl auf nativem ARM und damit den besseren Anlass zu fragen |
| **GSD-Workflow-Zwang:** keine direkten Repo-Änderungen aussserhalb eines GSD-Kommandos | Gilt für die Ausführung, nicht für diese Recherche |

---

## Phase Requirements

| ID | Beschreibung (aus REQUIREMENTS.md) | Welche Rechercheergebnisse die Umsetzung tragen |
|---|---|---|
| **MESS-01** | Ein Vergleichslauf auf der AWS-Box (vorhandener v1.0-Korpus, 51.961 Docs) belegt die RSS-Ersparnis der gemeinsamen Engine gegen die v1.0-Baseline | Die Baseline-Zahlen stehen vollständig in der Vergleichsmatrix unten. Der Beleg-Weg ist `63-grundlast.sh` plus `52-woher-die-grundlast.py` (unverändert wiederverwendbar) und `01-grundlast-fein.py`. Die Ersparnis fällt **in der Grundlast** an, nicht an der Spitze, weil Plan 07-03 den Bau von Tokenizer und Splitter faul gemacht hat (amd64 gemessen: 575,0 MB) |
| **MESS-02** | Keine Regression: p95-Suchlatenz und die 10 deutschen CI-Sprachfälle bleiben im v1.0-Rahmen | p95: `scripts/ops/search_load.py` mit den fünf Nebenläufigkeitsstufen, Baseline 481,6 / 1.009,4 / 1.915,0 / 3.045,4 / 3.782,7 ms. Sprachfälle: der CI-Schritt "The ten German language cases, as the owner" in `integration.yml` ab Zeile 1427, gegen einen **eigenen** Nutzer mit `testdata/corpus` (Begründung unter Pitfall 3) |
| **MESS-03** | Der Messbericht liegt in docs/measurements mit identischer Struktur wie der v1.0-Bericht | Der v1.0-Bericht ist `docs/measurements/2026-09-05-semantiklauf-m7g/README.md`. Die bewährte Vergleichsform ist `2026-09-nachmessung-m7g/README.md` (drei Spalten: Posten, Baseline, dieser Lauf, Differenz). Die Abschnittsfolge steht unten als Vorlage |

---

## Architectural Responsibility Map

| Fähigkeit | Primäre Ebene | Sekundäre Ebene | Begründung |
|---|---|---|---|
| Instanz an- und abfahren, Kosten rechnen, SSH-Regel nachziehen | Lokales Werkzeug (`scripts/ops/aws_box.sh`) gegen AWS-API | , | Die Kostenrechnung und die Zustandsdatei leben im Werkzeug; eine Anfahrt von Hand geht an beidem vorbei (Lehre aus 06.1-18) |
| Speicherzahlen erheben | Box, cgroup-Dateien unter `/sys/fs/cgroup/.../memory.*` | , | Niemals der Docker-Klient. `rss_sampler.sh` liest die cgroup selbst, und ein Test hält die zwei Wörter des Klienten aus dem Skript heraus |
| Indexaufbau, OCR, Einbettung | ExApp-Container auf der Box | Nextcloud-PHP-Hälfte (Crawl, Übergabe) | Der Poller im Container zieht die Arbeit; die PHP-Hälfte entscheidet, was übergeben wird (`findling:index --restart`) |
| Suchlatenz über den Nutzerweg | Nextcloud-PHP (OCS-Route, Seitenroute) | ExApp-Container (`/search`, `/snippets`) | Neun Zehntel der Zeit liegen in PHP (Seitenbudget-Bericht 5.2). Eine Messung direkt gegen den Container beantwortet eine andere Frage |
| Die zehn Sprachfälle | Nextcloud-PHP über OCS, als angemeldeter Nutzer | ExApp-Container | Die Fälle sind Aussagen über den Nutzerweg samt ACL-Recheck, nicht über den Container |
| Beweis "Abbild gleich Arbeitsbaum" | Lokaler Arbeitsbaum **und** Abbild im Container | ghcr.io-Registry (Digest) | Zwei Baumhashes über dieselben Dateien plus der Digest des Manifests. Der Digest allein beweist nichts über den Arbeitsbaum, der Baumhash allein nichts über das, was ausgeliefert wird |
| Die amd64-Entsprechungen und die native arm64-Feinmessung | GitHub-Runner (`integration.yml`, `measure.yml` auf `ubuntu-24.04-arm`) | , | Kostet keine Box-Zeit. `measure.yml` läuft per `workflow_dispatch` nativ auf arm64 und schliesst DI-07-04, ohne dass die Box dafür hochfährt |

---

## Bestandsaufnahme: was schon existiert und wortgleich wiederverwendbar ist

### Die beiden Vorläufer-Messberichte

| Bericht | Rolle für Phase 10 | Umfang |
|---|---|---|
| `docs/measurements/2026-09-05-semantiklauf-m7g/` | **Die v1.0-Baseline.** Volllauf mit Semantik, 51.961 Dokumente, 18 h 56 min, anon-Spitze 1.837,8 MB. Der Bericht, dessen Struktur Kriterium 3 verlangt | README 25,5 KB, 16 Skripte, `semantiklauf.csv` (13.983 Aufnahmen), `statusseite.jsonl` |
| `docs/measurements/2026-09-nachmessung-m7g/` | **Die Form des Vergleichs.** Kürzerer Lauf vom 07.09. gegen denselben Bestand, der jede Zahl neben ihre Entsprechung aus dem Semantiklauf stellt, einschliesslich der drei, die schlechter geworden sind (Abschnitt 14) | README 33,4 KB, 13 Skripte, 27 Rohdateien |
| `docs/measurements/2026-09-grundlast-fein/` | Die Zerlegung der Grundlast in fünf benannte Posten und die Nachmessung des faulen Baus (amd64: 575,6 MB auf 0,6 MB). Liefert die **Erwartung**, gegen die Phase 10 auf nativem ARM misst | README 13 KB, 2 Skripte, 3 Rohdateien |
| `docs/measurements/2026-09-seitenbudget/` | Die Zahlen der Ergebnisseite aus Phase 9, gemessen auf einer amd64-Entwicklungsinstanz **ohne** `vectors.db`. Abschnitt 6.3 ist Pflichtlektüre vor jeder Übernahme | README 16 KB, 12 Rohdateien |
| `docs/measurements/2026-09-04-volllauf-m7g/` | Die Baseline **vor** der Semantik (Plan 05-21): 12 h 49 min, anon-Spitze 422,2 MB, Grundlast 58,7 MB. Die dritte Vergleichsspalte, wenn man wissen will, was die Semantik insgesamt kostet | README 7 KB, `volllauf.csv` |

### Skripte, die ohne Änderung wiederverwendbar sind

| Datei | Was sie tut | Zustand |
|---|---|---|
| `scripts/ops/aws_box.sh` | Sieben Unterbefehle: `prices create volume status stop start destroy`. `start` fährt an, liest die neue Adresse, zieht die SSH-Regel der Security Group auf die aktuelle Owner-Adresse (revoke vor authorize) und **nennt die drei bis fünf Handgriffe, die ein Start nicht selbst erledigt**. `stop` schreibt Laufzeit und Kosten in `~/.findling-loadtest/box.env` | Gepflegt, gegated durch `backend/tests/test_ops_scripts.py` (14 Zusicherungen allein für das AWS-Werkzeug) |
| `scripts/ops/rss_sampler.sh` | Eine CSV je Container: Zeitstempel, anon, file, slab, current, peak, plus Schlusszeile mit höchstem anon, `memory.events` und `OOMKilled`. Liest die cgroup, nie den Klienten | Unverändert benutzbar. Aufruf: `rss_sampler.sh <container> 5 rss.csv` |
| `scripts/ops/rss_digest.py` | Summe **je Zeitpunkt**, dann deren Maximum, dazu die Summe der Einzelmaxima als obere Schranke daneben. Optionale Phasengrenzen als ISO-Argumente | Unverändert benutzbar |
| `scripts/ops/search_load.py` | Nebenläufige Suchlast über die OCS-Route, p50/p95/max, dazu anon **und** `memory.current` vor, während und nach der Last. Adresse, Konto und Container sind Argumente, nichts aussser der Standardbibliothek importiert. `--concurrency --rounds --limit --json` | Unverändert benutzbar. Modulkopf trägt die Baseline-Reihe vom 07.09. bereits als Text |
| `2026-09-nachmessung-m7g/skripte/60-bestand.sh` | Der Zustand nach dem Maschinenstart, `memory.events` **vor** jedem Eingriff, das Volumen, die Marken in `state.db` | Wortgleich wiederverwendbar; die DI-05-36-Hälfte darin ist erledigt und kann entfallen |
| `.../skripte/61-wechsel.sh` | Abbild aus ghcr ziehen, Digest und Architektur festhalten, Baumhash im Abbild, Modell- und Tesseract-Bestand, `unregister` **ohne** `--rm-data`, `register` gegen `harp_aio`, harte Grenze neu setzen und **aus der cgroup** zurücklesen | Wiederverwendbar mit einer Korrektur, siehe Pitfall 1 |
| `.../skripte/63-grundlast.sh` | Grundlast in drei Teilen, benutzt die beiden Hilfsskripte des Semantiklaufs unverändert | Wortgleich wiederverwendbar |
| `.../skripte/64-spitze.sh` | Die erste semantische Suche als **Ereignis**: lesen, genau eine Suche gegen einen Container, der noch nie eine gesehen hat, wieder lesen. Danach die Nebenläufigkeitsstufen mit Sampler | Wortgleich wiederverwendbar. Das ist auch der Messweg für DI-07-02 |
| `.../skripte/67-nebenlaeufigkeit.sh` | Die belastbare Reihe über fünf Stufen, 410 Anfragen | Wortgleich wiederverwendbar |
| `.../skripte/71-ocrphase.sh` | OCR-Phase an einer frischen Charge über WebDAV, also auf dem Weg, den ein Nutzer geht | Wiederverwendbar, in Phase 10 aber wahrscheinlich unnötig, weil der Volllauf die OCR-Phase über den ganzen Korpus fährt |
| `2026-09-05-semantiklauf-m7g/skripte/41-neuaufsatz.sh` | Beide Hälften auf null: `findling:purge --now`, `unregister --rm-data`, `register --wait-finish`, harte Grenze | Wiederverwendbar. Achtung: `--rm-data` ist hier **richtig**, weil ein leeres Volumen gewollt ist. Das ist derselbe Schalter, der am 07.09. den Schaden angerichtet hat, nur mit Absicht |
| `.../skripte/42-semantiklauf.sh`, `42b-wachter.sh`, `42c-lesen.py`, `42d-bestand.py` | Der abgesetzte Volllauf, der Wächter (Übergang erste auf zweite Spur, Ende beider Spuren, OOM-Beweis vor jedem Eingriff), der Leser der Statusseite, die Bestandsaufnahme | Wiederverwendbar. `42c-lesen.py` ist die **korrigierte** Fassung (liest `indexed`/`embedded` unter `backend`) |
| `.../skripte/43-ntfy-watch.sh` | Meldekette mit protokolliertem HTTP-Code je Versuch | Wiederverwendbar, aber siehe Pitfall 6 |
| `.../skripte/44-korpus-pruefsumme.py` | sha256 über die sortierten Zeilen `name,groesse,sha256` des Korpus, gegen die Regel des Generators | **Kritisch und wortgleich wiederverwendbar.** Das ist der Beweis, dass es noch dieselben 20 GB sind. Vergleichswert: die ARM-Zeile `bcbef9b2cb067c2200df2a4a2e89408f690710983117d4e78328024046098a72` |
| `.../skripte/49-modellgrundlast.sh`, `49b-gewichte.py`, `50-grundlinie-woher.sh`, `50b-prozesse.py`, `51-ab-grundlinie.sh`, `52-woher-die-grundlast.py` | Die Grundlast-Aufschlüsselung Schritt für Schritt | Wortgleich wiederverwendbar. `52-woher-die-grundlast.py` ist die Quelle, aus der `2026-09-grundlast-fein/skripte/01-grundlast-fein.py` die Schritte 00 bis 10 und 13 bis 15 wortgleich übernommen hat |
| `2026-09-grundlast-fein/skripte/01-grundlast-fein.py` | Die feine Fassung mit den fünf einzeln benannten Kandidaten und Schritt 16 | Wiederverwendbar. Die native arm64-Rohdatei fehlt noch (DI-07-04) und entsteht ohne Box über `measure.yml` |
| `2026-09-nachmessung-m7g/skripte/66-generator-endungen.py`, `68-bestand-endungen.py` | Der Endungsvergleich, Hälfte eins aus dem Samen gerechnet, Hälfte zwei über `state.db` | Wiederverwendbar. QUAL-03 ist geschlossen, aber der Vergleich ist die billigste Gegenprobe, dass der neu aufgebaute Index derselbe Bestand ist |

### Der Weg, wie beide Hälften auf die Box kommen

| Hälfte | Weg | Beleg |
|---|---|---|
| Container (ExApp) | Aus ghcr ziehen, **nicht** auf der Box bauen. `<image-tag>` in einer Kopie von `backend/appinfo/info.xml` **aussserhalb** des Arbeitsbaums auf `dev` setzen (`sed`), `occ app_api:app:register findling_backend harp_aio --info-xml /tmp/info-box.xml --wait-finish`. `git status --porcelain backend/appinfo/info.xml` muss danach leer sein, das ist eine Abnahmebedingung | `docs/performance.md` Zeilen 872 bis 899, `61-wechsel.sh` |
| PHP-Begleit-App | `docker cp php nextcloud-aio-nextcloud:/var/www/html/custom_apps/findling`, dann `chown -R 33:33`, dann `occ app:enable findling`. Das Verzeichnis muss `findling` heissen, sonst findet der Klassenlader nichts und der Suchanbieter bleibt **ohne Fehlermeldung** unsichtbar | `docs/performance.md` Zeilen 927 bis 944 |

### Der Stand, der gemessen wird, und dass er heute schon im Abbild liegt

| Grösse | Wert | Beleg |
|---|---|---|
| HEAD | `888e239a44907d203a044bad81c6d28fc0e07481`, `main` gleich `origin/main`, Arbeitsbaum clean | `git status -sb`, `git rev-list --left-right --count` gleich `0 0` |
| Letzter Commit, der `backend/` berührt | `0175b56` (`feat(09-08)`) | `git log -- backend/` |
| Letzter Lauf von `docker.yml` | `2c1b741`, 2026-09-09T05:50:26Z, **success** | `gh run list --workflow=docker.yml` |
| `git diff 2c1b741 HEAD -- backend/` | **leer** | selbst gefahren |
| `git diff 2c1b741 HEAD -- php/` | **leer** | selbst gefahren |
| Folgerung | `ghcr.io/street1983nk/findling_backend:dev` trägt heute genau den Backend-Stand von HEAD. **Ein Bau auf der Box ist nicht nötig**, und die Abweichung vom Plan, die die Nachmessung begründen musste, braucht Phase 10 gar nicht zu begründen | , |
| Baumhash `backend/src/findling` im Arbeitsbaum (Rezept: sha256 über sortierte relative Pfade plus sha256 des Inhalts mit CRLF nach LF, über `**/*.py`) | **54 Dateien, `6c47cd219c430bccc9d5d57b1de1d2ff9f8672fa4f42b1160d0a31efb9367476`** | selbst nachgerechnet nach dem Rezept aus `40-abbild.sh` |
| Baumhash `php` (Rezept: dasselbe über `**/*.php`) | **58 Dateien, `26b55908b12f8139b86d8c8a7c391457c550b2584fb8d639a3957e8b6feb91ae`** | selbst nachgerechnet |
| Zum Vergleich: Nachmessung 07.09. | backend 53 Dateien / `278fab52...`, php 47 Dateien / `c203da57...` | Nachmessung Abschnitt 1 |
| Letzter Lauf von `integration.yml` | `2c1b741`, success. Der Schritt "The ten German language cases, as the owner" ist damit gegen den gemessenen Baum grün | `gh run list --workflow=integration.yml` |
| `<version>` beider Hälften | `1.0.3`, `<image-tag>1.0.3</image-tag>` | `backend/appinfo/info.xml:136,230`, `php/appinfo/info.xml:113` |

**Wichtige Folgerung aus der letzten Zeile:** `info.xml` zeigt auf das **freigegebene** 1.0.3-Abbild, nicht auf den zu messenden Stand. Der Tausch auf `dev` in einer Kopie aussserhalb des Arbeitsbaums ist damit Pflicht und nicht Bequemlichkeit. Und weil `dev` ein wandernder Zeiger ist, muss der Plan zu Beginn des Laufs den **Digest** festhalten und ihn im Bericht nennen; Kriterium 1 hängt daran.

---

## Der v1.0-Bericht, dessen Struktur zu spiegeln ist

Kriterium 3 nennt "die Struktur des v1.0-Berichts". Die Zuordnung ist eindeutig, weil die Nachmessung sie selbst schon vorgenommen hat: sie nennt den Semantiklauf durchgehend "06-11" und schreibt in ihrem zweiten Absatz, sie wiederhole "die Form des Semantiklaufs, damit die Zahlen vergleichbar sind statt nur nebeneinander zu stehen".

**Der v1.0-Bericht ist `docs/measurements/2026-09-05-semantiklauf-m7g/README.md`.**
**Die bewährte Vergleichsform ist `docs/measurements/2026-09-nachmessung-m7g/README.md`.**

Empfohlene Abschnittsfolge für den Phase-10-Bericht, gebildet aus der Schnittmenge beider und den Zusatzfragen dieser Phase:

| Nr | Abschnitt | Entspricht |
|---|---|---|
| 1 | Die Umgebung, und der Beweis des gemessenen Standes | Nachmessung 1, Semantiklauf "Die Umgebung" plus "Welcher Stand gemessen wird" |
| 2 | Der Korpus, und dass es noch dieselben Bytes sind | Semantiklauf "Der Korpus" |
| 3 | Der Wiederaufsatz: warum beide Hälften auf null mussten | Semantiklauf "Der Neuaufsatz" |
| 4 | Die Kernaussage, in der Form aus D-H2 | Nachmessung 2 |
| 5 | Die Grundlast, aufgeschlüsselt, neben der aus 06-11 und der Nachmessung | Nachmessung 3, Feinmessung 2. **Hier liegt MESS-01** |
| 6 | Die anon-Spitze, getrennt nach Phase, mit dem Zeitpunkt | Nachmessung 4, Semantiklauf "memory.events und die Spitzen" |
| 7 | Laufzeit beider Spuren, neben 06-11 und 05-21 | Semantiklauf "Beide Spuren sind durch" |
| 8 | Die Suchlast und die Nebenläufigkeitszusage | Nachmessung 5. **Hier liegt die p95-Hälfte von MESS-02** |
| 9 | Die erste Suche nach einem Containerstart, unter Nebenläufigkeit | neu, schliesst DI-07-02 |
| 10 | Wie oft der Rechteabgleich mehr als eine Runde dreht | neu, schliesst DI-07-03 |
| 11 | Die Ergebnisseite auf der Zielhardware, gegen `2026-09-seitenbudget` | neu, Phase 9 war nie auf der Box |
| 12 | Die zehn deutschen Sprachfälle, auf der Box | neu. **Hier liegt die zweite Hälfte von MESS-02** |
| 13 | `memory.events`, vollständig, an jeder Ablesestelle | Nachmessung 6 |
| 14 | Byte je Dokument, gemessen gegen gerechnet | Semantiklauf "Byte je Dokument" |
| 15 | Verdikte und der Endungsvergleich als Gegenprobe | Nachmessung 7 |
| 16 | Was nicht abgedeckt ist | Nachmessung 11 |
| 17 | Kosten und Verbleib der Box | Nachmessung 12. **Hier liegt Kriterium 4** |
| 18 | Die Skripte und die Rohdaten | Nachmessung 13, Semantiklauf "Die Skripte" |
| 19 | **Was dieser Lauf nicht besser gemacht hat** | Nachmessung 14. **Pflicht**, Kriterium 2 verlangt ausdrücklich, dass jede Verschlechterung benannt ist statt weggelassen |

Zusätzlich, aussserhalb von `docs/measurements`: `docs/performance.md` trägt eine Tabelle "Stand dieses Berichts" (Zeile 111) mit einer Zeile je Messung, und einen Abschnitt je Lauf. Zeile 3509 sagt wörtlich: "Der Vergleich Zeile für Zeile gegen die v1.0-Grundlinie, mit einem p95 über den vollen Bestand, gehört Phase 10." Der Plan muss diese Stellen nachziehen, sonst widerspricht das Projektdokument seinem eigenen Zeiger.

---

## Die Vergleichsmatrix: jede Baseline-Zahl, die eine Entsprechung braucht

Alle Werte [VERIFIED: aus den genannten Berichten im Repo gelesen]. Die Spalte "Erwartung v1.1" ist eine **Erwartung** und ausdrücklich keine Messung; sie steht hier, damit der Plan Abbruch- und Plausibilitätsbedingungen formulieren kann.

### Grundlast (Container gestartet, bewaffnet, noch keine Suche)

| Posten | 06-11 (v1.0) | Nachmessung 07.09. | Erwartung v1.1 | Warum |
|---|---|---|---|---|
| anon im Leerlauf, Modell nie geladen | **691,8 MB** | **693,4 MB** | **rund 118 bis 150 MB** | Plan 07-03 hat den Bau von Tokenizer und Splitter faul gemacht. Auf amd64 fiel Station "zweite Spur verdrahtet" von 644,7 auf 69,9 MB, gemessene Ersparnis 575,0 MB |
| dasselbe nach einem Maschinenneustart | nicht getrennt | 687,9 MB | , | , |
| Tokenizer gelesen | +268,8 MB | +269,4 MB | fällt erst an der ersten Einbettungszeile an | `_build_the_cutter` statt `_wire_the_second_track` |
| Chunker gebaut und gefahren | +272,8 MB | +274,3 MB | dito | , |
| Gewichte bei der ersten Einbettung | +397,1 MB | +391,9 MB | unverändert | Die Gewichte waren schon in v1.0 faul |
| Aktivierungen einer langen Einbettung | nicht getrennt | +26,4 MB | unverändert | , |
| deutscher Automat, 276.496 Einträge | , | +42,1 MB | unverändert | `_CACHED_GERMAN` war schon in v1.0 prozessweit |
| Wortliste gelesen | , | +21,9 MB | unverändert | , |
| Poller importiert | , | +41,2 MB | unverändert | , |
| Summe Tokenizer plus Splitter, fein zerlegt | , | 543,7 MB grob | amd64 544,3 MB, arm64 emuliert 550,1 MB | Feinmessung Abschnitt 4 |

### Spitzen und Schadenszähler

| Posten | 06-11 (v1.0) | Nachmessung | Erwartung v1.1 |
|---|---|---|---|
| Höchster anon-Wert des ganzen Laufs | **1.837,8 MB** um 05:34:05Z | **1.812,7 MB** um 05:55:53Z | offen. Die Spitze gehört inzwischen der OCR-Phase, und die ändert sich durch die Phasen 7 bis 9 nicht |
| Phase der ersten semantischen Suche | 1.837,8 MB | 1.125,2 MB (minus 712,6) | rund 1.125 MB minus dem, was der faule Bau in dieser Phase noch nicht bezahlt hat |
| anon vor / nach der ersten Suche | , | 694,3 / 1.116,6 MB (plus 422,3) | Vorherwert deutlich niedriger erwartet |
| Phase mit OCR | 1.562,7 MB | 1.812,7 MB (plus 250,0) | rund 1.812 MB |
| `memory.peak` (mit Dateicache) | 2.147.741.696 Byte | 1.990,3 MB | , |
| `memory.current`-Spitze | 2.048,0 MB (an der harten Grenze) | 1.219,8 MB in der Lastreihe | , |
| harte Grenze | `memory.max = 2147483648` (2,0 GiB) | dieselbe | dieselbe |
| `memory.events`: low, high | 0, 0 | 0, 0 | 0, 0 |
| **`max`** | **2.796** | **0** | 0 erwartet, und diese Null ist der eigentliche Gewinn |
| `oom`, `oom_kill`, `oom_group_kill` | 0, 0, 0 | 0, 0, 0 | 0, 0, 0. **Das ist die Store-Aussage in der Form D-H2** |
| `sock_throttled` | 3.044 | 0 | , |
| `OOMKilled`, `RestartCount` | false, 0 | false, 0 | false, 0 |

### Laufzeit und Durchsatz

| Posten | 05-21 (ohne Semantik) | 06-11 (v1.0) | Erwartung v1.1 |
|---|---|---|---|
| erste Spur (Volltext plus OCR, Einbettung nebenher) | 12 h 49 min | **18 h 04 min** | rund 18 h, unverändert. Der faule Bau verschiebt, er spart nicht |
| beide Spuren bis zum letzten Vektor | , | **18 h 56 min** | rund 19 h |
| Einbettung neben der OCR | , | rund 43 Dok/min | unverändert |
| Einbettung allein, nach der ersten Spur | , | rund 170 Dok/min | unverändert |

### Suchlatenz

| Messpunkt | Baseline | Quelle |
|---|---|---|
| p95 sequenziell, während des Nachlaufs (Vorrat 4.775) | **1.129,0 ms** | 06-11 |
| p95 sequenziell, voller Vektorbestand | **524,0 ms** | 06-11 |
| p95, Nebenläufigkeit 1 | **481,6 ms** | Nachmessung |
| p95, Nebenläufigkeit 4 | **1.009,4 ms** | Nachmessung |
| p95, Nebenläufigkeit 8 | **1.915,0 ms**, 76,6 Prozent des Budgets, **die Zusage** | Nachmessung |
| p95, Nebenläufigkeit 12 | 3.045,4 ms, Budget gerissen | Nachmessung |
| p95, Nebenläufigkeit 16 | 3.782,7 ms, Budget gerissen | Nachmessung |
| Budget der Ergebnisgruppe | 2.500 ms (`Provider::BUDGET_NANOSECONDS`) | `php/lib/Search/Provider.php:57` |
| Deckel je Containeraufruf | 1,5 s (`REQUEST_TIMEOUT_SECONDS`) | `php/lib/Service/ExAppService.php:89` |
| Kaltstart der ersten Suche, arm64, über den OCS-Weg | **1.332,1 ms**, Marge zum 1,5-s-Deckel 167,9 ms | 07-01, `docs/performance.md:3262` |
| dieselbe Grösse auf amd64 | 1.299 ms (sqlite) und 1.392 ms (mysql), Lauf 34221154596 | `docs/performance.md`, "Die amd64-Zahl" |
| Deckel der Seitenroute | `PAGE_REQUEST_TIMEOUT_SECONDS` 1,5 s, `PAGE_BUDGET_SECONDS` 3,0 s | Seitenbudget 6.1 und 6.2 |
| Seitenroute p95, Sitzung (amd64-Dev-Instanz, ohne `vectors.db`) | **0,122 s** | Seitenbudget 6.3 |
| Seitenroute p95, Basic-Auth (kostet 0,318 s Passwortprüfung extra) | 0,445 s | Seitenbudget 6.3 |
| Dialogweg p95, Basic-Auth, `limit=100`, dieselbe Instanz | 0,538 s | Seitenbudget 6.3 |
| Kandidatenaufruf gegen den Container, `limit=100` | p95 0,022 s | Seitenbudget 3 |
| Snippet-Aufruf, 25 Dateien | p95 0,088 s, **max 1,944 s** (1 von 100) | Seitenbudget 3 und 5.3 |

### Bestand, Grösse und Verdikte

| Posten | Baseline | Quelle |
|---|---|---|
| Korpus | 50.000 Dateien, 20.208.046.426 Byte, Listen-Prüfsumme `bcbef9b2cb067c2200df2a4a2e89408f690710983117d4e78328024046098a72` (**ARM-Zeile**, die x86-Zeile ist `c03a8803...` und der falsche Vergleichswert) | Semantiklauf "Der Korpus" |
| Index insgesamt | 51.961 indexiert (Lasttest-Korpus plus Drill-Korpus aus 05-21 plus Nextcloud-Mitbringsel, 1.998 Zeilen), 37 übersprungen, 0 fehlgeschlagen | Semantiklauf, Nachmessung 7 |
| Verdikte übersprungen | 21 `too_large` (csv), 14 `empty_text` (jpg), 2 `image_not_ocrable` (png) | Nachmessung 7 |
| Chunks | 145.854, also 2,807 je Dokument | Semantiklauf |
| `vectors.db` plus WAL | 68.642.504 Byte, **1.321,0 Byte je Dokument** | Semantiklauf |
| Tantivy-Index | 785.308.851 Byte, **15.113 Byte je Dokument**; Vektoren 8,74 Prozent davon | Semantiklauf |
| Zeichen im Korpus | 1.397.354.875 | Semantiklauf |
| Endungsvergleich | 13 Endungen, Generator gleich Bestand, eine benannte Abweichung (20 csv `too_large`, Kategorie `oversize`) | Nachmessung 7 |
| OCR je Seite, `deu+eng` | Median 3.473,7 ms, Spitzen-RSS 90,6 MB | Nachmessung 8 |
| OCR je Seite, `deu+eng+fra` | Median 3.556,9 ms (plus 2,4 Prozent), Spitzen-RSS 106,1 MB (plus 15,5 MB) | Nachmessung 8 |

---

## Runtime State Inventory (Wiederanlaufpfad der Box)

Die ROADMAP verlangt ihn wörtlich: "Phase 10 braucht einen Wiederanlaufpfad fuer die Box (Instanz, Datentraeger, Abbild-Digest), bevor sie startet." Hier ist er, Kategorie für Kategorie.

| Kategorie | Was gefunden wurde | Erforderliche Handlung |
|---|---|---|
| **Gespeicherte Daten** | Der ExApp-Datenspeicher `nc_app_findling_backend_data` wurde am 07.09. um 06:46:03Z gelöscht: `state.db`, `vectors.db`, der 785 MB grosse Tantivy-Index und die Wortliste sind weg. Das Volumen wurde beim Wiederaufsatz neu registriert und ist leer. **Der Korpus lebt**: 50.000 Dateien, 20 GB, unter `/mnt/findling/ncdata/lasttest/files/loadtest`, im Datenspeicher von Nextcloud. `oc_findling_file_state` trug nur 37 Zeilen | **Vollständiger Neuaufbau des Index, rund 19 Stunden.** `occ findling:index --restart` ist auf der Box bereits eingestellt und startet mit dem nächsten Lauf der Hintergrundaufträge. Der Korpus wird **nicht** neu erzeugt, sondern mit `44-korpus-pruefsumme.py` gegen `bcbef9b2...` verifiziert |
| **Lebende Dienstkonfiguration** | AIO mit sieben Containern plus ExApp, Nextcloud 33.0.8.2, PostgreSQL, HaRP, Daemon `harp_aio` von AppAPI selbst angelegt. Die PHP-Begleit-App liegt im Volumen unter `custom_apps/findling` und ist auf dem **Stand vom 07.09.** (47 php-Dateien), nicht auf dem Stand von HEAD (58 Dateien) | Die PHP-Hälfte neu einspielen (`docker cp` plus `chown 33:33` plus `occ app:enable`). Die ExApp neu registrieren gegen `:dev` mit einer info.xml-Kopie aussserhalb des Arbeitsbaums |
| **OS-registrierter Zustand** | Kein systemd-Unit für den Wächter: der Wächter ist eine `while`-Schleife mit Rundendeckel (340) und wird abgesetzt gestartet. Der Kernel-Parameter `mem=4G` steht in `/etc/default/grub.d/99-mem4g.cfg` und **überlebt** einen Neustart; er ist aus `/proc/cmdline` zurückzulesen. Die Docker- und containerd-Wurzel liegen auf `/mnt/findling` | `mem=4G` zurücklesen, nicht annehmen. Die harte Grenze `memory.max = 2147483648` ist **nach jeder Registrierung weg** und muss neu gesetzt und aus der cgroup zurückgelesen werden (Fallstrick 5 aus 06.1-RESEARCH) |
| **Netz und Adressen** | Die öffentliche Adresse wechselt bei **jedem** Start. Die SSH-Regel der Security Group `sg-0e782f5233d73a847` zeigt auf eine alte Owner-Adresse. Der A-Record `loadtest.infranode.dev` (Cloudflare-Zone laut `box.env`) zeigt auf `3.77.150.91` und damit auf eine Adresse, die die Box seit dem 05.09. nicht mehr hat | `aws_box.sh start` erledigt BOX_IP und die SSH-Regel selbst (revoke vor authorize) und **nennt** den A-Record ausdrücklich als offen. Der A-Record braucht Zugangsdaten, die der Ausführung am 07.09. nicht vorlagen. Siehe Offene Frage 4 |
| **Geheimnisse und Zugangsdaten** | `~/.findling-aws.env` (vorhanden, Zugangsdaten für die AWS-CLI, wird von `aws_box.sh` aus der Umgebung gelesen und nie ausgegeben). `~/.findling-loadtest/box.env` (7.944 Byte Zustand plus Protokoll, kein Geheimnis, führt `BOX_INSTANCE_ID VOLUME_ID BOX_SECURITY_GROUP BOX_SSH_KEY BOX_IP BOX_STARTED_ISO BOX_STOPPED_ISO BOX_LAST_UPTIME_HOURS BOX_LAST_UPTIME_COST_USD BOX_PARKED_COST_USD_PER_DAY` und weitere). SSH-Schlüssel `~/.ssh/findling-loadtest`. Die Nextcloud-Passwörter (admin, lasttest) liegen **auf der Box** unter `/home/ubuntu/work/.pw/`, am 05.09. per `occ user:resetpassword` neu gesetzt | Keine Umbenennung, keine Migration. Nur: nichts davon darf in eine Ausgabe oder in eine Rohdatei geraten. `test_ops_scripts.py` hält das für `scripts/ops`; für die Messskripte unter `docs/measurements` muss der Plan es selbst zusichern |
| **Bauartefakte** | Die Abbilder auf dem Datenträger sind die alten: `06-11-arm` (vor dem Fix) und das am 07.09. gezogene `:dev` mit Digest `sha256:00111fd0...` (Baumhash `278fab52...`, 53 Dateien). Beide sind **nicht** der zu messende Stand | Das aktuelle `:dev` ziehen, seinen Digest festhalten, den Baumhash im Abbild gegen `6c47cd21...` (54 Dateien) prüfen. Platz beachten: 30 von 60 GB waren am 07.09. belegt |

**Der teuerste Satz dieses Inventars, wörtlich aus der Nachmessung:** "eine zweite Nextcloud zum Testen darf nie am selben Docker-Dienst hängen wie eine Instanz, deren Datenbestand gebraucht wird, weil der Volumenname einer ExApp allein aus ihrer App-Kennung folgt." Wenn Phase 10 irgendeine Zweitinstanz auf derselben Box anfasst, ist der Lauf verloren.

---

## Architecture Patterns

### Der Ablauf des Laufs, als Datenfluss

```
Lokal (Windows, Arbeitsbaum HEAD 888e239)
  |
  | (1) gh: docker.yml-Lauf und Digest von :dev feststellen (bereits gruen auf 2c1b741)
  | (2) aws_box.sh prices / status  -> Kostenlage, ohne Nebenwirkung
  |
  +--[ CHECKPOINT Owner: Anfahrt, Dauer, Kostendeckel, DNS ]-------------+
  |                                                                      |
  | (3) aws_box.sh start  -> neue IP, SSH-Regel nachgezogen, 3 offene Punkte benannt
  |
  v
Box (m7g.large, aarch64, mem=4G, /mnt/findling)
  |
  | (4) 60-bestand: memory.events VOR jedem Eingriff, mem=4G aus /proc/cmdline,
  |     df, Volumeninhalt, Bestand in state.db
  | (5) 44-korpus-pruefsumme  -> 20.208.046.426 Byte, bcbef9b2...   [Kriterium 1: derselbe Korpus]
  | (6) :dev ziehen, Digest festhalten, Baumhash IM Abbild == 6c47cd21...
  |     php-Haelfte einspielen (docker cp, chown 33:33, app:enable)
  |     info-box.xml mit <image-tag>dev</image-tag>, aussserhalb des Arbeitsbaums
  |     register --wait-finish, dann harte Grenze setzen und AUS DER CGROUP lesen
  |                                                          [Kriterium 1: derselbe Stand]
  | (7) 63-grundlast + 52-woher-die-grundlast: die MESS-01-Kernzahl,
  |     Container gestartet, bewaffnet, noch keine Suche, Modell nie geladen
  |                                                          [MESS-01]
  | (8) 64-spitze: GENAU EINE Suche gegen einen Container, der noch nie eine
  |     gesehen hat -> die erste Suche als Ereignis, Kaltstartzahl
  |     danach dieselbe Messung unter Nebenlaeufigkeit 1/4/8       [DI-07-02]
  |
  | (9) rss_sampler (5 s) + Statusbeobachter (120 s) + Waechter (300 s) starten
  |     occ findling:index --restart bestaetigen, Lauf anstossen
  |     ~~~ 19 Stunden abgesetzt ~~~
  |     Waechter: Uebergang erste->zweite Spur -> Suchlast im Nachlauf
  |               Ende beider Spuren -> OOM-Beweis VOR jedem Eingriff
  |               Weckdatei 00-FERTIG schreiben (der eigentliche Vertrag)
  |                                                          [Kriterium 1, 2]
  | (10) 67-nebenlaeufigkeit: 5 Stufen, 410 Anfragen, ueber die OCS-Route
  |                                                          [MESS-02, p95]
  | (11) Seitenroute: dieselbe Rangregel wie 2026-09-seitenbudget,
  |      Sitzung UND Basic-Auth getrennt (0,318 s Unterschied)
  |      Rundenzaehlung des Rechteabgleichs                   [DI-07-03]
  | (12) Eigener Nutzer, testdata/corpus hochladen, indexieren,
  |      die zehn Sprachfaelle als curl-Block fahren          [MESS-02, Sprachfaelle]
  | (13) 68-bestand-endungen als Gegenprobe, 48-vektorbestand, Indexgroesse
  |
  v
  | (14) Rohdaten und Skripte herunterholen, committen
  |
  +--[ CHECKPOINT Owner: Bericht abgenommen ]---------------------------+
  |
  | (15) aws_box.sh stop  -> Laufzeit und Kosten in box.env  [Kriterium 4]
  v
Repo: docs/measurements/2026-09-vergleichsmessung-m7g/ (README + skripte/ + rohdaten/)
      docs/performance.md: Zeilen in "Stand dieses Berichts", neuer Abschnitt, Zeile 3509 abloesen
```

### Muster 1: Der Baumhash als Beweis, nicht das Kennzeichen

**Was:** sha256 über sortierte relative Pfade plus sha256 des Inhalts mit normalisierten Zeilenenden, einmal im Abbild und einmal im Arbeitsbaum.
**Wann:** immer, wenn ein Bericht behauptet, einen bestimmten Codestand gemessen zu haben.
**Warum:** ein Kennzeichen kann jeder vergeben, und `:dev` wandert.

```python
# Quelle: docs/measurements/2026-09-05-semantiklauf-m7g/skripte/40-abbild.sh
# im Abbild: root = /app/.venv/lib/python3.13/site-packages/findling
# im Arbeitsbaum: root = backend/src/findling
import hashlib
import pathlib

root = pathlib.Path("...")
digest = hashlib.sha256()
count = 0
for path in sorted(root.rglob("*.py")):
    data = path.read_bytes().replace(b"\r\n", b"\n")
    digest.update(
        path.relative_to(root).as_posix().encode()
        + b"\0"
        + hashlib.sha256(data).hexdigest().encode()
        + b"\n"
    )
    count += 1
print("dateien:", count)
print("baumhash:", digest.hexdigest())
```

### Muster 2: `memory.events` vor jedem Eingriff

**Was:** die sieben Zähler aus der cgroup lesen, bevor irgendetwas angefasst wird, und an **jeder** Ablesestelle.
**Warum:** wer nach dem Aufräumen liest, misst das Aufräumen. Die Nachmessung führt die Ablesestellen als eigene Tabelle (Abschnitt 6), und das ist die Form, die Phase 10 fortschreibt.

### Muster 3: anon **und** `memory.current` immer nebeneinander

**Was:** anon ist der Heap, `memory.current` zählt den Seitencache derselben cgroup mit.
**Warum:** der Tantivy-Index ist ein mmap, und jeder gelesene Block landet im Dateicache derselben cgroup. Eine Store-Aussage aus `memory.peak` beschreibt die App schlechter als sie ist; eine aus anon allein ist die billigere Hälfte der Wahrheit. Der Abstand war in der Lastreihe über alle Stufen rund 86 MB und wuchs mit der Nebenläufigkeit nicht.

### Muster 4: Die erste Suche als Ereignis, nicht als Mittelwert

**Was:** lesen, **eine** Suche gegen einen Container, der noch nie eine gesehen hat, wieder lesen.
**Warum:** so wurde in der Nachmessung bewiesen, dass die Spitze den Besitzer gewechselt hat: `erste-suche-vor anon 694,3 MB` gegen `erste-suche-nach anon 1.116,6 MB`, plus 422,3 MB, und das sind die Modellgewichte. Ein Mittelwert über zehn Suchen hätte diese Aussage nicht getragen.

### Muster 5: Der Vertrag des abgesetzten Laufs ist eine Datei

**Was:** `00-FERTIG` im Laufverzeichnis, mit Zeitpunkt, Dauer und Weckwort. Die Meldekette sendet zusätzlich und protokolliert den HTTP-Code jedes Versuchs.
**Warum:** ntfy hat am 05.09. von der Box mit HTTP 403 geantwortet. Eine Meldekette, die still nicht meldet, ist schlimmer als keine.

### Anti-Muster

- **Das Abbild auf der Box bauen.** Kostet rund 40 Minuten gedeckelter Laufzeit und erzeugt einen Stand, den nur die gelöschte Maschine kennt. Nicht nötig: `:dev` trägt den Backend-Stand von HEAD.
- **Speicherzahlen aus dem Docker-Klienten.** Der Klient liefert eine Zahl auf `memory.current`-Basis. `rss_sampler.sh` liest die cgroup selbst, und ein Test hält die zwei Wörter aus dem Skript heraus.
- **Eine Wartefrist gegen die Uhr bemessen, an die man gerade gedacht hat.** Die Gegenprobe des Semantiklaufs erklärte den Lauf 52 Sekunden zu früh für tot, weil AIO `cron.php` nur alle fünf Minuten ruft und der **erste** Auftrag noch nichts einreiht.
- **Verdikte bei vollem Arbeitsvorrat lesen.** `skipped:no_text_layer` ist ein vorübergehendes Verdikt. Wer die Tabelle liest, während Arbeit da ist, liest Zwischenstände. Regel: nur bei leerem Arbeitsvorrat.
- **Einen Ausreisser herausnehmen.** Der 1,944-Sekunden-Snippet-Aufruf steht unverändert in den Rohdaten, mit einer Gegenprobe über 80 weitere Aufrufe daneben.

---

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---|---|---|---|
| Instanz an- und abfahren, SSH-Regel, Kostenrechnung | `aws ec2 start-instances` von Hand | `scripts/ops/aws_box.sh start` und `stop` | Eine Anfahrt von Hand geht an der Kostenrechnung und an der Zustandsdatei vorbei. Genau dafür sind die zwei Unterbefehle am 07.09. entstanden. `start` zieht ausserdem die SSH-Regel nach (T-06.1-78) und **nennt**, was es nicht selbst tut |
| Auf AWS warten | Eigene Polling-Schleife | Die Waiter der CLI (`ec2 wait instance-running`) | Hausregel seit 04.09.: feste 15-Sekunden-Intervalle, begrenzte Versuche. Eine handgeschriebene Schleife hat dem Projekt diese Regel eingebracht |
| Speicher eines Containers samplen | `docker stats` parsen | `scripts/ops/rss_sampler.sh` | cgroup statt Klient, anon und current getrennt, Schlusszeile mit `memory.events` und `OOMKilled` |
| Aus Sampler-Reihen die Berichtszahlen ziehen | Eigenes Skript oder ein Blick in die CSV | `scripts/ops/rss_digest.py` | Summe je Zeitpunkt, dann deren Maximum, und die Summe der Einzelmaxima als obere Schranke daneben. Die Entscheidung ist im Modul dokumentiert; sie neu zu treffen heisst, sie anders zu treffen |
| Nebenläufige Suchlast | `ab`, `wrk`, eine `xargs -P`-Schleife | `scripts/ops/search_load.py` | Über die OCS-Route, also den Nutzerweg, mit anon und `memory.current` vor, während und nach der Last, ohne Fremdabhängigkeit, offline-taugliches Abbild. Der Modulkopf trägt die Baseline-Reihe bereits als Text |
| p50 und p95 berechnen | numpy oder eine eigene Interpolation | Die Rangregel der Vorläufer: Wert an Rang `ceil(0,50 * n)` beziehungsweise `ceil(0,95 * n)` der sortierten Reihe, ohne Interpolation | Zwei Berichte sind nur vergleichbar, wenn sie dieselbe Regel benutzen. Die Regel steht ausgeschrieben im Seitenbudget-Bericht Abschnitt 2 |
| Grundlast Schritt für Schritt | Eine neue Schrittfolge | `52-woher-die-grundlast.py` (grob) und `01-grundlast-fein.py` (fein, Schritte 00 bis 10 und 13 bis 15 wortgleich daraus übernommen) | Die Schrittnamen **sind** die Vergleichsschlüssel. Eine umbenannte Zeile macht die Zeile-für-Zeile-Vergleichbarkeit kaputt, die Kriterium 3 verlangt |
| Prüfen, dass es noch derselbe Korpus ist | Dateien zählen | `44-korpus-pruefsumme.py` gegen die **ARM**-Zeile | Gleicher Samen und gleiche Bytezahl ergeben auf arm64 eine andere Prüfsumme als auf x86, weil die Schriftrasterung anders ausfällt |
| Die zehn Sprachfälle | Neu formulieren | Den `curl`-Block aus `integration.yml` ab Zeile 1427 übernehmen | Jeder Fall hat eine eigene Fehlermeldung, weil zehn Fehlschläge zehn verschiedene Dinge bedeuten, und jeder prüft **Anzahl und Titel**, weil eine Suche, die "irgendwas" findet, nur beweist, dass der Index nicht leer ist |
| Den Endungsvergleich | Neu bauen | `66-generator-endungen.py` plus `68-bestand-endungen.py` | Die Spaltenfalle ist dort schon geschlossen: die Spalte heisst `state`, nicht `verdict`, und daran ist im Semantiklauf eine Messung gescheitert |

**Kernerkenntnis:** Der einzige neue Code dieser Phase sind (a) ein Ablaufskript, das die vorhandenen Skripte in der richtigen Reihenfolge ruft, (b) der Sprachfall-Block als Shell-Datei statt als Workflow-Schritt, (c) die Rundenzählung für DI-07-03 und (d) die Seitenroute-Reihe. Alles andere ist Wiederverwendung. Jede Zeile eigener Messlogik, die ein vorhandenes Skript ersetzt, kostet Vergleichbarkeit.

---

## Common Pitfalls

### Pitfall 1: Der Baumhash-Beweis hat in **beiden** Vorläufern keine Rohdatei

**Was schiefgeht:** Kriterium 1 verlangt "den Beleg, dass Abbild und Arbeitsbaum derselbe Stand sind". Beide Vorläuferberichte behaupten Gleichheit, und in beiden ist der Schritt in der Rohdatei **leer**.
**Beweis:** `61-wechsel.txt` Zeile 4 und 5: `=== The tree hash of the package INSIDE the image ===` steht da, und die nächste Zeile ist schon der folgende Abschnitt. `grep -ri "baumhash\|278fab52" rohdaten/` liefert im Nachmessungs-Verzeichnis **null Treffer**. Im Semantiklauf steht in `40-abbild.log` Zeile 52 dasselbe leere `=== Baumhash im Abbild ===`; die Zeilen 54 bis 58 tragen nur die Arbeitsbaum- und die php-Hälfte.
**Warum es passiert:** `40-abbild.sh` ruft `docker run --rm --entrypoint /app/.venv/bin/python "$TAG" - <<'PY'` **ohne `-i`**, also bekommt Python kein stdin und liest EOF. `61-wechsel.sh` hat `-i` ergänzt, aber die Ausgabe fehlt trotzdem, und der Grund ist im Repo nicht belegt.
**Vermeidung:** Den Schritt einzeln fahren, seine Ausgabe in eine **eigene** Rohdatei schreiben, und im Akzeptanzkriterium des Plans verlangen, dass diese Datei nicht leer ist und beide Hashes trägt. Robuster als das Heredoc: das Hash-Rezept als Datei in den Container kopieren (`docker cp` oder `-v ...:ro`) und als Argument aufrufen.
**Warnzeichen:** ein Abschnittstitel ohne Zeilen darunter in der Rohdatei.

### Pitfall 2: Die Python-Messskripte kommen unter Windows mit CRLF aus dem Checkout und starten auf der Box nicht

**Was schiefgeht:** Kriterium 4 verlangt, dass Skripte im Repo liegen und der Lauf wiederholbar beschrieben ist. Ein `#!/usr/bin/env python3` mit CRLF lässt den Kernel nach einem Interpreter suchen, dessen Name auf ein unsichtbares Zeichen endet.
**Beweis:** `.gitattributes` deckt `*.sh` global mit `text eol=lf` und `scripts/ops/*.py` ausdrücklich, aber **nicht** `docs/measurements/**/skripte/*.py`. Der Kommentar dort sagt sogar, die Einschränkung sei Absicht. Gemessen im Arbeitsbaum: `66-generator-endungen.py` **CRLF**, `01-grundlast-fein.py` **CRLF**, `60-bestand.sh` LF. `git check-attr text eol` liefert für die Python-Datei zweimal `unspecified`.
**Vermeidung:** Eine Regel `docs/measurements/**/skripte/*.py text eol=lf` in `.gitattributes` ergänzen (mit Begründung im Kommentarstil der Datei) und die beiden Altfälle renormalisieren, **oder** jedes Messskript ausdrücklich als `python3 <datei>` aufrufen statt über die Shebang. Empfehlung: beides, weil die Regel den nächsten Fall verhindert und der Aufruf den aktuellen überlebt.
**Warnzeichen:** `bad interpreter: No such file or directory` bei einer Datei, die sichtbar existiert.

### Pitfall 3: Die zehn Sprachfälle brechen gegen den Lasttest-Nutzer

**Was schiefgeht:** Jeder Fall behauptet `entries | length == 1`. Der Lasttest-Korpus enthält dieselben Wörter.
**Beweis:** `scripts/dev/build_load_corpus.py` führt in seiner Wortliste `Frist` (Zeile 179), `Genehmigung` (182), `Grundstücksverkehrsgenehmigung` (186), `Kündigungsfrist` (195), `Vertrag` (229) und einen Satz mit `Auszug` (608). Die Eindeutigkeitszusage der Fälle ist in `backend/tests/test_corpus_terms.py` ausdrücklich gegen den **39-Dateien-Referenzkorpus** aus `scripts/dev/build_corpus.py` gemessen, nicht gegen den Lastkorpus.
**Vermeidung:** Einen **eigenen** Nutzer anlegen, dessen Heimat nur `testdata/corpus` enthält, die 39 Dateien über WebDAV hochladen, indexieren lassen und die Fälle als dieser Nutzer fahren. Die ACL-Kette trennt die beiden Bestände. Der Plan muss die sieben Dateinamen mitführen: `09-bescheid.pdf`, `10-kuendigung.docx`, `11-uebersicht.odt`, `12-aktenvermerk.txt`, `15-schweiz-baubewilligung.pdf`, `16-oesterreich-mitteilung.pdf`, `30-nur-ein-bild.pdf`.
**Zweite Hälfte des Fallstricks:** die Fälle 8 bis 10 hängen an der OCR-Spur (die Wörter existieren nur als Pixel). Der Nutzer braucht also einen abgeschlossenen OCR-Durchgang, und Verdikte darf man erst bei leerem Arbeitsvorrat lesen. 21 gerenderte Seiten bei rund 3,5 s je Seite sind wenige Minuten, aber sie sind nicht null.
**Warnzeichen:** `length == 2` statt `1` bei `Genehmigung`, `Frist`, `Vertrag` oder `Auszug`.

### Pitfall 4: Die harte Grenze überlebt keine Registrierung

**Was schiefgeht:** `memory.max` fällt nach `app_api:app:register` auf unbegrenzt zurück, und dann misst der Lauf eine 4-GB-Box statt einer 2-GiB-cgroup.
**Vermeidung:** `docker update --memory=2g --memory-swap=2g` **nach** jeder Registrierung, und `memory.max` sowie `memory.swap.max` **aus der cgroup** zurücklesen, nicht aus `docker inspect`. Der Pfad ist `/sys/fs/cgroup/system.slice/docker-<CID>.scope/memory.max`. Erwarteter Wert: `2147483648`.
**Warnzeichen:** eine anon-Spitze deutlich über 2.048 MB, ohne dass `memory.events` etwas meldet.

### Pitfall 5: `--rm-data` löscht das Volumen jeder Instanz mit derselben App-Kennung

**Was schiefgeht:** Der Volumenname einer ExApp folgt allein aus ihrer App-Kennung. Am 07.09. hat eine **zweite**, frische Nextcloud am selben Docker-Dienst über ihre Deinstallations-Zusage `app_api:app:unregister --rm-data` ausgeführt und damit `nc_app_findling_backend_data` der **ersten** Instanz entfernt.
**Vermeidung:** Auf dieser Box läuft in Phase 10 genau eine Nextcloud. Kein Installationslauf, kein Fremdtest, keine zweite Instanz. Wo `--rm-data` in Phase 10 vorkommt (Wiederaufsatz nach dem Muster `41-neuaufsatz.sh`), ist es Absicht und läuft **vor** dem Indexaufbau, nicht danach.
**Warnzeichen:** mehr als eine Nextcloud in `docker ps`.

### Pitfall 6: Die Meldekette meldet nicht, und man merkt es nicht

**Was schiefgeht:** `https://ntfy.infranode.dev/infranode-alerts-f43ceefc1193` hat am 04.09. den Abschluss gemeldet und am 05.09. von derselben Box mit `{"code":40301,"http":403,"error":"forbidden"}` geantwortet, weil die Box eine neue öffentliche Adresse bekommen hatte. Der Server war erreichbar, das Thema hat die Annahme verweigert.
**Vermeidung:** Der Vertrag ist die Datei `00-FERTIG` im Laufverzeichnis, nicht die Nachricht. Der Wächter sendet weiter und **protokolliert den HTTP-Code jedes Versuchs** in `99-ntfy-watch.log`. Der Plan darf keinen Schritt daran hängen, dass eine Nachricht ankommt.
**Zusatz aus dem globalen Regelwerk:** ntfy primär plus Mail-Fallback, den Fallback nicht abschalten. Für einen 19-Stunden-Lauf über Nacht ist das relevant.

### Pitfall 7: Der `/etc/hosts`-Pin überlebt keinen Maschinenneustart

**Was schiefgeht:** Weil der A-Record nicht gesetzt werden konnte, war `loadtest.infranode.dev` in `/etc/hosts` der Box auf die Adresse des Apache-Containers festgenagelt. Ein Maschinenneustart verteilt die Adressen der Docker-Brücke neu: Apache wanderte von `172.18.0.6` auf `172.18.0.4`, der Pin zeigte weiter auf die alte. Der Container hat es korrekt und laut gemeldet und weiter Suchen beantwortet, aber der Poller lief 300 Sekunden lang ins Backoff, und die erste Beobachtung der DI-05-36-Gegenprobe stand auf null.
**Vermeidung:** Entweder den A-Record wirklich setzen (Offene Frage 4), oder den Pin nach **jedem** Neustart aus `docker inspect` des Apache-Containers neu bilden, oder mit `curl --resolve` arbeiten statt mit `/etc/hosts`.
**Warnzeichen:** `WARNING:findling.nc.queue:could not count the queue` und `the queue has not answered for 3 passes`.

### Pitfall 8: Ein Wächter, der eine Zahl protokolliert, muss gegen eine bekannte Zahl gelesen werden

**Was schiefgeht:** `42c-lesen.py` hat `indexed` und `embedded` auf der obersten Ebene der Aufnahme gesucht. Dort steht `indexed` der PHP-Hälfte, das per Bauart 0 bleibt, und `embedded` gar nicht; beide leben unter `backend`. Der Wächter hat die ganze Nacht `indexed=0 embedded=0` protokolliert, während der Container bei 47.000 Vektoren stand. Zwei Folgen: die Suchlastprobe im Nachlauf ist nie gefahren (Bedingung `embedded > 200`), und das Ende hätte der Wächter erst am Rundendeckel erkannt, rund neun Stunden nach dem echten Ende.
**Vermeidung:** Den Leser beim Scharfstellen **einmal** gegen eine bekannte Zahl fahren, bevor der Lauf angestossen wird. Die Fassung unter `skripte/` ist die korrigierte, aber die Regel gilt für jedes neue Leseskript dieser Phase. Dieselbe Lehre in anderem Kleid: jedes Leseskript, das `state.db` anfasst, einmal trocken gegen das echte Schema fahren (die Spalte heisst `state`, nicht `verdict`).
**Warnzeichen:** eine Zahl, die über viele Runden **exakt** gleich bleibt.

### Pitfall 9: Zwei Berichte sind nur bei gleichem Anmeldeweg vergleichbar

**Was schiefgeht:** Basic-Auth kostet auf der Vergleichsinstanz **0,318 Sekunden je Anfrage**, die ein angemeldeter Nutzer nicht bezahlt. Abschnitt 5.2 des Seitenbudget-Berichts hatte diese Zeit dem Rechteabgleich zugeschrieben; der Audit-Befund M-03 der Phase 9 hat das in Abschnitt 6.3 korrigiert.
**Vermeidung:** Der Plan muss den Anmeldeweg jeder Reihe ausdrücklich nennen und, wie 6.3 es tut, **beide** Wege messen (Sitzung und Basic-Auth), damit die Zahlen sowohl gegen den alten Bericht als gegen den Nutzeralltag stellbar sind. Der Weg für die Sitzung ist in `scripts/dev/probe_page_login.sh` und im Paritätsjob von Plan 09-07 vorgezeichnet, samt der Falle: LoginController von Nextcloud 34 weist eine Anmeldung ohne vertrauenswürdigen `Origin`-Kopf mit derselben Umleitung ab wie ein falsches Passwort.
**Warnzeichen:** eine Reihe, die 0,3 s über der Erwartung liegt und deren Kopfzeile den Anmeldeweg nicht nennt.

### Pitfall 10: Der Seitenbudget-Bericht misst keine Semantik

**Was schiefgeht:** Reihe C des Seitenbudget-Berichts war laut Bauart der hybride, teure Fall. Gemessen war sie so teuer wie Reihe B, weil `one_round()` die Vektorseite nur einschaltet, wenn `side.vectors is not None`, und auf jener Instanz gab es keine `vectors.db`.
**Vermeidung:** Auf der Box **gibt** es sie (145.854 Vektoren). Der Plan muss damit rechnen, dass die Seitenroute dort teurer ist als 0,122 s, und muss die Zahl als **Erstmessung** ausweisen, nicht als Vergleich. Die Gegenrichtung ist die eigentliche Chance: T-09-29 (voller Vektorscan je Anzeigeseite) wurde in Phase 9 mit `accept` und der Begründung geschlossen, dass die Zahlen fehlen. Phase 10 liefert sie.

### Pitfall 11: Eine Wartefrist gegen die falsche Uhr

**Was schiefgeht:** AIO ruft `cron.php` alle fünf Minuten, und der **erste** Auftrag der App reiht noch nichts ein. Die Gegenprobe des Semantiklaufs erklärte den Lauf deshalb 52 Sekunden zu früh für tot.
**Vermeidung:** Jede Wartefrist gegen die **langsamste** beteiligte Uhr bemessen: Poller-Backoff bis 300 s **und** zwei Runden des Fünf-Minuten-Systemcrons. Das Urteil des Skripts stehen lassen und den Nachtrag darunter schreiben, so wie `00-start.txt` es tut.

### Pitfall 12: Git für Windows schreibt Pfadargumente um

**Was schiefgeht:** Aus `/dev/sdf` wurde `C:/Program Files/Git/dev/sdf`, und die AWS-API lehnte den Attach mit einer Meldung ab, die den Wert nennt und nicht die Ursache.
**Vermeidung:** `aws_box.sh` schaltet die Umschreibung für seinen Prozess ab; ein Test hält das fest. Für neue Skripte, die von diesem Windows-Rechner aus gegen die Box oder die API laufen, gilt dasselbe.

---

## Kosten und Laufzeit

Sätze, festgenagelt in `scripts/ops/aws_box.sh` aus der Preisliste eu-central-1, Fassung 20260903195206, gültig ab 2026-09-01, und der VPC-Liste 20260831092232. Alles netto USD. [CITED: `scripts/ops/aws_box.sh` Zeilen 105 bis 134]

| Posten | Satz |
|---|---|
| m7g.large, On Demand Linux | 0,0978 USD je Stunde |
| Öffentliche IPv4-Adresse, in Benutzung | 0,005 USD je Stunde |
| gp3, bereitgestellter Speicher | 0,0952 USD je GB-Monat, gegen einen 730-Stunden-Monat |
| Datenträger insgesamt | 100 GB (60 GB Daten plus 40 GB Wurzel) gleich 9,52 USD je Monat gleich **0,3130 USD je Tag** gleich 0,01304 USD je Stunde |
| **Laufend** | **0,1158 USD je Stunde** (bestätigt durch zwei Läufe: 20,5 h gleich 2,37 USD; 1,95 h gleich 0,2254 USD) |
| **Angehalten** | **0,3130 USD je Tag**, nur die Datenträger |

### Szenarien

| Szenario | Box-Stunden | Kosten | Liefert |
|---|---|---|---|
| **A. Volllauf mit Semantik, Form von 06-11** (empfohlen) | 19 h Neuaufbau plus rund 3 h Anfahrt, Grundlast, Lastreihen, Sprachfälle, Abschluss gleich **22 h**, mit Reserve **26 h** | **2,55 bis 3,01 USD** | Alle vier Kriterien. Grundlast, Gesamtspitze, Laufzeit, `memory.events` über den ganzen Lauf, p95 über den vollen Bestand, Byte je Dokument, Endungsvergleich, DI-07-02, DI-07-03, Seitenroute, zehn Sprachfälle |
| **B. Nur Grundlast und Kaltstart, ohne Index** | rund 3 h | rund 0,35 USD | Nur MESS-01 in seiner Kernzahl. **Kein** p95 über den Bestand, keine Spitze, keine Laufzeit, keine Sprachfälle mit Inhalt. Kriterium 1 sagt ausdrücklich "mit dem vorhandenen v1.0-Korpus (51.961 Dokumente)", Kriterium 2 verlangt einen p95, der mit 481,6 ms vergleichbar ist. **Reicht nicht** |
| **C. Neuaufbau ohne zweite Spur** (`FINDLING_EMBED_ENABLED` aus) | rund 13 h plus 3 h gleich 16 h | rund 1,85 USD | Vergleichbar mit 05-21 (12 h 49 min), **nicht** mit 06-11. Die Semantik ist der Gegenstand von MESS-01. **Falsche Baseline** |
| Bereits angefallen, geparkt seit 07.09. | , | rund 0,63 USD bis heute, plus 0,31 USD je weiteren Tag | , |

**Empfohlener Kostendeckel für den Owner-Checkpoint: 30 Stunden und 3,50 USD netto.** Das ist Szenario A plus vier Stunden Reserve für einen Fehlstart. Zum Vergleich: der Owner-Deckel der Nachmessung lag bei 8 Stunden für einen Lauf, der 1,95 gebraucht hat; der Semantiklauf hat 20,5 Stunden und 2,37 USD gekostet und wurde abgenommen.

**Was die 19 Stunden wirklich sind, damit niemand sie für Rüstzeit hält:** sie sind der Volllauf, den Kriterium 1 verlangt. Der Neuaufbau erzeugt genau die Zahlen, die neben 1.837,8 MB und 18 h 56 min gehören. Ohne den Volumenvorfall hätte Phase 10 diese 19 Stunden **trotzdem** investieren müssen, wenn sie eine Gesamtspitze und eine Laufzeit ausweisen will; der Vorfall hat die Wahl genommen, nicht die Kosten erzeugt.

---

## Offene Fragen für Discuss und Owner

### 1. Umfang des Laufs: Volllauf oder Kurzlauf

**Was wir wissen:** Der Index ist weg, `--restart` ist eingestellt, ein Start zieht rund 19 Stunden nach sich. Die Baseline-Zahlen (Gesamtspitze, Laufzeit, `max`, Byte je Dokument) existieren nur als Volllauf-Zahlen.
**Was unklar ist:** Ob der Owner 22 bis 26 Box-Stunden über eine Nacht freigibt oder eine kürzere Aussage vorzieht.
**Optionen:** (a) Volllauf, Form von 06-11, alle vier Kriterien. (b) Kurzlauf über Grundlast und Kaltstart, MESS-01 nur in der Kernzahl, MESS-02 und Kriterium 1 offen. (c) Volllauf ohne zweite Spur, vergleichbar mit der falschen Baseline.
**Empfehlung: (a).** Die Kriterien 1 und 2 sind ohne den Bestand nicht erfüllbar, und der Neuaufbau ist unvermeidlich. Ein Kurzlauf würde die Box später ein zweites Mal für 19 Stunden anfahren müssen.

### 2. Die zehn Sprachfälle: auf der Box oder in CI

**Was wir wissen:** Die Fälle leben als Schritt in `integration.yml` und laufen gegen den 39-Dateien-Referenzkorpus auf einem Runner. Der letzte Lauf gegen den zu messenden Baum (`2c1b741`) war grün. Einen v1.0-Vergleichswert **auf der Box** gibt es nicht: weder der Semantiklauf noch die Nachmessung hat die Fälle gefahren.
**Was unklar ist:** Ob Kriterium 2 mit dem CI-Beleg erfüllt ist oder eine Messung auf der Zielhardware verlangt.
**Optionen:** (a) Nur den CI-Lauf zitieren, mit Laufnummer und Commit. Kostet null Box-Zeit. (b) Zusätzlich auf der Box fahren, gegen einen eigenen Nutzer mit `testdata/corpus`. Kostet rund 20 bis 30 Minuten Box-Zeit inklusive Upload und OCR. (c) Nur auf der Box.
**Empfehlung: (b).** Der Wortlaut des Kriteriums ("Der Lauf zeigt keine Regression: ... und die zehn deutschen CI-Sprachfaelle bleiben im v1.0-Rahmen") liest sich als Aussage über den Lauf. 30 Minuten sind rund 0,06 USD. Der Bericht muss dabei ausdrücklich sagen, dass es **keine** v1.0-Entsprechung auf der Box gibt und die Zahl damit eine Erstmessung neben einem CI-Beleg ist, keine Vergleichszeile.

### 3. Die drei geerbten Befunde aus Phase 7

**Was wir wissen:** `deferred-items.md` der Phase 7 weist **drei** Befunde ausdrücklich Phase 10 zu.

| ID | Frage | Aufwand auf der Box | Bemerkung |
|---|---|---|---|
| **DI-07-02** | Muss `REQUEST_TIMEOUT_SECONDS` von 1,5 s steigen? Der Kaltstart kostet 1.332,1 ms, die Marge ist 167,9 ms und nicht 1.167,9 ms | Der Messweg ist `64-spitze.sh`, ergänzt um Nebenläufigkeit. Rund 30 Minuten | Die **Entscheidung** über die Konstante ist eine Änderung, die jeden Nutzer länger warten lässt. Sie gehört nicht in einen Messplan, aber die Zahl schon |
| **DI-07-03** | Wie oft dreht die Schleife über `MAX_ROUNDS = 3` mehr als eine Runde, und was kosten die Runden? Im ungünstigsten Fall vier Containeraufrufe je Suche | Braucht eine Zählung im PHP-Weg oder eine Auswertung der Protokolle. Rund 1 Stunde | Der Befund sagt selbst: die Messung gehört Phase 10, eine Änderung am Rechteabgleich gehört Phase 11 |
| **DI-07-04** | Die native arm64-Rohdatei der Feinmessung fehlt, die vorhandene ist QEMU-emuliert | **Null Box-Zeit.** `workflow_dispatch` von `measure.yml` auf `ubuntu-24.04-arm`, Schritt "D, the base load step by step" | Das Artefakt `01-grundlast-fein-arm64.txt` ersetzt die emulierte Datei ohne weitere Änderung; danach sind die arm64-Spalten in vier Abschnitten und in `docs/performance.md` nachzuziehen |

**Was unklar ist:** Ob alle drei in diese Phase gehören oder ob DI-07-03 vertagt wird.
**Empfehlung:** Alle drei mitnehmen. DI-07-04 kostet nichts und schliesst eine benannte Lücke. DI-07-02 fällt als Nebenprodukt der Kaltstartmessung an. DI-07-03 ist der teuerste und der einzige, der vertagbar wäre; er ist aber die Zahl, die T-09-29 (`accept` mit fehlender Begründung) zu einer begründeten Entscheidung macht, und Phase 11 fährt die Audits erneut.

### 4. Der A-Record `loadtest.infranode.dev`

**Was wir wissen:** Er zeigt auf `3.77.150.91`, eine Adresse, die die Box seit dem 05.09. nicht mehr hat. Die Zone liegt laut `box.env` bei Cloudflare ("CF-A-Record loadtest nachziehen"). Der Ausführung am 07.09. lagen die Zugangsdaten nicht vor; Ersatz war ein `/etc/hosts`-Pin auf die Adresse des Apache-Containers, und der hat nach einem Maschinenneustart Kosten verursacht (Pitfall 7). Der Semantiklauf-Bericht sagt zum Ersatz ausdrücklich, er sei "für die Messung gleichwertig (dieselbe TLS-Kette, derselbe Apache, derselbe Weg durch AppAPI)".
**Optionen:** (a) Owner setzt den A-Record nach dem Start auf die neue Adresse. Beste Variante, ein Handgriff, beseitigt Pitfall 7. (b) `/etc/hosts`-Pin wie 06.1-18, aber nach **jedem** Neustart aus `docker inspect` neu gebildet. (c) `curl --resolve` in allen Messskripten, kein Pin.
**Empfehlung: (a), mit (b) als Rückfall.** Der 19-Stunden-Lauf ist genau die Situation, in der ein Neustart passieren kann, und die Adressen der Docker-Brücke werden dabei neu verteilt.

### 5. Wird `CLAUDE.md` um den Posten "Tokenizer und Splitter" ergänzt?

**Was wir wissen:** Die Feinmessung hat den Posten mit 544 MB gemessen, grösser als das Modell, und hat `CLAUDE.md` ausdrücklich nicht angefasst, mit dem Satz "Ob die Tabelle nachgezogen wird, entscheidet der Owner". `docs/performance.md` wiederholt das an Zeile 3534 bis 3539. Phase 10 liefert die Zahl auf nativem ARM und damit den besseren Anlass.
**Optionen:** (a) Der Plan schlägt die Zeile vor, der Owner nimmt sie im Abnahme-Checkpoint an. (b) Weiter offen lassen und in Phase 11 entscheiden.
**Empfehlung: (a).** Die RAM-Budget-Tabelle ist die Stelle, an die ein Fremder für die Hardwareanforderung schaut, und sie führt heute den zweitgrössten Posten nicht.

### 6. Verzeichnisname des neuen Messberichts

**Was wir wissen:** Die Namensgebung ist inkonsistent: `2026-09-05-semantiklauf-m7g` mit Tag, `2026-09-nachmessung-m7g` und `2026-09-grundlast-fein` ohne. Die neueren tragen keinen Tag.
**Empfehlung:** `docs/measurements/2026-09-vergleichsmessung-m7g/` mit `skripte/` und `rohdaten/`, also der Form der beiden jüngsten Berichte. Der Plan sollte den Namen festlegen, damit `docs/performance.md` und der Bericht nicht auf verschiedene Pfade zeigen.

### 7. Was passiert nach der Abnahme mit der Box

**Was wir wissen:** Kriterium 4 verlangt nur "die Box ist danach wieder angehalten". Das Abbaukriterium steht aber schon geschrieben: `docs/performance.md` Zeile 3784 bis 3789, "abgebaut wird **nach der v1.1-Messung** ... Erst wenn diese Messung abgenommen ist, fällt die Box, und dann mit derselben Nichtexistenz-Prüfung, die dieser Plan beschrieben hat." Plan 06.1-19 hatte den Abbau vorgesehen und ihn nicht ausgeführt; D-H3 verlangt eine eigene Freigabe.
**Was unklar ist:** Ob Phase 10 nur anhält (Kriterium 4) oder auch abbaut (Abbaukriterium erfüllt).
**Optionen:** (a) Nur anhalten, wie Kriterium 4 sagt; der Abbau bekommt einen eigenen Plan in Phase 11 mit eigener Freigabe. (b) Anhalten und im selben Plan nach Owner-Freigabe abbauen (`aws_box.sh destroy`, Nichtexistenz-Prüfung für Instanz, Datenträger und Security Group, plus Sweep nach Tag `purpose=findling-phase5`).
**Empfehlung: (a) als Vorgabe, (b) als Owner-Entscheid im Abnahme-Checkpoint.** Kriterium 4 sagt "angehalten", nicht "abgebaut", und ein Abbau, der eine Nacharbeit am Bericht unmöglich macht, gehört nicht in denselben Lauf wie der Bericht. Aber die Frage muss gestellt werden, sonst bleibt eine Box mit 0,31 USD je Tag stehen, für die das Abbaukriterium erfüllt ist.

### 8. Ob `docs/performance.md` weiterhin die Sammelstelle bleibt

**Was wir wissen:** `docs/performance.md` ist 3.800 Zeilen lang und führt je Lauf einen Abschnitt plus Zeilen in "Stand dieses Berichts". Zeile 3509 zeigt ausdrücklich auf Phase 10.
**Empfehlung:** Ja, nachziehen. Ein Zeiger im Projektdokument, der auf eine Phase zeigt, die gelaufen ist, ohne dass die Zahl nachkommt, ist genau der Widerspruch, den die Audits dieses Projekts sonst als Befund aufschreiben.

---

## Owner-Checkpoints, die die Pläne tragen müssen

Beide nach dem Muster von Plan 06.1-18 (`checkpoint:human-action` und `checkpoint:human-verify`, jeweils `gate="blocking"`).

### Checkpoint 1, vor dem ersten `aws_box.sh start`, blockierend

1. Darf die Box `i-06b1d913f5c6f669b` für diesen Lauf gestartet werden? Sie ist seit dem 07.09.2026, 06:56:42Z angehalten und kostet angehalten rund 0,3130 USD je Tag, laufend 0,1158 USD je Stunde.
2. **Der Lauf ist lang, und das ist unvermeidlich.** Der Index auf dem Datenträger ist seit dem Volumenvorfall vom 07.09. weg, `occ findling:index --restart` ist eingestellt, ein Start zieht rund 19 Stunden Neuaufbau nach sich. Erwartete Gesamtlaufzeit 22 bis 26 Stunden. Bitte bestätigen, dass ein abgesetzter Lauf über Nacht gewollt ist.
3. Gilt eine Kostenobergrenze? Vorschlag: 30 Stunden und 3,50 USD netto.
4. Der A-Record `loadtest.infranode.dev` zeigt auf eine alte Adresse (Offene Frage 4). Kann der Owner ihn nach dem Start in der Cloudflare-Zone nachziehen, oder wird wieder mit einem `/etc/hosts`-Pin gearbeitet?
5. Sollen die zehn Sprachfälle **auf der Box** gefahren werden (Offene Frage 2), rund 30 Minuten zusätzlich?
6. Sollen DI-07-02 und DI-07-03 in diesem Lauf mit beantwortet werden (Offene Frage 3)?
7. Der Abbau der Box ist **nicht** Teil des Laufs (D-H3) und braucht eine eigene Freigabe.

**Resume-Signal:** "box frei, weiter" plus die Antworten auf 2 bis 6.

### Checkpoint 2, nach dem Bericht und vor `aws_box.sh stop`, blockierend

1. Trägt der Bericht die Struktur des v1.0-Berichts, sodass jede Zahl neben ihrer Entsprechung steht?
2. Steht der Abschnitt "Was dieser Lauf nicht besser gemacht hat" mit **jeder** Verschlechterung, in eigener Überschrift?
3. Steht die Kernaussage in der Form aus D-H2 (drei Schadenszähler auf null, anon-Spitze mit Zahl, `max` als ausgewiesene Kennzahl mit erklärendem Satz), und steht die alte Zahl als Vergleich daneben?
4. Sind Rohdaten und Skripte im Repo, und ist der Lauf wiederholbar beschrieben?
5. Wird `CLAUDE.md` um den Posten "Tokenizer und Splitter" ergänzt (Offene Frage 5)?
6. Die Box wird jetzt angehalten. Soll sie danach abgebaut werden, oder bleibt sie stehen (Offene Frage 7)?

**Warum der Stop erst nach der Abnahme steht:** der Container soll unangetastet bleiben, damit der Owner die Verwaltungsseite und die cgroup selbst ansehen kann. So ist es im Semantiklauf gehandhabt worden. Der Preis sind ein paar Stunden Laufzeit; der Gegenwert ist eine Abnahme, die nicht auf einer Behauptung beruht. Der Plan sollte diesen Preis ausweisen und dem Owner die Wahl lassen.

---

## Environment Availability

| Abhängigkeit | Gebraucht für | Vorhanden | Fassung | Rückfall |
|---|---|---|---|---|
| `git`, `gh` | Stand feststellen, Laufnummern lesen | ja | `gh run list` funktioniert | , |
| `python` lokal | Baumhashes nachrechnen, Auswertung | ja | , | Global-Python 3.13 ist auf diesem Rechner defekt (globale Notiz); für Projektarbeit gilt `uv run` im `backend/` |
| `uv` | ruff, pyright, vulture, pytest | ja, Projektstandard (`cd backend && uv run ...`) | , | keiner |
| `aws` CLI | `aws_box.sh` | **nicht geprüft** (kein Cloud-Kontakt in dieser Recherche) | , | `aws_box.sh require_tools` prüft es selbst und bricht mit Meldung ab |
| AWS-Zugangsdaten | `aws_box.sh` | `~/.findling-aws.env` **vorhanden** (Existenz geprüft, Inhalt nicht gelesen) | , | keiner |
| Zustandsdatei | Instanz-, Volumen- und SG-Kennung | `~/.findling-loadtest/box.env` **vorhanden**, 7.944 Byte, führt alle 21 Schlüssel | , | keiner. `aws_box.sh` verweigert ohne sie |
| SSH-Schlüssel | Zugang zur Box | `~/.ssh/findling-loadtest` laut `box.env` (`BOX_SSH_KEY`) | nicht geprüft | keiner |
| `curl` | `aws_box.sh start` liest die Owner-Adresse über api.ipify.org | ja | , | keiner, `start` bricht ohne `curl` ab |
| Cloudflare-Zugang für `loadtest.infranode.dev` | Pitfall 7 vermeiden | **unbekannt**, lag am 07.09. nicht vor | , | `/etc/hosts`-Pin auf der Box, oder `curl --resolve` |
| ntfy-Thema `infranode-alerts-f43ceefc1193` | Meldekette des abgesetzten Laufs | **antwortet mit 403** von der Box (Stand 05.09.) | , | `00-FERTIG`-Datei plus Mail-Fallback. Kein Schritt darf daran hängen |
| Box selbst: Docker 29.8.0, containerd 2.3.4, AIO, Nextcloud 33.0.8.2, PostgreSQL, Tesseract mit `deu eng fra osd` | der ganze Lauf | war am 07.09. so | Nextcloud 33.0.8.2 liegt im Fenster min 33 / max 35 | keiner |
| Platz auf `/mnt/findling` | Index, Vektoren, Abbilder | 30 von 60 GB belegt am 07.09.; der neue Index braucht rund 0,85 GB, das alte `06-11-arm`-Abbild belegt weiter Platz | , | Alte Abbilder räumen, bevor der Lauf startet |

**Fehlend ohne Rückfall:** keines.
**Fehlend mit Rückfall:** Cloudflare-Zugang (Rückfall `/etc/hosts` oder `--resolve`), ntfy (Rückfall Datei plus Mail).
**Nicht geprüft, weil diese Recherche keine Cloud-Ressource angefasst hat:** der laufende Zustand der Instanz, der Digest von `:dev` in ghcr, der Inhalt des Datenträgers. Der Plan muss die Feststellung dieser drei Dinge als **ersten** Schritt nach der Anfahrt führen und darf keine Annahme aus dieser Recherche als Messwert übernehmen.

Kommandos für diese drei Feststellungen, für den Plan:

```sh
# ohne Nebenwirkung, vor der Anfahrt
scripts/ops/aws_box.sh status
scripts/ops/aws_box.sh prices

# der Digest, den der Bericht nennen muss
docker buildx imagetools inspect ghcr.io/street1983nk/findling_backend:dev

# nach der Anfahrt, auf der Box, vor jedem Eingriff
cat /proc/cmdline
df -h /mnt/findling
sudo docker volume ls --filter name=findling_backend
```

---

## Standard Stack

Diese Phase **installiert kein Paket** und fügt keine Abhängigkeit hinzu. Der Stack ist der ausgelieferte, und er ist in `CLAUDE.md` unter "Kernentscheidungen auf einen Blick" festgeschrieben (Tantivy 0.26.0, sqlite-vec 0.1.9, Tesseract 5.5.0, fastembed 0.8.0 mit multilingual-e5-small int8, pypdfium2 5.13.0, nc_py_api, FastAPI, python:3.13-slim-trixie).

Die Werkzeuge der Messung sind alle im Repo und importieren aussser der Standardbibliothek nichts (`search_load.py` sagt das in seinem Modulkopf ausdrücklich, weil das Abbild offline laufen muss).

**Ein Plan, der in dieser Phase ein Paket installiert, hat sich verlaufen.** Die einzige denkbare Ausnahme ist ein Analysewerkzeug für die Auswertung; auch das ist unnötig, weil `rss_digest.py` existiert und die Rangregel für p50 und p95 ohne Interpolation drei Zeilen sind.

## Package Legitimacy Audit

**Nicht anwendbar: diese Phase installiert keine externen Pakete.** Es gibt keine Zeile für die Tabelle. `slopcheck` wurde nicht gefahren, weil es keinen Paketnamen zu prüfen gibt.

Was der Plan stattdessen prüfen muss, ist die Herkunft des **Abbilds**, und dafür gibt es einen belegten Weg: `docker.yml` veröffentlicht per Digest, der Merge-Job prüft, dass das Manifest `linux/amd64` und `linux/arm64` trägt, und die Provenance-Attestierungen (unsigniert, buildkit, `slsa.dev/provenance/v1`) werden auf ihre Plattform-Digests hin geprüft. Der Workflow sagt selbst, was das **nicht** ist: keine GitHub-Artefakt-Attestierung, also ein Prüfpfad und keine Signatur. Der Bericht sollte diesen Unterschied nennen, statt "signiert" zu schreiben.

---

## Security Domain

`security_enforcement` ist in `.planning/config.json` nicht gesetzt, gilt also als aktiv.

### Anwendbare ASVS-Kategorien

| Kategorie | Trifft zu | Standardmassnahme in diesem Projekt |
|---|---|---|
| V2 Authentifizierung | ja, am Rand | Die Messskripte melden sich als echte Nutzer an (Basic-Auth oder Sitzung). Passwörter kommen aus einer Umgebungsvariablen (`--password-env` in `search_load.py`), nie aus einer Kommandozeile, nie in eine Rohdatei |
| V3 Sitzungsverwaltung | ja | Die Seitenroute-Reihe braucht eine Cookie-Sitzung. Der `Origin`-Kopf ist Pflicht, sonst weist LoginController die Anmeldung mit derselben Umleitung ab wie ein falsches Passwort (Befund aus Plan 09-07) |
| V4 Zugriffskontrolle | **ja, zentral** | Die Berechtigungskette bleibt unverändert: SQLite-ACL-Vorfilter im Container, finaler PHP-Recheck als Grenze. Kein Messweg darf sie umgehen. Die Sprachfälle laufen als Nutzer über OCS, nicht als Admin gegen den Container |
| V5 Eingabevalidierung | nein, kein neuer Eingabepfad | , |
| V6 Kryptographie | nein | Kein eigenes Krypto. TLS-Kette der Box unverändert (das Zertifikat ist echt, `docs/performance.md` "Das Zertifikat ist echt") |
| V7 Fehlerbehandlung und Protokollierung | ja | Rohdaten werden unverändert committet. Kein Geheimnis in eine Ausgabe. `box.env` liegt aussserhalb des Arbeitsbaums, "one careless git add away from a public commit" |
| V14 Konfiguration | **ja** | Die SSH-Regel der Security Group ist auf genau eine Adresse (`/32`) offen, revoke vor authorize. Die harte cgroup-Grenze wird nach jeder Registrierung neu gesetzt und zurückgelesen |

### Bekannte Bedrohungsmuster für diesen Lauf

| Muster | STRIDE | Standardmassnahme | Herkunft |
|---|---|---|---|
| SSH-Regel bleibt auf einer fremd gewordenen Adresse offen | Information Disclosure | `aws_box.sh start` zieht die Regel für Port 22 auf die aktuelle Owner-Adresse nach, revoke vor authorize, damit nie beide offen sind | T-06.1-78 |
| Zugangsdaten in einer Kommandozeile, einem Protokoll oder der Zustandsdatei | Information Disclosure | Die CLI liest die Zugangsdaten selbst aus der Umgebung; das Skript nennt sie genau einmal, in der Prüfung, ob sie gesetzt sind | T-05-17 |
| Vergessene Ressource in einem Konto, das anderes hält | Repudiation | Jede erzeugte Ressource trägt `purpose=findling-phase5`, und `destroy` sucht nach genau diesem Tag | T-05-19 |
| Eine fremde API sechzigmal je Minute fragen | Denial of Service gegen Dritte | Nur die Waiter der CLI, feste 15 Sekunden, begrenzte Versuche. Keine handgeschriebene Wartelaufschleife | Hausregel 04.09., und die globale Regel "API-Limits vor Zugriff prüfen" |
| Ein Messskript liest Nutzerinhalte und schreibt sie in eine Rohdatei, die committet wird | Information Disclosure | Der Statusbeobachter nimmt die Verwaltungsseite **ohne Namensträger** auf. Neue Leseskripte müssen dieselbe Regel tragen und sie im Docstring nennen (Muster von T-08-01) | Semantiklauf, "Die Beobachter" |
| Ein zerstörender Befehl trifft das falsche Volumen | Tampering, Denial of Service | Genau eine Nextcloud auf der Box. `--rm-data` nur im Wiederaufsatz vor dem Indexaufbau, nie danach | Nachmessung 12a |
| Der Lauf schreibt in Nutzerdateien | Tampering | Die Nur-Lese-Invariante (IDX-07) gilt unverändert; OCR ist strikt index-only, das Prüfsummen-Gate über den Referenzkorpus läuft in CI | CLAUDE.md-Kernentscheidung |
| Eine Verschlechterung wird nicht berichtet | Repudiation | Der Abschnitt "Was dieser Lauf nicht besser gemacht hat" ist Pflicht, in eigener Überschrift, und Kriterium 2 verlangt ihn wörtlich | Nachmessung 14 |

---

## Assumptions Log

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---|---|---|
| A1 | Der Neuaufbau des Index dauert wieder rund 19 Stunden. Die Zahl stammt aus 06-11 (18 h 04 min erste Spur, 18 h 56 min beide) und setzt voraus, dass die Phasen 7 bis 9 den Indexdurchsatz nicht verändert haben. Das ist plausibel (der faule Bau verschiebt, er spart nicht; `split_compound` war schon in v1.0 aktiv), aber nicht gemessen | Kosten und Laufzeit | Der Kostendeckel reisst, oder der Lauf endet mitten in einer Nacht. Der Plan braucht deshalb einen Rundendeckel im Wächter (06-11 hatte 340) und einen Abbruchpfad, der die bis dahin erhobenen Zahlen sichert |
| A2 | `occ findling:index --restart` steht auf der Box noch eingestellt. Die Notiz ist zwei Tage alt, die Box war seither aus | Runtime State Inventory | Der Lauf indexiert nicht an. Erkennbar an einem Arbeitsvorrat, der 0 bleibt. Der Plan muss den Vorrat prüfen und den Befehl notfalls erneut absetzen, nach der Wartefrist gegen die langsamste Uhr (Pitfall 11) |
| A3 | Der Korpus liegt unverändert unter `/mnt/findling/ncdata/lasttest/files/loadtest`. Belegt für den 07.09., nicht für heute | Runtime State Inventory | Der Vergleich zur Baseline fällt. `44-korpus-pruefsumme.py` gegen `bcbef9b2...` ist die Prüfung, und sie muss **vor** dem Indexaufbau laufen, damit ein Fehlbefund nicht 19 Stunden kostet |
| A4 | Der Digest von `:dev` in ghcr trägt den arm64-Baumhash `6c47cd21...` (54 Dateien). Der Arbeitsbaum-Hash ist selbst nachgerechnet, die Gleichheit von Baum und Abbild ist aus der Gleichheit der Git-Bäume zwischen `2c1b741` und HEAD **geschlossen**, nicht im Abbild gemessen | Bestandsaufnahme | Kriterium 1 fällt. Genau deshalb ist der Baumhash im Abbild ein eigener Schritt mit eigener Rohdatei (Pitfall 1) |
| A5 | Die erwartete Grundlast von rund 118 bis 150 MB ist aus der amd64-Nachmessung des faulen Baus (575,0 MB Ersparnis) und der arm64-Grundlast (693,4 MB) **gerechnet**, nicht gemessen | Vergleichsmatrix | Nur eine Erwartung, die der Plan als Plausibilitätsschwelle benutzen kann. Eine gemessene Grundlast von 690 MB würde bedeuten, dass der faule Bau auf der Box nicht greift, und das wäre der wichtigste Befund des Laufs |
| A6 | Der Lauf ist mit 22 bis 26 Stunden ausreichend bemessen. Die 3 Stunden Nebenzeit sind aus der Nachmessung (1,95 h für Anfahrt, Grundlast, Spitze, Lastreihe, OCR-Charge und Neustart-Drill) plus den Zusatzblöcken dieser Phase geschätzt | Kosten und Laufzeit | Kostendeckel. Vorschlag 30 h enthält vier Stunden Reserve |
| A7 | Die zehn Sprachfälle sind auf der Box mit einem eigenen Nutzer fahrbar. Der Weg ist plausibel (WebDAV-Upload wie in `71-ocrphase.sh`, ACL-Trennung wie im CI-Kollegenfall), aber diese Kombination ist nie gefahren worden | Offene Frage 2 | Ein Fall wird rot, weil ein Wort doch in einer zweiten Datei steht. Der Plan sollte die Fälle als eigenen, abbrechbaren Block führen, nicht als Vorbedingung für den Bericht |
| A8 | Die Cloudflare-Zone für `loadtest.infranode.dev` ist die Zone des Owners und er kann den A-Record setzen. Der Hinweis "CF-A-Record" steht in `box.env`, die Zugangsdaten lagen am 07.09. nicht vor | Offene Frage 4 | Rückfall auf den `/etc/hosts`-Pin, mit Pitfall 7 als bekanntem Preis |
| A9 | Die Preissätze gelten noch. Sie sind aus der Preisliste vom 01.09.2026 festgenagelt und durch zwei Läufe bestätigt, aber Preise ändern sich | Kosten und Laufzeit | Die Kostenzahl im Bericht wäre falsch. `aws_box.sh prices` nennt den Befehl, der sie reproduziert, und der Bericht sollte das Abfragedatum tragen |
| A10 | Die Box ist noch da und noch gestoppt. Festgestellt am Morgen des 07.09. per API; danach ist sie **nicht mehr angefasst** worden, und diese Recherche hat sie ebenfalls nicht angefasst | ganze Recherche | Der Plan beginnt mit `aws_box.sh status`, und dessen Antwort ist die erste Messung, nicht eine Bestätigung dieser Annahme |

---

## Sources

### Primär (HIGH)

- `docs/measurements/2026-09-05-semantiklauf-m7g/README.md` , die v1.0-Baseline, vollständig gelesen
- `docs/measurements/2026-09-nachmessung-m7g/README.md` , der bereits gefahrene Zeile-für-Zeile-Vergleich, vollständig gelesen
- `docs/measurements/2026-09-grundlast-fein/README.md` , die Zerlegung der Grundlast und die Nachmessung des faulen Baus, vollständig gelesen
- `docs/measurements/2026-09-seitenbudget/README.md` , die Zahlen der Ergebnisseite samt Nachtrag 6.3, Abschnitte 2 bis 6.3 gelesen
- `docs/performance.md` , Abschnitte "Stand dieses Berichts" (111), "Welcher Codestand" (839), "Die Begleit-App" (927), "Wo der Speicherunterschied anfällt" (3432), "Zwei Befunde über die Zeitkette" (3449), "Der grösste Posten der Grundlast" (3511), "Der dritte Verbleib" (3766)
- `scripts/ops/aws_box.sh` , Modulkopf, Preissätze, `cmd_start`, gelesen
- `scripts/ops/search_load.py`, `rss_sampler.sh`, `rss_digest.py` , Modulköpfe und Schnittstellen gelesen
- `.github/workflows/integration.yml` Zeilen 1039 bis 1600 , die zehn Sprachfälle und die Korpus-Dateinamen
- `.github/workflows/docker.yml` Zeilen 1 bis 60 und 480 bis 560 , Trigger, Pfadfilter, Manifest- und Attestierungsprüfung
- `.github/workflows/measure.yml` Zeilen 1 bis 80 , der arm64-Matrixast auf `ubuntu-24.04-arm`
- `.planning/phases/07-gemeinsame-embedding-engine/deferred-items.md` , DI-07-01 bis DI-07-04, vollständig gelesen
- `.planning/phases/09-eigene-ergebnisseite/09-08-SUMMARY.md` , Befund M-03, T-09-29, "Notes for Future Phases"
- `.planning/milestones/v1.0-phases/06.1-.../06.1-18-PLAN.md` , die Checkpoint-Form des Vorläuferplans
- `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/config.json`, `CLAUDE.md`
- `testdata/CORPUS.md` , die vier Aufgaben des 39-Dateien-Referenzkorpus
- Selbst gefahrene Feststellungen: `git status -sb`, `git rev-list --left-right --count origin/main...HEAD`, `git log -- backend/`, `git log -- php/`, `git diff --stat 2c1b741 HEAD -- backend/ php/`, `gh run list --workflow=docker.yml`, `gh run list --workflow=integration.yml`, Baumhashes beider Hälften nach dem Rezept aus `40-abbild.sh`, Zeilenenden von drei Messskripten, `git check-attr text eol`, `grep -ri baumhash rohdaten/`, Schlüsselliste aus `~/.findling-loadtest/box.env` (ohne Werte), Existenz von `~/.findling-aws.env`

### Sekundär (MEDIUM)

- `~/.findling-loadtest/box.env`, Protokollteil , die Laufhistorie, der Hinweis auf die Cloudflare-Zone, die Passwortablage auf der Box, "20,5 h gleich 2,37 USD". Zustandsdatei aussserhalb des Repos, damit nicht gegen den Repo-Stand prüfbar
- `scripts/dev/build_load_corpus.py` , die Wortliste des Lastkorpus, gegen die die Sprachfälle brechen würden
- `backend/tests/test_corpus_terms.py`, `backend/tests/test_ops_scripts.py`, `backend/tests/fixtures/compound_cases_de.txt` , die Gates, die die Zusagen tragen
- `php/lib/Command/IndexCommand.php` , `findling:index --restart`, Beschreibung und Bestätigungsabfrage
- `backend/appinfo/info.xml`, `php/appinfo/info.xml` , Version 1.0.3, `<image-tag>1.0.3</image-tag>`, Versionsfenster 33 bis 35
- `.gitattributes` , die fehlende Regel für `docs/measurements/**/skripte/*.py`

### Tertiär (LOW, markiert zur Prüfung)

- Der laufende Zustand der Box, der Digest von `:dev` in ghcr und der Inhalt des Datenträgers. **Kein Cloud-Kontakt in dieser Recherche.** Alle Aussagen dazu stammen aus Repo-Dokumenten vom 07. bis 09.09.2026 und sind vom Plan als erster Schritt nach der Anfahrt neu festzustellen

---

## Metadata

**Konfidenz im Einzelnen:**

- Bestandsaufnahme im Repo (Skripte, Berichte, Baseline-Zahlen, Baumhashes, CI-Stand): **HIGH** , jede Zahl aus einer gelesenen Datei oder selbst gefahren
- Struktur des zu spiegelnden Berichts: **HIGH** , die Nachmessung sagt selbst, welchen Bericht sie spiegelt
- Die gefundenen Fallstricke: **HIGH** für 1 bis 3 und 8 bis 12 (in Rohdaten und Dateien belegt), MEDIUM für 4 bis 7 (aus Berichtsprosa der Vorläufer)
- Laufzeit und Kosten: **MEDIUM** , die Sätze sind festgenagelt und durch zwei Läufe bestätigt, die 19 Stunden sind eine Übertragung aus 06-11 (A1)
- Zustand der Box: **LOW** , bewusst nicht angefasst
- Erwartete v1.1-Zahlen: **LOW** , gerechnet, nicht gemessen (A5). Ausdrücklich als Erwartung und nicht als Messung ausgewiesen

**Recherchedatum:** 2026-09-09
**Gültig bis:** rund 14 Tage für die Repo-Bestandsaufnahme. Für den Zustand der Box: **bis zum ersten `aws_box.sh status`**, danach gilt dessen Antwort. Für die Preissätze: bis zur nächsten Preisliste, das Abfragedatum gehört in den Bericht.
