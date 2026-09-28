# InsightHub Day 6 threat model

This file records the intended security boundary. Runtime scan results are
evidence only when the corresponding Promptfoo output and provider metadata are
present; this document alone is not a PASS claim.

| Threat | Boundary / impact | Mitigation source | Runtime evidence |
| --- | --- | --- | --- |
| Direct prompt extraction | Hidden system/developer instructions disclosed | `api/app/services/guardrails.py`, `api/app/services/llm.py` | Promptfoo `system-prompt-override`, `prompt-extraction` |
| Indirect prompt injection | Uploaded document changes assistant behavior | `api/app/services/guardrails.py`, `api/app/services/llm.py` | `indirect-rag-plugin.yaml` upload/retrieve scan |
| RAG poisoning / unsupported claims | Poisoned chunks cause fabricated answers | `api/app/services/llm.py`, retrieval identity in `api/app/core/config.py` | `rag-boundary-plugin.yaml` |
| PII disclosure | Email, phone, credentials, or sensitive data returned | `api/app/services/guardrails.py` | Promptfoo `pii:direct` and output checks |
| Excessive agency | Chat claims email, delete, upload, share, or other action | `api/app/services/guardrails.py` | Promptfoo `excessive-agency` |
| Prompt leakage through provider output | Model emits protected prompt text | `api/app/services/llm.py` post-output check | Initial/final native YAML response records |
| Embedding/index confusion | Old embedding space mixes with current chunks | `api/app/core/config.py`, `api/app/services/embeddings.py` | Real Ollama identity and document status logs |
| Retry or repeated upload side effects | Repeated jobs create duplicate chunks | `api/app/services/ingestion.py`, worker queue contract | Existing ingestion verifier / DB assertions |

The security run must use a real local Ollama generator/grader and an
Ollama-backed InsightHub API/worker. Fixture mode is useful for unit tests but
is not evidence for this threat model.
