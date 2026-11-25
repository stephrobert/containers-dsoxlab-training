# The application is slow, and yet it has headroom

## The situation

A service runs in a container, capped at half a processor, which is plenty for
what it does. And it is slow. Not down: slow, in fits and starts, with response
times tripling for no apparent reason.

The machine's metrics are calm. The container's show that it consumes exactly
what it was granted, which ought to be reassuring.

The cause is in the application itself, and it is an ordinary one: at startup it
asks the system how many processors are available, and sizes its threads on that
answer. It got the **machine's** number, not its limit's. So it launches far
too much work in parallel, and spends its time being held back by the kernel.

## Mission

On `docker.lab`, a throwaway Debian 13 with **two** processors and the engine
running. The container `brideur` is **already running**, capped at **0.5 CPU**,
and it does nothing for now.

The first two answers go into `/opt/lab-cpu/reponses.txt`, one line per entry,
with no spaces around the equals sign.

### 1. The quota the cgroup declares

On the `quota=` line, **as it is**.

The kernel does not know CPU fractions: it counts a **time** per slice of time.
So the value is written as two numbers, and `0.5` leaves no trace in it.

That is also what explains why the limit applies through **throttling** rather
than by refusing work.

### 2. The number of CPUs `brideur` sees

On the `cpu_vus=` line, asking **the container itself**.

**Compare it with the machine's CPU count before concluding you were wrong.**
The answer is surprising, and it is the lab's most useful question.

A time limit is not a view restriction. An application sizing its threads on
that number launches far too many, and spends its time being held back.

### 3. A container that sees fewer CPUs

Start a container named `epingle` that sees **only one** CPU.

It is not the same option as the one capping `brideur`, and it is not the same
mechanism: one limits the **time** granted, the other restricts the **set of
processors** usable. Only the second changes what the container sees.

The cgroup declares both, but in different places.

### 4. The proof that the limit has bitten

Put `brideur` under enough load for the kernel to have to **throttle** it.

Its cgroup counts the throttlings. As long as that counter is **zero**, the
limit has never bitten: it may well be right, it is not proven.

Enough load is a load that asks for more than the limit. Measure the counter
before and after, without assuming how many processes it takes.

### A word on tooling

A container's cgroup files are **readable without privilege**: measured on this
machine, they are `r--r--r--` or `rw-r--r--`, and an ordinary account opens them
without `sudo`. **Writing** them does require one, and that is what separates
observing from tuning.

And if you stop your load with `pkill -f`, know that the pattern may match the
shell carrying your command: it kills itself, and the return code is that of a
received signal. That is not an error.

### What is not graded

The command you typed. The load can be produced in several ways, and both
limiting options are set at the container's creation. Only the state counts, and
the throttling counter is part of it.
