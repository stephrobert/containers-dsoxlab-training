# A scan is dated evidence

## The situation

On `docker.lab`, `/opt/lab-image-scan` contains two images of Debian libraries:
`legacy` carries OpenSSL 1.1.1n, `fixed` carries OpenSSL 3.0.17. They are specimens
without their dependencies: **never run them** and do not publish them. Their
sources and checksums are in `fixtures/PROVENANCE.md`.

The scan is offline, with **debsecan**, on a Debian database frozen at
2026-11-01 11:37:02 UTC. It reads the Debian package inventory, not all
dependencies nor all files. The machine must be amd64.

## Mission

1. Run `python3 scan.py dsoxlab-scan:legacy legacy-report.json`. Use
   `/usr/bin/python3` if your interpreter lacks system packages. It extracts
   the actual image inventory without starting a container, invokes **debsecan**
   against the offline database and returns 1 for policy rejection.
2. Read the complete findings. The narrowly scoped promotion policy rejects
   **CVE-2023-0286**, the real OpenSSL X.400 type-confusion advisory; it does
   not claim that the corrected image has no other vulnerabilities.
3. Promote the supplied `fixed` image to `dsoxlab-scan:candidate`, scan it to
   `candidate-report.json`, retaining all findings and provenance fields.
4. Create executable `gate.sh IMAGE REPORT` that runs a fresh supplied scan,
   preserves its JSON evidence and returns its status. Prove rejection of
   legacy and acceptance of fixed. Do not filter, edit or fake scanner output.

At the start, there is no valid report, no candidate and no gate. The three checks
run the scan again and compare your evidence: findings, image identifiers,
fingerprints of the inventory and of the database. Evidence expires after 24 hours.
