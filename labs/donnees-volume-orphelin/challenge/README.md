# An orphan is not necessarily disposable

## The situation

On `docker.lab`, two volumes are attached to no container.
`dsoxlab-donnees-volume-orphelin-data` contains a receipt to recover.
`dsoxlab-donnees-volume-orphelin-stale` is empty and no longer useful. The `worker`
of project `dsoxlab-donnees-volume-orphelin` runs without its data. The project is
in `/opt/dsoxlab-donnees-volume-orphelin`.

## Mission

1. `worker` mounts the original `dsoxlab-donnees-volume-orphelin-data` volume
   read-only, at `/data`. This volume keeps its two labels, the lab's and the
   Compose project's.
2. `/data/receipt.txt` is identical to the supplied `expected.txt` file.
3. `dsoxlab-donnees-volume-orphelin-stale`, and it alone, is removed. Check its two
   labels first.

Keep the project and the `dsoxlab.lab=donnees-volume-orphelin` label. Do not recreate
the volume to keep, and use neither `volume prune` nor `system prune`.
