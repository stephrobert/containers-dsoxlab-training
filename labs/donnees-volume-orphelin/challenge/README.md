# Brief

Work on `docker.lab`, in `/opt/dsoxlab-donnees-volume-orphelin`.

1. Keep `worker` active, project `dsoxlab-donnees-volume-orphelin`,
   label `dsoxlab.lab=donnees-volume-orphelin`.
2. Mount the original `dsoxlab-donnees-volume-orphelin-data` volume read-only
   at `/data`, preserving both of its ownership labels.
3. `/data/receipt.txt` must exactly match the supplied `expected.txt`.
4. Remove only `dsoxlab-donnees-volume-orphelin-stale`, after checking its
   lab and Compose project labels.

Do not recreate the retained volume or use any global prune command.
