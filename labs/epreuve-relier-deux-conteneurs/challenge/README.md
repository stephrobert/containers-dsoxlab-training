# Test: connect two containers

Two containers run on this machine. `vitrine` is the page customers see,
`inventaire` is the service that holds the articles.

## What is observed

That is all that is observed, and none of the three findings states the cause.

1. The shop window answers, but it reports that the article is **unreachable**.
2. The inventory answers **from the company network**.
3. The shop window also answers from the company network, although it should
   only be reachable from this machine.

## The five checks

They are of equal weight, and each rests on a verifiable fact.

### 1. The name `stock` resolves from the shop window

And it resolves to an address the inventory **actually carries**. A name that
points elsewhere is worse than a name that does not resolve: the shop window
would be talking to the wrong thing.

### 2. The request traverses the shop window and then the inventory

Measured **from this machine**, on `127.0.0.1:18311`. The answer must carry the
value **only the inventory** holds. Resolving is not reaching, and reaching is
not getting an answer: this check is the only one that proves the whole chain.

### 3. The shop window publishes only on the interface asked for

**One** published port, bound to **`127.0.0.1`** only. An empty or `0.0.0.0`
address means every interface of the host, so the company network as well.

### 4. The inventory publishes no port, and leaves the default network

**This is the critical requirement: no total makes up for it.** A database has
no reason to be reachable from the outside, and on the default network a
container has an address but no name, which is the cause of the first symptom.

### 5. The real name `inventaire` resolves as well

Operations keeps naming the container by its own name, the one in the logs and
the inventories. An additional name **is added**, it does not replace: this
requirement rules out fixing things by renaming.

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
