# Aufgeschobene Befunde der Phase 11

Befunde, die während der Ausführung dieser Phase aufgefallen sind und außerhalb
des Plans lagen, in dem sie aufgefallen sind, oder die nicht klein genug für
eine Behebung im selben Lauf waren. Kein Fix hier, nur der Befund, warum er
nicht dort behoben wurde, und der Ort, an den er gehört.

Klein heißt in dieser Phase: keine Änderung an der Berechtigungskette, keine
Änderung am Suchweg, keine Änderung an einer Konstante, die jeden Nutzer
betrifft, und der Fix passt in denselben Lauf, in dem er gefunden wurde. Dazu
kommt eine harte Nebenbedingung, die diese Phase von Phase 10 geerbt hat: **jede
Nacharbeit an einer Messung kostet eine neue Anfahrt der Box, eine neue Freigabe
und Geld**, und die Box ist seit dem 10.09.2026 angehalten. Ein Befund, der eine
zweite Messung braucht, ist deshalb nie klein.

**Jeder Eintrag unten trägt sein Verdikt aus dem Audit der Phase**
(`docs/audits/2026-09-phase-11/README.md`, 11.09.2026) mit seiner Kennung, damit
kein Befund an zwei Stellen zwei Antworten bekommt.

---

## DI-11-01 (gefunden in Plan 11-06, Task 3): die Vorprüfung des Fremdbestands misst einen Antwortdeckel und nicht den Bestand

**VERDIKT 11.09.2026: LOW, weitergereicht, und mit DI-10-02 zusammengelegt**
(Audit L-08). DI-10-02 bleibt damit ausdrücklich offen.

**Gefunden:** beim Messblock B der Box-Anfahrt, als das Sprachfall-Skript mit
Rückgabewert 17 endete und kein einziger Fall als nicht messbar galt.

**Was:** Die Nachfolgefassung `98b-sprachfaelle.sh` (Plan 11-03) prüft vor den
zehn Fällen, wie viel Fremdbestand einem Begriff im Weg steht, und vergleicht
diese Zahl mit der Schwelle 64 (`MAX_RECHECKS_ABSOLUTE`). Auf der Mess-Box
liefert die OCS-Route jedem geprüften Begriff exakt **26** Treffer, bei Tiefe
64, 200 und 2000 gleichermaßen, und exakt 6 bei Tiefe 5. Die Zahl hängt weder
am Begriff noch an der Tiefe
(`docs/measurements/2026-09-werkzeugfixe/rohdaten/07-fremdbestand-gegenprobe.txt`).

Damit kann die Messgröße die Schwelle nie überschreiten, das dreiwertige
Urteil bleibt praktisch zweiwertig, und die vier Fälle 1, 2, 4 und 6 sind rot
wie am 10.09.2026. Die Bilanz `6 von 10, davon 0 nicht messbar` ist zahlengleich
mit der des 10.09.

**Was der Fix trotzdem gebracht hat:** drei der vier Zusagen halten. Jeder
Begriff trägt seine Fremdbestandszahl in einer eigenen Zeile, die Bilanzzeile
nennt zwei Zahlen statt einer, und `CI_LAUF` ist Pflichteingabe, deren Fehlen
den Lauf vor dem ersten Fall beendet.

**Warum nicht dort behoben:** Ein Messskript, das während seines eigenen Laufs
nachgebessert wird, macht jede Zahl daneben unbelegt. Die Änderung ist außerdem
keine Messung, sondern eine Änderung an der Messgröße, und sie braucht eine
eigene Überlegung: gezählt gehört die Zahl der Dokumente im Index, die den
Begriff tragen, und nicht die Zahl der Treffer, die die Route herausgibt. Ob
diese Zahl ohne Eingriff in die Berechtigungskette überhaupt erhebbar ist, ist
offen, und genau diese Frage darf unmittelbar vor einer Store-Abgabe nicht
nebenbei beantwortet werden.

**Wohin es gehört:** ein eigener Plan, ohne Box, in der v1.2-Härtung, gemeinsam
mit **DI-10-02**, dessen Frage dieselbe ist. Der Beweis mit eigenem Index liegt
weiterhin in `integration.yml`, Job `index-search-e2e`, zuletzt Lauf
**34530208024**, und dieser Lauf fährt dieselben zehn Fälle ohne Fremdbestand.

---

## DI-11-02 (gefunden in Plan 11-06, Task 2): eine leere Antwort ohne Protokollspur

**VERDIKT 11.09.2026: LOW, weitergereicht, ohne Zusatzmessung beantwortbar**
(Audit L-09).

**Gefunden:** beim Aufrechnen der beiden Zählungen von Messblock A.

**Was:** Die Kontrollstufe 8 meldet neun Fehlschläge. Acht davon gehen auf den
Begriff `Mahnung`, der im Lastkorpus keinen Treffer trägt. Der neunte bleibt
offen: das Nextcloud-Protokoll trägt im Fenster der Stufe 8 und eine Minute
darüber hinaus keine einzige Zeile der Apps `findling` oder `app_api`
(`docs/measurements/2026-09-werkzeugfixe/rohdaten/03-nc-protokoll-abbrueche.txt`).
Diese eine Anfrage bekam also eine leere Ergebnisgruppe, ohne dass irgendwo ein
Abbruch entstand.

**Vermutung, als Vermutung beschriftet:** DI-07-03, die Kandidatenschleife holt
keine zweite Runde nach, und der Rechteabgleich verwirft unter Last die
Kandidaten einer Runde vollständig. Nachgewiesen ist das nicht.

**Was diese Vermutung prüfbar macht:** Plan 11-13 hat am 10.09.2026 genau
diesen Fall mit einem eigenen Zustand versehen,
`SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED`, der statt einer leeren Liste
einen Satz zurückgibt. Die Box trug diesen Stand nicht, weil sie seit dem
10.09. angehalten war und kein neues Abbild bekommen hat. Ein Lauf mit dem
neuen Companion würde die Frage ohne Zusatzmessung beantworten: trägt die
Antwort den Satz, war es DI-07-03; bleibt sie leer, war es etwas anderes.

**Warum nicht dort behoben:** Die Anfahrt hatte den Auftrag, zwei Werkzeug-Fixe
zu beweisen, und sonst nichts. Ein einzelner Vorgang unter 80 trägt keine
Aussage.

**Warum das Audit ihn nicht schließt:** einer von 80, ohne Protokollspur, gegen
acht erklärte Fälle derselben Stufe. Das Audit kann die Vermutung weder
bestätigen noch widerlegen, und ein Verdikt "war DI-07-03" wäre eine Behauptung.

**Wohin es gehört:** der nächste Box-Lauf, in der v1.2-Messplanung, als eine
Zeile im Ablaufplan und nicht als eigener Messblock.

---

## DI-11-03 (gefunden in Plan 11-06, Task 2): der neue Zähler unterscheidet leer nicht von abgebrochen

**VERDIKT 11.09.2026: LOW, weitergereicht; im Audit geprüft, ob klein genug für
diesen Lauf, und ausdrücklich verneint** (Audit L-10).

**Gefunden:** beim Vergleich der Erwartung E3 mit dem Ergebnis.

**Was:** `EmptyResultGroup` zählt jede Antwort mit weniger als `--min-hits`
Treffern, gleich ob ein Containeraufruf abgebrochen ist oder ob die Suche
schlicht nichts gefunden hat. Auf Stufe 16 sind das 14 Abbrüche und 16 leere
Suchen in derselben Zahl 30. Der Name legt die erste Lesart nahe, und die
Erwartung E3 (`Stufe 8 zeigt failures == 0`) ist genau daran gescheitert.

**Warum das trotzdem kein Rückschritt ist:** `min_hits` und `hits_per_request`
stehen jetzt in jeder Rohdatei, also ist die Zahl lesbar statt stumm. Vorher
meldete das Werkzeug `"failures": 0`, während 17 Aufrufe abbrachen.

**Warum nicht in diesem Lauf behoben, und der Grund ist technisch und nicht
terminlich:** das Werkzeug **kann** die beiden Ursachen aus seiner eigenen Sicht
nicht trennen. Die OCS-Route antwortet in beiden Fällen mit HTTP 200 und einer
Ergebnisgruppe ohne Containerteil; der Unterschied steht ausschließlich im
Nextcloud-Protokoll auf der anderen Seite. Ein zweiter Fehlschlagname wäre
deshalb ein Name ohne Unterscheidungsmerkmal, also eine Verschlechterung. Die
tragfähige Fassung nennt stattdessen die Begriffe ohne Treffer, und dafür muss
sie den Bestand kennen, gegen den sie läuft.

**Wohin es gehört:** die nächste Fassung von `scripts/ops/search_load.py`,
zusammen mit der v1.2-Messplanung, weil die Entscheidung zwischen den beiden
Wegen einen Bestand braucht, gegen den sie geprüft wird. Kein Blocker, keine
Box.

---

## DI-11-04 (gefunden in Plan 11-07): zwei Log-Artefakte hießen "harp-logs-stable34"

**BEHOBEN 11.09.2026 im Fix-Lauf des Audits, Commit `2e8502b`** (Audit L-06).
Dieser Eintrag bleibt stehen, damit die Herkunft des neuen Namens nachlesbar
ist, und ist **kein offener Punkt mehr**.

**Gefunden:** beim Ablegen der Upgrade-Beweisdateien in das Log-Artefakt von
`deploy-harp.yml`.

**Was:** Der Upload-Schritt nannte das Artefakt
`harp-logs-${{ matrix.server-version }}`. Seit Plan 11-04 gibt es zwei Äste mit
`server-version: stable34` (amd64 und arm64), also zwei Artefakte gleichen
Namens. Im Lauf 34546421219 sind es 13.833 Byte (der amd64-Ast, mit
`upgrade-before.json`, `upgrade-after.json`, dem Urteil von `occ upgrade` und
dem Containerprotokoll) und 7.825 Byte (der arm64-Ast). Der Upload schlägt
nicht fehl, beide liegen nebeneinander, aber wer "das Artefakt
harp-logs-stable34" herunterlädt, weiß nicht, welches der beiden er bekommt,
und genau in diesem Namen liegen seit 11-07 die Beweisdateien des
Upgrade-Blocks.

**Warum nicht in Plan 11-07 behoben:** Der Name war seit Plan 11-04 so, gehörte
dem Upload-Schritt und nicht dem Upgrade-Block, und die Regel jenes Plans war,
keinen bestehenden Schritt umzubauen.

**Wie entschieden:** der Runner gehört in den Namen, und der Upgrade-Block
bekommt **kein** eigenes Artefakt; die zweite Variante hätte den Beweis von den
Nachbardateien getrennt, die zu seiner Lesart gehören. Neue Form
`harp-logs-${{ matrix.server-version }}-${{ matrix.runner }}`. Der alte Name
bleibt für die Läufe gültig, die ihn geschrieben haben; der Kommentar am Schritt
sagt das.

**Gemessen statt behauptet**, Lauf **34557178548** auf Commit `4becbbc`, alle
vier Äste grün, und die Artefaktliste des Laufs:

```
harp-logs-stable34-ubuntu-24.04        13.823 Byte
harp-logs-stable34-ubuntu-24.04-arm     7.826 Byte
harp-logs-stable33-ubuntu-24.04         7.805 Byte
harp-logs-stable35-ubuntu-24.04         7.815 Byte
```

Vier Namen, vier Artefakte, keine Kollision. Das große ist das des amd64-Astes
und trägt die sieben Beweisdateien des Upgrade-Blocks; es ist jetzt an seinem
Namen zu erkennen und nicht mehr nur an seiner Größe.

---

## DI-10-04 (übernommen aus Phase 10, hier entschieden): die Ursache der Mehrlaufzeit ist eingegrenzt und nicht bewiesen

**VERDIKT 11.09.2026: LOW, dokumentiert weitergereicht** (Audit L-07). Phase 11
war die Zieladresse aus Phase 10, und dieser Eintrag ist die Antwort darauf: die
Frage wird nicht hier beantwortet, und die nächste Adresse steht unten.

**Was:** Der Volllauf brauchte 26 h 37 min gegen 18 h 56 min in 06-11, also plus
40,6 Prozent bei einem Mehrbestand von 0,29 Prozent. Zwei Kandidaten stehen
nebeneinander, und die Daten entscheiden nicht zwischen ihnen: die Kopplung der
beiden Spuren (Indexierung minus 30,9 Prozent, Einbettung minus 24,4 Prozent, im
Gleichschritt) und die Zulauf-Lücken (`vorrat=0` in 62 von 325 Lesungen).
Speicherdruck ist als Erklärung ausgeschlossen. Belegstelle:
`docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/00-ende.txt`.

**Warum nicht in dieser Phase behoben, mit den Zahlen:**

1. Die Frage entscheidet nur eine Messung, und die braucht einen neuen Volllauf:
   entweder ein Lauf, der die Einbettung erst nach der Indexierung anstößt, oder
   eine Instrumentierung, die die Wartezeit des Zulaufs mitschreibt. Beides ist
   eine neue Anfahrt, **26 Stunden und rund 3 USD**.
2. Der Deckel dieser Phase war **4 Stunden und 0,50 USD** (Freigabe der
   Werkzeug-Anfahrt, Plan 11-06). Die Frage passt nicht hinein, und zwar um eine
   Größenordnung.
3. Der Befund berührt kein Erfolgskriterium. Er ist eine Frage an den Durchsatz
   und nicht an die Speicheraussage, und er ist in
   `docs/measurements/2026-09-vergleichsmessung-m7g/README.md`, Abschnitt 19.2,
   als Verschlechterung benannt statt weggelassen.

**Wohin es gehört:** die **v1.2-Messplanung**, zusammen mit dem
Box-Wiederaufbau-Runbook, weil die Box seit dem 10.09.2026 angehalten ist und
jede Antwort auf diese Frage zuerst eine Box braucht. In derselben Anfahrt
gehören dazu: die Entscheidung über die vier regressiven Laststufen (Audit
L-04), DI-11-02 als eine Zeile im Ablaufplan und DI-11-03 als Fassung des
Lastwerkzeugs.

---

## DI-11-05 (gefunden in Plan 11-10, beim Nachsehen des CI-Stands): der pgsql-Ast von `index-search-e2e` flattert

**VERDIKT 11.09.2026: LOW, hingenommen als Flattern des Messaufbaus, mit
Zieladresse** (Audit L-11).

**Gefunden:** beim Nachsehen des CI-Stands der Phase, vor dem Abschluss des
Audits.

**Was:** Der Integration-Lauf **34555358815** auf Commit `2838673` ist rot, und
zwar in genau einem Job von sieben: `index-search-e2e (pgsql)`. `sqlite` und
`mysql` sind grün. Die Fehlerzeile lautet `curl: (22) The requested URL returned
error: 423` nach `revision 8 written`, im Schritt "Overwrite it eight times while
the container is working". **423 ist Locked**, also die WebDAV-Sperre von
Nextcloud.

**Warum es kein Produktbefund sein kann:** `2838673` ändert ausschließlich
`.planning/ROADMAP.md`, `.planning/STATE.md` und `11-09-SUMMARY.md`. Kein
ausführbares Zeichen hat sich gegenüber dem grünen Vorlauf bewegt.

**Die Gegenprobe, gefahren statt vermutet:** `gh run rerun 34555358815 --failed`
am 11.09.2026, Ergebnis **success**. In der Geschichte des Workflows ist das ein
roter Lauf auf dreizehn.

**Warum nicht hier behoben:** Der Schritt gehört `integration.yml` und nicht
diesem Plan, der Fix ist eine Warteschleife auf 423 statt eines blinden neunten
Schreibvorgangs, und eine Änderung an der Integrationsstrecke unmittelbar vor dem
Release-Tag ersetzt ein seltenes Flattern durch ein neues Risiko.

**Der Merker für Plan 11-11:** geht der pgsql-Ast auf dem Release-Commit rot, ist
die erste Handlung eine **Wiederholung** und nicht eine Fehlersuche im Erzeugnis.

---

## DI-11-06 (gefunden in Plan 11-11, im Upgrade-Beweis): die Suche kennt die Version des Containers nur vom Hörensagen

**VERDIKT 11.09.2026: offen, Zieladresse v1.2** (Owner-Entscheid vom selben Tag,
zusammen mit der Freigabe des Fixes unten).

**Gefunden:** im Upgrade-Beweis von `deploy-harp.yml`, der mit dem Versionsbump
auf 1.1.0 zum ersten Mal einen echten Minor-Sprung fuhr.

**Was:** `SearchService` entscheidet über eine Versionsdrift, ohne den Container
zu fragen. Gelesen wird `oc_appconfig.backend_app_version`, also die Antwort,
die der Container gegeben hat, als ihn zuletzt etwas gefragt hat. Das Einzige,
was ihn je fragt, ist die Einstellungsseite über `GET /status`; ein
`php/lib/BackgroundJob/` gibt es nicht.

**Was daraus in Plan 11-11 wurde:** Der Wert überlebte das App-Update und
beschrieb einen Container von vorher. Gemessen: Companion 1.1.0, Marke 1.0.3,
AppAPI meldet den Container als 1.1.0, und dreißig Kanariensuchen kamen leer
zurück. Behoben ist das durch die Migration
`Version001100Date20260911000000`, die die veraltete Marke verwirft statt sie zu
raten.

**Was offen bleibt:** Zwischen dem Update und dem ersten Öffnen der
Einstellungsseite hat die Suche keine Marke und damit kein Drift-Urteil. Das ist
kein Loch, das der Fix gerissen hat: Jede Instanz, deren Einstellungsseite nie
geöffnet wurde, steht seit jeher so da. Es ist aber ein Fenster, in dem ein
Nutzer, der nur eine Hälfte aktualisiert, Treffer über einen Protokollbruch
hinweg bekommen könnte.

**Der Weg, der es schließt:** die Version in der Antwort mitführen, die die Suche
ohnehin holt, statt sie getrennt zu erfragen. Dann ist die Marke bei jeder Suche
frisch und der Sonderfall verschwindet.

**Warum nicht in dieser Phase:** Das ist eine Protokolländerung an beiden
Hälften, drei Tage vor der Abgabe, und sie berührt genau den Pfad, auf dem der
gerade gefundene Fehler saß.

**Der Merker für die nächste Minor-Version:** Solange die Marke so gepflegt wird
wie heute, braucht **jeder** Minor-Sprung eine Migration nach dem Muster von
`Version001100Date20260911000000`. Der Satz steht auch im Klassenkommentar
dieser Migration, weil das die Datei ist, die jemand liest, wenn er die nächste
schreibt.
Erst wenn die Wiederholung ebenfalls rot ist, ist es ein Befund.

**Wohin es gehört:** die v1.2-Härtung, als kleiner Schritt am Mutationsblock von
`integration.yml`.

---

## Geprüft und ausdrücklich kein Befund

Diese Kandidaten sind geprüft worden, weil sie sich aus dem Audit dieser Phase
anboten, und sie sind **kein** Eintrag hier:

- **T-09-29, der volle Vektorscan je Anzeigeseite.** Anderswo entschieden: in
  Phase 10, mit `accept` und mit Zahlen (tiefe Seite 0,333 s gegen erste Seite
  0,332 s, der Scan läuft einmal je Anfrage und nicht je Seite). Das Audit der
  Phase 11 übernimmt diesen Entscheid unverändert (L-03) und gibt ihm keine neue
  Adresse. Belegstellen:
  `.planning/phases/10-vergleichsmessung-auf-der-aws-box/10-07-SUMMARY.md` und
  `docs/audits/2026-09-phase-10/README.md`, Abschnitt 3. Wiedervorlage bei einem
  Vektorbestand deutlich über 146.171 Chunks.
- **DI-10-05, der aufgeschriebene Digest von `:dev`.** Anderswo entschieden und
  **vollzogen**: das Audit dieser Phase hat ihn als L-05 entschieden, und der
  Entscheid steht im Kopf von `.github/workflows/measure.yml` (Commit
  `ab39d37`). Ein Eintrag hier wäre ein offener Punkt, den es nicht mehr gibt.
- **DI-07-02, die Aufrufdecke von 1,5 s.** Gehört Phase 7 und steht dort. Das
  Audit dieser Phase entscheidet ihn als LOW mit Wiedervorlagebedingung (L-02);
  ein zweiter Eintrag an zweiter Stelle wäre genau der Widerspruch, den die
  Audits dieses Projekts sonst aufschreiben.
- **DI-07-03, die Kandidatenschleife.** Ebenfalls Phase 7, und in dieser Phase
  **gebaut**: Plan 11-13, Audit M-01, Belegstelle `11-13-SUMMARY.md`. Kein
  offener Punkt.
- **DI-10-02, der Messaufbau der Sprachfälle.** Er steht in
  `.planning/phases/10-vergleichsmessung-auf-der-aws-box/deferred-items.md` und
  bleibt dort offen. Phase 11 hat ihn angefasst, und ihr Ergebnis steht oben
  als **DI-11-01**; die beiden sind im Audit zu **L-08** zusammengelegt. Ein
  dritter Eintrag würde die Frage ein drittes Mal stellen.
- **Der neue Satz auf der Ergebnisseite als Existenz-Orakel über den
  Fremdbestand.** Im Audit als L-01 benannt und hingenommen, mit vier
  Feststellungen und einer Wiedervorlagebedingung. Er ist kein Befund außerhalb
  eines Plans, sondern die benannte Nebenwirkung eines Owner-Entscheids (v1-a
  vom 10.09.2026), und er gehört deshalb in den Auditbericht und nicht hierher.
- **Der Versionsbump an drei Stellen.** Kein Befund, sondern der Auftrag von
  Plan 11-11: `php/appinfo/info.xml`, `backend/appinfo/info.xml` und der
  `<image-tag>` daneben stehen heute alle drei auf `1.0.3`, und `docker.yml`
  bricht einen Tag-Lauf ab, wenn sie nach dem Bump nicht übereinstimmen.
- **Die vier Dateien `findling.tar.gz`, `findling_backend.tar.gz`,
  `findling.crt` und `findling_backend.crt` im Wurzelverzeichnis.** Geprüft,
  weil sie wie Release-Artefakte im Repositorium aussehen. `git ls-files` kennt
  keine von ihnen, `git log --all` nennt über keinen der vier Namen einen
  Commit, und `.gitignore` deckt sie mit `*.tar.gz` (Zeile 31) und `*.crt`
  (Zeile 5). Überbleibsel einer Handprobe, kein Befund.

---

## Aus Plan 11-12 (Snapshot und Abbau, 11.09.2026)

- **Die Durchsicht des geretteten Systemplatten-Materials auf Geheimnisse.**
  Beim Abbau der Box hat sich gezeigt, dass `/home/ubuntu/work` die gefahrenen
  Skripte und Protokolle der Phasen 5, 6 und 6.1 trägt und dass **kein
  Gegenstück im Repositorium existiert**: das älteste Messverzeichnis
  `docs/measurements/2026-09-04-volllauf-m7g/` führt kein `skripte/`. Das
  Material ist vor dem Abbau gesichert worden, aber **außerhalb** des
  Arbeitsbaums, unter
  `C:/Users/Student/.findling-loadtest/systemplatte-2026-09/` (435 Einträge,
  3.971.065 Byte, sha256 `fad3e7ce...`). Warum nicht ins Repositorium: dieses
  Repositorium ist öffentlich, und Protokolle einer Testinstanz brauchen vor
  einer Veröffentlichung eine eigene Durchsicht auf Zugangsdaten, Adressen und
  Sitzungsmarken. Das ist eine eigene Arbeit und war nicht der Auftrag von
  11-12. Gehört in die v1.2-Messplanung, zusammen mit dem
  Wiederaufbau-Runbook.
- **Die vier Dateien `99-reihe-a..d.txt.codes` der Vergleichsmessung.** Sie
  lagen nur auf der Box und belegen, dass alle 80 Antworten der vier
  Seitenbudget-Reihen HTTP 200 waren, also gemessene erfolgreiche Seitenaufrufe
  und keine Fehlerseiten. Der Bericht der Phase 10 sagt das so nicht. Inhalt und
  Zählung stehen jetzt in
  `docs/measurements/2026-09-werkzeugfixe/rohdaten/07-snapshot-und-abbau.txt`,
  Abschnitt 4b; die Dateien selbst liegen in der lokalen Sicherung. Eine
  Aufnahme in das abgenommene Messverzeichnis der Phase 10 wäre eine Änderung an
  einem abgeschlossenen Beleg und ist deshalb nicht ohne Entscheid erfolgt.
- **Wiedervorlage Snapshot `snap-03f1d1d9ad9262704`, nach der v1.2-Messung.**
  Auflage des Betreibers vom 11.09.2026: der Snapshot bleibt dauerhaft, weil die
  v1.2-Messung ihn braucht. Danach ist zu entscheiden: löschen (2,79 bis 2,99
  USD je Monat gespart) oder in die Archivstufe legen (rund 0,70 USD je Monat,
  dafür 90 Tage Mindestlaufzeit, rund 1,67 USD je Abruf und Stunden bis Tage
  Wartezeit).
- **Der A-Record `loadtest.infranode.dev` zeigt ins Leere.** Die Box ist
  abgebaut, der Eintrag bleibt als Merkposten stehen. Kein Befund, sondern eine
  Feststellung: er kostet nichts, er verweist auf nichts, und beim nächsten
  Aufbau ist er neu zu setzen.
