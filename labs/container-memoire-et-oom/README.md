# Memory and container-local OOM

`mem_limit` caps RAM. Docker's `MemorySwap` is the combined RAM-plus-swap
budget, not swap alone. Setting `memswap_limit` equal to `mem_limit` disables
container swap when the kernel supports accounting.

For a neutral project `demo-parser`, compare `HostConfig.Memory` and
`MemorySwap` with `memory.max` and `memory.swap.max` on cgroup v2.
An equal combined budget translates to a swap maximum of zero.
Memory includes anonymous allocations, charged page cache and tmpfs pages.

Exit 137 alone does not prove OOM; SIGKILL has other causes. An increased
`oom_kill` counter in `memory.events` proves the cgroup saw an OOM kill.
An exec probe can die without Docker marking PID 1 as `OOMKilled`.

This exercise doubles one awk string at most 26 times, only inside a verified
32 MiB cgroup, with a ten-second deadline and a host-memory guard. No host OOM
is intended. Cgroup v2 and memory/swap accounting are prerequisites.
See [the challenge](challenge/README.md).
