# Ten seconds to stop, and a 137 in the alerts

## The situation

Every deployment of your application triggers the same alert: the outgoing
container is reported as having "failed", code 137. The team has got into the
habit of ignoring it, which is the real problem: an alert people learn to
ignore protects nothing any more.

Two details are puzzling. The shutdown takes exactly the engine's timeout,
never less. And the application does know how to terminate cleanly: its code
traps the signal, writes a line to its logs and exits with a zero. That line
never appears.

A container taking the full timeout to die is not a slow container: it is a
container that ends up being **killed**, because it did not answer the polite
request that came first. What remains is finding out why the request does not
arrive.

## The goal

The `fragile` container is running. The sources of its image are readable in
`/opt/lab-signaux`: the application, the entry script, and the Dockerfile.

1. **Stop `fragile`**, and observe its exit code. It will not be zero: that is
   the symptom, and it is graded as such. **Do not fix it**, this container is
   the evidence.
2. Build an `img-corrige:1.0` image in which the container's PID 1 is the
   **application**, not the entry script.
3. Run then stop a `robuste` container from that image: its exit code must be
   **zero**.
4. Its logs must carry `sigterm-recu`, which `fragile` never wrote.

The brief also sits in `/opt/MISSION.md`.

One word separates the two images. And the entry script must **keep doing its
preparation**: emptying it would fix the symptom by removing the script's
reason to exist, which a check refuses.

## What is graded

The **state of the engine**: who the number one process is, the exit codes, and
the trace the application writes itself when it receives the signal.

Not the way you fix it. Several ways work, and they all count as long as the
signal reaches a process able to act on it.
