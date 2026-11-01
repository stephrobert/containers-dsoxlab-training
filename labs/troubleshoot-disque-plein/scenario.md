# ENOSPC inside a bounded filesystem sandbox

The worker's `/sandbox` is a 16 MiB tmpfs, not a host partition. A finite filler
has consumed its available capacity. `/sandbox/keep.txt` is useful data;
`/sandbox/fill.bin` is disposable.

In `/opt/dsoxlab-troubleshoot-disque-plein`, recover writable space in the
existing `worker`, project `dsoxlab-troubleshoot-disque-plein`, without losing
the receipt or increasing the sandbox limit.

Do not recreate the container to erase its data, resize the sandbox, fill any
host path or run global prune. The checker writes at most 1 MiB inside the
verified sandbox and removes its probe afterward.
