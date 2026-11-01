# Complete delivery chain

Capstone c4, 120 minutes. Read [the assessment](scenario.md).
Source → multistage BuildKit → actual SPDX inventory → loopback registry →
digest pull → hardened Compose API/PostgreSQL → durable data → eight incidents.

Dependencies and exact pins: [provenance](fixtures/PROVENANCE.md). Debian 13
amd64 VM, Docker/BuildKit, Compose v2 `up --wait`, Python 3, free 15088/18088.
Setup alone needs apt/image network access; builds use a bundled hashed wheel.
Only owned containers, images, networks, volumes and `/opt/lab-delivery`
are removed; shared bases are preserved. Reference is encrypted in
`solution/capstone-chaine-complete/solution.yaml`.
Pre-pull image IDs distinguish newly seeded bases from preexisting ones;
new bases are removed only if unused and unshared, without force or parent pruning.
