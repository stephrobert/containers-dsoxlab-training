# Bring the stack back into service

A small application used to run on this machine, as two Compose services. Its
composition has been lost: the images are there, the starting data too, and
nothing links them any more.

The local image `dsoxlab-epreuve-remettre-une-stack-en-service:service`
carries both roles, and there is **nothing to write and nothing to rebuild**:

- `donnees` serves its `/data` directory on port 8080, **publishing nothing**;
- `frontal` fetches the value from an upstream it queries **by the name the
  `CIBLE` variable gives it**, then serves it in turn on 8080.

The front end retries its upstream for a minute before giving up, so start-up
order will not be a problem for you.

## Mission

Write `/opt/lab-epreuve-remettre-une-stack-en-service/compose.yaml`, and start
it in the project `dsoxlab-epreuve-remettre-une-stack-en-service`.

What is expected at the end:

- the project carries **exactly** the two services, `donnees` and `frontal`,
  and both run;
- the front end reaches the data service **by its service name**: the façade
  returns the value `donnees` holds;
- **only the front end publishes** a port, and only on the address and port
  the provided environment file declares;
- a **record written before a recreation is served after it**;
- the composition **reads** the address and the port from
  `/opt/lab-epreuve-remettre-une-stack-en-service/.env` instead of copying
  them, and its resolved form carries no unresolved variable.

## What you do not have to do

No health probe, no dependency condition: the front end retries, and that is
enough. No registry, no image to build, no secret.

## How you are graded

Five checks of equal weight, and **only the final state counts**. No command
is imposed, and the names you give the network and the volume are yours.

The pass mark is **75 out of 100**. One requirement is made up for by no
total: **a record written before a recreation and lost after** fails the test,
even with everything else in place. It is the one thing a composition loses
for good.

Four hints are available, and **they cost points**: `dsoxlab hint`.

## Test: bring a stack back into service

Use the project name and file path the mission gives. The supplied image
already exists: this test is about **orchestration**, not about building an
image.

### The five checks

They are of equal weight, and each rests on a verifiable fact.

#### 1. The project carries its two services, and both run

Exactly two, `donnees` and `frontal`. The project name is part of the brief:
it is what ties containers, networks and volumes together, and without it
Compose derives it from the directory name.

#### 2. The business request reaches the data service by its **service name**

The façade must return the value `donnees` holds. The front end queries the
name `CIBLE` gives it: that name is a **service** name, and renaming a
container does not get around it. A façade returning `amont-injoignable`
means the join does not happen.

#### 3. Only the front end publishes, and on the loopback

The data service has no reason to be reachable from outside the stack. And
the façade must only be reachable on the address and port the provided
environment file declares.

#### 4. A record written before a recreation is served after it

**This is the critical requirement: no total makes up for it.** It is the one
thing a composition loses for good: a service restarts, a network is
recreated, a port is republished, but a record written into a container's
writable layer leaves with it.

The check writes a witness, recreates the stack and reads the façade again. It
imposes no volume name: only the effect counts. An anonymous volume is not
reattached to a recreated service, and therefore shows up here.

#### 5. The resolved composition carries no unresolved variable

`docker compose config` returns the composition **as the engine understands
it**, with variables substituted. A variable with no value and no default
becomes an empty string there: Compose **warns**, and **accepts anyway**. The
stack then starts listening on a port nobody expects, and the warning goes to
standard error, where a script does not read it.

And at least one value must come from an **interpolation**: the lab provides a
`.env`, and a composition that copies its values by hand does not use it.

### What the test does not ask for

No health probe, no dependency condition. They are taught in the next module,
and the supplied front end retries its upstream: start-up order does not
matter.

### The scale

Five checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**.

Four hints, from the vaguest to the most explicit, and **they cost points**.
