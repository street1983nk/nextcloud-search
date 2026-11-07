# Phase 43: Wortlaute zur Freigabe (D-43-06)

Stand: 2026-11-07 10:05, Plan 43-01 Task 1 (Entwurf, noch nicht freigegeben)

Vier Blöcke mit neuen Sätzen für den Abschnitt "Deckungsgrad der Suche" der Admin-Seite.
Der englische Satz ist der Katalogschlüssel und steht so im Template und in admin.js;
Deutsch gilt für `de` und `de_DE`, Französisch für `fr`. Die Sprachen es, it, nl, pt_BR
und pt_PT entstehen in 43-06 als maschineller Entwurf unter Vorbehalt (Muster 39-01)
und werden hier nicht abgefragt. Erst nach der Freigabe (Maschinenzeilen am Ende)
schreibt 43-06 die Sätze in Kataloge, Template und admin.js.

Begriffe nach dem Bestand der Kataloge und `docs/l10n-french.md`: Deckungsgrad /
coverage / couverture, durchsuchbar / searchable / peuvent être trouvés par la recherche,
Zahl / figure / chiffre, externer Speicher, je Nutzer eingebunden / external storage
mounted per user / stockage externe monté par utilisateur, Speicherort / storage /
espace de stockage, mehrfach hängen geblieben / stuck repeatedly / bloqué à plusieurs
reprises. Keiner der französischen Sätze enthält `:`, `;`, `?`, `!` oder Guillemets,
die Leerzeichenfrage vor diesen Zeichen stellt sich hier also nicht.

## Block H: einmaliger Hinweis nach dem Update (D-43-06 mit D-43-12)

- **Zweck:** Der Admin soll wissen, warum die Zahlen nach dem Update kleiner sind, und
  es nicht für einen Fehler oder Datenverlust halten.
- **Ort:** eigener Hinweis (`findling-coverage-per-document`) direkt unter der Unterzeile
  "%1$s von %2$s indexierbaren Dateien sind durchsuchbar".
- **Sichtbar:** nur auf Bestandsinstanzen nach dem Update auf 1.6.3 (Frischinstallationen
  sehen ihn nie).
- **Verschwindet:** sieben Tage nach der ersten vollständigen Zählung pro Dokument, von
  selbst (D-43-12).

### Variante (a): Recherche-Entwurf plus Satz zur Dauer

| | Wortlaut |
|---|---|
| EN | Since version 1.6.3, every document counts once, even when external storage is mounted separately for each user. The figures can therefore be lower than before. This note disappears seven days after the first complete count. |
| DE | Seit Version 1.6.3 zählt jedes Dokument einmal, auch wenn ein externer Speicher für jeden Nutzer einzeln eingebunden ist. Die Zahlen können deshalb niedriger sein als vorher. Dieser Hinweis verschwindet sieben Tage nach der ersten vollständigen Zählung. |
| FR | Depuis la version 1.6.3, chaque document compte une seule fois, même si un stockage externe est monté séparément pour chaque utilisateur. Les chiffres peuvent donc être plus bas qu'avant. Cette note disparaît sept jours après le premier comptage complet. |

### Variante (b): mit dem Grund (Empfehlung)

| | Wortlaut |
|---|---|
| EN | Since version 1.6.3, every document counts only once. Until now, external storage mounted separately for each user was counted once per mount, which is why the figures can now be lower than before. This note disappears seven days after the first complete count. |
| DE | Seit Version 1.6.3 zählt jedes Dokument nur einmal. Bisher wurde ein externer Speicher, der für jeden Nutzer einzeln eingebunden ist, je Einbindung gezählt, deshalb können die Zahlen jetzt niedriger sein als vorher. Dieser Hinweis verschwindet sieben Tage nach der ersten vollständigen Zählung. |
| FR | Depuis la version 1.6.3, chaque document ne compte qu'une seule fois. Jusqu'ici, un stockage externe monté séparément pour chaque utilisateur était compté une fois par montage, c'est pourquoi les chiffres peuvent désormais être plus bas qu'avant. Cette note disparaît sept jours après le premier comptage complet. |

**Empfehlung (b):** Der Grund steht im Satz, und der dritte Satz sagt vorab, dass der
Hinweis von selbst geht. Sonst weiß der Admin beim Verschwinden nicht, ob das gewollt ist.

**Abweichung vom Recherche-Entwurf:** "eine Freigabe" ist durch "ein externer Speicher"
ersetzt, weil der vorhandene 1.6.2-Satz ("Je Nutzer einmal eingebundene externe Speicher
werden hier je Einbindung gezählt ...") genau diesen Begriff führt. "Die Zahl" ist zu
"die Zahlen" geworden, weil beide Werte der Unterzeile sinken können, der Prozentwert
dagegen nicht zwingend. "Ab Version" ist zu "Seit Version" geworden, weil der Satz erst
nach dem Update zu lesen ist.

## Block Z: Zählung läuft noch (ersetzt im neuen Zählweg "The count of indexable files is being updated")

- **Zweck:** ehrlicher Zustand, solange der Container pro Dokument zählt; der alte Satz
  "wird neu ermittelt, danach erscheint der Anteil wieder" wäre im neuen Zählweg falsch.
- **Ort:** `findling-coverage-counting`, an der Stelle von Prozentzahl und Unterzeile
  (beide sind in diesem Zustand verborgen).
- **Sichtbar:** genau solange `counting` wahr ist.
- **Verschwindet:** sobald die Zählung fertig ist und die Zahl erscheint.

### Variante (a): Empfehlung

| | Wortlaut |
|---|---|
| EN | The coverage is being counted document by document. On large instances this can take some time, and the search keeps working normally meanwhile. The figure appears here as soon as the count is finished. |
| DE | Der Deckungsgrad wird gerade pro Dokument gezählt. Auf großen Instanzen kann das einige Zeit dauern, die Suche arbeitet währenddessen normal weiter. Die Zahl erscheint hier, sobald die Zählung fertig ist. |
| FR | La couverture est en cours de comptage, document par document. Sur les grandes instances, cela peut prendre un certain temps, et la recherche continue de fonctionner normalement. Le chiffre s'affiche ici dès que le comptage est terminé. |

### Variante (b): eigener Wortlaut des Owners

**Abweichung vom Planentwurf:** "Die Abdeckung" ist zu "Der Deckungsgrad" geworden (Begriff
der Überschrift und aller vorhandenen Sätze). "Die Zahl erscheint hier in Kürze" ist ersetzt,
weil "in Kürze" nach dem Update nicht stimmt: Auf einer Instanz wie der von mbozem
(190.000 Zeilen) läuft zuerst der Backfill der Dokumentschlüssel, und die Seite zeigt so
lange diesen Satz (K1 in 43-12). Der Satz zur Suche nimmt die Sorge, dass während der
Zählung nichts gefunden wird.

## Block U: nicht lesbare oder hängen gebliebene Dateien (D-43-11)

- **Zweck:** erklärt, warum der Deckungsgrad unter 100 Prozent bleibt, obwohl die
  Warteschlange leer ist (z. B. 190 von 200 = 95 Prozent bei SMB-Zugriffsrechten).
- **Ort:** `findling-coverage-not-readable`, eine Zeile unter der Unterzeile.
- **Sichtbar:** nur wenn die Zahl größer als 0 ist; `%s` ist die Anzahl.
- **Verschwindet:** sobald keine solche Datei mehr gezählt wird.

### Variante (a): Empfehlung

| | Wortlaut |
|---|---|
| EN | %s files could not be read or got stuck repeatedly. They count as not searchable and lower the coverage figure. |
| DE | %s Dateien konnten nicht gelesen werden oder sind mehrfach hängen geblieben. Sie zählen als nicht durchsuchbar und senken den Deckungsgrad. |
| FR | %s fichiers n'ont pas pu être lus ou sont restés bloqués à plusieurs reprises. Ils ne peuvent pas être trouvés par la recherche et font donc baisser la couverture. |

### Variante (b): eigener Wortlaut des Owners

**Abweichung vom Planentwurf:** "sind gelistet, aber" ist gestrichen, weil "gelistet" ein
Wort aus dem Innenleben ist; für den Admin zählt, dass die Datei da ist und nicht gelesen
werden konnte. "hängen geblieben" ist zu "mehrfach hängen geblieben" geworden wie der
vorhandene Grund "Mehrfach hängen geblieben" (FR "Bloqué à plusieurs reprises"), denn
gezählt werden nur Dateien, die PHP nach mehreren Versuchen aufgibt. "non consultables"
ist durch die Wendung des Bestands "peuvent être trouvés par la recherche" ersetzt. Der
Zusatz "senken den Deckungsgrad" sagt, warum die Zahl darüber kleiner ist.

## Block L: sichtbarer Rückfall auf die Zählweise von 1.6.2 (W10)

- **Zweck:** Über den Grenzen der neuen Zählung (mehr als 50.000 Speicherorte oder mehr als
  1000 Mitglieder einer Gruppe) zählt die Seite wie 1.6.2, aber nie still.
- **Ort:** `findling-coverage-legacy`, unter der Unterzeile.
- **Sichtbar:** nur bei `legacyReason = limits`.
- **Verschwindet:** sobald die Instanz wieder unter den Grenzen liegt.

### Variante (a): Empfehlung

| | Wortlaut |
|---|---|
| EN | This instance has more storages than the count per document can handle. The figure is therefore counted per storage as in version 1.6.2, and a file mounted for several users can stand in it several times. |
| DE | Diese Instanz hat mehr Speicherorte, als die Zählung pro Dokument verarbeiten kann. Die Zahl wird deshalb wie in Version 1.6.2 je Speicherort gezählt, und eine Datei, die für mehrere Nutzer eingebunden ist, kann mehrfach darin stehen. |
| FR | Cette instance compte plus d'espaces de stockage que le comptage par document ne peut en traiter. Le chiffre est donc compté par espace de stockage comme dans la version 1.6.2, et un fichier monté pour plusieurs utilisateurs peut y figurer plusieurs fois. |

### Variante (b): eigener Wortlaut des Owners

**Abweichung vom Planentwurf:** "Speicher" ist zu "Speicherorte" geworden wie im
vorhandenen Satz "Vorläufige Zahl, %1$s von %2$s Speicherorten sind durchgezählt"
(FR "espaces de stockage"). "kann zu hoch sein" ist durch den Grund ersetzt, denn die
Zahl ist nicht beliebig zu hoch, sondern genau um die Mehrfacheinbindungen.

**Fall `legacyReason = missing` (Backend noch auf 1.6.2):** Kein eigener Satz nötig. In
diesem Fall melden die beiden Hälften verschiedene Versionen, und im selben Abschnitt
erscheint schon das Banner "Die beiden Hälften von Findling melden unterschiedliche
Versionen ... Beide Hälften auf dieselbe Version bringen." (`findling-banner-lockstep`).
Will der Owner trotzdem einen Satz, käme als Vorschlag in Frage: EN "The backend is still
on an older version and cannot count per document yet, so the figure is counted as in
version 1.6.2." / DE "Das Backend ist noch auf einer älteren Version und kann noch nicht
pro Dokument zählen, deshalb wird die Zahl wie in Version 1.6.2 gezählt." / FR "Le service
est encore dans une version plus ancienne et ne peut pas encore compter par document, le
chiffre est donc compté comme dans la version 1.6.2." Dann kämen die Zeilen
`EN-LEGACY-MISSING`, `DE-LEGACY-MISSING` und `FR-LEGACY-MISSING` dazu.

## Selbstprüfung

- Deutsche Zeilen mit echten Umlauten (zählt, für, können, verschwindet, vollständigen,
  großen, währenddessen, hängen, mehr, Version), kein ae/oe/ue/ss-Ersatz.
- Keine U+2013 und keine U+2014.
- Je Block und Sprache höchstens drei Sätze.
- Platzhalter: nur Block U trägt `%s`, in allen drei Sprachen genau einmal.

## Maschinenzeilen (Task 2 füllt sie nach der Antwort des Owners)

Freigabe: 
Zitat: 
Datum: 
Kanal: 
EN-HINT: 
DE-HINT: 
FR-HINT: 
EN-COUNTING: 
DE-COUNTING: 
FR-COUNTING: 
EN-UNREADABLE: 
DE-UNREADABLE: 
FR-UNREADABLE: 
EN-LEGACY: 
DE-LEGACY: 
FR-LEGACY: 
