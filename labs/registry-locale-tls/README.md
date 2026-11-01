# Presented TLS, installed trust, verified pull

The registry starts over HTTP with a published product. Setup generates its
CA and certificate; no private identity is committed.

The hostname resolves to the VM network address: Docker implicitly considers
loopback insecure, so it could not prove this lab's requirement.
Checks verify HTTPS using the CA, rejection of a wrong hostname, absence of a
successful HTTP response, a real pull and its product. They also inspect
`RegistryConfig.IndexConfigs` to reject explicit insecure entries. Crucially,
they temporarily remove the registry-specific CA and require the pull to fail
with an X.509 error, then restore the CA. This also detects insecure CIDR
exceptions or resolution to loopback. Ordinary secure registries need not
appear in `IndexConfigs`: an absent entry alone cannot prove trust.

Every check first requires HTTPS, so none rewards the initial state.
Cleanup removes only this registry, its labeled images, hostname entry and
trust directory without restarting the Docker daemon.
