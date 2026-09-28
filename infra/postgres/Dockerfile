# Docker Desktop local-lab wrapper. Build a single amd64 image from the
# PostgreSQL base because this local Kubernetes runtime cannot execute the
# upstream pgvector multi-architecture manifest.
FROM postgres:16.14-bookworm AS build
ARG PGVECTOR_VERSION=v0.8.2
RUN apt-get update \
    && apt-get install --no-install-recommends --yes ca-certificates curl git gnupg make gcc \
    && install -d -m 0755 /etc/apt/keyrings \
    && curl --fail --silent --show-error https://www.postgresql.org/media/keys/ACCC4CF8.asc \
      | gpg --dearmor -o /etc/apt/keyrings/postgresql.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/postgresql.gpg] http://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" \
      > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install --no-install-recommends --yes postgresql-server-dev-16 \
    && git clone --depth 1 --branch "$PGVECTOR_VERSION" https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && make -C /tmp/pgvector \
    && make -C /tmp/pgvector install

FROM postgres:16.14-bookworm
COPY --from=build /usr/lib/postgresql/16/lib/vector.so /usr/lib/postgresql/16/lib/vector.so
COPY --from=build /usr/share/postgresql/16/extension/vector--*.sql /usr/share/postgresql/16/extension/
COPY --from=build /usr/share/postgresql/16/extension/vector.control /usr/share/postgresql/16/extension/vector.control
