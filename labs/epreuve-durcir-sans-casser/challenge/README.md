# Test: harden without breaking

The service runs with every default right, its secret is in its environment, its
root is writable, and it no longer reaches its provider.

## The five checks

They are of equal weight, and each rests on a verifiable fact.

### 1. The rights dropped, and the service still answering

**Three facts**: the capability set is reduced, `no-new-privileges` is set, and
the service answers. The third tells this test apart from an exercise in
deletion: dropping everything is easy, and the service dies.

The check **imposes no capability by name**. It measures that the set is reduced
and that the service runs: a learner who finds another way to do without the
capability has hardened better, and the test must not punish them.

### 2. The read-only root, and the declared writes

Two facts that only make sense together: a read-only root with no declared
writable path gives a service that dies, and a declared path without a read-only
root protects nothing.

The check measures them **by doing**: a write outside the declared paths must be
refused. Reading `ReadonlyRootfs` would not be enough, because the flag says the
intention and the attempt says the result.

### 3. The secret out of the environment, and yet delivered

**First critical requirement.** Two sides: the secret is gone from the
environment and the image, **and** the service receives it. Removing a variable
without replacing it gives a clean, wrong service, and the check compares the
value served with the one it expects.

### 4. The flow restored, the firewall intact

**Second critical requirement**, and the most tempting false fix in the test:
removing the firewall makes the symptom vanish in one command and leaves the
machine bare.

Three facts measured together: the flow gets through, the table still exists, and
the protection **still protects**. The third is the subtlest: a fix that flushes
the chain lifts the block **and** the protection, which looks like a job done. So
the check does not merely read the rule, it verifies that it acts.

### 5. The useful volume served, the disposable ones removed

Hardening goes through recreating the container, and that is where a volume gets
forgotten. Three volumes carry the lab's name: only one counts, and the brief
says which.

The check reads **the value served**, not the volume's mere existence: a volume
remounted empty carries the right name and is worth nothing.

## The marking

Five checks of equal weight, pass mark **75 out of 100**, and **two** critical
requirements.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
