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
