# Test: make a stack reliable

The stack works, "by restarting it twice". Two services: `coffre`, which holds a
value derived from a password, and `api`, which queries it **as it starts** and
then serves it.

## The five checks

They are of equal weight, and each rests on a verifiable fact.

### 1. The stack answers on the first try, from cold

**The check starts the stack itself**: that is the only way to measure a cold
start, since a stack already up has forgotten how it got there, and the second
attempt always succeeds.

Two facts are required together: the API answers, **and** no service needed to
restart. The second is the real check: a stack that picks itself up does
eventually answer, and it then works by accident.

### 2. The password out of the environment, and yet delivered

**This is the critical requirement: no total makes up for it.**

Two sides, measured together. The secret must no longer be readable in the
environment, in the image, or in what `docker compose config` renders. And the
vault must receive it **all the same**: removing a variable without replacing it
gives a clean, wrong stack, and the check compares the value served with the one
it expects.

### 3. A memory limit declared and applied

`HostConfig.Memory` says what the engine **retained** from the declaration.
`memory.max` in the cgroup says what the kernel **applies**. Both are read
because they are two distinct facts, and only the second protects the host: a
declaration the engine accepts without a word may impose **no** limit at all on
the container.

No value is imposed: a limit set too low would kill the service, and the start
check would see it.

### 4. A service that dies comes back on its own

**Every service** carries a restart policy, the vault as well as the API: a
stack whose vault does not come back is not made reliable, since the API falls
with it. The check reads the policy of both.

**And it makes the API die**, because declaring `restart:` proves nothing: the
value can be read by Compose and never apply, for instance on a container
created before the change.

It makes it die through the **failure trigger** the scenario announces, and not
through a `docker kill`: the engine treats a stop requested from outside as a
wanted stop, and no policy restarts a container stopped that way. What a policy
covers is a process that dies on its own.

### 5. Two variants that say different things

The check reads `docker compose config`, not the files: that is the composition
as the engine understands it, overlays applied. A `volumes:` written at the wrong
indentation level does not appear there, although it is indeed in the file.

## The marking

Five checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
