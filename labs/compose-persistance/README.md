# Prove persistence with new writes

The supplied image initializes only missing data. Three checks measure the
named-volume mount, force-recreation and down/up without volume removal.
Random trial writes distinguish real persistence from repeatedly copying the seed.
Each trial also measures the non-root UID and permissions before and after
replacement. A named volume preserves ownership; it does not grant access to
a new UID automatically. Prepare ownership once, keep the data directory
private. This protects application-level identities, not users controlling the
Docker socket.

This lab does **not** require a read-only root: that is taught much later in
the path, and a requirement no lesson has introduced yet does not train, it
blocks.
Tests restore the original content; cleanup deletes only this project's resources
and owner-labeled image. No host reboot is required or attested.
