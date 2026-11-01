# The registry answers, but Docker does not trust it

On `docker.lab`, `dsoxlab-tls-registry` already stores an image, but serves it
only over HTTP. `registry-tls.lab.test` resolves to the **VM network address**,
port `15443`, not loopback. Docker therefore rejects it until TLS and trust
are configured.

`/opt/lab-registry-tls` contains:

- `config.yml`, mounted at `/etc/docker/registry/config.yml` in the container;
- `certs/server.crt` and `certs/server.key`, mounted under `/certs`;
- `certs/ca.crt`, the private authority that signed the certificate;
- `data/`, the existing storage, which must be retained.

## Mission

- Configure TLS using the supplied certificate and restart the registry.
- Install the CA in Docker's trust directory for `registry-tls.lab.test:15443`.
- Make `docker pull registry-tls.lab.test:15443/catalogue/appli:1.0` succeed.
- Run the image without networking; it prints the prepared release.
- The `/v2/` API must no longer successfully answer over HTTP.
- Verify certificates: neither `insecure-registries`, `curl -k` nor changing
  name resolution to loopback is acceptable.

To inspect the presented chain:

```bash
curl --noproxy '*' --cacert /opt/lab-registry-tls/certs/ca.crt \
  https://registry-tls.lab.test:15443/v2/
```

Docker's directory name includes the port. The Docker engine performs the pull,
not your terminal: giving a CA only to curl is insufficient. This bench is
restricted to the private VM network and its checks require no public registry.
Do not change the product, CA or bench files.
