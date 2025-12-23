/* LCOV_EXCL_START */
#include <time.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <pthread.h>

#include "logging_mosq.h"

static uint64_t pkt_total = 0;
static short pkt_index = 0;
static signed char buffer[5000];

static FILE* fuzz_status_file = NULL;

static pthread_mutex_t fuzz_mutex = PTHREAD_MUTEX_INITIALIZER;

void fuzz_status_init() {
    const char* env_p = getenv("FUZZ_STATUS_FILE");
    if (env_p != NULL) {
        fuzz_status_file = fopen(env_p, "wb");
        if (fuzz_status_file == NULL) {
            log__printf(NULL, MOSQ_LOG_WARNING, "Failed to open fuzz status file: %s\n", env_p);
        }
    } else {
        log__printf(NULL, MOSQ_LOG_WARNING, "FUZZ_STATUS_FILE not set, fuzz status will not be recorded.\n");
    }
}

static void write_to_file_unsafe() {
    if (fuzz_status_file == NULL) {
        return;
    }
    time_t time_now = time(NULL);
    log__printf(NULL, MOSQ_LOG_DEBUG, "Writing fuzz status: time=%ld, total=%lu, count=%d\n", time_now, pkt_total, pkt_index);
    fwrite(&time_now, sizeof(time_t), 1, fuzz_status_file);
    fwrite(&pkt_total, sizeof(uint64_t), 1, fuzz_status_file);
    fwrite(buffer, sizeof(signed char), pkt_index, fuzz_status_file);
    fwrite("\n", sizeof(char), 1, fuzz_status_file);
    fflush(fuzz_status_file);
}

void fuzz_status_cleanup() {
    if (fuzz_status_file == NULL) {
        return;
    }
    pthread_mutex_lock(&fuzz_mutex);
    write_to_file_unsafe();
    fclose(fuzz_status_file);
    fuzz_status_file = NULL;
    pthread_mutex_unlock(&fuzz_mutex);
}

void fuzz_collect_rc(int rc) {
    if (fuzz_status_file == NULL) {
        return;
    }

    pthread_mutex_lock(&fuzz_mutex);

    buffer[pkt_index] = rc;
    pkt_index++;
    pkt_total++;
    
    if (pkt_index >= 5000) {
        write_to_file_unsafe();
        pkt_index = 0;
    }

    pthread_mutex_unlock(&fuzz_mutex);
}
/* LCOV_EXCL_STOP */