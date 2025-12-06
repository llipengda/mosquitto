#!/bin/bash

PID_FILE="/tmp/mosquitto_coverage.pid"
INTERVAL=${1:-60}

cleanup() {
    echo "Caught signal, performing cleanup..."
    if [ -f "$PID_FILE" ]; then
        kill $(cat "$PID_FILE") 2>/dev/null
        rm -f "$PID_FILE"
    fi
    lcov --capture --directory . --rc branch_coverage=1 --output-file coverage.info -j 16 -q
    lcov --add-tracefile coverage.info --add-tracefile merged.info --output-file merged.info --rc branch_coverage=1 -j 16 -q
    get_summary "exit"
    exit 0
}

trap cleanup INT TERM QUIT

rm -rf apps client CMakeFiles lib man plugins src *.pc *.cmake *.txt Makefile *.info
cmake .. -DCMAKE_BUILD_TYPE=Debug \
    -DCMAKE_C_FLAGS="--coverage -O0" \
    -DCMAKE_CXX_FLAGS="--coverage -O0" \
    -DCMAKE_EXE_LINKER_FLAGS="--coverage" \
    -DWITH_TLS=OFF
make mosquitto -j16

timestamp=$(date "+%Y-%m-%d_%H:%M:%S")
mkdir -p csv_data
csv_file="csv_data/coverage_${timestamp}.csv"
[ ! -f "$csv_file" ] && echo "timestamp,lines_hit,lines_total,functions_hit,functions_total,branches_hit,branches_total" > "$csv_file"

kill $(cat "$PID_FILE") 2>/dev/null || true
rm -f "$PID_FILE"

src/mosquitto -c ./mosquitto.conf > /dev/null 2>&1 &
sleep 5

kill -USR1 $(cat "$PID_FILE")
lcov --capture --directory . --rc branch_coverage=1 --output-file merged.info -j 16 -q

get_summary() {
    local timestamp=$(date "+%Y-%m-%d_%H:%M:%S")
    if [ -n "$1" ]; then
        timestamp="$1"
    fi
    local summary=$(lcov --summary merged.info --rc branch_coverage=1)
    echo "$summary"
    local lines_info=$(echo "$summary" | grep -E "^  lines" | sed -E 's/.*lines\.*: *[0-9.]+% *\(([0-9]+) *of *([0-9]+).*/\1,\2/' || echo "-,-")
    local functions_info=$(echo "$summary" | grep -E "^  functions" | sed -E 's/.*functions\.*: *[0-9.]+% *\(([0-9]+) *of *([0-9]+).*/\1,\2/' || echo "-,-")
    local branches_info=$(echo "$summary" | grep -E "^  branches" | grep -q "of" && \
                          echo "$summary" | grep -E "^  branches" | sed -E 's/.*branches\.*: *[0-9.]+% *\(([0-9]+) *of *([0-9]+).*/\1,\2/' || echo "-,-")
    echo "$timestamp,$lines_info,$functions_info,$branches_info" >> "$csv_file"
}

get_summary

while true; do
    sleep $INTERVAL
    kill -USR1 $(cat "$PID_FILE")
    lcov --capture --directory . --rc branch_coverage=1 --output-file coverage.info -j 16 -q
    lcov --add-tracefile coverage.info --add-tracefile merged.info --output-file merged.info --rc branch_coverage=1 -j 16 -q
    get_summary
done