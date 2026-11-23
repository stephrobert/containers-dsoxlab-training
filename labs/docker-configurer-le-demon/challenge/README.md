# Scenario

New containers have no log retention limit. Set the default driver to json-file, cap files at 1 MiB and retain two files. Existing daemon settings may not be discarded.

## Mission

Newly created containers use the requested defaults; cleanup restores the original daemon configuration.

## Functional contract: docker-configurer-le-demon

Tests inspect effective state on the remote `docker.lab` host. They reject the prepared starter state and pass only when the mission is satisfied. Test-created resources are bounded and carry this lab’s unique label.
