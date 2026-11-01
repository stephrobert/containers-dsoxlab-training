# Mission: reuse dependencies across source changes

Work on `docker.lab` in `/opt/lab-buildkit-cache`.
Keep the build tool unchanged and fix the Dockerfile so a cold build works,
a changed source reuses the dependency, and the runtime image contains no cache.

Read the [scenario](../scenario.md) for the bench, commands and acceptance criteria.
