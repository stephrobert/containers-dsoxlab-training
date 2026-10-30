# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running.

```text
boutique    the application. It looks for its database under the name `base`,
            hardcoded in its configuration, and that name cannot change.

catalogue   the database. It listens on its port 80 and answers a token.
```

Both are running, both answer when questioned from the inside, and the
application reaches nothing. The audit also reports that the database is
reachable from the outside.

## The four checks

**1. From `boutique`, the name `base` resolves**, to an address `catalogue`
actually carries.

A name pointing elsewhere is worse than no name: the application would talk to
something else.

**2. From `boutique`, a connection to `base` port 80 returns the token.**

This check is separate from the first because their causes differ: resolving is
not reaching.

**3. `catalogue` publishes no port.**

That is the audit's line. A database has no reason to be reachable from the
outside: its application reaches it through the container network.

**4. From `boutique`, the name `catalogue` resolves as well.**

Operations must keep designating the container by its real name. That is a
requirement, not a detail: the application has its own name, operations keeps
theirs.

## This is an assessment

**Nothing will be explained to you again.** The five networking labs of the
course taught what is needed. This one measures.

Four checks of equal weight, **75 points to pass**. The checks' messages name
the symptom, never the move: making the link is the work.

Four hints exist, from the vaguest to the most explicit, and they cost points.
The last one names the mistakes that let success be believed.

## Two things that are not hints

Keep the containers' **names**: the checks look for them by name, and the fourth
point already tells you why.

And to conclude that a service answers, **read the answer**. Docker's proxy
accepts a connection before anything is listening: `nc -w 3 <target> 80` must
print a `jeton=` line.

## What is not graded

The path. Recreating a container, attaching then detaching it, creating a third
network: anything leading to the required state counts. The checks name no
network.
