# Mission: a usable offline image delivery

Package the published product as `livraison.tar` with its portable SHA-256
receipt. An independent reader must recover and run it after its source
registry stops, without borrowing Docker's cached layers.

The [scenario](../scenario.md) gives the delivery paths and expected tag.
