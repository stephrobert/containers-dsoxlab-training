# epreuve-reprendre-un-hote-docker: the administration module's test

## What this test measures

Taking over a machine nobody looked after, without breaking what runs on it or
losing what it holds. It closes the "Administer the daemon" module and
re-explains nothing.

Its `lab_type: challenge` is what allows its `exam_passing_score`, set to **75**.
The five checks are of equal weight, and one of them is critical.

## Why this test was bench-tested before being written

It is the most intrusive setup in the catalogue: it touches the **daemon**,
**systemd** and the **accounts**, not merely containers. A reservation was
therefore stated before writing it: if its cycle did not give back a clean
machine, it would not be delivered.

Two moves were tested separately, on a bench that set them then removed them:

- **opening a TCP API without TLS**, through a systemd override, then removing it
  and checking the daemon comes back. The trap is well known: a `hosts` entry in
  `daemon.json` while systemd already passes `-H fd://` makes the daemon
  **refuse to start**. That would have broken the machine instead of planting a
  defect;
- **filtering by HTTP method** in front of the socket, and observing `200` on a
  read and `403` on a stop.

The bench concluded, and that is the condition on which this test exists.

## The four defects, and what they teach

| Defect | What it teaches |
| --- | --- |
| no log rotation | the `json-file` driver's default is to write without limit, and a chatty container fills the disk |
| dangling images and build cache | what an unmaintained host accumulates without anyone seeing it |
| a departed account still in `docker`, a tool mounting the socket | being in that group, or talking to the socket, means being able to do anything on the host |
| the API open over TCP without TLS | the gravest fault: one privileged container, and you are root |

## The critical requirement, and why it is the best trap in the catalogue

**Losing the application's volume fails the test**, even at 80 points.

It is a good trap because it does not spring on carelessness, but on **the move
that seems most reasonable**: to give space back you type `docker system prune`,
and one of its options takes volumes away. The learner who does it is right
about the intention and wrong about the reach.

The check compares the **data**, not the volume's existence: a volume recreated
empty carries the right name and is worth nothing.

## What the checks measure, and what they do not

The brief spoke of "free space above the threshold". An absolute threshold would
have meant nothing on this machine, which has twenty gigabytes with fourteen
free: the lab cannot fill a disk without risking filling it for real.

The check therefore measures what is genuinely at stake and verifiable: the
reclaimable objects have been given back, and the useful volume stayed. That is
the skill, not the number.

## What this lab gives back to the machine

Everything it changes, it records beforehand in
`/root/.lab-reprise-state.json`, and `cleanup` puts it back as it found it: the
exact contents of `daemon.json` if it existed, its absence otherwise, the
systemd override removed, the override directory removed **if it did not exist
before**, the daemon restarted on that restored configuration, the lab's two
accounts deleted, and the `docker` group restored.

The daemon is brought back **before** everything else, because the validation
cycle queries the engine after cleanup: a silent daemon does not give a
discrepancy, it gives an absence of measurement.

## What the test does not measure

Rootless mode, and hardening the runtime: that is the subject of
`epreuve-durcir-sans-casser`.
