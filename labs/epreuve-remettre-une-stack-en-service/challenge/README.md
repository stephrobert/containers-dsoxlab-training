# Test: bring a stack back into service

Use the project name and file path the mission gives. The supplied image
already exists: this test is about **orchestration**, not about building an
image.

## The five checks

They are of equal weight, and each rests on a verifiable fact.

### 1. The project carries its two services, and both run

Exactly two, `donnees` and `frontal`. The project name is part of the brief:
it is what ties containers, networks and volumes together, and without it
Compose derives it from the directory name.

### 2. The business request reaches the data service by its **service name**

The façade must return the value `donnees` holds. The front end queries the
name `CIBLE` gives it: that name is a **service** name, and renaming a
container does not get around it. A façade returning `amont-injoignable`
means the join does not happen.

### 3. Only the front end publishes, and on the loopback

The data service has no reason to be reachable from outside the stack. And
the façade must only be reachable on the address and port the provided
environment file declares.

### 4. A record written before a recreation is served after it

**This is the critical requirement: no total makes up for it.** It is the one
thing a composition loses for good: a service restarts, a network is
recreated, a port is republished, but a record written into a container's
writable layer leaves with it.

The check writes a witness, recreates the stack and reads the façade again. It
imposes no volume name: only the effect counts. An anonymous volume is not
reattached to a recreated service, and therefore shows up here.

### 5. The resolved composition carries no unresolved variable

`docker compose config` returns the composition **as the engine understands
it**, with variables substituted. A variable with no value and no default
becomes an empty string there: Compose **warns**, and **accepts anyway**. The
stack then starts listening on a port nobody expects, and the warning goes to
standard error, where a script does not read it.

And at least one value must come from an **interpolation**: the lab provides a
`.env`, and a composition that copies its values by hand does not use it.

## What the test does not ask for

No health probe, no dependency condition. They are taught in the next module,
and the supplied front end retries its upstream: start-up order does not
matter.

## The scale

Five checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**.

Four hints, from the vaguest to the most explicit, and **they cost points**.
