# What is asked

Two machines. `docker.lab` carried the stack; it is **no longer trusted**.
`docker-client.lab` is the host the service has to come back up on.

Both already carry:

- `/opt/lab-restauration/compose.yaml`, the stack as it was running;
- the image `lab-restauration/service:1.0`, built locally;
- `/opt/lab-restauration/sauvegarde/`, the backup taken before the fault.

**To work on `docker-client.lab`, open a session on it from your own machine:**

```bash
dsoxlab ssh docker-client
```

Hopping from one lab machine to the other is **not** possible: the two hosts do
not trust each other, and that is on purpose. You go through your own
workstation, which is the only one that talks to both.

The stack has three tiers. `front` is published on `127.0.0.1:18090` and sees
only `api`; `api` sees both sides; `db` is only on the data network, which is
**internal**. A business request crosses all three, and the service returns the
list of tiers crossed.

This is a **challenge**: the pass mark is 75%.

## 1. Establish the real state

Nothing tells you what was destroyed, and that is deliberate. Start by measuring
it rather than assuming it: containers, volumes, networks, and what the backup
contains.

## 2. Bring the service back up on `docker-client.lab`

The three tiers must run, in the Compose project `dsoxlab-restauration`, and the
business request must cross `front`, `api` and `db` in that order.

## 3. Restore the witness record

One record had been written **through the front end** before the fault. It must
be served again by the restored stack, and read by the same path: data you
cannot serve is not restored, it is merely present.

The backup is in `/opt/lab-restauration/sauvegarde/`.

## 4. Do not lose the isolation along the way

The network carrying `db` must stay **internal**, and `db` must publish no port.

Flattening the stack, everything onto one network, is the shortcut that makes a
restoration "work". It is refused here, and the check does not read your file: it
measures on the engine, verifying that a probe placed on the public network does
not reach `db`, and that `api` does.

## The expected final state

On `docker-client.lab`: the three tiers up, the business request crossing them,
the witness served, the data network internal and `db` with no published port.

## What is not graded

How you restore the data, nor the order in which you bring the tiers back up.
The check reads the state of both machines.
