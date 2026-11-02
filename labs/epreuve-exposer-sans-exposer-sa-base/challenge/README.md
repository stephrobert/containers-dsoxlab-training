# Expose an application without exposing its database

Two containers run on this machine. `vitrine` is the page customers see,
`inventaire` is the service that holds the articles.

## What is observed

That is all that is observed, and none of the four findings states the cause.

1. The shop window answers, but it reports that the article is **unreachable**.
2. The inventory answers **from the company network**.
3. The shop window also answers from the company network, although it should
   only be reachable from this machine.
4. The inventory **reaches the outside**. A database has no reason to do so,
   and that is what turns an unauthorised read into a leak.

## The five checks

They are of equal weight, and each rests on a verifiable fact.

### 1. The shop window publishes only on the interface asked for

**One** published port, bound to **`127.0.0.1`** only. An empty or `0.0.0.0`
address means every interface of the host, so the company network as well.

### 2. The inventory answers to `stock`, which is not its name

`stock` is written in the shop window's configuration and **does not change**.
This check does not look at resolution alone: it reads the **declared service
name**. A container renamed to `stock` would resolve too, and would tie the
shop window to one container instead of a service.

### 3. The inventory sits on a network **without a way out**

Two facts, and the second is the one that proves. Every network the inventory
is attached to is declared **internal**, and above all the inventory has **no
default route**, which is read inside the container. The declaration is an
intention; the missing route is the effect.

### 4. The inventory publishes no port

**This is the critical requirement: no total makes up for it.** A database has
no reason to be reachable from the outside: its shop window reaches it through
the container network. Nothing removes a published port from a container that
already exists, which is information in itself.

### 5. The business request gets through **despite** the isolation

Measured **from this machine**, on `127.0.0.1:18311`. The answer must carry the
value **only the inventory** holds.

This check is why the test exists: isolating the database cuts it off from
everything, publishing the shop window demands a way out, and both must hold
together. Each requirement is easy on its own.

## What is provided

The `lab-relier:1.0` image carries the service in both of its roles. Nothing to
write, nothing to rebuild. It expects two environment variables:

- `ROLE`, either `base` or `vitrine`;
- `CIBLE`, the name the shop window queries, namely `stock`.

Both containers keep their names: the checks look for them by name.

No volume and no Compose: that is not the subject.

## The marking

Five checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**: two ways of reaching the same state get the same mark. The name
you give the network is yours.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
