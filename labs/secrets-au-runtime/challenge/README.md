# Deliver a secret without publishing it

A random pedagogic token is stored privately in `secrets/token`. The worker
currently cannot access it. Its supplied command only writes a SHA-256 digest
to `/run/result` after the secret becomes readable; it never prints the token.

In `/opt/dsoxlab-secrets-au-runtime`, deliver the token as a read-only runtime
file at `/run/secrets/token` in `worker`, project `dsoxlab-secrets-au-runtime`.
Keep the source private and use the supplied application.

Never paste the token into commands, environment variables, Compose, images or
logs. Do not replace it with a real credential. Cleanup deletes this disposable
token; it does not claim cryptographic erasure.

## Brief

Work on `docker.lab`, in `/opt/dsoxlab-secrets-au-runtime`.

1. Keep `worker` active, project `dsoxlab-secrets-au-runtime`,
   label `dsoxlab.lab=secrets-au-runtime`.
2. Mount the supplied `secrets/token` read-only at `/run/secrets/token`.
   The host source must remain a regular mode-0600 file.
3. Keep the supplied application producing the source's SHA-256 in `/run/result`.
4. No token value may appear in inspect, logs, image metadata/history,
   Dockerfile or Compose configuration.

Use only the random pedagogic token. Never display it or put it in an environment
variable. Preserve the pinned image and resource guards.
