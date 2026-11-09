# Phase 43: Owner-Vorlage Abnahme Findling 1.6.3 (eine Runde)

Stand: 09.11.2026 (vorbereitet durch Plan 43-12 Task 1; die Runde selbst startet erst, wenn mbozem auf den Testbuild geantwortet hat oder der Owner ausdrücklich weitergeht. 43-TESTBUILD.md führt heute "Rueckmeldung: ausstehend" und "Wurzel-Frage: keine Antwort").

Antwort "wie empfohlen" übernimmt jede Empfehlung; Abweichungen als "C b" oder "D2 b" nennen. Nicht genannte Punkte gelten als wie empfohlen. Ausnahme: Punkt W (Wurzel-Frage) trägt bewusst KEINE Empfehlung und braucht ein eigenes Wort (grenze oder beheben), solange mbozem nicht geantwortet hat.

Nichts ist getaggt, nichts eingereicht, nichts gepostet. Das GO (Punkt F) und der Push (Punkt P) sind getrennte Entscheide (B5: je Gegenstand eine eigene Freigabe).

## Schon entschieden, nur protokolliert (keine Frage)

- D-43-01 bis D-43-05: Der Storage-Sweep läuft einmal je Abgleich-Takt, auch wenn Crawl oder Warteschlange den Walk blockieren; gelöschte und abgewählte Speicher verlieren ihre Dokumente sofort, die 30-Tage-Frist für verschwundene beginnt mit dem ersten Vermissen.
- D-43-06, D-43-12: Einmaliger Hinweis neben der Deckungsgrad-Zahl nach dem Update, verschwindet von selbst 7 Tage nach der ersten vollständigen Zählung. Wortlaut (H Variante b) am 07.11. freigegeben.
- D-43-07, D-43-11: Die Zählung pro Dokument ist die Hauptzahl; nicht lesbare und mehrfach hängen gebliebene Dateien gehören zum Nenner, die Quote geht nie über 100 Prozent.
- D-43-08, D-43-09: Pflicht-Abnahmetest mit mbozem-Topologie und unabhängiger Gegenprobe; E2E-Lauf 42525415627 auf dem auditierten Kopf, alle fünf Beine grün.
- D-43-10, D-43-13: Testbuild für mbozem als Workflow-Artefakt (kein Pre-Release), Kommentar mit Owner-Freigabe am 09.11. gepostet; #25 schließt erst nach seiner Bestätigung.
- D-43-14: Doppelzählung bei Weiterteilung eines SMB-Ordners und bei mehreren Einhängepunkten derselben Freigabe ist richtig behoben (Dokumentschlüssel, Backfill, Rückweg belegt).
- D-43-15: Verschiedene Wurzeln derselben Freigabe zählen in 1.6.3 noch doppelt; der Umgang damit ist Punkt W dieser Runde (nach mbozems Antwort, sonst Owner-Wort).
- D-43-16: SMB ohne Server-Verschlüsselung wird nicht blockierend mit Fristen gelesen; eine abgelehnte, gesperrte oder ausgelagerte Datei zählt als nicht lesbar statt einen PHP-Worker zu blockieren.

## Block B: Store-Text 1.6.3

Namen, Kurztexte und die sechs Beschreibungen sind zeichengleich zur abgenommenen Fassung 1.6.2. Der Diff `git diff v1.6.2..HEAD -- backend/appinfo/info.xml php/appinfo/info.xml` besteht aus den Versionszeilen, den sechs Doku-Links und der neuen sechsten Backend-Route (deklarativ, im Store-Text nicht sichtbar):

```
-	<version>1.6.2</version>            (zweimal, beide Apps)
+	<version>1.6.3</version>
-			<image-tag>1.6.2</image-tag>
+			<image-tag>1.6.3</image-tag>
-...blob/v1.6.2/docs/migrate-from-fulltextsearch...   (sechs Links en/de/fr)
+...blob/v1.6.3/docs/migrate-from-fulltextsearch...
+			<route> ^/coverage$  POST  ADMIN  bruteforce [401] </route>   (nur backend/info.xml)
```

- (a) bestätigt: so einreichen.
- (b) Änderung nennen.
- Empfehlung: (a); Kurztext-Regel, keine neue Beschreibung nötig. Was 1.6.3 bringt, zeigt der Store über CHANGELOG.md [1.6.3].

## Block C: Release-Notiz v1.6.3 (englisch, Faktenliste)

Gegen das ganze CHANGELOG [1.6.3] geprüft: 1 Added und 6 Fixed sind in vier Punkten abgedeckt (Obergrenze sechs).

```
Findling 1.6.3. Update both apps; 1.6.x versions work together.
- The coverage figure counts every document once; share groups and storages that are no longer mounted no longer inflate it (#25)
- The storage sweep removes documents of deleted or unmounted storages even on busy instances (#25)
- A note on the admin page explains the lower figures after the update; files that could not be read are named with a remedy (#25)
- Locked or refused files on SMB storage no longer block a PHP worker and count as not readable

**Full Changelog**: https://github.com/street1983nk/nextcloud-search/compare/v1.6.2...v1.6.3
```

Bei Entscheid "W grenze" kommt vor der Full-Changelog-Zeile zusätzlich diese Zeile dazu (derselbe Satz wie im CHANGELOG, Punkt W):

```
Known limitation: two configurations of the same share with different roots still count shared files twice; this is fixed in 1.6.4.
```

- (a) so ins Release übernehmen (plus die Known-limitation-Zeile, falls W = grenze).
- (b) Änderung nennen.
- Empfehlung: (a); vier Punkte, keine Messgeschichte, genau die Nutzerfolgen.

## Block V: Abhilfe-Satz "Not readable for the users asked" plus SMB-Zusatzsatz (neu zur Freigabe)

Die Blöcke H, Z, U und L sind seit dem 07.11. freigegeben (43-TEXTE.md, Maschinenzeilen). NEU zur Freigabe sind Block V (ersetzt die alte Abhilfe, seit 43-19 in allen 16 Katalogen) und der SMB-Zusatzsatz (erscheint nur, wenn die Erweiterung php-smbclient fehlt). Die Sprachen es, it, nl, pt_BR und pt_PT sind maschineller Entwurf unter Vorbehalt und gehen mit (Muster 39-01).

**V1: Abhilfe zu "Not readable for the users asked" (D-43-16)**

| | Wortlaut |
|---|---|
| en | The file is still there. Check the advanced permissions of the Team Folder or the access rights on the external storage: Findling reads a file only as a user who may open it and asks the first 20 of its users in alphabetical order. A file that is locked or offline is tried again a few times. |
| de | Die Datei ist noch vorhanden. Die erweiterten Berechtigungen des Team Folders oder die Zugriffsrechte auf dem externen Speicher prüfen: Findling liest eine Datei nur als Nutzer, der sie öffnen darf, und fragt die ersten 20 ihrer Nutzer in alphabetischer Reihenfolge. Eine gesperrte oder ausgelagerte Datei wird noch einige Male erneut versucht. |
| fr | Le fichier existe toujours. Vérifiez les permissions avancées du Team Folder ou les droits d'accès sur le stockage externe : Findling ne lit un fichier qu'en tant qu'utilisateur autorisé à l'ouvrir et interroge les 20 premiers de ses utilisateurs par ordre alphabétique. Un fichier verrouillé ou hors ligne est réessayé quelques fois. |

**V2: Zusatzsatz für SMB ohne php-smbclient (43-18 Fix 2)**

| | Wortlaut |
|---|---|
| en | On SMB storage without the php-smbclient extension, install this extension recommended by Nextcloud, or raise the timeout option of the storage (occ files_external:config). |
| de | Bei SMB-Speichern ohne die Erweiterung php-smbclient diese von Nextcloud empfohlene Erweiterung installieren, alternativ die Speicher-Option timeout erhöhen (occ files_external:config). |
| fr | Sur les stockages SMB sans l'extension php-smbclient, installez cette extension recommandée par Nextcloud, ou augmentez l'option timeout du stockage (occ files_external:config). |

- (a) beide so annehmen.
- (b) eigener Wortlaut (en/de/fr je Satz).
- Empfehlung: (a); V1 nennt jetzt auch externe Speicher und gesperrte/ausgelagerte Dateien (seit 1.6.3 landen 422-Fälle unter diesem Grund), V2 nennt die von Nextcloud empfohlene Abhilfe und die occ-Alternative.

## Block D: Audit 1.6.3

**D1 (Kenntnis):** Audit 43-09 über v1.6.2..37b518d6: 0 CRIT, 0 HIGH, 0 MEDIUM offen, 2 LOW akzeptiert (F-43A-02 Uhrsprung-Kadenz, F-43A-03 Diagnosezeile im Mischbetrieb; Begründungen in 43-AUDIT.md), 4 INFO. Kein Owner-LOW. Das eine MEDIUM (F-43A-01, synchroner Zähldeckel über dem Admin-Timeout auf ARM) ist lokal per TDD gefixt (Commit 37b518d6 = audited_head), end to end belegt (E2E 42525415627, alle Beine grün).

**D2: optionaler CHANGELOG-Satz zu F-43A-01**

Sichtbare Folge des Fixes: Instanzen mit 25.000 bis 100.000 Zeilen sehen nach dem Update einmal kurz den Satz "wird gezählt", danach kommt die Zahl aus dem Hintergrundpfad. Vorschlag unter [1.6.3] Fixed:

```
- The synchronous coverage count is capped at 25,000 rows, so the answer stays within the admin timeout of the companion on slow hardware; larger instances see the figure counted in the background once after the update.
```

- (a) Satz aufnehmen.
- (b) weglassen (kein Store-Text betroffen, der Satz ist nicht zwingend).
- Empfehlung: (a) wie empfohlen aufnehmen; genau die Instanzklasse, für die 1.6.3 gebaut ist, sieht diesen Zustand einmal, und der Satz erklärt ihn.

## Punkt W: Wurzel-Frage (D-43-15, KEINE Empfehlung, eigenes Wort nötig)

Stand: `Wurzel-Frage: keine Antwort` (43-TESTBUILD.md). Die Frage an mbozem steht seit dem 09.11. im Issue (https://github.com/street1983nk/nextcloud-search/issues/25#issuecomment-6732932582): "And is the same share configured with two different roots somewhere, like /Daten and /Daten/Projekte? That case still counts twice, I'd fix it before the store release if you have it, otherwise in 1.6.4."

Antwortet mbozem vor der Runde, entfällt dieser Punkt: "ja" heißt Stopp und Behebung vor dem Release, "nein" heißt bekannte Grenze. Ohne seine Antwort entscheidet der Owner zwischen zwei Wegen:

**Weg 1, grenze:** 1.6.3 erscheint mit der bekannten Grenze. Unter [1.6.3] im CHANGELOG kommt zu "### Known limitations" genau ein Satz dazu, derselbe Satz steht in der Release-Notiz (Block C):

```
Two configurations of the same share with different roots still count shared files twice; this is fixed in 1.6.4.
```

**Weg 2, beheben:** Zusatzplan VOR der Store-Einreichung (Dokumentschlüssel über host//share plus Wurzel plus filecache-Pfad, PHP-Gruppierung nach Freigabe, N1/phpOnly je Mitglied umgerechnet) plus Audit-Nachtrag. Diese Runde endet dann ohne GO (GO: nein), Tag und Einreichung warten auf den Zusatzplan.

- Antwort als eigenes Wort: "W grenze" oder "W beheben" (wird als `Freigabe Wurzel 43-12: <Zitat> (<Datum>, <Kanal>) Entscheid: grenze|beheben` in 43-FREIGABEN.md festgehalten).

## Block I: Außentexte (Entwürfe, englisch)

**I1: Forum-Post** (Thread 249775, Owner postet; Datei `C:/Users/Student/Desktop/Findling_1.6.3_Forum_ENTWURF.md`), wörtlich:

```
Findling 1.6.3 is in the store (update both apps together).

New in 1.6.3:
- Coverage counts every document once: per-user mounts of the same share no longer inflate the figure
- Documents of deleted or unmounted storages leave the index even while the crawl is busy
- A note on the admin page explains the lower figures after the update, and files that could not be read are shown with a remedy
- Locked or refused files on SMB storage no longer block a PHP worker

Changelog: https://github.com/street1983nk/nextcloud-search/releases/tag/v1.6.3
```

**I2: Antwort in #25** (Claude postet NACH dem Store-Release mit eigener Freigabe; OHNE Schließen: das Issue schließt mbozem oder wir erst nach seiner Bestätigung, kein "Closes"), wörtlich:

```
1.6.3 is in the app store now, update both apps together. Thanks again for the test and your table, most of this release is built on that data.

Coming from the rc it is a normal update and the figure stays. Coming straight from 1.6.2 the key backfill runs first (the page says the coverage is being counted, on your rows up to maybe 3.5 h), then it should land around 18 % while the crawl runs.

I'll leave this one open until you confirm the number on the store build.
```

- (a) beide so.
- (b) Änderung je Text nennen.
- Empfehlung: (a); kurz, nur Neuerungen, I2 dankt für Test und Daten und lässt das Issue offen.

## Block F: GO für Tag und Einreichung

EIN Wort für ZWEI unumkehrbare Handlungen, die der Owner selbst ausführt: (1) Tag v1.6.3 annotiert auf den grünen, auditierten Kopf <sha> und Push des Tags, (2) danach Auslösen der Store submission für beide Apps. Claude bereitet Befehle und Belege vor und prüft danach jede Belegzeile.

- audited_head = 37b518d6 (43-AUDIT.md); danach nur Harness- und Doku-Commits, Code-Diff leer (Beleg in 43-TESTBUILD.md und 43-AUDIT.md Fix-Delta).
- Nach dem Entscheid setzt Task 3 den Gesamttext in docs/store-listing.md ("# Entwurf v1.6.3 (Gesamttext), abgenommen am <Datum>") mit Gate scan_full_text_1_6_3 in backend/tests/test_store_metadata.py. Der Tag-Kopf ist dann `git log -1 --format=%H -- . ':!.planning'`; Bedingungen: leerer Code-Diff 37b518d6..Tag-Kopf, sieben Workflows grün per scripts/ci/head_green.sh. Der sha steht danach in 43-ABNAHME.md.

- (a) GO.
- (b) warten.
- Empfehlung: (a), aber nur zusammen mit beidem: Testbuild-Ergebnis liegt vor (mbozem bestätigt oder Owner-Wort zum Weitergehen) UND W = grenze. Bei W = beheben erzwingt die Runde GO: nein (G2-Sperre).

## Punkt P: Push der Abnahme-Commits (getrennt vom GO)

Das GO deckt keinen Push (B5). Eigene Frage: Darf Claude die Abnahme-Commits dieser Runde (Gesamttext, Gate, CHANGELOG-Ergänzungen, 43-ABNAHME.md) nach `git pull --rebase` auf main pushen? Die Antwort wird als `Freigabe Push 43-12: <Zitat> (<Datum>, <Kanal>) Entscheid: ja|nein` in 43-FREIGABEN.md festgehalten; ohne "Entscheid: ja" bleibt alles lokal.

- (a) ja.
- (b) nein (Owner pusht selbst oder später).
- Empfehlung: (a); ohne Push gibt es keinen grünen CI-Beleg des Tag-Kopfs.

## Umlaut-Audit (Regel 24.10.2026)

Umfang: alle in 1.6.3 neuen oder geänderten deutschen Texte. Vorfilter `grep -nE "(ae|oe|ue)[a-z]|ss[^a-z]"` über die Deltas v1.6.2..HEAD, dazu eine Suche nach ASCII-Ersatzwörtern (gross, heiss, ausser, schliess, fuer, ueber, koenn, muess, waehr, zaehl, laeuft, spaeter, groesse); jede Fundstelle von Hand geprüft.

| Text | Vorfilter-Treffer | echte Funde |
|---|---|---|
| php/l10n/de.json, sechs neue oder geänderte Werte (H, Z, U, L, V1, V2) | 2 (deutsch "dauern" in Z; englisch "access" im Schlüssel von V1) | 0 |
| php/l10n/de_DE.json, dieselben sechs Werte | 2 (dieselben) | 0 |
| docs/store-listing.md, Abschnitt "# Entwurf v1.6.3, Stand Plan 43-08" | 3 ("dauern"; englisch "access"; französisch "quelques") | 0 |
| docs/l10n-{french,spanish,italian,dutch,portuguese}.md, je zwei deutsche Nachtrag-Absätze (43-06, 43-19) | 0 | 0 |
| CHANGELOG.md [1.6.3] und Release-Notiz | englisch, keine deutsche Prosa | 0 |
| ASCII-Ersatzwort-Suche über alle Deltas | 1 (spanisch "fuera de línea" in l10n-spanish.md) | 0 |
| Forum-Entwurf 1.6.3 und I2 | englisch, keine Umlaute nötig | 0 |
| diese Vorlage (deutsche Prosa) | siehe "Prüfung dieser Vorlage" | 0 |

Ergebnis: 0 echte Funde, keine Korrektur nötig; kein eigener Entscheidungspunkt.

## Prüfung dieser Vorlage

- Umlaut-Vorfilter über diese Datei (Prosa ohne Codeblöcke): Treffer sind die Suchwörter der Methodenzeile selbst, englische Wörter (access, issue, success) und korrekte deutsche Wörter (dauern, Neuerungen, erneut versucht); 0 echte Funde.
- Keine U+2013 und keine U+2014, keine Emojis (Byte-Suche).
- "wie empfohlen" deckt B, C, V, D2, I und P; W und F brauchen das eigene Wort (W grenze|beheben, GO ja|nein).
