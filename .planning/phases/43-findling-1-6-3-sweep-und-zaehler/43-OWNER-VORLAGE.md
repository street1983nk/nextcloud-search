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

# Runde 2

Stand: 11.11.2026 (vorbereitet durch Plan 43-12 Task 1). Runde 1 oben bleibt als Geschichte stehen (GO: nein am 09.11.2026 07:05, weil mbozem den Wurzelfall bestätigt hat); ihre Zeilen erfüllen nichts in dieser Runde.

Antwort "wie empfohlen" übernimmt jede Empfehlung; Abweichungen als "C b" oder "T4 b" nennen. Nicht genannte Punkte gelten als wie empfohlen. Das GO (Punkt F) und der Push (Punkt P) sind getrennte Entscheide mit je eigenem Wort (GO ja|nein, P ja|nein).

Nichts ist getaggt, nichts eingereicht, nichts gepostet. Die CHANGELOG-Sätze aus Punkt T stehen seit dem 11.11.2026 als Entwurf öffentlich auf main (43-FREIGABEN.md, "Freigabe Push 43-26" und "Freigabe Push 43-27 Fix 2"), sind aber in keinem Release und in keinem Store-Paket.

Erste und zweite Handlung des Plans, geprüft am 11.11.2026:

- 43-TESTBUILD-RC2.md führt genau eine Zeile `Ergebnis: keine Antwort (Owner-Entscheid "Ok")`. Es gibt kein rc.2 (43-28 und 43-29 gestrichen), siehe Punkt R.
- 43-AUDIT.md führt `d_43_15: behoben` und `status_43_27: passed`.
- G2-Sperre: 43-TESTBUILD.md führt `Wurzel-Frage: ja`, zusammen mit `d_43_15: behoben` ist das GO nicht mehr gesperrt.

## Schon entschieden, nur protokolliert (keine Frage)

- D-43-01 bis D-43-14 und D-43-16: unverändert wie in Runde 1 oben.
- D-43-15: Verschiedene Wurzeln derselben Freigabe zählen einmal. mbozem hat den Fall am 09.11.2026 bestätigt, behoben in 43-21 bis 43-26, auditiert in 43-27.
- D-43-17: Dieselbe Freigabe in zwei Schreibweisen (//Daten und //daten) zählt einmal; Host und Freigabename werden für die Zählung gefaltet.
- OE-1 bis OE-8, alle Wahl a, Owner-Wort "Wie empfohlen" (2026-11-09 10:36, 43-FREIGABEN.md):
  - OE-1 a: Host und Freigabename ASCII-klein verglichen, Wurzel und Pfad ungefaltet (/projekte neben /Projekte zählt getrennt).
  - OE-2 a: lange (gehashte) Speicher-IDs nur über die Konfiguration und nur bei passendem md5; nicht Nachbaubares bleibt je Speicher gezählt und steht als Zahl in der Overview und stündlich im Log. Passwörter werden nie gelesen.
  - OE-3 a: Samba [homes] oder Freigabe gleich Anmeldename nie gruppieren.
  - OE-4 a: SFTP nur je Anmeldung gruppieren.
  - OE-5 a: Schlüsselformat 2 mit Formatmarke und einmaligem Neuaufbau, im Mischbetrieb nie eine falsche Zahl.
  - OE-6 a: PHPUnit lokal per Docker für alle PHP-Änderungen in 43-21 bis 43-27.
  - OE-7 a: Samba-Pfad mit %U oder %S als bekannte Grenze, ein Satz unter Known limitations.
  - OE-8 a: 43-11 schließt als "abweichend, abgelöst". Der Wortlaut des Entscheids nannte rc.2; nach der Streichung von rc.2 gilt der Owner-Entscheid vom 11.11.2026 ("Ok", 43-FREIGABEN.md, "Entscheid 43-11 abweichend, abgelöst").
- rc.2 gestrichen: Owner-Wort "Rc2 Streichen und antworten und Mittwoch geht es weiter" (09.11.2026 abends) und "Ok" zu 43-29 (11.11.2026).
- Audit-Fixes: Owner-Entscheid "A" am 11.11.2026, zweimal (die drei LOW F-43B-01 bis -03 beheben; nach dem roten Lauf Produkt-Fix F-43B-05 statt bloßer Wiederholung).

## Punkt W: Wurzel-Frage (erledigt, keine Frage)

- mbozem: "Same share with two roots: yes, we have exactly that case" (https://github.com/street1983nk/nextcloud-search/issues/25#issuecomment-6735344512), dazu die Schreibweisen //Daten und //daten.
- Behoben und auditiert: audited_head 2dacf753fdaacca0c0e6341fc816006bc4d42001, `d_43_15: behoben`, `status_43_27: passed` (43-AUDIT.md).
- End to end belegt: Lauf "Coverage end to end" 43094681914, success, sieben Beine grün (Punkt E).
- Ergebnis rc.2: entfällt, es gibt kein rc.2 (Punkt R).
- Nicht belegt: die Zahl einer echten Instanz mit Wurzeln und Schreibweisen nach der Behebung. mbozem erwartet rund 18 Prozent, gemessen hat das niemand; die erste Messung ist das Store-Release selbst.

## Punkt B: Store-Text 1.6.3 (unverändert seit Runde 1)

`git diff --stat 37b518d6..HEAD -- backend/appinfo/info.xml php/appinfo/info.xml` ist leer, ebenso der Diff über php/l10n, php/templates und php/js. Namen, Kurztexte, Beschreibungen und Kataloge sind die in Runde 1 abgenommenen ("Ok", 2026-11-09 07:00).

- (a) bestätigt: so einreichen.
- (b) Änderung nennen.
- Empfehlung: (a); kein Text hat sich geändert, die Abnahme aus Runde 1 trägt.

## Punkt C: Release-Notiz v1.6.3 (englisch, Faktenliste)

Fünf Punkte (Obergrenze sechs). Neu gegenüber Runde 1: der zweite Punkt zu Wurzeln und Schreibweisen und, nach OE-7 a, die Zeile zur bekannten Grenze mit %U. Die Grenzzeile zu Wurzeln aus Runde 1 entfällt, der Fall ist behoben.

```
Findling 1.6.3. Update both apps; 1.6.x versions work together.
- The coverage figure counts every document once; share groups and storages that are no longer mounted no longer inflate it (#25)
- One share configured with different roots, or with the server or share name spelled in a different case, counts once (#25)
- The storage sweep removes documents of deleted or unmounted storages even on busy instances (#25)
- A note on the admin page explains the lower figures after the update; files that could not be read are named with a remedy (#25)
- Locked or refused files on SMB storage no longer block a PHP worker and count as not readable

Known limitation: a Samba share whose folder depends on the user on the server side (a path with %U or %S) still counts as one tree for all users.

**Full Changelog**: https://github.com/street1983nk/nextcloud-search/compare/v1.6.2...v1.6.3
```

Möglicher sechster Punkt (Variante c), falls die Wartezeit nach dem Update in die Notiz soll:

```
- After the update the admin page says the coverage is being counted until the count is rebuilt; on very large instances this takes hours, and the search works normally meanwhile
```

- (a) so ins Release übernehmen (fünf Punkte plus Grenzzeile).
- (b) Änderung nennen.
- (c) wie (a), zusätzlich der sechste Punkt.
- Empfehlung: (a); die Wartezeit erklärt die Admin-Seite selbst (Block Z, in Runde 1 abgenommen), die Notiz bleibt eine kurze Faktenliste.

## Punkt T: CHANGELOG-Sätze 1.6.3 (Entwürfe, wörtlich aus den drei Dateien)

Stand der Dateien: CHANGELOG.md, CHANGELOG.de.md und CHANGELOG.fr.md, Abschnitt [1.6.3]. Der Abschnitt [Unreleased] ist in allen drei leer. T1 bis T3 stammen aus 43-23, T4 und T5 aus 43-27. Die drei Dateien reisen im Store-Archiv mit (scripts/release/store-archive.sh).

**T1: Fixed, Wurzeln und Schreibweisen (D-43-15, D-43-17, OE-3 a, OE-4 a)**

| | Wortlaut |
|---|---|
| en | The coverage figure counts a document once also when one share is configured with different roots, or with the server or share name spelled in a different case (#25). A Samba [homes] share is never grouped across users, and SFTP storages are grouped per login only. |
| de | Die Abdeckungszahl zählt ein Dokument auch dann einmal, wenn eine Freigabe mit verschiedenen Wurzeln konfiguriert ist oder Server- oder Freigabename in anderer Groß- und Kleinschreibung stehen (#25). Eine Samba-[homes]-Freigabe wird nie über Nutzer hinweg gruppiert, SFTP-Speicher nur je Anmeldename. |
| fr | Le chiffre de couverture compte un document une seule fois aussi lorsqu'un partage est configuré avec des racines différentes, ou lorsque le nom du serveur ou du partage est écrit avec une casse différente (#25). Un partage Samba [homes] n'est jamais regroupé entre utilisateurs, et les stockages SFTP ne sont regroupés que par identifiant de connexion. |

- (a) so. (b) eigener Wortlaut.
- Empfehlung: (a); der Satz nennt genau die zwei Fälle von mbozem und die zwei Ausnahmen, die der Owner mit OE-3 a und OE-4 a gewählt hat.

**T2: Known limitations, Samba-Pfad mit %U oder %S (OE-7 a)**

| | Wortlaut |
|---|---|
| en | A Samba share whose folder depends on the user on the server side (a path with %U or %S) still counts as one tree for all users. |
| de | Eine Samba-Freigabe, deren Ordner serverseitig vom Nutzer abhängt (ein Pfad mit %U oder %S), zählt weiterhin als ein Baum für alle Nutzer. |
| fr | Un partage Samba dont le dossier dépend de l'utilisateur côté serveur (un chemin avec %U ou %S) compte toujours comme un seul arbre pour tous les utilisateurs. |

- (a) so. (b) eigener Wortlaut.
- Empfehlung: (a); OE-7 a verlangt genau einen Satz, und er sagt die Folge ohne Technik.

**T3: Known limitations, lange Speicher-IDs, die sich nicht zuordnen lassen (OE-2 a)**

| | Wortlaut |
|---|---|
| en | Storages with an id longer than 64 characters that cannot be rebuilt from their configuration (global or user provided credentials, a login name other than the user id) are counted per storage. |
| de | Speicher mit einer Id länger als 64 Zeichen, die sich nicht aus ihrer Konfiguration neu bilden lässt (globale oder vom Nutzer hinterlegte Zugangsdaten, ein Anmeldename ungleich der Nutzer-Id), werden je Speicher gezählt. |
| fr | Les stockages dont l'identifiant dépasse 64 caractères et qui ne peuvent pas être reconstruits à partir de leur configuration (identifiants globaux ou fournis par l'utilisateur, un nom de connexion différent de l'identifiant utilisateur) sont comptés par stockage. |

- (a) so. (b) eigener Wortlaut. (c) weglassen.
- Empfehlung: (a); der Fall ist real (LDAP-Anmeldenamen, globale Zugangsdaten), und ohne den Satz sieht eine zu niedrige Zahl dort wie ein Fehler aus.

**T4: Fixed, Nachhol-Durchlauf (F-43B-02, neu aus 43-27)**

| | Wortlaut |
|---|---|
| en | The one time catch-up cycle after an update no longer starts a round when the reconcile is switched off at that very moment. |
| de | Der einmalige Nachhol-Durchlauf nach einem Update startet keine Runde mehr, wenn der Abgleich genau in diesem Augenblick ausgeschaltet wird. |
| fr | Le cycle de rattrapage unique après une mise à jour ne lance plus de tour lorsque le rapprochement est désactivé à cet instant précis. |

- (a) so. (b) eigener Wortlaut. (c) weglassen.
- Empfehlung: (a); der Fehler gilt auch in 1.6.2 (43-AUDIT.md, Fix-Runde), ein Satz reicht, und er behauptet nicht mehr als das Fenster von Millisekunden hergibt.

**T5: Fixed, vorübergehende Datenbanksperre (F-43B-05, neu aus 43-27)**

| | Wortlaut |
|---|---|
| en | A passing database lock during the first index no longer ends the crawl of a storage; the slice is tried again a few seconds later, up to five times in a row. |
| de | Eine vorübergehende Datenbanksperre während des ersten Index beendet den Durchlauf eines Speichers nicht mehr; der Abschnitt wird wenige Sekunden später erneut versucht, bis zu fünfmal hintereinander. |
| fr | Un verrou passager de la base de données pendant le premier index ne met plus fin au parcours d'un stockage ; la tranche est retentée quelques secondes plus tard, jusqu'à cinq fois de suite. |

- (a) so. (b) eigener Wortlaut. (c) weglassen.
- Empfehlung: (a); das ist der sichtbarste der vier Audit-Fixes (ohne ihn fehlen Dateien eines Speichers im Index, bis der Abgleich sie nachholt), und der Code stand so seit dem ersten Release.

**T6: Datum in der Überschrift**

Alle drei Dateien führen `## [1.6.3] - 2026-11-08`. Das war der Stand vor Runde 1; das Release liegt später.

- (a) beim Umsetzen (Task 3) in allen drei Dateien auf das Datum des Tags setzen.
- (b) so lassen.
- Empfehlung: (a); der Store zeigt das Datum. Hinweis: der Plan nennt für Task 3 nur CHANGELOG.md als geänderte Datei, das Datum steht aber in allen drei; ob ein Test das Datum festhält, ist nicht geprüft (in test_store_metadata.py und test_changelog_translations.py steht es nicht).

Folge einer Abweichung in T: Ein geänderter Wortlaut braucht die Fassungen en, de und fr zugleich (Gleichschritt-Test). Die CHANGELOG-Dateien liegen außerhalb der auditierten Code-Pfade, ein Audit-Nachtrag ist dafür nicht nötig.

## Punkt D: Audit-Nachtrag 43-27 (Kenntnis)

Der Nachtrag über das Delta von 43-21 bis 43-26 (37b518d6..2dacf753) zählt 12 Befunde: 0 CRITICAL, 0 HIGH, 0 MEDIUM, 5 LOW, 7 INFO. Vier LOW sind behoben (F-43B-01, -02, -03, -05), F-43B-04 ist mit Begründung akzeptiert (N1 je Wurzel kostet Wurzeln mal Kandidaten, gerechnet, nicht gemessen); neuer audited_head ist 2dacf753fdaacca0c0e6341fc816006bc4d42001.

F-43B-05 stammt nicht aus dem auditierten Delta, sondern aus dem roten Lauf 43079756645 (ein StorageCrawlJob endete an "database is locked" ohne Nachfolger); der Wiederholungsweg ist durch fünf PHPUnit-Fälle belegt, nicht end to end, weil die Sperre im grünen Lauf in keinem Bein mit Fix auftrat.

Owner-LOW: keiner offen. Die drei LOW F-43B-01 bis -03 und F-43B-05 hat der Owner am 11.11.2026 je mit "A" zum Beheben entschieden; F-43B-04 ist kein Owner-Punkt.

Im Audit als nicht belegt geführt (43-AUDIT.md, 43-27-SUMMARY.md): Bandsperre und Neuaufbau auf ARM und bei 491.000 Zeilen in echt; MySQL und PostgreSQL für die N1-Abfragen; eine echte Fremdinstanz; wie lange der Abgleich in Produktion braucht, um einen abgebrochenen Mount nachzuholen; die volle Python-Suite lokal (sie lief im Workflow "Python gates" auf 2dacf753).

- (a) zur Kenntnis.
- (b) Rückfrage oder weiterer Fix vor dem GO.
- Empfehlung: (a); kein Befund ab MEDIUM, alle LOW entschieden, der Kopf ist end to end belegt.

## Punkt R: Testbuild (kein rc.2, Landebericht zu rc.1)

Ein rc.2 ist nie gebaut worden. 43-TESTBUILD-RC2.md hält das fest und führt die Maschinenzeile `Ergebnis: keine Antwort (Owner-Entscheid "Ok")`; "keine Antwort" heißt dort: es wurde keine Frage zu rc.2 gestellt. Was vorliegt, ist der Landebericht von mbozem zu rc.1 vom 09.11.2026 (https://github.com/street1983nk/nextcloud-search/issues/25#issuecomment-6746382180), wörtlich:

```
doc key backfill, done=3099 missing=0 unresolved=54   (17:41 CET)
coverage: documents=42156  indexable=251758  percent=16
          counting=false  provisional=false  deduplicated=true  legacyCount=false
```

- Zahl: 16 Prozent, 42.156 von 251.758. Vorhergesagt waren 18 Prozent (43.602 von 247.123). mbozem ordnet die Lücke den Unterwurzeln und Schreibweisen zu: "16 %, not 18, and the gap is exactly your two still-counts-twice cases." (Im Issue steht hinter "18" ein Gedankenstrich; er ist hier durch ein Komma ersetzt, sonst ist das Zitat wörtlich.)
- Dauer des ersten Aufbaus: "7.5 h for ~497k ledger rows".
- Urteil: "1.6.3 is good to go to the store from our side; we'll take the store release over the artifact whenever it lands."
- hashedUngrouped: hat er nicht gemeldet. rc.1 kennt das Feld nicht (`git grep hashedUngrouped rc/1.6.3-rc.1 -- php/lib` ohne Treffer, das Feld kam mit 43-23); die Zahl kann erst seine Rückmeldung zum Store-Release nennen.
- Antwort des Owners im Issue (09.11.2026): kein rc.2 zu installieren, 1.6.3 geht in den Store, sobald die Zusammenführung drin und geprüft ist.
- Versionsnachweis rc.1 auf 1.6.3: Beine upgrade-rc1 und upgrade-rc1-cf, beide grün im Lauf 43094681914.

- (a) zur Kenntnis, weiter ohne rc.2.
- (b) doch noch ein Testbuild vor dem Store.
- Empfehlung: (a); so ist es am 09.11. und 11.11. entschieden und mbozem zugesagt. Der Preis steht bei Punkt W: die Zahl nach der Behebung ist auf keiner echten Instanz gemessen.

## Punkt E: End-to-End-Beleg (Kenntnis)

- Lauf "Coverage end to end" 43094681914 auf aabc17cc1f311c21d5daa329c2a7b8af547e917f (nur Planungs-Commits hinter 2dacf753, Code gleich): success, sieben Beine grün. Sechs Beine liefen im zweiten Versuch, weil der erste beim Hochladen der Artefakte in einen Ausfall von GitHub Actions lief ("Failed to CreateArtifact"); gemessen hatten alle sieben schon im ersten Versuch failures=0.
- Die sieben Beine: gate-crawl / wrapped, gate-queue / wrapped, gate-queue / native, v1.6.2 / native, upgrade / native, upgrade-rc1 / native, upgrade-rc1-cf / native.
- Werte des Laufs (43-E2E-WURZEL.md, "Grüner Lauf auf dem Kopf mit Fix 2"): failures=0, 85 von 95 lebenden Zeilen indexiert, Suchprobe W5 15 von 15, in den fünf Beinen mit 1.6.3-Zählung hashedVerified 3, hashedUngrouped 2, k = 4, keine Zeile "coverage count without a vector stock".
- `scripts/ci/e2e_head_proof.sh` gegen 2dacf753: Exit 0. Acht Workflows auf 2dacf753 grün (IDs in 43-AUDIT.md, "Läufe auf audited_head").
- Mischbetrieb, Upgrades und Rückweg: die Ergebniszeilen stehen wörtlich nur für den Lauf 43016026129 (Fix 1) in 43-E2E-WURZEL.md: `upgrade_1_6_2: ok`, `rollback_1_6_2: ok` (zweimal), `second_upgrade_rename: ok` (zweimal), `mixed_container_first: ok`, `mixed_companion_first_pause: ok`, `upgrade_rc1: ok` (zweimal). Für den Lauf 43094681914 sind dieselben Beine grün und die Werte oben belegt; seine einzelnen Ergebniszeilen sind in der Datei nicht abgeschrieben.
- Offen trotz grünem Lauf (unverändert aus 43-26): das Urteil skipped/gone beim Claim ist nicht gezeigt (gone_path=not_exercised), die Zeitreserve der gate-Beine ist nicht abgesichert, die Linkfreigabe hat keine eigene Ergebniszeile. Nicht Teil des Laufs: ARM, eine echte Fremdinstanz, mehr als 96 Zeilen im Neuaufbau.

- (a) zur Kenntnis.
- (b) Rückfrage.
- Empfehlung: (a); der Kopf mit allen Fixes ist an einen grünen Lauf gebunden.

## Punkt K: Kenntnis zu Neuaufbau, Mischbetrieb und rc-Branch

**K1: Neuaufbau der Dokumentschlüssel nach dem Update**

Nach dem Update baut der Container alle Schlüssel einmal neu auf (von 1.6.2: erster Aufbau; von rc.1: Format 1 wird verworfen). So lange zeigt die Seite "wird gezählt" ohne Zahl, die Suche läuft normal.

Dauer je 1.000 Zeilen aus 43-E2E-WURZEL.md, "Dauer des Neuaufbaus je 1.000 Zeilen":

| Bein | Weg | Dauer | Zeilen | rechnerisch je 1.000 Zeilen |
|---|---|---|---|---|
| upgrade | 1.6.2 auf Kopf, Container zuerst | 293 s | 95 | 3.084 s |
| upgrade-rc1 | rc.1 auf Kopf, Container zuerst | 281 s | 96 | 2.927 s |
| upgrade-rc1-cf | rc.1 auf Kopf, Companion zuerst | 20 s | 95 | 211 s |

Dieselbe Datei sagt dazu: keine dieser Zahlen misst den Durchsatz, bei 95 Zeilen besteht die Dauer aus Wartezeit. Belastbar ist die Messung aus 43-16, rund 65 s je 1.000 Zeilen auf CI-Hardware. Daraus und aus den Konstanten (5.000 Zeilen je Runde, eine Runde je 300 s):

| Zeilen | aus den Konstanten | mit 65 s je 1.000 Zeilen | Quelle |
|---|---|---|---|
| rund 491.000 (mbozem) | 99 Runden, rund 8,2 h | rund 8,9 h | 43-AUDIT.md, I-43B-04 und Tabelle "Performance und Hochrechnungen" |
| 1.000.000 | 200 Runden, rund 16,7 h | rund 18,1 h | hier gerechnet, in keiner Datei belegt |

Alles gerechnet, nicht gemessen. Der einzige Messwert einer echten Instanz ist der erste Aufbau unter rc.1 bei mbozem: 7,5 h für rund 497.000 Zeilen (das sind rund 54 s je 1.000 Zeilen, hier gerechnet). Der Neuaufbau unter 1.6.3 ist bei dieser Größe nicht gemessen, ARM auch nicht. Bei "Container zuerst" kommen einmal bis zu 300 s Cooldown dazu.

**K2: Mischbetrieb (Tabelle aus 43-24, Soll)**

| Companion | Container | Ergebnis |
|---|---|---|
| 1.6.2 | 1.6.3 | kein /coverage (Companion fragt /status leaveOut), Backfill wartet (404) wie bisher |
| 1.6.3-rc.1 | 1.6.3 | /coverage 422 (kein docKeyFormat), Companion zeigt den 1.6.2-Weg; Reset auf Generation 2 läuft; Backfill wartet (kein format); Aufträge ohne docKeyFormat schreiben keinen Schlüssel |
| 1.6.3 | 1.6.3-rc.1 | /coverage 422 (extra forbid im rc.1-Modell), Companion zeigt den 1.6.2-Weg; rc.1 nimmt Format-2-Schlüssel ungeprüft an, das Update setzt sie mit Generation 2 zurück |
| 1.6.3 | 1.6.3 nach rc.1, vor dem ersten Reset (Backfill nicht armiert oder Backup-Pause) | /coverage counting=true über die Generationssperre, keine Zahl aus Format-1-Schlüsseln |
| 1.6.3 | 1.6.2 | /coverage 404, 1.6.2-Weg wie bisher |

End to end gezeigt sind die Zeilen 2 und 3 (Beine upgrade-rc1 und upgrade-rc1-cf), die Zeile 4 mit Backup-Pause (upgrade-rc1-cf) und die Zeile 1 im Bein upgrade (Container zuerst, "doc key backfill waits, the companion has no doc key route"). Zeile 5 ist der Weg von 1.6.2 wie bisher; ein eigener Beleg im Abnahmetest dieser Runde ist in den gelesenen Dateien nicht benannt. In keinem Fall zeigt die Seite eine Zahl aus alten Schlüsseln.

**K5: rc-Branch**

Der Plan spricht von beiden rc-Branches. Es gibt nur einen: rc/1.6.3-rc.1 (lokal und auf origin, Kopf 47c4ce4e7047d98a2bc4a494146953821f4dbc29); ein Branch für rc.2 ist nie entstanden. Er bleibt bis nach dem Release stehen und wird nie nach main gemergt; ob er gelöscht wird, fragt 43-14 mit eigener Freigabe (Löschen eines Remote-Branches ist ein Push). Das Artefakt des Testbuilds läuft am 2026-12-08 ab.

- (a) zur Kenntnis (K1, K2, K5).
- (b) Rückfrage.
- Empfehlung: (a); K1 geht als Hinweis in I2, K5 wird in 43-14 entschieden.

## Punkt I: Außentexte (Entwürfe, englisch)

**I1: Forum-Post** (Thread 249775, Owner postet; Datei `C:/Users/Student/Desktop/Findling_1.6.3_Forum_ENTWURF.md`, Stand Runde 2), wörtlich:

```
Findling 1.6.3 is in the store (update both apps together).

New in 1.6.3:
- Coverage counts every document once: per-user mounts of the same share no longer inflate the figure
- One share configured with different roots, or with the server or share name in a different case, counts once
- Documents of deleted or unmounted storages leave the index even while the crawl is busy
- A note on the admin page explains the lower figures after the update, and files that could not be read are shown with a remedy
- Locked or refused files on SMB storage no longer block a PHP worker

Changelog: https://github.com/street1983nk/nextcloud-search/releases/tag/v1.6.3
```

**I2: Antwort in #25** (NACH dem Store-Release, mit eigener Freigabe in 43-14; OHNE Schließen: das Issue schließt mbozem oder wir erst nach seiner Bestätigung, kein "Closes"), wörtlich:

```
1.6.3 is in the app store now, update both apps together. Thanks again for the rc.1 test and the two topology posts, the fold for sub-roots and spelling is built on them.

Coming from rc.1 (or straight from 1.6.2) the document keys are rebuilt once, so the page says "being counted" again. On an instance your size that can take hours, I'd reckon 8 to 9 for your ~491k rows, and the search works normally meanwhile. After that you should land around 18 %.

Could you confirm the figure on the store build? I'll leave this one open until then.
```

Belege zu I2: "being counted" ist der Zustand der Seite aus dem Kommentar vom 09.11.; 8 bis 9 Stunden bei 491.000 Zeilen ist gerechnet (43-AUDIT.md, K1); "around 18 %" ist die Erwartung aus dem Verlauf (mbozem und Owner am 09.11.), nicht gemessen. Der Fall "von rc.2" entfällt, es gibt kein rc.2. Die Bitte um die Zahl hashedUngrouped (43-TESTBUILD-RC2.md) ist bewusst nicht im Text: sie steht nur in der Overview-Antwort und stündlich im Log, eine Nachfrage dazu passt besser in die Antwort auf seine Rückmeldung.

- (a) beide so.
- (b) Änderung je Text nennen.
- (c) I2 mit einem Zusatzsatz zu hashedUngrouped.
- Empfehlung: (a); kurz, nur Neuerungen, I2 dankt, nennt die Wartezeit ehrlich und lässt das Issue offen.

## Punkt F: GO für Tag und Einreichung

EIN Wort für ZWEI unumkehrbare Handlungen, die der Owner selbst ausführt: (1) Tag v1.6.3 annotiert auf den grünen, auditierten und end to end belegten Kopf und Push des Tags, (2) danach Auslösen der Store submission für beide Apps. Claude bereitet Befehle und Belege vor und prüft danach jede Belegzeile.

- audited_head = 2dacf753fdaacca0c0e6341fc816006bc4d42001 (43-AUDIT.md).
- Tag-Kopf nach der Regel `git log -1 --format=%H -- . ':!.planning'`, am 11.11.2026 neu gelesen: 2dacf753fdaacca0c0e6341fc816006bc4d42001, also gleich dem audited_head. Nach dem Entscheid kommen in Task 3 die Text-Commits dazu (CHANGELOG nach Punkt T, Gesamttext Runde 2 in docs/store-listing.md, Gate scan_full_text_1_6_3); der Tag-Kopf ist dann deren letzter Commit.
- Bedingungen für den Tag-Kopf: leerer Code-Diff audited_head..Tag-Kopf über backend/src, backend/docker, backend/appinfo, php/appinfo, php/lib, php/js, php/templates, php/l10n, .github/workflows und scripts; `scripts/ci/e2e_head_proof.sh <Tag-Kopf> 43-E2E-WURZEL.md` grün; sieben Workflows grün per scripts/ci/head_green.sh. Der sha steht danach als `Tag-Kopf:` in 43-ABNAHME.md unter Runde 2.
- Was das GO NICHT deckt: einen Push (Punkt P) und die Antwort in #25 (43-14).

Restrisiken, offen benannt: die Zahl nach der Behebung ist auf keiner echten Instanz gemessen (Punkt W, R); der Neuaufbau bei rund 491.000 Zeilen dauert gerechnet 8 bis 9 Stunden ohne Zahl auf der Seite (K1); der Wiederholungsweg von F-43B-05 ist nur durch PHPUnit belegt (Punkt D).

- (a) GO.
- (b) warten.
- Empfehlung: (a); G2 ist aufgehoben (`d_43_15: behoben`), der Kopf ist auditiert und end to end grün, mbozem hat rc.1 freigegeben ("good to go to the store from our side"), und kein Restrisiko berührt Suche, Rechte oder Daten, nur die Zahl auf der Admin-Seite.

## Punkt P: Push der Abnahme-Commits (getrennt vom GO)

Das GO deckt keinen Push (B5). Eigene Frage: Darf Claude die Abnahme-Commits dieser Runde (Vorlage Runde 2, 43-ABNAHME.md, 43-FREIGABEN.md, CHANGELOG nach Punkt T, Gesamttext Runde 2, Gate) nach `git pull --rebase` auf main pushen? Die Antwort wird als `Freigabe Push 43-12 Runde 2: <Zitat> (<Datum>, <Kanal>) Entscheid: ja|nein` in 43-FREIGABEN.md festgehalten, die Antwort zu T als `Freigabe Text 43-12 Runde 2: ...`; die Zeile `Freigabe Push 43-12:` aus Runde 1 ist verbraucht. Ohne "Entscheid: ja" bleibt alles lokal.

- (a) ja.
- (b) nein (Owner pusht selbst oder später).
- Empfehlung: (a); ohne Push gibt es keinen grünen CI-Beleg des Tag-Kopfs.

## Umlaut-Audit Runde 2 (Regel 24.10.2026)

Umfang: alle in 1.6.3 neuen oder geänderten deutschen Texte, über die Deltas v1.6.2..HEAD (Kopf 95e19139, dazugefügte Zeilen je Datei). Vorfilter `grep -nE "(ae|oe|ue)[a-z]|ss[^a-z]"`, dazu eine Suche nach ASCII-Ersatzwörtern (gross, heiss, ausser, schliess, fuer, ueber, koenn, muess, waehr, zaehl, laeuft, spaeter, groesse, moegl, aender, naech, pruef, loesch, oeffn, haeng, eintraeg, stoer, gemaess, massnahm, strasse); jede Fundstelle von Hand beurteilt.

| Text | Vorfilter-Treffer (Zeilen) | Wörter der Treffer | echte Funde |
|---|---|---|---|
| CHANGELOG.de.md (neu seit Runde 1, 78 Zeilen, zusätzlich ganz gelesen) | 4 | viermal "sodass" | 0 |
| php/l10n/de.json, de.js, de_DE.json, de_DE.js (je sechs Werte, seit Runde 1 unverändert, alle vier Fassungen wertgleich) | je 2 | deutsch "dauern", englisch "access" im Schlüssel | 0 |
| docs/store-listing.md (177 dazugefügte Zeilen) | 13 | dauern, neueste, erneuert, Quellpflicht; englisch access, success, across; französisch quelques; der Verzeichnisname sweep-und-zaehler in einem Pfad | 0 |
| docs/l10n-{dutch,french,italian,portuguese,spanish}.md (je zwei deutsche Nachtrag-Absätze) | 3, 2, 5, 3, 5 | "dauern", englisch "access", sonst niederländische, italienische, portugiesische und spanische Wörter (zum Beispiel toegangsrechten, questo, bloqueado, puede) | 0 |
| DESIGN.md (neu, intern, nicht nutzersichtbar) | 11 | neuer, muss, einbauen, Ausschluss; CSS-Namen wie color-success | 0 |
| PRODUCT.md (neu, intern, nicht nutzersichtbar) | 23 | Quelle (21-mal), Quellenangabe, visuelle, schauen, muss, dass | 0 |
| docs/testing.md | 10 | englischer Text | 0 |
| ASCII-Ersatzwort-Suche über alle genannten Deltas | 2 | der Pfad sweep-und-zaehler (Verzeichnisname, bleibt ASCII), spanisch "fuera de línea" | 0 |
| CHANGELOG.md, CHANGELOG.fr.md, Release-Notiz, Forum-Entwurf, I2 | englisch und französisch | keine deutsche Prosa | 0 |
| diese Vorlage, Abschnitt Runde 2 | siehe "Prüfung dieser Vorlage, Runde 2" | | 0 |

Ergebnis: 0 echte Funde, keine Korrektur nötig; kein eigener Entscheidungspunkt.

Beobachtung ohne Umlaut-Bezug, nur zur Kenntnis: CHANGELOG.de.md schreibt "Id" und "Nutzer-Id" (Punkt T3), üblich wäre "ID". Nicht geändert; wer es ändern will, nennt "T3 b".

## Prüfung dieser Vorlage, Runde 2

- Umlaut-Vorfilter über den Abschnitt Runde 2: Treffer sind die Suchwörter der Methodenzeile, die im Audit zitierten Wörter, englische und französische Wörter in den Entwürfen und korrekte deutsche Wörter (zuerst, Dauer, dauern, dauert, neuer, neuen, Neuerungen, Quelle, dass, muss); 0 echte Funde.
- Keine U+2013 und keine U+2014, keine Emojis (Byte-Suche). Ein Gedankenstrich im Zitat von mbozem (Punkt R) ist durch ein Komma ersetzt und dort so gekennzeichnet.
- Runde 1 oben ist unverändert (die ersten 14.690 Bytes der Datei sind gleich dem Stand vor diesem Abschnitt).
- "wie empfohlen" deckt B, C, T1 bis T6, D, R, E, K und I; F und P brauchen je das eigene Wort (GO ja|nein, P ja|nein).
- Abweichungen vom Wortlaut des Plans 43-12, alle Folge des gestrichenen rc.2: Punkt R nennt statt eines rc.2-Ergebnisses den Landebericht zu rc.1; I2 lässt den Fall "von rc.2" weg; K5 nennt einen rc-Branch statt zwei. Dazu: acht statt sieben Workflows liefen auf dem audited_head (der achte ist OpenSSF Scorecard).
