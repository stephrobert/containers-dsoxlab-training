FROM alpine@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
LABEL dsoxlab.lab="securite-seccomp"
RUN apk add --no-cache gcc musl-dev
COPY probe.c /src/probe.c
RUN cc -Os -o /usr/local/bin/syscall-probe /src/probe.c \
    && apk del gcc musl-dev && rm -rf /src
CMD ["sh", "-c", "while :; do sleep 3600; done"]
