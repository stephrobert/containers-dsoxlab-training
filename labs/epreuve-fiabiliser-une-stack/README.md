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

## The four defects, and why they live together in a real file

| Defect | Symptom | What it teaches |
| --- | --- | --- |
| `depends_on` with no health condition | "you have to restart it twice" | starting a container is not making a service available |
| the password in `environment` | none: everything works | a readable secret follows the stack everywhere, and nobody notices |
| no memory limit | none, until the day there is | a leaking service takes its neighbour down, not itself |
| the source mount left in deployment | none, until the next deployment | what helps in development hurts in production |

**Three of the four have no symptom at all.** That is the module's real lesson:
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
`memory.max` in the cgroup says what the kernel **applies**. The two can differ,
and the case is common: a limit written in a deploy section meant for an absent
orchestrator is read by Compose, accepted without error, and never applied. The
container stays unlimited, and the file looks right.

## Why the policy check kills a container

Declaring `restart:` and reading it back in the inspection proves nothing: the
value can be there and never apply, for instance on a container created before
the change. The only question that matters is "does it come back?", and it is
answered by killing.

`docker kill` and not `docker stop`: a requested stop is a wanted stop, and no
policy restarts a container you stopped yourself. Confusing the two leads to the
wrong conclusion that the policy does not work.

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
`epreuve-restaurer-une-stack`. Here, one host and four points of reliability.
