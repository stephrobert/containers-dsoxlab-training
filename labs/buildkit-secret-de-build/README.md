# A secret during the build, never inside its result

This challenge fetches a real product from a local private repository.
Setup generates the identity and the repository rejects incorrect credentials.

Checks read the product and inspect configuration, untruncated history and
every layer in `docker save`, including deleted files. They rebuild with a
fresh identity and product, then require missing and wrong secrets to fail,
with layer caching disabled. A fixed response or hardcoded identity cannot pass.

The HTTP repository serves only the isolated VM network; its TLS is not
measured. Trials restore its state and remove their own builder.
The supplied secret is purely educational and is never committed.

Measured on this bench on 2026-11-01: passing through `ARG` fails metadata
inspection; `COPY` then `rm` fails archive inspection; the secret mount leaves
no detected occurrence. The runtime cycle gives 0/3 before, 3/3 after, then
0/3 after resetting.
