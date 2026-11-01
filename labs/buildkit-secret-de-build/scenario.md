# The product is private, not the secret inside the image

On `docker.lab`, `/opt/lab-buildkit-secret/appli` contains a Dockerfile fetching
a product from a private repository. The repository answers at the VM address,
port `18083`, path `/artifact`, and requires `Authorization: Bearer <secret>`.
The training secret is in `/opt/lab-buildkit-secret/depot.token`, outside the
build context.

The initial Dockerfile passes the secret through `ARG DEPOT_SECRET`. The runtime
environment does not retain it, but image history exposes it. Copying then
deleting it does not solve the problem: earlier layers still ship with the image.

## Mission

Fix the Dockerfile and build `dsoxlab-secret:finale`.

- The container prints only the private product from `/produit.txt`.
- No secret appears in configuration, history or saved layers.
- A new identity supplied through `--secret id=depot,src=...` rebuilds successfully.
- Missing or incorrect secrets fail a build executed without layer caching.

The repository and its state are measurement instruments: do not modify them.
HTTP is restricted here to the isolated lab network; repository TLS is not
this exercise's subject.

You can prepare the builder with:

```bash
docker buildx create --name dsoxlab-secret-work --driver docker-container \
  --driver-opt image=moby/buildkit@sha256:cec9f139f45e93c5c69c60f8b07cfad9f43f4ef6b6a6cd917527fea5ff2e3dea
```

Supply `DEPOT_URL=http://<docker.lab-address>:18083/artifact` as a build argument,
and the credentials file as a BuildKit secret. It is not a `DEPOT_SECRET`
argument, and must not be copied into the context.

Checks read your image, then rebuild a context copy with a fresh product and
identity. They restore the repository after trials. Cleanup removes only this
lab's service, files and named builders.
