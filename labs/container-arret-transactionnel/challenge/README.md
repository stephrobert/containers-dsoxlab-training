# Contract 05: transactional shutdown

[Français](README.fr.md)

1. Use the supplied Python service and pinned image in project
   `dsoxlab-container-arret-transactionnel-stack`. Work directory:
   `/opt/dsoxlab-container-arret-transactionnel`. Repair the launch configuration,
   not the domain implementation; keep `/app/entry.sh` executable through `/bin/sh`.
2. Keep `/data` on a durable Docker volume. Admit a fresh `/write?id=ID` HTTP
   request and wait until `/inflight` reports its ID with `begun: true`.
   `/record?id=ID` must still return 404 while the write is uncommitted.
3. Stop gracefully within eight seconds. Observe the application's received
   SIGTERM, completed request and committed transaction. The caller receives
   HTTP 200 with `value: accepted`; the process exits zero after draining.
4. Recreate the container with the same volume and read that record through
   `/record`. Repeat with another held request and SIGKILL: its caller fails,
   the new record stays absent, earlier committed data remains readable and a
   subsequent write succeeds. No global database corruption is an acceptable negative.
5. Keep lab labels and avoid privileges, host namespaces and Docker API mounts.
   Run UID/GID 10001, read-only rootfs and a private `/data` volume owned by
   10001:10001, mode 0700. Another application UID must not read transactions.
   Adjust ownership of the existing SQLite files without discarding their data.
   Tests use private labelled trial containers and a private volume, removed
   in `finally`; they do not consume the learner's ledger data.
6. Observe `/configuration` over HTTP for two configurations of this same
   service image. `SERVICE_MODE` defaults to `standard`; changing only that
   variable must change the reported `service_mode`, without losing the ledger.

The single functional verdict deliberately covers the whole contract:
zero before repair, full after repair. The versioned ledger records the
actually measured passages for this revision.
No command history is graded. Explain cause and limits in the separate
[human review](review.md), not by adding a token file.
