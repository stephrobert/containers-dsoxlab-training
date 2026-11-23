# Harden a service without breaking it

The `service-expose` service runs with every right Docker grants by default. Its
secret is readable in its environment. Its root filesystem is writable. And since
a firewall update, it no longer reaches the `fournisseur-tiers` provider.

You are asked to harden it. Without breaking it.

## What is expected at the end

1. The service has lost **all its capabilities except the one it needs**, it
   carries **`no-new-privileges`**, and it still **answers**.
2. Its root is **read-only**, its writes go through a declared path, tmpfs or
   volume, and a write anywhere else is **refused**.
3. The secret appears **neither in the container's environment** nor **in the
   image**, and the service receives it all the same: its answer must stay
   correct. The `/opt/lab-durcir/jeton` file is provided.
4. The flow to the provider **gets through**, on `127.0.0.1:19443`, the firewall
   stays **active**, and its **protection rule** stays in place.
5. The `dsoxlab-durcir-donnees` volume is mounted back and **its value is
   served**; both `dsoxlab-durcir-jetable-1` and `dsoxlab-durcir-jetable-2`
   volumes are removed.

The full brief is also on the machine, in `/opt/lab-durcir/MISSION.md`.

## Two facts measured on this engine

They are given so that you do not look in the wrong place.

**`NET_BIND_SERVICE` is useless here.** A container with **no capability at all**
listens perfectly well on port 80, because the daemon sets
`net.ipv4.ip_unprivileged_port_start = 0` inside the container: every port there
is "unprivileged". The widespread advice "drop everything except
NET_BIND_SERVICE" therefore drops nothing useful and adds nothing. The capability
you need is elsewhere, and **the service's logs say which move fails when it is
missing**.

**The firewall can be fixed without being disabled**, and without its table being
deleted. In a chain, a rule that accepts can take precedence over one that
blocks, depending on their **order**.

## What you do not have to write

The `lab-durcir:1.0` image is provided: there is **nothing to rebuild**. The
service reads its secret from a **file** before looking at its environment, and
the path is set by `SECRET_FICHIER`, whose default is `/run/secrets/jeton`. Its
working directory is set by `TRAVAIL`, whose default is `/travail`.

seccomp and AppArmor are not measured by this test.

## How you are graded

Five checks of equal weight, and **only the final state counts**.

The pass mark is **75 out of 100**, and this test carries **two** requirements
that nothing makes up for:

- **the secret readable in the environment**;
- **the firewall disabled**, or its table deleted, or its protection rule
  removed.

Both are open doors, and an open door is not made up for by work done elsewhere.
The second is the most tempting false fix in the whole test: the flow does not
get through, the firewall blocks, so you remove the firewall. The symptom vanishes
in one command, and the machine is bare.

Four hints are available, and **they cost points**: `dsoxlab hint`.

## Test: harden without breaking

The service runs with every default right, its secret is in its environment, its
root is writable, and it no longer reaches its provider.

### The five checks

They are of equal weight, and each rests on a verifiable fact.

#### 1. The rights dropped, and the service still answering

**Three facts**: the capability set is reduced, `no-new-privileges` is set, and
the service answers. The third tells this test apart from an exercise in
deletion: dropping everything is easy, and the service dies.

The check **imposes no capability by name**. It measures that the set is reduced
and that the service runs: a learner who finds another way to do without the
capability has hardened better, and the test must not punish them.

#### 2. The read-only root, and the declared writes

Two facts that only make sense together: a read-only root with no declared
writable path gives a service that dies, and a declared path without a read-only
root protects nothing.

The check measures them **by doing**: a write outside the declared paths must be
refused. Reading `ReadonlyRootfs` would not be enough, because the flag says the
intention and the attempt says the result.

#### 3. The secret out of the environment, and yet delivered

**First critical requirement.** Two sides: the secret is gone from the
environment and the image, **and** the service receives it. Removing a variable
without replacing it gives a clean, wrong service, and the check compares the
value served with the one it expects.

#### 4. The flow restored, the firewall intact

**Second critical requirement**, and the most tempting false fix in the test:
removing the firewall makes the symptom vanish in one command and leaves the
machine bare.

Three facts measured together: the flow gets through, the table still exists, and
the protection **still protects**. The third is the subtlest: a fix that flushes
the chain lifts the block **and** the protection, which looks like a job done. So
the check does not merely read the rule, it verifies that it acts.

#### 5. The useful volume served, the disposable ones removed

Hardening goes through recreating the container, and that is where a volume gets
forgotten. Three volumes carry the lab's name: only one counts, and the brief
says which.

The check reads **the value served**, not the volume's mere existence: a volume
remounted empty carries the right name and is worth nothing.

### The marking

Five checks of equal weight, pass mark **75 out of 100**, and **two** critical
requirements.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
