# Security policy

**Language:** [English](./SECURITY.md) · [Français](./SECURITY.fr.md)

## Supported versions

`containers-dsoxlab-training` is under active development. Security fixes are
applied to the latest version of the `main` branch.

| Version | Supported |
| --- | --- |
| latest (`main`) | yes |
| older | no |

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

Please include:

- a description of the vulnerability and its impact,
- the steps to reproduce it (command, environment, `docker version`,
  `dsoxlab --version`),
- any relevant logs or proof of concept.

We will keep you posted on the fix and credit you in the release notes if you
wish.

## Disclosure policy

We practise coordinated disclosure and commit to the following timelines,
counted from the moment we receive your report:

| Step | Target |
| --- | --- |
| Acknowledging your report | within **48 hours** |
| Initial assessment and severity triage | within **5 days** |
| Fix released, or a written remediation plan | within **30 days** |
| Public disclosure of the vulnerability | within **90 days** |

We publish the advisory as soon as a fix is available, or at the **90-day** mark
at the latest, whichever comes first. If a vulnerability is being actively
exploited, we may disclose sooner to protect users. If a complex fix needs more
time, we tell you before the deadline and agree a new date with you, rather than
letting it lapse in silence.

## Scope

This repository ships **lab content**: a `lab.yaml` contract per lab, Ansible
playbooks that lay down and tear down the starting state, pytest tests that
read the state of a Docker engine, and encrypted reference solutions, all run
by the external `dsoxlab` CLI.

Labs that modify the **daemon** run on a throwaway virtual machine that
`dsoxlab provision` creates. The others talk to a Docker engine, and that is
where the real reach of this repository lies: a test builds images and starts
containers.

Because some lab material is deliberately faulty, CodeQL does not analyse
`labs/**/fixtures/**` or `solution/**`: see
[`.github/codeql/config.yml`](.github/codeql/config.yml), which explains the
reasoning. An alert that must never be fixed is not an alert: it is noise, and
noise hides. What the repository ships as its own tooling, that is the
workflows, the validation scripts, `conftest.py` and the pytest tests, stays
fully analysed, and that is exactly the scope listed below.

In scope:

- a lab that would execute unverified code, that would leave a door open on
  the learner's machine after `clean`, or that would exfiltrate anything;
- a container escape made possible by what a lab asks the learner to run,
  beyond what the lab teaches;
- a real secret, a private key or an API token committed by mistake;
- a reference solution shipped in clear, which spoils the lab and stays in the
  history;
- an image referenced without pinning by digest in what the repository ships
  as a reference.

Out of scope:

- vulnerabilities of the `dsoxlab` engine itself, which belong to
  [its own repository](https://github.com/stephrobert/dsoxlab);
- those of Docker, of a base image or of any third-party tool, to be reported
  to their respective projects;
- a deliberately faulty fixture Dockerfile, an over-privileged container or an
  unpinned image when it is the subject of the exercise;
- a lab that fails or scores wrongly: that is a defect, opened as a public
  issue.

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

Labs that need to modify the **daemon** (`daemon.json`, rootless, seccomp,
AppArmor, firewall) do not run on your own machine: they declare `runtime: vm`
and dsoxlab provisions a dedicated one. That is a design rule, not a
recommendation.
