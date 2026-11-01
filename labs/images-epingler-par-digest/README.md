# Pin the dependency of a rebuild

This lab distinguishes recovering an existing image from pinning a `FROM`.
Two local bases have different layers and identities. `stable` has already
moved at setup, and no final image is built.

Three checks prove initial delivery, integration of new source and stable
base layers despite a moved tag. Each first requires a correct delivery so
no points reward the initial state.

The tag mutation really happens in the registry. Builds use `--pull` and
`--no-cache`, and products run without networking: local caching, a fixed
response or a context file impersonating the base cannot pass.
Checks restore the tag and remove their context and images. Cleanup is scoped
to this lab's owner-labeled objects.
