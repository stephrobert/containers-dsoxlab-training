# Measure the delivery, not the local image cache

The product is generated and published at setup; its local tag is removed.
No delivery or checksum exists initially.

Two checks validate a portable checksum and a complete Docker archive, then
recover and run the exact product with the source registry stopped.
Skopeo reads all archive blobs into a fresh directory before Docker is involved,
so pre-existing Docker layers cannot hide missing archive layers.
The offline trial uses only that directory, never a network reference.

The source registry is restored in a finally block; the imported trial tag and
temporary directories are removed. Cleanup targets only named lab objects and
owner-labeled images. The original Alpine and Registry images are retained.
Loopback HTTP is an intentional packaging fixture, not a TLS recommendation.
