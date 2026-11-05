# Scenario

A second Docker engine is prepared on `docker.lab` for the dedicated
`dsoxlab-rootless` account. The system's rootful daemon must stay intact.

Everything is already in place: the account, its subordinate id range, its work
directory, its lingering and its service unit file. Setup deliberately stops
short of the last step, and that one is yours.

## Mission

**Start the dedicated account's `dsoxlab-rootless.service` user service.** That
is the only step expected of you, and it is the hard step of rootless.

The daemon is not a system service with `User=`: it is a **user** service, and
the account carrying it is a system account with no open session. `systemctl
--user` therefore fails as long as it finds neither its runtime directory nor
its bus. Read the UID from `/opt/dsoxlab-securite-rootless/state.json`, then
run `systemctl --user` as `dsoxlab-rootless` with
`XDG_RUNTIME_DIR=/run/user/<uid>` and
`DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/<uid>/bus`.

## What the checks prove, and what you do not have to build

The checks do not merely ask the daemon about its own state: they **build
themselves** a network, a named volume, an HTTP server and two peers on that
engine, then judge what it does with them. None of those objects is yours to
create, and `check` will not ask you for them.

What they establish from your single step:

- the dedicated service is active, and the real process belongs to the
  unprivileged account, not to root;
- the daemon reports rootless mode;
- its image store is **separate** from the rootful engine's, proven before any
  load: the VM's pinned image is unknown to it;
- it creates its own network and its own named volume;
- a fresh value survives **two** container recreations;
- its publication stays on loopback, on a nonprivileged port;
- a peer of its network reaches the service, and a networkless peer is refused.

## Going further

Be ready to explain UID mapping, the separate image store and the limits of
rootless networking, without confusing root inside the container with root on
the VM. This lab qualifies neither native privileged ports nor high
availability.
