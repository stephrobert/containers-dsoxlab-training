# reseau-bridge-par-defaut: the network nobody chooses

## What this lab tests

That the default network connects containers to each other and to the host, and
that it gives them **no name resolution**. It is the network you land on when
you say nothing, and its limits are only discovered by hitting them.

## The lesson was measured before it was written

On `docker.lab`, on 2026-10-30, from a container of the default network:

| Attempt | Result |
| --- | --- |
| connection to `arriere`'s **address** | its token |
| connection to its **name** | `nc: bad address 'arriere'` |
| `nslookup arriere` | times out, no server reachable |

The next lab, `reseau-bridge-dedie`, creates a network and recovers DNS. **The
contrast is the teaching**: claiming that a dedicated network "brings DNS" is
worth nothing until you have seen the other one do without it.

## Why `nc` and not `ping`

ICMP depends on the container's capabilities and on host kernel settings. A
networking lab failing for that reason would teach the wrong lesson: the
learner would conclude that the network does not work, when only ICMP is
filtered. A TCP connection proves the same reachability and depends on nothing
else.

## Why the token is not in the logs

A first version had `arriere` announce it on its standard output. `docker logs`
then handed it over **without a single packet crossing the network**, and the
lab could be solved without touching its subject.

So it lives only in the TCP answer, and a fresh one is drawn on every pass.
Finding it presupposes having opened a connection.

## An honest word about the fourth check

The host also reaches the default bridge directly: the token can therefore be
obtained from the host rather than from `avant`.

This is not a flaw in the lab, it is a **fact about the default network**, which
the scenario states, and it is even a useful security point. So the check grades
the state reached, `avant` carries the token, and not the path taken, which is
the repository's rule.

## The three questions, and what each one builds

| Answer | Where it is read | What it teaches |
| --- | --- | --- |
| `adresse` | inspecting the **container** | on this network it is the only way to name a neighbour |
| `passerelle` | inspecting the **network** | a container knows its address, the network knows its gateway |
| `interface` | the host, through `ip addr` | the gateway is carried by a real interface |

The second and the third are the ones usually skipped, and they are the ones
that turn container networking into something concrete.

## Why the interface is looked up by address, not by name

The default network's bridge is called `docker0` on an ordinary installation,
and the engine even names it in the network's options. But that name is
**configurable**: a check expecting a hardcoded `docker0` would be wrong on a
machine set up differently.

So the test looks for which host interface carries the gateway's address. Same
reason on the subnet side: no address is written into the tests, because
`172.17.0.0/16` depends on the machine.

## The starting state is broken, and that is the repository's rule

| Laid down by the setup | Starting state | Expected move | Check |
| --- | --- | --- | --- |
| `reponses.txt` | three keys, three **empty** values | fill them in | 1, 2 and 3 |
| the token, in `arriere`'s process | `avant` does not carry it | open a connection | 4 |

A setup task **verifies** that state before handing over: both containers are
running, and `avant` does not already carry a previous pass's token.

## What the lab does not require

A path. The address can be read from the container's inspection as well as from
the network's full output; the interface through `ip addr` as well as through
the options the engine declares; the connection through `nc` as well as `wget`
or any other client.
