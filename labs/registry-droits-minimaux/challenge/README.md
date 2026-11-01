# Mission: a publisher is not a reader

Work remotely in `/opt/lab-registry-rights`. The publisher is `docker.lab`,
the separate reader is `docker-client.lab`. Registry HTTPS listens on
`registry-rights.lab.test:15447`; token HTTPS on port `15448`.
TLS is already provisioned. Runtime-only credentials are in
`credentials.json` on the publisher (read with sudo). Never commit them.

1. Correct `auth.yml` so `publisher` can pull and push `catalogue/appli`,
   while `reader` can only pull it. Neither account may write other repositories.
   Keep authentication and signed Bearer authorization enabled.
2. Reload `dsoxlab-registry-droits-minimaux-auth`. Publish an image from the
   supplied pinned Dockerfile and fresh release content. Dedicated Docker
   login directories belong under this lab's path, not in your home config.
3. Retrieve the exact published digest using the reader account on the
   separate VM, initially without that product image. Its image ID and
   network-free output must match the publisher's product.
4. Prove the reader cannot push or open an upload session, including when it
   asks the token server for `pull,push`. Refuse writes to other repositories,
   anonymous access and incorrect passwords.
5. Preserve strict TLS verification on both hosts. A wrong hostname and a
   Docker pull without the private CA must fail. Do not use insecure-registry,
   a loopback HTTP substitute, a host Docker API or publisher cache as proof.

`dsoxlab check registry-droits-minimaux` creates fresh transfer probes and
cleans them in all cases. `dsoxlab clean registry-droits-minimaux` restores
preexisting trust and removes only lab-owned resources on both engines.
