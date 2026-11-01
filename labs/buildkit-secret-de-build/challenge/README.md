# Mission: fetch without leaking

On `docker.lab`, fix `/opt/lab-buildkit-secret/appli/Dockerfile` and build
`dsoxlab-secret:finale`. Fetch the private product using an ephemeral BuildKit
secret, not a build argument or a copied credential.

The [scenario](../scenario.md) gives the repository address and acceptance criteria.
