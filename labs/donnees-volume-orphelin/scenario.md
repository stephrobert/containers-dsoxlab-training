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
