# Functional contract: docker-contexte-ssh

The Docker client on `docker.lab` must use a named SSH context reaching the real
engine on `docker-client.lab`. Tests compare engine IDs, preserve the selected
default context and require refusal of a readable but unauthorized SSH key.
They reject the prepared starter state. Only dedicated lab identities and
workspaces are changed.
