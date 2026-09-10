# Phase 11: Vorentscheide V-1 und V-2

**Angelegt:** 2026-09-10 (Plan 11-01, Task 1)
**Zweck:** Zwei Fragen stehen vor der Arbeit dieser Phase und nicht in ihrer
Mitte. Beide veraendern, was spaetere Plaene bauen, und beide sind
Owner-Fragen. Diese Datei stellt die Beleglage bereit und traegt nach dem
Checkpoint die beiden Entscheide woertlich mit Datum. Die Folgeplaene zitieren
die Optionskennung (v1-a, v1-b, v2-a, v2-b) und keine Zusammenfassung.

---

## V-1, DI-07-03: in dieser Phase fixen oder dokumentiert als LOW entscheiden

### Was festgestellt ist

Der Messteil von DI-07-03 ist seit 10.09.2026 geschlossen
(`.planning/phases/07-gemeinsame-embedding-engine/deferred-items.md`, Abschnitt
DI-07-03, gemessen in Plan 10-06, Schritt 12):

| Fall | Runden je Suche | Containeraufrufe je Suche | Treffer | p50 | p95 | Marge zu 2.500 ms |
|---|---:|---:|---:|---:|---:|---:|
| 1, der Alltag | 1,0 | 1,9 (10 Kandidaten-, 9 Snippetaufrufe) | 54 | 589,4 ms | 683,6 ms | 1.816,4 ms |
| 2, provozierter Driftfall | 1,0 | 1,0 | 0 | 444,2 ms | 681,6 ms | 1.818,4 ms |

Der gerechnete Worst Case von vier Aufrufen gegen ein Gruppenbudget ist im
Alltag nicht eingetreten. Offen ist nicht die Laufzeit, sondern das Verhalten:

- Die Kandidatenschleife ueber `MAX_ROUNDS = 3`
  (`php/lib/Search/Provider.php:70`, verwendet in `caps()` ab
  `php/lib/Search/Provider.php:232`) holt **keine zweite Runde nach**, auch dann
  nicht, wenn der Recheck alle Kandidaten der ersten Runde verworfen hat.
- Auf einer Instanz mit grossem Fremdbestand findet ein Nutzer mit wenigen
  Dateien seine eigenen deshalb nicht, sobald seine Begriffe im Fremdbestand
  haeufig sind. Fuer **drei von vier** geprueften Begriffen kam die Datei des
  fragenden Kontos unter den ersten **2.000** Kandidaten eines **52.111er**
  Fremdbestands nicht vor. Belegstelle:
  `docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/98b-sprachfaelle-diagnose.txt`.
- Der Nutzer sieht in diesem Fall eine **leere Liste und keine Meldung**. Das
  ist der Befund hinter den vier roten Sprachfaellen der Vergleichsmessung und
  Punkt 5 der Liste "Was dieser Lauf nicht besser gemacht hat".

### Was unklar ist

Ob das ein MEDIUM-Befund ist, der nach der Owner-Regel vom 15.08.2026 vor dem
Phasenabschluss faellt, oder ein LOW, der dokumentiert entschieden wird. Der
naheliegende Fix (mehr Runden, groesseres Kandidatenfenster) fasst den
Rechteabgleich an, und genau das ist verboten.

### Die Leitplanke, die fuer beide Optionen gilt

`.planning/ROADMAP.md:25` sagt: *"Die Berechtigungskette bleibt unveraendert
(SQLite-ACL-Vorfilter im Container, finaler PHP-Recheck als Grenze). Keine Phase
dieses Milestones darf eine zweite Grenze aufmachen."* **Beide unten stehenden
Optionen halten das ein.** Option a fuegt einen Zustand und einen Text hinzu und
ruehrt weder `MAX_ROUNDS` noch den Recheck an; Option b aendert keinen Code.

### Option a: MEDIUM mit Abhilfe in dieser Phase

Der Dienst unterscheidet "es gab keine Kandidaten" von "es gab Kandidaten, und
der Recheck hat alle verworfen". Die Ergebnisseite sagt im zweiten Fall einen
Satz statt einer leeren Liste, und der Suchdialog unterscheidet den Zustand in
seiner Ablaufspur, ohne einen Eintrag zu erfinden (ein Eintrag im Dialog waere
ein Treffer, der keiner ist; so haelt es das Produkt schon fuer die vier
vorhandenen Gruende). Technisch ist das ein zusaetzlicher Zustand im
Ergebnisobjekt und **EIN** neuer Uebersetzungsschluessel. Keine zweite
Berechtigungsgrenze, keine Aenderung an `MAX_ROUNDS`.

**Kosten:** Der Katalog steigt von **173 auf 174** Schluessel
(`docs/l10n-french.md`, Abschnitt "Bedingung, unter der der franzoesische
Katalog kommt", Punkt 1: massgeblich ist die Schluesselmenge von
`php/l10n/de.json`, heute 173). Dieser eine Schluessel muss in **alle sechs
Katalogdateien**, also in `de.json`, `de.js`, `de_DE.json`, `de_DE.js` und in
die beiden neuen `fr.json` und `fr.js`. Damit liest ihn auch die franzoesische
Abnahme des Owners (D-07, FR-GATE) mit.

**Wer es baut:** **Plan 11-13** in Welle 2. Er ist bereits geschrieben und
bedingt gestellt (`.planning/ROADMAP.md:238`). Er laeuft nur bei diesem
Entscheid und wird bei Option b dokumentiert uebersprungen. Option a loest also
**keine Nachplanung** aus.

**Vorschlag fuer den Wortlaut**, damit der Owner etwas Konkretes bestaetigt
statt etwas Gedachtes:

- englischer Quellstring: `Other files contain this word, but none that you may open.`
- deutscher Wortlaut: `Andere Dateien enthalten dieses Wort, aber keine, die Sie öffnen dürfen.`

Ohne Prozent-Direktive, damit das Platzhalter-Gate von Plan 11-08 nichts Neues
zu pruefen bekommt. Der Owner darf ihn ersetzen; was er nennt, gilt.

### Option b: LOW dokumentiert entschieden

Kein Code. Ein Eintrag im Phase-11-Audit mit den Zahlen oben und der
Wiedervorlagebedingung. Plan 11-13 wird dokumentiert uebersprungen, Plan 11-10
entscheidet den Befund als LOW.

**Kosten:** Der Nutzer bekommt in v1.1.0 weiterhin eine leere Liste statt einer
Meldung. Die Owner-Regel vom 15.08.2026 verlangt, dass MEDIUM vor dem
Phasenabschluss faellt, also ist die LOW-Einstufung selbst Teil des Entscheids
und nicht eine Folge davon.

### Wer auf die Antwort wartet

| Plan | Wartet worauf |
|---|---|
| 11-13 (Welle 2, bedingt) | Laeuft nur bei v1-a; baut Zustand, Ergebnisseite und den 174. Schluessel |
| 11-05 | Uebersetzt 173 oder 174 Schluessel ins Franzoesische |
| 11-08 | Prueft den Katalog gegen 173 oder 174 Schluessel |
| 11-10 | Traegt den Befund als MEDIUM-gefixt oder als LOW-entschieden ins Audit |

**Empfehlung (Empfehlung, kein Entscheid):** Research empfiehlt Option a, also
MEDIUM mit der von der Berechtigungskette getrennten Abhilfe
(`11-RESEARCH.md`, Abschnitt 5.3 und Open Question 3).

### Entscheid

**Entscheid 2026-09-10: v1-a.** DI-07-03 wird in v1.1.0 gefixt, als MEDIUM mit
der von der Berechtigungskette getrennten Abhilfe. Plan 11-13 ist damit scharf
und faehrt in Welle 2. Der Katalog steigt von 173 auf 174 Schluessel.

Der Owner hat keinen eigenen Wortlaut genannt, also gilt der Vorschlag aus dem
Dossier woertlich als der geltende Wortlaut des neuen Katalogschluessels:

- englischer Quellstring: `Other files contain this word, but none that you may open.`
- deutscher Wortlaut: `Andere Dateien enthalten dieses Wort, aber keine, die Sie öffnen dürfen.`

Plan 11-13 schreibt den Schluessel ins Template und in die vier deutschen
Kataloge, Plan 11-05 uebersetzt ihn ins Franzoesische, Plan 11-08 prueft den
Katalog gegen 174 Schluessel, Plan 11-10 traegt DI-07-03 als MEDIUM-gefixt ins
Audit.

---

## V-2, Lesart von D-11 gegen den Codebestand

### Was festgestellt ist

D-11 (`11-CONTEXT.md`, 10.09.2026 nach Research) sagt woertlich: *"Das
Versionsfenster von v1.1.0 bleibt bei max Nextcloud 34 (NC 35 ist rc4)."*

Der Codebestand sagt etwas anderes:

- `php/appinfo/info.xml:207` und `backend/appinfo/info.xml:219` tragen seit
  E-H1 vom 06.09.2026 beide `<nextcloud min-version="33" max-version="35"/>`.
- `.github/workflows/deploy-harp.yml` faehrt genau die drei Aeste `stable33`,
  `stable34` und `stable35` (Include-Liste ab Zeile 138).
- Der 35er-Ast steht auf `tolerate-failure: true`
  (`deploy-harp.yml:187`), mit einem Kommentarblock, der **RE-CHECK DATE:
  2026-09-16** nennt und als nachverfolgenden Plan "die Store-Einreichung"
  benennt, also diese Phase.
- `backend/tests/test_lockstep_versions.py` haelt Fenster und Matrixliste in
  beide Richtungen zusammen
  (`test_the_window_stands_in_both_halves_and_the_matrix_runs_exactly_it`,
  `test_a_promised_version_that_nobody_runs_is_reported`). Ein Fenster, das sich
  in nur einer Datei bewegt, geht rot.
- Nextcloud 35 ist am 10.09.2026 Vorabversion: neueste 35er-Marke ist
  `v35.0.0rc4`, als Prerelease gekennzeichnet; neueste echte Freigabe ist
  `v34.0.4`.
- Der 35er-Ast lief am 07.09.2026 schon einmal gruen, Lauf **34114937751**, alle
  drei Aeste success.

### Was unklar ist

Ob D-11 als Feststellung ueber den Bestand gemeint war (dann steht sie neben dem
Bestand falsch und die Lesart ist zu bestaetigen) oder als Anweisung, das
ausgelieferte Fenster woertlich auf 34 zu senken (dann aendern sich Metadaten
unmittelbar vor der Abgabe).

### Option a: Fenster bleibt unveraendert bei 33 bis 35

Nichts an den beiden `info.xml`. Der `stable35`-Ast bleibt mit
`tolerate-failure: true` stehen, der RE-CHECK am 16.09. bleibt eigener
Merkposten, und die Einreichung wartet nicht darauf (das deckt sich mit D-10:
so frueh wie moeglich einreichen).

**Kosten:** Keine Aenderung an ausgelieferten Metadaten, keine Aenderung an
Workflow oder Lockstep-Test. Die Option weicht vom Wortlaut von D-11 ab und
braucht deshalb genau diese Bestaetigung. Es ist die Lesart, die Research
empfiehlt, und die einzige, die ohne Aenderung an ausgelieferten Metadaten
auskommt.

### Option b: Fenster woertlich auf max-version 34 senken

Zu aendern:

1. `php/appinfo/info.xml` (Zeile 207), Fenster auf `max-version="34"`
2. `backend/appinfo/info.xml` (Zeile 219), dasselbe
3. `.github/workflows/deploy-harp.yml`, den `stable35`-Matrixeintrag samt
   Kommentarblock entfernen
4. `backend/tests/test_lockstep_versions.py` nachziehen
5. `docs/store-listing.md` und die drei READMEs auf die genannte Serverversion
   durchsehen

**Kosten:** Eine Bestandsinstanz auf NC 35 bekaeme v1.1.0 nicht mehr angeboten.
Der einmal gruene 35er-Lauf 34114937751 faellt aus der Beleglage, weil der Ast
nicht mehr faehrt. Vier Dateien und ein Matrixeintrag aendern sich unmittelbar
vor der Abgabe, und nach dem Tag v1.1.0 ist der Store-Eintrag nicht mehr
editierbar.

### Wer auf die Antwort wartet

| Plan | Wartet worauf |
|---|---|
| 11-04 | Aendert die Matrix von `deploy-harp.yml` und zieht den Lockstep-Test nach |
| 11-11 | Setzt den Versionsbump und damit die ausgelieferten `info.xml` |

**Empfehlung (Empfehlung, kein Entscheid):** Research empfiehlt Option a, also
Fenster unveraendert bei 33 bis 35, mit ausdruecklicher Wiedervorlage am
16.09.2026 (`11-RESEARCH.md`, Open Question 2).

### Entscheid

**Entscheid 2026-09-10: v2-a.** Das Versionsfenster von v1.1.0 bleibt
unveraendert bei `min-version="33" max-version="35"`. Beide `info.xml` bleiben
wie sie sind, der `stable35`-Matrixeintrag in `deploy-harp.yml` bleibt mit
`tolerate-failure: true` stehen, `test_lockstep_versions.py` bleibt
unveraendert. Der RE-CHECK am 16.09.2026 bleibt eigener Merkposten, und die
Einreichung wartet nicht darauf (D-10). D-11 ist damit in der Lesart
bestaetigt, die den Codebestand beschreibt und nicht das Fenster senkt; ein
spaeteres 1.1.x hebt das Fenster, wenn 35 final ist.

Fuer die wartenden Plaene heisst das: Plan 11-04 laesst die Matrix von
`deploy-harp.yml` unveraendert und haelt nur die Wiedervorlage fest, Plan 11-11
setzt den Versionsbump ohne Aenderung am Fenster.
