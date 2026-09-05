#!/bin/sh
# Der Waechter des Semantiklaufs. Er tut drei Dinge, die niemand nachts von Hand
# tun kann, und er tut sie in dieser Reihenfolge, weil sie voneinander abhaengen.
#
#   1. Er erkennt den Uebergang von der ersten auf die zweite Spur und faehrt
#      GENAU DANN die Suchlastprobe. Waehrend des Nachlaufs, nicht davor und
#      nicht danach: das ist die Frage, die der Plan stellt.
#   2. Er erkennt das Ende BEIDER Spuren. Ende heisst hier: der Arbeitsvorrat ist
#      leer UND die Zahl embedded steht drei Aufnahmen lang still. Der Vorrat
#      allein reicht nicht, weil die zweite Spur mit einem leeren Vorrat noch
#      Stunden laeuft; embedded allein reicht auch nicht, weil die Zahl zwischen
#      zwei Anspruechen stillsteht, ohne dass die Spur fertig waere.
#   3. Er erhebt den OOM-Beweis NACH dem Lauf und VOR jedem Eingriff, und misst
#      danach den Vektorbestand. Ein Beweis eine Stunde spaeter ist noch gueltig,
#      einer nach dem ersten Neustart ist keiner mehr.
#
# Gefragt wird nicht selbst: der Waechter liest die letzte Zeile der Aufnahmen
# des Statusbeobachters. Der hat die Sitzung, und zwei Wege zur Anmeldung waeren
# zwei Wege, die kaputtgehen koennen.
set -eu

OUT=/home/ubuntu/work/semantiklauf
AUFNAHMEN="$OUT/statusseite.jsonl"
DECKEL=340
RUNDE=0
LEER=0
GESEHEN=0
SUCHLAST_GEFAHREN=0
LETZTES_EMBEDDED=-1
EMBEDDED_STILL=0

while [ "$RUNDE" -lt "$DECKEL" ]; do
    RUNDE=$((RUNDE + 1))
    set -- $(tail -1 "$AUFNAHMEN" 2>/dev/null | python3 /home/ubuntu/work/42c-lesen.py)
    vorrat="$1"
    indexed="$2"
    embedded="$3"

    case "$vorrat" in
    '0' | unklar) ;;
    *) GESEHEN=1 ;;
    esac

    # Der Uebergang: die zweite Spur hat angefangen. Ab dem ersten Vektor ist die
    # Frage des Plans beantwortbar, und sie ist es nur solange die Spur laeuft.
    if [ "$SUCHLAST_GEFAHREN" -eq 0 ] && [ "$embedded" != unklar ] && [ "$embedded" -gt 200 ]; then
        date -u +'suchlast-start %Y-%m-%dT%H:%M:%SZ'
        python3 /home/ubuntu/work/45-suchlast.py "$OUT/46-suchlast-nachlauf.json" 3 \
            > "$OUT/46-suchlast-nachlauf.log" 2>&1 || true
        date -u +'suchlast-ende %Y-%m-%dT%H:%M:%SZ'
        SUCHLAST_GEFAHREN=1
    fi

    # Steht die zweite Spur still?
    if [ "$embedded" != unklar ] && [ "$embedded" = "$LETZTES_EMBEDDED" ]; then
        EMBEDDED_STILL=$((EMBEDDED_STILL + 1))
    else
        EMBEDDED_STILL=0
    fi
    if [ "$embedded" != unklar ]; then
        LETZTES_EMBEDDED="$embedded"
    fi

    if [ "$vorrat" = '0' ] && [ "$GESEHEN" -eq 1 ] && [ "$EMBEDDED_STILL" -ge 3 ] && [ "$SUCHLAST_GEFAHREN" -eq 1 ]; then
        LEER=$((LEER + 1))
    else
        LEER=0
    fi

    date -u +"waechter runde=$RUNDE vorrat=$vorrat indexed=$indexed embedded=$embedded gesehen=$GESEHEN still=$EMBEDDED_STILL leer=$LEER %Y-%m-%dT%H:%M:%SZ"
    if [ "$LEER" -ge 3 ]; then
        break
    fi
    sleep 300
done

date -u +'lauf-ende-erkannt %Y-%m-%dT%H:%M:%SZ' | tee "$OUT/00-ende.txt"
sudo docker exec --user www-data nextcloud-aio-nextcloud php occ findling:index 2>&1 | tee -a "$OUT/00-ende.txt"

echo "=== Suchlast NACH dem Lauf, mit vollem Vektorbestand ===" | tee -a "$OUT/00-ende.txt"
python3 /home/ubuntu/work/45-suchlast.py "$OUT/47-suchlast-danach.json" 3 2>&1 | tee -a "$OUT/00-ende.txt"

echo "=== Beobachter beenden, damit die Abschlusszeile geschrieben wird ===" | tee -a "$OUT/00-ende.txt"
touch /tmp/sampler-stop
sleep 3
sudo pkill -TERM -f 'rss_sampler.sh nc_app_findling_backend' || true
pkill -TERM -f 'statusbeobachter2' || true
sleep 5
sudo chown ubuntu:ubuntu "$OUT"/* || true
grep 'summary' "$OUT/semantiklauf.csv" | tee -a "$OUT/00-ende.txt"
wc -l "$OUT/semantiklauf.csv" "$AUFNAHMEN" | tee -a "$OUT/00-ende.txt"

echo "=== OOM-Beweis, vor jedem Eingriff ===" | tee -a "$OUT/00-ende.txt"
CID=$(sudo docker inspect -f '{{.Id}}' nc_app_findling_backend)
SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"
{
    date -u +'oom-beweis %Y-%m-%dT%H:%M:%SZ'
    echo "-- 1. memory.events der cgroup --"
    sudo cat "$SCOPE/memory.events"
    echo "-- 2. memory.events.local --"
    sudo cat "$SCOPE/memory.events.local"
    echo "-- 3. memory.max, memory.peak, memory.current --"
    sudo cat "$SCOPE/memory.max" "$SCOPE/memory.peak" "$SCOPE/memory.current"
    echo "-- 4. OOMKilled und Neustartzahl des Containers --"
    sudo docker inspect nc_app_findling_backend \
        --format 'OOMKilled={{.State.OOMKilled}} RestartCount={{.RestartCount}} Status={{.State.Status}} StartedAt={{.State.StartedAt}}'
} 2>&1 | tee "$OUT/07-oom-beweis.txt"

echo "=== Der Vektorbestand: Byte je Dokument, gemessen ===" | tee -a "$OUT/00-ende.txt"
{
    date -u +'vektorbestand %Y-%m-%dT%H:%M:%SZ'
    echo "-- die Dateien des Datenspeichers, mit ihren Groessen --"
    sudo docker exec nc_app_findling_backend sh -c 'ls -la /nc_app_findling_backend_data; du -sb /nc_app_findling_backend_data/* 2>/dev/null'
    echo "-- Chunks, Dokumente und Byte je Dokument --"
    sudo docker cp /home/ubuntu/work/42d-bestand.py nc_app_findling_backend:/tmp/42d-bestand.py
    sudo docker exec nc_app_findling_backend /app/.venv/bin/python /tmp/42d-bestand.py
} 2>&1 | tee "$OUT/48-vektorbestand.txt"

date -u +'waechter-ende %Y-%m-%dT%H:%M:%SZ' | tee -a "$OUT/00-ende.txt"
echo "42B-WAECHTER-FERTIG" | tee -a "$OUT/00-ende.txt"
