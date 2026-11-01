# Every source change reinstalls the dependencies

On `docker.lab`, `/opt/lab-buildkit-cache` builds a product from
`source/version.txt` and a dependency in the local `depot/` repository.
`fabriquer.sh` installs the dependency into `/cache`, then writes a product and
a receipt into `/produit`. The local repository keeps this exercise independent
of internet speed; it represents a package-manager dependency.

The Dockerfile works, but each source change reinstalls the same dependency.
The dependency cache also ends up in the runtime image.

## Mission

Fix the Dockerfile without modifying the build tool so that:

- a new builder succeeds with an empty cache;
- two different source versions each produce their own product;
- the second build reuses the dependency even though the build step runs again;
- `/cache` contains no dependency in the runtime image.

The receipt includes `cache=miss` or `cache=hit`, the source, a fabrication
fingerprint and the dependency SHA-256. `/produit/dependency.txt` must match
the repository dependency.

You can create a dedicated builder named `dsoxlab-cache-work`:

```bash
docker buildx create --name dsoxlab-cache-work --driver docker-container \
  --driver-opt image=moby/buildkit@sha256:cec9f139f45e93c5c69c60f8b07cfad9f43f4ef6b6a6cd917527fea5ff2e3dea
docker buildx build --builder dsoxlab-cache-work --load \
  -t dsoxlab-cache:finale /opt/lab-buildkit-cache
docker run --rm dsoxlab-cache:finale
```

Change the source to invalidate the step: repeating an identical build only
proves layer caching. Do not force `--no-cache`: on this bench's BuildKit
version, that option also empties the cache mount.

Checks use an isolated builder, change the source and restore it afterwards.
They judge rebuilt products, not elapsed time or typed commands. `clean` removes
only this lab's named objects.
