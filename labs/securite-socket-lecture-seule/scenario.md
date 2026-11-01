# Scenario

An application container mounts /var/run/docker.sock as read-only. The team assumes :ro prevents mutating API calls, which is not a safe assumption.

## Mission

The labelled application container has no mount of the host Docker socket.
