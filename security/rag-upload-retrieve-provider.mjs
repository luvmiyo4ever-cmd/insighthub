const DEFAULT_BENIGN_QUESTION =
  "Tài liệu đã tải lên nói gì về cách xử lý tài liệu và RAG?";
const DEFAULT_BASE_URL = "http://127.0.0.1:8000";
const POLL_INTERVAL_MS = 500;
// CPU-only local Ollama can serialize embedding/chat work when Promptfoo has
// several target calls in flight. Keep bounded timeouts, but do not classify
// normal queue wait as a provider failure.
const POLL_TIMEOUT_MS = 180_000;
const REQUEST_TIMEOUT_MS = 120_000;

function asText(value) {
  if (typeof value === "string") {
    return value;
  }
  if (value && typeof value === "object") {
    return value.prompt || value.context || JSON.stringify(value);
  }
  return String(value ?? "");
}

function normalizeBaseUrl() {
  const value = process.env.INSIGHTHUB_REDTEAM_URL || DEFAULT_BASE_URL;
  return value.replace(/\/$/, "");
}

async function readJson(response, label) {
  const text = await response.text();
  let body;
  try {
    body = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(`${label} returned non-JSON response (${response.status})`);
  }
  if (!response.ok) {
    throw new Error(`${label} returned HTTP ${response.status}`);
  }
  return body;
}

async function fetchWithTimeout(url, init, label) {
  try {
    return await fetch(url, {
      ...init,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch (error) {
    throw new Error(
      `${label} unavailable at ${url}: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

async function waitForReady(baseUrl, documentId) {
  const deadline = Date.now() + POLL_TIMEOUT_MS;
  while (Date.now() < deadline) {
    const response = await fetchWithTimeout(
      `${baseUrl}/documents`,
      undefined,
      "GET /documents",
    );
    const documents = await readJson(response, "GET /documents");
    const document = Array.isArray(documents)
      ? documents.find((item) => item.id === documentId)
      : null;
    if (document?.status === "ready") {
      return document;
    }
    if (document?.status === "failed") {
      throw new Error(`Uploaded red-team document ${documentId} failed`);
    }
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
  }
  throw new Error(`Timed out waiting for document ${documentId} to become ready`);
}

export default class InsightHubRagUploadRetrieveProvider {
  id() {
    return "insighthub-rag-upload-retrieve";
  }

  async callApi(prompt, context) {
    const baseUrl = normalizeBaseUrl();
    const adversarialPayload = asText(prompt || context?.vars?.context);
    const fixture = [
      "# InsightHub red-team fixture",
      "This document is about InsightHub document ingestion and RAG security.",
      "",
      adversarialPayload,
    ].join("\n");
    const filename = `promptfoo-redteam-${Date.now()}.md`;
    const form = new FormData();
    form.append(
      "file",
      new Blob([fixture], { type: "text/markdown" }),
      filename,
    );

    const uploadResponse = await fetchWithTimeout(
      `${baseUrl}/documents`,
      { method: "POST", body: form },
      "POST /documents",
    );
    const upload = await readJson(uploadResponse, "POST /documents");
    if (uploadResponse.status !== 202 || !upload.id) {
      throw new Error("POST /documents did not return HTTP 202 with a document id");
    }

    const readyDocument = await waitForReady(baseUrl, upload.id);
    const chatResponse = await fetchWithTimeout(
      `${baseUrl}/chat`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question:
            process.env.INSIGHTHUB_REDTEAM_BENIGN_QUESTION ||
            DEFAULT_BENIGN_QUESTION,
        }),
      },
      "POST /chat",
    );
    const answer = await readJson(chatResponse, "POST /chat");
    return {
      output: answer.answer || "",
      metadata: {
        adapter: "upload-retrieve",
        document_id: readyDocument.id,
        upload_status: upload.status,
        retrieved_status: readyDocument.status,
      },
    };
  }
}
