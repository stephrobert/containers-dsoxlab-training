# A tag moves; its old digest remains addressable

Setup publishes two random products under the same tag and runs the second.
It records the original manifest digest in a delivery receipt.

Three checks prove the original image is running, its startup reference is
immutable and its manifest remains readable from the registry. Each first
requires restoration of the original image: no score rewards the initial state.

The registry belongs to this lab and listens only on loopback. Cleanup removes
its containers, references and storage without a global prune.

Cycle measured on `docker.lab` on 2026-11-01: 0/3 before, 3/3 after,
0/3 after `clean` and `run`, then the engine is returned intact.
The registry check also verifies that `stable` still points to the replacement.
