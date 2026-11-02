# Scenario

Your team delivers an image to a partner. They do not have your repository, nor
your cache, nor the right to write to your registry: they have a machine, your
authority's trust, and a read-only account.

The last delivery went wrong in two ways at once. The image would not start on
their side, because it depended on a file that existed only on the build
machine. And an auditor found the build token in a layer, by reading the image's
history: there was nothing to decode, it was written there.

You are asked to redo the delivery, and to make it verifiable.

## Mission

Build the image without the build secret surviving in a layer, publish it,
record its digest reference, and run it on the bare client by that digest.

This is a **challenge**: the pass mark is 75%. What is expected in detail is in
`/opt/lab-livraison/MISSION.md`.
