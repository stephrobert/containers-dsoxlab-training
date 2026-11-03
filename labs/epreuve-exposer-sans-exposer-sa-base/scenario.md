# The shop window cannot reach its inventory, and the database reaches too far

A small online shop runs on this machine, as two containers. `vitrine` is the
page customers see, `inventaire` is the service that holds the articles. Both
were started by hand, in a hurry, and three things have been reported since.

**The first comes from the customers.** The shop window answers, but it reports
that the article is unreachable. It is not down: it gets nothing from the
inventory.

**The second comes from the internal audit.** The inventory answers from the
company network. A database has no reason to be reachable there.

**The third comes from the same audit.** The shop window also answers from the
company network, although it should only be reachable from this machine: a
reverse proxy will publish it later, and that proxy will carry the front.

**The fourth is the quietest.** The inventory reaches the outside. A database
has no reason to do so, and that is what turns an unauthorised read into a
leak: with no way out, the data stays where it is, even when the service is
compromised.

None of the four findings states the cause. Establishing it is your job.

## What is expected at the end

- the shop window is reachable on port **18311**, **from this machine only**;
- the inventory answers to the name **`stock`**, which is written in the shop
  window's configuration and is not to be changed. It is the name of a
  **service**, not of a container: renaming the inventory will not do;
- the inventory sits on a network **without a way out**, and can no longer
  reach the outside;
- the inventory **publishes no port at all**;
- and the business request **still gets through**, end to end.

Both containers keep their names, `vitrine` and `inventaire`: the checks look
for them by name.

## What you do not have to write

The `lab-relier:1.0` image carries the service, in both of its roles. There is
no code to write and nothing to rebuild: it expects two environment variables,
`ROLE`, which is either `base` or `vitrine`, and `CIBLE`, the name the shop
window queries. The full brief is also on the machine, in
`/opt/lab-relier/MISSION.md`.

No volume and no Compose: that is not this test's subject.

## How you are graded

Five checks of equal weight, and **only the final state counts**. Two ways of
reaching the same state get the same mark: no command is imposed, and the name
you give the network is yours.

The pass mark is **75 out of 100**. One requirement is made up for by no total:
**a port published on the inventory** fails the test, even with everything else
in place. That is the fault the audit reported, and it is the one that exposes a
database to the whole company.

Four hints are available, and **they cost points**: `dsoxlab hint`.
