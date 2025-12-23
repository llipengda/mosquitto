#!/bin/bash

PID=-1

cleanup() {
    echo "Caught signal, performing cleanup..."
    if [ $PID -eq -1 ]; then
        echo "No process to kill."
        exit 1
    fi

    kill $PID
    lcov --capture --directory . --rc branch_coverage=1 --output-file coverage.info -j $(nproc) -q
    lcov --add-tracefile coverage.info --add-tracefile merged.info --output-file merged.info --rc branch_coverage=1 -j $(nproc) -q
    get_summary "exit"

    cp merged.info "${out_dir}/coverage.info"
    genhtml merged.info --rc branch_coverage=1 -o "${out_dir}/html_report" -q
    exit 0
}

trap cleanup INT TERM QUIT

timestamp=$(date "+%Y-%m-%d_%H:%M:%S")
out_dir="${OUTPUT_DIR}/${NAME}_${timestamp}"
mkdir -p "$out_dir"
csv_file="${out_dir}/coverage.csv"
[ ! -f "$csv_file" ] && echo "timestamp,lines_hit,lines_total,functions_hit,functions_total,branches_hit,branches_total" > "$csv_file"

export FUZZ_STATUS_FILE="${out_dir}/fuzz_status.info"
touch "$FUZZ_STATUS_FILE"
chmod 777 "$FUZZ_STATUS_FILE"

src/mosquitto -c mosquitto.conf > $LOG 2>$LOG_ERR &
PID=$!
sleep 5

kill -USR1 $PID
lcov --capture --directory . --rc branch_coverage=1 --output-file merged.info -j $(nproc) -q

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
    kill -USR1 $PID
    lcov --capture --directory . --rc branch_coverage=1 --output-file coverage.info -j $(nproc) -q
    lcov --add-tracefile coverage.info --add-tracefile merged.info --output-file merged.info --rc branch_coverage=1 -j $(nproc) -q
    get_summary
done