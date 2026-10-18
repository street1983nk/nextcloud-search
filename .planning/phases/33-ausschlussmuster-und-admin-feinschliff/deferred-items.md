# Phase 33: Zurückgestellte Funde

## Aus Plan 33-07 (14.10.2026)

- **Store-Text sagt noch "box".** `php/appinfo/info.xml:67` und `backend/appinfo/info.xml` tragen
  "free at most half of the box (Standard profile)"; `docs/store-listing.md:1367` begründet das Wort
  mit dem englischen Satz der Verwaltungsseite ("How much of this box Findling may use"), den Plan 33-07
  nach G5 (c) ersetzt hat. Der Store-Text reist mit dem Release und braucht laut Owner-Regel einen
  Entwurf zur Abnahme, deshalb nicht in 33-07 geändert. Vorschlag für Phase 36 (Release-Text 1.5.0):
  "box" dort ebenfalls ersetzen, Wortwahl wie auf der Seite ("the hardware Findling sees").

## Aus Plan 33-11 (Audit, 18.10.2026)

- **SubtreeExpandJob nach geleertem Papierkorb.** Wird ein Ordner gelöscht und der Papierkorb des
  Nutzers vor dem nächsten cron geleert, endet der Löschjob (`kind` delete) mit
  `OCP\DB\Exception: Could not fetch storage root` aus `FileAccess::getByAncestorInStorage`
  (`php/lib/BackgroundJobs/SubtreeExpandJob.php:159`, Zeile aus e3de49a2 vom 01.09.2026, nicht im Diff von Phase 33).
  Folge wie L-32-05: die Dokumente bleiben bis zum nächsten Abgleich; dazu eine Fehlerzeile Level 3
  je Job. Auf 8090 gesehen beim Aufräumen der Audit-Proben (ancestor 3025, 3031, 3037, 3091).
  Vorschlag für Phase 36: den Fall fangen und als "Teilbaum weg" ohne Fehlerzeile beenden.
