---
plan: 15-09
phase: 15-messphase-eine-box-anfahrt
status: complete
completed: 2026-09-20
requirements-completed: []  # MESS-05 wird an 15-16 abgerechnet
---

# 15-09 SUMMARY: Der Aufbau der Messbox, Bloecke 1 bis 13b

## Was steht

Die Messinstanz laeuft: m7g.large in eu-central-1c, 3.9Gi/2 Kerne/aarch64,
mem=4G in der Kommandozeile, Korpus-Volume aus snap-03f1d1d9ad9262704 ueber die
UUID gemountet (59G, 35G belegt), alle Container des Snapshots gestartet,
Registry antwortet, Systemplatte zurueckgespielt (sha256 identisch).
`loadtest.infranode.dev` loest als A-Record auf die Instanz auf (Weg 1 von 3),
status.php antwortet 200 mit installed:true. Der Abbildwechsel auf den
v1.2-Stand ist vollzogen und belegt: `baumhash-gleich ja` dreifach verankert,
Digest `sha256:80710fbb...4bf706` aus der Abbildstrecke (Lauf 35471225102,
f650c10), Baumhash im LAUFENDEN Container identisch mit dem Arbeitsbaum
(f3f1fb13...), Grenze 2147483648/0 aus der cgroup, Entladeschalter 0,
genau eine Nextcloud, Poller bewaffnet ("indexing is armed").

Rohdaten: `03-aufbau.txt` (alle Bloecke, acht Abweichungen), `40b-baumhash.txt`,
`92b-wechsel.txt`, `92b-info-box.xml`. Geheimnis-Gate auf 03-aufbau leer.

## Owner-Entscheide in dieser Sitzung

1. **A-Record delegiert** ("erledige du das"): gesetzt ueber den vorhandenen
   DNS-Zugang des Betreiber-Werkzeugkastens, TTL 120, nicht proxied.
2. **Werkzeug-Fix waehrend der bezahlten Anfahrt, zweimal, je mit Owner-Wort**
   (Ausnahme von der No-Edit-Regel des Plans):
   - d6fb185: 92b erwartete die harte Grenze in BEIDEN cgroup-Feldern; richtig
     ist memory.swap.max=0 (docker-Summensemantik, belegt durch die
     v1.1-Rohdaten 90-bestand.txt). Haette jede korrekte Maschine mit 39
     abgewiesen.
   - ff8e054: Abschnitt 15 verglich zwei Kennungsarten (Index-Digest gegen
     aufgeloesten Digest, Docker 29/containerd-Store) und las den richtigen
     Inhalt als fremd (36). Jetzt entscheidet der Baumhash im laufenden
     Container, die Kennung bleibt als Notiz.

## Die acht Abweichungen des Erstvollzugs (alle in 03-aufbau.txt, alle 15-15)

1. Schluesselpaar ueberlebt den Abbau (cmd_destroy loescht es nicht).
2. Alte lokale .pub-Datei liess ssh den falschen Schluessel anbieten.
3. ls /mnt/findling zeigt mehr als docker+ncdata (containerd!).
4. Frische Maschine hat KEIN Docker; daemon.json vor der Installation.
5. Abbild-Lager ist der containerd-Image-Store: containerd-Root muss auf
   /mnt/findling/containerd, sonst Container ohne Namen und keine Abbilder.
6. 91-MB-Erwartung in Block 9 misst den lebenden Altstand, nicht die Sicherung.
7. Runbook Block 12: memory.swap.max=0, nicht 2147483648 (siehe Fix d6fb185).
8. Block 9 liefert keinen Arbeitsbaum; Checkout auf der Box per git clone
   (core.fileMode false gegen die 100644-Falle).

Dazu zwei Befunde ohne Fix in der Anfahrt: die Phase-B-Pipeline von 92b
verschluckt occ-Fehler (Lauf 1 endete FERTIG/rc=0 ohne Registrierung), und
der Standwechsel verlangt ein occ upgrade (neue PHP-Haelfte 1.0.3 -> 1.1.0,
"requires upgrade"-Modus sperrt app_api), das das Runbook nicht kennt.
Nebenwirkung des Upgrades, protokolliert: contacts und notes wurden vom Store
mitaktualisiert.

## Verification

1. free 3.9Gi, nproc 2, aarch64: GRUEN (Block 5).
2. cgroup 2147483648 (memory.max) und 0 (memory.swap.max, korrigierte
   Erwartung): GRUEN.
3. baumhash-gleich ja: GRUEN, dreifach verankert plus laufender Container.
4. Genau eine Nextcloud, gezaehlt, zweimal: GRUEN.
5. Geheimnis-Gate 03-aufbau leer; in 92b-wechsel.txt stehen der uvicorn-
   Bind-All und die AIO-Bruecke als Werkzeugausgabe, keine Box-Adresse: GRUEN.

## Naechster Schritt

15-10: Zustandspruefung mit Abbruchbedingung (52.111 indexiert erwartet),
danach Nullstand.
