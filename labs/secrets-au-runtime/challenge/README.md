# Brief

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
