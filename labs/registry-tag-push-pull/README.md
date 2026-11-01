# The local cache does not prove publication

This lab distributes an already-built image into an empty local registry.
A setup-generated product distinguishes the release from a fixed response.

The first check reads the registry manifest and compares its identity with the
reference. The second downloads every layer using Skopeo into a fresh archive,
loads that archive and runs the image without networking.

Measured on `docker.lab` on 2026-11-01: an image pushed to the pinned Distribution
registry can be fetched with Skopeo, reloaded with Docker and run without registry
access. That transfer does not consult the producer's Docker cache even though
both clients run on the same VM.

The registry listens only on loopback. Checks remove their archive, container
and tag; cleanup removes the registry and storage without pruning other labs'
objects.
