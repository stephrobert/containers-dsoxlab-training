# epreuve-durcir-sans-casser: the hardening module's test

## What this test measures

Taking from a service what it does not need, without taking what it does. It
closes the "Harden the runtime" module and re-explains nothing.

Its `lab_type: challenge` is what allows its `exam_passing_score`, set to **75**.
The five checks are of equal weight, and **two** are critical: it is the only
test in the catalogue in that case.

## Two measurements founded this test, and they contradict common advice

**`NET_BIND_SERVICE` is useless in a Docker container.** Measured on 2026-11-02:
a container with NO capability at all listens perfectly well on port 80. The
reason is that the daemon sets `net.ipv4.ip_unprivileged_port_start = 0` inside
the container, which makes every port "unprivileged". The advice "drop everything
except NET_BIND_SERVICE", which you read everywhere, therefore drops nothing
useful and adds nothing.

**The capability that discriminates here is `CHOWN`.** Measured on this lab's
service: without it the service exits 77, with it alone it starts, and
`DAC_OVERRIDE` does not suffice. The service needs it because it adjusts the
ownership of its data directory at startup, which an image commonly does when its
data comes from a volume whose UID does not match.

The test's first design rested on `NET_BIND_SERVICE`. The check would then have
passed without any capability being necessary, and the test would have taught a
falsehood.

## Why the check imposes no capability by name

Because it grades the final state. It measures that the set is **reduced** and
that the service **runs**. A learner who does without `CHOWN` another way, by
preparing the volume's ownership before launching for instance, has hardened
better: demanding the capability's name would punish the better answer.

## The two critical requirements, and why two

**The secret readable in the environment**, and **the firewall disabled**. Both
are open doors. A marking scheme that let an open door be made up for by work done
elsewhere would issue a certificate on a vulnerable installation, which is the
opposite of what this test exists to measure.

The second is the most tempting false fix in the catalogue, and it is perfectly
rational from the point of view of whoever commits it: the flow does not get
through, the firewall blocks, you remove the firewall. The symptom vanishes in one
command.

## The firewall check verifies that the protection ACTS

Reading the rule is not enough. A blocking rule placed **after** an accepting rule
that matches first is still written and no longer does anything: in a chain, order
decides. So the check tries the protected port, in addition to reading the table.

It is the same requirement as everywhere in this catalogue: we measure what acts,
not what is declared.

## What this lab touches on the machine, and what it gives back

It sets up a **dedicated nftables table**, and that is the riskiest move in the
catalogue: a badly scoped rule cuts SSH, and the validator loses its target. Three
precautions, all bench-tested before writing:

- the table is **dedicated to the lab** and targets only two test ports. Port 22
  is never touched;
- cleanup removes it **by name**, never with a `flush`: Docker's rules live in
  other tables, and taking them away would cut the containers' network;
- cleanup **verifies** that the table is gone, and fails saying so otherwise: a
  machine left filtered would break the following labs in silence.

## What the test does not measure

seccomp and AppArmor. Those are subjects in their own right, and measuring them
here would have made a two-hour test.
