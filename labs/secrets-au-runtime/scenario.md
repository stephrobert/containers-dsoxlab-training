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
