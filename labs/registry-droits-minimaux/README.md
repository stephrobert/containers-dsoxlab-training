# Minimal registry permissions

**Language:** [English](README.md) · [Français](README.fr.md)

## Authentication and authorization are different

A successful login identifies an account. It does not authorize every
repository action. Distribution can challenge clients with a Bearer realm;
the client authenticates to a token service, requests repository scopes,
then presents the signed token to the registry.

The registry checks the token signature, issuer, audience and permitted
actions. A token service must intersect requested actions with an
administrator-controlled ACL. Basic authentication alone cannot provide
these roles. Here BCrypt protects synthetic account passwords in the token
service, not a role-free htpasswd gate in front of the registry.

## A neutral ACL example

In a disposable training configuration unrelated to this mission:

```yaml
acl:
  - match: {account: packager, name: workshop/widget}
    actions: ["pull", "push"]
  - match: {account: observer, name: workshop/widget}
    actions: ["pull"]
```

In docker_auth, rules are ordered and unmatched requests are denied.
Restrict the repository as well as the account. A publisher needs `pull`
as well as `push`: uploads may first inspect existing blobs.

## Prove a transfer, not a cache hit

Build a product with fresh content, record its image ID and registry digest,
and pull that digest on a separate engine which lacks that image ID.
Run it without networking and compare its output. Then attempt an upload
with the reader account. Test an upload session explicitly too: pushing
existing layers alone may not exercise the complete write boundary.

## Trust and limits

This fixture uses Distribution 2.8.3 and cesanta/docker_auth pinned by digest
(the auth fixture targets Linux amd64). Both endpoints serve real HTTPS on
the private VM address. A two-day synthetic CA is trusted only in Docker's
registry-specific directory; no daemon configuration or host Docker API is
exposed. Tokens expire after 60 seconds. This is a small local static ACL,
not production identity federation, revocation or an internet-facing service.

Only the ACL needs repairing; setup supplies TLS and runtime credentials.
The tests build a new product for every check, use separate login directories,
reject wrong credentials and hostname, and remove the private CA temporarily
to prove Docker cannot bypass it. Cleanup restores preexisting registry trust
and removes only added images and lab-owned paths and containers.

[Mission](scenario.md) · [Requirements](challenge/README.md)
