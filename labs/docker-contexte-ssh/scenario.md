# Scenario

Operations needs a named context for the staging engine on the distinct VM
`docker-client.lab`. A dedicated SSH identity is prepared on `docker.lab`;
the alias `dsoxlab-ssh-target` names the remote VM. Leave the default context unchanged.

## Mission

The named context reaches the real second-VM daemon over SSH; the default
context remains selected. A separate unauthorized key must fail authentication
against that same reachable SSH service. No unauthenticated Docker TCP API is needed.
