# Apply budgets that survive replacement

Follow `/opt/MISSION.md` and write `/opt/lab-compose-resources/compose.yaml`.
The three checks read effective cgroup budgets, measure bounded CPU throttling
and verify the limits again after container replacement.
