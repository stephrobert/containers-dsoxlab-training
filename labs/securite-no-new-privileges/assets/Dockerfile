FROM alpine@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
LABEL dsoxlab.lab="securite-no-new-privileges"
RUN apk add --no-cache gcc musl-dev
COPY probe.c /src/probe.c
RUN cc -Os -o /usr/local/bin/identity /src/probe.c \
    && chown 0:0 /usr/local/bin/identity \
    && chmod 4755 /usr/local/bin/identity \
    && apk del gcc musl-dev && rm -rf /src
USER 1000:1000
CMD ["sh", "-c", "while :; do sleep 3600; done"]
