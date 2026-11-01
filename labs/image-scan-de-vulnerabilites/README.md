# Real offline image vulnerability scans

Guided c4 lab, 45 minutes. Read [the mission](scenario.md) and
[fixture provenance](fixtures/PROVENANCE.md). Real debsecan output from actual
Debian packages, not invented CVEs or predictions about mutable public images.

Requires amd64 Debian 13 VM, Docker, dpkg, `/usr/bin/python3`, python3-apt and
debsecan (apt at setup). Database and packages are versioned; builds and scans
are offline. Only owned images/extraction containers and `/opt/lab-image-scan`
are cleaned. No vulnerable service runs. The gate covers CVE-2023-0286, not a
universal “zero vulnerabilities” claim. Reference: encrypted
`solution/image-scan-de-vulnerabilites/solution.yaml`.
