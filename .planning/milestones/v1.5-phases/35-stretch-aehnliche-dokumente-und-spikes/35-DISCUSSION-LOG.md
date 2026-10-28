# Phase 35: Stretch: Aehnliche Dokumente und Spikes - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md , this log preserves the alternatives considered.

**Date:** 2026-10-19
**Phase:** 35-stretch-aehnliche-dokumente-und-spikes
**Areas discussed:** Bedienung Aehnliche Dokumente, granite-Messaufbau, Wortlaut-Prozess, Form der Dedup-Notiz

---

## Bedienung Aehnliche Dokumente

| Option | Description | Selected |
|--------|-------------|----------|
| Textlink unter dem Treffer | Link unter Pfad/Auszug, zweiter Tab-Stopp, Link-Muster der Seite | ✓ |
| Icon-Button am Zeilenende | Platzsparender, neues Interaktionsmuster, Tooltip-Erklaerung | |
| You decide | Claude waehlt nach Seitenmuster | |

**User's choice:** Textlink unter dem Treffer

| Option | Description | Selected |
|--------|-------------|----------|
| Neue Serveransicht | GET-Link auf dieselbe Ergebnisseite (?similar=fileId), kein neues JS | ✓ |
| Inline aufklappen | Nachbarn per JS unter dem Treffer, Scroll-/Fokus-Handling noetig | |
| You decide | | |

**User's choice:** Neue Serveransicht

| Option | Description | Selected |
|--------|-------------|----------|
| 10, normale Trefferliste | Gleiche Hit-Liste, ohne Suchbegriff-Markierung, nach PHP-Recheck | ✓ |
| 5, kompakte Liste | Kuerzer, eventuell zu wenig bei grossen Bestaenden | |
| You decide | | |

**User's choice:** 10, normale Trefferliste

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, mit Rueckweg | Kopf nennt Ausgangsdatei, Link zurueck zur vorigen Trefferliste | ✓ |
| Nur Ausgangsdatei, kein Rueckweg | Browser-Zurueck reicht | |
| You decide | | |

**User's choice:** Ja, mit Rueckweg

---

## granite-Messaufbau

| Option | Description | Selected |
|--------|-------------|----------|
| AWS m7g mieten | Gleiche Basis wie September-Messung, Owner gibt Instanz frei | ✓ |
| Eigene ARM-Box | Keine Mietkosten, andere Hardware als Referenz | |
| Nur amd64 + Schaetzung | Schwaechere Aussage fuer v1.6-Empfehlung | |

**User's choice:** AWS m7g mieten

| Option | Description | Selected |
|--------|-------------|----------|
| Bestehender Messkorpus | Vergleichbar mit frueheren Zahlen | ✓ |
| Ratsvorlagen-Auszug | Realistischere Verwaltungssprache, neue Vergleichsbasis | |
| Beides | Mehr Aufwand | |

**User's choice:** Bestehender Messkorpus

| Option | Description | Selected |
|--------|-------------|----------|
| Feste Frage-Treffer-Paare | Vor der Messung definiert, automatisch auswertbar | ✓ |
| Plus Owner-Stichprobe | Zusaetzliche manuelle Sichtprobe | |
| You decide | | |

**User's choice:** Feste Frage-Treffer-Paare

---

## Wortlaut-Prozess

| Option | Description | Selected |
|--------|-------------|----------|
| Vorab-Plan wie 34-01 | Saetze de/en/fr vor Einbau abnehmen | ✓ |
| In der Abnahme-Runde | Saetze erst in der Playwright-Runde, Nachzuege teurer | |

**User's choice:** Vorab-Plan wie 34-01

---

## Form der Dedup-Notiz

| Option | Description | Selected |
|--------|-------------|----------|
| Nur interne Vorlage | Entscheidungsvorlage, v1.6-Entscheid faellt der Owner spaeter | ✓ |
| Plus Issue-Kommentar-Entwurf | Zusaetzlich englischer Entwurf fuer #25 | |

**User's choice:** Nur interne Vorlage

---

## Claude's Discretion

- Leerzustand bei 0 Nachbarn (Wortlaut via Wortlaut-Plan)
- Filter-/Sortier-Zeile in der Aehnlich-Ansicht
- Chunk-zu-Dokument-Aggregation, Score-Schnitt, Ausschluss der Ausgangsdatei
- Routen-/Parameterdesign, access_level der neuen ExApp-Route
- int8-Build-Weg fuer granite, Messskript-Aufbau
- Ablageort und Gliederung der Dedup-Notiz

## Deferred Ideas

- Embedding-Wechsel auf granite (v1.6, nur bei messbarem Gewinn)
- #25-Dedup-Bau (v1.6, nach STR-03-Entscheid)
- Issue-#25-Kommentar-Entwurf (bewusst nicht Teil der Phase)
