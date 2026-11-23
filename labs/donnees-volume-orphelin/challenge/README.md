# An orphan is not necessarily disposable

Two volumes belong exclusively to this lab. `dsoxlab-donnees-volume-orphelin-data`
contains an original receipt and must be recovered. The empty
`dsoxlab-donnees-volume-orphelin-stale` is expendable. Neither is attached to the
starter worker.

In `/opt/dsoxlab-donnees-volume-orphelin`, reconnect the original data read-only
at `/data` in `worker`, project `dsoxlab-donnees-volume-orphelin`. Retain the
receipt and delete only the stale lab volume.

Inspect both ownership labels before deletion. Never run volume prune, system
prune, or delete any unlabelled or unrelated volume.

## Brief

Work on `docker.lab`, in `/opt/dsoxlab-donnees-volume-orphelin`.

1. Keep `worker` active, project `dsoxlab-donnees-volume-orphelin`,
   label `dsoxlab.lab=donnees-volume-orphelin`.
2. Mount the original `dsoxlab-donnees-volume-orphelin-data` volume read-only
   at `/data`, preserving both of its ownership labels.
3. `/data/receipt.txt` must exactly match the supplied `expected.txt`.
4. Remove only `dsoxlab-donnees-volume-orphelin-stale`, after checking its
   lab and Compose project labels.

Do not recreate the retained volume or use any global prune command.
