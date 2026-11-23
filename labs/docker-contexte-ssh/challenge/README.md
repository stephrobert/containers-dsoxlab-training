# Scenario

Operations needs a named context for the staging engine on the distinct VM
`docker-client.lab`. A dedicated SSH identity is prepared on `docker.lab`;
the alias `dsoxlab-ssh-target` names the remote VM. Leave the default context unchanged.

## Mission

The named context reaches the real second-VM daemon over SSH; the default
context remains selected. A separate unauthorized key must fail authentication
against that same reachable SSH service. No unauthenticated Docker TCP API is needed.

## Functional contract: docker-contexte-ssh

The Docker client on `docker.lab` must use a named SSH context reaching the real
engine on `docker-client.lab`. Tests compare engine IDs, preserve the selected
default context and require refusal of a readable but unauthorized SSH key.
They reject the prepared starter state. Only dedicated lab identities and
workspaces are changed.
