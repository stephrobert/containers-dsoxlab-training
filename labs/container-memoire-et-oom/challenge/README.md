# Brief

Work on `docker.lab`, in `/opt/dsoxlab-container-memoire-et-oom`.

Keep `worker` active in project `dsoxlab-container-memoire-et-oom`, with its
`dsoxlab.lab=container-memoire-et-oom` label. Keep the project's pids and CPU
guards too. No host swap changes, no unbounded allocator.

Four independent checks measure four different things.

## 1. The declared limits bound memory and forbid swap

`Memory` and `MemorySwap` both equal 33554432, that is 32 MiB.

Their equality is what forbids swap, and the distinction is not cosmetic.
Measured on the lab host, in both views:

| Form | declared `MemorySwap` | `memory.swap.max` |
| --- | --- | --- |
| `--memory 32m` alone | 67108864, that is **twice** | 33554432 |
| `--memory-swap` equal | 33554432 | **0** |
| `--memory-swap -1` | -1 | `max` |

So a `--memory` set on its own does not leave swap "open": Docker doubles the
value, and the cgroup grants a swap budget **equal to memory**. Unlimited only
comes with `-1`. Only their equality sets `memory.swap.max` to 0.

Worth noting, because it changes what can be concluded: this lab's host has **no
swap at all**. An allocation therefore spills nowhere here, whatever the value,
and it is the deployment contract that requires the equality, not a spill one
could observe on this machine.

This check requires nothing about `OomKillDisable`, and that is measured: on a
cgroup v2 host the kernel cannot disable the OOM killer. Docker discards the
option with a warning and the field does not even hold `false`. A requirement
that cannot be violated checks nothing; what it aimed at is measured by check 3,
which observes a real OOM. A counted OOM **is** the proof that the killer is
active.

## 2. The cgroup actually applies the bound

Inside the container, `memory.max` is 33554432 and `memory.swap.max` is 0.

The previous check reads what was **asked** of the daemon, this one what the
kernel **retained**. A declaration the kernel did not retain bounds nothing, and
it is the cgroup that is authoritative.

## 3. An excessive allocation hits a real OOM

A bounded probe is run inside the container. It must be killed, and above all
`memory.events`'s `oom_kill` counter must **increase**.

A non-zero exit code proves nothing by itself: a command can fail for a thousand
reasons. It is `memory.events` that says the kernel killed the allocation, so
that is what gets read, before and after.

The probe is bounded deliberately. An endless allocator would stress the host,
which the scenario forbids, and would measure the global OOM killer instead of
the cgroup's.

Its size is **measured**, and that is less trivial than it looks: it must be
killed under 32 MiB *and survive* under the starting 96 MiB, or else it declares
the mission accomplished before any work.

The probe doubles a string on every round, so on the last round it holds both
the old and the new one: its peak usage therefore exceeds its stated size. By
how much is a matter of measurement. Read from the cgroup's `memory.peak`, the
ratio of peak to size tends towards **1.53**, not towards 2 as a quick reading
of the doubling suggests. A 32 MiB probe peaks at 49 MiB: above 32, under 96.

## 4. The service survives the OOM and keeps its state

Three things, after an OOM this check triggers itself: the worker is still
running, its `StartedAt` has not changed, and a receipt written **before** the
incident can be read after it.

This is the other half of the requirement, and the easiest to lose. A budget
that takes PID 1 down at every spike does not protect the service, it replaces
it with a restart. Surviving as a process is not enough either: a service that
starts over has lost what it held.

This check triggers **its own** probe rather than reusing check 3's. A check
that assumes another has already run would lie the moment you run it alone, and
that is also why it verifies for itself that an OOM happened: with no incident,
survival cannot be told from nothing having occurred.

## What is not graded, and why we tell you

Three verifications precede the measurements without being requirements: that
exactly one `worker` runs, that it carries its label, and that the host has
enough free memory. Without them no check can observe anything, and a check that
could not look must never conclude green.

The last two do not even depend on you. If the host margin is too small, the
probe risks being killed by the **global** OOM killer rather than the cgroup's:
the check would measure the machine instead of your work. The message then tells
you it is not your fault, and what to free.

Finally, keeping the receipt through the incident says nothing about surviving a
reboot of the machine: that is not what this lab measures.
