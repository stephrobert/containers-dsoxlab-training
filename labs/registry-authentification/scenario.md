# TLS does not make a registry private

On `docker.lab`, `registry-auth.lab.test:15445` already serves verified HTTPS.
Its CA is installed for Docker, but anyone on the private VM network can
download or publish images without credentials. TLS protects transport; it
does not decide who may use the registry.

`/opt/lab-registry-auth` contains:

- `config.yml`, mounted at `/etc/docker/registry/config.yml`;
- `auth/`, mounted at `/auth`, initially empty;
- `certs/`, mounted at `/certs`, with the supplied TLS identity;
- `data/`, the existing image storage;
- `credentials.env`, the generated `publisher` account and password;
- `client/`, a dedicated Docker configuration directory, initially empty;
- `appli/`, the source of the already published `catalogue/appli:1.0`.

## Mission

- Configure the registry's `htpasswd` provider using the supplied credentials.
  Its password file must use bcrypt, supported by this registry.
- Restart `dsoxlab-auth-registry` while preserving TLS and stored images.
- Anonymous API, manifest and upload requests must return `401` with an HTTP
  Basic challenge. Wrong credentials must also return `401`; the supplied
  account must succeed.
- Save a Docker login with `docker --config /opt/lab-registry-auth/client login`.
  Use `--password-stdin`, not a password in a command argument.
- With that client, pull `registry-auth.lab.test:15445/catalogue/appli:1.0`
  and prove that a fresh product can be pushed and pulled.

Use sudo for the protected credential file and host configuration. Do not
alter global Docker credentials, certificates, product source or name resolution.
`insecure-registries` and TLS verification bypasses are not solutions.
The checks exercise real registry operations over verified HTTPS, including
failure of Docker's pull when the private CA is temporarily removed.

The registry's path is inside its container: `/auth/htpasswd`, not the host's
work directory. A successful curl with credentials does not log Docker in.
