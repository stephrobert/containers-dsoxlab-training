# Recovering orphan volumes

A volume outlives a container. `dangling=true` means no container currently
references it, not that the data has no value. Before deleting anything,
inspect labels, mount references and the application's retention contract.

For a neutral disposable project `demo-ledger`, an `external: true` Compose
volume with an explicit `name` reuses an existing volume instead of creating a
project-prefixed replacement. A service mount can be read-only when recovery
does not require writes. Compare its inspect `Name` with the original volume.

Labels establish ownership, not business value. Data should be compared with
an independent receipt or checksum before recovery is considered complete.
Never treat a global prune as diagnosis.

This lab creates only tiny, uniquely named volumes with both project and lab
labels. Cleanup deletes only those jointly labelled resources.
See [the challenge](challenge/README.md).
