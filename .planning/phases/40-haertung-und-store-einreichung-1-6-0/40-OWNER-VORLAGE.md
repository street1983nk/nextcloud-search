# Phase 40: Owner-Vorlage Abnahme Findling 1.6.0 (eine Runde)

Stand: 29.10.2026, 11:30 Uhr

Antwort "wie empfohlen" übernimmt jede Empfehlung; Abweichungen als "A2 b" nennen. Nicht genannte Punkte gelten als wie empfohlen. Bei einem eigenen Wortlaut bitte en, de und fr nennen.

Ehrlich vorab: die Sichtung der Sätze in einer laufenden Instanz ist remote und ohne lokales docker nicht möglich. Diese Runde legt Texte, Diffs und CI-Belege vor; die UI-Sichtung ist ein Owner-Punkt nach dem Release (Abschnitt "Nach dem Release"). Nichts ist getaggt, nichts eingereicht.

## Schon entschieden, nur protokolliert (keine Frage)

- 28.10.2026: 1.6.0 wird verzögert und trägt das Fix-Paket zu Issue #36 (Plan 40-06); die Frage nach einem 1.6.1 entfällt.
- 29.10.2026: kein PHP-404 bei kaputten Share-Mounts; das Gateway bleibt im budachst-Fall bei 500 (E-40-06-03 gestrichen, Regressionstest "500, ausdrücklich nicht 404").
- 29.10.2026: gehäufte gleiche Fehler eskalieren ohne Gutschrift (W-1 der Verifikation; Commits 1b64c007, 991b1eff). Eine Datei, die immer ablehnt, endet beim vierten Ausgeben als failed (repeatedly_stuck), die Warteschlange läuft weiter.
- 29.10.2026: Fix-Antworten in Issues gibt es erst nach dem Store-Release.

## Block A: drei Katalogsätze der Admin-Seite (aus Plan 39-01)

Die Kataloge sind nach dem englischen Quellsatz gekeyt: ein neuer en-Wortlaut ändert den Schlüssel in allen 16 Katalogen (php/l10n/*.json und *.js), in admin.js, admin.php, dem Vertragstest und den fünf Tabellen docs/l10n-*.md, und er braucht vor dem Tag eine neue grüne CI-Runde. es, it, nl, pt_PT und pt_BR sind maschineller Entwurf unter Vorbehalt und gehen mit. Wortlaute zeichengleich aus php/l10n/de.json und fr.json.

**A1: Mehrfachzählungs-Satz (geändert, Schlüsselwechsel)**

Grund: der zweite Satz der alten Fassung war falsch (Befund F6: der Index führt jede Kopie je Datei-ID); seit 1.6 erscheint der Satz nur noch im Rückfall, wenn die Zählung nicht entdoppelt werden kann.

| | alt (1.5.1) | neu (1.6.0) |
|---|---|---|
| en | External storages mounted once per user are counted once per mount, so the same file can stand in this figure several times. The search itself holds every file once. | External storages mounted once per user are counted once per mount here, so the same file can stand in this figure several times. |
| de | Je Nutzer einmal eingebundene externe Speicher werden je Einbindung gezählt, dieselbe Datei kann daher mehrfach in dieser Zahl stehen. Die Suche selbst führt jede Datei nur einmal. | Je Nutzer einmal eingebundene externe Speicher werden hier je Einbindung gezählt, dieselbe Datei kann daher mehrfach in dieser Zahl stehen. |
| fr | Les stockages externes montés une fois par utilisateur sont comptés une fois par montage, le même fichier peut donc figurer plusieurs fois dans ce chiffre. La recherche elle-même ne contient chaque fichier qu'une fois. | Les stockages externes montés une fois par utilisateur sont comptés ici une fois par montage, le même fichier peut donc figurer plusieurs fois dans ce chiffre. |

- (a) neu so annehmen.
- (b) eigener Wortlaut (en/de/fr).
- Empfehlung: (a); die alte Fassung behauptete etwas Falsches, die neue sagt nur, was die Zahl tut.

**A2: Satz bei null bewusst ausgelassenen Dateien (neu, ANZE-01)**

- en: "Nothing is left out on purpose right now. Files that are too large, of a type Findling does not read, or excluded by a rule would be counted here, and they are not in the denominator above."
- de: "Derzeit ist nichts bewusst ausgelassen. Hier stünden Dateien, die zu groß sind, von einem Typ, den Findling nicht liest, oder durch eine Regel ausgeschlossen, und sie zählen nicht im Nenner darüber."
- fr: "Rien n'est volontairement laissé de côté pour l'instant. Seraient comptés ici les fichiers trop volumineux, d'un type que Findling ne lit pas, ou exclus par une règle, et ils ne figurent pas au dénominateur ci-dessus."
- (a) so annehmen. (b) eigener Wortlaut.
- Empfehlung: (a); erklärt die leere Zeile, statt sie stumm stehen zu lassen (L-36-05).

**A3: Hinweis nach einer Änderung der Ausschlussregeln (neu, ANZE-02)**

- en: "The exclusion rules were changed. The search applies them at once, the counters on this page follow once they have been worked out again."
- de: "Die Ausschlussregeln wurden geändert. Die Suche wendet sie sofort an, die Zähler auf dieser Seite folgen, sobald sie neu ermittelt sind."
- fr: "Les règles d'exclusion ont été modifiées. La recherche les applique immédiatement, les compteurs de cette page suivent dès qu'ils ont été recalculés."
- (a) so annehmen. (b) eigener Wortlaut.
- Empfehlung: (a); der Upgrade-Beweis (Zusicherung 12, HaRP deploy 40819967372) zeigt den Hinweis nach der Regeländerung über die Route und ohne ihn davor.

## Block B: Store-Text 1.6.0

Was sich gegenüber dem Store-Stand 1.5.1 ändert:
- neu das `discussion`-Element in beiden info.xml (Forum-Thread 249775, D-37-07),
- die drei Doku-Links je info.xml zeigen auf blob/v1.6.0 statt blob/v1.5.1,
- Version und image-tag 1.6.0.

Was gleich bleibt: die Namen (Findling Search / Findling Suche / Findling Recherche, Findling Backend), die sechs Beschreibungen Wort für Wort wie 1.5.1, der Cross-Promo-Satz zum MCP Connector (D-37-08). Damit bleibt der Text in der gewohnten Länge und eine Faktenliste mit einer Zahl. Was 1.6.0 neu bringt, einschließlich des Issue-#36-Fix-Pakets aus Plan 40-06, steht nicht in der Beschreibung, sondern im Store-Changelog: der Store zeigt auf der Release-Seite CHANGELOG.md, Abschnitt [1.6.0] (reist im Archiv mit, scripts/release/store-archive.sh).

Diff-Auszug (`git diff v1.5.1..HEAD -- backend/appinfo/info.xml php/appinfo/info.xml`, je Sprache gleich):

```
-Switching from fulltextsearch/Elasticsearch: [steps in the documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.5.1/docs/migrate-from-fulltextsearch.en.md)
+Switching from fulltextsearch/Elasticsearch: [steps in the documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.6.0/docs/migrate-from-fulltextsearch.en.md)
-	<version>1.5.1</version>
+	<version>1.6.0</version>
 	<website>https://github.com/street1983nk/nextcloud-search</website>
+	<discussion>https://help.nextcloud.com/t/findling-1-2-0-and-mcp-connector-0-2-1-released/249775</discussion>
 	<bugs>https://github.com/street1983nk/nextcloud-search/issues</bugs>
```

- (a) so einreichen: Beschreibungen wie 1.5.1, Store-Changelog = CHANGELOG [1.6.0] wie er steht (44 Zeilen, Form wie 1.5.0 mit 61 Zeilen).
- (b) wie (a), aber CHANGELOG [1.6.0] vor dem Tag auf die sechs Punkte der Release-Notiz (Block C) kürzen.
- (c) Änderung nennen.
- Empfehlung: (a); die Kurztext-Regel gilt für Beschreibungen und READMEs, und die bleiben unverändert. Der CHANGELOG folgt der Keep-a-Changelog-Form mit Abhängigkeitsversionen (1.5.0: 61 Zeilen); (b) wäre ein Bruch dieser Form nur für 1.6.0.

## Block C: Release-Notiz v1.6.0 (englisch, Faktenliste)

```
Findling 1.6.0. Both apps need to be on 1.6.0.
- A file the content gateway refuses no longer blocks indexing: it ends as failed (gateway_error), the rest of the pass goes on, and the log names the HTTP status (#36).
- A content gateway that does not answer is named on the admin page and in /status; an aborted pass leaves no half indexed document, and the search keeps answering on a broken mount (#36).
- /status answers at once, the language fill level is measured in the background (#19).
- Coverage counts SMB and SFTP mounts with a per-user login once per share; new hints when nothing is left out and after a change of the exclusion rules.
- The tunnel watcher reports a reissued HaRP certificate and takes over new files under /certs/frp without a new registration (docs/harp-tunnel.md).
- Discussion link in the store; security and dependency updates (filelock CVE fixes, fastapi, pypdf, striprtf).
**Full Changelog**: https://github.com/street1983nk/nextcloud-search/compare/v1.5.1...v1.6.0
```

- (a) so ins Release übernehmen. (b) Änderung nennen.
- Empfehlung: (a); sechs Punkte aus CHANGELOG [1.6.0], keine Messgeschichte, keine Zahl außer Versionen und Issue-Verweisen. Issue #33 steht bewusst nicht drin (die Antwort dort postet der Owner selbst, danach erst "Closes #33").

## Block D: Audit 1.6.0

Audit 40-01 über v1.5.1..336ccae7: 0 CRIT, 0 HIGH, 0 MEDIUM, sechs LOW, davon vier gefixt (F-40-01 bis F-40-04) und zwei akzeptiert (F-40-05, F-40-06); alle Workflows grün auf efcf26c5 (Python gates 40743288537, PHP gates 40743288689, HaRP deploy 40743288892). Das Fix-Paket 40-06 ist verifiziert (10/10, 40-06-VERIFICATION.md), die Warnungen W-1/W-2 sind per Owner-Entscheid vom 29.10. umgesetzt, Kopf 23e54187 grün (HaRP deploy 40851958179, Python gates 40851958142).

**D1: F-40-06, Tombstones ausgelassener Storages bleiben im Zähler** (einziger Owner-LOW)

Während der Erstindexierung kann die Abdeckung auf der Admin-Seite um die Tombstones der ganzen Gruppe zu hoch stehen (Beispiel der Probe: rund 10 statt 1 Prozentpunkt); bei voller Abdeckung erscheint keine falsche Zahl, sondern keine. Kein Risiko für Nutzer oder Rechte. Berührt die Zusage von Weg C ("jede Freigabe zählt einmal").

- (a) accept für 1.6.0, saubere Lösung in v1.7 zusammen mit dem Feld `indexed` (deferred-items.md).
- (b) Fix vor 1.6.0: `indexedLeftOut` zählt Tombstones wie `indexed` (eine Zeile SQL plus Tests, Paket-Baumhash, neue volle CI-Runde vor dem Tag).
- Empfehlung: (a); nur eine Prozentzahl während der Erstindexierung, und der Fix vor dem Tag kostet eine volle CI-Runde für einen Wert, der in v1.7 ohnehin neu gefasst wird.

F-40-05 (Hinweissatz fehlt im Rennen zweier Admins in derselben Sekunde) ist akzeptiert und braucht keine Owner-Entscheidung.

## Block E: Umlaut-Audit (Regel 24.10.2026)

Umfang: beide info.xml (Namen, Zusammenfassungen, Beschreibungen de), alle 16 l10n-Kataloge (de/de_DE auf Umlaute, die übrigen Sprachen auf eigene Akzentfehler), php/templates/admin.php und php/js/admin.js, README.md, README.en.md, README.fr.md, CHANGELOG.md, SECURITY.md, CONTRIBUTING.md, THIRD-PARTY.md, alle 84 Markdown-Dateien unter docs/. Vorfilter: Wörter mit ae/oe/ue/ss außerhalb von Codeblöcken, Inline-Code, URLs und Pfaden, dazu eine eigene Suche nach ss statt ß (heißt, außer, groß, Größe, schließt, Anstoß, -mäßig); jede Fundstelle von Hand gegen das Wort geprüft. Eigennamen (Bjoern Jacke), Analyzer-Beispiele (Strasse), Kennungen (PRUEF-01), Codekommentare, Dateinamen und niederländische, spanische, französische Wörter (zoeken, puede, continue) sind kein Fund.

| Datei | Vorfilter-Zeilen | echte Funde | Stand |
|---|---|---|---|
| backend/appinfo/info.xml, php/appinfo/info.xml (de) | 0 / 1 | 0 | sauber |
| php/l10n/de.json, de_DE.json (je 354 Schlüssel) und de.js, de_DE.js | 24 / 24 | 0 | sauber |
| php/l10n fr, es, it, nl, pt_PT, pt_BR (.json und .js) | 16 bis 86 | 0 | sauber (Stichprobe auf fehlende Akzente: très, está, è, ç; keine Treffer) |
| php/templates/admin.php, php/js/admin.js | 0 deutsche Strings | 0 | alles über t(), Quelle englisch |
| README.md / README.en.md / README.fr.md | 2 / 6 / 3 | 0 | sauber |
| CHANGELOG.md, SECURITY.md, CONTRIBUTING.md, THIRD-PARTY.md | 17 / 0 / 4 / 14 | 0 | englisch, sauber |
| docs/store-listing.md (deutsche Prosa) | 141 | 4 | gefixt in 00a63edf |
| docs/runbook-messbox.md | 117 | 95 | gefixt in 00a63edf |
| docs/reconcile.md | 51 | 19 | gefixt in 00a63edf |
| docs/performance.md | 185 | 9 (+1 Zitat) | 9 gefixt in 00a63edf, Zitat siehe E2 |
| docs/ocr.md | 18 | 1 | gefixt in 00a63edf |
| docs/l10n-dutch.md, -italian.md, -portuguese.md | 101 / 96 / 69 | je 1 (Giessform) | gefixt in 00a63edf |
| docs/l10n-*.md (fünf Tabellen) | | je 1 Tabellenkopf "Schluessel" | Vorschlag, E2 |
| übrige 25 Dateien unter docs/ (ohne audits/, measurements/) | | 0 | sauber |
| docs/audits/ und docs/measurements/ (39 von 54 Dateien) | 2047 | rund 1800 Stellen | Vorschlag, E1 |

Gefixt (reine Zeichenkorrektur, keine Owner-Formulierung berührt; Commit 00a63edf, CI siehe Block F): store-listing.md erfuellt, gehoert, Begruendung, einschliesslich; runbook-messbox.md durchgehend ss statt ß (außerhalb, Anstoß, Größe, größer, heißt, schließt, pflichtmäßig, Vorsichtsmaßnahmen, verstoßen) und ASCII-Umlaute in elf Überschriften (Wofür, günstiger, Kostensätze, Blöcken, Schlüsselpaar, Datenträger, zurückspielen, Zustandsprüfung, Rückgabewerte, Kostenüberblick, Kostenführung, Rückfluss); reconcile.md Abschnitt "Wiederherstellung aus dem Papierkorb" (zurück, für, Löschung, nächsten, gelöscht, Größe, während, überlässt, angestoßen); performance.md (ließ, größeren, heißt, einschließlich, außer, außen, zwei Überschriften Messgröße und Wiederaufwärm-Kosten); ocr.md (groß); drei l10n-Tabellen (Gießform). Codeblöcke, Shell-Kommentare, Dateinamen und wörtliche Zitate blieben unberührt.

**E1: ASCII-Umlaute in den historischen Berichten unter docs/audits/ und docs/measurements/**

39 Mess- und Auditberichte aus September und Oktober (Schwerpunkte: audits/2026-09-phase-10 und -phase-18, measurements/2026-09-v12-messung, -semantiklauf-m7g, -vektordistanzen, -komposita-rezept-a, -a4-sprachfaelle-ci, -werkzeugfixe) sind durchgehend mit ae/oe/ue und ss geschrieben, rund 1800 Stellen. Sie liegen nicht im Store-Archiv und in keiner Oberfläche, aber im öffentlichen Repository; mehrere Tests lesen diese Dateien.

- (a) nach dem Release als eigener Doku-Commit: Wortliste je Datei, Code, Zitate und Rohdatenzeilen ausgenommen, Diff von Hand geprüft, Tests grün.
- (b) jetzt vor dem Tag.
- (c) so lassen (historische Protokolle).
- Empfehlung: (a); die Regel verlangt die Korrektur, aber sie berührt kein Release-Artefakt, und ein Massendiff über 39 Berichte gehört nicht zwischen Abnahme und Tag.

**E2: zwei Stellen, die nur mit Code- bzw. Zitatänderung gehen** (Teil von E1, gleiche Option)

- Tabellenkopf "| Schluessel |" in den fünf docs/l10n-*.md: der Vertragstest test_admin_ui_contract.py liest die Tabellen über genau diesen Kopf; Korrektur auf "Schlüssel" nur zusammen mit dem Test.
- docs/performance.md:3987 zitiert wörtlich "die Box LAEUFT WEITER BIS ZUR BERICHTSABNAHME (10-07)."; als Zitat belassen.

## Block G: Bestätigung der #36-Nachträge aus Plan 40-06

**G1: Kandidat F (Issue #19)**

/status liefert den Sprachfüllstand sofort aus dem Cache, mit Frische-Marker `languagesFilledAsOf`; gemessen wird im Hintergrund (genau ein Refresh zur Zeit), /status wartet nie darauf. Bekannte Grenze: beim Kaltstart (erster Aufruf nach einem Containerstart oder Index-Reset) ist `languagesFilled` bis zum ersten Refresh leer. Die Admin-Zeile lautet dann kurz "Languages of the index: de, en switched on, with text in the index." (de: "... eingeschaltet, mit Text im Index.") mit leerem zweiten Teil; der nächste Abruf der Seite zeigt den vollen Satz.

- (a) bestätigen, so in 1.6.0.
- (b) bestätigen, aber die zweite Satzhälfte beim Kaltstart ausblenden (neuer Katalogsatz in 16 Katalogen, PHP-Baumhash, volle CI-Runde vor dem Tag).
- Empfehlung: (a); die Lücke dauert nur bis zum nächsten Abruf, dafür blockiert die Admin-Seite nie mehr während einer Indexierung (Kern von #19).

**G2: neuer Anzeige-Satz D der Admin-Seite (stummes Content-Gateway)**

- en: "The content gateway did not answer on the last indexing pass. The affected files stay in the queue and are tried again; the search keeps answering."
- de: "Das Content-Gateway hat beim letzten Indexierungslauf nicht geantwortet. Die betroffenen Dateien bleiben in der Warteschlange und werden erneut versucht; die Suche antwortet weiter."
- fr: "La passerelle de contenu n'a pas répondu lors du dernier passage d'indexation. Les fichiers concernés restent dans la file d'attente et seront réessayés. La recherche continue de répondre."

Bekannte Unschärfe: der Satz erscheint auch bei einer Häufungs-Eskalation (derselbe Fehlerstatus für mindestens fünf Dateien eines Passes, in kleinen Pässen für alle, z. B. 401 für alles), obwohl das Gateway dabei geantwortet hat, nur mit Fehlern. Die Logzeile nennt in beiden Fällen den HTTP-Status.

- (a) so bestätigen, Unschärfe für v1.7 notiert.
- (b) neuer Wortlaut, der beide Fälle trägt (Schlüsselwechsel in 16 Katalogen, admin.js, admin.php, Test, fünf Tabellen, PHP-Baumhash, volle CI-Runde vor dem Tag):
  - en: "The content gateway did not deliver the files of the last indexing pass. The affected files stay in the queue and are tried again; the search keeps answering."
  - de: "Das Content-Gateway hat die Dateien des letzten Indexierungslaufs nicht geliefert. Die betroffenen Dateien bleiben in der Warteschlange und werden erneut versucht; die Suche antwortet weiter."
  - fr: "La passerelle de contenu n'a pas livré les fichiers du dernier passage d'indexation. Les fichiers concernés restent dans la file d'attente et seront réessayés. La recherche continue de répondre."
- (c) eigener Wortlaut.
- Empfehlung: (a); der häufige Fall (Ausfall, Proxy 502/503/504) ist genau getroffen, der seltene Fall ist sichtbar und im Log eindeutig, und (b) kostet eine volle CI-Runde vor dem Tag.

**G3: der schon gepostete Kommentar in Issue #36**

Vor dem Owner-Entscheid "Fix-Antworten erst nach dem Store-Release" ging ein englischer Kommentar ohne "Closes" hinaus (issuecomment-6492666744, Link auf 6880fa1e und den Vergleich c75fb6cf...4ed0f846; der Nachtrag W-1 ist darin nicht enthalten).

- (a) stehen lassen; nach dem Store-Release folgt die eine Fix-Antwort mit Store-Version, die ihn ergänzt.
- (b) löschen.
- Empfehlung: (a); er ist sachlich richtig und verspricht kein Datum, ein Löschen wäre für den Melder verwirrender als ein Nachtrag.

## Block F: GO für Tag und Einreichung

EIN Wort für ZWEI unumkehrbare Handlungen: (1) Tag v1.6.0 annotiert auf den grünen Kopf mit Release-Lauf, Tag-Links und CI-Fremdinstallation aus den Release-Assets, UND (2) danach Einreichung beider Apps (findling, findling_backend) über den Workflow Store submission, ohne weitere Rückfrage, solange jeder Beleg grün ist; bei Rot Stopp und neue Frage. Es gibt keine zweite Runde für die Einreichung. Ein Tag ist öffentlich und eine eingereichte Version samt Store-Text ist nicht mehr editierbar.

Kopf: Code-Kopf 23e54187 (head_green Exit 0, Läufe in 40-06-SUMMARY), danach nur Doku: 523f2253 (.planning) und 00a63edf (Umlaut-Fix docs/). `scripts/ci/head_green.sh 00a63edf "Python gates" "Security scans"`: Exit 0 (Python gates 40856857305, Security scans 40856857515, OpenSSF Scorecard 40856857456, alle success). HaRP deploy, Integration, Resilience, Multi-arch image und PHP gates startet der Pfadfilter für docs/*.md nicht; `git diff --stat 23e54187..00a63edf -- backend php scripts .github testdata` ist leer, ihre letzten grünen Läufe stehen auf 23e54187 (PHP gates 40834773386 auf 4ed0f846). Plan 40-04 Task 3 setzt nach der Antwort noch den Abschnitt "Gesamttext v1.6.0" in docs/store-listing.md mit seinem Gate in test_store_metadata.py; der Tag-Kopf ist der letzte Commit außerhalb .planning danach und wird mit head_green über alle sieben Workflows belegt, bevor getaggt wird.

- (a) GO.
- (b) warten.
- Empfehlung: (a).

## Nach dem Release (keine Entscheidung, nur Kenntnis)

- UI-Sichtung der Sätze A1 bis A3, G2 und der Sprachzeile (G1) auf einer echten Instanz durch den Owner.
- Issue #33: Antwort und HaRP-Upstream-Vorschlag (Entwürfe aus Phase 38 auf dem Desktop) postet der Owner selbst, erst danach ein "Closes #33". Kopierbefehl in docs/harp-tunnel.md seit F-40-03 um `test -s` ergänzt; die Entwürfe verlinken nur die Doku.
- Issue #36 und #19: Fix-Antwort mit Store-Version nach dem Release (Dauerregel).
- v1.7-Merkliste: F-40-06 mit dem Feld `indexed`, Unschärfe G2, Kaltstart-Satz G1, Endverdikt gateway_error statt repeatedly_stuck nach erschöpftem Budget.
