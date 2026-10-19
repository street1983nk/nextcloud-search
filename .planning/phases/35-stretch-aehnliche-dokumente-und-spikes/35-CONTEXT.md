# Phase 35: Stretch: Aehnliche Dokumente und Spikes - Context

**Gathered:** 2026-10-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Drei Lieferstuecke, jedes einzeln streichbar ohne Release-Risiko:

1. **Aehnliche Dokumente (STR-01):** Nutzer ruft auf der Findling-Ergebnisseite
   zu einem Treffer die Vektor-Nachbarn aus dem bestehenden Index ab. Kein
   Index-, Schema- oder Modellwechsel; Dokumente ohne Leserecht erscheinen nie
   (PHP-Recheck).
2. **granite-Messbericht (STR-02):** granite-embedding-97m-multilingual-r2
   gegen e5-small (deutscher Korpus, Trefferqualitaet, CPU-Latenz amd64 und
   arm64, RAM, eigener int8-Build) unter docs/measurements/ mit Empfehlung fuer
   v1.6. Das ausgelieferte Modell bleibt e5-small. Pflichtpunkte aus der
   Owner-Frage vom 10.10.: Image-Groessenzuwachs bei zwei Modellen im Image,
   Dauer der Neu-Einbettung auf der 4-GB-ARM-Box, Bewertung des Vorschlags
   "Neuinstallation Standard granite, Bestand optional per Opt-in mit Rueckweg".
3. **#25-Dedup-Designnotiz (STR-03):** Entscheidungsvorlage je Mount-Config
   (fileid-Mapping vs. per-User-Crawl, ACL-Folgen) fuer den v1.6-Entscheid.

</domain>

<decisions>
## Implementation Decisions

### Bedienung Aehnliche Dokumente (Owner-Entscheide 19.10.2026)
- **D-35-01:** Einstieg pro Treffer als sichtbarer Textlink "Aehnliche
  Dokumente" unter Pfad/Auszug. Eigenes Element im `<li>` NEBEN dem
  Zeilen-Link (die Trefferzeile ist heute EIN `<a>`); zweiter Tab-Stopp pro
  Treffer, kein verschachteltes Interaktivelement im Anker.
- **D-35-02:** Klick fuehrt auf eine neue Serveransicht: GET-Link auf dieselbe
  Ergebnisseite (Parameter in der Art `?similar=fileId`), serverseitig
  gerendert wie Filter und Sortierung heute. Kein neues JS-Muster, der
  Browser-Zurueck-Knopf traegt.
- **D-35-03:** Maximal 10 Nachbarn nach PHP-Rechte-Recheck, dargestellt als
  normale Hit-Liste (Icon, Titel, Pfad) ohne Suchbegriff-Markierung.
- **D-35-04:** Kopf der Aehnlich-Ansicht nennt die Ausgangsdatei ("Aehnlich
  zu: ...") und traegt einen Rueckweg-Link zur vorherigen Trefferliste.

### granite-Messaufbau (Owner-Entscheide 19.10.2026)
- **D-35-05:** arm64-Messungen auf einer gemieteten AWS-m7g-Instanz, gleiche
  Basis wie docs/measurements/2026-09-vergleichsmessung-m7g. Der Owner gibt
  die Instanz frei (Miet-Start ist ein Checkpoint, nicht autonom).
- **D-35-06:** Qualitaetsvergleich auf dem bestehenden Messkorpus der
  bisherigen docs/measurements-Laeufe (Vergleichbarkeit mit frueheren Zahlen).
- **D-35-07:** Trefferqualitaet ueber feste Frage-Treffer-Paare, VOR der
  Messung definiert (Regel vor der Messung), automatisch auswertbar.

### Wortlaut-Prozess (Owner-Entscheid 19.10.2026)
- **D-35-08:** Eigener Wortlaut-Plan am Phasenanfang wie 34-01: die neuen
  UI-Saetze (Link "Aehnliche Dokumente", Kopf "Aehnlich zu ...", Rueckweg,
  Leerzustand) werden dem Owner de/en/fr zur Abnahme vorgelegt, BEVOR sie in
  Code und die 16 Kataloge reisen.

### Form der Dedup-Notiz (Owner-Entscheid 19.10.2026)
- **D-35-09:** Nur interne Entscheidungsvorlage (docs/ bzw. .planning/), kein
  Kommentar-Entwurf fuer Issue #25. Den v1.6-Entscheid faellt der Owner
  spaeter.

### Claude's Discretion
- Verhalten bei 0 Nachbarn (Leerzustand-Wortlaut geht durch den Wortlaut-Plan).
- Ob Filter/Sortier-Zeile in der Aehnlich-Ansicht erscheint.
- Aggregation Chunk-zu-Dokument bei den Vektor-Nachbarn (ein Dokument hat
  viele Chunks), Score-Schnitt, Ausschluss der Ausgangsdatei.
- Routen-/Parameterdesign und access_level der neuen ExApp-Route.
- Methodendetails des int8-Builds fuer granite und Messskript-Aufbau.
- Ablageort und Gliederung der Dedup-Notiz.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Ergebnisseite und Companion-App
- `php/templates/search.php` , Aufbau der Ergebnisseite: Trefferzeile ist EIN
  Link, GET-Link-Muster fuer Chips/Sortierung, Kommentar-Konventionen.
- `php/js/search.js` , das wenige JS der Seite (returned-Markierung).

### Messungen (Muster und Vergleichsbasis)
- `docs/measurements/2026-09-vergleichsmessung-m7g/` , m7g-Messaufbau und
  Vergleichszahlen, an die STR-02 anschliesst.
- `backend/tests/test_measurement_scripts.py` , Baumhash-Ratsche und
  Journal-Pflicht bei PHP-Aenderungen; Messrezepte-Vertrag.

### Anforderungen und Abgrenzung
- `.planning/REQUIREMENTS.md` , STR-01..03 mit den Pflichtpunkten vom 10.10.
- `.planning/ROADMAP.md` , Phase-35-Abschnitt (Stretch, einzeln streichbar).
- Issue #25 (GitHub street1983nk/nextcloud-search) , Dedup-Sachstand fuer
  STR-03.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Hit-Listen-Markup (`findling-hit`-Block in search.php) traegt die
  Aehnlich-Ansicht unveraendert; nur der Kopf und der neue Link je Treffer
  kommen hinzu.
- Vektorspeicher sqlite-vec mit int8-Vektoren existiert; Nachbarsuche ist eine
  Abfrage auf Bestandsdaten, kein neues Schema (STR-01-Vorgabe).
- PHP-Rechte-Recheck-Muster aus der Suche (getUserFolder/getFirstNodeById)
  gilt unveraendert fuer Nachbarn.

### Established Patterns
- Serverseitige GET-Links fuer alle Zustandswechsel der Ergebnisseite (Chips,
  Sortierung, Reset) , D-35-02 folgt dem.
- Wortlaut-Plan mit Owner-Abnahme vor Katalog-Einbau (34-01, 33-01);
  16 Kataloge + 5 Sprachtabellen je neuem Satz; de/fr zeichengleich aus dem
  Wortlaut-Dokument.
- Gemeinsame Playwright-Abnahme fuer UI am Phasenende (Owner-Regel); KEIN
  UI-SPEC (Owner-Entscheid 19.10., wie O10 in Phase 34).
- PHP-Baumhash-Ratsche: jede php/-Aenderung braucht den Journalabsatz.
- Messungen: Regel vor der Messung, Ablage docs/measurements/YYYY-MM-thema/.

### Integration Points
- Neue ExApp-Route fuer Nachbarabfrage (Python-Backend, Vektorscan) plus
  Proxy-Weg ueber die PHP-Companion wie bei /search und /snippets.
- search.php/SearchController: neuer Ansichtszweig fuer `similar`-Parameter.

</code_context>

<specifics>
## Specific Ideas

- Der Einstieg soll sich anfuehlen wie die bestehenden Seiten-Links (Chips,
  Sortierung): schlicht, serverseitig, kein Overlay.
- Messbericht endet mit einer klaren v1.6-Empfehlung inklusive Bewertung des
  Opt-in-Vorschlags (Neuinstallation granite, Bestand optional mit Rueckweg).

</specifics>

<deferred>
## Deferred Ideas

- Embedding-Wechsel auf granite r2: nur wenn STR-02 messbar gewinnt, Bau in
  v1.6 (steht so in REQUIREMENTS.md "Out of Scope").
- #25-Dedup-Bau: erst nach STR-03-Entscheid des Owners (v1.6).
- Kommentar-Entwurf fuer Issue #25: bewusst NICHT Teil dieser Phase (D-35-09).

</deferred>

---

*Phase: 35-stretch-aehnliche-dokumente-und-spikes*
*Context gathered: 2026-10-19*
