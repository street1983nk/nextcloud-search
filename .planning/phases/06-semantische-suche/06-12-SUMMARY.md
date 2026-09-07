---
phase: 06-semantische-suche
plan: 12
subsystem: release
tags: [store-abgabe, v1-0-0, d-08, d-11, d-12, d-17, d-26, tag-nach-phase-6, screenshots, t-06-58]

# Dependency graph
requires:
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: "05-17/05-18: die dreisprachigen Store-Texte, die drei Bilder, die Release-Strecke mit beiden Signaturen und den vier Upload-Stolperstein-Pruefungen"
  - phase: 06-semantische-suche
    provides: "06-09 (zweite Deckungszahl), 06-10 (Offline-Nachweis), 06-11 (die Zahlen: Einbettungsdauer, RSS)"
  - phase: 06.1-launch-haertung-vor-der-store-abgabe
    provides: "die Owner-Abnahme der Haertung als Startfreigabe (Owner-Regel vom 06.09.), die Nachmessung 1.813 MB (06.1-18), die Messsatz-Gleichheit in drei Dateien"
provides:
  - "Findling 1.0.0 IM STORE: beide Apps registriert (HTTP 201) und beide Releases gemeldet (HTTP 201) am 07.09.2026 ~16:34Z; apps.nextcloud.com/apps/findling und /apps/findling_backend antworten 200"
  - "Tag v1.0.0 auf 160a289 (Semantik + Launch-Haertung), Owner-Entscheid tag-nach-phase-6"
  - "Store-Texte EN/DE/FR mit den drei D-17-Zusagen und dem erweiterten Privacy-Block (huggingface-hub, requests, Offline-Beweis, Modell im Abbild)"
  - "beide Screenshots zeigen 1.0.0: semantischer Treffer mit Gegenprobe-Beleg, Admin-Seite mit beiden Deckungszahlen"
  - ".github/workflows/store-submit.yml: die Einreichung als manueller Workflow, Secrets verlassen den GitHub-Speicher nie"
affects: [phase-abschluss, v1.1, connector-synergie BL-01..03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Einreichung, die ein Secret braucht, laeuft dort, wo das Secret liegt (workflow_dispatch), statt das Secret zur Sitzung zu holen"
    - "Ein Tag auf einem Commit ohne backend/-Beruehrung braucht workflow_dispatch auf dem Tag-Ref fuer docker.yml (der Workflow-Kommentar sagt es selbst)"

key-files:
  created:
    - .github/workflows/store-submit.yml
  modified:
    - docs/store-listing.md
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - store/media/screenshot-search.png
    - store/media/screenshot-admin.png
    - store/media/README.md
---

# Phase 6 Plan 12: Die gebuendelte Store-Abgabe 1.0.0 Summary

**Eingangsstand (Task 4): EINGEREICHT UND ANGENOMMEN.** Beide Registrierungen
und beide Release-Meldungen antworteten HTTP 201 (Lauf 34143894059, 07.09.2026
16:34Z), beide Store-Seiten sind seither oeffentlich erreichbar (HTTP 200).
Die Phase endet mit einer Tatsache: Findling 1.0.0 und Findling Backend 1.0.0
stehen im Nextcloud App Store.

## Task 1: Owner-Entscheid tag-nach-phase-6

Es gab noch keinen Tag (Plan 05-19 wurde in 06.1-15 aufgeloest und hat den
Tag ausgelassen). Der Owner entschied am 07.09.: v1.0.0 wird erst jetzt
gesetzt, auf den Stand mit Semantik und Launch-Haertung. Damit weicht die
Ausfuehrung von Plan 05-19 in genau diesem Punkt ab, und ein Name meint einen
Stand: Tag, Archive und Store-Zahlen kommen alle von 160a289.

## Task 2: Texte und Bilder

- Beide info.xml und docs/store-listing.md (wieder wortgleich) tragen in
  EN/DE/FR die drei D-17-Zusagen: (a) Einbettungsdauer 18 h 04 min erste
  Spur, 18 h 56 min bis zum letzten Vektor, 52 Minuten Nachlauf; (b) die
  Abdeckungsaussage aus docs/embeddings.md woertlich, mit dem gemessenen
  Anteil 12,5 Prozent; (c) die RSS-Zahl 1.813 MB (stand seit 06.1 drin, die
  alte 422 ist aus store-listing.md verschwunden). Kein Tokendeckel beworben,
  kein Connector-Querverweis (D-12, Content-Hit-Fidelity-Test steht aus).
- Privacy-Block: Modell im Abbild, kein Download beim ersten Start, die zwei
  Netzwerkbibliotheken huggingface-hub und requests namentlich, der
  Offline-Beweis (docker.yml, --network none, beide Architekturen), kein
  Text, kein Vektor, keine Anfrage verlaesst den Server.
- Suchbild neu: die Frage "Wann muss ich spaetestens absagen, damit es nicht
  weiterlaeuft?" findet Kuendigung-Lagerflaeche-Sued.docx; kein
  inhaltstragendes Wort der Frage steht im Dokument, und zwei nur-lexikalische
  Gegenproben (Phrase, Minus-Operator) finden nichts. Admin-Bild neu: beide
  Deckungszahlen (87 Prozent Volltext, 87 Prozent nach Bedeutung), die vier
  Zaehler, der Uebersprungen-Grund Password protected. store/media/README.md
  traegt die neuen Groessen, Masse und SHA-Praefixe.
- docs/testing.md unveraendert: kein Gate wurde durch die Texte beruehrt
  (der Messsatz blieb wortgleich, die Gates liefen unveraendert gruen).
- Owner-Sichtprobe der Texte und Bilder am 07.09. im Chat: "sieht gut aus".

## Task 3: Tag, Release-Strecke, die vier Stolpersteine

- Tag v1.0.0 auf 160a289, Release-Lauf gruen; alle sieben Workflows auf dem
  Tag-Ref gruen. docker.yml lief zusaetzlich per workflow_dispatch auf dem
  Tag-Ref, weil 160a289 backend/ nicht beruehrt (der im Workflow-Kommentar
  beschriebene Weg); ghcr.io/street1983nk/findling_backend:1.0.0 ist public,
  amd64+arm64.
- Die vier Stolpersteine: (1) Signaturweg: die Strecke signiert das eine
  Archiv, das sie hochlaedt, und zur Abnahme wurden beide veroeffentlichten
  Assets HERUNTERGELADEN und die Signaturen gegen die Upstream-Zertifikate
  verifiziert (Verified OK beidseitig); (2) kein leeres info.xml-Element
  (Gate + XSD); (3) Lockstep 1.0.0 beidseitig inkl. image-tag; (4) beide
  info.xml validieren gegen die Store-XSD (transform + schema).
- Pruefsummen (SHA-256):
  findling.tar.gz    8a109225925d82c39bd5fbefbc3454aa00fd02e16e0b56e1d31a167f5c94325b
  findling_backend.tar.gz  603ca14875a8df90a309d0f4f2941c64bcbb14497c5a9adb5fb830a9d61d2fc6

## Die Einreichung, und warum sie doch aus dieser Sitzung kam

Der Plan sah die Einreichung beim Owner. Der Owner beauftragte sie am 07.09.
ausdruecklich im Chat ("kannst du einreichen?"), und der Weg respektiert die
Secret-Regeln: .github/workflows/store-submit.yml (nur workflow_dispatch)
registriert die App-Ids mit den Signierschluesseln und meldet die Releases mit
APPSTORE_TOKEN, alles innerhalb des GitHub-Secret-Speichers; kein Secret
erreichte die Sitzung, kein Schritt druckt eines. Keine Mail, kein Formular,
kein Browser im Namen des Owners.

## Abweichungen und Notizen

- Plan 05-19-Abweichung (Tag erst jetzt) wie oben, Owner-Entscheid.
- Der Medien-Commit 160a289 loeste wegen der Pfadfilter keinen CI-Lauf aus;
  die Gates dazu liefen lokal (48/71 passed je Lauf) und danach komplett auf
  dem Tag-Ref.
- Restmuell ausserhalb dieses Plans, Owner-Ok steht aus: der 05-18-Stack
  findling-shot-app-1 (Port 8091) samt Volume findling-shot_nextcloud, und
  das verwaiste Volume nc_app_findling_backend_data der abgebauten
  Sichtprobe-Instanz.
- Fuer Wiederholungen auf dieser Maschine (vom Medien-Lauf): Git-Bash
  verstuemmelt -e VAR=/pfad ohne MSYS_NO_PATHCONV=1, und nach dem Neuerzeugen
  des Backend-Containers braucht es app_api:app:disable/enable, sonst bleibt
  der Poller stumm.

## Verification

- Alle sieben Workflows gruen auf v1.0.0 (Python, PHP/Store, Integration,
  Resilience, HaRP, Multi-arch, Release).
- Beide Signaturen ueber die heruntergeladenen Assets: Verified OK.
- Store-Antworten: 4x HTTP 201; beide Store-Seiten HTTP 200.
- Kein Em-Dash und kein En-Dash in den geaenderten Textdateien.
