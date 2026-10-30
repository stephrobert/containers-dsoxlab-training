# troubleshoot-conflit-de-port: two messages, two worlds

## What this lab tests

That two port conflicts which look alike do not have the same cause, and that
Docker's tools are **blind** to one of the two.

## Measured before being written

On `docker.lab`, on 2026-10-30:

| Culprit | Engine's message | `docker ps` sees it | `ss` sees it |
| --- | --- | --- | --- |
| a container | "port is already allocated" | **yes** | yes, `docker-proxy` |
| a host process | "Error starting userland proxy: listen" | **no** | yes, the program |

The two messages differ, and that is the key. The first comes from the
**engine**, which knows what it has already reserved; the second comes from the
**system**, which refuses to listen. A troubleshooter who reads that difference
knows immediately whether to look inside Docker or outside.

Also measured: the refused container is **created all the same**, status
`created`, and it therefore occupies its name. That is why a second attempt
fails on "name already in use" and makes you believe in another failure.

And what is **not** a conflict: two containers can publish the same **container**
port on two different host ports. It is the host's port that is unique.

## Two design mistakes corrected by the validation cycle

This lab was red twice, and both times for the **same root cause**: a diagnostic
value cannot be read from an object the repair modifies.

**First version.** The lab asked for the intruders to be given back the port
they claimed, therefore for the culprit's port to be freed. At grading time, the
port's culprit was no longer `occupant` but the intruder itself, and the answers
to checks 2 and 3 became wrong. The lab contradicted itself.

The correction is not technical, it is **pedagogical**: freeing the port is the
spontaneous move and the wrong one. So the lab asks for the newcomer to be
**moved**, which leaves the culprits in place and keeps them identifiable.

**Second version.** The first check still read `intrus-a`'s status, which runs
after repair. Hence the **witness**: `temoin-refuse` fails like the others, the
brief expressly asks for it not to be repaired, and the status is read from it.
It stays true from start to finish.

## The fourth check verifies both halves of the remedy

The intruders run **elsewhere**, and the culprits are **intact**.

Without the second half, the most destructive answer would pass: cutting
everything would make the intruders run and the lab would teach exactly what to
avoid. Nothing said the container in place and the host's program were useless.

## A tooling trap, met for the second time

`pkill -f "nc -l -k -p 18201"` returns **`rc: -15`**: the command line of the
shell carrying the pkill contains the pattern sought, so the shell kills itself
before it can return 0, and `|| true` is never reached.

The parade comes from the `ps | grep` world: one letter in brackets. `n[c] -l -k
-p 18201` matches `nc -l -k -p 18201`, and the pkill's line contains `n[c]`,
which that pattern does not match.

It is this trap's second appearance in the section. In `container-limite-cpu` it
was absorbed by accepting code 143, which was correct but less clean: here the
process to kill is **outside** the containers, and leaving it alive would hold a
host port indefinitely.

## One cleanup move this lab alone has to make

Killing a process of the **host**. No other lab in the catalogue puts anything
outside the containers, and a forgotten listener would hold its port
indefinitely: the next lab wanting that port would fail for reasons unrelated to
its subject.

## The starting state is broken, and that is the repository's rule

| Laid down by the setup | Starting state | Expected move | Check |
| --- | --- | --- | --- |
| `reponses.txt` | three keys, three **empty** values | fill them in | 1, 2 and 3 |
| `occupant` | running, holding a port | leave it alone | 4 |
| a host listener | listening, outside Docker | leave it alone | 4 |
| `intrus-a`, `intrus-b` | created, refused | move them | 4 |
| `temoin-refuse` | created, refused | **do not repair** | 1 |

The setup verifies that the three refused ones are not running and that both
ports are indeed taken before handing over.

## What the lab does not require

A path. The container culprit can be found from the container list as well as
the inspection, the host's one through any tool reading sockets, and the move is
done by recreating the container on a free port, by any means.
