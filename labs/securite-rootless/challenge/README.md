# A daemon without root, only waiting to be started

## The situation

On `docker.lab`, a second Docker engine is prepared for the dedicated
`dsoxlab-rootless` account, next to the system's engine. The account, its
subordinate ids, its work directory, its `linger` and its service file are in
place. The last step is missing.

## Mission

**Start the `dsoxlab-rootless.service` user service of the `dsoxlab-rootless`
account.** It is not a system service: the account that carries it has no open
session, and its UID is in `/opt/dsoxlab-securite-rootless/state.json`.

The system's engine must stay intact.

## What is graded

Eight checks. They build themselves the network, the volume and the HTTP server
they need, then remove them: you have nothing else to create.

1. The dedicated service is active.
2. Its daemon reports rootless mode.
3. Its process belongs to the dedicated account, and its UID is not 0.
4. Its image store is distinct from the system engine's.
5. It creates its own network and its own named volume.
6. A new piece of data survives two recreations of the container.
7. Its publication stays on the loopback, on an unprivileged port.
8. A container of its network reaches the service, a container without network is
   refused.
