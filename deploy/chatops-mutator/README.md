# Day 5 approved scale mutator (local only)

This is the separately identified Tier 2 mutation backend. It is not exposed
through ngrok or an Ingress. Its Kubernetes `Role` can only `get` and `patch`
`deployments/scale` for `insighthub-api` in namespace `insighthub`.

## Prerequisites

Generate one new local shared secret. Do not reuse a Slack secret and do not
place the value in Git, an evidence file, Slack, or a terminal screenshot.
Put it in the ignored repository-root `.env` as:

```dotenv
CHATOPS_MUTATION_SIGNING_SECRET=<new-random-value>
CHATOPS_MUTATOR_URL=http://host.docker.internal:18083/v1/actions/scale-api
```

Create the matching local Kubernetes Secret without echoing its value in the
terminal. Replace the placeholder through your shell's secure input method:

```powershell
kubectl -n insighthub create secret generic chatops-mutator-auth --from-literal=shared-secret='<new-random-value>'
```

## Build and deploy

The local `docker-desktop` cluster already has the InsightHub API image. The
manifest reuses that image and mounts the mutator module from a local ConfigMap,
so no registry push or image import is needed. Generate/update that ConfigMap,
then apply the manifest:

```powershell
kubectl -n insighthub create configmap chatops-mutator-code --from-file=mutator.py=chatops-bot/app/mutator.py --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f deploy/chatops-mutator/mutator.yaml
kubectl -n insighthub rollout status deployment/chatops-mutator
kubectl -n insighthub port-forward svc/chatops-mutator 18083:8080
docker compose --profile chatops up --build -d --wait chatops-worker
```

The final command recreates the worker so it receives the local mutator
configuration. Keep the port-forward terminal open during the test.

## Live, bounded test and recovery

1. In `#insighthub-ops`, send `@InsightHub scale api to 2`.
2. The bot returns an opaque token; as the same Slack user, send exactly
   `@InsightHub confirm TOKEN` within 60 seconds.
3. Verify `kubectl -n insighthub get deployment insighthub-api` reports two
   desired replicas and read the audit file.
4. Restore the prior desired replica count with a new approval, for example
   `@InsightHub scale api to 1`, then its new confirmation token.

Do not retry a consumed token. If the mutator is unavailable, the consumed
approval does not cause a retry; request a new approval after diagnosing the
backend. This protects against replay or a delayed write.
