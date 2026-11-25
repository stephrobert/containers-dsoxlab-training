# A context for staging

## The situation

Operations wants to drive the staging engine from `docker.lab`. That engine runs
on another VM, `docker-client.lab`. SSH access is ready: the remote account
exists, a dedicated key is in place, and the SSH alias `dsoxlab-ssh-target` leads
to the second VM with that key.

## Mission

On `docker.lab`, under your account:

- create a Docker context named `dsoxlab-maintenance`, whose address goes through
  the SSH alias `dsoxlab-ssh-target`;
- this context answers, and it is the engine of `docker-client.lab` that answers;
- the context selected at the start stays selected.

Do not open a Docker API over TCP, and authorise no other key on the second VM:
the one in `/opt/dsoxlab-docker-contexte-ssh/unauthorized` must stay refused.

## What is graded

1. The `dsoxlab-maintenance` context targets the SSH alias.
2. It returns the identity of the second VM's engine, different from the local
   engine's, and the unauthorised key is refused by the SSH service.

Changing the selected context makes both checks fail.
