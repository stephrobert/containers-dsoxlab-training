# A full workspace

## The situation

On `docker.lab`, the `worker` of project `dsoxlab-troubleshoot-disque-plein` can
no longer write anything in `/sandbox`. This directory is a 16 MiB tmpfs, not a
host partition. It holds two files: `/sandbox/keep.txt`, a receipt to keep, and
`/sandbox/fill.bin`, a disposable filler. The project is in
`/opt/dsoxlab-troubleshoot-disque-plein`.

## Mission

Make `/sandbox` writable again in the **existing** container:

- `/sandbox/fill.bin` is absent;
- `/sandbox/keep.txt` still holds `keep-this-receipt`;
- a one MiB write into `/sandbox` succeeds.

Do not recreate the container, do not enlarge `/sandbox`, do not replace it with
a host directory, do not change its memory limits and do not run any global
prune.

## What is graded

1. The filler is gone and the receipt is intact.
2. The check writes one MiB into `/sandbox`, verifies that the file weighs
   1048576 bytes, then removes its probe.

Crossing a prohibition makes both checks fail, and the message names it. The
ceiling is read inside the container, through `df`.
