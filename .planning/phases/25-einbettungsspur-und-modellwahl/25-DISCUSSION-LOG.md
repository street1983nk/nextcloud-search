# Phase 25: Einbettungsspur und Modellwahl - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md, this log preserves the alternatives considered.

**Date:** 2026-09-28
**Phase:** 25-einbettungsspur-und-modellwahl
**Areas discussed:** fp32-Wahl und Kopplung, fp32-Downloadquelle, Suche waehrend Reindex, Rueckweg fp32 zu int8

---

## fp32-Wahl und Kopplung

| Option | Description | Selected |
|--------|-------------|----------|
| Standard und Leistung | In Sparsam nie; RAM-Schranke rechnet den fp32-Mehrbedarf ein | ✓ |
| Nur Leistung | fp32 erst ab 12 GB/6 Kernen, woertlichste Lesart von MOD-02 | |
| Unabhaengig vom Profil | Eigener Schalter auch in Sparsam | |

| Option | Description | Selected |
|--------|-------------|----------|
| Eigener occ-Schluessel | model_precision getrennt vom Profil, gleiche OCS-Lesestrecke | ✓ |
| Als vierte Profilstufe | z. B. performance_fp32, ein Wert statt zwei | |

| Option | Description | Selected |
|--------|-------------|----------|
| fp32 bleibt, gemeldet | Praezision wechselt nie automatisch, nur die Slots folgen Sparsam | ✓ |
| Automatisch auf int8 | Strenges Sparsam, aber Voll-Reindex bei jeder Schrumpfung (Flattern) | |

| Option | Description | Selected |
|--------|-------------|----------|
| int8 bleibt aktiv, Verdikt | Kein Reindex, neuer Versuch nur auf Admin-Aktion | ✓ |
| int8 bleibt, Wiederholen | Taeglicher Neuversuch ohne Admin-Klick | |

**User's choice:** jeweils die empfohlene Option.

---

## fp32-Downloadquelle

| Option | Description | Selected |
|--------|-------------|----------|
| Eigenes GitHub-Release | Asset im Release, sha256 fest im Code | ✓ |
| HuggingFace direkt | Revision-Hash plus sha256, kein eigenes Hosting | |
| GitHub, HF als Rueckfall | Beide Quellen, derselbe Digest | |

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, Datei ablegen | Selbst abgelegte Datei mit passendem Digest wird genutzt | ✓ |
| Nein, nur Download | Abgeschottete Boxen bleiben bei int8 | |

**User's choice:** jeweils die empfohlene Option.

---

## Suche waehrend Reindex

| Option | Description | Selected |
|--------|-------------|----------|
| Teilweise, nur neue Vektoren | Lexikalisch alles, Semantik waechst mit dem Fortschritt | ✓ |
| Semantik aus bis fertig | Nur lexikalisch bis 100 % | |
| Alte Vektoren bis fertig | Blau/Gruen, doppelter RAM und Plattenplatz | |

| Option | Description | Selected |
|--------|-------------|----------|
| Praezision plus Fortschritt | Prozent und Zaehlung auf der Adminseite | ✓ |
| Nur Zustandswort | "Neueinbettung laeuft" | |

**User's choice:** jeweils die empfohlene Option.

---

## Rueckweg fp32 zu int8

| Option | Description | Selected |
|--------|-------------|----------|
| Loeschen | Platte frei, erneuter Wechsel laedt neu | ✓ |
| Behalten | Schneller Hin- und Rueckwechsel, Datei bleibt belegt | |
| Nur selbst geladene loeschen | Selbst abgelegte Datei bleibt liegen | |

**User's choice:** Loeschen (gilt auch fuer eine selbst abgelegte Datei).

---

## Claude's Discretion

- Abbruchsemantik der zwei Nebenlaeufer, state.db-Zugriffe, Art-Filter am PHP-Anspruch
- RAM-Bedingung und Warteverhalten der Einbettungsspur
- Mitnahme idle-Guard EmbeddingModel.release()
- Asset-Name, Upload-Weg, Ablagepfad, Wechsel waehrend laufendem Reindex, Verdikt-Texte

## Deferred Ideas

- Blau/Gruen-Reindex und automatisches Wiederholen des Downloads: verworfen
- Issue-#18-Todo geprueft, nicht aufgenommen (passt nicht zu Phase 25)
