# Local-only verifier image: keep promtool and the project's pinned Python
# dependencies together without installing a host binary.
FROM prom/prometheus:v3.7.3 AS prometheus
FROM insighthub/api:day4-chaos-queue-20260928
COPY --from=prometheus /bin/promtool /usr/local/bin/promtool
WORKDIR /repo
