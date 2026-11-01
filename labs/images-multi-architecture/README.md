# An image index is not an execution result

A multi-platform image index associates a platform with a manifest digest.
Each manifest points to a configuration and layers. Changing the platform
metadata cannot translate the instructions of an executable.

There are three different operations: cross-compiling a program, assembling
its image, and executing that image. For example, Go's `GOOS` and `GOARCH`
choose its output platform; `CGO_ENABLED=0` can produce a standalone Linux
binary for a scratch image. Docker's `--platform` selects image metadata and,
when pulling an index, the appropriate manifest.

On a Linux AMD64 VM, an ARM64 executable needs an interpreter such as QEMU
registered through binfmt, or native ARM64 hardware. The interpreter must live
inside the lab VM, not the learner's workstation. Successful execution under
emulation establishes functional behavior for that environment only.

An acceptable proof includes the index digest, both manifests, real positive
and negative runtime checks, and an explicit native/emulated distinction.
