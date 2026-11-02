# A secret belongs to its consumer, not the whole project

`/opt/lab-compose-secret/credentials/token.txt` contains a random pedagogical token.
It is outside the image build context. Image `dsoxlab-compose-secret:app` reads
`/run/secrets/api_token` at startup and writes only its SHA-256 to `/tmp/fingerprint`.
It then stays running. No containers run initially.

## Mission

Write `/opt/lab-compose-secret/compose.yaml`, project `dsoxlab-compose-secrets`.
Run services `app` and `observer`. Use the supplied app image and unchanged command;
observer uses the supplied pinned Alpine reference, the one in the `FROM` of
`image/Dockerfile`, and `sleep infinity`.
Declare a top-level file-backed secret `api_token` pointing to the token file.
Grant it only to app; it must appear read-only at `/run/secrets/api_token`.
Do not use replacement mounts, entrypoints or environment-variable copies.
Observer must have no mounts and must not see the secret.

Then **put the next value in service**. `credentials/token-next.txt` carries
the token that must replace the current one: make `app` consume it, without
touching the secret declaration, which stays on `credentials/token.txt`. Mind
this: Compose does not restart a consumer when a mounted file changes, so
rewriting the file is not enough.

Neither value must appear in container metadata, rendered
configuration, logs or Git history. The prepared repository ignores `credentials/`;
never add the token even temporarily before deleting it from a later commit.
Checks inspect actual reachable Git blobs without printing the credential.
The startup fingerprint must match the file's actual bytes.
The fingerprint must match the bytes of the value put in service, and the
container must be younger than the file.

Standalone Compose file secrets are bind-mounted host files, not an encrypted
Swarm secret store. Host root and Docker administrators can still read them.
Recreation is necessary for this application to consume a rotated token;
Compose does not automatically restart consumers when a file changes.
