# Contract 31: correlated business load and real saturation

[Français](README.fr.md)

1. Configure the supplied stack, project `dsoxlab-compose-correlation-et-saturation-stack`,
   in `/opt/dsoxlab-compose-correlation-et-saturation`. No application coding.
2. Preserve each fresh `X-Request-ID` in both component JSON traces and the
   response. A quantity from 1 to 20 returns `quantity` and `total_cents`
   at 125 cents per item. Reject invalid quantities with HTTP 400.
3. Run both components with hard CPU quotas: gateway one CPU, worker quarter
   CPU. Read effective cgroup v2 `cpu.max` and `cpu.stat`.
4. Bound load to 16 requests, concurrency four. Record per-component usage,
   throttled-period and throttled-time deltas. Worker deltas must show actual
   throttling, at least 100000 usage microseconds per request and more than
   twice gateway usage. Identify the worker, not merely a large log.
5. Neither component logs Authorization or a fresh synthetic secret witness.
   Retain only component, event, request_id and business quantity/total fields.
   A representative variant with quota and correlation repaired but unsafe
   worker logging must be refused. The functional probe creates and removes
   this isolated variant, without printing raw logs or secrets.
6. Keep supplied image, labels and private cgroup namespaces, no added
   capabilities or privileged containers. Recreate from your Compose declaration.

Verdict: zero initially, full after correction, measured twice on `docker.lab` on 2026-11-01.
Human explanation is separate in [review.md](review.md). Thresholds are bounded
test conditions, not training percentages or an acceptance claim.
