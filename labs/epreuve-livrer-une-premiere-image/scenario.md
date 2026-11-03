# Deliver a first image worth publishing

A small application is waiting to be delivered. It lives in
`/opt/lab-premiere-livraison`, with everything its author left there: its code,
its dependency, the credentials file they used to fetch their packages, and the
working directory where they piled up their extracts.

**There is no Dockerfile.** Writing it is your job.

The lab's registry is already running on `127.0.0.1:5000`. It accepts HTTP
because it listens on the loopback interface: there is nothing to configure on
the daemon.

## What is expected at the end

1. The **`premiere-livraison:1.0`** image exists, and
   `docker run --rm premiere-livraison:1.0`, **with no identity option at
   all**, serves the line `inventaire=` followed by the value in the
   `donnees/reference` file.
2. The image **does not run as root**: the user it declares is a **numeric
   non-zero UID**, and the data directory inside the image **belongs to it**,
   without being world-writable.
3. Neither the `.identifiants` file, nor its token, nor the contents of
   `travail/` are present in **any layer** of the image.
4. The image's size stays **under the threshold this lab measured** on this
   machine, by building a reference of its own during `dsoxlab run`.
5. The image is **published** in the lab's registry, and the **digest the
   registry serves** is recorded in
   `/opt/lab-premiere-livraison/digest.txt`, on a single line, in the form
   `sha256:...`.

The full brief is also on the machine, in
`/opt/lab-premiere-livraison/MISSION.md`.

## Two points that matter

**The UID is yours to choose**, as long as it is numeric and non-zero. What is
measured is not the number, it is that it be numeric: a user name only resolves
inside the image that defines it, and an orchestrator does not read its
`/etc/passwd`.

**The size threshold is not an optimisation exercise.** It is generous, and the
gap it measures is the size of what was delivered without any reason to be.

## How you are graded

Six checks of equal weight, and **only the final state counts**. No Dockerfile
instruction is imposed: two ways of obtaining the same image get the same mark.

The pass mark is **75 out of 100**. One requirement is made up for by no total:
**the token present in a layer fails the test**, even with everything else in
place. A secret delivered in an image is a published secret: the image goes into
a registry, others read it, and removing it afterwards takes nothing back.

Four hints are available, and **they cost points**: `dsoxlab hint`.
