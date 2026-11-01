# Measure the effective cgroup controls

Three checks inspect effective memory/process/CPU limits, run a bounded CPU trial
and recreate the worker to reject manual-only limits. Setup explicitly requires
cgroup v2; unsupported hosts fail rather than skip. No OOM or fork exhaustion is induced.
