# Three containers, three states, and one confusion to clear

## The situation

You arrive on a machine where someone has already been working. Two containers
are there, and they are not in the same state:

```text
vitrine   it is running
rebut     it exists, stopped
```

That second state is the disconcerting one, and it is the subject of this lab:
**a stopped container has not disappeared**. It still holds its name, its logs
are still readable, and it will show up in any listing that is not limited to
running containers. Many people believe they have cleaned up by stopping, then
hit a name already taken without understanding why.

## Mission

On `docker.lab`, a throwaway Debian 13 with the engine running. The
`lab-base:1.0` image is already present: **nothing to pull, nothing to build**.

Two containers already exist, in two different states:

```text
vitrine   it is running
rebut     it exists, stopped
```

### 1. Run a container that is running

A container named **`premier`**, in the `running` state at the time of the
check.

The trap is immediate: a container whose command finishes stops right away.
Running the image as it is will not do, you have to give it something that
keeps it alive.

### 2. Its logs carry the requested line

Exactly `premier-est-la`, in the logs of `premier`.

A container's logs are the **output of its main process**: nothing else fills
them. What you ask the container to print ends up there, and that is what
separates "I ran an image" from "I ran an image and told it what to do".

### 3. Stop `vitrine`, without removing it

It must **still exist** and no longer be running. Removing it is a graded
mistake: the check says so explicitly, because it is the error this lab exists
to clear.

Stopping ends the container's process while keeping the container, with its
logs and its name.

### 4. Remove `rebut`

Its name must be gone from the listing, the one that shows stopped containers
**too**.

That is the observable consequence of a removal, and it is also why a stopped
container gets in the way: as long as it exists, it keeps its name, and no
other container can take it.

### What is not graded

The command you typed. A container can be run ten ways, and a stop can come
from a `stop`, a signal or a `kill`: the check looks at the resulting state,
not at the route.
