# One release, two real executions

The release currently has no usable multi-platform index. Work in
`/opt/lab-multiarch` on `docker.lab`; the disposable VM provides Go and QEMU.
Publish `127.0.0.1:15318/workshop/probe:release` with exactly two distinct
Linux variants: AMD64 and ARM64. The supplied program must compute a fresh
integer's square and reject malformed input on both platforms.

A manifest declaring ARM64 does not prove the executable is ARM64. The tests
resolve each manifest from the index, pull by manifest digest and execute each
variant, checking the binary's actual
architecture and result. AMD64 executes natively; ARM64 executes under QEMU
inside this AMD64 VM. This is an emulated runtime attestation, not a native
ARM64 hardware qualification or a performance measurement.

Do not install Docker or QEMU on your workstation. Do not expose the
loopback-only workshop registry or delete objects belonging to other labs.
