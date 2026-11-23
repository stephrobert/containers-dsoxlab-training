# The stack that only works on the second try

This stack has been running for months, and the team has picked up a habit: when
it does not answer, they restart it. It works. Nobody has looked into why.

It lives in `/opt/lab-stack-fiable/compose.yaml`, its project is named
`stack-fiable`, and it has two services. `coffre` holds a value derived from a
password. `api` queries it **as it starts**, then serves it on
`127.0.0.1:18420`.

Three other things were noted in passing, and none of them looks urgent: the
password can be read in the file, no service has a limit, and the source code
mount that was useful during development is still there.

## What is expected at the end

1. A `docker compose down` followed by a `docker compose up -d` yields a stack
   that **answers on the first try**, without any service having needed to
   restart.
2. The password appears **neither in the containers' environment** nor **in the
   image**, nor in what `docker compose config` renders, and the vault receives
   it all the same: the value served must stay correct.
3. Each service carries a **memory limit**, visible in the container's
   inspection as well as in its cgroup.
4. Each service carries a **restart policy**: a container that is killed comes
   back on its own.
5. There are **two variants**: `compose.yaml`, the deployment, which does **not**
   mount the source code, and `compose.dev.yaml`, the development one, which
   does. The second overlays the first.

The project keeps its name, and the API keeps its port. The
`lab-stack-fiable:1.0` image is provided: there is **nothing to rebuild**.

The service carries a **failure trigger**, which is a tool of the lab and not a
riddle: if the file `/tmp/panne-provoquee` exists inside a container, the service
exits with an error on the next request. That is how the restart-policy check
makes a service die, because a `docker kill` would not: the engine treats it as a
wanted stop, and no policy restarts a container you stopped yourself.

The full brief is also on the machine, in `/opt/lab-stack-fiable/MISSION.md`. It
states in particular that the service reads its password from a **file** before
looking at its environment, and that the path to that file is set by a variable.

## How you are graded

Five checks of equal weight, and **only the final state counts**. No syntax is
imposed: two ways of obtaining the same behaviour get the same mark.

The pass mark is **75 out of 100**. One requirement is made up for by no total:
**a readable password fails the test**, even with everything else in place. And
it is looked for in **four** places, not one: the containers' environment, the
**image's layers**, what `docker compose config` renders, and the **value
served** by the API.

Moving it out of the environment and into the image is therefore not a fix, it
is worse: an environment variable is read by `docker inspect` and by anyone who
can talk to the daemon, but an image **gets published**.

Beware the false fix: removing the password **without replacing it** gives a
clean, wrong stack. The check compares the value served with the one it expects.

Four hints are available, and **they cost points**: `dsoxlab hint`.

## Test: make a stack reliable

The stack works, "by restarting it twice". Two services: `coffre`, which holds a
value derived from a password, and `api`, which queries it **as it starts** and
then serves it.

### The five checks

They are of equal weight, and each rests on a verifiable fact.

#### 1. The stack answers on the first try, from cold

**The check starts the stack itself**: that is the only way to measure a cold
start, since a stack already up has forgotten how it got there, and the second
attempt always succeeds.

Two facts are required together: the API answers, **and** no service needed to
restart. The second is the real check: a stack that picks itself up does
eventually answer, and it then works by accident.

#### 2. The password out of the environment, and yet delivered

**This is the critical requirement: no total makes up for it.**

Two sides, measured together. The secret must no longer be readable in the
environment, in the image, or in what `docker compose config` renders. And the
vault must receive it **all the same**: removing a variable without replacing it
gives a clean, wrong stack, and the check compares the value served with the one
it expects.

#### 3. A memory limit declared and applied

`HostConfig.Memory` says what the engine **retained** from the declaration.
`memory.max` in the cgroup says what the kernel **applies**. Both are read
because they are two distinct facts, and only the second protects the host: a
declaration the engine accepts without a word may impose **no** limit at all on
the container.

No value is imposed: a limit set too low would kill the service, and the start
check would see it.

#### 4. A service that dies comes back on its own

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

#### 5. Two variants that say different things

The check reads `docker compose config`, not the files: that is the composition
as the engine understands it, overlays applied. A `volumes:` written at the wrong
indentation level does not appear there, although it is indeed in the file.

### The marking

Five checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
