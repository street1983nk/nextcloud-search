---
phase: 16-haertung-und-store-einreichung-v1-2-0
captured: 2026-09-21
mode: decisions-only
source: Owner-Rueckfragen in der Session vom 21.09.2026 (nach Phase-15-Abnahme)
---

# Phase 16: Owner-Entscheide vor der Planung

## Leitsatz der Abnahme (Wortlaut)

"ziel ist das wir den usern das best moegliche liefern" (21.09.2026)

## Gebundene Entscheide (LOCKED)

### E1: Messzahl der Store-Texte und READMEs

**731,9 MB nach Nutzung** ersetzt die alte 103,2 MB an allen neun Stellen.
Messgroesse: residenter Stand des Containers, nachdem einmal eingebettet und
wieder entladen wurde (Rohdatei 94b, 21.09.2026, m7g.large/aarch64,
ausgeliefertes v1.2-Abbild). Begruendung: die ehrlichste Zahl fuer
4-GB-Selfhoster, verschweigt den Bodensatz nicht. Hoechstens diese eine Zahl
im Text (Owner-Regel kurze Produkttexte). Das neue Gate (Erfolgskriterium 4)
haelt diese Zahl an drei Stellen: README.en.md und beide info.xml.

### E2: Die 58 Altfunde (Audit M-02)

**Bereinigen + Restliste.** Neue Commits ersetzen die Funde in den aktuellen
Dateien durch Platzhalter. Was begruendet stehen bleibt (z.B. bewusst
oeffentliche Hostnamen wie loadtest.infranode.dev, snap-Kennung), kommt auf
die benannte Ausnahmeliste des neuen Geheimnis-Gates. Historie wird NICHT
umgeschrieben, alte SHAs bleiben gueltig.

### E3: Weg fuer A4 (Sprachfaelle ohne Fremdbestand)

**CI zuerst, Box als Fallback.** Erst der kostenlose arm64-CI-Ast mit dem
98c-Korpus (39 Dateien) auf frischer Instanz. Nur falls der CI-Weg die
Messung nachweislich nicht traegt, die kleine Box-Anfahrt; deren Deckel
**7 h / 0,90 USD ist hiermit freigegeben**, Start nur bei belegtem
CI-Fehlschlag. 98c ist eingefroren (DRIVEN_V12_FASSUNGEN): Aenderungen nur
als Nachfolgefassung mit neuer Nummer.

### E4: BL-F02 Baustein 1 (OCR-Pakete spa/ita/nld/por)

**Nur ohne Terminrisiko.** Eigener Plan in der letzten Welle vor der
Einreichung; geraet die Abgabe in Verzug, faellt er ersatzlos aufs
Folgerelease. Kein Requirement.

## Frueher gefallene Entscheide, die diese Phase binden

- Auflagen A1-A4 der Phase-15-Abnahme (Wortlaut in 15-16-SUMMARY.md).
- Store-Token-Rotation VOR der Einreichung (Token stand im Box-Snapshot;
  Rotation ist ein Owner-Klick auf apps.nextcloud.com/account/token, die
  Plaene muessen sie als Vorbedingung der Submission fuehren).
- Store-Texte und README dem Owner VOR der Einreichung zeigen
  (Owner-Regel vom 06./07.09.2026).
- tantivy bleibt exakt 0.26.0 (Dependabot-ignore seit 21.09.2026);
  onnxruntime-Pin 1.30.0 darf sich nur mit eigenem Beweggrund bewegen.
- Dependabot-PR #11 (zwei Action-Bumps docker.yml) liegt beim Owner.

## Claude's Discretion

Alles Uebrige (Wellenschnitt, Reihenfolge, Gate-Bauform, Flake-Fixe) liegt
beim Planner im Rahmen von RESEARCH.md und den Projektregeln.
