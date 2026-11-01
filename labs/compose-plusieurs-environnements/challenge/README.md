# Operate two environments without cross-talk

Follow `/opt/MISSION.md`. Keep the base declaration and write dev/prod overrides.
Checks inspect both running deployments and verify that replacing either one
preserves its data without touching the other.
