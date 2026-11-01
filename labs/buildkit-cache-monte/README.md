# A cache that survives the step, not inside the image

This lab distinguishes layer caching from cache mounts: the source changes,
the step runs again, and its dependency remains reusable outside the image.

Measured on `docker.lab` on 2026-11-01 with the scenario's pinned BuildKit:
changing a build argument gives `miss` then `hit`, with a new product;
`/cache/dependency` is absent from the image. Two builds with `--no-cache`
instead give `miss` then `miss`. Checks therefore change the source, not that
option.

The dependency repository is local and installation deliberately small:
no timing threshold confuses cache correctness with internet speed. An empty
cache must work; a warm cache must avoid reinstallation.

Three checks cover cold/warm products, reuse after a source change and absence
of the cache from the image. The first also requires restored reuse, so it
awards no points for the initial state. Each check session creates and removes
its own builder and cache volume without purging other labs' caches.
