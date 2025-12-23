FROM debian:stable-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash build-essential cmake bash xsltproc docbook-xsl lcov libjson-xs-perl sed && \
    rm -rf /var/lib/apt/lists/*

COPY . /mosquitto

WORKDIR /mosquitto/build

ENV PORT=1883 \
    NAME=coverage \
    INTERVAL=60 \
    OUTPUT_DIR=/coverage_data \
    LOG=/dev/null \
    LOG_ERR=/dev/null

RUN cmake .. \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_C_FLAGS="--coverage -O0" \
  -DCMAKE_CXX_FLAGS="--coverage -O0" \
  -DCMAKE_EXE_LINKER_FLAGS="--coverage" \
  -DWITH_TLS=no \
  -DWITH_DOCS=no && \
  make -j$(nproc) mosquitto && \
  cp ../cov.sh . && \
  chmod -R 777 /mosquitto/build && \
  sed "s/\$PORT/$PORT/g" ../config.template > mosquitto.conf

EXPOSE $PORT

CMD ["./cov.sh"]
