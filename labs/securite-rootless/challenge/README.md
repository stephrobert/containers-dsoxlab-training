# Functional contract: securite-rootless

## What you deliver

One step only: **the dedicated account's `dsoxlab-rootless.service` user
service is active**. Everything else is already laid down by setup.

## What the eight checks prove

They inspect the real daemon on `docker.lab`, and **build the scenery
themselves**. You have no network, no volume and no HTTP server to create.

1. the dedicated service is active;
2. its daemon reports rootless mode;
3. the service's real process belongs to the unprivileged account, and its UID
   is not 0;
4. its image store is separate from the rootful engine's, proven before any
   load;
5. it creates its own network and its own named volume;
6. a fresh value survives two container recreations;
7. its publication stays on loopback, on a nonprivileged port;
8. a peer of its network reaches the service, and a networkless peer is
   refused.

Trial objects carry unique bounded names and are removed, including after a
partial allocation. The initial state scores nothing.
