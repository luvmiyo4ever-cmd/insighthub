# Kubernetes MCP Evidence

## Connection details

- Server: `kubernetes`
- Configured package: `kubernetes-mcp-server@0.0.66` (from the MCP configuration shared earlier)
- Transport: `stdio`
- Kubeconfig: `C:\Users\thang\.kube\config` (configured path)
- Runtime context: `docker-desktop` (verified 2026-09-22T13:59:20Z)
- MCP call timestamp / Codex version: not captured
- Cluster node `desktop-control-plane` matches the earlier MCP pod-list output.

## Successful read-only tool call

- Tool: `pods_list`
- Input: `{}` (lists pods across all namespaces)
- Result: call succeeded; 9 pods returned, all `Running` and `READY 1/1`.

Output reported by MCP:

```text
NAMESPACE            NAME                                             READY   STATUS
kube-system          coredns-589f44dc88-blvx9                         1/1     Running
kube-system          coredns-589f44dc88-wjx77                         1/1     Running
kube-system          etcd-desktop-control-plane                       1/1     Running
kube-system          kindnet-cq74l                                    1/1     Running
kube-system          kube-apiserver-desktop-control-plane             1/1     Running
kube-system          kube-controller-manager-desktop-control-plane    1/1     Running
kube-system          kube-proxy-tdrtk                                 1/1     Running
kube-system          kube-scheduler-desktop-control-plane             1/1     Running
local-path-storage   local-path-provisioner-855c7b7774-gpwr6          1/1     Running
```

## RBAC verification

RBAC checks run against context `docker-desktop` at `2026-09-22T13:59:20Z`:

```text
kubectl auth can-i get pods --as=system:serviceaccount:insighthub:mcp-readonly
yes

kubectl auth can-i delete pods --as=system:serviceaccount:insighthub:mcp-readonly
no

kubectl auth can-i list pods --as=system:serviceaccount:insighthub:mcp-readonly --all-namespaces
yes
```

The live cluster also contains ServiceAccount `insighthub/mcp-readonly`, ClusterRole `mcp-readonly`, and ClusterRoleBinding `mcp-readonly`. The ClusterRole grants only `get`, `list`, and `watch` on its declared resources; it does not grant write verbs.

- Inspector screenshot: not captured
