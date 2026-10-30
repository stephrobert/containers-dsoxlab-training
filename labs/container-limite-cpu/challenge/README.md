# What is asked

On `docker.lab`, a throwaway Debian 13 with **two** processors and the engine
running. The container `brideur` is **already running**, capped at **0.5 CPU**,
and it does nothing for now.

The first two answers go into `/opt/lab-cpu/reponses.txt`, one line per entry,
with no spaces around the equals sign.

## 1. The quota the cgroup declares

On the `quota=` line, **as it is**.

The kernel does not know CPU fractions: it counts a **time** per slice of time.
So the value is written as two numbers, and `0.5` leaves no trace in it.

That is also what explains why the limit applies through **throttling** rather
than by refusing work.

## 2. The number of CPUs `brideur` sees

On the `cpu_vus=` line, asking **the container itself**.

**Compare it with the machine's CPU count before concluding you were wrong.**
The answer is surprising, and it is the lab's most useful question.

A time limit is not a view restriction. An application sizing its threads on
that number launches far too many, and spends its time being held back.

## 3. A container that sees fewer CPUs

Start a container named `epingle` that sees **only one** CPU.

It is not the same option as the one capping `brideur`, and it is not the same
mechanism: one limits the **time** granted, the other restricts the **set of
processors** usable. Only the second changes what the container sees.

The cgroup declares both, but in different places.

## 4. The proof that the limit has bitten

Put `brideur` under enough load for the kernel to have to **throttle** it.

Its cgroup counts the throttlings. As long as that counter is **zero**, the
limit has never bitten: it may well be right, it is not proven.

**Enough load takes more than one busy process.** A single one can stay under
the ceiling without ever touching it, and the counter would stay at zero.

## A word on tooling

You have to be root to read a container's cgroup files.

And if you stop your load with `pkill -f`, know that the pattern may match the
shell carrying your command: it kills itself, and the return code is that of a
received signal. That is not an error.

## What is not graded

The command you typed. The load can be produced in several ways, and both
limiting options are set at the container's creation. Only the state counts, and
the throttling counter is part of it.
