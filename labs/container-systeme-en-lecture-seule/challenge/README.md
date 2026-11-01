# Brief

Work on `docker.lab`, in `/opt/dsoxlab-container-systeme-en-lecture-seule`.

1. Keep `worker` active in project `dsoxlab-container-systeme-en-lecture-seule`,
   with label `dsoxlab.lab=container-systeme-en-lecture-seule`.
2. Enable read-only root; a real write at `/` must fail.
3. Provide a writable `/run` tmpfs of exactly 4 MiB with noexec and nosuid.
4. Keep the supplied command updating `/run/heartbeat`.

Preserve the pinned image and bounded resources. No host mounts or daemon edits.
