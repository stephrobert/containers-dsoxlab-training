# Security policy

**Language:** [English](./SECURITY.md) · [Français](./SECURITY.fr.md)

## What this repository holds, and what it does not

A catalogue of teaching labs. No service is exposed, no user data is processed,
and nothing is deployed from here.

**Some labs deliberately lay down a faulty state.** A `fixtures/` directory may
carry a Dockerfile running as root, a secret in an environment variable, an
unpinned image or an over-privileged container: that is the exercise, and it is
what the learner must fix. A security scanner reading this repository will
therefore report **expected** findings.

The distinction is enforced in the tooling, not left to the reader:

| What is checked | What is not |
| --- | --- |
| the `solution/` directories, which set the example | the `fixtures/`, which pose the problem |
| the repository's own scripts | `challenge/work`, the learner's directory |

## Reporting a vulnerability

For a defect that goes beyond the teaching scope, that is, one that would put
someone playing a lab at risk:

- open a [private advisory](https://github.com/stephrobert/containers-dsoxlab-training/security/advisories/new);
- or write to the repository's author.

Please do not open a public issue for that.

In scope: a lab that would execute unverified code, that would leave a door
open on the learner's machine after `clean`, or that would exfiltrate anything.
Out of scope: a deliberately faulty fixture Dockerfile.

## An engine defect is not a catalogue defect

dsoxlab lives in [its own repository](https://github.com/stephrobert/dsoxlab).
A flaw in the CLI is reported there, since the CLI is what executes.

## What the labs do on your machine

Labs with `runtime: shell` talk to **your** Docker engine. They build images
and start containers there, and you should know within which limits:

- every object a test creates carries the `dsoxlab-<lab>-` prefix, so none can
  overwrite an image or a volume of yours;
- every object created is removed at the end, even when the test fails;
- `scripts/valider-labs.py` photographs the engine before and after, and a lab
  that leaves a trace is refused.

Labs that need to modify the **daemon** — `daemon.json`, rootless, seccomp,
AppArmor, firewall — do not run on your own machine: they declare `runtime: vm`
and dsoxlab provisions a dedicated one. That is a design rule, not a
recommendation.
