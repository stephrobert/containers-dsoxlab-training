# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. **Three
containers refused to start**, each on an already taken port:

```text
intrus-a        wanted the host's port 18200
intrus-b        wanted the host's port 18201
temoin-refuse   wanted port 18200 too
```

**Start by comparing the two error messages** the engine returned for `intrus-a`
and `intrus-b`. They do not say the same thing, and that is the whole key to the
diagnosis.

The first three answers go into `/opt/lab-conflit/reponses.txt`, one line per
entry, with no spaces around the equals sign.

## 1. `temoin-refuse`'s status

On the `statut_intrus=` line.

A refused container is **created all the same**, and it therefore occupies its
name. That is why a second attempt fails on a completely different message,
about a name already in use, and makes you look for a second problem that does
not exist.

**Do not repair `temoin-refuse`**: it stays as it is so that its status remains
readable to the end.

## 2. The container occupying port 18200

On the `coupable_a=` line.

The engine's message says the port is **already allocated**. That wording means
**it** reserved it itself, so the culprit is one of its containers. The
container list names it at once.

That is the easy case.

## 3. The program occupying port 18201

On the `coupable_b=` line.

The second message does not mention allocation: it mentions a **refused
listen**. That wording comes from the system, not the engine, and it says the
culprit is **outside** Docker.

**Do not look on Docker's side**: it shows nothing at all here, and that is
precisely what wastes time. The host's socket table names the program in one
line.

You have to be root for it to name it.

## 4. Repair, without cutting anything

The containers `intrus-a` and `intrus-b` must **run**, and publish their port 80
on a host port **other** than the one that was taken.

And both culprits must still be **there**: the container that runs, and the
host's program that listens.

Freeing the port would be the spontaneous move, and it is the wrong one.
**Nothing said they were useless**, and a taken port is often taken for a
reason. You do not cut a running service to start another one: it is the
newcomer you move.

The check verifies both halves.

## One detail that is not a conflict

Two containers can publish the same **container** port on two different host
ports. It is the **host's** port that is unique, not the container's.

## What is not graded

The command you typed. The culprits can be found in several ways, and the move
is done by recreating the container on a free port, by any means.
