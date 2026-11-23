# You are asked to isolate, but to isolate what from what?

## The situation

Two requests arrive on the same morning.

The first comes from security: a container processes files uploaded by clients,
and it must be able to reach **nothing**. Not the outside, not the host, not its
neighbours. It reads a volume, it writes a volume, it needs no network at all.

The second comes from the application team: their database must only be
reachable **by** their application. But reachable it must be, obviously, and the
application has to find it by name.

Both requests say "isolate it". They are not asking for the same thing at all,
and the answer to one is an outage for the other: a confined network still lets
neighbours through, and no network at all makes the database unusable.

## The goal

Obtain both isolations on the same machine. Four containers are running, all
built on `lab-isolation:1.0`, which listens on its port 80 and answers a token.
All are on the default network, so all of them get out.

```text
dehors      THE WITNESS. Published on the machine's routable address, it holds
            the role of everything OUTSIDE the container network.
            DO NOT TOUCH IT.

coffre      must have NO network: no interface, no neighbour, nothing
atelier-a   must be CONFINED with atelier-b
atelier-b   must reach atelier-a BY ITS NAME, and must not get out
```

Four things are expected:

1. `coffre` has no network interface besides the loopback.
2. `coffre` does not reach `dehors`.
3. A network named `confine` exists, declared **internal**, with the subnet
   **172.29.9.0/24**.
4. `atelier-a` and `atelier-b` are on it, they reach each other **by name**, and
   neither of them reaches `dehors`.

The brief is also written to `/opt/MISSION.md`, with the routable address.

## What you need to know before starting

**A container's network is only chosen at creation**, for the option that
declares it: it has to be destroyed and recreated.

And the previous lab's trap comes back: **a container can be on two networks at
once**. Being on the confined network is not enough, it also has to have left
the other one, otherwise the way out remains.

## What is graded

The **state of the system**. The first two checks are deliberately separate: the
first reads the container's configuration, the second tests what it can do. The
two can diverge, and when they diverge it is interesting.

The fourth check, though, is indivisible: confining without the members talking
to each other would give an unusable service, and having them talk without
confining them would be just one more dedicated network.

## A word on the mechanism

An internal network is not a filter placed in front of the containers. It is the
**absence of the path**: a member of that network has no default route. You can
see it for yourself, and it is the clearest way to understand what is going on.

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. Four containers
are **already running**, all built on `lab-isolation:1.0`, which listens on its
port 80 and answers a token. All are on the default network, so all of them get
out.

```text
dehors      THE WITNESS, published on the routable address. DO NOT TOUCH IT.
coffre      must have NO network at all
atelier-a   must be CONFINED with atelier-b
atelier-b   must reach atelier-a BY ITS NAME, without getting out
```

The machine's routable address is in `/opt/MISSION.md`.

### 1. `coffre` has no network interface

Besides the loopback, nothing must remain. No interface, so no address, so no
neighbour.

The check looks at the interfaces **inside** the container, not at what the
engine declares: the effect counts, not the path.

### 2. `coffre` does not reach `dehors`

That is the consequence, and it is measured. A container with no network reaches
nothing at all: not the outside, not the host, not its former neighbours.

This check is separate from the first on purpose. The first reads the
configuration, this one tests what the container **can do**, and the two can
diverge.

### 3. A `confine` network, internal, on 172.29.9.0/24

The word that counts is **internal**. An ordinary network lets its members out;
an internal one gives them **no default route**, and that is what confines them.

The subnet is imposed: a network created without a plan gets one the engine
picks, which is avoided in production.

### 4. The workshop talks without getting out

Three requirements at once, and they are inseparable:

- `atelier-a` and `atelier-b` are on `confine`;
- `atelier-b` reaches `atelier-a` **by its name**;
- neither of them reaches `dehors`.

Confining without the members talking to each other would give an unusable
service. Having them talk without confining them would be just one more
dedicated network, which was the previous lab. The conjunction is what counts.

### What you need to know before starting

**A container's network is only chosen at creation**, for the option that
declares it: destroy and recreate, under the **same name**.

The image carries its listener, so relaunching needs no particular command:

```bash
docker run -d --name <name> <network options> lab-isolation:1.0
```

And the previous lab's trap comes back: **a container can be on two networks at
once**. Being on the confined network is not enough, it also has to have left
the other one.

### Do not touch `dehors`

It is the witness for everything outside the network. Destroying it or changing
its publication would make two checks pass without proving anything, and the
checks verify by name that it is running and answering.

### A word on tooling

Do not settle for a connection that succeeds: **read the answer**. Docker's
proxy accepts before anything is listening.

And to understand what is going on rather than endure it, look at a confined
container's routing table: `docker exec <name> ip route`.

### What is not graded

The command you typed. Only the state counts, and it is measured inside the
container as well as on the network.
