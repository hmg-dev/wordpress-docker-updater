# syntax = docker/dockerfile:1.0-experimental
FROM ubuntu:18.04

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG MIRROR

RUN if [ -n "$MIRROR" ] ; then sed -i /'^deb '/s,'deb [^:]*:[^ ]* ',"deb ${MIRROR} ", /etc/apt/sources.list ; fi && \
    export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y apt-transport-https ca-certificates apt-utils unzip gnupg2 tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

CMD [ "sh", "/usr/local/bin/entrypoint.sh" ]
