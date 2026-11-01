# Scenario

A demonstration container emits a bounded stream but allows an oversized log file. Do not change daemon-wide defaults; only this service is in scope.

## Mission

The service uses json-file logs capped at 1 KiB with three retained files.
