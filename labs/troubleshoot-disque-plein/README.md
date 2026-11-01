# Diagnose ENOSPC, not the whole host

ENOSPC can mean exhausted data blocks or exhausted inodes. `df -h` reports
capacity, `df -i` reports inodes, and `du` attributes visible file usage.
Open deleted files can keep storage allocated until their processes close them.

For a neutral disposable project `demo-spool`, identify the mount containing
the failing path before deleting anything. Removing an explicitly expendable
file from that mount differs from pruning an entire Docker engine.
Verify retained data and make a finite write to prove recovery.

This exercise simulates filesystem capacity exhaustion in a container-local
tmpfs hard-capped at 16 MiB, inside a 64 MiB no-swap memory cgroup.
It reproduces ENOSPC safely, not physical disk latency, Docker layer accounting
or host-partition exhaustion. The initial dd has a fixed 16-block budget.
No loopback mount or host daemon changes are needed.

The engine and Compose must already be available, with at least 128 MiB of
available host memory. See [the challenge](challenge/README.md).
