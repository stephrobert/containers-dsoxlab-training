# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The container
`greffier` is **already running**: nothing to pull, nothing to build, nothing
to start.

Four pieces of information concern it, and **none is written on this machine**.
They are drawn at random on every pass: there is nothing to remember, and
nothing to copy from anywhere else.

## 1. The session token

`greffier` announced a token as it started. Write it in
`/opt/lab-inspection/reponses.txt`, on the `jeton=` line.

It is in no configuration file, in no image, and in no script: **the
container's output is the only place it exists**. That is the first question of
any troubleshooting, and also the first command to keep at hand.

## 2. The container's address

The engine gives the container an IP address **when it creates it**. Write it
on the `adresse=` line.

This is the container's own address, not the host's and not the gateway's. It
is reassigned at each creation, so it cannot be remembered: it has to be asked
for.

## 3. The host port

The container's `80` is published on a port of the **host**, and the engine
chose it on its own. Write that port on the `port=` line.

Careful: what is expected is the **host's** port, the left-hand side of the
mapping. The `80` is the container's port, the only value you already knew on
arrival.

An answer of the form `0.0.0.0:32768` is accepted: it does name the right port.

## 4. The trace, taken out of the container

`greffier` wrote `/var/log/greffier/trace.log` **after** it started. That file
is in no image: it has to be taken out of the container and put down at
`/opt/lab-inspection/trace.log`.

It is expected **unchanged**, not retyped: the trace carries a sequence drawn
at random, which is exactly what cannot be reconstructed by hand.

This is the move you make for real to carry off a log or a fingerprint before
destroying a container.

## The container must still be running at the end

You interrogate a live container, you do not stop it to search it. A stopped
container no longer has an address or a port table: stopping it costs two
checks.

`docker start` puts it back, but its values will have changed: they would have
to be read again.

## What is not graded

The command you typed. Each answer is recomputed by questioning the engine,
then compared with what you wrote. Several paths give the same value, and all
of them count.
