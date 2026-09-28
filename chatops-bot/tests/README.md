# ChatOps test suite

This directory contains Day 5 implementation tests. It covers raw-body Slack
authentication, app-mention projection, explicit intent routing, and the ACK
boundary around durable enqueue. It contains no placeholder passing tests.

The suite includes the fixed Kubernetes namespace tool, fixed Prometheus
query, structured audit records, and append/read coverage for the audit file.
Approval-bound mutations are intentionally out of scope for the current
read-only intents. Unit doubles do not replace the required live Slack
evidence.
