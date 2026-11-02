# epreuve-fiabiliser-une-stack: the reliability module's test

## What this test measures

Making a stack that already works, or almost, reliable. It closes the "Make a
stack reliable" module and re-explains nothing.

Its `lab_type: challenge` is what allows its `exam_passing_score`, set to **75**.
The five checks are of equal weight, and one of them is critical.

## The delivered stack WORKS, and that is the starting point

Nobody leaves a stack that never starts in production. They leave the one that
starts **when you restart it twice**, and the team picks up the habit of
restarting it. That is what this test reproduces, and that is what makes it
hard: there is no outright failure to find, there is a fragility to name.

## The five defects, and why they live together in a real file

| Defect | Symptom | What it teaches |
| --- | --- | --- |
| `depends_on` with no health condition | "you have to restart it twice" | starting a container is not making a service available |
| the password in `environment` | none: everything works | a readable secret follows the stack everywhere, and nobody notices |
| no memory limit | none, until the day there is | a leaking service takes its neighbour down, not itself |
| no restart policy | none, until the first death | a service that dies at four in the morning stays dead until someone notices |
| the source mount left in deployment | none, until the next deployment | what helps in development hurts in production |

**Four of the five have no symptom at all.** That is the module's real lesson:
reliability is not measured by what falls over today.

## Why the start check restarts the stack itself

A cold start is only measured from cold. A stack already up has forgotten how it
got there, and the second attempt always succeeds: that is precisely the symptom
being fixed. The check therefore runs `down` then `up -d`, and the brief says so.

It requires **two facts together**: the API answers, and no service needed to
restart. The second is the real check. With a restart policy and without waiting
for the vault's health, the API eventually answers, after two or three deaths: it
works, and it is wrong. A marking scheme that only looked at the answer would
validate that stack.

## The critical requirement, and the false fix it catches

**The password readable in the environment fails the test**, even at 80 points.
An environment variable is read by `docker inspect`, by `docker compose config`,
in the logs of whoever ran the command, and in the versioned file.

But the check has **two sides**, and that is what gives it value: the secret must
have gone from those places **and** reached the service. Removing a variable
without replacing it gives a clean, wrong stack that serves a default value or
nothing at all. The check therefore compares the value served with the derivative
the lab computed from the real password: it can only be right if the secret
actually arrived.

## Why the limit is read in two places

`HostConfig.Memory` says what the engine **retained** from the declaration.
`memory.max` in the cgroup says what the kernel **applies**. Reading both is not
a stylistic precaution: they are two distinct facts, and only the second
protects the host.

Nine forms measured on 2026-11-02 against Docker 29.9.2 and Compose 5.6.1, and
the result runs against intuition. `mem_limit` at service level **and**
`deploy.resources.limits.memory` both give `HostConfig.Memory` 67108864 for 64M:
the form is not the trap. A key written at the wrong level is not one either,
because Compose validates its schema and **refuses** the file, with a message
and an error code.

The one case accepted without a word and never applied lies elsewhere:
`deploy.resources.reservations.memory` is a **reservation**, not a limit. It
passes validation, and it leaves `HostConfig.Memory` at zero and `memory.max` at
`max`. The file talks about memory, and the container has no limit.

## Why the check causes a failure instead of killing

Declaring `restart:` and reading it back in the inspection proves nothing: the
value can be there and never apply, for instance on a container created before
the change. The only question that matters is "does it come back?".

It is **not** answered by killing, and that is what the "Frame resources and
restarts" lesson teaches. Measured on 2026-11-02: after a `docker kill` on a
container with `restart: unless-stopped`, the engine treats the stop as
**wanted**, the container stays `exited`, and the restart counter is still at
zero twenty seconds later. A `docker exec kill -9 1` does nothing either, since
the kernel shields a namespace's PID 1 from signals sent from inside that
namespace, SIGKILL included.

What a policy really covers is a process that **dies on its own**. The check
therefore places the failure trigger the scenario announces,
`/tmp/panne-provoquee`, and the service exits with an error on the next request.

## Why the checks are independent

Two of them would contradict each other otherwise: the cold-start check requires
a restart counter at zero, and the policy check **kills** a container to verify
it comes back. The first therefore restarts the stack itself, and both execution
orders yield the same verdict.

That is a lesson paid for elsewhere in this catalogue: execution order is not
part of pytest's contract, and a test that depends on another's trace returns a
verdict that depends on chance.

## What the test does not measure

Backup, restore, a second host: that is the subject of
`epreuve-restaurer-une-stack`. Here, one host and five points of reliability.
