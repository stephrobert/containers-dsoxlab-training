# A secret belongs to its consumer, not the whole project

`/opt/lab-compose-secret/credentials/token.txt` contains a random pedagogical token.
It is outside the image build context. Image `dsoxlab-compose-secret:app` reads
`/run/secrets/api_token` at startup and writes only its SHA-256 to `/tmp/fingerprint`.
It then stays running. No containers run initially.

## Mission

Write `/opt/lab-compose-secret/compose.yaml`, project `dsoxlab-compose-secrets`.
Run services `app` and `observer`. Use the supplied app image and unchanged command;
observer uses the supplied pinned Alpine reference and `sleep infinity`.
Declare a top-level file-backed secret `api_token` pointing to the token file.
Grant it only to app; it must appear read-only at `/run/secrets/api_token`.
Do not use replacement mounts, entrypoints or environment-variable copies.
Observer must have no mounts and must not see the secret.

Keep the token unchanged. It must not appear in container metadata, rendered
configuration, logs or Git history. The prepared repository ignores `credentials/`;
never add the token even temporarily before deleting it from a later commit.
Checks inspect actual reachable Git blobs without printing the credential.
The startup fingerprint must match the file's actual bytes.
The check briefly rotates the pedagogical token and force-recreates the services,
then restores the original file and deployment.

Standalone Compose file secrets are bind-mounted host files, not an encrypted
Swarm secret store. Host root and Docker administrators can still read them.
Recreation is necessary for this application to consume a rotated token;
Compose does not automatically restart consumers when a file changes.
