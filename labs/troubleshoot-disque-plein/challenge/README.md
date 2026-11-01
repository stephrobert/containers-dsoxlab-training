# Brief

Work on `docker.lab`, in `/opt/dsoxlab-troubleshoot-disque-plein`.

1. Keep the existing `worker` active, project `dsoxlab-troubleshoot-disque-plein`,
   label `dsoxlab.lab=troubleshoot-disque-plein`.
2. Preserve `/sandbox` as a 16 MiB tmpfs and the 64 MiB no-swap memory cap.
3. Remove only `/sandbox/fill.bin`; preserve `/sandbox/keep.txt` and its
   `keep-this-receipt` contents.
4. A real 1 MiB write must succeed inside `/sandbox`.

No container recreation, resizing, host writes or global prune. The checker
removes its own finite write probe in all cases.
