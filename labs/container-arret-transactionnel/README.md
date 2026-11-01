# Signals, draining and durable transactions

[Français](README.fr.md) | [Challenge](challenge/README.md)

Docker sends its stop signal to the container's first process. A launcher
that starts a child and merely waits need not forward that signal. Inspect
the process tree, not just the Dockerfile's syntax:

```sh
docker top tutorial-payments
docker inspect tutorial-payments --format '{{json .Config.Entrypoint}}'
docker logs tutorial-payments
```

These are neutral examples, not resources installed by this lab.
A graceful application stops accepting new work, finishes admitted requests,
commits its transaction and closes before the stop deadline. A larger timeout
alone does not deliver a signal to the correct process.

SQLite separates an uncommitted write from durable committed state. Killing
a process during a transaction should roll back that transaction, not erase
earlier records. Query the domain through HTTP after recreating the container
with the same storage; a log message alone is not a durability proof.

Use an observable transaction barrier before stopping. Fixed sleeps do not
establish that the request reached its database transaction.
The fixture provides `/inflight` and `/release`, with a 12-second failure
deadline. Its write is released by signal reception, not elapsed sleeping.

Source anchor: local guide `docker/execution-depannage.mdx`, heading
`Stop vs Kill : quelle différence ?`, linked by `lab.yaml`.
This lab's automated trial has a 110-second outer budget, not a training SLA.

## Author validation

Local fixture tests: `python3 -m unittest discover -s labs/container-arret-transactionnel/author_tests -v`.
VM protocol: `LAB_HOME=$PWD python3 scripts/valider-labs.py --double-passage --lab container-arret-transactionnel`.
On `docker.lab`, 2026-11-01: zero/full/zero/full, 76 seconds for the complete
protocol, Docker state restored. This does not perform the separate human review.
