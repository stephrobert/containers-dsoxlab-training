# Built here, available elsewhere

On `docker.lab`, `dsoxlab-registry-app:release` prints today's release.
It exists only in the local engine. The registry at `127.0.0.1:15000` is empty.

The workshop is `/opt/lab-registry-push/appli`. The image and product are already
built: your task is to distribute them, not replace them.

## Mission

- Tag the image as `127.0.0.1:15000/catalogue/appli:1.0`.
- Publish it to the registry.
- Retrieve it from the registry and check its output with `docker run`.
- A client without access to your engine's cache must recover every layer and
  run the same release without networking.

Do not change the registry or the bench's stored reference. The HTTP registry
is restricted to loopback: no unencrypted external registry access is needed,
and no daemon configuration change is expected.

A local `docker run` does not prove a push: the engine may already have the
image. Checks read the remote manifest, download an archive using Skopeo
without consulting Docker's cache, then load and run that archive. They never
delete your release to simulate a fresh client.
