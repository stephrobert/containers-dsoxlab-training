# Deliver a token without publishing it

## The situation

On `docker.lab`, the `worker` of project `dsoxlab-secrets-au-runtime` waits for a
token in `/run/secrets/token`. As soon as it can read it, it writes its SHA-256
fingerprint in `/run/result`, without ever displaying the token. The value, drawn
at random, is in `secrets/token`, under `/opt/dsoxlab-secrets-au-runtime`.

## Mission

1. `worker` receives `secrets/token` read-only, at `/run/secrets/token`.
2. `/run/result` carries the token's fingerprint.
3. A write into the mounted file is refused, and the source does not change: a
   regular file, in mode 0600.
4. The token appears neither in `docker inspect`, nor in the logs, nor in the image
   or its history, nor in the Dockerfile, nor in the Compose file.

Keep the project, the `dsoxlab.lab=secrets-au-runtime` label, the supplied command,
the pinned image and the resource limits. Paste the token nowhere and do not
replace it with a real credential.
