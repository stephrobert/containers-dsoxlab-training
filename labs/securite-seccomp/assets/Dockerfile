FROM alpine@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f
LABEL dsoxlab.lab="securite-seccomp"
RUN apk add --no-cache gcc musl-dev
COPY probe.c /src/probe.c
RUN cc -Os -o /usr/local/bin/syscall-probe /src/probe.c \
    && apk del gcc musl-dev && rm -rf /src
CMD ["sh", "-c", "while :; do sleep 3600; done"]
