# Day 4 MLOps overview notes

## 1. Artifact and registry

An ML artifact is the versioned unit that is approved for use: model identifier, embedding identity, prompt/template, evaluation dataset, thresholds and the container image digest that serves it. A registry records those immutable versions, provenance, owner and evaluation results. For InsightHub, changing provider, model, dimension, revision or preprocessing changes the vector space and requires an explicit migration/re-index decision rather than a silent rollout.

## 2. Approval gate

Promotion should be a human-approved gate after reproducible tests: security and policy checks, regression/evaluation results, cost budget and rollout plan. The approver accepts a specific artifact version and evidence, not the word “latest”. A production change must be traceable to its source revision, image digest, approver and change window.

## 3. Drift detection

Drift means a material change in inputs, retrieval quality, model behavior or operational performance compared with the approved baseline. Operational signals here include request error rate, RAG/LLM latency, token use/cost and queue depth; quality signals require a labelled evaluation set and retrieval or answer-quality measurements. An alert is an investigation trigger, not by itself proof that the model changed.

## 4. Rollback and ownership

Rollback returns to the previously approved image/configuration and verifies health, metrics and data compatibility. Do not roll back an embedding change without considering index/vector-space compatibility. DevOps owns safe deployment, observability, infrastructure and rollback execution; ML owns model/prompt/evaluation quality and approval criteria. Both share incident review, cost controls and the decision to promote or halt a model change.
